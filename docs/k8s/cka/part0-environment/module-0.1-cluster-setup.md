# Module 0.1: Cluster Setup

> **Complexity**: `[MEDIUM]` - Takes time but straightforward if you follow steps
>
> **Time to Complete**: 45-60 minutes (first time), 15-20 minutes (once familiar)
>
> **Prerequisites**: Two or more machines (physical, VMs, or cloud instances)

---

## Why This Module Matters

You can't practice Kubernetes administration without a Kubernetes cluster. Sounds obvious, right? Yet many CKA candidates rely entirely on managed clusters (EKS, GKE, AKS) or single-node setups (minikube, kind) and then freeze when the exam asks them to troubleshoot kubelet on a worker node.

The CKA exam runs on **kubeadm-provisioned clusters**. Not managed Kubernetes. Not Docker Desktop. Real kubeadm clusters with separate control plane and worker nodes.

This module teaches you to build exactly what you'll encounter in the exam.

> **The Orchestra Analogy**
>
> Think of a Kubernetes cluster like an orchestra. The **control plane** is the conductor—it doesn't play any instruments (run your apps), but it coordinates everything: who plays when, how loud, when to start and stop. The **worker nodes** are the musicians—they do the actual work of producing music (running containers). Without a conductor, you have chaos. Without musicians, you have silence. You need both, working together, communicating constantly.

---

## What You'll Build

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Practice Cluster                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │   cp-node   │    │  worker-01  │    │  worker-02  │        │
│   │ (control)   │    │             │    │             │        │
│   │             │    │             │    │             │        │
│   │ • API Server│    │ • kubelet   │    │ • kubelet   │        │
│   │ • etcd      │    │ • kube-proxy│    │ • kube-proxy│        │
│   │ • scheduler │    │ • containerd│    │ • containerd│        │
│   │ • ctrl-mgr  │    │             │    │             │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                   │                   │               │
│         └───────────────────┴───────────────────┘               │
│                        Pod Network (Calico)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**1 control plane node + 2 worker nodes** = realistic cluster for CKA practice.

---

## Choose Your Infrastructure

You need 3 machines. Here are your options:

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **VMs on Mac (UTM/Parallels)** | Local, no network issues | Resource heavy | Free (UTM) |
| **VMs on Linux (KVM/libvirt)** | Native performance | Linux host required | Free |
| **Cloud VMs (AWS/GCP/Azure)** | Closest to exam environment | Costs money | ~$0.10/hr |
| **Bare metal** | Best performance | Need hardware | Existing |
| **Raspberry Pi cluster** | Fun project, low power | ARM quirks | ~$200 |

### Minimum Specs Per Node

| Resource | Control Plane | Worker |
|----------|--------------|--------|
| CPU | 2 cores | 2 cores |
| RAM | 2 GB | 2 GB |
| Disk | 20 GB | 20 GB |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

> **Did You Know?**
>
> The CKA exam environment uses Ubuntu-based nodes. While Kubernetes runs on many distributions, practicing on Ubuntu means fewer surprises on exam day.

---

## Part 1: Prepare All Nodes

Run these steps on **ALL THREE nodes** (control plane AND workers).

### 1.1 Set Hostnames

On each node, set a meaningful hostname:

```bash
# On control plane node
sudo hostnamectl set-hostname cp-node

# On first worker
sudo hostnamectl set-hostname worker-01

# On second worker
sudo hostnamectl set-hostname worker-02
```

### 1.2 Update /etc/hosts

Add all nodes to `/etc/hosts` on EACH machine:

```bash
sudo tee -a /etc/hosts << EOF
192.168.1.10  cp-node
192.168.1.11  worker-01
192.168.1.12  worker-02
EOF
```

Replace the IPs with your actual node IPs.

### 1.3 Disable Swap

Kubernetes requires swap to be disabled. This is non-negotiable.

```bash
# Disable swap immediately
sudo swapoff -a

# Disable swap permanently (survives reboot)
sudo sed -i '/ swap / s/^/#/' /etc/fstab
```

> **War Story: The Mysterious OOMKill**
>
> A team spent days debugging why their pods kept getting OOMKilled despite having plenty of memory. The culprit? Swap was enabled. When the kubelet reported memory to the scheduler, it didn't account for swap, leading to over-scheduling and eventual memory pressure. Kubernetes doesn't manage swap—it expects you to disable it.

### 1.4 Load Kernel Modules

Kubernetes networking requires specific kernel modules:

```bash
# Load modules now
sudo modprobe overlay
sudo modprobe br_netfilter

# Ensure they load on boot
cat << EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
```

### 1.5 Configure Sysctl

Enable IP forwarding and bridge netfilter:

```bash
cat << EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply immediately
sudo sysctl --system
```

### 1.6 Verify cgroup v2

**Starting with Kubernetes 1.35, cgroup v1 support is disabled by default.** Your nodes must run cgroup v2 or the kubelet will fail to start.

```bash
# Check cgroup version (must show "cgroup2fs")
stat -fc %T /sys/fs/cgroup
# Expected output: cgroup2fs

# If it shows "tmpfs", you're on cgroup v1 — you need a newer OS
# Affected: CentOS 7, RHEL 7, Ubuntu 18.04
# Supported: Ubuntu 22.04+, Debian 12+, RHEL 9+, Rocky 9+
```

> **Breaking Change Alert**: If `stat -fc %T /sys/fs/cgroup` returns `tmpfs` instead of `cgroup2fs`, upgrade your OS before proceeding. Kubernetes 1.35 will not start on cgroup v1 nodes.

### 1.7 Install containerd

Kubernetes needs a container runtime. **containerd 2.0+** is required (1.35 is the last version supporting containerd 1.x):

```bash
# Install containerd (ensure version 2.0+)
sudo apt-get update
sudo apt-get install -y containerd

# Verify version
containerd --version
# Should be 2.0.0 or later

# Create default config
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Enable systemd cgroup driver (IMPORTANT!)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart containerd
sudo systemctl restart containerd
sudo systemctl enable containerd
```

> **Gotcha: SystemdCgroup**
>
> If you skip setting `SystemdCgroup = true`, you'll get cryptic errors later. The kubelet and containerd must agree on the cgroup driver. Modern systems use systemd. Don't miss this step.

> **Gotcha: containerd 2.0 and old images**
>
> containerd 2.0 removes support for Docker Schema 1 images. If you have very old images (pushed 5+ years ago), they will fail to pull. Rebuild or re-push them with a modern Docker/buildkit.

### 1.8 Install kubeadm, kubelet, kubectl

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes repository key
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add Kubernetes repository
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install components
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl

# Prevent automatic updates (version consistency matters)
sudo apt-mark hold kubelet kubeadm kubectl
```

### 1.9 Verify Setup

Run on each node:

```bash
# Check containerd
sudo systemctl status containerd

# Check kubelet (will be inactive until cluster is initialized)
sudo systemctl status kubelet

# Check kubeadm version
kubeadm version
```

---

## Part 2: Initialize Control Plane

Run these steps **ONLY on the control plane node** (cp-node).

### 2.1 Initialize the Cluster

```bash
sudo kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --control-plane-endpoint=cp-node:6443
```

This takes 2-3 minutes. When complete, you'll see output like:

```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join cp-node:6443 --token abcdef.0123456789abcdef \
    --discovery-token-ca-cert-hash sha256:...
```

**SAVE THE JOIN COMMAND!** You'll need it for the workers.

### 2.2 Configure kubectl

As a regular user (not root):

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 2.3 Verify Control Plane

```bash
kubectl get nodes
```

Output:
```
NAME      STATUS     ROLES           AGE   VERSION
cp-node   NotReady   control-plane   1m    v1.35.0
```

The node shows `NotReady` because we haven't installed a network plugin yet.

---

## Part 3: Install Network Plugin (CNI)

Kubernetes doesn't come with networking. You must install a CNI plugin. We'll use Calico (widely used, exam-friendly).

> **Why Doesn't Kubernetes Include Networking?**
>
> This surprises everyone at first. Kubernetes made a deliberate choice to define a networking *model* (every pod gets an IP, pods can reach each other) but not *implement* it. Why? Because networking needs vary wildly—some need advanced policies, some need high performance, some need cloud integration. By using the CNI (Container Network Interface) standard, Kubernetes lets you choose. Calico, Flannel, Cilium, Weave—they all implement the same interface but with different superpowers. It's like USB: the standard defines how to connect, but you choose your device.

**On the control plane node:**

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```

Wait for Calico pods to be ready:

```bash
kubectl get pods -n kube-system -w
```

After 1-2 minutes, check node status:

```bash
kubectl get nodes
```

Output:
```
NAME      STATUS   ROLES           AGE   VERSION
cp-node   Ready    control-plane   5m    v1.35.0
```

`Ready`! The control plane is operational.

---

## Part 4: Join Worker Nodes

Run these steps on **EACH worker node** (worker-01 and worker-02).

### 4.1 Join the Cluster

Use the join command from `kubeadm init` output:

```bash
sudo kubeadm join cp-node:6443 --token abcdef.0123456789abcdef \
    --discovery-token-ca-cert-hash sha256:...
```

> **Gotcha: Token Expired?**
>
> Tokens expire after 24 hours. If your token expired:
> ```bash
> # On control plane, generate new token
> kubeadm token create --print-join-command
> ```

### 4.2 Verify Workers Joined

**On the control plane node:**

```bash
kubectl get nodes
```

Output:
```
NAME        STATUS   ROLES           AGE   VERSION
cp-node     Ready    control-plane   10m   v1.35.0
worker-01   Ready    <none>          2m    v1.35.0
worker-02   Ready    <none>          1m    v1.35.0
```

All nodes `Ready`! Your cluster is operational.

> **War Story: The Phantom Node**
>
> An engineer once spent an hour trying to figure out why their "3-node cluster" only had 2 nodes showing. They ran `kubeadm join` on all three machines. Turns out, they ran it on the control plane node by mistake (instead of a worker), which silently failed because that node was already in the cluster. The lesson: always verify which node you're SSH'd into before running commands. The hostname in your terminal prompt is your friend.

### 4.3 Label Worker Nodes (Optional but Recommended)

```bash
kubectl label node worker-01 node-role.kubernetes.io/worker=
kubectl label node worker-02 node-role.kubernetes.io/worker=
```

Now `kubectl get nodes` shows:
```
NAME        STATUS   ROLES           AGE   VERSION
cp-node     Ready    control-plane   10m   v1.35.0
worker-01   Ready    worker          3m    v1.35.0
worker-02   Ready    worker          2m    v1.35.0
```

---

## Part 5: Verify Your Cluster

Run these tests to confirm everything works:

### 5.1 Deploy a Test Application

```bash
kubectl create deployment nginx --image=nginx --replicas=3
kubectl expose deployment nginx --port=80 --type=NodePort
```

### 5.2 Check Pods Distributed Across Nodes

```bash
kubectl get pods -o wide
```

You should see pods running on different worker nodes:
```
NAME                     READY   STATUS    NODE
nginx-77b4fdf86c-abc12   1/1     Running   worker-01
nginx-77b4fdf86c-def34   1/1     Running   worker-02
nginx-77b4fdf86c-ghi56   1/1     Running   worker-01
```

### 5.3 Test Connectivity

```bash
# Get NodePort
kubectl get svc nginx

# Test from any node
curl http://worker-01:<nodeport>
```

### 5.4 Clean Up Test Resources

```bash
kubectl delete deployment nginx
kubectl delete svc nginx
```

---

## Quick Reference: Commands You'll Use Often

```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes
kubectl get pods -A

# Check component health
kubectl get componentstatuses  # deprecated but still works

# SSH to nodes for troubleshooting
ssh worker-01 "sudo systemctl status kubelet"
ssh worker-01 "sudo journalctl -u kubelet -f"

# Reset a node (start over)
sudo kubeadm reset
```

---

## Did You Know?

- **kubeadm** was created specifically to make cluster setup straightforward. Before kubeadm, setting up Kubernetes involved manually generating certificates, writing systemd unit files, and configuring each component by hand. Some people still do this ("Kubernetes the Hard Way") for learning, but kubeadm is the production standard.

- **The CKA exam uses kubeadm clusters**. You won't see managed Kubernetes (EKS/GKE/AKS) on the exam. Everything is kubeadm-based, which is why practicing on kubeadm matters.

- **containerd replaced Docker** as the default container runtime in Kubernetes 1.24. Docker still works (via cri-dockerd), but containerd is simpler and what you'll encounter in the exam.

---

## Common Mistakes

| Problem | Cause | Solution |
|---------|-------|----------|
| `kubelet` keeps restarting | Swap enabled | `sudo swapoff -a` |
| Nodes stuck in `NotReady` | No CNI installed | Install Calico/Flannel |
| `kubeadm init` hangs | Firewall blocking ports | Open ports 6443, 10250 |
| Token expired | Tokens last 24h | `kubeadm token create --print-join-command` |
| `connection refused` to API | Wrong kubeconfig | Check `~/.kube/config` |

---

## Quiz

1. **Why must swap be disabled for Kubernetes?**
   <details>
   <summary>Answer</summary>
   Kubernetes expects to manage memory directly. With swap enabled, the kubelet can't accurately report memory usage, leading to over-scheduling and unpredictable behavior. The scheduler needs reliable memory information.
   </details>

2. **What's the purpose of the `--pod-network-cidr` flag in `kubeadm init`?**
   <details>
   <summary>Answer</summary>
   It defines the IP range for pod networking. The CNI plugin (like Calico) uses this range to assign IPs to pods. Different CNIs have different requirements—Calico is flexible, but Flannel requires 10.244.0.0/16 by default.
   </details>

3. **A node shows `NotReady` after joining. What's the most likely cause?**
   <details>
   <summary>Answer</summary>
   CNI plugin not installed or not running. Without a CNI, pods can't get network addresses, and the node reports NotReady. Check `kubectl get pods -n kube-system` for CNI pod status.
   </details>

4. **You need to add a new worker node but lost the join command. How do you get it?**
   <details>
   <summary>Answer</summary>
   Run `kubeadm token create --print-join-command` on the control plane node. This generates a new token and prints the complete join command.
   </details>

---

## Hands-On Exercise

**Task**: Build your practice cluster following this guide.

**Success Criteria**:
- [ ] 3 nodes showing `Ready` in `kubectl get nodes`
- [ ] Calico pods running in `kube-system` namespace
- [ ] Can deploy a pod and have it scheduled to a worker node
- [ ] Can SSH to worker and check kubelet status

**Verification**:
```bash
# All nodes ready?
kubectl get nodes | grep -c "Ready"  # Should output: 3

# Calico running?
kubectl get pods -n kube-system | grep calico

# Pods scheduling to workers?
kubectl run test --image=nginx
kubectl get pod test -o wide  # Should show worker node
kubectl delete pod test
```

---

## Practice Drills

### Drill 1: Node Health Check (Target: 2 minutes)

Verify your cluster is healthy. Run these commands and confirm expected output:

```bash
# All nodes Ready?
kubectl get nodes
# Expected: 3 nodes, all STATUS=Ready

# All system pods running?
kubectl get pods -n kube-system | grep -v Running
# Expected: No output (all pods Running)

# Can schedule workloads?
kubectl run test --image=nginx --rm -it --restart=Never -- echo "Cluster healthy"
# Expected: "Cluster healthy" then pod deleted
```

### Drill 2: Troubleshooting - Node NotReady (Target: 5 minutes)

**Scenario**: Simulate a node going NotReady and fix it.

```bash
# On worker-01, stop kubelet
sudo systemctl stop kubelet

# On control plane, watch node status
kubectl get nodes -w
# Wait until worker-01 shows NotReady

# Diagnose the issue
kubectl describe node worker-01 | grep -A5 Conditions

# Fix: Restart kubelet on worker-01
sudo systemctl start kubelet

# Verify recovery
kubectl get nodes
```

**What you learned**: kubelet health directly affects node status.

### Drill 3: Troubleshooting - CNI Failure (Target: 5 minutes)

**Scenario**: Pods stuck in ContainerCreating after CNI issues.

```bash
# Create a test pod
kubectl run cni-test --image=nginx

# Check status (should be Running if CNI works)
kubectl get pod cni-test

# If ContainerCreating, diagnose:
kubectl describe pod cni-test | grep -A10 Events
kubectl get pods -n kube-system | grep calico

# Common fix: Restart CNI pods
kubectl delete pods -n kube-system -l k8s-app=calico-node

# Cleanup
kubectl delete pod cni-test
```

### Drill 4: Reset and Rebuild (Target: 15 minutes)

**Challenge**: Practice cluster recovery by resetting a worker and rejoining.

```bash
# On worker-01: Reset the node
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d

# On control plane: Remove the node
kubectl delete node worker-01

# On control plane: Generate new join command
kubeadm token create --print-join-command

# On worker-01: Rejoin
sudo kubeadm join <command-from-above>

# Verify
kubectl get nodes
```

### Drill 5: Challenge - Add a Third Worker (Target: 20 minutes)

**No guidance provided.** Using only what you learned in this module:

1. Prepare a new VM with the same base setup
2. Join it to the cluster as `worker-03`
3. Verify it's Ready and can schedule pods
4. Label it with `node-role.kubernetes.io/worker=`

<details>
<summary>Hints (only if stuck)</summary>

1. Run all Part 1 steps (1.1-1.8) on the new node
2. Get join command: `kubeadm token create --print-join-command`
3. Label: `kubectl label node worker-03 node-role.kubernetes.io/worker=`

</details>

### Drill 6: Fix the Broken Cluster

**Scenario**: Your colleague broke something. Fix it.

```bash
# Setup: Run this to break the cluster (on control plane)
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/

# Problem: New pods won't schedule
kubectl run broken-test --image=nginx
kubectl get pods  # STATUS: Pending forever

# YOUR TASK: Figure out why and fix it
# Hint: Check control plane components
```

<details>
<summary>Solution</summary>

```bash
# Check what's running in kube-system
kubectl get pods -n kube-system
# Notice: No scheduler pod!

# Check manifest directory
ls /etc/kubernetes/manifests/
# Notice: kube-scheduler.yaml is missing

# Fix: Restore the scheduler
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/

# Wait for scheduler to restart
kubectl get pods -n kube-system | grep scheduler

# Verify pod now schedules
kubectl get pods  # Should transition to Running
kubectl delete pod broken-test
```

</details>

---

## Next Module

[Module 0.2: Shell Mastery](module-0.2-shell-mastery.md) - Aliases, autocomplete, and shell optimization for speed.
