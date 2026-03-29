---
title: "Module 1.6: Elastic Container Registry (ECR)"
slug: cloud/aws-essentials/module-1.6-ecr
sidebar:
  order: 7
---
## Complexity: [MEDIUM]
## Time to Complete: 1 hour

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 1.1: IAM & Security Foundations](module-1.1-iam/)
- Docker fundamentals (building and tagging images)
- Docker installed locally and running
- AWS CLI configured with appropriate permissions

---

## Why This Module Matters

In January 2024, a mid-stage fintech startup pushed a routine update to their payment processing service. The deployment succeeded. Five minutes later, their monitoring exploded. The application was crashing on startup, throwing cryptic "exec format error" messages. The previous container image -- the one that worked -- had been overwritten because they were using the `latest` tag with mutable tagging enabled. Their CI pipeline had pushed an ARM64 image over the existing AMD64 image. No versioning. No immutability. No way to roll back except to rebuild from source, which took 22 minutes while their payment pipeline was down. Twenty-two minutes of lost transactions for a fintech company is the kind of thing that ends up in board meeting slides.

Container registries are one of those infrastructure components that seem boring until they break. They sit between your CI pipeline and your runtime environment, holding every version of every service your company runs. A misconfigured registry means you cannot deploy, cannot roll back, and cannot verify that what is running in production is what you think is running. AWS Elastic Container Registry (ECR) is Amazon's managed container registry, deeply integrated with ECS, EKS, Lambda, and the rest of the AWS ecosystem.

In this module, you will learn how ECR works, how to configure it properly for production workloads, and how to avoid the mistakes that turn a routine deployment into a production incident. By the end, you will have built a complete image lifecycle -- from building and pushing images with proper tagging, to configuring lifecycle policies that keep your registry clean and your costs under control.

---

## ECR Architecture and Concepts

ECR is a fully managed Docker container registry. Unlike running your own registry (Docker Registry, Harbor, or Nexus), ECR handles storage, availability, encryption, and access control for you. Let us break down the key concepts.

### Registries, Repositories, and Images

```
ECR Structure:

AWS Account (123456789012)
|
+-- ECR Registry (one per account per region)
    |   Registry URL: 123456789012.dkr.ecr.us-east-1.amazonaws.com
    |
    +-- Repository: myapp/api
    |   +-- Image: sha256:abc123... (tag: v1.2.0)
    |   +-- Image: sha256:def456... (tag: v1.2.1)
    |   +-- Image: sha256:ghi789... (tag: v1.3.0, tag: latest)
    |
    +-- Repository: myapp/worker
    |   +-- Image: sha256:jkl012... (tag: v2.0.0)
    |   +-- Image: sha256:mno345... (tag: v2.1.0)
    |
    +-- Repository: shared/nginx-base
        +-- Image: sha256:pqr678... (tag: 1.25-custom)
```

**Registry**: One per AWS account per region. The URL format is always `{account_id}.dkr.ecr.{region}.amazonaws.com`. You cannot change this URL.

**Repository**: A collection of related container images, like a Git repository for code. Naming convention matters -- use a slash-separated hierarchy like `team/service` or `app/component`.

**Image**: An individual container image, identified by its SHA256 digest and optionally by one or more tags. A single image can have multiple tags.

### Public vs Private Repositories

ECR offers two flavors:

| Feature | ECR Private | ECR Public |
|---------|------------|------------|
| URL format | `{account_id}.dkr.ecr.{region}.amazonaws.com` | `public.ecr.aws/{alias}` |
| Authentication | Required for pull and push | Required for push; pull is anonymous |
| Cost | $0.10/GB/month storage + data transfer | Free (up to limits) |
| Use case | Internal services, proprietary code | Open source projects, shared base images |
| Regions | All commercial regions | us-east-1 only (content delivered globally via CloudFront) |
| Vulnerability scanning | Basic + Enhanced (Inspector) | Not supported |
| Lifecycle policies | Yes | No |

For most DevOps workflows, you will use private repositories. Public ECR is excellent for distributing open-source tools or shared base images that external teams or customers need to pull.

```bash
# Create a private repository
aws ecr create-repository \
  --repository-name myapp/api \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --encryption-configuration encryptionType=KMS

# Create a public repository
aws ecr-public create-repository \
  --repository-name my-oss-tool \
  --catalog-data '{
    "description": "My open source container tool",
    "architectures": ["x86-64", "ARM 64"],
    "operatingSystems": ["Linux"]
  }' \
  --region us-east-1
```

---

## Authentication and Pushing Images

ECR uses IAM for authentication, but Docker does not speak IAM natively. You need to exchange your IAM credentials for a Docker login token.

### Getting Authenticated

```bash
# The standard way: pipe ECR token directly to docker login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# The token is valid for 12 hours
# For CI/CD pipelines, refresh it at the start of each pipeline run
```

For ECS and EKS workloads, you do not need to handle authentication manually. ECS automatically pulls images from ECR using the task execution role. EKS nodes use the instance profile or IRSA (IAM Roles for Service Accounts) to authenticate.

### Building and Pushing Images

Here is the complete workflow from Dockerfile to ECR:

```bash
# Step 1: Build your image locally
docker build -t myapp/api:v1.3.0 .

# Step 2: Tag it for ECR
docker tag myapp/api:v1.3.0 \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/api:v1.3.0

# Step 3: Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/api:v1.3.0

# Verify the push
aws ecr describe-images \
  --repository-name myapp/api \
  --image-ids imageTag=v1.3.0
```

For production CI/CD pipelines, here is a more robust script:

```bash
#!/bin/bash
set -euo pipefail

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
REPO_NAME="myapp/api"
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_TAG="${GIT_SHA:-$(git rev-parse --short HEAD)}"

# Authenticate
aws ecr get-login-password --region ${REGION} | \
  docker login --username AWS --password-stdin ${REGISTRY}

# Build with cache from previous image (speeds up CI builds significantly)
docker build \
  --cache-from ${REGISTRY}/${REPO_NAME}:latest \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t ${REGISTRY}/${REPO_NAME}:${IMAGE_TAG} \
  -t ${REGISTRY}/${REPO_NAME}:latest \
  .

# Push both tags
docker push ${REGISTRY}/${REPO_NAME}:${IMAGE_TAG}
docker push ${REGISTRY}/${REPO_NAME}:latest

echo "Pushed ${REGISTRY}/${REPO_NAME}:${IMAGE_TAG}"
```

---

## Image Tagging Strategies and Immutability

Tagging is where most teams get into trouble. Let us get this right.

### Tag Immutability

When tag immutability is enabled, once you push an image with a specific tag, that tag cannot be overwritten. This is critical for production safety.

```bash
# Enable immutability on an existing repository
aws ecr put-image-tag-mutability \
  --repository-name myapp/api \
  --image-tag-mutability IMMUTABLE

# Now this will FAIL if v1.3.0 already exists:
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/api:v1.3.0
# Error: tag invalid: The image tag 'v1.3.0' already exists
```

With immutability enabled, you are guaranteed that `v1.3.0` always refers to the exact same image. This makes rollbacks reliable and audit trails meaningful.

### Tagging Strategy Comparison

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| Semantic version | `v1.3.0` | Human readable, clear progression | Requires version discipline |
| Git SHA | `abc1234` | Ties image to exact source code | Not human readable |
| Both (recommended) | `v1.3.0` + `abc1234` | Best of both worlds | Slightly more complex CI |
| `latest` only | `latest` | Simple | No versioning, cannot roll back, dangerous |
| Date-based | `2026-03-24-1432` | Chronological ordering | No semantic meaning |

The recommended approach for production: **tag every image with both the semantic version and the Git SHA.** Use `latest` only as a convenience pointer that also gets applied alongside the versioned tag.

```bash
# Recommended: apply multiple tags
docker tag myapp/api:local \
  ${REGISTRY}/${REPO_NAME}:v1.3.0
docker tag myapp/api:local \
  ${REGISTRY}/${REPO_NAME}:${GIT_SHA}
docker tag myapp/api:local \
  ${REGISTRY}/${REPO_NAME}:latest

# With immutability ON:
# - v1.3.0 and ${GIT_SHA} are permanent, cannot be overwritten
# - latest is NOT allowed with IMMUTABLE (it needs to change each push)
# Solution: use IMMUTABLE repos without the 'latest' tag,
# or use a separate mutable repo for 'latest'
```

A practical note on immutability and `latest`: they are fundamentally incompatible. If you enable immutability, you cannot push `latest` more than once. Most teams choose one of two patterns:

1. **Enable immutability, never use `latest`** -- deployments always reference explicit versions
2. **Keep mutability, enforce versioning through CI policy** -- lint your pipeline to reject pushes without a version tag

Pattern 1 is safer. Pattern 2 is more convenient. Choose based on your team's discipline.

---

## Vulnerability Scanning

ECR provides two levels of vulnerability scanning: Basic and Enhanced.

### Basic Scanning

Basic scanning uses the open-source Clair engine to check for known CVEs in OS packages. It is included in ECR at no extra cost.

```bash
# Enable scan-on-push for a repository
aws ecr put-image-scanning-configuration \
  --repository-name myapp/api \
  --image-scanning-configuration scanOnPush=true

# Manually trigger a scan on an existing image
aws ecr start-image-scan \
  --repository-name myapp/api \
  --image-id imageTag=v1.3.0

# Get scan results
aws ecr describe-image-scan-findings \
  --repository-name myapp/api \
  --image-id imageTag=v1.3.0
```

### Enhanced Scanning

Enhanced scanning uses Amazon Inspector and provides deeper analysis including application dependency vulnerabilities (not just OS packages). It costs extra but catches significantly more issues.

```bash
# Enable enhanced scanning at the registry level
aws ecr put-registry-scanning-configuration \
  --scan-type ENHANCED \
  --rules '[
    {
      "scanFrequency": "CONTINUOUS_SCAN",
      "repositoryFilters": [
        {"filter": "myapp/*", "filterType": "WILDCARD"}
      ]
    },
    {
      "scanFrequency": "SCAN_ON_PUSH",
      "repositoryFilters": [
        {"filter": "*", "filterType": "WILDCARD"}
      ]
    }
  ]'
```

### Interpreting Scan Results

```bash
# Get findings summary
aws ecr describe-image-scan-findings \
  --repository-name myapp/api \
  --image-id imageTag=v1.3.0 \
  --query 'imageScanFindings.findingSeverityCounts'

# Example output:
# {
#     "CRITICAL": 0,
#     "HIGH": 2,
#     "MEDIUM": 8,
#     "LOW": 15,
#     "INFORMATIONAL": 3
# }

# Get detailed findings for critical and high severity
aws ecr describe-image-scan-findings \
  --repository-name myapp/api \
  --image-id imageTag=v1.3.0 \
  --query 'imageScanFindings.findings[?severity==`HIGH` || severity==`CRITICAL`]'
```

A practical CI/CD gate using scan results:

```bash
#!/bin/bash
# Gate deployment based on scan findings
CRITICAL=$(aws ecr describe-image-scan-findings \
  --repository-name myapp/api \
  --image-id imageTag=${IMAGE_TAG} \
  --query 'imageScanFindings.findingSeverityCounts.CRITICAL // `0`' \
  --output text)

HIGH=$(aws ecr describe-image-scan-findings \
  --repository-name myapp/api \
  --image-id imageTag=${IMAGE_TAG} \
  --query 'imageScanFindings.findingSeverityCounts.HIGH // `0`' \
  --output text)

if [ "${CRITICAL}" -gt 0 ]; then
  echo "BLOCKED: ${CRITICAL} critical vulnerabilities found"
  exit 1
fi

if [ "${HIGH}" -gt 5 ]; then
  echo "WARNING: ${HIGH} high-severity vulnerabilities found (threshold: 5)"
  exit 1
fi

echo "Scan passed: ${CRITICAL} critical, ${HIGH} high"
```

---

## Lifecycle Policies

Without lifecycle policies, your ECR storage grows indefinitely. Every CI build pushes a new image, and old images accumulate. A team pushing 10 builds per day generates 300+ images per month per repository. At $0.10/GB/month, this adds up.

Lifecycle policies let you automatically expire old images based on rules you define.

### Understanding Lifecycle Policy Rules

```bash
# Set a lifecycle policy that retains the last 10 tagged images
aws ecr put-lifecycle-policy \
  --repository-name myapp/api \
  --lifecycle-policy-text '{
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep last 10 tagged images",
        "selection": {
          "tagStatus": "tagged",
          "tagPrefixList": ["v"],
          "countType": "imageCountMoreThan",
          "countNumber": 10
        },
        "action": {
          "type": "expire"
        }
      },
      {
        "rulePriority": 2,
        "description": "Remove untagged images older than 3 days",
        "selection": {
          "tagStatus": "untagged",
          "countType": "sinceImagePushed",
          "countUnit": "days",
          "countNumber": 3
        },
        "action": {
          "type": "expire"
        }
      }
    ]
  }'
```

### Production-Grade Lifecycle Policy

Here is a comprehensive policy that covers the typical scenarios:

```bash
aws ecr put-lifecycle-policy \
  --repository-name myapp/api \
  --lifecycle-policy-text '{
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep release images (v-prefixed) for 180 days",
        "selection": {
          "tagStatus": "tagged",
          "tagPrefixList": ["v"],
          "countType": "sinceImagePushed",
          "countUnit": "days",
          "countNumber": 180
        },
        "action": {"type": "expire"}
      },
      {
        "rulePriority": 2,
        "description": "Keep only last 5 feature branch images",
        "selection": {
          "tagStatus": "tagged",
          "tagPrefixList": ["feature-", "fix-", "dev-"],
          "countType": "imageCountMoreThan",
          "countNumber": 5
        },
        "action": {"type": "expire"}
      },
      {
        "rulePriority": 10,
        "description": "Remove untagged images after 1 day",
        "selection": {
          "tagStatus": "untagged",
          "countType": "sinceImagePushed",
          "countUnit": "days",
          "countNumber": 1
        },
        "action": {"type": "expire"}
      }
    ]
  }'
```

### Preview Before You Apply

Lifecycle policies can be destructive -- they delete images. Always preview first:

```bash
# Preview what a lifecycle policy WOULD delete (dry run)
aws ecr get-lifecycle-policy-preview \
  --repository-name myapp/api

# Start a preview (if no preview exists)
aws ecr start-lifecycle-policy-preview \
  --repository-name myapp/api
```

### Lifecycle Policy Rule Evaluation Order

ECR evaluates lifecycle rules in a specific order. Understanding this prevents surprises:

```
Rule Evaluation Flow:

1. Rules are sorted by priority (lowest number = highest priority)
2. Each image is evaluated against rules in priority order
3. Once a rule matches an image, that image is "claimed" by that rule
4. Later rules cannot affect images already claimed
5. The action (expire or keep) is applied based on the matching rule

Example with our policy:
- Image tagged "v1.3.0" pushed 90 days ago
  -> Matches Rule 1 (v-prefix, < 180 days) -> KEPT
- Image tagged "v1.0.0" pushed 200 days ago
  -> Matches Rule 1 (v-prefix, > 180 days) -> EXPIRED
- Image tagged "feature-auth-fix" (6th feature image)
  -> Matches Rule 2 (feature- prefix, > 5 count) -> EXPIRED
- Untagged image pushed 2 days ago
  -> Matches Rule 10 (untagged, > 1 day) -> EXPIRED
```

---

## Cross-Account and Cross-Region Sharing

In multi-account AWS environments (which is the standard for any serious organization), you often need to share images between accounts. The typical pattern: a CI/CD account builds and pushes images, and deployment accounts pull them.

### Cross-Account Access via Repository Policy

```bash
# Allow another AWS account to pull images
aws ecr set-repository-policy \
  --repository-name myapp/api \
  --policy-text '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowCrossAccountPull",
        "Effect": "Allow",
        "Principal": {
          "AWS": [
            "arn:aws:iam::987654321098:root",
            "arn:aws:iam::111222333444:root"
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
```

### Cross-Region Replication

ECR supports automatic replication of images to other regions. This is essential for multi-region deployments to avoid cross-region image pulls during container startup (which add latency and data transfer costs).

```bash
# Configure replication to eu-west-1 and ap-southeast-1
aws ecr put-replication-configuration \
  --replication-configuration '{
    "rules": [
      {
        "destinations": [
          {
            "region": "eu-west-1",
            "registryId": "123456789012"
          },
          {
            "region": "ap-southeast-1",
            "registryId": "123456789012"
          }
        ],
        "repositoryFilters": [
          {
            "filter": "myapp/",
            "filterType": "PREFIX_MATCH"
          }
        ]
      }
    ]
  }'
```

### Cross-Account and Cross-Region Together

For organizations with separate accounts per environment and multiple regions:

```bash
# Replicate from CI account (123456789012) to:
# - Production account (987654321098) in us-east-1 and eu-west-1
aws ecr put-replication-configuration \
  --replication-configuration '{
    "rules": [
      {
        "destinations": [
          {
            "region": "us-east-1",
            "registryId": "987654321098"
          },
          {
            "region": "eu-west-1",
            "registryId": "987654321098"
          }
        ]
      }
    ]
  }'
```

The destination account must grant permission for the source account to replicate:

```bash
# Run this in the DESTINATION account
aws ecr put-registry-policy \
  --policy-text '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowReplicationFrom",
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::123456789012:root"
        },
        "Action": [
          "ecr:CreateRepository",
          "ecr:ReplicateImage"
        ],
        "Resource": "arn:aws:ecr:*:987654321098:repository/*"
      }
    ]
  }'
```

---

## Did You Know?

1. **ECR stores images in S3 under the hood**, but you cannot see or access the S3 buckets directly. Each image layer is stored as an individual S3 object, deduplicated across all repositories in the same account and region. If five of your repositories use the same base layer (like `ubuntu:22.04`), that layer is stored only once. This deduplication can reduce your storage costs by 40-60% for organizations with many similar images.

2. **The ECR credential helper eliminates manual `docker login` calls.** Install `amazon-ecr-credential-helper` and configure Docker to use it, and every `docker pull` and `docker push` command against ECR automatically authenticates using your AWS credentials. GitHub Actions, GitLab CI, and Jenkins all have native ECR integration that uses this same mechanism under the hood.

3. **ECR pull-through cache** lets your ECR registry act as a proxy for public registries like Docker Hub, Quay.io, and GitHub Container Registry. When your workloads pull `docker.io/library/nginx:1.25`, ECR intercepts the request, caches the image locally, and serves subsequent pulls from the cache. This protects you from Docker Hub rate limits (100 pulls per 6 hours for anonymous users) and reduces external network dependencies.

4. **Amazon Inspector's enhanced scanning for ECR can detect vulnerabilities in 15+ programming languages**, not just OS packages. This includes npm, pip, Maven, NuGet, Go modules, Rust crates, and more. A single Node.js application image might have 3 OS-level vulnerabilities but 28 application-level ones. Basic scanning would only catch the 3.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using `latest` tag as the only tag | It is the Docker default and seems simple | Always tag with a version or Git SHA. Treat `latest` as a convenience alias, never as the deployment target |
| Forgetting to authenticate before pushing | ECR tokens expire after 12 hours | Add `aws ecr get-login-password` to the start of every CI pipeline. Use the credential helper for local development |
| Not enabling scan-on-push | It is not the default when creating repositories | Create a script or Terraform module that always enables scanning. Gate deployments on scan results |
| No lifecycle policy | Teams do not think about storage costs until the bill arrives | Apply lifecycle policies at repository creation time. A default policy that keeps the last 20 tagged images and removes untagged images after 3 days works for most teams |
| Mutable tags in production | It is the ECR default, and immutability seems restrictive | Enable IMMUTABLE tag mutability for all production repositories. Mutable tags make rollbacks unreliable |
| Pulling images cross-region in production | The image exists in us-east-1 but the ECS cluster is in eu-west-1 | Configure ECR replication to all regions where you deploy containers. Cross-region pulls add 200-500ms to container startup and incur data transfer charges |
| Repository names that do not match service names | Ad hoc naming without convention | Establish a naming convention (e.g., `{team}/{service}`) and enforce it in CI. Consistent naming prevents confusion when you have 50+ repositories |
| Not setting repository policies for cross-account access | Developers use root-account credentials or overly broad IAM policies | Use ECR repository policies for cross-account pull access. Keep IAM policies for push access controlled by the CI/CD account |

---

## Quiz

<details>
<summary>1. What is the difference between ECR Basic scanning and Enhanced scanning?</summary>

Basic scanning uses the open-source Clair engine and only checks for known CVEs in operating system packages (the packages installed via apt, yum, apk, etc.). It runs once per image when triggered manually or on push. Enhanced scanning uses Amazon Inspector, which analyzes both OS packages and application dependencies (npm, pip, Maven, Go modules, and more). Enhanced scanning can also run continuously, re-scanning images when new CVEs are published. The trade-off is cost: Basic scanning is free, while Enhanced scanning costs per image scanned. For production workloads, Enhanced scanning is strongly recommended because application dependency vulnerabilities typically outnumber OS-level ones by a factor of 5-10.
</details>

<details>
<summary>2. Why can you not use the `latest` tag with ECR image tag immutability enabled?</summary>

Image tag immutability means that once a tag is applied to an image, it cannot be reassigned to a different image. The `latest` tag, by convention, is meant to always point to the most recently pushed image -- which requires overwriting the tag with each push. These two concepts are fundamentally incompatible. If you push `myapp:latest` once with immutability enabled, every subsequent attempt to push `myapp:latest` will fail because the tag is already locked to the first image's digest. The solution is to either not use `latest` at all (preferred) or to maintain a separate mutable repository just for the `latest` pointer.
</details>

<details>
<summary>3. You have an ECR lifecycle policy that keeps the last 10 images tagged with "v" prefix and removes untagged images after 3 days. You push an image tagged v1.5.0 and also tag it as "latest". Later, the v1.5.0 tag is removed by the lifecycle policy (it becomes the 11th oldest). What happens to the "latest" tag?</summary>

This is a subtle but important behavior. ECR lifecycle policies operate on images (identified by digest), not on individual tags. If an image has multiple tags and the lifecycle policy matches one of those tags for expiration, the entire image (and all its tags) is deleted. So when v1.5.0 is expired, the image itself is deleted, and the "latest" tag that pointed to the same digest is also removed. This is why relying on `latest` as a deployment reference is dangerous -- it can disappear when the versioned tag it shares a digest with gets cleaned up by lifecycle rules.
</details>

<details>
<summary>4. How does ECR pull-through cache help with Docker Hub rate limits?</summary>

Docker Hub imposes rate limits on image pulls: 100 pulls per 6 hours for anonymous users and 200 for authenticated free accounts. When your Kubernetes cluster scales up and 50 pods start simultaneously, each pulling an image from Docker Hub, you can hit these limits quickly. ECR pull-through cache solves this by acting as a local proxy. The first pull goes to Docker Hub and caches the image in your ECR registry. All subsequent pulls come from ECR, which has no rate limits for your own account. This means only 1 external pull instead of 50. It also improves reliability -- if Docker Hub has an outage, your cached images are still available.
</details>

<details>
<summary>5. Explain how ECR image layer deduplication works and why it matters for costs.</summary>

Container images are composed of layers, each representing a filesystem change. When you push an image to ECR, each layer is stored individually and identified by its SHA256 digest. If multiple repositories contain images that share the same base layers (e.g., they all inherit from `python:3.12-slim`), those layers are stored only once in the underlying S3 storage. You are billed only for unique layer storage, not for each reference. For an organization with 30 microservices all built on the same base image, this can reduce storage costs by 40-60%. This is also why pushing images is faster when the base layers already exist -- Docker only uploads the layers that are new.
</details>

<details>
<summary>6. Your ECS tasks in eu-west-1 are pulling images from ECR in us-east-1. What problems does this cause and how do you fix them?</summary>

Cross-region image pulls cause three problems. First, latency: pulling a 500MB image across regions adds 2-8 seconds to container startup time, which compounds when you are scaling up many tasks simultaneously. Second, cost: inter-region data transfer is charged at $0.02/GB, so pulling that 500MB image 100 times costs $1.00 per scaling event. Third, reliability: if the network path between regions degrades, your tasks cannot start. The fix is ECR replication. Configure your us-east-1 registry to replicate to eu-west-1, then update your ECS task definitions to reference the eu-west-1 registry URL. Pulls become local, eliminating latency, cost, and cross-region dependency.
</details>

---

## Hands-On Exercise: Build, Push, Scan, and Lifecycle

In this exercise, you will create an ECR repository, build and push images with proper tagging, run vulnerability scans, and configure lifecycle policies.

### Setup

```bash
# Set your variables
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REGION="us-east-1"
export REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
export REPO_NAME="kubedojo/ecr-exercise"
```

### Task 1: Create a Repository with Best-Practice Settings

Create an ECR repository with scanning enabled and immutable tags.

<details>
<summary>Solution</summary>

```bash
aws ecr create-repository \
  --repository-name ${REPO_NAME} \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --encryption-configuration encryptionType=AES256 \
  --region ${REGION}

# Verify the repository settings
aws ecr describe-repositories \
  --repository-names ${REPO_NAME} \
  --query 'repositories[0].{Name:repositoryName,URI:repositoryUri,ScanOnPush:imageScanningConfiguration.scanOnPush,TagMutability:imageTagMutability}'
```
</details>

### Task 2: Build and Push a Test Image

Create a simple Dockerfile, build it, and push to ECR with proper tagging.

<details>
<summary>Solution</summary>

```bash
# Create a temporary directory for our test image
mkdir -p /tmp/ecr-exercise && cd /tmp/ecr-exercise

# Create a simple Dockerfile
cat > Dockerfile <<'DOCKERFILE'
FROM python:3.12-slim
LABEL maintainer="kubedojo"
LABEL version="1.0.0"

RUN pip install flask==3.0.0
COPY app.py /app/app.py
WORKDIR /app
EXPOSE 8080
CMD ["python", "app.py"]
DOCKERFILE

# Create a simple app
cat > app.py <<'PYTHON'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/")
def index():
    return jsonify({"message": "ECR Exercise App", "version": "1.0.0"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
PYTHON

# Authenticate
aws ecr get-login-password --region ${REGION} | \
  docker login --username AWS --password-stdin ${REGISTRY}

# Build and tag with version
docker build -t ${REGISTRY}/${REPO_NAME}:v1.0.0 .

# Push
docker push ${REGISTRY}/${REPO_NAME}:v1.0.0

# Verify
aws ecr describe-images \
  --repository-name ${REPO_NAME} \
  --query 'imageDetails[*].{Tags:imageTags,Pushed:imagePushedAt,Size:imageSizeInBytes,Digest:imageDigest}'
```
</details>

### Task 3: Push Multiple Versions (Simulate CI/CD History)

Build and push several versions to test lifecycle policies later.

<details>
<summary>Solution</summary>

```bash
# Push versions v1.1.0 through v1.12.0 (we will use lifecycle to prune)
for i in $(seq 1 12); do
  # Modify the app version to create different layers
  sed -i "s/version\": \"[0-9.]*\"/version\": \"1.${i}.0\"/" app.py

  docker build -t ${REGISTRY}/${REPO_NAME}:v1.${i}.0 .
  docker push ${REGISTRY}/${REPO_NAME}:v1.${i}.0

  echo "Pushed v1.${i}.0"
done

# List all images in the repository
aws ecr describe-images \
  --repository-name ${REPO_NAME} \
  --query 'sort_by(imageDetails, &imagePushedAt)[*].{Tag:imageTags[0],Pushed:imagePushedAt}' \
  --output table
```
</details>

### Task 4: Check Vulnerability Scan Results

Review the scan results for the latest image.

<details>
<summary>Solution</summary>

```bash
# Wait for scan to complete (scan-on-push was enabled)
echo "Waiting for scan to complete..."
aws ecr wait image-scan-complete \
  --repository-name ${REPO_NAME} \
  --image-id imageTag=v1.12.0

# Get scan findings summary
aws ecr describe-image-scan-findings \
  --repository-name ${REPO_NAME} \
  --image-id imageTag=v1.12.0 \
  --query '{
    Status: imageScanStatus.status,
    Counts: imageScanFindings.findingSeverityCounts,
    CompletedAt: imageScanFindings.imageScanCompletedAt
  }'

# Get detailed high/critical findings
aws ecr describe-image-scan-findings \
  --repository-name ${REPO_NAME} \
  --image-id imageTag=v1.12.0 \
  --query 'imageScanFindings.findings[?severity==`HIGH` || severity==`CRITICAL`].{Name:name,Severity:severity,Description:description,URI:uri}' \
  --output table
```
</details>

### Task 5: Apply a Lifecycle Policy to Retain Only the Last 10 Images

Configure a lifecycle policy that keeps the 10 most recent tagged images and removes the rest.

<details>
<summary>Solution</summary>

```bash
# First, preview what the policy would delete
aws ecr put-lifecycle-policy \
  --repository-name ${REPO_NAME} \
  --lifecycle-policy-text '{
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep only the last 10 versioned images",
        "selection": {
          "tagStatus": "tagged",
          "tagPrefixList": ["v"],
          "countType": "imageCountMoreThan",
          "countNumber": 10
        },
        "action": {
          "type": "expire"
        }
      },
      {
        "rulePriority": 2,
        "description": "Remove untagged images after 1 day",
        "selection": {
          "tagStatus": "untagged",
          "countType": "sinceImagePushed",
          "countUnit": "days",
          "countNumber": 1
        },
        "action": {
          "type": "expire"
        }
      }
    ]
  }'

# Verify the policy was applied
aws ecr get-lifecycle-policy \
  --repository-name ${REPO_NAME} \
  --query 'lifecyclePolicyText' --output text | python3 -m json.tool

# Note: Lifecycle policies run asynchronously (within 24 hours)
# To see what WOULD be deleted immediately, use:
aws ecr start-lifecycle-policy-preview \
  --repository-name ${REPO_NAME}

# Check preview results (may take a few minutes)
aws ecr get-lifecycle-policy-preview \
  --repository-name ${REPO_NAME} \
  --query 'previewResults[*].{Tag:imageTags[0],Action:action.type,AppliedRule:appliedAction.rulePriority}'
```
</details>

### Task 6: Clean Up

Remove all resources created during this exercise.

<details>
<summary>Solution</summary>

```bash
# Delete all images in the repository first (required before repo deletion)
IMAGE_IDS=$(aws ecr list-images \
  --repository-name ${REPO_NAME} \
  --query 'imageIds[*]' --output json)

aws ecr batch-delete-image \
  --repository-name ${REPO_NAME} \
  --image-ids "${IMAGE_IDS}"

# Delete the repository
aws ecr delete-repository \
  --repository-name ${REPO_NAME} \
  --force

# Clean up local Docker images
docker images --filter "reference=${REGISTRY}/${REPO_NAME}" -q | \
  xargs -r docker rmi

# Clean up temporary files
rm -rf /tmp/ecr-exercise

echo "Cleanup complete"
```
</details>

### Success Criteria

- [ ] ECR repository created with scan-on-push and immutable tags
- [ ] Successfully authenticated and pushed a versioned image
- [ ] Multiple image versions pushed (simulating CI/CD history)
- [ ] Vulnerability scan results reviewed and interpreted
- [ ] Lifecycle policy applied that retains only the last 10 images
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 1.7: Elastic Container Service (ECS) & Fargate](module-1.7-ecs-fargate/)** -- Now that you can store container images, it is time to run them. You will learn to deploy containers on AWS using ECS with both EC2 and Fargate launch types, integrate with load balancers, and debug running containers with ECS Exec.
