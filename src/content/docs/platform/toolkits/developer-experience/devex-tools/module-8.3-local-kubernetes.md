---
title: "Module 8.3: Local Kubernetes"
slug: platform/toolkits/developer-experience/devex-tools/module-8.3-local-kubernetes
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[QUICK]` | Time: 30-35 minutes

## Overview

Before you can develop for Kubernetes, you need Kubernetes. But you don't need a cloud account or a production cluster—you need a local, disposable environment for learning and testing. This module covers kind, minikube, and other local Kubernetes options for development.

**What You'll Learn**:
- Local Kubernetes options comparison
- kind for multi-node development clusters
- minikube for feature-rich local K8s
- Docker Desktop Kubernetes for simplicity

**Prerequisites**:
- Docker installed
- Basic Kubernetes concepts
- Terminal/CLI familiarity

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy local Kubernetes clusters using kind, minikube, and Docker Desktop with optimal configurations**
- **Configure local clusters with ingress controllers, registries, and multi-node topologies for realistic testing**
- **Implement local development workflows that mirror production Kubernetes environments accurately**
- **Compare local Kubernetes tools for CI/CD testing, application development, and learning scenarios**


## Why This Module Matters

Cloud Kubernetes costs money and has latency. Local Kubernetes is free and instant. For learning, testing, and development, local clusters are essential. The question isn't whether to use local K8s—it's which tool fits your needs.

> 💡 **Did You Know?** kind (Kubernetes IN Docker) was originally created to test Kubernetes itself. The Kubernetes project uses kind in its CI/CD to test Kubernetes against Kubernetes. It became so useful that developers adopted it for local development, and now it's one of the most popular tools for running local clusters.

---

## Tool Comparison

```
LOCAL KUBERNETES OPTIONS
════════════════════════════════════════════════════════════════════

                   kind           minikube         Docker Desktop
─────────────────────────────────────────────────────────────────
Multi-node         ✓✓             ✓                ✗
Speed              Fast           Medium           Fast
Resources          Low            Medium           Low
GPU support        ✗              ✓                ✓
LoadBalancer       Manual         Built-in         Built-in
Ingress            Manual         Addon            Manual
Container runtime  Docker         Multiple         Docker
Persistence        ✗*             ✓                ✓
Best for           CI/CD, testing Learning, addons Quick start
─────────────────────────────────────────────────────────────────

* kind clusters are ephemeral by design
```

### When to Use What

```
DECISION TREE
════════════════════════════════════════════════════════════════════

Need Kubernetes for what?
│
├── CI/CD testing
│   └──▶ kind (fast, ephemeral, multi-node)
│
├── Learning/tutorials
│   └──▶ minikube (addons, good docs)
│
├── Just need it to work
│   └──▶ Docker Desktop (already installed)
│
├── Multi-node testing
│   └──▶ kind (easy multi-node)
│
├── GPU/ML development
│   └──▶ minikube (GPU support)
│
└── Team standardization
    └──▶ Any (pick one, share configs)
```

---

## kind (Kubernetes IN Docker)

### Installation

```bash
# macOS
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify
kind version
```

### Basic Usage

```bash
# Create cluster
kind create cluster

# Create with name
kind create cluster --name my-cluster

# List clusters
kind get clusters

# Delete cluster
kind delete cluster --name my-cluster

# Get kubeconfig
kind get kubeconfig --name my-cluster
```

### Multi-Node Cluster

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
- role: worker
```

```bash
kind create cluster --config kind-config.yaml
```

### Ingress Setup

```yaml
# kind-config-ingress.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
```

```bash
# Create cluster with ingress support
kind create cluster --config kind-config-ingress.yaml

# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

### Loading Local Images

```bash
# Build image locally
docker build -t myapp:dev .

# Load into kind cluster
kind load docker-image myapp:dev

# Now you can use myapp:dev in your pods
# No registry needed!
```

> 💡 **Did You Know?** kind runs Kubernetes nodes as Docker containers. This means you can have a 3-node cluster using a few hundred MB of memory, all within Docker. It's how the Kubernetes project tests releases—if it's good enough for Kubernetes CI, it's good enough for development.

---

## minikube

### Installation

```bash
# macOS
brew install minikube

# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Verify
minikube version
```

### Basic Usage

```bash
# Start cluster
minikube start

# Start with specific resources
minikube start --cpus 4 --memory 8192

# Start with specific driver
minikube start --driver=docker

# Check status
minikube status

# Stop cluster
minikube stop

# Delete cluster
minikube delete

# SSH into node
minikube ssh
```

### Addons

```bash
# List available addons
minikube addons list

# Enable addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Access dashboard
minikube dashboard

# Disable addon
minikube addons disable dashboard
```

### Accessing Services

```bash
# Get service URL
minikube service myapp --url

# Open service in browser
minikube service myapp

# Tunnel for LoadBalancer services
minikube tunnel

# Access via NodePort
minikube ip  # Get node IP
```

### Multi-Node minikube

```bash
# Start with multiple nodes
minikube start --nodes 3

# Add node to existing cluster
minikube node add

# Delete specific node
minikube node delete minikube-m02
```

### Profiles (Multiple Clusters)

```bash
# Create cluster with profile
minikube start -p dev-cluster
minikube start -p test-cluster

# List profiles
minikube profile list

# Switch profile
minikube profile dev-cluster

# Delete profile
minikube delete -p test-cluster
```

> 💡 **Did You Know?** minikube supports multiple "drivers" for virtualization: Docker, VirtualBox, Hyperkit, KVM, and even bare-metal. On macOS, the Docker driver is fastest because it doesn't need a VM. On Linux, you can run minikube directly on the host with the "none" driver for maximum performance.

> 💡 **Did You Know?** minikube's addons system is more extensive than most realize—there are 60+ addons available. Beyond the common ones (ingress, dashboard, metrics-server), you can enable Istio, Ambassador, registry, and even GPU support with single commands. It's like having a curated marketplace of Kubernetes extensions, pre-configured to work together.

---

## Docker Desktop Kubernetes

### Enabling Kubernetes

```
Docker Desktop → Settings → Kubernetes → Enable Kubernetes
```

### Features

```bash
# No special commands - just works
kubectl get nodes
# NAME             STATUS   ROLES           AGE   VERSION
# docker-desktop   Ready    control-plane   10m   v1.28.2

# Reset if needed
Docker Desktop → Settings → Kubernetes → Reset Kubernetes Cluster
```

### Limitations

- Single node only
- Can't customize node configuration
- Tied to Docker Desktop lifecycle
- Limited resource control

### When It's Perfect

- You already have Docker Desktop
- Single-node is sufficient
- Don't want to manage another tool
- Quick testing/development

---

## Common Development Workflows

### Local Registry with kind

```bash
# Create registry container
docker run -d --restart=always -p 5000:5000 --name registry registry:2

# Create kind cluster with registry
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:5000"]
    endpoint = ["http://registry:5000"]
EOF

# Connect registry to kind network
docker network connect kind registry

# Push to local registry
docker build -t localhost:5000/myapp:dev .
docker push localhost:5000/myapp:dev

# Use in K8s
# image: localhost:5000/myapp:dev
```

### Development Cluster Script

```bash
#!/bin/bash
# dev-cluster.sh - Consistent dev environment

CLUSTER_NAME="dev"

# Delete existing if present
kind delete cluster --name $CLUSTER_NAME 2>/dev/null

# Create cluster with ingress support
cat <<EOF | kind create cluster --name $CLUSTER_NAME --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
- role: worker
EOF

# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "Dev cluster ready!"
```

---

## Resource Management

### kind Resource Limits

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  # Kind nodes are Docker containers, so limit via Docker
  extraMounts:
  - hostPath: /data/kind
    containerPath: /var/local-path-provisioner
```

### minikube Resources

```bash
# Start with specific resources
minikube start --cpus 4 --memory 8g --disk-size 50g

# Check allocated resources
minikube config view

# Set defaults
minikube config set cpus 4
minikube config set memory 8192
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Too many clusters | Eats all system resources | Delete unused clusters |
| No image loading | ImagePullBackOff errors | Use `kind load docker-image` |
| Ingress not working | Port mapping missing | Use config with extraPortMappings |
| Forgot which cluster | Commands hit wrong cluster | Use `kubectl config current-context` |
| Node not schedulable | Taints on control plane | Use worker nodes or tolerate taints |
| Storage not working | No StorageClass | Install local-path-provisioner |

---

## War Story: The Missing Cluster

*A developer spent 2 hours debugging why their pods weren't starting. "ImagePullBackOff" everywhere. The cluster couldn't pull from their local registry.*

**What went wrong**:
1. Built image locally: `docker build -t myapp:dev .`
2. Deployed to kind: `kubectl apply -f deployment.yaml`
3. kind couldn't find image (it's in host Docker, not kind's containerd)

**The fix**:
```bash
# After building locally, load into kind
docker build -t myapp:dev .
kind load docker-image myapp:dev

# OR use imagePullPolicy: Never
spec:
  containers:
  - name: myapp
    image: myapp:dev
    imagePullPolicy: Never
```

**Lesson**: kind runs its own container runtime. Images must be explicitly loaded or come from a registry.

---

## Quiz

### Question 1
When would you choose kind over minikube?

<details>
<summary>Show Answer</summary>

**Choose kind when**:
- Need multi-node cluster easily
- CI/CD testing (fast, ephemeral)
- Low resource usage is priority
- Don't need addons

**Choose minikube when**:
- Need addons (dashboard, ingress, metrics)
- Want GPU support
- Need persistent storage
- Learning/tutorials (better docs)

kind is lighter and faster; minikube is more feature-rich.

</details>

### Question 2
Why does `kind load docker-image` exist?

<details>
<summary>Show Answer</summary>

kind runs Kubernetes nodes as Docker containers. Each node has its own container runtime (containerd) separate from the host's Docker.

When you `docker build`, the image is in host Docker.
When kind tries to run pods, it looks in the node's containerd.

`kind load docker-image`:
1. Exports image from host Docker
2. Imports into each kind node's containerd

Without this, you'd get `ImagePullBackOff` because the image doesn't exist where Kubernetes is looking.

</details>

### Question 3
How do you expose services with kind (no LoadBalancer)?

<details>
<summary>Show Answer</summary>

Three options:

**1. Port mapping in cluster config**:
```yaml
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
```

**2. NodePort services**:
```yaml
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30080
```
Access via `localhost:30080`

**3. kubectl port-forward**:
```bash
kubectl port-forward svc/myapp 8080:80
```
Access via `localhost:8080`

For production-like ingress, use option 1 with nginx ingress controller.

</details>

---

## Hands-On Exercise

### Objective
Set up a local Kubernetes cluster with kind and deploy a sample application.

### Tasks

1. **Install kind**:
   ```bash
   brew install kind  # or Linux method
   ```

2. **Create multi-node cluster**:
   ```bash
   cat <<EOF | kind create cluster --config=-
   kind: Cluster
   apiVersion: kind.x-k8s.io/v1alpha4
   nodes:
   - role: control-plane
   - role: worker
   - role: worker
   EOF
   ```

3. **Verify nodes**:
   ```bash
   kubectl get nodes
   ```

4. **Deploy sample app**:
   ```bash
   kubectl create deployment nginx --image=nginx
   kubectl expose deployment nginx --port=80
   ```

5. **Access via port-forward**:
   ```bash
   kubectl port-forward svc/nginx 8080:80
   # Visit http://localhost:8080
   ```

6. **Load local image**:
   ```bash
   # Create simple image
   echo 'FROM nginx:alpine' > Dockerfile
   echo 'RUN echo "Hello kind!" > /usr/share/nginx/html/index.html' >> Dockerfile

   docker build -t my-nginx:dev .
   kind load docker-image my-nginx:dev

   kubectl set image deployment/nginx nginx=my-nginx:dev
   ```

7. **Clean up**:
   ```bash
   kind delete cluster
   ```

### Success Criteria
- [ ] kind installed and working
- [ ] Multi-node cluster created
- [ ] Sample app deployed
- [ ] Can access app via port-forward
- [ ] Local image loaded and running
- [ ] Cluster deleted cleanly

### Bonus Challenge
Add ingress support to your kind cluster and access nginx via hostname instead of port-forward.

---

## Further Reading

- [kind Documentation](https://kind.sigs.k8s.io/)
- [minikube Documentation](https://minikube.sigs.k8s.io/)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/kubernetes/)

---

## Toolkit Complete!

Congratulations on completing the Developer Experience Toolkit! You've learned:
- k9s and CLI productivity tools
- Telepresence and Tilt for development workflows
- Local Kubernetes options

Continue exploring other toolkits or start applying these tools to your daily work.

---

*"The best local cluster is the one that gets out of your way. Pick a tool, share the config, and focus on building."*
