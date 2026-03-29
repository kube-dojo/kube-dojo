---
title: "Module 14.2: k0s - Zero Friction Kubernetes"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.2-k0s
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

k0s (pronounced "kay-zero-ess") takes the "batteries included" philosophy to its logical extreme: a single binary that contains everything—including the container runtime. No dependencies to install, no system services to configure, no packages to manage. Download, run, Kubernetes. That's it.

Built by Mirantis, k0s was designed to eliminate every friction point in Kubernetes deployment, from initial install to day-2 operations.

This module teaches you to deploy and operate k0s for clean, dependency-free Kubernetes clusters.

## Prerequisites

- Kubernetes fundamentals (kubectl, deployments, services)
- Linux command-line basics
- SSH access to Linux machines (or VMs)
- Understanding of container runtimes

## Why This Module Matters

**k0s answers the question: "What if Kubernetes had zero host dependencies?"**

Every other Kubernetes distribution assumes something:
- kubeadm assumes you've installed containerd
- k3s assumes systemd for service management
- MicroK8s assumes snap package support

k0s assumes nothing. The single binary contains:
- kube-apiserver, controller-manager, scheduler
- kubelet, kube-proxy
- containerd (with runc)
- etcd (for single-node or HA)
- CoreDNS, konnectivity-server

If your system can execute a binary, it can run k0s.

## Did You Know?

- **Zero Dependencies**: k0s requires only a Linux kernel and some basic utilities (iptables)
- **Clean State**: All k0s data lives in `/var/lib/k0s`—delete the directory, k0s is gone
- **Mirantis Origin**: Created by Mirantis after acquiring Docker Enterprise
- **Cluster API Support**: k0s integrates with Cluster API for declarative cluster management
- **Name Origin**: "k0s" = Kubernetes with zero ops, zero dependencies, zero friction

## k0s Architecture

```
k0s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                        k0s Controller Node                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    k0s Binary (~180MB)                              │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Control Plane ───────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  kube-apiserver    kube-controller-manager    kube-scheduler    │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Embedded Components ─────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  etcd/SQLite    konnectivity-server    CoreDNS                  │   │
│  │  │  metrics-server kube-router           helm-controller           │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  Note: Controller nodes do NOT run workloads by default            │   │
│  │        (clean separation of control plane and workers)             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        /var/lib/k0s                                   │ │
│  │   All state, configs, binaries, and data in one directory             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    k0s Worker Node  │   │    k0s Worker Node  │   │    k0s Worker Node  │
│                     │   │                     │   │                     │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ k0s Binary    │  │   │  │ k0s Binary    │  │   │  │ k0s Binary    │  │
│  │               │  │   │  │               │  │   │  │               │  │
│  │ kubelet       │  │   │  │ kubelet       │  │   │  │ kubelet       │  │
│  │ containerd    │  │   │  │ containerd    │  │   │  │ containerd    │  │
│  │ kube-proxy    │  │   │  │ kube-proxy    │  │   │  │ kube-proxy    │  │
│  │ kube-router   │  │   │  │ kube-router   │  │   │  │ kube-router   │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│                     │   │                     │   │                     │
│  /var/lib/k0s       │   │  /var/lib/k0s       │   │  /var/lib/k0s       │
│  (isolated state)   │   │  (isolated state)   │   │  (isolated state)   │
│                     │   │                     │   │                     │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘

KEY DIFFERENTIATORS:
─────────────────────────────────────────────────────────────────────────────

1. ZERO HOST DEPENDENCIES
   • containerd embedded in binary
   • No pre-installed runtime required
   • No system packages needed

2. CLEAN SEPARATION
   • Controllers are pure control plane (no workloads)
   • Workers are pure workers
   • Single-node mode runs both

3. ISOLATED STATE
   • Everything in /var/lib/k0s
   • Clean uninstall: rm -rf /var/lib/k0s
   • No scattered configs across filesystem

4. KUBE-ROUTER
   • CNI, kube-proxy replacement, and service load balancer
   • All networking in one component
   • Supports BGP for advanced routing
```

## Installing k0s

### Single Node (Development)

The simplest deployment—single node with control plane and worker:

```bash
# Download k0s
curl -sSLf https://get.k0s.sh | sudo sh

# Check version
k0s version

# Start single-node cluster
sudo k0s install controller --single
sudo k0s start

# Check status
sudo k0s status

# Get kubeconfig
sudo k0s kubeconfig admin > ~/.kube/config
chmod 600 ~/.kube/config

# Verify cluster
kubectl get nodes
kubectl get pods -A
```

### Multi-Node Cluster (Manual)

**On the controller node:**

```bash
# Download and install
curl -sSLf https://get.k0s.sh | sudo sh

# Install controller (NOT --single, workers will join)
sudo k0s install controller
sudo k0s start

# Wait for control plane
sudo k0s status

# Generate worker join token
sudo k0s token create --role=worker

# Save this token for worker nodes
```

**On each worker node:**

```bash
# Download and install
curl -sSLf https://get.k0s.sh | sudo sh

# Install worker with token
sudo k0s install worker --token-file /path/to/token

# Or pass token directly
sudo k0s install worker --token "eyJhbG..."

# Start worker
sudo k0s start

# Check status
sudo k0s status
```

**Verify from controller:**

```bash
kubectl get nodes
```

### Multi-Node Cluster with k0sctl

k0sctl automates multi-node deployment:

```bash
# Install k0sctl
curl -sSLf https://github.com/k0sproject/k0sctl/releases/latest/download/k0sctl-linux-amd64 -o k0sctl
chmod +x k0sctl
sudo mv k0sctl /usr/local/bin/

# Create cluster configuration
cat > k0sctl.yaml <<EOF
apiVersion: k0sctl.k0sproject.io/v1beta1
kind: Cluster
metadata:
  name: my-k0s-cluster
spec:
  hosts:
  - ssh:
      address: 192.168.1.10
      user: root
      keyPath: ~/.ssh/id_rsa
    role: controller
  - ssh:
      address: 192.168.1.11
      user: root
      keyPath: ~/.ssh/id_rsa
    role: worker
  - ssh:
      address: 192.168.1.12
      user: root
      keyPath: ~/.ssh/id_rsa
    role: worker
  k0s:
    version: v1.28.5+k0s.0
    config:
      spec:
        api:
          externalAddress: 192.168.1.10
        network:
          provider: kube-router
EOF

# Apply configuration (deploys entire cluster)
k0sctl apply --config k0sctl.yaml

# Get kubeconfig
k0sctl kubeconfig --config k0sctl.yaml > ~/.kube/config

# Verify
kubectl get nodes
```

### High Availability Setup

```yaml
# k0sctl.yaml for HA
apiVersion: k0sctl.k0sproject.io/v1beta1
kind: Cluster
metadata:
  name: ha-k0s-cluster
spec:
  hosts:
  # 3 controllers for HA
  - ssh:
      address: 192.168.1.10
      user: root
      keyPath: ~/.ssh/id_rsa
    role: controller
  - ssh:
      address: 192.168.1.11
      user: root
      keyPath: ~/.ssh/id_rsa
    role: controller
  - ssh:
      address: 192.168.1.12
      user: root
      keyPath: ~/.ssh/id_rsa
    role: controller
  # Workers
  - ssh:
      address: 192.168.1.20
      user: root
      keyPath: ~/.ssh/id_rsa
    role: worker
  - ssh:
      address: 192.168.1.21
      user: root
      keyPath: ~/.ssh/id_rsa
    role: worker
  k0s:
    version: v1.28.5+k0s.0
    config:
      spec:
        api:
          # Load balancer address
          externalAddress: api.k0s.example.com
          sans:
            - api.k0s.example.com
            - 192.168.1.10
            - 192.168.1.11
            - 192.168.1.12
        storage:
          type: etcd
```

## k0s Configuration

### Configuration File Structure

```yaml
# /etc/k0s/k0s.yaml
apiVersion: k0s.k0sproject.io/v1beta1
kind: ClusterConfig
metadata:
  name: my-cluster
spec:
  api:
    address: 192.168.1.10
    port: 6443
    k0sApiPort: 9443
    externalAddress: api.k0s.example.com
    sans:
      - api.k0s.example.com
      - "192.168.1.10"
    extraArgs:
      enable-admission-plugins: "NodeRestriction,PodSecurityPolicy"

  storage:
    type: etcd  # etcd, kine+sqlite, kine+mysql, kine+postgres
    etcd:
      peerAddress: 192.168.1.10

  network:
    provider: kube-router  # or calico, custom
    kubeProxy:
      disabled: false
      mode: iptables  # iptables or ipvs
    podCIDR: 10.244.0.0/16
    serviceCIDR: 10.96.0.0/12
    clusterDomain: cluster.local
    dualStack:
      enabled: false

  controllerManager:
    extraArgs:
      bind-address: "0.0.0.0"

  scheduler:
    extraArgs:
      bind-address: "0.0.0.0"

  installConfig:
    users:
      etcdUser: etcd
      kineUser: kube-apiserver
      konnectivityUser: konnectivity-server
      kubeAPIserverUser: kube-apiserver
      kubeSchedulerUser: kube-scheduler

  extensions:
    helm:
      repositories:
      - name: stable
        url: https://charts.helm.sh/stable
      charts:
      - name: prometheus
        chartname: stable/prometheus
        namespace: monitoring
    storage:
      type: openebs_local_storage  # or external_storage

  telemetry:
    enabled: true
```

### Network Provider Options

**kube-router (default):**

```yaml
spec:
  network:
    provider: kube-router
    kube-router:
      # Enable all features
      metricsPort: 8080
      hairpin: Enabled
      autoMTU: true
      # BGP configuration
      peerRouterASNs: "64512"
      peerRouterIPs: "192.168.1.1"
```

**Calico:**

```yaml
spec:
  network:
    provider: calico
    calico:
      mode: vxlan  # vxlan, ipip, bird
      overlay: Always
      flexVolumeDriverPath: /usr/libexec/k0s/kubelet-plugins/volume/exec/nodeagent~uds
      wireguard: false
```

**Custom CNI (Cilium, Flannel, etc.):**

```yaml
spec:
  network:
    provider: custom
    # Install your own CNI after cluster is up
```

### Storage Configuration

**SQLite (single node):**

```yaml
spec:
  storage:
    type: kine
    kine:
      dataSource: sqlite:///var/lib/k0s/db/state.db
```

**External database:**

```yaml
spec:
  storage:
    type: kine
    kine:
      dataSource: mysql://user:password@tcp(mysql.example.com:3306)/k0s
      # Or PostgreSQL
      # dataSource: postgres://user:password@postgres.example.com:5432/k0s?sslmode=disable
```

## Helm Integration

k0s includes a Helm controller for declarative chart installation:

```yaml
# In k0s.yaml
spec:
  extensions:
    helm:
      repositories:
      - name: jetstack
        url: https://charts.jetstack.io
      - name: ingress-nginx
        url: https://kubernetes.github.io/ingress-nginx

      charts:
      - name: cert-manager
        chartname: jetstack/cert-manager
        version: "v1.13.0"
        namespace: cert-manager
        values: |
          installCRDs: true

      - name: ingress-nginx
        chartname: ingress-nginx/ingress-nginx
        version: "4.8.0"
        namespace: ingress-nginx
        values: |
          controller:
            service:
              type: LoadBalancer
```

Apply changes by restarting k0s or using:

```bash
# Reconcile Helm charts
sudo k0s controller --enable-dynamic-config
```

## Cluster API Integration

k0s integrates with Cluster API for declarative cluster management:

```bash
# Install clusterctl
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl
sudo mv clusterctl /usr/local/bin/

# Initialize CAPI with k0s provider
clusterctl init --infrastructure docker --bootstrap k0sproject-k0smotron --control-plane k0sproject-k0smotron

# Create workload cluster
cat <<EOF | kubectl apply -f -
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: my-cluster
spec:
  clusterNetwork:
    pods:
      cidrBlocks: ["10.244.0.0/16"]
    services:
      cidrBlocks: ["10.96.0.0/12"]
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: K0sControlPlane
    name: my-cluster-cp
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: DockerCluster
    name: my-cluster
EOF
```

## Day-2 Operations

### Backup and Restore

```bash
# Backup etcd (on controller)
sudo k0s backup --save-path /backup/k0s-backup.tar.gz

# Restore from backup
sudo k0s stop
sudo k0s restore /backup/k0s-backup.tar.gz
sudo k0s start
```

### Upgrading k0s

```bash
# Check current version
k0s version

# With k0sctl (recommended for multi-node)
k0sctl apply --config k0sctl.yaml --debug

# Manual upgrade
sudo k0s stop
curl -sSLf https://get.k0s.sh | sudo K0S_VERSION=v1.29.0+k0s.0 sh
sudo k0s start
```

### Reset and Cleanup

```bash
# Stop k0s
sudo k0s stop

# Uninstall service
sudo k0s reset

# This removes:
# - /var/lib/k0s
# - /run/k0s
# - All containers
# - Network interfaces
# - iptables rules
```

## Monitoring and Troubleshooting

### Built-in Status

```bash
# Check k0s status
sudo k0s status

# Check component health
sudo k0s kubectl get --raw /healthz

# View control plane logs
sudo journalctl -u k0scontroller

# View worker logs
sudo journalctl -u k0sworker

# Check etcd health (HA setup)
sudo k0s etcd member-list
```

### Debugging

```bash
# Run with debug logging
sudo k0s controller --debug

# Get detailed component status
sudo k0s kubectl get componentstatuses

# Check CNI status
sudo k0s kubectl -n kube-system get pods -l k8s-app=kube-router

# Verify networking
sudo k0s kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- kubernetes.default
```

## War Story: The Clean Slate Infrastructure

A fintech startup needed Kubernetes across hybrid infrastructure:

**The Challenge**:
- Mixed infrastructure: AWS, on-prem, edge locations
- Different Linux distributions (Ubuntu, RHEL, Amazon Linux)
- Strict security requirements (no unnecessary packages)
- Need for consistent deployment across all environments

**Why Other Solutions Had Issues**:
- kubeadm: Required pre-installing containerd, different steps per distro
- k3s: Assumed systemd, had dependency issues on older RHEL
- Managed K8s: Not available on-prem or edge

**The k0s Solution**:

```bash
# Same installation everywhere
curl -sSLf https://get.k0s.sh | sudo sh
sudo k0s install controller
sudo k0s start

# Worked on:
# - Ubuntu 20.04
# - RHEL 7.9
# - Amazon Linux 2
# - Debian 11
# - Even Alpine (with glibc compatibility)
```

**Fleet Automation with k0sctl**:

```yaml
# environments/production.yaml
apiVersion: k0sctl.k0sproject.io/v1beta1
kind: Cluster
metadata:
  name: production
spec:
  hosts:
  # AWS controllers
  - ssh:
      address: 10.0.1.10
      user: ec2-user
      keyPath: ~/.ssh/aws.pem
    role: controller
    privateAddress: 10.0.1.10
  # On-prem controllers
  - ssh:
      address: 192.168.1.10
      user: root
      keyPath: ~/.ssh/onprem.pem
    role: controller
    privateAddress: 192.168.1.10
  # Edge workers
  - ssh:
      address: edge-node-1.example.com
      user: admin
      keyPath: ~/.ssh/edge.pem
    role: worker
```

**GitOps for Cluster Configuration**:

```yaml
# k0s.yaml managed in Git
spec:
  extensions:
    helm:
      charts:
      - name: cert-manager
        chartname: jetstack/cert-manager
        namespace: cert-manager
        version: v1.13.0
      - name: vault
        chartname: hashicorp/vault
        namespace: vault
        version: 0.25.0
```

**The Results**:
- Deployment time: 5 minutes per cluster (automated)
- Same binary, same process across all environments
- Clean uninstall: `k0s reset` leaves no traces
- Security team approved: minimal attack surface
- Upgrade path: `k0sctl apply` updates entire fleet

**The Lesson**: Zero dependencies means zero surprises across diverse infrastructure.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using --single in production | No HA, can't add workers | Use controller-only for HA |
| Forgetting externalAddress | Certificates don't include LB IP | Set API externalAddress and sans |
| Not separating controller/worker | Controllers running workloads | Controllers should be control-plane only |
| Ignoring backup | Data loss on failure | Regular `k0s backup` to external storage |
| Manual token management | Tokens expire, manual process | Use k0sctl for token lifecycle |
| Wrong storage type for HA | SQLite in multi-controller | Use etcd for HA setups |
| Not checking status | Silent failures | Regular `k0s status` checks |
| Skipping k0s reset | Leftover state causes issues | Always `k0s reset` before reinstall |

## Quiz

Test your understanding of k0s:

<details>
<summary>1. What makes k0s different from k3s in terms of dependencies?</summary>

**Answer**: k0s embeds containerd within its binary—no host runtime installation required. k3s assumes containerd is available on the system. This makes k0s truly zero-dependency: the single binary contains everything needed to run Kubernetes, including the container runtime.
</details>

<details>
<summary>2. Why don't k0s controller nodes run workloads by default?</summary>

**Answer**: k0s enforces clean separation of control plane and workers. Controller nodes only run control plane components (API server, controller-manager, scheduler, etcd). This improves security and stability—a workload crash can't affect the control plane. Use `--single` mode only for development when you want both on one node.
</details>

<details>
<summary>3. What is k0sctl and when should you use it?</summary>

**Answer**: k0sctl is an automation tool that deploys and manages k0s clusters via SSH. Use it for: (1) Multi-node deployments, (2) HA cluster setup, (3) Fleet upgrades, (4) Consistent configuration across nodes. It's the recommended way to manage anything beyond single-node development.
</details>

<details>
<summary>4. How does k0s handle CNI differently than k3s?</summary>

**Answer**: k0s defaults to kube-router, which provides CNI, service proxy (kube-proxy replacement), and network policies in one component. It also supports Calico as a built-in option or custom CNI. k3s defaults to Flannel. kube-router's integration with BGP makes k0s particularly suitable for advanced networking scenarios.
</details>

<details>
<summary>5. What datastore options does k0s support?</summary>

**Answer**: k0s supports: (1) etcd (embedded, for HA), (2) SQLite via kine (single node), (3) MySQL via kine (external HA), (4) PostgreSQL via kine (external HA). Unlike k3s which embeds SQLite/etcd logic, k0s uses kine as an abstraction layer for non-etcd backends.
</details>

<details>
<summary>6. How do you cleanly uninstall k0s?</summary>

**Answer**: Run `sudo k0s stop` followed by `sudo k0s reset`. The reset command removes: /var/lib/k0s, /run/k0s, all containers, network interfaces created by k0s, and iptables rules. All state is contained in /var/lib/k0s, so removal is complete and clean.
</details>

<details>
<summary>7. How does k0s integrate with Cluster API?</summary>

**Answer**: k0s provides bootstrap and control plane providers for Cluster API through the k0smotron project. This enables declarative cluster management: define clusters as Kubernetes resources, and CAPI reconciles the desired state. Useful for managing fleets of k0s clusters at scale.
</details>

<details>
<summary>8. What's the purpose of the Helm extension in k0s configuration?</summary>

**Answer**: The Helm extension allows declarative chart installation as part of cluster configuration. Charts defined in k0s.yaml are automatically installed/upgraded when the cluster starts. This enables GitOps-style management of cluster add-ons without external tools like ArgoCD for basic use cases.
</details>

## Hands-On Exercise: Deploy HA k0s with k0sctl

### Objective
Use k0sctl to deploy a high-availability k0s cluster with automated configuration.

### Environment Setup

Using Multipass (or any 3+ Linux VMs):

```bash
# Create VMs
for i in 1 2 3; do
  multipass launch --name k0s-ctrl-$i --cpus 2 --memory 2G --disk 10G
done

for i in 1 2; do
  multipass launch --name k0s-worker-$i --cpus 2 --memory 2G --disk 10G
done

# Get IP addresses
multipass list
```

### Step 1: Install k0sctl

```bash
# Download k0sctl
curl -sSLf https://github.com/k0sproject/k0sctl/releases/latest/download/k0sctl-linux-amd64 -o k0sctl
chmod +x k0sctl
sudo mv k0sctl /usr/local/bin/

# Verify
k0sctl version
```

### Step 2: Prepare SSH Access

```bash
# Copy your SSH key to all nodes (if using Multipass)
# Multipass uses its own authentication, so we'll use shell access instead

# For real VMs, ensure SSH key access:
# for host in ctrl-1 ctrl-2 ctrl-3 worker-1 worker-2; do
#   ssh-copy-id root@$host
# done
```

### Step 3: Create Cluster Configuration

```bash
# Get VM IPs
CTRL1_IP=$(multipass info k0s-ctrl-1 | grep IPv4 | awk '{print $2}')
CTRL2_IP=$(multipass info k0s-ctrl-2 | grep IPv4 | awk '{print $2}')
CTRL3_IP=$(multipass info k0s-ctrl-3 | grep IPv4 | awk '{print $2}')
WORKER1_IP=$(multipass info k0s-worker-1 | grep IPv4 | awk '{print $2}')
WORKER2_IP=$(multipass info k0s-worker-2 | grep IPv4 | awk '{print $2}')

# For Multipass, we'll do manual install. For real VMs:
cat > k0sctl.yaml <<EOF
apiVersion: k0sctl.k0sproject.io/v1beta1
kind: Cluster
metadata:
  name: ha-k0s-demo
spec:
  hosts:
  - ssh:
      address: ${CTRL1_IP}
      user: root
      keyPath: ~/.ssh/id_rsa
    role: controller
    privateInterface: eth0
  - ssh:
      address: ${CTRL2_IP}
      user: root
      keyPath: ~/.ssh/id_rsa
    role: controller
    privateInterface: eth0
  - ssh:
      address: ${CTRL3_IP}
      user: root
      keyPath: ~/.ssh/id_rsa
    role: controller
    privateInterface: eth0
  - ssh:
      address: ${WORKER1_IP}
      user: root
      keyPath: ~/.ssh/id_rsa
    role: worker
  - ssh:
      address: ${WORKER2_IP}
      user: root
      keyPath: ~/.ssh/id_rsa
    role: worker
  k0s:
    version: v1.28.5+k0s.0
    config:
      spec:
        api:
          sans:
            - ${CTRL1_IP}
            - ${CTRL2_IP}
            - ${CTRL3_IP}
        network:
          provider: kube-router
        extensions:
          helm:
            charts:
            - name: metrics-server
              chartname: metrics-server/metrics-server
              namespace: kube-system
              values: |
                args:
                  - --kubelet-insecure-tls
EOF

# For this exercise with Multipass, we'll do manual deployment
```

### Step 4: Manual Installation (Multipass)

Since Multipass doesn't support direct SSH, we'll install manually:

```bash
# On first controller
multipass shell k0s-ctrl-1
curl -sSLf https://get.k0s.sh | sudo sh
sudo k0s install controller
sudo k0s start
# Wait for it to start
sleep 30
sudo k0s status
# Create join tokens
sudo k0s token create --role=controller > /tmp/controller-token
sudo k0s token create --role=worker > /tmp/worker-token
cat /tmp/controller-token
cat /tmp/worker-token
exit

# Copy tokens (get them from the output above)
# CONTROLLER_TOKEN="..."
# WORKER_TOKEN="..."

# On controller 2
multipass shell k0s-ctrl-2
curl -sSLf https://get.k0s.sh | sudo sh
# Use the controller token from ctrl-1
echo "PASTE_CONTROLLER_TOKEN_HERE" | sudo tee /tmp/token
sudo k0s install controller --token-file /tmp/token
sudo k0s start
exit

# On controller 3
multipass shell k0s-ctrl-3
curl -sSLf https://get.k0s.sh | sudo sh
echo "PASTE_CONTROLLER_TOKEN_HERE" | sudo tee /tmp/token
sudo k0s install controller --token-file /tmp/token
sudo k0s start
exit

# On workers
multipass shell k0s-worker-1
curl -sSLf https://get.k0s.sh | sudo sh
echo "PASTE_WORKER_TOKEN_HERE" | sudo tee /tmp/token
sudo k0s install worker --token-file /tmp/token
sudo k0s start
exit

multipass shell k0s-worker-2
curl -sSLf https://get.k0s.sh | sudo sh
echo "PASTE_WORKER_TOKEN_HERE" | sudo tee /tmp/token
sudo k0s install worker --token-file /tmp/token
sudo k0s start
exit
```

### Step 5: Verify Cluster

```bash
# Get kubeconfig from any controller
multipass shell k0s-ctrl-1
sudo k0s kubeconfig admin
# Copy the output

# On your local machine
cat > ~/.kube/k0s-config << 'EOF'
# Paste kubeconfig here
EOF

export KUBECONFIG=~/.kube/k0s-config

# Check nodes
kubectl get nodes

# Check etcd members
multipass exec k0s-ctrl-1 -- sudo k0s etcd member-list

# Check pods
kubectl get pods -A
```

### Step 6: Deploy Test Application

```bash
# Create deployment
kubectl create deployment nginx --image=nginx --replicas=3

# Check pods are on workers
kubectl get pods -o wide

# Expose with service
kubectl expose deployment nginx --port=80 --type=ClusterIP

# Test connectivity
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- nginx
```

### Step 7: Test Controller Failover

```bash
# Stop one controller
multipass stop k0s-ctrl-1

# Check cluster is still operational
kubectl get nodes
kubectl get pods -A

# etcd should still have quorum (2/3)

# Bring controller back
multipass start k0s-ctrl-1
sleep 30

# Verify rejoin
kubectl get nodes
```

### Success Criteria

- [ ] 3 controller nodes running
- [ ] 2 worker nodes joined
- [ ] etcd cluster healthy (3 members)
- [ ] Application deployed to workers
- [ ] Cluster survives controller failure
- [ ] Failed controller rejoins

### Cleanup

```bash
# Stop and delete VMs
for i in 1 2 3; do
  multipass delete k0s-ctrl-$i
done
for i in 1 2; do
  multipass delete k0s-worker-$i
done
multipass purge
```

## Key Takeaways

1. **True zero dependencies**: containerd embedded—nothing to pre-install
2. **Clean separation**: Controllers don't run workloads (by design)
3. **All state in /var/lib/k0s**: Clean install, clean uninstall
4. **k0sctl automates everything**: Use it for multi-node clusters
5. **kube-router provides CNI + service proxy**: All networking in one
6. **Helm extension for add-ons**: Declarative chart installation
7. **Cluster API support**: Enterprise-grade cluster management
8. **Multiple storage backends**: etcd, SQLite, MySQL, PostgreSQL
9. **Backup built-in**: `k0s backup` for disaster recovery
10. **Same binary everywhere**: Works on any Linux distribution

## Next Module

Continue to [Module 14.3: MicroK8s](module-14.3-microk8s/) — Canonical's snap-based Kubernetes with rich add-ons.

---

*"k0s achieves what Kubernetes always promised but never delivered: download one thing, run Kubernetes."*
