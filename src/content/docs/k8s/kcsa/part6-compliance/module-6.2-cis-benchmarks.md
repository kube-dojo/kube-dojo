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

1. **What is the CIS Kubernetes Benchmark?**
   <details>
   <summary>Answer</summary>
   A prescriptive security configuration guideline for Kubernetes developed by the Center for Internet Security. It provides specific recommendations for hardening Kubernetes clusters across control plane components, etcd, worker nodes, and policies.
   </details>

2. **What's the difference between Level 1 and Level 2 benchmarks?**
   <details>
   <summary>Answer</summary>
   Level 1 provides basic security with minimal impact on system operation or functionality. Level 2 provides defense-in-depth with potentially more restrictive settings that may affect functionality. Level 1 is the minimum bar; Level 2 is for more secure environments.
   </details>

3. **Why should you disable anonymous authentication on the API server?**
   <details>
   <summary>Answer</summary>
   Anonymous authentication allows unauthenticated requests to the API server. Even with authorization in place, it increases attack surface and may leak information through unauthenticated endpoints. Disabling it ensures all API requests must be authenticated.
   </details>

4. **Why does managed Kubernetes have different benchmarks?**
   <details>
   <summary>Answer</summary>
   In managed Kubernetes (EKS, GKE, AKS), the cloud provider manages the control plane. Customers can't configure many API server, etcd, or controller-manager settings. The managed benchmarks focus on what customers can control: worker nodes, workloads, and policies.
   </details>

5. **How does kube-bench help with compliance?**
   <details>
   <summary>Answer</summary>
   kube-bench automates CIS Benchmark checks. It scans cluster components against benchmark recommendations, reports PASS/FAIL/WARN status, and provides remediation guidance. It can run on nodes or as a pod, supports different Kubernetes versions and managed platforms, and outputs reports for compliance documentation.
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
