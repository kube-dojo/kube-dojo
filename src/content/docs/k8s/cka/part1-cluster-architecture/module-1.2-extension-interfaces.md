---
title: "Module 1.2: Extension Interfaces - CNI, CSI, CRI"
slug: k8s/cka/part1-cluster-architecture/module-1.2-extension-interfaces
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Conceptual with some hands-on
>
> **Time to Complete**: 30-40 minutes
>
> **Prerequisites**: Module 1.1 (Control Plane)

---

## Why This Module Matters

Kubernetes doesn't actually know how to run containers, set up networking, or provision storage. Surprised?

Kubernetes is designed to be **pluggable**. It defines *interfaces*—contracts that say "if you implement these functions, I'll use you." This is why you can run Kubernetes with Docker, containerd, or CRI-O. With Calico, Cilium, or Flannel. With AWS EBS, GCP PD, or local storage.

The CKA 2025 curriculum specifically calls out understanding CNI, CSI, and CRI. You need to know what they are, why they exist, and how to troubleshoot when they fail.

> **The USB Port Analogy**
>
> Think of these interfaces like USB ports. Your computer doesn't need to know the specifics of every mouse, keyboard, or drive ever made—it just needs USB compliance. Similarly, Kubernetes defines CNI/CSI/CRI interfaces, and any compliant plugin works. Want to swap your network plugin? Unplug one, plug in another. Same cluster, different implementation.

---

## What You'll Learn

By the end of this module, you'll understand:
- What CNI, CSI, and CRI are
- Why Kubernetes uses plugin architecture
- Common implementations of each
- How to check which plugins your cluster uses
- Basic troubleshooting for each

---

## Part 1: The Plugin Architecture

### 1.1 Why Plugins?

```
┌────────────────────────────────────────────────────────────────┐
│                   The Kubernetes Philosophy                     │
│                                                                 │
│   "Do one thing well, let others do the rest"                  │
│                                                                 │
│   Kubernetes Core:                                             │
│   ✓ API and resource management                                │
│   ✓ Scheduling and orchestration                               │
│   ✓ Controller patterns                                        │
│   ✓ Desired state reconciliation                               │
│                                                                 │
│   NOT Kubernetes Core (delegated to plugins):                  │
│   ✗ Container runtime details                                   │
│   ✗ Network implementation                                      │
│   ✗ Storage provisioning                                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

Benefits:
- **Choice**: Use the best tool for your environment
- **Innovation**: New plugins without changing Kubernetes core
- **Specialization**: Network vendors focus on networking, storage vendors on storage
- **Portability**: Same Kubernetes, different infrastructure

### 1.2 The Three Main Interfaces

| Interface | Purpose | kubelet Talks To |
|-----------|---------|------------------|
| **CRI** (Container Runtime Interface) | Run containers | containerd, CRI-O |
| **CNI** (Container Network Interface) | Pod networking | Calico, Cilium, Flannel |
| **CSI** (Container Storage Interface) | Persistent storage | AWS EBS, GCP PD, Ceph |

---

## Part 2: CRI - Container Runtime Interface

### 2.1 What It Does

CRI defines how kubelet communicates with container runtimes. Without CRI, kubelet would need custom code for every runtime.

```
┌────────────────────────────────────────────────────────────────┐
│                         CRI Flow                                │
│                                                                 │
│   kubelet                                                       │
│      │                                                          │
│      │  CRI (gRPC)                                             │
│      │  "Create container with image X"                        │
│      │  "Start container Y"                                    │
│      │  "Stop container Z"                                     │
│      ▼                                                          │
│   ┌─────────────────┐    or    ┌─────────────────┐             │
│   │   containerd    │          │     CRI-O       │             │
│   └────────┬────────┘          └────────┬────────┘             │
│            │                            │                       │
│            ▼                            ▼                       │
│       ┌─────────┐                  ┌─────────┐                 │
│       │  runc   │                  │  runc   │                 │
│       └─────────┘                  └─────────┘                 │
│            │                            │                       │
│            ▼                            ▼                       │
│       Linux containers              Linux containers            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Common Container Runtimes

| Runtime | Description | Used By |
|---------|-------------|---------|
| **containerd** | Industry standard, CNCF graduated | kubeadm default, GKE, EKS, AKS |
| **CRI-O** | Kubernetes-focused, lightweight | OpenShift, some enterprise |
| **Docker** | ⚠️ Deprecated in K8s 1.24 | Legacy clusters |

> **Did You Know?**
>
> Docker deprecation caused panic in 2020, but it was overblown. Docker images still work everywhere—they're OCI-compliant. What changed is kubelet no longer talks to Docker daemon directly. Most users saw zero impact because Docker builds images, containerd runs them.

### 2.3 Checking Your Container Runtime

```bash
# What runtime is kubelet using?
kubectl get nodes -o wide
# Look at CONTAINER-RUNTIME column

# On a node, check containerd
systemctl status containerd
crictl info

# List running containers
crictl ps

# List images
crictl images

# Inspect a container
crictl inspect <container-id>
```

### 2.4 CRI Troubleshooting

```bash
# Container runtime not responding
systemctl status containerd
journalctl -u containerd -f

# kubelet can't talk to runtime
journalctl -u kubelet | grep -i "runtime"

# Check CRI socket
ls -la /var/run/containerd/containerd.sock

# Verify kubelet configuration
cat /var/lib/kubelet/config.yaml | grep -i container
```

> **Gotcha: crictl vs docker**
>
> On modern clusters, `docker` commands don't work because Docker isn't running. Use `crictl` instead—it's the CRI-compatible CLI that talks to containerd directly.

---

## Part 3: CNI - Container Network Interface

### 3.1 What It Does

CNI handles pod networking:
- Assigns IP addresses to pods
- Sets up routes between pods
- Creates network namespaces
- Implements network policies (some plugins)

```
┌────────────────────────────────────────────────────────────────┐
│                       CNI Flow                                  │
│                                                                 │
│   1. kubelet creates pod sandbox (pause container)             │
│   2. kubelet calls CNI plugin: "Configure network for pod X"   │
│   3. CNI plugin:                                               │
│      - Creates veth pair (virtual ethernet)                    │
│      - Assigns IP from pool                                    │
│      - Sets up routes                                          │
│      - Connects pod to cluster network                         │
│   4. Pod can now communicate with other pods                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Common CNI Plugins

| Plugin | Key Features | Complexity |
|--------|--------------|------------|
| **Calico** | NetworkPolicy, BGP routing, high performance | Medium |
| **Cilium** | eBPF-based, observability, security | Higher |
| **Flannel** | Simple overlay network | Low |
| **Weave** | Encryption, easy setup | Low |
| **AWS VPC CNI** | Native VPC networking | AWS-specific |

### 3.3 How CNI Plugins Are Installed

CNI plugins are typically:
1. **Binary** in `/opt/cni/bin/`
2. **Configuration** in `/etc/cni/net.d/`
3. **DaemonSet** running on every node (for plugin-specific agents)

```bash
# List CNI binaries
ls /opt/cni/bin/

# List CNI configurations (first file wins!)
ls /etc/cni/net.d/

# Check the active CNI config
cat /etc/cni/net.d/10-calico.conflist  # Example for Calico
```

### 3.4 Checking CNI Status

```bash
# What CNI is running?
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel|weave"

# Check CNI pod logs
kubectl logs -n kube-system -l k8s-app=calico-node --tail=50

# Verify pod IP allocation
kubectl get pods -o wide  # Check IP column

# Test pod-to-pod connectivity
kubectl exec pod-a -- ping <pod-b-ip>
```

### 3.5 CNI Troubleshooting

```bash
# Pods stuck in ContainerCreating
kubectl describe pod <pod-name>
# Look for: "failed to set up sandbox container network"

# Check CNI configuration exists
ls -la /etc/cni/net.d/

# Check CNI binary exists
ls -la /opt/cni/bin/

# Check CNI agent logs
kubectl logs -n kube-system -l k8s-app=calico-node -c calico-node

# Node network issues
ip addr show  # Check interfaces
ip route     # Check routes
```

> **War Story: The Missing CNI**
>
> A junior engineer built a kubeadm cluster but skipped the CNI installation step. Pods were stuck in ContainerCreating forever with cryptic "network not ready" errors. The fix was one command: `kubectl apply -f calico.yaml`. Lesson: kubeadm gives you a cluster, CNI gives you networking. Both are required.

---

## Part 4: CSI - Container Storage Interface

### 4.1 What It Does

CSI handles persistent storage:
- Provisions volumes (creates actual disks)
- Attaches volumes to nodes
- Mounts volumes in pods
- Snapshots and clones

```
┌────────────────────────────────────────────────────────────────┐
│                        CSI Flow                                 │
│                                                                 │
│   PersistentVolumeClaim created                                │
│            │                                                    │
│            ▼                                                    │
│   StorageClass defines CSI driver                              │
│            │                                                    │
│            ▼                                                    │
│   CSI Controller (Deployment in kube-system)                   │
│   "Provision 10Gi volume from AWS EBS"                         │
│            │                                                    │
│            ▼                                                    │
│   Cloud Provider: Creates actual disk                          │
│            │                                                    │
│            ▼                                                    │
│   PersistentVolume created and bound                           │
│            │                                                    │
│            ▼                                                    │
│   Pod scheduled to node                                        │
│            │                                                    │
│            ▼                                                    │
│   CSI Node plugin: Attaches & mounts disk                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 CSI Components

```
┌────────────────────────────────────────────────────────────────┐
│                   CSI Architecture                              │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              CSI Controller (Deployment)                 │  │
│   │  - Runs as pods in kube-system                          │  │
│   │  - Handles provisioning, attach/detach                  │  │
│   │  - Usually 1-3 replicas                                 │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              CSI Node Plugin (DaemonSet)                 │  │
│   │  - Runs on every node                                   │  │
│   │  - Handles mount/unmount                                │  │
│   │  - Registers node with CSI driver                       │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Common CSI Drivers

| Driver | Storage | Environment |
|--------|---------|-------------|
| **ebs.csi.aws.com** | AWS EBS | AWS EKS |
| **pd.csi.storage.gke.io** | GCP Persistent Disk | GKE |
| **disk.csi.azure.com** | Azure Disk | AKS |
| **csi.vsphere.vmware.com** | vSphere | VMware |
| **rook-ceph.rbd.csi.ceph.com** | Ceph RBD | On-premises |
| **hostpath.csi.k8s.io** | Local path | Development |

### 4.4 Checking CSI Status

```bash
# List CSI drivers in cluster
kubectl get csidrivers

# Check CSI pods
kubectl get pods -n kube-system | grep csi

# View StorageClasses (use CSI drivers)
kubectl get storageclasses
kubectl describe storageclass <name>

# Check PV provisioner
kubectl get pv -o jsonpath='{.items[*].spec.csi.driver}'
```

### 4.5 CSI Troubleshooting

```bash
# PVC stuck in Pending
kubectl describe pvc <pvc-name>
# Look for: Events showing provisioning errors

# Check CSI controller logs
kubectl logs -n kube-system -l app=ebs-csi-controller -c ebs-plugin

# Check CSI node logs
kubectl logs -n kube-system -l app=ebs-csi-node -c ebs-plugin

# Verify CSI driver registered
kubectl get csinodes
kubectl describe csinode <node-name>
```

> **Did You Know?**
>
> Before CSI, Kubernetes had "in-tree" storage plugins—code baked into Kubernetes itself for each storage provider. This was unsustainable. CSI allows storage vendors to develop drivers independently, released on their schedule, not Kubernetes' release cycle.

---

## Part 5: Quick Reference

### 5.1 Interface Summary

| Interface | Kubernetes Talks To | Plugin Provides | Config Location |
|-----------|--------------------|--------------------|-----------------|
| CRI | Container runtime | Container lifecycle | `/var/run/containerd/` |
| CNI | Network plugin | Pod IPs, routing, policies | `/etc/cni/net.d/` |
| CSI | Storage driver | Volume provisioning, mount | CSI Driver CRDs |

### 5.2 Troubleshooting Cheatsheet

```bash
# ===== CRI Issues =====
# Symptom: Pods won't start, "container runtime not running"
systemctl status containerd
journalctl -u containerd
crictl info

# ===== CNI Issues =====
# Symptom: Pods stuck in ContainerCreating, "network not ready"
ls /etc/cni/net.d/
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel"
kubectl logs -n kube-system <cni-pod>

# ===== CSI Issues =====
# Symptom: PVC stuck in Pending, "provisioning failed"
kubectl get csidrivers
kubectl describe pvc <name>
kubectl logs -n kube-system <csi-controller-pod>
```

---

## Did You Know?

- **CNI configuration file order matters**. Kubernetes uses the first file alphabetically in `/etc/cni/net.d/`. That's why you see files named `10-calico.conflist`—the number ensures ordering.

- **CSI replaced Flexvolume**. Flexvolume was the predecessor, but it required plugins on every node and had security issues. CSI runs as containerized workloads.

- **Cilium uses eBPF** instead of iptables for networking. This makes it faster and more observable, but requires a modern Linux kernel (4.9+).

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Forgetting to install CNI | Pods stuck in ContainerCreating | Install CNI plugin after kubeadm init |
| Multiple CNI configs | Wrong plugin used | Remove old configs, keep one |
| Wrong CSI driver | PVC won't bind | Match StorageClass to your infrastructure |
| Ignoring CSI controller logs | Can't diagnose provisioning | Always check controller and node plugin logs |
| Using docker on new clusters | Command not found | Use crictl instead |

---

## Quiz

1. **What's the difference between CNI and CSI?**
   <details>
   <summary>Answer</summary>
   CNI (Container Network Interface) handles pod networking—IP assignment, routing, and network policies. CSI (Container Storage Interface) handles persistent storage—provisioning, attaching, and mounting volumes.
   </details>

2. **Where are CNI configuration files stored?**
   <details>
   <summary>Answer</summary>
   `/etc/cni/net.d/` on each node. The first file alphabetically is used, which is why files are typically prefixed with numbers like `10-calico.conflist`.
   </details>

3. **A pod is stuck in ContainerCreating with "network plugin not ready". What should you check?**
   <details>
   <summary>Answer</summary>
   1. Check if CNI pods are running: `kubectl get pods -n kube-system | grep -E "calico|cilium|flannel"`
   2. Check CNI config exists: `ls /etc/cni/net.d/`
   3. Check CNI binaries exist: `ls /opt/cni/bin/`
   4. Check CNI pod logs for errors
   </details>

4. **Why did Kubernetes deprecate Docker as a container runtime?**
   <details>
   <summary>Answer</summary>
   Docker wasn't CRI-compliant—it required a shim (dockershim) built into kubelet. Maintaining this shim was burdensome. containerd and CRI-O implement CRI natively, simplifying the architecture. Docker images still work because they're OCI-compliant.
   </details>

---

## Hands-On Exercise

**Task**: Explore your cluster's CNI and CRI configuration.

**Steps**:

1. **Identify your container runtime**:
```bash
kubectl get nodes -o wide
# Note the CONTAINER-RUNTIME column
```

2. **Explore CRI**:
```bash
# On a node (SSH or kubectl debug node)
crictl info
crictl ps
crictl images | head -10
```

3. **Identify your CNI plugin**:
```bash
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel|weave"
```

4. **Check CNI configuration**:
```bash
# On a node
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/*.conflist | head -30
```

5. **Check pod networking**:
```bash
# Create two pods
kubectl run test1 --image=nginx
kubectl run test2 --image=nginx

# Get their IPs
kubectl get pods -o wide

# Test connectivity
kubectl exec test1 -- curl -s <test2-ip>:80
```

6. **Check CSI drivers** (if available):
```bash
kubectl get csidrivers
kubectl get storageclasses
```

**Success Criteria**:
- [ ] Can identify container runtime in use
- [ ] Can use crictl to inspect containers
- [ ] Can identify CNI plugin and its configuration
- [ ] Understand pod-to-pod networking path
- [ ] Know where to look for each interface's logs

**Cleanup**:
```bash
kubectl delete pod test1 test2
```

---

## Practice Drills

### Drill 1: Interface Identification (Target: 2 minutes)

Match each tool/plugin to its interface:

| Tool/Plugin | Interface (CRI/CNI/CSI) |
|-------------|-------------------------|
| containerd | ___ |
| Calico | ___ |
| AWS EBS driver | ___ |
| CRI-O | ___ |
| Cilium | ___ |
| Rook-Ceph | ___ |

<details>
<summary>Answers</summary>

1. CRI - Container Runtime Interface
2. CNI - Container Network Interface
3. CSI - Container Storage Interface
4. CRI - Container Runtime Interface
5. CNI - Container Network Interface
6. CSI - Container Storage Interface

</details>

### Drill 2: CRI Troubleshooting - Container Runtime Down (Target: 5 minutes)

```bash
# Setup: Stop containerd (WARNING: breaks cluster temporarily!)
# Only do on practice nodes you can restart!
sudo systemctl stop containerd

# Observe the damage
kubectl get nodes  # Node becomes NotReady
kubectl describe node <your-node> | grep -A5 Conditions

# YOUR TASK: Restore containerd and verify recovery
```

<details>
<summary>Solution</summary>

```bash
sudo systemctl start containerd
sudo systemctl status containerd

# Wait for node to recover
kubectl get nodes -w  # Watch until Ready

# Verify containers running
sudo crictl ps
```

</details>

### Drill 3: CNI Troubleshooting - Pods Stuck in ContainerCreating (Target: 5 minutes)

```bash
# Setup: Temporarily break CNI config
sudo mv /etc/cni/net.d/10-calico.conflist /tmp/

# Create a test pod
kubectl run cni-broken --image=nginx

# Observe
kubectl get pods  # ContainerCreating forever
kubectl describe pod cni-broken | grep -A10 Events

# YOUR TASK: Diagnose and fix
```

<details>
<summary>Solution</summary>

```bash
# Check CNI config directory
ls /etc/cni/net.d/  # Empty!

# Restore CNI config
sudo mv /tmp/10-calico.conflist /etc/cni/net.d/

# Delete stuck pod and recreate
kubectl delete pod cni-broken --force --grace-period=0
kubectl run cni-fixed --image=nginx
kubectl get pods  # Running!

# Cleanup
kubectl delete pod cni-fixed
```

</details>

### Drill 4: crictl Mastery (Target: 3 minutes)

Practice using crictl commands:

```bash
# 1. List all running containers
sudo crictl ps

# 2. List all pods (sandbox containers)
sudo crictl pods

# 3. Get container logs
sudo crictl logs <container-id>

# 4. Inspect a container
sudo crictl inspect <container-id> | head -50

# 5. List images
sudo crictl images

# 6. Get runtime info
sudo crictl info
```

### Drill 5: CSI Driver Investigation (Target: 3 minutes)

Explore CSI drivers in your cluster:

```bash
# List all CSI drivers
kubectl get csidrivers

# Get details on a driver
kubectl describe csidriver <driver-name>

# Check CSI nodes
kubectl get csinodes
kubectl describe csinode <node-name>

# View StorageClasses using CSI
kubectl get sc -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.provisioner}{"\n"}{end}'
```

### Drill 6: CSI Provisioning - Create PVC with StorageClass (Target: 5 minutes)

Practice the full CSI workflow from PVC to mounted volume:

```bash
# Check available StorageClasses
kubectl get sc

# Create a PVC using the default StorageClass
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: csi-test-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  # storageClassName: standard  # Uncomment to use specific class
EOF

# Watch the PVC get bound (CSI provisioner creates PV)
kubectl get pvc csi-test-pvc -w

# Check the dynamically provisioned PV
kubectl get pv

# Create a pod that uses the PVC
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: csi-test-pod
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
      claimName: csi-test-pvc
EOF

# Wait for pod to be ready
kubectl wait --for=condition=ready pod/csi-test-pod --timeout=60s

# Verify the volume is mounted
kubectl exec csi-test-pod -- df -h /data

# Write test data
kubectl exec csi-test-pod -- sh -c "echo 'CSI works!' > /data/test.txt"
kubectl exec csi-test-pod -- cat /data/test.txt

# Cleanup
kubectl delete pod csi-test-pod
kubectl delete pvc csi-test-pvc
```

### Drill 7: Network Connectivity Test (Target: 5 minutes)

Verify CNI is working correctly:

```bash
# Create pods on different nodes
kubectl run net-test-1 --image=nginx --overrides='{"spec":{"nodeName":"worker-01"}}'
kubectl run net-test-2 --image=nginx --overrides='{"spec":{"nodeName":"worker-02"}}'

# Wait for running
kubectl wait --for=condition=ready pod/net-test-1 pod/net-test-2 --timeout=60s

# Get IPs
POD1_IP=$(kubectl get pod net-test-1 -o jsonpath='{.status.podIP}')
POD2_IP=$(kubectl get pod net-test-2 -o jsonpath='{.status.podIP}')

# Test cross-node connectivity
kubectl exec net-test-1 -- curl -s --connect-timeout 5 $POD2_IP:80
kubectl exec net-test-2 -- curl -s --connect-timeout 5 $POD1_IP:80

# Cleanup
kubectl delete pod net-test-1 net-test-2
```

### Drill 8: Challenge - Identify All Plugins

Without documentation, identify all plugins in your cluster:

```bash
# 1. Find container runtime
kubectl get nodes -o wide | awk '{print $NF}'

# 2. Find CNI plugin
ls /etc/cni/net.d/
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel|weave"

# 3. Find CSI drivers
kubectl get csidrivers
kubectl get sc

# Write down what you found - this is exam knowledge!
```

---

## Next Module

[Module 1.3: Helm](../module-1.3-helm/) - Package management for Kubernetes, deploying applications with charts.
