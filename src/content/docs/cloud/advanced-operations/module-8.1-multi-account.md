---
title: "Module 8.1: Multi-Account Architecture & Org Design"
slug: cloud/advanced-operations/module-8.1-multi-account
sidebar:
  order: 2
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 2.5 hours
>
> **Prerequisites**: [Cloud Architecture Patterns](../architecture-patterns/), familiarity with at least one hyperscaler (AWS, GCP, or Azure)
>
> **Track**: Advanced Cloud Operations

---

## Why This Module Matters

**March 2019. A mid-sized fintech company. 42 engineers. One AWS account.**

Everything lived together: production databases, staging environments, CI/CD pipelines, developer sandboxes, and the shared services that glued it all together. One Friday afternoon, a junior developer running load tests in what they believed was a staging environment accidentally saturated the NAT Gateway that production traffic also depended on. Payment processing halted for 93 minutes. The incident cost $2.1 million in failed transactions and triggered a PCI-DSS audit that consumed two months of engineering time.

The root cause was not the load test. It was the architecture -- or rather, the lack of it. When everything lives in a single account, there are no blast radius boundaries. IAM policies become impossibly complex. Cost attribution is guesswork. Audit trails are a tangled mess of production and development activity. And one mistake in any environment can cascade into every other.

This module teaches you how to design multi-account architectures across AWS, GCP, and Azure. You will learn to build organizational hierarchies that enforce isolation by default, centralize what should be shared (logging, security, networking), and keep what should be separate truly separate. More importantly, you will understand how these decisions directly impact your Kubernetes clusters -- where they live, how they communicate, and who controls their lifecycle.

---

## The Single-Account Trap

Before we design multi-account architectures, let's understand why teams end up in single-account messes. The pattern is always the same:

1. Start a project. Create one account. Deploy everything.
2. Grow the team. Add more workloads. Still one account.
3. Need staging. Create a namespace or tag. Still one account.
4. Need compliance. Realize IAM policies are spaghetti. Panic.

The single-account model works for a solo developer building a side project. It stops working the moment you need any of these: environment isolation, cost visibility, compliance boundaries, or team autonomy.

```
SINGLE-ACCOUNT ANTI-PATTERN
════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────┐
    │              AWS Account: 123456789012               │
    │                                                     │
    │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
    │  │   Prod    │  │  Staging │  │   Dev Sandbox    │  │
    │  │  EKS +    │  │  EKS +   │  │  Random EC2s +   │  │
    │  │  RDS +    │  │  RDS +   │  │  Load tests +    │  │
    │  │  S3       │  │  S3      │  │  Experiments     │  │
    │  └──────────┘  └──────────┘  └──────────────────┘  │
    │                                                     │
    │  Shared: VPC, NAT GW, IAM roles, CloudTrail        │
    │  Result: One blast radius. One bill. One nightmare. │
    └─────────────────────────────────────────────────────┘

    Problems:
    - Dev load test saturates prod NAT Gateway
    - IAM role for staging accidentally gets prod DB access
    - Cost report says "$84,000 this month" but WHO spent it?
    - CloudTrail logs mix dev experiments with prod audit events
```

The multi-account model solves all of these by creating hard boundaries. An AWS account, a GCP project, or an Azure subscription is the strongest isolation boundary each cloud offers below the organization level.

---

## Organizational Hierarchies Across Clouds

Every hyperscaler provides a hierarchy for organizing accounts. The terminology differs, but the concept is the same: nest accounts inside groupings that inherit policies downward.

### The Rosetta Stone of Cloud Organization

```
ORGANIZATIONAL HIERARCHY COMPARISON
════════════════════════════════════════════════════════════════

AWS                    GCP                    Azure
───────────────────    ───────────────────    ───────────────────
Organization           Organization           Tenant (Entra ID)
  │                      │                      │
  ├─ Root OU             ├─ Folder              ├─ Management Group
  │   │                  │   │                  │   │
  │   ├─ OU              │   ├─ Folder          │   ├─ Management Group
  │   │   │              │   │   │              │   │   │
  │   │   ├─ Account     │   │   ├─ Project     │   │   ├─ Subscription
  │   │   └─ Account     │   │   └─ Project     │   │   └─ Subscription
  │   │                  │   │                  │   │
  │   └─ OU              │   └─ Folder          │   └─ Management Group
  │       │              │       │              │       │
  │       └─ Account     │       └─ Project     │       └─ Subscription
  │                      │                      │
  └─ Root OU             └─ Folder              └─ Management Group

Policy Mechanism:      Policy Mechanism:      Policy Mechanism:
  Service Control        Organization           Azure Policy
  Policies (SCPs)        Policies               (assigned at MG level)
  Inherited downward     Inherited downward     Inherited downward
```

### Key Differences That Matter

| Feature | AWS (Organizations) | GCP (Resource Manager) | Azure (Management Groups) |
|---|---|---|---|
| Isolation unit | Account | Project | Subscription |
| Max nesting depth | 5 levels of OUs | 10 levels of folders | 6 levels of MGs |
| Policy mechanism | SCPs (deny-only) | Org Policies (boolean/list) | Azure Policy (deny + audit) |
| Billing boundary | Account-level | Project-level or Billing Account | Subscription-level |
| Hard resource limits | Per-account quotas | Per-project quotas | Per-subscription quotas |
| Cross-boundary networking | VPC Peering, Transit GW | Shared VPC, VPC Peering | VNet Peering, Virtual WAN |

One critical nuance: AWS SCPs can only deny -- they cannot grant permissions. This means your SCP strategy is about guardrails, not access grants. GCP Organization Policies work differently: they constrain resource configurations (e.g., "VMs can only be created in these regions"). Azure Policy can both deny and audit, making it the most flexible but also the most complex to reason about.

---

## Designing Your OU Structure

The organizational unit (OU) structure is the skeleton of your cloud architecture. Get it wrong, and you will fight it for years. Get it right, and it becomes invisible -- quietly enforcing isolation, compliance, and cost boundaries.

### The Reference Architecture

Here is a battle-tested OU structure used by organizations running 20-200 AWS accounts. The same pattern maps to GCP folders and Azure management groups.

```
RECOMMENDED OU STRUCTURE
════════════════════════════════════════════════════════════════

Root
├── Security OU
│   ├── Log Archive Account          (centralized logging)
│   ├── Security Tooling Account     (GuardDuty, SecurityHub)
│   └── Audit Account                (read-only cross-account)
│
├── Infrastructure OU
│   ├── Network Hub Account          (Transit Gateway, DNS)
│   ├── Shared Services Account      (CI/CD, artifact registries)
│   └── Identity Account             (SSO, directory services)
│
├── Workloads OU
│   ├── Production OU
│   │   ├── Team-A Prod Account      (EKS cluster + workloads)
│   │   ├── Team-B Prod Account      (EKS cluster + workloads)
│   │   └── Data Platform Prod       (analytics + ML)
│   │
│   ├── Staging OU
│   │   ├── Team-A Staging Account
│   │   └── Team-B Staging Account
│   │
│   └── Development OU
│       ├── Team-A Dev Account
│       └── Team-B Dev Account
│
├── Sandbox OU
│   ├── Developer-1 Sandbox
│   └── Developer-2 Sandbox
│
└── Suspended OU                     (decommissioned accounts)
```

### Why This Structure Works

**Security OU at the top**: Security accounts have the most restrictive SCPs. The Log Archive account is write-only for other accounts and read-only for security teams. No one can delete CloudTrail logs. No one can disable GuardDuty findings.

**Infrastructure OU is separate from Workloads**: The networking team manages Transit Gateways and DNS without needing access to application workloads. The CI/CD pipeline runs in a shared services account, pushing artifacts that workload accounts pull.

**Workloads OU splits by environment, not team**: This is critical. If you split by team first, you end up with Team-A-Prod, Team-A-Staging, Team-A-Dev all in one OU. This makes it impossible to apply environment-specific policies (like "production accounts cannot have public S3 buckets") without per-account exceptions.

**Sandbox OU has aggressive cost controls**: Sandbox accounts get auto-nuke policies (using tools like aws-nuke) that clean up resources older than 72 hours. Budget alarms fire at $50/month. This gives developers freedom to experiment without burning money.

### Setting Up AWS Organizations

```bash
# Create the organization (from management account)
aws organizations create-organization --feature-set ALL

# Create the OU structure
ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)

# Create top-level OUs
SECURITY_OU=$(aws organizations create-organizational-unit \
  --parent-id $ROOT_ID \
  --name "Security" \
  --query 'OrganizationalUnit.Id' --output text)

INFRA_OU=$(aws organizations create-organizational-unit \
  --parent-id $ROOT_ID \
  --name "Infrastructure" \
  --query 'OrganizationalUnit.Id' --output text)

WORKLOADS_OU=$(aws organizations create-organizational-unit \
  --parent-id $ROOT_ID \
  --name "Workloads" \
  --query 'OrganizationalUnit.Id' --output text)

# Create environment sub-OUs under Workloads
PROD_OU=$(aws organizations create-organizational-unit \
  --parent-id $WORKLOADS_OU \
  --name "Production" \
  --query 'OrganizationalUnit.Id' --output text)

STAGING_OU=$(aws organizations create-organizational-unit \
  --parent-id $WORKLOADS_OU \
  --name "Staging" \
  --query 'OrganizationalUnit.Id' --output text)

DEV_OU=$(aws organizations create-organizational-unit \
  --parent-id $WORKLOADS_OU \
  --name "Development" \
  --query 'OrganizationalUnit.Id' --output text)

# Create a new account and move it to the Production OU
aws organizations create-account \
  --email "team-a-prod@company.com" \
  --account-name "Team-A-Production"

# Move account to Production OU (once created)
aws organizations move-account \
  --account-id 111122223333 \
  --source-parent-id $ROOT_ID \
  --destination-parent-id $PROD_OU
```

### GCP Equivalent with Folders

```bash
# Create folder structure
ORG_ID=$(gcloud organizations list --format="value(ID)")

# Create top-level folders
gcloud resource-manager folders create \
  --display-name="Security" \
  --organization=$ORG_ID

gcloud resource-manager folders create \
  --display-name="Infrastructure" \
  --organization=$ORG_ID

WORKLOADS_FOLDER=$(gcloud resource-manager folders create \
  --display-name="Workloads" \
  --organization=$ORG_ID \
  --format="value(name)")

# Create environment sub-folders
gcloud resource-manager folders create \
  --display-name="Production" \
  --folder=$WORKLOADS_FOLDER

gcloud resource-manager folders create \
  --display-name="Staging" \
  --folder=$WORKLOADS_FOLDER

# Create a project in the Production folder
gcloud projects create team-a-prod-2026 \
  --folder=$PROD_FOLDER_ID \
  --name="Team A Production"
```

---

## Workload Isolation Patterns

Not every team needs its own account. And not every workload needs its own cluster. The art is matching isolation level to actual requirements.

### Isolation Decision Matrix

| Requirement | Same Account, Same Cluster | Same Account, Separate Clusters | Separate Accounts |
|---|---|---|---|
| Team autonomy | Low (shared RBAC) | Medium (cluster admin) | High (account admin) |
| Blast radius | Pod/Namespace level | Cluster level | Account level |
| Compliance boundary | Cannot achieve PCI/HIPAA | Possible with effort | Clean boundary |
| Cost visibility | Tags only | Tags + cluster | Account-level billing |
| Network isolation | NetworkPolicy | VPC/subnet separation | VPC per account |
| Resource contention | High risk | Medium risk | Zero risk |
| Operational overhead | Low | Medium | High |

### The War Story: When Namespace Isolation Isn't Enough

A healthcare company ran production workloads in a single EKS cluster, using namespaces for isolation between teams. Their compliance team signed off because NetworkPolicies were in place. Then during a PCI audit, the auditor asked: "Can a pod in namespace `team-b` read the Kubernetes API and discover that namespace `team-a-pci` exists?" The answer was yes. `kubectl get namespaces` works for any authenticated service account by default. The auditor flagged it as a data leakage risk -- not because data was exposed, but because the existence of a PCI workload was discoverable.

The fix required separate clusters. But by then, 14 teams had built tooling assuming a single cluster. The migration took five months.

Lesson: decide your isolation boundaries before you have tenants, not after.

### Kubernetes Lifecycle in a Multi-Account World

Each account that runs Kubernetes clusters needs a clear lifecycle model:

```
K8S CLUSTER LIFECYCLE PER ACCOUNT
════════════════════════════════════════════════════════════════

Shared Services Account              Workload Account (Team-A Prod)
┌────────────────────────┐           ┌────────────────────────────┐
│                        │           │                            │
│  Terraform/Crossplane  │──creates──▶  EKS/GKE/AKS Cluster     │
│  (IaC source of truth) │           │                            │
│                        │           │  ┌──────────────────────┐  │
│  ArgoCD / Flux         │──deploys──▶  │  Workloads           │  │
│  (GitOps controller)   │           │  │  - app deployments   │  │
│                        │           │  │  - ingress configs   │  │
│  ECR / Artifact Reg    │──images───▶  │  - secrets (ESO)     │  │
│  (shared registry)     │           │  └──────────────────────┘  │
│                        │           │                            │
│  Central Logging       │◀──logs────│  Fluentbit / OTel agent   │
│  (Log Archive account) │           │                            │
└────────────────────────┘           └────────────────────────────┘

Key principle: Clusters are CATTLE, not pets.
The IaC in Shared Services can recreate any cluster from scratch.
```

The critical decision is whether each team manages their own cluster infrastructure or whether a platform team provisions clusters centrally. Most organizations that scale past five teams find that central provisioning with team-owned workload deployment strikes the best balance.

---

## Centralized Logging & Audit

In a multi-account world, logging becomes both more important and more complex. You need a single pane of glass for security events, but you also need to ensure that no individual account can tamper with its own logs.

### The Immutable Log Archive Pattern

```
CENTRALIZED LOGGING ARCHITECTURE
════════════════════════════════════════════════════════════════

  Workload Account A          Workload Account B
  ┌───────────────────┐       ┌───────────────────┐
  │ CloudTrail ──────────────────────────────────────┐
  │ VPC Flow Logs ───────────────────────────────────┤
  │ EKS Audit Logs ──────────────────────────────────┤
  └───────────────────┘       └───────────────────┘  │
                                                      │
                                                      ▼
                              Log Archive Account (Security OU)
                              ┌──────────────────────────────┐
                              │  S3 Bucket (Object Lock)     │
                              │  - Governance mode: 1 year   │
                              │  - No delete, even by root   │
                              │                              │
                              │  Athena / OpenSearch for     │
                              │  query and investigation     │
                              │                              │
                              │  SCP prevents:               │
                              │  - Disabling CloudTrail      │
                              │  - Deleting log buckets      │
                              │  - Modifying Object Lock     │
                              └──────────────────────────────┘
```

### AWS: Organization-Wide CloudTrail

```bash
# Create organization trail (from management account)
aws cloudtrail create-trail \
  --name org-trail \
  --s3-bucket-name company-org-cloudtrail-logs \
  --is-organization-trail \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --kms-key-id arn:aws:kms:us-east-1:999888777666:key/mrk-abc123

aws cloudtrail start-logging --name org-trail

# SCP to prevent member accounts from disabling CloudTrail
cat <<'EOF' > deny-cloudtrail-changes.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ProtectCloudTrail",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "cloudtrail:UpdateTrail"
      ],
      "Resource": "arn:aws:cloudtrail:*:*:trail/org-trail"
    }
  ]
}
EOF

aws organizations create-policy \
  --name "ProtectCloudTrail" \
  --description "Prevent member accounts from disabling org CloudTrail" \
  --type SERVICE_CONTROL_POLICY \
  --content file://deny-cloudtrail-changes.json

# Attach SCP to the root (applies to ALL accounts)
aws organizations attach-policy \
  --policy-id p-1234567890 \
  --target-id $ROOT_ID
```

### GCP: Organization-Level Log Sinks

```bash
# Create organization-level log sink
gcloud logging sinks create org-audit-sink \
  storage.googleapis.com/company-org-audit-logs \
  --organization=$ORG_ID \
  --include-children \
  --log-filter='logName:"cloudaudit.googleapis.com"'

# Grant the sink's service account write access to the bucket
# (The sink creates a unique service account automatically)
SINK_SA=$(gcloud logging sinks describe org-audit-sink \
  --organization=$ORG_ID \
  --format="value(writerIdentity)")

gsutil iam ch $SINK_SA:objectCreator gs://company-org-audit-logs
```

### EKS Audit Logs to Central Logging

Kubernetes audit logs are separate from cloud-level audit trails. You need both.

```yaml
# Fluentbit ConfigMap to ship EKS audit logs to central account
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Tag               kube.audit.*
        Path              /var/log/kubernetes/audit/*.log
        Parser            json
        Refresh_Interval  10
        Mem_Buf_Limit     50MB

    [OUTPUT]
        Name              s3
        Match             kube.audit.*
        bucket            central-audit-logs-cross-account
        region            us-east-1
        role_arn          arn:aws:iam::999888777666:role/audit-log-writer
        total_file_size   50M
        upload_timeout    60s
        s3_key_format     /eks-audit/$TAG/%Y/%m/%d/%H/$UUID.gz
        compression       gzip
```

---

## Shared Services: What to Centralize

Not everything should be isolated. Some resources are natural shared services that benefit from centralization. The challenge is identifying which ones and building the right access patterns.

### Centralize vs. Distribute Decision Framework

| Resource | Centralize | Distribute | Reasoning |
|---|---|---|---|
| Container registry | Yes | | One source of truth for images, scan once |
| CI/CD pipelines | Yes | | Consistent build process, shared runners |
| DNS management | Yes | | Single delegation, avoid split-brain |
| Secrets management | Hybrid | Hybrid | Central vault, local caching (ESO pattern) |
| Service mesh control | Depends | Depends | Centralize if cross-cluster, distribute if single |
| Monitoring stack | Yes | | Unified dashboards, correlation across clusters |
| Cluster provisioning (IaC) | Yes | | Consistent configs, version control |
| Application deployment | | Yes | Teams own their deploy cadence |

### The Shared VPC Pattern (GCP)

GCP's Shared VPC is one of the cleanest implementations of centralized networking. A host project owns the VPC, and service projects attach to it.

```bash
# Enable Shared VPC in the host project (network hub)
gcloud compute shared-vpc enable network-hub-project

# Associate a service project (workload account)
gcloud compute shared-vpc associated-projects add team-a-prod \
  --host-project=network-hub-project

# Grant the service project's GKE service account access to the shared subnet
gcloud projects add-iam-policy-binding network-hub-project \
  --member="serviceAccount:service-TEAM_A_PROJECT_NUM@container-engine-robot.iam.gserviceaccount.com" \
  --role="roles/container.hostServiceAgentUser"

# Create a GKE cluster in the service project using the shared VPC
gcloud container clusters create team-a-prod \
  --project=team-a-prod \
  --network=projects/network-hub-project/global/networks/shared-vpc \
  --subnetwork=projects/network-hub-project/regions/us-central1/subnetworks/team-a-subnet \
  --cluster-secondary-range-name=pods \
  --services-secondary-range-name=services
```

This gives you centralized network management (firewall rules, routes, IP allocation) while letting each team own their cluster and workloads. The networking team sees all traffic flows. The application team sees only their project.

---

## Hierarchical Billing & Cost Allocation

Multi-account architecture gives you the most accurate cost attribution possible -- costs are naturally isolated to the account that incurred them.

### AWS: Consolidated Billing with Cost Allocation Tags

```bash
# Enable cost allocation tags at the organization level
aws ce update-cost-allocation-tags-status \
  --cost-allocation-tags-status \
    TagKey=Environment,Status=Active \
    TagKey=Team,Status=Active \
    TagKey=CostCenter,Status=Active

# Create a budget per workload account
aws budgets create-budget \
  --account-id 111122223333 \
  --budget '{
    "BudgetName": "team-a-prod-monthly",
    "BudgetLimit": {"Amount": "15000", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [
        {"SubscriptionType": "EMAIL", "Address": "team-a-lead@company.com"},
        {"SubscriptionType": "SNS", "Address": "arn:aws:sns:us-east-1:111122223333:budget-alerts"}
      ]
    }
  ]'
```

### Cost Hierarchy Visualization

```
HIERARCHICAL BILLING STRUCTURE
════════════════════════════════════════════════════════════════

Organization Payer Account
├── Security OU ────────────────── $2,100/month
│   ├── Log Archive ──── $1,400   (S3 storage, Athena queries)
│   ├── Security Tools ── $500    (GuardDuty, SecurityHub)
│   └── Audit ─────────── $200    (read-only access tooling)
│
├── Infrastructure OU ──────────── $8,300/month
│   ├── Network Hub ───── $3,200  (Transit GW, NAT GWs, DNS)
│   ├── Shared Services ─ $4,100  (CI/CD runners, ECR, ArgoCD)
│   └── Identity ──────── $1,000  (SSO, directory sync)
│
├── Workloads OU ───────────────── $63,500/month
│   ├── Production OU ── $48,000
│   │   ├── Team-A ───── $22,000  (3 EKS clusters, RDS, ElastiCache)
│   │   ├── Team-B ───── $18,000  (2 EKS clusters, DynamoDB)
│   │   └── Data ──────── $8,000  (EMR, Redshift)
│   ├── Staging OU ────── $9,500
│   └── Development OU ── $6,000
│
└── Sandbox OU ─────────────────── $1,200/month
                                   ─────────
                          Total:  $75,100/month

With single-account: "$75,100 — but we have no idea where it goes"
With multi-account:  Per-team, per-environment breakdown by default
```

### Pro tip: Tagging standards across accounts

Even with multi-account, you still need consistent tags for cross-cutting views. Define a tagging policy at the organization level.

```bash
# AWS: Create a tag policy (enforced via Organizations)
cat <<'EOF' > tag-policy.json
{
  "tags": {
    "Environment": {
      "tag_key": {"@@assign": "Environment"},
      "tag_value": {"@@assign": ["production", "staging", "development", "sandbox"]},
      "enforced_for": {"@@assign": ["ec2:instance", "eks:cluster", "rds:db"]}
    },
    "Team": {
      "tag_key": {"@@assign": "Team"},
      "enforced_for": {"@@assign": ["ec2:instance", "eks:cluster"]}
    },
    "CostCenter": {
      "tag_key": {"@@assign": "CostCenter"},
      "enforced_for": {"@@assign": ["ec2:instance", "eks:cluster", "rds:db", "s3:bucket"]}
    }
  }
}
EOF

aws organizations create-policy \
  --name "RequiredTags" \
  --type TAG_POLICY \
  --content file://tag-policy.json

aws organizations attach-policy \
  --policy-id p-tag12345 \
  --target-id $WORKLOADS_OU
```

---

## Did You Know?

1. **AWS Control Tower can provision a landing zone in under 60 minutes** that creates your management account, log archive account, audit account, and baseline SCPs. What used to take weeks of manual setup is now a wizard. GCP has a similar concept called "Fabric FAST" and Azure has "Enterprise-Scale Landing Zones" -- all three try to codify the multi-account best practices described in this module.

2. **GCP projects have a soft limit of 30 projects per billing account** but this can be raised to thousands. The real constraint is that every project gets its own set of quotas (API calls, resource limits), which means you sometimes need to spread workloads across projects to avoid hitting per-project ceilings -- not for organizational reasons, but for capacity.

3. **The AWS "Root" account email is the most powerful credential in your organization** and cannot be protected by SCPs. If someone compromises the root email address of your management account, they control your entire organization. Best practice: use a distribution list email (not a personal inbox), enable MFA with a hardware token, and store the credentials in a physical safe. This is not hyperbole.

4. **Azure Management Groups support "deny assignments"** that are even stronger than role assignments. A deny assignment at a management group level prevents any user, even Owner, from performing specific actions on resources below. This is how Azure enforces compliance for regulated industries -- the hierarchy physically prevents non-compliant configurations.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Organizing OUs by team instead of environment | Feels natural to team ownership | Structure by environment first, team second. Apply environment policies at the OU level. |
| Running everything in the management/payer account | "It's the first account, might as well use it" | Management account should run NOTHING except billing and organization management. Zero workloads. |
| Not creating a Suspended OU | Forgot about account decommissioning | Create a Suspended OU with SCPs that deny all actions. Move decommissioned accounts here instead of closing them (closing has a 90-day reopen window). |
| Sharing VPCs across environments | Trying to save on NAT Gateway costs | Separate VPCs per environment. The $30/month NAT Gateway savings is not worth the blast radius. |
| Manual account creation | "We only need a few accounts" | Automate with Account Factory (Control Tower), Terraform, or Crossplane from day one. Even if you only have three accounts. |
| Forgetting centralized DNS | Each account creates its own hosted zone | Create a central DNS account with Route53/Cloud DNS. Delegate subdomains to workload accounts via NS records. |
| No SCP/policy guardrails on day one | "We'll add governance later" | Apply baseline SCPs immediately: deny disabling CloudTrail, deny leaving the organization, restrict regions. |
| One IAM Identity Center permission set for all environments | "Admin is admin" | Create separate permission sets for prod (read-only default, break-glass for write) vs dev (broader access). |

---

## Quiz

<details>
<summary>1. Why should the management/payer account in AWS Organizations run zero workloads?</summary>

The management account is exempt from Service Control Policies (SCPs). SCPs cannot restrict the management account -- they only apply to member accounts. This means any workload running in the management account operates without the guardrails you've carefully built. Additionally, the management account has implicit access to billing data and organization-wide settings. Running workloads there unnecessarily expands the attack surface of your most privileged account. Keep it clean: billing, organization management, and nothing else.
</details>

<details>
<summary>2. What is the difference between AWS SCPs and GCP Organization Policies?</summary>

AWS SCPs function as permission boundaries -- they can only deny actions, never grant them. They filter what IAM policies can do. If an SCP denies `s3:DeleteBucket`, no IAM policy in that account can delete buckets, even if the policy explicitly allows it. GCP Organization Policies are different: they constrain resource configurations rather than API actions. For example, a GCP org policy can say "VMs can only be created in us-central1 and europe-west1" or "external IP addresses are not allowed on VMs." They're complementary concepts, not direct equivalents.
</details>

<details>
<summary>3. A company has 8 teams, each running 2 EKS clusters (prod and staging). Should they use 8 accounts or 16?</summary>

Use 16 accounts: one per team per environment. This gives you clean environment isolation (SCPs that apply to all prod accounts vs all staging accounts), per-team cost attribution at the account level, and separate IAM boundaries between prod and staging. With 8 accounts (one per team, both environments inside), you lose the ability to apply environment-wide policies and developers with staging access could accidentally touch production resources in the same account. The operational overhead of 16 vs 8 is negligible when using automated account provisioning (Account Factory, Terraform).
</details>

<details>
<summary>4. Why would you centralize your container registry in a shared services account rather than having one per workload account?</summary>

Centralizing the container registry provides several benefits: images are scanned once (not per-account), a single source of truth eliminates image sprawl and version confusion, cross-account pull is straightforward with ECR resource policies or Artifact Registry IAM, and you avoid paying storage costs for duplicate images across accounts. The shared services account also becomes the natural place for your CI/CD pipeline to push images after building them, creating a clean "build once, deploy many" flow.
</details>

<details>
<summary>5. What happens if you close an AWS account that still has resources in it?</summary>

When you close an AWS account, it enters a 90-day suspended state during which it can be reopened. During this period, resources continue to exist but are inaccessible. After 90 days, the account is permanently closed and AWS begins deleting resources. However, some resources (like S3 buckets with object lock, or Route53 hosted zones with delegated DNS) may not be cleaned up automatically. This is why the best practice is to move accounts to a Suspended OU (which denies all actions) and manually clean up resources before initiating account closure. Never close accounts with active DNS delegations or encrypted data you might need.
</details>

<details>
<summary>6. How does GCP Shared VPC differ from AWS VPC Peering for multi-account networking?</summary>

GCP Shared VPC is a centralized model: a host project owns the VPC and shares subnets with service projects. Service projects create resources (like GKE clusters) directly in the shared subnets. There is one VPC, one set of firewall rules, one routing table. AWS VPC Peering is a distributed model: each account has its own VPC, and peering connections create point-to-point links between them. Each VPC maintains its own route tables and security groups. Shared VPC is simpler to manage at scale but gives less network-level isolation. VPC Peering gives more isolation but creates an N-squared peering complexity problem as accounts grow (which is why AWS Transit Gateway exists).
</details>

<details>
<summary>7. Why should sandbox accounts have automated resource cleanup (aws-nuke or similar)?</summary>

Developers in sandbox accounts experiment freely, which is the whole point. But experiments leave behind resources: EC2 instances running overnight, EBS volumes, load balancers, NAT gateways. Without cleanup, sandbox costs grow linearly with the number of developers and eventually rival staging costs. Automated cleanup (wiping resources older than 48-72 hours) keeps sandbox costs predictable, removes the guilt barrier to experimentation ("I better not spin up that cluster, it'll cost money"), and prevents forgotten resources from becoming security risks (unpatched instances, exposed services).
</details>

---

## Hands-On Exercise: Design a Multi-Account Architecture

In this exercise, you will design and partially implement a multi-account architecture for a fictional company.

### Scenario

**Company**: CloudBrew (a SaaS analytics platform)
- 6 engineering teams
- 3 environments: production, staging, development
- Compliance requirement: SOC2 Type II (audit logs must be immutable for 1 year)
- Budget: team-level cost attribution required for quarterly planning
- Kubernetes: each team runs 1-2 EKS clusters per environment

### Task 1: Draw the OU Structure

Design the OU hierarchy for CloudBrew. Include all accounts, organized by OU.

<details>
<summary>Solution</summary>

```
Root
├── Security OU
│   ├── log-archive (immutable S3, 1-year retention for SOC2)
│   ├── security-tooling (GuardDuty, SecurityHub, Inspector)
│   └── audit-readonly (auditor access, no write permissions)
│
├── Infrastructure OU
│   ├── network-hub (Transit Gateway, central DNS, NAT)
│   ├── shared-services (CI/CD, ECR, ArgoCD management)
│   └── identity (IAM Identity Center, Okta/Entra connector)
│
├── Workloads OU
│   ├── Production OU (SCP: no public S3, no IMDSv1, no large instances w/o approval)
│   │   ├── analytics-prod
│   │   ├── ingestion-prod
│   │   ├── api-prod
│   │   ├── ml-prod
│   │   ├── frontend-prod
│   │   └── data-prod
│   ├── Staging OU (SCP: relaxed, but still no public S3)
│   │   └── (mirror of prod accounts)
│   └── Development OU (SCP: region-restricted, instance-size limited)
│       └── (mirror of prod accounts)
│
├── Sandbox OU (SCP: 72hr auto-nuke, $100/month budget, restricted regions)
│   └── (one per developer, auto-provisioned)
│
└── Suspended OU (SCP: deny all)
```

Total accounts: 3 (security) + 3 (infra) + 18 (workloads: 6 teams x 3 envs) + N (sandboxes) = 24 + sandboxes
</details>

### Task 2: Write the Baseline SCP

Write an SCP that should apply to ALL member accounts (attached at the root).

<details>
<summary>Solution</summary>

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyCloudTrailTampering",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "cloudtrail:UpdateTrail"
      ],
      "Resource": "arn:aws:cloudtrail:*:*:trail/org-trail"
    },
    {
      "Sid": "DenyLeavingOrganization",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    },
    {
      "Sid": "DenyDisablingGuardDuty",
      "Effect": "Deny",
      "Action": [
        "guardduty:DeleteDetector",
        "guardduty:DisassociateFromMasterAccount",
        "guardduty:UpdateDetector"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RestrictToAllowedRegions",
      "Effect": "Deny",
      "NotAction": [
        "iam:*",
        "organizations:*",
        "sts:*",
        "support:*",
        "billing:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "us-east-1",
            "us-west-2",
            "eu-west-1"
          ]
        }
      }
    }
  ]
}
```
</details>

### Task 3: Configure Cross-Account ECR Access

Write the ECR repository policy that allows all workload accounts to pull images from the shared services account's ECR.

<details>
<summary>Solution</summary>

```bash
# In the shared-services account, set the ECR repository policy
aws ecr set-repository-policy \
  --repository-name company/api-service \
  --policy-text '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowWorkloadAccountsPull",
        "Effect": "Allow",
        "Principal": {
          "AWS": [
            "arn:aws:iam::111111111111:root",
            "arn:aws:iam::222222222222:root",
            "arn:aws:iam::333333333333:root"
          ]
        },
        "Action": [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
      }
    ]
  }'

# Better approach: use an organization condition
aws ecr set-repository-policy \
  --repository-name company/api-service \
  --policy-text '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowOrgPull",
        "Effect": "Allow",
        "Principal": "*",
        "Action": [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ],
        "Condition": {
          "StringEquals": {
            "aws:PrincipalOrgID": "o-abc1234567"
          }
        }
      }
    ]
  }'
```

The organization condition is superior because you don't need to update the policy every time a new account is created.
</details>

### Task 4: Implement Centralized Logging for EKS Audit

Write a Terraform snippet that creates the centralized logging infrastructure: an S3 bucket with Object Lock in the log archive account and a cross-account role that workload accounts can assume to write logs.

<details>
<summary>Solution</summary>

```hcl
# In the log-archive account
resource "aws_s3_bucket" "audit_logs" {
  bucket = "cloudbrew-org-audit-logs"

  object_lock_enabled = true

  tags = {
    Environment = "security"
    Purpose     = "immutable-audit-logs"
    CostCenter  = "security-ops"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  rule {
    default_retention {
      mode = "GOVERNANCE"
      days = 365
    }
  }
}

resource "aws_s3_bucket_versioning" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowOrgWrite"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::*:role/audit-log-writer" }
        Action    = ["s3:PutObject"]
        Resource  = "${aws_s3_bucket.audit_logs.arn}/*"
        Condition = {
          StringEquals = {
            "aws:PrincipalOrgID" = "o-abc1234567"
          }
        }
      },
      {
        Sid       = "DenyDeleteForEveryone"
        Effect    = "Deny"
        Principal = "*"
        Action    = ["s3:DeleteObject", "s3:DeleteObjectVersion"]
        Resource  = "${aws_s3_bucket.audit_logs.arn}/*"
      }
    ]
  })
}

# IAM role in each workload account (deployed via StackSets)
resource "aws_iam_role" "audit_log_writer" {
  name = "audit-log-writer"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "audit_log_writer" {
  name = "write-to-central-bucket"
  role = aws_iam_role.audit_log_writer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "arn:aws:s3:::cloudbrew-org-audit-logs/*"
      }
    ]
  })
}
```
</details>

### Task 5: Calculate Cost Allocation

Given this simplified monthly cost data, calculate per-team costs including shared infrastructure allocation.

| Account | Monthly Cost |
|---|---|
| Network Hub | $3,200 |
| Shared Services | $4,100 |
| Team-Alpha Prod | $12,000 |
| Team-Alpha Staging | $2,400 |
| Team-Beta Prod | $8,000 |
| Team-Beta Staging | $1,600 |

<details>
<summary>Solution</summary>

Shared infrastructure: $3,200 + $4,100 = $7,300

Allocation method: proportional to direct workload spend.

Total workload spend: $12,000 + $2,400 + $8,000 + $1,600 = $24,000

Team Alpha direct: $12,000 + $2,400 = $14,400 (60% of workload spend)
Team Beta direct: $8,000 + $1,600 = $9,600 (40% of workload spend)

Team Alpha shared allocation: $7,300 x 0.60 = $4,380
Team Beta shared allocation: $7,300 x 0.40 = $2,920

**Team Alpha total: $14,400 + $4,380 = $18,780/month**
**Team Beta total: $9,600 + $2,920 = $12,520/month**

Grand total: $18,780 + $12,520 = $31,300 (matches $24,000 + $7,300)

This proportional model is the most common approach. Alternatives include equal split (unfair if teams have different scale) or usage-based (accurate but complex to measure).
</details>

### Success Criteria

- [ ] OU structure includes Security, Infrastructure, Workloads (with sub-OUs), Sandbox, and Suspended
- [ ] Baseline SCP protects CloudTrail, prevents leaving the org, and restricts regions
- [ ] ECR cross-account policy uses organization condition (not hardcoded account IDs)
- [ ] Centralized logging uses S3 Object Lock for immutability
- [ ] Cost allocation includes proportional shared infrastructure distribution

---

## Next Module

[Module 8.2: Advanced Cloud Networking & Transit Hubs](module-8.2-transit-hubs/) -- Learn how to connect all these accounts without creating a networking nightmare. Hub-and-spoke, transit gateways, and the art of routing traffic across organizational boundaries.
