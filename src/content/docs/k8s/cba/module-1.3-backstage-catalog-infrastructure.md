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

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** a comprehensive catalog taxonomy that models your organization's ownership, dependencies, and complex API contracts accurately.
2. **Implement** automated discovery providers and custom entity processors to seamlessly ingest services from external sources into the catalog.
3. **Diagnose** catalog ingestion failures, orphan entity accumulations, and relationship mismatches using the Backstage REST API and cursor-based pagination.
4. **Evaluate** the architectural differences between development SQLite setups and production PostgreSQL deployments, ensuring optimal database scaling.
5. **Debug** configuration layering issues within `app-config.yaml` to ensure secrets and environmental overrides behave as expected during runtime.

## Why This Module Matters

At Spotify, before the open-sourcing of Backstage, engineers faced a massive crisis of cognitive fragmentation. During a major peak traffic event, a critical payment routing service went down. The incident response team mobilized instantly, but they spent the first 45 minutes merely trying to diagnose who owned the service, where the deployment manifests were located, and what the upstream infrastructure dependencies were. Millions of dollars in transactions were delayed. This was not a failure of code; it was a catastrophic failure of context.

The software catalog is the beating heart of Backstage. Without it, Backstage is just a plugin framework with a pretty UI. With it, you have a single pane of glass over every service, API, team, and piece of infrastructure your organization owns. It bridges the gap between raw infrastructure and human accountability, turning tribal knowledge into an explicit graph of relationships. 

The Certified Backstage Associate (CBA) exam dedicates **22% to the catalog** (Domain 3) and another **22% to infrastructure** (Domain 2)—together, that is 44% of your total score. Mastering these concepts is not just about passing an exam; it is about learning how to cure the fundamental organizational chaos that plagues modern microservice architectures. Get these two domains right, and you are nearly halfway to passing before you even touch external plugins or documentation frameworks.

## What You'll Learn

By the end of this comprehensive module, you will deeply understand:
- The fundamental origins, CNCF status, and rapid market adoption of the Backstage framework.
- All eight core entity kinds and the supplementary Template kind, and exactly when to use each one.
- How entities are ingested into the catalog pipeline via manual configuration and automated discovery mechanisms.
- How to strictly structure and validate `catalog-info.yaml` descriptor files using the correct `apiVersion`.
- The Backstage client-server architecture: the React SPA frontend, the Node.js Express backend, the database layer, and the proxy system.
- Production deployment considerations, focusing on migrating from local configurations to resilient setups.
- Deep dives into core capabilities like the Kubernetes plugin and TechDocs generation pipelines.

## Did You Know?

1. Backstage was officially open sourced by Spotify on March 16, 2020, solving years of internal fragmentation.
2. Backstage was promoted from the CNCF Sandbox to the CNCF Incubating maturity level on March 15, 2022.
3. The New Frontend System became the default for newly created Backstage apps in v1.49.0, replacing the `--next` flag with a `--legacy` flag for older applications.
4. The Certified Backstage Associate (CBA) exam is a rigorous 90-minute, proctored, multiple-choice exam costing $250, which includes one free retake offered by the Linux Foundation.

---

## Part 1: The Origins, CNCF Status, and Market Impact

Understanding the lineage of Backstage provides crucial context for its architectural decisions. Backstage was open sourced by Spotify on March 16, 2020. The project quickly gained traction, entering the CNCF Sandbox on September 8, 2020. Recognizing its immense impact on developer productivity, the Cloud Native Computing Foundation promoted Backstage to the CNCF Incubating maturity level on March 15, 2022. 

As of April 2026, Backstage remains at the CNCF Incubating level and has not yet formally graduated, though it serves as the de facto standard for Internal Developer Portals (IDPs). Reports indicate Backstage adoption has grown significantly, with some marketing materials claiming over 3,000 organizations and 2 million developers utilizing it globally. While some blog summaries claim an 89% market share for Backstage in the IDP space, this lacks an authoritative primary source; nevertheless, its dominant footprint in the ecosystem is undeniable. Furthermore, as of early 2026, v1.49.0 is among the most recent major releases, introducing massive systemic upgrades like the New Frontend System.

---

## Part 2: The Software Catalog Entity Model (Domain 3)

The software catalog relies on a strictly typed, graph-based taxonomy. Everything in the Backstage catalog is represented as an entity. 

### Core Entity Kinds

There are eight core built-in entity kinds in the Backstage Software Catalog: Component, API, Resource, System, Domain, User, Group, and Location. Additionally, the `Template` kind is used heavily by the Scaffolder feature.

We can visualize this architecture natively using a Mermaid diagram:

```mermaid
graph TD
    subgraph Ownership
        Component
        API
        Resource
    end
    subgraph Organizational
        Group
        User
    end
    subgraph Catalog_Machinery
        Location
        Template
    end
    subgraph Grouping
        System
        Domain
    end
```

Let us examine the purpose of each entity:

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

A Resource entity specifically describes the infrastructure a Component needs to operate at runtime (e.g., databases, storage buckets, CDNs). Backstage Software Templates (Scaffolder) use a Template entity kind and are defined in YAML stored in a Git repository.

> **Pause and predict**: If you delete a Git repository containing a Template entity, what happens to the entity in Backstage? Will it disappear immediately? Predict the catalog's behavior before continuing.

**Key relationships between entity kinds:**

```mermaid
graph TD
    Domain --> System
    System --> Component
    System --> API
    Component -- ownedBy --> Group_User[Group/User]
    Component -- providesApi --> API
    Component -- consumesApi --> API
    Component -- dependsOn --> Resource
    API -- ownedBy --> Group_User
```

### The catalog-info.yaml Descriptor

The recommended filename for a Backstage catalog descriptor file is `catalog-info.yaml`. Every entity is described by this file, which typically resides at the root of the source repository. The current catalog entity descriptor `apiVersion` is `backstage.io/v1alpha1`; the schema has not been promoted to a stable (non-alpha) version yet.

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

The well-known `spec.lifecycle` values for Component and API entities are: `experimental`, `production`, and `deprecated`. Similarly, the well-known `spec.type` values for a Component entity include `service`, `website`, and `library`.

Entity references in Backstage use the format `[kind]:[namespace]/[name]`, where kind and namespace are optional depending on context. If omitted, the namespace defaults to `default`.

### Annotations and Discovery

Annotations are the conceptual glue between catalog entities and the broader ecosystem of Backstage plugins. They instruct plugins exactly where to look to retrieve external telemetry, documentation, or operational metrics.

| Annotation | What It Does |
|------------|-------------|
| `github.com/project-slug` | Links entity to a GitHub repo (`org/repo`) |
| `backstage.io/techdocs-ref` | Tells TechDocs where to find docs (`dir:.` = same repo) |
| `backstage.io/source-location` | Source code URL for the entity |
| `jenkins.io/job-full-name` | Links to a Jenkins job |
| `pagerduty.com/service-id` | Links to PagerDuty for on-call info |
| `backstage.io/managed-by-location` | Which Location entity registered this entity |
| `backstage.io/managed-by-origin-location` | Original Location that first introduced the entity |

---

## Part 3: Entity Ingestion, Providers, and Processors

Backstage catalog entity ingestion relies on two mechanisms: Entity Providers (which read raw definitions from sources) and Processors (which analyze/transform entity data).

### Manual Registration

You can statically define locations directly within the configuration file to manually onboard entities:

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

You can also define a pure Location entity directly in YAML:

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

### Automated Ingestion via Discovery

Backstage ships built-in discovery integrations for GitHub, GitLab, and Bitbucket Server. These providers scan entire organizations or groups to map out the topology automatically.

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

> **Stop and think**: If a developer changes the `catalogFile` path setting in the provider to look for `.backstage/catalog.yaml` instead of `catalog-info.yaml`, what must happen across all the organization's repositories for the next ingestion cycle to succeed?

### Entity Processors and Pipeline Stitching

The entity lifecycle moves from ingestion to processing and finally stitching.

```mermaid
sequenceDiagram
    participant Ingestion
    participant Processing
    participant Stitching
    Ingestion->>Processing: Feed Raw Entity Data
    Note over Processing: Validate YAML, Run Processors
    Processing->>Stitching: Emit Validated Entities
    Note over Stitching: Resolve Refs, Build Graph
    Stitching-->>Catalog DB: Final Visible Entity
```

Custom providers allow for arbitrary integration:

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

---

## Part 4: API Pagination and Troubleshooting

The Backstage Catalog REST API exposes a `GET /entities/by-query` endpoint with cursor-based pagination, superseding the older paginated `GET /entities` endpoint. Cursor pagination offers robust stability against data changes during reads, returning a token (cursor) that acts as a secure pointer to the next page.

When an entity reference is severed, you encounter orphans.

```bash
# List orphaned entities via the Backstage catalog API
curl http://localhost:7007/api/catalog/entities?filter=metadata.annotations.backstage.io/orphan=true

# Delete a specific orphaned entity
curl -X DELETE http://localhost:7007/api/catalog/entities/by-uid/<entity-uid>
```

You can force processing manually:

```bash
# Refresh a specific entity
curl -X POST http://localhost:7007/api/catalog/refresh \
  -H 'Content-Type: application/json' \
  -d '{"entityRef": "component:default/payments-service"}'
```

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Entity never shows up | Invalid YAML or schema violation | Check the catalog import page for errors |
| Entity appears then disappears | `rules` in app-config block the entity kind | Add the kind to `rules: allow` |
| Stale data after repo update | Refresh cycle has not run yet | Manually refresh via catalog API or wait ~100-200s |
| Entity shows as orphaned | The Location that registered it was deleted | Re-register or remove the orphan |
| Relationships broken | Referenced entity name does not match | Check exact `name` fields; they are case-sensitive |

---

## Part 5: Infrastructure Architecture (Domain 2)

Backstage utilizes a discrete client-server separation. The New Frontend System became the default in v1.49.0, modernizing how plugins bind to the application shell.

```mermaid
flowchart TD
    Browser[BROWSER Client]
    subgraph SPA[Backstage Frontend App React SPA]
        CatF[Catalog Plugin]
        TechF[TechDocs Plugin]
        ScaffF[Scaffolder Plugin]
    end
    Browser --> SPA
    SPA -- HTTP/REST API calls --> Backend

    subgraph Backend[BACKSTAGE BACKEND Node.js]
        CatB[Catalog Backend]
        TechB[TechDocs Backend]
        AuthB[Auth / Proxy]
    end

    subgraph Storage[Storage]
        DB[(Database Postgres)]
    end

    Backend --> DB
```

### Configuration Loading

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

Config layering merges values at startup:

```bash
# You can pass multiple config files — later files override earlier ones
node packages/backend --config app-config.yaml --config app-config.production.yaml
```

> **Stop and think**: If a frontend plugin makes a direct fetch call to an external API (like GitHub) from the user's browser, what security and network issues might occur? Think about CORS and token exposure.

### The Proxy System

The Proxy routes client browser requests safely through the backend to external sources, masking secret tokens.

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

```mermaid
sequenceDiagram
    participant Browser
    participant Backend as Backstage Backend
    participant External as External API
    
    Browser->>Backend: GET /api/proxy/pagerduty/services/PXXXXXX
    Backend->>External: GET /services/PXXXXXX (Authorization: Token ...)
    External-->>Backend: (response)
    Backend-->>Browser: (response forwarded)
```

In a production setup, Backstage supports PostgreSQL (recommended for production) and SQLite (used for development/testing) as catalog backend databases.

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

```yaml
app:
  baseUrl: https://backstage.mycompany.com

backend:
  baseUrl: https://backstage.mycompany.com
  cors:
    origin: https://backstage.mycompany.com
```

```yaml
auth:
  environment: production
  providers:
    github:
      production:
        clientId: ${AUTH_GITHUB_CLIENT_ID}
        clientSecret: ${AUTH_GITHUB_CLIENT_SECRET}
```

```text
1. User opens browser → loads React SPA from backend (static files)
2. SPA boots → calls backend APIs: /api/catalog, /api/techdocs, etc.
3. Backend plugins handle API calls → query database, call integrations
4. Backend returns JSON → SPA renders UI
5. For external data → SPA calls /api/proxy/* → backend forwards to external APIs
```

---

## Part 6: Core Extensions: Kubernetes and TechDocs

To truly understand Domain 2 of the CBA, you must grasp core plugins. 

**The Kubernetes Plugin**: The Backstage Kubernetes feature consists of two distinct packages: `@backstage/plugin-kubernetes` (the frontend UI surfacing health) and `@backstage/plugin-kubernetes-backend` (which handles cluster connectivity logic and service accounts). Historical references are OK (e.g., feature X was introduced in v1.1, v1.2, v1.3, v1.4, v1.5, v1.6, and v1.7). For modern production setups today, Kubernetes versions must strictly be v1.35 or higher. Do not deploy end-of-life API objects when binding Backstage ServiceAccounts to your clusters.

**TechDocs**: TechDocs uses MkDocs under the hood to convert Markdown files into a static HTML documentation site. TechDocs recommends generating docs on CI/CD and storing output to an external storage provider (e.g., AWS S3 or Google Cloud Storage) rather than generating dynamically on the Backstage server itself. This architectural choice dramatically reduces CPU load on the Backstage backend.

---

## War Story: The 10,000 Entity Tsunami

A platform team at a mid-size fintech company set up GitHub discovery to auto-register every repo in their organization. Within a week, the catalog had 10,000 entities—but morale was awful. The catalog ingested archived repositories, ancient forks, and experimental prototypes without prejudice. Search became absolutely useless.

When they removed the configuration block in panic, the entities remained. They became orphaned entities. Backstage correctly tracked that they had been registered via a Location that no longer existed, flagging them for human review. The team spent a weekend writing a Python loop calling `DELETE /api/catalog/entities/by-uid/<uid>` to purge the ghost data.

**The Lesson:** Always scope discovery providers using repository topic tags or explicit path exclusions to prevent digital hoarding.

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

**Q1: Which entity kind represents a boundary between components?**
> **Scenario**: You have two microservices. The frontend service needs to fetch data from the backend service. To properly document the contract and endpoints between these two components in Backstage, which entity kind should you use?
<details>
<summary>Answer</summary>

You should use the **API** kind. The API kind represents a contract or boundary between components, ensuring that dependencies and communication interfaces are explicitly defined in the catalog. A Component `providesApi` and another Component `consumesApi`. By registering it as an API entity, Backstage can display the exact specifications (such as OpenAPI, gRPC, GraphQL, or AsyncAPI) directly in the interface. This makes it clear to consumers how to interact with the service and who owns the contract.

</details>

**Q2: What is the default refresh interval for catalog entity processing?**
> **Scenario**: Your team just pushed a commit updating the `catalog-info.yaml` file to add a new tag. A developer checks Backstage immediately but does not see the new tag. Assuming no errors occurred, why is this happening and when should they expect to see the change automatically?
<details>
<summary>Answer</summary>

The update is not instantly reflected because Backstage relies on a background processing loop that has a default refresh interval of approximately **100-200 seconds**. The catalog processing loop continuously cycles through all registered entities, fetching their latest state from the source location. Because there is no guarantee of instant updates, developers must either wait for the next cycle to complete or manually trigger a refresh via `POST /api/catalog/refresh` with the `entityRef`. This asynchronous approach prevents the backend from being overwhelmed by simultaneous source repository updates.

</details>

**Q3: How do you inject secrets into app-config.yaml?**
> **Scenario**: You are deploying Backstage to a production environment and need to configure the GitHub integration to read repository data. You have a `GITHUB_TOKEN` that must be kept secure. How should you provide this secret to the `app-config.yaml` file without hardcoding it?
<details>
<summary>Answer</summary>

You must use **environment variable substitution** with the `${VARIABLE_NAME}` syntax, such as `token: ${GITHUB_TOKEN}`. Backstage resolves these values at startup by reading them directly from the host process's environment variables. You should never hardcode secrets in configuration files because they are often committed to version control, which poses a severe security risk. Injecting them via environment variables ensures that sensitive credentials remain strictly within the runtime environment.

</details>

**Q4: What is the purpose of the Backstage proxy plugin?**
> **Scenario**: Your Backstage frontend needs to display real-time incident data from PagerDuty. However, querying the PagerDuty API directly from the browser would expose your organization's API token to the client. How does Backstage securely handle this request?
<details>
<summary>Answer</summary>

Backstage securely handles this by using the **proxy plugin** (`/api/proxy`), which forwards requests from the frontend through the backend to external APIs. By routing the request through the backend, the server can safely inject the required authorization headers (such as the PagerDuty API token) before forwarding the request to the external service. The browser never sees the external service tokens, which prevents them from being leaked or exploited by malicious scripts. Furthermore, this pattern effectively circumvents CORS (Cross-Origin Resource Sharing) restrictions that would otherwise block direct client-side requests.

</details>

**Q5: Name two ways entities can be registered in the catalog.**
> **Scenario**: A new team is onboarding into your organization and wants their existing microservices to appear in the Backstage catalog. They can either add their services one-by-one or have them automatically picked up. What are the two primary mechanisms provided by Backstage to achieve this?
<details>
<summary>Answer</summary>

Entities can be registered through **manual registration** or **automated discovery**. Manual registration involves explicitly adding static Location entries in `app-config.yaml` under `catalog.locations` or clicking the "Register Existing Component" button in the UI. Automated discovery, on the other hand, utilizes built-in providers (like `githubDiscovery`, `gitlab`, or `githubOrg`) configured under `catalog.providers` to automatically scan repositories and organizational groups for `catalog-info.yaml` files. Automated discovery is highly recommended for scaling, while manual registration is useful for testing or isolated components.

</details>

**Q6: What database should be used for a production Backstage deployment?**
> **Scenario**: You have successfully tested Backstage locally using its default in-memory database and are now writing the deployment manifests for a production Kubernetes cluster. To ensure high availability and data persistence, which database backend must you configure?
<details>
<summary>Answer</summary>

You must use **PostgreSQL** for a production deployment. The default SQLite (or `better-sqlite3`) database is strictly intended for local development and testing, as it lacks the concurrency and durability required for real-world usage. PostgreSQL supports concurrent connections, ensures data persistence, and can efficiently handle the intense catalog processing workloads of a production environment. You configure it by setting `backend.database.client: pg` in your `app-config.production.yaml` file.

</details>

**Q7: What happens to entities when their source Location is deleted?**
> **Scenario**: A developer accidentally deletes a repository containing the `catalog-info.yaml` for a deprecated service. The repository was originally ingested via a static Location entry in Backstage. What will be the state of this entity in the Backstage catalog?
<details>
<summary>Answer</summary>

The entity will become an **orphaned entity**. It remains in the catalog database but is no longer actively refreshed from its source because the origin Location is missing. Backstage marks these entities by attaching the annotation `backstage.io/orphan: 'true'`, alerting administrators that the entity is disconnected. These orphans must be explicitly cleaned up, either manually through the Backstage UI or programmatically via the catalog API (`DELETE /api/catalog/entities/by-uid/<uid>`), to prevent the catalog from accumulating stale data.

</details>

**Q8: How does configuration layering work in Backstage?**
> **Scenario**: You want to run Backstage locally but need to override some of the base configuration settings with production-specific values when deploying to your Kubernetes cluster. How does Backstage process multiple configuration files to achieve this?
<details>
<summary>Answer</summary>

Backstage achieves this through **configuration layering**, where you pass multiple `--config` flags when starting the backend (e.g., `node packages/backend --config app-config.yaml --config app-config.production.yaml`). The framework reads the files in the order they are provided, using a deep merge strategy where values in later files override the corresponding values from earlier files. This pattern allows teams to maintain a common base configuration while safely applying environment-specific overrides, such as database credentials or authentication settings for production. For example, your base config might define the catalog providers, while your production config injects the necessary OAuth client secrets. This separation prevents accidental leakage of production secrets in local environments.

</details>

**Q9: Which annotation links a Backstage entity to its GitHub repository?**
> **Scenario**: You have registered a new Component in Backstage and want the GitHub plugin to display its recent pull requests, CI status, and code owners on the entity's overview page. Which specific metadata field must you add to your `catalog-info.yaml` to enable this?
<details>
<summary>Answer</summary>

You must add the **`github.com/project-slug`** annotation with the value formatted as `org/repo-name`. For example, specifying `github.com/project-slug: myorg/payments-service` tells Backstage exactly where the source code resides. This annotation acts as the crucial linkage that allows GitHub-related plugins to fetch and surface repository-level telemetry directly in the UI. Without it, the plugins lack the context needed to associate the catalog entity with its upstream source repository.

</details>

**Q10: In a production Kubernetes deployment of Backstage, why should catalog processing run on a single replica?**
> **Scenario**: You are scaling your Backstage backend deployment to 3 replicas to handle increased API traffic. However, you notice unexpected database lock errors and duplicate processing cycles in the logs. What architectural consideration regarding catalog processing was missed?
<details>
<summary>Answer</summary>

The issue occurs because catalog processing should ideally run on a **single replica** to avoid duplicate processing work and database conflicts. If multiple replicas simultaneously execute the catalog processing loop, they may redundantly fetch data from the same external sources and attempt conflicting database writes. To safely scale the backend while preventing these issues, the `@backstage/plugin-catalog-backend` supports leader election. This mechanism ensures that only one replica actively performs catalog processing tasks while all other replicas focus solely on serving API requests.

</details>

---

## Hands-On Exercise: Build a Multi-Entity Catalog

**Objective:** Create a complete catalog structure with multiple entity kinds, register them, and verify the robust relational dependency graph.

### Step 1: Define the Descriptors

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

### Step 2: Register Entities Config

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

### Step 3: Run Validation

```bash
# Start Backstage in development mode
yarn dev
```

### Step 4: Proxy Binding

```yaml
proxy:
  endpoints:
    '/jsonplaceholder':
      target: https://jsonplaceholder.typicode.com
```

```bash
# This request goes through the Backstage proxy
curl http://localhost:7007/api/proxy/jsonplaceholder/todos/1
```

### Success Checklist
<details>
<summary>View Checklist</summary>

- [ ] All entities appear cleanly in the UI.
- [ ] `orders-service` maps exactly to the `orders-system` hierarchy.
- [ ] The Proxy endpoint forwards requests correctly without exposing API keys locally.

</details>

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

## Next Module

**[CBA Track Overview]()** — Domain 4: Templates, documentation-as-code, and mastering the golden path for executing resilient scaffolding deployments. Prepare to build your first template in the next session!