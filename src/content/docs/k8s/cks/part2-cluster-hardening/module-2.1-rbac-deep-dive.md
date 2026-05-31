---
title: "Module 2.1: RBAC Deep Dive"
slug: k8s/cks/part2-cluster-hardening/module-2.1-rbac-deep-dive
sidebar:
  order: 1
revision_pending: false
lab:
  id: cks-2.1-rbac-deep-dive
  url: https://killercoda.com/kubedojo/scenario/cks-2.1-rbac-deep-dive
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core security skill
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: CKA RBAC knowledge, ServiceAccounts basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Audit** Kubernetes RBAC Roles, ClusterRoles, RoleBindings, ClusterRoleBindings, and ServiceAccounts to expose wildcard permissions, secret access, and privilege escalation paths.
2. **Implement** least-privilege Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings for workload requirements without granting unnecessary cluster-wide access.
3. **Trace** effective permissions for users and ServiceAccounts by following RoleBinding and ClusterRoleBinding relationships through the authorization chain.
4. **Diagnose** RBAC access denials and repair them with the smallest safe role or binding change rather than broad fallback permissions.

---

## Why This Module Matters

Hypothetical scenario: a deployment pipeline starts failing after a platform team removes `cluster-admin` from a CI ServiceAccount. The application team asks for the old binding back because releases are blocked, but the security review shows that the same token could also read every Secret, patch every ClusterRole, and delete workloads outside the application's namespace. A CKS-level engineer has to keep the release path working while proving which exact API operations the pipeline actually needs.

RBAC is where Kubernetes security becomes operationally concrete. Network policies, Pod Security Admission, and runtime hardening all matter, but the API server still decides whether a subject may create a pod, read a Secret, bind a role, or impersonate another user. When RBAC is too broad, the blast radius of one compromised container expands from a single namespace to the whole control plane; when RBAC is too narrow, real operators lose the ability to debug incidents safely.

This module rewrites the common "create a Role and RoleBinding" lesson into an audit workflow. You will learn how the authorizer assembles permissions, why some verbs are escalation-sensitive, how to compare a workload requirement against an existing role, and how to reduce access without breaking the workload you were asked to protect. The goal is not memorizing YAML fields; the goal is making defensible authorization decisions under exam and production pressure.

---

## RBAC Review: How Permissions Are Assembled

RBAC feels confusing until you separate the two halves of the model. A Role or ClusterRole answers "what actions are allowed," while a RoleBinding or ClusterRoleBinding answers "who receives those actions." That split is deliberate because it lets you reuse the same permission set for different subjects, but it also means you cannot judge risk by reading only one object. A harmless-looking Role becomes dangerous when it is bound to a broad group, and a harmless-looking ServiceAccount becomes dangerous when a ClusterRoleBinding points it at a powerful role.

```text
┌─────────────────────────────────────────────────────────────┐
│              RBAC COMPONENTS                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Role/ClusterRole                                          │
│  └── Defines WHAT actions are allowed                      │
│      ├── apiGroups: ["", "apps", "batch"]                  │
│      ├── resources: ["pods", "deployments"]                │
│      └── verbs: ["get", "list", "create", "delete"]        │
│                                                             │
│  RoleBinding/ClusterRoleBinding                            │
│  └── Defines WHO gets the permissions                      │
│      ├── subjects: [users, groups, serviceaccounts]        │
│      └── roleRef: [Role or ClusterRole]                    │
│                                                             │
│  Scope:                                                    │
│  ├── Role + RoleBinding = namespace-scoped                 │
│  ├── ClusterRole + ClusterRoleBinding = cluster-wide       │
│  └── ClusterRole + RoleBinding = reusable in namespace     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Scope is the second idea that must be automatic before you audit anything. A `Role` always lives inside one namespace, while a `ClusterRole` is cluster-scoped and can include either namespaced resources, cluster-scoped resources, or both. A `RoleBinding` always grants permissions inside one namespace, even when it references a `ClusterRole`; a `ClusterRoleBinding` grants the referenced `ClusterRole` at cluster scope. That last distinction is where many over-permissioned clusters are born.

Think of a `ClusterRole` as a reusable key blank and a binding as the door where the key gets installed. A `ClusterRole` named `pod-reader` can be safe when installed through a `RoleBinding` in one namespace, because it opens only that namespace's pod-read door. The same `ClusterRole` installed through a `ClusterRoleBinding` opens pod-read doors across the cluster, including namespaces that the original requester may never have mentioned.

The API group field is also easy to underestimate. Core resources such as Pods, Secrets, ConfigMaps, and ServiceAccounts use the empty API group `""`, while Deployments use `apps`, Jobs use `batch`, and RBAC objects use `rbac.authorization.k8s.io`. If a role grants `resources: ["*"]` across `apiGroups: ["*"]`, it does not merely cover the resources you had in mind today. It also covers future APIs and installed custom resources that match the wildcard.

Verbs are not all equal. `get`, `list`, and `watch` are read-oriented, but `list` on Secrets can expose many secret values at once. `create`, `update`, `patch`, and `delete` change cluster state, but `create pods` is more sensitive than it first appears because a new pod can run under a chosen ServiceAccount and request dangerous security context settings unless other controls stop it. RBAC therefore has to be read together with workload admission controls, not treated as an isolated spreadsheet.

The RBAC authorizer is additive, which means Kubernetes does not have a native RBAC "deny" rule that can subtract permission from a broad grant. If a subject receives `get secrets` from one binding and a narrow pod-only role from another binding, the effective answer still includes `get secrets`. This is why audit work starts from effective permissions and then traces backward to the binding that granted the risky verb.

Pause and predict: if a ServiceAccount has one RoleBinding to a narrow pod-reader Role and another ClusterRoleBinding to a broad monitoring ClusterRole, which object controls the final answer when you run `kubectl auth can-i get secrets --as=system:serviceaccount:team:app`? The important habit is to stop thinking in terms of the most recent object you edited. Kubernetes evaluates the union of every applicable grant, so the unexpected "yes" often comes from an older binding that nobody removed.

In Kubernetes 1.35, RBAC still uses the stable `rbac.authorization.k8s.io/v1` API for Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings. That stability is useful on the exam because the object shapes are predictable, but it can also create complacency. The hard part is not remembering the field names; the hard part is deciding whether a subject should have that verb on that resource at that scope, and then proving the decision with `kubectl auth can-i`.

---

## Dangerous RBAC Patterns

The easiest RBAC mistake to spot is the wildcard role. It is also the easiest mistake to rationalize during a migration, a broken deployment, or a hurried incident response. A wildcard says "all API groups, all resources, all verbs," and that means the subject can read Secrets, change RBAC, create workloads, delete workloads, and use APIs that were installed after the role was written. In practice, a wildcard ClusterRole bound cluster-wide is functionally close to `cluster-admin`.

```yaml
# DANGEROUS: Allows everything
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: too-permissive
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]

# WHY IT'S BAD:
# - Equivalent to cluster-admin
# - Can access secrets, modify RBAC, delete anything
# - Violates least privilege
```

Wildcards sometimes appear because the requester cannot describe their real API dependency. That is a process problem, not a reason to grant the wildcard permanently. The safer workflow is to grant a temporary, time-boxed debugging path outside the application ServiceAccount, observe the required API calls, and then convert the result into explicit resources and verbs. In an exam task, you usually do not need the observation step; the prompt gives you enough workload intent to write the narrow role directly.

Secret access is the next pattern because Secrets often carry credentials that outlive the pod where they were mounted. RBAC treats Secrets as ordinary API resources, but operationally they are identity material, database passwords, registry pull credentials, TLS keys, and application tokens. A subject with `list secrets` across a namespace can collect every Secret in that namespace with one API call, and a subject with cluster-wide Secret access can turn one ServiceAccount compromise into many application compromises.

```yaml
# DANGEROUS: Can read all secrets
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]

# WHY IT'S BAD:
# - Secrets contain passwords, tokens, certificates
# - One secret can compromise entire applications
# - Should be tightly scoped to specific secrets
```

There are legitimate Secret readers, but they should be rare and intentionally scoped. A controller that synchronizes a named TLS certificate may need `get` on that one Secret through `resourceNames`, while a backup system may need a separate design review because it touches many sensitive objects. The practical audit question is not "does this tool mention Secrets anywhere"; it is "which exact Secret names must this subject read, in which namespace, and what happens if the token leaks."

RBAC modification rights are even more sensitive because they let a subject change the authorization graph itself. A developer who can create ClusterRoleBindings can attempt to bind a subject to a powerful ClusterRole, and a subject with the `bind` verb can bypass the normal check that prevents binding roles with permissions they do not already hold. A subject with the `escalate` verb can create or update roles that grant permissions beyond their own current permissions. Those verbs are not routine administration helpers; they are deliberate privilege boundaries.

```yaml
# DANGEROUS: Can modify RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: rbac-modifier
rules:
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings"]
  verbs: ["create", "update", "patch"]

# WHY IT'S BAD:
# - Can mutate RBAC objects cluster-wide
# - Dangerous combined with bind/escalate or existing broad grants
# - Only tightly controlled admins should modify RBAC
```

The subtle version of this mistake is giving namespace administrators too much RBAC write access because the cluster uses shared namespaces poorly. A namespace Role that can update Roles and RoleBindings is still powerful inside that namespace, especially when privileged ServiceAccounts already exist there. Before granting RBAC write rights, check whether the subject can bind to existing roles, whether admission policy restricts the ServiceAccounts they can use, and whether the namespace contains credentials for workloads outside the requester's responsibility.

Pod creation is the pattern that surprises many learners because `create pods` does not look like a cluster-wide permission. A pod spec can select a ServiceAccount, mount projected tokens, request hostPath volumes, set security context fields, and run containers that make API calls. RBAC alone does not evaluate whether that pod is safe; the authorization decision only asks whether the subject may create a pod object. Pod Security Admission, namespace policy, image policy, and ServiceAccount design decide how dangerous that object can become.

```yaml
# DANGEROUS: Can create pods (potential escalation)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-creator
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["create"]

# WHY IT'S BAD:
# - Can create pods that request privileged settings or stronger ServiceAccounts
# - Can mount service account tokens into the workload
# - Node-level escape depends on admission controls (Pod Security Admission, etc.)
# - RBAC alone does not evaluate whether the pod spec is safe
```

Stop and think: a developer has a Role that allows `create` on `pods` but nothing else, and they claim they cannot do anything dangerous. If the namespace contains a more powerful ServiceAccount and admission allows the pod to use it, the developer may create a pod that runs with that ServiceAccount token. The RBAC grant looked narrow on paper, but the workload object became a bridge to another identity.

Impersonation belongs in the same mental bucket. Kubernetes supports impersonation headers so administrators and tools can test authorization as another user, group, or ServiceAccount. That is useful for debugging, but the `impersonate` verb must be treated as sensitive because it lets a subject ask the API server to evaluate requests as someone else. A narrow impersonation grant can be safe for support workflows; a broad one can erase the boundary between the support identity and the target identity.

When you audit dangerous patterns, keep the chain of consequence in view. A broad read grant may expose credentials, a broad write grant may change workloads, a pod-creation grant may reach stronger ServiceAccounts, an RBAC-write grant may rewrite authorization, and an impersonation grant may skip identity boundaries. The right fix depends on which chain exists, not on a generic rule that every create verb is bad or every ClusterRole is forbidden.

---

## Least Privilege Examples

Least privilege is not the smallest YAML file you can write. It is the smallest permission set that supports a known behavior with a clear ownership boundary. In Kubernetes, that means starting from the workload's API calls, choosing the narrowest scope, avoiding wildcards, and verifying the result as the same user or ServiceAccount that will run in production. A role that breaks the workload is not a secure role; it is an incomplete role that will be bypassed under pressure.

The simplest good role grants read-only pod visibility inside one namespace. This is useful for a dashboard, support script, or application component that needs to inspect its own pods and fetch logs without changing cluster state. Notice that `pods/log` is a subresource, so it appears as a separate resource entry. A subject can have log access without receiving broad pod update or delete permission.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-viewer
  namespace: production
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

This Role is intentionally namespaced because the need is namespaced. If the support tool only handles the `production` namespace, a ClusterRoleBinding would make the proof harder and the blast radius larger. You may still define a reusable ClusterRole for pod viewing, but bind it with a RoleBinding in each namespace where the access is approved. That pattern gives you reuse without silently turning one team's request into cluster-wide visibility.

Resource name restrictions are useful when the API request can name the exact object up front. The `resourceNames` field below allows reads of two ConfigMaps and blocks reads of other ConfigMaps in the same namespace. This is a good fit for controllers or applications that load named configuration objects, but it is not a general replacement for namespace design because list and watch behavior has important limitations with `resourceNames`.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: specific-configmap-reader
  namespace: app
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config", "feature-flags"]  # Only these!
  verbs: ["get"]
```

Use `resourceNames` only when the workload naturally knows the object name. If an application must discover every ConfigMap with a label, it needs list access and `resourceNames` will not express that discovery pattern cleanly. If an operator only needs one Secret, though, `resourceNames` can be the difference between a controlled credential read and a namespace-wide credential dump. This is the kind of tradeoff a CKS answer should explain, not merely encode.

Subresources are another way to narrow intent. The `pods/exec` subresource is different from the main `pods` resource, and the verb is usually `create` because an exec session is created against an existing pod. This may feel odd at first, but it lets you grant debugging access without also granting permission to create, update, or delete pod objects. Subresource precision is a common sign that the role was designed from the API operation rather than copied from a broad example.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-executor
  namespace: debug
rules:
- apiGroups: [""]
  resources: ["pods/exec"]  # Only exec, not full pod access
  verbs: ["create"]
```

Before running this in a real namespace, what output do you expect from `kubectl auth can-i create pods --as=<subject>` after granting only `pods/exec`? The safe answer is "no," because exec access is not pod creation access. Prediction questions like this help you catch roles that grant the right-looking verb on the wrong resource, which is one of the fastest ways to over-permit debugging workflows.

A complete least-privilege design also checks the binding subject. Users and groups often come from an external identity provider, while ServiceAccounts are Kubernetes identities used by workloads. If a role is meant for an application pod, bind it to that application's ServiceAccount rather than to the namespace's `default` ServiceAccount. The `default` ServiceAccount is easy to use, but it becomes a shared bucket of permissions when multiple pods rely on it.

Least privilege is iterative because workloads change. A new controller version might need to create Events, watch Leases, or update a Status subresource. The correct response is not to panic and grant `edit`; it is to identify the denied API call, decide whether the call belongs to the workload's responsibility, add the smallest rule that supports it, and verify that unrelated operations still fail. That habit is what separates an operational RBAC fix from a permission dump.

---

## Auditing and Tracing Permissions

An RBAC audit starts with two questions: which roles are dangerous, and which subjects receive them. Searching only for `cluster-admin` bindings is necessary but incomplete because custom ClusterRoles can be just as powerful. The first pass should find wildcard rules, Secret readers, RBAC writers, impersonation grants, pod creators in sensitive namespaces, and bindings that attach those roles to broad groups or workload identities. The second pass should verify effective permissions as the actual subject.

```bash
# List all ClusterRoles with wildcard permissions
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    (.verbs[]? == "*") or
    (.resources[]? == "*") or
    (.apiGroups[]? == "*")
  ) | .metadata.name'

# Find roles that can read secrets
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    (.resources[]? | contains("secrets")) and
    ((.verbs[]? == "get") or (.verbs[]? == "*"))
  ) | .metadata.name'

# Find roles that can modify RBAC
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    (.apiGroups[]? == "rbac.authorization.k8s.io") and
    ((.verbs[]? == "create") or (.verbs[]? == "update") or (.verbs[]? == "*"))
  ) | .metadata.name'
```

These queries are intentionally simple because they teach the shape of the investigation. In a production review, you would also check namespaced Roles, verbs such as `patch`, `delete`, `bind`, `escalate`, and `impersonate`, and resources such as `serviceaccounts/token`, `pods/exec`, `pods/attach`, `nodes/proxy`, and workload subresources. Simplicity is acceptable for a first pass as long as you understand what it misses. A clean first pass does not prove the cluster is safe.

Effective permission checks are the fastest way to confirm what Kubernetes will actually allow. The `--as` flag asks the API server to evaluate the request as a specific user or ServiceAccount, which means your current admin identity is used to make the test request while the authorization decision is calculated for the target subject. That distinction matters because a successful `kubectl auth can-i` call does not mean the target token was used; it means the API server answered the authorization question for that target identity.

```bash
# What can a specific user do?
kubectl auth can-i --list --as=system:serviceaccount:default:myapp

# Can user create privileged pods?
kubectl auth can-i create pods --as=developer

# Can user read secrets?
kubectl auth can-i get secrets --as=system:serviceaccount:app:backend

# In specific namespace
kubectl auth can-i delete deployments -n production --as=developer
```

The `--list` output is useful, but it can be noisy when a subject inherits permissions from several bindings. For audit evidence, pair broad listing with targeted yes-or-no checks that match the risk you are investigating. If the concern is Secret exposure, test `get`, `list`, and `watch` on Secrets in the namespace and at cluster scope. If the concern is workload escalation, test pod creation in the namespace where powerful ServiceAccounts already exist.

Use namespaces as audit lenses, not only as filters in commands. A ServiceAccount identity includes its namespace, but a ClusterRoleBinding can still grant that identity cluster-wide permissions, so the namespace in the subject name does not guarantee namespace-limited access. When you test a workload identity, run at least one check inside its home namespace and one check in a neighboring namespace. The contrast tells you whether the binding type matches the intended boundary.

Separate authorization proof from object discovery. `kubectl get rolebindings` tells you what binding objects exist, while `kubectl auth can-i` tells you what the authorizer will allow after every applicable binding is considered. Both are necessary because one answers "where might this come from" and the other answers "what happens if the subject asks." In a review note, record both the risky object and the effective permission it produced.

Pay attention to subresources while tracing. A role that allows `get pods` does not automatically allow `get pods/log`, and a role that allows `create pods/exec` does not automatically allow `create pods`. That precision is helpful for least privilege, but it can also hide missing or excessive permissions if you audit only the parent resource name. When a support workflow mentions logs, exec, attach, status, or scale, include the subresource in the authorization check.

Tracing then moves from the answer back to the binding. A `yes` answer means some RoleBinding or ClusterRoleBinding grants the permission, directly or indirectly through a group. Start with broad binding searches, then inspect the referenced role, then inspect the subject list. If a ServiceAccount is involved, write the full identity string as `system:serviceaccount:<namespace>:<name>` because many audit mistakes come from confusing two ServiceAccounts with the same name in different namespaces.

```bash
# Who has cluster-admin?
kubectl get clusterrolebindings -o json | jq -r '
  .items[] |
  select(.roleRef.name == "cluster-admin") |
  "\(.metadata.name): \(.subjects[]?.name // "unknown")"'

# List all ClusterRoleBindings
kubectl get clusterrolebindings -o wide

# Describe suspicious binding
kubectl describe clusterrolebinding suspicious-binding
```

Exercise scenario: you are given a ServiceAccount named `backend` in namespace `app`, and the verifier shows it can delete pods even though the application only needs to read pod status. Your first step is not editing random YAML; it is proving where the delete permission comes from. Run `kubectl auth can-i delete pods --as=system:serviceaccount:app:backend -n app`, list RoleBindings in `app`, inspect each referenced Role or ClusterRole, and look for a rule that grants `delete` on `pods`.

```bash
# Given: ServiceAccount with too many permissions
# Task: Reduce to only get/list pods

# Check current permissions
kubectl auth can-i --list --as=system:serviceaccount:app:backend -n app

# Find the rolebinding
kubectl get rolebindings -n app -o wide

# Check the role
kubectl get role backend-role -n app -o yaml

# Create restricted role
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: app
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
EOF

# Verify
kubectl auth can-i delete pods --as=system:serviceaccount:app:backend -n app
# Should return "no"
```

The worked example overwrites the existing Role because the prompt says the desired outcome is only `get` and `list` pods. In a real review, you would check whether other subjects also use `backend-role` before changing it in place. If a shared Role supports multiple workloads, the safer repair may be creating a new narrow Role for the `backend` ServiceAccount and moving only that binding. The exam often gives a controlled environment; production rarely does.

Cluster-admin bindings deserve a separate check because they are high-risk even when the subject name looks service-specific. A binding named `developer-admin` or `monitoring-admin` does not become safe because the name describes a narrow function. The `roleRef` controls the permission set, and a `roleRef` pointing at `cluster-admin` grants full cluster control. The subject list controls who receives it, including groups and ServiceAccounts.

```bash
# Find who has cluster-admin
kubectl get clusterrolebindings -o json | jq -r '
  .items[] |
  select(.roleRef.name == "cluster-admin") |
  .metadata.name'

# Remove inappropriate binding
kubectl delete clusterrolebinding developer-admin
```

Deleting a dangerous binding is appropriate when you have confirmed it is inappropriate and there is a replacement path. If you delete first and analyze later, you may break controllers, monitoring, or emergency access in ways that create a different outage. A better operational sequence is identify the subject, define the required API operations, create the narrow replacement, test with `kubectl auth can-i`, and then remove the dangerous binding. The exam may compress that sequence, but the reasoning still matters.

Many workloads need more than one resource. The example below reads ConfigMaps and creates Events, which is a common pattern for applications or controllers that load configuration and report status. The role does not include Secrets, RBAC resources, pod creation, or cluster-scoped resources because none of those capabilities is part of the stated requirement. That gap is the point: least privilege is mostly deciding what not to include.

```bash
# Requirement: App needs to read configmaps and create events
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-role
  namespace: myapp
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-binding
  namespace: myapp
subjects:
- kind: ServiceAccount
  name: myapp-sa
  namespace: myapp
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

Pause and predict: you run `kubectl auth can-i --list --as=system:serviceaccount:default:default` and see permissions to `get`, `list`, and `watch` Secrets cluster-wide, but you did not create any RoleBindings for the default ServiceAccount. The most likely explanation is that a ClusterRoleBinding, group binding, or previously installed add-on attached broad permissions to that identity or to a group it belongs to. The next move is to inspect bindings, not to assume the `default` ServiceAccount is magic.

Debugging RBAC denials uses the same logic in reverse. A `no` answer tells you the effective permission set lacks the requested verb, resource, API group, scope, or resource name. Do not fix it by granting a broad built-in role unless the requirement truly matches that role. Instead, identify the missing operation, add the narrow rule, and verify both the newly allowed action and at least one action that should still be denied.

```bash
# Test as specific user
kubectl auth can-i create pods --as=jane

# Test as ServiceAccount
kubectl auth can-i get secrets --as=system:serviceaccount:default:myapp

# List all permissions
kubectl auth can-i --list --as=jane

# Why can/can't user do something?
kubectl auth can-i create pods --as=jane -v=5

# Check who can do something
kubectl auth who-can create pods
kubectl auth who-can delete secrets -n production
```

Some clusters provide `who-can` through a plugin or distribution-specific extension, while portable Kubernetes practice should always include `kubectl auth can-i` because it is part of the standard kubectl authorization workflow. If `who-can` is unavailable during an exam or review, fall back to listing RoleBindings and ClusterRoleBindings, following each `roleRef`, and comparing rules manually. That slower method is valuable because it forces you to understand exactly which object grants the permission.

---

## RBAC Escalation Prevention

Escalation prevention is about blocking paths, not only blocking obvious admin roles. A subject can become more powerful by directly changing RBAC, indirectly creating a pod that uses a stronger ServiceAccount, reading a Secret that contains another credential, impersonating a privileged identity, or reaching a node-level API that exposes credentials. The authorization graph and the workload graph meet at ServiceAccounts, pods, and tokens, so an RBAC review has to examine those connections together.

```text
┌─────────────────────────────────────────────────────────────┐
│              RBAC ESCALATION PATHS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Direct Escalation:                                        │
│  ─────────────────────────────────────────────────────────  │
│  1. Create/update ClusterRoleBindings                      │
│     → Attach powerful roles (bind guardrail applies)       │
│                                                             │
│  2. bind / escalate on RBAC resources                      │
│     → Expand permissions beyond current grants             │
│                                                             │
│  Indirect Escalation:                                      │
│  ─────────────────────────────────────────────────────────  │
│  3. Create pods in any namespace                           │
│     → Mount privileged ServiceAccount                      │
│                                                             │
│  4. Create pods with node access                           │
│     → Read kubelet credentials                             │
│                                                             │
│  5. Impersonate users                                      │
│     → Act as cluster-admin                                 │
│                                                             │
│  Prevention:                                               │
│  ─────────────────────────────────────────────────────────  │
│  • Never give RBAC modification rights loosely             │
│  • Use Pod Security Admission                               │
│  • Audit escalation verbs regularly                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The direct path is the easiest to explain. If a subject can create or update ClusterRoleBindings, and the API server allows that subject to bind a powerful role, the subject can attach itself or a controlled ServiceAccount to `cluster-admin`. Kubernetes has guardrails around privilege escalation, but those guardrails are expressed through authorization too. The special `bind` and `escalate` verbs exist because writing RBAC objects is itself a privileged operation.

What would happen if you find a ClusterRoleBinding that grants `cluster-admin` to a ServiceAccount called `monitoring-agent` in the `monitoring` namespace, and the monitoring team says they need it to "see everything"? If an attacker compromises a pod using that ServiceAccount, the attacker can use the mounted token to call the API as cluster-admin. The monitoring requirement may be broad read visibility, but the binding grants broad write and RBAC authority too.

```yaml
# The 'bind' verb allows creating bindings to roles
# even without permissions the role grants
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterrolebindings"]
  verbs: ["create"]  # Plus...
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles"]
  verbs: ["bind"]  # ...this allows binding to any role!

# The 'escalate' verb allows granting permissions
# that the user doesn't have
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles"]
  verbs: ["escalate"]  # Can add any permissions to roles!
```

The indirect pod path is more nuanced because RBAC and admission control share responsibility. RBAC may allow `create pods`, but Pod Security Admission can reject privileged fields, host namespaces, or hostPath volumes according to the namespace's enforced standard. ServiceAccount configuration can also reduce risk by avoiding shared default identities and disabling automatic token mounting when an application does not need API access. None of those controls replace RBAC, but they make pod creation less likely to become identity theft.

Secret access is another indirect path because Kubernetes credentials are often stored as Secrets or exposed through projected tokens. Reading the wrong Secret may reveal a database password, registry credential, TLS private key, or application token that gives access outside the cluster. A strict role for an app that reads one named ConfigMap should not accidentally include Secrets because the words "configuration" and "credential" sound similar in a ticket. Treat Secrets as authority-bearing objects, not harmless text blobs.

Impersonation should be granted only to identities that have a specific support or automation need. For example, a helpdesk workflow might be allowed to impersonate a small set of users for authorization checks, but it should not impersonate `system:masters`, every group, or every ServiceAccount. When you see `impersonate` in a role, ask which targets are allowed and why the operator cannot use `kubectl auth can-i --as` from an existing administrative identity instead.

Node-facing permissions also deserve attention in hardened clusters. Some resources and subresources can expose kubelet functionality, node proxy access, or workload data that is more powerful than the resource name suggests. You do not need to memorize every obscure escalation path for this module, but you should recognize the pattern: any permission that crosses from API metadata into credentials, node access, workload execution, or RBAC mutation requires stronger justification than ordinary read-only application visibility.

Escalation prevention therefore uses layered proof. First, confirm the subject cannot mutate RBAC or bind stronger roles. Second, confirm the subject cannot read broad Secrets or impersonate stronger identities. Third, confirm pod creation is paired with namespace-level Pod Security Admission and appropriate ServiceAccount boundaries. Finally, test the intended allowed action and at least two denied actions so that your fix does not merely look narrow in YAML.

---

## Patterns & Anti-Patterns

Patterns and anti-patterns are useful only when they help you choose under constraint. The exam rarely asks, "is least privilege good?" It gives you a workload, a failing command, a too-broad role, or a suspicious binding, and asks you to change the cluster without creating a new escalation path. The patterns below are decision habits: they connect the subject, the resource, the verb, the scope, and the verification step.

```text
┌─────────────────────────────────────────────────────────────┐
│              RBAC BEST PRACTICES                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Least Privilege                                        │
│     └── Only grant what's needed                           │
│     └── Prefer Roles over ClusterRoles                     │
│     └── Use resourceNames when possible                    │
│                                                             │
│  2. No Wildcards                                           │
│     └── Never use "*" in production                        │
│     └── List specific resources and verbs                  │
│                                                             │
│  3. Audit Regularly                                        │
│     └── Review cluster-admin bindings                      │
│     └── Check for secret access                            │
│     └── Monitor RBAC changes                               │
│                                                             │
│  4. Namespace Isolation                                    │
│     └── One ServiceAccount per application                 │
│     └── Roles scoped to namespace                          │
│                                                             │
│  5. Protect RBAC Resources                                 │
│     └── Only cluster admins modify RBAC                    │
│     └── Audit bind/escalate verbs                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| Approach | Use It When | Why It Works | Scaling Consideration |
|---|---|---|---|
| Role plus RoleBinding | A workload needs namespaced resources in one namespace | Scope matches the resource boundary and limits accidental cluster-wide grants | Repeat per namespace or template through GitOps when the same workload pattern appears |
| ClusterRole plus RoleBinding | The same namespaced rule set should be reused in several namespaces | The permission set is reusable but each binding remains namespace-scoped | Keep ownership clear so one shared ClusterRole change does not surprise every namespace |
| Resource names | The workload reads or updates specific named objects | The rule blocks access to neighboring objects of the same kind | Avoid for discovery workflows that need list or watch across dynamic object sets |
| Separate ServiceAccounts | Multiple workloads run in the same namespace with different API needs | Each token carries only the workload's own permissions | Requires deployment discipline so pods do not silently fall back to the default ServiceAccount |

The first anti-pattern is using built-in roles as a substitute for requirements gathering. `view`, `edit`, `admin`, and `cluster-admin` are convenient, but convenience is not evidence that the role matches the workload. In particular, `edit` can be too powerful for many application ServiceAccounts because workload mutation can interact with credentials and admission policy. Prefer custom roles when the requirement is small enough to state precisely.

The second anti-pattern is fixing a denial by adding a ClusterRoleBinding because it works everywhere. That approach often hides the original scope error and makes future audits harder. If the denied request is namespaced, fix it with a RoleBinding in the namespace unless the workload truly needs cluster-scoped resources or all namespaces. A successful command after a broad grant is not proof of a good fix; it is only proof that the broad grant included the missing permission.

The third anti-pattern is sharing a powerful default ServiceAccount across unrelated pods. This usually happens because manifests omit `serviceAccountName`, the namespace default picks up permissions over time, and nobody knows which workload still needs them. The better alternative is one ServiceAccount per application or controller, with `automountServiceAccountToken: false` when the pod does not call the API. That design turns an audit from a namespace mystery into a workload-specific review.

The fourth anti-pattern is ignoring denied actions after a change succeeds. If you grant a pipeline permission to patch Deployments, also verify that it cannot read Secrets, create ClusterRoleBindings, or delete workloads in a neighboring namespace. Negative tests are not ceremony; they are how you prove the fix did not smuggle in authority that the request never justified. On the CKS exam, a pair of targeted `can-i` checks can prevent a broad but passing answer.

---

## Decision Framework

Use a decision framework when you are under time pressure and every YAML field looks plausible. Start with the subject because identity controls blast radius: a human user, external group, controller ServiceAccount, and application ServiceAccount have different lifetimes and compromise models. Then identify the required API operation in Kubernetes terms: API group, resource or subresource, verb, namespace, and object name if applicable. Only after those facts are clear should you choose Role versus ClusterRole and binding type.

| Decision Point | Choose the Narrower Option When | Choose the Broader Option Only When |
|---|---|---|
| Role or ClusterRole | The resources are namespaced and the rule is unique to one namespace | The rule includes cluster-scoped resources or must be reused consistently |
| RoleBinding or ClusterRoleBinding | Access should apply inside one namespace | Access must apply cluster-wide and the subject is trusted for that scope |
| `get` or `list/watch` | The workload knows the exact object name | The workload must discover or continuously observe a set of objects |
| Custom role or built-in role | The requirement names a small set of resources and verbs | The built-in role has been reviewed and matches the full requirement |
| ServiceAccount token mounted or disabled | The pod does not call the Kubernetes API | The workload needs API access and has a role designed for that identity |

The safest workflow is requirement, role, binding, verification, and negative verification. First, write one sentence that describes the required behavior, such as "the backend ServiceAccount reads pods and pod logs in namespace app." Next, translate that sentence into a Role or ClusterRole. Then bind it to the exact subject. Finally, verify the allowed operation and at least one denied operation that would indicate overreach.

If you find an existing broad grant, decide whether to edit, replace, or split it. Edit the role only when you know every subject bound to it should receive the new narrower permissions. Replace the binding when one subject needs a different permission set from other subjects. Split the role when a shared role mixes unrelated capabilities, such as ConfigMap reads and RBAC writes, that should be owned by different identities.

When a workload is broken by RBAC, resist the urge to jump directly from the error message to a canned role. A `forbidden` error usually includes the attempted verb, resource, API group, and namespace, which is enough to draft a narrow rule. The missing rule still needs a policy decision: an application asking to update its own Status subresource is different from an application asking to list every Secret. Debugging tells you what was denied, not whether it should be allowed.

For privilege escalation review, reverse the framework. Ask what a compromised subject could do next if the current permission were abused. `get pods` usually reveals metadata, `get secrets` may reveal credentials, `create pods` may create a new execution environment, `patch deployments` may change running code, and RBAC write verbs may alter the authorization graph. That consequence-first thinking helps you prioritize which findings must be fixed before a PR or exam answer is considered complete.

The final decision rule is ownership. A platform team can own ClusterRoles, namespace teams can own RoleBindings inside their namespaces, and application teams can own ServiceAccounts only when guardrails prevent them from binding stronger roles or bypassing admission. If ownership is unclear, RBAC drifts toward broad shared identities because nobody wants to break someone else's workload. Clear ownership is a security control because it makes narrow permissions maintainable.

---

## Did You Know?

- **Kubernetes RBAC became stable in the `rbac.authorization.k8s.io/v1` API during the 1.8 release line.** That stability is why the same core Role and RoleBinding structure still appears in Kubernetes 1.35 training and production audits.

- **The `system:masters` group is treated as a static superuser identity, not a permission you grant through a RoleBinding.** The API server authorizer grants cluster-admin-equivalent access to this group directly, so removing RBAC bindings will not narrow a client certificate or identity that still belongs to it.

- **Aggregated ClusterRoles extend built-in roles through labels such as `rbac.authorization.k8s.io/aggregate-to-view`.** This lets custom resources add read rules to `view`, but it also means built-in role behavior can change when new labeled ClusterRoles are installed.

- **Secret values are base64-encoded, not encrypted for the reader who has API permission to fetch them.** Encryption at rest protects storage media, but RBAC still decides whether a user or ServiceAccount can ask the API server for the decoded object data.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Giving `cluster-admin` to developers | A broad binding makes broken commands work immediately, so it feels like an efficient unblock | Define the actual deployment, debug, or read operations and bind a custom Role or reviewed built-in role at the narrowest scope |
| Using ClusterRoles when a Role works | Engineers choose reusable objects before deciding whether the access should cross namespace boundaries | Use a Role for one namespace, or pair a reusable ClusterRole with namespace RoleBindings instead of a ClusterRoleBinding |
| Wildcards in production | Teams copy bootstrap YAML from experiments where speed mattered more than authorization boundaries | Replace `*` with explicit API groups, resources, and verbs, then verify expected allows and important denials |
| Not auditing bindings | Reviewers inspect Roles but miss the subjects that actually receive them | Trace RoleBindings and ClusterRoleBindings, including groups and ServiceAccounts, before judging effective access |
| Ignoring ServiceAccount defaults | Pods without `serviceAccountName` inherit the namespace default identity, which may collect old permissions | Create workload-specific ServiceAccounts and disable token automounting for pods that do not call the Kubernetes API |
| Granting Secret list access for convenience | Applications often ask for "configuration" access and Secrets get included with ConfigMaps | Separate credentials from configuration and use `resourceNames` for named Secret reads when the workload truly needs them |
| Fixing denials with `edit` | The built-in role is familiar and usually makes the immediate error disappear | Add the missing verb and resource only after deciding the denied operation belongs to the workload |
| Forgetting negative tests | A success check proves the desired action works but does not reveal accidental extra authority | Pair every allowed `kubectl auth can-i` check with denied checks for Secrets, RBAC writes, and neighboring namespaces |

---

## Quiz

<details>
<summary>1. Your CI ServiceAccount can patch Deployments in the `payments` namespace, but an audit shows it is bound to a wildcard ClusterRole through a ClusterRoleBinding. How do you implement a safer replacement without breaking releases?</summary>

Create a namespaced Role in `payments` that grants only the verbs and resources the pipeline needs, such as patching Deployments and reading rollout status if required. Bind that Role to the CI ServiceAccount with a RoleBinding, verify the allowed deployment operation with `kubectl auth can-i`, and verify that Secrets and RBAC writes are denied. The wildcard ClusterRoleBinding should be removed only after the narrow binding is proven to support the release workflow. This implements least privilege while preserving the business function.
</details>

<details>
<summary>2. A compromised pod used its ServiceAccount token to list Secrets across several namespaces. What do you audit first, and why is checking only the pod manifest insufficient?</summary>

Start by tracing the effective RBAC grants for the ServiceAccount, especially ClusterRoleBindings and any Roles or ClusterRoles that include `get`, `list`, or `watch` on Secrets. The pod manifest tells you which ServiceAccount was mounted, but it does not show every binding that grants that identity permission. You should then replace the broad Secret access with named Secret reads or remove it entirely if the workload does not need API Secret reads. Verifying as `system:serviceaccount:<namespace>:<name>` proves whether the fix changed the authorization answer.
</details>

<details>
<summary>3. A developer has `create pods` in a namespace that contains a ServiceAccount bound to `cluster-admin`. They cannot update RBAC directly. Explain the escalation risk and the controls you would check.</summary>

The developer may be able to create a pod that runs as the powerful ServiceAccount and then use the mounted token to call the API with that stronger identity. RBAC did not grant RBAC write access directly, but pod creation became an indirect path to another credential. Check whether admission policy restricts ServiceAccount selection, whether Pod Security Admission blocks dangerous pod settings, and whether powerful ServiceAccounts exist in that namespace. The safer design separates workloads, narrows ServiceAccounts, and grants pod creation only where those guardrails are in place.
</details>

<details>
<summary>4. Your team receives a `forbidden` error when an operator tries to create Events, and a teammate suggests binding the operator to `edit`. How do you diagnose and repair the denial more precisely?</summary>

Read the forbidden message to identify the verb, resource, API group, and namespace, then test the same action with `kubectl auth can-i create events --as=<subject> -n <namespace>`. If creating Events is part of the operator's responsibility, add a narrow rule for `create` on `events` in the core API group or the relevant Events API group used by the cluster version. Avoid `edit` because it grants many unrelated workload mutation permissions. After the change, verify that Event creation succeeds and unrelated actions such as reading Secrets still fail.
</details>

<details>
<summary>5. A Role contains `resourceNames: ["app-config"]` with `verbs: ["get"]` on ConfigMaps, but the application fails when it tries to watch ConfigMaps by label. Is the Role wrong, or is the application requirement different?</summary>

The Role is correct for reading a known ConfigMap by name, but it does not match a discovery workflow that watches a dynamic set of ConfigMaps. `resourceNames` works best when the client names the object in the request, while list and watch operations usually need broader access to observe sets. You should decide whether the application truly needs discovery; if it does, grant the narrowest namespace-scoped list or watch rule that supports that behavior. If it does not, change the application configuration so it requests the named ConfigMap directly.
</details>

<details>
<summary>6. During a review, you find a ClusterRole with `bind` and `escalate` on RBAC resources assigned to a namespace automation account. What makes this different from ordinary create or update access?</summary>

The `bind` verb allows a subject to create bindings to roles whose permissions it may not otherwise hold, and `escalate` allows role changes that grant permissions beyond the subject's current authority. Those verbs are specifically about crossing authorization boundaries, so they are more sensitive than routine writes to ordinary namespaced resources. A namespace automation account rarely needs them because namespace-scoped deployment work can usually be handled with narrow Roles and RoleBindings. Remove or isolate those verbs unless the account is a tightly controlled administrative identity with an explicit RBAC management responsibility.
</details>

<details>
<summary>7. You trace a suspicious `yes` from `kubectl auth can-i get secrets --as=system:serviceaccount:default:default` but cannot find a RoleBinding in the `default` namespace. What should you check next?</summary>

Check ClusterRoleBindings because they can grant cluster-wide permissions to a ServiceAccount even when no namespaced RoleBinding exists. Also inspect group subjects if the identity provider or bootstrap process mapped the subject into a privileged group, although ServiceAccounts are usually easiest to trace by their full `system:serviceaccount` name. Once you find the binding, inspect the referenced ClusterRole for Secret rules and replace the grant with a namespace RoleBinding only if Secret access is truly required. The key is tracing the effective permission backward rather than assuming the namespace contains the source.
</details>

---

## Hands-On Exercise

In this exercise, you will audit and repair an intentionally over-permissioned ServiceAccount. The setup grants a namespace ServiceAccount a wildcard ClusterRole through a ClusterRoleBinding, which is exactly the kind of shortcut you should be able to recognize and remove. Run the commands in a disposable cluster or lab environment because the exercise creates RBAC objects and then deletes them during cleanup.

```bash
# Setup: Create overpermissive configuration
kubectl create namespace rbac-test
kubectl create serviceaccount admin-app -n rbac-test

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: overpermissive
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-app-binding
subjects:
- kind: ServiceAccount
  name: admin-app
  namespace: rbac-test
roleRef:
  kind: ClusterRole
  name: overpermissive
  apiGroup: rbac.authorization.k8s.io
EOF

# Task 1: Audit the permissions
kubectl auth can-i --list --as=system:serviceaccount:rbac-test:admin-app

# Task 2: Confirm it can read secrets (expected with the wildcard grant)
kubectl auth can-i get secrets --as=system:serviceaccount:rbac-test:admin-app

# Task 3: Create a restricted role (only pods in namespace)
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-manager
  namespace: rbac-test
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "create", "delete"]
EOF

# Task 4: Replace the ClusterRoleBinding with RoleBinding
kubectl delete clusterrolebinding admin-app-binding

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: admin-app-binding
  namespace: rbac-test
subjects:
- kind: ServiceAccount
  name: admin-app
  namespace: rbac-test
roleRef:
  kind: Role
  name: pod-manager
  apiGroup: rbac.authorization.k8s.io
EOF

# Task 5: Verify permissions are now restricted
kubectl auth can-i get secrets --as=system:serviceaccount:rbac-test:admin-app
# Should return "no"

kubectl auth can-i get pods --as=system:serviceaccount:rbac-test:admin-app -n rbac-test
# Should return "yes"

kubectl auth can-i get pods --as=system:serviceaccount:rbac-test:admin-app -n default
# Should return "no" (namespace-scoped)

# Cleanup
kubectl delete namespace rbac-test
kubectl delete clusterrole overpermissive
```

Your first task is to capture the unsafe baseline before you fix anything. Save the `kubectl auth can-i --list` output somewhere you can compare mentally against the final state, and run targeted checks for Secrets, pod access in `rbac-test`, and pod access in another namespace. The point is to prove both the existence of the risky grant and the exact scope of the repaired grant.

- [ ] Create the `rbac-test` namespace, `admin-app` ServiceAccount, wildcard ClusterRole, and ClusterRoleBinding from the setup block.
- [ ] Audit effective permissions for `system:serviceaccount:rbac-test:admin-app` and identify at least one dangerous allowed action.
- [ ] Confirm that the ServiceAccount can read Secrets before the fix, then write down why that is unacceptable for a pod-management identity.
- [ ] Replace the wildcard ClusterRoleBinding with a namespace RoleBinding to the `pod-manager` Role.
- [ ] Verify that pod management works in `rbac-test` and fails in `default`.
- [ ] Verify that Secret reads are denied after the replacement binding is applied.

<details>
<summary>Solution guidance</summary>

The important repair is changing both the permission set and the binding scope. The `pod-manager` Role is namespaced, and the replacement RoleBinding lives in `rbac-test`, so the ServiceAccount no longer receives wildcard cluster-wide permissions. Your final checks should show `no` for Secret reads, `yes` for pod access in `rbac-test`, and `no` for pod access in `default`. If any of those answers differ, inspect remaining ClusterRoleBindings because an old broad grant may still apply.
</details>

After the basic repair, extend the exercise by making the role more realistic. Decide whether the application truly needs `create` and `delete` on Pods, or whether it only needs `get`, `list`, `watch`, and `get` on `pods/log`. Then update the Role accordingly and repeat the positive and negative checks. This second pass matters because the provided `pod-manager` Role is safer than the wildcard, but it may still be broader than a read-only application actually needs.

<details>
<summary>Challenge solution</summary>

For a read-only workload, remove `create` and `delete` from the `pods` rule and add a separate `pods/log` rule with `get` if logs are required. Verify that `kubectl auth can-i delete pods --as=system:serviceaccount:rbac-test:admin-app -n rbac-test` returns `no`, while `kubectl auth can-i get pods --as=system:serviceaccount:rbac-test:admin-app -n rbac-test` returns `yes`. This demonstrates that least privilege is not only replacing cluster-wide scope; it is also removing unnecessary verbs inside the namespace.
</details>

Success is not just a passing command. A secure answer has evidence that the ServiceAccount kept the intended namespace pod capability, lost cluster-wide reach, lost Secret access, and no longer depends on wildcard permissions. That evidence is what you would put in a pull request, incident note, or exam answer to show that the repair is controlled rather than lucky.

---

## Learner check

> A wildcard ClusterRole bound through a ClusterRoleBinding lets a namespace ServiceAccount read Secrets cluster-wide; the hands-on exercise proves that over-broad baseline with `kubectl auth can-i` before you replace the binding with a namespace-scoped RoleBinding.

Before you move on, explain why mutating ClusterRoleBindings is not automatically equivalent to granting yourself `cluster-admin`, and which RBAC verbs make that difference explicit. A solid answer names the `bind` and `escalate` guardrails, contrasts direct RBAC mutation with indirect pod-based escalation, and includes at least one negative `kubectl auth can-i` check after your repair.

---

## Sources

- https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- https://kubernetes.io/docs/reference/access-authn-authz/authorization/
- https://kubernetes.io/docs/reference/access-authn-authz/authentication/
- https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_auth/kubectl_auth_can-i/
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/
- https://kubernetes.io/docs/concepts/security/pod-security-admission/
- https://kubernetes.io/docs/concepts/security/pod-security-standards/
- https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/role-v1/
- https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/role-binding-v1/
- https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/cluster-role-v1/
- https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/cluster-role-binding-v1/

## Next Module

[Module 2.2: ServiceAccount Security](../module-2.2-serviceaccount-security/) - Harden ServiceAccounts, token mounting, and workload identities so RBAC grants do not become reusable credentials.
