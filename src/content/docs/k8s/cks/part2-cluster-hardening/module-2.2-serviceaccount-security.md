---
title: "Module 2.2: ServiceAccount Security"
slug: k8s/cks/part2-cluster-hardening/module-2.2-serviceaccount-security
sidebar:
  order: 2
lab:
  id: cks-2.2-serviceaccount-security
  url: https://killercoda.com/kubedojo/scenario/cks-2.2-serviceaccount-security
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical for workload security
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 2.1 (RBAC Deep Dive), CKA ServiceAccount knowledge

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** ServiceAccounts with automountServiceAccountToken disabled and scoped permissions
2. **Audit** default ServiceAccount usage across namespaces to find over-exposed credentials
3. **Implement** bound service account tokens with expiration and audience restrictions
4. **Diagnose** pod authentication failures caused by ServiceAccount misconfigurations

---

## Why This Module Matters

Every pod runs as a ServiceAccount. By default, that's the 'default' ServiceAccount with auto-mounted credentials. If a pod is compromised, the attacker gets those credentials—potentially accessing the Kubernetes API.

CKS tests your ability to harden ServiceAccounts and minimize exposure.

---

## The ServiceAccount Problem

```
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT SERVICEACCOUNT EXPOSURE                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  By Default:                                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Pod                               │   │
│  │                                                      │   │
│  │  Token mounted at:                                  │   │
│  │  /var/run/secrets/kubernetes.io/serviceaccount/     │   │
│  │                                                      │   │
│  │  Contains:                                          │   │
│  │  ├── token  (JWT for API authentication)           │   │
│  │  ├── ca.crt (cluster CA certificate)               │   │
│  │  └── namespace (pod's namespace)                   │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Attack scenario:                                          │
│  1. Attacker compromises application                       │
│  2. Reads token from filesystem                            │
│  3. Uses token to call Kubernetes API                      │
│  4. Depending on RBAC, can access secrets, pods, etc.     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Disable Automatic Token Mounting

### Method 1: At ServiceAccount Level

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp
  namespace: production
automountServiceAccountToken: false  # Disable for all pods using this SA
```

### Method 2: At Pod Level

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  serviceAccountName: myapp
  automountServiceAccountToken: false  # Override for this pod only
  containers:
  - name: app
    image: myapp:1.0
```

### Method 3: Update Default ServiceAccount

```bash
# Patch the default ServiceAccount in a namespace
kubectl patch serviceaccount default -n production \
  -p '{"automountServiceAccountToken": false}'

# Verify
kubectl get sa default -n production -o yaml
```

---

## Create Dedicated ServiceAccounts

```yaml
# One ServiceAccount per application
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-api
  namespace: production
automountServiceAccountToken: false
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: frontend-app
  namespace: production
automountServiceAccountToken: false
---
# Pod using dedicated SA
apiVersion: v1
kind: Pod
metadata:
  name: backend
  namespace: production
spec:
  serviceAccountName: backend-api
  containers:
  - name: app
    image: backend:1.0
```

---

## Token Request API (Bound Tokens)

Kubernetes 1.22+ uses bound tokens by default—short-lived, audience-bound tokens that are more secure than long-lived secrets.

```
┌─────────────────────────────────────────────────────────────┐
│              BOUND vs LEGACY TOKENS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Legacy Token (Secret-based)                               │
│  ─────────────────────────────────────────────────────────  │
│  • Long-lived (never expires)                              │
│  • Stored as Secret                                        │
│  • Not bound to pod lifecycle                              │
│  • Works even after pod deleted                            │
│                                                             │
│  Bound Token (TokenRequest API)                            │
│  ─────────────────────────────────────────────────────────  │
│  • Short-lived (configurable expiry)                       │
│  • Bound to specific pod                                   │
│  • Invalidated when pod deleted                            │
│  • Audience-bound                                          │
│  • Default in K8s 1.22+                                    │
│                                                             │
│  Bound tokens are automatically refreshed by kubelet!      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Create Bound Token Manually

```bash
# Create short-lived token (1 hour)
kubectl create token myapp-sa -n production --duration=1h

# Create token with specific audience
kubectl create token myapp-sa -n production --audience=api.example.com
```

### Projected Volume for Bound Token

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  serviceAccountName: myapp-sa
  automountServiceAccountToken: false  # Disable default mount
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
      readOnly: true
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600  # 1 hour
          audience: api.example.com  # Specific audience
```

---

## ServiceAccount Best Practices

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICEACCOUNT SECURITY CHECKLIST              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  □ Disable automount on default ServiceAccount             │
│    kubectl patch sa default -p                             │
│    '{"automountServiceAccountToken": false}'               │
│                                                             │
│  □ Create dedicated ServiceAccount per app                 │
│    One SA per workload, not shared                         │
│                                                             │
│  □ Only mount token when needed                            │
│    Most apps don't need Kubernetes API access              │
│                                                             │
│  □ Use bound tokens with expiry                            │
│    Short-lived, audience-bound                             │
│                                                             │
│  □ Minimal RBAC permissions                                │
│    Only what the app actually needs                        │
│                                                             │
│  □ Audit ServiceAccount usage                              │
│    Which SAs have what access                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Auditing ServiceAccounts

### Find Pods with Token Mounted

```bash
# List all pods with their ServiceAccount
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name} -> {.spec.serviceAccountName}{"\n"}{end}'

# Check if automount is enabled
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.automountServiceAccountToken != false) |
  "\(.metadata.namespace)/\(.metadata.name): automount enabled"'
```

### Find ServiceAccounts with Permissions

```bash
# List all RoleBindings/ClusterRoleBindings for ServiceAccounts
kubectl get rolebindings,clusterrolebindings -A -o json | jq -r '
  .items[] |
  .subjects[]? |
  select(.kind == "ServiceAccount") |
  "\(.namespace)/\(.name)"' | sort -u

# Check permissions for a specific SA
kubectl auth can-i --list --as=system:serviceaccount:default:myapp
```

### Check for Legacy Token Secrets

```bash
# Find secrets of type ServiceAccount token
kubectl get secrets -A -o json | jq -r '
  .items[] |
  select(.type == "kubernetes.io/service-account-token") |
  "\(.metadata.namespace)/\(.metadata.name)"'
```

---

## Real Exam Scenarios

### Scenario 1: Disable Token Automount

```bash
# Disable for default SA in production namespace
kubectl patch serviceaccount default -n production \
  -p '{"automountServiceAccountToken": false}'

# Create new SA with automount disabled
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: webapp-sa
  namespace: production
automountServiceAccountToken: false
EOF
```

### Scenario 2: Fix Pod Using Default SA

```bash
# Check what SA a pod uses
kubectl get pod myapp -n production -o jsonpath='{.spec.serviceAccountName}'

# If using default, create dedicated SA
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: production
automountServiceAccountToken: false
EOF

# Recreate pod with new SA (can't patch SA on running pod)
kubectl get pod myapp -n production -o yaml > pod.yaml
# Edit pod.yaml: set serviceAccountName: myapp-sa
kubectl delete pod myapp -n production
kubectl apply -f pod.yaml
```

### Scenario 3: Create SA with Minimal Permissions

```bash
# Create SA for app that only needs to read configmaps
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: config-reader
  namespace: production
automountServiceAccountToken: true  # Needs API access
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config"]  # Only specific configmap
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: config-reader-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: config-reader
  namespace: production
roleRef:
  kind: Role
  name: configmap-reader
  apiGroup: rbac.authorization.k8s.io
EOF
```

---

## Token Security Deep Dive

### Examining a Token

```bash
# Get token from running pod
kubectl exec myapp -- cat /var/run/secrets/kubernetes.io/serviceaccount/token

# Decode JWT (without verification)
TOKEN=$(kubectl exec myapp -- cat /var/run/secrets/kubernetes.io/serviceaccount/token)
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .
```

### Token Contents

```json
{
  "aud": ["https://kubernetes.default.svc"],
  "exp": 1704067200,  // Expiration time
  "iat": 1703980800,  // Issued at
  "iss": "https://kubernetes.default.svc",
  "kubernetes.io": {
    "namespace": "production",
    "pod": {
      "name": "myapp-abc123",
      "uid": "..."
    },
    "serviceaccount": {
      "name": "myapp-sa",
      "uid": "..."
    }
  },
  "sub": "system:serviceaccount:production:myapp-sa"
}
```

---

## Did You Know?

- **TokenRequest API** was introduced in Kubernetes 1.12 and became default in 1.22. It's significantly more secure than the old secret-based tokens.

- **Bound tokens are rotated automatically** by kubelet before they expire. Applications don't need to handle refresh—the file is updated in place.

- **The default ServiceAccount** exists automatically in every namespace. Patching it affects all pods that don't specify a ServiceAccount.

- **Some controllers need API access**—operators, admission webhooks, and Kubernetes-aware apps. These legitimately need mounted tokens with appropriate RBAC.

- **PodCertificateRequests (Beta in K8s 1.35)** enable native workload identity with automated certificate rotation. The kubelet generates keys and requests X.509 certificates via `PodCertificateRequest` objects, enabling pure mTLS flows without bearer tokens. This is the future of pod-to-pod authentication in Kubernetes.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using default SA for everything | Shared permissions, hard to audit | Create dedicated SAs |
| Not disabling automount | Unnecessary API access | Disable by default |
| Long-lived token secrets | Never expire, can be stolen | Use bound tokens |
| Too much RBAC for SA | Compromised pod = excessive access | Minimal permissions |
| Assuming no token = secure | Other attack vectors exist | Defense in depth |

---

## Quiz

1. **What path is the ServiceAccount token mounted at by default?**
   <details>
   <summary>Answer</summary>
   `/var/run/secrets/kubernetes.io/serviceaccount/` - Contains `token`, `ca.crt`, and `namespace` files.
   </details>

2. **How do you disable automatic token mounting for a ServiceAccount?**
   <details>
   <summary>Answer</summary>
   Set `automountServiceAccountToken: false` in the ServiceAccount spec or in the Pod spec. Pod spec takes precedence.
   </details>

3. **What are bound tokens and why are they more secure?**
   <details>
   <summary>Answer</summary>
   Bound tokens are short-lived, audience-bound, and tied to a specific pod. They expire and are invalidated when the pod is deleted, unlike legacy long-lived token secrets.
   </details>

4. **Why shouldn't all pods use the default ServiceAccount?**
   <details>
   <summary>Answer</summary>
   Shared ServiceAccounts make permissions harder to audit and control. If one app needs more permissions, all apps using that SA get them. Dedicated SAs enable least privilege.
   </details>

---

## Hands-On Exercise

**Task**: Secure ServiceAccounts in a namespace.

```bash
# Setup
kubectl create namespace sa-security
kubectl run app1 --image=nginx -n sa-security
kubectl run app2 --image=nginx -n sa-security

# Step 1: Check current SA usage
kubectl get pods -n sa-security -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.serviceAccountName}{"\n"}{end}'

# Step 2: Verify token is mounted
kubectl exec app1 -n sa-security -- ls /var/run/secrets/kubernetes.io/serviceaccount/

# Step 3: Disable automount on default SA
kubectl patch serviceaccount default -n sa-security \
  -p '{"automountServiceAccountToken": false}'

# Step 4: Create dedicated SA (without automount)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: sa-security
automountServiceAccountToken: false
EOF

# Step 5: Recreate pods with new SA
kubectl delete pod app1 app2 -n sa-security

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: app1
  namespace: sa-security
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: app2
  namespace: sa-security
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: nginx
EOF

# Step 6: Verify token is NOT mounted
kubectl exec app1 -n sa-security -- ls /var/run/secrets/kubernetes.io/serviceaccount/ 2>&1 || echo "Directory not found (expected!)"

# Step 7: Verify pods use correct SA
kubectl get pods -n sa-security -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.serviceAccountName}{"\n"}{end}'

# Cleanup
kubectl delete namespace sa-security
```

**Success criteria**: Pods use dedicated SA with no token mounted.

---

## Summary

**Default Behavior (Insecure)**:
- Token auto-mounted to all pods
- Default SA often used
- Long-lived tokens

**Secure Configuration**:
- Disable automount on default SA
- Create dedicated SA per app
- Only mount when needed
- Use bound tokens with expiry

**Key Commands**:
```bash
# Disable automount
kubectl patch sa default -p '{"automountServiceAccountToken": false}'

# Create token manually
kubectl create token myapp-sa --duration=1h
```

**Exam Tips**:
- Know both SA and Pod level automount settings
- Practice patching the default SA
- Understand bound vs legacy tokens

---

## Next Module

[Module 2.3: API Server Security](../module-2.3-api-server-security/) - Securing the Kubernetes API server.
