---
title: "Module 1.2: CIS Benchmarks and kube-bench"
slug: k8s/cks/part1-cluster-setup/module-1.2-cis-benchmarks
sidebar:
  order: 2
lab:
  id: cks-1.2-cis-benchmarks
  url: https://killercoda.com/kubedojo/scenario/cks-1.2-cis-benchmarks
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core security auditing skill
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 0.3 (Security Tools), basic cluster administration

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Audit** a Kubernetes cluster against CIS benchmarks using kube-bench
2. **Diagnose** failing benchmark checks and trace them to specific configuration files
3. **Implement** remediation steps to harden API server, etcd, and kubelet settings
4. **Evaluate** which CIS recommendations are critical versus advisory for your environment

---

## Why This Module Matters

The CIS Kubernetes Benchmark is the gold standard for cluster security configuration. It's not opinion—it's consensus from security experts worldwide on how Kubernetes should be hardened.

kube-bench automates checking your cluster against these benchmarks. The CKS exam tests your ability to run it, interpret results, and fix failures.

---

## What is CIS?

```
┌─────────────────────────────────────────────────────────────┐
│              CENTER FOR INTERNET SECURITY                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CIS (Center for Internet Security)                        │
│  ├── Non-profit organization                               │
│  ├── Develops security best practices                      │
│  └── Publishes benchmarks for many technologies            │
│                                                             │
│  CIS Kubernetes Benchmark                                  │
│  ├── 200+ security checks                                  │
│  ├── Updated for each Kubernetes version                   │
│  ├── Covers control plane, nodes, policies                 │
│  └── Industry-accepted standard                            │
│                                                             │
│  Why it matters:                                           │
│  ├── Compliance requirements (SOC2, PCI-DSS)              │
│  ├── Objective security measurement                        │
│  ├── Standardized across organizations                     │
│  └── Auditor-friendly documentation                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## kube-bench Overview

kube-bench is an open-source tool that checks Kubernetes clusters against CIS benchmarks.

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-BENCH ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │ kube-bench  │────►│ CIS Checks  │────►│   Results   │  │
│  │   Binary    │     │   (YAML)    │     │             │  │
│  └─────────────┘     └─────────────┘     └─────────────┘  │
│         │                                       │          │
│         ▼                                       ▼          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                 What it checks:                      │  │
│  │  • API server configuration                         │  │
│  │  • Controller manager settings                      │  │
│  │  • Scheduler settings                               │  │
│  │  • etcd configuration                               │  │
│  │  • kubelet configuration                            │  │
│  │  • File permissions                                 │  │
│  │  • Network policies                                 │  │
│  │  • Pod security                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Running kube-bench

### Method 1: As a Kubernetes Job

```bash
# Apply the kube-bench job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Wait for completion
kubectl wait --for=condition=complete job/kube-bench --timeout=120s

# View results
kubectl logs job/kube-bench

# Cleanup
kubectl delete job kube-bench
```

### Method 2: Running Directly on Node

```bash
# Download kube-bench
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.7.0/kube-bench_0.7.0_linux_amd64.tar.gz -o kube-bench.tar.gz
tar -xvf kube-bench.tar.gz

# Run on control plane node
./kube-bench run --targets=master

# Run on worker node
./kube-bench run --targets=node

# Run specific check
./kube-bench run --targets=master --check=1.2.1

# Run with specific benchmark version
./kube-bench run --benchmark=cis-1.8
```

### Method 3: Running in Docker

```bash
# Run against local kubelet
docker run --rm -v /etc:/node/etc:ro \
  -v /var:/node/var:ro \
  aquasec/kube-bench:latest run --targets=node
```

---

## Understanding kube-bench Output

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-BENCH OUTPUT STRUCTURE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [INFO] 1 Control Plane Security Configuration             │
│  [INFO] 1.1 Control Plane Node Configuration Files         │
│                                                             │
│  [PASS] 1.1.1 Ensure API server pod specification file     │
│               permissions are set to 600 or more restrictive│
│                                                             │
│  [FAIL] 1.1.2 Ensure API server pod specification file     │
│               ownership is set to root:root                 │
│                                                             │
│  [WARN] 1.1.3 Ensure controller manager pod specification  │
│               file permissions are set to 600              │
│                                                             │
│  Status Legend:                                             │
│  ─────────────────────────────────────────────────────────  │
│  [PASS] - Check passed, configuration is secure            │
│  [FAIL] - Security issue found, MUST fix                   │
│  [WARN] - Manual verification needed                       │
│  [INFO] - Informational, not a check                       │
│                                                             │
│  Remediation (shown for failures):                         │
│  Run the following command on the control plane:           │
│  chown root:root /etc/kubernetes/manifests/kube-apiserver.yaml│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CIS Benchmark Structure

The benchmark is organized into sections:

```
┌─────────────────────────────────────────────────────────────┐
│              CIS KUBERNETES BENCHMARK SECTIONS              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Control Plane Components                                │
│     1.1 Control Plane Node Configuration Files             │
│     1.2 API Server                                         │
│     1.3 Controller Manager                                 │
│     1.4 Scheduler                                          │
│                                                             │
│  2. etcd                                                   │
│     2.1 etcd Node Configuration                            │
│                                                             │
│  3. Control Plane Configuration                            │
│     3.1 Authentication and Authorization                   │
│     3.2 Logging                                            │
│                                                             │
│  4. Worker Nodes                                           │
│     4.1 Worker Node Configuration Files                    │
│     4.2 Kubelet                                            │
│                                                             │
│  5. Policies                                               │
│     5.1 RBAC and Service Accounts                         │
│     5.2 Pod Security                                       │
│     5.3 Network Policies                                   │
│     5.4 Secrets Management                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Common CIS Failures and Fixes

### Category 1.2: API Server

```yaml
# 1.2.1 - Ensure anonymous authentication is disabled
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --anonymous-auth=false  # Add this

# 1.2.5 - Ensure kubelet certificate authority is set
    - --kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt

# 1.2.6 - Ensure authorization mode is not AlwaysAllow
    - --authorization-mode=Node,RBAC  # Not AlwaysAllow

# 1.2.10 - Ensure admission plugins include EventRateLimit
    - --enable-admission-plugins=NodeRestriction,EventRateLimit

# 1.2.16 - Ensure PodSecurity admission is enabled
    - --enable-admission-plugins=NodeRestriction,PodSecurity

# 1.2.20 - Ensure audit logging is enabled
    - --audit-log-path=/var/log/kubernetes/audit.log
    - --audit-log-maxage=30
    - --audit-log-maxbackup=10
    - --audit-log-maxsize=100
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
```

### Category 1.3: Controller Manager

```yaml
# 1.3.2 - Ensure profiling is disabled
# Edit /etc/kubernetes/manifests/kube-controller-manager.yaml
spec:
  containers:
  - command:
    - kube-controller-manager
    - --profiling=false

# 1.3.6 - Ensure RotateKubeletServerCertificate is true
    - --feature-gates=RotateKubeletServerCertificate=true
```

### Category 4.2: Kubelet

```yaml
# Fix kubelet settings in /var/lib/kubelet/config.yaml

# 4.2.1 - Ensure anonymous authentication is disabled
authentication:
  anonymous:
    enabled: false

# 4.2.2 - Ensure authorization mode is not AlwaysAllow
authorization:
  mode: Webhook

# 4.2.4 - Ensure read-only port is disabled
readOnlyPort: 0

# 4.2.6 - Ensure TLS is configured
tlsCertFile: /var/lib/kubelet/pki/kubelet.crt
tlsPrivateKeyFile: /var/lib/kubelet/pki/kubelet.key

# After changes, restart kubelet
sudo systemctl restart kubelet
```

### File Permission Fixes

```bash
# 1.1.1-1.1.4: Control plane manifest file permissions
chmod 600 /etc/kubernetes/manifests/kube-apiserver.yaml
chmod 600 /etc/kubernetes/manifests/kube-controller-manager.yaml
chmod 600 /etc/kubernetes/manifests/kube-scheduler.yaml
chmod 600 /etc/kubernetes/manifests/etcd.yaml

# 1.1.5-1.1.8: Ensure ownership is root:root
chown root:root /etc/kubernetes/manifests/*.yaml

# 4.1.1-4.1.2: Kubelet config permissions
chmod 600 /var/lib/kubelet/config.yaml
chown root:root /var/lib/kubelet/config.yaml
```

---

## Real Exam Scenarios

### Scenario 1: Fix Specific kube-bench Failures

```bash
# Run kube-bench and filter for failures
./kube-bench run --targets=master 2>&1 | grep -A 5 "\[FAIL\]"

# Example output:
# [FAIL] 1.2.6 Ensure --authorization-mode argument includes Node
# Remediation:
# Edit the API server pod specification file
# /etc/kubernetes/manifests/kube-apiserver.yaml
# and set --authorization-mode=Node,RBAC

# Fix by editing API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --authorization-mode=Node,RBAC

# Wait for API server to restart
kubectl get pods -n kube-system -w
```

### Scenario 2: Generate JSON Report

```bash
# Generate JSON output for parsing
./kube-bench run --json > kube-bench-results.json

# Filter critical failures
cat kube-bench-results.json | jq '.Controls[].tests[].results[] | select(.status=="FAIL")'

# Count failures by section
cat kube-bench-results.json | jq '.Controls[].tests[].results[] | select(.status=="FAIL")' | jq -s 'length'
```

### Scenario 3: Check Specific Section

```bash
# Run only control plane checks
./kube-bench run --targets=master --check=1.2

# Run only kubelet checks
./kube-bench run --targets=node --check=4.2

# Run specific check number
./kube-bench run --check=1.2.6
```

---

## Automating Remediation

### Script to Fix Common Issues

```bash
#!/bin/bash
# cis-remediation.sh - Fix common CIS failures

echo "Fixing file permissions..."
chmod 600 /etc/kubernetes/manifests/*.yaml 2>/dev/null
chmod 600 /var/lib/kubelet/config.yaml 2>/dev/null

echo "Fixing file ownership..."
chown root:root /etc/kubernetes/manifests/*.yaml 2>/dev/null
chown root:root /var/lib/kubelet/config.yaml 2>/dev/null

echo "Checking API server configuration..."
if ! grep -q "anonymous-auth=false" /etc/kubernetes/manifests/kube-apiserver.yaml; then
    echo "WARNING: anonymous-auth not disabled"
fi

if ! grep -q "audit-log-path" /etc/kubernetes/manifests/kube-apiserver.yaml; then
    echo "WARNING: audit logging not configured"
fi

echo "Checking kubelet configuration..."
if grep -q "anonymous:\s*enabled:\s*true" /var/lib/kubelet/config.yaml; then
    echo "WARNING: kubelet anonymous auth enabled"
fi

echo "Done. Re-run kube-bench to verify fixes."
```

---

## CIS Benchmark Levels

```
┌─────────────────────────────────────────────────────────────┐
│              CIS PROFILE LEVELS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 1 - Basic Security                                  │
│  ─────────────────────────────────────────────────────────  │
│  • Can be implemented without major operational impact     │
│  • Foundational security controls                          │
│  • Should be applied to ALL clusters                       │
│  • Examples:                                               │
│    - Disable anonymous auth                                │
│    - Enable RBAC                                           │
│    - Set file permissions                                  │
│                                                             │
│  Level 2 - Enhanced Security                               │
│  ─────────────────────────────────────────────────────────  │
│  • May require more planning to implement                  │
│  • Could impact some workloads                            │
│  • For high-security environments                          │
│  • Examples:                                               │
│    - Enable audit logging                                  │
│    - Restrict API server access                           │
│    - Implement network policies                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **CIS benchmarks are updated regularly.** Each Kubernetes version gets its own benchmark version. kube-bench auto-detects which one to use.

- **kube-bench was created by Aqua Security,** the same company behind Trivy. They're major contributors to Kubernetes security tooling.

- **Not all CIS recommendations apply to managed Kubernetes.** GKE, EKS, and AKS have modified benchmarks because you can't change control plane settings.

- **The benchmark is public and free.** You can download the full CIS Kubernetes Benchmark PDF from cisecurity.org (requires free registration).

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Running kube-bench only once | Security drift happens | Schedule regular scans |
| Ignoring [WARN] items | They may still be issues | Review each warning |
| Fixing without understanding | May break cluster | Read remediation carefully |
| Not restarting after fixes | Changes don't take effect | Restart affected component |
| Skipping file permissions | Easy points on exam | Always check ownership/perms |

---

## Quiz

1. **What does a [FAIL] status in kube-bench output indicate?**
   <details>
   <summary>Answer</summary>
   A security configuration issue that violates the CIS benchmark and should be fixed. kube-bench provides remediation instructions for each failure.
   </details>

2. **Where are API server configuration changes typically made?**
   <details>
   <summary>Answer</summary>
   In `/etc/kubernetes/manifests/kube-apiserver.yaml` for kubeadm clusters. The API server pod will automatically restart when this file changes.
   </details>

3. **What command runs kube-bench against only the control plane?**
   <details>
   <summary>Answer</summary>
   `./kube-bench run --targets=master` - This runs only control plane checks (sections 1.x, 2.x, 3.x).
   </details>

4. **After fixing kubelet configuration, what must you do?**
   <details>
   <summary>Answer</summary>
   Restart the kubelet service with `sudo systemctl restart kubelet` for changes to take effect.
   </details>

---

## Hands-On Exercise

**Task**: Run kube-bench, identify failures, and fix them.

```bash
# Step 1: Run kube-bench as a job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s

# Step 2: Capture all failures
kubectl logs job/kube-bench | grep -E "^\[FAIL\]" > failures.txt
cat failures.txt

# Step 3: Pick one failure and find its remediation
kubectl logs job/kube-bench | grep -A 10 "$(head -1 failures.txt)"

# Step 4: Apply the fix (example: file permissions)
# SSH to control plane node
# sudo chmod 600 /etc/kubernetes/manifests/kube-apiserver.yaml

# Step 5: Re-run kube-bench to verify fix
kubectl delete job kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s
kubectl logs job/kube-bench | grep -E "^\[FAIL\]" | wc -l

# The failure count should decrease

# Cleanup
kubectl delete job kube-bench
```

**Success criteria**: Successfully fix at least one CIS benchmark failure and verify with kube-bench.

---

## Summary

**CIS Benchmarks**:
- Industry standard for Kubernetes security
- 200+ checks across control plane, nodes, policies
- Two levels: basic (Level 1) and enhanced (Level 2)

**kube-bench**:
- Automates CIS benchmark checking
- Run as Job, binary, or container
- Provides remediation for failures

**Common fixes**:
- File permissions (chmod 600)
- Ownership (chown root:root)
- API server flags (edit manifest)
- Kubelet config (restart required)

**Exam tips**:
- Know how to run kube-bench
- Understand output format
- Practice applying common fixes
- Remember to restart after changes

---

## Next Module

[Module 1.3: Ingress Security](../module-1.3-ingress-security/) - Securing ingress controllers and TLS termination.
