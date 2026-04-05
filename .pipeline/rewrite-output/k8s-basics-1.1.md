---
title: "Module 1.1: Your First Cluster"
slug: prerequisites/kubernetes-basics/module-1.1-first-cluster
sidebar:
  order: 2
---

# Module 1.1: Your First Cluster

**Complexity:** [MEDIUM]  
**Time to Complete:** 30-40 minutes  
**Prerequisites:** Docker installed, Cloud Native 101 completed  

## Learning Outcomes

By the end of this module, you will be able to:
- Construct a local Kubernetes environment using declarative configurations to validate application deployments.
- Contrast different local Kubernetes deployment architectures based on host resource constraints and testing requirements.
- Diagnose common cluster initialization failures related to container runtime availability, resource limits, and network port conflicts.
- Design multi-node cluster topologies to simulate production scheduling constraints.

## Why This Module Matters

An infrastructure engineer at a mid-sized e-commerce retailer was tasked with updating the resource allocations for the company's core checkout microservice. The service was occasionally dropping connections, and the hypothesis was that it needed more memory. The engineer edited the Kubernetes deployment manifest, increasing the memory limit. Lacking a functional local Kubernetes environment, they relied on a simple YAML syntax linter and immediately merged the pull request. The CI/CD pipeline picked up the change and deployed it directly to the staging environment, which unfortunately shared a cluster control plane with production. 

The engineer had made a fatal error: they configured a liveness probe with an extremely aggressive interval and timeout, combined with an application startup time that was slightly longer than the probe allowed. The moment the deployment applied, the Kubernetes agent on the nodes began aggressively restarting the application containers before they could ever fully boot. This generated thousands of state change events per minute. The internal state database of the cluster became overwhelmed by the write volume, causing the control plane API to lock up. The scheduling thrash brought down the entire production checkout system for two hours during a high-traffic flash sale. The outage cost the company nearly eight hundred thousand dollars in lost revenue and breached multiple service level agreements.

If that engineer had utilized a local cluster, they could have applied their manifest on their own laptop, witnessed the cascading crash loop within seconds, and debugged the probe configuration in complete isolation. Local clusters are not merely educational playgrounds; they are the absolute first line of defense in the modern deployment pipeline. They provide an isolated, high-fidelity environment where you can break things safely, experiment rapidly, and validate complex distributed configurations without the latency, financial risk, or blast radius of cloud infrastructure. In this module, we will explore the fundamental architecture of a cluster, evaluate the tools available for running one on your workstation, and guide you through constructing and troubleshooting your own isolated environments.

## The Anatomy of a Cluster

Before we build a cluster, we must establish exactly what a Kubernetes cluster is. At its core, Kubernetes is a distributed system designed to automate the deployment, scaling, and management of containerized applications. It achieves this by dividing responsibilities into two distinct domains: the Control Plane and the Worker Nodes.

Think of a Kubernetes cluster like a symphony orchestra. The Control Plane is the conductor. The conductor does not play an instrument; instead, they read the sheet music (your declarative YAML files) and direct the musicians to ensure the music sounds exactly as intended. The Worker Nodes are the musicians. They hold the instruments (your application containers) and perform the actual work of generating the music.

### The Control Plane

The Control Plane makes global decisions about the cluster, responding to cluster events and ensuring the current state matches your desired state. It consists of several critical components:

- **API Server (`kube-apiserver`)**: The front door to the cluster. Every command you run, and every internal component communicating with another, passes through the API server. It exposes a RESTful API and handles authentication, authorization, and validation.
- **etcd**: The memory of the cluster. This is a highly available, distributed key-value store holding the entire state of the cluster. If it is not in etcd, it does not exist in Kubernetes.
- **Scheduler (`kube-scheduler`)**: The stage manager. When you request a new workload to run, the scheduler evaluates the resource requirements of that workload and scans the worker nodes to find a machine with enough available capacity.
- **Controller Manager (`kube-controller-manager`)**: The reconciliation engine. It runs continuous background loops that watch the state of the cluster through the API server and make changes to drive the current state toward the desired state (e.g., replacing a pod if a node fails).

### The Worker Nodes

The Worker Nodes execute the actual application payloads. Every node in a Kubernetes cluster runs the following components:

- **Kubelet**: The lead musician of a section. It is an agent that registers the node with the API server and takes instructions. Its primary job is to ensure that the containers described in a Pod specification are running and healthy on its specific machine.
- **Kube-proxy**: The traffic router. It maintains network rules on the host machine (usually by manipulating `iptables` or IPVS) to allow network communication to your Pods from network sessions inside or outside of your cluster.
- **Container Runtime**: The software responsible for actually pulling the images and running the containers. Historically this was Docker, but modern clusters typically use `containerd` or `CRI-O`.

```text
+-------------------------------------------------------------+
|                     Kubernetes Cluster                      |
|                                                             |
|  +-------------------------------------------------------+  |
|  |                    Control Plane                      |  |
|  |  +-------------+  +-------+  +-----------+ +-------+  |  |
|  |  | API Server  |  | etcd  |  | Scheduler | | C-Mgr |  |  |
|  |  +------+------+  +-------+  +-----------+ +-------+  |  |
|  +---------|---------------------------------------------+  |
|            | (Cluster API)                                  |
|            v                                                |
|  +-----------------------+       +-----------------------+  |
|  |     Worker Node 1     |       |     Worker Node 2     |  |
|  | +---------+ +-------+ |       | +---------+ +-------+ |  |
|  | | Kubelet | | Proxy | |       | | Kubelet | | Proxy | |  |
|  | +----+----+ +-------+ |       | +----+----+ +-------+ |  |
|  |      |                |       |      |                |  |
|  | +----v----+ +-------+ |       | +----v----+ +-------+ |  |
|  | | Pod A   | | Pod B | |       | | Pod C   | | Pod D | |  |
|  | +---------+ +-------+ |       | +---------+ +-------+ |  |
|  +-----------------------+       +-----------------------+  |
+-------------------------------------------------------------+
```

> **Pause and predict:** Based on the architecture described above, what do you think happens to the applications currently running on the worker nodes if the `etcd` database abruptly becomes corrupted or entirely unreachable?

If you predicted that the applications keep running, you are correct. The worker nodes do not constantly query the control plane to keep containers alive. Once the Kubelet has received its instructions, it will maintain those processes locally. However, without the control plane and etcd, the cluster cannot make any new decisions. You cannot deploy new applications, scale existing ones, or automatically recover if a worker node crashes, because the central nervous system is offline.

## The Local Cluster Landscape

Running a full distributed system on a single laptop requires clever engineering. Over the years, several tools have emerged to solve this problem, each taking a different architectural approach. Selecting the right tool depends entirely on your host operating system constraints and what specific behaviors you are trying to test.

| Tool | Architecture Approach | Best Use Case | Primary Drawbacks |
|------|-----------------------|---------------|-------------------|
| **kind** (Kubernetes IN Docker) | Runs entire Kubernetes nodes as nested Docker containers. | CI/CD pipelines, multi-node topology testing, rapid ephemeral environments. | Requires a running Docker daemon; networking integrations can be complex on macOS/Windows. |
| **minikube** | Traditionally boots a full Virtual Machine (VM) to host the cluster (though it now supports containers). | Deep integration testing, utilizing extensive pre-built addons (like Istio or Ingress). | VM overhead can consume significant static RAM and CPU even when idle. |
| **k3d** | A lightweight wrapper around k3s (a stripped-down Kubernetes distribution designed for the edge). | Simulating edge computing, IoT environments, or running on highly constrained hardware. | Uses Traefik instead of standard Nginx ingress by default; strips out some legacy APIs. |
| **Docker Desktop** | A single-click toggle built into the Docker Desktop application. | Absolute beginners who want a zero-configuration, single-node cluster instantly. | Opaque configuration; no native ability to simulate multi-node scheduling or complex topologies. |

For this curriculum, we exclusively utilize **`kind`**. It perfectly balances speed, low resource consumption, and the flexibility to declaratively define complex multi-node environments, making it the industry standard for local infrastructure testing.

## Building Your First Cluster with kind

Under the hood, `kind` performs an impressive trick. Instead of provisioning heavy virtual machines, it utilizes Docker containers to simulate entire bare-metal machines. When you create a node in `kind`, it pulls a specialized Docker image (`kindest/node`) that contains a full `systemd` init process, the `containerd` runtime, and the Kubernetes binaries. It then runs a "Docker within Docker" (or more accurately, containers within a container) setup.

### Step 1: Installation and Creation

Assuming you have Docker installed and running on your system, establishing a cluster requires a single command. The `kind` CLI tool handles the heavy lifting of pulling the node image, configuring the internal certificates, bootstrapping the API server via `kubeadm`, and exposing the API port to your host machine.

```bash
# Create a default, single-node cluster
kind create cluster
```

You will observe output detailing the provisioning lifecycle:

```text
Creating cluster "kind" ...
 ✓ Ensuring node image (kindest/node:v1.35.0) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-kind"
```

Notice the final line of the output. The tool has automatically modified your local `~/.kube/config` file. This file acts as your passport to Kubernetes clusters, containing the necessary cluster addresses, user certificates, and context definitions.

### Step 2: Verification

We verify the cluster's health using `kubectl`, the official command-line interface for communicating with the Kubernetes API server. Engineers type this command hundreds of times a day, so it is an industry standard practice to immediately alias it.

```bash
# Create the alias
alias k=kubectl

# Verify the cluster API is responding
k cluster-info
```

To prove that `kind` is actually running the control plane components we discussed earlier, we can interrogate the `kube-system` namespace. Namespaces are logical partitions within a cluster. Kubernetes places its own critical infrastructure into the `kube-system` partition to separate it from your application workloads.

```bash
k get pods -n kube-system
```

Expected output:
```text
NAME                                         READY   STATUS    RESTARTS   AGE
coredns-6f6b679f8f-2kdfm                     1/1     Running   0          2m
coredns-6f6b679f8f-8j4lk                     1/1     Running   0          2m
etcd-kind-control-plane                      1/1     Running   0          2m
kindnet-v2l4p                                1/1     Running   0          2m
kube-apiserver-kind-control-plane            1/1     Running   0          2m
kube-controller-manager-kind-control-plane   1/1     Running   0          2m
kube-proxy-7q9rz                             1/1     Running   0          2m
kube-scheduler-kind-control-plane            1/1     Running   0          2m
local-path-provisioner-57c5987fd4-9q6z2      1/1     Running   0          2m
```

This output is the heartbeat of your cluster. You can see the `etcd` database, the API server, the scheduler, and the controller manager running as static pods directly on the control plane node. You also see `CoreDNS` (handling internal cluster name resolution) and `kindnet` (the Container Network Interface ensuring pods can route traffic to each other).

## Advanced Cluster Topologies

A single-node cluster is excellent for verifying that an application boots correctly. However, in production, you will have dozens or hundreds of worker nodes. Many advanced Kubernetes features—such as node affinity, pod anti-affinity, and topology spread constraints—dictate how workloads should be distributed across multiple distinct physical machines. You cannot test a rule that says "never place these two pods on the same machine" if you only have one machine.

Because `kind` uses containers as nodes, spinning up additional nodes takes seconds and requires minimal overhead. We accomplish this by passing a declarative YAML configuration file during cluster creation.

Create a file named `multi-node-config.yaml`:

```yaml
# multi-node-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    # We can enforce a specific Kubernetes version by pinning the node image
    image: kindest/node:v1.35.0
  - role: worker
    image: kindest/node:v1.35.0
  - role: worker
    image: kindest/node:v1.35.0
```

To apply this architecture, you must first destroy your existing default cluster to free up the API port, and then instruct `kind` to use your configuration file:

```bash
# Tear down the default cluster
kind delete cluster

# Boot the new multi-node topology
kind create cluster --config multi-node-config.yaml
```

Once the provisioning completes, validating the topology reveals a radically different structure:

```bash
k get nodes
```

```text
NAME                 STATUS   ROLES           AGE     VERSION
kind-control-plane   Ready    control-plane   3m12s   v1.35.0
kind-worker          Ready    <none>          2m45s   v1.35.0
kind-worker2         Ready    <none>          2m45s   v1.35.0
```

You now possess a distributed, multi-node orchestration platform running entirely localized within your workstation's memory space. 

> **Pause and predict:** If you build a custom Docker image on your laptop using `docker build -t my-app:latest .` and then deploy it to this new multi-node `kind` cluster, it will fail with an `ImagePullBackOff` error. Why does the cluster fail to find the image, even though you just built it on the exact same machine?

The failure occurs because `kind` nodes are highly isolated containers. The `containerd` process running inside the `kind-worker` node has absolutely no access to the image cache of the host Docker Engine running on your laptop. To solve this, you must explicitly inject the image archive into the cluster's internal filesystem using the command `kind load docker-image my-app:latest`. 

## Did You Know?

- Kubernetes was originally an internal Google project named "Project Seven", named after the Star Trek character Seven of Nine. This legacy is the reason why the official Kubernetes steering wheel logo possesses exactly seven spokes.
- The `kind` tool was not originally designed for application developers. It was built by the Kubernetes maintainers solely to run the project's own conformance and integration tests within isolated CI environments, eventually becoming popular due to its speed.
- `etcd`, the distributed key-value store backing the control plane, utilizes the Raft consensus algorithm. This algorithm requires a strict mathematical majority (quorum) to operate. This means a three-node control plane can survive the failure of one node, but a two-node control plane cannot survive any failures at all.
- When you delete a resource using `kubectl delete pod`, the API server does not immediately kill the process. It updates the state in `etcd` and sets a deletion timestamp, allowing the Kubelet to intercept the change and gracefully send a `SIGTERM` signal to your application, giving it time to close database connections cleanly.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| **kind fails to connect to Docker daemon** | The `kind` binary requires an active container runtime to spawn its nested nodes. If Docker Desktop or the `dockerd` service is asleep or not started, the command will immediately fail. | Ensure your container runtime application (Docker Desktop, Rancher Desktop, or orbstack) is actively running in your system tray before executing `kind` commands. |
| **Port 6443 already bound** | `kind` attempts to bind the Kubernetes API server to port 6443 on your local machine. If another local cluster (like Docker Desktop's built-in Kubernetes) is already running, the port conflicts. | Stop the conflicting cluster, or use a `kind-config.yaml` to map the `apiServerPort` to an alternative open port, such as 6444. |
| **Control plane crashes randomly** | The host machine lacks sufficient resources. Running nested containers requires memory. If Docker is hard-capped at 2GB of RAM in its settings, the API server will be silently killed by the Linux Out Of Memory (OOM) killer. | Open your Docker Desktop settings and increase the allocated memory limit to an absolute minimum of 4GB, ideally 8GB if running multi-node topologies. |
| **kubectl timing out on cloud clusters** | Executing `kind create cluster` automatically modifies your `~/.kube/config` and forcefully switches your active context to point to localhost, breaking connections to external environments. | Run `kubectl config get-contexts` to find your cloud cluster name, then execute `kubectl config use-context <cloud-context>` to switch back. |
| **Local images throwing `ImagePullBackOff`** | You built a Docker image locally and applied a manifest, but the isolated `containerd` instance inside the `kind` node cannot access your host machine's Docker image cache. | Execute `kind load docker-image <image-name>` to sideload the image directly into the worker nodes' local registry cache. |
| **Deleting the Docker container manually** | A user runs `docker rm -f kind-control-plane` to destroy the cluster. This forcefully kills the node but leaves behind stale, broken certificates in the user's local `kubeconfig` file. | Never manipulate the underlying Docker containers directly. Always utilize `kind delete cluster` to ensure a clean teardown of both infrastructure and configuration files. |

## Quiz

<details>
<summary>1. Your team is migrating from a single-node local setup to a three-node local setup to test pod anti-affinity rules. You execute the creation command, but when you run `kubectl get nodes`, the terminal hangs indefinitely until it eventually throws an API timeout. What is the most likely root cause?</summary>
The host machine lacks sufficient resources (specifically memory) allocated to the Docker Engine. The Docker daemon is struggling to provision and maintain three nested containers simultaneously. The nodes are crashing internally due to OOM (Out of Memory) kills before the control plane can fully initialize the API server. You must increase Docker's resource limits in the application settings.
</details>

<details>
<summary>2. You are participating in a live demonstration and attempt to create a kind cluster. The CLI returns a fatal error indicating that port 6443 is already in use. You cannot reboot your machine, and you are not running any other `kind` clusters. How do you resolve this immediately?</summary>
Another application or background service (most commonly the built-in Kubernetes feature of Docker Desktop or Rancher Desktop) is already running and has claimed the default Kubernetes API port on your localhost interface. You must either dive into the settings of Docker Desktop and disable its internal Kubernetes cluster, or write a quick `kind` configuration file that maps the `apiServerPort` to an alternative port, such as 6444.
</details>

<details>
<summary>3. A junior engineer complains that their new local cluster is extremely sluggish. Running a simple command like `kubectl get pods -A` takes over ten seconds to return, and application deployments frequently time out. They reveal they are running a 5-node topology on a thin laptop. What architectural constraint should you explain to them?</summary>
You must explain the constraint of CPU throttling and disk I/O exhaustion. Running multiple worker nodes in `kind` means running multiple instances of the Kubelet, the container runtime, and various system pods, all fiercely competing for the same limited host CPU cycles. On constrained hardware like a laptop, a single-node cluster is almost always sufficient for functional application testing. Multi-node should only be used temporarily when explicitly testing scheduling constraints.
</details>

<details>
<summary>4. Your company is planning to upgrade production from Kubernetes v1.33 to v1.35. You want to test how your application's custom resource definitions behave on the newer version before approving the upgrade. How can you accomplish this using `kind` without having to download a new version of the `kind` CLI itself?</summary>
You utilize specific node images. The `kind` CLI is decoupled from the Kubernetes version it deploys. You can instruct kind to pull a specific container image containing the newer binaries during cluster creation. You do this by passing a configuration file specifying the image (`kindest/node:v1.35.0`) or by using the command line flag `kind create cluster --image kindest/node:v1.35.0`.
</details>

<details>
<summary>5. You have just finished creating a new local cluster. Immediately after, an alert fires for your production AWS EKS cluster. You run `kubectl get pods -n production` to investigate, but the command returns "No resources found" or a connection timeout. Your cloud provider CLI confirms your IAM credentials are valid. What happened during the local cluster creation?</summary>
The `kind create cluster` command automatically mutates your local `~/.kube/config` file. It injects the new local cluster certificates and automatically switches your current active context to the new `kind` environment. Your `kubectl` tool is functioning perfectly, but it is currently directing your queries to your empty local cluster instead of AWS. You must execute `kubectl config use-context <eks-cluster-name>` to redirect your commands back to the cloud.
</details>

<details>
<summary>6. You deploy a basic Nginx web server to your local cluster using a declarative YAML file. You then open your web browser and navigate to `http://localhost:80`. The browser returns an "Unable to connect" error. Given what you know about the architecture of worker nodes, why does this fail?</summary>
The Nginx container is running successfully, but it is deeply isolated. It is running inside a Pod network, which is inside a simulated Worker Node (a Docker container), which is running on your host machine. There is no automatic network bridge between your host operating system's web browser and the internal Pod network of the cluster. You must explicitly create a tunnel, typically by utilizing a tool like `kubectl port-forward`, to route host traffic into the cluster.
</details>

## Hands-On Exercise

In this exercise, you will master the lifecycle of local cluster management by creating, manipulating, and destroying different architectures, culminating in a troubleshooting scenario.

### Setup

Ensure your container runtime (e.g., Docker Desktop) is running and has at least 4GB of memory allocated in its system settings.

### Tasks

**Task 1: The Default Cluster**
Create a standard, single-node cluster. Once provisioned, execute the command necessary to view all the internal system pods running in the control plane namespace. Verify that the `coredns` pods are in a `Running` state.

<details>
<summary>View Solution for Task 1</summary>

```bash
# Create the cluster
kind create cluster

# Check system pods
kubectl get pods -n kube-system

# You should see two coredns pods showing 1/1 READY and Running status.
```
</details>

**Task 2: Exposing a Workload**
Deploy a simple Nginx pod to your cluster. Because the cluster is isolated inside Docker, you cannot hit its IP directly from your browser. Use `kubectl port-forward` to map port 8080 on your host machine to port 80 on the Nginx pod. Verify by opening `http://localhost:8080` in your browser.

<details>
<summary>View Solution for Task 2</summary>

```bash
# Deploy the pod using an imperative command
kubectl run webserver --image=nginx:alpine

# Wait a few seconds for it to start, then create the tunnel
# This command runs in the foreground, blocking the terminal
kubectl port-forward pod/webserver 8080:80
```
Open a browser to `http://localhost:8080`. You should see the "Welcome to nginx!" screen. Press `Ctrl+C` in your terminal to close the tunnel.
</details>

**Task 3: Declarative Topologies**
Clean up your environment by deleting the default cluster. Create a new directory and create a file named `advanced-cluster.yaml`. Configure this file to deploy a cluster with exactly one control plane node and two worker nodes. Deploy the cluster using this file and verify the node topology.

<details>
<summary>View Solution for Task 3</summary>

```bash
# Destroy the old environment
kind delete cluster

# Create the config file
cat <<EOF > advanced-cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

# Build the multi-node cluster
kind create cluster --config advanced-cluster.yaml

# Verify topology
kubectl get nodes
```
</details>

**Task 4: The Context Switch (Troubleshooting)**
Simulate a corrupted kubeconfig state. Find your active context name, then intentionally switch your context away from your cluster to a non-existent cluster named `broken-context`. Attempt to run `kubectl get nodes`. Finally, use `kubectl` commands to discover the correct context name and switch back to restore access.

<details>
<summary>View Solution for Task 4</summary>

```bash
# Break your access intentionally
kubectl config use-context broken-context
# Output: error: no context exists with the name: "broken-context"

# You might be tempted to guess the name, but let's find it definitively.
# List all available contexts in your configuration file
kubectl config get-contexts

# Identify the context that belongs to kind (usually named 'kind-kind')
kubectl config use-context kind-kind

# Verify access is restored
kubectl get nodes
```
</details>

### Success Criteria

- [ ] I successfully provisioned and destroyed a single-node cluster using the `kind` CLI.
- [ ] I can articulate the difference between the control plane components and the worker node components.
- [ ] I successfully utilized `kubectl port-forward` to bridge network traffic from my local host operating system into the isolated cluster network.
- [ ] I successfully provisioned a multi-node cluster utilizing a declarative YAML configuration file.
- [ ] I can navigate the `kubeconfig` file using `kubectl config` commands to recover from context manipulation errors.

## Next Module

Now that you have a functioning orchestration platform on your laptop, it is time to master the language used to command it. 

[Module 1.2: kubectl Basics](/prerequisites/kubernetes-basics/module-1.2-kubectl-basics/) — Learn to talk to your cluster.
