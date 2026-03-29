---
title: "Module 0.1: KCNA Exam Overview"
slug: k8s/kcna/part0-introduction/module-0.1-kcna-overview
sidebar:
  order: 2
---
> **Complexity**: `[QUICK]` - Essential orientation
>
> **Time to Complete**: 15-20 minutes
>
> **Prerequisites**: None - this is your starting point!

---

## Why This Module Matters

The KCNA (Kubernetes and Cloud Native Associate) is the **entry point** to Kubernetes certifications. Unlike CKA or CKAD, it's a multiple-choice exam testing your conceptual understanding—not your ability to type kubectl commands under pressure.

This makes it perfect for:
- Managers who need to understand Kubernetes
- Developers new to cloud native
- Anyone starting their Kubernetes journey
- IT professionals transitioning to cloud native

---

## What is KCNA?

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CERTIFICATION PATH                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENTRY LEVEL (Multiple Choice)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  KCNA - Kubernetes and Cloud Native Associate       │   │
│  │  • Concepts and fundamentals                        │   │
│  │  • No hands-on required                             │   │
│  │  • Great starting point                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│  PROFESSIONAL LEVEL (Hands-On)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    CKA      │  │    CKAD     │  │    CKS      │        │
│  │ Administrator│  │  Developer  │  │  Security   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ALSO ENTRY LEVEL                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  KCSA - Kubernetes and Cloud Native Security Assoc  │   │
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

### Key Difference from CKA/CKAD/CKS

| Aspect | KCNA | CKA/CKAD/CKS |
|--------|------|--------------|
| Format | Multiple choice | Hands-on CLI |
| Focus | Concepts | Implementation |
| Skills tested | Understanding | Doing |
| Time pressure | Moderate | High |
| Documentation | Not allowed | Allowed |

---

## Exam Domains

```
┌─────────────────────────────────────────────────────────────┐
│              KCNA DOMAIN WEIGHTS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Kubernetes Fundamentals       ██████████████████████ 46%  │
│  Pods, Deployments, Services, Architecture                  │
│                                                             │
│  Container Orchestration       ██████████░░░░░░░░░░░ 22%   │
│  Scheduling, scaling, service discovery                     │
│                                                             │
│  Cloud Native Architecture     ████████░░░░░░░░░░░░░ 16%   │
│  Principles, CNCF, serverless                               │
│                                                             │
│  Cloud Native Observability    ████░░░░░░░░░░░░░░░░░ 8%    │
│  Monitoring, logging, Prometheus                            │
│                                                             │
│  Application Delivery          ████░░░░░░░░░░░░░░░░░ 8%    │
│  CI/CD, GitOps, Helm                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Where to Focus

**68% of the exam** comes from two domains:
- Kubernetes Fundamentals (46%)
- Container Orchestration (22%)

Master these, and you're most of the way there.

---

## What KCNA Tests

### You Need to Know

```
┌─────────────────────────────────────────────────────────────┐
│              KCNA KNOWLEDGE AREAS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONCEPTS (What is it?)                                    │
│  ├── What is a Pod?                                        │
│  ├── What is a Deployment?                                 │
│  ├── What does the control plane do?                       │
│  └── What is cloud native?                                 │
│                                                             │
│  RELATIONSHIPS (How do things connect?)                    │
│  ├── How do Services find Pods?                            │
│  ├── How does scheduling work?                             │
│  └── How do containers relate to Pods?                     │
│                                                             │
│  PURPOSE (Why use it?)                                     │
│  ├── Why use Kubernetes over VMs?                          │
│  ├── Why use Deployments over Pods?                        │
│  └── Why is observability important?                       │
│                                                             │
│  ECOSYSTEM (What tools exist?)                             │
│  ├── What is Prometheus for?                               │
│  ├── What is Helm?                                         │
│  └── What projects are in CNCF?                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### You Don't Need to Know

- Exact kubectl command syntax
- YAML manifest details
- Troubleshooting procedures
- Production configuration

---

## Study Approach

Since KCNA is conceptual, your study approach differs from hands-on exams:

### Do This

1. **Understand the "why"** - Know why each concept exists
2. **Learn vocabulary** - Know what terms mean
3. **Study diagrams** - Visualize architecture
4. **Take practice quizzes** - Multiple choice practice
5. **Explore CNCF landscape** - Know major projects

### Don't Do This

- Don't memorize kubectl commands
- Don't spend hours on YAML syntax
- Don't build complex clusters
- Don't stress about edge cases

---

## Sample Questions

Here's what KCNA questions look like:

### Question 1
**What is the smallest deployable unit in Kubernetes?**
- A) Container
- B) Pod
- C) Deployment
- D) Node

<details>
<summary>Answer</summary>
B) Pod. While containers run inside Pods, the Pod is the smallest unit Kubernetes manages.
</details>

### Question 2
**Which component is responsible for scheduling Pods to nodes?**
- A) kubelet
- B) kube-proxy
- C) kube-scheduler
- D) etcd

<details>
<summary>Answer</summary>
C) kube-scheduler. It watches for newly created Pods and assigns them to nodes.
</details>

### Question 3
**What does CNCF stand for?**
- A) Cloud Native Computing Foundation
- B) Container Network Configuration Framework
- C) Cloud Networking and Container Federation
- D) Container Native Cloud Foundation

<details>
<summary>Answer</summary>
A) Cloud Native Computing Foundation. CNCF hosts Kubernetes and other cloud native projects.
</details>

---

## Did You Know?

- **KCNA launched in 2021** as the first entry-level Kubernetes certification. Before that, CKA was the only option.

- **75% pass rate requirement** means you can miss about 15 questions and still pass. That's more forgiving than CKA's 66%.

- **No hands-on means no kubectl** - You won't type a single command during the exam. It's all reading and selecting answers.

- **The exam changes** - A curriculum update is coming November 2025. Stay current with CNCF announcements.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Over-preparing technically | Wasted time on kubectl | Focus on concepts |
| Ignoring CNCF ecosystem | Missing 16%+ of questions | Study the landscape |
| Not practicing multiple choice | Different skill than hands-on | Take practice tests |
| Rushing through questions | Missing subtle wording | Read carefully |
| Skipping cloud native principles | Fundamental to 16% of exam | Understand 12-factor apps |

---

## Quiz

1. **How long is the KCNA exam?**
   <details>
   <summary>Answer</summary>
   90 minutes for approximately 60 multiple choice questions.
   </details>

2. **What percentage of the exam covers Kubernetes Fundamentals?**
   <details>
   <summary>Answer</summary>
   46% - nearly half the exam. This is where you should focus most study time.
   </details>

3. **What's the minimum passing score for KCNA?**
   <details>
   <summary>Answer</summary>
   75%. You need to answer approximately 45 out of 60 questions correctly.
   </details>

4. **Is KCNA a hands-on or multiple choice exam?**
   <details>
   <summary>Answer</summary>
   Multiple choice. Unlike CKA, CKAD, and CKS, you won't use a terminal or type commands.
   </details>

---

## Curriculum Structure

This curriculum follows the exam domains:

| Part | Domain | Weight | Modules |
|------|--------|--------|---------|
| 0 | Introduction | - | Exam overview, study strategy |
| 1 | Kubernetes Fundamentals | 46% | Core concepts, architecture |
| 2 | Container Orchestration | 22% | Scheduling, scaling, services |
| 3 | Cloud Native Architecture | 16% | Principles, CNCF, serverless |
| 4 | Cloud Native Observability | 8% | Monitoring, logging |
| 5 | Application Delivery | 8% | CI/CD, GitOps, Helm |

---

## Summary

**KCNA is your entry point** to Kubernetes certification:

- **Format**: 90 minutes, ~60 multiple choice, 75% to pass
- **Focus**: Concepts over commands
- **Biggest domain**: Kubernetes Fundamentals (46%)
- **Study approach**: Understand "why," learn vocabulary, explore ecosystem

**This is different from CKA/CKAD/CKS**:
- No terminal access
- No kubectl commands
- No YAML writing
- Pure conceptual understanding

---

## Next Module

[Module 0.2: Study Strategy](../module-0.2-study-strategy/) - How to effectively prepare for a multiple-choice Kubernetes exam.
