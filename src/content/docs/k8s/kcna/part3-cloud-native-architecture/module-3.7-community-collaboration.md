---
title: "Module 3.7: Cloud Native Community & Collaboration"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.7-community-collaboration
sidebar:
  order: 8
---

> **Complexity**: `[MEDIUM]` | **Time**: 30-40 minutes | **Prerequisites**: Modules 3.1-3.6 (Cloud Native Architecture)

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the CNCF governance model including the TOC, SIGs, and Working Groups
2. **Trace** how a feature moves from KEP proposal to shipped release in Kubernetes
3. **Identify** the path from observer to contributor in CNCF projects
4. **Compare** project maturity stages and the criteria for sandbox, incubating, and graduated status

---

## Why This Module Matters

In December 2021, a critical vulnerability in the Apache Log4j library (CVE-2021-44228) sent shockwaves through the entire software industry. Millions of applications were at risk. The Kubernetes ecosystem was no exception -- projects like Elasticsearch operators, Kafka connectors, and Java-based controllers all needed urgent patches.

What happened next was remarkable. Within 48 hours, CNCF project maintainers across dozens of time zones coordinated responses. SIG Security issued guidance. Upstream patches landed through the standard KEP and PR process -- not through some corporate emergency channel, but through the same open governance model that handles routine feature work. Contributors who had never spoken to each other before reviewed, tested, and merged fixes because the process was transparent and the authority structure was clear.

This was not luck. It was the result of a governance model deliberately designed to scale trust across thousands of strangers. If you work with cloud native technology -- even if you never submit a single pull request -- understanding how this community operates will change how you consume its output. You will know where decisions are made, how to influence them, and how to get help when something breaks.

---

## What You'll Learn

- How the CNCF governance model works, from the TOC down to individual maintainers
- How SIGs, Working Groups, and KEPs turn ideas into shipped features
- The concrete path from observer to contributor
- How projects enter, mature, and graduate within the CNCF landscape

---

## Part 1: The CNCF Governance Model

### A City, Not a Corporation

The cloud native ecosystem is often compared to a city. This analogy is useful because cities have multiple layers of governance, and no single authority controls everything.

The **Cloud Native Computing Foundation (CNCF)** is part of the Linux Foundation. It does not own Kubernetes or any other project. Instead, it provides a vendor-neutral home -- think of it as the city charter that defines how governance works, but does not micromanage neighborhoods.

Here is how the layers fit together:

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

The key insight: **technical decisions are made by technical people, not by the companies that fund the foundation.** The Governing Board handles money and marketing. The TOC handles technology. This separation is deliberate -- it prevents any single vendor from controlling the direction of projects like Kubernetes, Envoy, or Prometheus.

### The Kubernetes Project: Its Own Government

Kubernetes predates CNCF. Google donated it to the foundation in 2015, but the Kubernetes project has its own governance structure that sits *within* the CNCF umbrella. The Kubernetes Steering Committee handles project-wide policy, while day-to-day technical work is organized through SIGs.

This matters because when someone says "the CNCF decided X about Kubernetes," they are usually wrong. The Kubernetes community decides Kubernetes direction. CNCF provides the home and the infrastructure.

---

## Part 2: SIGs, Working Groups, and KEPs

### How Decisions Actually Get Made

If governance is the constitution, **SIGs (Special Interest Groups)** are the legislative bodies. Each SIG owns a specific area of Kubernetes:

| SIG | What They Own | Example Decisions |
|-----|---------------|-------------------|
| SIG Network | Networking, Services, DNS, Ingress | Gateway API design, IPv4/IPv6 dual-stack |
| SIG Storage | Persistent Volumes, CSI, storage classes | CSI migration from in-tree drivers |
| SIG Auth | Authentication, authorization, security policies | Pod Security Standards replacing PSPs |
| SIG Node | Kubelet, container runtime, node lifecycle | Containerd as default runtime |
| SIG Apps | Workload controllers (Deployments, StatefulSets) | Job indexing, pod failure policies |
| SIG Release | Release process, cadence, tooling | Three releases per year schedule |

There are currently about 20 SIGs, plus subprojects within them. **Working Groups (WGs)** are temporary -- they form around cross-cutting problems (like "WG Policy" or "WG Batch") and disband when the work is done.

### The KEP Process: From Idea to Feature

When someone wants to make a significant change to Kubernetes, they do not just open a pull request. They write a **KEP (Kubernetes Enhancement Proposal)**. Think of it as an architectural design document that must survive public scrutiny.

The lifecycle of a feature looks like this:

1. **Problem statement** -- Author describes the problem and why it matters
2. **KEP draft** -- Proposed solution, alternatives considered, risks identified
3. **SIG review** -- The owning SIG discusses the KEP in meetings and on GitHub
4. **Alpha** -- Feature lands behind a feature gate, disabled by default
5. **Beta** -- Feature gate enabled by default after proving stability
6. **GA (Generally Available)** -- Feature gate removed, feature is permanent

This process is deliberately slow. A feature like the Gateway API took years from initial KEP to GA. The reason: once a feature reaches GA, the project commits to supporting it indefinitely. Rushing leads to API debt that millions of users inherit.

> **Key insight for the KCNA exam**: The KEP process exists to prevent breaking changes and ensure community consensus. It is not bureaucracy for its own sake -- it is how you maintain stability when 5.6 million developers depend on your API.

---

## Part 3: From Lurker to Contributor

### The Contribution Ladder

Every Kubernetes contributor started the same way: watching. There is no shame in lurking -- in fact, it is the recommended first step. Here is the concrete path:

**Step 1: Observe (Week 1-2)**
- Join `slack.k8s.io` and follow channels like `#sig-docs`, `#kubernetes-dev`, or a SIG that interests you
- Watch a recorded SIG meeting on YouTube (they are all public)
- Read through 3-5 merged pull requests to understand the review culture

**Step 2: Triage (Week 2-4)**
- Find issues labeled `good-first-issue` or `help-wanted`
- Reproduce bugs and add information to the issue (Kubernetes version, environment, logs)
- Answer questions in Slack or on GitHub Discussions where you have expertise

**Step 3: Small Contributions (Month 1-2)**
- Fix documentation typos or improve unclear explanations
- Add or fix tests for existing functionality
- Review other people's PRs (anyone can leave review comments)

**Step 4: Sustained Contribution (Month 3+)**
- Take on larger issues within a SIG
- Attend SIG meetings regularly and volunteer for action items
- Work toward **Reviewer** status (granted by SIG leads after consistent quality)

**Step 5: Leadership (Year 1+)**
- Become an **Approver** for a subproject (technical authority over merges)
- Run for SIG lead positions
- Author KEPs for features you care about

### What Makes a Good Contribution

The difference between contributions that get merged and those that languish:

- **Good bug reports** include: Kubernetes version, cluster setup (kind/EKS/GKE), exact reproduction steps, expected vs. actual behavior, and relevant logs
- **Good PRs** include: clear description of what and why, tests that prove the change works, response to reviewer feedback within a few days
- **Good reviews** include: testing the change locally, checking edge cases, being respectful but honest about concerns

---

## Part 4: The CNCF Landscape and Graduation

### How Projects Join and Mature

The CNCF does not just accept any project. There is a deliberate maturity model:

| Level | What It Means | Requirements | Examples |
|-------|--------------|--------------|----------|
| **Sandbox** | Early stage, experimental | TOC sponsor, clear scope | Backstage (early), OpenKruise |
| **Incubating** | Growing adoption, maturing governance | Healthy contributor base, used in production | Kyverno, Cilium (before graduation) |
| **Graduated** | Production-ready, proven governance | Independent security audit, diverse maintainers | Kubernetes, Prometheus, Envoy, Argo |

The graduation criteria are strict. A project must demonstrate that no single company controls it -- if the primary maintainer leaves, the project must be able to continue. This is why the CNCF requires diverse maintainers from multiple organizations.

As of 2025, the CNCF landscape includes over 170 projects and maps more than 1,000 tools across categories like orchestration, service mesh, observability, and security. The landscape (landscape.cncf.io) is deliberately overwhelming -- it reflects the real breadth of the ecosystem.

### Why Graduation Matters to You

When you evaluate tools for production use, the CNCF maturity level tells you something concrete:

- **Graduated** projects have passed independent security audits, have diverse governance, and will not disappear if one company loses interest
- **Incubating** projects are production-viable but still maturing their governance
- **Sandbox** projects are experiments -- useful for evaluation but risky for production dependencies

---

## Did You Know?

1. **Kubernetes has over 3,200 individual contributors** from more than 80 countries. No single company contributes more than 25% of the code, by design.

2. **The first Kubernetes commit was on June 6, 2014.** It was open-sourced by Google just one year later and donated to the newly formed CNCF in 2015 -- one of the fastest paths from internal tool to community-governed project in history.

3. **KEP-4222 (CBOR serialization)** took three years from proposal to beta. During that time, the community identified and solved backward-compatibility issues that the original authors had not considered. The slow process prevented breaking millions of existing API clients.

4. **The CNCF End User Technical Advisory Board** includes engineers from companies like Spotify, Intuit, and The New York Times. Their job is to ensure that CNCF project decisions reflect actual production needs, not just vendor roadmaps.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix |
|---------|----------------|------------|
| Opening a large PR without a KEP | Eager to contribute, unaware of process | Check if your change needs a KEP. Any API change or new feature likely does. |
| Asking questions already answered in docs | Enthusiasm outruns preparation | Read the contributor guide, CONTRIBUTING.md, and search Slack history first. |
| Equating CNCF membership with endorsement | The landscape is large and confusing | Check the maturity level. Sandbox is experimental, not "CNCF-approved for production." |
| Ignoring reviewer feedback on a PR | Feeling defensive about code | Reviews are collaborative. Respond to every comment, even if just to acknowledge it. |
| Assuming one company controls Kubernetes | Brand association (Google created it) | Look at contributor stats. Kubernetes governance is deliberately vendor-diverse. |
| Treating SIG meetings as optional spectating | Not realizing decisions happen there | SIG meetings are where work is assigned and designs are debated. Attend to participate. |

---

## Quiz: Test Your Understanding

**Question 1**: A new engineer wants to add a feature that changes the Kubernetes API for Pod scheduling. They open a pull request directly with the code. What will likely happen, and what should they have done instead?

<details>
<summary>Answer</summary>

The PR will almost certainly be rejected or put on hold. Any change to the Kubernetes API requires a KEP (Kubernetes Enhancement Proposal) before implementation begins. The KEP process ensures the community agrees on the problem, reviews alternative approaches, and considers backward compatibility. The engineer should have started by drafting a KEP, presenting it to the relevant SIG (likely SIG Scheduling), and getting consensus before writing code. This is not gatekeeping -- it prevents the project from accumulating API debt that millions of users would inherit.
</details>

**Question 2**: Your company is evaluating two CNCF projects for service mesh. Project A is Graduated and Project B is in Sandbox but has more features. Your manager asks which to choose for a production deployment handling financial transactions. What factors from the CNCF maturity model should inform this decision?

<details>
<summary>Answer</summary>

The Graduated project (A) has passed an independent security audit, has demonstrated diverse maintainer governance (no single-vendor dependency), and has proven production adoption. The Sandbox project (B) may have appealing features, but it has not yet proven governance resilience or undergone security scrutiny. For financial transactions where reliability and security are critical, the maturity level matters more than feature count. You could use Project B in non-critical environments while it matures, but production financial workloads should favor the Graduated project's proven stability and security posture.
</details>

**Question 3**: A contributor has been actively fixing bugs in SIG Network for six months. They want to become a Reviewer so their approvals carry more weight. Who grants this status, and what are they evaluating?

<details>
<summary>Answer</summary>

Reviewer status is granted by the SIG leads (SIG chairs and tech leads), not by the CNCF or any corporate entity. They evaluate the contributor's track record: consistency of contributions, quality of code reviews they have already done (anyone can leave comments), understanding of the codebase area, and ability to identify edge cases and potential regressions. The Kubernetes project uses an OWNERS file system where Reviewers are listed per directory. This is a meritocratic process -- it does not matter which company you work for or whether you work for one at all.
</details>

**Question 4**: During a SIG meeting, two major cloud providers disagree on the design of a new storage feature. One provider threatens to fork the feature if their approach is not accepted. How does CNCF governance handle this situation?

<details>
<summary>Answer</summary>

The CNCF governance model is specifically designed to prevent vendor capture. The TOC and SIG leads evaluate technical proposals on merit, not on the contributor's employer. The KEP process requires documenting alternatives and their trade-offs, which means the community can objectively compare approaches. If a vendor forks, they lose the benefit of community maintenance, security audits, and ecosystem integration. In practice, the threat of forking rarely succeeds because the cost of maintaining a fork exceeds the cost of compromise. The Steering Committee can also intervene if a SIG-level dispute escalates.
</details>

**Question 5**: You notice that a popular tool appears on the CNCF Landscape website. Your team assumes this means the CNCF has vetted it for production use. Is this assumption correct? Why or why not?

<details>
<summary>Answer</summary>

This assumption is incorrect and it is one of the most common misunderstandings about the CNCF. The CNCF Landscape is a comprehensive map of the cloud native ecosystem -- it includes over 1,000 entries, many of which are not CNCF projects at all. Even among actual CNCF projects, the maturity levels vary dramatically: Sandbox projects are early-stage experiments, while Graduated projects have passed rigorous governance and security reviews. Appearing on the landscape means a tool exists in the ecosystem, not that the CNCF endorses or has audited it. Always check the specific project's maturity level and do your own evaluation.
</details>

---

## Reflection Exercise

Find a real Kubernetes Enhancement Proposal (KEP) at `github.com/kubernetes/enhancements/tree/master/keps`. Pick one that interests you -- perhaps something related to a feature you use daily.

Read through the KEP and answer these questions in your notes:

1. **What problem does this KEP solve?** Summarize it in two sentences.
2. **What alternatives were considered?** Why were they rejected?
3. **Which SIG owns this KEP?** Look at the labels and the `kep.yaml` metadata.
4. **What is the current status?** (Provisional, Implementable, Alpha, Beta, GA, Deprecated)
5. **How long has it been in progress?** Check the git history of the KEP directory.

This exercise builds a skill you will use repeatedly in your career: reading design documents to understand not just *what* a system does, but *why* it was built that way and what trade-offs were accepted.

---

**Next Module**: [Module 3.8: AI/ML in Cloud Native](/k8s/kcna/part3-cloud-native-architecture/module-3.8-ai-ml-cloud-native/)
