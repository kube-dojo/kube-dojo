# KCA - Kyverno Certified Associate

> **Multiple-choice exam** | 90 minutes | Passing score: 75% | $250 USD | **Launched 2024**

## Overview

The KCA (Kyverno Certified Associate) validates your ability to use Kyverno for Kubernetes policy management. Unlike CKA/CKS which are performance-based, the KCA is a **multiple-choice exam** -- but don't let that fool you. The questions are scenario-heavy and expect you to read, write, and debug real Kyverno YAML policies.

**KubeDojo covers ~95% of KCA topics** through our existing Platform Engineering and CKS tracks, plus two dedicated KCA modules covering advanced policies, CLI operations, and policy management.

> **Why KCA matters**: Kyverno is the most popular YAML-native policy engine in the Kubernetes ecosystem. As organizations shift from "deploy fast" to "deploy safely," policy-as-code skills are in high demand. KCA proves you can enforce governance without writing a line of Rego.

---

## KCA-Specific Modules

These modules fill the gaps between KubeDojo's existing Kyverno toolkit module and the KCA exam requirements:

| # | Module | Topic | Domains Covered |
|---|--------|-------|-----------------|
| 1 | [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md) | verifyImages, CEL expressions, cleanup policies, advanced validate/mutate/generate | Domain 5 (32%) |
| 2 | [Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) | kyverno apply/test/jp, policy exceptions, metrics, HA deployment | Domains 2, 3, 6 (40%) |

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| Fundamentals of Kyverno | 18% | Excellent (Kyverno toolkit module) |
| Installation, Configuration & Upgrades | 18% | Good (Kyverno module + CKS modules) |
| Kyverno CLI | 12% | Excellent ([Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) — apply/test/jp) |
| Applying Policies | 10% | Excellent (Kyverno + OPA modules) |
| Writing Policies | 32% | Excellent ([Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md) — CEL, verifyImages, cleanup) |
| Policy Management | 10% | Excellent ([Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) — exceptions, metrics, HA) |

---

## Domain 1: Fundamentals of Kyverno (18%)

### Competencies
- Understanding Kyverno's role as a Kubernetes admission controller
- Policy types: ClusterPolicy vs Policy (namespace-scoped)
- YAML structure of a Kyverno policy
- How Kyverno integrates with the Kubernetes API server via webhooks

### KubeDojo Learning Path

**Core module:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | Architecture, policy model, validate/mutate/generate | Direct |
| [OPA & Gatekeeper 4.2](../../platform/toolkits/security-tools/module-4.2-opa-gatekeeper.md) | Policy engine concepts, admission control patterns | Context |

**Kubernetes foundations (admission controllers):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [CKS Admission Controllers](../../k8s/cks/part5-supply-chain-security/module-5.4-admission-controllers.md) | ValidatingWebhookConfiguration, MutatingWebhookConfiguration | Direct |
| [CKS Pod Security Admission](../../k8s/cks/part4-microservice-vulnerabilities/module-4.2-pod-security-admission.md) | Built-in admission control, PSA vs policy engines | Context |
| [CKS API Server Security](../../k8s/cks/part2-cluster-hardening/module-2.3-api-server-security.md) | API server admission chain | Context |

### Key Concepts to Master
- **Admission webhook flow**: API request -> mutating webhooks -> validating webhooks -> persist to etcd
- **ClusterPolicy** applies cluster-wide; **Policy** is namespace-scoped (same syntax, different scope)
- Kyverno runs as a Deployment with multiple replicas, not a DaemonSet
- Policies are Kubernetes CRDs -- managed with kubectl, GitOps, Helm like any other resource

---

## Domain 2: Installation, Configuration & Upgrades (18%)

### Competencies
- Installing Kyverno via Helm charts
- Understanding Kyverno CRDs and their lifecycle
- Configuring RBAC for Kyverno service accounts
- High Availability (HA) deployment patterns
- Upgrading Kyverno across versions

### KubeDojo Learning Path

**Kyverno-specific:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | Installation, Helm values, basic configuration | Direct |

**Supporting Kubernetes concepts:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [CKS Kubernetes Upgrades](../../k8s/cks/part2-cluster-hardening/module-2.4-kubernetes-upgrades.md) | Upgrade strategies, version skew | Context |
| [Helm & Kustomize](../../platform/toolkits/gitops-deployments/module-2.4-helm-kustomize.md) | Helm install, upgrade, rollback patterns | Direct |

### Key Concepts to Master
- **Helm install**: `helm install kyverno kyverno/kyverno -n kyverno --create-namespace`
- **HA mode**: 3 replicas, pod anti-affinity, separate webhook and background controller
- **CRDs**: ClusterPolicy, Policy, ClusterPolicyReport, PolicyReport, AdmissionReport, UpdateRequest
- **RBAC**: Kyverno needs permissions to watch/list resources it governs
- **Webhook configuration**: `failurePolicy: Fail` vs `Ignore` -- critical for production stability
- **Resource filters**: Exclude kyverno namespace and system resources from policy evaluation

---

## Domain 3: Kyverno CLI (12%)

### Competencies
- Using `kyverno apply` to test policies against resources offline
- Using `kyverno test` for policy unit testing
- Using `kyverno jp` for JMESPath expression debugging
- Integrating Kyverno CLI into CI/CD pipelines

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | CLI basics, CI/CD integration | Partial |
| [Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) | kyverno apply/test/jp, policy exceptions, metrics, HA deployment | Direct |
| [DevSecOps 4.3](../../platform/disciplines/devsecops/module-4.3-security-cicd.md) | Security in CI/CD pipelines (policy-as-code pattern) | Context |
| [CKS Static Analysis](../../k8s/cks/part5-supply-chain-security/module-5.3-static-analysis.md) | Pre-deploy scanning concepts | Context |

### Key Concepts to Master

```bash
# Apply a policy against a resource (offline, no cluster needed)
kyverno apply policy.yaml --resource deployment.yaml

# Run policy test suites
kyverno test ./tests/

# Debug JMESPath expressions (used in preconditions and variables)
kyverno jp query "request.object.metadata.labels.app" -i resource.json

# CI/CD pipeline usage -- fail the build if policies are violated
kyverno apply policies/ --resource manifests/ --detailed-results
```

- **`kyverno apply`**: Tests policies against resources without a cluster. Essential for shift-left.
- **`kyverno test`**: Runs test cases defined in YAML. Each test specifies a policy, resource, and expected result (pass/fail/skip).
- **`kyverno jp`**: Interactive JMESPath query tool. Invaluable for debugging complex match conditions.
- **Test file structure**: `kyverno-test.yaml` with `policies:`, `resources:`, and `results:` fields.

---

## Domain 4: Applying Policies (10%)

### Competencies
- Resource selection with `match` and `exclude` blocks
- Targeting specific resource kinds, namespaces, labels, and annotations
- Using preconditions for conditional policy execution
- Policy ordering and conflict resolution

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | match/exclude, resource selection | Direct |
| [OPA & Gatekeeper 4.2](../../platform/toolkits/security-tools/module-4.2-opa-gatekeeper.md) | Constraint selectors (comparison) | Context |

### Key Concepts to Master

```yaml
# Match/Exclude patterns
spec:
  rules:
  - name: require-labels
    match:
      any:
      - resources:
          kinds:
          - Pod
          namespaces:
          - production
          - staging
          selector:
            matchLabels:
              app.kubernetes.io/managed-by: helm
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
      - clusterRoles:
          - cluster-admin
```

- **`match.any`** = OR logic (match any condition); **`match.all`** = AND logic (match all conditions)
- **`exclude`** takes precedence over `match` -- always processed after match
- **Preconditions**: Use JMESPath expressions for conditional logic (`{{ request.object.metadata.annotations.\"skip-policy\" }}`)
- **Resource filters**: Global filters in Kyverno ConfigMap exclude resources from all policy evaluation

---

## Domain 5: Writing Policies (32%)

> This is the largest domain. It requires deep hands-on practice.

### Competencies
- Writing **validate** rules (deny non-compliant resources)
- Writing **mutate** rules (auto-fix resources at admission)
- Writing **generate** rules (auto-create companion resources)
- Writing **verifyImages** rules (enforce image signatures and attestations)
- Using **CEL expressions** in policies (Kubernetes 1.30+ alternative to JMESPath)
- Writing **cleanup policies** (TTL-based resource deletion)

### KubeDojo Learning Path

**Well-covered (validate, mutate, generate):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | Validate, mutate, generate policies with examples | Direct |
| [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md) | verifyImages, CEL expressions, cleanup policies, advanced patterns | Direct |
| [Security Mindset 4.1](../../platform/foundations/security-principles/module-4.1-security-mindset.md) | Why policy enforcement matters | Context |
| [Defense in Depth 4.2](../../platform/foundations/security-principles/module-4.2-defense-in-depth.md) | Layered security model | Context |

**Additional depth (verifyImages, CEL, cleanup):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Supply Chain Security 4.4](../../platform/toolkits/security-tools/module-4.4-supply-chain.md) | Cosign, image signing, attestations (verifyImages context) | Direct |
| [DevSecOps Supply Chain 4.4](../../platform/disciplines/devsecops/module-4.4-supply-chain-security.md) | Supply chain theory, SLSA, SBOM | Context |

### Key Concepts to Master

**Validate (deny non-compliant resources):**
```yaml
spec:
  validationFailureAction: Enforce  # Enforce = block, Audit = warn only
  rules:
  - name: require-resource-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "CPU and memory limits are required."
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"
                cpu: "?*"
```

**Mutate (auto-fix at admission):**
```yaml
spec:
  rules:
  - name: add-default-securitycontext
    match:
      any:
      - resources:
          kinds:
          - Pod
    mutate:
      patchStrategicMerge:
        spec:
          containers:
          - (name): "*"
            securityContext:
              runAsNonRoot: true
              readOnlyRootFilesystem: true
```

**Generate (auto-create companion resources):**
```yaml
spec:
  rules:
  - name: generate-networkpolicy
    match:
      any:
      - resources:
          kinds:
          - Namespace
    generate:
      kind: NetworkPolicy
      apiVersion: networking.k8s.io/v1
      name: default-deny-ingress
      namespace: "{{request.object.metadata.name}}"
      data:
        spec:
          podSelector: {}
          policyTypes:
          - Ingress
```

**verifyImages (enforce image signatures) -- covered in [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md):**
```yaml
spec:
  rules:
  - name: verify-image-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "ghcr.io/myorg/*"
      attestors:
      - entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              ...
              -----END PUBLIC KEY-----
```

**CEL expressions (alternative to JMESPath) -- covered in [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md):**
```yaml
spec:
  rules:
  - name: check-replicas-cel
    match:
      any:
      - resources:
          kinds:
          - Deployment
    validate:
      cel:
        expressions:
        - expression: "object.spec.replicas >= 2"
          message: "Deployments must have at least 2 replicas"
```

**Cleanup policies (TTL-based deletion) -- covered in [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md):**
```yaml
apiVersion: kyverno.io/v2beta1
kind: ClusterCleanupPolicy
metadata:
  name: cleanup-stale-pods
spec:
  match:
    any:
    - resources:
        kinds:
        - Pod
        selector:
          matchLabels:
            environment: test
  conditions:
    any:
    - operator: Equals
      key: "{{ target.status.phase }}"
      value: Succeeded
  schedule: "*/30 * * * *"
```

### Study Focus for This Domain
1. Practice writing all 4 policy types (validate, mutate, generate, verifyImages) from scratch
2. Understand `validationFailureAction: Enforce` vs `Audit` -- this is heavily tested
3. Learn JMESPath basics for variable substitution (`{{ request.object.* }}`)
4. Study CEL expressions -- Kyverno added CEL support as an alternative to pattern-based validation
5. Understand cleanup policies -- cron-based TTL deletion of resources matching conditions

---

## Domain 6: Policy Management (10%)

### Competencies
- Reading and interpreting PolicyReports and ClusterPolicyReports
- Configuring policy exceptions for legitimate bypasses
- Monitoring Kyverno with metrics (Prometheus)
- Managing policy lifecycle (audit -> enforce migration)

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-tools/module-4.7-kyverno.md) | Policy reports, audit mode | Direct |
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Prometheus metrics, ServiceMonitor | Context |
| [SRE SLOs 1.2](../../platform/disciplines/sre/module-1.2-slos.md) | Measuring policy compliance as an SLO | Context |
| [DevSecOps Fundamentals 4.1](../../platform/disciplines/devsecops/module-4.1-devsecops-fundamentals.md) | Policy-as-code lifecycle | Context |

### Key Concepts to Master

**PolicyReports:**
```bash
# View cluster-wide policy results
kubectl get clusterpolicyreport -o wide

# View namespace-scoped results
kubectl get policyreport -n production -o wide

# Results have pass/fail/warn/error/skip counts
```

**Policy Exceptions (bypass for legitimate cases):**
```yaml
apiVersion: kyverno.io/v2
kind: PolicyException
metadata:
  name: allow-privileged-cni
  namespace: kube-system
spec:
  exceptions:
  - policyName: disallow-privileged-containers
    ruleNames:
    - require-non-privileged
  match:
    any:
    - resources:
        kinds:
        - Pod
        namespaces:
        - kube-system
        names:
        - "calico-node-*"
```

**Kyverno metrics (Prometheus):**
- `kyverno_admission_requests_total` -- total admission requests processed
- `kyverno_policy_results_total` -- policy evaluation results (pass/fail/error)
- `kyverno_policy_execution_duration_seconds` -- policy execution latency
- All metrics exposed on `:8000/metrics` by default

**Audit -> Enforce migration pattern:**
1. Deploy policy with `validationFailureAction: Audit`
2. Monitor PolicyReports for violations
3. Fix existing violations or create PolicyExceptions
4. Switch to `validationFailureAction: Enforce`
5. Monitor admission metrics for blocked requests

---

## Study Strategy

```
KCA PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1: Foundations & Architecture (18%)
├── KubeDojo Kyverno module 4.7 (start here)
├── CKS Admission Controllers module
├── OPA & Gatekeeper module (compare approaches)
└── Install Kyverno on a kind cluster

Week 2: Installation & Policy Basics (18% + 10%)
├── Helm install with custom values
├── Configure HA mode (3 replicas)
├── Practice match/exclude patterns
├── Write 10+ validate policies from scratch
└── Deploy Kyverno via ArgoCD (GitOps pattern)

Week 3: Writing Policies Deep Dive (32% -- spend the most time here!)
├── Mutate policies (patchStrategicMerge, patchesJson6902)
├── Generate policies (NetworkPolicy, ResourceQuota, LimitRange)
├── verifyImages with Cosign (use KubeDojo supply chain module)
├── CEL expressions (practice converting JMESPath -> CEL)
├── Cleanup policies (cron-based TTL deletion)
└── Kyverno policy library: study 20+ community policies

Week 4: CLI, Management & Review (12% + 10%)
├── kyverno apply / test / jp CLI commands
├── Write kyverno-test.yaml test suites
├── PolicyReports and ClusterPolicyReports
├── Policy exceptions for legitimate bypasses
├── Prometheus metrics and Grafana dashboards
└── Practice exam questions, review weak areas
```

---

## Exam Tips

- **Writing Policies is 32% of the exam** -- you MUST be able to write validate, mutate, generate, and verifyImages policies from memory
- **Know the difference between `Enforce` and `Audit`** -- this distinction appears in many questions
- **JMESPath is your friend** -- practice `{{ request.object.* }}` variable syntax until it's second nature
- **CEL is new and testable** -- the exam tests both JMESPath and CEL approaches
- **Policy exceptions vs exclude** -- know when to use each (exceptions are for operational bypasses; exclude is for structural filtering)
- **CLI commands are easy points** -- memorize `kyverno apply`, `kyverno test`, and `kyverno jp` syntax
- **Read the policy library** -- many exam questions are variations of standard community policies: [kyverno.io/policies](https://kyverno.io/policies/)

---

## Gap Analysis

KubeDojo's existing modules plus the two dedicated KCA modules now cover ~95% of the KCA curriculum:

| Topic | Status | Notes |
|-------|--------|-------|
| verifyImages policies | Covered | [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md) — Cosign, attestations, image verification |
| CEL expressions in Kyverno | Covered | [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md) — CEL validate expressions |
| Cleanup policies | Covered | [Advanced Kyverno Policies](module-1-advanced-kyverno-policies.md) — ClusterCleanupPolicy, TTL-based deletion |
| Kyverno CLI deep dive | Covered | [Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) — apply, test, jp commands |
| Policy exceptions | Covered | [Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) — PolicyException CRD |
| Kyverno Prometheus metrics | Covered | [Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) — admission, policy result, and execution metrics |
| HA deployment details | Covered | [Kyverno Operations & CLI](module-2-kyverno-operations-cli.md) — replicas, anti-affinity, webhook config |

### Recommended External Resources
- **Kyverno documentation**: [kyverno.io/docs](https://kyverno.io/docs/) -- authoritative reference for all domains
- **Kyverno policy library**: [kyverno.io/policies](https://kyverno.io/policies/) -- 200+ ready-made policies to study
- **Kyverno playground**: [playground.kyverno.io](https://playground.kyverno.io/) -- test policies in-browser without a cluster
- **CNCF KCA curriculum**: [github.com/cncf/curriculum](https://github.com/cncf/curriculum) -- official exam objectives

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Entry Level:
├── KCNA (Cloud Native Associate) — K8s fundamentals
├── KCSA (Security Associate) — Security fundamentals
└── KCA (Kyverno Certified Associate) ← YOU ARE HERE

Professional Level:
├── CKA (K8s Administrator) — Cluster operations
├── CKAD (K8s Developer) — Application deployment
├── CKS (K8s Security Specialist) — Security hardening
└── CNPE (Platform Engineer) — Platform at scale

KCA pairs naturally with:
├── CKS — KCA covers policy engine depth, CKS covers broader security
├── KCSA — KCA is the hands-on follow-up to KCSA's theory
└── CNPE — Policy-as-code is a core platform engineering skill
```

KCA is unique among CNCF certifications because it focuses on a **single project** (Kyverno) rather than a broad domain. This makes it more focused but also deeper -- expect detailed questions about Kyverno-specific features that wouldn't appear on CKS.
