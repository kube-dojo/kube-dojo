---
title: "Module 6.4: Immutable Infrastructure"
slug: k8s/cks/part6-runtime-security/module-6.4-immutable-infrastructure
sidebar:
  order: 4
lab:
  id: cks-6.4-immutable-infrastructure
  url: https://killercoda.com/kubedojo/scenario/cks-6.4-immutable-infrastructure
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Security architecture
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 6.3 (Container Investigation), container basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** read-only root filesystems with targeted writable volume mounts for required paths
2. **Implement** immutable container patterns using non-root users, minimal base images, and no-shell builds
3. **Audit** running workloads to detect containers with writable filesystems or mutable configurations
4. **Design** deployment specifications that enforce immutability as a defense-in-depth layer

---

## Why This Module Matters

Immutable infrastructure means containers don't change after deployment. If an attacker can't modify files or install tools, their options are severely limited. Read-only filesystems, non-root users, and minimal images create defense in depth.

CKS tests immutable container configuration as a core security practice.

---

## What is Immutable Infrastructure?

```
┌─────────────────────────────────────────────────────────────┐
│              MUTABLE vs IMMUTABLE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MUTABLE (Traditional):                                    │
│  ─────────────────────────────────────────────────────────  │
│  • Software updated in place                               │
│  • Configuration changes at runtime                        │
│  • Persistent state in container                           │
│  • Drift between deployments                               │
│  • Attackers can modify and persist                        │
│                                                             │
│  IMMUTABLE (Cloud Native):                                 │
│  ─────────────────────────────────────────────────────────  │
│  • New image for every change                              │
│  • Configuration via ConfigMaps/Secrets                    │
│  • State in external systems (DB, storage)                │
│  • Consistent, reproducible deployments                    │
│  • Changes don't survive restart                           │
│                                                             │
│  Security Benefits of Immutable:                          │
│  ├── Malware can't persist                                │
│  ├── Easier to detect changes                             │
│  ├── Known good state always available                    │
│  └── Faster recovery (just redeploy)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementing Immutable Containers

### Read-Only Root Filesystem

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: immutable-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true  # Can't write to container filesystem
    volumeMounts:
    # Writable directories for application needs
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

### What Read-Only Prevents

```
┌─────────────────────────────────────────────────────────────┐
│              READ-ONLY FILESYSTEM PROTECTION                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BLOCKED Actions:                                          │
│  ├── Installing packages (apt, yum, pip)                  │
│  ├── Downloading malware (wget, curl to disk)             │
│  ├── Modifying system files (/etc/passwd)                 │
│  ├── Creating persistence (cron, init scripts)            │
│  ├── Web shells (can't write PHP/JSP files)              │
│  └── Log tampering (can't modify /var/log)               │
│                                                             │
│  STILL ALLOWED:                                            │
│  ├── Writing to mounted emptyDir volumes                  │
│  ├── Network connections                                   │
│  ├── Memory-based attacks                                  │
│  └── Process execution (existing binaries)                │
│                                                             │
│  Defense in depth: combine with other controls            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Minimal Base Images

### Why Minimal Matters

```
┌─────────────────────────────────────────────────────────────┐
│              ATTACK SURFACE COMPARISON                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Ubuntu Full (~80MB installed):                            │
│  ├── bash, sh, dash                                        │
│  ├── apt, dpkg                                             │
│  ├── wget, curl                                            │
│  ├── python, perl                                          │
│  ├── mount, umount                                         │
│  └── 1000+ packages with CVEs                             │
│                                                             │
│  Alpine (~5MB installed):                                  │
│  ├── ash (busybox shell)                                   │
│  ├── apk                                                   │
│  └── ~50 packages                                          │
│                                                             │
│  Distroless (~2MB installed):                              │
│  ├── NO shell                                              │
│  ├── NO package manager                                    │
│  ├── Only runtime + app                                   │
│  └── Minimal CVE surface                                  │
│                                                             │
│  Fewer tools = fewer options for attackers                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Distroless Example

```dockerfile
# Build stage
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o myapp

# Production stage - distroless
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]

# No shell - kubectl exec will fail!
# No package manager - can't install tools
# Running as non-root - limited privileges
```

---

## Non-Root Containers

### Configure Non-Root

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nonroot-pod
spec:
  securityContext:
    runAsNonRoot: true      # Fail if image tries to run as root
    runAsUser: 1000         # Run as UID 1000
    runAsGroup: 1000        # Run as GID 1000
    fsGroup: 1000           # Volume ownership
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false  # Can't gain more privileges
      capabilities:
        drop: ["ALL"]  # Drop all capabilities
```

### What Non-Root Prevents

```
┌─────────────────────────────────────────────────────────────┐
│              NON-ROOT PROTECTION                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  As non-root, attackers CANNOT:                           │
│  ├── Bind to ports < 1024                                 │
│  ├── Modify /etc/passwd, /etc/shadow                      │
│  ├── Install system-wide packages                         │
│  ├── Access /proc/sys for kernel params                   │
│  ├── Load kernel modules                                  │
│  └── Mount filesystems                                     │
│                                                             │
│  With allowPrivilegeEscalation: false:                    │
│  ├── setuid binaries don't work                           │
│  ├── Can't use sudo/su                                    │
│  └── Capabilities can't be gained                         │
│                                                             │
│  With capabilities drop ALL:                              │
│  └── Even if root, very limited powers                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Immutable Pod Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fully-immutable
spec:
  # Pod-level security
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault

  containers:
  - name: app
    image: gcr.io/distroless/static:nonroot  # Minimal image

    # Container-level security
    securityContext:
      readOnlyRootFilesystem: true           # Immutable filesystem
      allowPrivilegeEscalation: false        # No privilege gain
      capabilities:
        drop: ["ALL"]                         # No capabilities

    # Resource limits prevent resource exhaustion
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
      requests:
        memory: "64Mi"
        cpu: "250m"

    # Only mount what's needed, read-only where possible
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: config
      mountPath: /etc/config
      readOnly: true

  # Volumes
  volumes:
  - name: tmp
    emptyDir:
      medium: Memory  # tmpfs - in memory, not on disk
      sizeLimit: 10Mi
  - name: config
    configMap:
      name: app-config

  # Don't mount service account token
  automountServiceAccountToken: false
```

---

## Enforcing Immutability

### Pod Security Admission for Restricted

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce restricted standard
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
```

The `restricted` profile requires:
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities.drop: ["ALL"]
- seccompProfile set

### OPA Gatekeeper for ReadOnly

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirereadonlyfilesystem
spec:
  crd:
    spec:
      names:
        kind: K8sRequireReadOnlyFilesystem
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirereadonlyfilesystem
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.readOnlyRootFilesystem
          msg := sprintf("Container %v must use readOnlyRootFilesystem", [container.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireReadOnlyFilesystem
metadata:
  name: require-readonly-fs
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production"]
```

---

## Real Exam Scenarios

### Scenario 1: Make Existing Deployment Immutable

```yaml
# Before (mutable)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  template:
    spec:
      containers:
      - name: nginx
        image: nginx

# After (immutable)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 101  # nginx user
        fsGroup: 101
      containers:
      - name: nginx
        image: nginx
        securityContext:
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
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
```

### Scenario 2: Identify Mutable Pods

```bash
# Find pods without read-only filesystem
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.containers[].securityContext.readOnlyRootFilesystem != true) |
  "\(.metadata.namespace)/\(.metadata.name)"
'

# Find pods running as root
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.securityContext.runAsNonRoot != true) |
  "\(.metadata.namespace)/\(.metadata.name)"
'
```

### Scenario 3: Test Immutability

```bash
# Create immutable pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: immutable-test
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: test
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
EOF

# Test: Can't write to root filesystem
kubectl exec immutable-test -- touch /test.txt
# Error: touch: /test.txt: Read-only file system

# Test: Can write to /tmp
kubectl exec immutable-test -- touch /tmp/test.txt
# Success

# Cleanup
kubectl delete pod immutable-test
```

---

## Benefits Summary

```
┌─────────────────────────────────────────────────────────────┐
│              IMMUTABLE INFRASTRUCTURE BENEFITS              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Security:                                                 │
│  ├── Malware can't persist across restarts                │
│  ├── Attackers can't install tools                        │
│  ├── System files can't be modified                       │
│  └── Easier to detect unauthorized changes                │
│                                                             │
│  Operations:                                               │
│  ├── Consistent deployments every time                    │
│  ├── No configuration drift                               │
│  ├── Easy rollback (redeploy old image)                  │
│  └── Simpler troubleshooting (known state)               │
│                                                             │
│  Compliance:                                               │
│  ├── Audit trail via image versions                       │
│  ├── Prove exact software running                         │
│  └── Meet immutability requirements                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Distroless images have no shell**, which means `kubectl exec` with bash/sh won't work. Use `kubectl debug` with an ephemeral container for troubleshooting.

- **emptyDir with medium: Memory** creates a tmpfs (RAM-based filesystem). It's fast and doesn't persist to disk, but counts against container memory limits.

- **Some applications require writable directories** for temporary files, caches, or PID files. Identify these during development and mount emptyDir volumes.

- **Even with read-only filesystem**, attackers can still run malicious code in memory. Combine with seccomp profiles and network policies for defense in depth.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No writable /tmp | Application fails | Mount emptyDir for /tmp |
| Forgetting nginx paths | 502 errors | Mount cache, run directories |
| Image runs as root | runAsNonRoot fails | Use non-root image or specify UID |
| Too small emptyDir | Application fails | Set appropriate sizeLimit |
| Not testing locally | Surprises in production | Test immutable config in dev |

---

## Quiz

1. **What does readOnlyRootFilesystem: true prevent?**
   <details>
   <summary>Answer</summary>
   It prevents any writes to the container's root filesystem. This blocks malware installation, configuration tampering, and web shell creation. Applications can still write to mounted volumes.
   </details>

2. **Why combine read-only filesystem with non-root?**
   <details>
   <summary>Answer</summary>
   Defense in depth. Read-only prevents file modifications. Non-root prevents privileged actions. Together, they significantly limit what an attacker can do even after gaining code execution.
   </details>

3. **How do you allow writes for applications with read-only filesystem?**
   <details>
   <summary>Answer</summary>
   Mount emptyDir volumes for directories the application needs to write to (like /tmp, /var/cache). These directories become writable while the rest of the filesystem stays read-only.
   </details>

4. **What's the advantage of distroless images for immutability?**
   <details>
   <summary>Answer</summary>
   Distroless images have no shell or package manager, so attackers can't easily install tools or explore the system. They contain only the application runtime, minimizing attack surface.
   </details>

---

## Hands-On Exercise

**Task**: Create and verify an immutable container configuration.

```bash
# Step 1: Create mutable pod for comparison
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: mutable-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
EOF

# Step 2: Create immutable pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: immutable-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
EOF

# Wait for pods
kubectl wait --for=condition=Ready pod/mutable-pod --timeout=60s
kubectl wait --for=condition=Ready pod/immutable-pod --timeout=60s

# Step 3: Test mutable pod
echo "=== Testing Mutable Pod ==="
kubectl exec mutable-pod -- touch /test.txt && echo "Write to / succeeded"
kubectl exec mutable-pod -- whoami

# Step 4: Test immutable pod
echo "=== Testing Immutable Pod ==="
kubectl exec immutable-pod -- touch /test.txt 2>&1 || echo "Write to / blocked (expected)"
kubectl exec immutable-pod -- touch /tmp/test.txt && echo "Write to /tmp succeeded"
kubectl exec immutable-pod -- whoami

# Step 5: Compare security contexts
echo "=== Security Comparison ==="
echo "Mutable pod security:"
kubectl get pod mutable-pod -o jsonpath='{.spec.containers[0].securityContext}'
echo ""
echo "Immutable pod security:"
kubectl get pod immutable-pod -o jsonpath='{.spec.securityContext}'
echo ""
kubectl get pod immutable-pod -o jsonpath='{.spec.containers[0].securityContext}'
echo ""

# Cleanup
kubectl delete pod mutable-pod immutable-pod
```

**Success criteria**: Understand immutable configuration and its effects.

---

## Summary

**Immutability Components**:
- readOnlyRootFilesystem: true
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities.drop: ["ALL"]
- Minimal base images

**What It Prevents**:
- Malware installation
- Configuration tampering
- Persistence mechanisms
- Privilege escalation

**Implementation**:
- Mount emptyDir for writable paths
- Use distroless images
- Enforce with PSA restricted
- Test thoroughly

**Exam Tips**:
- Know security context fields
- Understand emptyDir usage
- Be able to fix mutable pods
- Know common application paths

---

## Part 6 Complete!

Congratulations! You've finished **Monitoring, Logging & Runtime Security** (20% of CKS). You now understand:
- Kubernetes audit logging configuration and analysis
- Runtime threat detection with Falco
- Container investigation techniques
- Immutable infrastructure principles

---

## CKS Curriculum Complete!

You've completed the entire CKS curriculum:

| Part | Topic | Weight |
|------|-------|--------|
| 0 | Environment Setup | - |
| 1 | Cluster Setup | 10% |
| 2 | Cluster Hardening | 15% |
| 3 | System Hardening | 15% |
| 4 | Minimize Microservice Vulnerabilities | 20% |
| 5 | Supply Chain Security | 20% |
| 6 | Monitoring & Runtime Security | 20% |

**Next Steps**:
1. Review weak areas
2. Practice with killer.sh
3. Time yourself on exercises
4. Schedule your exam!

Good luck with your CKS certification!
