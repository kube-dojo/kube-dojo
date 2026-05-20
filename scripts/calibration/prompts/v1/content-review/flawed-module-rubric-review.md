Review this deliberately flawed module against `docs/quality-rubric.md`.

Output a JSON list of failing rubric criteria with file:line evidence. Do not
enumerate passing criteria.

```markdown
---
title: Kubernetes RBAC Quick Guide
sidebar:
  order: 42
---

# Kubernetes RBAC Quick Guide

RBAC is simply a way to give users permissions. This module explains the
basics.

## Learn outcomes

- Understand RBAC
- Know Roles

## Lab

Run:

```bash
kubectl auth reconcile --remove-extra-permission -f role.yaml
```

This command always removes every extra permission cluster-wide.

## Diagram

No diagram is needed because RBAC is intuitive.

## Sources

- Kubernetes RBAC docs: https://kubernetes.io/docs/reference/access-authn-authz/rbac-missing-page/
```

Known traps include a hallucinated kubectl flag, missing IPA tags, wrong header
levels, broken citation, off-by-one Bloom level, missing diagram, duplicate H1,
and banned wording.

