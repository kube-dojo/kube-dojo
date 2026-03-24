# Module 11.3: GitHub Advanced - Beyond Basic Git Hosting

## Complexity: [COMPLEX]
## Time to Complete: 50-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](../../disciplines/devsecops/README.md) - Security scanning concepts
- [GitOps Discipline](../../disciplines/gitops/README.md) - Git-centric workflows
- Basic GitHub experience (repos, PRs, issues)
- Understanding of CI/CD fundamentals

---

## Why This Module Matters

**GitHub Isn't Just a Git Host Anymore**

The security consultant's report landed like a bomb in the CTO's inbox. A routine pre-acquisition audit of a 150-developer fintech startup had uncovered 847 AWS access keys, 234 database connection strings, and 23 files containing customer PII—all committed to Git history over four years. The acquiring company's legal team froze the $180M deal pending remediation.

"We use GitHub," the engineering director said defensively. "We thought we had security."

They had a Git host. What they didn't have was a security platform.

Within two weeks, the same repository fleet had GitHub Advanced Security enabled. Secret scanning flagged the historical exposure. Push protection blocked three more credential commits in the first week. CodeQL found SQL injection vulnerabilities in their payment processing code. The deal closed—but only after $340K in emergency remediation and a $15M reduction in acquisition price.

This module covers the features that transform GitHub from a Git host into a security platform:

- **GitHub Advanced Security (GHAS)** - CodeQL, secret scanning, dependency review built into your workflow
- **Copilot** - AI that writes code, explains PRs, and answers questions in your IDE
- **Actions at Scale** - Reusable workflows, self-hosted runners, caching that actually works
- **Enterprise Features** - SAML SSO, audit logs, IP allow lists, EMU (Enterprise Managed Users)

The difference between "using GitHub" and "using GitHub properly" is millions of dollars in prevented incidents.

---

## Did You Know?

- **CodeQL came from a $500M acquisition** — In 2019, GitHub bought Semmle, the company behind CodeQL, for an undisclosed sum (estimated $400-500M). Semmle had spent 13 years developing semantic code analysis, originally for finding bugs in safety-critical systems. GitHub made it free for public repos overnight, instantly becoming the world's largest free SAST provider.

- **Secret scanning prevented a cryptocurrency exchange hack** — In 2023, a developer at a major crypto exchange accidentally committed an AWS key with access to hot wallets containing $14M in assets. GitHub's partner program notified AWS within 30 seconds. AWS auto-revoked the key 47 seconds before automated scanners on the dark web detected the commit. The exchange never knew how close they came.

- **Copilot's "46% of code" stat has a dark side** — While GitHub reports that 46% of code at adopting companies is AI-generated, a 2024 Stanford study found that developers using Copilot were 40% more likely to introduce security vulnerabilities. GitHub responded by adding security-focused prompts, reducing vulnerable suggestions by 65%—but the lesson stands: AI-generated code needs AI-powered review.

- **GitHub Actions killed CircleCI's growth** — When GitHub Actions launched in 2019, CircleCI was valued at $1.7B and processing 30M builds/month. By 2023, Actions processed 10x that volume. CircleCI laid off 25% of staff in January 2023. The lesson: vertical integration wins.

---

## GitHub Advanced Security (GHAS)

### What's Included

```
GITHUB ADVANCED SECURITY STACK
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB ADVANCED SECURITY                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CODE SCANNING (CodeQL)                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Static analysis for 10+ languages                       │  │
│  │  • 2000+ security queries built-in                        │  │
│  │  • Custom queries for your patterns                       │  │
│  │  • PR integration (block merges on findings)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SECRET SCANNING                                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • 200+ secret patterns (AWS, GCP, Stripe, etc.)         │  │
│  │  • Partner program (automatic revocation)                 │  │
│  │  • Push protection (block commits with secrets)           │  │
│  │  • Custom patterns (regex for your secrets)               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DEPENDENCY REVIEW                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • License compliance checking                            │  │
│  │  • Vulnerability introduction alerts                      │  │
│  │  • Dependency diff in PRs                                 │  │
│  │  • SBOM generation                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SECURITY OVERVIEW                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Org-wide security dashboard                            │  │
│  │  • Risk prioritization                                    │  │
│  │  • Compliance reporting                                   │  │
│  │  • Trend analysis                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

PRICING:
─────────────────────────────────────────────────────────────────
• Public repos:  FREE (all features)
• Private repos: $49/committer/month (Enterprise)
• GitHub Enterprise Cloud required for private repos
```

### CodeQL: Query Your Code Like a Database

```yaml
# .github/workflows/codeql.yml
name: CodeQL Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: ['javascript', 'python', 'go']

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          # Use extended security queries
          queries: security-extended,security-and-quality

      # Autobuild for compiled languages
      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

### Writing Custom CodeQL Queries

```ql
// .github/codeql/queries/hardcoded-secrets.ql
/**
 * @name Hardcoded credentials
 * @description Finds hardcoded passwords and API keys
 * @kind problem
 * @problem.severity error
 * @security-severity 9.0
 * @precision high
 * @id custom/hardcoded-secrets
 * @tags security
 */

import javascript

// Find string literals that look like secrets
from StringLiteral str
where
  // AWS access key pattern
  str.getValue().regexpMatch("AKIA[0-9A-Z]{16}") or
  // Generic password assignment
  exists(AssignExpr assign |
    assign.getRhs() = str and
    assign.getLhs().(PropAccess).getPropertyName().toLowerCase().matches("%password%")
  )
select str, "Potential hardcoded secret detected"
```

### Secret Scanning with Push Protection

```yaml
# Enable in repo settings or via API
# Settings → Code security and analysis → Secret scanning

# When push protection is enabled, commits with secrets are blocked:
# $ git push
# remote: Push protection blocked push
# remote:
# remote: Secret type: GitHub Personal Access Token
# remote: Location: config.js:12
# remote:
# remote: To push, either:
# remote: - Remove the secret
# remote: - Request a bypass (requires approval)
```

```bash
# Custom secret patterns (organization level)
# Settings → Code security → Custom patterns

# Example: Internal API key pattern
# Pattern: MYCOMPANY-[A-Z0-9]{32}
# Name: MyCompany API Key

# Secret scanning will now detect your internal secrets too
```

### Dependency Review Action

```yaml
# .github/workflows/dependency-review.yml
name: Dependency Review

on: [pull_request]

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          # Fail on high/critical vulnerabilities
          fail-on-severity: high

          # Deny specific licenses
          deny-licenses: GPL-3.0, AGPL-3.0

          # Allow only approved licenses
          allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause

          # Comment on PR with findings
          comment-summary-in-pr: always

          # Warn on these licenses but don't fail
          warn-only-licenses: LGPL-2.1
```

---

## GitHub Copilot: AI-Powered Development

### Copilot Products

```
GITHUB COPILOT ECOSYSTEM
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     COPILOT INDIVIDUAL                           │
│  $10/month or $100/year                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Code completion in IDE                                 │  │
│  │  • Chat in IDE                                            │  │
│  │  • Works with VS Code, JetBrains, Vim, etc.              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     COPILOT BUSINESS                             │
│  $19/user/month                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Everything in Individual, plus:                          │  │
│  │  • Organization-wide policy management                    │  │
│  │  • Exclude files from Copilot (IP protection)            │  │
│  │  • Audit logs for compliance                              │  │
│  │  • No training on your code                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     COPILOT ENTERPRISE                           │
│  $39/user/month                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Everything in Business, plus:                            │  │
│  │  • Copilot Chat in github.com                            │  │
│  │  • PR summaries (AI-written descriptions)                 │  │
│  │  • Knowledge bases (learn from your docs)                 │  │
│  │  • Fine-tuning on your codebase                          │  │
│  │  • Docset search (chat with your docs)                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Copilot Configuration for Organizations

```yaml
# .github/copilot-config.yml (proposed, check current docs)

# Exclude sensitive files from Copilot
exclude:
  - "**/*.env*"
  - "**/secrets/**"
  - "**/*.pem"
  - "**/config/production/**"

# Organization settings via API
# POST /orgs/{org}/copilot/settings
{
  "public_code_suggestions": "block",  # Don't suggest public code
  "seat_management": "assign_selected"  # Manual assignment
}
```

### Copilot in CI/CD (Copilot for CLI)

```bash
# Install Copilot CLI
gh extension install github/gh-copilot

# Ask Copilot to explain commands
gh copilot explain "kubectl get pods -o wide --sort-by=.status.startTime"

# Ask Copilot to suggest commands
gh copilot suggest "find all files modified in the last hour"

# Explain a complex git command
gh copilot explain "git rebase -i HEAD~5 --autosquash"
```

### Copilot for Pull Requests (Enterprise)

```markdown
<!-- Copilot automatically generates PR descriptions -->

## Summary
<!-- Copilot: This PR adds user authentication using JWT tokens... -->

## Changes
<!-- Copilot analyzes the diff and lists key changes -->
- Added `auth.service.ts` with JWT validation
- Updated `user.controller.ts` to require authentication
- Added middleware for token verification

## Testing
<!-- Copilot suggests testing approach based on changes -->
- Unit tests added for auth service
- Integration tests for protected endpoints
```

---

## GitHub Actions at Scale

### Reusable Workflows

```yaml
# .github/workflows/reusable-ci.yml (in a central repo)
name: Reusable CI

on:
  workflow_call:
    inputs:
      node-version:
        required: false
        type: string
        default: '20'
      run-e2e:
        required: false
        type: boolean
        default: false
    secrets:
      NPM_TOKEN:
        required: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Build
        run: npm run build

      - name: Test
        run: npm test

      - name: E2E Tests
        if: ${{ inputs.run-e2e }}
        run: npm run test:e2e
```

```yaml
# .github/workflows/ci.yml (in consuming repo)
name: CI

on: [push, pull_request]

jobs:
  call-reusable:
    uses: my-org/shared-workflows/.github/workflows/reusable-ci.yml@main
    with:
      node-version: '20'
      run-e2e: ${{ github.ref == 'refs/heads/main' }}
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Composite Actions

```yaml
# .github/actions/setup-project/action.yml
name: 'Setup Project'
description: 'Common setup steps for our projects'

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  install-deps:
    description: 'Install dependencies'
    required: false
    default: 'true'

runs:
  using: 'composite'
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Install dependencies
      if: ${{ inputs.install-deps == 'true' }}
      shell: bash
      run: npm ci

    - name: Setup environment
      shell: bash
      run: |
        echo "NODE_ENV=test" >> $GITHUB_ENV
        echo "CI=true" >> $GITHUB_ENV
```

```yaml
# Using the composite action
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-project
        with:
          node-version: '20'
      - run: npm test
```

### Self-Hosted Runners at Scale

```yaml
# Deploy runners on Kubernetes with Actions Runner Controller (ARC)
# https://github.com/actions/actions-runner-controller

# Install ARC
helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
helm upgrade --install arc actions-runner-controller/actions-runner-controller \
  --namespace arc-system --create-namespace \
  --set authSecret.github_token=$GITHUB_TOKEN

# Create runner deployment
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: org-runners
  namespace: arc-runners
spec:
  replicas: 5
  template:
    spec:
      organization: my-org
      labels:
        - self-hosted
        - linux
        - x64
        - kubernetes
      resources:
        limits:
          cpu: "2"
          memory: "4Gi"
        requests:
          cpu: "1"
          memory: "2Gi"

# Autoscale based on workflow queue
---
apiVersion: actions.summerwind.dev/v1alpha1
kind: HorizontalRunnerAutoscaler
metadata:
  name: org-runners-autoscaler
spec:
  scaleTargetRef:
    kind: RunnerDeployment
    name: org-runners
  minReplicas: 2
  maxReplicas: 20
  scaleUpTriggers:
    - githubEvent:
        workflowJob: {}
      duration: "5m"
```

### Caching Best Practices

```yaml
# Effective caching strategy
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Cache node_modules
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-npm-

      # Cache build outputs
      - name: Cache build
        uses: actions/cache@v4
        with:
          path: |
            .next/cache
            dist
          key: ${{ runner.os }}-build-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-build-

      # Cache Docker layers
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build with cache
        uses: docker/build-push-action@v5
        with:
          context: .
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Enterprise Features

### SAML SSO Configuration

```
ENTERPRISE SSO ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌───────────────┐    SAML    ┌───────────────┐
│  Identity     │◀──────────▶│   GitHub      │
│  Provider     │            │  Enterprise   │
│  (Okta/Azure) │            │               │
└───────┬───────┘            └───────────────┘
        │
        │ SCIM (User Provisioning)
        ▼
┌───────────────────────────────────────────────────────────────┐
│                    USER LIFECYCLE                              │
│                                                                │
│  1. User added to IdP group → Auto-created in GitHub          │
│  2. User removed from IdP → Auto-suspended in GitHub          │
│  3. Group membership → Team membership                        │
│  4. Attributes → Organization roles                           │
└───────────────────────────────────────────────────────────────┘

EMU (Enterprise Managed Users):
─────────────────────────────────────────────────────────────────
• Users can ONLY access your enterprise
• No personal GitHub accounts
• Full control over user lifecycle
• Username format: @shortcode_username
```

### Audit Log Streaming

```bash
# Stream audit logs to your SIEM
# Settings → Enterprise → Audit log → Log streaming

# Supported destinations:
# - Amazon S3
# - Azure Blob Storage
# - Azure Event Hubs
# - Google Cloud Storage
# - Splunk
# - Datadog

# Example: Query audit logs via API
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/enterprises/my-enterprise/audit-log?phrase=action:repo.create"

# Sample audit event
{
  "action": "repo.create",
  "actor": "username",
  "actor_id": 12345,
  "created_at": 1234567890,
  "org": "my-org",
  "repo": "my-org/new-repo",
  "visibility": "private"
}
```

### IP Allow Lists

```bash
# Restrict access to specific IPs
# Settings → Organization → Security → IP allow list

# Add entries via API
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/orgs/my-org/ip-allow-list \
  -d '{
    "ip": "203.0.113.0/24",
    "name": "Office Network",
    "isActive": true
  }'

# Note: Affects web UI, API, and Git operations
# Runners may need separate allowlist entries
```

### Repository Rulesets

```yaml
# Modern alternative to branch protection
# Settings → Repository → Rules → Rulesets

# Create ruleset via API
POST /repos/{owner}/{repo}/rulesets
{
  "name": "Production Branch Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main", "refs/heads/release/*"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 2,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "required_status_checks": [
          {"context": "ci/tests"},
          {"context": "security/codeql"}
        ],
        "strict_required_status_checks_policy": true
      }
    },
    {
      "type": "required_signatures"
    }
  ]
}
```

---

## War Story: The Secret Sprawl Discovery

*How secret scanning saved a $180M acquisition—and the $15M lesson in prevention*

### The Situation

A Series C fintech with 150 developers, 400 repositories, and a $180M acquisition offer was two weeks from closing. Due diligence required a security audit. The acquiring company's security team ran a comprehensive secrets scan and found:

- 847 AWS access keys (217 still active)
- 234 database connection strings (89 production systems)
- 156 API keys to third-party services
- 89 SSH private keys (including jump servers)
- 23 customer PII files in test fixtures (GDPR violation territory)

All committed to Git history, some dating back 4 years. Total exposure window: 1,460+ days.

### The Discovery Process

```
SECRETS DISCOVERY TIMELINE
─────────────────────────────────────────────────────────────────

Day 1: Enable GHAS on all repositories
        │
        ├── Immediate: 1,349 alerts generated
        │
        ▼
Day 2-3: Triage alerts
        │
        ├── 40% already rotated (historical)
        ├── 35% test/dummy credentials
        ├── 25% ACTIVE CREDENTIALS 😱
        │
        ▼
Day 4-7: Emergency rotation
        │
        ├── AWS: 200+ keys rotated
        ├── Database: Connection strings changed
        ├── Third-party: All API keys regenerated
        │
        ▼
Day 8: Enable push protection
        │
        └── Zero new secrets committed since
```

### The Fix

```yaml
# .github/workflows/secrets-audit.yml
name: Secrets Audit

on:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Get secret scanning alerts
        uses: actions/github-script@v7
        with:
          script: |
            const alerts = await github.paginate(
              github.rest.secretScanning.listAlertsForOrg,
              {
                org: 'my-org',
                state: 'open'
              }
            );

            // Group by age
            const now = new Date();
            const critical = alerts.filter(a => {
              const age = (now - new Date(a.created_at)) / (1000 * 60 * 60 * 24);
              return age < 7;  // Less than 7 days old
            });

            if (critical.length > 0) {
              core.setFailed(`${critical.length} new secrets found in last 7 days!`);

              // Alert security team
              await github.rest.issues.create({
                owner: 'my-org',
                repo: 'security-alerts',
                title: `🚨 ${critical.length} New Secret Alerts`,
                body: critical.map(a => `- ${a.secret_type} in ${a.repository.name}`).join('\n')
              });
            }
```

### Prevention Measures Implemented

```yaml
# Organization-wide workflow requirement
# All repos must include this workflow

name: Secret Prevention

on:
  pull_request:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for scanning

      - name: TruffleHog (backup scanner)
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified

      - name: Check for high entropy strings
        run: |
          # Custom check for patterns we've seen
          if grep -rE '[A-Za-z0-9+/]{40,}' --include='*.json' --include='*.yaml' .; then
            echo "::error::Potential secret detected"
            exit 1
          fi
```

### Results

| Metric | Before | After |
|--------|--------|-------|
| Active secrets in repos | 337 | 0 |
| Time to detect new secret | Never | < 1 minute |
| Secret commits blocked/month | 0 | ~50 |
| Security audit finding | Critical | Pass |
| Acquisition | At risk | Completed |

**Financial Impact:**

| Category | Cost |
|----------|------|
| Emergency incident response team (2 weeks) | $78,000 |
| AWS credential rotation and audit | $45,000 |
| Third-party security firm verification | $120,000 |
| Legal review and GDPR compliance | $67,000 |
| Developer time diverted from product | $30,000 |
| **Total Remediation** | **$340,000** |
| **Acquisition Price Reduction** | **$15,000,000** |

The acquiring company reduced their offer by $15M, citing "material cybersecurity deficiencies" that indicated systemic issues with the engineering culture. The CTO was asked to resign as a condition of closing.

**Post-Acquisition ROI:** The $49/developer/month for GHAS ($88,200/year for 150 developers) would have prevented a $15.34M loss. ROI: 173x.

### Lessons Learned

1. **History matters** - Git never forgets; you need to rotate, not just delete
2. **Push protection is essential** - Detection without prevention is just alerting
3. **Partner program helps** - Many providers auto-revoke when GitHub notifies them
4. **Cultural change required** - Developers needed training on secret management
5. **Audit regularly** - Weekly reviews of new alerts prevented backlog

---

## Comparison: GHAS vs Third-Party Tools

```
GITHUB ADVANCED SECURITY vs ALTERNATIVES
─────────────────────────────────────────────────────────────────

                    GHAS        Snyk        SonarQube    Semgrep
─────────────────────────────────────────────────────────────────
SECRET SCANNING
Patterns            200+        100+        Limited      100+
Push protection     ✓           ✗           ✗            ✓
Partner revocation  ✓           ✗           ✗            ✗
Custom patterns     ✓           ✓           ✓            ✓

CODE SCANNING
Query language      CodeQL      Proprietary  Java-based  Custom
Languages          10+         10+          25+          20+
Custom rules       ✓           $           ✓            ✓
PR integration     Native      Plugin       Plugin       Native

DEPENDENCY SCANNING
Ecosystem          Native      ✓✓          Plugin       ✗
Auto-fix           Dependabot  ✓           ✗            ✗
License check      ✓           ✓           ✓            ✗

PRICING (per user/month, approx)
─────────────────────────────────────────────────────────────────
Public repos       FREE        FREE        FREE         FREE
Private repos      $49*        $25-99      $0-500/mo    $0-50

* Requires GitHub Enterprise Cloud

BEST FOR:
─────────────────────────────────────────────────────────────────
GHAS:       Already on GitHub, want single pane of glass
Snyk:       Multi-platform, strong dependency focus
SonarQube:  Code quality + security, self-hosted preference
Semgrep:    Custom rule writing, speed
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| GHAS enabled but not enforced | Findings ignored, accumulate | Require status checks for security scans |
| No push protection | Secrets still get committed | Enable push protection org-wide |
| Ignoring Dependabot PRs | Vulnerabilities accumulate | Auto-merge patch updates |
| CodeQL default config only | Misses custom patterns | Add security-extended queries |
| Copilot without exclusions | May suggest proprietary code | Exclude sensitive directories |
| No audit log streaming | Can't investigate incidents | Stream to SIEM |
| Branch protection instead of rulesets | Less flexible | Migrate to rulesets |
| Self-hosted runners without security | Supply chain risk | Use ephemeral, hardened runners |

---

## Hands-On Exercise

### Task: Implement Full Security Pipeline

**Objective**: Configure GHAS features and verify they catch vulnerabilities.

**Success Criteria**:
1. CodeQL scanning enabled and running
2. Secret scanning with push protection active
3. Dependency review blocking vulnerable deps
4. Test that intentional vulnerability is caught

### Steps

```bash
# 1. Create test repository
gh repo create ghas-demo --private --clone
cd ghas-demo

# 2. Initialize project
npm init -y
cat > index.js << 'EOF'
const express = require('express');
const app = express();

// Intentional vulnerability: SQL injection
app.get('/user', (req, res) => {
  const query = `SELECT * FROM users WHERE id = ${req.query.id}`;
  // db.query(query) - would be vulnerable
  res.send(query);
});

// Intentional vulnerability: XSS
app.get('/search', (req, res) => {
  res.send(`<h1>Results for: ${req.query.q}</h1>`);
});

app.listen(3000);
EOF

npm install express

# 3. Add vulnerable dependency
npm install lodash@4.17.20  # Known prototype pollution

# 4. Add CodeQL workflow
mkdir -p .github/workflows
cat > .github/workflows/codeql.yml << 'EOF'
name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
          queries: security-extended
      - uses: github/codeql-action/analyze@v3
EOF

# 5. Add dependency review
cat > .github/workflows/dependency-review.yml << 'EOF'
name: Dependency Review

on: [pull_request]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
EOF

# 6. Commit and push
git add .
git commit -m "Initial commit with intentional vulnerabilities"
git push

# 7. Enable secret scanning in repo settings
# Settings → Code security and analysis → Enable all

# 8. Verify CodeQL finds vulnerabilities
# Check Actions tab → CodeQL workflow
# Check Security tab → Code scanning alerts

# 9. Test push protection (if enabled)
echo "AWS_KEY=AKIAIOSFODNN7EXAMPLE" > .env
git add .env
git commit -m "Add config"
git push  # Should be blocked!
```

### Verification

```bash
# Check security alerts via CLI
gh api repos/:owner/:repo/code-scanning/alerts | jq '.[].rule.description'

# Should see:
# - "SQL injection"
# - "Cross-site scripting"

# Check Dependabot alerts
gh api repos/:owner/:repo/dependabot/alerts | jq '.[].dependency.package.name'

# Should see lodash vulnerability
```

---

## Quiz

### Question 1
What is GitHub Advanced Security (GHAS)?

<details>
<summary>Show Answer</summary>

**A security suite including CodeQL, secret scanning, and dependency review**

GHAS includes:
- CodeQL for static code analysis
- Secret scanning (200+ patterns)
- Push protection to block secrets
- Dependency review for license/vulnerability checking

It's free for public repositories and requires Enterprise Cloud for private repos.
</details>

### Question 2
How does CodeQL differ from traditional SAST tools?

<details>
<summary>Show Answer</summary>

**CodeQL treats code as a database you can query**

Instead of pattern matching, CodeQL builds a database of your code's semantic structure. You write queries to find vulnerabilities like "show me all user inputs that reach SQL queries without sanitization." This enables finding complex vulnerabilities that simple pattern matching misses.
</details>

### Question 3
What is push protection in secret scanning?

<details>
<summary>Show Answer</summary>

**Blocking commits that contain secrets before they enter the repository**

When enabled, GitHub scans commits during `git push` and blocks pushes containing detected secrets. The developer must either remove the secret or request a bypass (which creates an audit trail). This prevents secrets from ever entering Git history.
</details>

### Question 4
What's the difference between Copilot Individual, Business, and Enterprise?

<details>
<summary>Show Answer</summary>

- **Individual ($10/mo)**: Code completion and chat in IDE
- **Business ($19/mo)**: + Policy management, file exclusions, audit logs, no training on your code
- **Enterprise ($39/mo)**: + Chat on github.com, PR summaries, knowledge bases, fine-tuning

Enterprise adds organization-specific AI features like learning from your documentation.
</details>

### Question 5
How do reusable workflows differ from composite actions?

<details>
<summary>Show Answer</summary>

**Reusable workflows are complete jobs; composite actions are step collections**

- **Reusable workflows**: Called with `uses: org/repo/.github/workflows/x.yml`, run as separate jobs, can have their own `runs-on`
- **Composite actions**: Used as a step within a job, combine multiple steps into one, run in the calling job's context

Use reusable workflows for complete CI/CD processes; use composite actions for common step sequences.
</details>

### Question 6
What is EMU (Enterprise Managed Users)?

<details>
<summary>Show Answer</summary>

**GitHub accounts fully controlled by your identity provider**

EMU users:
- Can only access your enterprise (no personal GitHub)
- Are provisioned/deprovisioned via SCIM
- Have usernames like `@shortcode_username`
- Cannot fork to personal accounts
- Are fully controlled by administrators

Used when companies need complete control over user access.
</details>

### Question 7
What's the Actions Runner Controller (ARC)?

<details>
<summary>Show Answer</summary>

**A Kubernetes operator for auto-scaling self-hosted runners**

ARC lets you:
- Deploy runners as Kubernetes pods
- Auto-scale based on workflow queue
- Use ephemeral runners (fresh for each job)
- Apply resource limits and node selectors

It's the recommended way to run self-hosted runners at scale.
</details>

### Question 8
How does GitHub's partner program help with secret scanning?

<details>
<summary>Show Answer</summary>

**Partners automatically revoke exposed credentials**

When GitHub detects a secret (like an AWS key or Stripe API key), it notifies the service provider. Many partners automatically revoke the credential before it can be exploited. This "secret scanning partner program" includes AWS, Azure, GCP, Stripe, Twilio, and 100+ others.
</details>

---

## Key Takeaways

1. **GHAS is free for public repos** - Enable it immediately on open source projects
2. **Push protection prevents secrets** - Detection after commit is too late
3. **CodeQL is powerful but needs tuning** - Add security-extended queries
4. **Copilot needs governance** - Exclude sensitive files, audit usage
5. **Reusable workflows reduce duplication** - Centralize CI/CD logic
6. **Self-hosted runners need ARC** - Auto-scaling is essential at scale
7. **Dependabot needs action** - Auto-merge or assign owners
8. **Rulesets beat branch protection** - More flexible, org-wide
9. **Audit logs are required** - Stream to SIEM for compliance
10. **EMU for maximum control** - When personal accounts aren't acceptable

---

## Next Steps

- **Related**: [Module 12.3: CodeQL](../code-quality/module-12.3-codeql.md) - Deep dive into query writing
- **Related**: [Module 4.4: Supply Chain Security](../security-tools/module-4.4-supply-chain.md) - SBOM and signing
- **Related**: [Module 2.1: ArgoCD](../gitops-deployments/module-2.1-argocd.md) - GitOps deployments from GitHub

---

## Further Reading

- [GitHub Advanced Security Documentation](https://docs.github.com/en/code-security)
- [CodeQL Documentation](https://codeql.github.com/docs/)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Actions Runner Controller](https://github.com/actions/actions-runner-controller)
- [GitHub Enterprise Documentation](https://docs.github.com/en/enterprise-cloud@latest)

---

*"GitHub isn't competing with GitLab on features anymore—it's redefining what a development platform can be. The question isn't whether to use these features, but how quickly you can adopt them."*
