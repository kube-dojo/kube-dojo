---
title: "Module 4.5: Tetragon - eBPF Runtime Security"
slug: platform/toolkits/security-quality/security-tools/module-4.5-tetragon
sidebar:
  order: 6
---
## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 4.3 (Falco basics), Understanding of Linux syscalls, Basic Kubernetes security concepts
**Learning Objectives**:
- Understand eBPF-based runtime security
- Deploy Tetragon for kernel-level threat detection
- Write TracingPolicies for custom security rules
- Block malicious actions at the kernel level before they complete

---

## Why This Module Matters

Traditional runtime security tools like Falco detect threats by watching syscalls from userspace and alerting after the fact. By the time you see the alert, the malicious command has already executed. You're always one step behind the attacker.

**Tetragon changes the game by operating inside the kernel.**

Using eBPF, Tetragon can observe and **enforce** security policies at the kernel level. It doesn't just detect the cryptominer starting—it can kill the process before the first instruction executes. It doesn't just log the data exfiltration—it can block the network connection at the packet level.

> "With Falco, you detect the attack and respond. With Tetragon, you prevent the attack from happening."

---

## Did You Know?

- Tetragon can **kill a process mid-syscall**, before the syscall completes
- A single Tetragon policy can block entire attack chains—from binary execution to network exfiltration
- Tetragon sees **inside encrypted connections** when you're blocking at the syscall level
- Tetragon is maintained by Isovalent, the company behind Cilium and Hubble
- The name comes from a geometric shape—representing the structured, precise nature of eBPF programs
- Tetragon can enforce security without ever touching the application—no sidecars, no code changes

---

## Falco vs Tetragon: Understanding the Difference

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Falco Architecture                               │
│                                                                         │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐  │
│  │ Application│───▶│   Kernel   │───▶│   Falco    │───▶│   Alert    │  │
│  │ executes   │    │ (syscall)  │    │ (userspace)│    │ (after)    │  │
│  │ malware    │    │            │    │ detects    │    │            │  │
│  └────────────┘    └────────────┘    └────────────┘    └────────────┘  │
│                                                                         │
│  Timeline: [malware executes] ──────▶ [detection] ──────▶ [response]   │
│                                        (too late)                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       Tetragon Architecture                             │
│                                                                         │
│  ┌────────────┐    ┌────────────────────────────────┐                  │
│  │ Application│───▶│            Kernel              │                  │
│  │ tries to   │    │  ┌─────────────────────────┐   │                  │
│  │ execute    │    │  │  Tetragon eBPF program  │   │                  │
│  │ malware    │    │  │  - Detect pattern       │   │                  │
│  └────────────┘    │  │  - SIGKILL process      │   │                  │
│        ▲           │  │  - Block syscall        │   │                  │
│        │           │  └─────────────────────────┘   │                  │
│        │           └────────────────────────────────┘                  │
│        │                         │                                      │
│        │                         ▼                                      │
│        │ Process killed     ┌────────────┐                             │
│        └───────────────────│   Alert    │                              │
│          before execution   │ (during)   │                             │
│                             └────────────┘                              │
│                                                                         │
│  Timeline: [attempt] ───▶ [blocked + alert] (prevented)                │
└─────────────────────────────────────────────────────────────────────────┘
```

| Aspect | Falco | Tetragon |
|--------|-------|----------|
| **Detection Location** | Userspace | Kernel (eBPF) |
| **Response Capability** | Alert only | Alert + Block + Kill |
| **Latency** | ~milliseconds | ~microseconds |
| **Attack Prevention** | After the fact | In real-time |
| **Enforcement** | External (needs separate tools) | Built-in |
| **Process Context** | Available | Rich (file descriptors, arguments, environment) |

---

## Tetragon Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                              │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                     kube-system namespace                         │ │
│  │  ┌────────────────────┐  ┌────────────────────────────────────┐  │ │
│  │  │  Tetragon Operator │  │  TracingPolicy CRDs                │  │ │
│  │  └────────────────────┘  │  - file-monitoring                 │  │ │
│  │                          │  - process-execution               │  │ │
│  │                          │  - network-connections             │  │ │
│  │                          └────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐              │
│  │    Node 1     │  │    Node 2     │  │    Node 3     │              │
│  │  ┌─────────┐  │  │  ┌─────────┐  │  │  ┌─────────┐  │              │
│  │  │Tetragon │  │  │  │Tetragon │  │  │  │Tetragon │  │              │
│  │  │ Agent   │  │  │  │ Agent   │  │  │  │ Agent   │  │              │
│  │  │(DaemonSet│  │  │  │(DaemonSet│  │  │  │(DaemonSet│  │              │
│  │  └────┬────┘  │  │  └────┬────┘  │  │  └────┬────┘  │              │
│  │       │       │  │       │       │  │       │       │              │
│  │  ┌────┴────┐  │  │  ┌────┴────┐  │  │  ┌────┴────┐  │              │
│  │  │  eBPF   │  │  │  │  eBPF   │  │  │  │  eBPF   │  │              │
│  │  │Programs │  │  │  │Programs │  │  │  │Programs │  │              │
│  │  └────┬────┘  │  │  └────┬────┘  │  │  └────┬────┘  │              │
│  │       │       │  │       │       │  │       │       │              │
│  │  ┌────┴────┐  │  │  ┌────┴────┐  │  │  ┌────┴────┐  │              │
│  │  │ Kernel  │  │  │  │ Kernel  │  │  │  │ Kernel  │  │              │
│  │  └─────────┘  │  │  └─────────┘  │  │  └─────────┘  │              │
│  └───────────────┘  └───────────────┘  └───────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Role | Description |
|-----------|------|-------------|
| **Tetragon Agent** | Kernel enforcement | DaemonSet that loads eBPF programs |
| **eBPF Programs** | Detection & action | Kernel programs that monitor and enforce |
| **TracingPolicy CRD** | Policy definition | Kubernetes-native security policies |
| **Tetragon CLI** | Debugging | `tetra` command for inspecting events |

---

## Installing Tetragon

### Option 1: Helm (Recommended)

```bash
# Add Cilium Helm repo
helm repo add cilium https://helm.cilium.io
helm repo update

# Install Tetragon
helm install tetragon cilium/tetragon -n kube-system \
  --set tetragon.enableProcessCred=true \
  --set tetragon.enableProcessNs=true

# Verify installation
kubectl -n kube-system get pods -l app.kubernetes.io/name=tetragon
```

### Option 2: Quick Install (Testing)

```bash
# Direct apply
kubectl apply -f https://raw.githubusercontent.com/cilium/tetragon/main/install/kubernetes/tetragon.yaml

# Wait for pods
kubectl -n kube-system wait --for=condition=ready pod -l app.kubernetes.io/name=tetragon --timeout=120s
```

### Install Tetragon CLI

```bash
# Install tetra CLI
GOOS=$(go env GOOS)
GOARCH=$(go env GOARCH)
curl -L --remote-name-all https://github.com/cilium/tetragon/releases/latest/download/tetra-${GOOS}-${GOARCH}.tar.gz
sudo tar -C /usr/local/bin -xzvf tetra-${GOOS}-${GOARCH}.tar.gz
```

### Verify Installation

```bash
# Check Tetragon status
kubectl -n kube-system logs -l app.kubernetes.io/name=tetragon -c tetragon

# Use CLI to see events
kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents
```

---

## TracingPolicy: The Core Concept

TracingPolicy is a Kubernetes CRD that defines what Tetragon monitors and how it responds:

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: example-policy
spec:
  kprobes:
    - call: "sys_execve"           # Which syscall to monitor
      syscall: true
      args:                         # Capture these arguments
        - index: 0
          type: "string"            # Filename being executed
      selectors:
        - matchArgs:
          - index: 0
            operator: "Equal"
            values:
              - "/bin/bash"         # Match specific binaries
          matchActions:
            - action: Sigkill       # Kill the process
```

### TracingPolicy Structure

```
TracingPolicy
├── kprobes[]              # Kernel probe hooks
│   ├── call               # Function name (syscall or kernel function)
│   ├── syscall            # Is this a syscall?
│   ├── args[]             # Arguments to capture
│   └── selectors[]        # Conditions and actions
│       ├── matchArgs[]    # Match on arguments
│       ├── matchPIDs[]    # Match on process IDs
│       ├── matchNamespaces[]  # Match on namespaces
│       └── matchActions[] # What to do on match
│
├── tracepoints[]          # Kernel tracepoint hooks
└── uprobes[]              # Userspace probe hooks
```

---

## Practical Security Policies

### 1. Block Cryptocurrency Miners

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-crypto-miners
spec:
  kprobes:
    - call: "sys_execve"
      syscall: true
      args:
        - index: 0
          type: "string"
      selectors:
        # Block known mining binaries
        - matchArgs:
          - index: 0
            operator: "Postfix"
            values:
              - "xmrig"
              - "cpuminer"
              - "minerd"
              - "cgminer"
              - "bfgminer"
          matchActions:
            - action: Sigkill
```

### 2. Prevent Sensitive File Access

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: protect-sensitive-files
spec:
  kprobes:
    - call: "fd_install"
      syscall: false
      args:
        - index: 0
          type: "int"
        - index: 1
          type: "file"
      selectors:
        - matchArgs:
          - index: 1
            operator: "Equal"
            values:
              - "/etc/shadow"
              - "/etc/passwd"
              - "/root/.ssh/id_rsa"
              - "/var/run/secrets/kubernetes.io"
          matchActions:
            - action: Sigkill
            - action: NotifyEnforcer  # Also send alert
```

### 3. Block Reverse Shells

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-reverse-shells
spec:
  kprobes:
    # Detect shell with network redirect
    - call: "sys_execve"
      syscall: true
      args:
        - index: 0
          type: "string"
        - index: 1
          type: "string"
      selectors:
        - matchArgs:
          - index: 0
            operator: "Postfix"
            values:
              - "bash"
              - "sh"
              - "zsh"
          - index: 1
            operator: "Contains"
            values:
              - "/dev/tcp"
              - "/dev/udp"
              - "nc -e"
              - "bash -i"
          matchActions:
            - action: Sigkill

    # Also block netcat with execute flag
    - call: "sys_execve"
      syscall: true
      args:
        - index: 0
          type: "string"
      selectors:
        - matchArgs:
          - index: 0
            operator: "Postfix"
            values:
              - "nc"
              - "ncat"
              - "netcat"
          matchActions:
            - action: Sigkill
```

### 4. Detect Container Escape Attempts

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-container-escape
spec:
  kprobes:
    # Detect attempts to access host filesystem
    - call: "sys_openat"
      syscall: true
      args:
        - index: 0
          type: "int"
        - index: 1
          type: "string"
      selectors:
        - matchArgs:
          - index: 1
            operator: "Prefix"
            values:
              - "/proc/1/root"      # Host root via PID 1
              - "/host"             # Common host mount path
          matchNamespaces:
            - namespace: Mnt
              operator: NotIn
              values:
                - "4026531840"      # Host mount namespace
          matchActions:
            - action: Sigkill
            - action: NotifyEnforcer
```

### 5. Block Kubectl Exec from Pods

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-kubectl-exec
spec:
  kprobes:
    - call: "sys_execve"
      syscall: true
      args:
        - index: 0
          type: "string"
      selectors:
        - matchArgs:
          - index: 0
            operator: "Postfix"
            values:
              - "kubectl"
          matchNamespaces:
            - namespace: Pid
              operator: NotIn
              values:
                - "host"  # Allow from host only
          matchActions:
            - action: Sigkill
```

---

## Actions Explained

| Action | Effect | Use Case |
|--------|--------|----------|
| `Sigkill` | Immediately kill the process | Stop attacks in progress |
| `Signal` | Send specific signal | Custom process control |
| `Override` | Override syscall return value | Fake "permission denied" |
| `NotifyEnforcer` | Send event to userspace | Alerting without blocking |
| `UnfollowFd` | Stop tracking file descriptor | Performance optimization |
| `CopyFd` | Copy FD for analysis | Forensics |

### Override Example: Fake Permission Denied

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: fake-permission-denied
spec:
  kprobes:
    - call: "sys_openat"
      syscall: true
      args:
        - index: 0
          type: "int"
        - index: 1
          type: "string"
      selectors:
        - matchArgs:
          - index: 1
            operator: "Equal"
            values:
              - "/etc/shadow"
          matchActions:
            - action: Override
              argError: -1  # EPERM - Operation not permitted
```

This returns "Permission denied" without revealing that security monitoring is active.

---

## Monitoring Tetragon Events

### Using the CLI

```bash
# Stream all events
kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents

# Filter by event type
kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents --process-exec

# JSON output for processing
kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents -o json

# Filter by namespace
kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents --namespace production
```

### Event Types

```bash
# Process execution events
tetra getevents --process-exec

# Process exit events
tetra getevents --process-exit

# File access events (requires policy)
tetra getevents --process-kprobe

# Network events (requires policy)
tetra getevents --process-kprobe | grep -i "connect"
```

### Exporting to SIEM

```yaml
# Enable export to stdout (for log collectors)
helm upgrade tetragon cilium/tetragon -n kube-system \
  --set tetragon.export.stdout.enabled=true \
  --set tetragon.export.stdout.format=json

# Events can be collected by Fluentd/Fluent Bit and sent to:
# - Elasticsearch
# - Splunk
# - CloudWatch
# - Any SIEM
```

---

## War Story: The Zero-Second Response

A financial services company was running a multi-tenant Kubernetes platform. They had Falco deployed and felt secure—until a red team exercise showed a terrifying gap.

**The Attack Scenario**:
1. Attacker compromises a web application pod
2. Downloads and executes a cryptocurrency miner
3. Falco detects and alerts
4. Security team responds in 15 minutes
5. **By then, the miner has run for 15 minutes**

**The Problem**:
- Falco's alert arrived in 200ms after execution
- But "after execution" means the damage is done
- 15 minutes of crypto mining = noticeable cloud bill
- More critically: 15 minutes to exfiltrate data

**The Tetragon Solution**:

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-post-exploit-tools
spec:
  kprobes:
    - call: "sys_execve"
      syscall: true
      args:
        - index: 0
          type: "string"
      selectors:
        # Block common post-exploitation binaries
        - matchArgs:
          - index: 0
            operator: "Postfix"
            values:
              - "wget"
              - "curl"
              - "nc"
              - "ncat"
              - "python"
              - "perl"
              - "ruby"
          matchNamespaces:
            - namespace: Pid
              operator: NotIn
              values:
                - "host"
          matchActions:
            - action: Sigkill
            - action: NotifyEnforcer
```

**The Results**:
- Red team attempts to download malware: **Process killed in 0.003ms**
- Miner never executes
- Alert still fires for investigation
- Zero impact from the attack

**The Key Insight**:
> "We went from 'detect and respond' to 'prevent and investigate.' The attack surface didn't change—our response time became effectively zero."

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Too broad policies | Kill legitimate processes | Test in audit mode first, narrow selectors |
| Missing namespace filters | Block host system processes | Always include `matchNamespaces` |
| Not testing policies | Production breakage | Test in staging with `NotifyEnforcer` only |
| Blocking curl/wget globally | Break init containers, health checks | Whitelist specific pods/namespaces |
| Ignoring policy order | Unexpected behavior | Policies are independent, design carefully |
| Not monitoring events | Miss attacks despite policies | Always collect and analyze Tetragon events |

---

## Tetragon + Falco: Defense in Depth

Use both tools together:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Architecture                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Layer 1: Prevention (Tetragon)            │   │
│  │                                                          │   │
│  │  - Block known-bad binaries (miners, exploit tools)      │   │
│  │  - Prevent sensitive file access                         │   │
│  │  - Kill reverse shell attempts                           │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Layer 2: Detection (Falco)                │   │
│  │                                                          │   │
│  │  - Detect anomalous patterns                             │   │
│  │  - Alert on suspicious behavior                          │   │
│  │  - Rich contextual rules                                 │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Layer 3: Response (SIEM/SOAR)             │   │
│  │                                                          │   │
│  │  - Correlate events                                      │   │
│  │  - Trigger automated responses                           │   │
│  │  - Incident investigation                                │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hands-On Exercise: Block a Simulated Attack

**Objective**: Deploy Tetragon policies to prevent a simulated attack chain.

### Setup

```bash
# Create test namespace
kubectl create namespace tetragon-demo

# Deploy a vulnerable-ish application (just a shell for demo)
kubectl apply -n tetragon-demo -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: target-app
  labels:
    app: target
spec:
  containers:
  - name: app
    image: ubuntu:22.04
    command: ["/bin/bash", "-c", "apt-get update && apt-get install -y curl netcat-openbsd && sleep infinity"]
EOF

# Wait for pod
kubectl wait --for=condition=ready pod -n tetragon-demo target-app --timeout=180s
```

### Task 1: Observe Normal Behavior

```bash
# Watch Tetragon events in one terminal
kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents --namespace tetragon-demo

# In another terminal, simulate normal activity
kubectl exec -n tetragon-demo target-app -- ls /
kubectl exec -n tetragon-demo target-app -- cat /etc/hostname
```

### Task 2: Apply Protection Policy

```bash
# Apply a policy to block attack tools
kubectl apply -f - <<EOF
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-attack-tools
spec:
  kprobes:
    - call: "sys_execve"
      syscall: true
      args:
        - index: 0
          type: "string"
      selectors:
        - matchArgs:
          - index: 0
            operator: "Postfix"
            values:
              - "curl"
              - "wget"
              - "nc"
              - "ncat"
          matchNamespaces:
            - namespace: Pod
              operator: In
              values:
                - "tetragon-demo"
          matchActions:
            - action: Sigkill
            - action: NotifyEnforcer
EOF
```

### Task 3: Attempt the "Attack"

```bash
# Try to use curl (should be killed)
kubectl exec -n tetragon-demo target-app -- curl http://example.com

# You should see:
# command terminated with exit code 137 (SIGKILL)

# Try netcat
kubectl exec -n tetragon-demo target-app -- nc -h

# Also killed immediately
```

### Task 4: Check the Events

```bash
# See the enforcement events
kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents -o json | grep -A 20 "SIGKILL"
```

### Task 5: Add File Protection

```bash
kubectl apply -f - <<EOF
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: protect-secrets
spec:
  kprobes:
    - call: "fd_install"
      syscall: false
      args:
        - index: 0
          type: "int"
        - index: 1
          type: "file"
      selectors:
        - matchArgs:
          - index: 1
            operator: "Prefix"
            values:
              - "/etc/shadow"
              - "/var/run/secrets"
          matchNamespaces:
            - namespace: Pod
              operator: In
              values:
                - "tetragon-demo"
          matchActions:
            - action: Sigkill
EOF

# Try to read /etc/shadow
kubectl exec -n tetragon-demo target-app -- cat /etc/shadow
# Process killed
```

### Success Criteria

- [ ] Observed normal events in Tetragon output
- [ ] Applied the block-attack-tools policy
- [ ] Confirmed curl/wget/nc are killed immediately
- [ ] Applied the protect-secrets policy
- [ ] Confirmed sensitive file access is blocked
- [ ] Viewed enforcement events in Tetragon logs

### Cleanup

```bash
kubectl delete namespace tetragon-demo
kubectl delete tracingpolicy block-attack-tools protect-secrets
```

---

## Quiz

### Question 1
What is the fundamental difference between Falco and Tetragon?

<details>
<summary>Show Answer</summary>

**Falco detects threats in userspace and alerts; Tetragon can prevent threats at the kernel level**

Tetragon uses eBPF to operate inside the kernel, allowing it to block syscalls and kill processes before malicious actions complete. Falco monitors syscalls from userspace and alerts after the fact.
</details>

### Question 2
What action immediately terminates a process in Tetragon?

<details>
<summary>Show Answer</summary>

**`action: Sigkill`**

This sends SIGKILL to the process, terminating it immediately without allowing cleanup. The process is killed before the monitored syscall completes.
</details>

### Question 3
What is a TracingPolicy in Tetragon?

<details>
<summary>Show Answer</summary>

**A Kubernetes CRD that defines what Tetragon monitors and how it responds**

TracingPolicy allows you to specify kprobes (kernel probes), tracepoints, or uprobes with selectors for matching conditions and actions to take when matches occur.
</details>

### Question 4
How can you make Tetragon return "Permission denied" without killing the process?

<details>
<summary>Show Answer</summary>

**Use `action: Override` with `argError: -1` (EPERM)**

This overrides the syscall return value to make it appear that permission was denied, without revealing that security monitoring blocked the attempt.
</details>

### Question 5
Why should you include `matchNamespaces` in Tetragon policies?

<details>
<summary>Show Answer</summary>

**To avoid blocking legitimate system processes and to scope policies to specific namespaces**

Without namespace filters, policies might kill essential system processes. The filter ensures policies only apply to intended workloads.
</details>

### Question 6
What command streams Tetragon events in real-time?

<details>
<summary>Show Answer</summary>

**`kubectl exec -n kube-system -ti ds/tetragon -c tetragon -- tetra getevents`**

The `tetra getevents` command connects to the Tetragon agent and streams events. Add `--namespace` to filter by Kubernetes namespace.
</details>

### Question 7
When should you use Tetragon vs Falco?

<details>
<summary>Show Answer</summary>

**Use Tetragon for prevention of known-bad actions; use Falco for detection of suspicious patterns**

Tetragon excels at blocking specific, known-malicious behaviors. Falco excels at detecting anomalous patterns that might indicate novel attacks. Use both for defense in depth.
</details>

### Question 8
What is a kprobe in Tetragon?

<details>
<summary>Show Answer</summary>

**A hook into a kernel function that allows monitoring and taking action when that function is called**

Kprobes are eBPF programs attached to kernel functions. When the function is called (like `sys_execve` for process execution), the kprobe runs and can inspect arguments, apply selectors, and take actions.
</details>

---

## Key Takeaways

1. **Tetragon operates in the kernel** - blocks attacks before they complete
2. **TracingPolicy is the core abstraction** - Kubernetes-native security rules
3. **Sigkill stops processes immediately** - zero-second response time
4. **Override fakes errors** - stealth defense without revealing monitoring
5. **Namespace filters are essential** - scope policies to specific workloads
6. **Use with Falco, not instead of** - prevention + detection = defense in depth
7. **Test policies carefully** - too broad = production breakage
8. **Export events for analysis** - blocking is half the story
9. **Low overhead** - eBPF is production-safe
10. **Kernel-level visibility** - sees what applications can't hide

---

## Further Reading

- [Tetragon Documentation](https://tetragon.cilium.io/docs/) - Official guides
- [TracingPolicy Reference](https://tetragon.cilium.io/docs/concepts/tracing-policy/) - Complete policy syntax
- [Tetragon GitHub](https://github.com/cilium/tetragon) - Source and examples
- [eBPF for Security](https://ebpf.io/applications/#security) - Understanding the technology

---

## Next Module

Continue to [Module 4.6: KubeArmor](../module-4.6-kubearmor/) to learn about runtime security policies with least-privilege enforcement.
