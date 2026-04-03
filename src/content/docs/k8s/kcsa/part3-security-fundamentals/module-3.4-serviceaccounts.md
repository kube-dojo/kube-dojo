---
title: "Module 3.4: ServiceAccount Security"
slug: k8s/kcsa/part3-security-fundamentals/module-3.4-serviceaccounts
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 3.3: Secrets Management](../module-3.3-secrets/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Assess** ServiceAccount configurations for excessive API access and auto-mounted tokens
2. **Evaluate** the risk of default ServiceAccount usage across cluster namespaces
3. **Identify** lateral movement paths enabled by misconfigured ServiceAccount permissions
4. **Explain** bound token volume projection and how it reduces token exposure risks

---

## Why This Module Matters

ServiceAccounts are how pods authenticate to the Kubernetes API. Every pod runs with a ServiceAccount, and by default, that account may have more access than needed. Understanding ServiceAccount security is crucial for implementing least privilege for workloads.

Misconfigured ServiceAccounts are a common attack vector for lateral movement within clusters.

---

## ServiceAccount Basics

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICEACCOUNT OVERVIEW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT IS A SERVICEACCOUNT?                                 │
│  • Identity for pods to authenticate to API server         │
│  • Namespace-scoped resource                               │
│  • Every pod has one (default if not specified)            │
│                                                             │
│  HOW IT WORKS:                                             │
│  1. Pod created with serviceAccountName                    │
│  2. Token projected into pod at /var/run/secrets/...       │
│  3. Pod uses token to authenticate API requests            │
│  4. API server validates token, extracts identity          │
│  5. RBAC checked against ServiceAccount                    │
│                                                             │
│  DEFAULT SERVICEACCOUNT:                                   │
│  • Every namespace has "default" ServiceAccount            │
│  • Pods use it if none specified                           │
│  • May have unintended permissions                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ServiceAccount Tokens

### Token Evolution

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICEACCOUNT TOKEN TYPES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LEGACY TOKENS (pre-1.24)                                  │
│  ├── Stored in Secrets                                     │
│  ├── Never expire                                          │
│  ├── Not audience-bound                                    │
│  ├── Auto-mounted to all pods                              │
│  └── SECURITY RISK - avoid                                 │
│                                                             │
│  BOUND SERVICE ACCOUNT TOKENS (1.24+)                      │
│  ├── JWT tokens signed by API server                       │
│  ├── Time-limited (default 1 hour, configurable)           │
│  ├── Audience-bound (specific to intended recipient)       │
│  ├── Projected via volume (not Secret)                     │
│  └── Automatically rotated before expiration               │
│                                                             │
│  TOKEN LOCATION IN POD:                                    │
│  /var/run/secrets/kubernetes.io/serviceaccount/            │
│  ├── token     - The JWT token                             │
│  ├── ca.crt    - Cluster CA certificate                    │
│  └── namespace - Pod's namespace                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: Every pod gets a ServiceAccount token mounted by default. If most of your pods never call the Kubernetes API, what is the security cost of leaving auto-mounting enabled?

### Token Request API

Create tokens programmatically:

```yaml
apiVersion: authentication.k8s.io/v1
kind: TokenRequest
metadata:
  name: my-token
  namespace: default
spec:
  audiences:
  - api                      # Who can use this token
  expirationSeconds: 3600    # 1 hour
  boundObjectRef:            # Optional: bind to specific pod
    kind: Pod
    name: my-pod
    uid: abc-123
```

---

## ServiceAccount Configuration

### Basic ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app
  namespace: production
automountServiceAccountToken: false  # Don't auto-mount token
```

### Using ServiceAccount in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  serviceAccountName: my-app
  automountServiceAccountToken: false  # Override at pod level
  containers:
  - name: app
    image: myapp:1.0
```

### Projected Token (When Needed)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api-client
spec:
  serviceAccountName: api-caller
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
          path: api-token
          expirationSeconds: 3600
          audience: api
```

---

## Default ServiceAccount Issues

```
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT SERVICEACCOUNT RISKS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROBLEM:                                                  │
│  • Every namespace has "default" ServiceAccount            │
│  • Pods use it automatically if not specified              │
│  • Token auto-mounted to pods                              │
│  • May have roles bound (often more than needed)           │
│                                                             │
│  ATTACK SCENARIO:                                          │
│  1. Attacker compromises application container             │
│  2. Reads token from /var/run/secrets/...                  │
│  3. Uses token to query Kubernetes API                     │
│  4. Discovers secrets, other pods, escalates               │
│                                                             │
│  MITIGATIONS:                                              │
│  • Disable auto-mount for default SA                       │
│  • Create dedicated SAs for each application               │
│  • Don't bind roles to default SA                          │
│  • Use automountServiceAccountToken: false                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Securing the Default ServiceAccount

```yaml
# Disable token mounting on default SA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default
  namespace: production
automountServiceAccountToken: false
```

---

> **Pause and predict**: Bound service account tokens expire after 1 hour by default. What happens to a long-running pod when its token expires? Does the pod crash?

## Workload Identity

Map Kubernetes ServiceAccounts to cloud provider identities:

```
┌─────────────────────────────────────────────────────────────┐
│              WORKLOAD IDENTITY                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT WORKLOAD IDENTITY:                                │
│  • Store cloud credentials as K8s Secrets                  │
│  • Long-lived, static credentials                          │
│  • Same credentials for all pods using the Secret          │
│  • Manual rotation required                                │
│                                                             │
│  WITH WORKLOAD IDENTITY:                                   │
│  • K8s ServiceAccount → Cloud IAM role                     │
│  • Short-lived, auto-rotated tokens                        │
│  • Per-pod identity                                        │
│  • No static credentials                                   │
│                                                             │
│  IMPLEMENTATIONS:                                          │
│  • AWS: IAM Roles for Service Accounts (IRSA)              │
│  • GCP: Workload Identity                                  │
│  • Azure: Workload Identity (formerly AAD Pod Identity)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### AWS IRSA Example

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-reader
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456:role/S3Reader
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  serviceAccountName: s3-reader
  containers:
  - name: app
    image: myapp:1.0
    # AWS SDK automatically uses projected token
```

---

## ServiceAccount Best Practices

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICEACCOUNT SECURITY CHECKLIST              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MINIMIZE ACCESS                                           │
│  ☐ Create dedicated SA per application                     │
│  ☐ Don't reuse SAs across different apps                   │
│  ☐ Grant minimal RBAC permissions                          │
│  ☐ Use namespace-scoped roles                              │
│                                                             │
│  TOKEN MANAGEMENT                                          │
│  ☐ Disable auto-mount when API access not needed          │
│  ☐ Use bound tokens (short-lived, audience-bound)          │
│  ☐ Clean up legacy token Secrets                           │
│                                                             │
│  CLOUD INTEGRATION                                         │
│  ☐ Use workload identity instead of static credentials     │
│  ☐ Map SAs to cloud roles with least privilege             │
│                                                             │
│  DEFAULT SA                                                │
│  ☐ Disable auto-mount on default SA                        │
│  ☐ Don't bind roles to default SA                          │
│  ☐ Explicitly specify SA in all pods                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ServiceAccount Attack Vectors

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICEACCOUNT ATTACK SCENARIOS                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TOKEN THEFT                                               │
│  1. Compromise container                                   │
│  2. Read /var/run/secrets/.../token                       │
│  3. Use token to access API                                │
│  Mitigation: automountServiceAccountToken: false           │
│                                                             │
│  PRIVILEGE ESCALATION                                      │
│  1. SA has create pods permission                          │
│  2. Create privileged pod with same SA                     │
│  3. Escape to host                                         │
│  Mitigation: Don't give SAs create pods permission         │
│                                                             │
│  SECRET EXTRACTION                                         │
│  1. SA has get secrets permission                          │
│  2. Query API for all secrets                              │
│  3. Extract credentials                                    │
│  Mitigation: Minimal RBAC, namespace isolation             │
│                                                             │
│  LATERAL MOVEMENT                                          │
│  1. SA has list pods permission                            │
│  2. Discover other applications                            │
│  3. Target other pods                                      │
│  Mitigation: Network policies, minimal RBAC                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Every pod has a ServiceAccount** - if you don't specify one, it uses the `default` SA in the namespace.

- **Bound tokens are JWTs** - you can decode them (header + payload) but not forge them without the signing key.

- **Legacy tokens persist** - even though Kubernetes 1.24+ uses bound tokens by default, old Secret-based tokens may still exist in your cluster.

- **automountServiceAccountToken** can be set at both ServiceAccount and Pod level. Pod-level overrides SA-level.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using default SA | Shared, may have roles | Create dedicated SAs |
| Token always mounted | Attack surface even when not needed | Set automountServiceAccountToken: false |
| Static cloud credentials | Long-lived, not auditable | Use workload identity |
| Overprivileged SA | Lateral movement possible | Minimal RBAC |
| Same SA for all apps | Shared identity, shared blast radius | Per-app ServiceAccounts |

---

## Quiz

1. **An attacker compromises a web application pod and finds a ServiceAccount token at `/var/run/secrets/kubernetes.io/serviceaccount/token`. The pod uses the `default` ServiceAccount, which has no explicit RBAC bindings. Can the attacker still do damage with this token?**
   <details>
   <summary>Answer</summary>
   Yes, potentially. Even without explicit bindings, the default ServiceAccount can perform API discovery (listing API groups and resources). The attacker can enumerate the cluster's API surface, check their permissions with `kubectl auth can-i --list`, and discover any system:authenticated bindings that grant additional permissions. In some clusters, default ServiceAccounts have been given unintended access through broad ClusterRoleBindings. The token also reveals the cluster's internal DNS and API server address, aiding further reconnaissance. Prevention: set `automountServiceAccountToken: false` on pods that don't need API access.
   </details>

2. **Your cluster was upgraded from Kubernetes 1.23 to 1.26. A security scan reveals 200+ legacy ServiceAccount token Secrets still exist. Why are these more dangerous than the bound tokens used by current pods, and how would you remediate?**
   <details>
   <summary>Answer</summary>
   Legacy tokens are dangerous because they never expire (valid indefinitely), are not audience-bound (usable against any API), and persist even after the pod that created them is deleted — they remain as Secret objects. If any were leaked (through etcd access, RBAC over-permission, or backup exposure), the attacker has permanent API access. Remediation: identify all legacy token Secrets (`kubectl get secrets --field-selector type=kubernetes.io/service-account-token`), check if any running workloads still reference them via volume mounts, migrate those workloads to use projected bound tokens, then delete the legacy Secret objects.
   </details>

3. **A team stores AWS credentials as Kubernetes Secrets for their pods to access S3. You recommend switching to IRSA (IAM Roles for Service Accounts). They push back: "What's wrong with Secrets? They work fine." Articulate the security advantages of workload identity.**
   <details>
   <summary>Answer</summary>
   Static credentials in Secrets are long-lived (never rotate automatically), shared across all pods using that Secret (same blast radius), accessible to anyone with `get secrets` RBAC permission, stored in etcd (vulnerable to etcd compromise), and require manual rotation. IRSA provides: short-lived tokens (auto-rotated, typically 1-hour expiry), per-pod identity (each pod gets its own credential), no static secrets in the cluster, automatic credential management by the cloud provider, and audit trails through IAM CloudTrail logging. If a pod is compromised with IRSA, the stolen token expires quickly; with static credentials, the attacker has indefinite S3 access.
   </details>

4. **You set `automountServiceAccountToken: false` on both the ServiceAccount and the Pod spec. But a specific pod in the namespace legitimately needs API access for leader election. How would you grant it a token while keeping other pods token-free?**
   <details>
   <summary>Answer</summary>
   Create a dedicated ServiceAccount for that pod (e.g., `leader-election-sa`) with `automountServiceAccountToken: false` at the SA level. In the specific pod spec, use a projected volume to explicitly request a bound token: define a `projected` volume with `serviceAccountToken` source, set a short `expirationSeconds` (e.g., 3600), and specify the appropriate `audience`. This gives the pod a time-limited, audience-bound token without auto-mounting. Pair this with a minimal RBAC Role that only grants the verbs and resources needed for leader election (create/get/update on leases).
   </details>

5. **During incident response, you discover a pod was compromised and the attacker used its ServiceAccount to create a new privileged pod in the same namespace. Trace the attack chain and identify which controls at each step would have prevented it.**
   <details>
   <summary>Answer</summary>
   Attack chain: (1) Application compromised -> (2) Read auto-mounted SA token -> (3) SA had `create pods` permission -> (4) Created privileged pod -> (5) Container escape to host. Prevention at each step: (1) Application security, image scanning; (2) `automountServiceAccountToken: false` would block token access; (3) Minimal RBAC — the SA should not have had `create pods` permission; (4) Pod Security Standards (Baseline/Restricted) enforcement would reject the privileged pod at admission; (5) seccomp/AppArmor would limit escape even if the pod were somehow created. Defense in depth means any single control could have broken this chain.
   </details>

---

## Hands-On Exercise: ServiceAccount Security Review

**Scenario**: Review this setup and identify security issues:

```yaml
# ServiceAccount with too much access
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: app-admin
subjects:
- kind: ServiceAccount
  name: app-sa
  namespace: default
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  namespace: default
spec:
  # serviceAccountName not specified
  containers:
  - name: app
    image: nginx:1.25
```

**Identify the security issues:**

<details>
<summary>Security Issues</summary>

1. **cluster-admin bound to app-sa**
   - Full cluster access from any pod using app-sa
   - Massive over-privilege
   - Fix: Use minimal, namespace-scoped Role

2. **ClusterRoleBinding instead of RoleBinding**
   - Grants cluster-wide permissions
   - Fix: Use RoleBinding for namespace scope

3. **ServiceAccount in default namespace**
   - default namespace often not properly secured
   - Fix: Use dedicated namespace

4. **Pod doesn't specify serviceAccountName**
   - Will use `default` SA, not `app-sa`
   - The app-sa with cluster-admin is unused here
   - But `default` SA might have its own issues

5. **No automountServiceAccountToken: false**
   - Token mounted unnecessarily
   - nginx doesn't need API access
   - Fix: Add automountServiceAccountToken: false

**Secure version:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: nginx-sa
  namespace: production
automountServiceAccountToken: false
---
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  namespace: production
spec:
  serviceAccountName: nginx-sa
  automountServiceAccountToken: false
  containers:
  - name: app
    image: nginx:1.25
# No RBAC binding needed if pod doesn't access API
```

</details>

---

## Summary

ServiceAccount security is about controlling pod identity:

| Aspect | Risk | Mitigation |
|--------|------|------------|
| **Default SA** | Shared identity | Create dedicated SAs |
| **Token mounting** | Attack surface | automountServiceAccountToken: false |
| **RBAC** | Over-privilege | Minimal, namespace-scoped |
| **Cloud access** | Static credentials | Use workload identity |
| **Legacy tokens** | Never expire | Clean up, use bound tokens |

Key principles:
- One ServiceAccount per application
- Disable token mounting unless needed
- Use bound tokens (Kubernetes 1.24+)
- Integrate with cloud workload identity
- Never give more RBAC than necessary

---

## Next Module

[Module 3.5: Network Policies](../module-3.5-network-policies/) - Controlling pod-to-pod network traffic.
