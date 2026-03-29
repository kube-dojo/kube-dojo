---
title: "Module 8.4: Cross-Account IAM & Enterprise Identity"
slug: cloud/advanced-operations/module-8.4-enterprise-identity
sidebar:
  order: 5
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 2.5 hours
>
> **Prerequisites**: [Module 8.1: Multi-Account Architecture](module-8.1-multi-account/), basic understanding of IAM roles and policies in at least one cloud
>
> **Track**: Advanced Cloud Operations

---

## Why This Module Matters

**January 2023. A Fortune 500 financial services company.**

An engineer needed to debug a production issue in a Kubernetes cluster running in a different AWS account. The standard process: log into the management console, switch roles to the production account, navigate to EKS, download the kubeconfig, and authenticate with the cluster. The "role switch" used a long-lived IAM user with `AdministratorAccess` in the production account because the team had never gotten around to building proper cross-account role assumption chains.

That IAM user's access keys were stored in a shared `.env` file in a private GitHub repo. When an employee left the company and their personal GitHub account was compromised three months later, the attacker found the keys, assumed the production role, and had full admin access to production infrastructure for 11 hours before CloudTrail alerts triggered. The attacker exfiltrated 2.3 million customer records. The breach cost $18 million in regulatory fines, legal fees, and customer notification.

Every component of this failure was an identity problem: long-lived credentials instead of temporary tokens, overly broad permissions instead of least privilege, no just-in-time access controls, and no separation between human and machine identities. In a multi-account, multi-cluster world, identity is the new perimeter. This module teaches you how to build identity architectures that scale across accounts and clouds without becoming the security vulnerability they are supposed to prevent.

---

## Trust Boundaries: The Foundation of Cross-Account Identity

A trust boundary is the line between "I trust you" and "prove yourself." In a single AWS account, trust is implicit -- IAM roles trust the account they live in. In a multi-account world, you must explicitly establish trust between accounts.

```
TRUST BOUNDARY HIERARCHY
════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────┐
  │  Organization Trust (AWS Organizations / GCP Org)       │
  │  "These accounts are all part of our organization"      │
  │                                                         │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │  Account Trust (IAM role trust policies)          │   │
  │  │  "Account A trusts Account B to assume this role" │   │
  │  │                                                    │   │
  │  │  ┌─────────────────────────────────────────────┐  │   │
  │  │  │  Service Trust (IRSA / Workload Identity)    │  │   │
  │  │  │  "Pod X in K8s namespace Y can assume this  │  │   │
  │  │  │   IAM role"                                  │  │   │
  │  │  │                                              │  │   │
  │  │  │  ┌────────────────────────────────────────┐ │  │   │
  │  │  │  │  Application Trust (mTLS, JWT, SPIFFE) │ │  │   │
  │  │  │  │  "This specific workload identity is   │ │  │   │
  │  │  │  │   allowed to call this API"            │ │  │   │
  │  │  │  └────────────────────────────────────────┘ │  │   │
  │  │  └─────────────────────────────────────────────┘  │   │
  │  └──────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────┘
```

### The Three Types of Identity

| Identity Type | Examples | Lifetime | Risk Level |
|---|---|---|---|
| Human | Engineers, admins, auditors | Session-based (1-12 hours) | High (phishing, credential theft) |
| Machine (cloud) | EC2 instance roles, GCE service accounts | Instance lifetime | Medium (compromise requires host access) |
| Workload (K8s) | Pod service accounts with cloud IAM bindings | Pod lifetime (minutes to days) | Medium-High (compromised pod = compromised identity) |

The critical insight: in a Kubernetes world, **workload identity is the most important identity type**. Pods need cloud credentials to access databases, secret stores, message queues, and storage. How you provide those credentials determines your security posture.

---

## Cross-Account Role Assumption (AWS)

The fundamental mechanism for cross-account access in AWS is role assumption. Account A creates a role with a trust policy that allows Account B's principals to assume it.

### The Role Chain Pattern

```
CROSS-ACCOUNT ROLE ASSUMPTION
════════════════════════════════════════════════════════════════

  Identity Account (Hub)           Workload Account (Spoke)
  ┌───────────────────────┐       ┌───────────────────────────┐
  │                       │       │                           │
  │  IAM Identity Center  │       │  Role: EKS-Admin          │
  │  (SSO)                │       │  Trust: Identity Account  │
  │       │               │       │  Permissions:             │
  │       │ User logs in  │       │    eks:DescribeCluster    │
  │       │ via SSO       │       │    eks:ListClusters       │
  │       ▼               │       │    eks:AccessKubernetesApi│
  │  Permission Set:      │       │                           │
  │  "EKS-ReadOnly"       │       │  Role: Deploy-Pipeline    │
  │       │               │       │  Trust: Shared Services   │
  │       │ Assumes role ─┼──────▶│  Permissions:             │
  │       │ in spoke      │  STS  │    ecr:GetDownloadUrl     │
  │       │               │       │    eks:AccessKubernetesApi│
  └───────────────────────┘       │                           │
                                  │  Role: Pod-S3-Reader      │
  Shared Services Account        │  Trust: OIDC provider (EKS)│
  ┌───────────────────────┐       │  Permissions:             │
  │                       │       │    s3:GetObject            │
  │  CI/CD Pipeline       │       │    s3:ListBucket           │
  │  (CodeBuild/GH Actions)       │                           │
  │       │               │       └───────────────────────────┘
  │       │ Assumes role ─┼──────▶
  │       │ in spoke      │  STS
  └───────────────────────┘
```

### Setting Up Cross-Account Roles

```bash
# In the WORKLOAD account: Create a role that the Identity account can assume
aws iam create-role \
  --role-name EKS-Admin \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::111111111111:root"
        },
        "Action": "sts:AssumeRole",
        "Condition": {
          "StringEquals": {
            "aws:PrincipalOrgID": "o-abc1234567"
          },
          "Bool": {
            "aws:MultiFactorAuthPresent": "true"
          }
        }
      }
    ]
  }'

# Attach a policy that limits what this role can do
aws iam put-role-policy \
  --role-name EKS-Admin \
  --policy-name eks-admin-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:AccessKubernetesApi",
          "eks:ListNodegroups",
          "eks:DescribeNodegroup"
        ],
        "Resource": "arn:aws:eks:*:222222222222:cluster/*"
      }
    ]
  }'

# In the IDENTITY account: Allow a user/role to assume the cross-account role
aws iam put-user-policy \
  --user-name platform-engineer \
  --policy-name cross-account-assume \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": [
          "arn:aws:iam::222222222222:role/EKS-Admin",
          "arn:aws:iam::333333333333:role/EKS-Admin"
        ]
      }
    ]
  }'

# Assume the role and get temporary credentials
CREDS=$(aws sts assume-role \
  --role-arn arn:aws:iam::222222222222:role/EKS-Admin \
  --role-session-name "debug-session-$(date +%s)" \
  --duration-seconds 3600)

export AWS_ACCESS_KEY_ID=$(echo $CREDS | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo $CREDS | jq -r '.Credentials.SessionToken')

# Now interact with EKS in the workload account
aws eks update-kubeconfig --name prod-cluster --region us-east-1
```

---

## IAM Identity Center (AWS SSO)

IAM Identity Center is the recommended way to manage human access to multiple AWS accounts. It provides a single sign-on portal where users authenticate once and then can switch between accounts and permission sets.

```
IAM IDENTITY CENTER ARCHITECTURE
════════════════════════════════════════════════════════════════

  External IdP                    IAM Identity Center
  (Okta, Entra ID)               (Management Account)
  ┌──────────────────┐           ┌──────────────────────────┐
  │  User: alice      │   SAML/  │                          │
  │  Groups:          │   SCIM   │  Users synced from IdP   │
  │   - platform-eng  │─────────▶│  Groups synced from IdP  │
  │   - sre-oncall    │          │                          │
  └──────────────────┘           │  Permission Sets:        │
                                  │  ┌────────────────────┐  │
                                  │  │ ProdReadOnly       │  │
                                  │  │ - eks:Describe*    │  │
                                  │  │ - logs:Get*        │  │
                                  │  │ - cloudwatch:Get*  │  │
                                  │  └────────────────────┘  │
                                  │  ┌────────────────────┐  │
                                  │  │ ProdAdmin          │  │
                                  │  │ - eks:*            │  │
                                  │  │ - ec2:Describe*    │  │
                                  │  │ - s3:*             │  │
                                  │  └────────────────────┘  │
                                  │  ┌────────────────────┐  │
                                  │  │ DevFullAccess      │  │
                                  │  │ - * (all actions)  │  │
                                  │  └────────────────────┘  │
                                  │                          │
                                  │  Assignments:            │
                                  │  platform-eng + ProdRead │
                                  │   -> Accounts: prod-*    │
                                  │  sre-oncall + ProdAdmin  │
                                  │   -> Accounts: prod-*    │
                                  │  platform-eng + DevFull  │
                                  │   -> Accounts: dev-*     │
                                  └──────────────────────────┘
```

### Setting Up IAM Identity Center with Terraform

```hcl
# Configure the Identity Center instance
data "aws_ssoadmin_instances" "main" {}

locals {
  sso_instance_arn = tolist(data.aws_ssoadmin_instances.main.arns)[0]
  identity_store   = tolist(data.aws_ssoadmin_instances.main.identity_store_ids)[0]
}

# Create permission sets
resource "aws_ssoadmin_permission_set" "prod_readonly" {
  name             = "ProdReadOnly"
  instance_arn     = local.sso_instance_arn
  session_duration = "PT4H"
  description      = "Read-only access to production accounts"
}

resource "aws_ssoadmin_managed_policy_attachment" "prod_readonly_view" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/ViewOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.prod_readonly.arn
}

# Custom inline policy for EKS access
resource "aws_ssoadmin_permission_set_inline_policy" "prod_readonly_eks" {
  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.prod_readonly.arn

  inline_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:AccessKubernetesApi"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_ssoadmin_permission_set" "prod_admin" {
  name             = "ProdAdmin"
  instance_arn     = local.sso_instance_arn
  session_duration = "PT1H"  # Short session for admin access
  description      = "Admin access to production (break-glass)"
}

# Assign permission set to group for specific accounts
resource "aws_ssoadmin_account_assignment" "sre_prod_admin" {
  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.prod_admin.arn

  principal_id   = data.aws_identitystore_group.sre_oncall.group_id
  principal_type = "GROUP"

  target_id   = "222222222222"  # prod account ID
  target_type = "AWS_ACCOUNT"
}
```

---

## GCP Workload Identity Federation Across Projects

GCP's approach to cross-project identity uses Workload Identity Federation -- allowing GKE workloads in one project to impersonate service accounts in another project without managing keys.

```
GCP WORKLOAD IDENTITY ACROSS PROJECTS
════════════════════════════════════════════════════════════════

  GKE Project (team-a-prod)          Target Project (data-lake)
  ┌──────────────────────────┐      ┌──────────────────────────┐
  │                          │      │                          │
  │  GKE Cluster             │      │  BigQuery Dataset        │
  │  ┌────────────────────┐  │      │  Cloud Storage Buckets   │
  │  │  Pod                │  │      │                          │
  │  │  SA: data-reader    │  │      │  Service Account:        │
  │  │  (K8s SA)           │  │      │  bq-reader@data-lake     │
  │  └────────┬───────────┘  │      │  .iam.gserviceaccount.com│
  │           │              │      │                          │
  │  Workload Identity binds │      │  IAM Policy:             │
  │  K8s SA to GCP SA ──────┼─────▶│  roles/bigquery.dataViewer│
  │                          │      │                          │
  └──────────────────────────┘      └──────────────────────────┘

  The Pod authenticates as bq-reader@data-lake WITHOUT any
  service account keys. GKE's Workload Identity provides
  federated tokens that GCP IAM trusts.
```

```bash
# Step 1: Enable Workload Identity on the GKE cluster
gcloud container clusters update team-a-prod \
  --project=team-a-prod \
  --region=us-central1 \
  --workload-pool=team-a-prod.svc.id.goog

# Step 2: Create a GCP service account in the TARGET project
gcloud iam service-accounts create bq-reader \
  --project=data-lake \
  --display-name="BigQuery Reader for Team A"

# Step 3: Grant the GCP SA access to BigQuery
gcloud projects add-iam-policy-binding data-lake \
  --member="serviceAccount:bq-reader@data-lake.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Step 4: Allow the K8s SA to impersonate the GCP SA
# This is the cross-project trust binding
gcloud iam service-accounts add-iam-policy-binding \
  bq-reader@data-lake.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:team-a-prod.svc.id.goog[analytics/data-reader]"
#                          ^^^^^^^^^^^^^^ GKE project
#                                         ^^^^^^^^^ K8s namespace
#                                                    ^^^^^^^^^^^ K8s SA name

# Step 5: Create the K8s ServiceAccount with the annotation
kubectl --context team-a-prod create namespace analytics

kubectl --context team-a-prod apply -f - <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-reader
  namespace: analytics
  annotations:
    iam.gke.io/gcp-service-account: bq-reader@data-lake.iam.gserviceaccount.com
EOF

# Step 6: Deploy a pod using this service account
kubectl --context team-a-prod apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-worker
  namespace: analytics
spec:
  replicas: 2
  selector:
    matchLabels:
      app: analytics-worker
  template:
    metadata:
      labels:
        app: analytics-worker
    spec:
      serviceAccountName: data-reader
      containers:
        - name: worker
          image: gcr.io/team-a-prod/analytics-worker:v1.4.2
          # No GCP credentials needed - Workload Identity provides them
EOF
```

---

## Azure Entra ID and Workload Identity

Azure uses Entra ID (formerly Azure AD) as the central identity provider, with Workload Identity Federation for Kubernetes pods.

```bash
# Step 1: Enable OIDC issuer and workload identity on AKS
az aks update \
  --resource-group prod-rg \
  --name team-a-prod \
  --enable-oidc-issuer \
  --enable-workload-identity

# Get the OIDC issuer URL
OIDC_ISSUER=$(az aks show \
  --resource-group prod-rg \
  --name team-a-prod \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Step 2: Create a Managed Identity (cross-subscription capable)
az identity create \
  --name "team-a-keyvault-reader" \
  --resource-group identity-rg \
  --subscription IDENTITY_SUB_ID

CLIENT_ID=$(az identity show \
  --name "team-a-keyvault-reader" \
  --resource-group identity-rg \
  --query 'clientId' -o tsv)

# Step 3: Create federated credential (trust K8s SA)
az identity federated-credential create \
  --name "aks-team-a-prod" \
  --identity-name "team-a-keyvault-reader" \
  --resource-group identity-rg \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:app:keyvault-reader" \
  --audience "api://AzureADTokenExchange"

# Step 4: Grant the Managed Identity access to Key Vault
# (in a DIFFERENT subscription)
az role assignment create \
  --assignee $CLIENT_ID \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/KEYVAULT_SUB_ID/resourceGroups/security-rg/providers/Microsoft.KeyVault/vaults/prod-secrets"

# Step 5: Create the K8s ServiceAccount with workload identity labels
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: keyvault-reader
  namespace: app
  annotations:
    azure.workload.identity/client-id: "$CLIENT_ID"
  labels:
    azure.workload.identity/use: "true"
EOF
```

---

## Attribute-Based Access Control (ABAC)

ABAC extends traditional RBAC by making access decisions based on attributes of the requester, the resource, and the environment -- not just static role assignments.

```
RBAC vs ABAC
════════════════════════════════════════════════════════════════

RBAC: "Alice has the EKS-Admin role, which allows eks:* on all clusters"
  - Static assignment
  - Broad permissions
  - No context awareness

ABAC: "Alice can access EKS clusters IF:
  - She is in the sre-oncall group AND
  - The cluster has tag Environment=production AND
  - The current time is during her on-call shift AND
  - She has completed the security training this quarter AND
  - The request originates from the corporate VPN"
  - Dynamic, context-aware
  - Fine-grained
  - Harder to reason about
```

### AWS ABAC with Tags

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:AccessKubernetesApi"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Team": "${aws:PrincipalTag/Team}",
          "aws:ResourceTag/Environment": "production"
        }
      }
    }
  ]
}
```

This policy says: "You can access EKS clusters only if the cluster's `Team` tag matches your own `Team` tag, and the cluster is in production." An engineer tagged `Team=payments` can access the payments production cluster but not the analytics production cluster. No explicit role assignment per cluster needed -- the tags do the work.

```bash
# Tag the IAM user/role with their team
aws iam tag-user \
  --user-name alice \
  --tags Key=Team,Value=payments Key=CostCenter,Value=CC-1234

# Tag the EKS cluster
aws eks tag-resource \
  --resource-arn arn:aws:eks:us-east-1:222222222222:cluster/payments-prod \
  --tags Team=payments,Environment=production
```

### GCP ABAC with IAM Conditions

```bash
# Grant access to GKE cluster only during business hours
gcloud projects add-iam-policy-binding team-a-prod \
  --member="user:alice@company.com" \
  --role="roles/container.developer" \
  --condition='expression=request.time.getHours("America/New_York") >= 9 && request.time.getHours("America/New_York") <= 17,title=business-hours-only,description=Access only during EST business hours'
```

---

## Just-In-Time (JIT) Access

JIT access grants elevated permissions only when needed, for a limited duration, with an approval workflow. It eliminates standing privileges -- the most dangerous security pattern in cloud environments.

```
JIT ACCESS FLOW
════════════════════════════════════════════════════════════════

  Engineer                     Approval System              Cloud IAM
  ┌───────────┐               ┌──────────────┐            ┌──────────┐
  │           │    Request    │              │            │          │
  │  "I need  │──────────────▶│  ConductorOne │            │  No access│
  │  prod     │    reason:   │  / Indent /   │            │  (default)│
  │  access"  │   "PD-1234"  │  AccessLint   │            │          │
  │           │               │              │            │          │
  │           │               │  Auto-approve│  Grant     │          │
  │           │               │  IF:         │──────────▶│  Temporary│
  │           │               │  - On-call   │  role for  │  role     │
  │           │               │  - PagerDuty │  4 hours   │  active   │
  │           │               │    incident  │            │          │
  │           │               │  - Team lead │            │          │
  │           │               │    approval  │  Revoke    │          │
  │  Access   │               │              │──────────▶│  Access   │
  │  expires  │               │  After 4hrs: │  after TTL │  revoked  │
  │           │               │  auto-revoke │            │          │
  └───────────┘               └──────────────┘            └──────────┘

  Key principle: NO standing admin access.
  Even the CEO cannot access prod without going through JIT.
```

### Implementing JIT with AWS SSO Permission Sets

```bash
# Create a "break-glass" permission set with short duration
aws sso-admin create-permission-set \
  --instance-arn $SSO_INSTANCE_ARN \
  --name "BreakGlass-ProdAdmin" \
  --session-duration "PT2H" \
  --description "Emergency production admin access - requires approval"

# The approval workflow lives in your JIT tool (ConductorOne, Indent, etc.)
# When approved, the tool makes this API call:

aws sso-admin create-account-assignment \
  --instance-arn $SSO_INSTANCE_ARN \
  --target-id 222222222222 \
  --target-type AWS_ACCOUNT \
  --permission-set-arn $BREAKGLASS_PS_ARN \
  --principal-type USER \
  --principal-id $USER_ID

# When the TTL expires, the tool removes the assignment:
aws sso-admin delete-account-assignment \
  --instance-arn $SSO_INSTANCE_ARN \
  --target-id 222222222222 \
  --target-type AWS_ACCOUNT \
  --permission-set-arn $BREAKGLASS_PS_ARN \
  --principal-type USER \
  --principal-id $USER_ID
```

### Kubernetes RBAC for JIT

```yaml
# A ClusterRoleBinding that grants temporary admin access
# Created by your JIT tool when access is approved
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: jit-alice-admin-20260324
  labels:
    jit.company.com/requester: alice
    jit.company.com/expires: "2026-03-24T14:00:00Z"
    jit.company.com/ticket: "PD-1234"
  annotations:
    jit.company.com/reason: "Investigating payment processing errors"
    jit.company.com/approver: "bob@company.com"
subjects:
  - kind: User
    name: alice@company.com
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
---
# CronJob to clean up expired JIT bindings
apiVersion: batch/v1
kind: CronJob
metadata:
  name: jit-cleanup
  namespace: kube-system
spec:
  schedule: "*/15 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: jit-cleanup-sa
          containers:
            - name: cleanup
              image: bitnami/kubectl:1.35
              command:
                - /bin/sh
                - -c
                - |
                  NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
                  kubectl get clusterrolebindings -l jit.company.com/expires -o json | \
                    jq -r --arg now "$NOW" \
                    '.items[] | select(.metadata.labels["jit.company.com/expires"] < $now) | .metadata.name' | \
                    xargs -r kubectl delete clusterrolebinding
          restartPolicy: OnFailure
```

---

## Did You Know?

1. **AWS IAM evaluates an average of 2.5 billion authorization requests per second** across all AWS accounts globally. Every API call, every S3 object access, every Lambda invocation goes through IAM evaluation. The system has a design target of sub-millisecond evaluation latency, which is why IAM policies are evaluated locally at the service endpoint rather than at a central authorization server.

2. **GCP's Workload Identity Federation supports external identity providers beyond GCP.** You can configure a GKE workload in one cloud to authenticate to GCP services using an OIDC token issued by an AWS EKS cluster. This means an EKS pod can access BigQuery without any GCP service account keys -- the EKS OIDC issuer is registered as a trusted identity provider in GCP. This is how true multi-cloud workload identity works.

3. **The concept of "confused deputy" attacks** was first described by Norm Hardy in 1988. In cloud IAM, it applies when a service (the "deputy") is tricked into using its own permissions on behalf of an unauthorized caller. AWS mitigates this with the `aws:SourceArn` and `aws:SourceAccount` conditions on trust policies. Every cross-account role should include these conditions to prevent confused deputy attacks.

4. **Azure Entra ID processes over 90 billion authentications per day** as of 2025, making it the largest identity provider in the world by transaction volume. This includes not just Azure cloud access but Microsoft 365, third-party SaaS applications, and on-premises Active Directory hybrid scenarios. When you federate AKS workload identity through Entra ID, your Kubernetes pods are participating in this same identity fabric.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Using long-lived access keys for cross-account access | "AssumeRole is complicated" | Always use STS temporary credentials. If your tool doesn't support AssumeRole, the tool is not ready for multi-account. |
| Granting `*` permissions on cross-account roles | "We'll tighten it later" | Define the minimum required permissions from day one. Use CloudTrail to identify which APIs are actually called, then scope down. |
| Not using MFA for human cross-account role assumption | "SSO handles authentication" | Even with SSO, require MFA via the `aws:MultiFactorAuthPresent` condition on trust policies for production account roles. |
| Sharing GCP service account keys between projects | "Workload Identity is too complex" | Workload Identity eliminates key management entirely. The setup complexity is a one-time cost; managing keys is a forever cost with ongoing risk. |
| No session duration limits on admin roles | Default is 1 hour for SSO, 12 hours for IAM roles | Set aggressive session durations: 1h for admin, 4h for read-only, 15 minutes for break-glass. Force re-authentication. |
| Using the same K8s service account for multiple workloads | "It's easier to manage one SA" | Each workload should have its own service account with its own cloud IAM binding. Shared SAs mean shared blast radius. |
| Not logging cross-account role assumptions | "CloudTrail is enabled" | Verify that AssumeRole events are captured in your centralized log archive. Create alerts for role assumptions into production accounts outside business hours. |
| Forgetting to add `aws:SourceAccount` to trust policies | "The role ARN in the trust policy is enough" | Without source conditions, any account that can construct the right principal ARN could assume your role. Always add `aws:PrincipalOrgID` or `aws:SourceAccount`. |

---

## Quiz

<details>
<summary>1. Why are temporary credentials (STS) preferred over long-lived access keys for cross-account access?</summary>

Temporary credentials have a built-in expiration (typically 1-12 hours), which limits the window of exploitation if they are compromised. Long-lived access keys never expire unless manually rotated, meaning a leaked key provides permanent access until someone notices and revokes it. STS credentials also carry session metadata (who assumed the role, from which account, the session name) that appears in CloudTrail logs, making audit trails more useful. Additionally, STS role assumption can enforce MFA, IP restrictions, and time-based conditions at the point of assumption, which static keys cannot.
</details>

<details>
<summary>2. How does GCP Workload Identity Federation eliminate the need for service account keys?</summary>

Workload Identity Federation creates a trust relationship between a Kubernetes service account and a GCP service account. When a pod needs GCP credentials, the GKE metadata server intercepts the token request and exchanges the pod's Kubernetes service account token (a JWT signed by the cluster's OIDC issuer) for a short-lived GCP access token. No long-lived keys are stored anywhere -- not in Kubernetes Secrets, not in environment variables, not in files. The trust is established by registering the GKE cluster's OIDC issuer URL with GCP IAM, and the binding is between a specific K8s namespace/service-account combination and a specific GCP service account.
</details>

<details>
<summary>3. What is the difference between RBAC and ABAC, and when would you choose ABAC for cloud IAM?</summary>

RBAC assigns permissions based on roles: "Alice is an EKS-Admin, therefore she can manage clusters." ABAC assigns permissions based on attributes: "Alice can manage clusters IF the cluster's Team tag matches her Team tag AND she is on-call AND the request comes from the VPN." Choose ABAC when: (a) you have many similar resources that differ by a tag (e.g., 50 EKS clusters owned by different teams), (b) you want permissions to scale automatically as resources are created (no new role assignment needed), or (c) you need context-aware access decisions (time of day, source IP, incident status). ABAC is harder to audit than RBAC, so many organizations use RBAC as the baseline and add ABAC conditions for specific high-sensitivity scenarios.
</details>

<details>
<summary>4. What is a "confused deputy" attack in the context of cross-account IAM?</summary>

A confused deputy attack occurs when a service with cross-account permissions is tricked into acting on behalf of an unauthorized party. Example: Service X in Account A can assume a role in Account B. An attacker convinces Service X to make a request to Account B using its cross-account credentials, but for the attacker's purposes. Without source conditions (aws:SourceArn, aws:SourceAccount), Account B's trust policy cannot distinguish between legitimate requests from Service X and requests that Service X was tricked into making. The fix is always to add conditions that verify the original caller's identity, not just the immediate caller's identity.
</details>

<details>
<summary>5. Why should each Kubernetes workload have its own service account with its own cloud IAM binding?</summary>

If multiple workloads share a service account, they all share the same cloud IAM permissions. If one workload needs S3 read access and another needs DynamoDB write access, the shared SA gets both -- violating least privilege. More critically, if any one of those workloads is compromised, the attacker gains the combined permissions of all workloads using that SA. With individual SAs, a compromised pod can only access the specific cloud resources that particular workload needs. The operational overhead of creating per-workload SAs is minimal when automated through IaC, and the security benefit is significant.
</details>

<details>
<summary>6. How does Just-In-Time (JIT) access reduce the risk of credential compromise?</summary>

JIT access eliminates standing privileges -- no one has permanent admin access to production. Permissions are granted only when a specific need arises (an incident, a deployment, a debugging session), for a limited duration (1-4 hours), with an approval trail (who approved, why, linked to a ticket). This means that even if an attacker compromises an engineer's credentials, those credentials have no production access by default. The attacker would need to also compromise the JIT approval workflow, which is a separate system with its own authentication. The attack surface shrinks from "permanent admin access" to "temporary access during approved windows."
</details>

---

## Hands-On Exercise: Build Cross-Account Identity for EKS

In this exercise, you will set up cross-account IAM role assumption and workload identity for an EKS cluster.

### Scenario

**Setup**: Two AWS accounts (simulated with IAM roles in a single account for this exercise).
- "Identity Account" role: manages who can access what
- "Workload Account" role: runs the EKS cluster
- A pod in EKS needs to read from an S3 bucket in a "Data Account"

### Task 1: Create the Cross-Account Trust Policy

Write an IAM role trust policy that allows the Identity Account to assume a role in the Workload Account, with MFA required and organization condition.

<details>
<summary>Solution</summary>

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowIdentityAccountAssumption",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-abc1234567"
        },
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        },
        "NumericLessThan": {
          "aws:MultiFactorAuthAge": "3600"
        }
      }
    }
  ]
}
```

The `MultiFactorAuthAge` condition ensures the MFA was verified within the last hour, preventing stale MFA sessions.
</details>

### Task 2: Configure EKS IRSA for Cross-Account S3 Access

Write the IAM role and Kubernetes ServiceAccount configuration for a pod that needs to read S3 objects from a different account.

<details>
<summary>Solution</summary>

```bash
# Step 1: Get the EKS OIDC provider URL
OIDC_PROVIDER=$(aws eks describe-cluster \
  --name prod-cluster \
  --query "cluster.identity.oidc.issuer" \
  --output text | sed 's|https://||')

# Step 2: Create the IAM role with trust policy for IRSA
cat <<EOF > irsa-trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::222222222222:oidc-provider/${OIDC_PROVIDER}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_PROVIDER}:sub": "system:serviceaccount:analytics:s3-reader",
          "${OIDC_PROVIDER}:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name pod-s3-reader \
  --assume-role-policy-document file://irsa-trust-policy.json

# Step 3: Grant the role cross-account S3 access
aws iam put-role-policy \
  --role-name pod-s3-reader \
  --policy-name s3-cross-account-read \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::data-account-analytics-bucket",
          "arn:aws:s3:::data-account-analytics-bucket/*"
        ]
      }
    ]
  }'
```

```yaml
# Step 4: Create the Kubernetes ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-reader
  namespace: analytics
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::222222222222:role/pod-s3-reader
---
# Step 5: Deploy a pod using the service account
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-processor
  namespace: analytics
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-processor
  template:
    metadata:
      labels:
        app: data-processor
    spec:
      serviceAccountName: s3-reader
      containers:
        - name: processor
          image: amazon/aws-cli:latest
          command: ["sh", "-c", "aws s3 ls s3://data-account-analytics-bucket/ && sleep 3600"]
```

Note: The S3 bucket in the Data Account also needs a bucket policy allowing the role from the Workload Account.
</details>

### Task 3: Write the S3 Bucket Policy (Data Account Side)

Write the bucket policy that allows the pod's IAM role to read objects.

<details>
<summary>Solution</summary>

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCrossAccountRead",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222222222222:role/pod-s3-reader"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::data-account-analytics-bucket",
        "arn:aws:s3:::data-account-analytics-bucket/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-abc1234567"
        }
      }
    }
  ]
}
```

The organization condition ensures only roles from your organization can access the bucket, even if the role ARN is known.
</details>

### Task 4: Design JIT Access for Production EKS

Design a JIT access flow that grants temporary kubectl admin access to a production EKS cluster, including the approval workflow, the RBAC objects, and the cleanup mechanism.

<details>
<summary>Solution</summary>

```
JIT Flow:
1. Engineer opens a request in JIT tool (e.g., ConductorOne)
   - Specifies: cluster name, namespace, duration, reason, PagerDuty incident
2. Auto-approval if: on-call + active incident
   Manual approval if: not on-call
3. Approved -> JIT tool executes:
   a. Creates temporary IAM Identity Center assignment (SSO access)
   b. Creates ClusterRoleBinding in EKS with TTL label
   c. Notifies #security-audit Slack channel
4. TTL expires -> JIT tool executes:
   a. Removes IAM Identity Center assignment
   b. CronJob deletes expired ClusterRoleBinding
   c. Logs access duration and actions taken
```

```yaml
# The ClusterRoleBinding created by the JIT tool
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: jit-alice-20260324-pd5678
  labels:
    jit.company.com/requester: alice
    jit.company.com/expires: "2026-03-24T16:00:00Z"
    jit.company.com/incident: "PD-5678"
    jit.company.com/type: break-glass
  annotations:
    jit.company.com/approver: auto-approved-oncall
    jit.company.com/reason: "Payment processing errors in us-east-1"
subjects:
  - kind: Group
    name: sso-alice-prod-admin
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
---
# Scoped alternative: namespace-level admin instead of cluster-admin
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jit-alice-payments-admin
  namespace: payments
  labels:
    jit.company.com/requester: alice
    jit.company.com/expires: "2026-03-24T16:00:00Z"
subjects:
  - kind: Group
    name: sso-alice-prod-admin
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: admin
  apiGroup: rbac.authorization.k8s.io
```
</details>

### Success Criteria

- [ ] Trust policy includes organization condition AND MFA requirement
- [ ] IRSA configuration correctly binds K8s SA to IAM role with namespace+SA conditions
- [ ] S3 bucket policy uses organization condition (not just role ARN)
- [ ] JIT design includes approval workflow, temporary RBAC, and automated cleanup
- [ ] No long-lived credentials used anywhere in the solution

---

## Next Module

[Module 8.5: Disaster Recovery: RTO/RPO for Kubernetes](module-8.5-disaster-recovery/) -- Your multi-account architecture is secure, your clusters can communicate, and your identity is solid. Now learn what happens when everything falls over. RTO, RPO, etcd snapshots, Velero, and the art of recovering from the unthinkable.
