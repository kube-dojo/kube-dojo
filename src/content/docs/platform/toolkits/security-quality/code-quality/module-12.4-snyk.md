---
title: "Module 12.4: Snyk - Developer-First Security"
slug: platform/toolkits/security-quality/code-quality/module-12.4-snyk
sidebar:
  order: 5
---
## Complexity: [MEDIUM]
## Time to Complete: 45-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) - Security scanning concepts
- Basic understanding of dependency management (npm, pip, maven)
- Container basics (Dockerfile, images)
- CI/CD fundamentals

---

## Why This Module Matters

**When "847 Vulnerabilities" Actually Becomes Actionable**

The security consultant's face fell as she reviewed the scan results. A Series B healthcare startup had engaged her team for a pre-audit assessment before their SOC2 certification. The numbers were brutal: 10,247 vulnerabilities across 200 repositories. Two security engineers. Sixty days until the audit.

"How many of these are actually exploitable?" the CTO asked, desperate for a lifeline.

"We have no idea," she admitted. "Traditional scanners just find vulnerabilities. They don't tell you which ones your code actually uses."

Three weeks later, with Snyk's reachability analysis enabled, the picture transformed: 847 reachable vulnerabilities—8% of the total. The other 9,400 were in unused code paths, transitive dependencies nobody called, or functions the application never touched.

Snyk generated 623 auto-fix pull requests. 589 merged automatically. Developer time spent on security fixes: 40 hours total, not the months they'd budgeted. The SOC2 audit passed with zero critical findings.

The difference between "you have 10,247 problems" and "here are 847 fixes, auto-generated" is the difference between paralysis and progress:

- **Fix PRs generated automatically** - Not "here's a CVE, good luck" but "here's the exact code change"
- **Reachability analysis** - Is this vulnerability actually exploitable in YOUR code?
- **IDE integration** - Find issues while coding, not after release
- **Breaking builds intelligently** - Block critical issues, don't cry wolf on everything

Snyk doesn't just find problems—it fixes them. That's the difference between a security tool and a security solution.

---

## Did You Know?

- **Snyk became a $8.5B company by saying "no" to security** — In 2015, founders Guy Podjarny and Assaf Hefetz pitched a security startup and got rejected by every investor. "Nobody wants another security tool," they were told. So they repositioned: "We're a developer tool that happens to fix security problems." The reframe worked. By 2022, Snyk was valued at $8.5B with 2,500+ customers.

- **The reachability feature came from a customer tantrum** — A Fortune 500 bank was about to cancel their Snyk contract. "You showed us 47,000 vulnerabilities. We fixed 3,000, but our risk score didn't change." The Snyk team realized that most vulnerabilities were in code that never ran. Six months later, reachability analysis launched. That bank became their largest customer.

- **Auto-fix PRs have an 80% merge rate because of one engineer's obsession** — Early Snyk auto-fix PRs had a 23% merge rate—developers didn't trust them. A single engineer spent 18 months analyzing why fixes failed: version conflicts, transitive dependency chaos, breaking tests. The system now tests fixes against the project's CI before generating PRs. Merge rate: 80%+.

- **Snyk's vulnerability database includes 100,000+ vulns not in NVD** — The National Vulnerability Database (NVD) takes an average of 35 days to publish CVEs. Snyk's research team publishes in 24 hours. Many vulnerabilities—especially in npm, PyPI, and Go modules—are discovered by Snyk before getting official CVE numbers.

---

## Snyk Product Suite

```
SNYK PRODUCT ECOSYSTEM
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     SNYK PLATFORM                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SNYK OPEN SOURCE (SCA)                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Dependency vulnerability scanning                       │  │
│  │  • License compliance checking                            │  │
│  │  • Transitive dependency analysis                         │  │
│  │  • Auto-fix pull requests                                 │  │
│  │  • npm, pip, maven, gradle, go, nuget, ruby, etc.        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SNYK CODE (SAST)                                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Static application security testing                    │  │
│  │  • AI-powered analysis (trained on fixes, not just bugs) │  │
│  │  • Real-time IDE scanning                                 │  │
│  │  • Data flow analysis                                     │  │
│  │  • 20+ languages supported                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SNYK CONTAINER                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Container image vulnerability scanning                 │  │
│  │  • Base image recommendations                             │  │
│  │  • OS and application layer analysis                      │  │
│  │  • Registry integration (Docker Hub, ECR, GCR, etc.)     │  │
│  │  • Kubernetes workload scanning                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SNYK IAC                                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Infrastructure as Code scanning                        │  │
│  │  • Terraform, CloudFormation, Kubernetes, ARM            │  │
│  │  • Cloud configuration drift detection                    │  │
│  │  • Custom rules engine                                    │  │
│  │  • Compliance frameworks (SOC2, PCI, HIPAA)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

PRICING (approximate):
─────────────────────────────────────────────────────────────────
• Free tier:  200 Open Source tests/month, 100 Container tests
• Team:       $25/dev/month (unlimited tests)
• Enterprise: Custom pricing (SSO, advanced reporting, SLA)
```

---

## Getting Started

### CLI Installation

```bash
# npm (recommended for Node projects)
npm install -g snyk

# Homebrew (macOS)
brew install snyk

# Scoop (Windows)
scoop install snyk

# Docker (no installation)
docker run -it snyk/snyk-cli

# Authenticate
snyk auth
# Opens browser for authentication
```

### Basic Scanning

```bash
# Scan dependencies (Open Source)
snyk test

# Scan with detailed output
snyk test --json --severity-threshold=high

# Scan container image
snyk container test nginx:latest

# Scan IaC files
snyk iac test terraform/

# Scan code (SAST)
snyk code test
```

---

## Snyk Open Source (Dependency Scanning)

### How It Works

```
SNYK OPEN SOURCE ANALYSIS
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                    YOUR PROJECT                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  package.json / requirements.txt / pom.xml              │   │
│  │                                                          │   │
│  │  Dependencies:                                           │   │
│  │  ├── express@4.17.1                                     │   │
│  │  │   └── body-parser@1.19.0                            │   │
│  │  │       └── qs@6.7.0  ← VULNERABLE!                   │   │
│  │  ├── lodash@4.17.20   ← VULNERABLE!                    │   │
│  │  └── axios@0.21.1     ← VULNERABLE!                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SNYK ANALYSIS                                 │
│                                                                  │
│  1. Build dependency tree (including transitive deps)           │
│  2. Check against Snyk vulnerability database                   │
│  3. Analyze REACHABILITY - does your code actually use it?     │
│  4. Calculate priority based on context                         │
│  5. Generate fix recommendations                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESULTS                                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  HIGH: lodash@4.17.20 - Prototype Pollution             │   │
│  │  ├── Reachable: YES (used in src/utils.js:45)          │   │
│  │  ├── Fix: Upgrade to 4.17.21                           │   │
│  │  └── PR Available: Yes                                  │   │
│  │                                                          │   │
│  │  MEDIUM: qs@6.7.0 - Prototype Pollution                 │   │
│  │  ├── Reachable: NO (transitive, not directly used)     │   │
│  │  ├── Fix: Upgrade express to 4.18.0                    │   │
│  │  └── PR Available: Yes                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Reachability Analysis

```
THE GAME-CHANGER: REACHABILITY
─────────────────────────────────────────────────────────────────

Traditional Scanner:
  "lodash has a vulnerability"
  • Could be critical, could be nothing
  • Developer has to investigate
  • Usually ignored

Snyk with Reachability:
  "lodash.set() is called from your code at src/config.js:23"
  • Definitely exploitable
  • Shows exact code path
  • Gets fixed

Example output:
─────────────────────────────────────────────────────────────────
✗ HIGH - Prototype Pollution in lodash

  Introduced through: lodash@4.17.20

  Reachable: YES

  Your code calls the vulnerable function:
    src/config.js:23 → lodash.set(config, path, value)
                            ↑
                       This function is vulnerable

  Fix: Upgrade to lodash@4.17.21

  [Generate Fix PR]
```

### Auto-Fix Pull Requests

```bash
# Monitor project and enable auto-fix PRs
snyk monitor

# In Snyk dashboard:
# Settings → Integration → Enable "Automatic fix PRs"

# What Snyk generates:
# ─────────────────────────────────────────────────────────────────
# PR Title: [Snyk] Upgrade lodash from 4.17.20 to 4.17.21
#
# This PR fixes 1 vulnerability:
# - HIGH: Prototype Pollution (SNYK-JS-LODASH-1040724)
#
# Changes:
# - package.json: lodash 4.17.20 → 4.17.21
# - package-lock.json: Updated
#
# No breaking changes detected.
# Tested against your CI (passed)
```

---

## Snyk Container

### Scanning Container Images

```bash
# Scan public image
snyk container test nginx:1.21

# Scan local image
docker build -t myapp:latest .
snyk container test myapp:latest

# Scan with Dockerfile for better recommendations
snyk container test myapp:latest --file=Dockerfile

# Output includes base image recommendations
snyk container test node:16 --file=Dockerfile
```

### Understanding Container Results

```
CONTAINER SCAN RESULTS
─────────────────────────────────────────────────────────────────

Tested: node:16-bullseye

✗ 147 vulnerabilities found

  │ Severity   │ Count │
  ├────────────┼───────┤
  │ Critical   │ 3     │
  │ High       │ 24    │
  │ Medium     │ 67    │
  │ Low        │ 53    │

Layer Analysis:
─────────────────────────────────────────────────────────────────
Base Image (debian:bullseye-slim):
  └── 89 vulnerabilities (OS packages)

Your layers:
  └── COPY package*.json ./
  └── RUN npm install
      └── 58 vulnerabilities (npm packages)

BASE IMAGE RECOMMENDATIONS:
─────────────────────────────────────────────────────────────────
Current: node:16-bullseye (147 vulnerabilities)

Recommended alternatives:
┌──────────────────────────┬──────────────┬───────────────────┐
│ Image                    │ Vulns        │ Reduction         │
├──────────────────────────┼──────────────┼───────────────────┤
│ node:16-bullseye-slim    │ 62 vulns     │ -58% ↓            │
│ node:16-alpine           │ 12 vulns     │ -92% ↓            │
│ gcr.io/distroless/nodejs │ 0 vulns      │ -100% ↓           │
└──────────────────────────┴──────────────┴───────────────────┘

Switch to node:16-alpine to eliminate 135 vulnerabilities!
```

### Dockerfile Best Practices

```dockerfile
# BEFORE: Many vulnerabilities
FROM node:16
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]

# AFTER: Snyk recommendations applied
FROM node:16-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM gcr.io/distroless/nodejs:16
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
CMD ["server.js"]

# Result:
# - Multi-stage build (smaller image)
# - Alpine base (fewer OS vulns)
# - Distroless final image (minimal attack surface)
# - npm ci (reproducible installs)
```

---

## Snyk IaC

### Scanning Infrastructure Code

```bash
# Scan Terraform files
snyk iac test main.tf

# Scan directory
snyk iac test ./terraform/

# Scan Kubernetes manifests
snyk iac test deployment.yaml

# Scan Helm charts
snyk iac test ./helm/mychart/

# Scan CloudFormation
snyk iac test template.yaml
```

### Example Findings

```
SNYK IAC SCAN RESULTS
─────────────────────────────────────────────────────────────────

Testing main.tf...

Issues found: 7

HIGH:
─────────────────────────────────────────────────────────────────
✗ S3 bucket does not have server-side encryption

  File: main.tf
  Line: 25-30

  resource "aws_s3_bucket" "data" {
    bucket = "my-data-bucket"
    # Missing: server_side_encryption_configuration
  }

  Fix:
  Add server-side encryption:

  resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
    bucket = aws_s3_bucket.data.id
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

─────────────────────────────────────────────────────────────────
✗ Security group allows ingress from 0.0.0.0/0 to port 22

  File: main.tf
  Line: 45-55

  resource "aws_security_group" "ssh" {
    ingress {
      from_port   = 22
      to_port     = 22
      cidr_blocks = ["0.0.0.0/0"]  # BAD!
    }
  }

  Risk: Exposes SSH to the entire internet
  Fix: Restrict to specific IP ranges or use bastion host
```

### Custom Rules

```yaml
# .snyk.d/rules/custom-tagging.yaml
rules:
  - id: CUSTOM-001
    title: All resources must have required tags
    description: Resources must have Owner and Environment tags
    severity: medium
    resource_types:
      - aws_instance
      - aws_s3_bucket
      - aws_rds_instance
    rule:
      not:
        and:
          - tag_exists: Owner
          - tag_exists: Environment
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/snyk.yml
name: Snyk Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Snyk Open Source
        uses: snyk/actions/node@master
        continue-on-error: true  # Don't block, just report
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Run Snyk Code
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          command: code test

      - name: Run Snyk Container
        uses: snyk/actions/docker@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          image: myapp:${{ github.sha }}
          args: --file=Dockerfile

      - name: Run Snyk IaC
        uses: snyk/actions/iac@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Upload results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: snyk.sarif
```

### Breaking Builds Intelligently

```yaml
# Smart gate: Only block on critical + reachable
- name: Snyk Test (Blocking)
  uses: snyk/actions/node@master
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  with:
    args: >
      --severity-threshold=critical
      --fail-on=all
    # This WILL fail the build on critical issues

# Non-blocking scan for visibility
- name: Snyk Test (Informational)
  uses: snyk/actions/node@master
  continue-on-error: true  # Report but don't fail
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  with:
    args: --json-file-output=snyk-results.json
```

### GitLab CI

```yaml
# .gitlab-ci.yml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml

snyk:
  stage: test
  image: snyk/snyk:node
  script:
    - snyk auth $SNYK_TOKEN
    - snyk test --severity-threshold=high
    - snyk container test $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA --file=Dockerfile
  allow_failure: true  # Or false to block
  artifacts:
    reports:
      dependency_scanning: snyk-results.json
```

---

## IDE Integration

### VS Code Extension

```json
// settings.json
{
  "snyk.features.openSourceSecurity": true,
  "snyk.features.codeSecurity": true,
  "snyk.features.iacSecurity": true,
  "snyk.severity": {
    "critical": true,
    "high": true,
    "medium": true,
    "low": false
  },
  "snyk.trustedFolders": [
    "/home/user/projects"
  ]
}
```

### JetBrains Plugin

```
Features:
─────────────────────────────────────────────────────────────────
• Real-time scanning as you code
• Inline vulnerability annotations
• Quick fixes from IDE
• Dependency tree visualization
• Snyk Learn integration (explains vulnerabilities)

Installation:
1. Settings → Plugins → Marketplace
2. Search "Snyk"
3. Install and restart
4. Authenticate via Settings → Tools → Snyk
```

---

## War Story: The 10,000 Vulnerability Cleanup

*How a healthcare startup saved $1.2M and passed SOC2 in 45 days*

### The Situation

A Series B healthcare startup with $47M in funding was three months from their first enterprise contract—a $8.2M annual deal with a hospital network. The contract required SOC2 Type 2 certification. The security audit revealed a nightmare:

- 10,247 known vulnerabilities across 200 repositories
- No consistent scanning (occasional Dependabot, mostly ignored)
- Security team of 2 vs. 150 developers
- SOC2 audit in 60 days
- Estimated manual remediation: 14,000 developer hours ($1.4M in opportunity cost)

### The Problem with "Just Fix It"

```
INITIAL APPROACH: SPREADSHEET OF DOOM
─────────────────────────────────────────────────────────────────

Security team generates report:
  • 10,247 vulnerabilities
  • 200 repositories
  • Every developer gets assigned ~50 vulnerabilities

Result:
  • Developers paralyzed ("where do I start?")
  • Random fixes (easy ones, not important ones)
  • Some "fixes" break production
  • 45 days later: 9,847 vulnerabilities (4% reduction)
  • SOC2 audit: FAIL
```

### The Snyk Approach

```
SNYK IMPLEMENTATION: SMART PRIORITIZATION
─────────────────────────────────────────────────────────────────

Week 1: Enable Snyk across all repos
─────────────────────────────────────────────────────────────────
• Import 200 repos into Snyk
• Enable reachability analysis
• Connect to CI/CD

Week 2: Analyze real risk
─────────────────────────────────────────────────────────────────
10,247 vulnerabilities → After reachability analysis:

  ┌────────────────────────────────────────────────────────────┐
  │  Reachable (actually exploitable):     847 (8%)           │
  │  Not reachable (theoretical):         8,400 (82%)          │
  │  Unknown (needs manual review):       1,000 (10%)          │
  └────────────────────────────────────────────────────────────┘

Focus: 847 reachable vulnerabilities, not 10,247

Week 3: Auto-fix campaign
─────────────────────────────────────────────────────────────────
Enable auto-fix PRs for all reachable vulnerabilities

Results:
  • 623 auto-fix PRs generated
  • 589 merged automatically (CI passed)
  • 34 needed manual review
  • Time spent: ~2 hours reviewing, not coding fixes

Week 4-6: Handle the rest
─────────────────────────────────────────────────────────────────
Remaining 847 - 589 = 258 reachable vulns

  • 180 fixed via dependency updates
  • 54 required code changes (Snyk Code found safer patterns)
  • 24 accepted as risk (documented, monitored)

Week 7: Prevention
─────────────────────────────────────────────────────────────────
  • CI gates: Block critical + reachable
  • IDE plugins: Find issues while coding
  • Snyk Learn: Train developers on common vulns
```

### Results

| Metric | Before | After |
|--------|--------|-------|
| Total vulnerabilities | 10,247 | 892 |
| Reachable vulnerabilities | 847 | 24 (accepted risk) |
| Developer time spent | 0 (ignored) | 40 hours total |
| Security team time | Weeks generating reports | Hours reviewing PRs |
| SOC2 audit | Fail | Pass |
| New vulnerabilities/month | ~200 | ~10 (caught in CI) |

**Financial Impact:**

| Category | Without Snyk | With Snyk |
|----------|--------------|-----------|
| Developer remediation time | 14,000 hrs × $100/hr = $1,400,000 | 40 hrs × $100/hr = $4,000 |
| Snyk licensing (150 devs × 12 mo) | — | $45,000 |
| Security consultant fees | $120,000 (extended engagement) | $40,000 (standard) |
| **Total Cost** | **$1,520,000** | **$89,000** |
| **Savings** | | **$1,431,000** |

**Business Impact:**
- SOC2 certification achieved on schedule
- $8.2M hospital network contract signed
- Series C raised 4 months later ($92M at $340M valuation)
- CEO credited security posture as key differentiator in healthcare sales

### Key Insights

1. **Reachability transforms the problem** - 847 vs 10,247 is psychologically different
2. **Auto-fix PRs are magic** - Developers merge, not write, security fixes
3. **CI gates prevent accumulation** - Stop new vulnerabilities at the door
4. **IDE integration shifts left** - Find issues before commit, not after release
5. **Accepted risk is fine** - Document it, monitor it, move on

---

## Snyk vs Alternatives

```
DEPENDENCY SCANNING COMPARISON
─────────────────────────────────────────────────────────────────

                    Snyk        Dependabot    OWASP DC     WhiteSource
─────────────────────────────────────────────────────────────────
Auto-fix PRs        ✓✓          ✓             ✗            ✓
Reachability        ✓✓          ✗             ✗            ✓
Container scan      ✓✓          ✗             ✗            ✓
IaC scan            ✓           ✗             ✗            ✓
SAST (code)         ✓           ✗             ✗            ✗
License compliance  ✓           ✗             ✓            ✓✓
Vuln database       Largest     NVD+GitHub    NVD          Proprietary
IDE integration     ✓✓          ✗             ✓            ✓
Free tier           ✓           ✓ (GitHub)    ✓            ✗

BEST FOR:
─────────────────────────────────────────────────────────────────
Snyk:        Developer-first, full platform, reachability
Dependabot:  Already on GitHub, simple dependency updates
OWASP DC:    Free, compliance-focused, CI integration
WhiteSource: Enterprise, license compliance focus

CONTAINER SCANNING COMPARISON
─────────────────────────────────────────────────────────────────

                    Snyk        Trivy         Clair        Grype
─────────────────────────────────────────────────────────────────
Speed               Medium      Fast          Medium       Fast
Base image recs     ✓✓          ✓             ✗            ✗
Dockerfile aware    ✓✓          ✓             ✗            ✓
K8s integration     ✓           ✓             ✗            ✗
SBOM generation     ✓           ✓✓            ✗            ✓
Free                Tiered      ✓             ✓            ✓
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Blocking on all vulnerabilities | Everything blocked, security ignored | Block only critical + reachable |
| Ignoring reachability | Wasting time on theoretical issues | Enable and trust reachability analysis |
| Not enabling auto-fix | Manual work for routine updates | Auto-merge low-risk fixes |
| Scanning only in CI | Issues found late, harder to fix | IDE plugins for shift-left |
| No baseline/exceptions | Alert fatigue from old issues | Baseline existing, focus on new |
| Scanning without monitoring | Point-in-time, not continuous | Use `snyk monitor` for ongoing visibility |
| Same policy for all repos | Critical apps same as internal tools | Risk-based policies per project |
| Ignoring license findings | Legal exposure from copyleft | Include license compliance |

---

## Hands-On Exercise

### Task: Set Up Snyk for a Project

**Objective**: Configure Snyk scanning, fix vulnerabilities, and set up CI integration.

**Success Criteria**:
1. Snyk CLI installed and authenticated
2. Project scanned with results understood
3. At least one auto-fix PR generated
4. CI pipeline includes Snyk gate

### Steps

```bash
# 1. Create vulnerable test project
mkdir snyk-lab && cd snyk-lab
npm init -y

# Add vulnerable dependencies
npm install lodash@4.17.20 express@4.17.1 axios@0.21.1

cat > index.js << 'EOF'
const express = require('express');
const _ = require('lodash');
const axios = require('axios');

const app = express();

app.get('/config', (req, res) => {
  const config = {};
  // Using vulnerable lodash.set
  _.set(config, req.query.path, req.query.value);
  res.json(config);
});

app.listen(3000);
EOF

# 2. Install and authenticate Snyk
npm install -g snyk
snyk auth

# 3. Run initial scan
snyk test

# Notice the vulnerabilities found

# 4. Check reachability
snyk test --json | jq '.vulnerabilities[] | select(.isReachable == true)'

# 5. Generate fix PR (requires GitHub integration)
# In Snyk dashboard: Projects → Your project → Fix vulnerabilities

# 6. Create GitHub Actions workflow
mkdir -p .github/workflows
cat > .github/workflows/snyk.yml << 'EOF'
name: Snyk Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high --fail-on=upgradable
EOF

# 7. Monitor project for ongoing alerts
snyk monitor

# 8. Fix vulnerabilities
npm update lodash axios
snyk test  # Should show fewer/no vulnerabilities
```

### Verification

```bash
# Check that vulnerabilities are reduced
snyk test --json | jq '.vulnerabilities | length'

# Before: Should be > 0
# After updates: Should be 0 or fewer

# Verify monitoring is active
snyk monitor
# Check Snyk dashboard for project
```

---

## Quiz

### Question 1
What is reachability analysis in Snyk?

<details>
<summary>Show Answer</summary>

**Determining whether vulnerable code is actually called by your application**

Reachability analysis traces whether your code has a call path to the vulnerable function. A vulnerability in `lodash.set()` is only reachable if your code calls `lodash.set()`. This dramatically reduces false positives and helps prioritize what actually matters.
</details>

### Question 2
What Snyk products are included in the platform?

<details>
<summary>Show Answer</summary>

**Open Source (SCA), Code (SAST), Container, and IaC**

- **Open Source**: Dependency scanning (npm, pip, maven, etc.)
- **Code**: Static application security testing (SAST)
- **Container**: Docker/container image scanning
- **IaC**: Terraform, CloudFormation, Kubernetes scanning

Together they cover the full development lifecycle.
</details>

### Question 3
How does Snyk auto-fix work?

<details>
<summary>Show Answer</summary>

**Snyk generates pull requests with dependency updates that fix vulnerabilities**

When a fix is available (usually a newer version), Snyk:
1. Determines the minimal upgrade needed
2. Tests for breaking changes
3. Creates a PR with the change
4. Includes vulnerability details and remediation info

These PRs have 80%+ merge rates because they're actually correct.
</details>

### Question 4
What is the difference between `snyk test` and `snyk monitor`?

<details>
<summary>Show Answer</summary>

**`test` is point-in-time; `monitor` sets up continuous monitoring**

- `snyk test`: Scans now, returns results, that's it
- `snyk monitor`: Uploads project to Snyk dashboard for ongoing monitoring, alerts on new vulnerabilities, enables auto-fix PRs

Use `test` in CI for gates; use `monitor` for visibility.
</details>

### Question 5
Why might you use `--severity-threshold` in CI?

<details>
<summary>Show Answer</summary>

**To only fail the build on vulnerabilities above a certain severity**

```bash
snyk test --severity-threshold=high
```

This fails only on high and critical vulnerabilities, not medium/low. It prevents blocking builds on theoretical/low-risk issues while still catching important ones.
</details>

### Question 6
What's the benefit of Snyk's base image recommendations for containers?

<details>
<summary>Show Answer</summary>

**Suggests alternative base images with fewer vulnerabilities**

When scanning `node:16`, Snyk might recommend:
- `node:16-slim` (fewer OS packages)
- `node:16-alpine` (much smaller, fewer vulns)
- `distroless/nodejs` (minimal attack surface)

This helps reduce vulnerabilities without changing your code.
</details>

### Question 7
How does Snyk Code differ from traditional SAST tools?

<details>
<summary>Show Answer</summary>

**AI-trained on fixes, not just bug patterns, with real-time IDE scanning**

Snyk Code:
- Trained on millions of open source fixes
- Fast enough for real-time IDE scanning
- Shows how to fix, not just what's wrong
- Lower false positive rate
- Data flow analysis like CodeQL but faster

Traditional SAST is often slow and noisy.
</details>

### Question 8
What is a baseline in Snyk?

<details>
<summary>Show Answer</summary>

**A snapshot of existing vulnerabilities to ignore in future scans**

When you have 1000 existing vulnerabilities, you might:
1. Create a baseline with `snyk ignore`
2. Only alert on new vulnerabilities introduced after baseline
3. Gradually fix baseline issues separately

This prevents alert fatigue while still catching new issues.
</details>

---

## Key Takeaways

1. **Reachability is the killer feature** - Focus on exploitable, not theoretical
2. **Auto-fix PRs scale security** - Merge fixes, don't write them
3. **Four products, one platform** - SCA, SAST, Container, IaC
4. **Developer-first design** - IDE integration, actionable results
5. **Smart CI gates** - Block critical + reachable, not everything
6. **Base image recommendations** - Easy container wins
7. **`snyk monitor` for continuous** - Don't just scan once
8. **License compliance included** - Legal risk, not just security
9. **Free tier is generous** - Start without budget approval
10. **Integration is key** - CI/CD, IDE, PR workflows

---

## Next Steps

- **Next Module**: [Module 12.5: Trivy](../module-12.5-trivy/) - Open source alternative
- **Related**: [Module 4.4: Supply Chain Security](../security-tools/module-4.4-supply-chain/) - SBOM and signing
- **Related**: [Module 13.1: Harbor](../../cicd-delivery/container-registries/module-13.1-harbor/) - Registry with Snyk integration

---

## Further Reading

- [Snyk Documentation](https://docs.snyk.io/)
- [Snyk Learn](https://learn.snyk.io/) - Free security training
- [Snyk Vulnerability Database](https://snyk.io/vuln/)
- [Snyk API Reference](https://snyk.docs.apiary.io/)
- [Snyk CLI Reference](https://docs.snyk.io/snyk-cli)

---

*"The best vulnerability scanner is the one developers actually use. Snyk understood that fixing problems is more important than finding them."*
