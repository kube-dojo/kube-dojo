TASK: Write a complete KubeDojo educational module. Write the output DIRECTLY to the file at src/content/docs/prerequisites/kubernetes-basics/module-1.7-namespaces-labels.md (overwrite it completely).

### Module Specification

- **Title**: Module 1.7: Namespaces and Labels
- **File path**: prerequisites/kubernetes-basics/module-1.7-namespaces-labels.md
- **Complexity**: [MEDIUM]
- **Time to Complete**: 35-40 minutes
- **Prerequisites**: Module 1.4 (Deployments), Module 1.5 (Services)
- **Next Module**: [Module 1.8: YAML for Kubernetes](/prerequisites/kubernetes-basics/module-1.8-yaml-kubernetes/) — Master the language Kubernetes speaks

### Topic Coverage

- What namespaces actually isolate (DNS names, RBAC policies, resource quotas) and what they DON'T (network traffic by default — needs NetworkPolicy)
- Default namespaces: default, kube-system, kube-public, kube-node-lease — what lives in each and why
- Creating and switching namespaces, setting default namespace in kubectl context
- Labels: key-value pairs for organizing resources — naming conventions and real-world labeling strategies
- Selectors: equality-based vs set-based, how Services use them, how Deployments use them
- Annotations vs Labels: when to use which (metadata for humans/tools vs metadata for selection)
- Resource Quotas and LimitRanges per namespace — preventing one team from consuming all cluster resources

### Hands-On Exercise Concept

Set up a multi-team cluster: create namespaces for "team-frontend" and "team-backend", apply resource quotas, deploy apps with proper labels, use selectors to query across namespaces, and demonstrate what happens when a quota is exceeded. Include a scenario where students use labels to do a canary deployment selection.

---

### Quality Standard: 10/10 on the Dojo Scale

**LENGTH**: 600-800 lines of **content** minimum. Deep teaching, not an outline.

**REQUIRED SECTIONS** (in this exact order):

1. **Title and metadata** — H1 title, complexity tag, time estimate, prerequisites
2. **Learning Outcomes** — 3-5 measurable, Bloom's L3+ action verbs
3. **Why This Module Matters** — Real-world incident opening, 2-3 paragraphs
4. **Core content sections** (3-6 sections) with explanations, code, diagrams, tables, war stories, inline active learning prompts (at least 2 total)
5. **Did You Know?** — Exactly 4 facts with real numbers
6. **Common Mistakes** — 6-8 row table (Mistake | Why | Fix)
7. **Quiz** — 6-8 questions in `<details>` tags, at least 4 scenario-based
8. **Hands-On Exercise** — 4-6 progressive tasks with `<details>` solutions
9. **Next Module** — Link with teaser

**FRONTMATTER**:
```yaml
---
title: "Module 1.7: Namespaces and Labels"
slug: prerequisites/kubernetes-basics/module-1.7-namespaces-labels
sidebar:
  order: 8
---
```

**TONE**: Conversational but authoritative. "Why" before "what". Analogies. Direct and practical.

**VISUAL AIDS**: ASCII for architecture, Mermaid for flows, Tables for comparisons. Properly aligned.

**TECHNICAL**: Runnable commands. YAML 2-space. Language-tagged blocks. `k` alias. K8s 1.35+.

**PEDAGOGICAL**: Bloom's L3+. Constructive alignment. Scaffolded complexity. Worked examples. Distributed active learning.

**AVOID**: No 47. No generic examples. No thin outlines. No emojis. No recall quizzes. No back-loaded learning.
