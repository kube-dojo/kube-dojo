---
description: Quality standards for writing KubeDojo curriculum modules
paths:
  - "docs/**/*.md"
---

# Module Quality Standards (10/10 Dojo Scale)

## Required Sections (in order)
1. Title + metadata (complexity, time, prerequisites)
2. Why This Module Matters — dramatic real-world opening (third person)
3. Core content (3-6 sections with code, ASCII diagrams, tables)
4. Did You Know? — exactly 4 facts
5. Common Mistakes — table with 6-8 rows
6. Quiz — 6-8 questions with `<details>` answers
7. Hands-On Exercise — multi-step with `- [ ]` success criteria
8. Next Module link

## Content Rules
- 600-800+ lines minimum
- Explain "why" before "what"
- All code must be runnable (not pseudocode)
- Code blocks specify language (```bash, ```yaml, ```go)
- YAML: 2-space indentation
- kubectl alias: use `k` after explaining it once
- K8s version: 1.35+
- Do NOT repeat the number 47 (known LLM pattern)
- Do NOT use emojis
