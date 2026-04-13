---
title: "Module 4.2: Secrets"
slug: k8s/ckad/part4-environment/module-4.2-secrets
sidebar:
  order: 2
lab:
  id: ckad-4.2-secrets
  url: https://killercoda.com/kubedojo/scenario/ckad-4.2-secrets
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Similar to ConfigMaps but with security considerations
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 4.1 (ConfigMaps), understanding of base64 encoding

---

## Learning Outcomes

After completing this module, you will be able to:
- **Create** Secrets using `kubectl create secret` for generic, TLS, and docker-registry types
- **Configure** pods to consume Secrets as environment variables and volume mounts securely
- **Explain** how Kubernetes stores Secrets (base64, not encrypted) and the security implications
- **Debug** authentication failures caused by incorrectly encoded or missing Secret data

---

## Why This Module Matters

Secrets store sensitive data like passwords, API keys, and TLS certificates. While similar to ConfigMaps in usage, Secrets have additional security features and are designed specifically for sensitive information.

The CKAD exam tests your ability to:
- Create Secrets from literals, files, and YAML
- Consume Secrets as environment variables and volumes
- Understand different Secret types
- Know the security implications

> **The Safe Deposit Box Analogy**
>
> If ConfigMaps are like a public bulletin board, Secrets are like safe deposit boxes. The data is still accessible to authorized parties (pods), but it's stored more carefully, handled differently, and you wouldn't put anything there that you'd be comfortable posting publicly.

---

## Creating Secrets

### Generic Secrets (from Literals)

```bash
# Single key-value
k create secret generic db-secret --from-literal=password=mysecretpassword

# Multiple key-values
k create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=mysecretpassword \
  --from-literal=host=db.example.com
```

### From Files

```bash
# Create files with sensitive data
echo -n 'admin' > username.txt
echo -n 'mysecretpassword' > password.txt

# Create Secret from files
k create secret generic db-secret \
  --from-file=username=username.txt \
  --from-file=password=password.txt

# Cleanup files
rm username.txt password.txt
```

### From YAML (Base64 Encoded)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: YWRtaW4=      # base64 of 'admin'
  password: bXlzZWNyZXQ=  # base64 of 'mysecret'
```

> **Pause and predict**: If you run `echo 'mypassword' | base64` versus `echo -n 'mypassword' | base64`, you get different results. Why? Which one would cause your application to fail authentication?

### From YAML (Plain Text with stringData)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  username: admin
  password: mysecret
```

Note: `stringData` is write-only and converts to `data` (base64) when stored.

---

## Secret Types

| Type | Purpose |
|------|---------|
| `Opaque` | Default, arbitrary user data |
| `kubernetes.io/service-account-token` | ServiceAccount tokens |
| `kubernetes.io/dockerconfigjson` | Docker registry credentials |
| `kubernetes.io/tls` | TLS certificate and key |
| `kubernetes.io/basic-auth` | Basic authentication |
| `kubernetes.io/ssh-auth` | SSH credentials |

### Docker Registry Secret

```bash
k create secret docker-registry my-registry \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@example.com
```

### TLS Secret

```bash
k create secret tls my-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem
```

---

## Consuming Secrets

### As Environment Variables

**Single variable:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
```

**All keys as variables:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    envFrom:
    - secretRef:
        name: db-secret
```

### As Volume Files

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: db-secret
```

### With Specific Permissions

```yaml
volumes:
- name: secret-volume
  secret:
    secretName: db-secret
    defaultMode: 0400  # Read-only for owner
```

### Mount Specific Keys

```yaml
volumes:
- name: secret-volume
  secret:
    secretName: db-secret
    items:
    - key: password
      path: db-password
```

---

## Base64 Encoding/Decoding

```bash
# Encode
echo -n 'mysecret' | base64
# bXlzZWNyZXQ=

# Decode
echo 'bXlzZWNyZXQ=' | base64 -d
# mysecret

# View secret decoded
k get secret db-secret -o jsonpath='{.data.password}' | base64 -d
```

**Important**: Use `-n` with echo to avoid newline being encoded!

---

## Security Considerations

### What Secrets Provide

- **Base64 encoding** (not encryption!)
- **Stored in etcd** (can be encrypted at rest with proper config)
- **RBAC protection** - control who can read secrets
- **Limited exposure** - not shown in `kubectl get` output

> **Stop and think**: A colleague says "Kubernetes Secrets are encrypted, so our passwords are safe." Are they correct? What exactly does Kubernetes do with Secret data?

### What Secrets Don't Provide

- **Encryption by default** - base64 is encoding, not encryption
- **Memory protection** - secrets in pods are in plain text in memory
- **Log protection** - apps might log secret values

### Best Practices

```yaml
# Mount as read-only
volumeMounts:
- name: secrets
  mountPath: /etc/secrets
  readOnly: true

# Use specific permissions
volumes:
- name: secrets
  secret:
    secretName: my-secret
    defaultMode: 0400
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    Secrets Flow                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Create Secret                                              │
│  ┌─────────────────────────────────────┐                   │
│  │ k create secret generic db-secret   │                   │
│  │   --from-literal=pass=mysecret      │                   │
│  └─────────────────────────────────────┘                   │
│                    │                                        │
│                    ▼                                        │
│  Stored in etcd (base64)                                   │
│  ┌─────────────────────────────────────┐                   │
│  │ data:                               │                   │
│  │   pass: bXlzZWNyZXQ=               │                   │
│  └─────────────────────────────────────┘                   │
│                    │                                        │
│         ┌─────────┴─────────┐                              │
│         ▼                   ▼                              │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │ Environment  │    │   Volume     │                      │
│  │  Variable    │    │   Mount      │                      │
│  │              │    │              │                      │
│  │ $PASS=       │    │ /secrets/    │                      │
│  │ "mysecret"   │    │  pass file   │                      │
│  │ (decoded)    │    │ (decoded)    │                      │
│  └──────────────┘    └──────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Secrets vs ConfigMaps

| Feature | ConfigMap | Secret |
|---------|-----------|--------|
| Data encoding | Plain text | Base64 |
| Purpose | Non-sensitive config | Sensitive data |
| Size limit | 1MB | 1MB |
| Encryption at rest | No | Optional |
| Special types | No | Yes (TLS, docker-registry) |
| Mount permissions | Default | Can restrict (0400) |

---

## Quick Reference

```bash
# Create
k create secret generic NAME --from-literal=KEY=VALUE
k create secret generic NAME --from-file=FILE
k create secret tls NAME --cert=CERT --key=KEY
k create secret docker-registry NAME --docker-server=... --docker-username=...

# View (base64 encoded)
k get secret NAME -o yaml

# Decode specific key
k get secret NAME -o jsonpath='{.data.KEY}' | base64 -d

# Edit
k edit secret NAME

# Delete
k delete secret NAME
```

---

## Did You Know?

- **Base64 is not encryption.** Anyone with cluster access can decode secrets. It's just encoding to handle binary data safely in YAML.

- **Kubernetes can encrypt secrets at rest** in etcd using EncryptionConfiguration. This is cluster admin setup, not CKAD scope.

- **Secrets are namespaced.** A pod can only access secrets in its own namespace (unless using RBAC to allow cross-namespace access).

- **Environment variables from secrets can leak** in logs, crash dumps, or when printed by apps. Volume mounts are generally safer.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting `-n` when encoding | Newline gets encoded with data | Always use `echo -n` |
| Thinking base64 is secure | Anyone can decode | Use proper RBAC + encryption at rest |
| Logging secret env vars | Secrets exposed in logs | Mount as files, don't log |
| Not setting readOnly | Container could modify mount | Always use `readOnly: true` |
| Committing secrets to git | Secrets exposed in repo | Use external secret management |

---

## Quiz

1. **A developer creates a Secret with `echo 'dbpass123' | base64` and puts the result in a Secret YAML under `data.password`. Their application connects to the database but authentication fails every time, even though the password is correct. What went wrong?**
   <details>
   <summary>Answer</summary>
   The developer forgot the `-n` flag on `echo`. Without it, `echo` appends a newline character (`\n`) to the string, so the base64 encoding includes the newline. When the Secret is decoded and passed to the application, the password becomes `dbpass123\n` instead of `dbpass123`. The database rejects it because the trailing newline is part of the string. Fix: always use `echo -n 'dbpass123' | base64`, or better yet, use `stringData` in the YAML which handles encoding automatically, or create it imperatively with `kubectl create secret generic --from-literal=password=dbpass123`.
   </details>

2. **An application pod mounts a Secret as environment variables via `envFrom`. During a security incident, the team discovers the database password appears in application crash dump logs. How did this happen, and what is a more secure approach?**
   <details>
   <summary>Answer</summary>
   Environment variables are part of the process environment and are captured in crash dumps, core files, and often logged by application frameworks during startup or errors. They can also be viewed with `kubectl exec pod -- env` by anyone with exec access. A more secure approach is to mount the Secret as a volume file (e.g., at `/etc/secrets/db-password`) with `readOnly: true` and restrictive permissions (`defaultMode: 0400`). The application reads the file at startup instead of relying on environment variables. File-mounted secrets don't appear in crash dumps or process environment listings, reducing the attack surface.
   </details>

3. **You run `kubectl get secret app-creds -o yaml` and see values under `data:` that look like gibberish. A junior developer asks if this means the secrets are encrypted. What do you tell them, and what would you recommend for actual security?**
   <details>
   <summary>Answer</summary>
   The values are base64-encoded, not encrypted. Anyone can decode them with `echo 'value' | base64 -d`. Base64 is just an encoding scheme to safely represent binary data in YAML — it provides zero security. For actual protection: (1) enable etcd encryption at rest via EncryptionConfiguration so secrets are encrypted in storage, (2) use RBAC to restrict who can read secrets (`get`, `list`, `watch` on secrets), (3) consider external secret management (HashiCorp Vault, AWS Secrets Manager) for production-critical credentials, and (4) never commit Secret YAMLs to git repositories.
   </details>

4. **You need to provide your pod with Docker registry credentials to pull a private image. You create a generic Secret with the registry username and password. The pod still fails with `ImagePullBackOff`. What type of Secret should you have created instead?**
   <details>
   <summary>Answer</summary>
   Image pull credentials require a `kubernetes.io/dockerconfigjson` type Secret, not a generic `Opaque` Secret. Create it with: `kubectl create secret docker-registry my-registry --docker-server=registry.example.com --docker-username=user --docker-password=pass --docker-email=user@example.com`. Then reference it in the pod spec under `imagePullSecrets: - name: my-registry`. A generic Secret doesn't have the correct format that the kubelet expects when authenticating with a container registry. The docker-registry type encodes the credentials in the specific `.dockerconfigjson` format that container runtimes understand.
   </details>

---

## Hands-On Exercise

**Task**: Create and consume secrets in multiple ways.

**Setup:**
```bash
# Create a secret
k create secret generic app-secret \
  --from-literal=api-key=supersecretkey123 \
  --from-literal=db-password=dbpass456
```

**Part 1: Environment Variables**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secret-env
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo "API Key: $API_KEY" && echo "DB Pass: $DB_PASSWORD" && sleep 3600']
    env:
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: api-key
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: db-password
EOF

k wait --for=condition=Ready pod/secret-env --timeout=60s
k logs secret-env
```

**Part 2: Volume Mount**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secret-vol
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /secrets && cat /secrets/api-key && sleep 3600']
    volumeMounts:
    - name: secrets
      mountPath: /secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: app-secret
      defaultMode: 0400
EOF

k wait --for=condition=Ready pod/secret-vol --timeout=60s
k logs secret-vol
```

**Part 3: Decode Secret**
```bash
# View encoded
k get secret app-secret -o yaml

# Decode
k get secret app-secret -o jsonpath='{.data.api-key}' | base64 -d
echo  # newline
```

**Cleanup:**
```bash
k delete pod secret-env secret-vol
k delete secret app-secret
```

---

## Practice Drills

### Drill 1: Create from Literals (Target: 1 minute)

```bash
k create secret generic drill1 --from-literal=pass=secret123
k get secret drill1 -o yaml
k delete secret drill1
```

### Drill 2: Decode Secret (Target: 2 minutes)

```bash
k create secret generic drill2 --from-literal=token=mytoken123
k get secret drill2 -o jsonpath='{.data.token}' | base64 -d
echo
k delete secret drill2
```

### Drill 3: Environment Variable (Target: 3 minutes)

```bash
k create secret generic drill3 --from-literal=DB_PASS=dbsecret

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo $DB_PASS && sleep 3600']
    env:
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: drill3
          key: DB_PASS
EOF

k wait --for=condition=Ready pod/drill3 --timeout=60s
k logs drill3
k delete pod drill3 secret drill3
```

### Drill 4: Volume Mount (Target: 3 minutes)

```bash
k create secret generic drill4 --from-literal=cert=CERTIFICATE_DATA

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill4
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'cat /certs/cert && sleep 3600']
    volumeMounts:
    - name: certs
      mountPath: /certs
      readOnly: true
  volumes:
  - name: certs
    secret:
      secretName: drill4
EOF

k wait --for=condition=Ready pod/drill4 --timeout=60s
k logs drill4
k delete pod drill4 secret drill4
```

### Drill 5: YAML with stringData (Target: 3 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: drill5
type: Opaque
stringData:
  username: admin
  password: supersecret
EOF

# Verify it was encoded
k get secret drill5 -o yaml | grep -A2 data

# Decode
k get secret drill5 -o jsonpath='{.data.password}' | base64 -d
echo

k delete secret drill5
```

### Drill 6: Complete Scenario (Target: 5 minutes)

**Scenario**: Deploy app with database credentials.

```bash
# Create database secret
k create secret generic drill6-db \
  --from-literal=MYSQL_USER=appuser \
  --from-literal=MYSQL_PASSWORD=apppass123 \
  --from-literal=MYSQL_DATABASE=myapp

# Deploy app using all secrets as env vars
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill6
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'env | grep MYSQL && sleep 3600']
    envFrom:
    - secretRef:
        name: drill6-db
EOF

k wait --for=condition=Ready pod/drill6 --timeout=60s
k logs drill6
k delete pod drill6 secret drill6-db
```

---

## Next Module

[Module 4.3: Resource Requirements](../module-4.3-resources/) - Configure CPU and memory requests and limits.
