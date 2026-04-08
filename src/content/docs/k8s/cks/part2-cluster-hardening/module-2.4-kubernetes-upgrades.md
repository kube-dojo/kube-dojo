---
title: "Module 2.4: Kubernetes Security Upgrades"
slug: k8s/cks/part2-cluster-hardening/module-2.4-kubernetes-upgrades
sidebar:
  order: 4
lab:
  id: cks-2.4-kubernetes-upgrades
  url: https://killercoda.com/kubedojo/scenario/cks-2.4-kubernetes-upgrades
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - CKA refresher with security focus
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: CKA upgrade knowledge, kubeadm experience

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** Kubernetes CVEs to determine upgrade urgency and security impact
2. **Implement** security-focused upgrade procedures using kubeadm
3. **Audit** cluster versions to identify components running with known vulnerabilities
4. **Design** an upgrade strategy that minimizes security exposure windows

---

## Why This Module Matters

In 2018, Tesla's Kubernetes administrative console was left exposed without authentication. But the real danger often lies in what's *inside* the cluster. Consider the devastating cryptojacking attacks where hackers exploited an unpatched vulnerability in an older Kubernetes version to deploy DaemonSets running Monero miners across thousands of nodes. Because the victim clusters were running an unsupported version, the known CVE had never been patched.

Running outdated Kubernetes versions is a massive security risk. Each release patches vulnerabilities—some critical. The CKS exam expects you to evaluate CVEs, verify versions, and execute upgrades without leaving the cluster vulnerable.

This module focuses on the security aspects of upgrades, not just the mechanical process you learned for the CKA.

---

## Security Implications of Versions

```
┌─────────────────────────────────────────────────────────────┐
│              VERSION SECURITY LIFECYCLE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Kubernetes Support Model:                                 │
│  ─────────────────────────────────────────────────────────  │
│  • 3 minor versions supported at any time                  │
│  • Security fixes backported to all 3                      │
│  • Older versions: NO SECURITY PATCHES                     │
│                                                             │
│  Example (if current is 1.35):                             │
│  ├── 1.35 ✓ Supported (security patches)                  │
│  ├── 1.34 ✓ Supported (security patches)                  │
│  ├── 1.33 ✓ Supported (security patches)                  │
│  ├── 1.32 ✗ End of life (no patches!)                     │
│  └── 1.31 ✗ Unsupported (vulnerable!)                     │
│                                                             │
│  Risk of running unsupported versions:                     │
│  ⚠️  Known CVEs remain unpatched                           │
│  ⚠️  No security advisories                                │
│  ⚠️  Compliance violations                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Stop and think**: Your cluster is running Kubernetes 1.32 and the current supported versions are 1.33, 1.34, and 1.35. A critical CVE was just announced affecting all versions up to 1.34.2. Your version is out of the support window. What are your options, and how urgent is this?

## Checking Current Versions

```bash
# Check cluster version
kubectl version

# Check all component versions
kubectl get nodes -o wide

# Check control plane component versions
kubectl get pods -n kube-system -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.containers[0].image}{"\n"}{end}' | grep -E "kube-apiserver|kube-controller|kube-scheduler|etcd"

# Check kubelet versions on nodes
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {.status.nodeInfo.kubeletVersion}{"\n"}{end}'
```

---

## Understanding CVEs

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CVE EXAMPLE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CVE-2024-XXXX: Container Escape via Symlink Attack       │
│                                                             │
│  Severity: HIGH (CVSS 8.8)                                 │
│  Affected: v1.26.0 - v1.27.5                               │
│  Fixed: v1.27.6, v1.28.2, v1.29.0                         │
│                                                             │
│  Impact:                                                   │
│  A malicious container can write to host filesystem        │
│  using a specially crafted symlink                         │
│                                                             │
│  Action:                                                   │
│  Upgrade to fixed version immediately                      │
│                                                             │
│  Where to find CVEs:                                       │
│  • kubernetes.io/security                                  │
│  • github.com/kubernetes/kubernetes/security/advisories   │
│  • cve.mitre.org                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Upgrade Process (Security Review)

### Pre-Upgrade Security Checklist

```bash
# 1. Check current version vulnerabilities
kubectl version --short
# Research CVEs for your version

# 2. Review release notes for security fixes
# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/

# 3. Backup critical components
kubectl get all -A -o yaml > cluster-backup.yaml
ETCDCTL_API=3 etcdctl snapshot save backup.db

# 4. Check deprecation warnings
kubectl api-resources --verbs=list -o name | xargs -n 1 kubectl get --show-labels -A 2>&1 | grep -i deprecated
```

### Kubeadm Upgrade (Quick Review)

```bash
# On control plane
sudo apt update
sudo apt install -y kubeadm=1.35.0-*

# Plan the upgrade
sudo kubeadm upgrade plan

# Apply upgrade
sudo kubeadm upgrade apply v1.35.0

# Upgrade kubelet and kubectl
sudo apt install -y kubelet=1.35.0-* kubectl=1.35.0-*
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

---

## Security-Focused Upgrade Considerations

### 1. API Deprecations

```yaml
# Old API (may be removed in new version)
apiVersion: extensions/v1beta1
kind: Ingress

# New API
apiVersion: networking.k8s.io/v1
kind: Ingress
```

### 2. Admission Controller Changes

```bash
# Check if PodSecurityPolicy is being removed
# (Removed in 1.25, use Pod Security Admission instead)
kubectl get psp 2>&1 | grep -q "the server doesn't have" && echo "PSP already removed"
```

### 3. Feature Gate Changes

```yaml
# Some security features graduate from beta to stable
# Check if feature gates need updating in API server

# Example: PodSecurity feature (stable since 1.25)
- --feature-gates=PodSecurity=true  # May not be needed anymore
```

---

> **Pause and predict**: What would happen if you upgrade the API server to 1.35 first (correct order), but a junior admin accidentally upgrades one worker node's kubelet to 1.35 before upgrading the controller-manager (still on 1.33). Does this violate the version skew policy? What could break?

## Version Skew Policy

```
┌─────────────────────────────────────────────────────────────┐
│              VERSION SKEW RULES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kube-apiserver:                                           │
│  └── Must be newest component in cluster                   │
│                                                             │
│  kube-controller-manager, kube-scheduler:                  │
│  └── Same or one minor version older than API server       │
│                                                             │
│  kubelet:                                                  │
│  └── Same, one, or two minor versions older               │
│  └── Never newer than API server                           │
│                                                             │
│  kubectl:                                                  │
│  └── One minor version newer or older                      │
│                                                             │
│  Why this matters for security:                            │
│  • Inconsistent versions can have unexpected behavior      │
│  • Security fixes may not work with version mismatches    │
│  • Upgrade API server first, then other components        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Checking for Security Updates

```bash
# Check Kubernetes security announcements
# https://kubernetes.io/docs/reference/issues-security/security/

# Check specific component for CVEs
trivy image registry.k8s.io/kube-apiserver:v1.30.0

# Check node OS for security updates
apt list --upgradable 2>/dev/null | grep -i security

# Use kube-bench to verify security settings after upgrade
./kube-bench run --targets=master
```

---

## Upgrade Rollback

### When to Rollback

```
┌─────────────────────────────────────────────────────────────┐
│              ROLLBACK TRIGGERS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Rollback if upgrade causes:                               │
│  ─────────────────────────────────────────────────────────  │
│  • API server not starting                                 │
│  • Authentication failures                                 │
│  • RBAC not working                                        │
│  • Networking issues (CNI incompatibility)                 │
│  • Admission controller rejecting valid workloads          │
│                                                             │
│  DO NOT rollback for:                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Deprecated API warnings (fix your manifests)            │
│  • Feature changes (adapt your workflows)                  │
│  • Known issues with workarounds                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Rollback Commands

```bash
# Check previous kubelet version
journalctl -u kubelet | grep "Kubelet version" | head -1

# Downgrade kubelet (if needed)
sudo apt install kubelet=<previous-version>
sudo systemctl restart kubelet

# Note: kubeadm doesn't support direct downgrade
# For control plane, restore from etcd backup
```

---

## Real Exam Scenarios

### Scenario 1: Verify Upgrade Readiness

```bash
# Check current versions match
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {.status.nodeInfo.kubeletVersion}{"\n"}{end}'

# All should show same version
# Inconsistent versions = security risk

# Check for deprecated APIs in use
kubectl get --raw /metrics | grep apiserver_requested_deprecated
```

### Scenario 2: Post-Upgrade Security Verification

```bash
# After upgrade, verify security settings
# 1. Check API server is running
kubectl get pods -n kube-system | grep apiserver

# 2. Verify RBAC is working
kubectl auth can-i create pods --as=developer

# 3. Check admission controllers
kubectl get pods -n kube-system -o yaml | grep admission

# 4. Run kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench
```

### Scenario 3: Find Version with CVE Fix

```bash
# Question: "Upgrade cluster to version that fixes CVE-2024-XXXX"

# 1. Research CVE (exam may provide info)
# 2. Find fixed version
kubectl version --short

# 3. Plan upgrade
kubeadm upgrade plan | grep -E "v1\.[0-9]+\.[0-9]+"

# 4. Execute upgrade to fixed version
```

---

> **Pause and predict**: After upgrading from 1.34 to 1.35, you run `kube-bench` and see 3 new [FAIL] results that weren't there before the upgrade. You didn't change any configuration. How is that possible?

## Managed Kubernetes Upgrades

```
┌─────────────────────────────────────────────────────────────┐
│              MANAGED K8S UPGRADE CONSIDERATIONS             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EKS (AWS):                                                │
│  • Control plane upgraded separately from nodes            │
│  • Managed node groups can auto-upgrade                    │
│  • eksctl upgrade cluster                                  │
│                                                             │
│  GKE (GCP):                                                │
│  • Release channels for automatic upgrades                 │
│  • Maintenance windows for planned upgrades                │
│  • gcloud container clusters upgrade                       │
│                                                             │
│  AKS (Azure):                                              │
│  • Auto-upgrade channel available                          │
│  • Node image upgrades separate                            │
│  • az aks upgrade                                          │
│                                                             │
│  Security note:                                            │
│  Managed K8s often behind latest version (for stability)   │
│  Check provider's security patch timeline                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Kubernetes has quarterly releases** (every ~4 months). Each release gets about 14 months of patch support.

- **CVE severity doesn't always mean exploitability.** Some "critical" CVEs require very specific conditions. Read the full advisory.

- **The Kubernetes Security Response Committee** handles vulnerability reports. They coordinate fixes across supported versions.

- **Auto-upgrading production clusters is risky.** Many organizations run one version behind latest to benefit from community bug discovery.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Skipping versions | May break components | Upgrade one minor at a time |
| Upgrading workers before control plane | Version skew violation | Control plane first |
| Not checking deprecations | Workloads may break | Review release notes |
| No backup before upgrade | Can't rollback | Always backup etcd |
| Running unsupported versions | No security patches | Keep within support window |

---

## Quiz

1. **Your security team receives a CVE advisory for a container escape vulnerability affecting Kubernetes 1.33 through 1.34.3. Your production cluster runs 1.34.1. The fix is in 1.34.4 and 1.35.0. You have a change freeze for the next two weeks. What do you recommend, and what interim mitigations could you apply?**
   <details>
   <summary>Answer</summary>
   A container escape CVE is critical -- it could allow an attacker to break out of a container and access the host node. Recommend an emergency patch to 1.34.4 (patch version upgrade, minimal risk) even during the change freeze. If the freeze is absolutely unbreakable, apply interim mitigations: restrict pod security with Pod Security Admission in `enforce` mode using the `restricted` profile, ensure AppArmor/seccomp profiles are applied to all workloads, disable privileged containers, and increase monitoring with Falco rules targeting container escapes. But these are stopgaps -- the upgrade should happen as soon as possible because known CVEs get actively exploited.
   </details>

2. **After upgrading your cluster from 1.34 to 1.35, you run `kubectl get nodes` and notice worker node `node-2` shows version 1.33 -- it was missed during the upgrade. The API server is 1.35. Is this a security problem even though the cluster "works"?**
   <details>
   <summary>Answer</summary>
   Yes, this is a security problem on multiple levels. First, the kubelet version skew policy allows kubelets up to 2 minor versions older than the API server, so 1.33 is technically within skew for a 1.35 API server -- but just barely. However, 1.33 won't receive security patches much longer (only 3 versions are supported), and any security fixes in 1.34 and 1.35 are not applied to that node. Second, the node may lack security features introduced in newer versions. Third, inconsistent versions make security auditing unreliable -- kube-bench results differ per node. Upgrade node-2 immediately to 1.35 to maintain a consistent security posture.
   </details>

3. **You run `kubeadm upgrade plan` and it shows an available upgrade to 1.35.0. A colleague says "just run `kubeadm upgrade apply` and we're done." What security-critical steps are they skipping before and after the upgrade?**
   <details>
   <summary>Answer</summary>
   Running `kubeadm upgrade apply` without preparation is extremely risky because it ignores the necessary security validations and backup procedures. Before the upgrade, they skipped backing up etcd (`etcdctl snapshot save`), which is critical because if the upgrade corrupts the datastore, you cannot roll back securely. They also failed to review release notes for deprecated APIs or removed security features (like PodSecurityPolicy), which could cause workloads to fail upon restart. After the upgrade, they are missing critical validation steps: they must upgrade the kubelets on the nodes, run `kube-bench` to ensure the new control plane components are configured securely, and verify that RBAC and admission controllers are still actively restricting access. Failing to perform these steps leaves the cluster in an unknown, potentially vulnerable state where security policies might silently fail.
   </details>

4. **Your organization runs three clusters: dev (1.33), staging (1.34), and production (1.34). Kubernetes 1.36 is released, making 1.33 unsupported. The dev team says "it's just dev, we don't need to upgrade." Why is this thinking dangerous from a security perspective?**
   <details>
   <summary>Answer</summary>
   Running an unsupported version in a development environment is highly dangerous because attackers often use less-secure environments as a stepping stone into production. Development clusters frequently have access to shared resources like container registries, CI/CD pipelines, or cloud credentials. If an unpatched CVE allows an attacker to compromise the dev cluster, they can pivot to steal those credentials or inject malicious code into the development pipeline. Furthermore, compliance frameworks typically require all environments connected to the corporate network to be actively patched, meaning an unsupported dev cluster is a direct compliance violation. You should establish a cadence where the dev cluster is upgraded first to test the process, followed shortly by staging and production.
   </details>

---

## Hands-On Exercise

**Task**: Practice pre-upgrade security assessment and post-upgrade verification.

First, create an isolated namespace for our testing. This ensures we don't interfere with existing workloads while we simulate an upgrade scenario.

```bash
kubectl create namespace upgrade-test
```

Next, deploy a test workload configured with strict security contexts. We will use this pod to verify that security settings (like `runAsNonRoot` and `readOnlyRootFilesystem`) remain intact and are enforced after an upgrade.

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: security-test
  namespace: upgrade-test
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
EOF
```

Before initiating any upgrade, you must capture the current state of your critical workloads. If an upgrade fails, this backup is your lifeline.

```bash
echo "=== Pre-Upgrade State Capture ==="
kubectl get all -n upgrade-test -o yaml > /tmp/pre-upgrade-backup.yaml
echo "Backup saved to /tmp/pre-upgrade-backup.yaml"
```

Audit the current versions of your cluster components. You need to know exactly what versions are running to determine if they are vulnerable to known CVEs and to plan the upgrade path.

```bash
echo "=== Current Versions ==="
kubectl version --short 2>/dev/null || kubectl version

echo "=== Node Versions ==="
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {.status.nodeInfo.kubeletVersion}{"\n"}{end}'
```

Deprecated APIs are a major source of failed upgrades. Check your manifests and running resources to ensure none are using APIs that will be removed in the target version.

```bash
echo "=== Checking Deprecated APIs ==="
# Look for deprecated API versions in our resources
kubectl get pod security-test -n upgrade-test -o yaml | grep "apiVersion"
```

> **Stop and think**: If you find a deprecated API in use, do you fix it before or after the upgrade?

After the upgrade (simulated here), verify that Role-Based Access Control (RBAC) is still functioning correctly. An upgrade should never silently escalate or drop permissions.

```bash
echo "=== RBAC Verification ==="
kubectl auth can-i list pods -n upgrade-test --as=system:serviceaccount:upgrade-test:default
```

Confirm that the security contexts applied to your workloads are still present and actively enforced by the new API server version.

```bash
echo "=== Security Context Verification ==="
kubectl get pod security-test -n upgrade-test -o jsonpath='{.spec.securityContext}' && echo ""
kubectl get pod security-test -n upgrade-test -o jsonpath='{.spec.containers[0].securityContext}' && echo ""
```

Ensure the pod remains in a running state and hasn't been blocked by any new admission controllers.

```bash
echo "=== Pod Status ==="
kubectl get pod security-test -n upgrade-test
```

In a real scenario, you would run a security benchmarking tool like `kube-bench` against your nodes to ensure the new components are configured securely.

```bash
echo "=== Security Benchmark Check ==="
echo "On control plane, would run: ./kube-bench run --targets=master"
echo "On worker nodes, would run: ./kube-bench run --targets=node"
```

Verify that NetworkPolicies are still supported and active. Some CNI plugins require specific updates to remain compatible with new Kubernetes versions.

```bash
echo "=== Testing NetworkPolicy Support ==="
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-policy
  namespace: upgrade-test
spec:
  podSelector:
    matchLabels:
      app: security-test
  policyTypes:
  - Ingress
  - Egress
EOF

kubectl get networkpolicy -n upgrade-test
```

Finally, clean up the testing environment.

```bash
echo "=== Cleanup ==="
kubectl delete namespace upgrade-test
rm -f /tmp/pre-upgrade-backup.yaml

echo ""
echo "=== Exercise Complete ==="
echo "Key upgrade security checks performed:"
echo "1. ✓ Backed up cluster state"
echo "2. ✓ Checked versions for consistency"
echo "3. ✓ Verified no deprecated APIs in use"
echo "4. ✓ Confirmed RBAC working"
echo "5. ✓ Validated security contexts"
echo "6. ✓ Verified NetworkPolicy support"
```

**Success criteria**: Successfully perform pre-upgrade backup, version audit, and post-upgrade security verification checklist.

---

## Summary

**Version Security**:
- Only 3 minor versions receive patches
- Unsupported = vulnerable
- Upgrade regularly

**Upgrade Order**:
1. Control plane (API server first)
2. Controllers and scheduler
3. Worker node kubelets

**Security Checks Post-Upgrade**:
- API server running
- RBAC working
- Admission controllers active
- Run kube-bench

**Exam Tips**:
- Know how to check versions
- Understand version skew policy
- Be aware of deprecation impacts

---

## Next Module

[Module 2.5: Restricting API Access](../module-2.5-restricting-api-access/) - Network and authentication restrictions for the API server.