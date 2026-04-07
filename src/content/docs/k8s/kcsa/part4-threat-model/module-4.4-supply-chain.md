---
title: "Module 4.4: Supply Chain Threats"
slug: k8s/kcsa/part4-threat-model/module-4.4-supply-chain
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Threat awareness
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 4.3: Container Escape](../module-4.3-container-escape/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Identify** supply chain attack vectors: compromised base images, malicious dependencies, tampered pipelines
2. **Evaluate** image provenance and signing mechanisms (cosign, Sigstore, SLSA)
3. **Assess** CI/CD pipeline security for injection points and trust boundary violations
4. **Explain** how admission controllers can enforce image signing and registry restrictions

---

## Why This Module Matters

Supply chain attacks compromise trusted components before they reach your cluster. A malicious container image, compromised dependency, or tampered CI/CD pipeline can bypass all runtime security controls because the attack is embedded in trusted artifacts.

KCSA tests your understanding of software supply chain risks and the controls to mitigate them.

---

## What is a Supply Chain Attack?

```
┌─────────────────────────────────────────────────────────────┐
│              SUPPLY CHAIN ATTACK DEFINED                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LEGITIMATE SUPPLY CHAIN:                                  │
│  Developer → Code → Build → Image → Registry → Cluster     │
│      ✓        ✓       ✓       ✓        ✓          ✓       │
│                                                             │
│  SUPPLY CHAIN ATTACK:                                      │
│  Any point in the chain can be compromised                 │
│                                                             │
│  Developer → Code → Build → Image → Registry → Cluster     │
│      ✓        ✓       ✓       ✓        ✓          ✓       │
│              ↑                  ↑                           │
│           Malicious          Tampered                      │
│          dependency          image                         │
│                                                             │
│  IMPACT:                                                   │
│  • Malicious code runs with full trust                    │
│  • Bypasses runtime security controls                      │
│  • Can affect many clusters/organizations                  │
│  • Difficult to detect                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Attack Vectors

### 1. Malicious Base Images

```
┌─────────────────────────────────────────────────────────────┐
│              BASE IMAGE ATTACKS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TYPOSQUATTING                                             │
│  ├── Create: ngimx/nginx (misspelled)                      │
│  ├── User mistypes: pulls malicious image                  │
│  └── Contains: Backdoor, cryptominer, etc.                 │
│                                                             │
│  COMPROMISED MAINTAINER                                    │
│  ├── Attacker gains access to image maintainer             │
│  ├── Pushes malicious update                               │
│  └── All users pulling :latest get backdoor                │
│                                                             │
│  ABANDONED IMAGES                                          │
│  ├── Popular image stops being maintained                  │
│  ├── Vulnerabilities accumulate                            │
│  └── No security patches available                         │
│                                                             │
│  MITIGATION:                                               │
│  • Use official/verified images only                       │
│  • Pin to digest, not tag                                  │
│  • Scan all images before use                              │
│  • Build your own base images                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: You pin your base images by SHA256 digest to ensure immutability. If the maintainers of that exact base image release an emergency patch for a zero-day vulnerability, what happens to your build pipeline, and how does your cluster respond?

### 2. Compromised Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│              DEPENDENCY ATTACKS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MALICIOUS PACKAGE                                         │
│  ├── Attacker publishes package to npm/PyPI/etc.           │
│  ├── Package name similar to popular library               │
│  ├── Developer installs wrong package                      │
│  └── Malicious code executes at build or runtime           │
│                                                             │
│  DEPENDENCY CONFUSION                                      │
│  ├── Company has internal package "auth-utils"             │
│  ├── Attacker publishes "auth-utils" to public registry    │
│  ├── Build system pulls public (higher version)            │
│  └── Public malicious package installed                    │
│                                                             │
│  COMPROMISED MAINTAINER                                    │
│  ├── Attacker gains access to package maintainer           │
│  ├── Pushes malicious version                              │
│  └── All downstream projects affected                      │
│                                                             │
│  EXAMPLES:                                                 │
│  • event-stream (npm) - Bitcoin wallet theft               │
│  • ua-parser-js (npm) - Cryptominer injection              │
│  • PyPI typosquatting attacks                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. CI/CD Pipeline Attacks

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD PIPELINE ATTACKS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ATTACK SURFACES:                                          │
│                                                             │
│  Source Repository                                         │
│  ├── Stolen credentials                                    │
│  ├── Compromised developer workstation                     │
│  └── Direct code injection                                 │
│                                                             │
│  Build System                                              │
│  ├── Malicious build scripts                               │
│  ├── Compromised build agents                              │
│  └── Environment variable injection                        │
│                                                             │
│  Artifact Storage                                          │
│  ├── Registry credential theft                             │
│  ├── Image replacement                                     │
│  └── Tag overwriting                                       │
│                                                             │
│  Deployment                                                │
│  ├── Manifest tampering                                    │
│  ├── Secret injection                                      │
│  └── Configuration modification                            │
│                                                             │
│  REAL-WORLD: SolarWinds (build system compromise)          │
│  REAL-WORLD: Codecov (bash uploader tampering)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Image Registry Attacks

```
┌─────────────────────────────────────────────────────────────┐
│              REGISTRY ATTACKS                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TAG MUTABILITY                                            │
│  ├── Pull image:v1.0 on Monday                             │
│  ├── Attacker overwrites image:v1.0 on Tuesday             │
│  ├── New node pulls image:v1.0 on Wednesday                │
│  └── Different (malicious) image running                   │
│                                                             │
│  REGISTRY COMPROMISE                                       │
│  ├── Attacker gains registry access                        │
│  ├── Replaces images with backdoored versions              │
│  └── All clusters pulling from registry affected           │
│                                                             │
│  MAN-IN-THE-MIDDLE                                         │
│  ├── Intercept registry traffic                            │
│  ├── Serve malicious image                                 │
│  └── Bypassed if not using digest verification             │
│                                                             │
│  MITIGATION:                                               │
│  • Immutable tags                                          │
│  • Image signing                                           │
│  • Pull by digest                                          │
│  • Private registries                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Supply Chain Security Controls

### Image Signing and Verification

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE SIGNING                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONCEPT:                                                  │
│  • Sign images after build                                 │
│  • Verify signature before deployment                      │
│  • Reject unsigned/incorrectly signed images               │
│                                                             │
│  TOOLS:                                                    │
│  ├── Cosign (Sigstore) - Keyless signing                  │
│  ├── Notary v2 - Content trust                            │
│  └── Docker Content Trust (DCT)                           │
│                                                             │
│  COSIGN WORKFLOW:                                          │
│  1. Build image                                            │
│  2. Sign: cosign sign --key cosign.key myimage:tag        │
│  3. Push signature to registry                             │
│  4. Verify: cosign verify --key cosign.pub myimage:tag    │
│                                                             │
│  KEYLESS SIGNING (Sigstore):                              │
│  • Uses OIDC identity (GitHub, Google, etc.)              │
│  • No key management                                       │
│  • Transparent, auditable                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Admission Control for Images

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE ADMISSION CONTROL                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENFORCE AT CLUSTER LEVEL:                                 │
│                                                             │
│  1. ALLOWED REGISTRIES                                     │
│     Only allow images from trusted registries              │
│     Block: docker.io, allow: gcr.io/my-project             │
│                                                             │
│  2. SIGNATURE VERIFICATION                                 │
│     Require valid signatures on all images                 │
│     Tools: Kyverno, OPA/Gatekeeper, Connaisseur           │
│                                                             │
│  3. VULNERABILITY SCANNING                                 │
│     Block images with critical CVEs                        │
│     Tools: Trivy, Snyk, Anchore                           │
│                                                             │
│  4. IMAGE DIGEST REQUIREMENT                               │
│     Require digest, reject tags                            │
│     image: nginx@sha256:abc123...                         │
│                                                             │
│  KYVERNO POLICY EXAMPLE:                                   │
│  Verify images are signed with specific key               │
│  before allowing pod creation                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### SBOM (Software Bill of Materials)

```
┌─────────────────────────────────────────────────────────────┐
│              SOFTWARE BILL OF MATERIALS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT IS SBOM?                                             │
│  • Inventory of all components in software                 │
│  • Lists packages, versions, licenses                      │
│  • Enables vulnerability tracking                          │
│                                                             │
│  FORMATS:                                                  │
│  ├── SPDX (ISO standard)                                  │
│  ├── CycloneDX (OWASP)                                    │
│  └── SWID tags                                            │
│                                                             │
│  GENERATION TOOLS:                                         │
│  ├── Syft (Anchore)                                       │
│  ├── Trivy (Aqua)                                         │
│  └── Docker Scout                                         │
│                                                             │
│  USE CASES:                                                │
│  • Vulnerability response (find affected images)           │
│  • License compliance                                      │
│  • Dependency tracking                                     │
│  • Incident response                                       │
│                                                             │
│  EXAMPLE: Log4Shell response                              │
│  With SBOM: Query "which images have log4j?"              │
│  Without SBOM: Manual scanning of all images              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Secure Supply Chain Practices

### Image Security

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE SECURITY CHECKLIST                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BUILD PHASE                                               │
│  ☐ Use minimal base images (distroless, scratch)           │
│  ☐ Multi-stage builds (separate build/runtime)             │
│  ☐ Pin base image to digest                                │
│  ☐ Scan during build, fail on critical CVEs                │
│  ☐ Generate SBOM                                           │
│                                                             │
│  SIGN AND STORE                                            │
│  ☐ Sign images after build                                 │
│  ☐ Use private registry                                    │
│  ☐ Enable immutable tags                                   │
│  ☐ Store signatures with images                            │
│                                                             │
│  DEPLOY                                                    │
│  ☐ Pull by digest, not tag                                 │
│  ☐ Verify signatures at admission                          │
│  ☐ Allow only approved registries                          │
│  ☐ Block images with critical vulnerabilities              │
│                                                             │
│  RUNTIME                                                   │
│  ☐ Continuous scanning in registry                         │
│  ☐ Alert on new CVEs in running images                     │
│  ☐ Have patching/rebuild process                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### CI/CD Security

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD SECURITY CONTROLS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SOURCE CODE                                               │
│  ├── Require code review for all changes                   │
│  ├── Branch protection rules                               │
│  ├── Signed commits                                        │
│  └── Dependency scanning in PR                             │
│                                                             │
│  BUILD ENVIRONMENT                                         │
│  ├── Ephemeral build agents                                │
│  ├── Minimal build permissions                             │
│  ├── Isolated build environments                           │
│  └── Audit logging of all builds                           │
│                                                             │
│  SECRETS MANAGEMENT                                        │
│  ├── No secrets in code/env vars                           │
│  ├── Use secret managers (Vault, AWS Secrets)              │
│  ├── Rotate credentials regularly                          │
│  └── Audit secret access                                   │
│                                                             │
│  DEPLOYMENT                                                │
│  ├── GitOps (declarative, auditable)                       │
│  ├── Require approval for production                       │
│  ├── Verify artifacts before deploy                        │
│  └── Rollback capability                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Supply Chain Frameworks

> **Pause and predict**: You have successfully implemented Sigstore/Cosign to sign all images built by your CI/CD pipeline. However, during a red team exercise, an attacker manages to bypass this by deploying a malicious container. Assuming the cryptographic signatures themselves weren't forged, what misconfiguration in the cluster's admission control could allow this to happen?

### SLSA (Supply-chain Levels for Software Artifacts)

```
┌─────────────────────────────────────────────────────────────┐
│              SLSA FRAMEWORK                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SLSA = Supply-chain Levels for Software Artifacts         │
│  Pronounced "salsa"                                        │
│                                                             │
│  LEVELS:                                                   │
│                                                             │
│  Level 0: No guarantees                                    │
│  └── No provenance, no verification                        │
│                                                             │
│  Level 1: Provenance exists                                │
│  └── Build process generates provenance                    │
│                                                             │
│  Level 2: Hosted build platform                            │
│  └── Build on hosted, managed platform                     │
│                                                             │
│  Level 3: Hardened builds                                  │
│  └── Isolated, ephemeral build environments                │
│                                                             │
│  PROVENANCE:                                               │
│  • Who built it?                                           │
│  • What source was used?                                   │
│  • What build process?                                     │
│  • Cryptographically signed attestation                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Sigstore Ecosystem

```
┌─────────────────────────────────────────────────────────────┐
│              SIGSTORE ECOSYSTEM                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  COMPONENTS:                                               │
│                                                             │
│  Cosign                                                    │
│  ├── Container signing and verification                    │
│  ├── Keyless signing with OIDC                            │
│  └── Store signatures in OCI registries                    │
│                                                             │
│  Fulcio                                                    │
│  ├── Certificate authority for Sigstore                    │
│  ├── Issues short-lived certificates                       │
│  └── Based on OIDC identity                                │
│                                                             │
│  Rekor                                                     │
│  ├── Transparency log                                      │
│  ├── Immutable record of signatures                        │
│  └── Public, auditable                                     │
│                                                             │
│  KEYLESS WORKFLOW:                                         │
│  1. Authenticate with OIDC (GitHub, Google)                │
│  2. Fulcio issues short-lived cert                         │
│  3. Sign artifact with cert                                │
│  4. Record in Rekor transparency log                       │
│  5. Verifier checks Rekor + OIDC identity                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The SolarWinds attack** compromised 18,000+ organizations through a single supply chain breach. Build systems are high-value targets.

- **Typosquatting accounts for thousands of malicious packages**. A single character difference (e.g., `lodash` vs `1odash`) can lead to compromise.

- **SBOM is becoming mandatory** in many sectors. US Executive Order 14028 requires SBOM for software sold to the federal government.

- **Keyless signing with Sigstore** eliminates key management—one of the biggest barriers to image signing adoption.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using :latest tag | Mutable, unpredictable | Pin to digest |
| No image scanning | Unknown vulnerabilities | Scan in CI and registry |
| Trusting public images | May be compromised | Build/verify your own |
| Hardcoded secrets in CI | Exposed in logs/history | Use secret managers |
| No provenance | Can't verify origin | Implement SLSA |

---

## Quiz

1. **Scenario:** A zero-day vulnerability is announced in a popular JSON parsing library used across your organization. Your security team needs to know exactly which of the 500 running microservices are vulnerable within the next hour.
   **Question:** How does having a Software Bill of Materials (SBOM) integrated into your CI/CD pipeline fundamentally change your incident response capabilities in this scenario compared to traditional container scanning?
   <details>
   <summary>Answer</summary>
   Traditional container scanning requires actively analyzing the filesystem of every running or stored image to detect the vulnerable library, a resource-intensive process that can take hours for 500 microservices. An SBOM acts as a comprehensive, pre-computed inventory of all dependencies, licenses, and packages embedded within an application at build time. By querying the SBOM database, the security team can instantly identify which specific images and versions contain the vulnerable JSON parser. This fundamental shift from reactive scanning to proactive querying drastically reduces the mean time to identify (MTTI), allowing teams to focus immediately on patching rather than discovery.
   </details>

2. **Scenario:** Your build pipeline relies on a mix of public and private npm packages. During a routine build, the pipeline unexpectedly pulls a malicious version of an internal package named `auth-helpers` from the public npm registry instead of your private repository, leading to compromised credentials.
   **Question:** Why did the build system prioritize the malicious public package over the internal one, and what specific architectural controls must be implemented to prevent this supply chain vector?
   <details>
   <summary>Answer</summary>
   This incident is a classic dependency confusion attack, which occurs because package managers often default to pulling the highest available version number from public registries over private ones. The attacker exploited this behavior by publishing `auth-helpers` to the public registry with an artificially high version number, causing the build system to "upgrade" to the malicious payload. To prevent this, organizations must enforce namespace scoping (e.g., `@company/auth-helpers`) to segregate internal packages. Additionally, build systems must be explicitly configured to route private scopes exclusively to internal registries or use proxy caches that block upstream resolution for internal namespace patterns.
   </details>

3. **Scenario:** Your cluster is configured with an admission controller that strictly enforces an allowed registry policy, blocking any image not pulled from your organization's private ECR. Despite this, an attacker who compromised a developer's laptop successfully deployed a backdoored image into the production namespace.
   **Question:** Since the allowed registry policy was not bypassed, how did the malicious image execute, and what cryptographic control is missing from the admission process to validate the artifact's integrity?
   <details>
   <summary>Answer</summary>
   The allowed registry policy only verifies the source location of the image, not the authenticity or integrity of the image itself. The attacker was able to push a backdoored image to the private ECR using stolen credentials, meaning the admission controller saw a valid registry URI and permitted the deployment. To prevent this, the cluster requires an image signing validation mechanism, such as Cosign integrated with Kyverno or Gatekeeper. By enforcing signature verification at admission time, the cluster ensures that only images cryptographically signed by the automated CI/CD pipeline—and not those pushed manually by a compromised user—are allowed to run.
   </details>

4. **Scenario:** A development team frequently deploys a microservice using the `FROM node:20-alpine` base image. A critical production bug appears on Wednesday, but developers cannot reproduce it locally using the exact same Git commit that was deployed on Tuesday.
   **Question:** Why might the container environment differ between the Tuesday deployment and Wednesday's local debugging session despite identical source code, and how does this highlight a fundamental flaw in using mutable image references?
   <details>
   <summary>Answer</summary>
   The `node:20-alpine` tag is mutable, meaning the underlying image it points to can be updated by its maintainers at any time. Between the Tuesday deployment and the Wednesday debugging session, the maintainers likely pushed a new version of the base image (e.g., updating system libraries), resulting in the local build pulling a different filesystem than the one running in production. This non-deterministic build behavior makes troubleshooting nearly impossible and introduces the risk of upstream vulnerabilities being pulled automatically. To fix this, the Dockerfile must pin the base image to an immutable SHA256 digest (e.g., `FROM node:20-alpine@sha256:1234...`), ensuring the exact same byte-for-byte environment is used across all stages.
   </details>

5. **Scenario:** An external auditor is evaluating your Kubernetes environment against the SLSA (Supply-chain Levels for Software Artifacts) framework. They find that while all your container images are cryptographically signed using Cosign, you cannot definitively prove that the images were built from the approved main branch of your source repository.
   **Question:** Why does image signing alone fail to satisfy the auditor's requirement, and what specific metadata must be generated during the build process to establish verifiable provenance?
   <details>
   <summary>Answer</summary>
   Image signing guarantees that an artifact has not been tampered with after it was built, and verifies the identity of the signer, but it provides no context about the build process itself. An attacker with access to the signing keys could build an image from a compromised local machine or a malicious branch and sign it successfully. To establish verifiable provenance, the CI/CD pipeline must generate a cryptographic attestation (such as an in-toto formatted SLSA provenance document) that records the exact Git commit SHA, the build instructions used, and the environment details. This metadata must be stored alongside the signature so the admission controller can independently verify both the integrity of the image and that it originated from the approved source code workflow.
   </details>

---

## Hands-On Exercise: Supply Chain Risk Assessment

**Scenario**: Review this CI/CD setup and identify supply chain risks:

```yaml
# Dockerfile
FROM ubuntu:latest
RUN apt-get update && apt-get install -y nodejs npm
COPY package.json .
RUN npm install
COPY . .
CMD ["node", "app.js"]

# CI Pipeline
steps:
  - checkout
  - run: docker build -t myapp .
  - run: docker push myregistry/myapp:latest
  - run: kubectl set image deployment/myapp myapp=myregistry/myapp:latest
```

**Identify the supply chain risks:**

<details>
<summary>Supply Chain Risks</summary>

**Dockerfile Issues:**

1. **FROM ubuntu:latest**
   - Mutable tag, unpredictable content
   - Large image with many packages
   - Fix: Use pinned digest, minimal base image

2. **apt-get install nodejs npm**
   - Installing from public repos at build time
   - No version pinning
   - Fix: Use official Node image or pin versions

3. **npm install without lockfile**
   - Dependency versions may change between builds
   - Vulnerable to dependency confusion
   - Fix: Use npm ci with package-lock.json

**CI Pipeline Issues:**

4. **No image scanning**
   - Vulnerabilities not detected before push
   - Fix: Add trivy/grype scan step

5. **No image signing**
   - No way to verify image authenticity
   - Fix: Sign with cosign after build

6. **Push to :latest**
   - Mutable tag
   - Fix: Use commit SHA or version tag + digest

7. **kubectl set image with tag**
   - Pods may pull different images
   - Fix: Use digest in deployment

8. **No approval/gate**
   - Direct push to production
   - Fix: Add manual approval step

**Secure version concept:**
- Pin base image to digest
- Use lockfiles for dependencies
- Scan images for CVEs
- Sign images after build
- Push with immutable tags
- Verify signatures at admission
- Use GitOps with approval gates

</details>

---

## Summary

Supply chain security protects the path from code to cluster:

| Attack Vector | Examples | Prevention |
|--------------|----------|------------|
| **Base images** | Typosquatting, compromised | Pin digest, verify, scan |
| **Dependencies** | Malicious packages, confusion | Lockfiles, scanning, private repos |
| **CI/CD** | Build compromise, secret theft | Isolated builds, secret management |
| **Registry** | Tag overwrite, compromise | Signing, digest, immutable tags |

Key controls:
- Sign images and verify at admission
- Generate and maintain SBOMs
- Scan continuously for vulnerabilities
- Implement SLSA for provenance
- Use GitOps for auditable deployments

---

## Next Module

[Module 5.1: Image Security](../part5-platform-security/module-5.1-image-security/) - Securing container images through the lifecycle.