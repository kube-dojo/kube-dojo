---
title: "Module 1.5: GUI Security (Kubernetes Dashboard)"
slug: k8s/cks/part1-cluster-setup/module-1.5-gui-security
sidebar:
  order: 5
lab:
  id: cks-1.5-gui-security
  url: https://killercoda.com/kubedojo/scenario/cks-1.5-gui-security
  duration: "30 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Common attack surface
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: RBAC knowledge from CKA, Module 1.1 (Network Policies)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** Kubernetes Dashboard with authentication and least-privilege RBAC
2. **Audit** dashboard deployments for exposed services and overly permissive ServiceAccounts
3. **Implement** network-level restrictions to limit dashboard access to authorized users
4. **Evaluate** whether to deploy, restrict, or remove GUI components in production clusters

---

## Why This Module Matters

The Kubernetes Dashboard has been a notorious attack vector. In 2018, Tesla's Kubernetes cluster was compromised through an exposed dashboard—attackers used it to mine cryptocurrency. A misconfigured dashboard gives attackers full cluster control with a nice GUI.

CKS tests your ability to secure or restrict web-based cluster access.

---

## The Dashboard Risk

```
┌─────────────────────────────────────────────────────────────┐
│              DASHBOARD ATTACK SCENARIO                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Common Misconfiguration:                                  │
│                                                             │
│  Internet ────► Dashboard (exposed) ────► Full cluster     │
│                                            access!         │
│                                                             │
│  What goes wrong:                                          │
│  ─────────────────────────────────────────────────────────  │
│  1. Dashboard exposed without authentication               │
│  2. Dashboard uses cluster-admin ServiceAccount           │
│  3. Skip button allows anonymous access                    │
│  4. No NetworkPolicy restricting access                    │
│                                                             │
│  Result:                                                   │
│  ⚠️  Anyone can view secrets                               │
│  ⚠️  Anyone can deploy pods (cryptominers!)               │
│  ⚠️  Anyone can delete resources                          │
│  ⚠️  Full cluster compromise                               │
│                                                             │
│  Real incident: Tesla (2018)                               │
│  └── Attackers mined crypto using exposed dashboard        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Dashboard Security Options

```
┌─────────────────────────────────────────────────────────────┐
│              DASHBOARD ACCESS MODES                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Option 1: Don't Install It                                │
│  ─────────────────────────────────────────────────────────  │
│  Most secure. Use kubectl instead.                         │
│  CLI is more secure than GUI.                              │
│                                                             │
│  Option 2: Read-Only Access                                │
│  ─────────────────────────────────────────────────────────  │
│  Dashboard can view but not modify.                        │
│  Use minimal RBAC permissions.                             │
│                                                             │
│  Option 3: Authenticated Access Only                       │
│  ─────────────────────────────────────────────────────────  │
│  Require token or kubeconfig login.                        │
│  No skip button.                                           │
│                                                             │
│  Option 4: Internal Access Only                            │
│  ─────────────────────────────────────────────────────────  │
│  kubectl proxy or port-forward required.                   │
│  No external exposure.                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Secure Dashboard Installation

### Step 1: Deploy Dashboard

```bash
# Official dashboard installation
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Verify deployment
kubectl get pods -n kubernetes-dashboard
kubectl get svc -n kubernetes-dashboard
```

### Step 2: Create Minimal ServiceAccount

```yaml
# Read-only dashboard service account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-readonly
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-readonly
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dashboard-readonly
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dashboard-readonly
subjects:
- kind: ServiceAccount
  name: dashboard-readonly
  namespace: kubernetes-dashboard
```

### Step 3: Get Access Token

```bash
# Create token for the service account
kubectl create token dashboard-readonly -n kubernetes-dashboard

# Or create a long-lived secret (older method)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-readonly-token
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/service-account.name: dashboard-readonly
type: kubernetes.io/service-account-token
EOF

# Get the token
kubectl get secret dashboard-readonly-token -n kubernetes-dashboard -o jsonpath='{.data.token}' | base64 -d
```

---

## Access Methods

### Method 1: kubectl proxy (Most Secure)

```bash
# Start proxy (only accessible from localhost)
kubectl proxy

# Access dashboard at:
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### Method 2: Port Forward

```bash
# Forward dashboard port
kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443

# Access at https://localhost:8443
# Use token to authenticate
```

### Method 3: NodePort (Less Secure)

```yaml
# Expose dashboard as NodePort
apiVersion: v1
kind: Service
metadata:
  name: kubernetes-dashboard-nodeport
  namespace: kubernetes-dashboard
spec:
  type: NodePort
  selector:
    k8s-app: kubernetes-dashboard
  ports:
  - port: 443
    targetPort: 8443
    nodePort: 30443
```

**Warning**: NodePort exposes on all nodes. Use NetworkPolicy to restrict access!

---

## Restricting Dashboard Access

### NetworkPolicy for Dashboard

```yaml
# Only allow access from specific namespace/pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-access
  namespace: kubernetes-dashboard
spec:
  podSelector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  policyTypes:
  - Ingress
  ingress:
  # Only from admin namespace
  - from:
    - namespaceSelector:
        matchLabels:
          name: admin-access
    ports:
    - port: 8443
```

### Disable Skip Button

The dashboard has a "Skip" button that allows anonymous access. Disable it:

```yaml
# In dashboard deployment, add argument
spec:
  containers:
  - name: kubernetes-dashboard
    args:
    - --auto-generate-certificates
    - --namespace=kubernetes-dashboard
    - --enable-skip-login=false  # Disable skip button
```

Or patch existing deployment:

```bash
kubectl patch deployment kubernetes-dashboard -n kubernetes-dashboard \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--enable-skip-login=false"}]'
```

---

## Ingress for Dashboard (Production)

If you must expose dashboard externally:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # Client certificate authentication
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-secret: "kubernetes-dashboard/ca-secret"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - dashboard.example.com
    secretName: dashboard-tls
  rules:
  - host: dashboard.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kubernetes-dashboard
            port:
              number: 443
```

---

## Security Checklist

```
┌─────────────────────────────────────────────────────────────┐
│              DASHBOARD SECURITY CHECKLIST                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  □ Do you really need the dashboard?                       │
│    └── Consider kubectl or Lens instead                    │
│                                                             │
│  □ Minimal RBAC permissions                                │
│    └── Never use cluster-admin                             │
│    └── Read-only if possible                               │
│                                                             │
│  □ Skip button disabled                                    │
│    └── --enable-skip-login=false                           │
│                                                             │
│  □ Access restricted                                       │
│    └── kubectl proxy or port-forward                       │
│    └── NetworkPolicy limiting source                       │
│                                                             │
│  □ If exposed externally                                   │
│    └── TLS required                                        │
│    └── mTLS client certificates                            │
│    └── VPN access only                                     │
│                                                             │
│  □ Token-based authentication only                         │
│    └── Short-lived tokens preferred                        │
│    └── No basic auth                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Real Exam Scenarios

### Scenario 1: Restrict Dashboard RBAC

```bash
# Check current dashboard permissions
kubectl get clusterrolebinding | grep dashboard
kubectl describe clusterrolebinding kubernetes-dashboard

# If using cluster-admin, create restricted role instead
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-viewer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "nodes"]
  verbs: ["get", "list"]
EOF

# Update binding
kubectl delete clusterrolebinding kubernetes-dashboard
kubectl create clusterrolebinding kubernetes-dashboard \
  --clusterrole=dashboard-viewer \
  --serviceaccount=kubernetes-dashboard:kubernetes-dashboard
```

### Scenario 2: Disable Anonymous Access

```bash
# Patch dashboard to disable skip
kubectl patch deployment kubernetes-dashboard -n kubernetes-dashboard \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--enable-skip-login=false"}]'

# Verify
kubectl get deployment kubernetes-dashboard -n kubernetes-dashboard -o yaml | grep skip
```

### Scenario 3: Apply NetworkPolicy

```bash
# Create NetworkPolicy to restrict access
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-restrict
  namespace: kubernetes-dashboard
spec:
  podSelector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          dashboard-access: "true"
EOF
```

---

## Alternatives to Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│              DASHBOARD ALTERNATIVES                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl (CLI)                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Most secure - uses kubeconfig                          │
│  • Full functionality                                      │
│  • Scriptable                                              │
│                                                             │
│  Lens (Desktop App)                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Local GUI application                                   │
│  • Uses your kubeconfig                                    │
│  • No cluster-side components                              │
│                                                             │
│  K9s (Terminal UI)                                         │
│  ─────────────────────────────────────────────────────────  │
│  • Terminal-based GUI                                      │
│  • Uses your kubeconfig                                    │
│  • Very efficient for operations                           │
│                                                             │
│  Rancher/OpenShift Console                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Enterprise-grade                                        │
│  • Built-in authentication                                 │
│  • More secure by design                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The Tesla breach in 2018** happened because their Kubernetes dashboard was exposed without password protection. Attackers deployed crypto-mining containers.

- **Dashboard v2.0+** disabled the skip button by default. Older versions had it enabled, making anonymous access trivially easy.

- **The dashboard pods themselves** need RBAC permissions to read cluster resources. Limiting the dashboard's ServiceAccount limits what users can see.

- **kubectl proxy** is secure because it only binds to localhost and uses your kubeconfig credentials. The dashboard sees your permissions, not elevated ones.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using cluster-admin for dashboard | Full cluster access for attackers | Create minimal RBAC |
| Exposing via LoadBalancer | Public internet access | Use kubectl proxy |
| Leaving skip button enabled | Anonymous access possible | --enable-skip-login=false |
| No NetworkPolicy | Any pod can reach dashboard | Restrict ingress sources |
| Not updating dashboard | Known vulnerabilities | Keep updated |

---

## Quiz

1. **What is the most secure way to access the Kubernetes dashboard?**
   <details>
   <summary>Answer</summary>
   Using `kubectl proxy` - it binds only to localhost and uses your kubeconfig credentials. The dashboard inherits your RBAC permissions.
   </details>

2. **What argument disables the dashboard skip button?**
   <details>
   <summary>Answer</summary>
   `--enable-skip-login=false` - Add this to the dashboard container arguments to prevent anonymous access.
   </details>

3. **Why shouldn't the dashboard use a cluster-admin ServiceAccount?**
   <details>
   <summary>Answer</summary>
   Cluster-admin has full access to everything. If the dashboard is compromised, attackers get complete control over the cluster. Use minimal permissions instead.
   </details>

4. **What happened in the Tesla Kubernetes breach?**
   <details>
   <summary>Answer</summary>
   Tesla exposed their Kubernetes dashboard without authentication. Attackers accessed it, discovered AWS credentials in environment variables, and used cluster resources for cryptocurrency mining.
   </details>

---

## Hands-On Exercise

**Task**: Secure a Kubernetes dashboard installation.

```bash
# Step 1: Install dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Step 2: Wait for deployment
kubectl wait --for=condition=available deployment/kubernetes-dashboard -n kubernetes-dashboard --timeout=120s

# Step 3: Create restricted ServiceAccount
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-readonly
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-readonly
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dashboard-readonly
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dashboard-readonly
subjects:
- kind: ServiceAccount
  name: dashboard-readonly
  namespace: kubernetes-dashboard
EOF

# Step 4: Disable skip button
kubectl patch deployment kubernetes-dashboard -n kubernetes-dashboard \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--enable-skip-login=false"}]'

# Step 5: Create NetworkPolicy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-ingress
  namespace: kubernetes-dashboard
spec:
  podSelector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  policyTypes:
  - Ingress
  ingress: []  # Deny all ingress - only kubectl proxy works
EOF

# Step 6: Get token for readonly user
kubectl create token dashboard-readonly -n kubernetes-dashboard

# Step 7: Access via proxy
kubectl proxy &
echo "Access dashboard at: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"

# Cleanup
kubectl delete namespace kubernetes-dashboard
```

**Success criteria**: Dashboard requires token, skip is disabled, NetworkPolicy restricts access.

---

## Summary

**Dashboard Risks**:
- Full cluster access if misconfigured
- Skip button allows anonymous access
- Public exposure invites attacks

**Security Measures**:
- Minimal RBAC (never cluster-admin)
- Disable skip button
- Use kubectl proxy for access
- NetworkPolicy restrictions

**Best Practices**:
- Consider not installing dashboard
- Use kubectl, Lens, or K9s instead
- If needed, restrict access heavily
- Token authentication only

**Exam Tips**:
- Know how to create minimal ServiceAccount
- Know the skip button argument
- Understand kubectl proxy is most secure

---

## Part 1 Complete!

You've finished **Cluster Setup** (10% of CKS). You now understand:
- Network Policies for segmentation
- CIS Benchmarks with kube-bench
- Ingress TLS and security headers
- Metadata service protection
- Dashboard security hardening

**Next Part**: [Part 2: Cluster Hardening](../part2-cluster-hardening/module-2.1-rbac-deep-dive/) - RBAC, ServiceAccounts, and API security.
