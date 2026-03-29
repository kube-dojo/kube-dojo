---
title: "Module 2.1: RBAC Deep Dive"
slug: k8s/cks/part2-cluster-hardening/module-2.1-rbac-deep-dive
sidebar:
  order: 1
---
> **Complexity**: `[MEDIUM]` - Core security skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: CKA RBAC knowledge, ServiceAccounts basics

---

## Why This Module Matters

RBAC is the access control mechanism for Kubernetes. CKA taught you to create Roles and RoleBindings. CKS goes deeper: you must audit RBAC for over-permissioned accounts, understand escalation paths, and implement least privilege.

Misconfigured RBAC is a top Kubernetes vulnerability.

---

## RBAC Review

```
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

---

## Dangerous RBAC Patterns

### Pattern 1: Wildcard Permissions

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

### Pattern 2: Secrets Access

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

### Pattern 3: RBAC Escalation

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
# - Can grant themselves cluster-admin
# - Privilege escalation attack
# - Only admins should modify RBAC
```

### Pattern 4: Pod Creation with Privileges

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
# - Can create privileged pods
# - Can mount service account tokens
# - Can escape container to node
# - Needs Pod Security to be safe
```

---

## Least Privilege Examples

### Good: Specific Resource Access

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

### Good: Resource Names Restriction

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

### Good: Subresources Only

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

---

## Auditing RBAC

### Find Overpermissive Roles

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

### Check User Permissions

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

### Find Bindings to Dangerous Roles

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

---

## RBAC Escalation Prevention

```
┌─────────────────────────────────────────────────────────────┐
│              RBAC ESCALATION PATHS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Direct Escalation:                                        │
│  ─────────────────────────────────────────────────────────  │
│  1. Create/update ClusterRoleBindings                      │
│     → Bind self to cluster-admin                           │
│                                                             │
│  2. Create/update ClusterRoles                             │
│     → Add * permissions                                    │
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

### The Escalate and Bind Verbs

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

---

## Best Practices

```
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

---

## Real Exam Scenarios

### Scenario 1: Reduce Permissions

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

### Scenario 2: Find and Remove Dangerous Binding

```bash
# Find who has cluster-admin
kubectl get clusterrolebindings -o json | jq -r '
  .items[] |
  select(.roleRef.name == "cluster-admin") |
  .metadata.name'

# Remove inappropriate binding
kubectl delete clusterrolebinding developer-admin
```

### Scenario 3: Create Least-Privilege Role

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

---

## RBAC Debugging

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

---

## Did You Know?

- **Kubernetes doesn't have a 'deny' rule.** RBAC is purely additive—you can only grant permissions, not explicitly deny them. To restrict access, simply don't grant it.

- **The 'system:masters' group** is hardcoded to have cluster-admin. You can't remove it via RBAC. If someone is in this group, they have full access.

- **'escalate' and 'bind' verbs** were added specifically to prevent privilege escalation. Before Kubernetes 1.12, anyone who could create RoleBindings could bind to cluster-admin!

- **Aggregated ClusterRoles** (like admin, edit, view) automatically include rules from other roles labeled with the aggregation label. This is how CRDs extend built-in roles.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Giving cluster-admin to developers | Full access to everything | Use edit or custom roles |
| Using ClusterRoles when Role works | Excessive scope | Prefer namespace-scoped |
| Wildcards in production | No access control | List specific permissions |
| Not auditing bindings | Unknown who has access | Regular RBAC reviews |
| Ignoring ServiceAccount defaults | Default SA may have permissions | Disable auto-mount, use specific SA |

---

## Quiz

1. **What's the difference between Role and ClusterRole?**
   <details>
   <summary>Answer</summary>
   Role is namespace-scoped and can only grant permissions within a namespace. ClusterRole is cluster-wide and can grant permissions on cluster-scoped resources (like nodes) or be used with RoleBinding for reusable namespace-scoped permissions.
   </details>

2. **How do you check what permissions a ServiceAccount has?**
   <details>
   <summary>Answer</summary>
   `kubectl auth can-i --list --as=system:serviceaccount:<namespace>:<sa-name>` - This lists all permissions the ServiceAccount has.
   </details>

3. **Why are wildcard (*) permissions dangerous?**
   <details>
   <summary>Answer</summary>
   Wildcards grant access to all resources, verbs, or API groups—including secrets, RBAC resources, and sensitive system components. They effectively grant cluster-admin level access.
   </details>

4. **What are the 'bind' and 'escalate' verbs for?**
   <details>
   <summary>Answer</summary>
   These are privilege escalation prevention verbs. 'bind' allows creating bindings to roles with permissions you don't have. 'escalate' allows modifying roles to add permissions you don't have. Both should be tightly controlled.
   </details>

---

## Hands-On Exercise

**Task**: Audit and fix overpermissive RBAC.

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

# Task 2: Check if it can read secrets (it shouldn't!)
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

**Success criteria**: ServiceAccount can only manage pods in its own namespace.

---

## Summary

**RBAC Security Principles**:
- Least privilege always
- No wildcards in production
- Prefer Role over ClusterRole
- Use resourceNames when possible

**Dangerous Patterns**:
- Wildcard permissions (*, *)
- Secrets access without need
- RBAC modification rights
- bind/escalate verbs

**Auditing Commands**:
- `kubectl auth can-i --list --as=...`
- `kubectl auth who-can <verb> <resource>`
- Check ClusterRoleBindings to cluster-admin

**Exam Tips**:
- Know how to reduce permissions
- Practice finding overpermissive roles
- Understand escalation paths

---

## Next Module

[Module 2.2: ServiceAccount Security](../module-2.2-serviceaccount-security/) - Hardening ServiceAccounts and token management.
