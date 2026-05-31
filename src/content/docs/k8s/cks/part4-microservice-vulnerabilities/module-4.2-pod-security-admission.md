---
title: "Module 4.2: Pod Security Admission (PSA)"
slug: k8s/cks/part4-microservice-vulnerabilities/module-4.2-pod-security-admission
sidebar:
  order: 2
lab:
  id: cks-4.2-pod-security-admission
  url: https://killercoda.com/kubedojo/scenario/cks-4.2-pod-security-admission
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 4.1 (Security Contexts), namespace basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** Pod Security Admission namespace labels with enforce, audit, warn, and version pinning for Kubernetes 1.35+ clusters.
2. **Compare** the privileged, baseline, and restricted Pod Security Standards and choose the right profile for each workload class.
3. **Diagnose** PSA rejection messages and remediate pod specs with non-root execution, dropped capabilities, seccomp, and privilege-escalation controls.
4. **Design** a PSP-to-PSA migration strategy that uses namespace rollout, cluster-wide defaults, exemptions, and optional Kyverno or Gatekeeper policies.

---

## Why This Module Matters

Hypothetical scenario: a platform team is preparing a Kubernetes 1.35 upgrade for a cluster that still carries the habits of the PodSecurityPolicy era. Most application namespaces run ordinary web services, a few observability namespaces run node agents, and several development namespaces contain old debugging pods that nobody has reviewed in months. The upgrade itself is not the scary part. The real risk is discovering too late that the cluster has no consistent admission boundary between an ordinary deployment and a pod that asks for host namespaces, broad Linux capabilities, or root execution.

Pod Security Admission solves a narrower problem than many people expect, and that narrowness is its strength. It does not try to become a full policy language, mutate workloads, validate images, or enforce business-specific naming rules. It applies the upstream Pod Security Standards at admission time, usually through namespace labels, so teams can block or observe pod specs that violate the privileged, baseline, or restricted profile. That makes PSA easy to reason about during the CKS exam and dependable enough to become the first layer of production workload hardening.

The operational skill is not memorizing one perfect manifest. The operational skill is reading a rejection message, mapping it back to the exact pod field that violated a profile, deciding whether the namespace should be baseline or restricted, and knowing when PSA is not expressive enough. This module walks through that judgment from the history of PSP, through the profile mechanics, into migration and cluster-wide configuration, then finishes with exam-style diagnosis and a lab that exercises the whole admission flow.

---

## From PodSecurityPolicy to Pod Security Admission

PodSecurityPolicy was Kubernetes' first built-in answer to unsafe pod specs, but it had two properties that made it difficult to operate at scale. It was selected through RBAC, so the effective policy for a pod depended on which user or service account created it, not just where the pod lived. It also included mutating behavior, which meant a request could be changed by admission rather than being accepted or rejected exactly as submitted. Those choices were powerful, but they made debugging surprising when several roles, controllers, and policy objects interacted.

The Kubernetes project deprecated PSP in v1.21 and removed it in v1.25, replacing the built-in pod-security path with the Pod Security Admission controller and the Pod Security Standards. The replacement deliberately changed the shape of the feature. PSA is namespace-oriented, profile-oriented, and validation-oriented. It asks, "does this pod comply with the selected standard for this namespace and mode?" rather than "which RBAC-selected policy should this creator be allowed to use, and should any defaults be injected?"

That distinction matters during migration because PSA is not a drop-in PSP clone. A PSP could express controls that the Pod Security Standards do not cover, and it could default fields that an application team forgot to set. PSA expects the workload spec to be explicit enough to pass validation. If an old PSP used mutation to set seccomp defaults or drop capabilities automatically, a PSA migration must move those settings into manifests, Helm charts, Kustomize patches, or a separate mutating policy engine before enforcement is enabled.

Think of PSP as a configurable inspection booth with many local rules and a few automatic corrections. Think of PSA as a standardized traffic signal at every namespace boundary. The signal is easier to interpret and easier to roll out consistently, but it only has three colors: privileged, baseline, and restricted. When the organization needs rules that do not fit those colors, PSA should stay in place for the universal floor while Kyverno, OPA Gatekeeper, image verification, or CI checks handle the specialized controls.

```text
┌──────────────────────────┐       ┌──────────────────────────┐
│ PodSecurityPolicy         │       │ Pod Security Admission    │
├──────────────────────────┤       ├──────────────────────────┤
│ RBAC selects policy       │       │ Namespace selects profile │
│ Could mutate pod fields   │       │ Validates only            │
│ Many custom restrictions  │       │ Three upstream profiles   │
│ Deprecated in v1.21       │       │ Stable since v1.25        │
│ Removed in v1.25          │       │ Enabled by default        │
└──────────────────────────┘       └──────────────────────────┘
```

The CKS exam usually tests the new model, not historical PSP authoring. You may still see a migration scenario where an existing workload fails after a namespace moves to restricted, or where a cluster needs a cluster-wide AdmissionConfiguration file because namespace labels alone cannot establish the desired default. In those tasks, the fastest path is to identify the profile and mode, inspect the violating pod fields, and make the smallest manifest change that satisfies the standard without granting new privilege.

Pause and predict: if a PSP previously defaulted `allowPrivilegeEscalation: false` but the application manifests never declared that field, what happens when the namespace switches to `enforce: restricted` under PSA? The important answer is that PSA will not fill in the missing value. The pod author must set the field explicitly, or another admission component must mutate the request before PSA validation sees it.

Migration planning begins with inventory, not labels. Review which namespaces contain ordinary applications, which contain node-level agents, which are system namespaces, and which development namespaces need temporary warning-only treatment. The first label change should usually be `audit: restricted` and `warn: restricted`, while `enforce` remains absent or set to baseline. That produces developer-facing warnings and audit annotations before the cluster starts rejecting pods that might still be owned by teams without a current maintainer.

The cost dimension is mostly operational rather than license-based because PSA ships with Kubernetes. Enabling audit and warn can still create work: audit logs grow, CI systems may surface more warnings, and platform engineers need time to triage violations. A moderate cluster with hundreds of namespaces can produce enough admission noise to matter if every controller repeatedly creates noncompliant pods. The practical cost control is a staged rollout with clear namespace ownership, pinned versions, and a short list of exemptions rather than one global switch flipped during an upgrade window.

---

## Pod Security Standards as Engineering Profiles

The Pod Security Standards are not random checklists. They describe three operating assumptions about workload trust. The privileged profile is intentionally unrestricted because some cluster components need host-level access. The baseline profile prevents common privilege-escalation paths while allowing broad compatibility with ordinary container images. The restricted profile aims at least privilege for application workloads and expects the pod author to be explicit about identity, capabilities, seccomp, volume types, and privilege escalation.

The useful comparison is not "which profile is more secure?" because restricted always wins that narrow question. The useful comparison is "which workloads can honestly run under this profile without either breaking or hiding exceptions?" A CNI DaemonSet that configures node networking may need privileged behavior and host access, so forcing it into restricted would create a fake sense of policy discipline. A web API that listens on port 8080 and writes only to a declared cache directory should be able to pass restricted, so leaving it at baseline misses an easy reduction in blast radius.

| Control area | Privileged | Baseline | Restricted |
|---|---|---|---|
| Privileged containers | Allowed | Disallowed | Disallowed |
| Host namespaces | Allowed | Disallowed for hostPID, hostIPC, and hostNetwork | Disallowed |
| HostPath volumes | Allowed | Disallowed | Disallowed |
| Linux capabilities | Unrestricted | Blocks dangerous additions beyond the baseline allowlist | Must drop `ALL`; only `NET_BIND_SERVICE` may be added |
| Running as root | Allowed | Allowed | Must not run as UID 0; `runAsNonRoot` and nonzero user settings matter |
| Privilege escalation | Allowed | Not comprehensively blocked | Must set `allowPrivilegeEscalation: false` for Linux containers |
| Seccomp | Unrestricted | Must not explicitly use `Unconfined` | Must explicitly use `RuntimeDefault` or `Localhost` |
| Volume types | Unrestricted | Broadly compatible except for `hostPath` | Limited to safe volume sources such as ConfigMap, Secret, PVC, projected, downwardAPI, CSI, emptyDir, and ephemeral |

Baseline is the profile you use when you need compatibility but still want to stop obviously risky pod specs. It blocks privileged containers, host namespaces, and HostPath volumes, restricts host ports and dangerous capability additions, and prevents several direct escapes from the container boundary. It does not require non-root execution, does not require dropping all capabilities, and does not require read-only root filesystems. That makes baseline a reasonable default for development namespaces or legacy application namespaces during the first migration phase.

Restricted is the profile you use when application teams can own their manifests and images. It requires the pod spec to close the usual privilege paths: no privilege escalation, no broad capability set, no root execution, and an explicit seccomp profile. Baseline also forbids HostPath volumes; restricted inherits that baseline rule and then narrows the remaining allowed volume sources. Restricted still does not enforce every hardening control a security team may want. For example, it does not require `readOnlyRootFilesystem`, resource limits, signed images, network policies, or approved registries.

The last point is a frequent exam trap. `readOnlyRootFilesystem: true` is a strong application hardening choice, and many organizations require it for production services, but it is not required by the upstream restricted Pod Security Standard. If a question asks for PSA compliance only, focus on the fields PSA actually checks. If a question asks for a hardened workload beyond PSA, then adding a read-only root filesystem and explicit writable volumes is a sensible extra defense.

Here is a compact restricted pod that satisfies the PSA fields most often tested in CKS-style tasks. The image is `busybox:1.36` and the command sleeps, so the pod does not need a writable root filesystem or a privileged port. The security settings are split between pod-level identity and container-level process controls because that mirrors how real manifests are commonly structured.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-ok
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "sleep 3600"]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
```

Several fields in that manifest are doing admission work rather than runtime decoration. `runAsNonRoot: true` tells Kubernetes the process must not start as root, while `runAsUser: 1000` removes ambiguity for images whose default user might otherwise be unknown. `allowPrivilegeEscalation: false` prevents setuid-style privilege gains for Linux containers. `capabilities.drop: ["ALL"]` removes the default Linux capability set, and `seccompProfile.type: RuntimeDefault` tells the runtime to apply its default syscall filter instead of leaving seccomp unset.

A noncompliant version helps you read rejection messages faster. This pod asks for privileged mode, host networking, UID 0, added capabilities, and no seccomp profile. Under `enforce: baseline`, privileged mode, host networking, and the capability addition are already enough to reject the request. Under `enforce: restricted`, the root user, missing `allowPrivilegeEscalation: false`, missing `drop: ["ALL"]`, and missing seccomp profile will also appear in the violation list.

Logical representation:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-fail
spec:
  hostNetwork: true
  containers:
  - name: app
    image: nginx:1.27-alpine
    securityContext:
      privileged: true
      runAsUser: 0
      capabilities:
        add: ["NET_ADMIN"]
```

This is an intentionally noncompliant example, not a lab step. The YAML is syntactically valid in a permissive namespace; each line references the field path where the relevant policy applies (e.g., `privileged` lives in `spec.containers[].securityContext.privileged`).

Before running this, what output do you expect if the namespace has `enforce: baseline`, `warn: restricted`, and `audit: restricted`? The pod should be rejected because it violates the enforced baseline profile, so the warning mode is not the reason it fails. If you remove the baseline violations but leave restricted-only gaps, the pod can be admitted while the API server warns the caller and records audit annotations for the restricted profile.

The standards also apply to workload resources that create pod templates, but enforcement ultimately blocks the pod creation request. That means a Deployment can be accepted in some workflows while its ReplicaSet repeatedly fails to create pods, depending on the admission path and object version being evaluated. During an exam, check both the controller object and the pod events. A rejected pod may show up as a ReplicaSet event even though the `kubectl apply` command that created the Deployment looked successful.

When you compare profiles in production, keep exceptions close to the workload type instead of the team name. A namespace for node agents may need privileged controls because the workload class demands it. A namespace for ordinary APIs should not stay privileged because the owning team is busy. This framing reduces political drift: the exception is attached to a technical requirement, and the namespace labels can be tightened when that requirement disappears.

There are a few less-visible checks that separate a good PSA answer from a memorized template. Restricted narrows allowed sysctls to safe names, limits SELinux types, blocks `procMount: Unmasked`, and prevents AppArmor from being explicitly unconfined where that field applies. Baseline also blocks several unsafe knobs that are not obvious from the common `privileged` and `hostNetwork` examples. When a rejection message names one of these fields, resist the urge to replace the whole pod. Read the named field, remove the unsafe value, and keep the rest of the workload spec stable.

Windows workloads add another reason to read the actual message. In modern Kubernetes, pod OS information lets Pod Security Standards distinguish Linux-only controls from Windows pods. Fields such as Linux capabilities, seccomp, and privilege escalation are meaningful for Linux containers; they are not the same mechanism for Windows containers. CKS tasks usually use Linux examples, but production clusters with mixed operating systems should pin policy versions and test both workload classes before declaring a namespace ready for restricted enforcement.

Ephemeral containers are also part of the mental model. Debug containers can be added after a pod is running, and they still pass through admission. A namespace that enforces restricted should not allow a later debug action to smuggle privileged settings into a pod that originally passed policy. This matters operationally because incident response often happens under stress. If a team needs privileged debugging, provide a controlled privileged namespace or break-glass workflow rather than weakening the policy for every application pod.

The standards intentionally avoid application-level promises. A pod can pass restricted while still running a vulnerable web framework, accepting traffic from every namespace, using an unsigned image, or writing sensitive data to logs. That is not a PSA failure; it is a boundary definition. PSA answers the pod-spec privilege question. NetworkPolicy, image admission, runtime detection, secret management, and application security controls answer different questions that sit around the pod-security floor.

---

## PSA Modes, Namespace Labels, and Rejection Diagnosis

Pod Security Admission has three modes, and each mode answers a different operational question. `enforce` asks whether the API server should reject the pod. `warn` asks whether the API server should allow the pod but return warnings to the client. `audit` asks whether the API server should annotate the audit event so security teams can search for violations later. The modes are independent, so a namespace can enforce baseline while warning and auditing restricted at the same time.

That mixed-mode pattern is the normal rollout path. Enforcing baseline blocks the most dangerous pod specs early, while warn and audit against restricted create a report of what still needs work. Developers see warnings in `kubectl` and other clients that surface server warnings. Cluster operators see audit annotations only if audit logging is configured for the API server and retained somewhere useful. PSA itself does not create a separate dashboard, so the log surface depends on the cluster's audit and observability design.

Namespace labels follow a fixed shape. The mode label selects the profile, and the optional version label selects the Kubernetes policy version. `latest` follows the API server's current version, which is convenient in a lab but can surprise production teams during upgrades. A pinned version such as `v1.35` makes the policy behavior stable until the platform team deliberately changes the label. For production namespaces, pin during rollout and move pins as part of the upgrade plan.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: payments-prod
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/enforce-version: v1.35
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.35
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.35
```

The same labels can be applied imperatively when you are working quickly in an exam environment. Use `--overwrite` because namespaces often already carry one or more PSA labels, and a failed label command wastes time. If you are changing an existing namespace to a stricter `enforce` level, use a dry-run first so the API server reports existing pods that would violate the new level.

```bash
kubectl label namespace payments-prod \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/warn-version=v1.35 \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/audit-version=v1.35 \
  --overwrite

kubectl label namespace payments-prod \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  --dry-run=server \
  --overwrite
```

The error format is one of the most valuable clues PSA gives you. A typical rejection starts with `Error from server (Forbidden)`, names the pod or resource, identifies the violated profile and version, then lists field-level reasons. Do not treat that message as a wall of text. Split it into three questions: which profile rejected the request, which container or init container is named, and which field value must be changed.

```text
Error from server (Forbidden): error when creating "pod.yaml":
pods "restricted-fail" is forbidden: violates PodSecurity "restricted:v1.35":
allowPrivilegeEscalation != false (container "app" must set
securityContext.allowPrivilegeEscalation=false), unrestricted capabilities
(container "app" must set securityContext.capabilities.drop=["ALL"]),
runAsNonRoot != true (pod or container "app" must set
securityContext.runAsNonRoot=true), seccompProfile (pod or container "app"
must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
```

That message is almost a remediation checklist. Add or move the missing security fields at the pod or container level, then retry the apply. If the message names an init container or ephemeral container, fix that container too. Restricted checks apply across containers, init containers, and ephemeral containers where the field is relevant. A Deployment with one hardened app container and one forgotten init container can still fail admission.

The following manifest fixes the rejection without adding unrelated hardening controls. Notice that it does not add `readOnlyRootFilesystem` because the PSA error did not ask for it. In a production hardening story you might add that later, but in an exam remediation you should satisfy the policy quickly and avoid introducing startup failures that are not part of the question.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-fixed
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 101  # UID for the nginx user in nginx:1.27-alpine
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:1.27-alpine
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
```

Note: the default nginx startup path assumes root-oriented ports and writable paths, so this pod passes PSA admission but may CrashLoopBackOff at runtime — PSA admission and runtime health are independent concerns, covered later in this module.

Warnings look similar, but they do not stop the request. When a namespace has `warn: restricted`, `kubectl apply` may print lines beginning with `Warning:` that name the profile and the violating fields. Those warnings are easy to ignore during a busy rollout, which is why warn mode should feed a ticket, report, or CI quality gate. A warning-only rollout that nobody reads is just delayed enforcement without a repair plan.

Audit mode is different because the feedback is not returned to the developer. PSA adds audit annotations to the API audit event for the request, and those annotations can be queried by whatever log pipeline receives API server audit logs. This is useful for migration because it captures controller traffic as well as human `kubectl` traffic. It is also the mode most likely to create unexpected log volume when a controller repeatedly retries a noncompliant pod template.

```bash
kubectl get namespace payments-prod --show-labels

kubectl describe namespace payments-prod

kubectl get events -n payments-prod --sort-by=.lastTimestamp
```

Those commands do not replace reading the rejection message, but they orient you quickly. `get namespace --show-labels` confirms the active modes and versions. `describe namespace` is convenient when labels wrap awkwardly in a terminal. Events help when a controller rather than a human created the failing pod. On the CKS exam, this small sequence often reveals whether you are fixing the namespace policy, the workload spec, or a controller template.

There is one more subtle interaction: the namespace label controls new admissions, not a retroactive rewrite of existing pods. Existing pods continue running after you tighten a namespace label, although future recreations may fail. That is why a deployment can look healthy until a rollout, node drain, or autoscaler replacement forces new pods through admission. A safe production rollout checks current pod templates before enforcement and rehearses at least one restart for critical workloads.

---

## Migration Scenario: Two Hundred Namespaces Without a Freeze

Hypothetical scenario: a cluster has two hundred namespaces, about thirty shared platform namespaces, and a long tail of application namespaces owned by separate teams. The old PSP setup allowed most application service accounts to use a restrictive policy, but a few service accounts had access to a broader policy for migrations and debugging. The platform team has four business days before the next control-plane upgrade rehearsal, so the goal is not to make every workload perfect. The goal is to remove PSP dependency, set a predictable PSA floor, and create a queue of restricted-profile fixes that teams can finish without blocking the upgrade.

Hour zero starts with discovery. Export namespace labels, list pods with host namespace fields, find privileged containers, and identify obvious DaemonSets that cannot be restricted. The team does not enforce anything yet because the inventory itself can reveal stale namespaces, abandoned controllers, and false assumptions about which workloads still exist. The most useful spreadsheet columns are namespace owner, workload class, proposed enforce profile, proposed warn profile, violations seen, and exception owner.

```bash
kubectl get namespaces --show-labels

kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.hostNetwork}{"\t"}{.spec.hostPID}{"\t"}{.spec.hostIPC}{"\n"}{end}'

kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{":"}{.securityContext.privileged}{" "}{end}{"\n"}{end}'
```

Day one is audit and warn. The team labels application namespaces with `audit: restricted` and `warn: restricted`, then labels obvious node-agent namespaces with `enforce: privileged` only when the workload class truly needs it. For ordinary application namespaces, `enforce: baseline` is a good first safety net because it blocks privileged containers, host namespaces, and HostPath volumes while leaving root-running legacy images enough room to keep serving traffic. The team pins labels to `v1.35` so policy behavior is not silently changed by the next control-plane upgrade.

Day two is remediation of the noisy failures. The top causes are usually missing `allowPrivilegeEscalation: false`, missing `capabilities.drop: ["ALL"]`, missing seccomp profile, and containers that run as UID 0. These are not all equal in difficulty. Adding seccomp and dropping capabilities is often a Helm values change. Moving away from root may require image rebuilds, file-permission fixes, or volume mount changes. That difference drives the rollout order: fix manifest-only gaps first, schedule image rebuilds second, and document real exceptions third.

Day three is enforcement rehearsal. The platform team uses server-side dry-run label changes and controlled restarts for representative deployments. This catches the failure mode where a namespace appears clean because old pods are still running, but the next ReplicaSet cannot create replacements. Any namespace that fails rehearsal stays at `enforce: baseline` with restricted warn and audit. Any namespace that passes moves to `enforce: restricted`, still pinned to `v1.35`, with an owner recorded for future upgrades.

Day four is cleanup and communication. PSP manifests are removed from Git only after the team confirms no component still depends on them, and the platform runbook changes from "which PSP grants this service account permission?" to "which PSA labels apply to this namespace?" The team also decides which gaps need a policy engine. For example, PSA can require restricted pod fields, but it cannot require images from an internal registry or block `latest` tags. Those controls move to Kyverno or Gatekeeper rather than being squeezed into PSA.

The concrete timeline matters because it prevents two common failures. The first failure is enforcing restricted everywhere before application teams have seen warnings, which turns policy migration into an outage. The second failure is leaving everything in audit forever, which creates a permanent report with no security boundary. A four-day migration does not complete every hardening task, but it establishes a defensible floor and a visible queue for the remaining work.

For CKS purposes, the migration mental model is smaller. If a namespace is too loose, add or tighten labels. If a pod violates a profile, fix the pod spec. If a cluster needs defaults or exemptions that should apply even when labels are absent, use AdmissionConfiguration. If a requirement is custom, such as "only allow images from this registry" or "require a team label on every pod," choose Kyverno or Gatekeeper because PSA has no field for that policy.

---

## Cluster-Wide Configuration and Exemptions

Namespace labels are the normal interface for PSA because they make policy visible where workloads live. Cluster-wide AdmissionConfiguration is the interface for defaults and exemptions. The kube-apiserver loads it through `--admission-control-config-file`, and the file can set default profiles for namespaces without labels, define what happens when a version label is absent, and exempt specific usernames, runtime classes, or namespaces. This is not a replacement for namespace labels; it is the cluster baseline underneath them.

Use cluster-wide configuration when absence of labels should still mean something. A security team may want unlabeled namespaces to enforce baseline by default, warn restricted by default, and audit restricted by default. That avoids the dangerous gap where a newly created namespace has no PSA labels because someone forgot a template. Namespace labels can still override the default when a workload class needs a different profile.

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: PodSecurity
  configuration:
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: baseline
      enforce-version: v1.35
      audit: restricted
      audit-version: v1.35
      warn: restricted
      warn-version: v1.35
    exemptions:
      runtimeClasses:
      - privileged-runtime
      namespaces:
      - kube-system
```

The kube-apiserver flag is operationally important because a bad path or invalid file can affect API server startup. In a managed cluster you may not have direct access to this configuration, so the practical tool may be namespace labels plus provider defaults. In a self-managed cluster or an exam environment that exposes control-plane static pod manifests, you need to know that the admission config file is referenced by the API server, not applied with `kubectl apply` like a normal Kubernetes object.

```bash
kube-apiserver \
  --admission-control-config-file=/etc/kubernetes/admission/admission.yaml
```

Exemptions should be rare and boring. Exempting `kube-system` is common because system components and node agents may need privileges that application workloads should never copy. Exempting a runtime class can be appropriate when a sandboxed or special runtime has a different security model. Exempting usernames is powerful but dangerous because it follows the actor, not the workload. If a broad automation identity is exempt, every namespace that identity can create pods in may bypass PSA.

The version fields in AdmissionConfiguration have the same production tradeoff as namespace label versions. `latest` reduces maintenance but couples policy behavior to upgrades. A pinned version supports controlled change management, especially when a cluster upgrade and a security-profile upgrade are separate workstreams. For Kubernetes 1.35-oriented curriculum and production examples, pinning `v1.35` makes the lesson and the rollout deterministic.

Pinning should be consistent across modes, not only on the enforced label. If `enforce-version` is pinned but `warn-version` is left to default behavior, the cluster may enforce one policy version while warning against another after an upgrade. That can produce confusing migration reports because developers see warnings that do not match the current enforcement boundary. In production runbooks, treat the six namespace labels as a documented unit: three mode labels and three version labels, reviewed together during cluster upgrades.

In the exam, do not overuse cluster-wide configuration. If the task says "configure namespace `secure` to enforce restricted," labels are the direct answer. If the task says "set default pod security behavior for unlabeled namespaces" or shows an API server admission config file, then AdmissionConfiguration with a nested PodSecurityConfiguration is in scope. The fastest diagnostic cue is whether the requested policy is namespace-specific or should apply before a namespace owner adds any labels.

---

## CKS Exam Workflow for PSA Tasks

PSA exam tasks reward sequence more than memorization. Start by identifying the namespace, then identify the active labels, then inspect the pod or controller template that admission will evaluate. Many wrong answers come from fixing a standalone pod YAML while the real workload is a Deployment template, or from changing `warn` labels when the rejection came from `enforce`. A disciplined workflow keeps you from changing the wrong layer under time pressure.

The first command is usually a namespace read. You need to know all three modes and all relevant versions because mixed-mode configuration is common. If a namespace enforces baseline and warns restricted, a restricted warning is not a rejection. If a namespace enforces restricted with no version label, the next question is whether the task expects you to pin the version for deterministic behavior. Read labels before editing pods because the labels explain which standard is judging the request.

```bash
kubectl get namespace secure-ns --show-labels
kubectl describe namespace secure-ns
```

The second step is to decide whether the request is a direct pod or a controller-managed pod. A forbidden message that names `pods "api-7cfd..."` may still point back to a Deployment, ReplicaSet, Job, or CronJob template. Editing a live rejected pod is usually impossible because the pod was never stored. Fix the template that will create the next pod. On the exam, use `kubectl get deploy -n secure-ns -o yaml` or the specific controller name shown in events, then patch or edit the template fields.

```bash
kubectl get events -n secure-ns --sort-by=.lastTimestamp
kubectl get deployment -n secure-ns
kubectl get deployment api -n secure-ns -o yaml
```

The third step is to translate the PSA message into a manifest diff. If the message says `allowPrivilegeEscalation != false`, set `allowPrivilegeEscalation: false` on the named container. If it says `unrestricted capabilities`, add `capabilities.drop: ["ALL"]`. If it says `seccompProfile`, add `seccompProfile.type: RuntimeDefault` at pod or container level. If it says `runAsNonRoot != true`, set `runAsNonRoot: true` and remove any explicit UID 0. Do not change the namespace to a weaker profile unless the task explicitly asks for an exception.

The fourth step is to think about scope. Some fields are naturally pod-level defaults, and some fields are container-level controls. A pod-level `seccompProfile` and `runAsNonRoot` can cover every container unless a container overrides them. `allowPrivilegeEscalation` and capabilities belong to individual containers. When a pod has app, sidecar, and init containers, scan every container list. The fastest fix is often a repeated container `securityContext` block, not a single pod-level field that PSA does not use for that control.

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
  initContainers:
  - name: init
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
```

Pause and classify: if a question asks you to "make the pod pass restricted" and the pod currently has `hostPath`, `privileged: true`, UID 0, and missing seccomp, which fixes are mandatory for PSA and which are separate production hardening choices? Mandatory PSA fixes include removing privileged mode, removing `hostPath` because baseline and restricted both forbid it, ensuring non-root execution, setting seccomp, blocking privilege escalation, and dropping capabilities. Separate hardening choices might include read-only root filesystems, approved image registries, or NetworkPolicy.

The fifth step is to validate with server-side dry-run when the cluster allows it. Dry-run sends the request through admission without storing the object, which is exactly the behavior you need when testing a policy fix. It also avoids leaving failed experiment objects in the namespace. If dry-run is unavailable for the object or environment, use a temporary namespace with equivalent labels and delete the object immediately after testing.

```bash
kubectl apply -n secure-ns --dry-run=server -f fixed-pod.yaml
kubectl diff -n secure-ns -f fixed-deployment.yaml
kubectl apply -n secure-ns -f fixed-deployment.yaml
```

The sixth step is to verify that the controller actually creates a pod. Admission success for the updated Deployment object is not enough if the template still has a hidden violation or the application cannot start with the new identity. Watch the ReplicaSet events and pod status after applying the fix. A pod that passes PSA can still fail at runtime because a non-root user cannot write to an image path. That runtime failure is different from admission failure and should be debugged as a security-context or filesystem problem.

The final step is to leave policy intent visible. If you add labels, confirm the final namespace labels. If you fix a workload, confirm the template contains the security fields, not just a one-off pod. If you use an exemption, be prepared to explain why labels were not enough. CKS grading often checks the final cluster state rather than your command history, so end by reading the object that the grader is likely to inspect.

---

## Patterns & Anti-Patterns

The strongest PSA pattern is a staged namespace rollout: audit first, warn second, enforce last. This is not bureaucracy. It matches the fact that admission policy is evaluated when pods are created, while many production pods may have been running for weeks. Audit and warn reveal what will fail on the next rollout, and enforcement turns the known clean state into a real boundary once the repair work is complete.

| Pattern | When to Use | Why It Works |
|---|---|---|
| `enforce: baseline`, `warn/audit: restricted` | Legacy application namespaces moving toward least privilege | Blocks obvious high-risk specs while creating a restricted remediation queue |
| `enforce: restricted` with pinned version | Production services with owned manifests and compatible images | Makes least-privilege requirements predictable across upgrades |
| Privileged only for workload-class namespaces | CNI, CSI, node monitoring, or controlled break-glass tooling | Keeps necessary host access away from ordinary application namespaces |
| Cluster defaults plus namespace overrides | Platform teams that need safe behavior for new namespaces | Prevents unlabeled namespaces from becoming policy gaps |

Anti-patterns usually come from treating PSA as either too weak or too magical. It is too weak to be the only policy layer for image provenance, network segmentation, or custom business rules. It is also not magical enough to fix manifests that used to rely on PSP mutation. Teams get into trouble when they enable restricted enforcement before the workload specs actually contain the fields restricted requires.

| Anti-Pattern | Why It Happens | Better Alternative |
|---|---|---|
| Enforcing restricted on `kube-system` without inventory | The team wants a simple "secure everywhere" rule | Exempt system namespaces or classify node agents separately |
| Using `latest` on every production label | It feels future-proof and avoids version bookkeeping | Pin versions during rollout, then update pins intentionally after upgrade testing |
| Assuming warnings are enough | Developers see warnings but no owner tracks them | Route audit and warn findings into remediation work with namespace ownership |
| Adding Kyverno or Gatekeeper before PSA | The platform team wants one policy framework for everything | Use PSA for the upstream pod-security floor, then add custom policy where needed |

The balance is pragmatic. PSA should be the first admission layer for pod privilege because it is upstream, enabled by default, and aligned with the standards Kubernetes documents. It should not become an excuse to ignore workload design. A pod that passes restricted can still be vulnerable because it uses a risky image, exposes an unnecessary service, has no NetworkPolicy, or runs an application with a severe bug. Admission is a guardrail, not a complete security program.

---

## Decision Framework

Choose PSA alone when the question is about the upstream Pod Security Standards and the policy boundary is the namespace. A namespace full of ordinary web services can usually enforce restricted after the image and manifest gaps are fixed. A legacy namespace can enforce baseline while warning restricted. A node-agent namespace can be privileged with a clear owner and a documented reason. These decisions are simple enough to express with labels, and simple policies are easier to audit under exam pressure and production stress.

Choose AdmissionConfiguration when the cluster needs default behavior or centrally managed exemptions. The key phrase is "before labels exist." If newly created namespaces should start at baseline automatically, namespace labels alone are reactive because they must be added after namespace creation. If `kube-system` or a special runtime class must be exempt, the cluster-wide config gives the API server a consistent exception list rather than requiring every namespace owner to remember special label combinations.

Choose Kyverno or OPA Gatekeeper when the rule is not part of the Pod Security Standards. Concrete examples include requiring images from `registry.example.com`, blocking mutable image tags, requiring a business owner label, limiting host ports to an approved range, or allowing a capability only for pods with a specific service account and label. Kyverno is often attractive when teams want policy-as-YAML and optional mutation. Gatekeeper is often attractive when teams already use Open Policy Agent and Rego constraints across multiple platforms.

| Requirement | PSA Labels | AdmissionConfiguration | Kyverno or Gatekeeper |
|---|---|---|---|
| Enforce restricted in one namespace | Best fit | Not needed | Not needed |
| Warn on restricted violations during migration | Best fit | Useful as a default | Optional reporting layer |
| Default unlabeled namespaces to baseline | Not sufficient alone | Best fit | Possible but heavier |
| Exempt `kube-system` or a runtime class | Not sufficient alone | Best fit | Possible but less direct |
| Require approved image registry | Not supported | Not supported | Best fit |
| Mutate missing security context fields | Not supported | Not supported | Kyverno or another mutating admission layer |

For the CKS exam, prefer the smallest tool that exactly matches the task. If the prompt mentions `pod-security.kubernetes.io/enforce`, use labels. If it shows a forbidden message naming `violates PodSecurity "restricted:v1.35"`, fix the manifest fields. If it mentions the API server admission config file, edit the PodSecurity configuration carefully. If it asks for policy that PSA cannot express, explain or implement a policy engine rule rather than pretending a PSA label can validate arbitrary fields.

---

## Did You Know?

- Kubernetes deprecated PodSecurityPolicy in v1.21 and removed it in v1.25, so modern CKS practice should focus on PSA rather than writing new PSP objects.
- PSA has three independent modes, which means one namespace can enforce baseline while simultaneously warning and auditing against restricted.
- `latest` in a PSA version label follows the API server's policy version, while a value such as `v1.35` pins the behavior for safer upgrade planning.
- The upstream restricted profile requires dropped capabilities and seccomp, but it does not require `readOnlyRootFilesystem`, even though many production hardening guides recommend it.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Enabling `enforce: restricted` before reading warnings | Teams want a fast migration and underestimate old pod templates | Start with `audit` and `warn`, repair the common violations, then enforce namespace by namespace |
| Treating PSA as a PSP clone | PSP could mutate fields and express controls outside the Pod Security Standards | Move defaults into manifests or a mutating policy engine, and use PSA for validation |
| Leaving version labels at `latest` in production | It is convenient in examples and labs | Pin to the cluster target such as `v1.35`, then update pins during upgrade rehearsals |
| Fixing only the main container | Rejection messages often name init or ephemeral containers too | Apply restricted fields to every container type that PSA evaluates |
| Expecting audit mode to warn developers | Audit annotations go to API audit logs, not the interactive client | Use `warn` for developer feedback and audit for centralized reporting |
| Adding `readOnlyRootFilesystem` to satisfy PSA | It is a good hardening control, so people assume restricted requires it | Add it when the workload can support it, but fix the actual PSA fields first |
| Exempting a broad automation username | It feels easier than classifying workload namespaces | Prefer namespace or runtimeClass exemptions, and keep username exemptions narrow and reviewed |

---

## Quiz

<details><summary>1. Your namespace enforces baseline and warns restricted. A pod uses `runAsUser: 0` but does not request host networking, privileged mode, or dangerous added capabilities. Should the pod be admitted, and what feedback should the developer see?</summary>

The pod should be admitted because baseline allows containers to run as root when no other baseline violation is present. The developer should see a warning if the restricted profile is configured in warn mode, because restricted does not allow root execution and expects non-root settings. This is the normal migration pattern: baseline enforcement blocks the most dangerous specs while restricted warnings identify the next hardening tasks.

</details>

<details><summary>2. A Deployment rollout starts failing after a namespace label changes to `pod-security.kubernetes.io/enforce: restricted`. The error mentions `allowPrivilegeEscalation != false` and `unrestricted capabilities`. Which pod-spec changes are the smallest likely fix?</summary>

Set `securityContext.allowPrivilegeEscalation: false` for each Linux container that lacks it, and set `securityContext.capabilities.drop: ["ALL"]` for the relevant containers. Do not add unrelated settings first, because the admission message already names the failed checks. After that, reapply or restart the controller so a new pod creation request goes through admission with the corrected template.

</details>

<details><summary>3. During a PSP migration, you discover old workloads passed because PSP defaulted seccomp settings. Under PSA restricted, the same manifests are rejected for missing `seccompProfile`. Why did this happen?</summary>

PSA validates the submitted pod; it does not mutate missing fields into compliance. PSP could include defaulting behavior, so workloads may have depended on policy mutation rather than declaring their own security context. The fix is to add `seccompProfile.type: RuntimeDefault` or `Localhost` to the pod or container spec, or use a separate mutating admission layer before relying on PSA enforcement.

</details>

<details><summary>4. Your platform team wants every new unlabeled namespace to enforce baseline, warn restricted, and exempt `kube-system`. Should you solve this with namespace labels only?</summary>

Namespace labels are not enough because the requirement applies before a namespace owner adds labels and includes a cluster-level exemption. Use the PodSecurity AdmissionConfiguration loaded by the kube-apiserver to set defaults and exemptions, then allow namespace labels to override the defaults when appropriate. In a managed cluster, check whether the provider exposes that configuration; otherwise, combine provider defaults with namespace automation.

</details>

<details><summary>5. A security team asks you to require images from an internal registry and also enforce restricted pod security fields. Which policy layer should own each part?</summary>

Use PSA for the restricted pod security fields because that is exactly what the upstream restricted profile is for. Use Kyverno, Gatekeeper, or another admission policy engine for the registry rule because PSA does not validate image registry prefixes. Keeping the responsibilities separate makes the universal pod-security floor easy to audit while leaving custom organizational rules in a policy language that can express them.

</details>

<details><summary>6. A namespace currently has `enforce: restricted` with no version label. The cluster is being upgraded, and the team wants deterministic policy behavior during the change. What should you do?</summary>

Add the matching `pod-security.kubernetes.io/enforce-version` label, such as `v1.35` for a Kubernetes 1.35 target, and do the same for warn and audit labels when they are present. Without version labels, the policy version follows default behavior that can change with the API server version. Pinning turns policy updates into an explicit rollout step rather than an accidental side effect of a cluster upgrade.

</details>

<details><summary>7. A ReplicaSet event says pod creation is forbidden because an init container violates restricted, but the main container already has all the expected security fields. Where do you look next?</summary>

Inspect `.spec.template.spec.initContainers` in the controller template and add the missing restricted fields to the init container. PSA checks init containers as well as regular containers for relevant controls, so a hardened main container does not make the whole pod compliant. After fixing the template, let the controller create a fresh pod and confirm the event no longer appears.

</details>

---

## Hands-On Exercise

This exercise uses a disposable namespace and ordinary `kubectl` operations. It is designed to make the admission flow visible without requiring control-plane file access. You will label a namespace, trigger baseline and restricted feedback, repair a pod, and inspect the labels that explain why each request behaved the way it did. If you are using the Killercoda lab, start from a clean terminal and avoid reusing namespace names from previous attempts.

### Task 1: Create a migration namespace with baseline enforcement

Create a namespace that enforces baseline while warning and auditing restricted. This mirrors the safest first phase of a real migration because high-risk pods are blocked, but restricted-only problems are visible before they become outages.

```bash
kubectl create namespace psa-lab

kubectl label namespace psa-lab \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/warn-version=v1.35 \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/audit-version=v1.35 \
  --overwrite

kubectl get namespace psa-lab --show-labels
```

<details><summary>Solution notes for task 1</summary>

The final command should show all six PSA labels. If a label command fails because the namespace already exists or a label already has a value, rerun it with `--overwrite`. The important design choice is enforcing baseline while observing restricted.

</details>

### Task 2: Confirm that baseline blocks privileged pods

Apply a pod that requests privileged mode. The pod should be rejected because privileged containers violate baseline, not merely restricted. Read the error message and identify the profile that blocked the request.

```bash
cat <<'EOF' | kubectl apply -n psa-lab -f -
apiVersion: v1
kind: Pod
metadata:
  name: privileged-demo
spec:
  containers:
  - name: app
    image: nginx:1.27-alpine
    securityContext:
      privileged: true
EOF
```

<details><summary>Solution notes for task 2</summary>

The request should fail with a forbidden error that names a PodSecurity baseline violation. If it succeeds, inspect the namespace labels because enforcement may be missing or set to privileged. Delete the pod afterward if it was admitted unexpectedly.

</details>

### Task 3: Trigger restricted warnings without blocking the pod

Create a pod that passes baseline but lacks restricted settings. The pod should run or at least be admitted, while the client prints warnings about restricted violations such as missing seccomp, missing dropped capabilities, and non-root requirements.

```bash
cat <<'EOF' | kubectl apply -n psa-lab -f -
apiVersion: v1
kind: Pod
metadata:
  name: baseline-pass
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "sleep 3600"]
EOF

kubectl get pod baseline-pass -n psa-lab
```

<details><summary>Solution notes for task 3</summary>

The namespace enforces baseline, so an ordinary BusyBox pod without host namespaces or privileged settings should be admitted. Restricted warnings are expected because the pod lacks explicit non-root, seccomp, privilege-escalation, and capabilities settings. Those warnings are the repair list for the next task.

</details>

### Task 4: Tighten enforcement with a server-side dry run

Before changing enforcement for real, ask the API server what would happen if the namespace enforced restricted. This is the habit that prevents existing but noncompliant pod templates from surprising you during a rollout.

```bash
kubectl label namespace psa-lab \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=v1.35 \
  --dry-run=server \
  --overwrite
```

<details><summary>Solution notes for task 4</summary>

The dry run should report warnings if existing pods in the namespace violate the proposed enforced level. Because this is a dry run, it should not change the namespace labels. Confirm with `kubectl get namespace psa-lab --show-labels` if you are unsure.

</details>

### Task 5: Create a restricted-compliant pod

Apply a pod that declares the fields restricted commonly requires. The goal is not to create a universal template, but to practice turning PSA messages into specific manifest fields.

```bash
cat <<'EOF' | kubectl apply -n psa-lab -f -
apiVersion: v1
kind: Pod
metadata:
  name: restricted-pass
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "sleep 3600"]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
EOF

kubectl get pod restricted-pass -n psa-lab
```

<details><summary>Solution notes for task 5</summary>

This pod should be admitted without restricted warnings related to the common fields in the manifest. If the image or runtime adds a different issue, read the warning or rejection message and fix the named field rather than changing the namespace policy. The important practice is field-level diagnosis.

</details>

### Task 6: Clean up and record what each mode did

Delete the namespace and write down one sentence for each PSA mode. This forces you to separate the admission decision from developer feedback and centralized audit visibility.

```bash
kubectl delete namespace psa-lab
```

<details><summary>Solution notes for task 6</summary>

`enforce` decided whether the pod was admitted. `warn` returned visible warnings to the client while allowing the request when enforcement passed. `audit` recorded policy violations in API audit annotations when audit logging was configured. Those three surfaces are separate, which is why production rollouts often use all three at once.

</details>

### Success Criteria

- [ ] You can explain why `privileged-demo` was rejected under baseline enforcement.
- [ ] You can explain why `baseline-pass` was admitted but warned under restricted warn mode.
- [ ] You can convert a restricted PSA warning into concrete pod `securityContext` fields.
- [ ] You can use server-side dry-run before tightening namespace enforcement.
- [ ] You can describe when namespace labels are enough and when AdmissionConfiguration is needed.
- [ ] You can state one example rule that requires Kyverno or Gatekeeper rather than PSA.

---

## Learner check

> Baseline also forbids HostPath volumes; restricted inherits that baseline rule and then narrows the remaining allowed volume sources.

Before moving on, confirm you can explain why a pod with `spec.volumes[].hostPath` fails in a namespace that enforces `baseline:v1.35`, even if it does not request privileged mode or host namespaces.

---

## Sources

- [Kubernetes: Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Kubernetes: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes: Enforce Pod Security Standards by configuring namespace labels](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/)
- [Kubernetes: Enforce Pod Security Standards with namespace labels and the built-in admission controller](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-admission-controller/)
- [Kubernetes Blog: Pod Security Admission Controller Stable in v1.25](https://kubernetes.io/blog/2022/08/25/pod-security-admission-stable/)
- [Kubernetes: PodSecurityPolicy deprecation](https://kubernetes.io/docs/concepts/policy/pod-security-policy/)
- [Kubernetes KEP 2579: Pod Security Admission](https://github.com/kubernetes/enhancements/tree/master/keps/sig-auth/2579-psp-replacement)
- [Kubernetes: Migrate from PodSecurityPolicy to the Built-In PodSecurity Admission Controller](https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/)
- [Kubernetes source: restricted runAsNonRoot check](https://github.com/kubernetes/kubernetes/blob/release-1.35/staging/src/k8s.io/pod-security-admission/policy/check_runAsNonRoot.go)
- [Kyverno policy library: Pod Security Standards](https://kyverno.io/policies/pod-security/)
- [OPA Gatekeeper policy library](https://open-policy-agent.github.io/gatekeeper-library/website/)

---

## Next Module

[Module 4.3: Secrets Management](../module-4.3-secrets-management/) - Securing Kubernetes secrets.
