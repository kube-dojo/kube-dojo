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

> **Stop and think**: Your CI/CD pipeline scans images for vulnerabilities before deployment. A supply chain attacker inserts a backdoor that contains no known CVEs — it's custom malicious code. Would your scanning catch it? What additional control is needed?

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

> **Pause and predict**: You enforce that all images must come from your private registry. An attacker compromises a developer's machine and pushes a malicious image to your private registry with a legitimate tag. What supply chain control would catch this?

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

1. **A critical vulnerability (like Log4Shell) is announced. You have 500 container images in your registry. Without an SBOM, how would you identify which images are affected? With an SBOM? Explain why this difference matters for incident response time.**
   <details>
   <summary>Answer</summary>
   Without SBOM: you must scan every single image with a vulnerability scanner, waiting for each scan to complete and hoping your scanner's database includes the CVE. For 500 images, this could take hours. Images no longer running but still in the registry might be missed. With SBOM: query your SBOM database for any image containing the affected library (e.g., "which images contain log4j-core?"). This is a database query that returns results in seconds, including exact versions. You immediately know which running workloads need patching and which images need rebuilding. The difference is hours vs. seconds for identification, which is critical when a zero-day is being actively exploited.
   </details>

2. **Your team uses `npm install` during the Docker build. An attacker publishes a package called `lodash-utils` to the public npm registry, similar to your internal package `@company/lodash-utils`. One of your developers accidentally references `lodash-utils` without the scope. What attack is this, and what controls prevent it?**
   <details>
   <summary>Answer</summary>
   This is a dependency confusion (or namespace confusion) attack. The public package takes priority over the unscoped internal name, so the build pulls the attacker's malicious package. Prevention: (1) Always use scoped package names (`@company/lodash-utils`) that can't be hijacked on the public registry; (2) Configure `.npmrc` to route scoped packages to your private registry; (3) Use `npm ci` with a lockfile (`package-lock.json`) to pin exact versions and registries; (4) Claim your package names on the public registry even if you don't publish to them; (5) Use a registry proxy (Artifactory, Nexus) that can block unknown public packages.
   </details>

3. **Your admission controller enforces that all images must come from your private registry (gcr.io/my-project). An attacker compromises a CI/CD service account and pushes a backdoored image to gcr.io/my-project/backend:v2.1. The image passes the registry allowlist. What additional supply chain control would detect this?**
   <details>
   <summary>Answer</summary>
   Image signing verification. If your CI/CD pipeline signs images with Cosign after a successful build and security scan, and the admission controller verifies signatures before allowing pods, the attacker's manually pushed image would be unsigned (or signed with different credentials) and would be rejected at admission. Additional controls: (1) Only the CI/CD pipeline's identity should be authorized to sign images; (2) Use keyless signing tied to the CI/CD OIDC identity so you can verify WHO built the image; (3) Require provenance attestation (SLSA) proving the image came from a specific git commit through a specific build process; (4) Immutable tags in the registry would prevent overwriting existing tags.
   </details>

4. **Your Dockerfile uses `FROM node:20` as the base image. Over a weekend, the `node:20` tag is updated with a new build. Monday's deployments use a different base image than Friday's, despite no code changes. Explain the risk and the fix.**
   <details>
   <summary>Answer</summary>
   Mutable tags mean the image content can change without the tag changing. Risks: (1) The new base image might introduce vulnerabilities or breaking changes; (2) Different nodes may pull different versions of `node:20`, causing inconsistent behavior; (3) If the tag was overwritten by an attacker (registry compromise), you'd pull a malicious image; (4) You can't reproduce Friday's builds because the base image is different. Fix: pin to digest — `FROM node:20@sha256:abc123...`. Digests are content-addressable and immutable — the exact same bytes are pulled every time. Update the digest explicitly when you want a new base image, after scanning and testing. This makes builds reproducible and tamper-evident.
   </details>

5. **A compliance audit requires that you can prove the provenance of every container image running in production. You use GitHub Actions for CI/CD and ECR for image storage. Design the minimal set of supply chain controls that would satisfy this requirement.**
   <details>
   <summary>Answer</summary>
   Minimal provenance controls: (1) Sign images with Cosign using keyless signing — this ties each image to the GitHub Actions OIDC identity that built it, proving WHO built it and WHEN; (2) Generate SLSA provenance attestation during the build, recording the git commit SHA, repository URL, and build workflow — proving WHAT source was used; (3) Store signatures and attestations alongside images in ECR (OCI artifacts); (4) Deploy a Kyverno or Connaisseur admission policy that verifies the Cosign signature and checks that provenance matches expected values (correct repository, correct workflow); (5) Generate and attach SBOMs to prove WHAT'S INSIDE. Together, this creates an auditable chain: git commit → GitHub Actions build → signed image with provenance → verified at admission → running in production.
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
