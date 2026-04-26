---
title: "Module 12.1: SonarQube - The Code Quality Platform"
slug: platform/toolkits/security-quality/code-quality/module-12.1-sonarqube
sidebar:
  order: 2
---

# Module 12.1: SonarQube - The Code Quality Platform

## Complexity: [COMPLEX]

## Time to Complete: 50-60 minutes

## Prerequisites

Before starting this module, you should have completed:

- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/) for CI/CD, shift-left security, and policy-as-code context
- [CI/CD Pipelines Toolkit](/platform/toolkits/cicd-delivery/ci-cd-pipelines/) for pipeline design and merge protection concepts
- Basic experience with one application language such as Java, Python, JavaScript, TypeScript, Go, or C#
- Basic Docker and Kubernetes knowledge, including Services, Deployments, Secrets, PVCs, and Ingress

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a SonarQube rollout that separates developer feedback, CI analysis, server processing, and long-term quality reporting.
- **Configure** quality gates and analysis scope so new changes are blocked for meaningful defects without freezing delivery on legacy debt.
- **Evaluate** SonarQube metrics, security hotspots, coverage data, and duplication findings to choose a remediation plan that fits team risk.
- **Debug** failed scans, failed gates, missing coverage reports, and pull request decoration issues by tracing the scanner-to-server workflow.
- **Implement** valid GitHub Actions, GitLab CI, local scanner, Docker Compose, and Kubernetes examples that learners can adapt safely.

## Why This Module Matters

A platform engineer joins a payments team after a damaging production incident. The incident report says the direct cause was a retry bug, but the timeline tells a deeper story: the same service had duplicated validation paths, weak tests around idempotency, a complex conditional nobody wanted to touch, and several warnings that code review treated as noise. The team was not careless; it was operating without a reliable way to see quality risk accumulating across hundreds of small commits.

The new platform engineer faces a common problem. Developers already have linters, reviewers already have checklists, and managers already have dashboards, yet none of those things consistently answers the question that matters before a merge: does this change make the software more fragile, less secure, or harder to maintain? Without an automated quality gate, every review depends on whoever happens to notice the risky part of the diff that day.

SonarQube gives teams a shared inspection system for code quality and code security. It does not replace design review, threat modeling, or tests, but it makes repeatable checks visible and enforceable. A scanner analyzes source code and test reports, the server stores metrics and issues, and quality gates turn those metrics into merge decisions. The value is not that SonarQube can assign a number to every problem; the value is that teams can stop arguing from vague impressions and start improving from observable evidence.

The senior-level skill is knowing how to adopt SonarQube without turning it into a delivery blocker or a vanity dashboard. A strict gate on all legacy code can paralyze a codebase. A weak gate that never fails becomes decoration. A coverage target with no behavior focus creates tests that execute code without proving anything. This module teaches the operating model: start with new code, make gates meaningful, wire feedback close to developers, and use metrics to guide engineering judgment instead of replacing it.

## Core Content

### 1. Build the Mental Model Before Installing Anything

SonarQube is easiest to understand as a feedback loop, not as a single web application. Developers get early feedback from SonarLint in the IDE, CI runs the scanner against the exact commit or pull request, the SonarQube server processes and stores analysis results, and repository checks decide whether a change can merge. If one part of that loop is missing, quality feedback either arrives too late, disappears into a dashboard, or becomes inconsistent across machines.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SONARQUBE FEEDBACK LOOP                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEVELOPER WORKSTATION                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ IDE + SonarLint                                                       │  │
│  │ - Fast local feedback while editing                                   │  │
│  │ - Connected mode can sync project rules from the server               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           │ git push or pull request                         │
│                           ▼                                                  │
│  CI/CD PIPELINE                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Build + test + coverage report                                        │  │
│  │ SonarScanner reads code, metadata, and reports                        │  │
│  │ Scanner uploads an analysis report to SonarQube                       │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           │ analysis report                                  │
│                           ▼                                                  │
│  SONARQUBE SERVER                                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Web UI and API      Compute Engine      Search Index                  │  │
│  │ Project settings    Issue processing    Fast issue navigation         │  │
│  │ Quality gates       Metric history      Code search and filtering     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           │ gate status and pull request decoration           │
│                           ▼                                                  │
│  REPOSITORY PLATFORM                                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Required check passes or fails before merge                           │  │
│  │ Reviewers see changed-code issues in the pull request                 │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

The scanner does not do all useful work by itself. It needs context from the build, including compiled classes for some languages, coverage reports from the test runner, branch or pull request metadata from CI, and a token that allows it to upload results. When a team says "SonarQube missed our coverage," the usual root cause is not that SonarQube cannot measure coverage; it is that the pipeline never produced the report, wrote it to a different path, or excluded the files before the scanner could match them.

| Component | Primary job | What platform engineers must verify |
|-----------|-------------|--------------------------------------|
| SonarLint | Shows issues while the developer edits code | Connected mode points to the same project and rules as CI |
| SonarScanner | Analyzes code and uploads a report | Build outputs, coverage reports, project key, and token are present |
| Web UI and API | Exposes projects, gates, issues, and administration | Authentication, project permissions, and gate ownership are clear |
| Compute Engine | Processes submitted analysis tasks asynchronously | Background task queues are healthy and sized for analysis volume |
| Search index | Supports issue navigation and code search | Storage and memory are sufficient for the project count |
| PostgreSQL database | Stores projects, metrics, issues, and history | Backups, upgrades, and storage growth are treated as production concerns |

A good rollout starts by deciding where each feedback loop should fire. SonarLint is for fast personal correction, so it should catch simple issues before code leaves the laptop. Pull request analysis is for team-level review, so it should focus on changed code and enforce the quality gate. Main branch analysis is for historical trend, so it should be stable, complete, and used for dashboards. Mixing these purposes leads to frustration, such as developers waiting several minutes for CI to tell them about a trivial unused variable.

> **Pause and predict:** If a team installs SonarQube but only analyzes the `main` branch after merge, which class of problems will still reach production review too late? Think about whether developers see the issue before or after the decision point, then compare your answer with the next paragraph.

Analyzing only after merge turns SonarQube into a reporting tool rather than a merge guard. It can still show trends, help with cleanup, and identify hotspots, but it cannot prevent a risky change from entering the default branch. For platform teams, the critical design choice is to connect pull request analysis to branch protection or merge checks, then keep the gate focused enough that failures are actionable within a normal review cycle.

### 2. Interpret SonarQube Metrics as Signals, Not Absolute Truth

SonarQube groups findings into reliability, security, maintainability, coverage, duplication, and security review signals. These categories are useful because they answer different operational questions. Reliability asks whether code is likely to fail at runtime. Security asks whether code has a known exploitable pattern. Maintainability asks whether future change will become more expensive. Coverage asks whether tests executed changed code, while duplication asks whether the same logic is being maintained in several places.

```text
SONARQUBE QUALITY MODEL
──────────────────────────────────────────────────────────────────────────────

RELIABILITY
├── Main finding type: bugs
├── Typical meaning: code is probably wrong or unsafe at runtime
├── Example: dereferencing a possibly null object after a failed lookup
└── Operational question: could this fail for a user or operator?

SECURITY
├── Main finding type: vulnerabilities
├── Typical meaning: code contains a likely exploitable weakness
├── Example: building SQL with untrusted input instead of parameters
└── Operational question: could an attacker abuse this path?

SECURITY REVIEW
├── Main finding type: security hotspots
├── Typical meaning: a human must inspect context before deciding risk
├── Example: cryptography, random number generation, permissive CORS
└── Operational question: has a qualified reviewer accepted or fixed it?

MAINTAINABILITY
├── Main finding type: code smells
├── Typical meaning: the code works now but is harder to change safely
├── Example: duplicated logic, deep nesting, excessive method complexity
└── Operational question: will future fixes become slower or riskier?

COVERAGE
├── Main input: test coverage report produced outside SonarQube
├── Typical meaning: tests executed these lines or branches
├── Example: JaCoCo XML, lcov.info, coverage.xml, OpenCover XML
└── Operational question: did changed behavior get exercised by tests?

DUPLICATION
├── Main signal: repeated blocks or repeated lines
├── Typical meaning: future fixes may need coordinated edits
├── Example: copied validation rules in two services
└── Operational question: will one bug fix leave another copy broken?
```

The distinction between vulnerabilities and hotspots matters because automation can detect patterns better than it can understand intent. A string-concatenated SQL query using raw request input is often a vulnerability because the exploit path is direct. A cryptographic library call may be a hotspot because the same API could be acceptable or dangerous depending on mode, key management, randomness, and business context. Treating every hotspot as a vulnerability overwhelms teams; ignoring hotspots teaches reviewers to skip the exact places where context matters most.

Technical debt estimates are also signals rather than precise schedules. SonarQube assigns remediation effort to issues and can aggregate those estimates by file, category, or project. That helps a team find concentration, but it does not mean a developer can literally fix a project in the exact number of displayed hours. The estimate is best used comparatively: this file has much more maintainability risk than nearby files, this subsystem is getting worse over time, or this rule is generating noise that needs calibration.

```text
TECHNICAL DEBT TRIAGE VIEW
──────────────────────────────────────────────────────────────────────────────

Project: billing-service

Debt by category:
├── Maintainability findings: high volume, moderate risk
│   ├── Complex conditions in invoice eligibility
│   ├── Duplicate mapping logic in import and export paths
│   └── Long service methods that mix validation, persistence, and retries
├── Reliability findings: lower volume, high urgency
│   ├── Possible null dereference after customer lookup
│   └── Ignored return value from transaction commit helper
└── Security review findings: requires human judgment
    ├── Manual review needed for token generation
    └── Manual review needed for webhook signature verification

Practical remediation order:
1. Fix reliability findings on changed code before merge.
2. Review security hotspots owned by the current feature team.
3. Refactor high-change files when the next feature touches them.
4. Avoid broad cleanup sprints unless the business risk justifies them.
```

| Signal | Strong use | Weak use |
|--------|------------|----------|
| Bugs | Block changed code that is likely to fail at runtime | Treat every historical bug as a reason no feature can merge |
| Vulnerabilities | Escalate likely exploitable patterns quickly | Assume the scanner replaces threat modeling |
| Hotspots | Force documented human review for risky constructs | Count unreviewed hotspots as automatic proof of compromise |
| Code smells | Prioritize refactoring where change frequency is high | Spend weeks fixing low-risk smells in untouched code |
| Coverage | Verify changed behavior has tests | Reward tests with no assertions or no behavioral value |
| Duplication | Remove copy-paste logic that changes often | Refactor generated or intentionally mirrored code |

> **Pause and decide:** A pull request adds a new payment retry path. SonarQube reports high coverage, one duplicated block, and an unreviewed hotspot around token generation. Which finding should the reviewer discuss first, and why? The strongest answer starts from business risk, not from whichever metric is easiest to improve.

A senior reviewer would usually start with the hotspot because payment token generation is security-sensitive and requires context. High coverage is useful, but it does not prove the token is generated safely. The duplicated block matters too, especially if it copies retry logic from another path, but it is usually less urgent than a security-sensitive construct that has not been reviewed. This is the pattern to practice: use SonarQube to focus attention, then apply engineering judgment to the actual change.

### 3. Design Quality Gates That Improve Delivery Instead of Freezing It

A quality gate is a decision rule. It takes metrics from an analysis and returns pass or fail. The difficult part is not creating a strict gate; the difficult part is creating a gate that blocks the right changes at the right time. For most existing codebases, the safest starting point is to gate new code, which means code introduced or changed during the configured new-code period, branch, or pull request.

```text
QUALITY GATE STRATEGY
──────────────────────────────────────────────────────────────────────────────

Bad first gate for a legacy application:
├── Overall coverage must be at least 80 percent
├── Overall maintainability rating must be A
├── Total bugs must be zero
└── Result: normal feature work is blocked by old debt outside the diff

Better first gate for adoption:
├── Coverage on new code must meet the agreed threshold
├── Duplications on new code must stay low
├── Reliability rating on new code must be A
├── Security rating on new code must be A
├── Security hotspots on new code must be reviewed
└── Result: each change must be clean without requiring a rewrite first

Mature gate after adoption:
├── Keep all new-code conditions
├── Add a gradual overall coverage floor for critical services
├── Add stricter rules for regulated or externally exposed systems
└── Result: quality improves without making the gate impossible to pass
```

Gating on new code expresses the "do not make it worse" operating principle. It allows a team to keep shipping while preventing new debt from entering the codebase unchecked. Over time, the team can raise expectations, add service-specific policies, and schedule targeted cleanup for high-risk areas. This approach is more sustainable than trying to fix the entire history of a codebase before the first gate is enabled.

| Gate condition | Good default for adoption | When to tighten it |
|----------------|---------------------------|--------------------|
| Reliability rating on new code | A | Immediately for user-facing and critical workflows |
| Security rating on new code | A | Immediately for internet-facing and regulated services |
| Security hotspots reviewed on new code | 100 percent | Keep strict; adjust reviewer workflow, not the threshold |
| Coverage on new code | 80 percent when tests are meaningful | Raise only after teams have stable test patterns |
| Duplicated lines on new code | Less than or equal to 3 percent | Tighten for libraries and shared domain logic |
| Maintainability rating on new code | A | Keep strict, but tune noisy rules before broad enforcement |
| Overall coverage | Observe first, then set floor cautiously | Use for mature services with reliable test data |

A gate should fail in a way that a developer can fix inside the pull request. If a new change introduces a likely null dereference, the fix belongs in that change. If a new change has no tests around a branch-heavy calculation, the fix belongs in that change. If a new change touches an old file that already has hundreds of smells unrelated to the diff, the gate should not require the author to repair all of history before merging a small behavioral fix.

> **What would happen if:** A platform team sets "overall coverage must be 80 percent" on a service that currently has low coverage and many urgent feature branches. Predict the human behavior this gate will create before predicting the metric behavior.

The likely human behavior is workarounds. Developers may add shallow tests that execute code without assertions, split changes to avoid touching difficult files, request exceptions for urgent fixes, or pressure platform owners to disable the gate. The metric may improve briefly, but trust in the quality program will decline. A better rollout starts with new-code coverage, teaches what behavior-focused tests look like, and treats overall coverage as a staged improvement target for services where the team has capacity to improve legacy tests.

### 4. Configure Projects So the Scanner Sees the Same System Developers Build

The most common SonarQube implementation failures are configuration mismatches. The scanner analyzes a directory tree, but the build output lives elsewhere. The test runner creates a coverage report, but the path in `sonar-project.properties` points to a stale filename. A monorepo has several services, but the team analyzes the whole repository as one project and cannot tell which service owns which gate failure. These are design problems, not scanner mysteries.

A minimal configuration should identify the project, define source and test roots, point to coverage and test reports, and exclude files that are generated or outside the learning signal. Exclusions are not a way to hide embarrassing code. They are a way to keep generated clients, vendored dependencies, build outputs, snapshots, and test fixtures from distorting metrics that are supposed to guide engineering decisions.

```properties
# sonar-project.properties for a Java service built with Gradle or Maven

sonar.projectKey=mycompany_billing-service
sonar.projectName=Billing Service
sonar.projectVersion=1.0

sonar.sources=src/main
sonar.tests=src/test
sonar.sourceEncoding=UTF-8

sonar.java.binaries=build/classes/java/main
sonar.java.test.binaries=build/classes/java/test
sonar.coverage.jacoco.xmlReportPaths=build/reports/jacoco/test/jacocoTestReport.xml
sonar.junit.reportPaths=build/test-results/test

sonar.exclusions=\
  **/generated/**,\
  **/build/**,\
  **/node_modules/**

sonar.coverage.exclusions=\
  **/config/**,\
  **/*Application.java,\
  **/dto/**
```

The exclusion choices in this example are intentionally narrow. Generated code should usually be excluded because developers do not maintain it directly and its style is controlled by tooling. Application bootstrapping code may be excluded from coverage when testing it adds little value compared with testing business behavior. DTOs may be excluded from coverage if they contain no logic, but that decision should be revisited if validation or transformation logic starts appearing in those classes.

For Python, the scanner usually consumes coverage generated by `pytest` and `coverage.py`. The scanner does not run tests on its own, so the pipeline must produce `coverage.xml` before analysis. If the report contains paths relative to a different working directory, SonarQube may show coverage as missing even though the test command succeeded.

```properties
# sonar-project.properties for a Python service

sonar.projectKey=mycompany_inventory-api
sonar.projectName=Inventory API

sonar.sources=src
sonar.tests=tests
sonar.sourceEncoding=UTF-8

sonar.python.version=3.12
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=pytest-report.xml

sonar.exclusions=\
  **/.venv/**,\
  **/__pycache__/**,\
  **/migrations/**
```

```bash
# Example test command that creates the reports referenced above.
.venv/bin/python -m pytest \
  --junitxml=pytest-report.xml \
  --cov=src \
  --cov-report=xml:coverage.xml
```

Monorepos need a sharper ownership decision. One approach is a single SonarQube project for the whole repository, which gives one dashboard and one gate. That can work for a small monorepo owned by one team. Larger monorepos usually work better with separate project keys per service or package, because each team gets a gate aligned to its release responsibility and can tune exclusions without affecting unrelated services.

```text
MONOREPO ANALYSIS OPTIONS
──────────────────────────────────────────────────────────────────────────────

Option A: One SonarQube project for the whole repository
├── Simpler setup
├── One quality gate for all code
├── Useful when one team owns the complete repository
└── Risk: failures can be hard to assign in a large organization

Option B: One SonarQube project per service or package
├── Clear ownership
├── Service-specific gates and exclusions
├── Better dashboards for platform and product teams
└── Cost: CI configuration and project administration are more explicit

Option C: Hybrid model
├── Critical services get separate projects
├── Shared libraries get separate projects when ownership differs
├── Small utilities remain in a grouped project
└── Useful transition path for messy repositories
```

```properties
# sonar-project.properties for analyzing a single service inside a monorepo

sonar.projectKey=mycompany_monorepo_billing-api
sonar.projectName=Monorepo / Billing API

sonar.sources=services/billing-api/src
sonar.tests=services/billing-api/tests

sonar.python.version=3.12
sonar.python.coverage.reportPaths=services/billing-api/coverage.xml

sonar.exclusions=\
  services/billing-api/src/generated/**,\
  services/billing-api/.venv/**
```

> **Pause and diagnose:** A team says its SonarQube project shows zero coverage, but the CI test step prints "coverage.xml written." What are three checks you would make before blaming SonarQube itself?

The first check is whether the scanner runs from the directory where `sonar-project.properties` expects the report. The second is whether the report paths inside the coverage file match the source paths SonarQube analyzes. The third is whether exclusions remove the source files before coverage can attach to them. For compiled languages, add a fourth check: verify the build output exists before scanning, because some analyzers need binaries to reason about code accurately.

### 5. Put SonarQube in CI Without Copy-Paste Traps

A valid CI example must use real action versions and make the quality gate result visible to the repository platform. Internal scripts or placeholder `uses` tags do not teach learners; they create broken workflows. The examples below use public GitHub Actions with explicit versions and keep the scan command close to the build and test steps that produce its inputs.

For GitHub Actions, the scan should run after checkout, build, and test report generation. Fetching full history is recommended because SonarQube can use blame and branch context more accurately when the checkout is not shallow. If your organization pins every action by commit SHA, replace version tags with reviewed SHAs through your normal dependency process; the important point is that the `uses` value references a real action, not a local script.

```yaml
# .github/workflows/sonarqube.yml
name: SonarQube Analysis

on:
  push:
    branches:
      - main
  pull_request:
    types:
      - opened
      - synchronize
      - reopened

jobs:
  analyze:
    name: Build, test, and analyze
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
    steps:
      - name: Check out source
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Set up JDK
        uses: actions/setup-java@v5
        with:
          distribution: temurin
          java-version: "21"

      - name: Cache SonarQube scanner packages
        uses: actions/cache@v4
        with:
          path: ~/.sonar/cache
          key: ${{ runner.os }}-sonar

      - name: Build and test
        run: ./gradlew clean test jacocoTestReport

      - name: Run SonarQube scan and wait for gate
        uses: SonarSource/sonarqube-scan-action@v7.1.0
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
        with:
          args: >
            "-Dsonar.projectKey=mycompany_billing-service"
            "-Dsonar.sources=src/main"
            "-Dsonar.tests=src/test"
            "-Dsonar.java.binaries=build/classes/java/main"
            "-Dsonar.coverage.jacoco.xmlReportPaths=build/reports/jacoco/test/jacocoTestReport.xml"
            "-Dsonar.qualitygate.wait=true"
            "-Dsonar.qualitygate.timeout=300"
```

This workflow uses `sonar.qualitygate.wait=true`, which makes the scanner wait for the server to process the analysis and return the gate status. That is simple and effective for many repositories. Some organizations prefer a separate quality gate action because they want to scan first, then perform a distinct status check from the generated analysis metadata. Both patterns can work; the platform requirement is that merge protection depends on the gate status, not merely on the scanner process starting successfully.

```yaml
# .github/workflows/sonarqube-gate-action.yml
name: SonarQube Gate With Separate Check

on:
  pull_request:
    types:
      - opened
      - synchronize
      - reopened

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Check out source
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Build and test
        run: ./gradlew clean test jacocoTestReport

      - name: Run SonarQube scan
        uses: SonarSource/sonarqube-scan-action@v7.1.0
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
        with:
          args: >
            "-Dsonar.projectKey=mycompany_billing-service"

      - name: Check SonarQube quality gate
        uses: SonarSource/sonarqube-quality-gate-action@v1.2.0
        timeout-minutes: 5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

GitLab CI follows the same sequence, but the scanner usually runs as a container image. The important settings are `GIT_DEPTH: "0"` for complete history, a persistent scanner cache, and `sonar.qualitygate.wait=true` if the job should fail when the quality gate fails. Use `sonar.token` or the `SONAR_TOKEN` environment variable rather than older authentication properties.

```yaml
# .gitlab-ci.yml
stages:
  - test
  - analyze

test:
  stage: test
  image: eclipse-temurin:21
  script:
    - ./gradlew clean test jacocoTestReport
  artifacts:
    paths:
      - build/reports/jacoco/test/jacocoTestReport.xml
      - build/classes/java/main
    expire_in: 1 day

sonarqube:
  stage: analyze
  image: sonarsource/sonar-scanner-cli:latest
  variables:
    SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar"
    GIT_DEPTH: "0"
  cache:
    key: "${CI_JOB_NAME}"
    paths:
      - .sonar/cache
  dependencies:
    - test
  script:
    - >
      sonar-scanner
      -Dsonar.projectKey="${CI_PROJECT_PATH_SLUG}"
      -Dsonar.sources=src/main
      -Dsonar.tests=src/test
      -Dsonar.java.binaries=build/classes/java/main
      -Dsonar.coverage.jacoco.xmlReportPaths=build/reports/jacoco/test/jacocoTestReport.xml
      -Dsonar.host.url="${SONAR_HOST_URL}"
      -Dsonar.qualitygate.wait=true
      -Dsonar.qualitygate.timeout=300
  allow_failure: false
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
```

The senior-level debugging habit is to follow the artifact chain. If the gate fails unexpectedly, check whether SonarQube is reporting real changed-code issues. If coverage is missing, confirm the report exists in the scan job and uses paths SonarQube can resolve. If pull request decoration is absent, check the edition and ALM integration settings, then confirm the scanner receives pull request metadata from CI. If the scanner fails before uploading, inspect credentials, host URL reachability, and whether the action or container version supports the runner environment.

```text
CI DEBUGGING PATH
──────────────────────────────────────────────────────────────────────────────

Gate failed
├── Open SonarQube project or pull request decoration
├── Identify which condition failed
├── Confirm the issue is on new code, not unrelated old code
└── Fix code, tests, or gate calibration depending on evidence

Coverage missing
├── Confirm test step generated a coverage report
├── Confirm scan step can read the same file path
├── Confirm source paths in report match sonar.sources
└── Confirm exclusions did not remove measured files

Scan failed before upload
├── Validate SONAR_HOST_URL from the runner
├── Validate SONAR_TOKEN permissions and project access
├── Check action, Java, scanner, and build tool versions
└── Review scanner logs before changing the quality gate

Pull request decoration missing
├── Confirm the repository integration is configured in SonarQube
├── Confirm pull request analysis is supported by the edition in use
├── Confirm CI event is a pull request event, not only a branch push
└── Confirm repository branch protection requires the expected check
```

### 6. Operate SonarQube as a Production Platform Service

Running SonarQube locally is useful for learning, but production operation deserves the same discipline as any internal developer platform service. The server stores project history, issue states, quality gate definitions, security hotspot review decisions, and authentication configuration. Losing that data damages trust because teams lose the context that explains why a finding was accepted, fixed, or suppressed.

For a local learning environment, Docker Compose is enough. The example below uses PostgreSQL, persists SonarQube data and extensions, and exposes the UI on `127.0.0.1:9000`. Some systems require increasing `vm.max_map_count` for the search engine; on managed developer machines, learners may need administrator rights for that setting.

```yaml
# docker-compose.yml
services:
  sonarqube:
    image: sonarqube:lts-community
    container_name: sonarqube
    depends_on:
      - db
    ports:
      - "127.0.0.1:9000:9000"
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonar
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs
    ulimits:
      nofile:
        soft: 65536
        hard: 65536

  db:
    image: postgres:16
    container_name: sonarqube-db
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: sonar
      POSTGRES_DB: sonar
    volumes:
      - postgresql_data:/var/lib/postgresql/data

volumes:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
  postgresql_data:
```

```bash
# Local startup for a learning environment.
sudo sysctl -w vm.max_map_count=524288
docker compose up -d

# Wait until SonarQube reports that it is up.
until curl -fsS http://127.0.0.1:9000/api/system/status | grep -q '"status":"UP"'; do
  sleep 10
done

echo "SonarQube is ready at http://127.0.0.1:9000"
```

On Kubernetes, prefer the official Helm chart for real deployments because it captures many operational defaults that are easy to miss in handwritten manifests. A teaching manifest is still useful because it shows the moving parts: namespace, database credentials, persistent volumes, a single SonarQube application pod for non-clustered editions, readiness checks, service exposure, and ingress. Treat the database as stateful production infrastructure, not as an afterthought inside an application namespace.

```text
KUBERNETES DEPLOYMENT SHAPE
──────────────────────────────────────────────────────────────────────────────

Ingress
└── Service: sonarqube:9000
    └── Deployment: sonarqube application pod
        ├── PersistentVolumeClaim: application data
        ├── PersistentVolumeClaim: extensions
        ├── Secret: database username and password
        ├── Readiness probe: /api/system/status
        └── Liveness probe: /api/system/status

PostgreSQL
└── Stateful storage managed by database team or Helm dependency
    ├── Backups
    ├── Upgrade plan
    ├── Storage monitoring
    └── Disaster recovery procedure
```

```yaml
# sonarqube-basic.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sonarqube
---
apiVersion: v1
kind: Secret
metadata:
  name: sonarqube-db-secret
  namespace: sonarqube
type: Opaque
stringData:
  username: sonar
  password: change-me-before-production
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sonarqube-data
  namespace: sonarqube
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sonarqube-extensions
  namespace: sonarqube
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sonarqube
  namespace: sonarqube
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sonarqube
  template:
    metadata:
      labels:
        app: sonarqube
    spec:
      securityContext:
        fsGroup: 1000
      initContainers:
        - name: set-vm-max-map-count
          image: busybox:1.36
          securityContext:
            privileged: true
          command:
            - sh
            - -c
            - sysctl -w vm.max_map_count=524288
      containers:
        - name: sonarqube
          image: sonarqube:lts-community
          ports:
            - name: http
              containerPort: 9000
          env:
            - name: SONAR_JDBC_URL
              value: jdbc:postgresql://postgresql.sonarqube.svc.cluster.local:5432/sonar
            - name: SONAR_JDBC_USERNAME
              valueFrom:
                secretKeyRef:
                  name: sonarqube-db-secret
                  key: username
            - name: SONAR_JDBC_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: sonarqube-db-secret
                  key: password
          resources:
            requests:
              cpu: 500m
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 4Gi
          volumeMounts:
            - name: data
              mountPath: /opt/sonarqube/data
            - name: extensions
              mountPath: /opt/sonarqube/extensions
          readinessProbe:
            httpGet:
              path: /api/system/status
              port: http
            initialDelaySeconds: 60
            periodSeconds: 30
            timeoutSeconds: 5
          livenessProbe:
            httpGet:
              path: /api/system/status
              port: http
            initialDelaySeconds: 120
            periodSeconds: 30
            timeoutSeconds: 5
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: sonarqube-data
        - name: extensions
          persistentVolumeClaim:
            claimName: sonarqube-extensions
---
apiVersion: v1
kind: Service
metadata:
  name: sonarqube
  namespace: sonarqube
spec:
  type: ClusterIP
  selector:
    app: sonarqube
  ports:
    - name: http
      port: 9000
      targetPort: http
```

A Helm deployment lets platform teams express the same intent with less handwritten YAML. The values below are intentionally conservative: one application replica for community-style deployment, persistent storage, a PostgreSQL dependency for a lab or small internal instance, ingress enabled, and authentication forced so anonymous users do not browse internal code metrics. Production teams should replace the embedded database with their standard PostgreSQL service when that is their organizational pattern.

```yaml
# sonarqube-values.yaml
replicaCount: 1

image:
  repository: sonarqube
  tag: lts-community

service:
  type: ClusterIP
  port: 9000

ingress:
  enabled: true
  ingressClassName: nginx
  hosts:
    - name: sonarqube.example.com
      path: /

persistence:
  enabled: true
  storageClass: standard
  size: 20Gi

postgresql:
  enabled: true
  auth:
    username: sonar
    database: sonar
  primary:
    persistence:
      enabled: true
      size: 20Gi

resources:
  requests:
    cpu: 500m
    memory: 2Gi
  limits:
    cpu: "2"
    memory: 4Gi

sonarProperties:
  sonar.forceAuthentication: true
```

```bash
helm repo add sonarqube https://SonarSource.github.io/helm-chart-sonarqube
helm repo update

helm upgrade --install sonarqube sonarqube/sonarqube \
  --namespace sonarqube \
  --create-namespace \
  --values sonarqube-values.yaml
```

Operating the service means defining who owns rules, gates, exceptions, upgrades, and review states. Security teams may own vulnerability policy, but application teams usually need authority to tune maintainability rules that create noise in their domain. Platform teams should provide the paved road: project templates, CI snippets, token management, default gates, dashboards, and support playbooks. The best operating model makes the default path strong enough for most teams while leaving documented escalation paths for exceptional cases.

### 7. Worked Example: Turn a Noisy Adoption Into a Useful Gate

Consider a team adopting SonarQube for an older order-management service. The first scan reports low overall coverage, many duplicated blocks, several code smells, and two reliability findings. A naive rollout would create a strict gate on overall metrics and demand a cleanup sprint. A better rollout classifies findings by risk, separates old debt from new changes, and chooses a gate the team can honor immediately.

```text
WORKED EXAMPLE: ORDER SERVICE ADOPTION
──────────────────────────────────────────────────────────────────────────────

Initial scan:
├── Overall coverage is low because legacy service methods lack tests
├── New order validation code has good tests
├── Duplicated address-normalization logic appears in three older files
├── Two reliability findings are in code touched by the current pull request
└── One security hotspot appears in a new webhook signature helper

Decision:
├── Fix the two reliability findings before merge
├── Review the webhook hotspot before merge
├── Keep new-code coverage gate enabled for the pull request
├── Create a follow-up ticket for address-normalization duplication
└── Do not block the pull request on untouched legacy coverage

Result:
├── The risky current change is corrected
├── The gate teaches the team what future changes must satisfy
├── Legacy debt becomes visible without stopping urgent delivery
└── Cleanup work is prioritized where it connects to future change
```

The first gate for this service should focus on new code: no new reliability or security regressions, reviewed hotspots on changed code, meaningful coverage for new behavior, and low duplication in the diff. The team should also track overall coverage and duplication trends, but those metrics should begin as dashboards rather than immediate blockers. After a few iterations, the team can add an overall coverage floor for critical packages or set a remediation target for the duplicated address-normalization logic.

```yaml
# Quality gate policy described as code-like documentation for team review.
quality_gate_name: order-service-new-code
conditions:
  - metric: reliability_rating_on_new_code
    operator: is_worse_than
    value: A
    action: fail
  - metric: security_rating_on_new_code
    operator: is_worse_than
    value: A
    action: fail
  - metric: security_hotspots_reviewed_on_new_code
    operator: is_less_than
    value: 100
    action: fail
  - metric: coverage_on_new_code
    operator: is_less_than
    value: 80
    action: fail
  - metric: duplicated_lines_density_on_new_code
    operator: is_greater_than
    value: 3
    action: fail
observed_metrics:
  - overall_coverage
  - overall_duplicated_lines_density
  - technical_debt_ratio
```

This example also shows why "coverage is a means, not the mission" is more than a slogan. If the pull request adds behavior to payment or order logic, tests should prove the behavior and edge cases. The coverage report helps SonarQube confirm that the changed lines were exercised, but reviewers still need to inspect whether the assertions would catch the bug the team fears. Coverage without assertions is theater; assertions without relevant execution are dead code; useful tests combine both.

> **Pause and apply:** Your team touches one function in a file with many old code smells. SonarQube fails the pull request because the new function has no tests and creates a new reliability issue. What should you fix in the pull request, and what should become follow-up work?

The pull request should fix the new reliability issue and add meaningful tests around the changed function. The old smells in unrelated parts of the file should be triaged separately unless the current change depends on them. This is the discipline behind sustainable quality gates: the author is responsible for the quality of the change, while the team plans legacy remediation based on risk, ownership, and change frequency.

## Did You Know?

- **Connected mode changes developer behavior:** SonarLint connected mode can align IDE feedback with the server-side quality profile, which reduces the frustrating pattern where code looks clean locally but fails under CI rules.
- **Security hotspots are intentionally review-driven:** A hotspot is not automatically a vulnerability; it marks code that needs human judgment because context decides whether the pattern is acceptable.
- **Coverage import is external by design:** SonarQube usually consumes coverage reports from tools such as JaCoCo, coverage.py, lcov, or OpenCover rather than running the tests itself.
- **New-code gating is the adoption lever:** Teams can prevent new debt immediately while using overall metrics to plan cleanup, which is why many successful rollouts begin with changed-code conditions.

## Common Mistakes

| Mistake | Problem | Better Practice |
|---------|---------|-----------------|
| Gating on overall coverage during first adoption | Legacy gaps block unrelated feature work and encourage shallow tests written only to satisfy a number | Start with coverage on new code, teach behavior-focused tests, and add overall floors gradually |
| Copying CI examples with invalid `uses` values | The workflow fails before analysis and learners lose trust in the guidance | Use real public actions with explicit versions or approved commit SHAs |
| Treating every hotspot as a confirmed vulnerability | Reviewers waste time fighting false urgency and may stop reading hotspot results carefully | Require hotspot review, document the decision, and escalate only when context proves exploitability |
| Excluding large directories to make the dashboard look better | Metrics improve on paper while risky maintained code disappears from analysis | Exclude generated, vendored, or irrelevant files only, and review exclusions like production policy |
| Running analysis only on the default branch | Problems are discovered after merge when the cheapest review moment has already passed | Analyze pull requests and make the quality gate a required merge check |
| Forgetting to generate coverage reports before scanning | SonarQube shows missing coverage even though tests passed successfully | Run tests with report output enabled and point scanner properties to the produced files |
| Using one monorepo project for unrelated teams | Gate failures become hard to assign and teams tune rules for code they do not own | Use separate project keys for independently owned services or packages when ownership differs |
| Allowing unexplained suppressions such as `NOSONAR` | Real issues can be hidden without review, and future maintainers cannot tell why the finding disappeared | Require justification, review suppressions periodically, and prefer rule tuning when a pattern is noisy |

## Quiz

<details>
<summary>1. Your team enables SonarQube on a seven-year-old service. The first pull request fails because overall coverage is below the target, even though the changed lines have tests. What should you change in the gate, and why?</summary>

You should change the gate to focus on coverage for new code rather than overall coverage during the first adoption phase. The current failure is caused by old untested code outside the pull request, so it does not give the author a reasonable path to fix the change. Keep overall coverage visible as a trend, create follow-up work for critical legacy areas, and let the gate enforce that new or changed behavior has meaningful tests.
</details>

<details>
<summary>2. A scanner job completes successfully, but the SonarQube project shows zero coverage for a Python service. CI logs show that `coverage.xml` was created. What do you check next?</summary>

Check the working directory of the scan job, the `sonar.python.coverage.reportPaths` value, and the source paths inside the coverage report. The scanner must be able to read the file at the configured path, and the report paths must match files included by `sonar.sources`. Also inspect exclusions, because a broad pattern such as `**/src/**` or a misplaced test exclusion can remove measured files before coverage attaches.
</details>

<details>
<summary>3. A pull request adds webhook verification. SonarQube reports one security hotspot in the signature code and no vulnerabilities. The developer says the gate should ignore it because it is not a vulnerability. How do you respond?</summary>

You should keep the hotspot review requirement because signature verification is security-sensitive and context matters. A hotspot means the scanner cannot prove the code is unsafe, not that the code is safe. Review the algorithm choice, secret handling, replay protection, timing behavior, and test coverage, then mark the hotspot reviewed only after the team can justify the implementation.
</details>

<details>
<summary>4. A GitHub Actions workflow uses `uses: ./scripts/run-sonar.py@main` for the scan step and fails with an action resolution error. What is the correct fix?</summary>

Replace the invalid `uses` reference with a real action or run the script as a shell command. For SonarQube scanning, a valid action reference would be `SonarSource/sonarqube-scan-action@v7.1.0`, with `SONAR_TOKEN` and `SONAR_HOST_URL` passed through secrets. If the organization wraps scanning in an internal script, the step should use `run: ./scripts/run-sonar.py` after checkout rather than pretending the script is a GitHub Action.
</details>

<details>
<summary>5. A monorepo has one SonarQube project for ten services. A pull request in the catalog service fails because the shared dashboard includes unrelated issues from the billing service. What redesign would you recommend?</summary>

Create separate SonarQube project keys for independently owned services, especially when they have different teams, release cycles, or risk profiles. Each service can keep its own gate, source paths, exclusions, and dashboards, while shared libraries can receive their own project when ownership is distinct. This reduces noisy failures and makes remediation accountable to the team that can actually change the code.
</details>

<details>
<summary>6. A team celebrates reaching 90 percent coverage after adding tests with no assertions around a critical retry function. SonarQube now passes, but reviewers are uneasy. What should the review focus on?</summary>

The review should focus on whether the tests prove behavior, not only whether they execute lines. Ask whether the tests would fail if retry count, idempotency handling, timeout behavior, or duplicate submission prevention were broken. Coverage is useful as a signal that changed code was exercised, but the team should improve assertions, edge cases, and failure-mode tests before treating the change as safe.
</details>

<details>
<summary>7. A scan fails before uploading results after a SonarQube server migration. The build and tests still pass. Which troubleshooting path should you follow?</summary>

Start with connectivity and authentication because the scan fails before the server can process analysis. Verify `SONAR_HOST_URL` from the CI runner, confirm the token has access to the project, check TLS or proxy settings if the URL changed, and inspect scanner logs for HTTP status or certificate errors. Do not change quality gate conditions until the scanner can upload an analysis report successfully.
</details>

<details>
<summary>8. A platform team wants one strict enterprise quality profile for every language and repository. Several teams argue that generated clients and framework-specific patterns create noise. How should the platform team handle the disagreement?</summary>

The platform team should provide a strong default profile and gate, but allow documented tuning where teams can show that a rule is noisy for maintained code or irrelevant for generated code. Generated and vendored code should usually be excluded, while real application code should remain visible. The policy should require justification and periodic review so tuning improves signal quality rather than hiding risk.
</details>

## Hands-On Exercise

**Objective**: Deploy a local SonarQube instance, analyze a sample project with intentional issues, configure a new-code-oriented quality gate, and debug the most common scanner-to-server failure points.

This exercise uses Docker Compose for the server and the SonarScanner container for analysis. The goal is not to create a perfect production deployment. The goal is to practice the workflow that a platform engineer later automates for teams: create a project, produce scan inputs, run analysis, inspect findings, adjust the gate, and verify the failure is tied to meaningful risk.

### Part 1: Start SonarQube Locally

```bash
mkdir -p sonarqube-lab
cd sonarqube-lab

cat > docker-compose.yml << 'EOF'
services:
  sonarqube:
    image: sonarqube:lts-community
    container_name: sonarqube
    depends_on:
      - db
    ports:
      - "127.0.0.1:9000:9000"
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonar
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs

  db:
    image: postgres:16
    container_name: sonarqube-db
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: sonar
      POSTGRES_DB: sonar
    volumes:
      - postgresql_data:/var/lib/postgresql/data

volumes:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
  postgresql_data:
EOF

sudo sysctl -w vm.max_map_count=524288
docker compose up -d

until curl -fsS http://127.0.0.1:9000/api/system/status | grep -q '"status":"UP"'; do
  sleep 10
  echo "Waiting for SonarQube..."
done

echo "SonarQube is ready at http://127.0.0.1:9000"
```

Log in at `http://127.0.0.1:9000` with the default local credentials and change the password when prompted. Create a token from the user security page and keep it for the scanner command. In a real platform, this token would be stored as a CI secret, scoped to the project or automation account, and rotated through an operational process.

### Part 2: Create a Sample Python Project

```bash
mkdir -p sample-project/src sample-project/tests
cd sample-project

cat > src/app.py << 'EOF'
import hashlib
import subprocess


def get_user_query(user_id: str) -> str:
    query = "SELECT * FROM users WHERE id = " + user_id
    return query


def run_operator_command(command: str) -> int:
    return subprocess.call(command, shell=True)


def classify_invoice(amount: int, country: str, vip: bool, overdue: bool) -> str:
    if amount > 0:
        if country:
            if vip:
                if overdue:
                    return "vip-overdue"
                return "vip-current"
            if amount > 1000:
                return "manual-review"
            return "standard"
        return "missing-country"
    return "invalid"


def normalize_customer_name(name: str) -> str:
    result = name.strip().lower()
    result = result.replace("-", "_")
    result = result.replace(" ", "_")
    return result


def normalize_vendor_name(name: str) -> str:
    result = name.strip().lower()
    result = result.replace("-", "_")
    result = result.replace(" ", "_")
    return result


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def add_numbers(left: int, right: int) -> int:
    return left + right
EOF

cat > tests/test_app.py << 'EOF'
from src.app import add_numbers, classify_invoice


def test_add_numbers_handles_positive_and_negative_values():
    assert add_numbers(1, 2) == 3
    assert add_numbers(-1, 1) == 0


def test_classify_invoice_flags_invalid_amounts():
    assert classify_invoice(0, "US", False, False) == "invalid"
EOF

cat > sonar-project.properties << 'EOF'
sonar.projectKey=sample-project
sonar.projectName=Sample Project
sonar.projectVersion=1.0

sonar.sources=src
sonar.tests=tests
sonar.sourceEncoding=UTF-8

sonar.python.version=3.12
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=pytest-report.xml
EOF
```

This sample intentionally contains several findings: command execution through a shell, string-built SQL, duplicated normalization logic, a complex branch-heavy function, and weak hashing. Do not fix them before the first scan. The point is to learn how SonarQube presents different issue categories, then decide which findings should block a change and which should become review or refactoring work.

### Part 3: Generate Test and Coverage Reports

```bash
.venv/bin/python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install pytest pytest-cov

.venv/bin/python -m pytest \
  --junitxml=pytest-report.xml \
  --cov=src \
  --cov-report=xml:coverage.xml
```

If you do not already have `.venv/bin/python` available in your environment, create the virtual environment exactly as shown above. The important learning point is that the scanner consumes `coverage.xml` and `pytest-report.xml`; it does not create those reports by itself. If you skip this step, SonarQube can still analyze code issues, but it will not have coverage evidence for the sample project.

### Part 4: Run the Scanner

```bash
export SONAR_TOKEN="replace-with-your-token"

docker run --rm \
  --network sonarqube-lab_default \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="${SONAR_TOKEN}" \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.qualitygate.wait=true \
  -Dsonar.qualitygate.timeout=300
```

Open the `sample-project` dashboard in SonarQube after the scan finishes. Inspect the issue list before changing any settings. For each finding, classify whether it is reliability, security, hotspot review, maintainability, duplication, or coverage-related. Then decide whether that finding should block new code immediately or become follow-up work.

### Part 5: Configure and Test a Practical Gate

In the SonarQube UI, copy the default gate or create a new gate for the sample project. Add or verify conditions that focus on new code first: reliability rating on new code, security rating on new code, reviewed hotspots on new code, coverage on new code, and duplication on new code. Avoid creating a first gate that blocks all historical debt in the sample project, because that is exactly the rollout failure this module warned about.

```bash
curl -fsS \
  -u "${SONAR_TOKEN}:" \
  "http://127.0.0.1:9000/api/qualitygates/project_status?projectKey=sample-project"
```

Read the JSON response and identify the failed condition. If the gate fails because of a current-code issue, fix one issue in `src/app.py`, rerun tests, rerun the scanner, and compare the gate response. If the gate fails because coverage was not imported, debug the report path instead of lowering the coverage threshold.

### Part 6: Practice a Focused Fix

Fix the command execution issue by replacing the dangerous function with a constrained command runner. This is a small example, but it mirrors the professional workflow: understand the finding, choose a safer implementation, test the behavior, and rerun analysis.

```bash
cat > src/app.py.tmp << 'EOF'
import hashlib
import subprocess


def get_user_query(user_id: str) -> str:
    query = "SELECT * FROM users WHERE id = " + user_id
    return query


def run_operator_command(command: str) -> int:
    allowed_commands = {
        "show_status": ["echo", "status-ok"],
        "show_version": ["echo", "version-1"],
    }
    if command not in allowed_commands:
        raise ValueError("unsupported command")
    completed = subprocess.run(allowed_commands[command], check=False)
    return completed.returncode


def classify_invoice(amount: int, country: str, vip: bool, overdue: bool) -> str:
    if amount > 0:
        if country:
            if vip:
                if overdue:
                    return "vip-overdue"
                return "vip-current"
            if amount > 1000:
                return "manual-review"
            return "standard"
        return "missing-country"
    return "invalid"


def normalize_customer_name(name: str) -> str:
    result = name.strip().lower()
    result = result.replace("-", "_")
    result = result.replace(" ", "_")
    return result


def normalize_vendor_name(name: str) -> str:
    result = name.strip().lower()
    result = result.replace("-", "_")
    result = result.replace(" ", "_")
    return result


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def add_numbers(left: int, right: int) -> int:
    return left + right
EOF

mv src/app.py.tmp src/app.py

cat >> tests/test_app.py << 'EOF'


def test_operator_command_rejects_unknown_commands():
    from src.app import run_operator_command

    try:
        run_operator_command("rm -rf /")
    except ValueError as exc:
        assert "unsupported command" in str(exc)
    else:
        raise AssertionError("expected unsupported command to be rejected")
EOF

.venv/bin/python -m pytest \
  --junitxml=pytest-report.xml \
  --cov=src \
  --cov-report=xml:coverage.xml
```

Rerun the scanner and observe whether the issue list changes. If SonarQube still reports a related issue, inspect the exact message rather than assuming the tool is wrong. Static analysis findings often teach you that a fix is partial: replacing `shell=True` removes one risk, but you may still need validation, logging, least privilege, or stronger domain modeling depending on the command.

### Success Criteria

- [ ] SonarQube is running at `http://127.0.0.1:9000` and reports system status `UP`.
- [ ] The sample project appears in SonarQube after a scanner run.
- [ ] The scanner imports coverage from `coverage.xml` rather than showing missing coverage because of a path error.
- [ ] You can classify at least one finding as reliability, security, hotspot review, maintainability, duplication, or coverage-related.
- [ ] A quality gate is configured to focus on new-code conditions rather than blocking all historical debt by default.
- [ ] The quality gate status can be checked through the SonarQube API.
- [ ] You fixed one issue, reran tests, reran analysis, and compared the result.
- [ ] You can explain which remaining findings should block a pull request and which should become planned remediation.

## Next Module

Continue to [Module 12.2: Semgrep](../module-12.2-semgrep/) to learn how custom security rules can catch organization-specific patterns that general-purpose scanners may not know about.
