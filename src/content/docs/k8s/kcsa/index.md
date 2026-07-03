---
title: "KCSA Curriculum"
sidebar:
  order: 1
  label: "KCSA"
---
> **Kubernetes and Cloud Native Security Associate** - Entry-level certification for cloud native security fundamentals

## About KCSA

The KCSA is a **multiple-choice exam** (not hands-on) that validates foundational knowledge of Kubernetes security and cloud native security concepts. It bridges the gap between general Kubernetes knowledge (KCNA/CKA) and specialist security skills (CKS).

| Aspect | Details |
|--------|---------|
| **Format** | Multiple choice |
| **Duration** | 90 minutes |
| **Questions** | ~60 questions |
| **Passing Score** | 75% |
| **Validity** | 2 years |
| **Prerequisites** | None (CKA knowledge helpful) |

## Curriculum Structure

| Part | Topic | Weight | Modules |
|------|-------|--------|---------|
| [Part 0](part0-introduction/) | Introduction | - | 2 |
| [Part 1](part1-cloud-native-security/) | Overview of Cloud Native Security | 14% | 3 |
| [Part 2](part2-cluster-component-security/) | Kubernetes Cluster Component Security | 22% | 4 |
| [Part 3](part3-security-fundamentals/) | Kubernetes Security Fundamentals | 22% | 5 |
| [Part 4](part4-threat-model/) | Kubernetes Threat Model | 16% | 5 |
| [Part 5](part5-platform-security/) | Platform Security | 16% | 4 |
| [Part 6](part6-compliance/) | Compliance and Security Frameworks | 10% | 3 |
| **Total** | | **100%** | **26** |

## Module Overview

### Part 0: Introduction (2 modules)
- [0.1 KCSA Overview](part0-introduction/module-0.1-kcsa-overview/) - Exam format and domains
- [0.2 Security Mindset](part0-introduction/module-0.2-security-mindset/) - Thinking like a security professional

### Part 1: Overview of Cloud Native Security - 14% (3 modules)
- [1.1 The 4 Cs of Cloud Native Security](part1-cloud-native-security/module-1.1-four-cs/) - Cloud, Cluster, Container, Code
- [1.2 Cloud Provider Security](part1-cloud-native-security/module-1.2-cloud-provider-security/) - Shared responsibility model
- [1.3 Security Principles](part1-cloud-native-security/module-1.3-security-principles/) - Defense in depth, least privilege

### Part 2: Kubernetes Cluster Component Security - 22% (4 modules)
- [2.1 Control Plane Security](part2-cluster-component-security/module-2.1-control-plane-security/) - API server, etcd, scheduler
- [2.2 Node Security](part2-cluster-component-security/module-2.2-node-security/) - kubelet, container runtime
- [2.3 Network Security](part2-cluster-component-security/module-2.3-network-security/) - CNI, service mesh basics
- [2.4 PKI and Certificates](part2-cluster-component-security/module-2.4-pki-certificates/) - Certificate management

### Part 3: Kubernetes Security Fundamentals - 22% (5 modules)
- [3.1 Pod Security](part3-security-fundamentals/module-3.1-pod-security/) - SecurityContext, Pod Security Standards
- [3.2 RBAC Fundamentals](part3-security-fundamentals/module-3.2-rbac/) - Roles, bindings, best practices
- [3.3 Secrets Management](part3-security-fundamentals/module-3.3-secrets/) - Secret types and handling
- [3.4 ServiceAccount Security](part3-security-fundamentals/module-3.4-serviceaccounts/) - Identity and tokens
- [3.5 Network Policies](part3-security-fundamentals/module-3.5-network-policies/) - Traffic control

### Part 4: Kubernetes Threat Model - 16% (5 modules)
- [4.1 Attack Surfaces](part4-threat-model/module-4.1-attack-surfaces/) - Where vulnerabilities exist
- [4.2 Common Vulnerabilities](part4-threat-model/module-4.2-vulnerabilities/) - CVEs and misconfigurations
- [4.3 Container Escape](part4-threat-model/module-4.3-container-escape/) - Breakout scenarios
- [4.4 Supply Chain Threats](part4-threat-model/module-4.4-supply-chain/) - Image and dependency risks
- [4.5 Threat Modeling & Supply Chain Theory](part4-threat-model/module-4.5-threat-modeling-supply-chain-theory/) - Supply chain threat analysis

### Part 5: Platform Security - 16% (4 modules)
- [5.1 Image Security](part5-platform-security/module-5.1-image-security/) - Scanning and signing
- [5.2 Observability](part5-platform-security/module-5.2-observability/) - Security monitoring
- [5.3 Runtime Security](part5-platform-security/module-5.3-runtime-security/) - Detection and response
- [5.4 Security Tooling](part5-platform-security/module-5.4-security-tooling/) - Tools ecosystem

### Part 6: Compliance and Security Frameworks - 10% (3 modules)
- [6.1 Compliance Frameworks](part6-compliance/module-6.1-compliance-frameworks/) - PCI-DSS, HIPAA, SOC 2
- [6.2 CIS Benchmarks](part6-compliance/module-6.2-cis-benchmarks/) - Kubernetes CIS benchmark
- [6.3 Security Assessments](part6-compliance/module-6.3-security-assessments/) - Audits and testing

## How to Use This Curriculum

1. **Follow the order** - Modules build on security concepts progressively
2. **Think "defense in depth"** - Layer security at every level
3. **Understand threats first** - Know what you're defending against
4. **Take quizzes** - Each module has quiz questions
5. **Connect to CKS** - This prepares you for hands-on security skills

## KCSA vs Other Certifications

| Aspect | KCSA | KCNA | CKS |
|--------|------|------|-----|
| Focus | Security concepts | General K8s concepts | Security implementation |
| Format | Multiple choice | Multiple choice | Hands-on |
| Difficulty | Associate | Associate | Specialist |
| Prerequisites | None | None | Active CKA |

## Key Study Tips

- **Master the 4 Cs** - Cloud, Cluster, Container, Code frame everything
- **Think like an attacker** - Understand threats to defend against them
- **Know security principles** - Defense in depth, least privilege, zero trust
- **Understand components** - Know what each K8s component does and its risks
- **Focus on Part 2 & 3** - They're 44% of the exam combined

## Relationship to CKS

KCSA is the **conceptual foundation** for CKS:

```
KCSA (Concepts)          CKS (Implementation)
──────────────           ────────────────────
"What is RBAC?"     →    "Configure RBAC for service X"
"Why use PSS?"      →    "Apply restricted PSS to namespace"
"What is Falco?"    →    "Write Falco rules for detection"
```

If you pass KCSA and CKA, you're well-prepared to tackle CKS.

## Start Learning

Begin with [Part 0: Introduction](part0-introduction/module-0.1-kcsa-overview/) to understand the exam format and security mindset, then proceed through each part in order.

Good luck on your KCSA journey!
