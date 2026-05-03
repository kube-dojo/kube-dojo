---
revision_pending: false
title: "Module 5.4: Security Tooling"
slug: k8s/kcsa/part5-platform-security/module-5.4-security-tooling
sidebar:
  order: 5
---

# Module 5.4: Security Tooling

> **Complexity**: `[MEDIUM]` - Tool awareness, operational comparison, and practical stack design
>
> **Time to Complete**: 55-65 minutes
>
> **Prerequisites**: [Module 5.3: Runtime Security](../module-5.3-runtime-security/)

## Learning Outcomes

After completing this module, you will be able to perform the following security tooling decisions in a realistic platform review:

1. **Evaluate** security tool coverage across build, deploy, runtime, audit, secrets, and service-to-service phases.
2. **Compare** Trivy, Grype, Cosign, kube-bench, Kyverno, Gatekeeper, Falco, Tetragon, Vault, Sealed Secrets, and Istio for Kubernetes 1.35+ environments.
3. **Design** an adoption plan that moves policy and runtime tooling from audit signals to enforceable controls.
4. **Diagnose** coverage gaps by matching scanner, policy, runtime detector, secrets, and service mesh findings to operational risks.
5. **Implement** a minimum viable Kubernetes security tooling stack with the `k` alias and repeatable validation steps.

## Why This Module Matters

In late 2021, a widely used Java logging library vulnerability forced operations teams into an uncomfortable race. A platform team at a large online retailer discovered that it could inventory container images quickly, but it could not prove which workloads were already running vulnerable packages, which namespaces would block emergency patches, or which suspicious runtime activity deserved immediate response. The team had expensive tools, several dashboards, and plenty of alerts, yet the incident bridge still spent hours arguing over ownership because each tool described only one slice of the risk.

That kind of failure is not caused by one missing scanner. It is caused by an unplanned security tooling stack where build-time checks, admission policy, runtime detection, cluster hardening, secret handling, and service identity do not form a chain. Kubernetes makes this problem sharper because the attack surface spans images, manifests, admission controllers, kubelet behavior, cloud identity, network paths, and the kernel boundary beneath containers. A finding from one layer is useful only when the team knows which other layer should prevent, confirm, or compensate for it.

This module teaches the security tools named most often in Kubernetes security practice and KCSA preparation, but the goal is not memorizing logos. You will learn how to evaluate tool categories, compare overlapping tools honestly, design a small stack that fits a team, and diagnose gaps before an incident exposes them. The examples assume Kubernetes 1.35+ behavior and use `alias k=kubectl`; when you see an inline command such as `k get pods -A`, read it as the standard kubectl client through that short alias.

## Security Tool Categories

The first mistake many teams make is treating Kubernetes security tooling as a shopping list. They hear that Trivy is popular, that Kyverno feels approachable, that Falco catches runtime behavior, and that kube-bench maps to CIS, so they install all of them and call the cluster protected. That creates activity, but not necessarily control. A useful stack starts by asking where a mistake enters the system, when the platform has a chance to stop it, and what signal proves the stop actually worked.

The lifecycle view below is the preserved map from the original module. Read it from top to bottom as a set of defensive opportunities rather than a catalog. Image security tools act before or during delivery, cluster hardening tools inspect the platform, policy tools make admission decisions, runtime tools watch behavior after admission, secrets tools reduce credential exposure, and service mesh tools strengthen identity and authorization between workloads. The same incident usually crosses more than one category.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES SECURITY TOOLS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IMAGE SECURITY                                            │
│  ├── Scanning: Trivy, Grype, Clair                        │
│  ├── Signing: Cosign, Notary                              │
│  └── SBOM: Syft, Trivy                                    │
│                                                             │
│  CLUSTER HARDENING                                         │
│  ├── Benchmarks: kube-bench                               │
│  ├── Auditing: kubeaudit, Polaris                         │
│  └── Penetration: kube-hunter                             │
│                                                             │
│  POLICY ENFORCEMENT                                        │
│  ├── Admission: OPA/Gatekeeper, Kyverno                   │
│  ├── Network: CNI policies, Cilium                        │
│  └── Runtime: Seccomp, AppArmor                           │
│                                                             │
│  RUNTIME SECURITY                                          │
│  ├── Detection: Falco, Tetragon                           │
│  ├── Sandboxing: gVisor, Kata                             │
│  └── Platforms: Aqua, Sysdig, Prisma                      │
│                                                             │
│  SECRETS MANAGEMENT                                        │
│  ├── External: Vault, AWS Secrets Manager                 │
│  └── Encryption: SealedSecrets, SOPS                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A practical tool stack also needs a feedback loop. If Trivy blocks a critical image in CI, the developer needs a path to rebuild or accept a time-boxed risk. If Kyverno audits a privileged container, the owning team needs a policy exception process and a remediation date. If Falco reports a shell inside a production container, the incident responder needs context from Kubernetes labels, runtime metadata, and deployment history. Tools that produce findings without a workflow become another queue that engineers learn to ignore.

Pause and predict: what do you think happens if a team buys a commercial platform that includes scanning, policy, runtime detection, and compliance, but nobody maps those capabilities to the existing release process? The likely outcome is a polished dashboard with unclear accountability. The platform may have excellent detection, but if it is not wired into CI, admission, incident response, and backlog triage, the organization still has weak controls.

Open-source stacks have the opposite failure mode. They often integrate deeply with Kubernetes and can be tuned precisely, but they require the team to own upgrades, alert routing, dashboards, exception handling, and cross-tool correlation. Commercial platforms can reduce operational burden and provide unified reporting, but they may hide implementation details or force workflows that do not match the team. The best answer is rarely "buy" or "build"; it is matching operational capacity to the security lifecycle.

The KCSA-level mental model is straightforward: scanning finds known risk before or around deployment, signing proves artifact identity, admission policy blocks unacceptable manifests, benchmark tools check cluster configuration, runtime tools detect behavior that controls missed, and secret tools limit blast radius when an application needs credentials. When you evaluate security tool coverage, draw the lifecycle first and mark which category has a preventive control, which has a detective control, and which has an owner.

## Image Security: Scanning, SBOMs, and Signing

Image security tools address the earliest Kubernetes security question: should this artifact be allowed anywhere near a cluster? A container image packages an operating system layer, language dependencies, application binaries, startup commands, and metadata. That bundle can contain known vulnerabilities, outdated packages, leaked files, weak configuration, or an unknown provenance. Scanners and signers do not make code secure by themselves, but they create a repeatable decision point before the cluster has to run the workload.

Trivy is often the first tool teams adopt because it covers several related checks with one CLI. It can scan images, repositories, filesystems, Kubernetes manifests, infrastructure-as-code, and SBOMs, which makes it useful in local development, CI pipelines, and cluster review. The tradeoff is that one broad tool can tempt teams to treat all findings the same. A critical remote-code-execution vulnerability in a reachable service deserves a different response than a medium package issue in an unused debug layer.

```text
┌─────────────────────────────────────────────────────────────┐
│              TRIVY                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Comprehensive security scanner                       │
│  BY: Aqua Security (open source)                           │
│                                                             │
│  SCANS:                                                    │
│  ├── Container images (OS + language packages)            │
│  ├── Filesystems and repositories                         │
│  ├── Kubernetes manifests (misconfigurations)             │
│  ├── IaC (Terraform, CloudFormation)                      │
│  └── SBOM generation                                       │
│                                                             │
│  KEY FEATURES:                                             │
│  ├── Fast (local DB, no network for scanning)             │
│  ├── Comprehensive (multiple scanners in one)             │
│  ├── CI/CD integration (exit codes for failures)          │
│  └── Multiple output formats (JSON, SARIF, etc.)          │
│                                                             │
│  COMMANDS:                                                 │
│  trivy image nginx:1.25                                   │
│  trivy fs .                                               │
│  trivy k8s --report summary                               │
│  trivy config Dockerfile                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Grype occupies a narrower but very useful lane. It is a vulnerability scanner for images, filesystems, archives, and SBOMs, and it pairs naturally with Syft when a team wants a clear separation between generating a software bill of materials and analyzing that bill of materials for vulnerabilities. That separation matters in regulated environments because the SBOM can be stored, signed, shared with customers, and rescanned later when vulnerability databases change. The image might not change, but the risk interpretation can.

```text
┌─────────────────────────────────────────────────────────────┐
│              GRYPE                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Vulnerability scanner for containers                 │
│  BY: Anchore (open source)                                 │
│                                                             │
│  SCANS:                                                    │
│  ├── Container images                                      │
│  ├── Filesystems                                           │
│  ├── SBOMs (from Syft)                                    │
│  └── Archives (tar, zip)                                   │
│                                                             │
│  KEY FEATURES:                                             │
│  ├── Fast scanning                                        │
│  ├── Works with Syft SBOMs                                │
│  ├── Multiple DB sources                                  │
│  └── CI/CD friendly                                       │
│                                                             │
│  PAIRS WITH SYFT:                                          │
│  Syft generates SBOM → Grype scans SBOM for CVEs          │
│                                                             │
│  COMMANDS:                                                 │
│  grype nginx:1.25                                         │
│  grype sbom:./sbom.json                                   │
│  grype dir:/path/to/project                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The scanner decision is not only about finding more CVEs. It is about where the finding appears and who can act on it. A local developer scan gives fast feedback but is easy to bypass. A CI gate is consistent but can block urgent releases if severity rules are too blunt. A registry or cluster scan can discover drift, but it may find vulnerable images after they are already running. Mature teams combine these layers and define which severities fail builds, which create tickets, and which require emergency action.

Cosign answers a different question: is this the artifact we intended to run, and can we verify who signed it? Signing is easy to misunderstand because it does not prove an image is vulnerability-free. It proves identity and integrity. A signed vulnerable image is still vulnerable, but an unsigned or incorrectly signed image should not be trusted simply because it has a familiar name. This distinction becomes critical when attackers compromise a pipeline, a registry credential, or a dependency publishing path.

```text
┌─────────────────────────────────────────────────────────────┐
│              COSIGN                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Container image signing and verification             │
│  BY: Sigstore project (Linux Foundation)                   │
│                                                             │
│  FEATURES:                                                 │
│  ├── Sign container images                                │
│  ├── Store signatures in OCI registries                   │
│  ├── Keyless signing (OIDC identity)                      │
│  ├── Transparency log (Rekor)                             │
│  └── Attestation support                                  │
│                                                             │
│  WORKFLOW:                                                 │
│  # Generate key pair                                       │
│  cosign generate-key-pair                                 │
│                                                             │
│  # Sign image                                              │
│  cosign sign --key cosign.key myregistry/myimage:v1       │
│                                                             │
│  # Verify signature                                        │
│  cosign verify --key cosign.pub myregistry/myimage:v1     │
│                                                             │
│  # Keyless signing (uses OIDC)                            │
│  cosign sign myregistry/myimage:v1                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

In a Kubernetes 1.35+ platform, image scanning and image signing usually meet at admission. The pipeline scans and signs, the registry stores artifacts and signatures, and an admission policy verifies that images come from allowed registries, include expected attestations, and meet vulnerability rules. This is where scanner output becomes a control rather than a report. Without admission enforcement, a developer with deploy permissions can often reference an older image tag, a side registry, or an emergency build that skipped the gate.

Before running this in a real pipeline, what output would you expect if the scanner finds one critical package in a transitive dependency but the image is signed correctly? The right answer is two separate signals. The signing check should pass because identity and integrity are intact, while the vulnerability policy may fail or require an exception. Keeping those signals separate helps teams avoid the false comfort of a signature and the false panic of a scanner finding without exploitability context.

The operational pattern is to start with visibility, then tune, then enforce. Run scanners in report mode first, measure how often builds would fail, and identify noisy packages that have no fixed version. Add exception files with owners and expiry dates instead of global allowlists. Then enforce on the risks the organization is ready to remediate quickly. Security tooling earns trust when it blocks the right release for the right reason and gives engineers enough information to fix it.

## Cluster Security Assessment and Configuration Auditing

Cluster assessment tools answer the platform question: is the Kubernetes environment itself configured in a way that supports secure workloads? A perfect application image still runs on nodes, kubelets, API servers, admission chains, and storage paths. If the API server allows anonymous access, the kubelet exposes sensitive endpoints, etcd is weakly protected, or node permissions are loose, workload-level tooling cannot compensate fully. Benchmark and auditing tools make these platform risks visible in repeatable language.

kube-bench maps cluster and node configuration to the CIS Kubernetes Benchmark. That means it is especially useful when a team needs a recognizable control framework, audit evidence, or a baseline against managed-cluster defaults. It is also a reminder that managed Kubernetes does not eliminate responsibility. Cloud providers may operate the control plane, but teams still configure node pools, RBAC, network exposure, admission plugins, workload policy, logging, and upgrades.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBE-BENCH                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: CIS Kubernetes Benchmark checker                     │
│  BY: Aqua Security (open source)                           │
│                                                             │
│  CHECKS:                                                   │
│  ├── Control plane component configuration                │
│  ├── etcd configuration                                   │
│  ├── Control plane configuration files                    │
│  ├── Worker node configuration                            │
│  └── Kubernetes policies                                  │
│                                                             │
│  OUTPUT:                                                   │
│  [PASS] 1.1.1 Ensure API server pod spec file perms        │
│  [FAIL] 1.1.2 Ensure API server pod spec ownership         │
│  [WARN] 1.2.1 Ensure anonymous-auth is disabled           │
│                                                             │
│  RUN AS:                                                   │
│  # On master node                                          │
│  kube-bench run --targets master                          │
│                                                             │
│  # On worker node                                          │
│  kube-bench run --targets node                            │
│                                                             │
│  # As Job in cluster                                       │
│  kubectl apply -f job.yaml                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The important nuance is that kube-bench findings are not all equally actionable in every cluster. A self-managed cluster gives the platform team direct access to control plane flags and host files. A managed service may hide those components or implement equivalent controls differently. The finding still matters, but the remediation path may be a provider setting, an upgrade, a support ticket, or a compensating control. Treat benchmark results as a structured conversation with the platform owner, not as a blind pass-fail score.

kubeaudit focuses more on workload manifests and running resources. It looks for practical workload risks such as privileged containers, root users, added capabilities, missing resource limits, host namespace usage, and service account token exposure. This makes it complementary to kube-bench. If kube-bench is inspecting the building's locks and fire doors, kubeaudit is walking through each office to see whether people propped doors open, stored keys on desks, or ran machinery without guards.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBEAUDIT                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Kubernetes security auditing tool                    │
│  BY: Shopify (open source)                                 │
│                                                             │
│  AUDITS FOR:                                               │
│  ├── Privileged containers                                │
│  ├── Running as root                                      │
│  ├── Capabilities                                         │
│  ├── Host namespace usage                                 │
│  ├── Read-only filesystem                                 │
│  ├── Service account tokens                               │
│  ├── Network policies                                     │
│  └── Resource limits                                      │
│                                                             │
│  MODES:                                                    │
│  ├── Cluster mode - audit running cluster                 │
│  ├── Manifest mode - audit YAML files                     │
│  └── Local mode - audit current context                   │
│                                                             │
│  COMMANDS:                                                 │
│  kubeaudit all                     # All audits           │
│  kubeaudit privileged              # Check for privileged │
│  kubeaudit rootfs                  # Check read-only FS   │
│  kubeaudit -f deployment.yaml      # Audit manifest       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Polaris overlaps with workload auditing, but it presents findings as best-practice validation across security, reliability, and efficiency. That broader view is valuable because security findings rarely travel alone. A workload without resource requests may also be missing probes, running as root, or mounting a writable root filesystem. A dashboard that shows several quality dimensions can help application teams prioritize changes that improve resilience and security together instead of treating them as unrelated chores.

```text
┌─────────────────────────────────────────────────────────────┐
│              POLARIS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Best practices validation                            │
│  BY: Fairwinds (open source)                               │
│                                                             │
│  VALIDATES:                                                │
│  ├── Security (privileged, root, capabilities)            │
│  ├── Reliability (resource requests, probes)              │
│  ├── Efficiency (resource limits)                         │
│  └── Custom checks                                        │
│                                                             │
│  DEPLOYMENT OPTIONS:                                       │
│  ├── Dashboard - Web UI for cluster                       │
│  ├── CLI - Local scanning                                 │
│  ├── Admission Controller - Block bad configs             │
│  └── CI/CD - Scan before deploy                           │
│                                                             │
│  SCORING:                                                  │
│  Provides letter grades (A-F) based on checks             │
│  Helps prioritize remediation                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

kube-hunter moves from audit into controlled penetration testing. It looks for exposed Kubernetes components, kubelet weaknesses, etcd exposure, and other discoverable risks. Because it can run in remote, internal, and active modes, it must be used with change-control discipline. An internal scan can reveal what an attacker might see after gaining a foothold, while an active scan can alter systems or trigger alarms. That makes authorization and scoping part of the tool, not paperwork around the tool.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBE-HUNTER                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Kubernetes penetration testing tool                  │
│  BY: Aqua Security (open source)                           │
│                                                             │
│  FINDS:                                                    │
│  ├── Exposed API servers                                  │
│  ├── Kubelet exposures                                    │
│  ├── etcd exposures                                       │
│  ├── Sensitive information disclosure                     │
│  └── Known vulnerabilities                                │
│                                                             │
│  MODES:                                                    │
│  ├── Remote - Scan from outside cluster                   │
│  ├── Internal - Scan from inside (as pod)                 │
│  └── Network - Scan IP range                              │
│                                                             │
│  COMMANDS:                                                 │
│  # Remote scan                                             │
│  kube-hunter --remote 192.168.1.100                       │
│                                                             │
│  # Internal scan (run as pod)                              │
│  kube-hunter --pod                                        │
│                                                             │
│  # Active exploitation (use carefully!)                    │
│  kube-hunter --active                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A useful assessment program starts with baselines and trends. The first run will often produce a discouraging list, especially on older clusters where teams have accumulated exceptions and legacy manifests. Do not respond by hiding the results. Categorize findings by platform ownership, workload ownership, severity, exploitability, and remediation cost. Then decide which findings become admission policies, which become tickets, and which remain documented risks because the platform cannot change them immediately.

War story: a financial services team once ran a benchmark tool shortly before an external audit and found several control-plane checks marked as failures. The first reaction was panic, but the deeper review showed that some checks applied to self-managed clusters while the team's managed control plane used provider-managed equivalents. The real gap was not the failed label; it was the absence of documented evidence. They fixed the evidence path, then focused engineering effort on worker-node and workload issues they actually controlled.

## Policy Enforcement: Admission as a Control Point

Policy engines turn security intent into a Kubernetes admission decision. That matters because admission happens before an object is persisted or a workload is scheduled, so it is one of the few places the platform can reject unsafe configuration consistently. Policy also creates a shared contract between security and application teams. Instead of asking every team to remember every rule, the cluster can validate labels, images, Pod Security settings, capabilities, volume types, resource limits, and namespace-specific expectations.

OPA Gatekeeper and Kyverno are the two policy engines most KCSA learners should recognize. Gatekeeper brings the Open Policy Agent model into Kubernetes through constraints and Rego templates, which makes it powerful for organizations already using OPA beyond Kubernetes. Kyverno uses Kubernetes-native YAML policies and offers validate, mutate, generate, and verify-image features. The choice is partly technical, but it is also about who will write and maintain policy. A policy nobody can read becomes shelfware with admission privileges.

```text
┌─────────────────────────────────────────────────────────────┐
│              POLICY ENGINE COMPARISON                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OPA GATEKEEPER                                            │
│  ├── Policy language: Rego                                │
│  ├── Learning curve: Steeper                              │
│  ├── Flexibility: Very high                               │
│  ├── Beyond K8s: Yes (OPA is general-purpose)             │
│  ├── Ecosystem: Large, mature                             │
│  └── Good for: Complex policies, existing OPA users       │
│                                                             │
│  KYVERNO                                                   │
│  ├── Policy language: YAML (Kubernetes-native)            │
│  ├── Learning curve: Gentler                              │
│  ├── Flexibility: High                                    │
│  ├── Beyond K8s: No (Kubernetes-specific)                 │
│  ├── Features: Validate, mutate, generate, verify         │
│  └── Good for: K8s-only, YAML-familiar teams              │
│                                                             │
│  BOTH CAN:                                                 │
│  • Block bad configurations at admission                  │
│  • Enforce organizational policies                         │
│  • Audit existing resources                               │
│  • Report violations                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Audit mode is the adoption bridge. It lets a team measure violations without blocking deployments, which is essential when existing workloads were never designed against the new policy set. The danger is staying in audit forever. A policy engine that only reports insecure configuration becomes another scanner. The path from audit to enforcement should include violation ownership, exception rules, non-production enforcement, warning periods, production rollout, and regular cleanup of expired exceptions.

Pause and predict: your team deploys Kyverno in `Audit` mode and discovers 200 policy violations across the cluster. Management wants to switch to `Enforce` mode immediately. The risky outcome is not that all insecure workloads magically become secure; it is that restarted pods, emergency rollouts, and routine deployments can suddenly fail across many teams. Enforcement is powerful because it blocks change, so it must be introduced with the same care as any other production control.

Policy tools also expose an important design tension. Mutation can reduce toil by adding defaults such as labels, resource requests, or security contexts, but it can also hide responsibility if developers never see what the platform changed. Validation is clearer because it rejects bad manifests, but it may slow teams until they learn the standards. Generation can create supporting resources such as NetworkPolicies, but generated objects must still fit the application model. Choose the policy style that teaches the desired behavior.

The healthiest policy programs publish examples, not just failures. If a privileged container is blocked, the error should explain the safer alternative and link to a working manifest. If images must come from approved registries, the policy should define how new registries are approved. If production namespaces require signed images, the pipeline should produce signatures automatically. Admission policy should feel like guardrails on a narrow mountain road: firm enough to prevent disaster, visible enough that drivers know where the edge is.

## Runtime Security and Behavioral Detection

Runtime tools handle the uncomfortable truth that preventive controls are never complete. A clean scan can miss a zero-day, an admission policy can allow a manifest that later behaves maliciously, and a signed image can still contain vulnerable application logic. Runtime detection watches what processes, files, network calls, syscalls, and Kubernetes events actually occur after the workload starts. It is the difference between checking a restaurant's ingredients at delivery time and watching the kitchen during service.

Falco is the canonical Kubernetes runtime detection tool. It observes system calls through a kernel module or eBPF probe, enriches events with container and Kubernetes metadata, evaluates rules, and sends alerts to configured outputs. Its default rules catch behaviors such as shells spawned inside containers, writes to sensitive paths, unexpected package management commands, and suspicious network tooling. The strength of Falco is maturity and rule ecosystem; the cost is that useful runtime detection always requires tuning.

```text
┌─────────────────────────────────────────────────────────────┐
│              FALCO ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DATA SOURCES:                                             │
│  ├── System calls (kernel module or eBPF)                 │
│  ├── Kubernetes audit logs                                │
│  └── Cloud audit logs (AWS CloudTrail, etc.)              │
│                                                             │
│  RULE ENGINE:                                              │
│  Rules written in Falco rule language                      │
│  - rule: Terminal shell in container                      │
│    condition: spawned_process and container and shell     │
│    output: Shell in container (user=%user.name ...)       │
│    priority: WARNING                                       │
│                                                             │
│  OUTPUT CHANNELS:                                          │
│  ├── Stdout / syslog                                      │
│  ├── File                                                 │
│  ├── HTTP webhook                                         │
│  ├── Slack / Teams                                        │
│  ├── Kafka / NATS                                         │
│  └── gRPC                                                 │
│                                                             │
│  DEPLOYMENT:                                               │
│  ├── DaemonSet on nodes                                   │
│  └── Requires privileged (for eBPF/kernel module)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The privilege requirement deserves attention. Runtime tools often need deep host visibility, so they may run as privileged DaemonSets or use kernel capabilities that ordinary workloads should never receive. That is not hypocrisy; it is a controlled exception for a defensive component. The platform team must protect that exception with tight RBAC, limited image sources, node selection, update discipline, and monitoring of the security tool itself. A compromised runtime sensor would be a high-value target.

Tetragon approaches runtime security through eBPF observability and enforcement, especially in environments already using Cilium. It can monitor process execution, file access, network activity, and system calls with rich Kubernetes context. Compared with Falco, Tetragon often feels closer to network and process enforcement, while Falco offers a broad detection rule ecosystem and mature alerting integrations. Both can be appropriate, but running both without clear ownership can duplicate signals and confuse responders.

```text
┌─────────────────────────────────────────────────────────────┐
│              TETRAGON                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: eBPF-based security observability and enforcement    │
│  BY: Cilium/Isovalent (CNCF)                              │
│                                                             │
│  MONITORS:                                                 │
│  ├── Process execution                                    │
│  ├── File access                                          │
│  ├── Network activity                                     │
│  └── System calls                                         │
│                                                             │
│  KEY FEATURES:                                             │
│  ├── Enforcement (not just detection)                     │
│  ├── Low overhead (in-kernel eBPF)                        │
│  ├── Rich Kubernetes context                              │
│  └── TracingPolicy CRDs                                   │
│                                                             │
│  VS FALCO:                                                 │
│  ├── Both: eBPF-based runtime monitoring                  │
│  ├── Tetragon: More enforcement focus                     │
│  ├── Tetragon: Tighter Cilium integration                 │
│  └── Falco: More mature, larger rule library              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Runtime security succeeds or fails on signal quality. A "shell in container" rule is valuable when production web containers never need shells, but noisy when maintenance jobs legitimately run shell scripts all day. Suppressing the rule globally destroys coverage. The better approach is contextual tuning: allow known maintenance pods by label, downgrade expected events, keep high-priority alerts for unusual namespaces, and route severe events to people who can act. Detection rules should encode operational knowledge, not fight it.

War story: a platform team deployed Falco with default alerts and routed every warning to the same incident channel. Within two weeks, engineers had trained themselves to ignore the stream because batch jobs produced noisy shell alerts and backup containers wrote to paths that looked suspicious. The fix was not uninstalling Falco. The team built namespace-specific exceptions, mapped severities to response channels, attached runbooks, and reviewed the top noisy rules every Friday until alerts became rare enough to deserve attention.

Runtime tooling also depends on response maturity. If Falco or Tetragon detects a suspicious process, the responder needs to know whether to isolate a namespace, scale a deployment to zero, capture forensic data, rotate credentials, block egress, or open an application incident. A tool can say "this behavior is unusual"; it cannot decide the business impact alone. The stack is complete only when detection leads to a practiced action.

## Secrets Management and Service-to-Service Security

Secrets management tools reduce the chance that credentials leak through manifests, logs, images, or developer workstations. Kubernetes Secrets are base64-encoded API objects, not a full secrets management system. They become much safer when encryption at rest, RBAC, service account scoping, audit logging, external secret stores, and rotation processes are in place. The right tool depends on whether the team needs dynamic credentials, GitOps-friendly encrypted manifests, cloud provider integration, or centralized auditability.

HashiCorp Vault is a broad secrets platform rather than a Kubernetes-only tool. It can issue dynamic secrets, rotate credentials, provide detailed audit logs, and enforce access policies. In Kubernetes, Vault often appears through agent injection, CSI mounts, or an operator that syncs secrets into Kubernetes Secret objects. Each integration changes the trust boundary. Injected files avoid storing some values as Kubernetes API objects, while synced secrets fit existing applications but reintroduce Kubernetes Secret lifecycle concerns.

```text
┌─────────────────────────────────────────────────────────────┐
│              VAULT WITH KUBERNETES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Enterprise secrets management                        │
│  BY: HashiCorp                                             │
│                                                             │
│  INTEGRATION METHODS:                                      │
│                                                             │
│  1. VAULT AGENT INJECTOR                                   │
│     ├── Sidecar automatically injects secrets             │
│     ├── Annotations control what secrets to inject         │
│     └── Secrets written to shared volume                   │
│                                                             │
│  2. CSI DRIVER                                             │
│     ├── Mounts secrets as volumes                         │
│     └── Kubernetes CSI standard                            │
│                                                             │
│  3. EXTERNAL SECRETS OPERATOR                              │
│     ├── Syncs Vault secrets to K8s Secrets                │
│     └── Automatic rotation                                 │
│                                                             │
│  BENEFITS:                                                 │
│  • Dynamic secrets (auto-generated)                       │
│  • Automatic rotation                                      │
│  • Detailed audit logging                                 │
│  • Fine-grained access control                            │
│  • Encryption as a service                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Sealed Secrets solves a narrower GitOps problem. Teams want declarative manifests in Git, but ordinary Kubernetes Secret objects should not be committed because base64 is only encoding. Sealed Secrets encrypts a Secret into a SealedSecret that only the cluster controller can decrypt. This lets the encrypted object travel through Git while keeping plaintext out of the repository. The tradeoff is that decryption is tied to the controller's private key and operational recovery depends on key backup discipline.

```text
┌─────────────────────────────────────────────────────────────┐
│              SEALED SECRETS                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Encrypt secrets for GitOps                           │
│  BY: Bitnami                                               │
│                                                             │
│  PROBLEM SOLVED:                                           │
│  • Can't commit K8s Secrets to Git (base64 encoded)        │
│  • Need secrets in version control for GitOps              │
│                                                             │
│  HOW IT WORKS:                                             │
│  1. Install controller in cluster                          │
│  2. Controller generates public/private key pair           │
│  3. Use kubeseal CLI to encrypt secrets with public key    │
│  4. Commit encrypted SealedSecret to Git                   │
│  5. Controller decrypts to regular Secret in cluster       │
│                                                             │
│  WORKFLOW:                                                 │
│  kubectl create secret ... --dry-run -o yaml |            │
│    kubeseal > sealed-secret.yaml                          │
│  git add sealed-secret.yaml                               │
│  git commit -m "Add encrypted secret"                     │
│                                                             │
│  SealedSecret → Git → Cluster → Secret                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Secrets tooling should be evaluated through rotation and blast radius, not only storage. A static database password encrypted into Git can still live too long, appear in application memory, and be copied into logs if the application mishandles it. Vault dynamic credentials reduce that window but add operational dependencies. External Secrets Operator can bridge cloud secret managers into Kubernetes but still creates Kubernetes Secret objects. The best design is the one that makes rotation routine and limits how many workloads can use each credential.

Service mesh security adds another layer by giving workloads stronger service identity and policy-controlled communication. Istio can provide mutual TLS, certificate management, peer authentication, request authentication, and authorization policies that reason about service principals, paths, methods, and headers. This is more expressive than plain NetworkPolicy, but it also adds sidecars or ambient components, control plane behavior, certificate rotation, and debugging complexity. Mesh security is powerful when service identity is the problem; it is expensive when teams only need simple network segmentation.

```text
┌─────────────────────────────────────────────────────────────┐
│              ISTIO SECURITY                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  mTLS (MUTUAL TLS)                                         │
│  ├── Automatic certificate management                     │
│  ├── Encryption between all services                      │
│  ├── Service identity via SPIFFE                          │
│  └── Modes: STRICT, PERMISSIVE, DISABLE                   │
│                                                             │
│  AUTHORIZATION POLICIES                                    │
│  ├── Allow/deny based on source service                   │
│  ├── Method, path, header matching                        │
│  ├── JWT validation                                       │
│  └── More granular than NetworkPolicy                     │
│                                                             │
│  EXAMPLE:                                                  │
│  apiVersion: security.istio.io/v1beta1                    │
│  kind: AuthorizationPolicy                                │
│  spec:                                                    │
│    selector:                                              │
│      matchLabels:                                         │
│        app: backend                                       │
│    rules:                                                 │
│    - from:                                                │
│      - source:                                            │
│          principals: ["frontend.default.svc"]             │
│      to:                                                  │
│      - operation:                                         │
│          methods: ["GET", "POST"]                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The decision point is whether the organization is trying to protect secrets, authenticate services, authorize requests, or all three. Vault and cloud secret managers help applications obtain credentials. Sealed Secrets helps GitOps teams store encrypted secret manifests. Istio helps workloads identify and authorize each other at request time. These tools can complement each other, but they should not be treated as substitutes. Encrypting a Secret in Git does not prove that only the right service can call the backend, and mTLS does not rotate a leaked database password.

Which approach would you choose here and why: a small platform team with ten services wants GitOps and simple encrypted credentials, while a larger regulated organization wants dynamic database accounts, central audit logs, and short-lived credentials? The small team may reasonably start with Sealed Secrets and strict RBAC. The regulated organization is likely better served by Vault or a cloud secret manager integrated through CSI or an external secrets controller, with service identity layered separately.

## Tool Selection Guide

Tool selection becomes easier when you name the job before naming the tool. "We need Kubernetes security" is too broad to guide a design. "We need to block unsigned images from unapproved registries in production" points toward signing, registry policy, and admission enforcement. "We need to know whether our worker nodes match CIS expectations" points toward kube-bench or provider benchmark evidence. "We need to detect a shell spawned in a production container" points toward runtime detection and response.

```text
┌─────────────────────────────────────────────────────────────┐
│              TOOL SELECTION BY USE CASE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "I need to scan images for vulnerabilities"               │
│  → Trivy (comprehensive), Grype (fast)                    │
│                                                             │
│  "I need to check cluster against CIS benchmark"           │
│  → kube-bench                                             │
│                                                             │
│  "I need to audit workload configurations"                 │
│  → kubeaudit, Polaris                                     │
│                                                             │
│  "I need to block insecure configurations"                 │
│  → Kyverno (simpler), OPA/Gatekeeper (flexible)           │
│                                                             │
│  "I need runtime threat detection"                         │
│  → Falco (mature), Tetragon (Cilium users)               │
│                                                             │
│  "I need to sign and verify images"                        │
│  → Cosign (Sigstore)                                      │
│                                                             │
│  "I need secrets management beyond K8s Secrets"            │
│  → Vault (enterprise), Sealed Secrets (GitOps)            │
│                                                             │
│  "I need service-to-service security"                      │
│  → Istio (full mesh), Linkerd (simpler)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A minimum viable security tooling stack for many clusters starts with image scanning, admission policy, runtime detection, and benchmark evidence. That usually means Trivy or Grype in CI, Kyverno or Gatekeeper in audit mode, Falco or Tetragon on nodes, and kube-bench for baseline reviews. Secrets management may be urgent earlier if teams are already committing credentials or using long-lived shared passwords. Image signing may be urgent earlier if supply-chain risk is the driver. The right first tool is the one that closes the most dangerous open path with the least operational surprise.

The following comparison summarizes the main categories in operational terms. Notice that the "best" tool changes depending on who owns remediation. Developers can usually fix Dockerfiles and dependencies faster than they can change cluster control plane settings. Platform teams can enforce admission policy but need application context for exceptions. Security teams can define detection goals, but application owners know which runtime behavior is normal. A stack design that ignores ownership will stall even if every tool is technically sound.

| Category | Typical Tools | Primary Question | Best First Owner |
|---|---|---|---|
| Image scanning | Trivy, Grype, Clair | Is this artifact carrying known risk? | Application team with platform guardrails |
| Image signing | Cosign, Notary | Can we prove artifact identity and integrity? | Platform and CI/CD owners |
| Cluster assessment | kube-bench, kubeaudit, Polaris | Is the platform or workload baseline weak? | Platform team plus service owners |
| Admission policy | Kyverno, Gatekeeper | Should this object be accepted by the API server? | Platform team with security policy input |
| Runtime detection | Falco, Tetragon | Is the running workload behaving suspiciously? | Security operations and platform team |
| Secrets management | Vault, Sealed Secrets, SOPS | How are credentials stored, delivered, and rotated? | Platform team and application owners |
| Service mesh security | Istio, Linkerd, Cilium features | Can services authenticate and authorize each other? | Platform networking owners |

The original quick-reference summary is still useful when you need a compact KCSA memory aid. Use it after the deeper comparison, not instead of the deeper comparison, because the table names the category and primary purpose without explaining ownership, rollout mode, or operational tradeoff.

| Category | Tools | Purpose |
|----------|-------|---------|
| **Scanning** | Trivy, Grype | Find vulnerabilities |
| **Signing** | Cosign | Verify image authenticity |
| **Assessment** | kube-bench, kubeaudit | Check configurations |
| **Policy** | Kyverno, Gatekeeper | Enforce standards |
| **Runtime** | Falco, Tetragon | Detect threats |
| **Secrets** | Vault, Sealed Secrets | Manage sensitive data |

The most important design habit is avoiding orphan findings. Every tool output should have a destination, an owner, a severity model, and a remediation expectation. A Trivy finding may fail the build, create a ticket, or be accepted with an expiry date. A Kyverno violation may warn a developer, block production, or produce a namespace-level report. A Falco alert may page immediately, create a low-priority event, or enrich a SIEM. Without those decisions, the stack is only collecting evidence of future regret.

### Worked Example: Reading the Stack as a Story

Imagine a payments namespace where a team deploys a new API image every afternoon. The first control is Trivy in CI, which fails the build if the image contains a critical vulnerability with an available fix. The second control is Cosign, which signs the image after the pipeline produces the SBOM and test results. The third control is Kyverno, which rejects unsigned images, blocks privileged pods, and requires the namespace's baseline security context. Each control answers a different question, so the release decision is stronger than any single scan result.

Now imagine that the same API passes CI and admission but begins making unusual outbound connections after deployment. The scanner and policy engine did their jobs, but neither watches process behavior after startup. Falco or Tetragon supplies the runtime view, while NetworkPolicy or a mesh policy may limit which destinations the workload can reach. A responder who sees the runtime alert should ask whether the image digest matches the signed artifact, whether the pod was admitted under the expected policy, and whether any secret mounted into the pod needs rotation.

The example shows why security tooling conversations should follow the workload path. Artifact creation, admission, runtime behavior, credential use, and service communication are connected events in one story. If the team discusses tools as isolated products, it will miss the handoffs. If it discusses the deployment story, it can decide where a finding should block, where it should warn, where it should page, and where it should become evidence for the next security review.

This style of review also prevents overengineering. A small internal batch job may not need a service mesh policy on day one if it has no inbound service traffic and runs in a restricted namespace. It still needs image scanning, reasonable admission policy, and secret handling. A public API that processes payments likely needs stronger signing, runtime detection, egress controls, secret rotation, and request-level authorization. The difference is not that one team cares about security and the other does not; the difference is risk, exposure, and operational value.

## Patterns & Anti-Patterns

Strong Kubernetes security tooling programs use a small set of proven patterns. They start with visibility, graduate to enforcement, and keep the feedback loop close to the people who can fix the issue. They also treat tools as controls with operational cost, not as badges. Installing a policy engine, scanner, or runtime detector changes developer experience, incident response, and upgrade planning. Those changes should be designed deliberately.

| Pattern | When to Use | Why It Works | Scaling Considerations |
|---|---|---|---|
| Audit before enforce | Introducing Kyverno, Gatekeeper, or Polaris admission checks into an existing cluster | It reveals current violations without breaking deployments and gives teams time to remediate | Set deadlines, owners, and exception expiry dates so audit mode does not become permanent |
| Shift left plus verify right | Combining CI image scans with registry or cluster scans | CI catches issues early while later scans detect drift, old tags, and database changes | Keep severity rules consistent or developers will see conflicting verdicts |
| Runtime alerts with runbooks | Deploying Falco or Tetragon in production | Responders know what each alert means and what action is authorized | Review noisy rules regularly and route severities to different channels |
| Policy as product | Publishing examples, docs, and self-service exception paths for admission policies | Teams learn the intended secure pattern instead of only seeing rejection messages | Version policies, announce breaking changes, and measure violation trends |

Anti-patterns appear when teams confuse tool presence with security outcomes. The most common failure is a dashboard full of findings that no one owns. Another is an enforcement rollout that surprises application teams and causes outages. A third is buying a broad platform and assuming its default rules match the organization's threat model. The better alternative is to define the control objective, wire the tool into the workflow, and measure whether risky behavior actually decreases.

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|---|---|---|---|
| Scanner as theater | Vulnerabilities are reported but never remediated | It is easy to add a CI step and hard to fund cleanup | Define severity SLAs, exception expiry, and owner routing |
| Big-bang enforcement | Valid deployments fail suddenly across namespaces | Leadership wants fast proof of security progress | Move from audit to warn to enforce by namespace and policy class |
| Runtime firehose | Responders ignore alerts because false positives dominate | Default rules are treated as finished production policy | Tune rules with labels, severities, and documented runbooks |
| Tool overlap without ownership | Multiple tools report similar findings with different language | Teams install popular tools independently | Pick a source of truth for each category and map duplicate signals |

The original quick mistake table remains a good shorthand for a whiteboard review, especially when you are coaching a team that is about to install tools faster than it can operate them. Treat these phrases as prompts for discussion, then expand them into the more specific mistakes and fixes later in the module.

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Too many tools | Complexity, overlap | Choose focused stack |
| Scanning without action | False security | Define SLAs, automate |
| Policy without testing | Breaks deployments | Test in audit mode first |
| Runtime without response | Alerts ignored | Create incident runbooks |
| No baseline | Can't measure improvement | Run assessments first |

The pattern to remember for the KCSA is coverage with flow. A tool should cover a category, produce a signal at the right time, and flow that signal to a decision. If the decision is "block," use admission or CI gates with clear remediation. If the decision is "investigate," use runtime alerts with context and runbooks. If the decision is "improve," use benchmark and audit reports that become backlog items. Coverage without flow creates noise; flow without coverage misses risk.

## Decision Framework

Use this framework when you design or review a Kubernetes security tooling stack. Start by asking where the risk appears. If it appears before code reaches the cluster, scanning and signing are natural controls. If it appears in manifests, admission policy and workload auditing are natural controls. If it appears after the container starts, runtime detection and network observability are needed. If it involves credentials or service identity, secrets and mesh controls belong in the conversation.

| Decision Question | Choose This Direction | Tradeoff to Accept |
|---|---|---|
| Do we need broad image, IaC, and manifest scanning quickly? | Start with Trivy because it covers several artifact types with one workflow | Broad coverage can create mixed finding types that need careful triage |
| Do we already generate SBOMs and want focused vulnerability analysis? | Use Syft with Grype for SBOM-first scanning | You maintain two connected tools instead of one broad scanner |
| Do we need Kubernetes-native policy authorship? | Choose Kyverno for YAML-based validate, mutate, generate, and verify rules | Policies are Kubernetes-specific and less portable beyond the cluster |
| Do we use OPA elsewhere or need complex reusable policy logic? | Choose Gatekeeper with Rego-based constraints | Rego has a steeper learning curve for many platform teams |
| Do we need mature runtime detection with many existing rules? | Start with Falco and tune alerts by namespace, image, and severity | The sensor needs privileged visibility and tuning effort |
| Are we already standardized on Cilium and need eBPF enforcement context? | Evaluate Tetragon alongside Cilium security features | The value is strongest when the network and runtime stack are already aligned |
| Do teams need encrypted GitOps secrets with modest complexity? | Use Sealed Secrets with careful key backup | It does not provide dynamic credentials or central secret policy by itself |
| Do we need dynamic secrets, central audit, and rotation? | Use Vault or a cloud secret manager through CSI or an external secrets controller | Operational dependency and integration complexity increase |

After choosing the direction, decide the rollout mode. Visibility tools can usually start in report mode. Enforcement tools should start in audit or warning mode unless the target namespace is new and empty. Runtime tools should start with alert routing that separates informational events from urgent incidents. Secrets tools need migration planning because applications may cache credentials or expect environment variables. Service mesh security should begin with permissive or namespace-scoped rollout before strict mTLS and authorization policies reach production.

Here is the practical decision loop: define the risk, choose the category, pick the tool that your team can operate, run in visibility mode, measure findings, assign owners, enforce only the stable rules, and review exceptions. Repeat the loop when Kubernetes upgrades, the team changes deployment patterns, or the threat model changes. Kubernetes 1.35+ clusters evolve quickly; a stack that was adequate last quarter may miss a new admission policy, runtime capability, or provider control today.

One final decision test is reversibility. If a tool can be introduced in read-only mode and removed without changing application behavior, it is a low-risk first experiment. If a tool changes admission, network paths, secret delivery, or sidecar behavior, it deserves a staged rollout and a rollback plan. This is why scanners and benchmark tools often come before enforcing policy or service mesh strictness. Visibility builds the evidence base that makes later enforcement credible.

Another test is skill fit. Gatekeeper may be a better long-term choice for an organization already using OPA policies in CI, API gateways, and cloud authorization because the same policy language can travel across systems. Kyverno may be a better first choice for Kubernetes-heavy teams that want policies written in familiar YAML. Falco may be a faster runtime win for teams that need common detection rules, while Tetragon may fit teams already invested in Cilium and eBPF observability. The right comparison includes the humans who will maintain the rules.

Finally, decide how success will be measured. "Tool installed" is not a security outcome. Better measures include the percentage of images scanned before deployment, the number of policy violations trending down, the mean age of vulnerability exceptions, the false-positive rate of runtime alerts, the number of secrets rotated successfully, and the time required to produce benchmark evidence. These measurements turn security tooling from a one-time installation into a continuous platform capability.

## Did You Know?

- **Falco joined the CNCF in 2018 and later graduated**, which is one reason its rule ecosystem and Kubernetes integrations are widely recognized.
- **Cosign keyless signing relies on OpenID Connect identity**, so a CI workflow can sign an image without long-lived private signing keys stored in the pipeline.
- **CIS Kubernetes Benchmarks are versioned against Kubernetes releases**, which is why benchmark evidence should name the cluster version and benchmark profile.
- **Kubernetes Secrets are base64-encoded API objects by default**, so teams still need encryption at rest, RBAC, audit logging, and rotation discipline.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Installing too many tools at once | Teams want quick coverage and copy popular reference stacks without mapping ownership | Start with one tool per lifecycle gap, name the owner, and add overlap only when it solves a real problem |
| Scanning images without remediation rules | A scanner is easy to add to CI, but fixing old dependencies takes planning | Define severity SLAs, ticket routing, exception expiry, and a policy for unfixed vulnerabilities |
| Turning policy enforcement on too quickly | Audit findings create pressure to show immediate progress | Move from audit to warning to enforcement by namespace, starting with low-risk workloads |
| Treating runtime alerts as self-explanatory | Default rules produce technical messages without local business context | Attach runbooks, enrich alerts with labels, and tune known-good behavior instead of muting entire rules |
| Using Sealed Secrets as a full Vault replacement | Both tools involve secrets, so teams assume they solve the same problem | Use Sealed Secrets for encrypted GitOps manifests and Vault or a cloud manager for dynamic credentials and central audit |
| Ignoring managed-cluster boundaries in benchmark results | kube-bench can report checks that the customer cannot directly change | Separate provider-owned controls from customer-owned controls and document compensating evidence |
| Accepting signed images without vulnerability policy | Signing is mistaken for a security scan | Verify signatures for identity and integrity, then apply scanner or attestation rules for risk decisions |

## Quiz

<details>
<summary>Your organization wants to evaluate security tool coverage across build, deploy, runtime, audit, secrets, and service-to-service phases. The current stack has Trivy in CI and no other controls. What coverage gaps would you report first?</summary>

Trivy gives useful build-time vulnerability visibility, but it does not enforce Kubernetes manifests at admission, verify runtime behavior, benchmark cluster configuration, manage secrets, or authenticate service-to-service calls. The first report should separate preventive and detective gaps so leaders do not overestimate what image scanning provides. A reasonable next step is Kyverno or Gatekeeper in audit mode for deployment controls, kube-bench for platform baseline evidence, and Falco or Tetragon for runtime detection. Secrets and mesh controls should be prioritized based on whether credentials or service identity are already active risk drivers.

</details>

<details>
<summary>Your team must compare Trivy, Grype, Cosign, kube-bench, Kyverno, Gatekeeper, Falco, Tetragon, Vault, Sealed Secrets, and Istio for a Kubernetes 1.35+ platform. How would you group them so the comparison is useful?</summary>

Group them by security job rather than by popularity. Trivy and Grype belong in scanning, Cosign belongs in signing and verification, kube-bench belongs in benchmark assessment, Kyverno and Gatekeeper belong in admission policy, Falco and Tetragon belong in runtime detection, Vault and Sealed Secrets belong in secrets management, and Istio belongs in service identity and authorization. This grouping prevents false comparisons such as asking whether Cosign is better than Trivy, because they answer different questions. It also reveals where overlap is real, such as Kyverno versus Gatekeeper or Falco versus Tetragon.

</details>

<details>
<summary>A platform team designs an adoption plan for Kyverno after finding many violations in audit mode. Leadership asks for production enforcement by the end of the week. What safer plan should the team propose?</summary>

The team should avoid a sudden switch from audit to enforce across all namespaces because normal restarts and deployments could fail at once. A safer plan categorizes violations by severity, assigns service owners, fixes low-effort issues, and moves policies through warning and enforcement one class at a time. Non-production namespaces should enforce first, followed by production namespaces that have reached zero audit violations for the chosen policy set. Exceptions should be explicit, owned, time-limited, and reviewed so audit mode does not become permanent.

</details>

<details>
<summary>During an incident, Falco reports shells in containers, kube-bench has several failed node checks, and Trivy reports high vulnerabilities in an image. How do you diagnose which finding maps to the immediate operational risk?</summary>

Start with the runtime signal because it describes behavior happening now. A shell in a production container may indicate active misuse, so responders should identify the pod, image, namespace, user, and recent deployment history before deciding whether to isolate or capture evidence. The Trivy finding explains a possible entry path if the vulnerable package is reachable, while kube-bench findings describe platform weaknesses that may increase blast radius. The diagnosis should connect the signals instead of treating them as three unrelated tickets.

</details>

<details>
<summary>A team wants to implement a minimum viable Kubernetes security tooling stack and only has one sprint. Which tools and validation steps would you choose first?</summary>

Choose a small stack that covers the highest-value lifecycle points without overwhelming the team. A practical first sprint is Trivy in CI for image scanning, Kyverno in audit mode for admission policy visibility, kube-bench for a cluster baseline, and Falco with limited alert routing for runtime detection. Validation should include one intentionally vulnerable image, one manifest that violates policy, one benchmark report, and one expected runtime alert in a test namespace. Secrets and signing can be next if the current sprint cannot include them responsibly.

</details>

<details>
<summary>Your organization uses Vault centrally, but one GitOps team asks to use Sealed Secrets for several application credentials. How should you decide whether this creates a coverage gap?</summary>

Compare the requirement to each tool's strength. Sealed Secrets is reasonable when the goal is encrypted GitOps manifests and the credentials are static enough for that workflow, but it does not provide dynamic credential issuance, central policy, or the same audit model as Vault. If the organization requires rotation evidence and central access control, External Secrets Operator or a Vault CSI integration may preserve GitOps deployment while keeping Vault as the source of truth. The decision should be based on rotation, audit, and blast radius, not preference alone.

</details>

## Hands-On Exercise: Security Tool Stack Design

In this exercise, you will design and validate a minimum viable security tooling stack for a production Kubernetes environment. You do not need to install every tool locally to complete the reasoning, but you should write the stack as if a platform team could turn it into tickets. Use the `k` alias consistently when you sketch validation commands, such as `k get pods -A`, because the goal is a repeatable Kubernetes operator workflow rather than one-off documentation.

**Scenario**: Your task is to design a security tool stack for a production Kubernetes environment with these concrete requirements:

- Scan images for vulnerabilities in CI/CD
- Enforce policies to block insecure configurations
- Detect runtime threats
- Manage secrets securely
- Audit cluster configuration against CIS benchmark

**Progressive tasks**: Work through these tasks in order so the design moves from broad lifecycle coverage into rollout and evidence:

- [ ] Map each requirement to one lifecycle category and one primary tool.
- [ ] Choose whether Kyverno or Gatekeeper is the first admission policy engine and justify the tradeoff.
- [ ] Define one audit-mode policy, one enforcement milestone, and one exception rule with an owner.
- [ ] Describe how runtime alerts from Falco or Tetragon will route to a responder with enough Kubernetes context.
- [ ] Add one secrets-management choice and explain how rotation or GitOps recovery will work.
- [ ] Write success criteria that prove the stack can scan, block, detect, audit, and handle credentials.

<details>
<summary>Recommended Tool Stack</summary>

**1. Image Scanning (CI/CD)**

- **Tool**: Trivy
- **Why**: Comprehensive scanning (OS + language packages), fast, good CI integration
- **Implementation**:

```bash
# In CI pipeline
trivy image --exit-code 1 --severity CRITICAL,HIGH $IMAGE
```

**2. Policy Enforcement**

- **Tool**: Kyverno
- **Why**: YAML-native, easier adoption, validate + mutate + generate
- **Implementation**:
  - Enforce Pod Security Standards
  - Require resource limits
  - Block privileged containers
  - Enforce allowed registries

**3. Runtime Security**

- **Tool**: Falco
- **Why**: Mature, rich rule library, CNCF graduated
- **Implementation**:
  - Deploy as DaemonSet
  - Enable default rules
  - Alert to Slack/PagerDuty
  - Create response runbooks

**4. Secrets Management**

- **Tool**: Sealed Secrets + External Secrets Operator
- **Why**: GitOps-friendly, can integrate with cloud secret stores
- **Implementation**:
  - Sealed Secrets for GitOps workflow
  - External Secrets Operator for cloud provider secrets
  - Rotate secrets regularly

**5. Configuration Audit**

- **Tool**: kube-bench
- **Why**: Industry standard CIS benchmark
- **Implementation**:
  - Run as Job weekly/monthly
  - Alert on failures
  - Track improvement over time

**Optional Additions:**

- **Cosign** for image signing (if supply chain security is priority)
- **Istio** for mTLS if service-to-service encryption needed
- **Polaris** dashboard for visibility

**Architecture:**

```text
CI/CD: Trivy scan → Cosign sign → Push
                          ↓
Cluster: Kyverno (admission) → Falco (runtime)
                ↓                    ↓
         Block bad configs    Detect threats
                ↓                    ↓
Secrets: Sealed Secrets ← Git → External Secrets
                ↓
Audit: kube-bench → Reports
```

</details>

<details>
<summary>Validation checklist solution</summary>

A strong answer maps image scanning to Trivy or Grype, admission policy to Kyverno or Gatekeeper, runtime detection to Falco or Tetragon, cluster baseline review to kube-bench, and secrets management to Vault, a cloud secret manager, Sealed Secrets, or External Secrets Operator. The policy rollout should begin in audit mode, include violation ownership, and move to enforcement by namespace or policy class. Runtime detection should include alert routing and runbooks, not only installation. The final validation should prove each tool produces a signal and that each signal has an owner and decision path.

</details>

**Success criteria**: The exercise is complete when your written stack can be reviewed against the following operational checks:

- [ ] Every requirement maps to a lifecycle category and a named primary tool.
- [ ] The design explains why each selected tool fits the team and where it overlaps with alternatives.
- [ ] The policy rollout includes audit mode, enforcement milestones, and exception handling.
- [ ] Runtime detection includes alert routing, tuning, and response ownership.
- [ ] Secrets management includes rotation, recovery, or source-of-truth reasoning.
- [ ] The final stack includes scan, sign or verify, audit, policy, runtime, and secrets coverage.

## Sources

- [Kubernetes: Security Checklist](https://kubernetes.io/docs/concepts/security/security-checklist/)
- [Kubernetes: Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes: Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Kubernetes: Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [Kubernetes: Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Trivy Documentation](https://trivy.dev/latest/)
- [Grype Documentation](https://github.com/anchore/grype)
- [Cosign Documentation](https://docs.sigstore.dev/cosign/overview/)
- [OPA Gatekeeper Documentation](https://open-policy-agent.github.io/gatekeeper/website/docs/)
- [Kyverno Documentation](https://kyverno.io/docs/)
- [Falco Documentation](https://falco.org/docs/)
- [Tetragon Documentation](https://tetragon.io/docs/)
- [kube-bench Project](https://github.com/aquasecurity/kube-bench)
- [Sealed Secrets Project](https://github.com/bitnami-labs/sealed-secrets)
- [Istio Authorization Policy](https://istio.io/latest/docs/reference/config/security/authorization-policy/)

## Next Module

[Module 6.1: Compliance Frameworks](/k8s/kcsa/part6-compliance/module-6.1-compliance-frameworks/) - Next, you will connect these practical Kubernetes controls to compliance frameworks, evidence collection, and audit conversations that security teams use to prove a platform is governed responsibly.
