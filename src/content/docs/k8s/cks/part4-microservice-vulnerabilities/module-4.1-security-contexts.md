---
title: "Module 4.1: Security Contexts"
slug: k8s/cks/part4-microservice-vulnerabilities/module-4.1-security-contexts
sidebar:
  order: 1
lab:
  id: cks-4.1-security-contexts
  url: https://killercoda.com/kubedojo/scenario/cks-4.1-security-contexts
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: CKA pod spec knowledge, basic Linux security concepts

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** pod and container security contexts to enforce non-root, read-only, and drop-all-capabilities
2. **Audit** workloads for dangerous security context settings like privileged mode and hostPID
3. **Implement** defense-in-depth security contexts combining runAsNonRoot, readOnlyRootFilesystem, and capability drops
4. **Debug** application failures caused by security context restrictions

---

## Why This Module Matters

Security contexts define privilege and access control settings for pods and containers. They're your first line of defense against container breakout—controlling whether containers run as root, can access host resources, or have elevated privileges.

CKS heavily tests security context configuration.

---

## What Security Contexts Control

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY CONTEXT SCOPE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pod-Level (spec.securityContext):                         │
│  ├── runAsUser           - UID for all containers         │
│  ├── runAsGroup          - GID for all containers         │
│  ├── fsGroup             - GID for volume ownership       │
│  ├── runAsNonRoot        - Prevent running as root        │
│  ├── supplementalGroups  - Additional group memberships   │
│  ├── seccompProfile      - Seccomp profile               │
│  └── sysctls             - Kernel parameters              │
│                                                             │
│  Container-Level (containers[].securityContext):           │
│  ├── runAsUser           - Override pod-level UID         │
│  ├── runAsGroup          - Override pod-level GID         │
│  ├── runAsNonRoot        - Container-specific check       │
│  ├── privileged          - Full host access (dangerous!)  │
│  ├── allowPrivilegeEscalation - Prevent privilege gain   │
│  ├── capabilities        - Linux capabilities             │
│  ├── readOnlyRootFilesystem - Immutable container        │
│  ├── seccompProfile      - Container-specific seccomp    │
│  └── seLinuxOptions      - SELinux labels                │
│                                                             │
│  Container settings OVERRIDE pod settings                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Critical Security Context Settings

### runAsNonRoot

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: non-root-pod
spec:
  securityContext:
    runAsNonRoot: true  # Pod-level enforcement
  containers:
  - name: app
    image: nginx
    securityContext:
      runAsUser: 1000  # Must specify non-root UID
      runAsGroup: 1000

# If image tries to run as root (UID 0), pod fails to start:
# Error: container has runAsNonRoot and image will run as root
```

### allowPrivilegeEscalation

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-escalation
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false  # Prevent setuid, setgid

# This prevents:
# - setuid binaries from gaining privileges
# - Container processes from becoming root
# - Exploits that rely on privilege escalation
```

### readOnlyRootFilesystem

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readonly-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true  # Can't write to container filesystem
    volumeMounts:
    - name: tmp
      mountPath: /tmp  # Must provide writable volume for temp files
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

### privileged (AVOID!)

```yaml
# DON'T DO THIS in production
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true  # Full access to host!

# privileged: true means:
# - Access to all host devices
# - Can load kernel modules
# - Can modify iptables
# - Can escape container entirely
# - ONLY use for system-level daemons (CNI, CSI drivers)
```

---

## Linux Capabilities

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX CAPABILITIES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Capabilities split root powers into fine-grained units:   │
│                                                             │
│  CAP_NET_BIND_SERVICE  - Bind to ports < 1024             │
│  CAP_NET_ADMIN         - Configure network interfaces      │
│  CAP_NET_RAW           - Use raw sockets (ping, etc.)     │
│  CAP_SYS_ADMIN         - Many syscalls (mount, etc.)      │
│  CAP_SYS_PTRACE        - Debug other processes            │
│  CAP_CHOWN             - Change file ownership             │
│  CAP_DAC_OVERRIDE      - Bypass file permissions          │
│  CAP_SETUID/SETGID     - Change UID/GID                   │
│  CAP_KILL              - Send signals to any process       │
│                                                             │
│  Default container capabilities (Docker):                  │
│  CHOWN, DAC_OVERRIDE, FOWNER, FSETID, KILL,              │
│  SETGID, SETUID, SETPCAP, NET_BIND_SERVICE, NET_RAW,      │
│  SYS_CHROOT, MKNOD, AUDIT_WRITE, SETFCAP                  │
│                                                             │
│  Best practice: Drop ALL, add only what's needed          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Configuring Capabilities

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: minimal-caps
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      capabilities:
        drop:
          - ALL  # Drop all capabilities
        add:
          - NET_BIND_SERVICE  # Only add what's needed
```

---

## Complete Secure Pod Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
      requests:
        memory: "64Mi"
        cpu: "250m"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

---

## Pod vs Container Security Context

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mixed-context
spec:
  securityContext:
    runAsUser: 1000        # Default for all containers
    runAsGroup: 1000
  containers:
  - name: app
    image: myapp
    # Inherits runAsUser: 1000 from pod
  - name: sidecar
    image: sidecar
    securityContext:
      runAsUser: 2000      # Overrides pod-level setting
      # This container runs as UID 2000, not 1000
```

---

## Real Exam Scenarios

### Scenario 1: Fix Pod Running as Root

```yaml
# Before (insecure)
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: nginx

# After (secure)
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
```

### Scenario 2: Add Minimal Capabilities

```bash
# Pod needs to bind to port 80 but shouldn't run as root
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-server
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: nginx
    image: nginx
    securityContext:
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE  # Allow binding to port 80
      allowPrivilegeEscalation: false
EOF
```

### Scenario 3: Make Filesystem Read-Only

```bash
# Add read-only filesystem with required writable mounts
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: readonly-nginx
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
EOF
```

---

## Debugging Security Context Issues

```bash
# Check pod's effective security context
kubectl get pod mypod -o yaml | grep -A 20 securityContext

# Check container's security context
kubectl get pod mypod -o jsonpath='{.spec.containers[0].securityContext}' | jq .

# Check if pod failed due to security context
kubectl describe pod mypod | grep -i error

# Common errors:
# "container has runAsNonRoot and image will run as root"
# "unable to write to read-only filesystem"
# "operation not permitted" (missing capability)
```

---

## Did You Know?

- **runAsNonRoot doesn't pick a UID for you.** If the image runs as root and you set runAsNonRoot: true without runAsUser, the pod fails to start.

- **Docker drops many capabilities by default.** Containers don't get the full root power set even when running as UID 0—but privileged: true gives everything back.

- **The nobody user is UID 65534** on most systems. It's a common choice for runAsUser when you don't have a specific user in mind.

- **fsGroup changes volume ownership.** When you mount a volume, Kubernetes changes the group ownership to fsGroup and sets group-writable permissions.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| runAsNonRoot without runAsUser | Pod fails if image defaults to root | Specify runAsUser: 1000 |
| Using privileged: true | Full host access | Never use unless required |
| Not dropping capabilities | Excessive permissions | Drop ALL, add what's needed |
| Forgetting emptyDir with readOnly | App can't write temp files | Mount writable volumes |
| Only setting pod-level context | Container can override | Set at both levels |

---

## Quiz

1. **What happens if you set runAsNonRoot: true but the image runs as root?**
   <details>
   <summary>Answer</summary>
   The pod fails to start with error "container has runAsNonRoot and image will run as root". You must also specify runAsUser with a non-zero UID.
   </details>

2. **What does allowPrivilegeEscalation: false prevent?**
   <details>
   <summary>Answer</summary>
   It prevents setuid/setgid binaries from gaining additional privileges and blocks execve from gaining more capabilities than the parent process.
   </details>

3. **How do you drop all Linux capabilities and add only NET_BIND_SERVICE?**
   <details>
   <summary>Answer</summary>
   ```yaml
   securityContext:
     capabilities:
       drop: ["ALL"]
       add: ["NET_BIND_SERVICE"]
   ```
   </details>

4. **What extra configuration is needed with readOnlyRootFilesystem: true?**
   <details>
   <summary>Answer</summary>
   You need to mount emptyDir volumes for any paths the application needs to write to (like /tmp, /var/cache, /var/run).
   </details>

---

## Hands-On Exercise

**Task**: Create a fully hardened pod.

```bash
# Step 1: Create an insecure pod first
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
EOF

# Step 2: Check its security context
kubectl get pod insecure -o yaml | grep -A 20 securityContext
# (Likely empty or minimal)

# Step 3: Create hardened version
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: hardened
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE
    volumeMounts:
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
  - name: tmp
    emptyDir: {}
EOF

# Step 4: Wait for pods
kubectl wait --for=condition=Ready pod/hardened --timeout=60s

# Step 5: Verify security context
kubectl get pod hardened -o jsonpath='{.spec.securityContext}' | jq .
kubectl get pod hardened -o jsonpath='{.spec.containers[0].securityContext}' | jq .

# Step 6: Test that writing to root filesystem fails
kubectl exec hardened -- touch /etc/test 2>&1 || echo "Write blocked (expected)"

# Step 7: Test that writable volume works
kubectl exec hardened -- touch /tmp/test && echo "Write to /tmp succeeded"

# Cleanup
kubectl delete pod insecure hardened
```

**Success criteria**: Hardened pod runs with all security settings applied.

---

## Summary

**Essential Security Context Settings**:
- `runAsNonRoot: true` + `runAsUser: 1000`
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- `capabilities: drop: [ALL]`

**Never Use**:
- `privileged: true` (unless absolutely required)
- Running as root without justification

**Best Practices**:
- Set at both pod and container level
- Drop all capabilities, add selectively
- Mount emptyDir for writable paths

**Exam Tips**:
- Know the full hardened pod template
- Understand pod vs container context
- Debug common errors

---

## Next Module

[Module 4.2: Pod Security Admission](../module-4.2-pod-security-admission/) - Enforcing security standards at namespace level.
