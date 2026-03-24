# Module 4.6: Security Culture and Automation

> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 4.5: Runtime Security](module-4.5-runtime-security.md) — Completed DevSecOps technical modules
- **Required**: Experience working with development teams
- **Recommended**: Basic understanding of organizational change
- **Helpful**: Exposure to incident management

---

## Why This Module Matters

You can have the best security tools in the world. Scanners in every pipeline. Policies for every resource. Alerts for every anomaly.

**But if developers see security as "someone else's job," you've already lost.**

Tools don't create secure software. People do. Culture determines whether security is embraced or circumvented, whether vulnerabilities are reported or hidden, whether security is a shared value or a checkbox.

This final module brings together the human side of DevSecOps.

After this module, you'll understand:
- How to build a security-first culture
- Security champions programs that work
- Metrics that matter for measuring security
- Automating security operations at scale
- Continuous improvement practices

---

## Culture Eats Tools for Breakfast

### The Tool Trap

```
┌─────────────────────────────────────────────────────────────┐
│                  SECURITY MATURITY JOURNEY                   │
│                                                              │
│  PHASE 1: Buy Tools                                         │
│  "We need SAST, DAST, SCA, container scanning..."           │
│  Result: Dashboards full of red, developers overwhelmed     │
│                                                              │
│  PHASE 2: Tune Tools                                        │
│  "Too many false positives, let's configure..."             │
│  Result: Better signal, but still developers ignore alerts  │
│                                                              │
│  PHASE 3: Enforce Tools                                     │
│  "Block builds on Critical, mandatory security review..."   │
│  Result: Developers bypass or game the system               │
│                                                              │
│  PHASE 4: Culture Change                                    │
│  "Security is everyone's job, let's train and enable..."    │
│  Result: Developers own security, tools become helpful      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Signs of Poor Security Culture

| Symptom | What It Means |
|---------|---------------|
| "That's the security team's job" | Security seen as separate function |
| High bypass rate of security checks | Developers see tools as obstacles |
| Vulnerabilities hidden until audit | Fear of blame, no safe reporting |
| Same issues recurring repeatedly | No learning from incidents |
| Security as last-minute checkbox | Not integrated into workflow |

### Signs of Strong Security Culture

| Indicator | What It Shows |
|-----------|---------------|
| Developers fix issues before security asks | Ownership |
| Security findings decrease over time | Learning |
| Teams request security reviews early | Trust and value |
| Post-mortems are blameless and honest | Psychological safety |
| Security metrics are team metrics | Shared responsibility |

---

## The Security Champions Program

### What is a Security Champion?

A security champion is a developer who:
- Has deeper security knowledge than peers
- Advocates for security within their team
- Is the first point of contact for security questions
- Multiplies the security team's reach

```
┌─────────────────────────────────────────────────────────────┐
│              WITHOUT SECURITY CHAMPIONS                      │
│                                                              │
│  Security Team (5 people)                                   │
│         │                                                    │
│         └────────────▶ 100 Developers                       │
│                        (bottleneck)                          │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│              WITH SECURITY CHAMPIONS                         │
│                                                              │
│  Security Team (5 people)                                   │
│         │                                                    │
│         ├──▶ Champion (Team A) ──▶ 10 Devs                  │
│         ├──▶ Champion (Team B) ──▶ 10 Devs                  │
│         ├──▶ Champion (Team C) ──▶ 10 Devs                  │
│         ├──▶ ...                                            │
│         └──▶ Champion (Team J) ──▶ 10 Devs                  │
│                                                              │
│  10x reach, faster response, embedded expertise             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Building a Champions Program

**Step 1: Define the Role**
```markdown
## Security Champion Role

**Time Commitment**: 10-20% of work time

**Responsibilities**:
- Attend monthly security champion meetings
- Review security-relevant PRs for your team
- Be first responder for security questions
- Share security learnings with your team
- Participate in security training

**This is NOT**:
- A full-time security role
- A promotion or separate job
- An excuse to avoid regular work

**Benefits**:
- Specialized training and certifications
- Conference attendance budget
- Recognition in performance reviews
- Career growth in security path
```

**Step 2: Recruit Champions**
```markdown
## Champion Selection Criteria

**Must Have**:
- Interest in security (willing volunteers, not conscripts)
- Good communication skills
- Respected by peers
- At least 1 year with the company

**Nice to Have**:
- Some security background
- Past security contributions
- Architecture experience

**Selection Process**:
1. Manager nomination or self-nomination
2. Brief interview with security team
3. Probationary period (3 months)
4. Bi-directional opt-out if not working
```

**Step 3: Train and Enable**
```markdown
## Champion Training Program

**Month 1: Foundations**
- Secure coding practices (OWASP Top 10)
- Your organization's security tools
- How to triage security findings
- When to escalate to security team

**Month 2: Deep Dives**
- Authentication and authorization
- Secrets management
- Container security
- Your tech stack-specific risks

**Month 3: Practice**
- Conduct a security review (shadowed)
- Present a security topic to team
- Lead a threat modeling session

**Ongoing**:
- Monthly champion meetings
- Quarterly training updates
- Annual conference attendance
```

---

## Did You Know?

1. **The term "Security Champion" originated at Microsoft** in the early 2000s as part of their Security Development Lifecycle (SDL). The program helped them reduce security vulnerabilities in Windows by over 45%.

2. **Organizations with security champions programs** report 50% fewer critical vulnerabilities reaching production, according to a 2022 study by the DevSecOps Community.

3. **Google's "Project Zero"** is an elite security research team, but they also maintain thousands of internal security champions across product teams. The ratio is roughly 1 champion per 10-15 developers.

4. **The "blameless postmortem" concept** came from aviation safety culture, where the focus on learning over blame reduced fatal accidents by 90% over 50 years. Tech adopted this practice, and organizations like Etsy pioneered it in software.

---

## Metrics That Matter

### The Wrong Metrics

| Metric | Why It's Problematic |
|--------|---------------------|
| Number of vulnerabilities found | Incentivizes finding, not fixing |
| Time to security review | May rush reviews, miss issues |
| Security tickets closed | Incentivizes closing, not solving |
| Tools deployed | Measures capability, not outcomes |

### The Right Metrics

**1. Mean Time to Remediate (MTTR)**

```
MTTR = Time from vulnerability discovery to fix deployed

                     Discovery                           Fix Deployed
                         │                                    │
                         ▼                                    ▼
─────────────────────────●────────────────────────────────────●───────▶
                         │◀───────────────────────────────────▶│
                                        MTTR

Target MTTR by severity:
- Critical: < 24 hours
- High: < 7 days
- Medium: < 30 days
- Low: < 90 days
```

**2. Escape Rate**

```
Escape Rate = Vulnerabilities found in production
              ─────────────────────────────────────
              Total vulnerabilities found

Goal: Minimize. Catch issues before production.

Healthy: < 5% escape to production
Concerning: > 20% escape to production
```

**3. Coverage**

```
Pipeline Coverage = Repos with security scanning
                    ───────────────────────────
                    Total repos

Container Coverage = Images scanned before deploy
                     ───────────────────────────
                     Total images deployed

Goal: 100% coverage
```

**4. Risk Reduction Over Time**

```
Trend of Critical/High Vulnerabilities

  Vulns
    │
 30 │  ●
    │    ●
 20 │      ●
    │        ●
 10 │          ●  ●  ●  ●
    │                      ●  ●
  0 │──────────────────────────────▶ Time
    Jan Feb Mar Apr May Jun Jul Aug

This is what healthy security looks like.
New code is more secure than old code.
```

### Security Scorecard

```markdown
## Team Security Scorecard - Q4 2024

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| MTTR (Critical) | < 24h | 18h | ✅ |
| MTTR (High) | < 7d | 5.2d | ✅ |
| Escape Rate | < 5% | 3.2% | ✅ |
| Pipeline Coverage | 100% | 98% | ⚠️ |
| Container Scanning | 100% | 100% | ✅ |
| Champion Ratio | 1:15 | 1:12 | ✅ |
| Training Completion | 100% | 87% | ⚠️ |

**Trend**: Improving quarter-over-quarter
**Focus Areas**: Pipeline coverage for new repos, training completion
```

---

## Automating Security Operations

### The SecOps Automation Pyramid

```
┌─────────────────────────────────────────────────────────────┐
│               AUTOMATION MATURITY LEVELS                     │
│                                                              │
│                        ▲                                     │
│                       ╱ ╲                                    │
│                      ╱   ╲   Autonomous                      │
│                     ╱ L5  ╲  Response                        │
│                    ╱───────╲                                 │
│                   ╱    L4   ╲  Automated                     │
│                  ╱───────────╲ Remediation                   │
│                 ╱     L3      ╲  Orchestrated                │
│                ╱───────────────╲ Workflows                   │
│               ╱      L2         ╲  Automated                 │
│              ╱───────────────────╲ Detection                 │
│             ╱        L1           ╲  Manual with             │
│            ╱─────────────────────────╲ Tools                 │
│           ╱          L0               ╲                      │
│          ╱─────────────────────────────╲ Manual              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Level 2: Automated Detection

```yaml
# GitHub Actions: Auto-create issues for vulnerabilities
name: Security Issue Creator
on:
  workflow_run:
    workflows: ["Security Scan"]
    types: [completed]

jobs:
  create-issues:
    runs-on: ubuntu-latest
    steps:
      - name: Download scan results
        uses: actions/download-artifact@v3
        with:
          name: security-results

      - name: Create issues for critical findings
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('trivy-results.json'));

            for (const vuln of results.Results[0].Vulnerabilities) {
              if (vuln.Severity === 'CRITICAL') {
                await github.rest.issues.create({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  title: `[Security] ${vuln.VulnerabilityID}: ${vuln.Title}`,
                  body: `
## Vulnerability Details
- **ID**: ${vuln.VulnerabilityID}
- **Severity**: ${vuln.Severity}
- **Package**: ${vuln.PkgName}@${vuln.InstalledVersion}
- **Fixed in**: ${vuln.FixedVersion || 'No fix available'}

## Description
${vuln.Description}

## Reference
${vuln.PrimaryURL}

## SLA
Critical vulnerabilities must be remediated within 24 hours.
                  `,
                  labels: ['security', 'critical', 'automated']
                });
              }
            }
```

### Level 3: Orchestrated Workflows

```yaml
# Slack + Jira + GitHub integration
name: Security Orchestration

on:
  issues:
    types: [labeled]

jobs:
  orchestrate:
    if: contains(github.event.label.name, 'security-critical')
    runs-on: ubuntu-latest
    steps:
      # 1. Alert Slack
      - name: Notify Security Channel
        uses: slackapi/slack-github-action@v1
        with:
          channel-id: 'security-alerts'
          payload: |
            {
              "text": "🚨 Critical Security Issue",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Critical Security Issue*\n<${{ github.event.issue.html_url }}|${{ github.event.issue.title }}>"
                  }
                }
              ]
            }

      # 2. Create Jira ticket
      - name: Create Jira Issue
        uses: atlassian/gajira-create@v3
        with:
          project: SEC
          issuetype: Bug
          summary: ${{ github.event.issue.title }}
          description: |
            GitHub Issue: ${{ github.event.issue.html_url }}

            ${{ github.event.issue.body }}

      # 3. Page on-call if after hours
      - name: Check business hours
        id: hours
        run: |
          hour=$(date +%H)
          if [ $hour -lt 9 ] || [ $hour -gt 17 ]; then
            echo "after_hours=true" >> $GITHUB_OUTPUT
          fi

      - name: Page on-call
        if: steps.hours.outputs.after_hours == 'true'
        uses: pagerduty/trigger-incident@v1
        with:
          routing-key: ${{ secrets.PAGERDUTY_KEY }}
          event-action: trigger
          summary: 'Critical security vulnerability requires immediate attention'
```

### Level 4: Automated Remediation

```yaml
# Auto-update vulnerable dependencies
name: Auto-Remediate

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for vulnerabilities
        id: scan
        run: |
          trivy fs --severity CRITICAL,HIGH --format json . > vulns.json

      - name: Update vulnerable packages
        run: |
          # Parse vulns and update
          npm audit fix --force || true
          pip install --upgrade $(pip list --outdated --format=json | jq -r '.[].name') || true

      - name: Create PR if changes
        uses: peter-evans/create-pull-request@v5
        with:
          title: "Security: Auto-remediate vulnerabilities"
          body: |
            This PR automatically updates packages with known vulnerabilities.

            ## Scan Results
            $(cat vulns.json | jq -r '.Results[].Vulnerabilities[] | "- \(.VulnerabilityID): \(.PkgName)"')

            ## Testing
            - [ ] All tests pass
            - [ ] Application works as expected
          branch: security/auto-remediation
          labels: security,automated
```

---

## War Story: The Culture Turnaround

A mid-sized SaaS company had a security problem. Not technical—cultural.

**The Symptoms:**
- Average MTTR for Critical vulnerabilities: 47 days
- Developers actively avoided security reviews
- Security team seen as "the department of no"
- Same vulnerabilities appearing quarterly

**The Intervention:**

**Month 1: Listening**
```
Security team conducted 30 developer interviews:
"What's your experience with security here?"

Common responses:
- "Security just blocks our releases"
- "I don't understand the findings"
- "When I ask for help, they're too busy"
- "We have no time budgeted for security"
```

**Month 2: Quick Wins**
```
1. Fixed the biggest pain point: Pre-commit hooks that took 10 minutes
   → Reduced to 30 seconds (moved heavy scans to CI)

2. Created a Slack channel for security questions
   → Response time < 4 hours guaranteed

3. Added "security" as a planning category
   → Teams now explicitly plan security work
```

**Month 3: Security Champions Launch**
```
Recruited 8 volunteers (1 per team)

Training program:
- Week 1: Secure coding fundamentals
- Week 2: Company-specific tools
- Week 3: How to conduct security reviews
- Week 4: Threat modeling workshop

Champions became the first line of support
```

**Month 6: Measurement**
```
Results:
- MTTR Critical: 47 days → 3 days
- MTTR High: 60 days → 12 days
- Developer satisfaction with security: 3.2 → 7.8 / 10
- Security review requests: +300%

Champions received first security questions,
freeing security team for architecture reviews
```

**Month 12: Culture Shift**
```
"Security is part of how we build" - CTO

Observable changes:
- Developers now fix issues before pushing
- Teams request security design reviews early
- Post-mortems include security lessons
- Security champions are valued team members
```

**The Key Insight:**

The technology didn't change much. The tools were similar. What changed was:
1. Security team became **enablers**, not gatekeepers
2. Developers had **skin in the game** (champions)
3. Security work was **visible and planned**
4. Feedback was **fast and actionable**

---

## Continuous Improvement

### The Security Improvement Loop

```
┌─────────────────────────────────────────────────────────────┐
│               CONTINUOUS IMPROVEMENT LOOP                    │
│                                                              │
│          ┌─────────────────────────────────────┐            │
│          │                                      │            │
│          ▼                                      │            │
│    ┌──────────┐      ┌──────────┐      ┌───────┴──┐         │
│    │  MEASURE │─────▶│ ANALYZE  │─────▶│  IMPROVE │         │
│    │          │      │          │      │          │         │
│    │ Metrics  │      │ Root     │      │ Actions  │         │
│    │ Incidents│      │ Causes   │      │ Training │         │
│    │ Trends   │      │ Patterns │      │ Tools    │         │
│    └──────────┘      └──────────┘      └──────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Blameless Postmortems

```markdown
## Security Incident Postmortem Template

### Incident Summary
- **Date**: 2024-01-15
- **Duration**: 4 hours
- **Severity**: High
- **Impact**: API credentials exposed in public repo

### Timeline
- 09:00: Developer pushes code including API key
- 09:15: GitHub secret scanning alerts
- 09:45: Alert reaches security team (30 min delay)
- 10:00: Key rotated
- 13:00: Root cause identified and fixed

### What Went Well
- GitHub secret scanning caught it
- Developer immediately acknowledged mistake
- Key rotation was quick

### What Went Wrong
- Alert took 30 minutes to reach security team
- Pre-commit hooks weren't installed for this repo
- No documentation on handling secret exposure

### Root Causes
1. Onboarding didn't include pre-commit hook setup
2. Alert routing went to email, not Slack
3. Runbook for secret exposure didn't exist

### Action Items
| Action | Owner | Due |
|--------|-------|-----|
| Add pre-commit to onboarding checklist | @onboarding | 2024-01-20 |
| Route GitHub alerts to Slack | @security | 2024-01-17 |
| Write secret exposure runbook | @security | 2024-01-22 |

### Lessons Learned
- Defense in depth works (multiple layers caught this)
- Speed matters (rotation within 1 hour)
- Gaps in alerting are gaps in response
```

### Monthly Security Review

```markdown
## Monthly Security Review - January 2024

### Key Metrics
| Metric | This Month | Last Month | Trend |
|--------|------------|------------|-------|
| Critical Vulns Found | 12 | 18 | ↓ 33% |
| MTTR Critical | 2.1 days | 3.4 days | ↓ 38% |
| Escape Rate | 4.2% | 5.1% | ↓ 18% |
| Pipeline Coverage | 97% | 95% | ↑ 2% |

### Incidents
1. Secret exposure (resolved, no impact)
2. Dependency vulnerability (patched within SLA)

### Champion Activity
- 15 security reviews conducted
- 3 threat modeling sessions
- 2 training sessions delivered

### Focus for Next Month
1. Improve pre-commit adoption (target: 100%)
2. Reduce DAST scan time (currently 45 min)
3. Complete container signing rollout

### Recognition
@jane-doe - Caught SQL injection in code review
@john-smith - Delivered excellent XSS training
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Blaming developers | Creates fear, hides issues | Blameless culture, focus on systems |
| Security as gatekeeper | Friction, bypass | Security as enabler, self-service |
| Vanity metrics | Looks good, means nothing | Outcome-based metrics (MTTR, escape rate) |
| Champions as unpaid work | Burnout, no volunteers | Explicit time allocation, recognition |
| One-time training | Knowledge fades | Continuous, just-in-time learning |
| No feedback loop | Same mistakes repeat | Postmortems, trend analysis |

---

## Quiz: Check Your Understanding

### Question 1
A developer bypasses the security pipeline with `--no-verify` and ships a vulnerability to production. What should happen?

<details>
<summary>Show Answer</summary>

**This is a systems problem, not a people problem.**

**Wrong response:**
- Blame the developer
- "Name and shame" in meetings
- Threaten consequences

**Right response:**

1. **Fix the immediate issue**: Patch the vulnerability

2. **Blameless postmortem**:
   - Why did the developer bypass?
   - Was the check too slow? (Fix the check)
   - Was there deadline pressure? (Address planning)
   - Didn't understand the risk? (Improve training)

3. **Systemic fixes**:
   - Move critical checks to server-side (can't bypass)
   - Make client-side checks faster (less incentive to skip)
   - Track bypass rate as a metric
   - Address root causes (deadlines, training)

4. **Conversation with developer**:
   - Understand their perspective
   - Explain the risk
   - Collaborate on solutions

**The goal**: Make it easier to do the right thing than to bypass. If bypassing is common, the system is broken.

</details>

### Question 2
Your MTTR for Critical vulnerabilities is 30 days. The target is 24 hours. How do you improve?

<details>
<summary>Show Answer</summary>

**Break down MTTR into components:**

```
MTTR = Detection Time + Triage Time + Assignment Time +
       Fix Development + Review Time + Deploy Time
```

**Analyze each component:**

| Component | Current | Target | Actions |
|-----------|---------|--------|---------|
| Detection | 2 days | 0 | Automate scanning, real-time alerts |
| Triage | 3 days | 2 hours | Clear severity criteria, on-call |
| Assignment | 5 days | 2 hours | Auto-assign to team/champion |
| Fix Dev | 10 days | 4 hours | Training, pre-built patches |
| Review | 5 days | 4 hours | Expedited review process |
| Deploy | 5 days | 4 hours | Hotfix deployment path |

**Key improvements:**

1. **Alerting**: Critical vulns page immediately
2. **Clear ownership**: Auto-route to owning team
3. **SLA enforcement**: Make SLA visible, track
4. **Remove blockers**: Fast-track for security fixes
5. **Pre-approved fixes**: Dependency updates auto-merge

**Cultural changes:**

- Security SLAs are non-negotiable
- Teams have capacity for security work
- Critical = drop everything
- Champions empower immediate response

</details>

### Question 3
A new developer says "I don't know anything about security. That's the security team's job." How do you respond?

<details>
<summary>Show Answer</summary>

**This is a teachable moment, not a failure.**

**Response:**

1. **Acknowledge their honesty**:
   "Thanks for being upfront. Many developers feel this way starting out."

2. **Explain shared responsibility**:
   "In our culture, everyone owns security. The security team helps, but they can't be everywhere. You're the expert on your code—you'll catch things they'd miss."

3. **Make it manageable**:
   "You don't need to be an expert. Start with:
   - Trust the pipeline warnings
   - Ask your security champion
   - Take the secure coding training
   That's 80% of what you need."

4. **Provide resources**:
   - Security champion introduction
   - Secure coding training link
   - Slack channel for questions
   - Office hours schedule

5. **Set expectations**:
   "Within 3 months, you should be comfortable:
   - Fixing security findings in your PRs
   - Knowing when to ask for help
   - Understanding basic risks (XSS, SQL injection)"

6. **Follow up**:
   Check in after their first security finding. Make sure they have support.

**Key point**: Everyone starts knowing nothing about security. Create a path from "I don't know" to "I'm confident with the basics."

</details>

### Question 4
Your security champions program has 50% participation after 6 months. How do you improve?

<details>
<summary>Show Answer</summary>

**Diagnose before prescribing:**

1. **Survey current and former champions**:
   - What's working?
   - What's frustrating?
   - Why did people leave?

**Common issues and solutions:**

| Issue | Solution |
|-------|----------|
| No time allocated | Work with managers on explicit 20% time |
| Training is boring | Make it hands-on, CTF-style |
| Feels unrewarded | Add to performance criteria, public recognition |
| Too much responsibility | Reduce scope, better support |
| No impact visible | Share metrics, show contribution |
| Better champions got promoted | Good! Recruit new ones |

2. **Improve the value proposition**:
   ```markdown
   ## What Champions Get
   - Specialized training (SANS, conferences)
   - Recognition in performance reviews
   - Path to security roles
   - First access to new tools
   - Direct line to security leadership
   ```

3. **Reduce friction**:
   - Clear, limited expectations
   - Good tooling
   - Security team backup
   - Written escalation paths

4. **Celebrate success**:
   - Monthly champion spotlight
   - Bugs caught = public kudos
   - Annual champion awards

**Metric target**: 80%+ active participation, 90%+ team coverage

</details>

---

## Hands-On Exercise: Build Security Automation

Implement automated security operations using GitHub Actions.

### Part 1: Setup Security Orchestration Repository

```bash
# Create a new repository for security automation
mkdir security-automation && cd security-automation
git init

# Create directory structure
mkdir -p .github/workflows templates scripts
```

### Part 2: Create Automated Vulnerability Issue Creator

```yaml
# .github/workflows/create-security-issues.yml
cat > .github/workflows/create-security-issues.yml << 'EOF'
name: Security Issue Automation
on:
  workflow_dispatch:
    inputs:
      severity:
        description: 'Minimum severity to create issues for'
        required: true
        default: 'HIGH'
        type: choice
        options:
          - CRITICAL
          - HIGH
          - MEDIUM

jobs:
  scan-and-create-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'json'
          output: 'trivy-results.json'
          severity: ${{ github.event.inputs.severity }}

      - name: Create issues for findings
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('trivy-results.json'));

            for (const result of results.Results || []) {
              for (const vuln of result.Vulnerabilities || []) {
                // Check if issue already exists
                const existing = await github.rest.issues.listForRepo({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  state: 'open',
                  labels: 'security,automated'
                });

                const exists = existing.data.some(i =>
                  i.title.includes(vuln.VulnerabilityID)
                );

                if (!exists) {
                  await github.rest.issues.create({
                    owner: context.repo.owner,
                    repo: context.repo.repo,
                    title: `[Security] ${vuln.VulnerabilityID}: ${vuln.PkgName}`,
                    body: `## Vulnerability Details

**Severity**: ${vuln.Severity}
**Package**: ${vuln.PkgName}@${vuln.InstalledVersion}
**Fixed In**: ${vuln.FixedVersion || 'No fix available'}

## Description
${vuln.Description || 'No description available'}

## References
- ${vuln.PrimaryURL || 'N/A'}

## SLA
- CRITICAL: 24 hours
- HIGH: 7 days
- MEDIUM: 30 days

---
*This issue was automatically created by security scanning.*`,
                    labels: ['security', 'automated', vuln.Severity.toLowerCase()]
                  });
                  console.log(`Created issue for ${vuln.VulnerabilityID}`);
                }
              }
            }
EOF
```

### Part 3: Create Security Metrics Dashboard

```yaml
# .github/workflows/security-metrics.yml
cat > .github/workflows/security-metrics.yml << 'EOF'
name: Security Metrics Report
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  generate-metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Calculate metrics
        uses: actions/github-script@v7
        id: metrics
        with:
          script: |
            // Get security issues
            const issues = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'security',
              state: 'all',
              per_page: 100
            });

            // Calculate MTTR
            let totalTime = 0;
            let closedCount = 0;

            for (const issue of issues.data) {
              if (issue.closed_at) {
                const created = new Date(issue.created_at);
                const closed = new Date(issue.closed_at);
                const days = (closed - created) / (1000 * 60 * 60 * 24);
                totalTime += days;
                closedCount++;
              }
            }

            const mttr = closedCount > 0 ? (totalTime / closedCount).toFixed(1) : 'N/A';
            const openCount = issues.data.filter(i => !i.closed_at).length;

            // Count by severity
            const critical = issues.data.filter(i =>
              i.labels.some(l => l.name === 'critical') && !i.closed_at
            ).length;
            const high = issues.data.filter(i =>
              i.labels.some(l => l.name === 'high') && !i.closed_at
            ).length;

            return {
              mttr,
              openCount,
              closedCount,
              critical,
              high
            };

      - name: Post metrics to issue
        uses: actions/github-script@v7
        with:
          script: |
            const metrics = ${{ steps.metrics.outputs.result }};
            const date = new Date().toISOString().split('T')[0];

            const body = `# Security Metrics Report - ${date}

## Summary
| Metric | Value |
|--------|-------|
| Open Security Issues | ${metrics.openCount} |
| Closed This Period | ${metrics.closedCount} |
| MTTR (days) | ${metrics.mttr} |
| Open Critical | ${metrics.critical} |
| Open High | ${metrics.high} |

## Trend
- 📊 Track weekly to see improvement
- 🎯 Target MTTR: < 7 days
- ⚠️ Critical issues should be 0

---
*Generated automatically every Monday*`;

            // Find or create metrics tracking issue
            const issues = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'metrics',
              state: 'open'
            });

            if (issues.data.length > 0) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issues.data[0].number,
                body: body
              });
            } else {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: '📊 Security Metrics Tracking',
                body: body,
                labels: ['metrics', 'security']
              });
            }
EOF
```

### Part 4: Create Slack Alert Integration

```yaml
# .github/workflows/security-alerts.yml
cat > .github/workflows/security-alerts.yml << 'EOF'
name: Security Alert Notifications
on:
  issues:
    types: [labeled]

jobs:
  notify-critical:
    if: github.event.label.name == 'critical'
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚨 Critical Security Issue Created",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*🚨 CRITICAL Security Issue*\n<${{ github.event.issue.html_url }}|${{ github.event.issue.title }}>\n\n*SLA: 24 hours*"
                  }
                },
                {
                  "type": "section",
                  "fields": [
                    {
                      "type": "mrkdwn",
                      "text": "*Repository:*\n${{ github.repository }}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "*Created by:*\n${{ github.event.issue.user.login }}"
                    }
                  ]
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK
EOF
```

### Part 5: Test the Automation

```bash
# Initialize git and push
git add .
git commit -m "Add security automation workflows"

# Create a test repository on GitHub and push
# gh repo create security-automation --public --source=. --push

# Or push to existing repo
# git remote add origin https://github.com/YOUR_USERNAME/security-automation.git
# git push -u origin main

# Trigger the workflow manually from GitHub Actions tab
# Or add a vulnerable requirements.txt to test:
cat > requirements.txt << 'EOF'
requests==2.25.0
pyyaml==5.3.1
EOF

git add requirements.txt
git commit -m "Add dependencies for testing"
git push
```

### Success Criteria

- [ ] Created automated issue creation workflow
- [ ] Created security metrics dashboard workflow
- [ ] Created Slack notification workflow
- [ ] Tested workflows create issues automatically
- [ ] Verified metrics are calculated correctly
- [ ] Understand how to extend for your organization

---

## Key Takeaways

1. **Culture > Tools** — Tools are multipliers; without culture, they're shelfware
2. **Security champions scale** — Embedded expertise multiplies security team reach
3. **Measure outcomes** — MTTR, escape rate, coverage—not activity metrics
4. **Automate operations** — Detection, routing, remediation at scale
5. **Continuous improvement** — Blameless postmortems, monthly reviews, trend analysis

---

## Further Reading

**Books:**
- **"Building a Security Culture"** — Kai Roer
- **"The DevOps Handbook"** — Kim, Humble, Debois, Willis (security chapter)
- **"Accelerate"** — Forsgren, Humble, Kim (metrics)

**Programs:**
- **OWASP SAMM** — Software Assurance Maturity Model
- **BSIMM** — Building Security In Maturity Model
- **Microsoft SDL** — Security Development Lifecycle

**Talks:**
- **"Sprinting to Security"** — Netflix security (YouTube)
- **"DevSecOps: Security at Speed"** — Shannon Lietz (RSA)

---

## Summary

Security culture is the foundation everything else rests on:

- **Tools without culture** → Ignored, bypassed, resented
- **Culture without tools** → Good intentions, poor outcomes
- **Culture with tools** → Multiplied impact, sustainable security

Building culture requires:
- Leadership commitment
- Security champions embedded in teams
- Metrics that matter (MTTR, escape rate)
- Automation at scale
- Continuous, blameless improvement

The goal is a world where security is "how we build," not "what blocks us."

---

## Track Complete

🎉 Congratulations! You've completed the DevSecOps discipline track.

**What you've learned:**
- Module 4.1: DevSecOps fundamentals and shift-left philosophy
- Module 4.2: Pre-commit security and developer tooling
- Module 4.3: CI/CD pipeline security integration
- Module 4.4: Supply chain security with SBOMs and signing
- Module 4.5: Runtime security and threat detection
- Module 4.6: Building security culture and automation

**Next steps:**
- Apply these concepts to your organization
- Start a security champions program
- Implement the metrics discussed
- Continue to the [DevSecOps Toolkit](../../toolkits/security-tools/README.md) for hands-on tool implementations

---

*"Security is everyone's job. Culture is how you make that real."*
