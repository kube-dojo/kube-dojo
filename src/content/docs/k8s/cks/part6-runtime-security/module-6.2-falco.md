---
title: "Module 6.2: Runtime Security with Falco"
slug: k8s/cks/part6-runtime-security/module-6.2-falco
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Critical CKS skill
>
> **Time to Complete**: 50-55 minutes
>
> **Prerequisites**: Module 6.1 (Audit Logging), Linux system calls basics

---

## Why This Module Matters

Audit logs tell you what happened via the API. Falco tells you what's happening inside containers at runtime. It detects suspicious system calls, file access, and network activity that could indicate a breach.

CKS requires understanding Falco for runtime threat detection.

---

## What is Falco?

```
┌─────────────────────────────────────────────────────────────┐
│              FALCO OVERVIEW                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Falco = Runtime Security Engine                           │
│  ─────────────────────────────────────────────────────────  │
│  • Open source (CNCF graduated)                            │
│  • Kernel-level visibility                                 │
│  • Real-time alerting                                      │
│  • Highly configurable rules                               │
│                                                             │
│  How Falco works:                                          │
│                                                             │
│  Container ──► syscalls ──► Kernel ──► Falco Driver       │
│                                               │             │
│                                               ▼             │
│                                       ┌──────────────┐     │
│                                       │ Falco Engine │     │
│                                       │  ┌────────┐  │     │
│                                       │  │ Rules  │  │     │
│                                       │  └────────┘  │     │
│                                       └──────┬───────┘     │
│                                              │              │
│                                              ▼              │
│                                       Alerts/Logs          │
│                                                             │
│  Detects:                                                  │
│  ├── Shell spawned in container                           │
│  ├── Sensitive file read (/etc/shadow)                    │
│  ├── Process privilege escalation                         │
│  ├── Unexpected network connections                       │
│  └── Container escape attempts                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Installing Falco

### On Kubernetes (DaemonSet)

```bash
# Add Falco Helm repo
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install Falco
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# Check installation
kubectl get pods -n falco
```

### On Linux Host

```bash
# Add Falco repository (Debian/Ubuntu)
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] https://download.falco.org/packages/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/falcosecurity.list

# Install
sudo apt update && sudo apt install -y falco

# Start Falco
sudo systemctl start falco
sudo systemctl enable falco

# View logs
sudo journalctl -u falco -f
```

---

## Falco Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              FALCO COMPONENTS                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Driver (kernel module or eBPF)                            │
│  ─────────────────────────────────────────────────────────  │
│  • Captures system calls from kernel                       │
│  • Minimal overhead                                        │
│  • Options: kernel module, eBPF probe, userspace          │
│                                                             │
│  Engine (libsinsp + libscap)                               │
│  ─────────────────────────────────────────────────────────  │
│  • Processes syscall events                                │
│  • Enriches with container/K8s metadata                   │
│  • Evaluates against rules                                 │
│                                                             │
│  Rules Engine                                              │
│  ─────────────────────────────────────────────────────────  │
│  • YAML-based rule definitions                            │
│  • Conditions using Falco filter syntax                   │
│  • Customizable priorities and outputs                    │
│                                                             │
│  Output Channels                                           │
│  ─────────────────────────────────────────────────────────  │
│  • stdout/stderr                                           │
│  • File                                                    │
│  • Syslog                                                  │
│  • HTTP webhook (Falcosidekick)                           │
│  • gRPC                                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Falco Rules

### Rule Structure

```yaml
# A Falco rule has these components:
- rule: <name>
  desc: <description>
  condition: <filter expression>
  output: <output message with fields>
  priority: <severity level>
  tags: [list, of, tags]
  enabled: true/false
```

### Built-in Rules Examples

```yaml
# Detect shell spawned in container
- rule: Terminal shell in container
  desc: A shell was used as the entrypoint/exec point into a container
  condition: >
    spawned_process and container and
    shell_procs and proc.tty != 0
  output: >
    A shell was spawned in a container
    (user=%user.name container=%container.name shell=%proc.name
    parent=%proc.pname cmdline=%proc.cmdline)
  priority: NOTICE
  tags: [container, shell, mitre_execution]

# Detect sensitive file read
- rule: Read sensitive file untrusted
  desc: Attempt to read sensitive files from untrusted process
  condition: >
    sensitive_files and open_read and
    not proc.name in (allowed_readers)
  output: >
    Sensitive file opened (user=%user.name command=%proc.cmdline
    file=%fd.name container=%container.name)
  priority: WARNING
  tags: [filesystem, mitre_credential_access]

# Detect unexpected outbound connection
- rule: Unexpected outbound connection
  desc: Container making outbound connection to internet
  condition: >
    outbound and container and
    not allowed_outbound
  output: >
    Unexpected outbound connection (container=%container.name
    command=%proc.cmdline connection=%fd.name)
  priority: WARNING
  tags: [network, mitre_command_and_control]
```

---

## Falco Filter Syntax

### Common Fields

```yaml
# Process fields
proc.name          # Process name (e.g., "bash")
proc.pname         # Parent process name
proc.cmdline       # Full command line
proc.pid           # Process ID
proc.ppid          # Parent process ID
proc.exepath       # Executable path

# User fields
user.name          # Username
user.uid           # User ID

# Container fields
container.name     # Container name
container.id       # Container ID
container.image    # Image name
k8s.pod.name       # Kubernetes pod name
k8s.ns.name        # Kubernetes namespace

# File fields
fd.name            # File/socket name
fd.directory       # Directory name
fd.filename        # Base filename

# Network fields
fd.sip             # Source IP
fd.dip             # Destination IP
fd.sport           # Source port
fd.dport           # Destination port
```

### Operators and Macros

```yaml
# Operators
=, !=              # Equality
<, <=, >, >=       # Comparison
contains           # String contains
startswith         # String starts with
endswith           # String ends with
in                 # List membership
pmatch             # Prefix match for paths

# Logical operators
and, or, not

# Built-in macros
spawned_process    # A new process was spawned
open_read          # File opened for reading
open_write         # File opened for writing
container          # Event from a container
outbound           # Outbound network connection
inbound            # Inbound network connection
```

---

## Custom Rules

### Creating Custom Rules

```yaml
# /etc/falco/rules.d/custom-rules.yaml

# Detect kubectl exec
- rule: kubectl exec into pod
  desc: Detect kubectl exec or attach to a pod
  condition: >
    spawned_process and container and
    proc.name in (bash, sh, ash) and
    proc.pname in (runc, containerd-shim)
  output: >
    kubectl exec detected (user=%user.name pod=%k8s.pod.name
    namespace=%k8s.ns.name command=%proc.cmdline)
  priority: WARNING
  tags: [k8s, exec]

# Detect crypto miner
- rule: Detect cryptocurrency miner
  desc: Detect process names associated with crypto mining
  condition: >
    spawned_process and
    proc.name in (xmrig, cpuminer, minerd, cgminer, bfgminer)
  output: >
    Cryptocurrency miner detected (process=%proc.name
    cmdline=%proc.cmdline container=%container.name)
  priority: CRITICAL
  tags: [cryptomining]

# Detect container escape via mount
- rule: Container escape via mount
  desc: Detect attempts to escape container via host filesystem mount
  condition: >
    container and
    (evt.type = mount or evt.type = umount) and
    not proc.name in (mount, umount)
  output: >
    Container mount attempt (command=%proc.cmdline
    container=%container.name)
  priority: CRITICAL
  tags: [container_escape]
```

### Using Lists and Macros

```yaml
# Define a list
- list: allowed_processes
  items: [nginx, python, node, java]

# Define a macro
- macro: in_allowed_processes
  condition: proc.name in (allowed_processes)

# Use in rule
- rule: Unexpected process in production
  desc: Non-whitelisted process running in production namespace
  condition: >
    spawned_process and
    container and
    k8s.ns.name = "production" and
    not in_allowed_processes
  output: >
    Unexpected process (proc=%proc.name pod=%k8s.pod.name
    namespace=%k8s.ns.name)
  priority: WARNING
```

---

## Falco Configuration

### Main Configuration

```yaml
# /etc/falco/falco.yaml

# Output configuration
json_output: true
json_include_output_property: true

# Buffered outputs
buffered_outputs: false

# File output
file_output:
  enabled: true
  keep_alive: false
  filename: /var/log/falco/events.json

# Stdout output
stdout_output:
  enabled: true

# Syslog output
syslog_output:
  enabled: false

# HTTP output (webhook)
http_output:
  enabled: true
  url: http://falcosidekick:2801

# Rules files
rules_file:
  - /etc/falco/falco_rules.yaml
  - /etc/falco/falco_rules.local.yaml
  - /etc/falco/rules.d
```

### Priority Levels

```yaml
# Falco priority levels (highest to lowest)
EMERGENCY   # System is unusable
ALERT       # Action must be taken immediately
CRITICAL    # Critical conditions
ERROR       # Error conditions
WARNING     # Warning conditions
NOTICE      # Normal but significant
INFO        # Informational messages
DEBUG       # Debug-level messages
```

---

## Real Exam Scenarios

### Scenario 1: Detect Shell in Container

```bash
# Check if Falco is running
sudo systemctl status falco

# Create rule to detect shell
cat <<EOF | sudo tee /etc/falco/rules.d/shell-detection.yaml
- rule: Shell in container
  desc: Detect shell spawned in container
  condition: >
    spawned_process and
    container and
    proc.name in (bash, sh, ash, zsh)
  output: >
    Shell spawned (container=%container.name shell=%proc.name
    cmdline=%proc.cmdline user=%user.name)
  priority: WARNING
  tags: [shell, container]
EOF

# Restart Falco
sudo systemctl restart falco

# Test by exec into a pod
kubectl exec -it nginx-pod -- /bin/bash

# Check Falco logs
sudo grep "Shell spawned" /var/log/falco/events.json | jq .
```

### Scenario 2: Detect Sensitive File Access

```yaml
# /etc/falco/rules.d/sensitive-files.yaml
- list: sensitive_files
  items:
    - /etc/shadow
    - /etc/passwd
    - /etc/kubernetes/pki
    - /var/run/secrets/kubernetes.io

- rule: Access to sensitive files
  desc: Detect reads of sensitive system files
  condition: >
    open_read and
    fd.name in (sensitive_files)
  output: >
    Sensitive file accessed (file=%fd.name user=%user.name
    process=%proc.name container=%container.name)
  priority: WARNING
  tags: [filesystem, sensitive]
```

### Scenario 3: Alert on Network Activity

```yaml
# /etc/falco/rules.d/network-rules.yaml
- rule: Unexpected outbound connection
  desc: Container making unexpected outbound connection
  condition: >
    outbound and
    container and
    fd.dport in (22, 23, 3389)
  output: >
    Suspicious outbound connection (container=%container.name
    process=%proc.cmdline dest=%fd.sip:%fd.dport)
  priority: CRITICAL
  tags: [network, lateral_movement]
```

---

## Falco Output Analysis

### Parse Falco JSON Output

```bash
# View recent alerts
tail -100 /var/log/falco/events.json | jq .

# Count alerts by rule
cat /var/log/falco/events.json | jq -r '.rule' | sort | uniq -c | sort -rn

# Find critical alerts
cat /var/log/falco/events.json | jq 'select(.priority == "Critical")'

# Find alerts from specific namespace
cat /var/log/falco/events.json | jq 'select(.output_fields["k8s.ns.name"] == "production")'

# Find shell alerts
cat /var/log/falco/events.json | jq 'select(.rule | contains("shell"))'
```

### Sample Falco Alert

```json
{
  "hostname": "node-1",
  "output": "Shell spawned in container (user=root container=nginx shell=bash cmdline=bash)",
  "priority": "Warning",
  "rule": "Terminal shell in container",
  "source": "syscall",
  "tags": ["container", "shell", "mitre_execution"],
  "time": "2024-01-15T10:30:00.123456789Z",
  "output_fields": {
    "container.name": "nginx",
    "k8s.ns.name": "production",
    "k8s.pod.name": "nginx-abc123",
    "proc.cmdline": "bash",
    "proc.name": "bash",
    "user.name": "root"
  }
}
```

---

## Did You Know?

- **Falco uses eBPF** (extended Berkeley Packet Filter) as its default driver in newer versions. eBPF is safer and more portable than kernel modules.

- **Falco is a CNCF graduated project**, meaning it's production-ready and widely adopted. It's the de-facto standard for Kubernetes runtime security.

- **Falco rules are similar to Sysdig filters**. Sysdig (the company behind Falco) created the filter syntax.

- **Falcosidekick** is a companion tool that routes Falco alerts to Slack, Teams, PagerDuty, SIEM systems, and 40+ other outputs.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Too many rules enabled | Alert fatigue | Start with critical rules |
| Not tuning rules | False positives | Add exceptions for known behavior |
| Ignoring alerts | Breaches missed | Set up proper alerting pipeline |
| Rules not loaded | No detection | Check /var/log/falco for errors |
| Missing container metadata | Hard to investigate | Ensure K8s enrichment enabled |

---

## Quiz

1. **What does Falco monitor to detect threats?**
   <details>
   <summary>Answer</summary>
   Falco monitors system calls (syscalls) from the kernel. It intercepts calls like open, exec, connect, etc. and evaluates them against rules.
   </details>

2. **What's the difference between a Falco rule and a macro?**
   <details>
   <summary>Answer</summary>
   A rule defines a complete detection with condition, output, and priority. A macro is a reusable condition fragment that can be used in multiple rules.
   </details>

3. **How do you add custom Falco rules without modifying the default rules file?**
   <details>
   <summary>Answer</summary>
   Create files in `/etc/falco/rules.d/` directory. Falco automatically loads all YAML files from this directory.
   </details>

4. **What Falco fields identify Kubernetes context?**
   <details>
   <summary>Answer</summary>
   `k8s.pod.name`, `k8s.ns.name`, `k8s.deployment.name`, `container.name`, `container.id`, `container.image`.
   </details>

---

## Hands-On Exercise

**Task**: Create and test Falco rules for common threats.

```bash
# Step 1: Check if Falco is available
which falco && falco --version || echo "Falco not installed"

# Step 2: Create custom rules file
cat <<'EOF' > /tmp/custom-falco-rules.yaml
# Custom security rules

# Detect shell in container
- rule: Shell spawned in container
  desc: Shell process started in container
  condition: >
    spawned_process and
    container and
    proc.name in (bash, sh, ash, zsh, csh, fish)
  output: >
    Shell spawned (container=%container.name shell=%proc.name
    user=%user.name cmdline=%proc.cmdline pod=%k8s.pod.name)
  priority: WARNING
  tags: [shell, container]

# Detect package manager usage
- rule: Package manager in container
  desc: Package manager executed in running container
  condition: >
    spawned_process and
    container and
    proc.name in (apt, apt-get, yum, dnf, apk, pip, npm)
  output: >
    Package manager used (container=%container.name
    command=%proc.cmdline user=%user.name)
  priority: NOTICE
  tags: [package, container]

# Detect write to /etc
- rule: Write to /etc in container
  desc: Write to /etc directory detected
  condition: >
    container and
    open_write and
    fd.directory = /etc
  output: >
    Write to /etc (container=%container.name file=%fd.name
    process=%proc.name user=%user.name)
  priority: WARNING
  tags: [filesystem, container]

# Detect outbound SSH
- rule: Outbound SSH connection
  desc: Outbound SSH connection from container
  condition: >
    container and
    outbound and
    fd.dport = 22
  output: >
    Outbound SSH (container=%container.name dest=%fd.sip:%fd.dport
    process=%proc.cmdline)
  priority: WARNING
  tags: [network, ssh]
EOF

echo "=== Custom Rules Created ==="
cat /tmp/custom-falco-rules.yaml

# Step 3: Validate rules syntax
echo "=== Validating Rules ==="
python3 -c "import yaml; yaml.safe_load(open('/tmp/custom-falco-rules.yaml'))" && echo "Valid YAML"

# Step 4: Demonstrate rule analysis
echo "=== Rule Analysis ==="
echo "Rules created:"
grep "^- rule:" /tmp/custom-falco-rules.yaml | sed 's/- rule:/  -/'

echo ""
echo "Priority levels used:"
grep "priority:" /tmp/custom-falco-rules.yaml | sort | uniq

# Step 5: Sample Falco output analysis
cat <<'EOF' > /tmp/sample-falco-events.json
{"time":"2024-01-15T10:00:00Z","rule":"Shell spawned in container","priority":"Warning","output":"Shell spawned (container=nginx shell=bash user=root)","output_fields":{"container.name":"nginx","k8s.ns.name":"default","proc.name":"bash"}}
{"time":"2024-01-15T10:05:00Z","rule":"Package manager in container","priority":"Notice","output":"Package manager used (container=app command=apt-get install curl)","output_fields":{"container.name":"app","k8s.ns.name":"production","proc.cmdline":"apt-get install curl"}}
{"time":"2024-01-15T10:10:00Z","rule":"Outbound SSH connection","priority":"Warning","output":"Outbound SSH (container=suspicious dest=10.0.0.5:22)","output_fields":{"container.name":"suspicious","k8s.ns.name":"default","fd.dport":"22"}}
EOF

echo "=== Sample Event Analysis ==="
echo "All events by priority:"
cat /tmp/sample-falco-events.json | jq -r '.priority' | sort | uniq -c

echo ""
echo "Warning events:"
cat /tmp/sample-falco-events.json | jq 'select(.priority == "Warning") | {rule: .rule, container: .output_fields["container.name"]}'

# Cleanup
rm -f /tmp/custom-falco-rules.yaml /tmp/sample-falco-events.json
```

**Success criteria**: Understand Falco rule structure and alert analysis.

---

## Summary

**Falco Basics**:
- Runtime security monitoring
- Kernel-level syscall inspection
- Rule-based threat detection
- Real-time alerting

**Rule Components**:
- condition (filter expression)
- output (alert message with fields)
- priority (severity level)
- tags (categorization)

**Common Detections**:
- Shell in container
- Sensitive file access
- Package manager usage
- Unexpected network connections

**Exam Tips**:
- Know rule syntax
- Understand common fields
- Be able to create custom rules
- Know how to analyze alerts

---

## Next Module

[Module 6.3: Container Investigation](../module-6.3-container-investigation/) - Analyzing suspicious container behavior.
