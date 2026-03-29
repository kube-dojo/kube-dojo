---
title: "Module 1.3: Backstage Catalog & Infrastructure"
slug: k8s/cba/module-1.3-backstage-catalog-infrastructure
sidebar:
  order: 4
---
> **Complexity**: `[COMPLEX]` - Covers two exam domains (44% of CBA combined)
>
> **Time to Complete**: 60-75 minutes
>
> **Prerequisites**: Module 1 (Backstage Overview), Module 2 (Plugins & Extensibility)

---

## Why This Module Matters

The software catalog is the beating heart of Backstage. Without it, Backstage is just a plugin framework with a pretty UI. With it, you have a single pane of glass over every service, API, team, and piece of infrastructure your organization owns. The CBA exam dedicates **22% to the catalog** (Domain 3) and another **22% to infrastructure** (Domain 2)—together, that is 44% of your score.

Get these two domains right and you are nearly halfway to passing before you even touch plugins or TechDocs.

> **The Library Analogy**
>
> Think of the Backstage catalog as a library's card catalog system. Every book (Component) has a card describing it—author, genre, location. Some books reference other books (API relationships). The librarian (entity processor) receives new books, catalogs them, and shelves them. The building itself—shelves, lighting, HVAC—is the infrastructure. You need both: a great catalog system is useless if the building has no electricity, and a beautiful building with empty shelves helps nobody.

---

## What You'll Learn

By the end of this module, you'll understand:
- All nine entity kinds and when to use each one
- How entities get into the catalog (manual and automated)
- How to write and structure `catalog-info.yaml` files
- The Backstage architecture: frontend, backend, database, proxy
- How to configure Backstage with `app-config.yaml`
- Production deployment considerations
- Common troubleshooting patterns for catalog issues

---

## Did You Know?

1. **Spotify's catalog tracks over 10,000 components** across hundreds of teams. The software catalog was the original reason Backstage was built—everything else came later.
2. **Entity refresh is not instant.** By default, Backstage re-processes entities every 100-200 seconds. This trips up almost every new admin who registers something and wonders why it is not appearing.
3. **The Backstage proxy** (`/api/proxy`) lets the frontend call external APIs without exposing credentials to the browser—a pattern so useful that many teams use Backstage as their universal API gateway during development.
4. **You can run Backstage without a single plugin installed.** The catalog alone provides enough value that some organizations deploy it purely as a service directory with ownership tracking.

---

## Part 1: The Software Catalog (Domain 3 — 22%)

### 1.1 Entity Kinds

Everything in the Backstage catalog is an **entity**. Each entity has a `kind`, an `apiVersion`, `metadata`, and a `spec`. There are nine built-in kinds:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKSTAGE ENTITY KINDS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OWNERSHIP          ORGANIZATIONAL        CATALOG MACHINERY      │
│  ┌───────────┐      ┌──────────┐          ┌──────────┐          │
│  │ Component │      │  Group   │          │ Location │          │
│  │ (service, │      │  (team,  │          │ (points  │          │
│  │  library) │      │  dept)   │          │  to YAML)│          │
│  └───────────┘      └──────────┘          └──────────┘          │
│  ┌───────────┐      ┌──────────┐          ┌──────────┐          │
│  │    API    │      │   User   │          │ Template │          │
│  │ (REST,   │      │  (person)│          │ (scaffol-│          │
│  │  gRPC)   │      └──────────┘          │  ding)   │          │
│  └───────────┘                            └──────────┘          │
│  ┌───────────┐      GROUPING                                    │
│  │ Resource  │      ┌──────────┐                                │
│  │ (DB, S3, │      │  System  │                                │
│  │  queue)  │      │  (group  │                                │
│  └───────────┘      │  of comp)│                                │
│                     └──────────┘                                │
│                     ┌──────────┐                                │
│                     │  Domain  │                                │
│                     │ (business│                                │
│                     │  area)   │                                │
│                     └──────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

| Kind | Purpose | Example |
|------|---------|---------|
| **Component** | A piece of software (service, website, library) | `payments-service`, `react-ui-library` |
| **API** | A boundary between components (REST, gRPC, GraphQL, AsyncAPI) | `payments-api` (OpenAPI spec) |
| **Resource** | Physical or virtual infrastructure a component depends on | `orders-db` (PostgreSQL), `events-queue` (Kafka topic) |
| **System** | A collection of components and APIs that form a product | `payments-system` (groups payments service + API + DB) |
| **Domain** | A business area grouping related systems | `finance` (groups payments, billing, invoicing systems) |
| **Group** | A team or organizational unit | `platform-team`, `backend-guild` |
| **User** | An individual person | `jane.doe` |
| **Location** | A pointer to other entity definition files | A URL referencing a `catalog-info.yaml` in a repo |
| **Template** | A software template for scaffolding new projects | `springboot-service-template` |

**Key relationships between entity kinds:**

```
Domain
  └── System
        ├── Component ──ownedBy──► Group/User
        │     ├── providesApi ──► API
        │     ├── consumesApi ──► API
        │     └── dependsOn ──► Resource
        └── API ──ownedBy──► Group/User
```

### 1.2 The catalog-info.yaml File

Every entity is described by a YAML descriptor. The standard name is `catalog-info.yaml` and it typically lives at the root of a repository:

```yaml
# catalog-info.yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payments-service
  description: Handles all payment processing
  annotations:
    github.com/project-slug: myorg/payments-service
    backstage.io/techdocs-ref: dir:.
  tags:
    - java
    - payments
  links:
    - url: https://payments.internal.myorg.com
      title: Production
      icon: dashboard
spec:
  type: service
  lifecycle: production
  owner: team-payments
  system: payments-system
  providesApis:
    - payments-api
  dependsOn:
    - resource:payments-db
```

**Required fields for every entity:**
- `apiVersion` — always `backstage.io/v1alpha1` for built-in kinds
- `kind` — one of the nine kinds above
- `metadata.name` — unique within its kind+namespace; lowercase, hyphens, max 63 chars
- `spec` — varies by kind

### 1.3 Annotations and Entity Discovery

Annotations are the glue between catalog entities and Backstage plugins. They tell plugins where to find data about a component. This is a critical exam topic.

| Annotation | What It Does |
|------------|-------------|
| `github.com/project-slug` | Links entity to a GitHub repo (`org/repo`) |
| `backstage.io/techdocs-ref` | Tells TechDocs where to find docs (`dir:.` = same repo) |
| `backstage.io/source-location` | Source code URL for the entity |
| `jenkins.io/job-full-name` | Links to a Jenkins job |
| `pagerduty.com/service-id` | Links to PagerDuty for on-call info |
| `backstage.io/managed-by-location` | Which Location entity registered this entity |
| `backstage.io/managed-by-origin-location` | Original Location that first introduced the entity |

Annotations are how Backstage stays loosely coupled. The core catalog does not know about Jenkins or PagerDuty. Plugins read annotations to find the data they need.

### 1.4 Manual Registration: Location Entities

The simplest way to get entities into the catalog is **manual registration** using Location entities.

**Option A: Register via the UI**

Click "Register Existing Component" in Backstage, paste a URL to a `catalog-info.yaml`, and Backstage creates a Location entity pointing to that URL.

**Option B: Static Location in app-config.yaml**

```yaml
# app-config.yaml
catalog:
  locations:
    - type: url
      target: https://github.com/myorg/payments-service/blob/main/catalog-info.yaml
      rules:
        - allow: [Component, API]

    - type: file
      target: ../../examples/all-components.yaml
      rules:
        - allow: [Component, System, Domain]
```

**Location entity YAML** (can also be its own file):

```yaml
apiVersion: backstage.io/v1alpha1
kind: Location
metadata:
  name: myorg-payments
  description: Payments team components
spec:
  type: url
  targets:
    - https://github.com/myorg/payments-service/blob/main/catalog-info.yaml
    - https://github.com/myorg/payments-api/blob/main/catalog-info.yaml
```

> **Exam tip:** A Location entity can reference multiple targets. This is useful for registering many repos at once without automated discovery.

### 1.5 Automated Ingestion

Manual registration does not scale. For organizations with hundreds or thousands of repos, Backstage supports **discovery providers** that automatically find and register entities.

**GitHub Discovery:**

```yaml
# app-config.yaml
catalog:
  providers:
    githubDiscovery:
      myOrgProvider:
        organization: 'myorg'
        catalogPath: '/catalog-info.yaml'   # where to look in each repo
        schedule:
          frequency: { minutes: 30 }
          timeout: { minutes: 3 }
```

This scans every repo in the `myorg` GitHub organization, checks if `/catalog-info.yaml` exists, and automatically registers any entities found.

**GitLab Discovery:**

```yaml
catalog:
  providers:
    gitlab:
      myGitLab:
        host: gitlab.mycompany.com
        branch: main
        fallbackBranch: master
        catalogFile: catalog-info.yaml
        group: 'mygroup'                    # optional: limit to a group
        schedule:
          frequency: { minutes: 30 }
          timeout: { minutes: 3 }
```

**GitHub Org Data Provider** (for users and teams):

```yaml
catalog:
  providers:
    githubOrg:
      myOrgProvider:
        id: production
        orgUrl: https://github.com/myorg
        schedule:
          frequency: { hours: 1 }
          timeout: { minutes: 10 }
```

This imports GitHub teams as `Group` entities and GitHub org members as `User` entities automatically—no need to maintain user YAML files by hand.

### 1.6 Entity Processors and Custom Providers

The catalog has a processing pipeline that runs continuously:

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Ingestion  │────►│   Processing    │────►│   Stitching      │
│              │     │                 │     │                  │
│ - Locations  │     │ - Validate YAML │     │ - Resolve refs   │
│ - Discovery  │     │ - Run processors│     │ - Build relation │
│ - Providers  │     │ - Emit entities │     │   graph          │
│              │     │ - Emit errors   │     │ - Final entity   │
└──────────────┘     └─────────────────┘     └──────────────────┘
       │                     │                        │
       ▼                     ▼                        ▼
  Entity enters        Entity validated          Entity visible
  the pipeline         and enriched              in the catalog
```

**Entity processors** are functions that run on every entity during the processing phase. Built-in processors handle things like:
- Validating entity schema
- Resolving `Location` targets into child entities
- Extracting relationships from `spec` fields

**Custom entity providers** let you ingest entities from any source—a CMDB, a spreadsheet, an internal API. They implement the `EntityProvider` interface:

```typescript
import { EntityProvider, EntityProviderConnection } from '@backstage/plugin-catalog-node';

class MyCustomProvider implements EntityProvider {
  getProviderName(): string {
    return 'my-custom-provider';
  }

  async connect(connection: EntityProviderConnection): Promise<void> {
    // Fetch entities from your custom source
    const entities = await fetchFromMySource();

    await connection.applyMutation({
      type: 'full',
      entities: entities.map(entity => ({
        entity,
        locationKey: 'my-custom-provider',
      })),
    });
  }
}
```

### 1.7 Troubleshooting the Catalog

**Entity not appearing after registration:**

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Entity never shows up | Invalid YAML or schema violation | Check the catalog import page for errors |
| Entity appears then disappears | `rules` in app-config block the entity kind | Add the kind to `rules: allow` |
| Stale data after repo update | Refresh cycle has not run yet | Manually refresh via catalog API or wait ~100-200s |
| Entity shows as orphaned | The Location that registered it was deleted | Re-register or remove the orphan |
| Relationships broken | Referenced entity name does not match | Check exact `name` fields; they are case-sensitive |

**Orphaned entities** occur when the Location that originally registered an entity is removed, but the entity itself remains. Backstage marks these as orphans. You can clean them up in the catalog UI or via the API:

```bash
# List orphaned entities via the Backstage catalog API
curl http://localhost:7007/api/catalog/entities?filter=metadata.annotations.backstage.io/orphan=true

# Delete a specific orphaned entity
curl -X DELETE http://localhost:7007/api/catalog/entities/by-uid/<entity-uid>
```

**Forcing a refresh:**

```bash
# Refresh a specific entity
curl -X POST http://localhost:7007/api/catalog/refresh \
  -H 'Content-Type: application/json' \
  -d '{"entityRef": "component:default/payments-service"}'
```

---

## Part 2: Backstage Infrastructure (Domain 2 — 22%)

### 2.1 Framework Architecture

Backstage is a Node.js application with a clear client-server split:

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (Client)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Backstage Frontend App (React SPA)            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │  │
│  │  │ Catalog  │ │ TechDocs │ │ Scaffolder│ │ Search      │  │  │
│  │  │ Plugin   │ │ Plugin   │ │ Plugin   │ │ Plugin      │  │  │
│  │  │ (front)  │ │ (front)  │ │ (front)  │ │ (front)     │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP/REST API calls
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKSTAGE BACKEND (Node.js)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ Catalog  │ │ TechDocs │ │ Scaffolder│ │ Auth / Proxy /    │  │
│  │ Backend  │ │ Backend  │ │ Backend  │ │ Search Backend    │  │
│  └─────┬────┘ └──────────┘ └──────────┘ └───────────────────┘  │
│        │                                                        │
│        ▼                                                        │
│  ┌──────────┐    ┌──────────────────────────────────────────┐   │
│  │ Database │    │         Integrations                      │   │
│  │(Postgres)│    │  GitHub, GitLab, Azure DevOps, LDAP ...  │   │
│  └──────────┘    └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Key architectural points for the exam:**

1. **Frontend** — A React single-page application (SPA). Built at compile time. Served as static files. All frontend plugins are compiled into one bundle.
2. **Backend** — A Node.js (Express) server. Each backend plugin registers its own API routes under `/api/<plugin-id>/`. Runs entity processing, scaffolding, TechDocs generation, etc.
3. **Database** — SQLite for development, **PostgreSQL for production**. Stores catalog entities, search index, scaffolder task history.
4. **Integrations** — Configured connections to external systems (SCM, CI/CD, cloud providers). Defined in `app-config.yaml` under the `integrations` key.

### 2.2 Configuration: app-config.yaml

The `app-config.yaml` file is the central configuration for a Backstage instance. Understanding its structure is essential.

```yaml
# app-config.yaml — Top-level structure
app:
  title: My Company Backstage
  baseUrl: http://localhost:3000          # Frontend URL

backend:
  baseUrl: http://localhost:7007          # Backend URL
  listen:
    port: 7007
  database:
    client: better-sqlite3                # dev default
    connection: ':memory:'
  cors:
    origin: http://localhost:3000

organization:
  name: MyOrg

integrations:
  github:
    - host: github.com
      token: ${GITHUB_TOKEN}              # environment variable substitution

auth:
  providers:
    github:
      development:
        clientId: ${AUTH_GITHUB_CLIENT_ID}
        clientSecret: ${AUTH_GITHUB_CLIENT_SECRET}

proxy:
  endpoints:
    '/pagerduty':
      target: https://api.pagerduty.com
      headers:
        Authorization: Token token=${PAGERDUTY_TOKEN}

catalog:
  locations: []
  providers: {}
  rules:
    - allow: [Component, System, API, Resource, Location, Domain, Group, User, Template]
```

**Environment variable substitution:**

Backstage supports `${VAR_NAME}` syntax in `app-config.yaml`. At startup, the backend resolves these from the process environment. This is the primary way to inject secrets.

**Configuration layering (config includes):**

```bash
# You can pass multiple config files — later files override earlier ones
node packages/backend --config app-config.yaml --config app-config.production.yaml
```

A common pattern:
- `app-config.yaml` — base/development configuration
- `app-config.production.yaml` — production overrides (database, URLs, auth)
- `app-config.local.yaml` — personal local overrides (gitignored)

### 2.3 The Backstage Proxy

The proxy plugin (`/api/proxy`) lets the **backend** forward requests to external APIs on behalf of the frontend. This solves two problems: CORS restrictions and secret management.

```yaml
# app-config.yaml
proxy:
  endpoints:
    '/pagerduty':
      target: https://api.pagerduty.com
      headers:
        Authorization: Token token=${PAGERDUTY_TOKEN}
    '/grafana':
      target: https://grafana.internal.myorg.com
      headers:
        Authorization: Bearer ${GRAFANA_TOKEN}
      allowedHeaders: ['Content-Type']
```

**How it works:**

```
Browser                    Backstage Backend              External API
  │                              │                             │
  │  GET /api/proxy/pagerduty/   │                             │
  │  services/PXXXXXX            │                             │
  │─────────────────────────────►│                             │
  │                              │  GET /services/PXXXXXX      │
  │                              │  Authorization: Token ...   │
  │                              │────────────────────────────►│
  │                              │                             │
  │                              │◄────────────────────────────│
  │◄─────────────────────────────│   (response forwarded)      │
  │                              │                             │
```

The browser never sees the PagerDuty API token. It only talks to the Backstage backend. The backend injects the credentials and forwards the request.

### 2.4 Production Deployment

Moving from `yarn dev` to production requires several changes:

**Database — switch to PostgreSQL:**

```yaml
# app-config.production.yaml
backend:
  database:
    client: pg
    connection:
      host: ${POSTGRES_HOST}
      port: ${POSTGRES_PORT}
      user: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
```

**HTTPS and base URLs:**

```yaml
app:
  baseUrl: https://backstage.mycompany.com

backend:
  baseUrl: https://backstage.mycompany.com
  cors:
    origin: https://backstage.mycompany.com
```

In practice, most teams terminate TLS at a load balancer or ingress controller in front of Backstage, not in the Node.js process itself.

**Authentication:**

Backstage supports multiple auth providers (GitHub, Google, Okta, SAML, etc.). In production, authentication is not optional. Without it, anyone on the network can access the catalog.

```yaml
auth:
  environment: production
  providers:
    github:
      production:
        clientId: ${AUTH_GITHUB_CLIENT_ID}
        clientSecret: ${AUTH_GITHUB_CLIENT_SECRET}
```

**Scaling considerations:**

- Backstage is a **stateless** Node.js app (state is in the database). You can run multiple replicas behind a load balancer.
- The catalog processing loop should ideally run on a **single instance** to avoid duplicate work. Use the `@backstage/plugin-catalog-backend` leader election or dedicate one replica for processing.
- Search indexing is also best run on a single replica to avoid index conflicts.
- Static frontend assets can be served via CDN for better performance.

### 2.5 Client-Server Architecture

For the exam, understand the request flow:

```
1. User opens browser → loads React SPA from backend (static files)
2. SPA boots → calls backend APIs: /api/catalog, /api/techdocs, etc.
3. Backend plugins handle API calls → query database, call integrations
4. Backend returns JSON → SPA renders UI
5. For external data → SPA calls /api/proxy/* → backend forwards to external APIs
```

**Port defaults:**
- Frontend dev server: `3000` (development only — in production, served by backend)
- Backend: `7007`

**In production**, there is typically a single serving endpoint. The backend serves both the static frontend bundle and its own API routes. A reverse proxy or Kubernetes Ingress sits in front.

---

## War Story: The Case of the 10,000 Orphaned Entities

A platform team at a mid-size fintech company set up GitHub discovery to auto-register every repo in their organization. Within a week, the catalog had 10,000 entities—but morale was not what they expected. Developers were complaining that search was useless. The catalog was full of archived repos, forks, test projects, and abandoned experiments.

Worse, when they tried to clean up by deleting the discovery provider config, the entities did not disappear. They became **orphans**—still visible in the catalog but no longer refreshed. The team spent two days writing scripts to bulk-delete orphans via the catalog API.

**Lessons learned:**
1. Always scope discovery providers with filters (topic tags, path patterns, team ownership).
2. Understand the orphan lifecycle before removing discovery providers.
3. Start with manual registration for your most important services, then gradually expand automated discovery.
4. Use `catalog.rules` to restrict which entity kinds can be registered from which sources.

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Using SQLite in production | It is the default and "works" in dev | Always configure PostgreSQL for production |
| Not scoping discovery providers | GitHub discovery imports *every* repo | Use topic filters, path patterns, or allowlists |
| Expecting instant catalog updates | Developers register YAML and refresh the page immediately | Explain the ~100-200s refresh cycle; use manual refresh API for urgent updates |
| Hardcoding secrets in app-config.yaml | Copy-pasting tokens during setup | Use `${ENV_VAR}` substitution; never commit secrets |
| Forgetting `rules: allow` for entity kinds | Register a Template but it never appears | Each Location source needs explicit `rules` for allowed kinds |
| Running TLS termination in Node.js | Seems simpler than a reverse proxy | Use an ingress controller or load balancer for TLS; Node.js TLS is not needed |
| Not configuring auth for production | Dev mode works without it | Every production instance must have authentication enabled |
| Ignoring orphaned entities | They accumulate silently | Monitor orphan count; establish a cleanup process |

---

## Quiz

Test your understanding of Backstage catalog and infrastructure.

**Q1: Which entity kind represents a boundary between components?**

<details>
<summary>Answer</summary>

**API**. The API kind represents a contract/boundary between components. A Component `providesApi` and another Component `consumesApi`. API entities can describe REST (OpenAPI), gRPC (protobuf), GraphQL, or AsyncAPI interfaces.

</details>

**Q2: What is the default refresh interval for catalog entity processing?**

<details>
<summary>Answer</summary>

Approximately **100-200 seconds**. The catalog processing loop continuously cycles through entities, but there is no guarantee of instant updates. You can trigger a manual refresh via `POST /api/catalog/refresh` with the `entityRef`.

</details>

**Q3: How do you inject secrets into app-config.yaml?**

<details>
<summary>Answer</summary>

Use **environment variable substitution** with `${VARIABLE_NAME}` syntax. For example: `token: ${GITHUB_TOKEN}`. Backstage resolves these at startup from the process environment. Never hardcode secrets in config files.

</details>

**Q4: What is the purpose of the Backstage proxy plugin?**

<details>
<summary>Answer</summary>

The proxy plugin (`/api/proxy`) forwards requests from the frontend through the backend to external APIs. This solves CORS issues and keeps API credentials server-side. The browser never sees the external service tokens—only the backend injects them before forwarding.

</details>

**Q5: Name two ways entities can be registered in the catalog.**

<details>
<summary>Answer</summary>

1. **Manual registration** — via the UI ("Register Existing Component" button) or by adding static Location entries in `app-config.yaml` under `catalog.locations`.
2. **Automated discovery** — using providers like `githubDiscovery`, `gitlab`, or `githubOrg` configured under `catalog.providers` in `app-config.yaml`.

Other valid answers include: custom entity providers (programmatic) or direct API calls.

</details>

**Q6: What database should be used for a production Backstage deployment?**

<details>
<summary>Answer</summary>

**PostgreSQL**. SQLite (or better-sqlite3) is only suitable for local development. PostgreSQL supports concurrent connections, is durable, and handles the catalog processing workload in production. Configure it via `backend.database.client: pg` in `app-config.production.yaml`.

</details>

**Q7: What happens to entities when their source Location is deleted?**

<details>
<summary>Answer</summary>

They become **orphaned entities**. They remain in the catalog but are no longer refreshed from their source. Orphans are flagged with the annotation `backstage.io/orphan: 'true'`. They should be cleaned up either through the UI or via the catalog API (`DELETE /api/catalog/entities/by-uid/<uid>`).

</details>

**Q8: How does configuration layering work in Backstage?**

<details>
<summary>Answer</summary>

You pass multiple `--config` flags when starting the backend: `node packages/backend --config app-config.yaml --config app-config.production.yaml`. Later files override values from earlier files (deep merge). Common pattern: base config, production overrides, and a gitignored local config for personal development settings.

</details>

**Q9: Which annotation links a Backstage entity to its GitHub repository?**

<details>
<summary>Answer</summary>

`github.com/project-slug` with the value `org/repo-name`. For example: `github.com/project-slug: myorg/payments-service`. This annotation is read by GitHub-related plugins to display pull requests, CI status, code owners, and other repo-level information.

</details>

**Q10: In a production Kubernetes deployment of Backstage, why should catalog processing run on a single replica?**

<details>
<summary>Answer</summary>

To avoid **duplicate processing work** and potential conflicts. If multiple replicas all run the processing loop simultaneously, they may redundantly fetch the same sources, create duplicate refresh cycles, and potentially conflict on database writes. The `@backstage/plugin-catalog-backend` supports leader election to ensure only one replica performs catalog processing while others handle API requests.

</details>

---

## Hands-On Exercise: Build a Multi-Entity Catalog

**Objective:** Create a complete catalog structure with multiple entity kinds, register them, and verify the relationships.

**What you'll need:** A running Backstage instance (`npx @backstage/create-app@latest` if you do not have one).

### Step 1: Create the Entity Descriptors

Create a file called `catalog-entities.yaml` in your Backstage project root:

```yaml
---
apiVersion: backstage.io/v1alpha1
kind: Domain
metadata:
  name: commerce
  description: All commerce-related systems
spec:
  owner: group:platform-team

---
apiVersion: backstage.io/v1alpha1
kind: System
metadata:
  name: orders-system
  description: Handles order lifecycle
spec:
  owner: group:backend-team
  domain: commerce

---
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: orders-service
  description: REST API for order management
  annotations:
    backstage.io/techdocs-ref: dir:.
  tags:
    - java
    - springboot
spec:
  type: service
  lifecycle: production
  owner: group:backend-team
  system: orders-system
  providesApis:
    - orders-api
  dependsOn:
    - resource:orders-db

---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: orders-api
  description: Orders REST API
spec:
  type: openapi
  lifecycle: production
  owner: group:backend-team
  system: orders-system
  definition: |
    openapi: "3.0.0"
    info:
      title: Orders API
      version: 1.0.0
    paths:
      /orders:
        get:
          summary: List orders
          responses:
            '200':
              description: OK

---
apiVersion: backstage.io/v1alpha1
kind: Resource
metadata:
  name: orders-db
  description: PostgreSQL database for orders
spec:
  type: database
  owner: group:backend-team
  system: orders-system

---
apiVersion: backstage.io/v1alpha1
kind: Group
metadata:
  name: backend-team
  description: Backend engineering team
spec:
  type: team
  children: []

---
apiVersion: backstage.io/v1alpha1
kind: Group
metadata:
  name: platform-team
  description: Platform engineering team
spec:
  type: team
  children: []
```

### Step 2: Register via app-config.yaml

Add to your `app-config.yaml`:

```yaml
catalog:
  rules:
    - allow: [Component, System, API, Resource, Location, Domain, Group, User, Template]
  locations:
    - type: file
      target: ./catalog-entities.yaml
      rules:
        - allow: [Domain, System, Component, API, Resource, Group]
```

### Step 3: Start Backstage and Verify

```bash
# Start Backstage in development mode
yarn dev
```

Open http://localhost:3000 and verify:

1. Navigate to the **Catalog** — you should see `orders-service` listed as a Component
2. Click on `orders-service` — verify the **System** is `orders-system`
3. Check the **API** tab — `orders-api` should appear under "Provided APIs"
4. Check the **Dependencies** tab — `orders-db` should appear
5. Navigate to `orders-system` — verify it groups the component, API, and resource
6. Navigate to the `commerce` Domain — verify it contains `orders-system`

### Step 4: Test the Proxy (Optional)

Add a proxy endpoint to `app-config.yaml`:

```yaml
proxy:
  endpoints:
    '/jsonplaceholder':
      target: https://jsonplaceholder.typicode.com
```

Restart the backend and test:

```bash
# This request goes through the Backstage proxy
curl http://localhost:7007/api/proxy/jsonplaceholder/todos/1
```

You should get a JSON response from jsonplaceholder.typicode.com, forwarded through your Backstage backend.

### Success Criteria

- [ ] All seven entities appear in the catalog
- [ ] `orders-service` shows correct owner (`backend-team`), system, API, and dependency
- [ ] Domain > System > Component hierarchy is visible in the UI
- [ ] You understand the refresh cycle (modify an entity, observe the delay before the catalog updates)
- [ ] Proxy endpoint returns data from the external API (optional)

---

## Key Takeaways

| Topic | Remember This |
|-------|--------------|
| Entity kinds | 9 built-in: Component, API, Resource, System, Domain, Group, User, Location, Template |
| catalog-info.yaml | Lives in repo root; `apiVersion`, `kind`, `metadata`, `spec` are required |
| Annotations | Connect entities to plugins; key discovery mechanism |
| Registration | Manual (UI or static locations) vs. automated (discovery providers) |
| Processing | Continuous loop with ~100-200s cycle; ingestion → processing → stitching |
| Architecture | React SPA frontend + Node.js backend + PostgreSQL database |
| app-config.yaml | Layered config; `${ENV_VAR}` for secrets; `--config` flag for overrides |
| Proxy | `/api/proxy/*` forwards frontend requests through backend to external APIs |
| Production | PostgreSQL, HTTPS (via ingress), authentication required, single processing replica |

---

## Next Module

**[CBA Track Overview]()** — Domain 4: Templates, documentation-as-code, and the golden path for new services.
