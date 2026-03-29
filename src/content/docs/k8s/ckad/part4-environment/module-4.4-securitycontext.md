---
title: "Module 4.4: SecurityContexts"
slug: k8s/ckad/part4-environment/module-4.4-securitycontext
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Important for security, multiple settings
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Basic Linux user/group concepts, Module 1.1 (Pods)

---

## Why This Module Matters

SecurityContexts define privilege and access control settings for pods and containers. They control who the container runs as, what capabilities it has, and what it can access on the host.

The CKAD exam tests:
- Setting user and group IDs
- Running as non-root
- Managing Linux capabilities
- File system permissions

> **The Building Security Analogy**
>
> SecurityContext is like building security policies. You control who can enter (runAsUser), what areas they can access (capabilities), whether they can change things (readOnlyRootFilesystem), and if they have master keys (privileged). Different tenants (containers) in the same building (pod) can have different access levels.

---

## SecurityContext Levels

### Pod Level vs Container Level

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-demo
spec:
  securityContext:        # Pod-level (applies to all containers)
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: app
    image: nginx
    securityContext:      # Container-level (overrides pod-level)
      runAsUser: 2000
      allowPrivilegeEscalation: false
```

**Priority**: Container-level settings override pod-level settings.

---

## Common Settings

### Run As User/Group

```yaml
securityContext:
  runAsUser: 1000       # UID to run as
  runAsGroup: 3000      # GID for the process
  fsGroup: 2000         # GID for mounted volumes
```

### Run As Non-Root

```yaml
securityContext:
  runAsNonRoot: true    # Fail if image tries to run as root
```

### Privilege Escalation

```yaml
securityContext:
  allowPrivilegeEscalation: false  # Prevent gaining more privileges
```

### Read-Only Filesystem

```yaml
securityContext:
  readOnlyRootFilesystem: true     # Container can't write to filesystem
```

### Privileged Container

```yaml
securityContext:
  privileged: true      # Full host access (DANGEROUS - rarely needed)
```

---

## Linux Capabilities

Capabilities grant specific root powers without full root:

```yaml
securityContext:
  capabilities:
    add:
    - NET_ADMIN          # Network configuration
    - SYS_TIME           # System clock
    drop:
    - ALL                # Remove all capabilities first
```

### Common Capabilities

| Capability | Purpose |
|------------|---------|
| `NET_ADMIN` | Network configuration |
| `NET_BIND_SERVICE` | Bind to ports < 1024 |
| `SYS_TIME` | Modify system clock |
| `SYS_PTRACE` | Debug other processes |
| `CHOWN` | Change file ownership |

### Best Practice: Drop All, Add Specific

```yaml
securityContext:
  capabilities:
    drop:
    - ALL
    add:
    - NET_BIND_SERVICE
```

---

## Complete Examples

### Secure Pod (Non-Root)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
```

### Pod with Volume Permissions

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-perms
spec:
  securityContext:
    runAsUser: 1000
    fsGroup: 2000         # Volume files owned by this group
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /data && sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                SecurityContext Hierarchy                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pod Security Context                                       │
│  ┌─────────────────────────────────────────────────┐       │
│  │ runAsUser: 1000                                 │       │
│  │ runAsGroup: 3000                                │       │
│  │ fsGroup: 2000 (for volumes)                     │       │
│  │                                                 │       │
│  │  Container A           Container B              │       │
│  │  ┌────────────────┐   ┌────────────────┐       │       │
│  │  │ (inherits pod) │   │ runAsUser: 2000│       │       │
│  │  │ runAsUser:1000 │   │ (overrides pod)│       │       │
│  │  │                │   │                │       │       │
│  │  │ capabilities:  │   │ readOnly: true │       │       │
│  │  │  drop: [ALL]   │   │                │       │       │
│  │  └────────────────┘   └────────────────┘       │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Verifying Security Settings

```bash
# Check what user process runs as
k exec my-pod -- id
# uid=1000 gid=3000 groups=2000

# Check file ownership in volume
k exec my-pod -- ls -la /data
# drwxrwsrwx 2 root 2000 ...

# Check capabilities
k exec my-pod -- cat /proc/1/status | grep Cap
```

---

## Quick Reference

```yaml
# Pod-level
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    runAsNonRoot: true

# Container-level
containers:
- name: app
  securityContext:
    runAsUser: 1000
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    privileged: false
    capabilities:
      drop: ["ALL"]
      add: ["NET_BIND_SERVICE"]
```

---

## Did You Know?

- **`fsGroup` only affects volume mounts.** Files created in emptyDir or PVC get this group ownership. Regular container filesystem is unaffected.

- **`runAsNonRoot: true` is a runtime check.** If the container image's default user is root (UID 0), the container fails to start.

- **Capabilities are Linux-specific.** On Windows containers, capabilities settings are ignored.

- **`readOnlyRootFilesystem` breaks many apps** that need to write temp files. Use emptyDir volumes for /tmp and similar paths.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| `runAsNonRoot` with root image | Container fails to start | Use `runAsUser: 1000` explicitly |
| `readOnlyRootFilesystem` without tmpfs | App can't write temp files | Mount emptyDir to /tmp |
| Not dropping capabilities | More attack surface | Always `drop: [ALL]`, add specific |
| Confusing pod/container context | Wrong settings applied | Container overrides pod |
| `privileged: true` unnecessarily | Security risk | Only for specific system tools |

---

## Quiz

1. **What's the difference between pod-level and container-level securityContext?**
   <details>
   <summary>Answer</summary>
   Pod-level settings apply to all containers in the pod. Container-level settings override pod-level settings for that specific container.
   </details>

2. **What does `fsGroup` control?**
   <details>
   <summary>Answer</summary>
   `fsGroup` sets the group ownership of files in mounted volumes. Processes run with this as a supplementary group.
   </details>

3. **What happens if you set `runAsNonRoot: true` but the image defaults to root?**
   <details>
   <summary>Answer</summary>
   The container fails to start. You must also set `runAsUser` to a non-zero UID.
   </details>

4. **How do you allow a container to bind to port 80 without running as root?**
   <details>
   <summary>Answer</summary>
   Add the `NET_BIND_SERVICE` capability:
   ```yaml
   capabilities:
     add: ["NET_BIND_SERVICE"]
   ```
   </details>

---

## Hands-On Exercise

**Task**: Configure security settings for pods.

**Part 1: Run as Non-Root**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nonroot-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'id && sleep 3600']
EOF

k logs nonroot-pod
# Should show: uid=1000 gid=3000 groups=3000
```

**Part 2: fsGroup Demo**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: fsgroup-pod
spec:
  securityContext:
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /data && id && sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
EOF

k logs fsgroup-pod
# Files in /data owned by group 2000
```

**Part 3: Read-Only Filesystem**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: readonly-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'touch /test 2>&1 || echo "Cannot write!"; sleep 3600']
    securityContext:
      readOnlyRootFilesystem: true
EOF

k logs readonly-pod
# Should show: Cannot write!
```

**Cleanup:**
```bash
k delete pod nonroot-pod fsgroup-pod readonly-pod
```

---

## Practice Drills

### Drill 1: Run As User (Target: 2 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill1
spec:
  securityContext:
    runAsUser: 1000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'id && sleep 3600']
EOF

k logs drill1
k delete pod drill1
```

### Drill 2: Non-Root Enforcement (Target: 2 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill2
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: busybox
    command: ['sleep', '3600']
EOF

k get pod drill2
k delete pod drill2
```

### Drill 3: Capabilities (Target: 3 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: app
    image: busybox
    command: ['sleep', '3600']
    securityContext:
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
EOF

k exec drill3 -- cat /proc/1/status | grep Cap
k delete pod drill3
```

### Drill 4: Read-Only with Temp (Target: 3 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill4
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'touch /tmp/test && echo "Wrote to /tmp" && sleep 3600']
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
EOF

k logs drill4
k delete pod drill4
```

### Drill 5: fsGroup Verification (Target: 3 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill5
spec:
  securityContext:
    fsGroup: 2000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'touch /data/file && ls -la /data && sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
EOF

k logs drill5
# File should be owned by group 2000
k delete pod drill5
```

### Drill 6: Complete Secure Pod (Target: 5 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill6
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'id && ls -la /data && sleep 3600']
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
EOF

k logs drill6
k get pod drill6 -o yaml | grep -A20 securityContext
k delete pod drill6
```

---

## Next Module

[Module 4.5: ServiceAccounts](../module-4.5-serviceaccounts/) - Configure pod identities for API access.
