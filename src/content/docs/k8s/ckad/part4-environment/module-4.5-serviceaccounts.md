---
title: "Module 4.5: ServiceAccounts"
slug: k8s/ckad/part4-environment/module-4.5-serviceaccounts
sidebar:
  order: 5
lab:
  id: ckad-4.5-serviceaccounts
  url: https://killercoda.com/kubedojo/scenario/ckad-4.5-serviceaccounts
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Important for API access and identity
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 4.4 (SecurityContexts), understanding of RBAC basics

---

## Learning Outcomes

After completing this module, you will be able to:
- **Configure** pods to use specific ServiceAccounts for API server authentication
- **Explain** how ServiceAccount tokens are mounted and used by applications inside pods
- **Debug** API permission errors by tracing from pod to ServiceAccount to Role bindings
- **Design** a least-privilege ServiceAccount setup that limits pod access to only required resources

---

## Why This Module Matters

ServiceAccounts provide identity for pods to interact with the Kubernetes API. When your application needs to list pods, create ConfigMaps, or access other cluster resources, it uses its ServiceAccount's credentials.

The CKAD exam tests:
- Creating and assigning ServiceAccounts
- Understanding token mounting
- Configuring pod identity
- Opting out of automatic token mounting

> **The Employee Badge Analogy**
>
> ServiceAccounts are like employee ID badges. Every employee (pod) gets a badge (ServiceAccount) that identifies them to security systems (API server). The default badge (default ServiceAccount) gets basic access, but specific roles need specific badges. Without a badge, you can't get past the lobby.

---

## ServiceAccount Basics

### Default ServiceAccount

Every namespace has a `default` ServiceAccount:

```bash
# View default ServiceAccount
k get serviceaccount
# NAME      SECRETS   AGE
# default   0         10d

# Describe it
k describe sa default
```

### Every Pod Gets a ServiceAccount

```bash
# Check pod's ServiceAccount
k get pod my-pod -o jsonpath='{.spec.serviceAccountName}'
# default

# Or in describe
k describe pod my-pod | grep "Service Account"
```

---

## Creating ServiceAccounts

### Imperative

```bash
# Create ServiceAccount
k create serviceaccount my-app-sa

# In specific namespace
k create sa my-app-sa -n my-namespace
```

### Declarative

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: default
```

---

## Assigning ServiceAccounts to Pods

### In Pod Spec

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: my-app-sa    # Use this ServiceAccount
  containers:
  - name: app
    image: nginx
```

### In Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      serviceAccountName: my-app-sa    # Pod template uses this SA
      containers:
      - name: app
        image: nginx
```

---

## Token Mounting

### Automatic Token Mounting (Default)

By default, Kubernetes mounts a token at `/var/run/secrets/kubernetes.io/serviceaccount/`:

```bash
# View mounted token files
k exec my-pod -- ls /var/run/secrets/kubernetes.io/serviceaccount/
# ca.crt
# namespace
# token

# View the token
k exec my-pod -- cat /var/run/secrets/kubernetes.io/serviceaccount/token
```

### Token Contents

| File | Purpose |
|------|---------|
| `token` | JWT token for API authentication |
| `ca.crt` | CA certificate to verify API server |
| `namespace` | Pod's namespace |

> **Pause and predict**: Every pod gets the `default` ServiceAccount's token mounted automatically. Why might this be a security concern for pods that never call the Kubernetes API?

### Disabling Automatic Token Mount

For pods that don't need API access:

**On Pod:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-api-access
spec:
  automountServiceAccountToken: false    # Don't mount token
  containers:
  - name: app
    image: nginx
```

**On ServiceAccount:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: restricted-sa
automountServiceAccountToken: false    # Default for pods using this SA
```

---

## ServiceAccount Token Types

### Bound Service Account Tokens (Kubernetes 1.22+)

Modern tokens are:
- **Time-limited** - expire automatically
- **Audience-bound** - only valid for specific purposes
- **Object-bound** - tied to specific pod

```yaml
# Request token with specific audience
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: my-app-sa
  containers:
  - name: app
    image: my-app
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600    # 1 hour
          audience: my-audience
```

### Legacy Tokens (pre-1.24)

Before Kubernetes 1.24, long-lived tokens were stored in Secrets. This is deprecated.

```bash
# Old way (deprecated) - DO NOT use
k create token my-app-sa    # Creates short-lived token instead
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│              ServiceAccount Flow                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Create ServiceAccount                                   │
│  ┌─────────────────────────────────┐                       │
│  │ k create sa my-app-sa           │                       │
│  └─────────────────────────────────┘                       │
│                    │                                        │
│                    ▼                                        │
│  2. Assign to Pod                                          │
│  ┌─────────────────────────────────┐                       │
│  │ spec:                           │                       │
│  │   serviceAccountName: my-app-sa │                       │
│  └─────────────────────────────────┘                       │
│                    │                                        │
│                    ▼                                        │
│  3. Token Mounted Automatically                            │
│  ┌─────────────────────────────────┐                       │
│  │ /var/run/secrets/kubernetes.io/ │                       │
│  │   serviceaccount/               │                       │
│  │   ├── token     ← JWT token     │                       │
│  │   ├── ca.crt    ← API CA cert   │                       │
│  │   └── namespace ← Pod namespace │                       │
│  └─────────────────────────────────┘                       │
│                    │                                        │
│                    ▼                                        │
│  4. Pod Uses Token for API Access                          │
│  ┌─────────────────────────────────┐                       │
│  │ curl -H "Authorization:         │                       │
│  │   Bearer $(cat /var/run/...)"   │                       │
│  │   https://kubernetes/api/v1/... │                       │
│  └─────────────────────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Using ServiceAccount Tokens

### From Within a Pod

```bash
# Inside a pod, query the API
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

# List pods in current namespace
curl -s --cacert $CACERT \
  -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces/$NAMESPACE/pods
```

### With kubectl

```bash
# Create short-lived token
k create token my-app-sa

# Create token with duration
k create token my-app-sa --duration=1h
```

---

## ServiceAccounts and RBAC

> **Stop and think**: You create a ServiceAccount called `pod-manager` and assign it to your pod. When the pod tries to list other pods via the API, it gets a 403 Forbidden error. What's missing?

ServiceAccounts alone don't grant permissions. You need RBAC:

```yaml
# 1. Create ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-reader-sa
---
# 2. Create Role with permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
# 3. Bind Role to ServiceAccount
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
subjects:
- kind: ServiceAccount
  name: pod-reader-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

---

## Quick Reference

```bash
# Create ServiceAccount
k create sa NAME

# View ServiceAccounts
k get sa
k describe sa NAME

# Assign to pod
spec:
  serviceAccountName: NAME

# Disable auto-mount
spec:
  automountServiceAccountToken: false

# Create short-lived token
k create token NAME

# Check pod's SA
k get pod POD -o jsonpath='{.spec.serviceAccountName}'
```

---

## Did You Know?

- **The default ServiceAccount has no special permissions.** It can't do anything unless you add RBAC rules. This is secure by default.

- **Tokens are JWTs.** You can decode them to see claims: `cat token | cut -d. -f2 | base64 -d | jq`

- **ServiceAccounts are namespaced.** A ServiceAccount in namespace A cannot be used by pods in namespace B.

- **`kubectl auth can-i --as=system:serviceaccount:default:my-sa`** lets you test what a ServiceAccount can do.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Expecting default SA to have permissions | API calls fail with 403 | Create RBAC for the SA |
| Using deprecated long-lived tokens | Security risk | Use `k create token` or bound tokens |
| Not disabling mount when unneeded | Unnecessary attack surface | Set `automountServiceAccountToken: false` |
| Wrong ServiceAccount name | Pod uses default SA | Verify with `k describe pod` |
| Confusing SA with RBAC | SA alone doesn't grant access | SA + Role + RoleBinding needed |

---

## Quiz

1. **A developer creates a ServiceAccount called `deployer-sa` and assigns it to a pod that needs to list Deployments. The pod starts successfully, but when it calls the Kubernetes API to list deployments, it gets a 403 Forbidden error. What is missing and what steps are needed to fix it?**
   <details>
   <summary>Answer</summary>
   A ServiceAccount by itself has no permissions — it's just an identity. You need three things: (1) a Role that grants the `list` verb on `deployments` in the `apps` apiGroup, (2) a RoleBinding that binds that Role to the `deployer-sa` ServiceAccount. Without RBAC, the ServiceAccount is like an employee badge that gets you through the front door but doesn't open any office doors. You can verify what the SA can do with `kubectl auth can-i list deployments --as=system:serviceaccount:default:deployer-sa`.
   </details>

2. **During a security audit, the team discovers that a frontend pod (which never calls the Kubernetes API) has a ServiceAccount token mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`. An attacker who compromises this pod could use the token to query the API server. How do you eliminate this attack surface?**
   <details>
   <summary>Answer</summary>
   Set `automountServiceAccountToken: false` in the pod spec (or on the ServiceAccount itself). This prevents Kubernetes from mounting the token, CA certificate, and namespace file into the pod. For pods that don't need API access — which is most application pods — this is a security best practice. You can set it on the pod spec level (affects just that pod) or on the ServiceAccount definition (affects all pods using that SA). Pod-level setting takes precedence if both are specified.
   </details>

3. **A pod is configured with `serviceAccountName: custom-sa`, but `kubectl describe pod` shows it's using the `default` ServiceAccount instead. What could have gone wrong?**
   <details>
   <summary>Answer</summary>
   The most likely cause is that the ServiceAccount `custom-sa` doesn't exist in the pod's namespace. When you specify a non-existent ServiceAccount, the behavior depends on the cluster configuration — some clusters reject the pod, others fall back to the default SA. Check with `kubectl get sa custom-sa` in the correct namespace. If it doesn't exist, create it with `kubectl create sa custom-sa`. Another possibility: the pod was created in a different namespace than where the SA exists (ServiceAccounts are namespaced). Always verify both the SA and pod are in the same namespace.
   </details>

4. **Your team manages two applications: an internal monitoring tool that needs to list pods across all namespaces, and a web frontend that only needs to read ConfigMaps in its own namespace. How would you set up ServiceAccounts and RBAC for each following least-privilege principles?**
   <details>
   <summary>Answer</summary>
   For the monitoring tool: create a ServiceAccount (e.g., `monitor-sa`), a ClusterRole with `list` and `get` verbs on `pods` resources, and a ClusterRoleBinding connecting them. ClusterRole + ClusterRoleBinding is needed because it must work across all namespaces. For the web frontend: create a ServiceAccount (e.g., `frontend-sa`), a Role (namespace-scoped) with `get` and `list` on `configmaps`, and a RoleBinding in the frontend's namespace. This follows least privilege — each SA gets exactly the permissions it needs, no more. The monitoring tool can only list pods (not delete or create), and the frontend can only read ConfigMaps in its own namespace.
   </details>

---

## Hands-On Exercise

**Task**: Create and use a ServiceAccount.

**Part 1: Create ServiceAccount**
```bash
k create sa app-sa

# Verify
k get sa app-sa
```

**Part 2: Pod with Custom ServiceAccount**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sa-demo
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'cat /var/run/secrets/kubernetes.io/serviceaccount/namespace && sleep 3600']
EOF

# Verify SA assigned
k get pod sa-demo -o jsonpath='{.spec.serviceAccountName}'
echo

# Check token mount
k exec sa-demo -- ls /var/run/secrets/kubernetes.io/serviceaccount/
```

**Part 3: Pod without Token Mount**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-token
spec:
  serviceAccountName: app-sa
  automountServiceAccountToken: false
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls /var/run/secrets 2>&1 || echo "No secrets mounted" && sleep 3600']
EOF

k logs no-token
# Should show: No secrets mounted (or directory not found)
```

**Cleanup:**
```bash
k delete pod sa-demo no-token
k delete sa app-sa
```

---

## Practice Drills

### Drill 1: Create ServiceAccount (Target: 1 minute)

```bash
k create sa drill1-sa
k get sa drill1-sa
k delete sa drill1-sa
```

### Drill 2: Pod with ServiceAccount (Target: 2 minutes)

```bash
k create sa drill2-sa

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill2
spec:
  serviceAccountName: drill2-sa
  containers:
  - name: app
    image: busybox
    command: ['sleep', '3600']
EOF

k get pod drill2 -o jsonpath='{.spec.serviceAccountName}'
echo

k delete pod drill2 sa drill2-sa
```

### Drill 3: Check Token Location (Target: 2 minutes)

```bash
k run drill3 --image=busybox --restart=Never -- sleep 3600

k exec drill3 -- ls /var/run/secrets/kubernetes.io/serviceaccount/
k exec drill3 -- cat /var/run/secrets/kubernetes.io/serviceaccount/namespace

k delete pod drill3
```

### Drill 4: Disable Token Mount (Target: 2 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill4
spec:
  automountServiceAccountToken: false
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls /var/run/secrets/kubernetes.io/serviceaccount 2>&1; sleep 3600']
EOF

k logs drill4
# Should show error (directory doesn't exist)

k delete pod drill4
```

### Drill 5: Create Token (Target: 2 minutes)

```bash
k create sa drill5-sa

# Create short-lived token
k create token drill5-sa

# Create with duration
k create token drill5-sa --duration=30m

k delete sa drill5-sa
```

### Drill 6: Deployment with ServiceAccount (Target: 3 minutes)

```bash
k create sa drill6-sa

cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill6
spec:
  replicas: 2
  selector:
    matchLabels:
      app: drill6
  template:
    metadata:
      labels:
        app: drill6
    spec:
      serviceAccountName: drill6-sa
      containers:
      - name: app
        image: nginx
EOF

# Verify all pods use correct SA
k get pods -l app=drill6 -o jsonpath='{.items[*].spec.serviceAccountName}'
echo

k delete deploy drill6 sa drill6-sa
```

---

## Next Module

[Module 4.6: Custom Resource Definitions](../module-4.6-crds/) - Extend Kubernetes with custom resources.
