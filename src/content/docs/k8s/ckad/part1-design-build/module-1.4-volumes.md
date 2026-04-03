---
title: "Module 1.4: Volumes for Developers"
slug: k8s/ckad/part1-design-build/module-1.4-volumes
sidebar:
  order: 4
lab:
  id: ckad-1.4-volumes
  url: https://killercoda.com/kubedojo/scenario/ckad-1.4-volumes
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Essential for stateful applications
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 1.3 (Multi-Container Pods)

---

## Learning Outcomes

After completing this module, you will be able to:
- **Create** pods with emptyDir, hostPath, and PersistentVolumeClaim volumes
- **Configure** volume mounts to share data between containers in the same pod
- **Debug** volume mount errors including permission issues and missing PVCs
- **Explain** the difference between ephemeral and persistent volumes and when to use each

---

## Why This Module Matters

Containers are ephemeral—when they restart, all data is lost. For real applications, you need persistent storage: databases need durable data, applications need shared files, and containers need ways to exchange data.

The CKAD tests practical volume usage: mounting ConfigMaps, sharing data between containers, and using persistent storage. You won't manage StorageClasses (that's CKA), but you will use PersistentVolumeClaims.

> **The Desk Drawer Analogy**
>
> A container's filesystem is like a whiteboard—useful while you're there, but wiped when you leave. An `emptyDir` volume is like a shared table in a meeting room—everyone in the meeting can use it, but it's cleared when the meeting ends. A PersistentVolume is like your desk drawer—it's yours, persists between workdays, and contains your important files.

---

## Volume Types for Developers

### Quick Reference

| Volume Type | Persistence | Sharing | Use Case |
|-------------|-------------|---------|----------|
| `emptyDir` | Pod lifetime | Between containers | Scratch space, caches |
| `hostPath` | Node lifetime | No | Node access (dev only) |
| `configMap` | Cluster lifetime | Read-only | Configuration files |
| `secret` | Cluster lifetime | Read-only | Sensitive data |
| `persistentVolumeClaim` | Beyond pod | Depends | Databases, stateful apps |
| `projected` | Varies | Read-only | Combine multiple sources |

---

## emptyDir: Temporary Shared Storage

An `emptyDir` is created when a Pod starts and deleted when the Pod is removed. Perfect for:
- Sharing files between containers
- Scratch space for computation
- Caches

### Basic emptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: emptydir-demo
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "echo 'Hello' > /data/message && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /data
  - name: reader
    image: busybox
    command: ["sh", "-c", "cat /data/message && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /data
  volumes:
  - name: shared
    emptyDir: {}
```

### Memory-Backed emptyDir

For high-speed scratch space:

```yaml
volumes:
- name: cache
  emptyDir:
    medium: Memory      # Uses RAM instead of disk
    sizeLimit: 100Mi    # Limit memory usage
```

---

## ConfigMap Volumes

Mount ConfigMaps as files. Each key becomes a file.

### Create ConfigMap

```bash
# From literals
k create configmap app-config \
  --from-literal=log_level=debug \
  --from-literal=api_url=http://api.example.com

# From file
k create configmap nginx-config --from-file=nginx.conf
```

### Mount as Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-demo
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "cat /config/log_level && sleep 3600"]
    volumeMounts:
    - name: config
      mountPath: /config
  volumes:
  - name: config
    configMap:
      name: app-config
```

Result:
```
/config/
├── log_level     # Contains "debug"
└── api_url       # Contains "http://api.example.com"
```

### Mount Specific Keys

```yaml
volumes:
- name: config
  configMap:
    name: app-config
    items:
    - key: log_level
      path: logging/level.txt   # Custom path
```

### SubPath: Mount Single File Without Overwriting

```yaml
volumeMounts:
- name: config
  mountPath: /etc/app/config.yaml    # Specific file
  subPath: config.yaml               # Key from ConfigMap
```

---

## Secret Volumes

Like ConfigMaps but for sensitive data. Mounted files are tmpfs (memory-backed).

### Create Secret

```bash
k create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secret123
```

### Mount Secret

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-demo
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "cat /secrets/password && sleep 3600"]
    volumeMounts:
    - name: db-secrets
      mountPath: /secrets
      readOnly: true
  volumes:
  - name: db-secrets
    secret:
      secretName: db-creds
```

### File Permissions

```yaml
volumes:
- name: db-secrets
  secret:
    secretName: db-creds
    defaultMode: 0400    # Read-only by owner
```

---

## PersistentVolumeClaim (PVC)

For data that survives pod restarts. As a developer, you request storage with a PVC; the cluster provisions it.

### Create PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
  - ReadWriteOnce         # RWO, ROX, RWX
  resources:
    requests:
      storage: 1Gi
  # storageClassName: fast  # Optional: specific class
```

### Access Modes

| Mode | Short | Description |
|------|-------|-------------|
| `ReadWriteOnce` | RWO | One node can mount read-write |
| `ReadOnlyMany` | ROX | Many nodes can mount read-only |
| `ReadWriteMany` | RWX | Many nodes can mount read-write |

### Use PVC in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pvc-demo
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: data-pvc
```

### Imperative PVC Creation

```bash
# No direct imperative command, but quick YAML
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
EOF
```

---

## Projected Volumes

Combine multiple sources into one mount point.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-demo
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "ls -la /projected && sleep 3600"]
    volumeMounts:
    - name: all-config
      mountPath: /projected
  volumes:
  - name: all-config
    projected:
      sources:
      - configMap:
          name: app-config
      - secret:
          name: app-secrets
      - downwardAPI:
          items:
          - path: "labels"
            fieldRef:
              fieldPath: metadata.labels
```

---

## Common Volume Patterns

### Pattern 1: Shared Scratch Space

```yaml
spec:
  containers:
  - name: processor
    image: processor
    volumeMounts:
    - name: scratch
      mountPath: /tmp/work
  - name: uploader
    image: uploader
    volumeMounts:
    - name: scratch
      mountPath: /data
  volumes:
  - name: scratch
    emptyDir: {}
```

### Pattern 2: Config + Secrets

```yaml
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: config
      mountPath: /etc/app
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: app-config
  - name: secrets
    secret:
      secretName: app-secrets
```

### Pattern 3: Init Container Prepares Data

```yaml
spec:
  initContainers:
  - name: download
    image: curlimages/curl
    command: ["curl", "-o", "/data/app.tar", "http://example.com/app.tar"]
    volumeMounts:
    - name: app-data
      mountPath: /data
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: app-data
      mountPath: /app
  volumes:
  - name: app-data
    emptyDir: {}
```

---

## Troubleshooting Volumes

### Check Volume Status

```bash
# Pod volumes
k describe pod myapp | grep -A10 Volumes

# PVC status
k get pvc

# PVC details
k describe pvc data-pvc
```

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Pod stuck Pending | PVC not bound | Check PV availability |
| Permission denied | Wrong mode/user | Set `securityContext.fsGroup` |
| File not found | Wrong mountPath | Verify paths match |
| ConfigMap not updating | Mounted files cached | Restart pod or use subPath carefully |

### Fix Permission Issues

```yaml
spec:
  securityContext:
    fsGroup: 1000    # Group ID for volume files
  containers:
  - name: app
    image: myapp
    securityContext:
      runAsUser: 1000
```

---

## Did You Know?

- **ConfigMaps and Secrets are eventually consistent.** When you update them, pods see changes within a minute—but NOT if you used `subPath` mounting. SubPath mounts are snapshots that don't auto-update.

- **emptyDir uses node disk by default** but can use RAM (`medium: Memory`). RAM-backed volumes are faster but count against container memory limits.

- **PVC deletion is blocked** if a pod is using it. Delete the pod first, then the PVC. Set `persistentVolumeReclaimPolicy: Delete` to auto-delete underlying storage when PVC is removed.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting `volumeMounts` | Volume defined but not mounted | Add mount to container |
| Wrong `mountPath` | Files appear in unexpected location | Double-check paths |
| Using `subPath` for live updates | Updates won't propagate | Avoid subPath or restart pod |
| PVC with wrong access mode | Multi-node apps fail | Use RWX for shared access |
| Missing volume definition | Pod fails to start | Define volume in `spec.volumes` |

---

## Quiz

1. **What happens to data in an emptyDir when the pod is deleted?**
   <details>
   <summary>Answer</summary>
   The data is deleted. emptyDir storage is tied to pod lifecycle—it's created when the pod starts and deleted when the pod is removed.
   </details>

2. **How do you mount only one key from a ConfigMap as a specific filename?**
   <details>
   <summary>Answer</summary>
   Use the `items` field with `path`:
   ```yaml
   volumes:
   - name: config
     configMap:
       name: my-config
       items:
       - key: app.conf
         path: application.conf
   ```
   </details>

3. **What access mode allows multiple nodes to mount a volume read-write?**
   <details>
   <summary>Answer</summary>
   `ReadWriteMany` (RWX). This is required for shared storage across pods on different nodes, like NFS or cloud file shares.
   </details>

4. **How do containers in the same pod share files?**
   <details>
   <summary>Answer</summary>
   Through a shared volume. Define an `emptyDir` (or other volume type) and mount it in both containers. They can then read/write the same files.
   </details>

---

## Hands-On Exercise

**Task**: Create a complete application with multiple volume types.

**Scenario**: Build an app that:
1. Uses ConfigMap for configuration
2. Uses Secret for credentials
3. Uses emptyDir for shared cache between containers
4. Uses PVC for persistent data

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
data:
  config.json: |
    {"logLevel": "info", "cacheEnabled": true}
---
apiVersion: v1
kind: Secret
metadata:
  name: app-creds
type: Opaque
stringData:
  api-key: super-secret-key
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 100Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: volumes-app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/app
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
    - name: cache
      mountPath: /tmp/cache
    - name: data
      mountPath: /data
  - name: cache-warmer
    image: busybox
    command: ["sh", "-c", "while true; do echo 'Cache data' > /cache/warm; sleep 30; done"]
    volumeMounts:
    - name: cache
      mountPath: /cache
  volumes:
  - name: config
    configMap:
      name: app-settings
  - name: secrets
    secret:
      secretName: app-creds
  - name: cache
    emptyDir: {}
  - name: data
    persistentVolumeClaim:
      claimName: app-data
```

**Verification:**
```bash
# Apply all resources
k apply -f volumes-app.yaml

# Check pod running
k get pod volumes-app

# Verify mounts
k exec volumes-app -c app -- ls -la /etc/app
k exec volumes-app -c app -- ls -la /etc/secrets
k exec volumes-app -c app -- ls -la /tmp/cache
k exec volumes-app -c app -- ls -la /data

# Check PVC bound
k get pvc app-data

# Cleanup
k delete pod volumes-app
k delete pvc app-data
k delete configmap app-settings
k delete secret app-creds
```

---

## Practice Drills

### Drill 1: emptyDir Sharing (Target: 3 minutes)

```bash
# Create pod with shared emptyDir
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: shared-pod
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "echo hello > /shared/msg && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /shared
  - name: reader
    image: busybox
    command: ["sh", "-c", "sleep 5 && cat /shared/msg && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /shared
  volumes:
  - name: shared
    emptyDir: {}
EOF

# Verify sharing works
k logs shared-pod -c reader

# Cleanup
k delete pod shared-pod
```

### Drill 2: ConfigMap Volume (Target: 3 minutes)

```bash
# Create ConfigMap
k create configmap web-config --from-literal=index.html="Welcome to CKAD!"

# Create pod using ConfigMap
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web
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
      name: web-config
EOF

# Verify content
k exec web -- cat /usr/share/nginx/html/index.html

# Cleanup
k delete pod web
k delete cm web-config
```

### Drill 3: Secret Volume (Target: 3 minutes)

```bash
# Create Secret
k create secret generic db-pass --from-literal=password=mysecret

# Mount in pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secret-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "cat /secrets/password && sleep 3600"]
    volumeMounts:
    - name: creds
      mountPath: /secrets
      readOnly: true
  volumes:
  - name: creds
    secret:
      secretName: db-pass
EOF

# Verify secret mounted
k logs secret-pod

# Cleanup
k delete pod secret-pod
k delete secret db-pass
```

### Drill 4: PVC Usage (Target: 4 minutes)

```bash
# Create PVC
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 50Mi
EOF

# Use in pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pvc-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: test-pvc
EOF

# Check PVC bound
k get pvc test-pvc

# Write data
k exec pvc-pod -- sh -c "echo 'Persistent!' > /data/test.txt"
k exec pvc-pod -- cat /data/test.txt

# Cleanup
k delete pod pvc-pod
k delete pvc test-pvc
```

### Drill 5: Projected Volume (Target: 4 minutes)

```bash
# Create sources
k create cm proj-config --from-literal=config=value
k create secret generic proj-secret --from-literal=secret=hidden

# Create pod with projected volume
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: proj-pod
  labels:
    app: projected
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "ls -la /projected && sleep 3600"]
    volumeMounts:
    - name: combined
      mountPath: /projected
  volumes:
  - name: combined
    projected:
      sources:
      - configMap:
          name: proj-config
      - secret:
          name: proj-secret
EOF

# Check combined files
k exec proj-pod -- ls /projected

# Cleanup
k delete pod proj-pod
k delete cm proj-config
k delete secret proj-secret
```

### Drill 6: Complete Volume Challenge (Target: 6 minutes)

**Build from memory—no hints:**

Create a pod `data-processor` that:
1. Init container downloads "data" (simulate with echo)
2. Main container processes data (nginx)
3. Sidecar logs processing status
4. Uses emptyDir for shared data
5. Mounts a ConfigMap with processing settings

<details>
<summary>Solution</summary>

```bash
# Create ConfigMap
k create cm processing-config --from-literal=mode=fast

# Create pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-processor
spec:
  initContainers:
  - name: downloader
    image: busybox
    command: ["sh", "-c", "echo 'Downloaded data' > /data/input.txt"]
    volumeMounts:
    - name: data
      mountPath: /data
  containers:
  - name: processor
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
    - name: config
      mountPath: /etc/config
  - name: logger
    image: busybox
    command: ["sh", "-c", "while true; do echo Processing $(cat /data/input.txt); sleep 5; done"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
  - name: config
    configMap:
      name: processing-config
EOF

# Verify
k get pod data-processor
k logs data-processor -c logger
k exec data-processor -c processor -- cat /etc/config/mode

# Cleanup
k delete pod data-processor
k delete cm processing-config
```

</details>

---

## Next Module

[Part 1 Cumulative Quiz](../part1-cumulative-quiz/) - Test your Application Design and Build knowledge.
