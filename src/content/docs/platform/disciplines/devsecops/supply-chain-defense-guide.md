---
title: "Supply Chain Defense Guide"
sidebar:
  order: 6
---
> **Practical Reference** | Applies to any project, any language, any CI/CD platform

This guide distills the lessons from real supply chain attacks -- SolarWinds (2020), Codecov (2021), the Trivy/LiteLLM incident (2026), and dozens of smaller compromises -- into a concrete checklist you can apply today. It is organized by the layer of the supply chain you are defending.

---

## 1. CI/CD Pipeline Hardening

Your CI/CD system has the keys to everything: source code, cloud credentials, package registries, container registries, Kubernetes clusters. It is the single highest-value target in your software supply chain.

### Pin all third-party actions and tools to immutable references

Git tags are mutable. A maintainer (or attacker) can rewrite what `v1` or `latest` points to at any time.

```yaml
# VULNERABLE — tag can be rewritten:
- uses: aquasecurity/trivy-action@latest
- uses: actions/checkout@v4

# SECURE — commit SHA is immutable:
- uses: aquasecurity/trivy-action@a7a829a0ece790ca07e16ed53ba6daba6e7e4e04
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

How to find the SHA for an action:
```bash
# Look up the commit SHA for a specific tag
git ls-remote https://github.com/actions/checkout refs/tags/v4.2.2
```

For tools installed via `apt`, `brew`, or `curl`, pin by version and verify checksums:
```bash
# Verify checksum after download
curl -LO https://example.com/tool-v1.2.3.tar.gz
echo "expected_sha256_hash  tool-v1.2.3.tar.gz" | sha256sum -c -
```

### Scope secrets to the jobs that need them

Never grant a security scanner access to your publish credentials. Use GitHub's `permissions:` block to enforce least privilege per job:

```yaml
jobs:
  test:
    permissions:
      contents: read          # Read-only, no secrets
    steps:
      - uses: actions/checkout@11bd719...
      - run: npm test

  scan:
    permissions:
      contents: read          # Read-only, no secrets
      security-events: write  # Upload SARIF results
    steps:
      - uses: aquasecurity/trivy-action@a7a829...

  publish:
    needs: [test, scan]
    permissions:
      id-token: write         # OIDC for Trusted Publishers
      packages: write         # Push to registry
    steps:
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### Use OIDC / Trusted Publishers instead of long-lived tokens

Long-lived API tokens (like `PYPI_PUBLISH`) can be stolen from CI environments. OIDC-based Trusted Publishers generate short-lived, scoped tokens per workflow run:

- **PyPI**: [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- **npm**: [Provenance](https://docs.npmjs.com/generating-provenance-statements)
- **Docker Hub / GHCR**: OIDC token exchange
- **AWS / GCP / Azure**: Workload Identity Federation

### Audit workflow permissions regularly

```bash
# Find all GitHub Actions with elevated permissions
grep -r "permissions:" .github/workflows/ --include="*.yml" -A 5

# Find all uses of secrets
grep -r "secrets\." .github/workflows/ --include="*.yml"

# Check for unpinned actions
grep -r "uses:.*@v[0-9]" .github/workflows/ --include="*.yml"
grep -r "uses:.*@latest" .github/workflows/ --include="*.yml"
grep -r "uses:.*@main" .github/workflows/ --include="*.yml"
```

---

## 2. Dependency Management

### Lock all dependencies with verified hashes

Every package manager supports lockfiles. Use them, and where possible, require hash verification:

| Language | Lockfile | Secure Install |
|----------|----------|----------------|
| Python | `requirements.txt` with hashes | `pip install --require-hashes -r requirements.txt` |
| Node.js | `package-lock.json` | `npm ci` (strict lockfile install) |
| Go | `go.sum` | `go mod verify` |
| Rust | `Cargo.lock` | `cargo install --locked` |
| Ruby | `Gemfile.lock` | `bundle install --frozen` |
| Java | Gradle/Maven lock | `gradle --write-locks` then `--locked` |

Generate hashes for Python:
```bash
pip-compile --generate-hashes requirements.in -o requirements.txt
```

### Prevent dependency confusion

If you use internal packages, attackers can publish a higher-versioned package with the same name on a public registry:

```ini
# .npmrc — scope internal packages to your registry
@mycompany:registry=https://npm.internal.mycompany.com
registry=https://registry.npmjs.org

# pip.conf — prioritize internal index
[global]
index-url = https://pypi.internal.mycompany.com/simple/
extra-index-url = https://pypi.org/simple/
```

Additional defenses:
- Use scoped package names (`@mycompany/utils`, not `utils`)
- Reserve your internal package names on public registries
- Configure your package manager to never fall back to public for scoped packages

### Monitor and update dependencies continuously

```yaml
# Dependabot (GitHub)
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

For self-hosted: Renovate supports all ecosystems and can auto-merge patch updates.

### Audit new dependencies before adoption

Before adding any dependency:

```bash
# Check package health signals
# - Age of package, number of maintainers, download trends
# - Recent ownership transfers (red flag)
# - Source repository matches published package

# npm
npm audit
npx socket npm:package-name  # Socket.dev analysis

# Python
pip-audit

# Go
govulncheck ./...
```

### Audit transitive dependencies, not just direct ones

The LiteLLM compromise hit many projects that never directly installed it. Cursor IDE users were affected because an MCP plugin pulled LiteLLM as a transitive dependency. Your `requirements.txt` or `package.json` may look clean while your resolved dependency tree contains hundreds of packages you never chose.

```bash
# Python — audit the full resolved graph
pip-audit                              # Scans installed packages for known vulns
pip install pipdeptree && pipdeptree   # Visualize the full dependency tree

# Node.js — audit transitive deps
npm audit --all                        # Includes transitive dependencies
npx socket report create               # Socket.dev deep analysis of full tree

# Go — list all transitive modules
go mod graph | grep litellm            # Check if a specific package is in your tree

# General — list all packages, direct + transitive
pip freeze | wc -l                     # "I depend on 12 packages" vs "I have 247 installed"
```

Make this part of CI: fail the build if a new transitive dependency appears that wasn't explicitly approved. Tools like Socket.dev and Phylum automate this.

### Defend against registry quarantine (collateral damage)

When PyPI quarantined the entire `litellm` package, **no version** was available for download -- not just the compromised v1.82.8. Every project that depended on LiteLLM had broken builds, even if they pinned a safe version.

Defenses:
- **Vendor critical dependencies**: Cache packages locally or in an internal registry (Artifactory, Nexus, GitLab Package Registry)
- **Mirror public registries**: Run a pull-through cache so builds never depend on public registry availability
- **Pin + cache in CI**: Use `pip download` or `npm pack` to pre-fetch packages and store them as build artifacts
- **Test with `--no-index`**: Periodically verify your builds succeed with only cached/vendored packages

```bash
# Cache Python deps for offline builds
pip download -r requirements.txt -d ./vendor/
# Install from cache
pip install --no-index --find-links=./vendor/ -r requirements.txt

# Node.js — use verdaccio as a local registry mirror
# npm set registry http://localhost:4873
```

This is also a business continuity issue: if a single PyPI package being quarantined breaks your deployment pipeline, your blast radius from supply chain incidents extends far beyond the compromised package.

---

## 3. Container Image Security

### Sign images and verify at admission

```bash
# Sign with Cosign (keyless, uses OIDC)
cosign sign --yes ghcr.io/myorg/myapp@sha256:abc123...

# Verify before deploy
cosign verify ghcr.io/myorg/myapp@sha256:abc123... \
  --certificate-identity-regexp 'https://github.com/myorg/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

Enforce in Kubernetes with admission control:
```yaml
# Kyverno policy: reject unsigned images
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-signature
      match:
        any:
          - resources:
              kinds: ["Pod"]
      verifyImages:
        - imageReferences: ["ghcr.io/myorg/*"]
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/myorg/*"
                    issuer: "https://token.actions.githubusercontent.com"
```

### Generate and store SBOMs for every image

```bash
# Generate at build time
trivy image --format cyclonedx myapp:latest > sbom.cdx.json

# Attach to image as attestation
cosign attest --predicate sbom.cdx.json --type cyclonedx \
  ghcr.io/myorg/myapp@sha256:abc123...

# Query later: "Are we affected by CVE-X?"
grype sbom:./sbom.cdx.json --only-vuln-id CVE-2026-XXXX
```

### Use digest references, not tags

```yaml
# VULNERABLE — tag can be overwritten:
image: nginx:1.25

# SECURE — digest is immutable:
image: nginx@sha256:6a59f1cbb8d28ac484176d52c473494859a512ddba3ea62a547258cf16c9b3...
```

Automate digest pinning with tools like `crane digest` or Renovate's `pinDigests` option.

### Scan for `.pth` files and other auto-execute mechanisms

The LiteLLM v1.82.8 attack used a Python `.pth` file that executes on **every Python interpreter startup** -- no import needed:

```bash
# Audit Python site-packages for unexpected .pth files
python -c "
import site, os
for d in site.getsitepackages():
    for f in os.listdir(d):
        if f.endswith('.pth'):
            print(f'{d}/{f}')
"

# Compare against known-good list
# Node.js equivalent: check for preinstall/postinstall scripts
npm ls --json | jq '.. | .scripts? | select(.preinstall or .postinstall)'
```

---

## 4. Kubernetes Runtime Defense

Even if your supply chain is compromised, runtime controls can detect and block the payload.

### Enforce Pod Security Standards

Block privileged containers, host mounts, and hostPID -- the exact techniques used in the LiteLLM backdoor:

```yaml
# Namespace-level enforcement
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Monitor system namespaces for anomalies

The LiteLLM backdoor deployed pods into `kube-system` because attackers know operators rarely audit it:

```yaml
# Falco rule: alert on non-system pods in kube-system
- rule: Unexpected Pod in kube-system
  desc: >
    Detect pods created in kube-system that don't match known system
    components (coredns, kube-proxy, etcd, etc.)
  condition: >
    kevt and pod and kcreate and
    k8s.ns.name = "kube-system" and
    not k8s.pod.name startswith "coredns" and
    not k8s.pod.name startswith "kube-proxy" and
    not k8s.pod.name startswith "kube-apiserver" and
    not k8s.pod.name startswith "kube-controller" and
    not k8s.pod.name startswith "kube-scheduler" and
    not k8s.pod.name startswith "etcd"
  output: >
    Unexpected pod in kube-system
    (pod=%k8s.pod.name user=%ka.user.name image=%container.image.repository)
  priority: CRITICAL
```

### Restrict egress traffic

Supply chain payloads need to exfiltrate data. Deny egress by default and allow only known destinations:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53
          protocol: UDP    # DNS only
    - to:
        - ipBlock:
            cidr: 10.0.0.0/8    # Internal services only
```

### Treat AI/LLM gateway packages as critical infrastructure

Packages like LiteLLM, LangChain, and LlamaIndex sit between your applications and multiple AI providers. By design, they have access to API keys for OpenAI, Anthropic, Azure, and other services. A compromised LLM gateway package has a disproportionate blast radius because it can:

- **Intercept and exfiltrate every API key** it routes traffic through
- **Read and log all prompts and responses**, including those containing PII or business-critical data
- **Modify model responses** silently, poisoning downstream outputs
- **Pivot to other services** using the credentials it legitimately holds

Treat LLM proxy/gateway packages with the same rigor as your database driver or auth library:
- Pin to exact versions with hash verification
- Run them in isolated network segments with egress restricted to known AI provider endpoints
- Monitor for unexpected outbound connections (the LiteLLM backdoor connected to a C2 server)
- Audit the package before every upgrade -- these packages update frequently and have large dependency trees

### Detect persistence mechanisms

Watch for systemd services, cron jobs, and startup scripts created by compromised workloads:

```bash
# Audit nodes for unexpected systemd services
for node in $(kubectl get nodes -o name); do
  kubectl debug $node -it --image=busybox -- \
    find /host/etc/systemd -name "*.service" -newer /host/etc/os-release
done
```

---

## 5. Incident Response Preparation

### Know your blast radius before an incident

Maintain a dependency graph so you can answer these questions in minutes, not days:

- "We use package X -- which services are affected?"
- "This CI token was compromised -- what can the attacker access?"
- "This container image was backdoored -- where is it running?"

```bash
# Which pods use a specific image?
kubectl get pods --all-namespaces -o json | \
  jq -r '.items[] | select(.spec.containers[].image | contains("litellm")) |
  "\(.metadata.namespace)/\(.metadata.name)"'

# Which workflows use a specific action?
grep -rl "trivy-action" .github/workflows/
```

### Credential rotation playbook

When a supply chain compromise is detected, rotate in this order:

1. **CI/CD tokens** -- package registry publish tokens, cloud credentials
2. **Kubernetes secrets** -- service account tokens, kubeconfig files
3. **Cloud credentials** -- IAM keys, service principals, workload identities
4. **Application secrets** -- database passwords, API keys, encryption keys
5. **SSH keys** -- deploy keys, user keys that were present on compromised runners

Automate rotation where possible. If you cannot rotate a credential within 15 minutes, it is too manual.

### Verify rotation is complete, not just initiated

The March 2026 Trivy/LiteLLM incident was a **second compromise** -- attackers reused credentials retained from a previous breach because remediation was not fully atomic. Starting a rotation is not the same as completing one.

After every rotation:

```bash
# Verify old credentials are actually revoked (not just new ones issued)
# PyPI: check old token returns 401
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token $OLD_TOKEN" \
  https://upload.pypi.org/legacy/

# AWS: verify old access key is disabled
aws iam list-access-keys --user-name ci-publisher \
  --query 'AccessKeyMetadata[?Status==`Active`]'

# K8s: verify old service account tokens are invalidated
kubectl get secrets -n production -o json | \
  jq '.items[] | select(.type=="kubernetes.io/service-account-token") |
  {name: .metadata.name, created: .metadata.creationTimestamp}'
```

Build a rotation verification checklist:
- [ ] New credential issued and tested
- [ ] Old credential revoked (not just deactivated)
- [ ] All systems using old credential updated to new one
- [ ] Audit log confirms old credential has zero successful auth attempts post-rotation
- [ ] Rotation documented in incident timeline with timestamps

### Maintain a known-good baseline

```bash
# Snapshot current state for comparison during incidents
kubectl get pods --all-namespaces -o json > baseline-pods.json
kubectl get sa --all-namespaces -o json > baseline-sa.json

# During incident: diff against baseline
diff <(jq -r '.items[].metadata.name' baseline-pods.json | sort) \
     <(kubectl get pods --all-namespaces -o json | jq -r '.items[].metadata.name' | sort)
```

---

## Quick Reference: Defense by Attack Stage

| Attack Stage | What Attacker Does | Your Defense |
|---|---|---|
| **Compromise CI tool** | Rewrite Git tags, push malicious release | Pin to commit SHA, verify checksums |
| **Steal CI credentials** | Exfiltrate secrets from runner environment | Scope secrets per job, use OIDC |
| **Publish malicious package** | Use stolen token to push backdoored version | Trusted Publishers (OIDC), package signing |
| **Execute on install** | `.pth` files, postinstall scripts, import hooks | Audit auto-execute mechanisms, use `--ignore-scripts` |
| **Exfiltrate data** | Harvest credentials, upload to C2 | Egress network policies, secrets encryption at rest |
| **Persist in cluster** | Deploy privileged pods, install node backdoors | Pod Security Standards, admission control, Falco |
| **Lateral movement** | Use stolen kubeconfig to access other clusters | Network segmentation, short-lived tokens, audit logging |
| **Transitive dependency** | Compromise a library used by many packages | Audit full resolved dependency tree, not just direct deps |
| **Registry quarantine** | Package yanked, all versions unavailable | Vendor/mirror critical deps, test offline builds |
| **AI gateway compromise** | Intercept API keys and prompts via LLM proxy | Isolate AI packages, restrict egress to known providers |
| **Incomplete remediation** | Reuse credentials from prior breach | Verify old creds revoked, audit post-rotation auth attempts |

---

## Checklist: Minimum Viable Supply Chain Security

Use this as a starting point. Not everything applies to every project, but most of it does.

### CI/CD
- [ ] All third-party actions/tools pinned to commit SHA or checksum
- [ ] No long-lived publish tokens -- use OIDC Trusted Publishers
- [ ] Secrets scoped to specific jobs, not available to all steps
- [ ] Workflow permissions set to minimum required per job
- [ ] CI/CD audit log enabled and monitored

### Dependencies
- [ ] Lockfile committed and enforced (`npm ci`, `pip --require-hashes`)
- [ ] Automated dependency updates (Dependabot / Renovate)
- [ ] New dependency review process (manual or automated)
- [ ] Internal packages use scoped names, reserved on public registries
- [ ] Transitive dependency tree audited (not just direct deps)
- [ ] Critical dependencies vendored or cached in internal registry
- [ ] AI/LLM gateway packages treated as critical infrastructure

### Containers
- [ ] Images signed in CI/CD (Cosign/Sigstore)
- [ ] Admission controller enforces signature verification
- [ ] SBOM generated and stored for every image
- [ ] Images referenced by digest, not tag, in production manifests

### Runtime
- [ ] Pod Security Standards enforced (at minimum `baseline`, ideally `restricted`)
- [ ] Default-deny egress NetworkPolicy in production namespaces
- [ ] Runtime detection (Falco or Tetragon) watching system namespaces
- [ ] Credential rotation can be completed within 15 minutes

### Incident Readiness
- [ ] Dependency graph maintained (know what runs where)
- [ ] Credential rotation playbook documented and tested
- [ ] Rotation verification: old credentials confirmed revoked, not just new ones issued
- [ ] Known-good baseline snapshots available for comparison
- [ ] Team has practiced a supply chain incident tabletop exercise

---

## Further Reading

- [SLSA Framework](https://slsa.dev/) -- Supply chain Levels for Software Artifacts
- [OpenSSF Scorecard](https://securityscorecards.dev/) -- Automated security health checks for open source
- [Sigstore](https://sigstore.dev/) -- Keyless signing for software artifacts
- [CNCF Supply Chain Security Best Practices](https://github.com/cncf/tag-security/tree/main/supply-chain-security)
- [Snyk: Poisoned Security Scanner Backdooring LiteLLM](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/) -- Full analysis of the March 2026 incident

---

*"The attacker only needs to find one unpinned dependency. You need to pin all of them."*
