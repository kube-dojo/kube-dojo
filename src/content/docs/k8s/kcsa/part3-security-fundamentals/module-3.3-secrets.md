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

> **Stop and think**: A colleague says "our secrets are safe because we enabled RBAC and only admins can access them." What other paths could an attacker use to read secrets even without direct RBAC permission?

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

> **Pause and predict**: You enable encryption at rest for etcd secrets using `aescbc`. A developer uses `kubectl get secret db-creds -o yaml` and sees the secret value in base64. Does this mean encryption at rest isn't working?

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

1. **A compliance audit discovers that your team stores database passwords as Kubernetes Secrets without encryption at rest. The team lead says "base64 encoding protects them." Explain why this is wrong and what the actual risk is if etcd is compromised.**
   <details>
   <summary>Answer</summary>
   Base64 is encoding, not encryption — it's trivially reversible with `echo "value" | base64 -d`. If etcd is compromised (through direct access, backup exposure, or etcd API access), all secrets are readable in plaintext. Base64 provides zero security; it's just a data format for handling binary data in YAML. The fix is enabling encryption at rest with an EncryptionConfiguration that uses aescbc or KMS. With encryption, even if etcd storage is stolen, secrets are encrypted and require the encryption key to read.
   </details>

2. **Your application uses environment variables to inject database credentials into pods. During incident response, you discover the credentials appeared in application crash dumps and container inspection output. What happened, and what delivery method would prevent this?**
   <details>
   <summary>Answer</summary>
   Environment variables are visible through multiple paths: `/proc/<pid>/environ` inside the container, `kubectl describe pod` output, container runtime inspection, crash dumps, and child processes that inherit all environment variables. They're also commonly logged accidentally by debugging middleware. The safer alternative is volume mounts: mount the secret as a file at a specific path (e.g., `/etc/secrets/db-password`), set it as read-only, and have the application read from the file. Volume mounts don't appear in process listings, aren't inherited by child processes, and can be updated when secrets rotate.
   </details>

3. **You enable encryption at rest for secrets using the `aescbc` provider with `identity` as a fallback. After enabling it, a colleague runs `kubectl get secret -o yaml` and sees the value in base64. They claim encryption isn't working. Are they correct?**
   <details>
   <summary>Answer</summary>
   They are incorrect. Encryption at rest protects data stored in etcd, not data returned by the API server. When `kubectl get secret` retrieves a secret, the API server decrypts it from etcd and returns the base64-encoded value to the authorized user. The base64 output is expected — it's the API's response format. To verify encryption is working, you'd need to read directly from etcd (bypassing the API server) and confirm the data is encrypted. The `identity` fallback allows reading pre-existing unencrypted secrets; after enabling encryption, you should re-encrypt all secrets and can then optionally remove the identity fallback.
   </details>

4. **Your organization uses HashiCorp Vault for secrets management but a team continues creating native Kubernetes Secrets manually. What risks does this dual approach create, and how would you enforce a single source of truth?**
   <details>
   <summary>Answer</summary>
   Dual management creates risks: manually created secrets lack Vault's audit logging, automatic rotation, and access policies. They may not be encrypted at rest if the cluster isn't configured for it. There's no centralized visibility into which secrets exist or who accessed them. Enforcement approach: use an admission controller (Kyverno or OPA) to block creation of Opaque secrets that don't originate from the External Secrets Operator or Vault CSI driver. Allow only the Vault operator's ServiceAccount to create/update secrets. This forces all secrets through Vault's management lifecycle — providing rotation, audit trails, and centralized access control.
   </details>

5. **A namespace has 50 secrets. Three different ServiceAccounts need access to different subsets: SA-A needs the database credentials, SA-B needs the API keys, and SA-C needs TLS certificates. How would you implement this given that Kubernetes RBAC for secrets is all-or-nothing within a namespace?**
   <details>
   <summary>Answer</summary>
   Kubernetes RBAC cannot grant access to individual secrets within a namespace — `get secrets` grants access to all secrets in scope. Solutions: (1) Split secrets into separate namespaces by category (database-ns, api-keys-ns, tls-ns) and grant each SA access only to its namespace; (2) Use `resourceNames` in RBAC rules to restrict to specific secret names (e.g., `resourceNames: ["db-creds"]`), though this is brittle and requires maintenance as secrets change; (3) Use an external secrets manager (Vault) with per-path access policies that provide fine-grained access control Kubernetes RBAC cannot. Option 3 is the most robust for production environments.
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
