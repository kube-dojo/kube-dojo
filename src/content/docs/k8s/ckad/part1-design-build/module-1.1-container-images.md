---
title: "Module 1.1: Container Images"
slug: k8s/ckad/part1-design-build/module-1.1-container-images
revision_pending: false
sidebar:
  order: 1
lab:
  id: ckad-1.1-container-images
  url: https://killercoda.com/kubedojo/scenario/ckad-1.1-container-images
  duration: "75 min"
  difficulty: intermediate
  environment: kubernetes
---

> **Complexity**: `[MEDIUM]` - Requires understanding of Dockerfile behavior, image references, registry access, and Kubernetes Pod startup diagnostics
>
> **Time to Complete**: 75 minutes
>
> **Prerequisites**: [Module 0.2 (Developer Workflow)](../part0-environment/module-0.2-developer-workflow/), basic container knowledge, and comfort reading Pod events

---

## Learning Outcomes

After completing this module, you will be able to:

- **Diagnose** `ImagePullBackOff`, `ErrImagePull`, registry authentication failures, and malformed image references by reading Kubernetes Pod events and image fields.
- **Design** reproducible Kubernetes 1.35+ image references using explicit registries, tags, digests, and `imagePullPolicy` values.
- **Compare and implement** Dockerfile `CMD` and `ENTRYPOINT` behavior with Kubernetes `command` and `args` overrides.
- **Optimize** Dockerfiles for layer caching, minimal base images, non-root execution, and smaller runtime attack surface.
- **Evaluate** OCI image indexes, layer media types, registry referrers, and signatures when planning multi-architecture or supply-chain workflows.

## Why This Module Matters

Hypothetical scenario: a staging rollout looks ordinary until every new replica pauses in `ImagePullBackOff`. The Deployment is healthy enough to exist, the scheduler has placed Pods, and the cluster has capacity, but the kubelet cannot obtain the container image that the Pod specification requests. A developer can pull the same image from a laptop, which makes the failure feel mysterious, but the node runtime is the system that actually needs registry access.

Container images are the handoff point between application development and Kubernetes operations. Kubernetes does not build your application, inspect your source tree, or guess which binary you meant to ship. It asks the node runtime to pull a named artifact, unpack that artifact into a filesystem, and start the configured process with the isolation rules in the Pod spec. If any part of that chain is vague, mutable, or unauthenticated, a clean manifest can still fail at runtime.

This module treats image handling as an operational skill rather than a packaging footnote. You will connect the image reference string to the registry lookup, connect Dockerfile instructions to Kubernetes `command` and `args`, and connect pull policy choices to node cache behavior. The goal is not to memorize every container tool. The goal is to make image-related failures boring because you know where each decision is made.

The CKAD exam rewards that kind of practical diagnosis. A Pod stuck before the container starts has a different investigation path than an application that crashes after startup, and image problems often reveal themselves only in the Events section. By the end, you should be able to look at an image name, a pull policy, a Secret, and a Dockerfile entrypoint and predict how a Kubernetes 1.35+ node will behave.

## Image References Are Runtime Addresses

An image reference is more than a short name in YAML. It is the address that tells the node runtime which registry to contact, which repository path to read, which tag or digest to resolve, and which image manifest to download. When the reference is incomplete, Kubernetes and the container runtime fill in defaults, and those defaults are convenient for practice but risky for controlled deployments.

The compact reference shape is worth learning because it explains many confusing pull failures. A bare `nginx` reference is not a magic Kubernetes object; it becomes a request for the default Docker Hub namespace and the default `latest` tag. A fully qualified reference carries more intent, while a digest adds cryptographic immutability by naming the exact manifest content instead of a movable tag.

```text
[registry/][namespace/]image[:tag][@digest]
```

The bracketed pieces are optional, but optional does not mean irrelevant. Omitting the registry usually means `docker.io`, omitting the namespace often means `library`, and omitting the tag means `latest`. Those defaults make quick demos pleasant, yet they hide decisions that production systems normally want to record explicitly in version control.

| Component | Required | Example | Default |
|-----------|----------|---------|---------|
| Registry | No | `docker.io`, `gcr.io`, `quay.io` | `docker.io` |
| Namespace | No | `library`, `mycompany` | `library` |
| Image | Yes | `nginx`, `myapp` | - |
| Tag | No | `latest`, `1.19.0`, `alpine` | `latest` |
| Digest | No | `sha256:abc123...` | - |

The examples below all look like ordinary YAML values, but they represent different operational guarantees. A short public image reference is easy to type during a lab, a private registry reference requires credentials, and a digest reference gives you the strongest repeatability because the content address must match. Kubernetes stores the string you provide; the node runtime performs the registry work when a Pod lands on a node.

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

Tags are human-friendly pointers, not permanent release records. A team can retag a different image as `v1.21.0` if the registry allows it, and many teams accidentally overwrite `latest` during development. Digests are different because the hash is computed from the manifest content, so the same digest cannot silently point at a different image without changing the address.

```yaml
# BAD: latest can change unexpectedly
image: nginx:latest

# GOOD: specific version, reproducible
image: nginx:1.21.0

# BETTER: specific version with Alpine base (smaller)
image: nginx:1.21.0-alpine
```

For CKAD work, the practical habit is simple: read the full image string before changing anything else. If the tag is omitted, you are already dealing with `latest`. If the registry is omitted, make sure the cluster is expected to pull from the public default. If the reference includes a digest, understand that changing only a tag elsewhere will not affect this Pod unless the digest value changes too.

Pause and predict: if two Pods use `nginx:1.21.0`, but one Pod also pins a digest that does not belong to that tag, which reference do you expect the runtime to trust? The digest is the stronger content selector, so a mismatch should make you suspicious of the manifest reference before you blame scheduling or application code.

## What an Image Contains

Container images are standardized artifacts, not Docker-specific folklore. The Open Container Initiative defines the image format, distribution behavior, and runtime bundle expectations that let tools such as Docker, containerd, BuildKit, Podman, Buildah, registries, and Kubernetes interoperate. Docker remains a common developer interface, but Kubernetes worker nodes usually talk to a CRI-compatible runtime such as containerd.

An OCI image manifest describes the image configuration and the ordered layers that form the container filesystem. The `schemaVersion` remains set to `2` for compatibility with Docker-style registries, and the OCI media type for a single-platform image manifest is `application/vnd.oci.image.manifest.v1+json`. That manifest is the thing a digest usually identifies when you pin an image by `sha256`.

Layers are read-only filesystem changes stacked in order. A running container gets an additional thin writable layer, and copy-on-write behavior means the runtime copies a file into that writable layer only when the container modifies it. This is why many Pods on the same node can share the same base image layers without duplicating the entire filesystem for every container.

The layer model explains both performance and surprise. It is efficient because identical layers can be reused across images and containers, but it also means a badly ordered Dockerfile can invalidate expensive cached layers every time a source file changes. When you optimize a Dockerfile, you are really arranging filesystem changes so stable work stays in stable layers and volatile work happens later.

OCI layer media types describe how those layer tar archives are represented during transfer. Common media types include `application/vnd.oci.image.layer.v1.tar`, `application/vnd.oci.image.layer.v1.tar+gzip`, and `application/vnd.oci.image.layer.v1.tar+zstd`. The zstd variant matters in modern registries because better compression can reduce bandwidth and speed up pulls, especially for large fleets or frequent rollouts.

Multi-architecture images add one more level. Instead of one manifest, an OCI image index uses media type `application/vnd.oci.image.index.v1+json` and points to platform-specific manifests. When an AMD64 node and an ARM64 node pull the same logical image reference, the runtime can select the nested manifest that matches the node architecture, which keeps the Pod spec portable across mixed clusters.

This matters because Kubernetes schedules Pods before the image pull happens. The scheduler can place a Pod on a node that satisfies the Pod constraints, and then the kubelet asks the runtime to fetch the image for that node. If the registry only has an AMD64 manifest and the Pod lands on ARM64, the failure appears during image resolution even though the YAML looked syntactically valid.

The OCI Distribution Specification governs the registry API used to move those artifacts. Version 1.1 added the Referrers API shape at `GET /v2/<name>/referrers/<digest>`, which lets registries discover artifacts that refer to a target image digest. That is important for supply-chain metadata because signatures, SBOMs, and attestations can point to an image without mutating the image manifest itself.

At execution time, the OCI Runtime Specification describes how an unpacked bundle is run with namespaces, cgroups, mounts, process settings, and platform-specific configuration. Kubernetes users do not usually write runtime bundles by hand, but the concept is useful: image pulling and container execution are separate phases. A Pod can fail because the image cannot be fetched, or it can fetch successfully and then fail because the configured process cannot run.

Modern tool versions move quickly, so avoid turning release numbers into permanent design assumptions. As of the current module update, OCI Image Spec 1.1.1, OCI Distribution Spec 1.1.1, OCI Runtime Spec 1.3.0, BuildKit 0.29.0, Docker Buildx 0.33.0, Buildah 1.43.0, Podman 5.8.2, and Cosign 3.0.6 are representative current releases. In real platform work, pin the tool version in CI and verify release notes before changing builders or signing policy.

## Dockerfiles Shape Kubernetes Runtime Behavior

A Dockerfile is a build recipe, but several of its choices survive into Kubernetes runtime behavior. The base image defines the starting filesystem, `COPY` and `RUN` create layers, `USER` influences default process identity, and `ENTRYPOINT` plus `CMD` define the process model. Kubernetes can override parts of that model, yet the cleanest Pod specs usually rely on an image that already has sensible defaults.

To leverage modern Dockerfile behavior, the recommended frontend pin for the stable Dockerfile 1.x syntax is `docker/dockerfile:1`. You will often see that directive in production Dockerfiles because it lets builders select a parser and feature set explicitly. The simple Dockerfile below is intentionally plain, but it already shows a cache-aware pattern: copy dependency metadata before copying the rest of the application.

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

Every instruction either changes the filesystem, sets image metadata, or records a default for container startup. `EXPOSE`, for example, documents intended ports but does not publish them in Kubernetes; a Service or Pod port field is still needed for cluster networking. `CMD` records a default argument vector, while `ENTRYPOINT` records the executable that should usually remain stable.

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

The most common runtime confusion is the mapping between Docker terminology and Kubernetes terminology. Dockerfile `ENTRYPOINT` maps to Kubernetes `command`, and Dockerfile `CMD` maps to Kubernetes `args`. The names are unfortunate because `command` sounds like it should map to `CMD`, but it does not. Remember it as executable first, default arguments second.

Pause and predict: in a Kubernetes Pod spec, `command` overrides one Dockerfile instruction and `args` overrides another. If an image uses `ENTRYPOINT ["python"]` and `CMD ["app.py"]`, what field would you change to run `python test.py` without changing the executable?

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

For the prediction above, the clean override is `args: ["test.py"]`. You keep the image's `ENTRYPOINT` as the executable and replace only the default argument. If you set `command: ["test.py"]`, the kubelet asks the runtime to execute `test.py` directly, which fails unless that file is executable and available on the process path.

```yaml
spec:
  containers:
  - name: app
    image: python:3.9
    command: ["python"]    # Overrides ENTRYPOINT
    args: ["myapp.py"]     # Overrides CMD
```

The same distinction helps when debugging Pods that exit immediately. If `kubectl describe pod` shows the image pulled successfully but the container terminates with an executable error, inspect `command` and `args` before rebuilding the image. A Pod-level override can accidentally bypass the image's intended entrypoint even when the Dockerfile itself is correct.

Building and pushing images are not central CKAD exam tasks, but the build cycle explains why registry state and Pod state sometimes disagree. A developer may build `myapp:v1.0.0` locally and forget to push it, or push to a different registry path than the Deployment references. Kubernetes never sees the local build unless the node runtime can pull the same reference.

```bash
# Build in current directory
docker build -t myapp:v1.0.0 .

# Build with specific Dockerfile
docker build -t myapp:v1.0.0 -f Dockerfile.prod .

# Build with build arguments
docker build --build-arg VERSION=1.0.0 -t myapp:v1.0.0 .
```

Tagging and pushing are separate operations, and that separation creates a useful diagnostic habit. If a Pod references `myregistry.com/team/myapp:v1.0.0`, confirm that this exact tag exists in that exact repository path. A successful local `docker images` listing does not prove that a cluster node can authenticate to the registry or fetch that repository.

```bash
# Tag an existing image
docker tag myapp:v1.0.0 myregistry.com/team/myapp:v1.0.0

# Push to registry
docker push myregistry.com/team/myapp:v1.0.0

# Push all tags
docker push --all-tags myregistry.com/team/myapp
```

Multi-stage builds, introduced in Docker Engine 17.05, are the usual way to separate build-time tools from runtime contents. Compile in one stage, copy the final artifact into a smaller image, and leave compilers, package caches, and test fixtures behind. Even when you do not write the full Dockerfile during CKAD practice, recognizing the pattern helps you evaluate image size and attack surface.

## Pull Policy, Registry Credentials, and Node Cache Behavior

After the scheduler assigns a Pod to a node, the kubelet asks the container runtime to make sure the image is available. The runtime may reuse a local image, contact the registry, or fail before the container process starts. `imagePullPolicy` controls that cache decision, and the default depends on the tag shape in the image reference.

```yaml
spec:
  containers:
  - name: app
    image: nginx:1.21.0
    imagePullPolicy: Always  # IfNotPresent | Never | Always
```

The three policies are small, but their operational consequences are large. `Always` asks the runtime to check the registry each time the container starts, which is useful for intentionally mutable tags but expensive for stable versioned images. `IfNotPresent` uses the local cache when available, which is normally right for immutable version tags. `Never` refuses to pull and should be reserved for deliberate local or air-gapped workflows.

| Policy | Behavior | Use When |
|--------|----------|----------|
| `Always` | Pull every time | Using `latest` tag, need freshest image |
| `IfNotPresent` | Pull only if not cached | Specific tags, save bandwidth |
| `Never` | Never pull, use cached | Local development, air-gapped |

Kubernetes chooses defaults to reduce surprise for common cases. If the image uses no tag or explicitly uses `:latest`, the default policy is `Always`. If the image uses a specific tag or a digest, the default policy is `IfNotPresent`. Those defaults are reasonable, but explicit policies are easier to review in manifests that will be maintained by several engineers.

| Image Tag | Default Policy |
|-----------|---------------|
| No tag (implies `:latest`) | `Always` |
| `:latest` | `Always` |
| Specific tag (`:v1.0.0`) | `IfNotPresent` |
| Digest (`@sha256:...`) | `IfNotPresent` |

Node cache behavior is local to the node, not global to the cluster. If one worker has already pulled `myapp:v2.1.0`, that does not help a Pod scheduled on a different worker unless that second node also has the same image content. This is why `IfNotPresent` is safe for stable tags but not a substitute for a registry, a pull-through cache, or a pre-pull strategy in environments where new nodes appear during scaling.

The cache is also not a correctness guarantee. Kubelet image garbage collection can remove unused images when disk pressure crosses configured thresholds, and a newly replaced node starts with an empty local image store. Design deployments so a missing cache causes a normal registry pull, not a startup failure. If the workload requires offline startup, that is a special operating mode that should be documented and tested separately.

`ImagePullBackOff` includes a timing clue as well as a status clue. Kubernetes does not retry a failing pull in a tight loop forever; it backs off between attempts after repeated failures. That protects the registry and the node, but it also means a corrected Secret or tag might not appear instantaneously in Pod status. Reading Events tells you whether the latest retry used the corrected information or whether the Pod is still waiting for the next pull attempt.

One practical habit is to compare the controller image field with the newest Pod image field after every fix. If you patch only a Pod owned by a Deployment, the controller may recreate the old template on the next replacement. Fix the controller, then verify the new ReplicaSet or Pod template carries the corrected image reference.

Before running this, what output do you expect if a Pod uses `image: nginx` and no explicit `imagePullPolicy`? You should expect Kubernetes to treat the image as `nginx:latest` and set the pull policy to `Always`, because a mutable default tag should be checked rather than trusted from a stale node cache.

Private registries add an authentication boundary. Your laptop may be logged in to a registry through Docker, Podman, or a cloud CLI, but Kubernetes worker nodes do not inherit that login. A Pod needs registry credentials through `imagePullSecrets`, or it needs a ServiceAccount that references those credentials so Pods using that account can pull private images.

```bash
# Create docker-registry secret
kubectl create secret docker-registry regcred \
  --docker-server=myregistry.com \
  --docker-username=user \
  --docker-password=your-password-here \
  --docker-email=user@example.com
```

The `docker-registry` Secret type stores credentials in the format Kubernetes expects for image pulls. In production, avoid placing real credentials in shell history or shared documents; use your team's approved secret management flow. In a CKAD-style lab, the command teaches the object shape, and the important part is that the Pod references the Secret by name.

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

Attaching `imagePullSecrets` directly to every Pod works, but it becomes repetitive as soon as a namespace contains several workloads. A cleaner pattern is to attach the pull Secret to a ServiceAccount, then set `serviceAccountName` on Pods that should inherit the registry access. This keeps the image credential policy near the workload identity policy.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
imagePullSecrets:
- name: regcred
```

```yaml
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

For diagnosis, treat registry credentials as node-side requirements. If Events say `unauthorized`, `authentication required`, or `pull access denied`, do not spend the first minutes rewriting the Deployment. Check whether the Pod or ServiceAccount references the Secret, whether the Secret is in the same namespace, and whether the registry server value matches the image reference host.

Docker Hub rate limits are another reason to prefer explicit registry strategy. Public base images are convenient, but unauthenticated pulls can be throttled, and large autoscaling events can make many nodes request the same base layers at once. Pull-through caches, private mirrors, and authenticated registry access reduce that dependency while keeping Pod specs predictable.

## Security and Troubleshooting Start in the Pod Spec

Image security starts before admission control or runtime scanning. If you choose a large base image, run as root, and leave the root filesystem writable, Kubernetes can still run the Pod, but you have shipped unnecessary tools and privileges into every replica. Good image hygiene removes unneeded files, narrows the default process identity, and makes the Pod spec enforce the same assumptions.

```yaml
# BAD
image: nginx:latest

# GOOD
image: nginx:1.21.0-alpine
```

Minimal base images reduce size and vulnerability exposure, but they also change debugging ergonomics. Alpine-based images are small, Debian slim images are often easier for language runtimes, and `scratch` images contain no shell or package manager at all. That tradeoff is normal: production runtime images should not be treated as general-purpose repair environments.

```dockerfile
# 133MB
FROM python:3.9

# 45MB - much smaller
FROM python:3.9-slim

# 17MB - even smaller
FROM python:3.9-alpine
```

The official Alpine Linux image has historically been only a few megabytes, and the 3.23 release branch is current in this module's timeframe. Small does not automatically mean safer, because package choice, update cadence, and vulnerability handling still matter. Treat base image selection as an engineering decision with compatibility, support, and scanning consequences.

`FROM scratch` is the extreme minimal base. It gives you an empty filesystem, which is excellent for statically linked binaries that do not need shell tools, certificates beyond what you copy in, or package manager files. It is a poor fit for applications that expect dynamic libraries, timezone data, certificate bundles, or shell scripts unless you intentionally add those assets.

Distroless and Wolfi-based images sit between full distributions and `scratch`. They aim to remove package managers and shells while keeping enough runtime files for common languages. Evaluate the specific project, update channel, SBOM support, and signing story rather than assuming all minimal images behave the same. The best base image is the smallest one that still supports your runtime contract.

Running as non-root should be part of that contract. A Dockerfile can declare a non-root user, and the Pod spec can enforce that the container must not run as UID zero. When both layers agree, you reduce privilege inside the container and make accidental root execution easier to catch during deployment.

```dockerfile
FROM python:3.9-slim
RUN useradd -m appuser
USER appuser
COPY --chown=appuser:appuser . /app
```

Kubernetes `securityContext` turns image intent into cluster policy at the Pod or container level. `runAsNonRoot: true` causes startup to fail if the image or override would run as root, while `runAsUser` supplies a numeric UID. Numeric users are easier for runtimes to enforce than names, because the image filesystem may or may not contain user database files.

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: myapp:v1.0.0
```

A read-only root filesystem is another powerful guardrail. It forces the application to write only to explicitly mounted locations, such as `/tmp` backed by an `emptyDir`. This quickly exposes applications that quietly write caches, lock files, or generated configuration into the image filesystem instead of using declared storage.

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

Supply-chain security adds evidence around the image. Cosign can sign images, and modern registries can store signatures and related artifacts as OCI referrers connected to the target digest. This matters most when admission policy or release automation verifies that the exact digest has an expected signature, SBOM, or provenance record before allowing the workload to run.

Troubleshooting begins by separating image acquisition from process execution. If the Pod status is `Pending`, `ErrImagePull`, or `ImagePullBackOff`, inspect Events and image fields. If the image pulls and the container enters `CrashLoopBackOff`, move to logs, command arguments, probes, and application behavior. Mixing those paths wastes time because the failure phases are different.

Pause and predict: a Pod references a private registry image but has no `imagePullSecrets`. The image exists and the tag is correct. What error would you expect in Events, and how would that differ from a tag typo? Authentication failures usually mention authorization, while missing tags usually mention manifest lookup or not found errors.

| Error | Cause | Solution |
|-------|-------|----------|
| `ImagePullBackOff` | Can't pull image | Check image name, registry access |
| `ErrImagePull` | Pull failed | Verify image exists, check credentials |
| `InvalidImageName` | Malformed image reference | Fix image name format |
| `ImageInspectError` | Image inspection failed | Check image manifest |

The fastest command is usually `kubectl describe pod`, because Events include messages from the kubelet and runtime. Then inspect the image string exactly as Kubernetes sees it, check whether the pull Secret exists in the namespace, and reproduce the pull from a suitably authenticated environment only after reading the cluster-side error. A laptop pull proves little if the cluster uses different credentials.

```bash
# Check pod events
kubectl describe pod myapp | grep -A10 Events

# Check image name
kubectl get pod myapp -o jsonpath='{.spec.containers[0].image}'

# Verify secret exists
kubectl get secret regcred

# Test pull manually (if docker available)
docker pull myregistry.com/team/myapp:v1.0.0
```

The worked example below follows the exact diagnosis path. The Pod is not failing because NGINX cannot start; it is failing because the runtime cannot find the referenced tag. Once the image reference is corrected, Kubernetes can create a new Pod that pulls a valid image and proceeds to container startup.

```bash
# Pod stuck in ImagePullBackOff
kubectl get pods
# NAME    READY   STATUS             RESTARTS   AGE
# myapp   0/1     ImagePullBackOff   0          5m

# Check events
kubectl describe pod myapp
# Events:
#   Failed to pull image "nginx:latst": rpc error: ...not found

# Found it: typo in tag (latst instead of latest)

# Fix: Edit the pod or delete and recreate
kubectl delete pod myapp
kubectl run myapp --image=nginx:latest
```

## Patterns & Anti-Patterns

Pattern one is to pin intent at the level that matters. Use a full registry path when the workload should not depend on public defaults, use a specific tag when the release process treats tags as immutable, and use a digest when exact binary repeatability is mandatory. This works because reviewers can see the intended source and mutability model in the Pod spec.

The matching anti-pattern is treating `latest` as a release channel. Teams fall into it because it shortens early demos and avoids thinking about versioning, but it makes rollbacks, audits, and incident reconstruction harder. A better alternative is a release tag created by CI, optionally paired with the digest that was promoted through the environment.

Pattern two is to make the registry credential path namespace-local and repeatable. Put the image pull Secret in the same namespace as the workload, attach it to a ServiceAccount used by related Pods, and keep the registry host aligned with the image reference. This scales better than copying Secret references into every manifest by hand.

The matching anti-pattern is debugging private image pulls from a developer laptop first. That laptop has a different credential store, network path, and registry configuration than the node runtime. Start with Pod Events and namespace objects, then use external pulls to confirm registry content only after the cluster-side authentication path is understood.

Pattern three is to order Dockerfile layers by volatility. Copy dependency manifests before application source, install dependencies while those manifests are stable, and copy frequently changing code later. This works because BuildKit and other builders can reuse expensive dependency layers when only application files change.

The matching anti-pattern is placing `COPY . .` near the top of the Dockerfile. It feels simple because the build context is available immediately, but every small source edit invalidates the downstream cache. A better structure copies only package metadata first, installs dependencies, and then copies the rest of the project.

Pattern four is to keep the runtime image smaller than the build environment. Multi-stage builds let a compiler, SDK, or package manager live in a temporary stage while the final image contains only the application and runtime files. That reduces pull time, scanning noise, and the number of tools available to an attacker inside the container.

The matching anti-pattern is shipping a full development image to production because it is easier to inspect. Debuggability matters, but production replicas should not contain compilers and package caches just to make emergency shells convenient. Use ephemeral debug containers, purpose-built diagnostic images, and observability instead of bloating every application image.

Pattern five is to align Dockerfile process defaults with Kubernetes overrides. Put the stable executable in `ENTRYPOINT`, put default arguments in `CMD`, and override only `args` when a Pod needs a different mode. This lets Kubernetes customize behavior without replacing the image's intended process launcher.

The matching anti-pattern is using `command` in every Pod spec out of habit. Overriding `command` replaces the image entrypoint and can bypass setup logic that the image author expected to run. Before changing `command`, inspect the Dockerfile or image metadata and decide whether you really mean to replace the executable.

Pattern six is to fail closed on runtime permissions. Build the image for a non-root user, set `runAsNonRoot`, and mount writable paths explicitly when the root filesystem is read-only. This gives the application a clear contract and turns accidental writes or root assumptions into early deployment failures instead of quiet production drift.

The matching anti-pattern is relying on a vulnerability scanner alone. Scanning is useful evidence, but it does not make a mutable tag reproducible, does not stop a root process, and does not prove that a signature belongs to the digest you deployed. Combine scanning with pinning, signing, admission checks, and Pod security settings.

## Decision Framework

Start with the failure phase. If the Pod cannot pull the image, investigate the reference, tag, registry host, pull policy, credentials, and node access. If the image pulls and the process exits, investigate `command`, `args`, user identity, writable paths, logs, and application configuration. This single split prevents most image debugging sessions from wandering.

Next decide how reproducible the workload must be. For a disposable lab Pod, a short public image tag is acceptable. For a shared development namespace, use an explicit tag and a clear pull policy. For staging and production, prefer an immutable release tag process and record the digest that was promoted, especially when signature verification or SBOM lookup depends on that digest.

Then decide how fresh the node cache should be. `Always` is reasonable for intentionally mutable tags and some development loops, but it creates registry dependency on every start. `IfNotPresent` is normally the right policy for versioned images because it avoids repeated downloads while still bootstrapping new nodes. `Never` belongs only in controlled environments where the image is preloaded.

Now check the registry trust path. Public registries are convenient, but they expose you to external availability, throttling, and naming assumptions. Private registries require `imagePullSecrets`, node identity integration, or cloud-provider mechanisms, but they give teams more control over promotion, mirroring, retention, and access policy. The Pod spec should make that registry path obvious.

After that, examine the image contents. If the image is large, ask whether the runtime really needs the build toolchain, package cache, shell, and distribution utilities. If the application requires dynamic libraries or certificates, do not jump straight to `scratch`; choose the smallest base that still provides the needed runtime files and support model.

Then inspect the process contract. If the image uses `ENTRYPOINT ["python"]` and `CMD ["app.py"]`, Kubernetes `args` can select another script without replacing Python. If the image embeds setup behavior in entrypoint scripts, replacing `command` may skip that behavior. The decision is not whether Kubernetes can override it; the decision is whether overriding it preserves the intended startup contract.

Next apply runtime constraints. Use non-root execution when the application does not require privileged filesystem ownership, and use read-only root filesystems when writable directories are explicit. If the application fails under those settings, the failure is useful information: the image has hidden assumptions that should be documented, mounted, or fixed before production.

Finally, decide what evidence must accompany the image. A low-risk lab image may need only a readable tag. A production image may need a digest, SBOM, vulnerability scan, provenance attestation, and Cosign signature. OCI referrers make those attachments discoverable without changing the image digest, which keeps the verification target stable.

When you are unsure, choose the option that leaves a future investigator with fewer guesses. Fully qualified image names, explicit pull policies, namespace-local Secrets, and digest-aware release records are not ceremonial. They reduce the number of hidden defaults between a YAML manifest and the process that eventually runs on a node.

## Did You Know?

- **OCI image-spec 1.1.0 was the first minor release after the 1.0.0 line from July 2017.** That long interval is one reason image format details tend to be stable across tools even while builders and registries evolve quickly. Source: [OCI Image Spec v1.1.0 release](https://github.com/opencontainers/image-spec/releases/tag/v1.1.0).
- **Docker Engine 23.0 made BuildKit the default builder on Linux in February 2023.** BuildKit's parallel execution and cache model are why modern Dockerfile ordering has a direct effect on build time. Source: [Docker Engine 23.0 release notes](https://docs.docker.com/engine/release-notes/23.0/).
- **Unauthenticated Docker Hub pulls have historically been capped at 100 pulls per 6-hour window.** That number is large for one laptop and small for an autoscaling cluster that repeatedly pulls common base images. Source: [Docker Hub pull usage limits](https://docs.docker.com/docker-hub/usage/pulls/).
- **The `latest` tag has no chronological meaning.** It is only the default tag string used when you omit a tag, so `image: nginx` means `image: nginx:latest` rather than "newest verified release."

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Using `latest` in production | It feels convenient during development, but it hides which image content actually ran | Pin a release tag and record the digest promoted by CI |
| Typos in image names | Registry, namespace, repository, and tag are packed into one string | Read the exact image field and compare it with registry contents |
| Forgetting `imagePullSecrets` | A laptop registry login is mistaken for cluster node access | Add the Secret in the same namespace or attach it to the ServiceAccount |
| Choosing `Never` to avoid slow pulls | Cache misses are mistaken for unnecessary network use | Use `IfNotPresent` for stable tags and pre-pull only in controlled environments |
| Overriding `command` when only arguments should change | Kubernetes names differ from Dockerfile names | Remember `command` maps to `ENTRYPOINT` and `args` maps to `CMD` |
| Copying the whole source tree before dependency installation | A simple Dockerfile is written before cache behavior is considered | Copy dependency manifests first, install dependencies, then copy application code |
| Running as root by default | Base images often start with UID zero unless changed | Set a non-root user in the image and enforce `runAsNonRoot` in the Pod spec |
| Treating scan results as the whole supply-chain story | Vulnerability reports do not prove identity, provenance, or immutability | Combine scans with digest pinning, signatures, SBOMs, and admission policy |

## Quiz

<details>
  <summary>1. Your Deployment uses `image: myapp` and a developer says a new image was pushed, but a restarted Pod still behaves like the old application. What do you check first?</summary>
  Start by expanding the implicit reference: `myapp` means `myapp:latest`, normally from the default registry namespace. Check the exact Pod image field, the registry repository that was pushed, and whether the pushed tag is actually `latest`. The deeper fix is to stop relying on the mutable default and deploy an explicit release tag or digest so the rollout names the intended content.
</details>

<details>
  <summary>2. A Pod is stuck in `ImagePullBackOff`, and the image pulls from your laptop. How do you diagnose the cluster-side cause?</summary>
  Use `kubectl describe pod` and read Events before changing the manifest. If Events mention `unauthorized` or `authentication required`, inspect `imagePullSecrets`, ServiceAccount configuration, namespace placement, and the registry host in the Secret. If Events mention `manifest unknown` or `not found`, inspect the repository path and tag. A laptop pull only proves your laptop has access, not that the node runtime has the same credentials.
</details>

<details>
  <summary>3. An image has `ENTRYPOINT ["python"]` and `CMD ["app.py"]`. In Kubernetes you need to run `python test.py` for one Pod. Which field should you override?</summary>
  Override `args` with `["test.py"]` and leave `command` unset. Kubernetes `command` replaces Dockerfile `ENTRYPOINT`, while Kubernetes `args` replaces Dockerfile `CMD`. Keeping the entrypoint preserves the intended executable, and changing the arguments selects a different script. Replacing `command` with `["test.py"]` would try to execute the script directly.
</details>

<details>
  <summary>4. Your team wants faster restarts for versioned images such as `myapp:v2.1.0`, and someone proposes `imagePullPolicy: Never`. Why is that dangerous?</summary>
  `Never` makes the Pod depend on a preloaded image on every node. It may work on one node and fail immediately when the Deployment scales to a new node, during node replacement, or after disaster recovery. For stable tags, `IfNotPresent` gives the cache benefit while still allowing a node to pull the image when it is missing. If pulls are still slow, investigate registry caching or mirrors rather than disabling pulls completely.
</details>

<details>
  <summary>5. A Dockerfile starts with `FROM ubuntu:latest`, runs `COPY . .`, and then installs dependencies. Builds are slow and the image is large. What two changes give the biggest improvement?</summary>
  First, move dependency metadata such as `requirements.txt` or `package.json` before the full source copy, then install dependencies from that stable layer. This preserves cache reuse when application code changes. Second, choose a smaller supported runtime base such as a slim, Alpine, distroless, Wolfi-based, or multi-stage final image when compatible. Those changes reduce rebuild work and remove unnecessary runtime files.
</details>

<details>
  <summary>6. A mixed ARM64 and AMD64 cluster pulls the same image name on both node types without architecture-specific tags. What OCI mechanism makes that possible?</summary>
  The registry serves an OCI image index, also called a multi-platform manifest list in Docker terminology. The index points to platform-specific manifests, and the node runtime selects the manifest matching the node architecture and operating system. This lets one logical image reference work across node types, as long as the registry contains a compatible manifest for each scheduled platform.
</details>

<details>
  <summary>7. Security policy requires an SBOM and Cosign signature for the exact image digest, but the release team does not want to mutate the image manifest. What registry feature helps?</summary>
  OCI referrers let signatures, SBOMs, and attestations point to a target digest as related artifacts. The target image digest stays stable because the metadata refers to the image instead of being inserted into the image manifest. This is useful for admission controllers and release automation that verify evidence for the exact deployed digest.
</details>

<details>
  <summary>8. A Pod pulls successfully but exits with an executable error after someone added `command: ["worker"]`. Where do you look?</summary>
  Inspect the image's original `ENTRYPOINT` and `CMD`, then compare them with the Pod `command` and `args`. The new `command` replaced the image entrypoint, so it may have skipped a launcher script or tried to execute a binary that is not on the path. If only the worker mode should change, restore the entrypoint and override `args` instead. If the executable really must change, make sure it exists in the image and has the expected permissions.
</details>

## Hands-On Exercise

Exercise scenario: you have been asked to investigate a broken staging deployment and then harden the image-related settings. Work through the tasks in order, because each one isolates a different part of the image lifecycle: reference parsing, pull failure diagnosis, private registry wiring, command overrides, pull policy checks, and Dockerfile optimization.

Use a disposable namespace if your cluster policy requires it, and clean up every object when finished. The commands assume you have `kubectl` configured for a Kubernetes 1.35+ cluster or compatible local environment. If your environment blocks public pulls, read the commands and expected Events as a diagnostic exercise rather than forcing a policy exception.

**Task 1: Setup the broken environment**

```bash
# Create a deployment with intentional image problems
kubectl create deploy broken-app --image=nginx:nonexistent
```

**Task 2: Diagnose the failure**

Observe the state of the deployment to identify the exact cause of the image pull failure. The key skill is not merely seeing `ImagePullBackOff`; it is reading Events until you can explain which part of the image reference failed and what change would let the node pull successfully.

```bash
# Check pod status
kubectl get pods
# Shows ImagePullBackOff

# Get details
kubectl describe pod -l app=broken-app | grep -A5 Events
# Shows: nginx:nonexistent not found

# Fix by patching the deployment
kubectl set image deploy/broken-app nginx=nginx:1.21.0

# Verify
kubectl get pods
# Should show Running

# Cleanup
kubectl delete deploy broken-app
```

**Task 3: Parse image names**

Before changing manifests, practice translating references into their registry, namespace, image, and tag components. This is the mental model you use when Events mention `not found`, because the missing part may be the repository path rather than the final tag.

```text
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

**Task 4: Fix another image pull failure**

This drill repeats the same diagnosis with a Pod instead of a Deployment. Notice that deleting and recreating a standalone Pod is reasonable in a lab, while a managed workload should usually be fixed by patching the controller so replacement Pods inherit the corrected image.

```bash
# Create broken pod
kubectl run broken --image=nginx:1.999.0

# Diagnose
kubectl describe pod broken | grep -A5 Events

# Fix
kubectl delete pod broken
kubectl run broken --image=nginx:1.21.0

# Verify
kubectl get pod broken

# Cleanup
kubectl delete pod broken
```

**Task 5: Wire a private registry Secret**

This task focuses on object shape rather than a real private registry. In a real environment, replace the example server and credentials with approved values from your secret management workflow, and remember that the Secret must be in the same namespace as the Pod that references it.

```bash
# Create registry secret
kubectl create secret docker-registry myregistry \
  --docker-server=private.registry.io \
  --docker-username=testuser \
  --docker-password=your-password-here

# Create pod with secret reference
cat << EOF | kubectl apply -f -
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
kubectl get pod private-pod -o jsonpath='{.spec.imagePullSecrets}'

# Cleanup
kubectl delete pod private-pod
kubectl delete secret myregistry
```

**Task 6: Override command and args**

Use this task to confirm the Dockerfile `ENTRYPOINT`/`CMD` to Kubernetes `command`/`args` mapping in live Pod specs. BusyBox ships with default `CMD ["sh"]` and no fixed `ENTRYPOINT`, so an `args`-only Pod replaces just the default command while leaving the image entrypoint unset. A second Pod sets both fields to show when you fully replace the image process launcher.

```bash
# Part A: args-only override — Kubernetes `args` maps to Dockerfile `CMD`
# Leave `command` unset so the image entrypoint (if any) stays in place.
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: args-only-cmd
spec:
  containers:
  - name: busybox
    image: busybox
    args: ["echo", "Args-only override replaces image CMD"]
EOF

kubectl logs args-only-cmd
kubectl get pod args-only-cmd -o jsonpath='{.spec.containers[0].command}{"\n"}'
kubectl get pod args-only-cmd -o jsonpath='{.spec.containers[0].args}{"\n"}'

# Part B: command+args — replaces Dockerfile ENTRYPOINT and CMD
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: command-and-args
spec:
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c"]
    args: ["echo 'command replaces ENTRYPOINT; args replace CMD' && sleep 5"]
EOF

kubectl logs command-and-args
kubectl get pod command-and-args -o jsonpath='{.spec.containers[0].command}{"\n"}'
kubectl get pod command-and-args -o jsonpath='{.spec.containers[0].args}{"\n"}'

# Cleanup
kubectl delete pod args-only-cmd command-and-args
```

**Task 7: Compare pull policies**

Create two Pods with the same image and different pull policies, then inspect the stored policy values. The point is not to benchmark a registry; it is to build the habit of making cache behavior explicit when a workload has clear reproducibility or freshness requirements.

```bash
# Create pods with different policies
cat << EOF | kubectl apply -f -
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
kubectl get pod pull-always -o jsonpath='{.spec.containers[0].imagePullPolicy}'
kubectl get pod pull-ifnotpresent -o jsonpath='{.spec.containers[0].imagePullPolicy}'

# Cleanup
kubectl delete pod pull-always pull-ifnotpresent
```

**Task 8: Complete image troubleshooting**

This scenario combines controller status, Pod selection, Event inspection, image correction, and rollout verification. Use it as a timed CKAD-style drill: identify the failing image reference, change the controller, and prove the replacement Pod reaches the expected state.

```bash
# Setup (simulating the problem)
kubectl create deploy webapp --image=nginx:alpine-wrong-tag

# YOUR TASK: Find and fix the issue

# Step 1: Check deployment status
kubectl get deploy webapp
kubectl get pods -l app=webapp

# Step 2: Investigate the error
kubectl describe pods -l app=webapp | grep -A10 Events

# Step 3: Find correct image tag
# (In real scenario, check registry or documentation)
# The correct tag is nginx:alpine

# Step 4: Fix
kubectl set image deploy/webapp nginx=nginx:alpine

# Step 5: Verify
kubectl rollout status deploy/webapp
kubectl get pods -l app=webapp

# Cleanup
kubectl delete deploy webapp
```

**Task 9: Optimize a Dockerfile**

This final task moves from cluster diagnosis back to image construction. The original Dockerfile works, but it combines a large base with poor cache ordering. Your rewrite should make the dependency layer stable and use a smaller runtime base when the application is compatible.

```dockerfile
FROM node:18
WORKDIR /usr/src/app
COPY . .
RUN npm install
CMD ["node", "index.js"]
```

Your tasks are to identify the layer caching issue causing slow rebuilds, identify the base image size issue, and rewrite the Dockerfile to optimize it.

```dockerfile
# 1. Switch to a smaller base image (alpine)
FROM node:18-alpine
WORKDIR /usr/src/app

# 2. Copy ONLY package files first for layer caching
COPY package*.json ./
RUN npm install

# 3. Copy the rest of the application code AFTER dependencies
COPY . .
CMD ["node", "index.js"]
```

**Success Criteria:**

- [ ] Diagnosed an `ImagePullBackOff` by reading Pod Events and identifying the failing image reference.
- [ ] Designed a corrected image reference and pull policy that allows the workload to start predictably.
- [ ] Confirmed a private registry Pod references the expected `imagePullSecrets` entry.
- [ ] Compared Kubernetes `command` and `args` with Dockerfile `ENTRYPOINT` and `CMD` behavior in a live Pod.
- [ ] Optimized a Dockerfile for layer caching, smaller base image selection, and cleaner runtime contents.
- [ ] Evaluated whether OCI image indexes, digests, signatures, or referrers would matter for the workload you just debugged.

<details>
  <summary>Solution notes</summary>
  A successful run shows the broken Deployment or Pod entering `ImagePullBackOff`, Events explaining that the requested tag does not exist, and a corrected workload reaching `Running` after the image is changed. The private registry task may still fail to pull because the registry is illustrative, but the Pod spec should show the Secret reference. The args-only task should print `Args-only override replaces image CMD` with an empty `command` field in JSONPath output, while the command-and-args task should print the shell message and show both arrays populated.
</details>

## Learner check

> Observe the state of the deployment to identify the exact cause of the image pull failure. The key skill is not merely seeing `ImagePullBackOff`; it is reading Events until you can explain which part of the image reference failed and what change would let the node pull successfully.

## Sources

- https://kubernetes.io/docs/concepts/containers/images/
- https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/
- https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/
- https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- https://github.com/opencontainers/image-spec/releases/tag/v1.1.0
- https://github.com/opencontainers/image-spec/blob/v1.1.1/spec.md
- https://github.com/opencontainers/image-spec/blob/v1.1.1/media-types.md
- https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md
- https://github.com/opencontainers/runtime-spec/releases/tag/v1.3.0
- https://docs.docker.com/reference/dockerfile/
- https://docs.docker.com/build/building/multi-stage/
- https://docs.docker.com/build/buildkit/
- https://docs.docker.com/engine/release-notes/23.0/
- https://docs.docker.com/docker-hub/usage/pulls/
- https://docs.docker.com/engine/storage/containerd/
- https://docs.sigstore.dev/cosign/
- https://www.alpinelinux.org/releases/

## Next Module

[Module 1.2: Jobs and CronJobs](../module-1.2-jobs-cronjobs/) - Master executing isolated workloads and scheduling resilient batch infrastructure.
