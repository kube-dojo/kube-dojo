---
title: "Module 9.8: Secrets Management Deep Dive"
slug: cloud/managed-services/module-9.8-secrets-deep
sidebar:
  order: 9
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2h | **Prerequisites**: Module 9.1 (Databases), Kubernetes RBAC, cloud IAM basics

## Why This Module Matters

In December 2023, a developer at a healthcare company committed a `.env` file containing an AWS access key to a public GitHub repository. An automated scanner (one of thousands operated by attackers) detected the key within 11 minutes. By the 14-minute mark, the attacker had used the key to enumerate S3 buckets, finding one containing patient records. By minute 22, they had exfiltrated 340,000 patient records. The breach cost the company $4.8 million in HIPAA fines, $1.2 million in incident response, and immeasurable reputation damage.

The root cause was not the developer's carelessness. It was an architecture that allowed long-lived, static credentials to exist in the first place. The access key had been active for 19 months. No one had rotated it. No one monitored its usage pattern. The secret was stored in a Kubernetes Secret (base64-encoded -- not encrypted) and also in a `.env` file on the developer's laptop.

Modern secrets management eliminates this entire class of vulnerability. Dynamic secrets have short TTLs and are generated on demand. External secret operators sync secrets from vaults without human access to plaintext. Sealed Secrets encrypt values so they are safe to commit to Git. This module teaches you the full spectrum of Kubernetes secrets management, from External Secrets Operator to Secrets Store CSI Driver to HashiCorp Vault, with honest comparisons so you can choose the right approach for your environment.

---

## The Kubernetes Secrets Problem

### What Kubernetes Secrets Actually Are

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: YWRtaW4=        # base64("admin")
  password: cDRzc3cwcmQ=    # base64("p4ssw0rd")
```

Kubernetes Secrets are base64-encoded, **not encrypted**. Anyone with `kubectl get secret` access can decode them instantly:

```bash
k get secret db-credentials -o jsonpath='{.data.password}' | base64 -d
# Output: p4ssw0rd
```

### What Kubernetes Does and Does Not Provide

| Feature | Kubernetes Native | What You Actually Need |
|---------|------------------|-----------------------|
| Storage | etcd (encrypted at rest if configured) | External vault with audit logging |
| Access control | RBAC (namespace-level) | Attribute-based access with MFA |
| Rotation | Manual (delete and recreate) | Automatic with zero-downtime |
| Auditing | API audit logs (if enabled) | Who accessed what, when, from where |
| Dynamic secrets | Not supported | Short-lived, auto-expiring credentials |
| Git safety | Plaintext in manifests | Encrypted at rest in Git |

---

## External Secrets Operator (ESO): The Standard Approach

ESO is the most widely adopted solution for syncing secrets from cloud secret managers into Kubernetes Secrets. It runs as an operator in your cluster and periodically fetches secrets from external sources.

### Architecture

```
  +------------------+         +------------------+
  |  AWS Secrets     |         |  GCP Secret      |
  |  Manager         |         |  Manager         |
  +--------+---------+         +--------+---------+
           |                            |
           +----------+  +--------------+
                      |  |
              +-------+--+-------+
              | External Secrets |
              | Operator         |
              +-------+----------+
                      |
                      | Creates/Updates
                      v
              +------------------+
              | K8s Secret       |
              | (managed by ESO) |
              +------------------+
                      |
                      | Volume mount / env var
                      v
              +------------------+
              | Application Pod  |
              +------------------+
```

### Installing ESO

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace \
  --set installCRDs=true
```

### ClusterSecretStore Configuration

A ClusterSecretStore defines how ESO authenticates with the external secret provider. It is cluster-scoped, meaning any namespace can use it.

```yaml
# AWS Secrets Manager with IRSA
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets
---
# GCP Secret Manager with Workload Identity
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: gcp-secret-manager
spec:
  provider:
    gcpsm:
      projectID: my-project
      auth:
        workloadIdentity:
          clusterLocation: us-central1
          clusterName: production
          serviceAccountRef:
            name: gcp-secrets-sa
            namespace: external-secrets
---
# Azure Key Vault with Workload Identity
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: azure-key-vault
spec:
  provider:
    azurekv:
      vaultUrl: "https://my-vault.vault.azure.net"
      authType: WorkloadIdentity
      serviceAccountRef:
        name: azure-secrets-sa
        namespace: external-secrets
```

### ExternalSecret: Syncing Individual Secrets

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
    deletionPolicy: Retain
  data:
    - secretKey: username
      remoteRef:
        key: production/database
        property: username
    - secretKey: password
      remoteRef:
        key: production/database
        property: password
    - secretKey: host
      remoteRef:
        key: production/database
        property: host
    - secretKey: connection-string
      remoteRef:
        key: production/database
        property: connection_string
```

### ExternalSecret: Templating

ESO can transform secret data using Go templates:

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: database-url
  namespace: production
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: database-url
    template:
      engineVersion: v2
      data:
        DATABASE_URL: "postgresql://{{ .username }}:{{ .password }}@{{ .host }}:5432/{{ .dbname }}?sslmode=require"
  data:
    - secretKey: username
      remoteRef:
        key: production/database
        property: username
    - secretKey: password
      remoteRef:
        key: production/database
        property: password
    - secretKey: host
      remoteRef:
        key: production/database
        property: host
    - secretKey: dbname
      remoteRef:
        key: production/database
        property: dbname
```

---

## Secrets Store CSI Driver

The Secrets Store CSI Driver mounts secrets directly from a vault as files in a pod, bypassing Kubernetes Secrets entirely. The secret exists only in the pod's filesystem and the vault -- it never lands in etcd.

### Architecture Difference from ESO

```
ESO:                                    CSI Driver:
  Vault --> ESO --> K8s Secret --> Pod     Vault --> CSI Driver --> Pod Filesystem
                    (in etcd)                       (no K8s Secret)
```

### Installing the CSI Driver

```bash
helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver \
  --namespace kube-system \
  --set syncSecret.enabled=true

# Install AWS provider
k apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
```

### SecretProviderClass

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: db-secrets
  namespace: production
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "production/database"
        objectType: "secretsmanager"
        jmesPath:
          - path: username
            objectAlias: db-username
          - path: password
            objectAlias: db-password
  secretObjects:
    - secretName: db-credentials-synced
      type: Opaque
      data:
        - objectName: db-username
          key: username
        - objectName: db-password
          key: password
```

### Pod Using CSI Mounted Secrets

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api-server
  namespace: production
spec:
  serviceAccountName: app-sa
  containers:
    - name: api
      image: mycompany/api-server:3.0.0
      volumeMounts:
        - name: secrets
          mountPath: /mnt/secrets
          readOnly: true
      env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials-synced
              key: username
  volumes:
    - name: secrets
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: db-secrets
```

### ESO vs CSI Driver: When to Use Each

| Factor | ESO | Secrets Store CSI |
|--------|-----|------------------|
| Secret in etcd | Yes (K8s Secret) | Optional (only if syncSecret enabled) |
| Multiple pods share secret | Yes (via K8s Secret) | Each pod mounts independently |
| Secret refresh | Automatic (refreshInterval) | Requires pod restart or rotation |
| Template/transform | Yes (Go templates) | Limited |
| Git-friendly | ExternalSecret in Git (no plaintext) | SecretProviderClass in Git (no plaintext) |
| Vault-native rotation | Works with any rotation | Better with CSI rotation reconciler |
| Best for | Most use cases | Zero-trust (no secrets in etcd) |

**For most teams, ESO is the better choice.** It is simpler, more flexible, and works well with GitOps. Use Secrets Store CSI when your security requirements prohibit secrets from existing in etcd at all.

---

## Dynamic Secrets with HashiCorp Vault

Dynamic secrets are generated on-demand and automatically expire. Instead of a static database password that lives forever, Vault creates a temporary database user with a 1-hour TTL every time a pod requests credentials.

### Dynamic Secret Lifecycle

```
  Pod starts
    |
    v
  Request credentials from Vault
    |
    v
  Vault creates temporary DB user (TTL: 1h)
    |
    v
  Pod uses credentials for 1 hour
    |
    v
  Vault automatically revokes the user
    |
    v
  Pod requests new credentials (or renews lease)
```

### Vault Setup for Database Dynamic Secrets

```bash
# Enable database secrets engine
vault secrets enable database

# Configure PostgreSQL connection
vault write database/config/production-db \
  plugin_name=postgresql-database-plugin \
  allowed_roles="app-readonly,app-readwrite" \
  connection_url="postgresql://{{username}}:{{password}}@app-postgres.abc123.us-east-1.rds.amazonaws.com:5432/appdb?sslmode=require" \
  username="vault_admin" \
  password="vault-admin-password"

# Create a role that generates read-only credentials
vault write database/roles/app-readonly \
  db_name=production-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  revocation_statements="REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; DROP ROLE IF EXISTS \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

# Create a readwrite role
vault write database/roles/app-readwrite \
  db_name=production-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="4h"
```

### Vault Agent Sidecar for Dynamic Secrets

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "api-server"
        vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/app-readonly"
        vault.hashicorp.com/agent-inject-template-db-creds: |
          {{- with secret "database/creds/app-readonly" -}}
          export DB_USERNAME="{{ .Data.username }}"
          export DB_PASSWORD="{{ .Data.password }}"
          {{- end -}}
    spec:
      serviceAccountName: api-server
      containers:
        - name: api
          image: mycompany/api-server:3.0.0
          command:
            - /bin/sh
            - -c
            - "source /vault/secrets/db-creds && ./start-server"
```

### Vault vs Cloud Secret Managers

| Feature | HashiCorp Vault | AWS Secrets Manager | GCP Secret Manager | Azure Key Vault |
|---------|----------------|--------------------|--------------------|-----------------|
| Dynamic secrets | Yes (database, AWS, PKI) | No (static only) | No | No |
| Secret rotation | Built-in (TTL + revocation) | Lambda-based rotation | Rotation with Cloud Functions | Auto-rotation (certificates) |
| PKI/certificates | Yes (built-in CA) | Via ACM (separate service) | Via CAS | Via Key Vault certificates |
| Multi-cloud | Yes | AWS only | GCP only | Azure only |
| Self-hosted | Yes (or HCP Vault) | N/A (managed) | N/A (managed) | N/A (managed) |
| Complexity | High (operate Vault cluster) | Low | Low | Medium |
| Cost | Free (OSS) or ~$0.03/secret/month (HCP) | $0.40/secret/month | $0.06/secret version | $0.03/operation |

**Recommendation**:
- Single cloud, simple needs: Use the cloud-native secret manager with ESO
- Multi-cloud or dynamic secrets needed: Use Vault
- Small team, few secrets: Cloud-native is easiest
- Enterprise with strict compliance: Vault gives the most control

---

## Sealed Secrets: GitOps-Safe Encryption

Sealed Secrets encrypts secrets so they can be safely stored in Git. Only the Sealed Secrets controller in the cluster can decrypt them.

### How It Works

```
Developer                    Git Repo                    Cluster
    |                           |                          |
    | 1. kubeseal encrypt       |                          |
    |-------------------------->|                          |
    |   (SealedSecret YAML)     |                          |
    |                           | 2. GitOps sync           |
    |                           |------------------------->|
    |                           |   3. Controller decrypts  |
    |                           |   4. Creates K8s Secret   |
    |                           |                          |
```

### Installing Sealed Secrets

```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system

# Install kubeseal CLI
brew install kubeseal
```

### Creating a Sealed Secret

```bash
# Create a regular secret (do NOT apply it)
k create secret generic db-credentials \
  --from-literal=username=appadmin \
  --from-literal=password=super-secret-password \
  --dry-run=client -o yaml > /tmp/secret.yaml

# Seal it (encrypts with the cluster's public key)
kubeseal --format yaml < /tmp/secret.yaml > sealed-secret.yaml

# The sealed version is safe to commit to Git
cat sealed-secret.yaml
```

```yaml
# This is safe to commit to Git
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  encryptedData:
    username: AgB7w2K...long-encrypted-string...==
    password: AgCx9f3...long-encrypted-string...==
  template:
    metadata:
      name: db-credentials
      namespace: production
    type: Opaque
```

### Sealed Secrets Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| Cluster-specific encryption | Sealed Secret from cluster A cannot be decrypted in cluster B | Export and share the sealing key, or use SOPS instead |
| No rotation mechanism | Secret value stays the same until manually re-sealed | Combine with ESO for rotation |
| Key management | Losing the sealing key means losing all sealed secrets | Back up the sealing key to a secure location |

---

## SOPS: Mozilla's Alternative to Sealed Secrets

SOPS (Secrets OPerationS) encrypts YAML/JSON files using cloud KMS keys, PGP, or age. Unlike Sealed Secrets, SOPS is not Kubernetes-specific -- it encrypts files that can be decrypted by anyone with the KMS key.

### SOPS with AWS KMS

```bash
# Install SOPS
brew install sops

# Create a .sops.yaml configuration
cat > .sops.yaml << 'EOF'
creation_rules:
  - path_regex: .*secrets.*\.yaml$
    kms: arn:aws:kms:us-east-1:123456789:key/mrk-abc123
  - path_regex: .*secrets.*\.yaml$
    gcp_kms: projects/my-project/locations/global/keyRings/sops/cryptoKeys/sops-key
EOF

# Create a secret file
cat > secrets.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: production
stringData:
  username: appadmin
  password: super-secret-password
EOF

# Encrypt it
sops --encrypt secrets.yaml > secrets.enc.yaml

# The encrypted file can be committed to Git
# Argo CD / Flux can decrypt it using SOPS integration
```

### SOPS vs Sealed Secrets

| Feature | SOPS | Sealed Secrets |
|---------|------|---------------|
| Encryption backend | KMS, PGP, age | Cluster-specific RSA key |
| Multi-cluster | Same KMS key works everywhere | Different key per cluster |
| GitOps integration | Argo CD SOPS plugin, Flux SOPS | Native Kubernetes controller |
| Edit encrypted files | `sops secrets.enc.yaml` opens in editor | Must re-seal entire secret |
| Non-K8s files | Encrypts any YAML/JSON | Kubernetes Secrets only |

---

## Putting It All Together: A Complete Secrets Architecture

```
  +-------------------+
  | Developers        |
  | (kubeseal/sops)   |
  +--------+----------+
           |
           | Encrypted secrets in Git
           v
  +-------------------+
  | GitOps (Argo CD)  |
  | - SealedSecrets   |
  | - SOPS decrypt    |
  +--------+----------+
           |
           | Sync to cluster
           v
  +-------------------+        +-------------------+
  | ESO               |------->| AWS Secrets Mgr   |
  | (dynamic refresh) |        | GCP Secret Mgr    |
  +--------+----------+        | Azure Key Vault   |
           |                   +-------------------+
           | Creates K8s Secrets
           v
  +-------------------+        +-------------------+
  | Application Pods  |------->| Vault (dynamic)   |
  | - env vars        |        | - DB creds (1h)   |
  | - volume mounts   |        | - PKI certs (24h) |
  +-------------------+        +-------------------+
```

| Layer | Tool | Purpose |
|-------|------|---------|
| Git encryption | Sealed Secrets or SOPS | Safe to commit secrets to Git |
| External sync | ESO | Sync cloud secrets to K8s Secrets |
| Dynamic secrets | Vault | Short-lived credentials with auto-revocation |
| Runtime mount | Secrets Store CSI | Mount directly, bypassing etcd |
| Rotation trigger | Reloader | Restart pods when secrets change |

---

## Did You Know?

1. **GitHub scans every public commit for over 200 secret patterns** (API keys, tokens, passwords) through their Secret Scanning program. In 2024 alone, they detected and notified providers about over 15 million leaked secrets. Despite this, the median time between a secret being committed and an attacker exploiting it is under 30 minutes.

2. **HashiCorp Vault's dynamic database secrets feature creates and destroys** roughly 50 million ephemeral database credentials per day across its customer base. Each credential lives for an average of 45 minutes before automatic revocation -- compared to the industry average of 11 months for static database passwords.

3. **Kubernetes Secrets are stored in etcd in plaintext by default.** Encryption at rest was added in Kubernetes 1.13 (2018) but must be explicitly configured. A 2024 survey by Wiz found that 38% of production Kubernetes clusters still had not enabled etcd encryption, meaning anyone with access to the etcd data directory could read all secrets.

4. **The External Secrets Operator (ESO) emerged from a consolidation** of four competing projects: Godaddy's kubernetes-external-secrets, Alibaba's external-secrets, ContainerSolutions's externalsecret-operator, and AWS's secrets-store-csi-driver. The ESO project unified them under the CNCF in 2021 and is now the standard.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Treating base64 as encryption | "The secret is encoded, so it is safe" | base64 is encoding, not encryption; anyone can decode it |
| Storing secrets in ConfigMaps | Developer confusion between ConfigMap and Secret | Use Secrets (they get masked in logs and have RBAC separation) |
| Not enabling etcd encryption at rest | Not configured by default | Enable `EncryptionConfiguration` with AES-CBC or KMS provider |
| Using the same secret across all environments | "Simpler to manage one secret" | Separate secrets per environment; use ESO with environment-specific paths |
| Not monitoring secret access | "We have RBAC, that is enough" | Enable Kubernetes audit logging; alert on secret read events from unexpected sources |
| Committing plaintext secrets to Git then deleting them | "I removed it, so it is gone" | Git history preserves everything; rotate the secret immediately, use git-filter-repo to purge |
| Running Vault without HA | "It is just a dev cluster" | Vault is a critical dependency; always run HA mode (3+ replicas) in production |
| Setting ESO refreshInterval too low | "Faster sync is better" | Below 1 minute creates unnecessary API calls and costs; 5-15 minutes is usually fine |

---

## Quiz

<details>
<summary>1. Why are Kubernetes Secrets not secure by default, and what minimum steps should you take?</summary>

Kubernetes Secrets are base64-encoded, not encrypted. Anyone with `kubectl get secret` permission can decode them instantly. They are stored in etcd, which by default does not encrypt data at rest. Minimum steps: (1) Enable etcd encryption at rest using an EncryptionConfiguration with AES-CBC or a KMS provider. (2) Restrict RBAC so only necessary ServiceAccounts and users can read secrets. (3) Enable Kubernetes audit logging to track who accesses secrets. (4) Use an external secrets manager (via ESO or CSI driver) so the source of truth is not in etcd. These steps bring Kubernetes secrets from "anyone can read them" to "audited, encrypted, access-controlled."
</details>

<details>
<summary>2. What is the key architectural difference between ESO and the Secrets Store CSI Driver?</summary>

ESO creates a Kubernetes Secret in etcd that pods reference via environment variables or volume mounts. The secret exists in the cluster's etcd store and is synced periodically from the external vault. The Secrets Store CSI Driver mounts secrets directly from the vault into the pod's filesystem as a volume. By default, no Kubernetes Secret is created -- the secret only exists in the vault and in the pod's ephemeral filesystem. CSI Driver provides a stricter security posture because secrets never touch etcd, but ESO is more flexible and easier to use with standard Kubernetes patterns.
</details>

<details>
<summary>3. Explain dynamic secrets in Vault and why they are more secure than static secrets.</summary>

Dynamic secrets are generated on-demand when a pod or application requests them. For example, when a pod needs database access, Vault creates a temporary database user with a specific TTL (e.g., 1 hour). When the TTL expires, Vault automatically revokes the user. This is more secure because: (1) there is no long-lived credential to steal, (2) each pod gets unique credentials so access can be traced, (3) if a credential leaks, the blast radius is limited to the TTL window, and (4) revocation is automatic -- no human needs to remember to rotate. Static secrets, by contrast, live indefinitely, are shared across many pods, and require manual rotation.
</details>

<details>
<summary>4. When would you choose Sealed Secrets over SOPS, and vice versa?</summary>

Choose Sealed Secrets when you run a single Kubernetes cluster and want the simplest possible GitOps-safe encryption. Sealed Secrets requires no external KMS service -- the controller generates its own encryption keys. Choose SOPS when you have multiple clusters (same KMS key works everywhere), when you need to encrypt non-Kubernetes files, or when you want to edit encrypted files in place (`sops edit`). SOPS is also better for multi-cloud environments because it supports AWS KMS, GCP KMS, Azure Key Vault, PGP, and age as encryption backends. Sealed Secrets is simpler; SOPS is more flexible.
</details>

<details>
<summary>5. Why should you set ESO's refreshInterval to 5-15 minutes instead of 30 seconds?</summary>

Every refresh interval, ESO calls the cloud secret manager API to check for changes. At 30 seconds with 100 ExternalSecrets, that is 200 API calls per minute, or 288,000 per day. Cloud secret manager APIs charge per-request (AWS: $0.05 per 10,000 calls). More importantly, aggressive polling can hit rate limits, causing ESO to fail and secrets to become stale. A 5-15 minute interval is sufficient for most use cases because secret rotations are planned events, not emergencies. For immediate propagation after rotation, use push-based notification (CloudWatch Event triggering a webhook) rather than faster polling.
</details>

<details>
<summary>6. A developer committed a database password to Git and then deleted it in the next commit. Is the secret safe?</summary>

No. Git stores the complete history of every file change. The secret exists in the Git history and can be recovered by anyone with repository access using `git log --all --full-history` or tools like truffleHog and GitLeaks. The correct response is: (1) rotate the secret immediately -- generate a new password and update the database, (2) use `git-filter-repo` or BFG Repo Cleaner to purge the secret from history, (3) force-push the cleaned history, and (4) ensure all clones are updated. Prevention is better: use pre-commit hooks with detect-secrets or gitleaks to block secret commits before they happen.
</details>

---

## Hands-On Exercise: Multi-Layer Secrets Management

### Setup

```bash
# Create kind cluster
kind create cluster --name secrets-lab

# Install ESO
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace \
  --set installCRDs=true
k wait --for=condition=ready pod -l app.kubernetes.io/name=external-secrets \
  --namespace external-secrets --timeout=120s

# Install Sealed Secrets controller
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system
k wait --for=condition=ready pod -l app.kubernetes.io/name=sealed-secrets \
  --namespace kube-system --timeout=120s
```

### Task 1: Create and Seal a Secret

Use kubeseal to encrypt a secret that is safe to store in Git.

<details>
<summary>Solution</summary>

```bash
# Install kubeseal CLI if not present
# brew install kubeseal  # or download from GitHub releases

# Create a secret manifest (NOT applied to cluster)
k create secret generic app-secrets \
  --namespace default \
  --from-literal=api-key=sk-live-abc123def456 \
  --from-literal=webhook-secret=whsec-xyz789 \
  --dry-run=client -o yaml > /tmp/plain-secret.yaml

# Seal the secret
kubeseal --format yaml \
  --controller-name sealed-secrets \
  --controller-namespace kube-system \
  < /tmp/plain-secret.yaml > /tmp/sealed-secret.yaml

# Verify the sealed version does not contain plaintext
echo "=== Sealed Secret (safe to commit) ==="
cat /tmp/sealed-secret.yaml

# Apply the sealed secret
k apply -f /tmp/sealed-secret.yaml

# Verify the controller created the K8s Secret
sleep 5
k get secret app-secrets
k get secret app-secrets -o jsonpath='{.data.api-key}' | base64 -d
echo ""
```
</details>

### Task 2: Set Up a Fake Secret Store with ESO

Since we do not have a real cloud provider, use ESO's Fake provider to demonstrate the workflow.

<details>
<summary>Solution</summary>

```yaml
# Fake SecretStore (for lab only -- uses in-cluster data)
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: fake-store
  namespace: default
spec:
  provider:
    fake:
      data:
        - key: "/production/database"
          value: '{"username":"app_user","password":"dynamic-pass-892","host":"db.example.com","port":"5432"}'
        - key: "/production/redis"
          value: '{"host":"redis.example.com","port":"6379","auth_token":"redis-token-456"}'
---
# ExternalSecret that syncs from the fake store
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: database-creds
  namespace: default
spec:
  refreshInterval: 1m
  secretStoreRef:
    name: fake-store
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: /production/database
        property: username
    - secretKey: password
      remoteRef:
        key: /production/database
        property: password
    - secretKey: host
      remoteRef:
        key: /production/database
        property: host
```

```bash
k apply -f /tmp/eso-fake.yaml

# Wait for sync
sleep 10

# Verify ESO created the secret
k get externalsecret database-creds
k get secret db-credentials
k get secret db-credentials -o jsonpath='{.data.password}' | base64 -d
echo ""
```
</details>

### Task 3: Use ESO Templates to Generate a Connection String

Create an ExternalSecret that templates multiple fields into a single connection string.

<details>
<summary>Solution</summary>

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: database-url
  namespace: default
spec:
  refreshInterval: 1m
  secretStoreRef:
    name: fake-store
    kind: SecretStore
  target:
    name: database-url
    template:
      engineVersion: v2
      data:
        DATABASE_URL: "postgresql://{{ .username }}:{{ .password }}@{{ .host }}:{{ .port }}/appdb?sslmode=require"
  data:
    - secretKey: username
      remoteRef:
        key: /production/database
        property: username
    - secretKey: password
      remoteRef:
        key: /production/database
        property: password
    - secretKey: host
      remoteRef:
        key: /production/database
        property: host
    - secretKey: port
      remoteRef:
        key: /production/database
        property: port
```

```bash
k apply -f /tmp/eso-template.yaml
sleep 10

k get secret database-url -o jsonpath='{.data.DATABASE_URL}' | base64 -d
echo ""
# Should output: postgresql://app_user:dynamic-pass-892@db.example.com:5432/appdb?sslmode=require
```
</details>

### Task 4: Deploy a Pod That Uses the Synced Secret

Deploy a pod that reads the ESO-managed secret as an environment variable.

<details>
<summary>Solution</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-consumer
  namespace: default
spec:
  restartPolicy: Never
  containers:
    - name: app
      image: busybox:1.36
      command:
        - /bin/sh
        - -c
        - |
          echo "=== Secret Consumer ==="
          echo "DB Username: $DB_USERNAME"
          echo "DB Host: $DB_HOST"
          echo "DB Password length: $(echo -n $DB_PASSWORD | wc -c) characters"
          echo "Connection String: $DATABASE_URL"
          echo "=== Sealed Secret ==="
          echo "API Key: $API_KEY"
          echo "=== Done ==="
      env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: host
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-url
              key: DATABASE_URL
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: api-key
```

```bash
k apply -f /tmp/secret-consumer.yaml
k wait --for=condition=ready pod/secret-consumer --timeout=30s
sleep 3
k logs secret-consumer
```
</details>

### Task 5: Verify Secret Status and Health

Check the status of all ExternalSecrets and SealedSecrets.

<details>
<summary>Solution</summary>

```bash
echo "=== ExternalSecret Status ==="
k get externalsecrets -o wide

echo ""
echo "=== SealedSecret Status ==="
k get sealedsecrets -o wide

echo ""
echo "=== All Secrets (non-system) ==="
k get secrets --field-selector type!=kubernetes.io/service-account-token

echo ""
echo "=== ESO SecretStore Status ==="
k get secretstores -o wide
```
</details>

### Success Criteria

- [ ] SealedSecret is applied and the controller creates a K8s Secret
- [ ] ESO fake SecretStore syncs secrets to K8s Secrets
- [ ] Templated ExternalSecret generates a valid connection string
- [ ] Pod reads secrets from both Sealed Secrets and ESO
- [ ] All ExternalSecrets show `SecretSynced` status

### Cleanup

```bash
kind delete cluster --name secrets-lab
```

---

**Next Module**: [Module 9.9: Cloud-Native API Gateways & WAF](module-9.9-api-gateways/) -- Learn how cloud API gateways compare to Kubernetes Gateway API, how to integrate WAF protection, and how to handle OAuth2/OIDC proxying for your services.
