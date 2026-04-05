TASK: Write a complete KubeDojo educational module. Write the output DIRECTLY to the file at src/content/docs/prerequisites/modern-devops/module-1.3-cicd-pipelines.md (overwrite it completely).

### Module Specification

- **Title**: Module 1.3: CI/CD Pipelines
- **File path**: prerequisites/modern-devops/module-1.3-cicd-pipelines.md
- **Complexity**: [MEDIUM]
- **Time to Complete**: 35-40 minutes
- **Prerequisites**: Module 1.1 (Infrastructure as Code), basic Git knowledge
- **Next Module**: [Module 1.4: Observability](/prerequisites/modern-devops/module-1.4-observability/) — Learn how to see what's happening in production

### Topic Coverage

- CI vs CD vs CD: Continuous Integration, Continuous Delivery, Continuous Deployment — the real differences with concrete examples
- Anatomy of a pipeline: stages (build → test → scan → deploy), jobs, steps, artifacts, and how they chain together
- Pipeline-as-code: why pipelines live in the repo (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`)
- Tool comparison deep-dive: GitHub Actions vs GitLab CI vs Jenkins vs Tekton — architecture, trade-offs, K8s-native vs traditional
- Container-native CI/CD: building images in pipelines, registry push, image scanning (Trivy, Snyk), signing (cosign)
- Deployment strategies triggered by CI/CD: rolling update, blue-green, canary — how pipelines implement each
- Pipeline anti-patterns: no tests, manual gates everywhere, secrets in code, flaky tests ignored, "deploy on Friday" culture

### Hands-On Exercise Concept

Write a complete GitHub Actions workflow from scratch that builds a Docker image, runs tests, scans for vulnerabilities with Trivy, pushes to a registry, and deploys to a kind cluster. Include stages for different environments (staging, production) with manual approval gates. Debug a broken pipeline where the image scan finds a critical CVE.

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
title: "Module 1.3: CI/CD Pipelines"
slug: prerequisites/modern-devops/module-1.3-cicd-pipelines
sidebar:
  order: 4
---
```

**TONE**: Conversational but authoritative. "Why" before "what". Analogies. Direct and practical.

**VISUAL AIDS**: ASCII for pipeline architecture, Mermaid for pipeline flows, Tables for tool comparisons.

**TECHNICAL**: Runnable commands and YAML. 2-space indent. Language-tagged blocks. K8s 1.35+.

**PEDAGOGICAL**: Bloom's L3+. Constructive alignment. Scaffolded complexity. Worked examples. Distributed active learning.

**AVOID**: No 47. No generic examples. No thin outlines. No emojis. No recall quizzes. No back-loaded learning.
