---
title: "Module 5.2: Image Scanning with Trivy"
slug: k8s/cks/part5-supply-chain-security/module-5.2-image-scanning
sidebar:
  order: 2
lab:
  id: cks-5.2-image-scanning
  url: https://killercoda.com/kubedojo/scenario/cks-5.2-image-scanning
  duration: "45 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical CKS skill
>
> **Time to Complete**: 45 minutes
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

Trivy is best understood as a unified local evidence collector, not only as a container CVE lookup command. The same CLI can inspect image layers, package databases, lock files, application dependencies, Kubernetes YAML, Helm output, secrets, licenses, SBOMs, and live Kubernetes resources. That breadth is useful on the CKS exam because the prompt may say "scan this image" in one task and "find unsafe settings in this manifest" in the next task without changing tools. The danger is treating every Trivy command as the same kind of scan. `trivy image` answers what packages and files exist in the artifact; `trivy config` answers whether declared infrastructure violates policy; `trivy k8s` answers what the cluster currently exposes through the Kubernetes API and workload inventory.

The offline database model is one reason Trivy fits exam and CI workflows. After a database is downloaded, the scanner can run repeatably without querying a remote SaaS service for every finding, which helps when an exam VM has limited network access or a build runner is isolated from the internet. The tradeoff is freshness. A cached database makes scans faster and more deterministic, but it may miss advisories published after the cache was warmed. A network-refreshed run sees newer advisory data, but it can fail because a registry mirror, proxy, or rate limit is unavailable. Good pipelines separate those concerns by warming the database in a scheduled job, scanning with a known cache in short pull-request jobs, and recording the database update time beside the artifact digest.

Trivy also exposes a plugin architecture, which matters operationally even when the exam only requires built-in commands. Plugins are managed through the `trivy plugin` subcommands, and `trivy plugin list` is the quick inventory check for extensions installed in the current environment. A plugin can add output handling or integration behavior, but it is also code that runs in the scanner's trust boundary. In a hardened pipeline, plugin installation should be versioned, reviewed, and cached like any other build dependency, rather than fetched dynamically inside every scan job.

```bash
trivy plugin list
trivy plugin install github.com/aquasecurity/trivy-plugin-referrer
trivy plugin list
```

The upstream data path is intentionally broad. Aqua's `vuln-list` repository tracks NVD, GitHub Advisory Database, GitLab Advisory Database, Debian Security Tracker, Ubuntu CVE Tracker, Alpine secdb, Amazon Linux Security Center, Red Hat OVAL and Security Data, SUSE CVRF, Oracle Linux OVAL, AlmaLinux, Rocky Linux, Arch Linux, Photon OS, and other vendor feeds. Trivy's vulnerability guide also documents language ecosystem sources such as GitHub Advisory Database for Composer, pip, RubyGems, npm, Maven, Go, NuGet, and Pub, plus OS vendor feeds and the Kubernetes official CVE feed for Kubernetes components. A result is therefore a package-to-advisory match, not an independent exploit proof.

The database pipeline is not a simple copy of NVD. A useful scanner result requires an advisory identifier, an affected package or ecosystem, vulnerable version ranges, and enough source context to map that advisory to what Trivy found in the image or filesystem. Aqua's database build process packages upstream records into OCI-distributed database artifacts, and the trivy-db metadata uses a 24-hour update interval as the normal freshness boundary. In practice, a CVE can appear through NVD, an OS vendor advisory, GHSA, a language ecosystem advisory, or Aqua research once there is actionable package mapping. When those sources disagree, Trivy may still show the finding, but the severity source and fixed-version fields become part of the evidence you must read.

Air-gapped environments usually mirror the OCI database artifacts rather than expecting every runner to reach Aqua's public registries. A platform team can copy `trivy-db`, `trivy-java-db`, and `trivy-checks` into an internal registry, then point scans at that mirror with `--db-repository`, `--java-db-repository`, and `--checks-bundle-repository` where needed. The mirror job is the controlled internet-facing component; the cluster or CI runner consumes only the approved internal artifact. That design also gives auditors a stable answer to "which advisory database did this scan use," because the mirror digest and update timestamp can be recorded with the scan report.

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

Cache and parallelism tuning are performance controls, not excuses to hide findings. `--cache-dir` lets a runner persist database and scan cache data between jobs, and a shared cache can remove most of the cost from repeated pull-request scans. `--parallel` controls scanner concurrency, with lower values helping memory-constrained runners and higher values helping larger runners process layers faster. The high-signal CI pattern is to warm the database once, scan several images from the warmed cache, and keep the cache key tied to Trivy version plus database metadata. If a job blindly deletes the cache every run, it spends time downloading the same evidence; if it never refreshes the cache, it gives a polished report with old facts.

Trivy's default image scan also enables secret scanning, which can make first scans slower and can surprise teams expecting only CVE output. For image-only vulnerability checks in a tight CI loop, `--scanners vuln` narrows the work to vulnerabilities; for a broader supply-chain check, keep secret scanning and misconfiguration checks in separate jobs with separate owners. Mixing all security checks into one gate often produces unclear failures, while splitting them keeps the exit code tied to the decision you actually want to automate.

## Reading Severity and CVSS Without Overreacting

CVSS v3.1 is a standardized way to communicate vulnerability characteristics, but it is not a complete deployment decision. FIRST defines the qualitative severity bands as Low from 0.1 to 3.9, Medium from 4.0 to 6.9, High from 7.0 to 8.9, and Critical from 9.0 to 10.0, with a vector string explaining the metrics that produced the score. Trivy reports severities such as `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`, and the v0.70.0 help confirms `--severity HIGH,CRITICAL` as the filter syntax.

The vector string is where CVSS becomes useful for triage. `AV` is attack vector, so `AV:N` means network reachable while `AV:L` means local access is required. `AC` is attack complexity, `PR` is privileges required, `UI` is user interaction, `S` is whether exploitation crosses a security scope boundary, and `C`, `I`, and `A` describe confidentiality, integrity, and availability impact. A verified example from NVD is the Trivy ecosystem compromise record, which includes the CVSS v3.1 vector `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` and a High base score. Read it as network-accessible, low complexity, some privileges required, no user interaction, unchanged scope, and high impact across confidentiality, integrity, and availability. That explains why the event was operationally severe even though the v3.1 score is High rather than Critical.

The nuance is source selection. Trivy can use vendor-specific severities because OS vendors backport fixes and evaluate packages in the context of their distribution. An NVD score may describe the upstream software in a general way, while Debian, Red Hat, Ubuntu, or Alpine may rate the package differently based on compilation options, backports, or affected code paths. Trivy exposes `--vuln-severity-source` when you need a source priority, but the safer default for learners is to read the `SeveritySource` in JSON output and compare it with the package family before overriding the scanner's logic.

CVSS and exploitability diverge because CVSS describes inherent vulnerability characteristics, not whether attackers are using the bug against your deployment today. CISA's Known Exploited Vulnerabilities catalog is a signal that real exploitation has been observed and that affected organizations need urgent treatment. EPSS is a probabilistic signal about exploitation likelihood in the wild. A Critical finding with no reachable code path, no exposed interface, strong sandboxing, and no exploit telemetry may be lower immediate priority than a High finding in CISA KEV that sits in a public build runner. Neither signal replaces engineering judgment, but both help avoid the common mistake of sorting only by the largest number in the scanner table.

A Critical finding can be acceptable for a short, documented window when defense-in-depth blocks the attack chain and no safe patch is available yet. For example, a vulnerable package might exist in an image used only for an offline migration job, the vulnerable daemon is never started, the container runs without network egress, the filesystem is read-only, and the namespace has admission controls that block privilege escalation. That does not make the finding harmless forever. It means the risk decision can be time-bound, tied to a rebuild plan, and reviewed by someone who owns the workload and the compensating controls.

A Medium finding can be unacceptable when it sits on a sensitive data path or supply-chain boundary. A medium-rated parser bug in an image that processes untrusted uploads, a medium secret-handling flaw in a CI helper image, or a medium package issue in an admission controller can carry more operational risk than a Critical bug in a dormant package. This is why mature gates combine severity with fixed-version availability, exploit signals, asset exposure, package reachability, and workload role. The CKS exam often rewards that reasoning because blindly deleting every finding is slower than identifying the few findings that actually block deployment.

Two real CVEs show why IDs must be checked rather than invented. NVD lists CVE-2021-44228 ([Log4Shell, canonical write-up in DevSecOps](/platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/)) <!-- incident-xref: log4shell --> with CVSS v3.1 10.0 Critical. NVD lists CVE-2024-3094 ([xz-utils backdoor, canonical in KCSA supply chain](/k8s/kcsa/part4-threat-model/module-4.4-supply-chain/)) <!-- incident-xref: xz-utils-2024 --> with Red Hat CNA CVSS v3.1 10.0. In 2026, NVD also lists CVE-2026-33634 for the Trivy ecosystem supply-chain compromise, with CVSS v3.1 8.8 High and references to Aqua's vendor advisory. Those examples are useful precisely because the CVE identifiers, affected products, and scores can be verified in NVD instead of copied from a scanner table.

```bash
# Human-readable triage view.
trivy image --severity HIGH,CRITICAL nginx:1.27

# Machine-readable evidence for review or dashboards.
trivy image --format json --output trivy-nginx.json nginx:1.27

# Narrow to fixed high-impact vulnerabilities for a fast rebuild gate.
trivy image --ignore-unfixed --severity HIGH,CRITICAL nginx:1.27
```

Pause and predict: given the vector `AV:N/AC:L/PR:L` on a batch job image with no network egress, the vulnerable package is present but the daemon that uses it never starts, and the namespace blocks privilege escalation — would you block deployment on Critical severity alone, or do you need more evidence first? A strong answer names what still needs verification: confirm the severity from `SeveritySource` and NVD rather than trusting one scanner row, prove the attack chain is unreachable in this workload, and decide whether compensating controls justify a time-bound exception instead of an immediate rebuild.

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

Advanced scanning options should be selected from the workload question you are trying to answer. `--scanners vuln` is the fast CVE gate for a production image. `--scanners vuln,secret` is a reasonable developer check for image layers that may accidentally contain credentials. `--scanners vuln,misconfig,secret,license` is broader and useful for a release candidate, because it asks about vulnerable packages, declared configuration, leaked secrets, and license findings in one run. The scanner name for configuration findings is `misconfig` in current Trivy help, even though the subcommand for scanning manifests is `trivy config`. That distinction matters in scripts because a wrong scanner name turns a policy decision into a failing command instead of a useful report.

`--skip-dirs` and `--skip-files` are sharp tools. They are appropriate when a build context contains generated test fixtures, vendored sample archives, or mounted cache directories that are not part of the deployable artifact. They are dangerous when used to silence noisy directories without proving those files are absent from production. Over-skipping defeats the scan because the scanner can only reason about the files it is allowed to inspect. A reviewer should be able to read every skip pattern and understand whether it removes non-shipped test data, a tool cache, or a real part of the image.

`--ignore-policy` moves exception logic from a flat ignore file into Rego, which is useful when the allowlist decision depends on fields such as finding type, package name, path, or status. Trivy evaluates a Rego package named `trivy` with an `ignore` rule against each finding. A conservative policy ignores only narrow cases that your team can explain, such as a license classification for a file path that is never shipped, or a vulnerability in a package that exists only in a documented builder-only path. The policy should live in the repository, receive code review, and be exported with scan evidence, because it is part of the security decision.

For VEX, use the current Trivy workflow of managing VEX repositories with `trivy vex repo` commands and passing VEX sources with `--vex`, such as `--vex repo` for repository-backed statements. The goal is to carry exploitability information as machine-readable evidence instead of burying it in a ticket comment. A VEX statement can say that a product is not affected, fixed, under investigation, or affected in a specific context. In triage, this is the actively exploitable subset question: which package matches represent real product exposure, and which package matches are present but blocked by reachability, build configuration, or runtime controls.

```bash
# Broad release-candidate scan across vulnerability, config, secret, and license signals.
trivy image --scanners vuln,misconfig,secret,license registry.example.com/team/api:1.2.3

# Skip only known non-shipped fixtures or caches, and document the reason in review.
trivy fs --scanners vuln,secret --skip-dirs test/fixtures/vendor-cache .
trivy image --skip-files usr/share/doc/example/sample-key.pem my-api:dev

# Use reviewed Rego policy and VEX evidence for narrow, auditable suppressions.
trivy image --ignore-policy policy/trivy-ignore.rego my-api:dev
trivy image --vex repo my-api:dev
```

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

`trivy k8s` is not a replacement for per-image CI scans. The cluster command works from Kubernetes API discovery and workload inventory, so it can find images that actually run, objects that violate Kubernetes checks, and drift between declared pipelines and live state. A per-image scan is better for a deterministic build gate because it scans the artifact before deployment and can fail the exact pipeline that produced it. Use both when possible: the pipeline scan prevents known-bad artifacts from entering the registry, and the cluster scan catches stale deployments, manual changes, injected sidecars, and workloads that arrived before the gate existed.

Cluster-wide and namespace-scoped scans have different RBAC implications. A cluster-wide scan needs permission to list many resource types across namespaces and may need access to cluster-scoped resources, so it should be run by a deliberately scoped service account rather than a human admin token copied into CI. A namespace-scoped scan is safer for an application team because it limits discovery to the team's boundary, but it can miss cluster-level policy objects, admission configuration, CRDs, and workloads outside the namespace that still affect the application. For CKS practice, assume the service account permissions are part of the answer: prove what you can list, scan only the requested scope, and avoid requesting cluster-admin when the task only asks for one namespace.

> **Pause and predict**: an exam task gives you a namespace-scoped `Role` that can list Pods and Deployments in `payments` but nothing cluster-scoped. Can that identity run `trivy k8s --include-namespaces payments --report summary` successfully, and what cluster objects might the scan miss even when it succeeds? The useful habit is to map scanner discovery needs to RBAC verbs before you assume the command will see the whole risk picture.

Custom resources and cluster-scoped resources differ from Pods because they may describe controllers, policies, or admission behavior rather than executable containers. A Pod spec exposes image names, security context, volumes, service account, and runtime settings. A CRD instance might represent an Ingress controller rule, a network policy abstraction, a certificate issuer, or a platform-specific deployment object that later creates Pods indirectly. Cluster-scoped resources such as ClusterRoles and CRDs also affect multiple namespaces, so misconfiguration there can create broad exposure even when every Pod in the current namespace looks reasonable. A scanner report should separate vulnerable workload images from unsafe cluster configuration because the remediation owner is often different.

KubeBench, KubeHunter, and KubeAudit answer adjacent questions. KubeBench checks whether cluster components align with the CIS Kubernetes Benchmark, so it is strongest for control-plane and node hardening evidence. KubeHunter is closer to penetration testing and looks for externally observable Kubernetes attack paths, so it is higher risk to run against production without authorization. KubeAudit inspects Kubernetes resources for common workload controls such as running as non-root, read-only root filesystems, capabilities, and privileged settings. Trivy overlaps most directly with KubeAudit for manifest and cluster object checks, overlaps less with KubeBench's benchmark focus, and should not be treated as a stealth penetration-testing tool.

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

In GitHub Actions, the official `aquasecurity/trivy-action` README documents inputs such as `image-ref`, `scan-type`, `scan-ref`, `format`, `exit-code`, `ignore-unfixed`, `vuln-type`, and `severity`. The action's README examples may use a version tag, but the March 2026 Trivy ecosystem compromise is a strong reason to pin security-sensitive third-party actions by full commit SHA and update that SHA deliberately. The SHA below is the `v0.36.0` tag target observed with `git ls-remote` during this module update, not a mutable `v0.36.0` string. A real organization should refresh that SHA through dependency maintenance and review release notes before changing the workflow.

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
      packages: write
      id-token: write
    strategy:
      fail-fast: false
      matrix:
        include:
          - image: my-api
            context: services/api
            dockerfile: services/api/Dockerfile
          - image: my-worker
            context: services/worker
            dockerfile: services/worker/Dockerfile
    steps:
      - name: Checkout
        uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd  # v5.0.1

      - name: Build image
        run: |
          IMAGE="ghcr.io/${{ github.repository }}/${{ matrix.image }}:${{ github.sha }}"
          docker build \
            --file "${{ matrix.dockerfile }}" \
            --tag "$IMAGE" \
            "${{ matrix.context }}"

      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25  # v0.36.0
        with:
          image-ref: ghcr.io/${{ github.repository }}/${{ matrix.image }}:${{ github.sha }}
          format: sarif
          output: trivy-${{ matrix.image }}.sarif
          exit-code: "1"
          ignore-unfixed: true
          vuln-type: os,library
          severity: CRITICAL,HIGH

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@458d36d7d4f47d0dd16ca424c1d3cda0060f1360  # v3
        with:
          sarif_file: trivy-${{ matrix.image }}.sarif

      - name: Log in to GitHub Container Registry
        if: github.event_name == 'push'
        run: echo "${{ github.token }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin

      - name: Push scanned image
        if: github.event_name == 'push'
        run: docker push "ghcr.io/${{ github.repository }}/${{ matrix.image }}:${{ github.sha }}"

      - name: Install cosign
        if: github.event_name == 'push'
        uses: sigstore/cosign-installer@d58896d6a1865668819e1d91763c7751a165e159  # v3.9.2

      - name: Sign pushed digest
        if: github.event_name == 'push'
        env:
          COSIGN_YES: "true"
        run: |
          IMAGE="ghcr.io/${{ github.repository }}/${{ matrix.image }}:${{ github.sha }}"
          DIGEST="$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE")"
          cosign sign "$DIGEST"
```

That workflow is intentionally strict but not magical. `exit-code: "1"` means the action fails when findings match the selected scanners, severities, and other filters; it does not mean every possible risk has been eliminated. `--exit-code 1 --severity HIGH,CRITICAL` in the CLI has the same policy meaning: the command returns the chosen nonzero exit code only when High or Critical findings remain after filtering. `ignore-unfixed: true` maps to Trivy's unfixed-vulnerability filtering and reduces noise from findings where the source data has no fixed package version, but it can also hide urgent issues where the correct action is to change base image, remove a package, or apply a vendor mitigation. Use it to avoid blocking every build on unpatchable backlog, not to avoid triage.

The scan, sign, and push order deserves precision. The security intent is "scan before publishing a trusted artifact," but cosign signatures are normally attached to registry references and digests. The practical workflow is build a local tag, scan that tag, push only after the scan gate passes, resolve the pushed digest, then sign the digest. Admission policy can later require a valid signature on the digest while vulnerability policy records the SARIF or JSON evidence that justified the push. If the workflow signs before the scanner gate or pushes before the scan result is known, downstream systems can observe an artifact that the pipeline later rejects.

Pause and predict: if you reorder the GitHub Actions steps to push before the Trivy scan, sign immediately after push, and only then fail the job on Critical findings, what can a registry consumer observe during the minutes between push and failure? The answer should mention a vulnerable or unreviewed digest already published, a signature that attests to the wrong moment in the pipeline, and admission systems that may pull the artifact before the gate completes.

SARIF upload turns a one-time CI log into an audit trail in GitHub's Security tab. The useful triage flow is to upload SARIF on every run, fail the job only on the policy threshold, assign ownership for new findings, and close findings by rebuilding or documenting a time-bound exception. Retention matters because scan results describe a moment in time: image digest, Trivy version, database metadata, workflow SHA, and the exact gate settings. A future reviewer should be able to answer whether a deployment was accepted because there were no matching findings, because the finding was unfixed and filtered, or because an explicit allowlist policy suppressed it.

GitLab has two common patterns. GitLab's own container scanning documentation says the container scanning analyzer uses Trivy and passes Trivy environment variables through, while the Trivy documentation also shows a direct GitLab CI job using the `aquasec/trivy` image. The built-in template is easier for GitLab Security Dashboard integration; the direct job is easier for open-source repositories or custom reports. In both cases, keep the job tied to the image digest or tag produced by the same pipeline stage.

```yaml
stages:
  - build
  - scan
  - publish

variables:
  IMAGE_REF: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA"

build_image:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  script:
    - docker build -t "$IMAGE_REF" .
    - docker save "$IMAGE_REF" -o image.tar
  artifacts:
    paths:
      - image.tar

trivy_image_scan:
  stage: scan
  image:
    name: docker.io/aquasec/trivy:0.70.0
    entrypoint: [""]
  services:
    - docker:27-dind
  variables:
    TRIVY_CACHE_DIR: "$CI_PROJECT_DIR/.trivy-cache"
  cache:
    key: "trivy-0.70.0"
    paths:
      - .trivy-cache/
  script:
    - docker load -i image.tar
    - trivy image --download-db-only
    - trivy image --format json --output "trivy-${CI_COMMIT_SHA}.json" "$IMAGE_REF"
    - trivy image --exit-code 1 --ignore-unfixed --severity HIGH,CRITICAL "$IMAGE_REF"
  artifacts:
    when: always
    expire_in: 30 days
    paths:
      - "trivy-${CI_COMMIT_SHA}.json"
      - image.tar

push_image:
  stage: publish
  image: docker:27
  services:
    - docker:27-dind
  needs:
    - job: trivy_image_scan
      artifacts: true
  script:
    - docker load -i image.tar
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    - docker push "$IMAGE_REF"
```

Design gates around failure domains. A global Critical gate can stop every service in an organization when a widely used base image receives a new advisory, so mature teams separate "newly introduced by this change" from "pre-existing backlog," and they maintain an emergency path for false positives or unavailable fixes. The emergency path should be auditable: who approved the exception, which CVE or advisory ID it covers, when it expires, and what compensating control or rebuild plan exists. A scanner gate without an exception process will be bypassed when it blocks real delivery, while a scanner gate with no exit-code policy produces attractive reports that nobody has to obey.

Matrix scanning is the CI pattern that prevents shared repositories from hiding risk behind one happy-path image. A monorepo may build an API image, a background worker image, a migration image, and a debugging image from different Dockerfiles. If the matrix scans only the API, the release can still push a vulnerable worker image that handles queue payloads or a migration image with broad database privileges. Give every matrix entry a clear image name, context, Dockerfile, scan output file, and owner. When one entry fails, the team should know whether to rebuild a base image, update an application dependency, or remove a package from a production stage.

## Handling False Positives and Accepted Risk

False positive handling starts by naming the evidence, not by hiding the finding. A Trivy vulnerability row usually contains the vulnerability ID, package name, installed version, fixed version, severity, primary URL, and source information. Before suppressing it, ask whether the package is from the detected OS vendor, whether the fixed version exists in the image's package repository, whether the vulnerable code is reachable, and whether the image actually runs in the environment being reviewed. Vendor severity and package backports are common reasons for apparent mismatch between scanners.

Trivy supports several suppression mechanisms. The classic `.trivyignore` file suppresses finding IDs for a scan directory, and `--ignorefile` selects a non-default ignore file. The newer `.trivyignore.yaml` format can carry structured ignore entries and expiration metadata, but Trivy's filtering documentation marks explicit `--ignorefile ./.trivyignore.yaml` use as necessary while the feature is still experimental. For advanced cases, `--ignore-policy` evaluates a Rego policy against each finding, and VEX can state that a vulnerability is not exploitable in a particular product context.

```text
# .trivyignore
# Accept until 2026-06-30: package present in debug-only image, not deployed.
CVE-2023-48795
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

The example IDs above are real CVEs, but the suppression reasons are deliberately lab examples. In a production repository, never copy an ignore entry from a tutorial into a live policy. Validate the CVE in NVD or the vendor advisory, prove the affected package is present in the scanned artifact, and write a reason that a reviewer can verify. A useful allowlist expires; a dangerous allowlist is permanent, broad, and disconnected from ownership. Critical supply-chain findings such as CVE-2024-3094 (the xz-utils backdoor, NVD CVSS v3.1 10.0 Critical) should not appear in a routine ignore file without executive incident-response ownership, because suppressing a confirmed backdoor is a fundamentally different decision than accepting a medium-rated protocol weakness in a non-production debug image.

VEX is better than a bare ignore when you need machine-readable exploitability context across tools. If a library is present but the vulnerable function is unreachable, a VEX statement can say the product is not affected and explain the justification. That does not remove the CVE from history, and it does not mean every scanner will accept the statement automatically. It gives security, platform, and application teams a structured way to separate "package present" from "risk exploitable here" without losing auditability.

## Comparing Trivy With Grype, Clair, Snyk, Copa, and Aqua Platform

Trivy and Grype are both strong open-source scanners for container images and filesystems, and both can scan SBOMs. Grype is closely paired with Syft for SBOM generation and emphasizes risk prioritization features such as EPSS, KEV, and OpenVEX support. Trivy has a broader all-in-one surface for Kubernetes clusters, Kubernetes manifests, Helm charts, secrets, licenses, SBOMs, and misconfiguration checks from one CLI. For CKS, Trivy is the most exam-friendly tool because a single binary covers the image and Kubernetes scanning paths you need to practice.

Tool comparison should stay qualitative unless you have a reproducible benchmark for your own images. Speed depends on image size, package ecosystem, language dependency layout, network access to databases, cache warmth, and output format. False positives depend on source mapping, vendor backports, package detection, and whether the scanner optimizes for precise or comprehensive detection. The table below is a practical selection guide, not a universal measurement. In an exam, the choice is already Trivy; in production, the useful comparison is whether the tool integrates with your registry, SBOM process, exception workflow, and security ownership model.

| Tool | Speed | DB freshness | False-positive behavior | SBOM output formats |
|---|---|---|---|---|
| Trivy | Fast with warmed DB and cache; broad scanners add time. | OCI-distributed DBs with daily metadata interval and broad vendor feeds. | Defaults toward precise package matching, with vendor severity and Rego/VEX suppression options. | JSON, CycloneDX, SPDX, SPDX JSON, and table-oriented reports. |
| Grype | Fast for image and SBOM scans, especially paired with Syft-generated SBOMs. | Anchore vulnerability feed plus ecosystem data, with strong SBOM-first workflows. | Strong risk-prioritization features such as EPSS, KEV, and VEX context; results still depend on package evidence. | JSON, CycloneDX, SPDX-derived SBOM workflows through Syft pairing. |
| Snyk Container | Depends on hosted integration and registry workflow; strong developer UX. | Vendor-managed service freshness and commercial prioritization data. | Commercial fix guidance and policy context reduce triage burden, but findings still need workload context. | SBOM support depends on product plan and integration path. |
| Clair | Built for registry-style indexing and notification rather than ad hoc local scans. | Feed freshness is tied to the deployed Clair updater and indexer. | Good for continuous re-evaluation of indexed images; less convenient for single-command CKS tasks. | Primarily API/report integration around indexed manifests rather than a local SBOM authoring workflow. |

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
| Running scans without a failing exit code | The report looks serious in CI logs, but the job always succeeds. | Add `--exit-code 1` or the action `exit-code: "1"` to the policy gate, then publish JSON or SARIF for triage. |

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

8. **A scan finds `CVE-2024-3094` (NVD CVSS v3.1 10.0 Critical, the xz-utils backdoor) in an image approved for an offline batch namespace with no egress. What is the correct triage sequence before changing gates?**

   <details>
   <summary>Answer</summary>
   First, verify severity from authoritative sources — read `SeveritySource` in JSON output and confirm the NVD record — before treating the finding as anything less than Critical. Then classify reachability: is the affected package actually executed in the container, and do compensating controls (no egress, read-only root filesystem, non-root execution, admission policy) break the attack chain? A Critical backdoor in an offline batch namespace still needs far stronger justification than a Medium finding: executive incident-response ownership, a documented rebuild or base-image migration plan with a short expiry, and explicit compensating-control evidence. Only after that review should you consider a time-bound exception in `.trivyignore.yaml` or VEX, never a silent flat-file suppression. Align the gate with namespace risk, but do not downgrade Critical supply-chain findings without verified severity and ownership.
   </details>

## Hands-On Exercise

This exercise is designed for a disposable workstation and Kubernetes lab cluster. You will scan an image, export evidence, scan manifests and Helm charts, run a namespace-scoped cluster scan, configure a CI-style gate, and practice writing an allowlist entry with enough context for review. The commands use only flags verified against Trivy v0.70.0 help or the official Trivy Action README commit named earlier.

In a first exam-style image scenario, the prompt gives you an image reference and asks for High and Critical vulnerabilities in JSON. Start by resolving the exact image name or digest in the prompt, run `trivy image --format json --output findings.json --severity HIGH,CRITICAL IMAGE`, and inspect the package name, installed version, fixed version, and severity source before editing anything. If the image is built from a Debian or Ubuntu base and the task explicitly asks for package remediation, patch the Dockerfile with `apt-get update && apt-get upgrade -y` in the appropriate production stage, clean package lists, rebuild the image, and rescan the rebuilt artifact. In production, a base image bump is often cleaner than a broad upgrade line, but the exam may reward showing the rebuild loop: scan, identify fixed packages, update the Dockerfile, rebuild, and prove the finding set changed.

In a second exam-style manifest scenario, the prompt gives you a Kubernetes YAML file and asks for misconfiguration findings plus a patched version. Run `trivy config manifest.yaml` or scan the containing directory if multiple files share labels and service accounts. Then patch the security-relevant fields directly: set `runAsNonRoot`, avoid privileged containers, drop unnecessary Linux capabilities, set `allowPrivilegeEscalation: false`, add a seccomp profile, remove unsafe host paths, and ensure the service account matches the workload's permissions. The key is to preserve application intent while reducing the misconfiguration. A good answer includes both the scanner output and a patched manifest that a reviewer can apply without guessing which control changed.

In a third pipeline scenario, the prompt asks you to fail a Jenkins, GitHub Actions, or GitLab CI build on Critical findings. The minimum acceptable gate is not "run Trivy and print a table"; it is a command whose exit code changes the job result when matching findings remain. For a shell-based Jenkins stage, that can be `trivy image --exit-code 1 --ignore-unfixed --severity CRITICAL "$IMAGE_REF"` followed by archiving the JSON output. For GitHub Actions or GitLab CI, use the same semantics through action inputs or direct CLI commands, then store SARIF or JSON as an artifact. The scanner gate should sit after the image is built and before the image is treated as releasable.

When a scan returns more than one hundred CVEs and the timer is running, use a three-pass strategy. First, identify the artifact and evidence: image digest, database freshness, output format, and scanner filters. Second, prioritize only findings that match the requested threshold, have fixed versions, affect packages in the production stage, or carry exploit signals such as KEV. Third, remediate the few findings that can change the result quickly, usually by bumping the base image, upgrading packages in the final stage, or removing unnecessary packages. Do not spend twenty minutes reading every Low and Medium row when the task asks for High and Critical output, and do not ignore a Medium that sits on a supply-chain or data-path boundary merely because the table sorts it below larger numbers.

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

## Learner check

> Image scanning with Trivy is not a single command memorization exercise. The CKS skill is knowing which artifact to scan, which database and severity source produced the evidence, which findings should fail a pipeline, and which risks scanning cannot see without manifest checks, cluster inventory, and digest-based deployment discipline.

---

## Sources

- [Trivy vulnerability scanning documentation](https://trivy.dev/docs/latest/guide/scanner/vulnerability/)
- [Trivy database configuration documentation](https://trivy.dev/docs/latest/guide/configuration/db/)
- [Trivy container image target documentation](https://trivy.dev/docs/dev/guide/target/container_image/)
- [Trivy image CLI reference](https://trivy.dev/docs/latest/references/configuration/cli/trivy_image/)
- [Trivy Kubernetes CLI reference](https://trivy.dev/docs/latest/references/configuration/cli/trivy_kubernetes/)
- [Trivy Helm scanning coverage](https://trivy.dev/docs/latest/coverage/iac/helm/)
- [Trivy filtering and suppression documentation](https://trivy.dev/docs/dev/docs/configuration/filtering/)
- [Trivy VEX documentation](https://trivy.dev/docs/latest/supply-chain/vex/)
- [Trivy plugin list CLI reference](https://trivy.dev/latest/docs/references/configuration/cli/trivy_plugin_list/)
- [Trivy GitHub Action README at commit ed142fd0673e97e23eac54620cfb913e5ce36c25](https://github.com/aquasecurity/trivy-action/tree/ed142fd0673e97e23eac54620cfb913e5ce36c25)
- [Aqua Security trivy-db repository](https://github.com/aquasecurity/trivy-db)
- [Aqua Security vuln-list repository](https://github.com/aquasecurity/vuln-list)
- [Aqua Security advisory: Trivy ecosystem supply chain temporarily compromised](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)
- [NVD CVE-2026-33634](https://nvd.nist.gov/vuln/detail/CVE-2026-33634)
- [NVD CVE-2021-44228](https://nvd.nist.gov/vuln/detail/CVE-2021-44228)
- [NVD CVE-2024-3094](https://nvd.nist.gov/vuln/detail/CVE-2024-3094)
- [FIRST CVSS v3.1 specification](https://www.first.org/cvss/v3.1/specification-document)
- [FIRST CVSS v3.1 calculator](https://www.first.org/cvss/calculator/3.1)
- [FIRST EPSS](https://www.first.org/epss/)
- [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [Kubernetes Security Checklist](https://kubernetes.io/docs/concepts/security/security-checklist/)
- [Kubernetes SIG Security repository](https://github.com/kubernetes/sig-security)
- [CIS Kubernetes Benchmarks](https://www.cisecurity.org/benchmark/kubernetes)
- [Aqua Security kube-bench repository](https://github.com/aquasecurity/kube-bench)
- [Aqua Security kube-hunter repository](https://github.com/aquasecurity/kube-hunter)
- [Shopify kubeaudit repository](https://github.com/Shopify/kubeaudit)
- [NIST SP 800-190: Application Container Security Guide](https://csrc.nist.gov/pubs/sp/800/190/final)
- [GitLab container scanning documentation](https://docs.gitlab.com/user/application_security/container_scanning/)
- [Trivy GitLab CI integration documentation](https://www.trivy.dev/docs/dev/tutorials/integrations/gitlab-ci/)
- [Anchore Grype repository](https://github.com/anchore/grype)
- [Clair documentation](https://quay.github.io/clair/whatis.html)
- [Snyk Container documentation](https://docs.snyk.io/scan-with-snyk/snyk-container)
- [Project Copacetic documentation](https://project-copacetic.github.io/copacetic/website/)

## Next Module

[Module 5.3: Static Analysis with kubesec and OPA](./module-5.3-static-analysis/) - Scan Kubernetes manifests and enforce supply-chain policy before risky objects reach the API server.
