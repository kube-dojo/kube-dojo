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

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the KCNA exam format, question types, and passing criteria
2. **Identify** the five exam domains and their relative weight in scoring
3. **Compare** KCNA with CKA, CKAD, and other Kubernetes certifications
4. **Evaluate** your current knowledge gaps against the KCNA curriculum

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

> **Pause and predict**: Given that Kubernetes Fundamentals is worth 46% and Container Orchestration is worth 22%, how would you structure a two-week study plan to maximize your score? What would you study first, and why?

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

> **Stop and think**: KCNA is multiple-choice while CKA/CKAD/CKS are hands-on. How does this change what you need to study? If you can recognize the right answer but cannot recall it from memory, is that enough for KCNA? What about for CKA?

## Sample Questions

Here's what KCNA questions look like:

### Question 1
**Scenario:** Your development team wants to deploy a new microservices application. They need a way to ensure that if a container crashes, it automatically restarts, and they want to easily scale the number of replicas. Which Kubernetes resource should they use to manage these requirements?
- A) Pod
- B) Deployment
- C) Service
- D) Ingress

<details>
<summary>Answer</summary>
B) Deployment. While a Pod is the smallest deployable unit, it does not self-heal or scale on its own. A Deployment manages Pods, providing self-healing (restarting crashed containers) and easy scaling of replicas.
</details>

### Question 2
**Scenario:** You have a web application running in a Kubernetes cluster across multiple Pods. You need to provide a single, stable IP address that other internal services can use to communicate with this web application, even as individual Pods are created or destroyed. Which component provides this capability?
- A) Ingress
- B) Service
- C) Kube-proxy
- D) NodePort

<details>
<summary>Answer</summary>
B) Service. A Service provides a stable, abstract IP address and DNS name that load balances traffic across a dynamic set of Pods. While Ingress handles external access and Kube-proxy implements the routing rules, the Service itself is the resource that provides the stable internal IP.
</details>

### Question 3
**Scenario:** Your organization is adopting cloud-native practices and wants to ensure their applications are portable, scalable, and loosely coupled. Which set of principles should they follow to best align with the Cloud Native Computing Foundation (CNCF) definition?
- A) Building monolithic applications optimized for a single cloud provider.
- B) Utilizing microservices, containers, and declarative APIs.
- C) Relying strictly on virtual machines and manual deployment scripts.
- D) Using proprietary orchestration tools without open-source components.

<details>
<summary>Answer</summary>
B) Utilizing microservices, containers, and declarative APIs. The CNCF defines cloud-native systems as those that use open source software stack to be containerized, dynamically orchestrated, and microservices-oriented. This approach ensures applications are resilient, manageable, and observable.
</details>

### Question 4 (Worked Elimination Example)
**Scenario:** An application is experiencing high latency. You need to understand the flow of requests and identify where the bottleneck is occurring across multiple microservices. Which category of CNCF tools should you investigate?
- A) Container Registries
- B) Distributed Tracing
- C) Continuous Integration
- D) Service Proxy

<details>
<summary>Answer and Elimination Strategy</summary>
B) Distributed Tracing.

*Elimination process:*
- *A is incorrect:* Container registries store images, they don't monitor live traffic.
- *C is incorrect:* CI tools build and test code, they don't track request latency in production.
- *D is incorrect:* While a service proxy routes traffic, distributed tracing (like Jaeger) is the specific observability category used to track requests across multiple services to find bottlenecks.
</details>

---

## Hands-On Exercise: Mapping Your KCNA Strategy

While the KCNA exam is not hands-on, preparing for it requires active engagement with the curriculum. In this exercise, you will map out the CNCF landscape and align it with the exam domains to create a personalized study foundation.

### Step 1: Explore the CNCF Landscape
1. Open your web browser and navigate to the interactive [CNCF Cloud Native Landscape](https://landscape.cncf.io/).
2. Locate the "Orchestration & Management" section and identify where Kubernetes sits.
3. Find at least three other graduated projects in the landscape (e.g., Prometheus for observability, Helm for application delivery).

### Step 2: Analyze the Exam Syllabus
1. Download the latest official KCNA exam syllabus from the Linux Foundation website.
2. Review the detailed bullet points under each of the five main domains.
3. Highlight any concepts or tools you have never encountered before.

### Step 3: Draft Your Study Plan
1. Create a simple document or spreadsheet with the five exam domains.
2. Based on your syllabus review, assign a confidence score (1-5) to each domain.
3. Allocate your available study hours proportionally, giving the most time to your lowest-scoring domains that have the highest exam weight (like Kubernetes Fundamentals).

### Success Criteria

- [ ] I have successfully navigated the CNCF Landscape and identified Kubernetes' category.
- [ ] I have located three graduated CNCF projects relevant to the KCNA domains (e.g., Observability, App Delivery).
- [ ] I have reviewed the official KCNA syllabus and identified my specific knowledge gaps.
- [ ] I have drafted a study plan that prioritizes the heavily weighted domains (Fundamentals and Orchestration).

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
| Memorizing YAML files | KCNA tests concepts, not syntax | Understand the structure, don't memorize |
| Neglecting Observability & CI/CD | Missing 16% of the exam combined | Review Prometheus, GitOps, and Helm basics |
| Assuming CKA materials work for KCNA | Content is too deep and not broad enough | Use KCNA-specific study materials |

---

## Quiz

1. **A colleague who just passed CKA tells you to spend most of your KCNA study time practicing kubectl commands in a lab cluster. Is this good advice? Why or why not?**
   <details>
   <summary>Answer</summary>
   This is not good advice for KCNA. CKA is a hands-on exam where kubectl fluency is essential, but KCNA is a multiple-choice conceptual exam. You will never type a command during KCNA. Your study time is better spent understanding concepts, relationships between components, and the "why" behind Kubernetes features. Practicing kubectl helps for CKA/CKAD/CKS, but for KCNA, focus on reading, flashcards, and practice quizzes instead.
   </details>

2. **You have exactly two weeks to prepare for KCNA. Your background is in frontend development with no Kubernetes experience. How would you allocate your study time across the five domains to maximize your chances of passing?**
   <details>
   <summary>Answer</summary>
   Allocate roughly proportional to exam weights: spend ~46% of time on Kubernetes Fundamentals (7 days), ~22% on Container Orchestration (3 days), ~16% on Cloud Native Architecture (2 days), and split the remaining time between Observability and Application Delivery (~1 day each). Since you have no K8s background, the fundamentals are both the highest-weighted domain and where you need the most learning. Mastering Fundamentals and Container Orchestration covers 68% of the exam, giving you the best chance of passing the 75% threshold.
   </details>

3. **Your manager asks whether KCNA certification proves you can administer a Kubernetes cluster in production. What would you explain?**
   <details>
   <summary>Answer</summary>
   KCNA proves conceptual understanding, not hands-on ability. It certifies that you understand what Kubernetes is, how its components work, and the cloud native ecosystem. It does not prove you can troubleshoot a production cluster, write YAML manifests, or debug scheduling failures under pressure. For production administration skills, CKA (Certified Kubernetes Administrator) is the appropriate certification. KCNA is an entry point that validates foundational knowledge.
   </details>

4. **A team member scored 73% on a KCNA practice test. They are disappointed and want to reschedule the exam to study more. What factors should they consider?**
   <details>
   <summary>Answer</summary>
   At 73% they are only 2% below the 75% passing threshold, meaning they can miss about 15 questions and still pass. They should analyze which domains they scored lowest in and focus study there. Since Kubernetes Fundamentals alone is 46% of the exam, improving even slightly in that domain could push them over the threshold. Practice tests also tend to be harder than the real exam. Rather than postponing significantly, a few more days of targeted review on weak areas would likely be sufficient.
   </details>

5. **Scenario: Your company is migrating a legacy monolithic application to Kubernetes. A senior engineer suggests putting all components (web server, application logic, and database) into a single large Pod to mimic a Virtual Machine. Is this an anti-pattern, and how does it relate to Kubernetes Fundamentals?**
   <details>
   <summary>Answer</summary>
   Yes, this is an anti-pattern. Kubernetes Fundamentals dictate that Pods should generally contain a single primary application container to ensure proper scaling, resource allocation, and lifecycle management. Bundling everything into one Pod defeats the purpose of distributed container orchestration, as the components cannot scale independently or be updated without restarting the entire stack. A cloud-native approach would separate these into distinct Pods managed by Deployments or StatefulSets.
   </details>

6. **Scenario: During a security audit, an auditor asks how Kubernetes ensures that a compromised container cannot easily bring down the entire node. How does the concept of container orchestration provide isolation, and what KCNA domain covers this?**
   <details>
   <summary>Answer</summary>
   Container orchestration provides isolation by leveraging Linux kernel features like namespaces and cgroups, which restrict what a container can see and use on the host system. This means a compromised container is limited in its access to other processes and system resources. This concept falls under the Container Orchestration and Kubernetes Fundamentals domains of the KCNA exam. Understanding how Kubernetes schedules and isolates workloads is critical for answering questions about security and architecture.
   </details>

7. **Scenario: A developer is confused about why they need to learn about Prometheus and Fluentd for the KCNA exam, stating they are only interested in Kubernetes scheduling. How would you explain the importance of the Cloud Native Observability domain to their overall understanding?**
   <details>
   <summary>Answer</summary>
   While Kubernetes handles orchestration, observability tools like Prometheus (metrics) and Fluentd (logging) are essential for understanding the health and performance of distributed systems. The KCNA exam dedicates 8% of its questions to Cloud Native Observability because running applications in Kubernetes requires knowing when and why things fail. Without observability, a dynamically scaled microservices architecture becomes a black box, making it impossible to troubleshoot issues effectively. Learning these tools conceptually ensures you understand the complete lifecycle of a cloud-native application.
   </details>

8. **Scenario: Your team is adopting GitOps for Application Delivery, but some members still prefer applying YAML files manually using `kubectl`. How does GitOps improve the deployment process, and why is this concept tested on the KCNA exam?**
   <details>
   <summary>Answer</summary>
   GitOps improves the deployment process by making a Git repository the single source of truth for declarative infrastructure and applications. This approach enables automated, auditable, and easily reversible deployments, reducing human error from manual configuration changes. The KCNA exam tests this under the Application Delivery domain (8%) because GitOps is a foundational practice in the modern cloud-native ecosystem. It tightly integrates with CI/CD pipelines to ensure consistent and reliable cluster states across environments.
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