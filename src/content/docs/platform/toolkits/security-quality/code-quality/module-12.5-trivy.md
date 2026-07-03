---
revision_pending: false
title: "Module 12.5: Trivy - The Swiss Army Knife of Security Scanning"
slug: platform/toolkits/security-quality/code-quality/module-12.5-trivy
sidebar:
  order: 6
---
## Complexity: `[MEDIUM]`
## Time to Complete: 45-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/module-4.1-devsecops-fundamentals/) - Security scanning concepts
- Container fundamentals (images, Dockerfiles)
- Basic Kubernetes knowledge
- CI/CD basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Trivy for comprehensive vulnerability scanning of container images, filesystems, and Git repositories**
- **Configure Trivy in CI/CD pipelines with severity thresholds and ignore policies for practical scanning**
- **Implement Trivy Operator for continuous Kubernetes cluster scanning with vulnerability and config audit reports**
- **Compare Trivy's open-source scanning against commercial alternatives for enterprise security requirements**

---

## Why This Module Matters

The typical security scanning setup in a mid-sized engineering organization looks something like this: one tool for container image scanning, another for infrastructure-as-code misconfigurations, a third for secret detection, a fourth for software bill of materials generation, and possibly a fifth to scan the running Kubernetes cluster. Each tool has its own installation method, its own configuration format, its own output schema, and its own CI/CD integration. The result is not better security — it is operational fatigue. Engineers spend more time maintaining the scanning infrastructure than responding to the findings it produces.

Unified vulnerability and misconfiguration scanning addresses this problem at its root. Instead of assembling a patchwork of specialized scanners, a single tool that understands container images, filesystems, Git repositories, Kubernetes clusters, and infrastructure-as-code templates provides consistent severity ratings, a unified output format, and a single configuration surface. This is the category that Trivy occupies, and it is the reason the tool has become a default choice in registries like Harbor and in countless CI pipelines. The capability itself — unified, open-source scanning across targets — is durable regardless of which specific tool implements it. The principles you learn here transfer to any scanner that follows the same unified model.

> **Hypothetical scenario:**
>
> A platform team at a growing SaaS company is preparing for their first SOC 2 Type II audit. They have 30 microservices, each with its own Dockerfile, a Terraform-managed infrastructure, and a Kubernetes cluster running in production. Six weeks before the audit, they discover they have no documented evidence that container images are scanned before deployment. The engineering manager evaluates five separate tools — Grype for containers, Checkov for Terraform, Syft for SBOMs, Gitleaks for secrets, and a commercial scanner for the cluster — and estimates three weeks of integration work plus ongoing maintenance across five CI configurations. A colleague suggests trying a single unified scanner. After a two-hour proof of concept, they have container scanning, IaC auditing, secret detection, and SBOM generation all running from one tool, with a single JSON output format and one `.trivyignore` file for accepted risks. The integration effort drops from three weeks to two days. The audit passes because every image has a scan record, every deployment has an SBOM, and every Terraform change is checked for misconfigurations before apply. The team redirects the saved engineering time toward actually fixing the vulnerabilities the scanner found.

Understanding unified scanning means you can decide intelligently whether one tool that is "good enough" across all targets serves your organization better than a collection of best-in-breed point solutions — and you will know how to implement either choice correctly.

---

## The Unified Scanning Philosophy

Every security scanner operates on the same fundamental model: it examines a target, compares what it finds against a database of known issues, and produces a report. What changes between tools is which targets they can examine and which databases they consult. When an organization deploys separate scanners for container images, infrastructure code, Git repositories, and running clusters, it is not gaining fundamentally different capabilities — it is paying the integration tax multiple times.

The integration tax shows up in several concrete ways. First, each tool produces findings in its own format: one outputs JSON with a `vulnerabilities` array, another uses a `findings` key with different field names, and a third produces SARIF while a fourth uses a proprietary schema. To build a unified dashboard or feed findings into a SIEM, someone has to write and maintain a normalization layer that understands each schema. Second, severity ratings are not consistent across tools. A vulnerability that one scanner rates CRITICAL might register as HIGH in another because they consult different advisory databases or apply different environmental adjustments. This inconsistency erodes trust: when the dashboard shows conflicting severities for the same CVE, teams learn to ignore both. Third, each tool requires its own configuration for ignoring false positives, setting severity thresholds, and defining scan scope. When a new CVE drops and every team needs to add an exception, they have to update five different ignore files in five different formats.

A unified scanner collapses all of this into a single operational surface. One JSON schema for all findings. One severity scale applied consistently because the same vulnerability database backs every target. One configuration file for ignore rules and thresholds. One CI integration that covers container, filesystem, IaC, and secret scanning in a single pipeline step. The operational simplification is not a minor convenience — it is the difference between a scanning program that engineers maintain and one they abandon.

This philosophy aligns directly with the DevSecOps principle of making security "invisible" to developers: the scanner should integrate into existing workflows without demanding that developers learn five different tools, five different output formats, and five different exception processes. When security tooling creates friction, developers route around it. When it is transparent, they accept it as part of the build pipeline, and scanning coverage approaches 100 percent. Cross-reference the DevSecOps tool-class taxonomy in [Module 4.1: DevSecOps Fundamentals](/platform/disciplines/reliability-security/devsecops/module-4.1-devsecops-fundamentals/) for the broader architectural context in which unified scanning operates.

---

## How Image Scanning Works Under the Hood

Container image scanning is the capability most people associate with vulnerability scanners, and understanding its internals reveals why some findings matter more than others. When Trivy scans a container image, it does not simply run a single check. It decomposes the image into layers, identifies every installed package across both the operating system layer and the application dependency layer, and cross-references each package against multiple vulnerability databases.

### OS Packages vs. Language Dependencies

A container image typically contains two distinct categories of software. The operating system packages — `libssl`, `curl`, `glibc`, `openssl` — come from the base image's package manager (apt, apk, yum). Language dependencies — `express`, `lodash`, `requests`, `jackson-databind` — come from the application's package manager (npm, pip, maven, bundler). These two categories are fundamentally different in how they are updated and how their vulnerabilities should be handled. An OS package vulnerability is fixed by rebuilding the image with an updated base image tag. A language dependency vulnerability is fixed by updating a version constraint in `package.json` or `requirements.txt` and rebuilding. Understanding this distinction matters because the remediation path is different, and the urgency may be different too — an OS-level remote code execution vulnerability in `openssl` is typically more dangerous than a prototype pollution vulnerability in a frontend JavaScript library that never processes untrusted input.

Trivy separates these findings in its output, labeling OS package vulnerabilities with their source package name and language vulnerabilities with their ecosystem and library name. This separation allows teams to route findings to the right owners: OS vulnerabilities to the platform team managing base images, and language vulnerabilities to the application teams owning the dependency manifests.

### The Vulnerability Database Pipeline

At the heart of every scanner is a vulnerability database. Trivy maintains its own database — the Trivy DB — which aggregates advisories from multiple upstream sources: the National Vulnerability Database (NVD), distribution-specific security trackers (Debian Security Tracker, Red Hat Security Data, Alpine SecDB), GitHub Security Advisories, and language-specific advisory databases (npm audit, PyPA Advisory Database, RustSec). The Trivy DB is updated every six hours and distributed as a compact binary blob that the scanner downloads and caches locally. This local caching is the reason Trivy can complete a first scan in seconds rather than minutes: the database is already on disk, and subsequent scans only query it and download incremental updates.

The freshness of the vulnerability database is a critical operational concern. A scanner with a week-old database will miss vulnerabilities disclosed in the last seven days. Trivy's default behavior is to download the latest database before each scan, but in air-gapped environments or CI pipelines where external network access is restricted, you can use the `--skip-db-update` flag and rely on a separately managed database cache. The `--db-repository` flag even allows pointing Trivy at a private OCI registry that mirrors the database, enabling fully offline scanning.

### Layer Caching and Rebuild Economics

Container images are composed of layers, and the vulnerability status of a layer changes only when the packages inside it change. Trivy exploits this by caching scan results per layer. If you rebuild an application image and only the top layer (your application code) changed, Trivy can reuse the cached scan results for all lower layers — the base OS layer, the installed system packages, and the language runtime. This layer-aware caching dramatically reduces scan time in CI pipelines where the same base image is used across many builds.

This caching behavior also explains why pinning image tags matters for security. If your Dockerfile specifies `FROM node:16`, the actual base image you get depends on when the build runs — the `node:16` tag is mutable and may point to a different digest tomorrow than it did today. A vulnerability that did not exist in yesterday's build may appear in today's because the base image was rebuilt with an updated package that introduced a new CVE. Conversely, a vulnerability that was fixed upstream may disappear. To make vulnerability scanning deterministic — and to make audit trails reproducible — always pin base images to digests: `FROM node:16@sha256:abc123...`. This guarantees that the same scan results apply to every build using that exact image, and it prevents the "mystery vulnerability" that appears when a floating tag silently updates.

A concrete example of why this matters: in August 2025, Bitnami moved its container images from the `bitnami/*` namespace to `bitnamilegacy/*` for legacy tags while transitioning to a new versioning scheme. Teams that were pinning to `bitnami/postgresql:14.7.0` found their builds failing because the tag no longer resolved. Teams that were using floating tags found themselves pulling entirely different images with different vulnerability profiles. The lesson is not about Bitnami specifically — it is that image references are contracts, and floating tags break those contracts silently. Pin to digests whenever reproducibility matters.

---

## Infrastructure as Code and Misconfig Scanning

Vulnerability scanning asks "does this software contain known bugs?" Misconfiguration scanning asks a different question: "is this software configured in a way that creates security risk?" The distinction matters because a perfectly patched container running as root with a wide-open security group is still dangerous. Trivy's misconfiguration scanner — which absorbed the capabilities of the former tfsec project when Aqua Security folded it into Trivy — checks infrastructure-as-code templates, Kubernetes manifests, Dockerfiles, and Helm charts against a library of hundreds of policy rules. This consolidation was not just an acquisition — it reflected a deliberate product strategy of making Trivy the single tool that could answer every security question about an artifact, from "does this image contain known vulnerabilities?" to "is this Terraform module going to create an insecure S3 bucket?" to "does this Kubernetes manifest run containers as root?"

### How Policy Checking Works

Each misconfiguration rule in Trivy is a small program that examines a specific pattern in a configuration file. A rule might check that an AWS S3 bucket has server-side encryption enabled, that a Kubernetes container does not run as root, that a Dockerfile does not expose port 22, or that a Terraform security group does not allow ingress from `0.0.0.0/0` on administrative ports. The rule library is organized by platform (AWS, GCP, Azure, Kubernetes, Docker) and by severity (CRITICAL, HIGH, MEDIUM, LOW), following a taxonomy similar to vulnerability severity scoring.

When Trivy scans a directory of Terraform files, it does not execute the Terraform — it parses the HCL directly and builds an internal representation of the resources and their attributes. It then evaluates each applicable rule against that representation. If a rule fires, the finding includes the file path, line number, a description of the issue, and a link to the Aqua Vulnerability Database entry for that misconfiguration ID, which provides remediation guidance.

This approach has a key limitation: Trivy can only check what is statically declared in the configuration files. It cannot detect misconfigurations that arise from dynamic behavior, Terraform modules that generate resources at apply time, or configurations spread across multiple files that only become dangerous in combination. This is not a flaw in Trivy — it is a fundamental constraint of static analysis — but it means that IaC scanning is a complement to, not a replacement for, runtime security controls like admission webhooks and network policies.

### Custom Policies with Rego

For organizations that need to enforce rules beyond the built-in policy library, Trivy supports custom policies written in Rego, the policy language from Open Policy Agent (OPA). A Rego policy for Trivy is a small program that receives the parsed configuration as input and returns a set of rule results. This allows teams to encode organization-specific requirements — for example, "every S3 bucket must have a tag named `data_classification`" or "no Kubernetes Deployment may use the `latest` image tag" — as automated checks that run alongside the built-in rules.

The ability to write custom policies transforms Trivy from a generic scanner into an organization-specific compliance tool. Rather than maintaining a separate policy-as-code system for infrastructure guardrails, teams can encode their infrastructure policies in the same tool that scans for vulnerabilities and secrets. The operational simplification is the same as with unified scanning: one tool, one configuration format, one exception process.

---

## Trivy as the Worked Example

Trivy is an open-source security scanner maintained by Aqua Security. It is distributed as a single static binary (written in Go) with no external runtime dependencies — no database server, no agent, no background service required for basic scanning. This architectural simplicity is a deliberate design choice: a scanner that requires a separate database service to operate is a scanner that cannot run in a CI pipeline without additional infrastructure, which means it will not be run consistently. Trivy's self-contained design — download the binary, run it, get results — removes that barrier entirely.

The tool has been integrated into Harbor as its default vulnerability scanner, is available as a GitHub Action, a Kubernetes operator, a VS Code extension, and a standalone CLI. The current stable version as of mid-2026 is in the 0.71.x line, with active development continuing on GitHub (36,000+ stars as of this writing). The breadth of integration points reflects the unified scanning philosophy: whether a developer wants to scan from their editor, a CI pipeline wants to scan during build, or a cluster operator wants continuous scanning of running workloads, the same tool with the same configuration model and the same output format serves all three contexts.

### Installation

```bash
# macOS (Homebrew)
brew install trivy

# Linux (apt)
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Linux (script)
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Docker (no installation)
docker run aquasec/trivy image nginx:latest

# Verify installation
trivy version
```

### Container Image Scanning

The `trivy image` command is the most commonly used subcommand. It pulls the specified image (or reads it from a local tar file with `--input`), decomposes it into layers, identifies all installed packages and their versions, and cross-references them against the Trivy DB. The output separates OS package findings from language dependency findings, making it clear which team owns each remediation.

```bash
# Scan an image from a registry
trivy image nginx:latest

# Scan with severity filter (only CRITICAL and HIGH findings)
trivy image --severity HIGH,CRITICAL nginx:latest

# Scan only OS-level packages
trivy image --vuln-type os nginx:latest

# Scan only language-level dependencies
trivy image --vuln-type library nginx:latest

# Output as machine-readable JSON
trivy image --format json --output results.json nginx:latest

# Output as SARIF (for GitHub Code Scanning integration)
trivy image --format sarif --output trivy.sarif nginx:latest

# Ignore vulnerabilities with no available fix
trivy image --ignore-unfixed nginx:latest
```

The `--ignore-unfixed` flag is particularly important in operational pipelines. When a CVE is disclosed, it may take days or weeks for the upstream package maintainer to release a patched version. Until a fix is available, a scanner will report the vulnerability on every run. If your CI pipeline blocks on every CRITICAL finding, an unfixed CVE will halt all deployments until a fix is published — which may be outside your control. The `--ignore-unfixed` flag tells Trivy to report only vulnerabilities that have an available fix, so your pipeline gates on actionable findings rather than on the upstream patch release schedule.

This flag embodies a broader principle in security scanning: distinguish between findings you can fix and findings you can only track. A CVE with no available patch is still a risk, and it still belongs in your vulnerability register, but blocking deployments on it does not reduce risk — it only reduces delivery velocity. The correct response to an unfixed CVE is to assess whether the vulnerable code path is reachable in your application, document the assessment in a VEX statement or an exception tracker, and set a review cadence to re-evaluate when a patch becomes available. The scanner's job is to surface the finding; the team's job is to decide what to do about it. A pipeline gate that cannot distinguish "fixable" from "trackable" conflates these two very different categories and eventually trains teams to route around the gate entirely.

### Filesystem and Repository Scanning

The `trivy fs` command scans a local directory tree, identifying dependency manifests (`package.json`, `go.sum`, `requirements.txt`, `pom.xml`, and dozens of others) and checking them against language-specific vulnerability databases. It can also scan for secrets and misconfigurations in the same pass.

When you run `trivy fs .` in a project root, Trivy recursively walks the directory tree, detects which package ecosystems are present by matching known manifest filenames, parses each manifest to extract the dependency graph (including transitive dependencies), and cross-references every resolved version against the appropriate advisory database. For a Node.js project, it reads `package-lock.json` to get the exact resolved versions rather than the semver ranges in `package.json`, because a version range like `^4.17.0` does not tell you whether the installed version is 4.17.20 (vulnerable) or 4.17.21 (patched). This is why lockfiles are critical for accurate scanning: without a lockfile, Trivy must assume the worst case for every semver range, which produces false positives for ranges that would resolve to a patched version in practice.

```bash
# Scan the current directory for vulnerabilities
trivy fs .

# Scan with all scanners enabled (vulnerabilities, secrets, misconfigs)
trivy fs --scanners vuln,secret,misconfig .

# Scan only specific package ecosystems
trivy fs --pkg-types npm,pip .
```

The `trivy repo` command is a convenience wrapper that clones a remote repository, scans it, and discards the clone. It is useful for auditing third-party dependencies or checking an open-source project before incorporating it into your supply chain. For reproducibility, always scan a specific commit rather than a branch head.

```bash
# Scan a remote Git repository
trivy repo https://github.com/aquasecurity/trivy

# Scan a specific branch or commit
trivy repo --branch develop https://github.com/myorg/myrepo
```

### Secret Detection

Trivy's secret scanner checks for over 100 patterns of credentials, API keys, private keys, and tokens. It scans both the current filesystem state and, when used with `trivy repo`, the entire Git history. The scanner uses regular expressions and entropy-based heuristics to identify potential secrets without requiring a pre-configured list of known credential formats.

Secret scanning is most effective when it runs in pre-commit hooks or early in CI, before a secret ever reaches a shared repository. Once a secret is committed to Git, even if it is later removed, it remains in the commit history and must be rotated. Trivy's scanner can detect secrets in existing commits, but detection after the fact is damage control, not prevention. The real value of secret scanning is in catching credentials before they are pushed — integrated into a pre-commit hook via `trivy fs --scanners secret` on staged files, or run as the first step in CI before any other tool touches the codebase.

One operational nuance: secret scanners produce false positives on test fixtures, example configuration files, and documentation. A file named `config/example.env` that contains `AWS_SECRET_ACCESS_KEY=your-secret-key` is not a leak, but a regex-based scanner does not know the difference between example documentation and a real credential. This is why `.trivyignore` entries and scanner configuration with path exclusions are essential — without them, every CI run flags the same documentation files, and teams learn to ignore all secret findings rather than triaging them individually.

```bash
# Scan for secrets in the current directory
trivy fs --scanners secret .

# Scan a container image for embedded secrets
trivy image --scanners secret nginx:latest

# Scan a Git repository including history
trivy repo --scanners secret https://github.com/myorg/myrepo
```

---

## Kubernetes Cluster Scanning and the Trivy Operator

Scanning container images in CI catches vulnerabilities before deployment, but it does not protect against vulnerabilities disclosed after deployment. A container image that was clean when it shipped last Tuesday may have three new CRITICAL CVEs by Friday. The only way to catch these is to scan running workloads continuously.

### The Trivy Operator

The Trivy Operator is a Kubernetes operator that runs inside the cluster and automatically scans every workload as it is deployed and on a configurable schedule thereafter. It produces Kubernetes custom resources — `VulnerabilityReport`, `ConfigAuditReport`, `ExposedSecretReport`, and others — that describe the security posture of each workload. These reports are namespaced resources, meaning each namespace's reports are isolated and can be accessed by the teams that own those namespaces.

```bash
# Install the Trivy Operator via Helm
helm repo add aqua https://aquasecurity.github.io/helm-charts/
helm repo update
helm install trivy-operator aqua/trivy-operator \
  --namespace trivy-system \
  --create-namespace \
  --set trivy.ignoreUnfixed=true

# List vulnerability reports across all namespaces
kubectl get vulnerabilityreports -A

# List config audit reports
kubectl get configauditreports -A

# Inspect a specific report
kubectl describe vulnerabilityreport replicaset-nginx-6d4cf56db-nginx
```

The operator approach has two major advantages over CI-only scanning. First, it catches vulnerabilities that are disclosed after deployment — the operator rescans images periodically (default: every 24 hours) and updates the reports when new CVEs appear. Second, it provides a Kubernetes-native API for querying security posture. A dashboard like Octant or a custom controller can watch `VulnerabilityReport` resources and alert when a running workload acquires a new CRITICAL finding.

### Manual Cluster Scanning

For ad-hoc auditing, the `trivy k8s` command can scan a running cluster using your current kubeconfig context. It enumerates pods, deployments, and other resources, pulls the images they reference, and scans them.

```bash
# Scan the entire cluster and produce a summary report
trivy k8s cluster --report summary

# Scan a specific namespace
trivy k8s --namespace production cluster

# Scan a specific resource
trivy k8s --include-namespaces default deployment/nginx
```

---

## CI/CD Integration and the Shift-Left Security Model

The "shift-left" principle in security means moving detection as early as possible in the development lifecycle. A vulnerability caught during local development costs minutes to fix. The same vulnerability caught in production costs hours of incident response, a rollback, and a patched redeployment. Trivy's design — a single binary with deterministic exit codes and multiple output formats — makes it straightforward to integrate into any CI system.

### Exit Codes as Policy Gates

Trivy uses exit codes to signal scan results to the CI system. The default behavior is to exit 0 (success) regardless of findings, which is appropriate for informational scanning. With `--exit-code 1`, Trivy exits with code 1 if any vulnerabilities are found at the specified severity level or above. This allows a CI pipeline to treat the scan as a quality gate: if the exit code is non-zero, the pipeline fails and the deployment is blocked.

The severity threshold is a policy decision that each team must make based on their risk tolerance and operational reality. Blocking on CRITICAL only is common because it prevents known-exploitable vulnerabilities from reaching production without creating excessive friction. Blocking on HIGH catches more issues but can stall deployments when a new CVE is disclosed that affects a widely-used library and no patch is yet available. The threshold should be paired with `--ignore-unfixed` so that findings without available fixes are reported but do not block the pipeline — otherwise a single CVE with no upstream patch can halt all deployments indefinitely, which is operationally indistinguishable from a denial-of-service attack on your delivery pipeline.

```bash
# Report only (always succeeds)
trivy image myapp:latest

# Gate on CRITICAL findings
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Gate on HIGH or CRITICAL
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:latest
```

### GitHub Actions Integration

```yaml
# .github/workflows/trivy.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          format: 'sarif'
          output: 'trivy-fs.sarif'

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Trivy image scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-image.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Trivy config scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: './terraform'
          severity: 'CRITICAL,HIGH'
          format: 'sarif'
          output: 'trivy-config.sarif'

      - name: Upload to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: '.'
```

Note on the `trivy-action` version: following the TeamPCP supply chain incident in March 2026 where threat actors rewrote Git tags in the `trivy-action` repository (tag `v0.69.4` was pointed to a malicious release that exfiltrated CI/CD secrets), the community recommendation is to pin GitHub Actions to commit SHAs, not tags. See [Module 4.4: Supply Chain Security](/platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/) for the full postmortem and mitigation strategies. If you are using `trivy-action` in production, pin to a specific commit SHA rather than `@master` or a version tag.

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - scan

trivy-scan:
  stage: scan
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy fs --exit-code 0 --severity HIGH,CRITICAL .
    - trivy image --exit-code 1 --severity CRITICAL $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - trivy config --exit-code 0 --severity HIGH,CRITICAL ./terraform/
  artifacts:
    reports:
      container_scanning: gl-container-scanning-report.json
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Security Scan') {
            steps {
                sh '''
                    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                    trivy fs --severity HIGH,CRITICAL --exit-code 0 .
                    docker build -t myapp:${BUILD_NUMBER} .
                    trivy image --severity CRITICAL --exit-code 1 myapp:${BUILD_NUMBER}
                    trivy config --severity HIGH,CRITICAL ./terraform/
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '**/trivy-*.json', allowEmptyArchive: true
        }
    }
}
```

---

## SBOM Generation and the Transparency Chain

A Software Bill of Materials (SBOM) is a structured inventory of every component in a software artifact — every library, every package, every dependency, including transitive dependencies. An SBOM does not tell you whether those components have vulnerabilities. It tells you what you have, so that when a vulnerability is disclosed, you can answer the question "are we affected?" without scanning every image from scratch.

The operational value of an SBOM becomes most apparent during high-severity vulnerability events. When a vulnerability like Log4Shell (CVE-2021-44228)<!-- incident-xref: log4shell --> is disclosed, the first question every organization must answer is: which of our running applications include the affected library? Without SBOMs, answering this question requires scanning every container image in every registry and every running workload in every cluster — a process that can take hours or days, during which the vulnerable systems remain exposed. With SBOMs generated at build time and stored alongside images (or in a searchable document store), the same question can be answered in minutes by scanning SBOMs against the updated vulnerability database. The SBOM is not a security control by itself — it is an accelerant for every other security process that depends on knowing what is running where.

Trivy can generate SBOMs in both major industry formats: CycloneDX (OWASP) and SPDX (Linux Foundation). These are the two formats recognized by the US Executive Order on Improving the Nation's Cybersecurity and by the EU Cyber Resilience Act, making them the de facto standards for software supply chain transparency.

```bash
# Generate CycloneDX SBOM from a container image
trivy image --format cyclonedx --output sbom.json nginx:latest

# Generate SPDX SBOM
trivy image --format spdx-json --output sbom.spdx.json nginx:latest

# Generate SBOM from a filesystem (source code dependencies)
trivy fs --format cyclonedx --output sbom.json .

# Scan an existing SBOM for vulnerabilities
trivy sbom sbom.json
```

The `trivy sbom` command is particularly powerful: it can take an SBOM generated months ago and scan it against the current vulnerability database. This means you do not need to keep old container images around to check whether a newly disclosed CVE affects them. If you generated an SBOM at build time and stored it (in an OCI registry via `cosign attach sbom`, or in a document store), you can scan that SBOM against the latest Trivy DB and immediately know which of your deployed artifacts are affected by a new vulnerability.

### VEX: Documenting Non-Exploitability

Not every vulnerability finding is actionable. A CVE in a library function that your code never calls is a finding on paper but not a risk in practice. The Vulnerability Exploitability eXchange (VEX) standard provides a machine-readable way to document that a vulnerability is "not affected" in your specific context, with a justification that auditors can review.

```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/myapp",
  "author": "Security Team",
  "timestamp": "2026-06-15T00:00:00Z",
  "statements": [
    {
      "vulnerability": { "@id": "CVE-2025-12345" },
      "products": [{ "@id": "pkg:docker/myapp@1.0.0" }],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "The vulnerable function is in a code path that our application does not exercise."
    }
  ]
}
```

```bash
# Scan with VEX suppression
trivy image --vex vex.json myapp:latest
```

A VEX document turns noise into signal. Without it, every scan reports the same unactionable CVEs, and teams learn to ignore the scanner. With VEX, the scanner reports only findings that the organization has not already triaged and documented as non-exploitable. The VEX file becomes part of the compliance audit trail — it is evidence that a finding was reviewed, not ignored.

---

## Ignoring Findings with .trivyignore

For CVEs or misconfigurations that are accepted risks but do not warrant a full VEX statement, Trivy supports a simple ignore file. Each line specifies a CVE ID, a misconfiguration ID, or a package identifier to suppress. Entries can include an expiration date, after which the ignore rule stops applying and the finding reappears — preventing temporary workarounds from becoming permanent blind spots.

```
# .trivyignore

# Ignore a specific CVE (no expiration — permanent suppression)
CVE-2025-12345

# Ignore with expiration — finding reappears after the date
CVE-2025-67890 exp:2026-12-31

# Ignore by package identifier
pkg:npm/lodash@4.17.20

# Ignore a misconfiguration rule
AVD-AWS-0088
```

The expiration mechanism is critical for operational hygiene. Without it, an ignore file accumulates entries indefinitely, and vulnerabilities that were temporarily accepted because no fix existed become permanently invisible even after a fix is published. Setting a 90-day or 180-day expiration forces periodic re-review. When an expiration date arrives and the finding reappears in scan output, the team has three options: apply the now-available fix, extend the expiration with a new justification if the fix is still unavailable, or accept the risk permanently with a documented rationale. The key principle is that every suppression should have a documented decision behind it, and that decision should be revisited on a schedule rather than allowed to fossilize.

The `.trivyignore` file should be checked into the repository alongside the code it governs, so that ignore decisions are version-controlled and reviewable in pull requests. A central security team maintaining a single global ignore file for all projects is an anti-pattern — the team closest to the code has the context to assess whether a CVE is exploitable in their specific application, and they should own their own exception decisions, with the security team providing oversight through PR review rather than acting as a gatekeeper.

---

## Patterns and Anti-Patterns

### Patterns

**Scan everywhere.** Run Trivy in CI (on every push), at the registry (Harbor's built-in scanner), and in the cluster (Trivy Operator). Each layer catches what the previous one missed. CI catches issues before deployment, the registry gate catches images pushed outside CI, and the cluster scanner catches vulnerabilities disclosed after deployment. This layering is not redundant — each scanning point has a different view of the artifact lifecycle, and a gap at any layer creates a blind spot that the other layers cannot fully close.

**Block on CRITICAL, alert on HIGH.** The CI pipeline should fail on CRITICAL vulnerabilities with available fixes. HIGH findings should generate alerts (Slack, PagerDuty, dashboard) but not block deployment. This balances security with delivery velocity — the pipeline enforces the floor, and the alerting system drives continuous improvement above the floor. The alternative, blocking on all severity levels, creates a perverse incentive: developers who cannot ship because of a MEDIUM finding in a transitive dependency they do not control will find ways to bypass the scanner entirely, and the organization ends up with less security, not more.

**Generate an SBOM at every build and store it with the image.** Use `cosign attach sbom` to attach the SBOM to the image in the registry. When a new CVE is disclosed, scan stored SBOMs against the updated database to identify affected artifacts without re-pulling every image. The storage cost of an SBOM is negligible (typically a few kilobytes of JSON), and the time savings during an incident are measured in hours.

**Use VEX or .trivyignore with expirations for accepted risks.** Every suppressed finding should have an owner and a review date. Temporary workarounds that become permanent blind spots are a common failure mode in scanning programs. Set expirations of 90 to 180 days and route the review to the team that owns the affected component, not to a central security team that lacks the context to assess exploitability.

### Anti-Patterns

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| Only scanning in CI | New CVEs are disclosed after deployment. A clean CI scan on Tuesday means nothing on Friday. | Deploy the Trivy Operator for continuous cluster scanning. |
| Blocking on all severity levels | Developers find workarounds (skipping scans, pushing directly to registry) when every build is blocked. | Block only on CRITICAL with available fixes; alert on HIGH. |
| Running scans without caching | Full database downloads on every CI run waste time and bandwidth. Slow scans encourage developers to disable them. | Cache the Trivy DB using GitHub Actions cache or a persistent volume. |
| No SBOM generation | Without an SBOM, a new CVE requires re-scanning every image individually. With an SBOM, a single query identifies all affected artifacts. | Generate CycloneDX SBOMs and store them alongside images. |
| Ignoring IaC findings | A misconfigured security group is as dangerous as a vulnerable library. Teams often focus on CVEs because they are "real vulnerabilities" while ignoring configuration issues. | Include `trivy config` in every CI pipeline, with the same severity thresholds as image scanning. |
| Manual triage of every finding | Does not scale beyond a handful of services. Engineers burn out reviewing false positives. | Automate policy decisions with severity thresholds and VEX documents. Reserve manual review for exceptions. |
| Different tools for different targets | Inconsistent severity ratings, multiple output formats, and fragmented configurations create operational overhead that kills scanning programs. | Use a unified scanner (Trivy or an equivalent) across all targets. |
| Pinning to floating tags | `FROM node:16` pulls a different image tomorrow than today. Scan results from last week are meaningless. | Pin to digests: `FROM node:16@sha256:abc123...` |

---

## Decision Framework: Choosing a Unified Scanner

When selecting a vulnerability and misconfiguration scanner, the durable capability dimensions are independent of any specific vendor or version. The table below compares the major open-source and commercial options on these dimensions as of mid-2026. This landscape changes fast — verify against current vendor documentation before making procurement decisions.

**Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

### Rosetta: Capability Comparison

| Capability | Trivy (Aqua, OSS) | Grype + Syft (Anchore, OSS) | Clair (Red Hat/Quay, OSS) | Snyk (Commercial) |
|---|---|---|---|---|
| **Image scanning** | OS + language packages | OS + language packages | OS packages primarily | OS + language packages |
| **Filesystem / repo scanning** | Yes (`trivy fs`, `trivy repo`) | Grype scans directories; Syft generates SBOMs | No | Yes (CLI + SCM integration) |
| **IaC / misconfig scanning** | Yes (Terraform, K8s, Docker, CloudFormation, Helm, Ansible) | No | No | Yes (Terraform, K8s, CloudFormation, ARM) |
| **Kubernetes cluster scanning** | Yes (Operator + `trivy k8s`) | No | Via Clair operator (limited) | Yes (Kubernetes integration) |
| **SBOM generation** | CycloneDX, SPDX | Syft: CycloneDX, SPDX | No | CycloneDX, SPDX |
| **Secret detection** | Yes (100+ patterns) | No | No | Yes |
| **In-cluster operator** | Trivy Operator (VulnerabilityReport CRDs) | No | Clair operator (limited) | Yes (Snyk monitor) |
| **OSS vs commercial** | Fully open-source (Apache 2.0); commercial Aqua Platform available | Fully open-source (Apache 2.0); commercial Anchore Enterprise available | Fully open-source (Apache 2.0) | Freemium; enterprise features require paid tier |
| **CI integration** | GitHub Actions, GitLab CI, Jenkins, CircleCI, and others | GitHub Actions, GitLab CI | Limited; primarily registry-integrated | Extensive CI/CD integrations, IDE plugins, PR comments |
| **Custom policies** | Rego (OPA) for misconfigs | No | No | Custom rules in Snyk policy language |
| **Auto-fix / remediation** | No | No | No | Yes (automated PRs for dependency upgrades) |

None of these tools is universally "best." Choose based on the capabilities you need today and the operational overhead you can absorb. A team that needs auto-fix PRs and IDE integration may choose Snyk despite its cost. A team that wants a single free tool covering all targets may choose Trivy. A team already invested in the Anchore ecosystem may pair Grype with Syft. Cross-reference [Module 12.4: Snyk - Developer-First Security](/platform/toolkits/security-quality/code-quality/module-12.4-snyk/) for the commercial peer to Trivy's open-source model, including when paid features like auto-fix and IDE integration justify the licensing cost.

---

## Did You Know?

- **Trivy was created by Teppei Fukuda at Aqua Security, with its first release in 2019.** It was built because existing scanners were operationally heavy — they typically required a separate database service and were awkward to wire into CI. The durable design insight was packaging the vulnerability database into a compact, self-contained bundle that a client downloads once and caches locally, so a scan needs no database server and runs quickly inside a pipeline. That single-binary, no-server model is the reason Trivy fits naturally into CI steps and registry-gate workflows.

- **Harbor selected Trivy as its default vulnerability scanner after evaluating multiple alternatives.** The Harbor registry, itself a CNCF Graduated project, ships with Trivy as the built-in scanner that runs automatically on every pushed image. This means any organization running Harbor already has Trivy integrated into their image pipeline — the scanner runs at the registry gate, blocking vulnerable images from being pulled, even if the CI pipeline does not include its own scan step. See the [Harbor vulnerability scanning documentation](https://goharbor.io/docs/latest/administration/vulnerability-scanning/) for configuration details.

- **Trivy scans for secrets across over 100 patterns, including cloud provider credentials, API keys, and private keys.** The secret scanner uses both regular expression matching (for structured credentials like AWS access keys which follow the `AKIA...` pattern) and entropy analysis (for high-entropy strings that look like randomly generated tokens). Secret scanning is integrated into the same `trivy fs` and `trivy image` commands that handle vulnerability detection — no separate tool or configuration required. The detection patterns are maintained in the Trivy source repository and updated as new credential formats emerge from cloud providers and SaaS platforms.

- **The Trivy vulnerability database is updated every six hours and can be mirrored to a private OCI registry.** For air-gapped environments where scanners cannot reach the internet, Trivy supports downloading the database once from a connected machine, pushing it to an internal OCI-compatible registry, and configuring all internal scanners to pull from that mirror using the `--db-repository` flag. This decouples scanning from internet access — a critical capability for regulated industries, government systems, and high-security environments where build servers are isolated from external networks.

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---|---|---|
| Blocking on all severity levels | Developers find workarounds when every build is blocked. They push directly to the registry or comment out the scan step. | Block on CRITICAL with available fixes; alert on HIGH. |
| No .trivyignore or VEX file | The same false positives appear on every scan, training teams to ignore scanner output entirely. | Document accepted risks with expiration dates. Review quarterly. |
| Scanning without caching in CI | Full database downloads on every pipeline run waste 30-60 seconds per job. Over 100 builds per day, that is hours of wasted CI time. | Cache the Trivy DB using your CI system's cache mechanism. |
| Only scanning in CI, not in the cluster | A CVE disclosed on Wednesday affects workloads deployed on Monday. CI-only scanning misses the entire fleet of running containers. | Deploy Trivy Operator for continuous cluster scanning. |
| Ignoring IaC misconfigurations | Teams treat CVEs as "real findings" and configuration issues as "nice to have." A wide-open security group is a CVE in practice. | Include `trivy config` with the same severity thresholds as image scanning. |
| No SBOM generation | When Log4Shell-level<!-- incident-xref: log4shell --> vulnerabilities are disclosed, you cannot answer "are we affected?" without re-scanning every image. | Generate CycloneDX SBOMs at build time and store them with the image. |
| Manual triage of all findings | Engineers spend hours reviewing CVEs that could be automatically classified by severity and fix availability. | Automate with severity gates and VEX documents. Reserve manual review for exceptions. |
| Using floating image tags | `FROM node:16` pulls different content over time. Scan results become non-reproducible, and audit trails lose meaning. | Pin to digests: `FROM node:16@sha256:abc123...` |

---

## Quiz

### Question 1

What is the key operational advantage of a unified scanner like Trivy over deploying separate specialized tools for container images, IaC, secrets, and SBOMs?

<details>
<summary>Answer</summary>

A unified scanner provides a single JSON or SARIF output schema, one configuration file for ignore rules and severity thresholds, and one CI integration across all scanning targets. This eliminates the normalization layer that would otherwise be needed to merge findings from five different tools with five different output formats and five different severity scales. The operational simplification is the difference between a scanning program that engineers maintain and one they eventually disable because the integration overhead exceeds the perceived security benefit. When findings are inconsistent across tools, teams learn to distrust all of them — a single consistent severity scale across all targets prevents that erosion of trust.
</details>

### Question 2

How does Trivy's `--ignore-unfixed` flag affect scan results, and why is it important in CI pipelines?

<details>
<summary>Answer</summary>

The `--ignore-unfixed` flag suppresses vulnerabilities for which no patch has been released by the upstream package maintainer. Without this flag, a newly disclosed CVE with no available fix will appear on every CI scan and, if the pipeline is configured to block on CRITICAL findings with `--exit-code 1`, will halt all deployments until a fix is published — which may take days or weeks and is outside the team's control. Using `--ignore-unfixed` gates the pipeline only on actionable findings where a remediation path exists, preventing the upstream patch release schedule from becoming a deployment blocker. The tradeoff is that you accept the risk of known-but-unfixable vulnerabilities in production, which should be tracked separately through your vulnerability management process.
</details>

### Question 3

What is the purpose of the Trivy Operator in a Kubernetes cluster, and how does it complement CI-based scanning?

<details>
<summary>Answer</summary>

The Trivy Operator runs inside the cluster and continuously scans deployed workloads, producing Kubernetes custom resources (`VulnerabilityReport`, `ConfigAuditReport`, `ExposedSecretReport`) that describe each workload's current security posture. It complements CI-based scanning by catching vulnerabilities disclosed after deployment — a container image that was clean when it shipped on Monday may have three new CRITICAL CVEs by Thursday, and CI-only scanning will never detect those because the image has already been deployed. The operator rescans images on a configurable schedule (default: every 24 hours) and updates the reports when new CVEs appear, providing a Kubernetes-native API that dashboards and alerting systems can watch.
</details>

### Question 4

Why does pinning container image references to digests matter for vulnerability scanning?

<details>
<summary>Answer</summary>

Floating tags like `nginx:latest` or `node:16` are mutable — they can point to different image digests at different times as the upstream maintainer rebuilds and republishes the tag. This breaks the reproducibility of vulnerability scans because a scan performed last week against `node:16` may not correspond to the image actually deployed today, which was pulled from the same tag but a different digest. Worse, a CVE that was not present in last week's build may appear in today's because the base image was silently updated with a new package version. Pinning to a digest (`node:16@sha256:abc123...`) makes scans deterministic, audit trails reproducible, and vulnerability status changes traceable to specific image rebuilds rather than mysterious "it worked yesterday" failures.
</details>

### Question 5

A team's CI pipeline blocks on HIGH and CRITICAL vulnerabilities. After a widely-publicized CVE is disclosed in a common library, all deployments are blocked for three days because no upstream fix exists yet. What configuration change would you recommend?

<details>
<summary>Answer</summary>

Add the `--ignore-unfixed` flag to the Trivy invocation so that only vulnerabilities with available fixes cause the pipeline to fail. For the specific CVE blocking deployments, add it to `.trivyignore` with an expiration date (e.g., `exp:2026-09-15`) so the suppression is automatically re-reviewed when a fix is expected. Additionally, lower the blocking threshold from HIGH to CRITICAL — blocking on HIGH findings creates too much friction during zero-day events when fixes are not immediately available. HIGH findings should generate alerts (Slack, dashboard) but not block the pipeline. The three-day deployment freeze was caused by a pipeline configuration that treated "known but unfixable" the same as "known and fixable," which are operationally very different categories.
</details>

### Question 6

What are the two industry-standard SBOM formats that Trivy supports, and what is the operational value of generating an SBOM at build time?

<details>
<summary>Answer</summary>

Trivy supports CycloneDX (OWASP) and SPDX (Linux Foundation), the two formats recognized by the US Executive Order on Improving the Nation's Cybersecurity and the EU Cyber Resilience Act. The operational value of generating an SBOM at build time is that when a new CVE is disclosed, you can scan stored SBOMs against the updated vulnerability database using `trivy sbom` without re-pulling every container image. This reduces the "are we affected?" query from a fleet-wide re-scan of potentially thousands of images to a single query against a document store. SBOMs can be attached to images in the registry using `cosign attach sbom`, making them discoverable alongside the artifact they describe.
</details>

### Question 7

A platform team is evaluating Trivy against Grype + Syft and Snyk. They need container scanning, IaC scanning, K8s cluster scanning, and SBOM generation. Which tool covers all four capabilities without requiring additional tooling?

<details>
<summary>Answer</summary>

Trivy covers all four capabilities: container image scanning (`trivy image`), IaC misconfig scanning (`trivy config` for Terraform, K8s manifests, Dockerfiles, and more), Kubernetes cluster scanning (`trivy k8s` and the Trivy Operator), and SBOM generation (`--format cyclonedx` or `--format spdx-json`). Grype handles container scanning, and Syft handles SBOM generation, but neither covers IaC or K8s cluster scanning. Snyk covers all four in its commercial tier but at per-developer licensing cost. The choice depends on whether the team values operational simplicity (one tool, one configuration) over best-in-breed depth in any single category, and whether they have budget for commercial licensing.
</details>

### Question 8

What is the difference between `.trivyignore` and a VEX document, and when would you use each?

<details>
<summary>Answer</summary>

`.trivyignore` is a simple text file listing CVE IDs or misconfiguration IDs to suppress, with optional expiration dates. It is appropriate for quick, local suppressions — a false positive in a specific scan context, or a CVE you have manually verified does not apply. A VEX (Vulnerability Exploitability eXchange) document is a structured, machine-readable JSON document following the openvex.dev specification that includes the vulnerability ID, the affected product, the status (`not_affected`, `fixed`, `under_investigation`), a justification code from a controlled vocabulary, and a human-readable impact statement. VEX is appropriate for organization-wide suppressions that need to be shared across teams, reviewed by auditors, and consumed by multiple tools. Use `.trivyignore` for quick operational exceptions; use VEX for auditable, cross-tool vulnerability triage.
</details>

---

## Hands-On Exercise

### Objective

Set up Trivy for comprehensive security scanning across code, containers, and configuration. By the end of this exercise, you will have run filesystem vulnerability scanning, container image scanning with SBOM generation, infrastructure-as-code misconfiguration detection, and configured a `.trivyignore` file for accepted risks. Each step is designed to be completed in sequence — the later steps depend on the artifacts created in the earlier ones.

### Success Criteria

After completing this exercise, verify that you have achieved the following outcomes:
- [ ] Filesystem scan runs and produces findings
- [ ] Container image scan completes with SBOM generation
- [ ] Infrastructure-as-code scan detects misconfigurations in Terraform and Kubernetes manifests
- [ ] `.trivyignore` is configured with at least one accepted risk with an expiration date

### Setup

```bash
# 1. Create a lab directory
mkdir trivy-lab && cd trivy-lab

# 2. Create a Dockerfile with a known-old base image (will have findings)
cat > Dockerfile << 'EOF'
FROM node:16
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["node", "server.js"]
EOF

# 3. Create a package.json with older dependency versions
cat > package.json << 'EOF'
{
  "name": "trivy-lab",
  "version": "1.0.0",
  "dependencies": {
    "express": "4.17.1",
    "lodash": "4.17.20"
  }
}
EOF

# 4. Create a Terraform configuration with intentional misconfigurations
mkdir terraform
cat > terraform/main.tf << 'EOF'
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
EOF

# 5. Create a Kubernetes manifest with security issues
mkdir k8s
cat > k8s/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:latest
        securityContext:
          runAsUser: 0
          privileged: true
EOF
```

### Scanning

```bash
# 6. Install Trivy (if not already installed)
brew install trivy

# 7. Filesystem scan — vulnerabilities and secrets
trivy fs --scanners vuln,secret .

# 8. Build and scan the container image
docker build -t trivy-lab:latest .
trivy image trivy-lab:latest

# 9. Generate an SBOM for the image
trivy image --format cyclonedx --output sbom.json trivy-lab:latest

# 10. Scan the SBOM itself (demonstrates SBOM scanning workflow)
trivy sbom sbom.json

# 11. Scan infrastructure-as-code
trivy config ./terraform/
trivy config ./k8s/

# 12. Create a .trivyignore for a specific accepted risk
cat > .trivyignore << 'EOF'
# Accept this misconfiguration for the lab environment
AVD-AWS-0088 exp:2026-12-31
EOF

# 13. Re-run IaC scan — the ignored finding should be suppressed
trivy config ./terraform/
```

### Verification

```bash
# Confirm filesystem scan found vulnerabilities
trivy fs . --severity CRITICAL,HIGH --format json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Findings: {len(d.get(\"Results\",[]))}')"

# Confirm SBOM was generated and has components
cat sbom.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Components: {len(d.get(\"components\",[]))}')"

# Confirm IaC scan detected misconfigurations
trivy config ./terraform/ --format json | python3 -c "import sys,json; d=json.load(sys.stdin); results=d.get('Results',[]); misconfigs=[r for r in results if r.get('Misconfigurations')]; print(f'Misconfigurations found: {len(misconfigs)}')"
```

---

## Sources

- [Trivy Documentation](https://trivy.dev) — Official documentation covering all scanners, targets, and configuration options
- [Trivy GitHub Repository](https://github.com/aquasecurity/trivy) — Source code, releases, and issue tracker (Aqua Security, Apache 2.0)
- [Trivy Operator Documentation](https://aquasecurity.github.io/trivy-operator/) — Kubernetes operator for continuous cluster scanning
- [Trivy Operator GitHub](https://github.com/aquasecurity/trivy-operator) — Operator source code and Helm chart
- [Aqua Vulnerability Database](https://avd.aquasec.com/) — Public web interface for Trivy's misconfiguration rules and vulnerability data
- [Grype — Anchore Vulnerability Scanner](https://github.com/anchore/grype) — Open-source vulnerability scanner for container images and filesystems
- [Syft — SBOM Generator](https://github.com/anchore/syft) — Open-source SBOM generation tool (paired with Grype)
- [Clair — Quay Vulnerability Scanner](https://github.com/quay/clair) — Red Hat's open-source container vulnerability scanner
- [CycloneDX Specification](https://cyclonedx.org) — OWASP SBOM standard (XML, JSON, Protocol Buffers)
- [SPDX Specification](https://spdx.dev) — Linux Foundation SBOM standard (tag-value, JSON, YAML, RDF)
- [OpenVEX Specification](https://openvex.dev) — Vulnerability Exploitability eXchange standard
- [Harbor Vulnerability Scanning](https://goharbor.io/docs/latest/administration/vulnerability-scanning/) — Harbor's built-in scanner documentation (defaults to Trivy)
- [Kubernetes Container Images](https://kubernetes.io/docs/concepts/containers/images/) — K8s documentation on image references, tags, and digests
- [Kubernetes Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) — Pod and container security context configuration
- [OWASP Docker Top 10](https://owasp.org/www-project-docker-top-10/) — Top 10 security risks for containerized environments
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html) — Practical Docker security guidance

---

## Next Module

- **Related**: [Module 12.4: Snyk - Developer-First Security](/platform/toolkits/security-quality/code-quality/module-12.4-snyk/) — Commercial alternative with auto-fix and IDE integration
- **Related**: [Module 4.1: DevSecOps Fundamentals](/platform/disciplines/reliability-security/devsecops/module-4.1-devsecops-fundamentals/) — The DevSecOps context in which unified scanning operates
- **Related**: [Module 4.4: Supply Chain Security](/platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/) — SBOM, signing, attestation, and supply chain integrity

---

*A scanner only reduces risk if it actually runs. The durable goal is to make scanning a low-friction, default step wherever code and images enter the system — local development, CI pipelines, and registry gates — rather than a separate task that teams must remember to perform.*
