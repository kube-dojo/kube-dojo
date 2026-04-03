---
title: "Module 4.1: Volumes"
slug: k8s/cka/part4-storage/module-4.1-volumes
sidebar:
  order: 2
lab:
  id: cka-4.1-volumes
  url: https://killercoda.com/kubedojo/scenario/cka-4.1-volumes
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Foundation for all storage concepts
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 2.1 (Pods), Module 2.7 (ConfigMaps & Secrets)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Configure** emptyDir, hostPath, and projected volumes and explain when to use each
- **Mount** volumes into containers at specific paths with read-only or read-write access
- **Explain** volume lifecycle (tied to pod, not container) and data persistence guarantees
- **Debug** volume mount failures by checking events, paths, and permissions

---

## Why This Module Matters

Containers are ephemeral - when they restart, all data is lost. Volumes solve this problem by providing persistent or shared storage that outlives container restarts. On the CKA exam, you'll need to configure various volume types to share data between containers, cache temporary files, and inject configuration.

> **The Filing Cabinet Analogy**
>
> Think of a container as a desk with drawers that get emptied every time you leave work. A volume is like a filing cabinet in the corner - it keeps your files even when you're gone. Some cabinets are shared between desks (emptyDir), some are building-wide storage (PV), and some are just mirrors of the company directory (configMap/secret projected volumes).

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand why volumes are needed
- Use emptyDir for temporary shared storage
- Use hostPath for node-level storage (and know its risks)
- Use projected volumes for configuration injection
- Understand volume lifecycle and when data persists

---

## Did You Know?

- **emptyDir in memory**: You can back emptyDir with RAM instead of disk using `medium: Memory` - great for sensitive temp files that should never hit disk
- **Projected volumes combine 4 sources**: configMap, secret, downwardAPI, and serviceAccountToken can all be projected into a single directory
- **hostPath is banned in production**: Most security policies (including Pod Security Standards) block hostPath because it exposes the node filesystem to pods

---

## Part 1: Understanding Volumes

### 1.1 The Container Storage Problem

Containers have an isolated filesystem. When a container crashes and restarts:

```
┌──────────────────────────────────────────────────────────────┐
│ Container Restart = Data Loss                                 │
│                                                               │
│   Container v1              Container v2 (after restart)     │
│   ┌─────────────────┐       ┌─────────────────┐              │
│   │ /app            │       │ /app            │              │
│   │ ├── config.yml  │  ──→  │ ├── config.yml  │ (from image) │
│   │ └── data/       │       │ └── data/       │              │
│   │     └── cache   │       │     └── (empty!)│              │
│   └─────────────────┘       └─────────────────┘              │
│                                                               │
│   Runtime data is GONE after restart                          │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 How Volumes Solve This

Volumes provide storage that exists outside the container's filesystem:

```
┌──────────────────────────────────────────────────────────────┐
│ With Volumes = Data Persists                                  │
│                                                               │
│   Container v1              Container v2 (after restart)     │
│   ┌─────────────────┐       ┌─────────────────┐              │
│   │ /app            │       │ /app            │              │
│   │ ├── config.yml  │       │ ├── config.yml  │              │
│   │ └── data/ ──────┼───┐   │ └── data/ ──────┼───┐          │
│   └─────────────────┘   │   └─────────────────┘   │          │
│                         │                         │          │
│                         ▼                         ▼          │
│                    ┌────────────────────────────────┐        │
│                    │        Volume (shared)          │        │
│                    │    └── cache (still here!)     │        │
│                    └────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

### 1.3 Volume Types Overview

| Volume Type | Lifetime | Use Case | Data Persistence |
|-------------|----------|----------|------------------|
| emptyDir | Pod lifetime | Temp storage, inter-container sharing | Lost when pod deleted |
| hostPath | Node lifetime | Node-level data, DaemonSets | Persists on node |
| configMap | ConfigMap lifetime | Config files | Managed by ConfigMap |
| secret | Secret lifetime | Credentials | Managed by Secret |
| projected | Source lifetime | Multiple sources in one mount | Depends on sources |
| persistentVolumeClaim | PV lifetime | Persistent data | Survives pod deletion |
| image | Image lifetime | OCI image content as read-only volume (K8s 1.35+) | Read-only, pulled from registry |

> **New in K8s 1.35: Image Volumes (GA)**
>
> Image volumes let you pull an OCI image from a registry and mount its contents directly as a read-only volume. No init containers or bootstrap scripts needed. Perfect for ML models, config bundles, or static assets:
>
> ```yaml
> volumes:
> - name: model-data
>   image:
>     reference: registry.example.com/ml-models/bert:v2
>     pullPolicy: IfNotPresent
> ```

---

## Part 2: emptyDir Volumes

### 2.1 What Is emptyDir?

An emptyDir volume is created when a pod is assigned to a node and exists as long as the pod runs on that node. It starts empty, hence the name.

**Key characteristics**:
- Created when pod starts on a node
- Deleted when pod is removed from node (any reason)
- Shared between all containers in the pod
- Can be backed by disk or memory (tmpfs)

### 2.2 Basic emptyDir Usage

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-data
spec:
  containers:
  - name: writer
    image: busybox
    command: ['sh', '-c', 'echo "Hello from writer" > /data/message; sleep 3600']
    volumeMounts:
    - name: shared-storage
      mountPath: /data
  - name: reader
    image: busybox
    command: ['sh', '-c', 'sleep 5; cat /data/message; sleep 3600']
    volumeMounts:
    - name: shared-storage
      mountPath: /data
  volumes:
  - name: shared-storage
    emptyDir: {}
```

### 2.3 emptyDir with Memory Backing

For sensitive temporary data or faster I/O:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: memory-backed
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'sleep 3600']
    volumeMounts:
    - name: tmpfs-volume
      mountPath: /cache
  volumes:
  - name: tmpfs-volume
    emptyDir:
      medium: Memory        # Uses RAM instead of disk
      sizeLimit: 100Mi      # Important! Limit memory usage
```

**When to use Memory-backed emptyDir**:
- Temporary credentials that shouldn't touch disk
- High-speed caching
- Scratch space for computation

**Warning**: Memory-backed volumes count against the container's memory limit!

### 2.4 emptyDir Size Limits

```yaml
volumes:
- name: cache
  emptyDir:
    sizeLimit: 500Mi    # Limit disk usage
```

If the pod exceeds the size limit, it will be evicted.

---

## Part 3: hostPath Volumes

### 3.1 What Is hostPath?

hostPath mounts a file or directory from the host node's filesystem into the pod.

```
┌─────────────────────────────────────────────────────────────┐
│                         Node                                 │
│                                                              │
│   Node Filesystem           Pod                              │
│   ┌─────────────────┐       ┌─────────────────────────┐     │
│   │ /var/log/       │       │  Container              │     │
│   │   └── pods/     │◄──────│  /host-logs/ ◄────┐     │     │
│   │       └── *.log │       │                   │     │     │
│   └─────────────────┘       │  volumeMounts:    │     │     │
│                             │    mountPath:     │     │     │
│   /data/                    │      /host-logs ──┘     │     │
│   └── myapp/        ◄───────│                         │     │
│       └── config    │       └─────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 hostPath Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-example
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /host-data; sleep 3600']
    volumeMounts:
    - name: host-volume
      mountPath: /host-data
      readOnly: true           # Good practice for security
  volumes:
  - name: host-volume
    hostPath:
      path: /var/log           # Path on the node
      type: Directory          # Must be a directory
```

### 3.3 hostPath Types

| Type | Behavior |
|------|----------|
| `""` (empty) | No checks before mount |
| `DirectoryOrCreate` | Create directory if missing |
| `Directory` | Must exist, must be directory |
| `FileOrCreate` | Create file if missing |
| `File` | Must exist, must be file |
| `Socket` | Must exist, must be UNIX socket |
| `CharDevice` | Must exist, must be char device |
| `BlockDevice` | Must exist, must be block device |

### 3.4 hostPath Security Risks

**Why hostPath is dangerous**:

```yaml
# DANGEROUS - Never do this in production!
volumes:
- name: root-access
  hostPath:
    path: /                    # Access to entire node filesystem!
    type: Directory
```

**Risks**:
- Container escape to node
- Reading sensitive node files (/etc/shadow, kubelet creds)
- Writing malicious files to node
- Modifying node configuration

**Safe uses of hostPath**:
- DaemonSets that need node access (log collectors, monitoring agents)
- Node-level debugging (temporary)
- Docker socket access for CI/CD (use with extreme caution)

### 3.5 hostPath in DaemonSets

Legitimate hostPath use - log collection:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      name: log-collector
  template:
    metadata:
      labels:
        name: log-collector
    spec:
      containers:
      - name: collector
        image: fluentd:latest
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true          # Read-only for safety
        - name: containers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
          type: Directory
      - name: containers
        hostPath:
          path: /var/lib/docker/containers
          type: Directory
```

---

## Part 4: Projected Volumes

### 4.1 What Are Projected Volumes?

Projected volumes combine multiple volume sources into a single directory. This is useful when you need configMaps, secrets, and downwardAPI data in one location.

```
┌──────────────────────────────────────────────────────────────┐
│ Projected Volume                                              │
│                                                               │
│   Sources:                        Mount Point:                │
│   ┌─────────────┐                 /etc/config/                │
│   │ ConfigMap A │─────┐           ├── app.conf     (from A)   │
│   └─────────────┘     │           ├── db.conf      (from A)   │
│   ┌─────────────┐     │           ├── password     (from B)   │
│   │ Secret B    │─────┼────────→  ├── api-key      (from B)   │
│   └─────────────┘     │           ├── labels       (from C)   │
│   ┌─────────────┐     │           └── annotations  (from C)   │
│   │ DownwardAPI │─────┘                                       │
│   └─────────────┘                                             │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Projected Volume Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-volume-demo
  labels:
    app: demo
    version: v1
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /etc/config; sleep 3600']
    volumeMounts:
    - name: all-config
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: all-config
    projected:
      sources:
      # Source 1: ConfigMap
      - configMap:
          name: app-config
          items:
          - key: app.properties
            path: app.conf
      # Source 2: Secret
      - secret:
          name: app-secrets
          items:
          - key: password
            path: credentials/password
      # Source 3: Downward API
      - downwardAPI:
          items:
          - path: labels
            fieldRef:
              fieldPath: metadata.labels
          - path: cpu-limit
            resourceFieldRef:
              containerName: app
              resource: limits.cpu
```

### 4.3 Service Account Token Projection

Modern Kubernetes uses projected service account tokens instead of legacy tokens:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: service-account-projection
spec:
  serviceAccountName: my-service-account
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
      readOnly: true
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600     # Short-lived token
          audience: api               # Intended audience
```

### 4.4 Projected Volume Use Cases

| Use Case | Sources Combined |
|----------|------------------|
| App config bundle | configMap + secret |
| Pod identity | serviceAccountToken + downwardAPI |
| Full config injection | configMap + secret + downwardAPI |
| Sidecar config | Multiple configMaps |

---

## Part 5: ConfigMap and Secret Volumes

### 5.1 ConfigMap as Volume

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
      listen 80;
      location / {
        root /usr/share/nginx/html;
      }
    }
---
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: nginx-config
      # Optional: select specific keys
      items:
      - key: nginx.conf
        path: default.conf     # Rename the file
```

### 5.2 Secret as Volume

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-certs
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
---
apiVersion: v1
kind: Pod
metadata:
  name: tls-app
spec:
  containers:
  - name: app
    image: nginx:1.25
    volumeMounts:
    - name: certs
      mountPath: /etc/tls
      readOnly: true
  volumes:
  - name: certs
    secret:
      secretName: tls-certs
      defaultMode: 0400       # Restrictive permissions
```

### 5.3 Auto-Updates for ConfigMap/Secret Volumes

When mounted as volumes (not env vars), ConfigMaps and Secrets update automatically:

```
┌──────────────────────────────────────────────────────────────┐
│ Update Behavior                                               │
│                                                               │
│ ConfigMap/Secret updated ───→ Volume updated (within ~1 min) │
│                                                               │
│ ⚠️  Caveats:                                                  │
│     • Uses atomic symlink swap                                │
│     • subPath mounts do NOT auto-update                       │
│     • Application must detect and reload                      │
│     • kubelet sync period affects delay                       │
└──────────────────────────────────────────────────────────────┘
```

### 5.4 subPath Mounts (No Auto-Update)

When you need to mount a single file into an existing directory:

```yaml
volumeMounts:
- name: config
  mountPath: /etc/nginx/nginx.conf    # Single file
  subPath: nginx.conf                  # Key from ConfigMap
  readOnly: true
```

**Warning**: subPath mounts don't receive updates when the ConfigMap/Secret changes!

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| emptyDir for persistent data | Data lost when pod deleted | Use PersistentVolumeClaim |
| hostPath in production | Security vulnerability | Use PVC or avoid entirely |
| No sizeLimit on emptyDir | Pod can fill node disk | Always set sizeLimit |
| subPath expecting updates | Config changes not reflected | Use full mount or restart pod |
| Memory emptyDir without limit | OOM kills | Set sizeLimit, count against memory |
| hostPath type: "" | No validation, silent failures | Use explicit type like Directory |

---

## Quiz

### Q1: Volume Lifetime
What happens to emptyDir data when a container crashes but the pod stays running?

<details>
<summary>Answer</summary>

The emptyDir data **persists**. emptyDir lifetime is tied to the pod, not the container. Only when the pod is deleted or evicted from the node is the emptyDir deleted.

</details>

### Q2: Memory-Backed emptyDir
What's the key consideration when using `emptyDir.medium: Memory`?

<details>
<summary>Answer</summary>

Memory-backed emptyDir counts against the container's memory limit. You must set a sizeLimit to prevent OOM issues, and the total must fit within your pod's memory allocation.

</details>

### Q3: hostPath Security
Why is hostPath type `""` (empty string) risky?

<details>
<summary>Answer</summary>

Type `""` performs no checks before mounting. The path might not exist, might be the wrong type (file vs directory), or might be a symlink to somewhere unexpected. Use explicit types like `Directory` or `File` for validation.

</details>

### Q4: Projected Volume Sources
Name the four types of sources that can be combined in a projected volume.

<details>
<summary>Answer</summary>

1. **configMap** - ConfigMap data
2. **secret** - Secret data
3. **downwardAPI** - Pod metadata and resource info
4. **serviceAccountToken** - Projected service account tokens

</details>

### Q5: ConfigMap Auto-Update
A ConfigMap is mounted as a volume. You update the ConfigMap. What must the application do?

<details>
<summary>Answer</summary>

The application must **detect and reload** the configuration. While Kubernetes automatically updates the files in the mounted volume (within ~1 minute), the application must watch for changes and reload - this is not automatic. Alternatively, restart the pod to pick up changes.

</details>

### Q6: subPath Behavior
Why would you use subPath, and what's the trade-off?

<details>
<summary>Answer</summary>

Use subPath to mount a single file from a ConfigMap/Secret into an existing directory without overwriting other files. The trade-off is that subPath mounts **do not auto-update** when the source changes - you must restart the pod.

</details>

---

## Hands-On Exercise: Multi-Container Volume Sharing

### Scenario
Create a pod with two containers that share data through volumes. One container writes logs, another processes them.

### Setup

```bash
# Create namespace
k create ns volume-lab

# Create the multi-container pod
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: log-processor
  namespace: volume-lab
spec:
  containers:
  # Writer container - generates logs
  - name: writer
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      i=0
      while true; do
        echo "\$(date): Log entry \$i" >> /logs/app.log
        i=\$((i+1))
        sleep 5
      done
    volumeMounts:
    - name: log-volume
      mountPath: /logs
  # Reader container - processes logs
  - name: reader
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      echo "Waiting for logs..."
      sleep 10
      tail -f /logs/app.log
    volumeMounts:
    - name: log-volume
      mountPath: /logs
      readOnly: true
  volumes:
  - name: log-volume
    emptyDir:
      sizeLimit: 50Mi
EOF
```

### Tasks

1. **Verify the pod is running**:
```bash
k get pod log-processor -n volume-lab
```

2. **Check writer is creating logs**:
```bash
k exec -n volume-lab log-processor -c writer -- cat /logs/app.log
```

3. **Check reader can see the logs**:
```bash
k logs -n volume-lab log-processor -c reader
```

4. **Verify volume sharing**:
```bash
# Write from writer
k exec -n volume-lab log-processor -c writer -- sh -c 'echo "TEST MESSAGE" >> /logs/app.log'

# Read from reader
k exec -n volume-lab log-processor -c reader -- tail -1 /logs/app.log
```

5. **Check emptyDir location on node** (for understanding):
```bash
k get pod log-processor -n volume-lab -o jsonpath='{.status.hostIP}'
# emptyDir is at /var/lib/kubelet/pods/<pod-uid>/volumes/kubernetes.io~empty-dir/log-volume
```

### Success Criteria
- [ ] Pod running with both containers
- [ ] Writer creating log entries every 5 seconds
- [ ] Reader can see logs written by writer
- [ ] Data persists across container restarts (test with `k exec ... -- kill 1`)

### Bonus Challenge

Add a third container that monitors disk usage of the shared volume and writes warnings when usage exceeds 80%.

### Cleanup

```bash
k delete ns volume-lab
```

---

## Practice Drills

Practice these scenarios for exam readiness:

### Drill 1: Create emptyDir Pod (2 min)
```bash
# Task: Create a pod with emptyDir volume mounted at /cache
# Hint: k run cache-pod --image=busybox --dry-run=client -o yaml > pod.yaml
# Then add volumes section
```

### Drill 2: Memory-Backed emptyDir (2 min)
```bash
# Task: Create emptyDir backed by RAM with 64Mi limit
# Key fields: emptyDir.medium: Memory, emptyDir.sizeLimit: 64Mi
```

### Drill 3: hostPath Read-Only (2 min)
```bash
# Task: Mount /var/log from host as read-only volume
# Important: Always use readOnly: true for hostPath when possible
```

### Drill 4: Projected Volume (3 min)
```bash
# Task: Create projected volume combining:
# - ConfigMap "app-config"
# - Secret "app-secrets"
# Mount at /etc/app
```

### Drill 5: ConfigMap Volume with Items (2 min)
```bash
# Task: Mount only "app.conf" key from ConfigMap as "config.yaml"
# Use configMap.items to select and rename
```

### Drill 6: subPath Mount (2 min)
```bash
# Task: Mount single file from ConfigMap into /etc/myapp/config.yaml
# Without overwriting other files in /etc/myapp
```

### Drill 7: Volume Sharing Between Containers (3 min)
```bash
# Task: Create pod with 2 containers sharing emptyDir
# Container 1 writes to /shared/data.txt
# Container 2 reads from /shared/data.txt
```

### Drill 8: Debug Volume Mount Issues (2 min)
```bash
# Given: Pod stuck in ContainerCreating
# Task: Identify if it's a volume mount issue
# Commands: k describe pod, check Events section
```

---

## Next Module

Continue to [Module 4.2: PersistentVolumes & PersistentVolumeClaims](../module-4.2-pv-pvc/) to learn about persistent storage that survives pod deletion.
