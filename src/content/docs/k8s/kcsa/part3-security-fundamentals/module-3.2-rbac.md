---
title: "Module 3.2: RBAC Fundamentals"
slug: k8s/kcsa/part3-security-fundamentals/module-3.2-rbac
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: [Module 3.1: Pod Security](../module-3.1-pod-security/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** RBAC policies for over-permissioned roles and privilege escalation risks
2. **Assess** whether a given Role or ClusterRole follows the principle of least privilege
3. **Identify** dangerous RBAC patterns: wildcard verbs, cluster-admin bindings, escalation paths
4. **Explain** how Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings interact

---

## Why This Module Matters

RBAC (Role-Based Access Control) is Kubernetes' primary authorization mechanism. It determines who can do what in your cluster. Misconfigured RBAC is one of the most common security issues in Kubernetes—either too permissive (security risk) or too restrictive (operational issues).

Understanding RBAC is essential for both the exam and real-world Kubernetes administration.

---

## RBAC Concepts

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

---

## Roles vs ClusterRoles

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

---

> **Stop and think**: If RBAC only allows additive permissions (no deny rules), how would you prevent a specific user from accessing Secrets in a namespace where they have a broad Role?

## Role Definition

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

### Rule Components

| Component | Description | Examples |
|-----------|-------------|----------|
| **apiGroups** | API group containing resource | `""` (core), `"apps"`, `"networking.k8s.io"` |
| **resources** | Resource types | `"pods"`, `"deployments"`, `"secrets"` |
| **verbs** | Actions allowed | `"get"`, `"list"`, `"create"`, `"delete"` |
| **resourceNames** | Specific resource names (optional) | `["my-configmap"]` |

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

---

## Role Bindings

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

---

## Built-in Roles

Kubernetes includes default ClusterRoles:

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

---

## RBAC Best Practices

### Least Privilege

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

> **Pause and predict**: A ServiceAccount has `create` permission on Pods but not on Secrets. Can it still access secrets in the namespace? Think about what a newly created pod can do.

### Dangerous Permissions

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

---

## ServiceAccount RBAC

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

---

## Aggregated ClusterRoles

ClusterRoles can aggregate other ClusterRoles:

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

The built-in `admin`, `edit`, and `view` roles use aggregation.

> **Stop and think**: Aggregated ClusterRoles automatically include rules from any ClusterRole with a matching label. What security risk does this introduce if an attacker can create ClusterRoles with arbitrary labels?

---

## Did You Know?

- **RBAC is default-deny** - if no role grants permission, the action is denied. There's no "deny" rule in RBAC.

- **Role escalation protection** - you can't grant permissions you don't have. To create a RoleBinding to a Role, you need either (a) the `bind` verb on that role, or (b) all the permissions in that role.

- **The `view` role doesn't include secrets** by design. This lets you give broad read access without exposing sensitive data.

- **Wildcards aggregate** - using `resources: ["*"]` grants access to resources that don't exist yet (future CRDs).

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using cluster-admin for apps | Way too much access | Create specific roles |
| Wildcards in production | Grants more than intended | Specify exact resources/verbs |
| ClusterRoleBinding for namespaced needs | Cluster-wide access when namespace is enough | Use RoleBinding |
| Not reviewing default SA | May have unintended permissions | Audit default SA bindings |
| Shared roles for different teams | Can't revoke individually | Team-specific roles |

---

## Quiz

1. **A new team needs read access to Deployments and Services across five namespaces. Should you create five separate Roles or one ClusterRole? What binding strategy would you use, and why?**
   <details>
   <summary>Answer</summary>
   Create one ClusterRole with get/list/watch on Deployments and Services, then create five RoleBindings (one per namespace) referencing that ClusterRole. This avoids duplicating the Role definition while keeping access scoped to specific namespaces. Using a ClusterRoleBinding would be wrong — it grants cluster-wide access. The RoleBinding+ClusterRole pattern gives you reusable permission definitions with namespace-scoped access control.
   </details>

2. **During a security audit, you discover a ServiceAccount with `create` permission on Pods and `get` permission on Secrets. The team says they need pod creation for their CI/CD pipeline. Explain the privilege escalation risk and propose a safer approach.**
   <details>
   <summary>Answer</summary>
   With `create pods` permission, the CI/CD ServiceAccount can create a pod that mounts any secret in the namespace as a volume — effectively escalating from "get specific secrets" to "read all secrets." It can also create privileged pods, enabling container escape. Safer approach: use a dedicated namespace for CI/CD with only the secrets it needs, enforce Pod Security Standards (Restricted) to prevent privilege escalation, and restrict the ServiceAccount to only `create` Deployments (not raw Pods) so that admission controllers can validate the pod spec.
   </details>

3. **The built-in `view` ClusterRole deliberately excludes access to Secrets. A developer binds `view` to their ServiceAccount but also creates a second Role granting `get secrets`. What is the resulting effective permission, and what RBAC principle does this demonstrate?**
   <details>
   <summary>Answer</summary>
   The ServiceAccount gets both the `view` permissions AND `get secrets` because RBAC is additive — the union of all granted permissions applies. There are no deny rules in Kubernetes RBAC. This demonstrates why you must audit all bindings for a subject, not just individual roles. The `view` ClusterRole's exclusion of secrets is a design choice, not an enforcement mechanism. Any additional Role or ClusterRole binding can override this intent. Prevention: restrict who can create Roles and RoleBindings via RBAC, and audit bindings regularly.
   </details>

4. **A cluster has 30 namespaces. You need to grant a monitoring tool read-only access to pods, services, and endpoints in ALL namespaces. Compare two approaches: (a) a ClusterRoleBinding to a ClusterRole, vs (b) 30 RoleBindings to a ClusterRole. When would you choose each?**
   <details>
   <summary>Answer</summary>
   Approach (a) is simpler — one ClusterRoleBinding covers all namespaces including future ones. Choose this when the monitoring tool legitimately needs cluster-wide access and you trust it. Approach (b) requires maintaining 30 bindings but provides explicit control — new namespaces are NOT automatically included, and you can revoke access to specific namespaces. Choose this when some namespaces contain sensitive workloads that monitoring should not access, or when compliance requires explicit per-namespace authorization. The trade-off is operational simplicity vs. security granularity.
   </details>

5. **You want to prevent a specific group from ever being granted `cluster-admin`. Since RBAC has no deny rules, what strategies could you use to enforce this policy?**
   <details>
   <summary>Answer</summary>
   Since RBAC is additive-only, you cannot deny permissions directly. Strategies: (1) Use an admission controller (Kyverno or OPA/Gatekeeper) to block creation of ClusterRoleBindings that bind `cluster-admin` to that group; (2) Restrict who can create/modify ClusterRoleBindings via RBAC — only a small set of admins should have `create` and `update` on `clusterrolebindings`; (3) Use audit logging to alert when cluster-admin bindings are created and trigger automated remediation; (4) Implement a policy-as-code approach where RBAC manifests are reviewed in Git before applying.
   </details>

---

## Hands-On Exercise: RBAC Design

**Scenario**: Design RBAC for a development team with these requirements:

1. Developers can view all resources in the `dev` namespace
2. Developers can create/update/delete Deployments and Services in `dev`
3. Team lead can do everything developers can, plus manage ConfigMaps and Secrets
4. CI/CD service account needs to deploy to `staging` namespace

**Create the RBAC resources:**

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

</details>

---

## Summary

RBAC is Kubernetes' authorization system:

| Component | Purpose | Scope |
|-----------|---------|-------|
| **Role** | Define permissions | Namespace |
| **ClusterRole** | Define permissions | Cluster |
| **RoleBinding** | Grant role to subjects | Namespace |
| **ClusterRoleBinding** | Grant role to subjects | Cluster |

Best practices:
- Follow least privilege
- Avoid wildcards (`*`)
- Prefer namespace-scoped roles
- Be careful with pod create, secrets access, and impersonation
- Audit RBAC regularly

---

## Next Module

[Module 3.3: Secrets Management](../module-3.3-secrets/) - How to securely handle sensitive data in Kubernetes.
