---
revision_pending: false
title: "Module 1.2: Cloud Provider Security"
slug: k8s/kcsa/part1-cloud-native-security/module-1.2-cloud-provider-security
sidebar:
  order: 3
---

# Module 1.2: Cloud Provider Security

> **Complexity**: `[MEDIUM]` - Foundational knowledge
>
> **Time to Complete**: 45-60 minutes
>
> **Prerequisites**: [Module 1.1: The 4 Cs of Cloud Native Security](../module-1.1-four-cs/)

## Learning Outcomes

After completing this module, you will be able to make provider-aware Kubernetes security decisions, explain the evidence behind those decisions, and defend the tradeoffs in a production review:

1. **Evaluate** the shared responsibility boundary for managed Kubernetes control planes, worker nodes, identities, networks, and data.
2. **Diagnose** cloud IAM and Kubernetes RBAC failures that allow workload identity pivots or over-permissioned cluster access.
3. **Design** cloud network and encryption controls for private API endpoints, subnet placement, pod segmentation, and key management.
4. **Compare** EKS, GKE, and AKS security defaults, then choose compensating controls for production clusters.
5. **Implement** an evidence-based responsibility map and verification workflow using Kubernetes 1.35+ commands with the `k` alias.

---

## Why This Module Matters

The textbook 2019 cloud-IAM case study is documented in [the CKS node-metadata module](../../../cks/part1-cluster-setup/module-1.4-node-metadata/) <!-- incident-xref: capital-one-2019 -->: a workload bug became a cloud identity problem, and a cloud identity problem became a data exposure problem affecting tens of millions of records. The lesson worth carrying into KCSA is not the specific exploit; it is the architecture boundary that the exploit crossed. A workload running inside a cluster is also running inside a cloud account, and that cloud account holds identities, network paths, storage buckets, and privileges that the cluster itself cannot revoke. The breach also led to regulatory action and a widely reported settlement, which is the kind of consequence that turns an abstract architecture boundary into an executive concern.

Kubernetes does not erase that boundary. A managed control plane can remove the operational burden of patching API server binaries, maintaining etcd availability, and hardening physical infrastructure, yet it still leaves your team responsible for who can reach the API endpoint, which pods can talk across namespaces, which cloud roles a service account may assume, and where application data is encrypted. The danger is not that the provider is careless; the danger is that teams mistake a secure service for a secure deployment.

This module teaches cloud provider security as a set of decisions rather than a list of product names. You will evaluate the shared responsibility model, compare managed Kubernetes defaults across AWS, Google Cloud, and Azure, diagnose IAM-to-RBAC gaps, and design network and encryption controls that fit realistic cluster operations. For command examples, this module uses the standard KubeDojo shortcut `alias k=kubectl`; all Kubernetes examples assume Kubernetes 1.35+ unless a provider feature has its own version requirement.

```bash
alias k=kubectl
k version --client=true
```

## The Shared Responsibility Boundary

Cloud security is a partnership, but the word "shared" can be misleading if it sounds like every layer is jointly handled. In practice, each layer has an accountable owner, and the owner changes as the service model becomes more managed. A cloud provider usually owns physical facilities, hardware lifecycle, backbone networking, and the managed control plane service itself, while the customer owns identities, data classification, network exposure choices, workload configuration, and the policies that decide who can do what.

The distinction is often described as security "of" the cloud versus security "in" the cloud. Security of the cloud includes the provider's data centers, racks, hypervisors, and service control plane engineering. Security in the cloud includes your clusters, application images, access policies, encryption choices, and incident response playbooks. The line is simple to say, but it becomes operationally interesting when a Kubernetes pod, a cloud role, a storage bucket, and a public API endpoint all participate in the same failure path.

```text
┌─────────────────────────────────────────────────────────────┐
│              SHARED RESPONSIBILITY MODEL                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "Security OF the cloud" vs "Security IN the cloud"        │
│                                                             │
│  ┌──────────────────────┬────────────────────────────────┐ │
│  │   CLOUD PROVIDER     │         YOU (CUSTOMER)         │ │
│  │   RESPONSIBILITY     │         RESPONSIBILITY         │ │
│  ├──────────────────────┼────────────────────────────────┤ │
│  │                      │                                │ │
│  │  Physical security   │  Data                         │ │
│  │  Hardware            │  Identity & access management  │ │
│  │  Network infra       │  Application configuration    │ │
│  │  Hypervisor          │  Network configuration        │ │
│  │  Compute/storage     │  OS patches (IaaS)            │ │
│  │  Global network      │  Firewall/security groups     │ │
│  │                      │  Encryption choices           │ │
│  │                      │  Client-side data integrity   │ │
│  │                      │                                │ │
│  └──────────────────────┴────────────────────────────────┘ │
│                                                             │
│  The boundary shifts based on service type (IaaS/PaaS)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The practical question is not "who is better at security?" The practical question is "who has the control needed to reduce this risk?" If the API server certificate expires inside a managed control plane, the provider owns that repair. If a cluster admin grants `cluster-admin` to every developer group because onboarding was slow, the provider cannot fix that without taking away the flexibility you bought the service to obtain.

When responsibility shifts, control shifts with it. A self-managed control plane gives your team maximum authority over flags, admission plugins, and network placement, but it also gives your team every patching and availability problem. A managed Kubernetes service hides much of that machinery, which is usually the right tradeoff, but it means security review must move up a layer toward service configuration, identity mappings, network reachability, and workload policy.

```text
┌─────────────────────────────────────────────────────────────┐
│              RESPONSIBILITY BY SERVICE MODEL                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              ON-PREM    IaaS      PaaS      SaaS           │
│              ────────   ────      ────      ────           │
│  Data          YOU      YOU       YOU       YOU            │
│  Application   YOU      YOU       YOU       Provider       │
│  Runtime       YOU      YOU       Provider  Provider       │
│  OS            YOU      YOU       Provider  Provider       │
│  Virtualization YOU     Provider  Provider  Provider       │
│  Hardware      YOU      Provider  Provider  Provider       │
│  Network       YOU      Provider  Provider  Provider       │
│  Physical      YOU      Provider  Provider  Provider       │
│                                                             │
│  More managed = less responsibility, but also less control │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Managed Kubernetes sits between IaaS and a higher-level platform. The provider normally operates the control plane, but you still decide whether that control plane endpoint is public, which identities authenticate to it, and which Kubernetes RBAC bindings authorize actions after authentication. That is why a cluster can be "managed" and still fail an audit because too many humans have admin access, node pools are reachable from public subnets, or pods can obtain broad cloud permissions through an overpowered node role.

Pause and predict: if your company moves from self-managed Kubernetes to EKS, which security tasks can you stop owning immediately, and which new review tasks appear because you now depend on AWS IAM and EKS service configuration? A strong answer separates control plane operations from customer policy decisions. It also notices that the team may trade direct patching work for deeper provider configuration review.

A useful review technique is to write every control as an owner-action-evidence statement. "Provider patches the API server" is incomplete because it does not tell you how your team verifies the managed service version. "Customer restricts API server access to corporate networks and private automation runners" is better because it names the owner, the control, and the evidence you can collect. This mindset turns shared responsibility from a poster into an audit-ready operating model.

For a KCSA learner, this is the point where cloud security becomes testable rather than philosophical. A cluster review should be able to answer whether the provider, platform team, application team, or security team owns each control, and it should name the artifact that proves the control exists. If nobody can produce evidence for an owner-action statement, the control may exist only as an assumption.

```bash
k auth can-i get pods --all-namespaces
k auth can-i create clusterrolebindings
k get namespaces
```

Those commands do not prove your cloud account is secure, but they establish the Kubernetes half of the boundary. If a human identity can create cluster role bindings, that identity can often turn a narrow mistake into full cluster control. The matching cloud-side review should ask whether the same human can also create IAM roles, attach broad policies, modify private endpoint settings, or read production storage. Cloud provider security becomes much clearer when you inspect the chain instead of treating each layer as a separate checklist.

## Managed Kubernetes Provider Defaults

Managed Kubernetes services reduce undifferentiated operational work, yet their defaults are not identical. Amazon EKS, Google Kubernetes Engine, and Azure Kubernetes Service all provide managed control planes, but they integrate with different identity systems, node operating systems, networking models, policy add-ons, and private cluster options. A good security engineer does not memorize defaults as trivia; they compare defaults so they can decide which controls must be explicitly enabled before production workloads arrive.

The provider-managed part of Kubernetes is valuable because control plane maintenance is hard to do well. API servers need secure patching, highly available front ends, certificate lifecycle management, and safe integration with etcd. Controller managers and schedulers need version compatibility with the cluster. Etcd needs durability and backup discipline. A mature managed service hides most of that complexity, which lets your team focus on the parts that are still yours.

```text
┌─────────────────────────────────────────────────────────────┐
│              MANAGED KUBERNETES - PROVIDER SCOPE            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTROL PLANE                                              │
│  ├── API server availability and patching                  │
│  ├── etcd availability and backups                         │
│  ├── Controller manager                                    │
│  ├── Scheduler                                             │
│  └── Control plane network security                        │
│                                                             │
│  INFRASTRUCTURE                                             │
│  ├── Physical security of data centers                     │
│  ├── Network backbone                                      │
│  ├── Hardware maintenance                                  │
│  └── Hypervisor security                                   │
│                                                             │
│  COMPLIANCE                                                 │
│  ├── SOC 2 Type II                                         │
│  ├── ISO 27001                                             │
│  └── Various regulatory certifications                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The customer-managed side is where most Kubernetes incidents become specific. RBAC tells the API server what an authenticated identity may do. Network policies decide whether one compromised pod can laterally scan another namespace. Pod Security Standards shape what workloads can ask from the node kernel. Admission controllers, image policy, secret handling, logging, and backup choices all remain customer decisions. The provider supplies secure building blocks, but it does not know your data sensitivity, team structure, or incident tolerance.

```text
┌─────────────────────────────────────────────────────────────┐
│              MANAGED KUBERNETES - YOUR SCOPE                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLUSTER CONFIGURATION                                      │
│  ├── RBAC policies                                         │
│  ├── Network policies                                      │
│  ├── Pod Security Standards                                │
│  ├── Admission controllers                                 │
│  └── Audit policy configuration                            │
│                                                             │
│  WORKLOADS                                                  │
│  ├── Container images                                      │
│  ├── Pod security contexts                                 │
│  ├── Application configuration                             │
│  └── Secrets management                                    │
│                                                             │
│  WORKER NODES (varies by provider)                         │
│  ├── Node OS security                                      │
│  ├── Node group configuration                              │
│  └── Node patching (often automated)                       │
│                                                             │
│  DATA                                                       │
│  ├── Your application data                                 │
│  ├── Encryption key management                             │
│  └── Backup and recovery                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The most common provider-default surprise is API server reachability. A public endpoint does not mean unauthenticated access is allowed, but it does mean the endpoint is reachable from the internet and becomes part of your external attack surface. A private endpoint reduces exposure, although it adds operational requirements for VPNs, bastion hosts, private CI runners, and emergency access procedures. The right decision depends on the environment, but production clusters usually deserve a documented reason before accepting broad public reachability.

| Security Feature | Amazon EKS | Google GKE | Azure AKS |
|------------------|------------|------------|-----------|
| **API Server Endpoint** | Public by default (can be restricted) | Public by default (Private clusters recommended) | Public by default (Private clusters available) |
| **Node OS** | Amazon Linux 2 / Bottlerocket | Container-Optimized OS (COS) | Ubuntu / Azure Linux |
| **Workload Identity** | IAM Roles for Service Accounts (IRSA/Pod Identity) | Workload Identity (enabled by default on Autopilot) | Microsoft Entra Workload ID |
| **Network Policies** | Requires add-on (e.g., Calico or VPC CNI) | Dataplane V2 (Cilium) built-in | Azure Network Policies or Calico |

That table is a starting point, not a verdict. EKS gives strong integration with AWS IAM, but the team must choose endpoint settings, node role scope, add-ons, and workload identity design. GKE offers strong managed defaults, especially in Autopilot, yet teams still need to review authorized networks, service accounts, and policy posture. AKS integrates naturally with Microsoft Entra ID and Azure networking, but production readiness still depends on private cluster decisions, node pool controls, workload identity, and policy enforcement.

Pause and predict: if you provision a default cluster on your chosen provider without specifying security parameters, which critical boundaries might remain public, permissive, or undefined? Good candidates include API server endpoint exposure, workload-to-cloud identity mapping, network policy enforcement, node metadata access, logging coverage, and encryption key ownership. If your answer only mentions Kubernetes manifests, widen the review to include cloud service configuration.

Provider defaults also change over time, so security baselines should be expressed as desired properties rather than assumptions about a console wizard. "The API server must be private or restricted to approved CIDR ranges" is more durable than "the default endpoint setting is acceptable." "Every production workload must use workload identity rather than static cloud keys" is more durable than "we followed the sample application." A baseline written this way survives provider UI changes and cluster version upgrades.

A realistic war story looks like this: a platform team creates a dev cluster quickly, leaves the public API endpoint enabled, and maps an operations IAM role to cluster admin for convenience. Months later, automation starts deploying sensitive test data into the same cluster because the cluster "already exists." Nothing dramatic changed in Kubernetes, but the risk changed because the cluster's purpose changed. The review failure was not one bad field; it was the absence of a lifecycle checkpoint when a low-trust environment became a higher-trust environment.

Provider defaults should therefore be reviewed at creation time and again when the cluster's purpose changes. New data classes, new tenants, new automation paths, and new compliance obligations can all invalidate an earlier decision. A default that was acceptable for a disposable sandbox may become unacceptable when the same cluster starts receiving production-like data, so the baseline must travel with the workload rather than remain frozen at cluster creation.

Another useful habit is to capture "default plus decision" in infrastructure code. If a public endpoint is temporarily allowed, the configuration should explain the approved CIDR ranges and the planned expiration. If network policy enforcement depends on a provider add-on, the add-on should be installed and tested before workloads depend on it. The goal is not to distrust the provider defaults, but to make every accepted default visible enough that a future reviewer can tell whether it was intentional.

## Cloud IAM, Kubernetes RBAC, and Workload Identity

Identity is where cloud provider security and Kubernetes security meet. Cloud IAM decides which human, service, or workload can call provider APIs. Kubernetes authentication decides who reaches the API server, and RBAC decides what that identity may do after reaching it. Workload identity connects a Kubernetes ServiceAccount to a cloud identity so a pod can call storage, messaging, database, or key management APIs without carrying long-lived static credentials.

IAM policies are built from principals, actions, resources, and conditions. That sounds formal, but it mirrors everyday access decisions. A principal is the person or machine asking for access. An action is the operation they want to perform. A resource is the target. A condition narrows the situation, such as source network, time, tag, MFA state, service account, namespace, or audience claim. Least privilege means all four parts are as specific as the workload can tolerate.

```text
┌─────────────────────────────────────────────────────────────┐
│              IAM CORE CONCEPTS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRINCIPAL         WHO is requesting access?               │
│  ├── Users         Human identities                        │
│  ├── Groups        Collections of users                    │
│  ├── Roles         Assumable identities                    │
│  └── Service Accts Machine identities                      │
│                                                             │
│  ACTION            WHAT are they trying to do?             │
│  ├── Read          Get, List, Describe                     │
│  ├── Write         Create, Update, Delete                  │
│  └── Admin         Full control, IAM changes               │
│                                                             │
│  RESOURCE          WHICH resource is involved?             │
│  ├── Specific      arn:aws:s3:::my-bucket/file.txt        │
│  ├── Pattern       arn:aws:s3:::my-bucket/*               │
│  └── All           * (dangerous!)                          │
│                                                             │
│  CONDITION         UNDER WHAT circumstances?               │
│  ├── Time-based    Only during business hours             │
│  ├── IP-based      Only from corporate network            │
│  └── MFA-required  Only with second factor                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Kubernetes adds a second authorization layer, and the order matters. A human might authenticate to AWS, Google Cloud, or Azure first, then receive a token that the managed Kubernetes API server accepts. After that, Kubernetes RBAC decides whether the user can list secrets, create deployments, or modify role bindings. Cloud IAM can open the front door, but RBAC decides which rooms the visitor may enter once inside the building.

```text
┌─────────────────────────────────────────────────────────────┐
│              IAM + KUBERNETES INTEGRATION                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CLUSTER ACCESS                                          │
│     Cloud IAM controls who can access the cluster          │
│                                                             │
│     User → Cloud IAM → API Server → Kubernetes RBAC        │
│                                                             │
│     Example (AWS EKS):                                      │
│     - IAM user/role authenticates to AWS                   │
│     - aws-auth ConfigMap maps IAM to K8s groups            │
│     - RBAC authorizes actions in cluster                   │
│                                                             │
│  2. WORKLOAD IDENTITY                                       │
│     Pods can assume cloud IAM roles                        │
│                                                             │
│     Pod → ServiceAccount → Cloud IAM Role → AWS API        │
│                                                             │
│     Example (GKE Workload Identity):                        │
│     - K8s ServiceAccount annotated with GCP SA             │
│     - Pod automatically gets GCP credentials               │
│     - No static credentials needed                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The most dangerous IAM mistake in Kubernetes is giving a node role broad permissions and then letting every pod inherit the node's cloud identity. That pattern was common before workload identity matured, because it was easy to attach one storage policy to a node group and call the application done. It also meant a small application compromise could become a cloud account compromise if the attacker reached the instance metadata service or abused a library that could request credentials.

To understand why workload identity is critical, consider an IAM pivot attack. An attacker exploits a Server-Side Request Forgery vulnerability in a web application pod. The pod runs on a worker node whose instance profile has broad object storage access because several teams share the same node group. The attacker reaches the metadata service, obtains short-lived credentials for the node role, and then uses those credentials outside the cluster to read unrelated buckets. The original flaw was in one application, but the blast radius was defined by cloud IAM.

Workload identity changes the shape of that failure. Instead of letting the pod borrow the node role, the platform maps a Kubernetes ServiceAccount to a narrowly scoped cloud role. The application gets short-lived credentials for that role when it runs, and the policy can limit access to one bucket, one key prefix, or one queue. If the pod is compromised, the attacker still has a problem, but the problem is bounded by the workload's intended permission set rather than the node group's shared permission set.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: invoice-reader
  namespace: payments
  annotations:
    example.com/cloud-role: payments-invoice-readonly
```

That manifest is intentionally provider-neutral because each cloud implements the binding differently. EKS can use IAM Roles for Service Accounts or EKS Pod Identity. GKE uses Workload Identity Federation for GKE. AKS uses Microsoft Entra Workload ID. The important design property is the same across all three: a pod should obtain short-lived credentials through a trusted identity exchange, not through a static key copied into a Kubernetes Secret.

| Static Credentials | Workload Identity |
|-------------------|-------------------|
| Long-lived secrets | Short-lived tokens |
| Stored in cluster | Automatically rotated |
| Same creds for all pods | Per-pod identity |
| Manual rotation | Provider-managed |
| Risk of exposure | Minimal blast radius |

Static credentials are sometimes defended as "simple," but their simplicity is deceptive. A key stored as a Secret can be read by any identity with the right RBAC permission, copied into backups, printed by debugging tools, or left behind after a team changes ownership. Rotation requires coordination between the cloud account, the Kubernetes Secret, deployment rollout, and incident response records. Workload identity has complexity too, but it moves that complexity into an auditable provider integration instead of spreading long-lived keys across cluster state.

Before running this, what output do you expect if your current identity can read pods but cannot view Secret values? The first command may succeed while the second returns a forbidden response, and that difference is exactly what RBAC should express. If both commands succeed for a broad developer role in production, the finding is not merely "too much access"; it is a cloud provider security issue because those Secret values may include credentials that reach outside the cluster.

```bash
k auth can-i get pods -n payments
k auth can-i get secrets -n payments
k auth can-i create rolebindings -n payments
```

Human cluster access deserves the same chain-of-trust review as workload access. In EKS, an AWS IAM principal can be mapped into Kubernetes groups. In GKE, Google identities can authenticate to the cluster and then depend on Kubernetes RBAC. In AKS, Microsoft Entra identities can integrate with Kubernetes authorization. The exact product names differ, but the failure pattern is consistent: cloud identity grants entry, Kubernetes RBAC grants authority, and weak separation between the two creates escalation paths.

A strong diagnostic habit is to ask three questions for every identity path. First, can this principal authenticate to the cluster endpoint from its network location? Second, after authentication, which Kubernetes verbs and resources can it use? Third, can it create or modify cloud IAM objects that would make its Kubernetes access more powerful? That third question is easy to miss, yet it is where many real escalations live.

The same three-question model works for automation. A CI/CD runner may need deployment rights in one namespace, but it rarely needs to create cluster-wide role bindings, change node pools, or attach IAM policies. If the runner also has broad cloud permissions, a compromised pipeline token can become more serious than a compromised developer laptop. Treat automation identities as production users with different ergonomics, not as harmless service plumbing.

Workload identity reviews should include lifecycle cleanup. When an application is retired, its Kubernetes ServiceAccount, cloud role, policy attachments, and audit expectations should be retired together. Orphaned roles are dangerous because nobody feels responsible for them, yet they may still trust a cluster issuer or namespace pattern. A mature platform makes identity ownership part of application ownership so cloud access does not outlive the workload it was meant to support.

## Cloud Network, Encryption, and Multi-Tenancy Controls

Network security in cloud Kubernetes starts before a packet reaches a pod. The VPC or virtual network defines address space and routing boundaries. Subnets decide which resources are internet-facing and which remain private. Security groups, firewall rules, network security groups, and network ACLs constrain traffic near instances and interfaces. Kubernetes NetworkPolicy then adds workload-aware controls inside the cluster, usually by label, namespace, and port.

```text
┌─────────────────────────────────────────────────────────────┐
│              CLOUD NETWORK SECURITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VPC (Virtual Private Cloud)                               │
│  ├── Isolated network space                                │
│  ├── Your own IP address range                             │
│  └── Foundation for other network controls                 │
│                                                             │
│  SUBNETS                                                    │
│  ├── Public subnets  → Internet-facing resources           │
│  ├── Private subnets → Internal resources                  │
│  └── Control plane   → Often in provider-managed subnet    │
│                                                             │
│  SECURITY GROUPS                                            │
│  ├── Stateful firewalls                                    │
│  ├── Allow rules only (implicit deny)                      │
│  └── Applied to instances/ENIs                             │
│                                                             │
│  NETWORK ACLs                                               │
│  ├── Stateless firewalls                                   │
│  ├── Allow and deny rules                                  │
│  └── Applied to subnets                                    │
│                                                             │
│  Best Practice: Private subnets for worker nodes,          │
│  public only for load balancers if needed                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A private worker node subnet is not automatically a private application. A public load balancer can still forward traffic to those nodes, and egress rules may still allow compromised workloads to reach the internet. Likewise, a public API endpoint is not automatically a breach, because authentication still applies, but it increases the number of systems that can attempt authentication and exploit future vulnerabilities. Good network design layers reachability controls so one mistake does not provide the full path.

Kubernetes NetworkPolicy is a cluster-layer control, not a replacement for cloud networking. Cloud firewalls are usually better for coarse boundaries such as "only VPN ranges can reach the API endpoint" or "only load balancers can reach node ports." NetworkPolicy is better for workload boundaries such as "only the frontend namespace can call the checkout service" or "only the backup job can reach the database service." The two controls are complementary because they operate at different levels of abstraction.

Which approach would you choose here and why: restrict a production API server to private networking, restrict it to approved public CIDR ranges, or leave it public with strong identity controls? A private endpoint is usually strongest for production, but it requires reliable private operations paths. CIDR restriction can be a pragmatic intermediate step for distributed teams. A fully public endpoint may be defensible for temporary labs, but it should be treated as an explicit risk acceptance rather than an unnoticed default.

Encryption has the same layered character. TLS protects API server traffic and most node-to-control-plane communication. Storage encryption protects disks, snapshots, object stores, and managed databases. Kubernetes secret encryption protects Secret objects at rest in etcd, but it does not stop a user with `get secrets` permission from reading decrypted values through the API server. Key management then decides who can use, rotate, audit, disable, and recover the keys that protect those layers.

```text
┌─────────────────────────────────────────────────────────────┐
│              ENCRYPTION LAYERS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENCRYPTION IN TRANSIT                                      │
│  ├── TLS for API server communication                      │
│  ├── TLS between nodes and control plane                   │
│  ├── TLS for etcd peer communication                       │
│  └── Service mesh for pod-to-pod encryption                │
│                                                             │
│  ENCRYPTION AT REST                                         │
│  ├── EBS/disk encryption (provider-managed keys)           │
│  ├── etcd encryption (Kubernetes secrets)                  │
│  ├── Object storage encryption (S3, GCS)                   │
│  └── Customer-managed keys (CMK) for more control          │
│                                                             │
│  KEY MANAGEMENT                                             │
│  ├── Cloud KMS for key storage                             │
│  ├── Envelope encryption pattern                           │
│  ├── Key rotation policies                                 │
│  └── Audit logging of key usage                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Customer-managed keys provide more control, but they also create operational responsibility. If a key is disabled accidentally, workloads can fail to read data. If key administrators are too broad, encryption becomes a checkbox rather than a boundary. If audit logs are not retained, the team cannot answer who used a sensitive key during an incident. The decision is not "provider-managed keys are bad" or "customer-managed keys are always better"; the decision is whether the organization can operate the additional control responsibly.

Multi-tenancy forces these decisions into sharper focus. Namespaces are useful for organization, quotas, RBAC scoping, and many application boundaries, but they are not the same as separate clusters or separate cloud accounts. Multiple tenants in one cluster share a control plane, many admission policies, logging systems, node pools, and often the same cloud network. Stronger isolation usually costs more money and operational effort, yet it may be required when tenants represent different customers, regulatory scopes, or blast-radius expectations.

```text
┌─────────────────────────────────────────────────────────────┐
│              MULTI-TENANCY ISOLATION LEVELS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STRONGEST: Separate Cloud Accounts                        │
│  ├── Complete blast radius isolation                       │
│  ├── Separate IAM boundaries                               │
│  ├── Independent billing                                   │
│  └── Use for: Production vs non-prod, different customers  │
│                                                             │
│  STRONG: Separate Clusters                                  │
│  ├── Cluster-level isolation                               │
│  ├── Separate RBAC                                         │
│  ├── No shared control plane                               │
│  └── Use for: Different security levels, teams             │
│                                                             │
│  MODERATE: Namespace Isolation                              │
│  ├── RBAC per namespace                                    │
│  ├── Network policies between namespaces                   │
│  ├── Resource quotas                                       │
│  └── Use for: Different applications, environments         │
│                                                             │
│  WEAK: Same Namespace (not recommended)                     │
│  └── No isolation between workloads                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A practical isolation decision starts with trust, not tooling. If two workloads are owned by the same team, handle the same data class, and fail under the same incident commander, namespace isolation with strong policies may be enough. If two workloads represent different customers, different regulatory scopes, or different administrative teams, separate clusters or separate cloud accounts become easier to justify. Security isolation is not free, so the architecture should match the risk rather than chasing the strongest possible boundary everywhere.

The failure pattern to watch is shared infrastructure becoming a hidden dependency between teams that believe they are isolated. One team changes a node security group, another team loses service connectivity, and a third team discovers that its debug pod can still reach both namespaces. Nothing in that story requires a zero-day. It only requires the organization to treat cloud network, Kubernetes policy, and tenancy design as separate decisions when they are actually one security boundary.

Network and tenancy reviews should also include egress, because many teams focus only on inbound exposure. A compromised pod that cannot receive internet traffic may still send data to arbitrary destinations if outbound rules are open. Restricting egress is operationally harder than restricting ingress because applications often call package registries, telemetry endpoints, cloud APIs, and partner services, but the difficulty does not remove the risk. Production designs should at least know which egress paths are expected and which logs would show unexpected ones.

For encryption, practice explaining exactly what each layer protects against. Disk encryption helps with lost media, snapshots, and provider storage paths. Secret encryption helps with etcd storage exposure. TLS helps with traffic interception. KMS audit logs help with forensic questions about key use. None of those controls proves that an over-permissioned pod cannot read data through an authorized API, so encryption findings should always be paired with identity findings.

## Evidence-Based Verification Workflow

Cloud provider security reviews can become vague if they rely on dashboard impressions. A better workflow gathers evidence in layers: cluster access, Kubernetes authorization, workload identity, network reachability, encryption posture, and tenancy boundaries. Each layer should produce an artifact that another engineer can inspect later. The artifact might be a command output, a provider configuration export, a policy document, or a ticket linking a risk acceptance to a compensating control.

Start with the Kubernetes side because it is fast and teaches you how identities behave once they reach the API server. The `k auth can-i` command is not a complete audit, but it is a good first probe for privilege. If a developer role can create pods in production, check whether it can mount service account tokens or read secrets. If an automation role can patch deployments, check whether it can also update role bindings. The goal is to identify escalation edges, not merely list permissions.

```bash
k auth can-i list secrets -n payments
k auth can-i create pods -n payments
k auth can-i patch rolebindings.rbac.authorization.k8s.io -n payments
k get serviceaccounts -n payments
```

Next, connect each Kubernetes ServiceAccount to its cloud identity story. A service account with no workload identity binding may still run safely if the workload never calls cloud APIs. A service account with a broad binding needs review even if the pod specification looks hardened. The cloud role should name the workload purpose, scope resources narrowly, and include conditions when the provider supports them. A reviewer should be able to explain why that role exists without reading the application code from scratch.

Then inspect network evidence from both sides. From Kubernetes, list NetworkPolicy objects and confirm that the plugin actually enforces them for the cluster type. From the cloud provider, inspect subnets, route tables, security groups, firewall rules, and API endpoint access settings. A cluster with perfect NetworkPolicy objects can still be exposed through an overly broad load balancer rule, and a cluster with private subnets can still have unrestricted egress that makes data exfiltration easy after a compromise.

Encryption evidence should also distinguish configuration from access. It is useful to know that etcd encryption or secret encryption is enabled, but the next question is who can read the decrypted data through the API server. It is useful to know that disks use encrypted volumes, but the next question is who can create snapshots, share images, or use the keys. Security controls protect against specific paths; they are not magic labels that make the data safe in every state.

Finally, turn the evidence into a responsibility map. The map should list provider-owned controls, customer-owned controls, shared dependencies, evidence sources, and review frequency. It should also identify any compensating controls that make a less-than-ideal default acceptable. For example, a public API endpoint restricted to a corporate CIDR range and protected by strong identity may be acceptable for a temporary staging cluster, while the same setting might be unacceptable for production payment workloads.

An evidence bundle does not need to be elaborate to be useful. A small markdown file in the service repository can capture command outputs, provider setting screenshots or exports, links to infrastructure code, and the date of review. What matters is that the evidence is reproducible and connected to named controls. If a reviewer cannot rerun the command or find the cloud setting later, the bundle becomes a memory aid rather than an assurance artifact.

The workflow should also distinguish steady-state evidence from incident evidence. Steady-state evidence proves that the intended controls exist before an incident. Incident evidence helps responders determine what happened after a control failed or was bypassed. API audit logs, cloud IAM logs, KMS logs, load balancer logs, and Kubernetes events all answer different questions. A production cluster should not wait for an incident to discover that one of those records was never enabled.

## Patterns & Anti-Patterns

Patterns and anti-patterns help teams move from isolated findings to repeatable engineering choices. A pattern is not a universal rule; it is a design that tends to work when the assumptions match. An anti-pattern is not a moral failure; it is a shortcut that often begins as convenience and later becomes an incident path. Cloud provider security improves when teams name both, because named patterns are easier to review and teach.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---|---|---|---|
| Private or restricted API server endpoints | Production clusters, regulated workloads, and high-trust environments | Reduces internet reachability before authentication is even tested | Requires private CI runners, VPN access, break-glass procedures, and monitoring paths |
| Workload identity per application role | Any pod that calls cloud APIs such as storage, queues, KMS, or databases | Replaces static secrets and broad node roles with short-lived scoped credentials | Needs naming standards, policy review, and lifecycle cleanup when apps are retired |
| Separate cloud accounts for strong tenancy | Different customers, different regulatory scopes, or production versus non-production | Creates a hard IAM and billing boundary outside the Kubernetes control plane | Increases provisioning, networking, logging, and cost-management complexity |
| Evidence-based access reviews | Quarterly reviews, production readiness checks, and incident follow-up | Ties permissions to command output and provider configuration instead of memory | Requires automation so evidence collection does not become manual theater |

The first anti-pattern is assuming "managed" means "secured." Teams fall into it because the provider genuinely does handle difficult work, and that success can hide the remaining customer responsibilities. The better alternative is to keep a responsibility map beside the cluster baseline. If a control is provider-owned, document how you verify the provider setting. If a control is customer-owned, document the exact configuration and evidence source.

The second anti-pattern is using one broad node role for every pod. Teams fall into it because it works quickly and avoids learning workload identity on the first deployment. The better alternative is to map each application ServiceAccount to a narrowly scoped cloud role and block or limit metadata access where the provider recommends it. This reduces the blast radius when one pod is compromised.

The third anti-pattern is treating namespace boundaries as customer boundaries. Teams fall into it because namespaces are cheap, familiar, and easy to automate. The better alternative is to choose isolation based on trust and impact. Namespaces are helpful for team separation, but separate clusters or cloud accounts are stronger when tenants represent different customers, administrators, or regulatory obligations.

The fourth anti-pattern is enabling encryption without reviewing access to decrypted data. Teams fall into it because encryption settings are visible in dashboards and satisfy many checklist items. The better alternative is to pair encryption-at-rest evidence with RBAC, key administration, snapshot permissions, and audit log review. Encryption protects storage states, while authorization controls live access.

The fifth anti-pattern is copying a provider tutorial into production without translating the assumptions. Tutorials optimize for a quick success path, which often means public endpoints, broad temporary permissions, simplified networking, or sample namespaces. Those choices are useful for learning but dangerous when they become permanent. The better pattern is to treat tutorials as syntax references and run every copied decision through the production responsibility map before it reaches a shared environment.

## Decision Framework

Use this framework when you are designing or reviewing a managed Kubernetes environment. It intentionally starts with data and tenancy because those factors determine how much isolation is justified. It then moves through control plane reachability, identity, network segmentation, encryption, and evidence. If a team begins with provider preference before answering these questions, the result often looks secure in one console and weak in the actual failure path.

| Decision | Low-Risk Development Choice | Production Default | Strong Isolation Choice |
|---|---|---|---|
| Control plane endpoint | Public endpoint restricted to trusted CIDR ranges | Private endpoint or tightly restricted public endpoint | Private endpoint reachable only from controlled networks |
| Workload cloud access | No cloud permissions or tightly scoped sandbox role | Workload identity per application ServiceAccount | Separate cloud accounts and workload identity per tenant |
| Worker node placement | Private subnet when practical | Private subnet with controlled egress | Dedicated node pools in separate accounts or clusters |
| Pod-to-pod traffic | Namespace defaults plus selective policies | Default-deny NetworkPolicy with explicit allows | Separate clusters plus network policy inside each cluster |
| Secret and data encryption | Provider-managed encryption for non-sensitive data | Secret encryption and reviewed key access | Customer-managed keys with strict admin separation and audit |
| Evidence | Manual checklist for temporary clusters | Automated evidence bundle per release or quarter | Continuous configuration monitoring and independent review |

Read the table from left to right only after you know the business risk. A demo cluster with synthetic data does not need the same isolation cost as a payment platform, and a payment platform should not inherit demo-cluster defaults because they were convenient. The best decision is the one that makes the expected failure small enough for the environment. That is a more useful standard than simply choosing the most expensive control.

A quick decision flow is useful during design reviews. If workloads contain regulated or customer-separated data, start by considering separate accounts or clusters. If the workloads call cloud APIs, require workload identity and reject static cloud keys. If humans or automation need API server access from outside the cloud network, require a documented access path. If any Secret or key protects production data, review both encryption settings and read permissions. If evidence cannot be collected, the control is not ready for production.

This framework also helps compare EKS, GKE, and AKS without arguing over brands. Ask how each provider implements the required property, then review the operational cost of that implementation. EKS might fit a team already mature in AWS IAM. GKE Autopilot may reduce node-management burden for teams that accept its constraints. AKS may fit organizations standardized on Microsoft Entra ID and Azure networking. The secure answer is provider-specific, but the evaluation criteria are portable.

When two options both satisfy the baseline, choose the one your team can operate consistently. A theoretically stronger design can become weaker in practice if only one engineer understands it, if emergency access is unclear, or if evidence collection is manual and often skipped. Security architecture is not only the control selected on paper; it is also the team's ability to maintain, test, and explain that control during routine change and stressful incidents.

The final decision should leave an audit trail that future teams can understand. Record the selected provider feature, the rejected alternatives, the reason for the choice, the evidence that proves it is configured, and the next review date. This small habit prevents the common problem where a cluster inherits a setting nobody remembers choosing. It also gives incident responders context when they need to decide whether a finding is expected behavior or a drifted control.

## Did You Know?

- **85% of cloud breaches** involve human error according to several industry summaries, and the recurring pattern is usually misconfigured access or exposed storage rather than a cinematic exploit chain.

- **Workload Identity** eliminates the need for static cloud credentials in many pod designs. GKE Workload Identity, EKS IAM Roles for Service Accounts or Pod Identity, and AKS Workload Identity all implement this pattern with provider-specific details.

- **The shared responsibility model** was popularized by AWS and is now standard across major cloud providers, but each service shifts the boundary differently because IaaS, PaaS, SaaS, and managed Kubernetes expose different controls.

- **Private clusters** are increasingly normal for production Kubernetes because a private API endpoint removes broad internet reachability, but they also require planned access for operators, CI/CD, monitoring, and emergency response.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Assuming the cloud provider secures everything | Managed services hide control plane work, so teams forget they still own identity, data, workload, and network configuration | Maintain a responsibility map that names provider-owned and customer-owned controls with evidence for each one |
| Using static credentials for pods | Static keys are easy to create and work across providers, but they persist in Secrets, backups, logs, and developer machines | Use workload identity with short-lived scoped credentials and remove long-lived cloud keys from the cluster |
| Leaving a public API server endpoint unnoticed | Default cluster creation often optimizes for easy access during setup rather than production exposure limits | Use private endpoints or restrict public endpoints to approved networks, then document operator and CI/CD access paths |
| Granting overly permissive IAM policies to node roles | Shared node groups feel like an infrastructure layer, so teams attach broad policies once for many applications | Move permissions to per-workload identities and keep node roles focused on node operations |
| Enabling etcd encryption but ignoring RBAC | Encryption at rest sounds complete, yet Kubernetes decrypts Secret values for authorized API readers | Pair encryption with least-privilege RBAC, audit logging, and external secret rotation where appropriate |
| Treating namespaces as strong tenant boundaries | Namespaces are cheap and familiar, but they share a control plane, node infrastructure, and many policy systems | Use separate clusters or cloud accounts when tenants represent customers, different trust levels, or regulated data |
| Forgetting provider-specific network policy behavior | The same Kubernetes manifest can behave differently if the chosen CNI or managed mode does not enforce policies | Verify the provider networking mode, install required add-ons, and test deny and allow paths before production |

## Quiz

<details>
<summary>Question 1: Your team migrates from self-managed Kubernetes to a managed service and stops tracking API server patching. During the same migration, it leaves broad RBAC and public endpoint settings unchanged. How should you evaluate the shared responsibility boundary?</summary>

The provider now owns much of the control plane operation, including API server availability and patching, so it is reasonable to stop managing those binaries directly. The customer still owns API endpoint exposure, cloud identity mappings, Kubernetes RBAC, workload configuration, and data protection. The review should separate tasks the provider has truly absorbed from controls the customer must still configure. A good answer also asks for evidence, such as endpoint settings, RBAC bindings, and provider documentation for the managed control plane.

</details>

<details>
<summary>Question 2: During a security review, you discover that a development team stores AWS access keys as Kubernetes Secrets so pods can read an object storage bucket. The keys were created 18 months ago and have never been rotated. What risks does this create, and what should replace this approach?</summary>

The static keys create persistent access that may survive far beyond the workload or team that created them. They can leak through Kubernetes RBAC mistakes, etcd backups, application logs, debugging output, or local developer copies. The safer replacement is workload identity, such as EKS IRSA or Pod Identity, with a role scoped to the exact bucket and prefix the pod needs. That design uses short-lived credentials and reduces the blast radius if the pod is compromised.

</details>

<details>
<summary>Question 3: Your organization uses EKS with a public API server endpoint, and a consultant recommends a private endpoint. What threat does this mitigate, and what operational changes are required?</summary>

A private endpoint reduces the API server's internet reachability before authentication is tested, which lowers exposure to brute force attempts, reconnaissance, credential stuffing, and future API server vulnerabilities. It does not replace strong identity or RBAC, because authorized users can still do harmful things from approved networks. The operational tradeoff is that developers, automation, monitoring, and break-glass responders need a private path such as VPN, bastion access, or in-network runners. The decision should include those access paths before the setting is changed.

</details>

<details>
<summary>Question 4: A multi-tenant SaaS platform runs all customer workloads in one Kubernetes cluster using namespace isolation. A security audit says this is insufficient for high-value tenants. How do you diagnose the isolation problem and choose an alternative?</summary>

Namespace isolation is a moderate boundary because tenants still share the API server, admission policy, node infrastructure, logging path, and many cloud networking controls. It can be appropriate for applications with the same owner and trust level, but it is weaker when tenants represent different customers or regulatory scopes. Stronger alternatives are separate clusters or separate cloud accounts, depending on the desired blast-radius boundary. The decision should consider customer impact, IAM separation, network routing, operational cost, and incident response ownership.

</details>

<details>
<summary>Question 5: Encryption at rest is enabled for the cluster's Secret storage, but a colleague says application credentials are now safe. What assumption are they making that could be wrong?</summary>

They are assuming encryption at rest controls every way a Secret can be exposed. In reality, Kubernetes decrypts Secret values for users and pods that are authorized to read them through the API server. Backups, snapshots, RBAC, audit logging, and key administration still matter because each one controls a different exposure path. The correct fix is to pair encryption with least-privilege RBAC, workload identity where possible, key access review, and rotation plans.

</details>

<details>
<summary>Question 6: A team compares EKS, GKE, and AKS for a production platform, but the discussion becomes a brand preference debate. What security criteria should drive the comparison instead?</summary>

The comparison should focus on properties the platform needs, not the provider logo. Important criteria include API endpoint reachability, workload identity maturity, node operating system and patching model, network policy enforcement, integration with the organization's identity provider, encryption and key management options, logging coverage, and evidence collection. Each provider can satisfy those criteria differently. The final choice should document compensating controls for any default that does not meet the production baseline.

</details>

<details>
<summary>Question 7: An incident review finds that a compromised pod used a broad node role to read unrelated storage objects. Which IAM and Kubernetes controls would you implement first, and why?</summary>

The first control is workload identity for the affected application, because it moves cloud permissions from the shared node role to a narrowly scoped ServiceAccount binding. The node role should then be reduced to node operations so unrelated pods cannot inherit broad storage access. Kubernetes RBAC should be reviewed to limit who can modify service accounts, create pods that use privileged identities, or read Secrets. Network and metadata access controls should also be tested so a pod compromise does not automatically reach credentials.

</details>

## Hands-On Exercise: Responsibility Mapping and Evidence Review

In this exercise, you will build a lightweight responsibility map for a managed Kubernetes deployment and connect each responsibility to evidence you could collect. You can complete the exercise with any Kubernetes 1.35+ cluster, including a local test cluster, because the goal is to practice reasoning before provider-specific automation. If you do have access to EKS, GKE, or AKS, add the matching provider evidence in the notes column.

### Scenario

You are deploying a new payment-support application to managed Kubernetes. The application needs to read invoices from object storage, expose a private internal API, and store configuration in Kubernetes. Developers need read access for troubleshooting, while CI/CD needs deployment access. The security review must decide which controls belong to the provider, which belong to the platform team, and which evidence should be gathered before production.

| Security Task | Provider or Customer? |
|--------------|----------------------|
| Patching the Kubernetes API server | ? |
| Creating RBAC roles for developers | ? |
| Enabling etcd encryption | ? |
| Securing physical access to data center | ? |
| Configuring network policies | ? |
| Patching worker node OS | ? |
| Managing your application secrets | ? |
| Ensuring API server high availability | ? |

### Tasks

- [ ] Classify each task in the table as provider, customer, or shared, and write one sentence explaining the owner.
- [ ] Run `k auth can-i` checks for developer-style access in a non-production namespace and record whether the identity can read pods, read secrets, and create role bindings.
- [ ] Identify one workload that needs cloud API access and write the intended workload identity mapping in plain language.
- [ ] Choose an API server exposure posture for production and document the operator, CI/CD, and emergency access paths it requires.
- [ ] Select the right isolation level for production, staging, and customer-specific workloads using the multi-tenancy model from this module.
- [ ] Create a final evidence checklist with at least one Kubernetes command output and one provider configuration item for each major control.

### Suggested Commands

```bash
k create namespace payments-review
k auth can-i get pods -n payments-review
k auth can-i get secrets -n payments-review
k auth can-i create rolebindings -n payments-review
k get serviceaccounts -n payments-review
k get networkpolicies -A
```

### Solution Guide

<details>
<summary>Responsibility table answer</summary>

| Security Task | Responsibility |
|--------------|----------------|
| Patching the Kubernetes API server | **Provider** - They manage control plane |
| Creating RBAC roles for developers | **Customer** - You configure access |
| Enabling etcd encryption | **Customer** (usually) - You decide encryption settings |
| Securing physical access to data center | **Provider** - Physical security |
| Configuring network policies | **Customer** - You configure workload networking |
| Patching worker node OS | **Customer** (but often automated) |
| Managing your application secrets | **Customer** - Your application data |
| Ensuring API server high availability | **Provider** - Control plane availability |

</details>

<details>
<summary>Evidence checklist answer</summary>

A strong checklist includes Kubernetes evidence and provider evidence for every boundary. For RBAC, include `k auth can-i` output for representative human and automation identities. For workload identity, include the ServiceAccount name, namespace, cloud role name, allowed resources, and rotation behavior. For network posture, include API endpoint settings, subnet placement, firewall or security group rules, and NetworkPolicy enforcement evidence. For encryption, include provider encryption settings, key ownership, Secret read permissions, and audit logging coverage.

</details>

### Success Criteria

- [ ] Every listed security task has an owner and evidence source.
- [ ] Developer access is tested with `k auth can-i`, not guessed from group names.
- [ ] At least one workload identity mapping replaces a static credential design.
- [ ] API server exposure is justified with operational access paths.
- [ ] The tenancy decision matches data sensitivity and customer separation.
- [ ] The final checklist includes both Kubernetes and cloud provider evidence.

### Summary Table

| Concept | Key Points |
|---------|------------|
| **Shared Responsibility** | Provider secures "of the cloud," you secure "in the cloud" |
| **Managed Kubernetes** | Provider handles control plane, you handle workloads |
| **IAM** | Foundation for all cloud access, integrate with Kubernetes |
| **Workload Identity** | Eliminate static credentials for pods |
| **Network Security** | Private subnets, security groups, encryption in transit |
| **Multi-Tenancy** | Account > Cluster > Namespace isolation strength |

Remember that the cloud provider gives you secure building blocks, while your team assembles them into a secure system. That assembly work is where most Kubernetes cloud security reviews should spend their time. When a control crosses from provider infrastructure into customer configuration, write down the owner, the evidence, and the expected failure mode so the boundary remains visible after the cluster is created.

## Sources

- [AWS EKS security best practices](https://docs.aws.amazon.com/eks/latest/userguide/security.html)
- [AWS EKS API server endpoint access](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)
- [AWS EKS IAM roles for service accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [AWS EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)
- [Google Kubernetes Engine security overview](https://cloud.google.com/kubernetes-engine/docs/concepts/security-overview)
- [GKE Workload Identity Federation for GKE](https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity)
- [GKE private clusters](https://cloud.google.com/kubernetes-engine/docs/concepts/private-cluster-concept)
- [Azure AKS security concepts](https://learn.microsoft.com/en-us/azure/aks/concepts-security)
- [Azure AKS Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
- [Kubernetes security overview](https://kubernetes.io/docs/concepts/security/)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

## Next Module

Continue with [Module 1.3: Security Principles](../module-1.3-security-principles/) to connect these cloud-provider boundaries to defense in depth, least privilege, fail-safe defaults, and other principles that guide secure Kubernetes design.
