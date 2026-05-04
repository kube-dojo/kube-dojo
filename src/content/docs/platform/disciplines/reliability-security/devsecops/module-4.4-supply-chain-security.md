---
title: "Module 4.4: Supply Chain Security"
slug: platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security
sidebar:
  order: 5
---

> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 55-65 min

## Prerequisites

Before starting this module, you should be comfortable reading CI/CD workflows, container image references, dependency lockfiles, and Kubernetes admission policy examples. This module builds directly on [Module 4.3: Security in CI/CD](../module-4.3-security-cicd/), where you learned how pipeline permissions, secret handling, and branch protections shape the trust boundary around a delivery system.

You do not need to be a cryptographer to succeed here, but you should understand the basic idea of signing and verification. A signature proves that a trusted identity approved a specific artifact digest. It does not prove that the artifact is vulnerability-free, well-designed, or safe to run by itself. Supply chain security is the practice of combining identity, provenance, dependency evidence, and runtime enforcement so that no single control has to carry the whole risk.

You should also have basic familiarity with container registries and Kubernetes workloads. The examples use container images, SBOMs, Sigstore Cosign, SLSA provenance, GitHub Actions, and Kyverno-style admission policies. The same mental model applies to language packages, binaries, Helm charts, Terraform modules, and internal platform templates.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Map** a software supply chain from source commit to Kubernetes deployment and identify where tampering, confusion, or secret exposure can occur.
- **Generate and evaluate** SBOM evidence so an incident team can answer whether a vulnerable component exists in a released artifact.
- **Design and verify** an artifact signing flow that binds an image digest to a workload identity, not merely to a mutable tag.
- **Compare and apply** SLSA, lockfiles, dependency controls, and admission policies to reduce realistic supply chain attack paths.
- **Debug** a failed deployment caused by missing signatures, stale provenance, or unsafe dependency resolution without weakening the control.

---

## Why This Module Matters

A platform team ships a payment service after weeks of security work. The application code has passed review, the container scan is clean, and the deployment pipeline uses protected branches. On release morning, the on-call engineer notices outbound traffic from a new pod in `kube-system`, even though no platform component was scheduled for maintenance. The source repository looks untouched, so the first instinct is to search the application code for a backdoor.

The backdoor is not in the code the team reviewed. It entered through the build path. A CI action was referenced by a mutable tag, a publish token was available to a step that did not need it, and a package uploaded under a familiar name was accepted because the install command trusted registry defaults. The team had protected the application while leaving the path that created the application weak enough to impersonate.

Supply chain security matters because modern software is assembled, not handwritten. A production image contains operating system packages, language dependencies, generated files, base layers, CI helpers, build actions, registry metadata, and cluster policy decisions. A senior engineer does not ask only, "Is the code secure?" They ask, "Can we prove what ran, who built it, what it contains, and why the cluster accepted it?"

This module teaches that proof chain step by step. You will start by modeling the attack surface, then generate an SBOM to make components visible, then sign and verify artifacts, then connect those controls into SLSA provenance and Kubernetes admission. The goal is not to memorize tool commands. The goal is to reason about evidence and enforcement when an artifact's origin is in doubt.

---

## 1. Model the Supply Chain Before Choosing Tools

Supply chain security starts with a map, not a scanner. If a team begins by installing every popular security tool, they often create noisy dashboards while leaving the dangerous trust decisions unchanged. The useful first question is, "What has to be true for this artifact to be safe enough to deploy?" That question forces the team to identify source integrity, dependency resolution, build isolation, artifact immutability, registry trust, and cluster admission as separate links.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SOFTWARE SUPPLY CHAIN PATH                           │
│                                                                              │
│  ┌────────────┐   ┌──────────────┐   ┌─────────────┐   ┌────────────────┐   │
│  │ Source     │   │ Dependencies │   │ Build       │   │ Artifact       │   │
│  │ repository │──▶│ and base     │──▶│ environment │──▶│ registry       │   │
│  │ commits    │   │ images       │   │ and CI jobs │   │ and metadata   │   │
│  └─────┬──────┘   └──────┬───────┘   └──────┬──────┘   └───────┬────────┘   │
│        │                 │                  │                  │            │
│        ▼                 ▼                  ▼                  ▼            │
│  insider commit    typosquat package   secret exposure    tag replacement   │
│  branch bypass     dependency drift    build injection    registry tamper    │
│                                                                              │
│  ┌────────────────┐   ┌─────────────────┐   ┌───────────────────────────┐   │
│  │ Deployment     │   │ Admission       │   │ Runtime and incident       │   │
│  │ manifests      │──▶│ controller      │──▶│ response evidence          │   │
│  │ and GitOps     │   │ verification    │   │                           │   │
│  └────────────────┘   └─────────────────┘   └───────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

The diagram shows why "scan the image" is only one part of the answer. A vulnerability scanner can report known CVEs in installed packages, but it cannot prove that the image was built from the approved commit. A signature can prove that a trusted identity signed a digest, but it cannot prove that the dependency tree was free of risky transitive packages. An admission controller can reject unsigned images, but it cannot help if the signing workflow signs whatever the attacker builds.

A useful supply chain design names the evidence each stage must produce. Source control produces commits, reviews, and branch protection events. Dependency managers produce lockfiles and resolved package URLs. Build systems produce logs, artifact digests, SBOMs, and provenance attestations. Registries preserve immutable digests and metadata. Kubernetes admission records why a workload was accepted or rejected. Incident response becomes dramatically faster when these records are already connected.

| Stage | Main Question | Evidence to Keep | Common Attack |
|---|---|---|---|
| Source | Was this change reviewed and approved? | Commit SHA, reviewer record, branch protection result | Insider commit or bypassed review |
| Dependencies | Were packages resolved from expected sources? | Lockfile, registry URL, package hash, SBOM component | Dependency confusion or typosquatting |
| Build | Was the artifact created by the trusted workflow? | Build logs, runner identity, provenance, digest | Build script injection or secret theft |
| Registry | Is this exact artifact immutable and traceable? | Image digest, signature, attestation, push event | Tag replacement or registry compromise |
| Admission | Did the cluster verify the artifact before running it? | Admission decision, policy version, verified identity | Unsigned or unapproved image deployment |
| Runtime | Can responders connect a running pod back to evidence? | Pod image digest, workload owner, SBOM, provenance | Long dwell time after compromise |

> **Pause and predict:** If an attacker can replace `ghcr.io/acme/payments:v1.2.0` in the registry but cannot change the digest `sha256:...`, which deployments are still vulnerable? Write down whether a manifest using the tag, the digest, or both the tag and digest would run the attacker's image before you continue.

The safest Kubernetes manifests deploy immutable digests, because tags are names that can move. A tag is convenient for humans, but the digest is the content identity. A manifest such as `image: ghcr.io/acme/payments@sha256:...` says exactly which bytes should run. A manifest such as `image: ghcr.io/acme/payments:v1.2.0` asks the registry what that tag means today, which creates a trust decision at pull time.

This does not mean tags are useless. Teams often publish tags for discoverability and release communication, then resolve those tags to digests during promotion. The promotion system can record, "release `v1.2.0` means digest `sha256:abc...`," and GitOps can deploy the digest. That pattern gives developers readable releases while giving the cluster immutable content.

```bash
IMAGE="ghcr.io/acme/payments:v1.2.0"

docker buildx imagetools inspect "$IMAGE"

# A real promotion script would capture the digest from the registry response,
# store it in the release record, and update deployment manifests to use it.
```

The next design choice is where to enforce trust. CI can fail builds that have unapproved dependencies. The registry can require signatures before promotion. Admission can reject workloads whose image identity or provenance does not match policy. Runtime detection can alert on unexpected privileged pods or new system namespace workloads. Mature platforms use all of these because attackers move laterally through whichever stage is least protected.

The table below is a compact decision matrix for choosing the first control when a team has limited time. It does not replace defense in depth, but it helps avoid random tool adoption. Start where the evidence gap causes the worst incident response failure.

| Symptom | First Control to Add | Why It Helps | What It Does Not Solve |
|---|---|---|---|
| Nobody knows whether a CVE affects production | SBOM generation and storage | Makes released components searchable | Does not prove who built the image |
| Images can be replaced under the same tag | Digest deployment and signing | Binds deployment to immutable content | Does not block risky dependencies alone |
| CI secrets are available to every step | Job-scoped permissions and secret scoping | Limits blast radius of compromised tools | Does not identify transitive packages |
| Developers use unpinned CI actions | Commit SHA pinning and dependency review | Reduces mutable third-party execution | Does not verify final runtime admission |
| Clusters run whatever manifests request | Admission verification | Moves trust enforcement to deploy time | Does not generate missing build evidence |
| Releases cannot be traced to source | SLSA provenance | Connects artifact, builder, and source | Does not replace vulnerability management |

The beginner version of supply chain security is "scan dependencies." The senior version is "preserve and verify a chain of evidence from source to runtime." Tools matter, but only because they produce or enforce evidence at a specific trust boundary.

---

## 2. Build SBOMs That Answer Incident Questions

A Software Bill of Materials, or SBOM, is an inventory of the components inside an artifact. It lists packages, versions, package URLs, licenses, hashes, and relationships depending on the format and generator. The operational value is simple: when a new vulnerability is announced, responders can query released artifacts instead of asking every team to inspect every repository by hand.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                                SBOM CONTENT                                  │
│                                                                              │
│  Artifact: ghcr.io/acme/payments@sha256:8a2...                                │
│  Build:    release workflow run 9021                                          │
│  Format:   CycloneDX JSON                                                     │
│                                                                              │
│  ┌─────────────────────────────┐    ┌────────────────────────────────────┐   │
│  │ Direct application packages │    │ Operating system packages          │   │
│  │ flask 2.3.3                 │    │ openssl 3.x                        │   │
│  │ requests 2.31.0             │    │ ca-certificates                     │   │
│  └──────────────┬──────────────┘    └──────────────────┬─────────────────┘   │
│                 │                                      │                     │
│                 ▼                                      ▼                     │
│  ┌─────────────────────────────┐    ┌────────────────────────────────────┐   │
│  │ Transitive dependencies     │    │ Base image layer components        │   │
│  │ urllib3                     │    │ debian or alpine packages          │   │
│  │ idna                        │    │ shell, libc, package manager data  │   │
│  └─────────────────────────────┘    └────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

An SBOM is not a security verdict. It is evidence. A clean SBOM can still describe a malicious package that has no known CVE. A noisy SBOM can include a vulnerable package that is not reachable in the deployed application. Treat the SBOM as the starting point for investigation, then combine it with exploitability analysis, runtime exposure, and business impact.

The two common formats you will see are SPDX and CycloneDX. SPDX has strong roots in license compliance and is widely used for legal and open source governance. CycloneDX is common in application security workflows because it models components, services, vulnerabilities, and dependency relationships in a way many security tools consume naturally. Either format is better than having no searchable inventory, and many organizations store both when tooling allows it.

| Format | Strong Fit | Typical Consumers | Trade-Off |
|---|---|---|---|
| SPDX | License compliance and legal review | Legal teams, open source program offices, artifact stores | Security relationships may require extra tooling |
| CycloneDX | Vulnerability management and dependency analysis | AppSec teams, scanners, policy engines, dashboards | License workflows may need additional fields |
| SWID | Enterprise asset inventory | Asset management and procurement systems | Less common in cloud-native build pipelines |
| in-toto statement | Attestation envelope for evidence | Provenance and policy verification systems | Carries predicates rather than being only an inventory |

A practical SBOM workflow has four steps. Generate the SBOM during the build, store it next to the artifact, attach or attest it so the digest and inventory stay linked, and index it for incident queries. If the SBOM lives only in a CI log or an engineer's laptop, it will not help during an incident. If it is generated after deployment from a mutable tag, it may describe a different artifact than the one running in production.

```bash
mkdir -p supply-chain-demo
cd supply-chain-demo

cat > requirements.txt <<'EOF'
flask==2.3.3
requests==2.31.0
EOF

cat > app.py <<'EOF'
from flask import Flask

app = Flask(__name__)

@app.get("/")
def hello():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
EOF

cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
EOF

docker build -t supply-chain-demo:v1 .
```

After the image exists locally, generate an SBOM from the actual image rather than only from the source directory. Source scans are useful, but they miss operating system packages and base layer contents. Image scans see what will actually ship, including dependencies introduced by the base image or package manager.

```bash
syft supply-chain-demo:v1 -o cyclonedx-json > sbom.cdx.json

jq '.components[] | {name: .name, version: .version, type: .type}' sbom.cdx.json | head
```

If your team uses Trivy instead of Syft, the same pattern applies. The important design point is not the brand of generator. The important point is that the SBOM is created from a specific artifact digest in the same release path that creates the deployable image.

```bash
trivy image --format cyclonedx --output sbom.cdx.json supply-chain-demo:v1

trivy sbom sbom.cdx.json
```

> **Stop and think:** Your scanner reports a critical CVE in a package from the base image, but developers say the application never imports that package. What evidence would you need before deciding whether to block release, patch immediately, or accept temporary risk?

The answer depends on exposure and policy. A package in a base image can be reachable through a system utility, an interpreter, a shell, or a library loaded by another package. The SBOM tells you the package exists. A vulnerability scanner tells you a known issue may apply. Runtime configuration, reachable code paths, exploit prerequisites, and compensating controls determine urgency. Senior teams document that decision instead of treating every scanner row as equal.

A strong SBOM program also records relationships. During a Log4Shell-style event, the key question is often not "Does any repository import this package directly?" but "Which released artifacts include it transitively?" Relationship data lets you trace from application framework to logging library to vulnerable component. Without that chain, teams waste time searching source code and miss packaged dependencies.

```bash
grype sbom:./sbom.cdx.json

# For a targeted incident query, filter scanner output for the vulnerability ID.
# Replace the example ID with the incident identifier your security team is tracking.
grype sbom:./sbom.cdx.json --only-fixed
```

| SBOM Failure Mode | What Happens During an Incident | Better Practice |
|---|---|---|
| SBOM generated only from source | Base image and OS packages are missing | Generate from the final image digest |
| SBOM stored only as a CI artifact | Evidence expires or is hard to find | Store with release metadata and artifact registry |
| SBOM not tied to digest | Inventory may describe the wrong image | Attach or attest SBOM against the digest |
| SBOM generated after release | The artifact may have changed | Generate during the build path |
| SBOM ignored after creation | Vulnerability response stays manual | Index SBOMs for search and alerting |
| SBOM treated as a pass/fail gate only | Teams lose context and over-block | Combine inventory with risk analysis |

SBOMs become more valuable when they are boring. Every build produces one, every release stores one, every incident query uses the same location, and every exception records why the component was accepted. The team should not be inventing the SBOM process during a zero-day response.

---

## 3. Sign Artifacts and Verify Identity

Image signing answers a different question than vulnerability scanning. Scanning asks, "What known weaknesses are inside this artifact?" Signing asks, "Did a trusted identity approve this exact artifact digest?" You need both questions because an attacker can create a backdoored image with no known CVEs, and a legitimate image can contain vulnerable packages.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                           SIGNING TRUST MODEL                                │
│                                                                              │
│  Build workflow                                                              │
│  identity: repo acme/payments, release workflow                              │
│          │                                                                   │
│          │ builds image                                                       │
│          ▼                                                                   │
│  ghcr.io/acme/payments@sha256:8a2...                                          │
│          │                                                                   │
│          │ signs digest, not mutable tag                                      │
│          ▼                                                                   │
│  Signature + certificate + transparency log entry                             │
│          │                                                                   │
│          │ verified by admission policy                                       │
│          ▼                                                                   │
│  Kubernetes accepts only images signed by the expected workflow identity      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Sigstore is popular in cloud-native environments because it supports keyless signing. Traditional signing often requires teams to create, store, rotate, and protect long-lived private keys. Keyless signing uses workload identity through OIDC, short-lived certificates, and a transparency log. The result is still a cryptographic signature, but the human or workflow identity becomes part of the verification story.

Cosign is the command-line tool most teams use with Sigstore. Fulcio issues short-lived signing certificates based on OIDC identity. Rekor records transparency log entries so signatures can be audited. Policy controllers and admission systems can verify that an image digest was signed by a specific identity, such as a GitHub Actions workflow in a specific repository.

| Component | Role in the Signing Flow | Operational Question It Answers |
|---|---|---|
| Cosign | Signs and verifies artifacts | Can this digest be linked to a trusted signer? |
| Fulcio | Issues short-lived certificates | Which OIDC identity performed the signing? |
| Rekor | Records transparency log entries | Is there an auditable record of the signature event? |
| OIDC issuer | Provides workload or user identity | Was the signer a trusted workflow or account? |
| Admission policy | Enforces verification before runtime | Should this cluster accept the workload? |

The most important habit is signing the digest. A tag can point to different content over time, so signing only a tag-shaped reference can hide ambiguity in conversations and runbooks. When a build pushes an image, capture the pushed digest and sign that digest. The digest is the immutable subject of the trust decision.

```bash
IMAGE="ghcr.io/acme/payments"
TAG="v1.2.0"

docker build -t "$IMAGE:$TAG" .
docker push "$IMAGE:$TAG"

DIGEST="$(docker buildx imagetools inspect "$IMAGE:$TAG" --format '{{json .Manifest.Digest}}' | tr -d '"')"
echo "$IMAGE@$DIGEST"
```

In GitHub Actions, keyless signing requires `id-token: write` because the workflow must request an OIDC token. This permission should be granted only to the job that signs or generates attestations. The build job should have only the permissions it needs, and the publish job should not expose package registry tokens to unrelated scanners or test steps.

```yaml
name: build-sign-release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      packages: write
    outputs:
      image: ${{ steps.meta.outputs.image }}
      digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@8edcb1bdb4e267140fa742c62e395cd74f332709

      - name: Set image name
        id: meta
        run: echo "image=ghcr.io/${GITHUB_REPOSITORY}" >> "$GITHUB_OUTPUT"

      - name: Log in to registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${GITHUB_ACTOR}" --password-stdin

      - name: Build and push
        id: build
        run: |
          docker build -t "${{ steps.meta.outputs.image }}:${GITHUB_REF_NAME}" .
          docker push "${{ steps.meta.outputs.image }}:${GITHUB_REF_NAME}"
          DIGEST="$(docker buildx imagetools inspect "${{ steps.meta.outputs.image }}:${GITHUB_REF_NAME}" --format '{{json .Manifest.Digest}}' | tr -d '"')"
          echo "digest=${DIGEST}" >> "$GITHUB_OUTPUT"

  sign:
    needs: build
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      id-token: write
      packages: write
    steps:
      - uses: sigstore/cosign-installer@398d4b0eeef1380460a10c8013a76f728fb906ac

      - name: Sign image digest
        run: cosign sign --yes "${{ needs.build.outputs.image }}@${{ needs.build.outputs.digest }}"
```

The workflow pins actions to commit SHAs rather than broad tags. That choice matters because CI actions are executable dependencies. A mutable action tag can change what runs inside your trusted pipeline. Pinning does not make third-party code harmless, but it prevents silent drift and makes updates reviewable.

> **Decision point:** A developer proposes signing images from their laptop after local testing because it is faster than waiting for CI. Would you allow that for production images? Decide what identity, environment, and review evidence would be lost or preserved.

For production images, signing from a laptop usually weakens the trust story. The signer identity proves that a person signed something, but it does not prove that the artifact came from the reviewed source, a clean build environment, or the approved release workflow. A better pattern is to let developers sign development artifacts for testing, while production policy accepts only signatures from the release workflow identity.

Verification should be as specific as practical. "Signed by someone" is weak. "Signed by the release workflow in `acme/payments` using the GitHub OIDC issuer" is much stronger. Good verification names the expected issuer and subject, then binds that identity to the image digest being deployed.

```bash
cosign verify "ghcr.io/acme/payments@sha256:REPLACE_WITH_DIGEST" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --certificate-identity-regexp "https://github.com/acme/payments/.github/workflows/build-sign-release.yml@refs/tags/v.*"
```

Kubernetes admission control moves verification from a human checklist into the deployment path. A Kyverno policy can require signatures for images from a registry namespace, and the policy can specify the expected keyless identity. The cluster then rejects workloads that do not match, even if someone bypasses a manual release checklist.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-payments-images
spec:
  validationFailureAction: Enforce
  background: false
  rules:
    - name: verify-payments-image-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/acme/payments*"
          attestors:
            - entries:
                - keyless:
                    issuer: "https://token.actions.githubusercontent.com"
                    subject: "https://github.com/acme/payments/.github/workflows/build-sign-release.yml@refs/tags/v*"
```

Admission policies should start in audit mode for existing clusters, then move to enforcement after teams understand what will break. This is not because enforcement is optional. It is because a poorly scoped policy can cause an outage by rejecting system workloads, vendor controllers, or emergency rollback images. Roll out verification by namespace, registry prefix, or application group, and document how a break-glass exception is approved and expired.

---

## 4. Worked Example: Trace, Sign, Attest, and Enforce One Image

This worked example connects the pieces into one coherent flow. The scenario is a platform team releasing `ghcr.io/acme/orders:v2.0.0` to a Kubernetes 1.35 cluster. The team wants evidence that the image came from the approved repository, contains a searchable SBOM, has provenance from the release workflow, and cannot run unless admission verifies the release identity.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         WORKED EXAMPLE CONTROL FLOW                          │
│                                                                              │
│  1. Build image from reviewed source                                          │
│            │                                                                 │
│            ▼                                                                 │
│  2. Push image and capture immutable digest                                   │
│            │                                                                 │
│            ▼                                                                 │
│  3. Generate SBOM from that exact digest                                      │
│            │                                                                 │
│            ▼                                                                 │
│  4. Sign digest and attach SBOM/provenance attestations                       │
│            │                                                                 │
│            ▼                                                                 │
│  5. Deploy by digest, then admission verifies signer identity                 │
│            │                                                                 │
│            ▼                                                                 │
│  6. Incident team can query digest, SBOM, signer, and source commit           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Step one is to define the artifact identity. The team refuses to promote a tag alone. The release record contains the image repository, tag, digest, source commit, workflow run, SBOM location, and signature verification command. This release record is boring metadata until an incident occurs, then it becomes the difference between a five-minute query and a multi-day search.

| Release Field | Example Value | Why It Matters |
|---|---|---|
| Source repository | `github.com/acme/orders` | Defines the expected source of truth |
| Source commit | `9b6c...` | Ties the artifact to reviewed code |
| Workflow identity | `build-sign-release.yml` | Defines the trusted builder |
| Image digest | `sha256:8a2...` | Identifies immutable content |
| SBOM artifact | `orders-v2.0.0.cdx.json` | Supports incident component queries |
| Signature identity | GitHub OIDC subject | Supports admission verification |
| Provenance predicate | SLSA provenance | Links builder, source, and artifact |

Step two is to build and push the image. The exact commands vary by build system, but the behavior should not. The build produces an image, the push returns or allows lookup of a digest, and every later control uses that digest as the subject. If a later step receives only `orders:v2.0.0`, the workflow has already lost precision.

```bash
IMAGE="ghcr.io/acme/orders"
TAG="v2.0.0"

docker build -t "$IMAGE:$TAG" .
docker push "$IMAGE:$TAG"

DIGEST="$(docker buildx imagetools inspect "$IMAGE:$TAG" --format '{{json .Manifest.Digest}}' | tr -d '"')"
IMAGE_REF="$IMAGE@$DIGEST"

printf '%s\n' "$IMAGE_REF"
```

Step three is to generate the SBOM from the immutable image reference. The team stores the SBOM as a build artifact and attaches it as an attestation. Storing the file supports search and dashboards. Attaching the predicate supports verification that the SBOM belongs to the digest being deployed.

```bash
syft "$IMAGE_REF" -o cyclonedx-json > orders-v2.0.0.cdx.json

cosign attest --yes \
  --predicate orders-v2.0.0.cdx.json \
  --type cyclonedx \
  "$IMAGE_REF"
```

Step four is to sign the digest with the release workflow identity. If the image is rebuilt, the digest changes and the old signature does not automatically apply. That is the desired behavior. A signature says, "this exact content was approved by this identity," not "anything with this tag is acceptable."

```bash
cosign sign --yes "$IMAGE_REF"

cosign verify "$IMAGE_REF" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --certificate-identity-regexp "https://github.com/acme/orders/.github/workflows/build-sign-release.yml@refs/tags/v.*"
```

Step five is to deploy by digest and let admission enforce the same identity requirement. Notice that the manifest does not ask Kubernetes to resolve a moving tag. The digest is explicit, which means the admission controller, kubelet, registry, and incident record all talk about the same artifact.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
  namespace: payments
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orders
  template:
    metadata:
      labels:
        app: orders
    spec:
      containers:
        - name: orders
          image: ghcr.io/acme/orders@sha256:REPLACE_WITH_REAL_DIGEST
          ports:
            - containerPort: 8080
```

Step six is to test the negative case. A control that has never rejected anything is not yet proven. The team attempts to deploy an unsigned image in a staging namespace where the policy is enforced. The expected result is a rejected admission request with a message that names signature verification or attestor mismatch.

```bash
kubectl apply -f deployment.yaml

kubectl get events -n payments --sort-by='.lastTimestamp' | tail -n 20
```

If the deployment fails even though the image was signed, debug the evidence chain in order. First confirm the manifest uses the digest that was signed. Then verify the certificate issuer and subject match the policy. Then confirm the policy image pattern matches the image reference. Finally, check whether the attestation type or signature is stored in a registry location the verifier can access.

| Failure Symptom | Likely Cause | First Debug Command |
|---|---|---|
| Verification says no signatures found | Signed tag or wrong digest | `cosign verify "$IMAGE_REF" ...` |
| Admission says subject mismatch | Policy expects different workflow identity | Inspect certificate identity from `cosign verify` output |
| Admission does not run | Policy match selector misses the workload | `kubectl get clusterpolicy` and review `match` block |
| SBOM query finds nothing | SBOM stored as file but not indexed | Check artifact store and attestation upload |
| Rollback image is rejected | Old release lacks signature | Sign historical digest or define approved exception |
| Vendor image is rejected | Policy scope too broad | Limit policy to owned registry prefixes first |

This worked example is intentionally narrow. It secures one image path rather than pretending to solve all supply chain risk at once. Once the team can do this reliably for one service, they can template it into platform pipelines, GitOps promotion, and admission policy libraries.

---

## 5. Raise Maturity with SLSA and Dependency Controls

SLSA, pronounced "salsa," is a framework for improving software supply chain integrity. It is useful because it turns vague maturity goals into concrete build and provenance requirements. A team can say, "We want SLSA Build Level 2 for internal services this quarter," and that statement implies hosted builds, authenticated provenance, and repeatable evidence instead of a generic promise to be more secure.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              SLSA BUILD LEVELS                               │
│                                                                              │
│  Level 0                                                                      │
│  No meaningful supply chain guarantees. Builds may be manual, local, or       │
│  undocumented, and released artifacts cannot be reliably traced.              │
│                                                                              │
│  Level 1                                                                      │
│  Provenance exists. The build process is scripted, and the artifact has       │
│  basic information about how it was produced.                                 │
│                                                                              │
│  Level 2                                                                      │
│  Hosted build service and authenticated provenance. The build runs on a       │
│  trusted platform, and provenance is signed or otherwise authenticated.        │
│                                                                              │
│  Level 3                                                                      │
│  Hardened build platform. Builds are isolated, stronger tamper resistance     │
│  exists, and provenance is difficult for project maintainers to falsify.      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

SLSA is not a badge you earn once and forget. It is a way to reason about how much confidence you can place in the relationship between source, builder, and artifact. A manual build from a developer laptop might be acceptable for a prototype, but it is weak evidence for production. A hosted build with authenticated provenance is better. A hardened build platform with strong isolation and non-falsifiable provenance is stronger still.

| Capability | Level 1 | Level 2 | Level 3 |
|---|---:|---:|---:|
| Scripted build process | Yes | Yes | Yes |
| Provenance generated | Yes | Yes | Yes |
| Hosted build service | No | Yes | Yes |
| Authenticated provenance | No | Yes | Yes |
| Strong build isolation | No | Partial | Yes |
| Tamper-resistant provenance | Basic | Better | Strong |
| Suitable default for production platforms | Limited | Common target | High assurance target |

GitHub Actions can produce provenance through artifact attestations or SLSA generator workflows. The exact implementation changes over time, but the principle stays stable: provenance must describe the subject artifact, the build type, the source material, and the builder identity. A policy engine can then verify whether the artifact came from the expected source and build path.

```yaml
name: provenance

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      packages: write
      id-token: write
      attestations: write
    steps:
      - uses: actions/checkout@8edcb1bdb4e267140fa742c62e395cd74f332709

      - name: Build artifact
        run: |
          mkdir -p dist
          printf 'release artifact for %s\n' "$GITHUB_SHA" > dist/app.txt

      - name: Generate artifact attestation
        uses: actions/attest-build-provenance@1c6080f900062f3ac3f4c313417efc5d40923a8c
        with:
          subject-path: dist/app.txt
```

Provenance protects against a different class of confusion than SBOMs. An SBOM can tell you an artifact contains `openssl`. Provenance can tell you the artifact was built by `github.com/acme/orders` at a specific commit using a specific workflow. If an attacker uploads a lookalike artifact to the registry, provenance verification should fail because the trusted builder relationship is missing.

Dependency controls are the other side of the maturity model. Many supply chain incidents begin before the build produces anything: package names are confused, transitive dependencies drift, action tags move, or a maintainer account is compromised. Lockfiles, registry scoping, hash verification, and update automation reduce the chance that a build silently consumes something unexpected.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY CONFUSION PATTERN                         │
│                                                                              │
│  Internal package expected:       @acme/internal-metrics 1.3.0                │
│  Private registry expected:       https://npm.acme.example                    │
│                                                                              │
│  Risky configuration:             package name without enforced scope         │
│          │                                                                   │
│          ▼                                                                   │
│  Public registry contains:        internal-metrics 99.0.0                     │
│          │                                                                   │
│          ▼                                                                   │
│  Installer chooses public package because version or registry precedence wins │
│                                                                              │
│  Safer configuration:             scoped package + private registry mapping   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

For npm, scoped packages and registry mapping are essential. The scope tells the package manager that `@acme/*` packages belong to the organization. The `.npmrc` mapping tells the installer where those packages may be resolved. The lockfile records the resolved URL and integrity hash so CI can install the same dependency graph that was reviewed.

```json
{
  "dependencies": {
    "@acme/internal-metrics": "1.3.0",
    "express": "4.18.3"
  }
}
```

```ini
@acme:registry=https://npm.acme.example
registry=https://registry.npmjs.org
always-auth=true
```

```bash
npm ci
npm audit signatures
```

For Python, hash-checked requirements reduce silent package replacement. This approach is stricter than a plain `requirements.txt`, because each package version must match an expected hash. It takes more maintenance, but it gives high-value services a stronger guarantee that the package downloaded in CI is the package that was reviewed.

```text
flask==2.3.3 \
    --hash=sha256:REPLACE_WITH_HASH_FROM_LOCK_TOOL
requests==2.31.0 \
    --hash=sha256:REPLACE_WITH_HASH_FROM_LOCK_TOOL
```

```bash
pip install --require-hashes -r requirements.txt
```

Use an appropriate lock tool to generate real hashes rather than typing placeholders by hand. For Python teams, `pip-tools`, Poetry, or uv can produce reproducible lock data depending on the standard your organization has adopted. The control is not "make requirements hard to edit." The control is "make dependency resolution explicit enough that a changed package source or hash creates a reviewable diff."

| Ecosystem | Resolution Control | CI Command | Risk Reduced |
|---|---|---|---|
| npm | `package-lock.json` and scoped `.npmrc` | `npm ci` | Registry drift and dependency confusion |
| Yarn | `yarn.lock` with immutable install | `yarn install --immutable` | Silent dependency updates |
| pnpm | `pnpm-lock.yaml` | `pnpm install --frozen-lockfile` | Transitive dependency drift |
| pip | Hash-checked requirements or lock file | `pip install --require-hashes -r requirements.txt` | Package replacement and unreviewed versions |
| Poetry | `poetry.lock` | `poetry install --sync` | Environment drift |
| Go | `go.sum` and module verification | `go mod verify` | Module checksum mismatch |
| Containers | Digest-pinned base images | `docker build` with pinned `FROM` digest | Mutable base image changes |

Automation helps when it creates small, reviewable changes. Dependabot or Renovate should open pull requests that update lockfiles, run tests, regenerate SBOMs, and show vulnerability context. Automatic merge can be reasonable for low-risk patch updates in well-tested services, but major updates and security-sensitive packages need human review. The point is not to freeze dependencies forever. The point is to make change deliberate.

```json
{
  "extends": ["config:recommended"],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"]
  },
  "packageRules": [
    {
      "matchUpdateTypes": ["patch", "minor"],
      "automerge": true,
      "requiredStatusChecks": ["test", "sbom", "image-scan"]
    },
    {
      "matchUpdateTypes": ["major"],
      "labels": ["major-update", "needs-review"]
    }
  ]
}
```

Finally, SLSA and dependency controls should feed platform policy. If a service is tier one, the platform might require digest deployment, signed images, SBOM attestation, SLSA provenance, lockfile enforcement, and admission verification. If a service is experimental, the platform might require fewer controls but still prevent known dangerous patterns such as `latest` tags and unscoped internal package names. Senior platform teams design risk tiers instead of pretending every workload has identical assurance needs.

---

## Did You Know?

1. The SolarWinds compromise <!-- incident-xref: solarwinds-2020 --> showed that a trusted software update mechanism can become the delivery path for malicious code when the build process itself is compromised. For the full case study, see [CI/CD Pipelines](../../../../prerequisites/modern-devops/module-1.3-cicd-pipelines/).

2. SBOMs are most useful when they are generated for released artifacts, because source-only inventories can miss base image packages and build-time additions.

3. Keyless signing does not mean unsigned signing; it means the signing key is short-lived and tied to an identity provider instead of a long-lived private key managed by the team.

4. SLSA focuses on artifact integrity and build provenance, so it complements vulnerability scanning rather than replacing scanners, code review, or runtime detection.

---

## Common Mistakes

| Mistake | Why It Fails | Better Practice |
|---|---|---|
| Deploying mutable tags in production | A tag can be repointed after review, which makes incident evidence ambiguous | Promote and deploy immutable image digests |
| Generating SBOMs only from source directories | Source scans miss operating system packages and base image contents | Generate SBOMs from final image digests |
| Signing images from developer laptops for production | The signature proves a person signed something, not that CI built reviewed source | Accept production signatures only from trusted release workflows |
| Granting publish tokens to every CI step | A compromised scanner or test tool can steal release credentials | Scope secrets and permissions to the job that needs them |
| Trusting broad signature checks | "Signed by anyone" does not prove the artifact came from the right repository | Verify expected issuer, subject, repository, workflow, and digest |
| Enforcing admission policies without audit rollout | Legitimate workloads may be blocked because image patterns or vendor exceptions were missed | Start with audit, review events, then enforce by namespace or registry scope |
| Treating SBOM findings as automatic release blockers | Some findings are unreachable or mitigated, while others are urgent | Combine SBOM data with exploitability, exposure, and policy |
| Updating dependencies without lockfile review | Transitive changes can enter production without meaningful inspection | Require lockfile diffs, tests, SBOM regeneration, and review |

---

## Quiz

### Question 1

Your team deploys `ghcr.io/acme/api:v3.1.0` in production. During an incident, the registry shows that the tag now points to a digest different from the one recorded in last week's release notes. The image has a valid vulnerability scan report with no critical findings. What should you check first, and what long-term control would prevent this ambiguity?

<details>
<summary>Show Answer</summary>

Check whether the running Pods are using a tag or an immutable digest. If the manifest uses only `v3.1.0`, Kubernetes may pull whichever digest the registry currently associates with that tag, depending on pull policy and node cache behavior. The vulnerability scan does not prove the image is the reviewed release; it only describes known issues in the scanned artifact.

The long-term control is to promote and deploy by digest, then sign that digest and verify it at admission. Release metadata should record the tag, digest, source commit, SBOM, signature identity, and provenance. Tags may still exist for human readability, but the cluster should run the immutable digest.

</details>

### Question 2

A new CVE affects a transitive Java logging library. Developers search the repository and say the service does not import that library directly. Your SBOM index shows the vulnerable package inside the production image. How should you investigate before deciding whether to block the next release?

<details>
<summary>Show Answer</summary>

First, trace the dependency relationship from the SBOM or build tool to identify which direct dependency introduced the library. Then check whether the vulnerable component is present in the final runtime image, whether the affected code path is reachable, and whether the deployed configuration exposes the exploit prerequisite. The fact that developers do not import the package directly is not enough, because transitive dependencies can still be packaged and reachable.

A reasonable response is to update the direct dependency that brings the vulnerable library, override or exclude the vulnerable version if the ecosystem supports it, rebuild the image, regenerate the SBOM, and verify that the fixed version appears in the released artifact. If exploitability is unclear, document the temporary risk decision and compensating controls instead of ignoring the SBOM finding.

</details>

### Question 3

A platform team adds Cosign signing to CI, but admission rejects the image with a subject mismatch. The image was signed successfully, and `cosign verify` shows a GitHub OIDC certificate. What should you compare, and why is weakening the policy to "any valid signature" the wrong fix?

<details>
<summary>Show Answer</summary>

Compare the certificate issuer and subject from `cosign verify` with the issuer and subject pattern in the admission policy. The workflow file path, repository name, branch or tag reference, and OIDC issuer must match what the policy expects. A common cause is signing from a different workflow, branch, repository fork, or manual environment than the policy was designed to trust.

Weakening the policy to accept any valid signature proves only that someone signed the image. It no longer proves that the trusted release workflow for the expected repository produced the artifact. The correct fix is to align the policy with the intended release identity or change the workflow so it signs from the expected identity.

</details>

### Question 4

A service uses an internal package named `internal-utils`. An attacker publishes `internal-utils` with a much higher version number to a public package registry. A CI build unexpectedly installs the public package. Which controls would you add, and which evidence would show the fix is working?

<details>
<summary>Show Answer</summary>

Use scoped package names such as `@acme/internal-utils`, configure the package manager so the `@acme` scope resolves only from the private registry, and enforce lockfile-based installation in CI. For npm, that means `.npmrc` registry mapping and `npm ci`. For other ecosystems, use the equivalent private registry and lockfile or hash verification controls.

Evidence of the fix includes a lockfile entry whose resolved URL points to the private registry, CI logs showing immutable lockfile installation, dependency review that flags unexpected public packages, and an SBOM showing the expected package coordinates. You can also test the negative case by attempting to install the unscoped public package in a controlled branch and confirming CI fails.

</details>

### Question 5

A team claims they have reached SLSA Level 3 because all builds run in GitHub Actions and generate an SBOM. You are reviewing the claim for a production platform. What questions would you ask before accepting or rejecting it?

<details>
<summary>Show Answer</summary>

Ask whether the build produces authenticated provenance that names the artifact digest, source repository, source commit, build workflow, and builder identity. Then ask whether the build environment has the isolation and tamper-resistance expected for the claimed level, and whether provenance is difficult for maintainers or compromised repository workflows to falsify. An SBOM alone is not SLSA provenance; it describes contents, not necessarily the trustworthy relationship between builder, source, and artifact.

You should also ask whether policy verifies the provenance before deployment. A maturity claim is weak if provenance is generated but never checked. The likely conclusion is that hosted CI plus SBOM generation may be useful, but it does not automatically prove SLSA Level 3.

</details>

### Question 6

A cluster admission policy begins enforcing signed images for every Pod in every namespace. Several vendor controllers and emergency rollback workloads fail to start. The security team suggests disabling the policy globally to restore service. What safer response would you recommend?

<details>
<summary>Show Answer</summary>

First, restore service with a narrow, time-bound exception rather than disabling verification globally. Scope the exception to the affected namespace, image registry prefix, service account, or specific digest where possible. Record the exception owner and expiration so it does not become permanent bypass policy.

Then review audit data to refine the policy rollout. Owned application namespaces can enforce signatures from internal release workflows, while vendor images may require separate trusted identities, mirrored registries, or approved digest lists. The lesson is not that admission verification is too strict; the lesson is that enforcement should be staged and scoped with operational evidence.

</details>

### Question 7

A scanner step in CI needs read-only access to the repository, but the workflow exposes the package publishing token to all jobs through a global environment variable. The scanner action is pinned to a broad version tag. What attack path does this create, and how would you redesign the workflow?

<details>
<summary>Show Answer</summary>

A compromised scanner action could read the publishing token and upload a malicious package or image under the project's trusted name. The broad version tag adds risk because the action code can change without a reviewed commit update. The scanner becomes a supply chain dependency with access to release credentials.

Redesign the workflow so the scanner job has only read permissions and no publish token. Put publishing in a separate job that runs after tests and scans pass, grant the token only to that job, and pin third-party actions to commit SHAs. If the platform supports OIDC-based publishing or trusted publishing, prefer that over long-lived tokens.

</details>

---

## Hands-On Exercise: Build a Verifiable Release Path

In this exercise, you will create a small containerized application, generate an SBOM from the built image, scan the SBOM, sign the image digest, attach the SBOM as an attestation, and write an admission policy that would reject unsigned images. You can complete the artifact steps locally with Docker, Syft, Grype, and Cosign. The admission step requires a Kubernetes 1.35 cluster with Kyverno or a compatible image verification controller.

### Part 1: Create the Demo Application

Create a clean working directory so the release evidence is easy to inspect. The application is intentionally small because the lesson is the release path, not the web framework.

```bash
mkdir -p supply-chain-demo
cd supply-chain-demo

cat > requirements.txt <<'EOF'
flask==2.3.3
requests==2.31.0
EOF

cat > app.py <<'EOF'
from flask import Flask

app = Flask(__name__)

@app.get("/")
def hello():
    return {"service": "supply-chain-demo", "status": "ok"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
EOF

cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
EOF

docker build -t supply-chain-demo:v1 .
```

### Part 2: Generate and Inspect the SBOM

Generate the SBOM from the final image, not just from the source directory. Then inspect a few components so you can confirm the inventory includes application dependencies.

```bash
syft supply-chain-demo:v1 -o cyclonedx-json > sbom.cdx.json

jq '.components[] | select(.name == "flask" or .name == "requests") | {name, version, type}' sbom.cdx.json

grype sbom:./sbom.cdx.json
```

If Grype reports vulnerabilities, do not treat the output as a rote pass/fail result. Pick one finding and identify the package, version, severity, fixed version if available, and whether the vulnerable package came from `requirements.txt` or the base image.

### Part 3: Push by Tag, Resolve the Digest, and Sign the Digest

Set `REGISTRY_IMAGE` to a registry path you control. Docker Hub, GHCR, or an internal registry can work as long as Cosign can write signatures to it.

```bash
export REGISTRY_IMAGE="ghcr.io/YOUR_ORG/supply-chain-demo"
export TAG="v1"

docker tag supply-chain-demo:v1 "$REGISTRY_IMAGE:$TAG"
docker push "$REGISTRY_IMAGE:$TAG"

export DIGEST="$(docker buildx imagetools inspect "$REGISTRY_IMAGE:$TAG" --format '{{json .Manifest.Digest}}' | tr -d '"')"
export IMAGE_REF="$REGISTRY_IMAGE@$DIGEST"

printf 'Immutable image reference: %s\n' "$IMAGE_REF"

cosign sign --yes "$IMAGE_REF"
```

### Part 4: Attach and Verify the SBOM Attestation

Attach the SBOM to the same immutable digest. Then verify that the attestation exists. If you used keyless signing, match the certificate identity and issuer to the account or workflow you used.

```bash
cosign attest --yes \
  --predicate sbom.cdx.json \
  --type cyclonedx \
  "$IMAGE_REF"

cosign verify-attestation "$IMAGE_REF" \
  --type cyclonedx \
  --certificate-identity "YOUR_IDENTITY_HERE" \
  --certificate-oidc-issuer "YOUR_OIDC_ISSUER_HERE"
```

### Part 5: Write an Admission Policy

Create a policy that accepts only images from your registry path when they are signed by the expected identity. Apply this first in a non-production cluster or namespace. If you do not have Kyverno installed, still write the policy and explain which fields you would customize for your platform.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-supply-chain-demo
spec:
  validationFailureAction: Audit
  background: false
  rules:
    - name: verify-demo-image
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/YOUR_ORG/supply-chain-demo*"
          attestors:
            - entries:
                - keyless:
                    issuer: "YOUR_OIDC_ISSUER_HERE"
                    subject: "YOUR_SIGNER_SUBJECT_HERE"
```

Apply the policy in audit mode first, deploy a signed image by digest, and then test an unsigned image or mismatched registry path. The expected learning outcome is not merely "the policy applied." The outcome is that you can explain why the signed digest is accepted and why the negative case is rejected or audited.

### Success Criteria

- [ ] You built a demo image and recorded the immutable digest that identifies the pushed artifact.
- [ ] You generated an SBOM from the final image and inspected at least two components from the inventory.
- [ ] You scanned the SBOM and explained one finding in terms of package source, severity, and remediation path.
- [ ] You signed the image digest, not only the mutable tag.
- [ ] You attached the SBOM as an attestation to the same digest.
- [ ] You wrote an admission policy that verifies an expected signer identity for your registry path.
- [ ] You tested or described a negative case where an unsigned or mismatched image would be rejected.
- [ ] You can trace the release from source, to digest, to SBOM, to signature, to admission decision.

### Reflection Prompts

After the lab, answer these questions in your own notes. Which evidence would your incident team query first if a new CVE affected `requests`? Which identity should production admission trust for this image, and which identities should it reject? Which step in your workflow would be most dangerous if a third-party action or tool were compromised?

Your answers should reveal whether the control design is coherent. If you cannot explain who is trusted to sign, where the SBOM is stored, or how the cluster verifies the digest, the release path is not yet ready for production.

---

## Next Module

Continue to [Module 4.5: Runtime Security](../module-4.5-runtime-security/), where you will extend supply chain assurance into running workloads by detecting suspicious behavior, constraining privilege, and responding when prevention is not enough.
