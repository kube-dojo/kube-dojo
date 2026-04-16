---
title: "CGOA Practice Questions Set 2"
slug: k8s/cgoa/module-1.5-practice-questions-set-2
sidebar:
  order: 105
---

> **CGOA Track** | Practice questions | Set 2

## How To Use This Set

This set leans harder into comparisons. The exam is very likely to ask you to distinguish GitOps from adjacent practices and to recognize the role of the main GitOps tools.

## Questions

### 1. Which statement about GitOps principles is correct?

1. GitOps is primarily about using YAML instead of JSON.
2. The four principles describe a pull-based control loop around declarative desired state.
3. GitOps only applies to application code.
4. GitOps and IaC are synonyms.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The principle set is about the operating model, not the file format. The control loop is the part to remember.
</details>

### 2. Which scenario best fits GitOps?

1. A team manually applies hotfixes directly in production and later documents them in a wiki.
2. A cluster pulls desired state from a versioned repository and reconciles drift automatically.
3. A release is triggered by an email approval chain.
4. An operator uses a shell script to copy manifests into each cluster.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The key signals are versioned desired state, pull-based reconciliation, and automatic drift correction.
</details>

### 3. Which of the following is the best description of Flux?

1. A single application dashboard that stores manifests.
2. A toolkit of specialized controllers for GitOps workflows.
3. A Helm replacement that only renders charts.
4. A CI system for building container images.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Flux is controller-based and modular. Remember its source, kustomize, helm, notification, and image-related controllers.
</details>

### 4. Which of the following is the best description of ArgoCD?

1. An application-centric GitOps controller with UI and CLI support.
2. A policy engine for admission control.
3. A Kubernetes distribution.
4. A database provisioning tool.

<details>
<summary>Answer</summary>

**Correct answer: 1**

ArgoCD is the app-centric GitOps tool in the exam vocabulary. It is a good contrast point to Flux.
</details>

### 5. Which statement about Helm and Kustomize is most accurate?

1. Helm manages reconciliation loops and Kustomize manages controllers.
2. Helm is templating and packaging; Kustomize is patching and overlaying.
3. Kustomize is only for Helm chart testing.
4. Both tools are the same thing with different names.

<details>
<summary>Answer</summary>

**Correct answer: 2**

This is a recurring comparison in GitOps discussions and a likely exam distractor pair.
</details>

## Readiness Check

If you can explain why 2 is correct for questions 1, 2, and 3 without repeating the wording of the question, you likely understand the core GitOps model well enough for CGOA.

## Final Review Notes

- GitOps is about desired state, reconciliation, and trust in the source of truth.
- ArgoCD and Flux share the GitOps goal but differ in architecture and emphasis.
- Helm and Kustomize are supporting tools, not the GitOps control loop itself.
