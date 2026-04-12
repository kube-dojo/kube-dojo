---
title: "Self-Hosted CI/CD"
description: "Architecture, trade-offs, and operational patterns for running Tekton, Gitea Actions, Jenkins, Woodpecker, and Drone on bare-metal Kubernetes."
sidebar:
  order: 76
---

# Self-Hosted CI/CD

## Why This Module Matters

In 2021, a major financial services company suffered a catastrophic software supply chain breach when an advanced persistent threat group compromised their self-hosted CI/CD environment. The attackers exploited a vulnerability in the Docker image creation process, gaining access to a bash uploader script used deep within their automated pipeline. Because the build runners had excessive permissions, operated in privileged mode, and lacked proper namespace isolation, the attackers successfully extracted administrative credentials, deployment tokens, and intellectual property from thousands of customer environments over a period of two months. 

The financial impact of this breach ran into the tens of millions of dollars in external audit fees, complete infrastructure remediation, and lost enterprise contracts. This devastating incident demonstrated definitively that CI/CD infrastructure is not merely an operational convenience or a background development tool; it is the most critical attack surface in a modern software engineering organization. When attackers compromise your CI/CD pipeline, they implicitly gain the keys to your entire production environment and your entire software supply chain.

As organizations scale on-premises Kubernetes architectures, the default approach of relying on managed SaaS runners breaks down rapidly due to strict data sovereignty requirements, exorbitant outbound bandwidth costs, and the need for specialized hardware such as GPUs or custom ARM silicon. Operating a self-hosted CI/CD ecosystem—whether using GitHub Actions runners, GitLab CI, Jenkins, or Kubernetes-native tools like Tekton—demands a rigorous understanding of pod lifecycles, unprivileged container execution, and dynamic volume provisioning. A misconfigured self-hosted runner does not just fail a software build; it provides a direct, privileged vector into your core bare-metal infrastructure.

## Learning Outcomes

* Compare self-hosted CI/CD platforms based on architecture, resource overhead, and Kubernetes-native integration.
* Implement rootless, unprivileged container image builds using Kaniko or Buildah on bare-metal clusters.
* Configure distributed build caching and artifact storage using internal S3-compatible endpoints (MinIO) and local OCI registries.
* Diagnose runner scheduling failures, persistent volume attachment bottlenecks, and pod eviction loops in dynamic CI environments.
* Design secret injection workflows that decouple credentials from pipeline definitions using External Secrets Operator.
* Route multi-architecture builds to dedicated hardware nodes using node labels and tolerations.

## Did You Know?

* **Argo CD Graduation:** The Argo project moved from CNCF incubation to CNCF graduation on December 6, 2022, cementing its status as a mature GitOps standard.
* **Flux Graduation:** Flux moved to CNCF graduation on November 30, 2022 after earlier incubation, providing a strong declarative alternative to Argo CD.
* **Tekton Incubation:** Tekton became a CNCF incubating project and publicly announced that status on March 24, 2026.
* **Runner Expirations:** If automatic updates are disabled, GitHub requires self-hosted runner software updates within 30 days, and jobs are not queued after that.

## The Landscape of Self-Hosted CI/CD

Running CI/CD on bare-metal Kubernetes requires shifting from managed, infinite-scale runner pools to finite, cluster-bound compute resources. The primary architectural divide lies between systems designed natively for Kubernetes (where pipelines are Custom Resource Definitions) and systems that use Kubernetes merely as an execution backend for ephemeral workers.

| Platform | Architecture | Pipeline Definition | Memory Footprint (Control Plane) | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Tekton** | Kubernetes-native (CRDs) | YAML (Custom CRDs) | Low (~100MB per controller) | Highly customized, container-native delivery chains. |
| **Gitea Actions** | Server + Polling Agents | YAML (GitHub Actions format) | Low-Medium | Teams migrating from GitHub seeking syntax compatibility. |
| **Jenkins** | Monolithic Master + Ephemeral Pods | Groovy (Jenkinsfile) | High (1GB+ baseline) | Legacy enterprise pipelines requiring massive plugin ecosystems. |
| **Woodpecker CI** | Server + RPC Agents | YAML (Drone-like) | Very Low (<50MB) | Lightweight, container-first workflows tightly coupled to Git events. |
| **Drone** | Server + RPC Agents | YAML (Drone format) | Very Low (<50MB) | Similar to Woodpecker, but subject to Harness enterprise licensing limits. |

Here is a visual representation of how the Kubernetes-native architecture (specifically Tekton) differs from legacy polling mechanisms. Tekton leverages the Kubernetes control plane directly:

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

## Deep Dive: GitHub Actions Self-Hosted Runners

For teams heavily invested in the GitHub ecosystem, self-hosting runners provides a way to bring execution inside the corporate firewall. A self-hosted GitHub runner is a system that the user deploys and manages. Unlike the ephemeral workers hosted by GitHub, self-hosted GitHub runners are free to use, while infrastructure and maintenance are paid by the runner owner. 

These runners are highly adaptable. Self-hosted GitHub runners can run on physical machines, virtual machines, in containers, on-premises, or in the cloud. The GitHub self-hosted runner OS support includes specific supported Linux, Windows, and macOS versions. At the hardware level, GitHub self-hosted runners support `x64`, preview `ARM64`, and `ARM32` architectures. 

To function correctly, they have strict network requirements. Self-hosted GitHub runners need at least ~70 Kbps throughput, outbound HTTPS/443, and domain access required by the workflow type. The core agent powering this, the GitHub Actions runner application, is open source. 

Maintenance of these runners is critical. Self-hosted runner software updates occur on job assignment or within a week if unused. Security is enforced aggressively: if automatic updates are disabled, GitHub requires self-hosted runner software updates within 30 days, and jobs are not queued after that. 

When a workflow is triggered, GitHub routes self-hosted jobs by `runs-on` labels/groups, re-queues after 60 seconds, and fails queued jobs after 24 hours. For advanced container workloads, GitHub container actions and service containers on self-hosted runners require a Linux runner with Docker installed. 

To run these efficiently in Kubernetes, administrators use the Actions Runner Controller (ARC). GitHub supports ARC legacy and Autoscaling Runner Sets, but only the latest Autoscaling Runner Sets are supported by GitHub. Currently, GitHub states ARC is for OpenShift public preview and requires GitHub Enterprise Server 3.9+. Overall, GitHub positions Actions Runner Controller as the reference implementation for autoscaling self-hosted runners in Kubernetes.

> **Pause and predict**: If a self-hosted GitHub runner relies on outbound HTTPS/443 polling to fetch jobs, what happens to the runner agent if your cluster's NAT gateway IP changes unexpectedly during a workflow execution?

### Gitea Actions: The Compatibility Layer

Gitea Actions implements a GitHub Actions-compatible engine using `act_runner`. Runners connect to Gitea via gRPC, poll for jobs, and spawn Docker containers or Kubernetes pods.

**Operational Characteristics:**
* **Pros:** Reuses existing GitHub Actions community steps (`uses: actions/checkout@v4`). Familiar syntax.
* **Cons:** The Kubernetes execution environment for `act_runner` creates pods dynamically via the Docker API translation or directly via the Kubernetes API. The translation layer occasionally fails on complex container networking setups (e.g., service containers communicating with the build container).
* **Configuration:** Require configuring `container` contexts explicitly. `act_runner` daemon must have appropriate RBAC to spawn pods in the target namespace.

## Deep Dive: GitLab Runner on Kubernetes

GitLab offers a highly robust runner architecture. GitLab Runner executes CI/CD jobs from GitLab pipelines and is managed/owned operationally by the administrator. GitLab distinguishes self-managed runners from GitLab-hosted runners and says self-managed gives full administrative control.

The agent itself is lightweight. GitLab Runner is a single binary application and has no language-specific requirements. Because of this, GitLab Runner supports installation on Linux, FreeBSD, macOS, Windows, and z/OS; plus Docker or Kubernetes-based deployment methods. It also spans various hardware profiles, as GitLab Runner supports architectures including x86, AMD64, ARM64, ARM, s390x, ppc64le, riscv64, and loong64.

Administrators have vast flexibility in how jobs are executed. GitLab Runner supports multiple execution models including shell, Docker, Docker+SSH, Docker-based autoscaling, and remote SSH. In a cluster environment, the GitLab Kubernetes executor creates a Kubernetes pod per CI job and runs builds inside that pod. 

To do this securely, the GitLab Kubernetes executor requires Kubernetes API permissions and service account access to create/list/watch pods and related actions. To avoid strange API mismatches or missing features, GitLab recommends keeping GitLab Runner major.minor versions in sync with GitLab major.minor for compatibility.

## Deep Dive: Jenkins on Kubernetes

When migrating from virtual machines to Kubernetes, teams often attempt to lift-and-shift legacy CI tools like Jenkins. Jenkins uses a distributed architecture of controller, nodes, agents, and executors. The workers themselves, known as Jenkins agents, are Java-based processes that can use any operating system that supports Java. 

Modern deployments avoid static nodes. Jenkins can dynamically allocate agents through systems including Kubernetes. When configured correctly, the Jenkins Kubernetes plugin provisions pods for agents, creating a pod per agent and supporting shared/extra containers via pod templates. Interestingly, Jenkins agents are not required to run inside Kubernetes even when using the Kubernetes plugin—they can communicate with external controllers.

**Operational Characteristics:**
* **Pros:** Handles extreme edge cases via Groovy scripting.
* **Configuration:** Running Jenkins on Kubernetes effectively requires abandoning UI-based configuration; Jenkins Configuration as Code (JCasC) should define the master state.
* **Architecture:** The agent pod definition often requires multiple containers (a JNLP agent container to communicate with the master, and specific tool containers like `maven` or `node`).

However, running a monolithic Jenkins controller inside Kubernetes presents significant operational challenges:
* **Cons:** The JVM master is a single point of failure and memory hog. Garbage collection pauses on the master can cause missed webhooks or dropped agent connections.

To mitigate this, you must explicitly configure `-Xmx` and `-Xms` JVM flags to match your Kubernetes Pod resource limits, preventing the Linux kernel OOM killer from terminating the controller during high load.

## Deep Dive: Tekton Pipelines (CRD Native)

Tekton operates without a central CI server. Tekton is a cloud-native CI/CD framework that runs as an extension on Kubernetes and is defined by Kubernetes Custom Resources. The pipeline state is literally the Kubernetes etcd state. Tekton’s `TaskRun` model is pod-based; by design each TaskRun executes inside a Kubernetes Pod. 

**Operational Characteristics:**
* **Pros:** Complete Kubernetes API integration. RBAC applies directly to pipelines. Highly scalable; controller bottlenecks are extremely rare.
* **Cons:** Extremely verbose YAML syntax. Sharing data between tasks requires `Workspaces` (PersistentVolumeClaims), which can introduce attach/detach latency on bare-metal block storage like Ceph.
* **Production Gotcha:** PVC attach limits. If a `PipelineRun` spins up 10 parallel tasks sharing the same `ReadWriteOnce` Workspace, the pods must be scheduled on the same node.

> **Stop and think**: If Tekton stores pipeline state entirely in `etcd`, what is the risk of retaining 100,000 completed `PipelineRun` objects in a production cluster?

## Deep Dive: GitOps with Argo CD and Flux

CI builds the artifact, but CD deploys it. In modern Kubernetes environments, Continuous Delivery is managed via GitOps. 

Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes. Instead of a CI pipeline pushing changes to the cluster using static credentials, Argo CD uses Git as the source of truth and can track updates from branches, tags, and commits. The tool pulls the desired state and reconciles it against the live cluster state.

Both Argo CD and Flux have become industry standards for CD. The Argo project moved from CNCF incubation to CNCF graduation on December 6, 2022. Similarly, Flux moved to CNCF graduation on November 30, 2022 after earlier incubation. 

## Core CI/CD Challenges on Bare Metal

### Unprivileged Container Builds

Without the Docker daemon, building OCI images inside Kubernetes pods requires user-space build tools.

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
* **Registry Pull-Through Cache:** Configure a local Harbor or Docker Registry instance as a pull-through mirror for `docker.io`, `gcr.io`, and `ghcr.io`. Point containerd on the worker nodes to this mirror to avoid rate limits.
* **Kaniko Cache:** Kaniko can cache image layers to a remote registry using the `--cache=true` and `--cache-repo=internal-registry:5000/cache` flags.

### Secret Injection

Hardcoding secrets in CI definitions or relying on the CI tool's native secret manager leads to security fragmentation. Synchronize secrets into the CI namespace using External Secrets Operator (ESO), or inject them at runtime using Vault Agent sidecars.

For Tekton, you can bind secrets directly to the ServiceAccount executing the `TaskRun`.

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

## Common Mistakes

| Mistake | Why | Fix |
|---|---|---|
| Mounting `/var/run/docker.sock` | Exposes the host kernel directly to the CI pod, leading to instant root privilege escalation. | Use rootless Buildah or Kaniko. |
| Ignoring PVC Attach Latency | Cloud storage takes 10-30s to detach/attach between tasks. | Use Node affinity or object storage for artifacts. |
| Unbounded Build Caches | Ephemeral caches fill up local disks and cause node evictions. | Apply S3 lifecycle policies to prune caches older than 7 days. |
| Hardcoding Secrets in CI | Exposes credentials in logs and YAML definitions. | Use External Secrets Operator to inject secrets via ServiceAccounts. |
| Single-arch builds for ARM | QEMU emulation is over 10x slower for compiled languages. | Route ARM builds to physical ARM nodes via `nodeSelector`. |
| Running Jenkins Masters in pods without tuning | JVM heap limits cause OOMKills during garbage collection. | Set explicit `-Xmx` and `-Xms` flags matching pod limits. |

## Hands-on Lab: Tekton Unprivileged Builds with Kaniko

This lab deploys Tekton Pipelines and executes an unprivileged Kaniko build that pushes to a local in-cluster registry at `registry.registry.svc.cluster.local`. 

### Prerequisites

To begin, ensure you have these prerequisites:
* A running Kubernetes cluster (v1.32+).
* `kubectl` configured.
* A local unsecured registry running in the cluster.

<details>
<summary>Task 1: Deploy a local registry</summary>

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
</details>

<details>
<summary>Task 2: Install Tekton Pipelines</summary>

Apply the current Tekton Pipelines release directly from the release artifact.

```bash
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
```

Wait for the controllers to become ready:
```bash
kubectl wait --for=condition=ready pods -l app.kubernetes.io/part-of=tekton-pipelines -n tekton-pipelines --timeout=90s
```
</details>

<details>
<summary>Task 3: Create the Kaniko Task</summary>

Define a reusable `Task` that accepts a Git repository URL, clones it, and runs Kaniko. Note we are using `v1.22.0` of Kaniko in this specific example. 

```bash
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
</details>

<details>
<summary>Task 4: Execute the TaskRun</summary>

Trigger the build. We will use an EmptyDir workspace for this simple test, avoiding PVC provisioning latency. We will build a sample application from a public repository.

```bash
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
</details>

<details>
<summary>Task 5: Verify Execution</summary>

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
</details>

**Troubleshooting:**
* If the `clone` step fails with DNS resolution errors, verify your cluster's CoreDNS is functioning.
* If Kaniko fails to push with `connection refused`, ensure the registry Service `registry.registry.svc.cluster.local` is resolving and the registry Pod is `READY`.

**Practitioner Gotchas:**
1. **PVC Attach/Detach Latency on Workspaces:** When running pipelines that pass state between tasks via PersistentVolumeClaims (PVCs), bare-metal storage classes (like Rook-Ceph block or Longhorn) often take 10-30 seconds to detach a volume from the Node running Task A and attach it to the Node running Task B. This adds massive overhead to multi-step pipelines. *Fix:* Use Node affinity to force all Pods for a specific `PipelineRun` onto the same Node, or switch to S3/GCS API-based artifact passing instead of POSIX mounts. If `ReadWriteMany` is used via NFS to bypass this, I/O bottlenecks will quickly degrade build performance.
2. **Dangling Pipeline Resources:** Tekton and Jenkins Kubernetes agents create Pods that are supposed to be cleaned up after execution. Network partitions or OOM kills of the controller can leave `Completed` or `Error` pods lingering permanently, eventually exhausting node inode or IP limits. *Fix:* Configure aggressive Pod GC thresholds on the kubelet, and deploy a CronJob to prune CI namespaces of pods older than 24 hours. For Tekton, configure the `tekton-config-observability` ConfigMap to limit history.
3. **Kaniko Memory Spikes:** Kaniko loads the entire filesystem state into memory during layer calculation. Building large images (e.g., machine learning containers with gigabytes of dependencies) will OOMKill the Kaniko pod if resource limits are set too tightly. *Fix:* Remove memory limits entirely for Kaniko pods, or implement the `--snapshot-mode=redo` flag which trades CPU time for lower memory consumption during file system delta calculation.
4. **Woodpecker/Drone Server SQLite Corruption:** By default, lightweight CI servers often default to local SQLite databases. If scheduled on storage prone to high IO latency or non-graceful pod terminations, the database corrupts, losing all pipeline history and agent registration state. *Fix:* Always configure external Postgres or MySQL databases for the CI control plane on production bare-metal clusters.

## Quiz

<details>
<summary>Question 1: Your bare-metal Kubernetes cluster uses a Ceph block storage backend. You design a Tekton `Pipeline` with 5 sequential `Tasks`. You define a `Workspace` backed by a `ReadWriteOnce` PVC to share the compiled binary between tasks. You observe that the pipeline takes significantly longer than expected, with pods spending minutes in the `ContainerCreating` state. What is the most likely architectural cause?</summary>

A) The Ceph cluster is out of IOPS and throttling the container creation.
B) Tekton is waiting for the previous Task's Pod to be garbage collected before scheduling the next.
C) The PVC must be unmounted from the previous Node and mounted to the new Node for each Task, causing attach/detach latency.
D) The `ReadWriteOnce` access mode requires manual approval from the CSI driver for sequential pod usage.

**Answer:** C) The PVC must be unmounted from the previous Node and mounted to the new Node for each Task, causing attach/detach latency.

**Explanation:** In a multi-node bare metal cluster using block storage, a `ReadWriteOnce` volume can only be attached to a single node at a time. Tekton creates a new Pod for every Task execution. If the new Task is scheduled on a different node than the previous Task, the storage orchestrator must forcefully detach the volume from Node A and attach it to Node B. This CSI orchestration inevitably introduces significant delay compared to local volume mounts. It is highly unlikely that B) Tekton is waiting for the previous Task's Pod to be garbage collected before scheduling the next.
</details>

<details>
<summary>Question 2: You are migrating an existing Jenkins pipeline to Kubernetes using the Jenkins Kubernetes plugin. The legacy pipeline executed `docker build` and `docker push`. To replicate this on your unprivileged bare-metal cluster, which approach maintains cluster security boundaries while accomplishing the goal?</summary>

A) Mount `/var/run/docker.sock` from the host node into the Jenkins agent pod and use the Docker CLI.
B) Set `securityContext.privileged: true` on the agent pod and run Docker-in-Docker (DinD).
C) Replace the Docker CLI steps with a Kaniko container execution, providing the registry credentials via a mounted Secret.
D) Expose the kubelet's internal containerd socket to the agent pod via a HostPath volume.

**Answer:** C) Replace the Docker CLI steps with a Kaniko container execution, providing the registry credentials via a mounted Secret.

**Explanation:** Mounting the host's Docker socket into a pod gives that pod root-level access to the underlying Kubernetes node, entirely bypassing container isolation. Privileged containers running Docker-in-Docker present similar critical security risks. Kaniko solves this by executing Dockerfile build instructions entirely in user space without requiring a daemon, ensuring that your CI workloads remain unprivileged and isolated from the host operating system.
</details>

<details>
<summary>Question 3: A developer complains that their CI pipeline running on Gitea Actions fails intermittently with `No space left on device` during the `npm install` phase. The worker node has 500GB of free disk space. The pod is scheduled successfully but terminates mid-execution. What is the most likely cause?</summary>

A) The Node's container runtime has exhausted the allocated image filesystem (ephemeral-storage) limit for the pod.
B) The Gitea `act_runner` process has a hardcoded 5GB volume limit for all executions.
C) The Git repository contains too many branches, exceeding the allowed inode count for the clone operation.
D) Kubernetes does not support temporary disk space allocation for CI workloads without a mounted PVC.

**Answer:** A) The Node's container runtime has exhausted the allocated image filesystem (ephemeral-storage) limit for the pod.

**Explanation:** Kubernetes limits the amount of local ephemeral storage a pod can use based on its resource requests and limits. Even if the underlying physical node has hundreds of gigabytes of free disk space, if the pod exceeds its defined `ephemeral-storage` limit while downloading heavy `node_modules`, the kubelet will aggressively evict and terminate the pod to protect the node's disk integrity.
</details>

<details>
<summary>Question 4: You need to compile an application for both `amd64` and `arm64` architectures. Your bare-metal cluster consists of 10 `amd64` servers and 2 `arm64` servers. What is the most efficient pattern to produce the multi-architecture OCI image?</summary>

A) Run QEMU emulation inside a Kaniko pod on an `amd64` node to build both architectures sequentially, then push the manifest.
B) Deploy separate CI agents constrained by `nodeSelector` to specific architectures, build architecture-specific images natively, and combine them with a final manifest-tool job.
C) Configure the Kubernetes control plane to automatically translate `amd64` container instructions to `arm64` using the MutatingAdmissionWebhook.
D) Use Buildah on the `arm64` nodes to cross-compile the binary, copy it via SCP to the `amd64` node, and run `docker build`.

**Answer:** B) Deploy separate CI agents constrained by `nodeSelector` to specific architectures, build architecture-specific images natively, and combine them with a final manifest-tool job.

**Explanation:** While you technically could run QEMU emulation on an `amd64` machine to build an `arm64` image, the translation overhead makes it prohibitively slow for compiled languages. The most efficient and scalable approach is to route the workloads directly to their native hardware using Kubernetes scheduling primitives like `nodeSelector`. It is not feasible to C) Configure the Kubernetes control plane to automatically translate `amd64` container instructions to `arm64` using the MutatingAdmissionWebhook.
</details>

<details>
<summary>Question 5: You deploy an internal S3-compatible storage cluster (MinIO) to serve as a distributed build cache for your CI pipelines. After three months, the MinIO nodes crash due to full disks. You verify that the current active projects only consume 50GB of cache data, but MinIO shows 2TB of utilization. What operational control is missing?</summary>

A) The CI pipelines are not running the `minio prune` command at the end of every run.
B) The MinIO bucket lacks a lifecycle management policy to automatically expire and delete old objects.
C) The CI runners are writing to the root filesystem instead of the mounted MinIO volume.
D) Kubernetes PV reclaim policy was set to `Retain` instead of `Delete`.

**Answer:** B) The MinIO bucket lacks a lifecycle management policy to automatically expire and delete old objects.

**Explanation:** Build caches generate massive amounts of ephemeral data as branches are created, built, and merged. Without an aggressive object lifecycle policy (e.g., deleting objects older than 7 days) configured at the S3 bucket level, orphaned caches from deleted branches will accumulate indefinitely until the storage cluster is entirely exhausted.
</details>

## Next Module

Now that you have established a secure, unprivileged CI pipeline capable of building OCI images natively in Kubernetes, the next step is securely storing and distributing those artifacts. Proceed to [Module 7.7: Private Registry Operations](/docs/operations/module-7.7-private-registries) to learn how to deploy and secure Harbor on bare metal, implement vulnerability scanning, and configure pull-through caches for your worker nodes.

## Further Reading

* [Tekton Architecture Overview](https://tekton.dev/docs/concepts/overview/)
* [Building Images with Kaniko](https://github.com/GoogleContainerTools/kaniko)
* [Jenkins Kubernetes Plugin Documentation](https://plugins.jenkins.io/kubernetes/)
* [Woodpecker CI Architecture](https://woodpecker-ci.org/docs/architecture)
* [act_runner Configuration](https://docs.gitea.com/usage/actions/act-runner)