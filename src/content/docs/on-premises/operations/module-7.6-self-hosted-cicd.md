---
title: "Self-Hosted CI/CD"
description: "Architecture, trade-offs, and operational patterns for running Tekton, Gitea Actions, Jenkins, Woodpecker, and Drone on bare-metal Kubernetes."
sidebar:
  order: 76
---

# Self-Hosted CI/CD

## Learning Outcomes

* Compare self-hosted CI/CD platforms based on architecture, resource overhead, and Kubernetes-native integration.
* Implement rootless, unprivileged container image builds using Kaniko or Buildah on bare-metal clusters.
* Configure distributed build caching and artifact storage using internal S3-compatible endpoints (MinIO) and local OCI registries.
* Diagnose runner scheduling failures, persistent volume attachment bottlenecks, and pod eviction loops in dynamic CI environments.
* Design secret injection workflows that decouple credentials from pipeline definitions using External Secrets Operator.
* Route multi-architecture builds to dedicated hardware nodes using node labels and tolerations.

## The Landscape of Self-Hosted CI/CD

Running CI/CD on bare-metal Kubernetes requires shifting from managed, infinite-scale runner pools to finite, cluster-bound compute resources. The primary architectural divide lies between systems designed natively for Kubernetes (where pipelines are CRDs) and systems that use Kubernetes merely as an execution backend for ephemeral workers.

| Platform | Architecture | Pipeline Definition | Memory Footprint (Control Plane) | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Tekton** | Kubernetes-native (CRDs) | YAML (Custom CRDs) | Low (~100MB per controller) | Highly customized, container-native delivery chains. |
| **Gitea Actions** | Server + Polling Agents | YAML (GitHub Actions format) | Low-Medium | Teams migrating from GitHub seeking syntax compatibility. |
| **Jenkins** | Monolithic Master + Ephemeral Pods | Groovy (Jenkinsfile) | High (1GB+ baseline) | Legacy enterprise pipelines requiring massive plugin ecosystems. |
| **Woodpecker CI** | Server + RPC Agents | YAML (Drone-like) | Very Low (<50MB) | Lightweight, container-first workflows tightly coupled to Git events. |
| **Drone** | Server + RPC Agents | YAML (Drone format) | Very Low (<50MB) | Similar to Woodpecker, but subject to Harness enterprise licensing limits. |

### Tekton Pipelines: The CRD Native

Tekton operates without a central CI server. The pipeline state is the Kubernetes etcd state. Execution is managed by custom controllers watching `PipelineRun` and `TaskRun` objects, translating them into standard Kubernetes Pods.

```mermaid
graph TD
    A[Git Webhook] --> B[Tekton Triggers (EventListener)]
    B --> C[TriggerBinding / TriggerTemplate]
    C --> D[PipelineRun CRD Created]
    D --> E[Tekton Controller]
    E --> F[TaskRun CRDs Created]
    F --> G[Pod 1 Created]
    F --> H[Pod N Created]
```

**Operational Characteristics:**
* **Pros:** Complete Kubernetes API integration. RBAC applies directly to pipelines. Highly scalable; controller bottlenecks are rare.
* **Cons:** Extremely verbose YAML. Sharing data between tasks requires `Workspaces` (PersistentVolumeClaims), which can introduce attach/detach latency on bare-metal storage like Ceph or Longhorn.
* **Production Gotcha:** PVC attach limits. If a `PipelineRun` spins up 10 parallel tasks sharing the same `ReadWriteOnce` Workspace, the pods must be scheduled on the same node. If `ReadWriteMany` is used via NFS, I/O bottlenecks quickly degrade build performance.

### Gitea Actions: The Compatibility Layer

Gitea Actions implements a GitHub Actions-compatible engine using `act_runner`. Runners connect to Gitea via gRPC, poll for jobs, and spawn Docker containers or Kubernetes pods.

**Operational Characteristics:**
* **Pros:** Reuses existing GitHub Actions community steps (`uses: actions/checkout@v4`). Familiar syntax.
* **Cons:** The Kubernetes execution environment for `act_runner` creates pods dynamically via the Docker API translation or directly via the Kubernetes API. The translation layer occasionally fails on complex container networking setups (e.g., service containers communicating with the build container).
* **Configuration:** Require configuring `container` contexts explicitly. `act_runner` daemon must have appropriate RBAC to spawn pods in the target namespace.

### Jenkins on Kubernetes (JCasC + Kubernetes Plugin)

Running Jenkins on Kubernetes requires abandoning UI-based configuration. Jenkins Configuration as Code (JCasC) defines the master state, while the Kubernetes plugin dynamically provisions agent Pods.

**Operational Characteristics:**
* **Pros:** Handles extreme edge cases via Groovy scripting.
* **Cons:** The JVM master is a single point of failure and memory hog. Garbage collection pauses on the master can cause missed webhooks or dropped agent connections.
* **Architecture:** The agent pod definition often requires multiple containers (a JNLP agent container to communicate with the master, and specific tool containers like `maven` or `node`).

:::caution
Never mount the host Docker socket (`/var/run/docker.sock`) into Jenkins agents. Use Kaniko, BuildKit daemonsets, or rootless Buildah for image building to maintain cluster security boundaries.
:::

## Core CI/CD Challenges on Bare Metal

### Unprivileged Container Builds

Without Docker, building OCI images inside Kubernetes pods requires user-space build tools.

1. **Kaniko:** Executes Dockerfile instructions completely in userspace. Ideal for standard Dockerfiles.
2. **BuildKit (rootless):** Can be run as a rootless daemon inside a pod or deployed as a shared service (`buildkitd`) within the cluster.
3. **Buildah:** Red Hat's daemonless build tool. Requires specific seccomp profiles or `securityContext.privileged: true` if unprivileged user namespaces are not enabled on the host kernel.

**Kaniko Implementation Detail:**
Kaniko requires the `DOCKER_CONFIG` environment variable to point to a mounted secret containing registry credentials.

```yaml
volumeMounts:
  - name: docker-config
    mountPath: /kaniko/.docker/
```

### Build Caching

Ephemeral CI pods start with cold caches. Downloading dependencies (npm, maven, go modules) and base images for every run destroys pipeline velocity.

* **Distributed Cache Storage:** Deploy an internal S3-compatible object store (MinIO) exclusively for CI caches.
* **Registry Pull-Through Cache:** Configure a local Harbor or Docker Registry instance as a pull-through mirror for `docker.io`, `gcr.io`, and `ghcr.io`. Point containerd on the worker nodes to this mirror.
* **Kaniko Cache:** Kaniko can cache image layers to a remote registry using the `--cache=true` and `--cache-repo=internal-registry:5000/cache` flags.

:::tip
Always configure aggressive lifecycle policies on your cache storage buckets. Orphaned build caches are the leading cause of CI infrastructure storage exhaustion.
:::

### Secret Injection

Hardcoding secrets in CI definitions or relying on the CI tool's native secret manager leads to fragmentation. Synchronize secrets into the CI namespace using External Secrets Operator (ESO), or inject them at runtime using Vault Agent sidecars.

For Tekton, bind secrets directly to the ServiceAccount executing the `TaskRun`.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: build-bot
secrets:
  - name: registry-credentials
```

### Multi-Architecture Builds

Building `arm64` images on `amd64` nodes using QEMU emulation is prohibitively slow for compiled languages (Rust, Go, C++). Bare-metal clusters should utilize native hardware routing.

1. Tag physical `arm64` nodes with `kubernetes.io/arch=arm64`.
2. Apply nodeSelectors or tolerations to the pipeline agents.
3. Build the architecture-specific images natively, push them with unique tags (e.g., `v1.0.0-amd64`, `v1.0.0-arm64`).
4. Execute a final, lightweight manifest-tool job to create and push the multi-arch OCI index (manifest list).

## Hands-on Lab: Tekton Unprivileged Builds with Kaniko

This lab deploys Tekton Pipelines and executes an unprivileged Kaniko build that pushes to a local in-cluster registry.

### Prerequisites

* A running Kubernetes cluster (v1.32+).
* `kubectl` configured.
* A local unsecured registry running in the cluster.

**Step 1: Deploy a local registry**
We need a target for our Kaniko build. Deploy a simple Docker registry.

```bash
kubectl create namespace registry
kubectl apply -n registry -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: registry
spec:
  selector:
    matchLabels:
      app: registry
  template:
    metadata:
      labels:
        app: registry
    spec:
      containers:
      - name: registry
        image: registry:2.8.3
        ports:
        - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: registry
spec:
  selector:
    app: registry
  ports:
  - port: 5000
    targetPort: 5000
EOF
```

Verify the registry is running:
```bash
kubectl get pods -n registry -l app=registry
```

**Step 2: Install Tekton Pipelines**
Apply the current Tekton Pipelines release directly from the release artifact.

```bash
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
```

Wait for the controllers to become ready:
```bash
kubectl wait --for=condition=ready pods -l app.kubernetes.io/part-of=tekton-pipelines -n tekton-pipelines --timeout=90s
```

**Step 3: Create the Kaniko Task**
Define a reusable `Task` that accepts a Git repository URL, clones it, and runs Kaniko.

```yaml
cat <<EOF | kubectl apply -f -
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: kaniko-build
spec:
  params:
    - name: git-url
      type: string
      description: URL of the Git repository
    - name: image
      type: string
      description: Target image reference
  workspaces:
    - name: source
  steps:
    - name: clone
      image: alpine/git:v2.43.0
      script: |
        rm -rf \$(workspaces.source.path)/*
        git clone \$(params.git-url) \$(workspaces.source.path)
    - name: build-and-push
      image: gcr.io/kaniko-project/executor:v1.22.0
      workingDir: \$(workspaces.source.path)
      command:
        - /kaniko/executor
      args:
        - --dockerfile=Dockerfile
        - --context=\$(workspaces.source.path)
        - --destination=\$(params.image)
        - --insecure=true
        - --skip-tls-verify=true
EOF
```

**Step 4: Execute the TaskRun**
Trigger the build. We will use an EmptyDir workspace for this simple test, avoiding PVC provisioning latency. We will build a sample application from a public repository.

```yaml
cat <<EOF | kubectl apply -f -
apiVersion: tekton.dev/v1beta1
kind: TaskRun
metadata:
  generateName: kaniko-run-
spec:
  taskRef:
    name: kaniko-build
  params:
    - name: git-url
      value: https://github.com/GoogleCloudPlatform/microservices-demo.git
    - name: image
      value: registry.registry.svc.cluster.local:5000/email-service:latest
  workspaces:
    - name: source
      emptyDir: {}
EOF
```

**Step 5: Verify Execution**
Find the generated TaskRun name and tail the logs.

```bash
TASKRUN=$(kubectl get taskrun -o jsonpath='{.items[0].metadata.name}')
kubectl get taskrun $TASKRUN
```

Look for the underlying pod created by Tekton:
```bash
POD=$(kubectl get pod -l tekton.dev/taskRun=$TASKRUN -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD -c step-build-and-push -f
```

Expected output:
```text
INFO[0000] Retrieving image manifest golang:1.22.1-alpine 
...
INFO[0012] Pushing image to registry.registry.svc.cluster.local:5000/email-service:latest 
INFO[0012] Pushed registry.registry.svc.cluster.local:5000/email-service@sha256:...
```

**Troubleshooting:**
* If the `clone` step fails with DNS resolution errors, verify your cluster's CoreDNS is functioning.
* If Kaniko fails to push with `connection refused`, ensure the registry Service `registry.registry.svc.cluster.local` is resolving and the registry Pod is `READY`.

## Practitioner Gotchas

1. **PVC Attach/Detach Latency on Workspaces:** When running pipelines that pass state between tasks via PersistentVolumeClaims (PVCs), bare-metal storage classes (like Rook-Ceph block or Longhorn) often take 10-30 seconds to detach a volume from the Node running Task A and attach it to the Node running Task B. This adds massive overhead to multi-step pipelines.
   * *Fix:* Use Node affinity to force all Pods for a specific `PipelineRun` onto the same Node, or switch to S3/GCS API-based artifact passing instead of POSIX mounts.

2. **Dangling Pipeline Resources:** Tekton and Jenkins Kubernetes agents create Pods that are supposed to be cleaned up after execution. Network partitions or OOM kills of the controller can leave `Completed` or `Error` pods lingering permanently, eventually exhausting node inode or IP limits.
   * *Fix:* Configure aggressive Pod GC thresholds on the kubelet, and deploy a CronJob to prune CI namespaces of pods older than 24 hours. For Tekton, configure the `tekton-config-observability` ConfigMap to limit history.

3. **Kaniko Memory Spikes:** Kaniko loads the entire filesystem state into memory during layer calculation. Building large images (e.g., machine learning containers with gigabytes of dependencies) will OOMKill the Kaniko pod if resource limits are set too tightly.
   * *Fix:* Remove memory limits entirely for Kaniko pods, or implement the `--snapshot-mode=redo` flag which trades CPU time for lower memory consumption during file system delta calculation.

4. **Woodpecker/Drone Server SQLite Corruption:** By default, lightweight CI servers often default to local SQLite databases. If scheduled on storage prone to high IO latency or non-graceful pod terminations, the database corrupts, losing all pipeline history and agent registration state.
   * *Fix:* Always configure external Postgres or MySQL databases for the CI control plane on production bare-metal clusters.

## Quiz

**Question 1:**
Your bare-metal Kubernetes cluster uses a Ceph block storage backend. You design a Tekton `Pipeline` with 5 sequential `Tasks`. You define a `Workspace` backed by a `ReadWriteOnce` PVC to share the compiled binary between tasks. You observe that the pipeline takes significantly longer than expected, with pods spending minutes in the `ContainerCreating` state. What is the most likely architectural cause?
A) The Ceph cluster is out of IOPS and throttling the container creation.
B) Tekton is waiting for the previous Task's Pod to be garbage collected before scheduling the next.
C) The PVC must be unmounted from the previous Node and mounted to the new Node for each Task, causing attach/detach latency.
D) The `ReadWriteOnce` access mode requires manual approval from the CSI driver for sequential pod usage.
**Correct Answer:** C

**Question 2:**
You are migrating an existing Jenkins pipeline to Kubernetes using the Jenkins Kubernetes plugin. The legacy pipeline executed `docker build` and `docker push`. To replicate this on your unprivileged bare-metal cluster, which approach maintains cluster security boundaries while accomplishing the goal?
A) Mount `/var/run/docker.sock` from the host node into the Jenkins agent pod and use the Docker CLI.
B) Set `securityContext.privileged: true` on the agent pod and run Docker-in-Docker (DinD).
C) Replace the Docker CLI steps with a Kaniko container execution, providing the registry credentials via a mounted Secret.
D) Expose the kubelet's internal containerd socket to the agent pod via a HostPath volume.
**Correct Answer:** C

**Question 3:**
A developer complains that their CI pipeline running on Gitea Actions fails intermittently with `No space left on device` during the `npm install` phase. The worker node has 500GB of free disk space. The pod is scheduled successfully but terminates mid-execution. What is the most likely cause?
A) The Node's container runtime has exhausted the allocated image filesystem (ephemeral-storage) limit for the pod.
B) The Gitea `act_runner` process has a hardcoded 5GB volume limit for all executions.
C) The Git repository contains too many branches, exceeding the allowed inode count for the clone operation.
D) Kubernetes does not support temporary disk space allocation for CI workloads without a mounted PVC.
**Correct Answer:** A

**Question 4:**
You need to compile an application for both `amd64` and `arm64` architectures. Your bare-metal cluster consists of 10 `amd64` servers and 2 `arm64` servers. What is the most efficient pattern to produce the multi-architecture OCI image?
A) Run QEMU emulation inside a Kaniko pod on an `amd64` node to build both architectures sequentially, then push the manifest.
B) Deploy separate CI agents constrained by `nodeSelector` to specific architectures, build architecture-specific images natively, and combine them with a final manifest-tool job.
C) Configure the Kubernetes control plane to automatically translate `amd64` container instructions to `arm64` using the MutatingAdmissionWebhook.
D) Use Buildah on the `arm64` nodes to cross-compile the binary, copy it via SCP to the `amd64` node, and run `docker build`.
**Correct Answer:** B

**Question 5:**
You deploy an internal S3-compatible storage cluster (MinIO) to serve as a distributed build cache for your CI pipelines. After three months, the MinIO nodes crash due to full disks. You verify that the current active projects only consume 50GB of cache data, but MinIO shows 2TB of utilization. What operational control is missing?
A) The CI pipelines are not running the `minio prune` command at the end of every run.
B) The MinIO bucket lacks a lifecycle management policy to automatically expire and delete old objects.
C) The CI runners are writing to the root filesystem instead of the mounted MinIO volume.
D) Kubernetes PV reclaim policy was set to `Retain` instead of `Delete`.
**Correct Answer:** B

## Further Reading

* [Tekton Architecture](https://tekton.dev/docs/concepts/architecture/)
* [Building Images with Kaniko](https://github.com/GoogleContainerTools/kaniko)
* [Jenkins Kubernetes Plugin Documentation](https://plugins.jenkins.io/kubernetes/)
* [Woodpecker CI Architecture](https://woodpecker-ci.org/docs/architecture)
* [act_runner Configuration](https://docs.gitea.com/usage/actions/act-runner)