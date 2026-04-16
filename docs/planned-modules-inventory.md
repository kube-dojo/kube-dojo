# Planned Modules Inventory

## Purpose

This document consolidates the repo's current planned-module backlog into one source of truth.

It distinguishes between:
- `planned-only` — tracked in issues, no module file yet
- `placeholder` — scaffold page exists, content not written
- `content-file` — module file exists already, regardless of review quality

## Issue Map

| Issue | Scope | Status |
|---|---|---|
| [#198](https://github.com/kube-dojo/kube-dojo.github.io/issues/198) | Master execution plan | umbrella only |
| [#197](https://github.com/kube-dojo/kube-dojo.github.io/issues/197) | On-prem expansion | mostly `content-file`, 1 known missing module |
| [#199](https://github.com/kube-dojo/kube-dojo.github.io/issues/199) | AI/ML migration + modernization | base track exists, modernization expansion partly concrete |
| [#244](https://github.com/kube-dojo/kube-dojo.github.io/issues/244) | AI/ML learner-path gaps | fully `content-file` |
| [#182](https://github.com/kube-dojo/kube-dojo.github.io/issues/182) | Missing certification prep tracks | normalized `planned-only` modules |
| [#183](https://github.com/kube-dojo/kube-dojo.github.io/issues/183) | CKA mock exam modules | `planned-only` and deferred |

## Current Inventory

### 1. On-Prem Expansion (`#197`)

Status summary:
- 21 modules planned
- 21 module files already exist
- no known missing module files in this expansion slice

| Module | Path | Status |
|---|---|---|
| 1.5 On-Prem FinOps & Chargeback | `src/content/docs/on-premises/planning/module-1.5-onprem-finops-chargeback.md` | `content-file` |
| 3.5 Cross-Cluster Networking | `src/content/docs/on-premises/networking/module-3.5-cross-cluster-networking.md` | `content-file` |
| 3.6 Service Mesh on Bare Metal | `src/content/docs/on-premises/networking/module-3.6-service-mesh-bare-metal.md` | `content-file` |
| 4.4 Object Storage on Bare Metal | `src/content/docs/on-premises/storage/module-4.4-object-storage-bare-metal.md` | `content-file` |
| 4.5 Database Operators | `src/content/docs/on-premises/storage/module-4.5-database-operators.md` | `content-file` |
| 5.4 Fleet Management | `src/content/docs/on-premises/multi-cluster/module-5.4-fleet-management.md` | `content-file` |
| 5.5 Active-Active Multi-Site | `src/content/docs/on-premises/multi-cluster/module-5.5-active-active-multi-site.md` | `content-file` |
| 6.5 Workload Identity with SPIFFE/SPIRE | `src/content/docs/on-premises/security/module-6.5-workload-identity-spiffe.md` | `content-file` |
| 6.6 Secrets Management on Bare Metal | `src/content/docs/on-premises/security/module-6.6-secrets-management-vault.md` | `content-file` |
| 6.7 Policy as Code & Governance | `src/content/docs/on-premises/security/module-6.7-policy-as-code.md` | `content-file` |
| 6.8 Zero Trust Architecture | `src/content/docs/on-premises/security/module-6.8-zero-trust-architecture.md` | `content-file` |
| 7.6 Self-Hosted CI/CD | `src/content/docs/on-premises/operations/module-7.6-self-hosted-cicd.md` | `content-file` |
| 7.7 Self-Hosted Container Registry | `src/content/docs/on-premises/operations/module-7.7-self-hosted-registry.md` | `content-file` |
| 7.8 Observability at Scale | `src/content/docs/on-premises/operations/module-7.8-observability-at-scale.md` | `content-file` |
| 7.9 Serverless on Bare Metal | `src/content/docs/on-premises/operations/module-7.9-serverless-bare-metal.md` | `content-file` |
| 9.1 GPU Nodes & Accelerated Computing | `src/content/docs/on-premises/ai-ml-infrastructure/module-9.1-gpu-nodes-accelerated.md` | `content-file` |
| 9.2 Private AI Training Infrastructure | `src/content/docs/on-premises/ai-ml-infrastructure/module-9.2-private-ai-training.md` | `content-file` |
| 9.3 Private LLM Serving | `src/content/docs/on-premises/ai-ml-infrastructure/module-9.3-private-llm-serving.md` | `content-file` |
| 9.4 Private MLOps Platform | `src/content/docs/on-premises/ai-ml-infrastructure/module-9.4-private-mlops-platform.md` | `content-file` |
| 9.5 Private AIOps | `src/content/docs/on-premises/ai-ml-infrastructure/module-9.5-private-aiops.md` | `content-file` |
| 9.6 High-Performance Storage for AI | `src/content/docs/on-premises/ai-ml-infrastructure/module-9.6-high-performance-storage-ai.md` | `content-file` |

Note:
- `#197` is fully materialized as module files in the repo, but still needs normal review / quality tracking rather than placeholder tracking.

### 2. AI/ML Learner-Path Expansion (`#244`, parent `#199`)

Status summary:
- 10 modules planned
- 10 real content files exist

| Module | Path | Status |
|---|---|---|
| 1.2 Home AI Workstation Fundamentals | `src/content/docs/ai-ml-engineering/prerequisites/module-1.2-home-ai-workstation-fundamentals.md` | `content-file` |
| 1.3 Reproducible Python, CUDA, and ROCm Environments | `src/content/docs/ai-ml-engineering/prerequisites/module-1.3-reproducible-python-cuda-rocm-environments.md` | `content-file` |
| 1.4 Notebooks, Scripts, and Project Layouts | `src/content/docs/ai-ml-engineering/prerequisites/module-1.4-notebooks-scripts-project-layouts.md` | `content-file` |
| 1.6 Home-Scale RAG Systems | `src/content/docs/ai-ml-engineering/vector-rag/module-1.6-home-scale-rag-systems.md` | `content-file` |
| 1.11 Notebooks to Production for ML/LLMs | `src/content/docs/ai-ml-engineering/mlops/module-1.11-notebooks-to-production-for-ml-llms.md` | `content-file` |
| 1.12 Small-Team Private AI Platform | `src/content/docs/ai-ml-engineering/mlops/module-1.12-small-team-private-ai-platform.md` | `content-file` |
| 1.10 Single-GPU Local Fine-Tuning | `src/content/docs/ai-ml-engineering/advanced-genai/module-1.10-single-gpu-local-fine-tuning.md` | `content-file` |
| 1.11 Multi-GPU and Home-Lab Fine-Tuning | `src/content/docs/ai-ml-engineering/advanced-genai/module-1.11-multi-gpu-home-lab-fine-tuning.md` | `content-file` |
| 1.4 Local Inference Stack for Learners | `src/content/docs/ai-ml-engineering/ai-infrastructure/module-1.4-local-inference-stack-for-learners.md` | `content-file` |
| 1.5 Home AI Operations and Cost Model | `src/content/docs/ai-ml-engineering/ai-infrastructure/module-1.5-home-ai-operations-cost-model.md` | `content-file` |

### 3. AI/ML Migration and Modernization (`#199`)

Status summary:
- The base AI/ML Engineering track already exists as migrated content
- `#199` is partly structural and modernization-focused, not a clean standalone module list
- The concrete learner-path additions under this umbrella are tracked in `#244`

Explicit new-content requirement from `#199`:
- add at least 5 new 2026-relevant modules during modernization

Current state:
- the `#244` learner-path modules already satisfy that requirement in quantity
- most of the named 2026 topics in `#199` are already represented by existing modules
- the last clear missing-module gap from this slice is now materialized

| Module | Path | Status |
|---|---|---|
| Anthropic Agent SDK and Runtime Patterns | `src/content/docs/ai-ml-engineering/ai-native-development/module-1.10-anthropic-agent-sdk-and-runtime-patterns.md` | `content-file` |

### 4. Missing Certification Prep Tracks (`#182`)

Status summary:
- 4 tracks planned
- directories and exam-prep modules now exist
- the remaining work is review and quality hardening, not missing-file creation

| Track | Directory | Planned State |
|---|---|---|
| LFCS | `src/content/docs/k8s/lfcs/` | `content-file` |
| CNPE | `src/content/docs/k8s/cnpe/` | `content-file` |
| CNPA | `src/content/docs/k8s/cnpa/` | `content-file` |
| CGOA | `src/content/docs/k8s/cgoa/` | `content-file` |

Normalized exact missing modules:

| Module | Path | Status |
|---|---|---|
| LFCS Exam Strategy and Workflow | `src/content/docs/k8s/lfcs/module-1.1-exam-strategy-and-workflow.md` | `content-file` |
| LFCS Essential Commands Practice | `src/content/docs/k8s/lfcs/module-1.2-essential-commands-practice.md` | `content-file` |
| LFCS Running Systems and Networking Practice | `src/content/docs/k8s/lfcs/module-1.3-running-systems-and-networking-practice.md` | `content-file` |
| LFCS Storage, Services, and Users Practice | `src/content/docs/k8s/lfcs/module-1.4-storage-services-and-users-practice.md` | `content-file` |
| LFCS Full Mock Exam | `src/content/docs/k8s/lfcs/module-1.5-full-mock-exam.md` | `content-file` |
| CNPE Exam Strategy and Environment | `src/content/docs/k8s/cnpe/module-1.1-exam-strategy-and-environment.md` | `content-file` |
| CNPE GitOps and Delivery Lab | `src/content/docs/k8s/cnpe/module-1.2-gitops-and-delivery-lab.md` | `content-file` |
| CNPE Platform APIs and Self-Service Lab | `src/content/docs/k8s/cnpe/module-1.3-platform-apis-and-self-service-lab.md` | `content-file` |
| CNPE Observability, Security, and Operations Lab | `src/content/docs/k8s/cnpe/module-1.4-observability-security-and-operations-lab.md` | `content-file` |
| CNPE Full Mock Exam | `src/content/docs/k8s/cnpe/module-1.5-full-mock-exam.md` | `content-file` |
| CNPA Exam Strategy and Blueprint Review | `src/content/docs/k8s/cnpa/module-1.1-exam-strategy-and-blueprint-review.md` | `content-file` |
| CNPA Core Platform Fundamentals Review | `src/content/docs/k8s/cnpa/module-1.2-core-platform-fundamentals-review.md` | `content-file` |
| CNPA Delivery, APIs, and Observability Review | `src/content/docs/k8s/cnpa/module-1.3-delivery-apis-and-observability-review.md` | `content-file` |
| CNPA Practice Questions Set 1 | `src/content/docs/k8s/cnpa/module-1.4-practice-questions-set-1.md` | `content-file` |
| CNPA Practice Questions Set 2 | `src/content/docs/k8s/cnpa/module-1.5-practice-questions-set-2.md` | `content-file` |
| CGOA Exam Strategy and Blueprint Review | `src/content/docs/k8s/cgoa/module-1.1-exam-strategy-and-blueprint-review.md` | `content-file` |
| CGOA GitOps Principles Review | `src/content/docs/k8s/cgoa/module-1.2-gitops-principles-review.md` | `content-file` |
| CGOA Patterns and Tooling Review | `src/content/docs/k8s/cgoa/module-1.3-patterns-and-tooling-review.md` | `content-file` |
| CGOA Practice Questions Set 1 | `src/content/docs/k8s/cgoa/module-1.4-practice-questions-set-1.md` | `content-file` |
| CGOA Practice Questions Set 2 | `src/content/docs/k8s/cgoa/module-1.5-practice-questions-set-2.md` | `content-file` |

### 5. CKA Mock Exams (`#183`)

Status summary:
- section directory exists
- index exists
- module count is zero
- deferred exact slots are now named for queue clarity
- intentionally deferred for now

| Item | Path | Status |
|---|---|---|
| CKA Part 6 Mock Exams | `src/content/docs/k8s/cka/part6-mock-exams/` | `planned-only` |
| CKA Mock Exam: Cluster Architecture and Troubleshooting | `src/content/docs/k8s/cka/part6-mock-exams/module-6.1-cluster-architecture-and-troubleshooting.md` | `planned-only` |
| CKA Mock Exam: Workloads, Networking, and Storage | `src/content/docs/k8s/cka/part6-mock-exams/module-6.2-workloads-networking-and-storage.md` | `planned-only` |
| CKA Mock Exam: Full Mixed-Domain Exam | `src/content/docs/k8s/cka/part6-mock-exams/module-6.3-full-mixed-domain-mock-exam.md` | `planned-only` |

Issue expectation:
- 3 to 5 realistic mock exam modules

## Practical Reading

If the question is "what is already visible in the repo versus still only planned?", the answer is:

- `#197` on-prem expansion is mostly already materialized as content files
- `#244` AI/ML learner-path expansion is fully materialized as content files
- `#182` is now materialized as real exam-prep content files
- `#183` remains real backlog, but explicitly deferred
- `#199` no longer has a clear missing-module slice beyond `#244`; remaining work is mainly modernization and quality refinement

## Recommended Next Cleanup

1. Keep this document updated when a planned module moves from `planned-only` -> `content-file`.
2. Keep `#182` under review/quality tracking rather than missing-module tracking.
3. Treat the remaining work under `#199` as quality modernization rather than missing-module creation unless a new exact gap is identified.
