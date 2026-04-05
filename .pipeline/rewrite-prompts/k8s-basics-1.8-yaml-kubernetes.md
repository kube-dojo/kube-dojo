TASK: Write a complete KubeDojo educational module. Write the output DIRECTLY to the file at src/content/docs/prerequisites/kubernetes-basics/module-1.8-yaml-kubernetes.md (overwrite it completely).

### Module Specification

- **Title**: Module 1.8: YAML for Kubernetes
- **File path**: prerequisites/kubernetes-basics/module-1.8-yaml-kubernetes.md
- **Complexity**: [MEDIUM]
- **Time to Complete**: 35-40 minutes
- **Prerequisites**: Modules 1.1-1.7 (familiarity with K8s resources)
- **Next Module**: Continue to [Philosophy and Design](/prerequisites/philosophy-design/module-1.1-why-kubernetes-won/) — Understand the bigger picture

### Topic Coverage

- YAML fundamentals: scalars, sequences, mappings, multi-line strings (| vs >), anchors and aliases
- The four required K8s fields: apiVersion, kind, metadata, spec — what each does and why they exist
- Using `kubectl explain` to explore API schema interactively (explain pod.spec.containers, explain --recursive)
- Common YAML patterns: environment variables, volume mounts, labels/selectors, resource requests
- Multi-resource files with `---` document separator
- Validating YAML: `kubectl apply --dry-run=client`, `kubectl diff`, server-side dry-run
- Real debugging: reading K8s error messages to find YAML mistakes (wrong apiVersion, bad indentation, type mismatches)

### Hands-On Exercise Concept

Write a complete multi-resource YAML file from scratch (Deployment + Service + ConfigMap), deliberately introduce 5 common YAML errors and debug each one using kubectl error messages and `kubectl explain`. Progress from fixing simple indentation to diagnosing wrong apiVersion for a resource type.

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
title: "Module 1.8: YAML for Kubernetes"
slug: prerequisites/kubernetes-basics/module-1.8-yaml-kubernetes
sidebar:
  order: 9
---
```

**TONE**: Conversational but authoritative. "Why" before "what". Analogies. Direct and practical.

**VISUAL AIDS**: ASCII for structure/anatomy, Mermaid for flows, Tables for comparisons.

**TECHNICAL**: Runnable commands. YAML 2-space. Language-tagged blocks. `k` alias. K8s 1.35+.

**PEDAGOGICAL**: Bloom's L3+. Constructive alignment. Scaffolded complexity. Worked examples. Distributed active learning.

**AVOID**: No 47. No generic examples. No thin outlines. No emojis. No recall quizzes. No back-loaded learning.
