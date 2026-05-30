---
revision_pending: false
title: "Module 6.1: Compliance Frameworks"
slug: k8s/kcsa/part6-compliance/module-6.1-compliance-frameworks
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` - Conceptual knowledge with practical Kubernetes control mapping
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: [Module 5.4: Security Tooling](/k8s/kcsa/part5-platform-security/module-5.4-security-tooling/)

Before you begin, set the standard Kubernetes shortcut used throughout KubeDojo: `alias k=kubectl`. The text uses that alias after this point, so when you see `k get namespaces` or `k auth can-i`, read it as a complete `kubectl` command with the same arguments. Kubernetes examples in this module assume Kubernetes 1.35 or newer, because compliance conversations should be anchored in the control surfaces teams are actually expected to operate today.

## Learning Outcomes

After completing this module, you will be able to make defensible design decisions rather than merely name compliance frameworks. Each outcome is written so you can test it against a realistic Kubernetes scenario, a control map, or the hands-on evidence exercise near the end of the module.

1. **Evaluate** compliance framework scope for payment, health, service-organization, and personal data workloads in Kubernetes.
2. **Design** Kubernetes control mappings that connect RBAC, audit logging, encryption, network segmentation, and image scanning to PCI DSS, HIPAA, SOC 2, and GDPR requirements.
3. **Diagnose** default posture gaps in a Kubernetes 1.35 cluster and choose hardening controls that create compliance-ready evidence.
4. **Implement** continuous evidence collection with policy as code, audit trails, and repeatable verification commands using the `k` alias.
5. **Compare** framework-specific work with shared-control programs so teams avoid duplicate compliance projects.

## Why This Module Matters

A healthcare payments startup once learned the hard way that "we use Kubernetes" was not an answer to an auditor's question. Its platform processed card payments for patient invoices, stored clinical billing notes, and supported customers in the European Union, so one application crossed PCI DSS, HIPAA, and GDPR boundaries at the same time. The engineering team had encryption enabled in several places and had a mature deployment pipeline, but nobody could show which namespace contained regulated data, which service accounts could read it, how long audit logs were retained, or whether a new workload could bypass the intended network boundary.

The financial impact came from delay rather than a public breach. A large hospital customer paused rollout until the startup could produce credible evidence, the sales team missed a renewal window, and engineers spent weeks reconstructing decisions that should have been recorded continuously. Nothing in that failure was exotic. The cluster had default service account token behavior, permissive network paths, inconsistent image scanning reports, and audit logs that were useful for debugging but not sufficient for a regulated access review.

This module teaches compliance as an engineering translation problem. Frameworks describe obligations in the language of risk, privacy, auditability, and control effectiveness; Kubernetes exposes mechanisms such as RBAC, NetworkPolicy, admission control, encryption providers, audit logging, labels, and policy engines. Your job is to connect those two worlds without pretending that a cluster setting alone satisfies a law, a contractual audit, or an industry standard.

The KCSA exam does not expect you to memorize every clause of every framework. It does expect you to recognize the shape of the problem when someone says a cluster handles card data, protected health information, customer personal data, or a SaaS service covered by an audit report. The exam-level skill is practical classification: identify the obligation, find the Kubernetes control surfaces that matter, and explain what evidence would demonstrate the control.

That skill also matters outside exams because compliance conversations often arrive late. A sales deal may require SOC 2 evidence, a payment integration may trigger PCI DSS scope review, a healthcare customer may ask about HIPAA safeguards, or a privacy team may ask where personal data appears in logs and backups. Engineers who can translate those requests into Kubernetes work help the organization avoid last-minute rewrites, emergency spreadsheets, and brittle exceptions.

The rest of the module builds that translation in layers. First you will distinguish compliance from security, then compare the major frameworks, then map the frameworks to Kubernetes controls, then design evidence that can survive an audit and a real incident review. Keep asking whether each claim can be observed in a cluster or in the surrounding operating process, because unsupported claims are where compliance programs usually break.

## What Compliance Means in Kubernetes

Compliance is the act of meeting defined security and governance requirements, but the definition of "meeting" changes depending on who is asking. A regulator may care about statutory obligations, a payment assessor may care about cardholder data environments, a customer may care about a SOC 2 report, and an internal risk team may care about whether controls are consistently applied. Kubernetes does not make an organization compliant by existing, because Kubernetes is an execution platform rather than a complete governance program.

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLIANCE FUNDAMENTALS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  COMPLIANCE = Meeting defined security requirements         │
│                                                             │
│  TYPES:                                                    │
│  ├── Regulatory - Required by law (HIPAA, GDPR)           │
│  ├── Industry - Required by industry (PCI-DSS)            │
│  └── Voluntary - Self-imposed (SOC2, ISO 27001)           │
│                                                             │
│  WHY IT MATTERS:                                           │
│  ├── Legal requirements (fines, prosecution)              │
│  ├── Customer requirements (contracts)                    │
│  ├── Insurance requirements                               │
│  ├── Trust and reputation                                 │
│  └── Security best practices                              │
│                                                             │
│  COMPLIANCE ≠ SECURITY                                     │
│  • Compliance is minimum bar                              │
│  • Security goes beyond compliance                        │
│  • Being compliant doesn't mean being secure              │
│  • Being secure often means being compliant               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The diagram's most important line is the warning that compliance is not the same thing as security. Compliance sets a minimum bar that is inspected through evidence, policies, and operating practice. Security asks whether the system resists realistic attacks, recovers from mistakes, and limits damage when a control fails. A cluster can pass a narrow audit and still run over-privileged pods, and a secure platform can still fail an audit if the team cannot prove what it did.

Think of compliance evidence like receipts for a business expense. The fact that money was spent correctly matters, but the finance team still needs a receipt, approval record, category, date, and owner before it can close the books. Kubernetes evidence works the same way: a NetworkPolicy may enforce segmentation, but an auditor may also need a diagram, a change record, a test result, and a log trail showing the policy remained in force during the review period.

Pause and predict: if a team says every production change goes through Git, what evidence would you ask for before accepting that statement as a compliance control? A strong answer mentions repository permissions, pull request approvals, admission or deployment linkage, change timestamps, and proof that emergency changes follow the same or an explicitly documented process.

Compliance language can feel abstract because it describes duties rather than implementation details. "Restrict access" becomes real only when you decide which Kubernetes subjects can perform which verbs on which resources in which namespaces. "Monitor access" becomes real only when audit logs capture the relevant API calls, those logs are retained outside the cluster, and someone reviews or alerts on activity that violates expectations. "Encrypt data" becomes real only when you know which data is stored in etcd, which data is stored in volumes, which traffic crosses networks, and which keys protect each layer.

The most useful mental model is a chain of claims. A team might claim that payment workloads are isolated, but that claim depends on namespace boundaries, NetworkPolicies, ingress rules, egress rules, workload identities, node placement, and administrative permissions. If any link is undocumented or untested, the claim becomes fragile. Compliance work strengthens the chain by making each link explicit and by preserving evidence that the link existed during the relevant review period.

### Framework Families and Scope

The first skill is scope judgment. PCI DSS follows payment card data and the systems connected to it, HIPAA follows protected health information in covered healthcare relationships, SOC 2 follows the controls of a service organization, and GDPR follows personal data of people in the European Union. Scope is not a paperwork detail; it determines which workloads, people, networks, logs, backups, and third-party systems inherit compliance obligations.

```
┌─────────────────────────────────────────────────────────────┐
│              FRAMEWORK COMPARISON                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FRAMEWORK    FOCUS              SCOPE           TYPE       │
│  ──────────────────────────────────────────────────────────│
│  PCI-DSS      Payment data       Industry        Required   │
│  HIPAA        Health data        US Healthcare   Regulatory │
│  SOC 2        Service orgs       Voluntary       Audit      │
│  GDPR         Personal data      EU              Regulatory │
│  ISO 27001    Info security      Global          Voluntary  │
│  NIST CSF     Cybersecurity      US Federal      Framework  │
│  CIS          Benchmarks         Technical       Voluntary  │
│                                                             │
│  COMMON THEMES:                                            │
│  • Access control                                         │
│  • Encryption (transit + rest)                            │
│  • Audit logging                                          │
│  • Incident response                                      │
│  • Risk assessment                                        │
│  • Vulnerability management                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Most Kubernetes compliance mistakes begin when teams scope by application name instead of data movement. A namespace called `payments` is useful, but it does not prove that only payment workloads can reach payment data. Sidecars, batch jobs, debug pods, shared observability agents, backup tools, ingress controllers, service meshes, and log pipelines may all touch regulated data directly or indirectly, which means they may become part of the control boundary.

For KCSA-level reasoning, start with three questions. What regulated data enters the cluster? Which identities, workloads, and networks can reach it? What evidence proves those answers stayed true over time? These questions keep the discussion practical, because they turn a broad framework into Kubernetes resources you can inspect with `k get`, `k describe`, `k auth can-i`, audit log searches, and policy reports.

Framework scope also changes the cost of mistakes. If a marketing service accidentally talks to a logging endpoint, the result may be ordinary operational noise. If a payment service sends cardholder data to the same logging endpoint, the logging system may become part of the cardholder data environment. If a health application writes diagnosis notes into a debug log, the observability stack may now hold protected health information. The Kubernetes resources may look identical, but the compliance consequence depends on the data flowing through them.

This is why teams should not wait for auditors to draw the boundary. Engineers know how workloads communicate, where Secrets are mounted, which operators have cluster-wide privileges, and which controllers mutate Pods at admission. A strong platform team turns that knowledge into diagrams, labels, policies, and repeatable checks before the audit request arrives. The work feels slower at first, but it saves time because the team can answer scope questions from maintained evidence instead of memory.

### PCI DSS in a Cluster

PCI DSS applies when an organization stores, processes, or transmits payment card data, and the Kubernetes relevance is strongest around segmentation, access control, encryption, vulnerability management, monitoring, and secure development. The standard is prescriptive compared with many frameworks, so it tends to produce concrete questions about firewall behavior, default credentials, cardholder data storage, logging, and periodic testing. In Kubernetes, those questions map naturally to NetworkPolicy, RBAC, Secrets handling, image scanning, audit logs, admission control, and patch management.

```
┌─────────────────────────────────────────────────────────────┐
│              PCI-DSS (Payment Card Industry)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  APPLIES TO: Organizations handling payment card data       │
│                                                             │
│  12 REQUIREMENTS (grouped):                                │
│                                                             │
│  BUILD SECURE NETWORK                                      │
│  1. Install/maintain firewall                              │
│  2. Don't use vendor-supplied default passwords           │
│                                                             │
│  PROTECT CARDHOLDER DATA                                   │
│  3. Protect stored cardholder data                        │
│  4. Encrypt transmission over public networks             │
│                                                             │
│  MAINTAIN VULNERABILITY MANAGEMENT                         │
│  5. Use and update anti-virus software                    │
│  6. Develop secure systems and applications               │
│                                                             │
│  IMPLEMENT ACCESS CONTROL                                  │
│  7. Restrict access on need-to-know basis                 │
│  8. Assign unique ID to each person                       │
│  9. Restrict physical access                              │
│                                                             │
│  MONITOR AND TEST                                          │
│  10. Track and monitor all access                         │
│  11. Regularly test security systems                      │
│                                                             │
│  MAINTAIN POLICY                                           │
│  12. Maintain information security policy                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The phrase "cardholder data environment" matters because scope expands to systems that can affect the security of payment data. If a general-purpose build agent can deploy into the payment namespace, that agent may be in scope. If a shared logging stack stores full request payloads containing card data, the logging stack may be in scope. If a support namespace can run arbitrary debug containers that reach payment services, the support namespace may be in scope even though it is not named after payments.

```
┌─────────────────────────────────────────────────────────────┐
│              PCI-DSS KUBERNETES CONTROLS                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  REQUIREMENT → KUBERNETES CONTROL                          │
│                                                             │
│  Firewalls (1)                                             │
│  → Network Policies, CNI segmentation                      │
│                                                             │
│  No default passwords (2)                                  │
│  → Secrets management, service account tokens              │
│                                                             │
│  Protect stored data (3)                                   │
│  → Encryption at rest (etcd, secrets)                     │
│                                                             │
│  Encrypt transmission (4)                                  │
│  → TLS everywhere, service mesh mTLS                      │
│                                                             │
│  Secure development (6)                                    │
│  → Image scanning, supply chain security                  │
│                                                             │
│  Access control (7,8)                                      │
│  → RBAC, ServiceAccounts, authentication                  │
│                                                             │
│  Monitoring (10)                                           │
│  → Audit logging, runtime security                        │
│                                                             │
│  Regular testing (11)                                      │
│  → Vulnerability scanning, penetration testing            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A practical PCI design usually starts with isolation before it starts with tooling. A separate cluster gives the cleanest boundary, but it adds operational cost and may be too heavy for smaller teams. A dedicated namespace with default-deny NetworkPolicies, restricted admission, narrow RBAC, separate node pools, tightly controlled ingress, and explicit egress can be acceptable when the team can prove the boundary. The tradeoff is evidence burden: the weaker the physical or administrative boundary, the stronger the documentation and testing must be.

> **Stop and think**: A startup says "we're compliant with SOC 2 Type II, so our Kubernetes cluster is secure." Is this a valid conclusion, and what could be insecure despite passing a SOC 2 audit? A careful answer separates the report boundary from current cluster reality, then checks for privileged Pods, weak RBAC, exposed Secrets, missing NetworkPolicies, unreviewed exceptions, and new deployments after the audit period.

PCI DSS also shows why "Kubernetes control" and "application control" must work together. NetworkPolicy can restrict which services reach a payment API, but it cannot decide whether the application stores full card numbers or tokenized references. Secret encryption can protect values in etcd, but it cannot compensate for writing sensitive data to unredacted logs. Image scanning can identify known vulnerabilities, but the organization still needs a patching and exception process when a fix cannot be deployed immediately.

### HIPAA, SOC 2, and GDPR

HIPAA is often misunderstood because it does not provide a Kubernetes checklist and it does not offer an official certification badge. It requires covered entities and business associates to protect electronic protected health information through administrative, physical, and technical safeguards. Kubernetes mostly helps with the technical safeguards, such as access control, audit controls, integrity, authentication, and transmission security, while the organization still needs policies, training, vendor management, and breach procedures outside the cluster.

```
┌─────────────────────────────────────────────────────────────┐
│              HIPAA (Healthcare)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  APPLIES TO: Healthcare providers, insurers, associates     │
│  PROTECTS: Protected Health Information (PHI)              │
│                                                             │
│  SECURITY RULE SAFEGUARDS:                                 │
│                                                             │
│  ADMINISTRATIVE                                            │
│  ├── Risk analysis and management                         │
│  ├── Security policies and procedures                     │
│  ├── Workforce training                                   │
│  └── Incident response                                    │
│                                                             │
│  PHYSICAL                                                  │
│  ├── Facility access controls                             │
│  ├── Workstation security                                 │
│  └── Device and media controls                            │
│                                                             │
│  TECHNICAL                                                 │
│  ├── Access control (unique user IDs)                     │
│  ├── Audit controls (logging)                             │
│  ├── Integrity controls (data validation)                 │
│  ├── Transmission security (encryption)                   │
│  └── Authentication                                       │
│                                                             │
│  BREACH NOTIFICATION:                                      │
│  • Must notify individuals within 60 days                 │
│  • May require HHS notification                           │
│  • Media notification for large breaches                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

SOC 2 is different again because it is an attestation report for service organizations, not a law that applies to a category of data. Security is the required Trust Services Criterion, while availability, processing integrity, confidentiality, and privacy are optional criteria selected based on customer promises and business needs. For Kubernetes teams, SOC 2 usually asks whether logical access, change management, monitoring, vulnerability management, incident response, and system operations are designed and operating effectively over a period of time.

```
┌─────────────────────────────────────────────────────────────┐
│              SOC 2 (Service Organization Control)           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  APPLIES TO: Service organizations (SaaS, cloud)           │
│  TYPE I: Point-in-time assessment                          │
│  TYPE II: Period of time (usually 12 months)              │
│                                                             │
│  TRUST SERVICE CRITERIA:                                   │
│                                                             │
│  SECURITY (required)                                       │
│  ├── Protection against unauthorized access               │
│  ├── Logical and physical access controls                 │
│  └── System operations security                           │
│                                                             │
│  AVAILABILITY (optional)                                   │
│  ├── System availability for operation                    │
│  └── Disaster recovery capabilities                       │
│                                                             │
│  PROCESSING INTEGRITY (optional)                           │
│  ├── System processing is complete and accurate           │
│  └── Data validation                                      │
│                                                             │
│  CONFIDENTIALITY (optional)                                │
│  ├── Information designated confidential protected        │
│  └── Data classification                                  │
│                                                             │
│  PRIVACY (optional)                                        │
│  ├── Personal information collection and use              │
│  └── GDPR alignment                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

GDPR follows personal data and accountability. A Kubernetes operator may not decide the legal basis for processing, but the platform can strongly affect data minimization, integrity, confidentiality, breach detection, deletion workflows, and retention. If logs capture personal data indefinitely, if backups cannot support deletion or minimization decisions, or if cross-region placement violates a documented data transfer design, the cluster architecture becomes part of the privacy problem.

```
┌─────────────────────────────────────────────────────────────┐
│              GDPR (EU Data Protection)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  APPLIES TO: Organizations processing EU resident data      │
│  SCOPE: Any personal data (PII)                            │
│                                                             │
│  KEY PRINCIPLES:                                           │
│  ├── Lawfulness, fairness, transparency                   │
│  ├── Purpose limitation                                   │
│  ├── Data minimization                                    │
│  ├── Accuracy                                             │
│  ├── Storage limitation                                   │
│  ├── Integrity and confidentiality                        │
│  └── Accountability                                       │
│                                                             │
│  DATA SUBJECT RIGHTS:                                      │
│  ├── Right to access                                      │
│  ├── Right to rectification                               │
│  ├── Right to erasure ("right to be forgotten")          │
│  ├── Right to data portability                           │
│  └── Right to object to processing                        │
│                                                             │
│  SECURITY REQUIREMENTS:                                    │
│  • "Appropriate" technical and organizational measures    │
│  • Encryption, pseudonymization                           │
│  • Regular testing and evaluation                         │
│  • 72-hour breach notification                            │
│                                                             │
│  FINES: Up to €20M or 4% global annual revenue           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Before running the next command in a real environment, what output would you expect from `k auth can-i get secrets --as system:serviceaccount:payments:checkout -n payments`? If the answer is yes, the next question is whether that access is needed, whether it is logged, and whether the service account can reach only the workloads that justify the permission.

When these three frameworks overlap, the same Kubernetes evidence can support different stories. HIPAA may use audit logs to show technical safeguards around protected health information, SOC 2 may use the same logs to show monitoring and logical access control, and GDPR may use related records to demonstrate accountability and security of processing. The control does not change, but the explanation changes because each framework asks why the control exists and what risk it reduces.

There are also limits that Kubernetes cannot solve alone. HIPAA workforce training, SOC 2 vendor risk review, and GDPR legal basis for processing are organizational controls. Kubernetes can store evidence, enforce deployment paths, and restrict access, but it cannot replace contracts, policies, records of processing, or human accountability. A mature compliance map is honest about those limits so the platform team does not promise more than the cluster can prove.

### Default vs. Compliant Posture

A vanilla Kubernetes cluster prioritizes flexible scheduling and developer productivity, not a particular regulatory posture. That does not make Kubernetes insecure by default in every deployment, but it does mean the platform needs deliberate configuration before it can support regulated workloads. Compliance-ready Kubernetes is less about one magic switch and more about narrowing defaults, recording decisions, and continuously proving that workloads stay inside intended boundaries.

| Component | Vanilla Kubernetes Default | Compliance-Ready Posture | Compliance Impact |
|-----------|----------------------------|--------------------------|-------------------|
| **Network** | Flat network (all pods can communicate) | Default-deny NetworkPolicies, strict segmentation | Fails PCI-DSS scope reduction; fails SOC 2 logical access |
| **Secrets** | Base64 encoded in etcd (plain-text) | Encrypted at rest using a KMS provider | Fails HIPAA/PCI-DSS data protection requirements |
| **Service Accounts** | Tokens automounted to every pod | `automountServiceAccountToken: false` by default | Fails least privilege access (SOC 2, PCI-DSS) |
| **Pod Security** | Pods can run as root, mount host paths | Pod Security Admission (Restricted/Baseline) | Fails SOC 2 system operations security; increases blast radius |
| **Audit Logs** | Often disabled or limited retention | API server audit logging enabled, shipped to SIEM | Fails HIPAA audit controls; fails PCI-DSS monitoring |
| **Images** | Pull from any registry, no scanning | Signed images from trusted registries, continuous scanning | Fails PCI-DSS secure development; fails SOC 2 vulnerability management |

This table is a diagnostic tool, not a guarantee. A managed Kubernetes service may handle portions of the control plane, patching, encryption integration, or logging pipeline, but customers usually still own namespace design, workload identity, RBAC, admission policy, application secrets, network segmentation, image provenance, and evidence retention. Shared responsibility means the cloud provider may operate the building, while your team still decides who gets keys to each room.

> **Pause and predict**: Your cluster handles both payment card data (PCI-DSS) and health records (HIPAA). Would you run both workloads in the same namespace, and what isolation strategy would satisfy both frameworks? A defensible answer starts with separate namespaces or clusters, default-deny network policy, distinct service accounts, restricted admission, separate evidence, and a documented reason if the workloads share any platform component.

> **Stop and think**: If you deploy a managed Kubernetes cluster like EKS or GKE, are these default posture gaps automatically fixed for you, or is compliance still a shared responsibility? The provider may inherit control-plane duties, but your team still owns workload configuration, data classification, access decisions, application behavior, and the evidence that proves regulated workloads were operated correctly.

Default posture diagnosis should be performed before workload onboarding, not after sensitive data is already flowing. A good onboarding review asks whether the namespace has a data classification label, whether service account tokens are needed, whether egress is controlled, whether audit policy captures sensitive verbs, whether admission policy blocks privileged configurations, and whether image provenance is checked. If the answer is "we will add that later," the team should treat the workload as not ready for regulated data.

The important tradeoff is velocity versus provability. Open defaults let teams move quickly, but they require detective work after the fact and create ambiguity during audits. Hardened defaults may require more up-front platform engineering, yet they make each new workload easier to explain because the baseline is already known. Compliance-ready Kubernetes usually chooses guardrails for regulated namespaces and more flexible policy for low-risk development spaces.

## Designing Kubernetes Control Maps

Compliance control mapping connects framework language to concrete Kubernetes mechanisms. The mapping is not one-to-one, because a single Kubernetes control can support multiple obligations and a single framework requirement may require technical, procedural, and human evidence. RBAC helps with least privilege, but it does not prove access reviews happened; audit logs record API activity, but they do not prove someone investigated suspicious access; image scanning finds known vulnerabilities, but it does not prove emergency patch decisions were risk accepted.

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES COMPLIANCE CONTROLS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ACCESS CONTROL                                            │
│  ├── RBAC with least privilege                            │
│  ├── Strong authentication (OIDC, certificates)           │
│  ├── ServiceAccount management                            │
│  ├── Namespace isolation                                  │
│  └── Pod Security Standards                               │
│                                                             │
│  DATA PROTECTION                                           │
│  ├── Secrets encryption at rest                           │
│  ├── TLS for all communications                           │
│  ├── Service mesh mTLS                                    │
│  ├── Secure secret management (Vault)                     │
│  └── Data classification labeling                         │
│                                                             │
│  AUDIT & MONITORING                                        │
│  ├── API server audit logging                             │
│  ├── Container logging                                    │
│  ├── Runtime security (Falco)                            │
│  ├── Log retention                                        │
│  └── SIEM integration                                     │
│                                                             │
│  VULNERABILITY MANAGEMENT                                  │
│  ├── Image scanning                                       │
│  ├── Cluster configuration scanning                       │
│  ├── Regular patching                                     │
│  └── Penetration testing                                  │
│                                                             │
│  NETWORK SECURITY                                          │
│  ├── Network Policies                                     │
│  ├── Private API endpoints                                │
│  ├── Ingress security                                     │
│  └── Egress controls                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Start a control map by naming the asset and the risk, then attach the Kubernetes mechanism. For example, if the asset is electronic protected health information in the `patient-records` namespace, the risks include unauthorized API reads, accidental exposure through logs, weak workload boundaries, and untracked administrative changes. Useful controls include namespace-level RBAC, admission policies requiring restricted pods, encrypted Secrets, audit policy rules for sensitive resource verbs, NetworkPolicies around the application, and log redaction controls outside Kubernetes.

Control mapping should also describe evidence freshness. A screenshot from six months ago proves almost nothing about today's cluster. A Git-tracked policy, a current `k get networkpolicy -n payments` export, an admission report, and an audit log query over the review period are much stronger because they show both design and operation. For SOC 2 Type II, operation over time is especially important; for PCI DSS, periodic testing and monitoring need a repeatable cadence; for GDPR, accountability favors records that explain why processing and protection decisions were made.

```yaml
# Kyverno policy enforcing encryption requirement
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-encryption-annotation
  annotations:
    policies.kyverno.io/description: |
      PCI-DSS Requirement 3: All pods handling cardholder
      data must have encryption enabled
spec:
  validationFailureAction: Enforce
  rules:
  - name: check-encryption-annotation
    match:
      any:
      - resources:
          kinds:
          - Pod
          namespaces:
          - payment-processing
    validate:
      message: "Pods in payment-processing namespace must have encryption enabled"
      pattern:
        metadata:
          annotations:
            security.company.com/encryption: "enabled"
```

The Kyverno policy above is intentionally narrow: it checks an annotation on Pods in a payment namespace. In a production program, the annotation would need to mean something enforceable, such as deployment through a platform path that injects encryption configuration, validates application settings, or binds the workload to approved storage. A policy that checks a label nobody verifies becomes paperwork as code, while a policy tied to runtime behavior becomes useful evidence.

A worked example makes the distinction concrete. Suppose a checkout service stores card tokens in an external payment vault and keeps only transaction references in Kubernetes. The team can reduce PCI scope by documenting that card data does not persist in etcd, proving that Secrets do not contain cardholder data, enforcing egress only to the payment vault, logging service account access, and scanning images before deployment. The control map should say exactly which claim each artifact supports, because auditors and incident responders both need that traceability.

Control maps become stronger when they include negative evidence as well as positive evidence. Positive evidence says the payment service can reach the payment vault. Negative evidence says the marketing service cannot reach the payment vault, cannot create Pods in the payment namespace, and cannot read Secrets used by the checkout service. Kubernetes is especially good at producing this kind of proof through authorization checks, NetworkPolicy tests, admission denials, and audit log searches.

Do not hide exceptions from the map. Real systems have break-glass access, temporary debug privileges, emergency images, and manual remediation paths. The compliance problem is not that exceptions exist; it is that exceptions become permanent or invisible. A defensible exception includes a business reason, approval, expiration, compensating controls, and evidence that the exception was removed or renewed after review. Without those records, an exception looks like an uncontrolled bypass.

The mapping process should include application owners because the platform team cannot infer every data obligation from Kubernetes resources alone. A Pod spec may show a database endpoint, but it may not reveal whether the database contains billing identifiers, clinical notes, or anonymized analytics. Application owners bring data meaning, platform engineers bring control mechanics, and security or compliance owners bring framework interpretation. The control map is the shared artifact where those views meet.

## Building Continuous Evidence

Evidence collection is where many otherwise strong Kubernetes teams struggle. They can explain the architecture in a meeting, but they cannot quickly produce the artifacts that prove the architecture is still true. Compliance-ready systems treat evidence as a by-product of normal engineering work: policies live in Git, scans run on schedule, audit logs are retained, access reviews have owners, and deployment metadata ties each running workload back to an approved change.

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLIANCE EVIDENCE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUDITORS NEED:                                            │
│                                                             │
│  POLICIES                                                  │
│  ├── Security policies (as code)                          │
│  ├── RBAC configurations                                  │
│  ├── Network Policies                                     │
│  └── Pod Security Standards                               │
│                                                             │
│  LOGS                                                      │
│  ├── Audit logs showing access                            │
│  ├── Authentication logs                                  │
│  ├── Changes to sensitive resources                       │
│  └── Security incident logs                               │
│                                                             │
│  SCAN REPORTS                                              │
│  ├── Vulnerability scan results                           │
│  ├── CIS benchmark reports                                │
│  ├── Penetration test results                             │
│  └── Configuration audit reports                          │
│                                                             │
│  PROCEDURES                                                │
│  ├── Incident response procedures                         │
│  ├── Change management evidence                           │
│  ├── Access review documentation                          │
│  └── Training records                                     │
│                                                             │
│  AUTOMATION HELPS:                                         │
│  • Policy as code (version controlled)                    │
│  • Automated scanning (continuous evidence)               │
│  • Infrastructure as code (reproducible)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A useful evidence record has five properties: it identifies the control, covers the correct scope, shows a timestamp or review period, has an owner, and can be reproduced. For Kubernetes, that usually means exporting resource state, linking it to source control, retaining audit logs outside the cluster, and recording tool versions. A single command output is weaker than a scheduled job with immutable storage, but even a command output is better when it includes namespace, cluster, time, and the exact question it answers.

Runbooks should separate "prove the design" from "prove the operation." Design evidence includes architecture diagrams, threat models, RBAC role definitions, NetworkPolicies, admission policies, encryption configuration, and documented data flows. Operating evidence includes audit log samples, access review tickets, scan reports, deployment approvals, incident drills, and exceptions with expiration dates. When these are mixed together, teams either over-focus on static YAML or drown auditors in logs without a coherent story.

```
┌─────────────────────────────────────────────────────────────┐
│              CONTINUOUS COMPLIANCE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRADITIONAL COMPLIANCE:                                   │
│  Annual audit → Fix findings → Pass audit → Drift         │
│                     ↓                                      │
│  Problems: Point-in-time, costly, reactive                │
│                                                             │
│  CONTINUOUS COMPLIANCE:                                    │
│  Automated checks → Continuous monitoring → Real-time fix │
│                     ↓                                      │
│  Benefits: Always compliant, proactive, efficient         │
│                                                             │
│  IMPLEMENTATION:                                           │
│  ├── Policy as code (Kyverno/OPA)                        │
│  ├── Automated scanning (daily/hourly)                    │
│  ├── Drift detection                                      │
│  ├── Automated remediation where safe                     │
│  └── Dashboard and reporting                              │
│                                                             │
│  TOOLS:                                                    │
│  ├── kube-bench (CIS checks)                             │
│  ├── Trivy (vulnerability scanning)                       │
│  ├── Polaris (configuration checks)                       │
│  └── Cloud provider compliance tools                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Continuous compliance does not mean automatically remediating every finding. Some fixes are safe, such as blocking a privileged Pod before admission or denying a workload that lacks a required label. Other findings require human judgment, such as whether an emergency image should be allowed temporarily because it fixes an active incident. A mature program distinguishes enforceable guardrails from alerting controls and documents who can approve exceptions, for how long, and with what compensating measures.

Which approach would you choose here and why: blocking noncompliant Pods at admission, or allowing them and creating tickets after deployment? For regulated namespaces containing payment or health data, blocking is usually the right default because the blast radius of a bad deployment is high. For lower-risk development namespaces, alerting may be acceptable if the team uses the findings for education and drift reduction rather than pretending every warning is an incident.

You can collect a simple evidence bundle from a live cluster with commands like `k get rolebinding -A`, `k get networkpolicy -A`, `k get validatingadmissionpolicy -A`, and `k auth can-i list secrets --as system:serviceaccount:payments:checkout -n payments`. These commands are not a complete audit, but they help learners connect framework language to observable cluster state. The next level is to schedule those checks, store signed results, and compare them against approved policy so drift becomes visible quickly.

An evidence pipeline should be boring by design. It should run on a predictable schedule, write to storage that workload administrators cannot silently alter, and include enough metadata to make each record understandable later. The metadata matters because a raw YAML export without cluster name, namespace, time, reviewer, tool version, and policy baseline is difficult to trust. Auditors and incident responders both need to know whether an artifact describes the right environment at the right time.

Evidence review also needs prioritization. A missing label in a development namespace may be a cleanup task, while a newly privileged Pod in a payment namespace may require immediate containment. Continuous compliance systems should classify findings by data sensitivity, exposure, exploitability, and control importance. This keeps teams from treating every policy result as equal and helps them focus engineering time where compliance and security risk overlap.

Finally, continuous evidence should feed improvement rather than just storage. If the same exception appears every week, the team may need a better platform feature, a clearer policy, or a refactored workload. If access reviews repeatedly find unused permissions, the RBAC model may be too broad. Compliance programs become valuable when the evidence loop changes engineering behavior, not when it simply produces larger folders before an audit.

## Patterns & Anti-Patterns

Good compliance engineering favors shared controls, narrow boundaries, and evidence that is generated during normal operations. The pattern is similar to site reliability engineering: you do not wait for an outage to invent observability, and you should not wait for an audit to invent evidence. Teams that do this well can answer compliance questions with the same systems they use to deploy, monitor, and review production changes.

The strongest pattern is to make the secure path the easy path. Developers should not need to memorize every PCI DSS or HIPAA implication before deploying a service; the platform should guide regulated workloads into approved namespaces, default-deny networking, restricted Pod settings, trusted registries, and standard logging. The compliance team still owns interpretation, but the platform reduces the number of custom decisions each application team must make.

Another useful pattern is evidence reuse with careful wording. The same NetworkPolicy export might support PCI DSS segmentation, SOC 2 logical access, and GDPR security of processing, but the control description should explain the framework-specific risk each time. Reuse does not mean pretending all frameworks are identical. It means one well-operated control can answer several questions when the team preserves enough context.

| Pattern | When to Use | Why It Works | Scaling Considerations |
|---------|-------------|--------------|------------------------|
| Shared-control mapping | Multiple frameworks apply to the same platform | One strong RBAC, logging, encryption, and segmentation program supports several audits | Maintain a control matrix with framework references, owners, and evidence links |
| Regulated namespace or cluster boundary | A workload handles payment, health, or personal data with higher risk | Boundaries make scope easier to explain and test | Separate clusters reduce ambiguity but increase platform overhead |
| Policy as code with exception expiry | Teams need consistent enforcement without blocking legitimate emergencies | Admission policies stop known bad states while exception records preserve accountability | Exceptions need owners, expiration dates, and review cadence |
| Continuous evidence pipeline | Audits require operating effectiveness over time | Scheduled exports, scans, and log queries reduce manual collection | Store evidence outside the cluster and protect it from workload administrators |

The main anti-pattern is treating a framework as a checklist detached from architecture. Teams copy a control statement into a spreadsheet, mark it complete because a tool exists somewhere, and then discover that the tool was not enabled for the regulated namespace. The better alternative is to trace from data to workload to identity to network path to evidence, because that chain exposes the places where a framework requirement can fail in practice.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| One cluster, no scope boundary | Every connected workload can become part of the audit scope | Use separate clusters or strict namespace, network, identity, and admission boundaries |
| Evidence collected only before audits | Drift hides for months and teams scramble under deadline pressure | Generate evidence continuously and review exceptions on a schedule |
| Tool presence counted as control effectiveness | A scanner or policy engine may exist but miss critical namespaces | Verify coverage and test representative workloads regularly |
| Framework-specific duplicate projects | Separate PCI, HIPAA, SOC 2, and GDPR efforts create inconsistent controls | Build shared controls and map them to each framework requirement |

The old quick checklist still captures the operational smell of several failures, and it remains useful as a compressed review aid after you understand the deeper pattern behind each row. Read it as a warning against shallow audit preparation rather than as the full common-mistake section for this module.

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Treating compliance as checkbox | Missing real security | Use frameworks as foundation |
| Point-in-time compliance | Drift between audits | Continuous monitoring |
| Manual evidence collection | Slow, incomplete | Automate evidence gathering |
| Ignoring framework overlap | Duplicate work | Map controls across frameworks |
| No compliance ownership | Gaps and confusion | Assign clear responsibility |

## Decision Framework

Use a decision framework when a team asks whether a Kubernetes control is "enough" for compliance. The answer depends on data sensitivity, legal or contractual scope, available boundaries, evidence quality, and operational maturity. A team running public marketing content can accept different defaults than a team running payment authorization, patient scheduling, or identity verification workloads, even when the YAML files look superficially similar.

| Decision Question | Lower-Risk Answer | Higher-Risk Answer | Kubernetes Decision |
|-------------------|-------------------|--------------------|---------------------|
| What regulated data is present? | No payment, health, or personal data | Cardholder data, PHI, or EU personal data | Label namespaces and workloads by data class |
| How strong must the boundary be? | Shared platform with logical separation | Dedicated environment or strict isolation | Choose namespace boundary, node isolation, or separate cluster |
| How fast can drift hurt you? | Development-only impact | Customer, patient, or payment impact | Prefer admission enforcement for regulated workloads |
| What evidence is required? | Internal review only | External audit or legal review | Store immutable evidence with owners and timestamps |
| Who owns exceptions? | Platform team triage | Risk owner approval required | Add exception expiry, compensating controls, and review records |

The framework can be applied as a short sequence. First, classify the data and framework obligations. Second, draw the real access paths, including CI systems, observability agents, operators, backups, and human administrators. Third, choose the smallest boundary that can be defended with evidence. Fourth, map each framework requirement to Kubernetes controls plus non-Kubernetes process evidence. Finally, automate enough collection that the next audit is a review of records, not a reconstruction project.

```text
Start
  |
  v
Classify regulated data
  |
  v
Can unrelated workloads reach it?
  | yes
  v
Strengthen boundary or move workload
  |
  v
Map controls to framework requirements
  |
  v
Collect design and operating evidence
  |
  v
Review drift, exceptions, and ownership
```

The summary table below is a compact reference for the four frameworks emphasized in this module. It is useful during design reviews because it keeps the conversation anchored in the purpose of each framework rather than in tool names. Tool names come later, after the team agrees what it is protecting and how the evidence will be judged.

Use the framework as a conversation tool with application teams. Ask them to describe what data they process, who needs access, what would happen if the workload were misconfigured, and what evidence would convince a skeptical reviewer. Then translate those answers into Kubernetes controls. This approach avoids the common failure where platform teams impose generic controls that do not match the application risk or the framework obligation.

The decision framework should also produce an explicit residual-risk statement. No control set eliminates risk, and compliance does not require pretending otherwise. It does require knowing which risks remain, who accepted them, what compensating controls exist, and when the decision will be reviewed. In Kubernetes, residual risk often appears around shared components, emergency access, legacy workloads, and observability systems that need broad visibility.

For a medium-sized platform, the best decision artifact is often a short control narrative attached to the control matrix. The narrative explains why the boundary was chosen, which alternatives were rejected, which Kubernetes resources enforce the decision, and which evidence shows operation over time. This prevents the matrix from becoming a set of disconnected cells and gives future engineers enough context to maintain the control when clusters, teams, or frameworks change. It also helps reviewers detect when a technical control has drifted away from the original risk decision. That context is often what saves the next audit from becoming archaeology for everyone involved.

| Framework | Focus | Key Requirements |
|-----------|-------|-----------------|
| **PCI-DSS** | Payment data | Network segmentation, encryption, access control |
| **HIPAA** | Health data | Technical safeguards, audit controls, breach notification |
| **SOC 2** | Service orgs | Trust criteria (security, availability, etc.) |
| **GDPR** | Personal data | Data protection, subject rights, breach notification |

## Did You Know?

- **PCI DSS Level 1** generally applies to merchants processing more than 6 million Visa or Mastercard transactions annually, which is why high-volume payment platforms face external assessment pressure even when their Kubernetes footprint seems small.

- **HIPAA has no official certification** from the U.S. Department of Health and Human Services, so a vendor claiming to be "HIPAA certified" should still be asked for specific safeguards, contracts, policies, and evidence.

- **SOC 2 Type II** is often more persuasive than Type I because it evaluates whether controls operated over a review period, while Type I describes design at a point in time.

- **GDPR breach notification** can require notice to a supervisory authority within 72 hours after becoming aware of a personal data breach, which makes detection and evidence retention operationally important.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating a passed audit as proof that every Kubernetes workload is secure | Audit reports have scope, timing, and evidence limits, while new workloads can introduce risk after the review period | Keep continuous controls running after the audit and review regulated namespaces for drift |
| Assuming a managed Kubernetes service automatically satisfies PCI DSS, HIPAA, SOC 2, or GDPR | Providers operate parts of the stack, but customers still own workload identity, data flow, RBAC, network policy, and evidence | Write a shared-responsibility map that lists provider controls and customer controls separately |
| Scoping by namespace name instead of data movement | Teams trust labels like `payments` or `prod` without tracing logs, backups, operators, and egress paths | Build data-flow diagrams and verify them with `k get`, network tests, and audit log searches |
| Enabling audit logs without a retention and review plan | Logs may exist briefly but fail to support investigations or audit review periods | Ship logs to protected storage, define retention, and test queries for sensitive resource access |
| Creating separate control projects for each framework | Compliance owners work in silos and ask engineering for duplicate evidence | Build shared controls once, then map the same evidence to PCI DSS, HIPAA, SOC 2, and GDPR |
| Writing policy as code that checks meaningless labels | Teams can satisfy a rule by adding metadata while the underlying risk remains unchanged | Tie labels and annotations to enforced deployment paths, runtime settings, or admission checks |
| Forgetting human and procedural controls | Kubernetes can enforce many technical controls but cannot prove training, contracts, physical security, or incident ownership alone | Pair cluster evidence with policies, access reviews, incident exercises, and vendor records |

## Quiz

<details><summary>Your platform hosts payment card tokenization, patient billing notes, and public documentation in one Kubernetes cluster. An assessor says the whole cluster may be in scope. What do you check before agreeing or pushing back?</summary>
Check actual data flow and reachability, not just namespace names. Inspect which workloads, service accounts, CI jobs, logging agents, backup tools, and operators can access the payment and health workloads, then compare those paths with NetworkPolicies, RBAC, ingress, egress, and audit logs. If unrelated workloads can communicate with or administer regulated workloads, the assessor has a strong argument. If strict boundaries exist and evidence proves they operated over time, you may be able to defend a narrower scope.</details>

<details><summary>A team passed SOC 2 Type II last month, then deployed a privileged debug Pod into a regulated namespace today. How can both statements be true, and what control would reduce the risk?</summary>
The SOC 2 report covers a defined review period and a defined set of controls, so it does not automatically prevent a bad deployment after the report date. This reveals why compliance is not the same as continuous security. A strong Kubernetes control would block privileged Pods with Pod Security Admission or an admission policy in regulated namespaces. The team should also record the attempted change in audit logs and review why the debug path existed.</details>

<details><summary>Your organization wants separate PCI DSS, HIPAA, SOC 2, and GDPR Kubernetes projects with different evidence folders. Compare that approach with a shared-control program.</summary>
Separate projects can feel organized at first, but they usually duplicate work and create inconsistent control definitions. RBAC, audit logging, encryption, NetworkPolicy, image scanning, and incident response support all four frameworks when mapped carefully. A shared-control program builds the control once, assigns an owner, stores evidence once, and references that evidence from each framework matrix. Framework-specific details still matter, but they should refine the shared control rather than create parallel systems.</details>

<details><summary>A developer adds `security.company.com/encryption: "enabled"` to a Pod so it passes the Kyverno policy, but no encryption behavior changes. What failed in the control design?</summary>
The policy checked metadata rather than an enforceable security condition. Labels and annotations can be useful when they are produced by a trusted deployment path or connected to runtime configuration, but they are weak when anyone can add them manually. The fix is to validate the actual condition where possible, restrict who can set trusted metadata, and document what the metadata proves. Evidence should show the control reduces risk, not merely that a YAML field exists.</details>

<details><summary>A privacy request arrives under GDPR, but personal data appears in application logs, backups, and several caches. How should that affect Kubernetes architecture decisions?</summary>
GDPR rights and accountability require knowing where personal data exists and how long it remains there. Kubernetes architecture should support data classification labels, log redaction, retention controls, deletion workflows, and backup policies that match the organization's privacy commitments. The platform team should help map which namespaces and services process personal data, but application owners must also design deletion and minimization behavior. Compliance fails when data copies are invisible, even if the main database supports deletion.</details>

<details><summary>Your evidence bundle contains current RBAC YAML, but no access review record or audit log sample. Is that enough for a compliance review?</summary>
It proves part of the design, but not the full operating control. RBAC YAML shows intended permissions at a point in time, while access reviews show that permissions were evaluated by accountable owners and audit logs show how access was used. Many frameworks care about both design and operating effectiveness. A stronger bundle includes role definitions, bindings, review approval, exceptions, and representative audit queries for sensitive actions.</details>

<details><summary>A managed Kubernetes provider encrypts control-plane storage and publishes compliance reports. What customer-owned gaps remain before the cluster can host regulated workloads?</summary>
The customer still owns workload-level decisions such as namespace scope, service account permissions, application secrets, image provenance, admission policy, network segmentation, data classification, and evidence retention. Provider reports can support the shared-responsibility story, but they do not prove the customer's workloads are configured safely. The team should document which controls are inherited from the provider and which are implemented in the cluster. Auditors often ask for both sides of that map.</details>

## Hands-On Exercise: Compliance Mapping

In this exercise you will turn a broad compliance conversation into a concrete Kubernetes control map. You do not need a live cluster to reason through the mapping, but the verification commands are written so you can run them in a Kubernetes 1.35 lab environment if one is available. The goal is to practice moving from "the framework says access control" to "this namespace, this service account, this policy, this log source, and this evidence record demonstrate the control."

### Scenario

Map these Kubernetes controls to compliance framework requirements while keeping the real operating story in view. Imagine a platform team that supports a payment namespace, a patient billing namespace, and a marketing namespace on the same managed Kubernetes service. The team wants to avoid four separate compliance projects, but it must still prove which controls apply to which data, which evidence is fresh, and which exceptions have accountable owners.

### Controls
1. RBAC with least privilege roles
2. API server audit logging enabled
3. Secrets encrypted at rest with KMS
4. Network Policies enforcing segmentation
5. Container images scanned for vulnerabilities

### Tasks

- [ ] Evaluate compliance framework scope for a cluster that contains `payment-processing`, `patient-billing`, and `marketing-site` namespaces.
- [ ] Design a Kubernetes control mapping that connects RBAC, audit logging, encryption, NetworkPolicies, and image scanning to PCI DSS, HIPAA, SOC 2, and GDPR.
- [ ] Diagnose default posture gaps by deciding which vanilla Kubernetes defaults would fail or weaken the evidence for each regulated namespace.
- [ ] Implement a continuous evidence checklist that names the `k` commands, scan reports, policy reports, and audit log queries you would collect each week.
- [ ] Compare a shared-control evidence bundle with four separate framework-specific evidence folders and choose the approach you would defend in a design review.

Use the preserved mapping below as the worked answer, then adapt it for your own environment by adding owners, review cadence, evidence storage location, and exception handling. The mapping is intentionally compact, so your design review notes should explain why each control is in scope and what proof would show it is operating.

When you complete the tasks, do not stop at matching words in a framework table. Explain the cause and consequence for each mapping. For example, RBAC supports access control because it limits which authenticated subjects can perform sensitive actions, and the evidence is stronger when role definitions are paired with access review records and audit log samples. NetworkPolicy supports segmentation because it constrains pod-to-pod and pod-to-external communication, but only if the CNI enforces the policy and the team tests representative allowed and denied paths.

Treat the exercise as a small design review. If you choose a shared cluster, justify why logical controls are strong enough for the data involved. If you choose separate clusters, explain the cost and operational complexity you are accepting. If you rely on admission policy, say whether violations are blocked or only reported. If you rely on scans, say how quickly findings are reviewed and who can approve temporary risk acceptance.

<details>
<summary>Compliance Mapping</summary>

| Control | PCI-DSS | HIPAA | SOC 2 | GDPR |
|---------|---------|-------|-------|------|
| **RBAC with least privilege** | 7.1, 7.2 (Access control) | Access Control (Technical) | CC6.1-CC6.3 (Logical access) | Article 32 (Security measures) |
| **API server audit logging** | 10.1-10.3 (Track access) | Audit Controls (Technical) | CC7.2 (Monitoring) | Article 30 (Records of processing) |
| **Secrets encrypted at rest** | 3.4 (Protect stored data) | Encryption (Technical) | CC6.7 (Data protection) | Article 32 (Encryption) |
| **Network Policies** | 1.2, 1.3 (Firewall rules) | Integrity (Technical) | CC6.6 (Network controls) | Article 32 (Security measures) |
| **Image scanning** | 6.1, 6.2 (Vulnerability management) | Risk Analysis (Admin) | CC7.1 (Vulnerability management) | Article 32 (Testing) |

**Key observations:**
- Most controls map to multiple frameworks
- Access control and encryption are universal requirements
- Audit logging is required by every framework
- Network segmentation is consistently important
- Vulnerability management is always included

**This shows why:**
- Implementing strong security often achieves multi-framework compliance
- Control mapping reduces duplicate effort
- A comprehensive security program naturally supports compliance

</details>

<details>
<summary>Example Evidence Checklist</summary>

Use this as a starting point for a weekly evidence collection run:

```bash
alias k=kubectl
k get namespaces --show-labels
k get role,rolebinding,clusterrole,clusterrolebinding -A
k get networkpolicy -A
k get validatingadmissionpolicy -A
k auth can-i get secrets --as system:serviceaccount:payment-processing:checkout -n payment-processing
k auth can-i create pods --as system:serviceaccount:marketing-site:web -n payment-processing
```

A passing review does not require every command to return "no"; it requires the output to match the documented design. For example, the checkout service may need to read a specific Secret in its own namespace, but the marketing service should not be able to create Pods in the payment namespace. Store command output with cluster name, timestamp, reviewer, and ticket link so the evidence remains meaningful later.

</details>

### Success Criteria

- [ ] Your scope statement names which namespaces contain payment, health, personal, or non-regulated data.
- [ ] Your control map connects each Kubernetes control to at least two framework requirements where appropriate.
- [ ] Your default posture diagnosis explains why flat networking, broad service accounts, unencrypted Secrets, weak audit retention, and unscanned images create compliance risk.
- [ ] Your evidence checklist separates design evidence from operating evidence.
- [ ] Your final recommendation explains why shared controls reduce duplicate work without ignoring framework-specific obligations.

## Sources

- [PCI Security Standards Council: PCI DSS v4.0.1 standard](https://docs.pcisecuritystandards.org/PCI%20DSS/Standard/PCI-DSS-v4_0_1.pdf)
- [U.S. HHS: HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [U.S. HHS: HIPAA Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)
- [AICPA and CIMA: SOC suite of services](https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services)
- [EUR-Lex: General Data Protection Regulation](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [European Commission: Data protection rules](https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations_en)
- [Kubernetes documentation: Security concepts](https://kubernetes.io/docs/concepts/security/)
- [Kubernetes documentation: RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)
- [Kubernetes documentation: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes documentation: Encrypting confidential data at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Kubernetes documentation: Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [Kubernetes documentation: Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Center for Internet Security: Kubernetes Benchmarks](https://www.cisecurity.org/benchmark/kubernetes)

## Next Module

Continue with [Module 6.2: CIS Benchmarks](../module-6.2-cis-benchmarks/) to learn how CIS Kubernetes Benchmark checks turn hardening guidance into repeatable technical assessment evidence.
