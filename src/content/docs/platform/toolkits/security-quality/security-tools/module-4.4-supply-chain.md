---
title: "Module 4.4: Supply Chain Security"
slug: platform/toolkits/security-quality/security-tools/module-4.4-supply-chain
sidebar:
  order: 5
---

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 60-75 minutes
>
> **Prerequisites**: [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/), container image basics, CI/CD pipeline concepts, and basic Kubernetes admission control terminology.
>
> **Tools used**: Cosign, Sigstore, Syft, Trivy, Harbor, Kyverno, and GitHub Actions examples.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a layered supply chain security pipeline that protects source, dependencies, builds, registries, and Kubernetes admission.
- **Implement** image signing, SBOM generation, vulnerability scanning, and evidence attachment using practical open source tooling.
- **Evaluate** when to use keyless signing, key-based signing, registry policy, and admission control for different operating environments.
- **Debug** common supply chain failures such as mutable tags, missing provenance, stale SBOMs, unsigned images, and noisy vulnerability gates.
- **Compare** SLSA, in-toto, SBOMs, signatures, and registry controls as complementary evidence rather than interchangeable security badges.

---

## Why This Module Matters

A platform team can harden every Kubernetes cluster and still deploy compromised software if the build pipeline is trusted blindly. The SolarWinds supply-chain compromise <!-- incident-xref: solarwinds-2020 --> showed that a signed artifact is only trustworthy when the path that created it is also controlled, observable, and independently verifiable. For the canonical case study, see [CI/CD Pipelines](../../../../prerequisites/modern-devops/module-1.3-cicd-pipelines/).

A second class of failures comes from dependencies rather than build systems. Log4Shell <!-- incident-xref: log4shell --> showed how one vulnerable library can create emergency work across thousands of teams that never wrote a line of logging framework code. For the canonical Log4Shell case study, see [DevSecOps Supply Chain Security](../../../disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/).

Supply chain security is the discipline of replacing vague trust with evidence. You are not trying to make developers memorize a separate security ceremony for every release. You are designing a path where normal delivery produces verifiable artifacts: images identified by digest, signatures tied to real identities, SBOMs attached to the artifact, vulnerability results stored with the build, provenance that explains how the artifact was produced, and admission policies that reject deployments when that evidence is missing or inconsistent.

---

## 1. Map the Supply Chain Before Adding Tools

The first mistake in supply chain security is starting with a scanner or a signing command before you know what you are protecting. A modern delivery path has several trust boundaries, and each boundary answers a different question. Source control answers who changed the code, dependency management answers what entered the build, the CI system answers how the artifact was produced, the registry answers which bytes are being distributed, and admission control answers what is allowed to run.

```text
SOFTWARE SUPPLY CHAIN ATTACK SURFACE
====================================================================

    Developer      Dependencies      Build          Registry       Runtime
    ---------      ------------      -----          --------       -------
        |               |              |                |              |
        v               v              v                v              v
    +---------+    +-----------+    +-----------+    +----------+    +---------+
    | Laptop  |    | npm, PyPI |    | CI runner |    | OCI      |    | K8s     |
    | token   |    | base      |    | workflow  |    | registry |    | cluster |
    | theft   |    | image     |    | injection |    | tag swap |    | policy  |
    +---------+    +-----------+    +-----------+    +----------+    +---------+

DEFENSES AT EACH STAGE
--------------------------------------------------------------------

Developer:     MFA, least-privilege tokens, reviewed commits, protected branches
Dependencies:  lock files, private mirrors, SBOMs, vulnerability scanning
Build:         ephemeral runners, pinned actions, provenance, isolated secrets
Registry:      immutable tags, digest promotion, signatures, malware scanning
Runtime:       admission control, signature verification, SBOM-aware exceptions
```

A useful mental model is an airport security chain. A passport alone does not prove the suitcase is safe, and a luggage scan does not prove the traveler is authorized. Each checkpoint contributes a different kind of evidence, and the later checkpoints should not silently ignore missing evidence from earlier ones. In software, a signature proves that an identity signed a particular artifact, but it does not prove the source code was reviewed, the dependencies were patched, or the build runner was clean.

Supply chain evidence should be designed around the questions responders need during an incident. If a new critical vulnerability appears, you need to find affected components across images. If a registry tag is overwritten, you need to know which immutable digest was deployed. If a CI credential is stolen, you need to identify artifacts produced during the exposure window and decide whether to revoke trust in them. Good tooling supports those investigations because it records decisions at build time instead of forcing teams to reconstruct history later.

> **Pause and predict:** If an attacker can overwrite `myapp:latest` in a registry after an image was scanned, which downstream controls still protect you and which controls become misleading? Write down your answer before reading the next paragraph, because this single scenario explains why digest-based promotion matters.

Tags are human-friendly pointers, not stable artifact identities. A scan result for `myapp:latest` describes whatever bytes the tag pointed to when the scan ran, while a later deployment of `myapp:latest` may pull different bytes. A digest such as `sha256:...` identifies immutable content, so signatures, SBOMs, provenance, and deployment records should converge on the digest. Tags still matter for humans and release notes, but policy decisions should be made against immutable identifiers whenever the tooling supports it.

| Supply Chain Stage | Primary Risk | Evidence You Want | Tooling Examples |
|---|---|---|---|
| Source | Malicious or unreviewed changes | branch protection, signed commits, review metadata | GitHub, GitLab, Gitea |
| Dependencies | vulnerable or typosquatted packages | lock files, SBOMs, package provenance | Syft, Dependabot, Renovate |
| Build | compromised runner or workflow injection | build provenance, isolated identity, pinned actions | SLSA generators, GitHub OIDC |
| Registry | overwritten tags or untrusted uploads | immutable digests, signatures, scan reports | Harbor, Cosign, Trivy |
| Runtime | unsigned or unscanned image admitted | admission decision logs and policy results | Kyverno, Ratify, Gatekeeper |

The important design move is to connect these stages without pretending that one control solves all of them. A scanner can identify known vulnerabilities, but it cannot prove who built the image. A signature can prove that a trusted identity signed an artifact, but it cannot prove the artifact is free of vulnerabilities. An SBOM can list components, but it cannot enforce deployment policy by itself. The platform engineer’s job is to build a chain where each control produces evidence that the next control can check.

---

## 2. Establish Artifact Identity with Digests and Signatures

Before you sign anything, make sure you know exactly what the artifact is. In OCI registries, an image digest identifies the content-addressed manifest, while a tag is a movable label. This is why senior teams usually build with a commit tag for traceability, push the image, read back the digest from the registry, and use that digest for signing, attestation, promotion, and deployment.

```text
TAG VERSUS DIGEST
====================================================================

Human workflow:
  developer says "deploy release v1.8.0"

Registry reality:
  ghcr.io/acme/payments:v1.8.0       -> mutable pointer
  ghcr.io/acme/payments@sha256:abcd  -> immutable artifact identity

Policy consequence:
  signatures, SBOMs, provenance, and admission should target the digest
  release notes and dashboards may display the tag for human readability
```

Cosign is the most common command-line tool for signing and verifying OCI artifacts in the Sigstore ecosystem. Sigstore is not one tool; it is a set of services and formats that make software signing easier to adopt. Cosign signs and verifies artifacts, Fulcio issues short-lived certificates for keyless signing, and Rekor records signature metadata in a transparency log so that signatures can be audited later.

```text
SIGSTORE ECOSYSTEM
====================================================================

+------------------------------------------------------------------+
|                            SIGSTORE                              |
|                                                                  |
|  +---------------+      +---------------+      +---------------+ |
|  | Cosign        |      | Fulcio        |      | Rekor         | |
|  | signing and   | ---> | short-lived   | ---> | transparency  | |
|  | verification  |      | certificates  |      | log entries   | |
|  +---------------+      +---------------+      +---------------+ |
|                                                                  |
|  Keyless flow: CI identity proves who it is through OIDC, Fulcio |
|  issues a short-lived certificate, Cosign signs the artifact,     |
|  and Rekor records evidence that can be checked during verify.    |
+------------------------------------------------------------------+
```

Keyless signing is usually the best default for internet-connected CI systems because it avoids long-lived private keys. The build job receives an OIDC identity from the CI platform, Cosign uses that identity to obtain a short-lived certificate, and verification checks that the signer identity and issuer match the expected workflow. This shifts the risk from key storage to CI identity governance, which is usually easier to audit with branch protection, environment rules, and workflow permissions.

Key-based signing is still useful in air-gapped environments, highly regulated deployments, or places where the signing identity must be controlled by an internal certificate authority. The trade-off is operational burden. Someone must generate keys, store private keys safely, rotate them, revoke trust after compromise, and distribute public keys to verifiers. If that lifecycle is weak, key-based signing can create a false sense of security because the ceremony looks formal while the private key is effectively just another shared secret.

```bash
# Install Cosign on macOS when Homebrew is available.
brew install cosign

# Verify the installed command.
cosign version
```

```bash
# Key-based signing for an exercise or an isolated environment.
# Use a registry image that your account is allowed to push and modify.
export IMAGE="ghcr.io/YOUR_ORG/YOUR_APP@sha256:REPLACE_WITH_DIGEST"

cosign generate-key-pair
cosign sign --key cosign.key "$IMAGE"
cosign verify --key cosign.pub "$IMAGE"
```

```bash
# Keyless signing in CI or an authenticated shell with supported identity.
# The identity and issuer must later be checked during verification.
export IMAGE="ghcr.io/YOUR_ORG/YOUR_APP@sha256:REPLACE_WITH_DIGEST"

cosign sign --yes "$IMAGE"

cosign verify "$IMAGE" \
  --certificate-identity="https://github.com/YOUR_ORG/YOUR_REPO/.github/workflows/release.yaml@refs/heads/main" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"
```

Verification is where many teams accidentally weaken the system. A command that merely asks whether an image has any valid signature is less useful than a command that checks the expected identity. In a production pipeline, you usually want to verify that the image was signed by a specific workflow, from a specific organization, through a specific OIDC issuer. Otherwise, an attacker may be able to sign their own image with their own identity and still satisfy a vague “is signed” check.

> **Stop and think:** Your platform allows any image signed by any GitHub Actions workflow to pass admission. A developer from an unrelated public repository signs a malicious image with their own workflow and pushes it to a registry your cluster can reach. Should admission allow it? Explain which field in the verification policy should have prevented that outcome.

A practical signing rollout should begin in report-only mode before it blocks production. First, sign images in CI and collect verification results without enforcing admission. Second, fix missing signatures, identity mismatches, and digest handling. Third, enforce signatures on a narrow set of production namespaces or registries. Finally, expand enforcement once teams have clear failure messages and documented exception paths. This rollout sequence prevents supply chain policy from becoming an unplanned deployment freeze.

---

## 3. Add SBOMs and Vulnerability Scans as Evidence, Not Decoration

An SBOM, or software bill of materials, is an inventory of components inside an artifact. It is most valuable when it is generated from the actual artifact that will be deployed, attached to that artifact, and used during incident response. An SBOM generated from a source directory may be useful during development, but it can miss packages introduced by the base image or build process. For runtime questions, the deployed image is the stronger source of truth.

```text
SBOM FORMATS
====================================================================

+------------------------------------------------------------------+
| SPDX                                                             |
|   Stewarded by the Linux Foundation ecosystem                    |
|   Strong for license and package metadata exchange               |
|   Common encodings include JSON, RDF, and tag-value              |
|                                                                  |
| CycloneDX                                                        |
|   Stewarded by OWASP                                             |
|   Strong for application security and vulnerability workflows    |
|   Common encodings include JSON and XML                          |
|                                                                  |
| Practical rule: choose the format your scanners, risk tools,     |
| registry, and compliance process can consistently consume.        |
+------------------------------------------------------------------+
```

Syft is a common tool for generating SBOMs from container images, filesystems, and directories. Trivy can generate SBOMs too, and it can scan images, filesystems, configuration files, and existing SBOMs. The right choice is less about brand preference and more about where the evidence enters your workflow. If your registry stores CycloneDX attestations and your risk platform consumes CycloneDX, generate CycloneDX consistently. If your legal team depends on SPDX, make sure the SPDX file is produced and retained.

```bash
# Install common tools on macOS when Homebrew is available.
brew install syft trivy

# Generate a CycloneDX SBOM from an image.
export IMAGE="ghcr.io/YOUR_ORG/YOUR_APP@sha256:REPLACE_WITH_DIGEST"
syft "$IMAGE" -o cyclonedx-json > sbom.cdx.json

# Generate an SPDX SBOM from the current directory.
syft . -o spdx-json > sbom.spdx.json

# Generate a CycloneDX SBOM with Trivy when Trivy is the standard scanner.
trivy image --format cyclonedx --output sbom.trivy.cdx.json "$IMAGE"
```

A vulnerability scan compares discovered components against vulnerability databases and applies matching logic. That means the result can change over time even when the artifact does not change, because new CVEs are published and vulnerability metadata is corrected. For release gates, scan at build time to prevent obvious known risks from shipping. For operations, rescan stored SBOMs or deployed image digests on a schedule so you can detect newly disclosed vulnerabilities in already-running software.

```bash
# Scan the image directly.
trivy image --severity HIGH,CRITICAL "$IMAGE"

# Scan the SBOM that was generated from the image.
trivy sbom --severity HIGH,CRITICAL sbom.cdx.json

# Fail CI only for critical vulnerabilities in this example.
trivy image --exit-code 1 --severity CRITICAL "$IMAGE"
```

Attaching the SBOM to the image as an attestation keeps the inventory close to the artifact. This matters because detached files in a build workspace are easy to lose, overwrite, or mismatch with the wrong release. An attestation does not automatically make the SBOM true; it records a signed claim about the artifact. The value comes from generating it in a controlled pipeline, binding it to the digest, and verifying that the attestation was produced by the expected identity.

```bash
# Attach a CycloneDX SBOM as an attestation to the immutable image digest.
export IMAGE="ghcr.io/YOUR_ORG/YOUR_APP@sha256:REPLACE_WITH_DIGEST"

cosign attest --yes \
  --predicate sbom.cdx.json \
  --type cyclonedx \
  "$IMAGE"

# Verify that a CycloneDX attestation exists from the expected identity.
cosign verify-attestation "$IMAGE" \
  --type cyclonedx \
  --certificate-identity="https://github.com/YOUR_ORG/YOUR_REPO/.github/workflows/release.yaml@refs/heads/main" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"
```

The hardest part of vulnerability scanning is not running the scanner; it is choosing gates that create useful pressure without blocking every release indefinitely. A good first gate might block critical vulnerabilities with known fixes in internet-facing services, while reporting high vulnerabilities for review. A stricter gate may be appropriate for base images or shared platform components because they spread risk widely. Exceptions should have owners, expiry dates, compensating controls, and links to the deployed digest they affect.

| Evidence Type | What It Proves | What It Does Not Prove | Best Use |
|---|---|---|---|
| Image digest | The exact artifact bytes | Who built the artifact or whether it is safe | stable identity for signing and deployment |
| Signature | An expected identity signed the artifact | The artifact has no vulnerabilities | admission and release verification |
| SBOM | Components discovered in an artifact | Components are patched or acceptable | incident response and risk analysis |
| Vulnerability scan | Known vulnerability matches at scan time | Unknown vulnerabilities are absent | release gates and continuous monitoring |
| Provenance | Build process and source inputs | Runtime configuration is secure | audit, SLSA alignment, build trust |

> **Pause and predict:** A team stores `sbom.json` as a CI artifact but deploys by mutable tag. Three days later, the tag is overwritten and a vulnerability alert fires. What extra investigation work did the team create for itself, and how would digest-bound attestations reduce that work?

The answer is that responders must now prove which SBOM belongs to which deployed bytes. They may need to inspect registry history, CI logs, deployment events, and cluster state to reconstruct the relationship between tag, digest, and inventory. If the SBOM was attached as an attestation to the image digest, the responder can query evidence for the exact artifact running in the cluster. That difference is the gap between an inventory that exists somewhere and an inventory that is operationally useful.

---

## 4. Use Registries and Admission Control as Enforcement Points

A registry is not just a place to store images; it is a policy boundary between build systems and runtime environments. Harbor is a CNCF graduated registry that adds project-level access control, vulnerability scanning, replication, audit logging, retention policies, and integration points for signing workflows. Even if your organization uses another registry, the same design questions apply: who can push, can tags be overwritten, where are scan results stored, and can promotion require evidence?

```text
HARBOR ARCHITECTURE
====================================================================

+------------------------------------------------------------------+
|                              HARBOR                              |
|                                                                  |
|  +---------------+      +---------------+      +---------------+ |
|  | Core          |      | Registry      |      | Portal        | |
|  | API, auth,    |      | OCI storage   |      | web UI and    | |
|  | projects      |      | and manifests |      | workflows     | |
|  +---------------+      +---------------+      +---------------+ |
|                                                                  |
|  +---------------+      +---------------+      +---------------+ |
|  | Trivy         |      | Notary or     |      | Job Service   | |
|  | vulnerability |      | signing       |      | replication   | |
|  | scanning      |      | integration   |      | and cleanup   | |
|  +---------------+      +---------------+      +---------------+ |
+------------------------------------------------------------------+
```

```bash
# Add the Harbor Helm repository and install Harbor with Trivy enabled.
helm repo add harbor https://helm.getharbor.io
helm repo update

helm install harbor harbor/harbor \
  --namespace harbor \
  --create-namespace \
  --set expose.type=ingress \
  --set expose.ingress.hosts.core=harbor.example.com \
  --set externalURL=https://harbor.example.com \
  --set persistence.persistentVolumeClaim.registry.size=50Gi \
  --set trivy.enabled=true
```

Harbor can scan images on push, but scan-on-push should not be confused with deployment authorization. A registry scan tells you what the registry observed, while admission control decides what enters a cluster. You usually want both. Registry policy catches problems early and gives teams feedback near the publishing step. Admission control catches bypasses, stale images, untrusted registries, and artifacts that were pushed before the current policy existed.

Admission policies should be scoped carefully because Kubernetes workloads pull images in many forms. Some namespaces may be allowed to run public base images for experimentation, while production namespaces should require images from approved registries. Some controllers create Pods indirectly, so policies must match the Pod image fields that actually reach the API server. The policy should produce clear denial messages that tell a developer which evidence is missing and how to regenerate it.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  validationFailureAction: Enforce
  background: false
  rules:
    - name: verify-ghcr-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - production
      verifyImages:
        - imageReferences:
            - "ghcr.io/acme-platform/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/acme-platform/*"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: https://rekor.sigstore.dev
```

A policy like this is a starting point, not a finished operating model. You still need to test how it behaves with init containers, ephemeral containers, CronJobs, Helm releases, and rollbacks. You also need to decide whether emergency break-glass deployments are allowed and how they are audited. A production-ready exception process is not a loophole; it is a controlled path for rare cases where availability risk temporarily exceeds supply chain risk.

Ratify and Gatekeeper provide another common pattern: an external verifier checks artifact metadata, and Gatekeeper constraints enforce the result. This is useful when you want admission control to verify multiple artifact types or when your organization already standardizes on Open Policy Agent and Gatekeeper. The trade-off is extra moving parts, so the platform team must own observability for verifier latency, registry reachability, and policy failure modes.

```yaml
apiVersion: config.ratify.deislabs.io/v1beta1
kind: Verifier
metadata:
  name: cosign-verifier
spec:
  name: cosign
  artifactTypes: application/vnd.dev.cosign.simplesigning.v1+json
  parameters:
    key: |
      -----BEGIN PUBLIC KEY-----
      REPLACE_WITH_PUBLIC_KEY_CONTENT
      -----END PUBLIC KEY-----
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: RatifyVerification
metadata:
  name: require-signature
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
```

```text
ENFORCEMENT FLOW
====================================================================

Developer push
    |
    v
CI builds image by commit SHA
    |
    v
CI pushes image and records digest
    |
    v
CI signs digest and attaches SBOM
    |
    v
Registry stores artifact and scan metadata
    |
    v
Deployment references approved registry image
    |
    v
Admission policy verifies expected signature and evidence
    |
    v
Kubernetes admits the Pod or returns a clear denial
```

The senior-level design question is where to fail closed and where to fail open. A production namespace that cannot verify a signature because the registry is unavailable should probably fail closed, because otherwise an outage in the verifier becomes a security bypass. A development namespace may fail open temporarily while still recording policy violations. The right answer depends on the environment, but the decision must be explicit, documented, and tested during failure drills.

---

## 5. Scaffold from Single Controls to a Complete Pipeline

Tool-specific commands become useful when learners can see how they compose. The simplest path is to build one image, identify its digest, scan it, generate an SBOM, sign it, and verify it manually. The next layer moves those same actions into CI with a narrow set of permissions. The final layer connects CI evidence to registry policy and admission control. This gradual progression prevents the “wall of YAML” problem where the pipeline looks impressive but nobody understands which control answers which risk.

```text
PROGRESSIVE SCAFFOLDING
====================================================================

Level 1: Local proof
  Build image -> scan image -> generate SBOM -> sign digest -> verify digest

Level 2: CI evidence
  Protected branch -> OIDC identity -> push digest -> sign -> attest SBOM

Level 3: Registry control
  Approved projects -> scan on push -> immutable tags -> promotion rules

Level 4: Runtime enforcement
  Deployment by digest -> admission verification -> exception audit trail
```

Start with a single-image workflow because it exposes the artifact identity problem directly. The local example below uses a tiny application, builds it, and shows how the same image can be referenced by tag for convenience and digest for evidence. You should not treat this as a production architecture; treat it as the smallest lab that teaches why digest-first thinking matters.

```bash
# Create a minimal demo application.
mkdir -p supply-chain-demo
cd supply-chain-demo

cat > Dockerfile <<'EOF'
FROM cgr.dev/chainguard/nginx:latest
COPY index.html /usr/share/nginx/html/index.html
EOF

cat > index.html <<'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Supply Chain Demo</title>
  </head>
  <body>
    <h1>Signed and scanned artifact</h1>
  </body>
</html>
EOF

docker build -t supply-chain-demo:v1 .
trivy image --severity HIGH,CRITICAL supply-chain-demo:v1
syft supply-chain-demo:v1 -o cyclonedx-json > sbom.cdx.json
```

Local images are useful for learning, but most signing and attestation workflows become more meaningful after pushing to a registry because Cosign stores signature objects alongside the image in OCI-compatible storage. The important step is to push first and then sign the digest that the registry reports. A digest taken only from a local image may not represent the same registry manifest that deployers will pull, especially for multi-platform images.

```bash
# Replace these values with a registry namespace you can push to.
export REGISTRY_IMAGE="ghcr.io/YOUR_ORG/supply-chain-demo:v1"

docker tag supply-chain-demo:v1 "$REGISTRY_IMAGE"
docker push "$REGISTRY_IMAGE"

# Read the immutable digest from the registry.
export IMAGE_DIGEST="$(docker buildx imagetools inspect "$REGISTRY_IMAGE" \
  --format '{{json .Manifest.Digest}}' | tr -d '"')"

export IMAGE_BY_DIGEST="${REGISTRY_IMAGE%:v1}@${IMAGE_DIGEST}"

echo "$IMAGE_BY_DIGEST"
```

Once the digest exists, the controls line up in a predictable order. Scan the digest so the result describes immutable bytes. Generate or regenerate the SBOM from the digest so the inventory describes the pushed artifact. Sign the digest so the signature binds to the artifact identity. Attach the SBOM as an attestation so responders can retrieve it from the artifact rather than searching through CI logs.

```bash
trivy image --severity HIGH,CRITICAL "$IMAGE_BY_DIGEST"

syft "$IMAGE_BY_DIGEST" -o cyclonedx-json > sbom.cdx.json

cosign sign --yes "$IMAGE_BY_DIGEST"

cosign attest --yes \
  --predicate sbom.cdx.json \
  --type cyclonedx \
  "$IMAGE_BY_DIGEST"

cosign verify "$IMAGE_BY_DIGEST" \
  --certificate-identity-regexp="https://github.com/YOUR_ORG/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

cosign verify-attestation "$IMAGE_BY_DIGEST" \
  --type cyclonedx \
  --certificate-identity-regexp="https://github.com/YOUR_ORG/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"
```

Now translate the manual sequence into CI. The workflow needs minimal permissions: read source, write packages, and request an OIDC token for keyless signing. It should build and push the image, capture the digest, scan the digest, generate the SBOM, sign the digest, and attach the SBOM. If you later add provenance generation, it should be bound to the same digest so that all evidence points at one immutable artifact.

```yaml
name: Secure Build and Evidence

on:
  push:
    branches:
      - main

permissions:
  contents: read
  packages: write
  id-token: write
  security-events: write

jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image_by_digest: ${{ steps.digest.outputs.image_by_digest }}

    steps:
      - uses: actions/checkout@v4

      - name: Install Cosign
        uses: sigstore/cosign-installer@v3

      - name: Install Syft
        uses: anchore/sbom-action/download-syft@v0

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        run: |
          IMAGE="ghcr.io/${{ github.repository }}:${{ github.sha }}"
          docker build -t "$IMAGE" .
          docker push "$IMAGE"

      - name: Resolve pushed digest
        id: digest
        run: |
          IMAGE="ghcr.io/${{ github.repository }}:${{ github.sha }}"
          DIGEST="$(docker buildx imagetools inspect "$IMAGE" --format '{{json .Manifest.Digest}}' | tr -d '"')"
          IMAGE_BY_DIGEST="ghcr.io/${{ github.repository }}@${DIGEST}"
          echo "image_by_digest=${IMAGE_BY_DIGEST}" >> "$GITHUB_OUTPUT"

      - name: Vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.digest.outputs.image_by_digest }}
          format: sarif
          output: trivy-results.sarif
          severity: CRITICAL,HIGH
          exit-code: "1"

      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif

      - name: Generate SBOM
        run: |
          syft "${{ steps.digest.outputs.image_by_digest }}" -o cyclonedx-json > sbom.cdx.json

      - name: Sign image digest
        run: |
          cosign sign --yes "${{ steps.digest.outputs.image_by_digest }}"

      - name: Attach SBOM attestation
        run: |
          cosign attest --yes \
            --predicate sbom.cdx.json \
            --type cyclonedx \
            "${{ steps.digest.outputs.image_by_digest }}"
```

This worked example deliberately keeps the controls visible instead of hiding them behind a reusable action. In a larger platform, you may package the same sequence as a reusable workflow so application teams do not copy and paste security logic. The reusable workflow should still expose the important outputs: image digest, signer identity, SBOM location, scan result, and provenance reference. Those outputs become inputs to promotion, deployment, and incident response systems.

> **Stop and think:** If the Trivy step fails after the image has already been pushed but before it is signed, what should your registry and admission policies do with that unsigned image? Decide whether deletion, quarantine, retention, or admission blocking is the right default for your organization.

The safest common default is to allow the registry to retain the pushed image for investigation while preventing deployment because it lacks required evidence. Immediate deletion can destroy useful forensic context and make flaky scanner failures harder to debug. Admission control should reject the image because it is unsigned or lacks required attestations. A registry retention or quarantine policy can then clean up failed build artifacts after a defined period.

---

## 6. Operate the System: Exceptions, Provenance, and Incident Response

Supply chain security becomes real when something goes wrong. A vulnerability may appear after deployment, a CI workflow may be modified incorrectly, a signing identity may change, or a registry may replicate an image before scanning completes. The platform should make these cases visible and actionable. That means evidence must be queryable, policy failures must explain themselves, and exceptions must be tracked as engineering decisions rather than private conversations.

Provenance records describe how an artifact was built, including source repository, commit, workflow, builder identity, and build parameters. SLSA provides a maturity framework for reasoning about build provenance and build platform hardening, while in-toto provides a way to describe and verify supply chain steps. These frameworks are not replacements for SBOMs or signatures. They answer a different question: not merely what is inside the artifact or who signed it, but how the artifact came to exist.

```text
EVIDENCE RELATIONSHIP
====================================================================

                 +--------------------+
                 | Source repository  |
                 | commit and review  |
                 +---------+----------+
                           |
                           v
+----------+      +--------------------+      +-------------------+
| Lockfile | ---> | Controlled build   | ---> | Image digest      |
| inputs   |      | runner and workflow|      | immutable output  |
+----------+      +----------+---------+      +---------+---------+
                             |                          |
                             v                          v
                  +--------------------+      +-------------------+
                  | Provenance         |      | Signature         |
                  | how it was built   |      | who endorsed it   |
                  +--------------------+      +-------------------+
                             |                          |
                             v                          v
                  +--------------------+      +-------------------+
                  | SBOM               |      | Admission policy  |
                  | what is inside     |      | what may run      |
                  +--------------------+      +-------------------+
```

A good exception process has four properties. It names an owner who accepts the risk, it states the exact artifact or workload covered, it describes compensating controls, and it expires automatically. Without expiry, exceptions become a shadow policy that silently weakens the platform. Without artifact scope, one exception for an urgent release can accidentally permit unrelated future deployments.

```yaml
apiVersion: security.acme.example/v1
kind: SupplyChainException
metadata:
  name: payments-cve-temporary-exception
  namespace: production
spec:
  owner: payments-platform
  imageDigest: ghcr.io/acme-platform/payments@sha256:REPLACE_WITH_DIGEST
  reason: "Critical CVE has no vendor fix and the vulnerable code path is not reachable."
  compensatingControls:
    - "NetworkPolicy blocks external access to the vulnerable endpoint."
    - "Runtime alert watches for unexpected process execution."
    - "Service owner reviews vendor advisory every business day."
  expiresAt: "2026-05-15T12:00:00Z"
```

Incident response should begin with artifact identity, not service names. A service name may map to many deployments across clusters, but the digest tells you which exact bytes are running. From the digest, retrieve the SBOM, signatures, provenance, scan history, deployment events, and exception records. This order keeps the investigation grounded in evidence and avoids wasting time on tag ambiguity.

```bash
# Example investigation flow for a running Kubernetes workload.
# The alias k is used below for kubectl after this first command.
alias k=kubectl

k -n production get pod -l app=payments \
  -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.containers[*].image}{"\n"}{end}'

export IMAGE="ghcr.io/acme-platform/payments@sha256:REPLACE_WITH_DIGEST"

cosign verify "$IMAGE" \
  --certificate-identity-regexp="https://github.com/acme-platform/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

cosign verify-attestation "$IMAGE" \
  --type cyclonedx \
  --certificate-identity-regexp="https://github.com/acme-platform/.*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

trivy image --severity HIGH,CRITICAL "$IMAGE"
```

The operating model also includes routine maintenance. Signing identities change when repositories move. Vulnerability gates need tuning as base images improve or degrade. Admission policies need tests before Kubernetes upgrades. Registry retention needs enough history for incident response but not unlimited storage growth. These are platform product responsibilities, not one-time security project tasks.

A useful maturity path is to start with evidence generation, then evidence verification, then policy enforcement, then continuous improvement. First, make every build produce a digest, SBOM, scan result, and signature. Next, verify that evidence in CI and promotion jobs. Then enforce verification in production admission. Finally, measure exception rates, policy bypasses, time to answer vulnerability exposure questions, and percentage of deployments that use digest-pinned images.

---

## Did You Know?

- **Keyless signing reduces secret storage risk**: Sigstore keyless signing uses short-lived certificates tied to workload identity, which means the platform does not need to distribute a long-lived private signing key to every build runner.

- **SBOMs are incident response tools as much as compliance artifacts**: Their most practical value appears when a new vulnerability is disclosed and teams must quickly find which running artifacts contain an affected component.

- **A valid signature is not the same as a safe artifact**: Signatures identify endorsement or build identity, while vulnerability scans, provenance, source review, and runtime policy provide different evidence about risk.

- **Mutable tags are a major source of supply chain confusion**: Tags help humans discuss releases, but digests are the stable identifiers that signatures, attestations, deployment records, and forensic investigations should share.

---

## Common Mistakes

| Mistake | Problem | Better Approach |
|---|---|---|
| Signing only mutable tags | The tag can later point to different bytes, making the signature relationship ambiguous during verification and response. | Push the image, resolve the registry digest, and sign the digest that deployment will use. |
| Treating scanning as proof of safety | A scanner only detects known issues with available metadata at a point in time, so unknown or newly disclosed vulnerabilities remain possible. | Combine scanning with SBOM retention, scheduled rescans, provenance, and risk-based exception handling. |
| Verifying “any signature” | An attacker may sign a malicious artifact with their own identity if policy does not restrict expected signer identity and issuer. | Verify the expected repository, workflow, OIDC issuer, and environment-specific signing identity. |
| Storing SBOMs only as detached CI files | Detached files are easy to lose or mismatch with the wrong image, especially after tag moves or rebuilds. | Attach SBOMs as digest-bound attestations and retain CI artifacts as secondary evidence. |
| Blocking every vulnerability equally | Teams may be unable to deploy urgent fixes because low-risk or unreachable vulnerabilities create the same failure as exploitable critical issues. | Use severity, exploitability, fix availability, exposure, and service criticality to design gates. |
| Enforcing admission before observing impact | A strict policy can break controllers, rollbacks, and emergency releases if missing evidence patterns are not discovered first. | Start in audit mode, fix common failures, document exceptions, and enforce gradually by namespace or registry. |
| Ignoring build workflow permissions | A signed image can still be risky if the workflow that signed it has broad secrets, unpinned actions, or unsafe pull request triggers. | Harden CI permissions, pin third-party actions, separate untrusted PR builds from release signing, and protect release branches. |
| Forgetting operational ownership | Policies drift, signer identities change, vulnerability feeds evolve, and exceptions accumulate without a team accountable for the system. | Assign platform ownership, publish runbooks, review metrics, and test failure modes regularly. |

---

## Quiz

### Question 1

Your team signs `ghcr.io/acme/orders:latest` after every build, and the cluster admission policy verifies that the tag has a valid signature. During an incident, responders discover that `latest` was overwritten after the scan completed. What should you change in the pipeline and deployment process?

<details>
<summary>Show Answer</summary>

Change the pipeline to resolve the registry digest after push, then scan, sign, attest, promote, and deploy that digest. Tags can remain as human-friendly release labels, but the evidence chain should bind to `ghcr.io/acme/orders@sha256:...`. The admission policy should verify signatures and attestations for the digest being admitted, because that digest identifies the exact bytes that Kubernetes will pull. This reduces ambiguity during response and prevents a later tag move from inheriting trust that belonged to different content.

</details>

### Question 2

A development team adds Cosign signing to CI, but verification only checks whether an image has a valid Sigstore signature. A contractor signs an image from a personal repository, pushes it to an approved registry path, and the image passes admission. What policy condition was missing?

<details>
<summary>Show Answer</summary>

The policy failed to verify the expected signer identity and OIDC issuer. A useful keyless policy should restrict signatures to a trusted repository, workflow, branch, environment, or service account identity, depending on the platform design. “Has a valid signature” only proves that some identity signed the artifact; it does not prove that the organization’s release workflow produced it. Admission should check both artifact location and signer identity so unrelated signatures do not satisfy production policy.

</details>

### Question 3

A critical CVE is announced in a compression library. Your service owners ask whether production is affected, but some teams store SBOMs as CI artifacts while others attach SBOM attestations to image digests. Which group can answer faster, and why?

<details>
<summary>Show Answer</summary>

The teams with digest-bound SBOM attestations can usually answer faster because they can start from the running image digest and retrieve the SBOM associated with that exact artifact. Teams with detached CI artifacts may need to correlate service names, tags, commit SHAs, build logs, and registry history before they know which SBOM belongs to the deployed bytes. The difference is not merely storage location; it is whether the inventory is bound to the immutable artifact identity used in production.

</details>

### Question 4

A Trivy scan fails for a high vulnerability in a package that is present in the image, but the service is internal, the vulnerable feature is not used, and no patched package exists yet. The release contains an urgent fix for a production outage. How should a mature platform handle the deployment decision?

<details>
<summary>Show Answer</summary>

The platform should support a documented, time-limited exception rather than forcing an undocumented bypass. The exception should name an owner, identify the exact image digest or workload, explain why the vulnerability is not currently exploitable, list compensating controls, and include an expiry or review date. Admission may allow the specific digest while still denying unrelated images with the same vulnerability. This preserves delivery under controlled risk while keeping the security decision visible and reviewable.

</details>

### Question 5

Your organization wants to adopt SLSA and a manager suggests removing SBOM generation because provenance will now prove that builds are trustworthy. How would you evaluate that proposal?

<details>
<summary>Show Answer</summary>

Do not remove SBOM generation because provenance and SBOMs answer different questions. Provenance explains how an artifact was built, including source and builder information, while an SBOM lists components inside the artifact. A trustworthy build can still include a vulnerable dependency, and an SBOM can still be generated by an untrusted process. A stronger design keeps both: provenance for build integrity and SBOMs for dependency inventory and vulnerability response.

</details>

### Question 6

A Kyverno image verification policy works for direct Pods but does not block an unsigned image deployed by a Helm chart as a Deployment. The platform team assumes Kyverno is broken. What should they check before replacing the tool?

<details>
<summary>Show Answer</summary>

They should check the policy match scope, the resources Kyverno evaluates, namespace selectors, validation mode, and whether the image fields in generated Pods are covered. Helm creates Kubernetes objects such as Deployments, and the Deployment controller later creates ReplicaSets and Pods. Depending on the policy design, verification may need to target Pod admission while also considering controllers, background scans, and namespace exclusions. The likely issue is policy coverage or rollout configuration, not necessarily the tool itself.

</details>

### Question 7

A build workflow signs images correctly, but it also runs on pull requests from forks with broad token permissions and access to release secrets. What supply chain risk remains even though signatures exist?

<details>
<summary>Show Answer</summary>

The signing process itself may be reachable from untrusted code, which means a malicious pull request could influence a trusted signing workflow or exfiltrate credentials. Signatures only help when the signer identity represents a controlled release path. The workflow should separate untrusted PR validation from release signing, minimize permissions, protect environments, pin third-party actions, and require protected branches or approvals before signing. Otherwise the organization may faithfully sign artifacts produced through an unsafe process.

</details>

---

## Hands-On Exercise

### Objective

Build a small supply chain evidence path for a container image, then reason about how the same controls would move into CI and admission control. This exercise uses local commands first because the mechanics are easier to see before they are hidden inside workflow YAML.

### Setup

Install the tools you need and create a small demo application. If you cannot push to a registry, complete the local scan and SBOM steps, then read the registry-specific commands and explain what would change in your environment. Cosign signatures and attestations are most realistic when stored in an OCI registry that your account can write to.

```bash
brew install cosign syft trivy
cosign version
syft version
trivy --version
```

```bash
mkdir -p supply-chain-lab
cd supply-chain-lab

cat > Dockerfile <<'EOF'
FROM cgr.dev/chainguard/nginx:latest
COPY index.html /usr/share/nginx/html/index.html
EOF

cat > index.html <<'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>KubeDojo Supply Chain Lab</title>
  </head>
  <body>
    <h1>KubeDojo Supply Chain Lab</h1>
  </body>
</html>
EOF
```

### Part 1: Build, Scan, and Inventory the Image

Build the local image, run a vulnerability scan, and generate an SBOM. Do not skip the scan if it reports findings; the point is to observe and record the result, not to pretend the first image is perfect. A real platform pipeline would decide which findings block release and which findings become tracked risk.

```bash
docker build -t supply-chain-lab:v1 .

trivy image --severity HIGH,CRITICAL supply-chain-lab:v1

syft supply-chain-lab:v1 -o cyclonedx-json > sbom.cdx.json

trivy sbom --severity HIGH,CRITICAL sbom.cdx.json
```

### Part 2: Push and Resolve the Digest

Push the image to a registry you control and resolve the immutable digest. Replace the registry path with your own organization or account. If your registry does not support the exact command shown, use the registry UI or CLI to find the digest and record it in `IMAGE_BY_DIGEST`.

```bash
export REGISTRY_IMAGE="ghcr.io/YOUR_ORG/supply-chain-lab:v1"

docker tag supply-chain-lab:v1 "$REGISTRY_IMAGE"
docker push "$REGISTRY_IMAGE"

export IMAGE_DIGEST="$(docker buildx imagetools inspect "$REGISTRY_IMAGE" \
  --format '{{json .Manifest.Digest}}' | tr -d '"')"

export IMAGE_BY_DIGEST="${REGISTRY_IMAGE%:v1}@${IMAGE_DIGEST}"

echo "$IMAGE_BY_DIGEST"
```

### Part 3: Sign and Verify the Digest

Use keyless signing if your environment supports it. If not, use a local key pair for the lab and write down why that is not the same operational model as production keyless signing. The important requirement is that you sign the digest, not the mutable tag.

```bash
cosign sign --yes "$IMAGE_BY_DIGEST"

cosign verify "$IMAGE_BY_DIGEST" \
  --certificate-identity-regexp=".*" \
  --certificate-oidc-issuer-regexp=".*"
```

For a stricter production-style check, replace the permissive regular expressions with the exact repository workflow identity and issuer that your platform expects. The permissive version is acceptable only for a lab because it proves that verification mechanics work, not that your organization’s release policy is strong.

### Part 4: Attach and Verify the SBOM

Attach the SBOM as an attestation and verify that the attestation can be discovered later. This step turns the SBOM from a detached file into artifact-bound evidence. In a real incident, responders should be able to start with a running image digest and retrieve the SBOM associated with that digest.

```bash
cosign attest --yes \
  --predicate sbom.cdx.json \
  --type cyclonedx \
  "$IMAGE_BY_DIGEST"

cosign verify-attestation "$IMAGE_BY_DIGEST" \
  --type cyclonedx \
  --certificate-identity-regexp=".*" \
  --certificate-oidc-issuer-regexp=".*"
```

### Part 5: Design the Admission Rule

Write a short policy design note for your environment before copying any policy YAML. Identify which registry paths should be allowed, which signer identities should be trusted, whether SBOM attestations are required, and how exceptions expire. Then adapt the Kyverno example from the module to one namespace where enforcement is safe to test.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-lab-signatures
spec:
  validationFailureAction: Audit
  background: false
  rules:
    - name: verify-lab-image-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - supply-chain-lab
      verifyImages:
        - imageReferences:
            - "ghcr.io/YOUR_ORG/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/YOUR_ORG/*"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: https://rekor.sigstore.dev
```

### Success Criteria

- [ ] You built a container image locally and recorded whether the vulnerability scan found high or critical issues.
- [ ] You generated a CycloneDX SBOM and scanned that SBOM separately from the image.
- [ ] You pushed the image to a registry and resolved the immutable digest that identifies the pushed artifact.
- [ ] You signed the image digest rather than only signing a mutable tag.
- [ ] You attached the SBOM as an attestation bound to the image digest.
- [ ] You verified the signature and attestation and can explain what identity constraints would be stricter in production.
- [ ] You drafted an admission policy scope that names trusted registries, trusted signer identities, target namespaces, and exception behavior.

### Reflection Questions

Answer these in a short design note after the commands work. Which step would fail if your registry allowed tag overwrites but your deployment used digests? Which step would fail if a developer built the same source from an untrusted fork? Which evidence would you query first if a new CVE affected a library in the SBOM? These answers are the bridge from tool usage to platform design.

---

## Next Module

Continue to [Networking Toolkit](/platform/toolkits/infrastructure-networking/networking/) to learn how Kubernetes networking, service mesh patterns, and Cilium policies extend platform security from artifact trust into runtime traffic control.
