---
title: "Module 0.1: KCSA Exam Overview"
slug: k8s/kcsa/part0-introduction/module-0.1-kcsa-overview
sidebar:
  order: 2
---
> **Complexity**: `[QUICK]` - Essential orientation
>
> **Time to Complete**: 15-20 minutes
>
> **Prerequisites**: None - this is your starting point!

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the KCSA exam format, domains, and how it fits in the Kubernetes certification path
2. **Evaluate** your readiness by mapping current skills against the six KCSA exam domains
3. **Compare** KCSA scope with KCNA (general knowledge) and CKS (hands-on security specialist)
4. **Design** a study plan that prioritizes high-weight security domains

---

## Why This Module Matters

The KCSA (Kubernetes and Cloud Native Security Associate) fills a crucial gap in the Kubernetes certification landscape. Before KCSA, you had to choose between general knowledge (KCNA) or jump straight into hands-on security specialist work (CKS). Now there's a bridge.

KCSA is perfect for:
- Security professionals entering the Kubernetes space
- Developers who need security awareness
- Compliance and audit professionals
- Anyone preparing for CKS
- IT professionals responsible for cloud native security

---

## What is KCSA?

```
┌─────────────────────────────────────────────────────────────┐
│           KUBERNETES SECURITY CERTIFICATION PATH            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENTRY LEVEL (Multiple Choice)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  KCNA - Kubernetes and Cloud Native Associate       │   │
│  │  • General Kubernetes concepts                      │   │
│  │  • Cloud native fundamentals                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  KCSA - Kubernetes and Cloud Native Security Assoc ←│   │
│  │  • Security concepts and principles            YOU  │   │
│  │  • Threat modeling and defense                 ARE  │   │
│  │  • Compliance frameworks                       HERE │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│  PROFESSIONAL LEVEL (Hands-On)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  CKS - Certified Kubernetes Security Specialist     │   │
│  │  • Hands-on security implementation                 │   │
│  │  • Requires active CKA certification                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Exam Format

| Aspect | Details |
|--------|---------|
| **Duration** | 90 minutes |
| **Questions** | ~60 multiple choice |
| **Passing Score** | 75% (~45 correct answers) |
| **Format** | Online proctored |
| **Prerequisites** | None |
| **Validity** | 3 years |

### Key Difference from CKS

| Aspect | KCSA | CKS |
|--------|------|-----|
| Format | Multiple choice | Hands-on CLI |
| Focus | Security concepts | Security implementation |
| Skills tested | Understanding threats & defenses | Configuring security |
| Prerequisites | None | Active CKA |
| Duration | 90 min | 120 min |

---

## Exam Domains

```
┌─────────────────────────────────────────────────────────────┐
│              KCSA DOMAIN WEIGHTS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cluster Component Security    ██████████████████████ 22%  │
│  API server, etcd, kubelet, networking                      │
│                                                             │
│  Security Fundamentals         ██████████████████████ 22%  │
│  RBAC, Secrets, Pod Security, Network Policies              │
│                                                             │
│  Kubernetes Threat Model       ████████████████░░░░░ 16%   │
│  Attack surfaces, vulnerabilities, container escape         │
│                                                             │
│  Platform Security             ████████████████░░░░░ 16%   │
│  Image security, admission control, runtime                 │
│                                                             │
│  Cloud Native Security         ███████████░░░░░░░░░░ 14%   │
│  The 4 Cs, shared responsibility, principles                │
│                                                             │
│  Compliance Frameworks         ██████████░░░░░░░░░░░ 10%   │
│  CIS Benchmarks, NIST, assessment                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Where to Focus

**44% of the exam** comes from two domains:
- Kubernetes Cluster Component Security (22%)
- Kubernetes Security Fundamentals (22%)

Master these, and you're nearly halfway there.

---

## What KCSA Tests

### You Need to Know

```
┌─────────────────────────────────────────────────────────────┐
│              KCSA KNOWLEDGE AREAS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONCEPTS (What is it?)                                    │
│  ├── What are the 4 Cs of cloud native security?          │
│  ├── What is defense in depth?                            │
│  ├── What is the principle of least privilege?            │
│  └── What is a security context?                          │
│                                                             │
│  THREATS (What can go wrong?)                              │
│  ├── What are Kubernetes attack surfaces?                  │
│  ├── How can containers escape?                            │
│  ├── What supply chain risks exist?                        │
│  └── What misconfigurations are common?                    │
│                                                             │
│  DEFENSES (How do we protect?)                             │
│  ├── How does RBAC work?                                   │
│  ├── What do Network Policies do?                          │
│  ├── How do admission controllers help?                    │
│  └── What is Pod Security Standards?                       │
│                                                             │
│  COMPLIANCE (How do we prove it?)                          │
│  ├── What are CIS Benchmarks?                              │
│  ├── What is NIST?                                         │
│  └── How do we assess security posture?                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### You Don't Need to Know

- Exact kubectl commands for security configuration
- YAML manifest details
- Complex troubleshooting procedures
- Tool-specific command-line syntax

---

## Sample Questions

Here's what KCSA questions look like:

### Question 1
**Which of the following represents the 4 Cs of cloud native security in the correct order from outermost to innermost?**
- A) Container, Code, Cloud, Cluster
- B) Cloud, Cluster, Container, Code
- C) Code, Container, Cluster, Cloud
- D) Cluster, Cloud, Code, Container

<details>
<summary>Answer</summary>
B) Cloud, Cluster, Container, Code. Security layers from outermost (infrastructure) to innermost (application).
</details>

### Question 2
**What Kubernetes feature restricts which users or service accounts can perform actions on cluster resources?**
- A) Network Policies
- B) Pod Security Admission
- C) RBAC (Role-Based Access Control)
- D) SecurityContext

<details>
<summary>Answer</summary>
C) RBAC (Role-Based Access Control). RBAC controls who can do what in the cluster through Roles and RoleBindings.
</details>

### Question 3
**A container running as root with hostPID: true poses what primary risk?**
- A) Network bandwidth consumption
- B) Container escape and host compromise
- C) Excessive CPU usage
- D) Storage capacity issues

<details>
<summary>Answer</summary>
B) Container escape and host compromise. These settings allow the container to access host processes, enabling potential escape.
</details>

---

## Did You Know?

- **KCSA bridges the gap** between KCNA and CKS. You don't need hands-on experience to validate your security knowledge.

- **Security is everyone's job** - KCSA recognizes that developers, operators, and managers all need security awareness, not just security specialists.

- **75% pass rate** means you can miss about 15 questions and still pass. Focus on understanding concepts, not memorizing details.

- **No prerequisites** - Unlike CKS which requires CKA, anyone can attempt KCSA. It's truly entry-level.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Focusing on commands | KCSA tests concepts, not CLI | Study "what" and "why," not "how to type" |
| Ignoring threat model | 16% of exam is about threats | Think like an attacker |
| Skipping compliance | 10% is frameworks and benchmarks | Learn CIS and NIST basics |
| Not connecting concepts | Security is layered | Understand how defenses work together |
| Rushing through questions | Security questions have subtle wording | Read every option carefully |

---

## Quiz

1. **How long is the KCSA exam?**
   <details>
   <summary>Answer</summary>
   90 minutes for approximately 60 multiple choice questions.
   </details>

2. **What percentage of the exam covers Kubernetes Security Fundamentals?**
   <details>
   <summary>Answer</summary>
   22% - tied with Cluster Component Security as the largest domain.
   </details>

3. **What's the minimum passing score for KCSA?**
   <details>
   <summary>Answer</summary>
   75%. You need to answer approximately 45 out of 60 questions correctly.
   </details>

4. **Does KCSA require CKA as a prerequisite?**
   <details>
   <summary>Answer</summary>
   No. KCSA has no prerequisites, unlike CKS which requires an active CKA.
   </details>

5. **Is KCSA a hands-on or multiple choice exam?**
   <details>
   <summary>Answer</summary>
   Multiple choice. You won't use a terminal or configure anything during the exam.
   </details>

---

## Curriculum Structure

This curriculum follows the exam domains:

| Part | Domain | Weight | Modules |
|------|--------|--------|---------|
| 0 | Introduction | - | Exam overview, security mindset |
| 1 | Overview of Cloud Native Security | 14% | 4 Cs, cloud provider, principles |
| 2 | Cluster Component Security | 22% | Control plane, nodes, network, PKI |
| 3 | Security Fundamentals | 22% | RBAC, secrets, pod security, network policies |
| 4 | Threat Model | 16% | Attack surfaces, vulnerabilities, supply chain |
| 5 | Platform Security | 16% | Images, admission, runtime, audit |
| 6 | Compliance Frameworks | 10% | CIS, NIST, assessment |

---

## Summary

**KCSA validates your security knowledge** for Kubernetes and cloud native:

- **Format**: 90 minutes, ~60 multiple choice, 75% to pass
- **Focus**: Security concepts, threats, and defenses
- **Biggest domains**: Cluster Components (22%) and Security Fundamentals (22%)
- **Study approach**: Understand threats, know defenses, think in layers

**KCSA prepares you for CKS**:
- Learn the "why" before the "how"
- Understand threats before configuring defenses
- Build security intuition through concepts

---

## Next Module

[Module 0.2: Security Mindset](../module-0.2-security-mindset/) - How to think like a security professional and approach security questions strategically.
