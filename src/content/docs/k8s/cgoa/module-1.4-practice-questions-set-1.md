---
title: "CGOA Practice Questions Set 1"
slug: k8s/cgoa/module-1.4-practice-questions-set-1
sidebar:
  order: 104
---

> **CGOA Track** | Practice questions | Set 1

## How To Use This Set

Answer each question before reading the explanation. If you can explain why the other options are wrong, you are in good shape.

## Questions

### 1. What is the best short description of GitOps?

1. Storing all Kubernetes YAML in a Git repository.
2. A pull-based operating model where desired state is declared in Git and continuously reconciled.
3. Any deployment workflow that uses pull requests.
4. A replacement for CI/CD.

<details>
<summary>Answer</summary>

**Correct answer: 2**

That answer includes both the declaration of desired state and the continuous reconciliation loop. The other options are incomplete or too broad.
</details>

### 2. Which statement best describes a state drift?

1. The cluster is healthy and Git matches actual state.
2. The desired state and actual state no longer match.
3. A change approved in a pull request.
4. A rollback to a previous commit.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Drift is the mismatch between desired and actual state. It is the condition GitOps systems are meant to detect and correct.
</details>

### 3. What is the clearest difference between GitOps and CI/CD?

1. GitOps is only for developers; CI/CD is only for operators.
2. GitOps is a desired-state and reconciliation model; CI/CD is the build/test/delivery pipeline.
3. CI/CD always uses pull-based reconciliation.
4. GitOps does not use Git.

<details>
<summary>Answer</summary>

**Correct answer: 2**

They can work together, but they solve different problems. That distinction is central to the exam.
</details>

### 4. Which tool pairing is the most accurate?

1. Helm templates, Kustomize patches
2. Helm reconciles drift, Kustomize manages secrets
3. ArgoCD renders JSON only, Flux renders YAML only
4. Flux is a chart packaging tool, Helm is a controller

<details>
<summary>Answer</summary>

**Correct answer: 1**

Helm and Kustomize are common manifest-generation and customization tools. The other statements swap tool responsibilities incorrectly.
</details>

### 5. Which option best captures why pull-based GitOps is preferred?

1. It avoids all networking concerns.
2. It allows the target environment to fetch and reconcile desired state without giving external systems push access.
3. It eliminates the need for Git.
4. It makes deployments manual again.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Pull-based systems reduce exposed credentials and fit the reconciliation model described by OpenGitOps.
</details>

## Review Notes

- If you picked 1 on question 1, you are missing the reconciliation model.
- If you picked 4 on question 4, revisit the Helm and Kustomize comparison.
- If you picked 3 on question 5, the question is explicitly about why Git stays central.

## Next Module

Continue with [CGOA Practice Questions Set 2](./module-1.5-practice-questions-set-2/).
