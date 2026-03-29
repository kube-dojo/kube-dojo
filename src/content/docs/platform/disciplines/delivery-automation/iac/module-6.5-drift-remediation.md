---
title: "Module 6.5: Drift Detection and Remediation"
slug: platform/disciplines/delivery-automation/iac/module-6.5-drift-remediation
sidebar:
  order: 6
---
## Complexity: [MEDIUM]
## Time to Complete: 45 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](module-6.1-iac-fundamentals/) - Core IaC concepts
- [Module 6.4: IaC at Scale](module-6.4-iac-at-scale/) - Scale challenges
- Basic understanding of desired state vs. actual state

---

## Why This Module Matters

**The Silent Security Group**

At 2:47 AM, a senior engineer at a healthcare company received an urgent page. Their compliance monitoring system had detected an anomaly: a production database was accepting connections from an IP range that wasn't in any approved configuration. The engineer's first thought was a breach. Their second thought was worse: *when did this happen?*

The investigation revealed a troubling timeline. Six weeks earlier, during an incident, an on-call engineer had manually added a security group rule to allow access from a vendor's IP for emergency debugging. The incident was resolved. The temporary rule was forgotten. For 42 days, the production database had a security hole that existed nowhere in their Terraform configurations.

The rule itself wasn't exploited—they got lucky. But the audit finding triggered a mandatory penetration test, delayed their SOC2 certification by three months, and cost $340,000 in remediation and consulting fees.

This module teaches you how to detect and remediate infrastructure drift—because the most dangerous configuration changes are the ones you don't know about.

---

## Understanding Infrastructure Drift

Infrastructure drift occurs when the actual state of resources diverges from the desired state defined in code.

```
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE DRIFT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   DESIRED STATE              ACTUAL STATE                       │
│   (Terraform)                (Cloud)                            │
│   ┌──────────────┐           ┌──────────────┐                  │
│   │ instance_type│           │ instance_type│                  │
│   │ = "t3.medium"│           │ = "t3.large" │ ◄── DRIFT!       │
│   ├──────────────┤           ├──────────────┤                  │
│   │ tags = {     │           │ tags = {     │                  │
│   │   env: prod  │           │   env: prod  │                  │
│   │ }            │           │   temp: true │ ◄── DRIFT!       │
│   ├──────────────┤           │ }            │                  │
│   │ sg_rules:    │           ├──────────────┤                  │
│   │ - port: 443  │           │ sg_rules:    │                  │
│   │   cidr: vpc  │           │ - port: 443  │                  │
│   │              │           │   cidr: vpc  │                  │
│   └──────────────┘           │ - port: 22   │ ◄── DRIFT!       │
│                              │   cidr: any  │                  │
│                              └──────────────┘                  │
│                                                                 │
│   DRIFT SOURCES:                                                │
│   ┌────────────────────────────────────────────────────────┐   │
│   │ • Manual console changes (most common)                  │   │
│   │ • Emergency fixes not back-ported to code               │   │
│   │ • Auto-scaling / self-healing systems                   │   │
│   │ • Other automation tools (scripts, Lambda)              │   │
│   │ • Cloud provider auto-updates                           │   │
│   │ • Malicious actors                                      │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Types of Drift

### 1. Configuration Drift

Resource attributes differ from code:

```hcl
# In Terraform:
resource "aws_instance" "app" {
  instance_type = "t3.medium"  # Desired
}

# In AWS:
# Instance is t3.large (someone resized manually)
```

### 2. State Drift

Resources exist that aren't in state:

```bash
# Resources in AWS but not in Terraform:
# - aws_security_group_rule (manually added)
# - aws_ebs_volume (created by console)
# - aws_iam_policy (created by script)

# These are "shadow IT" - unmanaged infrastructure
```

### 3. Code Drift

State doesn't match code (uncommitted changes):

```hcl
# main.tf has:
instance_type = "t3.large"

# terraform.tfstate has:
"instance_type": "t3.medium"

# Developer made local changes but never applied
```

---

## Detecting Drift

### Method 1: Terraform Plan

The simplest drift detection—run plan and look for unexpected changes:

```bash
# Basic drift detection
terraform plan -detailed-exitcode

# Exit codes:
# 0 = No changes (no drift)
# 1 = Error
# 2 = Changes detected (drift!)

# Script for CI/CD
#!/bin/bash
terraform plan -detailed-exitcode -out=tfplan
EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
    echo "⚠️ DRIFT DETECTED"
    terraform show tfplan
    # Send alert
    curl -X POST "$SLACK_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d '{"text":"🚨 Infrastructure drift detected in production!"}'
fi
```

### Method 2: Terraform Refresh (Deprecated Approach)

```bash
# Old way - updates state from actual infrastructure
terraform refresh

# New way - use plan with refresh
terraform plan -refresh-only

# Shows what would change in state without modifying resources
```

### Method 3: Scheduled Drift Detection

```yaml
# .github/workflows/drift-detection.yml
name: Drift Detection

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, production]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Terraform Init
        working-directory: environments/${{ matrix.environment }}
        run: terraform init

      - name: Check for Drift
        id: drift
        working-directory: environments/${{ matrix.environment }}
        run: |
          terraform plan -detailed-exitcode -out=tfplan 2>&1 | tee plan.txt
          echo "exit_code=$?" >> $GITHUB_OUTPUT
        continue-on-error: true

      - name: Report Drift
        if: steps.drift.outputs.exit_code == '2'
        run: |
          # Create GitHub Issue
          gh issue create \
            --title "🚨 Drift detected in ${{ matrix.environment }}" \
            --body "$(cat environments/${{ matrix.environment }}/plan.txt)" \
            --label "drift,infrastructure"

          # Slack notification
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H "Content-Type: application/json" \
            -d '{
              "text": "🚨 Infrastructure drift detected",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Environment:* ${{ matrix.environment }}\n*Details:* See GitHub Issue"
                  }
                }
              ]
            }'
```

### Method 4: AWS Config Rules

Detect drift at the cloud provider level:

```hcl
# AWS Config rule for security group drift
resource "aws_config_config_rule" "security_group_ssh" {
  name = "restricted-ssh"

  source {
    owner             = "AWS"
    source_identifier = "INCOMING_SSH_DISABLED"
  }

  scope {
    compliance_resource_types = ["AWS::EC2::SecurityGroup"]
  }
}

# Custom rule for required tags
resource "aws_config_config_rule" "required_tags" {
  name = "required-tags"

  source {
    owner             = "AWS"
    source_identifier = "REQUIRED_TAGS"
  }

  input_parameters = jsonencode({
    tag1Key   = "Environment"
    tag2Key   = "Team"
    tag3Key   = "ManagedBy"
  })
}

# Aggregate compliance across accounts
resource "aws_config_configuration_aggregator" "organization" {
  name = "organization-aggregator"

  organization_aggregation_source {
    all_regions = true
    role_arn    = aws_iam_role.config_aggregator.arn
  }
}

# Alert on non-compliant resources
resource "aws_cloudwatch_event_rule" "config_compliance" {
  name = "config-compliance-change"

  event_pattern = jsonencode({
    source      = ["aws.config"]
    detail-type = ["Config Rules Compliance Change"]
    detail = {
      newEvaluationResult = {
        complianceType = ["NON_COMPLIANT"]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.config_compliance.name
  target_id = "send-to-sns"
  arn       = aws_sns_topic.security_alerts.arn
}
```

### Method 5: Driftctl (Open Source)

Specialized tool for drift detection:

```bash
# Install driftctl
brew install driftctl

# Scan for drift
driftctl scan

# Output example:
# Found 142 resource(s)
#  - 134 covered by IaC
#  - 5 not covered by IaC  ◄── Unmanaged resources
#  - 3 missing on cloud    ◄── Deleted outside Terraform
#
# Coverage: 94%

# Scan with specific filters
driftctl scan --filter "Type=='aws_security_group'"

# Output as JSON for automation
driftctl scan --output json://drift-report.json

# Generate .driftignore for known exceptions
driftctl gen-driftignore
```

```yaml
# .driftignore - Known acceptable drift
# Auto-generated resources
aws_autoscaling_group.*
aws_launch_template.*

# Managed by other teams
aws_iam_role.external-*

# AWS-managed resources
aws_iam_service_linked_role.*
```

---

## Remediation Strategies

### Strategy 1: Auto-Remediate with Apply

For non-critical drift, automatically apply to restore desired state:

```yaml
# .github/workflows/auto-remediate.yml
name: Auto-Remediate Drift

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to remediate'
        required: true
        type: choice
        options: [dev, staging]  # Not production!

jobs:
  remediate:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Terraform Init
        working-directory: environments/${{ inputs.environment }}
        run: terraform init

      - name: Terraform Apply
        working-directory: environments/${{ inputs.environment }}
        run: terraform apply -auto-approve

      - name: Notify Success
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -d '{"text":"✅ Drift remediated in ${{ inputs.environment }}"}'
```

### Strategy 2: Import Unmanaged Resources

When drift is intentional, bring resources under management:

```bash
# Discover unmanaged resource
driftctl scan --filter "Type=='aws_security_group'"
# Found: aws_security_group.sg-12345 (not in state)

# Add to Terraform configuration
cat >> security_groups.tf << 'EOF'
resource "aws_security_group" "imported" {
  name        = "manually-created-sg"
  description = "Previously manual, now managed"
  vpc_id      = aws_vpc.main.id

  # Add rules to match actual state
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}
EOF

# Import into state
terraform import aws_security_group.imported sg-12345

# Verify
terraform plan  # Should show no changes
```

### Strategy 3: Accept Drift (Ignore Changes)

For resources managed elsewhere:

```hcl
# Auto-scaling managed instance counts
resource "aws_autoscaling_group" "app" {
  name                = "app-asg"
  desired_capacity    = 2
  min_size            = 2
  max_size            = 10

  lifecycle {
    ignore_changes = [
      desired_capacity,  # Managed by ASG policies
      target_group_arns, # Managed by ALB
    ]
  }
}

# EKS node group with cluster autoscaler
resource "aws_eks_node_group" "workers" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "workers"

  scaling_config {
    desired_size = 3
    min_size     = 2
    max_size     = 20
  }

  lifecycle {
    ignore_changes = [
      scaling_config[0].desired_size,  # Cluster autoscaler manages this
    ]
  }
}

# Secrets rotated externally
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = random_password.db.result

  lifecycle {
    ignore_changes = [secret_string]  # Rotated by Lambda
  }
}
```

### Strategy 4: Prevent Drift at Source

Block manual changes entirely:

```hcl
# SCP to prevent manual changes to tagged resources
resource "aws_organizations_policy" "prevent_manual_changes" {
  name    = "PreventManualChangesToManagedResources"
  type    = "SERVICE_CONTROL_POLICY"
  content = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyManualChangesToManagedResources"
        Effect    = "Deny"
        Action    = [
          "ec2:ModifyInstanceAttribute",
          "ec2:ModifySecurityGroupRules",
          "rds:ModifyDBInstance",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy"
        ]
        Resource  = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/ManagedBy" = "terraform"
          }
          # Exception for Terraform role
          "ArnNotLike" = {
            "aws:PrincipalArn" = "arn:aws:iam::*:role/TerraformRole"
          }
        }
      }
    ]
  })
}

# IAM policy preventing modifications
resource "aws_iam_policy" "read_only_managed" {
  name = "ReadOnlyManagedResources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "DenyWriteToManagedResources"
        Effect   = "Deny"
        Action   = [
          "ec2:*",
          "rds:*",
          "s3:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/ManagedBy" = "terraform"
          }
        }
      },
      {
        Sid      = "AllowReadToManagedResources"
        Effect   = "Allow"
        Action   = [
          "ec2:Describe*",
          "rds:Describe*",
          "s3:Get*",
          "s3:List*"
        ]
        Resource = "*"
      }
    ]
  })
}
```

---

## Continuous Drift Monitoring

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               DRIFT MONITORING ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │  Scheduled   │                                               │
│  │    Job       │──────┐                                        │
│  │  (6 hours)   │      │                                        │
│  └──────────────┘      │                                        │
│                        ▼                                        │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐         │
│  │  CloudTrail  │  │    Drift      │  │   AWS        │         │
│  │   Events     │─▶│   Detection   │◀─│   Config     │         │
│  │              │  │   Service     │  │   Rules      │         │
│  └──────────────┘  └───────────────┘  └──────────────┘         │
│                           │                                     │
│          ┌────────────────┼────────────────┐                   │
│          ▼                ▼                ▼                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │   Metrics    │ │   Alerts     │ │   Reports    │            │
│  │  Dashboard   │ │  (Slack/PD)  │ │  (Weekly)    │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│          │                │                │                    │
│          └────────────────┼────────────────┘                   │
│                           ▼                                     │
│                  ┌──────────────┐                               │
│                  │ Remediation  │                               │
│                  │  Runbook     │                               │
│                  └──────────────┘                               │
│                           │                                     │
│          ┌────────────────┼────────────────┐                   │
│          ▼                ▼                ▼                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │    Auto      │ │   Manual     │ │   Accept &   │            │
│  │  Remediate   │ │   Review     │ │   Document   │            │
│  │   (Dev)      │ │   (Prod)     │ │   (Known)    │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### CloudWatch Dashboard

```hcl
resource "aws_cloudwatch_dashboard" "drift_monitoring" {
  dashboard_name = "InfrastructureDrift"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Drift Detection Results"
          region = "us-east-1"
          metrics = [
            ["Terraform", "DriftDetected", "Environment", "production", { stat = "Sum", period = 86400 }],
            ["Terraform", "DriftDetected", "Environment", "staging", { stat = "Sum", period = 86400 }],
            ["Terraform", "DriftDetected", "Environment", "dev", { stat = "Sum", period = 86400 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "AWS Config Compliance"
          region = "us-east-1"
          metrics = [
            ["AWS/Config", "ComplianceByConfigRule", "ConfigRuleName", "required-tags"],
            ["AWS/Config", "ComplianceByConfigRule", "ConfigRuleName", "restricted-ssh"],
            ["AWS/Config", "ComplianceByConfigRule", "ConfigRuleName", "encrypted-volumes"]
          ]
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 6
        width  = 24
        height = 2
        properties = {
          markdown = "## Drift Remediation\n\n| Priority | Action |\n|----------|--------|\n| Critical | [Run Auto-Remediation](https://github.com/company/infra/actions/workflows/remediate.yml) |\n| Review | [View Drift Report](https://github.com/company/infra/issues?q=label:drift) |"
        }
      }
    ]
  })
}
```

### Custom Drift Metrics

```python
# Lambda function to publish drift metrics
import boto3
import subprocess
import json

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    environment = event['environment']

    # Run terraform plan
    result = subprocess.run(
        ['terraform', 'plan', '-detailed-exitcode', '-json'],
        cwd=f'/terraform/{environment}',
        capture_output=True,
        text=True
    )

    # Parse plan output
    drift_detected = result.returncode == 2
    changes = parse_plan_changes(result.stdout)

    # Publish metrics
    cloudwatch.put_metric_data(
        Namespace='Terraform',
        MetricData=[
            {
                'MetricName': 'DriftDetected',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': 1 if drift_detected else 0,
                'Unit': 'Count'
            },
            {
                'MetricName': 'ResourcesWithDrift',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': changes['total'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'AddedResources',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': changes['add'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'ChangedResources',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': changes['change'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'DestroyedResources',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': changes['destroy'],
                'Unit': 'Count'
            }
        ]
    )

    return {
        'drift_detected': drift_detected,
        'changes': changes
    }

def parse_plan_changes(plan_json):
    changes = {'add': 0, 'change': 0, 'destroy': 0, 'total': 0}
    for line in plan_json.split('\n'):
        try:
            data = json.loads(line)
            if data.get('@level') == 'info' and 'changes' in data.get('@message', ''):
                # Parse "Plan: X to add, Y to change, Z to destroy"
                msg = data['@message']
                # ... parsing logic
        except json.JSONDecodeError:
            continue
    return changes
```

---

## War Story: The 42-Day Security Hole

**Company**: Healthcare SaaS provider
**Incident**: Undiscovered security group drift for 6 weeks

**Timeline**:

- **Day 0 (Friday 11 PM)**: Production incident—vendor can't connect for emergency support
- **Day 0 (11:30 PM)**: On-call engineer adds temporary security group rule via console
- **Day 0 (Saturday 1 AM)**: Incident resolved, engineer goes to sleep
- **Day 1 (Saturday)**: Engineer has day off, forgets to remove rule
- **Day 2-41**: Rule persists, nobody notices
- **Day 42 (Wednesday 2 PM)**: Compliance scanner detects anomaly
- **Day 42 (3 PM)**: Security team investigates, finds 42-day-old rule
- **Day 42 (5 PM)**: Incident declared, forensics begins

**What the Security Group Looked Like**:

```hcl
# In Terraform (desired state):
resource "aws_security_group_rule" "db_access" {
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = ["10.0.0.0/8"]  # Internal only
  security_group_id = aws_security_group.db.id
}

# Actual AWS state (unknown to Terraform):
# - Original rule (10.0.0.0/8) ✓
# - Manual rule (vendor IP: 203.0.113.0/24) ← 42 days old!
```

**Financial Impact**:
- Incident response team: $45K
- External forensics: $120K
- Compliance consultant: $85K
- Penetration test (required): $65K
- SOC2 delay (3 months): Lost deal worth $2.1M
- Additional security monitoring: $25K/year
- **Total**: $340K direct + $2.1M opportunity cost

**Detection That Would Have Caught This**:

```yaml
# If they had drift detection running...
# Day 1 detection would have shown:

terraform plan output:
# aws_security_group.db has changed
#
# ~ resource "aws_security_group" "db" {
#     ~ ingress {
#         + {
#           + cidr_blocks = ["203.0.113.0/24"]  # UNEXPECTED!
#           + from_port   = 5432
#           + to_port     = 5432
#           + protocol    = "tcp"
#         }
#       }
#   }
#
# 1 resource has drift
```

**Prevention Measures Implemented**:

```hcl
# 1. SCP preventing manual security group changes
resource "aws_organizations_policy" "no_manual_sg" {
  content = jsonencode({
    Statement = [{
      Effect = "Deny"
      Action = ["ec2:AuthorizeSecurityGroupIngress"]
      Resource = "*"
      Condition = {
        ArnNotLike = {
          "aws:PrincipalArn" = "arn:aws:iam::*:role/TerraformRole"
        }
      }
    }]
  })
}

# 2. Drift detection every 6 hours
# (GitHub Actions workflow)

# 3. Break-glass procedure for emergencies
# - Requires ticket number
# - Auto-expires after 4 hours
# - Creates GitHub issue for follow-up

# 4. CloudTrail alerting on any SG changes
resource "aws_cloudwatch_event_rule" "sg_changes" {
  event_pattern = jsonencode({
    source = ["aws.ec2"]
    detail-type = ["AWS API Call via CloudTrail"]
    detail = {
      eventName = [
        "AuthorizeSecurityGroupIngress",
        "AuthorizeSecurityGroupEgress",
        "RevokeSecurityGroupIngress",
        "RevokeSecurityGroupEgress"
      ]
    }
  })
}
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No drift detection | Silent divergence from desired state | Scheduled terraform plan |
| Ignoring drift alerts | Alert fatigue, missed critical drift | Categorize severity, auto-remediate low-risk |
| Manual console access | Primary drift source | SCPs, read-only console access |
| No break-glass procedure | Emergency changes bypass IaC entirely | Tracked emergency access with auto-expiry |
| Too broad ignore_changes | Masks legitimate drift | Only ignore what's truly managed elsewhere |
| No drift metrics | Can't track drift trends | CloudWatch metrics, dashboards |
| Remediation without review | Apply might break things | Always review production drift before apply |
| No root cause analysis | Same drift recurs | Track drift sources, fix process gaps |

---

## Quiz

<details>
<summary>1. What are the three main types of infrastructure drift?</summary>

**Answer**:
1. **Configuration Drift**: Resource attributes in cloud differ from Terraform code
2. **State Drift**: Resources exist in cloud but not in Terraform state (unmanaged)
3. **Code Drift**: Terraform code and state don't match (uncommitted local changes)
</details>

<details>
<summary>2. What exit code does `terraform plan -detailed-exitcode` return when drift is detected?</summary>

**Answer**: Exit code **2** indicates changes are needed (drift detected).
- 0 = No changes, infrastructure matches configuration
- 1 = Error during planning
- 2 = Succeeded with non-empty diff (drift or planned changes)
</details>

<details>
<summary>3. When should you use `lifecycle { ignore_changes = [...] }` versus fixing the drift?</summary>

**Answer**: Use `ignore_changes` when:
- Resource is managed by another system (auto-scaling, cluster autoscaler)
- Attribute is intentionally dynamic (secret rotation, tags added by AWS)
- You're migrating and need temporary flexibility

Fix the drift when:
- Change was unintentional (manual console change)
- Change violates security/compliance requirements
- Change could affect system behavior
- Source of change is unknown
</details>

<details>
<summary>4. Calculate the cost impact if drift detection runs every 6 hours versus no detection, assuming drift causes one 8-hour outage per quarter at $50K/hour.</summary>

**Answer**:
- **Without detection**: 1 outage × 8 hours × $50K/hour = **$400K/quarter** = **$1.6M/year**
- **With 6-hour detection**: Maximum 6-hour exposure window
  - Assume 75% of drift is caught before causing outage
  - Cost: 0.25 × $400K = **$100K/quarter** = **$400K/year**
- **Annual savings**: $1.6M - $400K = **$1.2M/year**
- Plus: Reduced security risk, compliance benefits, team confidence
</details>

<details>
<summary>5. What is driftctl and how does it differ from terraform plan?</summary>

**Answer**:
**driftctl** is a specialized drift detection tool that:
- Scans cloud resources directly (not just state)
- Detects **unmanaged resources** (exist in cloud but not in Terraform)
- Provides coverage metrics (% of cloud resources managed by IaC)
- Supports `.driftignore` for known exceptions
- Faster for drift-only scans

**terraform plan** is:
- Part of standard Terraform workflow
- Detects drift from state, not from all cloud resources
- Doesn't find unmanaged resources (shadow IT)
- Shows planned changes as well as drift
</details>

<details>
<summary>6. What is a Service Control Policy (SCP) and how can it prevent drift?</summary>

**Answer**: An SCP is an AWS Organizations policy that sets permission guardrails across accounts. For drift prevention:
- Deny manual changes to resources tagged as Terraform-managed
- Allow exceptions only for designated Terraform roles
- Apply at organizational unit level for broad coverage
- Cannot be overridden by IAM policies (hard boundary)

Example: Deny `ec2:ModifySecurityGroupRules` for any principal except `TerraformRole`.
</details>

<details>
<summary>7. A production database security group has a manually added rule that's been there for 42 days. What's the remediation process?</summary>

**Answer**:
1. **Assess risk**: Is the rule still needed? Is it overly permissive?
2. **Document**: Create incident report, note who/when/why
3. **Decide action**:
   - If needed: Add to Terraform code, run apply to sync state
   - If not needed: Run Terraform apply to remove (terraform is source of truth)
   - If unsure: Add to code temporarily with TODO, schedule review
4. **Root cause**: Why was it added manually? Fix process gap
5. **Prevent recurrence**: SCPs, alerts, break-glass procedure
6. **Monitor**: Watch for similar drift patterns
</details>

<details>
<summary>8. Why is auto-remediation typically not recommended for production environments?</summary>

**Answer**:
- **Risk of disruption**: Reverting drift might break something that depends on it
- **Loss of information**: Manual changes might be intentional emergency fixes
- **Blast radius**: Auto-apply could cascade to dependent resources
- **Compliance**: Changes should be reviewed and approved
- **Audit trail**: Need human decision recorded for compliance

Better approach for production:
- Alert on drift
- Create ticket for review
- Require approval before remediation
- Auto-remediate only in dev/staging
</details>

---

## Hands-On Exercise

**Objective**: Set up drift detection and demonstrate remediation strategies.

### Part 1: Create Driftable Infrastructure

```bash
# Create test infrastructure
mkdir -p drift-lab
cd drift-lab

cat > main.tf << 'EOF'
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Create a file that we'll manually modify
resource "local_file" "config" {
  filename = "${path.module}/config.json"
  content  = jsonencode({
    environment = "production"
    debug       = false
    timeout     = 30
    tags = {
      ManagedBy = "terraform"
    }
  })
}

output "config_path" {
  value = local_file.config.filename
}
EOF

# Apply initial configuration
terraform init
terraform apply -auto-approve

# Verify file contents
cat config.json
```

### Part 2: Introduce Drift

```bash
# Manually modify the file (simulating console change)
cat > config.json << 'EOF'
{
  "environment": "production",
  "debug": true,
  "timeout": 60,
  "tags": {
    "ManagedBy": "terraform",
    "TempFix": "ticket-12345"
  }
}
EOF

# Check for drift
terraform plan -detailed-exitcode
echo "Exit code: $?"

# View the drift
terraform plan
```

### Part 3: Remediation Options

```bash
# Option A: Revert to desired state
terraform apply -auto-approve
cat config.json  # Back to original

# Option B: Accept drift by updating code
# First, introduce drift again
cat > config.json << 'EOF'
{
  "environment": "production",
  "debug": true,
  "timeout": 60
}
EOF

# Update Terraform to match actual state
cat > main.tf << 'EOF'
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

resource "local_file" "config" {
  filename = "${path.module}/config.json"
  content  = jsonencode({
    environment = "production"
    debug       = true       # Updated to match reality
    timeout     = 60         # Updated to match reality
    tags = {
      ManagedBy = "terraform"
    }
  })
}
EOF

terraform plan  # Should show changes to match our new code
```

### Part 4: Automated Detection Script

```bash
# Create drift detection script
cat > detect-drift.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Running drift detection..."

terraform plan -detailed-exitcode -out=tfplan 2>&1 | tee plan.txt
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No drift detected"
elif [ $EXIT_CODE -eq 2 ]; then
    echo "⚠️ DRIFT DETECTED!"
    echo ""
    echo "Changes found:"
    terraform show tfplan
    echo ""
    echo "Remediation options:"
    echo "1. Run 'terraform apply' to restore desired state"
    echo "2. Update Terraform code to accept changes"
    echo "3. Add lifecycle { ignore_changes } for managed attributes"
else
    echo "❌ Error during drift detection"
    exit 1
fi

exit $EXIT_CODE
EOF

chmod +x detect-drift.sh

# Test the script
./detect-drift.sh
```

### Success Criteria

- [ ] Initial infrastructure deployed successfully
- [ ] Manual changes introduced (drift created)
- [ ] `terraform plan -detailed-exitcode` returns exit code 2
- [ ] Drift details visible in plan output
- [ ] At least one remediation option successfully executed
- [ ] Detection script works and provides actionable output

---

## Key Takeaways

- [ ] **Drift is inevitable** - Manual changes, emergencies, other automation all cause drift
- [ ] **Detect early, detect often** - Run terraform plan on schedule (every 6 hours minimum)
- [ ] **Categorize drift severity** - Security drift is critical, tag drift might be informational
- [ ] **Automate detection, review remediation** - Auto-apply only for non-production
- [ ] **Use ignore_changes sparingly** - Only for truly externally-managed attributes
- [ ] **Prevent at source** - SCPs, read-only console access, break-glass procedures
- [ ] **Track metrics** - Drift frequency, time-to-detect, time-to-remediate
- [ ] **Root cause analysis** - Fix the process that caused drift, not just the drift
- [ ] **Document exceptions** - Known drift should be in .driftignore with explanation
- [ ] **Break-glass needs follow-up** - Emergency changes must be codified within 24 hours

---

## Did You Know?

> **Drift Statistics**: A 2023 survey found that 73% of organizations experience infrastructure drift within 24 hours of deployment, and 91% experience drift within one week.

> **Detection Gap**: The average time to detect infrastructure drift is 12 days, but security-related drift takes an average of 27 days to discover.

> **Driftctl Origins**: Driftctl was created by Cloudskiff (now part of Snyk) in 2020 specifically to solve the problem of detecting unmanaged cloud resources that Terraform plan cannot find.

> **Cost of Drift**: According to a 2023 report, organizations spend an average of 4.2 hours per week manually investigating and remediating infrastructure drift, costing approximately $35,000 per engineer annually.

---

## Related Modules

> **GitOps Drift**: For GitOps-specific drift detection (ArgoCD sync, Flux reconciliation), see [GitOps Drift Detection](../gitops/module-3.4-drift-detection/).

---

## Next Module

Continue to [Module 6.6: IaC Cost Management](module-6.6-iac-cost-management/) to learn how to estimate, track, and optimize infrastructure costs directly in your Terraform workflow.
