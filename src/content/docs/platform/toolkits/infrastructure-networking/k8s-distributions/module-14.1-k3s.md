---
title: "Module 14.1: k3s - Lightweight Kubernetes for Edge"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.1-k3s
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 45-50 minutes

## Overview

k3s is Kubernetes that fits on a Raspberry Pi. Created by Rancher Labs (now SUSE), it packages all of Kubernetes into a ~60MB binary that runs on devices with as little as 512MB RAM. It's not a toy—it's a CNCF Sandbox project running production workloads at the edge of networks worldwide, from factory floors to retail stores to autonomous vehicles.

This module teaches you to deploy, configure, and operate k3s for edge and resource-constrained environments.

## Prerequisites

- Kubernetes fundamentals (kubectl, deployments, services)
- Linux command-line basics
- Understanding of container runtimes (containerd)
- SSH access to at least one Linux machine (or VM)

## Why This Module Matters

**Kubernetes is everywhere, but not everywhere can run Kubernetes.**

Traditional Kubernetes requires:
- 2GB+ RAM for control plane
- Multiple machines for HA
- Complex etcd cluster management
- Significant operational overhead

Edge computing has different constraints:
- Limited RAM (512MB-2GB)
- Single nodes or small clusters
- Intermittent connectivity
- Minimal operational staff

k3s bridges this gap. It's real Kubernetes—same APIs, same kubectl, same ecosystem—but packaged for environments where every megabyte matters.

## Did You Know?

- **Why "k3s"?**: Kubernetes has 10 letters, often shortened to K8s (K + 8 letters + s). k3s has 5 letters—half of K8s, for "half the memory"
- **Origin**: Created by Rancher Labs founder Darren Shepherd in 2019
- **Scale**: Over 1 million nodes running k3s in production worldwide
- **Certifications**: k3s is CNCF certified Kubernetes—100% compatible

## k3s Architecture

```
k3s ARCHITECTURE DEEP DIVE
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                          k3s Server Node                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      k3s Binary (~60MB)                             │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Control Plane ───────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  kube-apiserver    kube-controller-manager    kube-scheduler    │   │
│  │  │  ─────────────────────────────────────────────────────────────  │   │
│  │  │  tunnel-proxy (server)    service-lb-controller                 │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Node Components ─────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  kubelet    kube-proxy    containerd                            │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Bundled Components ──────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  Traefik        CoreDNS       Local Path      Flannel          │   │
│  │  │  (Ingress)      (DNS)         (Storage)       (CNI)            │   │
│  │  │                                                          │      │   │
│  │  │  ServiceLB      Metrics       Network Policy                    │   │
│  │  │  (Load Balancer) Server       Controller                        │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Datastore Options                                │ │
│  │                                                                       │ │
│  │  SQLite (default)  │  etcd (HA)  │  MySQL  │  PostgreSQL             │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    k3s Agent Node   │   │    k3s Agent Node   │   │    k3s Agent Node   │
│                     │   │                     │   │                     │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ k3s Binary    │  │   │  │ k3s Binary    │  │   │  │ k3s Binary    │  │
│  │               │  │   │  │               │  │   │  │               │  │
│  │ kubelet       │  │   │  │ kubelet       │  │   │  │ kubelet       │  │
│  │ kube-proxy    │  │   │  │ kube-proxy    │  │   │  │ kube-proxy    │  │
│  │ containerd    │  │   │  │ containerd    │  │   │  │ containerd    │  │
│  │ flannel       │  │   │  │ flannel       │  │   │  │ flannel       │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│                     │   │                     │   │                     │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘

WHAT'S DIFFERENT FROM UPSTREAM K8S:
─────────────────────────────────────────────────────────────────────────────

Removed:
✗ Legacy, alpha, non-default features
✗ In-tree cloud providers
✗ In-tree storage drivers
✗ Docker (uses containerd directly)

Added:
✓ SQLite datastore (single node)
✓ Embedded etcd (HA mode)
✓ Tunnel proxy (agent communication)
✓ ServiceLB (bare-metal load balancer)
✓ Local Path Provisioner
✓ Traefik Ingress Controller
✓ Flannel CNI (by default)
```

## Installing k3s

### Single Node Installation

The fastest way to get started:

```bash
# Install k3s server (includes agent)
curl -sfL https://get.k3s.io | sh -

# Check service status
sudo systemctl status k3s

# Get kubeconfig
sudo cat /etc/rancher/k3s/k3s.yaml

# Or use k3s kubectl directly
sudo k3s kubectl get nodes

# Copy kubeconfig for regular user
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER ~/.kube/config

# Now use regular kubectl
kubectl get nodes
```

### Installation Options

k3s supports many installation flags via environment variables:

```bash
# Install specific version
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.28.5+k3s1" sh -

# Skip bundled components
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik --disable servicelb" sh -

# Use different CNI
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--flannel-backend=none" sh -

# Enable secrets encryption
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--secrets-encryption" sh -

# Custom data directory
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--data-dir=/opt/k3s" sh -
```

### Multi-Node Cluster

**On the server node:**

```bash
# Install server and get token
curl -sfL https://get.k3s.io | sh -

# Get the node token (needed for agents)
sudo cat /var/lib/rancher/k3s/server/node-token
```

**On each agent node:**

```bash
# Replace K3S_URL and K3S_TOKEN with actual values
curl -sfL https://get.k3s.io | K3S_URL=https://server-ip:6443 K3S_TOKEN=your-node-token sh -

# Verify agent joined
kubectl get nodes
```

### High Availability Setup

For production, deploy multiple server nodes:

```
HA k3s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

           ┌─────────────────────────────────────────┐
           │          Load Balancer                  │
           │     (HAProxy / cloud LB / DNS RR)       │
           │         api.k3s.example.com:6443        │
           └─────────────────────┬───────────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Server 1      │     │   Server 2      │     │   Server 3      │
│   (init node)   │◄───▶│                 │◄───▶│                 │
│                 │     │                 │     │                 │
│  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │
│  │ embedded  │◄─┼─────┼─▶│ embedded  │◄─┼─────┼─▶│ embedded  │  │
│  │   etcd    │  │     │  │   etcd    │  │     │  │   etcd    │  │
│  └───────────┘  │     │  └───────────┘  │     │  └───────────┘  │
└─────────────────┘     └─────────────────┘     └─────────────────┘

Option A: Embedded etcd (recommended for simplicity)
Option B: External datastore (MySQL, PostgreSQL, etcd)
```

**Using embedded etcd (recommended):**

```bash
# First server - initialize cluster
curl -sfL https://get.k3s.io | sh -s - server \
  --cluster-init \
  --tls-san=api.k3s.example.com

# Get token
sudo cat /var/lib/rancher/k3s/server/token

# Second and third servers - join cluster
curl -sfL https://get.k3s.io | sh -s - server \
  --server https://first-server-ip:6443 \
  --token <token-from-first-server> \
  --tls-san=api.k3s.example.com
```

**Using external datastore:**

```bash
# All servers point to external datastore
curl -sfL https://get.k3s.io | sh -s - server \
  --datastore-endpoint="mysql://user:password@tcp(host:3306)/k3s" \
  --tls-san=api.k3s.example.com

# Or PostgreSQL
curl -sfL https://get.k3s.io | sh -s - server \
  --datastore-endpoint="postgres://user:password@host:5432/k3s?sslmode=disable" \
  --tls-san=api.k3s.example.com
```

## k3s Configuration

### Server Configuration File

```yaml
# /etc/rancher/k3s/config.yaml
write-kubeconfig-mode: "0644"
tls-san:
  - "api.k3s.example.com"
  - "192.168.1.100"
cluster-cidr: "10.42.0.0/16"
service-cidr: "10.43.0.0/16"
cluster-dns: "10.43.0.10"
flannel-backend: "vxlan"
disable:
  - traefik  # Use your own ingress controller
secrets-encryption: true
kube-apiserver-arg:
  - "enable-admission-plugins=NodeRestriction,PodSecurityPolicy"
kubelet-arg:
  - "max-pods=250"
```

### Agent Configuration File

```yaml
# /etc/rancher/k3s/config.yaml (on agent nodes)
server: https://api.k3s.example.com:6443
token: your-node-token
node-label:
  - "node-type=worker"
  - "region=us-east"
kubelet-arg:
  - "max-pods=250"
```

### Disabling Default Components

Choose what you need:

```bash
# Disable all optional components
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC=" \
  --disable traefik \
  --disable servicelb \
  --disable local-storage \
  --disable metrics-server \
  " sh -

# Then install your preferred alternatives
# Example: Install nginx-ingress instead of Traefik
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
```

## Storage Options

### Local Path Provisioner (Default)

k3s includes Local Path Provisioner for simple persistent storage:

```yaml
# PVC using local-path StorageClass
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-data
```

### Longhorn (Distributed Storage)

For HA storage, install Longhorn:

```bash
# Install Longhorn
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/master/deploy/longhorn.yaml

# Wait for deployment
kubectl -n longhorn-system get pods -w

# Create StorageClass
cat <<EOF | kubectl apply -f -
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: longhorn
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "2"
  staleReplicaTimeout: "2880"
  fromBackup: ""
EOF

# Make Longhorn the default
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
kubectl patch storageclass longhorn -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## Networking

### Service Load Balancer (ServiceLB)

k3s includes a built-in load balancer for bare metal:

```yaml
# Exposes Service on node's external IP
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: my-app
```

ServiceLB creates a DaemonSet that listens on the node ports:

```bash
# Check LoadBalancer services
kubectl get svc

# See the ServiceLB pods
kubectl -n kube-system get pods | grep svclb
```

### Traefik Ingress Controller

k3s bundles Traefik for ingress:

```yaml
# Ingress using Traefik
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

### Network Policies

k3s supports network policies via its built-in controller:

```yaml
# Allow only frontend to access backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

## Air-Gapped Installation

For environments without internet access:

```bash
# On a machine with internet access:

# 1. Download k3s binary
wget https://github.com/k3s-io/k3s/releases/download/v1.28.5+k3s1/k3s

# 2. Download images archive
wget https://github.com/k3s-io/k3s/releases/download/v1.28.5+k3s1/k3s-airgap-images-amd64.tar.gz

# 3. Download install script
wget https://get.k3s.io -O install.sh

# Transfer all files to air-gapped machine, then:

# 4. Install images
sudo mkdir -p /var/lib/rancher/k3s/agent/images/
sudo cp k3s-airgap-images-amd64.tar.gz /var/lib/rancher/k3s/agent/images/

# 5. Install binary
sudo cp k3s /usr/local/bin/
sudo chmod +x /usr/local/bin/k3s

# 6. Run install script
chmod +x install.sh
INSTALL_K3S_SKIP_DOWNLOAD=true ./install.sh
```

## Upgrading k3s

### Manual Upgrade

```bash
# Check current version
k3s --version

# Download new version
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.29.0+k3s1" sh -

# Restart service
sudo systemctl restart k3s

# Verify upgrade
k3s --version
kubectl get nodes
```

### Automated Upgrades with system-upgrade-controller

```bash
# Install System Upgrade Controller
kubectl apply -f https://github.com/rancher/system-upgrade-controller/releases/latest/download/system-upgrade-controller.yaml

# Create upgrade plan for servers
cat <<EOF | kubectl apply -f -
apiVersion: upgrade.cattle.io/v1
kind: Plan
metadata:
  name: server-plan
  namespace: system-upgrade
spec:
  concurrency: 1
  cordon: true
  nodeSelector:
    matchExpressions:
    - key: node-role.kubernetes.io/control-plane
      operator: In
      values:
      - "true"
  serviceAccountName: system-upgrade
  upgrade:
    image: rancher/k3s-upgrade
  channel: https://update.k3s.io/v1-release/channels/stable
EOF

# Create upgrade plan for agents
cat <<EOF | kubectl apply -f -
apiVersion: upgrade.cattle.io/v1
kind: Plan
metadata:
  name: agent-plan
  namespace: system-upgrade
spec:
  concurrency: 2
  cordon: true
  nodeSelector:
    matchExpressions:
    - key: node-role.kubernetes.io/control-plane
      operator: DoesNotExist
  prepare:
    args:
    - prepare
    - server-plan
    image: rancher/k3s-upgrade
  serviceAccountName: system-upgrade
  upgrade:
    image: rancher/k3s-upgrade
  channel: https://update.k3s.io/v1-release/channels/stable
EOF
```

## Monitoring k3s

### Built-in Metrics Server

k3s includes metrics-server for `kubectl top`:

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -A

# Get detailed node metrics
kubectl describe node | grep -A 10 "Allocated resources"
```

### Prometheus Integration

```yaml
# prometheus-scrape-config.yaml
# k3s exposes metrics on /metrics
- job_name: 'k3s-server'
  static_configs:
    - targets:
      - 'server-ip:6443'
  scheme: https
  tls_config:
    insecure_skip_verify: true  # Or provide certs
  bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

- job_name: 'k3s-agent'
  static_configs:
    - targets:
      - 'agent-ip:10250'
  scheme: https
  tls_config:
    insecure_skip_verify: true
```

## War Story: The Retail Edge

A major retailer needed to run Kubernetes at 2,000 store locations:

**The Challenge**:
- 2,000 stores worldwide
- Each store has limited hardware (8GB RAM, 2 cores)
- Unreliable internet connectivity
- Zero on-site IT staff
- Need to run inventory management, point-of-sale, and analytics

**Why Traditional K8s Failed**:
- Minimum 2GB RAM just for control plane
- etcd cluster complexity
- Required 3 nodes minimum for HA
- Operational overhead impossible at scale

**The k3s Solution**:

```yaml
# Per-store deployment
Resources per store:
- 1 x Dell Edge Gateway (8GB RAM, 4 cores)
- k3s single-node mode
- Local Path Provisioner for storage
- Traefik for ingress

Workloads per store:
- Inventory service (200MB)
- POS API (150MB)
- Analytics agent (100MB)
- Local cache (Redis, 256MB)
Total: ~700MB + OS + k3s ≈ 2GB
Headroom: 6GB for burst
```

**Fleet Management**:

```yaml
# Rancher Fleet for GitOps at scale
apiVersion: fleet.cattle.io/v1alpha1
kind: GitRepo
metadata:
  name: store-applications
  namespace: fleet-default
spec:
  repo: https://github.com/company/store-apps
  branch: main
  paths:
  - releases
  targets:
  - name: all-stores
    clusterSelector:
      matchLabels:
        env: production
```

**The Results**:
- Deployment time: 15 minutes per store (automated)
- Memory usage: 1.5GB average (with workloads)
- Uptime: 99.9% (offline-capable for 48 hours)
- Updates: Zero-touch via system-upgrade-controller
- Cost savings: $2M/year vs. traditional infrastructure

**The Lesson**: k3s makes Kubernetes viable where it previously wasn't. The same APIs and tooling, but packaged for the real world.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using default token | Security vulnerability | Generate unique tokens per cluster |
| Not setting --tls-san | Certificate errors with LB | Include all access IPs/hostnames |
| Ignoring storage | Data loss on node failure | Use Longhorn or external storage |
| No HA setup | SPOF on single server | Deploy 3+ server nodes for production |
| Skipping upgrades | Security vulnerabilities | Use system-upgrade-controller |
| Not disabling swap | Kubelet issues | Disable swap on all nodes |
| Wrong flannel backend | Performance issues | Use wireguard for encrypted, vxlan for simple |
| No backup strategy | Cluster unrecoverable | Backup etcd/SQLite regularly |

## Quiz

Test your understanding of k3s:

<details>
<summary>1. What does k3s remove from upstream Kubernetes?</summary>

**Answer**: k3s removes: (1) Legacy, alpha, and non-default features, (2) In-tree cloud providers (AWS, GCP, Azure), (3) In-tree storage drivers, (4) Docker (uses containerd directly). These removals reduce the binary size by ~90% while maintaining full Kubernetes API compatibility.
</details>

<details>
<summary>2. What datastore options does k3s support?</summary>

**Answer**: k3s supports: (1) SQLite (default for single node), (2) Embedded etcd (for HA with --cluster-init), (3) External etcd cluster, (4) MySQL, (5) PostgreSQL. For single-node edge deployments, SQLite is perfect. For HA, embedded etcd is recommended for simplicity.
</details>

<details>
<summary>3. How do you join an agent node to an existing k3s cluster?</summary>

**Answer**: On the agent node, run: `curl -sfL https://get.k3s.io | K3S_URL=https://server:6443 K3S_TOKEN=<token> sh -`. The token is found at `/var/lib/rancher/k3s/server/node-token` on the server. The agent will automatically register with the cluster.
</details>

<details>
<summary>4. What is ServiceLB and why is it included in k3s?</summary>

**Answer**: ServiceLB (formerly Klipper) is a bare-metal load balancer included in k3s. When you create a LoadBalancer service, ServiceLB creates a DaemonSet that listens on the requested ports on each node. This provides LoadBalancer functionality without cloud provider integration or MetalLB—essential for edge deployments.
</details>

<details>
<summary>5. How do you disable bundled components in k3s?</summary>

**Answer**: Use the `--disable` flag: `k3s server --disable traefik --disable servicelb --disable local-storage`. Or in config.yaml: `disable: [traefik, servicelb, local-storage]`. This lets you use alternative components like nginx-ingress or MetalLB.
</details>

<details>
<summary>6. What's the difference between k3s server and k3s agent?</summary>

**Answer**: k3s server runs the control plane (API server, controller manager, scheduler) plus node components (kubelet, containerd). k3s agent runs only node components and connects to the server for cluster coordination. In single-node mode, the server is both control plane and worker. In multi-node mode, agents are dedicated workers.
</details>

<details>
<summary>7. How do you set up HA k3s with embedded etcd?</summary>

**Answer**: First server: `k3s server --cluster-init`. Get token from `/var/lib/rancher/k3s/server/token`. Additional servers: `k3s server --server https://first-server:6443 --token <token>`. Requires odd number of servers (3, 5, 7) for etcd quorum. All servers run both control plane and embedded etcd.
</details>

<details>
<summary>8. How do you perform air-gapped installation of k3s?</summary>

**Answer**: Download the k3s binary, airgap images tarball, and install script on an internet-connected machine. Transfer to air-gapped machine. Place images tarball in `/var/lib/rancher/k3s/agent/images/`. Place binary in `/usr/local/bin/k3s`. Run install script with `INSTALL_K3S_SKIP_DOWNLOAD=true`.
</details>

## Hands-On Exercise: Deploy HA k3s Cluster

### Objective
Deploy a high-availability k3s cluster with 3 server nodes and test failover.

### Environment Setup

We'll use Multipass for local VMs (or use any 3 Linux VMs/cloud instances):

```bash
# Install Multipass (macOS)
brew install multipass

# Or on Ubuntu
sudo snap install multipass

# Create 3 server VMs
for i in 1 2 3; do
  multipass launch --name k3s-server-$i --cpus 2 --memory 2G --disk 10G
done

# Create 2 agent VMs
for i in 1 2; do
  multipass launch --name k3s-agent-$i --cpus 2 --memory 2G --disk 10G
done

# List VMs and get IPs
multipass list
```

### Step 1: Initialize First Server

```bash
# SSH into first server
multipass shell k3s-server-1

# Install k3s with cluster-init
curl -sfL https://get.k3s.io | sh -s - server \
  --cluster-init \
  --tls-san=$(hostname -I | awk '{print $1}')

# Get the join token
sudo cat /var/lib/rancher/k3s/server/token

# Get server IP
hostname -I | awk '{print $1}'

# Exit shell
exit
```

### Step 2: Join Additional Servers

```bash
# Get SERVER_IP and TOKEN from step 1, then:

# Server 2
multipass shell k3s-server-2
curl -sfL https://get.k3s.io | sh -s - server \
  --server https://SERVER_IP:6443 \
  --token TOKEN
exit

# Server 3
multipass shell k3s-server-3
curl -sfL https://get.k3s.io | sh -s - server \
  --server https://SERVER_IP:6443 \
  --token TOKEN
exit
```

### Step 3: Join Agent Nodes

```bash
# Agent 1
multipass shell k3s-agent-1
curl -sfL https://get.k3s.io | K3S_URL=https://SERVER_IP:6443 K3S_TOKEN=TOKEN sh -
exit

# Agent 2
multipass shell k3s-agent-2
curl -sfL https://get.k3s.io | K3S_URL=https://SERVER_IP:6443 K3S_TOKEN=TOKEN sh -
exit
```

### Step 4: Verify Cluster

```bash
# From server-1
multipass shell k3s-server-1

# Check all nodes
sudo k3s kubectl get nodes

# Check etcd members
sudo k3s etcd-snapshot ls

# Check system pods
sudo k3s kubectl get pods -A

exit
```

### Step 5: Deploy Test Application

```bash
multipass shell k3s-server-1

# Create deployment
sudo k3s kubectl create deployment nginx --image=nginx --replicas=3

# Expose with LoadBalancer
sudo k3s kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Check pods are distributed across agents
sudo k3s kubectl get pods -o wide

# Get LoadBalancer IP
sudo k3s kubectl get svc nginx
```

### Step 6: Test Failover

```bash
# From your host machine, stop a server
multipass stop k3s-server-1

# From server-2, check cluster health
multipass shell k3s-server-2
sudo k3s kubectl get nodes
# Server-1 should show NotReady

# Check etcd is still functional
sudo k3s kubectl get pods -A

# Application should still work
curl http://LOADBALANCER_IP

exit

# Bring server-1 back
multipass start k3s-server-1

# Verify it rejoins
multipass shell k3s-server-1
sudo k3s kubectl get nodes
```

### Success Criteria

- [ ] 3 server nodes running with embedded etcd
- [ ] 2 agent nodes joined to cluster
- [ ] Application deployed across agent nodes
- [ ] Cluster survives server-1 failure
- [ ] Server-1 successfully rejoins after restart

### Cleanup

```bash
# Delete all VMs
multipass delete --purge k3s-server-1 k3s-server-2 k3s-server-3 k3s-agent-1 k3s-agent-2
```

## Key Takeaways

1. **k3s is real Kubernetes**: Same API, same kubectl, same ecosystem—just smaller
2. **Single binary simplicity**: ~60MB contains everything needed
3. **Multiple datastore options**: SQLite for single node, embedded etcd for HA
4. **Batteries included**: Traefik, CoreDNS, Local Path, ServiceLB bundled
5. **Disable what you don't need**: Customize by removing bundled components
6. **ServiceLB for bare metal**: LoadBalancer services work without cloud provider
7. **Air-gap friendly**: Download artifacts once, deploy anywhere
8. **Upgrade with care**: Use system-upgrade-controller for rolling upgrades
9. **HA requires 3+ servers**: Odd numbers for etcd quorum (3, 5, 7)
10. **Edge native**: Built for resource-constrained, distributed environments

## Next Module

Continue to [Module 14.2: k0s](module-14.2-k0s/) — Zero-dependency Kubernetes with even cleaner architecture.

---

*"k3s doesn't make Kubernetes simpler—it makes Kubernetes small enough to fit where you need it."*
