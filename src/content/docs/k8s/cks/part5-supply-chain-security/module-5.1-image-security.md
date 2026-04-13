---
title: "Module 5.1: Container Image Security"
slug: k8s/cks/part5-supply-chain-security/module-5.1-image-security
sidebar:
  order: 1
lab:
  id: cks-5.1-image-security
  url: https://killercoda.com/kubedojo/scenario/cks-5.1-image-security
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Docker/container basics, Module 0.3 (Security Tools)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Create** hardened Dockerfiles using multi-stage builds, minimal base images, and non-root users
2. **Configure** image pull policies and private registry authentication for clusters
3. **Implement** image digest pinning to prevent tag-based supply chain attacks
4. **Audit** container images for unnecessary packages, setuid binaries, and embedded secrets

---

## Why This Module Matters

Container images are the foundation of your workloads. A vulnerable base image, malicious package, or misconfigured Dockerfile can compromise your entire cluster. Supply chain attacks target the software before it even runs.

CKS heavily tests image security—scanning, hardening, and verification.

---

## Image Security Risks

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER IMAGE RISKS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Vulnerable Base Images                                    │
│  ├── CVEs in OS packages (glibc, openssl, etc.)           │
│  ├── Outdated language runtimes (Python, Node, Java)      │
│  └── Unnecessary tools (wget, curl, shells)               │
│                                                             │
│  Supply Chain Attacks                                      │
│  ├── Compromised package registries (npm, PyPI)           │
│  ├── Typosquatting (python vs pytbon)                     │
│  └── Malicious base images on Docker Hub                  │
│                                                             │
│  Image Misconfigurations                                   │
│  ├── Running as root                                       │
│  ├── Including secrets in layers                          │
│  └── World-readable sensitive files                       │
│                                                             │
│  Tag Mutability                                            │
│  ├── :latest can change without notice                    │
│  └── Tags can be overwritten with malicious images        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Stop and think**: Your team pulls `nginx:latest` from Docker Hub. That image was uploaded by someone you don't know, could contain malware, and "latest" might change at any time. How many assumptions about trust are you making with a single `docker pull`?

## Base Image Selection

### Choosing Secure Base Images

```
┌─────────────────────────────────────────────────────────────┐
│              BASE IMAGE OPTIONS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Distroless (Google) - MOST SECURE                        │
│  ─────────────────────────────────────────────────────────  │
│  • No shell, no package manager                            │
│  • Only application runtime                                │
│  • Minimal attack surface                                  │
│  • gcr.io/distroless/static                               │
│  • gcr.io/distroless/base                                 │
│  • gcr.io/distroless/java17                               │
│                                                             │
│  Alpine - SMALL & SECURE                                   │
│  ─────────────────────────────────────────────────────────  │
│  • ~5MB base image                                        │
│  • musl libc (not glibc)                                  │
│  • apk package manager                                    │
│  • May have compatibility issues                          │
│                                                             │
│  Slim variants - BALANCED                                  │
│  ─────────────────────────────────────────────────────────  │
│  • python:3.11-slim, node:20-slim                         │
│  • Removes dev tools and docs                             │
│  • Still has shell access                                 │
│                                                             │
│  Full images - AVOID in production                        │
│  ─────────────────────────────────────────────────────────  │
│  • ubuntu:22.04, debian:12                                │
│  • Many unnecessary packages                              │
│  • Large attack surface                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Image Size Comparison

```bash
# Check image sizes
docker images | grep -E "nginx|distroless|alpine"

# Typical sizes:
# nginx:latest          ~190MB
# nginx:alpine          ~40MB
# gcr.io/distroless/base ~20MB
# gcr.io/distroless/static ~2MB
```

---

## Dockerfile Security Best Practices

### Secure Dockerfile Example

```dockerfile
# Use specific version, not :latest
FROM python:3.11-slim-bookworm AS builder

# Don't run as root during build (when possible)
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM gcr.io/distroless/python3-debian12

# Copy from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

WORKDIR /app
COPY . .

# Run as non-root
USER nonroot

# Don't expose unnecessary ports
EXPOSE 8080

# Use exec form, not shell form
ENTRYPOINT ["python", "app.py"]
```

### Security Anti-Patterns

```dockerfile
# ❌ BAD: Using latest tag
FROM ubuntu:latest

# ❌ BAD: Running as root (implicit)
# No USER directive

# ❌ BAD: Including secrets
ENV API_KEY=supersecret123

# ❌ BAD: Installing unnecessary tools
RUN apt-get update && apt-get install -y \
    curl wget vim nano git ssh

# ❌ BAD: Shell form (vulnerable to shell injection)
ENTRYPOINT /bin/sh -c "python app.py $ARGS"

# ❌ BAD: World-readable sensitive files
COPY config.yaml /etc/config/
# Should set permissions explicitly
```

---

## Multi-Stage Builds

Multi-stage builds reduce attack surface by excluding build tools from production images.

```dockerfile
# Build stage - has all tools
FROM golang:1.21 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o myapp

# Production stage - minimal
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]
```

### Benefits

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-STAGE BENEFITS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Before (single stage):                                    │
│  ├── golang:1.21 base (~800MB)                            │
│  ├── Includes compiler, tools                              │
│  └── All build dependencies                                │
│                                                             │
│  After (multi-stage):                                      │
│  ├── distroless/static (~2MB)                             │
│  ├── Only the compiled binary                              │
│  └── No shell, no tools, no package manager               │
│                                                             │
│  Attack surface reduced by 99%+                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **What would happen if**: An attacker compromises Docker Hub and replaces the `nginx:1.25` image with a backdoored version. You redeploy your production pods (which use `image: nginx:1.25`). Would you notice? What image reference format would have protected you?

## Image Tags and Digests

### The Problem with Tags

```bash
# Tags are mutable - same tag, different content!
docker pull nginx:1.25  # Today: image A
docker pull nginx:1.25  # Tomorrow: image B (patched)

# :latest is worst - changes constantly
docker pull nginx:latest  # ???

# Tags can be maliciously overwritten in compromised registries
```

### Use Image Digests

```yaml
# SECURE: Using SHA256 digest
apiVersion: v1
kind: Pod
metadata:
  name: secure-nginx
spec:
  containers:
  - name: nginx
    # Immutable reference - can never change
    image: nginx@sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
```

### Find Image Digest

```bash
# Get digest when pulling
docker pull nginx:1.25
# Output: Digest: sha256:0d17b565...

# Or inspect existing image
docker inspect nginx:1.25 | jq -r '.[0].RepoDigests'

# Or use crane/skopeo
crane digest nginx:1.25
skopeo inspect docker://nginx:1.25 | jq -r '.Digest'
```

---

## Private Registries

### Using Private Registry

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-app
spec:
  containers:
  - name: app
    image: registry.company.com/myapp:1.0
  imagePullSecrets:
  - name: registry-creds
```

### Create Registry Secret

```bash
kubectl create secret docker-registry registry-creds \
  --docker-server=registry.company.com \
  --docker-username=user \
  --docker-password=password \
  --docker-email=user@company.com
```

### Default ImagePullSecrets for ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
imagePullSecrets:
- name: registry-creds
```

---

## Image Pull Policies

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pull-policy-demo
spec:
  containers:
  - name: app
    image: myapp:1.0
    imagePullPolicy: Always  # Always pull from registry
    # Options:
    # Always - Pull every time (good for :latest)
    # IfNotPresent - Use local if exists (default for tagged)
    # Never - Only use local image
```

### Policy Recommendations

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE PULL POLICIES                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Always                                                    │
│  └── Use when: :latest tag, mutable tags                   │
│      Ensures latest version, but requires registry access  │
│                                                             │
│  IfNotPresent (default)                                    │
│  └── Use when: Immutable tags (v1.2.3), digests           │
│      Faster, uses cached images                            │
│                                                             │
│  Never                                                     │
│  └── Use when: Pre-loaded images, air-gapped environments │
│      Image must exist on node                              │
│                                                             │
│  Best Practice: Use specific tags + IfNotPresent          │
│  Or: Use digests for maximum security                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Pause and predict**: A distroless image has no shell, no package manager, and no debugging tools. An attacker compromises the application inside it. What can they do compared to compromising an application inside an Ubuntu-based image?

## Real Exam Scenarios

### Scenario 1: Fix Insecure Image Reference

```yaml
# Before (insecure)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx:latest  # Mutable!
    imagePullPolicy: IfNotPresent

# After (secure)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx@sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
    imagePullPolicy: IfNotPresent
```

### Scenario 2: Use Private Registry

```bash
# Create registry secret
kubectl create secret docker-registry private-reg \
  --docker-server=gcr.io \
  --docker-username=_json_key \
  --docker-password="$(cat key.json)" \
  -n production

# Create pod using private image
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: private-app
  namespace: production
spec:
  containers:
  - name: app
    image: gcr.io/myproject/myapp:1.0
  imagePullSecrets:
  - name: private-reg
EOF
```

### Scenario 3: Identify Pods Using :latest

```bash
# Find all pods using :latest tag
kubectl get pods -A -o json | jq -r '
  .items[] |
  .spec.containers[] |
  select(.image | contains(":latest") or (contains(":") | not)) |
  "\(.name): \(.image)"
'
```

---

## Dockerfile Analysis Checklist

```bash
# Questions to ask when reviewing Dockerfile:

# 1. Base image security
grep "^FROM" Dockerfile
# Is it using :latest? A known vulnerable version?
# Is it from a trusted source?

# 2. Running as root?
grep "^USER" Dockerfile
# No USER directive = running as root

# 3. Secrets in image?
grep -E "ENV.*KEY|ENV.*SECRET|ENV.*PASSWORD" Dockerfile
grep -E "COPY.*\.env|COPY.*secret" Dockerfile

# 4. Unnecessary tools installed?
grep -E "curl|wget|vim|nano|ssh|git" Dockerfile

# 5. Setuid/setgid binaries?
# Are there commands to remove setuid bits if not needed?
# e.g., RUN find / -xdev -perm /6000 -exec chmod a-s {} \; || true

# 6. Using exec form?
grep "^ENTRYPOINT\|^CMD" Dockerfile
# Shell form: ENTRYPOINT /bin/sh -c "..."
# Exec form: ENTRYPOINT ["...", "..."]
```

---

## Did You Know?

- **Docker Hub rate limits** unauthenticated pulls to 100 per 6 hours. Many production outages have been caused by hitting these limits.

- **Distroless images don't have a shell**, which means you can't exec into them for debugging. Use ephemeral debug containers (`kubectl debug`) instead.

- **Image layers are shared**. If multiple pods use the same base image, that layer is stored only once on the node.

- **Alpine uses musl libc** instead of glibc. Some applications may have compatibility issues, particularly those using DNS resolution or certain threading patterns.

- **K8s 1.35: Image pull credentials now verified for every pod** (KubeletEnsureSecretPulledImages, enabled by default). Even if an image is cached locally, the kubelet re-validates pull credentials. This prevents unauthorized pods from using cached images they shouldn't have access to. Configure via `imagePullCredentialsVerificationPolicy`: `AlwaysVerify` (default), `NeverVerify`, or `NeverVerifyAllowlistedImages`.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using :latest | Unpredictable deployments | Use specific tags or digests |
| No USER directive | Container runs as root | Add USER nonroot |
| Secrets in ENV | Visible in image history | Use secrets at runtime |
| Full base images | Large attack surface | Use slim/distroless |
| No pull policy | May use stale images | Set explicit policy |

---

## Quiz

1. **Your production deployment uses `image: myapp:latest`. After a routine pod restart, the application starts behaving differently -- new endpoints appear that weren't in your code. Investigation reveals the `:latest` tag now points to a compromised image. How did this happen, and what image reference format prevents it?**
   <details>
   <summary>Answer</summary>
   The `:latest` tag is mutable -- someone (or an attacker who compromised the registry) pushed a new image with the same tag. When the pod restarted, kubelet pulled the new (compromised) image. Use image digests instead: `image: myapp@sha256:abc123...`. Digests are content-addressable and immutable -- they always point to the exact same image bytes. Even if an attacker replaces the tag, the digest reference continues pulling the original verified image. Additionally, set `imagePullPolicy: IfNotPresent` (not `Always`) and use a private registry with access controls and image signing (cosign/Notary) to verify image provenance.
   </details>

2. **A security scanner reports that your `ubuntu:22.04`-based application image has 142 vulnerabilities, including 3 CRITICAL ones in OpenSSL and curl. Your application is a compiled Go binary that doesn't use OpenSSL or curl. Are these vulnerabilities still a risk, and how do you eliminate them?**
   <details>
   <summary>Answer</summary>
   Yes, they're still a risk. Even though your Go binary doesn't use OpenSSL directly, an attacker who compromises the container can use the installed `curl` and vulnerable OpenSSL for lateral movement, data exfiltration, and further exploitation. The base image's tools become the attacker's toolkit. Solution: switch to a distroless or scratch base image. For Go: `FROM gcr.io/distroless/static-debian12` (or `FROM scratch` for fully static binaries). This eliminates all 142 vulnerabilities because there are no extra packages -- just your binary. Use multi-stage builds: compile in an `ubuntu` stage, copy only the binary to distroless. The 3 CRITICAL CVEs disappear entirely because the vulnerable libraries aren't present.
   </details>

3. **Your CI/CD pipeline builds images and pushes them to a private registry. A developer notices that the `staging` and `production` deployments show different application behavior even though they reference the same tag `myapp:v2.1`. How is this possible, and what supply chain controls prevent it?**
   <details>
   <summary>Answer</summary>
   Tags are mutable -- someone pushed a new image with the same `v2.1` tag between the staging and production deployments. Staging pulled the original, production pulled the replacement. Prevention: (1) Use image digests in deployment manifests so both environments reference the exact same image bytes. (2) Implement image signing with cosign -- sign images in CI and verify signatures before deployment. (3) Use an admission controller (or ImagePolicyWebhook) that rejects unsigned or unverified images. (4) Configure the registry to be immutable (prevent tag overwrites). (5) Pin CI/CD to promote the exact digest from staging to production, never re-resolving tags.
   </details>

4. **Your Dockerfile starts with `FROM ubuntu:22.04`, installs `gcc`, `make`, and `python3` for building, then copies the compiled binary. The final image is 850MB with 200+ packages. How do you reduce this to under 20MB while maintaining the same build process?**
   <details>
   <summary>Answer</summary>
   Use a multi-stage build. Stage 1 (`builder`): `FROM ubuntu:22.04`, install build tools, compile the binary. Stage 2 (`final`): `FROM gcr.io/distroless/static-debian12` (or `scratch`), `COPY --from=builder /app/binary /app/binary`. The final image contains only the compiled binary -- no gcc, make, python3, or any Ubuntu packages. This reduces the image from 850MB to under 20MB, eliminates 200+ packages of attack surface, and removes all build tools an attacker could use. The build process is identical -- only the final artifact changes. Add `USER nonroot` in the distroless stage for non-root execution.
   </details>

---

## Hands-On Exercise

**Task**: Analyze and secure a container image deployment.

```bash
# Step 1: Find pods using :latest or no tag
echo "=== Pods with potentially insecure images ==="
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.containers[].image | (contains(":latest") or (contains(":") | not))) |
  "\(.metadata.namespace)/\(.metadata.name): \(.spec.containers[].image)"
'

# Step 2: Create insecure pod for testing
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: nginx:latest
    imagePullPolicy: Always
EOF

# Wait for pod to be ready so the image is pulled and imageID is populated
kubectl wait --for=condition=Ready pod/insecure-pod --timeout=60s

# Step 3: Get the actual digest of the image
kubectl get pod insecure-pod -o jsonpath='{.status.containerStatuses[0].imageID}'
# This shows the actual digest being used

# Step 4: Create secure version with digest
# (Use the digest from step 3 or pull fresh)
DIGEST=$(kubectl get pod insecure-pod -o jsonpath='{.status.containerStatuses[0].imageID}' | sed 's/docker-pullable:\/\///')

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  containers:
  - name: app
    image: ${DIGEST}
    imagePullPolicy: IfNotPresent
EOF

# Step 5: Verify
kubectl get pod secure-pod -o jsonpath='{.spec.containers[0].image}'

# Cleanup
kubectl delete pod insecure-pod secure-pod
```

**Success criteria**: Understand image tag risks and how to use digests.

---

## Summary

**Image Security Principles**:
- Use specific tags, not :latest
- Prefer digests for immutability
- Choose minimal base images
- Multi-stage builds for production

**Base Image Hierarchy** (most to least secure):
1. Distroless
2. Alpine
3. Slim variants
4. Full distributions

**Dockerfile Security**:
- Non-root USER
- Exec form for ENTRYPOINT/CMD
- No secrets in ENV
- Minimal packages

**Exam Tips**:
- Know how to identify insecure images
- Understand pull policies
- Be able to convert tags to digests

---

## Next Module

[Module 5.2: Image Scanning with Trivy](../module-5.2-image-scanning/) - Finding vulnerabilities in container images.
