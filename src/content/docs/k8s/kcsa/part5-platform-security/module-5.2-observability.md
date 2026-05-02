---
revision_pending: false
title: "Module 5.2: Security Observability"
slug: k8s/kcsa/part5-platform-security/module-5.2-observability
sidebar:
  order: 3
---
# Module 5.2: Security Observability

> **Complexity**: `[MEDIUM]` - Core knowledge. **Time to Complete**: 25-30 minutes. **Prerequisites**: [Module 5.1: Image Security](../module-5.1-image-security/). This module assumes Kubernetes 1.35 or newer and uses `k` as the short command form after you define `alias k=kubectl` in your shell.

## Learning Outcomes

After completing this module, you will be able to:

1. **Evaluate** audit logging configurations for completeness of security-relevant event capture.
2. **Design** correlated observability signals across logs, metrics, events, and runtime alerts for Kubernetes threat detection.
3. **Diagnose** monitoring gaps that would leave compromised workloads, privileged API use, or data exfiltration undetected.
4. **Implement** an incident investigation workflow that connects audit logs, runtime alerts, and network telemetry.

## Why This Module Matters

In 2024, a regional payments company discovered that an attacker had used a compromised service account to list production Secrets, exec into a long-running container, and open a quiet outbound connection to a database replica. The cluster had prevention controls: images were scanned, Pod Security Admission was enabled, and developers did not have direct cluster-admin access. The incident still lasted long enough to become expensive because the team could not quickly answer a basic sequence of questions: who touched the Secret, which pod ran the shell, what namespace sent the unusual traffic, and whether the same identity had modified RBAC earlier in the week.

The financial impact came less from a single failed control than from slow reconstruction. Engineers pulled fragments from API server audit logs, node logs, application logs, cloud firewall exports, and a chat channel where runtime alerts had been posted without paging anyone. Each source told part of the truth, but no one had designed the signals as an investigation system. By the time the company understood the path from credential use to container activity to database access, the response had already expanded into customer notification, compliance review, and several weeks of platform hardening.

Security observability is the discipline of making that path visible before an incident. It does not replace prevention, admission control, least privilege, or image security; it tells you whether those controls are being bypassed, misused, or quietly failing. KCSA expects you to reason about Kubernetes audit logging, runtime detection, event streams, metrics, and alert routing as complementary layers. In this module, you will build a practical mental model for choosing what to log, how much detail to retain, and how to connect signals so a suspicious API request becomes an actionable investigation instead of a line buried in storage.

## Security Observability Pillars

Security teams often begin with "turn on logging" because logs feel concrete, but Kubernetes security visibility is broader than one stream of text. A useful observability plan treats logs, metrics, events, and traces as different camera angles on the same system. Audit logs show requests to the API server, runtime alerts show behavior inside containers and on nodes, metrics show rates and pressure over time, and events show control-plane decisions that affected workload state. None of these signals is complete alone, and that incompleteness is the reason correlation matters.

The most important design move is to tie each signal to a threat question. If the question is "Did anyone grant cluster-admin?", the API server audit log is the primary source because RBAC changes are Kubernetes API objects. If the question is "Did a shell run inside the compromised container?", a runtime detector such as Falco or Tetragon is the better source because the action may never touch the API server. If the question is "Did the pod move data to an unusual destination?", network telemetry and egress metrics become necessary. Good observability names those boundaries instead of pretending that one tool sees everything.

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

Logs are evidence-rich but expensive. They can preserve identities, object references, request paths, response codes, and sometimes request bodies, which makes them valuable during investigations and compliance reviews. The tradeoff is volume and sensitivity: detailed logs cost money to store, slow down search, and may contain information that deserves the same protection as the resources being logged. A mature platform team therefore avoids both extremes. It does not log nothing, and it does not blindly log every response body for every resource forever.

Metrics are weaker as forensic evidence but stronger as early-warning indicators. A spike in failed authentication, a sudden burst of `create` requests for pods, or an unusual rate of denied authorization decisions may not prove compromise, yet it can guide responders toward the right logs before retention windows close. Metrics also help distinguish a single strange event from a pattern. One denied request may be a typo; hundreds from a new source identity suggest probing, broken automation, or credential misuse.

Events sit between those worlds. Kubernetes Events explain scheduling failures, image pull errors, policy denials, and lifecycle changes, while security tools often emit their own event objects or webhook alerts. They are useful because they speak the platform's language, but they are usually short-lived and not designed as long-term records. If your incident process depends on events, you must forward them to durable storage. Otherwise the most useful context may disappear before anyone begins the investigation.

Traces are less central in KCSA security observability than audit logs or runtime alerts, but they become useful in service-heavy environments. A trace can show that an external request passed through an ingress, a checkout service, a payment adapter, and a database client before producing an error. When traces carry workload identity and namespace metadata, they can connect application behavior to infrastructure signals. That helps responders decide whether a suspicious Kubernetes event corresponds to real user traffic, background automation, or attacker-driven activity.

Pause and predict: if a cluster has perfect API server audit logging but no runtime or network visibility, which parts of a container compromise remain invisible? The answer should include anything that happens after the workload is already running: a shell reading environment variables, a package manager downloading tooling, a process scanning internal services, or a direct database connection that never calls the Kubernetes API.

## Kubernetes Audit Logging

Kubernetes audit logging records requests as they pass through the API server. That position is powerful because nearly every intentional change to cluster state flows through the API server: RBAC updates, Secret reads, pod creation, namespace deletion, admission decisions, and exec requests all have API shape. It is also limited because the audit log sees API activity, not arbitrary process behavior inside an already running container. Treat it as the control-plane ledger, not as a full host or application sensor.

An audit policy decides which requests are logged and at what level. The level is a precision dial. `Metadata` records who made the request, what resource was targeted, when it happened, where it came from, and whether it succeeded. `Request` adds the request body, which is useful for creates and patches because you can see what fields changed. `RequestResponse` adds the response body as well, which can be invaluable for some investigations but dangerous for sensitive resources because it may place returned data into the log store.

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

The policy below is intentionally security-biased. It logs anonymous access, Secret access, exec and attach activity, RBAC changes, and pod mutations with more detail than ordinary reads. That ordering matters because audit policy rules are evaluated in order. A broad `Metadata` rule placed too early can accidentally prevent later high-value rules from taking effect. When you evaluate an audit policy, read it like a firewall policy: from top to bottom, asking which rule catches a request first.

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

Stop and think: if you log every request at `RequestResponse`, you capture the most detail, but you also create a second high-value data store full of sensitive content. The better question is not "How do we maximize logs?" but "Which investigation questions require bodies, and which can be answered from metadata?" Secret reads often need careful treatment because response bodies can contain values, while RBAC changes and pod specs often justify richer detail because the changed fields explain the security impact.

An audit event becomes useful when responders know which fields to inspect first. The `user.username` and `user.groups` fields identify the authenticated principal, `sourceIPs` shows where the request appeared to originate, `objectRef` identifies the resource, and `responseStatus.code` tells whether the attempt succeeded. The `requestURI` is especially useful for subresources such as `pods/exec`, because the subresource often tells a more suspicious story than the parent object alone. A simple `get pod` request is ordinary; an exec into a production pod deserves attention.

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

The example above can answer several incident questions quickly. It says a human-looking user accessed a production Secret, the request succeeded, and the source appeared to be an internal address. It does not by itself prove malicious intent. A developer may have a legitimate break-glass role, an automation job may impersonate a user, or a proxy may hide the true client address. That is why audit analysis should be paired with RBAC context, identity provider logs, change tickets, runtime telemetry, and normal behavior baselines.

For command-line checks during a lab or incident drill, define `alias k=kubectl` and then use `k auth can-i get secrets --as system:serviceaccount:prod:checkout`. That command does not prove a Secret was accessed, but it helps evaluate whether the identity had the permission needed to perform the access shown in the audit log. In real investigations, permission checks are strongest when combined with the actual audit event, because RBAC may have changed after the suspicious request occurred.

War story: one platform team discovered that its audit policy logged RBAC changes at `Metadata` but not `Request`. During a compromise review, responders could see that a ClusterRoleBinding had been patched, but not which subject had been added because the request body was absent and the object had already been changed again. The team could eventually reconstruct the change from GitOps history, but the delay exposed a design flaw. For high-impact mutation resources, metadata alone may tell you that something happened without preserving enough detail to explain why it mattered.

## Runtime Security Monitoring

Runtime monitoring watches what workloads and nodes actually do after admission. This layer matters because many attacks begin with an ordinary-looking deployment and become visible only when a process behaves strangely. An attacker who compromises an application may spawn a shell, read sensitive files, run a package manager, scan the network, or open a reverse connection without creating any new Kubernetes object. API audit logs will not see those actions because they are operating-system and network behaviors, not API requests.

Falco is a common open source runtime security tool because it observes system calls and enriches alerts with Kubernetes context. The important idea is not that every cluster must use Falco specifically; the important idea is that a runtime detector can see a different class of behavior than the API server. It can notice that `/bin/sh` appeared in a container that normally runs a single web process, or that a process read a sensitive path, or that a network utility executed inside a workload that should not have it.

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

Runtime rules need tuning because normal behavior varies by workload. A shell inside a short-lived debug pod may be expected during a planned maintenance window, while the same shell inside a payment API container is highly suspicious. A package manager in a build job may be routine, while a package manager in a production runtime image suggests drift or attacker tooling. The goal is not zero alerts; the goal is alerts that carry enough workload context, severity, and routing information to create a fast and correct response.

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

Before running a rule set in production, ask what output you expect from a known-good workload. If your normal images start a shell during entrypoint setup, the shell rule may produce noise unless you add an exception. If a database container legitimately reads files that match a generic sensitive path list, the file rule may need workload-specific tuning. Good runtime monitoring is closer to smoke alarm placement than surveillance: too little coverage misses fires, but alarms that trigger every morning teach people to ignore them.

Falco is not the only runtime option, and the tool choice should follow the operational requirement. Tetragon, from the Cilium ecosystem, uses eBPF and can observe process execution, file access, and network behavior with Kubernetes identity attached. KubeArmor focuses on policy and enforcement through Linux security modules. Commercial platforms often combine runtime detection with vulnerability data, compliance reports, and managed rules. The right choice depends on whether you need open rules, enforcement hooks, managed operations, or integration with a broader security platform.

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

The practical distinction between detection and protection is response time. A runtime alert that lands in an unattended channel is useful later as evidence, but it may not prevent damage. A critical alert that pages on-call, opens an incident, attaches pod metadata, links to the audit query, and offers a quarantine runbook has a much better chance of changing the outcome. Some tools can enforce policies directly, such as killing a process or blocking behavior, but enforcement raises its own availability risk and must be tested carefully.

Pause and predict: Falco detects a shell spawned inside a production container and posts to a Slack channel that the on-call engineer checks every few hours. Is that monitoring effective? Detection becomes protection only when the signal reaches a responder quickly enough, contains the context needed to decide, and is paired with a practiced action such as isolating the workload, collecting evidence, or revoking a credential.

## Security Events to Monitor

Kubernetes security monitoring becomes manageable when events are grouped by attacker objective. Authentication events show attempts to enter the control plane. Authorization events show attempts to use or expand permissions. Workload events show attempts to create, change, or enter execution environments. Runtime events show what processes do after the workload exists. This grouping prevents dashboards from becoming random collections of charts and helps responders move from symptom to hypothesis.

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

Not every high-priority event deserves the same response. A single failed authentication from a developer laptop may be ordinary, while anonymous API access from an internet-facing address is a stronger signal. A pod using `hostNetwork` in a monitoring namespace may be expected, while the same field in a public application namespace could be a policy failure. A Secret read by an application service account may be normal during startup, while a list operation across many Secrets is a common reconnaissance pattern. Context turns raw events into security judgment.

Detection queries should be written as investigation starters, not as magic truth machines. The query for unauthorized Secret access begins with successful `get`, `list`, or `watch` requests on Secret resources, then subtracts expected users and service accounts. The query for privileged pod creation begins with pod creates or patches whose request body includes privileged fields, host namespace settings, or dangerous volume mounts. The query for production exec focuses on `pods/exec` subresources in production namespaces because interactive access changes the incident risk even when the identity is legitimate.

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

Correlation is where these queries become powerful. Imagine an audit alert for a service account listing Secrets, followed six minutes later by a runtime alert for a shell in the same pod, followed by unusual egress from that namespace. Each signal alone has an innocent explanation: a controller might list Secrets, an engineer might debug a pod, and traffic might increase during a release. Together, in a narrow time window, they form a credible intrusion chain that deserves urgent response.

The inverse is also true: correlation can reduce false positives. If a production exec occurs during an approved incident, from the expected engineer, after a change ticket, and without any runtime follow-on indicators, the alert may remain informational. That does not mean it should be ignored; it means the response can be evidence preservation and review rather than emergency containment. A strong monitoring program supports both escalation and de-escalation by providing enough surrounding facts.

War story: a team once alerted on every denied RBAC request and created so much noise that engineers stopped reading the channel. During a real incident, the attacker generated denied requests while probing permissions, but the signal blended into the background. The fix was not to delete the alert. The team changed it to detect unusual denied-request rates by identity, namespace, and source, then paired it with successful sensitive operations by the same principal. The result was fewer alerts with a clearer story.

### Worked Example: Following One Suspicious Identity

Suppose an alert says `system:serviceaccount:prod:reporting` successfully listed Secrets in the `prod` namespace. The first mistake is to ask whether service accounts should ever read Secrets in the abstract. Some applications legitimately read a small number of Secrets, and some controllers need broader access to reconcile resources. The better first question is whether this identity normally performs this verb against this resource in this namespace. Security observability is most useful when it compares a specific event to a specific expected behavior.

Begin with the audit log because the suspicious action is a Kubernetes API request. Confirm the verb, resource, namespace, response code, source IP, user agent, and timestamp. If the event is a `list` rather than a `get`, raise the priority because list operations often reveal more than one object and are common during reconnaissance. If the source IP belongs to a pod, pivot from the IP to the pod name, owner, node, and image digest using cluster metadata from the log pipeline. That pivot is much faster when collectors enrich records consistently.

Next, check RBAC around the time of the request. A current `k auth can-i` result is useful, but it only describes the permissions that exist now. If a role binding was created, patched, or deleted shortly before the Secret access, the current answer may hide the path that made the request possible. Audit events for `roles`, `rolebindings`, `clusterroles`, and `clusterrolebindings` should therefore be searched in the surrounding window. This is where richer audit detail for RBAC changes pays off, because the changed subject and role explain the privilege path.

After the control-plane review, move to runtime evidence for the pod that used the service account. Look for shell execution, package manager activity, suspicious file reads, unexpected child processes, and network tools launched near the Secret access time. The goal is to decide whether the Secret read was application behavior, controller behavior, or attacker behavior after compromise. A pod that listed Secrets and then spawned a shell is a much stronger incident signal than a pod that listed one known Secret during normal startup.

Network telemetry provides the next layer. A Secret access event can be a credential collection step, but the damage often appears when the credential is used against another service. Check egress from the namespace, connections from the pod to databases or cloud APIs, and traffic to destinations the workload does not usually contact. If your network logs include Kubernetes labels and service account identity, the investigation can follow the same principal across API activity, process behavior, and traffic. If they do not, responders must infer identity from IP addresses that may be reused.

Finally, decide whether to contain, observe, or close. Containment may include deleting the pod, scaling the workload to zero, applying a restrictive NetworkPolicy, rotating the accessed Secret, or revoking the service account token. Observation may be appropriate when the event matches a known rollout and no runtime or network indicators appear. Closure should still leave a record of why the event was considered benign, because future responders need to distinguish confirmed normal behavior from ignored noise. The decision is stronger when each layer has contributed evidence.

This worked example also shows why dashboards should support pivots rather than only totals. A chart that says "Secret reads increased" may be enough to start an investigation, but it does not identify the actor, workload, or next query. A useful dashboard lets the responder click from resource access to identity, from identity to RBAC changes, from workload to runtime alerts, and from namespace to egress. The interface does not need to be fancy; it needs to preserve the investigative chain under time pressure.

The same method applies to privileged pod creation. Start with the audit event for the pod mutation, inspect the request body for `securityContext`, host namespace settings, and volume mounts, then connect the new pod to its service account and image. Runtime monitoring can show whether that pod immediately ran tools or touched sensitive files. Network telemetry can show whether it contacted the metadata service, database endpoints, or unfamiliar external addresses. The observability design is successful when each pivot is expected and practiced rather than invented during the incident.

When you evaluate a cluster for KCSA-style questions, look for these pivots explicitly. Ask whether a sensitive API event can be tied to an identity, whether that identity can be tied to a workload, whether the workload can be tied to runtime behavior, and whether runtime behavior can be tied to network impact. If one link is missing, name the monitoring gap rather than hand-waving it away. A precise gap statement is more valuable than a vague claim that the cluster needs "better observability."

The final lesson is that observability design should be tested with drills. Create a harmless Secret access scenario, a planned production exec scenario, and a simulated runtime shell alert in a non-production environment. Then ask the on-call engineer to reconstruct the story from available signals. If they can answer who acted, what changed, what ran, what traffic followed, and what action was expected, the design is working. If they cannot, the drill has found a fixable gap before a real attacker depends on it.

## Logging Architecture

A Kubernetes logging architecture has three jobs: collect data near the source, enrich it with Kubernetes context, and store it where responders can search it quickly. Container logs usually live on nodes before an agent forwards them. API audit logs may be written by the API server to files, webhooks, or managed provider integrations. Runtime tools may send alerts to stdout, syslog, webhooks, or security platforms. If these paths are designed independently, responders spend incidents stitching together timestamps and names by hand.

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

Collection agents should add metadata that lets a person pivot between signals. Namespace, pod name, container name, node name, workload owner, service account, cluster name, and image digest are all useful. Without those fields, responders end up searching by raw message text, which is fragile and slow. With those fields, a runtime alert can point to the pod, the pod can point to its service account, and the service account can point to relevant audit events.

Retention is a security decision, not only a storage decision. Short retention may satisfy day-to-day debugging while failing incident response, because many compromises are discovered after the first suspicious action. Long retention improves investigation but increases cost and expands the amount of sensitive data that must be protected. A practical strategy is tiered retention: keep high-value security logs searchable for the response window, archive older records in cheaper storage, and apply stronger access controls to audit streams that may reveal Secrets or privileged activity.

Dashboards are useful when they show decisions, not decoration. A security dashboard should help answer whether the cluster is under attack, whether a control is drifting, and where responders should look next. Panels that show authentication failures, sensitive resource access, privileged pods, policy violations, and runtime alerts are valuable because each one connects to a response path. Panels that simply count all log lines rarely help under pressure.

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

Alert routing should reflect severity and ownership. A failed image pull belongs to the application team unless it suggests supply-chain tampering. A shell in a production container may belong to both the service owner and security on-call. A ClusterRoleBinding change may belong to platform engineering and identity governance. Routing every signal to one central channel creates fatigue, while routing signals only to service teams can hide cross-namespace attack patterns. The design should preserve both local ownership and central visibility.

There is also a trust boundary around the logging system itself. Attackers who gain cluster permissions may try to delete pods, rotate logs, disable agents, or flood storage with noise. For sensitive environments, send audit data off-cluster or to a hardened control-plane integration, restrict who can change collector configurations, and alert when logging agents stop reporting. Observability is part of the security system; if it can be silently disabled by the same identities it monitors, it is weaker than it looks.

## Patterns & Anti-Patterns

### Pattern: Tiered Audit Detail

Use tiered audit detail when different resources have different investigation value and sensitivity. RBAC mutations, exec subresources, admission webhook changes, and privileged pod specifications usually deserve richer logging because the changed fields explain risk. Routine reads of low-sensitivity resources usually do not need request bodies. This pattern works because it accepts that logs are both evidence and liability, then deliberately spends detail where it will matter during an incident.

The scaling consideration is policy maintenance. As teams add controllers, custom resources, and platform extensions, the audit policy should be reviewed so important mutation paths do not fall into a low-detail default. Custom resources that grant infrastructure access, manage credentials, or change admission behavior may be just as security-relevant as built-in Kubernetes resources. A stale policy can look complete while missing the objects your platform actually depends on.

### Pattern: Correlated Alert Runbooks

Use correlated runbooks when a single alert does not provide enough confidence to act alone. A runbook for Secret access can instruct responders to check identity, source IP, namespace, service account permissions, related RBAC changes, runtime alerts from the same pod, and egress from the namespace. This turns monitoring into a repeatable investigation workflow instead of a pile of dashboards. It also helps newer on-call engineers make consistent decisions under stress.

The scaling consideration is automation. At small scale, a person can run several saved queries manually. At larger scale, alerts should attach the most useful context automatically: the last sensitive API events for that identity, current pod owner, image digest, node, and recent runtime alerts. Automation should gather evidence before taking destructive actions, unless the organization has explicitly accepted enforcement risk for a high-confidence signal.

### Pattern: Durable Off-Cluster Evidence

Use durable off-cluster evidence for audit logs, critical runtime alerts, and collector health signals. Local node storage is useful for troubleshooting but weak as the only forensic source because nodes can be replaced, compromised, or cleaned. Off-cluster storage makes it harder for a cluster-local attacker to erase the record. It also allows incident responders to keep investigating if containment requires draining nodes or deleting suspicious workloads.

The scaling consideration is access control. Central log stores often become powerful because they contain records from many clusters and namespaces. Give responders enough access to investigate quickly, but avoid turning the log system into an unrestricted data lake of Secrets, tokens, request bodies, and customer identifiers. Sensitive audit streams should have role-based access, retention rules, and monitoring of their own administrative changes.

### Anti-Pattern: Logging Everything Without Ownership

Teams fall into this anti-pattern because it feels safer to collect more data than to make hard choices. The result is usually high cost, slow search, and a backlog of alerts no one owns. In severe cases, the log system becomes a second breach surface because request and response bodies contain sensitive material. The better alternative is to define investigation questions, map them to required fields, and assign owners for each alert class before increasing volume.

### Anti-Pattern: Treating Audit Logs as Runtime Security

Teams fall into this anti-pattern when they correctly enable API audit logging and then assume the cluster is observable. Audit logs are excellent for control-plane activity, but they do not see every process, file read, or network connection inside a running container. The better alternative is layered coverage: API audit logs for Kubernetes actions, runtime monitoring for process behavior, network telemetry for egress and lateral movement, and application logs for domain-specific actions.

### Anti-Pattern: Alerts Without Response Paths

Teams fall into this anti-pattern when tool installation is treated as the finish line. A detector sends alerts, dashboards fill with signals, and no one has decided which alerts page, who owns them, or what action is expected. The better alternative is to write runbooks while designing detections. Every critical alert should identify the likely threat, the first evidence to collect, the containment options, the escalation target, and the conditions for closing the incident.

## Decision Framework

Start with the investigation question, then choose the signal. If the question asks who changed a Kubernetes object, begin with audit logs. If it asks what a process did inside a container, begin with runtime telemetry. If it asks whether traffic left the namespace or cluster, begin with network observability. If it asks whether a user-facing transaction moved through a suspicious path, begin with traces and application logs. This ordering keeps you from forcing every problem into the tool you happen to have installed.

Next, decide the detail level. For high-impact mutations, choose request detail when the changed fields are required to understand risk. For sensitive reads, prefer metadata unless you have a strong reason to capture bodies and can protect the resulting logs. For noisy system components, suppress or downsample only after confirming the events are not needed to detect privilege escalation, workload changes, or credential use. The decision should be documented because future responders need to know why a signal exists or why it is absent.

Then decide the response path. Informational signals can live in dashboards and daily review. Suspicious signals should create tickets or low-priority notifications with enough context to triage. Critical signals should page, open an incident, and attach evidence automatically. Enforcement signals, such as killing a process or quarantining a pod, should be reserved for high-confidence conditions and tested with service owners because a false positive can become an outage.

Finally, review the design against failure modes. What if the logging agent stops on one node? What if the audit backend is unavailable? What if an attacker changes RBAC and then generates noise? What if the alert contains sensitive fields that are forwarded to a broad chat channel? A good observability design includes health checks for the monitoring system, protects the evidence store, and avoids leaking sensitive investigation data into low-trust destinations.

## Did You Know?

- **Kubernetes audit policy reached the stable `audit.k8s.io/v1` API long before Kubernetes 1.35**, which means modern clusters can rely on a stable policy format instead of experimental audit configuration.
- **Falco joined the CNCF in 2018 and graduated in 2024**, reflecting years of operational use for runtime threat detection across container and Kubernetes environments.
- **A single busy cluster can generate many gigabytes of audit data per day**, so retention, filtering, and field selection are financial controls as well as security controls.
- **Kubernetes Events are not a durable forensic record by default**, so teams that rely on them for security investigations need forwarding and retention outside the short-lived event stream.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| No audit logging | Teams assume managed control planes or application logs will provide enough evidence after an incident. | Enable an explicit audit policy or provider audit integration and confirm that sensitive resources, RBAC, pod mutations, and exec subresources are captured. |
| Logging everything at maximum detail | Engineers fear missing evidence and choose `RequestResponse` broadly without considering cost or sensitivity. | Use tiered audit levels, reserve bodies for high-value mutations, and protect audit storage as a sensitive system. |
| Missing runtime monitoring | The team treats API audit logs as complete security visibility and forgets in-container behavior. | Add runtime detection such as Falco, Tetragon, KubeArmor, or a managed platform for process, file, and network behavior. |
| Alerts without response ownership | Tool installation finishes before on-call routing, severity rules, and runbooks are defined. | Assign alert owners, route critical signals to paging, and attach investigation steps to each high-priority detection. |
| Short retention for security logs | Storage budgets are set for debugging convenience rather than incident timelines. | Define retention by investigation requirements, keep recent records searchable, and archive older security evidence safely. |
| Unprotected log stores | Audit logs are treated as harmless metadata even when they contain request bodies or sensitive object references. | Restrict access, monitor log-store administration, and avoid sending sensitive fields to broad chat channels. |
| No monitoring health checks | Collectors and alert pipelines are assumed to work until an incident proves otherwise. | Alert when agents stop reporting, audit backends fail, or expected cluster metadata disappears from incoming records. |

## Quiz

<details><summary>Your team must investigate who accessed a production Secret, but the audit policy logs Secret reads only at `Metadata`. Can you answer the core question, and what risk would `RequestResponse` add?</summary>
Yes, metadata usually answers the core access question because it includes the authenticated user, groups, source IPs, target resource, namespace, verb, timestamp, and response status. It will not include the returned Secret data, which is usually a benefit because the log store should not become another place where secret values live. `RequestResponse` may add forensic detail for some resources, but for Secret reads it can expose sensitive response bodies and increase blast radius. A better design is to capture enough metadata for accountability while using richer levels for mutations where the request body explains what changed.
</details>

<details><summary>Falco reports a shell in a production container, but the alert went only to a low-traffic chat channel and was seen hours later. What gap does this reveal, and how should the observability design change?</summary>
The gap is not detection capability; the detector saw the suspicious behavior. The failure is response design, because a critical signal did not reach the right person quickly enough and was not connected to a containment runbook. The design should route high-severity runtime alerts to paging or incident automation, include pod and namespace context, and link to audit and network queries for the same workload. If the organization accepts the risk, a high-confidence rule can also trigger quarantine or process termination after testing.
</details>

<details><summary>A colleague wants to reduce audit volume by setting everything to `None` except Secrets and RBAC. Which monitoring gaps would that create?</summary>
That policy would lose visibility into pod creation, pod updates, exec and attach subresources, ServiceAccount changes, admission-related objects, namespace changes, and other mutation paths attackers use to gain execution or persistence. Secrets and RBAC are important, but they are not the whole attack path. A better approach is tiered logging: high detail for sensitive mutations, metadata for most other mutations, and suppression only for well-understood low-value noise. The goal is to reduce volume without deleting the trail that explains how an attacker moved from identity to workload execution.
</details>

<details><summary>An audit entry shows Secret access from an internal pod IP rather than a developer workstation. How do you diagnose whether this is normal or suspicious?</summary>
Start by identifying the service account, namespace, pod owner, and exact Secret object from the audit event. Then compare the access to expected application behavior: whether that service account should read that Secret, whether it normally calls the API server, and whether the request was a single `get` or broad `list` operation. Correlate the timestamp with runtime alerts and network telemetry from the same pod because a compromised workload may use its token after initial exploitation. The event is not automatically malicious, but it deserves investigation if the identity, namespace, verb, or volume of access is unusual.
</details>

<details><summary>An attacker compromises an application, reads environment variables, connects directly to a database, and exfiltrates data without calling the Kubernetes API. Would API audit logs detect the attack?</summary>
No, API audit logs would not detect the in-container environment read or the direct database connection because those actions do not pass through the Kubernetes API server. The audit log may show the original pod creation or earlier Secret mounting, but it will not show process behavior after the workload is running. Runtime monitoring can detect unusual process activity, and network telemetry can detect unexpected egress or data movement. This scenario is the reason security observability must combine audit logs with runtime and network signals.
</details>

<details><summary>A dashboard shows a spike in denied RBAC requests from one service account, followed by a successful ClusterRoleBinding update by a different user. What should responders check next?</summary>
Responders should treat the sequence as a possible privilege escalation path rather than two unrelated events. They should inspect the denied requests to learn what permissions were being probed, review the successful ClusterRoleBinding change to identify the added subjects and roles, and check whether the same source IP, namespace, or automation account appears in both timelines. They should also look for subsequent sensitive operations, such as Secret listing, pod creation, or exec. The reasoning matters because attackers often probe first, then use a stronger identity or misconfiguration to complete the action.
</details>

<details><summary>You are implementing a new incident workflow for observability signals. Which evidence should be collected first when a production exec alert fires?</summary>
Collect volatile context first: the audit event for the `pods/exec` request, the identity and source IP, the pod owner, service account, node, image digest, and runtime alerts around the same timestamp. Then preserve container logs and relevant network telemetry before deleting or restarting anything, unless containment urgency overrides evidence collection. Check whether RBAC or Secret access changed shortly before the exec event because interactive access is often one step in a larger chain. The workflow should make these pivots repeatable so responders do not improvise under pressure.
</details>

## Hands-On Exercise: Audit Policy Design

In this exercise, you will design a production audit policy and an investigation checklist for a cluster that uses Kubernetes 1.35 or newer. The scenario is intentionally realistic: the platform team wants strong evidence for sensitive operations without drowning the logging backend in low-value traffic. You will use `k` in the checks after setting `alias k=kubectl`, but the main artifact is the policy reasoning rather than a live cluster change.

**Scenario**: Design an audit policy for a production cluster. Determine what to log at each level:

**Requirements:**
- All secret access must be logged
- All RBAC changes must be logged with full detail
- Pod creation/deletion in production namespace needs logging
- Exec into any pod is high priority
- Normal read operations should have minimal logging

Work through the tasks in order. Each task adds one layer: identify the protected resources, choose the audit level, explain the tradeoff, connect the signal to a response, and validate that the resulting policy supports the learning outcomes from this module. If you have a test cluster, you can adapt the policy into your API server configuration; if you do not, the exercise still works as a design review.

- [ ] Identify the API resources and subresources that must be high priority: Secrets, RBAC resources, `pods/exec`, `pods/attach`, `pods/portforward`, ServiceAccounts, and production pod mutations.
- [ ] Choose an audit level for each high-priority category and write one sentence explaining why metadata alone is or is not enough for investigation.
- [ ] Add noise-control rules for low-value reads and system components without suppressing security-relevant mutations.
- [ ] Define the first three responder actions for a successful Secret read by an unexpected service account.
- [ ] Define the first three responder actions for a runtime shell alert that occurs within minutes of an audit event for production exec.
- [ ] Validate the design by checking whether each learning outcome is exercised by the policy, the response steps, or both.

<details>
<summary>Solution and reasoning</summary>

The high-priority resources are the ones that either expose credentials, change authorization, create execution, or provide interactive access. `RequestResponse` is appropriate for exec and RBAC changes when the organization accepts the storage and sensitivity tradeoff, because responders need full detail about what changed or which subresource was used. `Request` is a reasonable default for Secret operations in this teaching policy, but real organizations should be careful with returned data and may prefer metadata for reads while keeping request bodies for creates and updates. Noise-control rules should come after high-priority rules so they do not swallow sensitive events.

The responder actions should pivot across layers. For an unexpected service account reading a Secret, check the audit event, current RBAC, pod owner, namespace, and recent runtime or network alerts from that workload. For a shell alert near an exec event, preserve evidence, identify the user and source, check whether the exec was approved, and decide whether to isolate the pod or revoke credentials. The design is complete only if the evidence can answer who acted, what object was touched, what ran afterward, and how responders should act.

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

</details>

Success criteria:

- [ ] Your policy logs exec, attach, and port-forward subresources before any broad default rule.
- [ ] Your policy logs RBAC mutations with enough detail to reconstruct the changed role or binding.
- [ ] Your policy records Secret access while explicitly acknowledging the sensitivity of audit log storage.
- [ ] Your noise-control rules do not suppress pod mutations, ServiceAccount mutations, or privileged workload changes.
- [ ] Your incident workflow correlates audit logs, runtime alerts, and network telemetry instead of relying on one signal.

## Next Module

[Module 5.3: Runtime Security](../module-5.3-runtime-security/) - Enforcing security policies at runtime after detection shows what workloads are doing.

## Sources

- [Kubernetes: Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [Kubernetes: Audit configuration API](https://kubernetes.io/docs/reference/config-api/apiserver-audit.v1/)
- [Kubernetes: Logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes: RBAC authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes: Service accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [Kubernetes: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes: kubectl auth can-i](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_auth/kubectl_auth_can-i/)
- [Falco documentation](https://falco.org/docs/)
- [Falco rules documentation](https://falco.org/docs/concepts/rules/)
- [Tetragon overview](https://tetragon.io/docs/overview/)
- [Tetragon tracing policy concepts](https://tetragon.io/docs/concepts/tracing-policy/)

Security observability enables threat detection and incident response:

| Component | Purpose | Tools |
|-----------|---------|-------|
| **Audit Logs** | API activity | Built-in Kubernetes |
| **Runtime Monitoring** | Container behavior | Falco, Tetragon |
| **Log Aggregation** | Centralized analysis | ELK, Loki, Splunk |
| **Alerting** | Rapid response | PagerDuty, Slack |
