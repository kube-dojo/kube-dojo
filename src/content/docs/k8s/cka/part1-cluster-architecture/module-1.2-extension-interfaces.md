---
title: "Module 1.2: Extension Interfaces - CNI, CSI, CRI"
slug: k8s/cka/part1-cluster-architecture/module-1.2-extension-interfaces
sidebar:
  order: 3
lab:
  id: cka-1.2-extension-interfaces
  url: https://killercoda.com/kubedojo/scenario/cka-1.2-extension-interfaces
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Conceptual with some hands-on
>
> **Time to Complete**: 30-40 minutes
>
> **Prerequisites**: Module 1.1 (Control Plane)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Explain** the plugin architecture (CNI, CSI, CRI) and why Kubernetes uses interfaces instead of built-in implementations
- **Identify** which runtime, network, and storage plugins are installed on a cluster
- **Diagnose** plugin failures by checking pod logs, socket files, and kubelet configuration
- **Compare** common implementations (containerd vs CRI-O, Calico vs Cilium, local vs CSI drivers) and their trade-offs

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

> **Pause and predict**: Why does Kubernetes use a gRPC interface (CRI) to talk to container runtimes instead of just calling containerd functions directly? What advantage does this indirection give you as a cluster operator?

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

> **Stop and think**: You just ran `kubeadm init` and the node shows as Ready, but CoreDNS pods are stuck in Pending. What's missing, and why does this specific component fail before others?

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

> **What would happen if**: The CSI controller pod crashes but the CSI node plugins on each worker are still running. Can existing pods still read and write to their mounted volumes? Can new PVCs be provisioned?

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

> **Trade-off: Local Storage vs. Remote CSI**
> Local storage (like `hostpath` or local volumes) provides high performance and low latency because data is on the node's physical disk. However, it tightly couples the Pod to that specific node—if the node fails, the data is inaccessible. Remote CSI drivers (like EBS or Ceph) add network latency but allow Pods to float between nodes because the volume can be detached and reattached elsewhere, providing higher availability.

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

1. **Your team migrated from an on-prem cluster using Flannel to a new cluster using Cilium. A developer asks: "Do I need to change my Deployment manifests?" What's your answer, and what does this tell you about how CNI works?**
   <details>
   <summary>Answer</summary>
   No manifest changes are needed. CNI is an interface — Kubernetes defines a contract for pod networking (assign IPs, set up routes, enable pod-to-pod communication), and any compliant plugin fulfills that contract transparently. From the application's perspective, pods still get IPs, DNS works, and Services resolve the same way regardless of whether Flannel or Cilium handles the underlying networking. This is the core benefit of the plugin architecture: you can swap implementations without changing workloads. The only differences are operational — Cilium adds eBPF-based observability and network policy enforcement that Flannel lacks.
   </details>

2. **After a node reboot, pods on that node are stuck in ContainerCreating. You SSH into the node and find that `/etc/cni/net.d/` contains two files: `10-calico.conflist` and `05-flannel.conflist`. What's the problem and how do you fix it?**
   <details>
   <summary>Answer</summary>
   Kubernetes uses the first CNI configuration file alphabetically in `/etc/cni/net.d/`. Since `05-flannel.conflist` comes before `10-calico.conflist`, kubelet is trying to use Flannel for networking — but if your cluster runs Calico, the Flannel binaries and agents aren't present, causing the ContainerCreating state. The fix is to remove the stale Flannel config: `sudo rm /etc/cni/net.d/05-flannel.conflist`. This commonly happens when a previous CNI installation wasn't cleaned up properly. After removing it, the pods should start using Calico correctly.
   </details>

3. **A PersistentVolumeClaim has been in Pending state for 5 minutes. You run `kubectl get csidrivers` and see your EBS CSI driver listed. The CSI controller pods are running. Where should you look next, and what are two likely causes?**
   <details>
   <summary>Answer</summary>
   Run `kubectl describe pvc <name>` and check the Events section for provisioning error messages. Then check the CSI controller logs: `kubectl logs -n kube-system -l app=ebs-csi-controller -c ebs-plugin`. Two likely causes: (1) The StorageClass specified in the PVC doesn't match any available StorageClass, or the StorageClass references a different CSI driver than what's installed. (2) The CSI controller lacks IAM permissions to provision EBS volumes in AWS — the controller pod needs the right ServiceAccount and IAM role to call the AWS API. You can also check `kubectl get sc` to verify the StorageClass exists and its provisioner matches the CSI driver name.
   </details>

4. **A colleague upgrades a cluster from Kubernetes 1.23 to 1.25 and reports that all `docker ps` commands on nodes return "command not found," even though containers are still running. They're panicking about data loss. What do you tell them?**
   <details>
   <summary>Answer</summary>
   There's no data loss. Starting with Kubernetes 1.24, Docker (dockershim) was removed as a supported container runtime. The cluster now uses containerd directly, which was already running containers under Docker previously. The containers are still running — they just need to use `crictl ps` instead of `docker ps` to inspect them. All existing Docker images continue to work because they're OCI-compliant, meaning containerd can pull and run them without modification. The key distinction is that Docker was the runtime interface, not the image format — and containerd implements CRI natively, which is what kubelet actually needs.
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

# Wait for pods to be ready
kubectl wait --for=condition=Ready pod/test1 pod/test2 --timeout=60s

# Get their IPs
kubectl get pods -o wide

# Test connectivity
TEST2_IP=$(kubectl get pod test2 -o jsonpath='{.status.podIP}')
kubectl exec test1 -- curl -s $TEST2_IP:80
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
NODE_NAME=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl describe node $NODE_NAME | grep -A5 Conditions

# YOUR TASK: Restore containerd and verify recovery
```

<details>
<summary>Solution</summary>

```bash
sudo systemctl start containerd
sudo systemctl status containerd

# Wait for node to recover
kubectl wait --for=condition=Ready node --all --timeout=120s

# Verify containers running
sudo crictl ps
```

</details>

### Drill 3: CNI Troubleshooting - Pods Stuck in ContainerCreating (Target: 5 minutes)

```bash
# Setup: Temporarily break CNI config
sudo mkdir -p /tmp/cni-backup
sudo mv /etc/cni/net.d/* /tmp/cni-backup/

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
sudo mv /tmp/cni-backup/* /etc/cni/net.d/

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
CONT_ID=$(sudo crictl ps -q | head -n 1)
sudo crictl logs $CONT_ID

# 4. Inspect a container
sudo crictl inspect $CONT_ID | head -50

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
DRIVER_NAME=$(kubectl get csidrivers -o jsonpath='{.items[0].metadata.name}')
kubectl describe csidriver $DRIVER_NAME

# Check CSI nodes
kubectl get csinodes
NODE_NAME=$(kubectl get csinodes -o jsonpath='{.items[0].metadata.name}')
kubectl describe csinode $NODE_NAME

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
kubectl wait --for=jsonpath='{.status.phase}'=Bound pvc/csi-test-pvc --timeout=60s

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
kubectl wait --for=condition=Ready pod/csi-test-pod --timeout=60s

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
NODE1=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
NODE2=$(kubectl get nodes -o jsonpath='{.items[1].metadata.name}')
NODE2=${NODE2:-$NODE1}
kubectl run net-test-1 --image=nginx --overrides='{"spec":{"nodeName":"'"$NODE1"'"}}'
kubectl run net-test-2 --image=nginx --overrides='{"spec":{"nodeName":"'"$NODE2"'"}}'

# Wait for running
kubectl wait --for=condition=Ready pod/net-test-1 pod/net-test-2 --timeout=60s

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
