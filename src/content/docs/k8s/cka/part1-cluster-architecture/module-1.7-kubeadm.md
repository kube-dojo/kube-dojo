---
title: "Module 1.7: kubeadm Basics - Cluster Bootstrap"
slug: k8s/cka/part1-cluster-architecture/module-1.7-kubeadm
sidebar:
  order: 8
---
> **Complexity**: `[MEDIUM]` - Essential cluster management
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 1.1 (Control Plane), Module 1.2 (Extension Interfaces)

---

## Why This Module Matters

kubeadm is the official tool for creating Kubernetes clusters. The CKA exam environment uses kubeadm-based clusters, and you'll need to understand how they work.

While the 2025 curriculum **deprioritizes cluster upgrades**, you still need to know:
- How clusters are bootstrapped
- How to join nodes
- Where control plane components live
- Basic cluster maintenance tasks

Understanding kubeadm helps you troubleshoot cluster issues and understand what's happening under the hood.

> **The Construction Blueprint Analogy**
>
> Think of kubeadm like a construction foreman with blueprints. When you say "init," it follows the blueprints to build the control plane—laying the foundation (certificates), erecting the framework (static pods), and connecting utilities (networking). When workers (nodes) arrive, it gives them instructions to join the team. The foreman doesn't build the house alone; it orchestrates the process.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand what kubeadm does during cluster creation
- Bootstrap a control plane node
- Join worker nodes to a cluster
- Understand static pods and manifests
- Perform basic node management

---

## Part 1: kubeadm Overview

### 1.1 What kubeadm Does

kubeadm automates cluster setup:

```
┌────────────────────────────────────────────────────────────────┐
│                    kubeadm init Process                         │
│                                                                 │
│   1. Pre-flight Checks                                         │
│      └── Verify system requirements (CPU, memory, ports)       │
│                                                                 │
│   2. Generate Certificates                                     │
│      └── CA, API server, kubelet, etcd certificates           │
│      └── Stored in /etc/kubernetes/pki/                        │
│                                                                 │
│   3. Generate kubeconfig Files                                 │
│      └── admin.conf, kubelet.conf, controller-manager.conf     │
│      └── Stored in /etc/kubernetes/                            │
│                                                                 │
│   4. Generate Static Pod Manifests                             │
│      └── API server, controller-manager, scheduler, etcd       │
│      └── Stored in /etc/kubernetes/manifests/                  │
│                                                                 │
│   5. Start kubelet                                             │
│      └── kubelet reads manifests and starts control plane      │
│                                                                 │
│   6. Apply Cluster Configuration                               │
│      └── CoreDNS, kube-proxy DaemonSet                        │
│                                                                 │
│   7. Generate Join Token                                       │
│      └── For worker nodes to join                              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 What kubeadm Does NOT Do

- **Install container runtime** (containerd) - you do this first
- **Install kubelet/kubectl** - you install these first
- **Install CNI plugin** - you apply this after init
- **Configure load balancers** - that's your infrastructure
- **Set up HA** - requires additional configuration

### 1.3 Prerequisites

Before running kubeadm:

```bash
# Required on ALL nodes:
# 1. Container runtime (containerd)
# 2. kubelet
# 3. kubeadm
# 4. kubectl (at least on control plane)
# 5. Swap disabled
# 6. Required ports open
# 7. Unique hostname, MAC, product_uuid
```

---

## Part 2: Initializing a Cluster

### 2.1 Basic kubeadm init

```bash
# Initialize control plane
sudo kubeadm init

# With specific pod network CIDR (required by some CNIs)
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# With specific API server address (for HA or custom networking)
sudo kubeadm init --apiserver-advertise-address=192.168.1.10

# With specific Kubernetes version
sudo kubeadm init --kubernetes-version=v1.35.0
```

### 2.2 After init - Setup kubectl Access

```bash
# For regular user (recommended)
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# For root user
export KUBECONFIG=/etc/kubernetes/admin.conf
```

### 2.3 Install CNI Plugin

```bash
# Without CNI, pods won't get IPs and CoreDNS won't start

# Calico
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/calico.yaml

# Flannel
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# Cilium
cilium install
```

### 2.4 Verify Cluster

```bash
# Check nodes
kubectl get nodes
# NAME           STATUS   ROLES           AGE   VERSION
# control-plane  Ready    control-plane   5m    v1.35.0

# Check system pods
kubectl get pods -n kube-system
# Should see: coredns, etcd, kube-apiserver, kube-controller-manager,
#             kube-proxy, kube-scheduler, CNI pods
```

> **Did You Know?**
>
> The `kubeadm init` output includes a `kubeadm join` command with a token. This token expires in 24 hours by default. Save it, or you'll need to generate a new one.

---

## Part 3: Joining Worker Nodes

### 3.1 The Join Command

After `kubeadm init`, you get a join command:

```bash
# Example output from kubeadm init
kubeadm join 192.168.1.10:6443 --token abcdef.0123456789abcdef \
  --discovery-token-ca-cert-hash sha256:abc123...
```

Run this on worker nodes:

```bash
# On worker node (as root)
sudo kubeadm join 192.168.1.10:6443 \
  --token abcdef.0123456789abcdef \
  --discovery-token-ca-cert-hash sha256:abc123...
```

### 3.2 Regenerating Join Tokens

If the token expired:

```bash
# On control plane - create new token
kubeadm token create --print-join-command

# Or manually:
# 1. Create token
kubeadm token create

# 2. Get CA cert hash
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | \
  openssl rsa -pubin -outform der 2>/dev/null | \
  openssl dgst -sha256 -hex | sed 's/^.* //'

# 3. Construct join command
kubeadm join <control-plane-ip>:6443 --token <new-token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

### 3.3 List and Manage Tokens

```bash
# List existing tokens
kubeadm token list

# Delete a token
kubeadm token delete <token>

# Create token with custom TTL
kubeadm token create --ttl 2h
```

---

## Part 4: Understanding Static Pods

### 4.1 What Are Static Pods?

Static pods are managed directly by kubelet, not the API server. Control plane components run as static pods in kubeadm clusters.

```bash
# Static pod manifests location
ls /etc/kubernetes/manifests/
# etcd.yaml
# kube-apiserver.yaml
# kube-controller-manager.yaml
# kube-scheduler.yaml
```

### 4.2 How Static Pods Work

```
┌────────────────────────────────────────────────────────────────┐
│                    Static Pod Lifecycle                         │
│                                                                 │
│   /etc/kubernetes/manifests/                                   │
│           │                                                     │
│           │ kubelet watches this directory                     │
│           ▼                                                     │
│   ┌─────────────┐                                              │
│   │   kubelet   │                                              │
│   └──────┬──────┘                                              │
│          │                                                      │
│          │ For each YAML file:                                 │
│          │ 1. Start container                                  │
│          │ 2. Keep it running                                  │
│          │ 3. Restart if it crashes                            │
│          │ 4. Create mirror pod in API server                  │
│          ▼                                                      │
│   ┌─────────────────────────────────────────┐                  │
│   │ Control Plane Containers                 │                  │
│   │ • kube-apiserver                        │                  │
│   │ • kube-controller-manager               │                  │
│   │ • kube-scheduler                        │                  │
│   │ • etcd                                  │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Working with Static Pods

```bash
# View static pod manifests
sudo cat /etc/kubernetes/manifests/kube-apiserver.yaml

# Modify a static pod (edit the manifest)
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# kubelet automatically restarts the pod

# "Delete" a static pod (remove the manifest)
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/
# kubelet stops the pod

# Restore it
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/
# kubelet starts the pod again
```

> **Gotcha: kubectl delete Won't Work**
>
> You can't delete static pods with `kubectl delete pod`. They're recreated immediately because kubelet manages them. To stop a static pod, remove or rename its manifest file.

---

## Part 5: Cluster Directory Structure

### 5.1 Key Directories

```
/etc/kubernetes/
├── admin.conf               # kubectl config for admin
├── controller-manager.conf  # kubeconfig for controller-manager
├── kubelet.conf             # kubeconfig for kubelet
├── scheduler.conf           # kubeconfig for scheduler
├── manifests/               # Static pod definitions
│   ├── etcd.yaml
│   ├── kube-apiserver.yaml
│   ├── kube-controller-manager.yaml
│   └── kube-scheduler.yaml
└── pki/                     # Certificates
    ├── ca.crt               # Cluster CA
    ├── ca.key
    ├── apiserver.crt        # API server cert
    ├── apiserver.key
    ├── apiserver-kubelet-client.crt
    ├── front-proxy-ca.crt
    ├── sa.key               # ServiceAccount signing key
    ├── sa.pub
    └── etcd/                # etcd certificates
        ├── ca.crt
        └── ...
```

### 5.2 Certificate Locations

```bash
# Cluster CA
/etc/kubernetes/pki/ca.crt
/etc/kubernetes/pki/ca.key

# API Server
/etc/kubernetes/pki/apiserver.crt
/etc/kubernetes/pki/apiserver.key

# etcd CA (separate CA)
/etc/kubernetes/pki/etcd/ca.crt
/etc/kubernetes/pki/etcd/ca.key

# Check certificate expiration
kubeadm certs check-expiration
```

---

## Part 6: Node Management

### 6.1 Viewing Nodes

```bash
# List nodes
kubectl get nodes

# Detailed info
kubectl get nodes -o wide

# Node details
kubectl describe node <node-name>
```

### 6.2 Draining a Node

Before maintenance, drain the node to safely evict pods:

```bash
# Drain node (evict pods, mark unschedulable)
kubectl drain <node-name> --ignore-daemonsets

# If there are pods with local storage:
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Force (for pods without controllers):
kubectl drain <node-name> --ignore-daemonsets --force
```

### 6.3 Cordoning and Uncordoning

```bash
# Mark node unschedulable (no new pods)
kubectl cordon <node-name>

# Mark node schedulable again
kubectl uncordon <node-name>

# Check node status
kubectl get nodes
# NAME    STATUS                     ROLES    AGE   VERSION
# node1   Ready                      worker   10d   v1.35.0
# node2   Ready,SchedulingDisabled   worker   10d   v1.35.0  # cordoned
```

### 6.4 Removing a Node

```bash
# 1. Drain the node first
kubectl drain <node-name> --ignore-daemonsets --force

# 2. Delete from cluster
kubectl delete node <node-name>

# 3. On the node itself, reset kubeadm
sudo kubeadm reset

# 4. Clean up
sudo rm -rf /etc/kubernetes/
sudo rm -rf /var/lib/kubelet/
sudo rm -rf /var/lib/etcd/
```

---

## Part 7: kubeadm reset

### 7.1 When to Use Reset

Use `kubeadm reset` to:
- Remove a node from the cluster
- Start fresh after failed init
- Completely tear down a cluster

### 7.2 Reset Process

```bash
# On the node to reset
sudo kubeadm reset

# This does:
# 1. Stops kubelet
# 2. Removes /etc/kubernetes/
# 3. Removes cluster state from etcd (if control plane)
# 4. Removes certificates
# 5. Cleans up iptables rules

# Additional cleanup you should do:
sudo rm -rf /etc/cni/net.d/
sudo rm -rf $HOME/.kube/config
sudo iptables -F && sudo iptables -t nat -F
```

---

## Part 8: Common Troubleshooting

### 8.1 kubelet Not Starting

```bash
# Check kubelet status
systemctl status kubelet

# Check kubelet logs
journalctl -u kubelet -f

# Common issues:
# - Swap not disabled
# - Container runtime not running
# - Wrong container runtime socket
```

### 8.2 Control Plane Not Starting

```bash
# Check container runtime
crictl ps

# Check static pod containers
crictl logs <container-id>

# Look for API server errors
sudo cat /var/log/pods/kube-system_kube-apiserver-*/kube-apiserver/*.log
```

### 8.3 Node Not Joining

```bash
# On the node, check logs
journalctl -u kubelet | tail -50

# Common issues:
# - Token expired
# - Wrong CA hash
# - Network connectivity to control plane
# - Firewall blocking port 6443
```

### 8.4 Certificates Expired

```bash
# Check expiration
kubeadm certs check-expiration

# Renew all certificates
kubeadm certs renew all

# Restart control plane components
# (just move manifests and wait)
```

---

## Part 9: Exam-Relevant Commands

### 9.1 Quick Reference

```bash
# Initialize cluster
kubeadm init --pod-network-cidr=10.244.0.0/16

# Get join command
kubeadm token create --print-join-command

# Join worker
kubeadm join <control-plane>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>

# Check certificates
kubeadm certs check-expiration

# Drain node for maintenance
kubectl drain <node> --ignore-daemonsets

# Make node schedulable again
kubectl uncordon <node>

# Reset node
kubeadm reset
```

---

## Did You Know?

- **kubeadm doesn't manage kubelet**. kubelet runs as a systemd service. kubeadm generates the config, but systemctl manages the service.

- **Static pods have mirror pods**. The API server shows "mirror" pods for static pods so you can see them with kubectl. But you can't manage them through the API.

- **HA control planes** require external load balancers. kubeadm can init additional control plane nodes, but you need to set up load balancing yourself.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Running init with swap enabled | Init fails | `swapoff -a` and remove from /etc/fstab |
| Forgetting CNI after init | Pods stay Pending | Install CNI immediately after init |
| Token expired | Can't join nodes | `kubeadm token create --print-join-command` |
| Using kubectl delete on static pods | Pods keep coming back | Edit/remove manifests in /etc/kubernetes/manifests/ |
| Not draining before maintenance | Pod disruption | Always `kubectl drain` first |

---

## Quiz

1. **Where are control plane static pod manifests stored?**
   <details>
   <summary>Answer</summary>
   `/etc/kubernetes/manifests/` on the control plane node. kubelet watches this directory and manages the pods defined there.
   </details>

2. **You lost the kubeadm join command. How do you get a new one?**
   <details>
   <summary>Answer</summary>
   Run `kubeadm token create --print-join-command` on the control plane. This creates a new token and outputs the complete join command with the CA cert hash.
   </details>

3. **How do you prevent new pods from being scheduled on a node without evicting existing pods?**
   <details>
   <summary>Answer</summary>
   `kubectl cordon <node-name>` marks the node as unschedulable. Existing pods continue running, but no new pods will be scheduled there.
   </details>

4. **You edited /etc/kubernetes/manifests/kube-apiserver.yaml. What happens next?**
   <details>
   <summary>Answer</summary>
   kubelet detects the file change and automatically restarts the kube-apiserver pod with the new configuration. No manual restart needed.
   </details>

---

## Hands-On Exercise

**Task**: Practice node management operations.

> **Note**: This exercise requires a cluster with at least one worker node. If using minikube or kind, some operations may differ.

**Steps**:

1. **View cluster nodes**:
```bash
kubectl get nodes -o wide
```

2. **Examine a node**:
```bash
kubectl describe node <node-name> | head -50
```

3. **Check static pod manifests** (on control plane):
```bash
# If you have SSH access to control plane
ls /etc/kubernetes/manifests/
cat /etc/kubernetes/manifests/kube-apiserver.yaml | head -30
```

4. **Practice cordon/uncordon**:
```bash
# Cordon a worker node
kubectl cordon <worker-node>
kubectl get nodes
# Should show SchedulingDisabled

# Try to schedule a pod
kubectl run test-pod --image=nginx

# Check where it landed
kubectl get pods -o wide
# Won't be on cordoned node

# Uncordon
kubectl uncordon <worker-node>
kubectl get nodes
```

5. **Practice drain** (careful in production!):
```bash
# Create a deployment first
kubectl create deployment drain-test --image=nginx --replicas=2

# Check pod locations
kubectl get pods -o wide

# Drain a node with pods
kubectl drain <node-with-pods> --ignore-daemonsets

# Check pods moved
kubectl get pods -o wide

# Uncordon the node
kubectl uncordon <node-name>
```

6. **Check certificates** (on control plane):
```bash
# If you have access to control plane
kubeadm certs check-expiration
```

7. **Generate join command**:
```bash
# On control plane
kubeadm token create --print-join-command
```

8. **Cleanup**:
```bash
kubectl delete deployment drain-test
kubectl delete pod test-pod
```

**Success Criteria**:
- [ ] Can view and describe nodes
- [ ] Understand cordon vs drain
- [ ] Know where static pod manifests are stored
- [ ] Can generate new join tokens
- [ ] Understand the kubeadm init process

---

## Practice Drills

### Drill 1: Node Management Commands (Target: 3 minutes)

```bash
# List nodes with details
kubectl get nodes -o wide

# Get node labels
kubectl get nodes --show-labels

# Describe a node
kubectl describe node <node-name> | head -50

# Check node conditions
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Check node resources
kubectl describe node <node-name> | grep -A10 "Allocated resources"
```

### Drill 2: Cordon and Uncordon (Target: 5 minutes)

```bash
# Cordon a node (prevent new pods)
kubectl cordon <worker-node>

# Verify
kubectl get nodes  # Shows SchedulingDisabled

# Try to schedule a pod
kubectl run cordon-test --image=nginx
kubectl get pods -o wide  # Won't be on cordoned node

# Uncordon
kubectl uncordon <worker-node>
kubectl get nodes  # Back to Ready

# Cleanup
kubectl delete pod cordon-test
```

### Drill 3: Drain and Recover (Target: 5 minutes)

```bash
# Create test deployment
kubectl create deployment drain-test --image=nginx --replicas=3

# Wait for pods
kubectl wait --for=condition=available deployment/drain-test --timeout=60s
kubectl get pods -o wide

# Drain a worker node
kubectl drain <worker-node> --ignore-daemonsets --delete-emptydir-data

# Watch pods move to other nodes
kubectl get pods -o wide

# Uncordon the node
kubectl uncordon <worker-node>

# Cleanup
kubectl delete deployment drain-test
```

### Drill 4: kubeadm Token Management (Target: 3 minutes)

```bash
# List existing tokens
kubeadm token list

# Create a new token
kubeadm token create

# Create token with specific TTL
kubeadm token create --ttl 2h

# Generate full join command
kubeadm token create --print-join-command

# Delete a token
kubeadm token delete <token-id>
```

### Drill 5: Static Pod Exploration (Target: 5 minutes)

```bash
# Find static pod manifest directory
cat /var/lib/kubelet/config.yaml | grep staticPodPath
# Usually: /etc/kubernetes/manifests

# List static pod manifests
ls -la /etc/kubernetes/manifests/

# View one manifest
cat /etc/kubernetes/manifests/kube-apiserver.yaml | head -30

# Create your own static pod
cat << 'EOF' | sudo tee /etc/kubernetes/manifests/my-static-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-static-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
EOF

# Wait and verify (will have node name suffix)
sleep 10
kubectl get pods | grep my-static-pod

# Remove static pod
sudo rm /etc/kubernetes/manifests/my-static-pod.yaml
```

### Drill 6: Certificate Inspection (Target: 5 minutes)

```bash
# Check certificate expiration (on control plane)
kubeadm certs check-expiration

# View certificate details
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | head -30

# Check all certificates
ls -la /etc/kubernetes/pki/

# Check CA certificate
openssl x509 -in /etc/kubernetes/pki/ca.crt -text -noout | grep -E "Subject:|Issuer:|Not"
```

### Drill 7: Troubleshooting - Node NotReady (Target: 5 minutes)

```bash
# Simulate: Stop kubelet on a worker
# (Run on worker node)
sudo systemctl stop kubelet

# On control plane, diagnose
kubectl get nodes  # Shows NotReady
kubectl describe node <worker> | grep -A10 Conditions

# Check what's happening
kubectl get events --field-selector involvedObject.kind=Node

# Fix: Restart kubelet (on worker)
sudo systemctl start kubelet

# Verify recovery
kubectl get nodes -w
```

### Drill 8: Challenge - Node Maintenance Workflow

Perform a complete maintenance workflow:

1. Cordon the node
2. Drain all workloads
3. Simulate maintenance (wait 30s)
4. Uncordon the node
5. Verify pods can be scheduled again

```bash
# YOUR TASK: Complete this without looking at solution
NODE_NAME=<your-worker-node>
kubectl create deployment maint-test --image=nginx --replicas=2

# Start timer - Target: 3 minutes total
```

<details>
<summary>Solution</summary>

```bash
NODE_NAME=worker-01  # Replace with your node

# 1. Cordon
kubectl cordon $NODE_NAME

# 2. Drain
kubectl drain $NODE_NAME --ignore-daemonsets --delete-emptydir-data

# 3. Verify pods moved
kubectl get pods -o wide

# 4. Simulate maintenance
echo "Performing maintenance..."
sleep 30

# 5. Uncordon
kubectl uncordon $NODE_NAME

# 6. Verify scheduling works
kubectl scale deployment maint-test --replicas=4
kubectl get pods -o wide  # Some should land on $NODE_NAME

# Cleanup
kubectl delete deployment maint-test
```

</details>

---

## Summary: Part 1 Complete!

Congratulations! You've completed **Part 1: Cluster Architecture, Installation & Configuration**.

You now understand:
- ✅ Control plane components and how they interact
- ✅ Extension interfaces: CNI, CSI, CRI
- ✅ Helm for package management
- ✅ Kustomize for configuration management
- ✅ CRDs and Operators for extending Kubernetes
- ✅ RBAC for access control
- ✅ kubeadm for cluster management

### Part 1 Module Index

Quick links for review:

| Module | Topic | Key Skills |
|--------|-------|------------|
| [1.1](../module-1.1-control-plane/) | Control Plane Deep-Dive | Component roles, troubleshooting, static pods |
| [1.2](../module-1.2-extension-interfaces/) | Extension Interfaces | CNI/CSI/CRI, crictl, plugin troubleshooting |
| [1.3](../module-1.3-helm/) | Helm | Install, upgrade, rollback, values |
| [1.4](../module-1.4-kustomize/) | Kustomize | Base/overlay, patches, `kubectl -k` |
| [1.5](../module-1.5-crds-operators/) | CRDs & Operators | Create CRDs, manage custom resources |
| [1.6](../module-1.6-rbac/) | RBAC | Roles, bindings, ServiceAccounts, `can-i` |
| [1.7](../module-1.7-kubeadm/) | kubeadm Basics | Init, join, cordon, drain, tokens |

📝 **Before moving on**: Complete the [Part 1 Cumulative Quiz](../part1-cumulative-quiz/) to test your retention.

---

## Next Steps

Continue to [Part 2: Workloads & Scheduling](../part2-workloads-scheduling/) - Learn how to deploy and manage applications.

This covers 15% of the exam and builds directly on what you've learned about cluster architecture.
