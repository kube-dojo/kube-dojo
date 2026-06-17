---
revision_pending: false
title: "Module 7.5: AWS CloudFormation"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.5-cloudformation
sidebar:
  order: 6
---
## Learning Outcomes

- **Design** CloudFormation stack boundaries that separate shared foundations, application resources, and account-wide baselines without creating fragile export dependencies.
- **Implement** parameterized YAML templates that use `Ref`, `Fn::GetAtt`, `Fn::Sub`, `Fn::ImportValue`, and `Fn::If` for late binding instead of hard-coded resource identifiers.
- **Diagnose** failed updates, replacements, rollbacks, and drift reports by reading stack events, change sets, and resource drift details.
- **Evaluate** CloudFormation tradeoffs against Terraform and AWS CDK by comparing capabilities, state ownership, ecosystem shape, language ergonomics, and cloud scope without ranking the tools.
- **Configure** StackSets, deletion policies, update replacement policies, stack policies, registry extensions, and the AWS SAM transform for common AWS-native platform patterns.

## Why This Module Matters

CloudFormation is AWS infrastructure as code at the service boundary where templates, accounts, Regions, IAM, resource providers, and rollback behavior all meet. Terraform, Pulumi, CDK, and higher-level platform tools may be more pleasant for some teams, but CloudFormation remains the contract that many AWS-native workflows rely on directly or indirectly. If you operate AWS estates long enough, you will eventually read a CloudFormation event stream, review a change set, debug drift, protect a stateful resource with a deletion policy, or explain why a stack export cannot be removed yet.

> **Complexity:** `[COMPLEX]` | **Time to Complete:** 90 minutes | **Prerequisites:** Complete [Module 6.1: IaC Fundamentals](/platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) first, then use this module as the AWS-specific deep dive rather than a repeat of the discipline-level IaC theory.

The durable idea is not that CloudFormation is the right tool for every infrastructure job. The durable idea is that CloudFormation gives AWS a declarative deployment contract: a template describes intended resources, a stack records the managed deployment, and the CloudFormation service orchestrates the underlying AWS API calls. That service-owned control plane changes the operational tradeoffs. You do not design a remote state backend, but you do design stack boundaries, IAM capabilities, update policies, exports, drift workflows, and recovery procedures.

Hypothetical scenario: a platform team owns a shared networking stack that exports subnet IDs, security group IDs, and route table outputs for application stacks. During an incident, an engineer changes a security group rule directly in the AWS console to restore traffic, then forgets to record the emergency change. The next stack update becomes risky because the template, the actual resource, and the team's intent no longer match. CloudFormation does not magically know the human reason for the change, but drift detection gives the team a structured way to find the mismatch before another update turns an emergency workaround into a hidden dependency.

Think of CloudFormation as a building inspector with a stamped plan set. The template is the plan, the stack is the inspector's case file, and the deployed resources are the building. If a contractor changes a door after the inspection, the building may still work, but the case file is now stale. Change sets, stack policies, deletion policies, and drift detection are not decorations around the template. They are the controls that keep the plan, the case file, and the building aligned while real people make changes under pressure.

## CloudFormation's Mental Model

A CloudFormation template is a declarative document written in JSON or YAML. The most important section is `Resources`, because every template must describe at least one resource that CloudFormation can create, update, or delete. Other sections shape how the resource graph is built: `Parameters` accept runtime values, `Mappings` hold lookup tables, `Conditions` decide whether selected resources or properties apply, `Outputs` expose results, and `Transform` runs macros such as AWS SAM before the final template is processed.

A stack is the deployment unit. When you create a stack, CloudFormation reads the template, resolves parameters, evaluates conditions, builds a dependency graph, and calls the relevant AWS service APIs in an order that respects references and explicit dependencies. When you update a stack, CloudFormation compares the submitted template and parameter values with the current stack model, then decides which resources can be updated in place, which require replacement, and which must be added or removed. That comparison is why a stack is more than a folder full of YAML files.

CloudFormation state is managed by AWS as part of the stack. This is different from tools that require a separate state file or state backend that your team must secure, lock, back up, and migrate. The tradeoff is control. You get an AWS-managed state model, automatic event history, and service-level rollback behavior, but you do not get direct state surgery as a normal workflow. When a resource is wrong, the CloudFormation-native moves are import, update, drift remediation, replacement, retention, or stack refactoring rather than editing a local state database.

CloudFormation also has a distinct security model because it is an AWS service acting on your behalf. The caller needs permission to create or update the stack, and CloudFormation needs permission to operate the resources in the template, either through the caller's permissions or a service role assigned to the stack. Templates that create IAM resources require explicit capabilities such as `CAPABILITY_IAM` or `CAPABILITY_NAMED_IAM`, which is a useful friction point in review. Treat those capabilities as a reminder that infrastructure code is also privilege code.

## Template Anatomy and Resource Graphs

Template design starts with names. A resource logical ID such as `AuditBucket` is the name CloudFormation uses inside the template and stack events, while the physical ID is the real AWS resource identifier created by the target service. `Ref` usually returns a useful identifier for a resource, but the exact return value depends on the resource type. For an `AWS::S3::Bucket`, `Ref` returns the bucket name, while `Fn::GetAtt` can return attributes such as the bucket ARN.

The resource graph is built from references and dependencies. If a bucket policy references a bucket, CloudFormation understands that the bucket must exist before the policy can be attached. If an internet route depends on a VPC gateway attachment, you can use `DependsOn` to make that ordering explicit when the reference alone is not enough. A good template reads like a graph of relationships, not like a shell script that happens to call AWS APIs in a particular order.

The following compact example uses an S3 bucket because the resource type is easy to reason about, supports drift detection, and avoids unnecessary IAM setup in the first lab. The template deliberately leaves the bucket name unspecified so CloudFormation can generate a compliant physical name in the stack's Region. That choice also avoids a common replacement trap: naming globally scoped resources too early, then discovering later that a supposedly simple name change requires replacement.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Minimal CloudFormation resource graph example

Parameters:
  EnvironmentName:
    Type: String
    Default: sandbox
    AllowedPattern: '^[a-z][a-z0-9-]{1,20}$'

Resources:
  AuditBucket:
    Type: AWS::S3::Bucket
    Properties:
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: ManagedBy
          Value: CloudFormation

Outputs:
  BucketName:
    Description: Generated bucket name
    Value: !Ref AuditBucket
  BucketArn:
    Description: Bucket ARN
    Value: !GetAtt AuditBucket.Arn
```

The template is small, but it already shows the CloudFormation pattern. Parameters represent deploy-time choices, resource properties represent desired configuration, and outputs expose values that operators or later stacks may need. The important habit is to read the template as a contract: if the template says public access is blocked and encryption uses S3-managed keys, then a later manual console change should be treated as drift until the team intentionally updates either the resource or the template.

## Intrinsic Functions as Late Binding

Intrinsic functions are CloudFormation's way to express values that cannot be fully known when a human writes the file. They are not general-purpose programming functions. They are template-time and deploy-time binding tools used in resource properties, outputs, metadata attributes, update policies, and conditional resource creation. The practical mental model is simple: use intrinsics when a value must come from a parameter, another resource, a pseudo parameter, a condition, an export, or a transform result.

`Ref` is the first intrinsic most people learn because it creates the simplest relationship. When you reference a parameter, `Ref` returns the parameter value. When you reference a resource, it returns the identifier defined by that resource type's reference behavior. That difference matters in reviews. Seeing `!Ref AuditBucket` in an output means "return the bucket name," not "return the whole bucket object" or "return the ARN." For the ARN, you need `Fn::GetAtt`.

`Fn::GetAtt` returns a named attribute from a resource. The function is resource-specific, so you must check the Template Reference page for the resource type before assuming an attribute exists. This is where AWS accuracy matters most in CloudFormation authoring. A made-up attribute name does not become valid because it looks consistent with another service. If the `AWS::S3::Bucket` reference lists `Arn`, then `!GetAtt AuditBucket.Arn` is valid; if a resource reference does not list the attribute you want, the template must be redesigned.

`Fn::Sub` substitutes variables in a string. It can replace parameter names, logical IDs, resource attributes, pseudo parameters such as `AWS::Region`, and explicit variables supplied in a map. Use it for ARNs, names, descriptions, and user data where concatenation would otherwise bury intent. The common review question is whether the substitution creates a valid value for the target service. CloudFormation can substitute text, but S3, IAM, Lambda, and EC2 still enforce their own naming and property constraints.

```yaml
Outputs:
  RegionalBucketArn:
    Value: !Sub 'arn:${AWS::Partition}:s3:::${AuditBucket}'
  BucketDescription:
    Value: !Sub
      - 'Stack ${StackName} manages bucket ${BucketName}'
      - StackName: !Ref AWS::StackName
        BucketName: !Ref AuditBucket
```

`Fn::ImportValue` is for cross-stack references. One stack exports an output name, and another stack imports that value in the same account and Region. This is powerful because it prevents consumers from hard-coding resource IDs, but it also creates a lifecycle constraint: once another stack imports an export, CloudFormation blocks deleting the exporting stack or changing the exported value until the imports are removed. That protection is useful for shared foundations, but painful when teams export too much.

`Fn::If` chooses between two values based on a named condition. It is useful for environment differences, optional properties, and outputs that should exist only in certain deployments. Conditions are not a substitute for thoughtful stack boundaries. If a template becomes a dense maze of environment-specific branches, the team may need separate stacks or nested templates instead. Use conditions for controlled variation, not as a way to hide unrelated architectures in one file.

```yaml
Parameters:
  RetentionDays:
    Type: Number
    Default: 30
    AllowedValues:
      - 7
      - 30
      - 90

Conditions:
  LongRetention: !Equals [!Ref RetentionDays, 90]

Resources:
  AuditBucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: !If [LongRetention, Enabled, Suspended]
```

The key teaching point is that intrinsic functions preserve declarative intent while avoiding hard-coded values. They let the graph stay explicit even when the concrete values are resolved late. The failure mode is over-cleverness. If every property is nested inside three functions, reviewers stop seeing the infrastructure shape. Prefer the smallest intrinsic expression that keeps the relationship correct, and move broad design choices into stack boundaries, parameters, or separate templates.

## Change Sets, Rollback, and Update Risk

Change sets are CloudFormation's preview mechanism. You submit a proposed template or parameter change, and CloudFormation creates a change set that lists the resources it expects to add, modify, remove, import, or replace. Nothing changes until you execute the change set. That makes change sets the review surface for production updates, especially when the template touches stateful resources, named resources, IAM roles, routing, security groups, or anything with external consumers.

A change set is not a success guarantee. AWS documentation is explicit that a change set can show the intended impact without proving that the update will complete. The update can still fail because of service quotas, unsupported update behavior, missing permissions, naming conflicts, or runtime constraints in the target service. This distinction is important for platform teams. A change set answers "what does CloudFormation plan to attempt," not "will every downstream service accept it."

Replacement is the word to slow down on. Some property updates can happen without interruption, some cause interruption, and some require CloudFormation to create a new physical resource. Replacement can be safe for disposable resources and dangerous for data-bearing or externally referenced resources. For example, an S3 bucket with an explicitly specified `BucketName` cannot be replaced with the same name, and the S3 resource reference documents that a bucket name update requires replacement. That is a design signal to avoid hard-coded names unless the name is part of the external contract.

Rollback behavior is one reason teams choose CloudFormation for AWS-native workflows. If stack creation or update fails, CloudFormation attempts to roll resources back toward the previous stable state. Rollback does not eliminate operational risk; a failed rollback can still require careful repair, and retained resources or external dependencies can complicate cleanup. The right lesson is to combine change sets with small stack boundaries, explicit policies, backups for stateful resources, and rehearsed recovery steps rather than trusting rollback as a magic undo button.

```bash
aws cloudformation create-change-set \
  --stack-name cfn-lab \
  --change-set-name initial-create \
  --change-set-type CREATE \
  --template-body file://cfn-lab.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=sandbox

aws cloudformation describe-change-set \
  --stack-name cfn-lab \
  --change-set-name initial-create \
  --query 'Changes[].ResourceChange.{Action:Action,LogicalId:LogicalResourceId,Replacement:Replacement}'

aws cloudformation execute-change-set \
  --stack-name cfn-lab \
  --change-set-name initial-create
```

Reviewing a change set should feel like reviewing a database migration. You are looking for actions, replacements, permissions, and blast radius. A clean-looking `Modify` may still hide a service interruption, while a planned `Replace` may be acceptable if the resource is ephemeral and downstream references are managed. The strongest teams review both the CloudFormation view and the target resource reference, because the resource reference tells you which property updates require replacement and which attributes are safe to consume.

## Drift Detection and Reconciliation

Drift is the gap between CloudFormation's expected configuration and the actual configuration returned by the underlying service. It happens for understandable reasons: emergency console changes, service-side defaults, operators testing a fix, automation outside the stack, or partial migrations from manual infrastructure. Drift detection lets CloudFormation compare explicitly set template properties and parameter values with actual resource properties for resource types that support the feature. Unsupported resources are marked `NOT_CHECKED`, so a clean drift result is not a universal proof of correctness.

CloudFormation reports stack drift statuses such as `IN_SYNC`, `DRIFTED`, and `NOT_CHECKED`, and resource drift statuses such as `MODIFIED`, `DELETED`, `IN_SYNC`, and `NOT_CHECKED`. Property differences can show values added, removed, or changed. The exact result depends on what the resource provider can read back from the target service. If a property was never set in the template and merely relied on a service default, CloudFormation may not include that default in drift comparison. This is why explicit properties are easier to govern than implicit defaults.

Drift detection is diagnostic, not automatic remediation. After detecting drift, the team still decides whether to update the resource back to the template, update the template to match the intentional real-world change, import or refactor resources, or accept a known difference temporarily. That decision should be recorded in code review or an incident note. Otherwise, drift detection becomes another alert stream that people acknowledge without changing the system of record.

Nested stacks add another wrinkle. Running drift detection on a parent stack does not automatically detect drift inside nested stacks; you initiate drift detection directly on the nested stack when you need that detail. Cross-stack relationships also require care because a drifted shared resource can affect many consumers even when the consumer stacks themselves look unchanged. For platform teams, drift reviews belong in the same operating rhythm as change-set reviews, not only in annual audits.

```bash
DETECTION_ID=$(aws cloudformation detect-stack-drift \
  --stack-name cfn-lab \
  --query StackDriftDetectionId \
  --output text)

aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id "$DETECTION_ID"

aws cloudformation describe-stack-resource-drifts \
  --stack-name cfn-lab \
  --stack-resource-drift-status-filters MODIFIED DELETED
```

The healthiest drift workflow is humble. It assumes that emergency human changes may be valid, but also assumes that undocumented differences will eventually surprise a deployment. That balance avoids two bad extremes: blindly overwriting manual fixes because "the template wins," or letting manual fixes become invisible production configuration. CloudFormation gives you the comparison. Engineering judgment still decides the reconciliation path.

## Nested Stacks and Cross-Stack References

Nested stacks split a large template into reusable pieces by creating `AWS::CloudFormation::Stack` resources inside a parent stack. The parent stack passes parameters to child templates and can read child outputs with `Fn::GetAtt` on the nested stack resource. This pattern is useful when lifecycle is shared. If the network, security, and application components should be deployed and deleted as one unit, nesting keeps that relationship explicit under a root stack.

Cross-stack references solve a different problem. They let independent stacks share values through exported outputs and `Fn::ImportValue`. This fits shared foundations such as VPC IDs, subnet IDs, or security group IDs that application stacks consume without owning. The independence is the point: the networking stack can have a slower lifecycle than the application stack. The cost is coupling through exports. Export names must be unique within an account and Region, imports are same-account and same-Region, and imported exports block changes to the exported value until all imports are removed.

```yaml
# shared-network.yaml
Outputs:
  SharedBucketName:
    Description: Shared audit bucket name
    Value: !Ref AuditBucket
    Export:
      Name: !Sub '${AWS::StackName}-AuditBucketName'
```

```yaml
# consumer.yaml
Parameters:
  NetworkStackName:
    Type: String

Resources:
  AppConfig:
    Type: AWS::SSM::Parameter
    Properties:
      Name: !Sub '/apps/${AWS::StackName}/audit-bucket'
      Type: String
      Value:
        Fn::ImportValue: !Sub '${NetworkStackName}-AuditBucketName'
```

Choosing between nested stacks and exports is a lifecycle decision, not a syntax preference. Use nested stacks when the child components are part of one deployable product and should rise or fall with the root. Use exports when a producer stack owns shared infrastructure and consumer stacks should be deployed independently. Avoid exporting every convenient value. Every export is an API, and every import is a consumer contract that must be versioned, deprecated, and removed deliberately.

There is a third option in modern CloudFormation documentation, `Fn::GetStackOutput`, for some cross-account or cross-Region output lookup cases, but this module focuses on the durable export and import model because it enforces referential integrity. Strong references are easier to reason about in a curriculum setting. In production, if you choose weaker lookup patterns, document what happens when the referenced stack or output disappears. Convenience that removes lifecycle protection should be treated as an architectural tradeoff.

## StackSets for Multi-Account and Multi-Region Governance

StackSets extend the stack model across accounts and Regions. You define a template once in an administrator context, then create stack instances in selected target accounts and Regions. This is especially useful for organization-wide baselines: enabling detective controls, creating common IAM roles, deploying notification topics, or placing guardrail resources into every account. The point is consistency at fleet scope, not just reuse within one account.

StackSets have permission models. With service-managed permissions, CloudFormation integrates with AWS Organizations and creates the needed roles on your behalf for accounts in the organization. With self-managed permissions, you manage the administration and execution roles yourself. Service-managed StackSets can target an organization or organizational units, but AWS documents important constraints, including that templates with nested stacks or macros and transforms are not supported in that service-managed mode. That constraint matters if you planned to reuse a SAM or macro-heavy template as an account baseline.

```bash
aws cloudformation create-stack-set \
  --stack-set-name account-baseline \
  --template-url https://s3.region-code.amazonaws.com/amzn-s3-demo-bucket/baseline.yaml \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=true

aws cloudformation create-stack-instances \
  --stack-set-name account-baseline \
  --deployment-targets OrganizationalUnitIds=ou-abcd-example \
  --regions us-east-1 us-west-2 \
  --operation-preferences FailureToleranceCount=0,MaxConcurrentCount=1
```

The operational question for StackSets is blast radius. A template that is harmless in one sandbox account can be disruptive when applied to many accounts across several Regions. StackSet operation preferences, failure tolerance, concurrency, delegated administration, and automatic deployment settings are governance controls. Use them intentionally. A conservative first deployment to a small OU is usually more informative than a broad launch that proves only that mistakes can scale.

StackSets are also a reminder that CloudFormation is not only an application deployment tool. In platform engineering, many CloudFormation stacks are account-shaping infrastructure: logging, monitoring, IAM, backup, configuration recording, service control prerequisites, and shared networking. Those stacks need ownership, review, and rollback thinking just like application stacks. The difference is that their consumers may be every team in the organization.

## Deletion Policies, Update Replacement Policies, and Stack Policies

Deletion behavior is where infrastructure code becomes data protection. By default, CloudFormation deletes a resource when the stack is deleted or when the resource is removed from the template, with documented exceptions for certain RDS resources. `DeletionPolicy` lets you choose a different behavior for selected resources. `Retain` leaves the resource behind but removes it from CloudFormation's scope, `Snapshot` creates a snapshot for supported resource types, `RetainExceptOnCreate` keeps resources for most operations but deletes the newly created resource if the initial stack operation rolls back, and `Delete` is the default behavior.

`UpdateReplacePolicy` handles a different event: replacement during an update. If a property change requires a new physical resource, CloudFormation can delete, retain, or snapshot the old physical resource depending on the policy and resource support. The distinction is easy to miss. `DeletionPolicy` protects resources when they leave the stack model, while `UpdateReplacePolicy` protects the old resource when a replacement is created. Production databases, persistent volumes, and critical buckets deserve both policies to be reviewed explicitly.

```yaml
Parameters:
  DataVolumeAvailabilityZone:
    Type: AWS::EC2::AvailabilityZone::Name

Resources:
  ImportantDataVolume:
    Type: AWS::EC2::Volume
    DeletionPolicy: Snapshot
    UpdateReplacePolicy: Snapshot
    Properties:
      AvailabilityZone: !Ref DataVolumeAvailabilityZone
      Size: 20
      VolumeType: gp3
```

Stack policies are another safety layer. A stack policy is a JSON document that controls which update actions can be performed on protected resources in a stack. AWS documentation is clear that stack policies apply during stack updates and are not a replacement for IAM. Use IAM to control who can call CloudFormation and underlying service APIs; use stack policies as a fail-safe against accidental updates to specific stack resources once someone already has update permission.

The practical design pattern is layered protection. Use IAM and deployment roles to constrain who can update stacks, change sets to preview the update, stack policies to prevent accidental modification of critical logical IDs, and deletion or replacement policies to preserve data when a resource leaves CloudFormation control. No one layer is enough. Together, they turn a template from a resource list into an operational contract.

## Registry, Resource Providers, Macros, and AWS SAM

The CloudFormation registry is the extension hub for CloudFormation. It contains AWS resource types, public and private third-party resource types, modules, and Hooks. A resource provider defines how CloudFormation creates, reads, updates, deletes, and lists a resource type. This is why CloudFormation can manage many AWS services through `AWS::...` resource types and can also support activated third-party or private types. When you use extensions, you inherit their handler behavior, schema quality, permissions, and pricing model.

The registry changes how you should think about CloudFormation coverage. A missing resource type is not always a permanent limitation, but an extension is not the same as a built-in AWS resource type. Public and private extensions may have separate activation, versioning, operational, and billing considerations. For production, review who publishes the type, how updates are delivered, how failures appear in stack events, and what permissions the provider needs. A resource provider is code that CloudFormation runs on your behalf, not just a new YAML keyword.

Macros perform custom processing on templates before CloudFormation creates the final processed template. The `Transform` section can invoke macros, including AWS-hosted transforms such as `AWS::Include` and AWS SAM. Macros are powerful because they can generate or rewrite template fragments, but they also make review harder if reviewers only inspect the source template. For macro-heavy stacks, teach reviewers to look at the processed template or synthesized artifact as well as the original authoring format.

AWS SAM is the serverless-specific transform. A template declares `Transform: AWS::Serverless-2016-10-31`, uses SAM resource types such as `AWS::Serverless::Function`, and CloudFormation expands that syntax into standard CloudFormation resources such as Lambda functions and IAM roles when creating a change set. SAM is not separate from CloudFormation in the deployment path; it is a transform that produces CloudFormation-managed resources.

```yaml
Transform: AWS::Serverless-2016-10-31
Resources:
  HandlerFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: index.handler
      Runtime: nodejs20.x
      CodeUri: s3://amzn-s3-demo-bucket/source.zip
```

The same mental model applies to AWS CDK. CDK lets you define infrastructure in general-purpose languages and uses CloudFormation for provisioning on AWS. That does not make CDK better or worse than direct templates. It changes the authoring layer. CDK gives constructs, language features, and synthesis; CloudFormation remains the deployment substrate. When debugging a CDK deployment, the CloudFormation stack, change set, and events are still part of the operational truth.

## Landscape Snapshot - as of 2026-06

Verify this table against current vendor documentation before relying on it for policy, quotas, pricing, or procurement. The durable concepts above are more stable than service quotas and pricing rules, and AWS can change limits, resource provider behavior, or billing details without changing the basic stack model.

| Area | Snapshot | Why it matters |
|---|---|---|
| Authoring formats | CloudFormation templates are JSON or YAML documents with required `Resources` and optional sections such as `Parameters`, `Mappings`, `Conditions`, `Outputs`, and `Transform`. | Reviewers should understand section roles before debating tool preference. |
| Template body size | The AWS CLI `create-change-set` reference lists a direct `--template-body` maximum of 51,200 bytes and an S3 `--template-url` object maximum of 1 MB. | Large templates should use S3-hosted templates, nested stacks, modules, or generation workflows. |
| Template shape quotas | AWS documents quotas including 500 resources, 200 parameters, and 200 outputs per template. | Quotas shape stack boundaries and discourage monolithic templates. |
| Dynamic references | AWS documents 60 dynamic references per stack template. | Secrets and external parameters need deliberate grouping, not unbounded copy-paste. |
| Stack count | AWS documents a default quota of 2,000 stacks per account and Region. | Very fine-grained stack designs need account and Region quota awareness. |
| StackSets scale | AWS documents quotas such as 1,000 stack sets in an administrator account and 100,000 stack instances per stack set. | Fleet governance should consider quotas and operation preferences early. |
| CloudFormation charges | AWS pricing says there is no additional charge for CloudFormation with `AWS::*`, `Alexa::*`, and `Custom::*` resource providers, while other provider and Hook handler operations can incur charges. | "No additional charge" does not mean deployed resources are free, and extensions may have their own billing surface. |
| CDK relationship | AWS CDK is an open-source framework for defining infrastructure in supported programming languages and provisioning it through CloudFormation. | CDK changes authoring ergonomics, while CloudFormation remains part of deployment and debugging. |

## CloudFormation, Terraform, and CDK as Tradeoffs

CloudFormation, Terraform, and CDK overlap, but they optimize for different operating models. CloudFormation is AWS-native, has service-owned stack state, integrates directly with IAM capabilities, StackSets, exports, registry extensions, drift detection, and rollback events. Terraform uses providers to interact with many APIs and requires state to map configuration to real-world resources. CDK uses programming languages and constructs, then synthesizes CloudFormation templates for AWS deployments. Those are capability differences, not a ranking.

CloudFormation's strengths are most visible when an organization is deeply AWS-centered and wants the deployment control plane to be AWS itself. StackSets, service-managed permission integration with AWS Organizations, server-side stack state, and native event history fit account factories and compliance-oriented baselines. The cost is authoring ergonomics. Raw YAML and JSON can become verbose, and complex reusable abstractions often require nested stacks, modules, transforms, CDK, or disciplined template generation.

Terraform's strengths are most visible when an organization wants one workflow across multiple clouds, SaaS APIs, and infrastructure platforms. Its provider model and HCL language create a portable operating pattern, and its plan workflow is familiar to many teams. The cost is state ownership and provider lifecycle management. Terraform state is necessary for Terraform to map configuration to real-world objects, so teams must treat backend design, locking, secrets exposure, and state migration as first-class operational concerns.

CDK's strengths are most visible when AWS teams want higher-level constructs, general-purpose language features, package reuse, and testable abstractions while still deploying through CloudFormation. The cost is a second representation to understand. Reviewers may need to inspect both the source code and the synthesized template, and operators still need CloudFormation literacy when a deployment fails. CDK can reduce template repetition, but it does not remove the need to understand stacks, change sets, IAM capabilities, and rollbacks.

The decision question is not "which tool is best." Ask which control plane should own state, which clouds or APIs are in scope, which authoring style the team can maintain, how changes are reviewed, how drift is detected, and how account-wide governance is deployed. A mature platform may use more than one tool: CloudFormation StackSets for AWS account baselines, Terraform or OpenTofu for multi-provider infrastructure, CDK for AWS application platforms, and Ansible for post-provisioning configuration. The boundary is the architecture.

## Operating CloudFormation in a Platform Team

CloudFormation becomes easier to operate when each stack has an owner, a lifecycle, and a review path. A shared networking stack, an application stack, an account-baseline StackSet, and a one-off experiment stack should not all receive the same process. The shared networking stack may need dependency tracking for imports, the application stack may need fast rollback and observable deployments, the baseline StackSet may need staged OU rollout, and the experiment stack may need an aggressive cleanup date. The template syntax is the same, but the operating model is not.

A useful platform convention is to treat stack outputs as public API only when they are deliberately exported. An ordinary output can help humans inspect a stack or let a parent nested stack consume a child output. An exported output invites other stacks to depend on it, so it should have a stable name, a clear owner, and a removal plan. If you would not publish a field in a service API without versioning it, do not casually publish the same kind of contract through a CloudFormation export. Infrastructure dependencies are still dependencies.

Another convention is to separate review questions by failure mode. Template syntax review asks whether the document is valid CloudFormation. Resource review asks whether each resource type and property are valid for the target AWS service. Change-set review asks what CloudFormation intends to do to existing resources. Operational review asks how the team will detect failure, roll back, repair drift, and clean up retained resources. Mixing those questions into one vague "looks good" review hides the fact that each layer catches different mistakes.

Stack events should be part of the team's normal debugging vocabulary. A failed deployment usually leaves clues in chronological event order: which logical ID failed, which service returned the error, whether rollback started, whether rollback completed, and whether any resources are stuck in cleanup. Teach engineers to read events by logical ID and physical ID together. The logical ID tells you which line of the template to inspect, while the physical ID tells you which actual AWS resource to investigate in the target service.

For production stacks, retained resources need an inventory path. `Retain` and `Snapshot` are valuable safety controls, but they intentionally leave resources or snapshots outside the normal stack deletion flow. That means the team needs tags, ownership metadata, backup retention rules, and a cleanup workflow for anything retained. Otherwise the organization trades accidental deletion risk for quiet cost growth and unclear ownership. Data protection policies should describe both how resources are preserved and how preserved resources are eventually retired.

Finally, CloudFormation work should be tested at the smallest scope that still exercises the risky behavior. You do not need a full production VPC to learn how change sets show replacement, how `Fn::If` changes a property, or how drift detection reports a tag mismatch. Small sandbox stacks are excellent teaching tools because they make the event stream readable. Once the behavior is understood, the same review habit can be applied to larger stacks where the blast radius is real.

## Review Checklist for Production Stacks

Before a production stack update, first check whether the proposed change alters stack boundaries, exports, IAM capabilities, or resource names. Those changes are architecture changes disguised as template edits. A new export may create future deletion constraints, a renamed resource may force replacement, and a new IAM capability may allow the stack to create or alter privileges. These are the places where reviewers should slow down even when the diff is small.

Next, read the change set for action and replacement rather than only for resource count. A one-resource change can be more dangerous than a ten-resource change if the one resource is a database, bucket, route, or role with external consumers. When the change set says replacement, open the resource reference for the changed property and confirm the behavior. If the resource stores data or has a stable external identity, require an explicit retention, snapshot, migration, or downtime plan before execution.

Then check the drift posture. If the stack has not had drift detection recently and the stack is known to be touched during incidents, run drift detection before applying a sensitive update. A template update against a drifted resource may overwrite an emergency fix or fail because the real resource no longer matches assumptions. Drift does not always mean the template is wrong, but unexamined drift means the team is updating from incomplete information.

Finally, check cleanup and observability. The update plan should say who watches the stack events, which CloudWatch alarms or service dashboards matter after deployment, what retained resources or snapshots may remain, and how the team will know that consumers are healthy. CloudFormation gives a strong deployment record, but application correctness often depends on signals outside CloudFormation. Production review should connect the stack operation to the service behavior it supports.

## Lab Walkthrough

This lab deploys a simple S3-backed stack with parameters, previews it with a change set, updates it through another change set, creates intentional drift, detects the drift, and cleans up. It assumes the AWS CLI is installed, configured, and authorized for CloudFormation and S3 in a sandbox account. The template avoids named buckets, IAM resources, and paid compute resources, but you are still responsible for any AWS resources you create in your account.

- [ ] Create a file named `cfn-lab.yaml` with this template.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: CloudFormation lab for parameters, change sets, and drift detection

Parameters:
  EnvironmentName:
    Type: String
    Default: sandbox
    AllowedPattern: '^[a-z][a-z0-9-]{1,20}$'
  RetentionDays:
    Type: Number
    Default: 30
    AllowedValues:
      - 7
      - 30
      - 90

Conditions:
  LongRetention: !Equals [!Ref RetentionDays, 90]

Resources:
  LabBucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: !If [LongRetention, Enabled, Suspended]
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: ManagedBy
          Value: CloudFormation

Outputs:
  BucketName:
    Description: Generated bucket name
    Value: !Ref LabBucket
  BucketArn:
    Description: Bucket ARN
    Value: !GetAtt LabBucket.Arn
```

- [ ] Validate the template before creating a stack.

```bash
aws cloudformation validate-template \
  --template-body file://cfn-lab.yaml
```

- [ ] Create and review an initial change set, then execute it only after the planned resource list matches the template.

```bash
aws cloudformation create-change-set \
  --stack-name cfn-lab \
  --change-set-name initial-create \
  --change-set-type CREATE \
  --template-body file://cfn-lab.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=sandbox \
               ParameterKey=RetentionDays,ParameterValue=30

aws cloudformation wait change-set-create-complete \
  --stack-name cfn-lab \
  --change-set-name initial-create

aws cloudformation describe-change-set \
  --stack-name cfn-lab \
  --change-set-name initial-create \
  --query 'Changes[].ResourceChange.{Action:Action,LogicalId:LogicalResourceId,Replacement:Replacement}' \
  --output table

aws cloudformation execute-change-set \
  --stack-name cfn-lab \
  --change-set-name initial-create

aws cloudformation wait stack-create-complete \
  --stack-name cfn-lab
```

- [ ] Create an update change set that changes the retention parameter to the long-retention path and inspect whether the bucket can be updated in place.

```bash
aws cloudformation create-change-set \
  --stack-name cfn-lab \
  --change-set-name retention-update \
  --change-set-type UPDATE \
  --template-body file://cfn-lab.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=sandbox \
               ParameterKey=RetentionDays,ParameterValue=90

aws cloudformation wait change-set-create-complete \
  --stack-name cfn-lab \
  --change-set-name retention-update

aws cloudformation describe-change-set \
  --stack-name cfn-lab \
  --change-set-name retention-update \
  --query 'Changes[].ResourceChange.{Action:Action,LogicalId:LogicalResourceId,Replacement:Replacement}' \
  --output table

aws cloudformation execute-change-set \
  --stack-name cfn-lab \
  --change-set-name retention-update

aws cloudformation wait stack-update-complete \
  --stack-name cfn-lab
```

- [ ] Create intentional drift by changing one tag outside CloudFormation, then run stack drift detection and inspect the modified resource.

```bash
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name cfn-lab \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
  --output text)

aws s3api put-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --tagging 'TagSet=[{Key=Environment,Value=sandbox},{Key=ManagedBy,Value=Console}]'

DETECTION_ID=$(aws cloudformation detect-stack-drift \
  --stack-name cfn-lab \
  --query StackDriftDetectionId \
  --output text)

aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id "$DETECTION_ID"

aws cloudformation describe-stack-resource-drifts \
  --stack-name cfn-lab \
  --stack-resource-drift-status-filters MODIFIED \
  --output table
```

- [ ] Restore the tag, verify the stack can be deleted cleanly, and remove the lab stack.

```bash
aws s3api put-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --tagging 'TagSet=[{Key=Environment,Value=sandbox},{Key=ManagedBy,Value=CloudFormation}]'

aws cloudformation delete-stack \
  --stack-name cfn-lab

aws cloudformation wait stack-delete-complete \
  --stack-name cfn-lab
```

The lab is intentionally small so the operational signals are easy to see. The important observations are the change set action, the replacement column, the stack event stream during create and update, the generated bucket name returned by `Ref`, the ARN returned by `Fn::GetAtt`, and the drift result after the out-of-band tag edit. If those signals make sense on a one-resource stack, the same reading habits scale to VPCs, IAM roles, Lambda applications, and organization-wide StackSets.

## Did You Know?

- **CloudFormation templates can use transforms:** The `Transform` section lets CloudFormation process macros, including AWS SAM, before the final template is executed.
- **Drift detection is explicit:** CloudFormation does not continuously scan every stack; you initiate drift detection and then inspect the operation result.
- **S3 bucket deletion has a service rule:** CloudFormation can delete an S3 bucket only when the bucket is empty, so retained or populated buckets need cleanup planning.
- **CDK still needs CloudFormation literacy:** CDK deployments provision through CloudFormation, so stack events, change sets, and rollback states remain operationally relevant.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---|---|---|
| Treating change sets as guaranteed success | A change set previews intended actions but does not prove quotas, permissions, names, or service constraints will allow the update. | Review the change set, then still monitor stack events and prepare rollback or repair steps. |
| Exporting every convenient output | Each import creates a lifecycle dependency that blocks changing or deleting the exported value while consumers exist. | Export only stable platform contracts and version or deprecate them deliberately. |
| Naming resources too early | Some named resources require replacement when their name changes, and globally scoped names can collide across accounts or Regions. | Let CloudFormation generate names unless the name is part of an external contract. |
| Ignoring drift after emergency fixes | Manual changes can make later updates overwrite or conflict with the real production state. | Run drift detection after incidents and decide whether the template or resource should change. |
| Relying only on `DeletionPolicy` | `DeletionPolicy` does not protect the old physical resource during replacement caused by an update. | Pair `DeletionPolicy` with `UpdateReplacePolicy` for stateful or critical resources. |
| Using stack policies as access control | Stack policies apply to update behavior and are not a substitute for IAM permissions. | Use IAM for authorization and stack policies as an extra fail-safe for protected logical IDs. |
| Making one monolithic template | Large templates become hard to review, approach quotas, and tie unrelated lifecycles together. | Split by lifecycle with nested stacks, cross-stack references, modules, or separate stacks. |
| Forgetting transform output in review | SAM, macros, and CDK can generate CloudFormation that differs from what reviewers saw in source form. | Review the processed or synthesized template when generated resources affect security or data. |

## Quiz

<details>
<summary>1. Why is a CloudFormation stack more than a template file?</summary>

A template is the desired resource declaration, while a stack is the managed deployment record that CloudFormation uses to create, update, delete, roll back, and report events for the resources. The stack stores the relationship between logical IDs, physical resources, parameters, outputs, and update history inside the AWS control plane. That distinction matters because operational tasks such as drift detection, change sets, imports, exports, and rollbacks all operate against a stack, not just against a local YAML file.
</details>

<details>
<summary>2. When should you prefer a cross-stack export over a nested stack output?</summary>

Prefer a cross-stack export when the producer and consumer need independent lifecycles, such as a shared networking stack used by several application stacks. The export becomes a stable contract in the same account and Region, and consumers import it without owning the producer stack. Prefer nested stack outputs when the child templates belong to one root deployment and should be created, updated, and deleted together. The key decision is lifecycle coupling, not which syntax feels shorter.
</details>

<details>
<summary>3. What does a replacement warning in a change set tell you to investigate?</summary>

A replacement warning means CloudFormation expects to create a new physical resource for a logical ID and move references to the replacement. You should check whether the old resource contains data, has external consumers, uses a fixed name, or needs a snapshot or retention policy. Replacement may be harmless for disposable resources, but it can be severe for databases, buckets, network identities, endpoints, and IAM roles that other systems reference outside CloudFormation.
</details>

<details>
<summary>4. Why can a stack be reported as in sync even when you still have governance risk?</summary>

Drift detection compares supported resources and explicitly set properties that CloudFormation can read back from the underlying service. Unsupported resources can be marked `NOT_CHECKED`, default values may not be compared when they were never specified, and some properties cannot be mapped back reliably. An `IN_SYNC` result is useful evidence, but it is not a complete compliance audit. Teams still need policy checks, resource inventory, logging, and review of generated templates.
</details>

<details>
<summary>5. How do `DeletionPolicy` and `UpdateReplacePolicy` differ?</summary>

`DeletionPolicy` controls what CloudFormation does when a resource is removed from the stack model or when the stack is deleted. `UpdateReplacePolicy` controls what happens to the old physical resource when an update requires replacement. For critical stateful resources, reviewing only `DeletionPolicy` leaves a gap because an update can replace a resource without being a stack deletion. The safer pattern is to evaluate both policies together.
</details>

<details>
<summary>6. What is the main tradeoff between raw CloudFormation and AWS CDK?</summary>

Raw CloudFormation exposes the deployment model directly in YAML or JSON, which keeps the stack contract close to the reviewed artifact but can become verbose. CDK offers general-purpose languages, constructs, package reuse, and synthesis, but the synthesized CloudFormation template still matters for deployment and debugging. The tradeoff is authoring ergonomics versus representation layers. CDK can improve abstraction, but it does not remove the need to understand CloudFormation stack behavior.
</details>

<details>
<summary>7. Why are StackSets useful and risky at the same time?</summary>

StackSets are useful because they let one template deploy consistent stacks across multiple accounts and Regions, which fits security baselines, logging, and organization-wide platform controls. They are risky because the same consistency can scale mistakes quickly. A bad IAM policy, wrong Region target, or disruptive resource update can affect many accounts. Operation preferences, delegated administration, staged OU rollout, and small initial targets help manage that blast radius.
</details>

<details>
<summary>8. Why is `Fn::Sub` often clearer than string joins for ARNs and names?</summary>

`Fn::Sub` keeps the intended string shape visible while letting CloudFormation replace parameters, pseudo parameters, logical IDs, and attributes at runtime. That makes ARNs, names, descriptions, and user data easier to review than a long chain of joins. The reviewer can see both the literal structure and the dynamic pieces. The remaining responsibility is to confirm that the substituted string is valid for the target AWS service.
</details>

## Hands-On

Use the lab walkthrough above as the executable exercise, and treat this checklist as the operational record you would attach to a pull request. The goal is not merely to create an S3 bucket. The goal is to practice the CloudFormation deployment loop: validate the template, preview the change, execute only after review, observe stack events, create controlled drift, detect the mismatch, restore the intended configuration, and clean up without leaving unmanaged resources behind.

- [ ] The `cfn-lab.yaml` template validates with `aws cloudformation validate-template`.
- [ ] The initial `CREATE` change set shows the expected `LabBucket` resource before execution.
- [ ] The update change set for `RetentionDays=90` is reviewed for action and replacement behavior.
- [ ] The generated bucket name is read from stack outputs rather than guessed or hard-coded.
- [ ] Drift detection reports the intentional tag change after the out-of-band `s3api put-bucket-tagging` command.
- [ ] The tag is restored and the stack reaches `DELETE_COMPLETE` during cleanup.

Write down what you observed in the change-set output before execution and in the drift output after the manual tag edit. In a real review, those notes become evidence that the operator understood the planned action and the reconciliation path. If your drift result does not show the expected modification, do not invent an explanation. Check whether the drift detection operation finished, whether the bucket tags were actually changed, whether your AWS CLI profile points at the same account and Region, and whether the resource type support page still lists the resource as drift-detection capable.

## Next Module

Continue to [Module 7.6: Azure Bicep](../module-7.6-bicep/) for the Azure-native IaC comparison point, and keep the discipline-level concepts from [IaC Discipline](../../../disciplines/delivery-automation/iac/) in mind as you compare cloud-specific tooling across provider-specific deployment systems.

## Sources

- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference-ref.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference-getatt.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference-sub.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference-importvalue.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference-conditions.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-drift.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs-associate-stackset-with-org.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-exports.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-nested-stacks.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-attribute-deletionpolicy.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-attribute-updatereplacepolicy.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/registry.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-s3-bucket.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ec2-volume.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-supported-resources.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
- https://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-change-set.html
- https://docs.aws.amazon.com/cli/latest/reference/cloudformation/detect-stack-drift.html
- https://aws.amazon.com/cloudformation/pricing/
- https://docs.aws.amazon.com/cdk/v2/guide/home.html
- https://developer.hashicorp.com/terraform/language/state/purpose
- https://developer.hashicorp.com/terraform/language/providers
