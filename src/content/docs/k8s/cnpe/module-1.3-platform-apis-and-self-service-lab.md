---
title: "CNPE Platform APIs and Self-Service Lab"
slug: k8s/cnpe/module-1.3-platform-apis-and-self-service-lab
sidebar:
  order: 103
---

> **CNPE Track** | Complexity: `[COMPLEX]` | Time to Complete: 75-90 min
>
> **Prerequisites**: CNPE Exam Strategy and Environment, Platform Engineering fundamentals, CRDs and Operators, Backstage, Crossplane, Kubebuilder, vCluster

## What You'll Be Able to Do

After this module, you will be able to:
- distinguish a platform API from the implementation behind it
- read a CRD-backed contract and identify the user-facing fields that matter
- use self-service provisioning patterns without bypassing platform governance
- troubleshoot reconciliation failures by checking spec, status, and events
- explain when to consume an existing platform API versus when to author a new one

## Why This Module Matters

CNPE is a platform-engineering exam, so self-service is one of its core ideas. The real test is not "can you write YAML?" It is "can you use platform abstractions to make a safe, repeatable change without hand-crafting the underlying infrastructure?"

That means you need to understand how a platform API works as a contract:
- the user declares intent
- the platform validates and reconciles that intent
- the user reads status instead of guessing

> **The Restaurant Analogy**
>
> A good platform API is like a menu, not a kitchen tour. The caller should order outcomes. The platform should handle the cooking, the plating, and the cleanup.

## What CNPE Wants You to Understand

The CNPE self-service domain usually mixes several layers:
- CRDs and custom resources
- controllers and reconciliation loops
- claims, compositions, or templates
- portal-backed workflows such as Backstage templates
- virtual environments such as vCluster

The exam often rewards the person who can tell whether the current problem is:
- a user error in the claim
- a platform bug in the composition or controller
- an access issue in RBAC
- a sync issue in the backing resources

## Part 1: Platform API Thinking

### 1.1 Three Layers to Remember

```text
User Intent -> Platform Contract -> Platform Implementation

Example:
  Claim   -> Namespace + Policy + App Template -> Deployment, Service, Secret, RBAC
```

The user should interact with the highest layer that still satisfies the task. That keeps the platform maintainable and the user experience consistent.

### 1.2 What Good Self-Service Looks Like

Good self-service has:
- a clear input schema
- predictable defaults
- status feedback
- safe failure modes
- a documented escape hatch

Bad self-service has:
- too many fields with no guidance
- hidden side effects
- unclear ownership of errors
- manual steps that break the abstraction

### 1.3 When to Use Which Tool

Use the simplest layer that fits the request:
- Backstage for discoverable templates and developer workflows
- Crossplane for platform composition and claims
- Kubebuilder or operators when the platform needs a custom controller
- vCluster when the problem is tenant isolation or ephemeral environments

If the task can be solved by consuming an existing API, do that instead of designing a new one.

## Part 2: Lab Scenarios

### 2.1 Scenario A: Read the Contract

You are given a custom resource and asked to explain what it provisions.

Look for:
- `spec` fields that express intent
- `status` fields that show progress
- conditions or events that explain failures
- references to generated resources

If you cannot explain the contract from the manifest, you do not understand the platform yet.

### 2.2 Scenario B: Provision a Team Workspace

You are asked to create a team workspace or app platform through self-service.

Common outcomes:
- namespace creation
- quota or limit configuration
- baseline policy attachment
- app scaffold or deployment template
- access configured through RBAC or identity bindings

You should not patch the generated resources manually unless the exam explicitly asks you to. The point is to use the contract.

### 2.3 Scenario C: Troubleshoot Reconciliation

A claim or custom resource stays stuck.

Use this sequence:
1. read the custom resource
2. inspect `status.conditions`
3. inspect events
4. inspect backing resources
5. check RBAC and admission rules

The failure is usually one of three things:
- the input is invalid
- the controller is blocked
- a dependent resource failed to create

### 2.4 Scenario D: Decide Whether to Build or Consume

CNPE may ask for a platform capability that sounds new.

Ask:
- does the track already provide a CRD, template, or operator for this?
- is the missing piece a configuration issue rather than a new API?
- can the same outcome be solved through a portal template instead of custom code?

The right answer on an exam is usually the one that changes the least while producing the correct platform behavior.

## Part 3: Reading Status Well

The platform user should not guess.

Practice reading:
- `kubectl get <resource> -o yaml`
- `kubectl describe <resource>`
- `kubectl get events -A`
- controller logs if available
- status conditions on the custom resource

If the status says `NotReady`, your first job is to find out why, not to overwrite the resource blindly.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---------|---------|-----------------|
| Editing generated resources directly | You fight the controller and create drift | Fix the claim, template, or composition |
| Treating the CRD as the whole solution | The contract exists but nothing reconciles it | Check the controller and status path |
| Ignoring conditions | You miss the reason the resource is blocked | Read status before making changes |
| Rebuilding the platform API from scratch | You waste time and may violate the exam intent | Consume the existing abstraction if possible |
| Skipping RBAC checks | Self-service fails for non-obvious permission reasons | Verify access early |

## Did You Know?

- Good platform APIs make users feel like they are working with a product instead of a pile of YAML.
- In a healthy self-service system, the user spends more time reading status than editing generated objects.
- A small number of well-designed claims often deliver more value than a large number of low-quality templates.

## Hands-On Exercise

**Task**: Build a simple self-service mental model.

**Steps**:
1. Pick one CRD or platform template from the platform track.
2. Identify the user-facing fields in `spec`.
3. Identify the reconciliation signals in `status` or events.
4. Describe what resource(s) get created behind the scenes.
5. Decide whether you would solve a new request by extending the contract or by consuming what already exists.

**Success Criteria**:
- [ ] You can explain the contract in plain language
- [ ] You can point to one status signal that tells you whether the resource is healthy
- [ ] You can describe the generated resources without opening the controller code

**Verification**:
```bash
kubectl get <custom-resource> -o yaml
kubectl describe <custom-resource>
kubectl get events -A --sort-by=.lastTimestamp | tail -n 15
```

## Quiz

1. Why is a platform API more than just YAML?
   <details>
   <summary>Answer</summary>
   Because the API is a contract between user intent and platform implementation. It includes validation, reconciliation, feedback, and ownership of the resulting resources.
   </details>

2. What is the first place to look when a claim is stuck?
   <details>
   <summary>Answer</summary>
   Start with the custom resource itself: spec, status, conditions, and events. That usually tells you whether the issue is user input, controller health, or a dependent resource.
   </details>

3. When should you author a new API instead of consuming an existing one?
   <details>
   <summary>Answer</summary>
   Only when the existing abstractions cannot express the required platform outcome. If a template or existing claim can satisfy the request, prefer that because it keeps the platform simpler.
   </details>

4. Why is vCluster relevant to CNPE?
   <details>
   <summary>Answer</summary>
   Because it solves a common platform problem: tenant isolation and ephemeral environments. It is one way to provide self-service safely when multiple users or teams need separated control planes.
   </details>

## Next Module

Continue with [CNPE Observability, Security, and Operations Lab](./module-1.4-observability-security-and-operations-lab/), where the platform contract is judged by its signals, policies, and incident response behavior.
