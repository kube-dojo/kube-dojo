---
revision_pending: false
title: "Module 4.1: Vault & External Secrets"
slug: platform/toolkits/security-quality/security-tools/module-4.1-vault-eso
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 minutes

## What You'll Be Able to Do

Completing this module equips you to design and operate Kubernetes secret delivery using external stores rather than ad hoc copies, with Vault and External Secrets Operator as the reference implementation throughout the exercises and quiz scenarios.

- **Implement External Secrets Operator to sync Vault secrets into Kubernetes Secrets automatically**
- **Configure Vault's Kubernetes authentication and dynamic secret generation for database credentials**
- **Secure secret rotation with zero-downtime patterns: `refreshInterval` on ExternalSecrets for KV sync, and `VaultDynamicSecret` generators for Vault dynamic engines (database, PKI, cloud)**

---

## Why This Module Matters

**Hypothetical scenario:** A platform team migrates three hundred application credentials from hand-maintained Kubernetes `Secret` objects into a centralized external store during a staged cutover. The migration plan looks clean on paper: each team declares an `ExternalSecret`, ESO materializes native Secrets, and GitOps repos finally contain only references instead of base64 blobs. On cutover night, two namespaces lose database connectivity because several `remoteRef.key` paths pointed at retired KV paths, and one team deleted their legacy Secrets before the controller reported `SecretSynced`. Recovery takes most of a weekend because nobody had a single dashboard showing sync status across clusters, and audit logs could not answer which pod last read the compromised static password that had lived in a ConfigMap for two years.

That scenario is illustrative, not a report of a specific organization. The durable lesson is that **secrets management on Kubernetes is a systems problem**, not a storage problem. Native `Secret` objects solve the narrow API contract—mount env vars, project volumes—but they do not solve lifecycle, rotation, GitOps safety, blast-radius control, or authoritative audit. External stores plus sync operators (we use **External Secrets Operator** with **HashiCorp Vault** as the running backend) address the lifecycle layer while still letting existing workloads consume familiar Kubernetes primitives.

Every production breach post-mortem eventually surfaces credentials in an unexpected place: a committed `.env` file, a CI variable with overly broad scope, a `ConfigMap` that was never meant to hold passwords, or a long-lived database user shared by twelve microservices. **Secrets sprawl** is what happens when convenience wins over control. The durable capability you are learning is how to **centralize authority**, **automate rotation**, **scope access per workload**, and **keep Git repositories free of plaintext**—using Vault and ESO as concrete tools, not as the subject of a product tour.

Platform engineers inherit this problem whether or not applications "use Vault." If any team can `kubectl create secret generic` with a shared password, you already operate a shadow store with no rotation, no audit, and unbounded duplication into Helm values and CI caches. Standardizing on ESO does not remove human creativity—it **redirects** it: instead of inventing another S3 bucket of `.env` files, teams declare ExternalSecrets that platform reviewers can grep in Git. The win is visibility and consistent controls, not a magic elimination of secrets from the cluster entirely.

---

## The Kubernetes Native Secret Problem

Kubernetes `Secret` objects look like security primitives because the API names them secrets, but the platform treats them as typed configuration blobs with mild obfuscation. Values in `data` and `stringData` fields are **base64-encoded**, which is encoding for transport—not encryption. Anyone with RBAC read access to Secrets in a namespace, access to etcd backups, or access to the control plane audit stream can recover cleartext without breaking cryptography. **Encryption at rest** for etcd is optional and configured cluster-wide through `EncryptionConfiguration` and often a KMS provider; it protects etcd media, not every downstream consumer, and it does not fix overly broad RBAC or accidental logging of environment variables.

The GitOps conflict makes the problem sharper. Declarative repositories want to be the source of truth for desired state, yet committing cleartext credentials violates every reasonable security policy. Teams respond with anti-patterns: sealed blobs checked into Git without rotation discipline, manual `kubectl create secret` steps documented in runbooks, or secrets duplicated into CI systems that outlive the engineers who created them. Each workaround creates a **second source of truth** that drifts from the application manifests operators actually deploy.

RBAC leakage amplifies blast radius. A `Secret` mounted into one Deployment may be readable by any identity with `get/list` on Secrets in that namespace, including debugging tools, misconfigured CI jobs, and compromised service accounts. Native Secrets also land in etcd with object versioning; backups, snapshots, and test-cluster restores copy them forward unless you operate rigorous key rotation and deletion practices. **The durable insight:** Kubernetes gives you a **delivery mechanism** for sensitive material to pods; it does not give you **secrets management**—generation, policy, rotation, leasing, auditing, and emergency revocation across environments.

Control-plane operators sometimes assume **EncryptionConfiguration** alone satisfies auditors. Encryption at rest protects backup media and etcd disks from casual inspection, yet it does not prevent authorized API clients from reading decrypted content through normal Kubernetes APIs. Key rotation for encryption providers is also a planned event: providers and keys must be updated in order without leaving objects unreadable. Treat etcd encryption as a necessary layer in depth, then implement external lifecycle management for anything an attacker would actually exfiltrate during a realistic compromise—long-lived API tokens, database passwords, signing keys—not as a substitute for those practices.

Application developers experience the gap as **environment variable convenience**. Twelve-factor guidance encourages config via env vars, which Kubernetes satisfies through `envFrom.secretRef`. That pattern is ergonomically excellent and security-poor when the backing Secret is static, widely readable, and copied into logs by frameworks that print configuration on startup at debug level. Platform defaults should steer teams toward **projected volumes**, **read-only mounts**, and **external sync with rotation** while linters flag `secretKeyRef` usage for highly sensitive key names in pull requests.

---

## Durable Solution Patterns

Mature platforms combine one or more patterns below. None is universally superior; each optimizes different constraints: GitOps compatibility, whether a native `Secret` ever exists, rotation cadence, operational complexity, and cloud portability.

**External store plus sync operator.** A controller running in the cluster authenticates to an authoritative backend (Vault KV, cloud secret manager, 1Password, and others) and materializes a native Kubernetes `Secret`. **External Secrets Operator (ESO)** is the worked example in this module: you declare `SecretStore`/`ClusterSecretStore` for connectivity and auth, then `ExternalSecret` for desired keys, refresh interval, and templating. Applications keep using `secretKeyRef`; the platform gains centralized rotation and audit at the backend. Tradeoff: a native `Secret` still exists in etcd unless you add additional controls—so RBAC and encryption-at-rest remain relevant.

**Encrypted-in-Git.** Tools such as **Sealed Secrets** and **SOPS with age** let you commit ciphertext that only the cluster (or holders of private keys) can decrypt. This preserves GitOps purity without plaintext in remotes. Tradeoff: rotation and access distribution follow key-management rules you own; dynamic database credentials are not the sweet spot unless paired with another pattern.

**Sidecar or CSI injection.** **Vault Agent Injector** and the **Secrets Store CSI Driver** with provider plugins mount secrets as files or env sources **without** creating a Kubernetes `Secret` object. The material travels directly from the backend to the pod filesystem or memory according to policy. Tradeoff: stronger reduction of etcd exposure, but you must ensure application and sidecar lifecycle align, and local node compromise remains in scope.

**Dynamic and short-lived secrets.** Backends like Vault **database**, **PKI**, and **cloud** engines mint credentials with **TTL and lease** metadata. Each request can yield unique usernames, passwords, or certificates that expire automatically. Tradeoff: applications must tolerate rotation or rely on frequent sync; operations gain precise blast-radius containment when a credential leaks.

Teaching these patterns as a **capability spine** keeps the module valid even when individual vendors rev versions or licenses. Vault and ESO appear throughout as **illustrative** implementations; the Rosetta table later maps the same capabilities to peer tools.

Understanding **when to combine patterns** matters as much as picking one. A typical progressive adoption path starts with encrypted-in-Git or a cloud manager for bootstrap credentials, introduces ESO for application delivery once roles exist, and reserves injection for tiers where etcd persistence is unacceptable. Skipping straight to injection everywhere often overwhelms platform teams with sidecar lifecycles before basic RBAC hygiene is fixed. Conversely, stopping at native Secrets synced from Vault without etcd encryption or namespace RBAC reviews leaves a false sense of completion because the delivery problem is solved while the persistence and access problems remain largely unchanged.

The **authoritative store** concept is the hinge. Exactly one system should mint, rotate, and revoke a credential; every downstream copy—Kubernetes `Secret`, mounted file, or CI variable—is a cache with expectations attached. When caches multiply without TTL discipline, incident response becomes archaeology: five copies of the same API key with unknown readers and unknown rotation cadence. Platform engineering success is measured by shrinking the number of caches and shortening their lifetimes, not by accumulating more secret-shaped objects across clusters.

---

## GitOps, Compliance, and the Second Source of Truth


## Landscape Snapshot and Rosetta

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> - **HashiCorp Vault** community edition is distributed under the **Business Source License (BSL)**; HashiCorp announced the license change in August 2023. See [Vault licensing](https://developer.hashicorp.com/vault/docs/license).
> - **OpenBao** is a community fork maintained under **MPL 2.0**, hosted under the Linux Foundation OpenSSF umbrella; it targets API compatibility with the Vault 1.14-era lineage. See [OpenBao documentation](https://openbao.org/docs/).
> - **IBM completed its acquisition of HashiCorp** on **27 February 2025** per [IBM's announcement](https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp,-creates-comprehensive,-end-to-end-hybrid-cloud-platform).
> - **External Secrets Operator** is a **CNCF Sandbox** project (accepted **26 July 2022**); an incubation application was deferred in 2024 with guidance to strengthen maintainer sustainability—see [CNCF project page](https://www.cncf.io/projects/external-secrets/) and the [TOC incubation thread](https://github.com/cncf/toc/issues/1486).
> - **Sealed Secrets** and **SOPS** remain widely used encrypted-in-Git options; **Secrets Store CSI Driver** is a Kubernetes SIG subproject for mount-time injection.

| Capability | ESO + Vault (this module) | Sealed Secrets | SOPS + age | Vault Agent Injector | Secrets Store CSI | Cloud secret managers (AWS/GCP/Azure) |
|------------|---------------------------|----------------|------------|----------------------|-------------------|---------------------------------------|
| Sync to native K8s `Secret` | Yes — core ESO flow | Yes — decrypt in cluster | Yes — with tooling | No — direct injection | Optional — often avoids etcd Secret | Yes — via ESO providers |
| Encrypted-in-Git | Indirect — refs only in Git | Yes — SealedSecret CRD | Yes — ciphertext in repo | No | No | No |
| CSI / sidecar injection | Via separate Vault tooling | No | No | Yes | Yes — provider plugins | Via provider-specific drivers |
| Dynamic secrets (DB/PKI/cloud) | Yes — Vault engines + ESO generators | No | No | Yes — Vault native | Yes — with Vault provider | Limited — cloud-native scopes |
| GitOps-safe declarative refs | Yes — ExternalSecret manifests | Yes — SealedSecret manifests | Yes — encrypted files | Partial — annotations on pods | Partial — SecretProviderClass | Yes — provider CRDs |
| Multi-backend portability | High — ESO provider model | Low — cluster-bound keys | Medium — key distribution | Vault-centric | Provider-dependent | Cloud-vendor scoped |

Use the Rosetta to **choose patterns**, not to crown a winner. Many production platforms blend **ESO for application Secrets**, **CSI or Agent** for especially sensitive tiers, and **SOPS or Sealed Secrets** for bootstrapping or offline disaster bundles.

License and ownership facts belong in the snapshot precisely because they churn independently of the capability model. A team standardized on Vault CE under MPL years ago may need a deliberate review after BSL and corporate acquisition headlines—not because the architecture was wrong, but because procurement, redistribution, and fork strategy assumptions changed. Likewise, CNCF Sandbox status tells you about governance maturity and ecosystem visibility, not about whether ESO's CRDs fit your GitOps workflow today. Treat maturity labels as planning inputs; validate fit with proofs of concept against your backends and your compliance regime.

---

## GitOps, Compliance, and the Second Source of Truth

GitOps repositories want to describe **desired state** completely, yet security policy forbids cleartext credentials in Git remotes, issue trackers, and public CI logs. The durable resolution is to commit **references and contracts**—which keys a workload needs, which store backs them, refresh expectations—while keeping **values** in systems designed for confidentiality and audit. ExternalSecret manifests embody that contract: reviewers see names, namespaces, and backend paths in diffs without seeing passwords.

Compliance frameworks frequently ask who accessed a secret, when rotation last occurred, and whether emergency revocation is practiced. Native Kubernetes Secrets offer limited answers: RBAC tells you who may read objects, not who did read them at what time, unless you invest heavily in audit logging and still miss off-cluster copies. Central backends like Vault add **request audit trails** when devices are enabled, tying authentication identity to path operations. ESO becomes the **delivery agent** in that story rather than the **system of record**, which simplifies reasoning during audits: Vault (or your cloud manager) holds history; Kubernetes holds current materialized state for pod consumption.

Sealed Secrets and SOPS remain valuable when teams need **air-gapped bootstrap** or when the secret store itself requires credentials that cannot yet be delivered dynamically. The anti-pattern is using encrypted-in-Git for high-churn database passwords because rotation becomes a re-encryption ceremony across every branch and environment. Pair encrypted-in-Git with static, rarely changed material—initial Vault unseal shards stored offline, emergency break-glass bundles—and pair ESO with material that rotates on schedule or on demand.

---

## External Secrets Operator: Architecture and CRDs

External Secrets Operator watches custom resources and reconciles desired secret material into Kubernetes. The mental model is **declare intent, not copy/paste**: platform teams commit `ExternalSecret` manifests to Git; the controller handles fetch, transformation, and ownership of the target native `Secret`. ESO is **backend-agnostic**—the same CRD shapes work for Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, and numerous community providers documented on [external-secrets.io](https://external-secrets.io/latest/introduction/overview/).

**SecretStore** is namespaced: it encodes how to reach a backend and how the controller authenticates in that namespace. **ClusterSecretStore** is cluster-scoped and typically pairs with a centrally managed service account and tighter policy, optionally constrained by namespace selectors or conditions. Splitting store connectivity from secret mapping lets platform teams publish vetted backends while application teams own only the keys they need.

**ExternalSecret** binds a store to a target native `Secret`. Important fields include `refreshInterval` (how often to reconcile), `data`/`dataFrom` (key mapping or bulk extract), `target.template` (compose connection strings or TLS keystores), and ownership policies such as `creationPolicy: Owner` so deleting the `ExternalSecret` can garbage-collect the materialized Secret. **PushSecret** (see ESO docs) reverses flow for scenarios that must write generated material back to a backend—useful for hybrid migrations but less common day-to-day than pull sync.

```
ESO FLOW
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  1. Create ExternalSecret CR                                    │
│     ┌───────────────────┐                                       │
│     │  ExternalSecret   │                                       │
│     │  name: db-creds   │                                       │
│     │  secretStore: ... │                                       │
│     └─────────┬─────────┘                                       │
│               │                                                  │
│  2. ESO Controller watches                                       │
│               │                                                  │
│               ▼                                                  │
│     ┌───────────────────┐    3. Fetch    ┌───────────────────┐ │
│     │  ESO Controller   │───────────────▶│  Vault / AWS /    │ │
│     │                   │◀───────────────│  GCP / Azure      │ │
│     └─────────┬─────────┘    4. Return   └───────────────────┘ │
│               │                                                  │
│  5. Create/Update Kubernetes Secret                              │
│               │                                                  │
│               ▼                                                  │
│     ┌───────────────────┐                                       │
│     │  Secret           │◀── Pod mounts this                    │
│     │  name: db-creds   │                                       │
│     └───────────────────┘                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Installation commonly uses the upstream Helm chart with CRDs bundled. Production clusters should pin chart versions, run the controller with least-privilege RBAC, and network-policy the egress path to Vault or cloud APIs.

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

helm install external-secrets external-secrets/external-secrets \
  -n external-secrets \
  --create-namespace \
  --set installCRDs=true
```

When debugging sync failures, treat the **`ExternalSecret` status conditions** and controller logs as primary signals. A typo in `remoteRef.key` for Vault KV v2 is a frequent root cause: ESO expects the logical secret name (for example `production/database`), not the internal `secret/data/...` API path exposed in Vault CLI output.

Operational maturity shows up in **how teams observe sync health at scale**. A single `kubectl describe` suffices in a lab; production needs aggregated views—Prometheus metrics if you expose them, GitOps health checks, or periodic controllers that alert when any `ExternalSecret` in a fleet reports error states beyond a short grace window. Treat desync like a broken deployment: it is user-visible only when applications fail, but the control-plane signal existed earlier in the ExternalSecret status.

**PushSecret** deserves a mention even when pull sync dominates day-to-day work. Some migrations require writing generated or rotated material from Kubernetes back into a legacy vault path so mainframe-era batch systems or external SaaS with manual upload portals stay synchronized. Push flows invert trust boundaries: the cluster becomes a writer, not only a reader, so policies must be tighter and audits more frequent. Default to pull sync unless a documented integration requires push.

---

## External Secrets Operator: Store and Sync Examples

The YAML below shows the two store scopes and three common `ExternalSecret` shapes: per-key mapping, bulk extract, and templated connection strings. These examples assume Vault KV v2 mounted at `secret/`; adjust `server`, `path`, and auth to match your environment.

```yaml
# SecretStore - namespaced
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: production
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "production-apps"
          serviceAccountRef:
            name: "external-secrets"
---
# ClusterSecretStore - cluster-wide
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "cluster-wide-read"
          serviceAccountRef:
            name: "external-secrets"
            namespace: "external-secrets"
---
# Basic secret sync
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-credentials
    creationPolicy: Owner
  data:
  - secretKey: username
    remoteRef:
      key: production/database
      property: username
  - secretKey: password
    remoteRef:
      key: production/database
      property: password
---
# Sync entire secret (all keys)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-config
spec:
  refreshInterval: 30m
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: app-config
  dataFrom:
  - extract:
      key: production/app-config
---
# Template the secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-url
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-url
    template:
      type: Opaque
      data:
        DATABASE_URL: "postgresql://{{ .username }}:{{ .password }}@postgres:5432/mydb"
  data:
  - secretKey: username
    remoteRef:
      key: production/database
      property: username
  - secretKey: password
    remoteRef:
      key: production/database
      property: password
```

Templating is how platforms keep application interfaces stable while backends evolve—teams store atomic fields in Vault but deliver a single `DATABASE_URL` env var the app already understands. Keep templates in Git-reviewed manifests so connection string composition stays auditable.

When multiple applications consume overlapping keys from one Vault path, prefer **`dataFrom.extract`** with careful **`target.template`** merging rather than duplicating `remoteRef` stanzas per Deployment. Central teams can publish "golden" ExternalSecret patterns in internal catalogs so application repos only parameterize namespace, secret name, and key prefix. That reduces drift where each team copies YAML from outdated blog posts with subtly wrong `path` or `version` fields.

Production stores should enforce **TLS verification** on Vault endpoints (`caProvider` or cert bundles in provider config per ESO docs) rather than disabling TLS checks to unblock labs. Similarly, restrict which namespaces may reference a `ClusterSecretStore` using Kubernetes admission policy in addition to ESO conditions—defense in depth beats assuming developers will never paste a cluster store reference into an experimental namespace.

---

## HashiCorp Vault as an External Store

Vault is a secrets and identity backend organized around **auth methods**, **secrets engines**, and **policies**. Clients authenticate, receive a **token** with attached policies, then access paths permitted by those policies. Audit devices record requests when enabled. Storage backends (commonly integrated Raft in modern deployments) hold encrypted blobs; **unseal** operations protect master keys. This module treats Vault as the **authoritative store** ESO reads—not as the only valid choice. **OpenBao** exposes a compatible API surface for teams prioritizing OSI-approved licensing; ESO provider configuration is largely analogous though you must verify version matrices in provider docs.

Teams evaluating **Vault versus OpenBao** should separate licensing questions from architecture questions. The capability spine—dynamic engines, Kubernetes auth, injection, ESO sync—is shared because APIs intentionally align. Differences emerge in enterprise feature packaging, long-term roadmap ownership, and organizational comfort with BSL source-available terms after IBM's acquisition of HashiCorp. Neither choice removes the obligation to operate HA storage, backup, and unseal procedures correctly; a misconfigured cluster fails equally embarrassingly regardless of trademark on the binary.

High availability for the external store is a dependency of every synced Secret. If Vault is down, ESO cannot reconcile; applications may continue with last-synced material until TTLs expire, then fail in bulk. Run game days that include Vault outage simulation so teams know whether applications fail open or closed and whether on-call playbooks prioritize restoring Vault or temporarily pinning emergency KV versions. Document RTO/RPO for secrets separately from application RTO because they are coupled during incidents even when charts treat them as independent microservices.

```
VAULT ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                         VAULT CLUSTER                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API / CLI                             │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                        │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │                  AUTH METHODS                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │  K8s    │ │  OIDC   │ │  LDAP   │ │  Token  │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                        │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │                 SECRETS ENGINES                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │   KV    │ │Database │ │   PKI   │ │  AWS    │       │   │
│  │  │(static) │ │(dynamic)│ │ (certs) │ │(dynamic)│       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                        │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │                    STORAGE                               │   │
│  │         Raft (integrated) / Consul / etcd               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### KV v2 for Static Material

The **KV secrets engine version 2** adds versioning, soft-delete, and metadata paths separate from data paths. Static API keys, OAuth client secrets, and TLS bundles that change infrequently fit here. ESO reads logical keys; Vault retains version history so operators can roll back a bad update without restoring etcd snapshots. Versioning complements GitOps: the declared `ExternalSecret` stays stable while operators bump `remoteRef.version` when intentionally pinning.

```bash
vault kv put secret/myapp/config \
  api_key="sk-xxx" \
  db_password="hunter2"

vault kv get secret/myapp/config
```

Policies should grant **least privilege** per path prefix. A read-only application policy might allow `read` on `secret/data/myapp/*` and explicitly `deny` administrative paths.

```hcl
path "secret/data/myapp/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/myapp/*" {
  capabilities = ["list"]
}

path "secret/data/admin/*" {
  capabilities = ["deny"]
}
```

### Dynamic Secrets and Leases

**Dynamic secrets** invert the static-password antipattern. Instead of one shared database user embedded in twelve Deployments, Vault's database engine creates a **unique role** with a **TTL** for each credential request. When the lease expires, Vault revokes the user automatically. If a pod logs a password or an attacker exfiltrates a file, the credential's scope is limited in time and often in privilege. This is why dynamic secrets reduce **blast radius** compared with long-lived KV passwords copied into clusters.

```bash
vault secrets enable database

vault write database/config/postgres \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@postgres:5432" \
  allowed_roles="readonly" \
  username="vault" \
  password="vault-password"

vault write database/roles/readonly \
  db_name=postgres \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

vault read database/creds/readonly
```

PKI and cloud engines follow the same lifecycle philosophy: **mint, use, expire, revoke**. ESO integrates through **generator** resources such as `VaultDynamicSecret` so Kubernetes-native Secrets can reflect periodically minted credentials where applications still consume env vars rather than files.

The conceptual shift for application teams is subtle but important: **they no longer "own" a password**; they own **access to a role** that mints passwords. Onboarding documentation should describe Vault paths and Kubernetes service accounts, not shared credentials in wiki pages. Incident runbooks should include **lease revocation** commands and ESO resync steps rather than "ask DBA to reset the shared user again." That cultural move often determines whether dynamic secrets actually reduce risk or merely add moving parts.

---

## Kubernetes Authentication into Vault

Long-lived Vault tokens stored in Git or baked into images recreate the sprawl you are trying to eliminate. **Kubernetes auth** binds Vault roles to **service account identity**: the pod (or ESO controller) presents a projected service account token; Vault validates it against the Kubernetes TokenReview API and returns a **short-lived Vault token** with attached policies.

```bash
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

vault write auth/kubernetes/role/myapp \
  bound_service_account_names=myapp \
  bound_service_account_namespaces=production \
  audiences=vault \
  policies=app-readonly \
  ttl=1h
```

Modern Vault releases validate **`aud` claims** on projected tokens. Ensure the `audiences` field on the role matches the audience configured on the service account token projection used by ESO or your application. Mismatched audiences manifest as auth failures that look like intermittent network errors until you inspect Vault audit logs.

For ESO specifically, the **`serviceAccountRef` on the SecretStore** determines which identity fetches secrets. Platform teams usually dedicate a service account per namespace or per tenant role, mapping one-to-one to Vault policies. Avoid reusing a cluster-admin-adjacent identity for secret retrieval; compromise of that token becomes total store read access.

TokenReview failures often trace to **cluster API endpoint mismatches** when Vault runs outside the cluster but auth configuration still points at an internal URL reachable only from pods. Helm charts and Terraform modules frequently templatize `kubernetes_host`; verify the value from the Vault server's network perspective, not from your laptop. Rotating the Kubernetes CA requires updating Vault's auth config promptly or every ESO sync halts simultaneously—a classic platform-wide outage with a narrow fix window if playbooks omit CA rotation coupling.

---

## Rotation: KV Refresh versus Dynamic Generators

Rotation strategy depends on whether the material is **static KV** or **engine-generated dynamic** credentials. Conflating the two leads to either stale passwords (KV synced too rarely) or excessive database churn (dynamic TTL shorter than connection pools tolerate).

For KV secrets, **`refreshInterval` on `ExternalSecret`** controls how often ESO re-reads the backend and updates the native Secret. Critical credentials might reconcile every five to fifteen minutes; slow-changing TLS bundles might use twenty-four hours. Pair periodic sync with **Reloader** or a controlled rollout mechanism so applications pick up new values without manual pod deletion.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: rotating-db-creds
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
    deletionPolicy: Retain
  dataFrom:
  - sourceRef:
      generatorRef:
        apiVersion: generators.external-secrets.io/v1alpha1
        kind: VaultDynamicSecret
        name: dynamic-db-credentials
```

```yaml
apiVersion: generators.external-secrets.io/v1alpha1
kind: VaultDynamicSecret
metadata:
  name: dynamic-db-credentials
spec:
  path: "/database/creds/app"
  method: "GET"
  resultType: "Data"
  provider:
    server: "https://vault.example.com"
    auth:
      kubernetes:
        mountPath: "kubernetes"
        role: "external-secrets-operator"
        serviceAccountRef:
          name: "external-secrets"
```

Use **`VaultDynamicSecret` generators** when the Vault path returns **new lease-bound credentials** each call—database, PKI, or cloud STS-style engines. Static KV paths should use `data`/`dataFrom` with `refreshInterval`, not generators, unless you intentionally re-fetch versioned keys.

Applications that cache credentials in memory need explicit **rotation tolerance**: connection pools should recycle before TTL expiry, or sidecars should signal reload. For batch jobs, short TTL plus retry-on-auth-failure is often enough. For long-lived servers, coordinate TTL with `refreshInterval` and rolling restart annotations.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  annotations:
    reloader.stakater.com/auto: "true"
spec:
  template:
    spec:
      containers:
      - name: app
        envFrom:
        - secretRef:
            name: db-credentials
```

Remember to **`vault write -force database/rotate-root/...`** on a schedule for the Vault admin connection itself—root database credentials are easy to forget because applications no longer use them directly after dynamic roles land.

**Zero-downtime rotation** combines three levers: refresh cadence on the `ExternalSecret`, application tolerance for credential change, and orchestration that rolls pods without hard downtime. For stateless HTTP services, Reloader-triggered rolling updates are often sufficient. For connection pools, stagger refreshes so new credentials propagate before old leases expire, or set TTL slightly longer than two refresh intervals to absorb transient sync delays. Document the arithmetic explicitly in service runbooks so on-call engineers do not shorten TTL in panic during incidents and accidentally amplify outages.

Database engines may also support **graceful revocation delays** configured in Vault roles; use them when applications cannot reconnect instantly. The goal is not the shortest possible TTL—it is the shortest TTL compatible with observed reconnect latency plus ESO reconcile time. Measure both before tightening production values copied from tutorial examples.

---

## Injection Paths: When Native Secrets Are Optional

Not every workload must materialize a Kubernetes `Secret`. **Vault Agent Injector** mutating webhooks annotate pods to run an agent sidecar that authenticates and renders files under `/vault/secrets`. **Secrets Store CSI Driver** mounts volumes backed by provider plugins; the [Secrets Store CSI documentation](https://secrets-store-csi-driver.sigs.k8s.io/introduction) describes mount-time retrieval and optional sync-to-Secret behaviors. Choose injection when etcd confidentiality is paramount, when secrets are large keystores, or when you want per-pod identity without cluster-wide Secret objects.

Injection trades operational complexity for narrower persistence: you must manage sidecar upgrades, ensure init order before application start, and verify node-level protections. Many teams use **ESO for mainstream app env vars** and **CSI or Agent for tier-zero keys**—a deliberate split documented in the Rosetta rather than a single global mandate.

Sidecars also shift **failure modes**: if Vault is unavailable at pod start, the main container may never become ready, which is correct fail-closed behavior but requires SLO thinking on Vault itself. Health checks should distinguish "application broken" from "secret mount pending." For batch jobs, consider init-container-only agents that exit after rendering files so long-running sidecars do not inflate resource requests across thousands of CronJob pods.

---

## Multi-Tenant Secrets Patterns

Shared Vault clusters commonly partition paths by team (`secret/team-a/...`, `secret/team-b/...`) and bind **Kubernetes auth roles** so each namespace's ESO identity can read only its prefix. **ClusterSecretStore** suits truly shared material—wildcard TLS, corporate CA bundles—while **SecretStore** keeps tenant credentials from sharing authentication paths that could be misconfigured into cross-tenant reads.

```
MULTI-TENANT SECRETS ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                         VAULT                                    │
│  secret/                                                         │
│  ├── team-a/  ◀── team-a-policy                                 │
│  ├── team-b/  ◀── team-b-policy                                 │
│  └── shared/certificates/  ◀── shared-readonly                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Namespace team-a          │  Namespace team-b                  │
│  SecretStore vault-team-a  │  SecretStore vault-team-b          │
└─────────────────────────────────────────────────────────────────┘
```

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-team-a
  namespace: team-a
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "team-a"
          serviceAccountRef:
            name: "vault-auth"
```

For shared TLS, a `ClusterSecretStore` plus namespace **conditions** prevents staging namespaces from pulling production certificates while still centralizing renewal in Vault PKI or a corporate CA workflow.

Tenant onboarding checklists should include **path prefix conventions**, **Vault policy names**, **Kubernetes auth role names**, and **allowed service account names** as a single tuple verified in staging before production namespaces receive access. Drift happens when application teams create arbitrary service account names that no longer match `bound_service_account_names` on Vault roles; CI linting against allowed tuples catches most mistakes cheaper than weekend outages.

---

## Audit, Monitoring, and Emergency Revocation

Centralized secrets management earns its keep during incidents. Enable Vault **audit devices** to record authenticated requests with path, operation, and identity metadata. Forward logs to your SIEM with retention aligned to compliance requirements. ESO controller logs complement Vault audit by showing reconcile errors, backoff behavior, and provider HTTP failures—correlate timestamps when users report "the app says login failed" after a Vault policy change.

**Emergency revocation** has two layers: invalidate active **leases** for dynamic secrets (`vault lease revoke` or revoke-by-prefix operations where appropriate), and **disable or rotate static KV versions** when material may have leaked from etcd backups or CI logs. After revocation, force ESO reconcile by bumping an annotation or temporarily shortening `refreshInterval`; waiting passively for the next interval extends exposure when attackers already possess copied values. Communicate with application owners before mass revocation—fail-closed security helps only if teams expect credential death and have rehearsed reconnect behavior.

Monitoring should include synthetic checks: a canary `ExternalSecret` in a platform namespace that reads a low-risk test key proves end-to-end health beyond "Vault UI loads." Alert on rising sync error rates per cluster and on Vault seal status changes. These signals catch network policy regressions and certificate rotations on Vault ingress long before application teams open tickets.

Treat **secret consumption** as part of workload identity reviews the same way you review `ClusterRoleBindings`. During access recertification campaigns, export Vault audit samples for paths tied to each product line and compare against expected service account identities. Orphaned paths—still read monthly but owned by decommissioned namespaces—are debt that becomes incident fuel when forgotten credentials leak from old etcd backups. Automate path ownership tags in Vault metadata where possible so CI can fail when application repos disappear but secret paths remain.

---

## Patterns, Anti-Patterns, and Decision Framework

### Patterns

**Pattern: Git declares references, store holds values.** Commit `ExternalSecret` manifests and policy-as-code for Vault roles; never commit cleartext or long-lived root tokens. Reviewers can reason about blast radius because paths and namespaces are visible in diffs.

**Pattern: One Vault role per ESO service account.** Map Kubernetes identity to narrowly scoped policies. When a namespace is compromised, attackers inherit only that role's paths—not the entire KV tree.

**Pattern: Layer encryption at rest with RBAC least privilege.** Even with ESO, enable etcd encryption and restrict `get/list/watch` on Secrets. Defense in depth assumes etcd backups and control-plane access are realistic threats.

**Pattern: Dual-run migrations.** Operate legacy Secrets and ESO-managed Secrets in parallel until `SecretSynced` is proven and applications validate connectivity. Only then retire manual objects—see the hypothetical scenario in **Why This Module Matters**.

**Pattern: Version and pin intentionally.** KV v2 supports version pins in ESO when rolling out breaking secret shape changes; unpin after consumers migrate. Document pin duration in change tickets so security debt does not linger across quarters.

**Pattern: Separate control plane and data plane credentials.** Vault unseal keys, cloud KMS credentials for auto-unseal, and ESO bootstrap tokens belong in break-glass procedures distinct from application database roles. Mixing them in one policy path guarantees over-privileged recovery runbooks.

### Anti-Patterns

**Anti-pattern: Root or admin tokens in CI.** Any token that can read `secret/*` or manage policies becomes a universal skeleton key. Use namespaced roles and short TTL tokens bound to workload identity.

**Anti-pattern: Infinite TTL on dynamic roles "to reduce churn."** Defeating TTL removes the primary benefit of dynamic secrets and recreates shared-password incidents with extra steps.

**Anti-pattern: ClusterSecretStore without namespace guards.** A cluster-wide store simplifies demos and creates cross-environment leakage when every namespace can reference the same backend role.

**Anti-pattern: Skipping Vault audit devices.** Without audit logs, sync errors and unauthorized reads devolve into guesswork during incidents.

**Anti-pattern: Logging secret values in ESO debug modes.** Temporary debug logging during troubleshooting sometimes exposes fetched material to centralized log stacks with longer retention than etcd. Disable debug flags explicitly in change tickets and verify log redaction policies with security before enabling verbose provider logs in production namespaces.

### Decision Framework

| Your constraint | Prefer | Why |
|-----------------|--------|-----|
| GitOps must stay plaintext-free with minimal new CRDs | Sealed Secrets or SOPS | Ciphertext in Git; cluster keys stay in cluster |
| Existing apps only support `secretKeyRef` env vars | ESO + external store | Keeps pod contract; centralizes authority |
| Must avoid native Secret in etcd entirely | Vault Agent or CSI driver | Mount-time delivery without Secret object |
| Database creds rotate frequently; many consumers | Vault dynamic engine + ESO generator | Unique short-lived users; automatic revocation |
| Multi-cloud portability with one controller | ESO with provider abstraction | Same CRDs; swap SecretStore provider stanza |
| Strong OSI license requirement for backend | OpenBao + ESO Vault provider | MPL-licensed fork; verify compatibility matrix |

```mermaid
flowchart TD
  A[Need secrets in Kubernetes] --> B{Can a native Secret exist in etcd?}
  B -->|Yes| C{Need dynamic DB/PKI creds?}
  B -->|No| D[CSI or Vault Agent injection]
  C -->|KV/static| E[ESO ExternalSecret + refreshInterval]
  C -->|Dynamic| F[ESO VaultDynamicSecret generator]
  E --> G[Enable etcd encryption + tight RBAC]
  F --> G
  D --> H[Per-pod SA auth + short TTL]
```

---

## Did You Know?

- **Kubernetes encrypt-at-rest is cluster-wide, not per-Secret:** You enable it via `EncryptionConfiguration` and optional KMS providers; it protects etcd persistence but does not replace external lifecycle management—see the [Kubernetes encryption guide](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/).
- **KV v2 keeps metadata even after delete:** Soft-delete and version history help rollback operator mistakes; ESO typically reads live versions unless you pin `remoteRef.version`.
- **Vault dynamic database users are real SQL roles:** Each `vault read database/creds/...` issues a distinct username/password pair with `VALID UNTIL` aligned to lease TTL—revocation is explicit, not hopeful.
- **ESO provider count exceeds Vault alone:** The same `ExternalSecret` shape can target cloud vendor APIs; migrations often change only the `SecretStore` provider stanza while Deployments stay untouched.

The External Secrets project publishes provider-specific guides for each backend; treating those guides as part of your internal runbook set prevents teams from assuming AWS-only examples when your platform standardized on Vault paths and Kubernetes auth roles years ago. Revisit provider release notes quarterly because authentication defaults and CRD version bumps change more often than core Kubernetes APIs typically do in practice.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Storing Vault root token in Git | Full administrative compromise | Bootstrap with recovery keys; use Kubernetes auth and scoped policies |
| Using KV v1 paths with v2 provider config | Sync failures or empty keys | Set `version: "v2"` and use logical keys without `data/` prefix in ESO |
| Long `refreshInterval` on rotated KV secrets | Pods run stale passwords for hours | Match interval to rotation SLO; add Reloader or rolling restarts |
| Single shared Vault token for all namespaces | Massive blast radius on one leak | One Kubernetes auth role per tenant service account |
| Deleting legacy Secrets before sync verified | Immediate application outage | Dual-run until `SecretSynced=True` and apps health-check |
| Ignoring Vault audit devices | No forensic trail during incidents | Enable file or socket audit sinks with retention |
| Forgetting database root rotation | Vault admin DB cred becomes static linchpin | Schedule `vault write -force database/rotate-root/...` |
| Wrong projected token audience on K8s auth role | Auth succeeds in dev, fails in prod | Align `audiences` with service account token projection |

---

## Quiz

**Question 1:** A junior engineer argues that Kubernetes Secrets are "encrypted" because values appear as base64 in YAML dumps. Explain why that belief is dangerous in production RBAC and backup models.

<details>
<summary>Answer</summary>

Base64 is encoding for transport, not encryption. Anyone with RBAC read access to Secrets, etcd backup access, or compromised control-plane visibility can recover cleartext without breaking cryptography. Real protection requires restricting who can read Secret objects, encrypting etcd at rest with `EncryptionConfiguration`, and— for lifecycle needs—external stores with rotation, auditing, and least-privilege access paths rather than relying on the API object's obfuscation.
</details>

**Question 2:** When should you choose ESO with `VaultDynamicSecret` generators instead of a static KV `ExternalSecret` with `refreshInterval`?

<details>
<summary>Answer</summary>

Use `VaultDynamicSecret` when the Vault path represents a **dynamic engine**—database, PKI, or cloud—that mints **new lease-bound credentials** on each generation call. Use static KV sync with `refreshInterval` when values change occasionally but are not regenerated per request. Conflating the two yields either stale passwords (KV synced too rarely) or excessive database user churn (dynamic TTL shorter than connection pools tolerate). Match generator usage to engine semantics documented in Vault and ESO provider guides.
</details>

**Question 3:** During a deployment freeze, several namespaces report `SecretSyncedError` on new ExternalSecrets while older ones keep working. Describe a step-by-step investigation that separates Vault policy regressions from ESO misconfiguration.

<details>
<summary>Answer</summary>

Start with `kubectl describe externalsecret` for status conditions and events, then inspect ESO controller logs in the install namespace. Verify the referenced `SecretStore` or `ClusterSecretStore` shows valid connectivity and that Kubernetes auth audiences match the service account projection. Confirm Vault policy allows read on the intended path and that `remoteRef.key` uses the KV v2 logical name (for example `production/database`, not `secret/data/production/database`). Network policies blocking egress to Vault and expired tokens on the store's service account are frequent root causes in multi-namespace clusters.
</details>

**Question 4:** Compare blast radius of a shared static database password in KV versus Vault dynamic credentials for the same application tier.

<details>
<summary>Answer</summary>

A shared KV password reused across many Deployments means one leak grants persistent access until manual rotation completes, and you cannot tell which consumer was compromised. Dynamic credentials issue **unique users with TTL** per generation; leakage exposes only one lease window and one role's privileges. Revocation is automatic at lease end. Dynamic secrets add operational requirements—applications must handle rotation—but shrink both duration and scope of exposure, which is why dynamic engines pair well with ESO generators for data-tier access.
</details>

**Question 5:** Your security team forbids native Kubernetes Secrets in etcd for a payment service. Which pattern fits without abandoning Kubernetes scheduling?

<details>
<summary>Answer</summary>

Use **Vault Agent Injector** or **Secrets Store CSI Driver** with the Vault provider to mount secrets as files or env sources at pod start without creating a persistent Secret object in etcd. Pair per-pod Kubernetes auth with short TTL Vault tokens. This trades sidecar or CSI operational complexity for reduced etcd persistence of cleartext. Many platforms still use ESO for less sensitive tiers while restricting injection to high-sensitivity workloads—document the split explicitly in architecture reviews.
</details>

**Question 6:** Platform leadership asks whether to standardize on one ClusterSecretStore for simplicity or many namespaced SecretStores per team. What criteria should drive that decision for database credentials versus organization-wide TLS bundles?

<details>
<summary>Answer</summary>

Use **SecretStore** for tenant-scoped credentials where each namespace should authenticate with a distinct Vault role and path prefix—isolation failures stay namespace-bound. Use **ClusterSecretStore** for genuinely shared material such as organization-wide TLS bundles or CA certificates, combined with namespace **conditions** so only approved environments reference the store. Avoid cluster stores for application database credentials; the convenience of a single manifest often becomes cross-tenant leakage when conditions are forgotten during onboarding.
</details>

**Question 7:** Your team plans a weekend migration from manually created Secrets to ESO-managed Secrets for twelve production Deployments. Outline a dual-run cutover sequence that avoids the outage pattern described in the module's hypothetical scenario.

<details>
<summary>Answer</summary>

Implement External Secrets Operator alongside existing Secrets: create `SecretStore` and `ExternalSecret` objects targeting **new** native Secret names or temporarily duplicate keys, verify `SecretSynced=True`, and run application connectivity tests against the ESO-managed Secret. Update Deployments to reference the new Secret only after validation. Retire manual Secrets last. Maintain a dashboard of sync status across namespaces (`kubectl get externalsecrets -A`) during the window. This implements the dual-run pattern and avoids the cutover failure mode where typos in `remoteRef.key` surface only after old Secrets were deleted.
</details>

**Question 8:** Security architecture review flags long-lived Vault tokens embedded in legacy Helm charts. Explain how Kubernetes auth into Vault plus ESO `serviceAccountRef` reduces sprawl compared with distributing static tokens to every namespace.

<details>
<summary>Answer</summary>

Kubernetes auth binds Vault policies to **service account identity** validated through TokenReview, returning **short-lived Vault tokens** instead of embedding long-lived secrets in Git or images. ESO uses the same model via `serviceAccountRef` on SecretStore specs. Compromise of a pod yields only that role's paths and TTL—not a root token usable cluster-wide. Operators rotate and audit at Vault, while workloads never store bootstrap credentials in repositories, closing the loop between GitOps hygiene and runtime authentication.
</details>

---

## Hands-On Exercise

Set up Vault (dev or lab), install External Secrets Operator, and sync a KV secret into a native Kubernetes `Secret` using Kubernetes auth or token auth for lab simplicity.

### Environment Setup

```bash
docker run -d --name vault \
  -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=root' \
  -e 'VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200' \
  hashicorp/vault:latest

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

vault kv put secret/myapp/config \
  database_url="postgresql://user:pass@db:5432/mydb" \
  api_key="sk-test-12345"
```

Install ESO with the upstream Helm chart in a dedicated namespace so CRDs and controller RBAC remain isolated from application workloads.

```bash
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace --set installCRDs=true
```

For lab clusters, create a namespaced SecretStore that uses token authentication only long enough to validate sync semantics; production paths should use Kubernetes auth as documented earlier.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-dev
spec:
  provider:
    vault:
      server: "http://host.docker.internal:8200"
      path: "secret"
      version: "v2"
      auth:
        tokenSecretRef:
          name: vault-token
          key: token
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-config
spec:
  refreshInterval: 1m
  secretStoreRef:
    name: vault-dev
    kind: SecretStore
  target:
    name: myapp-config
  dataFrom:
  - extract:
      key: myapp/config
```

After applying manifests, confirm reconciliation by inspecting ExternalSecret conditions and comparing decoded Secret keys against the Vault KV entries you created in the setup step.

```bash
kubectl get externalsecrets
kubectl describe externalsecret myapp-config
kubectl get secret myapp-config -o yaml
```

Mark the lab complete when all of the following success criteria pass; repeat the Vault KV update test to prove refreshInterval behavior rather than assuming one-time sync.

Success criteria:

- [ ] ESO controller pods are Running in `external-secrets`
- [ ] `SecretStore` status reports valid provider configuration
- [ ] `ExternalSecret` condition shows `SecretSynced=True`
- [ ] Native Secret contains `database_url` and `api_key` matching Vault KV
- [ ] Updating Vault KV and waiting one `refreshInterval` updates the native Secret

---

## Next Module

Continue to [Module 4.2: OPA & Gatekeeper](../module-4.2-opa-gatekeeper/) for policy-as-code admission control—secrets management ensures only authorized workloads receive credentials; admission policies ensure only compliant workloads run at all.

---

## Sources

- [Kubernetes: Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) — Official guide to `EncryptionConfiguration`, KMS providers, and etcd encryption scope.
- [External Secrets Operator Overview](https://external-secrets.io/latest/introduction/overview/) — Upstream introduction to sync controllers and provider model.
- [ESO SecretStore API](https://external-secrets.io/latest/api/secretstore/) — Reference for namespaced and cluster-scoped store connectivity.
- [ESO ExternalSecret API](https://external-secrets.io/latest/api/externalsecret/) — Reference for sync intervals, templating, and ownership policies.
- [ESO HashiCorp Vault Provider](https://external-secrets.io/latest/provider/hashicorp-vault/) — Vault-specific auth and path configuration for ESO.
- [Vault KV Secrets Engine v2](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2) — Versioning, metadata paths, and delete semantics.
- [Vault Database Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/databases) — Dynamic credential generation, TTL, and revocation.
- [Vault Kubernetes Auth Method](https://developer.hashicorp.com/vault/docs/auth/kubernetes) — TokenReview integration, roles, and audience validation.
- [Vault Agent Injector on Kubernetes](https://developer.hashicorp.com/vault/docs/platform/k8s/injector) — Sidecar injection pattern without native Secrets.
- [Secrets Store CSI Driver Introduction](https://secrets-store-csi-driver.sigs.k8s.io/introduction) — Mount-time secret retrieval and provider plugins.
- [Sealed Secrets (Bitnami Labs)](https://github.com/bitnami-labs/sealed-secrets) — Encrypted-in-Git controller for Kubernetes.
- [Mozilla SOPS](https://github.com/getsops/sops) — Encrypts structured files with age/PGP for GitOps workflows.
- [OpenBao Documentation](https://openbao.org/docs/) — MPL-licensed Vault-compatible secrets management fork.
- [CNCF External Secrets Project Page](https://www.cncf.io/projects/external-secrets/) — Sandbox acceptance date and project description.
- [IBM Completes Acquisition of HashiCorp (2025-02-27)](https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp,-creates-comprehensive,-end-to-end-hybrid-cloud-platform) — Corporate ownership context for HashiCorp products.
- [Vault License FAQ](https://developer.hashicorp.com/vault/docs/license) — BSL terms for HashiCorp Vault distribution.
