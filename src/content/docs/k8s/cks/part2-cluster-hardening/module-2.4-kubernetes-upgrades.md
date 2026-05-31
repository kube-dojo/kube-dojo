---
revision_pending: false
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

1. **Evaluate** Kubernetes CVE advisories and release support windows to choose a secure upgrade target.
2. **Audit** cluster, node, control-plane, and workload evidence before approving a Kubernetes upgrade.
3. **Implement** a kubeadm upgrade workflow that preserves backups, version skew, and security controls.
4. **Diagnose** post-upgrade RBAC, admission, policy, and benchmark failures before returning traffic to normal.
5. **Design** managed and self-managed upgrade strategies that minimize security exposure windows.

---

## Why This Module Matters

Hypothetical scenario: a vulnerability advisory lands on a Monday morning, and it says the fix is available only in newer Kubernetes patch releases than the one your production cluster is running. The cluster still schedules pods, the dashboards are green, and the business would prefer to wait for the next monthly maintenance window. From a security perspective, that calm surface is misleading, because the advisory has converted an unknown weakness into a documented upgrade requirement that attackers, auditors, and defenders can all read.

The CKS exam treats upgrades as security work rather than housekeeping. You are expected to know how to read the relationship between supported releases, CVE fixes, component versions, version skew, backups, admission behavior, and post-upgrade validation. The mechanical kubeadm commands matter, but they are only one part of the decision: a secure upgrade also proves that the chosen version contains the fix, that every component can legally run with its peers, and that workloads still face the same or stronger security controls after the change.

This module rewrites the CKA upgrade reflex into a CKS upgrade discipline. You will start by evaluating whether a version is still inside the supported patch window, then gather version and configuration evidence, then apply a kubeadm-driven upgrade plan with security checks on both sides of the maintenance. By the end, you should be able to explain not only which command to run, but also why that command belongs at that moment in the security response.

## Security Implications of Versions

Kubernetes security upgrades begin with the release support model because the support model tells you whether a patch can exist for your current minor version. The upstream project supports a rolling set of recent minor releases, and security fixes are backported only inside that supported window. For the 1.35 target used in this curriculum, the working example is 1.33, 1.34, and 1.35 as supported minors; 1.32 and older are outside the example window and should be treated as unsupported for security planning.

```text
+-------------------------------------------------------------+
|              VERSION SECURITY LIFECYCLE                     |
+-------------------------------------------------------------+
|                                                             |
|  Kubernetes Support Model:                                  |
|  ---------------------------------------------------------  |
|  - 3 minor versions supported at any time                   |
|  - Security fixes backported to all supported minors        |
|  - Older versions receive no new security patches           |
|                                                             |
|  Example when the target release is 1.35:                   |
|  +-- 1.35 Supported, receives security patches              |
|  +-- 1.34 Supported, receives security patches              |
|  +-- 1.33 Supported, receives security patches              |
|  +-- 1.32 End of life, no new patches                       |
|  +-- 1.31 Unsupported, known issues remain                  |
|                                                             |
|  Risk of running unsupported versions:                      |
|  - Known CVEs remain unpatched                              |
|  - Security advisories may not provide a fixed build        |
|  - Compliance evidence becomes difficult to defend          |
|                                                             |
+-------------------------------------------------------------+
```

The important detail is that "working" and "supported" are different states. A 1.32 cluster can continue accepting API requests even when the project has stopped shipping patched 1.32 binaries, just as an expired passport can still look like a passport in your drawer. The operational risk is not that the cluster stops immediately; the risk is that a disclosed vulnerability can remain permanently present unless you cross a minor-version boundary.

Pause and predict: your cluster is running Kubernetes 1.32, and the supported example window is 1.33, 1.34, and 1.35. A critical CVE is announced that affects releases up to 1.34.2, and your current version is outside the supported window. What options remain available, and which one reduces the exposure window fastest without pretending an unsupported patch will arrive?

Version auditing should collect more than the single server version shown by a default `kubectl version` call. The API server, controller-manager, scheduler, kubelets, static pod images, etcd image, and client tooling can move at different times during an upgrade. When you investigate a security advisory, you need enough evidence to prove which component is affected and whether any node or control-plane pod was missed during the last maintenance.

The inventory should also include how the cluster is built, because the same Kubernetes version number can hide very different operational responsibilities. A kubeadm cluster puts etcd, static pod manifests, host packages, kubelet configuration, and node operating-system updates under your direct control. A managed cluster moves the hosted API server into the provider's hands, but node images, add-ons, admission webhooks, workload manifests, and namespace policies can still remain your responsibility.

For security planning, treat version data as scoped evidence rather than a single pass or fail. If the API server is fixed but a worker node still runs an affected kubelet, workloads scheduled there may remain exposed to the node-side issue. If every kubelet is patched but the CNI or admission webhook is incompatible with the new API behavior, the cluster can become less reliable exactly when you need a clean response. Good upgrade work keeps those scopes visible.

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

A mature audit also distinguishes cluster facts from package-manager facts. `kubectl get nodes` tells you which kubelet version each node reports to the API server, but it does not prove that the host package repository has no newer security patch waiting. Static pod images reveal what the control plane is actually running, but they do not replace release notes, package changelogs, or provider advisories. Treat the cluster as a crime scene: collect evidence from the API, the node, and the vendor source before you decide the response.

## CVE Triage and Upgrade Target Selection

A Kubernetes CVE advisory normally gives you three pieces of information that matter for action: affected versions, fixed versions, and conditions required for exploitation. Severity tells you how worried to be, but the fixed-version line tells you what to do. If the advisory says that 1.34.4 and 1.35.0 contain the fix, then "upgrade to a newer Kubernetes" is too vague; the plan must name a patch release that is both fixed and reachable from your current cluster.

```text
+-------------------------------------------------------------+
|              KUBERNETES CVE EXAMPLE                         |
+-------------------------------------------------------------+
|                                                             |
|  CVE-2024-XXXX: Container Escape via Symlink Attack          |
|                                                             |
|  Severity: HIGH (CVSS 8.8)                                  |
|  Affected: v1.26.0 - v1.27.5                                |
|  Fixed: v1.27.6, v1.28.2, v1.29.0                           |
|                                                             |
|  Impact:                                                    |
|  A malicious container can write to the host filesystem      |
|  using a specially crafted symlink                          |
|                                                             |
|  Action:                                                    |
|  Upgrade to a fixed version immediately                     |
|                                                             |
|  Where to find CVEs:                                        |
|  - kubernetes.io/security                                   |
|  - github.com/kubernetes/kubernetes/security/advisories     |
|  - cve.mitre.org                                            |
|                                                             |
+-------------------------------------------------------------+
```

The safest target is usually the smallest fixed version that fits your support and version-skew constraints. If production is already on 1.34.1 and the advisory is fixed in 1.34.4, a patch upgrade to 1.34.4 is often less disruptive than a minor upgrade to 1.35.0. If the current minor is unsupported, however, you cannot wait for a patch that will never be built, so the response becomes a minor-version upgrade path with careful staging.

You should also read the exploit conditions before you decide whether mitigations can buy time. A CVE that requires privileged pods, hostPath volumes, or a disabled admission policy may be mitigated temporarily by tightening Pod Security Admission, seccomp, AppArmor, RBAC, or runtime policy. Those mitigations do not erase the need to upgrade, but they can reduce reachable attack paths while change approvals, node drains, and workload owners are coordinated.

Exercise scenario: an advisory says that a kube-apiserver authorization bypass affects 1.33.0 through 1.33.8 and 1.34.0 through 1.34.3, with fixes in 1.33.9, 1.34.4, and 1.35.0. Your staging cluster is 1.34.1, production is 1.34.2, and development is 1.33.7. The first decision is not whether to upgrade everything to the newest visible release; the first decision is which fixed target matches each current minor while preserving a safe order.

For staging and production in that scenario, a move to 1.34.4 is the narrowest secure change because both clusters are already on 1.34 and the fixed patch exists in that minor. Development can move to 1.33.9 if 1.33 is still supported in the working window, or it can be promoted to 1.34.4 if the organization wants to rehearse the same target before production. If 1.33 has already left support, development should not be patched inside that minor because no supported fixed patch is available.

The second decision is whether exploitability requires interim controls. If the bypass is reachable by authenticated users with broad namespace access, tighten RBAC and admission policy while the maintenance is scheduled. If the bypass requires a disabled feature or a configuration you do not use, document that fact, but do not use it as an excuse to leave the version unpatched indefinitely. A good triage note separates "not currently reachable" from "not affected," because those are different claims.

The third decision is sequencing. Development should run the commands first if it is connected enough to reveal real compatibility issues but isolated enough that failure has low business impact. Staging should then prove workload behavior, admission, and observability with production-like objects. Production should receive the smallest fixed target only after the rehearsal has produced exact commands, validation output, and rollback triggers. That sequence is a security acceleration, not a delay, because it reduces unknowns before the most sensitive change.

Before running this, what output do you expect from a healthy pre-upgrade assessment? You should expect version data that is consistent, a target release that appears in the release notes, no surprise deprecated API use for critical workloads, and a backup artifact that exists before any control-plane component changes.

```bash
# 1. Check current version vulnerabilities
kubectl version
# Research CVEs for your version

# 2. Review release notes for security fixes
# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/

# 3. Backup critical components
kubectl get all -A -o yaml > cluster-backup.yaml
ETCDCTL_API=3 etcdctl snapshot save backup.db

# 4. Check deprecated APIs in use (cluster-wide request traffic)
kubectl get --raw /metrics | grep apiserver_requested_deprecated
# Optional manifest spot-check for critical workloads:
kubectl get pod -n <namespace> <name> -o yaml | grep apiVersion
```

That checklist is intentionally conservative. The all-namespaces YAML export is not a complete disaster-recovery backup, but it captures enough workload intent to compare before and after state. The etcd snapshot is the high-value control-plane artifact in a self-managed cluster, because kubeadm cannot simply unwind every control-plane state change if the API server or datastore becomes unhealthy. The `apiserver_requested_deprecated` metric shows actual deprecated API traffic, not kubectl client warnings, because a security upgrade can fail for reasons that are not themselves security vulnerabilities.

When choosing between fixed releases, evaluate both exposure and blast radius. A same-minor patch usually has the smallest behavioral surface, while a minor upgrade may include API removals, feature-gate changes, default changes, and new benchmark expectations. The security answer is not always "latest immediately"; the security answer is "fixed, supported, compatible, and verifiable within the shortest responsible window."

This is where CKS judgment differs from pure command recall. A candidate who memorizes `kubeadm upgrade apply` can still make a poor security decision by selecting a target that does not contain the fix, by patching only the control plane, or by leaving unsupported development clusters connected to the same delivery pipeline. A candidate who can explain the target selection can defend the change even when the exact advisory details vary.

| Decision question | Prefer a patch upgrade when | Prefer a minor upgrade when |
|---|---|---|
| Is the current minor supported? | Yes, and the fix exists in the same minor. | No, or the fix is not backported to your minor. |
| Are API removals likely? | You need a low-risk emergency fix. | You already cleared deprecation scans in staging. |
| Are nodes heterogeneous? | You can patch one pool at a time. | You need to standardize an aging fleet. |
| Is a provider involved? | Provider has shipped the fixed patch. | Provider support policy requires moving to a newer minor. |

## Secure Kubeadm Upgrade Workflow

Kubeadm upgrades are ordered because the Kubernetes API server is the compatibility anchor for the rest of the cluster. The API server must be upgraded before components that depend on its API behavior, and kubelets must not run newer than the API server they report to. This order is not ceremony; it prevents a partially upgraded cluster from entering a version relationship that the project does not test or support.

The pre-upgrade stage should produce an explicit change record. That record names the current version, target version, affected CVE or maintenance reason, backup location, deprecation findings, expected version skew during the maintenance, rollback trigger, and validation checks. In a CKS context, you may not be asked to write a change record, but thinking in those terms makes the exam commands easier because every command has a reason.

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

The kubeadm sequence separates planning from applying because planning queries the current cluster and shows which versions kubeadm considers valid. If the plan output does not show the fixed version you expected, stop and investigate repository configuration, supported upgrade paths, and package availability before changing the control plane. Pressing ahead with a different version can leave you with a cluster that is newer but still not patched for the advisory that triggered the work.

On a multi-control-plane cluster, security pressure does not remove the need for quorum and availability discipline. Upgrade one control-plane node at a time, verify static pod health and etcd membership after each step, then proceed to the next member. For workers, drain, upgrade kubelet and the runtime as required, restart services, uncordon, and confirm that workloads return with the same security posture they had before the change.

The CKS angle is that every operational step has a security side effect. Draining a node exercises PodDisruptionBudgets and can reveal workloads that were running as single points of failure. Restarting kubelet applies new defaults and may change how admission results surface on the node. Updating kubectl reduces the chance that the operator misreads server behavior through an older client, even though kubectl itself has a looser version-skew allowance.

Backups deserve special care because a backup that has never been restored is only an optimistic file. In a self-managed cluster, the etcd snapshot should be written to a known location, copied off the node when appropriate, and paired with the restore command and certificate assumptions needed to use it. The YAML export is useful for comparison, but the etcd snapshot is the object that protects the control plane from a failed upgrade or data corruption event.

Package management should be explicit as well. Pin or select the exact kubeadm, kubelet, and kubectl versions needed for the target, then avoid unattended package jobs during the maintenance window. A host-level automation tool that upgrades kubelet early can create skew before the operator reaches that node. Conversely, forgetting to upgrade kubelet after the control plane can leave the cluster in a technically running but incomplete security state.

Node drains are another place where security and availability overlap. A drain that fails because of a strict PodDisruptionBudget may reveal a workload that cannot tolerate maintenance, while a forceful drain may evict a critical pod without enough replicas. In a security emergency, you may accept more disruption than usual, but you should make that decision consciously and record which workloads were protected, delayed, or manually handled.

After each phase, take a small verification pause instead of waiting until the end. Confirm the upgraded control-plane pod image, confirm the node Ready state, confirm the kubelet version, and confirm that workloads rescheduled. These checkpoints make it easier to identify which step introduced a fault. They also help you avoid the common failure mode where the team completes every package command and only then discovers that the first control-plane node was unhealthy.

Which approach would you choose here and why: an emergency patch directly in production after a green `kubeadm upgrade plan`, or a short staging rehearsal that captures the exact commands, validation output, and rollback trigger first? The answer depends on exploitability and exposure, but a rehearsal often shortens production risk because it turns the maintenance into execution rather than discovery.

## Compatibility, Deprecations, and Version Skew

Security upgrades frequently fail because the cluster is carrying old API shapes into a newer API server. The vulnerability may be in kubelet or the API server, but the maintenance can still be blocked by an Ingress manifest using an API version removed long ago. That is why a security upgrade plan must include compatibility work, not merely package installation.

```yaml
# Old API (may be removed in new version)
apiVersion: extensions/v1beta1
kind: Ingress

# New API
apiVersion: networking.k8s.io/v1
kind: Ingress
```

The old and new Ingress snippets are deliberately simple, but the real migration is usually more than changing one string. Newer API versions can require different fields, defaulting behavior, validation rules, or controller expectations. When a deprecated API warning appears, fix the object model before the upgrade if the workload is important; otherwise you risk discovering the required schema changes during the maintenance window.

CustomResourceDefinitions add another layer because the Kubernetes API server can be healthy while an operator still depends on an old CRD schema or client library. Before a minor upgrade, check whether controllers, admission webhooks, and operators publish compatibility guidance for the target release. A security patch that breaks the policy controller can accidentally reduce enforcement, so add-ons that participate in security decisions should be part of the upgrade evidence.

Admission changes deserve the same attention because security controls often move from deprecated extensions into newer built-in mechanisms. PodSecurityPolicy was removed in earlier Kubernetes releases, and Pod Security Admission is the replacement baseline for namespace-level pod security enforcement. A cluster that upgrades without mapping old policy intent to new admission controls can accidentally weaken enforcement even though the binaries are newer.

```bash
# Check if PodSecurityPolicy is being removed
# (Removed in 1.25, use Pod Security Admission instead)
kubectl get psp 2>&1 | grep -q "the server doesn't have" && echo "PSP already removed"
```

Feature gates create another compatibility edge. A gate that was needed when a feature was beta may become unnecessary, removed, or ignored when the feature graduates. Leaving stale feature-gate flags in static pod manifests can make future troubleshooting harder because operators cannot quickly tell which flags still affect behavior and which are historical leftovers.

Admission webhooks are especially sensitive during upgrades because they sit directly in the API request path. A webhook using an old certificate, unsupported API, or unavailable service can block workload creation at the exact moment nodes are being drained and pods need to reschedule. For a security upgrade, review failure policies, webhook health, certificate expiry, and compatibility with the target API server before the maintenance begins.

```yaml
# Some security features graduate from beta to stable
# Check if feature gates need updating in API server

# Example: PodSecurity feature (stable since 1.25)
- --feature-gates=PodSecurity=true  # May not be needed anymore
```

Version skew is the formal boundary around this compatibility work. The API server should be the newest Kubernetes component in the cluster; controller-manager and scheduler follow tightly; kubelets may lag within the documented policy, but they must not lead the API server. Skew rules are not a performance recommendation, because they define the combinations that upstream tests and supports.

```text
+-------------------------------------------------------------+
|              VERSION SKEW RULES                             |
+-------------------------------------------------------------+
|                                                             |
|  kube-apiserver:                                            |
|  +-- Must be the newest component in the cluster             |
|                                                             |
|  kube-controller-manager, kube-scheduler:                   |
|  +-- Same minor as API server or one minor older             |
|                                                             |
|  kubelet:                                                   |
|  +-- Up to three minors older (kubelet 1.25+)                |
|  +-- Never newer than the API server                         |
|                                                             |
|  kubectl:                                                   |
|  +-- One minor newer or older is supported                   |
|                                                             |
|  Why this matters for security:                             |
|  - Inconsistent versions can produce unexpected behavior     |
|  - Security fixes may not protect every component equally    |
|  - Upgrade API server first, then the remaining components   |
|                                                             |
+-------------------------------------------------------------+
```

For kubelet 1.25 and later, the API server at 1.35 may pair with kubelets as old as 1.32 (three minor versions behind). Before kubelet 1.25, the limit was two minor versions older. See the [Kubernetes version skew policy](https://kubernetes.io/releases/version-skew-policy/).

Pause and predict: what happens if you correctly upgrade the API server to 1.35, but a worker node's kubelet is upgraded before the controller-manager, which still runs 1.33? The kubelet may still be legal if it is not newer than the API server, but the controller-manager relationship may violate skew once the API server is two minors ahead, so the cluster can enter a state that is partially functional yet unsupported.

The practical lesson is to maintain a version-skew map during the upgrade, especially when multiple administrators or automation jobs touch the same cluster. Record the intended order, the temporary states that are legal, and the states that require an immediate stop. If an accidental package upgrade puts a node or component outside policy, your next action is not to keep going blindly; it is to restore a supported relationship by moving the correct control-plane component or node next.

A useful skew map is small enough to read during the change. It can be a table in the ticket that lists each control-plane component, each node pool, the current version, the target version, and the allowed temporary state. The point is not paperwork; the point is shared situational awareness. When two engineers work in parallel, the map prevents one person from upgrading a node pool while another is still proving the API server phase.

## Verification, Rollback, and Managed Cluster Paths

Post-upgrade verification proves that the cluster is safer, not just newer. The first checks are liveness checks: API server pods are running, nodes are Ready, and system pods are stable. The second checks are security checks: RBAC still denies what it should deny, admission still rejects unsafe workloads, NetworkPolicy still exists and is enforced by the CNI, and benchmark output is understood rather than ignored.

Add event and log review to that verification pass. Kubernetes events can show admission denials, image pull failures, scheduling problems, and CNI errors that a simple Ready check misses. Control-plane logs can show authentication errors, webhook timeouts, or repeated authorization denials after the API server changes. The purpose is not to read every log line manually; the purpose is to sample the paths most likely to reveal a security-control regression before users discover it indirectly.

Observability checks should be tied to the upgrade objective. If the upgrade was driven by a kube-apiserver CVE, inspect API server health, authentication, authorization, admission, and audit behavior first. If the advisory affected kubelet or the container runtime boundary, prioritize node versions, kubelet logs, runtime status, pod security contexts, and privileged workload inventory. This focus prevents validation from becoming a generic dashboard tour that looks thorough but misses the component that was actually vulnerable.

Audit logging deserves particular attention in security upgrades because a broken audit path can hide later evidence. Confirm that audit policy configuration still loads, audit log destinations still receive records, and high-value events such as denied pod creation or privileged workload attempts remain visible. A cluster can be technically patched while becoming harder to investigate, and that is not a good security outcome. Verification should preserve detection as well as prevention.

Finally, decide who signs off on the upgraded security posture. Platform engineers can prove component health, but workload owners may need to confirm application behavior, and security engineers may need to accept benchmark exceptions or temporary mitigations. A clear sign-off boundary prevents the upgrade from ending in a vague "looks good" message. The result you want is a dated record that says which version is running, which security checks passed, which exceptions remain, and who owns each follow-up. That artifact is also what lets the next upgrade begin from evidence instead of memory.

```bash
# Check Kubernetes security announcements
# https://kubernetes.io/docs/reference/issues-security/security/

# Check specific component for CVEs
trivy image registry.k8s.io/kube-apiserver:v1.35.0

# Check node OS for security updates
apt list --upgradable 2>/dev/null | grep -i security

# Use kube-bench to verify security settings after upgrade
./kube-bench run --targets=master
```

Benchmark tools such as kube-bench are useful after an upgrade because the benchmark version, Kubernetes version, and control-plane defaults all interact. A new failure does not automatically mean the upgrade broke the cluster; it may mean the benchmark now checks a control that was not checked before, or that the target Kubernetes version has a different recommended setting. Treat benchmark changes as evidence requiring triage, not as automatic proof that rollback is necessary.

Rollback decisions should be written before the maintenance begins because stress makes vague criteria dangerous. Roll back when the API server cannot start, authentication or authorization is broken, etcd health is compromised, or admission rejects valid critical workloads in a way you cannot fix quickly. Do not roll back merely because a deprecated API warning appears after the upgrade; warnings are a signal to fix manifests, not a reason to reintroduce an unpatched version.

```text
+-------------------------------------------------------------+
|              ROLLBACK TRIGGERS                              |
+-------------------------------------------------------------+
|                                                             |
|  Roll back if upgrade causes:                               |
|  ---------------------------------------------------------  |
|  - API server not starting                                  |
|  - Authentication failures                                  |
|  - RBAC not working                                         |
|  - Networking issues such as CNI incompatibility            |
|  - Admission controller rejecting valid workloads           |
|                                                             |
|  Do not roll back for:                                      |
|  ---------------------------------------------------------  |
|  - Deprecated API warnings that require manifest fixes       |
|  - Feature changes that have documented migration paths      |
|  - Known issues with tested workarounds                     |
|                                                             |
+-------------------------------------------------------------+
```

The rollback mechanism differs between components. Kubelet packages can usually be downgraded if the package repository still contains the previous version, but kubeadm does not support a casual control-plane downgrade after `upgrade apply`. For control-plane failure, your real rollback is the tested etcd snapshot and the documented restore procedure, which is why the backup step is a security requirement rather than an administrative nicety.

```bash
# Check previous kubelet version
journalctl -u kubelet | grep "Kubelet version" | head -1

# Downgrade kubelet (if needed)
sudo apt install kubelet=<previous-version>
sudo systemctl restart kubelet

# Note: kubeadm doesn't support direct downgrade
# For control plane, restore from etcd backup
```

The exam often presents upgrade tasks as small scenarios, so practice reading the intent behind each command. If the task says to verify readiness, collect version consistency and deprecated API evidence. If it says to verify post-upgrade security, test RBAC, admission, benchmark output, and system pod health. If it says to find the version that fixes a CVE, do not guess from the highest available package; connect the advisory's fixed-version line to the target.

```bash
# Check current versions match
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {.status.nodeInfo.kubeletVersion}{"\n"}{end}'

# All should show same version
# Inconsistent versions = security risk

# Check for deprecated APIs in use
kubectl get --raw /metrics | grep apiserver_requested_deprecated
```

The `apiserver_requested_deprecated` metric is a useful clue because it shows requests to deprecated APIs that may not be obvious from static manifests alone. Controllers, operators, and CI tools can continue using older APIs even after application YAML has been cleaned up. During an upgrade rehearsal, that metric helps you identify the caller before a removed API turns from a warning into an outage.

```bash
# After upgrade, verify security settings
# 1. Check API server is running — expect at least one Running apiserver pod
kubectl get pods -n kube-system | grep apiserver

# 2. Verify RBAC allow + deny with a lab ServiceAccount and RoleBinding
kubectl create namespace upgrade-test --dry-run=client -o yaml | kubectl apply -f -
kubectl create serviceaccount probe-sa -n upgrade-test --dry-run=client -o yaml | kubectl apply -f -
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-lister
  namespace: upgrade-test
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["list", "get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-lister-binding
  namespace: upgrade-test
subjects:
- kind: ServiceAccount
  name: probe-sa
  namespace: upgrade-test
roleRef:
  kind: Role
  name: pod-lister
  apiGroup: rbac.authorization.k8s.io
EOF
kubectl auth can-i list pods -n upgrade-test --as=system:serviceaccount:upgrade-test:probe-sa
# Expect: yes
kubectl auth can-i create pods -n upgrade-test --as=system:serviceaccount:upgrade-test:probe-sa
# Expect: no

# 3. Confirm admission webhook configurations are registered — expect resource names (may be empty on minimal clusters)
kubectl get validatingwebhookconfiguration,mutatingwebhookconfiguration

# 4. Negative Pod Security Admission test — expect Admission denied for privileged pod
kubectl label namespace upgrade-test pod-security.kubernetes.io/enforce=restricted --overwrite
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: psa-probe
  namespace: upgrade-test
spec:
  containers:
  - name: probe
    image: busybox
    command: ["sleep", "60"]
    securityContext:
      privileged: true
EOF
# Expect: error contains "violates PodSecurity"
kubectl delete pod psa-probe -n upgrade-test --ignore-not-found

# 5. Run kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench
```

The RBAC check should include both allowed and denied expectations. A single `can-i` result can be misleading if you ask only for a permission the user is supposed to have. For security validation, test a representative normal action and a representative forbidden action with a ServiceAccount you created in the lab, because an upgrade that accidentally broadens permissions can be more dangerous than one that blocks too much.

Admission validation should also include a negative test. Listing webhook configurations confirms the admission path is registered, and a Pod Security Admission probe in a restricted namespace confirms enforcement still rejects unsafe workloads. Do not run destructive probes against production workloads, but do prove that the policy path still exists. A successful upgrade should preserve both the ability to run valid workloads and the ability to block invalid ones.

```bash
# Question: "Upgrade cluster to version that fixes CVE-2024-XXXX"

# 1. Research CVE (exam may provide info)
# 2. Find fixed version
kubectl version

# 3. Plan upgrade
sudo kubeadm upgrade plan | grep -E "v1\.[0-9]+\.[0-9]+"

# 4. Execute upgrade to fixed version
```

Pause and predict: after upgrading from 1.34 to 1.35, you run kube-bench and see three new failed checks that did not appear before the upgrade. That can happen because the benchmark profile changed, the target version changed, or a default moved from acceptable to discouraged, so your job is to map each finding to the benchmark guidance before deciding whether it is a real regression.

Managed Kubernetes changes the mechanics, not the security reasoning. EKS, GKE, and AKS separate control-plane upgrades from node upgrades, and each provider controls which versions are available at a given moment. You still need to identify the fixed version, understand provider maintenance windows, upgrade nodes or node images, validate policy behavior, and watch for add-on compatibility such as CNI, CSI, DNS, ingress, and admission webhooks.

```text
+-------------------------------------------------------------+
|              MANAGED K8S UPGRADE CONSIDERATIONS             |
+-------------------------------------------------------------+
|                                                             |
|  EKS (AWS):                                                 |
|  - Control plane upgraded separately from nodes             |
|  - Managed node groups can auto-upgrade                     |
|  - eksctl upgrade cluster                                   |
|                                                             |
|  GKE (GCP):                                                 |
|  - Release channels for automatic upgrades                  |
|  - Maintenance windows for planned upgrades                 |
|  - gcloud container clusters upgrade                        |
|                                                             |
|  AKS (Azure):                                               |
|  - Auto-upgrade channel available                           |
|  - Node image upgrades separate from control plane upgrade  |
|  - az aks upgrade                                           |
|                                                             |
|  Security note:                                             |
|  Managed Kubernetes may lag the newest upstream release      |
|  for stability, so check provider patch timelines           |
|                                                             |
+-------------------------------------------------------------+
```

In managed clusters, the common security mistake is assuming the provider upgraded everything that matters. The provider usually owns the hosted control plane, but you still own workloads, policy configuration, add-ons, node pools, admission webhooks, and many identity bindings. A secure managed upgrade plan therefore includes both provider commands and cluster-level verification, because the shared-responsibility line does not disappear during a CVE response.

Managed upgrade timing should be compared with the advisory's exposure window. Providers sometimes delay a new upstream patch while they validate integration with their platform, and that delay may be reasonable for stability. Your job is to know the provider's published patch timeline, apply compensating controls if the fixed control-plane build is not yet available, and avoid promising that an upstream fixed version is installed before the provider actually offers it.

Node image upgrades in managed services are easy to overlook because they may use a separate command, pool operation, or auto-upgrade channel. A control-plane version banner can look reassuring while old nodes still carry vulnerable kubelets, container runtimes, or operating-system packages. Post-upgrade validation should therefore include node image versions, kubelet versions, daemonset health, CNI status, DNS behavior, and workload admission, not merely the provider console's control-plane status.

## Patterns & Anti-Patterns

Good upgrade practice is repeatable because a security response should not depend on whoever happens to be on call. The patterns below are written as operating habits rather than slogans. Each one creates evidence that another engineer can inspect, and each anti-pattern names the tempting shortcut that usually causes the failure.

| Pattern | When to use it | Why it works | Scaling consideration |
|---|---|---|---|
| Advisory-to-target mapping | Any CVE-driven upgrade | It connects affected and fixed versions to an exact release. | Keep the mapping in the change record for audit review. |
| Rehearsed kubeadm runbook | Self-managed clusters | It turns production maintenance into a known sequence. | Refresh it for each minor version because removals accumulate. |
| Version-skew board | Multi-node or multi-admin upgrades | It shows which temporary states are legal. | Update after each control-plane and node pool step. |
| Post-upgrade security probe set | Every upgrade | It verifies RBAC, admission, policy, and benchmark behavior. | Automate probes, but keep human review for surprising deltas. |

| Anti-pattern | What goes wrong | Better alternative |
|---|---|---|
| Upgrading to the newest visible package | The package may not be the fixed or supported target you intended. | Choose the target from advisories, release notes, and skew policy. |
| Treating node upgrades as optional | Kubelets and node images can retain vulnerable behavior. | Plan node pool upgrades and verify every kubelet version. |
| Ignoring deprecated API traffic | Removed APIs can break controllers during or after the upgrade. | Check manifests and API server metrics before the maintenance. |
| Trusting one green dashboard | Health checks can miss weakened authorization or admission behavior. | Run explicit security probes after the upgrade. |

These patterns add a small amount of ceremony, but the ceremony pays for itself when a patch is urgent. A short runbook, a version-skew board, and a validation checklist are much cheaper than improvising under a public advisory. The anti-patterns are attractive because they save minutes at the beginning; they often cost hours when the cluster enters an unsupported state or returns with a weaker security posture.

## Decision Framework

Use the following framework when a Kubernetes upgrade is security-driven. Start with the advisory, not with the package manager. Identify the affected component, affected versions, fixed versions, exploit conditions, and whether your current minor is still supported. Then decide whether a same-minor patch, one-step minor upgrade, or provider-controlled upgrade path is the smallest responsible change that lands on a fixed version.

```text
+-------------------------------------------------------------+
|              SECURITY UPGRADE DECISION FLOW                 |
+-------------------------------------------------------------+
|  1. Does the advisory affect a component you run?            |
|     +-- No: document why, then monitor.                      |
|     +-- Yes: continue.                                       |
|                                                             |
|  2. Is your current minor still supported?                   |
|     +-- Yes: prefer the fixed patch in the same minor.       |
|     +-- No: plan a supported minor upgrade path.             |
|                                                             |
|  3. Is exploitation reachable in your environment?           |
|     +-- Yes: shorten approval and maintenance windows.       |
|     +-- No: apply mitigations, but still schedule patching.  |
|                                                             |
|  4. Are deprecations, add-ons, and skew clean?               |
|     +-- Yes: execute runbook and validate.                   |
|     +-- No: fix blockers or create a staged upgrade.         |
+-------------------------------------------------------------+
```

The framework deliberately separates urgency from recklessness. A reachable critical vulnerability can justify emergency change approval, but it does not justify skipping backup, version-skew checks, or post-upgrade security validation. Conversely, a low-exploitability advisory may allow a normal maintenance window, but it still requires a target version and an owner because unsupported clusters do not become safer by waiting.

For self-managed kubeadm clusters, the decision often turns on whether you can safely move control-plane components and nodes within the required window. For managed clusters, the decision turns on provider version availability, maintenance windows, node pool behavior, and add-on compatibility. In both cases, the final decision should be written as an operational sentence: "upgrade cluster X from version A to fixed version B by date C, using mitigations D until completion, and validate with checks E."

## Did You Know?

- **Kubernetes patch support follows recent minor releases.** The exact dates move with the release calendar, so security planning should reference the official patch-release page rather than a copied wiki table.

- **A same-minor patch can be a security upgrade.** Moving from 1.34.1 to 1.34.4 may close a CVE with less behavioral change than jumping directly to a new minor release.

- **Version skew policy is a security control.** Unsupported component combinations make it harder to know whether a fix is actually protecting the path you care about.

- **Managed clusters still need node and add-on work.** A hosted control-plane patch does not automatically update every kubelet, node image, CNI, CSI driver, or admission webhook.

## Common Mistakes

Security upgrade failures usually come from missing evidence rather than missing commands. The command sequence is easy to memorize, but the decision around it requires proof that the cluster is affected, the target is fixed, and the resulting system still enforces the same controls.

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Skipping versions without checking support policy | Teams confuse urgency with permission to ignore tested upgrade paths. | Upgrade one minor at a time unless official guidance says otherwise. |
| Upgrading workers before the control plane | Node automation runs independently from the control-plane maintenance. | Upgrade the API server first, then controllers, then kubelets within skew policy. |
| Not checking deprecations before the change | Operators focus on the CVE and forget workload API compatibility. | Review release notes, scan manifests, and inspect deprecated API metrics. |
| Taking no etcd backup before kubeadm apply | The cluster looks healthy, so the backup feels like delay. | Capture and test an etcd snapshot before changing self-managed control planes. |
| Running unsupported versions in non-production | Development clusters are treated as disposable even when they hold credentials. | Keep all connected environments inside the supported patch window. |
| Trusting benchmark failures without triage | New benchmark versions can add or reinterpret checks. | Compare old and new benchmark profiles, then classify each finding. |
| Assuming managed service upgrades finish the job | Provider-owned and customer-owned responsibilities blur during incidents. | Verify node pools, add-ons, workloads, policies, and identity bindings separately. |

## Learner check

> Version skew is the formal boundary around this compatibility work. The API server should be the newest Kubernetes component in the cluster; controller-manager and scheduler follow tightly; kubelets may lag within the documented policy, but they must not lead the API server.

Before you continue, explain why a kubelet at 1.32 can remain legal on an API server at 1.35 while a controller-manager at 1.33 cannot. A strong answer names the separate skew rules for kubelets versus control-plane components and cites the three-minor kubelet allowance for kubelet 1.25+.

## Quiz

<details><summary>Question 1: Your security team receives a CVE advisory for a container escape vulnerability affecting Kubernetes 1.33 through 1.34.3. Production runs 1.34.1, and the advisory says the fix is in 1.34.4 and 1.35.0. What do you recommend during a short change freeze?</summary>
Recommend an emergency same-minor patch to 1.34.4 if the organization can approve it, because it reaches a fixed version with less behavioral change than a minor upgrade. The change freeze should not be treated as absolute when the advisory describes a reachable container escape. Interim mitigations such as restricted Pod Security Admission, seccomp, AppArmor, tighter RBAC, and disabling privileged workloads can reduce exposure, but they do not replace the patched binary. A jump to 1.35.0 may be reasonable later, but the smallest secure target is the fixed 1.34 patch.
</details>

<details><summary>Question 2: After an upgrade, `kubectl get nodes` shows the API server at 1.35 and one worker kubelet still at 1.33. The cluster appears healthy. What do you check before calling the upgrade complete?</summary>
First check the Kubernetes version-skew policy to confirm whether that kubelet is still inside the supported relationship with the API server. Even if the skew is technically allowed, the missed worker may still lack security fixes included in the target upgrade, so you should inspect the advisory and upgrade plan before accepting the state. Verify the node pool package state, node image, runtime updates, and workload placement on that node. The upgrade is not complete until every intended kubelet version is accounted for and the security objective is satisfied.
</details>

<details><summary>Question 3: A colleague wants to run `kubeadm upgrade apply v1.35.0` immediately because `kubeadm upgrade plan` shows it as available. Which security-critical steps are missing?</summary>
They are missing the evidence that makes the upgrade defensible: advisory-to-target mapping, etcd backup, deprecated API review, version-skew plan, and post-upgrade validation. `kubeadm upgrade plan` proves that kubeadm can see an upgrade path, but it does not prove that the target fixes the CVE that triggered the change. The team also needs to plan kubelet and kubectl package updates, because a control-plane upgrade alone can leave vulnerable nodes behind. After the apply step, RBAC, admission, NetworkPolicy, and benchmark checks should prove that the cluster is still enforcing security controls.
</details>

<details><summary>Question 4: Development runs 1.33 while staging and production run 1.34. The organization targets 1.35 next, and the developers argue that an unsupported development cluster is acceptable. How do you evaluate that risk?</summary>
An unsupported development cluster is still a security problem if it connects to registries, CI systems, cloud accounts, identity providers, or production-like data. Attackers often benefit from weaker adjacent environments because those environments hold credentials and deployment paths. The better strategy is to upgrade development first, use it as a rehearsal environment, then move staging and production with the lessons learned. Treating development as disposable is only safe when it is truly isolated, and most real development clusters are not.
</details>

<details><summary>Question 5: After moving from 1.34 to 1.35, kube-bench reports three new failed checks, but no manifest changed. How do you diagnose the result?</summary>
Compare the benchmark version, benchmark target profile, and Kubernetes target version before assuming the upgrade introduced a regression. A new failed check may reflect a new recommendation or a stricter interpretation rather than a changed control-plane flag. Then inspect the actual control referenced by each finding, such as API server flags, kubelet configuration, or file permissions. Fix true regressions, document accepted exceptions, and avoid rollback unless the finding maps to a serious operational or security failure.
</details>

<details><summary>Question 6: Your managed cluster provider patched the hosted control plane, but node pools remain on the previous minor version and the CNI add-on is behind. What is your completion decision?</summary>
Do not call the security upgrade complete just because the hosted control plane moved. Managed services split responsibility, so the provider may own the API server while you still own node pools, add-ons, workload policy, and validation. Check the provider version policy, schedule node pool upgrades, review add-on compatibility, and run the same RBAC, admission, NetworkPolicy, and workload checks you would run on a self-managed cluster. The completion decision should be based on the full attack surface, not one provider status line.
</details>

## Hands-On Exercise

Exercise scenario: you are preparing a security-focused Kubernetes upgrade rehearsal in a lab cluster. The goal is not to perform a real control-plane upgrade from this page, because lab environments vary. The goal is to practice the evidence collection, compatibility checks, and post-upgrade validation that make a real upgrade safe enough to execute under pressure.

Start by creating an isolated namespace so the rehearsal does not interfere with existing workloads. You will deploy a small workload with explicit security context settings, capture its state, inspect cluster and node versions, check for deprecated API clues, and then run the same security probes you would run after a real upgrade. Keep the outputs together, because the value of the exercise is the comparison between pre-change intent and post-change behavior.

- [ ] Evaluate a simulated CVE advisory and select a fixed 1.35 patch target for the rehearsal notes.
- [ ] Audit cluster nodes, control-plane images, kubelet versions, and workload API evidence before the change.
- [ ] Implement a kubeadm-style preflight record with backup, target version, and version-skew assumptions.
- [ ] Diagnose post-upgrade RBAC, admission, NetworkPolicy, and benchmark evidence for regressions.
- [ ] Design a short managed Kubernetes completion note that separates provider work from cluster-owner work.

<details><summary>Solution guide for task 1</summary>
Write one sentence that names the affected version, fixed version, and urgency. A good answer looks like this: "Cluster 1.34.1 is affected by the simulated advisory, 1.34.4 and 1.35.0 are fixed, and the rehearsal will target the smallest fixed version unless the support window requires moving to 1.35." The important part is that the target comes from the advisory, not from guessing the newest visible package.
</details>

First, create an isolated namespace for the rehearsal. The namespace gives every later command a small, reversible target, which makes the exercise safe to repeat.

```bash
kubectl create namespace upgrade-test
```

Next, deploy a test workload configured with strict security contexts. This pod lets you verify that settings such as `runAsNonRoot` and `readOnlyRootFilesystem` remain present and visible after an upgrade or simulated validation pass.

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: security-test
  namespace: upgrade-test
  labels:
    app: security-test
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

Before initiating any upgrade, capture the current state of the workload. If a later validation step fails, this file gives you a concrete comparison point instead of relying on memory.

```bash
echo "=== Pre-Upgrade State Capture ==="
kubectl get all -n upgrade-test -o yaml > /tmp/pre-upgrade-backup.yaml
echo "Backup saved to /tmp/pre-upgrade-backup.yaml"
```

Audit the current versions of your cluster components. You need to know exactly what versions are running to determine whether they are vulnerable to known CVEs and whether the target upgrade path is legal.

```bash
echo "=== Current Versions ==="
kubectl version

echo "=== Node Versions ==="
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {.status.nodeInfo.kubeletVersion}{"\n"}{end}'
```

Deprecated APIs are a major source of failed upgrades. Check your manifests and running resources to confirm that the objects in this small rehearsal are using API versions that remain valid for the target release.

```bash
echo "=== Checking Deprecated APIs ==="
# Look for deprecated API versions in our resources
kubectl get pod security-test -n upgrade-test -o yaml | grep "apiVersion"
```

Pause and decide: if you find a deprecated API in use during a rehearsal, fix it before the production upgrade rather than treating the warning as a post-upgrade cleanup item. The warning means a future API server may reject the object, and production maintenance is the wrong time to learn the replacement schema.

After the upgrade or simulated validation point, verify that Role-Based Access Control still behaves as expected. An upgrade should never silently widen permissions, and it should not unexpectedly remove permissions required by normal workloads.

```bash
echo "=== RBAC Verification ==="
kubectl create serviceaccount probe-sa -n upgrade-test --dry-run=client -o yaml | kubectl apply -f -
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-lister
  namespace: upgrade-test
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["list", "get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-lister-binding
  namespace: upgrade-test
subjects:
- kind: ServiceAccount
  name: probe-sa
  namespace: upgrade-test
roleRef:
  kind: Role
  name: pod-lister
  apiGroup: rbac.authorization.k8s.io
EOF
kubectl auth can-i list pods -n upgrade-test --as=system:serviceaccount:upgrade-test:probe-sa
# Expect: yes
kubectl auth can-i create pods -n upgrade-test --as=system:serviceaccount:upgrade-test:probe-sa
# Expect: no
```

Confirm that the security contexts applied to your workload are still present. This does not prove every runtime control is enforced, but it catches accidental manifest drift and gives you a starting point for admission and runtime policy checks.

```bash
echo "=== Security Context Verification ==="
kubectl get pod security-test -n upgrade-test -o jsonpath='{.spec.securityContext}' && echo ""
kubectl get pod security-test -n upgrade-test -o jsonpath='{.spec.containers[0].securityContext}' && echo ""
```

Ensure the pod remains in a running state and has not been blocked by a new admission controller, image policy, or node scheduling issue. If this simple pod cannot run, investigate before validating more complex workloads.

```bash
echo "=== Pod Status ==="
kubectl get pod security-test -n upgrade-test
```

In a real scenario, you would run a security benchmarking tool such as kube-bench against your nodes to ensure the new components are configured securely. This lab keeps the command as an explicit reminder because benchmark execution depends on the lab environment.

```bash
echo "=== Security Benchmark Check ==="
echo "On control plane, would run: ./kube-bench run --targets=master"
echo "On worker nodes, would run: ./kube-bench run --targets=node"
```

Verify that NetworkPolicy resources are still accepted by the API server and select the rehearsal pod. Remember that API acceptance is not the same as enforcement, so a real production validation should also test traffic behavior through the CNI.

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

kubectl get networkpolicy test-policy -n upgrade-test -o jsonpath='{.spec.podSelector.matchLabels.app}{"\n"}'
# Expect: security-test (policy selects the rehearsal pod)
```

Finally, clean up the testing environment. The cleanup should remove both cluster objects and local evidence files that are no longer needed.

```bash
echo "=== Cleanup ==="
kubectl delete namespace upgrade-test
rm -f /tmp/pre-upgrade-backup.yaml

echo ""
echo "=== Exercise Complete ==="
echo "Key upgrade security checks performed:"
echo "1. Backed up cluster state"
echo "2. Checked versions for consistency"
echo "3. Verified no deprecated APIs in use"
echo "4. Confirmed RBAC working"
echo "5. Validated security contexts"
echo "6. Verified NetworkPolicy support"
```

<details><summary>Solution guide for tasks 2 through 5</summary>
For the audit task, save the output of `kubectl version`, node kubelet versions, control-plane image versions, and the deprecated API check. For the preflight task, write the target version, backup location, expected temporary skew, and rollback trigger in one short note. For the diagnosis task, compare RBAC, security context, pod status, NetworkPolicy acceptance, and benchmark findings against the expected result. For the managed-cluster task, state which items the provider owns, which node and add-on work you own, and which checks prove the full cluster is actually patched.
</details>

Success criteria:

- [ ] The rehearsal namespace and pod were created successfully.
- [ ] The pre-upgrade workload backup was written to `/tmp/pre-upgrade-backup.yaml`.
- [ ] Cluster and node versions were captured and reviewed against the simulated target.
- [ ] Deprecated API evidence was checked before the upgrade decision.
- [ ] RBAC, security context, pod status, benchmark placeholder, and NetworkPolicy checks were completed.
- [ ] The namespace and temporary backup file were cleaned up.

## Sources

- https://kubernetes.io/releases/patch-releases/
- https://kubernetes.io/releases/version-skew-policy/
- https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/
- https://kubernetes.io/docs/reference/issues-security/security/
- https://github.com/kubernetes/kubernetes/security/advisories
- https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/
- https://kubernetes.io/docs/reference/using-api/deprecation-guide/
- https://kubernetes.io/docs/concepts/security/pod-security-admission/
- https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/
- https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- https://kubernetes.io/docs/concepts/services-networking/network-policies/
- https://github.com/aquasecurity/kube-bench
- https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
- https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html
- https://cloud.google.com/kubernetes-engine/docs/concepts/release-channels
- https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions

## Next Module

[Module 2.5: Restricting API Access](../module-2.5-restricting-api-access/) - Network and authentication restrictions for the API server.
