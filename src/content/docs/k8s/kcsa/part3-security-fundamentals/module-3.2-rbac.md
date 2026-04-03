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

1. **What's the difference between a Role and a ClusterRole?**
   <details>
   <summary>Answer</summary>
   A Role is namespace-scoped and can only grant permissions within a single namespace. A ClusterRole is cluster-scoped and can grant permissions to cluster-wide resources or be used across multiple namespaces.
   </details>

2. **Can a RoleBinding reference a ClusterRole?**
   <details>
   <summary>Answer</summary>
   Yes. A RoleBinding can bind a ClusterRole to subjects within its namespace. This grants the ClusterRole's permissions but only within the RoleBinding's namespace. This is useful for reusable roles.
   </details>

3. **What permissions does the built-in `view` ClusterRole grant?**
   <details>
   <summary>Answer</summary>
   Read-only access to most namespace-scoped resources (get, list, watch). It explicitly excludes secrets and does not include any write permissions.
   </details>

4. **Why is granting `create pods` permission dangerous?**
   <details>
   <summary>Answer</summary>
   A user who can create pods can potentially create privileged pods, mount host filesystems, or access any secret by mounting them as volumes. This can lead to container escape and cluster compromise.
   </details>

5. **How does Kubernetes RBAC handle deny rules?**
   <details>
   <summary>Answer</summary>
   Kubernetes RBAC doesn't have deny rules. It's additive - permissions are granted, never revoked. To restrict access, you remove the granting rule or don't create it. If no rule grants permission, access is denied by default.
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
