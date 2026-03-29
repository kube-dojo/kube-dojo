---
title: "Module 1.1: Your First Cluster"
slug: prerequisites/kubernetes-basics/module-1.1-first-cluster/
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Hands-on setup required
>
> **Time to Complete**: 30-40 minutes
>
> **Prerequisites**: Docker installed, Cloud Native 101 completed

---

## Why This Module Matters

Before you can learn Kubernetes, you need a Kubernetes cluster. This module gets you a working local cluster in minutes, so you can start practicing immediately.

We'll use **kind** (Kubernetes in Docker)—it's fast, lightweight, and perfect for learning.

---

## Cluster Options

### For Learning (Local)

| Tool | Pros | Cons |
|------|------|------|
| **kind** | Fast, lightweight, multi-node possible | Requires Docker |
| **minikube** | Feature-rich, multiple drivers | Heavier, more setup |
| **k3d** | k3s in Docker, very fast | Slightly different from standard K8s |
| **Docker Desktop** | Easy if you have it | Limited configuration |

### For Production (Managed)

| Service | Provider |
|---------|----------|
| EKS | AWS |
| GKE | Google Cloud |
| AKS | Azure |

**Recommendation**: Use **kind** for this curriculum. It matches exam environments well.

---

## Installing kind

### macOS

```bash
# Using Homebrew
brew install kind

# Or download binary
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-darwin-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Linux

```bash
# Download binary
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Windows

```powershell
# Using Chocolatey
choco install kind

# Or download from:
# https://kind.sigs.k8s.io/dl/latest/kind-windows-amd64
```

### Verify Installation

```bash
kind version
# kind v0.20.0 go1.20.4 darwin/amd64
```

---

## Installing kubectl

kubectl is the command-line tool for interacting with Kubernetes.

### macOS

```bash
# Using Homebrew
brew install kubectl

# Or download binary
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
```

### Linux

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
```

### Verify Installation

```bash
kubectl version --client
# Client Version: v1.28.0
```

---

## Creating Your First Cluster

### Simple Single-Node Cluster

```bash
# Create cluster
kind create cluster

# Output:
# Creating cluster "kind" ...
#  ✓ Ensuring node image (kindest/node:v1.27.3) 🖼
#  ✓ Preparing nodes 📦
#  ✓ Writing configuration 📜
#  ✓ Starting control-plane 🕹️
#  ✓ Installing CNI 🔌
#  ✓ Installing StorageClass 💾
# Set kubectl context to "kind-kind"
```

### Verify It Works

```bash
# Check cluster info
kubectl cluster-info
# Kubernetes control plane is running at https://127.0.0.1:xxxxx

# List nodes
kubectl get nodes
# NAME                 STATUS   ROLES           AGE   VERSION
# kind-control-plane   Ready    control-plane   60s   v1.27.3

# Check all pods (system)
kubectl get pods -A
# Shows kube-system pods running
```

---

## Multi-Node Cluster (Optional)

For more realistic testing, create a multi-node cluster:

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
```

```bash
# Create multi-node cluster
kind create cluster --config kind-config.yaml --name multi-node

# Verify
kubectl get nodes
# NAME                       STATUS   ROLES           AGE   VERSION
# multi-node-control-plane   Ready    control-plane   60s   v1.27.3
# multi-node-worker          Ready    <none>          30s   v1.27.3
# multi-node-worker2         Ready    <none>          30s   v1.27.3
```

---

## Managing Clusters

```bash
# List clusters
kind get clusters

# Delete cluster
kind delete cluster                    # Delete "kind" cluster
kind delete cluster --name multi-node  # Delete named cluster

# Get cluster kubeconfig
kind get kubeconfig --name kind

# Export kubeconfig (if needed)
kind export kubeconfig --name kind
```

---

## Understanding What You Have

```
┌─────────────────────────────────────────────────────────────┐
│              YOUR KIND CLUSTER                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Docker Container                        │   │
│  │              "kind-control-plane"                    │   │
│  │                                                     │   │
│  │    ┌───────────────────────────────────────────┐   │   │
│  │    │         Control Plane                     │   │   │
│  │    │  ┌─────────┐ ┌──────────┐ ┌───────────┐  │   │   │
│  │    │  │   API   │ │Scheduler │ │Controller │  │   │   │
│  │    │  │ Server  │ │          │ │  Manager  │  │   │   │
│  │    │  └─────────┘ └──────────┘ └───────────┘  │   │   │
│  │    │           ┌──────────┐                    │   │   │
│  │    │           │   etcd   │                    │   │   │
│  │    │           └──────────┘                    │   │   │
│  │    └───────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │    ┌───────────────────────────────────────────┐   │   │
│  │    │         Worker (same container)           │   │   │
│  │    │  ┌─────────┐ ┌──────────┐                │   │   │
│  │    │  │ kubelet │ │Container │                │   │   │
│  │    │  │         │ │ Runtime  │                │   │   │
│  │    │  └─────────┘ └──────────┘                │   │   │
│  │    │                                           │   │   │
│  │    │  Your pods will run here                 │   │   │
│  │    └───────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  The entire K8s cluster runs inside one Docker container    │
│  (or multiple for multi-node clusters)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## First Commands

Now that you have a cluster, try these commands:

```bash
# See what's running in the cluster
kubectl get pods -A

# Get more detail on nodes
kubectl describe node kind-control-plane

# Check component health (componentstatuses is deprecated; use this instead)
kubectl get --raw='/readyz?verbose'

# View cluster events
kubectl get events -A
```

---

## Troubleshooting

### "Cannot connect to the Docker daemon"

```bash
# Ensure Docker is running
docker info

# If using Docker Desktop, make sure it's started
```

### "kind: command not found"

```bash
# Verify kind is in PATH
which kind

# If not, add to PATH or reinstall
```

### "kubectl: connection refused"

```bash
# Ensure cluster is running
kind get clusters
docker ps  # Should show kind container

# Check kubeconfig context
kubectl config current-context
# Should show "kind-kind" or your cluster name
```

---

## Did You Know?

- **kind stands for "Kubernetes in Docker."** It runs K8s nodes as Docker containers instead of VMs.

- **kind was created for testing Kubernetes itself.** The K8s project uses it to test K8s. It's reliable enough for that.

- **Each kind node is a Docker container** running systemd, kubelet, and containerd inside it.

- **kind clusters persist across Docker restarts.** Your cluster survives reboots (unless you delete it).

---

## Quiz

1. **What is kind?**
   <details>
   <summary>Answer</summary>
   Kind (Kubernetes in Docker) is a tool for running local Kubernetes clusters using Docker containers as nodes. It's lightweight, fast, and ideal for development and learning.
   </details>

2. **What command creates a kind cluster?**
   <details>
   <summary>Answer</summary>
   `kind create cluster` creates a single-node cluster. Use `--config` flag with a YAML file for multi-node clusters. Use `--name` for custom cluster names.
   </details>

3. **How do you verify your cluster is working?**
   <details>
   <summary>Answer</summary>
   Run `kubectl get nodes` to see nodes, `kubectl cluster-info` to see cluster endpoints, or `kubectl get pods -A` to see all system pods running.
   </details>

4. **How do you delete a kind cluster?**
   <details>
   <summary>Answer</summary>
   `kind delete cluster` deletes the default cluster. Use `--name cluster-name` to delete a specific named cluster.
   </details>

---

## Hands-On Exercise

**Task**: Create, verify, and delete a cluster.

```bash
# 1. Create a cluster
kind create cluster --name practice

# 2. Verify nodes are ready
kubectl get nodes

# 3. List all pods in cluster
kubectl get pods -A

# 4. View cluster info
kubectl cluster-info

# 5. Delete the cluster
kind delete cluster --name practice

# 6. Verify it's gone
kind get clusters
```

**Success criteria**: All commands complete without error.

---

## Summary

You now have a working Kubernetes cluster:

**Tools installed**:
- kind - Creates local K8s clusters
- kubectl - CLI for interacting with K8s

**Key commands**:
- `kind create cluster` - Create cluster
- `kind delete cluster` - Delete cluster
- `kubectl get nodes` - Verify cluster

You're ready to start working with Kubernetes!

---

## Next Module

[Module 2: kubectl Basics](module-1.2-kubectl-basics/) - Your command-line interface to Kubernetes.
