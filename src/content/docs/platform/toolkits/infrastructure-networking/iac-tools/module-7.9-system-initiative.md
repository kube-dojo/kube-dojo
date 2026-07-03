---
revision_pending: false
title: "Module 7.9: System Initiative - DevOps Automation Reimagined"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.9-system-initiative
sidebar:
  order: 10
---
## Complexity: `[COMPLEX]`

## Time to Complete: 50-55 minutes

---

## Prerequisites

Before starting this module, you should have completed [Module 7.1: Terraform](../module-7.1-terraform/) so the desired-state, state-file, drift, and plan/apply vocabulary is familiar. You should also have read [Module 7.3: Pulumi](../module-7.3-pulumi/) or an equivalent infrastructure-from-code module, because System Initiative sits beyond that point on the abstraction spectrum rather than beside Terraform as another template syntax.

This module is not a production recommendation. It uses System Initiative as a clear case study for model-based infrastructure automation: build a high-fidelity simulation of infrastructure, let properties propagate through a graph, validate model changes before execution, and reconcile intent with provider-reported reality. Those ideas remain useful even when a specific tool, company, or hosted service changes status.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Explain** where System Initiative sits on the IaC spectrum from scripts to declarative templates, infrastructure-from-code, and model-based reactive automation.
- **Model** components, resources, subscriptions, and change sets as a digital twin that separates intended configuration from provider-reported reality.
- **Evaluate** qualification functions, reactive property propagation, and bidirectional sync as safety mechanisms for platform self-service.
- **Compare** System Initiative with Terraform/OpenTofu, Pulumi, and cloud development kits using durable capability tradeoffs instead of vendor momentum claims.

---

## Why This Module Matters

Most infrastructure automation failures are not caused by one missing syntax feature. They appear in the space between tools: a pull request changes Terraform, a CI job applies it, a cloud console hotfix drifts reality, a ticketing workflow carries approval context, an architecture diagram falls behind, and a platform engineer tries to reconstruct what the system actually looks like under incident pressure. Each piece can be reasonable in isolation, but the handoffs become the operational tax.

Traditional IaC improved the old world of shell scripts by giving teams versioned declarations and repeatable plans. That remains valuable. The limit appears when the real workflow is not simply "make this static desired state true." Platform teams often need to discover existing resources, model relationships across tools, preview a change in context, ask policy questions while a user is editing, and then decide whether reality should update intent or intent should update reality. That is a different problem shape than compiling a directory of templates.

System Initiative is useful to study because it tried to make the model itself the primary interface. Instead of treating code as the only source of truth, it represented infrastructure as data in a reactive graph. Components carried intended configuration. Resources carried provider-reported reality. Subscriptions propagated values between components. Change sets acted like safe simulations where edits could be reviewed before they were applied. Qualification functions gave immediate feedback when a proposed configuration violated a rule.

The durable idea is not that every team should use a visual canvas or a particular product. The durable idea is that infrastructure automation can move from "write declarations and hope the plan explains enough" toward "operate on a living model that understands relationships, state, policy, and drift." That model-based approach is the far end of the IaC spectrum: more ambitious than declarative templates, more opinionated than programming-language IaC, and more dependent on the platform owning a coherent view of the world.

Use a spreadsheet analogy. Terraform-style declarative IaC is like writing down the expected values in a workbook and asking a reconciler to compare them with the last saved copy. Pulumi-style infrastructure-from-code is like generating those sheets with a real programming language. A reactive model is closer to a workbook whose cells have formulas, validation rules, comments, and live data imports. Change the VPC CIDR cell, and subnet cells recalculate. Change the provider-reported value, and the model can show that reality no longer matches intent.

That extra context has a cost. A model-based platform asks engineers to trust a database and execution engine that are not Git, not a simple state file, and not just a wrapper around provider APIs. Debugging moves from reading source files to inspecting graph nodes, subscriptions, generated actions, function results, and audit history. Lock-in also changes shape: the more knowledge you encode in one platform's schemas and model semantics, the more migration work you face later if the platform disappears or the organization changes direction.

The right way to read this module is therefore disciplined curiosity. Learn the abstraction, learn what it solves, and learn why it is risky. Do not memorize the old CLI flow as if it were stable. The current status snapshot below is intentionally dated because vendor tooling changes quickly, and in this case the project status changed in a way that matters for real adoption decisions.

---

## Did You Know?

- **Digital twins are not only for physical systems** - In infrastructure automation, a digital twin means the model keeps both desired intent and observed provider reality visible instead of collapsing one into the other.
- **A graph can reveal side effects a file diff hides** - If one component subscribes to another component's property, a single edit can cause downstream values to change even when no human directly edited those downstream components.
- **Validation timing changes behavior** - A qualification that runs while you edit catches a different class of mistake than a policy check that runs only after a pull request or deployment job starts.
- **A model is a product surface** - When engineers change infrastructure through a platform database, the schema, permissions, audit log, and escape hatches become part of the platform's user experience.

---

## 1. The IaC Spectrum: From Commands to Models

Imperative scripts were the first automation step for many teams. A shell script or Python script calls cloud APIs in sequence: create the network, create the subnet, create the instance, attach the security group, and print the result. That style is easy to start because it mirrors what an operator would do manually. It is also easy to break because the script must handle retries, partial failure, idempotency, dependency ordering, and discovery of resources that already exist.

Declarative templates changed the center of gravity. Tools such as Terraform, OpenTofu, CloudFormation, and ARM/Bicep let you describe desired resources while an engine works out the provider calls needed to reach that state. The state record becomes important because the tool needs to map a logical declaration to a physical cloud object. Plans and change sets give reviewers a way to inspect intended changes before execution, although reviewers still need to understand provider semantics and module abstractions.

Infrastructure-from-code moved authoring into general-purpose languages. Pulumi, AWS CDK, and similar approaches let you use loops, functions, classes, packages, and tests to produce a resource graph or provider-native template. That can reduce awkward templating when infrastructure is highly parameterized. It can also create new complexity because ordinary code can hide resource declarations behind abstractions, generate large plans, or run side effects during preview if engineers are careless.

Model-based reactive automation takes another step. Instead of asking a program to synthesize a declaration, it asks a platform to maintain a live model of infrastructure and relationships. The model stores properties, dependencies, computed values, validation results, pending actions, and observed reality. Users or agents mutate the model through a UI, API, or CLI; the platform records those mutations as change sets; functions compute downstream effects; and provider actions apply approved changes to the real world.

That spectrum is not a maturity ladder where every organization must march to the end. It is a set of tradeoffs. Scripts optimize immediacy and local control. Declarative IaC optimizes reviewable desired state. Infrastructure-from-code optimizes language expressiveness. Model-based automation optimizes contextual operations on a shared graph. The more context the tool owns, the more it can help with propagation, policy, and collaboration, but the more you depend on its data model.

The distinction matters because teams sometimes evaluate a model-based platform using the wrong criteria. Asking "where are the files I review in Git" is a fair governance question, but it may miss the tool's point. The point is not to make a prettier Terraform module. The point is to make infrastructure relationships first-class data that can be queried, simulated, validated, and reconciled from both directions. If that is not the problem you have, the abstraction may be unnecessary.

```text
IaC abstraction spectrum

Manual operations
  |
  v
Imperative scripts
  - You encode steps.
  - You own retries, discovery, and partial failure.

Declarative templates
  - You encode desired resources.
  - The engine owns diff and reconciliation against state.

Infrastructure from code
  - You encode programs that produce resource graphs.
  - The engine still owns preview and apply.

Model-based reactive automation
  - You mutate a shared model of intent and reality.
  - The platform owns graph propagation, validation, and action execution.
```

System Initiative belongs at the model-based end. Its public documentation described components as one-to-one mappings to provider resources, subscriptions as property propagation between components, change sets as simulation and change-control mechanisms, and qualifications as validation functions that evaluate configuration and resource state. Those concepts are the teaching value of the tool, independent of whether you ever operate the archived implementation.

---

## 2. Landscape Snapshot - as of 2026-06

> **Landscape snapshot - as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**
>
> System Initiative, Inc. was associated with founders Adam Jacob, the co-founder and former CTO of Chef, and Mahir Lupinacci. Public coverage reported that the company raised $18M. The main `systeminit/si` repository reports an Apache-2.0 license, and The New Stack reported the project as fully open source rather than open-core, with no enterprise-only withheld feature set.
>
> The production-readiness status is the critical fact: as of 2026-06, the `systeminit/si` GitHub repository is archived and read-only. Its final commit was dated 2026-02-06 and stated that System Initiative was no longer maintained. A GitHub API check of the public `systeminit` organization showed thirty-one of thirty-two repositories archived, so the project/company appears to have wound down or been discontinued. Verify before relying on the hosted service, docs, install commands, provider coverage, or any operational path.
>
> Treat System Initiative in this curriculum as a clear illustration of model-based and digital-twin DevOps automation, not as a recommended production platform. Current version numbers, hosted-service availability, supported cloud-provider coverage, governance, and maintainer activity must be confirmed against upstream sources at the time of any real evaluation.

This snapshot belongs in one place because the rest of the module is about durable architecture. If you weave project status into every paragraph, the learning becomes a dated product obituary. If you omit it, the lesson becomes irresponsible. Keeping the current facts here lets you study the design honestly while preserving a clean boundary between long-lived concepts and volatile vendor reality.

---

## 3. The Problem: Glue Between DevOps Tools

The platform problem System Initiative targeted is easiest to see in a mundane request. A developer wants a service deployed in a new environment. The actual work crosses a network module, IAM policy, container registry, Kubernetes deployment, DNS record, monitoring dashboard, deployment pipeline, ticket approval, and maybe a runbook update. Each tool has its own state and its own notion of what changed. The platform team becomes the glue layer that keeps those systems aligned.

Declarative IaC helps with part of that flow. It can define the network, registry, database, and DNS record. It can preview changes and create an auditable merge history. It does not automatically know that a dashboard should be updated when a service relationship changes, that an existing production resource discovered through the console should become part of the model, or that a proposed property value should trigger a policy warning while the user is still composing the change.

Glue work grows because infrastructure is relational. A subnet belongs to a VPC. A route table references a gateway. A security group grants traffic from another security group. A deployment references an image tag. A certificate depends on a DNS validation record. A service-level objective depends on a monitor. In file-based IaC, those relationships are often spread across modules, outputs, remote state, provider data sources, naming conventions, and documentation that may or may not still be current.

A model-based platform tries to move that relational context into one graph. Instead of expressing each relationship indirectly through a text interpolation, it stores the relationship as data. Instead of discovering drift only when a plan runs, it can maintain separate intent and reality views. Instead of asking every reviewer to infer policy from a large diff, it can run qualifications against the edited component and show validation status close to the thing being changed.

The tradeoff is that the glue does not disappear. It moves. Someone must design schemas, write functions, decide what provider data belongs in the model, define permission boundaries, maintain credentials, and teach users what the model means. If the platform does those things well, routine changes can become safer and more contextual. If it does them poorly, the organization now has one more complex system between humans and cloud APIs.

**Hypothetical scenario:** A platform group supports several product teams that share a landing-zone pattern. The old workflow uses Terraform modules, pull requests, and a ticket queue for each new environment. The slow part is not writing the first VPC. The slow part is checking whether subnet ranges overlap, whether tags match policy, whether the service has the right route, whether the diagram was updated, whether the monitoring template was copied, and whether a manual hotfix changed the baseline. A model-based platform could represent those relationships directly and validate them while the user edits the proposed environment.

That hypothetical scenario does not prove model-based automation is cheaper or better. It shows the class of problem the design addresses. When your main pain is authoring a small number of stable resources, the model may feel heavy. When your main pain is coordinating many related changes across teams, tools, and existing infrastructure, a shared graph becomes more interesting.

---

## 4. Digital Twin: Intent and Reality Side by Side

The most important System Initiative concept is the digital twin. In this context, a digital twin is not a decorative architecture diagram. It is a structured model that keeps two views of a resource visible: what the user intends and what the provider reports. The intended view answers "what do we want this configuration to be?" The reality view answers "what does the cloud provider say exists right now?"

That separation is powerful because drift stops being a mystery. In many IaC workflows, drift is discovered by refreshing state or running a plan. If someone changes a database setting in a cloud console, the IaC state can become stale until the next refresh. A digital-twin model can represent the intended value and the observed value at the same time, making the disagreement explicit. A human or policy function can then decide whether to accept reality, enforce intent, or investigate.

Bidirectional sync is the design leap. Traditional IaC usually flows from source to provider: write code, plan, apply, and update state. A model-based platform can also flow from provider to model: discover a real resource, create model objects that represent it, and then let users automate future changes from that point forward. That matters in brownfield organizations where important infrastructure was not born inside a clean repository.

The bidirectional idea does not mean the platform should blindly copy every provider value into desired state. Reality includes accidental manual changes, emergency fixes, provider defaults, and values the team may not want to manage. Good reconciliation distinguishes "accept this discovered value as intent" from "leave this as provider-owned reality" and "apply an action to return reality to intent." Without that distinction, bidirectional sync can legitimize drift instead of controlling it.

The model also changes collaboration. A diagram manually drawn after deployment is documentation. A model that drives deployment is operational state. If a component on the canvas represents a real load balancer and its attributes feed actions, then editing the model is not a harmless sketch. It is a proposed infrastructure change that needs permissions, review, audit logging, rollback thinking, and clear separation between simulation and execution.

```text
Digital twin mental model

Component
  - Intent tree: values users or agents want.
  - Relationships: subscriptions to other components.
  - Functions: validation, generation, management, actions.

Resource
  - Reality tree: values reported by the provider.
  - Provider identifiers: IDs, status, metadata, observed settings.
  - Drift signal: where reality and intent disagree.

Change set
  - A safe copy of the model where proposed mutations can be reviewed.
  - Downstream effects are computed before actions update real resources.
```

Think carefully about authority. In Git-centered workflows, source files are usually treated as the authority for desired infrastructure. In System Initiative's model, a component's intent data is authoritative for desired configuration, and the resource data is authoritative for observed provider state. The platform becomes the place where those two authorities are compared. That is a different governance model, not just a different UI.

---

## 5. Reactive Property Propagation

Reactive property propagation is the mechanism that makes the graph feel alive. A component can subscribe to a value from another component. When the source value changes, the dependent value updates. In a network model, a subnet component might subscribe to a VPC identifier. In a service model, a deployment might subscribe to an image tag or endpoint. The point is that dependencies are data flows, not just strings copied between files.

This is where the spreadsheet analogy becomes useful. If a spreadsheet cell contains a formula that references another cell, you do not manually update every dependent cell after the source changes. The sheet recalculates. A reactive infrastructure model makes that style of dependency explicit for infrastructure properties. A change to a region, account, network range, component name, or provider identifier can produce downstream changes before anything is applied to reality.

Reactive propagation addresses a real weakness in file-based workflows: reviewers often see the direct edit but miss the derived effects. A Terraform plan can reveal many of those effects, but the relationship usually appears as a provider diff rather than as a domain-level explanation. A model can record the actual dependency path: this subnet's VPC ID changed because it subscribes to that VPC component, which changed because this change set selected another region.

The danger is hidden magic. If users cannot inspect subscriptions, function inputs, and recomputed values, reactive automation becomes harder to trust than explicit declarations. A mature model-based platform needs excellent explainability: show the source property, show the target property, show the function that transformed the value, show who changed the upstream value, and show whether downstream changes will enqueue real provider actions.

Reactive propagation also creates schema-design pressure. If a schema exposes every provider field with no opinion, users may drown in attributes. If it hides too much, the abstraction leaks when a production edge case appears. Good schemas choose which properties are user-managed, which are provider-managed, which are derived from relationships, and which require explicit override. That is platform product design as much as infrastructure engineering.

One useful review question is "would we be surprised if this value changed?" If the answer is yes, the model needs better visibility. Reactive systems are safest when users can predict the propagation path. They are dangerous when a small edit silently cascades into a large change set that nobody understands until provider actions begin.

---

## 6. Change Sets as Simulation Boundaries

A change set is the boundary between exploration and execution. In a model-based workflow, a user should be able to propose changes, watch derived values update, run qualifications, inspect generated actions, and ask for review without touching real infrastructure. Only after the change is accepted should provider actions mutate the external world. That separation is the operational equivalent of a branch, a plan, and an approval gate combined into a platform-native object.

System Initiative's docs described change sets as simulation and change-control mechanisms. The useful durable idea is that a change set is not merely a text diff. It is a snapshot of the model plus a set of mutations and downstream effects. If one user changes a component property and a subscription updates several dependent properties, the change set can track both the original edit and the derived edits. That gives reviewers a more complete impact view than a hand-authored patch alone.

Simulation boundaries matter because infrastructure is expensive to learn from by accident. If a proposed region change would force replacement of stateful resources, the user should learn that before action execution. If a policy qualification fails, the user should see it while the change set is still safe. If reality has changed since the change set was opened, the platform should update or invalidate the proposal so reviewers do not approve stale assumptions.

The model-based approach also changes conflict handling. In Git, two branches can conflict at the file level even when the underlying infrastructure changes are compatible. In a graph model, the platform can reason about operational transforms against the model. That does not remove all conflict risk, because two users can still propose incompatible infrastructure outcomes, but it gives the platform a richer object to compare than lines of text.

There is a governance tradeoff. Git-based workflows have decades of mature review, signing, branch protection, and audit tooling. A model-based platform must recreate or integrate those controls in its own world. Who can create a change set? Who can apply one? What approval is required for production? How are actions logged? Can a regulator reconstruct the change? Can a team export the model if the platform goes away? These questions are not optional.

The practical lesson is to treat change sets as first-class operational artifacts. A good change set should answer what changed, why it changed, which downstream values changed, which qualifications passed or failed, which provider actions will run, and how the team can recover if execution fails. If it cannot answer those questions, the visual model may be attractive but the operational discipline is weak.

---

## 7. Qualification Functions and Policy Timing

Qualification functions are validation functions attached to the model. They inspect component configuration, generated artifacts, and resource state, then return a result such as success, warning, or failure. The important point is timing. A qualification can run while a user is shaping a proposed change, not only after code review or deployment. That moves feedback closer to the moment of intent.

Policy timing changes behavior because people respond differently to immediate feedback. If a developer drags a database component into a model and instantly sees that encryption is missing, the fix is part of normal design. If the same issue appears after a long CI pipeline, it feels like a bureaucratic rejection. Earlier feedback is not automatically more correct, but it tends to be cheaper and easier to act on.

Qualifications also support self-service platform design. A platform team can allow users to propose infrastructure changes while encoding safety checks near the resources. For example, a qualification can warn about public ingress, fail missing backup retention, or verify that a referenced provider resource exists. The user still owns the request, but the platform provides guardrails that do not depend solely on a human reviewer reading every property.

The limitation is that qualifications are only as good as the model and the code behind them. If a qualification checks a stale resource view, it can pass the wrong configuration. If it encodes policy too rigidly, teams will ask for bypasses. If failures are vague, users will learn to treat the platform as an obstacle. Good qualification design includes clear messages, actionable remediation, severity levels, and a documented exception path for unusual but valid cases.

Do not confuse qualifications with complete security. They are one layer. You still need cloud IAM, provider-side policy, secrets management, change approval, monitoring, and incident response. A model-based platform can make policy more visible and earlier in the workflow, but it cannot make organizational risk disappear. The platform team remains responsible for deciding which checks belong in the model and which belong closer to the provider.

Here is a simplified qualification shape. It is not a current System Initiative API guarantee; it is a durable pattern: read a component's intended properties, optionally read observed reality, and return a structured result that the platform can display and enforce.

```typescript
type QualificationResult = {
  result: "success" | "warning" | "failure";
  message: string;
};

function qualifySecurityGroup(component: {
  domain: {
    ingress: Array<{ fromPort: number; toPort: number; cidr: string }>;
    owner: string;
  };
}): QualificationResult {
  const openSsh = component.domain.ingress.some(
    (rule) => rule.cidr === "0.0.0.0/0" && rule.fromPort <= 22 && rule.toPort >= 22,
  );

  if (openSsh) {
    return {
      result: "failure",
      message: "SSH ingress from the public internet is not allowed; restrict the CIDR or use a bastion pattern.",
    };
  }

  if (!component.domain.owner) {
    return {
      result: "warning",
      message: "Owner metadata is missing; add an accountable team before production apply.",
    };
  }

  return { result: "success", message: "Security group passes baseline checks." };
}
```

Read this code as a teaching artifact, not as a recommendation to bypass upstream docs. The durable lesson is the input-output contract. A qualification consumes model data and returns a status the platform can surface before action execution. That contract is valuable whether the implementation lives in System Initiative, an internal developer portal, a policy engine, or a CI validation step.

---

## 8. Rosetta Table: Capability Comparison

The table below compares durable capabilities rather than ranking tools. It includes a license/governance row because governance affects adoption, but those values are volatile and must be verified against upstream sources. For System Initiative specifically, use the dated snapshot above as the authority for current status.

| Capability | System Initiative | Terraform/OpenTofu | Pulumi | AWS CDK or Wing-style tools |
|---|---|---|---|---|
| Abstraction model | Shared model of components, resources, subscriptions, functions, and change sets | Declarative resource graph written in configuration files | Resource graph registered by programs in general-purpose languages | Application or construct code synthesizes provider-native infrastructure artifacts |
| Primary authoring surface | Web UI, API, CLI, and functions mutate model data | HCL files, modules, providers, and state backends | TypeScript, Python, Go, C#, Java, YAML, and stack configuration | TypeScript/Python/etc. constructs for CDK; cloud-oriented language patterns for Wing-like tools |
| What compiles or synthesizes | Model mutations become actions against providers after review | Configuration plus state becomes a plan and provider operations | Program execution registers resources; engine previews and applies | Source code synthesizes CloudFormation, Terraform, or another deployment artifact depending on tool |
| State management | Model stores intent and provider-reported reality as separate but related data | State tracks logical resources and physical provider IDs | Stack state tracks registered resources, provider versions, and outputs | Usually delegates state to the synthesized target, such as CloudFormation or Terraform |
| Target clouds | Provider coverage depends on schemas and integrations; verify current status | Broad provider ecosystem through Terraform/OpenTofu providers | Broad provider ecosystem, including bridged providers and native packages | Often strongest in the cloud or runtime ecosystem the tool was designed around |
| Drift handling | Digital twin can expose intent-versus-reality differences and support accept-or-enforce decisions | Refresh and plan reveal differences between state/configuration and provider reality | Refresh and preview reveal differences for the selected stack | Depends on synthesized backend and provider-native drift tooling |
| Primary use case | Coordinated changes across a shared infrastructure model, including discovery, policy, and collaboration | Reviewable desired state for infrastructure provisioning across many providers | Language-native infrastructure abstractions and reusable software-style components | Application-centric cloud infrastructure with construct libraries or local simulation |
| License and governance | See the 2026-06 snapshot; archived Apache-2.0 repository, verify before relying | Verify project and provider licenses separately, especially after ecosystem forks | Verify open-source engine, service terms, and provider packages separately | Verify tool-specific license, hosted-service dependency, and target-platform governance |

The most useful comparison question is not "which tool wins?" It is "where does our team want the source of truth to live, and what operations do we need the tool to understand?" If the answer is "reviewable files and mature provider coverage," declarative IaC remains strong. If the answer is "real programming languages and internal libraries," infrastructure-from-code may fit. If the answer is "a shared operational model that includes discovered reality and reactive relationships," model-based automation is the concept to evaluate.

The table also shows why migration can be hard. Moving from Terraform to Pulumi changes authoring language but preserves much of the plan/apply and state mindset. Moving from file-based IaC to a model-based platform changes where intent lives, how reviews happen, how drift is represented, and how users inspect dependencies. That is a bigger organizational change than adopting another provider plugin.

---

## 9. Tradeoffs and Failure Modes

The first tradeoff is mental model. Many infrastructure engineers trust files because files are inspectable, diffable, searchable, and easy to archive. A graph database with functions and reactive subscriptions can feel opaque even when it is technically more expressive. Teams adopting a model-based platform need training that explains how the graph works, how changes are audited, how generated actions are inspected, and how to recover when a function misbehaves.

The second tradeoff is ecosystem maturity. Declarative IaC ecosystems have extensive examples, provider coverage, modules, CI integrations, policy tooling, and operational folklore. A newer model-based platform must build equivalent depth or integrate with existing tools. If provider schemas lag cloud APIs, users will fall back to manual work. If import and discovery are incomplete, brownfield adoption becomes selective. If the hosted service disappears, the organization needs an exit plan.

The third tradeoff is lock-in to the model. Every platform encodes concepts in its own way: schema variants, component paths, subscriptions, functions, action queues, permissions, and audit records. That encoded knowledge is valuable while the platform is healthy, but it becomes migration debt if the platform is retired. A serious evaluation should ask how to export the model, how to preserve audit history, and how to recreate critical infrastructure definitions in another tool.

The fourth tradeoff is debuggability. File-based IaC failures can be painful, but the debugging path is familiar: inspect the plan, read provider logs, check state, and reproduce locally. Model-based failures may require inspecting function execution, graph snapshots, derived attributes, queued actions, provider credentials, and reality polling. The richer the model, the more important the introspection tools become. Without them, users will blame the platform even when the provider caused the failure.

The fifth tradeoff is governance. A platform that lets users or agents propose changes directly against a model must have strong authorization boundaries. It must distinguish viewing a model from changing intent, changing intent from applying actions, and applying low-risk actions from applying production-impacting actions. A Git pull request has familiar social and technical controls. A model-based platform needs equally clear controls or it will create a parallel change path that security teams cannot reason about.

The sixth tradeoff is abstraction leakage. No model can perfectly hide provider reality. Cloud APIs have quotas, eventual consistency, replacement semantics, regional differences, and service-specific edge cases. A good model exposes the right provider details at the right time. A weak model hides important details until an action fails. Engineers should distrust any platform that promises to remove all provider knowledge from infrastructure work.

The final tradeoff is organizational fit. Model-based automation is most interesting when multiple teams need to coordinate changes across existing infrastructure, policy, diagrams, and operational workflows. It is less compelling for a small, stable environment where a few Terraform modules are readable and fast. Sophistication is not free. Use it when it buys clarity, safety, or collaboration that simpler tools cannot provide.

---

## 10. How to Evaluate a Model-Based Automation Platform

Start with source-of-truth questions. Where does desired state live? Can it be exported? How is it versioned? How do you review a change? Can reviewers inspect downstream effects? Can the platform explain why a derived value changed? Can you reconstruct the state of the model at the time of an incident? These questions matter more than the prettiness of the UI.

Next, test brownfield discovery. Most real organizations already have infrastructure. Ask the platform to import or discover a representative service. Inspect what it can model, what it leaves unmanaged, what it misidentifies, and how it represents provider defaults. A model-based platform that only works for greenfield demos may not help the messy estates where model-based automation is most needed.

Then evaluate policy timing. Create a deliberately unsafe configuration in a sandbox, such as public database ingress, missing ownership metadata, or absent backup retention. A useful platform should surface the problem early, explain it clearly, and guide the user toward correction. If validation appears only after apply time, the model is not using its full advantage.

Evaluate drift from both directions. Change a harmless property outside the model in a sandbox provider account, refresh or rediscover reality, and inspect how the platform represents the mismatch. Then decide whether to accept reality or enforce intent. The workflow should make the choice explicit. Silent reconciliation is dangerous because it hides whether the organization is approving drift or correcting it.

Inspect generated or queued actions before execution. A model is only safe if humans can understand what real-world operations it will perform. Look for provider calls, replacement risk, dependency order, failure handling, and audit records. If the platform says "trust me" at the exact moment it is about to mutate production, it is not mature enough for high-risk changes.

Finally, plan exit before adoption. This is not pessimism; it is platform hygiene. Ask how you would preserve the model, recreate infrastructure definitions, recover credentials, keep audit history, and continue operations if the vendor service, open-source project, or internal team changed direction. The System Initiative status snapshot makes this concrete: strong ideas can outlive a specific project, but production dependency needs a continuity plan.

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---|---|---|
| Treating the model as a prettier diagram | Users may forget that model edits can become real infrastructure actions | Teach that the model is operational state with permissions, audit, and execution semantics |
| Ignoring the current project status | Learners may confuse a concept case study with an adoption recommendation | Keep volatile facts in a dated snapshot and verify upstream before relying on any tool |
| Assuming bidirectional sync means accepting every console change | Manual drift can become normalized instead of controlled | Separate accept-reality, enforce-intent, and investigate-drift workflows |
| Hiding subscriptions from reviewers | Derived changes look surprising and reduce trust in the platform | Show source property, target property, transformation logic, and downstream action impact |
| Writing vague qualifications | Users see failures but do not know how to fix them | Return clear severity, reason, and remediation guidance for each validation result |
| Skipping exit planning | Model-specific schemas and functions become migration debt | Require export, audit retention, and fallback workflows before production dependency |
| Replacing all Git governance overnight | Security and compliance teams lose familiar controls | Map model change sets to review, approval, logging, and incident reconstruction requirements |
| Overusing the abstraction for simple estates | The platform adds complexity without meaningful coordination benefit | Use model-based automation where relationships, policy, drift, and collaboration justify it |

---

## Quiz

### Question 1

Where does System Initiative sit on the IaC spectrum, and why is it not simply another declarative template tool?

<details>
<summary>Answer</summary>

System Initiative sits at the model-based reactive end of the spectrum. Scripts encode steps, declarative tools encode desired resources, and infrastructure-from-code uses programs to generate a resource graph. System Initiative's durable concept is different: mutate a shared model of components, resources, subscriptions, functions, and change sets, then use the platform to compute downstream effects and provider actions.
</details>

### Question 2

What is the difference between intended configuration and provider-reported reality in a digital twin, and why should a platform keep both visible during drift review?

<details>
<summary>Answer</summary>

Intent is the configuration the user or platform wants. Reality is what the provider reports currently exists. Keeping both views visible lets a platform represent drift explicitly. The team can then decide whether to accept reality into intent, enforce intent against the provider, or investigate before taking action.
</details>

### Question 3

Why can reactive property propagation improve infrastructure reviews, and under what conditions can hidden subscriptions make a review harder to trust?

<details>
<summary>Answer</summary>

Reactive propagation can improve reviews because it shows downstream effects of a source change, such as dependent subnet or route values recalculating after a network property changes. It makes reviews worse when subscriptions and transformations are hidden. Reviewers need to see the source, target, transformation, and resulting provider actions.
</details>

### Question 4

In a model-based platform, what should a change set explain before anyone applies it to real infrastructure in a shared production account?

<details>
<summary>Answer</summary>

A useful change set should explain the direct edits, downstream derived changes, qualification results, provider actions to be enqueued, replacement or deletion risk, approval status, and audit context. The point is to keep exploration and simulation separate from real infrastructure execution until the team intentionally approves the change.
</details>

### Question 5

How do qualification functions support self-service infrastructure workflows without pretending that early model validation is the same as complete security?

<details>
<summary>Answer</summary>

Qualification functions give immediate feedback while users shape a proposed change. They can catch missing tags, unsafe ingress, absent backups, invalid references, or expensive choices before apply time. They are still only one layer; cloud IAM, provider policy, reviews, secrets management, monitoring, and incident response remain necessary.
</details>

### Question 6

Why is the dated landscape snapshot important for this module when the durable automation concept outlives the specific project status?

<details>
<summary>Answer</summary>

The dated snapshot prevents two errors. It avoids presenting an archived project as a current production recommendation, and it keeps volatile facts away from the durable teaching spine. Learners can study model-based automation honestly while knowing that real adoption requires fresh upstream verification.
</details>

### Question 7

What is the main lock-in risk of model-based infrastructure automation when an organization encodes schemas, subscriptions, functions, and audit history in one platform?

<details>
<summary>Answer</summary>

The main lock-in risk is not just a hosted service contract. It is the accumulated knowledge encoded in one platform's schemas, component paths, subscriptions, functions, permissions, action history, and audit model. That knowledge is valuable while the platform is healthy and expensive to migrate when it is not.
</details>

---

## Hands-On Exercise

### Task: Simulate a Reactive Infrastructure Model Locally

This exercise avoids the archived System Initiative runtime and focuses on the durable mechanism. You will run a small local simulation that models components, subscriptions, qualifications, a change set, and a provider reality value. The goal is to see how changing one intent value can propagate through a graph before any real infrastructure action exists.

### Steps

- [ ] Run the local simulation from the repository root using the project virtual environment.
- [ ] Change the `vpc_cidr` value and confirm that subnet CIDRs recalculate in the proposed change set.
- [ ] Intentionally set the SSH rule to public ingress and confirm that the qualification fails before apply.
- [ ] Change the observed provider VPC CIDR and decide whether the model should accept reality or enforce intent.

```bash
.venv/bin/python - <<'PY'
from ipaddress import ip_network


def subnet_cidr(vpc_cidr, index, new_prefix):
    network = ip_network(vpc_cidr)
    return str(list(network.subnets(new_prefix=new_prefix))[index])


def qualify_security_group(model):
    for rule in model["security_group"]["ingress"]:
        if rule["cidr"] == "0.0.0.0/0" and rule["port"] == 22:
            return {
                "result": "failure",
                "message": "SSH ingress from the public internet is not allowed.",
            }
    return {"result": "success", "message": "Security group passes baseline checks."}


head = {
    "vpc": {"intent_cidr": "10.0.0.0/16", "reality_cidr": "10.0.0.0/16"},
    "subnets": {},
    "security_group": {"ingress": [{"port": 443, "cidr": "0.0.0.0/0"}]},
}

change_set = {
    "vpc": {**head["vpc"], "intent_cidr": "10.8.0.0/16"},
    "subnets": {},
    "security_group": {"ingress": [{"port": 22, "cidr": "0.0.0.0/0"}]},
}

for index, name in enumerate(["public-a", "public-b", "private-a", "private-b"]):
    change_set["subnets"][name] = {
        "intent_cidr": subnet_cidr(change_set["vpc"]["intent_cidr"], index, 24)
    }

qualification = qualify_security_group(change_set)
drift = change_set["vpc"]["intent_cidr"] != change_set["vpc"]["reality_cidr"]

print("Proposed subnet CIDRs:")
for name, subnet in change_set["subnets"].items():
    print(f"- {name}: {subnet['intent_cidr']}")

print(f"Qualification: {qualification['result']} - {qualification['message']}")
print(f"Drift visible: {drift}")
print("Decision: fix the security group before any apply action is allowed.")
PY
```

The expected output shows four recalculated subnet CIDRs, a failed qualification for public SSH, and an explicit drift signal because the proposed intent differs from the provider-reported value stored in the model. Nothing touches a cloud account. That is the point: a change set should let you reason about propagation, validation, and drift before action execution.

### Success Criteria

- [ ] The script prints four proposed subnet CIDRs derived from the changed VPC CIDR.
- [ ] The qualification result is `failure` when SSH ingress is public.
- [ ] The drift signal is visible before any provider action is executed.
- [ ] You can explain whether you would accept reality or enforce intent for the VPC CIDR mismatch.

---

## Key Takeaways

Model-based automation changes the center of infrastructure work from files to a shared operational model. That model can represent intent, observed reality, relationships, validation results, and proposed actions in one place. The advantage is richer context for self-service, collaboration, drift handling, and policy timing. The cost is dependence on the platform's schema, execution engine, audit model, and long-term viability.

System Initiative is a useful teaching case precisely because it is ambitious and imperfect as an adoption target. The design shows how a reactive digital twin can address the glue between DevOps tools, but the archived status shows why vendor durability, export paths, and governance matter. Learn the pattern, compare it carefully, and avoid turning any one tool into a universal answer.

---

## Next Module

Continue to [Module 7.10: Nitric](../module-7.10-nitric/) to study another infrastructure abstraction that moves application intent closer to cloud resource generation while making a different set of tradeoffs.

---

## Sources

- [System Initiative docs source: What is System Initiative](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/what-is-si.md)
- [System Initiative docs source: IaC comparison](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/explanation/iac-comparison.md)
- [System Initiative docs source: Digital twin](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/explanation/architecture/digital-twin.md)
- [System Initiative docs source: Snapshot data model](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/explanation/architecture/snapshot.md)
- [System Initiative docs source: Change control](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/explanation/architecture/change-control.md)
- [System Initiative docs source: Functions architecture](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/explanation/architecture/functions.md)
- [System Initiative docs source: Change sets reference](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/reference/change-sets.md)
- [System Initiative docs source: Components reference](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/reference/components.md)
- [System Initiative docs source: Qualification reference](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/reference/qualification.md)
- [System Initiative docs source: Code generation reference](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/reference/code-generation.md)
- [System Initiative docs source: Actions reference](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/reference/actions.md)
- [System Initiative docs source: CLI reference](https://raw.githubusercontent.com/systeminit/si/main/app/docs/src/reference/si-cli.md)
- [systeminit/si GitHub repository](https://github.com/systeminit/si)
- [GitHub API metadata for systeminit/si](https://api.github.com/repos/systeminit/si)
- [Final archive commit for systeminit/si](https://github.com/systeminit/si/commit/b4f83f5e93ed5c9e78edb67670ba39c3662895f6)
- [The New Stack: System Initiative Code Now Open Source](https://thenewstack.io/system-initiative-code-now-open-source/)
- [Runtime News: Meet System Initiative](https://www.runtime.news/meet-system-initiative-a-new-devops-tool-from-adam-jacob/)
