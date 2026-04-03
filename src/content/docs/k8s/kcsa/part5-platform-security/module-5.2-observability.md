---
title: "Module 5.2: Security Observability"
slug: k8s/kcsa/part5-platform-security/module-5.2-observability
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 5.1: Image Security](../module-5.1-image-security/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** audit logging configurations for completeness of security-relevant event capture
2. **Assess** which observability signals (logs, metrics, events) detect which threat categories
3. **Identify** gaps in security monitoring that would leave attacks undetected
4. **Explain** how to correlate audit logs, runtime alerts, and network telemetry during incident investigation

---

## Why This Module Matters

You can't protect what you can't see. Security observability—logs, metrics, traces, and events—provides visibility into cluster behavior, enabling detection of threats, investigation of incidents, and verification of security controls.

KCSA tests your understanding of Kubernetes security monitoring, audit logging, and runtime detection tools.

---

## Security Observability Pillars

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY OBSERVABILITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LOGS                                                      │
│  ├── API server audit logs                                 │
│  ├── Container application logs                            │
│  ├── Node-level system logs                                │
│  └── Component logs (kubelet, etcd, etc.)                  │
│                                                             │
│  METRICS                                                   │
│  ├── API request rates and errors                          │
│  ├── Resource usage (CPU, memory, network)                 │
│  ├── Authentication/authorization failures                 │
│  └── Custom security metrics                               │
│                                                             │
│  EVENTS                                                    │
│  ├── Kubernetes events (pod events, etc.)                  │
│  ├── Security-specific events                              │
│  ├── Policy violations                                     │
│  └── Runtime security alerts                               │
│                                                             │
│  TRACES                                                    │
│  ├── Request flow through services                         │
│  ├── API call chains                                       │
│  └── Distributed transaction tracking                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubernetes Audit Logging

### Audit Policy

```
┌─────────────────────────────────────────────────────────────┐
│              AUDIT LOG LEVELS                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  None       - Don't log                                    │
│  Metadata   - Log request metadata only                    │
│  Request    - Log metadata + request body                  │
│  RequestResponse - Log metadata + request + response       │
│                                                             │
│  AUDIT STAGES:                                             │
│  RequestReceived  - When request first arrives             │
│  ResponseStarted  - After response headers sent            │
│  ResponseComplete - After response body sent               │
│  Panic            - On panic                               │
│                                                             │
│  WHAT TO LOG:                                              │
│  • All authentication failures                             │
│  • Secrets access                                          │
│  • RBAC changes                                            │
│  • Pod creation/deletion                                   │
│  • Privileged operations                                   │
│  • Exec into containers                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Audit Policy Configuration

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Log authentication failures at metadata level
  - level: Metadata
    users: ["system:anonymous"]
    verbs: ["*"]

  # Log all secret access with request body
  - level: Request
    resources:
    - group: ""
      resources: ["secrets"]

  # Log exec into pods with request and response
  - level: RequestResponse
    resources:
    - group: ""
      resources: ["pods/exec", "pods/attach"]

  # Log RBAC changes
  - level: RequestResponse
    resources:
    - group: "rbac.authorization.k8s.io"
      resources: ["*"]

  # Log pod operations
  - level: Request
    resources:
    - group: ""
      resources: ["pods"]
    verbs: ["create", "delete", "patch", "update"]

  # Default: log metadata for everything else
  - level: Metadata
    omitStages:
    - "RequestReceived"
```

### Audit Log Output

```
┌─────────────────────────────────────────────────────────────┐
│              AUDIT LOG ENTRY                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  {                                                         │
│    "kind": "Event",                                        │
│    "apiVersion": "audit.k8s.io/v1",                       │
│    "level": "Request",                                     │
│    "auditID": "abc-123-def",                              │
│    "stage": "ResponseComplete",                            │
│    "requestURI": "/api/v1/namespaces/prod/secrets/db-cred",│
│    "verb": "get",                                          │
│    "user": {                                               │
│      "username": "alice@example.com",                      │
│      "groups": ["developers"]                              │
│    },                                                      │
│    "sourceIPs": ["10.0.0.5"],                             │
│    "objectRef": {                                          │
│      "resource": "secrets",                                │
│      "namespace": "prod",                                  │
│      "name": "db-credentials"                              │
│    },                                                      │
│    "responseStatus": { "code": 200 },                      │
│    "requestReceivedTimestamp": "2024-01-15T10:30:00Z",    │
│    "stageTimestamp": "2024-01-15T10:30:00Z"               │
│  }                                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Runtime Security Monitoring

### Falco

```
┌─────────────────────────────────────────────────────────────┐
│              FALCO RUNTIME SECURITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT IS FALCO?                                            │
│  • CNCF runtime security project                           │
│  • Monitors system calls in real-time                      │
│  • Detects anomalous behavior                              │
│  • Kubernetes-aware (pod context)                          │
│                                                             │
│  HOW IT WORKS:                                             │
│  Kernel → eBPF/kernel module → Falco → Rules → Alerts     │
│                                                             │
│  DETECTS:                                                  │
│  • Shell spawned in container                              │
│  • Sensitive file access (/etc/shadow)                     │
│  • Network connections from unexpected processes           │
│  • Privilege escalation attempts                           │
│  • Container escape techniques                             │
│  • Crypto mining behavior                                  │
│                                                             │
│  OUTPUT OPTIONS:                                           │
│  • Syslog, stdout                                          │
│  • HTTP webhook                                            │
│  • Slack, email alerts                                     │
│  • SIEM integration                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Falco Rules

```yaml
# Detect shell spawned in container
- rule: Terminal shell in container
  desc: A shell was spawned in a container
  condition: >
    spawned_process and
    container and
    shell_procs and
    proc.tty != 0
  output: >
    Shell spawned in container
    (user=%user.name container=%container.name
     shell=%proc.name pod=%k8s.pod.name)
  priority: WARNING

# Detect sensitive file access
- rule: Read sensitive file in container
  desc: Sensitive file read in container
  condition: >
    open_read and
    container and
    sensitive_files
  output: >
    Sensitive file read in container
    (file=%fd.name user=%user.name
     container=%container.name pod=%k8s.pod.name)
  priority: WARNING

# Detect privilege escalation
- rule: Privilege escalation via setuid
  desc: Process set user ID
  condition: >
    evt.type = setuid and
    container and
    evt.arg.uid = 0 and
    not proc.name in (setuid_whitelist)
  output: >
    Privilege escalation detected
    (user=%user.name command=%proc.cmdline
     container=%container.name)
  priority: CRITICAL
```

### Other Runtime Security Tools

```
┌─────────────────────────────────────────────────────────────┐
│              RUNTIME SECURITY TOOLS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TETRAGON (Cilium)                                         │
│  ├── eBPF-based security observability                     │
│  ├── Process execution, network, file access               │
│  ├── Enforcement capabilities                              │
│  └── Low overhead                                          │
│                                                             │
│  SYSDIG                                                    │
│  ├── Commercial runtime security                           │
│  ├── Built on Falco technology                            │
│  ├── Managed rules and compliance                          │
│  └── Enterprise features                                   │
│                                                             │
│  KUBEARMOR                                                 │
│  ├── LSM-based enforcement                                 │
│  ├── Process, file, network policies                       │
│  ├── Less established than Falco                           │
│  └── Focus on enforcement                                  │
│                                                             │
│  AQUA/PRISMA/STACKROX                                      │
│  ├── Commercial platforms                                  │
│  ├── Full-stack security                                   │
│  ├── Runtime + vulnerability management                    │
│  └── Compliance and reporting                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Events to Monitor

### High-Priority Events

```
┌─────────────────────────────────────────────────────────────┐
│              CRITICAL SECURITY EVENTS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHENTICATION                                            │
│  ├── Failed authentication attempts                        │
│  ├── Anonymous API access                                  │
│  ├── Use of highly privileged accounts                     │
│  └── Authentication from unexpected sources                │
│                                                             │
│  AUTHORIZATION                                             │
│  ├── RBAC permission denied events                         │
│  ├── Attempts to access secrets                            │
│  ├── Cluster-admin role usage                             │
│  └── Privilege escalation patterns                         │
│                                                             │
│  WORKLOAD                                                  │
│  ├── Privileged pod creation                               │
│  ├── Host namespace usage (hostPID, hostNetwork)           │
│  ├── Exec into containers                                  │
│  ├── Port forwarding                                       │
│  └── Pod creation with service account tokens              │
│                                                             │
│  RUNTIME                                                   │
│  ├── Shell processes in containers                         │
│  ├── Sensitive file access                                 │
│  ├── Outbound network connections                          │
│  ├── Package manager execution                             │
│  └── Crypto mining signatures                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Detection Queries

```
┌─────────────────────────────────────────────────────────────┐
│              EXAMPLE DETECTION QUERIES                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  UNAUTHORIZED SECRET ACCESS:                               │
│  Filter audit logs where:                                  │
│  • resource = secrets                                      │
│  • verb = get, list, watch                                │
│  • responseStatus.code = 200                              │
│  • user not in expected list                              │
│                                                             │
│  PRIVILEGED POD CREATION:                                  │
│  Filter audit logs where:                                  │
│  • resource = pods                                         │
│  • verb = create                                          │
│  • requestObject contains privileged: true                │
│                                                             │
│  EXEC INTO PRODUCTION:                                     │
│  Filter audit logs where:                                  │
│  • resource = pods/exec                                    │
│  • namespace in [production, prod]                        │
│  • Alert on any occurrence                                 │
│                                                             │
│  RBAC CHANGES:                                             │
│  Filter audit logs where:                                  │
│  • apiGroup = rbac.authorization.k8s.io                   │
│  • verb = create, update, patch, delete                   │
│  • Alert on changes to ClusterRoleBindings                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Logging Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES LOGGING STACK                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  COLLECTION                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Nodes                                              │   │
│  │  ├── Fluent Bit / Fluentd (DaemonSet)              │   │
│  │  ├── Collects container logs                        │   │
│  │  ├── Collects node logs                             │   │
│  │  └── Adds Kubernetes metadata                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                   │
│  AGGREGATION                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Central Logging                                    │   │
│  │  ├── Elasticsearch / Loki / Splunk                 │   │
│  │  ├── Long-term storage                              │   │
│  │  └── Indexed for search                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                   │
│  ANALYSIS                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Visualization/SIEM                                 │   │
│  │  ├── Kibana / Grafana                              │   │
│  │  ├── Security dashboards                            │   │
│  │  └── Alert rules                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Dashboards

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY DASHBOARD METRICS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHENTICATION PANEL                                      │
│  ├── Auth attempts over time                               │
│  ├── Failed auth by user/source IP                         │
│  ├── Anonymous access attempts                             │
│  └── Unusual authentication patterns                       │
│                                                             │
│  API ACTIVITY PANEL                                        │
│  ├── API requests by verb (create, delete, etc.)          │
│  ├── Requests to sensitive resources                       │
│  ├── Requests by user/service account                      │
│  └── Error rates and types                                 │
│                                                             │
│  WORKLOAD SECURITY PANEL                                   │
│  ├── Privileged pods running                               │
│  ├── Pods with host access                                 │
│  ├── Policy violations                                     │
│  └── Image vulnerability summary                           │
│                                                             │
│  RUNTIME ALERTS PANEL                                      │
│  ├── Falco alerts by severity                              │
│  ├── Shell spawns in containers                            │
│  ├── Sensitive file access                                 │
│  └── Network anomalies                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Kubernetes audit logs can be overwhelming**—a single busy cluster can generate gigabytes daily. Proper filtering and retention policies are essential.

- **Falco uses eBPF** to monitor system calls with minimal overhead. It can detect threats that network-based tools miss.

- **Most breaches are detected by external parties**, not internal monitoring. Good observability dramatically improves detection time.

- **Audit logs are essential for compliance** (PCI-DSS, SOC2, HIPAA) and incident investigation. Many organizations fail audits due to missing logs.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No audit logging | Can't investigate incidents | Enable audit policy |
| Logging everything | Noise, cost, storage | Tune audit policy |
| No log retention | Evidence lost | Define retention policy |
| Alerts without response | Alert fatigue | Create runbooks |
| Missing runtime monitoring | Late detection | Deploy Falco |

---

## Quiz

1. **What are the four audit log levels in Kubernetes?**
   <details>
   <summary>Answer</summary>
   None (don't log), Metadata (request metadata only), Request (metadata + request body), RequestResponse (metadata + request + response body). Higher levels provide more detail but use more storage.
   </details>

2. **What does Falco monitor and how?**
   <details>
   <summary>Answer</summary>
   Falco monitors system calls using eBPF or a kernel module. It applies rules to detect anomalous behavior like shell spawns in containers, sensitive file access, privilege escalation, and network anomalies. It provides Kubernetes context (pod name, namespace) with alerts.
   </details>

3. **Why should you log access to secrets?**
   <details>
   <summary>Answer</summary>
   Secrets contain sensitive data (passwords, API keys, certificates). Logging access helps detect unauthorized access attempts, enables incident investigation, supports compliance requirements, and provides accountability for who accessed what and when.
   </details>

4. **What's the difference between audit logs and runtime security monitoring?**
   <details>
   <summary>Answer</summary>
   Audit logs capture API server activity (who did what via the API). Runtime security monitoring (Falco) captures system-level activity inside containers (processes, file access, network). Both are needed for complete visibility.
   </details>

5. **What events should trigger immediate alerts?**
   <details>
   <summary>Answer</summary>
   Privileged pod creation, exec into production pods, cluster-admin role changes, anonymous API access, shell spawns in containers, sensitive file access, and authentication from unexpected sources. These indicate potential active attacks.
   </details>

---

## Hands-On Exercise: Audit Policy Design

**Scenario**: Design an audit policy for a production cluster. Determine what to log at each level:

**Requirements:**
- All secret access must be logged
- All RBAC changes must be logged with full detail
- Pod creation/deletion in production namespace needs logging
- Exec into any pod is high priority
- Normal read operations should have minimal logging

**Create the audit policy:**

<details>
<summary>Audit Policy</summary>

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # HIGH PRIORITY: Exec into pods - full detail
  - level: RequestResponse
    resources:
    - group: ""
      resources: ["pods/exec", "pods/attach", "pods/portforward"]

  # HIGH PRIORITY: All secret operations
  - level: Request
    resources:
    - group: ""
      resources: ["secrets"]

  # HIGH PRIORITY: RBAC changes - full detail
  - level: RequestResponse
    resources:
    - group: "rbac.authorization.k8s.io"
      resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
    verbs: ["create", "update", "patch", "delete"]

  # MEDIUM: Pod operations in production
  - level: Request
    resources:
    - group: ""
      resources: ["pods"]
    namespaces: ["production", "prod"]
    verbs: ["create", "update", "patch", "delete"]

  # MEDIUM: ServiceAccount operations
  - level: Request
    resources:
    - group: ""
      resources: ["serviceaccounts"]
    verbs: ["create", "update", "patch", "delete"]

  # LOW: Log metadata for remaining mutating operations
  - level: Metadata
    verbs: ["create", "update", "patch", "delete"]

  # MINIMAL: Skip logging for read-only operations on common resources
  - level: None
    resources:
    - group: ""
      resources: ["events", "endpoints"]

  - level: None
    users: ["system:kube-proxy"]

  - level: None
    userGroups: ["system:nodes"]
    verbs: ["get", "list", "watch"]

  # DEFAULT: Metadata for everything else
  - level: Metadata
    omitStages:
    - "RequestReceived"
```

**Key decisions:**
1. RequestResponse for exec/RBAC (need full detail for investigation)
2. Request for secrets (see what was requested)
3. Metadata for other mutations (who did what)
4. None for noisy read operations (reduce volume)
5. None for system components (reduce noise)

</details>

---

## Summary

Security observability enables threat detection and incident response:

| Component | Purpose | Tools |
|-----------|---------|-------|
| **Audit Logs** | API activity | Built-in Kubernetes |
| **Runtime Monitoring** | Container behavior | Falco, Tetragon |
| **Log Aggregation** | Centralized analysis | ELK, Loki, Splunk |
| **Alerting** | Rapid response | PagerDuty, Slack |

Key principles:
- Log security-relevant events at appropriate detail
- Monitor runtime behavior, not just API
- Alert on high-priority events
- Retain logs for investigation
- Build dashboards for visibility

---

## Next Module

[Module 5.3: Runtime Security](../module-5.3-runtime-security/) - Enforcing security policies at runtime.
