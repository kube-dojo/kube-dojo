---
title: "Module 5.2: Image Scanning with Trivy"
slug: k8s/cks/part5-supply-chain-security/module-5.2-image-scanning
sidebar:
  order: 2
lab:
  id: cks-5.2-image-scanning
  url: https://killercoda.com/kubedojo/scenario/cks-5.2-image-scanning
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 5.1 (Image Security), Docker basics, and Kubernetes manifests

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Scan** local images, remote registry images, Kubernetes clusters, Kubernetes manifests, and Helm charts with Trivy using verified CLI flags.
2. **Interpret** vulnerability findings by reading CVE identifiers, package evidence, fixed versions, CVSS v3.1 severity bands, vendor severity sources, and exploit context.
3. **Integrate** Trivy into GitHub Actions and GitLab CI with exit-code gates, SARIF or JSON output, cache-aware database updates, and pinned action references.
4. **Triage** false positives and accepted risk through `.trivyignore`, `.trivyignore.yaml`, VEX, Rego policies, and documented allowlist review instead of silent suppression.

## Why This Module Matters

Hypothetical scenario: a team ships an internal API from a Dockerfile that has not changed in months. The application code is clean, tests pass, and the image tag is immutable, yet the next morning a critical OpenSSL advisory lands against the Debian base layer that the image inherited. The image is now riskier than it was yesterday even though no developer edited a line of code, because image risk is a moving relationship between packaged software, advisory databases, runtime exposure, and how quickly the team rebuilds from patched bases.

Trivy is popular in Kubernetes supply-chain work because it gives one practical tool for several exam-relevant views of that problem. It can scan a container image before it reaches a registry, scan a pushed image by reference, inspect a running cluster's workload images and Kubernetes objects, and evaluate Kubernetes manifests or Helm charts for configuration issues. The CKS skill is not memorizing one command. The real skill is knowing what evidence the scanner used, which severities should block a pipeline, which results need human context, and which risks image scanning cannot see at all.

Scanning is also part of governance. The Kubernetes security checklist recommends image scanning before deployment, usually in CI/CD, to obtain vulnerability information such as CVSS scores. NIST SP 800-190 makes a similar operational point for containers: container-specific vulnerability management should account for both image software vulnerabilities and secure configuration settings, because traditional host scanners can miss the immutable-image workflow. A clean Trivy report is therefore not a certificate of safety, but a useful checkpoint in a larger build, admission, runtime, and rebuild process.

On a CKS exam, one realistic scenario includes a Pod manifest using `my-api:latest` because a teammate deployed a hotfix quickly and only updated the manifest image field. A correct response is to resolve and scan the digest actually running (`kubectl` + image name plus SHA), not rerun against `latest`, then verify whether the CVE is still unresolved because the base image in the deployment was still on a known-vulnerable tag while the patch candidate references a newer vendor image alias. That distinction is the difference between passing a lab and understanding how digest drift creates invisible exposure.

## How Trivy Loads Vulnerability Data

Trivy's binary is only the scanner engine. The actionable intelligence arrives through databases that Trivy downloads, caches, and refreshes when scans run. The main vulnerability database is `trivy-db`, the Java database is `trivy-java-db`, and the checks bundle is `trivy-checks` for misconfiguration scanning. In Trivy v0.70.0, the CLI help shows the default vulnerability database repositories as `mirror.gcr.io/aquasec/trivy-db:2` first and `ghcr.io/aquasecurity/trivy-db:2` second, with equivalent defaults for the Java database. That detail matters in restricted environments because database access can be the difference between a meaningful scan and stale evidence.

The upstream data path is intentionally broad. Aqua's `vuln-list` repository tracks NVD, GitHub Advisory Database, GitLab Advisory Database, Debian Security Tracker, Ubuntu CVE Tracker, Alpine secdb, Amazon Linux Security Center, Red Hat OVAL and Security Data, SUSE CVRF, Oracle Linux OVAL, AlmaLinux, Rocky Linux, Arch Linux, Photon OS, and other vendor feeds. Trivy's vulnerability guide also documents language ecosystem sources such as GitHub Advisory Database for Composer, pip, RubyGems, npm, Maven, Go, NuGet, and Pub, plus OS vendor feeds and the Kubernetes official CVE feed for Kubernetes components. A result is therefore a package-to-advisory match, not an independent exploit proof.

```text
Image layers or filesystem
        |
        v
Package discovery
  OS packages, lock files, JARs, binaries, language dependencies
        |
        v
Trivy DBs
  trivy-db, trivy-java-db, trivy-checks
        |
        v
Advisory sources
  NVD, GHSA, OS vendors, language ecosystems, Kubernetes CVE feed
        |
        v
Report
  vulnerability ID, package, installed version, fixed version, severity
```

Database freshness creates an important exam and production habit: read the scan time and understand whether the database was updated. `trivy image --download-db-only` warms the vulnerability database without scanning, while `--skip-db-update` uses the cached database and avoids a network fetch. That is useful in air-gapped CI or when a default-branch cache update job refreshes the database daily, but it is risky if every job skips updates forever. A cached scan can be repeatable and still miss a newly published advisory.

Trivy's default image scan also enables secret scanning, which can make first scans slower and can surprise teams expecting only CVE output. For image-only vulnerability checks in a tight CI loop, `--scanners vuln` narrows the work to vulnerabilities; for a broader supply-chain check, keep secret scanning and misconfiguration checks in separate jobs with separate owners. Mixing all security checks into one gate often produces unclear failures, while splitting them keeps the exit code tied to the decision you actually want to automate.

## Reading Severity and CVSS Without Overreacting

CVSS v3.1 is a standardized way to communicate vulnerability characteristics, but it is not a complete deployment decision. FIRST defines the qualitative severity bands as Low from 0.1 to 3.9, Medium from 4.0 to 6.9, High from 7.0 to 8.9, and Critical from 9.0 to 10.0, with a vector string explaining the metrics that produced the score. Trivy reports severities such as `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`, and the v0.70.0 help confirms `--severity HIGH,CRITICAL` as the filter syntax.

The nuance is source selection. Trivy can use vendor-specific severities because OS vendors backport fixes and evaluate packages in the context of their distribution. An NVD score may describe the upstream software in a general way, while Debian, Red Hat, Ubuntu, or Alpine may rate the package differently based on compilation options, backports, or affected code paths. Trivy exposes `--vuln-severity-source` when you need a source priority, but the safer default for learners is to read the `SeveritySource` in JSON output and compare it with the package family before overriding the scanner's logic.

Two real CVEs show why IDs must be checked rather than invented. NVD lists CVE-2021-44228, Log4Shell in Apache Log4j, as a CVSS v3.1 10.0 Critical remote code execution issue. NVD lists CVE-2024-3094, the xz-utils backdoor, with a Red Hat CNA CVSS v3.1 score of 10.0 Critical and weakness CWE-506 for embedded malicious code. In 2026, NVD also lists CVE-2026-33634 for the Trivy ecosystem supply-chain compromise, with CVSS v3.1 8.8 High and references to Aqua's vendor advisory. Those examples are useful precisely because the CVE identifiers, affected products, and scores can be verified in NVD instead of copied from a scanner table.

```bash
# Human-readable triage view.
trivy image --severity HIGH,CRITICAL nginx:1.27

# Machine-readable evidence for review or dashboards.
trivy image --format json --output trivy-nginx.json nginx:1.27

# Narrow to fixed high-impact vulnerabilities for a fast rebuild gate.
trivy image --ignore-unfixed --severity HIGH,CRITICAL nginx:1.27
```

A severity gate should be boring, predictable, and documented. A common policy is to fail new images on fixed Critical vulnerabilities, warn on High findings, and require a ticket or time-bound exception for any accepted risk. Another common policy fails on both High and Critical only for internet-facing services or production namespaces, while internal batch jobs receive a shorter warning window instead of an immediate block. The correct answer depends on asset exposure, fix availability, business criticality, exploit maturity, and whether the vulnerable package is actually reachable.

## Scanning Images, Registries, Clusters, Manifests, and Helm Charts

Start with the image that will actually run. Trivy can scan an image from a local container engine, remote registry, or tar archive, and the `--image-src` flag lets you prioritize sources such as Docker, containerd, Podman, and remote registries. The `--input` flag scans a saved tar archive, which is useful when a build system exports an image artifact before pushing it. A CKS answer should show the right target: scanning a Dockerfile or repository is useful, but it is not the same as scanning the final image layers after the build.

```bash
# Scan a remote registry image by reference.
trivy image registry.k8s.io/pause:3.10

# Scan a locally built image tag if your container engine has it.
trivy image my-api:dev

# Scan an exported image archive.
docker save my-api:dev -o my-api-dev.tar
trivy image --input my-api-dev.tar

# Use registry credentials without placing the password in shell history.
printf '%s\n' "$REGISTRY_PASSWORD" | trivy image \
  --username "$REGISTRY_USER" \
  --password-stdin \
  registry.example.com/team/my-api:1.2.3
```

Registry scans are where authentication and tag discipline become part of security. A scanner that pulls `latest` may not inspect the same digest that admission later deploys, and a scanner using broad registry credentials can become a high-value CI secret. Prefer immutable digests or release tags, authenticate with a read-only token scoped to the repository being scanned, and publish the scan result next to the artifact it describes. The useful record is "digest X was scanned with database version Y at time Z," not "the pipeline once scanned a name that may now point elsewhere."

Kubernetes cluster scanning answers a different question: what is running now? Trivy v0.70.0 exposes `trivy k8s`, with options such as `--include-namespaces`, `--exclude-namespaces`, `--report summary`, `--report all`, `--skip-images`, and `--kubeconfig`. This is valuable because production clusters can contain old ReplicaSets, CronJobs, init containers, sidecars injected after CI, and manually deployed images that never passed through the expected pipeline. It is also more sensitive operationally because cluster scanning may create node collector jobs unless configured otherwise.

```bash
# Scan the current kubeconfig context and summarize findings.
trivy k8s --report summary

# Limit the scan to one namespace for a focused production review.
trivy k8s --include-namespaces payments --report summary

# Include all report details when exporting evidence for later analysis.
trivy k8s --include-namespaces payments --report all \
  --format json --output trivy-payments-k8s.json

# Scan Kubernetes objects without pulling workload images.
trivy k8s --skip-images --report summary
```

Manifest and Helm scanning catch risks that CVE matching cannot see. `trivy config ./manifests` scans Kubernetes YAML, Dockerfiles, Terraform, Helm, and other IaC formats for misconfiguration checks. For Helm, Trivy renders templates with values and flags such as `--helm-values`, `--helm-set`, `--helm-set-string`, `--helm-set-file`, and `--helm-kube-version`, then runs Kubernetes checks over the rendered manifests. That is the right model for CKS: an image can have zero known CVEs and still run as root, mount the Docker socket, use host networking, or deploy a privileged container.

```bash
# Scan raw Kubernetes YAML for misconfigurations.
trivy config ./manifests

# Render a Helm chart with production values before scanning.
trivy config --helm-values values-prod.yaml ./charts/my-api

# Scan a repository filesystem for vulnerabilities, secrets, and config issues.
trivy fs --scanners vuln,secret,misconfig .
```

The practical workflow is layered. Scan the final image before push, scan the pushed digest before deploy, scan rendered manifests before apply, and scan the cluster periodically to find drift. Each layer has a different failure mode: pre-push scans catch developer image problems, registry scans bind evidence to the deployable artifact, manifest scans catch unsafe Kubernetes configuration, and cluster scans reveal what escaped the pipeline. Treat those layers as complementary instead of asking one Trivy command to prove the whole supply chain is safe.

## CI/CD Gating With GitHub Actions and GitLab CI

In GitHub Actions, the official `aquasecurity/trivy-action` README at commit `314ff8b43182423b84c50b1670b0e10f858f2d98` documents inputs such as `image-ref`, `scan-type`, `scan-ref`, `format`, `exit-code`, `ignore-unfixed`, `vuln-type`, and `severity`. The action's README examples use a version tag, but the March 2026 Trivy ecosystem compromise is a strong reason to pin security-sensitive third-party actions by full commit SHA and update that SHA deliberately. Aqua's own action now pins its dependent `setup-trivy` action by commit internally, which reinforces the same discipline.

```yaml
name: image-security
on:
  pull_request:
  push:
    branches:
      - main

jobs:
  trivy:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      security-events: write
    steps:
      - name: Checkout
        uses: actions/checkout@v5

      - name: Build image
        run: docker build -t docker.io/example/my-api:${{ github.sha }} .

      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@314ff8b43182423b84c50b1670b0e10f858f2d98
        with:
          image-ref: docker.io/example/my-api:${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          exit-code: "1"
          ignore-unfixed: true
          vuln-type: os,library
          severity: CRITICAL,HIGH
```

That workflow is intentionally strict but not magical. `exit-code: "1"` means the action fails when matching vulnerabilities are found, not when all possible risk is eliminated. `ignore-unfixed: true` reduces noise from vulnerabilities that cannot be remediated by rebuilding today, but it can also hide urgent issues where the only realistic action is to change base image, remove a package, or apply a vendor workaround. If the job uploads SARIF to GitHub code scanning, check whether severity filtering behaves the way your team expects for SARIF output and document the policy beside the workflow.

GitLab has two common patterns. GitLab's own container scanning documentation says the container scanning analyzer uses Trivy and passes Trivy environment variables through, while the Trivy documentation also shows a direct GitLab CI job using the `aquasec/trivy` image. The built-in template is easier for GitLab Security Dashboard integration; the direct job is easier for open-source repositories or custom reports. In both cases, keep the job tied to the image digest or tag produced by the same pipeline stage.

```yaml
stages:
  - build
  - scan

variables:
  IMAGE_REF: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA"

build_image:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    - docker build -t "$IMAGE_REF" .
    - docker push "$IMAGE_REF"

trivy_image_scan:
  stage: scan
  image:
    name: docker.io/aquasec/trivy:0.70.0
    entrypoint: [""]
  script:
    - trivy image --exit-code 1 --ignore-unfixed --severity HIGH,CRITICAL "$IMAGE_REF"
```

Design gates around failure domains. A global Critical gate can stop every service in an organization when a widely used base image receives a new advisory, so mature teams separate "newly introduced by this change" from "pre-existing backlog," and they maintain an emergency path for false positives or unavailable fixes. The emergency path should be auditable: who approved the exception, which CVE or advisory ID it covers, when it expires, and what compensating control or rebuild plan exists. A scanner gate without an exception process will be bypassed when it blocks real delivery.

## Handling False Positives and Accepted Risk

False positive handling starts by naming the evidence, not by hiding the finding. A Trivy vulnerability row usually contains the vulnerability ID, package name, installed version, fixed version, severity, primary URL, and source information. Before suppressing it, ask whether the package is from the detected OS vendor, whether the fixed version exists in the image's package repository, whether the vulnerable code is reachable, and whether the image actually runs in the environment being reviewed. Vendor severity and package backports are common reasons for apparent mismatch between scanners.

Trivy supports several suppression mechanisms. The classic `.trivyignore` file suppresses finding IDs for a scan directory, and `--ignorefile` selects a non-default ignore file. The newer `.trivyignore.yaml` format can carry structured ignore entries and expiration metadata, but Trivy's filtering documentation marks explicit `--ignorefile ./.trivyignore.yaml` use as necessary while the feature is still experimental. For advanced cases, `--ignore-policy` evaluates a Rego policy against each finding, and VEX can state that a vulnerability is not exploitable in a particular product context.

```text
# .trivyignore
# Accept until 2026-06-30: package present in debug-only image, not deployed.
CVE-2024-3094
```

```yaml
# .trivyignore.yaml
vulnerabilities:
  - id: CVE-2026-33634
    paths:
      - "ci/trivy-runner-image"
    statement: "Historical runner image retained only for forensic rebuilds."
    expired_at: "2026-06-30"
```

The example IDs above are real CVEs, but the suppression reasons are deliberately lab examples. In a production repository, never copy an ignore entry from a tutorial into a live policy. Validate the CVE in NVD or the vendor advisory, prove the affected package is present in the scanned artifact, and write a reason that a reviewer can verify. A useful allowlist expires; a dangerous allowlist is permanent, broad, and disconnected from ownership.

VEX is better than a bare ignore when you need machine-readable exploitability context across tools. If a library is present but the vulnerable function is unreachable, a VEX statement can say the product is not affected and explain the justification. That does not remove the CVE from history, and it does not mean every scanner will accept the statement automatically. It gives security, platform, and application teams a structured way to separate "package present" from "risk exploitable here" without losing auditability.

## Comparing Trivy With Grype, Clair, Snyk, Copa, and Aqua Platform

Trivy and Grype are both strong open-source scanners for container images and filesystems, and both can scan SBOMs. Grype is closely paired with Syft for SBOM generation and emphasizes risk prioritization features such as EPSS, KEV, and OpenVEX support. Trivy has a broader all-in-one surface for Kubernetes clusters, Kubernetes manifests, Helm charts, secrets, licenses, SBOMs, and misconfiguration checks from one CLI. For CKS, Trivy is the most exam-friendly tool because a single binary covers the image and Kubernetes scanning paths you need to practice.

Clair is architecturally different. Clair is a service for parsing image contents, indexing manifests, matching vulnerabilities, and notifying when newly discovered vulnerabilities affect indexed images. That fits registry-backed or platform workflows where images are continuously indexed and re-evaluated as advisory data changes. It is less convenient as a single local exam command, but it is useful context because many enterprise registries and image platforms think in Clair-like indexing and notification terms rather than one-off CLI scans.

Snyk Container is a commercial developer-security product that scans container images and provides integrations for repositories, registries, Kubernetes, and fix guidance. It is often attractive when teams already use Snyk for open-source dependency risk and want a hosted workflow around prioritization and remediation. Project Copacetic, usually invoked as `copa`, is not a scanner in the same sense; it patches container images by applying OS package updates based on vulnerability scan results. That makes Copa a remediation companion, not a replacement for scanning, rebuilding, and provenance.

Aqua Security also has a commercial platform around cloud-native security, while Trivy remains the open-source scanner maintained by Aqua. The practical distinction is support and lifecycle coverage. Open-source Trivy is a CLI and library ecosystem for scanning targets and producing results. Aqua's commercial offering adds enterprise platform capabilities such as centralized management, runtime and cloud coverage, policy workflows, reporting, and commercial support. Using Trivy does not require buying Aqua, and buying Aqua does not remove the need to understand what a Trivy result means.

## Did You Know?

- **Trivy's database is not just NVD.** Aqua's `vuln-list` includes NVD, GHSA, GitLab advisories, OS vendor feeds, and language ecosystem data, while `trivy-db` packages that data for scanner use.
- **The March 2026 Trivy ecosystem compromise has its own NVD record.** NVD lists CVE-2026-33634 for malicious code affecting Trivy-related distribution paths, and Aqua's advisory describes compromised releases and force-pushed action tags.
- **`--severity HIGH,CRITICAL` and `--exit-code 1` are verified Trivy v0.70.0 flags.** The image command help also confirms `--input`, `--ignore-unfixed`, `--download-db-only`, `--skip-db-update`, and `--ignorefile`.
- **Helm chart scanning renders templates before checks.** Trivy's Helm coverage documentation says it evaluates Helm variables and functions into Kubernetes manifests, then applies Kubernetes checks to the rendered artifact.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Treating a clean image scan as a security guarantee | CVE scanning sees known package matches, not every runtime path, secret, policy, or supply-chain compromise. | Pair image scanning with manifest scanning, admission policy, runtime controls, rebuild cadence, and digest-based artifact tracking. |
| Scanning `latest` instead of the deployed digest | Tags are convenient and examples often use them. | Build, push, deploy, and record immutable image digests or release tags tied to a specific pipeline run. |
| Blocking every deployment on all High findings | Teams copy a strict gate without an exception or backlog policy. | Fail on fixed Critical or context-specific High findings, track existing backlog separately, and require time-bound approvals for exceptions. |
| Suppressing CVEs without ownership or expiry | `.trivyignore` is easy to edit and hard to review later. | Include the CVE, affected package, justification, approver, expiry date, and follow-up ticket in the allowlist workflow. |
| Running with stale databases forever | Air-gapped or cached CI jobs often set `--skip-db-update` and forget the refresh job. | Use a scheduled `--download-db-only` or mirror process and record database freshness in the scan evidence. |
| Confusing manifest scanning with image scanning | Both commands are in the same tool, so teams assume they answer the same question. | Use `trivy image` for final image layers, `trivy config` for YAML and Helm, and `trivy k8s` for running cluster state. |
| Pinning a GitHub Action tag after a tag-compromise incident | Version tags are easy to read and easy for tooling to update. | Pin security-sensitive third-party actions to full commit SHAs and update them through reviewed dependency-maintenance changes. |

## Quiz

1. **A pipeline runs `trivy image --exit-code 1 --severity CRITICAL my-api:latest` and passes. What two important risks can still remain?**

   <details>
   <summary>Answer</summary>
   The image tag may not be the immutable artifact that will actually deploy, and the scan only gates Critical findings visible to Trivy's current database and scanner configuration. High findings, misconfigured Kubernetes manifests, leaked secrets, unsigned images, runtime exposure, stale databases, and vulnerable dependencies without current CVE matches can still remain. A stronger workflow scans the image digest, records database freshness, scans rendered manifests, and applies policy at admission or deployment time.
   </details>

2. **Why can Trivy, NVD, and an OS vendor disagree about severity for the same CVE?**

   <details>
   <summary>Answer</summary>
   NVD often scores the upstream vulnerability generically, while an OS vendor may account for package build options, backported patches, disabled code paths, or distribution-specific exposure. Trivy can prefer vendor severity sources for OS packages and exposes source selection through `--vuln-severity-source`. The right response is to read the severity source and package family rather than assuming the highest number is always the best operational priority.
   </details>

3. **Your GitHub Actions workflow uses `aquasecurity/trivy-action@v0.36.0`. Why might a security reviewer ask for a full commit SHA instead?**

   <details>
   <summary>Answer</summary>
   A version tag is mutable in Git and can be force-pushed if the maintainer account or release process is compromised. Aqua's March 2026 advisory for the Trivy ecosystem compromise described force-pushed `trivy-action` tags, which makes SHA pinning a practical control for security-sensitive actions. SHA pinning does not eliminate all supply-chain risk, but it makes the reviewed action reference immutable until the repository intentionally updates it.
   </details>

4. **When should you use `trivy config --helm-values values-prod.yaml ./charts/my-api` instead of `trivy image my-api:1.2.3`?**

   <details>
   <summary>Answer</summary>
   Use the Helm command when the question is about rendered Kubernetes configuration, such as whether the chart creates privileged Pods, unsafe host mounts, missing resource limits, or other misconfigurations. Use the image command when the question is about packages, dependencies, secrets, licenses, or image-layer vulnerabilities in the built artifact. A complete release pipeline normally runs both because they inspect different security surfaces.
   </details>

5. **A Trivy result shows a Critical CVE in a package, but the fixed version column is empty. Should the pipeline always fail?**

   <details>
   <summary>Answer</summary>
   Not always. An empty fixed version means the scanner does not know an available package update for that advisory in the detected source, so an immediate rebuild may not remove the finding. The team still needs triage: change base image, remove the package, apply a vendor mitigation, add a time-bound exception, or block if exposure is severe enough. `--ignore-unfixed` can reduce unfixable noise, but it must be paired with a vulnerability-management process for high-impact cases.
   </details>

6. **What is the difference between `.trivyignore` and a VEX statement in a mature vulnerability workflow?**

   <details>
   <summary>Answer</summary>
   A `.trivyignore` entry suppresses a finding ID for the scan context, usually with limited structure unless the team adds review conventions. A VEX statement is machine-readable exploitability information that explains whether a product is affected, not affected, fixed, or under investigation for a vulnerability. VEX is better for cross-tool auditability, while `.trivyignore` remains useful for local, carefully reviewed exceptions.
   </details>

7. **Why does cluster scanning with `trivy k8s` complement CI image scanning instead of replacing it?**

   <details>
   <summary>Answer</summary>
   CI image scanning checks the artifact before deployment, but clusters can drift through manual deploys, old ReplicaSets, init containers, injected sidecars, scheduled Jobs, and images that predate the current gate. `trivy k8s` inspects what is running or configured through Kubernetes, which catches runtime inventory gaps. It should be scoped carefully with namespace and report flags so the scan is useful without overloading cluster operations.
   </details>

8. **A scan finds `CVE-2024-3094` as Medium with fixed versions available, but the same image is approved for an offline batch namespace. What is the correct triage sequence before changing gates?**

   <details>
   <summary>Answer</summary>
   First, classify the finding by verifying whether the vulnerability is actually reachable in the deployed container and whether a patched package is available for that exact image lineage. If it is present but accepted temporarily, document the acceptance with a time-bound exception in an allowlist file (`.trivyignore`/`.trivyignore.yaml`) or VEX statement, and record approver, rationale, and expiry. Then set a rebuild or base-image migration task and align the policy with the namespace risk profile instead of merely disabling the alert.
   </details>

## Hands-On Exercise

This exercise is designed for a disposable workstation and Kubernetes lab cluster. You will scan an image, export evidence, scan manifests and Helm charts, run a namespace-scoped cluster scan, configure a CI-style gate, and practice writing an allowlist entry with enough context for review. The commands use only flags verified against Trivy v0.70.0 help or the official Trivy Action README commit named earlier.

- [ ] Install or download Trivy and verify the version with `trivy --version`.
- [ ] Warm the vulnerability database with `trivy image --download-db-only`.
- [ ] Scan a known public image with `trivy image --severity HIGH,CRITICAL nginx:1.27`.
- [ ] Export a JSON evidence file with `trivy image --format json --output trivy-nginx.json nginx:1.27`.
- [ ] Run a CI-style failure gate with `trivy image --exit-code 1 --ignore-unfixed --severity CRITICAL nginx:1.27`, then record whether the exit code blocks the pipeline.
- [ ] Save a local image archive with `docker save nginx:1.27 -o nginx-1.27.tar` and scan it with `trivy image --input nginx-1.27.tar`.
- [ ] Create or reuse a small Kubernetes manifest directory and scan it with `trivy config ./manifests`.
- [ ] Render-scan a Helm chart with `trivy config --helm-values values.yaml ./charts/example`, adjusting the path to your chart.
- [ ] Run a namespace-scoped cluster scan with `trivy k8s --include-namespaces default --report summary`.
- [ ] Export detailed cluster evidence with `trivy k8s --include-namespaces default --report all --format json --output trivy-k8s-default.json`.
- [ ] Add a temporary `.trivyignore` entry for a real CVE from your scan, including owner, reason, and expiry in an adjacent comment, then rerun the scan to observe the suppression.
- [ ] Remove the temporary ignore entry and write a short policy note stating which severities block, which severities warn, and who may approve an exception.

### Success Criteria

- [ ] You can explain which Trivy database was used and whether the scan updated it or used a cache.
- [ ] You scanned an image by name and an image archive with the verified `--input` flag.
- [ ] You produced at least one JSON or SARIF evidence file suitable for CI artifacts.
- [ ] You scanned Kubernetes YAML or Helm output separately from image packages.
- [ ] You ran a namespace-scoped `trivy k8s` scan and can explain what cluster state it observes.
- [ ] You wrote an exception that includes CVE ID, package context, owner, reason, and expiry.
- [ ] You can explain why SHA-pinned GitHub Actions reduce, but do not eliminate, CI supply-chain risk.

## Sources

- [Trivy vulnerability scanning documentation](https://trivy.dev/docs/latest/guide/scanner/vulnerability/)
- [Trivy database configuration documentation](https://trivy.dev/docs/latest/guide/configuration/db/)
- [Trivy container image target documentation](https://trivy.dev/docs/dev/guide/target/container_image/)
- [Trivy Kubernetes CLI reference](https://trivy.dev/docs/latest/references/configuration/cli/trivy_kubernetes/)
- [Trivy Helm scanning coverage](https://trivy.dev/docs/latest/coverage/iac/helm/)
- [Trivy filtering and suppression documentation](https://trivy.dev/docs/dev/docs/configuration/filtering/)
- [Trivy GitHub Action README at commit 314ff8b43182423b84c50b1670b0e10f858f2d98](https://github.com/aquasecurity/trivy-action/tree/314ff8b43182423b84c50b1670b0e10f858f2d98)
- [Aqua Security trivy-db repository](https://github.com/aquasecurity/trivy-db)
- [Aqua Security vuln-list repository](https://github.com/aquasecurity/vuln-list)
- [Aqua Security advisory: Trivy ecosystem supply chain temporarily compromised](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)
- [NVD CVE-2026-33634](https://nvd.nist.gov/vuln/detail/CVE-2026-33634)
- [NVD CVE-2021-44228](https://nvd.nist.gov/vuln/detail/CVE-2021-44228)
- [NVD CVE-2024-3094](https://nvd.nist.gov/vuln/detail/CVE-2024-3094)
- [FIRST CVSS v3.1 specification](https://www.first.org/cvss/v3.1/specification-document)
- [FIRST CVSS v3.1 calculator](https://www.first.org/cvss/calculator/3.1)
- [Kubernetes Security Checklist](https://kubernetes.io/docs/concepts/security/security-checklist/)
- [Kubernetes SIG Security repository](https://github.com/kubernetes/sig-security)
- [CIS Kubernetes Benchmarks](https://www.cisecurity.org/benchmark/kubernetes)
- [NIST SP 800-190: Application Container Security Guide](https://csrc.nist.gov/pubs/sp/800/190/final)
- [GitLab container scanning documentation](https://docs.gitlab.com/user/application_security/container_scanning/)
- [Trivy GitLab CI integration documentation](https://www.trivy.dev/docs/dev/tutorials/integrations/gitlab-ci/)
- [Anchore Grype repository](https://github.com/anchore/grype)
- [Clair documentation](https://quay.github.io/clair/whatis.html)
- [Snyk Container documentation](https://docs.snyk.io/scan-with-snyk/snyk-container)
- [Project Copacetic documentation](https://project-copacetic.github.io/copacetic/website/)

## Next Module

[Module 5.3: Static Analysis with kubesec and OPA](../module-5.3-static-analysis-with-kubesec-and-opa/) - Scan Kubernetes manifests and enforce supply-chain policy before risky objects reach the API server.
