TASK: Write a complete KubeDojo educational module. Write the output DIRECTLY to the file at src/content/docs/prerequisites/modern-devops/module-1.5-platform-engineering.md (overwrite it completely).

### Module Specification

- **Title**: Module 1.5: Platform Engineering Concepts
- **File path**: prerequisites/modern-devops/module-1.5-platform-engineering.md
- **Complexity**: [MEDIUM]
- **Time to Complete**: 30-35 minutes
- **Prerequisites**: Modules 1.1-1.4 (IaC, GitOps, CI/CD, Observability)
- **Next Module**: [Module 1.6: DevSecOps](/prerequisites/modern-devops/module-1.6-devsecops/) — Learn to build security into every stage

### Topic Coverage

- What Platform Engineering is: building internal platforms that abstract infrastructure complexity for developers
- The problem it solves: "Kubernetes is too complex for every developer" — cognitive load, ticket-driven ops, shadow IT
- Internal Developer Platform (IDP): what it includes (service catalog, self-service provisioning, golden paths, developer portal)
- Platform as a Product: treating internal developers as customers, measuring adoption, iterating on feedback
- Role comparison: Platform Engineer vs DevOps Engineer vs SRE — overlaps and distinct responsibilities
- Real-world platform examples: Backstage (Spotify), Humanitec, Kratix — what they provide and how they work
- When NOT to build a platform: premature platforming, YAGNI principle, the "platform of one" anti-pattern

### Hands-On Exercise Concept

Design an Internal Developer Platform for a fictional company with 3 development teams. Create a decision matrix of what to build vs buy, sketch the golden path for deploying a new microservice (from "git push" to "running in production"), and evaluate when the company should invest in a platform team based on team size and deployment frequency metrics.

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
title: "Module 1.5: Platform Engineering Concepts"
slug: prerequisites/modern-devops/module-1.5-platform-engineering
sidebar:
  order: 6
---
```

**TONE**: Conversational but authoritative. "Why" before "what". Analogies. Direct and practical.

**VISUAL AIDS**: ASCII for platform architecture, Mermaid for developer workflows, Tables for role comparisons.

**TECHNICAL**: Runnable examples where applicable. Language-tagged blocks. K8s 1.35+.

**PEDAGOGICAL**: Bloom's L3+. Constructive alignment. Scaffolded complexity. Worked examples. Distributed active learning.

**AVOID**: No 47. No generic examples. No thin outlines. No emojis. No recall quizzes. No back-loaded learning.
