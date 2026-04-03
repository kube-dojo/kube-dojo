---
title: "Module 5.1: Image Security"
slug: k8s/kcsa/part5-platform-security/module-5.1-image-security
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 4.4: Supply Chain Threats](../part4-threat-model/module-4.4-supply-chain/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** container image security across the build-store-deploy-run lifecycle
2. **Assess** image hardening practices: minimal base images, non-root users, multi-stage builds
3. **Identify** vulnerable image patterns: latest tags, unscanned registries, embedded secrets
4. **Explain** how image scanning, signing, and admission control form a defense-in-depth pipeline

---

## Why This Module Matters

Container images are the packaging format for all Kubernetes workloads. Every vulnerability, misconfiguration, or malicious code in an image becomes part of your runtime environment. Securing images throughout their lifecycle—build, store, deploy, run—is fundamental to Kubernetes security.

KCSA tests your knowledge of image security practices and vulnerability management.

---

## Image Security Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE SECURITY LIFECYCLE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BUILD                                                     │
│  ├── Choose secure base image                              │
│  ├── Minimize installed packages                           │
│  ├── Don't include secrets                                 │
│  ├── Use multi-stage builds                                │
│  └── Scan for vulnerabilities                              │
│                                                             │
│  STORE                                                     │
│  ├── Use private registry                                  │
│  ├── Sign images                                           │
│  ├── Enable vulnerability scanning                         │
│  ├── Use immutable tags                                    │
│  └── Implement access controls                             │
│                                                             │
│  DEPLOY                                                    │
│  ├── Verify signatures                                     │
│  ├── Enforce allowed registries                            │
│  ├── Block vulnerable images                               │
│  ├── Pull by digest                                        │
│  └── Use image pull secrets                                │
│                                                             │
│  RUN                                                       │
│  ├── Continuous vulnerability monitoring                   │
│  ├── Runtime threat detection                              │
│  ├── Read-only filesystem                                  │
│  └── Non-root execution                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Building Secure Images

### Base Image Selection

```
┌─────────────────────────────────────────────────────────────┐
│              BASE IMAGE COMPARISON                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IMAGE TYPE           SIZE      CVEs    USE CASE            │
│  ───────────────────────────────────────────────────────    │
│  ubuntu:22.04        ~77MB     100+    Development          │
│  debian:bookworm     ~50MB     50+     General purpose      │
│  alpine:3.19         ~7MB      10-20   Lightweight apps     │
│  distroless/static   ~2MB      0-5     Static binaries      │
│  scratch             0MB       0       Go/Rust binaries     │
│                                                             │
│  RECOMMENDATIONS:                                          │
│  ├── Production: Distroless or Alpine                      │
│  ├── Static binaries: Scratch or distroless/static         │
│  ├── Need shell: Alpine (smaller) or Debian (compatible)   │
│  └── Avoid: Full OS images (Ubuntu, CentOS) in production  │
│                                                             │
│  DISTROLESS BENEFITS:                                      │
│  • No shell (harder for attackers)                         │
│  • No package manager                                      │
│  • Minimal attack surface                                  │
│  • Smaller size = faster pulls                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: A Go application compiled as a static binary has zero runtime dependencies. Why would you still choose `gcr.io/distroless/static` over `scratch` as the base image?

### Multi-Stage Builds

```dockerfile
# Build stage - has all build tools
FROM golang:1.21 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app/myapp

# Runtime stage - minimal image
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]
```

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-STAGE BUILD BENEFITS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT MULTI-STAGE:                                      │
│  Final image includes:                                     │
│  • Build tools (gcc, make, etc.)                          │
│  • Source code                                             │
│  • Intermediate artifacts                                  │
│  • Test dependencies                                       │
│  Result: Large image with unnecessary attack surface       │
│                                                             │
│  WITH MULTI-STAGE:                                         │
│  Final image includes:                                     │
│  • Only the compiled binary                                │
│  • Minimal runtime dependencies                            │
│  Result: Small image with minimal attack surface           │
│                                                             │
│  SIZE COMPARISON EXAMPLE:                                  │
│  Go app with build tools: ~800MB                          │
│  Go app multi-stage:      ~20MB                           │
│  Go app on scratch:       ~10MB                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Dockerfile Best Practices

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKERFILE SECURITY PRACTICES                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DO:                                                       │
│  ✓ Pin base image to digest                                │
│    FROM alpine@sha256:abc123...                            │
│                                                             │
│  ✓ Run as non-root user                                    │
│    USER nonroot:nonroot                                    │
│                                                             │
│  ✓ Use COPY instead of ADD                                 │
│    COPY --chown=nonroot:nonroot app /app                   │
│                                                             │
│  ✓ Minimize layers and clean up                            │
│    RUN apt-get update && apt-get install -y pkg \          │
│        && rm -rf /var/lib/apt/lists/*                     │
│                                                             │
│  DON'T:                                                    │
│  ✗ Include secrets in image                                │
│    ENV API_KEY=secret123  # BAD                           │
│                                                             │
│  ✗ Use latest tag                                          │
│    FROM nginx:latest  # BAD                               │
│                                                             │
│  ✗ Run as root                                             │
│    USER root  # BAD for production                        │
│                                                             │
│  ✗ Install unnecessary packages                            │
│    RUN apt-get install vim curl wget  # Avoid if unused   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Image Scanning

### Vulnerability Scanning

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE SCANNING TOOLS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRIVY (Aqua Security)                                     │
│  ├── OS packages and language dependencies                 │
│  ├── Misconfigurations                                     │
│  ├── Secrets detection                                     │
│  └── SBOM generation                                       │
│                                                             │
│  GRYPE (Anchore)                                           │
│  ├── Fast vulnerability scanning                           │
│  ├── Multiple DB sources                                   │
│  └── CI/CD integration                                     │
│                                                             │
│  CLAIR (CoreOS/Red Hat)                                    │
│  ├── API-based scanning                                    │
│  ├── Registry integration                                  │
│  └── Continuous monitoring                                 │
│                                                             │
│  SCAN TIMING:                                              │
│  • Build time: Fail builds with critical CVEs              │
│  • Registry: Continuous scanning of stored images          │
│  • Runtime: Alert on new CVEs in running images            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Trivy Example

```bash
# Scan image for vulnerabilities
trivy image nginx:1.25

# Scan with severity filter
trivy image --severity HIGH,CRITICAL nginx:1.25

# Fail if critical CVEs found (for CI)
trivy image --exit-code 1 --severity CRITICAL nginx:1.25

# Generate SBOM
trivy image --format spdx-json -o sbom.json nginx:1.25

# Scan Dockerfile for misconfigurations
trivy config Dockerfile
```

### Scan Results Interpretation

```
┌─────────────────────────────────────────────────────────────┐
│              TRIVY SCAN OUTPUT                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  nginx:1.25 (debian 12.2)                                  │
│  Total: 142 (UNKNOWN: 0, LOW: 85, MEDIUM: 45, HIGH: 10,   │
│              CRITICAL: 2)                                  │
│                                                             │
│  ┌────────────┬──────────────┬──────────┬─────────────┐    │
│  │  LIBRARY   │     CVE      │ SEVERITY │   STATUS    │    │
│  ├────────────┼──────────────┼──────────┼─────────────┤    │
│  │ openssl    │ CVE-2024-XXX │ CRITICAL │ fixed 3.1.5 │    │
│  │ curl       │ CVE-2024-YYY │ HIGH     │ fixed 8.5.0 │    │
│  │ zlib       │ CVE-2023-ZZZ │ MEDIUM   │ no fix      │    │
│  └────────────┴──────────────┴──────────┴─────────────┘    │
│                                                             │
│  RESPONSE:                                                 │
│  CRITICAL: Block deployment, patch immediately             │
│  HIGH: Schedule patch within days                          │
│  MEDIUM: Include in regular updates                        │
│  LOW/UNKNOWN: Track, address opportunistically             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Registry Security

### Private Registry Configuration

```
┌─────────────────────────────────────────────────────────────┐
│              REGISTRY SECURITY                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ACCESS CONTROL                                            │
│  ├── Authentication required for all operations            │
│  ├── Role-based access (push vs pull)                      │
│  ├── Per-repository permissions                            │
│  └── Service account integration                           │
│                                                             │
│  IMAGE INTEGRITY                                           │
│  ├── Content trust (signing)                               │
│  ├── Immutable tags                                        │
│  ├── Vulnerability scanning integration                    │
│  └── Image promotion workflows                             │
│                                                             │
│  NETWORK SECURITY                                          │
│  ├── TLS encryption required                               │
│  ├── Private endpoints (no public access)                  │
│  ├── VPC/network isolation                                 │
│  └── Audit logging                                         │
│                                                             │
│  CLOUD REGISTRIES:                                         │
│  • AWS: ECR (Elastic Container Registry)                   │
│  • GCP: Artifact Registry                                  │
│  • Azure: Container Registry                               │
│  • Self-hosted: Harbor, Quay                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Image Pull Secrets

```yaml
# Create registry secret
apiVersion: v1
kind: Secret
metadata:
  name: registry-credentials
  namespace: production
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
---
# Use in pod
apiVersion: v1
kind: Pod
metadata:
  name: private-app
spec:
  imagePullSecrets:
  - name: registry-credentials
  containers:
  - name: app
    image: myregistry.io/myapp:v1.0
```

```yaml
# Or attach to ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
imagePullSecrets:
- name: registry-credentials
```

---

> **Pause and predict**: Your CI pipeline scans images and blocks builds with Critical CVEs. But images already in your registry develop new Critical CVEs as new vulnerabilities are discovered. How do you handle this gap between build-time and runtime scanning?

## Admission Control for Images

### Policy Enforcement

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE ADMISSION POLICIES                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  POLICY EXAMPLES:                                          │
│                                                             │
│  1. ALLOWED REGISTRIES                                     │
│     Allow: gcr.io/my-project/*, myregistry.io/*           │
│     Deny: docker.io/*, *                                   │
│                                                             │
│  2. NO LATEST TAG                                          │
│     Allow: image:v1.0, image@sha256:...                   │
│     Deny: image:latest, image (no tag)                    │
│                                                             │
│  3. REQUIRE DIGEST                                         │
│     Allow: image@sha256:abc123...                         │
│     Deny: image:v1.0 (tag only)                           │
│                                                             │
│  4. SIGNATURE REQUIRED                                     │
│     Allow: Images signed by trusted key                    │
│     Deny: Unsigned images                                  │
│                                                             │
│  5. NO CRITICAL CVES                                       │
│     Allow: Images with no critical vulnerabilities         │
│     Deny: Images with CRITICAL severity CVEs               │
│                                                             │
│  ENFORCEMENT TOOLS:                                        │
│  • Kyverno                                                 │
│  • OPA/Gatekeeper                                          │
│  • Connaisseur (signature verification)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kyverno Policy Example

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-trusted-registry
spec:
  validationFailureAction: Enforce
  rules:
  - name: validate-registry
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Images must be from trusted registries"
      pattern:
        spec:
          containers:
          - image: "gcr.io/my-project/* | myregistry.io/*"
```

---

## Runtime Image Security

```
┌─────────────────────────────────────────────────────────────┐
│              RUNTIME IMAGE SECURITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  READ-ONLY FILESYSTEM                                      │
│  securityContext:                                          │
│    readOnlyRootFilesystem: true                           │
│  • Prevents writing to image filesystem                    │
│  • Blocks many attack techniques                           │
│  • Use emptyDir for writable paths                         │
│                                                             │
│  NON-ROOT EXECUTION                                        │
│  securityContext:                                          │
│    runAsNonRoot: true                                     │
│    runAsUser: 1000                                        │
│  • Limits privilege if container compromised               │
│  • Image must support non-root                             │
│                                                             │
│  DROP CAPABILITIES                                         │
│  securityContext:                                          │
│    capabilities:                                          │
│      drop: ["ALL"]                                        │
│  • Remove unnecessary Linux capabilities                   │
│  • Reduce attack surface                                   │
│                                                             │
│  CONTINUOUS MONITORING                                     │
│  • Alert on new CVEs in running images                     │
│  • Track image drift (unexpected changes)                  │
│  • Audit image pull events                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The average container image has 300+ packages** and 100+ known vulnerabilities. Minimal base images can reduce this by 90%.

- **Distroless images have no shell**—if an attacker gets code execution, they can't easily run commands. This is defense in depth.

- **Google's distroless images** are built from scratch daily and include only what's needed to run a specific language runtime.

- **Image layers are cached and shared**. A vulnerability in a base layer affects all images built on it.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using :latest | Unpredictable, mutable | Pin to digest |
| Fat base images | Large attack surface | Use minimal/distroless |
| Running as root | Higher privilege if exploited | runAsNonRoot: true |
| No scanning | Unknown vulnerabilities | Scan in CI and registry |
| Writable filesystem | Persistence possible | readOnlyRootFilesystem |

---

## Quiz

1. **An application team deploys an image based on `ubuntu:22.04` with 147 CVEs (2 Critical). They say they need Ubuntu for `apt-get` access during debugging. How would you reduce the attack surface while addressing their debugging needs?**
   <details>
   <summary>Answer</summary>
   Use a multi-stage build: build stage uses Ubuntu with all necessary tools, runtime stage uses a distroless or Alpine base image containing only the compiled application. For debugging, use `kubectl debug` with ephemeral containers (which can attach a debug image temporarily) rather than bloating the production image. If shell access is truly needed, Alpine (~7MB, ~15 CVEs) is dramatically smaller than Ubuntu (~77MB, 100+ CVEs). The 2 Critical CVEs alone justify the migration — distroless images typically have 0-5 CVEs. The debugging argument is a common anti-pattern: production images should be minimal, and debugging tools should be brought in temporarily.
   </details>

2. **Your admission controller blocks images not from your private registry. A developer pushes `myregistry.io/app:v2.0` at 2 PM. At 4 PM, a new node joins the cluster and needs to pull the same image. But between 2 PM and 4 PM, an attacker replaced the image behind the `v2.0` tag. Would the new node get the compromised image? What prevents this?**
   <details>
   <summary>Answer</summary>
   Yes, the new node would pull the compromised image because `v2.0` is a mutable tag — it now points to the attacker's image. Existing nodes may still have the original cached, but new nodes pull fresh. Prevention: (1) Pull by digest (`myregistry.io/app@sha256:abc123...`) — the digest is content-addressed and immutable; (2) Enable immutable tags in the registry so tags cannot be overwritten; (3) Use image signing — the attacker's replacement wouldn't have a valid signature from your CI pipeline; (4) Use `imagePullPolicy: IfNotPresent` to avoid re-pulls, though this doesn't protect new nodes. The combination of digest + signing provides the strongest protection.
   </details>

3. **Your Dockerfile contains `ENV DATABASE_URL=postgres://admin:password@db:5432/prod`. The image was built, pushed, and deployed to 50 pods. You've since rotated the database password. Is the old password still accessible, and where?**
   <details>
   <summary>Answer</summary>
   Yes, the old password persists in multiple places: (1) Every layer of the Docker image — even if you add a subsequent layer removing the ENV, the original layer with the secret is still accessible via `docker history` or direct layer inspection; (2) In the registry where the image is stored; (3) On every node that cached the image; (4) In any CI/CD logs that show the build output; (5) Via `kubectl describe pod` which shows environment variables. This is why secrets must never be in Dockerfiles. The correct approach: use Kubernetes Secrets or external secret managers injected at runtime, and use `.dockerignore` to exclude `.env` files from COPY commands.
   </details>

4. **Your registry continuously scans stored images. A scan at 9 AM shows zero Critical CVEs. At 2 PM, a new CVE is published affecting OpenSSL. At 3 PM, the next scan reveals 30 images with this new Critical CVE. What should happen automatically, and what should require human decision?**
   <details>
   <summary>Answer</summary>
   Automatic actions: alert the security team and affected image owners, mark affected images in the registry dashboard, trigger rebuild pipelines for images with automated rebuild processes, and update vulnerability tracking systems. Human decisions needed: prioritizing which images to rebuild first (based on exposure and data sensitivity), deciding whether to roll back running deployments or wait for patched images, evaluating whether the CVE is exploitable in your specific context, and approving deployment of patched images. The key insight is that continuous scanning closes the gap between build-time scanning (which can't predict future CVEs) and the moment a new vulnerability is published.
   </details>

5. **A Kyverno policy requires all images to be from `gcr.io/my-project/*`. A developer needs to use an open-source sidecar (like Envoy) from `docker.io`. How would you handle this without weakening the registry restriction?**
   <details>
   <summary>Answer</summary>
   Mirror the Envoy image to your private registry: pull `docker.io/envoyproxy/envoy:v1.28`, scan it for vulnerabilities, sign it with your organization's key, and push it to `gcr.io/my-project/envoy:v1.28@sha256:...`. The developer references the mirrored image, which passes the admission policy. Benefits: you control when images are updated (preventing surprise upstream changes), the image is scanned before entering your registry, you have a local copy if Docker Hub has rate limits or outages, and the signing ensures it hasn't been tampered with. This is the image promotion pattern — external images are vetted and promoted to your trusted registry before use.
   </details>

---

## Hands-On Exercise: Image Security Audit

**Scenario**: Audit this Dockerfile and pod spec for security issues:

```dockerfile
FROM ubuntu:latest
RUN apt-get update && apt-get install -y curl wget vim nodejs npm
ENV DATABASE_PASSWORD=supersecret123
COPY . /app
WORKDIR /app
RUN npm install
EXPOSE 3000
CMD ["node", "server.js"]
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  containers:
  - name: app
    image: myregistry/webapp:latest
    ports:
    - containerPort: 3000
```

**Identify security issues and provide fixes:**

<details>
<summary>Security Issues and Fixes</summary>

**Dockerfile Issues:**

1. **FROM ubuntu:latest**
   - Large image, mutable tag
   - Fix: `FROM node:20-alpine@sha256:...` or distroless

2. **Installing unnecessary packages**
   - curl, wget, vim not needed at runtime
   - Fix: Remove or use multi-stage build

3. **Secret in ENV**
   - DATABASE_PASSWORD exposed in image
   - Fix: Use Kubernetes secrets at runtime

4. **COPY . /app**
   - May copy sensitive files (.env, .git)
   - Fix: Use .dockerignore, copy specific files

5. **Running as root**
   - No USER instruction
   - Fix: Add `USER node` or create non-root user

6. **npm install without lockfile**
   - Inconsistent dependencies
   - Fix: `COPY package*.json` first, use `npm ci`

**Pod Spec Issues:**

7. **image:latest tag**
   - Mutable, unpredictable
   - Fix: Use specific version or digest

8. **No securityContext**
   - Running as root, writable filesystem
   - Fix: Add securityContext

**Secure Dockerfile:**
```dockerfile
FROM node:20-alpine@sha256:abc123 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY src/ ./src/

FROM gcr.io/distroless/nodejs20:nonroot
COPY --from=builder /app /app
WORKDIR /app
USER nonroot
EXPOSE 3000
CMD ["server.js"]
```

**Secure Pod Spec:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  containers:
  - name: app
    image: myregistry/webapp@sha256:def456...
    ports:
    - containerPort: 3000
    securityContext:
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
    env:
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
```

</details>

---

## Summary

Image security spans the entire lifecycle:

| Phase | Key Controls |
|-------|-------------|
| **Build** | Minimal base, multi-stage, no secrets, scan |
| **Store** | Private registry, signing, immutable tags |
| **Deploy** | Verify signatures, allowed registries, digest |
| **Run** | Read-only FS, non-root, continuous scanning |

Key principles:
- Smaller images = smaller attack surface
- Pin to digest, not tag
- Scan at every phase
- Sign and verify images
- Run with least privilege

---

## Next Module

[Module 5.2: Security Observability](../module-5.2-observability/) - Monitoring and detecting security threats in Kubernetes.
