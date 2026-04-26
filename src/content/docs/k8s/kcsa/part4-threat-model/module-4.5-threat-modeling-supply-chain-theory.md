---
qa_pending: true
title: "Module 4.5: Threat Modeling & Supply Chain Theory"
slug: k8s/kcsa/part4-threat-model/module-4.5-threat-modeling-supply-chain-theory
sidebar:
  order: 6
---

> **Complexity**: `[MEDIUM]` - Core security mindset
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: [Module 4.1: Attack Surfaces](../module-4.1-attack-surfaces/), [Module 4.4: Supply Chain Threats](../module-4.4-supply-chain/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** a Kubernetes threat model that maps assets, data flows, entry points, trust boundaries, and abuse cases across the 4C layers.
2. **Evaluate** supply chain trust boundaries and decide where signatures, attestations, SBOMs, admission policies, and runtime controls provide useful verification.
3. **Compare** STRIDE categories against Kubernetes examples so you can avoid modeling only the threats that are already familiar to your team.
4. **Prioritize** mitigations by owner, impact, and residual risk instead of producing a long control list that nobody can implement.
5. **Debug** a weak supply chain security design by identifying which boundary failed and which evidence would prove the artifact should be trusted.

---

## Why This Module Matters

In December 2020, a FireEye security investigation exposed a terrifying pattern: attackers had reached thousands of organizations through a trusted SolarWinds software update. The update did not arrive as a suspicious binary from an unknown server. It arrived through an expected vendor channel, carried the appearance of normal delivery, and moved through environments that had already decided to trust that vendor's software.

A Kubernetes platform can make the same mistake at smaller scale every day. A deployment may use an image from the approved registry, a workflow from the approved repository, and a service account created by the approved platform team, yet still run attacker-controlled code because the build path itself was compromised. Runtime controls matter, but runtime controls often see a poisoned artifact as ordinary behavior if the artifact entered through the trusted path.

Threat modeling gives a team a disciplined way to reason before the incident. Instead of asking, "Do we have scanning?" the team asks, "What are we protecting, where does trust change hands, how could an attacker abuse each handoff, and which control would give us evidence?" That shift is the difference between collecting security tools and building a security argument.

KCSA expects that mindset. You do not need to become a specialist in every supply chain framework, but you do need to recognize how Kubernetes threat modeling connects code, containers, clusters, and cloud infrastructure. The exam tests whether you can reason about security relationships, not merely remember product names.

---

## The Threat Modeling Mindset

Threat modeling is a structured way to answer a practical question: what can go wrong, and what should the team do about it? The useful output is not a beautiful diagram. The useful output is a shared understanding of assets, assumptions, abuse cases, controls, owners, and remaining risk.

A weak threat model starts with tools. It says, "We use Trivy, Kyverno, and Falco, so we have supply chain security." A stronger threat model starts with a story about how software becomes a running workload. It asks who can change the source, who can change the build, who can publish the image, who can approve the deployment, and who can observe the workload after admission.

For Kubernetes, the modeling scope should include both the workload and the delivery path. A pod specification is not the beginning of the story. The story begins when a developer chooses a dependency, writes code, changes a workflow, or opens a pull request. By the time the pod reaches the API server, many security decisions have already happened.

A useful beginner pattern is to model in five passes. First, identify assets. Second, map data flows. Third, mark trust boundaries. Fourth, create abuse cases using a framework such as STRIDE. Fifth, choose controls and document residual risk. The sequence matters because controls chosen before assets and boundaries are often fashionable rather than relevant.

```text
+-------------------------------------------------------------+
|                 THREAT MODELING WORKFLOW                    |
+-------------------------------------------------------------+
|                                                             |
|  1. IDENTIFY ASSETS                                         |
|     What would hurt if it were stolen, changed, or lost?    |
|     Examples: secrets, customer data, images, source code.  |
|                                                             |
|  2. MAP DATA FLOWS                                          |
|     How do code, credentials, artifacts, and requests move? |
|     Examples: commit -> CI -> registry -> admission -> pod. |
|                                                             |
|  3. MARK TRUST BOUNDARIES                                   |
|     Where does responsibility or security context change?   |
|     Examples: developer laptop to repo, registry to cluster.|
|                                                             |
|  4. MODEL ABUSE CASES                                       |
|     How could an attacker misuse a normal path?             |
|     Examples: poisoned dependency, stolen CI token, tag swap.|
|                                                             |
|  5. ASSIGN MITIGATIONS                                      |
|     Which control reduces which risk, and who owns it?      |
|     Examples: signed images, SBOMs, RBAC, NetworkPolicies.  |
|                                                             |
+-------------------------------------------------------------+
```

The phrase "misuse a normal path" is especially important for supply chain work. An attacker does not always need an exotic exploit if the pipeline accepts new code, builds it, signs it, and deploys it automatically. The threat model should therefore describe how a normal success path could be turned into an attacker success path.

**Active learning prompt:** Your team says, "Our cluster is safe because only signed images can run." Before reading further, decide which earlier step in the delivery path could still let an attacker produce a signed malicious image. Keep that answer in mind as you study trust boundaries.

---

## The 4C Model for Kubernetes Threats

Kubernetes security is often described with the 4C model: Cloud, Cluster, Container, and Code. These layers are not separate checklists. They are dependencies. The outer layers rely on the inner layers, and the inner layers rely on the outer environment that builds, stores, and runs them.

The 4C model helps beginners avoid a common blind spot. A team may harden pods while ignoring the CI runner that builds the pod image. Another team may lock down the cloud network while allowing a compromised dependency to run inside an approved workload. Both teams improved security in one layer, but neither proved the full path was trustworthy.

```text
+------------------------------------------------------------------+
|                          THE 4C MODEL                            |
+------------------------------------------------------------------+
|                                                                  |
|  +------------------------------------------------------------+  |
|  | CLOUD                                                      |  |
|  | IAM, networks, managed Kubernetes settings, storage, DNS.  |  |
|  | A cloud role with broad permissions can turn one pod       |  |
|  | compromise into account-wide damage.                       |  |
|  |                                                            |  |
|  |  +------------------------------------------------------+  |  |
|  |  | CLUSTER                                              |  |  |
|  |  | API server, etcd, RBAC, admission, audit, kubelets.   |  |  |
|  |  | A permissive ClusterRole can make a small foothold    |  |  |
|  |  | become a platform-wide control problem.               |  |  |
|  |  |                                                      |  |  |
|  |  |  +------------------------------------------------+  |  |  |
|  |  |  | CONTAINER                                      |  |  |  |
|  |  |  | Image contents, runtime settings, capabilities, |  |  |  |
|  |  |  | seccomp, AppArmor, read-only filesystems.       |  |  |  |
|  |  |  |                                                |  |  |  |
|  |  |  |  +------------------------------------------+  |  |  |  |
|  |  |  |  | CODE                                     |  |  |  |  |
|  |  |  |  | Source, dependencies, build scripts,      |  |  |  |  |
|  |  |  |  | package managers, and application logic.  |  |  |  |  |
|  |  |  |  +------------------------------------------+  |  |  |  |
|  |  |  +------------------------------------------------+  |  |  |
|  |  +------------------------------------------------------+  |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  Key idea: a trusted Kubernetes deployment can still run          |
|  untrusted code if the supply chain admitted bad inputs earlier.  |
|                                                                  |
+------------------------------------------------------------------+
```

Supply chain attacks are dangerous because they often enter at the Code layer and then inherit trust as they move outward. The registry may accept the image because the CI system built it. The admission controller may accept the image because the image is signed. The runtime may permit the process because it behaves like the expected application. Each layer says "this came from the layer before me," but the original compromise may have happened much earlier.

The 4C model also prevents overcorrection. If a malicious package runs inside a pod with no egress restrictions, no read-only filesystem, broad service account permissions, and cloud metadata access, the Code-layer failure becomes a Cluster and Cloud problem. If the same package runs in a constrained pod with narrow RBAC, denied metadata access, and blocked outbound network paths, the blast radius is smaller even though the dependency was still malicious.

| 4C Layer | Supply Chain Failure Example | What the Threat Model Should Ask |
|---|---|---|
| Code | A dependency maintainer account is compromised and publishes a malicious package. | Are dependencies pinned, reviewed, scanned, and limited to trusted registries? |
| Container | A base image tag is overwritten after the application team approved it. | Are images referenced by digest and verified before admission? |
| Cluster | An admission webhook trusts any image signed by the CI key, even from unprotected branches. | Does admission verify provenance, branch, builder identity, and policy context? |
| Cloud | A pod reaches the instance metadata service and obtains broad cloud credentials. | Are workload identities scoped, and is metadata access restricted or concealed? |

A senior-level model connects layers through consequences. It does not simply record "malicious dependency" under Code and stop. It asks what that dependency can reach, which Kubernetes identity it gets, what network paths are open, which secrets are mounted, and whether the cloud environment treats the pod as a privileged workload.

**Active learning prompt:** A team blocks privileged containers, requires non-root users, and uses read-only root filesystems. Their CI pipeline still builds unreviewed workflow changes from pull requests. Which 4C layer has the weakest assumption, and how could that weakness bypass the container hardening?

---

## STRIDE Applied to Kubernetes

STRIDE is a threat modeling framework that helps teams avoid focusing only on the attacks they already know. The categories are Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege. The value is not memorizing the words. The value is using each category as a prompt that forces a different kind of security question.

For Kubernetes, STRIDE becomes more useful when it is tied to concrete objects. Ask about service accounts, image tags, admission requests, ConfigMaps, Secrets, API audit events, package registries, CI jobs, container capabilities, and cloud identities. That keeps the model grounded in things the team can inspect and change.

| STRIDE Category | Kubernetes Question | Supply Chain Scenario | Useful Evidence or Control |
|---|---|---|---|
| Spoofing | Could something pretend to be a trusted user, node, service, or artifact? | An attacker publishes `corp-logging` to a public package registry and the build pulls it instead of the internal package. | Registry scoping, lockfile integrity, private package repositories, and dependency review. |
| Tampering | Could an attacker change data, configuration, or artifacts without detection? | A CI workflow modifies the image after tests pass but before signing. | Protected workflows, isolated builders, reproducible builds, provenance attestations, and code review. |
| Repudiation | Could someone deny making a change because evidence is missing? | A production image exists in the registry, but nobody can prove which commit or workflow produced it. | Signed provenance, immutable logs, audit events, and transparency logs. |
| Information Disclosure | Could sensitive data leak through normal or accidental paths? | An SBOM reveals internal package names, or a compromised pod reads mounted service credentials. | Secret minimization, RBAC, log redaction, careful SBOM publishing, and scoped tokens. |
| Denial of Service | Could a dependency, image, or workload exhaust shared resources? | A malicious package starts high CPU work during startup across hundreds of replicas. | Resource requests and limits, rollout controls, dependency scanning, and admission guardrails. |
| Elevation of Privilege | Could a low-privilege component gain more authority than intended? | A signed image runs with a service account that can list Secrets across namespaces. | Least-privilege RBAC, namespace boundaries, Pod Security Standards, and workload identity scoping. |

A common beginner mistake is to turn STRIDE into a vocabulary exercise. For example, asking "What does T stand for?" checks recall, not security thinking. A useful STRIDE exercise asks, "This build path lets a contributor change a workflow and publish an image; which STRIDE categories apply, what evidence would reveal the issue, and which mitigation closes the most important gap?"

STRIDE categories can overlap, and that is acceptable. A compromised CI token may involve Spoofing because the attacker acts as the CI system, Tampering because the image is changed, Repudiation because logs may not identify the actor, and Elevation of Privilege because the image reaches a powerful runtime identity. The goal is not to put each incident into one perfect box. The goal is to make sure the model asks enough different questions.

---

## Supply Chain Trust Boundaries

A trust boundary is a point where data, code, credentials, or artifacts move from one security context to another. Boundaries matter because the receiving side must decide whether to trust what arrived. If that decision is automatic and unevidenced, the boundary becomes a good place for an attacker to operate.

In a Kubernetes supply chain, boundaries appear before the cluster sees anything. The developer laptop, source repository, CI system, build runner, package registry, image registry, admission controller, and runtime environment all have different owners and different security assumptions. A mature threat model names those assumptions instead of hiding them inside a generic "CI/CD" box.

```text
+--------------------------------------------------------------------------------+
|                         SUPPLY CHAIN TRUST BOUNDARIES                          |
+--------------------------------------------------------------------------------+
|                                                                                |
|  Developer        Source Repo          Build System          Image Registry     |
|      |                 |                    |                      |            |
|      | Boundary 1      | Boundary 2         | Boundary 3           |            |
|      v                 v                    v                      v            |
|  Commit push ---> Pull request ---> Build and sign image ---> Store artifact    |
|                                                                                |
|  Boundary 1: Developer -> Source Repo                                          |
|    Risk: stolen credentials, compromised workstation, unreviewed source.        |
|    Control: MFA, signed commits, branch protection, required review.           |
|    Evidence: commit signature, review record, protected branch settings.       |
|                                                                                |
|  Boundary 2: Source Repo -> Build System                                       |
|    Risk: malicious workflow, dependency confusion, unsafe build context.        |
|    Control: protected workflow files, pinned dependencies, isolated builders.  |
|    Evidence: provenance showing source commit, builder identity, parameters.   |
|                                                                                |
|  Boundary 3: Build System -> Image Registry                                    |
|    Risk: tag overwrite, image tampering, stolen push credential.               |
|    Control: immutable tags, digest references, image signing, short tokens.    |
|    Evidence: signature, registry audit log, immutable digest, transparency log.|
|                                                                                |
|  Image Registry       Admission Control       Runtime                          |
|        |                    |                    |                              |
|        | Boundary 4         | Boundary 5         |                              |
|        v                    v                    v                              |
|  Image pull -----> Policy decision -----> Running workload                      |
|                                                                                |
|  Boundary 4: Registry -> Cluster                                               |
|    Risk: cluster pulls the wrong image, an old image, or an unsigned image.     |
|    Control: allowed registries, signature verification, SBOM requirements.     |
|    Evidence: admission decision, digest, attestation, vulnerability status.     |
|                                                                                |
|  Boundary 5: Admission -> Runtime                                              |
|    Risk: accepted workload behaves maliciously or receives excessive access.   |
|    Control: NetworkPolicy, RBAC, seccomp, AppArmor, runtime detection.         |
|    Evidence: audit logs, Falco alerts, network telemetry, service account use. |
|                                                                                |
+--------------------------------------------------------------------------------+
```

The important design habit is to connect each boundary to a verification question. At the developer-to-source boundary, ask whether the repository can prove who changed the code. At the source-to-build boundary, ask whether the build system can prove what input it used. At the build-to-registry boundary, ask whether the registry can prove the image was not replaced. At the registry-to-cluster boundary, ask whether admission can prove the artifact meets policy. At runtime, ask whether the workload can damage other assets if earlier verification fails.

Verification should be independent when possible. If the same compromised CI system both creates the image and controls the only evidence that the image is safe, then the model relies on a circular claim. Stronger designs use isolated builders, short-lived identities, protected workflow definitions, transparency logs, and admission policies that inspect signed attestations rather than trusting a tag alone.

| Boundary | Weak Assumption | Stronger Question | Example Mitigation |
|---|---|---|---|
| Developer to Source | "The commit is in Git, so it is legitimate." | Can we prove the actor and require review for sensitive paths? | MFA, signed commits, CODEOWNERS, protected branches. |
| Source to Build | "CI ran, so the build is trustworthy." | Can we prove the workflow, commit, builder, and dependency inputs? | SLSA-style provenance, pinned actions, isolated runners. |
| Build to Registry | "The tag name is correct." | Can we prove this digest is the approved artifact? | Immutable tags, digest pinning, signing, registry audit logs. |
| Registry to Cluster | "It came from our registry." | Does the artifact satisfy policy for this namespace and workload? | Admission checks for signatures, attestations, SBOMs, and CVEs. |
| Admission to Runtime | "It passed admission, so it is safe forever." | What limits reduce blast radius if the artifact is malicious? | NetworkPolicy, least-privilege RBAC, runtime monitoring, Pod Security Standards. |

**Worked example:** A team deploys `payments-api:stable` from a private registry. The image is signed, but the registry allows tag overwrite, and admission verifies only that the tag points to a signed image. An attacker with stolen registry credentials pushes a malicious image to the same tag after approval. The signature check still passes if the attacker can sign or if the registry accepts a previously signed artifact under the tag.

The fix is not "use more scanning" as the first move. The boundary failure is Build-to-Registry and Registry-to-Cluster. The team should use immutable tags, deploy by digest, restrict registry push permissions, audit registry writes, and have admission verify the digest and provenance policy. Runtime controls still matter, but they reduce blast radius after the wrong artifact has already crossed the boundary.

---

## Provenance, SBOMs, and Attestations

Provenance answers where an artifact came from and how it was produced. In a supply chain model, provenance is evidence for a claim. It can connect a running image digest back to a source repository, commit, workflow, builder identity, build parameters, and timestamp.

An SBOM, or Software Bill of Materials, answers a different question: what is inside the artifact? It lists packages, versions, and often transitive dependencies. Provenance and SBOMs complement each other. Provenance says how the artifact was made; an SBOM says what ingredients it contains.

An attestation is a signed statement about an artifact. For example, an attestation might state that image digest `sha256:...` was built from a specific commit by a specific CI workflow, or that a vulnerability scan completed with no critical findings. Admission policy can then evaluate that signed statement instead of trusting a mutable label or a human claim.

```text
+-------------------------------------------------------------------+
|                         PROVENANCE CHAIN                          |
+-------------------------------------------------------------------+
|                                                                   |
|  Weak claim:                                                      |
|    "This image is named registry.example.com/payments:prod."       |
|                                                                   |
|  Stronger claim:                                                  |
|    "This exact digest was built by the protected release workflow  |
|     from commit abc123 on the main branch using an isolated        |
|     builder, and the statement was signed by the CI identity."     |
|                                                                   |
|  Provenance evidence answers:                                     |
|    WHO built it?        CI identity or builder service account.    |
|    WHAT source?         Repository URL, branch, commit SHA.        |
|    HOW was it built?    Workflow, build command, builder image.    |
|    WHEN was it built?   Timestamp and build run identifier.        |
|    WHERE was it built?  Trusted builder, runner, or build service. |
|    WHY trust it?        Signature, policy match, immutable log.    |
|                                                                   |
|  SBOM evidence adds:                                              |
|    WHAT is inside?      Packages, versions, licenses, dependencies.|
|                                                                   |
+-------------------------------------------------------------------+
```

The senior-level point is that evidence must be policy-relevant. A signed attestation that says "CI built this image" may be too weak if any branch can trigger the same CI identity. A stronger policy might require the protected release workflow, the main branch, a reviewed commit, an approved builder, and no critical vulnerabilities with available fixes. The threat model should define which claims matter for the workload's risk level.

Provenance is also not a replacement for runtime security. A perfectly traceable image can still contain a vulnerable library, a dangerous application bug, or a legitimate feature that leaks sensitive data when misconfigured. Provenance helps the team decide whether the artifact is authentic and accountable; it does not prove the artifact is harmless.

**Pause and predict:** Your pipeline signs every image, but the same CI workflow signs images from feature branches and protected release branches. A developer account is compromised and pushes a feature branch that builds a backdoored image. What should admission verify besides the signature?

The stronger answer is that admission should verify the signed provenance claims, not only the cryptographic signature. It should check the source repository, branch or tag policy, workflow identity, builder identity, and possibly whether required reviews happened before the release. A signature proves that a key signed something; policy decides whether that signed thing is acceptable for this namespace.

| Evidence Type | Question It Answers | What It Does Not Prove by Itself |
|---|---|---|
| Image signature | Was this digest signed by a trusted identity? | That the source was reviewed, safe, or built from an approved branch. |
| Provenance attestation | Which source, workflow, and builder produced this artifact? | That the dependencies are free of vulnerabilities or malicious behavior. |
| SBOM | Which packages and versions are present in the artifact? | That the package behavior is safe or that the build was not tampered with. |
| Vulnerability scan | Are known vulnerabilities present under the scanner's database? | That unknown vulnerabilities or malicious logic are absent. |
| Registry audit log | Who pushed, deleted, or retagged artifacts? | That the artifact content itself is trustworthy. |

---

## Policy Gates at the Cluster Boundary

Admission control is where Kubernetes can enforce many supply chain decisions before a pod starts. This boundary is powerful because the API server has the full pod request and can reject workloads that violate policy. It is also risky because policy gaps become production gaps if the team assumes admission checks more than it actually checks.

A policy gate should match the threat model. If the threat is tag overwrite, the gate should require immutable digests or verify that tags resolve to approved digests. If the threat is untrusted builds, the gate should verify provenance from a trusted builder. If the threat is unknown dependencies, the gate should require an SBOM and recent scan result. If the threat is post-admission abuse, the gate should also enforce runtime constraints such as non-root users, dropped capabilities, and seccomp profiles.

```text
+--------------------------------------------------------------------+
|                         POLICY GATE MODEL                          |
+--------------------------------------------------------------------+
|                                                                    |
|  Pod creation request                                              |
|          |                                                         |
|          v                                                         |
|  +-------------------+    fail -> image is not from an allowed      |
|  | Registry policy   |            registry or required repository   |
|  +---------+---------+                                             |
|            | pass                                                   |
|            v                                                       |
|  +-------------------+    fail -> image reference is mutable or      |
|  | Digest policy     |            digest does not match approval     |
|  +---------+---------+                                             |
|            | pass                                                   |
|            v                                                       |
|  +-------------------+    fail -> digest lacks trusted signature     |
|  | Signature policy  |            from an accepted identity          |
|  +---------+---------+                                             |
|            | pass                                                   |
|            v                                                       |
|  +-------------------+    fail -> provenance does not match source,  |
|  | Attestation check |            branch, workflow, or builder       |
|  +---------+---------+                                             |
|            | pass                                                   |
|            v                                                       |
|  +-------------------+    fail -> critical vulnerability, missing    |
|  | SBOM and scan     |            SBOM, or stale scan evidence       |
|  +---------+---------+                                             |
|            | pass                                                   |
|            v                                                       |
|  +-------------------+    fail -> privileged pod, broad identity,    |
|  | Runtime hardening |            missing seccomp, unsafe volume     |
|  +---------+---------+                                             |
|            | pass                                                   |
|            v                                                       |
|      Pod admitted                                                  |
|                                                                    |
+--------------------------------------------------------------------+
```

Tools such as Kyverno, OPA Gatekeeper, Ratify, Connaisseur, and Sigstore-related components can implement parts of this model. KCSA does not require deep vendor-specific operation, but it does expect you to understand the control pattern. The cluster receives a request, evaluates evidence and policy, and either rejects the workload or allows it to run under defined constraints.

The strongest policy is not always the best first policy. A platform team may begin in audit mode, measure violations, fix build pipelines, and then move critical namespaces to enforce mode. That staged approach can be more effective than immediately blocking every team without giving them a migration path. The threat model should still be honest about residual risk during audit mode.

Here is a small runnable example showing the kind of pod property a policy engine might reject. This command creates a local manifest file and uses `kubectl` client-side validation to confirm the YAML is structurally valid. In a real cluster, an admission controller would decide whether the image policy, security context, and namespace rules are acceptable.

```bash
cat > unsafe-pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: unsigned-mutable-image
  namespace: default
spec:
  containers:
    - name: app
      image: docker.io/library/nginx:latest
      securityContext:
        runAsUser: 0
        allowPrivilegeEscalation: true
EOF

kubectl apply --dry-run=client -f unsafe-pod.yaml
```

After `kubectl` has been introduced, KubeDojo examples often use the alias `k` for speed. If you use it locally, define it explicitly with `alias k=kubectl` before running commands. The alias does not change Kubernetes behavior; it only shortens command entry during practice.

```bash
alias k=kubectl
k apply --dry-run=client -f unsafe-pod.yaml
```

A policy-focused threat model would not merely say "reject this pod because it is bad." It would explain that `latest` is a mutable tag, `docker.io/library` may not be an approved registry for production, `runAsUser: 0` means the process runs as root, and `allowPrivilegeEscalation: true` increases the impact if the image is compromised. That explanation links policy to risk.

| Policy Gate | Threat Reduced | Example Rejection Reason | Owner |
|---|---|---|---|
| Allowed registries | Pulling artifacts from untrusted sources | Image must come from `registry.example.com/prod`. | Platform |
| Digest requirement | Tag overwrite or accidental drift | Workload must reference `@sha256:` digest for production. | Platform |
| Signature verification | Unsigned or tampered artifact | Image digest lacks signature from trusted release identity. | Security |
| Provenance verification | Build from wrong branch or workflow | Attestation does not show protected release workflow. | Security and Platform |
| SBOM requirement | Unknown dependencies in production | No SBOM attestation exists for this image digest. | Security |
| Runtime hardening | Increased blast radius after compromise | Pod must run as non-root and disallow privilege escalation. | Platform |

---

## Worked Example: Modeling a Payment Service

A worked example turns the framework into a repeatable method. Imagine a team deploying a payment service to Kubernetes. The service handles payment tokens, talks to an external payment processor, stores transaction records, and is deployed through a CI pipeline to a private registry. The security question is not "Which tool should we buy?" The security question is "Where could a trusted path become dangerous?"

Start with assets. The most obvious asset is payment data, but the supply chain view adds less obvious assets: source code, workflow definitions, image signing identity, registry permissions, service account tokens, and provenance records. If an attacker can change the workflow that creates the image, the attacker may not need direct database access at first.

```text
+--------------------------------------------------------------------------------+
|                         PAYMENT SERVICE THREAT MODEL                           |
+--------------------------------------------------------------------------------+
|                                                                                |
|  Business assets:                                                              |
|    Payment tokens, customer identifiers, transaction logs, refund workflow.     |
|                                                                                |
|  Platform assets:                                                              |
|    Kubernetes service account, namespace policies, database Secret, API key.    |
|                                                                                |
|  Supply chain assets:                                                          |
|    Source repository, CI workflow, build runner, signing identity, registry.    |
|                                                                                |
|  Delivery flow:                                                                |
|                                                                                |
|    Developer -> Pull Request -> Protected Branch -> CI Build -> Registry        |
|         |             |                 |              |             |          |
|         |             |                 |              |             v          |
|         |             |                 |              |        Admission       |
|         |             |                 |              |             |          |
|         |             |                 |              |             v          |
|         +-------------+-----------------+--------------+------> Running Pod     |
|                                                                    |           |
|                                                                    v           |
|                    User -> Ingress -> payment-api -> PostgreSQL -> Processor   |
|                                                                                |
|  Key trust boundaries:                                                         |
|    1. Developer identity to source repository.                                  |
|    2. Source repository to build system.                                        |
|    3. Build system to registry and signing service.                             |
|    4. Registry to admission controller.                                         |
|    5. Admitted pod to database, network, and cloud identity.                    |
|                                                                                |
+--------------------------------------------------------------------------------+
```

Now apply STRIDE to create abuse cases. For Tampering, an attacker changes a build step to add a credential exfiltration binary before the image is signed. For Spoofing, the attacker publishes a package that looks like an internal payment helper package. For Information Disclosure, the application logs payment processor tokens during error handling. For Elevation of Privilege, the pod uses a service account that can read Secrets in other namespaces.

The next step is to match controls to the specific abuse case. A vulnerability scanner may not detect a malicious workflow change if the added code has no known CVE. Signed images may not help if the compromised workflow signs the malicious image. NetworkPolicy may not prevent the image from being admitted, but it can reduce exfiltration after admission. Each control has a role, and no single control carries the full argument.

| Abuse Case | STRIDE Category | Boundary | Better Mitigation |
|---|---|---|---|
| Attacker changes CI workflow to add backdoor before image signing. | Tampering and Repudiation | Source to Build | Protected workflow files, required review, isolated builder, provenance verification. |
| Public package shadows an internal package during build. | Spoofing and Tampering | Source to Build | Registry scoping, lockfiles, dependency review, private package repository. |
| Registry tag is overwritten after release approval. | Tampering | Build to Registry | Immutable tags, digest deployments, registry audit logs, admission digest checks. |
| Pod reads database Secret and sends it to external endpoint. | Information Disclosure | Admission to Runtime | Least-privilege Secret mounts, egress NetworkPolicy, runtime detection. |
| Compromised app service account lists Secrets across namespaces. | Elevation of Privilege | Runtime to Cluster API | Namespace-scoped RBAC, separate service accounts, audit alerts. |
| Malicious dependency causes every replica to consume CPU. | Denial of Service | Code to Runtime | Resource limits, rollout strategy, dependency scanning, canary deployment. |

A good mitigation table includes owners because unowned mitigations are wishes. Platform might own admission policy and namespace defaults. Security might own signing policy, vulnerability criteria, and detection. Application teams might own dependency updates, code review, and safe logging. Cloud teams might own workload identity and cloud IAM scope.

| Threat | Mitigation | Owner | Residual Risk |
|---|---|---|---|
| Workflow tampering before signing | Require review for workflow files and verify protected release provenance at admission. | Platform | CI provider compromise remains possible and is reviewed during vendor risk assessment. |
| Dependency confusion | Use registry scoping, lockfiles, and private package namespaces for internal packages. | Application | Malicious update from a legitimate maintainer can still occur. |
| Tag overwrite | Deploy by digest and enable immutable tags for release repositories. | Platform | Emergency rollback process must still avoid mutable shortcuts. |
| Secret exfiltration from compromised pod | Restrict Secret mounts, apply egress NetworkPolicy, and alert on unusual DNS or HTTP destinations. | Platform and Security | Approved payment processor egress could still be abused without application-level detection. |
| Overbroad service account | Bind only required verbs and resources in the namespace. | Platform | New features may need review to avoid permission creep. |
| Critical vulnerability in base image | Scan in CI and require recent scan evidence before admission. | Security | Unknown vulnerabilities require patch process and runtime constraints. |

The finished threat model should tell a coherent story. If the payment service is compromised through a dependency, the model explains how that dependency entered, which boundary failed, what the workload could access, how the team might detect the behavior, which mitigation reduces recurrence, and which residual risk remains. That is much stronger than a diagram that only lists "signed images, scanning, RBAC."

---

## Building a Practical Threat Model

A practical threat model is small enough to maintain and specific enough to guide decisions. A team does not need to model every Kubernetes object in the cluster on the first pass. For KCSA-level reasoning, start with one workload and its delivery path, then expand to shared platform components such as admission webhooks, registries, DNS, and CI runners.

The first pass should define scope. For example, "This model covers the `payments` namespace, its deployment pipeline, its image registry path, its database access, and its external payment processor egress." Scope prevents endless discussion and makes residual risk visible. Out-of-scope items are acceptable only when they are named and reviewed later.

The second pass should identify assumptions. Security incidents often exploit assumptions that were never written down. Examples include "only maintainers can change workflows," "the signing key cannot be used outside CI," "tags are immutable," "all production images come from the private registry," and "pods cannot reach cloud metadata." Each assumption should be testable.

The third pass should turn assumptions into evidence. If the team assumes tags are immutable, show the registry setting or audit rule. If the team assumes the signing key is protected, show how the key is managed or replaced with keyless signing. If the team assumes the pod cannot reach the metadata service, test network behavior or review cloud provider configuration.

| Modeling Step | Output | Quality Check |
|---|---|---|
| Scope the model | Workload, namespace, pipeline, registry, identities, and external dependencies. | Could another engineer tell what is included and excluded? |
| Identify assets | Data, credentials, artifacts, source, build definitions, policies, logs. | Does the list include supply chain assets, not only runtime data? |
| Map flows | Commit path, build path, deployment path, request path, secret path. | Are trust boundaries marked where ownership or security context changes? |
| Create abuse cases | STRIDE-based scenarios tied to boundaries and assets. | Could a reviewer understand how the attacker succeeds? |
| Choose mitigations | Controls, owners, evidence, rollout state, and residual risk. | Does every major control map to a specific threat? |
| Review triggers | Events that require updating the model. | Would a new registry, CI system, or sensitive feature trigger review? |

Do not confuse a threat model with a compliance checklist. A checklist can ask whether image scanning is enabled. A threat model asks whether image scanning would catch the abuse case under discussion, whether admission uses the scan result, whether the scan result is recent, and what happens if the scanner misses malicious behavior. This deeper reasoning is where the teaching value sits.

A threat model should be updated when the system changes. New ingress paths, new service accounts, new CI workflows, new package registries, new admission exceptions, and new data classifications all change the model. A stale threat model can become actively misleading because it preserves old assumptions after the system has moved on.

---

## Mitigation Matrix

The following matrix maps common Kubernetes and supply chain threats to the layer where the risk often appears, the kind of mitigation that helps, and the owner who typically needs to act. Treat it as a starting point, not a universal answer. Your cluster, organization, and risk tolerance may shift ownership and priority.

| Threat | 4C Layer | Mitigation | Owner |
|---|---|---|---|
| Compromised admission webhook mutates workloads into unsafe forms. | Cluster | Isolate webhook namespace, use mTLS, restrict RBAC, audit changes, and prefer fail-closed behavior for critical policy. | Platform |
| Registry poisoning or tag overwrite changes a trusted application image. | Code and Container | Use immutable tags, digest references, image signing, registry audit logs, and admission digest verification. | Platform and Security |
| Node or container escape expands a compromised image into host access. | Container | Enforce Pod Security Standards, seccomp, AppArmor, dropped capabilities, non-root users, and read-only root filesystems. | Platform |
| Stolen kubeconfig gives an attacker direct API server access. | Cluster | Use short-lived credentials, OIDC login, MFA, least-privilege RBAC, and audit alerting for unusual verbs. | Security |
| Malicious dependency enters during build and runs inside an approved image. | Code | Use lockfiles, private registries, dependency review, SBOM generation, and provenance-aware admission. | Application and Security |
| CI/CD credential theft lets an attacker build or publish artifacts. | Code and Cluster | Use ephemeral runners, OIDC federation, short-lived tokens, protected workflows, and scoped registry permissions. | Platform |
| etcd data exposure reveals Kubernetes Secrets and configuration. | Cluster | Enable encryption at rest, restrict etcd access, require mTLS, and limit control plane network exposure. | Platform |
| Cloud metadata service abuse turns a pod compromise into cloud account access. | Cloud | Use workload identity, metadata concealment or IMDS restrictions, narrow IAM roles, and egress controls. | Cloud and Platform |
| Overbroad service account lets a compromised pod read unrelated resources. | Cluster | Bind minimal verbs and resources, separate service accounts by workload, and audit privilege creep. | Platform |
| Missing audit trail prevents incident reconstruction after a suspicious deployment. | Cluster and Code | Retain API audit logs, CI logs, registry logs, signed provenance, and deployment history. | Security |

A mitigation matrix is useful only if it drives action. The team should review which rows apply to the modeled workload, which controls are already enforced, which are only documented, and which are accepted residual risk. The difference between "we plan to require signed images" and "admission rejects unsigned images in production namespaces" should be explicit.

---

## Did You Know?

- **SolarWinds showed the leverage of build compromise**: attackers reached many downstream environments because the trusted update path became the delivery mechanism, which is exactly why supply chain modeling focuses on trust boundaries before runtime.

- **SLSA focuses on build integrity**: the framework helps teams reason about tamper resistance, provenance, and build platform trust, which are central questions when admission policy depends on artifact evidence.

- **SBOMs are evidence, not magic protection**: an SBOM can reveal what is inside an image, but teams still need policies, scanning, review, and response processes to turn that inventory into reduced risk.

- **Kubernetes admission is a decision point**: by the time a pod reaches runtime, the cluster has already made trust decisions about images, identities, policies, and namespaces, so admission design strongly shapes supply chain defense.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Practice |
|---|---|---|
| Modeling only the running cluster and ignoring CI/CD | Supply chain attacks often succeed before the pod exists, so runtime-only models miss the compromised path. | Include source, workflow, build runner, registry, signing, admission, and runtime in the model. |
| Treating signed images as automatically safe | A compromised build system can sign malicious images if policy checks only the signature. | Verify provenance claims such as branch, workflow, builder identity, and protected release status. |
| Deploying mutable tags in production | Tags can move, so the running workload may not match the artifact that was reviewed. | Deploy by digest and use immutable release tags where tags are still needed for humans. |
| Writing abuse cases without owners | A threat model with unowned mitigations becomes documentation rather than risk reduction. | Assign each mitigation to a team and record whether it is planned, enforced, or accepted as residual risk. |
| Confusing vulnerability scanning with malware detection | Many malicious changes do not have known CVEs and will not be caught by package vulnerability databases. | Combine scanning with review, provenance, behavior limits, and runtime monitoring. |
| Forgetting residual risk | Teams may believe the system is safe because controls exist, even when important gaps remain. | Document accepted risks, review triggers, compensating controls, and decision owners. |
| Using STRIDE as a memorization checklist | Learners can name categories while still missing how an attacker abuses a real boundary. | Convert each STRIDE category into a scenario tied to an asset, boundary, and Kubernetes object. |
| Leaving admission policies in permanent audit mode | Audit-only policy records violations but does not stop unsafe workloads from running. | Use audit mode for migration, then enforce in production namespaces once teams have a clear path to compliance. |

---

## Quiz

1. **Your team deployed `payments-api` from a private registry, and admission accepted it because the image was signed. Later, security discovers the release workflow signs images from any branch, including unreviewed feature branches. What should you check first, and what policy change best reduces the risk?**

   <details>
   <summary>Answer</summary>

   Check the provenance for the running image digest: source repository, branch, workflow identity, builder identity, and build trigger. The signature proves that a trusted identity signed the image, but it does not prove the image came from an approved release path. The best policy change is to make admission verify signed provenance claims, such as protected branch or release tag, approved workflow, and trusted builder, instead of accepting any image signed by the CI system.

   </details>

2. **Your team deployed a service using `registry.example.com/orders:stable`. During an incident, the digest behind `stable` differs from the digest recorded in the release ticket. What trust boundary failed, and what would you change before the next deployment?**

   <details>
   <summary>Answer</summary>

   The Build-to-Registry or Registry-to-Cluster boundary failed because a mutable tag allowed the artifact reference to drift after review. Before the next deployment, require production workloads to reference images by digest, enable immutable tags for release repositories, restrict push permissions, and make admission verify that the requested digest matches policy and provenance evidence. Scanning alone does not fix the identity problem because the wrong artifact may still be scanned and admitted.

   </details>

3. **Your team deployed a logging sidecar update, and pods across several namespaces begin sending DNS queries to an unknown external domain. The image passed vulnerability scanning and came from the approved registry. Which parts of the threat model help you respond?**

   <details>
   <summary>Answer</summary>

   Start with the Code and Registry-to-Cluster boundaries, then move to runtime blast radius. Check provenance for the sidecar image, recent dependency changes, registry audit logs, and admission evidence. Then inspect runtime controls: egress NetworkPolicies, service account permissions, DNS logs, and Falco or audit events. The scenario shows why an approved registry and vulnerability scan are not enough; malicious behavior may have no known CVE and still need network limits and runtime detection.

   </details>

4. **Your team deployed a new CI workflow that builds images for pull requests and production releases. A contributor can modify the workflow file in the same pull request that triggers the build. Which STRIDE categories apply, and what mitigation would you prioritize?**

   <details>
   <summary>Answer</summary>

   Tampering applies because the workflow can be changed to alter the build. Repudiation applies if the resulting artifact lacks trustworthy evidence about the workflow and actor. Elevation of Privilege may apply if the workflow can access signing or registry credentials. Prioritize protecting workflow files with required review or CODEOWNERS, separating pull request builds from release signing, using short-lived scoped credentials, and verifying provenance at admission.

   </details>

5. **Your team deployed an application with a narrow container security context, but the pod service account can list and read Secrets in every namespace. A malicious dependency is later discovered in the image. What should the threat model say about blast radius?**

   <details>
   <summary>Answer</summary>

   The container hardening reduces some host-level risks, but the overbroad service account creates a Cluster-layer blast radius. The model should record that a Code-layer compromise can use the pod's Kubernetes identity to disclose Secrets across namespaces. The immediate fix is least-privilege RBAC with a workload-specific service account, plus audit alerts for unusual Secret access. Runtime hardening and supply chain verification remain useful, but they do not compensate for broad API permissions.

   </details>

6. **Your team deployed admission policy that requires an SBOM attestation for every production image. A critical incident still occurs because a legitimate dependency version contains intentionally malicious behavior that had no known CVE. What conclusion should the team draw?**

   <details>
   <summary>Answer</summary>

   The team should conclude that SBOMs improve visibility but do not prove safe behavior. The SBOM can show which dependency version was present and help response teams find affected workloads, but it may not prevent a novel malicious package from running. The threat model should combine SBOM requirements with dependency review, registry controls, provenance, least-privilege runtime design, egress restrictions, and monitoring for suspicious behavior.

   </details>

7. **Your team deployed a policy in audit mode that reports unsigned images but does not block them. A production namespace still runs several unsigned workloads after two months. How should you evaluate this control in the threat model?**

   <details>
   <summary>Answer</summary>

   Record the control as detective rather than preventive while it remains in audit mode. The residual risk is that unsigned or unverified images can still run in production, so the model should not claim signature enforcement as a mitigation. A reasonable next step is to set a deadline, fix violating pipelines, communicate exceptions, and move production namespaces to enforce mode with a documented break-glass process.

   </details>

8. **Your team deployed a payment service that can reach the cloud metadata service from its pod network. The application image is signed, scanned, and built from protected branches. Why is the threat model still incomplete, and which layer needs attention?**

   <details>
   <summary>Answer</summary>

   The model is incomplete because it focuses on artifact trust but not runtime consequences after compromise. Even a well-built image can contain an unknown vulnerability or application bug. If the pod can reach metadata credentials with broad cloud permissions, a Container or Code-layer compromise can become a Cloud-layer incident. The team should restrict metadata access, use scoped workload identity, narrow IAM permissions, and monitor unusual cloud API calls from the workload identity.

   </details>

---

## Hands-On Exercise: Build and Review a Supply Chain Threat Model

**Task:** Create a threat model for an e-commerce application running on Kubernetes, then review it as if you were the security reviewer deciding whether the service can move to production.

**Scenario:** The application has three services: `frontend` written in TypeScript, `api` written in Go, and `worker` written in Python. The team uses GitHub Actions for CI/CD, builds images with a shared runner, pushes images to a private ECR registry, and deploys to an EKS cluster using GitOps. The application stores customer profile data in PostgreSQL and calls an external payment provider.

### Step 1: Define Scope and Assets

Write a short scope statement that names the workload, namespace, pipeline, registry, cloud environment, and external dependencies included in your model. Then list at least eight assets that need protection, including at least three supply chain assets.

Example assets might include customer profile data, payment provider API tokens, PostgreSQL credentials, GitHub Actions workflow files, build runner identity, image signing identity, ECR image digests, GitOps repository manifests, Kubernetes service accounts, and audit logs. The goal is to include the path that creates the workload, not only the workload after it is running.

Success criteria:

- [ ] Your scope statement names what is included and what is out of scope.
- [ ] Your asset list includes business data, Kubernetes identities, and supply chain artifacts.
- [ ] At least three assets are from the delivery path before runtime.

### Step 2: Map Data and Artifact Flows

Draw a flow from developer change to running pod, and include the runtime request path. Use text or ASCII art. Mark at least five trust boundaries where ownership, identity, or verification changes.

Your flow should include developer workstation, source repository, pull request, CI workflow, build runner, package registry, image registry, GitOps repository, Kubernetes admission, running pods, database, and payment provider. You may simplify names, but do not collapse the entire delivery path into one "CI/CD" box.

Success criteria:

- [ ] Your flow includes both software delivery and runtime request paths.
- [ ] You mark at least five trust boundaries.
- [ ] Each boundary has a short note describing what must be verified there.

### Step 3: Create STRIDE Abuse Cases

Create at least six abuse cases using STRIDE. Each abuse case must name the asset, boundary, attacker action, likely impact, and one or more controls. Avoid generic statements such as "attacker hacks the cluster." Make each scenario specific enough that a platform or security engineer could investigate it.

Use this structure:

| Abuse Case | STRIDE | Boundary | Impact | Candidate Control |
|---|---|---|---|---|
| Contributor modifies release workflow to inject a backdoor before signing. | Tampering | Source to Build | Signed malicious image reaches production. | Protected workflows, required review, provenance admission. |

Success criteria:

- [ ] You include at least six abuse cases.
- [ ] At least four STRIDE categories are represented.
- [ ] Every abuse case maps to a boundary and an asset.
- [ ] Every control addresses the scenario rather than being a generic tool name.

### Step 4: Build a Mitigation and Ownership Table

Turn your abuse cases into an implementation table. Include owner, current status, verification evidence, and residual risk. Use realistic statuses such as `Enforced`, `Audit`, `Planned`, or `Accepted`.

Success criteria:

- [ ] Every high-impact abuse case has an owner.
- [ ] At least one mitigation is preventive, one is detective, and one reduces blast radius.
- [ ] You document residual risk for at least three threats.
- [ ] You identify at least two review triggers, such as a new registry, new CI runner, new payment feature, or new namespace exception.

### Step 5: Review the Model Like a Security Reviewer

Read your own model and answer these questions in writing. Where does the model rely on a single system to both create trust and prove trust? Which controls are still in audit mode? Which assumption would be most damaging if false? Which mitigation would you implement first if you had only one sprint?

Success criteria:

- [ ] You identify the weakest trust boundary in your design.
- [ ] You explain why your top mitigation is the best first investment.
- [ ] You name one control that helps admission and one control that helps after admission.
- [ ] You can explain the difference between artifact evidence and runtime blast-radius reduction.

---

## Next Module

[Module 5.1: Image Security](/k8s/kcsa/part5-platform-security/module-5.1-image-security/)
