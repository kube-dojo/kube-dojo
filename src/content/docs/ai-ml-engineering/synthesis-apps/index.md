---
title: "Synthesis Apps: Building LLM-Native Applications on Kubernetes"
slug: ai-ml-engineering/synthesis-apps
sidebar:
  order: 0
  label: "Synthesis Apps"
---

> **AI/ML Engineering Track** | Phase 7 | 4-module mini-arc

---

## Why This Section Exists

KubeDojo already teaches the ingredients of modern LLM systems in depth:
vector databases, RAG, inference engines, GPU scheduling, AI agents, MLOps,
and platform operations.
The missing step is synthesis.
Learners can complete those sections and still be left asking how the pieces
become one Kubernetes-native application that starts reliably, communicates
through internal services, survives pod restarts, exposes useful health checks,
and gives the application layer enough failure vocabulary to implement retries
and quality gates.

This mini-arc closes that gap by building one LLM-native application substrate
in four passes.
The first module wires the backing services.
The second module adds the orchestration service and state handling.
The third module gates deployments with automated LLM evals in CI.
The fourth module makes agent behavior observable with OpenTelemetry tracing.
The point is not to celebrate another tool stack; it is to teach the operational
boundaries between the layers so you can replace individual tools later without
losing the architecture.

## The Shape Of The Arc

The arc starts below the application code because that is where many LLM apps
fail first.
If inference and memory are not healthy as Kubernetes services, a LangGraph,
LangChain, LlamaIndex, or custom orchestration layer has no stable substrate.
Once those services are verified, the second module can teach application logic
against known failure modes instead of hoping the backend is fine.
The third module makes evaluation a deployment gate, and the fourth makes the
running system observable, so quality and visibility are part of the delivery
path, not a dashboard someone opens after users complain.

```text
 Module 3.1          Module 3.2          Module 3.3          Module 3.4
+----------------+  +----------------+  +----------------+  +----------------+
| Backing        |->| Orchestration  |->| Eval gates in  |->| Observability  |
| services       |  | service+state  |  | CI             |  | with OTel      |
+----------------+  +----------------+  +----------------+  +----------------+
 vLLM + Qdrant       LangGraph shape     promptfoo/ragas     agent span tree
 GPU + storage       Redis checkpoints   golden/regression   gen_ai.* attrs
 NetworkPolicy       retries + budgets   rollout gate        cost + traces
```

## Modules

| Module | Learning Outcome |
|--------|------------------|
| [3.1 LLM-Native Stack: Inference and Memory on Kubernetes](module-3.1-llm-native-stack-k8s/) | Deploy vLLM and Qdrant as coordinated Kubernetes services, bound by namespace resource policy and NetworkPolicy, then verify and break the stack deliberately. |
| [3.2 Wiring the LLM App: The Orchestration Layer](module-3.2-orchestration-layer/) | Build a Kubernetes-deployed orchestration service that calls the Module 3.1 services, persists state with Redis checkpointing, and handles backend failure modes explicitly. |
| [3.3 Production Gates: LLM Evals in CI](module-3.3-llm-evals-in-ci/) | Gate deployments with automated LLM eval suites in CI — golden-vs-regression thresholds, what to gate on, and where the gate sits in the rollout. |
| [3.4 Agent Observability with OpenTelemetry](module-3.4-agent-observability-otel/) | Trace agent and LLM calls with OpenTelemetry — an agent span tree, token-cost span attributes, and feeding production traces back into the eval set. |

## What This Section Assumes

You should already be comfortable with Kubernetes workload objects, Services,
ConfigMaps, Secrets, PersistentVolumeClaims, and namespace-level policy.
The modules will explain why each object exists in this stack, but they will
not re-teach every Kubernetes primitive from first principles.
If those objects still feel unfamiliar, strengthen the Kubernetes certification
tracks before treating this arc as a build path.

You should also have completed the inference and vector database prerequisites.
Module 3.1 assumes you have seen vLLM as an inference engine and Qdrant as a
vector database before.
The new material here is the coordination layer between them: resource quota,
service discovery, readiness, restart behavior, and verification probes.

## What This Section Does Not Cover

This is not a broad survey of every LLM application framework.
The arc mentions KServe, Ray Serve, BentoML, DeepEval, Promptfoo, and LangFuse
only where they clarify a concrete integration pattern.
You will not deploy all of them in this section.
The goal is to learn the responsibilities they abstract or reinforce.

This is also not an agent-building section.
Module 3.2 uses orchestration vocabulary, but the dedicated framework and agent
material remains in the Frameworks & Agents phase.
Here the question is narrower and more operational:
when the app calls inference, memory, and state services inside a cluster,
what must be true for the request to be reliable?

## Recommended Order

Read the four modules in order.
The first module produces the backing service substrate that the second module
depends on.
The second module gives the application layer the failure-handling vocabulary
that the third module gates on and the fourth observes in production.
Skipping ahead is possible if you already operate this kind of stack, but it
removes the main teaching benefit for most learners.

```text
AI Infrastructure
      |
      v
Synthesis Apps 3.1
      |
      v
Synthesis Apps 3.2
      |
      v
Synthesis Apps 3.3
      |
      v
Synthesis Apps 3.4
      |
      v
Advanced GenAI & Safety
```

## Where This Fits In The Track

This phase sits after AI Infrastructure because you need a working mental model
for inference engines and GPU scheduling before you can design a Kubernetes
application around them.
It sits before Advanced GenAI & Safety because evaluation and safety gates make
more sense once you can see the application path those gates protect.
That placement is intentional: first learn the pieces, then synthesize them,
then harden the resulting system.

| If You Just Finished | Come Here To Practice |
|----------------------|-----------------------|
| Vector Search & RAG | Running the vector database as a managed dependency rather than a local demo. |
| Frameworks & Agents | Giving the orchestration layer stable internal services and explicit failure modes. |
| MLOps & LLMOps | Translating deployment discipline into multi-service LLM application boundaries. |
| AI Infrastructure | Moving from an isolated inference endpoint to a full internal application stack. |

## Output Of The Mini-Arc

By the end of the four modules, you will have a working shape for a private,
Kubernetes-native LLM application.
It will not be a toy notebook and it will not be a black-box platform service.
It will be a service graph whose responsibilities you can name, probe, restart,
restrict, and test.
That is the skill the rest of the AI/ML Engineering track needs when isolated
specializations become one production system.

## Start Here

Begin with [LLM-Native Stack: Inference and Memory on Kubernetes](module-3.1-llm-native-stack-k8s/).
It builds the substrate: GPU allocation, vLLM, Qdrant, internal networking,
readiness, and controlled failure injection.
Once that layer is stable, the next module can safely teach application-level
retry and orchestration logic.
