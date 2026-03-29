---
title: "Module 4.3: Cloud IAM Integration for Kubernetes"
slug: cloud/architecture-patterns/module-4.3-cloud-iam
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 2.5 hours
>
> **Prerequisites**: [Module 4.1: Managed vs Self-Managed Kubernetes](module-4.1-managed-vs-selfmanaged/)
>
> **Track**: Cloud Architecture Patterns

---

## Why This Module Matters

**January 2023. A Series B startup in the healthcare space.**

A developer needed their Kubernetes pod to read patient records from an S3 bucket. The fastest path? Create an IAM user, generate an access key, paste it into a Kubernetes Secret, and mount it into the pod. Took five minutes. Shipped to production on Friday afternoon.

On Monday morning, the security team's automated scanner flagged something alarming. The access key had been committed to a private GitHub repository in a Helm values file. GitHub's secret scanning caught it. But here's the real problem: the IAM user had `AmazonS3FullAccess` -- not scoped to the one bucket, but to every bucket in the account. And the key had no expiration date.

The security team revoked the key, which broke the pod, which broke the patient data pipeline, which delayed lab results for 340 patients. The incident postmortem revealed that 23 other services in the same cluster used the same pattern: long-lived IAM access keys stored as Kubernetes Secrets. Nine of those keys had been rotated zero times in over a year.

This is the problem that cloud IAM integration solves. Instead of passing secrets around -- creating them, storing them, rotating them, and praying nobody commits them to Git -- you pass *identity*. The pod says "I am the payment processor" and the cloud provider says "I can verify that claim, and here's a short-lived credential good for the next 15 minutes."

No long-lived keys. No secrets to rotate. No credentials to leak. In this module, you'll learn exactly how this works, from the OIDC mechanics underneath to the practical implementation on each major cloud provider.

---

## The Fundamental Problem: Pods Need Cloud Access

Almost every real Kubernetes workload needs to talk to cloud services. Reading from S3, publishing to SNS, querying DynamoDB, pulling images from ECR, encrypting data with KMS. Each of these API calls requires authentication.

### The Old Way: Static Credentials

```
THE CREDENTIALS ANTI-PATTERN
═══════════════════════════════════════════════════════════════

Developer creates IAM user
        │
        ▼
Generates access key + secret key
        │
        ▼
Stores in Kubernetes Secret
        │
        ├──▶ Key committed to Git (risk: exposure)
        ├──▶ Key shared across pods (risk: blast radius)
        ├──▶ Key never rotated (risk: compromise window)
        ├──▶ Key has broad permissions (risk: lateral movement)
        └──▶ Key stored base64-encoded, not encrypted (risk: theft)
               │
               ▼
        Attacker gains access to one pod
               │
               ▼
        Reads mounted Secret (trivial)
               │
               ▼
        Uses long-lived key to access cloud resources
               │
               ▼
        Key works from ANYWHERE (no IP restriction)
               │
               ▼
        Full S3 access, full DynamoDB access, etc.
```

```yaml
# DO NOT DO THIS -- the anti-pattern
apiVersion: v1
kind: Secret
metadata:
  name: aws-credentials
  namespace: production
type: Opaque
data:
  # These are base64-encoded, NOT encrypted
  # Anyone with namespace read access can decode them
  AWS_ACCESS_KEY_ID: QUtJQVhYWFhYWFhYWFhYWA==
  AWS_SECRET_ACCESS_KEY: d0phbGpkaGZranNoZGtqZmhza2RqaGZrc2Q=
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-processor
spec:
  template:
    spec:
      containers:
        - name: processor
          image: company/data-processor:v1.2
          envFrom:
            - secretRef:
                name: aws-credentials
          # This pod now has permanent cloud access
          # The key works forever, from any network
          # If this pod is compromised, so is the key
```

### The New Way: Federated Identity

```
THE IDENTITY FEDERATION PATTERN
═══════════════════════════════════════════════════════════════

Pod starts up with a ServiceAccount
        │
        ▼
Kubernetes injects a signed JWT token (short-lived)
        │
        ▼
Pod presents token to cloud provider's STS
        │
        ▼
Cloud provider verifies the token signature
using the cluster's OIDC public key
        │
        ▼
Cloud provider returns temporary credentials
(valid for 15 minutes, scoped to one IAM role)
        │
        ▼
Pod uses temporary credentials for cloud API calls
        │
        ▼
Credentials expire automatically
No rotation needed. No secrets stored. Nothing to leak.


Security properties:
  - Credentials are ephemeral (15-60 min lifetime)
  - Credentials are scoped (one role per ServiceAccount)
  - No secrets exist in cluster (nothing to steal from etcd)
  - Audience-restricted (token only works with one provider)
  - Auditable (cloud audit logs show which pod made which call)
```

---

## How OIDC Federation Actually Works

The mechanism underneath is OIDC (OpenID Connect) token exchange. Let's trace the entire flow step by step.

### Step 1: The Cluster Publishes Its Public Keys

Every Kubernetes cluster has a Service Account Token Issuer. This issuer has a key pair. The public key is published at a well-known OIDC discovery endpoint.

```bash
# Every EKS cluster has an OIDC issuer URL
aws eks describe-cluster --name production --query "cluster.identity.oidc.issuer"
# Output: "https://oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890"

# The OIDC discovery document is publicly accessible
curl -s https://oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890/.well-known/openid-configuration | jq .
# {
#   "issuer": "https://oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890",
#   "jwks_uri": "https://oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890/keys",
#   "authorization_endpoint": "...",
#   "response_types_supported": ["id_token"],
#   "subject_types_supported": ["public"],
#   "id_token_signing_alg_values_supported": ["RS256"]
# }

# The public keys (JWKS) used to verify tokens
curl -s https://oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890/keys | jq .
# Returns RSA public keys that can verify ServiceAccount tokens
```

### Step 2: Kubernetes Injects a Signed Token into the Pod

When a pod uses a ServiceAccount with an associated IAM role, Kubernetes injects a projected service account token -- a JWT signed by the cluster's private key.

```yaml
# The ServiceAccount references an IAM role
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-processor
  namespace: production
  annotations:
    # EKS
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/data-processor-role
    # GKE
    # iam.gke.io/gcp-service-account: data-processor@project.iam.gserviceaccount.com
    # AKS
    # azure.workload.identity/client-id: "12345678-abcd-efgh-ijkl-123456789012"
```

```bash
# Inside the pod, the token is mounted at a well-known path
# Let's decode it to see what's inside
cat /var/run/secrets/eks.amazonaws.com/serviceaccount/token | jwt decode -

# Decoded JWT payload:
# {
#   "aud": ["sts.amazonaws.com"],           # Audience: only valid for AWS STS
#   "exp": 1711296000,                       # Expires in 24 hours
#   "iat": 1711209600,                       # Issued at
#   "iss": "https://oidc.eks...ABCDEF",     # Issuer: this cluster's OIDC endpoint
#   "kubernetes.io": {
#     "namespace": "production",
#     "pod": {
#       "name": "data-processor-7d4b8c9f-x2k4",
#       "uid": "a1b2c3d4-..."
#     },
#     "serviceaccount": {
#       "name": "data-processor",
#       "uid": "e5f6g7h8-..."
#     }
#   },
#   "sub": "system:serviceaccount:production:data-processor"
# }
```

### Step 3: The Pod Exchanges the Token for Cloud Credentials

The AWS SDK (or GCP/Azure SDK) in the pod automatically detects the projected token and calls STS (Security Token Service) to exchange it.

```
TOKEN EXCHANGE FLOW
═══════════════════════════════════════════════════════════════

  Pod                         AWS STS                  IAM
   │                            │                       │
   │  AssumeRoleWithWebIdentity │                       │
   │  (JWT token + role ARN)    │                       │
   │ ─────────────────────────▶ │                       │
   │                            │                       │
   │                            │  Fetch OIDC public    │
   │                            │  keys from cluster's  │
   │                            │  JWKS endpoint        │
   │                            │ ◀─────────────────▶   │
   │                            │                       │
   │                            │  Verify:              │
   │                            │  1. Token signature   │
   │                            │  2. Issuer matches    │
   │                            │  3. Audience is STS   │
   │                            │  4. Not expired       │
   │                            │  5. Subject matches   │
   │                            │     trust policy      │
   │                            │                       │
   │                            │  Check IAM role       │
   │                            │  trust policy allows  │
   │                            │  this ServiceAccount  │
   │                            │ ──────────────────▶   │
   │                            │                       │
   │                            │  ◀── Policy OK ────── │
   │                            │                       │
   │  Temporary credentials     │                       │
   │  (15-min expiry)           │                       │
   │ ◀───────────────────────── │                       │
   │                            │                       │
   │  Use credentials for       │                       │
   │  S3, DynamoDB, etc.        │                       │
```

### Step 4: IAM Trust Policy Controls Which Pods Get Which Roles

The IAM role's trust policy specifies exactly which Kubernetes ServiceAccounts can assume it. This is the access control boundary.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890:sub": "system:serviceaccount:production:data-processor",
          "oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

This trust policy says: "Only the `data-processor` ServiceAccount in the `production` namespace of the cluster with this specific OIDC issuer can assume this role." No other pod, no other namespace, no other cluster.

---

## The Confused Deputy Problem

The confused deputy problem is the most important security concept in IAM federation. Understanding it prevents a class of privilege escalation attacks.

```
THE CONFUSED DEPUTY ATTACK
═══════════════════════════════════════════════════════════════

Scenario: A CI/CD service (Jenkins) has broad IAM permissions
to deploy to Kubernetes. An attacker compromises a low-privilege
pod and exploits the CI/CD service to act on their behalf.

WITHOUT proper scoping:

  Attacker's Pod                  Jenkins (CI/CD)              AWS
  (low privilege)                 (high privilege)
       │                               │                        │
       │  "Please deploy this          │                        │
       │   manifest to production"     │                        │
       │ ─────────────────────────▶    │                        │
       │                               │                        │
       │                               │  Deploy (using         │
       │                               │  Jenkins's IAM role)   │
       │                               │ ─────────────────────▶ │
       │                               │                        │
       │                               │  Allowed! Jenkins has  │
       │                               │  production access     │
       │                               │ ◀───────────────────── │

  The attacker used Jenkins as a "confused deputy" --
  Jenkins acted on the attacker's behalf using its own
  elevated permissions.


WITH pod-level identity:

  Attacker's Pod                  AWS STS
  (ServiceAccount: "attacker-sa")
       │                               │
       │  AssumeRoleWithWebIdentity    │
       │  (token for "attacker-sa")    │
       │ ─────────────────────────▶    │
       │                               │
       │  Trust policy check:          │
       │  "attacker-sa" is NOT in      │
       │  the trust policy for the     │
       │  production deploy role       │
       │                               │
       │  ACCESS DENIED                │
       │ ◀───────────────────────────  │

  The attacker's identity is their ServiceAccount,
  not the CI/CD tool they're calling through.
  The cloud provider checks the ORIGINAL caller's identity.
```

The fix is straightforward: every pod gets its own ServiceAccount, and each IAM role's trust policy specifies exactly which ServiceAccounts can assume it. A pod in the `staging` namespace can never assume a role that trusts only `production:data-processor`.

---

## Implementation: AWS (IRSA and Pod Identity)

AWS offers two mechanisms. IRSA (IAM Roles for Service Accounts) is the established approach. EKS Pod Identity is the newer, simpler alternative.

### IRSA Setup

```bash
# Step 1: Associate OIDC provider with your AWS account
eksctl utils associate-iam-oidc-provider \
  --cluster production \
  --approve

# Step 2: Create IAM role with trust policy for the ServiceAccount
aws iam create-role \
  --role-name data-processor-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890:sub": "system:serviceaccount:production:data-processor",
          "oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890:aud": "sts.amazonaws.com"
        }
      }
    }]
  }'

# Step 3: Attach a permission policy (least privilege!)
aws iam put-role-policy \
  --role-name data-processor-role \
  --policy-name s3-read-patient-data \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::patient-data-bucket",
        "arn:aws:s3:::patient-data-bucket/*"
      ]
    }]
  }'
```

```yaml
# Step 4: Create ServiceAccount with role annotation
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-processor
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/data-processor-role
---
# Step 5: Use the ServiceAccount in your Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-processor
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-processor
  template:
    metadata:
      labels:
        app: data-processor
    spec:
      serviceAccountName: data-processor  # This is the key line
      containers:
        - name: processor
          image: company/data-processor:v1.2
          # No AWS_ACCESS_KEY_ID needed!
          # No AWS_SECRET_ACCESS_KEY needed!
          # The AWS SDK automatically uses the projected token
```

### EKS Pod Identity (Newer, Simpler)

```bash
# Pod Identity simplifies the trust relationship
# No OIDC provider setup needed per cluster

# Step 1: Install the Pod Identity Agent add-on
aws eks create-addon \
  --cluster-name production \
  --addon-name eks-pod-identity-agent

# Step 2: Create the association directly
aws eks create-pod-identity-association \
  --cluster-name production \
  --namespace production \
  --service-account data-processor \
  --role-arn arn:aws:iam::123456789012:role/data-processor-role
```

Pod Identity is simpler because you don't need to manage OIDC provider trust policies per cluster. The association is managed by EKS directly.

---

## Implementation: GCP (Workload Identity)

```bash
# Step 1: Enable Workload Identity on the cluster (if not already)
gcloud container clusters update production \
  --region us-central1 \
  --workload-pool=my-project.svc.id.goog

# Step 2: Create a GCP service account
gcloud iam service-accounts create data-processor \
  --display-name="Data Processor K8s Workload"

# Step 3: Grant the GCP SA access to resources
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:data-processor@my-project.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" \
  --condition="expression=resource.name.startsWith('projects/_/buckets/patient-data'),title=patient-data-only"

# Step 4: Bind K8s SA to GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  data-processor@my-project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-project.svc.id.goog[production/data-processor]"
```

```yaml
# Step 5: Annotate the Kubernetes ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-processor
  namespace: production
  annotations:
    iam.gke.io/gcp-service-account: data-processor@my-project.iam.gserviceaccount.com
```

## Implementation: Azure (Workload Identity)

```bash
# Step 1: Enable Workload Identity on the cluster
az aks update \
  --resource-group production-rg \
  --name production \
  --enable-oidc-issuer \
  --enable-workload-identity

# Step 2: Get the OIDC issuer URL
OIDC_ISSUER=$(az aks show \
  --resource-group production-rg \
  --name production \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Step 3: Create a managed identity
az identity create \
  --name data-processor-identity \
  --resource-group production-rg

CLIENT_ID=$(az identity show \
  --name data-processor-identity \
  --resource-group production-rg \
  --query "clientId" -o tsv)

# Step 4: Create federated credential
az identity federated-credential create \
  --name data-processor-fed \
  --identity-name data-processor-identity \
  --resource-group production-rg \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:production:data-processor" \
  --audiences "api://AzureADTokenExchange"

# Step 5: Grant access to Azure resources
az role assignment create \
  --assignee "$CLIENT_ID" \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/.../resourceGroups/.../providers/Microsoft.Storage/storageAccounts/patientdata"
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-processor
  namespace: production
  annotations:
    azure.workload.identity/client-id: "12345678-abcd-efgh-ijkl-123456789012"
  labels:
    azure.workload.identity/use: "true"
```

---

## Auditing Cloud API Calls Back to Pods

One of the most powerful benefits of federated identity is auditability. Every cloud API call made by a pod is logged with the assumed role's session name, which includes the pod identity.

```bash
# AWS CloudTrail: Find all S3 calls made by the data-processor pod
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::S3::Object \
  --query 'Events[?contains(CloudTrailEvent, `data-processor`)].CloudTrailEvent' \
  --output text | jq -r '
    select(.userIdentity.type == "AssumedRole") |
    {
      time: .eventTime,
      action: .eventName,
      resource: .requestParameters.bucketName,
      role: .userIdentity.arn,
      sourceIP: .sourceIPAddress,
      sessionIssuer: .userIdentity.sessionContext.sessionIssuer.userName
    }
  '

# Example output:
# {
#   "time": "2026-03-24T10:15:23Z",
#   "action": "GetObject",
#   "resource": "patient-data-bucket",
#   "role": "arn:aws:sts::123456789012:assumed-role/data-processor-role/...",
#   "sourceIP": "10.0.42.17",
#   "sessionIssuer": "data-processor-role"
# }
```

This gives you a complete audit trail: which pod, which ServiceAccount, which IAM role, which cloud resource, at what time. Compare this to the static key approach where the audit log just shows "IAM user data-processor-user" with no context about which pod or even which cluster made the call.

### Cross-Referencing with Kubernetes Audit Logs

```bash
# Kubernetes audit log shows which user/SA created the pod
# Combined with CloudTrail, you get end-to-end traceability:
#
# 1. Developer "alice@company.com" deploys data-processor (K8s audit)
# 2. Pod "data-processor-7d4b8c9f" starts (K8s events)
# 3. Pod assumes role "data-processor-role" (CloudTrail)
# 4. Pod reads "patient-data-bucket/file.json" (CloudTrail)
#
# Full chain: Human → Deployment → Pod → Cloud Resource
```

---

## Least Privilege at Pod Level

The principle of least privilege means each pod should have only the permissions it needs and nothing more. Here's how to implement it rigorously.

### One ServiceAccount Per Workload

```yaml
# BAD: Shared ServiceAccount with broad permissions
# Every pod in the namespace uses "default" SA
# with a role that has S3 + DynamoDB + SQS + SNS access

# GOOD: Dedicated ServiceAccounts with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-processor     # Can only write to orders DynamoDB table
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/order-processor
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: notification-sender  # Can only publish to notifications SNS topic
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/notification-sender
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: report-generator     # Can only read from S3 analytics bucket
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/report-generator
```

### Preventing ServiceAccount Token Theft

Even with short-lived tokens, a compromised pod could use its token to assume the IAM role from outside the cluster. Add condition keys to restrict where the role can be assumed from.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890:sub": "system:serviceaccount:production:data-processor",
          "oidc.eks.us-east-1.amazonaws.com/id/ABCDEF1234567890:aud": "sts.amazonaws.com"
        },
        "StringEquals": {
          "aws:SourceVpc": "vpc-0abc123def456"
        }
      }
    }
  ]
}
```

The `IpAddress` condition ensures the role can only be assumed from your VPC's CIDR range. Even if the token is exfiltrated, it's useless from outside your network.

---

## Did You Know?

- **Kubernetes ServiceAccount tokens were originally non-expiring JWTs stored as Secrets.** Before Kubernetes 1.22, every ServiceAccount automatically got a permanent token stored in a Secret object. These tokens never expired and were mounted into every pod by default. The shift to projected, time-bound tokens in 1.22+ was one of the most important security improvements in Kubernetes history -- and many clusters still have legacy non-expiring tokens lying around.

- **AWS processes over 500 million `AssumeRoleWithWebIdentity` calls per day** from EKS clusters alone. This API is the busiest STS endpoint globally. Each call involves verifying the JWT signature against the cluster's OIDC public keys, checking the trust policy, and issuing temporary credentials -- all in under 100 milliseconds.

- **The "confused deputy problem" was first described in a 1988 paper** by Norm Hardy, using the example of a compiler that could write to any file because it ran with elevated privileges. A user tricked the compiler into overwriting the system's billing file. The same concept applies today: a service with broad permissions acting on behalf of a less-privileged caller without verifying the caller's authority.

- **Google's Workload Identity Federation supports 100+ external identity providers**, not just GKE. You can federate identity from AWS, Azure, GitHub Actions, GitLab CI, and any OIDC-compliant provider. This means a GitHub Actions workflow can assume a GCP service account without any stored secrets -- the CI runner's OIDC token is sufficient.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using the default ServiceAccount | Pods use "default" SA unless explicitly configured | Always create and assign dedicated ServiceAccounts. Set `automountServiceAccountToken: false` on the default SA |
| Overly broad IAM policies | Developer uses managed policy like `AmazonS3FullAccess` for convenience | Write custom policies scoped to specific resources (bucket ARN, table name) |
| Not restricting trust policy audience | Trust policy missing `aud` condition | Always include audience condition (`sts.amazonaws.com` for AWS) to prevent token reuse |
| Forgetting to test token refresh | Works initially but breaks after token expiry (1hr or 24hr) | Run long-lived load tests to verify the SDK refreshes tokens automatically |
| One IAM role for entire namespace | "All services in production share one role" | One role per ServiceAccount. Blast radius of a compromise is one service, not the whole namespace |
| Not auditing AssumeRole calls | CloudTrail configured but nobody reviews it | Set up alerts for unexpected AssumeRoleWithWebIdentity calls (wrong source IP, unusual time) |
| Leaving legacy token Secrets | Old non-expiring SA token Secrets still exist in cluster | Audit and delete Secrets of type `kubernetes.io/service-account-token`. Use projected tokens only |
| Skipping IP condition on trust policy | Trusting any source that presents a valid token | Add `aws:SourceIp` or `aws:SourceVpc` condition to restrict where roles can be assumed from |

---

## Quiz

<details>
<summary>1. Why is storing AWS access keys as Kubernetes Secrets fundamentally insecure, even with RBAC restricting who can read the Secret?</summary>

Several reasons compound the risk. First, Kubernetes Secrets are base64-encoded, not encrypted, in etcd by default (encryption at rest requires explicit configuration). Anyone with etcd access can read them in plaintext. Second, RBAC can restrict who reads Secrets via the API, but the Secret is mounted as a file in every pod that references it -- a compromised container can read the filesystem. Third, static keys have no expiration, so a stolen key works forever until manually rotated. Fourth, Secrets can appear in etcd backups, logs (if accidentally printed), and CI/CD pipelines. Fifth, the key works from anywhere on the internet -- there's no network restriction by default. Federated identity solves all of these: no secret is stored, tokens are short-lived, and credentials are scoped to the pod's network location.
</details>

<details>
<summary>2. Trace the complete OIDC token exchange flow from pod startup to cloud API call.</summary>

1. Pod starts with a ServiceAccount that has an IAM role annotation. 2. The Kubernetes API server generates a signed JWT token (projected service account token) containing the pod's identity (namespace, SA name, pod name) and an audience claim (e.g., `sts.amazonaws.com`). 3. This token is mounted into the pod at a known path. 4. When the application makes an AWS API call, the AWS SDK detects the projected token and calls STS `AssumeRoleWithWebIdentity`, passing the token and the target role ARN. 5. STS fetches the cluster's OIDC public keys from the JWKS endpoint, verifies the token signature, checks expiration, and validates the audience. 6. STS checks the IAM role's trust policy to confirm the token's subject (SA identity) is allowed to assume this role. 7. If all checks pass, STS returns temporary credentials (access key, secret key, session token) valid for 15 minutes. 8. The SDK uses these temporary credentials for the actual cloud API call.
</details>

<details>
<summary>3. What is the confused deputy problem, and how does per-pod identity prevent it?</summary>

The confused deputy problem occurs when a trusted service with elevated permissions is tricked into performing actions on behalf of a less-privileged entity. For example, a CI/CD tool with broad deployment permissions might be exploited by a compromised pod to deploy malicious workloads. The CI/CD tool is the "confused deputy" -- it acts using its own elevated credentials on behalf of a caller whose actual permissions wouldn't allow the action.

Per-pod identity prevents this because the cloud provider authenticates the original caller (the pod's ServiceAccount), not the intermediary service. Even if a compromised pod calls through a privileged service, the cloud API call uses the pod's own identity. The trust policy on the IAM role verifies: "Is this specific ServiceAccount authorized?" -- not "Is the service this request came through authorized?"
</details>

<details>
<summary>4. Why should you add an IP address condition to IAM trust policies for IRSA roles?</summary>

Without an IP condition, a stolen projected token can be used from anywhere. If an attacker exfiltrates the JWT from a compromised pod (by reading the mounted token file), they can call `AssumeRoleWithWebIdentity` from their own machine using the stolen token. The token is cryptographically valid (signed by the cluster), the trust policy conditions match (correct subject and audience), and STS will issue credentials.

Adding an `aws:SourceIp` condition restricting role assumption to your VPC's CIDR range means the stolen token is useless from outside your network. The attacker would need to be inside your VPC to use it, which dramatically raises the bar for exploitation. This is defense in depth: even if token theft occurs, the blast radius is contained.
</details>

<details>
<summary>5. A developer creates one IAM role with S3, DynamoDB, SQS, and SNS permissions, then uses it for all ServiceAccounts in the production namespace. What are the risks?</summary>

This violates least privilege. If any single pod in the namespace is compromised, the attacker gains access to all four services -- S3, DynamoDB, SQS, and SNS. The blast radius is the entire namespace's cloud surface area instead of a single service's access scope.

Additionally, this makes auditing meaningless. CloudTrail logs show the same role ARN for every pod, making it impossible to distinguish which service made which call. You lose the ability to detect anomalous behavior (e.g., a notification service suddenly reading from S3).

The fix: one IAM role per ServiceAccount, each with the minimum permissions that specific workload needs. The order-processor gets DynamoDB write access only; the notification-sender gets SNS publish only; the report-generator gets S3 read only.
</details>

<details>
<summary>6. EKS Pod Identity was introduced after IRSA. What problem does it solve that IRSA doesn't?</summary>

IRSA requires you to set up and manage the OIDC provider trust relationship in IAM for each EKS cluster. When you have many clusters (10, 50, 100), each cluster needs its own OIDC provider registered in IAM, and each IAM trust policy must reference the specific cluster's OIDC issuer URL. This creates management overhead and long, complex trust policies.

EKS Pod Identity simplifies this by handling the association at the EKS level. Instead of configuring trust policies with OIDC issuer URLs, you create a pod identity association directly in EKS. The trust policy on the IAM role simply trusts the EKS Pod Identity service principal, regardless of which specific cluster the pod runs in. This is cleaner for fleet management, reduces IAM policy complexity, and makes it easier to move workloads between clusters without updating trust policies.
</details>

---

## Hands-On Exercise: Build a Zero-Trust Pod Identity Model

You're securing a microservices application that currently uses static AWS credentials. You'll design and implement a zero-trust identity model using OIDC federation.

### Context

The application has four microservices:

| Service | Cloud Resources Needed | Current Auth |
|---------|----------------------|-------------|
| `order-api` | DynamoDB (orders table, read/write) | Shared IAM user key |
| `payment-processor` | SQS (payment queue, send/receive), KMS (encrypt/decrypt) | Shared IAM user key |
| `notification-service` | SNS (notifications topic, publish only) | Shared IAM user key |
| `analytics-pipeline` | S3 (analytics bucket, read only), Athena (query) | Shared IAM user key |

All four services currently share one IAM user (`app-user`) with `AdministratorAccess`. Yes, really.

### Task 1: Design the IAM Role Architecture

For each service, define: the IAM role name, the trust policy, and the permission policy. Follow least privilege.

<details>
<summary>Solution</summary>

```json
// Role 1: order-api-role
// Trust: system:serviceaccount:production:order-api
// Permissions:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ],
    "Resource": [
      "arn:aws:dynamodb:us-east-1:123456789012:table/orders",
      "arn:aws:dynamodb:us-east-1:123456789012:table/orders/index/*"
    ]
  }]
}

// Role 2: payment-processor-role
// Trust: system:serviceaccount:production:payment-processor
// Permissions:
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:payment-queue"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/payment-key-id"
    }
  ]
}

// Role 3: notification-service-role
// Trust: system:serviceaccount:production:notification-service
// Permissions:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sns:Publish",
    "Resource": "arn:aws:sns:us-east-1:123456789012:notifications"
  }]
}

// Role 4: analytics-pipeline-role
// Trust: system:serviceaccount:production:analytics-pipeline
// Permissions:
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::analytics-data",
        "arn:aws:s3:::analytics-data/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryResults",
        "athena:GetQueryExecution"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "athena:workGroup": "analytics"
        }
      }
    }
  ]
}
```
</details>

### Task 2: Write the Kubernetes Manifests

Create ServiceAccount and Deployment manifests for each service using IRSA.

<details>
<summary>Solution</summary>

```yaml
# serviceaccounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-api
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/order-api-role
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: payment-processor
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/payment-processor-role
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: notification-service
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/notification-service-role
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: analytics-pipeline
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/analytics-pipeline-role
---
# Disable auto-mount on the default SA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default
  namespace: production
automountServiceAccountToken: false
```

```yaml
# deployments.yaml (showing order-api as example)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-api
  template:
    metadata:
      labels:
        app: order-api
    spec:
      serviceAccountName: order-api
      containers:
        - name: order-api
          image: company/order-api:v2.1
          ports:
            - containerPort: 8080
          env:
            - name: AWS_REGION
              value: "us-east-1"
            - name: DYNAMODB_TABLE
              value: "orders"
            # NO AWS_ACCESS_KEY_ID
            # NO AWS_SECRET_ACCESS_KEY
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
```
</details>

### Task 3: Design the Migration Plan

You need to migrate from static credentials to IRSA without downtime. Write the step-by-step plan.

<details>
<summary>Solution</summary>

**Migration Plan: Static Credentials to IRSA (Zero Downtime)**

```
Phase 1: Parallel Permissions (Week 1)
  - Create all 4 IAM roles with IRSA trust policies
  - Attach permission policies to each role
  - DO NOT remove the existing IAM user yet
  - Both auth methods work simultaneously

Phase 2: Rolling Migration (Week 2)
  For each service, one at a time:
  1. Create the new ServiceAccount with IRSA annotation
  2. Update the Deployment to use the new ServiceAccount
  3. Remove the envFrom referencing aws-credentials Secret
  4. Deploy with rolling update (zero downtime)
  5. Verify cloud API calls succeed (check CloudTrail)
  6. Monitor for 24 hours before moving to next service

Phase 3: Cleanup (Week 3)
  - Verify no pods still reference the old Secret
  - Delete the aws-credentials Kubernetes Secret
  - Disable the IAM user's access key (don't delete yet)
  - Wait 1 week for any stragglers

Phase 4: Decommission (Week 4)
  - Delete the IAM user's access key
  - Delete the IAM user
  - Remove AdministratorAccess policy (was attached to user)
  - Document the new architecture in runbooks
```

Key risk mitigation:
- Parallel auth during transition means rollback is instant (re-add Secret reference)
- One service at a time limits blast radius
- 24-hour monitoring window catches issues before proceeding
- IAM user not deleted until all services confirmed working for a full week
</details>

### Task 4: Write an Audit Query

Write a CloudTrail query that detects anomalous cloud API access -- calls that might indicate a compromised pod.

<details>
<summary>Solution</summary>

```bash
# CloudTrail Insights: Detect anomalous AssumeRoleWithWebIdentity calls

# Query 1: Calls from unexpected source IPs (outside VPC)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --start-time "2026-03-23T00:00:00Z" \
  --end-time "2026-03-24T23:59:59Z" \
  --query 'Events[].CloudTrailEvent' \
  --output text | jq -r '
    select(.sourceIPAddress != null) |
    select(.sourceIPAddress | test("^10\\.") | not) |
    {
      time: .eventTime,
      sourceIP: .sourceIPAddress,
      role: .requestParameters.roleArn,
      subject: .requestParameters.roleSessionName,
      error: .errorCode
    }
  '

# Query 2: Failed AssumeRole attempts (potential probing)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --query 'Events[?contains(CloudTrailEvent, `AccessDenied`)].CloudTrailEvent' \
  --output text | jq -r '{
    time: .eventTime,
    source: .sourceIPAddress,
    attemptedRole: .requestParameters.roleArn,
    error: .errorMessage
  }'

# Query 3: Unusual API calls for a specific role
# (e.g., the order-api role calling S3 -- it shouldn't)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=order-api-role \
  --query 'Events[].CloudTrailEvent' \
  --output text | jq -r '
    select(.eventName | test("^(GetObject|PutObject|ListBucket)")) |
    {
      alert: "ORDER-API ROLE ACCESSING S3 - UNEXPECTED",
      time: .eventTime,
      action: .eventName,
      resource: .requestParameters.bucketName
    }
  '
```
</details>

### Success Criteria

- [ ] Designed one IAM role per service with least-privilege permissions
- [ ] Trust policies specify exact ServiceAccount and audience
- [ ] Kubernetes manifests use projected tokens (no static credentials)
- [ ] Default ServiceAccount has automountServiceAccountToken disabled
- [ ] Migration plan ensures zero downtime
- [ ] Audit queries can detect anomalous behavior

---

## Next Module

[Module 4.4: Cloud-Native Networking and VPC Topologies](module-4.4-vpc-topologies/) -- Identity tells you *who* can access resources. Networking tells you *how* traffic flows between them. We'll design VPC architectures that keep your Kubernetes clusters connected, secure, and free from the dreaded IP exhaustion problem.
