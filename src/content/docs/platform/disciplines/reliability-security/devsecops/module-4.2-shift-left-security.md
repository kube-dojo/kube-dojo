---
title: "Module 4.2: Shift-Left Security"
slug: platform/disciplines/reliability-security/devsecops/module-4.2-shift-left-security
sidebar:
  order: 3
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 35-40 min

## Prerequisites

Before starting this module:
- **Required**: [Module 4.1: DevSecOps Fundamentals](../module-4.1-devsecops-fundamentals/) — Core concepts
- **Required**: Git basics (commits, branches, hooks)
- **Recommended**: IDE experience (VS Code, IntelliJ, etc.)
- **Helpful**: Basic understanding of static analysis

---

## Why This Module Matters

You've adopted DevSecOps. You have security scans in your pipeline. Great!

But the pipeline runs after you push. You write code Monday, push Tuesday, get scan results Wednesday, fix Thursday. That's 3-4 days of context switching.

**What if you caught issues before you committed?**

Shift-left security isn't just about having security in CI/CD. It's about pushing security so far left that developers catch issues in their IDE, before they even commit.

After this module, you'll understand:
- Pre-commit security checks and how to implement them
- IDE security plugins and developer-friendly tooling
- Secrets detection before they reach Git
- SAST integration at the earliest possible point

---

## The Pre-Commit Defense Line

### Why Pre-Commit Matters

```
The Commit Timeline
─────────────────────────────────────────────────────────────────▶

  Developer         Pre-commit        CI/CD           Production
  writes code       hooks run         scans run       deployed
       │                │                 │                │
       ▼                ▼                 ▼                ▼
   ┌───────┐        ┌───────┐        ┌───────┐        ┌───────┐
   │ CODE  │───────▶│ CHECK │───────▶│ SCAN  │───────▶│ LIVE  │
   └───────┘        └───────┘        └───────┘        └───────┘
                         │
                    Issue found
                    here = instant
                    feedback, easy fix
```

**Pre-commit advantages:**
- Developer still has context (just wrote the code)
- No wait for CI/CD pipeline
- No PR/review cycle for obvious issues
- Catches secrets before they enter Git history
- Teaches developers as they work

### Git Hooks Primer

Git hooks are scripts that run at specific points in the Git workflow:

```
┌─────────────────────────────────────────────────────────────┐
│                     GIT HOOK LIFECYCLE                       │
│                                                              │
│  Local Hooks                    Remote Hooks                 │
│  ───────────                    ─────────────                │
│                                                              │
│  pre-commit ────▶ commit-msg ────▶ pre-push ────▶ pre-receive│
│       │               │               │               │      │
│   Validate        Validate         Check           Server    │
│   code            message          before          validates │
│                                    push            received  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Most important for security:**
- `pre-commit`: Runs before commit is created (local)
- `pre-push`: Runs before push to remote (local)
- `pre-receive`: Runs on server (enforced)

---

## Implementing Pre-Commit Hooks

### Option 1: Pre-commit Framework

The [pre-commit](https://pre-commit.com/) framework manages hooks across languages.

**Installation:**
```bash
# Install pre-commit
pip install pre-commit

# Or with homebrew
brew install pre-commit
```

**Configuration (`.pre-commit-config.yaml`):**
```yaml
repos:
  # Detect secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Security linting for Python
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]

  # Security linting for Shell scripts
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.9.0
    hooks:
      - id: shellcheck

  # Dockerfile linting
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker
```

**Enable for repository:**
```bash
# Install hooks
pre-commit install

# Run against all files (first time)
pre-commit run --all-files
```

### Option 2: Husky (JavaScript/TypeScript)

For Node.js projects, [Husky](https://typicode.github.io/husky/) is popular:

```bash
# Install
npm install husky --save-dev

# Enable Git hooks
npx husky install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run security-check"
```

**package.json:**
```json
{
  "scripts": {
    "security-check": "npm audit && eslint --plugin security ."
  }
}
```

### Option 3: Native Git Hooks

For simple cases, native Git hooks work:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running security checks..."

# Check for secrets
if grep -rn "password\s*=" --include="*.py" .; then
    echo "ERROR: Possible hardcoded password found"
    exit 1
fi

# Check for AWS keys
if grep -rn "AKIA" --include="*" .; then
    echo "ERROR: Possible AWS key found"
    exit 1
fi

echo "Security checks passed"
exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Did You Know?

1. **GitHub found that 81% of data breaches involve leaked credentials** — and most of those credentials were committed to Git repositories. Pre-commit secrets detection could have prevented the majority of these breaches.

2. **The first public Git hook was added in 2005** with Git 0.99.5. The `pre-commit` hook has been available since the very beginning of Git, but most developers still don't use it for security.

3. **Uber's 2016 breach** started with credentials found in a GitHub repository. 57 million user records were exposed because an AWS key was committed to code. The fine: $148 million.

4. **TruffleHog, a popular secrets scanner, got its name** from the French truffle-hunting pigs. Just like pigs sniff out valuable truffles underground, TruffleHog sniffs out valuable secrets hidden in code repositories.

---

## Secrets Detection

### The Secrets Problem

Secrets in Git are forever (almost):

```
┌─────────────────────────────────────────────────────────────┐
│                  THE SECRET IN GIT PROBLEM                   │
│                                                              │
│  Commit 1: Add database connection                          │
│            DB_PASSWORD = "super_secret_123"   ← Secret!     │
│                                                              │
│  Commit 2: Oops, remove password                            │
│            DB_PASSWORD = os.getenv("DB_PASS")               │
│                                                              │
│  Current code looks safe... but:                            │
│                                                              │
│  $ git log -p                                                │
│  commit abc123                                               │
│  -DB_PASSWORD = "super_secret_123"   ← Still there!         │
│  +DB_PASSWORD = os.getenv("DB_PASS")                         │
│                                                              │
│  The secret lives in Git history FOREVER                    │
│  (unless you rewrite history, which is painful)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**The only safe secret is one that never enters Git.**

### Popular Secrets Detection Tools

| Tool | Strengths | Best For |
|------|-----------|----------|
| **detect-secrets** (Yelp) | Fast, baseline support, low false positives | Pre-commit |
| **TruffleHog** | Deep history scanning, regex patterns | CI/CD, audits |
| **gitleaks** | Fast, configurable, CI-friendly | CI/CD |
| **git-secrets** (AWS) | AWS-focused, simple | AWS credentials |
| **Talisman** (ThoughtWorks) | Pattern-based, checksum support | Pre-commit |

### Implementing detect-secrets

**Setup baseline (acknowledge existing secrets):**
```bash
# Generate baseline (treats existing findings as acknowledged)
detect-secrets scan > .secrets.baseline

# Review and acknowledge legitimate findings
detect-secrets audit .secrets.baseline
```

**Pre-commit configuration:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package.lock.json
```

**What it catches:**
```python
# These would be blocked:
api_key = "sk_live_abc123def456"      # Stripe key pattern
aws_key = "AKIAIOSFODNN7EXAMPLE"       # AWS access key pattern
password = "hunter2"                   # Keyword + string
github_token = "ghp_xxxxxxxxxxxx"      # GitHub token pattern
```

### Implementing gitleaks

**Configuration (`.gitleaks.toml`):**
```toml
[extend]
useDefault = true

[allowlist]
paths = [
    '''\.secrets\.baseline''',
    '''package-lock\.json''',
]

[[rules]]
description = "Custom API Key"
regex = '''mycompany_key_[a-zA-Z0-9]{32}'''
tags = ["api", "custom"]
```

**Run locally:**
```bash
# Scan current state
gitleaks detect --source . -v

# Scan Git history
gitleaks detect --source . --log-opts="--all" -v
```

**CI integration (GitHub Actions):**
```yaml
name: Secrets Scan
on: [push, pull_request]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## IDE Security Plugins

### The Fastest Feedback Loop

```
Feedback Loop Speed
───────────────────

IDE Plugin:        [=] seconds       ← Best!
Pre-commit:        [===] seconds     ← Good
CI/CD:             [============] minutes to hours
Security Review:   [=========================] days to weeks
```

IDE plugins give developers feedback while they type.

### Recommended Plugins by IDE

**VS Code:**
| Plugin | Purpose |
|--------|---------|
| SonarLint | Real-time SAST |
| Snyk | Vulnerability scanning |
| GitLens | Git history, identify who added secrets |
| ESLint (security plugin) | JavaScript security rules |
| Semgrep | Custom security rules |

**IntelliJ IDEA:**
| Plugin | Purpose |
|--------|---------|
| SonarLint | Real-time SAST |
| Snyk | Vulnerability scanning |
| Checkmarx | Enterprise SAST |
| SpotBugs | Java security bugs |

**VS Code SonarLint Configuration:**
```json
// settings.json
{
  "sonarlint.rules": {
    "javascript:S2068": {
      "level": "on"   // Hard-coded credentials
    },
    "javascript:S5131": {
      "level": "on"   // XSS
    },
    "javascript:S2076": {
      "level": "on"   // OS command injection
    }
  }
}
```

### What IDE Plugins Catch

**Real-time examples:**

```python
# Python with SonarLint
query = "SELECT * FROM users WHERE id = " + user_id
#       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#       💡 SQL Injection vulnerability detected
#          Use parameterized queries instead

password = "admin123"
#          ^^^^^^^^^
#       💡 Hard-coded password detected
#          Use environment variables or secrets manager
```

```javascript
// JavaScript with ESLint security plugin
document.innerHTML = userInput;
//                   ^^^^^^^^^
//       💡 Potential XSS vulnerability
//          Sanitize user input before rendering

exec("ls " + userInput);
//           ^^^^^^^^^
//       💡 Command injection risk
//          Use spawn with array arguments instead
```

---

## Static Analysis (SAST) Integration

### SAST at Different Stages

```
┌─────────────────────────────────────────────────────────────┐
│                    SAST INTEGRATION POINTS                   │
│                                                              │
│  IDE              Pre-commit           CI/CD                 │
│  ┌──────┐        ┌──────┐            ┌──────┐               │
│  │Sonar │        │Semgrep│           │CodeQL│               │
│  │Lint  │        │(fast) │           │(full)│               │
│  └──────┘        └──────┘            └──────┘               │
│     │               │                   │                    │
│ Real-time       Blocking           Comprehensive            │
│ squiggles       on commit          report                    │
│                                                              │
│  Speed: Fast ◀──────────────────────────────▶ Slow          │
│  Depth: Shallow ◀────────────────────────────▶ Deep         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Strategy:** Fast, shallow checks early; deep analysis in CI.

### Semgrep for Pre-commit

Semgrep is fast enough for pre-commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.45.0
    hooks:
      - id: semgrep
        args: ['--config', 'p/security-audit', '--error']
```

**Custom rules (`.semgrep.yaml`):**
```yaml
rules:
  - id: hardcoded-secret
    patterns:
      - pattern-either:
          - pattern: $X = "..."
          - pattern: $X = '...'
    message: "Potential hardcoded secret in variable $X"
    severity: ERROR
    languages: [python, javascript, typescript]
```

### Bandit for Python

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-ll", "-ii"]  # Low severity = Low confidence
```

**What Bandit catches:**
```python
# B106: Hardcoded password
connection = connect(password="secret123")

# B102: Use of exec
exec(user_input)

# B608: SQL injection
query = "SELECT * FROM users WHERE id = %s" % user_id

# B301: Pickle usage
pickle.loads(untrusted_data)
```

### ESLint Security Plugin for JavaScript

```json
// .eslintrc.json
{
  "plugins": ["security"],
  "extends": ["plugin:security/recommended"],
  "rules": {
    "security/detect-object-injection": "error",
    "security/detect-non-literal-regexp": "warn",
    "security/detect-unsafe-regex": "error",
    "security/detect-buffer-noassert": "error",
    "security/detect-eval-with-expression": "error",
    "security/detect-no-csrf-before-method-override": "error",
    "security/detect-possible-timing-attacks": "warn"
  }
}
```

---

## War Story: The $0 Secret That Almost Cost Millions

A startup was preparing for their Series B funding round. Due diligence included a security audit.

**The Discovery:**

The auditors ran TruffleHog against their main repository:

```bash
$ trufflehog git https://github.com/startup/main-app --only-verified

Found verified secret!
Detector Type: AWS
Decoder Type: PLAIN
Raw result: AKIAIOSFODNN7EXAMPLE
File: scripts/deploy.sh
Commit: abc123def (2019)
Author: Former Employee
```

An AWS key from 2019. The employee had left in 2020. The key was removed in a later commit. But it was still in Git history.

**The Impact:**
- Key had admin privileges
- Had been in history for 4 years
- Accessible to anyone with repo access
- Past contractors, past employees

**The Fix:**
1. Immediately rotate the AWS key
2. Audit CloudTrail for suspicious activity
3. Rewrite Git history (painful, but necessary)
4. Implement pre-commit secrets detection
5. Set up AWS key rotation policy

**The Lesson:**

They implemented a three-layer defense:
```
Layer 1: Pre-commit hooks (detect-secrets)
         → Blocks secrets before commit

Layer 2: CI/CD scanning (gitleaks)
         → Catches anything that slipped through

Layer 3: GitHub secret scanning
         → Alerts on known secret patterns
```

Cost to implement: A few hours.
Cost if exploited: Could have been catastrophic.

---

## Configuration as Code

### IaC Security Scanning

Infrastructure as Code (IaC) can have security issues too:

```yaml
# Terraform - Insecure
resource "aws_security_group" "bad" {
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Open to the world!
  }
}

# Kubernetes - Insecure
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    securityContext:
      privileged: true  # Never do this!
```

### Tools for IaC Scanning

| Tool | Targets | Pre-commit Support |
|------|---------|-------------------|
| **Checkov** | Terraform, K8s, CloudFormation, Dockerfile | Yes |
| **tfsec** | Terraform | Yes |
| **Kubesec** | Kubernetes | Yes |
| **kube-linter** | Kubernetes, Helm | Yes |
| **Trivy** | Everything + vulnerabilities | Yes |

### Checkov Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/bridgecrewio/checkov
    rev: 2.4.0
    hooks:
      - id: checkov
        args: [--quiet]
```

**What Checkov catches:**
```hcl
# CKV_AWS_23: Ensure every security group rule has a description
resource "aws_security_group_rule" "bad" {
  type        = "ingress"
  # Missing: description = "..."
}

# CKV_AWS_79: Ensure Instance Metadata Service Version 1 is not enabled
resource "aws_instance" "bad" {
  # Missing: metadata_options block
}
```

### Kubesec for Kubernetes

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: kubesec
        name: kubesec
        entry: bash -c 'kubesec scan "$@" | jq -e ".[].score >= 0"'
        language: system
        files: '\.(yaml|yml)$'
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Hook bypass with `--no-verify` | Developers skip checks | Make CI/CD mandatory, monitor bypass rate |
| Too many checks = slow hooks | Developers disable hooks | Keep pre-commit < 5 seconds |
| No baseline for existing code | 1000 findings = ignored | Create baseline, focus on new issues |
| Not sharing hook config | Inconsistent team setup | Commit `.pre-commit-config.yaml` |
| IDE plugins without team standards | Different results per dev | Document recommended plugins |
| Only checking on commit | Miss issues in development | Add IDE real-time analysis |

---

## Metrics for Shift-Left Success

Track these to measure effectiveness:

```
┌─────────────────────────────────────────────────────────────┐
│                    SHIFT-LEFT METRICS                        │
│                                                              │
│  Issues by Discovery Stage                                   │
│  ─────────────────────────                                   │
│                                                              │
│  IDE         ████████████████████  40%    ← Goal: increase  │
│  Pre-commit  ███████████████       30%    ← Goal: increase  │
│  CI/CD       █████████             20%    ← Goal: decrease  │
│  Production  ████                  10%    ← Goal: minimize  │
│                                                              │
│  Mean Time to Remediation (by stage)                        │
│  ─────────────────────────────────                          │
│                                                              │
│  IDE         5 minutes     ← Developer fixes while typing   │
│  Pre-commit  15 minutes    ← Fix before commit              │
│  CI/CD       2 hours       ← Context switch needed          │
│  Production  2 weeks       ← Full incident response         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Good signs:**
- More issues caught in IDE/pre-commit
- Fewer issues in CI/CD
- Near-zero in production
- MTTR decreasing at each stage

---

## Quiz: Check Your Understanding

### Question 1
A developer uses `git commit --no-verify` to bypass pre-commit hooks because "the hook is slow." How should this be addressed?

<details>
<summary>Show Answer</summary>

**Address both the symptom and root cause:**

**Root cause (slow hooks):**
- Audit which checks are slow
- Move slow checks to CI (keep fast ones in pre-commit)
- Target < 5 seconds for pre-commit
- Use incremental scanning (only changed files)

**Symptom (bypass):**
- Monitor `--no-verify` usage (wrapper script or CI check)
- Ensure CI runs same checks (can't skip)
- Document why hooks matter (link to past incidents)
- Make CI failure visible (Slack, email)

**Technical solutions:**
```bash
# Git alias that logs bypass attempts
git config --global alias.yolo '!f() {
  echo "$(date): bypass used" >> ~/.git-bypass.log;
  git commit --no-verify "$@";
}; f'
```

**Cultural solutions:**
- Discuss in retrospectives
- Track as team metric
- Celebrate when hooks catch issues

Pre-commit is a safety net, not a punishment. If developers bypass it, the process needs fixing.

</details>

### Question 2
You run `detect-secrets scan` on a legacy codebase and get 500 findings. What's the right approach?

<details>
<summary>Show Answer</summary>

**Don't try to fix all 500 at once. Use baselining:**

1. **Generate baseline:**
   ```bash
   detect-secrets scan > .secrets.baseline
   ```

2. **Audit baseline (mark false positives):**
   ```bash
   detect-secrets audit .secrets.baseline
   ```
   - Mark true positives for remediation
   - Mark false positives as acknowledged
   - Mark test data as acknowledged

3. **Commit baseline:**
   ```bash
   git add .secrets.baseline
   git commit -m "Add secrets baseline"
   ```

4. **Enable pre-commit with baseline:**
   ```yaml
   - repo: https://github.com/Yelp/detect-secrets
     hooks:
       - id: detect-secrets
         args: ['--baseline', '.secrets.baseline']
   ```

5. **Now:**
   - New secrets = blocked
   - Existing secrets = tracked for remediation
   - Legacy = addressed over time

**Priority for remediation:**
1. Production secrets (rotate immediately)
2. API keys with external access
3. Internal credentials
4. Test/mock data (lowest priority, may be fine)

</details>

### Question 3
Why is secrets scanning in pre-commit critical, as opposed to just in CI/CD?

<details>
<summary>Show Answer</summary>

**Because Git history is (nearly) permanent:**

Once a secret is committed:
1. It's in local Git history
2. After push, it's in remote history
3. Anyone with repo access can find it
4. `git revert` doesn't remove it (only the current file)
5. Full removal requires `git filter-branch` or BFG (disruptive)

**Pre-commit prevents the commit from happening:**
```
With pre-commit:
  Code → Pre-commit → ❌ BLOCKED → Never in history

Without pre-commit:
  Code → Commit → Push → CI fails → Secret in history forever
```

**Even if you delete and push again:**
```bash
# This doesn't help:
git rm secrets.txt
git commit -m "Remove secrets"
git push

# Secret still visible:
git log -p  # Shows the secret in history
```

**CI/CD scanning is still valuable** for:
- Deep history scans (already committed secrets)
- Backup if pre-commit bypassed
- Broader pattern matching

But pre-commit is the first line of defense that prevents the problem.

</details>

### Question 4
An IDE security plugin shows a warning for every use of `eval()` in JavaScript, but your codebase has legitimate uses in a sandboxed environment. How do you handle this?

<details>
<summary>Show Answer</summary>

**Don't disable the rule globally. Use targeted suppression:**

**Option 1: Inline suppression with comment**
```javascript
// eslint-disable-next-line security/detect-eval-with-expression
const result = sandboxedEval(expression);
```

**Option 2: File-level suppression**
```javascript
/* eslint-disable security/detect-eval-with-expression */
// This file contains sandboxed eval in controlled environment
// Risk accepted: JIRA-1234
```

**Option 3: Directory-level override**
```json
// .eslintrc.json in the specific directory
{
  "rules": {
    "security/detect-eval-with-expression": ["warn", {
      "allow": ["sandboxedEval"]
    }]
  }
}
```

**Best practice:**
- Document WHY the suppression exists
- Link to ticket/decision record
- Require review for new suppressions
- Periodically audit suppressions

**Never:**
- Disable the rule globally
- Suppress without documentation
- Let suppressions accumulate without review

The goal is security awareness, not zero warnings. Acknowledged risks are fine; unknown risks are not.

</details>

---

## Hands-On Exercise: Implement Pre-Commit Security

Set up a complete pre-commit security configuration for a project.

### Part 1: Setup Pre-commit Framework

```bash
# Create test directory
mkdir shift-left-demo && cd shift-left-demo
git init

# Install pre-commit
pip install pre-commit

# Create configuration
cat > .pre-commit-config.yaml << 'EOF'
repos:
  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # General security
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.45.0
    hooks:
      - id: semgrep
        args: ['--config', 'p/secrets', '--config', 'p/security-audit', '--error']
EOF

# Install hooks
pre-commit install

# Create empty baseline
echo "{}" > .secrets.baseline
```

### Part 2: Test Secrets Detection

```bash
# Create file with secret
cat > config.py << 'EOF'
# Database configuration
DB_HOST = "localhost"
DB_PASSWORD = "super_secret_password_123"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
EOF

# Try to commit
git add .
git commit -m "Add config"
# Should FAIL with secrets detected
```

### Part 3: Fix and Commit

```bash
# Fix the secrets issue
cat > config.py << 'EOF'
import os

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PASSWORD = os.getenv("DB_PASSWORD")
AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
EOF

# Update baseline
detect-secrets scan > .secrets.baseline

# Now commit should work
git add .
git commit -m "Add config with environment variables"
```

### Part 4: Test SAST Rules

```bash
# Create file with security issue
cat > app.py << 'EOF'
import os

def run_command(user_input):
    # Vulnerable to command injection
    os.system("echo " + user_input)

def get_user(user_id):
    # Vulnerable to SQL injection
    query = "SELECT * FROM users WHERE id = " + user_id
    return query
EOF

# Try to commit
git add app.py
git commit -m "Add app"
# Should FAIL with security issues
```

### Success Criteria

- [ ] Pre-commit framework installed
- [ ] Secrets detection blocks hardcoded credentials
- [ ] Baseline allows clean commits after fixing
- [ ] SAST rules catch injection vulnerabilities
- [ ] Understand how to fix flagged issues

---

## Key Takeaways

1. **Pre-commit is the earliest automated defense** — Catch issues before they enter Git history
2. **Secrets in Git are forever** — Pre-commit is the only reliable way to prevent this
3. **IDE plugins provide instant feedback** — Developers learn while coding
4. **Baseline legacy issues** — Don't block all commits; focus on new issues
5. **Speed matters** — Pre-commit hooks must be fast or developers will bypass them

---

## Further Reading

**Tools Documentation:**
- **pre-commit** — pre-commit.com
- **detect-secrets** — github.com/Yelp/detect-secrets
- **gitleaks** — github.com/gitleaks/gitleaks
- **Semgrep** — semgrep.dev

**Books:**
- **"Agile Application Security"** — Laura Bell et al.

**Articles:**
- **"Git Secrets: A Guide to Detection"** — AWS Security Blog
- **"Shift Left Security"** — OWASP

**Talks:**
- **"Secrets in Source Code"** — DEF CON (YouTube)

---

## Summary

Shift-left security pushes security checks as early as possible in the development lifecycle:

- **IDE plugins** give real-time feedback while coding
- **Pre-commit hooks** catch issues before they enter Git
- **Secrets detection** prevents credentials from ever being committed
- **SAST in pre-commit** catches code vulnerabilities early

The key is speed and developer experience. Checks must be fast (< 5 seconds) or developers will bypass them. Use baselining to handle legacy issues without blocking current work.

The earlier you catch issues, the cheaper they are to fix—and the more developers learn secure coding practices.

---

## Next Module

Continue to [Module 4.3: Security in CI/CD Pipelines](../module-4.3-security-cicd/) to learn how to implement comprehensive security scanning in your build and deployment pipelines.

---

*"The best time to catch a security bug was at code time. The second best time is pre-commit."*
