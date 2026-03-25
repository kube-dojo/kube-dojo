---
name: curriculum-writer
description: Write KubeDojo curriculum modules. Use when creating modules, writing theory, exercises, quizzes. Triggers on "write module", "create module", "new module".
---

# Curriculum Writer Skill

Expert skill for writing new KubeDojo curriculum modules. Ensures consistent structure, tone, and quality across all educational content.

## When to Use
- Creating new curriculum modules
- Expanding existing module content
- Writing theory sections, exercises, or quizzes

## Track-Specific Guidelines

KubeDojo has three tracks with different focuses:

### Kubernetes Certifications (docs/k8s/)
- Exam-focused content
- Aligned with official CNCF curriculum
- Time-boxed complexity (exam speed matters)
- kubectl commands emphasized

### Prerequisites (docs/prerequisites/)
- Beginner-friendly fundamentals
- No assumed knowledge
- Build foundation for certifications

### Platform Engineering (docs/platform/)
- Post-certification, practitioner content
- Theory-first approach (principles over tools)
- Three layers: Foundations → Disciplines → Toolkits

---

## Platform Track Structure

Platform modules have **three tiers**:

### Foundations (docs/platform/foundations/)
Timeless theory that doesn't change:
- Systems Thinking
- Reliability Engineering
- Observability Theory
- Security Principles
- Distributed Systems

### Disciplines (docs/platform/disciplines/)
Applied practices and mental models:
- SRE
- Platform Engineering
- GitOps
- DevSecOps
- MLOps

### Toolkits (docs/platform/toolkits/)
Current tools (will evolve over time):
- Observability (Prometheus, OTel, Grafana)
- GitOps Tools (ArgoCD, Flux)
- Security Tools (Vault, OPA, Falco)
- Platforms (Backstage, Crossplane)
- ML Platforms (Kubeflow, MLflow)

---

## Module Template (Certification Track)

```markdown
# Module X.Y: [Topic Name]

> **Complexity**: `[QUICK]` | `[MEDIUM]` | `[COMPLEX]`
>
> **Time to Complete**: X-Y minutes
>
> **Prerequisites**: [List required modules or knowledge]

---

## Why This Module Matters

[2-3 paragraphs explaining WHY this topic matters]

> **The [Topic] Analogy**
>
> [Memorable analogy that makes the concept stick]

---

## What You'll Learn

[Clear learning objectives]

---

## Part 1: [Theory/Concepts]

### 1.1 [Subsection]

[Content with diagrams/examples]

> **Did You Know?**
>
> [Interesting fact]

---

## Part 2: [Practical Application]

[Hands-on content]

> **War Story: [Catchy Title]**
>
> [Real incident that illustrates the concept]

---

## Did You Know?

- **[Fact 1]**: [Detail]
- **[Fact 2]**: [Detail]
- **[Fact 3]**: [Detail]

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| [Mistake 1] | [What goes wrong] | [How to fix] |
| [Mistake 2] | [What goes wrong] | [How to fix] |

---

## Quiz

1. **[Question]**
   <details>
   <summary>Answer</summary>
   [Detailed answer explaining why]
   </details>

[4 questions total]

---

## Hands-On Exercise

**Task**: [What to do]

**Steps**:
1. [Step 1]
2. [Step 2]

**Success Criteria**:
- [ ] [Verifiable outcome]

**Verification**:
```bash
[Commands to verify]
```

---

## Next Module

[Link to next module]
```

---

## Module Template (Platform Track)

Platform modules include additional sections:

```markdown
# Module X.Y: [Topic Name]

> **Complexity**: `[QUICK]` | `[MEDIUM]` | `[COMPLEX]`
>
> **Time to Complete**: X-Y minutes
>
> **Prerequisites**: [List required modules]
>
> **Track**: Foundations | Disciplines | Toolkits

---

## Why This Module Matters

[Real-world motivation - not exam-focused]

> **The [Topic] Analogy**
>
> [Analogy connecting to familiar concepts]

---

## What You'll Learn

[Learning objectives]

---

## Key Concepts

### [Concept 1]

[Theory explanation with diagrams]

### [Concept 2]

[More theory]

---

## Current Landscape

How this concept is implemented in practice:

| Tool/Approach | Description | When to Use |
|---------------|-------------|-------------|
| [Tool 1] | [What it does] | [Use case] |
| [Tool 2] | [What it does] | [Use case] |

---

## Best Practices

What good looks like:

1. **[Practice 1]** - [Explanation]
2. **[Practice 2]** - [Explanation]
3. **[Practice 3]** - [Explanation]

---

## Anti-Patterns

What to avoid:

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| [Pattern 1] | [Problem] | [Solution] |
| [Pattern 2] | [Problem] | [Solution] |

---

## Did You Know?

- **[Fact 1]**: [Detail]
- **[Fact 2]**: [Detail]

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| [Mistake 1] | [Impact] | [Fix] |

---

## Quiz

[4 questions with hidden answers]

---

## Hands-On Exercise

[Practical exercise with verification]

---

## Further Reading

Books, talks, and papers for deeper understanding:

- **[Book/Resource]** - [Why it's valuable]
- **[Talk/Video]** - [Key takeaway]
- **[Paper/Article]** - [What you'll learn]

---

## Next Module

[Link to next module]
```

---

## Writing Guidelines

### Tone
- Conversational, not academic
- Empathetic to learner struggles
- Confident but not arrogant
- Use "you" and "we" freely

### Analogies
- One memorable analogy per module minimum
- Connect concepts to familiar real-world things
- Analogies should illuminate, not oversimplify

### War Stories
- At least one per module
- Must have real consequences (time lost, money lost, outage)
- End with a lesson learned
- Can be anonymized but should feel authentic

### Code Examples
- All code must be complete and runnable
- Use realistic names (not foo/bar)
- Show expected output where helpful
- Include verification steps

### Diagrams
- Use ASCII art for architecture diagrams
- Keep diagrams simple and focused
- Every complex concept should have a visual

### Technical Accuracy
- Use current versions of tools
- Note when something is deprecated
- Link to official docs for deep dives
- For Platform track: cover principles before tools

### Quiz Questions
- Test understanding, not memorization
- Answers should explain "why"
- Mix of conceptual and practical
- 4 questions per module

### Complexity Tags
- `[QUICK]`: Simple concept, fast read
- `[MEDIUM]`: Moderate complexity
- `[COMPLEX]`: Deep topic, requires focus

---

## Quality Checklist

Before considering a module complete:

### All Tracks
- [ ] All structural elements present
- [ ] At least one memorable analogy
- [ ] At least one war story
- [ ] 2-3 "Did You Know?" facts
- [ ] Common mistakes table filled
- [ ] 4 quiz questions with detailed answers
- [ ] Hands-on exercise with verification
- [ ] All code tested and working
- [ ] Links to next module
- [ ] Proofread for clarity

### Platform Track Additional
- [ ] Current Landscape section (tools/approaches)
- [ ] Best Practices section
- [ ] Anti-Patterns section
- [ ] Further Reading section
- [ ] Theory explained before tools
- [ ] Principles emphasized over implementation

---

## Naming Conventions

### File Names
```
module-X.Y-topic-name.md
```

Examples:
- `module-1.1-what-is-sre.md`
- `module-2.3-error-budgets.md`

### Directory Structure
```
docs/platform/disciplines/sre/
├── README.md           # Part overview
├── module-1.1-xxx.md
├── module-1.2-xxx.md
└── ...
```

---

## Cross-References

When referencing other modules:
- Use relative links: `../foundations/systems-thinking/module-1.1-xxx.md`
- For prerequisites: Link to specific module, not just track
- For further learning: "See also [Module X.Y: Topic]"
