---
title: "CBA - Certified Backstage Associate"
sidebar:
  order: 0
  label: "CBA"
---
> **Multiple-choice exam** | 90 minutes | Passing score: 66% | $250 USD | **Launched 2025**

## Overview

The CBA (Certified Backstage Associate) validates your understanding of Backstage, the CNCF-incubating Internal Developer Portal created by Spotify. Unlike the Kubernetes certifications, CBA is **not a hands-on exam** -- it's multiple-choice. But don't be fooled: it tests real development knowledge. You need to understand TypeScript, React, plugin architecture, catalog YAML, and production deployment -- not just theory.

**KubeDojo covers ~90% of CBA topics** through our existing Backstage toolkit module, Platform Engineering discipline, and three dedicated CBA modules covering development workflows, plugin development, and catalog/infrastructure.

> **Key difference from other CNCF certs**: CBA is a developer certification. It tests whether you can *build and extend* Backstage, not just *use* it. Think of it as "CKAD for developer portals."

---

## CBA-Specific Modules

These modules cover the areas between KubeDojo's existing Backstage toolkit module and the CBA exam requirements:

| # | Module | Topic | Domains Covered |
|---|--------|-------|-----------------|
| 1 | [Module 1.1: Backstage Developer Workflow](module-1.1-backstage-dev-workflow/) | Monorepo structure, TypeScript essentials, Docker builds, app-config, CLI | Domain 1 (24%) |
| 2 | [Module 1.2: Backstage Plugin Development — Customizing Backstage](module-1.2-backstage-plugin-development/) | Frontend/backend plugins, React/MUI, scaffolder actions, themes, APIs | Domain 4 (32%) |
| 3 | [Module 1.3: Backstage Catalog & Infrastructure](module-1.3-backstage-catalog-infrastructure/) | Entity processors, providers, annotations, auth, deployment, troubleshooting | Domains 2-3 (44%) |

---

## Exam Details

| Detail | Value |
|--------|-------|
| **Certification** | Certified Backstage Associate (CBA) |
| **Issued by** | The Linux Foundation / CNCF |
| **Format** | Multiple-choice |
| **Duration** | 90 minutes |
| **Questions** | ~60 |
| **Passing score** | 66% |
| **Cost** | $250 USD (includes one free retake) |
| **Validity** | 3 years |
| **Prerequisites** | None (but TypeScript/React experience strongly recommended) |
| **Proctoring** | Online proctored via PSI |

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| Customizing Backstage | 32% | Excellent ([Module 1.2: Backstage Plugin Development — Customizing Backstage](module-1.2-backstage-plugin-development/) — React/MUI, plugins, themes, scaffolder) |
| Backstage Development Workflow | 24% | Excellent ([Module 1.1: Backstage Developer Workflow](module-1.1-backstage-dev-workflow/) — monorepo, TypeScript, Docker, CLI) |
| Backstage Infrastructure | 22% | Excellent ([Module 1.3: Backstage Catalog & Infrastructure](module-1.3-backstage-catalog-infrastructure/) — auth, deployment, production) |
| Backstage Catalog | 22% | Excellent ([Module 1.3: Backstage Catalog & Infrastructure](module-1.3-backstage-catalog-infrastructure/) — processors, providers, annotations) |

---

## Domain 1: Backstage Development Workflow (24%)

### What the Exam Tests
- Creating and running a Backstage app locally
- TypeScript fundamentals for Backstage development
- Monorepo structure (packages/app, packages/backend)
- Docker builds for Backstage
- yarn commands and workspace management
- Development vs production configuration

### KubeDojo Learning Path

**Existing coverage:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Installation, `npx @backstage/create-app`, `yarn dev` | Partial -- covers basic setup only |

**Dedicated CBA module:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Module 1.1: Backstage Developer Workflow](module-1.1-backstage-dev-workflow/) | Monorepo structure, TypeScript essentials, Docker builds, app-config overlays, CLI commands | Direct |

---

## Domain 2: Backstage Infrastructure (22%)

### What the Exam Tests
- Backstage framework architecture (frontend/backend separation)
- Configuration system (`app-config.yaml` hierarchy)
- Database setup (SQLite for dev, PostgreSQL for production)
- Authentication providers (GitHub, Okta, OIDC)
- Deploying Backstage to Kubernetes
- Client-server architecture and API communication
- Proxying external service requests

### KubeDojo Learning Path

**Existing coverage:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Architecture diagram, app-config.yaml, K8s deployment YAML | Direct |
| [Platform Eng 2.3](../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/) | IDP concepts, why portals matter | Background |
| [Platform Eng 2.2](../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) | Developer Experience principles | Background |

**Dedicated CBA module:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Module 1.3: Backstage Catalog & Infrastructure](module-1.3-backstage-catalog-infrastructure/) | Auth providers, proxy, database migrations, production hardening, backend-for-frontend | Direct |

---

## Domain 3: Backstage Catalog (22%)

### What the Exam Tests
- Entity kinds (Component, API, Resource, System, Domain, Group, User, Location, Template)
- `catalog-info.yaml` structure and fields
- Annotations and their purposes
- Entity ingestion methods (static, discovery, processors)
- Automated ingestion (GitHub discovery, entity providers)
- Entity relationships (ownerOf, partOf, consumesApi, providesApi, dependsOn)
- Troubleshooting catalog issues (orphaned entities, refresh failures)
- Well-known annotations (`backstage.io/techdocs-ref`, `github.com/project-slug`, etc.)

### KubeDojo Learning Path

**Existing coverage:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Entity types, catalog-info.yaml, relationships, annotations, auto-discovery | Direct |
| [Platform Eng 2.4](../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) | Golden paths concept (templates use catalog) | Background |
| [Platform Eng 2.5](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/) | Self-service concepts | Background |

**Dedicated CBA module:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Module 1.3: Backstage Catalog & Infrastructure](module-1.3-backstage-catalog-infrastructure/) | Entity processors, providers, all annotations, troubleshooting, Location kind, lifecycle management | Direct |

---

## Domain 4: Customizing Backstage (32%)

### What the Exam Tests
- Frontend plugin development (React components)
- Backend plugin development (Express routers)
- React fundamentals for Backstage (hooks, state, props)
- Material UI (MUI) components and theming
- Backstage plugin APIs (`createPlugin`, `createRoutableExtension`, `createApiRef`)
- Creating custom themes
- Adding pages and tabs to the entity view
- Scaffolder custom actions
- Extension points and overrides

### KubeDojo Learning Path

**Existing coverage:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Plugin ecosystem overview, basic plugin code snippet | Minimal |

**Dedicated CBA module:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Module 1.2: Backstage Plugin Development — Customizing Backstage](module-1.2-backstage-plugin-development/) | React/MUI, frontend/backend plugins, scaffolder actions, themes, extension points | Direct |

---

## Gap Analysis Summary

Our existing Backstage module (7.1) provides a toolkit overview, and three dedicated CBA modules now cover the exam in depth: development workflows, plugin development, and catalog/infrastructure operations.

### Coverage Breakdown

```
KUBEDOJO CBA COVERAGE
════════════════════════════════════════════════════════════════

Domain 1: Development Workflow (24%)    █████████░  ~90% covered
Domain 2: Infrastructure (22%)          █████████░  ~90% covered
Domain 3: Catalog (22%)                 █████████░  ~90% covered
Domain 4: Customizing Backstage (32%)   █████████░  ~90% covered

Overall weighted coverage:              ~90%
```

### CBA Modules

| Module | Topics | Domains Covered |
|--------|--------|-----------------|
| [Module 1.1: Backstage Developer Workflow](module-1.1-backstage-dev-workflow/) | Monorepo structure, TypeScript essentials, Docker builds, app-config overlays, CLI commands, local dev workflow | Domain 1 (24%) |
| [Module 1.2: Backstage Plugin Development — Customizing Backstage](module-1.2-backstage-plugin-development/) | Frontend plugins (React/MUI), backend plugins (Express), scaffolder custom actions, custom themes, extension points, API refs | Domain 4 (32%) |
| [Module 1.3: Backstage Catalog & Infrastructure](module-1.3-backstage-catalog-infrastructure/) | Entity processors, entity providers, all annotations, auth, production deployment, troubleshooting | Domains 2-3 (44%) |

These three modules plus the existing Module 7.1 provide comprehensive CBA preparation.

---

## Study Strategy

```
CBA PREPARATION PATH (4-week plan)
══════════════════════════════════════════════════════════════

Week 1: Foundations & Catalog (Domains 2-3, 44% of exam)
├── Platform Engineering 2.1-2.3 (IDP concepts)
├── Backstage 7.1 (architecture, catalog, templates)
├── Install Backstage locally, explore the catalog
├── Practice writing catalog-info.yaml for different entity kinds
└── Study all entity relationships and annotations

Week 2: Development Workflow (Domain 1, 24% of exam)
├── Set up local Backstage dev environment
├── Explore monorepo: packages/app, packages/backend
├── Understand app-config.yaml hierarchy and env substitution
├── Practice Docker builds (host build + multi-stage)
├── Learn Backstage CLI commands
└── KubeDojo: Module 1.1: Backstage Developer Workflow

Week 3: Customizing Backstage (Domain 4, 32% of exam!)
├── React fundamentals: components, hooks, props, state
├── Material UI: common components, theming, sx prop
├── Build a frontend plugin from scratch
├── Build a backend plugin with Express router
├── Create a custom scaffolder action
└── KubeDojo: Module 1.2: Backstage Plugin Development — Customizing Backstage

Week 4: Review & Practice
├── Review all 4 domains
├── Focus on Domain 4 (32%) -- biggest weight
├── Practice catalog troubleshooting scenarios
├── Review Backstage official documentation gaps
└── Take practice questions if available
```

### Priority Study Order

The CBA weights Customizing Backstage at **32%** -- nearly a third of the exam. Combined with Development Workflow (24%), that means **56% of the exam is about writing code**. If you're coming from an ops background, budget extra time for React and TypeScript.

```
STUDY TIME ALLOCATION (by exam weight)
══════════════════════════════════════════════════════════════

Customizing Backstage (32%)     ████████████████  ← Start weak? Study most
Development Workflow (24%)      ████████████
Backstage Catalog (22%)         ███████████
Backstage Infrastructure (22%)  ███████████
```

---

## Exam Tips

- **This is a code-reading exam.** Many questions show TypeScript/React snippets and ask what they do. You don't write code, but you need to *understand* it.
- **Know the plugin APIs by heart.** `createPlugin`, `createRoutableExtension`, `createApiRef`, `createBackendPlugin` -- know what each does and when to use it.
- **Catalog YAML is heavily tested.** Practice writing `catalog-info.yaml` from memory. Know every entity kind, annotation, and relationship type.
- **Don't skip Material UI.** Questions test specific MUI components (`Grid`, `Card`, `Table`, `InfoCard`) and how they're used in Backstage.
- **Understand the config hierarchy.** Know how `app-config.yaml`, `app-config.local.yaml`, and `app-config.production.yaml` merge and override. Know how `${VAR}` environment substitution works.
- **Focus on the "why."** The exam tests understanding of architectural decisions -- *why* Backstage separates frontend and backend plugins, *why* the catalog uses a descriptor format, *why* Software Templates use a step-based workflow.
- **Read the official Backstage docs.** The exam is closely aligned with [backstage.io/docs](https://backstage.io/docs). The "Getting Started" and "Plugin Development" sections are especially relevant.
- **TypeScript is non-negotiable.** If you don't know TypeScript, spend a few days on the basics before starting CBA prep. Focus on: types, interfaces, generics, async/await, and module imports.

---

## Essential Resources

- [Backstage Official Documentation](https://backstage.io/docs/) -- primary study source
- [Backstage GitHub Repository](https://github.com/backstage/backstage) -- read plugin source code
- [Backstage Storybook](https://backstage.io/storybook) -- see MUI components in action
- [CNCF CBA Curriculum](https://github.com/cncf/curriculum) -- official exam objectives
- [Backstage Community Plugins](https://backstage.io/plugins) -- understand the ecosystem

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Developer Portal:
└── CBA (Backstage Associate) ← YOU ARE HERE

Platform Engineering:
├── KCNA (Cloud Native Associate) — K8s fundamentals
├── CNPA (Platform Engineering Associate) — Platform basics
└── CNPE (Platform Engineer) — Hands-on platform engineering

Kubernetes:
├── CKA (K8s Administrator) — Cluster operations
├── CKAD (K8s Developer) — Application deployment
└── CKS (K8s Security Specialist) — Security hardening
```

The CBA pairs well with the **CNPE** (Certified Cloud Native Platform Engineer). CNPE tests building platforms; CBA tests building the portal that sits on top. Together, they validate end-to-end platform engineering skills. If you're pursuing the Kubestronaut path, CBA is a complementary certification that deepens your platform tooling expertise.

---

## KubeDojo Modules Referenced

| Module | Path | CBA Relevance |
|--------|------|---------------|
| Backstage 7.1 | [module-7.1-backstage.md](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Core -- architecture, catalog, templates, plugins overview |
| Platform Eng 2.1 | [module-2.1-what-is-platform-engineering.md](../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/) | Background -- what platform engineering is |
| Platform Eng 2.2 | [module-2.2-developer-experience.md](../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) | Background -- DevEx principles |
| Platform Eng 2.3 | [module-2.3-internal-developer-platforms.md](../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/) | Background -- IDP concepts |
| Platform Eng 2.4 | [module-2.4-golden-paths.md](../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) | Background -- golden paths (templates) |
| Platform Eng 2.5 | [module-2.5-self-service-infrastructure.md](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/) | Background -- self-service concepts |
| Platform Eng 2.6 | [module-2.6-platform-maturity.md](../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/) | Background -- maturity models |