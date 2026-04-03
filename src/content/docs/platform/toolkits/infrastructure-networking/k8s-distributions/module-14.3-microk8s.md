---
title: "Module 14.3: MicroK8s - Snap-Based Kubernetes from Canonical"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.3-microk8s
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

MicroK8s is Kubernetes the Ubuntu way—installed and updated through snap packages, with optional features enabled via add-ons. It's the fastest way to get Kubernetes running on Ubuntu, and its add-on system means you can go from "hello world" to production-ready with a few commands.

Built by Canonical (the company behind Ubuntu), MicroK8s targets developers who want Kubernetes that "just works" and operations teams who want consistent deployments across development, CI/CD, and production.

This module teaches you to deploy and operate MicroK8s for development and production environments.

## Prerequisites

- Kubernetes fundamentals (kubectl, deployments, services)
- Linux command-line basics
- Ubuntu or snap-capable Linux system
- Understanding of container runtimes

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy MicroK8s with snap-based installation and configure add-ons for development workflows**
- **Configure MicroK8s clustering for multi-node HA setups using the built-in join mechanism**
- **Implement MicroK8s add-ons for GPU workloads, observability, and service mesh capabilities**
- **Compare MicroK8s's add-on ecosystem against K3s and K0s for developer and edge use cases**


## Why This Module Matters

**MicroK8s answers: "What if installing Kubernetes add-ons was as easy as `snap install`?"**

Most Kubernetes distributions require separate installation of:
- CNI (Calico, Cilium, Flannel)
- Ingress controller (nginx, Traefik)
- Storage provisioner (local-path, OpenEBS)
- Monitoring (Prometheus, Grafana)
- Dashboard
- Registry

MicroK8s makes this trivial:

```bash
microk8s enable dns storage ingress prometheus dashboard
```

One command enables a production-ready stack.

## Did You Know?

- **Snap Delivery**: MicroK8s is delivered via snap—automatic updates, rollbacks, and confined execution
- **Dqlite**: Uses Dqlite (distributed SQLite) instead of etcd for clustering
- **CNCF Certified**: Passes all Kubernetes conformance tests
- **Ubuntu Pro**: Commercial support available through Ubuntu Pro
- **GPU Support**: Native NVIDIA GPU operator add-on for AI/ML workloads

## MicroK8s Architecture

```
MicroK8s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                         MicroK8s Node                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Snap Package                                    │   │
│  │                     /snap/microk8s                                  │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Core Services ───────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  kube-apiserver    kube-controller-manager    kube-scheduler    │   │
│  │  │  kubelet           kube-proxy                containerd         │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Datastore ───────────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  Dqlite (distributed SQLite) - HA clustering             │      │   │
│  │  │  or etcd (optional via add-on)                           │      │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────────── Add-ons System ──────────────────────┐      │   │
│  │  │                                                          │      │   │
│  │  │  dns        │  storage     │  ingress      │  dashboard │      │   │
│  │  │  prometheus │  registry    │  metallb      │  istio     │      │   │
│  │  │  gpu        │  cert-manager│  observability│  argocd    │      │   │
│  │  │  ... and 30+ more                                       │      │   │
│  │  │                                                          │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Data Locations                                    │ │
│  │                                                                       │ │
│  │  Config: /var/snap/microk8s/current                                  │ │
│  │  Data:   /var/snap/microk8s/common                                   │ │
│  │  Images: /var/snap/microk8s/common/var/lib/containerd               │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

ADD-ON ARCHITECTURE:
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Add-on System                                      │
│                                                                             │
│  microk8s enable <addon>                                                    │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  /snap/microk8s/current/addons/<addon>/enable                       │   │
│  │                                                                     │   │
│  │  1. Apply manifests (kubectl apply -f)                             │   │
│  │  2. Wait for pods to be ready                                       │   │
│  │  3. Configure integration with other add-ons                        │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Add-on Categories:                                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Core:         dns, storage, ingress, dashboard                            │
│  Networking:   metallb, cilium, multus                                     │
│  Observability: prometheus, observability (Loki+Grafana+Tempo)            │
│  Security:     cert-manager, rbac                                          │
│  CI/CD:        registry, argocd, fluxcd                                    │
│  AI/ML:        gpu, kubeflow                                               │
│  Service Mesh: istio, linkerd                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installing MicroK8s

### Quick Install (Ubuntu)

```bash
# Install MicroK8s
sudo snap install microk8s --classic

# Add user to microk8s group (avoid sudo)
sudo usermod -a -G microk8s $USER
sudo chown -R $USER ~/.kube
newgrp microk8s

# Check status
microk8s status --wait-ready

# Enable essential add-ons
microk8s enable dns storage
```

### Install Specific Version

```bash
# List available versions
snap info microk8s

# Install specific channel
sudo snap install microk8s --classic --channel=1.28/stable

# Track latest patch releases for 1.28
sudo snap refresh microk8s --channel=1.28/stable
```

### Install on Other Linux Distributions

```bash
# Install snapd first (if not on Ubuntu)
# Fedora
sudo dnf install snapd
sudo ln -s /var/lib/snapd/snap /snap

# Debian
sudo apt install snapd

# Then install MicroK8s
sudo snap install microk8s --classic
```

## Add-ons System

### Core Add-ons

```bash
# DNS (CoreDNS) - required for most workloads
microk8s enable dns

# Storage (hostpath provisioner)
microk8s enable storage

# Dashboard (Kubernetes Dashboard)
microk8s enable dashboard

# Get dashboard token
microk8s kubectl describe secret -n kube-system microk8s-dashboard-token

# Ingress (nginx ingress controller)
microk8s enable ingress

# Metrics Server (for kubectl top)
microk8s enable metrics-server
```

### Networking Add-ons

```bash
# MetalLB (bare-metal load balancer)
microk8s enable metallb:192.168.1.200-192.168.1.220

# Or with interactive configuration
microk8s enable metallb
# Enter IP range when prompted

# Cilium (eBPF-based CNI)
microk8s enable cilium

# Multus (multiple network interfaces)
microk8s enable multus
```

### Observability Add-ons

```bash
# Prometheus + Grafana (legacy)
microk8s enable prometheus

# Observability stack (Prometheus + Loki + Grafana + Tempo)
microk8s enable observability

# Access Grafana
microk8s kubectl port-forward -n observability svc/grafana 3000:80
```

### Security Add-ons

```bash
# cert-manager
microk8s enable cert-manager

# RBAC (enabled by default on newer versions)
microk8s enable rbac
```

### AI/ML Add-ons

```bash
# GPU support (NVIDIA)
microk8s enable gpu

# Kubeflow (full ML platform)
microk8s enable kubeflow
```

### CI/CD Add-ons

```bash
# Local registry
microk8s enable registry

# Push to local registry
docker tag myapp localhost:32000/myapp:v1
docker push localhost:32000/myapp:v1

# ArgoCD
microk8s enable argocd

# FluxCD
microk8s enable fluxcd
```

### List All Add-ons

```bash
microk8s status

# Example output:
# addons:
#   enabled:
#     dns
#     storage
#     dashboard
#   disabled:
#     ambassador
#     cilium
#     gpu
#     ...
```

## Multi-Node Clustering

MicroK8s supports clustering for high availability:

### Add Nodes

**On the first node (primary):**

```bash
# Generate join token
microk8s add-node

# Output:
# Join node with:
# microk8s join 192.168.1.10:25000/abc123...
```

**On additional nodes:**

```bash
# Install MicroK8s
sudo snap install microk8s --classic

# Join the cluster
microk8s join 192.168.1.10:25000/abc123...

# Verify on primary
microk8s kubectl get nodes
```

### High Availability with Dqlite

MicroK8s uses Dqlite (distributed SQLite) for HA:

```
Dqlite Clustering
─────────────────────────────────────────────────────────────────────────────

       ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
       │    Node 1     │     │    Node 2     │     │    Node 3     │
       │   (leader)    │     │  (follower)   │     │  (follower)   │
       │               │     │               │     │               │
       │  ┌─────────┐  │     │  ┌─────────┐  │     │  ┌─────────┐  │
       │  │ Dqlite  │◄─┼─────┼─▶│ Dqlite  │◄─┼─────┼─▶│ Dqlite  │  │
       │  └─────────┘  │     │  └─────────┘  │     │  └─────────┘  │
       │               │     │               │     │               │
       │  API Server   │     │  API Server   │     │  API Server   │
       │  Controller   │     │  Controller   │     │  Controller   │
       │  Scheduler    │     │  Scheduler    │     │  Scheduler    │
       └───────────────┘     └───────────────┘     └───────────────┘

Benefits of Dqlite:
• Simpler than etcd (SQLite semantics)
• Lower resource usage
• Automatic leader election
• Raft consensus for durability
```

### Remove Nodes

```bash
# On the node to remove
microk8s leave

# On remaining nodes (if needed)
microk8s remove-node <node-name>
```

## Configuration

### Accessing kubeconfig

```bash
# Use microk8s kubectl directly
microk8s kubectl get nodes

# Export kubeconfig for external tools
microk8s config > ~/.kube/config

# Or merge with existing config
KUBECONFIG=~/.kube/config:~/.kube/microk8s.config kubectl config view --flatten > ~/.kube/merged.config

# Create alias for convenience
alias kubectl='microk8s kubectl'
```

### Customizing API Server

```bash
# Edit API server arguments
sudo nano /var/snap/microk8s/current/args/kube-apiserver

# Add or modify arguments like:
# --enable-admission-plugins=NodeRestriction,PodSecurityPolicy
# --audit-log-path=/var/log/kubernetes/audit.log

# Restart to apply
microk8s stop
microk8s start
```

### Customizing kubelet

```bash
# Edit kubelet arguments
sudo nano /var/snap/microk8s/current/args/kubelet

# Example customizations:
# --max-pods=250
# --system-reserved=cpu=100m,memory=256Mi

# Restart
microk8s stop
microk8s start
```

### Container Runtime Configuration

```bash
# containerd configuration
sudo nano /var/snap/microk8s/current/args/containerd-template.toml

# Add insecure registries
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."myregistry.local:5000"]
  endpoint = ["http://myregistry.local:5000"]

# Restart containerd
microk8s stop
microk8s start
```

## Upgrading MicroK8s

### Automatic Updates (Default)

```bash
# Check current channel
snap info microk8s

# Snaps update automatically by default
# To refresh immediately:
sudo snap refresh microk8s

# To hold automatic updates:
sudo snap refresh --hold microk8s

# To unhold:
sudo snap refresh --unhold microk8s
```

### Track Specific Channel

```bash
# Switch to a different Kubernetes version
sudo snap refresh microk8s --channel=1.29/stable

# Available channels:
# 1.28/stable, 1.28/candidate, 1.28/beta, 1.28/edge
# 1.29/stable, 1.29/candidate, ...
# latest/stable, latest/edge
```

### Rollback

```bash
# Revert to previous version
sudo snap revert microk8s

# List available revisions
snap list --all microk8s
```

## Air-Gapped Installation

```bash
# On connected machine:

# Download the snap
snap download microk8s --channel=1.28/stable

# This creates:
# microk8s_xxxx.snap
# microk8s_xxxx.assert

# Transfer to air-gapped machine, then:

# Install assertion first
sudo snap ack microk8s_xxxx.assert

# Install snap
sudo snap install microk8s_xxxx.snap --classic

# Import container images
# First, export from connected machine:
docker save myimage:tag | gzip > myimage.tar.gz

# On air-gapped machine:
microk8s ctr image import myimage.tar.gz
```

## Troubleshooting

### Common Issues

```bash
# Check MicroK8s status
microk8s status

# Inspect logs
microk8s inspect

# Check kubelet logs
journalctl -u snap.microk8s.daemon-kubelet

# Check API server logs
journalctl -u snap.microk8s.daemon-apiserver

# Reset everything (destructive!)
microk8s reset

# Start fresh
microk8s stop
microk8s start
```

### Network Issues

```bash
# Check CNI pods
microk8s kubectl get pods -n kube-system -l k8s-app=calico-node

# Check DNS resolution
microk8s kubectl run test --image=busybox --rm -it --restart=Never -- nslookup kubernetes

# Verify cluster DNS
microk8s kubectl get svc -n kube-system kube-dns
```

### Storage Issues

```bash
# Check storage provisioner
microk8s kubectl get pods -n kube-system -l k8s-app=hostpath-provisioner

# Check PVCs
microk8s kubectl get pvc -A

# Check PVs
microk8s kubectl get pv
```

## War Story: The Ubuntu-Native Platform

A software company standardized on Ubuntu across their entire stack:

**The Setup**:
- 200+ developers using Ubuntu workstations
- CI/CD on Ubuntu runners
- Production on Ubuntu servers (bare metal and cloud)
- Existing tooling built around snap ecosystem

**The Challenge**:
- Developers needed local Kubernetes
- CI/CD needed ephemeral Kubernetes for tests
- Production needed HA Kubernetes
- All environments needed to be consistent

**Why MicroK8s Won**:

```
ENVIRONMENT CONSISTENCY
─────────────────────────────────────────────────────────────────────────────

Developer Laptop:
  sudo snap install microk8s --classic
  microk8s enable dns storage registry
  # Ready in 2 minutes

CI/CD Runner:
  # In GitHub Actions
  - name: Setup MicroK8s
    run: |
      sudo snap install microk8s --classic
      microk8s status --wait-ready
      microk8s enable dns storage
      microk8s kubectl apply -f k8s/

Production:
  # On each node
  sudo snap install microk8s --classic
  microk8s add-node  # On primary
  microk8s join ...  # On secondaries
  microk8s enable dns storage metallb:10.0.0.200-10.0.0.250

Same commands, same add-ons, same behavior everywhere.
```

**The Add-on Advantage**:

```yaml
# Standard configuration across all environments
# environments/base/kustomization.yaml
resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml

# Developer setup script
#!/bin/bash
microk8s enable dns storage registry ingress
microk8s enable observability  # Local debugging

# Production setup script
#!/bin/bash
microk8s enable dns storage metallb:$LB_RANGE
microk8s enable cert-manager
microk8s enable prometheus
```

**GitOps Integration**:

```bash
# Enable ArgoCD
microk8s enable argocd

# Configure applications
microk8s kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/app
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: default
EOF
```

**The Results**:
- Onboarding time: 2 hours → 15 minutes
- "Works on my machine" issues: 90% reduction
- CI/CD pipeline time: Reduced by 40% (snap caching)
- Production incidents from config drift: Near zero

**The Lesson**: When your entire stack is Ubuntu, MicroK8s eliminates friction that other distributions introduce.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not enabling dns | Services can't resolve names | Always `microk8s enable dns` first |
| Forgetting storage | PVCs stay pending | Enable storage add-on early |
| Using sudo with kubectl | Permission issues | Add user to microk8s group |
| Holding updates too long | Security vulnerabilities | Track stable channel, update regularly |
| Not waiting for ready | Commands fail randomly | Use `microk8s status --wait-ready` |
| Ignoring inspect output | Missed configuration issues | Run `microk8s inspect` when debugging |
| Wrong channel for production | Unstable features | Use stable channel, not edge |
| No resource limits | Workloads starve microk8s | Set limits on applications |

## Quiz

Test your understanding of MicroK8s:

<details>
<summary>1. What makes MicroK8s unique compared to k3s and k0s?</summary>

**Answer**: MicroK8s is delivered via snap packages with an integrated add-on system. Unlike k3s (single binary) or k0s (zero deps), MicroK8s uses snap's features: automatic updates, rollbacks, confined execution, and channel-based version tracking. The add-on system (`microk8s enable`) makes installing components trivial.
</details>

<details>
<summary>2. What is Dqlite and why does MicroK8s use it?</summary>

**Answer**: Dqlite is distributed SQLite with Raft consensus. MicroK8s uses it instead of etcd for HA clustering. Benefits: simpler than etcd, lower resource usage, SQLite semantics (familiar), automatic leader election. Trade-off: less battle-tested than etcd at extreme scale.
</details>

<details>
<summary>3. How do you enable a LoadBalancer service on bare metal with MicroK8s?</summary>

**Answer**: Use the MetalLB add-on: `microk8s enable metallb:IP_RANGE`. For example, `microk8s enable metallb:192.168.1.200-192.168.1.250`. MetalLB provides Layer 2 or BGP-based load balancing for Services of type LoadBalancer.
</details>

<details>
<summary>4. How do you join additional nodes to a MicroK8s cluster?</summary>

**Answer**: On the primary node, run `microk8s add-node` to generate a join command. On the new node, install MicroK8s and run the provided `microk8s join <primary-ip>:<port>/<token>` command. The cluster uses Dqlite for consensus, requiring odd numbers of nodes for HA.
</details>

<details>
<summary>5. How do you perform an air-gapped installation of MicroK8s?</summary>

**Answer**: On a connected machine: `snap download microk8s --channel=1.28/stable`. Transfer the .snap and .assert files to the air-gapped machine. Install: `sudo snap ack microk8s_xxxx.assert` then `sudo snap install microk8s_xxxx.snap --classic`. Import container images with `microk8s ctr image import`.
</details>

<details>
<summary>6. How do you customize the Kubernetes API server in MicroK8s?</summary>

**Answer**: Edit `/var/snap/microk8s/current/args/kube-apiserver` to add or modify arguments. Then restart MicroK8s with `microk8s stop && microk8s start`. Similar files exist for kubelet, scheduler, and other components in the same directory.
</details>

<details>
<summary>7. What's the difference between stable and edge channels?</summary>

**Answer**: Stable channels (e.g., `1.28/stable`) receive tested releases suitable for production. Edge channels receive latest builds, possibly unstable. Candidate and beta are between. For production, always use stable. For testing new features, use edge with caution.
</details>

<details>
<summary>8. How do you access the local registry add-on?</summary>

**Answer**: Enable with `microk8s enable registry`. It runs on `localhost:32000`. Push images: `docker tag myapp localhost:32000/myapp:v1 && docker push localhost:32000/myapp:v1`. In pod specs, reference as `localhost:32000/myapp:v1` (from within the cluster, use `registry.container-registry.svc.cluster.local:5000`).
</details>

## Hands-On Exercise: Full-Stack MicroK8s Deployment

### Objective
Deploy a complete development environment with MicroK8s including monitoring, ingress, and a sample application.

### Step 1: Install MicroK8s

```bash
# Install MicroK8s
sudo snap install microk8s --classic

# Configure user access
sudo usermod -a -G microk8s $USER
sudo chown -R $USER ~/.kube
newgrp microk8s

# Wait for ready
microk8s status --wait-ready
```

### Step 2: Enable Essential Add-ons

```bash
# Enable core add-ons
microk8s enable dns
microk8s enable storage
microk8s enable ingress
microk8s enable metrics-server

# Wait for all pods
microk8s kubectl wait --for=condition=ready pod -n kube-system -l k8s-app=kube-dns --timeout=60s
```

### Step 3: Enable Observability Stack

```bash
# Enable full observability (Prometheus + Grafana + Loki + Tempo)
microk8s enable observability

# Wait for stack to be ready
microk8s kubectl wait --for=condition=ready pod -n observability -l app.kubernetes.io/name=grafana --timeout=120s

# Check status
microk8s kubectl get pods -n observability
```

### Step 4: Enable Local Registry

```bash
# Enable registry
microk8s enable registry

# Check registry is running
microk8s kubectl get pods -n container-registry
```

### Step 5: Deploy Sample Application

```bash
# Create namespace
microk8s kubectl create namespace demo

# Create deployment
cat <<EOF | microk8s kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: web-app
  namespace: demo
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app
  namespace: demo
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: web-app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app
            port:
              number: 80
EOF

# Add host entry
echo "127.0.0.1 web-app.local" | sudo tee -a /etc/hosts

# Test application
curl http://web-app.local
```

### Step 6: Access Observability

```bash
# Port-forward Grafana
microk8s kubectl port-forward -n observability svc/kube-prom-stack-grafana 3000:80 &

# Get Grafana password
microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo

# Open http://localhost:3000
# Username: admin
# Password: (from above command)

# Explore dashboards:
# - Kubernetes / Compute Resources / Namespace
# - Kubernetes / Networking / Namespace
```

### Step 7: Test Metrics

```bash
# Check node resources
microk8s kubectl top nodes

# Check pod resources
microk8s kubectl top pods -n demo

# Scale and observe
microk8s kubectl scale deployment web-app -n demo --replicas=5
microk8s kubectl top pods -n demo
```

### Step 8: Multi-Node Setup (Optional)

If you have additional machines:

```bash
# On primary
microk8s add-node
# Copy the join command

# On secondary
sudo snap install microk8s --classic
microk8s join 192.168.x.x:25000/token...

# Verify
microk8s kubectl get nodes
```

### Success Criteria

- [ ] MicroK8s installed and running
- [ ] DNS, storage, ingress add-ons enabled
- [ ] Observability stack deployed
- [ ] Local registry available
- [ ] Sample application accessible via ingress
- [ ] Grafana dashboards showing metrics
- [ ] `kubectl top` returning data

### Cleanup

```bash
# Stop port-forwards
pkill -f "port-forward"

# Delete demo namespace
microk8s kubectl delete namespace demo

# Disable add-ons
microk8s disable observability
microk8s disable registry
microk8s disable ingress
microk8s disable metrics-server

# Or reset entirely
microk8s reset

# Uninstall
sudo snap remove microk8s
```

## Key Takeaways

1. **Snap-based delivery**: Automatic updates, rollbacks, version channels
2. **Add-on ecosystem**: 30+ add-ons for common functionality
3. **`microk8s enable` is powerful**: Complex stacks in one command
4. **Dqlite for clustering**: Simpler HA than etcd
5. **Ubuntu-native integration**: Best experience on Ubuntu
6. **Channel-based versions**: Stable for production, edge for testing
7. **Built-in registry**: Easy local image storage
8. **Observability stack**: Full monitoring with one command
9. **Group permissions**: Add user to microk8s group, avoid sudo
10. **Inspect for debugging**: `microk8s inspect` is comprehensive

## Toolkit Summary

You've completed the Kubernetes Distributions Toolkit! You now understand:

| Distribution | Best For | Key Feature |
|--------------|----------|-------------|
| **k3s** | Edge, IoT, resource-constrained | Smallest footprint (~60MB) |
| **k0s** | Multi-platform, zero-dependency | Self-contained binary with runtime |
| **MicroK8s** | Ubuntu ecosystem, developers | Add-on system, snap delivery |

**Choose based on your constraints:**
- Need smallest footprint? → k3s
- Need zero host dependencies? → k0s
- Using Ubuntu and want batteries-included? → MicroK8s
- Need vanilla Kubernetes at scale? → kubeadm

---

*"MicroK8s makes Kubernetes feel native to Ubuntu. For Ubuntu shops, that's not a small thing—that's everything."*
