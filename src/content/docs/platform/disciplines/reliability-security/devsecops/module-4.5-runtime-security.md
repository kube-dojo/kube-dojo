---
title: "Module 4.5: Runtime Security"
slug: platform/disciplines/reliability-security/devsecops/module-4.5-runtime-security
sidebar:
  order: 7
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- **Required**: [Module 4.4: Supply Chain Security](module-4.4-supply-chain-security/) — Securing the build
- **Required**: Kubernetes basics (Pods, containers, namespaces)
- **Recommended**: [Security Principles Track](../../../foundations/security-principles/) — Defense in depth
- **Helpful**: Linux process and syscall concepts

---

## Why This Module Matters

You've secured your code. Your pipeline is locked down. Your images are signed.

**Then your container gets compromised at runtime.**

All that pre-production security? It bought you time. It reduced your attack surface. But determined attackers find ways in—zero-days, misconfigurations, credential theft.

Runtime security is your last line of defense. It's what catches the attackers who got past everything else.

After this module, you'll understand:
- Runtime threat detection with Falco
- Container security contexts and restrictions
- Network policies for microsegmentation
- Pod Security Standards and admission control
- Incident response in containerized environments

---

## The Runtime Attack Surface

### What Attackers Do After Getting In

```
┌─────────────────────────────────────────────────────────────────┐
│                  RUNTIME ATTACK CHAIN                           │
│                                                                 │
│  INITIAL ACCESS         EXECUTION           PERSISTENCE         │
│  ┌─────────────┐       ┌─────────────┐     ┌─────────────┐     │
│  │ Exploit app │       │ Run shell   │     │ Install     │     │
│  │ vulnerability│─────▶│ commands    │────▶│ backdoor    │     │
│  │             │       │             │     │             │     │
│  └─────────────┘       └─────────────┘     └─────────────┘     │
│                                                   │             │
│                                                   ▼             │
│  LATERAL MOVEMENT      PRIVILEGE ESC      DATA EXFILTRATION    │
│  ┌─────────────┐       ┌─────────────┐     ┌─────────────┐     │
│  │ Access other│       │ Escape to   │     │ Steal       │     │
│  │ services    │◀──────│ host/root   │────▶│ secrets,    │     │
│  │             │       │             │     │ data        │     │
│  └─────────────┘       └─────────────┘     └─────────────┘     │
│                                                                 │
│  Runtime security detects and prevents these behaviors         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Runtime Security Controls

| Layer | Control | Purpose |
|-------|---------|---------|
| **Container** | Security Context | Restrict capabilities |
| **Pod** | Pod Security Standards | Enforce restrictions |
| **Network** | Network Policies | Microsegmentation |
| **Syscall** | Seccomp | Block dangerous syscalls |
| **Detection** | Falco | Detect suspicious behavior |
| **Response** | Runtime enforcement | Kill compromised workloads |

---

## Container Security Context

### What Security Context Controls

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:              # Pod-level settings
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault

  containers:
  - name: app
    image: myapp:v1
    securityContext:            # Container-level settings
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
      seccompProfile:
        type: RuntimeDefault

    volumeMounts:
    - name: tmp
      mountPath: /tmp

  volumes:
  - name: tmp
    emptyDir: {}
```

### Security Context Reference

| Setting | Effect | Recommendation |
|---------|--------|----------------|
| `runAsNonRoot: true` | Prevent root user | Always |
| `runAsUser: 1000` | Specific non-root UID | Recommended |
| `readOnlyRootFilesystem: true` | Prevent writes to filesystem | Where possible |
| `allowPrivilegeEscalation: false` | Prevent setuid/setgid | Always |
| `capabilities.drop: [ALL]` | Remove all Linux capabilities | Always, then add needed |
| `privileged: false` | Not a privileged container | Never use `true` |

### Linux Capabilities

Instead of root or non-root, Linux has granular capabilities:

```yaml
# Bad: Running as root to bind port 80
containers:
- name: nginx
  securityContext:
    runAsUser: 0  # Root! Don't do this

# Good: Add only the needed capability
containers:
- name: nginx
  securityContext:
    runAsUser: 1000
    capabilities:
      drop: [ALL]
      add: [NET_BIND_SERVICE]  # Only what's needed
```

**Common capabilities:**

| Capability | Purpose | When Needed |
|------------|---------|-------------|
| `NET_BIND_SERVICE` | Bind ports < 1024 | Web servers |
| `NET_RAW` | Raw sockets | Network tools |
| `SYS_PTRACE` | Process tracing | Debugging (rarely) |
| `SYS_ADMIN` | Many admin ops | Almost never |

---

## Did You Know?

1. **Falco was created at Sysdig in 2016** and donated to CNCF in 2018. It was one of the first tools designed specifically for container runtime security and is now used by thousands of organizations.

2. **The Linux capability system** has 41 distinct capabilities as of kernel 5.x. `CAP_SYS_ADMIN` alone grants about 30% of all privileged operations—which is why it's called "the new root."

3. **The first major container escape (CVE-2019-5736)** in runc allowed attackers to overwrite the host's runc binary and escape any container. It affected Docker, Kubernetes, containerd, and more. Patching required updating the container runtime, not just Kubernetes.

4. **Network policies are not enforced by default** in Kubernetes. Without a CNI that supports them (like Calico, Cilium, or Weave), NetworkPolicy resources are silently ignored—a common misconfiguration.

---

## Pod Security Standards

### The Three Levels

Kubernetes Pod Security Standards (PSS) replaced the deprecated PodSecurityPolicy:

```
┌─────────────────────────────────────────────────────────────┐
│              POD SECURITY STANDARDS LEVELS                   │
│                                                              │
│  PRIVILEGED                                                  │
│  ───────────                                                 │
│  No restrictions. Legacy workloads, system components.       │
│  Use only when absolutely necessary.                         │
│                                                              │
│  BASELINE                                                    │
│  ────────                                                    │
│  Minimally restrictive. Prevents known privilege escalations.│
│  Good starting point for general workloads.                  │
│                                                              │
│  RESTRICTED                                                  │
│  ──────────                                                  │
│  Heavily restrictive. Current pod hardening best practices.  │
│  Target for all production workloads.                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Baseline vs Restricted

| Check | Baseline | Restricted |
|-------|----------|------------|
| `privileged: false` | Required | Required |
| `hostNetwork: false` | Required | Required |
| `hostPID: false` | Required | Required |
| `hostIPC: false` | Required | Required |
| `allowPrivilegeEscalation: false` | | Required |
| `runAsNonRoot: true` | | Required |
| `capabilities.drop: [ALL]` | | Required |
| `seccompProfile: RuntimeDefault` | | Required |

### Enforcing with Namespace Labels

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce restricted level (reject violations)
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest

    # Warn about baseline violations in development
    pod-security.kubernetes.io/warn: baseline
    pod-security.kubernetes.io/warn-version: latest

    # Audit all violations for logging
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

### Testing Compliance

```bash
# Test if a pod would be admitted
kubectl label --dry-run=server ns my-namespace \
  pod-security.kubernetes.io/enforce=restricted

# Create a pod that violates restricted
kubectl run test --image=nginx -n production
# Error: pod "test" is forbidden: violates PodSecurity "restricted:latest"
```

---

## Network Policies

### Default Kubernetes Networking

```
┌─────────────────────────────────────────────────────────────┐
│            DEFAULT: ALL PODS CAN TALK TO ALL PODS            │
│                                                              │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│    │ Frontend│◀───▶│  API    │◀───▶│   DB    │              │
│    │         │     │         │     │         │              │
│    └─────────┘     └─────────┘     └─────────┘              │
│         ▲               ▲               ▲                    │
│         │               │               │                    │
│         └───────────────┼───────────────┘                    │
│                         │                                    │
│         Attacker compromises frontend,                       │
│         can directly access DB                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### With Network Policies (Microsegmentation)

```
┌─────────────────────────────────────────────────────────────┐
│            WITH NETWORK POLICIES: LEAST PRIVILEGE            │
│                                                              │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│    │ Frontend│─────▶│  API    │─────▶│   DB    │              │
│    │         │     │         │     │         │              │
│    └─────────┘     └─────────┘     └─────────┘              │
│         │               │               │                    │
│         ╳               │               ╳                    │
│         │               │               │                    │
│         └───────────────┴───────────────┘                    │
│                                                              │
│         Frontend can only talk to API                        │
│         Only API can talk to DB                              │
│         Attacker is contained                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Default Deny Policy

```yaml
# Deny all ingress and egress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}  # Applies to all pods
  policyTypes:
    - Ingress
    - Egress
  # No ingress or egress rules = deny all
```

### Allow Specific Traffic

```yaml
# Allow frontend to talk to API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow-frontend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080

---
# Allow API to talk to database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-allow-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api
      ports:
        - protocol: TCP
          port: 5432
```

### Allow Egress to External Services

```yaml
# Allow pods to access external APIs
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      needs-external: "true"
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8      # Block internal
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

---

## Runtime Threat Detection with Falco

### How Falco Works

```
┌─────────────────────────────────────────────────────────────┐
│                    FALCO ARCHITECTURE                        │
│                                                              │
│  KERNEL                                                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                     SYSCALLS                             ││
│  │  open()  exec()  connect()  write()  mount()  ...       ││
│  └────────────────────────┬────────────────────────────────┘│
│                           │                                  │
│                    eBPF probe                                │
│                           │                                  │
│  USERSPACE                ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   FALCO ENGINE                           ││
│  │                                                          ││
│  │  ┌─────────────┐    ┌─────────────┐   ┌─────────────┐   ││
│  │  │   RULES     │───▶│   EVENTS    │──▶│   ALERTS    │   ││
│  │  │             │    │             │   │             │   ││
│  │  │ if (shell)  │    │ bash in     │   │ Slack       │   ││
│  │  │   alert     │    │ container   │   │ PagerDuty   │   ││
│  │  └─────────────┘    └─────────────┘   └─────────────┘   ││
│  │                                                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Installing Falco

```bash
# Add Falco Helm repo
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install with eBPF driver (recommended for most clusters)
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=ebpf \
  --set tty=true
```

### Built-in Rules

Falco includes rules for common threats:

```yaml
# Example built-in rules (simplified)

# Detect shell spawned in container
- rule: Terminal shell in container
  desc: A shell was spawned in a container with an attached terminal
  condition: >
    spawned_process and
    container and
    shell_procs and
    proc.tty != 0
  output: >
    Shell spawned in container (user=%user.name container=%container.name
    shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline)
  priority: NOTICE
  tags: [container, shell, mitre_execution]

# Detect reading sensitive files
- rule: Read sensitive file untrusted
  desc: An attempt to read a sensitive file by non-trusted program
  condition: >
    sensitive_files and
    open_read and
    not trusted_program
  output: >
    Sensitive file accessed (file=%fd.name container=%container.name)
  priority: WARNING
  tags: [filesystem, mitre_credential_access]

# Detect container escape attempt
- rule: Container Drift Detected
  desc: New executable created in container
  condition: >
    container and
    evt.type in (open, openat) and
    evt.is_open_write = true and
    fd.filename = 'runc'
  output: >
    Potential container escape (container=%container.name file=%fd.name)
  priority: CRITICAL
  tags: [container, mitre_privilege_escalation]
```

### Custom Falco Rules

```yaml
# /etc/falco/rules.d/custom-rules.yaml

# Detect kubectl exec into production pods
- rule: Kubectl exec in production
  desc: kubectl exec was run against a production pod
  condition: >
    spawned_process and
    container and
    k8s.ns.name = "production" and
    proc.name = "kubectl" and
    proc.cmdline contains "exec"
  output: >
    kubectl exec in production (user=%ka.user.name pod=%k8s.pod.name
    namespace=%k8s.ns.name command=%proc.cmdline)
  priority: WARNING
  tags: [k8s, exec, production]

# Detect cryptocurrency mining
- rule: Cryptocurrency Mining Detected
  desc: Process associated with crypto mining detected
  condition: >
    spawned_process and
    container and
    (proc.name in (xmrig, ethminer, minerd) or
     proc.cmdline contains "stratum+tcp" or
     proc.cmdline contains "cryptonight")
  output: >
    Crypto mining detected (container=%container.name process=%proc.name)
  priority: CRITICAL
  tags: [cryptomining, mitre_execution]
```

### Falco Alerts to Slack

```yaml
# Falcosidekick configuration for Slack alerts
helm upgrade falco falcosecurity/falco \
  --namespace falco \
  --set falcosidekick.enabled=true \
  --set falcosidekick.config.slack.webhookurl="https://hooks.slack.com/..." \
  --set falcosidekick.config.slack.channel="#security-alerts" \
  --set falcosidekick.config.slack.minimumpriority="warning"
```

---

## War Story: The Cryptominer at 3 AM

An e-commerce company noticed their Kubernetes cluster costs had doubled overnight.

**The Discovery:**

```
2:47 AM - Autoscaler triggered: "Need more nodes"
3:15 AM - Again: "Need more nodes"
4:00 AM - Alert: "Cluster at capacity"
4:30 AM - On-call SRE: "Why are we at 200% CPU?"
```

**The Investigation:**

```bash
# Top pods by CPU
kubectl top pods -A --sort-by=cpu

NAMESPACE   NAME                    CPU
default     frontend-7b8c9-x2k9j    4000m  # Normal: 200m
default     frontend-7b8c9-a8s2d    4000m
default     frontend-7b8c9-m2k1p    4000m
```

All frontend pods at 4 CPUs each? Something was running inside.

```bash
# Exec into pod (before they added Falco)
kubectl exec -it frontend-7b8c9-x2k9j -- sh

$ ps aux
USER  PID  %CPU  COMMAND
app   1    0.1   node server.js
app   847  398   /tmp/xmrig --threads=4 --url=stratum+tcp://pool.minexmr.com
```

**The Root Cause:**

A vulnerable npm package allowed remote code execution. Attacker:
1. Exploited the RCE
2. Downloaded xmrig to /tmp
3. Started mining cryptocurrency
4. Company paid for compute, attacker got the crypto

**The Fix:**

```yaml
# 1. Read-only filesystem (no writing to /tmp)
securityContext:
  readOnlyRootFilesystem: true

# 2. Network policy (block outbound except known endpoints)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes: [Egress]
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: api
      ports:
        - port: 8080

# 3. Falco rule (detect mining immediately)
- rule: Cryptocurrency Mining
  condition: proc.name in (xmrig, minerd) or proc.cmdline contains "stratum"
  output: Crypto mining (container=%container.name cmd=%proc.cmdline)
  priority: CRITICAL
```

**After implementing:**
- Same attack attempt happened 2 weeks later
- Falco detected in 15 seconds
- Automatic alert to Slack
- Pod killed before meaningful mining
- Post-mortem: Found the vulnerable package, patched it

---

## Seccomp Profiles

### What Seccomp Does

Seccomp (Secure Computing Mode) filters syscalls:

```
┌─────────────────────────────────────────────────────────────┐
│                    SECCOMP FILTERING                         │
│                                                              │
│  APPLICATION                                                 │
│       │                                                      │
│       │ syscall: read()                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │               SECCOMP FILTER                             ││
│  │                                                          ││
│  │   read()    → ALLOW                                      ││
│  │   write()   → ALLOW                                      ││
│  │   exec()    → LOG + ALLOW (audit)                        ││
│  │   mount()   → DENY (EPERM)                               ││
│  │   ptrace()  → KILL (terminate process)                   ││
│  │                                                          ││
│  └─────────────────────────────────────────────────────────┘│
│       │                                                      │
│       ▼                                                      │
│  KERNEL                                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Seccomp Profile Types

```yaml
# RuntimeDefault - container runtime's built-in profile
securityContext:
  seccompProfile:
    type: RuntimeDefault

# Localhost - custom profile from node
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: profiles/my-app.json

# Unconfined - no seccomp (avoid in production)
securityContext:
  seccompProfile:
    type: Unconfined
```

### Creating Custom Seccomp Profiles

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close",
        "stat", "fstat", "lstat",
        "poll", "mmap", "mprotect",
        "brk", "ioctl", "access",
        "pipe", "dup", "dup2",
        "socket", "connect", "accept",
        "sendto", "recvfrom",
        "bind", "listen",
        "clone", "fork", "vfork",
        "execve", "exit", "exit_group",
        "futex", "epoll_wait", "epoll_ctl"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### Generating Seccomp Profiles

```bash
# Using Inspektor Gadget
kubectl gadget trace exec -n production -p my-pod > syscalls.log

# Using Security Profiles Operator
kubectl apply -f - <<EOF
apiVersion: security-profiles-operator.x-k8s.io/v1alpha1
kind: SeccompProfile
metadata:
  name: my-app-profile
  namespace: production
spec:
  defaultAction: SCMP_ACT_LOG
EOF

# After observing normal behavior, convert to allow-list
```

---

## Incident Response in Kubernetes

### Detection to Response Flow

```
┌─────────────────────────────────────────────────────────────┐
│               RUNTIME INCIDENT RESPONSE                      │
│                                                              │
│  DETECT          CONTAIN         INVESTIGATE      RECOVER   │
│  ┌──────┐       ┌──────┐        ┌──────┐        ┌──────┐   │
│  │Falco │       │Isolate│       │Collect│       │Patch │   │
│  │alerts│──────▶│pod/ns │──────▶│evidence│─────▶│deploy│   │
│  │      │       │      │        │       │       │      │   │
│  └──────┘       └──────┘        └──────┘        └──────┘   │
│     │              │               │               │        │
│     │         Network policy   Logs, memory,   Rollback    │
│     │         Label isolation  filesystem      Clean image │
│     │                                                       │
└─────────────────────────────────────────────────────────────┘
```

### Containment Strategies

**1. Network Isolation:**
```yaml
# Emergency isolation policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: emergency-isolate
  namespace: compromised-namespace
spec:
  podSelector:
    matchLabels:
      compromised: "true"
  policyTypes:
    - Ingress
    - Egress
  # No rules = deny all traffic
```

**2. Label-based Isolation:**
```bash
# Mark pod as compromised
kubectl label pod compromised-pod compromised=true

# Network policy automatically isolates it
```

**3. Delete but Preserve Evidence:**
```bash
# Create debug pod with same network namespace (before deleting)
kubectl debug pod/compromised-pod --image=busybox --target=compromised-container

# Capture pod spec for forensics
kubectl get pod compromised-pod -o yaml > evidence/pod-spec.yaml

# Get container filesystem
kubectl cp compromised-pod:/app ./evidence/app-filesystem

# Now delete
kubectl delete pod compromised-pod
```

### Forensic Data Collection

```bash
# Collect logs
kubectl logs compromised-pod > evidence/pod.log
kubectl logs compromised-pod --previous > evidence/pod-previous.log

# Collect events
kubectl get events --field-selector involvedObject.name=compromised-pod > evidence/events.log

# Collect metrics (if prometheus)
# Query: container_cpu_usage_seconds_total{pod="compromised-pod"}

# Collect Falco alerts
kubectl logs -n falco -l app=falco | grep "compromised-pod" > evidence/falco-alerts.log
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No network policies | All pods can talk to all pods | Default deny, explicit allow |
| Running as root | Easy privilege escalation | `runAsNonRoot: true` |
| Privileged containers | Full host access | Never use in production |
| No runtime detection | Attacks go unnoticed | Deploy Falco or similar |
| Writable root filesystem | Malware can persist | `readOnlyRootFilesystem: true` |
| All capabilities | Unnecessary privileges | `drop: [ALL]`, add only needed |
| No seccomp | All syscalls allowed | Use RuntimeDefault minimum |

---

## Quiz: Check Your Understanding

### Question 1
A container needs to bind to port 80. The developer says "it must run as root." What's the correct response?

<details>
<summary>Show Answer</summary>

**Don't run as root. Grant the specific capability instead:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-server
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      runAsUser: 1000
      runAsGroup: 1000
      runAsNonRoot: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
        add: [NET_BIND_SERVICE]  # Only this capability
    ports:
    - containerPort: 80
```

**Or even better:** Use port 8080 internally, expose as 80 via Service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-server
spec:
  ports:
  - port: 80          # External port
    targetPort: 8080  # Container port (unprivileged)
```

**Key principle:** Least privilege. Grant the minimum required, never root for convenience.

</details>

### Question 2
Falco alerts that a shell was spawned in your production API pod. What are your immediate steps?

<details>
<summary>Show Answer</summary>

**Immediate containment (first 5 minutes):**

1. **Isolate the pod:**
   ```bash
   # Label for network policy isolation
   kubectl label pod api-pod-xyz compromised=true

   # Apply isolation policy
   kubectl apply -f emergency-isolate-policy.yaml
   ```

2. **Preserve evidence (before pod restarts):**
   ```bash
   # Capture current state
   kubectl get pod api-pod-xyz -o yaml > evidence/pod.yaml
   kubectl logs api-pod-xyz > evidence/logs.txt
   kubectl describe pod api-pod-xyz > evidence/describe.txt
   ```

3. **Capture filesystem if possible:**
   ```bash
   kubectl cp api-pod-xyz:/app ./evidence/app/
   kubectl cp api-pod-xyz:/tmp ./evidence/tmp/
   ```

**Investigation (next 15-30 minutes):**

4. **Check Falco for attack chain:**
   ```bash
   kubectl logs -n falco -l app=falco | grep api-pod-xyz
   ```

5. **Check audit logs:**
   ```bash
   # Who exec'd into the pod?
   kubectl logs -n kube-system -l component=kube-apiserver | grep exec
   ```

6. **Check other pods:**
   ```bash
   # Are other pods compromised?
   kubectl get pods -l app=api -o name | xargs -I {} kubectl exec {} -- ps aux
   ```

**Recovery:**

7. **Rotate any secrets the pod had access to**
8. **Redeploy from known-good image**
9. **Enhance detection rules**

</details>

### Question 3
You've implemented a default-deny network policy, but DNS resolution stopped working. Why?

<details>
<summary>Show Answer</summary>

**DNS queries are egress traffic too!**

Default deny blocks all egress, including to `kube-dns`:

```yaml
# The problem: Denies everything including DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  # No egress rules = no DNS
```

**Solution: Explicitly allow DNS:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}  # All pods
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

**Best practice:** Create a base policy that allows DNS, then layer additional policies on top.

</details>

### Question 4
Your cluster uses Pod Security Standards at "restricted" level. A developer complains their pod won't start. The error says "runAsNonRoot must be true." But their Dockerfile has `USER 1000`. What's wrong?

<details>
<summary>Show Answer</summary>

**The Pod spec doesn't declare `runAsNonRoot: true`.**

Even if the container runs as non-root by default, Kubernetes can't verify this without the explicit declaration:

```yaml
# This fails PSS restricted
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: myapp:v1  # Has USER 1000 in Dockerfile
    # But no securityContext!

# Error: "runAsNonRoot must be true"
```

**Fix: Declare the security context explicitly:**

```yaml
apiVersion: v1
kind: Pod
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
    image: myapp:v1
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: [ALL]
```

**Key insight:** Pod Security Standards validate what's in the Pod spec, not what's in the container. Explicit declarations are required.

</details>

---

## Hands-On Exercise: Implement Runtime Security

Secure a Kubernetes namespace with runtime protections.

### Part 1: Apply Pod Security Standard

```bash
# Create namespace with restricted PSS
kubectl create namespace secure-demo

kubectl label namespace secure-demo \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/audit=restricted

# Test: This should fail
kubectl run test --image=nginx -n secure-demo
# Error: violates PodSecurity "restricted"

# Test: This should work
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-nginx
  namespace: secure-demo
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: nginx
    image: nginxinc/nginx-unprivileged
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: [ALL]
EOF
```

### Part 2: Apply Network Policies

```bash
# Default deny all
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: secure-demo
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
EOF

# Allow DNS
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: secure-demo
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
EOF

# Test: Pod should not reach external IPs
kubectl exec -n secure-demo secure-nginx -- curl -s -m 5 httpbin.org/get
# Should timeout
```

### Part 3: Deploy Falco (if cluster allows)

```bash
# Install Falco with Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=ebpf \
  --set tty=true

# Watch Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco -f

# Trigger alert: Shell in container
kubectl exec -n secure-demo secure-nginx -- /bin/sh
# Watch Falco log: "shell spawned in container"
```

### Success Criteria

- [ ] Namespace enforces restricted PSS
- [ ] Non-compliant pods are rejected
- [ ] Compliant pods run successfully
- [ ] Network policies block unwanted traffic
- [ ] DNS still works
- [ ] (Optional) Falco detects shell access

---

## Key Takeaways

1. **Defense in depth** — Security contexts, PSS, network policies, runtime detection
2. **Least privilege** — Drop all capabilities, add only what's needed
3. **Network segmentation** — Default deny, explicit allow
4. **Continuous monitoring** — Falco or equivalent for runtime detection
5. **Plan for incidents** — Know how to contain, collect evidence, recover

---

## Further Reading

**Tools:**
- **Falco** — falco.org
- **Open Policy Agent** — openpolicyagent.org
- **Cilium** — cilium.io (NetworkPolicy + eBPF)

**Kubernetes Documentation:**
- **Pod Security Standards** — kubernetes.io/docs/concepts/security/pod-security-standards/
- **Network Policies** — kubernetes.io/docs/concepts/services-networking/network-policies/

**Guides:**
- **NSA/CISA Kubernetes Hardening Guide** — media.defense.gov
- **CIS Kubernetes Benchmark** — cisecurity.org

---

## Summary

Runtime security protects running workloads through multiple layers:

- **Security contexts** restrict container capabilities
- **Pod Security Standards** enforce baseline or restricted modes
- **Network policies** implement microsegmentation
- **Seccomp profiles** filter dangerous syscalls
- **Falco** detects suspicious behavior in real-time

The goal is to limit blast radius: if an attacker gets in, they should be detected quickly and prevented from moving laterally or escalating privileges.

---

## Next Module

Continue to [Module 4.6: Security Culture and Automation](module-4.6-security-culture/) to learn about building security-first teams and automating security operations.

---

*"Prevention is ideal, detection is essential, response is mandatory."*
