---
revision_pending: false
title: "Module 7.1: Backstage"
slug: platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 75-90 minutes | **Track**: Toolkits

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Backstage as an internal developer portal with a software catalog and software templates that encode your organization's golden paths**
- **Configure Backstage plugins for CI/CD visibility, Kubernetes dashboards, and documentation integration so developers see operational context beside catalog metadata**
- **Implement software templates for standardized service scaffolding with built-in compliance guardrails such as ownership, repository settings, and catalog registration**
- **Integrate Backstage with existing toolchain components including GitHub, Argo CD, and PagerDuty to present a unified developer experience without replacing those systems**

## Why This Module Matters

Platform teams invest heavily in Kubernetes clusters, GitOps pipelines, observability stacks, and security tooling, yet developers still spend hours hunting for API documentation, service owners, deployment status, and the approved way to create a new repository. That friction is not a tooling shortage; it is a **discoverability and cognitive-load** problem. An Internal Developer Portal (IDP) addresses it by giving engineers one curated entry point where catalog metadata, documentation, templates, and plugin-driven views connect the dots across systems they already use.

Backstage is an open source **framework** for building such portals—not a single SaaS product with a fixed feature list. Spotify created it to tame microservice sprawl, open-sourced the project, and donated it to the Cloud Native Computing Foundation (CNCF). You adopt Backstage when you want a customizable portal whose core primitives (catalog, TechDocs, scaffolder, search, plugins) map cleanly to platform-engineering outcomes: ownership, self-service, and paved roads. We use Backstage throughout this module as a **worked example** of those durable IDP concepts; the Rosetta table later shows how the same capabilities appear in peer products without ranking them.

> **The Airport Terminal Analogy**
>
> Imagine arriving at an airport where every airline hides its gate behind a different app, the food court has no directory, and baggage claim numbers are posted only in a Slack channel someone forgot to invite you to. That is what developer experience feels like without an IDP. Backstage is the terminal building: a consistent layout where signs (catalog), maps (TechDocs), ticket counters (software templates), and information screens (plugins) help you reach the right destination without memorizing tribal routes.

## Prerequisites and Scope

Before you start, you should understand [Platform Engineering Discipline](/platform/disciplines/core-platform/platform-engineering/) concepts such as golden paths, self-service, and reducing cognitive load. Basic Node.js and Yarn familiarity helps when you customize the frontend or add plugins, and you should be comfortable with Kubernetes fundamentals because many integrations surface cluster state. This module teaches **durable IDP architecture** first and Backstage mechanics second; when a vendor revs a plugin API, the mental model still applies.

## Landscape Snapshot and IDP Rosetta

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> - **Backstage** is an open source framework for building developer portals, originally created at Spotify and **donated to CNCF**. Per the [CNCF project page](https://www.cncf.io/projects/backstage/), Backstage was **accepted to CNCF on September 8, 2020** and **moved to the Incubating maturity level on March 15, 2022**. It remains a **CNCF Incubating** project as of this snapshot—not Graduated.
> - The upstream monorepo's **latest release** as of June 2026 is **v1.52.0** (see [GitHub releases](https://github.com/backstage/backstage/releases)). New apps scaffolded from current templates use modern Yarn tooling; always check release notes before upgrading production instances.
> - **TechDocs** builds documentation with MkDocs-oriented tooling; treat MkDocs plugin versions as part of your upgrade checklist.
> - **Peer IDP products** (Port, Cortex, Kratix, Humanitec, custom portals) ship on independent release trains—compare capabilities in the Rosetta below, not headline marketing claims.

The Rosetta table maps **durable IDP capabilities** (rows) to representative implementations (columns). It is not a scorecard or a "best tool" ranking; it helps you translate requirements ("we need paved-road scaffolding with catalog registration") into architectural choices.

| Capability | Backstage (this module) | Port (getport.io) | Cortex (cortex.io) | Kratix (kratix.io) | Custom in-house portal |
|---|---|---|---|---|---|
| **Service catalog / entity model** | YAML entities (`catalog-info.yaml`) with kinds such as Component, System, API, Resource; graph relationships and ownership | Software catalog with scorecards and blueprints | Service catalog with scorecards and initiatives | Platform promises + CRD-driven delivery; catalog patterns vary by installation | Whatever your team models—often incomplete without explicit entity design |
| **Docs-as-code surfacing** | TechDocs (MkDocs pipeline, `backstage.io/techdocs-ref` annotation) | Embedded docs and spec pages tied to entities | Markdown/README integrations; docs features evolve per release | Docs typically live in Git; portal integration is custom | Confluence links or ad hoc README links—consistency varies |
| **Software templates / golden paths** | Scaffolder (`Template` CRs, actions such as `publish:github`, `catalog:register`) | Self-service actions and blueprints | Scaffolding via templates/initiatives depending on configuration | Promises + pipelines deliver platform capabilities | Cookiecutter scripts or ticket-driven provisioning |
| **Plugin / extensibility model** | Frontend + backend plugins, app configuration, community plugin index | Integrations marketplace | Integrations and API | Kubernetes-native controllers + marketplace patterns | Full custom code—high build cost |
| **Ownership and accountability** | `spec.owner` references Groups/Users; org data from identity providers | Ownership fields on entities | Ownership and team metadata | Team labels on promises | Depends on HR/LDAP sync quality |
| **Operational context (K8s, CI, incidents)** | Plugins (Kubernetes, GitHub Actions, Argo CD, PagerDuty, etc.) | Integration-driven widgets | Integrations for CI, K8s, incidents | Observability via platform pipeline | Usually the first features to break when APIs change |
| **Deployment model** | Self-hosted app (Node backend + Postgres/SQLite); you operate upgrades | SaaS or self-hosted options per vendor docs | SaaS-first with enterprise options | Runs on your Kubernetes cluster | You operate everything |
| **Open source / governance** | Apache-2.0, CNCF Incubating | Commercial product with documented API | Commercial product | Apache-2.0 platform components; CNCF Sandbox for Kratix—verify current status before production bets | Internal IP |

When you evaluate tools, ask which **rows** you must satisfy on day one versus which can wait. Teams that skip catalog ownership and jump straight to flashy dashboards usually rebuild later under incident pressure.

## The Developer Experience Problem

Without a portal, every question sends developers on a scavenger hunt across Confluence, GitHub, Grafana, Argo CD, PagerDuty, and Slack archives. Each hop uses a different search syntax, a different authentication flow, and a different mental model of what "the service" even means. Platform engineers feel this pain during incidents when the on-call engineer cannot find the runbook, the dependency graph, or the team that owns a failing deployment. The cost is not only time; it is **context switching** that erodes flow state and encourages unsafe shortcuts such as copying an old repository without updating CI secrets.

An IDP does not replace your toolchain—it **indexes and contextualizes** it. The catalog answers "what exists and who owns it," TechDocs answers "how it works," templates answer "how we create the next one correctly," and plugins answer "what is happening right now in systems X and Y." Backstage implements those four answers as first-class features with a shared entity graph, which is why it appears frequently in platform-engineering reference architectures. The ASCII sketch below contrasts the scattered workflow with a portal-centered workflow; read it as a capability map, not a promise that every installation ships every plugin on day one.

```
WITHOUT INTERNAL DEVELOPER PORTAL          WITH BACKSTAGE (ILLUSTRATIVE)
════════════════════════════════════       ═══════════════════════════════
Find API docs     -> Search 4 systems       -> Catalog -> Component -> Docs
Find owner        -> Slack + git blame       -> Catalog -> Owner -> Group
Create service    -> Copy old repo           -> Create -> Template wizard
Deploy status     -> Open Argo CD UI          -> Component -> Kubernetes/Argo plugin
On-call           -> PagerDuty only           -> Component -> PagerDuty plugin
```

## Architecture: Frontend, Backend, and Integrations

Backstage splits into a **React frontend** and a **Node.js backend** bundled as a single deployable application you configure through `app-config.yaml` (and optional `app-config.production.yaml` overlays). The frontend renders entity pages, search, TechDocs, and plugin routes; the backend hosts catalog processing, scaffolder actions, auth brokers, and proxy endpoints that hold credentials away from browsers. A relational database (PostgreSQL in production, SQLite for local experiments) stores catalog processing state, scaffolder tasks, and other plugin data depending on what you enable.

```
BACKSTAGE ARCHITECTURE (SIMPLIFIED)
═══════════════════════════════════════════════════════════════════
┌───────────────────────────────────────────────────────────────┐
│ BACKSTAGE APP                                                  │
│  Frontend (React) ──► Catalog UI, TechDocs, Templates, Plugins │
│         │                                                      │
│  Backend (Node) ───► Catalog, Scaffolder, TechDocs, Auth, Proxy│
│         │                                                      │
│  Database ─────────► PostgreSQL (prod) / SQLite (local dev)   │
└───────────────────────────────┬───────────────────────────────┘
                                │ integrations (tokens on backend)
                                ▼
        GitHub / GitLab / Bitbucket · Kubernetes · Argo CD · PagerDuty · LDAP/OAuth
```

Understanding this split matters when you debug permissions: browsers call backend APIs, backends call external systems. If GitHub rate-limits your catalog import, fix integration tokens and processors on the backend—not the React route. If TechDocs builds fail, inspect the TechDocs backend builder/publisher configuration and CI jobs that generate static sites.

## Software Catalog: Entities, Relationships, and Ownership

The catalog is the **graph-shaped heart** of Backstage. Each entity is a YAML or JSON document describing a thing your organization cares about: a microservice (`Component`), an HTTP API (`API`), a database (`Resource`), a product area (`System`), a business domain (`Domain`), or people/teams (`User`, `Group`). Files typically live beside code as `catalog-info.yaml`, which keeps metadata close to the repository developers already open.

Ownership is not decorative. Setting `spec.owner` to a `Group` entity (for example `group:default/team-payments`) powers access-control rules, review routing, and plugin views that show on-call rotations for the responsible team. When ownership is missing, the portal becomes a phone book with blank entries—exactly the problem you tried to escape.

Relationships express architecture explicitly: a `Component` **dependsOn** a `Resource`, **consumesApi** / **providesApi** links wire service boundaries, and **system** membership groups components into product slices. Processors ingest entities from Git hosts, URL locations, or manual registration, then **stitch** references so the UI can render dependency graphs. Annotations attach machine-readable hooks—`github.com/project-slug` ties a component to a repository, `backstage.io/techdocs-ref` binds documentation, and Prometheus or Grafana annotations can deep-link observability assets when you standardize those keys.

```yaml
# catalog-info.yaml (representative service)
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payment-service
  description: Processes card payments for checkout
  annotations:
    github.com/project-slug: myorg/payment-service
    backstage.io/techdocs-ref: dir:.
  tags: [java, payments]
spec:
  type: service
  lifecycle: production
  owner: group:default/team-payments
  system: checkout
  providesApis: [payment-api]
  dependsOn: [resource:default/payments-db]
```

Entity kinds form a taxonomy you should keep **boring at first**. Start with Components, Groups, and Systems; add Domains and complex API entities when teams feel pain without them. Overly elaborate taxonomies confuse contributors and stall catalog coverage metrics.

## Ingestion, Discovery, and Catalog Hygiene

Catalog data rots when ingestion is manual. Backstage supports **location-based** imports (point at a Git org and discover `catalog-info.yaml` files), **org** data from identity providers, and custom processors for your internal service registry. The durable operational pattern is: (1) encode catalog files in repository templates so new services start registered, (2) add CI checks that fail pull requests missing required metadata fields such as owner and system, and (3) run periodic audits comparing catalog entities to live deployment records.

Stitching resolves references asynchronously in current releases—entities may appear partially linked until processors finish. Platform teams should monitor catalog errors in backend logs and surface them to contributors with actionable messages rather than silent omission. Treat catalog health as a product metric: percentage of production services with owner, docs, and lifecycle set.

## TechDocs: Documentation as Code

TechDocs implements **docs-like-code** for services cataloged in Backstage. Authors write Markdown in a `docs/` folder, configure `mkdocs.yml`, and annotate the entity with `backstage.io/techdocs-ref: dir:.` (or a URL-based ref). A backend builder (local or CI-driven external builder) generates static HTML published to cloud storage or local filesystem; the frontend renders docs inside the entity page so readers never hunt for a separate wiki.

This separation teaches an important platform principle: **documentation is a delivery pipeline**, not a one-time wiki migration. Teams that skip the pipeline end up with stale MkDocs sites; teams that integrate doc builds into service CI keep docs versioned with code review. TechDocs also reinforces ownership—when docs live in the repository, the same team that ships code ships explanations.

```yaml
# mkdocs.yml (minimal TechDocs-ready)
site_name: Payment Service
plugins:
  - techdocs-core
nav:
  - Home: index.md
  - Runbook: runbook.md
```

Prefer short, task-oriented pages linked from runbooks and architecture notes. Platform standards documents (how to rotate secrets, how to request a database) belong in TechDocs or linked Systems—not duplicated inconsistently across Confluence and Git.

## Software Templates and Golden Paths

Software Templates (Scaffolder) turn platform decisions into **self-service forms**. A `Template` resource describes parameters (service name, owner, repository location), a sequence of **steps** (fetch skeleton, publish to GitHub, register catalog entry, trigger CI webhook), and **outputs** (links to repo and catalog entity). Templates encode golden paths: the blessed combination of language version, CI workflow, observability hooks, and security scanning your organization expects.

Golden paths are opinionated on purpose. They trade absolute flexibility for **predictable outcomes**—fewer snowflake repositories, easier upgrades, and simpler compliance evidence. Product management for templates means measuring time-to-first-successful-deploy and interviewing developers about friction, not merely publishing YAML.

```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: node-service-golden-path
  title: Node.js Service (Golden Path)
spec:
  owner: group:default/platform-team
  type: service
  parameters:
    - title: Service metadata
      required: [name, owner]
      properties:
        name:
          title: Name
          type: string
          pattern: '^[a-z][a-z0-9-]*$'
        owner:
          title: Owner
          type: string
          ui:field: OwnerPicker
  steps:
    - id: fetch
      name: Fetch skeleton
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
    - id: publish
      name: Publish to GitHub
      action: publish:github
      input:
        repoUrl: github.com?owner=myorg&repo=${{ parameters.name }}
    - id: register
      name: Register in catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps['publish'].output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml
```

Guardrails live in three places: template parameters (validation patterns), skeleton content (required files such as `catalog-info.yaml` and CI workflows), and post-publish policies (branch protection rules applied by separate automation). Templates should never bypass security review entirely—they should **pre-fill** the safe defaults so review focuses on business logic rather than missing Dockerfile USER directives.

## Plugins, Search, and Toolchain Integration

Plugins extend both UI and backend. Frontend plugins add tabs and routes on entity pages—Kubernetes workloads, GitHub Actions runs, Argo CD applications, PagerDuty services. Backend plugins implement proxy endpoints and scheduled sync jobs that fetch external data with service credentials. Installing a plugin typically means adding Yarn dependencies, registering routes in `packages/app`, and configuring `app-config.yaml` with endpoints and tokens.

Integration architecture should follow **least privilege**: GitHub tokens scoped to catalog read for ingestion, narrower scopes for scaffolder publish actions, Kubernetes service accounts with namespace-scoped RBAC for dev clusters, and read-only Argo CD tokens for status panels. Backstage becomes a **read-mostly aggregation layer**; Git remains source of truth for code, Argo CD for desired cluster state, PagerDuty for incident routing.

Search unifies catalog entities, TechDocs, and optionally external systems when you enable additional collators. Good search relevance depends on catalog metadata quality—tags, titles, descriptions—another reason to enforce metadata standards early.

## Configuration, Deployment, and Upgrades

Production deployments run the backend container behind ingress TLS, connect to managed PostgreSQL, and inject secrets via your cluster's secret store. Configuration splits between static `app-config.yaml` and environment-specific overrides for URLs, auth providers, and CORS settings. Auth integrates with OAuth providers, OIDC, or proxy-based SSO patterns common in enterprises.

Upgrades require reading upstream release notes—Backstage ships frequent minor releases with breaking UI token changes, catalog performance improvements, and scaffolder action updates. Maintain a staging portal that tracks production plugins and run automated smoke tests: catalog query, doc render, template dry-run, and representative plugin fetches.

Local development uses `npx @backstage/create-app@latest` followed by `yarn install` and `yarn dev`, which binds frontend and backend for iterative plugin work. Production images should pin versions and rebuild when security patches land, not float unlabeled `:latest` tags without a deliberate policy.

## Adoption as Product Management

Hypothetical scenario: a platform team launches a polished Backstage UI but sees low weekly active usage because catalog entries required a manual ticket, templates were absent, and Kubernetes integration was deferred "until phase two." Developers praised the demo, then returned to old habits because the portal did not shorten any real task. After the team enabled repository discovery, shipped three templates aligned to top request types, and embedded Argo CD status on entity pages, usage climbed because the portal saved measurable minutes per week.

That narrative is illustrative, not a measured case study. The durable lesson: treat the portal as a **product** with personas, success metrics, and iteration loops. Interview developers about their first-week tasks, remove steps from those flows, and publish changelog notes when entity pages gain new tabs. Without adoption work, Backstage becomes shelfware regardless of CNCF status or release cadence.

## Authentication and Authorization Patterns

Backstage auth spans **sign-in** (who is the human using the browser) and **authorization** (what that identity may see or execute). Most enterprises integrate with an OAuth/OIDC provider or place an authenticating reverse proxy in front of the app. The durable design choice is to treat Backstage as another corporate application subject to SSO lifecycle policies—session timeouts, step-up auth for sensitive actions, and group membership sourced from your identity provider rather than manually curated YAML lists that drift the moment someone transfers teams.

Authorization layers include catalog permission rules (who can read or register entities), scaffolder permissions (who may run which templates), and plugin-specific checks (for example Kubernetes RBAC still governs what cluster objects a user may see even if Backstage renders them). Platform teams sometimes mistakenly assume the portal becomes the authorization system of record; in practice it **reflects** policies defined in GitHub, Kubernetes, and cloud IAM. Your job is to align Backstage roles with those systems so developers experience coherent denials instead of confusing partial views.

Guest mode and demo identities help local development, but production configurations should map users to `User` entities and groups to `Group` entities via org providers. When group membership is wrong, ownership links lie, on-call plugins point at outdated rotations, and template pickers offer teams a developer no longer belongs to. Invest in automated org sync and monitor diff alerts when HR-driven group changes fail to propagate.

## Entity Processors and the Reconciliation Mindset

Catalog ingestion resembles a Kubernetes controller: locations declare desired inputs, processors transform raw files into entities, validators reject malformed documents, and stitchers resolve references into a coherent graph stored in the database. Thinking in reconciliation loops helps you debug "my entity exists but relationships are missing" reports—often the entity arrived before its dependency, stitching retried asynchronously, or a typo in `dependsOn` prevented linkage.

Processors also enforce **normalization**. Two teams might use different annotation keys for the same concept until platform engineering publishes a **catalog descriptor standard** documenting required annotations (`github.com/project-slug`, observability links, security tier labels). Normalization processors can migrate legacy keys or emit warnings rather than silently accepting incompatible metadata. This is how you prevent the catalog from becoming a dumping ground of one-off fields that search cannot interpret.

Location types trade off freshness versus load. A broad GitHub org scan simplifies onboarding but increases API utilization; narrowly scoped locations reduce noise but require teams to request additions. Hybrid models start broad for discovery, then shift critical production systems to explicitly reviewed location entries once ownership data is trustworthy. Document the refresh expectations so incident responders know whether catalog lag is acceptable during GitHub outages.

## Designing Plugin Boundaries for Maintainability

Plugins are powerful because they escape the core release cycle, but they also import **operational debt** when teams install everything at once. A durable plugin strategy groups integrations by **user journey** rather than by vendor logo count. Ask which tabs a developer needs on day one of owning a service: repository, docs, CI status, deployment health, on-call. Ship those before niche integrations that leadership requested after reading a conference blog post.

Each plugin adds frontend bundle weight, backend credentials, and upgrade coupling. Prefer official or actively maintained community plugins for critical paths; fork only when you must patch behavior and you are willing to merge upstream changes quarterly. Wrap external API calls with caching and timeouts so a slow Argo CD instance does not hang entity page renders. Surface degraded states honestly ("Argo CD unreachable—retry") instead of blank tabs that look like missing permissions.

Custom plugins follow a predictable split: React components for presentation, backend routers for secrets-bearing fetches, and optional scheduled tasks for synchronization jobs. Keep business logic out of React when possible—backend services are easier to test and rotate credentials. Document plugin ownership inside your platform team the same way product teams own microservices, including on-call rotation for integrations that become incident-critical during outages.

## Scaffolder Actions, Secrets, and Workflow Safety

Software Templates are tempting to implement as mega-workflows that provision cloud resources, register catalog entries, open Jira tickets, and post Slack announcements in one click. The durable approach phases automation: first repository and catalog correctness, then CI visibility, then optional infrastructure modules orchestrated by specialized systems such as Crossplane or Terraform pipelines triggered after the repo exists. Backstage scaffolder actions excel at **Git-native** and **catalog-native** steps; they are not a general-purpose replacement for every platform controller.

Actions receive parameters and secrets under controlled schemas. Sensitive values belong in action input marked as secrets and stored in the scaffolder task record according to your retention policies. Teach template authors to avoid echoing secrets into logs and to validate parameter shapes with JSON Schema constraints so mistyped repository names fail fast before partially creating resources. Dry-run or preview modes—where available—help developers understand what will happen without mutating production systems.

Idempotency matters when actions retry. Publishing to an existing repository or re-registering catalog entries should either succeed cleanly or fail with actionable errors. Platform teams should maintain a **template catalog** with lifecycle labels (`experimental`, `supported`, `deprecated`) mirroring service lifecycles so developers know which golden path is current. Deprecation includes migration guides, not silent removal, because templates are contracts between platform and product engineering.

## TechDocs Builder Modes and Publishing Topologies

TechDocs supports multiple builder topologies; choosing wrong is a common source of "works on my laptop" failures. **Local builder** mode compiles docs on the Backstage backend—simple for small doc sets, expensive for monorepos with heavy MkDocs plugins. **External builder** mode expects CI to generate and publish static sites to cloud storage that the backend reads—better for scale and for keeping build secrets out of the portal cluster. The annotation `backstage.io/techdocs-ref` tells the system where source lives; the `techdocs.builder` and `techdocs.publisher` settings tell it how to transform and store artifacts.

Publisher configuration must align with your security model. Buckets require IAM roles or service accounts with least privilege; misconfigured public ACLs on doc buckets have leaked internal runbooks in real incidents across the industry. Prefer private buckets with authenticated fetches through the Backstage backend proxy rather than public URLs embedded in entity pages unless content is genuinely public marketing material.

Docs quality standards belong in platform guidelines: required sections (overview, runbook, SLOs), link styles, diagram formats, and freshness review cadence tied to production change frequency. TechDocs makes compliance visible—reviewers can see missing pages in pull requests when doc paths change—especially if CI fails when `mkdocs build` breaks. Pair TechDocs with catalog enforcement so undocumented services cannot mark `lifecycle: production` without an approved exception recorded in the catalog.

## Mapping Platform Capabilities to Portal Surfaces

Platform engineering roadmaps often list capabilities—cluster namespaces, database provisioning, certificate issuance, observability dashboards—that developers experience as disconnected tickets. A useful design exercise maps each capability to **portal surfaces**: catalog metadata fields, template parameters, TechDocs sections, and plugin tabs. For example, vCluster-based dev environments might appear as template outputs linking to a virtual cluster name, a TechDocs page describing kubeconfig retrieval, and a Kubernetes plugin view scoped to that namespace.

This mapping clarifies what Backstage should **not** do. If Crossplane claims provision databases, the portal should surface claim status via plugins and documentation, not re-implement provisioning logic inside scaffolder shell scripts that bypass audit trails. If PagerDuty owns paging policy, show service links and escalation policies rather than storing pager numbers in free-text catalog fields that rot silently.

Cross-linking modules in KubeDojo reinforces the pattern: [Module 3.6: vCluster](../module-3.6-vcluster/) covers virtual clusters; [Module 7.2: Crossplane](../module-7.2-crossplane/) covers infrastructure APIs; this module covers the portal layer that makes those capabilities discoverable. Your organization’s graph may differ, but the **separation of concerns** remains: controllers enforce state, Git records intent, portals narrate how humans navigate the system.

## Security, Compliance, and Audit Evidence

Security reviewers ask whether a developer portal increases attack surface. It can, primarily by concentrating credentials and metadata. Mitigations include hosting Backstage inside your corporate network or zero-trust access layer, using short-lived tokens, enabling audit logs for scaffolder executions, and applying Kubernetes network policies so the backend reaches only approved API endpoints. Catalog metadata may describe data classification; integrate those fields with access rules so restricted components hide sensitive tabs from unauthorized groups.

Compliance frameworks often require evidence that production services have owners, change management hooks, and documented runbooks. Backstage does not automatically satisfy auditors, but catalog queries plus TechDocs links provide **machine-checkable artifacts** when you define policies such as "production Components must include owner, system, techdocs-ref, and CI annotation." Export catalog snapshots or use the catalog export capabilities described in upstream release notes when teams need CSV/JSON evidence for governance reviews.

Red-team exercises should include the portal: attempt to invoke templates without authorization, exfiltrate integration tokens from misconfigured clients, or enumerate entities that leak internal project codenames. Findings feed back into descriptor standards and permission rules. Treat those exercises as routine platform hygiene, not one-time launch gates.

## Operating Backstage in Production

Production operations extend beyond uptime monitoring. Track database migration health, plugin version skew between frontend and backend packages, search index freshness, and scaffolder queue depth. Backstage releases ship performance fixes—recent catalog releases split count queries from list queries to reduce UI latency—so staying reasonably current is an operational requirement, not vanity upgrading.

Backup strategy includes PostgreSQL snapshots and exported `app-config` secrets stored in your vault. Disaster recovery drills should restore a staging instance from backups and verify catalog imports rehydrate from Git locations rather than assuming the database alone is authoritative—Git-backed entities should rebuild after catastrophic DB loss, though scaffolder history may not.

Capacity planning accounts for org size: large enterprises with tens of thousands of entities need tuned database indexes, careful search collators, and potentially sharded location providers. Start smaller, measure p95 catalog query latency, and scale vertically before introducing architectural sharding. Developer complaints about "slow search" often trace to missing indexes or overly broad wildcard queries fixable without re-architecting the entire portal.

## IDP Maturity Stages and Platform Roadmaps

Teams rarely jump from zero to a fully pluginized portal in one quarter. A durable maturity model helps you sequence investments and communicate progress without overpromising instant self-service nirvana. **Stage one—catalog truth**—focuses on ownership, lifecycle, and repository linkage for production services, usually via `catalog-info.yaml` in repos plus CI lint rules. **Stage two—paved creation**—adds templates for the top three service types your organization actually ships, not the twenty types architects wish existed. **Stage three—operational line-of-sight**—embeds CI, GitOps, and incident context on entity pages so developers stop opening six tabs for a deploy verification. **Stage four—ecosystem automation**—connects templates to downstream controllers (secrets, clusters, databases) with clear boundaries about which system mutates state.

Each stage produces user-visible wins, which protects the portal during budget conversations. Leadership dashboards love entity counts; developers love shaving minutes off recurring tasks. Translate maturity into both languages. When a stage stalls, diagnose whether metadata quality, template maintenance, or plugin reliability blocked progress—those are different remediation projects.

Roadmaps should also name **non-goals**. Backstage will not replace your service mesh control plane, your cloud billing system, or your HR portal. Saying no prevents scope creep that turns the platform team into a generic web CRUD shop. Non-goals still allow deep links—billing dashboards can appear as catalog links without re-implementing FinOps analytics inside Backstage.

## Catalog Descriptor Standards in Practice

Publishing a descriptor standard document transforms catalog work from art to engineering. The standard lists required and optional metadata fields, annotation keys, tag vocabularies, and examples for each service tier. It explains how `lifecycle: experimental` differs from `production` in terms of SLO expectations and required integrations. New hires read the standard once instead of inferring conventions from whichever repository was copied most recently.

Standards pair with **lint automation**. CI jobs can validate `catalog-info.yaml` with JSON Schema or custom scripts, failing pull requests that omit owners or use deprecated annotation keys. Backstage validators add another layer server-side, but client-side lint gives faster feedback. When standards change, provide codemods or scripted migrations for high-value repositories rather than expecting manual edits across thousands of repos overnight.

Descriptor standards also clarify **API versus Component** modeling decisions so dependency graphs stay legible at scale. When every HTTP surface becomes its own Component without API entities, graphs look dense but say little about contract stability. When API entities are missing entirely, consumers cannot discover breaking-change policies. The standard should include decision trees: if more than two services consume an interface maintained by a platform team, promote an API entity with an OpenAPI spec link.

## Plugin Integration Patterns for GitHub, Argo CD, and PagerDuty

GitHub integration typically serves dual purposes: catalog location discovery and scaffolder repository publishing. Use separate credentials or GitHub Apps with narrowly scoped permissions for each purpose so a compromised scaffolder token cannot rewrite unrelated repositories. Rate-limit monitoring belongs on your platform dashboard because large org imports can exhaust REST quotas during business hours if processors rerun aggressively.

Argo CD plugins usually fetch application health and sync status for entities annotated with application names or labels. Align annotation conventions with how your GitOps repos name Applications—if teams use App-of-Apps patterns, document how entity pages map to the correct Application resource. Read-only tokens suffice for status panels; mutating syncs from Backstage should remain rare and heavily audited because GitOps principles expect Git to remain the desired-state source.

PagerDuty integration connects services to on-call schedules and open incidents. Map catalog components to PagerDuty service IDs via annotations validated in CI so pages route correctly during outages. During incident response, responders benefit from seeing upstream dependencies in the catalog graph while viewing PagerDuty escalation policies in the same UI. Avoid duplicating PagerDuty as a manual on-call spreadsheet stored in catalog descriptions—that data rots within weeks.

Together these three integrations cover the toolchain outcome in this module’s learning objectives: code hosting, deployment health, and incident routing appear beside the same entity without pretending Backstage owns those workflows. When any integration fails, degrade gracefully and link out to the native tool so developers are never blocked from executing emergency actions.

## Local Development to Production Promotion

The journey from `yarn dev` on a laptop to a hardened production deployment teaches platform engineers where Backstage differs from a static internal wiki. Local setups tolerate SQLite, guest users, and permissive CORS; production requires PostgreSQL backups, authenticated SSO, ingress TLS, and secrets injected from vaults rather than dotfiles. Document this promotion path so application teams do not copy local `app-config` snippets containing development credentials into staging clusters.

Container images should pin Backstage version tags matching your tested upgrade path—track upstream release notes for breaking changes to UI tokens, catalog stitching, and scaffolder APIs. Helm charts or raw Kubernetes manifests both work; choose based on your platform standards. Health checks should hit backend readiness endpoints that verify database connectivity, not merely TCP socket openness on the frontend port.

Environment-specific configuration overlays let you run the same container image in staging and production with different integration endpoints. Staging should mirror plugin enablement so teams catch breaking API changes before customer-facing developer traffic hits production. Automate smoke tests that create ephemeral template runs against sandbox GitHub organizations where possible, preventing scaffolder regressions from blocking service creation on Monday mornings.

Promotion also includes **content** promotion: catalog location entries, template YAML, and TechDocs standards should live in Git repositories reviewed like application code. Platform teams that click-edit production catalog entries without version control recreate the drift problems Backstage was meant to solve. GitOps for portal configuration keeps audit trails and enables rollback when a template change accidentally removes compliance workflows.

When you train internal champions, emphasize that Backstage rewards consistent metadata more than heroic customization. A plain entity page with accurate owner, working TechDocs, and trustworthy CI status beats a flashy homepage widget that rots after one release cycle. Champions should pair with service teams during their next launch, co-author `catalog-info.yaml`, and measure whether onboarding questions drop the following week—that qualitative signal often precedes formal portal analytics and keeps adoption grounded in real developer pain relief rather than executive dashboard vanity metrics.

Finally, remember that portal success is measured in **workflow completion**, not portal logins alone. Track whether developers finish template runs, merge scaffolded repos, and reach TechDocs from incident channels. Those behavioral traces validate that the IDP spine—catalog, docs, templates, plugins—is wired into daily work instead of existing as an optional sidebar bookmark. When metrics stall, return to interviews and remove steps before buying another plugin bundle.

Platform leaders sometimes ask whether to build an in-house portal instead of adopting Backstage. The build-versus-adopt decision hinges on whether your differentiator is the portal shell or the standards encoded in catalog descriptors, templates, and docs pipelines. Backstage gives you a maintained framework for the shell; your organizational value still lives in the metadata and automation you inject. Forking the entire UI rarely ages well unless you plan a dedicated product team with a multi-year roadmap competitive with upstream velocity.

Treat every catalog field and template parameter as a **policy lever**: small YAML decisions ripple across search, access control, compliance exports, and plugin renderers. Document why each required field exists so teams do not strip metadata during rushed launches. Review those levers quarterly with security and developer experience stakeholders across every product team so the portal stays aligned with how your organization actually ships software today, not how architecture slides imagined it last year during annual planning season.

## Did You Know?

1. **CNCF timeline:** Backstage joined CNCF on **September 8, 2020**, reached **Incubating** status on **March 15, 2022**, and—as of the 2026-06 snapshot—remains an **Incubating** project rather than Graduated ([CNCF project page](https://www.cncf.io/projects/backstage/)).

2. **Framework, not a single app:** Upstream ships a create-app scaffold and plugin ecosystem; every organization customizes routes, auth, and plugins. Two Backstage installations can look like different products while sharing the same core catalog/scaffolder concepts.

3. **TechDocs pipeline:** Documentation builds can run locally for fast feedback or externally in CI with published artifacts—choose based on doc size and build-time secrets; both patterns are documented in Backstage TechDocs guides.

4. **Scaffolder actions are composable:** Platform teams chain actions (fetch template, publish, register catalog, send webhook) similarly to CI jobs, which makes templates a workflow engine for golden paths rather than a static cookiecutter wrapper.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Launching catalog-only | Portal shows empty or stale entities; developers see no time savings | Pair catalog ingestion with templates and at least one high-value plugin tab |
| Missing `spec.owner` | Ownership queries fail; escalation paths break during incidents | Require owner in templates and CI lint for `catalog-info.yaml` |
| Templates without CI/CD | Golden paths stop at repository creation; first deploy still manual | Include workflow files and document verification steps in template outputs |
| Over-complex entity taxonomy | Contributors avoid registering; graph becomes inconsistent | Start with Component/System/Group; expand when pain is proven |
| Storing long-lived admin tokens in frontend config | Credential exposure via browser-accessible settings | Keep secrets in backend configuration and secret stores |
| Ignoring catalog processor errors | Silent data loss erodes trust in search and graphs | Monitor backend logs; publish contributor-facing error catalog |
| Skipping staging upgrades | Production portal breaks on plugin API changes | Maintain staging with production-like plugins; read release notes |
| Treating plugins as replacements | Teams expect Backstage to own Git or Kubernetes | Document that plugins aggregate external systems of record |

## Quiz

### Question 1
Your organization already runs GitHub, Argo CD, and PagerDuty. Where should Backstage sit in the architecture, and what should remain the system of record for code, deployments, and incidents?

<details>
<summary>Show Answer</summary>

Backstage should act as an **aggregation and navigation layer**, not a replacement for Git, Argo CD, or PagerDuty. Git remains the source of truth for source code and `catalog-info.yaml`; Argo CD remains the GitOps controller for cluster desired state; PagerDuty remains the incident and on-call system of record. Backstage integrates via backend plugins and proxies, presenting contextual tabs on catalog entities (build status, sync health, on-call rotation) while delegating mutations back to the native tools when actions are required.

</details>

### Question 2
Explain the difference between a `Component` and a `System`, and describe when you would model an API as its own `API` kind instead of only documenting it inside a Component page.

<details>
<summary>Show Answer</summary>

A **Component** is a deployable or maintainable piece of software—typically a service, website, or library—with code repository linkage and lifecycle metadata. A **System** groups related components that deliver a product capability (for example checkout). You model a separate **API** entity when multiple consumers need a stable contract reference, when OpenAPI/AsyncAPI specs should appear as first-class catalog objects, or when ownership of the interface differs from a single implementing component. Keeping APIs explicit improves dependency graphs and clarifies breaking-change communication.

</details>

### Question 3
A developer asks why they should use a Software Template instead of copying an existing repository. How do golden paths reduce risk for the platform team and the developer?

<details>
<summary>Show Answer</summary>

Copy-paste inherits hidden debt: outdated CI actions, missing security scans, wrong branch protections, and catalog metadata drift. Templates generate repositories from an approved skeleton with parameterized names, inject current workflow versions, register catalog entries automatically, and can trigger downstream automation. Developers gain speed; platform teams gain **standardization evidence** for audits and easier bulk upgrades because known files exist in every scaffolded repo.

</details>

### Question 4
TechDocs builds are failing intermittently in CI while local `mkdocs serve` works. What configuration areas do you investigate first in a Backstage deployment?

<details>
<summary>Show Answer</summary>

Compare **builder mode** (`local` vs `external`), publisher storage credentials, TechDocs annotation paths (`backstage.io/techdocs-ref`), and CI job permissions fetching repository content. External builders require published artifacts reachable by the backend; missing S3/GCS permissions or wrong bucket prefixes often manifest as flaky renders. Also verify MkDocs plugin versions match between local and CI containers.

</details>

### Question 5
Catalog ingestion from GitHub is slow and sometimes incomplete after large org imports. What operational knobs and hygiene practices improve reliability without blaming developers?

<details>
<summary>Show Answer</summary>

Tune location providers and processing frequency, ensure PAT/GitHub App rate limits are monitored, and split monolithic org imports into focused location targets. Add processors that validate entities and surface errors to contributors. Encourage small, well-formed `catalog-info.yaml` files in each repo rather than one giant manual YAML bundle. Check backend database health and catalog stitching logs after upgrades because deferred stitching can delay relationship graphs.

</details>

### Question 6
Which Backstage integration points require backend credentials, and why must those credentials avoid frontend `app-config` bundles shipped to browsers?

<details>
<summary>Show Answer</summary>

GitHub/GitLab discovery, scaffolder publish actions, Kubernetes API queries, Argo CD API calls, and PagerDuty REST access all run **server-side**. Browsers talk to Backstage backend routes; backends hold tokens. Frontend bundles are visible to users and must not embed privileged tokens because any user could extract them from downloaded JavaScript or config JSON exposed to the client.

</details>

### Question 7
Scenario: leadership wants a single "developer portal" KPI. Propose three measurable metrics tied to IDP outcomes rather than counting raw entity totals.

<details>
<summary>Show Answer</summary>

Measure **time-to-first-successful-template-run** (self-service efficiency), **percentage of production components with owner + TechDocs + lifecycle set** (metadata quality), and **weekly active developers viewing entity pages tied to services they deploy** (real usage). Raw entity counts are vanity if entities are stale; combine quality and activity metrics to guide plugin and template investments.

</details>

## Hands-On Exercise

### Objective
Run Backstage locally, register a component with TechDocs metadata, and trace how catalog location configuration connects a repository file to the portal UI.

### Environment Setup

```bash
# Requires Node 20+ and Yarn (installed by create-app)
npx @backstage/create-app@latest
# Accept defaults or name the app backstage-lab
cd backstage-lab
yarn install
yarn dev
# Frontend typically listens on http://127.0.0.1:3000
# Backend typically listens on http://127.0.0.1:7007
```

### Tasks

1. **Explore the default portal** — open the local URL, navigate to the catalog, and inspect a sample entity to see how tabs organize catalog data, docs, and CI information when demo content is present.

2. **Create a standalone catalog file** — in any directory, author `catalog-info.yaml` for a fictional `Component` with owner `user:default/guest` or a demo group, plus tags and description text.

3. **Register via file location** — add a `catalog.locations` entry pointing at your YAML file using the `file:` target scheme documented in Backstage catalog configuration, restart if needed, and confirm the entity appears in the catalog index.

4. **Add TechDocs metadata** — create `mkdocs.yml` and `docs/index.md` alongside the catalog file, set `backstage.io/techdocs-ref: dir:.`, configure TechDocs builder settings appropriate for local experimentation, and verify the Docs tab renders or note builder logs if external publishing is required.

5. **Integrate one external read-only view** — configure a GitHub integration token on the backend (read-only) or enable a bundled demo plugin following official docs, then confirm a plugin tab or card displays live metadata for your entity without storing the token in frontend-visible config.

### Success Criteria

- [ ] Backstage dev server runs locally with catalog UI reachable in a browser
- [ ] Custom `Component` entity appears after location registration
- [ ] Entity shows owner, description, and tags you authored
- [ ] TechDocs tab renders Markdown or you captured backend logs explaining required publisher setup
- [ ] At least one backend integration is configured with credentials stored server-side only

### Verification

```bash
# Confirm backend health endpoint responds
curl -sS http://127.0.0.1:7007/api/catalog/health

# After registering locations, query entities (adjust filter as needed)
curl -sS "http://127.0.0.1:7007/api/catalog/entities?filter=kind=component" | head
```

## Sources

- https://backstage.io/docs/overview/what-is-backstage
- https://backstage.io/docs/getting-started/
- https://backstage.io/docs/features/software-catalog/
- https://backstage.io/docs/features/software-catalog/descriptor-format/
- https://backstage.io/docs/features/software-templates/
- https://backstage.io/docs/features/techdocs/
- https://backstage.io/docs/plugins/
- https://backstage.io/docs/auth/
- https://backstage.io/docs/conf/
- https://github.com/backstage/backstage
- https://github.com/backstage/backstage/releases/tag/v1.52.0
- https://www.cncf.io/projects/backstage/
- https://engineering.atspotify.com/2020/03/what-the-heck-is-backstage-anyway/

## Next Module

Continue to [Module 7.2: Crossplane](../module-7.2-crossplane/) to learn how Kubernetes-native control planes provision infrastructure that your portal can expose through templates and catalog entities.

---

*"An internal developer portal succeeds when developers finish real tasks faster—not when architects admire a catalog graph."*
