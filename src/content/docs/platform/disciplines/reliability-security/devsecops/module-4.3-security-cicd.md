---
title: "Module 4.3: Security in CI/CD Pipelines"
slug: platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd
sidebar:
  order: 4
---

> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 55-70 min

## Prerequisites

Before starting this module, you should be comfortable reading a CI/CD workflow file and following how source code moves from commit to build, test, artifact publication, and deployment approval.

- **Required**: [Module 4.2: Shift-Left Security](../module-4.2-shift-left-security/) because this module assumes you already understand why developers need early feedback before code reaches shared branches.
- **Required**: Basic CI/CD experience with GitHub Actions, GitLab CI, Jenkins, Tekton, CircleCI, or a similar tool because examples use jobs, stages, artifacts, permissions, and branch protection.
- **Recommended**: Container image fundamentals, including Dockerfiles, base images, registries, tags, and digests because container scanning is a major security gate in modern delivery systems.
- **Helpful**: YAML configuration experience because most pipeline controls are expressed as YAML and mistakes in indentation, permissions, or job dependencies can change security behavior.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a layered CI/CD security pipeline that places secrets scanning, SAST, SCA, image scanning, IaC scanning, and deployment policy checks at the stages where they provide the strongest signal.
- **Evaluate** security findings by severity, exploitability, reachability, asset exposure, and deployment context so that gates block dangerous changes without creating constant false emergencies.
- **Debug** a failing security gate by tracing which tool produced the finding, which artifact was scanned, which policy decided the result, and what remediation path fits the risk.
- **Implement** a runnable GitHub Actions security workflow that uploads findings, limits token permissions, separates untrusted scan jobs from publish jobs, and blocks unsafe releases.
- **Compare** pipeline security trade-offs such as fast pull-request scans versus deeper scheduled scans, mutable action tags versus pinned references, and warning gates versus blocking gates.

---

## Why This Module Matters

At midnight before a holiday sale, a platform team member receives a page from the release channel rather than the monitoring system. The deployment is blocked, not because the application tests failed, but because the container scan found a critical remote-code-execution vulnerability in the base image used by every checkout service. The first reaction in the room is frustration: the feature is ready, the business deadline is real, and nobody wants a security tool deciding whether revenue ships.

Five minutes later, the room changes tone. The affected package is present in the runtime layer, the service is internet-facing, and the exploit requires only crafted input that the checkout service already accepts. The pipeline did not create the risk; it exposed a risk that was already riding toward production inside a green build. The gate forced the organization to make an explicit decision while there was still time to fix the image, route traffic around the affected service, or accept the risk with named ownership.

That is the purpose of CI/CD security. Pre-commit hooks help developers catch mistakes early, but they can be skipped, misconfigured, or disabled on a single workstation. Local scans also do not see the final container, the exact dependency graph after lockfile resolution, or the deployment manifest after templating. CI/CD is the first place where the organization can evaluate the change as a repeatable system rather than as a developer's private workspace.

A secure pipeline is not a pile of scanners glued onto the end of a build. It is a decision system that asks different security questions at different moments. Before code builds, the pipeline asks whether the repository contains secrets or obvious insecure patterns. While dependencies resolve, it asks whether third-party code introduces known vulnerabilities or unacceptable licenses. After the image is built, it asks whether the runtime artifact contains vulnerable packages, unsafe defaults, or unsigned layers. Before deployment, it asks whether policy allows this artifact to run in this environment.

The hard part is not installing tools. The hard part is designing gates that protect production without turning every pull request into a security negotiation. A pipeline that blocks every low-confidence warning will be bypassed. A pipeline that only writes reports nobody reads is theater. The practitioner skill is knowing which risks must stop the line, which risks should create work with a service-level objective, and which risks should be logged for trend analysis.

This module teaches that skill from the ground up. You will start with the anatomy of a security pipeline, then add scanners one layer at a time. You will learn how to interpret findings, how to implement gates, how to separate untrusted jobs from privileged publish jobs, and how to debug a failing gate without guessing. By the end, you should be able to design a security pipeline that a delivery team can live with and a security team can defend.

---

## The Security Pipeline Architecture

CI/CD security starts with a simple question: what is the pipeline allowed to decide before the change reaches production? If the answer is only "run tests and publish an image," then security becomes a late human review or a dashboard nobody checks under deadline pressure. If the answer includes "reject unsafe code, unsafe dependencies, unsafe artifacts, and unsafe deployment configuration," then the pipeline becomes a control point with real authority.

A useful mental model is to treat the pipeline as a series of evidence-producing stages. Each stage inspects a different version of the change. Source-stage checks inspect repository content. Build-stage checks inspect compiled code, dependency resolution, and generated artifacts. Test-stage checks inspect running behavior. Deploy-stage checks inspect whether the artifact is allowed to enter a target environment. Each stage produces evidence, and a gate decides whether that evidence is strong enough to continue.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                        DEVSECOPS PIPELINE STAGES                             │
├────────────────────┬────────────────────┬────────────────────┬──────────────┤
│ SOURCE             │ BUILD              │ TEST               │ DEPLOY       │
│ ┌────────────────┐ │ ┌────────────────┐ │ ┌────────────────┐ │ ┌──────────┐ │
│ │ Secrets scan   │ │ │ SAST           │ │ │ DAST           │ │ │ Policy   │ │
│ │ Commit checks  │ │ │ SCA            │ │ │ API checks     │ │ │ Verify   │ │
│ │ Action review  │ │ │ Image build    │ │ │ Auth tests     │ │ │ Sign     │ │
│ │ Lockfile diff  │ │ │ SBOM create    │ │ │ Abuse cases    │ │ │ Admit    │ │
│ └───────┬────────┘ │ └───────┬────────┘ │ └───────┬────────┘ │ └────┬─────┘ │
│         │          │         │          │         │          │      │       │
│         ▼          │         ▼          │         ▼          │      ▼       │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │                             SECURITY GATES                              │ │
│ │ Critical reachable risk -> block | High new risk -> block or exception  │ │
│ │ Medium risk -> warn with SLA     | Low risk -> record and trend         │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│                                      ▼                                       │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Findings store, SARIF upload, ticket creation, dashboards, audit trail   │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

The source stage should be fast and strict because it catches mistakes that should never enter shared history. Secret detection belongs here because a leaked token becomes dangerous as soon as it is pushed to a remote repository, not when the application is deployed. Commit-signing checks, branch protection, workflow-file review, and lockfile-diff checks also belong near the source boundary because they protect the integrity of the change itself.

The build stage is where the pipeline knows enough to inspect the software as a real artifact. SAST can analyze the application code, SCA can evaluate the dependency graph, and container scanning can inspect operating-system packages inside the final image. This stage should produce durable evidence such as SARIF reports, SBOMs, image digests, and vulnerability summaries because later deployment decisions need to refer to exactly what was built.

The test stage adds runtime context. A static scanner may report a dangerous endpoint pattern, but a dynamic application security test can exercise the running service and confirm whether authentication, authorization, headers, and input validation behave correctly. Runtime tests are slower and more environment-dependent, so teams usually run a focused set on pull requests and deeper scans on schedules or release candidates.

The deploy stage is the last opportunity to prevent unsafe artifacts from entering an environment. By this point, the pipeline should know the image digest, the signing status, the SBOM location, the scan results, and the Kubernetes manifests or Helm chart being applied. Admission policy, environment promotion rules, and deployment approvals should evaluate that evidence rather than trusting a human memory of what happened earlier in the pipeline.

| Stage | Primary question | Security activities | Typical gate decision |
|---|---|---|---|
| Source | Is the change itself safe to accept into shared review? | Secret scanning, workflow review, branch protection, lockfile inspection | Block leaked secrets, unauthorized workflow changes, or unsigned commits when required |
| Build | Is the produced artifact safe enough to publish or promote? | SAST, SCA, SBOM generation, image scanning, provenance capture | Block critical reachable findings, vulnerable base images, or missing artifact evidence |
| Test | Does the running service expose exploitable behavior? | DAST, API tests, abuse-case tests, authentication and authorization checks | Block confirmed exploit paths such as injection, auth bypass, or unsafe debug endpoints |
| Deploy | Is this exact artifact allowed in this exact environment? | Signature verification, policy-as-code, admission control, environment rules | Block unsigned images, forbidden privileges, drift from approved policy, or expired exceptions |

The table hides an important operational truth: different stages should have different tolerance for noise. A source-stage secret finding should usually be treated as urgent because leaked credentials must be rotated even if the pull request is closed. A SAST finding in experimental code might need triage before blocking. A deploy-stage policy violation such as `privileged: true` in a production namespace should block because the risk is concrete and the target environment is known.

A mature team does not ask "which scanner should we add?" before it asks "which decision are we trying to improve?" If the team keeps shipping containers with vulnerable base images, image scanning before registry push is the right control. If developers keep introducing SQL injection patterns, SAST and secure-code review are the right controls. If production clusters keep accepting workloads with broad permissions, deployment policy and admission checks are the right controls.

> **Stop and think:** A pull request changes only `README.md`, but the workflow still runs a full image build, dependency scan, and DAST suite. Which checks provide meaningful security signal for that change, and which checks are mostly burning developer time? Write down one rule you would use to keep documentation-only changes fast without weakening protection for code changes.

The answer is not to skip security whenever the diff looks small. Workflow files, lockfiles, Dockerfiles, deployment manifests, and generated code can change risk without touching application source. A good pipeline uses path filters carefully, but it treats security-sensitive files as high signal. When in doubt, optimize expensive checks by moving them to the right trigger rather than removing them entirely.

---

## Threat Modeling the Pipeline Itself

A CI/CD pipeline is not only a security control; it is also a privileged system that attackers want to control. Pipeline runners can read source code, access dependency caches, build trusted artifacts, request cloud credentials, publish packages, push images, and deploy to clusters. A scanner job that runs untrusted code with broad secrets can become more dangerous than the vulnerability it was supposed to detect.

The first design principle is least privilege per job. A job that scans source code does not need a package-publishing token. A job that builds a pull-request image does not need production cluster credentials. A job that comments on a pull request does not need permission to write repository contents. CI systems make broad permissions convenient, but secure pipelines treat every job as a separate trust boundary.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                            PIPELINE TRUST BOUNDARIES                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Untrusted PR code                                                            │
│  ┌────────────────┐        read-only token        ┌────────────────────────┐ │
│  │ scan and test  │──────────────────────────────▶│ findings and comments  │ │
│  │ no prod creds  │                               │ no artifact publish    │ │
│  └────────────────┘                               └────────────────────────┘ │
│                                                                              │
│  Trusted main branch                                                          │
│  ┌────────────────┐        scoped OIDC token       ┌────────────────────────┐ │
│  │ build artifact │──────────────────────────────▶│ registry publish       │ │
│  │ signed output  │                               │ provenance record      │ │
│  └────────────────┘                               └────────────────────────┘ │
│                                                                              │
│  Approved release                                                             │
│  ┌────────────────┐        deploy identity        ┌────────────────────────┐ │
│  │ policy verify  │──────────────────────────────▶│ staging or production  │ │
│  │ digest pinned  │                               │ admission control      │ │
│  └────────────────┘                               └────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

The second design principle is artifact immutability. A pipeline should promote image digests, not mutable tags. If the test job scans `myapp:latest` and the deploy job later deploys `myapp:latest`, there is no guarantee that the deployed image is the image that passed scanning. When possible, the build job should output a digest, downstream jobs should consume that digest, and deployment manifests should reference the digest or a signed provenance record.

The third design principle is controlled dependency on third-party pipeline components. GitHub Actions, GitLab includes, containerized build steps, shared Jenkins libraries, and marketplace plugins all execute code inside the delivery path. A compromised action or plugin can read environment variables, alter artifacts, modify scan output, or publish malicious packages. Treat external pipeline components as supply-chain dependencies, not harmless configuration snippets.

A practical pipeline threat model should answer five questions before the first scanner is added. Who can change the pipeline file? Which jobs run code from forks or untrusted branches? Which jobs receive secrets or cloud credentials? Which artifacts are trusted by later jobs or environments? Which external actions, containers, or plugins can execute inside the runner? These questions identify where an attacker would try to turn the pipeline into a deployment mechanism.

| Pipeline asset | Attacker goal | Defensive control | What to audit |
|---|---|---|---|
| Workflow files | Add a job that exfiltrates secrets or bypasses gates | CODEOWNERS, branch protection, review by platform or security owners | Changes under `.github/workflows/`, `.gitlab-ci.yml`, Jenkinsfiles, and shared templates |
| Runner credentials | Steal cloud, registry, package, or deployment tokens | Job-level permissions, OIDC with audience restrictions, secret scoping | Jobs with `write`, `id-token`, registry, or environment deployment access |
| Build artifacts | Replace or mutate artifacts after scanning | Digest promotion, signatures, provenance, immutable registry settings | Whether deploy jobs consume the exact digest produced by build jobs |
| External actions | Execute compromised third-party code in trusted jobs | Pin actions, review updates, restrict allowed actions, prefer maintained sources | Marketplace actions, Docker actions, and shared CI templates |
| Scan results | Hide findings or downgrade severity | Upload immutable reports, keep raw scanner output, gate on machine-readable files | `continue-on-error`, ignored exit codes, local filtering scripts, and exception files |

A common failure mode is granting permissions at the workflow level because it is easier than reasoning about each job. In GitHub Actions, permissions can be restricted per job. The following workflow is runnable, but deliberately small, so the permission boundary is easy to see. The scan job can read repository contents and upload security events, while the publish job only runs on `main` and receives the identity token needed for a trusted publish flow.

```yaml
name: Minimal Permission Boundary
on:
  pull_request:
  push:
    branches: [main]

permissions: {}

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Run dependency scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          format: sarif
          output: trivy-fs.sarif
          severity: CRITICAL,HIGH
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-fs.sarif

  publish:
    runs-on: ubuntu-latest
    needs: scan
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Show publish boundary
        run: |
          echo "Only this trusted main-branch job receives publish permissions."
```

This example still uses action version tags because the workflow must be directly runnable in a new repository. In a production program, teams commonly add an action-pinning policy, an allowlist of approved actions, and an automated update process that resolves tags to reviewed immutable references. The key teaching point is that the scanner and publisher should not share the same token boundary.

> **Active check:** Look at one CI/CD workflow you maintain or have used recently. Identify the job with the broadest permissions and write down whether that job runs untrusted pull-request code, trusted main-branch code, or release-only code. If you cannot answer from the YAML alone, the workflow needs clearer boundaries.

---

## Choosing the Right Security Checks

Security checks are easiest to understand when you map them to the class of risk they can actually observe. SAST inspects source code patterns and data flow. SCA inspects dependencies and known vulnerabilities. Secret scanning inspects accidental credential exposure. Container scanning inspects operating-system packages and image metadata. IaC scanning inspects infrastructure configuration before it is applied. DAST inspects a running application from the outside.

No single tool sees the whole system. SAST may find a SQL injection pattern but knows nothing about a vulnerable OpenSSL package in the base image. SCA may find a vulnerable library but not know whether a dangerous endpoint is exposed. DAST may confirm that a running service leaks data, but it usually cannot explain which line of code or dependency caused the issue. Layering is necessary because each tool observes a different surface.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                            WHAT EACH CHECK CAN SEE                           │
├──────────────────────┬───────────────────────────────────────────────────────┤
│ Secrets scanning     │ Repository content, commit history, accidental tokens  │
│ SAST                 │ Source patterns, data flow, unsafe API usage           │
│ SCA                  │ Direct and transitive dependencies, package CVEs        │
│ Container scanning   │ Base image, OS packages, language packages in image     │
│ IaC scanning         │ Terraform, Kubernetes YAML, Helm-rendered manifests     │
│ DAST                 │ Running service behavior, auth flow, headers, inputs    │
│ Policy verification  │ Whether artifact and manifest satisfy release rules     │
└──────────────────────┴───────────────────────────────────────────────────────┘
```

Secrets scanning belongs early because credential exposure is time-sensitive. A token committed to a public repository may be harvested within minutes, and closing the pull request does not make the credential safe again. Good pipelines scan both the current diff and enough history to detect newly introduced secrets. Mature programs also teach developers how to rotate leaked credentials because detection without revocation leaves the risk active.

SAST belongs early enough to give developers useful feedback while the code is still fresh. It is strongest when rules are tuned to the language, framework, and threat model of the service. Generic rule packs are a useful start, but high-value SAST programs add local rules for known dangerous helpers, banned crypto patterns, internal authentication conventions, and framework-specific mistakes that have caused incidents before.

SCA belongs near dependency resolution because lockfiles and build tools decide what actually gets installed. A `package.json` file is not the whole Node.js dependency graph, and a Python requirements file may not reflect transitive dependencies until resolution completes. Scanning the repository is useful, but scanning the generated SBOM or the built image can reveal differences between intended dependencies and shipped dependencies.

Container scanning belongs after the image is built because Dockerfiles are only instructions. The final image may include base-image packages, transitive language packages, build leftovers, shell utilities, package-manager caches, and files copied from previous stages. A scan before build can catch some Dockerfile issues, but only a scan of the final image can answer what the runtime artifact contains.

IaC scanning belongs before deployment because configuration can create severe risk even when the application code is clean. A secure service can become dangerous if it is deployed with a privileged container, a writable root filesystem, unrestricted egress, a public storage bucket, or a service account with broad permissions. Infrastructure security gates are especially important in Kubernetes because YAML defaults are often more permissive than teams realize.

DAST belongs after a deployable service is running in a controlled environment. It can detect missing security headers, authentication bypasses, injection behavior, unsafe redirects, and exposed debug routes. Because DAST can be slow and sometimes noisy, many teams run a small PR-level test against preview environments and a deeper scheduled scan against staging.

| Check type | Strong at finding | Weak at finding | Best trigger |
|---|---|---|---|
| Secrets scanning | Tokens, private keys, high-entropy strings, credentials in history | Whether a secret is still valid or already rotated | Pull request, push, scheduled history scan |
| SAST | Code-level insecure patterns, data-flow issues, dangerous APIs | Runtime configuration, vulnerable base images, actual exploitability in every context | Pull request and main branch |
| SCA | Known CVEs in dependency graphs, vulnerable transitive packages | Custom code flaws, whether a vulnerable function is reachable without extra analysis | Pull request when dependency files change, nightly full scan |
| Container scan | OS package CVEs, image-layer risks, vulnerable runtime contents | Source-only flaws that were not copied into the image | After image build and before registry push |
| IaC scan | Misconfigured cloud and Kubernetes resources | Runtime application bugs and hidden manual changes | Pull request and pre-deploy render |
| DAST | Confirmed behavior in a running service | Deep source cause, internal-only code paths, unreachable endpoints | Preview, staging, release candidate, scheduled scan |

The sequencing matters because each check should inspect the most truthful representation available at that moment. SCA before dependency resolution is useful but incomplete. Container scanning before image build is impossible. DAST before a service is running is only wishful thinking. A well-designed pipeline does not merely "run scanners"; it runs each scanner when its input is accurate.

A small but important design choice is whether security tools fail their own job or produce reports for a separate gate. Letting every tool fail immediately is simple, but it can hide later findings because the workflow stops at the first failure. A separate gate job can collect all results, upload reports, and then make one clear decision. The trade-off is that the gate job needs disciplined parsing and policy logic.

For practitioner work, prefer a design where tools always publish their raw findings and a gate makes a decision from machine-readable output. Developers should see all relevant findings in one pull request, not fix one scanner only to discover a second scanner failure on the next run. Security teams should also be able to audit why a build passed or failed without reconstructing terminal logs from expired CI runs.

---

## Static Analysis, Dependency Scanning, and Secrets

Static checks are the fastest way to catch many security issues before the build produces an artifact. They are also the most likely checks to frustrate developers if they are noisy, poorly tuned, or disconnected from remediation guidance. The goal is not to prove the code is secure. The goal is to catch known classes of mistakes early enough that fixing them is cheaper than arguing about them later.

SAST analyzes code without running it. Some tools use pattern matching, some build abstract syntax trees, and some perform deeper data-flow analysis across functions and files. For example, a SAST rule may trace untrusted request input into a SQL query builder, command execution call, template renderer, or file path operation. The finding is useful because it points to the developer's code, not just to a vague security category.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                                SAST ANALYSIS                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Source file                         Analysis engine                         │
│  ┌──────────────────────┐            ┌────────────────────────────────────┐  │
│  │ user_id = request... │   parse    │ syntax tree, data flow, patterns   │  │
│  │ query = "SELECT" +   │───────────▶│ source -> sink tracking            │  │
│  │ conn.execute(query)  │            │ framework-aware rules              │  │
│  └──────────────────────┘            └─────────────────┬──────────────────┘  │
│                                                        │                     │
│                                                        ▼                     │
│                                      ┌────────────────────────────────────┐  │
│                                      │ Finding: SQL injection candidate   │  │
│                                      │ Evidence: request input reaches    │  │
│                                      │ database execution without binding │  │
│                                      └────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

SAST findings require context. A scanner may identify an injection pattern, but the developer still needs to confirm whether the source is attacker-controlled and whether the sink is actually dangerous in that framework. This is why the best SAST gates combine severity with confidence, reachability, and file ownership. Blocking every low-confidence pattern creates alert fatigue; ignoring every finding because some are false positives creates blind spots.

Semgrep is a common starting point because it is fast, readable, and supports custom rules. CodeQL is useful for deeper semantic analysis, especially in repositories already using GitHub code scanning. Language-specific tools such as Bandit for Python, Gosec for Go, and Brakeman for Ruby on Rails can provide framework knowledge that generic tools miss. The right answer is often a small combination rather than one universal scanner.

| SAST tool | Common use | Strength | Practitioner caution |
|---|---|---|---|
| Semgrep | Fast pull-request checks and custom rules | Rules are readable and easy to tune near the codebase | Generic rule packs need local tuning to avoid noisy gates |
| CodeQL | Deeper analysis and GitHub code scanning | Strong data-flow analysis for supported languages | Requires correct language setup and sometimes a build step |
| Bandit | Python-specific security checks | Quick feedback for common Python mistakes | Does not replace dependency or runtime scanning |
| Gosec | Go-specific security checks | Finds dangerous Go APIs and crypto misuse patterns | Findings still need review for exploitability |
| Brakeman | Rails application analysis | Knows Rails conventions and common web risks | Best used alongside dependency and configuration checks |
| SonarQube | Enterprise code quality and security programs | Central reporting and broad language support | Needs governance to avoid mixing style noise with security gates |

The following workflow runs Semgrep on pull requests and pushes to `main`. It is intentionally concise, but it includes two production-minded choices: read-only repository permissions and SARIF upload even when findings occur. Uploading SARIF makes findings visible in the code-scanning interface rather than trapping them inside a CI log.

```yaml
name: SAST
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep:latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Semgrep
        run: |
          semgrep ci \
            --config p/security-audit \
            --config p/secrets \
            --config p/owasp-top-ten \
            --sarif \
            --output semgrep.sarif
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: semgrep.sarif
```

SCA answers a different question: what third-party code is included, and does any of it have known vulnerabilities or policy violations? Modern applications often contain far more dependency code than first-party code. A web service with a few thousand lines of business logic may pull in hundreds of packages through direct and transitive dependencies. A vulnerable transitive package can be just as dangerous as a vulnerable direct dependency if the affected code is reachable.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                           DEPENDENCY RISK SHAPE                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Application repository                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ First-party code: controllers, services, jobs, business rules           │  │
│  ├────────────────────────────────────────────────────────────────────────┤  │
│  │ Direct dependencies: packages named in requirements, package files      │  │
│  ├────────────────────────────────────────────────────────────────────────┤  │
│  │ Transitive dependencies: packages pulled by packages you chose          │  │
│  ├────────────────────────────────────────────────────────────────────────┤  │
│  │ Runtime packages: language packages and OS packages in final image      │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  SCA inspects the dependency graph; image scanning verifies what shipped.     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

A dependency finding should not be reduced to "critical equals block, everything else equals ignore." The meaningful question is whether the vulnerable package is present, reachable, exploitable in this service, and fixable without unacceptable operational risk. A critical vulnerability in a development-only dependency may have lower urgency than a high vulnerability in a public authentication path. Policy should encode these distinctions where possible, while still keeping the default conservative for internet-facing services.

Trivy, Grype, Snyk, Dependabot, OWASP Dependency-Check, npm audit, and language-native tools all solve part of the SCA problem. Trivy is popular because it can scan filesystems, containers, repositories, SBOMs, and configuration. Dependabot is useful because it turns some findings into pull requests. Commercial tools may add reachability analysis, prioritization, and management workflows. Tool choice matters less than whether the team has a reliable path from finding to fix.

| SCA tool | Common use | Strength | Practitioner caution |
|---|---|---|---|
| Trivy | Filesystem, image, SBOM, and config scanning | Broad coverage and simple CI integration | Configure severity and ignore files carefully; do not hide risk permanently |
| Grype | SBOM and container vulnerability scanning | Works well with Syft-generated SBOMs | Match database freshness to your response expectations |
| Dependabot | Automated dependency update pull requests | Converts known vulnerable dependencies into reviewable changes | PR volume needs grouping, ownership, and test confidence |
| Snyk | Developer-focused vulnerability management | Useful remediation advice and prioritization features | Token and organization setup must be managed securely |
| OWASP Dependency-Check | Java and compliance-oriented scanning | Familiar in many enterprise environments | Can be noisy without suppression governance |
| npm audit | Quick Node.js ecosystem checks | Built into common workflows | Advisory quality and transitive fix paths require review |

The following workflow demonstrates a filesystem dependency scan that uploads SARIF and fails on critical or high findings. It scans the repository rather than a container image, so it is useful before the image build. Later in this module, you will add image scanning so the final runtime artifact is also checked.

```yaml
name: Dependency Scan
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  trivy-fs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan dependency files and repository content
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          format: sarif
          output: trivy-fs.sarif
          severity: CRITICAL,HIGH
          exit-code: "1"
      - name: Upload Trivy SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-fs.sarif
```

Secret scanning deserves separate treatment because the remediation path is different from normal vulnerability remediation. If a developer commits an API key, removing it from the next commit is not enough. The credential may already be in remote history, CI logs, notifications, forks, package artifacts, or a search engine cache. The correct response is to revoke or rotate the credential, remove it from history when appropriate, and replace the workflow with a safer secret-management pattern.

A good secret gate should be fast, visible, and supported by clear incident behavior. Developers need to know whether a finding is a false positive, a test fixture, or a real credential. Security teams need an audit trail showing whether exposed credentials were rotated. Platform teams need patterns that reduce future exposure, such as OIDC federation to cloud providers, short-lived tokens, environment-scoped secrets, and no long-lived publish keys in broad runner environments.

---

## Container Image and IaC Scanning

Container scanning finds a class of risk that source scanners often miss: the operating-system and runtime contents of the final image. A Python service may have clean application code and patched Python dependencies while still shipping a vulnerable OpenSSL package from its base image. A Go service may compile to a static binary but still carry shell utilities, package-manager caches, or build dependencies because the Dockerfile was not structured carefully.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                             CONTAINER IMAGE LAYERS                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Application code and compiled assets                                   │  │
│  │ Security concern: first-party vulnerabilities and accidental secrets    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Language dependencies installed into the image                          │  │
│  │ Security concern: vulnerable direct and transitive packages             │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Operating-system packages from base image and install steps             │  │
│  │ Security concern: CVEs in libc, OpenSSL, curl, shell utilities          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Base image metadata, user, entrypoint, package manager, filesystem      │  │
│  │ Security concern: root user, excessive tools, outdated distribution     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

The most effective image-security decision often happens before scanning: choose a smaller, maintained base image. A minimal image reduces the number of packages that can have vulnerabilities and reduces the tools an attacker can use after compromise. Distroless images, Chainguard images, Alpine images, and slim distribution images each have trade-offs around compatibility, debugging, package availability, and vulnerability noise. The best choice depends on runtime needs, not fashion.

Image scanning should happen before the image is pushed to a registry that downstream systems trust. If the pipeline builds and pushes first, then scans later, a vulnerable image may already be available for deployment by another job or operator. The safer sequence is build, scan, sign or attest, and only then push or promote. Some registries also scan images after push, but registry scanning should complement CI gates rather than replace them.

| Image scanning tool | Common use | Strength | Practitioner caution |
|---|---|---|---|
| Trivy | CI image scanning and repository scanning | Simple action, broad vulnerability database support | Database freshness and severity thresholds must be intentional |
| Grype | SBOM-based and image vulnerability scanning | Strong pairing with Syft for SBOM workflows | Requires clear policy for matching and false positives |
| Docker Scout | Docker-focused image insight | Convenient for Docker Hub and Docker Desktop users | Fit depends on registry and ecosystem choice |
| Snyk Container | Developer-facing container remediation | Useful base-image upgrade advice | Requires token management and organization setup |
| Clair | Registry-integrated scanning | Common in Quay and platform environments | CI integration may need extra wiring |

The following workflow builds an image locally, scans it, uploads SARIF, and only pushes from the trusted `main` branch after the scan job succeeds. It also demonstrates why job dependencies matter: the `push` job cannot run unless the image scan completes successfully.

```yaml
name: Container Security
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write
  security-events: write

env:
  IMAGE_NAME: ghcr.io/${{ github.repository }}/app

jobs:
  build-and-scan:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.image-tag }}
    steps:
      - uses: actions/checkout@v4
      - name: Set image tag
        id: meta
        run: |
          echo "image-tag=${IMAGE_NAME}:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
      - name: Build image
        run: |
          docker build -t "${IMAGE_NAME}:${GITHUB_SHA}" .
      - name: Scan image before push
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: sarif
          output: trivy-image.sarif
          severity: CRITICAL,HIGH
          exit-code: "1"
      - name: Upload image scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-image.sarif

  push:
    runs-on: ubuntu-latest
    needs: build-and-scan
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Log in to GitHub Container Registry
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io \
            --username "${{ github.actor }}" \
            --password-stdin
      - name: Rebuild and push trusted image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ env.IMAGE_NAME }}:${{ github.sha }}
```

This example rebuilds in the push job because GitHub-hosted runners do not share local Docker images across jobs. In a production pipeline, teams often use buildx cache, an internal staging registry, or artifact export to avoid rebuilding. The security rule remains the same: whatever is pushed or promoted must be the same artifact that was scanned, or the pipeline needs a digest and provenance mechanism that proves equivalence.

IaC scanning checks whether infrastructure definitions violate security policy before they reach a cluster or cloud account. Kubernetes manifests are especially important because small fields carry large security meaning. A container running as root with a writable root filesystem and broad Linux capabilities can become a serious runtime risk even if the application code is clean. A service account bound to cluster-admin can turn a small application bug into a cluster compromise.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: unsafe-example
spec:
  containers:
    - name: app
      image: nginx:latest
      securityContext:
        privileged: true
        runAsUser: 0
      resources: {}
```

The manifest above is runnable YAML, but it is intentionally unsafe. It uses a mutable image tag, grants privileged mode, runs as root, and omits resource requests and limits. An IaC scanner or policy engine should flag these issues before anyone applies the manifest. In a Kubernetes 1.35+ environment, a safer baseline would pin the image, run as a non-root user, drop capabilities, use a read-only root filesystem when possible, and define resource constraints.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: safer-example
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: nginx:1.27.5
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      resources:
        requests:
          cpu: 50m
          memory: 64Mi
        limits:
          cpu: 250m
          memory: 256Mi
```

| IaC scanner | Common targets | Strength | Practitioner caution |
|---|---|---|---|
| Checkov | Terraform, Kubernetes, CloudFormation, Dockerfile | Broad policy library and CI integration | Tune suppressions and record why exceptions exist |
| Trivy config scan | Terraform, Kubernetes, Dockerfile, Helm output | One tool can scan dependencies, images, and config | Render templates first when source YAML is not final |
| kube-linter | Kubernetes manifests and Helm charts | Kubernetes-focused recommendations | Does not replace admission policy in the cluster |
| Kubesec | Kubernetes security scoring | Simple feedback for manifest hardening | Scores need interpretation, not blind pass/fail use |
| Terrascan | Terraform, Kubernetes, Dockerfile, cloud resources | Policy-as-code oriented scanning | Keep policies aligned with platform standards |
| Conftest | Any structured configuration through Rego policies | Strong for custom organizational policy | Requires policy authoring skill and tests |

The most common IaC-scanning mistake is scanning templates instead of rendered manifests. Helm charts, Kustomize overlays, Jsonnet, and Terraform modules can produce different output depending on values and environment. If production uses rendered Kubernetes YAML, the security gate should scan rendered YAML. Otherwise, the scanner may approve a template while the generated manifest still violates policy.

---

## Designing Gates That Developers Can Trust

A security gate is a policy decision, not a scanner setting. The scanner reports evidence. The gate decides what that evidence means for this repository, branch, artifact, and environment. Treating `exit-code: 1` as the entire security policy is simple, but it prevents teams from expressing useful distinctions such as new versus existing findings, reachable versus unreachable vulnerabilities, production versus development services, and expired versus approved exceptions.

The first gate design decision is severity threshold. Blocking on every medium finding may sound strict, but it can trap teams in noise if the scanner reports many theoretical vulnerabilities. Blocking only on critical findings may be too weak for internet-facing services where high-severity vulnerabilities are realistic exploitation paths. A practical baseline is to block critical findings, block high findings in new code or production-bound artifacts, warn on medium findings with an SLA, and record low findings for trend analysis.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                              SECURITY GATE POLICY                            │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│ Finding category     │ Default action       │ Expected follow-up            │
├──────────────────────┼──────────────────────┼───────────────────────────────┤
│ Critical reachable   │ Block                │ Fix before merge or release   │
│ Critical unknown     │ Block                │ Triage and document exposure  │
│ High new risk        │ Block for production │ Fix before release or exception│
│ High legacy risk     │ Warn with SLA        │ Track owner and due date      │
│ Medium risk          │ Warn                 │ Batch remediation             │
│ Low risk             │ Record               │ Trend and opportunistic fix   │
│ Missing evidence     │ Block                │ Repair pipeline or artifact   │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
```

The second gate design decision is baseline handling. Many organizations add scanners to mature systems and discover hundreds or thousands of existing findings. Blocking every existing issue immediately can freeze delivery and motivate teams to remove the scanner. A better approach is to create a reviewed baseline for existing findings, block newly introduced findings, and attach remediation work to owners with due dates. Baselines are not forgiveness; they are a way to keep new risk from growing while legacy risk is burned down.

The third gate design decision is exception governance. Exceptions are necessary because real systems have operational constraints, vendor dependencies, and emergency releases. They become dangerous when they are permanent, invisible, or unowned. A useful exception records the finding, affected artifact, justification, approving owner, expiration date, compensating control, and review link. If an exception has no expiration, it is not an exception; it is an undocumented policy change.

The fourth gate design decision is evidence preservation. A failed job should leave behind enough information for a developer to fix the issue without rerunning locally several times. The pipeline should upload SARIF, SBOMs, raw scanner logs, image digests, and policy summaries where the team can inspect them. A gate that simply says "security failed" is not a teaching tool or an operational control. It is a bottleneck.

| Gate input | Why it matters | Example policy question |
|---|---|---|
| Severity | Provides a rough urgency estimate from the tool or advisory source | Is this critical or high enough to block this branch? |
| Confidence | Separates likely real issues from weak pattern matches | Should a low-confidence SAST finding create a warning instead of a block? |
| Reachability | Indicates whether vulnerable code can execute in this application | Is the vulnerable dependency function reachable from production code paths? |
| Exposure | Connects the finding to attack surface | Is the affected service internet-facing, internal-only, or development-only? |
| Asset criticality | Adds business and operational context | Does this service handle credentials, payments, personal data, or cluster access? |
| New versus existing | Prevents legacy findings from hiding new risk | Did this pull request introduce the finding or only touch nearby code? |
| Exception status | Allows controlled risk acceptance | Is there an approved, unexpired exception with a compensating control? |

A separate gate job can make this policy visible. The example below is intentionally small and uses ordinary shell logic so the mechanism is understandable. In a larger program, this logic might move into OPA, Conftest, a custom gate service, or a vulnerability-management platform. The important idea is that scanner jobs produce outputs, and the gate job decides what blocks.

```yaml
name: Security Gate Example
on:
  pull_request:

permissions:
  contents: read
  security-events: write

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    continue-on-error: true
    outputs:
      outcome: ${{ steps.scan.outcome }}
    steps:
      - uses: actions/checkout@v4
      - name: Trivy filesystem scan
        id: scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: "1"
          format: sarif
          output: trivy-fs.sarif
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-fs.sarif

  security-gate:
    runs-on: ubuntu-latest
    needs: dependency-scan
    steps:
      - name: Decide whether the pull request can continue
        run: |
          if [ "${{ needs.dependency-scan.outputs.outcome }}" = "failure" ]; then
            echo "::error::Critical or high dependency findings require remediation or an approved exception."
            exit 1
          fi
          echo "Security gate passed."
```

Notice that `continue-on-error` appears on the scan job, not because the pipeline wants to ignore the failure, but because the pipeline wants to upload reports and let the gate produce the final decision. This is a subtle but important distinction. Used carelessly, `continue-on-error` hides security failures. Used deliberately, it preserves evidence before a central gate blocks.

> **Stop and think:** Your team has an old service with many high vulnerabilities already in the baseline. A pull request changes one controller and introduces a new medium SAST finding. Should the gate block, warn, or pass? Decide based on the new risk, the service exposure, the finding confidence, and whether the affected code path handles sensitive data.

A senior practitioner answer would not rely only on the word "medium." If the service is internet-facing and the medium finding is a high-confidence authorization bypass pattern in a sensitive controller, blocking may be reasonable. If the finding is low-confidence in an internal admin tool and does not reach production, warning with remediation work may be enough. The gate policy should leave room for context while still making dangerous defaults explicit.

---

## Worked Example: Debugging a Failing Security Gate

This worked example demonstrates a complete procedure from problem to solution. You will see the symptoms, inspect the evidence, identify which artifact failed, choose a remediation, and verify the fix. The scenario is intentionally realistic: a pull request fails after adding a container scan, and the team must decide whether to patch the Dockerfile, change the base image, or create an exception.

The application is a small Python service with a Dockerfile that uses an older base image. The pipeline builds the image and runs Trivy before pushing. The gate blocks on critical and high vulnerabilities. Developers see a red check named `build-and-scan`, but the first useful question is not "how do we make CI green?" The first useful question is "what exact risk did the pipeline find in what exact artifact?"

**Step 1: Read the failing job summary and identify the scanner.** The job name tells you this is the container scan, not the dependency filesystem scan or SAST job. That matters because the vulnerable package may come from the base image rather than application code. If a developer starts editing Python requirements without confirming the source, they may waste time and leave the image risk unchanged.

**Step 2: Inspect the scanner output and separate package source from severity.** A typical Trivy finding includes the package name, installed version, fixed version when available, severity, vulnerability identifier, and target image. The target image should match the image built in the job, usually tagged with the commit SHA. If the target is `latest` or a stale cached image, fix the pipeline before trusting the finding.

**Step 3: Confirm whether a fixed version exists.** Some findings can be fixed by updating packages inside the same base distribution. Other findings require changing the base image because the distribution has not published a patched package. A finding with no fixed version might still require mitigation, but the remediation path is different from a normal patch.

**Step 4: Choose the least risky remediation.** If a newer patch release of the same runtime image is available, update to it and rebuild. If the service does not need shell utilities or package managers at runtime, consider a slim or distroless runtime image. If changing the base image could break native dependencies, use a staging branch and run compatibility tests before promoting.

**Step 5: Verify the new artifact, not just the Dockerfile diff.** The pipeline must rebuild the image and rescan it. A Dockerfile change is only an instruction; the scan result on the final image is the evidence. If the scan passes but the image digest changes, downstream deployment should promote the new digest, not keep using a mutable tag.

Here is the intentionally vulnerable starting point. It is runnable, but the base image choice is the problem in this scenario.

```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
USER root
CMD ["python", "app.py"]
```

The team receives a finding in the image scan. The simplified output below shows what matters for the decision.

```bash
python:3.9 (debian 11)
======================
Total: 3 (HIGH: 2, CRITICAL: 1)

┌──────────────┬────────────────┬──────────┬───────────────┬───────────────┐
│   Package    │ Vulnerability  │ Severity │ Installed     │ Fixed         │
├──────────────┼────────────────┼──────────┼───────────────┼───────────────┤
│ openssl      │ CVE-EXAMPLE-1  │ CRITICAL │ 1.1.1-old     │ 1.1.1-fixed   │
│ libssl       │ CVE-EXAMPLE-2  │ HIGH     │ 1.1.1-old     │ 1.1.1-fixed   │
│ curl         │ CVE-EXAMPLE-3  │ HIGH     │ 7.x-old       │ 7.x-fixed     │
└──────────────┴────────────────┴──────────┴───────────────┴───────────────┘
```

The finding is in operating-system packages from the base image, not in `requirements.txt`. Installing a newer Python package will not fix OpenSSL in the image layer. The least disruptive first attempt is to move to a patched Python runtime image and stop running as root. If the application has no dependency on Debian 11 specifically, a slim patched runtime is a reasonable improvement.

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 appuser

COPY app.py .
USER 10001
CMD ["python", "app.py"]
```

This change improves three things at once. It moves to a maintained runtime line, reduces image size by using a slim image, and removes root as the runtime user. It does not prove the image is clean; it only changes the build instructions. The next step is to rebuild and rescan.

```bash
docker build -t security-demo:fixed .
trivy image --severity CRITICAL,HIGH --exit-code 1 security-demo:fixed
```

If the scan passes, the gate has evidence that the rebuilt image no longer contains critical or high findings according to the current database. If the scan still fails, inspect whether the remaining packages have fixed versions. A remaining high finding with no fix may require a temporary exception, but that exception should name the image digest, expiration date, service owner, and compensating controls such as network restrictions or WAF rules.

The debugging procedure generalizes to other gates. For SAST, identify the source, sink, and data path before changing code. For SCA, identify the direct dependency that pulls in the vulnerable transitive package before forcing overrides. For IaC, render the manifest that will actually be deployed before arguing with the scanner. For DAST, reproduce the request and response before assuming the tool is wrong.

| Debugging question | Why it matters | Example answer |
|---|---|---|
| Which tool failed? | Different tools inspect different artifacts and require different fixes | Trivy image scan, not Semgrep or filesystem SCA |
| What artifact was scanned? | A stale tag or wrong path can produce misleading results | `security-demo:${GITHUB_SHA}` built in the current job |
| What is the risk source? | Remediation depends on whether the issue is code, dependency, image, or config | OpenSSL package inherited from the base image |
| Is a fix available? | Determines whether to patch, upgrade, mitigate, or except | Fixed package exists in a newer base image |
| Did the final artifact pass? | The Dockerfile diff is not evidence by itself | Rebuilt image scans clean for critical and high findings |
| Is an exception needed? | Some risks cannot be fixed immediately without controlled acceptance | No exception needed after base image update |

This is the difference between a beginner and a senior response to security gates. A beginner sees a red check and tries random fixes until it turns green. A senior practitioner identifies the scanner, artifact, evidence, policy decision, remediation path, and verification point. The red check is only the entry point to a disciplined investigation.

---

## War Story: The Pipeline That Saved a Release Window

An e-commerce company planned a major checkout release shortly before its busiest sales weekend. The platform had strong unit tests and good deployment automation, but security checks were uneven. Some services ran SAST, a few teams used dependency scanning, and most container images were pushed to the registry without a blocking image scan. The organization believed it had "shifted left" because developers saw some warnings in pull requests, but the final runtime artifacts were not consistently inspected.

Two days before the release freeze, the platform team added a container scan to the shared build template. The first run was painful. Multiple services carried critical vulnerabilities in base-image packages, several images ran as root, and some services included build tools that were never needed at runtime. The findings were not new risks introduced that day; they were accumulated risk made visible by a stronger checkpoint.

The team triaged by exposure and exploitability rather than by raw count. Internet-facing checkout and payment services received immediate attention. Internal batch jobs with no external ingress were tracked separately with due dates. For the highest-risk services, teams updated base images, rebuilt artifacts, rescanned images, and deployed patched versions before the sale began. The release still shipped, but the pipeline forced the organization to spend scarce time on the risks that mattered most.

The lesson was not "add Trivy and everything is secure." The lesson was that CI/CD gates create decision points while change is still possible. Without the gate, the vulnerable images would have been deployed because application tests were green. With the gate, the team had evidence, prioritization, and a repeatable path to remediation.

A second lesson emerged during the postmortem. The scan job initially had access to the same credentials as the publish job because the workflow used broad permissions at the top level. The team corrected this by separating scan, publish, and deploy jobs, scoping permissions per job, and requiring review for workflow-file changes. The security tool improved artifact safety, but the pipeline itself also needed hardening.

This is a common pattern in DevSecOps maturity. The first win is visibility. The second win is gating. The third win is securing the delivery system that now has enough authority to block or ship production changes. Teams that stop at scanner installation miss the deeper platform engineering work.

---

## Building a Complete Secure Pipeline

A complete security pipeline should be understandable as a chain of evidence. The source stage proves the change does not expose secrets or alter delivery rules without review. The build stage proves the code, dependencies, image, and SBOM have been inspected. The policy stage proves the artifact is allowed to deploy. The publish stage proves only trusted branches and identities can release artifacts. The dashboard stage makes findings visible after the CI log disappears.

The following workflow is deliberately compact enough to study, but it includes the core pattern used in larger systems. It separates jobs, uploads SARIF, blocks on severe findings, and keeps publish permissions away from pull-request scan jobs. You would still tune it for a real organization by pinning third-party actions, adding CODEOWNERS for workflow changes, creating exception governance, and integrating with your vulnerability-management system.

```yaml
name: Secure CI/CD Pipeline

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: "23 3 * * 1"

permissions: {}

env:
  IMAGE_NAME: ghcr.io/${{ github.repository }}/app

jobs:
  secrets:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Detect committed secrets
        uses: gitleaks/gitleaks-action@v2

  sast:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Run Semgrep
        run: |
          docker run --rm \
            -v "${PWD}:/src" \
            semgrep/semgrep:latest \
            semgrep ci --config p/security-audit --sarif --output /src/semgrep.sarif
      - name: Upload SAST results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: semgrep.sarif

  dependency-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Scan dependencies and repository content
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          format: sarif
          output: trivy-fs.sarif
          exit-code: "1"
      - name: Upload dependency results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-fs.sarif

  image-scan:
    runs-on: ubuntu-latest
    needs: [secrets, sast, dependency-scan]
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Build image for scanning
        run: |
          docker build -t "${IMAGE_NAME}:${GITHUB_SHA}" .
      - name: Scan image before publication
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.IMAGE_NAME }}:${{ github.sha }}
          severity: CRITICAL,HIGH
          format: sarif
          output: trivy-image.sarif
          exit-code: "1"
      - name: Upload image scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-image.sarif

  iac-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Scan Kubernetes and Dockerfile configuration
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: config
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: "1"

  publish:
    runs-on: ubuntu-latest
    needs: [image-scan, iac-scan]
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Log in to registry
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io \
            --username "${{ github.actor }}" \
            --password-stdin
      - name: Build and push approved image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ env.IMAGE_NAME }}:${{ github.sha }}
```

This workflow has one important limitation: it rebuilds for publication after scanning because the example avoids a staging registry or cross-job artifact transfer. In a production pipeline, the stronger design is to build once, capture the image digest, scan the exact digest, sign or attest that digest, and promote that digest. The module keeps the YAML runnable while making the production improvement explicit.

The scheduled trigger is also intentional. Pull-request scans catch new changes, but they do not automatically respond when a vulnerability database learns about a new CVE affecting an old dependency. Scheduled scans rescan existing code and artifacts against updated advisories. This is how the pipeline helps during a zero-day response: it can answer "where are we affected?" without waiting for every team to open a pull request.

A mature pipeline produces dashboards, not only pass/fail checks. SARIF uploads make code findings visible in the repository. SBOMs make artifact contents queryable. Vulnerability-management tools help track ownership and due dates. Deployment systems can display whether the running artifact is signed and whether it passed policy. These reporting paths matter because vulnerabilities often require work across multiple sprints, teams, and services.

---

## Operating the Pipeline Over Time

The first version of a security pipeline is rarely the final version. As teams adopt it, they will discover noisy rules, missing ownership, slow jobs, stale exceptions, and gaps between scan output and remediation work. This is normal. The platform engineering task is to turn those discoveries into a better control system without quietly weakening the protections that made the pipeline valuable.

Performance tuning should preserve risk coverage. If a pipeline takes too long, split fast pull-request checks from deeper scheduled checks, cache vulnerability databases, run independent jobs in parallel, and trigger expensive scans only when relevant inputs change. Do not remove the only image scan because it is slow. Instead, scan the image when the Dockerfile, dependency files, application code, or base image changes, and run scheduled rescans to catch new advisories.

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│                             FAST AND DEEP SCANS                              │
├─────────────────────────────┬────────────────────────────────────────────────┤
│ Pull request path            │ Fast feedback on changed code and artifacts   │
│ Main branch path             │ Full artifact evidence before publication     │
│ Nightly or weekly path        │ Deeper scans and updated vulnerability data   │
│ Emergency path                │ Manual trigger across repos during incidents  │
└─────────────────────────────┴────────────────────────────────────────────────┘
```

Exception review should be part of normal operations. Every exception should expire, and the expiration should create visible work before the date arrives. If exceptions never expire, the pipeline becomes a documentation system for accepted risk rather than a control system. If exceptions are impossible, teams will find informal bypasses. The sustainable middle is disciplined, time-bound, owner-approved exception handling.

Finding ownership is just as important as finding detection. A vulnerability in a shared base image may belong to the platform team. A vulnerable application dependency may belong to the service team. A policy exception for a privileged workload may require both platform and security approval. If ownership is unclear, the pipeline can fail correctly while remediation stalls indefinitely.

Dashboards should emphasize decision quality rather than raw vulnerability counts. Raw counts reward low-value churn and punish larger services. Better measures include new critical findings introduced per week, mean time to remediate critical findings, percentage of images with current SBOMs, percentage of deployments using signed digests, number of expired exceptions, and policy violations by team or platform area.

| Operational metric | What it reveals | How to use it |
|---|---|---|
| New blocking findings by week | Whether teams are introducing fresh severe risk | Tune education, templates, and pre-merge controls |
| Mean time to remediate critical findings | Whether urgent risks are actually fixed | Escalate stuck ownership or missing patch paths |
| Images with SBOM and scan evidence | Whether artifacts are observable after build | Improve build templates and registry metadata |
| Deployments using signed digests | Whether production runs the artifact that passed gates | Tighten promotion and admission controls |
| Expired exceptions | Whether risk acceptance is being governed | Review or revoke stale approvals |
| Scanner runtime by job | Whether security feedback is slowing delivery unnecessarily | Cache, parallelize, split triggers, or resize runners |

The strongest pipelines also teach. A good finding links to remediation guidance, shows the exact file or package, explains why the policy blocks, and points to the team that owns exceptions. A bad finding says "security failed" and forces developers to search logs. Every confusing failure is an opportunity to improve the developer experience and reduce future bypass pressure.

---

## Did You Know?

1. **SARIF is useful because it separates finding data from scanner branding.** When tools emit SARIF, repositories and dashboards can show code-scanning findings consistently, which makes it easier to compare tools, migrate scanners, and preserve historical findings across pipeline changes.

2. **SBOMs are most valuable after an incident, not only during normal builds.** When a new vulnerability is announced, teams with searchable SBOMs can ask which images contain the affected package instead of manually inspecting every repository and Dockerfile.

3. **A mutable tag can make a security gate meaningless.** If the pipeline scans one image behind `latest` and later deploys a different image behind the same tag, the scan evidence no longer describes the running artifact.

4. **Secret rotation is part of secret detection.** A pipeline that finds a committed token but does not trigger revocation has only identified the exposure; the credential remains dangerous until it is invalidated or scoped out of use.

---

## Common Mistakes

| Mistake | Why it causes trouble | Better approach |
|---|---|---|
| Scanning after pushing trusted images | A vulnerable artifact can be consumed by another deployment path before the scan result is reviewed | Build, scan, sign or attest, then publish or promote the approved digest |
| Giving every job broad permissions | A compromised scanner, test, or pull-request job can steal publish or deployment credentials | Use workflow-level `permissions: {}` and grant only job-specific permissions |
| Blocking all scanner output without tuning | Developers see noise as arbitrary failure and start looking for bypasses | Block severe high-confidence risks, baseline legacy findings, and tune rules with owners |
| Treating `continue-on-error` as harmless | Security jobs may fail while the workflow still appears successful | Use it only when a later gate job explicitly evaluates the result and blocks if needed |
| Scanning templates instead of rendered manifests | Helm, Kustomize, or environment values may create unsafe final YAML not visible in source templates | Render the deployment artifact and scan the exact manifest intended for the environment |
| Using mutable tags for promotion | The deployed artifact may differ from the scanned artifact | Promote image digests and preserve provenance from build through deployment |
| Ignoring transitive dependencies | Vulnerable packages can enter through libraries the team never directly selected | Inspect dependency trees, update direct parents, use overrides carefully, and verify tests |
| Creating permanent exceptions | Temporary risk acceptance silently becomes normal policy | Require owner, justification, compensating control, review link, and expiration date |

---

## Quiz: Apply the Concepts

### Question 1

Your team adds container scanning to a service that has passed unit tests for months. The first scan blocks the pull request because the base image contains a critical OpenSSL vulnerability. The service team argues that their code does not call OpenSSL directly and asks you to disable the gate for this repository. What should you do?

<details>
<summary>Show Answer</summary>

Do not disable the gate simply because the vulnerable package is inherited from the base image. The final image still contains the vulnerable package, and attackers care about what is present in the runtime environment, not whether the application team intentionally imported it. First confirm the scanned artifact is the current image and that the finding has a fixed version. Then choose the least risky remediation, usually updating to a patched base image or a smaller runtime image.

If the service is internet-facing or handles sensitive data, blocking is appropriate for a critical vulnerability unless there is a documented reason the package is not exploitable and an approved exception exists. If no fixed version exists, create a time-bound exception only with compensating controls, an owner, and a review date. The important practitioner move is to resolve the risk source rather than weakening the control for the whole repository.

</details>

### Question 2

A pull request from a fork changes application code and triggers a scan job. The same workflow also contains a publish job with access to a package registry token, but the publish job is guarded by `if: github.ref == 'refs/heads/main'`. A teammate says this is enough because forked pull requests cannot satisfy that condition. What risk remains, and how would you improve the design?

<details>
<summary>Show Answer</summary>

The remaining risk is that broad workflow-level permissions or secrets may still be available to jobs that do not need them, and future workflow edits may accidentally change the condition or add a privileged step to the untrusted path. Conditional execution is useful, but it is not a substitute for least privilege. The scan job should run with read-only permissions and no publish token, while the publish job should receive package or OIDC permissions only on trusted branches and protected environments.

A stronger design sets `permissions: {}` at the workflow level, grants `contents: read` to scan jobs, grants `packages: write` or `id-token: write` only to the publish job, and protects workflow-file changes with CODEOWNERS. This way, even if untrusted code affects a scanner or test process, the job boundary prevents access to publish credentials.

</details>

### Question 3

Your SCA tool reports a critical vulnerability in a transitive dependency. The direct dependency that pulls it in is used only by an optional reporting feature, and the vulnerable function is not called by your current code. The service is internal but processes customer data. Should the gate block the merge?

<details>
<summary>Show Answer</summary>

The answer requires risk evaluation, not a blind yes or no. Because the vulnerability is critical and the service processes customer data, you should treat the finding seriously even if the vulnerable function is not currently called. First inspect the dependency tree to identify the direct parent, check whether a fixed version exists, and evaluate reachability with tests, code review, or a tool that supports reachability analysis.

If the fix is straightforward, block the merge and update the dependency because the cost of remediation is lower than carrying the risk. If the fix is disruptive and reachability evidence is strong, you may allow a time-bound exception with an owner, due date, and compensating control. The gate policy should at least prevent the team from ignoring the finding without documented analysis.

</details>

### Question 4

A Kubernetes deployment passes SAST, SCA, and container scanning, but the pre-deploy IaC scan fails because the rendered manifest sets `privileged: true` and mounts the host filesystem. The application team says the container needs this for debugging in production. How should the pipeline handle the release?

<details>
<summary>Show Answer</summary>

The pipeline should block the production release by default because privileged containers and host filesystem mounts create a large escape and lateral-movement risk. Passing code and image scans does not make the deployment safe if the runtime permissions are excessive. The team should explain the debugging requirement and replace it with a safer operational pattern such as ephemeral debug containers, restricted staging diagnostics, logs, metrics, traces, or a break-glass process with approval and audit.

If there is a truly exceptional operational need, it should go through an explicit exception process with expiration, compensating controls, and environment scoping. The key alignment point is that IaC scanning protects runtime configuration, which earlier stages cannot fully evaluate.

</details>

### Question 5

Developers complain that the security pipeline now takes twenty minutes on every pull request. The slowest steps are DAST and full dependency rescans. The security team wants to keep coverage because a recent incident came from an old dependency discovered after a new advisory. What design would reduce wait time without removing protection?

<details>
<summary>Show Answer</summary>

Split the pipeline into fast pull-request checks, main-branch checks, scheduled deep scans, and manual emergency scans. Pull requests should run fast SAST, secret scanning, dependency checks when dependency files change, and image scans when image inputs change. DAST can run against preview environments for changed services or run a smaller smoke-security suite on pull requests. Deeper DAST and full dependency rescans can run nightly or weekly, with alerting when new severe findings appear.

Also cache vulnerability databases, run independent jobs in parallel, and preserve branch protection for the checks that must block merges. This approach keeps fast feedback for developers while still rescanning existing code against updated vulnerability data.

</details>

### Question 6

Your organization added a baseline file for existing vulnerabilities so teams can continue shipping while they remediate old findings. Three months later, the baseline has grown because teams keep adding new exceptions for high vulnerabilities. What governance change should you recommend?

<details>
<summary>Show Answer</summary>

Recommend treating the baseline as a burn-down control, not as a general exception bucket. Existing findings should have owners and due dates, while new high or critical findings should be blocked unless an explicit exception is approved. Each exception should include the finding, artifact, justification, compensating control, approving owner, and expiration date. Expired exceptions should fail the gate or trigger escalation before release.

You should also report new findings separately from legacy findings. If the baseline is growing, the pipeline is no longer preventing risk accumulation. The governance change is to make new risk visible and costly to accept while giving teams a managed path to reduce old risk.

</details>

### Question 7

A deployment job uses `myapp:latest`, but the image scan job scans `myapp:${{ github.sha }}`. Both tags are created during the workflow. A production incident reveals that `latest` pointed to a different image than the commit SHA image that passed the scan. What pipeline design flaw caused this, and how should it be fixed?

<details>
<summary>Show Answer</summary>

The flaw is that the pipeline scanned one artifact and deployed another artifact identified by a mutable tag. Tags can move, so the scan evidence did not prove the safety of the deployed image. The fix is to promote immutable image digests through the pipeline. The build job should output the digest, the scan job should scan that digest, the signing or attestation step should bind evidence to that digest, and the deployment job should deploy the approved digest.

Using tags for human readability is fine, but gates and deployments should rely on immutable references. This ensures that production runs the exact artifact that passed security checks.

</details>

---

## Hands-On Exercise: Build and Debug a Security Pipeline

In this exercise, you will create a small intentionally vulnerable repository, add a security pipeline, observe failures, and fix the issues using the same reasoning process taught in the module. You do not need a Kubernetes cluster for the first parts. If you do have a local cluster, you can use `kubectl`, often shortened to `k` after creating an alias such as `alias k=kubectl`, for the optional manifest validation step.

### Part 1: Create the Sample Project

Create a new test repository outside any production codebase. The application contains intentional issues: unsafe SQL construction, command execution, vulnerable dependencies, a hardcoded-looking token, an unsafe Dockerfile, and an unsafe Kubernetes manifest. The point is not to write a good service; the point is to give the pipeline real findings to catch.

```bash
mkdir devsecops-pipeline-demo
cd devsecops-pipeline-demo
git init

cat > app.py << 'EOF'
import os
import sqlite3

API_KEY = "sk_live_demo_token_for_training_only"

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()

def run_command(cmd):
    return os.system(cmd)

if __name__ == "__main__":
    print(get_user("1"))
EOF

cat > requirements.txt << 'EOF'
requests==2.25.0
pyyaml==5.3
EOF

cat > Dockerfile << 'EOF'
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER root
CMD ["python", "app.py"]
EOF

mkdir -p k8s
cat > k8s/pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: devsecops-demo
spec:
  containers:
    - name: app
      image: devsecops-demo:latest
      securityContext:
        privileged: true
        runAsUser: 0
      resources: {}
EOF
```

Commit the starting point so pull-request workflows have a clear diff once you push to a remote repository. If you are testing locally only, you can still run some tools with Docker, but the GitHub Actions workflow requires a GitHub repository.

```bash
git add app.py requirements.txt Dockerfile k8s/pod.yaml
git commit -m "Add intentionally vulnerable demo service"
```

### Part 2: Add the Security Workflow

Create the workflow directory and add a compact pipeline. This workflow runs secret scanning, SAST, dependency scanning, image scanning, and IaC scanning. It uploads SARIF where supported and blocks on severe findings.

```bash
mkdir -p .github/workflows

cat > .github/workflows/security.yml << 'EOF'
name: Security Pipeline

on:
  pull_request:
  push:
    branches: [main]

permissions: {}

jobs:
  secrets:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Detect secrets
        uses: gitleaks/gitleaks-action@v2

  sast:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Run Semgrep
        run: |
          docker run --rm \
            -v "${PWD}:/src" \
            semgrep/semgrep:latest \
            semgrep scan --config p/python --sarif --output /src/semgrep.sarif /src
      - name: Upload SAST SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: semgrep.sarif

  dependency-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Scan dependencies
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          format: sarif
          output: trivy-fs.sarif
          exit-code: "1"
      - name: Upload dependency SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-fs.sarif

  image-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t devsecops-demo:${{ github.sha }} .
      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: devsecops-demo:${{ github.sha }}
          severity: CRITICAL,HIGH
          format: sarif
          output: trivy-image.sarif
          exit-code: "1"
      - name: Upload image SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-image.sarif

  iac-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Scan configuration
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: config
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: "1"
EOF
```

Commit the workflow separately. This makes it easier to review which change added the security control and which later changes remediate findings.

```bash
git add .github/workflows/security.yml
git commit -m "Add security pipeline"
```

### Part 3: Predict the Failures Before Running

Before pushing, predict which job should catch each issue. This is active practice, not busywork. If you can map issue to scanner before seeing CI output, you are learning to reason about pipeline coverage rather than memorizing tool names.

- [ ] The fake API key should be flagged by the secrets job or SAST secret rules.
- [ ] The SQL query string should be flagged by SAST because request-like input reaches SQL execution without binding.
- [ ] The old Python dependencies should be flagged by dependency scanning if current advisories include severe findings.
- [ ] The old base image and root user should be evaluated by image and configuration scans.
- [ ] The privileged Kubernetes pod should be flagged by IaC scanning before deployment.

### Part 4: Fix the Application and Artifact Risks

Fix the SQL query by using parameter binding, remove command execution, replace the demo token with an environment variable, update dependencies, and harden the Dockerfile. These changes address different evidence sources, so keep the mapping clear as you edit.

```bash
cat > app.py << 'EOF'
import os
import sqlite3

API_KEY = os.environ.get("DEMO_API_KEY", "")

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    query = "SELECT * FROM users WHERE id = ?"
    return conn.execute(query, (user_id,)).fetchone()

def describe_user_lookup(user_id):
    return f"Looking up user id {user_id}"

if __name__ == "__main__":
    print(describe_user_lookup("1"))
EOF

cat > requirements.txt << 'EOF'
requests==2.32.3
pyyaml==6.0.2
EOF

cat > Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 appuser
COPY app.py .
USER 10001
CMD ["python", "app.py"]
EOF
```

Harden the Kubernetes manifest by removing privileged mode, running as non-root, dropping capabilities, and defining resources. The image tag remains local for the exercise, but in a real deployment you would promote an immutable digest.

```bash
cat > k8s/pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: devsecops-demo
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: devsecops-demo:training
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      resources:
        requests:
          cpu: 50m
          memory: 64Mi
        limits:
          cpu: 250m
          memory: 256Mi
EOF
```

Commit the remediation. The commit message should say what risk was fixed, not only that CI is green.

```bash
git add app.py requirements.txt Dockerfile k8s/pod.yaml
git commit -m "Remediate demo security findings"
```

### Part 5: Verify Locally Where Possible

If Docker is available, build and scan the image locally. Local scans do not replace CI, but they reduce feedback time and help you understand what the pipeline will see.

```bash
docker build -t devsecops-demo:local .
docker run --rm devsecops-demo:local
```

If Trivy is installed locally, run the same categories of scans. These commands are optional if you rely on GitHub Actions, but they are useful for debugging.

```bash
trivy fs --severity CRITICAL,HIGH --exit-code 1 .
trivy image --severity CRITICAL,HIGH --exit-code 1 devsecops-demo:local
trivy config --severity CRITICAL,HIGH --exit-code 1 .
```

If you have a Kubernetes 1.35+ cluster and `kubectl` configured, you can validate the manifest without applying it. After explaining the alias once, you may use `k` for shorter commands in your own terminal.

```bash
kubectl apply --dry-run=server -f k8s/pod.yaml
```

### Part 6: Explain the Gate Decision

Write a short note in your pull request or learning journal explaining which jobs failed, what artifact each job inspected, what remediation you chose, and how you verified the result. The goal is to practice the senior debugging procedure: scanner, artifact, evidence, policy, remediation, verification.

### Success Criteria

- [ ] The workflow includes separate jobs for secrets, SAST, dependency scanning, image scanning, and IaC scanning.
- [ ] Scan jobs use least-privilege permissions rather than broad workflow-level write access.
- [ ] The initial vulnerable version produces meaningful security findings when pushed or scanned locally.
- [ ] The remediation changes address the actual risk source rather than merely suppressing the scanner.
- [ ] SARIF upload is configured for scanner output where the workflow produces SARIF.
- [ ] The Dockerfile no longer runs the application as root and uses a more current slim runtime image.
- [ ] The Kubernetes manifest no longer uses privileged mode and includes a non-root security context.
- [ ] Your written explanation identifies which artifact each security gate inspected and why the final decision passed or failed.

---

## Next Module

Continue to [Module 4.4: Supply Chain Security](../module-4.4-supply-chain-security/) to learn how source identity, artifact provenance, signing, SBOMs, dependency trust, and deployment admission fit together across the full software supply chain.
