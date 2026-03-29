---
title: "Module 1.6: Postmortems and Learning"
slug: platform/disciplines/core-platform/sre/module-1.6-postmortems
sidebar:
  order: 7
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.5: Incident Management](module-1.5-incident-management/) — Incident response
- **Required**: [Module 1.1: What is SRE?](module-1.1-what-is-sre/) — SRE fundamentals
- **Recommended**: [Systems Thinking Track](../../foundations/systems-thinking/) — Understanding system dynamics

---

## Why This Module Matters

An incident happened. You fixed it. Everyone's exhausted.

What happens next determines whether you're truly learning or just fighting the same fires forever.

**Without postmortems**: Incidents repeat. Knowledge stays in people's heads. Teams blame each other. Nothing improves.

**With postmortems**: Every incident makes the system stronger. Lessons are documented. Teams learn together. The same incident never happens twice.

This module teaches you how to conduct blameless postmortems that turn failures into fuel for improvement.

---

## What Is a Postmortem?

A postmortem is a structured analysis of an incident after it's resolved.

**Purpose:**
- Understand what happened
- Identify contributing factors
- Prevent recurrence
- Share learnings broadly

**Not purpose:**
- Assign blame
- Punish individuals
- Document for legal defense
- Check a compliance box

### When to Write a Postmortem

| Trigger | Postmortem? |
|---------|-------------|
| SEV-1 incident | Always |
| SEV-2 incident | Always |
| SEV-3 incident | If caused by interesting failure mode |
| Near miss | Often (we got lucky) |
| Recurring issue | Yes (why does this keep happening?) |
| Customer escalation | Usually |
| Data loss | Always |

The threshold should be low enough to capture learning, high enough to not overwhelm the team.

---

## Blameless Culture

The foundation of effective postmortems is **blamelessness**.

### Why Blamelessness?

**With blame:**
- People hide information to protect themselves
- Root causes stay hidden
- Changes don't prevent recurrence
- Fear dominates, innovation dies

**Without blame:**
- People share freely, knowing they're safe
- True root causes emerge
- Changes actually prevent recurrence
- Psychological safety enables improvement

### What Blamelessness Is NOT

Blameless doesn't mean:
- No accountability
- No consequences for negligence
- Ignoring patterns of behavior
- Pretending humans don't make mistakes

Blameless means:
- Focus on systems, not individuals
- Assume good intentions
- Ask "why did the system allow this?" not "who screwed up?"
- Build better systems, not blame better individuals

### The Second Story

Every incident has two stories:

**First story (blame narrative):**
```
"Alice pushed a bad config that took down production.
She should have been more careful."
```

**Second story (systems narrative):**
```
"A config change caused a production outage.
Why did our system allow a bad config to reach production?
Why didn't we have validation?
Why didn't we have automatic rollback?
Why didn't the review process catch it?
What about the system made the error likely?"
```

The second story finds root causes. The first story finds scapegoats.

---

## The Postmortem Process

### Timeline

```
Day 0: Incident occurs, resolved
Day 1-2: Initial draft written by incident responders
Day 3-4: Draft reviewed by participants
Day 5: Postmortem meeting held
Day 5-7: Final version published
Ongoing: Action items tracked to completion
```

### Step 1: Gather Data (Before Meeting)

**What to collect:**
- Timeline of events
- Alert history
- Metrics and dashboards
- Chat logs from incident channel
- Customer reports
- Deployment history

**Tip:** Do this while memories are fresh. Waiting a week loses detail.

### Step 2: Write the Draft

The Incident Commander or Tech Lead writes the initial draft.

Key sections:
- Summary
- Timeline
- Impact
- Contributing factors
- Action items

(Full template below)

### Step 3: Hold the Meeting

**Who attends:**
- Incident responders
- On-call engineers
- Service owners
- Stakeholders (optional for major incidents)

**Meeting structure (60-90 minutes):**

```
1. Read the timeline together (10 min)
   - Walk through events
   - Fill in gaps
   - Correct mistakes

2. Identify contributing factors (20 min)
   - What conditions led to this?
   - Apply "5 Whys"
   - Avoid single root cause

3. Discuss action items (20 min)
   - What would prevent recurrence?
   - Who owns each action?
   - When will they be done?

4. Share learnings (10 min)
   - What surprised us?
   - What did we learn?
   - Who else should know?
```

### Step 4: Publish and Share

- Post final postmortem to shared location
- Announce in relevant channels
- Present at team/company meetings for SEV-1
- Cross-link to related incidents

### Step 5: Track Action Items

Action items are useless if not completed.

```yaml
action_items:
  - item: "Add config validation in CI pipeline"
    owner: "@alice"
    due: "2024-02-15"
    status: "In Progress"
    priority: "P1"

  - item: "Add automatic rollback for config changes"
    owner: "@bob"
    due: "2024-02-28"
    status: "Not Started"
    priority: "P1"

  - item: "Document config change procedure"
    owner: "@carol"
    due: "2024-02-10"
    status: "Complete"
    priority: "P2"
```

Review action items weekly until all complete.

---

## Try This: The 5 Whys

Practice finding root causes with the 5 Whys technique:

```
Incident: Production database went down

Why #1: Why did the database go down?
  → It ran out of disk space

Why #2: Why did it run out of disk space?
  → Log files grew unexpectedly large

Why #3: Why did log files grow unexpectedly?
  → A new feature logged at debug level in production

Why #4: Why was debug logging enabled in production?
  → The developer forgot to change the log level before deploying

Why #5: Why did the deployment process allow incorrect log levels?
  → There's no validation of configuration in the deployment pipeline

Root cause: Missing configuration validation
Action: Add log level validation to CI/CD pipeline
```

Notice: We didn't stop at "the developer made a mistake." We asked why the system allowed that mistake.

---

## Postmortem Template

```markdown
# Postmortem: [TITLE]

**Date**: YYYY-MM-DD
**Authors**: [Names]
**Status**: Draft | Reviewed | Final
**Severity**: SEV-X

## Summary

[2-3 sentences describing what happened and the impact]

## Impact

- **Duration**: [Start time] to [End time] ([X] minutes/hours)
- **Users affected**: [Number or percentage]
- **Revenue impact**: [If applicable]
- **Error budget consumed**: [X]%
- **Data loss**: [Yes/No, details if yes]

## Timeline (All times in UTC)

| Time | Event |
|------|-------|
| 14:00 | Deploy of version X.Y.Z begins |
| 14:05 | Error rate increases, alerts fire |
| 14:10 | On-call acknowledges, begins investigation |
| 14:20 | Root cause identified |
| 14:25 | Rollback initiated |
| 14:30 | Service recovered |
| 14:35 | Incident declared resolved |

## Detection

How was the incident detected?
- [ ] Monitoring alert
- [ ] Customer report
- [ ] Internal user report
- [ ] Other: ____________

Time to detection (TTD): [X] minutes
Could detection be faster? [Yes/No, how]

## Contributing Factors

### Factor 1: [Name]
[Description of contributing factor]

### Factor 2: [Name]
[Description of contributing factor]

### Factor 3: [Name]
[Description of contributing factor]

## What Went Well

- [Thing that went well]
- [Another thing that went well]

## What Went Poorly

- [Thing that went poorly]
- [Another thing that went poorly]

## Where We Got Lucky

- [Way we got lucky that masked the severity]

## Action Items

| Action | Owner | Due Date | Priority | Status |
|--------|-------|----------|----------|--------|
| [Action 1] | @name | YYYY-MM-DD | P1 | Not Started |
| [Action 2] | @name | YYYY-MM-DD | P1 | Not Started |
| [Action 3] | @name | YYYY-MM-DD | P2 | Not Started |

## Lessons Learned

[Key insights from this incident]

## Related Incidents

- [Link to related postmortem]
- [Link to related postmortem]

## Supporting Information

- [Link to incident channel]
- [Link to dashboards]
- [Link to relevant docs]
```

---

## Did You Know?

1. **NASA's approach to postmortems inspired Google's SRE culture**. NASA's "lessons learned" database has entries going back to the 1960s, including failures that led to tragedies.

2. **The aviation industry's blameless culture has made flying remarkably safe**. Pilots can report mistakes anonymously, leading to systemic improvements. SRE borrowed this concept.

3. **John Allspaw (former Etsy CTO) popularized "blameless postmortems" in tech**. His 2012 talk "Blameless PostMortems" is considered a foundational SRE resource.

4. **Some companies publish their postmortems publicly** (GitLab, Cloudflare, Google). GitLab's handbook even includes their postmortem templates. This radical transparency builds customer trust and contributes to industry-wide learning.

---

## War Story: The Postmortem That Changed Culture

A company I worked with had a blame culture. After incidents:
- Managers asked "who did this?"
- Engineers got written up
- People hid mistakes
- Same incidents kept recurring

Then a major outage happened:

**The Incident:**
- 4-hour outage during peak traffic
- Cause: An engineer deployed a change that wasn't tested
- Impact: ~$500K revenue loss

**The Old Way (What Leadership Wanted):**
- Find who deployed the change
- Punish them
- "Make an example"

**What Actually Happened:**

The new VP of Engineering stopped the blame train:

```
"Before we talk about who, let's talk about what.

What systems allowed untested code to reach production?
What process failed to catch this?
What tooling gaps existed?

The engineer who deployed this is not the problem.
The engineer who deploys the NEXT untested change is also not the problem.
The problem is that our system makes it possible."
```

**The Postmortem Found:**
- No automated testing in CI
- No staging environment
- No deployment rollback process
- No config validation
- Review process was optional

**The Actions:**
- Built proper CI/CD pipeline
- Created staging environment
- Implemented automatic rollback
- Added config validation
- Made review mandatory

**Six Months Later:**
- Zero similar incidents
- Deployment frequency increased 4x
- Engineers reported near-misses proactively
- Team satisfaction improved dramatically

**The Lesson:** Blame finds scapegoats. Blamelessness finds solutions.

---

## Common Postmortem Anti-Patterns

### Anti-Pattern 1: The Blame Game

```
Bad: "The outage was caused by Alice's careless mistake."
Good: "A configuration error reached production because
       our validation process didn't catch it."
```

### Anti-Pattern 2: Single Root Cause

```
Bad: "Root cause: Bad deployment"
Good: "Contributing factors:
       1. Missing automated tests
       2. No staging environment
       3. Time pressure to ship
       4. Unclear rollback procedure"
```

### Anti-Pattern 3: Vague Action Items

```
Bad: "Be more careful"
Good: "Add automated config validation to CI pipeline"

Bad: "Improve monitoring"
Good: "Add alert for config drift > 5%"

Bad: "Document better"
Good: "Write runbook for config deployment with rollback steps"
```

### Anti-Pattern 4: Action Item Graveyard

```
Bad: Action items created, never tracked, never completed
Good: Weekly review of open action items until all complete
```

### Anti-Pattern 5: Writing for Defense

```
Bad: Postmortem written to defend team, hide problems
Good: Postmortem written honestly, focuses on improvement
```

---

## Making Postmortems Effective

### 1. Psychological Safety

People need to feel safe sharing:
- Leadership models blamelessness
- Mistakes are treated as learning opportunities
- Postmortems are not used for performance reviews
- Contributors are thanked, not criticized

### 2. Time Investment

Postmortems take time but save more:
- 2-4 hours to write well
- 1-2 hours for meeting
- Time saved: Avoiding repeat incidents

### 3. Follow-Through

Action items must be completed:
- Assign owners and due dates
- Review weekly
- Escalate if stuck
- Celebrate completions

### 4. Broad Sharing

Learnings should spread:
- Post to shared wiki
- Present at team meetings
- Cross-team sharing sessions
- Digest for leadership

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Blame individuals | People hide, problems repeat | Focus on systems |
| One root cause | Oversimplifies, misses factors | Multiple contributing factors |
| Skip when busy | Never learn, same incidents | Make postmortems mandatory |
| Vague actions | Nothing actually changes | Specific, measurable actions |
| No follow-up | Actions never complete | Weekly tracking |
| Only share internally | Organization doesn't learn | Broad publication |

---

## Quiz: Check Your Understanding

### Question 1
What does "blameless" mean in the context of postmortems?

<details>
<summary>Show Answer</summary>

Blameless means:
- Focus on systems and processes, not individuals
- Assume good intentions
- Ask "why did the system allow this?" not "who screwed up?"
- Build better systems, not blame better individuals

Blameless does NOT mean:
- No accountability
- No consequences for negligence
- Ignoring patterns of behavior

The goal is to create psychological safety so people share honestly, leading to true root causes and effective fixes.

</details>

### Question 2
What's wrong with "be more careful" as an action item?

<details>
<summary>Show Answer</summary>

"Be more careful" is a terrible action item because:

1. **Not actionable**: What exactly should be done?
2. **Not measurable**: How do you know if it's complete?
3. **Relies on humans**: Humans will make mistakes; systems should catch them
4. **Doesn't change the system**: The same failure mode remains possible

Better action items:
- "Add automated validation for X"
- "Create checklist for Y process"
- "Implement alert when Z happens"
- "Write runbook for A procedure"

Action items should change the system, not ask humans to be better.

</details>

### Question 3
Why is "single root cause" an anti-pattern?

<details>
<summary>Show Answer</summary>

Single root cause is an anti-pattern because:

1. **Oversimplifies**: Incidents usually have multiple contributing factors
2. **Stops investigation early**: Once you find "the" cause, you stop looking
3. **Fixes less**: Only addresses one factor, others remain
4. **Misses systemic issues**: Often the system allowed multiple failures

Better approach: Identify all contributing factors:
- Technical factors
- Process factors
- Organizational factors
- Environmental factors

Each factor is an opportunity for improvement.

</details>

### Question 4
When should you skip writing a postmortem?

<details>
<summary>Show Answer</summary>

Almost never. Write postmortems for:
- All SEV-1 and SEV-2 incidents
- Interesting SEV-3 incidents
- Near misses (we got lucky)
- Recurring issues
- Data loss events
- Customer escalations

You might skip for:
- Truly trivial issues (SEV-4, quick fix, no learning)
- External factors completely outside your control
- When you've already postmortem'd identical incident recently

When in doubt, write the postmortem. The cost is low, the learning is valuable.

</details>

---

## Hands-On Exercise: Write a Postmortem

Practice writing a postmortem for a mock incident.

### The Incident

```
Scenario: Payment service outage

Timeline:
- 09:00: Developer deploys new version
- 09:05: Error rate jumps to 50%
- 09:15: On-call receives page
- 09:20: On-call begins investigation
- 09:35: On-call identifies bad database query in new code
- 09:40: On-call rolls back deployment
- 09:45: Error rate returns to normal
- 09:50: Incident declared resolved

Context:
- The developer was new to the team
- The code passed code review
- There were no automated tests
- The staging environment was broken
- The deployment happened on a Friday afternoon
```

### Your Task

Write a complete postmortem using the template.

**Focus on:**

1. **Summary**: 2-3 sentences
2. **Impact**: Duration, users affected, error budget impact
3. **Contributing Factors**: List at least 4 (not just "bad code")
4. **Action Items**: At least 5 specific, actionable items

### Hints for Contributing Factors

Think about:
- Why wasn't this caught in testing?
- Why was staging broken?
- Why was review not sufficient?
- Why was the developer unprepared?
- Why deploy on Friday afternoon?

### Success Criteria

- [ ] Summary is clear and concise
- [ ] Impact is quantified
- [ ] At least 4 contributing factors identified
- [ ] No blame on individuals
- [ ] At least 5 specific action items
- [ ] All action items have owners and due dates
- [ ] "What went well" section included

---

## Key Takeaways

1. **Blamelessness enables learning** — blame hides truth, safety reveals it
2. **Multiple factors, not single root cause** — incidents are complex
3. **Action items must be specific and tracked** — vague items accomplish nothing
4. **Share broadly** — learnings benefit the whole organization
5. **Process requires discipline** — postmortems must happen, not optional

---

## Further Reading

**Books**:
- **"Site Reliability Engineering"** — Chapter 15: Postmortem Culture
- **"The Field Guide to Human Error"** — Sidney Dekker

**Articles**:
- **"Blameless PostMortems"** — John Allspaw
- **"How to Write a Postmortem"** — PagerDuty

**Talks**:
- **"Blameless Post-Mortems"** — John Allspaw (Velocity 2012)
- **"Learning from Failure"** — J. Paul Reed

---

## Summary

Postmortems are how organizations learn from failure.

Effective postmortems:
- Create psychological safety through blamelessness
- Focus on systems, not individuals
- Identify multiple contributing factors
- Produce specific, actionable improvements
- Track actions to completion
- Share learnings broadly

Every incident should make your system stronger. Postmortems are how that happens.

---

## Next Module

Continue to [Module 1.7: Capacity Planning](module-1.7-capacity-planning/) to learn how to ensure your systems can handle future demand.

---

*"We are not the sum of our accidents. We are the sum of what we learn from them."* — Unknown
