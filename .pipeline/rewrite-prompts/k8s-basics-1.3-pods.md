TASK: Write a complete KubeDojo educational module.

### Module Specification

- **Title**: Module 1.3: Pods - The Atomic Unit
- **File path**: prerequisites/kubernetes-basics/module-1.3-pods.md
- **Complexity**: [MEDIUM]
- **Time to Complete**: 40-45 minutes
- **Prerequisites**: Module 1.2 (kubectl Basics)
- **Next Module**: [Module 1.4: Deployments](/prerequisites/kubernetes-basics/module-1.4-deployments/) — Learn how Kubernetes manages groups of pods

### Topic Coverage

- What a pod really is (not just "a container wrapper" — shared network namespace, shared storage, co-scheduling)
- Why pods exist: the sidecar pattern, init containers, and why Kubernetes doesn't schedule bare containers
- Pod lifecycle in depth: Pending → Running → Succeeded/Failed, with what happens at each transition
- Creating pods imperatively vs declaratively (and why declarative wins)
- Pod spec anatomy: containers, volumes, resource requests/limits, restart policies
- Inspecting pods: kubectl describe, logs, exec, port-forward
- Diagnosing failures: CrashLoopBackOff, ImagePullBackOff, OOMKilled, Pending (no resources)

### Hands-On Exercise Concept

Build a multi-container pod (app + log collector sidecar), diagnose a broken pod that's stuck in CrashLoopBackOff, use kubectl exec to debug inside a running container, and set resource limits then trigger an OOMKill to see what happens. Progressive difficulty from "run a pod" to "debug a production-like failure."

---

### Quality Standard: 10/10 on the Dojo Scale

**LENGTH**: 600-800 lines of **content** minimum. This is a deep, rich learning module — not an outline or reference doc. Visual aids (ASCII diagrams, mermaid charts, code blocks used purely for illustration) do NOT count toward the line minimum — they are supplements to the teaching, not substitutes for it.

**REQUIRED SECTIONS** (in this exact order):

1. **Title and metadata** — H1 title, complexity tag, time estimate, prerequisites
2. **Learning Outcomes** — 3-5 measurable outcomes using Bloom's Taxonomy Level 3+ action verbs: "debug", "design", "evaluate", "compare", "diagnose", "implement". NOT "understand" or "know". Each outcome must be testable by the quiz or exercise.
3. **Why This Module Matters** — Open with a dramatic, real-world scenario written in third person. A real incident, a real company (anonymized if needed), real financial impact. Make the reader feel why this topic matters viscerally. Then transition to what they will learn. 2-3 paragraphs minimum.
4. **Core content sections** (3-6 sections) — Each section should include:
   - Clear explanations with analogies (treat the reader as a smart beginner)
   - Runnable code blocks (bash, YAML, Go, Python — whatever fits)
   - ASCII diagrams where architecture or flow needs visualization
   - Tables for comparisons, decision matrices, or reference data
   - "War Story" or practical example within the section
   - **At least 2 inline active learning prompts** across all sections
5. **Did You Know?** — Exactly 4 interesting facts with real numbers/dates
6. **Common Mistakes** — Table with 6-8 rows. Columns: Mistake | Why It Happens | How to Fix It
7. **Quiz** — 6-8 scenario-based questions in `<details>` tags. At least 4 scenario-based.
8. **Hands-On Exercise** — 4-6 progressive tasks with solutions in `<details>` tags
9. **Next Module** — Link with teaser

**FRONTMATTER** — must include exactly:
```yaml
---
title: "Module 1.3: Pods - The Atomic Unit"
slug: prerequisites/kubernetes-basics/module-1.3-pods
sidebar:
  order: 4
---
```

**TONE**: Conversational but authoritative. Explain "why" before "what". Use analogies. Be direct and practical.

**VISUAL AIDS**: ASCII for architecture/anatomy, Mermaid for flows/sequences, Tables for comparisons. Properly aligned, closed borders, integrated labels.

**TECHNICAL**: All commands runnable. YAML 2-space indent. Language-tagged code blocks. Use `k` alias. K8s 1.35+.

**PEDAGOGICAL**: Bloom's L3+. Constructive alignment. Scaffold complexity. Worked examples before practice. Distributed active learning.

**AVOID**: No 47 repetition. No generic examples. No thin outlines. No skipping exercise. No emojis. No recall quizzes. No back-loaded active learning.
