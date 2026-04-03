---
title: "Module 3.3: Secrets Management"
slug: k8s/kcsa/part3-security-fundamentals/module-3.3-secrets
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 3.2: RBAC Fundamentals](../module-3.2-rbac/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Assess** the security limitations of Kubernetes Secrets (base64 encoding, etcd storage)
2. **Evaluate** secrets management strategies: encryption at rest, external secret stores, sealed secrets
3. **Identify** common secrets exposure risks: environment variable leaks, RBAC over-access, unencrypted etcd
4. **Explain** how to implement encryption at rest and integrate external secret management tools

---

## Why This Module Matters

Secrets—passwords, API keys, certificates—are prime targets for attackers. Kubernetes has built-in Secrets resources, but they're not encrypted by default. Understanding the limitations and best practices for secrets management is critical for securing sensitive data.

Many organizations fail their first security audit due to improper secrets handling in Kubernetes.

---

## Kubernetes Secrets Overview

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES SECRETS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT SECRETS ARE:                                         │
│  • Key-value store for sensitive data                      │
│  • Mounted into pods as files or env vars                  │
│  • Separate from application config (ConfigMaps)           │
│                                                             │
│  WHAT SECRETS ARE NOT:                                     │
│  • Encrypted by default (just base64 encoded)              │
│  • Protected from users with get secrets permission        │
│  • A complete secrets management solution                  │
│                                                             │
│  IMPORTANT MISCONCEPTION:                                  │
│  Base64 ≠ Encryption                                       │
│  Base64 is encoding, not security!                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Secret Types

```yaml
# Generic/Opaque secret (most common)
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  password: cGFzc3dvcmQxMjM=  # base64 encoded
stringData:                    # Plain text (encoded at creation)
  api-key: my-api-key
```

### Built-in Secret Types

| Type | Description | Usage |
|------|-------------|-------|
| `Opaque` | Generic secret | Application credentials |
| `kubernetes.io/tls` | TLS cert + key | Ingress, service TLS |
| `kubernetes.io/dockerconfigjson` | Docker registry auth | Image pull secrets |
| `kubernetes.io/basic-auth` | Username + password | Basic authentication |
| `kubernetes.io/ssh-auth` | SSH private key | SSH authentication |
| `kubernetes.io/service-account-token` | SA token | Service account auth |

---

## Using Secrets in Pods

### As Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:1.0
    env:
    # Single key
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
    # Or all keys
    envFrom:
    - secretRef:
        name: app-secrets
```

### As Volume Mounts

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: app-secrets
      # Optional: specific keys only
      items:
      - key: password
        path: db-password
```

### Which Method is Better?

```
┌─────────────────────────────────────────────────────────────┐
│              ENV VARS vs VOLUME MOUNTS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENVIRONMENT VARIABLES                                     │
│  ├── Pros:                                                 │
│  │   └── Simple to use in application                      │
│  └── Cons:                                                 │
│      ├── Visible in /proc/<pid>/environ                    │
│      ├── Often logged accidentally                         │
│      ├── Inherited by child processes                      │
│      └── Not updated when secret changes                   │
│                                                             │
│  VOLUME MOUNTS                                             │
│  ├── Pros:                                                 │
│  │   ├── Can be mounted read-only                          │
│  │   ├── Updated when secret changes (eventually)          │
│  │   └── Less likely to be accidentally logged             │
│  └── Cons:                                                 │
│      └── Requires file reading in application              │
│                                                             │
│  RECOMMENDATION: Prefer volume mounts for sensitive data   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Secrets Security Concerns

### Default Storage (No Encryption)

```
┌─────────────────────────────────────────────────────────────┐
│              SECRET STORAGE IN ETCD                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT ENCRYPTION AT REST:                               │
│                                                             │
│  Secret "password: admin123"                               │
│       │                                                     │
│       ▼ (base64 encode)                                    │
│  Secret "password: YWRtaW4xMjM="                           │
│       │                                                     │
│       ▼ (store in etcd)                                    │
│  etcd: key="/registry/secrets/default/my-secret"           │
│        value="YWRtaW4xMjM=" ← Still readable!              │
│                                                             │
│  Anyone with etcd access can decode all secrets            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### RBAC for Secrets

```
┌─────────────────────────────────────────────────────────────┐
│              SECRETS ACCESS CONTROL                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHO CAN READ SECRETS:                                     │
│  ├── Users with "get secrets" permission                   │
│  ├── Service accounts with "get secrets" permission        │
│  ├── Anyone with etcd access                               │
│  └── Node (kubelet) for pods scheduled there               │
│                                                             │
│  RISKS:                                                    │
│  • `get secrets` in RBAC = read ALL secrets in scope       │
│  • No field-level access control                           │
│  • Listing secrets shows all names (potential info leak)   │
│                                                             │
│  BEST PRACTICES:                                           │
│  • Minimize who has `get secrets` permission               │
│  • Use namespace isolation for secret scope                │
│  • Audit secret access                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Encryption at Rest

Enable encryption to protect secrets in etcd:

```yaml
# EncryptionConfiguration
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      - identity: {}  # Fallback for reading unencrypted
```

### Encryption Providers

| Provider | Description | Use Case |
|----------|-------------|----------|
| `identity` | No encryption | Never for secrets |
| `aescbc` | AES-CBC encryption | Self-managed clusters |
| `aesgcm` | AES-GCM encryption | Faster than aescbc |
| `kms` | External KMS | Production, compliance |
| `secretbox` | XSalsa20 + Poly1305 | Alternative to AES |

### KMS Integration

```
┌─────────────────────────────────────────────────────────────┐
│              KMS ENCRYPTION                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENVELOPE ENCRYPTION:                                      │
│                                                             │
│  Secret ──→ Encrypt with DEK ──→ Encrypted Secret          │
│                                        │                    │
│                                        ▼                    │
│  DEK (Data Encryption Key)         Store in etcd           │
│       │                                                     │
│       ▼ Encrypt with KEK (in KMS)                          │
│  Encrypted DEK ──→ Store alongside secret                  │
│                                                             │
│  BENEFITS:                                                 │
│  • Key rotation without re-encrypting all secrets          │
│  • Key never leaves KMS                                    │
│  • Audit logging in KMS                                    │
│  • Compliance requirements met                             │
│                                                             │
│  PROVIDERS: AWS KMS, GCP KMS, Azure Key Vault, HashiCorp  │
│             Vault                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## External Secrets Management

For production, consider external secrets managers:

```
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL SECRETS MANAGERS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HASHICORP VAULT                                           │
│  ├── Full-featured secrets management                      │
│  ├── Dynamic secrets (short-lived)                         │
│  ├── Encryption as a service                               │
│  └── Kubernetes auth method                                │
│                                                             │
│  CLOUD PROVIDER SECRETS                                    │
│  ├── AWS Secrets Manager                                   │
│  ├── GCP Secret Manager                                    │
│  ├── Azure Key Vault                                       │
│  └── CSI driver integration                                │
│                                                             │
│  KUBERNETES OPERATORS                                      │
│  ├── External Secrets Operator                             │
│  ├── Secrets Store CSI Driver                              │
│  └── Sync external secrets to K8s Secrets                  │
│                                                             │
│  BENEFITS OVER NATIVE SECRETS:                             │
│  • Centralized management                                  │
│  • Audit logging                                           │
│  • Dynamic/rotating secrets                                │
│  • Access policies                                         │
│  • Works across clusters                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Secrets Store CSI Driver

```yaml
# Mount secrets directly from external store
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: secrets-store
      mountPath: /mnt/secrets
      readOnly: true
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: my-provider
```

---

## Secrets Best Practices

```
┌─────────────────────────────────────────────────────────────┐
│              SECRETS MANAGEMENT CHECKLIST                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STORAGE                                                   │
│  ☐ Enable encryption at rest for etcd                      │
│  ☐ Consider external secrets manager for production        │
│  ☐ Use KMS integration if available                        │
│                                                             │
│  ACCESS CONTROL                                            │
│  ☐ Minimize RBAC "get secrets" permissions                 │
│  ☐ Use namespace isolation                                 │
│  ☐ Audit secret access                                     │
│                                                             │
│  USAGE                                                     │
│  ☐ Prefer volume mounts over env vars                      │
│  ☐ Mount as read-only                                      │
│  ☐ Don't log secrets                                       │
│                                                             │
│  LIFECYCLE                                                 │
│  ☐ Rotate secrets regularly                                │
│  ☐ Have a revocation plan                                  │
│  ☐ Don't commit secrets to git                             │
│                                                             │
│  APPLICATION                                               │
│  ☐ Don't hardcode secrets in images                        │
│  ☐ Don't include secrets in container args                 │
│  ☐ Use short-lived credentials when possible               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Base64 is not encryption** - it's trivially reversible. `echo "cGFzc3dvcmQ=" | base64 -d` gives you the original value instantly.

- **Secrets are stored in etcd** alongside all other Kubernetes objects. If etcd is compromised, so are all your secrets.

- **The `view` ClusterRole** doesn't include secrets by design. This is intentional to allow broad read access without exposing sensitive data.

- **Secret updates propagate** to mounted volumes eventually (default ~1 minute), but environment variables require pod restart.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Assuming base64 = encrypted | Secrets readable by anyone with access | Enable encryption at rest |
| Secrets in environment variables | Logged, visible in /proc | Use volume mounts |
| Secrets in Git | Permanent exposure | Use sealed-secrets or external manager |
| Broad `get secrets` RBAC | All secrets accessible | Namespace isolation, minimal access |
| No rotation | Compromised secrets remain valid | Implement rotation process |

---

## Quiz

1. **Why is base64 encoding not sufficient protection for secrets?**
   <details>
   <summary>Answer</summary>
   Base64 is encoding, not encryption. It's trivially reversible—anyone who can read the base64 value can decode it. It provides no security, only convenience for handling binary data.
   </details>

2. **What happens to secrets when encryption at rest is enabled?**
   <details>
   <summary>Answer</summary>
   Secrets are encrypted before being stored in etcd. Even if etcd storage is compromised, the secrets are protected by encryption. You need the encryption key to decrypt them.
   </details>

3. **Why are volume mounts preferred over environment variables for secrets?**
   <details>
   <summary>Answer</summary>
   Environment variables are visible in /proc/<pid>/environ, often logged accidentally, inherited by child processes, and don't update when secrets change. Volume mounts are more secure and update when secrets change.
   </details>

4. **What is envelope encryption in the context of KMS?**
   <details>
   <summary>Answer</summary>
   Envelope encryption uses two keys: a Data Encryption Key (DEK) encrypts the data, and a Key Encryption Key (KEK) in KMS encrypts the DEK. This allows key rotation without re-encrypting all data and keeps the master key in secure hardware.
   </details>

5. **What RBAC permission allows reading all secrets in a namespace?**
   <details>
   <summary>Answer</summary>
   The `get` verb on `secrets` resource. There's no per-secret access control in Kubernetes RBAC—you either can read secrets or you can't. Use namespace isolation to scope access.
   </details>

---

## Hands-On Exercise: Secrets Security Review

**Scenario**: Review this deployment and identify secrets-related security issues:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:latest
        env:
        - name: DB_PASSWORD
          value: "supersecret123"
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secret
              key: key
        command:
        - /app
        - --db-password=$(DB_PASSWORD)
        - --debug
```

**Identify the security issues:**

<details>
<summary>Security Issues</summary>

1. **Hardcoded password in env**
   - `DB_PASSWORD` is directly in the manifest
   - Will be committed to Git, visible in API
   - Fix: Move to a Secret resource

2. **Secret in command args**
   - `--db-password=$(DB_PASSWORD)` exposes secret in process list
   - Visible via `ps aux`, logged in audit logs
   - Fix: Pass via file or env var, read in app

3. **Secret as environment variable**
   - `API_KEY` via env is visible in /proc
   - Fix: Mount as volume instead

4. **Debug mode enabled**
   - `--debug` may log sensitive data
   - Fix: Disable in production

5. **`image: myapp:latest`**
   - Mutable tag, unpredictable version
   - Fix: Use immutable tag with digest

**Secure version:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp@sha256:abc123...
        volumeMounts:
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true
      volumes:
      - name: secrets
        secret:
          secretName: app-secrets
```

</details>

---

## Summary

Kubernetes secrets require careful handling:

| Concern | Default Behavior | Best Practice |
|---------|-----------------|---------------|
| **Storage** | Base64 in etcd | Enable encryption at rest |
| **Access** | RBAC controls | Minimize get secrets permission |
| **Usage** | Env or volume | Prefer volume mounts |
| **Lifecycle** | No rotation | Implement rotation |
| **External** | Not integrated | Consider external manager |

Key points:
- Base64 ≠ Encryption
- Enable etcd encryption at rest
- Use volume mounts over env vars
- Consider external secrets managers
- Minimize who can access secrets

---

## Next Module

[Module 3.4: ServiceAccount Security](../module-3.4-serviceaccounts/) - Securing pod identities and API access.
