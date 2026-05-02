---
revision_pending: false
title: "Module 6.4: Compliance for Regulated Industries"
slug: on-premises/security/module-6.4-compliance
sidebar:
  order: 5
---

# Module 6.4: Compliance for Regulated Industries

**Complexity**: `[ADVANCED]` | **Time**: 75 minutes | **Prerequisites**: [Physical Security & Air-Gapped Environments](../module-6.1-air-gapped/), [Hardware Security (HSM/TPM)](../module-6.2-hardware-security/), and [Enterprise Identity](../module-6.3-enterprise-identity/). These examples assume Kubernetes 1.35 or newer; when running Kubernetes commands, define `alias k=kubectl` once in your shell and then use `k` for CLI examples.

## What You'll Be Able to Do

After completing this module, you will be able to connect regulatory language to concrete Kubernetes controls, gather evidence that proves those controls operated, and explain the operational tradeoffs to auditors and engineering leaders.

1. **Design** a Kubernetes audit logging pipeline that captures API server access with tamper-evident long-term storage so a third-party auditor can reconstruct who did what to compliance-scoped resources.
2. **Implement** policy-as-code controls with Kyverno (or OPA/Gatekeeper) that block non-compliant workloads at admission time and emit machine-readable PolicyReports usable as audit evidence.
3. **Plan** an evidence-collection strategy that maps each technical control in your cluster to a specific clause in HIPAA, PCI DSS, SOC 2, or GDPR, including retention and chain-of-custody.
4. **Debug** a failed audit scenario by tracing missing evidence back to either a missing control or a missing log path, and **evaluate** whether to fix the control, fix the logging, or do both.
5. **Compare** the trade-offs between a single multi-tenant compliance cluster (one cluster, many regulatory regimes) and per-domain dedicated clusters, and justify a recommendation for a given organization.

## Why This Module Matters

In 2023, a healthcare SaaS company running Kubernetes on-premises failed their HIPAA audit. They had not been breached. They had simply lost the argument with their auditor. The auditor opened with a deceptively simple question: "Show me the audit log for every engineer who accessed the production namespace containing PHI in the last 90 days, including any `kubectl exec` sessions into database pods." The platform team had Kubernetes audit logging enabled, but the policy was set to the default `None` level for almost every resource. They had pod logs in Loki, but those captured application output, not API-server access. They had no record of which engineer ran `kubectl exec` into a Postgres pod two months ago, and they could not produce one retroactively because the audit events had never been written.

The remediation took four months. The team had to design a comprehensive audit policy, deploy a tamper-evident log pipeline that shipped events to write-once storage, build evidence-collection dashboards, and retroactively document every control that should have been there from day one. The total cost — including the delayed product launch, the consultant fees, and the contractual penalties owed to a hospital network whose own audit slipped because of the vendor delay — exceeded eight hundred thousand dollars. The painful irony, and the lesson that should sit at the top of every platform engineer's mental model, is that the technical controls were mostly already in place. RBAC was tight, NetworkPolicies existed, etcd was encrypted. What was missing was the evidence — the ability to prove to an outside party that the controls existed, were operating during the audit window, and were monitored for drift.

> **The Restaurant Inspection Analogy**
>
> A restaurant can have a spotless kitchen and still fail a health inspection. If the temperature logs are not posted on the freezer, the handwashing signs are missing from the bathroom, and the food-safety certificates are not on file in the manager's binder, the inspector cannot give a passing grade no matter how clean the floors are. Compliance is not about being secure. It is about proving you are secure to someone who is professionally skeptical and will be making decisions on the basis of paper. Your Kubernetes cluster might be locked down to a fault, but without audit logs, documented policies, and an evidence-collection workflow, you will lose the audit even though you would not lose the pen test.

The throughline of this module is that compliance work splits cleanly into three things: writing controls that *exist*, writing logs that *prove* the controls existed, and writing pipelines that *retain* those logs in a form an auditor will accept. We will build all three for the four regimes platform teams hit most often on-premises — HIPAA, SOC 2, PCI DSS, and GDPR/data-sovereignty — and you will leave with a working audit pipeline you can demonstrate end to end on a kind cluster.
## What You'll Learn

- How HIPAA, SOC 2 Type II, PCI DSS v4.0, and GDPR data-sovereignty rules each map to specific Kubernetes controls (and which controls satisfy more than one regime at once).
- How to design a Kubernetes audit policy that captures the events auditors actually ask for, without drowning the API server in logging overhead or — worse — leaking secret values into the audit stream.
- How to build a tamper-evident audit pipeline using Fluent Bit plus dual-output to OpenSearch (search) and MinIO with object lock (immutable long-term retention).
- How to keep PCI DSS scope small using namespaces, taints, node affinity, and admission control, and why scope minimization is the single highest-leverage compliance decision you will make.
- How to use Kyverno PolicyReports to turn admission-control decisions into per-control evidence that can be filtered, exported, and handed directly to an assessor.
- How to walk through a worked compliance failure end to end — from the auditor's question, to the missing evidence, to the configuration change that fixes it, to the verification that the fix actually works.

Treat the module as an audit rehearsal, not as a catalogue of controls. Each technical choice has to answer three questions. What risk does the control reduce? What evidence proves the control operated during the audit window? What failure would make that evidence unreliable? The examples use Kubernetes 1.35 behavior and avoid cloud-only assumptions, because regulated on-premises platforms usually carry physical, identity, and locality constraints that managed clusters hide from the team.

The working habit to build is translation. Auditors ask for "access to systems containing PHI," "segmentation of the CDE," or "restricted processing of personal data." Kubernetes answers with `RoleBinding` objects, audit events, NetworkPolicies, taints, admission decisions, and signed evidence bundles. Your job is to bridge those vocabularies without guessing. When the bridge is explicit, a skeptical reviewer can trace every claim from the framework clause to a cluster object and then to an immutable artifact.

## Mapping Regulatory Frameworks to Kubernetes Controls

Before you can design any audit pipeline, you have to know which clauses of which standards apply to your cluster, and which Kubernetes primitives satisfy them. The mistake new platform teams make is treating each regulation as a fresh problem. In practice, almost every framework asks for the same handful of underlying controls — they just label them differently. A single set of well-implemented Kubernetes primitives (RBAC, NetworkPolicy, audit policy, encryption, admission control) can satisfy four or five regimes simultaneously if you label resources carefully and produce evidence in a common format.

```ascii
┌──────────────────────────────────────────────────────────────────┐
│           COMPLIANCE FRAMEWORKS vs KUBERNETES CONTROLS           │
│                                                                  │
│  Requirement          HIPAA    SOC2    PCI DSS    K8s Control    │
│  ──────────────────   ─────   ─────   ───────    ───────────     │
│  Access control        X        X        X       RBAC + OIDC     │
│  Audit logging         X        X        X       Audit policy    │
│  Encryption at rest    X        X        X       etcd encryption │
│  Encryption in transit X        X        X       mTLS (Istio)    │
│  Network segmentation  X        X        X       NetworkPolicy   │
│  Vulnerability mgmt    X        X        X       Trivy/Grype     │
│  Change management     X        X        X       GitOps + CI/CD  │
│  Incident response     X        X        X       Alerting + DR   │
│  Physical security     X                 X       Datacenter      │
│  Data sovereignty      GDPR              GDPR    On-prem + geo   │
│  Key management                          X       HSM/Vault       │
│  Penetration testing            X        X       Annual pentest  │
│  Business continuity   X        X                Multi-site DR   │
└──────────────────────────────────────────────────────────────────┘
```

Read that grid as a hint about leverage. Anything with an X in three columns is a control you build once and reuse across audits. RBAC, audit logging, encryption, and network segmentation are the four pillars on which a compliant cluster is built. Spend most of your time getting those four right and the rest of the audit becomes documentation work rather than engineering work. The rows that show up in only one column — physical security for HIPAA and PCI, key management for PCI, business continuity for HIPAA and SOC 2 — are domain-specific and worth treating as separate workstreams.

The framework-to-control map is also how you defend against scope creep. When a sales engineer brings in a customer who wants ISO 27001 and FedRAMP added to next quarter's compliance roadmap, the question is not "how much new work is this?" The question is "which rows in the grid are already green, and which truly new rows do these standards add?" In most cases the answer is one or two truly new rows plus a great deal of paperwork. Estimating new compliance work as deltas against your existing control matrix, rather than as fresh greenfield projects, is one of the highest-leverage skills a platform lead can develop.

A useful control matrix also makes ownership visible. RBAC evidence usually belongs to the identity team. NetworkPolicy evidence may belong to the platform team. Vulnerability evidence may come from security engineering, while physical access evidence comes from facilities. If those owners are not named before the audit, the platform team becomes the accidental collector for every missing artifact. That is how a technical audit turns into weeks of hallway archaeology.

Pause and predict: if your cluster has excellent NetworkPolicies but no namespace labels, what happens when the auditor asks for "all HIPAA-scoped segmentation evidence"? You may have the control, but you do not have the filter that proves which workloads are in scope. The safest design is to make labels mandatory at namespace creation and to treat missing labels as a failed admission decision, not as a documentation cleanup task.

## HIPAA Physical and Administrative Controls

HIPAA's Security Rule (45 CFR 164.310) requires physical safeguards for any system that stores, processes, or transmits Protected Health Information. The clauses were written long before Kubernetes existed, but the mapping is now well-established and is essentially what every healthcare auditor will work from.

### Physical Safeguard Requirements

| HIPAA Requirement | Section | On-Prem K8s Implementation |
|-------------------|---------|---------------------------|
| Facility access controls | 164.310(a)(1) | Badge access, visitor log, mantrap for server room |
| Workstation use policy | 164.310(b) | kubectl access via VPN only, session timeout |
| Workstation security | 164.310(c) | Encrypted laptops, MFA for kubectl (Keycloak) |
| Device and media controls | 164.310(d)(1) | Encrypted disks (LUKS+TPM), sanitize before disposal |
| Hardware inventory | 164.310(d)(2)(iii) | CMDB tracking all nodes, serial numbers, locations |

### Kubernetes-Specific HIPAA Controls

Inside the cluster, HIPAA enforcement starts with labelling. Every namespace that touches PHI should carry the labels `compliance: hipaa` and `data-classification: phi`, plus annotations for ownership and retention. These labels are not decorative. They drive admission policies (which webhooks fire for which namespaces), evidence collection (which namespaces show up in monthly exports), and incident-response playbooks (which on-call team gets paged when a PHI namespace alert fires). Without consistent labels, you end up with one-off scripts that have to enumerate namespaces by name and they rot the moment a new PHI workload lands.

Once the labels are in place, lock the namespace down with NetworkPolicies that default-deny both ingress and egress. Allowed ingress should be limited to other HIPAA-labeled namespaces and to specific API-gateway pods (matched by label, never by IP, because pod IPs are ephemeral). Egress should be limited to other HIPAA namespaces and to DNS on port 53 — full stop. Anything else, including outbound HTTPS to the public internet, has to be explicitly enumerated and justified during an audit. The default-deny posture is non-negotiable: an auditor will not accept "we have a policy that blocks malicious egress" if the underlying default is allow-all and the block is just a deny-list.

HIPAA also forces you to connect cluster access to workstation and facility controls. If an engineer can administer PHI workloads only from a managed laptop, through VPN, with MFA, then the Kubernetes audit event is only one piece of the evidence chain. The companion evidence is the device posture record, the VPN session, and the identity-provider authentication log. A strong audit package links those records by username and timestamp, so the reviewer can reconstruct the path from a human at a workstation to an API request against a namespace.

That linkage matters during incident response. A suspicious `pods/exec` event is not enough by itself. You need to know whether the engineer was on call, whether their laptop was compliant, whether the VPN session came from an expected region, and whether the namespace contained PHI. When those facts are joined automatically, the security team can decide quickly whether an event is routine support or a reportable privacy incident.

## SOC 2 on Premises

SOC 2 (Service Organization Control 2) is an audit framework based on five Trust Services Criteria. It is the framework most B2B SaaS companies will face first, because enterprise customers in the United States routinely require a SOC 2 Type II report before signing contracts. Type II is the variant that matters: it covers a defined window (typically twelve months) and proves that controls operated *consistently* across that window, not merely that they exist on the day the auditor walked in.

### Trust Services Criteria Mapping

| Criteria | Key Controls | K8s Implementation |
|----------|-------------|-------------------|
| **Security** (CC6) | Access control, network protection | RBAC, NetworkPolicy, mTLS, WAF |
| **Availability** (A1) | Uptime, disaster recovery | Multi-replica, PDB, multi-site DR |
| **Processing Integrity** (PI1) | Accurate processing | GitOps (immutable deployments), admission webhooks |
| **Confidentiality** (C1) | Data protection | Encryption at rest (HSM), encryption in transit (mTLS) |
| **Privacy** (P1-P8) | Personal data handling | Namespace isolation, audit logging, data retention |

### SOC 2 Evidence Collection

> **Stop and think**: An auditor will not accept "we have RBAC configured" as evidence. They need proof that specific controls were in place at specific times across the entire audit period. How does a monthly automated evidence-collection job differ from simply exporting your current configuration on the day the auditor asks?

The difference is chain-of-custody and continuity. A point-in-time export proves the cluster looks correct *today*. A monthly archive of point-in-time exports — written to immutable storage with timestamps the auditor can verify — proves the cluster looked correct on each of the twelve sample dates the auditor will pick. SOC 2 Type II is a sampling exercise. The auditor picks dates, asks for evidence from those dates, and judges whether the controls were operating. If you can produce a signed, timestamped snapshot for each requested date, you pass. If you cannot, you fail, even if the cluster is currently configured perfectly.

```bash
#!/bin/bash
# soc2-evidence.sh -- Run monthly via CronJob, store in evidence repository
EVIDENCE_DIR="/evidence/soc2/$(date +%Y-%m)"
mkdir -p "${EVIDENCE_DIR}"

# CC6.1: Access control
kubectl get clusterrolebindings -o json > "${EVIDENCE_DIR}/clusterrolebindings.json"
kubectl get rolebindings --all-namespaces -o json > "${EVIDENCE_DIR}/rolebindings.json"

# CC6.1: Users with cluster-admin (the high-blast-radius set the auditor will probe)
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

# Sign the entire bundle so a tampered file is detectable
sha256sum "${EVIDENCE_DIR}"/* > "${EVIDENCE_DIR}/sha256sums.txt"
gpg --detach-sign --armor "${EVIDENCE_DIR}/sha256sums.txt"

echo "Evidence: ${EVIDENCE_DIR} ($(du -sh ${EVIDENCE_DIR} | cut -f1))"
```

The signing step at the bottom is what turns a folder of JSON exports into something auditors will accept as evidence. A folder of JSON files, by itself, is something any administrator could have generated five minutes ago. A folder of JSON files with a SHA-256 manifest signed by a key that lives in your HSM is something that can be verified to have existed on the date the signature claims, because changing any file would invalidate the manifest and replacing the manifest would require access to the signing key. That chain of custody is what an auditor needs to accept your evidence without insisting on independent verification.
## PCI DSS Scope Isolation

PCI DSS requires strict isolation of the Cardholder Data Environment (CDE), which is the set of systems that store, process, or transmit primary account numbers. On Kubernetes, this means the namespaces handling payment-card data must be separated from everything else with such rigor that an auditor would conclude a compromise in any non-CDE namespace could not pivot to the CDE.

```ascii
┌──────────────────────────────────────────────────────────────────┐
│               PCI DSS SCOPE ON KUBERNETES                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐         │
│  │               KUBERNETES CLUSTER                    │         │
│  │                                                     │         │
│  │  ┌──────────────────────┐  ┌──────────────────────┐ │         │
│  │  │  IN-SCOPE (CDE)      │  │  OUT-OF-SCOPE        │ │         │
│  │  │                      │  │                      │ │         │
│  │  │  payment-processing  │  │  marketing-site      │ │         │
│  │  │  card-vault          │  │  analytics           │ │         │
│  │  │  tokenization        │  │  internal-tools      │ │         │
│  │  │                      │  │  staging             │ │         │
│  │  │  Strict controls:    │  │                      │ │         │
│  │  │  - Dedicated nodes   │  │  Standard controls   │ │         │
│  │  │  - Network isolation │  │                      │ │         │
│  │  │  - Full audit logging│  │                      │ │         │
│  │  │  - WAF               │  │                      │ │         │
│  │  │  - File integrity    │  │                      │ │         │
│  │  └──────────┬───────────┘  └──────────────────────┘ │         │
│  │             │ Network Policy: DENY ALL except       │         │
│  │             │ explicitly allowed connections        │         │
│  └─────────────┴───────────────────────────────────────┘         │
│                                                                  │
│  Key principle: MINIMIZE the CDE. Fewer namespaces in scope      │
│  = less to audit = lower compliance cost.                        │
└──────────────────────────────────────────────────────────────────┘
```

> **Stop and think**: PCI DSS scope isolation means fewer namespaces to audit, which directly reduces compliance cost. What is the incentive for engineering teams to keep their workloads OUT of PCI scope, and how would you enforce that organizationally if engineering and product happen to disagree?

The incentive answer is usually some mixture of velocity (in-scope workloads have heavier change-management overhead) and freedom (you cannot use whatever third-party SaaS you want from a CDE namespace). The enforcement answer is policy-as-code at the platform layer plus a one-page architecture review whenever a workload crosses a scope boundary. If the platform team owns the admission controllers, the platform team owns the question of whether a new namespace lands in the CDE — which means the conversation happens before the workload is built, not after the auditor finds it.

### Dedicated Nodes for the CDE (PCI DSS Req 2.2.1)

Workload-level isolation is necessary but not sufficient for PCI; the standard expects node-level isolation as well, so that a kernel-level escape from a non-payment container cannot land on the same host as a card-data container. Three primitives cooperate to enforce this on Kubernetes: taints prevent non-payment pods from being scheduled onto CDE nodes, node affinity ensures payment pods *only* land on CDE nodes, and an admission webhook backs both of those up by rejecting any pod in a CDE namespace that lacks the right toleration and affinity.

```bash
# Taint CDE nodes so only payment workloads schedule there
kubectl taint nodes cde-node-{1,2,3} pci-dss=cde:NoSchedule
kubectl label nodes cde-node-{1,2,3} node-role.kubernetes.io/pci-cde=""
```

A correctly configured payment workload deployment will declare a toleration for the `pci-dss=cde:NoSchedule` taint, a `requiredDuringSchedulingIgnoredDuringExecution` node affinity for `node-role.kubernetes.io/pci-cde`, a security context that runs as non-root, mounts a read-only root filesystem, drops all Linux capabilities, and refuses privilege escalation, and labels of `pci-scope: in-scope` on both the Deployment and the resulting Pod. The labels on both objects matter because audit queries against pods are simpler and faster than chasing owner-references back through ReplicaSets to Deployments, and the auditor will run those queries themselves during the assessment.
## Kubernetes Audit Policy Design

The Kubernetes audit policy controls what the API server logs. A well-designed policy captures the events compliance frameworks actually care about while staying quiet on the high-volume internal traffic that generates noise without value. A bad policy either logs nothing useful or logs so much that the log pipeline buckles under its own weight; both failure modes will sink an audit.

> **Pause and predict**: The audit policy below uses `Metadata` level for Secrets instead of `RequestResponse`. Why would logging Secret access at `RequestResponse` level actually make your cluster *less* secure, even though it appears to capture more information about what is happening?

### Understanding Audit Levels

The Kubernetes API server supports four audit levels, each picking a point on the trade-off between detail and risk. `None` writes no event at all — appropriate for high-volume, low-value endpoints like health checks or the metrics scrape that runs every fifteen seconds and otherwise floods the log. `Metadata` records who, what, when, and against which object, but not the request body; this is the right default for Secrets because it answers "who looked at this secret and when" without writing the secret value into a place the auditor can see. `Request` adds the request body, which is the right level for things like Role creation where the body is what you actually need to audit and is not itself sensitive. `RequestResponse` adds the response body and is the right level for `pods/exec` and `pods/attach`, where you may need to reconstruct exactly what command an engineer ran and what the pod returned to them.

The reason logging Secrets at `RequestResponse` is dangerous is that the API server's response to `kubectl get secret` includes the base64-encoded value of the secret. Any administrator with read access to the audit log — which is a much wider population than the set of administrators with read access to the secret itself — can decode the value. The audit log, which is supposed to be your strongest evidence, becomes your weakest credential store. This is the canonical example of how a well-meaning compliance change ("let's log everything!") can produce a worse security posture than the system you started with.

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

Order matters in audit policies, because the API server applies the first rule that matches and stops. The `None` rules at the top are deliberately first so health-check noise is dropped before any subsequent rule has a chance to log it. The `RequestResponse` rules for `pods/exec` and RBAC changes sit in the middle so they take precedence over the `Metadata` catch-all near the bottom. The catch-all itself is essential — without it, anything not specifically matched would default to no logging at all, which is exactly the failure mode that bit the healthcare SaaS company in the opening story.

### Configure the API Server

Once the policy file exists, the API server has to be told to use it. On a kubeadm cluster these flags go into `/etc/kubernetes/manifests/kube-apiserver.yaml`; on kind they go into the `extraArgs` of the cluster config (which is what we will use in the hands-on exercise). The flags below tell the API server which policy to apply, where to write the log, how long to retain individual log files on disk, and what format to emit. Disk retention is intentionally short because the source of truth is the log pipeline; the on-disk file is a buffer, not the archive.

```bash
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--audit-log-path=/var/log/kubernetes/audit/audit.log
--audit-log-maxage=365        # Keep 1 year on disk (ship to WORM for longer)
--audit-log-maxbackup=30
--audit-log-maxsize=200       # 200 MB per file
--audit-log-format=json
```

The audit policy file and the log directory both have to be mounted as volumes inside the API server static pod, otherwise the API server will start with logging silently disabled — the symptom is "no errors, no logs" which is the worst kind of failure because nothing alerts you to it. After making the change, restart the kubelet on the control-plane node and verify with `journalctl -u kubelet` that the API server pod restarted cleanly, then tail the audit log file to confirm events are being written.

Before running this in production, write down the evidence question each rule is meant to answer. Secret reads answer "who accessed sensitive configuration." RBAC writes answer "who changed privileges." `pods/exec` events answer "who opened an interactive path into a workload." Health checks answer nothing useful, so they should not consume retention budget. This simple annotation exercise exposes rules that are too broad and rules that are missing.

Which approach would you choose here and why: a small audit policy with a catch-all `Metadata` rule, or a long policy that tries to enumerate every regulated namespace by name? The catch-all usually wins because it is resilient to new namespaces. The named-list version looks precise, but it fails silently when a new `phi-claims` namespace appears and nobody updates the policy file. Compliance systems should fail closed when the environment changes.

## Tamper-Evident Audit Log Pipeline

Audit logs stored on the node's filesystem can be modified by anyone with root access on that node, which means they fail the most basic requirement an auditor will impose: that the logs be trustworthy as evidence of past behavior. The fix is a pipeline that ships logs off the node in near real-time and writes them to storage that prevents modification.

```ascii
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
│  (searchable, 90-day)       (immutable, WORM, 7-year)            │
│     │                          │                                 │
│     ▼                          ▼                                 │
│  Kibana/Grafana             Object Lock prevents                 │
│  (dashboards, alerts)       deletion or modification             │
│                                                                  │
│  Tamper evidence:                                                │
│  1. Logs signed with HMAC at source (Fluent Bit)                 │
│  2. WORM storage prevents modification                           │
│  3. Daily SHA256 of log batches stored separately                │
│  4. Alert if log gap > 5 minutes (indicates tampering/failure)   │
└──────────────────────────────────────────────────────────────────┘
```

The pattern that scales is dual-output: ship every event to OpenSearch for search and dashboarding, and simultaneously write the same event to an S3-compatible bucket configured with object lock for long-term immutable retention. OpenSearch is your interactive surface — it is what on-call uses to investigate an alert and what you point at when an auditor asks an ad-hoc question. The S3 bucket is your archive — it holds events for the multi-year retention window most regulations require and it is what you would re-index from if OpenSearch were lost. The two outputs share a single event stream, so they are guaranteed to agree about what happened, and if they ever disagree (bytes differ for the same timestamp) the divergence itself is an alert that the pipeline is compromised.

### Fluent Bit Configuration for Audit Logs

Deploy Fluent Bit as a DaemonSet on the control-plane nodes and point its `tail` input at the API server's audit log file. The relevant configuration looks like this:

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

Two things are worth stressing about this configuration. First, OpenSearch should be on a *different* control plane than the cluster being audited — typically a dedicated logging cluster — so that an attacker who roots the audited cluster cannot delete the evidence from the same pane of glass they used to compromise it. Second, the MinIO bucket must have object lock enabled in compliance mode at bucket-creation time; you cannot retroactively turn on immutability, and an auditor who sees a "governance" mode bucket where the lock can be lifted by an admin will downgrade the control. Compliance mode means "no one, including the root user, can delete or modify these objects until the retention window expires" — which is exactly the property a regulator wants to see.

The pipeline also needs negative evidence. It is not enough to prove that logs arrived. You must prove that silence would be detected. A simple control is an alert that compares expected event volume with observed volume for each control-plane node. Another is a heartbeat event written by the collector every minute. If the heartbeat stops, the absence of audit data becomes visible within the monitoring window, rather than appearing months later as an audit gap.

Do not hide pipeline failures inside the same cluster being audited. If Fluent Bit cannot reach OpenSearch, the alert should land in an independent paging path, and the outage should create its own evidence record. That record may feel embarrassing, but it is useful. A documented, bounded outage with corrective action is a process signal. An unexplained hole in the audit archive is a finding.

## Data Sovereignty

Data sovereignty rules require that data remain within a specific geographic or legal jurisdiction throughout its lifecycle, including backups, replicas, and disaster-recovery copies. GDPR is the most familiar driver of these requirements, but a growing number of jurisdictions impose them — Schrems II, the EU AI Act, and various national data-localization laws all converge on the same operational requirement: prove the bytes never crossed an unapproved border.

| Requirement | Implementation |
|-------------|---------------|
| Data must stay in-country | On-premises in domestic datacenter(s) |
| Data must not be accessible by foreign entities | Air-gapped or encrypted with locally-held keys (not cloud KMS) |
| Right to deletion (GDPR) | Application-level deletion + backup purge + audit proof |
| Cross-border transfer restrictions | No replication to foreign sites; DR site must be domestic |
| Government access requests | On-prem with local legal framework; no CLOUD Act exposure |

### Kubernetes Configuration for Data Sovereignty

The cluster-level enforcement point for data sovereignty is the admission controller. Use a ValidatingWebhookConfiguration or a Kyverno/OPA Gatekeeper policy to reject pods whose images come from unapproved registries — typically anything outside `registry.internal.corp` or your designated domestic mirror. All third-party container images have to be mirrored through the approved transfer process described in [Module 6.1](../module-6.1-air-gapped/), and the approval process should produce an artifact (a signed manifest or a CMDB entry) that the admission controller can verify before letting the image run. Without this enforcement, a single careless `image: docker.io/library/nginx` slipped past code review pulls bytes across a border the moment the pod is scheduled.
## Implementing Policy-as-Code for Compliance

To enforce regulatory controls continuously rather than as a quarterly cleanup exercise, Kubernetes clusters rely on policy-as-code engines like Kyverno or OPA Gatekeeper. These tools install as admission controllers, which means they get to inspect every resource that arrives at the API server and either allow it, mutate it, or reject it before it is persisted to etcd. The compliance value is twofold: non-compliant resources never get created in the first place (which is a stronger control than detecting them after the fact), and every admission decision produces a structured, queryable record that becomes part of your audit evidence.

### Why Kyverno for Compliance Reporting

Kyverno is a CNCF graduated project that uses Kubernetes-native YAML for policy definitions, which means platform engineers do not have to learn Rego (the policy language used by OPA) before they can write or read a policy. For compliance work, Kyverno's most valuable feature is the PolicyReport CRD: every time a policy is evaluated against a resource — whether it passes, fails, is skipped, or is in warn mode — Kyverno writes the result to a PolicyReport object that lives in the same namespace as the resource. PolicyReports are queryable with `kubectl`, exportable as JSON, and easy to render as human-readable HTML for an assessor.

### A Compliance Policy, End to End

Let's walk through a single Kyverno policy from definition through enforcement to evidence. The policy below enforces that every pod drops all Linux capabilities by default, which satisfies pod-security baselines used in SOC 2 CC6.1, PCI DSS Req 11, and HIPAA's "minimum necessary" principle.

```yaml
# Enforce that all pods drop ALL capabilities (SOC 2 CC6.1 / PCI DSS Req 11)
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-drop-all-capabilities
  annotations:
    policies.kyverno.io/category: Pod Security Standards (Restricted)
    policies.kyverno.io/severity: high
    policies.kyverno.io/subject: Pod
    policies.kyverno.io/description: |
      Containers must drop ALL Linux capabilities. Required for HIPAA, SOC 2,
      and PCI DSS. Evidence emitted via PolicyReport.
spec:
  validationFailureAction: Enforce
  background: true
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

Three fields on this policy are doing real compliance work. `validationFailureAction: Enforce` means non-compliant pods are rejected at admission; the alternative (`Audit`) only records violations without blocking, which is appropriate when you are rolling a policy out gradually but is not what an auditor wants to see in production. `background: true` tells Kyverno to scan existing resources on a schedule, not just new ones — without this flag, a pod created before the policy existed would never produce a PolicyReport entry and would silently violate the control. The annotations are not enforcement, but they are evidence: when the auditor exports the policy YAML they see the explicit framework mapping, which short-circuits the inevitable "what does this policy mean and why does it exist" conversation.

### Walkthrough: Policy Result on Real Workloads

Once the policy is applied, deploy a deliberately non-compliant pod and watch what happens:

```bash
$ kubectl run insecure --image=nginx
Error from server: admission webhook "validate.kyverno.svc-fail" denied
the request: resource Pod/default/insecure was blocked due to the
following policies:
  require-drop-all-capabilities:
    drop-all-capabilities: 'validation error: Containers must drop ALL
      capabilities. rule drop-all-capabilities failed at path
      /spec/containers/0/securityContext/capabilities/drop/'
```

The pod never reaches etcd, which means it never reaches the scheduler, which means it never runs. From a security standpoint, this is the strongest control you can apply: the non-compliant configuration is impossible, not just discouraged. Now apply a compliant version and check the resulting PolicyReport:

```bash
$ kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: secure
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      capabilities:
        drop: ["ALL"]
EOF
pod/secure created

$ kubectl get policyreport -A
NAMESPACE   NAME                              PASS   FAIL   WARN   ERROR  SKIP
default     cpol-require-drop-all-capabili.   1      0      0      0      0
```

That single line in the PolicyReport is the unit of compliance evidence. Multiply it across every namespace and every policy you have deployed and you get a cluster-wide control matrix that maps directly to the spreadsheet your auditor will hand you on day one. The query an auditor cares about is "show me every pod that violated a HIPAA-mapped policy in the last quarter," and with Kyverno that becomes a one-liner:

```bash
kubectl get policyreport -A -o json | \
  jq -r '.items[] |
    .results[] |
    select(.result == "fail") |
    "\(.policy) \(.resources[0].namespace)/\(.resources[0].name) \(.message)"'
```

Pipe that into your monthly evidence-collection script and you have continuous compliance reporting without writing a single custom controller. Compare this with the alternative — a quarterly manual audit where someone runs `kubectl get pod -o yaml` for every namespace and grep through the output — and the case for policy-as-code becomes overwhelming. The auditor gets better evidence, the platform team spends less time on audit prep, and the engineers writing application manifests get instant feedback at admission time instead of weeks later when the audit team finds the violation.

### Operational Patterns for Rolling Out Policies

Rolling a new policy from zero to enforce on a live cluster is where teams most often hurt themselves. The pattern that works is staged: first deploy with `validationFailureAction: Audit` and watch PolicyReports for a week to find existing violators. Fix or whitelist the violators. Then flip to `Enforce`. If you skip the audit phase and go straight to enforce, you will block a deployment from a critical service at three in the morning and the resulting incident will end any political support you had for the rest of your compliance program. The audit-then-enforce cycle is also evidence in itself — it shows the auditor that you operate compliance changes the same way you operate any other production change, which is exactly the maturity signal SOC 2 looks for.
## A Worked Compliance-Failure Walkthrough

Reading about compliance is useful, but the skill that earns money is the ability to take an auditor's question, work backward to the missing evidence, identify the missing control, and produce a remediation that closes the gap permanently. The walkthrough below is the kind of scenario you will face in your first real audit. Read it as a model for how to think when an auditor lands an unfamiliar question.

### Scenario

You are the on-call platform engineer for a healthcare SaaS company. The HIPAA auditor has just sent the following email:

> "For the audit window covering Q1, please provide an enumeration of every interactive shell session opened by an engineer into a pod in the `phi-production` namespace, including the username, the target pod, the timestamp, and the commands that were run. Flag any session that lasted longer than fifteen minutes for additional review."

You have a kind cluster running locally that mirrors the production audit configuration, and you have the past quarter of audit logs available in OpenSearch. Your task is to either produce the requested evidence or, if that is impossible, identify and fix the gap so future audits can answer the question.

### Step 1: Translate the Question into a Log Query

The auditor's question maps to API server `pods/exec` and `pods/attach` events filtered to the `phi-production` namespace. Both verbs represent interactive access; `portforward` is sometimes lumped in but is technically a network-tunnel rather than a shell session, so a precise answer treats it separately. The reasoning step here is to recognize that "interactive shell session" is the auditor's language and `pods/exec`/`pods/attach` is the Kubernetes-API language, and to bridge them deliberately rather than guessing.

```bash
# Start with the broadest query and narrow from there
kubectl logs -n monitoring deploy/opensearch-client -- \
  curl -s -XGET "https://opensearch:9200/k8s-audit-*/_search" \
       -H 'Content-Type: application/json' -d @- <<'EOF'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "objectRef.namespace": "phi-production" } },
        { "terms":  { "objectRef.subresource": ["exec","attach"] } }
      ]
    }
  },
  "size": 1000
}
EOF
```

### Step 2: Verify the Audit Policy Captures the Right Detail

Before you trust the query result, check that the audit policy was actually configured to log these events at the level the auditor needs. The policy section earlier in this module logs `pods/exec` at `RequestResponse`, which is what we want — the request body contains the command and the response body contains the output. If the policy were set to `Metadata` for `pods/exec`, you would have a list of sessions but no record of which commands were run, and the auditor's question would be unanswerable without re-running every session.

```bash
grep -A3 'pods/exec' /etc/kubernetes/audit-policy.yaml
# Expected output:
#   - level: RequestResponse
#     resources:
#     - group: ""
#       resources: ["pods/exec", "pods/attach", "pods/portforward"]
```

### Step 3: Produce the Evidence

If the policy is correct and the query returns events, you can shape them into the report the auditor asked for. The transformation below produces a one-line-per-session CSV with the fields requested, and flags any session whose total event span exceeds fifteen minutes.

```bash
jq -r '
  .hits.hits[]._source |
  select(.objectRef.subresource == "exec" or .objectRef.subresource == "attach") |
  "\(.requestReceivedTimestamp),\(.user.username),\(.objectRef.name),\(.requestObject.command|join(" "))"
' query-result.json | sort > exec-sessions.csv
```

A senior engineer would not stop here. They would also verify that the OpenSearch index covers the entire audit window (no gaps from the pipeline being down), cross-check the count of sessions against an independent source like an MDM-managed bastion log, and produce a one-paragraph cover note explaining what was queried, what assumptions were made, and what the limitations are. The cover note is what separates "evidence" from "data" — auditors want to know that a human reviewed the output and stands behind it.

### Step 4: Fix the Gap if One Exists

Suppose the query returns nothing for the first month of the quarter, then a normal volume thereafter. The reasoning step is to ask "did interactive access genuinely not happen, or did the pipeline fail?" The answer is almost always the latter, because real production systems get exec'd into. Cross-check with the Fluent Bit metrics:

```bash
kubectl logs -n logging daemonset/fluent-bit | grep -i 'audit.log'
# If you see "open() error" or "stat() error" for January dates,
# the on-disk audit log was rotated faster than Fluent Bit could ship it.
```

The remediation is twofold: backfill what you can from the on-disk log file (usually nothing if the rotation was aggressive) and shorten the rotation interval going forward so the buffer is always larger than the worst-case ingestion delay. Document the gap in your evidence package — the auditor would much rather see "events from Jan 1–14 are unrecoverable due to a rotation misconfiguration that we have since fixed; here is the post-incident review" than discover the gap themselves. Self-disclosure with remediation is treated very differently from concealment.

### What This Walkthrough Models

The general shape of compliance debugging is: translate the auditor question into Kubernetes terms, verify the control that should have produced the evidence is configured correctly, query the evidence store, verify the query is complete, and disclose any gaps with their remediation. Every word of that sequence matters and skipping any of them is how teams fail audits they should have passed.
## Evidence Collection for Auditors

Auditors think in controls, not in tools. They do not care that you use OpenSearch or Loki or Splunk; they care that you can produce evidence for control X over time period Y. The evidence-collection layer is the translation between your tooling and their language.

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

The pattern that scales is a single CronJob that runs monthly and produces a directory of artifacts organized by control area: access control (cluster-admin bindings, OIDC flags, recent role changes), encryption (etcd config snippet, HSM status output, LUKS device list), network segmentation (NetworkPolicy YAML for every namespace, plus a generated diagram of allowed flows), namespace inventory (every namespace with its compliance labels), and pod security (PSA enforcement levels per namespace). Package the directory as a timestamped, signed tarball and write it to the same WORM bucket that holds the audit logs. Run this on the same schedule every month, never by hand, because an auditor who sees evidence files all timestamped on the day before the audit will assume they were generated for the audit rather than collected during the period.

The discipline that distinguishes a mature compliance program from a thrash-ridden one is that the evidence is always older than the audit. If an auditor asks for January's evidence in February and you have to scramble to generate it, you have already failed a process control even if the underlying technical control was in place. Build the CronJob early, alert on its failure, and let twelve months of green runs do the talking when the auditor arrives.
## Did You Know?

- **HIPAA has no certification.** Unlike PCI DSS (which has the QSA assessor process) or SOC 2 (which produces a formal report from a CPA firm), HIPAA compliance is self-attested. The Office for Civil Rights only audits after a breach or complaint. This means many organizations believe they are HIPAA-compliant but have never been tested by a third party — and the test, when it eventually comes, is generally a breach investigation rather than a friendly assessor.

- **PCI DSS v4.0 (effective March 2025)** added explicit requirements for container security, including image integrity verification (Req 6.3.2) and runtime protection (Req 11.5.1.1). Previous versions did not mention containers at all, leaving QSAs to interpret traditional controls against Kubernetes resources. The shift means that admission-time image signing (with cosign or similar) and runtime detection (with Falco or Tracee) have moved from "good practice" to "required control" for any cluster handling cardholder data.

- **SOC 2 Type I vs Type II**: Type I is a point-in-time snapshot ("controls exist today"). Type II covers a defined period (usually twelve months) and proves controls were consistently operating across that period. Type II is far more valuable and is what enterprise customers typically require before signing. For Kubernetes, this is the difference between needing today's `kubectl get` output and needing twelve months of evidence with verifiable timestamps.

- **The CLOUD Act (2018)** allows United States law enforcement to compel US-based providers to produce data regardless of where it is stored geographically. This is a primary driver for data sovereignty decisions for European, Canadian, and Australian customers. On-premises infrastructure operated by a non-US provider eliminates CLOUD Act exposure entirely, which is one of the most concrete commercial advantages of on-premises Kubernetes for B2B SaaS companies selling into regulated European markets.
## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Audit policy set to `None` for secrets | No evidence of who accessed secrets | Set `Metadata` level for secrets (not `RequestResponse`, which would log secret data) |
| Audit logs stored only on the node | Root access = log tampering | Ship to WORM storage (MinIO with object lock) |
| No retention policy for logs | Logs deleted before audit period ends | HIPAA: 6 years, SOC 2: Type II period + 1 year, PCI: 1 year online + 1 year archive |
| Entire cluster in PCI scope | Massive audit surface, huge cost, slow change windows | Isolate CDE in dedicated namespaces + nodes, minimize scope aggressively |
| Using `cluster-admin` for daily work | Violates principle of least privilege (every framework) | Create role-specific ClusterRoles, reserve cluster-admin for break-glass |
| No evidence collection automation | Auditor asks for data, team scrambles for weeks | Monthly automated evidence-collection CronJob writing to WORM storage |
| Missing data flow diagrams | Auditor cannot understand what data goes where | Maintain current data flow diagrams in architecture docs, regenerated quarterly |
| Compliance labels missing on namespaces | Cannot query which namespaces are in-scope | Label all namespaces consistently: `compliance: hipaa`, `pci-scope: in-scope` |
## Quiz

### Question 1
Your PCI DSS assessor asks: "How do you ensure that only payment workloads run on CDE nodes?" Walk through the Kubernetes controls you would point to and the kubectl commands that produce the evidence.

<details>
<summary>Answer</summary>

Three Kubernetes mechanisms cooperate to enforce CDE node isolation, and you should be able to produce evidence for each.

**Taints and tolerations.** CDE nodes are tainted with `pci-dss=cde:NoSchedule`, so only pods declaring the matching toleration can be scheduled there. Non-payment workloads lack the toleration and the scheduler will refuse to place them. Evidence:

```bash
kubectl get nodes -l node-role.kubernetes.io/pci-cde -o json | \
  jq '.items[].spec.taints'
```

**Node affinity.** Payment Deployments use `requiredDuringSchedulingIgnoredDuringExecution` with a node selector for `node-role.kubernetes.io/pci-cde`, ensuring payment pods are *only* scheduled on CDE nodes and never spill onto general-purpose hardware. Evidence:

```bash
kubectl get pods -n payment-processing -o json | \
  jq '.items[].spec.affinity.nodeAffinity'
```

**Admission control.** A Kyverno policy or validating webhook rejects any pod created in a CDE namespace that lacks the toleration and affinity, which prevents an honest mistake from a developer turning into a PCI scope violation. Evidence:

```bash
kubectl get clusterpolicy require-cde-affinity -o yaml
kubectl get policyreport -n payment-processing
```

The combined story is defense-in-depth: taints prevent general workloads from entering, affinity ensures payment workloads go where they belong, and admission control catches any misconfiguration before it becomes a finding.
</details>

### Question 2
A developer argues that setting the audit policy to `RequestResponse` for the entire cluster is the safest choice for a SOC 2 audit because "we log absolutely everything." Why is this approach fundamentally flawed, and what would you recommend instead?

<details>
<summary>Answer</summary>

The approach is flawed for two compounding reasons.

**Secret exposure.** Logging at `RequestResponse` writes the API request and response bodies to the audit log. For Kubernetes Secrets, the response body contains the base64-encoded secret value. Anyone with read access to the audit log — typically a much wider population than the set of people who can read the secret directly — can decode it. The audit log, which is supposed to be your strongest evidence, becomes your weakest credential store. Auditors who notice this configuration treat it as a finding, not a control.

**Noise and performance degradation.** Logging every health check, every metrics scrape, and every internal controller reconcile at `RequestResponse` generates a volume of events that the API server, the disk, and the downstream pipeline cannot keep up with. The practical failure mode is that the API server starts dropping events under load, which means you have *less* evidence than you would have had with a disciplined policy. The legal failure mode is that even if everything is captured, the relevant events become impossible to find amid the noise, and "we logged it but cannot find it" is treated identically to "we did not log it."

The compliant alternative is surgical: `None` for high-volume non-resource URLs, `Metadata` for most operations including Secrets, and `RequestResponse` only for high-risk interactive verbs like `pods/exec`, `pods/attach`, and RBAC mutations.
</details>

### Question 3
A HIPAA auditor asks for evidence that data is encrypted at rest. The cluster uses etcd with KMS v2, LUKS-encrypted node disks bound to TPM, and Vault Transit for application-level secrets. Walk through what you would actually show them.

<details>
<summary>Answer</summary>

Layered evidence is what an auditor wants, because each layer answers a different threat model.

**Kubernetes Secret encryption (etcd).** Show the `EncryptionConfiguration` file, demonstrate that KMS v2 is the configured provider, and show that the Vault Transit key backing it is itself sealed by the HSM:

```bash
cat /etc/kubernetes/encryption-config.yaml
vault read transit/keys/kubernetes-secrets
vault status | grep "Seal Type"   # Expect "pkcs11"
```

**Disk encryption (LUKS + TPM).** Show that all data volumes appear as `crypto_LUKS`, that the cipher is AES-XTS, and that the volume is sealed to a TPM PCR set so removing the disk renders it unreadable:

```bash
lsblk -f
cryptsetup luksDump /dev/sdb
systemd-cryptenroll /dev/sdb --tpm2-device=auto --dry-run
```

**Application-level encryption.** For databases handling PHI, show the TLS certificate used for the connection and the key-rotation schedule:

```bash
kubectl get secret -n phi-production db-tls \
  -o jsonpath='{.data.tls\.crt}' | base64 -d | \
  openssl x509 -text -noout
```

For the cover note, also document the algorithm and key size for each layer, the rotation policy (Vault Transit auto-rotates, LUKS keys are sealed to TPM), the key-management process (HSM holds the master, Vault manages data keys, no human ever sees a raw key), and a one-page diagram of the envelope-encryption chain. Diagrams are persuasive in a way that command output is not, and an auditor who can hand the diagram to their report-reviewer wins your audit faster.
</details>

### Question 4
Your company processes both payment data (PCI DSS) and healthcare data (HIPAA) on the same Kubernetes cluster. How do you handle overlapping and conflicting compliance requirements, and when would you choose to split into separate clusters?

<details>
<summary>Answer</summary>

The default-correct answer is one cluster with strict namespace isolation, applying the *superset* of controls across the regimes.

Use namespace separation: PCI namespaces such as `payment-processing` and `card-vault`; HIPAA namespaces such as `phi-production`; and a `shared-infra` namespace where both apply. Where the frameworks conflict, apply the stricter control. HIPAA wants six years of audit retention and PCI wants one — apply six. PCI wants quarterly access reviews and SOC 2 wants semi-annual — apply quarterly. Dedicate nodes per domain, taint and label each pool, and reserve general nodes for non-regulated workloads. NetworkPolicies prevent any cross-domain flow that is not through `shared-infra` (monitoring, DNS), and the audit pipeline tags events with framework labels so a single log store can produce per-framework evidence.

You would split into separate clusters when one of three things is true: the regulatory regimes have *technical* requirements that conflict (PCI requires FIPS-validated cryptography that your HIPAA stack does not use), an auditor for one regime refuses to accept logical isolation as sufficient, or the operational risk of a shared incident is too high (a security incident in the PCI namespace freezes all change in the HIPAA namespace because the incident-response process applies cluster-wide). For most organizations the cost of running two clusters — duplicated control planes, duplicated tooling, doubled on-call surface — outweighs the benefit, but the calculation flips at scale.
</details>

### Question 5
You are designing a CronJob that produces monthly SOC 2 evidence and writes it to a MinIO bucket configured with object lock. Your colleague suggests just having the CronJob `kubectl exec` into the operator pod and dump JSON files. Critique this design and propose a better one.

<details>
<summary>Answer</summary>

The proposed design is broken for several compliance-relevant reasons.

First, `kubectl exec` is itself an audit event that fires every month, which adds noise to the very audit log you are trying to keep clean. Worse, the auditor will look at your monthly exec events and ask what they were doing — and "generating evidence" is a circular justification that does not inspire confidence. Second, the CronJob has to run with cluster-wide read access (it is enumerating every namespace), which means a compromise of the CronJob equals a compromise of read-everything credentials. Third, dumping files into the operator pod's filesystem means the evidence lives, even briefly, in a place an attacker can mutate before it is shipped — which breaks the chain-of-custody auditors expect.

A better design uses a dedicated ServiceAccount with the minimum read permissions required (no `secrets` read, for instance — list/get on metadata only), runs the CronJob as a normal pod rather than executing into another pod, signs the output bundle with a key sealed to the cluster's HSM, and writes directly to a MinIO bucket with object lock in compliance mode. The signing step is what turns a tarball into evidence: the tarball plus a signature plus the public key is verifiable by anyone, and an attacker who tampered with the contents would have to also forge the signature, which requires HSM access. The CronJob's RBAC bindings are themselves audit evidence and should appear in your monthly export.
</details>

### Question 6
During a tabletop exercise, the security team simulates a scenario where an attacker compromises a node and gains root. They claim they could now silently delete the on-disk audit log to cover their tracks. Walk through the controls that would defeat this attack in your pipeline, and identify the one weakness that remains.

<details>
<summary>Answer</summary>

The pipeline defends against this attack at four layers, and the residual weakness is real but bounded.

**Layer one: short on-disk retention.** The audit log on the node is a buffer, not the archive. Events are tailed by Fluent Bit within seconds and shipped off the node, so even if the attacker `rm`s the file, the events are already in OpenSearch and on their way to MinIO. The window during which an attacker can affect the archive is the latency between event write and Fluent Bit pickup — typically under a second.

**Layer two: dual output.** Fluent Bit writes to both OpenSearch (search) and MinIO (immutable archive). Compromising the node does not give the attacker access to either downstream store; they would have to compromise the OpenSearch cluster *and* the MinIO cluster *and* their respective credentials.

**Layer three: object lock in compliance mode.** Even if the attacker reaches MinIO with root credentials, objects in a compliance-mode bucket cannot be deleted or modified until the retention period expires — not even by the root user. This is the property that distinguishes WORM compliance from "we have a policy that says don't delete things."

**Layer four: gap detection.** A monitor compares expected event volume to actual event volume and alerts if the gap exceeds five minutes. Even if the attacker successfully suppresses logs from one node, the absence of events from that node is itself a detectable signal.

The residual weakness is the sub-second window between an event being written to disk and being read by Fluent Bit. An attacker who can pause Fluent Bit and rapidly truncate the file before pickup can lose a small number of events. The mitigation is to run Fluent Bit with elevated PID priority and to monitor its liveness independently of the main observability stack — a Fluent Bit that stops shipping should page on-call within sixty seconds, not fifteen minutes.
</details>

### Question 7
Your team rolls out a new Kyverno policy in `Enforce` mode without first running it in `Audit` mode. Within an hour, a critical service deployment fails because the existing manifests do not satisfy the new policy. The on-call engineer disables the policy to restore service. Critique what went wrong, what should have happened, and what the auditor will say at the next review.

<details>
<summary>Answer</summary>

The team made three compounding mistakes that together constitute a process failure auditors take seriously.

The first mistake was deploying directly to enforce. The correct rollout is to deploy with `validationFailureAction: Audit`, watch PolicyReports for at least a week to identify pre-existing violators, fix or whitelist them, then flip to enforce. Skipping the audit phase guarantees that any existing non-compliant workload becomes an outage at the moment the policy lands, and the policy lands at the worst possible time because admission control evaluates on every reconcile loop.

The second mistake was disabling the policy in production rather than rolling back the deployment that introduced it. Disabling a compliance policy creates an unbounded window during which non-compliant resources can be created, and there is no audit trail showing the policy was temporarily off versus permanently broken. The correct response was to roll back the policy resource itself (which is a tracked change in Git) and to flip it back to `Audit` mode while the team investigated.

The third mistake — the one the auditor will care about most — is that the change went to production without being staged, which means change management failed. SOC 2 CC8.1 expects every production change to follow a defined process with documented testing, and "we deployed it straight to enforce" fails that test even if the policy itself was technically correct. The auditor will ask for the change ticket, the staging-environment test results, and the approval record. If those do not exist, the policy rollout itself becomes evidence of a control failure.

The right post-incident actions are a written post-mortem documenting the failure mode, an updated runbook requiring audit-then-enforce for all new policies, and a formal change-management ticket retroactively documenting the rollback. Self-disclosure of the incident in the next audit, paired with the remediation, is far better than silence.
</details>

### Question 8
A new requirement lands: the company is expanding into a jurisdiction whose data sovereignty law forbids any access to customer data by personnel outside the country. You currently operate a single global Kubernetes cluster with on-call engineers spread across three continents. Evaluate the options and recommend an approach.

<details>
<summary>Answer</summary>

The constraint is fundamentally about who can *touch* the data, and the options break down into three buckets.

**Option A: A dedicated in-country cluster operated by in-country staff.** This is the clearest fit for the requirement and the easiest to defend in an audit. The downside is operational cost — you need on-call coverage by in-country personnel around the clock, which for a small team in a small market is expensive. You also need an in-country incident-response process and an in-country evidence-collection pipeline, both of which duplicate machinery you already operate elsewhere.

**Option B: A shared cluster with strict access controls preventing out-of-country administrators from touching the in-country namespaces.** This sounds attractive but has a hidden flaw: cluster administrators (anyone with `cluster-admin`) can always escalate to namespace access. The auditor will not accept "our policy says they will not look" as a control; they will demand a technical control that makes it impossible. The mitigation is to remove cluster-admin from out-of-country staff entirely, which usually fails on operational grounds because the same staff are responsible for cluster upgrades, etcd recovery, and other cluster-wide tasks.

**Option C: Logical separation via a virtual cluster (vcluster) hosted on shared infrastructure but operated by in-country staff.** This is a middle ground that works in some jurisdictions and not others, and the answer depends on whether the regulator considers the underlying host operators to have access to the data. In most strict regimes the answer is yes, which collapses the option back to A.

The recommendation, in most cases, is Option A: a dedicated in-country cluster with in-country staffing and in-country evidence collection. Start with the smallest viable cluster and grow it; the operational overhead is real but the alternative is failing the audit, and the cost of a failed audit usually dwarfs the cost of a small dedicated cluster. Document the decision and the rejected alternatives explicitly so the next platform lead understands why the architecture looks the way it does.
</details>
## Hands-On Exercise: Implement and Verify a Compliance Audit Policy

**Task**: Design and deploy a compliance-grade audit policy on a kind cluster, generate the events an auditor would ask about, and verify your policy captured them with the correct level of detail. This exercise mirrors the worked walkthrough above on a cluster you control end to end.

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
     - level: RequestResponse
       resources:
         - group: "rbac.authorization.k8s.io"
           resources: ["clusterroles","clusterrolebindings","roles","rolebindings"]
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

3. **Generate audit events** that mirror what a real auditor would ask about:

   ```bash
   alias k=kubectl
   k create secret generic test-secret --from-literal=password=s3cret
   k get secret test-secret -o yaml
   k delete secret test-secret
   k run test-pod --image=nginx --restart=Never
   k wait --for=condition=ready pod/test-pod --timeout=60s
   k exec test-pod -- whoami
   k create clusterrolebinding test-binding \
     --clusterrole=view --user=alice@example.com
   k delete clusterrolebinding test-binding
   ```

4. **Verify the audit log captures events at the right level of detail**:

   ```bash
   # Secret events should appear at Metadata level (no value field)
   cat /tmp/audit/logs/audit.log | \
     jq -r 'select(.objectRef.resource=="secrets") |
       "\(.requestReceivedTimestamp) \(.verb) \(.user.username) \(.objectRef.name) level=\(.level)"'

   # Exec events should appear at RequestResponse with the command body
   cat /tmp/audit/logs/audit.log | \
     jq 'select(.objectRef.subresource=="exec") | {ts:.requestReceivedTimestamp, user:.user.username, cmd:.requestObject.command}'

   # RBAC mutations should appear at RequestResponse with the role body
   cat /tmp/audit/logs/audit.log | \
     jq 'select(.objectRef.resource=="clusterrolebindings") | {ts:.requestReceivedTimestamp, verb:.verb, name:.objectRef.name, level:.level}'

   # Health checks should produce no events
   grep -c '/healthz' /tmp/audit/logs/audit.log
   ```

5. **Stretch goal — install Kyverno and demonstrate a PolicyReport** for the `require-drop-all-capabilities` policy from the policy-as-code section. Apply a non-compliant pod, observe the rejection, apply a compliant pod, and `k get policyreport -A` to confirm the pass appears in the report.

<details>
<summary>Solution notes and expected evidence</summary>

The secret read should create an audit event at `Metadata` level, which means the log proves access without copying the secret value into the evidence store. If you see a `responseObject` containing secret data, the policy is too verbose and must be fixed before the cluster handles regulated workloads. The `exec` event should show the `whoami` command in the request object, because interactive access is one of the highest-value audit trails during an investigation.

For RBAC, expect create and delete events for `test-binding` at `RequestResponse` level. That detail lets an auditor reconstruct not only that privileges changed, but which role was granted and to whom. The `/healthz` check should return zero matches because health probes add volume without answering a compliance question. If Kyverno is installed for the stretch goal, the non-compliant pod should be rejected before scheduling and the compliant pod should contribute a passing entry to the PolicyReport.

</details>

### Success Criteria

- [ ] Audit policy deployed alongside the kind cluster
- [ ] Secret create, read, and delete events present in the log at `Metadata` level (verify the `level` field reads `Metadata` and there is no `responseObject` for the get)
- [ ] Pod exec event present at `RequestResponse` level with the command (`whoami`) visible in `requestObject.command`
- [ ] ClusterRoleBinding create and delete events present at `RequestResponse` level with the binding body recorded
- [ ] No audit events for `/healthz` (the health-check `grep -c` returns zero)
- [ ] All audit lines parseable with `jq` (no malformed JSON)
- [ ] Stretch: non-compliant pod rejected at admission and a passing PolicyReport entry exists for the compliant pod

## Key Takeaways

1. **Compliance is about evidence, not just security.** You must prove controls exist, were operating during the audit window, and were monitored for drift. A perfectly secure cluster with no evidence trail will fail an audit a less secure cluster with good evidence will pass.
2. **Design audit policy before the auditor arrives.** Retrofitting logging is expensive and painful, and every event you missed during the audit window is unrecoverable. A surgical policy that captures what regulators care about is dramatically more valuable than a "log everything" policy that drowns the API server.
3. **Minimize PCI DSS scope aggressively.** Fewer in-scope namespaces means less audit surface, lower assessor cost, and faster change windows for non-CDE workloads. Scope minimization is a one-time architectural decision with annually-recurring savings.
4. **Ship audit logs to tamper-evident storage.** WORM storage with object lock in compliance mode is the only configuration that defeats a compromised-administrator threat model, and it is the only configuration auditors will accept for HIPAA and PCI evidence.
5. **Automate evidence collection.** Monthly automated CronJobs that produce signed evidence bundles transform audit prep from a multi-week scramble into a one-day exercise of "hand the auditor the bucket." The discipline that distinguishes mature programs is that the evidence is always older than the audit.
6. **Use policy-as-code to convert compliance from a quarterly project into a continuous control.** Kyverno PolicyReports are evidence that maps directly to assessor questions; once you have them, the audit conversation is about reading reports rather than running ad-hoc kubectl queries.

## Sources

- [Kubernetes audit logging](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [Kubernetes audit policy reference](https://kubernetes.io/docs/reference/config-api/apiserver-audit.v1/)
- [Kubernetes NetworkPolicy concepts](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes encrypting confidential data at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Kyverno PolicyReports](https://kyverno.io/docs/policy-reports/)
- [Kyverno validate rules](https://kyverno.io/docs/policy-types/cluster-policy/validate/)
- [Fluent Bit S3 output plugin](https://docs.fluentbit.io/manual/pipeline/outputs/s3)
- [MinIO object retention and object lock](https://min.io/docs/minio/linux/administration/object-management/object-retention.html)
- [HIPAA Security Rule, 45 CFR Part 164 Subpart C](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C)
- [PCI Security Standards Council document library](https://www.pcisecuritystandards.org/standards/)
- [GDPR Regulation (EU) 2016/679 official text](https://eur-lex.europa.eu/eli/reg/2016/679/oj)

## Next Module

Continue to [Module 7.1: Cluster Upgrades & Lifecycle](/on-premises/operations/module-7.1-upgrades/) to learn how to manage Kubernetes version upgrades, OS patching, and firmware updates in on-premises environments without violating the change-management controls you have just built.
