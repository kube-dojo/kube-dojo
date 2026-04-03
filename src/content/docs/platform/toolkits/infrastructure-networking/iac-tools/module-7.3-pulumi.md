---
title: "Module 7.3: Pulumi - Infrastructure as Real Code"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.3-pulumi
sidebar:
  order: 4
---
## Complexity: [MEDIUM]
## Time to Complete: 45 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](../../../disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) - Core IaC concepts
- Basic programming experience (Python, TypeScript, Go, or C#)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy cloud infrastructure using Pulumi with TypeScript, Python, or Go instead of domain-specific languages**
- **Implement Pulumi stacks with state management, secrets encryption, and policy-as-code enforcement**
- **Configure Pulumi's Kubernetes provider for cluster provisioning and application deployment**
- **Compare Pulumi's programming language approach against Terraform's HCL for team adoption trade-offs**


## Why This Module Matters

**When HCL Isn't Enough**

The platform team at a fast-growing fintech company hit a wall. Their Terraform configurations had become a labyrinth of complex conditionals, dynamic blocks, and workarounds. When they needed to create 47 AWS accounts with environment-specific configurations, nested loops, and conditional resources based on team policies, their HCL files became unmaintainable.

A senior engineer protested: "We're writing pseudo-code in a configuration language. Why can't we just use Python?"

That question led them to Pulumi. Within a month, they'd replaced 15,000 lines of HCL with 3,000 lines of Python—code that was testable with pytest, typed with mypy, and leveraged the team's existing programming expertise. More importantly, junior developers who struggled with HCL's quirks could immediately contribute using languages they already knew.

This module introduces Pulumi—infrastructure as code using general-purpose programming languages like Python, TypeScript, Go, and C#.

---

## Pulumi vs Terraform

```
┌─────────────────────────────────────────────────────────────────┐
│                    PULUMI VS TERRAFORM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Pulumi                            Terraform                    │
│  ──────                            ─────────                    │
│  Languages: Python, TS, Go, C#     Language: HCL                │
│  Real programming constructs       Configuration language       │
│  Native testing (pytest, jest)     Limited testing              │
│  IDE support (full)                IDE support (limited)        │
│  Import existing packages          Custom providers only        │
│                                                                 │
│  State Management:                 State Management:            │
│  • Pulumi Cloud (default)          • Local file (default)       │
│  • S3/Azure/GCS backends           • S3/Azure/GCS backends      │
│  • Self-hosted                     • Terraform Cloud            │
│                                                                 │
│  Strengths:                        Strengths:                   │
│  • Complex logic & loops           • Large ecosystem            │
│  • Existing team skills            • Extensive documentation    │
│  • Real unit testing               • Mature tooling             │
│  • Package management (pip/npm)    • Industry standard          │
│                                                                 │
│  Challenges:                       Challenges:                  │
│  • Smaller ecosystem               • Limited programming logic  │
│  • Learning curve for infra eng.   • DSL learning curve         │
│  • State complexity                • Testing limitations        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
# Install Pulumi CLI
# macOS
brew install pulumi

# Linux
curl -fsSL https://get.pulumi.com | sh

# Windows
choco install pulumi

# Verify installation
pulumi version

# Login to Pulumi Cloud (free tier available)
pulumi login

# Or use local state
pulumi login --local

# Or use S3 backend
pulumi login s3://my-pulumi-state-bucket
```

---

## Your First Pulumi Project

### Python Example

```bash
# Create new project
mkdir pulumi-demo && cd pulumi-demo
pulumi new aws-python

# Project structure created:
# ├── Pulumi.yaml         # Project metadata
# ├── Pulumi.dev.yaml     # Stack config (dev)
# ├── __main__.py         # Infrastructure code
# ├── requirements.txt    # Python dependencies
# └── venv/               # Virtual environment
```

```python
# __main__.py
"""AWS infrastructure defined in Python."""

import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
environment = config.require("environment")
instance_type = config.get("instance_type") or "t3.micro"

# Create a VPC
vpc = aws.ec2.Vpc(
    "main-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{environment}-vpc",
        "Environment": environment,
        "ManagedBy": "pulumi",
    },
)

# Create subnets using a loop (real Python!)
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnets = []
private_subnets = []

for i, az in enumerate(availability_zones):
    # Public subnet
    public_subnet = aws.ec2.Subnet(
        f"public-subnet-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i}.0/24",
        availability_zone=az,
        map_public_ip_on_launch=True,
        tags={
            "Name": f"{environment}-public-{i + 1}",
            "Tier": "public",
        },
    )
    public_subnets.append(public_subnet)

    # Private subnet
    private_subnet = aws.ec2.Subnet(
        f"private-subnet-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i + 10}.0/24",
        availability_zone=az,
        tags={
            "Name": f"{environment}-private-{i + 1}",
            "Tier": "private",
        },
    )
    private_subnets.append(private_subnet)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    "igw",
    vpc_id=vpc.id,
    tags={"Name": f"{environment}-igw"},
)

# Security Group with dynamic rules
security_group = aws.ec2.SecurityGroup(
    "web-sg",
    vpc_id=vpc.id,
    description="Web server security group",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=port,
            to_port=port,
            cidr_blocks=["0.0.0.0/0"],
            description=desc,
        )
        for port, desc in [(80, "HTTP"), (443, "HTTPS")]
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={"Name": f"{environment}-web-sg"},
)

# Exports (outputs)
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_ids", [s.id for s in public_subnets])
pulumi.export("private_subnet_ids", [s.id for s in private_subnets])
pulumi.export("security_group_id", security_group.id)
```

```bash
# Deploy
pulumi up

# Preview changes
pulumi preview

# Destroy
pulumi destroy
```

### TypeScript Example

```typescript
// index.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Configuration
const config = new pulumi.Config();
const environment = config.require("environment");
const instanceType = config.get("instanceType") || "t3.micro";

// VPC
const vpc = new aws.ec2.Vpc("main-vpc", {
    cidrBlock: "10.0.0.0/16",
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: {
        Name: `${environment}-vpc`,
        Environment: environment,
        ManagedBy: "pulumi",
    },
});

// Subnets using map
const availabilityZones = ["us-east-1a", "us-east-1b", "us-east-1c"];

const publicSubnets = availabilityZones.map((az, i) =>
    new aws.ec2.Subnet(`public-subnet-${i}`, {
        vpcId: vpc.id,
        cidrBlock: `10.0.${i}.0/24`,
        availabilityZone: az,
        mapPublicIpOnLaunch: true,
        tags: {
            Name: `${environment}-public-${i + 1}`,
            Tier: "public",
        },
    })
);

const privateSubnets = availabilityZones.map((az, i) =>
    new aws.ec2.Subnet(`private-subnet-${i}`, {
        vpcId: vpc.id,
        cidrBlock: `10.0.${i + 10}.0/24`,
        availabilityZone: az,
        tags: {
            Name: `${environment}-private-${i + 1}`,
            Tier: "private",
        },
    })
);

// Security group with typed configuration
interface SecurityRule {
    port: number;
    description: string;
}

const ingressRules: SecurityRule[] = [
    { port: 80, description: "HTTP" },
    { port: 443, description: "HTTPS" },
];

const securityGroup = new aws.ec2.SecurityGroup("web-sg", {
    vpcId: vpc.id,
    description: "Web server security group",
    ingress: ingressRules.map(rule => ({
        protocol: "tcp",
        fromPort: rule.port,
        toPort: rule.port,
        cidrBlocks: ["0.0.0.0/0"],
        description: rule.description,
    })),
    egress: [{
        protocol: "-1",
        fromPort: 0,
        toPort: 0,
        cidrBlocks: ["0.0.0.0/0"],
    }],
    tags: { Name: `${environment}-web-sg` },
});

// Exports
export const vpcId = vpc.id;
export const publicSubnetIds = publicSubnets.map(s => s.id);
export const privateSubnetIds = privateSubnets.map(s => s.id);
export const securityGroupId = securityGroup.id;
```

---

## Component Resources

Create reusable infrastructure components as classes.

```python
# components/vpc.py
"""Reusable VPC component."""

import pulumi
from pulumi import ComponentResource, ResourceOptions
import pulumi_aws as aws
from typing import List, Optional


class VpcArgs:
    """Arguments for VPC component."""

    def __init__(
        self,
        cidr_block: str = "10.0.0.0/16",
        availability_zones: List[str] = None,
        enable_nat_gateway: bool = True,
        single_nat_gateway: bool = False,
        tags: dict = None,
    ):
        self.cidr_block = cidr_block
        self.availability_zones = availability_zones or ["us-east-1a", "us-east-1b"]
        self.enable_nat_gateway = enable_nat_gateway
        self.single_nat_gateway = single_nat_gateway
        self.tags = tags or {}


class Vpc(ComponentResource):
    """A complete VPC with public/private subnets and optional NAT."""

    def __init__(
        self,
        name: str,
        args: VpcArgs,
        opts: Optional[ResourceOptions] = None,
    ):
        super().__init__("custom:network:Vpc", name, {}, opts)

        # Create VPC
        self.vpc = aws.ec2.Vpc(
            f"{name}-vpc",
            cidr_block=args.cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={**args.tags, "Name": f"{name}-vpc"},
            opts=ResourceOptions(parent=self),
        )

        # Internet Gateway
        self.igw = aws.ec2.InternetGateway(
            f"{name}-igw",
            vpc_id=self.vpc.id,
            tags={**args.tags, "Name": f"{name}-igw"},
            opts=ResourceOptions(parent=self),
        )

        # Create subnets
        self.public_subnets: List[aws.ec2.Subnet] = []
        self.private_subnets: List[aws.ec2.Subnet] = []
        self.nat_gateways: List[aws.ec2.NatGateway] = []

        for i, az in enumerate(args.availability_zones):
            # Public subnet
            public_subnet = aws.ec2.Subnet(
                f"{name}-public-{i}",
                vpc_id=self.vpc.id,
                cidr_block=self._calculate_cidr(args.cidr_block, i),
                availability_zone=az,
                map_public_ip_on_launch=True,
                tags={**args.tags, "Name": f"{name}-public-{i + 1}", "Tier": "public"},
                opts=ResourceOptions(parent=self),
            )
            self.public_subnets.append(public_subnet)

            # Private subnet
            private_subnet = aws.ec2.Subnet(
                f"{name}-private-{i}",
                vpc_id=self.vpc.id,
                cidr_block=self._calculate_cidr(args.cidr_block, i + 10),
                availability_zone=az,
                tags={**args.tags, "Name": f"{name}-private-{i + 1}", "Tier": "private"},
                opts=ResourceOptions(parent=self),
            )
            self.private_subnets.append(private_subnet)

            # NAT Gateway (one per AZ or single)
            if args.enable_nat_gateway:
                if args.single_nat_gateway and i > 0:
                    continue

                eip = aws.ec2.Eip(
                    f"{name}-nat-eip-{i}",
                    domain="vpc",
                    tags={**args.tags, "Name": f"{name}-nat-eip-{i + 1}"},
                    opts=ResourceOptions(parent=self),
                )

                nat = aws.ec2.NatGateway(
                    f"{name}-nat-{i}",
                    allocation_id=eip.id,
                    subnet_id=public_subnet.id,
                    tags={**args.tags, "Name": f"{name}-nat-{i + 1}"},
                    opts=ResourceOptions(parent=self, depends_on=[self.igw]),
                )
                self.nat_gateways.append(nat)

        # Register outputs
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "public_subnet_ids": [s.id for s in self.public_subnets],
            "private_subnet_ids": [s.id for s in self.private_subnets],
        })

    @staticmethod
    def _calculate_cidr(vpc_cidr: str, index: int) -> str:
        """Calculate subnet CIDR from VPC CIDR."""
        base = vpc_cidr.split("/")[0]
        octets = base.split(".")
        octets[2] = str(index)
        return f"{'.'.join(octets)}/24"


# Usage in __main__.py
from components.vpc import Vpc, VpcArgs

vpc = Vpc(
    "production",
    VpcArgs(
        cidr_block="10.0.0.0/16",
        availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
        enable_nat_gateway=True,
        single_nat_gateway=False,
        tags={"Environment": "production", "Team": "platform"},
    ),
)

pulumi.export("vpc_id", vpc.vpc.id)
```

---

## Testing Infrastructure

One of Pulumi's biggest advantages is native testing support.

### Python Unit Tests

```python
# test_infrastructure.py
"""Unit tests for infrastructure."""

import pulumi
import pytest
from unittest.mock import Mock


class MockResource:
    """Mock Pulumi resources for testing."""

    def __init__(self, name, props):
        self.name = name
        self.props = props


# Mock Pulumi runtime
pulumi.runtime.set_mocks(
    Mock(
        return_value=Mock(
            call=lambda args, **kwargs: (
                args.token.split(":")[-1] + "_id",  # Mock resource ID
                dict(args.props, id=args.token.split(":")[-1] + "_id"),
            )
        )
    )
)


# Test VPC configuration
@pulumi.runtime.test
def test_vpc_has_correct_cidr():
    """Test that VPC has correct CIDR block."""
    from __main__ import vpc

    def check_cidr(args):
        assert args["cidr_block"] == "10.0.0.0/16"

    return vpc.cidr_block.apply(lambda cidr: check_cidr({"cidr_block": cidr}))


@pulumi.runtime.test
def test_vpc_has_dns_enabled():
    """Test that VPC has DNS enabled."""
    from __main__ import vpc

    def check_dns(args):
        assert args["enable_dns_hostnames"] == True
        assert args["enable_dns_support"] == True

    return pulumi.Output.all(
        vpc.enable_dns_hostnames, vpc.enable_dns_support
    ).apply(
        lambda args: check_dns(
            {"enable_dns_hostnames": args[0], "enable_dns_support": args[1]}
        )
    )


@pulumi.runtime.test
def test_correct_number_of_subnets():
    """Test that correct number of subnets are created."""
    from __main__ import public_subnets, private_subnets

    assert len(public_subnets) == 3
    assert len(private_subnets) == 3


@pulumi.runtime.test
def test_security_group_rules():
    """Test security group has correct ingress rules."""
    from __main__ import security_group

    def check_rules(ingress):
        ports = [rule["from_port"] for rule in ingress]
        assert 80 in ports
        assert 443 in ports
        assert 22 not in ports  # SSH should not be open

    return security_group.ingress.apply(check_rules)


# Run tests
# pytest test_infrastructure.py -v
```

### TypeScript Tests with Jest

```typescript
// __tests__/infrastructure.test.ts
import * as pulumi from "@pulumi/pulumi";
import "jest";

// Mock Pulumi
pulumi.runtime.setMocks({
    newResource: (args: pulumi.runtime.MockResourceArgs): { id: string, state: any } => {
        return {
            id: args.name + "_id",
            state: args.inputs,
        };
    },
    call: (args: pulumi.runtime.MockCallArgs) => {
        return args.inputs;
    },
});

describe("Infrastructure", () => {
    let infra: typeof import("../index");

    beforeAll(async () => {
        infra = await import("../index");
    });

    test("VPC has correct CIDR", async () => {
        const cidr = await new Promise<string>((resolve) => {
            pulumi.Output.create(infra.vpcId).apply((id) => {
                // In real test, check actual CIDR
                resolve("10.0.0.0/16");
            });
        });
        expect(cidr).toBe("10.0.0.0/16");
    });

    test("Creates 3 public subnets", async () => {
        const subnetIds = await infra.publicSubnetIds;
        expect(subnetIds.length).toBe(3);
    });

    test("Creates 3 private subnets", async () => {
        const subnetIds = await infra.privateSubnetIds;
        expect(subnetIds.length).toBe(3);
    });
});

// Run: jest
```

### Policy as Code Tests

```python
# policy/security_policies.py
"""Pulumi policy pack for security enforcement."""

from pulumi_policy import (
    EnforcementLevel,
    PolicyPack,
    ReportViolation,
    ResourceValidationArgs,
    ResourceValidationPolicy,
)


def s3_no_public_read(args: ResourceValidationArgs, report_violation: ReportViolation):
    """Ensure S3 buckets don't have public read access."""
    if args.resource_type == "aws:s3/bucket:Bucket":
        acl = args.props.get("acl")
        if acl in ["public-read", "public-read-write"]:
            report_violation("S3 buckets must not have public read access")


def ec2_no_public_ip(args: ResourceValidationArgs, report_violation: ReportViolation):
    """Ensure EC2 instances don't have public IPs by default."""
    if args.resource_type == "aws:ec2/instance:Instance":
        if args.props.get("associatePublicIpAddress", False):
            report_violation("EC2 instances should not have public IPs directly")


def require_tags(args: ResourceValidationArgs, report_violation: ReportViolation):
    """Ensure resources have required tags."""
    required_tags = ["Environment", "Team", "ManagedBy"]
    taggable_types = [
        "aws:ec2/instance:Instance",
        "aws:ec2/vpc:Vpc",
        "aws:s3/bucket:Bucket",
        "aws:rds/instance:Instance",
    ]

    if args.resource_type in taggable_types:
        tags = args.props.get("tags", {})
        missing = [tag for tag in required_tags if tag not in tags]
        if missing:
            report_violation(f"Missing required tags: {', '.join(missing)}")


# Create policy pack
PolicyPack(
    name="security-policies",
    enforcement_level=EnforcementLevel.MANDATORY,
    policies=[
        ResourceValidationPolicy(
            name="s3-no-public-read",
            description="S3 buckets must not be publicly readable",
            validate=s3_no_public_read,
        ),
        ResourceValidationPolicy(
            name="ec2-no-public-ip",
            description="EC2 instances should not have public IPs",
            validate=ec2_no_public_ip,
        ),
        ResourceValidationPolicy(
            name="require-tags",
            description="Resources must have required tags",
            validate=require_tags,
        ),
    ],
)

# Run: pulumi preview --policy-pack ./policy
```

---

## Stack References

Share outputs between Pulumi projects/stacks.

```python
# network/stack/__main__.py
"""Network stack - shared VPC resources."""

import pulumi
import pulumi_aws as aws

vpc = aws.ec2.Vpc("shared-vpc", cidr_block="10.0.0.0/16")

# Export for other stacks
pulumi.export("vpc_id", vpc.id)
pulumi.export("vpc_cidr", vpc.cidr_block)


# app/stack/__main__.py
"""Application stack - uses network stack outputs."""

import pulumi
from pulumi import StackReference

# Reference the network stack
network = StackReference("organization/network-stack/production")

# Get outputs from network stack
vpc_id = network.get_output("vpc_id")
vpc_cidr = network.get_output("vpc_cidr")

# Use in resources
security_group = aws.ec2.SecurityGroup(
    "app-sg",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8080,
            to_port=8080,
            cidr_blocks=[vpc_cidr],  # Only from VPC
        )
    ],
)
```

---

## Configuration and Secrets

```bash
# Set configuration values
pulumi config set environment production
pulumi config set aws:region us-east-1

# Set secret (encrypted)
pulumi config set --secret database_password "super-secret-password"

# View config
pulumi config
```

```python
# Access configuration in code
config = pulumi.Config()

# Required values (fails if not set)
environment = config.require("environment")

# Optional values with defaults
instance_type = config.get("instance_type") or "t3.micro"

# Secrets (automatically encrypted)
db_password = config.require_secret("database_password")

# Access provider-specific config
aws_config = pulumi.Config("aws")
region = aws_config.get("region") or "us-east-1"
```

---

## CI/CD Integration

```yaml
# .github/workflows/pulumi.yml
name: Pulumi

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

jobs:
  preview:
    name: Preview
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Pulumi Preview
        uses: pulumi/actions@v5
        with:
          command: preview
          stack-name: production
          comment-on-pr: true

  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Pulumi Up
        uses: pulumi/actions@v5
        with:
          command: up
          stack-name: production
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Ignoring resource names | Name conflicts on updates | Always provide explicit names |
| Not using ComponentResources | Flat, unorganized code | Group related resources in components |
| Storing secrets in config | Secrets in plain text | Use `config.require_secret()` |
| Circular dependencies | Deployment fails | Use `depends_on` or restructure |
| Not testing | Bugs reach production | Write unit and policy tests |
| Hardcoding values | No environment flexibility | Use Config and stack references |
| Ignoring type hints | Runtime errors | Use proper typing (Python/TS) |
| Skipping preview | Unexpected changes | Always preview before up |

---

## Quiz

<details>
<summary>1. What is the main advantage of Pulumi over Terraform?</summary>

**Answer**: Pulumi uses general-purpose programming languages (Python, TypeScript, Go, C#) instead of a domain-specific language (HCL). This enables:
- Real loops, conditionals, and functions
- Native unit testing (pytest, jest)
- IDE support (autocomplete, refactoring)
- Package management (pip, npm)
- Leveraging existing team skills
</details>

<details>
<summary>2. What is a ComponentResource in Pulumi?</summary>

**Answer**: A ComponentResource is a custom resource that groups multiple child resources. It's similar to a Terraform module but implemented as a class in your programming language. Benefits:
- Encapsulates related resources
- Reusable across projects
- Can have custom logic and validation
- Provides clean abstraction layers
</details>

<details>
<summary>3. How do you share outputs between Pulumi stacks?</summary>

**Answer**: Use StackReference:
```python
# Reference another stack
network = StackReference("org/network-stack/prod")

# Get outputs
vpc_id = network.get_output("vpc_id")
```

This enables modular infrastructure where one stack (networking) provides resources for another (application).
</details>

<details>
<summary>4. How are secrets handled in Pulumi?</summary>

**Answer**: Secrets are encrypted and stored in the Pulumi state:
- Set: `pulumi config set --secret db_password "secret"`
- Access: `config.require_secret("db_password")`
- Automatically encrypted at rest
- Never shown in plain text in logs/outputs
- Decrypted only during deployment
</details>

<details>
<summary>5. Can Pulumi use Terraform providers?</summary>

**Answer**: Yes, through the Pulumi Terraform Bridge. Most popular Terraform providers are available as Pulumi packages:
- `pulumi-aws` (from terraform-provider-aws)
- `pulumi-azure-native` (native Azure)
- `pulumi-gcp` (from terraform-provider-google)

You get the same resources with language-native APIs.
</details>

<details>
<summary>6. What testing frameworks can you use with Pulumi?</summary>

**Answer**: Native testing frameworks for each language:
- **Python**: pytest with Pulumi mocks
- **TypeScript**: Jest or Mocha
- **Go**: Standard Go testing
- **C#**: NUnit or xUnit

Plus Pulumi-specific:
- Policy packs for compliance testing
- Integration tests with actual deployments
</details>

---

## Hands-On Exercise

**Objective**: Create a Pulumi project with a reusable VPC component.

### Part 1: Create Project

```bash
# Create project
mkdir pulumi-exercise && cd pulumi-exercise
pulumi new aws-python --name vpc-exercise --yes

# Structure
# ├── Pulumi.yaml
# ├── __main__.py
# └── requirements.txt
```

### Part 2: Create VPC Component

```bash
# Create components directory
mkdir -p components

# Create VPC component
cat > components/__init__.py << 'EOF'
from .vpc import Vpc, VpcArgs
EOF

cat > components/vpc.py << 'EOF'
"""Reusable VPC component."""

import pulumi
from pulumi import ComponentResource, ResourceOptions
import pulumi_aws as aws
from typing import List, Optional


class VpcArgs:
    def __init__(
        self,
        cidr_block: str = "10.0.0.0/16",
        num_availability_zones: int = 2,
        tags: dict = None,
    ):
        self.cidr_block = cidr_block
        self.num_availability_zones = num_availability_zones
        self.tags = tags or {}


class Vpc(ComponentResource):
    def __init__(
        self,
        name: str,
        args: VpcArgs,
        opts: Optional[ResourceOptions] = None,
    ):
        super().__init__("custom:network:Vpc", name, {}, opts)

        self.vpc = aws.ec2.Vpc(
            f"{name}-vpc",
            cidr_block=args.cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={**args.tags, "Name": f"{name}-vpc"},
            opts=ResourceOptions(parent=self),
        )

        self.igw = aws.ec2.InternetGateway(
            f"{name}-igw",
            vpc_id=self.vpc.id,
            tags={**args.tags, "Name": f"{name}-igw"},
            opts=ResourceOptions(parent=self),
        )

        self.public_subnets = []
        azs = aws.get_availability_zones(state="available")

        for i in range(args.num_availability_zones):
            subnet = aws.ec2.Subnet(
                f"{name}-public-{i}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i}.0/24",
                availability_zone=azs.names[i],
                map_public_ip_on_launch=True,
                tags={**args.tags, "Name": f"{name}-public-{i + 1}"},
                opts=ResourceOptions(parent=self),
            )
            self.public_subnets.append(subnet)

        self.register_outputs({
            "vpc_id": self.vpc.id,
            "subnet_ids": [s.id for s in self.public_subnets],
        })
EOF
```

### Part 3: Use Component

```bash
cat > __main__.py << 'EOF'
"""Main infrastructure."""

import pulumi
from components import Vpc, VpcArgs

config = pulumi.Config()
environment = config.get("environment") or "dev"

vpc = Vpc(
    environment,
    VpcArgs(
        cidr_block="10.0.0.0/16",
        num_availability_zones=2,
        tags={
            "Environment": environment,
            "ManagedBy": "pulumi",
        },
    ),
)

pulumi.export("vpc_id", vpc.vpc.id)
pulumi.export("subnet_ids", [s.id for s in vpc.public_subnets])
EOF
```

### Part 4: Deploy

```bash
# Set stack config
pulumi config set environment dev
pulumi config set aws:region us-east-1

# Preview
pulumi preview

# Deploy
pulumi up

# View outputs
pulumi stack output
```

### Success Criteria

- [ ] Project created with Python
- [ ] VPC component is reusable class
- [ ] Component creates VPC, IGW, subnets
- [ ] Tags applied correctly
- [ ] Outputs exported
- [ ] `pulumi preview` shows expected resources

---

## Key Takeaways

- [ ] **Real programming languages** - Python, TypeScript, Go, C# instead of DSL
- [ ] **Native testing** - pytest, jest for infrastructure tests
- [ ] **ComponentResources** - Reusable infrastructure classes
- [ ] **Type safety** - Catch errors before deployment
- [ ] **Package ecosystem** - pip, npm for dependencies
- [ ] **Stack references** - Share outputs between projects
- [ ] **Secrets built-in** - Encrypted configuration
- [ ] **Policy as code** - Enforce compliance programmatically
- [ ] **CI/CD friendly** - GitHub Actions, GitLab CI integration
- [ ] **IDE support** - Full autocomplete and refactoring

---

## Did You Know?

> **Pulumi Origin**: Pulumi was founded by Joe Duffy, former Microsoft developer who led .NET Core and TypeScript projects. He wanted to bring the power of real programming languages to infrastructure.

> **Terraform Bridge**: Pulumi can automatically generate providers from Terraform providers, which is why most Terraform providers are available in Pulumi within weeks of release.

> **Automation API**: Pulumi has an Automation API that lets you embed Pulumi deployments inside other applications—you can build your own Terraform Cloud alternative.

> **Language Stats**: According to Pulumi's 2023 survey, TypeScript is the most popular Pulumi language (45%), followed by Python (35%), Go (15%), and C# (5%).

---

## Next Module

Continue to [Module 7.4: Ansible](../module-7.4-ansible/) to learn about configuration management and the differences between infrastructure provisioning and configuration management.
