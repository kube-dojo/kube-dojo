---
title: "Module 6.2: CIS Benchmarks"
slug: k8s/kcsa/part6-compliance/module-6.2-cis-benchmarks
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Technical knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 6.1: Compliance Frameworks](../module-6.1-compliance-frameworks/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** CIS Benchmark categories and their coverage of control plane, node, and policy security
2. **Assess** benchmark findings to prioritize critical vs. advisory recommendations
3. **Identify** how kube-bench automates CIS compliance checking across cluster components
4. **Explain** the relationship between CIS Benchmarks and broader compliance frameworks

---

## Why This Module Matters

The CIS (Center for Internet Security) Kubernetes Benchmark provides prescriptive security recommendations for Kubernetes clusters. It's the industry standard for Kubernetes hardening and is widely referenced in compliance requirements.

KCSA tests your knowledge of CIS Benchmark categories and key recommendations.

---

## What is CIS Benchmark?

```
┌─────────────────────────────────────────────────────────────┐
│              CIS KUBERNETES BENCHMARK                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Security configuration guidelines for Kubernetes     │
│  BY: Center for Internet Security                          │
│  FORMAT: Prescriptive checks with remediation guidance     │
│                                                             │
│  STRUCTURE:                                                │
│  ├── Control Plane Components                              │
│  ├── etcd                                                  │
│  ├── Control Plane Configuration                          │
│  ├── Worker Nodes                                         │
│  └── Policies                                             │
│                                                             │
│  SCORING:                                                  │
│  ├── Scored - Affects compliance percentage               │
│  └── Not Scored - Recommendations only                    │
│                                                             │
│  PROFILES:                                                 │
│  ├── Level 1 - Basic security (minimal disruption)        │
│  └── Level 2 - Defense in depth (may affect function)     │
│                                                             │
│  VERSIONS:                                                 │
│  • Updated with each Kubernetes release                   │
│  • Managed distributions have specific benchmarks         │
│    (EKS, GKE, AKS, OpenShift)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Benchmark Categories

### 1. Control Plane Components

```
┌─────────────────────────────────────────────────────────────┐
│              CONTROL PLANE SECURITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1.1 CONTROL PLANE NODE CONFIGURATION                      │
│  ├── File permissions on component configs                 │
│  ├── Ownership of configuration files                      │
│  └── Secure directory permissions                          │
│                                                             │
│  1.2 API SERVER                                            │
│  ├── Disable anonymous authentication                      │
│  ├── Enable RBAC authorization                            │
│  ├── Disable insecure port                                │
│  ├── Enable admission controllers                          │
│  ├── Configure audit logging                              │
│  ├── Set appropriate request limits                        │
│  └── Enable encryption providers                           │
│                                                             │
│  1.3 CONTROLLER MANAGER                                    │
│  ├── Enable terminated pod garbage collection             │
│  ├── Use service account credentials                      │
│  └── Rotate service account tokens                         │
│                                                             │
│  1.4 SCHEDULER                                             │
│  ├── Disable profiling                                    │
│  └── Use secure authentication                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: Your organization uses EKS (managed Kubernetes). A colleague runs kube-bench with the default (self-managed) benchmark and gets 30 FAIL findings for control plane components. Are these findings valid? Why or why not?

### 2. etcd

```
┌─────────────────────────────────────────────────────────────┐
│              etcd SECURITY                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  2.1 PEER COMMUNICATION                                    │
│  ├── Use client certificate authentication               │
│  ├── Encrypt peer communication with TLS                 │
│  ├── Verify peer certificates                            │
│  └── Use unique certificates per member                  │
│                                                             │
│  2.2 CLIENT COMMUNICATION                                  │
│  ├── Require client certificates for API server          │
│  ├── Encrypt client communication with TLS               │
│  ├── Verify client certificates                          │
│  └── Restrict client access                              │
│                                                             │
│  2.3 DATA SECURITY                                         │
│  ├── Secure file permissions (700)                       │
│  ├── Proper ownership (etcd:etcd)                        │
│  └── Enable encryption at rest                           │
│                                                             │
│  KEY CHECKS:                                               │
│  • --cert-file and --key-file are set                    │
│  • --peer-cert-file and --peer-key-file are set          │
│  • --client-cert-auth=true                               │
│  • --peer-client-cert-auth=true                          │
│  • --auto-tls=false                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Worker Nodes

```
┌─────────────────────────────────────────────────────────────┐
│              WORKER NODE SECURITY                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  4.1 KUBELET                                               │
│  ├── Disable anonymous authentication                      │
│  ├── Use webhook authorization                            │
│  ├── Enable client certificate authentication             │
│  ├── Disable read-only port (10255)                       │
│  ├── Enable streaming connection timeouts                 │
│  ├── Protect kernel defaults                              │
│  ├── Set hostname override only if needed                 │
│  └── Enable certificate rotation                          │
│                                                             │
│  4.2 KUBELET CONFIG FILE                                   │
│  ├── File permissions (600)                               │
│  ├── Proper ownership (root:root)                         │
│  └── Disable insecure TLS cipher suites                   │
│                                                             │
│  KEY KUBELET SETTINGS:                                     │
│  --anonymous-auth=false                                   │
│  --authorization-mode=Webhook                             │
│  --client-ca-file=/path/to/ca.crt                        │
│  --read-only-port=0                                       │
│  --protect-kernel-defaults=true                           │
│  --rotate-certificates=true                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Policies

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES POLICIES                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  5.1 RBAC AND SERVICE ACCOUNTS                             │
│  ├── Limit use of cluster-admin role                      │
│  ├── Minimize access to secrets                           │
│  ├── Minimize wildcard use in roles                       │
│  ├── Minimize access to pod creation                      │
│  ├── Ensure default SA is not used                        │
│  └── Disable auto-mount of SA tokens                      │
│                                                             │
│  5.2 POD SECURITY STANDARDS                                │
│  ├── Minimize privileged containers                       │
│  ├── Minimize host namespace sharing                      │
│  ├── Minimize running as root                            │
│  ├── Minimize capabilities                                │
│  ├── Do not allow privilege escalation                   │
│  └── Apply Pod Security Standards                        │
│                                                             │
│  5.3 NETWORK POLICIES                                      │
│  ├── Use CNI that supports NetworkPolicy                  │
│  ├── Define default deny policies                         │
│  └── Ensure pods are isolated appropriately              │
│                                                             │
│  5.4 SECRETS MANAGEMENT                                    │
│  ├── Use secrets instead of environment variables         │
│  ├── Enable encryption at rest for secrets               │
│  └── Consider external secrets stores                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key CIS Recommendations

### API Server Hardening

```
┌─────────────────────────────────────────────────────────────┐
│              API SERVER RECOMMENDATIONS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHENTICATION                                            │
│  --anonymous-auth=false                                   │
│  • Disable anonymous access to API                        │
│  • All requests must be authenticated                     │
│                                                             │
│  AUTHORIZATION                                             │
│  --authorization-mode=Node,RBAC                           │
│  • Never use AlwaysAllow                                  │
│  • Use RBAC for role-based access                        │
│  • Node authorization for kubelet                         │
│                                                             │
│  ADMISSION CONTROLLERS                                     │
│  --enable-admission-plugins=NodeRestriction,PodSecurity  │
│  • NodeRestriction - Limit kubelet permissions           │
│  • PodSecurity - Enforce PSS                             │
│  • Other security-relevant controllers                    │
│                                                             │
│  AUDIT LOGGING                                             │
│  --audit-log-path=/var/log/kubernetes/audit.log          │
│  --audit-log-maxage=30                                    │
│  --audit-log-maxbackup=10                                 │
│  --audit-log-maxsize=100                                  │
│  --audit-policy-file=/etc/kubernetes/audit-policy.yaml   │
│                                                             │
│  ENCRYPTION                                                │
│  --encryption-provider-config=/path/to/encryption.yaml   │
│  • Encrypt secrets at rest                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kubelet Hardening

```
┌─────────────────────────────────────────────────────────────┐
│              KUBELET RECOMMENDATIONS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHENTICATION                                            │
│  authentication:                                          │
│    anonymous:                                             │
│      enabled: false                                       │
│    webhook:                                               │
│      enabled: true                                        │
│    x509:                                                  │
│      clientCAFile: /path/to/ca.crt                       │
│                                                             │
│  AUTHORIZATION                                             │
│  authorization:                                           │
│    mode: Webhook                                          │
│  • Use Webhook mode for API server authorization         │
│  • Never use AlwaysAllow                                  │
│                                                             │
│  NETWORK                                                   │
│  readOnlyPort: 0                                          │
│  • Disable unauthenticated read-only port                │
│  • Prevents information disclosure                        │
│                                                             │
│  CERTIFICATES                                              │
│  rotateCertificates: true                                 │
│  serverTLSBootstrap: true                                │
│  • Enable automatic certificate rotation                  │
│  • Ensure certs don't expire unexpectedly                │
│                                                             │
│  SECURITY                                                  │
│  protectKernelDefaults: true                             │
│  • Fail if kernel settings don't match kubelet needs     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Using kube-bench

### Running kube-bench

```bash
# Run on master node
kube-bench run --targets master

# Run on worker node
kube-bench run --targets node

# Run specific checks
kube-bench run --targets master --check 1.2.1,1.2.2

# Output as JSON
kube-bench run --targets master --json

# Run as Kubernetes Job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
```

### Interpreting Results

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-BENCH OUTPUT                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [INFO] 1 Control Plane Security Configuration             │
│  [INFO] 1.1 Control Plane Node Configuration Files         │
│  [PASS] 1.1.1 Ensure that the API server pod spec file     │
│               permissions are set to 600 or more restrictive│
│  [PASS] 1.1.2 Ensure that the API server pod spec file     │
│               ownership is set to root:root                │
│  [FAIL] 1.2.1 Ensure that the --anonymous-auth argument    │
│               is set to false                              │
│                                                             │
│  REMEDIATION:                                              │
│  1.2.1 Edit the API server pod specification file          │
│  /etc/kubernetes/manifests/kube-apiserver.yaml and set:    │
│  --anonymous-auth=false                                    │
│                                                             │
│  == Summary ==                                             │
│  45 checks PASS                                            │
│  10 checks FAIL                                            │
│  5 checks WARN                                             │
│  0 checks INFO                                             │
│                                                             │
│  SCORING:                                                  │
│  PASS = Compliant with recommendation                     │
│  FAIL = Not compliant, needs remediation                  │
│  WARN = Manual check needed                               │
│  INFO = Informational only                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CIS Benchmark for Managed Kubernetes

```
┌─────────────────────────────────────────────────────────────┐
│              MANAGED KUBERNETES BENCHMARKS                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHY DIFFERENT?                                            │
│  • Control plane managed by provider                       │
│  • Different configuration options available               │
│  • Shared responsibility model                             │
│                                                             │
│  EKS BENCHMARK                                             │
│  • AWS-specific recommendations                            │
│  • IAM integration                                         │
│  • EKS add-ons security                                   │
│  • kube-bench supports: --benchmark eks-1.0               │
│                                                             │
│  GKE BENCHMARK                                             │
│  • GCP-specific recommendations                            │
│  • Workload Identity                                       │
│  • Binary Authorization                                    │
│  • kube-bench supports: --benchmark gke-1.0               │
│                                                             │
│  AKS BENCHMARK                                             │
│  • Azure-specific recommendations                          │
│  • Azure AD integration                                    │
│  • Azure Policy                                           │
│  • kube-bench supports: --benchmark aks-1.0               │
│                                                             │
│  RESPONSIBILITY:                                           │
│  Provider: Control plane components                        │
│  Customer: Worker nodes, workloads, policies               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Pause and predict**: kube-bench reports a WARN for "Ensure that the admission control plugin PodSecurityPolicy is set." But PodSecurityPolicy was removed in Kubernetes 1.25. Does this mean the benchmark is wrong, or something else?

## Remediation Prioritization

```
┌─────────────────────────────────────────────────────────────┐
│              REMEDIATION PRIORITY                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CRITICAL (Fix immediately):                               │
│  ├── Anonymous auth enabled on API server                 │
│  ├── Insecure port enabled                                │
│  ├── AlwaysAllow authorization mode                       │
│  ├── No audit logging                                     │
│  └── etcd exposed without auth                            │
│                                                             │
│  HIGH (Fix within days):                                   │
│  ├── Kubelet anonymous auth enabled                       │
│  ├── Read-only kubelet port enabled                       │
│  ├── No encryption at rest for secrets                    │
│  ├── Privileged containers allowed                        │
│  └── Missing network policies                             │
│                                                             │
│  MEDIUM (Fix within weeks):                                │
│  ├── File permissions not restrictive                     │
│  ├── Audit log rotation not configured                    │
│  ├── Service account token auto-mount enabled             │
│  └── Certificate rotation not enabled                     │
│                                                             │
│  LOW (Plan for fix):                                       │
│  ├── Informational findings                               │
│  ├── Defense-in-depth recommendations                     │
│  └── Non-security settings                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Continuous CIS Compliance

```
┌─────────────────────────────────────────────────────────────┐
│              CONTINUOUS CIS COMPLIANCE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SCHEDULED SCANNING                                        │
│  apiVersion: batch/v1                                      │
│  kind: CronJob                                            │
│  metadata:                                                 │
│    name: kube-bench-scan                                  │
│  spec:                                                    │
│    schedule: "0 0 * * *"  # Daily                        │
│    jobTemplate:                                           │
│      spec:                                                │
│        template:                                          │
│          spec:                                            │
│            containers:                                    │
│            - name: kube-bench                            │
│              image: aquasec/kube-bench:latest           │
│              args: ["--json"]                            │
│            restartPolicy: Never                          │
│                                                             │
│  INTEGRATION POINTS:                                       │
│  • CI/CD: Scan before cluster changes                     │
│  • Monitoring: Alert on new failures                      │
│  • Reporting: Track compliance over time                  │
│  • Automation: Auto-remediate where safe                  │
│                                                             │
│  DRIFT DETECTION:                                          │
│  • Compare current state to baseline                      │
│  • Alert on configuration changes                         │
│  • Track remediation progress                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **CIS Benchmarks are consensus-based**—they're developed by security professionals from multiple organizations and represent agreed-upon best practices.

- **Not all checks apply to all environments**. Managed Kubernetes (EKS, GKE, AKS) has different benchmarks because customers don't control the control plane.

- **kube-bench can run as a pod**—you don't need SSH access to nodes to check compliance.

- **Level 2 controls** may affect functionality. For example, restricting syscalls with seccomp might break some applications.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Ignoring manual checks | Missing vulnerabilities | Review WARN items |
| Applying all controls blindly | May break cluster | Test in non-prod first |
| Running once only | Drift over time | Schedule regular scans |
| Not tracking progress | No improvement visibility | Build compliance dashboard |
| Treating all failures equally | Inefficient remediation | Prioritize by risk |

---

## Quiz

1. **Your kube-bench scan on an EKS cluster shows 30 FAIL findings for control plane components (API server flags, etcd configuration). Your colleague starts creating tickets to fix each one. What's wrong with this approach?**
   <details>
   <summary>Answer</summary>
   On EKS, the control plane is managed by AWS — customers cannot configure API server flags, etcd settings, or controller-manager parameters directly. These FAIL findings are false positives from running the self-managed Kubernetes benchmark against a managed cluster. The correct approach: use the EKS-specific benchmark (`kube-bench --benchmark eks-1.0`), which only checks controls that EKS customers are responsible for (worker nodes, workload policies, RBAC configuration). The control plane findings are AWS's responsibility under the shared responsibility model. This is why choosing the correct benchmark profile matters — mismatched benchmarks waste effort and create misleading compliance reports.
   </details>

2. **kube-bench reports 10 FAIL, 5 WARN, and 45 PASS findings. A manager asks for the "pass rate" (45/60 = 75%). Is this a useful metric? What would you report instead?**
   <details>
   <summary>Answer</summary>
   A raw pass rate is misleading because it treats all findings equally — a FAIL on "anonymous auth enabled" (critical risk) counts the same as a FAIL on "file permissions not 600" (low risk). More useful reporting: (1) Categorize FAILs by risk level (Critical: 3, High: 4, Medium: 3) — this shows actual security posture; (2) Track trends over time (were we at 15 FAIL last month? Improvement is happening); (3) Report WARN items separately — they require manual verification and may be passes or fails; (4) Map findings to compliance requirements (these 3 FAILs affect PCI-DSS requirements X, Y, Z); (5) Include remediation timeline for each severity level. Compliance reporting should communicate risk, not just percentages.
   </details>

3. **The CIS Benchmark Level 2 recommends enabling `protectKernelDefaults: true` on the kubelet. After enabling it on a test node, the kubelet fails to start. What happened, and how should you approach Level 2 controls?**
   <details>
   <summary>Answer</summary>
   `protectKernelDefaults: true` makes the kubelet check that kernel parameters match its expected values. If the node OS has different sysctl settings (common with custom AMIs or OS configurations), the kubelet refuses to start because the kernel state doesn't match. This is exactly why Level 2 is described as "may affect functionality." Approach: (1) Always test Level 2 controls in non-production first; (2) For this specific control, identify which kernel parameters differ and align them with kubelet expectations before enabling the flag; (3) Start with Level 1 (basic security, minimal disruption) and progressively add Level 2 controls after testing each one; (4) Document which Level 2 controls are deferred and why — this shows auditors you've evaluated them, not ignored them.
   </details>

4. **kube-bench flags that the PodSecurityPolicy admission plugin is not enabled. But your cluster runs Kubernetes 1.27 where PSP was removed. Should you mark this finding as "accepted risk" or remediated?**
   <details>
   <summary>Answer</summary>
   This is an outdated benchmark check, not a genuine finding. PSP was deprecated in 1.21 and removed in 1.25 — the replacement is Pod Security Admission (PSA). The finding should be marked as "not applicable" with a note that PSA is enabled instead. This happens when the kube-bench version lags behind the Kubernetes version or when using a benchmark version that predates PSP removal. Resolution: (1) Use the latest kube-bench version and benchmark matching your Kubernetes version; (2) If the check persists, document that PSA with the appropriate standard (Baseline/Restricted) replaces PSP; (3) Verify PSA labels are applied to namespaces (`pod-security.kubernetes.io/enforce: restricted`). This is a common situation with evolving benchmarks.
   </details>

5. **You run kube-bench as a daily CronJob. Monday's scan shows 5 FAIL findings. Tuesday's scan shows 8 FAIL — three new ones appeared overnight despite no intentional changes. What could cause findings to appear and disappear between scans?**
   <details>
   <summary>Answer</summary>
   Several causes: (1) Configuration drift — an operator or automation tool modified a kubelet config, API server manifest, or file permission outside of version control; (2) Node scaling — new nodes joined the cluster with different configurations (different AMI, different kubelet settings); (3) Cluster upgrade — a Kubernetes version upgrade changed default settings; (4) kube-bench database update — the tool updated its check definitions, adding new checks; (5) Transient state — a node was being rebuilt during the scan. This is why continuous CIS compliance matters: (a) version-control all node configurations so drift is detectable; (b) use immutable infrastructure (Bottlerocket, Talos) where node configs can't drift; (c) alert on new FAIL findings rather than just running reports; (d) compare scan results between runs to identify exactly what changed.
   </details>

---

## Hands-On Exercise: Benchmark Analysis

**Scenario**: You receive these kube-bench results. Prioritize the findings:

```
[FAIL] 1.2.1 Ensure --anonymous-auth is set to false
[FAIL] 1.2.5 Ensure --authorization-mode includes RBAC
[WARN] 1.2.11 Ensure --enable-admission-plugins includes PodSecurityPolicy
[FAIL] 4.2.1 Ensure --anonymous-auth is set to false (kubelet)
[FAIL] 4.2.2 Ensure --authorization-mode is not set to AlwaysAllow
[PASS] 4.2.6 Ensure --read-only-port is set to 0
[FAIL] 5.1.1 Ensure cluster-admin role is only used where required
[WARN] 5.2.1 Minimize privileged containers
[FAIL] 5.7.1 Create NetworkPolicy for each namespace
```

**Prioritize and create remediation plan:**

<details>
<summary>Remediation Plan</summary>

**CRITICAL - Fix Today:**

1. **1.2.1 - API server anonymous auth**
   ```yaml
   # /etc/kubernetes/manifests/kube-apiserver.yaml
   - --anonymous-auth=false
   ```
   Risk: Unauthenticated API access

2. **1.2.5 - Authorization mode**
   ```yaml
   - --authorization-mode=Node,RBAC
   ```
   Risk: Possible bypass of authorization

3. **4.2.2 - Kubelet authorization AlwaysAllow**
   ```yaml
   # kubelet config
   authorization:
     mode: Webhook
   ```
   Risk: Kubelet accepts any request

**HIGH - Fix Within Days:**

4. **4.2.1 - Kubelet anonymous auth**
   ```yaml
   authentication:
     anonymous:
       enabled: false
   ```
   Risk: Unauthenticated kubelet access

5. **5.1.1 - Cluster-admin usage**
   - Audit current cluster-admin bindings
   - Remove unnecessary bindings
   - Create role-specific roles
   Risk: Excessive privileges

**MEDIUM - Fix Within Weeks:**

6. **5.7.1 - NetworkPolicy per namespace**
   - Create default deny policies
   - Add explicit allow policies
   Risk: Unrestricted pod communication

7. **5.2.1 - Privileged containers** (WARN)
   - Enable Pod Security Standards
   - Audit privileged pods
   - Migrate to non-privileged
   Risk: Container escape possible

**NOTE:**
- 1.2.11 mentions PodSecurityPolicy which is deprecated
- Modern clusters should use Pod Security Admission instead

**Remediation Order:**
1. Authentication issues (immediate)
2. Authorization issues (same day)
3. RBAC cleanup (this week)
4. Network policies (this week)
5. Pod security (ongoing)

</details>

---

## Summary

CIS Benchmark provides Kubernetes security standards:

| Category | Key Areas |
|----------|----------|
| **Control Plane** | API server auth, authorization, admission, audit |
| **etcd** | TLS, authentication, encryption |
| **Worker Nodes** | Kubelet auth, authorization, read-only port |
| **Policies** | RBAC, Pod Security, Network Policies |

Key practices:
- Run kube-bench regularly
- Prioritize findings by risk
- Test remediations before applying
- Track compliance over time
- Use managed-specific benchmarks when applicable

---

## Next Module

[Module 6.3: Security Assessments](../module-6.3-security-assessments/) - Conducting and responding to security assessments.
