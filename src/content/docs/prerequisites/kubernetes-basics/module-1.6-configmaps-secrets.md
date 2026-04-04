---
title: "Module 1.6: ConfigMaps and Secrets"
slug: prerequisites/kubernetes-basics/module-1.6-configmaps-secrets
sidebar:
  order: 7
---
> **Complexity**: `[MEDIUM]` - Essential configuration management
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 3 (Pods)

Every major cloud security breach starts the same way — credentials that shouldn't have been there.

Imagine you have a web application with hardcoded database credentials in the source code. If that code is compromised, the attacker has the keys to your database. In Module 1.3, you learned how to run applications in Pods. But how do you pass configuration and sensitive data to those Pods without rebuilding the container image every time a password changes? Let's fix that hardcoded password.

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Create** ConfigMaps and Secrets and inject them into pods as environment variables or mounted files
- **Explain** why configuration should be separate from code (the 12-factor app principle)
- **Choose** between ConfigMaps and Secrets based on data sensitivity
- **Update** configuration dynamically without rebuilding container images
- **Identify** three security gaps in default Secret handling and describe mitigations

---

## Why This Module Matters

Applications need configuration: database URLs, feature flags, API keys, credentials. Hardcoding these in container images is bad practice. ConfigMaps and Secrets let you manage configuration separately from your application code.

Think of ConfigMaps as a restaurant's public menu: it changes occasionally, anyone can read it, and it tells the staff what to cook. Secrets are the locked safe containing the secret sauce recipe: you only give access to the specific chefs who actually need it.

---

## ConfigMaps vs Secrets

```text
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

> **Pause and predict**: Your application needs a feature flag (`ENABLE_BETA=true`) and a database password. Which object should store each, and why?

---

## ConfigMaps

ConfigMaps store non-confidential data in key-value pairs.

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

> **Stop and think**: When would you mount configuration as a file versus using an environment variable?

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

Now that you can create ConfigMaps, let's talk about their secretive cousin. Secrets follow the exact same pattern as ConfigMaps, but with two key differences: you reference them using `secretKeyRef` instead of `configMapKeyRef`, and their data values must be base64 encoded.

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

```text
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

## Worked Example: Refactoring Hardcoded Config

Let's walk through how to refactor an application that has hardcoded settings.

**1. Identify the configuration points**: The application connects to a database at `localhost:5432` with a password `supersecret`, and uses a caching TTL of `3600`.

**2. Separate by sensitivity**: The cache TTL is not sensitive, so it belongs in a ConfigMap. The database password is highly sensitive, so it must go into a Secret.

**3. Create the objects**:

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
data:
  CACHE_TTL: "3600"
---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
stringData:
  DB_PASSWORD: "supersecret"
```

**4. Mount them into the Pod**:

```yaml
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
```

---

## Production Reality: Handling Secrets Securely

In 2019, multiple startups suffered severe breaches because developers committed their `.env` files containing raw database passwords into public Git repositories. Storing plain Kubernetes Secret YAMLs in Git creates the exact same vulnerability.

In a production environment, you must address three major security gaps in default Kubernetes Secrets:

1. **Secrets are just Base64 encoded, not encrypted**. Anyone who can view the Secret can easily decode it.
   *Mitigation*: Enable Encryption at Rest in your Kubernetes API server so that secrets are encrypted before being written to the `etcd` database.
2. **You cannot commit plain Secrets to Git**.
   *Mitigation*: Use tools like **Sealed Secrets** (which encrypts the secret so it is safe to commit, and the cluster decrypts it) or the **External Secrets Operator** (which pulls secrets dynamically from cloud providers like AWS Secrets Manager or HashiCorp Vault).
3. **Environment variables can be leaked**. If an application crashes, crash reporting tools often dump all environment variables to the logs.
   *Mitigation*: Mount secrets as files using volumes. It is much harder to accidentally leak a mounted file than an environment variable, and files dynamically update when the Secret changes without requiring a Pod restart.

---

## Did You Know?

- **ConfigMap/Secret updates don't automatically restart pods.** Mounted volumes update (which can take up to a minute), but environment variables require a pod restart to pick up new values.
- **Max size is 1MB.** Both ConfigMaps and Secrets are limited to 1MB of data to prevent bloating the `etcd` database.
- **Secrets are stored in etcd.** Anyone with etcd access can read them. Use Role-Based Access Control (RBAC) to heavily restrict access to Secrets.

> **Stop and think**: A colleague says Secrets are secure because they are base64 encoded. How would you respond?

---

## Common Mistakes

| Mistake | Impact | Solution |
|---------|--------|----------|
| Committing secrets to Git | 100% compromise of credentials, requiring immediate rotation | Use sealed-secrets or external secret management |
| Thinking base64 = encrypted | False sense of security; anyone with read access can decode | Enable encryption at rest in etcd |
| Not using stringData | High rate of manual base64 encoding errors or trailing spaces | Use `stringData` for plain text |
| Hardcoding in images | Multi-minute deployment delays just to change a configuration value | Use ConfigMaps/Secrets |

---

## Quiz

1. **A developer updates a ConfigMap that is injected into a running Pod as an environment variable, but the application isn't picking up the new value. Why?**
   <details>
   <summary>Answer</summary>
   Environment variables are only read when the container starts. Updating a ConfigMap does not automatically restart the Pod. To pick up the new environment variable, the Pod must be deleted and recreated (or restarted via a Deployment rollout). If the ConfigMap was mounted as a volume instead, the file contents would update dynamically.
   </details>

2. **You are reviewing a colleague's Kubernetes YAML and notice they have stored a production API key in a ConfigMap. Why is this a problem, and how should it be fixed?**
   <details>
   <summary>Answer</summary>
   ConfigMaps are meant for non-sensitive data. Anyone with basic access to the namespace might have permission to read ConfigMaps, exposing the API key. It should be moved to a Secret, and access to Secrets should be tightly restricted using RBAC. Additionally, the cluster should be configured with encryption at rest for Secrets.
   </details>

3. **Your security team runs a vulnerability scan and finds that if your application crashes, the database password is being printed in the crash logs. How can you change how the Secret is provided to fix this?**
   <details>
   <summary>Answer</summary>
   The application is likely receiving the Secret as an environment variable, which crash dumpers often log by default. The mitigation is to mount the Secret as a volume (a file) instead. The application can read the file at startup, and crash reporters will not automatically log the contents of mounted files.
   </details>

4. **This YAML has a major problem. What is it?**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: db-creds
   data:
     password: mysecretpassword
   ```
   <details>
   <summary>Answer</summary>
   The YAML uses the `data` field but provides plain text (`mysecretpassword`). The `data` field expects values to be base64 encoded. The Secret creation will either fail or the application will receive garbage when it decodes it. The developer should either manually base64 encode the password, or change the key from `data` to `stringData`.
   </details>

---

## Hands-On Exercise

**Task**: Create and use ConfigMaps and Secrets.

```bash
# 1. Create ConfigMap
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=APP_NAME=myapp

# 2. DECISION POINT: Create the secret.
# Will you use --from-literal or create a YAML file with stringData? 
# We'll use the CLI for speed here:
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

# 4. Verify env vars are present
kubectl logs config-test | grep -E "LOG_LEVEL|APP_NAME|DB_PASSWORD"
```

**Success criteria**: Pod logs show all three environment variables populated with the correct values.

### Graduated Mini-Challenge

Instead of injecting the ConfigMap as an environment variable using `envFrom`, modify the `config-test` Pod YAML to mount `app-config` as a volume at `/etc/app-config`. 

Once the Pod is running, verify the files exist by running:
`kubectl exec config-test -- ls -l /etc/app-config`

Then clean up your resources:
```bash
kubectl delete pod config-test
kubectl delete configmap app-config
kubectl delete secret app-secret
```

---

## Summary

ConfigMaps and Secrets externalize configuration, allowing you to separate code from environment-specific variables.

**ConfigMaps**:
- Non-sensitive data
- Plain text storage
- Use for config values, feature flags, and non-sensitive files

**Secrets**:
- Sensitive data
- Base64 encoded (NOT encrypted by default)
- Use for passwords, API keys, tokens, and certificates

**Usage patterns**:
- Environment variables (`env`, `envFrom`) - easy to use, but static and prone to leaking in crash logs
- Volume mounts (files) - dynamically update and generally more secure

---

## Next Module

[Module 1.7: Namespaces and Labels](../module-1.7-namespaces-labels/) - Organizing your cluster.