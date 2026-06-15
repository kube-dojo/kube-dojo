---
citations_verified: true
revision_pending: false
title: "Module 4.1: DevSecOps Fundamentals"
slug: platform/disciplines/reliability-security/devsecops/module-4.1-devsecops-fundamentals
sidebar:
  order: 2
---

> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 45-55 min | Track: DevSecOps

## Prerequisites

Before starting this module, you should understand defense in depth and least privilege from the [Security Principles Track](/platform/foundations/security-principles/), because DevSecOps builds on those foundations rather than replacing them. You also need basic CI/CD vocabulary—commits, builds, tests, deployments—so that pipeline stages in this lesson map to something you have seen in practice. Familiarity with GitOps-style continuous delivery is helpful but not required; the security patterns here apply whether you deploy with Argo CD, a hosted pipeline, or a simpler script-driven workflow.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Evaluate your organization's security posture to identify gaps in the DevSecOps lifecycle**
- **Design a DevSecOps strategy that integrates security into every phase of software delivery**
- **Implement security champion programs that distribute security knowledge across development teams**
- **Analyze the cost of security remediation at each lifecycle stage to justify shift-left investments**

## Why This Module Matters

**Hypothetical scenario:** A platform team ships daily releases for a payment-adjacent service. On the morning of a major launch, a central security audit returns dozens of findings accumulated over three sprints. Developers who wrote the affected code three weeks ago are now on call for unrelated work, context reload takes half a day per issue, and leadership must choose between delaying the launch or accepting risk. The security team is labeled a blocker even though they surfaced real problems; delivery is labeled reckless even though they met every functional test gate. Nobody wins because security was treated as a final inspection phase instead of a continuous property of the delivery system.

DevSecOps exists to break that structural deadlock. When security checks live only at the end of a cycle, findings arrive after authors have moved on, fixes compete with feature pressure, and the security function scales linearly with headcount while delivery scales with automation. Embedding security into planning, coding, building, testing, releasing, deploying, operating, and monitoring turns vulnerabilities into ordinary engineering feedback that developers can act on while context is fresh. The goal is not to eliminate human judgment—it is to make automated guardrails handle repeatable risk so expert reviewers can focus on design, threat modeling, and the exceptions that actually require debate.

Modern cloud-native delivery amplifies the problem and the opportunity. A single microservice may pull hundreds of transitive dependencies, run in a container built from a shared base image, deploy through GitOps controllers, and expose APIs you never manually tested in a staging environment that mirrors production. Manual end-of-cycle review cannot inspect that surface area at the speed teams deploy. DevSecOps responds with tool classes—static analysis, composition analysis, policy-as-code, runtime detection—that run continuously and produce evidence the whole organization can trust. This module teaches the durable practice behind those tools: where each control belongs, why shift-left economics work, and how culture change—not scanner shopping—determines whether the investment pays off.

> **The Airport Security Analogy**
>
> Imagine an airport that screens passengers only after they are seated on the aircraft. Fixing a prohibited item at the gate is inconvenient; fixing it at altitude is catastrophic. DevSecOps moves screening earlier — check-in, baggage, the security line — so dangerous items never reach the runway. The goal is not more checkpoints for their own sake; it is placing verification where failure is still recoverable and where staff can coach travelers before they commit to a flight.

The [OWASP DevSecOps Guideline](https://owasp.org/www-project-devsecops-guideline/) describes integration of security activities into existing DevOps workflows rather than a parallel audit track. That framing matters for platform teams building internal developer portals: security features should appear as catalog metadata on templates, not as a separate portal developers must discover after their service is already in production.

---

## Why Security-as-a-Final-Phase Does Not Scale

Traditional software security often followed the same shape as waterfall testing: build the product, then hand it to specialists who hunt for defects before release. That model assumes security work is separable from feature work, that reviewers can reconstruct intent from artifacts alone, and that a late gate is an acceptable price for speed everywhere else. In practice, late gates create a bottleneck whose severity grows with release frequency. A team that deploys weekly might survive quarterly audits; a team that deploys many times per day cannot wait for a human review queue without either stopping delivery or bypassing the gate entirely.

The adversarial dynamic is predictable and expensive. Developers experience security as an external veto applied after they have already "finished." Security teams experience developers as shipping first and asking forgiveness later. Both perceptions contain some truth when the process rewards speed through the functional pipeline and punishes security findings only at the edge. Neither side gets the feedback loop they need: developers do not learn secure patterns at the moment of creation, and security teams cannot scale one-to-many review across hundreds of services and thousands of commits.

Shift-left is the durable response—not because earlier is magically cheaper in every case, but because earlier feedback preserves author context, reduces rework across dependent systems, and allows automation to enforce baselines without calendar coordination. A secret caught in a pre-commit hook never enters Git history. A vulnerable dependency caught in CI blocks only the pull request that introduced it. A policy violation caught at admission prevents a misconfigured pod from ever receiving traffic. Each of those outcomes is difficult to replicate when the same defect is discovered in production under incident pressure.

Security-as-code extends that shift from tools to governance. When policies live in version control beside application manifests, changes receive peer review, roll back like any other commit, and produce an audit trail regulators expect. That is why DevSecOps pairs cultural shared ownership with pipeline automation and policy-as-code: culture alone drifts, tools alone get bypassed, and paperwork alone lies. The combination makes the secure path the default path rather than the heroic exception.

Historical context explains why the final-phase habit persists even in agile organizations. Waterfall-era security reviews were the only practical option when builds were monolithic and releases were quarterly; specialists batching work made economic sense. Agile shortened iteration length but often left security staffing and procurement unchanged, so the same batch review moved to sprint boundaries or release trains. DevOps then automated everything except security gates, producing fast pipelines that still halted at human approval queues. DevSecOps is the corrective integration step: security activities become pipeline stages with the same visibility and ownership as unit tests, not a parallel process that finishes later.

The cultural corollary is shared responsibility without shared blamelessness. DevSecOps succeeds when developers fix findings they introduce and security engineers improve the system that surfaces those findings. Blame-oriented postmortems after escapes teach teams to hide issues; learning-oriented reviews after near-misses teach teams to strengthen controls. Platform leaders reinforce the model by celebrating reduced escape rates and faster remediation, not by counting how many builds security blocked.

---

## Analyzing Remediation Cost by Lifecycle Stage

Understanding remediation cost is central to justifying shift-left investments because budget conversations rarely start with CVE identifiers—they start with engineer-hours, delay risk, and customer exposure. The exact dollar cost of fixing a defect varies by organization, regulatory context, and blast radius, but the **shape** of the curve is consistent across industry experience and frameworks such as the [NIST Secure Software Development Framework (SSDF)](https://csrc.nist.gov/publications/detail/sp/800-218/final): defects cost more to remediate the later they are discovered relative to the activity that introduced them.

Use the following numbers as **illustrative round figures** for teaching the curve, not as audited statistics for your organization. Suppose fixing an insecure API pattern during design costs one unit of effort—roughly an hour of paired design review. The same pattern caught while the developer is still editing the file might cost three units once you include local testing and a small refactor. Caught in continuous integration before merge, it might cost ten units because another engineer must review the fix, rerun pipelines, and reconcile branch state. Found in staging, multiply again for cross-team coordination and environment resets. Found in production, effort explodes: incident triage, possible rollback, customer communication, emergency change controls, and post-incident hardening.

Security defects often carry multipliers beyond pure engineering time. A logic flaw may require data exposure assessment; a dependency flaw may require scanning every deployed artifact built during the vulnerable window; a misconfiguration may require proving which environments inherited the mistake. That is why leadership charts show exponential growth toward the right side of the lifecycle even when functional bug charts look milder. DevSecOps metrics should translate that shape into terms engineering managers already track: mean time to remediate by severity, vulnerability escape rate to production, and percentage of findings fixed within the same sprint they were introduced.

When you **analyze** remediation cost for a portfolio, map findings to the stage where they *should* have been caught, not only where they were found. A production SQL injection discovered by a bug bounty program is a code-stage defect with production-stage remediation cost. Reporting it that way clarifies which control failed—missing SAST rule, absent parameterized query standard, or bypassed review—and which investment closes the gap. Over time, organizations that shift left should see total remediation cost fall even if scanner counts rise, because scanners surface issues earlier when fixes are cheap.

Finance and engineering leaders often ask for a single ROI number; honest answers present ranges and sensitivity. Illustrative planning might assume ten engineer-hours to fix a critical authentication flaw in CI versus one hundred hours when production data paths must be audited after exploitation. Even if your ratios differ, the order of magnitude gap justifies budget for pre-commit hooks, CI minutes, and policy engines that look expensive until compared with one incident quarter. Document assumptions in the business case so future metrics can validate or revise them rather than treating shift-left as faith-based spending.

---

## Designing a DevSecOps Strategy Across Every Phase

A DevSecOps strategy is not a shopping list of scanners; it is a lifecycle map that assigns each security activity to the earliest phase where it is both **accurate enough to trust** and **actionable enough for the author**. The infinity loop—plan, code, build, test, deploy, operate, monitor—becomes a checklist of intents rather than a vendor diagram.

During **plan**, security contributes threat modeling, data classification, and abuse-case review while architecture is still malleable. Lightweight STRIDE sessions on new features cost little compared to retrofitting authorization after launch. Planning also defines what "done" means for security: required scans, severity thresholds, ownership for exceptions, and evidence retained for audits.

During **code**, the developer's editor and pre-commit hooks provide the fastest feedback on secrets, dangerous APIs, and obvious misconfigurations in local files. The objective is not exhaustive proof but prevention of classes of defects that are embarrassing and expensive when pushed to shared repositories.

During **build**, pipelines generate attestable artifacts: compiled binaries, container images, infrastructure plans. This is the natural home for SAST, SCA, SBOM generation, image scanning, and IaC scanning because the build output is the unit you will promote across environments. Failures here should link to documentation and examples, not merely to CVE identifiers.

During **test**, dynamic techniques exercise running software. DAST probes external behavior; IAST instruments runtime paths during automated tests. These stages catch issues static analysis cannot see—authentication bypass, session handling mistakes, misconfigured TLS—but they are slower and flakier, so they complement rather than replace static gates.

During **release**, signing, provenance metadata, and promotion controls ensure what reaches production is what you tested. Supply-chain security matures here; Module 4.4 covers depth, but every fundamentals reader should know that unsigned or unprovenanced artifacts break downstream trust.

During **deploy**, admission controllers and policy engines enforce organizational baselines: non-root containers, network policies, resource limits, label requirements. This is guardrail enforcement at the cluster boundary—fail closed when state does not match policy.

During **operate** and **monitor**, runtime detection, vulnerability management on running workloads, and compliance drift detection close the loop. Runtime tools cannot undo a shipped secret, but they shorten mean time to detect abuse and feed prioritization for patch cycles.

A coherent **strategy** sequences investments so each phase gains one or two high-signal controls before adding exotic scanners. Teams that skip planning and buy runtime-only tools often detect breaches faster while continuing to ship preventable classes of defects at full speed.

Cross-functional alignment determines whether the strategy survives contact with roadmaps. Product managers need security requirements expressed as user stories and acceptance criteria—"service must not store PAN in logs" rather than "pass PCI scan." SRE teams need error budgets that include security work so reliability and remediation do not fight for the same sprint capacity. Legal and compliance need evidence artifacts—SBOMs, scan reports, policy versions—not slide decks. When each function sees its language reflected in the strategy, DevSecOps becomes a program rather than a security-only initiative.

Operationalizing the strategy also means defining severity semantics once for the whole organization. A "critical" finding in SCA should trigger the same response playbook as a critical runtime alert, even if different teams execute the steps. Without shared severity vocabulary, dashboards disagree and executives lose confidence. Publish thresholds, SLAs, and exception processes where developers already look—internal developer portals, pipeline logs, and service catalog entries—not in PDFs buried on a shared drive.

Feedback loops should close within the same tooling ecosystem developers already use. Pull request comments beat separate security portals; chat notifications should deep-link to failing lines; service catalog entries should show last scan status and open critical counts. When security feedback feels like part of delivery tooling, developers treat findings like test failures rather than audit surprises.

---

## Security Tool Classes: What Each Detects and Where It Lives

Tools rename themselves every year; classes endure. Teaching classes helps you evaluate any vendor announcement without relearning fundamentals.

**Static Application Security Testing (SAST)** analyzes source or bytecode without executing it. It excels at patterns—SQL injection sinks, hardcoded credentials, weak cryptography—and runs quickly in CI. Tradeoffs include false positives on framework-specific patterns and blindness to runtime configuration.

**Software Composition Analysis (SCA)** inspects dependency manifests and lockfiles against vulnerability databases and license policies. Modern applications are mostly third-party code; SCA is how you reason about risk in libraries you never read. It would have flagged the Log4Shell<!-- incident-xref: log4shell --> artifact class before deployment when paired with accurate inventories—see the canonical treatment in [Supply Chain Security](../module-4.4-supply-chain-security/).

**Dynamic Application Security Testing (DAST)** probes running applications from the outside, mimicking an attacker without source access. It finds integration and deployment mistakes SAST misses but requires stable test environments and can be noisy on UI-heavy apps.

**Interactive Application Security Testing (IAST)** instruments applications during automated tests, combining some static precision with runtime visibility. It is powerful when tests exercise real workflows but adds operational complexity.

**Secret scanning** hunts high-entropy strings, known token formats, and repository history for credentials that should live in vaults. It belongs as early as pre-commit because every minute a secret spends in Git expands rotation cost.

**Container and image scanning** inspect filesystem layers for OS packages and language dependencies in images you deploy, not just repos you compile. Base image choice dominates residual risk; scanning without updating bases treats symptoms.

**Infrastructure-as-code scanning** evaluates Terraform, Kubernetes manifests, Helm charts, and cloud templates for misconfigurations before apply. It prevents public storage buckets and overly permissive security groups from ever existing.

**Policy-as-code and admission control** encode organizational baselines in Rego, Kyverno policies, or equivalent engines evaluated at deploy time. OPA Gatekeeper and Kyverno are common Kubernetes implementations; both rely on declarative policy evaluation rather than ticket-driven review.

**Runtime security / RASP-adjacent tooling** observes syscalls, network behavior, and process anomalies on live workloads. Falco and eBPF-based tools like Tetragon exemplify detection after deploy; they do not replace left-side prevention.

**SBOM generation** documents components inside an artifact. SBOMs enable targeted response when new CVEs drop; they are not scanners themselves but evidence consumed by scanners and incident processes.

No single class provides complete coverage. Defense in depth means overlapping classes with clear ownership: developers fix SAST and SCA findings, platform teams maintain policies, security operations tunes runtime alerts.

Tuning tradeoffs matter as much as selection. SAST false positives often come from framework-specific data flow the analyzer cannot see; suppress with care and regression tests. SCA noise spikes when teams pin vague version ranges; lockfiles and automated update bots stabilize signal. DAST flakiness grows when staging lacks realistic test data; invest in synthetic fixtures rather than disabling scans. Runtime alerts without runbooks become shelfware in SIEM queues. Each class requires operational ownership, not only license purchase.

Feedback quality determines whether developers trust the stack. Findings should cite file, line, severity rationale, and a fix example when possible. Aggregating ten tools into one unreadable PDF recreates the waterfall audit experience inside CI. Platform teams should normalize output formats and route notifications to the same channels developers already monitor for test failures.

---

## Shift-Left, Paved Roads, and Golden Paths

Shift-left is often misread as "run every scanner in the IDE." That fails because many checks require built artifacts, shared services, or production-like data. The durable idea is to move **appropriate** feedback earlier, not to collapse the entire pipeline into a laptop.

The **paved road** (or golden path) complements shift-left by making the secure implementation the easiest implementation. A platform team publishes templates: service skeleton with parameterized queries, distroless base images, prewired scan stages, and deployment manifests that already satisfy pod security standards. Developers who copy the template inherit controls; developers who diverge document exceptions. Guardrails scale because they reduce decision fatigue; pure gates scale poorly because each gate becomes a negotiation.

Contrast **guardrails** with **gates**. Guardrails default to safe settings—build clusters that cannot pull unsigned images, namespaces that deny `runAsRoot: 0`, CI templates that fail on critical SCA findings for new code only. Gates block promotion until a human approves. Humans do not scale; guardrails do. Effective DevSecOps uses gates sparingly for high-impact decisions—production deploy freeze during incident, manual approval for regulated data stores—and uses guardrails for repeatable baselines.

Self-service secure templates also shorten the feedback loop for champions and reviewers. When the paved road includes example fixes for common scanner findings, developers learn patterns without waiting for office hours. The platform measures adoption by percentage of services spawned from templates versus bespoke manifests, not by how many tickets security closed.

Golden paths should include escape hatches with guardrails, not unlimited customization. Teams that need a nonstandard base image or privileged capability document risk acceptance, compensating controls, and expiry dates. That pattern prevents shadow IT while acknowledging that pure one-size-fits-all blocks legitimate edge cases. Platform engineering maintains the catalog of approved exceptions so auditors see deliberate decisions instead of silent drift.

Developer experience metrics belong beside security metrics. Track median time from finding to fix for pre-commit versus CI failures, survey whether feedback felt actionable, and watch bypass rates such as `--no-verify` commits or disabled pipeline jobs. Rising bypass rates signal that guardrails are too slow, too noisy, or poorly documented even when scanners technically run.

---

## Evaluating Security Posture and Lifecycle Gaps

To **evaluate** organizational **posture**, start from the lifecycle map above and ask, for each phase, whether you have automated evidence, assigned ownership, and measured outcomes—not whether you own a tool with a logo. A maturity conversation grounded in phases avoids shelfware: an unused enterprise scanner licensed for build stage counts as a gap even if spend looks impressive.

Workshop the assessment with engineering and product leaders using concrete questions. In plan, do features record threat models or data flows before implementation? In code, do all repositories enforce secret scanning and basic SAST on changed files? In build, do pipelines produce SBOMs and block critical vulnerabilities on new dependencies? In test, do deployed artifacts receive dynamic testing proportional to exposure? In deploy, do clusters enforce policy-as-code with audited exceptions? In operate, do runtime alerts route to on-call with runbooks? Missing affirmative answers are **gaps** to prioritize.

Score gaps by exploitability and exposure, not scanner severity alone. An informational finding on an internal batch job differs from a critical finding on an internet-facing authentication service. DevSecOps prioritization ties vulnerability management to service tiering and customer data classification rather than raw CVE counts.

Revisit the assessment quarterly. Tooling churn is handled in the landscape snapshot below; posture assessment focuses on capabilities—do we detect secrets before push, do we sign artifacts, do we enforce admission policy—regardless of which vendor implements them this year.

External benchmarks help calibrate internal scores without turning maturity into vanity. OWASP DSOMM and the DevSecOps Verification Standard provide activity checklists you can map to your lifecycle assessment, highlighting whether you merely run tools or verify outcomes. NIST SSDF practices offer language for executive reporting. Use frameworks as rubrics, not as certification shopping lists; the goal is gap visibility, not badge collection.

Red-team and bug bounty results should feed the same gap model. An external finding in production maps backward to missing controls exactly like an internal scanner finding does. When multiple escapes share a root cause—missing IaC scanning, absent mTLS between services—prioritize platform fixes over repeated one-off remediations. Posture evaluation converges with incident learning when teams treat every escape as evidence about lifecycle holes.

---

## Security Champion Programs

Central security teams cannot scale one-to-many review across every pull request in a growing engineering organization. **Security champion programs** distribute knowledge by embedding practitioners in each squad—usually senior developers or tech leads who receive extra training, office hours with security architects, and time allocation for enablement work.

Effective programs select champions for credibility and curiosity, not merely for availability. A champion who never writes code cannot influence code review norms. Executive sponsorship matters because champions need visible permission to slow risky releases when necessary and to spend sprint capacity on guardrail improvements.

Support structures separate champions from being unpaid security headcount. Provide playbooks, office hours, decision trees for common findings, and escalation paths for novel issues. Measure champions by enablement outcomes—reduced remediation time in their squad, increased paved-road adoption, fewer repeated finding types—not by raw count of bugs filed.

Champions bridge culture and tooling. They translate scanner output into idiomatic fixes for their stack, feed false positive feedback to platform teams, and capture local threats planning misses. When incident response occurs, champions accelerate context gathering because they already know how their service is built.

Rotate champions periodically to avoid burnout and single points of failure, but overlap rotations so institutional memory persists. Document decisions champions make so audits show distributed ownership rather than heroics.

Champions succeed when security engineering treats them as partners, not free labor. Provide monthly enablement sessions on new CVE classes, policy changes, and tooling updates. Give champions direct channels to prioritize false positive fixes in shared rule sets. Recognize their contributions in performance reviews so the role is career-positive rather than a tax on high performers.

At scale, coordinate champions through a lightweight guild: shared chat channel, office hours, and a rolling agenda of topics raised by squads. The guild surfaces systemic issues—confusing scanner messages, missing paved-road templates—to platform teams faster than individual tickets. Executives see a federated model that scales sublinearly with engineering headcount while preserving local context.

---

## Threat Modeling with STRIDE

Threat modeling is how DevSecOps connects planning to actionable controls. STRIDE—Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege—provides a durable checklist for discussing threats without requiring a proprietary methodology.

Lightweight continuous threat modeling fits agile delivery: a one-page diagram, data flow arrows, trust boundaries, and thirty minutes asking STRIDE questions per feature. Heavyweight up-front modeling still suits regulated launches or major architecture pivots, but waiting for a perfect diagram often means shipping without any model.

Each STRIDE category suggests mitigations you can trace to tool classes. Spoofing maps to authentication and mTLS; tampering to integrity controls and signed artifacts; repudiation to audit logging; information disclosure to encryption and secret management; denial of service to rate limiting and capacity planning; elevation of privilege to RBAC and admission policy. When a threat model entry links to a CI check or policy rule, you can prove the organization addressed it deliberately rather than accidentally.

Store models beside repositories or in ticket systems so reviewers see threats alongside code changes. Update models when data classifications change or when new external integrations appear. Threat models are living documents, not gate artifacts to discard after launch.

Connecting STRIDE to DevSecOps pipelines closes the loop between design intent and verification. When a model identifies spoofing risk on an internal API, the corresponding story adds mutual TLS or token validation checks in CI tests. Tampering risks map to signed commits and image verification jobs. Repudiation risks map to structured audit logs shipped to immutable storage. This traceability helps auditors and new engineers understand why specific scans exist instead of treating them as mysterious red bars.

Facilitation skills matter as much as frameworks. A threat modeling session that devolves into architecture redesign fails; one that produces three prioritized mitigations and owners succeeds. Timebox discussions, use whiteboard or diagram-as-code tools, and record outcomes in tickets linked to epics. Champions often facilitate these sessions because they understand both implementation constraints and security vocabulary.

---

## Measuring DevSecOps Progress

Measurement keeps DevSecOps honest. Executives hear "we bought scanners"; metrics reveal whether risk is falling. Durable indicators include **vulnerability escape rate**—critical or high findings discovered in production divided by total discovered—**mean time to remediate (MTTR)** stratified by severity, **pipeline coverage** percentage of build jobs running agreed tool classes, and **coverage of critical assets** defined by tiering policy.

Use metrics to incentivize learning, not blame. A rising scanner count after enabling SCA reflects improved visibility, not necessarily worsening security. Pair counts with remediation velocity: are new critical findings fixed within SLA? Are repeat finding types declining quarter over quarter? DORA research on delivery performance reminds us that elite teams deploy frequently **and** maintain stability; security metrics should move with delivery metrics, not against them.

Publish dashboards engineering managers already review. When security KPIs appear beside deployment frequency and change failure rate, tradeoffs become explicit rather than political. Avoid vanity metrics like total scans executed without reference to outcomes.

Set realistic baselines when enabling noisy tools. Legacy repositories may inherit thousands of historical findings; track "new code" hygiene separately from backlog burndown so teams do not disable tools to greenwash dashboards.

Slice metrics by service tier and team to avoid org-wide averages hiding hotspots. A low global escape rate means little if one tier-one payment service repeatedly escapes. Likewise, fast average MTTR may reflect quick fixes on low-severity noise while critical findings linger. Publish tier-specific SLAs and hold service owners accountable through existing operational review forums rather than creating parallel security bureaucracy.

Balance delivery and security using DORA-style thinking: frequent deployments should not require sacrificing change failure rate or recovery time. When security work lengthens lead time without reducing failures, revisit whether controls run at the wrong stage or produce low-value findings. Continuous improvement applies to the DevSecOps system itself, not only to application code.

---

## Supply Chain, SBOM, and Provenance (Introduction)

Software supply-chain security asks whether you trust the artifacts you deploy, not only the code you wrote. Two complementary ideas anchor modern practice: **SBOMs** enumerate what is inside a build, and **provenance** records how it was produced.

SBOM formats such as [SPDX](https://spdx.dev/specifications/) and [CycloneDX](https://cyclonedx.org/specification/overview/) standardize component lists so responders can answer "are we affected?" within hours of a new CVE. Generating SBOMs in CI is necessary but insufficient; teams must store, index, and query them during incidents.

Provenance and signing frameworks like [SLSA](https://slsa.dev/) define increasing levels of tamper resistance from scripted builds to hardened, auditable platforms. [Sigstore cosign](https://docs.sigstore.dev/cosign/signing/overview/) provides practical signing and verification patterns for container images and blobs. Admission policies can require valid signatures before workloads start.

SolarWinds-style compromise<!-- incident-xref: solarwinds-2020 --> and CI/CD pipeline abuse are covered in depth in [Security in CI/CD Pipelines](../module-4.3-security-cicd/); this module only establishes vocabulary so later lessons can go deep without redefining SBOM or provenance.

Treat SBOMs as operational data, not compliance PDFs. Index them by image digest and deployment environment so responders can query "where is log4j-core 2.x running?" within minutes. Pair SBOM storage with vulnerability feeds that re-evaluate components when new CVEs publish; otherwise the artifact is a snapshot that decays immediately after generation.

Signing without verification is theater. Clusters and registries must enforce signature policies at admission, and CI must verify third-party artifacts before bundling them. Start with internal images, expand to approved vendor bases, and document rotation procedures for signing keys using hardware or cloud KMS practices your organization already trusts.

---

## Landscape Snapshot — as of 2026-06

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

| Tool class | Example implementations | Notes |
|------------|-------------------------|-------|
| SAST | Semgrep, CodeQL, SonarQube | Rule packs vary by language; tune false positives per repo |
| SCA | Trivy, Grype, Snyk Open Source | Requires accurate lockfiles; monitor transitive depth |
| Secret scan | gitleaks, TruffleHog | Run on history when onboarding legacy repos |
| Image scan | Trivy, Clair | Scan at build and on registry admission |
| IaC scan | Checkov, tfsec, KICS | Complements cloud CSPM; catches pre-apply mistakes |
| Policy-as-code | OPA Gatekeeper, Kyverno | Kubernetes admission; Kyverno graduated CNCF March 2026 |
| Runtime | Falco, Tetragon | Falco is CNCF graduated; eBPF tools need kernel support |

### Security Tool Rosetta (capability view)

| Capability | Semgrep / CodeQL | Trivy / Grype | gitleaks | Checkov | OPA Gatekeeper / Kyverno | Falco |
|------------|------------------|---------------|----------|---------|--------------------------|-------|
| Finds vulnerable dependencies | partial via rules | primary | no | partial | no | no |
| Finds hardcoded secrets | partial | partial | primary | no | no | no |
| Finds misconfigured IaC | no | partial | no | primary | partial | no |
| Enforces deploy-time policy | no | no | no | no | primary | no |
| Detects runtime anomalies | no | no | no | no | no | primary |

Peers differ by integration depth, rule ecosystems, and operational cost—not by a universal ranking. Pick based on languages, platforms, and team skill, then verify maturity and features in vendor documentation before standardizing.

---

## Patterns & Anti-Patterns

### Patterns

**Paved-road service templates.** Platform teams publish secure-by-default repositories with scanning wired, examples for common fixes, and documentation embedded in the template README. Adoption metrics prove the pattern works when most new services start from the template without mandatory security review.

**Incremental scanner enablement on legacy code.** Establish baselines, block only new critical issues, and burndown historical debt on a schedule. This pattern prevents teams from disabling tools when first scans explode in count.

**Policy-as-code with exception workflow.** Policies live in Git; exceptions carry owners, expiry dates, and approvers. Auditors see transparency; developers see predictable rules instead of tribal knowledge.

### Anti-Patterns

**Scanner shopping without lifecycle mapping.** Buying five overlapping SAST products increases noise without closing phase gaps. Anti-pattern vendors love because it inflates licenses; organizations suffer alert fatigue.

**Breaking builds on day one for legacy debt.** Turning every informational finding into a hard fail guarantees bypass culture—developers disable jobs, fork pipelines, or stop upgrading tools.

**Security team as sole approver for every deploy.** Human gates do not scale with microservice counts and teach developers that security is someone else's job.

### Decision Framework: Where to Place a Control

| Question | If yes | Place control |
|----------|--------|---------------|
| Does it need source code without running the app? | SAST / secret scan | IDE, pre-commit, or CI on diff |
| Does it need a built artifact or lockfile? | SCA / image scan / SBOM | CI build stage |
| Does it need a running instance with test traffic? | DAST / IAST | CI test stage or staging |
| Must it hold for all clusters regardless of app code? | Policy-as-code | Admission webhook |
| Must it detect attacks on live traffic? | Runtime | Daemonset / eBPF / SIEM integration |

When two placements seem valid, prefer the earliest phase that provides trustworthy signal without blocking author flow. Re-evaluate quarterly as tests and environments mature.

---

## Did You Know?

- **DevSecOps grew from DevOps plus rugged software advocacy.** The Rugged Manifesto (2010) argued that resilient software must expect adversarial pressure; DevSecOps operationalizes that idea in pipelines and shared ownership rather than in a separate inspection phase.
- **NIST SSDF organizes practices into Prepare, Protect, Produce, Respond.** SP 800-218 gives federal-grade vocabulary for activities this module maps to CI/CD phases, useful when aligning platform engineering work with compliance frameworks.
- **The Equifax breach<!-- incident-xref: equifax-2017 --> accelerated industry focus on patch velocity and dependency risk.** Canonical narrative lives in prerequisite modules; the lesson for DevSecOps is that known-vulnerable components in production become board-level incidents regardless of functional test success.
- **Netflix open-sourced Security Monkey (2014)** to detect cloud misconfigurations automatically, an early example of continuous compliance monitoring that influenced later CSPM and GitOps audit patterns.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Treating DevSecOps as a tool purchase | Shelfware accumulates; culture unchanged | Map lifecycle gaps first; buy tools to close specific gaps |
| Running scanners without ownership | Findings age in backlogs | Assign squad-level owners and SLAs by severity |
| Breaking builds on all severities day one | Developers bypass or disable checks | Gate new critical issues; burndown legacy separately |
| Ignoring false positives | Trust erodes; tools silenced | Tune rules; suppress with documented rationale |
| Skipping threat modeling | Repeatable design flaws ship | Lightweight STRIDE on features touching sensitive data |
| No paved road | Every team reinvents insecure defaults | Publish templates with wired scans and policies |
| Measuring scans run, not outcomes | Activity theater | Track escape rate, MTTR, and repeat finding types |
| Central security as only approver | Bottleneck and adversarial dynamic | Champions plus automated guardrails; human gates for exceptions |

---

## Quiz

1. **Scenario:** Your organization deploys twenty times per day but performs security review only at quarterly audits. Vulnerabilities keep reappearing in pen tests. Which evaluation finding best describes the primary gap?

<details>
<summary>Answer</summary>

The primary gap is missing continuous security activity across the DevSecOps lifecycle, not lack of quarterly effort. Evaluating posture by phase reveals that plan, code, build, test, deploy, and operate stages lack automated controls and ownership, so defects accumulate faster than periodic audits can remediate. Quarterly reviews become surprise debt dumps that stall delivery and reinforce adversarial dynamics. Closing the gap requires phase-aligned automation, paved-road defaults, and metrics like escape rate—not longer audits alone.

</details>

2. **Scenario:** Leadership asks for a DevSecOps strategy for a Kubernetes platform with fifty microservices. Where should you recommend investing first?

<details>
<summary>Answer</summary>

Start with a lifecycle map: secret scanning and SCA in CI, image scanning on promoted artifacts, SBOM generation, and admission policy-as-code for baseline pod security. Design the strategy so each phase gains high-signal evidence before exotic tools. Pair technical controls with a champion program and paved-road templates so squads can adopt without central review of every pull request. Defer runtime-only investments until left-side gaps show diminishing returns, because runtime detection cannot replace prevention for classes like secrets in Git or known-vulnerable dependencies.

</details>

3. **Scenario:** A squad wants a "security champion" but expects them to review every pull request manually. How should you implement the program instead?

<details>
<summary>Answer</summary>

Champions enable guardrails—they do not replace automation or become human CI gates. Implement the program by selecting a credible developer, granting time for tooling feedback and threat-model facilitation, and connecting them to security architects for escalation. Measure success by reduced repeat findings, faster remediation, and paved-road adoption in their squad. Rotate roles to avoid burnout. Manual review of every change does not scale and misdefines the champion as a mini-CISO instead of a local enabler.

</details>

4. **Scenario:** A critical SQL injection flaw is found in production. The same pattern would have been caught by SAST in CI. How do you analyze remediation cost to justify shift-left spending?

<details>
<summary>Answer</summary>

Analyze cost by comparing the production remediation path—incident triage, hotfix, possible disclosure, emergency testing—against the hypothetical CI path where the author fixes the line before merge. Document the effort multiplier using your organization's incident records, even if dollar figures are estimates. Attribute the gap to a missing or bypassed code-stage control, then propose investment in IDE or CI SAST on changed files plus paved-road examples for parameterized queries. Executives fund shift-left when you show escape events are expensive and preventable controls are cheap relative to repeats.

</details>

5. **Why does SCA complement SAST rather than replace it?**

<details>
<summary>Answer</summary>

SAST analyzes code your team writes; SCA analyzes third-party components and licenses in your dependency graph. Modern services contain far more foreign code than authored code, so SAST alone cannot see Log4Shell-class vulnerabilities in transitive JARs or npm packages. Conversely, SCA cannot find bespoke SQL injection in your handlers. Together they cover composition risk and custom implementation risk. Pipeline design should run both at build stage with policies tuned to new dependency introductions.

</details>

6. **What distinguishes guardrails from gates in a DevSecOps platform?**

<details>
<summary>Answer</summary>

Guardrails make the secure path the default—templates, cluster policies, unsigned-image denial—while gates require human approval before progress. Guardrails scale with automation because they encode repeatable decisions; gates scale with headcount and calendar time. Effective platforms use guardrails for baselines and reserve gates for high-impact exceptions such as regulated data stores or incident freezes. Overusing gates recreates the waterfall security phase in DevOps clothing.

</details>

7. **Which metric best shows DevSecOps improvement rather than scanner activity?**

<details>
<summary>Answer</summary>

Vulnerability escape rate—critical or high findings first detected in production divided by total findings—shows whether left-side controls fail. Pair it with MTTR by severity and percentage of critical assets covered by agreed tool classes. Raw scan counts rise when visibility improves, so they are misleading alone. Improvement appears when escapes fall, remediation accelerates, and repeat finding types decline quarter over quarter.

</details>

---

## Hands-On

This exercise walks through the feedback loop a DevSecOps pipeline automates: detect issues in source and dependencies, remediate while context is fresh, and verify with a second scan pass. You will use SAST on application code and SCA on manifests — two tool classes that overlap in purpose but not in coverage — so you can explain why mature programs run both at build stage. Complete the steps on a workstation with Python 3 and network access to install packages; no Kubernetes cluster is required.

The sample deliberately mixes author-written flaws with outdated dependencies because real incidents often involve both. After fixing, map each original finding to the lifecycle stage where your organization would ideally block it: pre-commit for secrets, build for SCA, deploy for image policy. That mapping connects the lab to the strategy and posture sections above.

### Setup

```bash
mkdir devsecops-intro && cd devsecops-intro

cat > app.py << 'EOF'
import os
import sqlite3

DB_PASSWORD = "super_secret_123"
API_KEY = "sk_live_1234567890abcdef"

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()

def run_command(cmd):
    os.system(f"echo {cmd}")

if __name__ == "__main__":
    print(get_user(input("Enter user ID: ")))
EOF

cat > requirements.txt << 'EOF'
requests==2.25.0
pyyaml==5.3.1
urllib3==1.26.4
EOF
```

### Scan and fix

```bash
pip install bandit pip-audit
bandit -r . -f txt
pip-audit -r requirements.txt

cat > app_fixed.py << 'EOF'
import os
import sqlite3
import subprocess

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    query = "SELECT * FROM users WHERE id = ?"
    return conn.execute(query, (user_id,)).fetchone()

def run_command(cmd):
    allowed = ['date', 'whoami']
    if cmd in allowed:
        subprocess.run([cmd], check=True)

if __name__ == "__main__":
    _ = os.getenv("DB_PASSWORD")
    _ = os.getenv("API_KEY")
    print(get_user(input("Enter user ID: ")))
EOF

cat > requirements_fixed.txt << 'EOF'
requests>=2.31.0
pyyaml>=6.0.1
urllib3>=2.0.7
EOF

bandit -r app_fixed.py -f txt
pip-audit -r requirements_fixed.txt
```

Optional: install [Trivy](https://aquasecurity.github.io/trivy/) and run `trivy fs --severity HIGH,CRITICAL .` for combined secret and dependency signal. Trivy illustrates how one implementation can span multiple tool classes while dedicated tools sometimes offer deeper language-specific rules.

### Success criteria

- [ ] Bandit reports SQL injection, hardcoded secret, and shell-related findings on the original `app.py`
- [ ] pip-audit reports known CVEs on the pinned vulnerable requirements file
- [ ] Fixed code and dependencies produce clean or materially reduced findings on re-scan
- [ ] You can explain which DevSecOps lifecycle stage each tool class represents (SAST vs SCA)

---

## Sources

- [DevSecOps Manifesto](https://www.devsecops.org/)
- [OWASP DevSecOps Guideline](https://owasp.org/www-project-devsecops-guideline/)
- [OWASP DevSecOps Maturity Model (DSOMM)](https://owasp.org/www-project-devsecops-maturity-model/)
- [OWASP DevSecOps Verification Standard](https://owasp.org/www-project-devsecops-verification-standard/)
- [NIST SP 800-218 — Secure Software Development Framework (SSDF)](https://csrc.nist.gov/publications/detail/sp/800-218/final)
- [NIST SP 800-218 PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf)
- [CNCF Cloud Native Security Whitepaper](https://www.cncf.io/reports/cloud-native-security-whitepaper/)
- [SLSA — Supply-chain Levels for Software Artifacts](https://slsa.dev/)
- [Sigstore cosign signing overview](https://docs.sigstore.dev/cosign/signing/overview/)
- [CycloneDX specification overview](https://cyclonedx.org/specification/overview/)
- [SPDX specifications](https://spdx.dev/specifications/)
- [Semgrep documentation](https://semgrep.dev/docs/)
- [Trivy documentation](https://aquasecurity.github.io/trivy/)
- [Open Policy Agent documentation](https://www.openpolicyagent.org/docs/latest/)
- [OPA Gatekeeper project](https://github.com/open-policy-agent/gatekeeper)
- [Kyverno documentation](https://kyverno.io/docs/)
- [Falco documentation](https://falco.org/docs/)
- [CNCF Falco project](https://www.cncf.io/projects/falco/)
- [CNCF Open Policy Agent project](https://www.cncf.io/projects/open-policy-agent/)
- [CNCF Kyverno project](https://www.cncf.io/projects/kyverno/)
- [DORA — DevOps Research and Assessment](https://dora.dev/)

---

## Next Module

Continue to [Module 4.2: Shift-Left Security](../module-4.2-shift-left-security/) for concrete techniques that move security feedback earlier in the developer workflow.
