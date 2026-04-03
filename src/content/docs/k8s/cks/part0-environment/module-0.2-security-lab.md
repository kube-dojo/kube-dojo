---
title: "Module 0.2: Security Lab Setup"
slug: k8s/cks/part0-environment/module-0.2-security-lab
sidebar:
  order: 2
lab:
  id: cks-0.2-security-lab
  url: https://killercoda.com/kubedojo/scenario/cks-0.2-security-lab
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Multiple tools to install
>
> **Time to Complete**: 45-60 minutes
>
> **Prerequisites**: Working Kubernetes cluster (from CKA), kubectl configured

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Deploy** a security-focused Kubernetes lab with Trivy, Falco, and kube-bench installed
2. **Configure** cluster components for security testing and vulnerability scanning
3. **Diagnose** common lab setup issues with security tool installations
4. **Create** reproducible lab environments for practicing CKS exam scenarios

---

## Why This Module Matters

CKS requires hands-on practice with security tools. You can't learn Trivy from documentation alone—you need to scan images, see vulnerabilities, and practice remediation. Same with Falco: writing rules requires a running instance generating alerts.

This module builds your security lab: a cluster equipped with all tools you'll encounter on the exam.

---

## Lab Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              CKS SECURITY LAB                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Kubernetes Cluster                        │   │
│  │                                                     │   │
│  │  Security Tools Deployed:                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐            │   │
│  │  │ Falco   │ │ Trivy   │ │ kube-bench│            │   │
│  │  │(runtime)│ │(scanner)│ │(CIS audit)│            │   │
│  │  └─────────┘ └─────────┘ └───────────┘            │   │
│  │                                                     │   │
│  │  Security Features Enabled:                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐            │   │
│  │  │AppArmor │ │ seccomp │ │  Audit    │            │   │
│  │  │profiles │ │profiles │ │  Logging  │            │   │
│  │  └─────────┘ └─────────┘ └───────────┘            │   │
│  │                                                     │   │
│  │  Vulnerable Apps (for practice):                   │   │
│  │  ┌─────────────────────────────────────────┐      │   │
│  │  │ Intentionally insecure deployments      │      │   │
│  │  │ for scanning and hardening practice     │      │   │
│  │  └─────────────────────────────────────────┘      │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Option 1: Kind Cluster (Recommended for Learning)

For most CKS study, a kind cluster with security tools works well:

```bash
# Create kind cluster with audit logging enabled
cat <<EOF > kind-cks.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        audit-policy-file: /etc/kubernetes/audit-policy.yaml
        audit-log-path: /var/log/kubernetes/audit.log
        audit-log-maxage: "30"
        audit-log-maxbackup: "3"
        audit-log-maxsize: "100"
      extraVolumes:
      - name: audit-policy
        hostPath: /etc/kubernetes/audit-policy.yaml
        mountPath: /etc/kubernetes/audit-policy.yaml
        readOnly: true
        pathType: File
      - name: audit-logs
        hostPath: /var/log/kubernetes
        mountPath: /var/log/kubernetes
        pathType: DirectoryOrCreate
  extraMounts:
  - hostPath: ./audit-policy.yaml
    containerPath: /etc/kubernetes/audit-policy.yaml
    readOnly: true
  - hostPath: ./audit-logs
    containerPath: /var/log/kubernetes
- role: worker
- role: worker
EOF

# Create the audit log directory on the host
mkdir -p audit-logs

# Create basic audit policy
cat <<EOF > audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Request
  resources:
  - group: ""
    resources: ["pods"]
- level: None
  users: ["system:kube-proxy"]
  verbs: ["watch"]
  resources:
  - group: ""
    resources: ["endpoints", "services"]
- level: Metadata
  omitStages:
  - RequestReceived
EOF

# Create the cluster
kind create cluster --name cks-lab --config kind-cks.yaml
```

---

## Option 2: Kubeadm Cluster (Closer to Exam)

If you have a kubeadm cluster from CKA practice, add security configurations:

```bash
# Enable audit logging on existing cluster
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml on control plane

# Add these flags to the API server:
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# --audit-log-path=/var/log/kubernetes/audit.log
# --audit-log-maxage=30
# --audit-log-maxbackup=3
# --audit-log-maxsize=100

# Create the audit policy file
sudo mkdir -p /etc/kubernetes
sudo tee /etc/kubernetes/audit-policy.yaml <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods"]
    verbs: ["create", "delete"]
- level: Metadata
  omitStages:
  - RequestReceived
EOF

# Create log directory
sudo mkdir -p /var/log/kubernetes
```

---

## Install Security Tools

### 1. Trivy (Image Scanner)

```bash
# Install Trivy CLI
# On Ubuntu/Debian
sudo apt-get install wget apt-transport-https gnupg lsb-release -y
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy -y

# On macOS
brew install trivy

# Verify installation
trivy --version

# Test scan
trivy image nginx:latest
```

### 2. Falco (Runtime Security)

```bash
# Install Falco using Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install Falco with modern eBPF driver
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=modern_ebpf \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# For kind clusters, use kernel module driver instead
# helm install falco falcosecurity/falco \
#   --namespace falco \
#   --create-namespace \
#   --set driver.kind=kmod

# Verify Falco is running
kubectl get pods -n falco

# Check Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco
```

### 3. kube-bench (CIS Benchmark)

```bash
# Run kube-bench as a job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Wait for completion
kubectl wait --for=condition=complete job/kube-bench --timeout=120s

# View results
kubectl logs job/kube-bench

# For detailed output, run interactively on control plane node
# Download and run kube-bench directly
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.7.0/kube-bench_0.7.0_linux_amd64.tar.gz -o kube-bench.tar.gz
tar -xvf kube-bench.tar.gz
./kube-bench run --targets=master
```

### 4. kubesec (Static Analysis)

```bash
# Install kubesec
# Binary installation
wget https://github.com/controlplaneio/kubesec/releases/download/v2.14.0/kubesec_linux_amd64.tar.gz
tar -xvf kubesec_linux_amd64.tar.gz
sudo mv kubesec /usr/local/bin/

# Or use Docker
# docker run -i kubesec/kubesec scan /dev/stdin < deployment.yaml

# Test kubesec
cat <<EOF | kubesec scan /dev/stdin
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
  - name: test
    image: nginx
    securityContext:
      runAsUser: 0
EOF
```

---

## Verify AppArmor Support

```bash
# Check if AppArmor is enabled (on nodes)
cat /sys/module/apparmor/parameters/enabled
# Should output: Y

# List loaded profiles
sudo aa-status

# Check if container runtime supports AppArmor
# For containerd, it's enabled by default
```

---

## Verify Seccomp Support

```bash
# Check kernel seccomp support
grep CONFIG_SECCOMP /boot/config-$(uname -r)
# Should see: CONFIG_SECCOMP=y

# Kubernetes default seccomp profile location
ls /var/lib/kubelet/seccomp/

# Create a test seccomp profile directory
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
```

---

## Deploy Vulnerable Apps (Practice Targets)

Create intentionally insecure deployments for practice:

```bash
# Create namespace for practice
kubectl create namespace insecure-apps

# Deploy vulnerable app 1: Privileged container
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    securityContext:
      privileged: true
EOF

# Deploy vulnerable app 2: Root user
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: root-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    securityContext:
      runAsUser: 0
EOF

# Deploy vulnerable app 3: No resource limits
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: unlimited-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    # No resources specified = unlimited
EOF

# Deploy vulnerable app 4: Vulnerable image
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: vulnerable-image
  namespace: insecure-apps
spec:
  containers:
  - name: app
    image: vulnerables/web-dvwa  # Known vulnerable image
EOF
```

---

## Lab Validation Script

Run this to verify your lab is ready:

```bash
#!/bin/bash
echo "=== CKS Lab Validation ==="
echo ""

# Check cluster
echo "1. Cluster Status:"
kubectl cluster-info | head -2
echo ""

# Check Trivy
echo "2. Trivy:"
if command -v trivy &> /dev/null; then
    trivy --version
else
    echo "   NOT INSTALLED"
fi
echo ""

# Check Falco
echo "3. Falco:"
kubectl get pods -n falco -l app.kubernetes.io/name=falco --no-headers 2>/dev/null | head -1 || echo "   NOT RUNNING"
echo ""

# Check kube-bench
echo "4. kube-bench:"
if command -v kube-bench &> /dev/null; then
    echo "   Installed"
else
    echo "   Available as Job"
fi
echo ""

# Check AppArmor
echo "5. AppArmor:"
if [ -f /sys/module/apparmor/parameters/enabled ]; then
    cat /sys/module/apparmor/parameters/enabled
else
    echo "   Check on cluster nodes"
fi
echo ""

# Check Audit Logging
echo "6. Audit Logging:"
kubectl get pods -n kube-system kube-apiserver-* -o yaml 2>/dev/null | grep -q "audit-log-path" && echo "   Enabled" || echo "   Check API server config"
echo ""

echo "=== Validation Complete ==="
```

---

## Did You Know?

- **Falco can detect cryptomining** in real-time by monitoring for suspicious CPU patterns and network connections to mining pools.

- **Trivy scans more than images**—it can scan filesystems, git repositories, and Kubernetes manifests for misconfigurations.

- **The CIS Kubernetes Benchmark** has over 200 checks. kube-bench automates all of them.

- **AppArmor and SELinux are alternatives**—most Kubernetes environments use AppArmor (Ubuntu default) or SELinux (RHEL/CentOS default). CKS focuses on AppArmor.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No audit logging enabled | Can't practice audit-related tasks | Configure API server with audit policy |
| Falco not running | Can't practice runtime detection | Install via Helm, check driver |
| Only scanning images once | Need workflow practice | Integrate into routine |
| Skipping vulnerable app setup | No targets to practice hardening | Deploy intentionally insecure apps |
| Not checking node-level tools | AppArmor/seccomp are node features | SSH to nodes, verify support |

---

## Quiz

1. **What does Trivy scan for?**
   <details>
   <summary>Answer</summary>
   Vulnerabilities (CVEs) in container images, filesystem, git repos, and Kubernetes misconfigurations. It's primarily used for image vulnerability scanning in CKS.
   </details>

2. **Where do seccomp profiles need to be stored for Kubernetes to use them?**
   <details>
   <summary>Answer</summary>
   In /var/lib/kubelet/seccomp/ on the node where the pod runs. Kubernetes references profiles relative to this directory.
   </details>

3. **What is the purpose of deploying intentionally vulnerable applications?**
   <details>
   <summary>Answer</summary>
   Practice targets for security scanning and hardening. You can scan them with Trivy, detect issues with Falco, and practice remediation—all in a safe environment.
   </details>

4. **What driver options does Falco support?**
   <details>
   <summary>Answer</summary>
   Kernel module (kmod), eBPF probe, or modern_ebpf. Modern eBPF is preferred when supported. Kernel module is most compatible but requires kernel headers.
   </details>

---

## Hands-On Exercise

**Task**: Validate your security lab setup.

```bash
# 1. Verify cluster is running
kubectl get nodes

# 2. Install Trivy and scan an image
trivy image nginx:latest | head -50

# 3. Check Falco is running (if installed)
kubectl get pods -n falco

# 4. Run kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s
kubectl logs job/kube-bench | head -100

# 5. Create a test pod and scan it
kubectl run test-pod --image=nginx:1.25
trivy image nginx:1.25

# 6. Cleanup
kubectl delete pod test-pod
kubectl delete job kube-bench
```

**Success criteria**: Trivy scans images, kube-bench reports results, cluster is accessible.

---

## Summary

Your CKS lab needs:

**Tools installed**:
- Trivy (image scanning)
- Falco (runtime detection)
- kube-bench (CIS benchmarks)
- kubesec (static analysis)

**Cluster features enabled**:
- Audit logging
- AppArmor support (node-level)
- Seccomp support (node-level)

**Practice targets**:
- Intentionally vulnerable deployments
- Known-vulnerable images

This lab environment lets you practice every CKS exam domain hands-on.

---

## Next Module

[Module 0.3: Security Tool Mastery](../module-0.3-security-tools/) - Deep dive into Trivy, Falco, and kube-bench usage.
