---
revision_pending: false
title: "Module 4.2: OPA & Gatekeeper"
slug: platform/toolkits/security-quality/security-tools/module-4.2-opa-gatekeeper
sidebar:
  order: 3
---
## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy OPA Gatekeeper and configure ConstraintTemplates for Kubernetes admission policy enforcement**
- **Implement Rego policies for pod security, resource limits, label requirements, and image restrictions**
- **Configure Gatekeeper audit mode for policy violation reporting without blocking existing workloads**
- **Evaluate OPA Gatekeeper against Kyverno for policy-as-code enforcement complexity and flexibility trade-offs**

## Why This Module Matters

Hypothetical scenario: a platform team supports ten application teams and roughly two hundred Kubernetes manifests spread across service repositories, GitOps overlays, and one emergency operations repository. The team already has pull request checks that catch missing labels, images from unapproved registries, and containers that request privileged mode. That helps, but it does not cover a direct `kubectl apply`, a misconfigured automation token, an old pipeline that skips the new check, or an operator that creates resources from a custom controller. The cluster still needs a final decision point where the API server asks, "Should this object be allowed to exist?"

Admission control is that final decision point. Kubernetes checks who the caller is, checks what the caller is allowed to do, and then runs admission before the object is persisted. The [Kubernetes admission controller documentation](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) describes this placement as after authentication and authorization but before storage. That timing is what makes admission control different from a lint rule. A lint rule advises before the request reaches the cluster; admission control participates in the cluster's own write path.

Policy-as-code is the discipline that makes admission control maintainable instead of arbitrary. A platform team should not encode "no privileged pods" as a private memory in one engineer's head, a Slack reminder, or a hand-edited checklist. It should encode the rule as reviewable text, test the rule with known-good and known-bad examples, roll it out in audit or warning mode, and only then make it blocking. The important shift is not the tool name. The important shift is moving from manual approval to automated guardrails that are visible, versioned, and reversible.

OPA Gatekeeper is a worked example of that discipline. [Open Policy Agent](https://www.openpolicyagent.org/docs/policy-language) gives you the Rego policy language and a general-purpose policy engine. [Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/howto/) connects that policy model to Kubernetes admission by using `ConstraintTemplate` resources for reusable policy logic and `Constraint` resources for scoped, parameterized policy instances. You will use Gatekeeper throughout this module because it exposes the durable mechanics clearly: policy code, parameters, admission decisions, audit results, and progressive enforcement.

The durable lesson will outlive any single policy engine. Kubernetes now has native [ValidatingAdmissionPolicy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/) with CEL, Kyverno provides a YAML and CEL-centered peer that is covered later in [Module 4.7: Kyverno](../module-4.7-kyverno/), and Polaris focuses on workload configuration checks. Your job as a platform engineer is not to memorize a product roster. Your job is to understand where enforcement belongs, how policy should be authored, how rollout risk is reduced, and which tradeoffs matter for a given platform.

## Admission Control Is the Last Gate

Every write to the Kubernetes API has a path. A caller first presents credentials, the API server authenticates the caller, authorization checks whether that caller may perform the requested verb on the requested resource, and admission decides whether the requested object is acceptable before it is stored. The admission phase is not a substitute for RBAC. RBAC answers "may this subject create pods in this namespace?" Admission answers "is this particular pod acceptable under the rules of this platform?"

That distinction matters because many real policies are about object shape, not user identity. A developer may be allowed to create Pods, but not Pods that run privileged containers. A CI service account may be allowed to update Deployments, but not Deployments that use an image registry outside the organization's trusted set. A namespace owner may be allowed to create workloads, but not workloads without `team`, `app`, and `environment` labels. RBAC alone cannot express these object-level constraints with enough precision.

The admission process also has phases. Kubernetes runs mutating admission first, then validating admission. Mutating admission may change an incoming object, often to apply defaults or inject fields. Validating admission observes the final form and may reject it. The same Kubernetes documentation explains that a rejection in either phase rejects the whole request. This ordering means mutation needs extra care: a mutator can make a valid object invalid for a later validator, and multiple mutators can interact in ways that are hard to reason about.

```
Kubernetes write path, simplified

caller
  |
  v
authentication
  |
  v
authorization
  |
  v
mutating admission
  |
  v
validating admission
  |
  v
object persisted to etcd
```

This is why admission belongs in a defense-in-depth design. CI policy checks are still valuable because they give developers fast feedback before a change reaches the cluster. GitOps checks are valuable because they protect the intended deployment path. Admission is valuable because it protects the actual cluster write path. When these layers agree, developers get early feedback and the cluster still has a reliable last gate when a request arrives through another path.

A useful analogy is airport screening. RBAC is the boarding pass check: it confirms that the traveler has permission to enter the secure area. Admission control is the bag scan: it checks the specific thing being brought in. A traveler with a valid boarding pass can still carry an item that is not allowed. A Kubernetes subject with valid create permission can still submit an object that violates platform policy.

The last-gate property also explains why admission policies should be narrow and understandable. A policy that blocks privileged pods, requires labels, or restricts image registries is a good fit because it can be evaluated from the request object and a small amount of policy data. A policy that needs a slow external inventory lookup, an unreliable SaaS endpoint, or a deep chain of business approvals may be better handled before admission, then reinforced at admission with a simpler invariant. Admission is a hot path, not a ticket workflow engine.

## Policy-As-Code Changes The Operating Model

Policy-as-code starts with a social problem: platform rules are easy to invent and hard to operate. A security team may say every workload must run as non-root. A finance team may require cost allocation labels. An operations team may require resource requests for scheduler stability. Each rule is reasonable in isolation, but a cluster with dozens of invisible rules becomes frustrating. Developers need to know what rule failed, why it exists, and what change would satisfy it.

Encoding policy as code gives the rule a lifecycle. The policy can be proposed in a pull request, reviewed by platform and security peers, tested with sample manifests, released first in audit or warning mode, and promoted to denial after the violations are understood. The policy can also be reverted if it causes harm. This is much healthier than a one-time cluster change that only the original author understands.

The most important design choice is to separate policy intent from rollout mode. A policy may express "pods must have team and app labels," but the enforcement action can start as audit or warn. In Gatekeeper, a `Constraint` can use `enforcementAction: dryrun` to record violations without blocking, `warn` to return admission warnings while still allowing the request, or `deny` to block violating requests. The [Gatekeeper constraint violation documentation](https://open-policy-agent.github.io/gatekeeper/website/docs/violations/) describes these modes as supported enforcement actions.

This separation creates a safer rollout sequence. First, apply the policy in audit mode and measure what existing objects violate it. Second, make the message useful enough that a developer can fix the manifest without finding the policy author. Third, move a small scope, such as one namespace or one team, to warnings. Fourth, enforce in scopes where the violation count is low and the exception process is clear. The sequence is slower than flipping directly to deny, but it avoids turning policy work into an outage.

Policy-as-code also needs tests because policy bugs are production bugs. A policy that looks obvious may miss init containers, ignore ephemeral containers, target Pods but not Deployments, or fail when a field is absent. [OPA policy testing](https://www.openpolicyagent.org/docs/policy-testing) provides a framework for testing Rego policies, and [Conftest](https://www.conftest.dev/) applies policy checks to structured configuration such as Kubernetes YAML and Terraform plans. Tests are not paperwork here. They are how you keep guardrails from becoming traps.

The cleanest platform repositories treat policies like shared APIs. Policy names are stable, messages are written for the user, parameters are documented, examples cover both passing and failing inputs, and breaking changes are announced before enforcement changes. This matters because policy is not just code that runs. It is also a contract between the platform team and the teams that use the platform.

## OPA And Rego: The Policy Engine Layer

Open Policy Agent is a general-purpose policy engine, not only a Kubernetes admission controller. It evaluates structured input against policies written in Rego and returns decisions. In a Kubernetes admission use case, the input is an admission review that contains the object under review, the operation, the user information, and related metadata. The policy author writes rules that inspect that input and produce violations when the object does not satisfy the rule.

Rego is declarative, which means a policy describes the conditions that make a result true instead of spelling out a step-by-step procedure. The [OPA policy language documentation](https://www.openpolicyagent.org/docs/policy-language) explains that Rego is designed for reasoning about structured data such as API requests and configuration data. That model fits admission well because Kubernetes resources are structured objects and platform policies usually ask questions about fields in those objects.

The learning curve in Rego is real. Many engineers arrive from imperative languages and expect loops, mutable variables, and early returns. Rego instead uses rules, references, comprehensions, set operations, and expressions that become true or undefined. This is powerful for policy work because a rule can ask for all containers that violate a condition, not just the first one. It also requires disciplined examples and tests so that policy authors understand what the rule is actually selecting.

Here is a small Rego fragment using modern v1 syntax. It is not a complete Gatekeeper template yet; it only shows the shape of a rule that finds containers without a CPU limit. The `violation contains` form builds a set of violation objects, one for each matching container, and the message uses the container name so the person fixing the manifest can find the problem quickly.

```rego
package k8scontainerlimits

violation contains {"msg": msg} if {
  container := input.review.object.spec.containers[_]
  not container.resources.limits.cpu
  msg := sprintf("container %q must set resources.limits.cpu", [container.name])
}
```

Good Rego policies are small, composable, and explicit about the resource shape they expect. A policy that checks Pods can read `input.review.object.spec.containers`. A policy that checks Deployments must read `input.review.object.spec.template.spec.containers`. A policy that claims to check "workloads" needs helper rules that normalize Pods, Deployments, StatefulSets, DaemonSets, Jobs, and CronJobs into a common container list. Otherwise the policy passes tests for one kind and silently misses another kind.

The strongest Rego policy authors write helper rules before clever one-liners. A helper named `containers contains container if { ... }` communicates intent. A helper named `allowed_registry(image)` makes the main violation rule easier to read. If a reviewer can understand the policy without mentally simulating every reference, the policy is safer to operate. Admission policy is not a code golf contest; the target reader is the next person debugging a blocked rollout.

## Gatekeeper's Template And Constraint Model

Gatekeeper maps OPA policy into Kubernetes resources through the constraint framework. A `ConstraintTemplate` defines the reusable policy type. It contains the policy code, the schema for parameters, and the Kubernetes kind that will be created for concrete constraints. A `Constraint` is an instance of that type. It supplies parameters, match rules, and enforcement action. The [Gatekeeper constraint template documentation](https://open-policy-agent.github.io/gatekeeper/website/docs/constrainttemplates/) describes this split as policy code plus the schema of the accompanying constraint object.

The template and constraint split is the durable model to remember. A template is like a function definition: "given a set of required labels, report missing labels." A constraint is like a function call: "require `team` and `app` labels for Pods in namespaces labeled for enforcement." This split lets one platform team maintain the policy logic while different teams or environments use different parameters and scopes.

The following template uses Gatekeeper's `ConstraintTemplate` API with Rego v1 syntax. It requires a `labels` parameter array and reports missing labels on the submitted object. The policy uses `object.get` to treat a missing `metadata.labels` map as an empty object, which avoids a common bug where the policy errors or becomes undefined when the whole labels map is absent.

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    code:
    - engine: Rego
      source:
        version: "v1"
        rego: |
          package k8srequiredlabels

          violation contains {"msg": msg} if {
            required := {label | some label in input.parameters.labels}
            provided := object.get(input.review.object.metadata, "labels", {})
            missing := required - {label | provided[label]}
            count(missing) > 0
            msg := sprintf("missing required labels: %v", [missing])
          }
```

A matching constraint chooses where that policy applies. This example starts in `dryrun`, matches namespaced Pods, and uses a namespace selector so the rollout can be controlled with a namespace label. The Gatekeeper `match` field supports matchers such as kinds, scope, namespaces, excluded namespaces, label selectors, and namespace selectors. The scope matters because cluster-scoped resources do not behave like namespace-scoped resources, and accidental cluster-wide matching is a common source of noisy audits.

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-and-app
spec:
  enforcementAction: dryrun
  match:
    scope: Namespaced
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaceSelector:
      matchLabels:
        policy.kubedojo.io/enforce: "true"
  parameters:
    labels:
    - team
    - app
```

The practical design question is not "can this policy be written?" Most policies can be written somehow. The question is "will this policy be understandable, testable, and supportable when it blocks a real deployment?" A required-label policy is easy to reason about. A policy that checks every image tag against an external vulnerability service during admission is harder because the admission path now depends on another service's latency and availability.

Gatekeeper also ships a community-owned [Gatekeeper Library](https://open-policy-agent.github.io/gatekeeper-library/website/) with reusable policies. Treat a library policy as a starting point, not a magic import. Read the template, understand which resource kinds it covers, check whether it handles init and ephemeral containers, and write local tests for your exact parameters. Library policies save time, but they do not remove responsibility for rollout and user-facing messages.

## Audit, Warn, And Enforce

Admission enforcement only sees requests that pass through admission after the policy exists. That means it cannot, by itself, discover every object that was already in the cluster. Gatekeeper's [audit documentation](https://open-policy-agent.github.io/gatekeeper/website/docs/audit/) explains that audit performs periodic evaluations of existing resources against constraints and records pre-existing misconfigurations. This is the bridge between admission-time prevention and cluster-state visibility.

Audit mode is where mature teams spend time before they enforce. If a policy requires labels, audit tells you which existing Pods or controllers are missing labels. If a policy restricts image registries, audit shows which existing images are outside the proposed allowlist. The result is not only a technical report. It is the migration plan for teams that need to update manifests before enforcement becomes blocking.

The rollout path should be explicit and boring. Start with a constraint in `dryrun`, review `status.violations`, and fix the biggest categories. Move to `warn` if you want admission-time feedback without blocking. Promote to `deny` after the violation set is small, the message is clear, and there is an exception path for legitimate edge cases. If the platform cannot explain how to get an exception, the platform is not ready to enforce.

Here are the operational commands you will use most often after a constraint is installed. They are intentionally simple because incident response is not the time to remember a complex query. The first command lists constraint kinds, the second inspects the concrete constraint, and the third reads Gatekeeper logs when you need controller-level context.

```bash
kubectl get constraints
kubectl get k8srequiredlabels require-team-and-app -o yaml
kubectl logs -n gatekeeper-system -l control-plane=controller-manager --tail=100
```

Audit also has performance implications. Gatekeeper can query the API during each audit cycle, and it can use a cache when configured for cache-based audit. A platform with many resources and many constraints should test audit cost before assuming every policy can scan every resource frequently. Admission latency and audit cost are separate concerns, but both become part of the operating budget for policy-as-code.

The right mental model is "observe before enforce." A policy that blocks new privileged Pods is usually reasonable. A policy that blocks updates to every old Deployment until the old manifest is fixed can surprise teams if they need to update an unrelated field during an incident. Audit gives you a way to see the backlog before a deny action turns that backlog into blocked work.

## Mutation: Useful Defaults, Higher Risk

Validation answers yes or no. Mutation changes the object. Gatekeeper supports mutation through separate resources such as `Assign` and `ModifySet`, and its [mutation documentation](https://open-policy-agent.github.io/gatekeeper/website/docs/mutation/) describes mutation policies as separate from validation constraints. That separation is important. A policy that denies a missing label is a different kind of control from a policy that writes a default label into the object.

Mutation is useful when the platform can safely provide a default that the user would have chosen anyway. Examples include setting a default `imagePullPolicy`, adding a harmless label, or setting a pod-level security default for a scoped set of namespaces. Mutation is risky when it hides responsibility, changes application behavior, or creates GitOps drift. If the object stored in the cluster differs from the object in Git, your reconciliation tools may fight the mutator or repeatedly report differences.

This Gatekeeper `Assign` example sets a pod-level `runAsNonRoot` default for matched Pods. It is an illustrative pattern, not a blanket recommendation. You would still need to test workloads that require a specific user, check how the policy interacts with pod and container security contexts, and decide whether mutation or validation gives developers clearer feedback.

```yaml
apiVersion: mutations.gatekeeper.sh/v1
kind: Assign
metadata:
  name: default-run-as-nonroot
spec:
  applyTo:
  - groups: [""]
    versions: ["v1"]
    kinds: ["Pod"]
  match:
    scope: Namespaced
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  location: "spec.securityContext.runAsNonRoot"
  parameters:
    assign:
      value: true
```

`ModifySet` is the companion pattern for list fields. It can add or remove list entries as though the list were a set, which is useful for arguments, capabilities, or other list-like fields. The risk is that list mutation can become surprising when application authors also manage the same field. If a platform mutates list fields, it should document exactly which fields it owns and how application teams can inspect the final admitted object.

The safest mutation policy is one that is narrow, idempotent, and visible. Narrow means it matches only the resources and namespaces that need it. Idempotent means repeated admission does not keep changing the object. Visible means the team can explain the mutation through docs, audit annotations, events, or reviewable policy code. A mutator that silently edits broad classes of resources is a future debugging problem.

## The Native Shift: ValidatingAdmissionPolicy And CEL

Kubernetes no longer requires every custom validation policy to run through an external webhook. [ValidatingAdmissionPolicy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/) is a built-in admission API that uses CEL expressions and `ValidatingAdmissionPolicyBinding` resources. The Kubernetes project announced this feature as generally available in [Kubernetes 1.30](https://kubernetes.io/blog/2024/04/24/validating-admission-policy-ga/), and the current docs list the feature state as stable.

The durable shift is architectural. A webhook policy engine runs outside the API server, so the API server must call a service over the network during admission. A ValidatingAdmissionPolicy evaluates CEL in process as part of the API server's admission path. The [Kubernetes CEL documentation](https://kubernetes.io/docs/reference/using-api/cel/) explains that CEL expressions are evaluated directly in the API server, which makes CEL a useful alternative to out-of-process mechanisms for many extensibility cases.

Here is the same required-label idea in native Kubernetes form. The policy contains the CEL expression, and the binding chooses the enforcement actions and match scope. Starting with `Warn` and `Audit` mirrors the safer rollout pattern you saw with Gatekeeper, while changing the binding to `Deny` makes the policy blocking.

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-team-label.example.com
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods"]
  validations:
  - expression: "has(object.metadata.labels) && 'team' in object.metadata.labels"
    message: "Pod must have a team label."
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-team-label-warning.example.com
spec:
  policyName: require-team-label.example.com
  validationActions: [Warn, Audit]
```

Native policy changes the build-versus-adopt calculus. If a rule is simple, local to the submitted object, and expressible cleanly in CEL, ValidatingAdmissionPolicy may remove the operational burden of a webhook. If a rule needs rich libraries, external data, reusable templates, broad reporting, or existing Rego investment, Gatekeeper may still be the better fit. If a team wants YAML-native authoring and generation capabilities, Kyverno may be a better peer to evaluate.

MutatingAdmissionPolicy is the matching native direction for mutation. The current upstream [MutatingAdmissionPolicy documentation](https://kubernetes.io/docs/reference/access-authn-authz/mutating-admission-policy/) describes CEL-based mutation policies that can apply server-side apply style mutations or JSON patches. KubeDojo's current Kubernetes standard for content is 1.35, while the public current docs page lists the feature as stable in 1.36. For 1.35-targeted exercises, treat MutatingAdmissionPolicy as a version-dependent native peer and verify the API on the actual cluster before relying on it.

The practical takeaway is not that webhooks are obsolete. The practical takeaway is that admission policy now has a native in-tree option for many validation use cases. Platform teams should choose the smallest mechanism that can express the rule, operate reliably, and give users clear feedback. A simple label rule does not need the same machinery as a registry trust policy with external attestations.

## Landscape Snapshot And Rosetta

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

OPA is a CNCF Graduated project; the [CNCF OPA project page](https://www.cncf.io/projects/open-policy-agent-opa/) records graduation on January 29, 2021. Kyverno is also CNCF Graduated; the [CNCF Kyverno project page](https://www.cncf.io/projects/kyverno/) records the move to Graduated on March 16, 2026, and the [CNCF announcement](https://www.cncf.io/announcements/2026/03/24/cloud-native-computing-foundation-announces-kyvernos-graduation/) is dated March 24, 2026. ValidatingAdmissionPolicy is Kubernetes native and GA since 1.30. MutatingAdmissionPolicy is the native mutation peer to track, but verify the feature state against the exact Kubernetes version and provider you run.

| Durable capability | OPA Gatekeeper | Kyverno | Native ValidatingAdmissionPolicy (CEL) | Polaris |
|--------------------|----------------|---------|----------------------------------------|---------|
| Policy language | Rego, and newer Gatekeeper paths can use CEL in templates | YAML and CEL in current policy types | CEL only | Built-in checks plus custom JSON Schema |
| Validating admission | Yes, via validating webhook and constraints | Yes, via admission controller and policy resources | Yes, in process through the API server | Yes, as an admission controller |
| Mutating admission | Yes, through mutation CRDs such as `Assign` and `ModifySet` | Yes, through mutation policy types | No; validation only | Can remediate some workload configuration issues |
| Audit and reports | Gatekeeper audit records existing violations on constraints | PolicyReports and background scans are part of the model | Binding actions include `Audit`, with cluster audit integration | Dashboard, CLI, and admission modes report workload checks |
| Generation | Not the core model | Generation is a core Kyverno capability | No generation | No general resource generation model |
| In-tree vs webhook | Webhook-based controller | Webhook-based controller, with newer native policy integrations | In-tree API server evaluation | Webhook or CLI/dashboard depending on mode |
| External data | Gatekeeper external data providers | Kubernetes resources and API calls in current policy model | Parameter resources, not arbitrary webhook calls | Configuration-focused checks, not a general external-data engine |

The Rosetta table is not a ranking. It is a map of tradeoffs. Rego is expressive and portable across OPA use cases, but it asks policy authors to learn a language that feels different from YAML. Kyverno aligns closely with Kubernetes resource authoring and adds generation and reporting features, but the policy model is its own system to operate. Native CEL reduces webhook operations for simple validation, but it is intentionally smaller than a full policy engine. Polaris focuses on workload best-practice checks and is useful when that narrower shape matches the problem.

Use Gatekeeper in this module as the running example because it makes the policy lifecycle visible. You can see the reusable template, the concrete constraint, the Rego rule, the match scope, the audit result, and the enforcement action. When you later study Kyverno, compare it on the same axes rather than asking which tool is "better" in the abstract.

## Operational Concerns That Decide Success

Webhook failure policy is one of the most important production decisions. Kubernetes dynamic admission webhooks can use `failurePolicy: Fail` or `Ignore`; the [dynamic admission control documentation](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) explains that `Fail` rejects the request when the webhook cannot be called, while `Ignore` proceeds without the webhook. `Fail` preserves policy during outages but can lock out cluster writes if the webhook is down. `Ignore` preserves availability but creates a policy bypass during webhook failure.

There is no universally correct failure policy. For high-risk security policies, failing closed may be appropriate after the webhook is highly available, monitored, and tested. For early rollout or non-critical advisory policies, failing open may be less disruptive. The decision should be written down with the policy's purpose, not copied from a blog post. A policy that exists to prevent privileged production workloads has a different availability tradeoff than a policy that encourages optional metadata hygiene.

Latency is the second concern. Admission happens on the API server write path, so every webhook call adds cost to user requests and controllers. A slow policy engine can slow deploys, operators, and controllers that create many objects. A policy that calls external data during admission adds another dependency to the path. If an external lookup is necessary, cache aggressively, set timeouts deliberately, and test behavior when the provider is unavailable.

Scope is the third concern. Broad matching is easy and dangerous. A constraint with no namespace selector, no excluded namespaces, and no resource-kind discipline can affect system add-ons, operators, and emergency repair workflows. Start with namespace labels, explicit resource kinds, and a documented exclusion model. Exclusions are not policy failure; they are part of safe operations when they are reviewed, temporary where possible, and visible.

Testing is the fourth concern. A good policy repository contains unit tests for policy logic, example manifests for common failures, and an integration path that evaluates real Kubernetes YAML before deployment. `opa test` is useful for Rego logic, Conftest is useful for structured files in CI, and a temporary cluster is useful for checking that the exact Gatekeeper `ConstraintTemplate` and `Constraint` APIs are accepted by the Kubernetes API server. Each layer catches a different class of mistake.

Progressive rollout is the final concern. Good platform teams create a path from observe to warn to enforce. They also publish the message developers will see, the remediation examples, the owner of the policy, and the exception process. A policy with no owner becomes a stale blocker. A policy with no remediation example becomes a support queue. A policy with no audit phase becomes a surprise.

## Worked Example: Required Labels With Gatekeeper

This worked example enforces required labels on Pods in a dedicated lab namespace. It starts in `dryrun` so you can confirm the policy and audit behavior without blocking workloads, then promotes the constraint to `deny`. The same pattern works for image registry restrictions, resource limit requirements, and security context rules. The details differ, but the lifecycle stays the same.

First, create a namespace and mark it as in scope. This label is deliberately policy-specific so a team can opt a namespace into enforcement during rollout without changing every constraint. In production, namespace selection should be managed by your platform ownership model rather than left as an arbitrary developer toggle.

```bash
kubectl create namespace gatekeeper-lab
kubectl label namespace gatekeeper-lab policy.kubedojo.io/enforce=true
```

Install Gatekeeper using a pinned release manifest if your cluster does not already have it. The release version below is a dated example for this module; verify the [Gatekeeper releases](https://github.com/open-policy-agent/gatekeeper/releases) and your cluster compatibility before production use. The command is copy-runnable for a test cluster with cluster-admin permissions and a current `kubectl` context.

```bash
GATEKEEPER_VERSION=v3.22.2
kubectl apply -f "https://raw.githubusercontent.com/open-policy-agent/gatekeeper/${GATEKEEPER_VERSION}/deploy/gatekeeper.yaml"
kubectl wait --for=condition=available deployment/gatekeeper-controller-manager -n gatekeeper-system --timeout=180s
```

Apply the `ConstraintTemplate` and `Constraint` from the earlier examples. Save them as `required-labels-template.yaml` and `required-labels-constraint.yaml`, then apply them with `kubectl apply -f`. Watch the template status after applying it because Gatekeeper reports ingestion errors there when Rego or schema validation fails.

```bash
kubectl apply -f required-labels-template.yaml
kubectl get constrainttemplate k8srequiredlabels -o yaml
kubectl apply -f required-labels-constraint.yaml
kubectl get k8srequiredlabels require-team-and-app -o yaml
```

Create a violating Pod while the constraint is still in `dryrun`. The request should be allowed because the policy is observing rather than enforcing. After the audit cycle runs, the violation should appear on the constraint status. Audit timing is not instantaneous, so give the controller a short window before assuming the policy failed.

```bash
kubectl run missing-labels \
  --namespace gatekeeper-lab \
  --image=registry.k8s.io/pause:3.10 \
  --restart=Never

kubectl get k8srequiredlabels require-team-and-app -o jsonpath='{.status.totalViolations}{"\n"}'
```

Promote the policy to denial only after you have confirmed the audit output and message. The patch below changes only the enforcement action. Then create one violating Pod and one compliant Pod so you can see both paths. The violating Pod should be denied with the policy message, and the compliant Pod should be admitted.

```bash
kubectl patch k8srequiredlabels require-team-and-app \
  --type=merge \
  -p '{"spec":{"enforcementAction":"deny"}}'

kubectl run blocked \
  --namespace gatekeeper-lab \
  --image=registry.k8s.io/pause:3.10 \
  --restart=Never

kubectl run allowed \
  --namespace gatekeeper-lab \
  --image=registry.k8s.io/pause:3.10 \
  --restart=Never \
  --labels=team=platform,app=allowed
```

Cleanup matters in policy labs because admission rules can outlive the exercise and surprise later work. Delete the constraint before the template, then delete the lab namespace. If you installed Gatekeeper only for this lab, remove it after all constraints and mutation resources are gone. In a shared development cluster, coordinate that removal with other users first.

```bash
kubectl delete k8srequiredlabels require-team-and-app
kubectl delete constrainttemplate k8srequiredlabels
kubectl delete namespace gatekeeper-lab
```

The required-label example is intentionally simple, but it exercises the core workflow. You deployed Gatekeeper, installed reusable policy logic through a `ConstraintTemplate`, instantiated that logic through a `Constraint`, observed audit behavior, and then promoted enforcement. The same rollout pattern is the habit you want before writing higher-impact policies such as registry restrictions or pod security controls.

## Patterns & Anti-Patterns

### Pattern: Start With Intent, Then Encode

Strong policy work begins with a sentence that a human can evaluate: "Pods in production namespaces must declare team and app labels." Only after that sentence is clear should you choose Rego, CEL, Kyverno YAML, or another encoding. If the intent is vague, the policy code becomes a debate disguised as automation. Clear intent also gives reviewers a way to decide whether the policy is too broad, too narrow, or missing an exception path.

### Pattern: Separate Policy Logic From Rollout Scope

Reusable policy logic should not hard-code every namespace, registry, or team-specific exception. Gatekeeper's template and constraint split gives you this separation naturally: the template holds the logic, and the constraint holds parameters, scope, and enforcement action. This pattern lets the same rule run in `dryrun` for one namespace, `warn` for another, and `deny` for a third while the underlying logic remains reviewable and tested in one place.

### Pattern: Write Messages For The Person Holding The Pager

The user-facing message is part of the product. "Denied by policy" is not enough. A useful message names the failed field, the requirement, and the simplest fix. During an incident, a developer may not know Rego or know who owns the policy. A clear message can turn a blocked deployment into a quick manifest correction instead of a support escalation.

### Anti-Pattern: Enforce Before You Audit

Immediate denial feels decisive, but it often turns unknown drift into blocked work. Existing workloads may lack labels, old charts may use registries you forgot, and operators may create resources that do not follow application-team conventions. Enforcing before audit makes the platform team discover these facts through failures. Audit first so the team learns from data rather than from production pressure.

### Anti-Pattern: Put Slow Business Logic In Admission

Admission is not the place for a multi-step approval workflow or an unreliable external dependency. If a policy needs to ask a slow system for every Pod create request, the platform has placed that system on the cluster write path. Prefer pre-admission workflows for heavyweight business decisions and admission policies for compact invariants that can be evaluated quickly and reliably.

### Anti-Pattern: Treat One Tool As The Policy Strategy

A tool can enforce rules, but it is not the strategy. The strategy is the policy lifecycle, ownership model, test discipline, rollout plan, exception process, and observability path. A team can misuse Gatekeeper, Kyverno, native CEL, or Polaris in the same way by skipping audit, hiding messages, and enforcing broad rules with no owner. Choose tools after the operating model is clear.

### Decision Framework

| Question | Gatekeeper-leaning answer | Native CEL-leaning answer | Kyverno or Polaris-leaning answer |
|----------|---------------------------|---------------------------|-----------------------------------|
| Is the rule complex, reusable, or already written in Rego? | Gatekeeper is a natural fit. | Native CEL may be too small. | Kyverno may fit if YAML or CEL authoring is preferred. |
| Can the rule be expressed as a short object-local CEL expression? | Gatekeeper can do it, but may be more machinery. | ValidatingAdmissionPolicy is a strong candidate. | Kyverno can still be useful if reports or broader workflows matter. |
| Does the rule need generation or rich YAML-native workflows? | Gatekeeper is not centered on generation. | Native CEL does not generate resources. | Kyverno is the peer to evaluate, and Polaris fits workload checks. |
| Does the rule need external data at admission time? | Gatekeeper external data may fit with careful latency controls. | Native CEL is intentionally limited here. | Kyverno may fit some Kubernetes resource and API lookup cases. |
| Is the main need a workload best-practice audit? | Gatekeeper can enforce custom rules. | Native CEL can enforce specific validations. | Polaris may be simpler when its built-in checks match the need. |

The framework should lead to a conversation, not a reflex. A small organization with a handful of label rules may prefer native CEL to avoid operating a webhook. A platform with existing Rego, constraint libraries, and cross-system OPA usage may prefer Gatekeeper. A team that wants Kubernetes-shaped policy resources with generation and policy reports may prefer Kyverno. A team auditing workload hygiene may start with Polaris. The correct answer depends on capability fit and operational maturity.

## Did You Know?

- **Admission does not protect reads**: Kubernetes admission applies to requests that create, update, delete, or otherwise modify resources, while read operations such as get, list, and watch bypass the admission layer.
- **Gatekeeper audit is separate from admission denial**: audit evaluates existing resources and records violations, while admission enforcement decides what happens to new or updated requests.
- **ValidatingAdmissionPolicy has multiple actions**: a binding can use `Deny`, `Warn`, and `Audit`, which lets native CEL policies follow the same progressive rollout idea.
- **Constraint parameters are schema-checked**: a Gatekeeper `ConstraintTemplate` defines the parameter schema, so the API server can reject constraints with the wrong parameter shape.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Matching only Pods when teams deploy Deployments | The policy may miss controller templates or produce confusing coverage gaps | Decide whether to validate Pods at creation, controller templates at submission, or both, then test each resource kind |
| Enforcing without an audit phase | Existing drift becomes blocked work when teams touch old resources | Start with `dryrun` or `warn`, review violations, and publish remediation steps before denial |
| Forgetting init or ephemeral containers | A security rule may miss containers that run outside the main `containers` list | Normalize all relevant container lists in helper rules and test each list explicitly |
| Using `failurePolicy: Fail` without recovery planning | A webhook outage can block cluster writes and slow incident response | Pair fail-closed policies with high availability, monitoring, runbooks, and scoped break-glass procedures |
| Calling slow external services during admission | API writes inherit the latency and availability of that dependency | Prefer cached data, short timeouts, or pre-admission checks for heavy lookups |
| Writing vague denial messages | Developers cannot tell which field to change or who owns the rule | Include the field, requirement, and remediation hint in the policy message |
| Hard-coding every exception into Rego | Policy code becomes brittle and politically hard to review | Put environment-specific choices into parameters, selectors, and documented exception resources |
| Treating audit reports as historical evidence | Current-state reports may not preserve the full history of denied or fixed requests | Send admission events, metrics, and audit logs to observability systems when history matters |

## Quiz

### Question 1

A team has CI checks that reject privileged containers, but a cluster administrator can still create a privileged Pod with `kubectl apply`. Where should the durable enforcement point be, and why?

<details><summary>Answer</summary>

The durable enforcement point should be Kubernetes admission because it runs after authentication and authorization but before the object is persisted. CI is useful because it gives early feedback, but it can be bypassed by direct cluster access, old automation, or controllers that create resources. Admission gives the cluster a final gate for object-level rules such as no privileged pods. A good design still keeps CI checks for speed and admission checks for last-mile enforcement.

</details>

### Question 2

You need to **Deploy OPA Gatekeeper and configure ConstraintTemplates for Kubernetes admission policy enforcement**. What is the difference between the `ConstraintTemplate` and the `Constraint` you apply afterward?

<details><summary>Answer</summary>

The `ConstraintTemplate` defines the reusable policy type: the parameter schema, the policy code, and the Kubernetes kind that will represent concrete constraints. The `Constraint` is the configured instance of that template, with match scope, parameters, and enforcement action. In the required-label example, the template defines how to find missing labels, while the constraint says which labels are required and where the rule applies. This split lets one policy implementation support different namespaces, parameters, and rollout modes.

</details>

### Question 3

You want to **Implement Rego policies for pod security, resource limits, label requirements, and image restrictions**. A Rego policy works for direct Pod creation but does not catch a Deployment that later creates Pods. What is the likely design bug?

<details><summary>Answer</summary>

The likely bug is that the policy only reads the Pod shape at `spec.containers` while the Deployment stores its pod template at `spec.template.spec.containers`. Gatekeeper evaluates the object submitted to admission, so a Deployment request is not the same object shape as a Pod request. The policy should either match Pods when they are created by controllers, validate controller templates directly, or normalize both shapes through helper rules. Tests should include each resource kind the policy claims to cover.

</details>

### Question 4

A security team wants to block images from registries outside an allowlist, but audit shows many existing add-ons use registries that were not considered. What rollout mode should you use first?

<details><summary>Answer</summary>

Start with audit-oriented rollout, such as Gatekeeper `dryrun` or possibly `warn`, instead of immediate denial. That lets you see existing violations and refine the allowlist without breaking workloads or blocking unrelated updates. After the team understands the violations, it can communicate remediation, add legitimate exceptions, and enforce in a smaller scope first. This is how you **Configure Gatekeeper audit mode for policy violation reporting without blocking existing workloads** while still moving toward enforcement.

</details>

### Question 5

Your platform team is choosing between Gatekeeper and native ValidatingAdmissionPolicy for a rule that requires a `team` label on Pods. How should you evaluate the tradeoff?

<details><summary>Answer</summary>

If the rule is a simple object-local validation that fits cleanly in CEL, native ValidatingAdmissionPolicy is attractive because it avoids operating an external webhook. Gatekeeper is still reasonable if the organization already uses Rego, wants reusable constraint templates, or needs Gatekeeper audit and external-data patterns. The decision should compare capability and operations rather than tool identity. This is part of how you **Evaluate OPA Gatekeeper against Kyverno for policy-as-code enforcement complexity and flexibility trade-offs**, with native CEL included as another peer.

</details>

### Question 6

A team proposes a Gatekeeper policy that calls an external vulnerability service during every Pod admission request. What operational risks should you review before approving it?

<details><summary>Answer</summary>

You should review admission latency, provider availability, timeout behavior, caching, and webhook failure policy. If the external service is slow or unavailable, the API server write path may slow down or fail depending on `failurePolicy`. You should also ask whether the heavy check can run before admission and be reduced to a simpler admission invariant. Admission policies should be reliable enough to sit on a hot path.

</details>

### Question 7

A policy author says mutation is safer than denial because it fixes manifests automatically. What is the missing concern?

<details><summary>Answer</summary>

Mutation can be useful, but it can also hide platform behavior and create drift between Git and the object stored in the cluster. A mutator should be narrow, idempotent, documented, and tested against the workloads it affects. If a default changes application behavior, validation with a clear message may be safer than silently editing the object. Mutation is not safer by default; it is safer only when the platform owns the field and users can see what happened.

</details>

## Hands-On

In this exercise, you will install Gatekeeper in a test cluster, create a required-label policy, observe it in `dryrun`, and then promote it to `deny`. Use a disposable cluster or a namespace you are allowed to control because admission policies affect real API writes. If Gatekeeper is already installed, skip the install step and verify the existing version and ownership before applying test policies.

1. Create a namespace named `gatekeeper-lab` and label it with `policy.kubedojo.io/enforce=true`.
2. Install Gatekeeper or verify that an existing Gatekeeper installation is healthy in `gatekeeper-system`.
3. Apply the `K8sRequiredLabels` `ConstraintTemplate` from this module and confirm that the template status has no ingestion errors.
4. Apply the `require-team-and-app` constraint in `dryrun` mode and create one Pod without labels in the lab namespace.
5. Inspect the constraint status for audit violations, then patch the constraint to `deny` and confirm that an unlabeled Pod is blocked while a labeled Pod is admitted.

Success criteria:

- [ ] `kubectl get deployment -n gatekeeper-system gatekeeper-controller-manager` reports an available Gatekeeper controller, or your existing managed policy controller is documented for the lab.
- [ ] `kubectl get constrainttemplate k8srequiredlabels -o yaml` shows the template was accepted without Rego ingestion errors.
- [ ] `kubectl get k8srequiredlabels require-team-and-app -o yaml` shows `enforcementAction: dryrun` before enforcement promotion.
- [ ] An unlabeled Pod in `gatekeeper-lab` is admitted during `dryrun` and appears as an audit violation after the audit cycle.
- [ ] After patching to `deny`, an unlabeled Pod is rejected and a Pod with `team` and `app` labels is admitted.

Verification commands:

```bash
kubectl get namespace gatekeeper-lab --show-labels
kubectl get constrainttemplate k8srequiredlabels -o yaml
kubectl get k8srequiredlabels require-team-and-app -o yaml
kubectl get pods -n gatekeeper-lab --show-labels
kubectl logs -n gatekeeper-system -l control-plane=controller-manager --tail=100
```

Clean up after the exercise so that the lab policy does not affect later work. Delete the concrete constraint before deleting the template because constraints depend on the generated kind. If you installed Gatekeeper only for this exercise, remove it after the constraints and templates are gone.

```bash
kubectl delete k8srequiredlabels require-team-and-app --ignore-not-found
kubectl delete constrainttemplate k8srequiredlabels --ignore-not-found
kubectl delete namespace gatekeeper-lab --ignore-not-found
```

## Sources

- [Kubernetes Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) - Primary documentation for the admission phase, mutating versus validating admission, and where admission sits in the API write path.
- [Kubernetes Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) - Primary documentation for webhook behavior, `failurePolicy`, and dynamic admission operations.
- [Kubernetes Validating Admission Policy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/) - Primary documentation for native CEL validation policy resources and binding actions.
- [Kubernetes Validating Admission Policy GA Announcement](https://kubernetes.io/blog/2024/04/24/validating-admission-policy-ga/) - Kubernetes project announcement that ValidatingAdmissionPolicy reached GA in Kubernetes 1.30.
- [Kubernetes Mutating Admission Policy](https://kubernetes.io/docs/reference/access-authn-authz/mutating-admission-policy/) - Primary documentation for native CEL mutation policy concepts and feature state.
- [Common Expression Language in Kubernetes](https://kubernetes.io/docs/reference/using-api/cel/) - Primary documentation for CEL usage, API server evaluation, and expression constraints in Kubernetes.
- [OPA Policy Language](https://www.openpolicyagent.org/docs/policy-language) - Primary documentation for Rego, declarative policy evaluation, and structured-data policy authoring.
- [OPA Kubernetes Admission Control](https://openpolicyagent.org/docs/kubernetes) - Primary OPA documentation for Kubernetes admission-control integration patterns.
- [OPA Policy Testing](https://www.openpolicyagent.org/docs/policy-testing) - Primary documentation for writing tests for Rego policies.
- [Gatekeeper How To](https://open-policy-agent.github.io/gatekeeper/website/docs/howto/) - Primary Gatekeeper documentation for constraints, templates, matching, parameters, and enforcement actions.
- [Gatekeeper Releases](https://github.com/open-policy-agent/gatekeeper/releases) - Primary release page used to verify the dated install example before pinning a lab manifest.
- [Gatekeeper Constraint Templates](https://open-policy-agent.github.io/gatekeeper/website/docs/constrainttemplates/) - Primary documentation for `ConstraintTemplate` structure and policy code fields.
- [Gatekeeper Handling Constraint Violations](https://open-policy-agent.github.io/gatekeeper/website/docs/violations/) - Primary documentation for `deny`, `dryrun`, and `warn` enforcement actions.
- [Gatekeeper Audit](https://open-policy-agent.github.io/gatekeeper/website/docs/audit/) - Primary documentation for periodic audit of existing resources and violation reporting.
- [Gatekeeper Mutation](https://open-policy-agent.github.io/gatekeeper/website/docs/mutation/) - Primary documentation for Gatekeeper mutation resources such as `Assign` and `ModifySet`.
- [Gatekeeper External Data](https://open-policy-agent.github.io/gatekeeper/website/docs/externaldata/) - Primary documentation for external data provider patterns and security considerations.
- [Gatekeeper Library](https://open-policy-agent.github.io/gatekeeper-library/website/) - Primary site for the community-owned Gatekeeper policy library.
- [CNCF Open Policy Agent Project](https://www.cncf.io/projects/open-policy-agent-opa/) - CNCF project page used to verify OPA maturity and project status.
- [CNCF Kyverno Project](https://www.cncf.io/projects/kyverno/) - CNCF project page used to verify Kyverno maturity and project status.
- [CNCF Kyverno Graduation Announcement](https://www.cncf.io/announcements/2026/03/24/cloud-native-computing-foundation-announces-kyvernos-graduation/) - CNCF announcement used to verify the public Kyverno graduation announcement date.
- [Kyverno Introduction](https://kyverno.io/docs/introduction/) - Primary Kyverno documentation for policy-as-code capabilities and authoring model.
- [Kyverno ValidatingPolicy](https://kyverno.io/docs/policy-types/validating-policy/) - Primary Kyverno documentation for its CEL-based validating policy type and comparison with native VAP.
- [Conftest](https://www.conftest.dev/) - Primary Conftest documentation for testing structured configuration data with policy.
- [Fairwinds Polaris Documentation](https://polaris.docs.fairwinds.com/) - Primary Polaris documentation for workload validation, remediation, admission controller, dashboard, and CLI modes.

## Next Module

Continue to [Module 4.3: Falco](../module-4.3-falco/) to learn runtime security monitoring for detecting threats in running containers.
