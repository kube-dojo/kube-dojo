---
title: "Module 4.5: Threat Modeling & Supply Chain Theory"
slug: k8s/kcsa/part4-threat-model/module-4.5-threat-modeling-supply-chain-theory
sidebar:
  order: 6
---
> **Complexity**: `[MEDIUM]` - Core security mindset
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 4.1: Attack Surfaces](../module-4.1-attack-surfaces/), [Module 4.4: Supply Chain Threats](../module-4.4-supply-chain/)

---

In December 2020, a routine FireEye security audit uncovered something terrifying: attackers had spent nine months inside 18,000+ organizations through a single compromised SolarWinds build server. No firewall blocked them. No IDS flagged them. The malicious code arrived through a trusted software update — signed, verified, and delivered through official channels. The organizations that fared best weren't the ones with the most tools — they were the ones that had threat-modeled their supply chain and knew exactly which trust boundaries mattered.

---

## Why This Module Matters

Supply chain attacks bypass every runtime control because they weaponize trust. Your admission controllers approve the image — it came from your own registry. Your network policies allow the traffic — the compromised pod looks legitimate. Falco sees nothing — the malicious code runs inside normal process boundaries.

KCSA tests whether you can *think* about threats systematically — not just react to them. This module teaches you how to model threats across the Kubernetes 4C layers and apply that thinking to supply chain risks specifically.

---

## The 4C Model: Systematic Threat Thinking

Kubernetes security operates in four concentric layers. Each layer inherits the weaknesses of the layer beneath it — a secure container means nothing on a compromised cluster.

```
┌─────────────────────────────────────────────────────────────┐
│              THE 4C MODEL                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CLOUD (Infrastructure Layer)                        │  │
│  │  • IAM misconfigurations                             │  │
│  │  • Metadata service abuse (169.254.169.254)          │  │
│  │  • Network exposure (public API servers)             │  │
│  │  • Storage bucket leaks                              │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  CLUSTER (Orchestration Layer)                 │  │  │
│  │  │  • etcd exposure (all secrets stored here)     │  │  │
│  │  │  • API server misconfiguration                 │  │  │
│  │  │  • Malicious admission webhooks                │  │  │
│  │  │  • Overly permissive RBAC                      │  │  │
│  │  │                                                 │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │  CONTAINER (Runtime Layer)               │  │  │  │
│  │  │  │  • Privilege escalation                  │  │  │  │
│  │  │  │  • Unbounded syscalls                    │  │  │  │
│  │  │  │  • Writable root filesystem              │  │  │  │
│  │  │  │  • Running as root                       │  │  │  │
│  │  │  │                                           │  │  │  │
│  │  │  │  ┌─────────────────────────────────────┐  │  │  │  │
│  │  │  │  │  CODE (Application Layer)          │  │  │  │  │
│  │  │  │  │  • Vulnerable dependencies         │  │  │  │  │
│  │  │  │  │  • Poisoned base images            │  │  │  │  │
│  │  │  │  │  • Secrets in source code          │  │  │  │  │
│  │  │  │  │  • Unvalidated input               │  │  │  │  │
│  │  │  │  └─────────────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  KEY INSIGHT: Each layer inherits risk from inner layers.   │
│  A compromised Code layer undermines Container, Cluster,    │
│  and Cloud security — this is why supply chain matters.     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why 4C Matters for Supply Chain

Supply chain attacks are uniquely dangerous because they enter at the **Code layer** — the innermost ring — and propagate outward:

| Layer | How Supply Chain Attacks Manifest |
|-------|-----------------------------------|
| **Code** | Malicious dependency, poisoned image, backdoored library |
| **Container** | Compromised image runs as expected — no runtime anomaly |
| **Cluster** | Admission controllers approve the "trusted" artifact |
| **Cloud** | Exfiltrated data flows through legitimate network paths |

A traditional attack works outside-in (network → cluster → container). A supply chain attack works **inside-out** — it starts trusted and exploits that trust.

---

## Threat Modeling Workflow for Kubernetes

Threat modeling is a structured way to answer: *"What can go wrong, and what should we do about it?"*

```
┌─────────────────────────────────────────────────────────────┐
│              THREAT MODELING WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: IDENTIFY ASSETS                                    │
│  ├── What are we protecting?                                │
│  ├── Secrets in etcd                                        │
│  ├── Customer data in databases                             │
│  ├── Service credentials                                    │
│  └── Container images and build artifacts                   │
│                                                             │
│  Step 2: MAP DATA FLOWS                                     │
│  ├── How does data move?                                    │
│  ├── kubectl → API server → etcd                            │
│  ├── CI/CD → Registry → kubelet → Container                 │
│  ├── Pod → Service → Ingress → Internet                     │
│  └── Each arrow is a potential attack surface                │
│                                                             │
│  Step 3: IDENTIFY ENTRY POINTS                              │
│  ├── Where can attackers get in?                            │
│  ├── API server (external/internal)                         │
│  ├── Ingress controllers                                    │
│  ├── CI/CD pipeline                                         │
│  ├── Image registry                                         │
│  └── Developer workstations                                 │
│                                                             │
│  Step 4: MODEL ABUSE CASES                                  │
│  ├── What if an attacker gains cluster-admin?               │
│  ├── What if a base image is poisoned?                      │
│  ├── What if an admission webhook is compromised?           │
│  └── What if CI/CD credentials are stolen?                  │
│                                                             │
│  Step 5: ASSIGN MITIGATIONS                                 │
│  ├── Who owns each control?                                 │
│  ├── Platform team → admission policies, RBAC               │
│  ├── Security team → scanning, monitoring                   │
│  ├── Dev team → secure code, dependency updates             │
│  └── Document residual risk for accepted gaps               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### STRIDE Applied to Kubernetes

STRIDE is a classic threat modeling framework. Here is how each category maps to Kubernetes:

| STRIDE Category | Kubernetes Example | Supply Chain Angle |
|----------------|--------------------|--------------------|
| **S**poofing | Fake kubelet joining cluster | Typosquatted image name |
| **T**ampering | Modified ConfigMap at rest | Build artifact tampered in CI |
| **R**epudiation | No audit trail for who ran kubectl | No provenance for built images |
| **I**nformation Disclosure | etcd exposed without TLS | SBOM leaks internal dependency info |
| **D**enial of Service | Resource bomb in pod spec | Dependency with infinite loop |
| **E**levation of Privilege | Container escape to node | Compromised image with reverse shell |

---

## Supply Chain Risk: A Deeper Model

Module 4.4 covered *what* supply chain attacks look like. This module focuses on *how to reason about* supply chain risk systematically.

### Trust Boundaries in the Supply Chain

Every handoff in the software delivery pipeline crosses a trust boundary. Threats concentrate at these boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│              SUPPLY CHAIN TRUST BOUNDARIES                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Developer ──┬── Source Repo ──┬── Build ──┬── Registry     │
│              │                │           │                  │
│         BOUNDARY 1       BOUNDARY 2   BOUNDARY 3            │
│                                                             │
│  BOUNDARY 1: Developer → Source                             │
│  ├── RISK: Compromised workstation, stolen credentials      │
│  ├── CONTROL: MFA, signed commits, branch protection        │
│  └── VERIFY: Commit signatures, code review                 │
│                                                             │
│  BOUNDARY 2: Source → Build                                 │
│  ├── RISK: Malicious build scripts, dependency confusion    │
│  ├── CONTROL: Isolated builds, pinned dependencies          │
│  └── VERIFY: Reproducible builds, build provenance          │
│                                                             │
│  BOUNDARY 3: Build → Registry                               │
│  ├── RISK: Image tampering, tag overwrite                   │
│  ├── CONTROL: Image signing, immutable tags                 │
│  └── VERIFY: Signature verification at admission            │
│                                                             │
│  Registry ──┬── Admission ──┬── Runtime                     │
│             │               │                                │
│        BOUNDARY 4      BOUNDARY 5                            │
│                                                             │
│  BOUNDARY 4: Registry → Cluster                             │
│  ├── RISK: Pulling compromised/outdated images              │
│  ├── CONTROL: Admission policies, allowed registries        │
│  └── VERIFY: Digest match, signature check, CVE scan        │
│                                                             │
│  BOUNDARY 5: Admission → Runtime                            │
│  ├── RISK: Admitted pod behaves maliciously                 │
│  ├── CONTROL: NetworkPolicies, seccomp, AppArmor            │
│  └── VERIFY: Runtime monitoring (Falco), audit logging      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Provenance: Knowing Where Things Came From

Provenance answers the fundamental question: *can you prove this artifact is what it claims to be?*

```
┌─────────────────────────────────────────────────────────────┐
│              PROVENANCE CHAIN                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT PROVENANCE:                                        │
│  "This image came from somewhere. It has a tag. Ship it."   │
│                                                             │
│  WITH PROVENANCE (SLSA Level 3):                            │
│  ├── WHO built it? → CI system identity (OIDC)              │
│  ├── WHAT source? → git commit SHA + repo URL               │
│  ├── HOW was it built? → build config, entry point          │
│  ├── WHEN was it built? → timestamp                         │
│  ├── WHERE was it built? → isolated, ephemeral builder      │
│  └── PROOF? → Signed attestation in Rekor transparency log  │
│                                                             │
│  SBOM adds: WHAT'S INSIDE?                                  │
│  ├── Every library, every version                           │
│  ├── Every transitive dependency                            │
│  └── Every license                                          │
│                                                             │
│  Together, provenance + SBOM answer:                        │
│  "I know exactly what's in this artifact,                   │
│   who built it, from what source, and I can prove it."      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Policy Gates: Enforcing Trust at the Cluster Boundary

Policy gates are admission-time controls that enforce supply chain requirements before pods run:

```
┌─────────────────────────────────────────────────────────────┐
│              POLICY GATE MODEL                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pod Creation Request                                       │
│        │                                                    │
│        ▼                                                    │
│  ┌──────────────┐   FAIL → "Image not from allowed          │
│  │ Registry     │           registry"                       │
│  │ Allowlist    │                                           │
│  └──────┬───────┘                                           │
│         │ PASS                                              │
│         ▼                                                    │
│  ┌──────────────┐   FAIL → "Image not signed by             │
│  │ Signature    │           trusted key"                    │
│  │ Verification │                                           │
│  └──────┬───────┘                                           │
│         │ PASS                                              │
│         ▼                                                    │
│  ┌──────────────┐   FAIL → "CRITICAL CVE found:             │
│  │ Vulnerability│           CVE-2024-XXXX"                  │
│  │ Scan Check   │                                           │
│  └──────┬───────┘                                           │
│         │ PASS                                              │
│         ▼                                                    │
│  ┌──────────────┐   FAIL → "No SBOM attestation             │
│  │ SBOM/        │           found"                          │
│  │ Attestation  │                                           │
│  └──────┬───────┘                                           │
│         │ PASS                                              │
│         ▼                                                    │
│  Pod Admitted ✓                                              │
│                                                             │
│  TOOLS: Kyverno, OPA/Gatekeeper, Connaisseur, Ratify       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Mitigation Matrix

This matrix maps common Kubernetes threats to conceptual mitigations. Use this as a template when threat-modeling your own clusters:

| Threat | 4C Layer | Mitigation | Owner |
|--------|----------|------------|-------|
| Compromised admission webhook | Cluster | mTLS, minimal RBAC, fail-closed defaults, webhook isolation | Platform |
| Registry poisoning | Code | Signed images, pinned digests, restricted registry egress, pre-admission SBOM scan | Security |
| Node/container escape | Container | seccomp/AppArmor, drop capabilities, distroless bases, read-only rootfs | Platform |
| Stolen kubeconfig | Cluster | Short-lived creds, client cert rotation, least-privilege RBAC, MFA | Security |
| Malicious dependency | Code | Lockfiles, dependency scanning, private package repos, SBOM generation | Dev |
| CI/CD credential theft | Code/Cluster | Ephemeral build agents, secret managers, OIDC federation (no long-lived tokens) | Platform |
| etcd data exposure | Cluster | Encryption at rest, restrict etcd access to API server only, mTLS | Platform |
| Metadata service abuse | Cloud | IMDSv2/metadata concealment, limit IAM scope, network policies | Cloud/Platform |

---

## Applying Threat Models: A Worked Example

Consider a team deploying a payment service:

```
┌─────────────────────────────────────────────────────────────┐
│              PAYMENT SERVICE THREAT MODEL                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ASSETS:                                                    │
│  • Credit card tokens (PCI scope)                           │
│  • API keys to payment processor                            │
│  • Transaction logs                                         │
│                                                             │
│  DATA FLOW:                                                 │
│  User → Ingress → payment-svc → payment-processor (ext)     │
│                        │                                    │
│                        ▼                                    │
│                   PostgreSQL (PCI data)                      │
│                                                             │
│  TOP THREATS:                                               │
│  1. Compromised payment-svc image (supply chain)            │
│     → Exfiltrates card tokens through DNS                   │
│     → Mitigation: signed images, SBOM, egress NetworkPolicy │
│                                                             │
│  2. Stolen payment processor API key                        │
│     → Fraudulent transactions                               │
│     → Mitigation: External Secrets Operator, rotation       │
│                                                             │
│  3. SQL injection exposing PCI data                         │
│     → Compliance violation, fines                           │
│     → Mitigation: Parameterized queries, WAF, audit logging │
│                                                             │
│  4. Container escape from payment-svc                       │
│     → Access to node, then cluster                          │
│     → Mitigation: seccomp, non-root, read-only rootfs       │
│                                                             │
│  RESIDUAL RISK:                                             │
│  • Zero-day in base image (accepted, mitigated by scanning) │
│  • Payment processor compromise (outside our control)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The 2020 SolarWinds breach** affected 18,000 organizations including US government agencies, yet the attackers compromised only one build server. Supply chain attacks offer extraordinary leverage — one breach, thousands of victims.

- **Google's SLSA framework** was born from a decade of internal supply chain security work. Google requires provenance for every binary running in production — over two billion containers per week.

- **The concept of "threat modeling" predates computers** — military strategists have used structured adversarial thinking for centuries. Microsoft formalized STRIDE for software in 1999, and it remains the most widely used framework.

- **A 2023 Sonatype report** found that software supply chain attacks increased 742% over the previous three years, with over 245,000 malicious packages discovered across npm, PyPI, and other registries.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Modeling once and never updating | New features introduce new attack surfaces | Re-model quarterly and after major changes |
| Focusing only on runtime threats | Supply chain attacks bypass runtime controls | Include CI/CD pipeline and dependencies in model |
| No ownership assigned to mitigations | Controls without owners don't get implemented | Assign each mitigation to a specific team |
| Ignoring residual risk | Creates false sense of security | Document accepted risks and review triggers |
| Threat modeling in isolation | Misses cross-team attack paths | Include platform, security, and dev teams |

---

## Quiz

1. **What are the four layers of the 4C security model?**
   <details>
   <summary>Answer</summary>
   Cloud, Cluster, Container, Code. Each outer layer inherits the risks of inner layers — a vulnerable Code layer undermines security at every other layer, which is why supply chain security is so critical.
   </details>

2. **Why are supply chain attacks uniquely dangerous compared to traditional network attacks?**
   <details>
   <summary>Answer</summary>
   Supply chain attacks enter through the innermost layer (Code) and work inside-out. The malicious code arrives through trusted channels — signed, approved, and deployed through normal processes. Runtime security controls see the malicious code as legitimate because it's embedded in trusted artifacts.
   </details>

3. **What five questions does provenance answer?**
   <details>
   <summary>Answer</summary>
   Who built it (identity), what source was used (git commit), how it was built (build config), when it was built (timestamp), and where it was built (build platform). At SLSA Level 3, these answers are cryptographically signed and recorded in a transparency log.
   </details>

4. **In STRIDE, what does each letter represent and how does it apply to Kubernetes?**
   <details>
   <summary>Answer</summary>
   Spoofing (fake kubelet, typosquatted images), Tampering (modified ConfigMaps, build artifacts), Repudiation (no audit trail, no image provenance), Information Disclosure (etcd exposure, leaked SBOMs), Denial of Service (resource bombs, bad dependencies), Elevation of Privilege (container escape, compromised images with reverse shells).
   </details>

5. **What is a trust boundary and why do threats concentrate at these points?**
   <details>
   <summary>Answer</summary>
   A trust boundary is a point where data or artifacts cross from one security domain to another — like developer to source repo, build system to registry, or registry to cluster. Threats concentrate here because each handoff requires verification: the receiving side must validate that the artifact hasn't been tampered with. Without verification (signatures, digests, scanning), attackers can inject malicious content at any boundary.
   </details>

6. **Why should you document residual risk in a threat model?**
   <details>
   <summary>Answer</summary>
   Not every threat can be fully mitigated. Documenting residual risk (e.g., "zero-day in base image — accepted, mitigated by continuous scanning") prevents a false sense of security and creates explicit review triggers. It also helps prioritize future security investment.
   </details>

---

## Hands-On Exercise: Build a Threat Model

**Task**: Create a threat model for a web application running in Kubernetes.

**Scenario**: An e-commerce application with three services — frontend (React), API (Go), and database (PostgreSQL). The team uses GitHub Actions for CI/CD and pushes images to a private ECR registry.

**Step 1 — Identify assets:**
List at least 5 assets that need protection.

<details>
<summary>Example Assets</summary>

1. Customer PII (names, addresses, emails)
2. Payment information (processed by external provider)
3. Database credentials
4. GitHub Actions secrets (ECR push credentials)
5. API authentication tokens
6. Container images in ECR
7. Kubernetes Secrets

</details>

**Step 2 — Map data flows and entry points:**
Draw the path from developer commit to running pod.

<details>
<summary>Example Data Flow</summary>

```
Developer → GitHub (push) → GitHub Actions → docker build → ECR
                                                              │
                                            ArgoCD sync ←─────┘
                                                │
                                                ▼
                                          EKS Cluster
                                   ┌──────────────────────┐
                                   │ frontend → api → db  │
                                   └──────────────────────┘

Entry points:
- GitHub (compromised developer credentials)
- GitHub Actions (secrets, runner compromise)
- ECR (registry access)
- EKS API server (kubeconfig theft)
- Ingress (external traffic)
```

</details>

**Step 3 — Model three abuse cases using STRIDE:**

<details>
<summary>Example Abuse Cases</summary>

1. **Tampering — Build pipeline compromise**: Attacker modifies GitHub Actions workflow to inject backdoor during build. Image passes signature check because it was built by the legitimate CI system.
   - Mitigation: Require PR review for workflow changes, use reusable workflows from a separate trusted repo, SLSA Level 3 provenance.

2. **Spoofing — Dependency confusion**: Attacker publishes a public npm package matching an internal package name. GitHub Actions pulls the public (higher-version) package instead.
   - Mitigation: .npmrc with registry scoping, lockfile integrity checks, private registry for internal packages.

3. **Information Disclosure — Secret leak in logs**: Database credentials appear in application error logs, captured by centralized logging, visible to operations team.
   - Mitigation: Log scrubbing, structured logging with sensitive field redaction, External Secrets Operator for rotation.

</details>

**Step 4 — Create a mitigation table with owners:**

<details>
<summary>Example Mitigation Table</summary>

| Threat | Mitigation | Owner | Status |
|--------|-----------|-------|--------|
| Build pipeline compromise | PR review for workflows, SLSA provenance | Platform | Planned |
| Dependency confusion | Registry scoping, lockfile checks | Dev | Implemented |
| Secret in logs | Log scrubbing, ESO rotation | Dev + Platform | In progress |
| Image with critical CVE | Trivy in CI, admission policy | Security | Implemented |
| Stolen kubeconfig | Short-lived tokens, OIDC auth | Platform | Implemented |

Residual risks:
- Zero-day in Go stdlib (accepted — mitigated by rapid patching process)
- GitHub Actions platform compromise (accepted — outside our control)

</details>

**Success criteria**: You have a document with assets, data flows, at least 3 STRIDE-based abuse cases, a mitigation table with owners, and documented residual risks.

---

## Summary

Threat modeling is the discipline of thinking like an attacker *before* they do:

| Concept | Key Insight |
|---------|------------|
| **4C Model** | Security is layered — inner layers (Code) affect all outer layers |
| **Supply chain** | Attacks enter at Code layer and exploit trust — bypassing runtime controls |
| **Trust boundaries** | Every handoff (dev → source → build → registry → cluster) needs verification |
| **Provenance** | You can't trust what you can't trace — sign, attest, verify |
| **Policy gates** | Enforce supply chain requirements at admission time, not after deployment |
| **STRIDE** | Systematic framework to avoid missing threat categories |
| **Residual risk** | Document what you *can't* mitigate — false security is worse than known risk |

The goal isn't to eliminate all risk — it's to know exactly where your risks are, who owns them, and what triggers a re-evaluation.

---

## Next Module

[Module 5.1: Image Security](../part5-platform-security/module-5.1-image-security/) - Securing container images through the lifecycle.
