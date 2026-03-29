---
title: "Module 1.11: CI/CD on AWS (Code Suite)"
slug: cloud/aws-essentials/module-1.11-cicd
sidebar:
  order: 12
---
**Complexity:** `[MEDIUM]` | **Time to Complete:** 2 hours | **Track:** AWS DevOps Essentials

## Prerequisites

Before starting this module, ensure you have:
- Completed [Module 1.6: ECR (Container Registry)](module-1.6-ecr/) (pushing/pulling container images)
- Completed [Module 1.7: ECS (Container Orchestration)](module-1.7-ecs-fargate/) (ECS services, task definitions, Fargate)
- Familiarity with CI/CD concepts (build, test, deploy pipeline stages)
- A GitHub account and a repository to use for pipeline integration
- AWS CLI v2 installed and configured
- Basic knowledge of Docker and Dockerfiles

---

## Why This Module Matters

In 2018, a well-known travel booking platform deployed a database migration to production on a Friday afternoon. The deployment was manual -- an engineer ran a script on a bastion host, copy-pasting commands from a wiki page that had not been updated in four months. The script applied schema changes in the wrong order, corrupting a foreign key relationship that silently broke booking confirmations. For 11 hours over the weekend, customers completed bookings and received confirmation emails, but no actual reservations were created. The company had to manually reconcile 23,000 phantom bookings, issue refunds, and rebook customers at higher prices. The estimated cost exceeded $6 million, not counting the permanent loss of trust from affected travelers.

A CI/CD pipeline would have caught this in minutes, not hours. Automated tests would have validated the migration against a staging database. A blue/green deployment would have allowed instant rollback when health checks failed. Code review enforced by the pipeline would have flagged the outdated migration script. And nobody would have needed to SSH into production on a Friday.

In this module, you will learn the AWS Code Suite -- CodeBuild for building and testing code, CodeDeploy for deployment strategies, and CodePipeline for orchestrating the full workflow. You will also learn how to connect GitHub and GitLab repositories to AWS using OIDC federation, which is the modern, secure alternative to storing long-lived access keys.

---

## Did You Know?

- **AWS CodePipeline was one of the first fully managed CI/CD services** in any cloud, launching in July 2015. Before that, most AWS teams ran Jenkins on EC2 instances -- a pattern that still exists but is increasingly replaced by managed alternatives.

- **CodeBuild runs on managed compute** that scales to zero when idle. Unlike Jenkins, where you pay for the build server 24/7, CodeBuild charges only for build minutes. A typical small team spends $5-15/month on CodeBuild versus $50-150/month for an always-on Jenkins instance.

- **OIDC federation for GitHub Actions** eliminates the need for IAM access keys entirely. GitHub's OIDC provider issues short-lived tokens (valid for about 15 minutes) that AWS trusts directly. This pattern, documented by AWS in 2021, has become the standard for GitHub-to-AWS authentication.

- **Blue/green deployments on ECS** require AWS CodeDeploy — there is no native ECS blue/green deployment controller. The ECS Deployment Circuit Breaker (introduced 2020) provides automated rollbacks for rolling updates only. CodeDeploy remains the only option for blue/green with traffic shifting controls (linear, canary, all-at-once) and automatic rollback on CloudWatch alarm triggers.

---

## CodeBuild: Building and Testing Code

CodeBuild is a fully managed build service. You give it source code, a build specification file (`buildspec.yml`), and a compute environment. It runs your build, publishes artifacts, and reports success or failure.

### How CodeBuild Works

```
+-------------------+     +-----------------------+     +------------------+
|   Source           |     |   CodeBuild           |     |   Artifacts      |
|   (GitHub, S3,    | --> |   - Provisions env    | --> |   (ECR image,    |
|    CodeCommit)    |     |   - Runs buildspec    |     |    S3 bucket,    |
|                   |     |   - Reports status    |     |    test reports) |
+-------------------+     +-----------------------+     +------------------+
                                    |
                                    v
                          +-------------------+
                          |  CloudWatch Logs  |
                          |  (build output)   |
                          +-------------------+
```

### The buildspec.yml File

This is the heart of CodeBuild. It defines what happens during each build phase:

```yaml
version: 0.2

env:
  variables:
    APP_NAME: "myapp"
    AWS_DEFAULT_REGION: "us-east-1"
  parameter-store:
    DB_PASSWORD: "/myapp/production/database/password"
  secrets-manager:
    DOCKER_HUB_TOKEN: "dockerhub-credentials:token"

phases:
  install:
    runtime-versions:
      docker: 20
      python: 3.12
    commands:
      - echo "Installing dependencies..."
      - pip install -r requirements.txt
      - pip install pytest flake8

  pre_build:
    commands:
      - echo "Running linting and unit tests..."
      - flake8 src/ --max-line-length 120
      - pytest tests/unit/ --junitxml=reports/unit-tests.xml
      - echo "Logging into ECR..."
      - ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
      - ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"
      - aws ecr get-login-password | docker login --username AWS --password-stdin ${ECR_URI}

  build:
    commands:
      - echo "Building Docker image..."
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-8)
      - IMAGE_TAG="${COMMIT_HASH:-latest}"
      - docker build -t ${ECR_URI}/${APP_NAME}:${IMAGE_TAG} .
      - docker build -t ${ECR_URI}/${APP_NAME}:latest .

  post_build:
    commands:
      - echo "Pushing Docker image to ECR..."
      - docker push ${ECR_URI}/${APP_NAME}:${IMAGE_TAG}
      - docker push ${ECR_URI}/${APP_NAME}:latest
      - echo "Writing image definitions for ECS..."
      - printf '[{"name":"myapp","imageUri":"%s"}]' ${ECR_URI}/${APP_NAME}:${IMAGE_TAG} > imagedefinitions.json

reports:
  unit-tests:
    files:
      - "reports/unit-tests.xml"
    file-format: JUNITXML

artifacts:
  files:
    - imagedefinitions.json
    - appspec.yml
  discard-paths: yes

cache:
  paths:
    - "/root/.cache/pip/**/*"
    - "/var/lib/docker/**/*"
```

Let's break down the important parts:

**Phases** execute in order: `install` -> `pre_build` -> `build` -> `post_build`. If any command in a phase fails (non-zero exit code), the build fails and subsequent phases are skipped (except `post_build`, which runs even on failure if you set `on-failure: CONTINUE`).

**Environment variables** can come from three sources: inline values, SSM Parameter Store, and Secrets Manager. CodeBuild resolves them before the build starts.

**Artifacts** are files preserved after the build completes. The `imagedefinitions.json` file is a special format that ECS deployments use to know which container image to pull.

**Cache** speeds up subsequent builds by preserving directories like pip's download cache or Docker layers.

### Creating a CodeBuild Project

```bash
# Create the CodeBuild service role first
aws iam create-role \
  --role-name codebuild-myapp-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "codebuild.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policies for ECR, logs, S3, and secrets
aws iam attach-role-policy \
  --role-name codebuild-myapp-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws iam put-role-policy \
  --role-name codebuild-myapp-role \
  --policy-name CodeBuildBasePolicy \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"logs:CreateLogGroup\",
          \"logs:CreateLogStream\",
          \"logs:PutLogEvents\"
        ],
        \"Resource\": \"arn:aws:logs:us-east-1:${ACCOUNT_ID}:log-group:/aws/codebuild/*\"
      },
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"s3:PutObject\",
          \"s3:GetObject\",
          \"s3:GetBucketAcl\",
          \"s3:GetBucketLocation\"
        ],
        \"Resource\": \"*\"
      },
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"ssm:GetParameters\",
          \"secretsmanager:GetSecretValue\"
        ],
        \"Resource\": \"*\"
      }
    ]
  }"

# Create the CodeBuild project
aws codebuild create-project \
  --name myapp-build \
  --source '{
    "type": "GITHUB",
    "location": "https://github.com/YOUR_ORG/myapp.git",
    "buildspec": "buildspec.yml"
  }' \
  --artifacts '{"type": "NO_ARTIFACTS"}' \
  --environment '{
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-x86_64-standard:5.0",
    "computeType": "BUILD_GENERAL1_SMALL",
    "privilegedMode": true
  }' \
  --service-role "arn:aws:iam::${ACCOUNT_ID}:role/codebuild-myapp-role"
```

The `privilegedMode: true` flag is required when building Docker images inside CodeBuild. Without it, the Docker daemon cannot start.

### Build Compute Types

| Compute Type | vCPU | Memory | Cost/min (US East) |
|-------------|------|--------|-------------------|
| BUILD_GENERAL1_SMALL | 3 | 3 GB | $0.005 |
| BUILD_GENERAL1_MEDIUM | 7 | 15 GB | $0.010 |
| BUILD_GENERAL1_LARGE | 15 | 72 GB | $0.020 |
| BUILD_GENERAL1_2XLARGE | 72 | 145 GB | $0.040 |

Most application builds work fine on SMALL. Use MEDIUM or LARGE for heavy compilation (C++, Rust) or large test suites.

---

## CodeDeploy: Deployment Strategies

CodeDeploy handles the how of getting new code onto your compute targets. It supports EC2 instances, on-premises servers, Lambda functions, and ECS services -- each with different deployment strategies.

### Deployment Types for ECS

```
Rolling Update (ECS native, no CodeDeploy needed):
+--------+--------+--------+--------+
| Old v1 | Old v1 | Old v1 | Old v1 |    Start: 4 tasks running v1
+--------+--------+--------+--------+
| Old v1 | Old v1 | Old v1 | NEW v2 |    Step 1: Replace 1 task
+--------+--------+--------+--------+
| Old v1 | Old v1 | NEW v2 | NEW v2 |    Step 2: Replace another
+--------+--------+--------+--------+
| NEW v2 | NEW v2 | NEW v2 | NEW v2 |    Done: All tasks v2
+--------+--------+--------+--------+

Blue/Green (CodeDeploy managed):
Blue (current):  [v1] [v1] [v1] [v1]  <-- ALB routes 100% here
Green (new):     [v2] [v2] [v2] [v2]  <-- Launched, health-checked

Traffic shift:
  - AllAtOnce:       0% --> 100% instantly
  - Canary10Percent5Minutes: 10% for 5 min, then 100%
  - Linear10PercentEvery1Minute: 10%, 20%, 30%... every minute
```

Blue/green is the gold standard for production ECS deployments because it provides:
1. **Instant rollback** -- just shift traffic back to the blue target group
2. **Zero downtime** -- the old tasks keep running until traffic fully shifts
3. **Validation window** -- test the green environment with real traffic before committing

### The appspec.yml File

For ECS deployments, CodeDeploy uses an `appspec.yml` that defines the task definition and optional lifecycle hooks:

```yaml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: "arn:aws:ecs:us-east-1:123456789012:task-definition/myapp:42"
        LoadBalancerInfo:
          ContainerName: "myapp"
          ContainerPort: 8080
        PlatformVersion: "LATEST"

Hooks:
  - BeforeInstall: "LambdaFunctionToValidateBeforeInstall"
  - AfterInstall: "LambdaFunctionToValidateAfterInstall"
  - AfterAllowTestTraffic: "LambdaFunctionToRunIntegrationTests"
  - BeforeAllowTraffic: "LambdaFunctionToValidateBeforeTraffic"
  - AfterAllowTraffic: "LambdaFunctionToRunSmokeTests"
```

Each hook references a Lambda function that CodeDeploy invokes at that point in the deployment. If any hook function returns failure, CodeDeploy rolls back automatically.

### Automatic Rollback

CodeDeploy can monitor CloudWatch Alarms during deployment and roll back if things go wrong:

```bash
# Create a deployment group with alarm-based rollback
aws deploy create-deployment-group \
  --application-name myapp \
  --deployment-group-name production \
  --deployment-config-name CodeDeployDefault.ECSCanary10Percent5Minutes \
  --ecs-services '[{
    "serviceName": "myapp-service",
    "clusterName": "production"
  }]' \
  --load-balancer-info '{
    "targetGroupPairInfoList": [{
      "targetGroups": [
        {"name": "myapp-blue-tg"},
        {"name": "myapp-green-tg"}
      ],
      "prodTrafficRoute": {
        "listenerArns": ["arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/myapp-alb/abc123/def456"]
      }
    }]
  }' \
  --auto-rollback-configuration '{
    "enabled": true,
    "events": ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  }' \
  --alarm-configuration '{
    "enabled": true,
    "alarms": [
      {"name": "myapp-5xx-errors-high"},
      {"name": "myapp-latency-p99-high"}
    ]
  }' \
  --service-role-arn arn:aws:iam::123456789012:role/codedeploy-ecs-role
```

This is powerful: deploy with canary at 10%, wait 5 minutes, and if the `5xx-errors-high` alarm fires during that window, automatically roll back. No human intervention needed.

---

## CodePipeline: Orchestrating the Full Workflow

CodePipeline connects source, build, and deploy stages into an automated workflow. When you push code to GitHub, the pipeline triggers automatically and progresses through each stage.

### Pipeline Architecture

```
+----------+    +------------+    +-----------+    +-----------+
|  Source   | -> |   Build    | -> |  Staging  | -> |Production |
|  (GitHub) |    | (CodeBuild)|    |  Deploy   |    |  Deploy   |
|           |    |            |    | (CodeDeploy)   | (CodeDeploy)|
+----------+    +------------+    +-----------+    +-----------+
                                       |                |
                                  [Manual approval] [Auto-rollback
                                                     on alarm]
```

### Creating a Pipeline with CLI

```bash
# Create the artifact bucket
aws s3 mb s3://myapp-pipeline-artifacts-${ACCOUNT_ID}

# Create the pipeline role
aws iam create-role \
  --role-name codepipeline-myapp-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "codepipeline.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# The pipeline definition (save as pipeline.json)
cat > /tmp/pipeline.json <<'EOF'
{
  "pipeline": {
    "name": "myapp-pipeline",
    "roleArn": "arn:aws:iam::ACCOUNT_ID:role/codepipeline-myapp-role",
    "artifactStore": {
      "type": "S3",
      "location": "myapp-pipeline-artifacts-ACCOUNT_ID"
    },
    "stages": [
      {
        "name": "Source",
        "actions": [
          {
            "name": "GitHub-Source",
            "actionTypeId": {
              "category": "Source",
              "owner": "AWS",
              "provider": "CodeStarSourceConnection",
              "version": "1"
            },
            "configuration": {
              "ConnectionArn": "arn:aws:codestar-connections:us-east-1:ACCOUNT_ID:connection/CONNECTION_ID",
              "FullRepositoryId": "YOUR_ORG/myapp",
              "BranchName": "main",
              "OutputArtifactFormat": "CODE_ZIP"
            },
            "outputArtifacts": [{"name": "SourceOutput"}]
          }
        ]
      },
      {
        "name": "Build",
        "actions": [
          {
            "name": "Docker-Build",
            "actionTypeId": {
              "category": "Build",
              "owner": "AWS",
              "provider": "CodeBuild",
              "version": "1"
            },
            "configuration": {
              "ProjectName": "myapp-build"
            },
            "inputArtifacts": [{"name": "SourceOutput"}],
            "outputArtifacts": [{"name": "BuildOutput"}]
          }
        ]
      },
      {
        "name": "Deploy-Staging",
        "actions": [
          {
            "name": "ECS-Deploy-Staging",
            "actionTypeId": {
              "category": "Deploy",
              "owner": "AWS",
              "provider": "ECS",
              "version": "1"
            },
            "configuration": {
              "ClusterName": "staging",
              "ServiceName": "myapp-service",
              "FileName": "imagedefinitions.json"
            },
            "inputArtifacts": [{"name": "BuildOutput"}]
          }
        ]
      },
      {
        "name": "Approval",
        "actions": [
          {
            "name": "Manual-Approval",
            "actionTypeId": {
              "category": "Approval",
              "owner": "AWS",
              "provider": "Manual",
              "version": "1"
            },
            "configuration": {
              "NotificationArn": "arn:aws:sns:us-east-1:ACCOUNT_ID:pipeline-approvals",
              "CustomData": "Review staging deployment before promoting to production"
            }
          }
        ]
      },
      {
        "name": "Deploy-Production",
        "actions": [
          {
            "name": "ECS-Deploy-Production",
            "actionTypeId": {
              "category": "Deploy",
              "owner": "AWS",
              "provider": "CodeDeployToECS",
              "version": "1"
            },
            "configuration": {
              "ApplicationName": "myapp",
              "DeploymentGroupName": "production",
              "TaskDefinitionTemplateArtifact": "BuildOutput",
              "AppSpecTemplateArtifact": "BuildOutput"
            },
            "inputArtifacts": [{"name": "BuildOutput"}]
          }
        ]
      }
    ]
  }
}
EOF

# Create the pipeline
aws codepipeline create-pipeline --cli-input-json file:///tmp/pipeline.json
```

### Source Providers: CodeStar Connections vs Webhooks

The modern way to connect GitHub to CodePipeline is through **CodeStar Connections** (also called CodeConnections). This replaces the older OAuth token and webhook approach:

```bash
# Create a connection (must be completed in the AWS Console)
aws codestar-connections create-connection \
  --provider-type GitHub \
  --connection-name myapp-github

# The connection starts in PENDING status
# Complete it via: AWS Console -> CodePipeline -> Settings -> Connections
# You'll authorize the AWS Connector for GitHub app
```

Why CodeStar Connections over webhooks:
- No long-lived OAuth token to manage or rotate
- GitHub App-based authentication (more secure, fine-grained permissions)
- Supports both clone and webhook trigger in one configuration
- Works with GitHub Organizations access controls

---

## OIDC Federation for GitHub Actions

If your team already uses GitHub Actions for CI and only needs AWS for deployment, you do not need CodeBuild or CodePipeline at all. Instead, configure OIDC federation so GitHub Actions can assume an IAM role directly.

### How OIDC Federation Works

```
GitHub Actions Workflow                        AWS
+----------------------+                 +------------------+
| 1. Job starts        |                 |                  |
| 2. Request OIDC      |                 |                  |
|    token from GitHub  |                 |                  |
| 3. Token contains:   |  trust chain   | IAM OIDC Provider |
|    - repo: org/myapp  | ------------> | trusts token.     |
|    - ref: refs/main   |               | actions.github.io |
|    - workflow: deploy |                 |                  |
| 4. AssumeRoleWith-   |                 | IAM Role:        |
|    WebIdentity       | --------------> | - Validates token |
| 5. Receive temp creds| <-------------- | - Returns creds   |
|    (15 min lifetime)  |                 | (STS temp creds)  |
+----------------------+                 +------------------+
```

### Setting Up OIDC Federation

```bash
# Step 1: Create the OIDC identity provider in IAM
aws iam create-open-id-connect-provider \
  --url "https://token.actions.githubusercontent.com" \
  --client-id-list "sts.amazonaws.com" \
  --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1"

# Step 2: Create the IAM role that GitHub Actions will assume
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

cat > /tmp/github-actions-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/myapp:ref:refs/heads/main"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name github-actions-deploy \
  --assume-role-policy-document file:///tmp/github-actions-trust.json

# Step 3: Attach permissions (e.g., ECR push + ECS deploy)
aws iam attach-role-policy \
  --role-name github-actions-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam put-role-policy \
  --role-name github-actions-deploy \
  --policy-name ECSDeployPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "iam:PassRole"
      ],
      "Resource": "*"
    }]
  }'
```

### GitHub Actions Workflow

```yaml
name: Deploy to ECS

on:
  push:
    branches: [main]

permissions:
  id-token: write   # Required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          aws-region: us-east-1

      - name: Login to ECR
        id: ecr-login
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.ecr-login.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/myapp:$IMAGE_TAG .
          docker push $ECR_REGISTRY/myapp:$IMAGE_TAG

      - name: Update ECS service
        env:
          ECR_REGISTRY: ${{ steps.ecr-login.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          # Get current task definition
          TASK_DEF=$(aws ecs describe-task-definition \
            --task-definition myapp \
            --query 'taskDefinition' --output json)

          # Update image in task definition
          NEW_TASK_DEF=$(echo $TASK_DEF | jq \
            --arg IMAGE "$ECR_REGISTRY/myapp:$IMAGE_TAG" \
            '.containerDefinitions[0].image = $IMAGE |
             del(.taskDefinitionArn, .revision, .status,
                 .requiresAttributes, .compatibilities,
                 .registeredAt, .registeredBy)')

          # Register new task definition
          NEW_REVISION=$(aws ecs register-task-definition \
            --cli-input-json "$NEW_TASK_DEF" \
            --query 'taskDefinition.taskDefinitionArn' --output text)

          # Update the service
          aws ecs update-service \
            --cluster production \
            --service myapp-service \
            --task-definition $NEW_REVISION \
            --force-new-deployment
```

The critical trust policy condition is `StringLike` on the `sub` claim. This restricts which repository and branch can assume the role. Without it, any GitHub repository could assume your role.

| Condition Pattern | What It Allows |
|-------------------|----------------|
| `repo:org/myapp:ref:refs/heads/main` | Only main branch pushes |
| `repo:org/myapp:*` | Any branch, any event in that repo |
| `repo:org/*:ref:refs/heads/main` | Main branch of any repo in the org |
| `repo:org/myapp:environment:production` | Only the "production" environment |

---

## Decision Matrix: CodePipeline vs GitHub Actions

| Factor | CodePipeline + CodeBuild | GitHub Actions + OIDC |
|--------|-------------------------|----------------------|
| All-AWS stack | Best fit | Extra config needed |
| Already using GitHub Actions | Redundant | Natural extension |
| Blue/green ECS deploys | CodeDeploy integration native | Requires custom scripting |
| Build caching | S3-based, manual config | GitHub Cache action, simpler |
| Cost (small team) | ~$5-20/month | Free tier generous (2,000 min/month) |
| Cost (large team) | Scales linearly | Can get expensive on private repos |
| Secrets management | SSM/SecretsManager native | GitHub Secrets + OIDC for AWS |
| Approval gates | Built-in manual approval stage | Environment protection rules |
| Visibility | AWS Console only | GitHub PR integration |

There is no single right answer. Many teams use a hybrid: GitHub Actions for CI (build + test) and CodeDeploy for production deployment (blue/green with alarm rollback).

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Storing AWS access keys as GitHub Secrets | Older tutorials still recommend this | Use OIDC federation -- no long-lived credentials to leak or rotate |
| Not setting `privilegedMode: true` in CodeBuild | Seems like a security flag to leave off | Required for Docker builds; without it, Docker daemon fails to start inside the build container |
| Buildspec `post_build` failing silently | Assuming post_build only runs on success | `post_build` runs even when `build` fails; check `$CODEBUILD_BUILD_SUCCEEDING` before push commands |
| Over-scoping the OIDC trust policy with `repo:org/*` | "It's easier to manage one role" | Create per-repo or per-team roles; a compromised repo should not access all your AWS resources |
| Using rolling updates instead of blue/green for production | "It's simpler" and the default | Blue/green gives instant rollback; rolling updates cannot undo a bad deployment without redeploying |
| Not adding CloudWatch Alarms to CodeDeploy | Not knowing about alarm-based rollback | Configure deployment group with alarm monitoring; automated rollback catches issues humans miss at 3 AM |
| Hardcoding account IDs in buildspec.yml | Copy-paste from examples | Use `aws sts get-caller-identity` or CodeBuild environment variables like `$AWS_ACCOUNT_ID` |
| Forgetting `imagedefinitions.json` format for ECS | Subtle format differences | ECS standard deploy needs `[{"name":"container","imageUri":"..."}]`; CodeDeploy ECS needs `appspec.yml` + `taskdef.json` |

---

## Quiz

<details>
<summary>1. What is the difference between the CodePipeline ECS deploy action and the CodeDeployToECS deploy action?</summary>

The **ECS deploy action** (`provider: ECS`) performs a standard rolling update -- it updates the ECS service's task definition and lets ECS replace tasks gradually. The **CodeDeployToECS action** (`provider: CodeDeployToECS`) uses AWS CodeDeploy to perform a blue/green deployment with traffic shifting. CodeDeployToECS provisions a new set of tasks (green), validates them with optional lifecycle hooks, then shifts ALB traffic from the old tasks (blue) to the new ones. CodeDeployToECS supports canary and linear traffic shifting, automatic rollback on CloudWatch alarms, and a manual approval window before cutting over full traffic. Use the ECS action for non-critical services; use CodeDeployToECS for production workloads where rollback speed matters.
</details>

<details>
<summary>2. Why does OIDC federation eliminate the need for IAM access keys in GitHub Actions?</summary>

With OIDC federation, GitHub's identity provider issues a short-lived JWT token that contains claims about the workflow (repository name, branch, actor). AWS IAM is configured to trust GitHub's OIDC provider and validate these tokens. When the GitHub Actions workflow calls `AssumeRoleWithWebIdentity`, AWS verifies the token's signature against GitHub's public keys and checks the claims against the IAM role's trust policy conditions. If everything matches, AWS returns temporary credentials (valid for about 15 minutes). No long-lived access key or secret key is stored anywhere -- not in GitHub Secrets, not in the repository, not in environment variables. This eliminates the risk of key leakage and removes the operational burden of rotating keys.
</details>

<details>
<summary>3. A CodeBuild build succeeds but the Docker image is not pushed to ECR. The push command is in the post_build phase. What happened?</summary>

The `post_build` phase runs regardless of whether the `build` phase succeeded or failed. If the `build` phase failed (perhaps a test failed or the Docker build had an error), the `post_build` phase still executes, but the Docker image was never built. The push command runs, tries to push a nonexistent image, and fails -- but since `post_build` already has a "build failed" status, this failure may not be prominently displayed. The fix is to check the `$CODEBUILD_BUILD_SUCCEEDING` environment variable at the start of `post_build` and skip the push if it equals `0`. Alternatively, move the push command to the end of the `build` phase.
</details>

<details>
<summary>4. Your OIDC trust policy uses "StringLike": "repo:myorg/*". Why is this dangerous?</summary>

This condition allows **any repository** in the `myorg` GitHub organization to assume the IAM role. If a less-critical repository (say, a documentation site or an internal tool) is compromised -- through a malicious pull request, a compromised dependency, or a disgruntled contributor -- the attacker can use that repository's GitHub Actions workflow to assume the IAM role and access whatever AWS resources the role permits. The principle of least privilege demands that each role's trust policy specifies the exact repository and ideally the exact branch or environment. Use `repo:myorg/myapp:ref:refs/heads/main` to restrict to a single repo's main branch, and create separate roles for separate repositories.
</details>

<details>
<summary>5. What is the imagedefinitions.json file, and when do you need it?</summary>

`imagedefinitions.json` is a JSON file that tells the CodePipeline ECS deploy action which container image to use. Its format is an array of objects: `[{"name":"container-name","imageUri":"123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:abc123"}]`. The `name` field must match the container name in your ECS task definition. You need this file when using the **standard ECS deploy action** in CodePipeline. When using **CodeDeployToECS** (blue/green), you instead need an `appspec.yml` and optionally a `taskdef.json` template. This distinction is a common source of confusion -- the wrong file format for the wrong deploy provider causes cryptic deployment failures.
</details>

<details>
<summary>6. How does CodeDeploy's canary deployment strategy reduce blast radius compared to all-at-once?</summary>

A canary deployment (e.g., `CodeDeployDefault.ECSCanary10Percent5Minutes`) shifts only 10% of traffic to the new version initially. During the 5-minute wait period, CloudWatch Alarms monitor error rates, latency, and other health metrics. If alarms trigger, CodeDeploy automatically rolls back, and only 10% of users were ever exposed to the bad deployment. With an all-at-once strategy, 100% of traffic shifts immediately, meaning all users are affected if the deployment is faulty. The canary approach gives you a validation window with real production traffic at minimal risk -- you catch regressions before they affect your entire user base.
</details>

---

## Hands-On Exercise: CodePipeline from GitHub Push to ECS Deploy

### Objective

Build a complete CI/CD pipeline: push code to GitHub, CodeBuild builds a Docker image and pushes to ECR, then ECS deploys the new image.

> **Note**: This exercise requires a GitHub repository and AWS resources. It will incur minor AWS charges (typically under $1 for the exercise duration).

### Setup

You need:
- A GitHub repository with a simple Dockerfile (a basic Nginx or Python Flask app)
- An ECR repository created (`aws ecr create-repository --repository-name cicd-lab`)
- An ECS cluster and service running (from Module 1.7, or create a simple one)

### Task 1: Create a Simple Application Repository

Set up a minimal application with a Dockerfile and buildspec.

<details>
<summary>Solution</summary>

Create these files in your GitHub repository:

**Dockerfile**:
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
```

**index.html**:
```html
<!DOCTYPE html>
<html>
<body><h1>CICD Lab - Version 1</h1></body>
</html>
```

**buildspec.yml**:
```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
      - ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"
      - aws ecr get-login-password | docker login --username AWS --password-stdin ${ECR_URI}
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-8)
      - IMAGE_TAG="${COMMIT_HASH:-latest}"
  build:
    commands:
      - docker build -t ${ECR_URI}/cicd-lab:${IMAGE_TAG} .
      - docker tag ${ECR_URI}/cicd-lab:${IMAGE_TAG} ${ECR_URI}/cicd-lab:latest
  post_build:
    commands:
      - docker push ${ECR_URI}/cicd-lab:${IMAGE_TAG}
      - docker push ${ECR_URI}/cicd-lab:latest
      - printf '[{"name":"cicd-lab","imageUri":"%s"}]' ${ECR_URI}/cicd-lab:${IMAGE_TAG} > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
```

Push these files to the `main` branch.
</details>

### Task 2: Set Up CodeStar Connection to GitHub

Connect your GitHub account to AWS for pipeline source access.

<details>
<summary>Solution</summary>

```bash
# Create the connection
aws codestar-connections create-connection \
  --provider-type GitHub \
  --connection-name cicd-lab-github

# Note the ConnectionArn from the output
# The connection is in PENDING status -- you must complete it in the console:
# 1. Go to AWS Console -> CodePipeline -> Settings -> Connections
# 2. Click "Update pending connection" for cicd-lab-github
# 3. Authorize the AWS Connector GitHub App
# 4. Select your GitHub account/organization
# 5. The status changes to "Available"

# Verify
aws codestar-connections list-connections \
  --query 'Connections[?ConnectionName==`cicd-lab-github`].[ConnectionArn,ConnectionStatus]' \
  --output table
```
</details>

### Task 3: Create the CodeBuild Project

<details>
<summary>Solution</summary>

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create CodeBuild service role
aws iam create-role \
  --role-name cicd-lab-codebuild-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "codebuild.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name cicd-lab-codebuild-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam put-role-policy \
  --role-name cicd-lab-codebuild-role \
  --policy-name CodeBuildLogs \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Effect\": \"Allow\",
      \"Action\": [\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],
      \"Resource\": \"arn:aws:logs:us-east-1:${ACCOUNT_ID}:log-group:/aws/codebuild/*\"
    },{
      \"Effect\": \"Allow\",
      \"Action\": [\"s3:PutObject\",\"s3:GetObject\",\"s3:GetBucketAcl\",\"s3:GetBucketLocation\"],
      \"Resource\": \"*\"
    }]
  }"

# Create the project
aws codebuild create-project \
  --name cicd-lab-build \
  --source '{"type":"CODEPIPELINE","buildspec":"buildspec.yml"}' \
  --artifacts '{"type":"CODEPIPELINE"}' \
  --environment '{
    "type":"LINUX_CONTAINER",
    "image":"aws/codebuild/amazonlinux2-x86_64-standard:5.0",
    "computeType":"BUILD_GENERAL1_SMALL",
    "privilegedMode":true
  }' \
  --service-role "arn:aws:iam::${ACCOUNT_ID}:role/cicd-lab-codebuild-role"
```
</details>

### Task 4: Create and Run the Pipeline

<details>
<summary>Solution</summary>

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CONNECTION_ARN=$(aws codestar-connections list-connections \
  --query 'Connections[?ConnectionName==`cicd-lab-github`].ConnectionArn' --output text)

# Create artifact bucket
aws s3 mb s3://cicd-lab-artifacts-${ACCOUNT_ID}

# Create pipeline role (needs broad permissions)
aws iam create-role \
  --role-name cicd-lab-pipeline-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "codepipeline.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam put-role-policy \
  --role-name cicd-lab-pipeline-role \
  --policy-name PipelinePolicy \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {\"Effect\":\"Allow\",\"Action\":[\"s3:*\"],\"Resource\":\"arn:aws:s3:::cicd-lab-artifacts-${ACCOUNT_ID}/*\"},
      {\"Effect\":\"Allow\",\"Action\":[\"codebuild:StartBuild\",\"codebuild:BatchGetBuilds\"],\"Resource\":\"*\"},
      {\"Effect\":\"Allow\",\"Action\":[\"ecs:*\"],\"Resource\":\"*\"},
      {\"Effect\":\"Allow\",\"Action\":[\"iam:PassRole\"],\"Resource\":\"*\"},
      {\"Effect\":\"Allow\",\"Action\":[\"codestar-connections:UseConnection\"],\"Resource\":\"${CONNECTION_ARN}\"}
    ]
  }"

# Create the pipeline (update YOUR_ORG/YOUR_REPO)
cat > /tmp/cicd-pipeline.json <<EOF
{
  "pipeline": {
    "name": "cicd-lab-pipeline",
    "roleArn": "arn:aws:iam::${ACCOUNT_ID}:role/cicd-lab-pipeline-role",
    "artifactStore": {
      "type": "S3",
      "location": "cicd-lab-artifacts-${ACCOUNT_ID}"
    },
    "stages": [
      {
        "name": "Source",
        "actions": [{
          "name": "GitHub",
          "actionTypeId": {"category":"Source","owner":"AWS","provider":"CodeStarSourceConnection","version":"1"},
          "configuration": {
            "ConnectionArn": "${CONNECTION_ARN}",
            "FullRepositoryId": "YOUR_ORG/YOUR_REPO",
            "BranchName": "main",
            "OutputArtifactFormat": "CODE_ZIP"
          },
          "outputArtifacts": [{"name": "SourceOutput"}]
        }]
      },
      {
        "name": "Build",
        "actions": [{
          "name": "DockerBuild",
          "actionTypeId": {"category":"Build","owner":"AWS","provider":"CodeBuild","version":"1"},
          "configuration": {"ProjectName": "cicd-lab-build"},
          "inputArtifacts": [{"name": "SourceOutput"}],
          "outputArtifacts": [{"name": "BuildOutput"}]
        }]
      },
      {
        "name": "Deploy",
        "actions": [{
          "name": "ECS-Deploy",
          "actionTypeId": {"category":"Deploy","owner":"AWS","provider":"ECS","version":"1"},
          "configuration": {
            "ClusterName": "YOUR_CLUSTER",
            "ServiceName": "YOUR_SERVICE",
            "FileName": "imagedefinitions.json"
          },
          "inputArtifacts": [{"name": "BuildOutput"}]
        }]
      }
    ]
  }
}
EOF

aws codepipeline create-pipeline --cli-input-json file:///tmp/cicd-pipeline.json

# Watch the pipeline execute
aws codepipeline get-pipeline-state \
  --name cicd-lab-pipeline \
  --query 'stageStates[*].[stageName,actionStates[0].latestExecution.status]' \
  --output table
```
</details>

### Task 5: Trigger the Pipeline with a Code Change

Update `index.html`, push to main, and verify the new version deploys.

<details>
<summary>Solution</summary>

```bash
# In your local repo clone
echo '<!DOCTYPE html><html><body><h1>CICD Lab - Version 2</h1><p>Deployed via pipeline!</p></body></html>' > index.html

git add index.html
git commit -m "feat: update to version 2"
git push origin main

# Monitor the pipeline
watch -n 10 'aws codepipeline get-pipeline-state \
  --name cicd-lab-pipeline \
  --query "stageStates[*].[stageName,actionStates[0].latestExecution.status]" \
  --output table'

# After Deploy stage shows "Succeeded", verify the ECS service updated
aws ecs describe-services \
  --cluster YOUR_CLUSTER \
  --services YOUR_SERVICE \
  --query 'services[0].deployments[*].[status,runningCount,taskDefinition]' \
  --output table
```
</details>

### Task 6: Clean Up

<details>
<summary>Solution</summary>

```bash
# Delete pipeline
aws codepipeline delete-pipeline --name cicd-lab-pipeline

# Delete CodeBuild project
aws codebuild delete-project --name cicd-lab-build

# Delete artifact bucket
aws s3 rb s3://cicd-lab-artifacts-${ACCOUNT_ID} --force

# Delete CodeStar connection
aws codestar-connections delete-connection --connection-arn $CONNECTION_ARN

# Delete IAM roles
aws iam delete-role-policy --role-name cicd-lab-codebuild-role --policy-name CodeBuildLogs
aws iam detach-role-policy --role-name cicd-lab-codebuild-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
aws iam delete-role --role-name cicd-lab-codebuild-role

aws iam delete-role-policy --role-name cicd-lab-pipeline-role --policy-name PipelinePolicy
aws iam delete-role --role-name cicd-lab-pipeline-role

# Delete ECR repository (if created for this lab)
aws ecr delete-repository --repository-name cicd-lab --force
```
</details>

### Success Criteria

- [ ] buildspec.yml builds Docker image and pushes to ECR
- [ ] CodeBuild project runs successfully with privileged mode enabled
- [ ] Pipeline triggers automatically on GitHub push
- [ ] imagedefinitions.json correctly maps container name to ECR URI
- [ ] ECS service updates with new task definition after pipeline completes
- [ ] Version 2 content is served by the updated service
- [ ] All resources cleaned up

---

## Next Module

Continue to [Module 1.12: Infrastructure as Code on AWS](module-1.12-cloudformation/) -- where you will learn to define all of the infrastructure you have been creating manually as declarative templates. Every resource from this CI/CD pipeline -- the IAM roles, CodeBuild project, pipeline definition, and ECS cluster -- can be managed as code.
