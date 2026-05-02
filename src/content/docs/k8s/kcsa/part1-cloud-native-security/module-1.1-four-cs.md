---
title: "Module 1.1: The 4 Cs of Cloud Native Security"
slug: k8s/kcsa/part1-cloud-native-security/module-1.1-four-cs
sidebar:
  order: 2
revision_pending: false
---

> **Complexity**: `[MEDIUM]` - Core security framework for KCSA learners who need to classify ambiguous cloud native findings across infrastructure, Kubernetes, runtime, and application boundaries.
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: [Module 0.2: Security Mindset](/k8s/kcsa/part0-introduction/module-0.2-security-mindset/)

## Learning Outcomes

After completing this module, you will be able to perform the following KCSA-level security analysis tasks with evidence rather than layer-name memorization:

1. **Compare** the Cloud, Cluster, Container, and Code layers and justify why security work must start from the lower layers before relying on upper-layer controls.
2. **Analyze** a cloud native incident and identify which 4 Cs layer the attacker entered through, which layers limited the blast radius, and which layers failed.
3. **Evaluate** whether a proposed security control addresses the right layer or only gives the team false confidence in another layer.
4. **Design** a layered response plan that maps practical controls to Cloud, Cluster, Container, and Code without treating any single layer as sufficient.
5. **Debug** ambiguous security findings by separating infrastructure responsibility, Kubernetes configuration responsibility, runtime responsibility, and application responsibility.

## Why This Module Matters

In late 2019, a large financial services company disclosed that an attacker had reached sensitive application data after abusing a server-side request forgery flaw and cloud instance metadata. The public discussion focused on the web application bug, but the deeper lesson was layered: application code accepted a dangerous request, the runtime environment could reach metadata, cloud identity allowed data access, and monitoring did not stop the sequence quickly enough. The reported business impact included regulatory penalties, legal costs, remediation work, and years of reputational damage, which is exactly why cloud native security cannot be reduced to one scanner, one firewall, or one Kubernetes policy.

A platform engineer sees the same pattern in smaller form during an ordinary incident. A production API starts sending suspicious outbound traffic, the application team points to yesterday's dependency scan, the Kubernetes administrator points to RBAC and says the workload service account cannot list Secrets, and the cloud team points to private subnets and says the cluster is not publicly exposed. Each statement may be true, but none of them answers the operational question that matters during containment: where did the attacker enter, how far can they move, which control should have stopped the next step, and which team owns the durable repair.

The 4 Cs of cloud native security give that conversation a structure. Instead of arguing from team ownership or favorite tools, the model asks learners to reason from dependency: Cloud supports Cluster, Cluster runs Containers, Containers execute Code. A weakness in a lower layer can undermine every layer above it, while a strong upper layer can still reduce damage after an attacker enters through the application. This module teaches that dependency model as an incident-analysis tool, a design-review tool, and a KCSA exam strategy.

This matters for the KCSA because exam scenarios rarely say, "This is a Cloud layer question." They describe a situation: a leaked IAM key, a permissive RoleBinding, a privileged container, or a vulnerable package. Your job is to map evidence to the correct layer, choose the control that actually changes risk, and avoid answers that sound secure but defend the wrong boundary. By the end of the module, you should be able to read a messy scenario, separate the layers, and explain why a single good control does not make the whole system safe.

## The 4 Cs Model: A Dependency Stack

The 4 Cs model is not four independent checklists. It is a stack of dependencies where each layer inherits risk from the layer below it. Cloud is the foundation because Kubernetes runs on infrastructure, identities, networks, and storage that exist before the cluster can protect anything. Cluster is next because the API server, admission controls, RBAC, NetworkPolicies, and node configuration decide what workloads may do. Container follows because images, runtime isolation, Linux capabilities, and filesystem settings decide how much damage a running process can cause. Code is the innermost layer because application logic, dependencies, authentication, and data handling are what users and attackers usually touch first.

```text
┌─────────────────────────────────────────────────────────────┐
│                    THE 4 Cs OF SECURITY                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│      Each layer builds on the security of the layer         │
│      below it. A breach at any layer can weaken all         │
│      layers above it unless other controls contain it.      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                     CLOUD                           │    │
│  │  Infrastructure, network, identity, storage          │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │                  CLUSTER                    │    │    │
│  │  │  Kubernetes control plane and configuration  │    │    │
│  │  │  ┌─────────────────────────────────────┐    │    │    │
│  │  │  │             CONTAINER               │    │    │    │
│  │  │  │  Image, runtime, and isolation       │    │    │    │
│  │  │  │  ┌─────────────────────────────┐    │    │    │    │
│  │  │  │  │           CODE              │    │    │    │    │
│  │  │  │  │  Application and libraries   │    │    │    │    │
│  │  │  │  └─────────────────────────────┘    │    │    │    │
│  │  │  └─────────────────────────────────────┘    │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Security at one layer cannot erase insecurity below it;    │
│  it can only reduce what happens after the lower layer       │
│  has already been trusted.                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A useful way to read the diagram is from the outside inward when designing controls, and from the inside outward when investigating many incidents. Design starts with the foundation: who can create infrastructure, which networks are reachable, and how cloud identities are scoped. Investigation often starts where symptoms appear: a web request hits vulnerable code, a container starts a shell, a Pod uses a broad service account, or an attacker uses a cloud credential. Senior practitioners move in both directions because the initial symptom is not always the root cause.

Think of the stack like a building rather than a set of locked rooms. Better application code is like a strong office door; it matters, but it does not compensate for a building badge system that lets anyone enter the server floor. Strong RBAC is like a floor access rule; it matters, but it does not compensate for a cloud administrator credential that can move the whole building's wiring. The point is not that lower layers are more important in every moment. The point is that lower layers are trusted by the layers above them, so a lower-layer failure can create paths that upper-layer teams never see.

> **Active check:** If a developer says, "We use distroless images and drop Linux capabilities, so the service is secure," which layer has the developer addressed, and which layers remain unproven? Write one sentence that separates the true part of the claim from the risky assumption.

| Layer | Primary question | Typical owner | Example control |
|---|---|---|---|
| **Cloud** | Can the underlying infrastructure, network, identity, and storage be trusted enough to host the cluster? | Cloud platform, infrastructure, security engineering | Least-privilege IAM, private subnets, encrypted volumes, firewall rules, audit logs |
| **Cluster** | Does Kubernetes authenticate, authorize, admit, isolate, schedule, and observe workloads safely? | Platform engineering, Kubernetes administrators, security engineering | RBAC, Pod Security Standards, admission policy, NetworkPolicy, etcd encryption, audit policy |
| **Container** | Does the image and runtime configuration limit what the process can do after it starts? | Application platform, DevSecOps, workload owners | Image scanning, signing, non-root users, read-only root filesystem, seccomp, dropped capabilities |
| **Code** | Does the application safely handle users, data, dependencies, secrets, and external input? | Application teams, product engineering, application security | Input validation, dependency scanning, authorization checks, secret handling, secure session management |

The central judgment skill is not naming a layer from memory. The skill is deciding whether a control changes the same risk that the finding describes. Image scanning does not fix broad RBAC. NetworkPolicy does not fix SQL injection. Encrypted cloud disks do not stop a compromised application from reading its own database password. Each control can be valuable, but only when it is applied to the layer where the risk actually lives.

That judgment also prevents false confidence during reviews. A team may show a clean image scan, but the scan says little about whether the Pod can talk to every namespace. A cluster may enforce restricted Pod security settings, but that says little about whether the application confuses tenant IDs. A cloud account may require multifactor authentication for administrators, but that says little about whether a workload identity can read an object bucket. When you compare layers, ask which claim has been proven and which claim has merely been implied.

## Layer 1: Cloud, the Infrastructure Boundary

The Cloud layer includes the infrastructure that makes the cluster possible: accounts or projects, virtual networks, compute instances, managed control plane services, storage, load balancers, DNS, key management, and cloud IAM. In self-managed environments this layer may include physical hosts and data center networking. In managed Kubernetes it still matters because the provider may run part of the control plane, but your organization usually decides who can create clusters, attach identities, expose load balancers, configure logging sinks, and read data from supporting services.

```text
┌─────────────────────────────────────────────────────────────┐
│              CLOUD LAYER SECURITY                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IDENTITY & ACCESS                                          │
│  ├── IAM policies with least privilege                      │
│  ├── MFA for privileged users                               │
│  └── Short-lived credentials for automation                 │
│                                                             │
│  NETWORK                                                    │
│  ├── VPC or virtual network isolation                       │
│  ├── Security groups, firewalls, and routing controls       │
│  ├── Private subnets for sensitive control paths            │
│  └── TLS for external entry points                          │
│                                                             │
│  COMPUTE                                                    │
│  ├── Patched node images and host operating systems         │
│  ├── Encrypted root and data volumes                        │
│  └── Restricted instance metadata access                    │
│                                                             │
│  DATA                                                       │
│  ├── Encryption at rest with managed keys where needed      │
│  ├── Encryption in transit between managed services         │
│  └── Access logging for storage and administrative APIs     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Cloud failures are powerful because cloud identities often sit outside Kubernetes authorization. If an attacker can use an infrastructure credential to create a node, attach a disk, change a firewall, read an object bucket, or modify a managed cluster, Kubernetes RBAC may never get a chance to deny the action. This is why "we locked down the cluster" is incomplete when the cloud account can still create an administrator path around the cluster. The Cloud layer asks whether the foundation is trustworthy enough for the cluster to rely on it.

Managed Kubernetes changes which tasks you perform, not whether the Cloud layer exists. The provider may patch the hosted API server, run etcd, and operate availability zones. You still configure the cloud account, network reachability, workload identity, logging sinks, encryption keys, and many managed cluster options. KCSA scenarios often test this shared-responsibility boundary because learners who over-trust the provider miss customer-owned configuration. A strong answer names the provider-operated part and the customer-operated part instead of saying "managed" as though it ends the analysis.

```text
┌─────────────────────────────────────────────────────────────┐
│              SHARED RESPONSIBILITY MODEL                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MANAGED KUBERNETES (EKS, GKE, AKS, and similar services)   │
│  ├── Provider: Managed control plane operations             │
│  └── You: Workloads, RBAC, policies, identity, networking   │
│                                                             │
│  SELF-MANAGED KUBERNETES                                   │
│  ├── Provider: Underlying compute and physical facilities   │
│  └── You: Control plane, nodes, patches, policies, apps     │
│                                                             │
│  ON-PREMISES                                                │
│  └── You: Physical security through application behavior    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| Cloud component | What can go wrong | Layer-correct mitigation |
|---|---|---|
| Cloud IAM role for automation | A CI job can create clusters, attach administrator policies, or read unrelated storage because its cloud role is too broad. | Split deployment roles, use short-lived credentials, scope permissions to required resources, and log administrative API use. |
| Virtual network and firewall rules | A control plane endpoint, node port, database, or internal service becomes reachable from networks that should never talk to it. | Use private endpoints where appropriate, narrow ingress and egress rules, and review route tables alongside Kubernetes exposure. |
| Managed key service | Sensitive volumes or secret encryption depend on keys that too many operators can administer or disable. | Separate key administration from cluster administration, enable rotation where appropriate, and audit key usage. |
| Instance metadata service | A compromised Pod reaches node metadata and steals infrastructure credentials attached to the node. | Restrict metadata access, prefer workload identity mechanisms, and avoid putting broad cloud permissions on nodes. |

Cloud-layer review should feel concrete, not philosophical. Ask which identities can create or modify clusters, which identities can attach privileged roles to nodes or workloads, which subnets and firewall rules expose cluster-adjacent services, and which logs would prove what happened during an incident. If a workload can call a cloud API, determine whether the permission comes from a node role, a workload identity binding, a static credential, or an external secret provider. The answer changes both the likely attack path and the owner of the durable fix.

> **Active check:** Your team finds a Pod that can read a cloud object bucket even though its Kubernetes service account has no permissions beyond reading ConfigMaps. Which layer should you investigate first, and what evidence would prove whether this is a Cloud identity problem or a Cluster RBAC problem?

A practical example makes the boundary clearer. Suppose a payments namespace has careful RBAC, but every node in the node group carries a cloud role that can read a shared settlement bucket. A compromised Pod may not need Kubernetes Secret access if it can reach metadata, obtain node credentials, and call the storage API directly. Tightening the Kubernetes RoleBinding would still be good hygiene, but it would not remove the data path. The layer-correct fix is to reduce cloud identity scope, prefer workload identity where available, and restrict metadata or egress paths so Pods do not inherit permissions meant for infrastructure.

## Layer 2: Cluster, the Kubernetes Control Boundary

The Cluster layer is where Kubernetes decides who can ask for what, which requests are allowed, where workloads run, how Pods communicate, and how cluster state is protected. This layer includes the API server, etcd, controller-manager, scheduler, kubelet, kube-proxy or its replacement, admission controllers, RBAC, service accounts, audit logs, Pod Security Standards, and NetworkPolicies. It is the layer most learners associate with Kubernetes security, but it is only one layer in the model. Cluster controls are most effective when they assume the application may eventually be compromised and the cloud foundation still needs separate verification.

```text
┌─────────────────────────────────────────────────────────────┐
│              CLUSTER LAYER SECURITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  API SERVER                                                 │
│  ├── TLS for all API communication                          │
│  ├── Strong authentication through OIDC or certificates     │
│  ├── RBAC authorization with least privilege                │
│  └── Audit logging for sensitive operations                 │
│                                                             │
│  ETCD                                                       │
│  ├── Encryption at rest for Secrets where supported         │
│  ├── TLS for peer and client communication                  │
│  └── Restricted network access to datastore endpoints       │
│                                                             │
│  NODES                                                      │
│  ├── Secure kubelet configuration                           │
│  ├── Disabled anonymous and read-only access where relevant │
│  └── Node authorization and NodeRestriction admission       │
│                                                             │
│  WORKLOAD CONTROLS                                          │
│  ├── Pod Security Standards                                 │
│  ├── NetworkPolicies with a default-deny posture            │
│  └── Resource quotas and limit ranges for guardrails        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Cluster-layer controls are powerful because every workload goes through Kubernetes before it runs. A Pod spec can be rejected by admission policy before a risky container starts. A service account can be denied access to Secrets even after the application is compromised. A NetworkPolicy can stop a vulnerable frontend from reaching a database namespace directly. These controls do not make bad code good, but they can prevent a Code-layer bug from becoming a full environment compromise.

The most common Cluster-layer mistake is confusing authentication with authorization. Authentication answers "who are you?" while authorization answers "what are you allowed to do?" A valid user or service account can still be dangerous when bound to broad roles. In exam scenarios, a phrase such as "the request is authenticated" does not mean the cluster is secure; you must inspect the RBAC, admission, and network decisions that follow. This distinction matters even more for service accounts because every Pod commonly has an identity, and that identity may be useful to an attacker after code execution.

| Cluster control | Risk reduced | What it does not solve |
|---|---|---|
| RBAC | Limits what authenticated users and service accounts can do through the Kubernetes API. | It does not stop application-layer injection, unsafe cloud IAM, or traffic between Pods by itself. |
| Admission policy | Rejects risky objects before they are persisted or scheduled, such as privileged Pods or untrusted images. | It does not patch vulnerable dependencies already inside an approved image. |
| NetworkPolicy | Limits Pod-to-Pod and Pod-to-external communication when supported by the network plugin. | It does not replace application authorization or cloud firewall rules. |
| Audit logging | Creates evidence of API activity for detection, investigation, and compliance. | It does not prevent an action unless paired with policy or response automation. |
| etcd encryption | Protects stored Kubernetes Secret data if the datastore or backups are exposed. | It does not stop a Pod with legitimate Secret access from reading the Secret through the API. |

A useful senior habit is to ask, "Which Kubernetes decision point should have stopped this?" If the object should never have been admitted, look at admission policy. If the identity should not have had API access, look at RBAC. If the Pod should not have reached another service, look at NetworkPolicy and the network plugin. If sensitive state was exposed at rest, look at etcd encryption, backup handling, and datastore access. That question keeps the analysis focused on Kubernetes mechanisms instead of drifting into vague advice.

Cluster controls also have a time dimension that is easy to miss. A one-time review of a Pod spec tells you what is running now, but admission policy tells you whether the next deployment can introduce a risk. A one-time RBAC review tells you what a service account can do today, but change control and audit logging tell you whether a future binding quietly expands privilege. A NetworkPolicy in one namespace tells you about that namespace, but platform defaults tell you whether new namespaces start open or start restricted. Mature teams design Cluster-layer controls as repeatable guardrails, not as one-off cleanup tasks.

Before running any command in a real environment, predict what evidence would change your decision. If `auth can-i` says the service account can list Secrets, the issue is Cluster authorization even if the application code is also vulnerable. If a NetworkPolicy exists but the network plugin does not enforce it, the object may create false confidence. If audit logs show a human administrator created a risky RoleBinding during an incident, the repair may involve approval workflow and alerting as much as YAML cleanup. The KCSA expects this kind of evidence-based classification.

## Layer 3: Container, the Runtime Boundary

The Container layer covers what is inside the image and what the runtime allows once the image starts. This includes base images, installed packages, image provenance, vulnerability scanning, signing, the configured user, Linux capabilities, seccomp and AppArmor profiles, filesystem mutability, privileged mode, host namespace sharing, and runtime choices such as containerd, CRI-O, or sandboxed runtimes. It is where "a process in a box" becomes either a useful boundary or a weak suggestion.

```text
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER LAYER SECURITY                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IMAGES                                                     │
│  ├── Use minimal base images where practical                │
│  ├── Scan operating system and language packages            │
│  ├── Sign images and verify provenance                      │
│  └── Use immutable references instead of floating tags      │
│                                                             │
│  RUNTIME                                                    │
│  ├── Run as a non-root user                                 │
│  ├── Use a read-only root filesystem when the app allows it │
│  ├── Drop all Linux capabilities, then add only required    │
│  └── Use seccomp or AppArmor profiles                       │
│                                                             │
│  ISOLATION                                                  │
│  ├── Avoid privileged containers                            │
│  ├── Disable hostPID, hostNetwork, and hostIPC by default   │
│  └── Consider sandboxed runtimes for high-risk workloads    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Container controls matter most after code starts executing. If a vulnerable web framework lets an attacker run commands, a hardened container can limit what those commands can change. Running as non-root may prevent writes to protected paths. A read-only root filesystem can stop simple persistence. Dropping capabilities can prevent network administration, mounting filesystems, or changing kernel-related settings. Seccomp can block dangerous syscalls. None of these controls make the application vulnerability disappear, but they can turn a severe incident into a contained one.

```text
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER ESCAPE PATH                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Misconfigured Container                                    │
│  │                                                          │
│  ├── privileged: true                                       │
│  │   └── Broad access to host devices and kernel surfaces   │
│  │                                                          │
│  ├── hostPID: true                                          │
│  │   └── Visibility into host process identifiers           │
│  │                                                          │
│  ├── hostNetwork: true                                      │
│  │   └── Direct use of the node network namespace           │
│  │                                                          │
│  └── Combined with a runtime or kernel flaw                 │
│      └── Potential path from container compromise to node   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A subtle point is that some controls involve two layers at once. Image signing is a Container-layer concern because it proves something about the image, but enforcing signature verification during admission is a Cluster-layer mechanism. The risk is image provenance; the enforcement point is Kubernetes admission. Good answers on the KCSA often recognize both: the control belongs to one layer for risk classification and another layer for implementation. Avoid arguing over a single label when the better answer is to name the risk and the enforcement point separately.

| Container setting | Safer default | Why the setting matters |
|---|---|---|
| `runAsNonRoot` | Require true when the image supports it. | A compromised process should not automatically have root privileges inside the container. |
| `readOnlyRootFilesystem` | Enable for services that write only to explicit volumes or temporary directories. | Attackers and buggy code have fewer places to persist tools or modify runtime files. |
| `allowPrivilegeEscalation` | Set false unless a tightly reviewed workload requires it. | The process should not gain more privilege than its initial container configuration grants. |
| `capabilities` | Drop all, then add only a documented minimum set. | Linux capabilities split root-like powers into smaller pieces that should not be granted casually. |
| `privileged` | Keep false for ordinary workloads. | Privileged containers weaken isolation and can create a path toward node compromise. |
| `seccompProfile` | Use `RuntimeDefault` as a baseline in Kubernetes 1.35+ unless a workload needs a custom profile. | Seccomp reduces the system call surface available to the process. |

The Container layer is also where supply chain risk becomes visible. A developer may not write vulnerable code directly, but a base image, operating system package, or language dependency can carry known vulnerabilities into production. Scanning is useful, but a scan result is not a boundary. The boundary comes from deciding which findings block release, which images are allowed to run, how quickly patched images are rebuilt, and whether Kubernetes admission enforces the policy consistently. Without a release rule, a vulnerability report is only a document that says a risk exists.

War story reviews often show that container hardening buys time. A team with a writable root filesystem may find attacker tools dropped into standard paths after a remote command execution bug. A team using non-root users, read-only filesystems, narrow writable volumes, dropped capabilities, and runtime-default seccomp may still have a serious Code-layer bug, but the attacker has fewer places to write, fewer privileged operations to perform, and more detectable failures. The practical lesson is not that hardening makes compromise harmless. The practical lesson is that hardening can change the incident from "attacker controls the node path" to "attacker controls one constrained process while responders contain it."

Pause and predict: if you remove `privileged: true` from a workload but leave `hostNetwork: true` and broad egress in place, which risk has changed and which risk remains? The first change reduces access to host devices and kernel surfaces, which is a Container-layer improvement. The remaining network posture still lets the process use the node network namespace and talk broadly, which means Cluster and Cloud egress decisions still need review. This is exactly why partial hardening should be described precisely rather than advertised as "secure."

## Layer 4: Code, the Application Boundary

The Code layer is the part users and attackers most often interact with directly. It includes application logic, dependency versions, authentication flows, authorization checks, input validation, output encoding, secrets handling, session management, error handling, logging behavior, and data access. A cluster can be well configured and still run an application that leaks data because its own authorization logic is wrong. Code is the smallest box in the diagram, but it is often the largest source of direct attacker input.

```text
┌─────────────────────────────────────────────────────────────┐
│              CODE LAYER SECURITY                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SECURE CODING                                              │
│  ├── Validate input at trust boundaries                     │
│  ├── Encode output for the destination context              │
│  ├── Use parameterized queries for database access          │
│  └── Handle errors without leaking sensitive details        │
│                                                             │
│  DEPENDENCIES                                               │
│  ├── Scan direct and transitive dependencies                │
│  ├── Pin versions and update through reviewed changes       │
│  ├── Verify integrity where package ecosystems support it   │
│  └── Remove unused libraries to reduce attack surface       │
│                                                             │
│  SECRETS                                                    │
│  ├── Never hardcode secrets into source or images           │
│  ├── Use Kubernetes Secrets or external secret stores       │
│  ├── Rotate credentials after exposure or staff changes     │
│  └── Prefer short-lived tokens when the platform supports it│
│                                                             │
│  AUTHENTICATION AND AUTHORIZATION                           │
│  ├── Verify identity with strong authentication mechanisms  │
│  ├── Enforce authorization for every sensitive operation    │
│  └── Keep server-side checks independent of client controls │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Code-layer vulnerabilities are easy to underestimate because they do not always look like Kubernetes problems. A broken access check may let one tenant read another tenant's data. A server-side request forgery flaw may let an attacker reach internal endpoints. A vulnerable logging library may execute attacker-controlled input. A hardcoded password may work anywhere the application is deployed. Kubernetes can reduce blast radius, but it cannot infer the business rule your application forgot to enforce. The application owns those rules because only the application understands its users, tenants, transactions, and data model.

The right mental model is not "Code is inside, so it matters less." Code is inside because it depends on every other layer, but it is often the first layer exposed to untrusted input. This is why the 4 Cs model supports both prevention and containment. Prevent code bugs with secure engineering practices; contain successful exploitation with Container, Cluster, and Cloud controls. A mature incident review asks both questions at the same time: why did the application accept the dangerous input, and why did the environment allow the resulting process to reach valuable targets.

| Code risk | Example symptom | Layer-correct response |
|---|---|---|
| Broken authorization | A user can access another tenant's records through a valid API request. | Fix application authorization logic, add tests for tenant boundaries, and monitor suspicious access patterns. |
| Vulnerable dependency | A dependency scanner reports a remotely exploitable library in the running image. | Patch or replace the dependency, rebuild the image, rescan, and redeploy through normal release controls. |
| Secret in source | A repository contains a database password that was also baked into an image. | Rotate the credential, remove it from source history where feasible, move it to a secret store, and rebuild images. |
| Unsafe input handling | A request parameter reaches a shell command or SQL query without safe binding. | Use safe APIs, parameterized queries, input validation, and tests that reproduce the exploit path. |

Code security work has its own version of defense in depth. Input validation narrows what the application accepts, parameterized queries stop entire classes of database injection, server-side authorization prevents client-side trust mistakes, and dependency management reduces known vulnerable components. These practices are not replaced by Kubernetes controls. They are complemented by Kubernetes controls that reduce the damage when one practice fails or a new vulnerability appears before the team can patch it.

Before you classify a Code-layer finding, ask whether the failed rule depends on application meaning. If the rule is "a customer must not read another customer's invoice," Kubernetes cannot infer it. If the rule is "a request parameter must not become a shell command," the application must use safe APIs and tests. If the rule is "the image must not include a vulnerable library," the vulnerable library may be a Code dependency or a Container package depending on where it lives. Good classification starts from the failed boundary, not from the tool that detected the problem.

## How the Layers Interact

A breach at a lower layer can give an attacker leverage over the layers above it, but a breach at an upper layer does not automatically give full control of the lower layers. This direction matters. If a cloud administrator credential is stolen, the attacker may create infrastructure, alter network paths, or modify cluster settings outside Kubernetes. If a single application endpoint is exploited, the attacker still has to fight container isolation, service account permissions, network policy, and cloud egress controls. The 4 Cs model is useful because it describes both the path of trust and the path of containment.

```text
┌─────────────────────────────────────────────────────────────┐
│              BREACH IMPACT CASCADE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLOUD breach (cloud credentials leaked)                    │
│  └── Attacker may be able to:                               │
│      ├── Reach or modify clusters                           │
│      ├── Attach or inspect storage                          │
│      └── Change network and identity boundaries             │
│                                                             │
│  CLUSTER breach (Kubernetes administrator access)           │
│  └── Attacker may be able to:                               │
│      ├── Deploy malicious containers                        │
│      ├── Read Kubernetes Secrets                            │
│      └── Move across namespaces unless constrained          │
│      (cloud infrastructure may still require separate auth) │
│                                                             │
│  CONTAINER breach (runtime escape or weak isolation)        │
│  └── Attacker may be able to:                               │
│      ├── Affect the node or neighboring workloads           │
│      └── Steal files available to the container or node     │
│      (cluster-wide API access still depends on credentials) │
│                                                             │
│  CODE breach (application vulnerability)                    │
│  └── Attacker may be able to:                               │
│      ├── Access application data and in-process secrets     │
│      └── Act as the application until contained             │
│      (other layers should limit privilege and movement)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Defense in depth means each layer assumes the adjacent layer might fail. A Code-layer fix prevents the original bug. A Container-layer control limits what exploited code can do. A Cluster-layer control limits which APIs and network destinations the compromised Pod can reach. A Cloud-layer control limits whether the attacker can leave the cluster, read infrastructure data, or use cloud credentials. The layers are strongest when they are deliberately aligned around the same scenario rather than maintained as separate compliance lists.

The alignment is what separates a security architecture from a pile of tools. If the scenario is "frontend compromise," the Code layer needs validation and authorization, the Container layer needs non-root execution and a narrow filesystem, the Cluster layer needs least-privilege service accounts and egress limits, and the Cloud layer needs scoped identity and observable storage access. A single dashboard may report all of these findings, but the response plan should still name the layer because ownership, urgency, and verification differ.

### Worked Example: Classifying and Containing a Suspicious Pod

A team receives an alert that a frontend Pod is making unexpected outbound connections after a new release. The image was built from a base image that had several critical package findings, the Pod runs as root, the namespace has no NetworkPolicy, and the node role has broad read access to an object bucket through the cloud provider. The team needs to classify the issues and decide what to fix first.

**Solution step 1: Identify the entry signal without assuming the root cause.** The suspicious outbound traffic appears at runtime, but that does not prove the first failure is a Container-layer issue. The attacker may have entered through vulnerable Code, a vulnerable package in the Container image, or a misused credential. The investigation should preserve logs, compare the release diff, inspect dependency findings, and check whether requests reached an application endpoint before the traffic started.

**Solution step 2: Map each concrete finding to the layer it belongs to.** The vulnerable application dependency or unsafe request handler is Code. The vulnerable base image packages and root user are Container. The missing NetworkPolicy is Cluster. The broad node role that can read an object bucket is Cloud.

**Solution step 3: Decide containment before permanent repair.** The fastest containment may be Cluster and Cloud controls: restrict egress from the namespace, remove broad bucket access from the node role, and rotate any credential that the Pod could have read. Then the team can rebuild the image with patched dependencies, run as non-root, and fix the application code path. Containment is not a substitute for repair, but repair without containment gives the attacker more time.

**Solution step 4: Check whether each fix reduces the matching risk.** Adding `runAsNonRoot` helps with Container runtime damage, but it does not stop the Pod from connecting to the bucket if cloud identity remains broad. Adding a NetworkPolicy helps with lateral and outbound traffic, but it does not remove the vulnerable dependency. Rotating a secret helps after exposure, but it does not prevent the next exploit. The final plan should cover all four layers because the incident crossed all four layers.

**Solution step 5: Convert the incident into a layered standard.** After the immediate response, the team should define release gates and platform defaults: dependency updates for Code, image scanning and non-root defaults for Container, default-deny NetworkPolicies and admission policy for Cluster, and narrow workload identity for Cloud. The senior move is turning a one-time fix into a repeated control that catches similar failures earlier.

```text
┌─────────────────────────────────────────────────────────────┐
│              WORKED EXAMPLE MAPPING                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Finding: broad node role can read object bucket             │
│  Layer:   Cloud                                             │
│  Fix:     narrow cloud IAM and prefer workload identity      │
│                                                             │
│  Finding: namespace has no egress NetworkPolicy              │
│  Layer:   Cluster                                           │
│  Fix:     default-deny egress plus explicit service paths    │
│                                                             │
│  Finding: Pod runs as root and image has package findings    │
│  Layer:   Container                                         │
│  Fix:     patched image, non-root user, runtime hardening    │
│                                                             │
│  Finding: application accepted malicious input               │
│  Layer:   Code                                              │
│  Fix:     validate input and add regression tests            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Now you decide:** A different team proposes fixing the same incident only by rebuilding the image with patched packages. Before reading further, decide which risks remain after that fix and which 4 Cs layer owns each remaining risk.

| Proposed fix | Layer directly improved | Risk still remaining if this is the only fix |
|---|---|---|
| Rebuild image with patched packages | Container and possibly Code, depending on whether the vulnerable component is an OS package or application library. | The Pod may still have broad network egress, broad cloud identity, or unsafe application behavior. |
| Add a default-deny egress NetworkPolicy | Cluster | The vulnerable code and root runtime configuration may still be exploitable inside the Pod. |
| Remove broad object bucket access from the node role | Cloud | The application may still be compromised and attempt lateral movement within the cluster. |
| Add server-side input validation and authorization checks | Code | Runtime, cluster, and cloud blast-radius controls still need to limit future unknown vulnerabilities. |

The example also shows why remediation order depends on incident phase. During active containment, you may prioritize egress restrictions and identity reduction because they reduce immediate movement while engineers prepare a patched release. During permanent repair, you must return to the entry point and fix the vulnerable application or dependency. During hardening, you convert the learning into admission policy, namespace defaults, release gates, and cloud identity standards.

## Practical Classification Patterns

Some security items are easy to classify because they live entirely in one layer. VPC firewall rules are Cloud. RBAC is Cluster. `runAsNonRoot` is Container. SQL injection prevention is Code. The harder exam and real-world cases combine a risk, an enforcement point, and an owner, so you need a repeatable classification method instead of a memorized list. Classification is an engineering habit: name the failed boundary, name the system that enforces the control, and name the evidence you would inspect.

Use three questions. First, ask what asset or boundary is at risk. Second, ask which system makes the allow-or-deny decision. Third, ask which team must change the durable control. If all three answers point to the same layer, classification is simple. If they point to different layers, state both the risk layer and the enforcement layer rather than forcing a false choice. This is especially important for platform teams because a single issue may require coordinated changes across application repositories, Kubernetes policy, and cloud infrastructure.

| Scenario clue | Likely layer | Reasoning pattern |
|---|---|---|
| "A cloud role can create load balancers in any project or account." | Cloud | The risk is infrastructure identity and external exposure, even if the load balancer fronts Kubernetes services. |
| "A service account can list Secrets across namespaces." | Cluster | The risk is Kubernetes API authorization through RBAC, not the application code that uses the token. |
| "A Pod is allowed to run with `privileged: true`." | Container and Cluster | The risky runtime state is Container, while admission policy is the Cluster mechanism that should prevent it. |
| "A base image includes a vulnerable OpenSSL package." | Container | The vulnerable component is packaged in the image and travels with the runtime artifact. |
| "A request parameter reaches a database query without binding." | Code | The application constructs unsafe behavior from untrusted input. |
| "A Pod can reach cloud metadata and retrieve node credentials." | Cloud and Cluster | The credential belongs to Cloud identity, while Pod placement and network restrictions are Cluster concerns. |
| "Secrets are stored unencrypted in etcd backups." | Cluster | The Kubernetes datastore and backup handling are part of protecting cluster state. |

For Kubernetes 1.35+ workloads, you should also recognize the difference between policy intent and workload configuration. A Pod spec can request safer settings, but without admission policy another team may submit a riskier spec tomorrow. A namespace can use NetworkPolicy, but only if the cluster networking implementation enforces it. A service account can be narrow today, but automation can bind it to a broad role tomorrow. Mature security checks both the object and the system that controls future objects.

The `kubectl` command is the standard CLI for Kubernetes; after the first full use, many practitioners use the alias `k` for speed. The following commands are not required for the concept, but they show how the model connects to real inspection. They use client-side dry run and local output where possible, so learners can read the object shape even before a full lab environment is available.

```bash
kubectl version --client
alias k=kubectl
k explain pod.spec.securityContext
k explain pod.spec.containers.securityContext
k auth can-i list secrets --as=system:serviceaccount:demo:frontend -n demo
```

Those commands do not magically classify every risk, but they reveal the places where layer decisions become concrete. Security context fields describe Container runtime posture. `kubectl auth can-i` checks Cluster authorization. Neither command tells you whether the cloud IAM role attached to the workload is too broad or whether the application validates tenant access. That separation is the point of the 4 Cs model. Use the command output as evidence for one layer, then deliberately ask what the command did not inspect.

For example, a successful `k auth can-i` denial is good news for Kubernetes API access, but it says nothing about whether the workload has an environment variable containing a cloud token or whether the application can reach an internal metadata endpoint. A `k explain` result can show where `runAsNonRoot` belongs in the schema, but it does not prove the deployed Pod actually uses that setting. A careful debugger writes down the layer each command covers and then chooses the next command to cover a different layer.

## Patterns & Anti-Patterns

The most reliable pattern is foundation-first design with incident-first verification. During design, start with Cloud identity and network boundaries, then define Cluster guardrails, then standardize Container runtime expectations, then verify Code-layer release practices. During verification, start from the symptom and trace outward through every layer that could contain or amplify the incident.

Another proven pattern is to separate risk classification from enforcement mechanism. A risky unsigned image is a Container artifact problem, but Kubernetes admission may be the enforcement point. A broad workload identity is a Cloud risk, but a Cluster egress policy may help limit metadata access. A vulnerable dependency is a Code or Container issue depending on where the component lives, but a release gate may be implemented in CI. Naming both sides helps teams avoid unproductive ownership arguments and produce fixes that actually land.

The third pattern is to turn one incident into reusable defaults. If a review finds a privileged container, do not only patch that Pod; define admission policy or namespace labels that make the risky shape difficult to deploy again. If a service account can list Secrets across namespaces, repair the binding and add review alerts for future broad bindings. If a node role exposes cloud data, move toward scoped workload identity and cloud audit queries that catch unusual reads. The value of the 4 Cs model is not a perfect diagram. The value is a repeatable way to turn failures into controls.

Anti-patterns usually begin with a true statement stretched beyond its evidence. "The image is clean" becomes a claim that the service is secure. "The cluster is private" becomes a claim that workloads cannot exfiltrate data. "The provider manages the control plane" becomes a claim that RBAC and admission are handled. "The app team fixed the bug" becomes a claim that runtime hardening no longer matters. In each case, the first sentence may be true, but the conclusion crosses layers without proof.

Use the following decision habit in reviews: accept the evidence, then limit the conclusion. A clean image scan supports a narrow claim about known image findings at scan time. Tight RBAC supports a narrow claim about Kubernetes API permissions for a specific identity. Private subnets support a narrow claim about network reachability from selected sources. Secure coding tests support a narrow claim about tested application behavior. When a team asks for production approval, require enough narrow claims across all four layers to support the broader risk decision.

## Decision Framework

When you face a 4 Cs question, resist the urge to answer from the tool name alone. Start with the failed boundary, then identify the decision point, then choose a control that changes that decision point. If the finding is "Pod can list Secrets," the decision point is Kubernetes authorization, so Cluster-layer RBAC is central. If the finding is "Pod can read a cloud bucket through node credentials," the decision point is cloud IAM and credential delivery, so Cloud-layer identity is central even though the symptom appears inside a Pod. If the finding is "customer can read another customer's invoice," the decision point is application authorization, so Code-layer logic is central even if the workload runs on Kubernetes.

The next step is to distinguish containment from repair. Containment limits what happens now, while repair removes the entry path or durable misconfiguration. NetworkPolicy can contain a compromised application, but it does not patch the vulnerable library. Patching the library repairs one entry path, but it does not remove a broad service account. Reducing cloud IAM limits data exposure, but it does not fix a broken tenant check. A strong layered response usually includes both: immediate controls that reduce movement and durable controls that remove the weakness.

When choosing between candidate answers on an exam or in a design review, prefer the answer that matches the layer of the described risk and does not claim more than it can prove. If a scenario describes a managed service responsibility boundary, ask what the provider operates and what the customer configures. If a scenario describes a Kubernetes object field, ask whether the field affects runtime behavior, API authorization, or network reachability. If a scenario describes application data rules, assume Kubernetes cannot infer those rules unless the application exposes them through explicit policy.

## Did You Know?

- **The 4 Cs model appears in Kubernetes security guidance** because it gives teams a shared vocabulary for layered controls instead of treating Kubernetes as the only security boundary.
- **Kubernetes Pod Security Standards define three policy levels** named privileged, baseline, and restricted, which helps teams reason about Container-layer risk through Cluster-layer admission.
- **Kubernetes 1.35+ still uses shared responsibility in managed services** because providers may operate control plane components while customers configure workloads, RBAC, admission, namespaces, and network policy.
- **Container hardening is containment, not application repair** because non-root users, read-only filesystems, and seccomp reduce attacker options after code is already executing.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Treating the 4 Cs as four equal checklists instead of a dependency stack. | Teams may spend energy on visible controls while ignoring lower-layer weaknesses that bypass everything above them. | Start with Cloud foundations, then Cluster policy, then Container hardening, then Code controls, while still maintaining all layers. |
| Assuming the cloud provider handles the entire Cluster layer in managed Kubernetes. | Managed services operate parts of the control plane, but customer-owned RBAC, admission, network policy, and workload configuration can still be unsafe. | Read the provider responsibility boundary and document which Kubernetes settings your team must configure and audit. |
| Calling every image-related control "Container" without noticing the enforcement point. | Image scanning, signing, and admission verification can involve both image risk and Kubernetes policy, so oversimplifying hides ownership. | State the risk layer and the enforcement layer when a control spans both, such as Container provenance enforced by Cluster admission. |
| Using RBAC as the answer to network or application authorization problems. | RBAC controls Kubernetes API actions, not whether one Pod can call another service or whether an app user may read a record. | Pair RBAC with NetworkPolicy for traffic paths and application authorization for business actions. |
| Believing non-root containers make vulnerable code safe. | Runtime hardening limits damage, but the application may still leak data, process malicious input, or perform unauthorized actions. | Fix the Code-layer flaw and keep Container controls as blast-radius reduction. |
| Ignoring cloud identity attached to nodes or workloads. | A Pod with little Kubernetes permission may still obtain powerful cloud credentials if identity boundaries are weak. | Prefer scoped workload identity, narrow node roles, metadata restrictions, and cloud audit logging. |
| Fixing the first visible finding and closing the incident too early. | Incidents often cross layers, so a single patch can leave the original movement path or data exposure path open. | Build an incident map that records entry point, failed controls, containment controls, and permanent fixes across all four layers. |

## Quiz

1. **Your team deploys a payment API on a managed Kubernetes service. The Pod uses a patched distroless image and runs as non-root, but its service account can list Secrets in every namespace. During review, someone says the container is hardened, so the risk is low. How should you evaluate that claim using the 4 Cs model?**
   <details>
   <summary>Answer</summary>
   The claim is incomplete because it points to Container-layer controls while the major finding is Cluster-layer authorization. A non-root distroless container reduces runtime damage after compromise, but it does not prevent the workload from using its Kubernetes service account token to list Secrets. The correct recommendation is to keep the Container hardening, narrow RBAC to the minimum namespace and resources needed, and verify with an authorization check such as `kubectl auth can-i` for the affected service account.
   </details>

2. **A developer reports that an application can read a cloud object bucket even though no Kubernetes RoleBinding grants bucket access. The workload runs on a node group with a broad cloud IAM role. Which layer is the likely root problem, and what Cluster-layer control might still help contain it?**
   <details>
   <summary>Answer</summary>
   The likely root problem is Cloud-layer identity because access to the object bucket comes from the cloud IAM role, not Kubernetes RBAC. A Cluster-layer control can still help if it prevents Pods from reaching the metadata endpoint or restricts egress paths, depending on the environment and network plugin. The durable fix is to narrow cloud IAM, prefer scoped workload identity, and ensure Pods cannot inherit broad node credentials unnecessarily.
   </details>

3. **A namespace has default-deny NetworkPolicies, tight RBAC, and encrypted Secrets, but a public endpoint has a broken authorization check that lets one customer read another customer's invoice. Which layer did the incident enter through, and why do the Cluster controls not fully solve it?**
   <details>
   <summary>Answer</summary>
   The incident entered through the Code layer because the application failed to enforce the business authorization rule. Cluster controls are still valuable because they may prevent lateral movement or Secret theft after exploitation, but they cannot know which invoice belongs to which customer. The application must enforce tenant authorization server-side, add regression tests for the rule, and monitor access patterns that suggest abuse.
   </details>

4. **A platform team proposes an admission policy that rejects Pods using unsigned images. Another engineer says image signing is a Container-layer topic and therefore admission policy is irrelevant. How would you resolve the disagreement?**
   <details>
   <summary>Answer</summary>
   Both engineers are seeing part of the picture. Image provenance is a Container-layer risk because it concerns what artifact is allowed to run. Admission policy is a Cluster-layer enforcement mechanism because Kubernetes decides whether to accept the Pod. A strong answer records both: use Cluster admission to enforce Container image trust requirements before workloads are scheduled.
   </details>

5. **After a vulnerability scan, a team rebuilds its image to patch a critical package. The Pod still runs privileged with `hostNetwork: true`, and the namespace allows all egress. What should the team fix next, and why is the patched image not enough?**
   <details>
   <summary>Answer</summary>
   The patched image addresses a Container or dependency risk, but the remaining runtime and Cluster risks still create a large blast radius. The team should remove privileged mode and host networking unless there is a documented exception, apply safer security context defaults, and add NetworkPolicy controls for egress and lateral movement. A patched image reduces one known entry path, but weak isolation and open network paths make future unknown flaws more dangerous. The order should prioritize containment if exploitation is active and durable hardening during the follow-up.
   </details>

6. **A company uses a managed Kubernetes service and assumes the provider encrypts all Kubernetes Secrets in the safest possible way by default. An audit finds etcd backups containing readable Secret values. How should you analyze responsibility and remediation?**
   <details>
   <summary>Answer</summary>
   This is primarily a Cluster-layer state protection issue with a managed-service shared-responsibility angle. The provider may operate the datastore infrastructure, but the customer may need to enable or configure application-layer Secret encryption, key management, and backup handling. Remediation should verify the provider feature set, enable Secret encryption where required, protect backups, restrict access to backup storage, and rotate exposed credentials. The answer should not assume "managed" means the customer has no control or no responsibility.
   </details>

7. **An incident review shows that attackers exploited a vulnerable library, wrote tools into the container filesystem, used the service account to read ConfigMaps in other namespaces, and then sent data to an external endpoint. Build a layered explanation of what failed and what should be improved.**
   <details>
   <summary>Answer</summary>
   The entry was Code because the vulnerable library allowed exploitation. Container controls were weak because the attacker could write tools into the filesystem, so a read-only root filesystem, non-root user, and reduced capabilities should be considered. Cluster controls were weak because the service account had cross-namespace access and egress was open, so RBAC and NetworkPolicy need tightening. Cloud controls should also be checked because external data transfer may involve firewall, NAT, egress gateway, or cloud logging policies that should detect or restrict suspicious outbound traffic.
   </details>

## Hands-On Exercise: Build a 4 Cs Incident Map

**Scenario:** You are reviewing a pre-production Kubernetes service before it is promoted to production. The team gives you the following evidence: the application uses a dependency with a critical remote-code-execution advisory, the image runs as root with a writable root filesystem, the namespace has no NetworkPolicy, the service account can list Secrets across the cluster, and the node group has a cloud IAM role that can read a shared object bucket. Your task is to turn this messy evidence into a layered risk map and a prioritized remediation plan.

### Step 1: Classify each finding by layer

Create a four-row map with Cloud, Cluster, Container, and Code. Put each finding in the row where the risk primarily belongs, and add a short reason. Do not classify by team ownership; classify by the boundary that fails. For example, the broad node IAM role belongs to Cloud even if the Kubernetes team owns the node group configuration.

| Finding | Primary layer | Reason |
|---|---|---|
| Dependency has a critical remote-code-execution advisory. | Code | The vulnerable component is part of the application dependency graph and can be triggered through application behavior. |
| Image runs as root with a writable root filesystem. | Container | The runtime configuration increases what exploited code can change inside the container. |
| Namespace has no NetworkPolicy. | Cluster | Kubernetes network isolation is missing, so a compromised Pod may communicate broadly. |
| Service account can list Secrets across the cluster. | Cluster | The Kubernetes API authorization boundary is too permissive. |
| Node group cloud IAM role can read a shared object bucket. | Cloud | Infrastructure identity may allow data access outside Kubernetes RBAC. |

### Step 2: Identify the likely attack chain

Write the attack chain as a sequence rather than a list of unrelated findings. A strong answer might say: "The attacker enters through the vulnerable dependency, writes tools because the container filesystem is writable and root is available, uses the broad service account to discover cluster data, and may reach the object bucket through the node cloud role." Sequencing matters because it shows which controls prevent entry and which controls reduce movement after entry. It also helps responders decide what to contain immediately while slower application and image fixes are prepared.

### Step 3: Choose immediate containment actions

Pick two or three changes that reduce active risk quickly while the application team prepares a patched release. Good containment actions include narrowing the service account, applying temporary egress restrictions, removing broad cloud object-bucket access from the node role, and blocking risky deployment patterns with admission policy if your platform supports it. Explain why each action matches the layer it changes.

### Step 4: Choose permanent remediation actions

Define durable fixes for all four layers. For Code, patch or replace the dependency and add regression checks. For Container, rebuild the image, run as non-root, set a read-only root filesystem where practical, and drop unnecessary capabilities. For Cluster, apply least-privilege RBAC and namespace NetworkPolicies. For Cloud, move from broad node identity toward scoped workload identity and audit access to the shared bucket. A complete plan should show which fixes prevent this exact incident and which fixes reduce the next unknown incident.

### Step 5: Verify with evidence

Use real checks where your environment supports them. The first command uses the full `kubectl` name; after that, the alias `k` means `kubectl`. Adapt the namespace, service account, and filenames to your lab cluster if you are practicing hands-on.

```bash
kubectl auth can-i list secrets --as=system:serviceaccount:payments:frontend -A
alias k=kubectl
k get networkpolicy -n payments
k get pod -n payments -o jsonpath='{range .items[*]}{.metadata.name}{" runAsNonRoot="}{.spec.securityContext.runAsNonRoot}{"\n"}{end}'
k describe serviceaccount frontend -n payments
```

### Success Criteria

- [ ] You classified every finding into Cloud, Cluster, Container, or Code and wrote a reason based on the failed boundary rather than the owning team.
- [ ] You wrote an attack chain that connects the findings in sequence from likely entry point to possible data access.
- [ ] You selected at least one containment action for Cluster risk and one containment action for Cloud or Container risk.
- [ ] You defined permanent remediation for all four layers, including a Code-layer fix for the vulnerable dependency.
- [ ] You identified at least one proposed fix that would be useful but insufficient by itself, and explained which risk would remain.
- [ ] You used or described verification evidence, such as RBAC checks, NetworkPolicy inspection, workload security context review, or cloud IAM review.

<details>
<summary>One possible solution</summary>

A complete solution classifies the vulnerable dependency as Code, the root writable container as Container, the missing NetworkPolicy and broad service account as Cluster, and the broad node IAM role as Cloud. The likely chain is Code entry through the vulnerable dependency, Container expansion because the attacker can write tools as root, Cluster movement because the service account can list Secrets and the namespace has open traffic, and Cloud data exposure because the node role can read the object bucket.

Immediate containment should narrow the service account, restrict namespace egress, and reduce or remove the cloud bucket permission from the node role while credentials are rotated if exposure is suspected. Permanent remediation should patch the dependency, rebuild and harden the image, enforce least-privilege RBAC, add NetworkPolicies, and move to scoped workload identity. Rebuilding the image alone is insufficient because broad RBAC, open egress, and cloud identity exposure would still let a future compromise spread.
</details>

## Next Module

[Module 1.2: Cloud Provider Security](../module-1.2-cloud-provider-security/) - Deep dive into the Cloud layer, shared responsibility, infrastructure identity, network boundaries, and the foundation that every Kubernetes cluster must trust before Cluster, Container, and Code controls can do their work.

## Sources

- [Kubernetes Documentation: Security Overview](https://kubernetes.io/docs/concepts/security/overview/)
- [Kubernetes Documentation: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes Documentation: Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes Documentation: Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Kubernetes Documentation: Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Kubernetes Documentation: Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Kubernetes Documentation: Configure a Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Kubernetes Documentation: Seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [Kubernetes Documentation: Good Practices for Kubernetes Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [CNCF Cloud Native Security Whitepaper](https://github.com/cncf/tag-security/blob/main/security-whitepaper/v2/CNCF_cloud-native-security-whitepaper-May2022-v2.pdf)
