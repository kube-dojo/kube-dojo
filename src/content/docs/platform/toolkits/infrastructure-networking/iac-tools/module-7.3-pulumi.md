---
revision_pending: false
title: "Module 7.3: Pulumi - Infrastructure as Real Code"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.3-pulumi
sidebar:
  order: 4
---

## Complexity: `[MEDIUM]`

## Time to Complete: 45 minutes

---

## Prerequisites

Before starting this module, you should have completed [Module 6.1: IaC Fundamentals](/platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/), which explains desired-state reconciliation, state files, and the difference between provisioning and configuration management. You should also be comfortable reading and writing in at least one general-purpose language such as Python, TypeScript, or Go, because Pulumi expresses infrastructure through those languages rather than through a dedicated configuration syntax.

This module is the tool-specific deep dive for Pulumi. The discipline-level concepts live in the Delivery Automation IaC track; here you will see how those ideas appear when infrastructure is authored as ordinary application code with stacks, providers, and encrypted configuration.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** reusable infrastructure abstractions with Pulumi ComponentResources that encapsulate related cloud resources behind a stable interface.
- **Implement** multi-resource Pulumi programs with stack-specific configuration, encrypted secrets, and preview-before-apply workflows.
- **Configure** Pulumi backends and stack settings for development and production environments, including Pulumi Cloud and self-managed object storage.
- **Diagnose** deployment failures caused by state conflicts, circular dependencies, missing stack references, or misconfigured secret values.
- **Evaluate** Pulumi against Terraform HCL and AWS CDK based on language expressiveness, testing ergonomics, provider coverage, and team skill alignment.

---

## Why This Module Matters

Infrastructure as code tools usually ask you to learn a second language. HashiCorp Configuration Language, CloudFormation templates, and similar DSLs are excellent for declarative configuration, but they become awkward when platform teams need the same expressive power they expect from application code: parameterized loops over account lists, shared libraries, typed data structures, and unit tests that run in CI before anyone touches production.

**Hypothetical scenario:** A platform team maintains Terraform modules for a multi-account landing zone. Each new organizational unit needs conditional networking rules, environment-specific tagging policies, and slightly different subnet layouts. The team keeps pushing HCL to its limits with nested dynamic blocks, string templating, and external data sources that call out to scripts. Onboarding engineers who know Python well still struggle with HCL edge cases, and the team cannot reuse existing internal libraries without wrapping them in fragile glue code.

That friction is exactly the problem Pulumi targets. Pulumi lets you describe cloud resources using TypeScript, Python, Go, C#, Java, or YAML while preserving the same fundamental IaC mental model you learned in the fundamentals module: register desired resources, build a dependency graph, compare against actual infrastructure, and reconcile differences through a plan and apply cycle. The tool changes; the engineering discipline does not.

This module teaches Pulumi as infrastructure expressed in real programming languages, not as a popularity contest between vendors. You will learn where language-native IaC shines, where operational complexity still exists, and how to structure projects so that preview, testing, and stack boundaries keep production changes safe.

---

## 1. The Mental Model: Real Languages on Top of a Resource Graph

Pulumi programs are ordinary projects in a language you already use. A Python Pulumi project has a `requirements.txt`, a TypeScript project has `package.json`, and both import provider packages such as `@pulumi/aws` or `pulumi_aws` that expose cloud resources as typed constructors. When your program runs, it does not immediately call cloud APIs for every line of code. Instead, it registers resource declarations with the Pulumi engine, which builds a directed acyclic graph of dependencies and determines a safe order for create, update, and delete operations.

Think of the Pulumi engine as a planner sitting between your code and the cloud. Your code describes intent: a VPC, three subnets, a security group with specific ingress rules. The engine records each resource's type, name, properties, and parent-child relationships. Outputs from one resource, such as a VPC identifier, flow into inputs for others as deferred values rather than as immediate strings. That deferred evaluation model is why you can use loops, functions, and conditional branches freely without worrying about creating resources in the wrong order during program execution.

The reconcile step mirrors Terraform-style planning. Running `pulumi preview` asks the engine to diff registered intent against the last known state for the active stack. Running `pulumi up` executes the resulting change set. State still matters: Pulumi records resource identifiers, provider versions, and encrypted secret metadata so that later runs can update existing infrastructure instead of attempting duplicate creation. If you skip state management or corrupt a backend, you will experience the same class of painful drift and orphan resources that plague any IaC tool.

```ascii
┌──────────────────────────────────────────────────────────────────────┐
│                     Pulumi Execution Mental Model                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Your program (Python/TS/Go)     Pulumi engine        Cloud API      │
│  ┌──────────────────────┐        ┌──────────────┐     ┌────────────┐   │
│  │ constructors register│───────▶│ resource     │────▶│ providers  │   │
│  │ resources & outputs  │        │ graph + plan │     │ create/    │   │
│  └──────────────────────┘        └──────────────┘     │ update/    │   │
│           │                            │              │ delete     │   │
│           │                            ▼              └────────────┘   │
│           │                     stack state file                       │
│           │                     (Pulumi Cloud or DIY backend)            │
│           ▼                                                            │
│  loops, functions, tests        preview / up / destroy                 │
│  run at program time            reconcile remote reality               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

A common beginner mistake is treating Pulumi like a shell script that calls cloud APIs directly. A senior engineer instead asks where state lives, which stack owns a set of resources, how outputs cross project boundaries, and how CI runs preview on pull requests. Language expressiveness solves authoring pain, but it does not remove platform responsibilities.

Pause and predict: if you copy a Pulumi program that creates ten S3 buckets inside a `for` loop, will the loop run ten times at plan time or at Python import time? The loop runs when the Pulumi program executes during preview or up, and each iteration registers another resource node in the graph. That distinction matters when you refactor code that accidentally creates resources at module import time outside of the Pulumi entrypoint.

Cross-reference the fundamentals module when reasoning about idempotency. Pulumi's apply operation is idempotent at the infrastructure layer: running the same program twice against unchanged configuration should produce no further changes. Your application code inside the Pulumi project must still avoid side effects unrelated to resource registration, such as sending emails or mutating external databases during preview, unless you guard those actions carefully.

Outputs deserve special attention because they are the contract surface for other stacks and for human operators. When you call `pulumi.export`, you publish a named value that appears in CLI output, CI logs, and StackReference consumers. Export only what downstream teams need, mark sensitive exports carefully, and treat renames as breaking API changes. Many production incidents begin when an application stack still references `vpcId` but the network stack renamed the export to `vpc_id` without a migration window.

Resource options modify behavior at registration time. `ResourceOptions(parent=...)` establishes hierarchy for components. `depends_on` breaks implicit dependency ordering when the engine fails to infer relationships, such as when one resource must exist before another but no output connects them. `protect=True` prevents accidental deletion during destroy operations, which is valuable for stateful data stores you never want removed by a mistyped command. `ignore_changes` tells the engine to stop managing specific property drift, a sharp tool that can hide real configuration problems if used casually to silence noisy diffs.

Understanding replacement semantics separates junior usage from senior platform engineering. When a property change forces replacement, Pulumi plans to delete the old resource and create a new one. For stateful resources such as databases or DNS names tied to immutable identifiers, replacement can cause outages. Preview output distinguishes update-in-place from replace operations; learn to read those symbols before approving CI applies. When provider upgrades suddenly introduce replacements across a large stack, pin provider versions immediately and schedule a controlled migration rather than approving a Friday-evening apply.

Finally, remember that Pulumi programs are still software engineering artifacts. They belong in version control, require code review, benefit from linting and formatting, and accumulate technical debt like any other codebase. The advantage of general-purpose languages is that your existing engineering practices transfer directly: pull request templates, CODEOWNERS files, static analysis, and package pinning are not optional extras—they are how you keep infrastructure code maintainable at organizational scale.

Multi-language teams sometimes standardize on one Pulumi language per domain to reduce cognitive load. Networking platforms might standardize on Python for data generation while application squads use TypeScript for services already in Node.js. That diversity is acceptable when shared components publish language-specific wrappers or when stacks remain owned by single teams. Problems appear when every repository chooses a different language without platform guidance, fragmenting reusable libraries and CI templates.

Drift detection still matters even with strong languages. Operators who modify security groups manually in a cloud console create differences between actual infrastructure and registered state. Schedule periodic `pulumi refresh` operations in lower environments to detect drift early, and teach incident responders that console fixes without IaC updates guarantee a future destructive plan. The discipline module covers drift conceptually; Pulumi implements detection through refresh and diff operations tied to stack state.

---

## 2. Landscape Snapshot — as of 2026-06

Vendor-specific details change frequently. Treat the table below as a orientation snapshot and verify current values in official documentation before relying on them in production decisions.

| Topic | Snapshot | Verify at |
|---|---|---|
| Open-source engine | Pulumi CLI and core SDKs are Apache-2.0 licensed | [github.com/pulumi/pulumi](https://github.com/pulumi/pulumi) |
| Current CLI line | 3.x series; check latest patch before pinning CI | [Pulumi releases](https://github.com/pulumi/pulumi/releases) |
| Managed service | Pulumi Cloud offers hosted state, secrets, and collaboration features beyond the open-source CLI | [Pulumi Cloud docs](https://www.pulumi.com/docs/pulumi-cloud/) |
| Self-managed state | DIY backends include local filesystem, Amazon S3, Azure Blob, Google Cloud Storage | [State and backends](https://www.pulumi.com/docs/iac/concepts/state/) |
| Supported languages | TypeScript/JavaScript, Python, Go, C#, Java, YAML | [Languages](https://www.pulumi.com/docs/iac/languages-sdks/) |
| Provider ecosystem | Many packages are bridged from Terraform providers via the Pulumi Terraform Bridge | [Terraform bridge](https://www.pulumi.com/docs/iac/adopting-pulumi/migrating-to-pulumi/from-terraform/) |

The durable takeaway is structural: Pulumi separates an open-source engine from an optional commercial control plane, supports multiple language runtimes against shared provider packages, and stores stack state in a backend you choose. Patch versions, pricing tiers, and preview-feature names should always be confirmed in vendor docs rather than memorized from curriculum snapshots.

---

## 3. Capability Comparison: Pulumi, Terraform HCL, and AWS CDK

Platform teams rarely choose IaC tools in isolation. They compare expressiveness, testing story, provider breadth, CI integration, and how well the tool matches existing skills. None of these tools eliminates operational work: you still design stack boundaries, protect secrets, review plans, and handle drift.

Pulumi and Terraform both follow a declarative desired-state model with persistent state. Terraform expresses configuration in HCL, which many teams prefer because it keeps infrastructure diffs visually compact and because a large module registry already exists. Pulumi expresses the same resources through general-purpose languages, which helps when infrastructure logic resembles application logic: parsing structured data, sharing libraries, generating many similar resources from a catalog, or writing unit tests with familiar frameworks.

AWS Cloud Development Kit is another language-native option, but it optimizes for generating CloudFormation templates within AWS rather than for a cloud-neutral resource model. CDK can be an excellent fit for AWS-centric teams already committed to CloudFormation deployment mechanics. Pulumi targets multi-cloud and Kubernetes scenarios with one programming model across providers, at the cost of learning Pulumi-specific project layout, stack naming, and backend configuration.

```ascii
┌─────────────────────────────────────────────────────────────────┐
│           Capability Lens (not a ranking)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Pulumi                         Terraform HCL                   │
│  ──────                         ─────────────                   │
│  Languages: Python, TS, Go, C#  Language: HCL + expressions     │
│  Application-style abstractions Configuration-first modules     │
│  Native unit tests with mocks   Plan-focused testing patterns   │
│  ComponentResource classes      Module composition              │
│                                                                 │
│  State: Pulumi Cloud or DIY     State: local or remote backends │
│  Secrets: per-stack encryption  Secrets: marked sensitive in    │
│                                   state; external vault patterns│
│                                                                 │
│  Tradeoff axis                  Tradeoff axis                   │
│  + rich logic in real code      + compact declarative files     │
│  + reuse language ecosystems    + broad module examples         │
│  − learn Pulumi stack concepts  − complex logic can sprawl      │
│  − backend/service choices      − HCL testing ergonomics vary   │
│                                                                 │
│  AWS CDK (AWS-focused peer)                                     │
│  + TypeScript/Python/etc.       + deep AWS construct library    │
│  + generates CloudFormation     − primarily AWS deployment path │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

When evaluating tools for your organization, write down concrete scenarios instead of debating abstract superiority. If your hardest problem is generating hundreds of similar resources from a data file, language-native IaC may reduce friction. If your hardest problem is curating vetted modules for dozens of teams, a mature module registry and strict HCL review pipelines may matter more. If you are all-in on AWS and standardizing on CloudFormation change sets, CDK deserves a serious look. Many enterprises run more than one tool deliberately: Terraform or Pulumi for cloud foundations, Ansible for instance configuration, Kubernetes controllers for cluster internals.

Language choice within Pulumi is another team decision with durable consequences. Python fits data-heavy generation pipelines and teams already running pytest in CI. TypeScript aligns with frontend and Node.js platform groups and offers strong typing for complex configuration objects. Go suits CLI-adjacent platform tools where static binaries and performance matter. C# and Java appear frequently in enterprises standardized on those runtimes. YAML Pulumi projects trade away some expressiveness for reviewers who prefer minimal Turing-complete surface area. None of these choices changes the underlying resource graph mechanics; they change who can read the code comfortably and which testing toolchain you reuse.

Provider coverage questions should be framed as capability checks, not loyalty tests. Before committing to Pulumi for a multi-cloud program, list each service you need, locate the corresponding Pulumi provider package, confirm who maintains it, and read recent release notes for breaking schema changes. Bridged providers inherit Terraform provider behavior, which accelerates availability but also inherits Terraform provider bugs and upgrade cadences. Native providers such as Azure Native may expose richer API surfaces at the cost of different naming conventions than bridged alternatives.

---

## 4. Projects, Stacks, Providers, and State Backends

A Pulumi **project** is the unit of source control: one repository directory with a `Pulumi.yaml` file describing the project name and runtime. A **stack** is an isolated instance of that project, typically mapped to an environment such as `dev`, `staging`, or `production`. Each stack has its own configuration file (`Pulumi.dev.yaml`, etc.) and its own state record. This separation prevents development experiments from overwriting production resource mappings.

**Providers** are plugins that teach Pulumi how to talk to a cloud or SaaS API. Provider packages are ordinary dependencies in your language ecosystem. When you instantiate `aws.ec2.Vpc`, Pulumi registers a resource of type `aws:ec2/vpc:Vpc` and delegates create/read/update/delete calls to the AWS provider binary during apply. Provider version pinning matters for the same reasons it matters in Terraform: upstream schema changes can force replacement plans if you upgrade carelessly.

**State** stores the mapping between Pulumi logical names and cloud physical identifiers. By default, many tutorials use Pulumi Cloud because `pulumi login` without arguments stores state in the managed service. Production platform teams often choose self-managed backends when policy requires object storage in a specific account, air-gapped environments, or custom retention controls. Supported DIY backends include Amazon S3, Azure Blob Storage, Google Cloud Storage, and local filesystem for learning only.

Choosing a backend is a governance decision, not a syntax detail. Pulumi Cloud can centralize audit logs, team access, and encrypted secrets handling, which reduces toil for small teams. Self-managed backends keep data entirely within infrastructure you already operate, but you must implement backup, locking discipline, and access reviews yourself. Some organizations use Pulumi Cloud for development stacks and an S3 backend with bucket policies and SSE-KMS for production stacks. Whatever you choose, document which stack lives where before the first `pulumi up` touches a shared account.

Stack configuration merges defaults from `Pulumi.yaml`, stack-specific YAML, and CLI overrides. Non-secret values are stored in plaintext in stack config files and can be checked into version control when appropriate. Secret values should always be set with `--secret` so Pulumi encrypts them at rest in the backend. Leaking secrets into exported outputs or CI logs remains a human failure mode: encryption at rest does not prevent accidental disclosure in a pull request comment if you print sensitive values during debugging.

Naming conventions for stacks deserve explicit platform standards. Some organizations use `{project}.{environment}` while others encode region or tenant identifiers. Consistency matters more than the specific pattern because StackReference strings, CI matrix jobs, and access control rules all key off stack names. Document whether engineers may create ad hoc stacks in shared accounts or must request a platform-managed stack with predefined backend and tags.

State locking and concurrent updates follow backend capabilities. Pulumi Cloud coordinates concurrent operations for stacks it manages. Self-managed object storage backends rely on cloud-specific consistency guarantees and operational playbooks you write yourself. Two CI jobs applying the same stack simultaneously can corrupt state or interleave partial updates if locking is absent. Serialize applies per stack in CI, or use platform features that enforce exclusive deployment leases.

Disaster recovery for state is non-negotiable for production. Back up state files or bucket prefixes on a schedule, test restores in a sandbox account, and monitor for accidental deletion events on state buckets. Losing state does not immediately delete cloud resources, but it severs the mapping that makes future updates safe. Re-import workflows exist but are painful at scale; prevention beats reconstruction.

The relationship between projects and repositories is flexible. Monorepos may host multiple Pulumi projects in subdirectories, each with its own `Pulumi.yaml`. Polyrepo setups may map one project per repository with shared components published as internal packages. Choose boundaries based on blast radius and team ownership rather than on what scaffolds most quickly in a tutorial.

Tagging strategy belongs in platform standards alongside stack naming. Consistent tags enable cost allocation, access reviews, and policy packs that reject untagged resources. Implement tags in components so application teams inherit baseline labels automatically rather than copying JSON blobs. When organizations adopt tag policies enforced by cloud-native services, Pulumi programs should generate compliant tags by default with optional extension points for team-specific metadata.

Access control for state backends must mirror sensitivity of the infrastructure described. A state file for a networking stack contains resource identifiers attackers can leverage for reconnaissance even when secrets are encrypted. Restrict bucket IAM policies, enable object versioning, and audit read access with the same seriousness applied to production database backups.

---

## 5. Installation and Backend Login

Install the Pulumi CLI on the machine or CI worker that will run previews and updates. The CLI orchestrates language runtimes, downloads provider plugins, and communicates with your chosen backend. After installation, authenticate to a backend before creating stacks.

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

# Login to Pulumi Cloud (optional managed backend)
pulumi login

# Or use local state for isolated learning only
pulumi login --local

# Or use an S3-compatible self-managed backend
pulumi login s3://my-pulumi-state-bucket
```

For production, avoid `--local` unless you truly accept single-machine state with no team locking story. Object storage backends should enforce versioning, encryption, and least-privilege IAM roles for CI jobs. Rotate credentials used by automation the same way you rotate application secrets, and scope CI roles to the minimum cloud permissions required for the resources in that stack.

When onboarding a new engineer, have them run `pulumi version` and `pulumi whoami -v` to confirm CLI connectivity and identity. Many "works on my laptop" incidents trace back to one developer logged into a personal Pulumi Cloud account while CI uses a service token tied to an organization stack. Align identities early.

Provider plugin downloads happen during `pulumi up` and sometimes during preview depending on configuration. Air-gapped environments should mirror provider binaries and configure plugin acquisition accordingly. Corporate proxies may intercept TLS traffic and break plugin downloads unless certificate trust is configured on CI workers. Treat plugin cache directories as disposable but reproducible; pin versions in lock files or language-specific dependency manifests alongside provider package versions.

---

## 6. Your First Pulumi Project

Creating a project scaffolds language-specific metadata and an entrypoint file. The entrypoint is where resource registration begins. Keep cloud-specific constants out of hardcoded literals when possible; read them from stack configuration so the same code serves multiple environments.

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

The Python example below demonstrates why teams adopt Pulumi: ordinary loops and list comprehensions generate multiple subnets without HCL dynamic block gymnastics. Notice that resource names use stable logical identifiers (`public-subnet-0`) while display tags incorporate the environment label from configuration.

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

Before applying, set required configuration and inspect the plan. Preview output is your last friendly checkpoint before cloud APIs mutate resources. Read replace versus update markers carefully; an unintended replace on a stateful resource can cause downtime.

```bash
pulumi config set environment dev
pulumi config set aws:region us-east-1

# Preview changes — always do this before up in shared accounts
pulumi preview

# Deploy after review
pulumi up

# Destroy when lab is complete
pulumi destroy
```

TypeScript offers the same patterns with idiomatic `map` calls and typed helper structures. Teams already standardized on Node.js for application development often pick TypeScript Pulumi projects to reuse ESLint rules, package publishing, and hiring pipelines.

Read preview output as a teaching tool, not as noise to scroll past. Each resource line shows whether Pulumi intends to create, update, delete, or replace. Pay attention to dependent resources that cascade from a parent change. If preview proposes deleting production networking unexpectedly, stop and compare against the previous commit rather than assuming the engine is wrong. Often the problem is a renamed logical identifier that Pulumi interprets as destroy-and-recreate.

Environment promotion workflows typically map one stack per environment with identical program code. Differences live in configuration: smaller instance types in development, stricter encryption settings in production, alternate CIDR ranges to avoid overlap when peering test networks. Avoid branching program logic heavily on environment names; too much conditional infrastructure code becomes harder to test than separate configuration values driving the same code paths.

Import and adoption workflows matter when migrating from manually created infrastructure or from another IaC tool. Pulumi supports importing existing cloud resources into state so subsequent plans treat them as managed. Adoption projects should start with read-only refresh and inventory, import a small pilot resource set, validate no-op plans, then expand scope. Rushing bulk imports without understanding dependencies produces state files that look healthy until the first update attempts an unintended replacement.

Destroy operations deserve the same review rigor as creates. Removing a stack from production should follow a checklist: confirm downstream StackReference consumers are updated, snapshot state, run targeted destroy in a maintenance window, and verify cloud consoles show expected cleanup. Protected resources and retained data stores may require explicit unprotect steps or deletion policies encoded in program logic.

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

## 7. Component Resources: Reusable Infrastructure Abstractions

Flat programs become unreadable when every stack repeats VPC, subnet, routing, and logging boilerplate. Pulumi addresses reuse with **ComponentResource**, a class that groups child resources under a parent node in the resource graph. Components behave similarly to Terraform modules but live in your language's module system: import them, version them, publish them to an internal package registry, and unit test them like application libraries.

Design components with explicit argument objects, sensible defaults, and registered outputs. Child resources should declare `ResourceOptions(parent=self)` so Pulumi understands hierarchy and dependency propagation. A well-designed component exposes only the outputs callers need, hiding internal security group identifiers or intermediate role ARNs unless cross-stack references require them.

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

Component boundaries should reflect ownership, not just code aesthetics. If networking and application stacks belong to different teams, expose outputs through stack references rather than importing components across repositories without a contract. Document which inputs are stable and which outputs consumers may depend on, similar to how you would document a Terraform module README.

Publishing components as internal packages scales platform standards. A `@myorg/network-vpc` npm package or internal PyPI module lets application teams consume approved architectures without copying code. Version those packages semver-style and run their unit tests independently from individual stack repositories. When a security baseline changes, bump the component package and notify consumers through changelog entries rather than silently editing a shared file everyone copied.

Custom resource types appear in the graph as `custom:network:Vpc` in the example because ComponentResource requires a type token. Choose type tokens that won't collide with first-party providers and that read clearly in diagnostics. Consistent naming helps policy packs target organizational abstractions separately from raw cloud resources.

---

## 8. Testing Infrastructure Code Before Apply

Language-native IaC enables tests that run in CI without provisioning real cloud resources. Pulumi provides mock runtimes that intercept provider calls and return synthetic values, letting you assert that properties, counts, and relationships look correct before anyone runs `pulumi up`. This does not replace integration tests or policy checks, but it catches many logic errors early.

Unit tests should focus on invariants: CIDR blocks match standards, security groups do not expose administrative ports publicly, required tags exist, and fan-out loops create the expected number of resources. Policy packs add another layer by scanning resource registrations during preview for compliance violations such as public S3 ACLs or missing encryption settings.

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
                args.token.split(":")[-1] + "_id",
                dict(args.props, id=args.token.split(":")[-1] + "_id"),
            )
        )
    )
)


@pulumi.runtime.test
def test_vpc_has_correct_cidr():
    """Test that VPC has correct CIDR block."""
    from __main__ import vpc

    def check_cidr(args):
        assert args["cidr_block"] == "10.0.0.0/16"

    return vpc.cidr_block.apply(lambda cidr: check_cidr({"cidr_block": cidr}))


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
        assert 22 not in ports

    return security_group.ingress.apply(check_rules)


# Run tests
# pytest test_infrastructure.py -v
```

TypeScript teams often use Jest with the same mock hooks. Regardless of language, wire tests into CI so pull requests fail when infrastructure logic regresses. Pair unit tests with `pulumi preview` in automation to catch provider-level changes mocks cannot simulate.

Integration tests that provision ephemeral environments are expensive but valuable for critical paths. Schedule them nightly or weekly rather than on every pull request unless you have dedicated sandbox accounts and automated cleanup. Tag integration-test resources aggressively so orphaned objects are easy to identify when destroy fails partway through.

Testing culture clashes sometimes appear when infrastructure engineers accustomed to plan-only review meet application developers who expect eighty percent unit test coverage. Pulumi makes higher coverage realistic, but agree on thresholds that match risk. Payment processing stacks merit stricter automated testing than disposable demo stacks. Document which components require tests before merge and enforce the rule in CI policy.

Policy packs express organizational guardrails as code executed during preview and update. They complement unit tests: unit tests validate your module logic, while policy packs validate that resulting resource registrations satisfy security baselines.

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


def require_tags(args: ResourceValidationArgs, report_violation: ReportViolation):
    """Ensure resources have required tags."""
    required_tags = ["Environment", "Team", "ManagedBy"]
    taggable_types = [
        "aws:ec2/instance:Instance",
        "aws:ec2/vpc:Vpc",
        "aws:s3/bucket:Bucket",
    ]

    if args.resource_type in taggable_types:
        tags = args.props.get("tags", {})
        missing = [tag for tag in required_tags if tag not in tags]
        if missing:
            report_violation(f"Missing required tags: {', '.join(missing)}")


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
            name="require-tags",
            description="Resources must have required tags",
            validate=require_tags,
        ),
    ],
)

# Run: pulumi preview --policy-pack ./policy
```

---

## 9. Stack References and Cross-Project Composition

Large platforms split infrastructure into layers owned by different teams. Networking publishes VPC and subnet identifiers; application stacks consume them. Pulumi models this with **StackReference**, which reads outputs from another stack in the same organization or backend.

Treat stack references like published APIs. Version or document output names, avoid renaming exports casually, and fail fast when required outputs are missing. A breaking change in the network stack should trigger a planned migration in downstream stacks rather than a surprise failure during application deployment.

```python
# network/stack/__main__.py
"""Network stack - shared VPC resources."""

import pulumi
import pulumi_aws as aws

vpc = aws.ec2.Vpc("shared-vpc", cidr_block="10.0.0.0/16")

pulumi.export("vpc_id", vpc.id)
pulumi.export("vpc_cidr", vpc.cidr_block)


# app/stack/__main__.py
"""Application stack - uses network stack outputs."""

import pulumi
import pulumi_aws as aws
from pulumi import StackReference

network = StackReference("organization/network-stack/production")

vpc_id = network.get_output("vpc_id")
vpc_cidr = network.get_output("vpc_cidr")

security_group = aws.ec2.SecurityGroup(
    "app-sg",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8080,
            to_port=8080,
            cidr_blocks=[vpc_cidr],
        )
    ],
)
```

When diagnosing stack reference failures, verify the fully qualified stack name, backend login context, and that the upstream stack exported the expected keys. Permissions matter: CI jobs need access to read remote stack state, not just update their own stack.

Splitting stacks by lifecycle reduces blast radius. Foundations that change quarterly belong in different stacks from application services deployed daily. The tradeoff is more StackReference wiring and more CI pipelines to maintain. A practical pattern keeps network, shared security, and cluster platforms in long-lived stacks while microservice-specific resources deploy from repositories owned by service teams.

---

## 10. Configuration, Secrets, and Provider Settings

Stack configuration separates environment-specific values from reusable program logic. Plaintext config suits non-sensitive values such as instance sizes or feature flags. Secrets belong in encrypted configuration or external secret stores integrated with your backend.

```bash
pulumi config set environment production
pulumi config set aws:region us-east-1
pulumi config set --secret database_password "super-secret-password"
pulumi config
```

```python
config = pulumi.Config()
environment = config.require("environment")
instance_type = config.get("instance_type") or "t3.micro"
db_password = config.require_secret("database_password")

aws_config = pulumi.Config("aws")
region = aws_config.get("region") or "us-east-1"
```

Never commit secret ciphertext to public repositories unless you intend that exposure and understand backend encryption keys. For teams with strict segregation, integrate HashiCorp Vault or cloud KMS-backed secret providers and keep Pulumi config as references rather than plaintext secret payloads.

Provider configuration namespaces avoid naming collisions between project settings and provider settings. The `aws:region` key belongs to the AWS provider configuration namespace, while bare `environment` belongs to project configuration. Document standard keys in a platform runbook so teams do not invent incompatible names across repositories.

Rotating secrets requires planning. When database passwords rotate, update encrypted stack configuration, run a preview to see dependent resource changes, and apply during a maintenance window if replacements trigger. Automate rotation notifications from your secret manager to the team owning the Pulumi stack so credentials never drift silently between the vault record and the IaC config.

---

## 11. Automation API: Embedding Pulumi in Applications

The Automation API lets you invoke Pulumi operations programmatically from application code without shelling out to the CLI. Platform portals, internal developer platforms, and custom CI systems use it to create stacks on demand, run previews with structured JSON results, and gate updates behind approval workflows you control.

Automation API workflows still require the same discipline as CLI workflows: stack names, backends, and credentials must be configured in the embedding program. The API shines when you need dynamic stack lifecycle management at scale, not when a simple Makefile wrapping `pulumi up` would suffice.

Consult the official Automation API documentation for language-specific entrypoints. The durable concept is that Pulumi separates **authoring** (your IaC program) from **orchestration** (when and how runs execute), and Automation API is the orchestration hook for custom control planes.

Imagine an internal platform where developers click "Create Preview Environment" in a web portal. The portal service uses Automation API to select or create a stack named after the feature branch, inject configuration for image tags, run preview, and store JSON results in a database row the UI renders. After approval, the same service runs update with a lease token so two operators cannot apply concurrently. None of that workflow requires abandoning Pulumi programs; it wraps the same projects CI already uses.

Error handling in embedded orchestrators must surface plan failures distinctly from cloud API failures. A syntax error in Python should fail before any cloud mutation occurs. A quota exceeded error during apply should mark the stack as failed but leave state consistent enough for retry. Build structured error types into portal responses so developers see actionable messages instead of raw provider stack traces.

---

## 12. CI/CD Integration Patterns

Continuous delivery for Pulumi typically runs `pulumi preview` on pull requests and `pulumi up` on merged mainline commits, using a service token or cloud OIDC role with least privilege. Store `PULUMI_ACCESS_TOKEN` or cloud credentials in CI secrets, pin provider and CLI versions, and comment preview results back to the pull request when your platform supports it.

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
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - uses: pulumi/actions@v5
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
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - uses: pulumi/actions@v5
        with:
          command: up
          stack-name: production
```

Add pytest or Jest jobs before preview so broken logic never reaches cloud planning. Separate stacks per environment rather than reusing one stack name for both preview and production unless you fully understand the blast radius.

Pull request workflows benefit from commenting preview summaries when policy allows. Developers review resource change counts before merge, and security teams audit policy pack violations inline. Protect production applies with manual approval gates or deployment windows even when CI is fully automated. Fast automation without human review transfers bugs from laptops to cloud accounts at machine speed.

Use OIDC federation to cloud providers instead of long-lived access keys whenever possible. GitHub Actions, GitLab CI, and other platforms can mint short-lived credentials tied to repository identity. Pair federation with IAM roles scoped to the minimum resources each stack requires. Central security teams often maintain a mapping table from repository paths to cloud roles so individual service teams cannot accidentally request `AdministratorAccess` for convenience.

Observability for IaC pipelines mirrors application observability. Log CLI version, stack name, commit SHA, and plan summary hash for every run. Alert when apply duration spikes or when destroy jobs run unexpectedly. These signals detect compromised tokens, misconfigured webhooks, or engineers bypassing preview gates during incidents.

When things go wrong during apply, resist the urge to manually fix cloud resources without updating Pulumi state. Manual fixes create drift that the next preview will attempt to revert, sometimes destructively. Prefer `pulumi refresh` to reconcile state with reality, then adjust program code, then plan again. Import existing resources when you deliberately adopt unmanaged infrastructure into Pulumi management.

Cost awareness belongs in platform education even when programs are code-first. NAT gateways, load balancers, and idle volumes accumulate charges when labs are forgotten. CI jobs should default to preview-only for feature branches and require explicit labels or approvals before applies that create billable resources. Tag resources with owner and expiration metadata where organizational policy allows so finance and platform teams can chase orphaned experiments.

Documentation for Pulumi stacks should explain purpose, owner, backend location, dependencies on other stacks, and rollback expectations. Future you—or an on-call engineer unfamiliar with the repository—should answer "what happens if this apply fails halfway?" without reading the entire program. Link runbooks from repository README files and keep architecture diagrams updated when component outputs change.

Platform onboarding should include a guided first preview and apply in a sandbox account. Reading documentation without executing preview and update leaves blind spots around stack selection, configuration namespaces, and destroy semantics. A short sandbox lab builds muscle memory that pays off during incident response when minutes matter and panic tempts engineers to skip planning.

Review cadence for provider package upgrades should be quarterly at minimum for production stacks. Provider releases may introduce new required fields, change defaults, or alter replacement behavior. Pin versions in language dependency files, test upgrades in a non-production stack, and keep a rollback pin ready if preview shows unexpected replacements. Treat provider upgrades as production changes even when application code did not change.

---

## Did You Know?

- **Component resources are first-class graph nodes.** A ComponentResource registers a parent entry with child resources nested beneath it, which helps organization in UI views and lets you encapsulate outputs without exposing every internal identifier.
- **The Terraform bridge accelerates provider coverage.** Many Pulumi provider packages wrap existing Terraform providers, which means resource schemas often track Terraform provider releases closely even though authoring happens in Python or TypeScript.
- **Automation API supports custom control planes.** Teams building internal developer portals can invoke preview and update operations programmatically instead of requiring engineers to run CLI commands locally.
- **Stack tags and configuration travel with the stack.** Each stack maintains its own config namespace, so the same program code reads different settings when you switch stacks with `pulumi stack select`.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Ignoring explicit resource names | Name collisions and confusing diffs on updates | Provide stable logical names; treat renames as migrations |
| Skipping ComponentResources for repeated patterns | Copy-pasted VPC and subnet code diverges over time | Encapsulate shared patterns in tested components |
| Storing secrets in plaintext config | Credentials exposed in repository history | Use `pulumi config set --secret` and external vault integrations |
| Creating circular dependencies | Preview or update fails with dependency cycles | Restructure resources, use `depends_on`, or split stacks |
| Relying only on mocks | Provider schema changes slip through CI | Combine unit tests with `pulumi preview` in automation |
| Hardcoding environment values | Same code cannot promote across stacks safely | Read environment-specific values from stack configuration |
| Renaming stack exports casually | Downstream StackReference consumers break | Treat exports as semver-like contracts with migration notes |
| Skipping preview before up | Unexpected replacements reach production | Require preview review gates in CI for shared accounts |

---

## Quiz

<details>
<summary>1. Your team debates replacing a complex Terraform module with Pulumi. What capability tradeoffs should the decision document address instead of counting lines of code?</summary>

The document should compare language expressiveness, testing ergonomics, existing team skills, provider coverage for your clouds, module reuse strategy, backend and secrets requirements, and CI integration costs. Lines of code alone mislead because HCL compactness may still beat Python for simple static stacks, while Python wins when infrastructure logic mirrors application data processing. Neither tool removes the need for stack boundaries, state protection, or plan review.
</details>

<details>
<summary>2. A developer runs a Pulumi program and expects immediate AWS API calls inside a Python loop. What actually happens during the first preview?</summary>

The loop executes during program runtime, but each resource constructor registers intent with the Pulumi engine rather than calling AWS immediately. The engine builds a dependency graph and performs cloud API calls during apply after planning. Side effects outside resource registration, such as writing local files or calling HTTP APIs unconditionally, may still run and should be avoided or guarded.
</details>

<details>
<summary>3. What is a ComponentResource and when should you prefer it over copying resource blocks?</summary>

A ComponentResource is a custom parent resource that groups related child resources in the graph and exposes selected outputs. Prefer components when multiple stacks need the same architecture pattern, when you want unit tests for reusable abstractions, or when you must hide internal identifiers from downstream consumers. Copying blocks is acceptable for one-off experiments but becomes a maintenance risk as standards evolve.
</details>

<details>
<summary>4. How do StackReference outputs differ from Terraform remote state data sources conceptually?</summary>

Both mechanisms read another deployment's exported values instead of duplicating resources. StackReference ties to Pulumi stack identifiers and backend organization, while Terraform remote state reads another Terraform state backend. In both cases, treat exported names as contracts, document breaking changes, and ensure CI credentials can read upstream state before planning downstream stacks.
</details>

<details>
<summary>5. An engineer stores database passwords with `pulumi config set` but without `--secret`. What risk remains even if the repository is private?</summary>

The value is stored in plaintext stack configuration and may appear in diffs, logs, or backups readable by anyone with repository or backend access. `--secret` encrypts the value at rest in the backend, but logs and exported outputs can still leak secrets if the program prints them. Prefer secret configuration, minimize exposure in outputs, and integrate vault systems when policies require it.
</details>

<details>
<summary>6. When would Automation API be a better fit than wrapping the Pulumi CLI in shell scripts?</summary>

Automation API fits when an internal platform must create or destroy stacks dynamically, embed preview results in a web UI, or orchestrate updates with custom approval metadata structured as JSON. Shell wrappers suffice for static repositories with one stack per environment. Automation API still requires backend credentials and stack configuration discipline identical to CLI usage.
</details>

<details>
<summary>7. Preview shows an unexpected replace on a subnet resource after a provider upgrade. What should you investigate first?</summary>

Compare provider changelog and schema diffs for properties that force replacement, verify whether logical resource names changed, and inspect whether state was manually edited. Provider upgrades can alter required attributes or default behaviors. Roll back the provider version pin if the replace is unsafe, then plan a controlled migration if the new schema is required.
</details>

<details>
<summary>8. Your organization requires all production state in self-managed S3 with versioning enabled. Can you still use Pulumi Cloud features?</summary>

Self-managed backends store state in your bucket while Pulumi Cloud features such as team RBAC, audit logs, or web UI may be limited or unused depending on architecture. Many teams use Pulumi Cloud for development and S3 with IAM boundaries for production, or stay entirely DIY. The decision is governance and operational ownership, not syntax. Document which stacks use which backend before onboarding multiple teams.
</details>

---

## Hands-On Exercise

**Objective**: Build a small multi-resource Pulumi program, extract a reusable VPC component, run preview and update, and execute a unit test with mocks.

This lab assumes AWS credentials with permission to create VPC-related resources in a non-production account. Destroy resources when finished to avoid ongoing cost.

### Part 1: Create the Project

- [ ] Create a new directory and scaffold an AWS Python project with Pulumi.
- [ ] Set stack configuration for environment name and AWS region.
- [ ] Confirm `pulumi preview` executes without Python import errors.

```bash
mkdir pulumi-exercise && cd pulumi-exercise
pulumi new aws-python --name vpc-exercise --yes
pulumi config set environment dev
pulumi config set aws:region us-east-1
pulumi preview
```

### Part 2: Implement a VPC Component

- [ ] Create a `components` package with a `Vpc` ComponentResource class.
- [ ] Ensure child resources declare the component parent in `ResourceOptions`.
- [ ] Export VPC and subnet identifiers from the component outputs.

```bash
mkdir -p components

cat > components/__init__.py << 'EOF'
from .vpc import Vpc, VpcArgs
EOF
```

Use the VPC component pattern from Section 7 or the simplified exercise variant below that queries availability zones dynamically.

```bash
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

### Part 3: Wire the Component in `__main__.py`

- [ ] Instantiate the component with environment tags.
- [ ] Export stack outputs for VPC and subnet identifiers.
- [ ] Run `pulumi preview` and verify expected resource counts.

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

pulumi preview
```

### Part 4: Deploy and Capture Outputs

- [ ] Apply the stack after reviewing the preview plan.
- [ ] Record outputs with `pulumi stack output`.
- [ ] Destroy the stack when validation is complete.

```bash
pulumi up
pulumi stack output
pulumi destroy
```

### Part 5: Add a Unit Test

- [ ] Create a pytest file that enables Pulumi mocks.
- [ ] Assert the component creates the configured number of subnets.
- [ ] Run pytest locally or in CI before cloud preview.

```bash
cat > test_vpc.py << 'EOF'
import pulumi
from unittest.mock import Mock

pulumi.runtime.set_mocks(Mock())

@pulumi.runtime.test
def test_subnet_count():
    from components.vpc import Vpc, VpcArgs

    vpc = Vpc("test", VpcArgs(num_availability_zones=2))
    assert len(vpc.public_subnets) == 2
EOF

pytest test_vpc.py -v
```

### Success Criteria

- [ ] Project created with Python and AWS provider dependencies installed.
- [ ] VPC ComponentResource encapsulates VPC, internet gateway, and subnets.
- [ ] `pulumi preview` shows only expected resources without errors.
- [ ] `pulumi up` succeeded and outputs include VPC and subnet identifiers.
- [ ] Unit test with mocks validates subnet fan-out logic.
- [ ] Resources destroyed after the exercise to avoid stray cost.

---

## Next Module

Continue to [Module 7.4: Ansible](../module-7.4-ansible/) to learn configuration management for existing hosts and how provisioning tools like Pulumi complement agentless configuration workflows.

---

## Sources

- [Pulumi documentation home](https://www.pulumi.com/docs/iac/) — Official entry point for concepts, guides, and language SDK references.
- [Pulumi concepts overview](https://www.pulumi.com/docs/iac/concepts/) — Explains projects, stacks, resources, and configuration model shared across languages.
- [Resource documentation](https://www.pulumi.com/docs/iac/concepts/resources/) — Describes how resources register in the engine graph and expose inputs and outputs.
- [Stacks](https://www.pulumi.com/docs/iac/concepts/stacks/) — Documents stack isolation, stack naming, and per-environment configuration files.
- [State and backends](https://www.pulumi.com/docs/iac/concepts/state/) — Covers Pulumi Cloud versus self-managed state storage options and operational implications.
- [Secrets handling](https://www.pulumi.com/docs/iac/concepts/secrets/) — Explains encrypted configuration values and safe handling during previews and updates.
- [Component resources](https://www.pulumi.com/docs/iac/concepts/components/) — Official guidance for building reusable multi-resource abstractions.
- [Testing guide](https://www.pulumi.com/docs/iac/guides/testing/) — Documents unit testing with mocks and integration testing patterns.
- [Automation API](https://www.pulumi.com/docs/iac/packages-and-automation/automation-api/) — Reference for embedding preview and update workflows in applications.
- [Providers](https://www.pulumi.com/docs/iac/concepts/providers/) — Explains provider plugins, version pinning, and plugin acquisition during `pulumi up`.
- [Adopting Terraform providers](https://www.pulumi.com/docs/iac/adopting-pulumi/migrating-to-pulumi/from-terraform/) — Describes the Terraform bridge that supplies many Pulumi provider packages.
- [Download and install](https://www.pulumi.com/docs/iac/download-install/) — Current CLI installation methods and version guidance.
- [Pulumi GitHub repository](https://github.com/pulumi/pulumi) — Apache-2.0 licensed engine source, releases, and issue tracking.
- [Pulumi Cloud](https://www.pulumi.com/docs/pulumi-cloud/) — Managed service features for state, secrets, and team collaboration beyond the open-source CLI.
