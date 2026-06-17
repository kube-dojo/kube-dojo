---
revision_pending: false
title: "Module 7.2: Crossplane"
slug: platform/toolkits/infrastructure-networking/platforms/module-7.2-crossplane
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 75-90 minutes

## Overview

Crossplane is easiest to understand if you stop thinking of it as "Terraform, but in Kubernetes" and start thinking of it as a framework for building control planes. Kubernetes gave platform teams a powerful pattern: users declare the state they want, controllers compare that desired state with the real world, and reconciliation keeps moving the system toward the declared target. Crossplane applies that pattern beyond pods and services. A platform team can define a stable internal API such as `XDatabase`, `XCluster`, or `XQueue`, then connect that API to cloud resources, Kubernetes resources, or other operational objects through controllers and composition functions.

The durable lesson is not that every infrastructure task should move into Crossplane. Some teams should keep Terraform, Pulumi, CloudFormation, Bicep, or service-specific workflows for parts of their estate. The durable lesson is that platform engineering often needs a product API, not merely a provisioning script. When application teams request infrastructure through a clear Kubernetes-style API, the platform team can centralize guardrails, defaults, ownership labels, deletion behavior, and status reporting while still giving developers a self-service workflow. Crossplane is one way to build that API on top of Kubernetes primitives instead of inventing a separate request system.

This module teaches the control-plane spine first: resources, reconciliation, providers, composite resource definitions, compositions, functions, readiness, deletion semantics, and GitOps ownership. The dated facts sit in one snapshot so they can be refreshed without rewriting the lesson. You will use Crossplane as the worked example, but the mental model should also help you evaluate Terraform controllers, Pulumi operators, cloud-native provisioning systems, and internal developer portal templates without turning the comparison into a vendor ranking.

## What You'll Be Able to Do

- Explain Crossplane reconciliation and control-plane ownership without reducing the tool to "cloud resources in YAML."
- Design a narrow platform API with composite resources and compositions that hide provider churn behind a stable contract.
- Compare Crossplane with Terraform, Pulumi, and provider-native stacks using Rosetta tradeoffs instead of ranking claims.
- Validate a composition render and explain user input versus platform-owned defaults before a composition reaches a live cluster.

You will also be able to recognize the most dangerous Crossplane failure modes before they reach production. Those failure modes are rarely caused by the idea of reconciliation itself. They usually come from exposing provider resources too directly, hiding destructive deletion behavior, failing to map useful status back to the user-facing API, treating secrets as an afterthought, or assuming that because a resource is represented in Kubernetes it automatically has good lifecycle ownership.

## Current Landscape

**Landscape snapshot - as of 2026-06-17. Verify these facts against upstream sources before relying on them in production plans, audits, or migration documents.**

| Fact | Snapshot |
|------|----------|
| CNCF maturity | Crossplane is CNCF Graduated. The CNCF project page lists the Graduated maturity level on October 28, 2025. |
| Current Crossplane release | GitHub releases list Crossplane `v2.3.2`, published on 2026-06-09. |
| Current documentation line | The public Crossplane documentation is labeled Crossplane v2.3. |
| Important v2 API posture | Crossplane v2 makes composite resources and managed resources namespaced, removes native patch-and-transform composition in favor of functions, and keeps backward compatibility paths for v1-style resources. |
| Worked lab package | The hands-on exercise pins function-patch-and-transform to `v0.10.7`, published on 2026-06-05, because package tags are volatile and must be explicit. |

The snapshot matters because Crossplane's surface moves in two independent ways: the core project changes, and provider packages change. A platform API should not expose either churn path directly to application teams. If your developer-facing contract says `engine: postgres` and `size: small`, you can update provider fields, package tags, naming conventions, or cloud-specific defaults behind that contract with less coordination cost. If your developer-facing contract exposes every raw provider field, every provider change becomes every application's problem.

Current Crossplane work should be read through the v2 lens unless you are maintaining an older installation. Many examples on the internet still teach a claim-first path because that was the common teaching pattern in earlier material. That does not make the examples useless, but it does mean you should translate them carefully. The durable idea is still "create a small API and compose resources behind it." The current implementation detail is that new v2-style XRs are namespaced, while v1-style claims are a compatibility concept rather than the default starting point for new product APIs.

Another important landscape point is that Crossplane is not only a cloud-provider bridge. Providers can manage external systems, but composition can also render Kubernetes resources and third-party custom resources when the control plane has permission. That matters for internal developer platforms because a useful product API often spans more than one system. A "database product" might create a cloud database, a network policy, a service binding secret, a monitoring rule, and an operational annotation. Crossplane gives you one reconciliation surface for that bundle, but you still have to decide whether Crossplane should own each part.

## Why This Module Matters

Many infrastructure workflows start with good intentions and drift into queues. A developer needs a database for a service. The platform team asks for a ticket with size, region, backup policy, environment, network, ownership, and compliance details. Someone turns that into Terraform or a cloud console change. Someone else reviews it. Credentials are copied into a secret. A month later, staging and production differ because a hotfix happened outside the normal path. Nobody was trying to build a slow system; the workflow simply lacked a product-shaped API.

Crossplane gives platform engineers a way to turn common infrastructure requests into Kubernetes APIs. The platform team still owns the hard decisions: which cloud resource is created, which tags are required, what backup policy is safe, how deletion works, where connection details land, and what status the developer can observe. The application team gets a smaller contract. They ask for a capability, not for every vendor-specific knob underneath it. That is the same product thinking behind a good internal developer platform: expose the choice that matters to the user and hide the details that should be centrally governed.

The analogy is a restaurant menu. A good menu does not expose the vendor catalog for every ingredient, the oven temperature curve, and the supplier contract. It offers stable dishes with useful options: size, spice level, dietary constraints, and sides. The kitchen still has recipes, equipment, and procurement work behind the counter. Crossplane compositions are the recipes, providers are the kitchen tools, managed resources are the ingredients being prepared, and composite resources are the menu items that customers can order without learning the whole kitchen.

## The Durable Control-Plane Model

Crossplane is built on the same reconciliation model that makes Kubernetes useful. A user creates an object that represents desired state. A controller observes that object, compares it with external state, and takes action until the observed world matches the desired declaration. The object also carries status, conditions, references, and events so humans and automation can understand progress. This model is durable because it is about feedback loops and contracts, not about one specific cloud API or package version.

```
DECLARE -> RECONCILE -> OBSERVE -> REPORT -> RECONCILE AGAIN

User or GitOps tool
  applies desired state
        |
        v
Kubernetes API stores resource
        |
        v
Crossplane controller/function/provider
  compares desired state with actual state
        |
        v
External resource or composed Kubernetes object
        |
        v
Status, conditions, events, and connection details
  flow back to the resource contract
```

There are two control-plane questions you should ask before adopting Crossplane for a workflow. First, is the thing you are managing naturally long-lived and declarative? Databases, buckets, queues, clusters, network attachments, DNS zones, and operational policies often fit. One-time imperative tasks can fit only when modeled as operations, jobs, or explicit lifecycle steps. Second, does a platform-owned API reduce cognitive load for users? If every consumer still needs to know the full cloud resource model, Crossplane may have moved the problem into Kubernetes without creating a better product.

The control-plane model also makes drift visible in a different way from a pull-request-only IaC pipeline. Terraform or Pulumi generally compare declared state to real state when a plan runs. Crossplane controllers reconcile continuously while the control plane is running. Continuous reconciliation can be powerful, but it also means ownership must be explicit. If a human changes a cloud resource directly, Crossplane may change it back. If another tool owns the same field, the tools can fight. A good design states which system owns which resource and which fields are intentionally left outside the Crossplane contract.

Reconciliation is not magic; it is a loop with memory, permissions, and failure modes. The API server stores the user's desired state, but the controller needs credentials and logic to act on that desired state. The external API may be slow, eventually consistent, rate limited, or temporarily unavailable. The provider may create an external resource but fail to publish a useful status field on the first pass. A good platform design expects the loop to take time and gives users observable status instead of pretending provisioning is an instant command.

The strongest Crossplane APIs use reconciliation to reduce operational anxiety. A user can ask for a capability and watch the resource move through conditions instead of asking which pipeline is running. A platform engineer can reason about drift through the resource owner instead of searching through scattered scripts. An incident responder can inspect the composite, composed resources, events, and provider logs to understand whether the problem is schema validation, composition rendering, provider credentials, cloud quota, external API failure, or an application expectation mismatch.

The weakest Crossplane APIs use reconciliation to hide decisions that should be explicit. If the composition silently chooses different backup policies per namespace, the platform becomes mysterious. If deletion behavior is encoded only in a low-level provider resource, reviewers may miss it. If provider credentials are broad and status is vague, the API looks simple while the blast radius remains large. Reconciliation should make the operating model clearer, not merely move hidden complexity behind a custom resource.

## Key Concepts

Crossplane has a small set of concepts that show up again and again. The names matter less than the boundaries between them. A provider knows how to talk to an external API or resource family. A managed resource is a Kubernetes representation of a concrete thing such as a bucket, database instance, network rule, or hosted service. A composite resource definition defines a new platform API. A composition defines how an instance of that API turns into one or more composed resources. A composition function performs the rendering or transformation work inside a composition pipeline.

| Building block | Durable job | What to watch |
|----------------|-------------|---------------|
| Provider | Extends Crossplane with resource controllers for an external system or resource family. | Provider packages and API groups change over time, so avoid exposing them as the developer contract. |
| Managed resource | Represents a concrete managed thing with `spec.forProvider`, status, conditions, and lifecycle policy. | Direct managed resources are powerful but often too detailed for application teams. |
| Composite resource definition | Creates the platform-owned API shape, including group, kind, scope, schema, and versions. | The schema is your product contract, so keep it small, stable, and intentionally versioned. |
| Composite resource | A user-created instance of that platform API, such as an `XDatabase` in a team namespace. | The resource should show useful status and avoid leaking provider internals unless they are genuinely needed. |
| Composition | Connects the platform API to one or more rendered resources through a pipeline. | Composition logic should encode defaults and guardrails, not every possible provider option. |
| Function | Runs a composition pipeline step that renders or transforms resources. | Functions are packages with versions, permissions, inputs, and operational behavior that must be reviewed like other controllers. |

In Crossplane v2, namespaced composite resources are the current mainline pattern. That is a significant shift from older claim-centered examples. Claims still matter when you are maintaining v1-style APIs or reading older content, but a new design should start by asking whether a namespaced XR gives the team the isolation and RBAC boundary they need. The practical effect is that the developer can create the platform resource in their namespace, while the platform team controls which API exists and how it is composed.

The first concept to internalize is that an XRD is not just a schema file. It is a platform product boundary. When you add a field, you are creating a promise that someone may automate against. When you remove a field, change an enum, or reinterpret a size class, you may break a deployment workflow even if the underlying provider would accept the new value. Treat XRD versioning with the same seriousness you would apply to an HTTP API used by many teams.

The second concept is that a composition is not just a template. It is a policy-bearing implementation of the product boundary. It chooses resource names, provider references, deletion behavior, tags, labels, status mapping, readiness logic, and sometimes environment-specific differences. Because it is executable platform behavior, composition review should ask both "does this render?" and "does this encode the contract we want?" A syntactically valid composition can still be a bad product if it exposes the wrong knobs or hides the wrong decisions.

The third concept is that provider packages are integrations, not neutral plumbing. They translate Kubernetes desired state into external API calls, and they evolve as the external API and provider project evolve. You should test provider upgrades with real sample resources, inspect release notes, and maintain rollback plans. If a provider changes a field name or behavior, a well-designed composite API gives you a place to adapt. If application teams use direct managed resources everywhere, the upgrade coordination cost spreads across the organization.

## Cross-Tool Rosetta

Tool comparisons are often framed as "which one wins," but platform engineers need a more durable Rosetta table. Each tool family has a different unit of desired state, execution rhythm, and user interface. The point is not to rank them. The point is to see which tradeoff matches the workflow you are building.

| Capability axis | Crossplane | Terraform or OpenTofu | Pulumi | CloudFormation or Bicep |
|-----------------|------------|------------------------|--------|-------------------------|
| Desired-state unit | Kubernetes resources, often custom platform APIs backed by compositions. | Configuration files and state snapshots managed by plans and applies. | Programs that create a resource graph and store state. | Cloud-provider-native templates and stacks. |
| Execution rhythm | Continuous reconciliation by controllers while the control plane runs. | Plan and apply cycles, usually from a human, CI job, or automation runner. | Program execution from CLI, CI, or automation service. | Provider-managed stack operations. |
| Developer-facing contract | Can be a small custom API such as `XDatabase` or direct managed resources. | Usually module inputs, variables, and outputs. | Usually language-level components and package interfaces. | Usually template parameters, modules, and stack outputs. |
| Drift posture | Controller observes and reconciles repeatedly, so ownership conflicts must be managed. | Drift is detected when a plan or drift check runs. | Drift is detected when preview or refresh workflows run. | Drift is detected through provider stack features and checks. |
| Policy location | Kubernetes admission, RBAC, composition logic, package review, and cloud policy can all apply. | Policy as code around plans, module review, state controls, and cloud policy. | Language review, policy as code, package review, and cloud policy. | Template policies, stack policies, service controls, and cloud policy. |
| Best fit | Product APIs for long-lived resources that benefit from Kubernetes-native reconciliation. | Broad infrastructure estates where plan review and explicit state workflows are central. | Teams that want infrastructure abstractions in general-purpose languages. | Teams anchored in a cloud provider's native stack lifecycle. |
| Common trap | Treating raw managed resources as the self-service API and overwhelming users. | Turning every request into a central review queue. | Hiding infrastructure behavior in code that only a few people understand. | Letting provider-specific template details leak into every platform contract. |

The Rosetta table also helps with coexistence. A team might use Terraform for foundational networking, Crossplane for developer self-service databases, Pulumi for a product team's specialized cloud integration, and CloudFormation or Bicep where a provider-native stack is already the cleanest boundary. The important design choice is ownership. If Terraform owns a VPC, Crossplane should not independently mutate the same VPC fields. If Crossplane owns a database instance, the Terraform module should not also manage that database's lifecycle. Multiple tools can coexist when the resource boundary is explicit.

The most useful Rosetta question is "where does the feedback loop run?" In Terraform and OpenTofu, the loop normally runs when a plan or apply executes, so the review artifact is central. In Crossplane, the loop runs continuously in the cluster, so the resource contract and controller permissions are central. In Pulumi, the loop is expressed through program execution, so language review and state handling are central. In provider-native stacks, the cloud provider's stack engine is central. None of those loops is inherently more mature for every problem; each creates a different review, audit, and incident response shape.

The second Rosetta question is "who is the customer?" A platform team may be comfortable reviewing Terraform modules, but a service team may need a smaller interface. A product team with strong TypeScript or Python skills may prefer Pulumi components for its own infrastructure, while a central platform team may prefer Crossplane for shared self-service APIs. A cloud team may prefer provider-native stacks for tightly integrated services. The tool decision should follow the user, ownership boundary, and operational loop, not a generalized claim about which tool is fashionable.

The third Rosetta question is "what happens when the desired state is wrong?" Every tool can faithfully create a bad design. Crossplane may continuously reconcile a harmful setting. Terraform may apply a destructive plan. Pulumi may hide a risky change behind a component abstraction. A cloud stack may delete a nested resource because the template changed. Mature platform work assumes the desired state can be wrong and adds review, policy, staging, rendering, previews, and deletion safeguards around the workflow.

## Designing a Platform API

A good Crossplane API starts with the user's job, not with the provider's catalog. Suppose application teams need a relational database for typical services. The platform team could expose every field from a cloud database API, but that would push backup windows, deletion policy, subnet placement, parameter groups, encryption, tags, and engine-specific quirks onto every service team. A better first API might expose `engine`, `size`, `region`, and `highAvailability`, while the composition chooses storage encryption, network placement, labels, backup defaults, and connection-secret format.

That does not mean the API should be childish or underpowered. It means the API should express decisions the consumer is qualified to make. A service team often knows whether it needs PostgreSQL or MySQL, whether the workload is small or large, and which region matches the application. The platform team is usually better positioned to encode retention policy, network reachability, audit tags, secret naming, provider configuration, and safe deletion defaults. Crossplane is useful when it lets each party own the right part of the decision.

Here is a compact v2-style composite resource definition. It is intentionally smaller than a cloud provider database API. The schema is the product interface, so every field should earn its place. You can add versions over time, but changing field meaning after teams depend on it is still a breaking platform change even if Kubernetes accepts the YAML.

```yaml
apiVersion: apiextensions.crossplane.io/v2
kind: CompositeResourceDefinition
metadata:
  name: xdatabases.platform.example.org
spec:
  scope: Namespaced
  group: platform.example.org
  names:
    kind: XDatabase
    plural: xdatabases
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              engine:
                type: string
                enum: ["postgres", "mysql"]
                default: "postgres"
              size:
                type: string
                enum: ["small", "medium", "large"]
              region:
                type: string
                enum: ["us-east-2", "eu-west-1"]
            required:
            - size
            - region
          status:
            type: object
            properties:
              endpoint:
                type: string
              ready:
                type: boolean
```

A developer-facing instance should feel like an order form, not like a cloud provider certification exam. This example is still technical because infrastructure is technical, but it is much smaller than the real provider resource. The platform team can attach a composition that maps `small` to the provider's current shape, sets organization tags, chooses backup defaults, and writes status back to the composite resource.

```yaml
apiVersion: platform.example.org/v1alpha1
kind: XDatabase
metadata:
  name: orders-db
  namespace: team-payments
spec:
  engine: postgres
  size: small
  region: us-east-2
```

The hardest part of this design is deciding what not to expose. A common mistake is to add a field every time a provider supports a field. That creates the appearance of flexibility, but it erodes the platform product. If every consumer can choose backup retention, storage encryption, public accessibility, subnet placement, engine patching, and deletion behavior, the platform has delegated its guardrails away. It may still use Crossplane, but it has not created a safer or easier interface.

Good API design starts with categories of choice. User choices are values the application team understands and can justify, such as region, workload class, or engine family. Platform choices are values the organization wants to standardize, such as encryption, audit labels, network placement, and deletion protection. Negotiated choices are values that require a workflow, such as unusually large size, nonstandard retention, or cross-region replication. Crossplane can represent all three categories, but they should not all look like casual fields in the first version of the XRD.

Versioning is the pressure release valve. If you later discover that `size: large` hides too much variation, create a new version or a new field with a clear migration path. If a provider deprecates a field, change the composition behind the API when you can, and change the public API only when the user's decision actually changed. This is the same discipline used in service APIs: backward compatibility is not a paperwork exercise; it is how you preserve trust in a shared platform.

## Compositions and Functions

The composition is where the product API becomes concrete resources. Crossplane v2 favors function pipelines for composition logic. A function receives the observed composite resource and produces desired composed resources, often using patch-and-transform rules, templates, or custom code. This is more flexible than old native patch-and-transform fields, but it also means functions are part of your trusted platform runtime. They should be pinned, reviewed, and upgraded intentionally.

The following snippet shows the shape of a pipeline composition using function-patch-and-transform. It renders a simple `ConfigMap` contract instead of a live cloud database so you can study the mechanics without needing cloud credentials. In a real platform, the base resource might be a provider managed resource, a CloudNativePG cluster, a secret, a service binding object, or another Kubernetes resource that Crossplane has permission to compose.

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xdatabase-contract
spec:
  compositeTypeRef:
    apiVersion: platform.example.org/v1alpha1
    kind: XDatabase
  mode: Pipeline
  pipeline:
  - step: render-contract
    functionRef:
      name: function-patch-and-transform
    input:
      apiVersion: pt.fn.crossplane.io/v1beta1
      kind: Resources
      resources:
      - name: database-contract
        base:
          apiVersion: v1
          kind: ConfigMap
          metadata:
            namespace: default
          data:
            engine: ""
            size: ""
            region: ""
            deletionPolicy: "Orphan"
        patches:
        - type: FromCompositeFieldPath
          fromFieldPath: spec.engine
          toFieldPath: data.engine
        - type: FromCompositeFieldPath
          fromFieldPath: spec.size
          toFieldPath: data.size
        - type: FromCompositeFieldPath
          fromFieldPath: spec.region
          toFieldPath: data.region
```

This example looks modest, but it teaches the key boundary. The user owns the `XDatabase` fields. The platform composition owns how those fields become concrete resources. In a production composition, you would also think about readiness checks, connection details, status patches, provider configuration references, deletion policy, resource naming, environment-specific selection, and RBAC for any non-Crossplane resources the pipeline creates.

Composition review has a different flavor from application code review. You are not only checking whether the YAML is valid. You are checking whether the rendered resources preserve the product contract, whether user input can escape intended bounds, whether composed resources have stable ownership, whether status will be understandable, and whether a future provider change can be absorbed without breaking users. This is why local rendering is useful: it gives reviewers a concrete output to discuss before the composition runs with real credentials.

Function pipelines also create a supply-chain surface. A function package can contain logic that changes rendered resources, reads observed state, or participates in operational workflows. That does not make functions unsafe by default, but it means "we installed a function" should be treated like "we installed a controller." Pin the package, know who maintains it, read release notes, test upgrades, and restrict who can change function definitions in the cluster. A composition function is part of your platform's trusted computing base.

## Direct Managed Resources Versus Product APIs

Crossplane lets you create managed resources directly. That is useful for platform engineers, experiments, imports, and specialized teams that truly need the provider's detailed shape. Direct managed resources are also a good way to learn a provider because they show the close mapping between a Kubernetes object and an external API. The danger is turning that low-level mapping into the primary developer experience for everyone.

The difference is similar to using a standard library versus exposing assembly instructions to every application team. Direct managed resources are precise and powerful, but they force the user to understand provider-specific fields, lifecycle consequences, and failure messages. Composite resources create a smaller language that fits your organization. When a developer asks for a `small` database, the platform team can translate that into today's provider shape and change the translation later without changing every application manifest.

Use direct managed resources when the consumer is the platform team, when the resource is uncommon enough that a product API would be premature, or when you are importing and observing existing infrastructure before deciding how to productize it. Use composite resources when multiple teams need the same pattern, the organization wants guardrails, and the platform team can commit to owning the API as a supported product.

There is a useful middle stage between direct resources and a full product API. Platform engineers can first model a resource directly to learn provider behavior, status fields, deletion behavior, and failure messages. They can then wrap the repeated parts in a composition after they understand which options matter. This avoids premature abstraction. A rushed abstraction can be worse than a raw resource because it hides details before the platform team understands them well enough to hide them safely.

Brownfield adoption needs the same patience. Existing databases, buckets, and networks often have settings that do not match the desired future template. If Crossplane immediately takes full ownership, it may try to "fix" differences that are intentional or too risky to change in place. A staged approach can observe first, import carefully, adopt selected fields, and then move future resources to the standard API. The right question is not "can Crossplane manage this object?" but "what exact behavior do we want during adoption, drift, and deletion?"

## GitOps and Ownership

Crossplane resources are Kubernetes resources, so GitOps tools can apply them like other manifests. That is attractive because application and infrastructure requests can share a review path. A team can open a pull request that adds a service deployment and an `XDatabase` instance. Argo CD or Flux applies the resource. Crossplane reconciles the backing resources. The resulting status, conditions, and connection details become part of the cluster's observable state.

```
Git repository
  apps/payments/
    deployment.yaml
    xdatabase.yaml
        |
        v
GitOps controller applies manifests
        |
        v
Kubernetes API stores XDatabase
        |
        v
Crossplane composition renders resources
        |
        v
Provider or Kubernetes controller creates backing systems
        |
        v
Status and connection data flow back to the team namespace
```

GitOps does not remove the need for ownership design. It makes ownership more visible. Decide whether the application repository is allowed to change database size directly, whether production changes require extra review, whether Crossplane resources live beside application manifests or in a separate platform repository, and whether deletion from Git should delete, orphan, or pause external infrastructure. A clean GitOps story includes the deletion story, not just the creation story.

You should also decide how to handle promotion. Some teams keep one manifest and let composition selection choose environment-specific details through labels. Other teams keep separate staging and production overlays because production needs stricter review and different values. Crossplane can support both, but the platform contract should be explicit. A hidden environment switch in composition logic is convenient until a developer cannot tell why staging and production behave differently.

GitOps also changes incident response. If a production resource looks wrong, responders need to know whether the source of truth is the Git manifest, the composite resource, the composition, a provider config, or an external system. A clean platform has a short path from symptom to owner. The application team can inspect its namespaced XR and status. The platform team can inspect the composition revision, rendered resources, provider logs, and package versions. The GitOps team can inspect sync history and pruning behavior. When these responsibilities blur, a simple provisioning delay turns into a long meeting.

A practical pattern is to separate "request manifests" from "implementation packages." Application teams own the manifests that request product APIs in their namespaces. Platform teams own the XRDs, compositions, functions, provider configs, and policies that implement those APIs. GitOps can apply both, but usually from repositories with different review rules. That separation keeps self-service real without making every application repository a place where provider credentials or composition internals can change casually.

## Security and Secrets

Crossplane often sits close to powerful credentials. A provider may need permission to create cloud resources, mutate network settings, read connection details, or manage service accounts. Treat provider credentials as platform-level secrets, not as casual application configuration. The platform team should scope credentials as narrowly as the provider and cloud allow, rotate them, monitor their use, and keep provider configuration objects out of namespaces where application teams can modify them without review.

Connection details deserve equal care. A successful database provision is not useful if the password lands in the wrong namespace, uses an unpredictable key shape, or bypasses the organization's secret-management pattern. Your composite API should define where connection data appears, which keys are stable, who can read them, and how rotation works. If your organization uses an external secret operator, service binding convention, or workload identity pattern, include that in the composition design instead of treating it as a post-provisioning chore.

RBAC is another boundary. Namespaced resources help create team-level isolation, but they do not automatically make every composition safe. If a composition can create arbitrary resources, then a user who controls the composite input may be able to influence more than you intended. Use schema enums, validation, admission policy, and narrow composition logic to keep user input inside the allowed contract. Do not rely on "developers will not ask for unsafe values" as a security control.

Provider credentials should be split by blast radius. A development composition that creates sandbox resources should not need the same cloud identity as a production composition that creates stateful services. If the organization uses multiple cloud accounts or subscriptions, reflect that separation in provider configs and composition selection. This is less convenient than one global credential, but it gives incident responders a smaller question to answer when something goes wrong: which platform API, environment, and provider identity could have taken this action?

Secret delivery should be designed as part of the user journey. Developers should know which secret name or binding object to consume, which keys are stable, and what happens during rotation. Platform engineers should know whether secrets are written by provider managed resources, composed Kubernetes objects, an external secret operator, or another controller. If a composition creates credentials but the application consumes them through a different convention in each environment, Crossplane will appear unreliable even when provisioning is working correctly.

## Deletion, Orphaning, and Adoption

Deletion is where many infrastructure abstractions reveal whether they were designed carefully. A Kubernetes object can disappear quickly. A database, bucket, or cluster may contain production state that should not disappear simply because someone removed a line from a Git repository. Crossplane gives you lifecycle controls such as deletion behavior and management policies, but those controls have to be chosen deliberately and tested in an environment where failure is cheap.

Hypothetical scenario: A platform team launches a `Database` API for internal services. The first version composes a managed database instance and uses a deletion policy that deletes the external resource when the Kubernetes object is deleted. During a repository cleanup, an engineer removes a stale-looking production `Database` manifest, the GitOps controller prunes the object, and Crossplane begins deleting the backing database. The team has backups, but the restore consumes hours, the incident interrupts a launch, and trust in the self-service platform drops. The root cause is not Crossplane; it is an API contract that never explained what deletion meant.

The safer design is explicit. Production data resources often use orphaning, deletion protection, final snapshots, or a separate decommission workflow. Non-production sandboxes may delete automatically to control cost. Imported resources may start with observe-only or limited management until the team is confident that Crossplane owns the right fields. The point is not that one deletion policy is always correct. The point is that deletion behavior is part of the product contract and must be visible to users and reviewers.

Adoption is the mirror image of deletion. When you bring an existing resource under Crossplane management, you are not merely adding a Kubernetes object; you are changing who gets to declare truth. A production resource may have years of manual changes, emergency exceptions, and undocumented dependencies. Before adoption, inspect the external resource, compare it with the desired composition, identify fields that Crossplane will manage, and decide how to handle fields that must remain untouched. A careful import plan can build confidence, while a rushed import can create drift remediation during business hours.

The best decommission flows are boring. They make the user state intent, require the right review for production, preserve data when required, and leave an audit trail. Crossplane can participate in that flow, but it should not be the only guard. Git review, admission policy, deletion protection, final snapshots, backup checks, and runbook steps all have a role. A platform API is not mature because it can create resources quickly; it is mature because it can handle the full lifecycle without surprises.

## Troubleshooting and Operations

Troubleshooting Crossplane starts with the resource contract and then moves inward. First inspect the composite resource the user created. Is the schema accepted? Are conditions present? Does status show a reason or a missing dependency? Then inspect the composition and composition revision. Did the expected composition bind to the resource? Did a function render the composed resources you expected? Then inspect composed resources, provider pods, package health, events, and external API errors. This sequence keeps you from jumping straight into provider logs when the problem is actually an invalid user field or an unselected composition.

Conditions are the shared language between users and operators, but only if you make them useful. A condition that says a resource is not ready without explaining why forces everyone to inspect internals. A status field that exposes an endpoint before the resource is actually usable creates false confidence. A good composition maps enough information back to the composite for the user to answer simple questions: is my request accepted, is provisioning still progressing, what dependency is blocking it, and where will I find connection details when it is ready?

Operational ownership includes package lifecycle. Providers and functions should have owners, upgrade windows, smoke tests, and rollback plans. A provider upgrade can change behavior even when the composite API stays the same. A function upgrade can change rendering behavior. A Crossplane core upgrade can change default posture or deprecation warnings. Treat these upgrades as platform releases. Render sample compositions, apply representative XRs in a test control plane, verify status and deletion behavior, then promote the package versions through environments.

Cost and quota are also operational concerns. Self-service APIs make it easier to request infrastructure, which means they can also make it easier to spend money or exhaust quotas. Put cost-shaping decisions in the API and policy layers: allowed sizes, allowed regions, environment-specific limits, expiration labels for sandboxes, and review gates for unusual requests. Crossplane will reconcile what you let users ask for. Platform engineering means designing the request language so normal use is safe by default.

## Best Practices

1. **Start with a narrow product API.** A small schema with clear fields is easier to support than a giant abstraction that mirrors a provider. You can always add a field in a new version, but you cannot easily remove a field after teams build workflows around it.

2. **Keep provider churn behind the contract.** Provider API groups, package tags, field names, and resource capabilities move over time. Let compositions absorb that movement wherever possible, and put volatile facts in dated operational runbooks rather than teaching every application team the provider internals.

3. **Write status for humans.** A platform API that only says "Synced" forces users to inspect composed resources. Patch useful endpoint, readiness, reason, and reference information back to the composite resource so the user can understand progress from the object they created.

4. **Design deletion before launch.** Decide which resources delete, orphan, pause, or require manual decommissioning. Test those paths in staging and document them in the API contract before any production data resource uses the composition.

5. **Pin and review packages.** Crossplane providers and functions are executable components. Use explicit package references, review release notes, test upgrades, and avoid unqualified package names that hide registry or version choices.

6. **Separate ownership boundaries.** Do not let Crossplane, Terraform, Pulumi, and cloud console automation manage the same resource fields. Shared ownership creates reconciliation fights that are difficult to diagnose because each tool believes it is correcting drift.

7. **Use policy at multiple layers.** Schema validation, Kubernetes RBAC, admission policies, composition logic, cloud IAM, and review workflows reinforce one another. A platform API is safer when no single layer has to carry the entire control burden.

8. **Render and test compositions locally where possible.** `crossplane composition render` helps you inspect what a pipeline will produce before you install it in a control plane. Rendering is not a full integration test, but it catches many schema, patch, and naming mistakes earlier.

## Anti-Patterns

| Anti-pattern | Why it hurts | Better approach |
|--------------|--------------|-----------------|
| Raw-provider self-service | Developers must learn provider-specific resource models and failure modes. | Create composite APIs for repeated product patterns and reserve raw managed resources for platform engineers. |
| Invisible deletion behavior | A normal Git delete can become a destructive infrastructure action. | Make deletion policy part of the API design, and use separate decommission flows for production data. |
| One composition for every environment | Hidden conditionals make staging and production behavior hard to reason about. | Use clear composition selection, overlays, or separate environment contracts when behavior truly differs. |
| Status black holes | Users cannot tell whether provisioning is slow, broken, or waiting on a dependency. | Patch meaningful readiness and endpoint information back to the composite resource. |
| Package drift by accident | Unpinned or unreviewed packages change behavior under the platform team. | Pin package references, test upgrades, and track package ownership like any other controller. |
| Shared field ownership | Multiple tools reconcile the same resource and undo each other's changes. | Assign a single owner for each resource or field set, and document handoff rules for imports and migrations. |
| Secret afterthoughts | Credentials land in inconsistent places or with inconsistent key names. | Standardize connection detail shape, access, rotation, and integration with the organization's secret pattern. |
| Abstraction without support | A composition is launched but no team owns versioning, upgrades, or incidents. | Treat each composite API as a platform product with owners, release notes, tests, and support paths. |

## Did You Know?

- **Crossplane is about control planes, not only cloud infrastructure.** The current docs describe Crossplane as a control-plane framework for platform engineering, and v2 composition can work with Crossplane managed resources, Kubernetes resources, or third-party custom resources when RBAC allows it.
- **Crossplane v2 changes the beginner mental model.** New v2-style composite resources are namespaced and do not use claims, while v1-style resources remain relevant for compatibility and older installations.
- **Rendering is a powerful feedback loop.** The Crossplane CLI can render a composition pipeline locally with Docker, which lets platform teams inspect generated resources before applying a package to a cluster.
- **Provider and function packages are part of the platform runtime.** They are not just data files. They run controllers or pipeline logic, so package review, version pinning, and upgrade testing belong in the same operational discipline as other cluster extensions.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Copying old claim examples into a new v2 design | The API shape may work only through legacy compatibility assumptions. | Start with namespaced v2-style XRs, then use legacy claim patterns only when maintaining v1 APIs. |
| Exposing provider enums directly | Application teams inherit provider churn and cloud-specific vocabulary. | Translate provider details into durable platform choices such as size, region, durability, or class. |
| Ignoring composition RBAC | Functions may render resources Crossplane cannot create in a live cluster. | Grant access deliberately, especially for non-Crossplane resources, and test with realistic permissions. |
| Treating `Ready` as the only status | Users still need endpoint, reason, and dependency context. | Patch user-relevant status fields and document what each condition means. |
| Letting GitOps prune production data | Removing a manifest can remove an external system if deletion is not guarded. | Use orphaning, deletion protection, or explicit decommission workflows for stateful production resources. |
| Forgetting import and brownfield paths | Existing resources cannot always be recreated safely from a new composition. | Plan observe, import, or staged adoption workflows before moving brownfield infrastructure under Crossplane. |
| Hiding cloud IAM under Kubernetes RBAC | A user may not edit a provider config, but the provider credential may still be too broad. | Scope cloud credentials, monitor provider actions, and separate provider configs by account or environment. |
| Skipping package upgrade tests | Provider and function changes can alter reconciliation behavior. | Maintain a test control plane, render compositions, apply sample XRs, and review release notes before upgrades. |

## Quiz

### Question 1

A team says, "Crossplane lets developers create cloud resources with YAML, so we can expose every provider managed resource directly." What is the platform-design flaw in that plan?

<details>
<summary>Answer</summary>

Direct managed resources are useful, but exposing them as the default self-service interface often pushes provider complexity onto application teams. A platform API should usually expose the decisions the consumer understands and keep provider-specific details in compositions. The better design is to create composite resources for repeated products, such as databases or queues, while reserving raw managed resources for platform engineers or specialized cases.

</details>

### Question 2

Why does the module place CNCF maturity, current release, and package versions in a dated landscape snapshot instead of weaving those facts throughout the prose?

<details>
<summary>Answer</summary>

Those facts are volatile. CNCF maturity, project versions, provider package tags, and documentation lines can change faster than the curriculum should be rewritten. A dated snapshot makes the current state easy to refresh while preserving the durable teaching: desired state, reconciliation, provider boundaries, composition, API contracts, and ownership.

</details>

### Question 3

In a new Crossplane v2 design, why should you think carefully before copying an older `claimNames` example?

<details>
<summary>Answer</summary>

Crossplane v2-style composite resources are namespaced and do not use claims. Older claim-centered examples can still matter for v1-style compatibility, but they should not be the default mental model for new APIs. A new design should start with namespaced XRs, RBAC boundaries, and a clear product schema, then use legacy claim patterns only when there is a specific compatibility reason.

</details>

### Question 4

Your GitOps controller prunes a production `XDatabase` because the manifest was removed from Git. What Crossplane design questions should have been answered before launch?

<details>
<summary>Answer</summary>

The platform team should have defined deletion behavior as part of the API contract. They should know whether deleting the composite resource deletes the external database, orphans it, pauses management, requires a final snapshot, or triggers a separate decommission workflow. They should also document who can approve production deletion and test the behavior in a safe environment.

</details>

### Question 5

How can Crossplane and Terraform coexist without fighting over infrastructure?

<details>
<summary>Answer</summary>

They can coexist when ownership boundaries are explicit. Terraform might own foundational networking while Crossplane owns developer-facing databases, or Crossplane might observe a resource before taking over selected fields. The dangerous pattern is letting both systems reconcile the same resource fields. Each resource or field set needs a single owner and a documented handoff process.

</details>

### Question 6

Why is `crossplane composition render` useful even though it is not a complete integration test?

<details>
<summary>Answer</summary>

Rendering lets the platform team inspect what a composition pipeline produces before installing it into a control plane. It can catch missing patches, wrong field paths, unexpected names, and package input mistakes early. It does not prove cloud credentials, provider controllers, RBAC, or external API behavior, so it should be followed by live-cluster tests for production compositions.

</details>

### Question 7

A developer asks for a new field named `storageEncrypted` on the `XDatabase` API because the underlying provider supports it. How should the platform team evaluate that request?

<details>
<summary>Answer</summary>

The team should ask whether this is truly a user decision or a platform guardrail. If every database must be encrypted, the field should not be exposed; the composition should enforce encryption. If there are legitimate product choices with different operational consequences, the API might expose a higher-level option with validation and documentation. The provider field name itself should not automatically become the platform contract.

</details>

## Hands-On Exercise

The goal of this exercise is to render a tiny Crossplane composition locally so you can see the API-to-resource translation without provisioning cloud infrastructure. You need the Crossplane CLI v2.3 line, Docker Engine for function execution, and a shell. The exercise writes three files and runs `crossplane composition render`; it does not require cloud credentials.

Create `xr.yaml` with the user-facing resource. This is the shape an application team would understand: engine, size, and region. It deliberately avoids provider-specific settings because the composition owns those details.

```yaml
apiVersion: platform.example.org/v1alpha1
kind: XDatabase
metadata:
  name: render-demo
  namespace: default
spec:
  engine: postgres
  size: small
  region: us-east-2
```

Create `composition.yaml` with a function pipeline that renders a `ConfigMap`. A production version might render provider managed resources, but this local exercise renders a harmless Kubernetes object so you can focus on patch mechanics.

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xdatabase-contract
spec:
  compositeTypeRef:
    apiVersion: platform.example.org/v1alpha1
    kind: XDatabase
  mode: Pipeline
  pipeline:
  - step: render-contract
    functionRef:
      name: function-patch-and-transform
    input:
      apiVersion: pt.fn.crossplane.io/v1beta1
      kind: Resources
      resources:
      - name: database-contract
        base:
          apiVersion: v1
          kind: ConfigMap
          metadata:
            namespace: default
          data:
            engine: ""
            size: ""
            region: ""
            deletionPolicy: "Orphan"
        patches:
        - type: FromCompositeFieldPath
          fromFieldPath: spec.engine
          toFieldPath: data.engine
        - type: FromCompositeFieldPath
          fromFieldPath: spec.size
          toFieldPath: data.size
        - type: FromCompositeFieldPath
          fromFieldPath: spec.region
          toFieldPath: data.region
```

Create `functions.yaml` with the pinned function package used by the composition. The package tag is intentionally explicit because Crossplane v2 requires fully qualified package references and because function behavior is part of your platform runtime.

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Function
metadata:
  name: function-patch-and-transform
spec:
  package: xpkg.crossplane.io/crossplane-contrib/function-patch-and-transform:v0.10.7
```

Render the composition locally and inspect the output. You should see the original composite resource followed by a generated `ConfigMap` whose `data.engine`, `data.size`, and `data.region` fields were copied from the composite resource.

```bash
crossplane composition render xr.yaml composition.yaml functions.yaml
```

Success criteria:

- [ ] The composition render command exits successfully.
- [ ] The output includes a `ConfigMap`.
- [ ] The rendered `ConfigMap` contains `engine: postgres`.
- [ ] The rendered `ConfigMap` contains `size: small`.
- [ ] The rendered `ConfigMap` contains `region: us-east-2`.
- [ ] You can validate the composition render and explain user input versus platform-owned defaults.

For a bonus exercise, add a new `tier` field to `xr.yaml`, add it to the rendered `ConfigMap`, and explain whether that field belongs in the public platform API. If the answer is "only platform engineers need it," remove the field again and set the value inside the composition instead. The purpose is to practice API discipline, not to add knobs for their own sake.

## Sources

- [CNCF Crossplane project page](https://www.cncf.io/projects/crossplane/)
- [Crossplane v2.3.2 GitHub release](https://github.com/crossplane/crossplane/releases/tag/v2.3.2)
- [Crossplane documentation landing page](https://docs.crossplane.io/latest/)
- [What is Crossplane?](https://docs.crossplane.io/latest/whats-crossplane/)
- [What's new in Crossplane v2](https://docs.crossplane.io/latest/whats-new/)
- [Install Crossplane](https://docs.crossplane.io/latest/get-started/install/)
- [Managed resources](https://docs.crossplane.io/latest/managed-resources/managed-resources/)
- [Managed resource activation policies](https://docs.crossplane.io/latest/managed-resources/managed-resource-activation-policies/)
- [Composite resources](https://docs.crossplane.io/latest/composition/composite-resources/)
- [Composite resource definitions](https://docs.crossplane.io/latest/composition/composite-resource-definitions/)
- [Compositions](https://docs.crossplane.io/latest/composition/compositions/)
- [Composition functions](https://docs.crossplane.io/latest/composition/composition-functions/)
- [Function Patch and Transform guide](https://docs.crossplane.io/latest/guides/function-patch-and-transform/)
- [Crossplane providers](https://docs.crossplane.io/latest/packages/providers/)
- [Crossplane configurations](https://docs.crossplane.io/latest/packages/configurations/)
- [Import existing resources](https://docs.crossplane.io/latest/guides/import-existing-resources/)
- [Crossplane CLI v2.3 documentation](https://docs.crossplane.io/cli/v2.3/)
- [Function Patch and Transform v0.10.7 release](https://github.com/crossplane-contrib/function-patch-and-transform/releases/tag/v0.10.7)

## Next Module

Continue to [Module 7.3: cert-manager](../module-7.3-cert-manager/) to learn how certificate automation turns another operational workflow into a declarative platform capability.
