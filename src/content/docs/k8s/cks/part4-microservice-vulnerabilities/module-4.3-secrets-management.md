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

1. **Configure** etcd encryption at rest for Kubernetes Secrets
2. **Implement** external secrets management using Vault or cloud provider secret stores
3. **Audit** RBAC permissions to identify overly broad access to Secret resources
4. **Design** a secrets management strategy that eliminates base64-only storage risks

---

## Why This Module Matters

Kubernetes Secrets store sensitive data like passwords, API keys, and certificates. By default, they're only base64-encoded (not encrypted!) and accessible to anyone with RBAC permissions. Proper secrets management prevents credential leaks and privilege escalation.

CKS heavily tests secrets security practices.

---

## Secret Security Problems

```
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT SECRETS SECURITY                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️  Base64 is NOT encryption!                             │
│  ─────────────────────────────────────────────────────────  │
│  $ echo "mysecretpassword" | base64                        │
│  bXlzZWNyZXRwYXNzd29yZAo=                                  │
│                                                             │
│  $ echo "bXlzZWNyZXRwYXNzd29yZAo=" | base64 -d            │
│  mysecretpassword                                          │
│                                                             │
│  Problems with default secrets:                            │
│  ├── Stored unencrypted in etcd                           │
│  ├── Visible to anyone with get secrets permission         │
│  ├── Appear in pod specs (kubectl describe)               │
│  ├── May be logged in audit logs                          │
│  └── Mounted as plain text files in containers            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Creating Secrets

### Generic Secret

```bash
# From literal values
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secretpass123

# From files
kubectl create secret generic ssh-key \
  --from-file=id_rsa=/path/to/id_rsa \
  --from-file=id_rsa.pub=/path/to/id_rsa.pub

# From env file
kubectl create secret generic app-config \
  --from-env-file=secrets.env
```

### TLS Secret

```bash
# Create TLS secret
kubectl create secret tls web-tls \
  --cert=server.crt \
  --key=server.key
```

### Docker Registry Secret

```bash
# Create registry credential
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=password \
  --docker-email=user@example.com
```

---

## Using Secrets in Pods

### Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-env-pod
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
```

### Volume Mounts (Preferred)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-volume-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
      # Optional: set specific permissions
      defaultMode: 0400
```

### Why Volume Mounts Are Better

```
┌─────────────────────────────────────────────────────────────┐
│              ENV VARS vs VOLUME MOUNTS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Environment Variables:                                     │
│  ├── Visible in /proc/<pid>/environ                        │
│  ├── May leak to child processes                           │
│  ├── Often logged by applications                          │
│  └── Visible in 'docker inspect'                           │
│                                                             │
│  Volume Mounts:                                             │
│  ├── Files with restricted permissions                     │
│  ├── tmpfs (in-memory, not written to disk)               │
│  ├── Auto-updated when secret changes                      │
│  └── Controlled access via file permissions               │
│                                                             │
│  Best Practice: Always use volume mounts                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Encryption at Rest

### Check Current Encryption Status

```bash
# Check API server configuration
ps aux | grep kube-apiserver | grep encryption-provider-config

# Or check the manifest
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep encryption
```

### Enable etcd Encryption

```yaml
# /etc/kubernetes/enc/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      # aescbc - recommended for production
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      # identity is the fallback (unencrypted)
      - identity: {}
```

### Generate Encryption Key

```bash
# Generate random 32-byte key
head -c 32 /dev/urandom | base64

# Example output (use your own!):
# K8sSecretEncryptionKey1234567890ABCDEF==
```

### Configure API Server

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    # Add this flag
    - --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml
    volumeMounts:
    # Mount the encryption config
    - mountPath: /etc/kubernetes/enc
      name: enc
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/enc
      type: DirectoryOrCreate
    name: enc
```

### Verify Encryption Works

```bash
# Create a test secret
kubectl create secret generic test-encryption --from-literal=mykey=myvalue

# Read directly from etcd (on control plane)
ETCDCTL_API=3 etcdctl get /registry/secrets/default/test-encryption \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key | hexdump -C

# If encrypted: You'll see random bytes, not readable text
# If NOT encrypted: You'll see "mykey" and "myvalue" in plain text
```

### Re-encrypt Existing Secrets

```bash
# After enabling encryption, re-encrypt all existing secrets
kubectl get secrets -A -o json | kubectl replace -f -
```

---

## Encryption Providers

```
┌─────────────────────────────────────────────────────────────┐
│              ENCRYPTION PROVIDERS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  identity (default)                                        │
│  └── No encryption, plain storage                          │
│                                                             │
│  aescbc (recommended)                                      │
│  └── AES-CBC with PKCS#7 padding                          │
│      Strong, widely supported                              │
│                                                             │
│  aesgcm                                                    │
│  └── AES-GCM authenticated encryption                     │
│      Faster, must rotate keys every 200K writes           │
│                                                             │
│  kms                                                       │
│  └── External KMS provider (AWS KMS, Azure Key Vault)     │
│      Best for production, keys never touch etcd           │
│                                                             │
│  secretbox                                                 │
│  └── XSalsa20 + Poly1305                                  │
│      Strong, fixed nonce size                              │
│                                                             │
│  Order matters: First provider encrypts new secrets        │
│  All listed providers can decrypt                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## RBAC for Secrets

### Restrict Secret Access

```yaml
# Only allow access to specific secrets
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["app-config", "db-creds"]  # Specific secrets only
  verbs: ["get"]
```

### Dangerous RBAC Patterns

```yaml
# DON'T DO THIS - grants access to ALL secrets
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dangerous-role
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]  # Can read ALL secrets cluster-wide!
```

### Audit Secret Access

```bash
# Find who can access secrets
kubectl auth can-i get secrets --as=system:serviceaccount:default:default
kubectl auth can-i list secrets --as=system:serviceaccount:kube-system:default

# List all roles that can access secrets
kubectl get clusterroles -o json | jq '.items[] | select(.rules[]?.resources[]? == "secrets") | .metadata.name'
```

---

## Preventing Secret Exposure

### Disable Secret Auto-mount

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-automount-pod
spec:
  automountServiceAccountToken: false  # Don't mount SA token
  containers:
  - name: app
    image: nginx
```

### Use Read-Only Mounts

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readonly-secrets
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true  # Prevent modification
  volumes:
  - name: secrets
    secret:
      secretName: app-secrets
      defaultMode: 0400  # Read-only for owner
```

---

## Real Exam Scenarios

### Scenario 1: Enable etcd Encryption

```bash
# Step 1: Create encryption config directory
sudo mkdir -p /etc/kubernetes/enc

# Step 2: Generate encryption key
ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)

# Step 3: Create encryption config
sudo tee /etc/kubernetes/enc/encryption-config.yaml << EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}
EOF

# Step 4: Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Add to command:
# - --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml

# Add volume mount:
# volumeMounts:
# - mountPath: /etc/kubernetes/enc
#   name: enc
#   readOnly: true

# Add volume:
# volumes:
# - hostPath:
#     path: /etc/kubernetes/enc
#     type: DirectoryOrCreate
#   name: enc

# Step 5: Wait for API server to restart
kubectl get nodes  # Wait until this works

# Step 6: Re-encrypt existing secrets
kubectl get secrets -A -o json | kubectl replace -f -
```

### Scenario 2: Fix Secret RBAC

```bash
# Find ServiceAccount with too much secret access
kubectl get rolebindings,clusterrolebindings -A -o json | \
  jq -r '.items[] | select(.roleRef.name | contains("secret")) |
         "\(.metadata.namespace // "cluster")/\(.metadata.name) -> \(.roleRef.name)"'

# Create restrictive role
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-secret-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["app-config"]  # Only this secret
  verbs: ["get"]
EOF
```

### Scenario 3: Create Secret from File

```bash
# Create secret containing certificate
kubectl create secret generic tls-cert \
  --from-file=tls.crt=./server.crt \
  --from-file=tls.key=./server.key \
  -n production

# Use in pod with volume mount
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: tls
      mountPath: /etc/tls
      readOnly: true
  volumes:
  - name: tls
    secret:
      secretName: tls-cert
      defaultMode: 0400
EOF
```

---

## External Secrets Management

```
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL SECRETS SOLUTIONS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HashiCorp Vault                                           │
│  └── Industry standard, rich features                      │
│      Vault Agent Injector for Kubernetes                   │
│                                                             │
│  AWS Secrets Manager + External Secrets Operator           │
│  └── Native AWS integration                                │
│      Syncs AWS secrets to Kubernetes                       │
│                                                             │
│  Azure Key Vault                                           │
│  └── Azure-native solution                                 │
│      CSI driver available                                  │
│                                                             │
│  Sealed Secrets (Bitnami)                                  │
│  └── Encrypt secrets for Git storage                       │
│      Only cluster can decrypt                              │
│                                                             │
│  Note: External solutions are NOT on CKS exam              │
│  but understanding them shows security maturity            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Base64 is just encoding**, not encryption. Anyone can decode it. The CKS exam tests whether you understand this critical distinction.

- **etcd stores secrets in plain text by default**. Without encryption at rest, anyone with etcd access can read all cluster secrets.

- **Secrets mounted as volumes** are stored in tmpfs (memory), not on disk. They're more secure than environment variables.

- **The encryption config order matters**. New secrets are encrypted with the first provider. All listed providers can decrypt, allowing key rotation.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Thinking base64 is secure | Data exposed | Enable encryption at rest |
| Using env vars for secrets | Leaks to logs | Use volume mounts |
| Broad RBAC for secrets | Any pod can read | Use resourceNames |
| Not re-encrypting after enabling | Old secrets unencrypted | Run kubectl replace |
| Secrets in Git | Permanent exposure | Use Sealed Secrets |

---

## Quiz

1. **Is base64 encoding encryption?**
   <details>
   <summary>Answer</summary>
   No! Base64 is reversible encoding, not encryption. Anyone can decode it with `base64 -d`. Secrets need encryption at rest for actual security.
   </details>

2. **Where should encryption config be stored?**
   <details>
   <summary>Answer</summary>
   On the control plane node, typically `/etc/kubernetes/enc/encryption-config.yaml`, and referenced by API server flag `--encryption-provider-config`.
   </details>

3. **Why are volume mounts preferred over environment variables for secrets?**
   <details>
   <summary>Answer</summary>
   Volume mounts: stored in tmpfs (memory), have file permissions, auto-update when secret changes. Environment variables: visible in /proc, may leak to child processes, often logged.
   </details>

4. **How do you verify secrets are encrypted in etcd?**
   <details>
   <summary>Answer</summary>
   Read directly from etcd using etcdctl. If encrypted, you'll see random bytes. If not encrypted, you'll see the secret values in plain text.
   </details>

---

## Hands-On Exercise

**Task**: Enable encryption at rest and verify it works.

```bash
# Step 1: Check current encryption status
ps aux | grep kube-apiserver | grep encryption-provider-config || echo "Not configured"

# Step 2: Create test secret BEFORE encryption
kubectl create secret generic pre-encryption --from-literal=test=beforeencryption

# Step 3: Create encryption config (on control plane node)
sudo mkdir -p /etc/kubernetes/enc

ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)
sudo tee /etc/kubernetes/enc/encryption-config.yaml << EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}
EOF

# Step 4: Backup API server manifest
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/kube-apiserver.yaml.bak

# Step 5: Edit API server manifest (add encryption config)
# Add: --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml
# Add volume and volumeMount for /etc/kubernetes/enc

# Step 6: Wait for API server restart
sleep 30
kubectl get nodes

# Step 7: Create test secret AFTER encryption
kubectl create secret generic post-encryption --from-literal=test=afterencryption

# Step 8: Re-encrypt pre-existing secret
kubectl get secret pre-encryption -o json | kubectl replace -f -

# Step 9: Verify in etcd (if you have access)
# Encrypted secrets show random bytes, not plain text

# Cleanup
kubectl delete secret pre-encryption post-encryption
```

**Success criteria**: Understand encryption configuration and verification.

---

## Summary

**Secret Security Problems**:
- Base64 is NOT encryption
- etcd stores plain text by default
- Environment variables leak

**Best Practices**:
- Enable encryption at rest (aescbc)
- Use volume mounts, not env vars
- Restrict RBAC with resourceNames
- Re-encrypt after enabling encryption

**Encryption Setup**:
- Create EncryptionConfiguration
- Add API server flag
- Restart API server
- Re-encrypt existing secrets

**Exam Tips**:
- Know encryption config format
- Understand provider order
- Be able to verify encryption works

---

## Next Module

[Module 4.4: Runtime Sandboxing](../module-4.4-runtime-sandboxing/) - gVisor and Kata Containers for container isolation.
