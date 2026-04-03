---
title: "Module 1.1: Container Images"
slug: k8s/ckad/part1-design-build/module-1.1-container-images
sidebar:
  order: 1
lab:
  id: ckad-1.1-container-images
  url: https://killercoda.com/kubedojo/scenario/ckad-1.1-container-images
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Requires understanding of Dockerfile and image registries
>
> **Time to Complete**: 45-60 minutes
>
> **Prerequisites**: Module 0.2 (Developer Workflow), basic Docker knowledge

---

## Learning Outcomes

After completing this module, you will be able to:
- **Create** a Dockerfile that follows best practices for size, security, and layer caching
- **Configure** image pull policies and registry credentials for pod specifications
- **Debug** image pull errors including `ImagePullBackOff` and authentication failures
- **Explain** image tagging strategies and why `:latest` is dangerous in production

---

## Why This Module Matters

Kubernetes doesn't run source code—it runs container images. Before any application reaches a cluster, it must be packaged into an image. The CKAD expects you to understand how images are built, tagged, pushed, and referenced.

While you won't build complex images during the exam (no time), you need to:
- Understand Dockerfile basics
- Know image naming conventions
- Fix common image-related issues
- Modify existing images when needed

> **The Shipping Container Analogy**
>
> Before containerization, shipping goods was chaos. Each port handled cargo differently. Then came the standardized shipping container—same dimensions everywhere, stackable, works on any ship. Container images are the same idea for software. Your application, its dependencies, its config—all packaged into a standard format that runs identically everywhere.

---

## Image Naming Convention

Understanding image names is critical. Every Kubernetes Pod spec references images:

```
[registry/][namespace/]image[:tag][@digest]
```

| Component | Required | Example | Default |
|-----------|----------|---------|---------|
| Registry | No | `docker.io`, `gcr.io`, `quay.io` | `docker.io` |
| Namespace | No | `library`, `mycompany` | `library` |
| Image | Yes | `nginx`, `myapp` | - |
| Tag | No | `latest`, `1.19.0`, `alpine` | `latest` |
| Digest | No | `sha256:abc123...` | - |

### Examples

```yaml
# Full specification
image: docker.io/library/nginx:1.21.0

# Equivalent short form (docker.io/library implied)
image: nginx:1.21.0

# Different registry
image: gcr.io/google-containers/nginx:1.21.0

# Custom namespace
image: myregistry.com/myteam/myapp:v2.0.0

# With digest (immutable reference)
image: nginx@sha256:abc123def456...

# Latest tag (avoid in production)
image: nginx:latest
image: nginx  # same as above
```

### Why Tags Matter

```yaml
# BAD: latest can change unexpectedly
image: nginx:latest

# GOOD: specific version, reproducible
image: nginx:1.21.0

# BETTER: specific version with Alpine base (smaller)
image: nginx:1.21.0-alpine
```

---

## Dockerfile Basics

A Dockerfile defines how to build an image. CKAD may ask you to understand or modify simple Dockerfiles.

### Minimal Dockerfile

```dockerfile
# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port (documentation)
EXPOSE 8080

# Command to run
CMD ["python", "app.py"]
```

### Common Instructions

| Instruction | Purpose | Example |
|-------------|---------|---------|
| `FROM` | Base image | `FROM nginx:alpine` |
| `WORKDIR` | Set working directory | `WORKDIR /app` |
| `COPY` | Copy files from build context | `COPY src/ /app/` |
| `RUN` | Execute command during build | `RUN apt-get update` |
| `ENV` | Set environment variable | `ENV PORT=8080` |
| `EXPOSE` | Document port (doesn't publish) | `EXPOSE 8080` |
| `CMD` | Default command to run | `CMD ["nginx", "-g", "daemon off;"]` |
| `ENTRYPOINT` | Main executable | `ENTRYPOINT ["python"]` |

> **Pause and predict**: In a Kubernetes Pod spec, `command` overrides one Dockerfile instruction and `args` overrides another. Which is which? Many developers get this backwards. Think about it before reading the mapping below.

### CMD vs ENTRYPOINT

```dockerfile
# CMD: Easily overridden
FROM nginx
CMD ["nginx", "-g", "daemon off;"]
# Can run: docker run myimage sleep 10 (replaces CMD)

# ENTRYPOINT: Hard to override
FROM python
ENTRYPOINT ["python"]
CMD ["app.py"]
# Runs: python app.py
# Can run: docker run myimage script.py (only replaces CMD)
```

In Kubernetes Pod specs:
- `ENTRYPOINT` maps to `command:`
- `CMD` maps to `args:`

```yaml
spec:
  containers:
  - name: app
    image: python:3.9
    command: ["python"]    # Overrides ENTRYPOINT
    args: ["myapp.py"]     # Overrides CMD
```

---

## Building Images

While you won't build images in the exam environment (no Docker daemon), understanding the process helps debug issues.

### Basic Build

```bash
# Build in current directory
docker build -t myapp:v1.0.0 .

# Build with specific Dockerfile
docker build -t myapp:v1.0.0 -f Dockerfile.prod .

# Build with build arguments
docker build --build-arg VERSION=1.0.0 -t myapp:v1.0.0 .
```

### Tagging and Pushing

```bash
# Tag an existing image
docker tag myapp:v1.0.0 myregistry.com/team/myapp:v1.0.0

# Push to registry
docker push myregistry.com/team/myapp:v1.0.0

# Push all tags
docker push myregistry.com/team/myapp --all-tags
```

---

## Image Pull Policy

Kubernetes decides when to pull images based on `imagePullPolicy`:

```yaml
spec:
  containers:
  - name: app
    image: nginx:1.21.0
    imagePullPolicy: Always  # IfNotPresent | Never | Always
```

| Policy | Behavior | Use When |
|--------|----------|----------|
| `Always` | Pull every time | Using `latest` tag, need freshest image |
| `IfNotPresent` | Pull only if not cached | Specific tags, save bandwidth |
| `Never` | Never pull, use cached | Local development, air-gapped |

> **Stop and think**: If you specify `image: nginx` (no tag) in a pod spec, what `imagePullPolicy` does Kubernetes use by default? What about `image: nginx:1.21.0`? The defaults are different -- why does that make sense?

### Default Behavior

| Image Tag | Default Policy |
|-----------|---------------|
| No tag (implies `:latest`) | `Always` |
| `:latest` | `Always` |
| Specific tag (`:v1.0.0`) | `IfNotPresent` |
| Digest (`@sha256:...`) | `IfNotPresent` |

---

## Private Registries

To pull from private registries, you need authentication:

### Step 1: Create a Secret

```bash
# Create docker-registry secret
k create secret docker-registry regcred \
  --docker-server=myregistry.com \
  --docker-username=user \
  --docker-password=password \
  --docker-email=user@example.com
```

### Step 2: Reference in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-app
spec:
  containers:
  - name: app
    image: myregistry.com/team/myapp:v1.0.0
  imagePullSecrets:
  - name: regcred
```

### Alternative: ServiceAccount Default

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
imagePullSecrets:
- name: regcred
---
apiVersion: v1
kind: Pod
metadata:
  name: private-app
spec:
  serviceAccountName: myapp-sa
  containers:
  - name: app
    image: myregistry.com/team/myapp:v1.0.0
```

---

## Troubleshooting Image Issues

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ImagePullBackOff` | Can't pull image | Check image name, registry access |
| `ErrImagePull` | Pull failed | Verify image exists, check credentials |
| `InvalidImageName` | Malformed image reference | Fix image name format |
| `ImageInspectError` | Image inspection failed | Check image manifest |

### Debugging Steps

```bash
# Check pod events
k describe pod myapp | grep -A10 Events

# Check image name
k get pod myapp -o jsonpath='{.spec.containers[0].image}'

# Verify secret exists
k get secret regcred

# Test pull manually (if docker available)
docker pull myregistry.com/team/myapp:v1.0.0
```

> **What would happen if**: A pod references a private registry image but has no `imagePullSecrets`. The image exists and is correctly tagged. What error would you see, and how would you distinguish it from a simple typo in the image name?

### Example: Fixing ImagePullBackOff

```bash
# Pod stuck in ImagePullBackOff
k get pods
# NAME    READY   STATUS             RESTARTS   AGE
# myapp   0/1     ImagePullBackOff   0          5m

# Check events
k describe pod myapp
# Events:
#   Failed to pull image "nginx:latst": rpc error: ...not found

# Found it: typo in tag (latst instead of latest)

# Fix: Edit the pod or delete and recreate
k delete pod myapp
k run myapp --image=nginx:latest
```

---

## Image Security Best Practices

While not always tested, understanding these makes you a better developer:

### 1. Use Specific Tags

```yaml
# BAD
image: nginx:latest

# GOOD
image: nginx:1.21.0-alpine
```

### 2. Use Minimal Base Images

```dockerfile
# 133MB
FROM python:3.9

# 45MB - much smaller
FROM python:3.9-slim

# 17MB - even smaller
FROM python:3.9-alpine
```

### 3. Run as Non-Root

```dockerfile
FROM python:3.9-slim
RUN useradd -m appuser
USER appuser
COPY --chown=appuser:appuser . /app
```

In Kubernetes:

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: myapp:v1.0.0
```

### 4. Use Read-Only Filesystem

```yaml
spec:
  containers:
  - name: app
    image: myapp:v1.0.0
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

---

## Did You Know?

- **Container images are layered.** Each Dockerfile instruction creates a layer. Layers are cached and shared between images, saving disk space and build time. That's why you put frequently changing content (like `COPY . .`) at the end.

- **The `latest` tag is just a convention.** It's not actually "latest" by time—it's whatever was last pushed without a specific tag. Many projects push `latest` with each build, but some never update it.

- **Image digests (sha256:...) are immutable.** Tags can be moved to point to different images, but a digest always refers to the exact same image content. Use digests for maximum reproducibility in production.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using `latest` in production | Unpredictable updates | Always use specific tags |
| Typos in image names | ImagePullBackOff | Double-check spelling |
| Forgetting `imagePullSecrets` | Can't pull private images | Add secret reference to pod |
| Wrong `imagePullPolicy` | Cache issues or unnecessary pulls | Set explicitly based on needs |
| Large base images | Slow pulls, security surface | Use `-slim` or `-alpine` variants |

---

## Quiz

1. **A developer pushes a fix to their app and deploys it using `image: myapp` (no tag). The pod restarts, but the old version is still running. They swear they pushed the new image. What's going on?**
   <details>
   <summary>Answer</summary>
   Without a tag, Kubernetes defaults to `:latest` and sets `imagePullPolicy: Always`. However, the developer likely pushed without tagging as `latest`, or the node has a cached version. The real problem is using `latest` in the first place -- it's ambiguous and unreproducible. The fix is to use specific version tags (e.g., `myapp:v1.2.3`) so each deployment references an exact image. This also makes rollbacks predictable since you know exactly which version each revision used.
   </details>

2. **Your colleague deployed a pod that's stuck in `ImagePullBackOff`. They say the image name is correct because they can `docker pull` it on their laptop. What are the three most likely causes, and how do you systematically diagnose which one?**
   <details>
   <summary>Answer</summary>
   Run `kubectl describe pod <name>` and check the Events section. The three most likely causes are: (1) the image name has a typo (e.g., `ngix` instead of `nginx`) -- the Events will say "not found"; (2) it's a private registry and the pod is missing `imagePullSecrets` -- the Events will show "unauthorized" or "authentication required"; (3) the tag doesn't exist in the registry -- Events will say "manifest unknown". Their laptop works because Docker is logged into the registry locally. The cluster nodes need separate authentication via `imagePullSecrets` or a ServiceAccount with registry credentials.
   </details>

3. **You have a Dockerfile with `ENTRYPOINT ["python"]` and `CMD ["app.py"]`. In your Kubernetes pod spec, you want to run `python test.py` instead. Should you override `command`, `args`, or both?**
   <details>
   <summary>Answer</summary>
   Override only `args: ["test.py"]`. In Kubernetes, `command` maps to Docker's `ENTRYPOINT` and `args` maps to `CMD`. Since you still want `python` as the entrypoint, leave `command` alone and just change `args`. If you set `command: ["python"]` AND `args: ["test.py"]`, it works but is redundant. If you only set `command: ["test.py"]`, it would try to execute `test.py` directly without the Python interpreter, which would fail.
   </details>

4. **Your production cluster pulls images slowly because every pod restart re-downloads from the registry. All your images use specific version tags like `v2.1.0`. A teammate suggests setting `imagePullPolicy: Never` to fix it. Why is that dangerous, and what's the correct solution?**
   <details>
   <summary>Answer</summary>
   `Never` means pods will fail to start on any node that doesn't already have the image cached -- this breaks scaling to new nodes and disaster recovery. The correct solution is `imagePullPolicy: IfNotPresent`, which is actually the default for specific version tags. If pods are still re-pulling, check whether someone has overridden the policy to `Always` in the pod spec. With `IfNotPresent`, the image is pulled once per node and cached, giving you fast restarts without the risk of `Never`.
   </details>

---

## Hands-On Exercise

**Task**: Fix a broken deployment with image issues.

**Setup:**
```bash
# Create a deployment with intentional image problems
k create deploy broken-app --image=nginx:nonexistent
```

**Your Tasks:**
1. Check why the pods aren't running
2. Find the correct image tag
3. Fix the deployment

**Solution:**
```bash
# Check pod status
k get pods
# Shows ImagePullBackOff

# Get details
k describe pod -l app=broken-app | grep -A5 Events
# Shows: nginx:nonexistent not found

# Fix by patching the deployment
k set image deploy/broken-app nginx=nginx:1.21.0

# Verify
k get pods
# Should show Running

# Cleanup
k delete deploy broken-app
```

**Success Criteria:**
- [ ] Identified the image issue
- [ ] Fixed the image reference
- [ ] Pod is now running

---

## Practice Drills

### Drill 1: Image Name Parsing (Target: 2 minutes)

Identify the components of these image references:

```
1. nginx
   Registry: docker.io (default)
   Namespace: library (default)
   Image: nginx
   Tag: latest (default)

2. gcr.io/google-containers/pause:3.2
   Registry: gcr.io
   Namespace: google-containers
   Image: pause
   Tag: 3.2

3. mycompany.com/team/app:v2.0.0-alpine
   Registry: mycompany.com
   Namespace: team
   Image: app
   Tag: v2.0.0-alpine
```

### Drill 2: Fix ImagePullBackOff (Target: 3 minutes)

```bash
# Create broken pod
k run broken --image=nginx:1.999.0

# Diagnose
k describe pod broken | grep -A5 Events

# Fix
k delete pod broken
k run broken --image=nginx:1.21.0

# Verify
k get pod broken

# Cleanup
k delete pod broken
```

### Drill 3: Private Registry Secret (Target: 4 minutes)

```bash
# Create registry secret
k create secret docker-registry myregistry \
  --docker-server=private.registry.io \
  --docker-username=testuser \
  --docker-password=testpass

# Create pod with secret reference
cat << EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: private-pod
spec:
  containers:
  - name: app
    image: private.registry.io/app:latest
  imagePullSecrets:
  - name: myregistry
EOF

# Check if secret is referenced
k get pod private-pod -o jsonpath='{.spec.imagePullSecrets}'

# Cleanup
k delete pod private-pod
k delete secret myregistry
```

### Drill 4: Override Command and Args (Target: 3 minutes)

```bash
# Create pod that overrides CMD
cat << EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: custom-cmd
spec:
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c"]
    args: ["echo 'Custom command' && sleep 10"]
EOF

# Check logs
k logs custom-cmd

# Verify the command
k get pod custom-cmd -o jsonpath='{.spec.containers[0].command}'
k get pod custom-cmd -o jsonpath='{.spec.containers[0].args}'

# Cleanup
k delete pod custom-cmd
```

### Drill 5: imagePullPolicy Testing (Target: 3 minutes)

```bash
# Create pods with different policies
cat << EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pull-always
spec:
  containers:
  - name: nginx
    image: nginx:1.21.0
    imagePullPolicy: Always
---
apiVersion: v1
kind: Pod
metadata:
  name: pull-ifnotpresent
spec:
  containers:
  - name: nginx
    image: nginx:1.21.0
    imagePullPolicy: IfNotPresent
EOF

# Check policies
k get pod pull-always -o jsonpath='{.spec.containers[0].imagePullPolicy}'
k get pod pull-ifnotpresent -o jsonpath='{.spec.containers[0].imagePullPolicy}'

# Cleanup
k delete pod pull-always pull-ifnotpresent
```

### Drill 6: Complete Image Troubleshooting (Target: 5 minutes)

**Scenario:** A colleague pushed a deployment but pods won't start.

```bash
# Setup (simulating the problem)
k create deploy webapp --image=nginx:alpine-wrong-tag

# YOUR TASK: Find and fix the issue

# Step 1: Check deployment status
k get deploy webapp
k get pods -l app=webapp

# Step 2: Investigate the error
k describe pods -l app=webapp | grep -A10 Events

# Step 3: Find correct image tag
# (In real scenario, check registry or documentation)
# The correct tag is nginx:alpine

# Step 4: Fix
k set image deploy/webapp nginx=nginx:alpine

# Step 5: Verify
k rollout status deploy/webapp
k get pods -l app=webapp

# Cleanup
k delete deploy webapp
```

---

## Next Module

[Module 1.2: Jobs and CronJobs](../module-1.2-jobs-cronjobs/) - Run one-time and scheduled batch workloads.
