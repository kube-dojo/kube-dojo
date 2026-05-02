---
revision_pending: false
title: "Module 3.3: Secrets Management"
slug: k8s/kcsa/part3-security-fundamentals/module-3.3-secrets
sidebar:
  order: 4
---

# Module 3.3: Secrets Management

**Complexity**: `[MEDIUM]` - Core knowledge. **Time to Complete**: 25-30 minutes. **Prerequisites**: [Module 3.2: RBAC Fundamentals](../module-3.2-rbac/). This module assumes Kubernetes 1.35 or newer and uses `k` as the `kubectl` alias after you define it with `alias k=kubectl` in your shell.

## Learning Outcomes

After completing this module, you will be able to:

1. **Assess** the security limitations of Kubernetes Secrets, including base64 encoding, etcd storage, API visibility, and node-level access paths.
2. **Evaluate** secrets management strategies such as encryption at rest, KMS envelope encryption, external secret stores, and sealed secret workflows.
3. **Diagnose** common secrets exposure risks involving environment variables, command arguments, RBAC over-access, logs, Git history, and unencrypted backups.
4. **Implement** a safer secret delivery plan that uses least-privilege RBAC, read-only volume mounts, rotation practices, and an appropriate external source of truth.

## Why This Module Matters

An operations team at a mid-sized payments company spent a long weekend investigating why a routine database password rotation kept failing. The first clue was not a Kubernetes event or an application alert; it was a security engineer finding the old password in a crash report that had been uploaded to an internal ticket. The team traced the value through a Deployment manifest, an environment variable, a process argument, a debug log, and finally a stale Secret stored in a cluster backup. The secret had not been exploited, but the audit response still consumed several engineering days, delayed a product launch, and forced emergency rotation of credentials across multiple environments.

That story is uncomfortable because every individual decision looked ordinary at the time. Kubernetes Secrets were used instead of ConfigMaps, RBAC existed, and only a small group could administer the namespace. The problem was that the team treated a Secret object as a vault instead of as an API object with special handling rules. Once a sensitive value enters the Kubernetes API, it can be copied into etcd, delivered to kubelets, mounted into pods, exposed to authorized clients, included in backups, and accidentally printed by applications that were never designed to protect credentials.

This module teaches you to reason about those paths before you choose a tool. Native Kubernetes Secrets are useful, but they are not a complete secrets management program by themselves. You will assess where the data travels, decide when encryption at rest is enough, recognize when an external secrets manager is a better source of truth, and practice reviewing a workload that leaks sensitive data through several common channels. Pause as you read and ask a practical question: if you had to rotate this credential during an incident, how many places would you need to inspect before trusting the rotation?

## Kubernetes Secrets Overview: Base64, API Objects, and Trust Boundaries

Kubernetes Secrets exist because applications need sensitive inputs without baking those values into container images or plain configuration files. They give the API server a standard object for small pieces of confidential data, usually credentials, private keys, certificates, or tokens. That standardization matters because controllers, kubelets, admission policies, RBAC, backup tools, and deployment workflows can all recognize the same resource type instead of inventing a different credential format for every workload. A Secret is not magic; it is a Kubernetes object with a narrower purpose and a higher operational burden.

The first misconception to remove is that base64 is encryption. Kubernetes stores Secret data in base64 because the API object is JSON or YAML and secret values can contain arbitrary bytes. Encoding makes the data portable through the API, but anyone who can read the encoded value can decode it immediately. Treat base64 like putting a document in a clear plastic sleeve: it protects the shape of the paper, not the contents from the person holding it. If a user has `get` access to Secrets, the API server returns data they can decode.

```text
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

The diagram is intentionally blunt because the most expensive mistakes often begin with language that sounds harmless. Teams say a value is "in a Secret" and mentally file it under "safe." A more accurate sentence is "the value is stored in a Kubernetes object that receives special delivery behavior and should be protected by RBAC, encryption at rest, audit logging, namespace design, and application discipline." That longer sentence is less convenient, but it describes the real security boundary.

Secret objects are namespaced. That means the default unit of isolation is usually the namespace, not the individual key inside the Secret. RBAC can restrict access by resource and sometimes by `resourceNames`, but Kubernetes does not provide field-level permissions that let one user read only `username` while another reads only `password` from the same object. The design pushes teams toward smaller namespaces, narrower service accounts, and external systems when they need policy decisions more granular than the Kubernetes API can express cleanly.

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

The `data` field contains base64-encoded values, while `stringData` lets you submit plain text and have the API server encode it when the object is created or updated. That convenience is useful for handwritten examples, but it does not make the value safer. The manifest still contains the secret value before submission, and any GitOps tool, CI log, shell history, or pull request that handles the manifest can accidentally preserve it. In production, a generated or synchronized workflow should usually create the object rather than asking humans to type sensitive values into YAML files.

### Built-in Secret Types

| Type | Description | Usage |
|------|-------------|-------|
| `Opaque` | Generic secret | Application credentials |
| `kubernetes.io/tls` | TLS cert + key | Ingress, service TLS |
| `kubernetes.io/dockerconfigjson` | Docker registry auth | Image pull secrets |
| `kubernetes.io/basic-auth` | Username + password | Basic authentication |
| `kubernetes.io/ssh-auth` | SSH private key | SSH authentication |
| `kubernetes.io/service-account-token` | SA token | Service account auth |

Secret `type` is partly documentation and partly validation. A `kubernetes.io/tls` Secret must contain the expected certificate and key fields, while an `Opaque` Secret can hold arbitrary names. The type does not choose a stronger encryption mode, and it does not automatically rotate the value. The value of typing is that humans and controllers can reason about intent: a registry pull secret should be referenced by image pull configuration, a TLS secret should feed ingress or service TLS, and an arbitrary app credential should be named and scoped so its purpose is obvious during review.

A practical review starts by drawing the trust boundary around the Secret. Who can create it, update it, read it through the API, mount it through a pod, back it up, or inspect the node where it is used? Those questions matter more than whether the object looks clean in YAML. A Secret that is never committed to Git but is readable by every service account in a shared namespace is still a weak design. A Secret that is tightly scoped but printed by the application on startup is also weak.

Think of a Secret as a package that moves through a building with many doors. The package may be marked confidential, but the label does not lock the mailroom, the elevator, the recipient’s desk, or the recycling bin. Kubernetes gives you a package format and a delivery system; your security design decides which doors are locked and which people can carry the package. That mental model helps beginners avoid the false comfort of a single control. It also helps experienced operators explain why a finding can be real even when another layer appears correctly configured.

**Pause and predict:** if a developer runs `k get secret app-secrets -o yaml` and can see `cGFzc3dvcmQxMjM=`, what is the security failure: base64, RBAC, encryption at rest, or all of those depending on the path? Write down your answer before continuing, because the distinction will guide how you debug real incidents.

The best answer is that the visible base64 is expected behavior for an authorized API read. If the developer should not have the Secret, the immediate failure is RBAC or namespace design. If the concern is stolen etcd storage or backups, the relevant control is encryption at rest. If the same value also appears in logs, process arguments, or Git history, the object storage control is not enough. A mature secrets review follows the credential through its whole lifecycle instead of stopping at the Kubernetes resource boundary.

## Using Secrets in Pods: Delivery Choices and Runtime Exposure

Once a Secret exists, Kubernetes needs to deliver it to workloads. The two common native delivery choices are environment variables and volume mounts. Both are legitimate API features, and both are widely used, but they have different failure modes. Environment variables are convenient because many applications already read configuration from the environment. Volume mounts require the application to read files, but they reduce several accidental exposure paths and support eventual updates when the mounted Secret changes.

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

Environment variables are attractive because they keep application startup simple. The problem is that an environment variable is part of process state, not just a configuration input. It can be inherited by child processes, surfaced in diagnostic tools, included in crash dumps, captured by overly broad debug logging, or exposed to anyone who can inspect the process environment inside the container. Some teams discover this only during incident response, when they search logs for an error string and find credentials printed next to the error.

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

Volume mounts move the secret value into files owned by the pod filesystem view. That design is not automatically safe, because the application can still read and leak the file, but it gives you better control over how the value is consumed. You can mount only the needed keys, choose an application-specific path, set the mount read-only, and avoid placing credentials in process-wide environment state. Mounted Secret volumes can also update after the Secret changes, although applications often need their own reload behavior to notice the new file content.

> **Stop and think**: A colleague says "our secrets are safe because we enabled RBAC and only admins can access them." What other paths could an attacker use to read secrets even without direct RBAC permission? A strong answer includes pod execution rights, node access, application logs, debug endpoints, backup systems, admission-controller mistakes, and any controller that can create a pod mounting the Secret.

The pod creation path is the subtle part. A user who cannot directly `get secrets` may still be able to create a pod that references a Secret and then run code inside that pod to read the mounted value. That is why Kubernetes documentation warns that granting permissions to create pods can indirectly allow access to Secrets available to the service account or namespace. RBAC reviews should therefore examine verbs like `create pods`, `exec`, `attach`, and workload controller permissions, not only direct `get secrets` rules.

### Which Method is Better?

```text
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

The recommendation to prefer volume mounts is a risk-reduction default, not a law. Some twelve-factor applications are built around environment variables, and rewriting them may take time. In that transition, you can still reduce risk by avoiding `envFrom` for large Secret objects, disabling verbose configuration dumps, preventing shell wrappers from echoing command lines, and ensuring crash reporting tools redact sensitive names. The long-term design should move the most sensitive credentials to file mounts or direct external-store mounts, especially when rotation and reload behavior matter.

Before running this in a lab cluster, what output do you expect from `k describe pod app` if a Secret is used through `secretKeyRef`? You should expect to see that an environment variable is sourced from a Secret reference, not the decoded value itself. That is useful, but it is not a complete protection story, because the value still exists in the running process environment once the container starts.

A practical war story: one platform team allowed developers to use `envFrom` for entire Secret objects because it made onboarding quick. Months later, a single shared Secret contained both a database password and an unrelated third-party API token. A service that needed only the database password inherited the API token too, and a debug endpoint printed the whole process environment during a production incident. The fix was not only "use mounts"; it was also to split Secrets by consumer, mount only specific keys, and make secret names reflect the credential owner and rotation plan.

That kind of cleanup is easier when applications have a narrow configuration contract. If a service expects every possible credential in its environment, platform teams cannot reason about which value is actually required. If the service reads one file path for one purpose, reviewers can connect the Secret, the mount, the application code, and the rotation plan. This is why secrets work often becomes application architecture work. A platform can provide the safer delivery pattern, but each workload still needs a clear agreement about what it consumes and what it must never print.

## Secrets Security Concerns: etcd, RBAC, Nodes, and Backups

Secret risk is easiest to reason about when you separate storage, authorization, delivery, and lifecycle. Storage asks what happens if someone obtains etcd data or a backup. Authorization asks who can use the Kubernetes API to read, update, or indirectly mount the Secret. Delivery asks how the value reaches the workload and what runtime paths can expose it. Lifecycle asks whether the value can be rotated, revoked, audited, and removed from old places after an incident.

### Default Storage (No Encryption)

```text
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

In an unencrypted default storage path, the API server persists the Secret object to etcd with the sensitive values encoded but not cryptographically protected by Kubernetes. An attacker who compromises etcd storage, snapshots, or backup media can decode values without needing Kubernetes RBAC. This matters because backup systems often have different access controls than the cluster itself. A storage administrator, cloud backup operator, or misplaced artifact in an object bucket can become a secret-reader even if they never had a Kubernetes account.

Encryption at rest addresses that storage-specific risk, but it does not hide data from authorized API clients. When a user with permission asks the API server for a Secret, the API server decrypts the stored object and returns the normal Secret representation. That distinction prevents a common false alarm: seeing base64 in `k get secret -o yaml` after enabling encryption at rest does not prove encryption failed. It proves the API server did its job for an authorized request. To verify storage encryption, you inspect etcd data or use documented control-plane validation procedures, not normal API output.

### RBAC for Secrets

```text
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

RBAC is the main API-level control, and it deserves more respect than a blanket "admins only" policy. The built-in `view` ClusterRole intentionally excludes Secret reads because Secret access can escalate into broader application access. A user who can read database credentials may not need shell access to damage the system. A service account that can list every Secret in a namespace may discover names that reveal vendors, internal systems, or migration projects even if the values are protected elsewhere.

Use namespace design to make the blast radius understandable. A shared namespace with dozens of applications forces broad compromises: either a service account can read too much, or operators manage brittle `resourceNames` rules that must be updated for every new Secret. Smaller namespaces, one service account per workload, and separate Secrets per consumer make review easier. External stores can add finer-grained policy when Kubernetes RBAC becomes too coarse for the organization’s risk model.

Nodes are another trust boundary. The kubelet on a node receives the Secrets needed by pods scheduled there, and node administrators can often inspect enough runtime state to become secret-readers. That is not a bug; the node must deliver data to workloads. It means secrets management depends on node hardening, workload isolation, admission policy, and scheduling choices. Highly sensitive workloads may require dedicated node pools, stricter debug access, and careful control over who can run privileged pods.

Backups and observability systems complete the picture. A backup tool that stores etcd snapshots without encryption can undo your RBAC design. A logging pipeline that indexes startup configuration can expose environment variables at scale. A support bundle generator can include mounted files unless it is configured to redact known paths. Diagnose secret exposure by following the data into every operational system that copies cluster state, not only by checking the live API.

The review should also include deletion and retention behavior. Removing a Secret from the live namespace does not necessarily remove it from old backups, audit events, support bundles, terminal scrollback, or Git history. That is why prevention is cheaper than cleanup. If a raw value reaches a permanent log or repository, rotation becomes the only reliable containment step, and the team must assume the old value is exposed. Good designs reduce the number of durable systems that ever see the credential, which reduces both incident scope and audit work.

## Encryption at Rest and KMS: Protecting Stored Secrets Without Confusing the API

Encryption at rest protects Secret data stored in etcd by having the API server encrypt selected resources before persistence. In self-managed clusters, this usually means configuring an `EncryptionConfiguration` for the API server. In managed clusters, the cloud provider may expose a setting that integrates with its own key management service. Either way, the control is about stored data and backups. It does not replace RBAC, runtime hardening, secret rotation, or application redaction.

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

Provider order matters because the first provider writes new data and later providers can read older data. The `identity` provider means no encryption, but it is commonly included as a temporary fallback so the API server can read objects that were stored before encryption was enabled. After enabling encryption, existing Secrets are not magically rewritten until they are updated. Operators usually perform a controlled rewrite of existing Secrets, verify encrypted storage, and then decide whether the fallback remains necessary during migration.

### Encryption Providers

| Provider | Description | Use Case |
|----------|-------------|----------|
| `identity` | No encryption | Never for secrets |
| `aescbc` | AES-CBC encryption | Self-managed clusters |
| `aesgcm` | AES-GCM encryption | Faster than aescbc |
| `kms` | External KMS | Production, compliance |
| `secretbox` | XSalsa20 + Poly1305 | Alternative to AES |

The local providers encrypt data using keys that the API server can access. That may satisfy a storage-at-rest requirement, but it still leaves key custody close to the control plane. KMS providers move key operations to an external service or plugin, often using envelope encryption. The API server encrypts each object with a data encryption key, while the key encryption key stays in the KMS. This gives security teams central key policy, audit logs, and rotation controls that fit better with enterprise compliance programs.

### KMS Integration

```text
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

Envelope encryption is like placing each document in its own locked envelope, then locking all envelope keys in a safe with an audit camera. If one document changes, you do not need to rebuild the entire safe. If policy changes, you can rotate or disable the key encryption layer centrally. The tradeoff is operational complexity: the API server now depends on KMS availability and latency, and the cluster team must monitor the provider, rotate keys deliberately, and test disaster recovery before an outage.

> **Pause and predict**: You enable encryption at rest for etcd secrets using `aescbc`. A developer uses `kubectl get secret db-creds -o yaml` and sees the secret value in base64. Does this mean encryption at rest isn't working? The expected answer is no; the API server decrypts data for authorized clients, so storage encryption must be verified at the storage path, not by normal API reads.

Key rotation has two layers. Rotating the encryption configuration key changes which key protects newly written data, but existing objects may still be protected by older providers until they are rewritten. Rotating the application credential inside the Secret is a separate operation that must update the real database, API, certificate, or token issuer. During incident response, confusing those layers wastes time. Storage encryption protects old snapshots; application credential rotation invalidates the value that an attacker might use.

A disciplined implementation plan includes change control for API server configuration, backup of encryption keys, verification against a non-production cluster, and a rollback plan that does not strand existing Secrets. It also includes documentation for application teams explaining that `k get secret` output will still show base64 to authorized users. Without that explanation, teams often file false incidents after the rollout, or worse, assume encryption failed and disable the control because they misunderstood its boundary.

Managed Kubernetes clusters change the operational details but not the reasoning. A cloud console checkbox may hide the API server configuration, key plugin deployment, and control-plane restart sequence, but the team still needs to know which resources are encrypted, which key protects them, how key rotation works, and whether existing objects require a rewrite. Some providers encrypt etcd storage by default with provider-managed keys, while customer-managed key integration may require a separate setting. Treat provider defaults as an input to the design review, not as a substitute for reading the current cluster documentation.

## External Secrets Management: Source of Truth, Sync, and Direct Mounts

Native Secrets are useful for delivering values to pods, but many organizations want the source of truth somewhere outside the cluster. External systems such as HashiCorp Vault, AWS Secrets Manager, Google Secret Manager, Azure Key Vault, and similar platforms provide policy, audit, rotation, replication, and human access workflows that Kubernetes does not try to own. The design question is whether Kubernetes should store a synchronized copy as a native Secret, mount values directly into pods, or receive only short-lived credentials generated on demand.

For production, consider external secrets managers:

```text
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

There are two common integration styles. A sync operator reads from the external store and creates or updates Kubernetes Secret objects. This works well with applications that already consume native Secrets, and it lets existing deployment patterns continue with fewer code changes. The tradeoff is that a copy of the value now exists inside Kubernetes, so RBAC, encryption at rest, and backups still matter. External Secrets Operator is a common example of this model.

A CSI-style integration mounts secrets from the external store into the pod filesystem without requiring a long-lived native Secret copy for every value. This can reduce the number of sensitive objects stored in etcd, and it aligns well with applications that already read credentials from files. The tradeoff is runtime dependency on the provider, node plugin behavior, and application reload semantics. If the external store is unavailable when pods start, workloads may fail even if the cluster itself is healthy.

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

Sealed secret workflows solve a different problem: storing encrypted secret manifests safely in Git. A controller holds the private key inside the cluster, while developers commit encrypted objects that are safe to review and apply. This is useful for GitOps teams, but it is not the same as dynamic secret management. If the underlying database password never rotates, sealing it only makes Git storage safer. You still need ownership, rotation, revocation, and incident procedures for the credential itself.

Which approach would you choose here and why: a small internal tool with one static webhook credential, a payment service using database credentials that rotate monthly, or a multi-cluster platform serving regulated workloads? The internal tool may be acceptable with a native Secret plus encryption at rest and tight RBAC. The payment service benefits from an external source of truth and a tested reload path. The regulated platform probably needs centralized audit, KMS integration, admission policy, and a documented exception process.

The best external secrets implementations are boring in daily use. Developers request a credential through the approved system, the platform synchronizes or mounts it with predictable names, RBAC prevents unrelated workloads from reading it, and rotation is rehearsed before an incident. The weakest implementations add an operator but keep manual native Secrets as an unofficial escape hatch. Once teams have two ways to create secrets, audit trails fragment and stale credentials multiply.

External systems also force you to define identity. A pod that asks Vault, a cloud secret manager, or a CSI provider for a value must prove which workload it is. In Kubernetes, that proof often starts with the service account token and continues through provider-specific trust configuration. If every workload shares one service account, the external store cannot make a meaningful authorization decision. The same least-privilege habit applies at both layers: one workload identity, one narrow policy, one observable path from request to delivered value.

## Secrets Best Practices: Designing for Rotation and Review

A secrets program is a lifecycle, not a resource template. Start with ownership: every credential should have an application owner, an issuing system, a consumer list, a rotation interval, and an emergency revocation path. Then decide how Kubernetes participates. Sometimes Kubernetes stores the value as a native Secret. Sometimes it only mounts a value from a provider. Sometimes it should not see the long-lived secret at all, because workload identity or dynamic credentials are available.

```text
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

The checklist is most useful when you apply it during design review, not after the application is live. Ask how the first version of the secret will be created, how a second version will be deployed, how old pods will stop using the old version, and what evidence proves the old value is gone. If the answer depends on a human remembering five manual commands during a breach, the design is not ready. Reliable rotation is an engineering feature, and it deserves the same testing as deployment rollback.

Audit logging should answer who accessed or changed Secret objects, but logs must not become another leak. Kubernetes audit policy can record request metadata without recording full request bodies for sensitive resources. External secret stores usually add their own audit records, which are valuable because they show access before the value reaches Kubernetes. During an investigation, compare the external store audit, Kubernetes API audit, workload rollout history, and application logs. Disagreement between those systems often reveals unofficial paths.

Admission control can enforce the decisions humans keep forgetting. Policies can reject plain Secret manifests in GitOps namespaces, block `envFrom` against Secret objects, require immutable image references, require approved labels on Secrets, or allow only a controller service account to create certain Secret types. Use policy as a guardrail, not as the only control. A policy that blocks every exception without a documented escalation path will be bypassed; a policy that records warnings but never blocks risky patterns will be ignored.

Naming is a small habit with large debugging value. A Secret named `db` tells you almost nothing during an incident. A Secret named for the application, system, purpose, and owner gives responders a starting point without decoding values. Labels can record ownership and rotation expectations, while annotations can point to an external provider path without exposing the secret itself. Avoid placing secret values or sensitive account identifiers in names, labels, or annotations, because metadata is often more broadly visible than data.

Rotation planning deserves a dry run before production depends on it. A useful rehearsal creates a second credential, updates the Kubernetes delivery path, confirms that new pods authenticate with the new value, watches old pods drain away, and then revokes the old credential at the issuer. The runbook should state what telemetry proves each step succeeded. Without that proof, teams often stop after updating the Secret object and discover later that a long-running pod, cached connection pool, or forgotten batch job still uses the old value.

## Patterns & Anti-Patterns

Use patterns when they make the secure path easier than the insecure path. The goal is not to ban every native Secret or force every team into the most complex provider on day one. The goal is to choose a delivery model whose failure modes are understood, monitored, and acceptable for the credential’s value. The following patterns scale because they combine storage protection, access control, delivery discipline, and rotation ownership.

| Pattern | When to Use | Why It Works | Scaling Considerations |
|---------|-------------|--------------|------------------------|
| Native Secret with encryption at rest and tight RBAC | Low-to-medium sensitivity credentials in a single cluster | Keeps delivery simple while protecting etcd storage and narrowing API readers | Requires namespace discipline, audit policy, and rotation ownership |
| External source of truth synchronized by controller | Teams already using GitOps or provider secret stores | Centralizes ownership while preserving native Kubernetes delivery | Still creates Kubernetes Secret copies, so backups and RBAC remain important |
| CSI direct mount from external store | High-value credentials where etcd copies should be minimized | Reduces stored Secret objects and supports provider-native policy | Adds runtime dependency on provider plugins and application file reload behavior |
| Dynamic short-lived credentials | Databases, cloud APIs, or systems that can issue temporary access | Shrinks the value of leaked credentials and improves revocation | Requires application compatibility, renewal handling, and good observability |

The strongest pattern is the one your team can operate under stress. A perfect external store design that no one can debug at 02:00 is less safe than a simpler design with clear ownership, tested rotation, and reliable monitoring. Start with the credential’s impact. A read-only token for a sandbox tool does not need the same ceremony as production payment database credentials. However, the low-risk path should still avoid Git leaks, hardcoded images, broad RBAC, and unencrypted backups.

Anti-patterns usually arise from convenience pressure. A developer needs a value quickly, a deployment template accepts environment variables, a team copies a working manifest, and the shortcut becomes the standard. Security reviews should look for these habits early because they become harder to remove after applications depend on them. The table below names the failure mode, why teams fall into it, and the better alternative to reach for during design.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Treating base64 as protection | Anyone with the object can decode the value | Use encryption at rest for storage and RBAC for API access |
| One shared Secret per namespace | Workloads receive credentials they do not need | Split by consumer and mount only specific keys |
| Secret values in command arguments | Values appear in process listings and diagnostics | Read from files or provider SDKs at runtime |
| Manual native Secrets alongside external stores | Audit trails fragment and stale credentials persist | Allow only approved controllers to create managed Secrets |
| Rotation as an undocumented manual task | Incidents depend on memory and timing | Rehearse rotation with clear success criteria and rollback |

Notice that the better alternative is rarely just "use tool X." Tools help when they reinforce a lifecycle. The platform team still needs to define who can create provider paths, how application teams request access, what labels or annotations are required, how rotation is tested, and how exceptions expire. A secrets program without an exception process becomes a pile of urgent bypasses. A secrets program with clear defaults and narrow exceptions becomes easier to adopt.

## Decision Framework

Choose the simplest design that protects the credential across its realistic exposure paths. Begin with impact: if this value leaks, what can the attacker do, how quickly can you revoke it, and what evidence would prove revocation worked? Then map operational constraints: does the application read files, environment variables, or provider SDKs; can it reload credentials; and does the platform already operate a reliable external store? Finally, decide where Kubernetes should store, reference, or avoid the sensitive value.

| Decision Point | Choose Native Secret | Choose External Sync | Choose CSI Direct Mount | Choose Dynamic Credentials |
|----------------|----------------------|----------------------|-------------------------|----------------------------|
| Credential sensitivity | Moderate and scoped | Moderate to high with central ownership | High and avoid etcd copies | High and issuer supports short lifetimes |
| Application change required | Low | Low to medium | Medium | Medium to high |
| Rotation expectation | Manual or periodic | Provider-driven with sync | Provider-driven with mount refresh | Automatic renewal or frequent issuance |
| Audit need | Kubernetes audit may be enough | External audit plus Kubernetes events | External audit plus node plugin events | External issuer audit is central |
| Operational risk | Simple cluster dependency | Controller dependency | Provider and CSI dependency | Issuer, renewal, and app dependency |

If you are unsure, walk the credential through four questions. First, who is allowed to know this value outside the application? Second, where is the value persisted after creation? Third, how does the workload receive it at runtime? Fourth, what exact steps rotate and revoke it during an incident? A design that cannot answer those questions is not ready for production, even if it uses a respected secrets tool.

For KCSA-level reasoning, remember the boundary between controls. Encryption at rest protects etcd and backups. RBAC protects API reads and writes. Volume mounts reduce process-level exposure compared with environment variables. External stores centralize policy, audit, and rotation. Admission control keeps teams on the approved path. None of those controls alone prevents every leak, and none of them excuses poor application logging or broad pod creation permissions.

When deciding under time pressure, use a risk ladder. For a low-impact development credential, a native Secret in an isolated namespace with encryption at rest may be enough. For a production credential that grants write access to customer data, raise the bar to external ownership, workload-specific identity, documented rotation, and audit review. For credentials that can be replaced by workload identity or dynamic issuance, challenge whether a long-lived static secret is needed at all. The safest secret is often the one you did not have to store.

## Did You Know?

- **Base64 is not encryption** - it's trivially reversible. `echo "cGFzc3dvcmQ=" | base64 -d` gives you the original value instantly.

- **Secrets are stored in etcd** alongside all other Kubernetes objects. If etcd is compromised, so are all your secrets unless encryption at rest protects the stored representation.

- **The `view` ClusterRole** doesn't include secrets by design. This is intentional to allow broad read access without exposing sensitive data.

- **Secret updates propagate** to mounted volumes eventually, commonly around a minute in ordinary clusters, but environment variables require pod restart because process environments are fixed after startup.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Assuming base64 means encrypted | The YAML output looks transformed, so teams mistake encoding for protection | Enable encryption at rest and teach reviewers that API output remains base64 for authorized reads |
| Putting secrets in environment variables by default | Frameworks make env configuration easy and examples are quick to copy | Prefer read-only volume mounts for sensitive values and redact environment dumps |
| Committing raw Secret manifests to Git | Teams want GitOps without a safe encryption workflow | Use sealed secrets, an external secrets operator, or provider-backed sync from a protected source |
| Granting broad `get secrets` permissions | Operators reuse admin-style roles for convenience | Create workload-specific service accounts, split namespaces, and audit direct Secret reads |
| Ignoring pod creation as an indirect read path | Reviews focus only on direct `get secrets` RBAC | Treat pod creation, exec, attach, and controller permissions as part of the Secret access model |
| Forgetting existing objects after enabling encryption | New writes are encrypted, but old data remains until rewritten | Rewrite existing Secrets during the migration and verify storage through the documented etcd path |
| Rotating the Kubernetes Secret but not the real credential | Teams update the delivery object and forget the issuing system | Rotate at the issuer first, deploy the new value, verify consumers, and revoke the old credential |

## Quiz

<details><summary>1. A compliance audit discovers database passwords stored as Kubernetes Secrets without encryption at rest. The team lead says base64 encoding protects them. What is wrong with that reasoning, and what risk remains if etcd backups leak?</summary>

Base64 is only an encoding format, so anyone who can read the Secret object can reverse it without a key. The storage risk is that etcd snapshots or backups may contain the encoded values in a form that can be decoded outside Kubernetes RBAC. Encryption at rest protects that storage path by encrypting selected resources before persistence. It still does not prevent authorized API users from reading the Secret, so RBAC and audit controls remain necessary.
</details>

<details><summary>2. Your application receives a database password through an environment variable. During incident response, the value appears in a crash report and a diagnostic bundle. What likely happened, and what delivery method should you evaluate first?</summary>

Environment variables become part of process state, so debugging tools, crash reporters, child processes, and support bundles can capture them. The safer native delivery method is usually a read-only Secret volume mount with only the required keys exposed. That does not make the application incapable of leaking the value, but it removes several automatic environment-based exposure paths. You should also check logging configuration and support-bundle redaction.
</details>

<details><summary>3. A platform team enables `aescbc` encryption with `identity` as a fallback. A developer then runs `k get secret db-creds -o yaml` and still sees base64 data. Are they seeing proof that encryption failed?</summary>

No. Encryption at rest protects the stored representation in etcd, while the API server decrypts data for authorized clients and returns the normal Secret format. Seeing base64 through `k get secret` is expected because the API response encodes binary-safe data. To validate encryption, inspect the storage path through documented procedures rather than normal API reads. The team should also rewrite existing Secrets so old unencrypted objects are stored with the new provider.
</details>

<details><summary>4. Your organization uses Vault, but one namespace still allows developers to create native Opaque Secrets manually. What risk does this dual path create, and how would you bring it under control?</summary>

The dual path fragments audit, ownership, and rotation because some values follow Vault policy while others exist only in Kubernetes. Stale credentials become harder to find, and incident responders cannot trust a single source of truth. A practical fix is to allow approved controllers or CSI integrations to create managed Secrets while admission policy blocks unmanaged Opaque Secrets in production namespaces. Exceptions should be documented, time-limited, and visible to the security review process.
</details>

<details><summary>5. A namespace contains many Secrets, and three service accounts need different subsets. Kubernetes RBAC feels too coarse for the desired policy. How should you redesign the boundary?</summary>

Start by splitting consumers and credentials so each workload receives only what it needs. Smaller namespaces and workload-specific service accounts make RBAC easier to review. For named exceptions, `resourceNames` can restrict direct Secret reads, but it can become brittle as names change. If the organization needs durable per-path or per-credential policy, an external secrets manager with provider-native access rules is usually a better source of truth.
</details>

<details><summary>6. A team rotates the value in a Kubernetes Secret but forgets to update the database password itself. Pods restart successfully, yet authentication still fails. What did they misunderstand?</summary>

They confused delivery-object rotation with issuer-side credential rotation. Updating a Kubernetes Secret changes what pods receive, but it does not automatically change the password, token, or certificate in the system that validates it. A correct rotation starts with the issuer or uses a coordinated dual-validity period, then updates consumers, verifies the new value, and revokes the old one. The runbook should name both the Kubernetes object and the external system.
</details>

<details><summary>7. An engineer who lacks `get secrets` permission can create pods in a namespace. They create a pod that mounts an existing Secret and then read the file. What lesson should the RBAC review capture?</summary>

Pod creation can be an indirect path to Secret access because the kubelet delivers referenced Secrets to scheduled pods. RBAC reviews must consider `create pods`, controller creation, `exec`, `attach`, and service account use, not just direct Secret verbs. The fix may include tighter workload creation permissions, separate namespaces, admission controls that restrict Secret references, and service accounts scoped to one application. Direct Secret read rules are only one part of the access model.
</details>

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

Work through the review as if you were the platform engineer approving a production change. Do not stop after spotting the hardcoded password. Follow the value through Git, the Kubernetes API, the pod environment, process arguments, application debug behavior, and image reproducibility. A strong review names the exposure path, explains why it matters during an incident, and proposes a change that the application team can actually implement.

- [ ] Identify every place the deployment can expose a sensitive value before the container even starts.
- [ ] Replace hardcoded values with an approved Secret source and explain who owns the credential.
- [ ] Redesign delivery so the application reads sensitive values from read-only files instead of process arguments.
- [ ] Decide whether this workload should use a native Secret, external sync, CSI direct mount, or dynamic credentials.
- [ ] Define success criteria for rotation, including how to prove the old value is no longer used.

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

The secure version is intentionally minimal, so finish the exercise by describing what is still missing. The manifest should eventually include a real immutable image digest, a Secret creation workflow that avoids raw values in Git, a reload or rollout plan for rotation, and policy preventing debug flags in production. If the organization already has an external store, the better answer may be to replace the native Secret volume with a provider-backed mount or a synced Secret managed by a controller.

Use the exercise as a template for real reviews. Start with the manifest because it is visible, but do not end there. Ask where the password came from, whether the issuing system can rotate it without downtime, which service account can mount it, whether backups protect it, and whether logs or support tooling can reveal it. The same questions apply to TLS keys, registry credentials, SSH keys, webhook tokens, and service account tokens. Secrets management is repetitive by design; repetition is what makes incidents survivable.

## Sources

- [Kubernetes Secrets concept](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Kubernetes good practices for Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [Kubernetes encrypt data at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Kubernetes KMS provider](https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/)
- [Kubernetes RBAC authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes Secret volumes](https://kubernetes.io/docs/concepts/storage/volumes/#secret)
- [Kubernetes Secrets as environment variables](https://kubernetes.io/docs/concepts/configuration/secret/#using-secrets-as-environment-variables)
- [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/)
- [External Secrets Operator](https://external-secrets.io/latest/)
- [HashiCorp Vault Kubernetes auth](https://developer.hashicorp.com/vault/docs/auth/kubernetes)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Azure Key Vault overview](https://learn.microsoft.com/en-us/azure/key-vault/general/overview)
- [Sealed Secrets project](https://github.com/bitnami-labs/sealed-secrets)

## Next Module

[Module 3.4: ServiceAccount Security](../module-3.4-serviceaccounts/) - Securing pod identities and API access.
