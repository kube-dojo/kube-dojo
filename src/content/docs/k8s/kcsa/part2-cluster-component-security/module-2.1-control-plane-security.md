---
revision_pending: false
title: "Module 2.1: Control Plane Security"
slug: k8s/kcsa/part2-cluster-component-security/module-2.1-control-plane-security
sidebar:
  order: 2
---

# Module 2.1: Control Plane Security

- **Complexity**: `[MEDIUM]` - Core knowledge
- **Time to Complete**: 30-35 minutes
- **Prerequisites**: [Module 1.3: Security Principles](/k8s/kcsa/part1-cloud-native-security/module-1.3-security-principles/)

## Learning Outcomes

After completing this module, you will be able to apply these skills during control plane reviews, incident response, and KCSA-style troubleshooting scenarios:

1. **Evaluate** API server authentication, authorization, admission, and audit controls for a Kubernetes 1.35 control plane
2. **Diagnose** etcd exposure, transport encryption, secrets encryption, and backup risks before they become cluster compromise paths
3. **Compare** scheduler and controller manager privileges, bind addresses, service account credentials, and network isolation choices
4. **Implement** a control plane assessment that maps insecure flags to hardened settings and prioritized remediation tasks

## Why This Module Matters

In early 2018, researchers reported that attackers had found an exposed Kubernetes administrative console used by Tesla and turned the environment into a crypto-mining platform. The public reporting focused on mining because it was visible, but the more serious lesson was about control plane reachability: once an attacker can speak to the machinery that creates, schedules, and stores cluster state, the cluster stops being a boundary and becomes a launch point. The direct invoice from that specific mining incident was not the only risk; exposed cloud credentials, workload metadata, and stored application data can produce investigation costs, regulatory exposure, and business disruption long after the malicious pods are removed.

That story matters because control plane security is not a decorative hardening checklist. The API server decides whether a request is real, whether the caller is allowed to act, whether the object is acceptable, and whether the event is recorded for later investigation. etcd stores the truth that the API server protects, including Secret objects and RBAC policy. The scheduler and controller manager continuously turn desired state into running workloads, so their credentials and network placement shape how far an attacker can move after one component fails.

For the KCSA exam, control plane security sits inside a large cluster component security domain, but the operational value is broader than the exam outline. A production team that can evaluate API server flags, diagnose etcd exposure, compare controller privileges, and implement a repeatable assessment can reduce cluster-wide compromise paths before an incident. This module uses Kubernetes 1.35+ terminology and examples, and the lab uses the common shell alias `alias k=kubectl`; after that introduction, commands and prompts refer to the Kubernetes CLI as `k`.

## Control Plane Architecture

The control plane is the part of Kubernetes that decides what the cluster should be and records what the cluster is. Worker nodes run containers, but they do not independently invent cluster policy, assign pods, approve admission decisions, or store the durable state database. That distinction is why a single compromised workload might be a namespace problem, while a compromised API server or etcd member can become a cluster problem within minutes.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CONTROL PLANE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API SERVER                        │   │
│  │  • Front door to the cluster                        │   │
│  │  • All requests go through here                     │   │
│  │  • Authentication, Authorization, Admission         │   │
│  └─────────────────────────────────────────────────────┘   │
│           │              │                │                 │
│           ▼              ▼                ▼                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │    ETCD     │ │  SCHEDULER  │ │ CONTROLLER MANAGER  │   │
│  │             │ │             │ │                     │   │
│  │ • Database  │ │ • Pod       │ │ • Reconciliation    │   │
│  │ • Secrets   │ │   placement │ │ • Built-in          │   │
│  │ • State     │ │             │ │   controllers       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│                                                             │
│  Each component has specific security requirements         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Read the diagram from the top, not from left to right. The API server is the front door, and every normal cluster action should enter through that door before it reaches etcd. The scheduler and controller manager do not bypass the API server to manipulate raw state; they watch objects, make decisions, and write updates back through authenticated API calls. This creates a deliberate choke point where identity, authorization, admission policy, and audit logging can be applied consistently.

The security tradeoff is that a choke point is also a prize. If the API server accepts anonymous requests, uses `AlwaysAllow`, skips important admission controls, or cannot prove the identity of etcd, the rest of the cluster inherits that weakness. If etcd is reachable from pods, a compromised workload may avoid every API server guardrail and read or alter state directly. If scheduler and controller manager endpoints listen broadly, a diagnostic interface that was convenient during setup can become an unnecessary attack surface.

A useful mental model is an airport. Passengers, crew, luggage, and maintenance teams all move through controlled paths, and the airport does not rely on one guard standing at one door. It checks identity, checks permission to enter a zone, screens items, logs exceptional events, and locks the rooms that contain route plans and keys. Kubernetes control plane security uses the same layered idea: no single flag makes the cluster safe, but each component can be configured so one missed control does not automatically collapse the rest.

## API Server Security

The API server is the most critical component because it is the only component that communicates with etcd in a healthy Kubernetes design and because it is the gateway for all cluster operations. In Kubernetes 1.35+, the expected request path is still the same layered decision model: authenticate the caller, authorize the requested verb and resource, run admission controls, persist accepted state, and write audit records when configured. If any step is removed or weakened, the remaining steps must carry more risk than they were designed to carry.

### Authentication

Authentication answers the first question in the request path: who is making this request? Kubernetes supports several authenticators because clusters serve different actors. Kubelets and control plane components often use X.509 client certificates, pods use service account tokens, human users commonly arrive through OIDC, and custom integrations may use webhook token authentication. The security goal is not to prefer one method everywhere, but to make sure each identity source is explicit, revocable, and scoped to a use case.

```text
┌─────────────────────────────────────────────────────────────┐
│              API SERVER AUTHENTICATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHENTICATION METHODS                                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  X.509 CLIENT CERTIFICATES                          │   │
│  │  • Used by: kubelet, controller-manager, scheduler  │   │
│  │  • CN = username, O = groups                        │   │
│  │  • Managed by cluster PKI                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SERVICE ACCOUNT TOKENS                             │   │
│  │  • Used by: Pods                                    │   │
│  │  • JWT tokens, auto-mounted                         │   │
│  │  • Bound to specific audience and expiration        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  OIDC (OpenID Connect)                              │   │
│  │  • Used by: Human users                             │   │
│  │  • Integrates with identity providers               │   │
│  │  • Supports MFA through provider                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  WEBHOOK TOKEN AUTHENTICATION                       │   │
│  │  • Used by: Custom integrations                     │   │
│  │  • External service validates tokens                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The first insecure setting to look for is `--anonymous-auth=true`. Anonymous authentication does not mean the API server skips all checks; it means unauthenticated requests can be assigned the anonymous user and groups, then passed to authorization. That sounds safer than it is because many clusters accumulate discovery permissions, health probes, legacy bindings, or custom roles that reveal more than intended. In production, disable anonymous authentication unless a documented compatibility requirement exists and the resulting permissions are tightly reviewed.

Pause and predict: what do you think happens if a request reaches admission before the API server has established a user and group? The admission controller would have less trustworthy context for policy decisions, and audit records would be less useful during investigation. Kubernetes keeps authentication before authorization and admission because every later decision depends on the identity established at the front of the request path. When you evaluate API server authentication, you are really evaluating the quality of evidence used by every later control.

### Authorization

Authorization answers the next question: is this identity allowed to perform this verb on this resource in this scope? The common secure production baseline is `--authorization-mode=Node,RBAC`, where the Node authorizer limits kubelet requests and RBAC expresses human, workload, and automation privileges. This does not make permissions automatically correct. It gives the cluster a policy engine that can represent least privilege and can be inspected with commands such as `k auth can-i`.

```text
┌─────────────────────────────────────────────────────────────┐
│              API SERVER AUTHORIZATION                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHORIZATION MODES (in order of evaluation)              │
│                                                             │
│  NODE                                                       │
│  • Authorizes kubelet requests                             │
│  • Limited to resources for pods on that node              │
│                                                             │
│  RBAC (Most common)                                        │
│  • Role-based access control                               │
│  • Roles, ClusterRoles, Bindings                           │
│  • Fine-grained permissions                                │
│                                                             │
│  ABAC (Legacy)                                             │
│  • Attribute-based access control                          │
│  • File-based policies                                     │
│  • Requires API server restart to change                   │
│                                                             │
│  WEBHOOK                                                    │
│  • External authorization service                          │
│  • Custom policy engines (OPA/Gatekeeper)                  │
│                                                             │
│  Typical configuration: --authorization-mode=Node,RBAC     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The dangerous authorization setting is `AlwaysAllow`. It can appear in old labs, hurried bootstrap scripts, or emergency recovery notes that were never removed. With `AlwaysAllow`, authentication becomes the only barrier, so any valid credential can create privileged pods, read Secrets, patch RBAC, or alter admission webhooks. A stolen low-privilege service account token becomes far more valuable because the authorization layer no longer asks whether that service account should be allowed to act.

RBAC is also not a magic shield when bindings are too broad. Binding a workload to `cluster-admin` because one controller needed one verb is like giving a building master key to a vendor because one closet was locked. The better operational move is to start from the observed API calls, create a narrow Role or ClusterRole, bind it to the exact service account, and review the binding when the controller changes. Before running a sensitive workload, ask yourself which `k auth can-i` checks would prove that the service account can do its job without owning the cluster.

### Admission Control

Admission control answers a more subtle question: should this otherwise valid and authorized request be accepted in its final form? Mutating admission can add defaults, sidecars, labels, or other changes before persistence. Validating admission can reject objects that violate security policy, naming rules, resource limits, or organizational requirements. That split matters because authorization decides whether the caller may ask for an action, while admission decides whether the resulting object is acceptable for the cluster.

```text
┌─────────────────────────────────────────────────────────────┐
│              ADMISSION CONTROL FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Request → Authentication → Authorization → Admission      │
│                                                             │
│  ADMISSION CONTROLLERS                                      │
│                                                             │
│  MUTATING (modify requests)                                │
│  ├── DefaultStorageClass: Adds default storage class       │
│  ├── ServiceAccount: Adds default service account          │
│  └── Custom webhooks: Add sidecars, labels                 │
│                                                             │
│  VALIDATING (accept/reject requests)                       │
│  ├── PodSecurity: Enforces Pod Security Standards          │
│  ├── ValidatingAdmissionPolicy: CEL-based validation       │
│  └── Custom webhooks: Policy enforcement                   │
│                                                             │
│  SECURITY-CRITICAL ADMISSION CONTROLLERS                   │
│  ├── PodSecurity (PSA)                                     │
│  ├── NodeRestriction                                       │
│  ├── ValidatingAdmissionWebhook                            │
│  └── MutatingAdmissionWebhook                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

For KCSA-level control plane security, two admission themes deserve special attention. PodSecurity helps enforce Pod Security Standards so teams cannot casually create privileged, host-mounted, or otherwise risky pods in namespaces where those profiles are not allowed. NodeRestriction works with the Node authorizer to limit what kubelets can modify, which helps keep a compromised node credential from changing objects outside its legitimate node identity. These controls reduce blast radius, but they must be enabled and paired with RBAC that does not hand attackers a separate path around them.

Admission webhooks add flexibility, and that flexibility creates an availability tradeoff. A validating webhook that times out on every pod creation can stop deployments across the cluster, while a mutating webhook that changes security context incorrectly can introduce risk at scale. The control plane security question is not simply whether webhooks exist. You evaluate whether they are reachable, whether their failure policy matches the risk, whether they are protected by TLS, and whether audit logs make their decisions visible enough to troubleshoot.

### API Server Security Flags

The following table is one of the fastest ways to turn an API server manifest into an assessment. Do not read it as a memorization aid only. Each flag maps to a control plane security behavior that changes what an attacker can do after they obtain network access, a token, or a misconfigured workload. When a verifier, auditor, or teammate asks whether the API server is hardened, these settings give you concrete evidence.

| Flag | Purpose | Secure Setting | CIS Benchmark |
|------|---------|----------------|---------------|
| `--anonymous-auth` | Allow unauthenticated requests | `false` for production | CIS 1.2.1 |
| `--authorization-mode` | How to authorize requests | `Node,RBAC` | CIS 1.2.7, 1.2.8 |
| `--enable-admission-plugins` | Which admission controllers | Include `PodSecurity,NodeRestriction` | CIS 1.2.15, 1.2.16 |
| `--audit-log-path` | Where to write audit logs | Set to valid path | CIS 1.2.19 |
| `--tls-cert-file` | API server TLS certificate | Must be configured | CIS 1.2.26 |
| `--etcd-cafile` | CA to verify etcd | Must be configured | CIS 1.2.28 |

Audit logging is often treated as a detective control, but it also changes behavior before an incident. Teams that know high-risk actions are recorded tend to create cleaner break-glass procedures and fewer informal admin shortcuts. A useful audit policy records authentication failures, RBAC changes, Secret access, admission webhook changes, and privileged workload creation without drowning operators in every low-value watch event. The API server cannot help you investigate what it was never configured to record.

## etcd Security

etcd is the cluster memory. Kubernetes stores objects there after they pass the API server path, which means etcd contains Deployments, Pods, ConfigMaps, RBAC bindings, leases, node status, and Secret resources. Secret values are not protected merely because they are base64 encoded in the Kubernetes API. Base64 is an encoding for transport and display, not encryption, so etcd exposure can turn a single network mistake into credential disclosure.

```text
┌─────────────────────────────────────────────────────────────┐
│              ETCD SECURITY                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ETCD CONTAINS:                                            │
│  • All Kubernetes objects (pods, deployments, etc.)        │
│  • Secrets (base64 encoded by default)                     │
│  • ConfigMaps                                               │
│  • RBAC configuration                                      │
│  • Service account tokens                                  │
│                                                             │
│  IF ETCD IS COMPROMISED:                                   │
│  • All secrets exposed                                     │
│  • Cluster state can be modified                           │
│  • Complete cluster compromise                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The first etcd control is network isolation. In a typical hardened design, only API server instances need direct client access to etcd, and that access should use TLS with client certificate authentication. Pods should not reach etcd by service discovery, node routing, host networking, or a permissive firewall rule. If an attacker compromises a pod and can connect to the etcd client port, the attacker may bypass API server authentication, RBAC, admission, and audit policy all at once.

```text
┌─────────────────────────────────────────────────────────────┐
│              ETCD SECURITY CONTROLS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ACCESS CONTROL                                            │
│  ├── Only API server should access etcd                    │
│  ├── Network isolation (firewall, security groups)         │
│  ├── Client certificate authentication                     │
│  └── No direct access from pods                            │
│                                                             │
│  ENCRYPTION IN TRANSIT                                     │
│  ├── TLS for client-to-server (CIS 2.1)                    │
│  ├── TLS for peer-to-peer (CIS 2.3, 2.4)                   │
│  └── Mutual TLS (mTLS) preferred (CIS 2.2)                 │
│                                                             │
│  ENCRYPTION AT REST                                        │
│  ├── Kubernetes secrets encryption (CIS 1.2.31)            │
│  ├── Provider options: aescbc, aesgcm, kms                 │
│  ├── KMS integration for key management                    │
│  └── Envelope encryption pattern                           │
│                                                             │
│  BACKUP SECURITY                                           │
│  ├── Encrypt backups                                       │
│  ├── Secure backup storage                                 │
│  └── Test restore procedures                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Transport encryption protects two paths. Client-to-server TLS protects the connection between the API server and etcd. Peer-to-peer TLS protects the replication traffic between etcd members. Both matter because a cluster may place etcd members on separate control plane nodes, and the internal network is not automatically trustworthy. A network observer that can read peer traffic or impersonate an etcd member can threaten consistency, confidentiality, and recovery.

Encryption at rest is a separate control. Kubernetes can encrypt selected resources before writing them into etcd by using an `EncryptionConfiguration`, and Secret resources are the usual first target. The provider order is important because the first provider writes new data, while every configured provider may be tried for reads. That is why an `identity` fallback can appear during a migration: it lets the API server read older unencrypted data until the team rewrites those objects under the new provider.

### Secrets Encryption at Rest

By default, Kubernetes secrets are only base64 encoded in etcd, not encrypted. The following preserved configuration example shows the common pattern: an encryption provider first, then identity as a read fallback. In production, the key material must be generated, stored, rotated, and distributed through a controlled process; the example intentionally uses a non-secret placeholder value so it cannot be mistaken for a usable key.

```yaml
# EncryptionConfiguration example
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-key>
      - identity: {}  # Fallback for reading unencrypted
```

| Provider | Description | Use Case |
|----------|-------------|----------|
| `identity` | No encryption | Never for production |
| `aescbc` | AES-CBC encryption | Good for self-managed |
| `aesgcm` | AES-GCM encryption | Faster than aescbc |
| `kms` | External key management | Best for compliance |

The practical mistake is enabling the file and assuming the job is finished. Existing Secrets remain in their previous stored form until they are rewritten, so a migration plan should include a controlled rewrite of Secret objects and verification that newly stored data is encrypted. In managed Kubernetes, the cloud provider may handle etcd and expose envelope encryption options through its platform API, but the assessment question remains the same: where is the key managed, what resources are covered, and how would you prove that old data was re-encrypted?

Before running this in a real cluster, what output would convince you that encryption is working rather than merely configured? A strong answer uses more than one signal: the API server manifest references the encryption configuration, a newly written Secret can still be read through the API, and a controlled inspection of raw etcd data does not reveal the Secret value in clear text. The important security habit is to verify behavior, not just file presence.

Backups deserve the same respect as the live database. An encrypted etcd member with unencrypted snapshots in a shared object bucket is still a data exposure path. Backup security includes encrypting the snapshot, restricting who can restore it, testing restoration in an isolated environment, and documenting which keys are required during recovery. A team that cannot restore securely may turn a security incident into an outage while trying to protect data.

## Scheduler Security

The scheduler does not usually read application secrets or terminate TLS, so it can look less sensitive than the API server or etcd. That impression is incomplete. The scheduler decides where pods run, and placement is a security decision whenever nodes have different trust zones, hardware access, compliance labels, tenant boundaries, or network reachability. A compromised scheduler can influence which workloads co-reside and which isolation assumptions stop being true.

Pause and predict: if an attacker compromises the scheduler, they can influence where pods are placed; how could this be exploited even without modifying the pods themselves? One answer is forced co-location. A sensitive workload could be placed on a node that also runs attacker-controlled code, or a noisy workload could be placed where it starves important services. Another answer is isolation bypass when teams rely on node labels, taints, and affinity to separate regulatory workloads from general workloads.

```text
┌─────────────────────────────────────────────────────────────┐
│              SCHEDULER SECURITY                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SCHEDULER RESPONSIBILITIES                                │
│  • Selects nodes for unscheduled pods                     │
│  • Respects resource requests and limits                   │
│  • Honors affinity and anti-affinity rules                │
│  • Enforces taints and tolerations                         │
│                                                             │
│  SECURITY CONCERNS                                         │
│  ├── Runs with significant cluster privileges             │
│  ├── Compromise could influence pod placement              │
│  ├── Could bypass node isolation                          │
│  └── Could cause denial of service                        │
│                                                             │
│  SECURITY CONTROLS                                         │
│  ├── Client certificate authentication to API server      │
│  ├── Minimal RBAC permissions (built-in binding)          │
│  ├── Bind address to localhost (127.0.0.1) (CIS 1.4.2)    │
│  ├── Disable profiling if not needed (CIS 1.4.1)          │
│  ├── Run on dedicated control plane nodes                 │
│  └── Network isolation from workload nodes                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The scheduler should authenticate to the API server with its own client certificate or kubeconfig, and its RBAC should stay close to the built-in permissions required for scheduling. It does not need broad administrative bindings created by hand. Its insecure serving interfaces should bind to localhost unless there is a deliberate, protected observability path. Profiling can be valuable during performance investigations, but leaving profiling endpoints broadly reachable in normal operation exposes internal behavior for little security benefit.

A realistic scheduler war story starts with an innocent label. A platform team labels a few nodes for PCI workloads, then later gives an automation service permission to label nodes because a rollout script needs flexibility. If the scheduler, node labels, and RBAC are not reviewed together, that automation service may indirectly decide where regulated workloads can run. Scheduler security therefore includes the scheduler process and the surrounding placement controls that feed its decisions.

## Controller Manager Security

The controller manager runs reconciliation loops. A controller notices that desired state and actual state differ, then takes action to close the gap. That action can create pods, update endpoints, react to node health, issue service account tokens, or manage other built-in resources. Reconciliation is one of Kubernetes' strengths, but a compromised controller manager is dangerous because it can repeatedly turn malicious desired state into durable cluster behavior.

```text
┌─────────────────────────────────────────────────────────────┐
│              CONTROLLER MANAGER SECURITY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTROLLERS INCLUDE:                                      │
│  • Node controller (node health)                           │
│  • Replication controller (pod replicas)                   │
│  • Endpoints controller (service endpoints)                │
│  • ServiceAccount controller (creates default SA)          │
│  • Many more...                                            │
│                                                             │
│  SECURITY CONCERNS                                         │
│  ├── Access to service account signing key                │
│  ├── Can create/delete pods and services                  │
│  ├── Manages node lifecycle                               │
│  └── Compromise = cluster-wide impact                     │
│                                                             │
│  KEY SECURITY FLAGS                                        │
│  ├── --use-service-account-credentials=true (CIS 1.3.3)   │
│  │   (Use separate SA for each controller)                 │
│  ├── --root-ca-file (CIS 1.3.5)                           │
│  │   (CA for verifying API server)                         │
│  └── --service-account-private-key-file (CIS 1.3.4)       │
│      (Key for signing SA tokens)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The `--use-service-account-credentials=true` flag matters because it separates controller identities instead of forcing every built-in controller through one broad credential. Separation improves audit clarity and limits how much one controller identity should be able to do. The `--service-account-private-key-file` flag matters because token signing is a trust root for workloads. If an attacker obtains the signing key, they may be able to mint tokens that look legitimate until the key is rotated and dependent trust is repaired.

Controller manager endpoint hardening follows the same principle as scheduler hardening. Bind diagnostic endpoints narrowly, expose metrics through a protected path, and avoid leaving profiling enabled without a reason. The component should authenticate to the API server with its own credentials and should not share client material with unrelated processes. A team investigating control plane compromise should be able to tell which controller identity performed a change rather than seeing one indistinct administrative actor everywhere.

The controller manager also connects control plane security to node lifecycle. If a controller can mark nodes, change endpoints, or affect service account behavior, then its compromise can redirect traffic, hide failing infrastructure, or make workloads trust the wrong identity. That is why controller manager hardening is not a niche CIS exercise. It protects the automation that quietly keeps the cluster alive.

## Control Plane Network Security

Network placement turns component hardening into a system boundary. A secure API server flag set cannot protect etcd if etcd is directly reachable from every pod network. A well-scoped scheduler credential is less useful if its debug endpoint listens on an interface exposed to worker nodes. Control plane network security asks which components need to talk, which ports are required, which paths are administrative, and which paths should be impossible during normal operation.

```text
┌─────────────────────────────────────────────────────────────┐
│              CONTROL PLANE NETWORK                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RECOMMENDED ARCHITECTURE                                  │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │           PRIVATE SUBNET (Control Plane)           │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │    │
│  │  │   API   │ │  etcd   │ │ Sched   │ │  Ctrl   │  │    │
│  │  │  Server │ │         │ │         │ │   Mgr   │  │    │
│  │  └────┬────┘ └─────────┘ └─────────┘ └─────────┘  │    │
│  │       │                                            │    │
│  └───────┼────────────────────────────────────────────┘    │
│          │ (Only API server exposed)                       │
│          ▼                                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │           PRIVATE SUBNET (Worker Nodes)            │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐              │    │
│  │  │  Node 1 │ │  Node 2 │ │  Node 3 │              │    │
│  │  │ kubelet │ │ kubelet │ │ kubelet │              │    │
│  │  └─────────┘ └─────────┘ └─────────┘              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  SECURITY REQUIREMENTS:                                    │
│  • etcd: Only accessible from API server                   │
│  • API server: Accessible from nodes and admins           │
│  • Scheduler/CM: Only need to reach API server            │
│  • Private API endpoint preferred                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The diagram preserves a simple but important architecture rule: the API server is exposed to the actors that need the Kubernetes API, while etcd, scheduler, and controller manager remain private control plane services. In self-managed clusters, you implement that with host firewalls, security groups, routing, TLS, and sometimes separate interfaces. In managed clusters, you often choose between public and private API endpoints and rely on the provider for etcd isolation, but you still own how administrator networks, CI systems, and worker nodes reach the API.

Network controls should be paired with identity controls because either layer can be misread. A private API endpoint does not remove the need for RBAC, audit logging, and admission policy; it only reduces who can reach the front door. TLS on etcd does not remove the need for firewall rules; it only requires a client to prove identity after it reaches the port. Defense in depth means an attacker must defeat network reachability, cryptographic trust, and Kubernetes policy rather than winning after one mistake.

For exam and production thinking, separate "reachable" from "authorized." A pod might be unauthorized to read Secrets through the API server but still able to open a TCP connection to etcd if routing permits it. A developer laptop might be authorized through OIDC but should not reach component debug endpoints directly. A good control plane assessment records both dimensions because real incidents often begin where teams assumed one layer implied the other.

## Control Plane Assessment Workflow

An assessment is useful when it turns scattered settings into a prioritized remediation plan. Start by identifying the cluster type, because managed and self-managed clusters expose different control surfaces. In self-managed clusters, static pod manifests and service unit files may show API server, scheduler, controller manager, and etcd flags directly. In managed clusters, provider APIs and cluster configuration screens may be the only supported path for endpoint exposure, encryption settings, and audit integration.

The first pass should map each insecure flag to the security property it weakens. Anonymous authentication weakens identity confidence. `AlwaysAllow` weakens authorization. Missing `PodSecurity` and `NodeRestriction` weaken admission and node blast-radius controls. Missing audit logs weaken detection and investigation. Plain HTTP etcd URLs weaken transport confidentiality and server identity. This mapping matters because it helps you explain risk in operational language instead of dumping a list of flags on another team.

The second pass should consider change risk. Switching `AlwaysAllow` to `Node,RBAC` in a production cluster without understanding existing workloads can cause outages, even though the current setting is unsafe. Enabling encryption at rest without rewriting existing Secrets can create a false sense of completion. Locking down an API endpoint without accounting for CI networks can break deployments. A senior remediation plan fixes the riskiest exposure quickly while sequencing high-blast-radius changes through staging, audit data, and rollback plans.

Which approach would you choose here and why: immediately harden every control plane flag in one maintenance window, or first collect audit evidence and stage the changes with workload owners? The safer answer is usually staged remediation, except for exposures that are actively exploitable and have a narrow fix, such as an etcd port reachable from workload networks. The goal is not to make change slow. The goal is to make the security improvement real instead of replacing one incident with another.

When you document findings, write them as cause, impact, and fix. "Anonymous auth is true" is a setting. "Unauthenticated requests can enter the API server request path, and any accidental anonymous RBAC binding can reveal cluster information; set `--anonymous-auth=false` after confirming required probes authenticate" is an actionable finding. This style also helps with constructive alignment for your own learning: you are evaluating controls, diagnosing exposures, comparing component risks, and implementing a prioritized assessment.

## Patterns & Anti-Patterns

### Pattern: API Server as the Only State Door

Use this pattern when you want every normal cluster state change to pass through authentication, authorization, admission, and audit. The API server should be the only client path to etcd, and administrative automation should use Kubernetes API credentials rather than direct database access. This pattern works because it concentrates policy enforcement at a component designed for Kubernetes semantics, not at a raw key-value store that cannot understand RBAC or Pod Security.

The scaling consideration is availability. If the API server is the only state door, the API server must be highly available, monitored, and protected from noisy clients. Rate limits, audit policy design, and webhook availability become part of the pattern rather than optional extras. A healthy implementation makes the API server central without making it fragile.

### Pattern: Component-Specific Identities

Use this pattern when scheduler, controller manager, kubelets, workloads, and humans need different permissions and different audit trails. The controller manager should use separated service account credentials where supported, the scheduler should use its own client identity, and workloads should avoid sharing broad service accounts. The pattern works because credentials then describe a real actor, which makes least privilege and incident response possible.

This pattern scales through review automation. Teams can periodically query RBAC, test `k auth can-i` for important service accounts, and alert on new cluster-admin bindings. It does not remove the need for human judgment, but it gives reviewers smaller units to reason about. A credential that only means "some internal component" is hard to defend and hard to investigate.

### Pattern: Private Components with Verified Exceptions

Use this pattern when the control plane spans networks, accounts, or administrative teams. etcd, scheduler, and controller manager endpoints should be private by default, while the API server should be exposed only to the networks and identities that need it. Exceptions should name the source, destination, port, protocol, business reason, and expiration or review date. This works because control plane services rarely need broad reachability, and broad reachability creates silent attack paths.

At scale, the hard part is drift. A firewall rule added during an incident can outlive the incident, and a temporary public API endpoint can become normal because it makes developer access easy. Treat network exceptions as configuration that needs ownership, review, and evidence. The security posture is not the diagram from the launch date; it is the effective reachability today.

### Anti-Pattern: Bootstrap Flags Left in Production

Teams fall into this anti-pattern when they use permissive settings to bring up a cluster and never remove them. `--authorization-mode=AlwaysAllow`, anonymous authentication, and minimal admission plugins can make early troubleshooting easier, but they are not neutral settings. They teach the cluster to trust too much and leave every later workload one credential theft away from a broader compromise.

The better alternative is to create a bootstrap checklist that has an explicit hardening exit. A cluster is not production-ready until the API server uses `Node,RBAC`, anonymous authentication is disabled unless justified, audit logging writes to a real path, and security-focused admission controllers are present. If an emergency requires a temporary relaxation, give it an owner and a removal time.

### Anti-Pattern: Treating etcd Encryption as a Checkbox

This anti-pattern appears when a team configures an encryption provider but does not rotate data, secure keys, or protect backups. It happens because encryption at rest sounds binary, while Kubernetes encryption behavior depends on provider order, resource selection, rewrites, and key management. The resulting cluster may pass a shallow review while older Secrets and snapshots remain exposed.

The better alternative is an encryption lifecycle. Decide which resources are covered, choose a provider that matches compliance needs, store keys outside casual administrator access, rewrite existing objects, verify raw storage, and test restore with the required keys. For managed clusters, record the provider option and evidence exposed by the platform instead of assuming the provider handles every detail automatically.

### Anti-Pattern: Public Debug Endpoints

This anti-pattern usually begins as observability convenience. A scheduler or controller manager endpoint is exposed broadly so a team can scrape metrics, profile performance, or troubleshoot during rollout. Over time, the endpoint becomes part of normal monitoring even if it exposes more information than workers or users need. The component may still require authentication for high-risk actions, but unnecessary reachability increases reconnaissance value.

The better alternative is a protected observability path. Bind sensitive component endpoints locally or privately, collect metrics through authenticated and authorized mechanisms, and disable profiling unless a current investigation needs it. If an endpoint must be reachable outside the control plane subnet, document why and place it behind network and identity controls that match its sensitivity.

## Decision Framework

Use a three-layer decision framework when reviewing control plane security: request path, state store, and component operations. The request path covers API server authentication, authorization, admission, TLS, and audit. The state store covers etcd reachability, transport encryption, at-rest encryption, key management, and backups. Component operations cover scheduler and controller manager identities, bind addresses, profiling, metrics, and network isolation. Keeping those layers separate prevents a common review mistake where one strong control hides a weak neighboring control.

Start with exploitability. If etcd is reachable from workload networks or the API server uses `AlwaysAllow`, prioritize those findings because they can turn one compromised credential or pod into broad control quickly. Next, review evidence controls such as audit logging, because missing logs make every later incident harder to bound. Then handle refinement work such as tightening overly broad RBAC, improving webhook failure policies, and reducing diagnostic endpoint exposure. This order favors fast reduction of cluster-wide compromise paths without ignoring long-term hygiene.

Use blast radius to choose between immediate and staged changes. Disabling anonymous authentication is usually low risk if no legitimate anonymous access exists, but changing authorization modes can break workloads that silently depended on permissive access. Enabling at-rest encryption is valuable, yet it needs a data rewrite and key plan. Restricting API endpoint networks improves exposure, but it must include CI, administrators, and break-glass access. The better decision is the one that reduces real risk and survives the next deployment day.

When comparing scheduler and controller manager risk, ask what the component can influence rather than whether it stores Secrets directly. The scheduler influences placement, which affects isolation, availability, and co-residency risk. The controller manager influences reconciliation, service account behavior, endpoints, and node lifecycle. Both should use narrow identities and private endpoints, but the impact stories differ. A good assessment explains those differences so remediation owners understand why a finding matters.

Finally, require proof. A manifest line, cloud setting, or screenshot is useful, but the strongest evidence ties configuration to observed behavior. Can an unauthenticated request do anything useful? Can the target service account create a privileged pod? Can a pod network reach etcd? Can a new Secret be read through the API but not seen in clear text in raw storage? The decision framework ends with verification because control plane security is only as strong as the behavior running cluster today.

Write the final decision in language that another engineer can act on during a change window. Good findings name the unsafe condition, the component affected, the expected hardened state, the verification evidence, and the operational risk of changing it. That level of specificity turns control plane security from an opinion into a repeatable engineering practice.

## Did You Know?

- **The API server is the only normal Kubernetes component that writes directly to etcd.** That design is why direct etcd access is so dangerous: it bypasses Kubernetes authentication, authorization, admission, and audit semantics.

- **Kubernetes Secrets are base64 encoded by default, not encrypted by default.** At-rest encryption requires explicit API server configuration or a managed Kubernetes provider feature, and older objects need to be rewritten to change their stored form.

- **Node authorization and NodeRestriction solve different halves of the node problem.** The authorizer limits what kubelet credentials may request, while the admission controller limits which node and pod fields kubelets may modify.

- **Managed Kubernetes reduces control plane ownership, not control plane responsibility.** You may not patch etcd flags directly, but you still choose API endpoint exposure, audit integration, encryption options, administrator access, and workload permissions.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Anonymous auth enabled | Bootstrap defaults or health checks are copied into production without reviewing anonymous RBAC impact | Set `--anonymous-auth=false` after confirming probes and clients authenticate correctly |
| No etcd encryption | Teams assume Secret base64 encoding is encryption or rely on provider defaults without evidence | Enable encryption at rest for Secrets, rewrite existing objects, and verify stored data behavior |
| etcd exposed to network | Flat networks or broad security groups let pods and worker nodes reach control plane database ports | Restrict etcd access to API server instances and require TLS client certificate authentication |
| Public API server endpoint | Remote administration is prioritized before network exposure and identity controls are designed | Prefer a private endpoint or restrict public access to approved networks with strong authentication |
| Missing audit logging | Logging is deferred to reduce noise, storage cost, or setup time during cluster bootstrap | Configure audit policy and `--audit-log-path`, then tune high-value events rather than disabling logs |
| `AlwaysAllow` authorization | Labs, emergency recovery, or early bootstrap settings survive into real environments | Move to `--authorization-mode=Node,RBAC` through staged testing and workload permission review |
| Controller endpoints exposed broadly | Metrics or profiling convenience leaves scheduler and controller manager interfaces reachable | Bind sensitive endpoints to localhost or private networks and route observability through protected paths |

## Quiz

<details>
<summary>Your API server assessment finds anonymous authentication enabled, audit logging disabled, and `Node,RBAC` authorization present. Which risk do you explain first, and what evidence would you collect before changing flags?</summary>
Anonymous authentication should be explained first because it allows unauthenticated requests to enter the request path as an anonymous identity. `Node,RBAC` still limits what that identity can do, so the evidence should include existing anonymous RBAC permissions, discovery access, health check requirements, and any clients that might be relying on unauthenticated behavior. Audit logging should be fixed as part of the same remediation plan because it provides evidence for future investigations. The safest change disables anonymous authentication after validating legitimate probes and then enables a focused audit policy rather than creating noisy logs with little value.
</details>

<details>
<summary>A teammate says etcd is safe because only administrators know the endpoint. During testing, a pod can open a TCP connection to etcd. How do you diagnose the exposure and explain the impact?</summary>
The diagnosis is a network isolation failure, not merely a documentation problem. If a pod can reach etcd, a compromised workload may try to bypass the API server controls that normally enforce authentication, RBAC, admission, and audit. The impact is severe because etcd stores cluster state, RBAC policy, and Secret resources that may not be encrypted in raw storage. The fix should restrict etcd client access to API server instances, require TLS client certificates, and verify that workload networks cannot reach the database path.
</details>

<details>
<summary>Your team enables an `aescbc` encryption provider with `identity` as a fallback, then declares all existing Secrets encrypted. What is wrong with that conclusion?</summary>
The conclusion confuses configured future writes with the stored form of existing objects. Provider order means new Secret writes use the first provider, while the identity fallback may still read older unencrypted Secrets. Existing Secrets need to be rewritten through the API server before their stored form changes. A complete answer includes key management, backup protection, and verification that raw etcd data does not reveal a newly written test value in clear text.
</details>

<details>
<summary>A cluster uses a private API endpoint but the API server runs with `--authorization-mode=AlwaysAllow`. How do you compare those controls?</summary>
The private endpoint is a useful reachability control because fewer networks can connect to the API server. It does not replace authorization because any identity that does reach the API server is allowed to perform every action under `AlwaysAllow`. The comparison should separate network access from Kubernetes permission checks. The remediation keeps endpoint restrictions while moving authorization to `Node,RBAC` through testing that identifies workloads depending on implicit broad access.
</details>

<details>
<summary>A scheduler endpoint is reachable from worker nodes, and profiling is enabled. No one has shown pod modification. Why is this still a control plane security finding?</summary>
The scheduler influences pod placement, and placement affects isolation, availability, and co-residency risk even when pod specs are not directly modified. A broadly reachable profiling or diagnostic endpoint also gives attackers reconnaissance value and may expose internals that should stay private. The finding is about unnecessary control plane reachability and information exposure. The fix is to bind sensitive endpoints to localhost or a private control plane network and expose metrics through an authenticated observability path.
</details>

<details>
<summary>The controller manager uses one broad credential for built-in controllers. During incident response, audit records show changes by the same identity everywhere. What design improvement would you recommend?</summary>
Recommend using separate service account credentials for controllers where supported, including `--use-service-account-credentials=true`. Separate identities improve least privilege because each controller can receive permissions closer to its job. They also improve audit quality because investigators can distinguish which control loop performed a change. The recommendation should include protecting service account signing keys and reviewing controller manager endpoint exposure at the same time.
</details>

<details>
<summary>You are asked to implement a control plane assessment for a production cluster in one afternoon. How do you prioritize the work without turning it into a risky mass change?</summary>
Start by collecting evidence for the request path, state store, and component operation layers. Prioritize actively exploitable cluster-wide paths first, such as `AlwaysAllow`, reachable etcd, missing etcd TLS, or absent audit logs. Stage changes that can break workloads, especially authorization mode changes and API endpoint restrictions, with testing and rollback notes. The output should map each insecure flag or exposure to impact, fix, owner, and verification evidence rather than only listing settings.
</details>

## Hands-On Exercise: Control Plane Security Assessment

This exercise uses a static API server snippet so you can practice assessment reasoning without needing administrative access to a real control plane. In a live self-managed cluster, similar flags might appear in a static pod manifest under the control plane host's manifest directory, while managed clusters expose equivalent choices through provider settings. Your job is to read the snippet like an investigator: identify the weakened control, explain the likely impact, choose a hardened setting, and decide whether the change is immediate or staged. Treat each finding as evidence for a decision, because production remediation succeeds when the team understands both the technical weakness and the operational consequence.

**Scenario**: Review these API server flags and identify security issues across authentication, authorization, admission, audit logging, and etcd transport security before you propose changes:

```bash
kube-apiserver \
  --anonymous-auth=true \
  --authorization-mode=AlwaysAllow \
  --enable-admission-plugins=NamespaceLifecycle,ServiceAccount \
  --audit-log-path="" \
  --etcd-servers=http://etcd:2379
```

Begin by separating the request path from the state store path. Anonymous authentication and `AlwaysAllow` affect how requests enter and pass through the API server. Missing admission plugins affect whether risky objects can be rejected after authorization. An empty audit log path affects detection and investigation. The plain HTTP etcd URL affects the trust and confidentiality of the connection to the state database. This separation keeps your answer precise because each flag weakens a different security property.

- [ ] Task 1: Evaluate API server authentication, authorization, admission, and audit controls in the snippet, then name the insecure flag for each control.
- [ ] Task 2: Diagnose the etcd transport exposure and explain why direct or unencrypted state store access changes the compromise path.
- [ ] Task 3: Compare the scheduler and controller manager controls from this module with the API server controls shown in the snippet, focusing on identity and bind address risk.
- [ ] Task 4: Implement a prioritized remediation plan that lists immediate fixes, staged fixes, validation commands or checks, and rollback considerations.
- [ ] Task 5: Write a short evidence note that an auditor could understand without seeing the original snippet.

<details>
<summary>Solution guidance for Tasks 1 and 2</summary>
The API server snippet has at least five important findings. `--anonymous-auth=true` allows unauthenticated requests to enter the request path and should normally be set to `false` in production. `--authorization-mode=AlwaysAllow` removes meaningful authorization and should be replaced with `Node,RBAC` after testing permissions. The admission plugin list omits security-focused controls such as `PodSecurity` and `NodeRestriction`, so risky pods and node credential behavior may not be constrained. `--audit-log-path=""` disables useful audit logging, and `--etcd-servers=http://etcd:2379` shows an unencrypted etcd client URL that should move to HTTPS with certificate validation.
</details>

<details>
<summary>Solution guidance for Tasks 3 and 4</summary>
Scheduler and controller manager controls follow the same themes but protect different behaviors. The scheduler needs a narrow identity, private bind address, and limited profiling exposure because it influences placement. The controller manager needs separated service account credentials where supported, protected signing keys, private endpoints, and clear audit identity because it performs reconciliation. For remediation, fix obviously unsafe and low-risk settings quickly, such as empty audit paths and exposed diagnostic endpoints, while staging authorization mode changes and encryption migrations through testing, owner review, and rollback plans.
</details>

<details>
<summary>Solution guidance for Task 5</summary>
A concise evidence note could say: "The assessed API server configuration weakens identity, authorization, admission, auditability, and etcd transport security. Anonymous requests are accepted, every authenticated request is authorized, security-focused admission controllers are absent, audit logging has no destination, and the etcd connection uses plain HTTP. Recommended remediation is `--anonymous-auth=false`, `--authorization-mode=Node,RBAC`, admission controls including `PodSecurity` and `NodeRestriction`, a real audit log path with policy, and HTTPS etcd endpoints with CA and client certificate validation." This note explains cause, impact, and fix without requiring the reader to infer risk from raw flags.
</details>

Use the success criteria below to check whether your assessment connects each finding to evidence, risk, and a practical remediation step:

- [ ] You can map each insecure API server flag to authentication, authorization, admission, audit, or etcd transport risk.
- [ ] You can explain why etcd exposure bypasses API server controls instead of merely duplicating them.
- [ ] You can distinguish scheduler placement risk from controller manager reconciliation and signing-key risk.
- [ ] You can propose a remediation order that reduces cluster-wide compromise paths without ignoring outage risk.
- [ ] You can name at least one verification check for each major control instead of relying only on configuration intent.

## Summary

Control plane security is about protecting the brain of Kubernetes, but that phrase is only useful when it points to concrete component responsibilities and control choices:

| Component | Key Security Controls |
|-----------|----------------------|
| **API Server** | TLS, authentication (certs, OIDC), RBAC authorization, admission control |
| **etcd** | Network isolation, TLS, encryption at rest, backup encryption |
| **Scheduler** | Certificate auth, network isolation, minimal privileges |
| **Controller Manager** | Certificate auth, separate service accounts per controller |

The most important lesson is that control plane security is layered. The API server should be the intentional front door, etcd should be private and encrypted, scheduler and controller manager endpoints should be narrow, and every component should use an identity that matches its job. If a cluster gives anonymous users, stolen workload tokens, or compromised pods a path around those layers, the cluster-wide blast radius expands quickly.

In practice, strong control plane reviews sound like engineering decisions, not slogans. You evaluate the API server request path, diagnose etcd exposure and encryption gaps, compare scheduler and controller manager privileges, and implement a remediation plan with evidence. That is the skill the KCSA exam expects and the habit production teams need when Kubernetes becomes important enough to defend.

## Sources

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
- [Kubernetes Authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
- [Kubernetes Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes Node Authorization](https://kubernetes.io/docs/reference/access-authn-authz/node/)
- [Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Operating etcd clusters for Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [etcd Transport Security Model](https://etcd.io/docs/v3.5/op-guide/security/)
- [kube-apiserver Reference](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/)
- [kube-controller-manager Reference](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)
- [kube-scheduler Reference](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/)

## Next Module

[Module 2.2: Node Security](../module-2.2-node-security/) continues the same layered-security theme by moving from control plane components to worker nodes, kubelets, and container runtimes.
