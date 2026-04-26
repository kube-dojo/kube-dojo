---
title: "Module 11.3: GitHub Advanced - Beyond Basic Git Hosting"
slug: platform/toolkits/cicd-delivery/source-control/module-11.3-github-advanced
sidebar:
  order: 4
---

## Complexity: [COMPLEX]
## Time to Complete: 50-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:

- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/) - Security scanning concepts
- [GitOps Discipline](/platform/disciplines/delivery-automation/gitops/) - Git-centric workflows
- Basic GitHub experience with repositories, pull requests, issues, branch protection, and Actions
- Understanding of CI/CD fundamentals, including build jobs, deployment credentials, and artifact promotion

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a GitHub platform control plane that connects repository governance, Actions, security scanning, and identity controls into one delivery workflow.
- **Evaluate** when to use reusable workflows, composite actions, hosted runners, self-hosted runner scale sets, and OIDC-based cloud access.
- **Debug** common GitHub Advanced Security findings across CodeQL, secret scanning, dependency review, and Dependabot alerts.
- **Configure** a secure pull request path that combines rulesets, required security checks, least-privilege workflow permissions, and audit visibility.
- **Compare** GitHub-native controls with third-party security tools and justify which capability should own each part of the software supply chain.

---

## Why This Module Matters

The platform team at a growing payments company thought GitHub was already under control because every service used pull requests, every repository had a `main` branch, and every deployment passed through GitHub Actions. The problem appeared during a pre-acquisition review, when the buyer's security team asked a simple question: "Show us how a vulnerable dependency, leaked cloud key, risky workflow change, and unreviewed production deployment would be stopped before release." The team could show separate tools, but they could not show a coherent control path.

One service used CodeQL, another used a third-party scanner, several repositories had no dependency review, and deployment workflows still used long-lived cloud credentials stored as repository secrets. Some repositories had branch protection, others had newer rulesets, and a few critical Actions workflows could be changed by any maintainer without code owner approval. None of these gaps looked catastrophic on its own, but together they meant the organization had a Git host with pockets of automation, not a governed delivery platform.

GitHub becomes powerful when you stop treating its features as independent checkboxes. CodeQL, secret scanning, dependency review, Dependabot, Actions, OIDC, rulesets, Copilot governance, audit logs, and enterprise identity controls form a chain. A platform engineer's job is to make that chain predictable: developers should get fast feedback, security teams should get actionable signals, and production credentials should never depend on someone copying a static key into a repository setting.

This module teaches GitHub Advanced from that platform perspective. You will start with the basic control loop of a pull request, add security checks, replace static deployment credentials with OIDC, scale workflows with reusable patterns and Kubernetes-backed runners, then place enterprise controls around the whole system. The goal is not to memorize GitHub features. The goal is to design a delivery system where GitHub is the front door for code, policy, evidence, and release trust.

---

## 1. The GitHub Platform Control Loop

A mature GitHub setup begins with a simple question: what must be true before code reaches production? The answer usually includes review, tests, security scans, dependency checks, secret prevention, artifact creation, and approved deployment identity. If those checks live in disconnected tools, developers experience them as random friction. If they are integrated into the pull request and workflow path, they become a delivery control loop.

The basic loop is straightforward. A developer opens a pull request, GitHub Actions runs build and test workflows, GitHub Advanced Security evaluates the code and dependencies, repository rulesets decide whether the change can merge, and deployment workflows request short-lived cloud credentials using OIDC. Enterprise identity and audit controls sit around that loop so the organization can prove who changed what, which policies applied, and which credentials were issued.

```text
GITHUB PLATFORM CONTROL LOOP
────────────────────────────────────────────────────────────────────────────

┌──────────────┐     ┌────────────────┐     ┌────────────────────────────┐
│ Developer    │────▶│ Pull Request   │────▶│ Required Checks            │
│ pushes code  │     │ review path    │     │ tests, CodeQL, dependencies│
└──────────────┘     └───────┬────────┘     └──────────────┬─────────────┘
                             │                              │
                             ▼                              ▼
                    ┌────────────────┐             ┌──────────────────────┐
                    │ Repository     │             │ Actions Workflow     │
                    │ ruleset        │             │ build and deploy     │
                    └───────┬────────┘             └──────────┬───────────┘
                            │                                  │
                            ▼                                  ▼
                    ┌────────────────┐             ┌──────────────────────┐
                    │ Merge allowed  │             │ OIDC cloud token     │
                    │ only if policy │             │ short-lived access   │
                    │ is satisfied   │             │ no stored cloud keys │
                    └────────────────┘             └──────────────────────┘

SURROUNDING CONTROLS
────────────────────────────────────────────────────────────────────────────
Enterprise SSO and SCIM  │  audit log streaming  │  IP allow lists
Copilot governance       │  secret scanning      │  security overview
```

This loop matters because each GitHub service answers a different governance question. Rulesets answer "may this code merge?" CodeQL answers "does this code introduce a known risky pattern?" Secret scanning answers "did a credential enter the repository path?" Dependency review answers "does this pull request add a vulnerable or disallowed dependency?" OIDC answers "can this workflow prove its identity without a stored secret?" Audit logs answer "can we reconstruct the change later?"

A common beginner mistake is enabling many features without deciding which decision each feature owns. That creates duplicate warnings, ignored alerts, and exceptions nobody can explain. A senior platform engineer starts by mapping each control to one decision point, then makes the decision visible in the developer workflow. If a high-severity dependency should block merge, dependency review must be a required check. If CodeQL is advisory for legacy code but blocking for new code, that policy should be explicit rather than implied by alert backlog.

> **Pause and predict:** If CodeQL finds a high-severity alert after a pull request has already merged, which control failed: CodeQL, the ruleset, the workflow trigger, or the team's alert triage process? Write down your answer before continuing, because the distinction determines whether you fix scanner configuration, merge policy, or operational ownership.

The best answer is usually "it depends on the intended control." If CodeQL was supposed to block risky new code, then the workflow and ruleset failed to enforce the result before merge. If CodeQL was intentionally advisory because the team is still burning down existing findings, then alert triage ownership failed only if nobody reviewed the alert within the expected service-level objective. The same technical finding can represent different governance failures depending on the policy design.

---

## 2. GitHub Advanced Security as Pull Request Feedback

GitHub Advanced Security is most useful when learners think of it as feedback in the change path rather than as a dashboard someone checks later. Code scanning, secret scanning, dependency review, and security overview are related, but they operate at different moments. CodeQL evaluates code behavior, dependency review evaluates package changes, secret scanning watches for exposed credentials, and security overview helps teams prioritize risk across repositories.

```text
GITHUB ADVANCED SECURITY STACK
────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│                        GITHUB ADVANCED SECURITY                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CODE SCANNING WITH CODEQL                                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Builds a semantic database of code, then queries it for risky flows │  │
│  │ Best for injection paths, unsafe APIs, data-flow issues, and custom │  │
│  │ organization-specific security patterns                            │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  SECRET SCANNING AND PUSH PROTECTION                                     │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Detects known secret patterns, custom patterns, and supported       │  │
│  │ partner tokens; push protection can stop secrets before they enter  │  │
│  │ repository history                                                 │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  DEPENDENCY REVIEW AND DEPENDABOT ALERTS                                 │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Reviews pull request dependency changes, vulnerability severity,    │  │
│  │ license policy, and package risk before the dependency becomes part │  │
│  │ of the default branch                                              │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  SECURITY OVERVIEW                                                       │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Aggregates repository security posture so platform and security     │  │
│  │ teams can prioritize teams, repos, and alert categories             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

CodeQL is different from a simple pattern scanner because it models code as data. For many languages, CodeQL builds a database that represents syntax, control flow, and data flow. A query can then ask whether user-controlled input reaches a dangerous sink without sanitization. That is why CodeQL can find issues such as SQL injection and cross-site scripting more precisely than a search for suspicious strings.

A minimal CodeQL workflow should run on pull requests, pushes to the default branch, and a schedule. Pull request runs catch newly introduced problems, default branch runs maintain the main security signal, and scheduled runs catch improvements from updated queries even when code has not changed. Matrix jobs let one workflow handle multiple languages, but you should only include languages that actually exist in the repository; a noisy scanner loses trust quickly.

```yaml
# .github/workflows/codeql.yml
name: CodeQL Analysis

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'

permissions:
  contents: read
  security-events: write

jobs:
  analyze:
    name: Analyze ${{ matrix.language }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language: ['javascript-typescript', 'python']

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended,security-and-quality

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

Secret scanning works differently because credentials are dangerous even if the application code is perfect. The important design choice is prevention versus detection. Detection tells you that a secret appeared somewhere in history or in a commit. Push protection tries to stop supported secrets during push, before they become part of the remote repository. For private internal token formats, custom patterns extend coverage beyond public provider formats.

```text
SECRET SCANNING DECISION FLOW
────────────────────────────────────────────────────────────────────────────

Developer pushes commits
        │
        ▼
┌──────────────────────────────┐
│ GitHub checks supported and  │
│ custom secret patterns       │
└──────────────┬───────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
No secret found    Secret detected
      │                 │
      ▼                 ▼
Push accepted      Push blocked or alert created
                        │
                        ▼
              Developer removes secret,
              rotates credential if needed,
              or requests audited bypass
```

> **Stop and think:** A developer commits an AWS key, notices immediately, deletes the line in the next commit, and pushes both commits together. Should the organization still rotate the key? Explain why before reading the next paragraph.

The key should be rotated because Git history is the exposure boundary, not the final file contents. If the secret reached a commit that was pushed, cloned, logged, mirrored, or scanned by another system, deletion from a later commit does not prove the credential stayed private. A strong GitHub security program therefore treats secret response as three steps: remove the secret from code, rotate or revoke the credential, and investigate whether the credential was used.

Dependency review closes another common gap. Dependabot alerts tell you about vulnerable dependencies already present in the repository, while dependency review evaluates what a pull request is adding or changing. That distinction matters during review. If a pull request upgrades a package but also introduces a restrictive license or a new high-severity vulnerability, the reviewer should see that risk before it merges.

```yaml
# .github/workflows/dependency-review.yml
name: Dependency Review

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Review dependency changes
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: GPL-3.0, AGPL-3.0
          allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC
          comment-summary-in-pr: always
```

The platform design principle is simple: security feedback belongs as close as possible to the change that introduced the risk. A repository-wide backlog view is useful for prioritization, but it is a weak teaching surface for developers. Pull request comments, required checks, and clear bypass rules help teams learn the policy while they are still editing the change.

---

## 3. Worked Example: Turning a Risky Service into a Governed Repository

Before building your own secure GitHub pipeline, study a complete example. The scenario is a Node.js service that currently has tests but no security checks, uses repository secrets for cloud deployment, and has branch protection that only requires one approval. The platform team wants to prevent three risks: obvious code vulnerabilities, vulnerable dependencies, and static cloud credentials in CI/CD.

First, create a small repository layout. This example is intentionally compact so you can see the control design instead of getting lost in application details. The code includes an unsafe query construction pattern and an unescaped response so CodeQL has realistic behavior to analyze. In a real service, the fix would be parameterized queries and output encoding; here the goal is to show how the platform catches risk before merge.

```bash
mkdir github-advanced-worked-example
cd github-advanced-worked-example
git init

npm init -y
npm install express lodash@4.17.20

cat > index.js <<'EOF'
const express = require('express');

const app = express();

app.get('/user', (req, res) => {
  const query = `SELECT * FROM users WHERE id = ${req.query.id}`;
  res.send({ query });
});

app.get('/search', (req, res) => {
  res.send(`<h1>Results for ${req.query.q}</h1>`);
});

app.listen(3000, () => {
  console.log('demo service listening on port 3000');
});
EOF

git add package.json package-lock.json index.js
git commit -m "Create demo service"
```

Second, add CodeQL and dependency review workflows. Notice that each workflow uses the narrowest permissions it needs. This is not cosmetic. GitHub Actions permissions are part of your supply-chain boundary, because a compromised action or script can only do what the job token allows. Many incidents become worse because every workflow quietly inherited broad write permissions.

```bash
mkdir -p .github/workflows

cat > .github/workflows/codeql.yml <<'EOF'
name: CodeQL Analysis

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript-typescript
          queries: security-extended,security-and-quality

      - name: Perform CodeQL analysis
        uses: github/codeql-action/analyze@v3
EOF

cat > .github/workflows/dependency-review.yml <<'EOF'
name: Dependency Review

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          comment-summary-in-pr: always
EOF

git add .github/workflows
git commit -m "Add security review workflows"
```

Third, replace stored cloud credentials with an OIDC deployment pattern. OIDC lets GitHub Actions ask a cloud provider for a short-lived token based on the workflow identity, branch, environment, repository, and other claims. The cloud provider decides whether that identity is allowed to assume a role. That means there is no long-lived AWS, Azure, or Google Cloud key sitting in GitHub secrets waiting to leak.

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Configure AWS credentials with OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-advanced-demo-prod
          aws-region: us-east-1

      - name: Verify caller identity
        run: aws sts get-caller-identity
```

Fourth, protect the merge path with a ruleset. The exact UI or API fields may change over time, but the design is stable: require pull requests, require status checks, require code owner review for sensitive paths, and include the security workflows in the required check set. The key is that checks become policy only when merge depends on them. A workflow that fails after merge is monitoring; a workflow that blocks merge is governance.

```json
{
  "name": "Production branch rules",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
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
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          {"context": "CodeQL Analysis"},
          {"context": "Dependency Review"}
        ]
      }
    }
  ]
}
```

Finally, test the result by opening a pull request that changes application code and dependency metadata. In a healthy setup, the pull request becomes the shared workspace where the developer, reviewer, and platform controls meet. The reviewer should not need to remember a separate security dashboard for every change. The evidence should be visible where the decision happens.

The worked example teaches the sequence you will reuse in the exercise: start with a risk, attach the right GitHub control to the right decision point, reduce workflow permissions, replace static credentials with OIDC, and make the result enforceable through rulesets. Senior platform work is rarely about enabling one feature. It is about connecting the feature to the correct operational decision.

---

## 4. GitHub Actions at Scale

Actions starts as a convenient CI system and becomes a platform concern when dozens or hundreds of repositories copy workflow files. At small scale, duplication is tolerable because each repository can move quickly. At platform scale, duplication becomes a control problem: security fixes must be repeated, caching mistakes spread, deployment permissions drift, and every team reinvents the same build logic.

There are three reuse tools to understand. Reusable workflows package whole jobs and can own their own runner selection, permissions, secrets contract, and deployment gates. Composite actions package repeated steps inside a job, such as setting up a language runtime or installing common tools. YAML anchors and local conventions can reduce repetition, but they do not create a centrally governable interface the way reusable workflows do.

| Reuse Pattern | Best Use | Governance Trade-Off |
|---------------|----------|----------------------|
| Reusable workflow | Standard CI, security scan, release, deployment, policy-heavy jobs | Strong interface with inputs, secrets, jobs, and permissions, but changes affect many repositories |
| Composite action | Shared step sequence such as setup, lint helper, artifact packaging | Easy to reuse inside jobs, but inherits caller job permissions and runner context |
| Local workflow copy | Highly specific repository logic | Simple for one team, but poor central control and high maintenance cost |
| Starter workflow | Initial scaffolding for new repositories | Good bootstrap experience, but not automatically updated after creation |

A reusable workflow is the right abstraction when the platform team wants to own a complete process. The caller should provide inputs, not copy the implementation. For example, a shared Node.js CI workflow can standardize checkout, runtime version, dependency install, build, test, artifact upload, and security scan behavior. The consuming repository only declares what varies.

```yaml
# .github/workflows/reusable-node-ci.yml in a shared workflow repository
name: Reusable Node CI

on:
  workflow_call:
    inputs:
      node-version:
        required: false
        type: string
        default: '22'
      run-e2e:
        required: false
        type: boolean
        default: false
    secrets:
      NPM_TOKEN:
        required: false

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: npm

      - name: Install dependencies
        run: npm ci
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Build
        run: npm run build

      - name: Test
        run: npm test

      - name: Run end-to-end tests
        if: ${{ inputs.run-e2e }}
        run: npm run test:e2e
```

```yaml
# .github/workflows/ci.yml in an application repository
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  call-platform-ci:
    uses: my-org/platform-workflows/.github/workflows/reusable-node-ci.yml@v1
    with:
      node-version: '22'
      run-e2e: ${{ github.ref == 'refs/heads/main' }}
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Composite actions are better when the platform team wants to standardize a repeated step sequence without owning the job boundary. They run in the caller's job context, so they are not a security boundary. That can be useful for setup actions, but risky if teams assume the composite action limits permissions. The caller still controls the job token, runner, and surrounding steps.

```yaml
# .github/actions/setup-project/action.yml
name: Setup Project
description: Common setup steps for Node.js projects

inputs:
  node-version:
    description: Node.js version
    required: false
    default: '22'

runs:
  using: composite
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: npm

    - name: Install dependencies
      shell: bash
      run: npm ci

    - name: Export test environment
      shell: bash
      run: |
        echo "NODE_ENV=test" >> "$GITHUB_ENV"
        echo "CI=true" >> "$GITHUB_ENV"
```

Caching is another scale concern because bad caches create either slow pipelines or misleading builds. Cache dependency downloads by lockfile hash, not by branch name alone. Cache build outputs only when the build system supports safe incremental reuse. For Docker builds, use Buildx cache support rather than trying to save arbitrary layer directories yourself.

```yaml
name: Build With Cache

on:
  pull_request:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js with npm cache
        uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build image with GitHub Actions cache
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          tags: example/app:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> **Pause and predict:** A team places `node_modules` itself in a cache key that only uses the operating system name. After a dependency upgrade, tests still pass in CI but fail in a fresh clone. What is the likely failure mechanism, and what should the cache key include?

The likely failure is cache poisoning by staleness. The workflow reused a dependency directory that no longer matches `package-lock.json`, so CI tested a different dependency graph than a fresh install would produce. A better strategy is to use `actions/setup-node` with npm cache support or key the cache by a lockfile hash. The lockfile is the contract; the cache should accelerate that contract, not replace it.

---

## 5. Runners, OIDC, and Deployment Trust

The runner is where your workflow code actually executes, so runner strategy is part of your threat model. GitHub-hosted runners are convenient and isolated for many workloads. Self-hosted runners are useful when jobs need private network access, specialized hardware, large caches, custom tooling, or data locality. The trade-off is that self-hosted runners move security responsibility back to your organization.

```text
RUNNER STRATEGY DECISION MAP
────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────┐
│ Does the job need private    │
│ network access or special    │
│ hardware?                    │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
      No               Yes
       │                │
       ▼                ▼
┌──────────────┐  ┌─────────────────────────────┐
│ GitHub-hosted│  │ Self-hosted runner strategy │
│ runner       │  │ with isolation controls     │
└──────────────┘  └─────────────┬───────────────┘
                                │
                                ▼
                  ┌─────────────────────────────┐
                  │ Prefer ephemeral runners,   │
                  │ runner groups, least        │
                  │ privilege, and network      │
                  │ segmentation                │
                  └─────────────────────────────┘
```

Actions Runner Controller, now commonly discussed through runner scale sets, is GitHub's Kubernetes-oriented path for running self-hosted runners at scale. The key idea is to create homogeneous groups of runners that autoscale based on workflow demand. A platform team can place those runners in restricted namespaces, apply network policies, use ephemeral runner pods, and separate high-risk workloads from trusted release jobs.

A modern runner scale set is different from treating a long-lived virtual machine as a shared build box. Long-lived runners accumulate credentials, caches, workspaces, and tools from previous jobs. Ephemeral runners reduce that risk because each job starts from a cleaner environment and disappears afterward. For sensitive workloads, the platform should also restrict which repositories can use which runner groups.

```yaml
# Example workflow targeting a runner scale set by name
name: Build On Platform Runner

on:
  pull_request:

permissions:
  contents: read

jobs:
  build:
    runs-on: platform-linux-build
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Run build
        run: |
          npm ci
          npm test
```

OIDC solves a separate but related problem: deployment identity. Without OIDC, teams often store cloud keys as GitHub secrets. Those keys may live for months, be copied across repositories, and become valuable if leaked through logs, compromised workflows, or overly broad repository access. With OIDC, the workflow asks GitHub for an identity token, and the cloud provider exchanges it for short-lived credentials only if claims match the trust policy.

```text
OIDC DEPLOYMENT TRUST FLOW
────────────────────────────────────────────────────────────────────────────

┌──────────────────────┐
│ GitHub Actions job   │
│ repo, branch, env    │
└──────────┬───────────┘
           │ requests OIDC token
           ▼
┌──────────────────────┐
│ GitHub OIDC provider │
│ signs identity token │
└──────────┬───────────┘
           │ token includes claims
           ▼
┌──────────────────────┐
│ Cloud identity trust │
│ policy validates repo│
│ branch and audience  │
└──────────┬───────────┘
           │ if allowed
           ▼
┌──────────────────────┐
│ Short-lived role     │
│ credentials issued   │
└──────────────────────┘
```

The strongest OIDC policies are specific. Trusting any workflow from any repository in an organization is much weaker than trusting one repository, one branch, one environment, and one audience. If a production deployment requires GitHub Environments with reviewers, the OIDC trust policy should align with that environment. That way, cloud access depends on both GitHub workflow identity and release approval policy.

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
    },
    "StringLike": {
      "token.actions.githubusercontent.com:sub": "repo:my-org/payments-api:environment:production"
    }
  }
}
```

Runner isolation and OIDC reinforce each other. Ephemeral runners reduce the chance that one job steals another job's residue, while OIDC reduces the value of any credential that a job can access. Together, they move the platform away from "protect this secret forever" and toward "issue narrow access only when this approved workflow is running."

---

## 6. Enterprise Governance: Identity, Rulesets, Audit, and Copilot

Enterprise GitHub governance begins with identity. SAML SSO centralizes authentication, SCIM automates user lifecycle, and Enterprise Managed Users go further by making GitHub accounts controlled by the identity provider. These controls matter because repository policy is only as strong as the account lifecycle behind it. If departing employees retain access, or if personal accounts become the route into production code, technical branch rules cannot compensate.

```text
ENTERPRISE IDENTITY ARCHITECTURE
────────────────────────────────────────────────────────────────────────────

┌──────────────────────┐        SAML SSO        ┌─────────────────────────┐
│ Identity Provider    │◀──────────────────────▶│ GitHub Enterprise       │
│ Okta, Entra ID, etc. │                         │ organizations and repos │
└──────────┬───────────┘                         └──────────┬──────────────┘
           │                                                │
           │ SCIM provisioning                              │ team and role mapping
           ▼                                                ▼
┌──────────────────────┐                         ┌─────────────────────────┐
│ User lifecycle       │                         │ Repository permissions  │
│ create, update,      │                         │ teams, roles, rulesets  │
│ suspend, remove      │                         │ and audit trail         │
└──────────────────────┘                         └─────────────────────────┘

ENTERPRISE MANAGED USERS
────────────────────────────────────────────────────────────────────────────
Managed identities are created and controlled by the enterprise identity
system. They are useful when the organization requires centralized lifecycle
control and does not want personal GitHub accounts to own enterprise access.
```

Rulesets are the modern place to express repository and organization policy. Branch protection is still widely used, but rulesets provide a more flexible model for applying rules across branches, tags, and repositories. The important learning point is not the UI location. The important point is that rulesets translate governance intent into merge behavior.

A strong production ruleset usually requires pull requests, code owner review for sensitive files, required status checks, signed commits where appropriate, and restrictions on force pushes and deletions. For platform-owned workflows, require review on workflow file changes too. A pull request that changes `.github/workflows/deploy.yml` can change the deployment path, so it deserves the same scrutiny as application code that handles payments or user data.

```yaml
# Example CODEOWNERS entries for platform-sensitive paths
.github/workflows/* @my-org/platform-engineering
.github/actions/* @my-org/platform-engineering
infra/** @my-org/platform-engineering @my-org/cloud-security
src/payments/** @my-org/payments-team @my-org/security-reviewers
```

Audit log streaming closes the investigation gap. GitHub's web audit log is useful for interactive review, but platform teams usually need events in a SIEM or data platform where they can correlate GitHub activity with cloud access, identity events, and incident timelines. When a production deployment behaves strangely, you want to answer who changed the workflow, who approved the environment, which runner executed the job, and which cloud role was issued.

```bash
# Query recent repository creation audit events.
# Replace the enterprise slug and token before running.
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/enterprises/my-enterprise/audit-log?phrase=action:repo.create"
```

IP allow lists can reduce exposure for organizations with predictable network boundaries, but they must be designed carefully. Developers, automation, GitHub Apps, runners, and integrations may all need access paths. A strict allow list without runner planning can break deployments or force teams into exceptions. Treat IP restrictions as one layer, not as a substitute for identity, repository policy, and workflow permissions.

Copilot governance belongs in this enterprise picture because AI assistance changes how code is produced and reviewed. Copilot can improve developer flow, explain unfamiliar code, and help generate tests, but it should not be allowed to blur sensitive boundaries. Organizations with Copilot Business or Enterprise can configure policies such as content exclusions for sensitive files, public code suggestion settings, and seat management. Learners should treat Copilot as a developer tool that needs guardrails, not as an autonomous reviewer.

```text
COPILOT GOVERNANCE MODEL
────────────────────────────────────────────────────────────────────────────

┌──────────────────────┐
│ Developer experience │
│ completion, chat,    │
│ explanations, tests  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Organization policy  │
│ seats, content       │
│ exclusions, public   │
│ code controls        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Review discipline    │
│ tests, security      │
│ scans, human review  │
│ and ownership        │
└──────────────────────┘
```

The senior stance is balanced. Copilot output should be reviewed like any other code, and security scanners should be treated as helpful signals rather than proof of correctness. The platform's job is to create a system where AI assistance, automated checks, and human review complement each other. None of them should become the only control.

---

## 7. Choosing GitHub-Native Controls and Third-Party Tools

GitHub-native controls are attractive because they meet developers inside the pull request path. That does not mean they replace every specialized tool. A platform team should decide what needs native enforcement, what needs deep specialist analysis, and what needs cross-platform coverage. The right answer depends on where the organization hosts code, how regulated the environment is, and which team owns each risk.

```text
GITHUB ADVANCED SECURITY vs ALTERNATIVES
────────────────────────────────────────────────────────────────────────────

                    GHAS        Snyk        SonarQube    Semgrep
────────────────────────────────────────────────────────────────────────────
SECRET SCANNING
Patterns            Varies by product and current rule set; verify exact
                    coverage in each vendor's latest documentation
Push protection     Secret-prevention approaches differ by platform; verify
                    current capabilities directly in vendor docs
Partner revocation  Provider-notification and revocation workflows vary by
                    platform and provider integration
Custom patterns     Yes         Yes         Yes          Yes

CODE SCANNING
Query language      CodeQL      Proprietary  Java-based  Custom
Languages           Language coverage varies substantially by product and
                    should be checked against current vendor documentation
Custom rules        Yes         Paid plan    Yes          Yes
PR integration      Native      Plugin       Plugin       Native

DEPENDENCY SCANNING
Ecosystem           Native      Strong       Plugin       Limited
Auto-fix            Dependabot  Available    Limited      Limited
License check       Available   Available    Available    Limited

BEST FIT
────────────────────────────────────────────────────────────────────────────
GHAS        Already on GitHub, want native pull request and alert workflow
Snyk        Strong dependency and container focus across several platforms
SonarQube   Combined quality and security with self-hosting preference
Semgrep     Fast custom rules and organization-specific policy checks
```

| Decision Area | Prefer GitHub-Native When | Consider Third-Party When |
|---------------|---------------------------|---------------------------|
| Pull request blocking | The repository is on GitHub and the control should be visible in the PR | The same policy must apply consistently across GitHub, GitLab, Bitbucket, and local scans |
| Dependency risk | Dependabot and dependency review cover the ecosystem and license policy well enough | You need deeper package reputation, reachability analysis, container scanning, or custom governance |
| Code scanning | CodeQL supports your languages and queries match your risk model | You need faster custom rules, unsupported languages, or a self-hosted analyzer |
| Secrets | Push protection and partner detection cover common leaks | You need broad history scanning across many systems or specialized internal token detection |
| Reporting | GitHub Security Overview satisfies repository-level prioritization | Compliance requires a centralized risk platform across code, cloud, tickets, and runtime |

The decision is not binary. Many strong programs use GitHub-native controls for first-line pull request enforcement and third-party tools for deeper analysis, centralized reporting, or coverage outside GitHub. The risk is overlap without ownership. If two tools report the same dependency vulnerability and nobody knows which one blocks merge, developers will learn to ignore both.

A good platform team publishes a control ownership map. It says which tool blocks merge, which tool opens remediation issues, which tool owns compliance reporting, which findings are advisory, and who approves exceptions. That map turns a pile of integrations into an operating model.

---

## Did You Know?

- **CodeQL came from Semmle's semantic analysis work**: GitHub acquired Semmle in 2019, bringing a query-based approach that lets security researchers express vulnerability patterns against a database representation of code rather than relying only on text matching.

- **Secret response is about credential lifetime, not file contents**: Removing a secret from the latest commit does not undo exposure from Git history, forks, logs, local clones, or mirrors, so serious programs rotate or revoke the credential after exposure.

- **OIDC changes the deployment trust model**: Instead of storing a long-lived cloud key in GitHub, a workflow can request a short-lived token whose claims are validated by the cloud provider against repository, branch, environment, and audience rules.

- **Runner choice is a security decision**: A self-hosted runner can reach networks and tools that GitHub-hosted runners cannot, but that same access makes isolation, runner groups, ephemeral execution, and workflow trust boundaries essential.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---------|--------------|-----------------|
| Enabling GHAS without merge policy | Alerts accumulate after risky code has already merged, so developers experience scanning as delayed criticism rather than actionable feedback | Decide which severities block merge, wire those checks into rulesets, and define alert triage ownership |
| Treating deleted secrets as safe | Git history and external mirrors may still contain the credential, and attackers often scan public events quickly | Remove the secret, rotate or revoke it, investigate usage, and enable push protection |
| Giving every workflow broad token permissions | A compromised action or script can write repository contents, create releases, or tamper with pull requests | Set default workflow permissions to read-only and grant job-level permissions only where needed |
| Copying workflows into every repository | Security fixes and performance improvements must be repeated manually, which causes drift | Use reusable workflows for complete processes and composite actions for shared setup steps |
| Using long-lived cloud keys for deployments | Repository secrets become high-value targets and may be copied across environments | Use OIDC with specific cloud trust policies and environment approval gates |
| Running sensitive jobs on shared long-lived runners | Workspaces, caches, tools, or credentials can leak between jobs or repositories | Prefer ephemeral runners, restricted runner groups, and network segmentation for sensitive workloads |
| Letting Copilot touch sensitive areas without policy | AI suggestions may be generated in contexts that include proprietary or regulated files | Configure content exclusions and keep human review, tests, and security scanning in the path |
| Streaming no audit logs | Incident response depends on manual UI checks and may miss correlated identity or cloud events | Stream audit logs to a SIEM or data platform and retain events according to investigation needs |

---

## Quiz

### Question 1

Your organization enabled CodeQL on every repository, but a high-severity SQL injection alert appears on `main` two days after the pull request merged. The team says "CodeQL worked because it found the issue." As the platform engineer, what do you check first, and how do you decide whether this is a scanner failure or a policy failure?

<details>
<summary>Show Answer</summary>

First check the intended control point. If CodeQL was supposed to block risky new code before merge, verify that the workflow ran on `pull_request`, that it completed successfully before merge, and that the ruleset required the relevant CodeQL status check. In that case, the failure is likely workflow or ruleset enforcement, not the scanner's ability to detect the issue.

If CodeQL was intentionally advisory during a rollout period, then the alert appearing on `main` may be expected, but you must check triage ownership and response time. The senior distinction is that scanners produce signals, while rulesets and operating procedures turn signals into governance.
</details>

### Question 2

A developer accidentally commits a cloud provider key, deletes it in the next commit, and asks for approval to push both commits because the final diff no longer contains the secret. What should the reviewer require before allowing the work to continue, and why?

<details>
<summary>Show Answer</summary>

The reviewer should require the key to be revoked or rotated, the secret to be removed from the commit history or replaced in a clean branch, and the incident to be reviewed for possible use. The final diff is not enough because the secret still existed in a commit and could be exposed through Git history, local clones, logs, or mirrors.

The better long-term control is push protection plus custom secret patterns for internal token formats. If the repository uses deployment credentials, the team should also evaluate whether OIDC can replace long-lived keys.
</details>

### Question 3

A team wants to standardize CI across thirty Node.js repositories. They propose a composite action that checks out code, installs dependencies, runs tests, uploads artifacts, and deploys to staging. What design concern should you raise, and what would you recommend instead?

<details>
<summary>Show Answer</summary>

A composite action is a step collection that runs inside the caller's job context, so it inherits the caller's runner and permissions. That makes it a poor abstraction for a complete governed process that includes job permissions, deployment gates, runner selection, and secrets contracts.

Use a reusable workflow for the full CI or deployment process, and use composite actions only for smaller repeated step sequences such as setting up Node.js or exporting common environment variables. The reusable workflow gives the platform team a stronger interface for inputs, secrets, permissions, and jobs.
</details>

### Question 4

A production deployment workflow uses an AWS access key stored as a repository secret. The team argues that only admins can read repository secrets, so the design is acceptable. How would you evaluate the risk and redesign the workflow?

<details>
<summary>Show Answer</summary>

The risk is not limited to humans reading the secret in the UI. A workflow step, compromised third-party action, malicious workflow change, or overly broad repository access can cause a long-lived key to be used or leaked. Long-lived keys also tend to spread across repositories and become difficult to rotate safely.

Redesign the workflow to use GitHub Actions OIDC with `id-token: write` and a cloud trust policy scoped to the repository, branch or environment, and expected audience. Add environment approvals for production and require review for workflow file changes through CODEOWNERS and rulesets.
</details>

### Question 5

A security team wants dependency review to fail pull requests on all medium vulnerabilities. After two weeks, developers are bypassing the check because many findings are in dev-only packages that do not ship to production. What should the platform team adjust?

<details>
<summary>Show Answer</summary>

The platform team should tune the policy so it reflects actual risk and remains credible. That may mean blocking high and critical vulnerabilities, treating medium findings as warnings, differentiating production and development dependencies where the tool supports it, and defining exception rules for non-exploitable cases.

The important principle is that a required check should be enforceable and trusted. If policy is too noisy, teams learn to bypass it, which is worse than starting with a narrower blocking rule and expanding as ownership improves.
</details>

### Question 6

A regulated company uses SAML SSO but allows engineers to access enterprise repositories through personal GitHub accounts. An auditor asks how access is removed when an employee leaves. What GitHub enterprise controls would you evaluate, and what trade-off should leadership understand?

<details>
<summary>Show Answer</summary>

Evaluate SCIM provisioning for automated lifecycle management and Enterprise Managed Users if the organization requires centrally controlled GitHub identities. SCIM helps create, update, and suspend access based on identity provider state. EMU goes further by using enterprise-managed accounts rather than personal accounts for enterprise work.

The trade-off is user flexibility versus administrative control. EMU can be appropriate for strict lifecycle and compliance requirements, but it changes how users interact with GitHub outside the enterprise and requires careful migration planning.
</details>

### Question 7

A team moves builds to Kubernetes-hosted self-hosted runners because they need private network access. Afterward, a pull request from a less-trusted repository can run on the same runner group used for production releases. What is the platform risk, and how should runner access be redesigned?

<details>
<summary>Show Answer</summary>

The risk is that untrusted or lower-trust workflows can execute in an environment with access intended for production release jobs. If runners are long-lived or share network paths, workspaces, or tools, one job can create exposure for another.

Redesign runner access with separate runner groups, restricted repository access, ephemeral runners, network segmentation, and least-privilege credentials. Production release runners should be reachable only by trusted repositories and approved workflows.
</details>

### Question 8

A team adopts Copilot Enterprise and then asks whether Copilot-generated code can skip normal review because "the AI already checked it." How should you respond as a platform engineer?

<details>
<summary>Show Answer</summary>

Copilot should be treated as an assistant, not as an approval authority. Generated code still needs tests, human review, security scanning, dependency review, and ownership from the team merging it. AI can help write code, summarize changes, or explain unfamiliar functions, but it does not replace accountability for the resulting system behavior.

The platform response should include governance controls such as content exclusions for sensitive files, seat and policy management, and continued enforcement through rulesets and required checks. AI assistance belongs inside the delivery system, not outside its controls.
</details>

---

## Hands-On Exercise

### Task: Build a Governed GitHub Security Pipeline

In this exercise you will create a small repository, add security workflows, design the ruleset that should enforce them, and replace static deployment credentials with an OIDC deployment pattern. You do not need a paid enterprise account to learn the design, but some features may require organization, enterprise, or product-level availability in a real environment. Where your account cannot enable a feature, document the intended configuration and verify the workflow files locally.

### Scenario

You are the platform engineer for `payments-api`, a service that handles customer payment requests. The service currently has unit tests but no code scanning, no dependency review, and a deployment workflow that uses a long-lived cloud access key stored in repository secrets. Your goal is to create a pull request path where risky code, vulnerable dependencies, and unsafe deployment credentials are visible before release.

### Steps

1. Create a demo repository and application.

```bash
mkdir payments-api-ghas-lab
cd payments-api-ghas-lab
git init
npm init -y
npm install express lodash@4.17.20

cat > index.js <<'EOF'
const express = require('express');

const app = express();

app.get('/user', (req, res) => {
  const query = `SELECT * FROM users WHERE id = ${req.query.id}`;
  res.send({ query });
});

app.get('/search', (req, res) => {
  res.send(`<h1>Search result for ${req.query.q}</h1>`);
});

app.listen(3000, () => {
  console.log('payments-api lab listening on port 3000');
});
EOF

git add package.json package-lock.json index.js
git commit -m "Create payments API lab service"
```

2. Add a CodeQL workflow with narrow permissions.

```bash
mkdir -p .github/workflows

cat > .github/workflows/codeql.yml <<'EOF'
name: CodeQL Analysis

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'

permissions:
  contents: read
  security-events: write

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript-typescript
          queries: security-extended,security-and-quality

      - name: Perform CodeQL analysis
        uses: github/codeql-action/analyze@v3
EOF

git add .github/workflows/codeql.yml
git commit -m "Add CodeQL analysis"
```

3. Add dependency review for pull requests.

```bash
cat > .github/workflows/dependency-review.yml <<'EOF'
name: Dependency Review

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: GPL-3.0, AGPL-3.0
          comment-summary-in-pr: always
EOF

git add .github/workflows/dependency-review.yml
git commit -m "Add dependency review"
```

4. Add an OIDC-based deployment workflow skeleton.

```bash
cat > .github/workflows/deploy.yml <<'EOF'
name: Deploy

on:
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Explain OIDC configuration
        run: |
          echo "This workflow is ready for cloud OIDC federation."
          echo "Configure the cloud trust policy for this repository and environment."

      - name: Placeholder deployment
        run: |
          echo "Deploy would run here after cloud federation is configured."
EOF

git add .github/workflows/deploy.yml
git commit -m "Add OIDC deployment workflow skeleton"
```

5. Add CODEOWNERS for workflow and infrastructure paths.

```bash
mkdir -p .github

cat > .github/CODEOWNERS <<'EOF'
.github/workflows/* @my-org/platform-engineering
.github/actions/* @my-org/platform-engineering
infra/** @my-org/platform-engineering @my-org/cloud-security
index.js @my-org/payments-team
EOF

git add .github/CODEOWNERS
git commit -m "Add code owners for sensitive paths"
```

6. Write a ruleset design note for the repository.

```bash
cat > RULESET-DESIGN.md <<'EOF'
# payments-api ruleset design

The `main` branch should require pull requests, two approvals, CODEOWNERS review, and strict required status checks.

Required checks:
- CodeQL Analysis
- Dependency Review
- Unit tests once the repository adds a test workflow

Sensitive paths:
- `.github/workflows/*` requires platform engineering review.
- `infra/**` requires platform engineering and cloud security review.

Deployment:
- Production deployment uses GitHub Environments and OIDC.
- Long-lived cloud keys must not be stored as repository secrets.
- The cloud trust policy should accept only the production environment identity for this repository.
EOF

git add RULESET-DESIGN.md
git commit -m "Document repository ruleset design"
```

7. Inspect the workflow permissions and explain each one.

```bash
grep -R "permissions:" -A4 .github/workflows
```

Your explanation should identify why CodeQL needs `security-events: write`, why dependency review does not need broad write access, and why the deployment workflow needs `id-token: write` only when it requests OIDC identity.

8. If you have a GitHub repository available, push the branch and open a pull request. Enable available code security features in repository settings, then verify that the pull request shows security workflow results. If your account does not support a feature, record which feature was unavailable and which organization or enterprise setting would enable it.

### Success Criteria

- [ ] The repository contains a runnable Node.js service with `package.json`, `package-lock.json`, and `index.js`.
- [ ] CodeQL runs on pull requests, pushes to `main`, and a weekly schedule.
- [ ] The CodeQL workflow uses least-privilege permissions and includes extended security queries.
- [ ] Dependency review runs on pull requests and fails on high-severity vulnerabilities.
- [ ] The deployment workflow uses `id-token: write` and does not reference a stored cloud access key.
- [ ] CODEOWNERS protects workflow files and other sensitive paths.
- [ ] The ruleset design note explains required pull request review, required checks, and deployment identity.
- [ ] You can explain which GitHub control owns each risk: code vulnerability, dependency risk, secret exposure, workflow tampering, and cloud deployment access.

### Verification

```bash
git log --oneline --decorate --max-count=8
find .github -maxdepth 3 -type f -print
grep -R "id-token: write" .github/workflows
grep -R "security-events: write" .github/workflows
grep -R "fail-on-severity: high" .github/workflows
```

Expected verification results: the commit log should show separate commits for the application, CodeQL, dependency review, deployment workflow, CODEOWNERS, and ruleset design. The `grep` commands should find the OIDC permission, CodeQL security event permission, and dependency review severity policy. If you pushed to GitHub, the pull request should show workflow checks or clear messages explaining which security features require additional account configuration.

---

## Next Module

Next, continue to [Module 12.3: CodeQL](/platform/toolkits/security-quality/code-quality/module-12.3-codeql/) for a deeper look at query writing, data-flow analysis, and custom security rules.

---

## Sources

- [About GitHub Advanced Security](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security) — Backs GitHub Advanced Security feature-set claims, including GitHub Code Security and GitHub Secret Protection positioning.
- [docs.github.com: about code scanning with codeql](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql) — The official CodeQL overview directly states that CodeQL treats code like data and contrasts it with traditional static analyzers.
- [OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect) — Backs GitHub Actions OIDC claims for short-lived federated authentication from workflows to cloud providers without long-lived secrets.
- [docs.github.com: streaming the audit log for your enterprise](https://docs.github.com/admin/monitoring-activity-in-your-enterprise/reviewing-audit-logs-for-your-enterprise/streaming-the-audit-log-for-your-enterprise) — The official audit-log-streaming docs enumerate these supported destinations.
- [docs.github.com: managing allowed ip addresses for your organization](https://docs.github.com/en/enterprise-cloud%40latest/organizations/keeping-your-organization-secure/managing-allowed-ip-addresses-for-your-organization) — The official IP allow-list docs explicitly describe protection across web, API, and Git access paths.
- [docs.github.com: enterprise managed users](https://docs.github.com/en/enterprise-cloud%40latest/admin/concepts/identity-and-access-management/enterprise-managed-users) — The EMU docs directly describe IdP-controlled lifecycle/authentication and the outside-collaboration restriction.
- [docs.github.com: about rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) — The official rulesets docs explicitly describe org-level scope and advantages over branch protection.
