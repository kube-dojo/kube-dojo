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

1. **What's the default image tag if none is specified?**
   <details>
   <summary>Answer</summary>
   `latest`. For example, `nginx` is equivalent to `nginx:latest`.
   </details>

2. **A Pod is stuck in ImagePullBackOff. What's the first debugging step?**
   <details>
   <summary>Answer</summary>
   Run `kubectl describe pod <name>` and check the Events section. It will show the specific pull error, like image not found or authentication failure.
   </details>

3. **How do you override a Dockerfile's CMD in a Kubernetes Pod spec?**
   <details>
   <summary>Answer</summary>
   Use the `args` field in the container spec:
   ```yaml
   containers:
   - name: app
     image: myimage
     args: ["new", "command", "here"]
   ```
   </details>

4. **What's the difference between `imagePullPolicy: Always` and `IfNotPresent`?**
   <details>
   <summary>Answer</summary>
   `Always` pulls the image on every pod start, even if cached locally. `IfNotPresent` only pulls if the image isn't already on the node. Use `Always` for `latest` tags; use `IfNotPresent` for specific version tags to save bandwidth.
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
