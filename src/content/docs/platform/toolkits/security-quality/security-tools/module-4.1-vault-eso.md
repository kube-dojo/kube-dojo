---
title: "Module 4.1: Vault & External Secrets"
slug: platform/toolkits/security-quality/security-tools/module-4.1-vault-eso
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 minutes

## Overview

Hardcoded secrets in Git are a security incident waiting to happen. This module covers HashiCorp Vault for enterprise secrets management and External Secrets Operator (ESO) for syncing secrets from external providers into Kubernetes.

**What You'll Learn**:
- Vault architecture and secrets engines
- External Secrets Operator patterns
- Multi-tenant secrets management
- Secret rotation strategies

**Prerequisites**:
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/)
- Kubernetes Secrets basics
- RBAC concepts

---

## Why This Module Matters

Every production breach post-mortem includes "we found credentials in..." somewhere. Secrets sprawl is inevitable without proper tooling. Vault and ESO provide the infrastructure to manage secrets at scale—centralized storage, automatic rotation, audit trails, and least-privilege access.

> 💡 **Did You Know?** HashiCorp Vault was open-sourced in 2015 and now manages secrets for most Fortune 500 companies. Its design philosophy of "secrets as a service" fundamentally changed how organizations think about credential management.

---

## The Secrets Problem

```
THE SECRETS SPRAWL PROBLEM
════════════════════════════════════════════════════════════════════

Where secrets end up without proper management:

┌─────────────────────────────────────────────────────────────────┐
│                     SECRETS SPRAWL                               │
│                                                                  │
│   .env files ───────────┐                                       │
│   Git repos ────────────┤                                       │
│   CI/CD variables ──────┼───▶ 😱 UNCONTROLLED ACCESS            │
│   ConfigMaps ───────────┤         No audit trail                │
│   Shell history ────────┤         No rotation                   │
│   Slack messages ───────┘         Shared passwords              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

With Vault + ESO:

┌─────────────────────────────────────────────────────────────────┐
│                     CENTRALIZED SECRETS                          │
│                                                                  │
│                    ┌─────────────┐                              │
│   App A ──────────▶│             │                              │
│   App B ──────────▶│    VAULT    │◀── Audit every access        │
│   App C ──────────▶│             │◀── Automatic rotation        │
│   CI/CD ──────────▶│             │◀── Least privilege           │
│                    └─────────────┘                              │
│                          │                                       │
│                          ▼                                       │
│                    ┌─────────────┐                              │
│                    │     ESO     │──▶ Kubernetes Secrets        │
│                    └─────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## HashiCorp Vault

### Architecture

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

### Key Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Secrets Engine** | Backend that stores/generates secrets | KV, Database, PKI, AWS |
| **Auth Method** | How clients authenticate | Kubernetes, OIDC, LDAP |
| **Policy** | What secrets a client can access | Read `secret/data/app/*` |
| **Token** | Credential returned after auth | Used for subsequent requests |
| **Lease** | TTL on dynamic secrets | Database creds expire in 1h |

### Secrets Engines Deep Dive

```
SECRETS ENGINE TYPES
════════════════════════════════════════════════════════════════════

KV (Key-Value) - Static Secrets
─────────────────────────────────────────────────────────────────
Use: API keys, passwords, config that doesn't change often
Features: Versioning, soft delete, metadata

vault kv put secret/myapp/config \
  api_key="sk-xxx" \
  db_password="hunter2"

vault kv get secret/myapp/config


Database - Dynamic Secrets
─────────────────────────────────────────────────────────────────
Use: Database credentials with automatic rotation
Features: Per-connection creds, TTL, automatic revocation

# Configure database connection
vault write database/config/postgres \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@postgres:5432" \
  allowed_roles="readonly" \
  username="vault" \
  password="vault-password"

# Create role
vault write database/roles/readonly \
  db_name=postgres \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

# Get credentials (new user each time!)
vault read database/creds/readonly


PKI - Certificate Authority
─────────────────────────────────────────────────────────────────
Use: TLS certificates for services
Features: Short-lived certs, automatic renewal

vault write pki/issue/web-certs \
  common_name="api.example.com" \
  ttl="720h"
```

> 💡 **Did You Know?** Dynamic database secrets are Vault's killer feature. Instead of one shared database password, each application instance gets unique credentials that automatically expire. When a credential leaks, you know exactly which instance was compromised.

### Vault Policies

```hcl
# policies/app-readonly.hcl
# Read-only access to app secrets

path "secret/data/myapp/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/myapp/*" {
  capabilities = ["list"]
}

# Deny access to admin secrets
path "secret/data/admin/*" {
  capabilities = ["deny"]
}
```

```bash
# Apply policy
vault policy write app-readonly policies/app-readonly.hcl

# Create token with policy
vault token create -policy=app-readonly
```

### Kubernetes Authentication

```bash
# Enable Kubernetes auth
vault auth enable kubernetes

# Configure it to talk to K8s API
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Create role for app pods
vault write auth/kubernetes/role/myapp \
  bound_service_account_names=myapp \
  bound_service_account_namespaces=production \
  policies=app-readonly \
  ttl=1h
```

---

## External Secrets Operator (ESO)

### Why ESO?

Vault is great, but applications expect Kubernetes Secrets. ESO bridges the gap:

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

### Installation

```bash
# Install ESO via Helm
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

helm install external-secrets external-secrets/external-secrets \
  -n external-secrets \
  --create-namespace \
  --set installCRDs=true
```

### SecretStore vs ClusterSecretStore

```yaml
# SecretStore - namespaced
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: production  # Only usable in this namespace
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
  name: vault-backend  # No namespace - usable from any namespace
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
```

### ExternalSecret Examples

```yaml
# Basic secret sync
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h  # How often to sync
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-credentials  # K8s Secret name
    creationPolicy: Owner       # ESO owns the Secret
  data:
  - secretKey: username         # Key in K8s Secret
    remoteRef:
      key: secret/data/production/database
      property: username        # Key in Vault
  - secretKey: password
    remoteRef:
      key: secret/data/production/database
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
      key: secret/data/production/app-config
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
      key: secret/data/production/database
      property: username
  - secretKey: password
    remoteRef:
      key: secret/data/production/database
      property: password
```

> 💡 **Did You Know?** ESO supports 20+ secret providers including AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, and even 1Password. You can migrate between cloud providers without changing your application code—just update the SecretStore.

---

## Multi-Tenant Patterns

### Namespace Isolation

```
MULTI-TENANT SECRETS ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                         VAULT                                    │
│                                                                  │
│  secret/                                                         │
│  ├── team-a/                                                    │
│  │   ├── app1/           ◀── team-a-policy                     │
│  │   └── app2/                                                  │
│  ├── team-b/                                                    │
│  │   ├── api/            ◀── team-b-policy                     │
│  │   └── worker/                                                │
│  └── shared/                                                    │
│      └── certificates/   ◀── shared-readonly                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       KUBERNETES                                 │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Namespace:      │  │ Namespace:      │                      │
│  │ team-a          │  │ team-b          │                      │
│  │                 │  │                 │                      │
│  │ SecretStore:    │  │ SecretStore:    │                      │
│  │ vault-team-a    │  │ vault-team-b    │                      │
│  │ (can only read  │  │ (can only read  │                      │
│  │  team-a/*)      │  │  team-b/*)      │                      │
│  └─────────────────┘  └─────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```yaml
# Team A's SecretStore
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
          role: "team-a"  # Vault role with team-a-policy
          serviceAccountRef:
            name: "vault-auth"
```

### Shared Secrets Pattern

```yaml
# ClusterSecretStore for shared secrets
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: shared-secrets
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "shared-readonly"
          serviceAccountRef:
            name: "external-secrets"
            namespace: "external-secrets"
  conditions:
  # Only allow access from specific namespaces
  - namespaces:
    - production
    - staging
---
# Any namespace can use shared TLS certs
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: wildcard-tls
  namespace: production
spec:
  refreshInterval: 24h
  secretStoreRef:
    name: shared-secrets
    kind: ClusterSecretStore
  target:
    name: wildcard-tls
    template:
      type: kubernetes.io/tls
  data:
  - secretKey: tls.crt
    remoteRef:
      key: secret/data/shared/certificates/wildcard
      property: certificate
  - secretKey: tls.key
    remoteRef:
      key: secret/data/shared/certificates/wildcard
      property: private_key
```

---

## Secret Rotation

### Automatic Rotation with Vault

```bash
# Enable database secrets engine
vault secrets enable database

# Configure PostgreSQL
vault write database/config/mydb \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@postgres:5432/mydb" \
  allowed_roles="app" \
  username="vault_admin" \
  password="admin_password"

# Create role with short TTL
vault write database/roles/app \
  db_name=mydb \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"
```

### ESO Refresh and Push

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: rotating-db-creds
spec:
  refreshInterval: 15m  # Sync every 15 minutes
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
    deletionPolicy: Retain  # Keep secret if ExternalSecret deleted
  data:
  - secretKey: username
    remoteRef:
      key: database/creds/app  # Dynamic secret path
      property: username
  - secretKey: password
    remoteRef:
      key: database/creds/app
      property: password
```

### Handling Rotation in Applications

```yaml
# Deployment that restarts on secret change
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  annotations:
    # Reloader watches for secret changes
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

```bash
# Install Reloader for automatic restarts
helm repo add stakater https://stakater.github.io/stakater-charts
helm install reloader stakater/reloader -n kube-system
```

> 💡 **Did You Know?** The Stakater Reloader watches Secrets and ConfigMaps and automatically triggers rolling restarts when they change. This solves the "I updated the secret but pods still have old values" problem without requiring application code changes.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Storing Vault token in Git | Token exposed, full Vault access | Use Kubernetes auth method |
| Long refresh intervals | Secrets out of sync for hours | Use 5-15m for critical secrets |
| No audit logging | Can't track who accessed what | Enable Vault audit device |
| Single Vault token for all apps | Blast radius too large | Per-app policies and tokens |
| Forgetting to rotate root creds | Vault DB admin password never changes | Use `vault write -force database/rotate-root/mydb` |
| Not versioning KV secrets | Can't rollback bad changes | Use KV v2, check versions |

---

## War Story: The Great Secret Migration

*A team migrated 200+ Kubernetes Secrets to Vault+ESO over a weekend. Monday morning, half the apps were down.*

**What went wrong**: They deleted the old Kubernetes Secrets before verifying ESO had synced successfully. Several ExternalSecrets had typos in the `remoteRef.key` paths.

**The fix**:
1. Always run ESO alongside existing secrets first
2. Verify each ExternalSecret shows `SecretSynced: True`
3. Only delete old secrets after apps confirm they're working
4. Use `kubectl get externalsecrets -A` to check sync status

```bash
# Verify all ExternalSecrets are synced
kubectl get externalsecrets -A -o custom-columns=\
'NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.conditions[0].reason'
```

---

## Quiz

### Question 1
What's the advantage of Vault's dynamic database secrets over static passwords?

<details>
<summary>Show Answer</summary>

Dynamic secrets:
1. **Unique per request** - Each application instance gets different credentials
2. **Auto-expire** - Credentials have TTL, automatically revoked
3. **Audit trail** - Know exactly which credential was used where
4. **Breach isolation** - If leaked, you know which instance was compromised
5. **No shared secrets** - No "one password everyone knows" problem

</details>

### Question 2
When should you use ClusterSecretStore vs SecretStore?

<details>
<summary>Show Answer</summary>

**SecretStore** (namespaced):
- Team/application specific secrets
- Different auth per namespace
- Isolation between tenants

**ClusterSecretStore** (cluster-wide):
- Shared secrets (TLS certs, CA bundles)
- Central secret management
- Use with `conditions.namespaces` to limit access

</details>

### Question 3
An ExternalSecret shows `SecretSyncedError`. How do you debug it?

<details>
<summary>Show Answer</summary>

```bash
# 1. Check ExternalSecret status
kubectl describe externalsecret <name>
# Look at Status.Conditions and Events

# 2. Check ESO controller logs
kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets

# 3. Verify SecretStore connection
kubectl describe secretstore <store-name>

# 4. Common causes:
# - Wrong Vault path (secret/myapp vs secret/data/myapp for KV v2)
# - Auth issues (service account, role binding)
# - Network (can ESO reach Vault?)
# - Policy (does Vault policy allow read?)
```

</details>

---

## Hands-On Exercise

### Objective
Set up Vault with Kubernetes auth and sync secrets using ESO.

### Environment Setup

```bash
# Start local Vault in dev mode
docker run -d --name vault \
  -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=root' \
  -e 'VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200' \
  hashicorp/vault:latest

export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='root'

# Create test secrets
vault kv put secret/myapp/config \
  database_url="postgresql://user:pass@db:5432/mydb" \
  api_key="sk-test-12345"
```

### Tasks

1. **Install ESO** in your cluster:
   ```bash
   helm install external-secrets external-secrets/external-secrets \
     -n external-secrets --create-namespace
   ```

2. **Create SecretStore** pointing to local Vault:
   ```yaml
   # Use token auth for dev (not for production!)
   apiVersion: external-secrets.io/v1beta1
   kind: SecretStore
   metadata:
     name: vault-dev
   spec:
     provider:
       vault:
         server: "http://host.docker.internal:8200"  # or your Vault URL
         path: "secret"
         version: "v2"
         auth:
           tokenSecretRef:
             name: vault-token
             key: token
   ```

3. **Create ExternalSecret** to sync `myapp/config`:
   ```yaml
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
         key: secret/data/myapp/config
   ```

4. **Verify** the Kubernetes Secret was created:
   ```bash
   kubectl get secret myapp-config -o yaml
   ```

### Success Criteria
- [ ] ESO controller running in `external-secrets` namespace
- [ ] SecretStore shows `Valid: True`
- [ ] ExternalSecret shows `SecretSynced: True`
- [ ] Kubernetes Secret contains both `database_url` and `api_key`
- [ ] Values match what's in Vault

### Bonus Challenge
Update the secret in Vault and verify ESO syncs the change within the refresh interval.

---

## Further Reading

- [Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [External Secrets Operator Docs](https://external-secrets.io/)
- [Vault Best Practices](https://developer.hashicorp.com/vault/tutorials/operations/production-hardening)

---

## Next Module

Continue to [Module 4.2: OPA & Gatekeeper](../module-4.2-opa-gatekeeper/) to learn policy-as-code for Kubernetes admission control.

---

*"The only secure secret is the one that doesn't exist. For everything else, there's Vault."*
