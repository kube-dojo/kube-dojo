---
title: "Module 3.7: Cloud Native Community & Collaboration"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.7-community-collaboration
sidebar:
  order: 8
revision_pending: false
---

# Module 3.7: Cloud Native Community & Collaboration

> **Complexity**: `[MEDIUM]` | **Time**: 45-60 minutes | **Prerequisites**: Modules 3.1-3.6, basic Kubernetes operations, and enough command-line comfort to inspect public repositories and run Kubernetes 1.35+ commands after introducing `alias k=kubectl` for the `k` alias.

## Learning Outcomes

After completing this module, you will be able to:

1. **Evaluate** CNCF governance decisions by tracing how the TOC, TAGs, SIGs, Working Groups, and maintainers share authority.
2. **Diagnose** whether a Kubernetes change needs a KEP, a SIG discussion, or an ordinary pull request before implementation begins.
3. **Design** a contributor plan that moves from observing to triage, pull requests, review, and project leadership.
4. **Compare** CNCF Sandbox, Incubating, and Graduated maturity levels when selecting production dependencies.

---

## Why This Module Matters

In December 2021, a critical vulnerability in a widely-used Java logging library — the full case study lives in [the supply-chain canonical](../../../../platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/) <!-- incident-xref: log4shell --> — turned into a global emergency for software teams running Java workloads. Security teams had to identify vulnerable components, platform teams had to patch shared clusters, and application owners had to rebuild images while attackers were already scanning the internet. The Kubernetes ecosystem was affected because controllers, operators, admission webhooks, dashboards, and supporting services could carry Java dependencies somewhere in their supply chain. Nobody could solve the incident from a private conference room because the affected software crossed company, cloud, and national boundaries.

What happened next showed why cloud native governance matters in practice. CNCF project maintainers, Kubernetes SIG contributors, security response teams, vendors, and end users coordinated in public issue trackers, Slack channels, mailing lists, and release notes. Guidance moved through the same community paths that handle ordinary features, but it moved quickly because people already knew where authority lived and how decisions were recorded. When a maintainer asked for testing on a patched controller, reviewers from another company could help immediately because the repository, roles, and review process were already open.

This module is about that operating system for trust. The CNCF is not just a logo on a website, and Kubernetes is not maintained by one invisible vendor team. The community uses layers of governance so a storage expert can influence storage design, a security engineer can challenge a risky default, and an end user can explain how an API behaves under production pressure. If you know how that system works, you can evaluate tools more carefully, escalate problems to the right place, and contribute without losing weeks in the wrong queue.

For the KCNA exam, community and collaboration topics often look softer than scheduling, networking, or storage. In real operations, they are just as concrete. The governance model determines whether a breaking API change is accepted, whether a project can survive the loss of one sponsor, and whether your team can safely depend on a tool for years. Treat this lesson as the map you use when the cloud native ecosystem stops being a product catalog and becomes a living system of people making technical decisions.

---

## CNCF Governance: Authority Without Vendor Control

The Cloud Native Computing Foundation is part of the Linux Foundation, but it does not operate like a single software company with a product manager assigning features to employees. Its job is to provide a neutral home for projects that need shared legal, trademark, event, security, and governance infrastructure. That neutrality matters because the cloud native ecosystem includes competitors who need to collaborate on the same standards while still competing in their commercial offerings. Without a foundation layer, every large contributor would worry that another vendor might quietly capture the direction of a project.

The CNCF governance model separates financial authority from technical authority. The Governing Board handles budget, legal, marketing, events, and membership concerns, while the Technical Oversight Committee, usually called the TOC, handles technical vision, project acceptance, maturity movement, and cross-project standards. That separation is the first pattern to notice because it prevents funding from automatically becoming architecture control. A company can sponsor events and employ many contributors, but it still has to win technical arguments in public.

Here is the original hierarchy from the module, preserved because it captures the separation visually:

```
CNCF GOVERNANCE HIERARCHY
================================================================

  ┌──────────────────────────────────────────────────────────┐
  │                  LINUX FOUNDATION                        │
  │              (parent organization)                       │
  └─────────────────────┬────────────────────────────────────┘
                        │
  ┌─────────────────────▼────────────────────────────────────┐
  │              CNCF GOVERNING BOARD                        │
  │         Budget, legal, marketing, events                 │
  │     (corporate members + community elected seats)        │
  └─────────────────────┬────────────────────────────────────┘
                        │
  ┌─────────────────────▼────────────────────────────────────┐
  │        TECHNICAL OVERSIGHT COMMITTEE (TOC)               │
  │     Technical vision, project acceptance, standards      │
  │           (11 elected community members)                 │
  └───────┬─────────────┬────────────────┬───────────────────┘
          │             │                │
   ┌──────▼──────┐ ┌───▼─────────┐ ┌────▼────────────┐
   │   TAGs      │ │  Projects   │ │  Working Groups │
   │ (Technical  │ │ (Sandbox →  │ │  (Cross-cutting │
   │  Advisory   │ │  Incubating │ │   topics like   │
   │  Groups)    │ │  → Graduated│ │   policy, CI)   │
   └─────────────┘ └─────────────┘ └─────────────────┘
```

Think of the CNCF as a city charter rather than a mayor who personally approves every building permit. The charter defines how neighborhoods can organize, how public records are kept, and how disputes move through legitimate channels. Each project is a neighborhood with its own maintainers, release process, and culture, while the foundation gives those neighborhoods a shared legal and operational base. That analogy explains why the CNCF can host Kubernetes, Prometheus, Envoy, Argo, and many smaller projects without pretending they are managed by one command chain.

Technical Advisory Groups, or TAGs, provide cross-project guidance in broad domains such as security, runtime, observability, and app delivery. A TAG usually does not own one repository in the way a project maintainer does. Instead, it helps the TOC evaluate proposals, documents shared practices, and connects experts who see the same problem appearing in many projects. When a cloud native concept spans more than one project, a TAG can help the ecosystem reason about it without forcing each project to invent separate vocabulary.

Working Groups are more focused and usually more temporary. They form around a problem that cuts across existing ownership boundaries, such as policy, conformance, or multi-tenancy. The important distinction is that a Working Group can gather people from multiple projects or SIGs without becoming the permanent owner of all resulting code. Once the problem is understood and ownership can move to the right maintainers, the Working Group may wind down or change shape.

Kubernetes adds another layer because it predates the CNCF. Google released Kubernetes as open source in 2014 and donated it to the newly formed CNCF in 2015, but the Kubernetes project has its own Steering Committee, SIGs, subprojects, OWNERS files, release team, and enhancement process. When someone says "the CNCF decided Kubernetes should do this," slow down and ask which body actually made the decision. Most Kubernetes technical direction comes from Kubernetes governance inside the CNCF umbrella, not from a foundation executive.

This distinction changes how you ask for help. If your question is about whether a project should move from Incubating to Graduated, the CNCF TOC and project maturity process are relevant. If your question is about a Kubernetes API behavior in Services, the right path probably starts with SIG Network, the relevant repository, and a Kubernetes Enhancement Proposal if the change is large enough. Correct routing is not etiquette theater; it keeps architectural questions in front of the people who own the technical contract.

Pause and predict: if two vendors fund the CNCF at different levels, should the larger sponsor get more power over whether Kubernetes changes the Pod API? The governance model says no, because technical authority is earned through community roles, documented review, and project ownership. That answer protects users as much as contributors. If sponsorship bought API control, every production cluster would inherit the priorities of the largest payer instead of the consensus of the maintainers responsible for compatibility.

This model is not perfect, and it does not eliminate politics. Large companies can still employ many maintainers, fund conference work, and dedicate engineers to long-running proposals that volunteers cannot match. The governance system reduces the risk by making decision records public, distributing authority across roles, and requiring evidence when projects claim maturity. A mature engineer does not assume openness magically creates fairness; they look for the process controls that make capture harder.

---

## Kubernetes SIGs, Working Groups, and KEPs

Kubernetes is too large for one committee to understand every technical tradeoff. Networking, storage, scheduling, security, node behavior, APIs, release engineering, documentation, and testing each have deep specialist knowledge. Special Interest Groups, usually called SIGs, divide that surface area into durable ownership zones. The result is a system where the people reviewing a storage migration are likely to understand storage failure modes, while the people reviewing a scheduling feature understand scheduler constraints and workload behavior.

The original SIG table is preserved here because it gives you the basic map:

| SIG | What They Own | Example Decisions |
|-----|---------------|-------------------|
| SIG Network | Networking, Services, DNS, Ingress | Gateway API design, IPv4/IPv6 dual-stack |
| SIG Storage | Persistent Volumes, CSI, storage classes | CSI migration from in-tree drivers |
| SIG Auth | Authentication, authorization, security policies | Pod Security Standards replacing PSPs |
| SIG Node | Kubelet, container runtime, node lifecycle | Containerd as default runtime |
| SIG Apps | Workload controllers (Deployments, StatefulSets) | Job indexing, pod failure policies |
| SIG Release | Release process, cadence, tooling | Three releases per year schedule |

A SIG is not just a chat room. It usually has chairs, technical leads, public meetings, notes, mailing lists, subprojects, and ownership files that describe who can review and approve changes in specific directories. Those roles matter because Kubernetes depends on sustained maintenance after the exciting design phase is over. A feature that lands without responsible owners becomes a support burden for every cluster administrator who later depends on it.

Working Groups differ because they are designed for cross-cutting problems. Imagine a multi-tenant security topic that touches NetworkPolicy, admission control, audit logging, storage isolation, and RBAC. No single SIG owns the entire problem, but several SIGs own pieces of the implementation. A Working Group can gather the right people, produce a shared design direction, and then hand durable ownership back to the permanent SIGs or subprojects.

The Kubernetes Enhancement Proposal process, usually shortened to KEP, is the mechanism that keeps significant changes from entering the project as surprise code. A KEP explains the problem, goals, non-goals, user impact, graduation criteria, test plan, alternatives, and rollout strategy before the project commits to implementation. This is slower than opening a pull request, but Kubernetes optimizes for compatibility across millions of clusters. Once a Kubernetes API reaches stable behavior, undoing a weak decision is expensive for users, vendors, client libraries, documentation, and certification material.

A useful mental model is that a KEP is the architectural review record for a change that users may depend on for years. It is not only permission to code, and it is not required for every small fix. It is the place where reviewers can ask whether the feature should exist, whether the API shape is durable, whether upgrades are safe, whether feature gates are needed, and whether conformance tests should protect behavior. The best KEPs make disagreement cheaper because the disagreement happens while the design is still editable.

The lifecycle usually moves from proposal to alpha, then beta, then stable. Alpha features are typically disabled by default and may change because the project is still learning from real use. Beta features are more widely available and enabled by default when the community has enough confidence, but they still retain feature-gate controls. Stable, often called GA, means the feature is part of the long-term API contract. That final step is intentionally difficult because stability is a promise to operators, vendors, documentation authors, and tool builders.

Before running this, what output do you expect if you only have a local Kubernetes 1.35+ client and no cluster context configured? The command can still show client information, but server information requires an accessible cluster. This small detail mirrors the community process: you can prepare locally, but meaningful validation often requires connecting to the shared system that will actually run the change.

```bash
alias k=kubectl
k version --client
```

The `k` alias is common in Kubernetes training because it keeps command examples short, but it should never hide the actual tool from a beginner. In this module, `k` means `kubectl`, and any command that inspects a cluster requires a valid kubeconfig context. Governance work often starts in GitHub and meeting notes rather than a terminal, but a contributor still needs enough operational skill to reproduce a bug or validate a proposed behavior against a real cluster.

A worked example makes the routing decision clearer. Suppose your platform team wants to change how Pods express a scheduling preference for a new class of workload. That touches API design, scheduler behavior, documentation, tests, and upgrade compatibility. The right path starts with SIG Scheduling discussion and likely a KEP, because the change affects Kubernetes API semantics and long-term user expectations. Opening a code-only pull request first would force reviewers to debate architecture inside a diff that cannot represent the full design space.

Now compare that to fixing a typo in the documentation for a scheduler flag. That change probably needs an ordinary pull request to the documentation repository, normal review, and no KEP. The skill is not memorizing which changes need paperwork. The skill is diagnosing blast radius. API changes, new features, feature gates, behavior changes, and cross-SIG work usually need a design record, while local fixes with no compatibility impact usually move through ordinary review.

Pause and predict: what would happen if Kubernetes accepted every useful API idea directly as stable because the initial implementation worked in one cluster? The project would collect incompatible assumptions faster than users could upgrade away from them. Cloud providers would implement behavior differently, client libraries would encode accidental semantics, and training material would become unreliable. The KEP process slows contributors down so the ecosystem does not push that cost onto operators later.

A practical war story appears in many large organizations during upgrades. A team discovers that a beta feature they adopted early behaves differently in the next release, then realizes the KEP and release notes described that possibility all along. The problem was not that Kubernetes broke a stable contract; the problem was that the team treated beta as finished. Reading the enhancement history teaches you which promises the project has made and which behaviors are still part of a learning loop.

---

## From Observer to Contributor

Every healthy open source project needs a path from outsider to trusted participant. Kubernetes and many CNCF projects use a ladder that starts with observation because context is part of the contribution. A new contributor who watches meetings, reads recent pull requests, and studies issue labels learns which problems are already debated, which maintainers are overloaded, and which norms shape review. That preparation makes the first contribution more likely to reduce work for maintainers instead of creating another vague item in the queue.

The first stage is observation. Join `slack.k8s.io`, watch a recorded SIG meeting, read meeting notes, and follow a few merged pull requests in the area you care about. This is not passive in the lazy sense. It is the same kind of preparation a good incident responder does before changing production: understand the system, identify the owners, and learn what evidence people trust.

The next stage is triage, and it is more valuable than beginners expect. Reproducing a bug, adding exact Kubernetes versions, attaching logs, narrowing a failing case, or confirming that an issue is stale saves maintainer time. In many projects, the fastest way to become known is not to submit a clever feature but to make existing issues easier to act on. Maintainers remember contributors who reduce uncertainty.

Small pull requests come after that foundation. Documentation fixes, test improvements, clearer examples, and narrow bug fixes teach the review workflow without forcing the contributor to defend a broad design. They also reveal whether the contributor responds well to feedback. In open source, technical skill matters, but so does the ability to keep a review moving when someone asks for changes.

Sustained contribution turns occasional help into project trust. Kubernetes uses roles such as Member, Reviewer, and Approver, with authority usually scoped to repositories or directories through OWNERS files. A Reviewer is trusted to evaluate changes in an area, while an Approver can approve merges for owned code. These roles are not honorary badges. They are operational controls that let a huge project merge changes without centralizing every decision in one group.

Leadership comes later and is built from reliability. SIG chairs, technical leads, release leads, and subproject owners carry coordination work that is often less glamorous than writing code. They run meetings, document decisions, handle disagreement, mentor contributors, and keep project health visible. A project without this labor can have brilliant code and still fail because no one can tell where decisions are made.

Which approach would you choose here and why: spending your first week opening three small documentation pull requests, or spending it reading SIG notes and reproducing one active bug with high-quality evidence? Either can be useful, but the better choice depends on what the project needs and what you can validate. If maintainers are drowning in unclear issues, a strong reproduction may have more impact than a drive-by text fix.

Good bug reports have a predictable shape. They include the Kubernetes version, environment, exact steps, expected behavior, actual behavior, relevant logs, and whether the issue reproduces on a supported release. Good pull requests explain what changed and why, include tests or docs when appropriate, and respond to review comments without disappearing. Good reviews are specific, respectful, and evidence-based; they explain risk rather than merely stating preference, which helps maintainers distinguish taste from compatibility concern.

The social side is not a substitute for technical rigor. Being friendly in Slack does not earn approval rights if your reviews miss regressions, and being technically sharp does not help if your comments make collaboration harder. The best contributors combine both forms of discipline. They make it easier for the project to accept change safely.

For a platform engineer, contributor skills also improve day-to-day operations. When an outage exposes a confusing Kubernetes behavior, you can read the relevant KEP, find the owning SIG, inspect recent issues, and ask a precise question in the right channel. Even if you never become a maintainer, that navigation skill shortens the distance between a production problem and the people who understand the upstream design.

---

## CNCF Project Maturity and Production Risk

The CNCF Landscape can be overwhelming because it maps far more than the set of official CNCF projects. Seeing a tool on landscape.cncf.io does not automatically mean it is a graduated project, a security-audited dependency, or a safe default for your production cluster. The landscape is a map of the ecosystem, not a blanket endorsement. A careful engineer treats it as a discovery tool and then checks maturity, governance, adoption, security posture, and maintainer diversity.

The original maturity table is preserved here because it is the core KCNA comparison:

| Level | What It Means | Requirements | Examples |
|-------|--------------|--------------|----------|
| **Sandbox** | Early stage, experimental | TOC sponsor, clear scope | Backstage (early), OpenKruise |
| **Incubating** | Growing adoption, maturing governance | Healthy contributor base, used in production | Kyverno, Cilium (before graduation) |
| **Graduated** | Production-ready, proven governance | Independent security audit, diverse maintainers | Kubernetes, Prometheus, Envoy, Argo |

Sandbox is the entry point for early projects that need a neutral home and room to collaborate. A Sandbox project may be promising, but the stage does not prove production readiness. It tells you the project has a defined scope and a path into the foundation. For a critical dependency, that is only the beginning of your evaluation, not the end.

Incubating projects have more evidence behind them. They should show growing adoption, a healthier contributor base, clearer governance, and signs that production users are depending on them. Incubating does not mean risk-free. It means the project is moving beyond experiment into serious adoption, while still proving that its governance and maintenance model can scale.

Graduated projects have cleared the CNCF's highest maturity bar. Graduation requires stronger evidence, including diverse maintainers, documented governance, production adoption, and an independent security audit. This does not mean a Graduated project has no bugs. It means the project has demonstrated enough governance, security, and operational maturity that organizations can treat it as a more dependable foundation for critical systems.

Maturity level is most useful when combined with workload risk. A Sandbox observability experiment might be acceptable in a lab cluster or a non-critical internal platform where your team can tolerate churn. A service mesh, policy engine, or runtime component used in regulated financial workloads demands a higher bar because failure affects security and availability. The maturity model gives you a starting signal for that risk conversation.

The CNCF landscape is deliberately broad because cloud native work spans build systems, registries, runtimes, scheduling, policy, networking, observability, and application delivery. That breadth is useful, but it can trick teams into equating visibility with endorsement. The better question is not "Is it on the landscape?" but "What evidence supports using it for this workload, and what risk would we own if the project slowed down?" That framing turns the landscape from a logo wall into the first step of a dependency review.

A real decision might look like this. Your team is choosing a policy engine for admission control in clusters that host regulated workloads. One project is Graduated, has an audit, and has fewer features. Another is Sandbox, has attractive integrations, and is moving quickly. For a production control plane dependency, the Graduated project usually deserves the first evaluation because governance and security evidence matter more than feature count. The Sandbox project may still belong in a proof of concept where the cost of change is low.

Project maturity also affects your support plan. With a Graduated project, you can expect a more mature release process, clearer security reporting, and broader community knowledge. With a Sandbox project, you may need to allocate engineering time for reading source code, testing upgrades, and handling breaking changes. Neither choice is morally superior. The mistake is pretending both choices carry the same operational risk.

The maturity model is therefore a decision aid, not a procurement shortcut. A responsible platform team still validates documentation quality, release cadence, maintainer responsiveness, security policy, compatibility with Kubernetes 1.35+, and fit for its own architecture. CNCF maturity tells you how much evidence the project has presented to the foundation. Your environment still decides whether that evidence is enough.

---

## Reading Community Signals Like an Operator

Community health is not a vague feeling. You can inspect it the same way you inspect cluster health: look for owners, queues, stale work, release cadence, security response paths, and clear escalation routes. A project with beautiful documentation but no active reviewers may create more risk than a project with rougher docs and a responsive maintainer base. The operational question is whether the project can absorb change and support users over time.

Start with the repository. Look for `GOVERNANCE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `OWNERS`, `MAINTAINERS.md`, release notes, and issue labels. These files tell you how work enters the project, who can approve it, how vulnerabilities are reported, and whether new contributors have a documented path. Missing files are not an automatic rejection, but they increase the amount of judgment you must apply.

Then inspect recent activity. A project with many open pull requests and no maintainer responses may be overloaded. A project with regular releases, reviewed changes, and clear issue triage has stronger evidence of operational health. Be careful with raw GitHub stars because they measure attention more than reliability. For production dependencies, reviewed releases and governance clarity beat popularity.

Meeting notes and Slack channels add context that repository metrics cannot show. A SIG may have a slow week because maintainers are preparing a release, resolving a design dispute, or waiting on upstream dependency work. Public notes help you tell the difference between temporary quiet and abandoned ownership. That is why watching SIG meetings is useful even for people who never intend to speak in them.

For Kubernetes features, the KEP repository is one of the best places to read intent. A KEP's README often explains goals, non-goals, alternatives, risks, graduation criteria, and test plans. The `kep.yaml` file identifies ownership and stage information. When documentation says a behavior exists, the KEP can explain why it exists, which alternatives were rejected, and what conditions must be met before the feature progresses.

The release process is another signal. Kubernetes ships on a regular cadence, and SIG Release coordinates the work required to branch, test, document, and publish each release. That cadence forces feature teams to meet deadlines for enhancement freeze, code freeze, docs, and test readiness. The process can feel strict, but it protects downstream users who need predictable upgrade planning.

Community signals are especially important during incidents. If a project has a public security policy, active maintainers across more than one employer, and a documented release process, your team has somewhere to go when a vulnerability appears. If a project depends on one person, one vendor, and one private roadmap, you may still use it, but you should record that concentration as a business risk. Governance is part of supply chain security because people are the supply chain.

This is where collaboration becomes an engineering practice rather than a slogan. When you file an issue with reproduction steps, attend a SIG meeting with a concise question, or test an alpha feature and report edge cases, you are improving the information the project uses to make decisions. The upstream community gets better evidence, and your organization gets earlier visibility into changes that may affect production.

---

## Patterns & Anti-Patterns

Patterns and anti-patterns help turn community knowledge into repeatable engineering behavior. In this topic, the risky moves are rarely dramatic. They are usually small shortcuts: treating a landscape entry as an endorsement, skipping the KEP because the code seems obvious, or asking a broad question in the wrong venue. The better patterns make work visible, route decisions to the right owners, and preserve evidence for future operators.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Start with governance files | Evaluating a dependency or joining a project | Shows who owns decisions, reviews, releases, and security response | Automate checks for these files in internal dependency reviews |
| Route by ownership area | Proposing Kubernetes changes or asking technical questions | Gets the issue to the SIG or project maintainers who can act | Maintain an internal map from platform components to upstream groups |
| Write design before code | Changing APIs, feature gates, or cross-SIG behavior | Makes tradeoffs visible before implementation inertia builds | Use KEPs or lightweight design docs depending on blast radius |
| Treat maturity as risk evidence | Choosing between CNCF projects for production | Connects governance maturity to operational confidence | Pair maturity level with workload criticality and security requirements |

The first pattern is to inspect governance before you inspect features. Feature lists are attractive because they map directly to immediate needs, but governance determines whether the feature will still be maintained after the original excitement fades. A project with clear reviewers, a security policy, and recent releases gives you stronger evidence than a project with many integrations and no visible ownership. This pattern scales well when platform teams standardize dependency intake.

The second pattern is to route by ownership. If your question involves Kubernetes networking behavior, start with SIG Network materials instead of sending a broad message to a general channel. If your concern involves CNCF project maturity, read the TOC process and project proposal history. Good routing is not just politeness. It reduces noise for volunteers and increases the chance that your question reaches someone with authority to answer.

The third pattern is to write the design before defending the code. For large changes, an implementation can hide unresolved policy choices, upgrade risks, and compatibility questions. A KEP or design document forces those questions into the open while the solution is still flexible. This pattern is slower at the start and faster over the full lifetime of the change because reviewers are not discovering fundamental disagreements after hundreds of lines already exist.

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|--------------|-----------------|------------------------|--------------------|
| Logo-driven adoption | Teams assume CNCF visibility equals production fitness | The landscape page looks official and comprehensive | Check maturity, governance files, releases, and security policy |
| Code-first feature proposals | Review stalls because architecture questions are unresolved | Engineers want to show a working implementation quickly | Discuss in the owning SIG and draft a KEP when blast radius is high |
| Drive-by issue escalation | Maintainers receive vague urgency without reproducible evidence | Production pressure makes teams skip preparation | Provide version, environment, logs, reproduction, and expected behavior |
| Single-vendor dependency blindness | A tool becomes risky when its sponsor changes priorities | The project solves today's problem well | Track maintainer diversity and plan exit or support options |

Logo-driven adoption is common because the CNCF brand is strong. The better habit is to separate three questions: is the tool in the cloud native ecosystem, is it an official CNCF project, and what maturity level has it reached? Those questions produce different answers. A tool can appear in the landscape without being a Graduated CNCF project, and a Sandbox project can be valuable without being the right dependency for your most critical control plane path.

Code-first feature proposals are common among skilled engineers because working code feels persuasive. In Kubernetes, working code is not enough when the change creates a contract for millions of users. The implementation may prove feasibility, but the KEP proves that the community has considered goals, non-goals, alternatives, rollout, tests, and compatibility. The better alternative is to use prototypes as evidence inside the design process rather than as a replacement for it.

Drive-by escalation happens during real outages. A team arrives in Slack and says the project is broken, but provides no version, logs, reproduction, or environment. Maintainers then have to spend their limited time extracting basics before they can help. A better report says what version is running, what changed, what behavior was expected, what happened instead, and which evidence supports the claim. That report respects the community's time and usually gets a better answer.

---

## Decision Framework

Use this framework when you need to decide where a community question, feature idea, or dependency evaluation belongs. The goal is not to memorize every CNCF and Kubernetes body. The goal is to reduce ambiguity by asking what kind of decision you are making, who owns that surface area, and how much long-term risk the decision creates. Good community navigation starts by classifying the problem.

| Situation | Primary Question | Best First Stop | Escalate When | Decision Risk |
|-----------|------------------|-----------------|---------------|---------------|
| Kubernetes API or behavior change | Does this affect user-facing contracts? | Owning SIG and KEP repository | Multiple SIGs or compatibility concerns appear | High |
| CNCF project adoption | Is the project mature enough for this workload? | CNCF project page and governance files | Security, maintainer diversity, or release health is unclear | Medium to high |
| Cross-cutting best practice | Does the topic span several owners? | TAG or Working Group materials | No single project can own the outcome | Medium |
| Small bug or documentation fix | Is the change local and testable? | Issue tracker and ordinary pull request | Review reveals broader design implications | Low to medium |

Start with blast radius. If a change affects a stable API, default behavior, upgrade compatibility, conformance, or more than one SIG, assume it needs public design discussion before code. If a change is local, reversible, and covered by an existing owner path, an ordinary pull request may be enough. This first branch prevents both extremes: drowning simple fixes in process and sneaking durable contracts through routine review.

Then identify the owner. In Kubernetes, ownership usually means the relevant SIG, subproject, and OWNERS file. In CNCF project maturity, ownership usually means project maintainers, TOC process, and documented governance. In cross-project topics, ownership may begin with a TAG or Working Group. If you cannot find an owner, treat that as a signal. A dependency with unclear ownership may be a risky dependency even if the code currently works.

Next, choose the evidence you need. For a KEP, evidence includes problem statements, alternatives, graduation criteria, tests, and compatibility analysis. For a dependency, evidence includes maturity level, release cadence, security policy, maintainer diversity, and production adoption. For a bug report, evidence includes reproduction steps, versions, environment, logs, and expected behavior. The right evidence makes collaboration faster because reviewers are not forced to guess.

Finally, decide how much uncertainty you can tolerate. A learning cluster can accept experimental tools and alpha features because the cost of change is low. A regulated production environment should prefer stable Kubernetes features and higher-maturity dependencies because the cost of surprise is high. This is the same engineering tradeoff you make with any system: innovation has value, but reliability has a price that must be paid before the incident.

Here is a compact flow for routing a Kubernetes change. If it changes a user-facing API or long-term behavior, talk to the owning SIG and expect a KEP. If it spans several ownership areas, involve the affected SIGs and look for a Working Group or broader design discussion. If it is a narrow fix, use the issue tracker and pull request workflow. If review reveals larger consequences, move the conversation back to design before merging.

For tool adoption, invert the flow. Start with the workload's criticality, then check CNCF maturity, then inspect community health. A Sandbox project can be the right choice when you need early innovation and can handle churn. A Graduated project is usually the safer default when the component becomes a platform dependency that many teams will inherit.

---

## Did You Know?

1. **Kubernetes has over 3,200 individual contributors** from more than 80 countries. No single company contributes more than 25% of the code, by design.

2. **The first Kubernetes commit was on June 6, 2014.** It was open-sourced by Google just one year later and donated to the newly formed CNCF in 2015, one of the fastest paths from internal tool to community-governed project in infrastructure history.

3. **KEP-4222 introduced CBOR serialization work through the public enhancement process.** The long review path exposed compatibility and client behavior concerns that would have been much harder to fix after a stable API promise.

4. **The CNCF End User Technical Advisory Board includes production engineers from major end-user organizations.** Its purpose is to keep foundation decisions connected to real operating needs, not only vendor roadmaps.

---

## Common Mistakes

Community mistakes often look harmless because they happen before code reaches production. A vague issue, a skipped design discussion, or a shallow maturity review can still create operational cost months later. Use this table as a checklist when your team interacts with upstream projects or evaluates cloud native dependencies.

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Opening a large PR without a KEP | Eager to contribute, unaware of process | Check if your change needs a KEP. Any API change or new feature likely does. |
| Asking questions already answered in docs | Enthusiasm outruns preparation | Read the contributor guide, CONTRIBUTING.md, and search Slack history first. |
| Equating CNCF membership with endorsement | The landscape is large and confusing | Check the maturity level. Sandbox is experimental, not "CNCF-approved for production." |
| Ignoring reviewer feedback on a PR | Feeling defensive about code | Reviews are collaborative. Respond to every comment, even if just to acknowledge it. |
| Assuming one company controls Kubernetes | Brand association, because Google created it | Look at contributor stats, SIG ownership, and Kubernetes governance records. |
| Treating SIG meetings as optional spectating | Not realizing decisions happen there | SIG meetings are where work is assigned and designs are debated. Attend to participate. |
| Choosing a Sandbox project for a critical path without a risk plan | Feature pressure outruns governance review | Pilot it first, track release and security signals, and define an exit strategy. |
| Filing urgent issues without reproduction details | Incident pressure compresses communication | Include versions, environment, logs, expected behavior, actual behavior, and exact steps. |

---

## Quiz: Test Your Understanding

Each question below is scenario-based because community collaboration is a decision skill. Read the situation, decide where the work belongs, and then open the answer to compare your reasoning with the governance model.

<details><summary>Question 1: A new engineer wants to add a feature that changes the Kubernetes API for Pod scheduling. They open a pull request directly with the code. What will likely happen, and what should they have done instead?</summary>

The PR will probably be paused or redirected because a user-facing Kubernetes API change needs design review before implementation. The engineer should start with the owning SIG, likely SIG Scheduling, and prepare a KEP that explains the problem, goals, alternatives, risks, tests, and graduation path. This is not bureaucracy for its own sake. It protects millions of users from inheriting an API contract that the community has not reviewed for compatibility.
</details>

<details><summary>Question 2: Your company is evaluating two CNCF projects for service mesh. Project A is Graduated and Project B is Sandbox but has more features. Your manager asks which to choose for a production deployment handling financial transactions. What factors from the CNCF maturity model should inform this decision?</summary>

The Graduated project has stronger maturity evidence, including governance, production adoption, maintainer diversity, and an independent security audit requirement. The Sandbox project may still be valuable, but its maturity level signals higher uncertainty and a greater need for internal validation. For financial transactions, reliability, security response, and long-term maintainability matter more than feature count. A reasonable plan is to evaluate the Sandbox project in a non-critical environment while favoring the Graduated option for the production control path.
</details>

<details><summary>Question 3: A contributor has been actively fixing bugs in SIG Network for six months. They want to become a Reviewer so their approvals carry more weight. Who grants this status, and what are they evaluating?</summary>

Reviewer status is granted through Kubernetes project ownership, usually by the relevant SIG or subproject leads following the contributor ladder and OWNERS process. They evaluate sustained contribution, review quality, technical judgment, responsiveness, and familiarity with the owned area. The contributor's employer is less important than the evidence of reliable project work. This structure lets authority scale without handing control to a single company.
</details>

<details><summary>Question 4: During a SIG meeting, two major cloud providers disagree on the design of a new storage feature. One provider threatens to fork the feature if its approach is not accepted. How does governance reduce the risk of vendor capture?</summary>

The SIG and KEP process require technical proposals to document alternatives, tradeoffs, compatibility risks, and review feedback in public. Decisions are supposed to be made by project owners on technical merit, not by sponsor size or commercial pressure. A vendor can fork code, but it then carries the cost of maintaining a divergent path outside the shared community. Public governance makes compromise more attractive than private control because the shared project retains maintainers, tests, users, and ecosystem trust.
</details>

<details><summary>Question 5: You notice that a popular tool appears on the CNCF Landscape website. Your team assumes this means the CNCF has vetted it for production use. Is this assumption correct?</summary>

The assumption is not correct. The CNCF Landscape is a broad map of the cloud native ecosystem, and not every entry has the same relationship to the foundation. Even official CNCF projects differ by maturity stage, with Sandbox, Incubating, and Graduated carrying different evidence levels. Your team should check whether the tool is an official project, what maturity stage it has reached, and whether its governance, releases, and security policy match your workload risk.
</details>

<details><summary>Question 6: Your team is building a new open-source Kubernetes cost optimization tool and wants a neutral home for cross-company collaboration. What maturity level must it apply for first, and what is the main goal of that stage?</summary>

The project should apply for the Sandbox stage first. Sandbox gives early projects a neutral home, a clear scope, and a path for collaboration without implying production readiness. The goal is to encourage open development and community formation while the project proves its governance and usefulness. It is an entry point, not a guarantee that the project will graduate.
</details>

<details><summary>Question 7: An organization mandates that critical infrastructure components must have completed an independent third-party security audit. Which CNCF maturity tier automatically aligns with that specific requirement?</summary>

The Graduated tier aligns with that requirement because independent security audit completion is part of the CNCF graduation bar. Incubating and Sandbox projects may be widely used, but they do not automatically carry the same maturity evidence. The reason this requirement appears at the highest tier is that Graduated projects are expected to support broad, mission-critical production use. Your organization should still read the audit and release history, but the maturity tier gives a strong starting signal.
</details>

<details><summary>Question 8: A platform team wants to define best practices for multi-tenant cluster security across networking, storage, and authentication. There is no single permanent SIG for the whole topic. Where should they start, and how does that group differ from a SIG?</summary>

They should look for a relevant Working Group or TAG activity and then identify the affected SIGs for implementation ownership. A Working Group is useful for a cross-cutting problem because it can gather people from several areas without becoming the permanent owner of every resulting code path. A SIG usually owns a durable area of the Kubernetes project, such as networking or authentication. The Working Group can coordinate shared guidance while long-term code ownership remains with the responsible SIGs and subprojects.
</details>

---

## Hands-On Exercise: Navigating CNCF Governance and KEPs

This exercise asks you to navigate the same public materials that platform engineers use when evaluating tools and tracking Kubernetes changes. You do not need a cluster for the research steps, but you should still use the `k` alias convention if you validate any Kubernetes 1.35+ examples locally. The goal is to practice evidence gathering, not to memorize website locations.

### Step 1: Analyze the CNCF Landscape

Navigate to the official CNCF Landscape at landscape.cncf.io and filter projects by maturity level. Your task is to separate ecosystem visibility from maturity evidence, then record what you would tell a production platform review board. Do not stop when you find a familiar logo; inspect the project page and look for governance, release, and security signals.

- [ ] Open the CNCF Landscape in your web browser.
- [ ] Filter the view to show only **Graduated** projects and identify three distinct projects related to "Observability and Analysis."
- [ ] Clear your filters, then filter the view to show only **Sandbox** projects and find one project that joined the foundation recently.
- [ ] Locate the GitHub repository or official documentation for one Graduated project and verify its governance structure in a `GOVERNANCE.md`, `CODE_OF_CONDUCT.md`, `OWNERS`, or `MAINTAINERS.md` file.

<details><summary>Solution guidance for Step 1</summary>

A strong answer names the projects, their maturity level, the category where you found them, and the governance evidence you inspected. For example, you might identify a Graduated observability project, open its repository, and record the files that explain maintainers, conduct, releases, or security reporting. The important part is not choosing the most famous project. The important part is showing that maturity and governance were verified instead of assumed from the landscape entry.
</details>

### Step 2: Investigate a Kubernetes Enhancement Proposal

Navigate to the official Kubernetes Enhancements repository at `github.com/kubernetes/enhancements/tree/master/keps` and trace one feature from ownership to maturity. Treat the KEP as a design record. You are looking for the owning SIG, the reviewers, the stage, the alternatives, and the evidence required before the feature can move forward.

- [ ] Open the `keps` directory and select a specific SIG folder that interests you, such as `sig-network`, `sig-auth`, or `sig-scheduling`.
- [ ] Choose a KEP that is currently in the `implemented` or `implementable` state and open its `kep.yaml` file.
- [ ] Identify the owning SIG, participating reviewers, approvers, and the milestone or stage targeted by the KEP.
- [ ] Locate the "Alternatives" section in the KEP's `README.md` and identify at least one technical approach that the authors considered but rejected.
- [ ] Review the `OWNERS` file in the KEP's directory or parent area to identify who has approval authority for that proposal.

<details><summary>Solution guidance for Step 2</summary>

A strong answer connects the KEP to a real owner and explains why an alternative was rejected. If the KEP is alpha, beta, or stable, note what evidence the proposal says is required for the next stage. If the proposal lacks the information you expected, record that too because incomplete design records are part of real-world evaluation. The goal is to practice reading intent and ownership, not only to copy field names from `kep.yaml`.
</details>

### Step 3: Build a Contributor Entry Plan

Choose one Kubernetes SIG or CNCF project that matches your interests, then design a two-week contributor entry plan. The plan should begin with observation and end with one concrete action that reduces maintainer workload. Keep the plan realistic. A good first action is often reproducing an issue, improving unclear documentation, or adding missing test evidence.

- [ ] Join or inspect the public communication channel for the project, such as `slack.k8s.io`, mailing lists, meeting notes, or GitHub Discussions.
- [ ] Read three recently merged pull requests and write down what reviewers consistently ask contributors to provide.
- [ ] Find one `good-first-issue`, `help-wanted`, or documentation issue and assess whether you can reproduce or clarify it.
- [ ] Draft a short issue comment or pull request plan that includes evidence, expected behavior, and the smallest useful contribution.

<details><summary>Solution guidance for Step 3</summary>

A strong plan is specific enough that another engineer could follow it. It names the SIG or project, the communication path, the issue or documentation area, and the evidence you will provide. Avoid plans that say only "contribute to Kubernetes" because they do not reduce maintainer workload. The best first contribution makes an existing decision easier for someone who already owns the area.
</details>

### Step 4: Validate Your Local Vocabulary

This final step is intentionally small. If you have a Kubernetes 1.35+ client installed, configure the `k` alias and verify that your local client is available. If you do not have a cluster, do not invent one; record that only client validation was possible. Clear reporting is part of good community collaboration.

- [ ] Run `alias k=kubectl` in your shell session.
- [ ] Run `k version --client` and record the client version.
- [ ] If you have a cluster context, run `k cluster-info` and record the server endpoint category without exposing private URLs.
- [ ] Write one sentence explaining which upstream community venue you would use if the command revealed a Kubernetes client or server bug.

<details><summary>Solution guidance for Step 4</summary>

If only the client command works, your result is still valid because the exercise is about honest evidence. Record the client version and explain that server validation requires a configured cluster. If a real bug appears, route it by ownership: client behavior may begin in the relevant Kubernetes repository issue tracker, while feature behavior should be checked against the owning SIG and any related KEP. Do not paste private cluster URLs into public issues.
</details>

### Success Criteria

- [ ] You distinguished CNCF Landscape visibility from CNCF project maturity.
- [ ] You identified one Graduated project's governance evidence.
- [ ] You traced one KEP to its owning SIG, reviewers, stage, and rejected alternative.
- [ ] You designed a realistic contributor entry plan that starts with observation.
- [ ] You used or documented the `k` alias convention for Kubernetes 1.35+ command examples.
- [ ] You can explain whether your chosen change needs a KEP, SIG discussion, or ordinary pull request.

---

## Sources

- [Cloud Native Computing Foundation](https://www.cncf.io/)
- [CNCF Projects](https://www.cncf.io/projects/)
- [CNCF Landscape](https://landscape.cncf.io/)
- [CNCF TOC Repository](https://github.com/cncf/toc)
- [CNCF Project Proposal Process](https://github.com/cncf/toc/blob/main/process/project_proposals.adoc)
- [CNCF Graduation Criteria](https://github.com/cncf/toc/blob/main/process/graduation_criteria.adoc)
- [Kubernetes Community Repository](https://github.com/kubernetes/community)
- [Kubernetes SIG List](https://github.com/kubernetes/community/tree/master/sig-list.md)
- [Kubernetes Contributor Guide](https://github.com/kubernetes/community/blob/master/contributors/guide/README.md)
- [Kubernetes Enhancements KEP Directory](https://github.com/kubernetes/enhancements/tree/master/keps)
- [Kubernetes Enhancement Process README](https://github.com/kubernetes/enhancements/blob/master/keps/README.md)
- [Kubernetes Slack Signup](https://slack.k8s.io/)

## Next Module

**Next Module**: [Module 3.8: AI/ML in Cloud Native](/k8s/kcna/part3-cloud-native-architecture/module-3.8-ai-ml-cloud-native/) introduces how machine learning workloads fit into cloud native architecture and what operational constraints they add.
