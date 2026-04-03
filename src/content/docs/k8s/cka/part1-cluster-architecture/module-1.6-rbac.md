---
title: "Module 1.6: RBAC - Role-Based Access Control"
slug: k8s/cka/part1-cluster-architecture/module-1.6-rbac
sidebar:
  order: 7
lab:
  id: cka-1.6-rbac
  url: https://killercoda.com/kubedojo/scenario/cka-1.6-rbac
  duration: "45 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Common exam topic
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 1.1 (Control Plane), understanding of namespaces

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Configure** Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings for least-privilege access
- **Debug** "forbidden" errors by tracing the RBAC chain (user → binding → role → permission)
- **Design** an RBAC scheme for a multi-team cluster with namespace isolation
- **Audit** existing RBAC rules to find overly permissive access (wildcard verbs, cluster-admin bindings)

---

## Why This Module Matters

In a real cluster, you don't want everyone to have admin access. Developers should deploy their apps but not delete production namespaces. CI/CD systems should manage deployments but not read secrets. Monitoring tools should read metrics but not modify resources.

RBAC (Role-Based Access Control) solves this. It's how Kubernetes answers: "Who can do what to which resources?"

The CKA exam regularly tests RBAC. You'll be asked to create Roles, ClusterRoles, and bind them to users or ServiceAccounts. Get comfortable with these concepts—they're essential for security and daily operations.

> **The Security Guard Analogy**
>
> Think of RBAC like a building's security system. A **Role** is like an access badge type—"Developer Badge" can access floors 2-3, "Admin Badge" can access all floors. A **RoleBinding** is giving someone a specific badge—"Alice gets a Developer Badge." The security system (API server) checks the badge before allowing entry to any floor (resource).

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand RBAC concepts (Roles, ClusterRoles, Bindings)
- Create Roles and ClusterRoles
- Bind roles to users, groups, and ServiceAccounts
- Test permissions with `kubectl auth can-i`
- Debug RBAC issues

---

## Part 1: RBAC Concepts

### 1.1 The Four RBAC Resources

| Resource | Scope | Purpose |
|----------|-------|---------|
| **Role** | Namespace | Grants permissions within a namespace |
| **ClusterRole** | Cluster | Grants permissions cluster-wide |
| **RoleBinding** | Namespace | Binds Role/ClusterRole to subjects in a namespace |
| **ClusterRoleBinding** | Cluster | Binds ClusterRole to subjects cluster-wide |

### 1.2 How RBAC Works

```
┌────────────────────────────────────────────────────────────────┐
│                        RBAC Flow                                │
│                                                                 │
│   Subject                Role                  Resources        │
│   (Who?)                 (What permissions?)   (Which things?)  │
│                                                                 │
│   ┌─────────┐           ┌──────────────┐      ┌─────────────┐  │
│   │  User   │           │    Role      │      │   pods      │  │
│   │  Alice  │◄─────────►│  verbs:      │─────►│   services  │  │
│   └─────────┘   Bound   │  - get       │      │   secrets   │  │
│                  via    │  - list      │      └─────────────┘  │
│   ┌─────────┐  Binding  │  - create    │                       │
│   │ Service │           └──────────────┘                       │
│   │ Account │                                                   │
│   └─────────┘                                                   │
│                                                                 │
│   ┌─────────┐                                                   │
│   │  Group  │                                                   │
│   └─────────┘                                                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Subjects: Who Gets Access

- **User**: Human identity (managed outside Kubernetes)
- **Group**: Collection of users
- **ServiceAccount**: Identity for pods/applications

### 1.4 Verbs: What Actions Are Allowed

| Verb | Description |
|------|-------------|
| `get` | Read a single resource |
| `list` | List resources (get all) |
| `watch` | Watch for changes |
| `create` | Create new resources |
| `update` | Modify existing resources |
| `patch` | Partially modify resources |
| `delete` | Delete resources |
| `deletecollection` | Delete multiple resources |

Common verb groups:
- **Read-only**: `get`, `list`, `watch`
- **Read-write**: `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`
- **Full control**: `*` (all verbs)

---

## Part 2: Roles and ClusterRoles

### 2.1 Creating a Role (Namespace-Scoped)

```yaml
# role-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
  - apiGroups: [""]          # "" = core API group (pods, services, etc.)
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

```bash
# Apply the Role
kubectl apply -f role-pod-reader.yaml

# Or create imperatively
kubectl create role pod-reader \
  --verb=get,list,watch \
  --resource=pods \
  -n default
```

### 2.2 Creating a ClusterRole (Cluster-Scoped)

```yaml
# clusterrole-node-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch"]
```

```bash
# Apply
kubectl apply -f clusterrole-node-reader.yaml

# Or imperatively
kubectl create clusterrole node-reader \
  --verb=get,list,watch \
  --resource=nodes
```

### 2.3 Multiple Rules

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: dev
rules:
  # Pods: full access
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec"]
    verbs: ["*"]

  # Deployments: full access
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["*"]

  # Services: create and view
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list", "create", "delete"]

  # ConfigMaps: read only
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]

  # Secrets: no access (not listed = denied)
```

### 2.4 API Groups Reference

| API Group | Resources |
|-----------|-----------|
| `""` (core) | pods, services, configmaps, secrets, namespaces, nodes, persistentvolumes |
| `apps` | deployments, replicasets, statefulsets, daemonsets |
| `batch` | jobs, cronjobs |
| `networking.k8s.io` | networkpolicies, ingresses |
| `rbac.authorization.k8s.io` | roles, clusterroles, rolebindings, clusterrolebindings |
| `storage.k8s.io` | storageclasses, volumeattachments |

```bash
# Find the API group for any resource
kubectl api-resources | grep deployment
# NAME         SHORTNAMES   APIVERSION   NAMESPACED   KIND
# deployments  deploy       apps/v1      true         Deployment
#                           ^^^^
#                           API group is "apps"
```

> **Gotcha: Core API Group**
>
> The core API group is an empty string `""`. Resources like pods, services, configmaps use `apiGroups: [""]`, not `apiGroups: ["core"]`.

---

## Part 3: RoleBindings and ClusterRoleBindings

### 3.1 RoleBinding (Namespace-Scoped)

Binds a Role or ClusterRole to subjects within a namespace:

```yaml
# rolebinding-alice-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: alice-pod-reader
  namespace: default
subjects:
  - kind: User
    name: alice
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
# Imperative command
kubectl create rolebinding alice-pod-reader \
  --role=pod-reader \
  --user=alice \
  -n default
```

### 3.2 ClusterRoleBinding (Cluster-Scoped)

Binds a ClusterRole to subjects cluster-wide:

```yaml
# clusterrolebinding-bob-node-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: bob-node-reader
subjects:
  - kind: User
    name: bob
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
# Imperative command
kubectl create clusterrolebinding bob-node-reader \
  --clusterrole=node-reader \
  --user=bob
```

### 3.3 Binding to Multiple Subjects

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-team-access
  namespace: development
subjects:
  # Bind to a user
  - kind: User
    name: alice
    apiGroup: rbac.authorization.k8s.io

  # Bind to a group
  - kind: Group
    name: developers
    apiGroup: rbac.authorization.k8s.io

  # Bind to a ServiceAccount
  - kind: ServiceAccount
    name: cicd-deployer
    namespace: development
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

### 3.4 Using ClusterRole in RoleBinding

A powerful pattern: define a ClusterRole once, bind it in specific namespaces:

```yaml
# Use the built-in "edit" ClusterRole in the "production" namespace only
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: alice-edit-production
  namespace: production
subjects:
  - kind: User
    name: alice
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole     # Using ClusterRole
  name: edit            # Built-in ClusterRole
  apiGroup: rbac.authorization.k8s.io

# Alice can edit resources in "production" namespace only
```

---

## Part 4: ServiceAccounts

### 4.1 What Are ServiceAccounts?

ServiceAccounts provide identity for pods. When a pod runs, it can use its ServiceAccount's permissions to talk to the API server.

```bash
# List ServiceAccounts
kubectl get serviceaccounts
kubectl get sa

# Every namespace has a "default" ServiceAccount
kubectl get sa default -o yaml
```

### 4.2 Creating a ServiceAccount

```bash
# Create a ServiceAccount
kubectl create serviceaccount myapp-sa

# Or with YAML
cat > myapp-sa.yaml << 'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: default
EOF
kubectl apply -f myapp-sa.yaml
```

### 4.3 Binding Roles to ServiceAccounts

```bash
# Create a Role
kubectl create role pod-reader \
  --verb=get,list,watch \
  --resource=pods

# Bind it to the ServiceAccount
kubectl create rolebinding myapp-pod-reader \
  --role=pod-reader \
  --serviceaccount=default:myapp-sa
#                  ^^^^^^^^^^^^^^^^^
#                  namespace:name format
```

### 4.4 Using ServiceAccount in a Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  serviceAccountName: myapp-sa    # Use this ServiceAccount
  containers:
  - name: myapp
    image: nginx
```

The pod now has the permissions granted to `myapp-sa`.

> **Did You Know?**
>
> By default, pods use the `default` ServiceAccount in their namespace. This account typically has no permissions. Always create dedicated ServiceAccounts with minimal required permissions.

---

## Part 5: Built-in ClusterRoles

Kubernetes comes with useful ClusterRoles:

| ClusterRole | Permissions |
|-------------|-------------|
| `cluster-admin` | Full access to everything (superuser) |
| `admin` | Full access within a namespace |
| `edit` | Read/write most resources, no RBAC |
| `view` | Read-only access to most resources |

```bash
# See all built-in ClusterRoles
kubectl get clusterroles | grep -v "^system:"

# Inspect a ClusterRole
kubectl describe clusterrole edit
```

### Using Built-in ClusterRoles

```bash
# Give alice admin access to namespace "myapp"
kubectl create rolebinding alice-admin \
  --clusterrole=admin \
  --user=alice \
  -n myapp

# Give bob view access to namespace "production"
kubectl create rolebinding bob-view \
  --clusterrole=view \
  --user=bob \
  -n production
```

---

## Part 6: Testing Permissions

### 6.1 kubectl auth can-i

Check if you (or someone else) can perform an action:

```bash
# Check your own permissions
kubectl auth can-i create pods
kubectl auth can-i delete deployments
kubectl auth can-i '*' '*'  # Am I admin?

# Check in a specific namespace
kubectl auth can-i create pods -n production

# Check for another user (requires admin)
kubectl auth can-i create pods --as=alice
kubectl auth can-i delete nodes --as=bob

# Check for a ServiceAccount
kubectl auth can-i list secrets --as=system:serviceaccount:default:myapp-sa
```

### 6.2 List All Permissions

```bash
# What can I do in this namespace?
kubectl auth can-i --list

# What can alice do?
kubectl auth can-i --list --as=alice

# What can a ServiceAccount do?
kubectl auth can-i --list --as=system:serviceaccount:default:myapp-sa
```

### 6.3 Debugging Permission Denied

```bash
# Error: pods is forbidden
kubectl get pods
# Error: User "alice" cannot list resource "pods" in API group "" in namespace "default"

# Debug steps:
# 1. Check what permissions the user has
kubectl auth can-i --list --as=alice

# 2. Check what roles are bound to the user
kubectl get rolebindings -A -o wide | grep alice
kubectl get clusterrolebindings -o wide | grep alice

# 3. Check the role's rules
kubectl describe role <role-name> -n <namespace>
kubectl describe clusterrole <clusterrole-name>
```

> **War Story: The 403 Mystery**
>
> An engineer spent hours debugging why their CI/CD pipeline couldn't deploy. `kubectl auth can-i` showed permissions were correct. The issue? The ServiceAccount was in namespace `cicd`, but the RoleBinding was in namespace `production` with a typo: `namespace: prduction`. One missing letter, hours of debugging. Always double-check namespaces in bindings.

---

## Part 7: Common RBAC Patterns

### 7.1 Developer Access

```bash
# Create namespace
kubectl create namespace development

# Create ServiceAccount
kubectl create serviceaccount developer -n development

# Bind edit ClusterRole (read/write most resources)
kubectl create rolebinding developer-edit \
  --clusterrole=edit \
  --serviceaccount=development:developer \
  -n development
```

### 7.2 Read-Only Monitoring

```bash
# ServiceAccount for monitoring tools
kubectl create serviceaccount monitoring -n monitoring

# Cluster-wide read access
kubectl create clusterrolebinding monitoring-view \
  --clusterrole=view \
  --serviceaccount=monitoring:monitoring
```

### 7.3 CI/CD Deployer

```bash
# Create role for deployments only
kubectl create role deployer \
  --verb=get,list,watch,create,update,patch,delete \
  --resource=deployments,services,configmaps \
  -n production

# Bind to CI/CD ServiceAccount
kubectl create rolebinding cicd-deployer \
  --role=deployer \
  --serviceaccount=cicd:pipeline \
  -n production
```

---

## Part 8: Exam Scenarios

### 8.1 Quick RBAC Creation

```bash
# Task: Create a Role that can get, list, and watch pods and services in namespace "app"

kubectl create role app-reader \
  --verb=get,list,watch \
  --resource=pods,services \
  -n app

# Task: Bind the role to user "john"

kubectl create rolebinding john-app-reader \
  --role=app-reader \
  --user=john \
  -n app

# Verify
kubectl auth can-i get pods -n app --as=john
# yes
kubectl auth can-i delete pods -n app --as=john
# no
```

### 8.2 ServiceAccount with Cluster Access

```bash
# Task: Create ServiceAccount "dashboard" that can list pods across all namespaces

kubectl create serviceaccount dashboard -n kube-system

kubectl create clusterrole pod-list \
  --verb=list \
  --resource=pods

kubectl create clusterrolebinding dashboard-pod-list \
  --clusterrole=pod-list \
  --serviceaccount=kube-system:dashboard
```

---

## Did You Know?

- **RBAC is additive**. There's no "deny" rule. If any Role grants a permission, it's allowed. You can't explicitly block access—you can only not grant it.

- **Aggregated ClusterRoles** let you combine multiple ClusterRoles. The built-in `admin`, `edit`, and `view` roles are aggregated—additional rules can be added to them.

- **system:* ClusterRoles** are for internal Kubernetes components. Don't modify them unless you know what you're doing.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Wrong apiGroup | Role doesn't grant access | Check `kubectl api-resources` for correct group |
| Missing namespace in binding | Wrong permissions | Always verify `-n namespace` |
| Forgetting ServiceAccount namespace | Binding doesn't work | Use `namespace:name` format |
| Using Role for cluster resources | Can't access nodes, PVs | Use ClusterRole for cluster-scoped resources |
| Empty apiGroup not quoted | YAML error | Use `apiGroups: [""]` with quotes |
| Missing `create` verb on exec/attach subresources | `kubectl exec` silently fails (K8s 1.35+) | Add `create` verb to `pods/exec`, `pods/attach`, `pods/portforward` — see note below |

> **K8s 1.35 Breaking Change: WebSocket Streaming RBAC**
>
> Starting in Kubernetes 1.35, `kubectl exec`, `attach`, and `port-forward` use WebSocket connections that require the **`create`** verb on the relevant subresource (e.g., `pods/exec`). Previously, only `get` was needed. Existing RBAC policies that grant `get pods/exec` will **silently fail** — commands hang or return permission errors. Audit your ClusterRoles and Roles:
>
> ```yaml
> # OLD (broken in 1.35+):
> - resources: ["pods/exec"]
>   verbs: ["get"]
>
> # FIXED:
> - resources: ["pods/exec", "pods/attach", "pods/portforward"]
>   verbs: ["get", "create"]
> ```

---

## Quiz

1. **What's the difference between Role and ClusterRole?**
   <details>
   <summary>Answer</summary>
   A **Role** grants permissions within a specific namespace. A **ClusterRole** grants permissions cluster-wide or for cluster-scoped resources (like Nodes). ClusterRoles can also be bound in a single namespace using a RoleBinding.
   </details>

2. **Can you bind a ClusterRole using a RoleBinding?**
   <details>
   <summary>Answer</summary>
   Yes! This is a common pattern. When you bind a ClusterRole with a RoleBinding, the permissions only apply within that namespace. This lets you define permissions once (ClusterRole) and grant them selectively (RoleBinding per namespace).
   </details>

3. **A pod needs to list Services in its namespace. What do you create?**
   <details>
   <summary>Answer</summary>
   1. Create a ServiceAccount
   2. Create a Role with `verbs: ["list"]` and `resources: ["services"]`
   3. Create a RoleBinding binding the Role to the ServiceAccount
   4. Set `serviceAccountName` in the pod spec
   </details>

4. **How do you check if user "alice" can delete pods in namespace "production"?**
   <details>
   <summary>Answer</summary>
   `kubectl auth can-i delete pods -n production --as=alice`

   This impersonates alice and checks her permissions against the RBAC rules.
   </details>

---

## Hands-On Exercise

**Task**: Set up RBAC for a development team.

**Steps**:

1. **Create a namespace**:
```bash
kubectl create namespace dev-team
```

2. **Create a ServiceAccount**:
```bash
kubectl create serviceaccount dev-sa -n dev-team
```

3. **Create a Role for developers**:
```bash
kubectl create role developer \
  --verb=get,list,watch,create,update,delete \
  --resource=pods,deployments,services,configmaps \
  -n dev-team
```

4. **Bind the Role to the ServiceAccount**:
```bash
kubectl create rolebinding dev-sa-developer \
  --role=developer \
  --serviceaccount=dev-team:dev-sa \
  -n dev-team
```

5. **Test the permissions**:
```bash
# Test as the ServiceAccount
kubectl auth can-i get pods -n dev-team \
  --as=system:serviceaccount:dev-team:dev-sa
# yes

kubectl auth can-i delete pods -n dev-team \
  --as=system:serviceaccount:dev-team:dev-sa
# yes

kubectl auth can-i get secrets -n dev-team \
  --as=system:serviceaccount:dev-team:dev-sa
# no (we didn't grant access to secrets)

kubectl auth can-i get pods -n default \
  --as=system:serviceaccount:dev-team:dev-sa
# no (role only applies in dev-team namespace)
```

6. **Create a pod using the ServiceAccount**:
```bash
cat > dev-pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: dev-shell
  namespace: dev-team
spec:
  serviceAccountName: dev-sa
  containers:
  - name: shell
    image: bitnami/kubectl
    command: ["sleep", "infinity"]
EOF

kubectl apply -f dev-pod.yaml
```

7. **Test from inside the pod**:
```bash
kubectl exec -it dev-shell -n dev-team -- /bin/bash

# Inside the pod:
kubectl get pods              # Should work
kubectl get secrets           # Should fail (forbidden)
kubectl get pods -n default   # Should fail (forbidden)
exit
```

8. **Add read-only cluster access** (bonus):
```bash
kubectl create clusterrolebinding dev-sa-view \
  --clusterrole=view \
  --serviceaccount=dev-team:dev-sa

# Now the ServiceAccount can read resources cluster-wide
kubectl auth can-i get pods -n default \
  --as=system:serviceaccount:dev-team:dev-sa
# yes (but read-only)
```

9. **Cleanup**:
```bash
kubectl delete namespace dev-team
kubectl delete clusterrolebinding dev-sa-view
rm dev-pod.yaml
```

**Success Criteria**:
- [ ] Can create Roles and ClusterRoles
- [ ] Can create RoleBindings and ClusterRoleBindings
- [ ] Can bind to Users, Groups, and ServiceAccounts
- [ ] Can test permissions with `kubectl auth can-i`
- [ ] Understand namespace vs cluster scope

---

## Practice Drills

### Drill 1: RBAC Speed Test (Target: 3 minutes)

Create RBAC resources as fast as possible:

```bash
# Create namespace
kubectl create ns rbac-drill

# Create ServiceAccount
kubectl create sa drill-sa -n rbac-drill

# Create Role (read pods)
kubectl create role pod-reader --verb=get,list,watch --resource=pods -n rbac-drill

# Create RoleBinding
kubectl create rolebinding drill-binding --role=pod-reader --serviceaccount=rbac-drill:drill-sa -n rbac-drill

# Test
kubectl auth can-i get pods -n rbac-drill --as=system:serviceaccount:rbac-drill:drill-sa

# Cleanup
kubectl delete ns rbac-drill
```

### Drill 2: Permission Testing (Target: 5 minutes)

```bash
kubectl create ns perm-test
kubectl create sa test-sa -n perm-test

# Create limited role
kubectl create role limited --verb=get,list --resource=pods,services -n perm-test
kubectl create rolebinding limited-binding --role=limited --serviceaccount=perm-test:test-sa -n perm-test

# Test various permissions
echo "=== Testing as test-sa ==="
kubectl auth can-i get pods -n perm-test --as=system:serviceaccount:perm-test:test-sa      # yes
kubectl auth can-i create pods -n perm-test --as=system:serviceaccount:perm-test:test-sa   # no
kubectl auth can-i get secrets -n perm-test --as=system:serviceaccount:perm-test:test-sa   # no
kubectl auth can-i get pods -n default --as=system:serviceaccount:perm-test:test-sa        # no
kubectl auth can-i get services -n perm-test --as=system:serviceaccount:perm-test:test-sa  # yes

# Cleanup
kubectl delete ns perm-test
```

### Drill 3: ClusterRole vs Role (Target: 5 minutes)

```bash
# Create namespaces
kubectl create ns ns-a
kubectl create ns ns-b
kubectl create sa cross-ns-sa -n ns-a

# Option 1: Role (namespace-scoped) - only works in ns-a
kubectl create role ns-a-reader --verb=get,list --resource=pods -n ns-a
kubectl create rolebinding ns-a-binding --role=ns-a-reader --serviceaccount=ns-a:cross-ns-sa -n ns-a

# Test
kubectl auth can-i get pods -n ns-a --as=system:serviceaccount:ns-a:cross-ns-sa  # yes
kubectl auth can-i get pods -n ns-b --as=system:serviceaccount:ns-a:cross-ns-sa  # no

# Option 2: ClusterRole + RoleBinding (still namespace-scoped binding)
kubectl create clusterrole pod-reader-cluster --verb=get,list --resource=pods
kubectl create rolebinding ns-b-binding -n ns-b --clusterrole=pod-reader-cluster --serviceaccount=ns-a:cross-ns-sa

# Now can read ns-b too
kubectl auth can-i get pods -n ns-b --as=system:serviceaccount:ns-a:cross-ns-sa  # yes

# Cleanup
kubectl delete ns ns-a ns-b
kubectl delete clusterrole pod-reader-cluster
```

### Drill 4: Troubleshooting - Permission Denied (Target: 5 minutes)

```bash
# Setup: Create SA with intentionally wrong binding
kubectl create ns debug-rbac
kubectl create sa debug-sa -n debug-rbac
kubectl create role secret-reader --verb=get,list --resource=secrets -n debug-rbac
# WRONG: binding role to different SA name
kubectl create rolebinding wrong-binding --role=secret-reader --serviceaccount=debug-rbac:other-sa -n debug-rbac

# User reports: "I can't read secrets!"
kubectl auth can-i get secrets -n debug-rbac --as=system:serviceaccount:debug-rbac:debug-sa
# no

# YOUR TASK: Diagnose and fix
```

<details>
<summary>Solution</summary>

```bash
# Check what the rolebinding references
kubectl get rolebinding wrong-binding -n debug-rbac -o yaml | grep -A5 subjects
# Shows: other-sa, not debug-sa

# Fix: Create correct binding
kubectl delete rolebinding wrong-binding -n debug-rbac
kubectl create rolebinding correct-binding --role=secret-reader --serviceaccount=debug-rbac:debug-sa -n debug-rbac

# Verify
kubectl auth can-i get secrets -n debug-rbac --as=system:serviceaccount:debug-rbac:debug-sa
# yes

# Cleanup
kubectl delete ns debug-rbac
```

</details>

### Drill 5: Aggregate ClusterRoles (Target: 5 minutes)

```bash
# Create aggregated role
cat << 'EOF' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aggregate-reader
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]
EOF

# The built-in 'view' ClusterRole automatically includes rules from
# any ClusterRole with label aggregate-to-view: "true"

# Check what 'view' includes
kubectl get clusterrole view -o yaml | grep -A20 "rules:"

# Cleanup
kubectl delete clusterrole aggregate-reader
```

### Drill 6: RBAC for User (Target: 5 minutes)

```bash
# Create role for hypothetical user "alice"
kubectl create ns alice-ns
kubectl create role alice-admin --verb='*' --resource='*' -n alice-ns
kubectl create rolebinding alice-is-admin --role=alice-admin --user=alice -n alice-ns

# Test as alice
kubectl auth can-i create deployments -n alice-ns --as=alice      # yes
kubectl auth can-i delete pods -n alice-ns --as=alice             # yes
kubectl auth can-i get secrets -n default --as=alice              # no (different ns)
kubectl auth can-i create namespaces --as=alice                   # no (cluster scope)

# List what alice can do
kubectl auth can-i --list -n alice-ns --as=alice

# Cleanup
kubectl delete ns alice-ns
```

### Drill 7: Challenge - Least Privilege Setup

Create RBAC for a "deployment-manager" that can:
- Create, update, delete Deployments in namespace `app`
- View (but not modify) Services in namespace `app`
- View Pods in any namespace (read-only cluster-wide)

```bash
kubectl create ns app
# YOUR TASK: Create the necessary Role, ClusterRole, and bindings
```

<details>
<summary>Solution</summary>

```bash
# Role for deployment management in 'app' namespace
kubectl create role deployment-manager \
  --verb=create,update,delete,get,list,watch \
  --resource=deployments \
  -n app

# Role for service viewing in 'app' namespace
kubectl create role service-viewer \
  --verb=get,list,watch \
  --resource=services \
  -n app

# ClusterRole for cluster-wide pod viewing
kubectl create clusterrole pod-viewer \
  --verb=get,list,watch \
  --resource=pods

# Create ServiceAccount
kubectl create sa deployment-manager -n app

# Bind all roles
kubectl create rolebinding dm-deployments \
  --role=deployment-manager \
  --serviceaccount=app:deployment-manager \
  -n app

kubectl create rolebinding dm-services \
  --role=service-viewer \
  --serviceaccount=app:deployment-manager \
  -n app

kubectl create clusterrolebinding dm-pods \
  --clusterrole=pod-viewer \
  --serviceaccount=app:deployment-manager

# Test
kubectl auth can-i create deployments -n app --as=system:serviceaccount:app:deployment-manager  # yes
kubectl auth can-i delete services -n app --as=system:serviceaccount:app:deployment-manager     # no
kubectl auth can-i get pods -n default --as=system:serviceaccount:app:deployment-manager        # yes

# Cleanup
kubectl delete ns app
kubectl delete clusterrole pod-viewer
kubectl delete clusterrolebinding dm-pods
```

</details>

---

## Next Module

[Module 1.7: kubeadm Basics](../module-1.7-kubeadm/) - Cluster bootstrap and node management.
