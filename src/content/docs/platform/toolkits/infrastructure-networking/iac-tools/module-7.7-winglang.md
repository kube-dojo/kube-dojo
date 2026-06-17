---
revision_pending: false
title: "Module 7.7: Wing - The Cloud-Oriented Programming Language"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.7-winglang
sidebar:
  order: 8
---

## Complexity: [COMPLEX]

## Time to Complete: 50-55 minutes

---

## Prerequisites

Before starting this module, you should have completed [Module 7.1: Terraform](../module-7.1-terraform/) for declarative provisioning concepts, [Module 7.3: Pulumi](../module-7.3-pulumi/) for infrastructure expressed in general-purpose languages, and [Module 7.10: Nitric](../module-7.10-nitric/) if you want a sibling comparison for application-centric cloud frameworks. You should be comfortable reading small programs in any C-like syntax, understand basic serverless primitives such as object storage, queues, and HTTP APIs, and have seen at least one IAM permission error in a cloud deployment. Distributed systems vocabulary from the [Distributed Systems Foundation](/platform/foundations/distributed-systems/) track helps when reasoning about event-driven workflows and least-privilege access.

This module is a tool-specific deep dive. The durable concepts live on the infrastructure-from-code spectrum; Wing is one peer implementation of that idea, not a universal replacement for every platform problem.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Deploy cloud applications using Wing's cloud-oriented programming model with local simulation**
- **Implement Wing preflight and inflight code patterns for compile-time infrastructure and runtime logic**
- **Configure Wing's platform providers to target AWS, Azure, GCP, or Kubernetes from a single codebase**
- **Evaluate Wing's unified cloud abstraction against traditional IaC tools for full-stack cloud development**

---

## Why This Module Matters

Most serverless teams eventually discover the same structural pain: application logic lives in one repository area, infrastructure templates live in another, IAM policies live in a third, and tests mock cloud services in a fourth. Each layer is reasonable on its own, yet together they create a synchronization problem that no amount of code review fully eliminates. A handler starts calling a new queue on Tuesday, the Terraform change lands on Thursday, and production breaks on Friday because the execution role still reflects Monday's world.

**Hypothetical scenario:** A payments team ships a webhook handler that validates signatures, writes to a key-value store, enqueues work, and publishes error notifications. The TypeScript handler is clear, the Terraform module is readable, and staging tests pass because staging IAM was updated manually during debugging. Production fails with `AccessDenied` on the first real traffic spike because the queue was added in application code before the role policy caught up. The incident is not mysterious once you diagram dependencies, but the team paid for a category of defect that declaratively separate repos almost invite.

Wing matters because it attacks that synchronization problem at the language level rather than at the process level. In Wing, declaring a bucket, wiring an event consumer, and writing the consumer body can live in one program with an explicit compile-time versus runtime boundary. The compiler synthesizes provisioning artifacts such as Terraform JSON and bundles inflight logic for cloud compute platforms, while a local simulator lets you exercise the same program without cloud credentials. This module teaches that model as engineering tradeoffs, not as hype: you will learn where unified cloud languages reduce glue work, where they introduce a new language to learn, and how to decide whether that exchange fits your team.

Platform leaders often ask whether Wing replaces Terraform or replaces application languages. The durable answer is neither: Wing replaces the *glue layer* between them for teams whose pain is synchronized change across those layers. Terraform remains the reconciliation engine for many deployments; JavaScript remains the inflight runtime today; TypeScript or Python may still exist in adjacent services your Wing functions call. Successful adoptions draw boundaries instead of declaring rip-and-replace mandates. Let Wing own tightly coupled serverless features; let existing Terraform modules continue serving shared VPCs, DNS zones, and audit logging buckets until there is a concrete reason to migrate.

Learners coming from Pulumi or CDK should notice what changes in code review culture. Pulumi diffs mix language refactors with resource graph changes; reviewers must infer which lines affect state. Wing diffs still require that inference, but phase errors fail earlier at compile time instead of appearing as surprising plan entries. Learners coming from Terraform should notice they gain runtime wiring clarity but accept a new syntax and toolchain. Everyone should leave this module able to explain *why* a unified model helps IAM synchronization without claiming unified models eliminate operations.

> **The Two-Phase Kitchen Analogy**
>
> Think of preflight as writing the kitchen blueprint and installing fixed equipment before opening night, and inflight as the service shift where cooks follow recipes using that equipment. You do not rebuild the stove during dinner rush, and you do not serve customers while pouring concrete for a new wall. Wing's compiler enforces that separation so infrastructure mutations stay in the blueprint phase while business logic runs in the service phase.

---

## 1. Where Wing Sits on the IaC Spectrum

Infrastructure automation did not arrive fully formed. Teams progressed from imperative scripts that SSHed into servers and ran shell commands, toward declarative templates that describe desired state and rely on a planner to reconcile reality, and more recently toward models where application code and infrastructure declarations share a toolchain. Each step solved a real problem and introduced a new abstraction cost. Understanding that progression is the durable spine of this module; Wing is one point on the line, not the line itself.

Imperative scripts remain valuable for bootstrapping and odd one-off tasks, but they struggle at scale because execution order becomes the documentation. Declarative IaC tools such as Terraform and OpenTofu invert that relationship: you publish desired resources and relationships, the engine builds a graph, and apply operations walk the graph safely. That model excels at data-center-style provisioning where the primary artifact is infrastructure shape rather than application behavior. It becomes awkward when the hardest logic is runtime coupling between services, especially when permissions must track fine-grained application usage rather than coarse resource lists.

Infrastructure-from-application-code tools push further. Pulumi lets you register cloud resources using TypeScript, Python, Go, or other languages while preserving a declarative plan/apply cycle backed by state. AWS CDK generates CloudFormation from familiar languages but optimizes for AWS-shaped deployments. Nitric and Wing both target full-stack cloud applications, yet they make different bets: Nitric keeps your source language and analyzes SDK calls; Wing introduces a dedicated cloud-oriented language with explicit execution phases. Neither eliminates operations work such as secret rotation, observability, or rollback discipline; they change where you express intent and how tightly infrastructure, permissions, and runtime code are coupled.

Wing's distinctive choice is the **preflight versus inflight** split enforced by the compiler. Preflight code runs during compilation and emits infrastructure configuration consumed by engines like Terraform or CloudFormation. Inflight code runs in cloud compute environments after deployment and implements request handlers, queue consumers, and scheduled jobs. Because both phases live in one language, the compiler can trace which inflight operations touch which preflight resources and synthesize least-privilege bindings instead of relying on a human to maintain parallel IAM documents.

That design targets teams building event-driven and API-centric cloud applications where permission drift between handler and template is a recurring incident category. It is a weaker default fit for large static topologies maintained by a central platform team that rarely co-changes application code, or for organizations that standardize on Kubernetes controllers as the primary reconciliation loop. The evaluation question is workload shape, not slogan comparison.

Cross-reference [Module 7.1: Terraform](../module-7.1-terraform/) when reasoning about state files and drift. Wing often emits Terraform JSON for AWS deployments, which means Terraform state still anchors reality even though Wing authored the configuration. Cross-reference [Module 7.3: Pulumi](../module-7.3-pulumi/) when comparing language-native IaC that keeps general-purpose syntax versus Wing's phase-aware cloud language. Cross-reference [Module 7.10: Nitric](../module-7.10-nitric/) when comparing application frameworks that infer infrastructure from SDK usage in TypeScript or Python rather than from a dedicated `.w` program.

Pause and predict: if a developer adds `bucket.put(...)` inside an inflight function, should Wing generate read or write IAM permissions for the corresponding Lambda role? The compiler qualifies lifts based on inflight API usage, so a `put` implies write access rather than a blanket `s3:*` policy. That behavior is the core value proposition—and also a place where implicit magic can surprise reviewers who expect explicit policy documents.

---

## 2. Landscape Snapshot — as of 2026-06

> **Landscape snapshot — as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**

| Topic | Snapshot | Verify at |
|---|---|---|
| Maintaining organization | Open-source repo `winglang/wing` (created by Elad Ben-Israel, of AWS CDK). **Note:** Wing Cloud — the company behind it — wound down its commercial operation in 2025; the repo is not archived but community-maintained. | [Who is behind Wing](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/030-who-is-behind-wing.md); [The New Stack (2025)](https://thenewstack.io/wing-the-startup-failed-but-the-language-has-potential/) |
| Open-source license | Language specification, toolchain, and local simulator under MIT license per upstream FAQ | [Who is behind Wing](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/030-who-is-behind-wing.md) |
| CLI package line | `winglang` npm package; verify latest patch before pinning CI | [npm registry](https://registry.npmjs.org/winglang/latest) |
| Project maturity | Pre-1.0; latest release **v0.85.49 (2025-02-03)** — development has largely stalled since 2025 after Wing Cloud wound down. Verify activity before adopting. | [Wing releases](https://github.com/winglang/wing/releases) |
| AWS support | Described as fully supported for simulator-compilable programs via Terraform engine | [Supported clouds FAQ](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/020-supported-clouds-services-and-engines/021-supported-clouds.md) |
| GCP / Azure support | Partial support; not all simulator-valid programs compile to every cloud yet | [Supported clouds FAQ](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/020-supported-clouds-services-and-engines/021-supported-clouds.md) |
| Primary compile targets | Terraform JSON for cloud providers; JavaScript bundles for inflight hosts; local `sim` target | [Preflight and inflight docs](https://github.com/winglang/wing/blob/main/docs/docs/02-concepts/01-preflight-and-inflight.md) |
| Local development | `wing it` compiles to simulator target and opens Wing Console with hot reload | [Run locally guide](https://github.com/winglang/wing/blob/main/docs/docs/01-start-here/04-run-locally.md) |

The durable takeaway is structural: Wing couples a dedicated language, a compile-time infrastructure phase, a runtime phase, Terraform-oriented synthesis for provisioning, and a built-in simulator for fast feedback. Version numbers, partial cloud parity, and commercial offerings around Wing Console should be confirmed in upstream documentation rather than memorized from this table.

---

## 3. Capability Rosetta: Wing, Terraform, Pulumi, and Nitric

Compare tools by capability and tradeoff, not by popularity narratives. The row owns the question; each column describes how that tool answers it today.

| Capability | Wing | Terraform / OpenTofu | Pulumi | Nitric |
|---|---|---|---|---|
| Abstraction model | Dedicated cloud-oriented language with explicit preflight/inflight phases | Declarative HCL configuration describing desired resources | General-purpose languages registering resources with Pulumi engine | Application SDK in TypeScript/Python/Go/Dart; providers synthesize infra |
| Language / syntax | Wing (`.w` files) | HCL + expressions | TypeScript, Python, Go, C#, Java, YAML | Existing languages via Nitric SDK |
| Compiles / synthesizes to | Terraform JSON, CloudFormation paths, JavaScript inflight bundles | Native Terraform plan/apply (or OpenTofu) | Pulumi engine driving provider plugins | Provider-generated Pulumi/Terraform/etc. per target |
| State management | Delegated to underlying engine (commonly Terraform state for AWS) | Terraform/OpenTofu state backends | Pulumi stack state in Pulumi Cloud or DIY backend | Provider-managed; varies by deployment target |
| Target clouds | AWS most complete; GCP/Azure partial; extensibility via CDKTF imports per FAQ | Broad provider ecosystem via Terraform providers | Broad via bridged providers | AWS, Azure, GCP via pluggable providers |
| Drift handling | Depends on chosen provisioning engine; Wing does not replace Terraform drift detection | Plan/refresh against state | Preview/refresh against stack state | Provider-specific reconciliation |
| Primary use case | Unified full-stack cloud apps with compile-time infra + runtime in one program | Platform provisioning, modules, multi-team foundations | Language-native IaC with rich logic in real code | Portable cloud app framework with SDK-defined resources |
| License / governance | MIT toolchain; community-maintained after Wing Cloud (commercial) wound down in 2025; pre-1.0 | BSL-licensed Terraform (OpenTofu MPL fork) | Apache-2.0 engine + commercial Pulumi Cloud | Apache-2.0 SDK; Nitric Technologies stewardship |

When this table steers a decision, write scenarios instead of picking a winner. If your pain is IAM drift between Lambda code and Terraform roles, Wing or Nitric merit evaluation because both tie permissions to program structure. If your pain is curating reusable modules for hundreds of teams, Terraform or OpenTofu module registries may matter more than application-language unification. If your team already invested heavily in TypeScript Pulumi components, Wing's new syntax is a migration cost that must be justified by simulator ergonomics or compiler-enforced phase boundaries rather than by slogans.

Walk through a concrete evaluation pattern platform teams use successfully. First, list the last three production incidents caused by configuration skew between application code and infrastructure templates. If at least two involve IAM or missing bindings, unified authoring tools belong on the short list. Second, identify whether your deployment unit is an application feature or a shared platform module; Wing-shaped workflows align with feature teams shipping endpoints and consumers, while central platform teams often continue publishing Terraform modules consumed by many services. Third, estimate onboarding cost honestly: a new language is not insurmountable when programs stay small and the simulator provides immediate feedback, but it is expensive when every engineer must simultaneously learn Wing, generated Terraform review, and cloud-specific edge cases. Fourth, run a time-boxed spike that compiles the same tiny API to simulator and AWS Terraform targets, then compare plan output readability with your existing module patterns. The spike should produce a written decision memo with explicit reject criteria, not a slide claiming victory because demo day felt fast.

Terraform remains the declarative baseline in this Rosetta because it defines the reconciliation vocabulary many organizations already operationalized: plan, apply, state, modules, and workspaces or equivalent isolation. OpenTofu enters the same column when teams require fully open-source licensing without changing the mental model. When Wing emits Terraform JSON, you are not escaping that vocabulary—you are generating it from a higher-level program. That is powerful when application developers should not hand-edit HCL, and fragile when platform engineers lose visibility because generated output becomes opaque. Healthy adoption keeps Terraform plans in CI with human-readable diffs and treats Wing source as the editable truth while generated JSON remains an artifact.

Pulumi occupies the adjacent cell for teams that refuse a new syntax but want loops, classes, and package ecosystems inside IaC. The tradeoff is phase ambiguity: nothing in TypeScript stops you from mixing resource registration with runtime side effects unless your team enforces conventions and entrypoint structure. Wing pays syntax cost to buy compiler enforcement. Nitric occupies the application-framework cell: you keep TypeScript or Python, declare resources through SDK objects, and let providers synthesize infrastructure. Nitric's `.allow()` declarations parallel Wing's lift qualifications; both attempt to derive permissions from code structure rather than from parallel IAM files. Choose Nitric when language continuity dominates; choose Wing when phase separation and simulator-first development dominate.

CDK and Bicep deserve mention even when they are not Rosetta columns because many readers arrive from AWS-centric shops. CDK generates CloudFormation, which makes it excellent when change sets, stack policies, and AWS service coverage through CloudFormation are non-negotiable. Wing's Terraform path targets organizations standardized on Terraform backends and provider ecosystems instead. Neither story is universally superior; they differ in provisioning engine, cloud focus, and where application code lives relative to infrastructure declarations. Keep comparisons at that capability layer and resist ranking tools by star counts or conference mentions—those signals churn quarterly and teach learners the wrong habit.

---

## 4. Preflight and Inflight: Wing's Core Model

Wing programs begin in **preflight**, the default execution phase. Preflight code runs during compilation, defines cloud resources such as buckets, queues, APIs, and functions, and emits infrastructure configuration for a provisioning engine. You do not annotate preflight explicitly; creating `new cloud.Bucket()` in the top-level program is already an infrastructure declaration. Preflight can also perform compile-time validation: `assert()` failures abort compilation, and `log()` prints diagnostics during compile, which turns some categories of mistakes into build failures instead of deployment surprises.

**Inflight** code runs after deployment inside compute hosts such as AWS Lambda, containers, or other environments Wing targets. Inflight blocks are marked with the `inflight` keyword and may call inflight APIs on cloud resources, such as `bucket.put` or `queue.push`. Inflight functions must be passed to preflight APIs that expect runtime handlers—`cloud.Function`, `queue.setConsumer`, `api.get`, and similar wiring points—so the compiler knows which host needs which bundle and permissions.

The boundary rules are strict for good reason. Inflight code cannot create new preflight resources, cannot call preflight mutators like `bucket.addObject` at runtime, and cannot invoke inflight handlers during compilation. Preflight code cannot directly execute inflight functions. These restrictions encode a safety invariant: infrastructure shape is fixed at deploy time, while business logic executes later under that shape. When teams violate similar boundaries manually across repos, the failure mode is subtle drift; when Wing violates them, compilation fails loudly.

Bridging phases uses **lifting**. Preflight values referenced inside inflight closures are lifted into the runtime environment, and the compiler analyzes which inflight methods are used to derive least-privilege qualifications. If you call `bucket.put` inside a function, the compiler associates write access with that bucket for the inflight host. When analysis cannot determine which resource handles flow through conditional logic, Wing may require an explicit `lift` block listing allowed methods—a sharp tool that documents intent for reviewers and prevents silent over-permissioning.

```
WING COMPILATION MODEL
─────────────────────────────────────────────────────────────────

Source Code:
┌─────────────────────────────────────────────────────────────────┐
│ bring cloud;                                                     │
│                                                                  │
│ let bucket = new cloud.Bucket();        // Preflight (infra)    │
│ let queue = new cloud.Queue();          // Preflight (infra)    │
│                                                                  │
│ queue.setConsumer(inflight (msg: str) => {  // Inflight (app)  │
│   bucket.put("processed/${msg}", processData(msg));             │
│ });                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Wing Compiler
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│   PREFLIGHT OUTPUT       │           │   INFLIGHT OUTPUT        │
│   (Infrastructure)       │           │   (Application)          │
├─────────────────────────┤           ├─────────────────────────┤
│ Terraform JSON / other   │           │ JavaScript bundle for    │
│ provisioning artifacts   │           │ Lambda and inflight hosts│
│ plus IAM/policy wiring   │           │ with env bindings        │
└─────────────────────────┘           └─────────────────────────┘
```

Classes group preflight and inflight members in one abstraction, which is how larger Wing programs stay readable. A preflight class can expose inflight methods and accept inflight callbacks in preflight methods like `setConsumer`. Inflight classes exist too, but only contain inflight members and are safe to instantiate at runtime. Preflight data referenced inflight is immutable: reassignment and mutating collections are rejected, which prevents runtime code from silently changing compile-time topology.

Senior engineers reading Wing diffs should ask the same questions they ask of Terraform and application PRs combined: Does this change alter infrastructure shape or only runtime behavior? Did a new inflight API call imply broader IAM than reviewers expect? Did someone bypass the model with raw CDKTF imports for a one-off resource? Wing reduces glue code, but it does not remove architectural judgment.

Preflight methods that accept inflight callbacks—such as `queue.setConsumer` or `bucket.onCreate`—are the wiring fabric of Wing applications. They tell the compiler which runtime entrypoints exist and which resources each entrypoint may touch. When you refactor by moving a handler from one queue to another, you are changing infrastructure bindings, not merely relocating a function file on disk. That is why simulator validation plus Terraform plan review still matter: the program semantics changed even if the inflight body text stayed identical.

Inflight hosts are the runtime environments where compiled JavaScript executes. AWS Lambda is the common example today, yet upstream documentation describes containers, virtual machines, and other hosts as part of the longer-term model. Preflight classes may implement `onLift` hooks to attach host-specific requirements when lifted operations demand extra configuration—policy statements on Lambda roles, environment variables, or network settings depending on host type. You typically do not call `onLift` directly; the compiler invokes it based on qualified operations. Extension authors and advanced teams care deeply about `onLift`; application developers should still know it exists so custom resources do not feel like unexplained magic when policies appear in generated Terraform.

Study a permission-focused example mentally. Suppose an inflight handler reads from one bucket and writes to another. The compiler should qualify read on the source and write on the destination rather than granting `s3:*` on both. Reviewers validating generated plans should see that separation. If plans look overly broad, inspect whether conditional logic forced a conservative `lift` block or whether a custom resource bypassed qualification logic. Least privilege is a process outcome; Wing automates much of the bookkeeping but not the human decision about whether a handler should have access at all.

Mutable versus immutable data crossing the boundary catches many first-time authors. Preflight variables referenced inflight are read-only; mutable arrays become immutable views inflight. That design prevents runtime code from altering compile-time topology indirectly by mutating shared structures. When learners complain the compiler is pedantic, translate the error into the incident it prevents: a handler that appends to a shared preflight list could otherwise imply dynamic infrastructure changes without a planned deployment. The pedantry is the point.

Testing benefits from the same clarity. Preflight assertions turn invalid configuration into compile failures. Inflight tests executed via `wing test` hit simulated resources, which means integration tests often require fewer bespoke mocks than equivalent TypeScript/Jest setups against raw AWS SDK clients. Keep tests focused: validate business rules and boundary conditions in inflight tests, validate infrastructure wiring by compilation to your target platform, and validate cloud-specific behavior in staged accounts when simulator fidelity is insufficient.

---

## 5. Compilation, Provisioning, and State

Wing is not a replacement for every provisioning engine; it is a front end that emits artifacts those engines apply. For AWS Terraform targets, `wing compile` produces JSON configuration and bundled function code you can inspect before any cloud mutation occurs. That inspectability matters for platform teams who require Terraform plan review in CI even when application developers author Wing source. Treat generated files as build outputs: reproducible from source, reviewable in pull requests, and disposable if corrupted.

State and drift stories inherit from the chosen backend. If Terraform applies Wing output, Terraform state remains the source of truth for resource identities. Drift detection still means refresh/plan workflows against live APIs. Wing's unified source reduces the chance that application changes and IAM changes diverge because they were authored separately, but it cannot prevent operators from editing resources in a console without updating source. Operational discipline still applies.

Installation follows the Node ecosystem today:

```bash
# Install Wing CLI (verify latest version in npm registry before pinning)
npm install -g winglang

# Verify installation
wing --version

# Bootstrap a new project
mkdir wing-demo && cd wing-demo
wing new empty
```

A minimal program demonstrates both phases:

```wing
// main.w
bring cloud;

// Preflight: create a bucket
let bucket = new cloud.Bucket();

// Preflight: wire a function that uses the bucket at runtime
new cloud.Function(inflight () => {
  bucket.put("hello.txt", "Hello from Wing!");
  let content = bucket.get("hello.txt");
  log("Content: ${content}");
}) as "greeter";
```

Compile before apply remains essential. Generated Terraform must be initialized and planned like any other Terraform workflow. Skipping compile and editing generated JSON manually defeats the purpose of single-source authoring and reintroduces the drift Wing tries to remove.

Treat compilation outputs as a contract between application and platform teams. Application developers own `.w` source and inflight logic; platform teams may own remote state backends, provider version pins, and guardrails around which AWS accounts accept applies. A practical CI pipeline runs `wing compile` on every pull request, archives generated Terraform as a build artifact, runs `terraform plan` against a dedicated validation account, and blocks merge when plans show unexpected replacements or broad policy changes. Production applies should originate from the same artifact hash promoted through environments rather than from ad hoc laptop compiles that nobody else can reproduce.

Version pinning deserves explicit policy because Wing is pre-release. Record the `winglang` npm version in package lockfiles or container images used by CI, and upgrade intentionally after reading release notes. Pair Wing CLI upgrades with Terraform provider upgrades carefully; generated JSON may assume provider schemas that changed between versions. If plan diffs explode after an upgrade, roll forward with a focused migration branch instead of mutating production state under time pressure.

Secrets and configuration split across phases the same way other tools separate build-time and runtime configuration. Preflight can reference secrets that become environment bindings for inflight hosts, but secret rotation and auditing remain operational tasks. Do not assume unified language eliminates secret sprawl; it consolidates wiring while you still choose vaults, rotation cadence, and break-glass access patterns. Document which secrets are compile-time constants versus runtime lookups so reviewers understand blast radius when a secret changes.

When things fail, triage along the pipeline: compiler errors are source or phase violations; Terraform plan errors are provider, quota, or policy constraints; runtime errors are inflight logic or external dependencies. Keeping that separation visible in runbooks prevents teams from randomly editing generated JSON when the fix belongs in inflight code, or rewriting handlers when the fix belongs in Terraform provider configuration. The unified source file does not merge those failure domains—it merges authorship.

---

## 6. Local Simulation with `wing it`

Wing's simulator target exists because cloud feedback loops are expensive in both time and money. Running `wing it main.w` compiles your program to the `sim` platform and opens the Wing Console, a local web UI for interacting with simulated buckets, queues, functions, and related resources. Hot reload recompiles on save, which makes exploratory development closer to application server workflows than to traditional IaC edit-plan-apply cycles for every small change.

```bash
# Run in local simulator and open Wing Console
wing it main.w

# Compile to Terraform for AWS
wing compile main.w --target tf-aws

# Inspect output directory under target/ before terraform apply
```

The simulator is not a perfect stand-in for every cloud edge case. Service limits, eventual consistency quirks, and provider-specific IAM semantics may differ. It is still valuable for integration-style tests that exercise real control flow across multiple resources without mocking every SDK call. Wing's testing model runs tests against simulated resources via `wing test`, which complements unit-style assertions for pure functions.

When teaching new contributors, emphasize a habit loop: express intent in Wing, run locally in the console, add tests for regressions, compile to the target platform, then run Terraform plan in a non-production account. That loop keeps the leaky abstraction risk visible early instead of hiding surprises until production traffic arrives.

Wing Console is more than a demo UI. The map view shows how queues, buckets, functions, and counters connect, which helps newcomers see event flow that would otherwise be scattered across YAML and code. Resource interaction panels let you push queue messages, inspect bucket objects, invoke functions, and reset counters without writing one-off curl scripts against half-configured endpoints. Hot reload means you edit `main.w`, save, and watch the map update—a feedback rhythm closer to web development than to classical IaC cycles. Teach teams to reproduce bugs starting in the console before they jump to cloud logs; when the bug appears only after deploy, you have strong evidence of provider or environment divergence rather than logic errors.

Simulator fidelity questions should be documented per service your application uses. Storage and messaging primitives often behave well locally; exotic API Gateway authorizer combinations or regional edge cases may not. Maintain a short team checklist of scenarios validated in simulator versus scenarios that require staged cloud tests. That checklist ages better than tribal knowledge in chat threads and prevents false confidence when demos always run locally but production traffic hits real IAM boundaries.

---

## 7. Building APIs and Event-Driven Workflows

The image-processing pipeline below shows how preflight wiring and inflight handlers cooperate in an event-driven design. Preflight declares buckets, a queue, and a topic; inflight functions react to uploads and queue messages; permissions and environment bindings are derived from usage rather than hand-maintained side files.

```wing
// image-processor.w
bring cloud;
bring util;

let uploadBucket = new cloud.Bucket() as "uploads";
let processedBucket = new cloud.Bucket() as "processed";
let notificationTopic = new cloud.Topic() as "notifications";
let processingQueue = new cloud.Queue() as "processing-queue";

uploadBucket.onCreate(inflight (key: str) => {
  log("New upload: ${key}");
  processingQueue.push(key);
});

processingQueue.setConsumer(inflight (message: str) => {
  let key = message;
  let original = uploadBucket.get(key);
  let processed = processImage(original);
  let processedKey = "processed-${key}";
  processedBucket.put(processedKey, processed);
  notificationTopic.publish(Json.stringify({
    original: key,
    processed: processedKey,
    timestamp: util.datetime.now()
  }));
});

inflight fn processImage(content: str): str {
  return "PROCESSED:${content}";
}
```

HTTP APIs follow the same pattern: preflight constructs `cloud.Api`, inflight handlers receive typed requests, and preflight fields like `api.url` can be referenced inflight when immutable configuration is needed for smoke tests or internal callbacks.

```wing
bring cloud;

let api = new cloud.Api();
let users = new cloud.Bucket();

api.get("/users/{id}", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let id = req.vars.get("id");
  try {
    let user = users.get("user-${id}");
    return cloud.ApiResponse { status: 200, body: user };
  } catch {
    return cloud.ApiResponse {
      status: 404,
      body: Json.stringify({ error: "User not found" })
    };
  }
});
```

Before copying examples into production services, validate input aggressively, add authentication at the API edge, and confirm compiled targets support every standard-library resource you use. Partial cloud support means a program that simulates cleanly may still fail compilation for Azure or GCP until provider coverage catches up—another reason the dated snapshot table exists.

Read the image processor pipeline as a narrative, not only as syntax. An upload triggers `onCreate`, which enqueues work rather than processing synchronously—a classic decoupling choice that protects upload latency from heavy computation. The queue consumer performs transformation and writes to a second bucket, which preserves raw inputs for replay and audit. The topic publishes a structured notification for downstream subscribers who may not care about storage internals. Each arrow corresponds to preflight wiring; each handler body is inflight. When requirements change—perhaps virus scanning before enqueue—you know whether you are editing topology (preflight) or algorithm (inflight) before you open the file.

For HTTP APIs, treat `cloud.ApiRequest` and `cloud.ApiResponse` types as contracts that encode common serverless patterns: path variables, headers, status codes, and JSON bodies. That consistency reduces bespoke API Gateway mapping templates scattered in Terraform modules. Authentication and authorization still belong in your design: Wing does not remove the need to validate tokens, enforce tenancy, or rate-limit abusive clients. Place auth early inflight, fail closed, and keep secrets out of logs even when `log()` is convenient during development.

Event-driven designs accumulate failure modes: poison messages, partial writes, duplicate deliveries, and downstream timeouts. Wing gives you wiring; you still implement idempotency keys, dead-letter handling, and retry policies appropriate to your business. Simulator runs help you practice happy paths quickly, but staged cloud tests should deliberately inject duplicate queue messages and slow consumers to observe behavior. Unified language does not automatically create reliable distributed systems—it removes one category of misconfiguration so you can spend attention on the harder problems.

---

## 8. Wing Standard Library and Portable Resources

Wing ships a standard library centered on portable cloud abstractions—`cloud.Bucket`, `cloud.Queue`, `cloud.Topic`, `cloud.Function`, `cloud.Api`, `cloud.Counter`, `cloud.Table`, `cloud.Schedule`, and `cloud.Secret` map to provider-specific services when compiled. That portability is intentional: application logic references stable types while platform targets supply concrete implementations. Portability is not magic; upstream FAQs explicitly warn that AWS is ahead of GCP and Azure in coverage, and compatibility matrices should be consulted before promising multi-cloud deployments to stakeholders.

Supporting modules cover everyday programming tasks without pulling arbitrary npm dependencies inflight unless you choose to. `bring http` enables inflight HTTP calls; `bring util` exposes time and UUID helpers; `bring expect` supports tests. Keeping inflight bundles small still matters for cold starts on function hosts even when Wing packages code for you. Heavy image processing libraries belong behind deliberate bundling choices with size review, not accidental imports copied from Node tutorials.

When portable types are insufficient, Wing documents escape hatches such as importing CDKTF libraries for Terraform provider resources not yet modeled in the Wing SDK. Escape hatches are power tools: they break uniform lift qualification unless wrapped carefully, and they reintroduce provider-specific knowledge platform teams hoped to hide. Wrap provider-specific resources in preflight classes with clear inflight interfaces so application code stays readable and reviewers can see boundaries.

Naming resources with `as "logical-name"` improves console maps and generated Terraform readability. Logical names become anchors for humans debugging across simulator and cloud environments. Invest in consistent naming conventions the same way you would for Terraform module instance names or Kubernetes labels: future you is also a teammate reading diffs under incident pressure.

---

## 9. Tradeoffs and Decision Framework

Wing trades a new language and toolchain for tighter coupling between infrastructure shape, permissions, and runtime logic. That trade is worthwhile when your team repeatedly pays integration tax across TypeScript handlers, Terraform modules, IAM snippets, and mocked tests, and when event-driven or API-centric workloads dominate the roadmap. The trade is costly when your organization already standardized on general-purpose IaC languages with mature component libraries, or when platform engineering owns static foundations that change slowly while application teams deploy frequently into shared accounts.

**Leaky abstraction risk** appears whenever a unified model hides provider limits. Simulator success does not guarantee multi-cloud parity. Explicit `lift` blocks and CDKTF escape hatches are signs that pure abstraction failed—use them deliberately and document why. **Debuggability** shifts: instead of reading a standalone Terraform plan and a separate stack trace, engineers read compiler diagnostics, generated Terraform JSON, and runtime logs together. Teams need literacy in both layers.

**Ecosystem youth** is real. Pre-release status means APIs, resource coverage, and compile targets can change between versions. Pin CLI versions in CI, read release notes, and treat upgrades as semver-sensitive events even when the language feels young. **Vendor stewardship is the central risk.** Wing Cloud — the company behind Wing — wound down its commercial operation in 2025 (per The New Stack), and the language has had no release since v0.85.49 in early 2025. The open-source repository remains but is dormant. Treat Wing as the clearest *illustration of the preflight/inflight, infrastructure-from-code model* rather than a production bet, and verify current project activity before adopting.

Choose Wing when unified simulation, compile-time IAM derivation, and single-program authoring address your dominant failure modes. Defer or decline when Kubernetes-first delivery, fine-grained Terraform module reuse, or strict multi-cloud parity on day one drive requirements. Many enterprises run multiple tools deliberately: Terraform for foundations, Wing or Nitric for application edges, Ansible for instance configuration. The mature decision names boundaries instead of declaring single-tool victory.

Use a written scorecard before adoption. Score integration pain, IAM incident frequency, team language familiarity, cloud target maturity, and required multi-cloud parity on a simple rubric. Weight criteria by incident cost, not by enthusiasm for new syntax. Revisit the scorecard quarterly while Wing matures because partial cloud support and CLI changes can shift answers faster than Terraform module ecosystems evolve. If the scorecard says defer, document reject criteria so the question becomes data-driven later instead of relitigated from memory in every architecture forum.

Communicate honestly with security reviewers. Generated IAM may be correct while still too broad for your org standards if lift analysis conservatively bundles permissions. Reviewers should treat Wing like any generator: trust but verify plans, demand justification for escape hatches, and require staged rollout with canary accounts. Security wins when permissions trace to code operations; security fails when teams assume compiler output is automatically minimal without reading the plan.

Communicate honestly with finops stakeholders. Simulator-first development can reduce stray cloud spend from experimental deploys, but production cost governance still requires tags, budgets, and lifecycle policies. Wing does not automatically tag resources for chargeback unless you implement tagging patterns in preflight configuration compatible with your target engine. Finops cares about outcomes—who pays for orphaned buckets—not about which language created them.

---

## Hypothetical scenario: From Many Files to One Program

**Hypothetical scenario:** A fintech team maintains a webhook service spread across TypeScript handlers, Terraform modules, IAM templates, Jest mocks, and deployment scripts. Each change touching a new downstream resource requires coordinated edits in at least two pull requests. Onboarding engineers must learn three mental models before shipping a safe feature.

A Wing-shaped rewrite consolidates infrastructure declarations, handler wiring, and runtime logic into one `.w` file (plus tests), with the compiler generating Terraform and bundles. Local simulation removes mock-heavy test setup for many integration paths, though teams still write explicit tests for business rules and abuse cases. The rewrite does not magically delete operational requirements: secrets management, observability, rate limiting, and data retention policies remain engineering work.

The lesson is categorical, not a fabricated ROI spreadsheet. Separate repos for tightly coupled concerns create synchronization defects; unified languages reduce those defects by construction when phase rules are respected. Whether that reduction justifies learning Wing depends on incident history, team skills, and cloud target maturity—not on invented percentage improvements.

---

## Did You Know?

- **Preflight is Wing's implicit default phase** — Programs start in preflight unless code enters an `inflight` block, which mirrors how cloud applications begin as architecture definitions before runtime handlers exist ([preflight and inflight docs](https://github.com/winglang/wing/blob/main/docs/docs/02-concepts/01-preflight-and-inflight.md)).
- **Lift qualification drives least-privilege IAM** — When inflight code calls methods such as `bucket.put`, the compiler qualifies lifted resources with those operations to generate narrower permissions instead of wildcard policies ([preflight and inflight docs](https://github.com/winglang/wing/blob/main/docs/docs/02-concepts/01-preflight-and-inflight.md)).
- **Inflight handlers compile to JavaScript today** — Runtime code targets Node.js-compatible environments, while provisioning output depends on the selected platform target ([README](https://raw.githubusercontent.com/winglang/wing/main/README.md)).
- **The toolchain and simulator are MIT-licensed** — Upstream FAQ states the language specification, toolchain, and local simulator remain free to use under MIT ([who is behind Wing](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/030-who-is-behind-wing.md)).

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Mixing preflight and inflight operations | Compilation fails or hides unsafe runtime infra mutations | Keep resource creation in preflight; use inflight APIs like `put` and `push` at runtime |
| Skipping the simulator | Slow feedback and surprise failures late in Terraform apply | Default to `wing it` for integration exploration before cloud deploys |
| Fighting abstractions with ad hoc escape hatches | Leaky patches bypass compiler IAM analysis | Use documented `lift` blocks or CDKTF imports intentionally with review |
| Deploying without inspecting compiled Terraform | Generated JSON errors become production incidents | Always compile, then run `terraform plan` in CI and non-prod accounts |
| Ignoring Wing Console during debugging | Harder to see resource interactions and message flow | Use console map and resource panels while developing locally |
| Assuming simulator parity on every cloud | Partial GCP/Azure support means compile failures or runtime gaps | Check supported clouds/services docs before promising multi-cloud |
| Large inflight bundles without review | Cold starts and deployment sizes grow silently | Keep handlers focused; factor shared inflight logic deliberately |
| Treating Wing as eliminating Terraform operations | State, drift, and backend policy remain Terraform concerns when using `tf-aws` | Train operators on both Wing compile outputs and Terraform workflows |

---

## Quiz

<details>
<summary>Question 1: What is the difference between preflight and inflight in Wing?</summary>

Preflight code runs during compilation and defines infrastructure configuration consumed by provisioning engines such as Terraform. Inflight code runs after deployment inside compute hosts and implements handlers, consumers, and request logic. The `inflight` keyword marks runtime blocks, while preflight is the default phase for top-level resource declarations.

</details>

<details>
<summary>Question 2: How does Wing derive IAM permissions for a Lambda that writes to a bucket?</summary>

The compiler lifts preflight bucket references into inflight closures and qualifies which inflight methods are used, such as `put`. Those qualifications inform least-privilege policies attached to the inflight host. Explicit `lift` blocks document permissions when static analysis cannot infer conditional resource handles.

</details>

<details>
<summary>Question 3: What does `wing it` do?</summary>

It compiles the program to the simulator target and opens Wing Console locally with hot reload on save. You can interact with simulated buckets, queues, functions, and related resources without cloud credentials, which supports fast integration feedback during development.

</details>

<details>
<summary>Question 4: How does Wing differ from Pulumi in language choice?</summary>

Wing introduces a dedicated cloud-oriented language with explicit phase boundaries enforced by the compiler. Pulumi uses general-purpose languages to register resources with the Pulumi engine while preserving a plan/apply workflow. Teams choose between new syntax plus phase safety versus existing language skills plus Pulumi stack concepts.

</details>

<details>
<summary>Question 5: What artifacts does `wing compile --target tf-aws` produce?</summary>

Preflight synthesis emits Terraform JSON and supporting provisioning files, while inflight code bundles into JavaScript suitable for Lambda-style hosts. Operators review and apply Terraform outputs using normal Terraform workflows and state backends.

</details>

<details>
<summary>Question 6: Can every simulator-valid program deploy to Azure or GCP today?</summary>

Not necessarily. Upstream documentation describes AWS as fully supported for simulator-compilable programs, with GCP and Azure only partially supported. Verify the compatibility matrix and supported services docs before committing to a multi-cloud roadmap.

</details>

<details>
<summary>Question 7: How should teams test Wing applications?</summary>

Use Wing's built-in test runner against simulated resources for integration-style cases, plus focused tests for pure business logic. Tests complement—not replace—Terraform plan review and staged cloud validation for provider-specific behavior.

</details>

<details>
<summary>Question 8: When is Wing a weak fit despite unified syntax?</summary>

When workloads are Kubernetes-first with controller-centric operations, when platform teams need large reusable Terraform module ecosystems without application coupling, or when strict day-one multi-cloud parity is mandatory. Evaluate workload shape and operational ownership before adopting a new language.

</details>

---

## Hands-On Exercise

Build a URL shortener that exercises preflight resource declarations, inflight HTTP handlers, counters, and local simulation before optional AWS compilation.

### Tasks

- [ ] Create `url-shortener.w` with a `cloud.Bucket` for mappings, a `cloud.Counter` for redirects, and a `cloud.Api` exposing shorten, redirect, and stats routes.
- [ ] Run `wing it url-shortener.w` and verify resources appear in Wing Console with hot reload enabled.
- [ ] Create a short URL via `POST /shorten`, follow the redirect via `GET /{code}`, and confirm the counter increments on `/stats`.
- [ ] Add `url-shortener.test.w` with at least two tests using `bring expect` and run `wing test`.
- [ ] Compile with `wing compile url-shortener.w --target tf-aws` and inspect generated Terraform JSON before any cloud apply.

```wing
// url-shortener.w
bring cloud;
bring util;

let urls = new cloud.Bucket() as "url-store";
let counter = new cloud.Counter() as "redirect-counter";
let api = new cloud.Api() as "shortener-api";

api.post("/shorten", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let body = Json.parse(req.body ?? "{}");
  let longUrl = body.get("url").asStr();
  let shortCode = util.uuid().substring(0, 8);
  urls.put(shortCode, longUrl);
  return cloud.ApiResponse {
    status: 201,
    body: Json.stringify({ short_url: "${api.url}/${shortCode}", code: shortCode })
  };
});

api.get("/{code}", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  let code = req.vars.get("code");
  try {
    let longUrl = urls.get(code);
    counter.inc();
    return cloud.ApiResponse { status: 302, headers: { "Location": longUrl } };
  } catch {
    return cloud.ApiResponse { status: 404, body: "URL not found" };
  }
});

api.get("/stats", inflight (req: cloud.ApiRequest): cloud.ApiResponse => {
  return cloud.ApiResponse {
    status: 200,
    body: Json.stringify({ total_redirects: counter.peek() })
  };
});

pub let apiUrl = api.url;
```

```bash
wing it url-shortener.w
wing test url-shortener.test.w
wing compile url-shortener.w --target tf-aws
```

### Success Criteria

- [ ] Simulator starts and exposes all three API routes in Wing Console.
- [ ] Shortening and redirect flows behave correctly with counter updates reflected in `/stats`.
- [ ] Tests pass locally without cloud credentials.
- [ ] Compiled Terraform output exists and is ready for plan review in a non-production account.

---

## Key Takeaways

1. **Spectrum placement** — Wing is infrastructure-from-code with explicit compile-time and runtime phases, not just another template language.
2. **Preflight/inflight** — The compiler enforces boundaries that prevent runtime infrastructure mutation and permission drift.
3. **Synthesis model** — Wing emits provisioning artifacts such as Terraform JSON plus JavaScript inflight bundles rather than talking to clouds directly.
4. **Simulator-first loop** — `wing it` and Wing Console shorten integration feedback before cloud spend.
5. **Lift qualifications** — IAM derives from inflight API usage; explicit `lift` blocks document ambiguous cases.
6. **AWS-first maturity** — Treat other clouds as verify-before-promising per upstream support docs.
7. **Tradeoffs** — New language cost, leaky abstraction risk, and youth are real; benefits concentrate on coupled app/infra workflows.
8. **Peer comparison** — Evaluate against Terraform, Pulumi, and Nitric on capabilities, not hype rankings.

---

## Sources

- [Wing GitHub repository](https://github.com/winglang/wing) — Source code, issues, and release history for the language and toolchain.
- [Wing README](https://raw.githubusercontent.com/winglang/wing/main/README.md) — Project overview, compilation model, and pre-release status notes.
- [What is Wing?](https://github.com/winglang/wing/blob/main/docs/docs/00-what-is-wing.md) — Introduction to cloud-oriented programming goals.
- [Preflight and inflight](https://github.com/winglang/wing/blob/main/docs/docs/02-concepts/01-preflight-and-inflight.md) — Official explanation of phase boundaries, lifting, and IAM qualification.
- [Simulator concept](https://github.com/winglang/wing/blob/main/docs/docs/02-concepts/05-simulator.md) — How local simulation relates to cloud targets.
- [Getting started](https://github.com/winglang/wing/blob/main/docs/docs/01-start-here/02-getting-started.md) — Project bootstrap and first program structure.
- [Run locally with Wing Console](https://github.com/winglang/wing/blob/main/docs/docs/01-start-here/04-run-locally.md) — `wing it` workflow and console interaction patterns.
- [AWS Terraform target (`tf-aws`)](https://github.com/winglang/wing/blob/main/docs/docs/03-platforms/02-AWS/tf-aws.md) — Compiling and deploying Wing programs to AWS via Terraform.
- [Supported clouds FAQ](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/020-supported-clouds-services-and-engines/021-supported-clouds.md) — Maturity differences across AWS, GCP, and Azure.
- [Supported services FAQ](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/020-supported-clouds-services-and-engines/022-supported-services.md) — Service coverage reference across platforms.
- [Terraform vs Wing FAQ](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/040-alternatives/041-terraform-vs-wing.md) — Upstream comparison framing against declarative IaC.
- [Pulumi vs Wing FAQ](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/040-alternatives/042-pulumi-vs-wing.md) — Upstream comparison framing against language-native IaC.
- [Who is behind Wing](https://github.com/winglang/wing/blob/main/docs/docs/999-faq/030-who-is-behind-wing.md) — Stewardship, licensing, and Wing Cloud context.
- [Wing tests concept](https://github.com/winglang/wing/blob/main/docs/docs/02-concepts/04-tests.md) — Testing model against simulated resources.
- [Wing npm package](https://registry.npmjs.org/winglang/latest) — CLI distribution channel and current published version metadata.
- [HashiCorp Terraform documentation](https://developer.hashicorp.com/terraform/docs) — Baseline declarative provisioning concepts Wing often emits artifacts for.
- [Pulumi documentation](https://www.pulumi.com/docs/iac/) — Peer language-native IaC reference for comparison.
- [Nitric documentation](https://nitric.io/docs) — Peer application-centric cloud framework reference.

---

## Next Module

Next: [Module 7.8: SST](../module-7.8-sst/) — compare Wing's compile-time phase model with a TypeScript-first serverless framework that emphasizes live cloud development and resource binding for Lambda-centric workflows.
