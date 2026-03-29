---
title: "Module 1.6: ConfigMaps and Secrets"
slug: prerequisites/kubernetes-basics/module-1.6-configmaps-secrets/
sidebar:
  order: 7
---
> **Complexity**: `[MEDIUM]` - Essential configuration management
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 3 (Pods)

---

## Why This Module Matters

Applications need configuration: database URLs, feature flags, API keys, credentials. Hardcoding these in container images is bad practice. ConfigMaps and Secrets let you manage configuration separately from your application code.

---

## ConfigMaps vs Secrets

```
┌─────────────────────────────────────────────────────────────┐
│              CONFIGMAPS vs SECRETS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap                     │  Secret                    │
│  ─────────────────────────────│────────────────────────────│
│  Non-sensitive data            │  Sensitive data           │
│  Plain text storage            │  Base64 encoded           │
│  Environment, config files     │  Passwords, tokens, keys  │
│                                │                            │
│  Examples:                     │  Examples:                │
│  • Log levels                  │  • Database passwords     │
│  • Feature flags               │  • API keys               │
│  • Config file content         │  • TLS certificates       │
│                                                             │
│  Note: Secrets are NOT encrypted by default!               │
│  Base64 is encoding, not encryption.                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ConfigMaps

### Creating ConfigMaps

```bash
# From literal values
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=ENVIRONMENT=staging

# From file
kubectl create configmap nginx-config --from-file=nginx.conf

# From directory (each file becomes a key)
kubectl create configmap configs --from-file=./config-dir/

# View ConfigMap
kubectl get configmap app-config -o yaml
```

### ConfigMap YAML

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "debug"
  ENVIRONMENT: "staging"
  config.json: |
    {
      "database": "localhost",
      "port": 5432
    }
```

### Using ConfigMaps

**As environment variables:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    env:
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: LOG_LEVEL
    # Or all keys at once:
    envFrom:
    - configMapRef:
        name: app-config
```

**As volume (files):**

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
    - name: config
      mountPath: /etc/nginx/conf.d
  volumes:
  - name: config
    configMap:
      name: nginx-config
```

---

## Secrets

### Creating Secrets

```bash
# From literal values
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secret123

# From file
kubectl create secret generic tls-cert \
  --from-file=cert.pem \
  --from-file=key.pem

# View secret (base64 encoded)
kubectl get secret db-creds -o yaml

# Decode a value
kubectl get secret db-creds -o jsonpath='{.data.password}' | base64 -d
```

### Secret YAML

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque              # Generic secret type
data:                     # Base64 encoded
  username: YWRtaW4=      # echo -n 'admin' | base64
  password: c2VjcmV0MTIz  # echo -n 'secret123' | base64
---
# Or use stringData for plain text (K8s encodes it)
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
stringData:               # Plain text, auto-encoded
  username: admin
  password: secret123
```

### Using Secrets

**As environment variables:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    env:
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: username
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
```

**As volume (files):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│              CONFIGMAP/SECRET USAGE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap/Secret                                          │
│  ┌─────────────────────┐                                   │
│  │ data:               │                                   │
│  │   KEY1: value1      │                                   │
│  │   KEY2: value2      │                                   │
│  └──────────┬──────────┘                                   │
│             │                                               │
│    ┌────────┴────────┐                                     │
│    ▼                 ▼                                      │
│                                                             │
│  As Environment      As Volume                              │
│  Variables           (Files)                                │
│  ┌────────────┐     ┌────────────────────┐                │
│  │ env:       │     │ /etc/config/       │                │
│  │   KEY1=val1│     │   KEY1  (file)     │                │
│  │   KEY2=val2│     │   KEY2  (file)     │                │
│  └────────────┘     └────────────────────┘                │
│                                                             │
│  Use envFrom for    Use volumes for                        │
│  simple key-value   config files                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Practical Example

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
data:
  LOG_LEVEL: "info"
  CACHE_TTL: "3600"
---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
stringData:
  DB_PASSWORD: "supersecret"
  API_KEY: "abc123"
---
# Pod using both
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
  - name: app
    image: myapp:v1
    envFrom:
    - configMapRef:
        name: app-settings
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: DB_PASSWORD
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: API_KEY
```

---

## Did You Know?

- **Secrets are NOT encrypted at rest by default.** They're just base64 encoded. Enable encryption at rest for real security.

- **ConfigMap/Secret updates don't automatically restart pods.** Mounted volumes update, but env vars require pod restart.

- **Max size is 1MB.** Both ConfigMaps and Secrets are limited to 1MB of data.

- **Secrets are stored in etcd.** Anyone with etcd access can read them. Use RBAC to restrict access.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Committing secrets to Git | Security breach | Use sealed-secrets or external secret management |
| Thinking base64 = encrypted | False security | Enable encryption at rest |
| Not using stringData | Manual base64 encoding errors | Use `stringData` for plain text |
| Hardcoding in images | Can't change without rebuild | Use ConfigMaps/Secrets |

---

## Quiz

1. **What's the difference between ConfigMaps and Secrets?**
   <details>
   <summary>Answer</summary>
   ConfigMaps are for non-sensitive configuration data (plain text). Secrets are for sensitive data (base64 encoded). Both can be used as environment variables or mounted as files.
   </details>

2. **How do you decode a Secret value?**
   <details>
   <summary>Answer</summary>
   `kubectl get secret NAME -o jsonpath='{.data.KEY}' | base64 -d`. The data is base64 encoded, not encrypted.
   </details>

3. **What happens to pods when you update a ConfigMap?**
   <details>
   <summary>Answer</summary>
   If mounted as a volume, files update automatically (may take up to a minute). Environment variables don't update—pods need to be restarted to pick up new env values.
   </details>

4. **What's the advantage of using `stringData` in Secrets?**
   <details>
   <summary>Answer</summary>
   You can write plain text, and Kubernetes automatically base64 encodes it. No manual encoding required, fewer errors.
   </details>

---

## Hands-On Exercise

**Task**: Create and use ConfigMaps and Secrets.

```bash
# 1. Create ConfigMap
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=APP_NAME=myapp

# 2. Create Secret
kubectl create secret generic app-secret \
  --from-literal=DB_PASS=secretpassword

# 3. Create pod using both
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: config-test
spec:
  containers:
  - name: test
    image: busybox
    command: ['sh', '-c', 'env && sleep 3600']
    envFrom:
    - configMapRef:
        name: app-config
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: DB_PASS
EOF

# 4. Verify env vars
kubectl logs config-test | grep -E "LOG_LEVEL|APP_NAME|DB_PASSWORD"

# 5. Cleanup
kubectl delete pod config-test
kubectl delete configmap app-config
kubectl delete secret app-secret
```

**Success criteria**: Pod logs show all environment variables.

---

## Summary

ConfigMaps and Secrets externalize configuration:

**ConfigMaps**:
- Non-sensitive data
- Plain text storage
- Use for config values, files

**Secrets**:
- Sensitive data
- Base64 encoded (NOT encrypted)
- Use for passwords, keys, tokens

**Usage patterns**:
- Environment variables (env, envFrom)
- Volume mounts (files)

---

## Next Module

[Module 7: Namespaces and Labels](module-1.7-namespaces-labels/) - Organizing your cluster.
