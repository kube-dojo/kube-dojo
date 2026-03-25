---
name: module-quality-reviewer
description: Review KubeDojo modules for quality. Use when reviewing, scoring, or checking modules. Triggers on "review module", "check quality", "score module".
---

# Module Quality Reviewer Skill

Expert skill for validating KubeDojo curriculum modules against established quality standards. Automatically invoked when reviewing educational content for quality assurance.

## When to Use
- Reviewing new or updated curriculum modules
- Checking if content meets KubeDojo quality bar
- Identifying gaps in educational content
- Comparing modules for consistency

## Quality Standards

### Structure (Must Have All)
- [ ] Complexity tag: `[QUICK]`, `[MEDIUM]`, or `[COMPLEX]`
- [ ] Time to Complete estimate
- [ ] Prerequisites listed
- [ ] "Why This Module Matters" section
- [ ] "Did You Know?" section (2-3 items)
- [ ] Common Mistakes table
- [ ] Quiz with `<details>` hidden answers
- [ ] Hands-On Exercise with Success Criteria
- [ ] "Next Module" link

### Content Quality Criteria

#### Theory Depth (25%)
- Explains "why" not just "what"
- No handwaving or glossing over complexity
- Junior-friendly (treats reader as beginner)
- Builds conceptual understanding before commands

#### Practical Value (25%)
- All code/commands are complete and runnable
- Clear step-by-step instructions
- Verification steps included
- Realistic scenarios, not toy examples

#### Engagement (25%)
- Memorable analogies that make concepts stick
- War stories with real consequences
- "Did You Know?" facts that reinforce learning
- Conversational tone, not textbook dry

#### Exam Relevance (25%)
- Aligns with CKA 2025 curriculum
- Speed tips for exam scenarios
- Common exam mistakes highlighted
- Complexity tags match exam question types

## Scoring

| Score | Meaning |
|-------|---------|
| 10/10 | Exceptional - Ready to publish, sets the standard |
| 9/10 | Excellent - Minor polish needed |
| 8/10 | Good - Ready for publication with small fixes |
| 7/10 | Acceptable - Needs revision in 1-2 areas |
| 6/10 | Needs Work - Multiple areas require attention |
| <6/10 | Major Rewrite - Does not meet standards |

## Output Format

When reviewing, provide:

```
## Module Review: [Name]

### Scores
| Category | Score | Notes |
|----------|-------|-------|
| Theory Depth | X/10 | ... |
| Practical Value | X/10 | ... |
| Engagement | X/10 | ... |
| Exam Relevance | X/10 | ... |
| **Overall** | **X/10** | |

### Structure Checklist
- [x] or [ ] for each required element

### Strengths
1. ...
2. ...
3. ...

### Areas for Improvement
1. ...
2. ...
3. ...

### Specific Recommendations
- ...
```

## Reference Standard

Module 0.5 (Exam Strategy) represents the quality bar:
- Score: 10/10
- Memorable analogies throughout
- War stories with real consequences
- Clear "why" explanations for every concept
- Practical, actionable content
- Complete structural elements
