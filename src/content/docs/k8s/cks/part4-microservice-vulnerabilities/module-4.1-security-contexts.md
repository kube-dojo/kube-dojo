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

> **Stop and think**: A container runs as root by default unless you explicitly set `runAsNonRoot: true`. But many popular images (nginx, redis, postgres) are built to run as root. What happens when you enforce `runAsNonRoot: true` on these images, and what's the proper fix?

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

### hostPID, hostNetwork, and hostIPC (AVOID!)

While not strictly inside the `securityContext` block, these pod-level fields are equally dangerous:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: host-namespaces
spec:
  hostPID: true      # Can see all processes on the node
  hostNetwork: true  # Uses node's network namespace
  hostIPC: true      # Can access node's IPC mechanisms
  containers:
  - name: app
    image: nginx
```

> **Warning**: A container with `hostPID: true` can inspect host processes and, if combined with `ptrace` capability or host mounts, inject code into host processes like the kubelet.

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

> **Pause and predict**: You set `capabilities: drop: ["ALL"]` on a container that needs to bind to port 80. The container crashes with "permission denied" on startup. What single capability do you need to add back, and why is the "drop all, add back" approach safer than the default?

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
      type: RuntimeDefault  # Block dangerous kernel syscalls
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
    resources:  # Prevent resource exhaustion (DoS)
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

## Real-World War Story: The Privileged Container Escape

In a well-documented incident at a major tech company, a security team investigating a breached Kubernetes cluster discovered that attackers had completely compromised a worker node by escaping a seemingly harmless application container. The root cause? During initial troubleshooting months earlier, developers had temporarily set `privileged: true` in the pod's security context to "make it work quickly" and forgot to remove it before deploying to production.

When the attackers found a basic remote code execution (RCE) vulnerability in the web application, they dropped into a shell. Because the container was privileged, it had all Linux capabilities enabled, including `CAP_SYS_MODULE` and `CAP_SYS_ADMIN`. The attackers compiled a malicious Linux kernel module, loaded it directly into the host's kernel from inside the container, and shattered the container's isolation boundary. From the host, they accessed the kubelet's TLS certificates and pivoted to compromise the entire cluster.

> **Stop and think**: If the developers had instead run the container as root (`runAsUser: 0`) but without `privileged: true` and with default capabilities, would the attackers have been able to load the kernel module?

**The Lesson:** If the developers had used `capabilities: drop: ["ALL"]` and explicitly added only the specific network capability they were trying to troubleshoot, the `CAP_SYS_MODULE` capability would have been dropped. The kernel module injection would have failed, trapping the attackers inside the container. Never use `privileged: true` as a shortcut for missing capabilities.

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

> **Pause and predict**: You deploy a pod with `readOnlyRootFilesystem: true` and `runAsNonRoot: true`. The application writes temporary files to `/tmp` and logs to `/var/log/app/`. Without any volume mounts, which writes will fail and why?

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

1. **You deploy an nginx pod with `runAsNonRoot: true` but without specifying `runAsUser`. The pod fails with "container has runAsNonRoot and image will run as root." A developer says "just remove runAsNonRoot." What's the correct fix that maintains security?**
   <details>
   <summary>Answer</summary>
   Don't remove `runAsNonRoot` -- add `runAsUser: 1000` (or any non-zero UID) to force the container to run as a non-root user. The nginx official image defaults to root, so `runAsNonRoot: true` correctly catches this. Better yet, use the `nginx:alpine` image with a non-root user configured, or build a custom image with `USER 1000` in the Dockerfile. The `runAsNonRoot` check is a safety net -- it validates at pod admission time that the container won't run as UID 0, preventing privilege escalation if an attacker compromises the application.
   </details>

2. **During a security audit, you find a container running with all default Linux capabilities (14 capabilities including NET_RAW, SYS_CHROOT, and SETUID). The application only serves HTTP on port 8080. A penetration tester uses NET_RAW to perform ARP spoofing within the pod network. How should the security context be configured to prevent this?**
   <details>
   <summary>Answer</summary>
   Use `capabilities: drop: ["ALL"]` to remove all 14 default capabilities. Since the app runs on port 8080 (above 1024), it doesn't even need `NET_BIND_SERVICE`. The "drop all, add back only what's needed" approach is the gold standard. NET_RAW enables packet crafting and ARP spoofing, SETUID enables privilege escalation, and SYS_CHROOT can be used for container escape techniques. By dropping all capabilities, the penetration tester's ARP spoofing attack is blocked because NET_RAW is unavailable. Always combine with `allowPrivilegeEscalation: false` to prevent regaining capabilities through setuid binaries.
   </details>

3. **Your application writes logs to `/var/log/app/`, caches data in `/tmp/`, and needs to update `/etc/nginx/conf.d/` at startup. You set `readOnlyRootFilesystem: true`. The pod crashes. What emptyDir volumes do you need, and is there a path you should NOT make writable?**
   <details>
   <summary>Answer</summary>
   Mount emptyDir volumes at `/var/log/app/` and `/tmp/` for logs and cache. For `/etc/nginx/conf.d/`, mount an emptyDir there too if nginx must write configs at startup. However, be cautious about making `/etc/` paths writable -- an attacker who compromises the application could modify nginx configuration to redirect traffic or expose sensitive data. The better approach is to use an initContainer to generate configs into a shared emptyDir volume, then mount it read-only in the main container. `readOnlyRootFilesystem: true` is powerful because it prevents attackers from writing malware, scripts, or modified binaries to the container filesystem.
   </details>

4. **A multi-container pod has security context set at both pod and container level. The pod-level sets `runAsUser: 1000`, but one container sets `runAsUser: 0` (root). Which setting takes effect for that container, and how do you prevent individual containers from overriding pod-level security?**
   <details>
   <summary>Answer</summary>
   The container-level setting wins -- that container runs as root (UID 0) despite the pod-level setting of 1000. Container-level security context always overrides pod-level for the same field. To prevent this override, use Pod Security Admission with the `restricted` profile in `enforce` mode on the namespace. PSA validates the final effective security context (including container-level overrides) and rejects pods where any container runs as root. This is why security contexts alone are insufficient -- they can be set by anyone who can create pods. PSA provides the policy enforcement layer that prevents bypasses.
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
      type: RuntimeDefault  # Block dangerous kernel syscalls
  containers:
  - name: app
    image: nginx
    command: ["sleep", "3600"]  # Override entrypoint so pod stays running for exec tests without crashing
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
kubectl delete pod insecure hardened --force
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