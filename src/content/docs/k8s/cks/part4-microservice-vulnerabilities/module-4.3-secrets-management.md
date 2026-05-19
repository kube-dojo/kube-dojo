---
title: "Module 4.3: Secrets Management"
slug: k8s/cks/part4-microservice-vulnerabilities/module-4.3-secrets-management
sidebar:
  order: 3
lab:
  id: cks-4.3-secrets-management
  url: https://killercoda.com/kubedojo/scenario/cks-4.3-secrets-management
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 4.2 (Pod Security Admission), RBAC basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Diagnose** default Kubernetes Secret exposure by tracing where values appear in manifests, Pod specs, environment variables, kubelet-managed volumes, etcd, and audit records.
2. **Implement** `EncryptionConfiguration` for Secrets at rest, including local providers, KMS v2, provider ordering, verification, and key rotation.
3. **Compare** External Secrets Operator, Sealed Secrets, HashiCorp Vault, and the Secrets Store CSI Driver for different operational and GitOps secret-delivery models.
4. **Design** least-privilege controls for Secret access using RBAC, projected ServiceAccount tokens, audit policies, immutable Secrets, and application-level rotation workflows.

## Why This Module Matters

Hypothetical scenario: a payment API goes down during an ordinary rollout because the new Pod cannot authenticate to its database. The Secret object exists, the Deployment references the correct key, and the application image did not change. The root cause is less dramatic and more common: an operator rotated a database password in the cloud secret manager, the Kubernetes Secret stayed stale, the Pod consumed the old value through an environment variable, and the application had no reload path short of a restart. Nothing was exploited, yet the outage came from the same design weakness an attacker would use: the team did not know which component was the source of truth for the credential.

Kubernetes Secrets are useful, but they are not a complete secrets-management system by themselves. A Secret gives you an API object for small sensitive values, a way to mount those values into Pods, and a type system for common payloads such as TLS keys and registry credentials. By default, however, the value is base64-encoded rather than encrypted, stored in the API server's backing store unless you configure encryption at rest, and readable by any subject with enough RBAC or indirect Pod-creation power in the namespace. That combination is easy to misunderstand because the object is called `Secret`, yet the default guarantees are closer to "separate this value from the image and Pod template" than to "cryptographically protect this value against cluster administrators, backups, and broad readers."

The CKS exam expects you to reason about that distinction under time pressure. You may need to inspect a Pod that leaks a password through an environment variable, restrict a Role that grants `list` on every Secret in a namespace, configure `--encryption-provider-config` for the API server, or explain why a projected ServiceAccount token is safer than a long-lived token Secret. Production work adds another layer: cost, rotation, audit volume, and failure modes. A secure design is not the tool with the strongest marketing page; it is the design where the storage boundary, decryption boundary, runtime delivery path, and human access path all match the risk you are trying to reduce.

## Diagnosing Default Secret Exposure

A Kubernetes Secret is an API object whose `data` fields are base64 strings. Base64 is an encoding format that lets arbitrary bytes travel safely through YAML, JSON, and HTTP APIs; it is not encryption because there is no key and no access decision during decoding. If someone can read the object, they can decode the value locally, and the API server will not know that decoding happened. The first diagnostic move is therefore to separate "who can read the Secret object" from "who can decode the bytes after reading it."

```bash
kubectl create namespace secrets-lab
kubectl -n secrets-lab create secret generic app-db \
  --from-literal=username=app_user \
  --from-literal=password=example-password

kubectl -n secrets-lab get secret app-db -o jsonpath='{.data.password}'
printf '\n'
kubectl -n secrets-lab get secret app-db -o jsonpath='{.data.password}' | base64 --decode
printf '\n'
```

That demonstration is intentionally plain because the exam often tests whether you notice the obvious exposure path before reaching for a larger tool. The API response contains encoded bytes, not ciphertext. If the cluster has no encryption provider configured, the API server also persists the object into etcd without envelope encryption. That means etcd snapshots, direct etcd access, and poorly protected control-plane backups can expose sensitive values even when normal `kubectl get secret` access is locked down. RBAC protects API reads; at-rest encryption protects the storage layer; neither replaces the other.

```text
+-------------------+       +--------------------+       +------------------+
| Secret manifest   | ----> | kube-apiserver     | ----> | etcd storage     |
| data: base64 text |       | admission + RBAC   |       | plaintext unless |
| stringData: input |       | optional encryptor |       | configured       |
+-------------------+       +--------------------+       +------------------+
          |                            |
          |                            v
          |                  +--------------------+
          |                  | kubelet on node    |
          |                  | projects as files  |
          |                  | or env variables   |
          |                  +--------------------+
          v
+-------------------+
| kubectl output    |
| logs, Git, chats  |
| copied snippets   |
+-------------------+
```

The runtime path matters just as much as storage. When a container receives a Secret through `env.valueFrom.secretKeyRef`, the value becomes part of the process environment. It can show up in debugging output, crash reports, accidental `printenv` dumps, and child processes. When a container receives a Secret through a volume, the kubelet writes files into a memory-backed volume and can update those files after the Secret changes, although applications still need to reopen or watch the files. A volume is not magic secrecy, but it gives you file permissions, a narrower read path, and a better rotation story than environment variables.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: env-leak-demo
  namespace: secrets-lab
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "sleep 3600"]
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-db
              key: password
```

Pause and predict: if a user cannot run `kubectl get secret app-db`, but can create Pods in `secrets-lab`, what could they do with the Pod above? The important gotcha is that Pod creation can become indirect Secret read access. A subject that can create a Pod in a namespace can usually mount or inject any Secret in that namespace into a container it controls, then read the value from inside the container. That is why Secret RBAC cannot be reviewed in isolation from workload-creation permissions.

Secret types add validation and convention, not universal confidentiality. `Opaque` is the generic type for arbitrary key-value pairs. `kubernetes.io/dockerconfigjson` stores registry pull credentials in the `.dockerconfigjson` key so kubelet image pulls can use them. `kubernetes.io/tls` expects `tls.crt` and `tls.key`, which ingress controllers and workloads commonly understand. `kubernetes.io/service-account-token` is a legacy long-lived ServiceAccount token Secret type that should usually be replaced by projected, bound tokens. Bootstrap token Secrets, using the `bootstrap.kubernetes.io/token` type, support kubelet TLS bootstrapping and should be treated as short-lived cluster-join credentials rather than application secrets.

| Secret type | Typical payload | Main risk to check |
|---|---|---|
| `Opaque` | Application credentials and API keys | Values are arbitrary, so naming and rotation conventions must come from your team. |
| `kubernetes.io/dockerconfigjson` | Registry authentication JSON | A stolen value may grant image-pull access across environments or registries. |
| `kubernetes.io/tls` | `tls.crt` and `tls.key` | The private key is high impact and should not be stored in ConfigMaps or logs. |
| `kubernetes.io/service-account-token` | Long-lived API bearer token | Prefer projected, audience-bound, time-bound tokens for modern workloads. |
| `bootstrap.kubernetes.io/token` | Node bootstrap token data | Expire and scope tightly because it participates in node trust establishment. |

Hypothetical scenario: during an outage, an engineer runs `kubectl describe pod payment-api` in a shared terminal recording and captures environment variable names showing exactly which Secret keys the container consumes. The output does not print the Secret value, but it reveals the credential map, the Secret object names, and enough structure for an attacker with later namespace access to know where to look. The fix is not to ban debugging; it is to consume high-value values as files, avoid dumping environments, restrict Pod creation, and keep audit logging focused on who read or changed Secret objects.

`stringData` is another place where naming can mislead learners. It is a write-friendly input field that lets you submit clear text in a manifest or command output, and the API server stores the resulting value under `data` as base64. That makes `stringData` convenient for ad hoc creation but risky for Git and chat transcripts because the submitted manifest contains the raw value. In reviewed configuration, prefer generator or encryption workflows that keep the clear text out of the repository before the Kubernetes API ever sees it.

The node boundary is also part of the exposure map. The kubelet retrieves Secret data for Pods scheduled to its node and writes projected files for those Pods, so a compromised node can become a credential collection point for the workloads running there. This is one reason Pod Security Admission, node hardening, hostPath restrictions, and runtime isolation still matter in a module about Secrets. A cluster can have perfect API RBAC and encrypted etcd snapshots while a privileged container on a node reads mounted credentials from neighboring workloads through host access.

Registry pull credentials deserve separate review because they often outlive the workload that used them. A `kubernetes.io/dockerconfigjson` Secret may grant access to a whole registry namespace, not just one image, and that access can enable supply-chain movement if an attacker can pull private images or inspect layers. Treat image pull Secrets as deployment credentials with their own rotation calendar, provider-side scoping, and namespace boundaries. If a workload only needs public images, removing the pull Secret is simpler than protecting a credential that should not exist.

On the exam, a fast Secret diagnosis can follow a consistent path: inspect how the Pod consumes the value, inspect who can read or indirectly mount the Secret, inspect whether the API server has encryption configured, and inspect whether logs or audit policy copy sensitive payloads. That sequence keeps you from overfocusing on one layer. A Pod using file mounts can still be unsafe if the Role grants `list secrets`; a cluster with encrypted etcd can still leak through environment dumps; and an external manager can still sync a native Secret that broad readers can decode.

## Implementing EncryptionConfiguration and KMS v2

At-rest encryption is configured on the kube-apiserver because the API server is the component that serializes API objects into etcd. The configuration file tells the API server which resources to encrypt and which providers to try. The first provider in the list is used for new writes, and each listed provider may be used to decrypt older data. This ordering rule is the heart of rotation: add the new key first, keep old keys below it for reads, rewrite the objects, verify, and only then remove retired keys.

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key-2026-05
              secret: REPLACE_WITH_32_BYTE_BASE64_KEY
      - identity: {}
```

The local providers have different tradeoffs. `aescbc` is the common local provider for clusters that cannot integrate with an external KMS yet, and it requires a base64-encoded 32-byte key. `aesgcm` is faster than `aescbc` because GCM authentication and decryption are accelerated on modern x86_64 chips, but it imposes a hard upper bound on writes per key. With a random 96-bit nonce, the birthday-bound for collisions starts to matter at roughly 2^32 (~4 billion) writes per key, after which an attacker observing collisions could derive plaintext. The Kubernetes documentation recommends `secretbox` over `aesgcm` for new clusters because secretbox's XSalsa20-Poly1305 construction uses a 192-bit nonce and dodges this constraint entirely. `secretbox` uses a NaCl secretbox construction and also requires a 32-byte key. `identity` performs no encryption and should normally appear only as a temporary fallback for reading old plaintext values during migration, because placing it first means new writes stay unencrypted.

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps
    providers:
      - aescbc:
          keys:
            - name: key-2026-06
              secret: REPLACE_WITH_NEW_32_BYTE_BASE64_KEY
            - name: key-2026-05
              secret: REPLACE_WITH_OLD_32_BYTE_BASE64_KEY
      - identity: {}
```

Enabling the file is only half of the work. The kube-apiserver must receive `--encryption-provider-config`, and a static Pod control plane must mount the host path containing that file into the API server container. A common exam failure is to create a valid file on the node and forget the `volumeMounts` and `volumes` entries, causing the API server to restart into a path-not-found error. After the API server is healthy, newly written Secrets use the first provider, but existing Secrets remain in their previous storage form until they are rewritten through the API.

### Wiring the config file into kube-apiserver

Edit `/etc/kubernetes/manifests/kube-apiserver.yaml` on the control plane node so the static Pod can see the encryption config file. Kubelet watches this manifest directory and restarts the static Pod after a valid edit, so the API server will pick up the new command/volume wiring automatically. The most common mistake is to create a correct `encryption-config.yaml` but forget to mount it into the kube-apiserver container.

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
# In spec.containers[0].command, add:
- --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml

# In spec.containers[0].volumeMounts, add:
- name: enc-config
  mountPath: /etc/kubernetes/enc
  readOnly: true

# In spec.volumes, add:
- name: enc-config
  hostPath:
    path: /etc/kubernetes/enc
    type: DirectoryOrCreate
```

All three pieces — the flag, mount, and volume — must be present; if one is missing, the API server does not load the config and falls back to identity (plaintext) writes silently.

```bash
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

Verification should prove both configuration and data transformation. The API server flag proves the process knows where the provider file is, but it does not prove older records were rewritten. A storage-level sample should show the encrypted storage prefix for a newly written Secret, while ordinary `kubectl get secret` should still return a usable object because decryption happens transparently on API reads. If a compliance check only asks whether the flag exists, it is checking intent rather than outcome. If it only checks one newly created Secret, it may miss historical plaintext data.

```bash
ETCDCTL_API=3 etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/secrets-lab/app-db | strings | head -5
```

After encryption is enabled, the value should start with `k8s:enc:aescbc:v1:` (or `:aesgcm:v1:` / `:secretbox:v1:` / `:kms:v2:` depending on provider). Before encryption, or when `identity` is used for write paths, plaintext fields are still visible and no such prefix appears. This is the canonical proof step: the verifier is authoritative when you can read the raw etcd value and see the `k8s:enc:...` prefix, because that is the storage format the API server writes when encryption is active.

Key rotation is a provider-ordering exercise, not a one-line replacement. Add the new key above the old key, restart or reload the API server according to your control-plane model, rewrite the protected resources, verify that new storage records reference the new key, and only then remove the old key from the provider list. Removing an old key too early can make older stored objects unreadable. Leaving retired keys forever weakens the purpose of rotation because a leaked old key remains useful for any object that was never rewritten.

Managed Kubernetes changes who performs the mechanical step, not the concept you need to understand. Some managed services expose a checkbox or API for secret envelope encryption, while self-managed clusters require direct kube-apiserver configuration. For CKS, you should still understand the file format because the exam environment commonly resembles a kubeadm-style control plane. In production, ask whether the managed service encrypts only Secrets or all API resources, whether customer-managed keys are supported, and what operational event re-encrypts historical objects after a key change.

KMS v2 is the production-grade version of this pattern when you want the root encryption key outside the cluster. In envelope encryption, Kubernetes encrypts each stored object with a data encryption key, then asks an external KMS plugin to encrypt or decrypt that data key with a key encryption key managed by AWS KMS, Google Cloud KMS, Azure Key Vault, Vault, or another provider. The API server talks to the plugin over a local Unix domain socket using the KMS provider protocol. The plugin boundary lets the cluster use a managed HSM-backed key without teaching the API server every cloud-specific authentication method.

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - kms:
          name: cloud-kms-v2
          apiVersion: v2
          endpoint: unix:///var/run/kmsplugin/socket.sock
          timeout: 3s
      - aescbc:
          keys:
            - name: emergency-local-key
              secret: REPLACE_WITH_32_BYTE_BASE64_KEY
      - identity: {}
```

KMS v2 became stable in Kubernetes 1.29 and is preferred over the older KMS v1 provider. The v2 protocol improves health reporting, observability, key version handling, and performance characteristics so the API server can tell whether the plugin is ready and which key version protected a value. That does not remove operational responsibility. If the plugin is slow, unavailable, or misconfigured during writes and decrypts, the API server path that handles encrypted resources can become slow or fail. Treat the KMS plugin as a control-plane dependency, monitor its latency and error rate, and test what happens when the external KMS throttles or rotates keys.

The KMS plugin identity is part of the trust boundary. On a cloud platform, the plugin or control-plane integration needs permission to use a specific key, and that permission should be narrower than general secret-manager administration. On self-managed clusters, the socket file path and plugin process need filesystem protection because the API server depends on that local endpoint for encryption operations. A compromised plugin host or overpowered cloud identity can undermine the benefit of moving the root key out of etcd.

Key versioning is the practical reason KMS v2 discussions mention observability so often. A provider can rotate the external key encryption key while Kubernetes continues to read older objects, but operators need to know which key version is active, which objects have been rewritten, and whether decrypt failures are increasing. Without that signal, rotation becomes a leap of faith. A healthy runbook records the external key version before rotation, rewrites a small namespace first, checks API server and plugin metrics, and only then runs the broader migration.

Disaster recovery deserves a dry run before a real incident. An encrypted etcd snapshot is not useful if the restore cluster cannot reach the same KMS, cannot authenticate as the plugin identity, or has lost the local provider keys. For local `aescbc`, back up the encryption config separately from etcd with strong access control, because the config contains the key needed to decrypt the data. For KMS v2, document how to restore the plugin, socket path, cloud identity, and key permissions before declaring the backup strategy complete.

Cloud KMS integration changes the cost model as well as the threat model. Managed KMS and secret-manager services usually bill for stored keys or secrets, API calls, and sometimes cross-region or log-ingestion side effects. KMS v2 reduces unnecessary external calls compared with less efficient designs, but short cache lifetimes, frequent rewrites, many clusters, and aggressive audit policies can still create visible monthly cost. External Secrets Operator adds another billable pattern because every refresh interval can call a cloud secret API, while audit logging Secret reads at high volume can shift the cost into your logging backend. Cost control comes from longer refresh intervals where safe, narrow resource selection, local plugin health, and clear ownership of which clusters actually need each external secret.

Before running this in a real cluster, what output do you expect from `kubectl get --raw /readyz?verbose` immediately after a control-plane manifest change? The expected answer is not "it always succeeds." Static Pod restarts create a short window where the API server is unavailable, and a bad encryption config can extend that window until the manifest is fixed. On the exam, make one controlled change, preserve a backup of the manifest, and verify API health before rewriting every Secret.

## Comparing External Secret Delivery Models

External Secrets Operator, usually shortened to ESO, solves a source-of-truth problem rather than an at-rest encryption problem. The operator watches `ExternalSecret` resources, reads values from external providers such as Vault, AWS Secrets Manager, AWS Systems Manager Parameter Store, Google Secret Manager, Azure Key Vault, 1Password, and other supported backends, then writes ordinary Kubernetes Secret objects for workloads to consume. That compatibility is the main benefit: existing Helm charts and applications can keep referencing native Secrets while the sensitive value is authored and rotated outside the cluster.

```yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: team-vault
  namespace: payments
spec:
  provider:
    vault:
      server: https://vault.example.com
      path: kv
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes
          role: payments-reader
          serviceAccountRef:
            name: eso-payments
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: payment-db
  namespace: payments
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: team-vault
    kind: SecretStore
  target:
    name: payment-db
    creationPolicy: Owner
  data:
      - secretKey: password
        remoteRef:
          key: payments/database
          property: password
```

Note: ExternalSecret moved from `external-secrets.io/v1beta1` to `external-secrets.io/v1` in ESO 0.10. Clusters running ESO 0.9.x still use `v1beta1` — replace the `apiVersion` field accordingly.

The `SecretStore` versus `ClusterSecretStore` decision is a governance decision. A `SecretStore` lives in one namespace and is usually owned by the team that owns the workloads there. A `ClusterSecretStore` is cluster-scoped and useful when a platform team wants one provider configuration shared by many namespaces. The cluster-scoped option is powerful, so pair it with admission policy, namespace allowlists, and provider-side authorization. Otherwise, a namespace owner may gain a clean Kubernetes API path to remote secrets they should never reach.

Provider identity is where ESO designs often succeed or fail. In AWS, the operator might use IAM Roles for Service Accounts; in Google Cloud, it might use Workload Identity; in Azure, it might use a managed identity path; and with Vault, it often authenticates through the Kubernetes auth method. Those provider identities should be scoped to the exact secret paths or names the operator must read. If the ESO controller has wildcard read access to a whole provider account, Kubernetes namespace boundaries become less meaningful because one compromised ExternalSecret definition can request far more than the workload owns.

Refresh intervals are not just freshness settings. A very short interval reduces the time between provider rotation and Kubernetes synchronization, but it also increases provider API calls, controller work, audit events, and the chance that a provider outage becomes visible as constant reconcile noise. A long interval lowers cost and noise but can leave a rotated credential stale until the next sync. For high-impact credentials, pair the interval with an explicit rotation event or manual reconcile process so rotation is deliberate instead of waiting for a polling loop to notice.

ESO still creates Kubernetes Secret objects, so it does not eliminate the need for etcd encryption, RBAC, runtime controls, or audit policies. Its value is that rotation and authoring happen in a managed external system, not in Git or ad hoc `kubectl create secret` commands. The tradeoff is controller dependency: if ESO loses provider access, the last synchronized Kubernetes Secret may remain usable while new values stop arriving. That can be exactly what you want for availability, but it can also hide failed rotations until a password expires. Monitor `ExternalSecret` conditions and provider errors as production signals, not as optional operator noise.

ESO templating is useful when the provider stores atomic values but the application needs a specific file or Secret type. For example, a provider may store a certificate, a private key, and a CA bundle as separate properties while the workload expects a `kubernetes.io/tls` Secret or a single configuration file. Templating should be kept small and reviewable because it becomes a translation layer between provider data and runtime behavior. Complex transformations are better handled in the application or a dedicated provisioning pipeline than hidden inside Secret synchronization.

Sealed Secrets is a different GitOps-centered pattern. The `kubeseal` client encrypts a Secret using the controller's public key, producing a `SealedSecret` custom resource safe to commit to Git for the target cluster and scope. The controller inside the cluster holds the private key and decrypts the resource into a native Secret. This fits teams that want pull-based GitOps and do not have, or do not want, a runtime dependency on a cloud secret manager for every application. It does not fit secrets that need dynamic issuance, short leases, or centralized provider audit trails across many clusters.

Sealed Secrets scope is a security feature that should be understood before moving encrypted YAML between environments. A sealed value can be bound to a name and namespace, which prevents someone from taking a ciphertext meant for one Secret and replaying it under a more privileged name elsewhere. That protection is useful, but it also means renaming or moving a Secret may require resealing. Back up the controller private key carefully, because losing it can make committed SealedSecret resources undecryptable during cluster recovery.

Sealed Secrets keys rotate automatically every 30 days when the controller flag `--key-renew-period=720h` (the default) is set, but older keys are kept indefinitely so existing SealedSecret resources continue to decrypt. To force a manual rotation, create a new key Secret in `kube-system` with the `sealedsecrets.bitnami.com/sealed-secrets-key: active` label and the controller will use it for new seals on its next reconcile; the existing SealedSecret resources do not need to be re-sealed because each carries the encryption-key fingerprint in its annotations. The controller decrypts using whichever key the fingerprint points at, even after rotation.

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: app-db
  namespace: production
spec:
  encryptedData:
    password: AgBy3i4OJSWK+...g8VPo3vP
  template:
    metadata:
      name: app-db
      namespace: production
    type: Opaque
```

`encryptedData` values are sealed against the controller's public key (via `kubeseal`); the controller in `kube-system` decrypts them at apply time and creates the matching plain Secret.

```text
+------------------+      public key       +-------------------+
| developer laptop | --------------------> | SealedSecret YAML |
| kubeseal client  |                       | committed to Git  |
+------------------+                       +-------------------+
                                                    |
                                                    v
                                          +--------------------+
                                          | cluster controller |
                                          | private key holder |
                                          +--------------------+
                                                    |
                                                    v
                                          +--------------------+
                                          | native Secret      |
                                          | consumed by Pods   |
                                          +--------------------+
```

HashiCorp Vault on Kubernetes gives you a richer runtime security model when you need dynamic secrets, leasing, renewal, and revocation. The Vault Agent injector mutating webhook can add an agent sidecar or init container that authenticates with Vault using the workload's Kubernetes identity, renders secrets into a shared volume, and renews leases where the secret type supports renewal. The Vault CSI provider and Secrets Store CSI Driver can mount values as volumes without first creating native Kubernetes Secrets, depending on configuration. These patterns reduce static credential lifetime, but they require the application or sidecar to handle file reads, renewal timing, and failure behavior when Vault is unavailable.

Dynamic database credentials are the clearest reason to accept Vault's complexity. Instead of storing one shared database password for months, Vault can create a database user with a lease for the workload, renew it while the workload is healthy, and revoke it when the lease ends. That model shrinks the value of a stolen credential, but it also changes incident response. You need to know how to revoke leases, how to drain old connections, and how the application behaves if renewal fails while traffic is still flowing.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: vault-agent-demo
  namespace: payments
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "payments-reader"
    vault.hashicorp.com/agent-inject-secret-db.txt: "database/creds/payments"
spec:
  serviceAccountName: payments-api
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "while true; do cat /vault/secrets/db.txt >/dev/null; sleep 30; done"]
```

Hypothetical scenario: a critical service starts without its expected Vault-rendered file because an injection annotation was copied to the Deployment template but the ServiceAccount was not bound to the Vault role. The container image is healthy, Kubernetes scheduling is healthy, and the application error looks like an ordinary missing-file problem. The security lesson is that injector-based delivery creates an admission-time dependency and a runtime file contract. Your readiness probe should fail if the rendered file is absent, and your deployment pipeline should validate both annotations and ServiceAccount-to-Vault-role bindings before traffic moves.

```bash
# One-time setup inside the Vault pod (after vault is unsealed):
kubectl exec -n vault vault-0 -- /bin/sh -c '
  vault auth enable kubernetes
  vault write auth/kubernetes/config \
    kubernetes_host="https://kubernetes.default.svc.cluster.local:443" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
    issuer="https://kubernetes.default.svc.cluster.local"
'
```

In this setup, `token_reviewer_jwt` is the ServiceAccount JWT Vault uses when calling Kubernetes TokenReview to validate client Pod service account tokens. The `issuer` must match the cluster's JWT issuer configured on the API server via `--service-account-issuer`, otherwise token validation requests are rejected.

The Secrets Store CSI Driver occupies the middle ground between native Kubernetes Secret consumption and direct application calls to an external provider. The kubelet mounts provider data into a Pod as a CSI volume, and optional sync features can also create a Kubernetes Secret when a workload or chart requires one. This is attractive when you want rotation to appear as file updates and when you want the external provider to remain the real store. The driver runs node components, provider plugins, and SecretProviderClass configuration, so operational ownership must include node coverage, provider credentials, and application reload behavior.

Direct application calls to a cloud secret API are sometimes the right answer, but they move the Kubernetes control plane out of the delivery path and put more responsibility into application code. That can be excellent for a platform with strong workload identity and libraries that cache, refresh, and report errors consistently. It can be poor for heterogeneous teams where every service invents a different secret client. Kubernetes-native delivery is less pure from a zero-copy perspective, but it centralizes patterns that reviewers, operators, and exam graders can inspect.

| Model | Best fit | Main tradeoff |
|---|---|---|
| Native Secret plus encryption | Small clusters, exam tasks, simple apps | Kubernetes remains the storage and RBAC boundary. |
| External Secrets Operator | Apps expect native Secrets, provider is external | Synced Secret still exists in etcd and must be protected. |
| Sealed Secrets | GitOps with encrypted manifests per cluster | Static payloads, controller private-key backup, resealing workflow. |
| Vault injector or agent | Dynamic credentials, lease renewal, templating | Runtime dependency, app reload needs, Vault operational cost. |
| Secrets Store CSI Driver | File-based mounts from external providers | Node plugin dependency and volume rotation semantics. |

## Designing RBAC, ServiceAccount Tokens, Audit Logging, and Rotation

Secret RBAC should be read as a blast-radius document. `get` on a named Secret is a narrow read. `list` on Secrets is a bulk exfiltration permission because the response can include every object in the namespace. `watch` is continuous exfiltration because it streams future changes. `create` Pods can become indirect read access, as discussed earlier. `update` or `patch` on Secrets can be as dangerous as read access because a malicious subject can replace credentials, inject trusted certificates, or change registry pull credentials to point workloads at attacker-controlled images.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: payment-api-secret-reader
  namespace: payments
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["payment-db"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: payment-api-secret-reader
  namespace: payments
subjects:
  - kind: ServiceAccount
    name: payment-api
    namespace: payments
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: payment-api-secret-reader
```

That Role is intentionally narrow, but it is not the whole policy. If the same ServiceAccount can create arbitrary Pods, exec into sibling Pods, or read every Secret through another binding, the narrow Role does not help much. `resourceNames` is useful for `get`, `update`, and `patch`, but broad `list` and `watch` permissions need separate scrutiny because they are often granted to controllers for convenience. A controller that truly needs to watch Secrets should run in a narrow namespace, use a dedicated ServiceAccount, and have an operational reason documented in the Role name or owner annotation.

Admission control is the companion to RBAC when the risk is indirect access. A Role can say who may create Pods, while an admission policy can say which Secrets those Pods may mount, whether `env.valueFrom.secretKeyRef` is allowed for high-value namespaces, and whether default ServiceAccount token automounting is permitted. This is especially useful in multi-tenant clusters where namespace administrators legitimately create workloads but should not be able to turn every Secret into a readable file. CKS focuses on built-in controls, yet the production lesson is to block dangerous Secret consumption paths before they become workload specs.

ServiceAccount tokens deserve special attention because Kubernetes historically represented them as long-lived Secret objects. Modern clusters use projected ServiceAccount tokens through the TokenRequest API. These tokens are time-bound, audience-bound, and mounted as projected volumes, which means a token intended for the Kubernetes API is not automatically valid for every external service and does not need to live forever as a Secret. Set `automountServiceAccountToken: false` for Pods that do not call the API, and request explicit projected tokens with a narrow audience when the workload needs an identity token for a specific recipient.

Audience choice is a security decision, not a label. A token minted for `https://kubernetes.default.svc` is meant for the Kubernetes API, while a token minted for Vault or an internal identity broker should be accepted only by that recipient. If a service accepts any Kubernetes-issued token without checking audience and expiry, it recreates the old bearer-token problem with newer mechanics. In reviews, ask which component validates the token, what audience it expects, and whether token lifetime is shorter than the likely detection and response window for a compromised Pod.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-token-demo
  namespace: payments
spec:
  serviceAccountName: payment-api
  automountServiceAccountToken: false
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "sleep 3600"]
      volumeMounts:
        - name: api-token
          mountPath: /var/run/secrets/tokens
          readOnly: true
  volumes:
    - name: api-token
      projected:
        sources:
          - serviceAccountToken:
              path: api-token
              audience: https://kubernetes.default.svc
              expirationSeconds: 3600
```

Audit logging is how you answer the question "who read the Secret?" after the fact, but it must be configured carefully because audit logs can become another place where sensitive data leaks. For Secret reads, use `Metadata` level in most cases, because `RequestResponse` can record response bodies for API requests and that is the last thing you want for a Secret. The policy below logs read-style verbs against Secret resources without capturing the Secret payload. In a static Pod control plane, the audit policy and log path must be mounted into the kube-apiserver container just like the encryption configuration file.

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - RequestReceived
rules:
  - level: Metadata
    verbs: ["get", "list", "watch"]
    resources:
      - group: ""
        resources: ["secrets"]
  - level: Metadata
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - group: ""
        resources: ["secrets"]
  - level: None
    nonResourceURLs:
      - /healthz*
      - /readyz*
      - /livez*
```

Audit analysis should distinguish normal controllers from surprising humans or workloads. ESO, cert-manager, ingress controllers, and image automation may legitimately read or update certain Secrets, but those accesses should come from predictable ServiceAccounts in predictable namespaces. A human user running `get secrets` in production, a CI account listing every Secret, or a workload ServiceAccount watching Secrets outside its namespace is a different signal. Build allowlists from expected controller identities and investigate the outliers rather than treating every Secret audit event as equally urgent.

Rotation is the design area where many technically correct secrets systems fail in production. A Kubernetes Secret mounted as a volume can update in the container filesystem after the object changes, but an environment variable does not update until the container restarts. A Secret mounted with `subPath` also does not receive live updates through the usual projected volume mechanism. Immutable Secrets, stable since Kubernetes 1.21, improve safety and kubelet performance for values that should not change in place, but they force a create-new-name-and-rollout pattern for rotation. That is a feature when you want deliberate rollouts and a problem when you expected silent replacement.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: payment-db-2026-05
  namespace: payments
type: Opaque
immutable: true
stringData:
  username: app_user
  password: example-password
```

Application behavior completes the rotation story. If the credential is a database password, the application may need a connection-pool drain, a file watcher, a `SIGHUP`, an HTTP reload endpoint, or a Deployment restart. If the credential is a TLS certificate, the server process may need to reload its listener and clients may need trust-bundle propagation. If the credential is dynamic Vault material with a lease, the application must be able to replace it before expiry or tolerate the sidecar doing that on disk. A good Secret design names the storage system, the delivery mechanism, the reload trigger, the rollback path, and the audit signal.

A practical rotation runbook has two clocks. The first clock is the secret store clock: when the provider value changes, when the old value stops working, and when rollback becomes impossible. The second clock is the workload clock: when Pods receive the new value, when processes reopen or reload it, and when health checks prove the new credential is actually in use. Align those clocks before the change window. If the provider invalidates the old password before Pods reload the new one, the outage is self-inflicted even though every individual tool behaved as documented.

## CKS Exam Pattern Walkthroughs

When the exam asks you to identify an exposed Secret in a Pod spec, start with consumption mode and permissions rather than tool names. Look for `env.valueFrom.secretKeyRef`, broad `envFrom` imports, `subPath` Secret mounts that will not update, and default ServiceAccount tokens on Pods that do not need API access. Then check the namespace Roles for `list` and `watch` on Secrets, and remember that Pod creation can be an indirect read path. The answer is often a small YAML edit plus a short explanation of blast radius.

When the exam asks for `EncryptionConfiguration`, write the smallest valid configuration first and expand only if the task requires more resources. The common passing shape is `apiVersion: apiserver.config.k8s.io/v1`, `kind: EncryptionConfiguration`, `resources: ["secrets"]`, an encrypting provider such as `aescbc`, and `identity` last. The API server flag and static Pod volume mount are part of the answer because a file on the host is invisible to the container until mounted. After the API server recovers, create a new Secret and rewrite an old one to prove the migration path.

When the exam asks you to restrict Secret access with RBAC, avoid namespace-wide read permissions unless the question explicitly describes a controller that needs them. A named `get` rule with `resourceNames` is usually the right primitive for one workload reading one Secret. Validate with `kubectl auth can-i` using the full ServiceAccount subject string, then test the negative case for `list secrets`. If the same account can create arbitrary Pods, mention that workload creation must also be constrained, because otherwise the named read rule is not the only path to the value.

When the exam gives you audit logs, focus on verb, user, namespace, resource, and response status. A successful `get` or `list` against Secrets by an unexpected user is more important than a denied request from a scanner. A repeated watch from an unknown ServiceAccount may indicate a controller compromise or a copied ClusterRoleBinding. Do not recommend `RequestResponse` logging for Secret reads as a reflex, because it can copy the protected value into the log backend. Metadata-level audit records are usually the safer evidence source.

When the exam scenario includes external secret tooling, name the remaining native Kubernetes risk. ESO synchronizes a provider value into a Kubernetes Secret, so etcd encryption and RBAC still apply. Sealed Secrets protects Git storage but produces a native Secret after decryption. Vault injection and CSI mounts may avoid a synced native Secret, but they add runtime dependencies and application reload requirements. This comparison is how you avoid the common wrong answer that installing a tool automatically solves every layer of secrets management.

A final exam habit is to write down the credential lifecycle in one sentence before changing YAML. For example: "The password originates in Vault, ESO syncs it to a native Secret hourly, the Pod mounts it as a file, the app reloads on rollout, and audit logs record Secret reads at metadata level." That sentence exposes missing links quickly. If you cannot name the source, delivery mechanism, runtime consumer, reload trigger, and audit point, you do not yet have a complete answer. In production, the same sentence becomes the basis for a runbook and a reviewer checklist.

## Patterns & Anti-Patterns

| Pattern | When to Use | Why It Works |
|---|---|---|
| Encrypt native Secrets at rest and restrict read verbs | Any cluster that stores Kubernetes Secrets | It separates API authorization from storage compromise and backup exposure. |
| Use ESO for provider-owned secrets consumed by ordinary charts | Teams already use AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, Vault, or 1Password | It preserves native Secret compatibility while moving authoring, rotation, and provider audit outside the cluster. |
| Use projected ServiceAccount tokens with explicit audiences | Pods that need API or identity tokens | Short-lived, audience-bound tokens reduce the value of token theft compared with legacy token Secrets. |
| Use immutable versioned Secrets for deliberate rollouts | Credentials that rotate through controlled deployment waves | A new Secret name makes rollout state visible and avoids accidental in-place mutation. |

| Anti-pattern | Why Teams Fall Into It | Better Alternative |
|---|---|---|
| Granting `list` and `watch` on Secrets to human troubleshooting groups | It feels like a convenient read-only permission | Grant named `get` only where possible and create break-glass access with audit review. |
| Storing base64 Secret manifests directly in Git | The encoded value looks less obvious than plaintext | Use Sealed Secrets, SOPS, ESO, or provider references rather than raw Secret values. |
| Assuming ESO removes the need for etcd encryption | The source of truth moved out of Kubernetes | ESO still writes native Secret objects unless you choose a mount-only design. |
| Rotating a Secret without restarting or reloading the application | The object update succeeded, so the rollout is assumed complete | Test the application reload path and include success probes that prove the new credential is in use. |

## Decision Framework

Choose native Kubernetes Secrets with at-rest encryption when the cluster is the right operational boundary, the values are simple, and your risk model is mostly about namespace isolation, backup protection, and exam-style hardening. Choose ESO when another system is already the source of truth and workloads still need native Secret objects. Choose Sealed Secrets when Git must carry encrypted declarative manifests and the secrets are static enough that resealing is acceptable. Choose Vault or CSI-based runtime delivery when short-lived credentials, leases, revocation, or avoiding synced native Secrets are worth the extra control-plane and application complexity.

```text
Start
  |
  v
Do applications already require native Kubernetes Secret objects?
  |-- yes --> Is the source of truth outside the cluster?
  |             |-- yes --> Use ESO, then protect synced Secrets.
  |             |-- no  --> Use native Secrets with encryption and RBAC.
  |
  |-- no  --> Do you need dynamic leased credentials?
                |-- yes --> Use Vault Agent, Vault CSI, or provider CSI.
                |-- no  --> Is Git the delivery system?
                              |-- yes --> Use Sealed Secrets or SOPS.
                              |-- no  --> Use CSI mount or direct provider SDK.
```

The cost decision follows the same path. Native Secrets add little direct cloud cost but increase the importance of etcd backup protection and audit storage. ESO and CSI designs add provider API calls, controller or node components, and logs. Vault adds storage, unseal, HA, backup, and operational staffing cost in exchange for dynamic secrets and stronger central control. A design that is too expensive or fragile will be bypassed, so the secure answer is the one your team can operate during rotation, outage, and incident response.

## Did You Know?

- **KMS v2 became stable in Kubernetes 1.29.** KMS v1 is marked deprecated as of Kubernetes 1.28 but remains functional and configurable through 1.30+. KMS v2 (GA in 1.29) is strongly preferred for new deployments because the v1 plugin protocol's gRPC-streaming design has known performance and partition-failure issues that v2's request/response model resolves.
- **Immutable Secrets became stable in Kubernetes 1.21.** They are not just a security guardrail; they also reduce kubelet watch load for clusters with many mounted Secret and ConfigMap objects.
- **A ServiceAccount token can be requested for a specific audience and expiration.** That is the modern alternative to treating a long-lived token Secret as a reusable password for every internal service.
- **A Secret read logged at `RequestResponse` level can expose the payload in the audit backend.** For most Secret access monitoring, `Metadata` level gives the actor, verb, resource, namespace, and timestamp without copying the sensitive value.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Treating base64 as encryption | The YAML looks transformed, so reviewers assume a cryptographic boundary exists. | Decode one value during review, explain the difference, and enable at-rest encryption for persisted objects. |
| Putting `identity` first in `EncryptionConfiguration` | Operators add it as a fallback but miss provider ordering semantics. | Put the encrypting provider first and keep `identity` last only while old plaintext data must be readable. |
| Granting `list` on Secrets for troubleshooting | Read-only roles are copied from broad templates. | Grant named `get` with `resourceNames`, use temporary break-glass bindings, and audit every access. |
| Using environment variables for rotating credentials | Framework examples often show simple `env` injection. | Prefer file mounts for sensitive values and implement reload or rollout logic for rotations. |
| Assuming ESO means Kubernetes stores no secret data | The external provider is visible in the architecture diagram. | Remember ESO materializes native Secret objects unless a mount-only pattern is chosen. |
| Leaving default ServiceAccount tokens mounted everywhere | The default is convenient and many Pods never call the API. | Set `automountServiceAccountToken: false` by default and add projected tokens only where needed. |
| Enabling audit logs at payload level for Secret reads | Teams want maximum forensic detail during an incident. | Log Secret reads at `Metadata` level and protect audit log retention, access, and export pipelines. |

## Quiz

1. **Your verifier finds that a Secret named `api-token` is stored as `YXBpLXRva2Vu` in a manifest committed to Git. The developer says no one can read it because it is encoded. What do you do first, and what design change prevents the repeat?**

   <details>
   <summary>Answer</summary>
   Treat it as a credential exposure because base64 is reversible without a key. The immediate action is to rotate the underlying credential, remove the raw value from future commits, and assume any clone or fork may retain the old value. The design change depends on workflow: use Sealed Secrets or SOPS for Git-encrypted manifests, or use ESO so Git contains a reference to the external provider path rather than the payload. This maps to the diagnostic outcome because the issue is not Kubernetes decoding; it is human and repository access to the encoded value.
   </details>

2. **You enabled an `aescbc` encryption provider and created a new Secret. A direct etcd inspection shows the new Secret is encrypted, but an older Secret still appears readable. Is encryption broken?**

   <details>
   <summary>Answer</summary>
   Encryption is probably not broken; enabling an encryption provider affects new writes and updates, not historical etcd records. Existing Secrets must be rewritten through the API server, commonly with `kubectl get secrets --all-namespaces -o json | kubectl replace -f -`, so the first configured provider can transform them. Keep older providers or `identity` available until the rewrite and verification are complete. This is a key exam pattern because provider configuration and data migration are separate steps.
   </details>

3. **A platform team wants to use AWS KMS, Google Cloud KMS, or Azure Key Vault as the root key boundary for Kubernetes Secret encryption. Which Kubernetes provider path should they evaluate, and what operational dependency does it introduce?**

   <details>
   <summary>Answer</summary>
   They should evaluate the KMS v2 provider, which lets the API server call a local plugin that integrates with the external KMS. The operational dependency is that encrypted-resource reads and writes now depend on a healthy plugin, valid cloud identity, reasonable latency, and external KMS availability. KMS v2 improves health, key version, and observability behavior compared with older provider paths, but it still belongs in control-plane monitoring and disaster recovery tests. A provider outage can become an API-server symptom, not just a secret-manager symptom.
   </details>

4. **An application team asks whether ESO or Sealed Secrets is the better fit for its GitOps repository. Their credentials already live in Azure Key Vault, rotate monthly, and must be available to an off-the-shelf Helm chart that reads native Kubernetes Secrets. Which option do you choose and why?**

   <details>
   <summary>Answer</summary>
   ESO is the better fit because the source of truth already lives in an external provider and the Helm chart expects native Kubernetes Secret objects. ESO can synchronize the provider value into the cluster while preserving the chart interface, and the refresh interval can be aligned with the rotation process. Sealed Secrets would move encrypted static payloads into Git, which duplicates the provider source of truth and adds resealing work after each rotation. The synced Secret still needs RBAC and at-rest encryption because ESO does not remove native Secret storage.
   </details>

5. **A namespace Role grants a CI ServiceAccount `create` on Pods but no Secret verbs. The security reviewer still says the account may be able to read application Secrets. What is the reviewer noticing?**

   <details>
   <summary>Answer</summary>
   The reviewer is noticing indirect Secret access through Pod creation. If the ServiceAccount can create a Pod in the namespace, it may create a container that mounts or injects a Secret, then read the value from inside that container. Removing `get secrets` is not sufficient when workload creation remains broad. The fix is to scope Pod creation, use admission policy, separate CI namespaces from runtime namespaces, and review Secret access together with workload permissions.
   </details>

6. **Your audit backend is growing quickly after you add Secret monitoring, and a sample event includes response data for a Secret read. What should change in the audit policy?**

   <details>
   <summary>Answer</summary>
   Secret read rules should usually log at `Metadata` level, not `RequestResponse`, because the response body can contain the sensitive payload. Metadata still records who made the request, which verb was used, which namespace and resource were touched, and when it happened. You should also restrict the rule to Secret verbs and resources instead of raising the audit level globally. That reduces both leakage risk and log-ingestion cost while preserving the forensic signal needed for access review.
   </details>

7. **A database password rotates in Vault, the CSI-mounted file updates in the Pod, but the application keeps failing authentication with the old password. Which layer is most likely missing?**

   <details>
   <summary>Answer</summary>
   The missing layer is application reload behavior. Updating a mounted file does not guarantee the process rereads the file or recreates database connections. The fix might be a file watcher, a `SIGHUP`, an HTTP reload endpoint, a connection-pool drain, or a controlled rollout triggered after rotation. Secret delivery and application consumption are separate responsibilities, and a complete rotation plan includes both.
   </details>

## Hands-On Exercise

This exercise is designed for a disposable lab cluster where you control the API server configuration. You will diagnose default exposure, write a safe `EncryptionConfiguration`, tighten one Secret read path, and reason through rotation. If your lab provider does not expose the control-plane filesystem, complete the static Pod manifest edits as review tasks rather than applying them to a managed control plane.

### Task 1: Prove base64 is not encryption

Create a namespace and Secret, then decode the stored value from the API response. The goal is to make the default boundary visible before adding tools.

```bash
kubectl create namespace secrets-lab
kubectl -n secrets-lab create secret generic app-db \
  --from-literal=username=app_user \
  --from-literal=password=example-password

kubectl -n secrets-lab get secret app-db -o jsonpath='{.data.password}' | base64 --decode
printf '\n'
```

<details>
<summary>Solution notes</summary>

The decoded output should match the literal value you provided. That proves the API object is merely encoded for transport and storage representation. If you can read the Secret object, you can decode its values outside Kubernetes without another permission check. This is the reason RBAC, at-rest encryption, and runtime delivery choices must all be reviewed.
</details>

### Task 2: Draft an encryption provider configuration

Generate a key in the lab and create a configuration file that encrypts only Secrets. Keep `identity` last so old plaintext records can still be read during migration.

If your lab exposes the control-plane filesystem, also wire the manifest edit from “Wiring the config file into kube-apiserver” into `/etc/kubernetes/manifests/kube-apiserver.yaml`, then wait for kubelet to restart the static API server Pod.

```bash
mkdir -p /tmp/cks-4-3
head -c 32 /dev/urandom | base64 > /tmp/cks-4-3/aescbc.key
ENC_KEY="$(cat /tmp/cks-4-3/aescbc.key)"

cat > /tmp/cks-4-3/encryption-config.yaml <<EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key-2026-05
              secret: ${ENC_KEY}
      - identity: {}
EOF

sudo mkdir -p /etc/kubernetes/enc
sudo cp /tmp/cks-4-3/encryption-config.yaml /etc/kubernetes/enc/encryption-config.yaml

# Edit /etc/kubernetes/manifests/kube-apiserver.yaml to mount and pass the new config:
# --encryption-provider-config, matching volumeMount, and volume entries.
# Then verify the static Pod has restarted.

kubectl get secrets --all-namespaces -o json | kubectl replace -f -

ETCDCTL_API=3 etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/secrets-lab/app-db | strings | head -5
```

<details>
<summary>Solution notes</summary>

The important checks are API version, resource name, provider ordering, and key length. New writes use the first provider, so `aescbc` must appear before `identity`. The `identity` fallback is acceptable during migration because it lets the API server read older unencrypted records, but it should not be the first provider. In a real static Pod control plane, this file must be mounted into the API server container and referenced with `--encryption-provider-config`.
</details>

### Task 3: Write a narrow Secret reader Role

Create a ServiceAccount that can read only the `app-db` Secret by name. Do not grant `list` or `watch`.

```bash
kubectl -n secrets-lab create serviceaccount app-reader

cat <<'EOF' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-db-reader
  namespace: secrets-lab
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["app-db"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-db-reader
  namespace: secrets-lab
subjects:
  - kind: ServiceAccount
    name: app-reader
    namespace: secrets-lab
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: app-db-reader
EOF

kubectl auth can-i get secret/app-db \
  --as=system:serviceaccount:secrets-lab:app-reader \
  -n secrets-lab

kubectl auth can-i list secrets \
  --as=system:serviceaccount:secrets-lab:app-reader \
  -n secrets-lab
```

<details>
<summary>Solution notes</summary>

The first authorization check should return `yes`, and the second should return `no`. That is the difference between a named read and a namespace-wide inventory. In a real review, you would also check whether the same ServiceAccount can create Pods, exec into Pods, or obtain Secret access through a different RoleBinding. RBAC is cumulative, so one narrow Role does not cancel a broader one.
</details>

### Task 4: Compare env and volume consumption

Run a Pod that mounts the Secret as a file, then read the mounted value. This task uses `busybox`, which includes `sh` and `cat`, so the exec command matches the image binary set.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secret-reader
  namespace: secrets-lab
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "sleep 3600"]
      volumeMounts:
        - name: db
          mountPath: /etc/db
          readOnly: true
  volumes:
    - name: db
      secret:
        secretName: app-db
        defaultMode: 0400
EOF

kubectl -n secrets-lab wait --for=condition=Ready pod/secret-reader --timeout=60s
kubectl -n secrets-lab exec secret-reader -- cat /etc/db/password
```

<details>
<summary>Solution notes</summary>

The mounted file should contain the decoded password value. A file mount gives you file permissions and a better rotation path than an environment variable, but the running process can still read the value. If you patch the Secret, the projected volume may update, but the application must reopen the file or reload its configuration. A process that cached the value at startup can continue using the old credential.
</details>

### Task 5: Review an audit policy for Secret reads

Create a policy snippet that records Secret reads at metadata level. You do not need to apply it unless your lab exposes the control-plane static Pod manifest.

```bash
cat > /tmp/cks-4-3/audit-policy.yaml <<'EOF'
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - RequestReceived
rules:
  - level: Metadata
    verbs: ["get", "list", "watch"]
    resources:
      - group: ""
        resources: ["secrets"]
EOF
```

<details>
<summary>Solution notes</summary>

This policy captures who read or watched Secret resources without logging response bodies. If you used `RequestResponse` for `get secrets`, the audit backend could receive the Secret payload and become another sensitive data store. In a kubeadm-style static Pod control plane, remember that both the audit policy path and audit log path must be mounted into the API server container. Also plan log retention, because Secret-heavy controllers can generate many audit events.
</details>

### Success Criteria

- [ ] You decoded a Secret value from the API response and can explain why that is not encryption.
- [ ] Your `EncryptionConfiguration` places an encrypting provider before `identity`.
- [ ] Your RBAC check allows named `get` on one Secret and denies namespace-wide `list`.
- [ ] Your runtime example mounts the Secret as a file and uses an image that contains the executed binary.
- [ ] Your audit policy logs Secret access at `Metadata` level rather than copying payloads into logs.

## Sources

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Good practices for Kubernetes Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Using a KMS provider for data encryption](https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/)
- [Kubernetes v1.29 release notes: KMS v2 stable](https://kubernetes.io/blog/2023/12/13/kubernetes-v1-29-release/)
- [Configure Service Accounts for Pods](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)
- [Kubernetes Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [Kubelet TLS bootstrapping](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/)
- [Kubernetes RBAC reference](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [External Secrets Operator documentation](https://external-secrets.io/latest/)
- [External Secrets Operator SecretStore API](https://external-secrets.io/latest/api/secretstore/)
- [External Secrets Operator ClusterSecretStore API](https://external-secrets.io/latest/api/clustersecretstore/)
- [Bitnami Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [HashiCorp Vault on Kubernetes](https://developer.hashicorp.com/vault/docs/deploy/kubernetes)
- [Vault Agent Injector](https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector)
- [Secrets Store CSI Driver](https://github.com/kubernetes-sigs/secrets-store-csi-driver)
- [Secrets Store CSI Driver documentation](https://secrets-store-csi-driver.sigs.k8s.io/)

## Next Module

[Module 4.4: Runtime Sandboxing](../module-4.4-runtime-sandboxing/) - Secure your pods beyond RBAC by learning how gVisor and Kata Containers add stronger workload isolation boundaries.
