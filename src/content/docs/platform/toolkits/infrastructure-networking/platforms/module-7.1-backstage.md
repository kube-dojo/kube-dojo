---
title: "Module 7.1: Backstage"
slug: platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-60 minutes

## Overview

"Where do I find the API docs?" "Who owns this service?" "How do I create a new microservice?" If your developers ask these questions repeatedly, you need an Internal Developer Portal. Backstage, created by Spotify and donated to CNCF, centralizes developer experience—service catalog, documentation, templates, and plugins—in one place.

**What You'll Learn**:
- Backstage architecture and core concepts
- Software Catalog and service ownership
- Software Templates for golden paths
- Plugin ecosystem and customization

**Prerequisites**:
- [Platform Engineering Discipline](../../../disciplines/core-platform/platform-engineering/)
- Node.js basics (for customization)
- Kubernetes fundamentals

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Backstage as an internal developer portal with service catalog and software templates**
- **Configure Backstage plugins for CI/CD visibility, Kubernetes dashboards, and documentation integration**
- **Implement software templates for standardized service scaffolding with built-in compliance guardrails**
- **Integrate Backstage with existing toolchain (GitHub, ArgoCD, PagerDuty) for unified developer experience**


## Why This Module Matters

Platform teams build great tools. Developers can't find them. Backstage solves the discoverability problem by creating a single pane of glass for everything developers need. It's not just a catalog—it's a developer portal that reduces cognitive load and enables self-service.

> 💡 **Did You Know?** Spotify created Backstage to manage their 2,000+ microservices and 400+ teams. Before Backstage, new engineers spent weeks figuring out where things lived. After Backstage, onboarding time dropped from weeks to days. Spotify open-sourced it in 2020, and it became a CNCF incubating project.

---

## The Developer Experience Problem

```
WITHOUT INTERNAL DEVELOPER PORTAL
════════════════════════════════════════════════════════════════════

Developer needs to:

Find API docs          → Search Confluence, Notion, GitHub, Slack
Check service health   → Log into multiple dashboards
Create new service     → Copy paste from old repo, modify, hope
Find service owner     → Ask around, check git blame, Slack channels
View deployment status → Check ArgoCD, Jenkins, Spinnaker
Access database        → Ask DBA, create ticket, wait

Result: Hours of searching, context switching, tribal knowledge

═══════════════════════════════════════════════════════════════════

WITH BACKSTAGE
════════════════════════════════════════════════════════════════════

Developer needs to:

Find API docs          → Backstage → Component → Docs tab
Check service health   → Backstage → Component → Dashboard
Create new service     → Backstage → Create → Select template
Find service owner     → Backstage → Component → Owner
View deployment status → Backstage → Component → Kubernetes tab
Access database        → Backstage → Component → Links

Result: Minutes to find anything, self-service, documented paths
```

---

## Architecture

```
BACKSTAGE ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                     BACKSTAGE APP                                │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    FRONTEND (React)                        │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │ │
│  │  │ Catalog │  │  Docs   │  │Templates│  │ Plugins │      │ │
│  │  │  UI     │  │TechDocs │  │ Wizard  │  │  ...    │      │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐ │
│  │                    BACKEND (Node.js)                       │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │ │
│  │  │ Catalog │  │ Scaffolder│ │TechDocs │  │  Auth   │      │ │
│  │  │ Backend │  │ Backend  │ │ Backend │  │ Backend │      │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐ │
│  │                     DATABASE                               │ │
│  │              (PostgreSQL, SQLite)                          │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ Integrates with
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                              │
│                                                                  │
│  GitHub  │  GitLab  │  Kubernetes  │  PagerDuty  │  Datadog   │
│  Jenkins │  ArgoCD  │  Prometheus  │  Slack      │  LDAP      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Features

| Feature | Description |
|---------|-------------|
| **Software Catalog** | Service registry with ownership, dependencies, metadata |
| **TechDocs** | Documentation as code, rendered from markdown |
| **Software Templates** | Scaffolding for new services (golden paths) |
| **Plugins** | Extensible architecture for custom integrations |
| **Search** | Unified search across all registered entities |

---

## Installation

```bash
# Create new Backstage app
npx @backstage/create-app@latest

# Follow prompts, choose:
# - App name: backstage
# - Database: PostgreSQL (for production)

cd backstage

# Start development server
yarn dev

# Access at http://localhost:3000
```

### Production Deployment

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backstage
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backstage
  template:
    spec:
      containers:
      - name: backstage
        image: backstage:latest
        ports:
        - containerPort: 7007
        env:
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: backstage-secrets
              key: POSTGRES_HOST
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: backstage-secrets
              key: POSTGRES_USER
```

---

## Software Catalog

### Catalog Entities

```yaml
# catalog-info.yaml (in your service repo)
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payment-service
  description: Handles payment processing
  annotations:
    github.com/project-slug: myorg/payment-service
    backstage.io/techdocs-ref: dir:.
    prometheus.io/rule: payment_service_errors_total
  tags:
    - java
    - spring-boot
    - payments
  links:
    - url: https://grafana.example.com/d/payments
      title: Grafana Dashboard
    - url: https://runbooks.example.com/payments
      title: Runbook
spec:
  type: service
  lifecycle: production
  owner: team-payments
  system: checkout
  providesApis:
    - payments-api
  consumesApis:
    - users-api
    - inventory-api
  dependsOn:
    - resource:payments-db
```

### Entity Types

| Kind | Description | Example |
|------|-------------|---------|
| **Component** | A piece of software | microservice, library, website |
| **API** | Interface definition | REST, gRPC, GraphQL |
| **Resource** | Infrastructure | database, S3 bucket, queue |
| **System** | Collection of components | checkout system |
| **Domain** | Business area | payments domain |
| **Group** | Team | payments-team |
| **User** | Individual | john.doe |

### Entity Relationships

```
ENTITY RELATIONSHIPS
════════════════════════════════════════════════════════════════════

                    ┌─────────────┐
                    │   Domain    │
                    │  (payments) │
                    └──────┬──────┘
                           │ hasPart
                           ▼
                    ┌─────────────┐
                    │   System    │
                    │ (checkout)  │
                    └──────┬──────┘
                           │ hasPart
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │Component │ │Component │ │   API    │
        │(frontend)│ │(backend) │ │(payments)│
        └──────────┘ └────┬─────┘ └──────────┘
                          │
            ┌─────────────┼─────────────┐
            │ dependsOn   │ consumesApi │
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ Resource │  │   API    │  │   API    │
      │  (db)    │  │ (users)  │  │(inventory)│
      └──────────┘  └──────────┘  └──────────┘

Owner: Group/User owns Components, Systems, APIs, Resources
```

> 💡 **Did You Know?** Backstage automatically discovers catalog files from GitHub/GitLab by scanning for `catalog-info.yaml` in repositories. You can set up a GitHub integration that auto-discovers all repos in your organization, meaning teams just need to add the YAML file and their service appears in Backstage automatically.

---

## TechDocs

### Documentation as Code

```
TECHDOCS WORKFLOW
════════════════════════════════════════════════════════════════════

1. Developer writes docs in Markdown (in repo)
2. TechDocs builds docs using MkDocs
3. Docs are published to storage (S3, GCS)
4. Backstage renders docs in browser

├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── api-reference.md
│   └── architecture.md
├── mkdocs.yml
└── catalog-info.yaml
```

### MkDocs Configuration

```yaml
# mkdocs.yml
site_name: Payment Service
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - API Reference: api-reference.md
  - Architecture: architecture.md

plugins:
  - techdocs-core
```

### Catalog Reference

```yaml
# catalog-info.yaml
metadata:
  annotations:
    backstage.io/techdocs-ref: dir:.  # Docs in same repo
    # OR
    backstage.io/techdocs-ref: url:https://github.com/org/docs
```

---

## Software Templates

### Golden Paths

Software Templates create "golden paths"—pre-approved ways to create new services, libraries, or infrastructure.

```yaml
# template.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: spring-boot-service
  title: Spring Boot Microservice
  description: Create a new Spring Boot microservice with CI/CD
  tags:
    - java
    - spring-boot
    - recommended
spec:
  owner: platform-team
  type: service

  parameters:
    - title: Service Information
      required:
        - name
        - description
        - owner
      properties:
        name:
          title: Service Name
          type: string
          description: Name of the service (lowercase, no spaces)
          pattern: '^[a-z][a-z0-9-]*$'
        description:
          title: Description
          type: string
          description: What does this service do?
        owner:
          title: Owner
          type: string
          description: Team that owns this service
          ui:field: OwnerPicker
          ui:options:
            catalogFilter:
              kind: Group

    - title: Repository
      required:
        - repoUrl
      properties:
        repoUrl:
          title: Repository Location
          type: string
          ui:field: RepoUrlPicker
          ui:options:
            allowedHosts:
              - github.com

  steps:
    - id: fetch-template
      name: Fetch Template
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          description: ${{ parameters.description }}
          owner: ${{ parameters.owner }}

    - id: publish
      name: Publish to GitHub
      action: publish:github
      input:
        repoUrl: ${{ parameters.repoUrl }}
        description: ${{ parameters.description }}
        defaultBranch: main

    - id: register
      name: Register in Catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps['publish'].output.repoContentsUrl }}
        catalogInfoPath: '/catalog-info.yaml'

  output:
    links:
      - title: Repository
        url: ${{ steps['publish'].output.remoteUrl }}
      - title: Open in Catalog
        icon: catalog
        entityRef: ${{ steps['register'].output.entityRef }}
```

### Template Skeleton

```
skeleton/
├── catalog-info.yaml
├── Dockerfile
├── pom.xml
├── README.md
├── src/
│   └── main/
│       └── java/
│           └── com/example/${{values.name}}/
│               └── Application.java
└── .github/
    └── workflows/
        └── ci.yaml
```

```yaml
# skeleton/catalog-info.yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: ${{ values.name }}
  description: ${{ values.description }}
spec:
  type: service
  lifecycle: experimental
  owner: ${{ values.owner }}
```

> 💡 **Did You Know?** Spotify uses Software Templates to standardize how all 2,000+ services are created. Every new service starts from a template that includes CI/CD, observability, security scanning, and documentation—all pre-configured. This reduces "time to first deployment" from days to minutes.

> 💡 **Did You Know?** Backstage's plugin ecosystem has grown to over 100 community plugins, from Kubernetes and ArgoCD to PagerDuty and cost management. The modular architecture means you can add capabilities without modifying core Backstage code. Companies like Netflix, American Airlines, and Expedia have built custom plugins for their internal tooling—and many have contributed them back to the community.

---

## Plugin Ecosystem

### Popular Plugins

| Plugin | Purpose |
|--------|---------|
| **Kubernetes** | View pods, deployments, logs |
| **GitHub Actions** | CI/CD status |
| **ArgoCD** | GitOps deployment status |
| **PagerDuty** | On-call schedules, incidents |
| **Tech Radar** | Technology standards visualization |
| **Cost Insights** | Cloud spend per service |
| **API Docs** | OpenAPI/Swagger viewer |

### Installing Plugins

```bash
# Add plugin dependency
yarn add --cwd packages/app @backstage/plugin-kubernetes

# packages/app/src/App.tsx
import { EntityKubernetesContent } from '@backstage/plugin-kubernetes';

// Add to entity page routes
```

### Custom Plugin Development

```typescript
// plugins/my-plugin/src/plugin.ts
import { createPlugin, createRoutableExtension } from '@backstage/core-plugin-api';

export const myPlugin = createPlugin({
  id: 'my-plugin',
  routes: {
    root: rootRouteRef,
  },
});

export const MyPluginPage = myPlugin.provide(
  createRoutableExtension({
    name: 'MyPluginPage',
    component: () => import('./components/MyPage').then(m => m.MyPage),
    mountPoint: rootRouteRef,
  }),
);
```

---

## Configuration

### app-config.yaml

```yaml
app:
  title: Acme Developer Portal
  baseUrl: https://backstage.acme.com

organization:
  name: Acme Corp

backend:
  baseUrl: https://backstage.acme.com
  database:
    client: pg
    connection:
      host: ${POSTGRES_HOST}
      port: 5432
      user: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}

integrations:
  github:
    - host: github.com
      token: ${GITHUB_TOKEN}

catalog:
  import:
    entityFilename: catalog-info.yaml
  rules:
    - allow: [Component, API, Resource, System, Domain, Group, User]
  locations:
    - type: url
      target: https://github.com/acme/backstage-catalog/blob/main/all.yaml
    - type: github-discovery
      target: https://github.com/acme

auth:
  providers:
    github:
      development:
        clientId: ${GITHUB_CLIENT_ID}
        clientSecret: ${GITHUB_CLIENT_SECRET}

techdocs:
  builder: 'external'
  publisher:
    type: 'awsS3'
    awsS3:
      bucketName: backstage-techdocs
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not defining ownership | "Who owns this?" still unanswered | Require owner in all catalog entries |
| Templates without CI/CD | Golden path doesn't include deployment | Include full pipeline in templates |
| Stale catalog data | Entities don't reflect reality | Auto-discovery + entity processors |
| Too many entity types | Confusing taxonomy | Start simple, add as needed |
| No documentation standards | TechDocs quality varies wildly | Provide documentation templates |
| Ignoring adoption | Build it and they won't come | Measure usage, iterate on UX |

---

## War Story: The Portal Nobody Used

*A platform team spent 6 months building a beautiful Backstage deployment. After launch, adoption was 10%.*

**What went wrong**:
1. Catalog required manual registration (developers didn't bother)
2. No Software Templates (no immediate value)
3. No integrations with existing tools (GitHub, Kubernetes)
4. Launched without documentation

**The fix**:
1. Enabled GitHub auto-discovery (instant 500+ services in catalog)
2. Created 3 golden path templates (immediate value)
3. Added Kubernetes plugin (see deployments in Backstage)
4. Required catalog-info.yaml in PR checklist

**Adoption after 3 months**: 85%

**Lesson**: Backstage is a product. Treat it like one—understand your users, provide immediate value, iterate based on feedback.

---

## Quiz

### Question 1
What's the difference between a Component and a System in Backstage?

<details>
<summary>Show Answer</summary>

**Component**: A single piece of software (deployable unit)
- Examples: microservice, website, mobile app, library
- Has code, can be deployed
- Owned by a team

**System**: A collection of Components that work together
- Examples: checkout system, search platform
- Logical grouping
- May span multiple teams

Hierarchy: Domain → System → Component

</details>

### Question 2
How do Software Templates create "golden paths"?

<details>
<summary>Show Answer</summary>

Golden paths are opinionated, pre-approved ways to do common tasks:

**Without golden path**:
1. Developer copies old repo
2. Removes old code, keeps structure
3. Misses CI/CD config
4. Forgets security scanning
5. Documentation? What documentation?

**With Software Template**:
1. Developer fills out form in Backstage
2. Template creates repo with:
   - Correct structure
   - CI/CD pipeline
   - Security scanning
   - Documentation skeleton
   - Catalog registration
3. Ready to code in minutes

Templates encode best practices into the starting point.

</details>

### Question 3
Why should you use GitHub auto-discovery instead of manual catalog registration?

<details>
<summary>Show Answer</summary>

**Manual registration problems**:
- Developers forget to add `catalog-info.yaml`
- Catalog becomes stale
- Low adoption (extra work)
- Incomplete service map

**Auto-discovery benefits**:
- Scans all repos automatically
- Finds `catalog-info.yaml` files
- Catalog always up-to-date
- Higher adoption (less work)
- Complete picture of services

**Best practice**: Use auto-discovery, but require `catalog-info.yaml` in repo templates and PR checklists.

</details>

---

## Hands-On Exercise

### Objective
Deploy Backstage locally and register a service in the catalog.

### Environment Setup

```bash
# Create Backstage app
npx @backstage/create-app@latest --skip-install
cd backstage
yarn install

# Start development server
yarn dev
```

### Tasks

1. **Access Backstage**:
   - Open http://localhost:3000
   - Explore the default interface

2. **Create catalog entry**:
   ```yaml
   # my-service/catalog-info.yaml
   apiVersion: backstage.io/v1alpha1
   kind: Component
   metadata:
     name: my-first-service
     description: A sample service for learning Backstage
     tags:
       - learning
       - sample
   spec:
     type: service
     lifecycle: experimental
     owner: guests
   ```

3. **Register in Backstage**:
   - Click "Create..." → "Register Existing Component"
   - Enter path to your `catalog-info.yaml`
   - Or add to `app-config.yaml`:
     ```yaml
     catalog:
       locations:
         - type: file
           target: /path/to/my-service/catalog-info.yaml
     ```

4. **Add documentation**:
   ```yaml
   # mkdocs.yml
   site_name: My First Service
   plugins:
     - techdocs-core
   ```

   ```markdown
   # docs/index.md
   # My First Service

   Welcome to my first service documentation!
   ```

5. **Update catalog entry**:
   ```yaml
   metadata:
     annotations:
       backstage.io/techdocs-ref: dir:.
   ```

6. **View in Backstage**:
   - Navigate to catalog
   - Find your service
   - Check the Docs tab

### Success Criteria
- [ ] Backstage running locally
- [ ] Component registered in catalog
- [ ] Can view component details
- [ ] Documentation renders (if configured)

### Bonus Challenge
Create a Software Template that scaffolds a simple Node.js service with a README and catalog-info.yaml.

---

## Further Reading

- [Backstage Documentation](https://backstage.io/docs/)
- [Backstage Plugin Marketplace](https://backstage.io/plugins)
- [Spotify Engineering Blog - Backstage](https://engineering.atspotify.com/tag/backstage/)
- [CNCF Backstage Project](https://www.cncf.io/projects/backstage/)

---

## Next Module

Continue to [Module 7.2: Crossplane](../module-7.2-crossplane/) to learn infrastructure provisioning using Kubernetes-native APIs.

---

*"The best developer experience is one where developers don't think about infrastructure. Backstage makes that possible."*
