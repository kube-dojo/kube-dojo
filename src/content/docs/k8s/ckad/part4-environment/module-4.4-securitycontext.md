---
title: "Module 4.4: SecurityContexts"
slug: k8s/ckad/part4-environment/module-4.4-securitycontext
sidebar:
  order: 4
lab:
  id: ckad-4.4-securitycontext
  url: https://killercoda.com/kubedojo/scenario/ckad-4.4-securitycontext
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Important for security, multiple settings
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Basic Linux user/group concepts, Module 1.1 (Pods)

---

## Learning Outcomes

After completing this module, you will be able to:
- **Configure** SecurityContexts at pod and container level including `runAsUser`, `runAsNonRoot`, and `readOnlyRootFilesystem`
- **Explain** the difference between pod-level and container-level security settings and their precedence
- **Evaluate** whether a pod meets security requirements by inspecting its SecurityContext configuration
- **Debug** permission denied errors caused by SecurityContext restrictions on file access or capabilities

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

> **Pause and predict**: A pod has `runAsNonRoot: true` set at the pod level, but one container sets `runAsUser: 0` (root). Will the container start? Which setting wins?

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

> **Stop and think**: You set `readOnlyRootFilesystem: true` on a container. The application needs to write temporary files to `/tmp`. How would you solve this without disabling the read-only filesystem?

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

1. **A security team requires all pods to run as non-root. A developer deploys a pod with `runAsNonRoot: true` but the container immediately fails with "container has runAsNonRoot and image will run as root." The developer is confused because they set the flag. What is the problem and how do they fix it?**
   <details>
   <summary>Answer</summary>
   `runAsNonRoot: true` is a validation check, not a configuration — it tells Kubernetes to reject the container if it would run as root, but it doesn't change the user. The container image (e.g., nginx) defaults to running as root (UID 0), so the check fails. The fix is to also set `runAsUser: 1000` (or another non-zero UID) in the securityContext, which forces the container to run as that user regardless of the image default. Some images may need additional adjustments (file permissions, writable directories) to work as non-root.
   </details>

2. **After enabling `readOnlyRootFilesystem: true` on an nginx pod, the container crashes on startup with "Permission denied" errors when trying to write to `/var/cache/nginx/`. How do you fix this while keeping the read-only filesystem security benefit?**
   <details>
   <summary>Answer</summary>
   Mount emptyDir volumes at the paths where the application needs to write. For nginx, you typically need writable directories at `/var/cache/nginx`, `/var/run`, and `/tmp`. Add each as an emptyDir volume mount. This gives you the security benefit of an immutable root filesystem (attackers can't modify application binaries or config) while still allowing the application to write temporary data to specific, ephemeral locations. The emptyDir volumes are cleaned up when the pod is deleted.
   </details>

3. **A pod has `securityContext.runAsUser: 1000` at the pod level. Container A does not set any securityContext. Container B sets `runAsUser: 2000`. What user does each container run as, and what user owns files in a volume mounted with `fsGroup: 3000`?**
   <details>
   <summary>Answer</summary>
   Container A runs as UID 1000 (inherits from the pod-level setting). Container B runs as UID 2000 (container-level overrides pod-level). Files in the volume are owned by GID 3000 (the fsGroup), and both containers have GID 3000 as a supplementary group, so both can access the volume files. The key takeaway is that container-level securityContext overrides pod-level for that specific container, but fsGroup is pod-level only and applies to all containers' volume mounts.
   </details>

4. **A developer needs their container to perform network configuration (setting up iptables rules). The security team won't allow `privileged: true`. What is the minimum-privilege approach to grant only the network capabilities needed?**
   <details>
   <summary>Answer</summary>
   Use Linux capabilities to grant only what's needed: drop all capabilities first with `capabilities.drop: ["ALL"]`, then add only `NET_ADMIN` (for network configuration and iptables). This follows the principle of least privilege — the container gets network administration rights without full root/privileged access. `privileged: true` grants every capability plus host device access, which is vastly more access than needed. Always prefer targeted capabilities over privileged mode. If the container also needs to bind to low ports (< 1024), add `NET_BIND_SERVICE` as well.
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
