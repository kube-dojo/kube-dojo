---
title: "Module 0.3: Security Tool Mastery"
slug: k8s/cks/part0-environment/module-0.3-security-tools
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Essential exam tools
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 0.2 (Security Lab Setup)

---

## Why This Module Matters

Three tools dominate CKS: **Trivy**, **Falco**, and **kube-bench**. The exam expects you to use them fluently—not just run basic commands, but interpret output, modify configurations, and troubleshoot issues.

This module builds that fluency.

---

## Trivy: Image Vulnerability Scanning

### Basic Scanning

```bash
# Scan an image
trivy image nginx:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL nginx:latest

# Output as JSON (for automation)
trivy image -f json nginx:latest > scan-results.json

# Scan and fail if vulnerabilities found
trivy image --exit-code 1 --severity CRITICAL nginx:latest
```

### Understanding Trivy Output

```
┌─────────────────────────────────────────────────────────────┐
│              TRIVY SCAN OUTPUT EXPLAINED                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  nginx:latest (debian 12.4)                                │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  Total: 142 (UNKNOWN: 0, LOW: 89, MEDIUM: 42,              │
│              HIGH: 10, CRITICAL: 1)                        │
│                                                             │
│  ┌────────────┬──────────┬──────────┬─────────────────┐    │
│  │ Library    │ Vuln ID  │ Severity │ Fixed Version   │    │
│  ├────────────┼──────────┼──────────┼─────────────────┤    │
│  │ openssl    │ CVE-2024-│ CRITICAL │ 3.0.13-1        │    │
│  │            │ XXXX     │          │                 │    │
│  │ libcurl    │ CVE-2024-│ HIGH     │ 7.88.1-10+d12u6│    │
│  │            │ YYYY     │          │                 │    │
│  └────────────┴──────────┴──────────┴─────────────────┘    │
│                                                             │
│  Key columns:                                              │
│  - Library: Affected package                               │
│  - Vuln ID: CVE identifier (searchable)                   │
│  - Severity: CRITICAL > HIGH > MEDIUM > LOW               │
│  - Fixed Version: Update to this version to fix           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Scan Types

```bash
# Image scan (most common for CKS)
trivy image nginx:1.25

# Filesystem scan (scan local directory)
trivy fs /path/to/project

# Config scan (find misconfigurations in K8s YAML)
trivy config ./manifests/

# Kubernetes scan (scan running cluster)
trivy k8s --report summary cluster
```

### Practical Exam Scenarios

```bash
# Scenario 1: Find images with CRITICAL vulnerabilities
trivy image --severity CRITICAL myregistry/myapp:v1.0

# Scenario 2: Scan all images in a namespace
for img in $(kubectl get pods -n production -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u); do
  echo "Scanning: $img"
  trivy image --severity HIGH,CRITICAL "$img"
done

# Scenario 3: CI/CD gate - fail build if vulnerabilities
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:latest

# Scenario 4: Generate report for compliance
trivy image -f json -o report.json nginx:latest
```

---

## Falco: Runtime Threat Detection

### How Falco Works

```
┌─────────────────────────────────────────────────────────────┐
│              FALCO ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │   System Calls  │ ← Every syscall goes through kernel   │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  eBPF/Kernel    │ ← Falco driver captures events        │
│  │     Driver      │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  Falco Engine   │ ← Matches events against rules        │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  Rules File     │ ← YAML rules define what's suspicious │
│  │  /etc/falco/    │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  Alert Output   │ ← stdout, file, Slack, etc.          │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Viewing Falco Alerts

```bash
# Check Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco -f

# Example alert:
# 14:23:45.123456789: Warning Shell spawned in container
#   (user=root container_id=abc123 container_name=nginx
#   shell=bash parent=entrypoint.sh cmdline=bash)
```

### Understanding Falco Rules

```yaml
# Falco rule structure
- rule: Terminal shell in container
  desc: A shell was spawned in a container
  condition: >
    spawned_process and
    container and
    shell_procs
  output: >
    Shell spawned in container
    (user=%user.name container=%container.name shell=%proc.name)
  priority: WARNING
  tags: [container, shell, mitre_execution]

# Key components:
# - rule: Name of the rule
# - desc: Human-readable description
# - condition: When to trigger (Falco filter syntax)
# - output: What to log when triggered
# - priority: EMERGENCY, ALERT, CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG
# - tags: Categories for filtering
```

### Common Falco Conditions

```yaml
# Detect shell in container
condition: spawned_process and container and shell_procs

# Detect sensitive file access
condition: >
  open_read and
  container and
  (fd.name startswith /etc/shadow or fd.name startswith /etc/passwd)

# Detect network connection
condition: >
  (evt.type in (connect, accept)) and
  container and
  fd.net != ""

# Detect privilege escalation
condition: >
  spawned_process and
  container and
  proc.name = sudo
```

### Modifying Falco Rules

```bash
# Falco rules are in /etc/falco/
# - falco_rules.yaml: Default rules (don't edit)
# - falco_rules.local.yaml: Your custom rules

# Method 1: Helm values (RECOMMENDED — persists across restarts)
# Create a values file with custom rules
cat <<EOF > falco-custom-rules.yaml
customRules:
  custom-rules.yaml: |-
    - rule: Detect cat of sensitive files
      desc: Someone is reading sensitive files
      condition: >
        spawned_process and
        container and
        proc.name = cat and
        (proc.args contains "/etc/shadow" or proc.args contains "/etc/passwd")
      output: "Sensitive file read (user=%user.name file=%proc.args container=%container.name)"
      priority: WARNING
EOF

# Upgrade Falco with custom rules
helm upgrade falco falcosecurity/falco \
  --namespace falco \
  --reuse-values \
  -f falco-custom-rules.yaml

# Method 2: ConfigMap (alternative — also persists)
kubectl create configmap falco-custom-rules \
  --namespace falco \
  --from-literal=custom-rules.yaml='
- rule: Detect cat of sensitive files
  desc: Someone is reading sensitive files
  condition: >
    spawned_process and
    container and
    proc.name = cat and
    (proc.args contains "/etc/shadow" or proc.args contains "/etc/passwd")
  output: "Sensitive file read (user=%user.name file=%proc.args container=%container.name)"
  priority: WARNING
'

# Then reference the ConfigMap in Helm values or mount it manually
# Restart Falco pods to pick up changes
kubectl rollout restart daemonset/falco -n falco
```

> **Important**: Never modify rules by exec-ing into Falco pods — those changes are lost when pods restart. Always use Helm values or ConfigMaps so custom rules survive upgrades and restarts.

### Testing Falco Detection

```bash
# Trigger shell detection
kubectl run test --image=nginx --restart=Never
kubectl exec -it test -- /bin/bash

# Check Falco logs for alert
kubectl logs -n falco -l app.kubernetes.io/name=falco | grep "shell"

# Cleanup
kubectl delete pod test
```

---

## kube-bench: CIS Benchmark Auditing

### Running kube-bench

```bash
# Run as Kubernetes Job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench

# Run specific checks
./kube-bench run --targets=master  # Control plane only
./kube-bench run --targets=node    # Worker nodes only
./kube-bench run --targets=etcd    # etcd only

# Run specific benchmark
./kube-bench run --benchmark cis-1.8  # CIS 1.8 benchmark
```

### Understanding kube-bench Output

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-BENCH OUTPUT EXPLAINED                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [INFO] 1 Control Plane Security Configuration             │
│  [INFO] 1.1 Control Plane Node Configuration Files         │
│                                                             │
│  [PASS] 1.1.1 Ensure API server pod file permissions       │
│  [PASS] 1.1.2 Ensure API server pod file ownership         │
│  [FAIL] 1.1.3 Ensure controller manager file permissions   │
│  [WARN] 1.1.4 Ensure scheduler pod file permissions        │
│                                                             │
│  Status meanings:                                           │
│  [PASS] - Check passed                                     │
│  [FAIL] - Security issue found, must fix                   │
│  [WARN] - Manual review needed                             │
│  [INFO] - Informational only                               │
│                                                             │
│  Remediation for 1.1.3:                                    │
│  Run: chmod 600 /etc/kubernetes/manifests/controller.yaml  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Common CIS Failures and Fixes

| Check | Issue | Remediation |
|-------|-------|-------------|
| 1.2.1 | Anonymous auth enabled | `--anonymous-auth=false` on API server |
| 1.2.6 | No audit logging | Configure audit policy and log path |
| 1.2.16 | No admission plugins | Enable PodSecurity admission |
| 4.2.1 | kubelet anonymous auth | `--anonymous-auth=false` on kubelet |
| 4.2.6 | TLS not enforced | Configure kubelet TLS certs |

```bash
# Fix API server anonymous auth
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --anonymous-auth=false

# Fix kubelet anonymous auth
# Edit /var/lib/kubelet/config.yaml
# Set: authentication.anonymous.enabled: false

# Restart kubelet after config changes
sudo systemctl restart kubelet
```

---

## kubesec: Static Manifest Analysis

### Scanning Manifests

```bash
# Scan a YAML file
kubesec scan deployment.yaml

# Scan from stdin
cat pod.yaml | kubesec scan /dev/stdin

# Example output:
# [
#   {
#     "score": -30,
#     "scoring": {
#       "passed": [...],
#       "critical": ["containers[] .securityContext .privileged == true"],
#       "advise": [...]
#     }
#   }
# ]
```

### Understanding kubesec Scores

```
┌─────────────────────────────────────────────────────────────┐
│              KUBESEC SCORING                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Score ranges:                                             │
│  ─────────────────────────────────────────────────────────  │
│  10+   : Good security posture                             │
│  0-10  : Acceptable, room for improvement                   │
│  < 0   : Security concerns, review required                 │
│  -30   : Critical issues (e.g., privileged container)       │
│                                                             │
│  Score modifiers:                                          │
│  +1 : runAsNonRoot: true                                   │
│  +1 : readOnlyRootFilesystem: true                         │
│  +1 : resources.limits defined                             │
│  -30: privileged: true (critical)                          │
│  -1 : no securityContext                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Trivy was created by Aqua Security** and is now the most popular open-source vulnerability scanner. It's faster than Clair and more user-friendly.

- **Falco processes millions of events per second** using eBPF for near-zero overhead. It was originally created by Sysdig.

- **CIS Benchmarks** are developed by the Center for Internet Security with input from security experts worldwide. They're the de facto standard for Kubernetes security auditing.

- **kubesec was created by Control Plane** (the same team behind the CNCF-certified Kubernetes security training).

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Only memorizing commands | Need to interpret output | Practice analyzing results |
| Ignoring "MEDIUM" severity | They add up to risk | Review all findings |
| Not customizing Falco rules | Default rules may miss threats | Add environment-specific rules |
| Skipping remediation practice | Exam asks you to FIX issues | Practice applying fixes |
| Running tools once | Need muscle memory | Integrate into daily practice |

---

## Quiz

1. **What Trivy flag makes the scan fail if CRITICAL vulnerabilities are found?**
   <details>
   <summary>Answer</summary>
   `--exit-code 1 --severity CRITICAL`. The exit-code flag controls whether Trivy returns non-zero on findings.
   </details>

2. **Where are custom Falco rules typically placed?**
   <details>
   <summary>Answer</summary>
   `/etc/falco/falco_rules.local.yaml`. The default rules in `falco_rules.yaml` should not be edited directly.
   </details>

3. **What does a [FAIL] status in kube-bench output indicate?**
   <details>
   <summary>Answer</summary>
   A security configuration issue that should be fixed. kube-bench provides remediation instructions for each failed check.
   </details>

4. **What does a negative kubesec score indicate?**
   <details>
   <summary>Answer</summary>
   Security concerns that require review. Critical issues like `privileged: true` can result in scores of -30 or lower.
   </details>

---

## Hands-On Exercise

**Task**: Use all four security tools.

```bash
# 1. Scan an image with Trivy
echo "=== Trivy Scan ==="
trivy image --severity HIGH,CRITICAL nginx:1.25

# 2. Check Falco is detecting events
echo "=== Falco Test ==="
kubectl run falco-test --image=nginx --restart=Never
kubectl exec falco-test -- cat /etc/passwd
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=5
kubectl delete pod falco-test

# 3. Run kube-bench
echo "=== kube-bench ==="
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s
kubectl logs job/kube-bench | grep -E "^\[FAIL\]" | head -10
kubectl delete job kube-bench

# 4. Scan a manifest with kubesec
echo "=== kubesec Scan ==="
cat <<EOF | kubesec scan /dev/stdin
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
EOF
```

**Success criteria**: Run all tools, interpret output, identify security issues.

---

## Summary

**Trivy** (Image Scanning):
- `trivy image <image>` - Basic scan
- `--severity HIGH,CRITICAL` - Filter by severity
- `--exit-code 1` - Fail on findings

**Falco** (Runtime Detection):
- Monitors system calls in real-time
- Rules define suspicious behavior
- Custom rules in `falco_rules.local.yaml`

**kube-bench** (CIS Benchmarks):
- Audits cluster against CIS standards
- [FAIL] = fix required
- Provides remediation steps

**kubesec** (Static Analysis):
- Scores YAML manifests
- Negative score = security concerns
- Quick pre-deployment check

---

## Next Module

[Module 0.4: CKS Exam Strategy](../module-0.4-exam-strategy/) - Security-focused exam approach.
