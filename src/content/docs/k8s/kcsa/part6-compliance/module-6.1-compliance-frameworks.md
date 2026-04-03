---
title: "Module 6.1: Compliance Frameworks"
slug: k8s/kcsa/part6-compliance/module-6.1-compliance-frameworks
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Conceptual knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 5.4: Security Tooling](../part5-platform-security/module-5.4-security-tooling/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Identify** major compliance frameworks (SOC 2, PCI DSS, HIPAA, GDPR) and their Kubernetes relevance
2. **Evaluate** how Kubernetes security controls map to specific compliance requirements
3. **Assess** the gap between Kubernetes default configuration and compliance-ready posture
4. **Explain** how to demonstrate compliance through audit trails, access controls, and encryption

---

## Why This Module Matters

Compliance frameworks define security requirements for specific industries and data types. Understanding these frameworks helps you implement appropriate controls in Kubernetes and demonstrate that your systems meet regulatory requirements.

KCSA tests your awareness of major compliance frameworks and how they apply to Kubernetes environments.

---

## What is Compliance?

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

---

## Major Compliance Frameworks

### PCI-DSS

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

### PCI-DSS in Kubernetes

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

### HIPAA

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

### SOC 2

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

### GDPR

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

---

## Framework Comparison

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

---

## Implementing Compliance in Kubernetes

### Common Control Categories

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

### Evidence Collection

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

---

## Compliance Automation

### Policy as Code

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

### Continuous Compliance

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

---

## Did You Know?

- **PCI-DSS Level 1** requires external audits for merchants processing over 6 million transactions annually. Level 4 merchants (under 20,000) can self-assess.

- **HIPAA has no certification**—unlike PCI-DSS, there's no official HIPAA certification. Organizations must self-attest to compliance.

- **SOC 2 Type II** is often more valuable than Type I because it demonstrates controls were effective over time, not just at a point in time.

- **GDPR fines have exceeded €1 billion** since enforcement began, with Amazon receiving the largest single fine of €746 million.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Treating compliance as checkbox | Missing real security | Use frameworks as foundation |
| Point-in-time compliance | Drift between audits | Continuous monitoring |
| Manual evidence collection | Slow, incomplete | Automate evidence gathering |
| Ignoring framework overlap | Duplicate work | Map controls across frameworks |
| No compliance ownership | Gaps and confusion | Assign clear responsibility |

---

## Quiz

1. **What's the difference between regulatory and voluntary compliance?**
   <details>
   <summary>Answer</summary>
   Regulatory compliance is required by law (HIPAA, GDPR)—non-compliance can result in fines or legal action. Voluntary compliance (SOC2, ISO 27001) is chosen by organizations to demonstrate security to customers or meet contractual requirements.
   </details>

2. **Why is compliance not the same as security?**
   <details>
   <summary>Answer</summary>
   Compliance is the minimum bar defined by a framework. It may not cover all threats relevant to your environment. A compliant system can still be insecure if it only meets minimum requirements. Security requires going beyond compliance to address specific risks.
   </details>

3. **What are the five SOC 2 Trust Service Criteria?**
   <details>
   <summary>Answer</summary>
   Security (required), Availability, Processing Integrity, Confidentiality, and Privacy. Only Security is required; organizations choose additional criteria based on their services and customer needs.
   </details>

4. **How does Kubernetes help with PCI-DSS compliance?**
   <details>
   <summary>Answer</summary>
   Kubernetes provides controls for network segmentation (Network Policies), access control (RBAC), encryption (Secrets encryption, TLS), monitoring (audit logging), and vulnerability management (image scanning). These map to PCI-DSS requirements for protecting cardholder data.
   </details>

5. **What is continuous compliance?**
   <details>
   <summary>Answer</summary>
   Continuous compliance uses automated tools to continuously check and enforce compliance controls, rather than relying on periodic audits. It includes policy as code, automated scanning, drift detection, and real-time alerting on violations.
   </details>

---

## Hands-On Exercise: Compliance Mapping

**Scenario**: Map these Kubernetes controls to compliance framework requirements:

**Controls:**
1. RBAC with least privilege roles
2. API server audit logging enabled
3. Secrets encrypted at rest with KMS
4. Network Policies enforcing segmentation
5. Container images scanned for vulnerabilities

**Map to frameworks:**

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

---

## Summary

Compliance frameworks provide security requirements for different industries:

| Framework | Focus | Key Requirements |
|-----------|-------|-----------------|
| **PCI-DSS** | Payment data | Network segmentation, encryption, access control |
| **HIPAA** | Health data | Technical safeguards, audit controls, breach notification |
| **SOC 2** | Service orgs | Trust criteria (security, availability, etc.) |
| **GDPR** | Personal data | Data protection, subject rights, breach notification |

Key principles:
- Compliance is the minimum bar, not the goal
- Implement continuous compliance through automation
- Map controls across frameworks to reduce duplicate work
- Collect evidence automatically
- Use policy as code for consistent enforcement

---

## Next Module

[Module 6.2: CIS Benchmarks](../module-6.2-cis-benchmarks/) - Understanding and implementing CIS Kubernetes Benchmark.
