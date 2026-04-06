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

> **Stop and think**: Every namespace gets a `default` ServiceAccount automatically, and every pod uses it unless told otherwise. If you never touch ServiceAccount configuration, what token is available inside every pod in your cluster right now? What could an attacker do with it?

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

> **What would happen if**: An attacker steals a legacy (secret-based) ServiceAccount token from a pod that was deleted yesterday. Can they still use it to authenticate to the API server? Now compare: what if they steal a bound token from a pod that was deleted yesterday?

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

> **Pause and predict**: You set `automountServiceAccountToken: false` on a ServiceAccount, but a pod using that SA sets `automountServiceAccountToken: true` in its pod spec. Which setting wins -- the ServiceAccount or the pod?

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

## Diagnosing Authentication Failures

When configuring pods that legitimately need Kubernetes API access, you will inevitably encounter authentication or authorization errors. Knowing how to diagnose these quickly is essential for the CKS exam and real-world troubleshooting.

> **Pause and predict**: A pod logs a `403 Forbidden` error when trying to list pods in its namespace. Is the issue a missing token, or missing RBAC permissions?

### 401 Unauthorized vs. 403 Forbidden

*   **401 Unauthorized**: The API server does not know who you are. The token is missing, expired, or invalid.
*   **403 Forbidden**: The API server knows who you are (the token is valid), but the associated ServiceAccount lacks the required RBAC permissions to perform the requested action.

### Step 1: Check Pod Logs

The first indicator of a problem will be in the application logs.

```bash
# View logs for API connection errors
kubectl logs my-api-pod
# Look for: "Unauthorized" (401) or "Forbidden" (403)
```

### Step 2: Verify Token Mounts (for 401 errors)

If a pod needs access but receives 401 errors, it likely does not have a token mounted.

```bash
# 1. Check if automount is disabled at the pod level
kubectl get pod my-api-pod -o jsonpath='{.spec.automountServiceAccountToken}'

# 2. Verify which ServiceAccount it is using
kubectl get pod my-api-pod -o jsonpath='{.spec.serviceAccountName}'

# 3. Exec into the pod and verify the token file exists
kubectl exec my-api-pod -- ls -l /var/run/secrets/kubernetes.io/serviceaccount/
# If this fails, the token is not mounted (check SA and Pod automount settings).
```

### Step 3: Check RBAC Bindings (for 403 errors)

If the pod logs show 403 errors, the token is present but lacks permissions. You must verify the RoleBindings associated with the pod's ServiceAccount.

```bash
# 1. Identify the ServiceAccount and Namespace
SA_NAME=$(kubectl get pod my-api-pod -o jsonpath='{.spec.serviceAccountName}')
NS=$(kubectl get pod my-api-pod -o jsonpath='{.metadata.namespace}')

# 2. Impersonate the ServiceAccount to test its permissions exactly
kubectl auth can-i list pods -n $NS --as=system:serviceaccount:$NS:$SA_NAME
# Output: no (This confirms the 403 is due to RBAC)

# 3. Check existing RoleBindings to see what is actually bound
kubectl get rolebindings,clusterrolebindings -A -o custom-columns='KIND:kind,NAMESPACE:metadata.namespace,NAME:metadata.name,SUBJECTS:subjects[*].name' | grep $SA_NAME
```

If `auth can-i` returns `no`, you must create or update a Role and RoleBinding to grant the specific API access the pod requires.

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

1. **During incident response, you discover an attacker extracted a token from `/var/run/secrets/kubernetes.io/serviceaccount/token` inside a compromised pod. Using that token, they listed all secrets in the namespace. The pod was a simple web app that never needed API access. What two configuration changes would have prevented this attack chain?**
   <details>
   <summary>Answer</summary>
   Two changes: (1) Set `automountServiceAccountToken: false` on either the ServiceAccount or the pod spec to prevent the token from being mounted at all -- the web app didn't need API access, so there was no reason to mount credentials. (2) Create a dedicated ServiceAccount for the web app with zero RBAC permissions instead of using the default SA. Even if a token were mounted, it would have no permissions to list secrets. The default SA in many clusters has accumulated permissions through ClusterRoleBindings that were meant for other purposes. Defense in depth means doing both.
   </details>

2. **Your security team finds 47 pods across the cluster using the `default` ServiceAccount. They want to patch the default SA to disable automount. A developer objects, saying their app reads ConfigMaps from the API and will break. How do you satisfy both security and the developer?**
   <details>
   <summary>Answer</summary>
   Patch the default ServiceAccount with `automountServiceAccountToken: false` to protect the 46 pods that don't need API access. For the developer's app, create a dedicated ServiceAccount (e.g., `configmap-reader`) with `automountServiceAccountToken: true`, bind a Role that grants only `get` and `list` on `configmaps` (using `resourceNames` if possible), and update the pod spec to use `serviceAccountName: configmap-reader`. The pod-level setting overrides the SA-level setting, so even if the default SA has automount disabled, the explicit pod spec wins. This gives the developer what they need while protecting everyone else.
   </details>

3. **A compliance audit flags that your cluster has 12 Secrets of type `kubernetes.io/service-account-token` -- legacy long-lived tokens. The auditor says these are a risk because they never expire. Your team says some are still needed for CI/CD pipelines. What's the migration path to eliminate legacy tokens?**
   <details>
   <summary>Answer</summary>
   Legacy token secrets never expire and remain valid even after the associated pod is deleted -- a stolen token works forever. Migration: (1) Audit which secrets are actually referenced by running workloads using `kubectl get pods -A -o jsonpath` to check `serviceAccountName` usage. (2) For CI/CD pipelines, switch to `kubectl create token <sa-name> --duration=1h` to generate short-lived bound tokens instead. (3) For in-cluster workloads, use projected volumes with `serviceAccountToken` source and `expirationSeconds` for automatic rotation. (4) Delete unused legacy token secrets. Bound tokens are invalidated when pods are deleted and expire automatically, eliminating the "stolen token works forever" risk.
   </details>

4. **You configure a pod with `automountServiceAccountToken: false` on the ServiceAccount AND `automountServiceAccountToken: true` on the pod spec. The pod starts and you find a token mounted. Your colleague says "the SA setting should override the pod." Who is right, and how does Kubernetes resolve this conflict?**
   <details>
   <summary>Answer</summary>
   The pod spec wins -- the token is mounted. Kubernetes uses the pod-level `automountServiceAccountToken` setting when it's explicitly set, regardless of the ServiceAccount-level setting. The precedence is: pod spec (if set) > ServiceAccount spec (if set) > default behavior (mount). This is by design -- it allows administrators to disable automount by default on the ServiceAccount while individual pods can opt in when they legitimately need API access. The important implication: to guarantee no token is mounted, you must control both the SA and the pod spec, or use admission control to enforce the policy.
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