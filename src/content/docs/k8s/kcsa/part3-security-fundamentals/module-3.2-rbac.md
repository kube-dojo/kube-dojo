---
revision_pending: false
title: "Module 3.2: RBAC Fundamentals"
slug: k8s/kcsa/part3-security-fundamentals/module-3.2-rbac
sidebar:
  order: 3
---
# Module 3.2: RBAC Fundamentals

**Complexity**: `[MEDIUM]` - Core knowledge. **Time to Complete**: 40-50 minutes. **Prerequisites**: [Module 3.1: Pod Security](../module-3.1-pod-security/). This lesson assumes you already know the Pod Security Standards from the previous module and are ready to connect workload hardening with API authorization decisions.

## Learning Outcomes

After completing this module, you will be able to make and defend practical authorization decisions in Kubernetes 1.35+ clusters. Each outcome below is assessed through the scenario quiz or the hands-on design exercise, so treat the list as a working checklist rather than a passive reading guide.

1. **Evaluate** RBAC policies for over-permissioned roles, wildcard access, and privilege escalation risks.
2. **Design** namespace-scoped RoleBinding and ClusterRoleBinding strategies that preserve least privilege across Kubernetes 1.35+ clusters.
3. **Diagnose** why a user, group, or ServiceAccount can or cannot perform an action by tracing subjects, roles, bindings, API groups, resources, and verbs.
4. **Compare** built-in roles, custom roles, aggregated ClusterRoles, and ServiceAccount permissions for realistic platform and application teams.
5. **Implement** an auditable RBAC model for developers, team leads, and deployment automation without granting broad cluster-admin access.

## Why This Module Matters

In 2023, a financial services platform suffered a severe Kubernetes incident after a deployment automation account was granted broad write permissions during a weekend release freeze. The change was supposed to be temporary, but it remained in the cluster after the release succeeded. When attackers later obtained the automation token from a compromised build job, they did not need a kernel exploit or a novel container escape. They used the permissions already granted to the ServiceAccount, created privileged workloads, mounted sensitive volumes, and turned a CI compromise into a cluster-wide recovery effort that consumed days of engineering time and delayed customer-facing work.

RBAC is the guardrail that decides whether an authenticated Kubernetes request is allowed after the API server knows who made the request. Authentication answers "who are you?", admission answers "is this object acceptable?", and authorization answers "may this subject do this verb on this resource in this scope?". If that middle authorization decision is too generous, every other control has to work harder. If it is too narrow or confusing, operators start bypassing the model with emergency bindings that become permanent risk.

This module treats RBAC as an engineering design problem rather than a list of object names to memorize. You will learn how Roles, ClusterRoles, RoleBindings, ClusterRoleBindings, users, groups, and ServiceAccounts combine into effective permissions; why apparently harmless verbs like `create` can become escalation paths; and how to reason about access before applying a manifest. When this module mentions command-line checks, it uses the short alias `alias k=kubectl`, so a command like `k auth can-i get pods -n production` means the standard Kubernetes client command with a shorter name.

## RBAC Concepts: Subjects, Rules, and Bindings

RBAC stands for Role-Based Access Control, but the name hides the most important detail: Kubernetes grants permissions by connecting a subject to a set of rules through a binding. The subject is the authenticated identity, such as a human user, an external identity group, or a ServiceAccount mounted into a Pod. The rule describes actions against resources, such as `get pods` in the core API group or `update deployments` in the `apps` API group. The binding is the actual grant, and without a binding the role definition is only an unused permission template.

Think of RBAC like a corporate office security system. A badge can be programmed to open only the storage room, only the third floor, or every door in the building, but the badge matters only after someone receives it. The access desk also has to know whether the person is an employee, contractor, or service technician, because the same badge policy may be appropriate for one identity and dangerous for another. Kubernetes follows the same pattern with subjects, roles, and bindings, except the doors are API resources and the door actions are verbs like `get`, `list`, `create`, `patch`, and `delete`.

```
┌─────────────────────────────────────────────────────────────┐
│              RBAC BUILDING BLOCKS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHO                           WHAT                        │
│  (Subjects)                    (Rules)                     │
│  ┌─────────────┐              ┌─────────────┐              │
│  │ Users       │              │ Verbs       │              │
│  │ Groups      │              │ Resources   │              │
│  │ ServiceAccts│              │ API Groups  │              │
│  └──────┬──────┘              └──────┬──────┘              │
│         │                            │                      │
│         │         BINDING            │                      │
│         │      (Connection)          │                      │
│         │     ┌───────────┐          │                      │
│         └────→│ Role      │←─────────┘                      │
│               │ Binding   │                                 │
│               └───────────┘                                 │
│                                                             │
│  Role = Collection of permissions (verbs on resources)     │
│  Binding = Connects subjects to roles                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The diagram is intentionally simple because every RBAC review starts with the same three questions. Who is the subject? What exact rules are granted? Where is the binding scoped? A surprising number of incidents come from answering only one of those questions. A team reviews a Role and sees modest verbs, but misses that a ClusterRoleBinding grants it everywhere. Another team reviews a RoleBinding and sees only one ServiceAccount, but misses that the ServiceAccount token is mounted into a workload controlled by a broader CI system.

RBAC is additive, which means Kubernetes does not support deny rules inside RBAC itself. If one binding grants `view` and another binding grants `get secrets`, the subject has both permissions. This feels natural when you are adding access for a team, but it becomes dangerous when administrators assume a safer role can cancel a risky role. It cannot. The effective permission set is the union of every matching grant for that user, group, and ServiceAccount.

An RBAC review is therefore a graph problem more than a file review. The risky grant may not be in the manifest you are currently editing; it may be in an older ClusterRoleBinding, an identity-provider group, or a ServiceAccount used by a controller. When a reviewer asks "can this workload read production Secrets?", the answer lives in the combination of subjects, bindings, role references, namespace scope, and inherited group membership. Reading only the new Role is like checking one door in a building while ignoring the master badge already issued to the same person.

This additive model also changes how you remediate mistakes. Removing a suspicious RoleBinding may not remove the permission if another binding grants the same rule through a group. Tightening a Role may not help if a ClusterRoleBinding grants a broader ClusterRole to the same subject. Good operators build the habit of proving both sides: the allowed action required by the workflow and the denied action that would indicate overreach.

> **Pause and predict**: If RBAC only allows additive permissions, what happens when a group has a safe read-only binding and one user in that group also receives a direct binding that grants secret access? Before reading further, decide which binding wins and how you would prove it with `k auth can-i`.

The direct answer is that both bindings apply, so the direct secret permission is allowed. Kubernetes authorization does not choose one binding over another, and it does not rank a group grant below a user grant for cancellation purposes. This is why effective access reviews must collect all subjects associated with a request: the username, the groups supplied by authentication, and the ServiceAccount identity when the request comes from a Pod.

## Roles, ClusterRoles, and Scope

RBAC scope is the first design decision because it determines the blast radius of a mistake. A Role is namespaced, so its rules apply only inside one namespace and only to namespaced resources. A ClusterRole is cluster-scoped, which means it can describe permissions for cluster resources such as nodes, persistent volumes, and namespaces. A ClusterRole can also be reused inside a namespace when a RoleBinding points to it, which is a useful pattern when many namespaces need the same permission shape without granting access to every namespace.

```
┌─────────────────────────────────────────────────────────────┐
│              ROLE SCOPE                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ROLE (Namespace-scoped)                                   │
│  ├── Defines permissions within a single namespace         │
│  ├── Can only reference namespace-scoped resources         │
│  └── Bound with RoleBinding                                │
│                                                             │
│  CLUSTERROLE (Cluster-scoped)                              │
│  ├── Defines permissions cluster-wide                      │
│  ├── Can reference any resource (including cluster-wide)   │
│  ├── Can be bound with:                                    │
│  │   ├── ClusterRoleBinding (cluster-wide access)          │
│  │   └── RoleBinding (namespace-scoped access)             │
│  └── Used for cluster-wide resources or reusable roles     │
│                                                             │
│  WHEN TO USE WHAT:                                         │
│  • Single namespace permissions → Role + RoleBinding       │
│  • Same role in multiple namespaces → ClusterRole +        │
│    RoleBinding per namespace                               │
│  • Cluster-wide permissions → ClusterRole +                │
│    ClusterRoleBinding                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The common beginner mistake is treating ClusterRole as synonymous with cluster-wide grant. It is not. A ClusterRole is a reusable definition, while the binding determines where the definition is granted. If you bind a ClusterRole with a RoleBinding in the `dev` namespace, the subject receives those rules only in `dev` for namespaced resources. If you bind the same ClusterRole with a ClusterRoleBinding, the subject receives the rules cluster-wide, including future namespaces that nobody considered during the original change request.

That distinction is useful in real platform teams. Suppose five product namespaces all need the same read-only access to Deployments and Services. Creating five identical Roles works, but the definitions drift over time when one namespace gets patched and another is forgotten. A better approach is often one ClusterRole that defines the shared permission set, plus one RoleBinding per namespace that references it. You preserve one central definition while still making namespace grants explicit and reviewable.

The opposite situation is a cluster-level controller that must watch namespaces or nodes. A Role cannot describe those resources because they do not live inside a namespace. In that case, a ClusterRole is required, and a ClusterRoleBinding may be justified if the controller truly needs to operate across the entire cluster. The security question is not "is ClusterRole always bad?"; it is "does the binding scope match the operational need?".

```yaml
# Namespace-scoped Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]           # "" = core API group
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

This Role grants only three read-style verbs on Pods in the `production` namespace. The empty string in `apiGroups` points to the core Kubernetes API group, which contains Pods, Services, ConfigMaps, Secrets, and several other foundational resources. The Role does not grant access to Deployments because Deployments are in the `apps` API group, and it does not grant access to Pods in another namespace because Role scope stops at the namespace boundary.

```yaml
# Cluster-scoped ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]      # Cluster-scoped resource
  verbs: ["get", "watch", "list"]
```

This ClusterRole can describe access to Nodes because Nodes are cluster-scoped resources. If a monitoring system needs to read node objects for inventory, scheduling signals, or capacity reporting, a ClusterRole like this may be appropriate. If a developer only needs to inspect Pods in one namespace, this shape would be wrong because it reaches into cluster infrastructure rather than application-owned resources.

### Rule Components

| Component | Description | Examples |
|-----------|-------------|----------|
| **apiGroups** | API group containing resource | `""` (core), `"apps"`, `"networking.k8s.io"` |
| **resources** | Resource types | `"pods"`, `"deployments"`, `"secrets"` |
| **verbs** | Actions allowed | `"get"`, `"list"`, `"create"`, `"delete"` |
| **resourceNames** | Specific resource names (optional) | `["my-configmap"]` |

Each rule is a tuple of API group, resource, optional resource name, and verb. You can think of it as a sentence: "allow this subject to perform these actions on these resource types in this API group, optionally only for these named objects." The precise wording matters because similar resource names can live in different API groups, and subresources such as `pods/log` and `pods/exec` are separate authorization targets from `pods` itself.

### Common Verbs

```
┌─────────────────────────────────────────────────────────────┐
│              RBAC VERBS                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  READ OPERATIONS                                           │
│  ├── get      - Read a single resource                     │
│  ├── list     - List all resources                         │
│  └── watch    - Watch for changes                          │
│                                                             │
│  WRITE OPERATIONS                                          │
│  ├── create   - Create new resources                       │
│  ├── update   - Update existing resources                  │
│  ├── patch    - Partially update resources                 │
│  └── delete   - Delete resources                           │
│                                                             │
│  SPECIAL VERBS                                             │
│  ├── deletecollection - Delete multiple resources          │
│  ├── bind     - Bind roles (for RoleBindings)              │
│  ├── escalate - Modify roles (requires special permission) │
│  ├── impersonate - Act as another user                     │
│  └── * (wildcard) - All verbs (DANGEROUS)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Read verbs are not automatically harmless. Listing Pods can reveal image names, environment variable names, node placement, labels, and operational structure. Getting Secrets is obviously sensitive, but getting ConfigMaps may also reveal internal endpoints, feature flags, and integration details that help an attacker move laterally. Watching resources gives a long-lived stream of cluster changes, which can expose new workloads or newly created objects as they appear.

Write verbs deserve even more scrutiny because Kubernetes objects often contain other objects. Creating a Deployment also creates Pods through a controller. Patching a Deployment can change the Pod template, mount a Secret, alter a ServiceAccount, or add an image from a hostile registry if admission controls do not stop it. Creating a Pod directly may let a subject request host paths, privileged settings, or Secret mounts, which turns a simple-looking verb into a possible escalation path.

Special verbs are usually the difference between application access and platform administration. The `bind` verb can let a subject attach roles to identities, while `escalate` controls whether a subject can create or update roles containing permissions they do not already hold. The `impersonate` verb is powerful because it allows a request to be evaluated as another user, group, or ServiceAccount. These verbs are appropriate for tightly controlled automation in some clusters, but they should never appear in a casual application role.

## Binding Identities to Permissions

A Role or ClusterRole does nothing until a binding connects it to a subject. RoleBindings are namespaced objects, and they can reference either a Role in the same namespace or a ClusterRole as a reusable definition. ClusterRoleBindings are cluster-scoped objects, and they can reference only ClusterRoles because a namespace-scoped Role cannot be granted across the cluster. This gives you three common grant patterns: Role plus RoleBinding for one namespace, ClusterRole plus RoleBinding for reusable namespaced access, and ClusterRole plus ClusterRoleBinding for genuine cluster-wide access.

```yaml
# Binds Role to users/groups in a namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
- kind: User
  name: alice
  apiGroup: rbac.authorization.k8s.io
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: my-app
  namespace: production
roleRef:
  kind: Role                    # or ClusterRole
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

This RoleBinding grants the referenced `pod-reader` Role inside `production` to three subject forms. Human users and external groups usually come from the cluster's authentication layer, such as client certificates, OpenID Connect, or a cloud provider integration. ServiceAccounts are native Kubernetes identities, and their namespace is part of the identity. A ServiceAccount named `my-app` in `production` is not the same subject as a ServiceAccount named `my-app` in `staging`.

```yaml
# Cluster-wide binding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-nodes-everywhere
subjects:
- kind: Group
  name: operations
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

This ClusterRoleBinding grants the `operations` group the `node-reader` ClusterRole across the cluster. For a central operations team that maintains node health, this may be justified. For an application team that only needs to troubleshoot workloads in one namespace, it would be too broad. The difference is not syntactic; the difference is whether the binding scope reflects the business and operational boundary.

Role references are immutable in Kubernetes. If you create a RoleBinding pointing to the wrong Role, you cannot patch only the `roleRef` to fix it; you delete and recreate the binding. That behavior is deliberate because changing `roleRef` on an existing binding could silently transform a harmless grant into a powerful one while preserving the same binding name. In GitOps workflows, this also makes reviews clearer because replacing a binding has a more obvious diff than mutating the meaning of an existing grant.

Before running any RBAC manifest, test your mental model with `k auth can-i`. If you plan to give a developer read access to Pods but not Secrets, ask the API server exactly that: `k auth can-i get pods -n production --as alice` and `k auth can-i get secrets -n production --as alice`. For ServiceAccounts, use the canonical username shape `system:serviceaccount:namespace:name`, and remember that group membership for service accounts also exists through service-account groups.

> **Before running this, what output do you expect?** Imagine a RoleBinding in `dev` references the `view` ClusterRole, while a ClusterRoleBinding grants the same group `get secrets` everywhere. Predict the result of `k auth can-i get secrets -n dev --as alice --as-group developers`, then explain which binding caused that result.

The expected result is yes if the supplied user and group match the broad secret grant. The RoleBinding to `view` does not include Secrets, but it also does not deny Secrets. The separate ClusterRoleBinding contributes another allowed rule, and the final authorization decision sees the union. This is why command-line checks are most valuable when you test both the intended access and the access you explicitly do not want.

## Auditing Effective Access

Auditing RBAC starts with a request, not with a manifest. A Kubernetes authorization check contains a user, zero or more groups, a verb, an API group, a resource or subresource, a namespace when applicable, and sometimes a resource name. If any rule reachable through any binding matches those request attributes, the request is allowed. This is why the most reliable audit question is concrete: "Can `system:serviceaccount:cicd:cicd-deployer` patch Deployments in `staging`, and can it read Secrets in `production`?"

A useful audit workflow has three passes. The first pass inventories subjects and bindings so you know which identities have direct or group-based access. The second pass classifies roles by risk, highlighting wildcards, special verbs, Secrets, workload creation, role management, and cluster-wide grants. The third pass runs representative positive and negative authorization checks against the API server. The first two passes tell you what the YAML appears to say, while the third pass confirms how the API server actually evaluates the subject.

ServiceAccounts deserve a separate pass because they are often less visible than human users. A human identity may be reviewed through an identity provider, ticketing workflow, or team roster, but a ServiceAccount can be created inside a namespace and then mounted into a Pod. If that Pod is controlled by a deployment system, an operator, or a compromised workload, the ServiceAccount's permissions become the workload's permissions. The audit should therefore connect each ServiceAccount binding to the workloads that can use it.

Subresources are another common audit blind spot. Access to `pods` is not the same as access to `pods/log`, `pods/exec`, or `pods/portforward`. A developer may need logs for troubleshooting without needing interactive shell access into containers. A support tool may need to watch Pods without needing to create them. Precise subresource rules let you support real operations without granting a broader resource permission than the workflow requires.

Resource names can narrow some permissions, but they are not a universal answer. A Role can restrict `get` or `update` to a named ConfigMap, which is useful for a workload that reads one known configuration object. The same technique becomes awkward for resources created dynamically, and it does not remove the need to review verbs and binding scope. Use `resourceNames` when the object identity is stable, but do not rely on it to fix an otherwise broad role.

Audit findings should be written in language that both platform and application teams can act on. "Wildcard verb on core resources" is technically accurate, but "this deployment token can delete every ConfigMap and Secret in `staging`" creates better urgency. Similarly, "ClusterRoleBinding to `edit`" is less useful than "members of this group can modify most namespaced resources in every namespace, including namespaces created later." Translating RBAC syntax into operational consequences is part of the security work.

The final audit step is deciding whether a risky permission is necessary, compensating, or unjustified. Necessary permissions should have owners, scope, and tests. Compensating permissions may be acceptable only when admission policy, namespace isolation, and monitoring reduce the practical risk. Unjustified permissions should be removed in the same change that records the expected negative checks, because otherwise the team may rediscover the risk and re-add the grant during a future incident.

## Built-In Roles and Aggregation

Kubernetes ships with default ClusterRoles that cover common administrative and user-facing patterns. These roles are convenient, but convenience should not replace review. The built-in `cluster-admin` role is essentially full power. The `admin` role is powerful inside a namespace and can manage roles and bindings there. The `edit` role can modify many namespace resources, while `view` is read-only for many resources and intentionally excludes Secrets. These are starting points, not a substitute for understanding your workload boundary.

```
┌─────────────────────────────────────────────────────────────┐
│              BUILT-IN CLUSTERROLES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  USER-FACING ROLES                                         │
│                                                             │
│  cluster-admin                                             │
│  ├── Full access to everything                             │
│  ├── Can do anything in any namespace                      │
│  └── DANGEROUS - use sparingly                             │
│                                                             │
│  admin                                                     │
│  ├── Full access within a namespace                        │
│  ├── Can create roles/bindings in namespace                │
│  └── Use for namespace administrators                      │
│                                                             │
│  edit                                                      │
│  ├── Read/write to most namespace resources                │
│  ├── Cannot view or modify roles/bindings                  │
│  └── Use for developers                                    │
│                                                             │
│  view                                                      │
│  ├── Read-only access to most namespace resources          │
│  ├── Cannot see secrets                                    │
│  └── Use for auditors, observers                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The `view` role's exclusion of Secrets is a good example of Kubernetes security design meeting operational reality. Many teams need to see Pods, Services, Deployments, Events, and ConfigMaps during troubleshooting, but reading Secrets would expose credentials and service tokens. Binding `view` is therefore safer than creating a broad custom read role with `resources: ["*"]`, but it is not a complete policy boundary. A second binding can still add secret access, and a subject with write access to workloads may still cause Pods to mount Secrets if other controls allow it.

### System Roles

```
┌─────────────────────────────────────────────────────────────┐
│              SYSTEM CLUSTERROLES                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  system:* roles are for Kubernetes components              │
│                                                             │
│  system:kube-scheduler                                     │
│  └── Permissions for the scheduler                         │
│                                                             │
│  system:kube-controller-manager                            │
│  └── Permissions for controller manager                    │
│                                                             │
│  system:node                                               │
│  └── Permissions for kubelets (with Node authorization)    │
│                                                             │
│  system:masters group                                      │
│  └── Bound to cluster-admin (full access)                  │
│  └── Certificate O=system:masters = cluster-admin          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

System roles support core Kubernetes components, and administrators should treat them as implementation details unless they are operating the control plane itself. Editing system roles can break controllers, kubelets, or scheduler behavior in ways that look like unrelated cluster instability. The `system:masters` group is especially sensitive because certificates carrying that organization are commonly bound to cluster-admin. If an organization uses client certificates, certificate issuance and storage become part of the RBAC threat model.

ClusterRole aggregation adds another layer. Some ClusterRoles are automatically composed from other ClusterRoles whose labels match an aggregation rule. The built-in `admin`, `edit`, and `view` roles use this pattern so extension APIs can participate in the user-facing roles. This is useful for CustomResourceDefinitions because a platform can label a ClusterRole and have those CRD permissions appear in a standard role, but the same mechanism becomes risky if untrusted users can create labeled ClusterRoles.

```yaml
# ClusterRole with aggregation rule
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-endpoints
  labels:
    rbac.example.com/aggregate-to-monitoring: "true"
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
---
# Aggregating ClusterRole (combines all matching)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring
aggregationRule:
  clusterRoleSelectors:
  - matchLabels:
      rbac.example.com/aggregate-to-monitoring: "true"
# Rules are automatically combined from aggregated roles
rules: []  # Populated by controller
```

The aggregation controller populates the rules of the aggregating ClusterRole, so the empty `rules: []` field is not a mistake. The operational risk is label control. If a subject can create a ClusterRole with a label selected by an important aggregate role, that subject may be able to add permissions to everyone bound to the aggregate. Admission policy and review rules should therefore treat aggregation labels as privileged configuration, not as harmless metadata.

For KCSA-level reasoning, aggregation is less about memorizing controller mechanics and more about recognizing indirect permission changes. A diff that adds a label to a ClusterRole may be just as important as a diff that edits a rule list. If the label is selected by an aggregate role bound to many users, that small metadata change can expand access across a large group. This is the same lesson as additive RBAC in another form: permissions can arrive through connections that are not obvious from the object being reviewed.

## Least Privilege and Dangerous Permissions

Least privilege is not the smallest YAML file you can write. It is the practice of granting only the actions a subject needs, at the narrowest scope that still supports the workflow, with enough clarity that reviewers can understand the grant later. In Kubernetes, that means choosing namespace scope when possible, avoiding wildcards, limiting verbs to real use cases, separating human and automation access, and revisiting old bindings when teams, tools, and namespaces change.

```
┌─────────────────────────────────────────────────────────────┐
│              LEAST PRIVILEGE RBAC                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BAD: Overly permissive                                    │
│  rules:                                                    │
│  - apiGroups: ["*"]        # All API groups                │
│    resources: ["*"]        # All resources                 │
│    verbs: ["*"]            # All actions                   │
│                                                             │
│  GOOD: Precisely scoped                                    │
│  rules:                                                    │
│  - apiGroups: [""]                                         │
│    resources: ["pods"]                                     │
│    verbs: ["get", "list"]                                  │
│  - apiGroups: [""]                                         │
│    resources: ["pods/log"]                                 │
│    verbs: ["get"]                                          │
│                                                             │
│  GUIDELINES:                                               │
│  • Use namespace-scoped roles when possible                │
│  • Avoid wildcards (*)                                     │
│  • Grant specific verbs, not ["*"]                         │
│  • Prefer RoleBinding over ClusterRoleBinding              │
│  • Review and audit regularly                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Wildcards deserve special attention because they include resources and verbs that may not exist when the role is written. A wildcard on resources can include future CustomResourceDefinitions, and a wildcard on verbs can include operational actions the author did not consider. This is especially risky in platform clusters where teams add operators over time. A role that looked like a broad convenience grant in January can silently become access to a new production database CRD later in the year.

```
┌─────────────────────────────────────────────────────────────┐
│              DANGEROUS RBAC PERMISSIONS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIVILEGE ESCALATION RISKS:                               │
│                                                             │
│  CREATE pods                                               │
│  └── Can create privileged pods, escape to host            │
│                                                             │
│  CREATE/UPDATE roles/rolebindings                          │
│  └── Can grant themselves more permissions                 │
│                                                             │
│  GET secrets                                               │
│  └── Can read all secrets (tokens, passwords)              │
│                                                             │
│  IMPERSONATE users/groups                                  │
│  └── Can act as any user                                   │
│                                                             │
│  EXEC into pods                                            │
│  └── Can run commands in any container                     │
│                                                             │
│  CREATE serviceaccounts + secrets                          │
│  └── Can create tokens for any service account             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The dangerous permissions in the diagram are dangerous because they connect RBAC to other control planes. Creating Pods is not only about creating Pods; it is about choosing a ServiceAccount, mounting volumes, requesting host access, selecting images, and triggering admission policy. Getting Secrets is not only about reading a single object; it can expose database passwords, registry credentials, and legacy service-account tokens. Impersonation is not only about debugging; it can turn one identity into many if the impersonation scope is broad.

> **Pause and predict**: A ServiceAccount has `create` permission on Pods but not `get` permission on Secrets. Can it still access Secrets in the namespace? Think through how a newly created Pod can mount a Secret even when the creating subject cannot read that Secret directly.

The answer depends on the surrounding controls, which is why RBAC must be evaluated with admission policy and namespace design. In many configurations, a subject that can create Pods can create a Pod spec that references a Secret as a volume or environment source, then read the data from inside the container. Kubernetes RBAC blocks the direct `get secrets` API request, but the workload path may still expose the data. Pod Security Standards, admission controllers, tight ServiceAccount choices, and namespace separation all help close that gap.

ServiceAccount design is where this becomes practical. Application Pods should not run with a default ServiceAccount that happens to receive broad permissions because someone wanted a quick fix. Deployment automation should have a dedicated identity, in a dedicated namespace when possible, with permissions limited to the resources it actually manages. Human users should normally receive access through groups rather than one-off user bindings, because group grants are easier to review and revoke when people change teams.

```yaml
# Create a ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app
  namespace: production
---
# Create a Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
---
# Bind the Role to the ServiceAccount
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-configmap-reader
  namespace: production
subjects:
- kind: ServiceAccount
  name: my-app
  namespace: production
roleRef:
  kind: Role
  name: configmap-reader
  apiGroup: rbac.authorization.k8s.io
---
# Use the ServiceAccount in a Pod
apiVersion: v1
kind: Pod
metadata:
  name: my-app
  namespace: production
spec:
  serviceAccountName: my-app
  # ...
```

This example is intentionally narrow. The application receives only `get` and `list` on ConfigMaps in its own namespace, which is enough for many configuration readers and not enough to mutate workloads, read Secrets, or inspect cluster infrastructure. If the application later needs another permission, the review should ask what code path requires it, whether the permission can be scoped to a named resource, and whether the workload should instead receive configuration through a safer delivery mechanism.

In production, least privilege also means planning for rotation and incident response. A narrowly scoped ServiceAccount token is easier to rotate because fewer workloads depend on it, and a narrowly scoped role is easier to reason about during containment. When a token is suspected of exposure, the platform team needs to answer which namespaces, resources, and actions were reachable. Broad wildcard roles turn that question into a cluster-wide investigation, while narrow roles let responders bound the incident quickly.

There is also a human workflow benefit. Developers are more willing to request precise access when the platform team responds quickly and explains the model. If every access request becomes a week-long negotiation, teams will search for shortcuts and shared credentials. A good RBAC program pairs strict grants with clear examples, reusable role templates, and fast review paths for common workflows. Least privilege succeeds when it is easier to do the right thing than to bypass the process.

## Patterns & Anti-Patterns

Good RBAC designs are boring to operate because their boundaries match team boundaries. A product team can inspect and deploy its own namespace without touching platform controllers. A monitoring service can read the objects needed for telemetry without owning the cluster. A release pipeline can update Deployments in staging without reading production Secrets. The design work is mostly in resisting shortcuts that collapse those boundaries during the first incident or release pressure.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| ClusterRole definition plus namespace RoleBindings | Multiple namespaces need the same namespaced permissions | One reusable permission definition avoids drift while each namespace grant remains explicit | Automate RoleBinding creation through GitOps so new namespaces do not silently miss required access |
| Group-based human access | Access belongs to a team rather than one person | Identity provider groups make onboarding and offboarding auditable | Review group-to-binding mappings during team changes and incident retrospectives |
| Dedicated ServiceAccount per workload class | Applications, controllers, and CI jobs have different trust levels | A compromised token exposes only the workload's actual permissions | Name ServiceAccounts after the workload and avoid sharing them between unrelated controllers |
| `k auth can-i` negative tests | Reviewing a new or changed binding | Testing denied actions catches additive grants that are easy to miss by reading one manifest | Keep representative checks in runbooks or CI policy tests for sensitive namespaces |

Anti-patterns usually appear when teams optimize for immediate success instead of future auditability. The most common version is granting `cluster-admin` to an application or pipeline because a deployment failed and nobody had time to identify the missing verb. Another version is writing `apiGroups: ["*"]`, `resources: ["*"]`, and `verbs: ["*"]` into a role because the author wants to avoid future support tickets. Those choices move complexity out of the YAML and into the incident response process, where it is much more expensive.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|-------------------|
| Binding `cluster-admin` to application ServiceAccounts | Any workload compromise becomes full cluster compromise | Create a custom Role for the exact resources the application touches |
| Using ClusterRoleBinding for one namespace | Access follows the subject into every namespace, including future ones | Use a RoleBinding that references a Role or reusable ClusterRole |
| Granting wildcards to avoid troubleshooting | Future resources and verbs become allowed without review | Start with observed required verbs and add narrowly after testing |
| Letting teams create aggregation labels freely | Aggregated roles may gain unexpected permissions | Protect aggregation labels with admission policy and code review |
| Sharing one deployment ServiceAccount across environments | A staging compromise may reach production permissions | Use separate identities and bindings per environment |

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using cluster-admin for apps | Way too much access | Create specific roles |
| Wildcards in production | Grants more than intended | Specify exact resources/verbs |
| ClusterRoleBinding for namespaced needs | Cluster-wide access when namespace is enough | Use RoleBinding |
| Not reviewing default SA | May have unintended permissions | Audit default SA bindings |
| Shared roles for different teams | Can't revoke individually | Team-specific roles |

The compact table above is useful as a quick review checklist, but it should not be the only review artifact for a serious change. A production RBAC review should include the requested workflow, the subject identity, the exact resources and verbs, the namespace or cluster scope, expected negative checks, and the rollback plan. If a role cannot be explained in those terms, it is usually too broad, too clever, or owned by the wrong team.

The strongest pattern across all of these examples is separation of duties. Humans, controllers, and pipelines should not share identities simply because they touch the same namespace. Read-only troubleshooting, deployment automation, secret management, and platform administration are different jobs, so they deserve different subjects and different bindings. When those duties are separated, a mistake in one workflow is less likely to grant power in another workflow, and audit logs are much easier to interpret.

Another durable pattern is treating RBAC manifests as production code. They should be reviewed, versioned, tested, and rolled back with the same care as application deployments. A one-line binding can be more sensitive than a hundred lines of application configuration because it changes who may alter the cluster. Git history also gives responders context during incidents: who approved the grant, what request it served, and which negative checks were expected to remain denied.

## Decision Framework

Use the binding scope as your first branch. If the subject needs to work in one namespace, begin with a Role and RoleBinding in that namespace. If several namespaces need the same namespaced permission set, define one ClusterRole and bind it separately in each namespace with RoleBindings. If the subject needs cluster-scoped resources or truly all namespaces, use a ClusterRole and consider a ClusterRoleBinding, but require stronger justification because the blast radius is larger.

If the subject needs one namespace only, use Role plus RoleBinding. If the same namespaced rules are needed in several namespaces, use ClusterRole plus one RoleBinding per namespace. If the subject needs cluster-scoped resources like nodes or namespaces, use ClusterRole plus a carefully reviewed ClusterRoleBinding. If the request includes role management, impersonation, binding, escalation, direct Pod creation, or broad Secret access, treat it as a platform-administration workflow even if the requester describes it as an application task.

After choosing scope, evaluate the verbs as escalation surfaces rather than labels. Read access to Pods and Events may be fine for troubleshooting, but read access to Secrets is credential exposure. Write access to Deployments may be acceptable for a deployment pipeline, but direct Pod creation could bypass higher-level controls. Role and RoleBinding mutation is administration, not application deployment. Impersonation and escalation are platform powers and should be rare enough that each grant has an owner and a recorded reason.

| Requirement | Prefer This | Avoid This | Review Question |
|-------------|-------------|------------|-----------------|
| Developers inspect workloads in `dev` | RoleBinding to `view` or a custom read Role | ClusterRoleBinding to `view` | Should they see every namespace or only their own? |
| CI updates Deployments in `staging` | Dedicated ServiceAccount with Deployment verbs in `staging` | Shared CI ServiceAccount with wildcard verbs | Can this token touch production if stolen? |
| Monitoring reads Pods in all namespaces | ClusterRoleBinding to narrow read ClusterRole | `cluster-admin` or broad `edit` | Does monitoring need Secrets, exec, or write verbs? |
| Team lead manages ConfigMaps and Secrets | Custom Role in the team namespace | Adding all team members to `admin` | Is secret management limited to the team boundary? |
| Operator watches custom resources | ClusterRole for required API groups | `resources: ["*"]` for future CRDs | Which CRDs are actually part of this controller? |

The best review habit is to write the denial cases before the allow cases. For example, if the request says "CI can deploy to staging," the negative cases might be "CI must not get production Secrets," "CI must not create ClusterRoleBindings," and "CI must not impersonate users." Running or documenting those negative `k auth can-i` checks forces the team to think about what success must not include. It also gives future reviewers a compact regression suite for the access model.

This framework should also consider time. Some access is durable because it represents a standing team responsibility, while other access is temporary because it supports a migration, incident, or one-time maintenance window. Kubernetes RBAC does not expire bindings by itself, so temporary grants need process support. Teams often solve this with GitOps pull requests that include removal dates, scheduled review issues, or automation that flags high-privilege bindings older than an approved window.

Finally, decide how you will observe the grant after it is applied. Audit logs can show whether a subject uses a sensitive permission, and alerting can highlight creation of ClusterRoleBindings, role changes with wildcards, or new bindings to privileged roles. Observation does not make an unsafe grant safe, but it helps validate assumptions and detect misuse. A permission that is both broad and never used is a strong candidate for removal. That evidence gives reviewers confidence to tighten access without guessing about production behavior.

### Component Reference

| Component | Purpose | Scope |
|-----------|---------|-------|
| **Role** | Define permissions | Namespace |
| **ClusterRole** | Define permissions | Cluster |
| **RoleBinding** | Grant role to subjects | Namespace |
| **ClusterRoleBinding** | Grant role to subjects | Cluster |

This reference table is simple, but it captures the difference that prevents many RBAC mistakes. Roles and ClusterRoles define permissions; bindings grant them. Roles and RoleBindings are namespaced; ClusterRoles and ClusterRoleBindings are cluster-scoped. The reusable pattern that confuses people is a namespaced RoleBinding pointing to a ClusterRole, which keeps the grant namespaced even though the role definition is stored at cluster scope.

## Did You Know?

- **RBAC is default-deny** - if no role grants permission, the action is denied, and there is no RBAC "deny" rule that can subtract access granted by another binding.

- **Role escalation protection exists** - to create a RoleBinding to a role, a subject needs either the `bind` verb on that role or all of the permissions contained in that role.

- **The `view` role deliberately excludes Secrets** - this design lets teams grant broad read access for troubleshooting without automatically exposing credentials, tokens, and private configuration values.

- **Wildcards aggregate over time** - using `resources: ["*"]` can grant access to future API resources and CustomResourceDefinitions that were not installed when the role was approved.

## Common Mistakes

The mistakes below are written from real review conversations, not from syntax trivia. In each case, the YAML often applies successfully, which makes the mistake harder to notice. The cluster accepts the configuration, the team unblocks its work, and the security problem appears only when a token is stolen, a namespace is added, or an auditor asks who can touch a sensitive resource.

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Binding `cluster-admin` to a workload ServiceAccount | The team is trying to make a failing deployment work quickly and does not know which verb is missing | Use `k auth can-i` and API audit events to find the missing permission, then create a narrow Role or ClusterRole |
| Using `resources: ["*"]` and `verbs: ["*"]` in production | Wildcards feel future-proof and reduce support requests during early development | Replace wildcards with named API groups, resources, and verbs; review again when new CRDs are introduced |
| Choosing ClusterRoleBinding for a one-namespace workflow | The author sees ClusterRole in an example and assumes the binding must also be cluster-scoped | Use a RoleBinding, even when it references a reusable ClusterRole, so the grant stays inside the namespace |
| Forgetting ServiceAccount namespace in a binding | ServiceAccount names look local, so authors bind the right name in the wrong namespace | Always specify `namespace` for ServiceAccount subjects and test the full `system:serviceaccount:namespace:name` identity |
| Treating `create pods` as ordinary write access | Pod creation sounds narrower than Deployment ownership, but Pods can mount Secrets and request risky settings | Prefer higher-level workload resources with admission controls, and restrict Pod creation in sensitive namespaces |
| Granting `impersonate`, `bind`, or `escalate` to application teams | Special verbs are misunderstood as debugging helpers instead of administrative powers | Reserve special verbs for platform automation with owner review, alerting, and explicit expiration where possible |
| Reviewing only one Role instead of effective access | RBAC grants are additive across users, groups, and ServiceAccounts | Review all RoleBindings and ClusterRoleBindings for the subject, then test both positive and negative `k auth can-i` cases |

## Quiz

<details><summary>Question 1: A development team needs read access to Deployments and Services across exactly five namespaces. Should you create five separate Roles or one ClusterRole, and how should you bind it?</summary>

Create one ClusterRole with `get`, `list`, and `watch` on Deployments and Services, then create one RoleBinding in each of the five namespaces that references that ClusterRole. This keeps the permission definition reusable while keeping each grant explicitly namespaced. A ClusterRoleBinding would be too broad because it would grant access in every namespace, including future namespaces that were not part of the request. Five separate Roles can work, but they are more likely to drift during later edits.

</details>

<details><summary>Question 2: During an audit, you find a CI ServiceAccount with `create pods` and `get secrets` in the same namespace. The team says both permissions are needed for deployments. What risk do you explain first?</summary>

The immediate risk is that the CI token can read credentials directly and may also create Pods that mount sensitive data or request dangerous runtime settings. Even if the team removed direct `get secrets`, Pod creation could still be an indirect path to secret exposure unless admission policy and namespace design prevent it. A safer design is a dedicated deployment identity with narrow verbs on Deployments, Services, and required ConfigMaps in the target namespace. Secret access should be separated, minimized, and tested with negative authorization checks.

</details>

<details><summary>Question 3: A ServiceAccount has the built-in `view` role through a RoleBinding and also has a second Role granting `get secrets`. What is the effective permission and why?</summary>

The ServiceAccount can read Secrets because Kubernetes RBAC is additive. The `view` role excludes Secrets, but that exclusion is not a deny rule and does not cancel another grant. The second Role contributes `get secrets` to the effective permission set, so the final decision allows the request. This is why reviewers must inspect all bindings for a subject rather than judging access from one familiar role name.

</details>

<details><summary>Question 4: A monitoring tool needs read-only access to Pods, Services, and Endpoints in all namespaces. When would you choose a ClusterRoleBinding instead of many RoleBindings?</summary>

Choose a ClusterRoleBinding when the tool is centrally operated, highly trusted, and genuinely needs coverage for all current and future namespaces. It is simpler to maintain and avoids missed telemetry when a new namespace appears. Choose per-namespace RoleBindings when some namespaces are sensitive enough to require explicit opt-in or separate approval. The tradeoff is operational simplicity versus tighter least-privilege boundaries.

</details>

<details><summary>Question 5: A contractor group must never receive `cluster-admin`, but RBAC has no deny rules. How do you enforce that policy?</summary>

You enforce it outside plain RBAC by controlling who can create or update ClusterRoleBindings and by using admission policy to reject bindings that attach `cluster-admin` to the contractor group. GitOps review can also block unsafe manifests before they reach the API server. Audit alerts should notify the platform team if a high-privilege binding appears despite the preventive controls. The key reasoning is that additive RBAC cannot express "never allow this subject," so another control plane must enforce the prohibition.

</details>

<details><summary>Question 6: An operator team wants to use aggregated ClusterRoles for a new CustomResourceDefinition. What security condition must be true before that design is safe?</summary>

Only trusted automation or administrators should be able to create ClusterRoles with labels selected by the aggregate role. Aggregation is powerful because matching labels cause rules to flow into the aggregate automatically, which means label control becomes permission control. If untrusted users can create labeled ClusterRoles, they may be able to add permissions to everyone bound to the aggregate role. The safe design protects aggregation labels with admission policy and code review.

</details>

<details><summary>Question 7: A developer can successfully run `k auth can-i get pods -n dev --as alice`, but production access is also returning yes unexpectedly. What should you check?</summary>

Check for ClusterRoleBindings that apply to Alice directly or to any group supplied with her authentication context. A namespaced RoleBinding in `dev` would not explain production access, so a broader binding is likely involved. Also check whether Alice belongs to a group such as `developers` that has a cluster-wide grant. The diagnosis should trace the subject, all matching groups, the referenced role, and the binding scope.

</details>

## Hands-On Exercise: RBAC Design

In this exercise, you will design and review an RBAC model for a small product team. The goal is not to memorize YAML; the goal is to practice explaining why each subject receives each verb at each scope. Work through the tasks in order, and for each task write down one action that should be allowed and one action that should be denied before you look at the solution.

**Scenario**: Design RBAC for a development team that owns the `dev` namespace, a team lead who handles sensitive configuration, and a CI/CD identity that deploys only to `staging`. The requirements below intentionally mix human and automation access so you can practice separating identities instead of giving everyone the same powerful role.

1. Developers can view all resources in the `dev` namespace
2. Developers can create/update/delete Deployments and Services in `dev`
3. Team lead can do everything developers can, plus manage ConfigMaps and Secrets
4. CI/CD service account needs to deploy to `staging` namespace

### Tasks

- [ ] Define the developer permission set for `dev`, and decide whether it belongs in a Role or ClusterRole.
- [ ] Define the team lead permission set, including why ConfigMap and Secret management should not be granted to every developer.
- [ ] Define the CI/CD deployment permission set for `staging`, keeping the ServiceAccount separate from human users.
- [ ] Create bindings for the `developers` group, the team lead user, and the CI/CD ServiceAccount.
- [ ] Write at least three positive `k auth can-i` checks and three negative checks that would prove the design does not grant accidental cluster-wide access.
- [ ] Review the final design for wildcard resources, wildcard verbs, direct Pod creation, Secret exposure, and ClusterRoleBinding usage.

<details>
<summary>Solution</summary>

```yaml
# Developer Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: dev
  name: developer
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["create", "update", "patch", "delete"]
---
# Team Lead Role (extends developer)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: dev
  name: team-lead
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["services", "configmaps", "secrets"]
  verbs: ["create", "update", "patch", "delete"]
---
# CI/CD Role for staging
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: staging
  name: deployer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["services", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
---
# Bindings
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: dev
  name: developers-binding
subjects:
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: dev
  name: team-lead-binding
subjects:
- kind: User
  name: lead@example.com
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: team-lead
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: staging
  name: cicd-binding
subjects:
- kind: ServiceAccount
  name: cicd-deployer
  namespace: cicd
roleRef:
  kind: Role
  name: deployer
  apiGroup: rbac.authorization.k8s.io
```

The solution follows the scenario but it is still worth reviewing critically. The developer and team-lead roles use read wildcards for namespace resources, which may be acceptable in a training exercise but should be narrowed in sensitive production namespaces. The CI/CD role avoids direct Pod creation and does not use a ClusterRoleBinding, which keeps the automation boundary closer to the stated deployment need. In a stricter environment, you would also separate secret management into a smaller role and require additional approval before binding it.

</details>

### Success Criteria

- [ ] Developer permissions are namespaced to `dev` and do not use a ClusterRoleBinding.
- [ ] Team lead permissions are broader than developer permissions but still namespaced to `dev`.
- [ ] CI/CD permissions are bound to a ServiceAccount and scoped to `staging`.
- [ ] The design includes negative checks for Secrets, ClusterRoleBindings, and production namespace access.
- [ ] The review identifies at least one place where the training solution could be narrowed for a real production cluster.

## Sources

- [Kubernetes RBAC authorization reference](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes authorization overview](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
- [Kubernetes ServiceAccount administration](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/)
- [Kubernetes ServiceAccount concepts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes admission controllers reference](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [kubectl auth can-i reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_auth/kubectl_auth_can-i/)
- [Kubernetes Node authorization](https://kubernetes.io/docs/reference/access-authn-authz/node/)
- [Kubernetes custom resources concepts](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Kubernetes RBAC API reference](https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/role-v1/)

## Next Module

[Module 3.3: Secrets Management](../module-3.3-secrets/) - Learn how to store, grant, rotate, and audit sensitive Kubernetes data without turning every read permission into credential exposure.
