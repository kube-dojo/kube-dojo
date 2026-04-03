---
title: "Module 4.3: Falco & Runtime Security"
slug: platform/toolkits/security-quality/security-tools/module-4.3-falco
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 minutes

## Overview

Admission control stops bad configurations, but what about runtime attacks? A container might be deployed safely then get compromised. This module covers Falco, the cloud-native runtime security tool that detects threats in running containers by monitoring system calls.

**What You'll Learn**:
- Falco architecture and syscall monitoring
- Writing and tuning Falco rules
- Alert routing and response
- Integration with incident response

**Prerequisites**:
- [Security Principles Foundations](../../../foundations/security-principles/)
- Linux basics (processes, files, networking)
- Kubernetes networking concepts

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Falco with eBPF driver for runtime security monitoring of Kubernetes workloads**
- **Configure custom Falco rules to detect suspicious container behavior (shell access, file modifications, network connections)**
- **Implement Falco alert routing to Slack, PagerDuty, and SIEM systems for security incident response**
- **Integrate Falco with Kubernetes admission controllers for runtime-informed deployment decisions**


## Why This Module Matters

Prevention eventually fails. When it does, you need detection. Falco watches what containers actually DO—not what they claim they'll do. Cryptominer spawning a process? Detected. Shell opened in a webserver container? Detected. Sensitive file read by unauthorized process? Detected.

> 💡 **Did You Know?** Falco was created by Sysdig and donated to CNCF in 2018. It uses eBPF (extended Berkeley Packet Filter) to hook into the Linux kernel and monitor every system call with near-zero overhead. It's like having a security camera for every container's soul.

---

## Runtime Security Landscape

```
SECURITY LAYERS
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    WHEN DOES IT CHECK?                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BUILD TIME                                                      │
│  ┌───────────────────────────────────────┐                      │
│  │ Image Scanning (Trivy, Snyk)          │                      │
│  │ SAST, secrets detection               │                      │
│  └───────────────────────────────────────┘                      │
│                     │                                            │
│                     ▼                                            │
│  DEPLOY TIME                                                     │
│  ┌───────────────────────────────────────┐                      │
│  │ Admission Control (Gatekeeper, Kyverno)│                     │
│  │ Image signature verification          │                      │
│  └───────────────────────────────────────┘                      │
│                     │                                            │
│                     ▼                                            │
│  RUNTIME ◀── YOU ARE HERE                                       │
│  ┌───────────────────────────────────────┐                      │
│  │ Syscall Monitoring (Falco)            │                      │
│  │ Network policies enforcement          │                      │
│  │ File integrity monitoring             │                      │
│  └───────────────────────────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Falco Architecture

```
FALCO ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                         NODE                                     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LINUX KERNEL                          │   │
│  │                                                          │   │
│  │   Process A ──┐                                          │   │
│  │   Process B ──┼──▶ System Calls ──▶ eBPF Probe          │   │
│  │   Process C ──┘    (open, exec,     (captures all)       │   │
│  │                     connect...)                          │   │
│  └───────────────────────────────────┬─────────────────────┘   │
│                                      │                          │
│                                      ▼                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                        FALCO                               │ │
│  │                                                            │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │ │
│  │  │   Driver    │───▶│   Engine    │───▶│   Outputs   │   │ │
│  │  │ (eBPF/kmod) │    │  (rules)    │    │ (alerts)    │   │ │
│  │  └─────────────┘    └─────────────┘    └─────────────┘   │ │
│  │                                              │             │ │
│  │                                              ▼             │ │
│  │                          ┌───────────────────────────────┐│ │
│  │                          │ stdout, syslog, webhook,      ││ │
│  │                          │ Slack, PagerDuty, Kafka...    ││ │
│  │                          └───────────────────────────────┘│ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Driver Options

| Driver | Pros | Cons |
|--------|------|------|
| **eBPF** | No kernel module, safer, modern | Needs kernel 4.14+ |
| **Kernel Module** | Works on older kernels | Requires kernel headers, more risk |
| **Modern eBPF (CO-RE)** | Portable across kernel versions | Needs kernel 5.8+ |

### Installation

```bash
# Add Falco Helm repo
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install with eBPF driver (recommended)
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true \
  --set driver.kind=ebpf

# Verify
kubectl get pods -n falco
kubectl logs -n falco -l app.kubernetes.io/name=falco
```

---

## Falco Rules

### Rule Structure

```yaml
# A Falco rule has these components:

- rule: Shell Spawned in Container
  desc: Detect shell execution in a container
  condition: >
    spawned_process and
    container and
    shell_procs
  output: >
    Shell spawned in container
    (user=%user.name container=%container.name
     shell=%proc.name parent=%proc.pname
     cmdline=%proc.cmdline)
  priority: WARNING
  tags: [container, shell, mitre_execution]
```

### Condition Components

```yaml
# Macros - reusable condition fragments
- macro: container
  condition: container.id != host

- macro: shell_procs
  condition: proc.name in (bash, sh, zsh, ksh, csh, dash)

- macro: spawned_process
  condition: evt.type = execve and evt.dir = <

# Lists - reusable value sets
- list: sensitive_files
  items: [/etc/shadow, /etc/passwd, /etc/sudoers]

- list: allowed_shells
  items: [bash, sh]
```

### Common Detection Rules

```yaml
# 1. Cryptominer Detection
- rule: Detect Cryptominer
  desc: Detect cryptocurrency mining activity
  condition: >
    spawned_process and
    (proc.name in (xmrig, minerd, cpuminer) or
     proc.cmdline contains "stratum+tcp" or
     proc.cmdline contains "mining" or
     proc.cmdline contains "--coin")
  output: >
    Cryptominer detected
    (user=%user.name command=%proc.cmdline container=%container.name)
  priority: CRITICAL
  tags: [cryptomining, mitre_impact]

# 2. Reverse Shell Detection
- rule: Reverse Shell
  desc: Detect reverse shell connections
  condition: >
    spawned_process and
    proc.name in (bash, sh, nc, ncat) and
    fd.type = ipv4 and
    fd.direction = out
  output: >
    Reverse shell detected
    (user=%user.name command=%proc.cmdline connection=%fd.name)
  priority: CRITICAL
  tags: [network, mitre_execution]

# 3. Sensitive File Access
- rule: Read Sensitive File
  desc: Detect read of sensitive files
  condition: >
    open_read and
    fd.name in (sensitive_files) and
    not trusted_process
  output: >
    Sensitive file read
    (user=%user.name file=%fd.name process=%proc.name)
  priority: WARNING
  tags: [filesystem, mitre_credential_access]

# 4. Package Manager in Container
- rule: Package Manager Execution in Container
  desc: Package managers should not run in containers
  condition: >
    spawned_process and
    container and
    proc.name in (apt, apt-get, yum, dnf, apk, pip)
  output: >
    Package manager run in container
    (user=%user.name command=%proc.cmdline container=%container.name)
  priority: ERROR
  tags: [container, mitre_persistence]

# 5. Container Escape Attempt
- rule: Container Escape via Mount
  desc: Detect attempt to mount host filesystem
  condition: >
    evt.type = mount and
    container and
    not allowed_mount
  output: >
    Mount attempt in container (possible escape)
    (user=%user.name command=%proc.cmdline container=%container.name)
  priority: CRITICAL
  tags: [container, escape, mitre_privilege_escalation]
```

> 💡 **Did You Know?** Falco rules use MITRE ATT&CK tags to map detections to the attacker's tactics. This helps SOC teams understand not just what happened, but why an attacker might do it. The MITRE framework categorizes attacks into techniques like Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, and Impact.

---

## Rule Tuning

### The False Positive Problem

```
RULE LIFECYCLE
════════════════════════════════════════════════════════════════════

Initial Deploy ──▶ Alert Storm ──▶ Tune Rules ──▶ Stable Detection
                    (too noisy)     (exceptions)    (useful alerts)

Common tuning needs:
• Legitimate shell access (kubectl exec for debugging)
• Backup tools reading sensitive files
• Init containers running package managers
• Sidecar containers with special permissions
```

### Adding Exceptions

```yaml
# Method 1: Macro exceptions
- macro: trusted_shell_process
  condition: >
    (container.image.repository = "gcr.io/my-project/debug-tools") or
    (k8s.pod.name startswith "maintenance-")

- rule: Shell Spawned in Container
  condition: >
    spawned_process and
    container and
    shell_procs and
    not trusted_shell_process  # Added exception
  # ... rest of rule

# Method 2: List exceptions
- list: allowed_package_manager_images
  items: [
    gcr.io/my-project/builder,
    docker.io/library/python  # pip during build
  ]

- rule: Package Manager Execution in Container
  condition: >
    spawned_process and
    container and
    proc.name in (apt, apt-get, yum, dnf, apk, pip) and
    not container.image.repository in (allowed_package_manager_images)
```

### Custom Rules File

```yaml
# custom-rules.yaml
customRules:
  my-rules.yaml: |-
    # Override default rule
    - rule: Terminal Shell in Container
      enabled: false  # Disable noisy default rule

    # Add our tuned version
    - rule: Unexpected Shell in Container
      desc: Shell in production container (excluding debug pods)
      condition: >
        spawned_process and
        container and
        shell_procs and
        not k8s.ns.name = "debug" and
        not k8s.pod.label.shell-allowed = "true"
      output: >
        Shell spawned (user=%user.name container=%container.name
        namespace=%k8s.ns.name pod=%k8s.pod.name)
      priority: WARNING
```

```bash
# Deploy with custom rules
helm upgrade falco falcosecurity/falco \
  --namespace falco \
  -f custom-rules.yaml
```

---

## Alert Routing with Falcosidekick

```
FALCOSIDEKICK ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Falco ──▶ Falcosidekick ──┬──▶ Slack                          │
│            (router)        ├──▶ PagerDuty                       │
│                           ├──▶ Prometheus                       │
│                           ├──▶ Elasticsearch                    │
│                           ├──▶ Loki                             │
│                           ├──▶ AWS Lambda                       │
│                           ├──▶ Webhook (custom)                 │
│                           └──▶ Kubernetes Response              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration

```yaml
# Falcosidekick config
falcosidekick:
  enabled: true
  config:
    slack:
      webhookurl: "https://hooks.slack.com/services/XXX/YYY/ZZZ"
      minimumpriority: "warning"
      messageformat: "fields"

    pagerduty:
      apikey: "your-api-key"
      minimumpriority: "critical"

    prometheus:
      enabled: true

    # Automatic response via Kubernetes
    kubernetestailor:
      enabled: true
      # Delete pod on critical alert
      annotations:
        annotation.falco.enabled: "true"
        annotation.falco.deletepod: "true"
```

### Response Actions

```yaml
# Automatic pod deletion on critical alerts
apiVersion: v1
kind: Pod
metadata:
  name: protected-app
  annotations:
    falco.enabled: "true"
    falco.deletepod: "true"  # Delete if Falco detects critical event
spec:
  containers:
  - name: app
    image: myapp:latest
```

> 💡 **Did You Know?** Falcosidekick can trigger AWS Lambda functions on alerts. Teams use this for automated response—quarantining pods, capturing forensic data, or creating tickets. One team built a Lambda that automatically captures memory dumps of suspicious containers before terminating them.

---

## Kubernetes Integration

### Pod Labels and Annotations in Rules

```yaml
- rule: Shell in Production Pod Without Debug Label
  condition: >
    spawned_process and
    container and
    shell_procs and
    k8s.ns.name = "production" and
    not k8s.pod.label.allow-shell = "true"
  output: >
    Unauthorized shell in production
    (pod=%k8s.pod.name namespace=%k8s.ns.name user=%user.name)
  priority: CRITICAL
```

### Available Kubernetes Fields

| Field | Description | Example |
|-------|-------------|---------|
| `k8s.pod.name` | Pod name | `nginx-5d4c7b8f-abc12` |
| `k8s.ns.name` | Namespace | `production` |
| `k8s.deployment.name` | Deployment name | `nginx` |
| `k8s.pod.label.<key>` | Pod label value | `k8s.pod.label.app` |
| `container.image.repository` | Image without tag | `nginx` |
| `container.image.tag` | Image tag | `1.21` |

> 💡 **Did You Know?** Falco can detect threats across 350+ system calls, but you don't need to know them all. The default rules cover the most common attack patterns, and the community constantly updates them. When the Log4Shell vulnerability hit, Falco community rules were updated within hours to detect exploitation attempts—faster than most signature-based tools.

---

## Debugging and Operations

### Checking Falco Status

```bash
# Falco pod logs
kubectl logs -n falco -l app.kubernetes.io/name=falco -f

# Check rules loaded
kubectl exec -n falco -it $(kubectl get pod -n falco -l app.kubernetes.io/name=falco -o jsonpath='{.items[0].metadata.name}') -- falco --list

# Verify driver loaded
kubectl exec -n falco -it <falco-pod> -- falco --version

# Test rule with dry-run
kubectl exec -n falco -it <falco-pod> -- falco -r /etc/falco/rules.d/my-rules.yaml --dry-run
```

### Generating Test Events

```bash
# Trigger shell detection
kubectl run test-shell --image=busybox --rm -it --restart=Never -- /bin/sh

# Trigger sensitive file access
kubectl run test-read --image=busybox --rm -it --restart=Never -- cat /etc/shadow

# Trigger package manager detection
kubectl run test-pkg --image=ubuntu --rm -it --restart=Never -- apt update
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Deploying default rules to prod | Alert fatigue (thousands of alerts) | Tune rules in staging first |
| Using kernel module on managed K8s | Module installation blocked | Use eBPF driver (or Modern eBPF) |
| Not correlating with K8s metadata | "Process X did Y" isn't actionable | Ensure K8s metadata enrichment is on |
| Blocking all shells | Can't debug anything | Allow shells in debug namespace, require label |
| Not testing rules | Rules don't fire as expected | Use `--dry-run` and test events |
| Ignoring driver errors | Falco running but not monitoring | Check logs for driver load failures |

---

## War Story: The Cryptominer That Hid in Plain Sight

*A team had Falco running but missed a cryptominer for 3 weeks. CPU usage was high but attributed to "traffic growth."*

**What went wrong**: The attacker modified their miner to:
1. Run as a process named `nginx-worker` (not `xmrig`)
2. Connect to mining pool via HTTPS (not `stratum+tcp`)
3. Only use 50% CPU (not 100%)

**The detection that finally worked**:
```yaml
- rule: Unusual Outbound Connection from Web Container
  condition: >
    outbound and
    container.image.repository contains "nginx" and
    not fd.sip in (known_api_endpoints) and
    fd.sport != 80 and fd.sport != 443
  output: >
    Nginx container connecting to unexpected destination
    (dest=%fd.sip:%fd.sport container=%container.name)
  priority: WARNING
```

**Lesson**: Behavioral detection (what SHOULDN'T this container do?) catches novel attacks better than signature detection (known bad process names).

---

## Quiz

### Question 1
What's the difference between build-time and runtime security scanning?

<details>
<summary>Show Answer</summary>

**Build-time** (Trivy, Snyk):
- Scans images for known vulnerabilities (CVEs)
- Checks dependencies, base images
- Happens BEFORE deployment
- Can't detect: runtime exploits, zero-days, behavioral attacks

**Runtime** (Falco):
- Monitors actual process behavior
- Detects: shells spawning, file access, network connections
- Happens DURING execution
- Catches: supply chain attacks that passed image scans, insider threats, zero-days

Both are needed—defense in depth.

</details>

### Question 2
Why might Falco not detect a shell spawned via `kubectl exec`?

<details>
<summary>Show Answer</summary>

Common reasons:
1. **Rule disabled or tuned out** - Shell rules often have exceptions
2. **Driver not loaded** - eBPF probe failed to attach
3. **Wrong container runtime** - Need appropriate config for containerd/CRI-O
4. **Namespace excluded** - Some rules exclude kube-system or debug namespaces

Debug:
```bash
# Check if Falco is receiving events
kubectl logs -n falco <falco-pod> | grep -i shell

# Verify driver
kubectl exec -n falco <falco-pod> -- falco --version
```

</details>

### Question 3
How do you reduce false positives without missing real attacks?

<details>
<summary>Show Answer</summary>

**Good approaches**:
1. Add specific exceptions (image, namespace, pod label)
2. Use behavioral baselines ("what should this container do?")
3. Tune severity, not disable rules
4. Exception by business context (debug namespace)

**Bad approaches**:
- Disable entire rule categories
- Raise all severity thresholds
- Only alert on CRITICAL

**Best practice**: Label pods that SHOULD have special access:
```yaml
metadata:
  labels:
    allow-shell: "true"  # Explicitly authorized
```

Then rules can check: `not k8s.pod.label.allow-shell = "true"`

</details>

---

## Hands-On Exercise

### Objective
Deploy Falco, trigger detection rules, and route alerts.

### Environment Setup

```bash
# Install Falco with Falcosidekick
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=ebpf \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=falco -n falco --timeout=120s

# Port-forward Falcosidekick UI
kubectl port-forward svc/falco-falcosidekick-ui -n falco 2802:2802 &
```

### Tasks

1. **Verify Falco is running**:
   ```bash
   kubectl logs -n falco -l app.kubernetes.io/name=falco | tail -20
   ```

2. **Trigger shell detection**:
   ```bash
   kubectl run shell-test --image=busybox --rm -it --restart=Never -- /bin/sh -c "echo pwned"
   ```

3. **Check Falco logs for alert**:
   ```bash
   kubectl logs -n falco -l app.kubernetes.io/name=falco | grep -i shell
   ```

4. **Trigger sensitive file read**:
   ```bash
   kubectl run read-test --image=busybox --rm -it --restart=Never -- cat /etc/shadow
   ```

5. **View alerts in Falcosidekick UI**:
   - Open http://localhost:2802
   - See events with Kubernetes metadata

6. **Add custom rule** to detect curl/wget:
   ```yaml
   # Create ConfigMap with custom rule
   kubectl create configmap custom-falco-rules -n falco --from-literal=rules.yaml='
   - rule: Download Tool in Container
     desc: Detect download tools that could fetch malware
     condition: >
       spawned_process and
       container and
       proc.name in (curl, wget)
     output: Download tool executed (user=%user.name command=%proc.cmdline container=%container.name)
     priority: WARNING
   '
   ```

### Success Criteria
- [ ] Falco pod running with eBPF driver
- [ ] Shell execution in container detected and logged
- [ ] Sensitive file access detected
- [ ] Events visible in Falcosidekick UI
- [ ] Custom download tool rule fires on `curl` command

### Bonus Challenge
Create a rule that detects base64 decoding (common in obfuscated attacks):
```bash
kubectl run b64-test --image=busybox --rm -it --restart=Never -- sh -c "echo aGVsbG8= | base64 -d"
```

---

## Further Reading

- [Falco Documentation](https://falco.org/docs/)
- [Falco Rules Repository](https://github.com/falcosecurity/rules)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [Falcosidekick Outputs](https://github.com/falcosecurity/falcosidekick)

---

## Next Module

Continue to [Module 4.4: Supply Chain Security](../module-4.4-supply-chain/) to learn about securing container images with signing, SBOMs, and vulnerability scanning.

---

*"Trust nothing. Verify everything. Monitor constantly. That's runtime security."*
