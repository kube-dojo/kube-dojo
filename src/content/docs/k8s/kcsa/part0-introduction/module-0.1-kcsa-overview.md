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

**The Real-World Cost of Knowledge Gaps**
Consider a common industry scenario: A development team quickly deployed a new microservice to production. Lacking foundational Kubernetes security knowledge, they left the default service account token mounted in their pods and did not implement network policies. When an attacker found a simple vulnerability in their application code, they used that default token to query the Kubernetes API, discover other services, and move laterally across the cluster. This was not an advanced zero-day exploit; it was a basic misconfiguration that could have been easily avoided. The KCSA curriculum is designed exactly to prevent this scenario by ensuring everyone interacting with the cluster understands the threat landscape and baseline defenses, demonstrating the practical field value of the certification beyond just passing a test.

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

> **Stop and think**: Looking at the domain weights, if you only had two weeks to prepare, which domains would you prioritize and why? Consider both the weight percentages and how the domains build on each other.

### Self-Assessment: Where Do You Stand?

Before diving in, take a moment to map your current experience against the six KCSA domains. Ask yourself:
- **Cluster Component Security (22%)**: Have I ever configured or secured the Kubernetes API server, etcd, or kubelet?
- **Security Fundamentals (22%)**: Do I regularly write RBAC roles, manage Kubernetes Secrets, or define Network Policies?
- **Kubernetes Threat Model (16%)**: Can I explain how a container escape happens or identify common Kubernetes attack surfaces?
- **Platform Security (16%)**: Have I worked with image scanners, admission controllers (like OPA Gatekeeper), or runtime security tools?
- **Cloud Native Security (14%)**: Am I familiar with the 4 Cs of cloud native security and the shared responsibility model?
- **Compliance Frameworks (10%)**: Have I ever run a CIS Benchmark assessment or mapped controls to NIST frameworks?

> **Pause and predict**: Based on your answers above, which two domains will require the most study time for you personally?

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

> **Pause and predict**: The KCSA is multiple-choice while CKS is hands-on. How does this difference change what you need to study? What depth of understanding is "enough" for a concept-based security exam?

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

1. **A colleague holds a CKA certification and asks whether they should skip KCSA and go straight to CKS. What would you advise, and why?**
   <details>
   <summary>Answer</summary>
   It depends on their security knowledge. CKS focuses on hands-on security implementation and requires an active CKA, which they have. However, KCSA covers security concepts, threat modeling, and compliance frameworks that CKS does not emphasize. If they lack a strong security conceptual foundation — understanding threats, the 4 Cs model, and compliance — KCSA would fill that gap. CKS tests "how to configure," while KCSA tests "why this matters and what could go wrong."
   </details>

2. **You have 90 minutes and roughly 60 questions on exam day. After 45 minutes you've answered 25 questions. Should you be worried? What strategy would you apply for the remaining time?**
   <details>
   <summary>Answer</summary>
   At that pace you'd finish about 55 questions, which is slightly behind. The three-pass strategy helps: use the first pass for quick, confident answers (1-2 min each), mark harder questions for a second pass (3-4 min each), and use remaining time for any questions you flagged. Since the passing score is 75% (~45 correct), you can afford to miss about 15 questions. Focus on answering the ones you know well rather than spending too long on uncertain ones.
   </details>

3. **The two highest-weighted KCSA domains together account for 44% of the exam. A study group member suggests ignoring the 10% Compliance domain entirely. Is this a sound strategy?**
   <details>
   <summary>Answer</summary>
   No. With a 75% passing threshold, every domain matters. The 10% Compliance domain represents roughly 6 questions — ignoring them means you'd need to score nearly perfectly on everything else. A better approach is to spend proportionally more time on the 22% domains (Cluster Components and Security Fundamentals) while still covering Compliance at a conceptual level. The domains also reinforce each other: understanding compliance frameworks helps contextualize why specific security controls exist.
   </details>

4. **Your team wants to validate that all members understand Kubernetes security basics before working on a production cluster. Which certification would you recommend and why — KCNA, KCSA, or CKS?**
   <details>
   <summary>Answer</summary>
   KCSA is the best fit. KCNA covers general Kubernetes knowledge but lacks security depth. CKS requires hands-on security implementation skills and a CKA prerequisite, which is overkill for baseline awareness. KCSA validates understanding of security concepts, threats, defenses, and compliance without requiring CLI expertise — exactly the "security awareness" level appropriate for team members who work with production clusters.
   </details>

5. **A KCSA exam question asks about a security concept you've never encountered. You can eliminate two of the four options. What reasoning approach should you use to choose between the remaining two?**
   <details>
   <summary>Answer</summary>
   Apply core security principles: choose the option that follows least privilege (most restrictive access), defense in depth (multiple layers), or default-deny (block unless explicitly allowed). KCSA questions are designed to test security thinking, so the "more secure" option that limits exposure is usually correct. Also consider which C layer (Cloud, Cluster, Container, Code) the question targets — the answer should address the correct layer.
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