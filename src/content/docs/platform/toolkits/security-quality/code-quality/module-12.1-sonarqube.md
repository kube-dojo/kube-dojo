---
title: "Module 12.1: SonarQube - The Code Quality Platform"
slug: platform/toolkits/security-quality/code-quality/module-12.1-sonarqube
sidebar:
  order: 2
---
## Complexity: [COMPLEX]
## Time to Complete: 50-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](../../disciplines/reliability-security/devsecops/) - CI/CD and security concepts
- [CI/CD Pipelines Toolkit](../ci-cd-pipelines/) - Pipeline implementation
- Experience with at least one programming language
- Basic Docker knowledge

---

## Why This Module Matters

**The Technical Debt Visualization Problem**

Every engineering leader has had this conversation:

*"We need to stop and fix our technical debt."*
*"How much technical debt do we have?"*
*"Um... a lot?"*
*"How long will it take to fix?"*
*"Hard to say..."*
*"Let's defer it to next quarter."*

Technical debt is invisible. Developers feel it—the code is hard to change, bugs keep appearing in the same places, new engineers take forever to onboard. But without numbers, debt loses every prioritization battle to feature work.

SonarQube makes technical debt visible. It shows you: "This codebase has 47 days of technical debt. File X has 8 hours alone. Fixing these 3 hotspots would eliminate 60% of it." Suddenly, that "we should really fix this" conversation has data.

But SonarQube is more than debt tracking. It catches bugs before they ship (null dereferences, resource leaks), identifies security vulnerabilities (SQL injection, XSS), and enforces quality gates that prevent bad code from merging. When developers see red on their PR, they fix it. When they don't see anything, technical debt accumulates silently.

---

## SonarQube Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SONARQUBE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DEVELOPER WORKSTATION                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │    IDE + SonarLint  ◄───────────────────────────────────┐│  │
│  │    (real-time)                                          ││  │
│  │                                                          ││  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                              │   │
│                              │ git push                     │   │
│                              ▼                              │   │
│  CI/CD PIPELINE                                             │   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │    sonar-scanner ─────────────────────────────────────┐  │  │
│  │    • Analyzes source code                             │  │  │
│  │    • Sends results to server                          │  │  │
│  │                                                        │  │  │
│  └──────────────────────────────────────────────────────┼───┘  │
│                                                          │      │
│                              analysis results            │      │
│                              ▼                           │ sync │
│  SONARQUBE SERVER                                        │      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │   Web UI    │  │ Compute     │  │   Search        │  │  │
│  │  │             │  │  Engine     │  │ (Elasticsearch) │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  │                          │                               │  │
│  │                          ▼                               │  │
│  │              ┌─────────────────────────┐                │  │
│  │              │      PostgreSQL         │                │  │
│  │              │   (metrics, history)    │                │  │
│  │              └─────────────────────────┘                │  │
│  │                                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Purpose | Notes |
|-----------|---------|-------|
| **SonarLint** | IDE plugin, real-time analysis | Free, works offline for standard rules |
| **Scanner** | CLI tool that analyzes code | Runs in CI, uploads to server |
| **Web Server** | UI, API, authentication | Main application |
| **Compute Engine** | Processes analysis reports | Background task processing |
| **Elasticsearch** | Full-text search | Code search, issue navigation |
| **Database** | Stores all metrics | PostgreSQL recommended for production |

---

## SonarQube Metrics Deep Dive

### The Quality Model

```
SONARQUBE QUALITY MODEL
─────────────────────────────────────────────────────────────────

RELIABILITY (Bugs)
├── Bugs: Code that is wrong (will fail at runtime)
├── Examples: Null dereference, division by zero, infinite loop
└── Rating: A (0 bugs) to E (many critical bugs)

SECURITY (Vulnerabilities)
├── Vulnerabilities: Code that could be exploited
├── Examples: SQL injection, XSS, hardcoded credentials
└── Rating: A (0 vulns) to E (many critical vulns)

SECURITY REVIEW (Hotspots)
├── Hotspots: Code that needs manual review
├── Examples: Crypto usage, random number generation
└── Rating: A (100% reviewed) to E (< 30% reviewed)

MAINTAINABILITY (Code Smells)
├── Code Smells: Code that's hard to maintain
├── Examples: Long methods, deep nesting, duplications
├── Technical Debt: Time to fix all smells
└── Rating: A (< 5% debt ratio) to E (> 50% debt ratio)

COVERAGE
├── Line Coverage: % of lines executed by tests
├── Branch Coverage: % of conditions tested
└── Target: Usually 80%+ for new code

DUPLICATIONS
├── Duplicated Blocks: Copy-pasted code
├── Duplicated Lines: % of codebase duplicated
└── Target: < 3% for new code
```

### Understanding Technical Debt

```
TECHNICAL DEBT BREAKDOWN
─────────────────────────────────────────────────────────────────

Total Debt: 47 days

By Category:
├── Code Smells:        35 days (74%)
│   ├── Long methods:    12 days
│   ├── Deep nesting:     8 days
│   ├── Duplications:     7 days
│   └── Other:            8 days
├── Bugs:                8 days (17%)
└── Vulnerabilities:     4 days  (9%)

By File (Top 5):
┌──────────────────────────────────────────────────────────────┐
│ File                          │ Debt   │ Issues │ % Total   │
├──────────────────────────────────────────────────────────────┤
│ src/legacy/PaymentService.java│ 8h     │ 47     │ 17%       │
│ src/auth/AuthController.java  │ 6h     │ 32     │ 13%       │
│ src/util/StringUtils.java     │ 4h     │ 28     │  8%       │
│ src/api/UserEndpoint.java     │ 3h     │ 21     │  6%       │
│ src/data/Repository.java      │ 3h     │ 19     │  6%       │
└──────────────────────────────────────────────────────────────┘

Fix Priority:
1. PaymentService.java - High debt, likely high change frequency
2. AuthController.java - Security-critical code
3. Focus on "new code" - Don't let debt grow
```

---

## Quality Gates: The Kill Switch

### Configuring Quality Gates

```
QUALITY GATE CONFIGURATION
─────────────────────────────────────────────────────────────────

Default "Sonar way" gate (recommended starting point):

Condition                        Operator    Value
─────────────────────────────────────────────────────────────────
Coverage on New Code             is less than 80%
Duplicated Lines on New Code     is greater than 3%
Maintainability Rating on New Code is worse than A
Reliability Rating on New Code   is worse than A
Security Hotspots Reviewed on New Code is less than 100%
Security Rating on New Code      is worse than A

─────────────────────────────────────────────────────────────────

"Stricter" custom gate (mature codebase):

Condition                        Operator    Value
─────────────────────────────────────────────────────────────────
All conditions from "Sonar way"  ...         ...
Coverage on New Code             is less than 90%
Technical Debt Ratio on New Code is greater than 2%
Blocker Issues on New Code       is greater than 0
Critical Issues on New Code      is greater than 0
```

### Quality Gate in CI/CD

```yaml
# GitHub Actions with Quality Gate check
name: SonarQube Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for blame

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Cache SonarQube packages
        uses: actions/cache@v4
        with:
          path: ~/.sonar/cache
          key: ${{ runner.os }}-sonar

      - name: Build and Test
        run: |
          ./gradlew build test jacocoTestReport

      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

      - name: Quality Gate Check
        uses: sonarsource/sonarqube-quality-gate-action@master
        timeout-minutes: 5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

```yaml
# GitLab CI with Quality Gate
sonarqube:
  stage: analyze
  image: sonarsource/sonar-scanner-cli:latest
  variables:
    SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar"
    GIT_DEPTH: 0
  cache:
    key: "${CI_JOB_NAME}"
    paths:
      - .sonar/cache
  script:
    - sonar-scanner
        -Dsonar.projectKey=${CI_PROJECT_NAME}
        -Dsonar.sources=src
        -Dsonar.host.url=${SONAR_HOST_URL}
        -Dsonar.login=${SONAR_TOKEN}
        -Dsonar.qualitygate.wait=true  # Blocks until gate result
  allow_failure: false
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## Project Configuration

### sonar-project.properties

```properties
# sonar-project.properties - Standard configuration

# Project identification
sonar.projectKey=mycompany:myproject
sonar.projectName=My Project
sonar.projectVersion=1.0

# Source configuration
sonar.sources=src/main
sonar.tests=src/test
sonar.sourceEncoding=UTF-8

# Language-specific settings
sonar.java.binaries=target/classes
sonar.java.libraries=target/dependency/*.jar
sonar.java.test.binaries=target/test-classes

# Coverage reports (from JaCoCo)
sonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml

# Test reports
sonar.junit.reportPaths=target/surefire-reports

# Exclusions (don't analyze these)
sonar.exclusions=\
  **/generated/**,\
  **/node_modules/**,\
  **/*.spec.ts,\
  **/test/**

# Coverage exclusions (don't count coverage for these)
sonar.coverage.exclusions=\
  **/config/**,\
  **/dto/**,\
  **/*Application.java

# Duplicate exclusions
sonar.cpd.exclusions=\
  **/dto/**,\
  **/entity/**

# Security hotspot review
# Mark certain files as already reviewed
sonar.security.hotspots.reviewed=true
```

### Multi-Module Projects

```properties
# sonar-project.properties for monorepo

sonar.projectKey=mycompany:monorepo
sonar.projectName=Monorepo

# Define modules
sonar.modules=api,web,shared

# API module
api.sonar.projectName=API Service
api.sonar.sources=api/src/main
api.sonar.tests=api/src/test
api.sonar.java.binaries=api/target/classes

# Web module
web.sonar.projectName=Web Frontend
web.sonar.sources=web/src
web.sonar.tests=web/src/**/*.spec.ts
web.sonar.typescript.lcov.reportPaths=web/coverage/lcov.info

# Shared module
shared.sonar.projectName=Shared Libraries
shared.sonar.sources=shared/src
```

### Language-Specific Configuration

```properties
# Python
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=pytest-report.xml

# JavaScript/TypeScript
sonar.javascript.lcov.reportPaths=coverage/lcov.info
sonar.typescript.tsconfigPath=tsconfig.json

# Go
sonar.go.coverage.reportPaths=coverage.out

# C#
sonar.cs.opencover.reportsPaths=coverage.opencover.xml
sonar.cs.vstest.reportsPaths=TestResults/*.trx
```

---

## Deploying SonarQube

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  sonarqube:
    image: sonarqube:lts-community
    container_name: sonarqube
    depends_on:
      - db
    ports:
      - "9000:9000"
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
    image: postgres:15
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
# Required system setting for Elasticsearch
sudo sysctl -w vm.max_map_count=524288
sudo sysctl -w fs.file-max=131072

# Start SonarQube
docker-compose up -d

# Access at http://localhost:9000
# Default login: admin/admin (change immediately!)
```

### Kubernetes Deployment (Production)

```yaml
# sonarqube-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sonarqube
  namespace: sonarqube
spec:
  replicas: 1  # SonarQube doesn't support horizontal scaling
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
        - name: sysctl
          image: busybox
          securityContext:
            privileged: true
          command: ['sh', '-c', 'sysctl -w vm.max_map_count=524288']
      containers:
        - name: sonarqube
          image: sonarqube:lts-community
          ports:
            - containerPort: 9000
          env:
            - name: SONAR_JDBC_URL
              value: "jdbc:postgresql://postgres-service:5432/sonar"
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
              memory: "2Gi"
              cpu: "500m"
            limits:
              memory: "4Gi"
              cpu: "2"
          volumeMounts:
            - name: sonarqube-data
              mountPath: /opt/sonarqube/data
            - name: sonarqube-extensions
              mountPath: /opt/sonarqube/extensions
          readinessProbe:
            httpGet:
              path: /api/system/status
              port: 9000
            initialDelaySeconds: 60
            periodSeconds: 30
          livenessProbe:
            httpGet:
              path: /api/system/status
              port: 9000
            initialDelaySeconds: 60
            periodSeconds: 30
      volumes:
        - name: sonarqube-data
          persistentVolumeClaim:
            claimName: sonarqube-data-pvc
        - name: sonarqube-extensions
          persistentVolumeClaim:
            claimName: sonarqube-extensions-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: sonarqube
  namespace: sonarqube
spec:
  type: ClusterIP
  ports:
    - port: 9000
      targetPort: 9000
  selector:
    app: sonarqube
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sonarqube
  namespace: sonarqube
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "64m"
spec:
  ingressClassName: nginx
  rules:
    - host: sonarqube.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: sonarqube
                port:
                  number: 9000
```

### Helm Chart (Recommended)

```bash
# Add Helm repo
helm repo add sonarqube https://SonarSource.github.io/helm-chart-sonarqube
helm repo update

# Create values file
cat > sonarqube-values.yaml << 'EOF'
# Production configuration
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
  persistence:
    enabled: true
    size: 20Gi

resources:
  requests:
    memory: 2Gi
    cpu: 500m
  limits:
    memory: 4Gi
    cpu: 2

# Plugins to install
plugins:
  install:
    - https://github.com/dependency-check/dependency-check-sonar-plugin/releases/download/4.0.0/sonar-dependency-check-plugin-4.0.0.jar

# Custom settings
sonarProperties:
  sonar.forceAuthentication: true
EOF

# Install
helm upgrade --install sonarqube sonarqube/sonarqube \
  --namespace sonarqube \
  --create-namespace \
  --values sonarqube-values.yaml
```

---

## Branch Analysis & Pull Request Decoration

### GitHub Integration

```yaml
# .github/workflows/sonar.yml
name: SonarQube
on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
        with:
          args: >
            -Dsonar.pullrequest.key=${{ github.event.number }}
            -Dsonar.pullrequest.branch=${{ github.head_ref }}
            -Dsonar.pullrequest.base=${{ github.base_ref }}
```

### PR Decoration Result

```
PULL REQUEST DECORATION
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│ SonarQube Analysis                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Quality Gate: ✅ Passed                                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Metric              │ Value    │ Gate Status       │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │  New Bugs            │ 0        │ ✅ Passed         │  │
│  │  New Vulnerabilities │ 0        │ ✅ Passed         │  │
│  │  New Code Smells     │ 2        │ ✅ Passed         │  │
│  │  Coverage on New     │ 87.3%    │ ✅ Passed (>80%)  │  │
│  │  Duplications on New │ 0.0%     │ ✅ Passed (<3%)   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  2 Code Smells introduced:                                  │
│  • src/UserService.java:45 - Refactor this method...       │
│  • src/DataProcessor.java:89 - Remove this unused...       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## SonarLint: IDE Integration

### VS Code Configuration

```json
// .vscode/settings.json
{
  "sonarlint.connectedMode.connections.sonarqube": [
    {
      "serverUrl": "https://sonarqube.example.com",
      "token": "${env:SONAR_TOKEN}"
    }
  ],
  "sonarlint.connectedMode.project": {
    "projectKey": "mycompany:myproject"
  },
  "sonarlint.rules": {
    "javascript:S1481": {
      "level": "off"  // Disable specific rule
    },
    "java:S1135": {
      "level": "on",
      "parameters": {
        "message": "Remove this TODO"
      }
    }
  }
}
```

### IntelliJ Configuration

```xml
<!-- .idea/sonarlint.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="SonarLintProjectSettings">
    <option name="bindingEnabled" value="true" />
    <option name="projectKey" value="mycompany:myproject" />
    <option name="connectionName" value="SonarQube" />
  </component>
</project>
```

---

## War Story: The Coverage Mandate

**Company**: Fintech startup, 50 engineers
**Challenge**: Board mandated 80% code coverage after production incident

**The Situation**:

A bug in payment processing caused $200k in duplicate charges. Root cause: untested edge case in transaction retry logic. The board's response: "We need 80% code coverage on all code, now."

**The Naive Approach**:

```
Week 1: Engineering mandate - 80% coverage required
Week 2: Developers write tests frantically
Week 3: Coverage jumps from 35% to 75%
Week 4: Quality gate enabled, PRs start failing
Week 5: Developers revolt - "I can't ship this hotfix!"
```

The problem: Tests were written to hit coverage numbers, not to verify behavior.

```java
// Real test written during "coverage panic"
@Test
void testPaymentService() {
    PaymentService service = new PaymentService();
    service.processPayment(null, null, null);
    // No assertions - just coverage!
}
```

**The Better Approach**:

```
PHASED COVERAGE STRATEGY
─────────────────────────────────────────────────────────────────

Phase 1 (Week 1-2): New Code Only
├── Quality gate: 80% on NEW code only
├── Legacy code excluded
├── Developers learn: "My PR needs tests"
└── Result: New code quality improves

Phase 2 (Month 2-3): Critical Path Testing
├── Identify business-critical code
├── Write behavior tests (not coverage tests)
├── Payment processing: 95% coverage + mutation testing
└── Result: $200k bugs won't recur

Phase 3 (Month 4-6): Gradual Legacy Coverage
├── Tackle high-debt files first
├── Coverage requirement: 60% overall (increasing)
├── Combine with refactoring
└── Result: Sustainable improvement

Phase 4 (Ongoing): Mutation Testing
├── Add PIT mutation testing
├── Find tests that pass but don't verify
├── Kill the "coverage theater" tests
└── Result: Real confidence in test suite
```

**Quality Gate Evolution**:

```yaml
# Phase 1: New code only
- Coverage on New Code >= 80%

# Phase 2: Add overall floor
- Coverage on New Code >= 80%
- Overall Coverage >= 50%

# Phase 3: Mature
- Coverage on New Code >= 80%
- Overall Coverage >= 70%
- Duplicated Lines on New Code <= 3%
- Maintainability Rating on New Code = A
```

**Results After 6 Months**:

| Metric | Before | After |
|--------|--------|-------|
| Overall Coverage | 35% | 72% |
| New Code Coverage | N/A | 88% |
| Production Bugs/Month | 12 | 3 |
| Hotfixes/Month | 8 | 2 |
| Developer Satisfaction | "Tests are pointless" | "Tests caught my bug" |

**Key Lesson**: Coverage is a lagging indicator, not a goal. The goal is catching bugs. Coverage mandates without behavior focus produce coverage theater.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Gate on overall coverage | Legacy code blocks all PRs | Gate only on new code |
| 100% coverage goal | Diminishing returns, test theater | 80% new code, behavior focus |
| Ignoring security hotspots | Vulnerabilities ship | Require 100% hotspot review |
| No exclusions | Generated code pollutes metrics | Exclude DTOs, generated, tests |
| Analyzing on main only | Issues found after merge | Analyze PRs with decoration |
| No SonarLint | Developers see issues late | Require SonarLint in IDE |
| Giant monolithic analysis | Slow feedback | Incremental analysis |
| Ignoring debt ratio | Debt accumulates silently | Alert on debt ratio increase |

---

## Quiz

<details>
<summary>1. What is the difference between a Bug and a Code Smell in SonarQube?</summary>

**Answer**:
- **Bug**: Code that is demonstrably wrong and will fail at runtime. Examples: null pointer dereference, resource leak, infinite loop. High certainty of failure.

- **Code Smell**: Code that works but is hard to maintain. Examples: method too long, duplicated code, overly complex conditions. Contributes to technical debt but won't cause immediate failures.

Bugs affect Reliability rating; Code Smells affect Maintainability rating.
</details>

<details>
<summary>2. Why should quality gates focus on "new code" rather than overall metrics?</summary>

**Answer**: Legacy codebases often have significant technical debt. Requiring perfect metrics on all code would:

1. Block all PRs until legacy code is fixed
2. Create impossible cleanup requirements
3. Discourage adoption of quality gates

"New code" focus means:
- Boy Scout Rule: Leave code cleaner than you found it
- Prevents debt from growing
- Gradual improvement over time
- PRs remain reviewable scope
</details>

<details>
<summary>3. What is a Security Hotspot vs a Vulnerability?</summary>

**Answer**:
- **Vulnerability**: Code that is definitely exploitable. High confidence of security impact. Example: SQL concatenation from user input.

- **Security Hotspot**: Code that might be a security issue but requires manual review. Context matters. Example: Using crypto functions (might be fine, might be weak).

Hotspots need human verification. The gate checks "% of hotspots reviewed" not "hotspots = 0".
</details>

<details>
<summary>4. How does technical debt time estimation work?</summary>

**Answer**: SonarQube assigns remediation time to each issue type based on typical fix effort:

```
Issue Type             Typical Time
───────────────────────────────────
Duplicated block       10 minutes
Long method            20 minutes
Complex condition      15 minutes
Null dereference       30 minutes
SQL injection          1 hour
```

Total debt = sum of all issue remediation times.

Debt ratio = debt time / estimated development time for codebase.

These estimates are configurable and should be calibrated to your team's reality.
</details>

<details>
<summary>5. What is the difference between SonarQube Community and Developer editions?</summary>

**Answer**:

| Feature | Community (Free) | Developer |
|---------|-----------------|-----------|
| Languages | 15+ | 28+ |
| Branch analysis | Main only | All branches |
| PR decoration | No | Yes |
| Security rules | Basic | Advanced |
| OWASP/SANS reports | No | Yes |
| Portfolio management | No | Yes |

For teams that want PR integration, Developer edition is effectively required.
</details>

<details>
<summary>6. How do you handle false positives in SonarQube?</summary>

**Answer**: Several approaches:

1. **Won't Fix**: Mark issue as intentional, will be ignored in metrics
2. **False Positive**: Mark as incorrectly detected, will be ignored
3. **Rule Exclusion**: Disable rule for specific file patterns
4. **Inline Comments**: `// NOSONAR` or `@SuppressWarnings("java:S1234")`

Best practice:
- Require justification for suppressions
- Review false positives periodically (rules improve)
- Consider contributing to rule improvement
</details>

<details>
<summary>7. What is the purpose of SonarLint connected mode?</summary>

**Answer**: SonarLint connected mode syncs IDE analysis with SonarQube server:

Benefits:
- Same rules as CI (no surprises)
- Organization's custom rules included
- Hotspot review status synced
- New issues flagged before commit

Without connected mode, SonarLint uses default rules which may differ from your SonarQube configuration.
</details>

<details>
<summary>8. How does SonarQube handle multi-branch projects?</summary>

**Answer**: Branch analysis (Developer+ edition):

- **Main branch**: Full analysis, historical data
- **Feature branches**: Compared against main, shows new issues only
- **Pull requests**: Decoration with pass/fail status

```
main ──────●───────────●───────────●─────▶ main analysis
            \         /
             \───●───/  feature branch
                 │
                 └── PR analysis: "adds 2 bugs vs main"
```

Community edition only analyzes one branch (typically main).
</details>

---

## Hands-On Exercise

**Objective**: Deploy SonarQube, analyze a project, and configure quality gates to fail on poor code.

### Part 1: Deploy SonarQube

```bash
# Create directory for docker-compose
mkdir sonarqube-lab && cd sonarqube-lab

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  sonarqube:
    image: sonarqube:lts-community
    ports:
      - "9000:9000"
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonar
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: sonar
      POSTGRES_DB: sonar
    volumes:
      - postgresql_data:/var/lib/postgresql/data

volumes:
  sonarqube_data:
  sonarqube_extensions:
  postgresql_data:
EOF

# Set required kernel parameter
sudo sysctl -w vm.max_map_count=524288

# Start SonarQube
docker-compose up -d

# Wait for startup (about 2 minutes)
echo "Waiting for SonarQube to start..."
until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do
  sleep 10
  echo "Still waiting..."
done
echo "SonarQube is ready!"

# Access at http://localhost:9000
# Login: admin / admin (you'll be prompted to change)
```

### Part 2: Create Sample Project with Issues

```bash
# Create sample project
mkdir -p sample-project/src
cd sample-project

# Create a Python file with intentional issues
cat > src/app.py << 'EOF'
import os
import subprocess

# BUG: Unused variable
unused_variable = "I'm never used"

# VULNERABILITY: SQL Injection
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    # This would be vulnerable to SQL injection
    return query

# VULNERABILITY: Command injection
def run_command(cmd):
    subprocess.call(cmd, shell=True)  # Dangerous!

# CODE SMELL: Function too complex
def complex_function(a, b, c, d, e, f):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            return "deep"
                        else:
                            return "not deep"
                    else:
                        return "shallow"
                else:
                    return "shallow"
            else:
                return "shallow"
        else:
            return "shallow"
    else:
        return "negative"

# CODE SMELL: Duplicated code
def process_item_1(item):
    result = item.strip().lower()
    result = result.replace("-", "_")
    result = result.replace(" ", "_")
    return result

def process_item_2(item):
    result = item.strip().lower()
    result = result.replace("-", "_")
    result = result.replace(" ", "_")
    return result

# HOTSPOT: Weak cryptography (needs review)
import hashlib
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# Good code for comparison
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
EOF

# Create test file
cat > src/test_app.py << 'EOF'
from app import add_numbers

def test_add_numbers():
    assert add_numbers(1, 2) == 3
    assert add_numbers(-1, 1) == 0
EOF

# Create sonar-project.properties
cat > sonar-project.properties << 'EOF'
sonar.projectKey=sample-project
sonar.projectName=Sample Project
sonar.projectVersion=1.0

sonar.sources=src
sonar.exclusions=**/*test*.py

sonar.python.version=3.11

sonar.sourceEncoding=UTF-8
EOF
```

### Part 3: Run Analysis

```bash
# Generate token in SonarQube UI:
# My Account → Security → Generate Token
# Save the token

# Run scanner (replace YOUR_TOKEN)
docker run --rm \
  --network sonarqube-lab_default \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="YOUR_TOKEN" \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli

# Or install scanner locally:
# brew install sonar-scanner
# sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.token=YOUR_TOKEN
```

### Part 4: Review Results and Configure Quality Gate

1. **View Project in UI**:
   - Go to http://localhost:9000
   - Click on "sample-project"
   - Explore: Issues, Security Hotspots, Measures

2. **Configure Quality Gate**:
   - Go to Quality Gates
   - Copy "Sonar way"
   - Add condition: "Bugs" greater than 0 → Fails gate

3. **Re-analyze and Verify Gate Fails**:
   ```bash
   # Run scanner again
   sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.token=YOUR_TOKEN

   # Check gate status via API
   curl "http://localhost:9000/api/qualitygates/project_status?projectKey=sample-project"
   ```

### Success Criteria

- [ ] SonarQube running and accessible
- [ ] Project analyzed with issues found
- [ ] Can identify: 1 bug, 2+ vulnerabilities, 2+ code smells
- [ ] Security hotspot visible (MD5 usage)
- [ ] Quality gate configured to fail on bugs
- [ ] Re-analysis shows failed gate status

---

## Key Takeaways

1. **Technical debt is measurable** — Days/hours to fix, not vague "we should clean this up"
2. **Gate on new code** — Don't let perfect be the enemy of good
3. **Security hotspots need review** — Not all security findings are automatic
4. **SonarLint = shift-left** — Find issues before commit, not after CI
5. **Coverage is a means, not an end** — 80% of tested behavior beats 100% of coverage theater
6. **Branch analysis requires paid edition** — Community edition is main-only
7. **Exclusions are important** — Generated code, DTOs pollute metrics
8. **Quality gates block merges** — Make them meaningful but achievable
9. **Technical debt ratio matters** — Absolute debt can grow; ratio shouldn't
10. **Integrate early** — Harder to add quality gates to legacy codebase

---

## Did You Know?

> **SonarQube Origins**: SonarQube started as "Sonar" in 2007, created by SonarSource in Geneva, Switzerland. The "Qube" was added in 2013 to distinguish it from the general word "sonar."

> **Scale**: SonarQube has analyzed over 400 billion lines of code across organizations worldwide. The largest known single instance manages over 10,000 projects.

> **Language Rules**: The SonarQube rule set contains over 5,000 rules across all languages. Java alone has 600+ rules covering bugs, vulnerabilities, and code smells.

> **Technical Debt Concept**: The "technical debt" metaphor was coined by Ward Cunningham in 1992. SonarQube was one of the first tools to make it quantifiable, turning an abstract concept into actionable metrics.

---

## Next Module

Continue to [Module 12.2: Semgrep](module-12.2-semgrep/) to learn about writing custom security rules in minutes—the developer-friendly alternative to complex SAST tools.
