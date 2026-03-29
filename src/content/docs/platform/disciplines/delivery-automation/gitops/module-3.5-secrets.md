---
title: "Module 3.5: Secrets in GitOps"
slug: platform/disciplines/delivery-automation/gitops/module-3.5-secrets
sidebar:
  order: 6
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 35-40 min

## Prerequisites

Before starting this module:
- **Required**: [Module 3.1: What is GitOps?](module-3.1-what-is-gitops/) — GitOps fundamentals
- **Required**: [Security Principles Track](../../foundations/security-principles/) — Security fundamentals
- **Recommended**: Understanding of Kubernetes Secrets
- **Helpful**: Basic cryptography concepts (encryption, keys)

---

## Why This Module Matters

GitOps says: "Everything in Git."

Security says: "Never commit secrets."

**This is the GitOps secrets problem.**

If you can't put secrets in Git, how do you manage them with GitOps? This isn't a minor inconvenience — it's a fundamental challenge that every GitOps adoption must solve.

Get it wrong:
- Secrets in Git history (forever)
- Security breaches
- Compliance violations
- Lost credentials

Get it right:
- Secrets managed declaratively
- Full GitOps workflow preserved
- Audit trail maintained
- Security enhanced

This module shows you the patterns and tools for handling secrets in GitOps.

---

## The Secrets Problem

### Why You Can't Just Commit Secrets

```yaml
# DON'T DO THIS - Ever
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
type: Opaque
data:
  username: YWRtaW4=      # base64 of "admin"
  password: cGFzc3dvcmQ=  # base64 of "password123"
```

**Problems:**

1. **Git history is forever**: Even if you delete, it's in history
2. **Base64 is not encryption**: Anyone can decode it
3. **Repository access = secret access**: Everyone with repo access sees secrets
4. **Leaked to forks**: Forks get the secrets too
5. **Compliance violations**: Many regulations forbid this

### The GitOps Secret Dilemma

```
┌─────────────────────────────────────────────────────────────┐
│                    GitOps Promise                            │
│                                                              │
│   "Git is the source of truth for all resources"            │
└─────────────────────────────────────────────────────────────┘
                              vs
┌─────────────────────────────────────────────────────────────┐
│                   Security Requirement                       │
│                                                              │
│   "Never store plaintext secrets in version control"        │
└─────────────────────────────────────────────────────────────┘

How do we reconcile these?
```

---

## Solution Categories

Three main approaches to GitOps secrets:

### 1. Encrypt Secrets in Git

Store encrypted secrets in Git. Decrypt at deploy time.

**Tools**: Sealed Secrets, SOPS, git-crypt

```
Git Repo                    Cluster
   │                           │
   │  Encrypted Secret         │
   │  (safe to commit)         │
   │           │               │
   │           ▼               │
   │      GitOps Agent         │
   │           │               │
   │           ▼               │
   │      Decrypt              │
   │           │               │
   │           ▼               │
   │      Kubernetes Secret    │
   │      (plaintext)          │
```

### 2. Reference External Secrets

Store secrets in external manager. Reference them in Git.

**Tools**: External Secrets Operator, Secrets Store CSI Driver

```
Git Repo                    External Store         Cluster
   │                            │                     │
   │  Secret Reference          │                     │
   │  (not actual secret)       │                     │
   │           │                │                     │
   │           ▼                │                     │
   │      GitOps Agent ─────────┼──── Fetch ──────────▶
   │                            │                     │
   │                            ▼                     │
   │                       Actual Secret              │
   │                            │                     │
   │                            ▼                     │
   │                    Kubernetes Secret             │
```

### 3. Inject at Runtime

Don't put secrets in Kubernetes at all. Inject directly to pods.

**Tools**: Vault Agent, Secrets Store CSI Driver (mounted)

```
Git Repo                    Vault                  Pod
   │                          │                     │
   │  Pod spec with           │                     │
   │  Vault annotations       │                     │
   │           │              │                     │
   │           ▼              │                     │
   │      Pod created ────────┼───── Auth ─────────▶
   │                          │                     │
   │                          ▼                     │
   │                    Secret injected             │
   │                    into pod filesystem         │
```

---

## Pattern 1: Sealed Secrets

The most GitOps-native solution. Secrets encrypted before Git, decrypted in cluster.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                      Encryption Flow                         │
│                                                              │
│   1. Create regular Kubernetes Secret                        │
│   2. Use kubeseal CLI to encrypt with cluster's public key  │
│   3. Commit SealedSecret to Git                              │
│   4. Sealed Secrets controller decrypts in cluster          │
│   5. Regular Secret created for pods to use                 │
└─────────────────────────────────────────────────────────────┘

Developer                Git                   Cluster
    │                     │                       │
    │ kubeseal           │                       │
    │─────────▶          │                       │
    │                     │                       │
    │ SealedSecret       │                       │
    │──────────────────▶ │                       │
    │                     │                       │
    │                     │  GitOps sync         │
    │                     │──────────────────────▶│
    │                     │                       │
    │                     │     Controller        │
    │                     │     decrypts          │
    │                     │         │             │
    │                     │         ▼             │
    │                     │     K8s Secret        │
```

### Installing Sealed Secrets

```bash
# Add controller to cluster
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Install kubeseal CLI
brew install kubeseal  # macOS
# or download from GitHub releases
```

### Creating a Sealed Secret

```bash
# 1. Create regular secret (don't commit this!)
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=supersecret \
  --dry-run=client -o yaml > secret.yaml

# 2. Seal it
kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# 3. Delete plaintext
rm secret.yaml

# 4. Commit sealed secret
cat sealed-secret.yaml
```

### Sealed Secret YAML

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-creds
  namespace: default
spec:
  encryptedData:
    # These are encrypted - safe to commit
    username: AgBy8hC7...long encrypted string...
    password: AgCtr4Hx...long encrypted string...
  template:
    metadata:
      name: db-creds
    type: Opaque
```

### Pros and Cons

**Pros:**
- True GitOps: encrypted secrets in Git
- Simple workflow
- Controller handles decryption
- Works with any GitOps tool

**Cons:**
- Cluster-specific encryption (can't share between clusters)
- Key management (backup the sealing key!)
- Rotation requires re-sealing

---

## Pattern 2: SOPS (Secrets OPerationS)

Encrypt specific values within YAML files, not entire files.

### How It Works

```yaml
# Original file (secret-values.yaml)
database:
  username: admin
  password: supersecret  # This needs encryption

# After SOPS encryption
database:
  username: admin
  password: ENC[AES256_GCM,data:...,type:str]

sops:
  kms:
    - arn: arn:aws:kms:...
      created_at: "2024-01-15T10:00:00Z"
      enc: ...
```

### Using SOPS

```bash
# Install
brew install sops

# Configure with AWS KMS (or GCP KMS, Azure Key Vault, PGP)
export SOPS_KMS_ARN="arn:aws:kms:us-east-1:123456789:key/abc-123"

# Encrypt a file
sops -e secrets.yaml > secrets.enc.yaml

# Decrypt (for viewing/editing)
sops -d secrets.enc.yaml

# Edit in place (decrypts, opens editor, re-encrypts)
sops secrets.enc.yaml
```

### SOPS with GitOps

**Flux native SOPS support:**

```yaml
# Kustomization with SOPS decryption
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
spec:
  decryption:
    provider: sops
    secretRef:
      name: sops-age  # Age key for decryption
```

**ArgoCD with SOPS plugin:**

```yaml
# argocd-cm ConfigMap
data:
  configManagementPlugins: |
    - name: kustomize-sops
      generate:
        command: ["sh", "-c"]
        args: ["kustomize build . | sops -d /dev/stdin"]
```

### Pros and Cons

**Pros:**
- Partial encryption (see structure, hide values)
- Multi-cloud KMS support
- Can work across clusters
- Mature, widely used

**Cons:**
- Requires KMS access from cluster
- More complex setup
- GitOps tool integration needed

---

## Pattern 3: External Secrets Operator

Don't store secrets in Git at all. Reference them.

### How It Works

```yaml
# This goes in Git - just a reference
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: db-creds  # K8s Secret to create
  data:
    - secretKey: username
      remoteRef:
        key: database/creds
        property: username
    - secretKey: password
      remoteRef:
        key: database/creds
        property: password
```

```
Git                     Operator            Vault           Cluster
 │                          │                 │                │
 │  ExternalSecret          │                 │                │
 │  (reference)             │                 │                │
 │───────────────────────▶ GitOps syncs       │                │
 │                          │                 │                │
 │                          │  Fetch secret   │                │
 │                          │────────────────▶│                │
 │                          │                 │                │
 │                          │◀────────────────│                │
 │                          │  Secret data    │                │
 │                          │                 │                │
 │                          │  Create K8s Secret               │
 │                          │────────────────────────────────▶│
```

### Supported Backends

External Secrets Operator supports:
- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager
- HashiCorp Vault
- 1Password
- And many more

### Setting Up ESO

```bash
# Install ESO
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets

# Create SecretStore (example: AWS Secrets Manager)
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
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
            name: external-secrets
            namespace: external-secrets
EOF
```

### Pros and Cons

**Pros:**
- No secrets in Git at all
- Central secret management
- Automatic rotation
- Multi-cluster friendly

**Cons:**
- Dependency on external system
- More moving parts
- Requires secret store setup

---

## Try This: Choose Your Approach

Answer these questions to help choose:

```
1. Do you already have a secrets manager (Vault, AWS SM, etc.)?
   [ ] Yes → Consider External Secrets Operator
   [ ] No → Sealed Secrets or SOPS

2. How many clusters do you have?
   [ ] One → Sealed Secrets is simple
   [ ] Many → SOPS or External Secrets (shareable)

3. Who manages secrets?
   [ ] Same team as infrastructure → Any approach
   [ ] Security team separately → External Secrets (separation)

4. Do you need secrets in Git history for audit?
   [ ] Yes → Sealed Secrets or SOPS
   [ ] No → External Secrets

5. Cloud provider preference?
   [ ] AWS/GCP/Azure → Use their KMS with SOPS
   [ ] Multi-cloud → Vault + External Secrets
   [ ] On-prem → Sealed Secrets or Vault
```

---

## Did You Know?

1. **GitHub scans for secrets** in commits and will alert you (and potentially revoke them if from known providers). This is a last-resort safety net, not a security strategy.

2. **The Sealed Secrets controller key is the crown jewel**. If you lose it, you lose all secrets. If it's leaked, all encrypted secrets are compromised. Back it up securely.

3. **SOPS was created by Mozilla** for their internal infrastructure. It's designed for GitOps-style workflows from the start.

4. **GitGuardian's 2023 report** found over 10 million secrets exposed in public GitHub commits that year alone. The most common: API keys, database credentials, and cloud provider secrets. Prevention beats detection every time.

---

## War Story: The Secret That Lived in Git Forever

A team I worked with made a common mistake:

**The Incident:**

Day 1: New developer commits a Secret with database credentials
Day 2: Reviewer catches it, asks to remove
Day 3: Developer deletes the file and commits
Day 30: Security audit finds the secret in git history

```bash
# The secret is still there!
git log --all --full-history -- secrets/database.yaml
git show abc123:secrets/database.yaml  # There it is
```

**The Damage:**

- Credentials had to be rotated immediately
- Database briefly inaccessible during rotation
- Git history couldn't be easily cleaned (forks, clones, backups)
- Compliance audit failed

**The Fix (Painful):**

1. Rotate all exposed credentials
2. BFG Repo Cleaner to rewrite history
3. Force push (broke everyone's clones)
4. Notify all fork owners
5. Invalidate CI caches

**Prevention:**

```yaml
# Pre-commit hook (.pre-commit-config.yaml)
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

# GitHub secret scanning
# (enabled by default on public repos)

# Sealed Secrets for all K8s secrets
# (never commit plain Secrets)
```

**Lesson:** The only safe approach is preventing secrets from ever entering Git. All other solutions are damage control.

---

## Secret Rotation

Managing secrets isn't just about storage — rotation is critical.

### Why Rotate?

- Credentials may be compromised
- Compliance requirements
- Employee departures
- Limiting exposure time

### Rotation with Sealed Secrets

```bash
# Manual rotation process
# 1. Create new secret
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=NEW_PASSWORD \
  --dry-run=client -o yaml > secret.yaml

# 2. Seal it
kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# 3. Commit and push
git add sealed-secret.yaml
git commit -m "Rotate database credentials"
git push

# 4. GitOps syncs, pods get new secret
# (may need pod restart depending on how secrets are consumed)
```

### Rotation with External Secrets

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
spec:
  refreshInterval: 1h  # Automatically fetches new values
  # ... rest of spec
```

Rotation happens in the external store. ESO picks up changes automatically.

### Rotation Patterns

| Pattern | Pros | Cons |
|---------|------|------|
| **Manual rotation** | Full control | Human effort, error-prone |
| **Scheduled rotation** | Regular, predictable | May rotate unnecessarily |
| **Event-driven** | Rotate when needed | Needs triggering mechanism |
| **Automatic (ESO)** | Hands-off | Depends on external store |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Committing plain secrets | In history forever | Use Sealed Secrets, SOPS, or ESO |
| Base64 = encryption | False security | Base64 is encoding, not encryption |
| Not backing up sealing key | Lose all secrets if lost | Secure backup of controller key |
| Same secrets all environments | One compromise = all compromised | Different secrets per environment |
| No rotation process | Stale, potentially leaked secrets | Implement rotation |
| Secrets in ConfigMaps | "It's not really a secret" | If sensitive, use Secrets |

---

## Quiz: Check Your Understanding

### Question 1
Why is base64 encoding insufficient for storing secrets in Git?

<details>
<summary>Show Answer</summary>

Base64 is **encoding, not encryption**.

```bash
# Anyone can decode it instantly
echo "c3VwZXJzZWNyZXQ=" | base64 -d
# Output: supersecret
```

**Base64:**
- Transforms data to printable characters
- No key required to reverse
- Provides zero security
- Required by Kubernetes for Secret data field

**Encryption:**
- Requires a key to decrypt
- Computationally hard to reverse without key
- Provides actual security

Kubernetes uses base64 because Secret data might be binary. It's not trying to hide the value.

</details>

### Question 2
You have 5 clusters and want to share the same encrypted secrets across all of them. Which approach works best?

<details>
<summary>Show Answer</summary>

**SOPS or External Secrets Operator** — not Sealed Secrets.

**Why not Sealed Secrets?**
- Sealed Secrets encrypts with a cluster-specific public key
- Each cluster has its own key pair
- A secret sealed for Cluster A can't be unsealed in Cluster B
- You'd have to seal 5 times for 5 clusters

**SOPS works because:**
- Encrypts with a shared key (KMS, PGP)
- Any cluster with KMS access can decrypt
- Same encrypted file works everywhere

**External Secrets works because:**
- Secret stored once in central manager (Vault, AWS SM)
- Each cluster fetches from same source
- Change once, propagates everywhere

**Sealed Secrets is great for:**
- Single cluster
- When you want cluster-specific secrets
- Simplicity over sharing

</details>

### Question 3
Your application loads secrets at startup and caches them. You rotate a secret using External Secrets. What happens?

<details>
<summary>Show Answer</summary>

**The application still has the old secret.**

External Secrets Operator:
1. Fetches new secret from backend ✓
2. Updates Kubernetes Secret ✓
3. Application doesn't know about update ✗

**Solutions:**

1. **Restart pods** (simple but disruptive)
   ```bash
   kubectl rollout restart deployment my-app
   ```

2. **Stakater Reloader** (automatic pod restart on Secret change)
   ```yaml
   metadata:
     annotations:
       reloader.stakater.com/auto: "true"
   ```

3. **Watch for Secret changes** (app-level)
   ```go
   // Application watches Secret file for changes
   ```

4. **Use Vault Agent** (sidecar handles rotation)
   - Vault Agent renews secrets
   - Writes to shared volume
   - App reads from file (can watch for changes)

**Best practice:** Design applications to handle secret rotation. Don't assume secrets are static.

</details>

### Question 4
How do you recover if you lose the Sealed Secrets controller key?

<details>
<summary>Show Answer</summary>

**Short answer: You can't decrypt existing SealedSecrets.**

**Recovery options:**

1. **Restore from backup** (if you have one)
   ```bash
   kubectl apply -f sealed-secrets-key-backup.yaml
   kubectl rollout restart deployment sealed-secrets-controller -n kube-system
   ```

2. **Re-create all secrets** (if you have original values)
   - Get plaintext values from application configs, password managers, etc.
   - Create new SealedSecrets with new controller key
   - Commit and deploy

3. **You're stuck** (if no backup, no original values)
   - Rotate everything
   - This is a disaster scenario

**Prevention:**

```bash
# Backup the key
kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > sealed-secrets-key-backup.yaml

# Store securely (Vault, encrypted S3, HSM)
# Not in the same Git repo!
```

**Lesson:** Back up the sealing key immediately after installing Sealed Secrets.

</details>

---

## Hands-On Exercise: Implement GitOps Secrets

Set up secrets management for a GitOps workflow.

### Scenario

You have a Kubernetes application that needs:
- Database credentials (username, password)
- API key for external service
- TLS certificate

### Part 1: Choose Your Approach

Based on your environment:

```markdown
## My Environment

- Number of clusters: ___
- Existing secret manager: [ ] None [ ] Vault [ ] AWS SM [ ] Other: ___
- Team managing secrets: [ ] Same as infra [ ] Security team

## Chosen Approach

[ ] Sealed Secrets
[ ] SOPS with ___ (KMS provider)
[ ] External Secrets with ___ (backend)

Rationale:
_______________________________________________
```

### Part 2: Implementation

For Sealed Secrets:

```bash
# Install controller
kubectl apply -f ___

# Create and seal database secret
kubectl create secret generic db-creds \
  --from-literal=username=___ \
  --from-literal=password=___ \
  --dry-run=client -o yaml | kubeseal --format yaml > ___

# Create and seal API key
___

# Create and seal TLS cert
___
```

For External Secrets:

```yaml
# ClusterSecretStore (configure your backend)
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: ___
spec:
  provider:
    ___: # Your provider config

---
# ExternalSecret for database
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
spec:
  secretStoreRef:
    name: ___
    kind: ClusterSecretStore
  target:
    name: db-creds
  data:
    - secretKey: ___
      remoteRef:
        key: ___
```

### Part 3: Verification

```bash
# Verify secrets are created in cluster
kubectl get secrets

# Verify application can access secrets
kubectl exec -it deploy/my-app -- env | grep DB_
```

### Part 4: Document Rotation Process

```markdown
## Secret Rotation Runbook

### When to Rotate
- [ ] Scheduled: Every ___ days
- [ ] On employee departure
- [ ] On suspected compromise

### Rotation Steps

1. Generate new credential
   ```bash
   ___
   ```

2. Update in secrets management
   ```bash
   ___
   ```

3. Verify propagation
   ```bash
   ___
   ```

4. Restart affected workloads (if needed)
   ```bash
   ___
   ```

5. Verify application works
   ```bash
   ___
   ```
```

### Success Criteria

- [ ] Chose approach with documented rationale
- [ ] Implemented at least one secret (database or API key)
- [ ] Verified secret is accessible in cluster
- [ ] Documented rotation process

---

## Key Takeaways

1. **Never commit plaintext secrets**: Git history is forever
2. **Three main patterns**: Encrypt in Git, reference external, inject at runtime
3. **Sealed Secrets**: Simple, cluster-specific, good for single-cluster
4. **SOPS**: Flexible, multi-cluster, needs KMS setup
5. **External Secrets Operator**: Central management, best for existing secret stores
6. **Always have rotation process**: Secrets are not set-and-forget

---

## Further Reading

**Documentation**:
- **Sealed Secrets** — github.com/bitnami-labs/sealed-secrets
- **SOPS** — github.com/mozilla/sops
- **External Secrets Operator** — external-secrets.io

**Articles**:
- **"Managing Kubernetes Secrets"** — Various tech blogs
- **"GitOps Secret Management"** — Weaveworks

**Tools**:
- **detect-secrets**: Secret detection for pre-commit
- **gitleaks**: Audit git repos for secrets
- **truffleHog**: Find secrets in git history

---

## Summary

Secrets in GitOps is a solved problem — but you must explicitly solve it.

Choose based on your needs:
- **Sealed Secrets**: Simple, GitOps-native, single cluster
- **SOPS**: Flexible, multi-cluster, uses existing KMS
- **External Secrets**: Central management, existing secret stores

All approaches share the goal: keep plaintext secrets out of Git while maintaining GitOps workflows.

---

## Next Module

Continue to [Module 3.6: Multi-Cluster GitOps](module-3.6-multi-cluster/) to learn how to manage multiple clusters with GitOps.

---

*"The best secret management is when developers never touch secrets directly."* — Security Wisdom
