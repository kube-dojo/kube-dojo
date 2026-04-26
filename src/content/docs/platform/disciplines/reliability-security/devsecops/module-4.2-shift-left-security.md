---
title: "Module 4.2: Shift-Left Security"
slug: platform/disciplines/reliability-security/devsecops/module-4.2-shift-left-security
sidebar:
  order: 3
---

# Module 4.2: Shift-Left Security

> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 45-55 min | Track: DevSecOps

## Prerequisites

Before starting this module, the learner should be comfortable with the security workflow introduced in [Module 4.1: DevSecOps Fundamentals](../module-4.1-devsecops-fundamentals/), because this lesson assumes the team already understands shared ownership between development, operations, and security.

The module also assumes working knowledge of Git commits, branches, local hooks, pull requests, and basic CI behavior. The examples use Python, JavaScript, YAML, shell scripts, and Kubernetes manifests, but the security patterns apply across most application stacks.

Learners will get the most value if they have seen static analysis warnings in an IDE before, even if they have not configured the rules themselves. Prior experience with pre-commit, Semgrep, Bandit, detect-secrets, or gitleaks is helpful but not required.

---

## Learning Outcomes

After completing this module, the learner will be able to:

- **Design** a layered shift-left security workflow that gives developers fast local feedback without removing deeper CI and production controls.
- **Implement** pre-commit security checks that block newly introduced secrets, risky code patterns, and insecure configuration before a commit is created.
- **Debug** a failing local security hook by separating tool configuration problems, real findings, false positives, baselines, and developer-experience issues.
- **Evaluate** when a security rule belongs in an IDE, pre-commit hook, pre-push hook, CI job, or server-side enforcement point.
- **Compare** secrets scanning, SAST, dependency scanning, and IaC scanning strategies so that each control is placed where it catches the right class of risk.

---

## Why This Module Matters

A platform team can spend months building a polished DevSecOps pipeline and still leave developers with security feedback that arrives too late. A pull request may pass unit tests, wait in review, trigger security scanning, and then fail because a token, unsafe query, permissive container setting, or vulnerable dependency was introduced hours or days earlier. By then, the author has moved on, the reviewer has lost flow, and the fix competes with delivery pressure.

The teams that handle security well do not treat the central pipeline as the first place a developer learns about risk. They move selected checks closer to the moment of creation, where the author still remembers the exact change, the intended behavior, and the local context. A warning in the editor or a fast hook before commit turns a security issue from a compliance event into ordinary engineering feedback.

Shift-left security matters because it changes the cost curve. A secret caught before commit never enters Git history. A risky API call caught while the developer is typing does not need a late-stage security review debate. An insecure Terraform rule caught locally avoids a failed deployment window. The practice is not about pushing all security responsibility onto developers; it is about designing guardrails that make the secure path easier, faster, and more visible.

The senior-level skill is choosing what to shift left and what to leave later. Fast, deterministic, low-noise checks belong close to the developer. Slow, expensive, whole-repository, or environment-aware checks usually belong in CI or production monitoring. A good DevSecOps platform gives teams both: early feedback for preventable mistakes and deeper independent verification for everything that requires more context.

---

## 1. The Shift-Left Feedback Model

Shift-left security means moving useful security feedback closer to the point where a change is authored. It does not mean every scanner must run inside the editor, and it does not mean the pipeline becomes optional. The phrase is useful only when it describes a deliberate feedback design: which signal appears at which stage, how long it takes, how trustworthy it is, and what the developer can do next.

```text
The Commit-to-Production Feedback Timeline
──────────────────────────────────────────────────────────────────────────────▶

  Authoring          Local Gate          Shared Gate          Runtime Gate
  IDE/editor         pre-commit          CI / PR checks        deploy / observe
      │                  │                    │                    │
      ▼                  ▼                    ▼                    ▼
  ┌──────────┐      ┌──────────┐        ┌──────────┐        ┌──────────┐
  │  WRITE   │─────▶│  BLOCK   │───────▶│  VERIFY  │───────▶│  DETECT  │
  └──────────┘      └──────────┘        └──────────┘        └──────────┘
      │                  │                    │                    │
      │                  │                    │                    │
      ├─ seconds         ├─ seconds           ├─ minutes           ├─ minutes to days
      ├─ low context     ├─ local context     ├─ repo context      ├─ real behavior
      └─ best for hints  └─ best for blockers └─ best for proof    └─ best for response
```

A useful early check has three properties: it is fast enough that developers tolerate it, specific enough that developers trust it, and actionable enough that the fix is obvious or discoverable. A hook that takes a minute and emits hundreds of findings will be bypassed. An IDE warning that flags every safe wrapper as dangerous will be ignored. A CI-only scanner that reports a hardcoded credential after it has already been pushed is valuable as a backup but late as a prevention control.

The guiding question is not "Can this tool run earlier?" The better question is "Does running this tool earlier improve the decision the developer can make right now?" A fast secret pattern check improves the commit decision because the correct response is usually to remove the value and rotate the credential. A full container image scan may not help before commit if the image does not exist yet, so it belongs later.

```text
Signal Quality by Stage
──────────────────────────────────────────────────────────────────────────────

  ┌──────────────────┬──────────────────────┬───────────────────────────────┐
  │ Stage            │ Best signal           │ Poor fit                      │
  ├──────────────────┼──────────────────────┼───────────────────────────────┤
  │ IDE              │ risky API use         │ full dependency graph proof   │
  │ pre-commit       │ new secret patterns   │ slow whole-history audits     │
  │ pre-push         │ broader repo checks   │ production-only behavior      │
  │ CI / pull request│ complete SAST reports │ hints that could be instant   │
  │ deployment       │ policy enforcement    │ style issues                  │
  │ runtime          │ exploit attempts      │ preventable syntax mistakes   │
  └──────────────────┴──────────────────────┴───────────────────────────────┘
```

**Pause and predict:** A team adds a pre-commit hook that runs every unit test, a dependency audit, a full container build, a complete SAST scan, and a license audit. Commits now take several minutes. Before reading further, decide which developer behaviors are likely to appear and which checks should move to a later stage.

The likely result is bypass pressure. Developers may use `--no-verify`, create temporary commits outside the hook path, disable the framework locally, or delay commits until work piles up. The fix is not to lecture the team about discipline. The fix is to split the control set so that only fast, local, deterministic checks block commits, while slower checks run on pre-push or CI where the team still gets enforcement without damaging the inner development loop.

| Stage | Good Fit | Why It Belongs There | Common Failure Mode |
|---|---|---|---|
| IDE | Security linting, unsafe APIs, dependency hints | Feedback appears while the author still sees the code path | Too much noise causes warning blindness |
| Pre-commit | New secrets, simple SAST patterns, changed-file linting | The commit can be stopped before bad data enters history | Hook becomes slow and gets bypassed |
| Pre-push | Wider test or scan sets, branch-level checks | More time is acceptable before sharing changes | Developers discover failures after many commits |
| CI / PR | Full SAST, dependency audit, IaC policy, tests | Central enforcement is consistent and auditable | Results arrive after context switching |
| Server-side Git | Required checks, protected branches, secret scanning | Local bypass cannot skip remote enforcement | Poor error messages frustrate contributors |
| Runtime | Attack detection, policy violations, drift | Only real traffic and deployed state reveal some risks | Incident response replaces prevention |

A senior engineer uses that table as a design tool, not as a rulebook. For example, a high-risk payments service may run a stricter pre-push check than an internal prototype. A monorepo may use path-aware hooks so a documentation change does not trigger a Java dependency scan. A regulated team may require server-side enforcement for the same rule that developers also see locally.

The important pattern is layered defense. IDE checks are coaching. Pre-commit checks are a local gate. CI checks are shared proof. Server-side rules are enforcement. Runtime controls are detection and response. Shift-left improves the early layers, but it never deletes the later layers because local tooling can be misconfigured, skipped, stale, or unavailable.

---

## 2. Pre-Commit Security Controls

A Git pre-commit hook runs before Git creates a commit object. That timing matters because it can prevent a bad change from becoming part of local history at all. For secrets, this is the difference between "remove the string and try again" and "rotate the credential, rewrite history, notify downstream consumers, and audit access logs."

```text
Git Hook Lifecycle for Security
──────────────────────────────────────────────────────────────────────────────

  Local developer machine                                      Shared systems

  ┌────────────┐     ┌────────────┐     ┌────────────┐       ┌──────────────┐
  │ pre-commit │────▶│ commit-msg │────▶│ pre-push   │──────▶│ pre-receive  │
  └────────────┘     └────────────┘     └────────────┘       └──────────────┘
       │                   │                  │                      │
       │                   │                  │                      │
       ├─ scan staged      ├─ validate        ├─ run broader         ├─ enforce rules
       │  content          │  message         │  checks before       │  on the server
       │                   │                  │  sharing branch      │
       │                   │                  │                      │
       └─ best place       └─ useful for      └─ useful for          └─ cannot be skipped
          to stop             traceability       slower local           by local config
          new secrets                            verification
```

The pre-commit stage should operate mostly on staged files rather than the entire repository. That keeps feedback fast and avoids surprising the developer with old unrelated findings. A whole-repository cleanup is still valuable, but it belongs in a planned remediation effort or CI report, not as a blocker for every small commit.

The most common framework for multi-language projects is `pre-commit`, which stores hook configuration in `.pre-commit-config.yaml`. The configuration is versioned with the repository, so every contributor can install the same checks. That is a major improvement over undocumented `.git/hooks` scripts, because native Git hooks live inside the local `.git` directory and are not normally committed.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]

  - repo: https://github.com/semgrep/pre-commit
    rev: v1.118.0
    hooks:
      - id: semgrep
        args: ["--config", "p/secrets", "--config", "p/security-audit", "--error"]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.3
    hooks:
      - id: bandit
        args: ["-ll", "-ii"]
        files: "\\.py$"

  - repo: https://github.com/hadolint/hadolint
    rev: v2.13.1-beta
    hooks:
      - id: hadolint-docker
```

This configuration uses four different kinds of checks. `detect-secrets` focuses on credential patterns and baseline management. Semgrep catches configurable code patterns across several languages. Bandit adds Python-specific security analysis. Hadolint catches risky Dockerfile patterns before container builds reach CI.

The versions are pinned because reproducibility matters. A floating branch or latest tag can silently change rule behavior, causing one developer to pass and another to fail. Pinning also creates an explicit upgrade workflow: test the new scanner version, examine rule changes, update baselines if needed, and commit the change intentionally.

```bash
# Run from the repository root after a .pre-commit-config.yaml exists.
.venv/bin/pre-commit install
.venv/bin/pre-commit run --all-files
```

The first command installs the framework-managed Git hook into the local repository. The second command runs every configured hook against all matching files, which is useful when introducing the framework to an existing project. After the initial setup, normal commits run checks only for files selected by the hooks and framework.

If the repository does not already have the tools in its virtual environment, install them explicitly through the repository Python environment rather than relying on whatever happens to be on the machine path. A reproducible local environment reduces "works on my laptop" drift and makes onboarding documentation easier to trust.

```bash
.venv/bin/python -m pip install pre-commit detect-secrets semgrep bandit
.venv/bin/pre-commit --version
.venv/bin/detect-secrets --version
.venv/bin/semgrep --version
.venv/bin/bandit --version
```

Native Git hooks are still useful for tiny repositories or one-off experiments, but they do not scale as well for teams. A native hook must be copied or installed manually, and different contributors may edit it without versioned review. In a mature platform, native hooks are usually wrapped by a versioned framework or generated from a central template.

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit
set -euo pipefail

echo "Running a minimal local secret pattern check..."

if git diff --cached --name-only | grep -E '\.(py|js|ts|yaml|yml|env)$' >/dev/null; then
  git diff --cached --unified=0 | grep -E '(AKIA[0-9A-Z]{16}|password[[:space:]]*=)' && {
    echo "Potential secret pattern found in staged changes."
    exit 1
  }
fi

echo "No minimal secret pattern found."
```

This native hook is intentionally narrow. It scans staged diffs for a small set of obvious patterns, exits with a failure when it finds one, and leaves deeper detection to purpose-built tools. It is runnable, but it is not a substitute for a mature scanner because regex-only hooks miss many formats and can create false positives.

| Hook Type | Strength | Weakness | Best Use |
|---|---|---|---|
| Native `.git/hooks/pre-commit` | Very simple and dependency-light | Not versioned by default and easy to drift | Small experiments or bootstrap checks |
| `pre-commit` framework | Multi-language, versioned, repeatable | Requires installation and periodic updates | Most shared repositories |
| Husky | Natural fit for Node projects | JavaScript-centric workflow | Frontend and TypeScript projects |
| Server-side hook | Cannot be skipped locally | Requires Git hosting or admin control | Critical enforcement and protected repos |
| CI required check | Central audit trail and consistent execution | Feedback arrives later than local hooks | Full verification and bypass backup |

A platform team should document expected hook runtime. A practical target for pre-commit is usually under five seconds for common changes, with rare heavier checks clearly explained. When runtime grows, the team should profile the hook set instead of accepting bypasses as normal.

**Pause and predict:** A Python service introduces Bandit and Semgrep in pre-commit. Developers report that commits touching documentation now run Python security checks anyway. What configuration mistake would cause that, and what should be changed?

The likely mistake is a missing file filter. Hooks should use `files`, `types`, or scanner-specific include options so unrelated changes do not trigger irrelevant checks. This is not just a performance issue; irrelevant failures teach developers that security tooling is arbitrary. A good hook is scoped tightly enough that its result feels connected to the change being committed.

---

## 3. Secrets Detection and Git History

Secrets detection deserves special treatment because a committed credential has a different failure mode from most bugs. A vulnerable function can often be fixed in the next commit. A leaked secret must be treated as compromised because the value may have been copied, logged, cached, indexed, or fetched by people and systems that are outside the current file view.

```text
The Secret-in-Git Problem
──────────────────────────────────────────────────────────────────────────────

  Commit A
  ┌────────────────────────────────────────────────────────────────────────┐
  │ settings.py                                                           │
  │ DATABASE_URL = "postgres://admin:plaintext-value@db.example.internal" │
  └────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  Commit B
  ┌────────────────────────────────────────────────────────────────────────┐
  │ settings.py                                                           │
  │ DATABASE_URL = os.environ["DATABASE_URL"]                             │
  └────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  Current file looks clean, but history still contains Commit A.

  git log -p -- settings.py
  git show <old-commit>:settings.py
  git clone --mirror <repo>
```

The phrase "secrets in Git are forever" is shorthand for a practical reality. Git history is distributed, cached, cloned, and backed up. Rewriting history can remove a value from the main repository, but it cannot guarantee that every clone, fork, CI cache, artifact, or log has been cleaned. The correct response to a real secret in history is rotation plus investigation, not simply deleting the line.

Pre-commit secret scanning prevents the easiest version of that incident. The scanner examines staged content before the commit exists. If it finds a likely credential, the developer can remove the value, replace it with an environment variable or secret manager reference, and commit a safe change without creating an incident.

```python
# insecure_config.py
DATABASE_PASSWORD = "plain-text-password-for-demo"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
GITHUB_TOKEN = "ghp_exampleexampleexampleexampleexample"
```

Those examples should never be treated as realistic credentials, but they demonstrate the categories scanners look for: provider-specific prefixes, high-entropy strings, suspicious variable names, and known token formats. Scanners combine pattern matching, entropy detection, allowlists, and baselines to reduce false positives.

A baseline is a snapshot of acknowledged findings. It is often necessary when adding secret detection to an existing repository that already contains test fixtures, fake tokens, historical examples, or real findings being remediated in phases. The baseline prevents old findings from blocking every new commit while still blocking newly introduced secrets.

```bash
# Create or refresh a detect-secrets baseline from the repository root.
.venv/bin/detect-secrets scan > .secrets.baseline

# Audit the baseline interactively so false positives and real findings are distinguished.
.venv/bin/detect-secrets audit .secrets.baseline

# Run the pre-commit hook after the baseline exists.
.venv/bin/pre-commit run detect-secrets --all-files
```

The baseline must not become a dumping ground for ignored risk. Each real finding needs an owner, severity, rotation decision, and remediation plan. If the value is a production credential, the first response is usually to rotate it immediately and inspect access logs. If it is a fake fixture, the team should make the fake nature obvious with names like `example`, `dummy`, or `not-a-real-secret`.

```toml
# .gitleaks.toml
[extend]
useDefault = true

[allowlist]
description = "Allow documented examples and generated scanner baselines"
paths = [
  '''\.secrets\.baseline''',
  '''docs/security/examples/.*''',
]

[[rules]]
id = "company-api-key"
description = "Company API key format"
regex = '''company_live_[A-Za-z0-9]{32}'''
tags = ["company", "api-key"]
```

Gitleaks is often used in CI because it can scan committed state and history efficiently. It also works locally, but a full history scan is usually too expensive for every commit. A common pattern is detect-secrets or a targeted gitleaks invocation in pre-commit, then broader gitleaks scanning in CI with `fetch-depth: 0` so history is available.

```yaml
name: Secrets Scan
on:
  pull_request:
  push:
    branches:
      - main

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

This CI job is not a replacement for pre-commit. It is the backup layer for skipped hooks, stale local environments, and branch history. In a healthy design, the same category of issue is visible locally before commit and centrally before merge, but the central check remains authoritative.

| Secret Scanner | Early-Stage Strength | Later-Stage Strength | Decision Guidance |
|---|---|---|---|
| detect-secrets | Strong baseline workflow and pre-commit fit | Less focused on deep verified history scanning | Use when legacy repositories need controlled adoption |
| gitleaks | Fast rule-based scanning and CI support | Strong repository and history scanning | Use for pull requests, branch scans, and custom rules |
| TruffleHog | Verified secret detection and deep discovery | Strong for audits and incident investigation | Use when confirming whether a finding is live or exploitable |
| git-secrets | Simple AWS-oriented local patterns | Narrower than general scanners | Use for teams heavily exposed to AWS credential leakage |
| Hosting-provider scanning | Central alerting for known token types | Depends on provider coverage and licensing | Use as an additional safety net, not the only layer |

A senior response to a secrets finding has two tracks. The first track fixes the code path so the secret is not embedded again. The second track handles the credential lifecycle: revoke, rotate, audit use, and communicate impact. Shift-left tooling helps with the first track, but incident handling discipline is still required for any value that already escaped.

**Pause and decide:** A scanner flags `tests/fixtures/payment_gateway.json` because it contains a realistic-looking test API key. The value is fake, but new developers keep asking whether it is safe. Should the team baseline it, rename it, suppress the rule, or move the fixture?

The best answer is usually to make the test data obviously fake and keep the scanner strict. A value named `sk_live_example` is a bad fixture because it resembles a real production token. A value named `not-a-real-token-for-tests` is easier for humans and tools to classify. Baselines and suppressions are useful, but the cleanest solution is often to remove ambiguity from the artifact itself.

---

## 4. IDE and SAST Feedback

IDE security plugins are the fastest feedback loop because they meet developers at the point of editing. Their job is not to prove that the repository is secure. Their job is to interrupt risky patterns while the code path is still visible and cheap to change.

```text
Feedback Speed and Depth
──────────────────────────────────────────────────────────────────────────────

  Faster feedback                                                       Deeper proof
  ◀──────────────────────────────────────────────────────────────────────────────▶

  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
  │ IDE hint    │──────▶│ pre-commit  │──────▶│ CI SAST     │──────▶│ review/audit │
  └─────────────┘       └─────────────┘       └─────────────┘       └─────────────┘
       │                     │                     │                     │
       ├─ seconds            ├─ seconds            ├─ minutes            ├─ hours/days
       ├─ partial context    ├─ staged context     ├─ repo context       ├─ human context
       └─ coaching           └─ blocking           └─ enforcement        └─ judgment
```

A useful IDE rule usually identifies a local pattern: hardcoded credential strings, unsafe HTML rendering, string-built SQL, shell command construction, path traversal, deserialization of untrusted data, or dangerous crypto choices. The warning is valuable because it changes the author's next keystroke, not because it produces an audit artifact.

```python
# app/users.py
import sqlite3

def find_user(connection: sqlite3.Connection, user_id: str):
    query = "SELECT id, email FROM users WHERE id = " + user_id
    return connection.execute(query).fetchone()
```

A SAST rule may flag the string concatenation because untrusted input can alter the SQL statement. The secure fix is not to sanitize with a homegrown regex. The secure fix is to use parameterized queries, which keep data separate from the query structure.

```python
# app/users.py
import sqlite3

def find_user(connection: sqlite3.Connection, user_id: str):
    query = "SELECT id, email FROM users WHERE id = ?"
    return connection.execute(query, (user_id,)).fetchone()
```

That example shows why shift-left is a teaching strategy as well as a control strategy. The developer sees the risky construction and the safer pattern next to each other. Over time, the team learns preferred idioms instead of waiting for security review comments.

JavaScript and TypeScript projects often combine ESLint security plugins, framework-specific linting, Semgrep, and IDE extensions. The same principle applies: use editor feedback for local patterns and CI for complete proof. A framework that escapes output by default may reduce XSS risk, but direct DOM writes still deserve local warnings.

```javascript
// app/renderProfile.js
export function renderProfile(container, userInput) {
  container.innerHTML = userInput;
}
```

```javascript
// app/renderProfile.js
export function renderProfile(container, userInput) {
  const textNode = document.createTextNode(userInput);
  container.replaceChildren(textNode);
}
```

The first version treats user input as markup. The second treats the same input as text. A good rule teaches that distinction. A noisy rule that flags every framework-managed rendering path without understanding the project will push developers toward broad suppressions, which is a design failure in the guardrail.

| IDE or Local Tool | Primary Signal | Good Team Standard | Risk if Misused |
|---|---|---|---|
| SonarLint | Local code smells and security warnings | Enable agreed high-value rules per language | Developers ignore broad warning sets |
| Snyk extension | Dependency and container hints | Pair with CI dependency enforcement | Local results differ from central policy |
| Semgrep extension | Custom organization rules | Start with a small trusted rule pack | Experimental rules create false positives |
| ESLint security plugin | JavaScript risky patterns | Use project-specific overrides with review | Global disables hide real issues |
| JetBrains inspections | Language-aware static checks | Share inspection profiles where practical | Personal IDE state drifts from team norms |
| CodeQL in CI | Deep semantic analysis | Use for central verification and queries | Too slow for most local commit paths |

SAST at pre-commit should be deliberately narrower than SAST in CI. Changed-file Semgrep rules, Bandit for touched Python files, or ESLint for staged JavaScript can be useful. Whole-program CodeQL analysis is usually better in CI because it needs time, dependencies, and repository context.

```yaml
# .semgrep.yaml
rules:
  - id: python-sql-string-concat
    languages:
      - python
    severity: ERROR
    message: "Use parameterized queries instead of concatenating SQL strings."
    patterns:
      - pattern: $CONN.execute("..." + $INPUT)
```

This rule is intentionally simple and would not catch every SQL injection pattern. That is acceptable for a teaching example. Production Semgrep rules should be tested against real code, tuned for false positives, and documented with examples of secure alternatives.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/semgrep/pre-commit
    rev: v1.118.0
    hooks:
      - id: semgrep
        args: ["--config", ".semgrep.yaml", "--error"]
        files: "\\.(py|js|ts)$"
```

The `files` filter keeps the hook scoped to languages the rules understand. Without that filter, a documentation-only change could still start a scanner, increasing runtime and reducing trust. Good shift-left design pays attention to this small operational detail because developer experience determines whether the control survives.

---

## 5. Configuration and IaC Security

Shift-left security is not limited to application code. Terraform, Kubernetes manifests, Helm charts, Dockerfiles, GitHub Actions workflows, and cloud configuration all encode production behavior. If a manifest grants privilege, opens a security group to the world, or runs a container as root, the risk can be caught before deployment.

```text
Configuration Risk Flow
──────────────────────────────────────────────────────────────────────────────

  Repository file                  Pipeline rendering              Cluster or cloud
  ┌────────────────┐              ┌────────────────┐              ┌────────────────┐
  │ deployment.yaml│─────────────▶│ templating     │─────────────▶│ API admission  │
  │ terraform.tf   │              │ validation     │              │ runtime policy │
  │ Dockerfile     │              │ image build    │              │ monitoring     │
  └────────────────┘              └────────────────┘              └────────────────┘
          │                                │                                │
          ├─ fastest place to catch        ├─ best place to validate        ├─ final place to enforce
          │  obvious insecure settings     │  rendered combined state       │  live environment rules
          │                                │                                │
          └─ examples: privileged pods,    └─ examples: Helm output,        └─ examples: admission control,
             open ingress, root containers   policy bundles, image scans      drift, runtime detection
```

A Kubernetes manifest that sets `privileged: true` is usually not a subtle vulnerability. It grants broad access from the container to the node and should require a strong exception process. A local IaC scanner can catch the field before the manifest reaches a cluster admission controller.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: insecure-demo
spec:
  containers:
    - name: app
      image: nginx:1.27
      securityContext:
        privileged: true
```

A safer baseline removes privileged mode, disables privilege escalation, sets a non-root identity, and uses a read-only root filesystem when the application permits it. Not every workload can use every hardening option immediately, but the manifest should make the risk explicit rather than accepting insecure defaults.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: safer-demo
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: nginx:1.27
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
```

Tools such as Checkov, Trivy, kube-linter, and Kubesec can run locally and in CI. The early-stage version should focus on obvious high-confidence findings. The CI version can run broader checks against rendered Helm output, Terraform plans, or full configuration directories.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/bridgecrewio/checkov
    rev: 3.2.405
    hooks:
      - id: checkov
        args: ["--quiet", "--framework", "kubernetes", "--framework", "terraform"]
        files: "\\.(yaml|yml|tf)$"
```

The `files` selector matters again. Running a Kubernetes scanner against every YAML file in a repository may produce false findings for examples, CI workflow files, or documentation fixtures. When a repository contains mixed YAML types, path filters are often better than extension filters.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/bridgecrewio/checkov
    rev: 3.2.405
    hooks:
      - id: checkov
        args: ["--quiet", "--framework", "kubernetes"]
        files: "^(deploy|helm|k8s)/.*\\.(yaml|yml)$"
```

Infrastructure scanning has one trap that application SAST does not always share: templates may not represent final deployed state. A Helm chart, Kustomize base, or Terraform module can look safe alone but render insecurely after values are applied. That is why local file scanning should be paired with CI jobs that scan rendered output or planned changes.

| IaC Target | Local Scanner Fit | CI Scanner Fit | Senior-Level Placement |
|---|---|---|---|
| Dockerfile | Strong for linting risky instructions | Strong for image and dependency scans | Lint locally, scan built image in CI |
| Kubernetes YAML | Strong for direct manifests | Stronger for rendered Helm or Kustomize | Scan changed files locally and rendered output centrally |
| Terraform code | Useful for obvious resource settings | Stronger with plan-aware policy checks | Run fast rules locally and plan checks in CI |
| GitHub Actions | Useful for pinned action and permission checks | Useful for organization policy enforcement | Catch obvious workflow risk before PR |
| Helm charts | Limited if values are missing | Strong after template rendering | Render in CI with representative values |
| CloudFormation | Useful for static resource checks | Strong with account policy context | Use local checks as hints and CI as gate |

**What would happen if:** A team scans only raw Helm chart templates in pre-commit and never scans rendered manifests in CI. A chart value enables host networking for a production environment. Decide which stage would miss the issue and which stage should catch it.

The pre-commit stage may miss the issue because the risky field appears only after values are merged. The CI stage should render the chart with representative values and scan the resulting manifests. This is constructive alignment in engineering form: local checks teach and catch simple mistakes, while shared checks validate the artifact that will actually be deployed.

---

## 6. Challenge/Solution Worked Example: Debugging a Broken Shift-Left Control

This worked example models the troubleshooting behavior expected in the hands-on exercise. The goal is not just to know which tool to install. The goal is to diagnose why a guardrail failed, decide whether the finding is real, and adjust the system without weakening security.

### Challenge

A payments team added `detect-secrets` and Semgrep to pre-commit. The next day, developers report three problems. Commits that change only Markdown still trigger Semgrep. A fake API key in a test fixture blocks every commit. One developer bypassed the hook with `--no-verify`, and CI still passed. The team lead asks whether pre-commit should be removed because it is slowing delivery.

```text
Observed Failure Report
──────────────────────────────────────────────────────────────────────────────

  Symptom A: Documentation commits run Semgrep and take too long.
  Symptom B: A fake token in tests blocks unrelated changes.
  Symptom C: A bypassed local hook still allows the pull request to pass CI.

  Question: Is the control wrong, or is the control placed and configured poorly?
```

The common beginner reaction is to disable the noisy rules. The senior reaction is to separate the failures. Symptom A is a scoping problem. Symptom B is a test-data and baseline problem. Symptom C is a missing central enforcement problem. Each needs a different fix, and removing pre-commit would throw away the useful parts of the control.

| Symptom | Diagnostic Question | Likely Root Cause | Correct Direction |
|---|---|---|---|
| Markdown changes trigger Semgrep | Is the hook filtered by file type or path? | Missing `files` filter | Scope the hook to supported languages |
| Fake token blocks unrelated changes | Is the token obviously fake and audited? | Ambiguous fixture or unmanaged baseline | Rename fixture or baseline with review |
| Local bypass passes CI | Does CI run equivalent checks? | Local-only enforcement | Add required CI checks |
| Developers complain about speed | Which hook consumes time? | No runtime budget or profiling | Move slow checks later |
| Warnings are ignored | Are findings actionable and trusted? | Rule noise or weak documentation | Tune rules and show fixes |

### Solution

Start with the scoping problem because it affects every developer. The Semgrep hook should run only on files where the configured rules apply. If the repository uses Python and JavaScript rules, a Markdown-only commit should not trigger those checks.

```yaml
# Before: Semgrep runs too broadly.
repos:
  - repo: https://github.com/semgrep/pre-commit
    rev: v1.118.0
    hooks:
      - id: semgrep
        args: ["--config", ".semgrep.yaml", "--error"]
```

```yaml
# After: Semgrep runs only for changed Python, JavaScript, and TypeScript files.
repos:
  - repo: https://github.com/semgrep/pre-commit
    rev: v1.118.0
    hooks:
      - id: semgrep
        args: ["--config", ".semgrep.yaml", "--error"]
        files: "\\.(py|js|ts)$"
```

Next, inspect the fake test token. If the value looks like a live provider token, rename the fixture so it is obviously non-secret. A scanner baseline can acknowledge unavoidable examples, but the better first move is to make examples unambiguous for both tools and humans.

```json
{
  "provider": "example-payments",
  "apiKey": "not-a-real-token-used-only-in-tests"
}
```

If the fixture must preserve a realistic shape for parser tests, add a narrow allowlist entry with a clear path and description. Avoid a broad regex suppression that would hide real tokens elsewhere in the repository.

```toml
# .gitleaks.toml
[allowlist]
description = "Allow deliberately fake payment fixture values used by parser tests"
paths = [
  '''tests/fixtures/payment_gateway_parser\.json''',
]
```

Finally, fix the enforcement gap. Local hooks are a convenience and teaching mechanism, not the final authority. CI must run equivalent or stronger checks, and branch protection should require them before merge. That way `--no-verify` can help a developer create a temporary local commit, but it cannot silently merge unscanned code.

```yaml
name: Security Gates
on:
  pull_request:

jobs:
  local-equivalent-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install security tools
        run: |
          python -m pip install pre-commit detect-secrets semgrep bandit
      - name: Run pre-commit checks in CI
        run: |
          pre-commit run --all-files
```

The CI example uses the hosted runner's Python because that is the CI environment, not the local KubeDojo repository environment. In the KubeDojo repository itself, local commands should use `.venv/bin/python` and `.venv/bin/pre-commit`. The key principle is consistency: CI should execute the same rule set or a stricter one, not a completely different interpretation of security.

The resulting decision is balanced. Keep pre-commit, but make it fast and scoped. Keep test fixtures, but make fake values obvious or narrowly allowlisted. Permit local bypass for emergencies if the organization chooses, but ensure CI and protected branches provide central enforcement. That is the troubleshooting behavior expected of a platform engineer: diagnose the control system instead of blaming either the developer or the tool.

---

## 7. Designing a Team-Level Shift-Left Program

A shift-left program fails when it is introduced as a pile of tools. It succeeds when the team treats each check as a product feature: there is a user, a workflow, a failure mode, a runtime budget, documentation, ownership, and a support path. Developers do not need another mysterious gate; they need clear feedback that helps them ship safer code with less rework.

The adoption sequence should begin with one or two high-confidence controls. Secrets detection is usually first because the risk is severe, the fix is easy to explain, and the benefit of preventing history contamination is concrete. A narrow SAST rule pack is often second. IaC scanning follows when the team has enough deployment configuration in the repository to make local checks useful.

```text
Practical Adoption Sequence
──────────────────────────────────────────────────────────────────────────────

  Step 1: Inventory common preventable findings.
          │
          ▼
  Step 2: Choose one high-confidence local control.
          │
          ▼
  Step 3: Run it in report-only mode or all-files mode once.
          │
          ▼
  Step 4: Baseline or remediate existing findings.
          │
          ▼
  Step 5: Block only new findings in pre-commit.
          │
          ▼
  Step 6: Add equivalent CI enforcement.
          │
          ▼
  Step 7: Track bypasses, runtime, false positives, and escaped issues.
```

The metrics should measure whether feedback is moving earlier and whether remediation is getting cheaper. Counting total findings without stage context can mislead leaders into thinking the program is getting worse when it is actually discovering issues earlier. Better metrics separate discovery stage, time to remediation, false-positive rate, and escaped issues.

```text
Shift-Left Metrics Model
──────────────────────────────────────────────────────────────────────────────

  Discovery Stage Distribution
  ┌──────────────┬─────────────────────────────┬────────────────────────────┐
  │ IDE          │ █████████████████████       │ desired to increase         │
  │ pre-commit   │ ████████████████            │ desired to increase         │
  │ CI / PR      │ ████████                    │ desired to decrease slowly  │
  │ production   │ ██                          │ desired to approach zero    │
  └──────────────┴─────────────────────────────┴────────────────────────────┘

  Supporting Measures
  ┌──────────────┬──────────────────────────────────────────────────────────┐
  │ Hook runtime │ Median and high-percentile runtime for normal commits    │
  │ Bypass rate  │ Frequency of commits created with local verification off │
  │ Noise rate   │ Findings closed as false positive or accepted risk       │
  │ Escape rate  │ Issues first detected in CI, deployment, or production   │
  └──────────────┴──────────────────────────────────────────────────────────┘
```

A healthy program will see some findings move from CI to local stages. That does not mean the central pipeline becomes less important. It means the pipeline can spend less time catching preventable mistakes and more time proving integrated behavior. The deepest checks remain central because they require whole-repository context, built artifacts, cloud state, or human judgment.

Exception handling is part of the design, not an afterthought. Some findings are false positives. Some risky patterns are accepted temporarily because migration would break production. Some suppressions are legitimate. The difference between mature risk acceptance and silent drift is documentation, ownership, expiration, and review.

```yaml
# .semgrepignore
# Temporary exception for legacy report renderer.
# Risk owner: appsec-platform
# Tracking issue: SEC-1820
# Review by: 2026-09-30
legacy/reporting/unsafe_renderer.py
```

That example shows the minimum information a suppression should carry. Without ownership and review, exceptions accumulate until the scanner becomes decorative. With ownership and review, exceptions become visible engineering debt that can be prioritized like any other risk.

| Design Decision | Beginner Approach | Senior Approach | Why the Senior Approach Works |
|---|---|---|---|
| Add a scanner | Enable the biggest default rule set | Start with high-confidence rules tied to common incidents | Trust grows from accurate findings |
| Handle legacy findings | Block everything immediately | Baseline, triage, and block only new risk | Teams can keep shipping while reducing debt |
| Deal with false positives | Disable the rule globally | Add narrow suppression with owner and review date | Useful signal remains intact |
| Improve speed | Tell developers to be patient | Profile hooks and move slow checks later | The control fits the workflow |
| Prevent bypass | Ban `--no-verify` culturally | Require equivalent CI checks and branch protection | Enforcement does not depend on local behavior |
| Measure success | Count scanner findings | Track discovery stage, MTTR, escapes, runtime, and noise | Metrics reflect real risk reduction |

**Pause and design:** A repository contains a small Go API, a Helm chart, Terraform for cloud resources, and Markdown documentation. The team wants a single command that runs local security checks. Decide which checks should run for every commit and which should run only when matching paths change.

A reasonable design runs secret detection for most staged text files, Go security linting only for Go files, Helm or Kubernetes scanning only for chart and manifest paths, Terraform scanning only for Terraform paths, and no application scanner for documentation-only commits. The point is not to make the command clever for its own sake; the point is to keep the developer's feedback relevant to the change.

---

## Did You Know?

1. **The `pre-commit` hook runs before Git creates the commit object**, which makes it uniquely valuable for stopping secrets before they enter local history. CI can catch a leaked value later, but the commit already exists by that point.

2. **Most mature teams still keep central CI enforcement after adding local hooks**, because local hooks can be skipped, misconfigured, or outdated. Shift-left improves feedback speed; it does not remove the need for independent verification.

3. **False positives are a product-design problem as much as a scanner problem**, because developers learn from the quality of the feedback loop. A small rule set with trusted findings often outperforms a huge rule set that everyone ignores.

4. **IaC scanning gets more accurate when it sees rendered output**, because Helm, Kustomize, Terraform modules, and environment-specific values can change the final security posture. Local file scanning is useful, but CI should validate deployable artifacts.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Running every scanner in pre-commit | Commits become slow, developers bypass hooks, and useful controls lose credibility | Keep pre-commit fast, path-aware, and focused on high-confidence findings |
| Treating local hooks as the only enforcement point | A developer can skip hooks or have stale tooling, allowing risky code into a pull request | Run equivalent or stronger checks in CI and require them before merge |
| Adding scanners without baselining legacy findings | Old issues block unrelated work and create pressure to disable the scanner entirely | Generate a reviewed baseline, remediate real risk by priority, and block new findings |
| Suppressing noisy rules globally | Real vulnerabilities disappear with the false positives, and future reviewers lose context | Use narrow suppressions with owner, reason, tracking issue, and review date |
| Scanning raw templates only | Helm, Kustomize, and Terraform may render into risky deployable state that local scans never see | Scan changed source locally and rendered or planned output in CI |
| Failing to document secure fixes | Developers see a block but do not learn the replacement pattern, so the same issue repeats | Include examples, links, and short remediation notes in rule messages or team docs |
| Letting IDE rules drift per developer | Different engineers see different warnings, causing inconsistent security behavior | Share recommended profiles and mirror critical rules in pre-commit or CI |
| Measuring only total findings | Increased early discovery can look like failure when it actually means the program is working | Track discovery stage, remediation time, false positives, bypasses, and production escapes |

---

## Quiz

### Question 1

A team adds a pre-commit configuration that runs secrets detection, dependency auditing, full SAST, unit tests, container builds, and Terraform plan checks. Developers begin committing with `--no-verify` because local commits take several minutes. How should the platform team redesign the guardrail without removing security coverage?

<details>
<summary>Show answer</summary>

The team should split the checks by feedback stage instead of treating pre-commit as the only gate. Fast, high-confidence checks such as staged-file secrets detection and narrow changed-file SAST rules should remain in pre-commit. Slower checks such as full dependency auditing, full SAST, container builds, and Terraform plans should move to pre-push or CI, where longer runtimes are acceptable and results are centrally visible.

The team should also measure hook runtime and set an explicit budget for normal commits. If a check is valuable but slow, the right fix is usually to move it later or make it path-aware, not to blame developers for bypassing it. CI should still run equivalent or stronger checks so a local bypass cannot merge unverified code.

</details>

### Question 2

A repository introduces detect-secrets and immediately reports hundreds of findings in old fixtures, generated examples, and a few likely real credentials. Product teams complain that they cannot commit unrelated fixes. What adoption plan preserves security while avoiding a blocked rollout?

<details>
<summary>Show answer</summary>

The team should create and audit a baseline rather than blocking all existing findings at once. Real credentials should be prioritized for rotation and investigation, while false positives and deliberately fake fixtures should be marked or rewritten so they are unambiguous. After the baseline is reviewed, the pre-commit hook should block newly introduced findings while legacy remediation proceeds separately.

This approach preserves the most important shift-left value: preventing new secrets from entering history. It also avoids turning the scanner into an all-or-nothing migration project. The key is that the baseline must be owned and reviewed, not used as a permanent hiding place for unresolved risk.

</details>

### Question 3

A developer removes a hardcoded API token in a follow-up commit and argues that the problem is solved because the current file no longer contains the secret. The original commit was already pushed to the shared repository. What should the team do next, and why is deletion alone insufficient?

<details>
<summary>Show answer</summary>

The team should treat the token as compromised, rotate or revoke it, inspect relevant access logs, and decide whether history rewriting is necessary for the repository. Deleting the value in a later commit only changes the current file state. The token remains visible through Git history, clones, caches, forks, and any systems that already fetched the repository.

This scenario is exactly why pre-commit secret scanning is valuable. If the token is blocked before commit, no history cleanup is needed. Once pushed, the response becomes an incident-handling problem rather than a simple code cleanup.

</details>

### Question 4

A Semgrep rule blocks `container.innerHTML = value` in a frontend project. One team claims the pattern is safe in their file because `value` is produced by a trusted sanitizer wrapper. Another team wants to disable the rule globally because the warning is annoying. What is the best engineering response?

<details>
<summary>Show answer</summary>

The team should avoid disabling the rule globally. They should verify whether the sanitizer wrapper is actually safe, then use a narrow suppression or rule refinement for the specific trusted pattern if the risk is accepted. The suppression should explain why the exception is safe, who owns it, and when it should be reviewed.

Global disablement would hide real XSS risks in other files. A targeted exception preserves the useful signal while acknowledging the known safe case. If many safe cases exist, the rule should be improved to recognize the team's approved wrapper rather than forcing repeated suppressions.

</details>

### Question 5

A Helm chart passes local YAML scanning in pre-commit, but the production release enables `hostNetwork: true` through an environment-specific values file. The risky rendered manifest was never scanned before deployment. Where did the shift-left design fail, and what should be added?

<details>
<summary>Show answer</summary>

The design failed by scanning only raw source templates and never scanning the deployable rendered output. Local pre-commit scanning is useful for obvious mistakes in chart templates, but Helm values can change the final manifest. CI should render the chart with representative environment values and scan the resulting Kubernetes YAML before deployment.

The team may keep the local scanner for fast feedback, but it should be paired with a CI check that validates what the cluster will actually receive. This layered approach catches both simple authoring mistakes and environment-specific configuration risk.

</details>

### Question 6

A security hook flags a realistic-looking payment token inside a parser test fixture. The value is fake, but it causes repeated confusion and blocks commits from developers who are not working on the parser. What should the team change first?

<details>
<summary>Show answer</summary>

The first improvement should be to make the fixture obviously fake if the parser test does not require a realistic provider token format. A value like `not-a-real-token-used-only-in-tests` is clearer to both humans and scanners than a string that resembles a live production credential. If the test truly requires a realistic shape, use a narrow allowlist or baseline entry tied to that exact fixture path.

The team should not add a broad suppression for payment tokens across the repository. Broad suppressions solve the immediate annoyance by hiding future real leaks. The better fix reduces ambiguity while preserving scanner coverage.

</details>

### Question 7

A team wants to measure whether shift-left security is working. Leadership asks for a monthly count of scanner findings. Why is that metric incomplete, and which additional measures would better show program health?

<details>
<summary>Show answer</summary>

A raw finding count is incomplete because it does not show whether issues are being found earlier, fixed faster, or prevented from reaching production. A higher local finding count may actually be good if it means problems moved from CI or production into IDE and pre-commit feedback. Without stage context, leadership may misread healthy early discovery as failure.

Better measures include discovery stage distribution, mean time to remediation by stage, pre-commit runtime, bypass rate, false-positive or accepted-risk rate, and escaped issues found in CI, deployment, or production. Together, those metrics show whether feedback is timely, trusted, and reducing real risk.

</details>

---

## Hands-On Exercise: Build and Debug a Shift-Left Security Guardrail

In this exercise, the learner will create a small local repository, configure pre-commit security checks, trigger failures, fix real findings, and diagnose a noisy hook. The exercise mirrors the worked example: build the guardrail, observe failure, separate real risk from configuration problems, and add a central-style command that can run in CI.

Run the commands from the KubeDojo repository root so `.venv/bin/python` and `.venv/bin/pip` refer to the existing local environment. The demo repository is created under `tmp/shift-left-demo` and can be deleted after the exercise.

### Part 1: Create a Demo Repository

```bash
mkdir -p tmp
rm -rf tmp/shift-left-demo
mkdir tmp/shift-left-demo
cd tmp/shift-left-demo
git init
git config user.email "learner@example.com"
git config user.name "KubeDojo Learner"
```

Create a small application file, a test fixture, and a documentation file so the repository has multiple file types. This setup makes it possible to test whether hooks are scoped correctly.

```bash
mkdir -p app tests/fixtures docs

cat > app/users.py << 'EOF'
import sqlite3

def find_user(connection: sqlite3.Connection, user_id: str):
    query = "SELECT id, email FROM users WHERE id = " + user_id
    return connection.execute(query).fetchone()
EOF

cat > tests/fixtures/payment_gateway.json << 'EOF'
{
  "provider": "example-payments",
  "apiKey": "not-a-real-token-used-only-in-tests"
}
EOF

cat > docs/notes.md << 'EOF'
# Demo Notes

This file should not trigger Python SAST checks when only documentation changes.
EOF
```

### Part 2: Install and Configure Pre-Commit

Return to the KubeDojo root in a second terminal if needed, then install the required tools into the repository virtual environment. The commands below use relative paths from the demo repository to the root virtual environment.

```bash
../../.venv/bin/python -m pip install pre-commit detect-secrets semgrep bandit
../../.venv/bin/pre-commit --version
../../.venv/bin/semgrep --version
```

Create a focused `.pre-commit-config.yaml`. The Semgrep hook is deliberately scoped to Python files so documentation-only commits do not trigger it.

```bash
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]

  - repo: https://github.com/semgrep/pre-commit
    rev: v1.118.0
    hooks:
      - id: semgrep
        args: ["--config", ".semgrep.yaml", "--error"]
        files: "\\.py$"
EOF
```

Create a small Semgrep rule that catches the insecure query pattern from the demo application. This rule is intentionally narrow so the exercise stays focused on diagnosing placement and behavior.

```bash
cat > .semgrep.yaml << 'EOF'
rules:
  - id: python-sql-string-concat-demo
    languages:
      - python
    severity: ERROR
    message: "Use parameterized queries instead of concatenating SQL strings."
    patterns:
      - pattern: $CONN.execute("..." + $INPUT)
EOF
```

Create an initial secrets baseline and install the hooks.

```bash
../../.venv/bin/detect-secrets scan > .secrets.baseline
../../.venv/bin/pre-commit install
```

### Part 3: Trigger and Diagnose a Real SAST Failure

Stage the repository and try to commit. The commit should fail because `app/users.py` builds SQL with string concatenation.

```bash
git add .
git commit -m "Add initial demo app"
```

Inspect the failure and identify whether it is a real finding, a false positive, or a configuration problem. In this case, the finding is real because untrusted input can alter the SQL query structure.

Fix the function by using a parameterized query.

```bash
cat > app/users.py << 'EOF'
import sqlite3

def find_user(connection: sqlite3.Connection, user_id: str):
    query = "SELECT id, email FROM users WHERE id = ?"
    return connection.execute(query, (user_id,)).fetchone()
EOF
```

Run the checks again and commit the safe version.

```bash
git add .
../../.venv/bin/pre-commit run --all-files
git commit -m "Add initial demo app with local security hooks"
```

### Part 4: Prove the Hook Is Properly Scoped

Change only the documentation file and run the hook. The Semgrep hook should not spend time analyzing Python if no Python files are staged, because the hook is filtered to `\\.py$`.

```bash
cat >> docs/notes.md << 'EOF'

A documentation-only change should keep local feedback fast.
EOF

git add docs/notes.md
git commit -m "Update demo notes"
```

If Semgrep runs for this documentation-only commit, inspect `.pre-commit-config.yaml` and verify the `files` filter is attached to the Semgrep hook rather than placed at the wrong indentation level.

### Part 5: Trigger and Fix a Secret Finding

Add a file that contains an obvious fake credential pattern. The point is to observe how the hook stops the commit before the value becomes part of Git history.

```bash
cat > app/insecure_settings.py << 'EOF'
DATABASE_PASSWORD = "plain-text-password-for-demo"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
EOF

git add app/insecure_settings.py
git commit -m "Add insecure settings"
```

The commit should fail. Fix the file by reading values from the environment instead of embedding them.

```bash
cat > app/insecure_settings.py << 'EOF'
import os

DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
EOF

git add app/insecure_settings.py
git commit -m "Add environment-based settings"
```

### Part 6: Add a CI-Equivalent Local Command

Create a script that runs the same checks against all files. This models what a pull request job should do centrally, even when a developer skips a local hook.

```bash
mkdir -p scripts

cat > scripts/security-check.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

../../.venv/bin/pre-commit run --all-files
EOF

chmod +x scripts/security-check.sh
./scripts/security-check.sh
```

A real CI workflow would install tools in the runner environment and run the same pre-commit configuration. The exact installation commands may differ, but the rule set should stay aligned with local development so developers can reproduce failures before pushing.

### Part 7: Explain the Design

Write a short note in the demo repository explaining which checks run early and which should stay in CI. This step forces the design reasoning, not just the tool commands.

```bash
cat > docs/security-design.md << 'EOF'
# Shift-Left Demo Design

Secrets detection runs in pre-commit because leaked values should be blocked before they enter Git history.

The Semgrep demo rule runs in pre-commit only for Python files because documentation-only changes should not trigger Python analysis.

The scripts/security-check.sh command runs all configured hooks and represents the kind of command a CI job should execute before merge.

Slower checks such as full dependency audits, container image scans, and rendered IaC policy checks should run in CI rather than blocking every local commit.
EOF

git add docs/security-design.md scripts/security-check.sh
git commit -m "Document shift-left security design"
```

### Success Criteria

- [ ] A local demo repository exists under `tmp/shift-left-demo` with committed pre-commit configuration.
- [ ] The first insecure SQL implementation fails before commit and is fixed with a parameterized query.
- [ ] A documentation-only change commits without triggering irrelevant Python SAST work.
- [ ] A hardcoded credential pattern is blocked before it enters Git history.
- [ ] The credential example is fixed by reading values from the environment.
- [ ] A local `scripts/security-check.sh` command runs all hooks and models CI enforcement.
- [ ] The design note explains why some checks belong in pre-commit and slower checks belong in CI.
- [ ] The learner can explain whether a hook failure is a real finding, a false positive, a scoping problem, or an enforcement gap.

---

## Next Module

Continue to [Module 4.3: Security in CI/CD Pipelines](../module-4.3-security-cicd/) to design the central verification layer that complements local shift-left security.
