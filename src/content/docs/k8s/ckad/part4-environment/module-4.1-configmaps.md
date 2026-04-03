---
title: "Module 4.1: ConfigMaps"
slug: k8s/ckad/part4-environment/module-4.1-configmaps
sidebar:
  order: 1
lab:
  id: ckad-4.1-configmaps
  url: https://killercoda.com/kubedojo/scenario/ckad-4.1-configmaps
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Multiple ways to create and consume
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 1.1 (Pods), understanding of environment variables

---

## Learning Outcomes

After completing this module, you will be able to:
- **Create** ConfigMaps from literals, files, and directories using imperative and declarative methods
- **Configure** pods to consume ConfigMaps as environment variables and volume mounts
- **Debug** application configuration issues caused by missing or incorrectly mounted ConfigMaps
- **Explain** when to use environment variables vs volume mounts for configuration injection

---

## Why This Module Matters

ConfigMaps decouple configuration from container images. Instead of baking settings into your image, you inject them at runtime. This lets you use the same image across environments (dev, staging, production) with different configurations.

The CKAD exam frequently tests ConfigMaps because they're fundamental to the twelve-factor app methodology. Expect questions on:
- Creating ConfigMaps from literals, files, and directories
- Consuming as environment variables
- Mounting as volumes
- Updating configurations

> **The Restaurant Menu Analogy**
>
> Think of ConfigMaps as a restaurant's specials board. The kitchen (container image) stays the same, but the specials (configuration) change daily. The chef doesn't rebuild the kitchen to change the menu—they just update the board. ConfigMaps work the same way: change the config, restart the pod, get new behavior.

---

## Creating ConfigMaps

### From Literals

```bash
# Single key-value
k create configmap app-config --from-literal=APP_ENV=production

# Multiple key-values
k create configmap app-config \
  --from-literal=APP_ENV=production \
  --from-literal=LOG_LEVEL=info \
  --from-literal=MAX_CONNECTIONS=100

# View the result
k get configmap app-config -o yaml
```

### From Files

```bash
# Create a config file
echo "database.host=db.example.com
database.port=5432
database.name=myapp" > app.properties

# Create ConfigMap from file
k create configmap app-config --from-file=app.properties

# Custom key name
k create configmap app-config --from-file=config.properties=app.properties

# Multiple files
k create configmap app-config \
  --from-file=app.properties \
  --from-file=logging.properties
```

### From Directories

```bash
# All files in directory become keys
k create configmap app-config --from-file=./config-dir/
```

### From YAML

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: production
  LOG_LEVEL: info
  app.properties: |
    database.host=db.example.com
    database.port=5432
    database.name=myapp
```

---

## Consuming ConfigMaps

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
    - name: APP_ENVIRONMENT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: APP_ENV
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
    - configMapRef:
        name: app-config
```

### As Volume Files

**Mount entire ConfigMap:**
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
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
```

**Mount specific keys:**
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
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: application.properties
```

**Mount to specific file:**
```yaml
volumeMounts:
- name: config-volume
  mountPath: /etc/config/app.conf
  subPath: app.properties
```

---

## ConfigMap Patterns

### Environment-Specific Config

```bash
# Development
k create configmap app-config \
  --from-literal=APP_ENV=development \
  --from-literal=DEBUG=true \
  -n development

# Production
k create configmap app-config \
  --from-literal=APP_ENV=production \
  --from-literal=DEBUG=false \
  -n production
```

### Configuration Files

```bash
# nginx.conf
cat << 'EOF' > nginx.conf
server {
    listen 80;
    server_name localhost;
    location / {
        root /usr/share/nginx/html;
    }
}
EOF

k create configmap nginx-config --from-file=nginx.conf

# Mount in pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx-custom
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
  volumes:
  - name: config
    configMap:
      name: nginx-config
EOF
```

---

## ConfigMap Updates

### Behavior by Consumption Method

| Method | Update Behavior |
|--------|-----------------|
| Environment variables | **NOT updated** - requires pod restart |
| Volume mounts | **Updated automatically** (kubelet sync period ~1 min) |
| subPath mounts | **NOT updated** - requires pod restart |

### Forcing Updates

```bash
# Restart pods to pick up env var changes
k rollout restart deployment/myapp

# For volume-mounted configs, wait or force sync
# Pods auto-update within kubelet sync period
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    ConfigMap Usage                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap: app-config                                      │
│  ┌─────────────────────────────────────┐                   │
│  │ APP_ENV: production                 │                   │
│  │ LOG_LEVEL: info                     │                   │
│  │ app.properties: |                   │                   │
│  │   database.host=db.example.com      │                   │
│  │   database.port=5432                │                   │
│  └─────────────────────────────────────┘                   │
│           │                    │                           │
│           ▼                    ▼                           │
│    ┌──────────────┐    ┌──────────────┐                   │
│    │   envFrom    │    │   volume     │                   │
│    │              │    │   mount      │                   │
│    │  $APP_ENV    │    │              │                   │
│    │  $LOG_LEVEL  │    │ /etc/config/ │                   │
│    └──────────────┘    │  app.properties│                  │
│                        └──────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

```bash
# Create
k create configmap NAME --from-literal=KEY=VALUE
k create configmap NAME --from-file=FILE
k create configmap NAME --from-file=DIR/

# View
k get configmap NAME -o yaml
k describe configmap NAME

# Edit
k edit configmap NAME

# Delete
k delete configmap NAME
```

---

## Did You Know?

- **ConfigMaps have a 1MB size limit.** For larger configurations, consider mounting external storage or using init containers.

- **ConfigMap data is stored in etcd unencrypted** (unlike Secrets which can be encrypted at rest). Don't put sensitive data in ConfigMaps.

- **The `immutable: true` field** (Kubernetes 1.21+) prevents accidental changes and improves cluster performance by reducing watch load.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Expecting env vars to update | App uses stale config | Restart pod after ConfigMap changes |
| Using subPath expecting updates | subPath doesn't auto-update | Use full volume mount or restart |
| Storing secrets in ConfigMaps | Data visible in plain text | Use Secrets for sensitive data |
| Not namespacing ConfigMaps | Config leaks across environments | Create per-namespace ConfigMaps |
| Typo in key name | Pod won't start or gets wrong config | Use `k describe cm` to verify |

---

## Quiz

1. **How do you create a ConfigMap from multiple key-value pairs?**
   <details>
   <summary>Answer</summary>
   `kubectl create configmap NAME --from-literal=KEY1=VAL1 --from-literal=KEY2=VAL2`
   </details>

2. **How do you inject all ConfigMap keys as environment variables?**
   <details>
   <summary>Answer</summary>
   Use `envFrom` with `configMapRef`:
   ```yaml
   envFrom:
   - configMapRef:
       name: configmap-name
   ```
   </details>

3. **Do environment variables from ConfigMaps update automatically?**
   <details>
   <summary>Answer</summary>
   No. Environment variables are set at pod startup and don't update. You must restart the pod to pick up changes.
   </details>

4. **How do you mount only specific keys from a ConfigMap?**
   <details>
   <summary>Answer</summary>
   Use `items` in the volume definition:
   ```yaml
   volumes:
   - name: config
     configMap:
       name: my-config
       items:
       - key: specific-key
         path: filename
   ```
   </details>

---

## Hands-On Exercise

**Task**: Create and consume ConfigMaps multiple ways.

**Setup:**
```bash
# Create ConfigMap from literals
k create configmap web-config \
  --from-literal=APP_COLOR=blue \
  --from-literal=APP_MODE=production

# Verify
k get configmap web-config -o yaml
```

**Part 1: Environment Variables**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: env-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo Color: $APP_COLOR, Mode: $APP_MODE && sleep 3600']
    envFrom:
    - configMapRef:
        name: web-config
EOF

# Verify environment
k logs env-pod
```

**Part 2: Volume Mount**
```bash
# Create config file
k create configmap nginx-index --from-literal=index.html='<h1>Hello from ConfigMap</h1>'

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: vol-pod
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
  volumes:
  - name: html
    configMap:
      name: nginx-index
EOF

# Test
k exec vol-pod -- cat /usr/share/nginx/html/index.html
```

**Cleanup:**
```bash
k delete pod env-pod vol-pod
k delete configmap web-config nginx-index
```

---

## Practice Drills

### Drill 1: Create from Literals (Target: 1 minute)

```bash
k create configmap drill1 --from-literal=KEY1=value1 --from-literal=KEY2=value2
k get cm drill1 -o yaml
k delete cm drill1
```

### Drill 2: Create from File (Target: 2 minutes)

```bash
echo "setting1=on
setting2=off" > /tmp/settings.conf

k create configmap drill2 --from-file=/tmp/settings.conf
k get cm drill2 -o yaml
k delete cm drill2
```

### Drill 3: Environment Variables (Target: 3 minutes)

```bash
k create configmap drill3 --from-literal=DB_HOST=localhost --from-literal=DB_PORT=5432

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'env | grep DB && sleep 3600']
    envFrom:
    - configMapRef:
        name: drill3
EOF

k logs drill3
k delete pod drill3 cm drill3
```

### Drill 4: Volume Mount (Target: 3 minutes)

```bash
k create configmap drill4 --from-literal=config.json='{"debug": true}'

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill4
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'cat /config/config.json && sleep 3600']
    volumeMounts:
    - name: cfg
      mountPath: /config
  volumes:
  - name: cfg
    configMap:
      name: drill4
EOF

k logs drill4
k delete pod drill4 cm drill4
```

### Drill 5: Specific Key Mount (Target: 3 minutes)

```bash
k create configmap drill5 \
  --from-literal=app.conf='main config' \
  --from-literal=log.conf='log config'

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill5
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls /config && cat /config/application.conf && sleep 3600']
    volumeMounts:
    - name: cfg
      mountPath: /config
  volumes:
  - name: cfg
    configMap:
      name: drill5
      items:
      - key: app.conf
        path: application.conf
EOF

k logs drill5
k delete pod drill5 cm drill5
```

### Drill 6: Complete Scenario (Target: 5 minutes)

**Scenario**: Deploy nginx with custom configuration.

```bash
# Create nginx config
cat << 'NGINX' > /tmp/nginx.conf
server {
    listen 8080;
    location / {
        return 200 'Custom Config Works!\n';
        add_header Content-Type text/plain;
    }
}
NGINX

k create configmap drill6-nginx --from-file=/tmp/nginx.conf

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill6
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
  volumes:
  - name: nginx-config
    configMap:
      name: drill6-nginx
EOF

# Test (wait for pod ready)
k wait --for=condition=Ready pod/drill6 --timeout=30s
k exec drill6 -- curl -s localhost:8080

k delete pod drill6 cm drill6-nginx
```

---

## Next Module

[Module 4.2: Secrets](../module-4.2-secrets/) - Manage sensitive data securely.
