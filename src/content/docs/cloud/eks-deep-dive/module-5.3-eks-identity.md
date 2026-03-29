---
title: "Module 5.3: EKS Identity: IRSA vs Pod Identity"
slug: cloud/eks-deep-dive/module-5.3-eks-identity
sidebar:
  order: 4
---
**Complexity**: [QUICK] | **Time to Complete**: 1.5h | **Prerequisites**: Module 5.1 (EKS Architecture & Control Plane)

## Why This Module Matters

In 2022, a healthcare SaaS company running on EKS discovered that every pod in their cluster had full access to their S3 buckets containing patient health records. The reason was painfully simple: their developers had attached an IAM instance profile with `s3:*` permissions to the node group. Since EC2 instance metadata is available to all pods on a node, any compromised pod -- including a logging sidecar from a third-party vendor -- could read, write, and delete HIPAA-protected data from any bucket. The security team discovered this during a compliance audit, not during development. The remediation involved rewriting IAM policies for 60 microservices and took three months.

This is the "node-level blast radius" problem. Without pod-level identity, every pod inherits whatever IAM permissions are attached to the underlying EC2 node. A vulnerability in one pod gives an attacker the combined permissions of every workload running on that node. The solution is pod-level IAM identity: giving each pod only the specific AWS permissions it needs, and nothing more.

EKS offers two mechanisms for this: **IAM Roles for Service Accounts (IRSA)**, which has been available since 2019, and **EKS Pod Identity**, which launched in late 2023 as a simpler replacement. In this module, you will understand how both systems work, when to use each, and how to migrate from IRSA to Pod Identity. You will also learn how to troubleshoot the most common STS errors that plague EKS identity configurations.

---

## The Problem: Node-Level IAM Is Dangerous

Before IRSA and Pod Identity existed, the only way to give pods AWS access was through the node's IAM instance profile. This is still the default if you do nothing else.

```text
EC2 Instance (Node)
IAM Role: eks-node-role
Permissions: s3:*, dynamodb:*, sqs:*, secretsmanager:*

┌─────────────────────────────────────────────┐
│                                             │
│  Pod A (web-frontend)     ← needs: nothing  │
│  Pod B (order-service)    ← needs: dynamodb │
│  Pod C (image-processor)  ← needs: s3       │
│  Pod D (notification-svc) ← needs: sqs      │
│                                             │
│  ALL FOUR PODS GET: s3 + dynamodb + sqs +   │
│  secretsmanager (full node role!)            │
└─────────────────────────────────────────────┘
```

If an attacker exploits a vulnerability in Pod A (which should not need any AWS access at all), they can reach the instance metadata service at `169.254.169.254` and obtain temporary credentials for the node role -- giving them access to DynamoDB, S3, SQS, and Secrets Manager.

Pod-level identity solves this:

```text
EC2 Instance (Node)
IAM Role: eks-node-role (minimal: ECR pull, EBS CSI only)

┌─────────────────────────────────────────────┐
│                                             │
│  Pod A (web-frontend)     → IAM: none       │
│  Pod B (order-service)    → IAM: dynamodb   │
│  Pod C (image-processor)  → IAM: s3-bucket  │
│  Pod D (notification-svc) → IAM: sqs-queue  │
│                                             │
│  Each pod gets ONLY its own credentials     │
└─────────────────────────────────────────────┘
```

---

## IRSA: IAM Roles for Service Accounts (The Legacy Approach)

IRSA was the first solution to pod-level identity on EKS. It works by leveraging OpenID Connect (OIDC) to establish a trust relationship between your EKS cluster and IAM.

### How IRSA Works

The flow involves four components: the EKS OIDC provider, IAM, the pod's service account, and the AWS SDK inside the pod.

```text
Step 1: Cluster Setup (one-time)
┌──────────────┐         ┌────────────┐
│ EKS Cluster  │────────►│ IAM OIDC   │
│ issues OIDC  │         │ Provider   │
│ tokens       │         │ (trust)    │
└──────────────┘         └────────────┘

Step 2: Pod Startup
┌──────────────┐    projected token    ┌────────────┐
│ kubelet      │──────────────────────►│ Pod        │
│ injects:     │                       │            │
│ - JWT token  │   AWS_ROLE_ARN env    │ /var/run/  │
│ - Role ARN   │──────────────────────►│ secrets/   │
│ - Token path │                       │ eks.amazonaws│
└──────────────┘                       │ .com/...   │
                                       └─────┬──────┘

Step 3: AWS API Call
┌──────────────┐    AssumeRoleWithWebIdentity    ┌────────────┐
│ Pod (AWS SDK)│────────────────────────────────►│ AWS STS    │
│ sends JWT +  │                                 │            │
│ role ARN     │◄────────────────────────────────│ Returns    │
│              │    Temporary credentials        │ creds      │
└──────────────┘                                 └────────────┘
```

### Setting Up IRSA

**Step 1: Create the OIDC provider for your cluster.**

```bash
# Get the OIDC issuer URL
OIDC_ISSUER=$(aws eks describe-cluster --name my-cluster \
  --query 'cluster.identity.oidc.issuer' --output text)

# Check if the provider already exists
aws iam list-open-id-connect-providers | grep $(echo $OIDC_ISSUER | cut -d'/' -f5)

# If not, create it
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve

# Or manually:
OIDC_ID=$(echo $OIDC_ISSUER | cut -d'/' -f5)
THUMBPRINT=$(openssl s_client -servername oidc.eks.us-east-1.amazonaws.com \
  -connect oidc.eks.us-east-1.amazonaws.com:443 2>/dev/null | \
  openssl x509 -fingerprint -noout | cut -d'=' -f2 | tr -d ':')

aws iam create-open-id-connect-provider \
  --url $OIDC_ISSUER \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list $THUMBPRINT
```

**Step 2: Create an IAM role with a trust policy referencing the OIDC provider.**

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_ID=$(aws eks describe-cluster --name my-cluster \
  --query 'cluster.identity.oidc.issuer' --output text | cut -d'/' -f5)

cat > /tmp/irsa-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/${OIDC_ID}"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.us-east-1.amazonaws.com/id/${OIDC_ID}:aud": "sts.amazonaws.com",
        "oidc.eks.us-east-1.amazonaws.com/id/${OIDC_ID}:sub": "system:serviceaccount:production:order-service-sa"
      }
    }
  }]
}
EOF

aws iam create-role \
  --role-name OrderServiceRole \
  --assume-role-policy-document file:///tmp/irsa-trust-policy.json

aws iam attach-role-policy \
  --role-name OrderServiceRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess
```

**Step 3: Annotate the Kubernetes ServiceAccount with the role ARN.**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-service-sa
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/OrderServiceRole
```

**Step 4: Use the ServiceAccount in your pod.**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      serviceAccountName: order-service-sa
      containers:
        - name: app
          image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/order-service:latest
          # AWS SDK automatically detects IRSA credentials
          # No AWS_ACCESS_KEY_ID needed!
```

### IRSA Pain Points

IRSA works, but it has real operational friction:

1. **OIDC provider management**: You must create and manage the OIDC provider per cluster, per region
2. **Trust policy complexity**: Each role's trust policy includes the full OIDC issuer URL, making it cluster-specific and hard to reuse across clusters
3. **Thumbprint rotation**: The OIDC provider's TLS certificate thumbprint must be updated when certificates rotate
4. **No native AWS API**: IRSA is configured through Kubernetes annotations, not the AWS API, making it invisible to IAM teams
5. **Cross-account complexity**: Setting up IRSA across accounts requires OIDC provider federation in the target account

---

## EKS Pod Identity: The Modern Approach

EKS Pod Identity, launched in November 2023, replaces IRSA with a simpler, AWS-native approach. Instead of OIDC federation, Pod Identity uses an agent running on each node to inject credentials directly into pods.

### How Pod Identity Works

```text
Step 1: Association (AWS API)
┌──────────────┐         ┌────────────────────┐
│ eks:          │────────►│ Pod Identity       │
│ CreatePod    │         │ Association        │
│ Identity     │         │ (cluster + SA +    │
│ Association  │         │  namespace → Role) │
└──────────────┘         └────────────────────┘

Step 2: Pod Startup
┌──────────────┐    projected token    ┌────────────────┐
│ kubelet      │──────────────────────►│ Pod Identity   │
│              │                       │ Agent (DaemonSet│
│              │                       │ on node)       │
│              │                       └───────┬────────┘
│              │                               │
│              │                       exchanges token
│              │                       for credentials
│              │                               │
│              │                       ┌───────▼────────┐
│              │                       │ AWS STS        │
│              │                       │ (AssumeRole    │
│              │                       │  ForPodIdentity│
│              │                       │  )             │
│              │                       └───────┬────────┘
│              │                               │
│              │     credentials injected      │
│              │◄──────────────────────────────┘
└──────────────┘
```

The key difference: Pod Identity does not require an OIDC provider, does not need role trust policy modifications with cluster-specific OIDC URLs, and is managed entirely through the AWS EKS API.

### Setting Up Pod Identity

**Step 1: Install the Pod Identity Agent add-on.**

```bash
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name eks-pod-identity-agent \
  --addon-version v1.3.4-eksbuild.1

# Verify the agent is running
k get daemonset eks-pod-identity-agent -n kube-system
k get pods -n kube-system -l app.kubernetes.io/name=eks-pod-identity-agent
```

**Step 2: Create an IAM role with a Pod Identity trust policy.**

```bash
cat > /tmp/pod-identity-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "pods.eks.amazonaws.com"
    },
    "Action": [
      "sts:AssumeRole",
      "sts:TagSession"
    ]
  }]
}
EOF

aws iam create-role \
  --role-name OrderServiceRole-PodIdentity \
  --assume-role-policy-document file:///tmp/pod-identity-trust.json

aws iam attach-role-policy \
  --role-name OrderServiceRole-PodIdentity \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess
```

Notice the trust policy: it trusts `pods.eks.amazonaws.com` as a service principal. There is no cluster-specific OIDC URL. This means the same role can be used across any EKS cluster in the account without modifying the trust policy.

**Step 3: Create the Pod Identity Association.**

```bash
aws eks create-pod-identity-association \
  --cluster-name my-cluster \
  --namespace production \
  --service-account order-service-sa \
  --role-arn arn:aws:iam::123456789012:role/OrderServiceRole-PodIdentity
```

**Step 4: Create the ServiceAccount (no annotation needed!).**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-service-sa
  namespace: production
  # No eks.amazonaws.com/role-arn annotation needed!
```

That is it. Any pod using this ServiceAccount in the `production` namespace will automatically receive credentials for the associated IAM role. No OIDC provider, no trust policy per cluster, no annotation.

### IRSA vs Pod Identity: Complete Comparison

| Feature | IRSA | Pod Identity |
| :--- | :--- | :--- |
| **Setup complexity** | OIDC provider + trust policy per cluster | Install agent add-on + one API call |
| **Trust policy** | Cluster-specific (contains OIDC URL) | Generic (`pods.eks.amazonaws.com` service principal) |
| **Cross-cluster reuse** | Requires trust policy update per cluster | Same role works across all clusters |
| **Cross-account** | OIDC provider in target account + federation | Simpler: trust policy + association |
| **Management API** | kubectl (annotations) | AWS EKS API (CloudTrail logged) |
| **Credential delivery** | STS `AssumeRoleWithWebIdentity` | Pod Identity Agent on node |
| **OIDC provider** | Required | Not required |
| **Audit trail** | Limited (ConfigMap + annotation changes) | Full CloudTrail logging |
| **Kubernetes version** | 1.14+ | 1.24+ |
| **Maturity** | Established (since 2019) | Newer (since 2023), rapidly adopted |

### When to Still Use IRSA

Pod Identity is the recommended approach for new setups, but IRSA is still necessary in a few scenarios:

- EKS clusters running Kubernetes versions below 1.24
- Self-managed Kubernetes on EC2 (not EKS) with OIDC federation
- Edge cases where you need the OIDC token itself (not just AWS credentials) for non-AWS identity providers

---

## Cross-Account Access

Both IRSA and Pod Identity support cross-account IAM role assumption, but the setup differs significantly.

### Cross-Account with Pod Identity

```text
Account A (EKS Cluster)              Account B (DynamoDB)
┌──────────────────────┐             ┌──────────────────────┐
│ Pod with SA          │             │ DynamoDB Table       │
│   │                  │             │                      │
│   ▼                  │             │ Role: CrossAcctRole  │
│ Pod Identity Agent   │             │ Trust: Account A     │
│   │                  │             │ role ARN             │
│   ▼                  │             └──────────────────────┘
│ Assume Local Role    │                       ▲
│   │                  │                       │
│   ▼                  │                       │
│ Chain: AssumeRole ───┼───────────────────────┘
│ into Account B       │
└──────────────────────┘
```

```bash
# In Account A: Create the pod's role with cross-account assume permission
cat > /tmp/pod-role-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sts:AssumeRole",
    "Resource": "arn:aws:iam::222222222222:role/CrossAccountDynamoDBRole"
  }]
}
EOF

aws iam put-role-policy \
  --role-name OrderServiceRole-PodIdentity \
  --policy-name CrossAccountAssume \
  --policy-document file:///tmp/pod-role-policy.json

# In Account B: Create the target role with trust back to Account A's pod role
cat > /tmp/cross-account-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::111111111111:role/OrderServiceRole-PodIdentity"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
  --role-name CrossAccountDynamoDBRole \
  --assume-role-policy-document file:///tmp/cross-account-trust.json

aws iam attach-role-policy \
  --role-name CrossAccountDynamoDBRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess
```

In the application code, you chain the role assumption:

```python
import boto3

# First, get credentials from Pod Identity (automatic)
sts_client = boto3.client('sts')

# Then, assume the cross-account role
response = sts_client.assume_role(
    RoleArn='arn:aws:iam::222222222222:role/CrossAccountDynamoDBRole',
    RoleSessionName='order-service-cross-account'
)

# Use the cross-account credentials
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    aws_access_key_id=response['Credentials']['AccessKeyId'],
    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
    aws_session_token=response['Credentials']['SessionToken']
)

table = dynamodb.Table('orders')
```

---

## Troubleshooting STS Errors

Identity issues on EKS produce some of the most confusing error messages in all of AWS. Here is your troubleshooting guide.

### Error: "An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity"

This is the most common IRSA error. The OIDC provider, trust policy, or service account does not match.

```bash
# 1. Verify the OIDC provider exists
aws iam list-open-id-connect-providers

# 2. Check the role's trust policy
aws iam get-role --role-name OrderServiceRole \
  --query 'Role.AssumeRolePolicyDocument' --output json

# 3. Verify the service account annotation
k get sa order-service-sa -n production -o json | \
  jq '.metadata.annotations["eks.amazonaws.com/role-arn"]'

# 4. Check the projected token inside the pod
k exec -it order-service-pod -n production -- \
  cat /var/run/secrets/eks.amazonaws.com/serviceaccount/token | \
  cut -d'.' -f2 | base64 -d 2>/dev/null | jq '.iss, .sub, .aud'
```

### Error: "No credentials provider found" or "Unable to locate credentials"

The AWS SDK is not detecting the injected credentials.

```bash
# Check that the environment variables are set in the pod
k exec -it order-service-pod -n production -- env | grep AWS

# For IRSA, you should see:
# AWS_ROLE_ARN=arn:aws:iam::123456789012:role/OrderServiceRole
# AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token

# For Pod Identity, you should see:
# AWS_CONTAINER_CREDENTIALS_FULL_URI=http://169.254.170.23/v1/credentials
# AWS_CONTAINER_AUTHORIZATION_TOKEN=<token>
```

### Error: "ExpiredTokenException"

The service account token has expired. IRSA tokens have a default lifetime of 24 hours.

```bash
# Check token expiry
k exec -it order-service-pod -n production -- \
  cat /var/run/secrets/eks.amazonaws.com/serviceaccount/token | \
  cut -d'.' -f2 | base64 -d 2>/dev/null | jq '.exp' | \
  xargs -I{} date -d @{}

# If expired, ensure the pod is using a current SDK that supports token refresh
# AWS SDK v2 (Go), Boto3 1.24+, and AWS SDK for Java v2 all support auto-refresh
```

### Debugging Checklist

```text
IRSA Not Working? Check in this order:
 1. OIDC provider exists?          → aws iam list-open-id-connect-providers
 2. Trust policy OIDC URL matches? → Compare cluster OIDC issuer with trust policy
 3. SA namespace:name matches?     → Trust policy "sub" condition must match exactly
 4. SA annotation correct?         → eks.amazonaws.com/role-arn must be set
 5. Pod using the right SA?        → spec.serviceAccountName set correctly
 6. Token file mounted?            → ls /var/run/secrets/eks.amazonaws.com/
 7. AWS SDK version supports IRSA? → Needs SDK from 2019+ with web identity support

Pod Identity Not Working? Check in this order:
 1. Agent add-on installed?        → k get ds eks-pod-identity-agent -n kube-system
 2. Agent pods running?            → k get pods -n kube-system -l app...=eks-pod-identity-agent
 3. Association exists?            → aws eks list-pod-identity-associations --cluster-name X
 4. Trust policy correct?          → Must trust pods.eks.amazonaws.com with sts:TagSession
 5. SA name and namespace match?   → Association must match exactly
 6. Env vars injected?             → AWS_CONTAINER_CREDENTIALS_FULL_URI set in pod
```

---

## Migration: IRSA to Pod Identity

Migrating from IRSA to Pod Identity can be done incrementally, service by service, with zero downtime.

### Migration Steps Per Service

```bash
# 1. Install the Pod Identity Agent (if not already)
aws eks create-addon --cluster-name my-cluster \
  --addon-name eks-pod-identity-agent

# 2. Create a new role with Pod Identity trust (or update existing)
cat > /tmp/pod-identity-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"]
  }]
}
EOF

aws iam update-assume-role-policy \
  --role-name OrderServiceRole \
  --policy-document file:///tmp/pod-identity-trust.json

# 3. Create the Pod Identity Association
aws eks create-pod-identity-association \
  --cluster-name my-cluster \
  --namespace production \
  --service-account order-service-sa \
  --role-arn arn:aws:iam::123456789012:role/OrderServiceRole

# 4. Remove the IRSA annotation from the ServiceAccount
k annotate sa order-service-sa -n production \
  eks.amazonaws.com/role-arn-

# 5. Restart pods to pick up new credential delivery
k rollout restart deployment order-service -n production

# 6. Verify pods are using Pod Identity (not IRSA)
k exec -it $(k get pods -n production -l app=order-service -o name | head -1) \
  -n production -- env | grep AWS
# Should show AWS_CONTAINER_CREDENTIALS_FULL_URI (Pod Identity)
# Should NOT show AWS_WEB_IDENTITY_TOKEN_FILE (IRSA)
```

> **Important**: If both IRSA annotation and Pod Identity association exist for the same service account, Pod Identity takes precedence. This means you can create the association first, then remove the annotation, and pods will seamlessly switch on their next restart.

---

## Did You Know?

1. IRSA uses the `sts:AssumeRoleWithWebIdentity` API call, which is subject to the same STS rate limits as all other AssumeRole calls. At large scale (thousands of pods restarting simultaneously during a deployment), IRSA can trigger STS throttling, causing pods to fail to obtain credentials. Pod Identity mitigates this with local credential caching on the agent, reducing STS API calls.

2. The Pod Identity Agent runs as a DaemonSet that listens on `169.254.170.23:80` and `169.254.170.23:2703` on each node. When the AWS SDK inside a pod makes a credential request, it is intercepted and redirected to this local agent rather than hitting the EC2 metadata service. The agent then exchanges the pod's service account token for temporary IAM credentials.

3. Before IRSA existed (2017-2019), the community tool `kiam` and later `kube2iam` were the only options for pod-level IAM. They worked by intercepting metadata requests using iptables rules and a node-level daemon. These tools were notoriously fragile -- iptables race conditions could cause pods to receive the wrong role's credentials. IRSA eliminated this entire class of bugs by using projected service account tokens instead of metadata interception.

4. When you delete a Pod Identity association, existing pods keep their current credentials until those credentials expire (typically within an hour). New credential requests will fail immediately. This gives you a grace period during migrations, but it also means that removing an association does not instantly revoke access -- you must also restart the pods if immediate revocation is required.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Using node IAM role for application access** | Easiest path: attach policies to the node role. All pods inherit access. | Use Pod Identity (or IRSA) to assign per-pod IAM roles. Strip the node role down to only ECR pull, EBS CSI, and basic node operations. |
| **IRSA trust policy with wrong namespace or SA name** | Copy-pasting trust policies and forgetting to update the `sub` condition. | The `sub` field must exactly match `system:serviceaccount:<namespace>:<sa-name>`. Double-check with `k get sa -n <namespace>`. |
| **Forgetting `sts:TagSession` in Pod Identity trust** | Copying IRSA trust policies that only have `sts:AssumeRoleWithWebIdentity`. | Pod Identity requires both `sts:AssumeRole` and `sts:TagSession` in the trust policy's Action array. Without `TagSession`, the association silently fails. |
| **Not restarting pods after migration** | Expecting IRSA-to-Pod-Identity switch to be live without pod restart. | Credential injection happens at pod start time. You must restart pods (rolling restart) to pick up new credential delivery. |
| **Using old AWS SDK that does not support IRSA/Pod Identity** | Running applications with SDK versions from before 2019 that do not understand web identity tokens. | Update to AWS SDK v2 (Go 1.17+), Boto3 1.24+, Java SDK v2.x, or Node.js SDK v3. All modern SDKs auto-detect both IRSA and Pod Identity. |
| **Pod Identity Agent not running on Fargate** | Assuming Pod Identity works everywhere. Fargate does not run DaemonSets. | Use IRSA for Fargate pods. Pod Identity requires the agent DaemonSet, which cannot run on Fargate. |
| **OIDC thumbprint not updated after certificate rotation** | The OIDC provider's TLS certificate changes and the thumbprint becomes stale. | AWS now automatically manages the thumbprint for EKS OIDC providers. If you created the provider manually, update the thumbprint using the AWS CLI. |
| **Overly broad IAM policies on pod roles** | "We will tighten it later." Later never comes. | Follow least privilege from day one. Use IAM Access Analyzer to generate minimum-required policies from CloudTrail logs after a burn-in period. |

---

## Quiz

<details>
<summary>Question 1: What is the fundamental security problem with relying on the EC2 instance profile for pod AWS access?</summary>

The instance profile's IAM role is shared by **every pod running on that node**. This means a compromised pod -- even one that should have no AWS access at all -- can access the EC2 metadata service at `169.254.169.254` and obtain temporary credentials with the full set of permissions attached to the node role. The blast radius is the union of all permissions needed by all workloads on that node, which violates the principle of least privilege. Pod Identity and IRSA solve this by giving each pod its own scoped IAM role.
</details>

<details>
<summary>Question 2: Why does Pod Identity not require an OIDC provider, while IRSA does?</summary>

IRSA uses **OpenID Connect federation** to establish trust between the EKS cluster and IAM. The cluster issues OIDC tokens, and IAM verifies them against the registered OIDC provider. This requires creating and maintaining an OIDC provider per cluster. Pod Identity uses a different mechanism: the **Pod Identity Agent** runs on each node and exchanges the pod's service account token for credentials by calling `sts:AssumeRoleForPodIdentity` directly. The trust is established through the `pods.eks.amazonaws.com` service principal in the IAM trust policy, which is a built-in AWS service identity. No external OIDC federation is needed.
</details>

<details>
<summary>Question 3: You set up a Pod Identity association, but the pod's AWS SDK returns "Unable to locate credentials." What three things should you check?</summary>

Check (1) the **Pod Identity Agent DaemonSet** is running on the node where your pod is scheduled -- look for the `eks-pod-identity-agent` pods in `kube-system`. If the agent pod is not running or is in CrashLoopBackOff, credentials cannot be injected. Check (2) the pod's **environment variables** -- you should see `AWS_CONTAINER_CREDENTIALS_FULL_URI` set to `http://169.254.170.23/v1/credentials`. If this is missing, the webhook that injects these variables may not be working. Check (3) the **association** matches the exact namespace and service account name using `aws eks list-pod-identity-associations --cluster-name my-cluster`.
</details>

<details>
<summary>Question 4: Can IRSA and Pod Identity coexist on the same cluster? What happens if a ServiceAccount has both an IRSA annotation and a Pod Identity association?</summary>

Yes, IRSA and Pod Identity can coexist on the same cluster simultaneously. If a ServiceAccount has both an IRSA annotation (`eks.amazonaws.com/role-arn`) and a Pod Identity association, **Pod Identity takes precedence**. The pod will receive credentials through the Pod Identity Agent, and the IRSA projected token will still be mounted but the AWS SDK will use the Pod Identity credentials first (because `AWS_CONTAINER_CREDENTIALS_FULL_URI` has higher priority in the SDK's credential chain). This makes migration safe -- you can set up Pod Identity first, verify it works, then remove the IRSA annotation.
</details>

<details>
<summary>Question 5: Why does the Pod Identity trust policy require `sts:TagSession` in addition to `sts:AssumeRole`?</summary>

Pod Identity uses **session tags** to include metadata about the pod's identity (cluster name, namespace, service account name) in the assumed role session. These tags can be used in IAM policy conditions for fine-grained access control -- for example, an S3 bucket policy that only allows access when the session tag `kubernetes-namespace` equals `production`. The `sts:TagSession` permission is required for this tagging to work. Without it, the `AssumeRoleForPodIdentity` call fails silently, and pods do not receive credentials.
</details>

<details>
<summary>Question 6: Your Fargate pods need AWS credentials. Can you use Pod Identity? What should you use instead?</summary>

**No**, Pod Identity cannot be used with Fargate pods. Pod Identity relies on the Pod Identity Agent DaemonSet running on each node, and Fargate does not support DaemonSets (each Fargate pod runs in its own isolated microVM with no shared node). Instead, use **IRSA** for Fargate pods. IRSA works with Fargate because it relies on projected service account tokens (mounted as files in the pod) and the `AssumeRoleWithWebIdentity` API, neither of which requires a node-level agent.
</details>

---

## Hands-On Exercise: DynamoDB App -- IRSA to Pod Identity Migration

In this exercise, you will deploy a simple application that reads from a DynamoDB table using IRSA, then migrate it to Pod Identity with zero downtime.

**What you will build:**

```text
┌────────────────────────────────────────────────────────────────┐
│  EKS Cluster                                                   │
│                                                                │
│  Phase 1: IRSA                                                 │
│  ┌──────────────────────────────────────┐                     │
│  │ Pod (order-reader)                   │                     │
│  │   SA: order-sa                       │                     │
│  │   Annotation: eks.../role-arn: Role  │                     │
│  │   → OIDC → STS → DynamoDB           │                     │
│  └──────────────────────────────────────┘                     │
│                                                                │
│  Phase 2: Pod Identity                                         │
│  ┌──────────────────────────────────────┐                     │
│  │ Pod (order-reader)                   │                     │
│  │   SA: order-sa                       │                     │
│  │   Association → Agent → STS → DynamoDB│                    │
│  └──────────────────────────────────────┘                     │
└────────────────────────────────────────────────────────────────┘
```

### Task 1: Create a DynamoDB Table

<details>
<summary>Solution</summary>

```bash
# Create a simple DynamoDB table
aws dynamodb create-table \
  --table-name dojo-orders \
  --attribute-definitions AttributeName=orderId,AttributeType=S \
  --key-schema AttributeName=orderId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Insert test data
aws dynamodb put-item --table-name dojo-orders \
  --item '{"orderId":{"S":"ORD-001"},"customer":{"S":"Alice"},"amount":{"N":"99.95"}}'
aws dynamodb put-item --table-name dojo-orders \
  --item '{"orderId":{"S":"ORD-002"},"customer":{"S":"Bob"},"amount":{"N":"149.50"}}'
aws dynamodb put-item --table-name dojo-orders \
  --item '{"orderId":{"S":"ORD-003"},"customer":{"S":"Carol"},"amount":{"N":"75.00"}}'

# Verify
aws dynamodb scan --table-name dojo-orders --query 'Items[*].orderId.S'
```

</details>

### Task 2: Set Up IRSA (Legacy Approach)

Configure OIDC provider and create an IRSA-based role.

<details>
<summary>Solution</summary>

```bash
CLUSTER_NAME="my-cluster"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

# Associate OIDC provider
eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --approve

# Get OIDC ID
OIDC_ID=$(aws eks describe-cluster --name $CLUSTER_NAME \
  --query 'cluster.identity.oidc.issuer' --output text | rev | cut -d'/' -f1 | rev)

# Create IAM role with IRSA trust
cat > /tmp/irsa-trust.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/oidc.eks.${REGION}.amazonaws.com/id/${OIDC_ID}"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.${REGION}.amazonaws.com/id/${OIDC_ID}:aud": "sts.amazonaws.com",
        "oidc.eks.${REGION}.amazonaws.com/id/${OIDC_ID}:sub": "system:serviceaccount:demo:order-sa"
      }
    }
  }]
}
EOF

aws iam create-role --role-name DojoOrderReader \
  --assume-role-policy-document file:///tmp/irsa-trust.json

# Attach DynamoDB read policy
cat > /tmp/dynamo-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["dynamodb:GetItem", "dynamodb:Scan", "dynamodb:Query"],
    "Resource": "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/dojo-orders"
  }]
}
EOF

aws iam put-role-policy --role-name DojoOrderReader \
  --policy-name DynamoDBRead \
  --policy-document file:///tmp/dynamo-policy.json

# Create namespace and service account with IRSA annotation
k create namespace demo

cat <<EOF | k apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-sa
  namespace: demo
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::${ACCOUNT_ID}:role/DojoOrderReader
EOF

# Deploy a test pod that reads from DynamoDB
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: order-reader
  namespace: demo
spec:
  serviceAccountName: order-sa
  containers:
    - name: aws-cli
      image: amazon/aws-cli:latest
      command: ["sleep", "3600"]
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
EOF

# Wait and test
k wait --for=condition=Ready pod/order-reader -n demo --timeout=60s
k exec -n demo order-reader -- \
  aws dynamodb scan --table-name dojo-orders --region us-east-1 \
  --query 'Items[*].{Order:orderId.S, Customer:customer.S}' --output table
```

</details>

### Task 3: Migrate to Pod Identity

Switch from IRSA to Pod Identity without service disruption.

<details>
<summary>Solution</summary>

```bash
CLUSTER_NAME="my-cluster"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Step 1: Install Pod Identity Agent (if not already installed)
aws eks create-addon \
  --cluster-name $CLUSTER_NAME \
  --addon-name eks-pod-identity-agent

# Wait for agent to be running
k rollout status daemonset eks-pod-identity-agent -n kube-system --timeout=120s

# Step 2: Update the role trust policy for Pod Identity
cat > /tmp/pod-identity-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"]
  }]
}
EOF

aws iam update-assume-role-policy \
  --role-name DojoOrderReader \
  --policy-document file:///tmp/pod-identity-trust.json

# Step 3: Create Pod Identity Association
aws eks create-pod-identity-association \
  --cluster-name $CLUSTER_NAME \
  --namespace demo \
  --service-account order-sa \
  --role-arn arn:aws:iam::${ACCOUNT_ID}:role/DojoOrderReader

# Step 4: Remove the IRSA annotation
k annotate sa order-sa -n demo eks.amazonaws.com/role-arn-

# Step 5: Restart the pod to pick up new credentials
k delete pod order-reader -n demo
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: order-reader
  namespace: demo
spec:
  serviceAccountName: order-sa
  containers:
    - name: aws-cli
      image: amazon/aws-cli:latest
      command: ["sleep", "3600"]
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
EOF

k wait --for=condition=Ready pod/order-reader -n demo --timeout=60s

# Step 6: Verify Pod Identity is active
k exec -n demo order-reader -- env | grep AWS
# Should show AWS_CONTAINER_CREDENTIALS_FULL_URI (Pod Identity)
# Should NOT show AWS_WEB_IDENTITY_TOKEN_FILE (IRSA)

# Step 7: Confirm DynamoDB access still works
k exec -n demo order-reader -- \
  aws dynamodb scan --table-name dojo-orders --region us-east-1 \
  --query 'Items[*].{Order:orderId.S, Customer:customer.S}' --output table
```

</details>

### Task 4: Verify and Audit

Confirm the migration is complete and verify the audit trail.

<details>
<summary>Solution</summary>

```bash
# List all Pod Identity associations
aws eks list-pod-identity-associations \
  --cluster-name $CLUSTER_NAME \
  --query 'associations[*].{Namespace:namespace, SA:serviceAccount, RoleArn:associationArn}' \
  --output table

# Verify no IRSA annotation remains
k get sa order-sa -n demo -o json | jq '.metadata.annotations'
# Should be empty or not contain eks.amazonaws.com/role-arn

# Check CloudTrail for the AssumeRoleForPodIdentity event
# (This confirms Pod Identity is being used, not IRSA)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleForPodIdentity \
  --max-results 5 \
  --query 'Events[*].{Time:EventTime, User:Username}' \
  --output table
```

</details>

### Clean Up

```bash
k delete namespace demo
aws eks delete-pod-identity-association \
  --cluster-name my-cluster \
  --association-id $(aws eks list-pod-identity-associations \
    --cluster-name my-cluster --namespace demo --service-account order-sa \
    --query 'associations[0].associationId' --output text)
aws iam delete-role-policy --role-name DojoOrderReader --policy-name DynamoDBRead
aws iam delete-role --role-name DojoOrderReader
aws dynamodb delete-table --table-name dojo-orders
```

### Success Criteria

- [ ] I created a DynamoDB table and populated it with test data
- [ ] I configured IRSA with an OIDC provider, trust policy, and ServiceAccount annotation
- [ ] I verified the pod could read from DynamoDB using IRSA credentials
- [ ] I installed the Pod Identity Agent add-on
- [ ] I migrated the role's trust policy from OIDC to `pods.eks.amazonaws.com`
- [ ] I created a Pod Identity association and removed the IRSA annotation
- [ ] I verified the pod uses Pod Identity (AWS_CONTAINER_CREDENTIALS_FULL_URI env var)
- [ ] I confirmed DynamoDB access works after migration with zero downtime

---

## Next Module

Your pods have identity and can authenticate to AWS services. But where do they store data? Head to [Module 5.4: EKS Storage & Data Management](module-5.4-eks-storage/) to master EBS, EFS, and S3 CSI drivers for stateful workloads.
