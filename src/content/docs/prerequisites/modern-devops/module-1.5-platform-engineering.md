---
title: "Module 1.5: Platform Engineering Concepts"
slug: prerequisites/modern-devops/module-1.5-platform-engineering/
sidebar:
  order: 6
---
> **Complexity**: `[MEDIUM]` - Strategic perspective
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Modules 1-4 (IaC, GitOps, CI/CD, Observability)

---

## Why This Module Matters

As organizations adopt Kubernetes, a problem emerges: Kubernetes is complex, and not every developer wants (or should need) to understand it deeply. Platform Engineering solves this by building internal platforms that abstract complexity, letting developers focus on code while platform teams handle infrastructure. Understanding this trend helps you position your skills effectively.

---

## The Problem Platform Engineering Solves

```
┌─────────────────────────────────────────────────────────────┐
│              THE COGNITIVE LOAD PROBLEM                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What a developer needs to do:                              │
│  ✓ Write code                                              │
│  ✓ Write tests                                             │
│  ✓ Deploy to production                                    │
│                                                             │
│  What they often have to learn:                            │
│  - Kubernetes (Pods, Deployments, Services, Ingress...)   │
│  - Helm charts                                             │
│  - CI/CD pipelines                                         │
│  - GitOps workflows                                        │
│  - Monitoring setup                                        │
│  - Secret management                                       │
│  - Network policies                                        │
│  - Resource quotas                                         │
│  - ... and more                                            │
│                                                             │
│  Result: Cognitive overload, slow onboarding, mistakes    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## What is Platform Engineering?

Platform Engineering is **the discipline of designing and building toolchains and workflows that enable developer self-service in the cloud-native era**.

```
┌─────────────────────────────────────────────────────────────┐
│              THE PLATFORM MODEL                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    DEVELOPERS                               │
│                        │                                    │
│                        │ "I need a database"               │
│                        │ "Deploy my app"                   │
│                        │ "Show me logs"                    │
│                        ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              INTERNAL DEVELOPER PLATFORM             │   │
│  │                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│  │  │Self-serve│  │Templates │  │Guardrails│         │   │
│  │  │  Portal  │  │& Golden  │  │& Policies│         │   │
│  │  │          │  │  Paths   │  │          │         │   │
│  │  └──────────┘  └──────────┘  └──────────┘         │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                        │                                    │
│                        ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              INFRASTRUCTURE                          │   │
│  │  Kubernetes • Cloud • Databases • Monitoring        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Developers get self-service without complexity            │
│  Platform team maintains standards and security            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## DevOps vs Platform Engineering

```
┌─────────────────────────────────────────────────────────────┐
│              EVOLUTION OF PRACTICES                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pre-DevOps:                                               │
│  ┌─────┐ throws code over wall ┌─────┐                    │
│  │ Dev │ ────────────────────► │ Ops │                    │
│  └─────┘                       └─────┘                     │
│  Slow, blame game, silos                                   │
│                                                             │
│  DevOps:                                                   │
│  ┌───────────────────────────────────┐                    │
│  │           Dev + Ops               │                    │
│  │   "You build it, you run it"      │                    │
│  └───────────────────────────────────┘                    │
│  Better, but every team reinvents the wheel               │
│                                                             │
│  Platform Engineering:                                      │
│  ┌───────────────────────────────────┐                    │
│  │           Product Teams           │                    │
│  │       Focus on business value     │                    │
│  └───────────────┬───────────────────┘                    │
│                  │ uses                                    │
│  ┌───────────────▼───────────────────┐                    │
│  │         Platform Team             │                    │
│  │  Builds reusable infrastructure   │                    │
│  │      "Platform as a Product"      │                    │
│  └───────────────────────────────────┘                    │
│  Best of both: autonomy with guardrails                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Developer Portal

A single place for developers to discover, create, and manage services.

```
┌─────────────────────────────────────────────────────────────┐
│  DEVELOPER PORTAL (e.g., Backstage)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SERVICE CATALOG                                           │
│  ├── frontend-app (React, team: frontend)                 │
│  ├── api-service (Go, team: backend)                      │
│  ├── user-service (Python, team: identity)                │
│  └── payment-service (Java, team: payments)               │
│                                                             │
│  TEMPLATES                                                  │
│  ├── [Create new microservice]                            │
│  ├── [Create new database]                                │
│  └── [Create new data pipeline]                           │
│                                                             │
│  DOCS                                                       │
│  ├── Getting Started                                       │
│  ├── API Documentation                                     │
│  └── Runbooks                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Golden Paths

Pre-built, recommended ways to accomplish common tasks:

```yaml
# Instead of: "Figure out how to deploy to Kubernetes"
# Golden Path: "Use this template"

# scaffold/microservice-template/template.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: microservice-template
  title: Create a new microservice
spec:
  parameters:
    - name: serviceName
      description: Name of your service
    - name: team
      description: Your team name
    - name: language
      options: [go, python, java, node]

  steps:
    - id: create-repo
      action: github:create-repo
    - id: add-ci-cd
      action: add-github-actions
    - id: register-service
      action: backstage:register
```

### 3. Self-Service Infrastructure

```yaml
# Developer request (simplified)
apiVersion: platform.company.io/v1
kind: DatabaseRequest
metadata:
  name: my-postgres
spec:
  type: postgresql
  size: small
  team: backend

# Platform handles:
# - Provisioning
# - Backups
# - Monitoring
# - Credentials
# - Network policies
```

---

## Platform Tools

```
┌─────────────────────────────────────────────────────────────┐
│              PLATFORM TOOLING LANDSCAPE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DEVELOPER PORTALS                                          │
│  ├── Backstage (Spotify, CNCF)   - Most popular           │
│  ├── Port                         - Commercial             │
│  └── Cortex                       - Commercial             │
│                                                             │
│  KUBERNETES ABSTRACTIONS                                    │
│  ├── Crossplane       - Universal control plane            │
│  ├── Kratix           - Platform-as-a-Product framework   │
│  └── KubeVela         - Application delivery platform     │
│                                                             │
│  DEVELOPER EXPERIENCE                                       │
│  ├── Telepresence     - Local K8s development             │
│  ├── Tilt             - Smart rebuilds for K8s            │
│  ├── Skaffold         - Build/deploy automation           │
│  └── Garden           - Development pipelines             │
│                                                             │
│  SERVICE MESH (Platform networking)                        │
│  ├── Istio            - Feature-rich, complex             │
│  ├── Linkerd          - Lightweight, simple               │
│  └── Cilium           - eBPF-based                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Backstage: The Leading Platform

Backstage (from Spotify, now CNCF) is the de facto standard:

```
┌─────────────────────────────────────────────────────────────┐
│              BACKSTAGE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  BACKSTAGE CORE                      │   │
│  │                                                      │   │
│  │  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│  │  │   Software   │  │  Scaffolder │  │  TechDocs │ │   │
│  │  │   Catalog    │  │ (Templates) │  │   (Docs)  │ │   │
│  │  └──────────────┘  └─────────────┘  └───────────┘ │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │               PLUGINS                         │  │   │
│  │  │  Kubernetes • CI/CD • Cost • Security • ...  │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Key features:                                             │
│  - Service catalog (who owns what)                        │
│  - Scaffolder (create new services from templates)        │
│  - TechDocs (documentation as code)                       │
│  - 100+ plugins for integrations                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Crossplane: Infrastructure Abstraction

Crossplane lets you define infrastructure as Kubernetes resources:

```yaml
# Platform team defines a CompositeResourceDefinition
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: databases.platform.company.io
spec:
  group: platform.company.io
  names:
    kind: Database
  versions:
    - name: v1
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                size:
                  type: string
                  enum: [small, medium, large]

---
# Developer just requests:
apiVersion: platform.company.io/v1
kind: Database
metadata:
  name: my-db
spec:
  size: small

# Platform handles the complex AWS/Azure/GCP resources
```

---

## The Platform Team

```
┌─────────────────────────────────────────────────────────────┐
│              PLATFORM TEAM RESPONSIBILITIES                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BUILD                                                      │
│  ├── Internal developer platform                          │
│  ├── Golden paths and templates                           │
│  ├── Shared libraries and tooling                         │
│  └── Documentation and training                           │
│                                                             │
│  OPERATE                                                    │
│  ├── Kubernetes clusters                                  │
│  ├── CI/CD pipelines                                      │
│  ├── Observability stack                                  │
│  └── Security tooling                                     │
│                                                             │
│  ENABLE                                                     │
│  ├── Developer onboarding                                 │
│  ├── Support and troubleshooting                          │
│  ├── Gather feedback and iterate                          │
│  └── Advocate for developer experience                    │
│                                                             │
│  Mindset: "Platform as a Product"                          │
│  Developers are your customers                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Platform Maturity Model

```
┌─────────────────────────────────────────────────────────────┐
│              PLATFORM MATURITY LEVELS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 1: Ad-hoc                                           │
│  - Teams figure out infrastructure themselves             │
│  - Lots of duplication and variation                      │
│  - "Ask Dave how to deploy"                               │
│                                                             │
│  Level 2: Standardized                                      │
│  - Documented processes and templates                     │
│  - Shared tooling (same CI/CD for everyone)              │
│  - Some automation, but manual steps remain               │
│                                                             │
│  Level 3: Self-Service                                      │
│  - Developer portal with service catalog                  │
│  - Golden paths for common tasks                          │
│  - Automated provisioning                                 │
│                                                             │
│  Level 4: Optimized                                         │
│  - Continuous improvement based on metrics                │
│  - FinOps integration (cost optimization)                │
│  - AI/ML assisted operations                              │
│                                                             │
│  Most companies are between Level 1-2                      │
│  Level 3 is the goal for most                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Backstage started at Spotify** to manage 1,500+ microservices. They open-sourced it in 2020, and it's now a CNCF Incubating project used by thousands of companies.

- **Platform Engineering is the #1 trend** in Gartner's 2024 strategic technology trends. They predict 80% of software engineering organizations will have platform teams by 2026.

- **Netflix's platform** lets developers deploy hundreds of times per day across thousands of microservices, with minimal platform team involvement.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Building without user input | Platform nobody wants | Talk to developers first |
| Too much abstraction | Developers can't debug | Provide escape hatches |
| No golden paths | Every team invents their own | Define and promote best practices |
| Platform as gatekeeper | Slows everyone down | Platform enables, not blocks |
| "Build it and they will come" | Low adoption | Treat platform as product, market it |

---

## Quiz

1. **What problem does Platform Engineering solve?**
   <details>
   <summary>Answer</summary>
   Cognitive overload. Developers shouldn't need to understand all of Kubernetes, CI/CD, monitoring, etc. Platform Engineering provides self-service abstractions that hide complexity while maintaining standards.
   </details>

2. **What's a "Golden Path"?**
   <details>
   <summary>Answer</summary>
   A pre-built, recommended way to accomplish common tasks. Instead of figuring out how to deploy to Kubernetes, developers use a template that handles best practices automatically.
   </details>

3. **How is Platform Engineering different from DevOps?**
   <details>
   <summary>Answer</summary>
   DevOps said "you build it, you run it" (every team does everything). Platform Engineering creates a dedicated team that builds reusable infrastructure, so product teams can focus on business value.
   </details>

4. **What is Backstage?**
   <details>
   <summary>Answer</summary>
   An open-source developer portal from Spotify (now CNCF). It provides a service catalog, templates for creating new services, and documentation system. It's the de facto standard for internal developer platforms.
   </details>

---

## Hands-On Exercise

**Task**: Experience platform-like abstractions with Kubernetes.

```bash
# This shows how platforms abstract complexity

# 1. The "hard way" (what platforms abstract)
cat << 'EOF' > complex-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
        readinessProbe:
          httpGet:
            path: /
            port: 80
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
EOF

kubectl apply -f complex-deployment.yaml

# 2. The "platform way" (simplified interface)
# Imagine a platform where developer just says:
cat << 'EOF'
# platform-request.yaml (hypothetical)
name: myapp
image: nginx:1.25
replicas: 3
expose: true
EOF

# Platform converts this to full K8s manifests
# Developer doesn't need to know:
# - Resource limits
# - Health checks
# - Service configuration
# - Labels and selectors

# 3. See what the "simple" request created
kubectl get deployment myapp
kubectl get service myapp
kubectl get pods -l app=myapp

# 4. This is what platform teams build:
# - Simple interfaces for developers
# - Best practices baked in
# - Guardrails (limits, security, etc.)

# 5. Cleanup
kubectl delete -f complex-deployment.yaml
rm complex-deployment.yaml
```

**Success criteria**: Understand the value of abstraction.

---

## Summary

**Platform Engineering** is about building better developer experiences:

**Core idea**:
- Internal Developer Platform (IDP)
- Self-service with guardrails
- "Platform as a Product"

**Key components**:
- Developer portal (Backstage)
- Golden paths (templates)
- Self-service infrastructure

**Tools**:
- Backstage for portals
- Crossplane for infrastructure
- Kubernetes as foundation

**Why it matters**:
- Reduces cognitive load
- Improves developer productivity
- Maintains standards and security
- Enables scaling DevOps practices

**For you**: Understanding Platform Engineering helps you build better platforms OR be a more effective platform user.

---

## Next Module

[Module 6: Security Practices (DevSecOps)](module-1.6-devsecops/) - Integrating security into DevOps.
