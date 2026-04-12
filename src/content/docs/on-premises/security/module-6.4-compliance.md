---
title: "Module 6.4: Compliance for Regulated Industries"
slug: on-premises/security/module-6.4-compliance
sidebar:
  order: 5
---

> **Complexity**: `[ADVANCED]` | Time: 60 minutes
>
> **Prerequisites**: [Physical Security & Air-Gapped Environments](../module-6.1-air-gapped/), [Hardware Security (HSM/TPM)](../module-6.2-hardware-security/), [Enterprise Identity](../module-6.3-enterprise-identity/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** a Kubernetes audit logging pipeline that captures API server access with tamper-evident storage for compliance evidence
2. **Implement** policy-as-code frameworks (OPA/Gatekeeper, Kyverno) that enforce regulatory controls and generate compliance reports
3. **Plan** an evidence collection strategy that maps technical controls to specific regulatory requirements (HIPAA, PCI-DSS, SOC 2, GDPR)
4. **Configure** continuous compliance monitoring with automated drift detection and audit-ready dashboards

---

## Why This Module Matters

In 2023, a healthcare SaaS company running Kubernetes on-premises failed their HIPAA audit. Not because of a breach -- because they could not prove controls existed. The auditor asked: "Show me your audit log for who accessed the production namespace containing PHI in the last 90 days." The platform team had Kubernetes audit logging enabled, but it was set to the default `None` level for most resources. They had pod logs in Loki, but those showed application activity, not API server access. They had no record of which engineer ran `kubectl exec` into a database pod two months ago.

The remediation took 4 months: designing a comprehensive audit policy, deploying a tamper-evident log pipeline, building evidence collection dashboards, and retroactively documenting every control. The total cost -- including the delayed product launch and consultant fees -- exceeded $800,000. The irony: the technical controls were mostly in place (RBAC, network policies, encryption). What was missing was evidence -- the ability to prove to a third party that the controls existed, were operating, and were monitored.

> **The Restaurant Inspection Analogy**
>
> A restaurant can have a spotless kitchen but fail a health inspection if the temperature logs are not posted, the handwashing signs are missing, and the food safety certificates are not on file. Compliance is not about being secure -- it is about proving you are secure. Your Kubernetes cluster might be locked down perfectly, but without audit logs, documented policies, and evidence collection, you will fail the audit.

---

## What You'll Learn

- How HIPAA, SOC 2, PCI DSS, and data sovereignty requirements map to Kubernetes controls
- Designing a Kubernetes audit policy that satisfies compliance requirements
- Audit log architecture for tamper-evident, long-term storage
- PCI DSS scope isolation using namespaces and network policies
- Evidence collection workflows for auditors
- Common compliance pitfalls and how to avoid them

---

## Mapping Regulatory Frameworks to Kubernetes

```
┌──────────────────────────────────────────────────────────────────┐
│           COMPLIANCE FRAMEWORKS vs KUBERNETES CONTROLS           │
│                                                                  │
│  Requirement          HIPAA    SOC2    PCI DSS    K8s Control    │
│  ──────────────────   ─────   ─────   ───────    ───────────    │
│  Access control        X        X        X       RBAC + OIDC    │
│  Audit logging         X        X        X       Audit policy   │
│  Encryption at rest    X        X        X       etcd encryption│
│  Encryption in transit X        X        X       mTLS (Istio)   │
│  Network segmentation  X        X        X       NetworkPolicy  │
│  Vulnerability mgmt    X        X        X       Trivy/Grype    │
│  Change management     X        X        X       GitOps + CI/CD │
│  Incident response     X        X        X       Alerting + DR  │
│  Physical security     X                 X       Datacenter     │
│  Data sovereignty      GDPR              GDPR    On-prem + geo  │
│  Key management                          X       HSM/Vault      │
│  Penetration testing            X        X       Annual pentest │
│  Business continuity   X        X                Multi-site DR  │
└──────────────────────────────────────────────────────────────────┘
```

---

## HIPAA Physical Controls Mapping

HIPAA's Security Rule (45 CFR 164.310) requires physical safeguards for systems handling Protected Health Information (PHI).

### Physical Safeguard Requirements

| HIPAA Requirement | Section | On-Prem K8s Implementation |
|-------------------|---------|---------------------------|
| Facility access controls | 164.310(a)(1) | Badge access, visitor log, mantrap for server room |
| Workstation use policy | 164.310(b) | kubectl access via VPN only, session timeout |
| Workstation security | 164.310(c) | Encrypted laptops, MFA for kubectl (Keycloak) |
| Device and media controls | 164.310(d)(1) | Encrypted disks (LUKS+TPM), sanitize before disposal |
| Hardware inventory | 164.310(d)(2)(iii) | CMDB tracking all nodes, serial numbers, locations |

### Kubernetes-Specific HIPAA Controls

Label PHI namespaces with `compliance: hipaa` and `data-classification: phi`. Apply strict NetworkPolicies that:

- **Default deny** all ingress and egress for the PHI namespace
- Allow ingress only from other HIPAA-labeled namespaces and specific API gateway pods
- Allow egress only to other HIPAA namespaces and DNS (port 53)
- Block all traffic to/from non-compliant namespaces

Add annotations for ownership and data classification to support automated evidence collection.

---

## SOC 2 on Premises

SOC 2 (Service Organization Control 2) is an audit framework based on five Trust Services Criteria. Here is how each maps to on-premises Kubernetes:

### Trust Services Criteria Mapping

| Criteria | Key Controls | K8s Implementation |
|----------|-------------|-------------------|
| **Security** (CC6) | Access control, network protection | RBAC, NetworkPolicy, mTLS, WAF |
| **Availability** (A1) | Uptime, disaster recovery | Multi-replica, PDB, multi-site DR |
| **Processing Integrity** (PI1) | Accurate processing | GitOps (immutable deployments), admission webhooks |
| **Confidentiality** (C1) | Data protection | Encryption at rest (HSM), encryption in transit (mTLS) |
| **Privacy** (P1-P8) | Personal data handling | Namespace isolation, audit logging, data retention |

### SOC 2 Evidence Collection

> **Stop and think**: An auditor will not accept "we have RBAC configured" as evidence. They need proof that specific controls were in place at specific times over the audit period. How does automated monthly evidence collection differ from simply exporting your current configuration?

Automate monthly evidence collection with a script that exports the current state of access controls, network policies, vulnerability reports, and deployment history. Each month's export creates a timestamped snapshot that proves controls were consistently operating.

```bash
#!/bin/bash
# soc2-evidence.sh -- Run monthly, store in evidence repository
EVIDENCE_DIR="/evidence/soc2/$(date +%Y-%m)"
mkdir -p "${EVIDENCE_DIR}"

# CC6.1: Access control
kubectl get clusterrolebindings -o json > "${EVIDENCE_DIR}/clusterrolebindings.json"
kubectl get rolebindings --all-namespaces -o json > "${EVIDENCE_DIR}/rolebindings.json"

# CC6.1: Users with cluster-admin
kubectl get clusterrolebindings -o json | \
  jq -r '.items[] | select(.roleRef.name=="cluster-admin") |
    .subjects[]? | "\(.kind): \(.name)"' > "${EVIDENCE_DIR}/cluster-admins.txt"

# CC6.6: Network segmentation
kubectl get networkpolicies --all-namespaces -o json > "${EVIDENCE_DIR}/netpol.json"

# CC7.1: Vulnerability scan results
kubectl get vulnerabilityreports --all-namespaces -o json \
  > "${EVIDENCE_DIR}/vuln-reports.json" 2>/dev/null

# CC8.1: Change management
kubectl rollout history deployment --all-namespaces > "${EVIDENCE_DIR}/deploy-history.txt"

# A1.2: Availability
kubectl get pdb --all-namespaces -o json > "${EVIDENCE_DIR}/pdbs.json"

echo "Evidence: ${EVIDENCE_DIR} ($(du -sh ${EVIDENCE_DIR} | cut -f1))"
```

---

## PCI DSS Scope Isolation

PCI DSS requires strict isolation of the Cardholder Data Environment (CDE). On Kubernetes, this means the namespaces handling payment card data must be separated from everything else.

```
┌──────────────────────────────────────────────────────────────────┐
│               PCI DSS SCOPE ON KUBERNETES                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │               KUBERNETES CLUSTER                     │        │
│  │                                                      │        │
│  │  ┌──────────────────────┐  ┌──────────────────────┐ │        │
│  │  │  IN-SCOPE (CDE)      │  │  OUT-OF-SCOPE        │ │        │
│  │  │                      │  │                       │ │        │
│  │  │  payment-processing  │  │  marketing-site      │ │        │
│  │  │  card-vault          │  │  analytics            │ │        │
│  │  │  tokenization        │  │  internal-tools       │ │        │
│  │  │                      │  │  staging              │ │        │
│  │  │  Strict controls:    │  │                       │ │        │
│  │  │  - Dedicated nodes   │  │  Standard controls    │ │        │
│  │  │  - Network isolation │  │                       │ │        │
│  │  │  - Full audit logging│  │                       │ │        │
│  │  │  - WAF               │  │                       │ │        │
│  │  │  - File integrity    │  │                       │ │        │
│  │  └──────────┬───────────┘  └──────────────────────┘ │        │
│  │             │ Network Policy: DENY ALL except        │        │
│  │             │ explicitly allowed connections          │        │
│  └─────────────┴────────────────────────────────────────┘        │
│                                                                  │
│  Key principle: MINIMIZE the CDE. Fewer namespaces in scope     │
│  = less to audit = lower compliance cost.                       │
└──────────────────────────────────────────────────────────────────┘
```

> **Stop and think**: PCI DSS scope isolation means fewer namespaces to audit, which reduces compliance cost. What is the incentive for engineering teams to keep their workloads OUT of PCI scope? How would you enforce this organizationally?

### Dedicated Nodes for CDE (PCI DSS Req 2.2.1)

Taints prevent non-payment pods from landing on CDE nodes, while node affinity ensures payment pods only run on CDE hardware. Together with admission control, this creates defense-in-depth isolation.

```bash
# Taint CDE nodes so only payment workloads schedule there
kubectl taint nodes cde-node-{1,2,3} pci-dss=cde:NoSchedule
kubectl label nodes cde-node-{1,2,3} node-role.kubernetes.io/pci-cde=""
```

Payment workload Deployments must include:
- **Toleration** for the `pci-dss=cde:NoSchedule` taint
- **Node affinity** requiring `node-role.kubernetes.io/pci-cde`
- **Security context**: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, drop all capabilities
- **Label**: `pci-scope: in-scope` on both Deployment and Pod for audit queries

---

## Kubernetes Audit Policy Design

The Kubernetes audit policy controls what the API server logs. A well-designed policy captures compliance-relevant events without generating excessive noise.

> **Pause and predict**: The audit policy below uses `Metadata` level for Secrets instead of `RequestResponse`. Why would logging Secret access at `RequestResponse` level actually make your cluster LESS secure, even though it captures more information?

### Understanding Audit Levels

The Kubernetes API server supports four audit levels:
- **`None`**: No event is logged. Use for high-volume, low-value endpoints (e.g., health checks).
- **`Metadata`**: Logs request metadata (who, what, when) but not the body. Use for most operations, including Secrets.
- **`Request`**: Logs metadata plus the request body. Use when you need to know what was submitted (e.g., RBAC role creation) without needing the response.
- **`RequestResponse`**: Logs metadata, request body, and response body. Use for operations requiring full forensic capability like `pods/exec`.

### Compliance-Grade Audit Policy

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Log nothing for health checks and metrics (high volume, low value)
  - level: None
    nonResourceURLs:
    - /healthz*
    - /readyz*
    - /livez*
    - /metrics
    - /openapi/*

  # Log nothing for system service accounts (reduces noise)
  - level: None
    users:
    - "system:kube-scheduler"
    - "system:kube-controller-manager"
    - "system:kube-proxy"
    - "system:apiserver"

  # CRITICAL: Log all Secret access with full metadata
  # (Required for HIPAA, SOC 2, PCI DSS)
  # WARNING: Do NOT use RequestResponse for secrets — it logs actual secret
  # data (values) in the audit log, creating a severe security vulnerability.
  # Metadata level captures who accessed which secret and when, without
  # exposing secret contents.
  - level: Metadata
    resources:
    - group: ""
      resources: ["secrets"]
    omitStages:
    - RequestReceived

  # CRITICAL: Log all exec, attach, portforward (interactive access)
  # (Detects unauthorized data access)
  - level: RequestResponse
    resources:
    - group: ""
      resources: ["pods/exec", "pods/attach", "pods/portforward"]
    omitStages:
    - RequestReceived

  # CRITICAL: Log RBAC changes (who changed permissions?)
  - level: RequestResponse
    resources:
    - group: "rbac.authorization.k8s.io"
      resources:
      - "clusterroles"
      - "clusterrolebindings"
      - "roles"
      - "rolebindings"
    omitStages:
    - RequestReceived

  # Log namespace operations in compliance-labeled namespaces
  - level: Metadata
    resources:
    - group: ""
      resources: ["namespaces"]

  # Log all write operations (create, update, delete) at metadata level
  - level: Metadata
    verbs: ["create", "update", "patch", "delete", "deletecollection"]
    omitStages:
    - RequestReceived

  # Log read operations at metadata level for compliance namespaces
  - level: Metadata
    namespaces: ["phi-production", "payment-processing", "card-vault"]
    omitStages:
    - RequestReceived

  # Catch-all: log everything else at metadata level
  - level: Metadata
    omitStages:
    - RequestReceived
```

### Configure the API Server

After designing the audit policy, configure the API server to use it. These flags control where audit logs are written, how long they are retained on disk, and the output format.

```bash
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--audit-log-path=/var/log/kubernetes/audit/audit.log
--audit-log-maxage=365        # Keep 1 year on disk (ship to WORM for longer)
--audit-log-maxbackup=30
--audit-log-maxsize=200       # 200 MB per file
--audit-log-format=json
```

Mount the audit policy file and log directory as volumes in the API server pod.

---

## Tamper-Evident Audit Log Pipeline

Audit logs stored on the node's filesystem can be modified by anyone with root access. For compliance, you need a pipeline that makes log tampering detectable.

```
┌──────────────────────────────────────────────────────────────────┐
│             TAMPER-EVIDENT AUDIT PIPELINE                        │
│                                                                  │
│  API Server                                                      │
│     │                                                            │
│     ▼                                                            │
│  audit.log (on node, short retention)                            │
│     │                                                            │
│     ▼                                                            │
│  Fluent Bit / Vector (ship logs in near-real-time)               │
│     │                                                            │
│     ├──────────────────────────┐                                 │
│     ▼                          ▼                                 │
│  Elasticsearch/OpenSearch    S3-compatible (MinIO)               │
│  (searchable, 90-day)       (immutable, WORM, 7-year)           │
│     │                          │                                 │
│     ▼                          ▼                                 │
│  Kibana/Grafana             Object Lock prevents                │
│  (dashboards, alerts)       deletion or modification            │
│                                                                  │
│  Tamper evidence:                                                │
│  1. Logs signed with HMAC at source (Fluent Bit)                │
│  2. WORM storage prevents modification                          │
│  3. Daily SHA256 of log batches stored separately               │
│  4. Alert if log gap > 5 minutes (indicates tampering/failure)  │
└──────────────────────────────────────────────────────────────────┘
```

### Fluent Bit Configuration for Audit Logs

Deploy Fluent Bit as a DaemonSet to ship audit logs from each control plane node. Key configuration:

```ini
[INPUT]
    Name         tail
    Path         /var/log/kubernetes/audit/audit.log
    Parser       json
    Tag          kube.audit

[FILTER]
    Name         modify
    Match        kube.audit
    Add          cluster_name on-prem-prod-01

[OUTPUT]
    Name         opensearch
    Match        kube.audit
    Host         opensearch.monitoring.svc
    Port         9200
    Index        k8s-audit
    TLS          On

[OUTPUT]
    Name         s3
    Match        kube.audit
    Bucket       audit-logs-worm
    Endpoint     http://minio.storage.svc:9000
    S3_key_format  /audit/%Y/%m/%d/%H-%M-%S-$UUID.json.gz
    Compression    gzip
```

The dual-output pattern sends logs to OpenSearch for searching (90-day retention) and to MinIO with WORM/object lock for tamper-proof long-term storage.

---

## Data Sovereignty

Data sovereignty requires that data remains within a specific geographic or legal jurisdiction.

| Requirement | Implementation |
|-------------|---------------|
| Data must stay in-country | On-premises in domestic datacenter(s) |
| Data must not be accessible by foreign entities | Air-gapped or encrypted with locally-held keys (not cloud KMS) |
| Right to deletion (GDPR) | Application-level deletion + backup purge + audit proof |
| Cross-border transfer restrictions | No replication to foreign sites; DR site must be domestic |
| Government access requests | On-prem with local legal framework; no CLOUD Act exposure |

### Kubernetes Configuration for Data Sovereignty

Use a ValidatingWebhookConfiguration or OPA/Gatekeeper policy to reject pods with images from unapproved registries. Only allow images from your internal registries (`registry.internal.corp`). All external images must be mirrored through the approved transfer process (see [Module 6.1](../module-6.1-air-gapped/)).

---

## Implementing Policy-as-Code for Compliance

To enforce regulatory controls continuously, Kubernetes clusters rely on Policy-as-Code engines like **Kyverno** or **OPA Gatekeeper**. These tools prevent non-compliant resources from being deployed and can generate compliance reports.

### Kyverno for Compliance Reporting

Kyverno (a CNCF graduated project) uses Kubernetes-native YAML for policy definitions. It can validate, mutate, and generate resources. Crucially for compliance, Kyverno generates PolicyReports that map policy violations to specific resources.

```yaml
# Enforce that all pods drop ALL capabilities (SOC 2 CC6.1 / PCI DSS Req 11)
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-drop-all-capabilities
  annotations:
    policies.kyverno.io/category: Pod Security Standards (Restricted)
    policies.kyverno.io/description: Proves capabilities are dropped.
spec:
  validationFailureAction: Enforce
  rules:
  - name: drop-all-capabilities
    match:
      any:
      - resources:
          kinds: ["Pod"]
    validate:
      message: "Containers must drop 'ALL' capabilities."
      pattern:
        spec:
          containers:
          - securityContext:
              capabilities:
                drop:
                - ALL
```

By deploying a suite of compliance policies, you can query violations across the cluster to provide evidence of control enforcement:
```bash
kubectl get policyreports -A
```

---

## Evidence Collection for Auditors

Auditors need evidence organized by control, not by technology. Here is a mapping of what they ask for and where to find it in Kubernetes.

### Auditor Questions and Evidence Sources

| Auditor Question | K8s Evidence | How to Collect |
|-----------------|--------------|----------------|
| "Who has admin access?" | ClusterRoleBindings for cluster-admin | `kubectl get crb -o json \| jq` |
| "Show me access logs for the last 90 days" | Audit logs (API server) | OpenSearch/Elasticsearch query |
| "How is data encrypted at rest?" | EncryptionConfiguration, HSM config | Config files + HSM admin console |
| "Show me your change management process" | Git history, PR reviews, Flux reconciliation logs | Git log, Flux events |
| "How are vulnerabilities tracked?" | Trivy/Grype scan reports | `kubectl get vulnerabilityreports` |
| "Show me your incident response plan" | Runbooks, alert configurations | Documented runbooks + PagerDuty/Opsgenie config |
| "How is network access controlled?" | NetworkPolicies, firewall rules | `kubectl get netpol --all-namespaces` |
| "Prove data never leaves this jurisdiction" | Network architecture, no external replication | Network diagrams, data flow maps |

### Automated Evidence Report

Build a script that generates auditor-ready evidence organized by control area: access control (cluster-admin bindings, OIDC flags), encryption (etcd config, HSM status, LUKS), network segmentation (NetworkPolicies), namespace inventory (compliance labels), and pod security (PSA levels). Package as a timestamped compressed archive. Run monthly and store in an immutable evidence repository.

---

## Did You Know?

- **HIPAA has no certification.** Unlike PCI DSS (which has the QSA certification) or SOC 2 (which produces a formal report), HIPAA compliance is self-attested. The Office for Civil Rights (OCR) only audits after a breach or complaint. This means many organizations believe they are HIPAA-compliant but have never been tested.

- **PCI DSS v4.0 (effective March 2025)** added explicit requirements for container security, including image integrity verification (Req 6.3.2) and runtime protection (Req 11.5.1.1). Previous versions did not mention containers at all, leaving assessors to interpret traditional controls.

- **SOC 2 Type I vs Type II**: Type I is a point-in-time snapshot ("controls exist today"). Type II covers a period (usually 12 months) and proves controls were consistently operating. Type II is far more valuable and what customers typically require. For Kubernetes, this means you need 12 months of audit logs, not just a current configuration export.

- **The CLOUD Act (2018)** allows US law enforcement to compel US-based cloud providers to produce data regardless of where it is stored geographically. This is a primary driver for data sovereignty decisions. On-premises infrastructure with a non-US provider eliminates CLOUD Act exposure entirely.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Audit policy set to `None` for secrets | No evidence of who accessed secrets | Set `Metadata` level for secrets (not `RequestResponse`, which would log secret data) |
| Audit logs stored only on the node | Root access = log tampering | Ship to WORM storage (MinIO with object lock) |
| No retention policy for logs | Logs deleted before audit period | HIPAA: 6 years, SOC 2: Type II period + 1 year, PCI: 1 year online + 1 year archive |
| Entire cluster in PCI scope | Massive audit surface, huge cost | Isolate CDE in dedicated namespaces + nodes, minimize scope |
| Using `cluster-admin` for daily work | Violates principle of least privilege (every framework) | Create role-specific ClusterRoles, reserve cluster-admin for break-glass |
| No evidence collection automation | Auditor asks for data, team scrambles for weeks | Monthly automated evidence collection script |
| Missing data flow diagrams | Auditor cannot understand what data goes where | Maintain current data flow diagrams in architecture docs |
| Compliance labels missing on namespaces | Cannot query which namespaces are in-scope | Label all namespaces: `compliance: hipaa`, `pci-scope: in-scope` |

---

## Quiz

### Question 1
Your PCI DSS assessor asks: "How do you ensure that only payment workloads run on CDE nodes?" Explain the Kubernetes controls.

<details>
<summary>Answer</summary>

**Three Kubernetes mechanisms enforce CDE node isolation:**

1. **Taints and Tolerations**: CDE nodes are tainted with `pci-dss=cde:NoSchedule`. Only pods with the matching toleration can be scheduled on these nodes. Non-payment workloads lack the toleration and will never be placed on CDE nodes.

2. **Node Affinity**: Payment deployments use `requiredDuringSchedulingIgnoredDuringExecution` with a node selector for `node-role.kubernetes.io/pci-cde`. This ensures payment pods are only scheduled on CDE nodes, not on general-purpose nodes.

3. **Admission Control**: A validating webhook or OPA/Gatekeeper policy enforces that pods in CDE namespaces (e.g., `payment-processing`) must have the CDE toleration and node affinity. This prevents a developer from accidentally deploying a non-payment pod to a CDE namespace without the correct scheduling constraints.

**Evidence for the assessor:**
```bash
# Show taints on CDE nodes
kubectl get nodes -l node-role.kubernetes.io/pci-cde -o json | \
  jq '.items[].spec.taints'

# Show only CDE-tolerated pods run on CDE nodes
kubectl get pods --field-selector spec.nodeName=cde-node-1 -A

# Show admission policy preventing non-CDE pods
kubectl get constrainttemplate pci-node-isolation -o yaml
```

This creates a defense-in-depth approach: taints prevent general workloads from entering, affinity ensures payment workloads go to the right place, and admission control prevents bypasses.
</details>

### Question 2
A developer complains that setting the audit policy level to `RequestResponse` for the entire cluster is the safest choice for passing a SOC 2 audit because "we log absolutely everything." Why is this approach fundamentally flawed for a compliant environment?

<details>
<summary>Answer</summary>

**This approach is flawed for two major reasons:**

1. **Security Vulnerability (Secret Exposure)**: Logging everything at `RequestResponse` level will log the request and response bodies of all API calls. For Kubernetes Secrets, this means the actual plaintext secret values (API keys, passwords, TLS certificates) will be written to the audit log. The audit log itself becomes a massive security breach. Secrets should be logged at the `Metadata` level to record *who* accessed them without exposing the data.

2. **Noise and Performance Degradation**: Logging every health check (`/healthz`), metrics scraping (`/metrics`), and internal controller loop at `RequestResponse` will generate an unmanageable volume of logs. This not only impacts API server performance and consumes vast storage resources, but it also creates "audit noise." In a compliance audit, generating so much noise that you cannot find the actual unauthorized access events is treated as an operational failure.

A compliant policy is surgical: `None` for health checks, `Metadata` for most operations (including Secrets), and `RequestResponse` only for specific interactive or high-risk actions like `pods/exec`.
</details>

### Question 3
A HIPAA auditor asks for evidence that data is encrypted at rest. What do you show them?

<details>
<summary>Answer</summary>

**Three layers of encryption at rest evidence:**

1. **Kubernetes Secret encryption (etcd)**:
   ```bash
   # Show the EncryptionConfiguration
   cat /etc/kubernetes/encryption-config.yaml
   # Show that KMS v2 provider is configured
   # Show the Vault Transit key used for envelope encryption
   vault read transit/keys/kubernetes-secrets
   # Show the HSM is backing the Vault seal
   vault status | grep "Seal Type"  # Should show "pkcs11"
   ```

2. **Disk encryption (LUKS)**:
   ```bash
   # Show all data volumes are LUKS-encrypted
   lsblk -f  # LUKS volumes show as "crypto_LUKS"
   cryptsetup luksDump /dev/sdb  # Show encryption algorithm (aes-xts-plain64)
   # Show TPM binding
   systemd-cryptenroll /dev/sdb --tpm2-device=auto --dry-run
   ```

3. **Application-level encryption (if applicable)**:
   ```bash
   # Show TLS certificates for database connections
   kubectl get secret -n phi-production db-tls -o jsonpath='{.data.tls\.crt}' | \
     base64 -d | openssl x509 -text -noout
   ```

**For the auditor's report, also provide:**
- The encryption algorithm and key size (AES-256 for LUKS, AES-256-GCM for etcd via Vault Transit)
- Key rotation schedule (Vault Transit auto-rotates, LUKS keys sealed to TPM)
- Key management process (HSM holds master key, Vault manages data keys)
- A diagram showing the envelope encryption chain: Data -> DEK -> KEK -> HSM
</details>

### Question 4
Your company processes payments (PCI DSS) and healthcare data (HIPAA) on the same Kubernetes cluster. How do you handle overlapping compliance requirements?

<details>
<summary>Answer</summary>

**Run a single cluster with strict namespace isolation and the superset of controls:**

1. **Namespace separation**: PCI namespaces (`payment-processing`, `card-vault`), HIPAA namespaces (`phi-production`), and `shared-infra` (both apply).

2. **Apply the stricter control** when frameworks conflict. Audit retention: HIPAA wants 6 years, PCI wants 1 year -- apply 6. Access reviews: PCI quarterly, SOC 2 semi-annually -- apply quarterly.

3. **Dedicated nodes per domain**: PCI CDE nodes and HIPAA PHI nodes, each tainted and labeled. General nodes for non-regulated workloads.

4. **Network policies prevent cross-domain flow**: PHI cannot reach PCI namespaces and vice versa. Both reach shared infra (monitoring, DNS). Default deny with explicit allows.

5. **Unified audit logging with compliance labels**: Tag events with framework identifiers. Evidence collection scripts generate separate reports per framework from the same log store.

**Alternative**: Separate clusters per compliance domain -- simpler for auditors but higher operational cost.
</details>

---

## Hands-On Exercise: Implement a Kubernetes Audit Policy

**Task**: Design and deploy a compliance-grade audit policy for a kind cluster, then verify it captures the expected events.

### Steps

1. **Create an audit policy** (`audit-policy.yaml`):
   ```bash
   cat <<EOF > audit-policy.yaml
   apiVersion: audit.k8s.io/v1
   kind: Policy
   rules:
     - level: None
       nonResourceURLs: ["/healthz*", "/readyz*", "/livez*", "/metrics", "/openapi/*"]
     - level: Metadata
       resources: [{group: "", resources: ["secrets"]}]
     - level: RequestResponse
       resources: [{group: "", resources: ["pods/exec"]}]
     - level: Metadata
       verbs: ["create", "update", "patch", "delete"]
     - level: Metadata
   EOF
   ```

2. **Create a kind cluster** with audit logging (`kind-audit.yaml`):
   ```bash
   cat <<EOF > kind-audit.yaml
   kind: Cluster
   apiVersion: kind.x-k8s.io/v1alpha4
   nodes:
   - role: control-plane
     kubeadmConfigPatches:
     - |
       kind: ClusterConfiguration
       apiServer:
         extraArgs:
           audit-policy-file: /etc/kubernetes/audit-policy.yaml
           audit-log-path: /var/log/kubernetes/audit/audit.log
         extraVolumes:
         - name: audit-policy
           hostPath: /etc/kubernetes/audit-policy.yaml
           mountPath: /etc/kubernetes/audit-policy.yaml
           readOnly: true
           pathType: File
         - name: audit-log
           hostPath: /var/log/kubernetes/audit
           mountPath: /var/log/kubernetes/audit
           readOnly: false
           pathType: DirectoryOrCreate
     extraMounts:
     - hostPath: ./audit-policy.yaml
       containerPath: /etc/kubernetes/audit-policy.yaml
       readOnly: true
     - hostPath: /tmp/audit/logs
       containerPath: /var/log/kubernetes/audit
   EOF

   mkdir -p /tmp/audit/logs
   kind create cluster --config kind-audit.yaml
   ```

3. **Generate audit events** (wait for pod readiness):
   ```bash
   kubectl create secret generic test-secret --from-literal=password=s3cret
   kubectl get secret test-secret -o yaml
   kubectl delete secret test-secret
   kubectl run test-pod --image=nginx --restart=Never
   kubectl wait --for=condition=ready pod/test-pod --timeout=60s
   kubectl exec test-pod -- whoami
   ```

4. **Verify audit log captures events**:
   ```bash
   cat /tmp/audit/logs/audit.log | \
     jq -r 'select(.objectRef.resource=="secrets") |
       "\(.requestReceivedTimestamp) \(.verb) \(.user.username) \(.objectRef.name)"'
   ```

### Success Criteria
- [ ] Audit policy deployed with kind cluster
- [ ] Secret create/read/delete events captured at `Metadata` level
- [ ] Pod exec events captured with command details
- [ ] Health check endpoints produce no audit events
- [ ] Audit log output parseable with `jq`

---

## Key Takeaways

1. **Compliance is about evidence, not just security** -- you must prove controls exist and are operating
2. **Design audit policy before the auditor arrives** -- retrofitting logging is expensive and painful
3. **Minimize PCI DSS scope** -- fewer in-scope namespaces means less audit surface and lower cost
4. **Ship audit logs to tamper-evident storage** -- WORM storage with object lock prevents log manipulation
5. **Automate evidence collection** -- monthly scripts produce auditor-ready packages without scrambling

---

## Next Module

Continue to [Module 7.1: Cluster Upgrades & Lifecycle](../operations/module-7.1-upgrades/) to learn how to manage Kubernetes version upgrades, OS patching, and firmware updates in on-premises environments.
