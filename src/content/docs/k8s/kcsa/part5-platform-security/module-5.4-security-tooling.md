---
title: "Module 5.4: Security Tooling"
slug: k8s/kcsa/part5-platform-security/module-5.4-security-tooling
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Tool awareness
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 5.3: Runtime Security](../module-5.3-runtime-security/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Identify** key security tools by category: scanning (Trivy), policy (OPA/Kyverno), runtime (Falco), auditing (kube-bench)
2. **Evaluate** which tools address which phases of the security lifecycle (build, deploy, runtime)
3. **Compare** policy engines (OPA Gatekeeper vs. Kyverno) by architecture and use case
4. **Assess** a security tooling stack for coverage gaps across the Kubernetes attack surface

---

## Why This Module Matters

The Kubernetes security ecosystem has a rich set of tools for scanning, monitoring, enforcing, and auditing security. Knowing which tools exist, what they do, and when to use them helps you build a comprehensive security program.

KCSA tests your awareness of common security tools and their purposes.

---

## Security Tool Categories

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES SECURITY TOOLS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IMAGE SECURITY                                            │
│  ├── Scanning: Trivy, Grype, Clair                        │
│  ├── Signing: Cosign, Notary                              │
│  └── SBOM: Syft, Trivy                                    │
│                                                             │
│  CLUSTER HARDENING                                         │
│  ├── Benchmarks: kube-bench                               │
│  ├── Auditing: kubeaudit, Polaris                         │
│  └── Penetration: kube-hunter                             │
│                                                             │
│  POLICY ENFORCEMENT                                        │
│  ├── Admission: OPA/Gatekeeper, Kyverno                   │
│  ├── Network: CNI policies, Cilium                        │
│  └── Runtime: Seccomp, AppArmor                           │
│                                                             │
│  RUNTIME SECURITY                                          │
│  ├── Detection: Falco, Tetragon                           │
│  ├── Sandboxing: gVisor, Kata                             │
│  └── Platforms: Aqua, Sysdig, Prisma                      │
│                                                             │
│  SECRETS MANAGEMENT                                        │
│  ├── External: Vault, AWS Secrets Manager                 │
│  └── Encryption: SealedSecrets, SOPS                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Image Scanning Tools

### Trivy

```
┌─────────────────────────────────────────────────────────────┐
│              TRIVY                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Comprehensive security scanner                       │
│  BY: Aqua Security (open source)                           │
│                                                             │
│  SCANS:                                                    │
│  ├── Container images (OS + language packages)            │
│  ├── Filesystems and repositories                         │
│  ├── Kubernetes manifests (misconfigurations)             │
│  ├── IaC (Terraform, CloudFormation)                      │
│  └── SBOM generation                                       │
│                                                             │
│  KEY FEATURES:                                             │
│  ├── Fast (local DB, no network for scanning)             │
│  ├── Comprehensive (multiple scanners in one)             │
│  ├── CI/CD integration (exit codes for failures)          │
│  └── Multiple output formats (JSON, SARIF, etc.)          │
│                                                             │
│  COMMANDS:                                                 │
│  trivy image nginx:1.25                                   │
│  trivy fs .                                               │
│  trivy k8s --report summary                               │
│  trivy config Dockerfile                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Grype

```
┌─────────────────────────────────────────────────────────────┐
│              GRYPE                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Vulnerability scanner for containers                 │
│  BY: Anchore (open source)                                 │
│                                                             │
│  SCANS:                                                    │
│  ├── Container images                                      │
│  ├── Filesystems                                           │
│  ├── SBOMs (from Syft)                                    │
│  └── Archives (tar, zip)                                   │
│                                                             │
│  KEY FEATURES:                                             │
│  ├── Fast scanning                                        │
│  ├── Works with Syft SBOMs                                │
│  ├── Multiple DB sources                                  │
│  └── CI/CD friendly                                       │
│                                                             │
│  PAIRS WITH SYFT:                                          │
│  Syft generates SBOM → Grype scans SBOM for CVEs          │
│                                                             │
│  COMMANDS:                                                 │
│  grype nginx:1.25                                         │
│  grype sbom:./sbom.json                                   │
│  grype dir:/path/to/project                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Image Signing: Cosign

```
┌─────────────────────────────────────────────────────────────┐
│              COSIGN                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Container image signing and verification             │
│  BY: Sigstore project (Linux Foundation)                   │
│                                                             │
│  FEATURES:                                                 │
│  ├── Sign container images                                │
│  ├── Store signatures in OCI registries                   │
│  ├── Keyless signing (OIDC identity)                      │
│  ├── Transparency log (Rekor)                             │
│  └── Attestation support                                  │
│                                                             │
│  WORKFLOW:                                                 │
│  # Generate key pair                                       │
│  cosign generate-key-pair                                 │
│                                                             │
│  # Sign image                                              │
│  cosign sign --key cosign.key myregistry/myimage:v1       │
│                                                             │
│  # Verify signature                                        │
│  cosign verify --key cosign.pub myregistry/myimage:v1     │
│                                                             │
│  # Keyless signing (uses OIDC)                            │
│  cosign sign myregistry/myimage:v1                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Cluster Security Assessment

### kube-bench

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-BENCH                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: CIS Kubernetes Benchmark checker                     │
│  BY: Aqua Security (open source)                           │
│                                                             │
│  CHECKS:                                                   │
│  ├── Control plane component configuration                │
│  ├── etcd configuration                                   │
│  ├── Control plane configuration files                    │
│  ├── Worker node configuration                            │
│  └── Kubernetes policies                                  │
│                                                             │
│  OUTPUT:                                                   │
│  [PASS] 1.1.1 Ensure API server pod spec file perms        │
│  [FAIL] 1.1.2 Ensure API server pod spec ownership         │
│  [WARN] 1.2.1 Ensure anonymous-auth is disabled           │
│                                                             │
│  RUN AS:                                                   │
│  # On master node                                          │
│  kube-bench run --targets master                          │
│                                                             │
│  # On worker node                                          │
│  kube-bench run --targets node                            │
│                                                             │
│  # As Job in cluster                                       │
│  kubectl apply -f job.yaml                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### kubeaudit

```
┌─────────────────────────────────────────────────────────────┐
│              KUBEAUDIT                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Kubernetes security auditing tool                    │
│  BY: Shopify (open source)                                 │
│                                                             │
│  AUDITS FOR:                                               │
│  ├── Privileged containers                                │
│  ├── Running as root                                      │
│  ├── Capabilities                                         │
│  ├── Host namespace usage                                 │
│  ├── Read-only filesystem                                 │
│  ├── Service account tokens                               │
│  ├── Network policies                                     │
│  └── Resource limits                                      │
│                                                             │
│  MODES:                                                    │
│  ├── Cluster mode - audit running cluster                 │
│  ├── Manifest mode - audit YAML files                     │
│  └── Local mode - audit current context                   │
│                                                             │
│  COMMANDS:                                                 │
│  kubeaudit all                     # All audits           │
│  kubeaudit privileged              # Check for privileged │
│  kubeaudit rootfs                  # Check read-only FS   │
│  kubeaudit -f deployment.yaml      # Audit manifest       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Polaris

```
┌─────────────────────────────────────────────────────────────┐
│              POLARIS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Best practices validation                            │
│  BY: Fairwinds (open source)                               │
│                                                             │
│  VALIDATES:                                                │
│  ├── Security (privileged, root, capabilities)            │
│  ├── Reliability (resource requests, probes)              │
│  ├── Efficiency (resource limits)                         │
│  └── Custom checks                                        │
│                                                             │
│  DEPLOYMENT OPTIONS:                                       │
│  ├── Dashboard - Web UI for cluster                       │
│  ├── CLI - Local scanning                                 │
│  ├── Admission Controller - Block bad configs             │
│  └── CI/CD - Scan before deploy                           │
│                                                             │
│  SCORING:                                                  │
│  Provides letter grades (A-F) based on checks             │
│  Helps prioritize remediation                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### kube-hunter

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-HUNTER                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Kubernetes penetration testing tool                  │
│  BY: Aqua Security (open source)                           │
│                                                             │
│  FINDS:                                                    │
│  ├── Exposed API servers                                  │
│  ├── Kubelet exposures                                    │
│  ├── etcd exposures                                       │
│  ├── Sensitive information disclosure                     │
│  └── Known vulnerabilities                                │
│                                                             │
│  MODES:                                                    │
│  ├── Remote - Scan from outside cluster                   │
│  ├── Internal - Scan from inside (as pod)                 │
│  └── Network - Scan IP range                              │
│                                                             │
│  COMMANDS:                                                 │
│  # Remote scan                                             │
│  kube-hunter --remote 192.168.1.100                       │
│                                                             │
│  # Internal scan (run as pod)                              │
│  kube-hunter --pod                                        │
│                                                             │
│  # Active exploitation (use carefully!)                    │
│  kube-hunter --active                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Policy Enforcement Tools

### OPA Gatekeeper vs Kyverno

```
┌─────────────────────────────────────────────────────────────┐
│              POLICY ENGINE COMPARISON                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OPA GATEKEEPER                                            │
│  ├── Policy language: Rego                                │
│  ├── Learning curve: Steeper                              │
│  ├── Flexibility: Very high                               │
│  ├── Beyond K8s: Yes (OPA is general-purpose)             │
│  ├── Ecosystem: Large, mature                             │
│  └── Good for: Complex policies, existing OPA users       │
│                                                             │
│  KYVERNO                                                   │
│  ├── Policy language: YAML (Kubernetes-native)            │
│  ├── Learning curve: Gentler                              │
│  ├── Flexibility: High                                    │
│  ├── Beyond K8s: No (Kubernetes-specific)                 │
│  ├── Features: Validate, mutate, generate, verify         │
│  └── Good for: K8s-only, YAML-familiar teams              │
│                                                             │
│  BOTH CAN:                                                 │
│  • Block bad configurations at admission                  │
│  • Enforce organizational policies                         │
│  • Audit existing resources                               │
│  • Report violations                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Runtime Security Tools

### Falco Deep Dive

```
┌─────────────────────────────────────────────────────────────┐
│              FALCO ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DATA SOURCES:                                             │
│  ├── System calls (kernel module or eBPF)                 │
│  ├── Kubernetes audit logs                                │
│  └── Cloud audit logs (AWS CloudTrail, etc.)              │
│                                                             │
│  RULE ENGINE:                                              │
│  Rules written in Falco rule language                      │
│  - rule: Terminal shell in container                      │
│    condition: spawned_process and container and shell     │
│    output: Shell in container (user=%user.name ...)       │
│    priority: WARNING                                       │
│                                                             │
│  OUTPUT CHANNELS:                                          │
│  ├── Stdout / syslog                                      │
│  ├── File                                                 │
│  ├── HTTP webhook                                         │
│  ├── Slack / Teams                                        │
│  ├── Kafka / NATS                                         │
│  └── gRPC                                                 │
│                                                             │
│  DEPLOYMENT:                                               │
│  ├── DaemonSet on nodes                                   │
│  └── Requires privileged (for eBPF/kernel module)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Tetragon

```
┌─────────────────────────────────────────────────────────────┐
│              TETRAGON                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: eBPF-based security observability and enforcement    │
│  BY: Cilium/Isovalent (CNCF)                              │
│                                                             │
│  MONITORS:                                                 │
│  ├── Process execution                                    │
│  ├── File access                                          │
│  ├── Network activity                                     │
│  └── System calls                                         │
│                                                             │
│  KEY FEATURES:                                             │
│  ├── Enforcement (not just detection)                     │
│  ├── Low overhead (in-kernel eBPF)                        │
│  ├── Rich Kubernetes context                              │
│  └── TracingPolicy CRDs                                   │
│                                                             │
│  VS FALCO:                                                 │
│  ├── Both: eBPF-based runtime monitoring                  │
│  ├── Tetragon: More enforcement focus                     │
│  ├── Tetragon: Tighter Cilium integration                 │
│  └── Falco: More mature, larger rule library              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Secrets Management Tools

### HashiCorp Vault

```
┌─────────────────────────────────────────────────────────────┐
│              VAULT WITH KUBERNETES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Enterprise secrets management                        │
│  BY: HashiCorp                                             │
│                                                             │
│  INTEGRATION METHODS:                                      │
│                                                             │
│  1. VAULT AGENT INJECTOR                                   │
│     ├── Sidecar automatically injects secrets             │
│     ├── Annotations control what secrets to inject         │
│     └── Secrets written to shared volume                   │
│                                                             │
│  2. CSI DRIVER                                             │
│     ├── Mounts secrets as volumes                         │
│     └── Kubernetes CSI standard                            │
│                                                             │
│  3. EXTERNAL SECRETS OPERATOR                              │
│     ├── Syncs Vault secrets to K8s Secrets                │
│     └── Automatic rotation                                 │
│                                                             │
│  BENEFITS:                                                 │
│  • Dynamic secrets (auto-generated)                       │
│  • Automatic rotation                                      │
│  • Detailed audit logging                                 │
│  • Fine-grained access control                            │
│  • Encryption as a service                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Sealed Secrets

```
┌─────────────────────────────────────────────────────────────┐
│              SEALED SECRETS                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: Encrypt secrets for GitOps                           │
│  BY: Bitnami                                               │
│                                                             │
│  PROBLEM SOLVED:                                           │
│  • Can't commit K8s Secrets to Git (base64 encoded)        │
│  • Need secrets in version control for GitOps              │
│                                                             │
│  HOW IT WORKS:                                             │
│  1. Install controller in cluster                          │
│  2. Controller generates public/private key pair           │
│  3. Use kubeseal CLI to encrypt secrets with public key    │
│  4. Commit encrypted SealedSecret to Git                   │
│  5. Controller decrypts to regular Secret in cluster       │
│                                                             │
│  WORKFLOW:                                                 │
│  kubectl create secret ... --dry-run -o yaml |            │
│    kubeseal > sealed-secret.yaml                          │
│  git add sealed-secret.yaml                               │
│  git commit -m "Add encrypted secret"                     │
│                                                             │
│  SealedSecret → Git → Cluster → Secret                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Mesh Security

### Istio Security Features

```
┌─────────────────────────────────────────────────────────────┐
│              ISTIO SECURITY                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  mTLS (MUTUAL TLS)                                         │
│  ├── Automatic certificate management                     │
│  ├── Encryption between all services                      │
│  ├── Service identity via SPIFFE                          │
│  └── Modes: STRICT, PERMISSIVE, DISABLE                   │
│                                                             │
│  AUTHORIZATION POLICIES                                    │
│  ├── Allow/deny based on source service                   │
│  ├── Method, path, header matching                        │
│  ├── JWT validation                                       │
│  └── More granular than NetworkPolicy                     │
│                                                             │
│  EXAMPLE:                                                  │
│  apiVersion: security.istio.io/v1beta1                    │
│  kind: AuthorizationPolicy                                │
│  spec:                                                    │
│    selector:                                              │
│      matchLabels:                                         │
│        app: backend                                       │
│    rules:                                                 │
│    - from:                                                │
│      - source:                                            │
│          principals: ["frontend.default.svc"]             │
│      to:                                                  │
│      - operation:                                         │
│          methods: ["GET", "POST"]                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tool Selection Guide

```
┌─────────────────────────────────────────────────────────────┐
│              TOOL SELECTION BY USE CASE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "I need to scan images for vulnerabilities"               │
│  → Trivy (comprehensive), Grype (fast)                    │
│                                                             │
│  "I need to check cluster against CIS benchmark"           │
│  → kube-bench                                             │
│                                                             │
│  "I need to audit workload configurations"                 │
│  → kubeaudit, Polaris                                     │
│                                                             │
│  "I need to block insecure configurations"                 │
│  → Kyverno (simpler), OPA/Gatekeeper (flexible)           │
│                                                             │
│  "I need runtime threat detection"                         │
│  → Falco (mature), Tetragon (Cilium users)               │
│                                                             │
│  "I need to sign and verify images"                        │
│  → Cosign (Sigstore)                                      │
│                                                             │
│  "I need secrets management beyond K8s Secrets"            │
│  → Vault (enterprise), Sealed Secrets (GitOps)            │
│                                                             │
│  "I need service-to-service security"                      │
│  → Istio (full mesh), Linkerd (simpler)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Trivy can scan more than images**—it handles filesystems, Git repos, Kubernetes clusters, and IaC like Terraform.

- **kube-bench** is based on the CIS Kubernetes Benchmark, which is updated with each Kubernetes release.

- **Falco was created at Sysdig** and donated to the CNCF. It's now a graduated CNCF project.

- **Cosign keyless signing** uses your GitHub/Google/Microsoft identity instead of managing keys—making signing much more accessible.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Too many tools | Complexity, overlap | Choose focused stack |
| Scanning without action | False security | Define SLAs, automate |
| Policy without testing | Breaks deployments | Test in audit mode first |
| Runtime without response | Alerts ignored | Create incident runbooks |
| No baseline | Can't measure improvement | Run assessments first |

---

## Quiz

1. **What's the difference between Trivy and kube-bench?**
   <details>
   <summary>Answer</summary>
   Trivy scans container images and code for vulnerabilities. kube-bench checks cluster configuration against the CIS Kubernetes Benchmark. Trivy focuses on what you're deploying; kube-bench focuses on how your cluster is configured.
   </details>

2. **When would you use Kyverno vs OPA/Gatekeeper?**
   <details>
   <summary>Answer</summary>
   Kyverno uses YAML for policies (easier for teams familiar with Kubernetes), while Gatekeeper uses Rego (more powerful, steeper learning curve). Choose Kyverno for simpler use cases and teams wanting to stay in YAML; choose Gatekeeper for complex policies or if already using OPA elsewhere.
   </details>

3. **What does Cosign do?**
   <details>
   <summary>Answer</summary>
   Cosign signs and verifies container images. It stores signatures in OCI registries alongside images and supports keyless signing using OIDC identities. It's part of the Sigstore project for software supply chain security.
   </details>

4. **How does Sealed Secrets enable GitOps for secrets?**
   <details>
   <summary>Answer</summary>
   Sealed Secrets encrypts Kubernetes Secrets with a cluster-specific public key. The encrypted SealedSecret can be safely committed to Git. When applied to the cluster, the Sealed Secrets controller decrypts it back to a regular Secret.
   </details>

5. **What's the difference between Falco and Tetragon?**
   <details>
   <summary>Answer</summary>
   Both use eBPF for runtime security monitoring. Falco is more mature with a larger rule library and focuses on detection. Tetragon (from Cilium) focuses more on enforcement and has tighter integration with Cilium network policies. Choose based on existing stack and enforcement needs.
   </details>

---

## Hands-On Exercise: Security Tool Stack Design

**Scenario**: Design a security tool stack for a production Kubernetes environment with these requirements:

- Scan images for vulnerabilities in CI/CD
- Enforce policies to block insecure configurations
- Detect runtime threats
- Manage secrets securely
- Audit cluster configuration against CIS benchmark

**Design your tool stack:**

<details>
<summary>Recommended Tool Stack</summary>

**1. Image Scanning (CI/CD)**
- **Tool**: Trivy
- **Why**: Comprehensive scanning (OS + language packages), fast, good CI integration
- **Implementation**:
  ```bash
  # In CI pipeline
  trivy image --exit-code 1 --severity CRITICAL,HIGH $IMAGE
  ```

**2. Policy Enforcement**
- **Tool**: Kyverno
- **Why**: YAML-native, easier adoption, validate + mutate + generate
- **Implementation**:
  - Enforce Pod Security Standards
  - Require resource limits
  - Block privileged containers
  - Enforce allowed registries

**3. Runtime Security**
- **Tool**: Falco
- **Why**: Mature, rich rule library, CNCF graduated
- **Implementation**:
  - Deploy as DaemonSet
  - Enable default rules
  - Alert to Slack/PagerDuty
  - Create response runbooks

**4. Secrets Management**
- **Tool**: Sealed Secrets + External Secrets Operator
- **Why**: GitOps-friendly, can integrate with cloud secret stores
- **Implementation**:
  - Sealed Secrets for GitOps workflow
  - External Secrets Operator for cloud provider secrets
  - Rotate secrets regularly

**5. Configuration Audit**
- **Tool**: kube-bench
- **Why**: Industry standard CIS benchmark
- **Implementation**:
  - Run as Job weekly/monthly
  - Alert on failures
  - Track improvement over time

**Optional Additions:**
- **Cosign** for image signing (if supply chain security is priority)
- **Istio** for mTLS if service-to-service encryption needed
- **Polaris** dashboard for visibility

**Architecture:**
```
CI/CD: Trivy scan → Cosign sign → Push
                          ↓
Cluster: Kyverno (admission) → Falco (runtime)
                ↓                    ↓
         Block bad configs    Detect threats
                ↓                    ↓
Secrets: Sealed Secrets ← Git → External Secrets
                ↓
Audit: kube-bench → Reports
```

</details>

---

## Summary

Kubernetes security tools serve different purposes:

| Category | Tools | Purpose |
|----------|-------|---------|
| **Scanning** | Trivy, Grype | Find vulnerabilities |
| **Signing** | Cosign | Verify image authenticity |
| **Assessment** | kube-bench, kubeaudit | Check configurations |
| **Policy** | Kyverno, Gatekeeper | Enforce standards |
| **Runtime** | Falco, Tetragon | Detect threats |
| **Secrets** | Vault, Sealed Secrets | Manage sensitive data |

Key principles:
- Choose tools that integrate well together
- Start with essentials: scanning, policy, runtime
- Automate everything in CI/CD
- Have response procedures for alerts
- Measure and improve over time

---

## Next Module

[Module 6.1: Compliance Frameworks](../part6-compliance/module-6.1-compliance-frameworks/) - Understanding security compliance standards for Kubernetes.
