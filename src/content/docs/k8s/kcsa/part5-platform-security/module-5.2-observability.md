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

> **Stop and think**: If you log everything at the RequestResponse level, you capture maximum detail but generate enormous log volumes. What security events are worth the storage cost of full request+response logging, and which are safe to log at just Metadata level?

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

> **Pause and predict**: Falco detects a shell spawned inside a container and fires an alert. But the alert goes to a Slack channel that the on-call engineer checks every few hours. Is this monitoring effective? What determines whether detection leads to protection?

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

1. **During an incident investigation, you need to determine who accessed a specific secret in the production namespace last Tuesday. Your audit policy logs secrets at `Metadata` level. Can you answer the question? What if it were logged at `Request` level instead?**
   <details>
   <summary>Answer</summary>
   At Metadata level: yes, you can identify WHO accessed the secret (username, source IP, groups), WHEN (timestamp), and the outcome (response code). This is sufficient for the "who accessed it" question. At Request level: you additionally get the request body, which for `get` operations shows which specific secret was requested. For `create/update`, you'd see the new secret values — which is useful for investigation but means secret values appear in audit logs, creating a new exposure risk. The trade-off: Request level provides better investigation data but requires securing the audit log storage as carefully as you secure secrets themselves. For most organizations, Metadata level for `get` operations and Request level for `create/update/delete` operations is the right balance.
   </details>

2. **Falco detects a shell spawned in a production container and sends an alert. The on-call engineer sees it 2 hours later. By then, the attacker has exfiltrated data and cleaned up. What gap does this reveal, and how would you close it?**
   <details>
   <summary>Answer</summary>
   The gap is between detection time and response time (MTTD vs MTTR). Detection without timely response is ineffective. Closing the gap: (1) Route critical Falco alerts to PagerDuty or equivalent immediate-notification system, not just Slack; (2) Create automated response playbooks — for shell-in-container, automatically kill the pod or quarantine it by applying a deny-all NetworkPolicy; (3) Use Tetragon instead of (or alongside) Falco for enforcement — Tetragon can kill processes that match policy violations, not just alert; (4) Define severity-based SLAs: shell-in-production = 5-minute response, policy violation = 1-hour response; (5) Conduct tabletop exercises so the team practices responding to alerts quickly.
   </details>

3. **Your audit logs show 10,000 requests per minute. Storage costs are high and searching is slow. A colleague suggests setting everything to `None` except secrets and RBAC. What security events would you lose visibility into, and what's a better approach?**
   <details>
   <summary>Answer</summary>
   Setting most resources to None loses visibility into: pod creation (can't detect privileged pod launches), exec/attach operations (can't detect someone entering containers), ServiceAccount changes, namespace creation/deletion, and admission webhook modifications. All of these are critical attack indicators. Better approach: use tiered logging — `RequestResponse` for exec/attach and RBAC changes, `Request` for secrets and pod mutations, `Metadata` for most other mutations, and `None` only for genuinely noisy, low-value operations (endpoints updates, node heartbeats, kube-proxy reads). Also filter out system components (`system:kube-proxy`, `system:nodes` for read operations) to reduce volume while keeping security-relevant events.
   </details>

4. **An audit log entry shows a user accessed a secret, but the `sourceIPs` field shows an internal pod IP rather than a developer's workstation. What does this suggest about the access pattern, and should it trigger an alert?**
   <details>
   <summary>Answer</summary>
   A pod IP as the source means the API request came from inside the cluster — a pod is using its ServiceAccount token to access secrets via the Kubernetes API. This could be legitimate (an application reading its own configuration secrets) or malicious (a compromised pod's attacker using the stolen SA token to enumerate secrets). It should trigger an alert if: the pod's ServiceAccount shouldn't have secret access, the secret isn't in the pod's own namespace, the access pattern is unusual (listing all secrets vs. getting one specific secret), or the pod typically doesn't make API calls. Baseline normal API access patterns for each ServiceAccount so anomalies are detectable.
   </details>

5. **Your cluster has API audit logging enabled but no runtime security monitoring (no Falco/Tetragon). An attacker compromises an application, reads environment variables containing a database password, connects directly to the database, and exfiltrates data — all without making any Kubernetes API calls. Would your audit logs detect this attack?**
   <details>
   <summary>Answer</summary>
   No. Kubernetes audit logs only capture API server activity. This attack never touches the API — it operates entirely within the container (reading env vars) and at the network level (database connection). Audit logs would show the initial pod creation and any secret access, but not the in-container activity or network connections. This is precisely the gap that runtime security monitoring fills: Falco would detect unusual database connection patterns, unexpected outbound data transfers, and processes reading environment files. Network monitoring would detect the data exfiltration volume. This illustrates why audit logs and runtime monitoring are complementary, not substitutes — you need both for complete security observability.
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
