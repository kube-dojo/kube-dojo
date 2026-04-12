---
title: "Module 2.7: ConfigMaps & Secrets"
slug: k8s/cka/part2-workloads-scheduling/module-2.7-configmaps-secrets
sidebar:
  order: 8
lab:
  id: cka-2.7-configmaps-secrets
  url: https://killercoda.com/kubedojo/scenario/cka-2.7-configmaps-secrets
  duration: "45 min"
  difficulty: intermediate
  environment: kubernetes
---
**Complexity:** `[MEDIUM]` | **Time to Complete:** 55 minutes | **CKA Weight:** Part of 15%

## Prerequisites

Before starting this module, ensure you have:
- Completed [Module 2.1: Pods Deep-Dive](../module-2.1-pods/) (Pod spec structure)
- Completed [Module 2.2: Deployments](../module-2.2-deployments/) (Updating configurations)
- A running Kubernetes cluster (kind or minikube)
- Basic understanding of environment variables
- `kubectl` aliased to `k` (`alias k=kubectl`) to execute the commands verbatim

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Create** ConfigMaps and Secrets from files, literals, and directories
- **Mount** configuration as environment variables and volume mounts and explain when to use each
- **Implement** immutable ConfigMaps/Secrets and explain when immutability matters
- **Troubleshoot** configuration issues (wrong mount path, missing key, base64 encoding errors)

---

## Why This Module Matters

Every real application needs configuration. Database connection strings, feature flags, API keys, certificates—these can't be hardcoded. Kubernetes provides two primitives for injecting configuration into Pods: **ConfigMaps** for non-sensitive data and **Secrets** for sensitive data.

**On the CKA exam**, you'll need to:
- Create ConfigMaps and Secrets from files, literals, and manifests
- Inject them as environment variables or mounted files
- Update configurations without rebuilding containers
- Understand the security implications of Secrets

Getting this wrong in production means leaked credentials or broken applications. Getting it right means secure, flexible deployments.

---

## Did You Know?

- **Secrets aren't encrypted by default**—they're only base64 encoded. Anyone with API access can decode them. Encryption at rest requires explicit configuration.

- **ConfigMap updates propagate automatically** when mounted as volumes, but NOT when used as environment variables. Environment variables require Pod restart.

- **The 1MB limit** on ConfigMaps and Secrets exists because they're stored in etcd. Larger configurations need different solutions (external config stores, init containers downloading configs).

- **Projected volumes** allow you to mount multiple ConfigMaps, Secrets, and Downward API information into a single directory, which is extremely useful when an application expects all its configuration files in one place.

---

## The Real-World Analogy

Think of ConfigMaps and Secrets like hotel room configuration:

- **ConfigMaps** are like the room service menu, Wi-Fi instructions, and TV channel guide. Everyone can see them, and they change the guest experience without renovating the room.

- **Secrets** are like the safe code and door lock combination. They need to stay private, and sharing them with unauthorized people causes serious problems.

Both are separate from the room itself (your container image)—you don't rebuild the room to change the menu or safe code.

---

## Understanding ConfigMaps

### What ConfigMaps Store

ConfigMaps hold key-value pairs of non-sensitive configuration data:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  # Simple key-value pairs
  LOG_LEVEL: "debug"
  MAX_CONNECTIONS: "100"
  FEATURE_FLAGS: "new-ui,beta-api"

  # Entire configuration files
  config.json: |
    {
      "database": {
        "host": "db.example.com",
        "port": 5432
      },
      "cache": {
        "enabled": true,
        "ttl": 300
      }
    }

  nginx.conf: |
    server {
      listen 80;
      server_name localhost;
      location / {
        root /usr/share/nginx/html;
      }
    }
```

Key concepts:
- **data**: String key-value pairs (most common)
- **binaryData**: Base64-encoded binary content
- **immutable**: If set to `true`, prevents modifications (performance optimization)

### Creating ConfigMaps

**Method 1: From literal values (exam favorite)**

```bash
# Single value
k create configmap app-config --from-literal=LOG_LEVEL=debug

# Multiple values
k create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=MAX_CONNECTIONS=100 \
  --from-literal=CACHE_ENABLED=true
```

**Method 2: From a file**

```bash
# Create a config file
cat > config.properties <<EOF
database.host=db.example.com
database.port=5432
cache.enabled=true
EOF

# Create ConfigMap from file
k create configmap app-config --from-file=config.properties

# The key becomes the filename, value is file contents
# Result: data: { "config.properties": "database.host=db.example.com\n..." }
```

**Method 3: From a file with custom key**

```bash
# Specify the key name
k create configmap app-config --from-file=app.conf=config.properties
# Result: data: { "app.conf": "..." }
```

**Method 4: From a directory**

```bash
# All files in directory become keys
k create configmap app-config --from-file=./config-dir/
```

**Method 5: From env file**

```bash
cat > config.env <<EOF
LOG_LEVEL=debug
MAX_CONNECTIONS=100
EOF

k create configmap app-config --from-env-file=config.env
# Each line becomes a separate key-value pair (not one key with file contents)
```

### Using ConfigMaps in Pods

**Option 1: As environment variables (specific keys)**

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
    - name: LOG_LEVEL           # Name in container
      valueFrom:
        configMapKeyRef:
          name: app-config      # ConfigMap name
          key: LOG_LEVEL        # Key in ConfigMap
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host
          optional: true        # Don't fail if key missing
```

**Option 2: All keys as environment variables**

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
    - configMapRef:
        name: app-config
      prefix: APP_              # Optional: prefix all vars
```

All ConfigMap keys become environment variables. With prefix, `LOG_LEVEL` becomes `APP_LOG_LEVEL`.

**Option 3: As a mounted volume (entire ConfigMap)**

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
    - name: config-volume
      mountPath: /etc/config    # Directory containing all files
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      # Each key becomes a file in /etc/config/
```

**Option 4: Mount specific keys as files**

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
    - name: config-volume
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf      # Mount single file, not directory
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      items:
      - key: nginx.conf        # Key from ConfigMap
        path: nginx.conf       # Filename in volume
```

> **Pause and predict**: You update a ConfigMap that is injected into a pod two ways: one key is used as an environment variable, and another key is mounted as a volume. After updating the ConfigMap, which value changes automatically in the pod and which one stays stale? What about if the volume uses `subPath`?

### ConfigMap Update Behavior

| Injection Method | Auto-Updates? | Notes |
|------------------|---------------|-------|
| Environment variable | No | Requires Pod restart |
| Volume mount | Yes | ~1 minute delay (kubelet sync) |
| subPath mount | No | Requires Pod restart |

---

## Understanding Secrets

### Secret Types

Kubernetes supports several Secret types:

| Type | Description | Auto-created? |
|------|-------------|---------------|
| `Opaque` | Generic key-value pairs | No (default) |
| `kubernetes.io/tls` | TLS certificate + key | No |
| `kubernetes.io/dockerconfigjson` | Docker registry auth | No |
| `kubernetes.io/service-account-token` | ServiceAccount token | Legacy (Use TokenRequest) |
| `kubernetes.io/basic-auth` | Username + password | No |
| `kubernetes.io/ssh-auth` | SSH private key | No |

> **Pause and predict**: You write a Secret YAML with `data: {password: MyPassword123}` and apply it. When your app reads the password, it gets garbled text. What went wrong, and what field should you use instead of `data` to avoid this issue?

### Creating Secrets

**Method 1: Generic secret from literals**

```bash
# Values are automatically base64 encoded
k create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password='S3cur3P@ssw0rd!'
```

**Method 2: From files**

```bash
# Create credential files
echo -n 'admin' > username.txt
echo -n 'S3cur3P@ssw0rd!' > password.txt

k create secret generic db-creds \
  --from-file=username=username.txt \
  --from-file=password=password.txt

# Clean up files
rm username.txt password.txt
```

**Method 3: TLS secret**

```bash
# From existing cert and key
k create secret tls app-tls \
  --cert=tls.crt \
  --key=tls.key
```

**Method 4: Docker registry secret**

```bash
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@example.com
```

**Method 5: From YAML (manual base64)**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
data:
  # Values must be base64 encoded
  username: YWRtaW4=           # echo -n 'admin' | base64
  password: UzNjdXIzUEBzc3cwcmQh   # echo -n 'S3cur3P@ssw0rd!' | base64
```

Or use `stringData` for plain text (Kubernetes encodes it):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
stringData:
  username: admin              # Plain text - Kubernetes encodes
  password: S3cur3P@ssw0rd!
```

### Using Secrets in Pods

**Option 1: As environment variables**

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

**Option 2: All keys as environment variables**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    envFrom:
    - secretRef:
        name: db-creds
      prefix: DB_
```

**Option 3: As mounted files**

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
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true           # Best practice for secrets
  volumes:
  - name: secret-volume
    secret:
      secretName: db-creds
      defaultMode: 0400        # Restrict permissions
```

**Option 4: Mount TLS certificate**

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
    - name: tls-certs
      mountPath: /etc/nginx/ssl
      readOnly: true
  volumes:
  - name: tls-certs
    secret:
      secretName: app-tls
      items:
      - key: tls.crt
        path: server.crt
      - key: tls.key
        path: server.key
        mode: 0400             # Restrictive for private key
```

### Decoding Secrets

```bash
# View encoded values
k get secret db-creds -o yaml

# Decode a specific key
k get secret db-creds -o jsonpath='{.data.password}' | base64 -d

# Decode all keys
k get secret db-creds -o go-template='{{range $k,$v := .data}}{{$k}}: {{$v | base64decode}}{{"\n"}}{{end}}'
```

---

## Security Considerations

### Secrets Are Not Truly Secret (by default)

Base64 is encoding, not encryption:

```bash
# Anyone can decode
echo 'UzNjdXIzUEBzc3cwcmQh' | base64 -d
# Output: S3cur3P@ssw0rd!
```

**Security measures:**

1. **RBAC**: Limit who can read Secrets
2. **Encryption at rest**: Enable etcd encryption
3. **Audit logging**: Track Secret access
4. **External secret stores**: HashiCorp Vault, AWS Secrets Manager

> **Stop and think**: A security auditor tells you that storing database passwords as environment variables is risky. They recommend volume mounts instead. What specific attack vector do environment variables create that mounted files avoid?

### Environment Variables vs Volume Mounts

| Aspect | Env Vars | Volume Mounts |
|--------|----------|---------------|
| Visibility | `kubectl exec -- env` shows them | Must cat files |
| Process inheritance | Child processes inherit | Must explicitly read |
| Logging risk | Often logged accidentally | Less likely to log |
| Updates | Requires restart | Auto-updates (~1min) |

**Best practice**: Use volume mounts for sensitive secrets to reduce accidental exposure.

### Secret Immutability

For production, consider immutable Secrets:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds-v1
type: Opaque
immutable: true              # Cannot be modified
data:
  password: UzNjdXIzUEBzc3cwcmQh
```

Benefits:
- Prevents accidental changes
- Performance: kubelet doesn't need to watch for updates
- Version control: Use naming (v1, v2) for rotation

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Forgetting base64 in YAML | Invalid Secret data | Use `stringData` for plain text |
| Not using `-n` with echo | Newline in encoded value | `echo -n 'value'` |
| Expecting env var updates | App uses stale config | Restart Pod or use volume mount |
| Hardcoding secrets in image | Security risk, inflexible | Always use Secrets |
| Committing Secrets to git | Credentials exposed | Use `.gitignore`, external stores |
| Overly permissive RBAC | Anyone can read Secrets | Limit with Role/RoleBinding |
| Not setting volume readOnly | Container could modify | Always `readOnly: true` |
| Ignoring subPath limitation | Config doesn't update | Use full volume mount when possible |
| Using in Static Pods | Pod fails to start | ConfigMaps/Secrets cannot be used in Static Pods |

---

## Hands-On Exercise

### Scenario: Configure a Web Application

You need to deploy a web application with:
- Configuration file (ConfigMap)
- Database credentials (Secret)
- Feature flags (ConfigMap as env vars)

### Task 1: Create Configuration

```bash
# Create namespace
k create ns config-demo

# Create ConfigMap with app configuration
k create configmap app-config -n config-demo \
  --from-literal=LOG_LEVEL=info \
  --from-literal=CACHE_TTL=300 \
  --from-literal=FEATURE_NEW_UI=true

# Create nginx configuration file
cat > /tmp/nginx.conf <<EOF
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF

k create configmap nginx-config -n config-demo \
  --from-file=nginx.conf=/tmp/nginx.conf
```

### Task 2: Create Secrets

```bash
# Database credentials
k create secret generic db-creds -n config-demo \
  --from-literal=DB_USER=appuser \
  --from-literal=DB_PASS='Pr0dP@ssw0rd!'

# Verify
k get secret db-creds -n config-demo -o yaml
```

### Task 3: Deploy Application

```bash
cat <<EOF > /tmp/webapp.yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
  namespace: config-demo
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
    # Environment variables from ConfigMap
    envFrom:
    - configMapRef:
        name: app-config
      prefix: APP_
    # Environment variables from Secret
    env:
    - name: DATABASE_USER
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: DB_USER
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: DB_PASS
    volumeMounts:
    # Mount nginx config
    - name: nginx-config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
    # Mount secrets as files
    - name: db-creds
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: nginx-config
    configMap:
      name: nginx-config
  - name: db-creds
    secret:
      secretName: db-creds
      defaultMode: 0400
EOF

k apply -f /tmp/webapp.yaml
```

### Task 4: Verify Configuration

```bash
# Check Pod is running
k get pod webapp -n config-demo

# Verify environment variables
k exec webapp -n config-demo -- env | grep -E "APP_|DATABASE"

# Verify mounted config file
k exec webapp -n config-demo -- cat /etc/nginx/conf.d/default.conf

# Verify secret files exist (don't cat in production!)
k exec webapp -n config-demo -- ls -la /etc/secrets/

# Test nginx health endpoint
k exec webapp -n config-demo -- curl -s localhost/health
```

### Task 5: Update ConfigMap

```bash
# Update a ConfigMap value non-interactively
k patch configmap app-config -n config-demo --type merge -p '{"data":{"LOG_LEVEL":"debug"}}'

# Check if env var updated (it won't - requires restart)
k exec webapp -n config-demo -- env | grep LOG_LEVEL
# Still shows: APP_LOG_LEVEL=info

# Restart pod to pick up changes
k replace --force -f /tmp/webapp.yaml

# Verify the pod is running again
k wait --for=condition=ready pod/webapp -n config-demo --timeout=60s

# Check the updated environment variable
k exec webapp -n config-demo -- env | grep LOG_LEVEL
# Should now show: APP_LOG_LEVEL=debug
```

### Success Criteria

- [ ] Pod is running with all configurations injected
- [ ] Environment variables visible with correct prefix
- [ ] nginx.conf mounted at correct path
- [ ] Secret files have restrictive permissions (0400)
- [ ] Health endpoint returns OK

### Cleanup

```bash
k delete ns config-demo
rm -f /tmp/nginx.conf /tmp/webapp.yaml
```

---

## Quiz

### Question 1
You have a config file `app.properties` with 20 key-value pairs. You need each pair as a separate environment variable in your pod. A teammate used `--from-file=app.properties`, but all 20 pairs ended up as a single key. What did they do wrong, and what's the correct command?

<details>
<summary>Show Answer</summary>

They used `--from-file`, which stores the entire file as a single key (the filename becomes the key, the file contents become the value). For individual key-value pairs, they should use `--from-env-file`:

```bash
# Wrong: single key "app.properties" with all content as value
k create configmap test --from-file=app.properties
# Result: data: { "app.properties": "key1=value1\nkey2=value2\n..." }

# Correct: each line becomes its own key-value pair
k create configmap test --from-env-file=app.properties
# Result: data: { "key1": "value1", "key2": "value2", ... }
```

Use `--from-file` when you need to mount the entire file (e.g., nginx.conf, application.yaml). Use `--from-env-file` when you need individual properties as separate environment variables. This distinction is a common exam trap.
</details>

### Question 2
You deploy an nginx pod with a ConfigMap-mounted `nginx.conf` using `subPath`. Later, you update the ConfigMap to add a new `location /api` block. Users report the change isn't taking effect even after 10 minutes. What's wrong, and what are your options?

<details>
<summary>Show Answer</summary>

When a ConfigMap is mounted using `subPath`, updates do NOT automatically propagate to the pod. This is because `subPath` mounts a specific file rather than a symlinked directory, bypassing the kubelet's automatic update mechanism. You have three options: (1) Delete and recreate the pod to pick up the new ConfigMap (simplest for exam), (2) switch from `subPath` to a full volume mount at a directory path (enables auto-updates but may overwrite other files in the directory), or (3) use an immutable ConfigMap naming scheme (e.g., `nginx-config-v2`) and update the pod spec to reference the new ConfigMap. Option 2 is the best long-term solution if auto-updates are important, but be aware that a full volume mount replaces the entire directory contents.
</details>

### Question 3
A junior developer wrote a Secret YAML with `data: {password: MySecurePassword123}` and applied it. Authentication to the database fails, but `kubectl get secret db-creds -o yaml` shows the password field has a value. They're confused because the value "is right there." What are two things wrong with this scenario, and how should the YAML be written?

<details>
<summary>Show Answer</summary>

Two issues: (1) The `data` field requires base64-encoded values, but `MySecurePassword123` is plain text. Kubernetes will try to base64-decode this value when injecting it into a pod, producing garbled output. (2) The developer may also be confused because `kubectl get secret -o yaml` shows base64-encoded values, which look valid but are actually a double-encoding issue. The fix is to either base64-encode the value yourself (`echo -n 'MySecurePassword123' | base64`) in the `data` field, or use `stringData` instead, which accepts plain text and Kubernetes handles the encoding:

```yaml
stringData:
  password: MySecurePassword123
```

Always use `echo -n` (not `echo`) when encoding to avoid including a trailing newline, which is another common cause of authentication failures.
</details>

### Question 4
A security audit found that your team's database passwords are visible when running `kubectl exec <pod> -- env` on any pod that uses them. The auditor requires that secrets not be retrievable via process introspection. What injection method are you using now, what should you switch to, and what additional hardening step should you take?

<details>
<summary>Show Answer</summary>

You're currently injecting secrets as environment variables (via `envFrom` or `env.valueFrom.secretKeyRef`), which makes them visible to `kubectl exec -- env`, child process inheritance, and crash dump logging. Switch to volume-mounted secrets, which are stored as files at a mount path (e.g., `/etc/secrets/password`). Applications must explicitly read the file to access the value. Additionally, set `readOnly: true` on the volume mount and use restrictive file permissions with `defaultMode: 0400` on the volume definition. This ensures the files can only be read by the container's process owner and cannot be modified. For deeper security, combine this with RBAC rules that limit which service accounts can access the Secret, and enable encryption at rest for etcd to protect the stored Secret data.
</details>

### Question 5
You created a Secret with `echo 'S3cur3P@ssw0rd!' | base64` and stored the result in your YAML. When the application tries to authenticate, it fails with "invalid credentials." You've triple-checked the password is correct. What went wrong?

<details>
<summary>Show Answer</summary>

The `echo` command adds a trailing newline character by default. When you pipe to base64, the newline is encoded along with the password, so the decoded value becomes `S3cur3P@ssw0rd!\n` instead of `S3cur3P@ssw0rd!`. The database rejects the password because of the invisible extra character. The fix is to use `echo -n` (no newline):

```bash
# Wrong: includes newline
echo 'S3cur3P@ssw0rd!' | base64    # encodes "S3cur3P@ssw0rd!\n"

# Correct: no newline
echo -n 'S3cur3P@ssw0rd!' | base64  # encodes "S3cur3P@ssw0rd!"
```

This is one of the most common Kubernetes Secret pitfalls. Alternatively, use `stringData` in your YAML to avoid base64 entirely, or use `kubectl create secret generic --from-literal=password='S3cur3P@ssw0rd!'` which handles encoding correctly.
</details>

### Question 6
Your application reads its config from a file at `/etc/config/app.yaml` mounted from a ConfigMap. After a ConfigMap update, the application picks up the new config automatically within a minute. Your team wants the same auto-update behavior for a TLS certificate stored in a Secret and mounted at `/etc/nginx/ssl/server.crt`. But they're using `subPath` for the certificate mount. Will the TLS certificate auto-update? What's the best approach?

<details>
<summary>Show Answer</summary>

No, the TLS certificate will NOT auto-update because `subPath` mounts bypass the kubelet's automatic update mechanism. The ConfigMap at `/etc/config/app.yaml` auto-updates because it uses a full volume mount (the kubelet creates symlinks that get updated). For the TLS certificate, remove the `subPath` and mount the entire secret volume to a directory (e.g., `/etc/nginx/ssl/`), then reference the files within that directory. The certificate will auto-update within approximately 60 seconds of a Secret change. However, note that nginx caches TLS certificates in memory, so you may also need a sidecar or process that watches for file changes and triggers a config reload (e.g., `nginx -s reload`).
</details>

### Question 7
You have a ConfigMap mounted as a volume in your Pod. You set `immutable: true` on the ConfigMap, but later need to update a configuration value. What is the correct procedure to apply this change to your application?

<details>
<summary>Show Answer</summary>

Because the ConfigMap is marked as immutable, you cannot update it in place. The kubelet also stops watching immutable ConfigMaps for changes, which improves cluster performance. To apply a change, you must: (1) Create a new ConfigMap with a new name (e.g., `app-config-v2`) containing the updated values, and (2) Update the Pod template (usually via its Deployment) to reference the new ConfigMap name. This triggers a rolling update of the Pods, ensuring a safe and version-controlled configuration rollout.
</details>

---

## Practice Drills

Practice these scenarios under exam time pressure.

### Drill 1: Quick ConfigMap Creation
**Target Time:** 30 seconds

Create a ConfigMap named `web-config` with these values:
- `SERVER_PORT=8080`
- `DEBUG_MODE=false`

<details>
<summary>Show Solution</summary>

```bash
k create configmap web-config \
  --from-literal=SERVER_PORT=8080 \
  --from-literal=DEBUG_MODE=false
```
</details>

### Drill 2: ConfigMap from File
**Target Time:** 45 seconds

Create a file `/tmp/app.properties` with content:
```
db.host=localhost
db.port=5432
```
Then create ConfigMap `app-props` from this file.

<details>
<summary>Show Solution</summary>

```bash
cat > /tmp/app.properties <<EOF
db.host=localhost
db.port=5432
EOF

k create configmap app-props --from-file=/tmp/app.properties
```
</details>

### Drill 3: Secret from Literals
**Target Time:** 30 seconds

Create a Secret named `api-key` with:
- `API_KEY=abc123secret`
- `API_SECRET=xyz789token`

<details>
<summary>Show Solution</summary>

```bash
k create secret generic api-key \
  --from-literal=API_KEY=abc123secret \
  --from-literal=API_SECRET=xyz789token
```
</details>

### Drill 4: Pod with ConfigMap Env Vars
**Target Time:** 2 minutes

Create a Pod `envpod` using image `nginx` that loads all keys from ConfigMap `web-config` as environment variables.

<details>
<summary>Show Solution</summary>

```bash
k run envpod --image=nginx --dry-run=client -o yaml > /tmp/pod.yaml
```

Edit to add `envFrom`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: envpod
spec:
  containers:
  - name: envpod
    image: nginx
    envFrom:
    - configMapRef:
        name: web-config
```

```bash
k apply -f /tmp/pod.yaml
```
</details>

### Drill 5: Pod with Secret Volume
**Target Time:** 2 minutes

Create Pod `secretpod` using image `nginx` that mounts Secret `api-key` at `/etc/api-secrets` with read-only access.

<details>
<summary>Show Solution</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secretpod
spec:
  containers:
  - name: secretpod
    image: nginx
    volumeMounts:
    - name: secret-vol
      mountPath: /etc/api-secrets
      readOnly: true
  volumes:
  - name: secret-vol
    secret:
      secretName: api-key
```

```bash
k apply -f /tmp/secretpod.yaml
```
</details>

### Drill 6: Decode Secret Value
**Target Time:** 30 seconds

Extract and decode the `API_KEY` value from Secret `api-key`.

<details>
<summary>Show Solution</summary>

```bash
k get secret api-key -o jsonpath='{.data.API_KEY}' | base64 -d
```
</details>

### Drill 7: TLS Secret
**Target Time:** 1 minute

You have files `server.crt` and `server.key`. Create a TLS Secret named `web-tls`.

<details>
<summary>Show Solution</summary>

```bash
# If you need to create test files first:
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/CN=test"

# Create the secret
k create secret tls web-tls --cert=server.crt --key=server.key
```
</details>

### Drill 8: Specific Key as File
**Target Time:** 2 minutes

Create Pod `configfile` that mounts only the `db.host` key from ConfigMap `app-props` as `/etc/dbhost` file.

<details>
<summary>Show Solution</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: configfile
spec:
  containers:
  - name: configfile
    image: nginx
    volumeMounts:
    - name: config-vol
      mountPath: /etc/dbhost
      subPath: db.host
  volumes:
  - name: config-vol
    configMap:
      name: app-props
      items:
      - key: db.host
        path: db.host
```

Note: This requires the ConfigMap to have a key named `db.host`. If your ConfigMap was created with `--from-file`, the key would be `app.properties` (the filename).
</details>

### Drill 9: Troubleshooting Missing ConfigMap
**Target Time:** 2 minutes

A Pod named `api-server` is crashing with `CreateContainerConfigError`. Troubleshoot and find out why it won't start. (Simulate this by creating a pod referencing a non-existent ConfigMap).

<details>
<summary>Show Solution</summary>

```bash
# Check the pod status and events
k describe pod api-server

# Look at the Events section at the bottom. You will see an error like:
# Warning  Failed  ...  Error: configmap "missing-config" not found

# To fix it, either create the missing ConfigMap or update the Pod to reference the correct one.
```
</details>

### Drill 10: Troubleshooting Secret Base64 Error
**Target Time:** 2 minutes

You created a Secret using YAML, but the application is getting rejected due to invalid credentials. You suspect an encoding issue. How do you verify the exact decoded value Kubernetes is passing to the Pod?

<details>
<summary>Show Solution</summary>

```bash
# Get the base64 encoded value from the secret
k get secret my-secret -o jsonpath='{.data.password}'

# Decode it and pipe through xxd or cat -e to reveal hidden characters (like trailing newlines)
k get secret my-secret -o jsonpath='{.data.password}' | base64 -d | cat -e

# If you see "mypassword%$" (where $ is a newline) instead of just "mypassword%", 
# it means it was encoded with a newline. Fix it by recreating the secret with echo -n.
```
</details>

---

## Key Takeaways

1. **ConfigMaps** store non-sensitive configuration; **Secrets** store sensitive data (but aren't encrypted by default)

2. **Creation methods**: `--from-literal`, `--from-file`, `--from-env-file`, YAML manifest

3. **Injection methods**: Environment variables (single or all), volume mounts (full or specific keys)

4. **Updates**: Volume mounts auto-update (~1min), environment variables require Pod restart, subPath mounts don't update

5. **Secrets**: Use `stringData` for plain text in YAML, always use `echo -n` to avoid newline issues

6. **Security**: Limit RBAC access, prefer volume mounts over env vars, consider external secret stores for production

---

## What's Next?

Congratulations! You've completed all modules in Part 2: Workloads & Scheduling.

**Next step:** [Part 2 Cumulative Quiz](../part2-cumulative-quiz/) - Test your knowledge across all Part 2 topics before moving on.

**Coming up in Part 3:** Services & Networking - How Pods communicate with each other and the outside world.

---

### Part 2 Module Index

Quick links for review:

| Module | Topic | Key Skills |
|--------|-------|------------|
| [2.1](../module-2.1-pods/) | Pods Deep-Dive | Multi-container patterns, lifecycle, probes |
| [2.2](../module-2.2-deployments/) | Deployments & ReplicaSets | Rolling updates, rollbacks, scaling |
| [2.3](../module-2.3-daemonsets-statefulsets/) | DaemonSets & StatefulSets | Node-level workloads, stateful apps |
| [2.4](../module-2.4-jobs-cronjobs/) | Jobs & CronJobs | Batch processing, scheduled tasks |
| [2.5](../module-2.5-resource-management/) | Resource Management | Requests, limits, QoS, quotas |
| [2.6](../module-2.6-scheduling/) | Scheduling | Affinity, taints, topology |
| [2.7](../module-2.7-configmaps-secrets/) | ConfigMaps & Secrets | Configuration injection |

**Exam Tip:** Part 2 (Workloads & Scheduling) is 15% of the CKA exam. Master `kubectl run`, `kubectl create deployment`, and `kubectl create configmap/secret` for quick task completion.