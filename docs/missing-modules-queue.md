# Missing Modules Queue

## Purpose

This is the execution queue for all currently missing modules, not just the first AI/ML learner-path slice.

It separates:
- `exact` backlog: modules with a concrete planned file/slot
- `deferred` backlog: explicitly real, but intentionally not on the active execution path

## Queue Summary

### Exact Missing Modules

These are concrete missing modules already identified by name and placement.

#### AI/ML Learner-Path (`#244`)
Status: `0 exact missing modules`

Completed:
1. `ai-ml-engineering/prerequisites/module-1.2-home-ai-workstation-fundamentals`
2. `ai-ml-engineering/prerequisites/module-1.3-reproducible-python-cuda-rocm-environments`
3. `ai-ml-engineering/prerequisites/module-1.4-notebooks-scripts-project-layouts`
4. `ai-ml-engineering/vector-rag/module-1.6-home-scale-rag-systems`
5. `ai-ml-engineering/mlops/module-1.11-notebooks-to-production-for-ml-llms`
6. `ai-ml-engineering/mlops/module-1.12-small-team-private-ai-platform`
7. `ai-ml-engineering/advanced-genai/module-1.10-single-gpu-local-fine-tuning`
8. `ai-ml-engineering/advanced-genai/module-1.11-multi-gpu-home-lab-fine-tuning`
9. `ai-ml-engineering/ai-infrastructure/module-1.4-local-inference-stack-for-learners`
10. `ai-ml-engineering/ai-infrastructure/module-1.5-home-ai-operations-cost-model`

#### Certification Prep Tracks (`#182`)
Status: `0 exact missing modules`

These tracks now have real exam-prep module content on top of their hubs.

##### LFCS
Completed:
1. `k8s/lfcs/module-1.1-exam-strategy-and-workflow`
2. `k8s/lfcs/module-1.2-essential-commands-practice`
3. `k8s/lfcs/module-1.3-running-systems-and-networking-practice`
4. `k8s/lfcs/module-1.4-storage-services-and-users-practice`
5. `k8s/lfcs/module-1.5-full-mock-exam`

##### CNPE
1. `k8s/cnpe/module-1.1-exam-strategy-and-environment`
2. `k8s/cnpe/module-1.2-gitops-and-delivery-lab`
3. `k8s/cnpe/module-1.3-platform-apis-and-self-service-lab`
4. `k8s/cnpe/module-1.4-observability-security-and-operations-lab`
5. `k8s/cnpe/module-1.5-full-mock-exam`

##### CNPA
1. `k8s/cnpa/module-1.1-exam-strategy-and-blueprint-review`
2. `k8s/cnpa/module-1.2-core-platform-fundamentals-review`
3. `k8s/cnpa/module-1.3-delivery-apis-and-observability-review`
4. `k8s/cnpa/module-1.4-practice-questions-set-1`
5. `k8s/cnpa/module-1.5-practice-questions-set-2`

##### CGOA
1. `k8s/cgoa/module-1.1-exam-strategy-and-blueprint-review`
2. `k8s/cgoa/module-1.2-gitops-principles-review`
3. `k8s/cgoa/module-1.3-patterns-and-tooling-review`
4. `k8s/cgoa/module-1.4-practice-questions-set-1`
5. `k8s/cgoa/module-1.5-practice-questions-set-2`

#### AI/ML Modernization Adds (`#199`)
Status: `0 exact missing modules`

The broad modernization ask in `#199` is now materially satisfied by the migrated track, the completed learner-path additions from `#244`, and the new Agent SDK runtime module in AI-Native Development.

### Deferred Missing Modules

These are real backlog items, but not on the active build path right now.

#### CKA Mock Exams (`#183`)
Status: `deferred 3-5 missing modules`

Section:
1. `k8s/cka/part6-mock-exams`

Issue expectation:
- `3-5` realistic mock exam modules

## Current Total

### Deterministic minimum

- `0` exact missing modules
- `0` active estimated modules
- `0` minimum total active missing modules

### Estimated upper bound from current issue text

- `0` exact missing modules
- `0` active estimated modules
- `0` likely upper bound for active missing modules

## Execution Rule

1. The `#244` AI/ML learner-path placeholder backlog is complete.
2. Treat `#182` as review/quality work rather than missing-module creation.
3. Reassess `#199` as modernization/quality work rather than missing-module creation.
4. Keep section `index.md` files in sync whenever a module moves from planned to real content.

## Important Exclusions

- `#197` On-Prem expansion is not in the missing-modules queue because those modules already exist as content files.
- `#183` CKA mock exams are intentionally deferred for now by product direction, even though they remain backlog.
- Existing modules that need quality improvement are backlog, but they are not "missing modules."
