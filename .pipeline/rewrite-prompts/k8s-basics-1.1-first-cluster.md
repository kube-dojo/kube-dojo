TASK: Write a complete KubeDojo educational module. Write the output DIRECTLY to the file at src/content/docs/prerequisites/kubernetes-basics/module-1.1-first-cluster.md (this file already exists — overwrite it completely).

### Module Specification

- **Title**: Module 1.1: Your First Cluster
- **File path**: prerequisites/kubernetes-basics/module-1.1-first-cluster.md
- **Complexity**: [MEDIUM]
- **Time to Complete**: 30-40 minutes
- **Prerequisites**: Docker installed, Cloud Native 101 completed
- **Next Module**: [Module 1.2: kubectl Basics](/prerequisites/kubernetes-basics/module-1.2-kubectl-basics/) — Learn to talk to your cluster

### Topic Coverage

- What a Kubernetes cluster actually is (control plane + worker nodes, analogy to an orchestra conductor)
- Why you need a local cluster for learning (cost, speed, safety to break things)
- Tool comparison: kind vs minikube vs k3d vs Docker Desktop (when to use each)
- Installing and creating a kind cluster step-by-step
- Verifying the cluster works: kubectl cluster-info, get nodes, system pods
- Creating a multi-node cluster with kind config
- Troubleshooting: Docker not running, port conflicts, resource limits, kind logs

### Hands-On Exercise Concept

Create three different kind clusters: a single-node default, a multi-node cluster with 1 control plane + 2 workers, and a cluster with a specific Kubernetes version. Verify each one works, deploy a test pod, then clean up. Include a troubleshooting scenario where students deliberately break something and fix it.

---

### Quality Standard: 10/10 on the Dojo Scale

**LENGTH**: 700-900 lines of **content** minimum. This is CRITICAL — modules under 600 lines WILL be rejected. This is a deep, rich learning module — not an outline or reference doc. Visual aids (ASCII diagrams, mermaid charts, code blocks used purely for illustration) do NOT count toward the line minimum — they are supplements to the teaching, not substitutes for it.

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
   - **At least 2 inline active learning prompts** across all sections: "Pause and predict: what do you think happens if...?", "Before running this, what output do you expect?", or "Which approach would you choose here and why?"
5. **Did You Know?** — Exactly 4 interesting facts. Include real numbers, dates, or surprising details. Each fact should teach something the reader won't forget.
6. **Common Mistakes** — Table with 6-8 rows. Columns: Mistake | Why It Happens | How to Fix It. Be specific — not generic advice.
7. **Quiz** — 6-8 questions using `<details><summary>Question</summary>Answer</details>` format. **At least 4 must be scenario-based** ("Your team just deployed X and Y happens — what do you check?"). Do NOT write recall questions ("What is the command for X?"). Answers should be thorough (3-5 sentences explaining WHY).
8. **Hands-On Exercise** — Multi-step practical exercise with:
   - Setup instructions (if needed)
   - 4-6 progressive tasks (easy → challenging)
   - Solutions in `<details>` tags
   - Clear success criteria checklist using `- [ ]` format
9. **Next Module** — Link to the next module with a one-line teaser

**FRONTMATTER** — must include exactly:
```yaml
---
title: "Module 1.1: Your First Cluster"
slug: prerequisites/kubernetes-basics/module-1.1-first-cluster
sidebar:
  order: 2
---
```

**TONE**:
- Conversational but authoritative — like a senior engineer mentoring you
- Explain "why" before "what" — motivation before instruction
- Use analogies from everyday life to explain abstract concepts
- Be direct and practical — no filler, no corporate-speak
- When discussing tools, be honest about trade-offs (no marketing language)

**VISUAL AID STANDARDS**:
- **ASCII**: Use for component anatomy, static architecture, hierarchies ("what's in the box")
- **Mermaid**: Use for logic flows, sequences, state machines, request paths ("how it works")
- **Tables**: Use for comparisons, decision matrices, reference data
- ASCII diagrams must be properly aligned — consistent box widths, aligned columns, uniform spacing
- Box borders must close properly (no missing corners, no dangling lines)
- Labels must be integrated INTO diagrams, not in separate legends

**TECHNICAL STANDARDS**:
- All commands must be complete and runnable (not pseudocode)
- YAML: 2-space indentation, valid syntax
- Code blocks must specify the language (```bash, ```yaml, etc.)
- Use `k` alias for kubectl (after explaining it once)
- Kubernetes version: 1.35+

**PEDAGOGICAL REQUIREMENTS**:
- Every module must operate at Bloom's Taxonomy Level 3 (Apply) or above
- Constructive Alignment: learning outcomes, teaching activities, and assessment must test the same thing
- Scaffold complexity: start simple, add layers. Don't dump the full picture first.
- Include at least one worked example before asking the learner to solve a similar problem
- Active learning must be distributed throughout, not just at the end

**WHAT TO AVOID**:
- Do NOT repeat the number 47 in timestamps, durations, or counts
- Do NOT use generic corporate examples — use realistic engineering scenarios
- Do NOT write thin outlines — every section needs depth, examples, and explanation
- Do NOT skip the exercise — it's the most important part for learning
- Do NOT use emojis
- Do NOT write quiz questions that test recall ("What is X?") — write scenario-based questions
- Do NOT create "list of facts" modules — every section needs teaching depth
- Do NOT back-load all active learning to the end — distribute throughout
