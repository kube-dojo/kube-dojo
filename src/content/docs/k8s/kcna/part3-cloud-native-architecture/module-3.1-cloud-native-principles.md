---
revision_pending: false
title: "Module 3.1: Cloud Native Principles"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.1-cloud-native-principles
sidebar:
  order: 2
---

# Module 3.1: Cloud Native Principles

**Complexity**: `[MEDIUM]` architecture concepts. **Time to Complete**: 45-55 minutes. **Prerequisites**: Part 2, Container Orchestration, including basic familiarity with Pods, Deployments, Services, and the difference between desired state and actual state.

## What You'll Be Able to Do

After completing this module, you will be able to use the following outcomes as review criteria during architecture discussions and Kubernetes workload inspections:

1. **Evaluate** whether an application follows cloud native principles by tracing its configuration, state, logging, and failure behavior.
2. **Compare** monolithic and microservice designs, then choose service boundaries that reduce blast radius without adding needless distributed complexity.
3. **Design** a Kubernetes 1.35+ workload manifest that applies 12-factor practices with environment configuration, replicas, probes, and stdout logging.
4. **Diagnose** deployment anti-patterns such as mutable server changes, hardcoded backing services, local container state, and imperative-only operations.

## Why This Module Matters

The core reference point here is the Knight Capital 2012 <!-- incident-xref: knight-capital-2012 --> walkthrough in [the modern DevOps track's infrastructure-as-code module](../../../prerequisites/modern-devops/module-1.1-infrastructure-as-code/), which is the canonical case for why cloud-native control loops and declarative rollout state matter when fleets must remain uniform.

That story matters for Kubernetes learners because cloud native architecture is often reduced to a shallow phrase: "put it in a container." A container can package a broken operating model just as easily as it can package a resilient one. If the application still depends on local disk, hardcoded database addresses, hand-edited servers, or one giant process that fails as a unit, Kubernetes can restart it, but Kubernetes cannot magically make the design scalable, observable, or safe to change.

The KCNA exam expects you to recognize cloud native principles as a design system, not a product label. You will connect the CNCF definition, 12-factor application design, microservice tradeoffs, immutable infrastructure, declarative APIs, and failure-oriented thinking into one operational model. The goal is practical judgment: when you review a workload, you should be able to say which parts are cloud native, which parts are merely containerized, and which changes would make the application safer to run on Kubernetes 1.35+.

## What Cloud Native Really Means

Cloud native describes applications and platforms built for modern, dynamic environments where nodes change, networks fail, capacity shifts, and releases happen frequently. The important word is not "cloud"; the important word is "native." A cloud native application behaves as if movement, replacement, automation, and partial failure are normal conditions, just as a native speaker does not translate every sentence back through another language before responding.

The Cloud Native Computing Foundation definition names containers, service meshes, microservices, immutable infrastructure, and declarative APIs because those technologies support that operating model. Containers give you a repeatable runtime package, service meshes can move cross-cutting network behavior out of application code, microservices allow independent change when boundaries are well chosen, immutable infrastructure eliminates drift, and declarative APIs let a control plane reconcile desired state. None of those tools is sufficient by itself, but together they change how teams design and operate software.

```text
┌─────────────────────────────────────────────────────────────┐
│              CLOUD NATIVE DEFINITION                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CNCF Definition:                                          │
│  ─────────────────────────────────────────────────────────  │
│  "Cloud native technologies empower organizations to       │
│   build and run scalable applications in modern, dynamic  │
│   environments such as public, private, and hybrid clouds."│
│                                                             │
│  Key characteristics:                                      │
│  • Containers                                              │
│  • Service meshes                                          │
│  • Microservices                                           │
│  • Immutable infrastructure                                │
│  • Declarative APIs                                        │
│                                                             │
│  Cloud Native ≠ "Running in the cloud"                    │
│  ─────────────────────────────────────────────────────────  │
│  You can run cloud native apps on-premises                │
│  You can run non-cloud-native apps in the cloud           │
│                                                             │
│  Cloud native = designed for cloud environments           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Think of cloud native as a contract between application and platform. The application promises to be portable, externally configurable, disposable, observable through standard streams and health signals, and tolerant of replacement. The platform promises to schedule it, restart it, scale it, connect it to backing services, enforce declared policy, and keep moving actual state toward desired state.

A useful review question is: "What would happen if this Pod disappeared during a normal business hour?" If the answer is "the Deployment creates another Pod, traffic shifts away while readiness catches up, logs remain available, and durable data lives elsewhere," you are seeing cloud native behavior. If the answer is "someone must SSH to the node, recover files from local disk, and rerun a setup script from memory," the container is hiding a traditional operating model.

This distinction also explains why cloud native architecture is not automatically microservice architecture. A modular monolith that follows 12-factor practices, exposes useful health checks, writes logs to stdout, and treats its database as an attached resource may be more cloud native than a swarm of tiny services sharing one fragile database and requiring coordinated releases. The principle is to design for automation and resilience first, then split services when the split pays for itself.

The first practical skill is therefore evaluation. Before changing YAML, inspect the application contract: where does state live, how is configuration supplied, what happens during shutdown, what signal says the instance is ready, and how can an operator reproduce the running version from source and manifests? Those questions map directly to Kubernetes objects you already know: Deployments, Services, ConfigMaps, Secrets, probes, Jobs, and controllers.

A second useful skill is separating platform capability from application responsibility. Kubernetes can place Pods, restart failed containers, and update endpoints, but it cannot know whether a checkout request is safe to retry or whether a recommendation response is optional. Those choices belong to the application and product teams, and the platform works best when those choices are exposed through clear contracts such as health endpoints, timeouts, idempotent handlers, and meaningful exit behavior.

Cloud native review also benefits from thinking in replacement events instead of steady-state diagrams. Ask what happens when the image changes, when a node drains, when a Secret rotates, when one dependency slows down, and when a second region needs the same release. Designs that seem acceptable during calm traffic often reveal hidden coupling during those transitions, because replacement forces every assumption about state, identity, and configuration into the open.

## The 12-Factor App in Kubernetes

The 12-factor methodology gives cloud native architecture a vocabulary for application behavior. It came from Heroku's operational experience running large numbers of applications, but the ideas fit Kubernetes because both models assume automation, repeatability, and separation between code, configuration, runtime process, and attached services. The factors are not a checklist to memorize; they are pressure tests for whether an application can move safely through environments and recover cleanly from platform events.

The first six factors focus on packaging and runtime boundaries. One codebase can produce many deploys, dependencies must be explicit, configuration belongs outside the code, backing services should be replaceable attachments, build and run stages must be separated, and application processes should be stateless. Kubernetes reinforces these ideas by turning the container image into the build artifact while ConfigMaps, Secrets, Services, and controllers supply environment-specific runtime behavior.

```text
┌─────────────────────────────────────────────────────────────┐
│              THE 12 FACTORS                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CODEBASE                                               │
│     One codebase tracked in version control                │
│     Many deploys (dev, staging, prod)                     │
│                                                             │
│  2. DEPENDENCIES                                           │
│     Explicitly declare and isolate dependencies            │
│     Never rely on system packages                          │
│                                                             │
│  3. CONFIG                                                 │
│     Store config in the environment                        │
│     Not in code (ConfigMaps/Secrets!)                     │
│                                                             │
│  4. BACKING SERVICES                                       │
│     Treat backing services as attached resources          │
│     Database, cache, queue = URLs, not special cases      │
│                                                             │
│  5. BUILD, RELEASE, RUN                                    │
│     Strictly separate build and run stages                │
│     Build → Release (build + config) → Run                │
│                                                             │
│  6. PROCESSES                                              │
│     Execute app as stateless processes                    │
│     State lives in backing services, not memory           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The next six factors describe how a process participates in an automated platform. Port binding makes the application self-contained, concurrency favors more process instances instead of one enormous host, disposability requires fast startup and graceful shutdown, dev/prod parity reduces surprises between environments, logs flow as event streams, and administrative tasks run as one-off processes. Kubernetes gives concrete forms to those ideas through container ports, replicas, termination grace periods, shared images, container log collection, and Jobs.

```text
┌─────────────────────────────────────────────────────────────┐
│              THE 12 FACTORS (continued)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  7. PORT BINDING                                           │
│     Export services via port binding                       │
│     App is self-contained, serves HTTP                    │
│                                                             │
│  8. CONCURRENCY                                            │
│     Scale out via the process model                       │
│     Run multiple instances, not bigger instances          │
│                                                             │
│  9. DISPOSABILITY                                          │
│     Maximize robustness with fast startup/shutdown        │
│     Can be started/stopped at any moment                  │
│                                                             │
│ 10. DEV/PROD PARITY                                        │
│     Keep development, staging, production similar         │
│     Same tools, same dependencies                         │
│                                                             │
│ 11. LOGS                                                   │
│     Treat logs as event streams                           │
│     Write to stdout, let platform handle collection       │
│                                                             │
│ 12. ADMIN PROCESSES                                        │
│     Run admin/management tasks as one-off processes       │
│     Migrations, scripts as separate Jobs                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Stateless does not mean "no data exists." It means the running web or worker process does not use memory, local container files, or a specific node as the system of record; durable state belongs in backing services with explicit lifecycle and recovery contracts.

Factor 3 and Factor 4 often appear together during Kubernetes migrations. A legacy application may connect to `localhost:5432`, write uploads under `/app/uploads`, and log to `/var/log/app.log` because it was designed for one server. In Kubernetes, that design collides with Pod scheduling because localhost means the Pod itself, local files disappear with the container, and file logs are harder for cluster-level collectors to preserve.

Here is the same factor list translated into Kubernetes terms. The table is not meant to imply a one-to-one mechanical mapping for every production system, but it gives you exam-ready language for recognizing how a workload expresses cloud native behavior inside a cluster. When you evaluate a design, look for the underlying principle rather than only the object name.

| Factor | Kubernetes Implementation |
|--------|--------------------------|
| Codebase | Container images from Git |
| Dependencies | Container images bundle deps |
| Config | ConfigMaps and Secrets |
| Backing services | Services point to databases |
| Build/Release/Run | CI/CD pipelines |
| Processes | Pods are stateless |
| Port binding | Container ports |
| Concurrency | Horizontal scaling (replicas) |
| Disposability | Fast container startup |
| Dev/prod parity | Same images everywhere |
| Logs | Stdout -> log aggregation |
| Admin processes | Jobs and CronJobs |

In the command examples for this module, `kubectl` is shortened with the common shell alias `k`. Define it once in your shell, then use `k get pods`, `k apply`, and related commands in the same way you would use the full command. The alias does not change Kubernetes behavior; it only makes repeated practice less noisy.

```bash
alias k=kubectl
k version --client
```

A minimal 12-factor Deployment does not need exotic Kubernetes features. It needs a stable image, environment-driven configuration, a port, enough replicas to tolerate replacement, and probes that tell the Service when a Pod can receive traffic. That foundation is more important than adding advanced networking before the application has a clean runtime contract.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
spec:
  replicas: 3
  selector:
    matchLabels:
      app: checkout
  template:
    metadata:
      labels:
        app: checkout
    spec:
      containers:
        - name: checkout
          image: ghcr.io/example/checkout:1.8.0
          ports:
            - containerPort: 8080
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: checkout-db
                  key: url
            - name: LOG_FORMAT
              value: json
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 20
            periodSeconds: 20
```

Before running this, what output do you expect from `k get deploy checkout` after applying a manifest like this in a healthy cluster? You should expect Kubernetes to report three desired replicas and, after startup and readiness succeed, three available replicas. If the image pulls but readiness fails, the Deployment may show Pods running while the Service still keeps them out of endpoints, which is exactly the separation a cloud native workload needs.

```bash
k apply -f checkout-deployment.yaml
k get deploy checkout
k get pods -l app=checkout
k logs -l app=checkout --tail=20
```

The worked example also demonstrates why "configuration in the environment" is not the same as "all configuration is harmless." A database URL usually belongs in a Secret because it may contain credentials, while a feature flag or log format may belong in a ConfigMap or plain environment value. The principle is externalization; the security decision depends on sensitivity and access control.

War story: one platform team migrated a payments worker to Kubernetes and kept a daily migration command inside the container entrypoint because it worked on a single VM. When the Deployment scaled to three replicas, three Pods tried to run the migration at the same time, and one process held a lock long enough to delay startup for the others. The durable fix was not a bigger timeout; it was moving the administrative task into a separate Kubernetes Job so normal web processes stayed disposable and predictable.

Notice how many factors are involved in that single story. The image was reusable, but the run command mixed serving traffic with administration. The process was stateless enough to scale, but startup behavior was not disposable because it depended on a global database lock. The better Kubernetes design did not require a new programming language or a service mesh; it required matching the 12-factor process model to Kubernetes controllers with a Deployment for serving and a Job for migration.

Another migration pattern is to externalize one dependency at a time and observe the result. Moving configuration into a Secret should make environment promotion easier, while moving uploads into object storage should make Pod replacement less risky. If a change does not improve replacement, portability, observability, or failure behavior, it may still be useful, but it is not necessarily advancing the cloud native contract.

When you read KCNA scenarios, translate symptoms into factors. "The team rebuilt the image to change the database host" points to configuration. "Users lose carts during rollout" points to stateless processes and backing services. "Logs disappear after restart" points to event streams. "Three replicas all run migrations" points to administrative processes. The exam usually describes behavior before naming the principle, so practice moving from symptom to design correction.

## Monoliths, Microservices, and Service Boundaries

Microservices are one of the most visible cloud native patterns, but they are also one of the easiest to misuse. A microservice is not just a small process or a repository with a REST API. A good service boundary gives a team independent ownership of a business capability, isolates failure and scaling pressure, and reduces coordination for changes that happen frequently.

A monolith is not automatically bad. Many successful systems begin as monoliths because a single deployable unit is easier to reason about while the team is still learning the domain. The failure mode is not "one process exists"; the failure mode is that unrelated capabilities become so tightly coupled that every release, incident, and scaling decision has to involve the entire application.

```text
┌─────────────────────────────────────────────────────────────┐
│              MONOLITH vs MICROSERVICES                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MONOLITH:                                                 │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Single Application                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │   UI    │ │ Orders  │ │ Payment │ │ Shipping│  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│  │              Shared Database                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  • One deployment                                          │
│  • Changes affect everything                               │
│  • Scale entire app                                        │
│                                                             │
│  MICROSERVICES:                                            │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │   UI    │  │ Orders  │  │ Payment │  │Shipping │       │
│  │ Service │  │ Service │  │ Service │  │ Service │       │
│  │   DB    │  │   DB    │  │   DB    │  │   DB    │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│       ↑            ↑            ↑            ↑             │
│       └────────────┴─────┬──────┴────────────┘             │
│                          │                                  │
│                     API Gateway                            │
│                                                             │
│  • Independent deployments                                 │
│  • Change one service only                                 │
│  • Scale individual services                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| Characteristic | Description |
|----------------|-------------|
| **Single responsibility** | Each service does one thing well |
| **Independent deployment** | Deploy without affecting others |
| **Decentralized data** | Each service owns its data |
| **Technology agnostic** | Use best tool for each service |
| **Failure isolation** | One failure doesn't crash all |
| **Team ownership** | Small teams own services |

Use that table as a tradeoff check, not a scoring sheet. Microservices help when a capability needs independent ownership, scaling, deployment, or failure isolation; they hurt when the split adds network calls, data consistency work, tracing requirements, and coordinated releases without giving the team real independence.

Stop and think: your company runs a monolithic e-commerce app, and a bug in the payment module crashes the entire process, including the shopping cart and product catalog. How would a microservices architecture change the blast radius of this failure? The payment flow might fail or degrade, but browsing and cart operations could remain available if the services, data paths, and user experience were designed to tolerate that partial outage.

The practical boundary question is not "how many services should we have?" A better question is "which capability changes at a different pace, scales under different load, or fails with a different business consequence?" Payment, search, recommendation, and image processing often have different operational profiles. Splitting along those lines can be valuable, but splitting every controller method into its own service usually creates coordination pain without meaningful isolation.

Kubernetes supports both choices. A cloud native monolith can run as a Deployment with replicas, probes, external configuration, and centralized logs. A microservice system can run many Deployments and Services with separate rollout strategies, resource requests, network policies, and autoscaling rules. The architectural maturity comes from matching the platform shape to the application and team, not from chasing a service count.

War story: a retail engineering group split a checkout system into order, inventory, payment, coupon, and shipping services before they had tracing, versioned contracts, or local development parity. The first holiday incident was not caused by Kubernetes; it was caused by humans being unable to answer which service owned a failing discount calculation. They kept the microservices, but only after adding ownership maps, contract tests, distributed tracing, and a rule that a service boundary needed a business owner as well as a repository.

That story illustrates why service boundaries should follow change boundaries. If coupons and payments always change together, forcing them into separate services can create a distributed transaction problem without delivering independent release value. If recommendations change many times a week and checkout changes carefully under stricter controls, separating them may reduce risk. The cloud native answer depends on the economic shape of change, not on an abstract preference for smaller deployables.

There is also a data boundary hidden behind every service boundary. A service that owns data must provide an API or event stream for other services to use, and it must absorb the operational cost of schema evolution. If other services bypass that API and read tables directly, the system keeps the deployment overhead of microservices but loses their independence. This is why experienced teams treat database ownership as part of the architecture, not as an implementation detail.

For KCNA purposes, be ready to defend both choices. A monolith can be the right answer when one team needs fast iteration and the workload can still be replicated, configured externally, and observed cleanly. Microservices become the stronger answer when separate teams need separate deployment authority, a hot path needs independent scaling, or an optional feature should fail without taking down the core user journey. Cloud native judgment is the ability to explain the tradeoff.

## Immutable and Declarative Operations

Immutable infrastructure is the discipline of replacing running units instead of mutating them by hand. In a traditional server model, an operator might SSH into a machine, install a package, edit a config file, restart a daemon, and write a ticket update afterward. That can be fast during a crisis, but it also creates drift because the machine now contains history that may not exist in Git, a build artifact, or a repeatable deployment path.

Cloud native systems prefer replacement because replacement is testable and reversible. If a container image contains version 1.8.0 of your application, every Pod created from that image should start from the same filesystem contents. When you need version 1.8.1, you build a new image, update the Deployment, and let the controller replace old Pods with new Pods according to the declared rollout strategy.

```text
┌─────────────────────────────────────────────────────────────┐
│              IMMUTABLE INFRASTRUCTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MUTABLE (Traditional):                                    │
│  ─────────────────────────────────────────────────────────  │
│  Server → SSH in → Update packages → Modify config        │
│                                                             │
│  Problem: Servers diverge over time ("snowflakes")        │
│  "But it works on server A!" doesn't work on server B     │
│                                                             │
│  IMMUTABLE (Cloud Native):                                 │
│  ─────────────────────────────────────────────────────────  │
│  Need change? → Build new image → Deploy new container    │
│                → Delete old container                      │
│                                                             │
│  ┌─────────┐      ┌─────────┐                             │
│  │ v1.0    │  →   │ v1.1    │   (new container)          │
│  │ Running │      │ Running │                             │
│  └─────────┘      └─────────┘                             │
│       ↓                                                    │
│   Deleted                                                  │
│                                                             │
│  Benefits:                                                 │
│  • Reproducible deployments                               │
│  • Easy rollback (just run old version)                   │
│  • No configuration drift                                  │
│  • Better testing (same image everywhere)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A severe production risk pattern is a fleet that diverges because rollout state is not uniformly enforced. A single missed unit can leave mixed versions in the wild, and Kubernetes does not erase that risk unless the control plane defines and observes desired state consistently through Deployment controllers, replica intent, rollout status, and rollback history.

Declarative operation is the partner of immutability. Imperative commands describe steps: run this, scale that, expose this port, patch that field. Declarative configuration describes the desired end state: this Deployment should exist, it should run this image, it should have three replicas, and it should expose these labels and probes. The controller then keeps comparing actual state to desired state.

```text
┌─────────────────────────────────────────────────────────────┐
│              DECLARATIVE vs IMPERATIVE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IMPERATIVE: "How to do it"                               │
│  ─────────────────────────────────────────────────────────  │
│  kubectl run nginx --image=nginx                          │
│  kubectl scale deployment nginx --replicas=3              │
│  kubectl expose deployment nginx --port=80                │
│                                                             │
│  • Step by step commands                                   │
│  • You specify the actions                                 │
│  • No record of desired state                             │
│                                                             │
│  DECLARATIVE: "What you want"                             │
│  ─────────────────────────────────────────────────────────  │
│  apiVersion: apps/v1                                      │
│  kind: Deployment                                          │
│  spec:                                                     │
│    replicas: 3                                             │
│    template:                                               │
│      spec:                                                 │
│        containers:                                         │
│        - name: nginx                                       │
│          image: nginx                                      │
│                                                             │
│  kubectl apply -f deployment.yaml                         │
│                                                             │
│  • Describe desired state                                  │
│  • Kubernetes figures out how                             │
│  • Version controlled (GitOps!)                           │
│                                                             │
│  Cloud native = Declarative                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Imperative commands are still useful for learning, debugging, and emergency inspection. The anti-pattern is running production primarily from a sequence of commands that nobody can reproduce. If the only record of the desired state is a terminal history, another engineer cannot review the change before it happens, and the cluster cannot tell whether the current state is intentional.

The declarative model becomes powerful when it is version controlled. A pull request can show that replicas changed from two to three, an image tag changed from 1.8.0 to 1.8.1, or a readiness path changed from `/ready` to `/health/ready`. Reviewers can reason about the intended state before it reaches the cluster, and Git history becomes part of the operational audit trail.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: checkout
spec:
  selector:
    app: checkout
  ports:
    - name: http
      port: 80
      targetPort: 8080
```

```bash
k apply -f checkout-service.yaml
k describe service checkout
k rollout status deployment/checkout
```

Which approach would you choose here and why: a one-line `k scale deployment checkout --replicas=5` during a traffic surge, or a pull request that changes the Deployment manifest and lets automation apply it? In a live incident, a temporary imperative scale may be reasonable if your team records and reconciles it afterward. For durable desired capacity, the manifest should win because it prevents the next apply from silently undoing the manual change.

The cloud native lesson is not "never type a command." The lesson is that durable production intent belongs in declarative state, and one-off commands should either inspect the system or create temporary changes that are later folded back into that state. Kubernetes controllers are reconciliation engines, so your operating model should give them clear desired state to reconcile.

Rollbacks show the value of immutability and declarative state together. If a new image causes errors, the team can point the Deployment back to the previous image or use rollout history rather than repairing individual containers. The old version is not reconstructed from memory; it is an artifact that already exists. This lowers cognitive load during an incident because the recovery path is another declared state, not a series of handcrafted machine edits.

Declarative state also improves security and compliance reviews. A reviewer can inspect who changed an image, which Secret name is referenced, whether privileged settings appeared, and whether resource requests were removed. Manual changes may be fast, but they often leave the weakest evidence trail at the exact moment when the organization needs to understand what changed. Versioned manifests make production change a reviewable artifact instead of a rumor.

There are still cases where imperative commands are the right tool. You may use `k logs` to inspect a crash, `k describe pod` to see scheduling events, or `k rollout restart` as part of a documented operational procedure. The difference is intent. Inspection commands gather facts, temporary commands buy time, and declarative changes define the steady state that should survive the next reconciliation loop.

## Design for Failure Instead of Hoping for Stability

Traditional infrastructure often treats failure as an exception to be prevented. Cloud native infrastructure treats failure as a normal input to design. Nodes are drained, Pods are evicted, networks drop packets, dependencies slow down, and deployments introduce bad versions. A resilient system does not avoid every failure; it limits the blast radius, detects unhealthy instances, and recovers without requiring a human to rebuild the service by hand.

```text
┌─────────────────────────────────────────────────────────────┐
│              DESIGN FOR FAILURE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cloud native assumption:                                  │
│  ─────────────────────────────────────────────────────────  │
│  "Everything will fail. Plan for it."                     │
│                                                             │
│  Patterns:                                                 │
│                                                             │
│  1. REDUNDANCY                                             │
│     Run multiple replicas                                  │
│     If one fails, others handle traffic                   │
│                                                             │
│  2. HEALTH CHECKS                                          │
│     Liveness: "Is the container alive?"                   │
│     Readiness: "Can it receive traffic?"                  │
│     Kubernetes restarts unhealthy containers              │
│                                                             │
│  3. CIRCUIT BREAKER                                        │
│     If service B is failing, stop calling it              │
│     Fail fast, don't wait for timeouts                    │
│                                                             │
│  4. RETRY WITH BACKOFF                                     │
│     Retry failed requests                                  │
│     Wait longer between each retry                        │
│                                                             │
│  5. GRACEFUL DEGRADATION                                   │
│     If recommendation service fails                        │
│     Show generic recommendations instead of error         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Redundancy is the most visible pattern in Kubernetes. A Deployment with three replicas gives the Service more than one endpoint, so a single Pod crash does not have to become a user-visible outage. Redundancy is not free, because every replica consumes resources and may increase pressure on databases or downstream APIs, but it is often the simplest way to make disposable processes practical.

Health checks are the communication channel between application and platform. A liveness probe answers whether the container should be restarted, while a readiness probe answers whether the Pod should receive traffic. Confusing those signals causes real incidents: if a slow dependency makes readiness fail, removing the Pod from endpoints may be correct; if the same dependency makes liveness fail, Kubernetes might restart every replica and amplify the outage.

Circuit breakers, timeouts, retries, and graceful degradation handle failures beyond the Pod itself. A checkout service calling a payment gateway should not let every request wait indefinitely when the gateway is slow. A timeout bounds waiting, a circuit breaker stops repeated calls for a short interval, retry with backoff avoids hammering a recovering service, and graceful degradation gives the user a reduced but controlled experience.

Deliberate failure injection — randomly terminating production instances during business hours, the textbook case study of which lives in [the chaos engineering canonical](../../../platform/disciplines/reliability-security/chaos-engineering/module-1.1-chaos-principles/) <!-- incident-xref: netflix-chaos-monkey --> — sounds reckless until you understand the goal. The point is to force engineers to build services that survive routine loss rather than depend on perfect infrastructure. Kubernetes creates a milder version of that reality every day because scheduling, rescheduling, rolling updates, and node maintenance are ordinary parts of cluster life.

The KCNA-level skill is recognizing which layer owns which recovery behavior. Kubernetes can restart a crashed container, stop routing to an unready Pod, and create replacement replicas. Your application still needs safe startup, graceful shutdown, idempotent request handling, bounded dependency calls, and data stored somewhere durable enough for the business requirement.

Consider a recommendation service that enriches a product page. If recommendation calls fail, the page can still show product details, reviews, and a generic "popular items" list. That is graceful degradation. If the same failure prevents every product page from rendering, the architecture turned an optional feature into a hard dependency, and Kubernetes cannot infer that business priority from a manifest.

Before adding a retry policy, pause and predict what happens if every client retries immediately when a dependency starts timing out. The failing service receives more traffic exactly when it has less capacity, and the retry storm can delay recovery. Backoff and jitter exist because cloud native systems include feedback loops, and careless feedback loops can make incidents worse.

Designing for failure also means deciding what not to automate. Restarting a process is helpful when the process is stuck, but harmful when the real issue is a database outage and every restart discards useful caches. Retrying a request is helpful when the failure is transient, but harmful when the operation is not idempotent and the payment gateway might process the first attempt later. Cloud native systems are automated, but good automation encodes domain knowledge rather than blindly repeating actions.

Readiness is one of the clearest examples of that domain knowledge. A service may be alive but not ready because it is warming a cache, loading a model, waiting for a dependency, or draining before shutdown. Sending traffic to that instance too early creates user-facing errors, while restarting it through liveness may reset progress. A well-designed readiness endpoint tells Kubernetes when routing is safe without pretending that every temporary dependency issue should kill the process.

Graceful shutdown matters for the same reason. Kubernetes sends a termination signal and gives the container time to exit, but the application must stop accepting new work, finish or hand off in-flight requests, and close resources cleanly. A service that ignores shutdown can lose messages during every rollout, which makes routine replacement feel dangerous. A service that handles shutdown well turns replacement into a normal maintenance action.

Failure design should be tested before the first major incident. Delete a non-production Pod and watch whether traffic recovers. Break a dependency in a staging environment and observe whether readiness, logs, and user experience match the design. Slow a downstream call and check whether timeouts protect the caller. These exercises are small, but they build confidence that the written architecture is reflected in runtime behavior.

## Patterns & Anti-Patterns

Patterns are reusable decisions that make the cloud native contract easier to keep under pressure. They are not decorations to add after the application works; they are ways to make replacement, scaling, observation, and failure handling ordinary. The patterns below are deliberately tied to symptoms you can see in a Kubernetes review, because KCNA questions often describe behavior and ask which principle is being violated.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Externalized configuration | Values differ by environment, region, tenant, or release stage | The same image can run in dev, staging, and production with different ConfigMaps or Secrets | Keep sensitive values in Secrets and rotate them without rebuilding images |
| Stateless web or worker replicas | Requests can be handled by any healthy instance | Pods can be replaced, rescheduled, and scaled horizontally | Move sessions, uploads, and durable data to backing services |
| Declarative manifests in version control | Production state must be reviewable and reproducible | Pull requests show desired changes before controllers reconcile them | Use GitOps or CI/CD to reduce manual drift between clusters |
| Health-aware traffic routing | Startup or dependency readiness can vary between instances | Readiness keeps bad endpoints out of Services while liveness handles stuck processes | Tune probes to avoid restarting healthy but temporarily unready containers |

Anti-patterns usually appear because the old approach was convenient in a smaller environment. A local upload directory is easy on one VM, a hardcoded database URL is fast for a prototype, and SSH edits feel efficient during an outage. Cloud native architecture asks whether those conveniences still work when Pods move, teams grow, releases accelerate, and failure is expected.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Containerized snowflake | The image is identical, but operators change running containers or nodes manually | Rebuild images or update declarative config, then roll out replacements |
| Shared database for unrelated services | Teams cannot deploy independently because schema changes affect everyone | Give services explicit data ownership and communicate through APIs or events |
| Local session or upload state | Pod replacement logs users out or loses files when scheduling changes | Store sessions in Redis or another backing service and uploads in object storage |
| Liveness probe checks every dependency | A downstream outage restarts otherwise healthy Pods and expands the incident | Use readiness for dependency availability and liveness for stuck process detection |

The scaling consideration is organizational as much as technical. A team that cannot operate one service safely will not become safer by operating many services. Start with the smallest architecture that honors the cloud native contract, then split where the split reduces a real bottleneck or failure domain.

Patterns should be introduced in the order that reduces the most risk for the least complexity. Externalized configuration is often early because it makes the same image portable. Probes usually follow because they let Kubernetes route traffic based on application readiness. Separate Jobs for administrative work become important once replicas increase. A service mesh or advanced progressive delivery system should come after the team understands the simpler contracts it is trying to automate.

Anti-patterns are often defended with true but incomplete statements. A local disk is fast, but it is not durable across Pod replacement. A shared database is convenient, but it couples independent services. A manual hotfix restores service, but it creates drift if it never becomes code or configuration. The review task is not to shame those choices; it is to ask whether they still fit the operating model the team wants.

When you are unsure, describe the failure you are trying to survive. If the failure is one Pod crashing, replicas and readiness may be enough. If the failure is a whole node disappearing, local node state becomes a problem. If the failure is a downstream service slowing down, timeouts and graceful degradation matter more than extra replicas. The right pattern follows from the failure mode.

## Decision Framework

Use this framework when you evaluate whether a workload is cloud native enough for Kubernetes. Start with state, because state determines whether the platform can replace Pods freely. Then inspect configuration, rollout method, observability, health signaling, and service boundaries. If any answer depends on a person remembering manual steps, the design needs more declarative control.

| Decision Question | Cloud Native Answer | Warning Sign | Kubernetes Object or Practice |
|-------------------|--------------------|--------------|-------------------------------|
| Where does durable state live? | In a backing service with a defined lifecycle | Files under the container filesystem or node-local paths | Managed database, PersistentVolume, object storage, Redis, StatefulSet when appropriate |
| How does configuration change? | Environment-specific values come from declarative sources | Rebuild image or edit running server for every environment | ConfigMap, Secret, Helm values, Kustomize overlays |
| How is desired state recorded? | Manifests live in version control and are applied through automation | Production depends on command history or manual SSH | GitOps, CI/CD, `k apply` from reviewed YAML |
| What happens when a Pod dies? | Replacement starts, traffic avoids unready instances, data remains safe | A human must recover files or restart a specific host | Deployment replicas, readiness probes, external state |
| When should a service split? | Different ownership, scaling pressure, release cadence, or failure impact | Splitting only to look modern | Separate Deployment and Service with clear API and data ownership |
| How are logs and admin tasks handled? | Logs go to stdout, migrations run as one-off Jobs | Logs stay inside files and migrations run in every replica | Cluster logging, Job, CronJob |

You can turn the table into a practical review sequence. First, ask whether a Pod can disappear without losing business data. Second, ask whether the same image can run across environments with only configuration changes. Third, ask whether the current cluster state can be recreated from source control. Fourth, ask whether the team can observe, roll back, and degrade the service during a dependency failure.

This framework also protects you from tool-first architecture. A service mesh can add retries and traffic policy, but it cannot fix a service that is unsafe to retry. A GitOps controller can reconcile YAML, but it cannot make an undocumented manual database migration safe. Kubernetes is powerful because it automates clearly declared intent, so unclear intent remains a design problem.

For new systems, choose a modular monolith when the domain is still changing quickly and one team owns the whole product. Keep it cloud native by externalizing config, writing logs to stdout, avoiding local durable state, and using Deployments with probes. Choose microservices when team ownership, scaling pressure, or failure isolation justifies the added network, data, and operational complexity.

For existing systems, migrate risk in layers instead of trying to fix everything at once. You might first containerize the application, then externalize configuration, then move uploads to object storage, then add readiness and liveness probes, then split a high-change capability. Each layer should make the next failure easier to understand, not merely add another platform feature.

Use the framework as a conversation tool with application teams. Instead of asking whether they are "cloud native," ask where the system stores durable data, how a new environment is configured, how they know an instance is ready, and what they do when a dependency is slow. Specific questions reduce defensiveness and expose concrete next steps. They also produce better architecture decisions than a generic demand to modernize.

## Did You Know?

- **12-factor started at Heroku in 2011** - The methodology came from operators who had seen many applications fail in similar ways across deployment environments.
- **Cloud native is older than Kubernetes** - Kubernetes became a CNCF project in 2015, but the architectural ideas behind disposability, automation, and external configuration were already established.
- **Microservices are a tradeoff, not a badge** - Independent deployment can reduce blast radius, but distributed tracing, contract testing, and data ownership become mandatory engineering concerns.
- **Failure testing went mainstream in the early 2010s** - the [chaos engineering canonical](../../../platform/disciplines/reliability-security/chaos-engineering/module-1.1-chaos-principles/) <!-- incident-xref: netflix-chaos-monkey --> covers the toolkit that pushed teams to prove instance loss during business hours did not have to become a customer outage.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating "runs in cloud" as "cloud native" | The infrastructure changed, but the application still assumes one stable host and manual repair | Evaluate config, state, logs, probes, rollout, and failure behavior before calling the design cloud native |
| Starting with many microservices before boundaries are understood | Teams copy the visible shape of large platforms without the operational maturity behind it | Start with a modular monolith, then split services when ownership, scaling, or failure domains justify it |
| Storing uploads or sessions in the container filesystem | Local files are easy during development and appear to work until a Pod moves | Use object storage, Redis, a database, or a properly managed persistent data pattern |
| Hardcoding database addresses or credentials in source code | Early prototypes value speed over environment portability | Inject configuration through ConfigMaps and Secrets so the same image can run across environments |
| Using liveness probes to check every dependency | Teams want Kubernetes to restart anything involved in a failed request | Use readiness for dependency availability and reserve liveness for stuck or unrecoverable local process failures |
| Fixing production by SSH and leaving the change there | Manual edits feel faster during an incident | Convert the fix into an image or manifest change, roll it out declaratively, and remove drift |
| Running migrations inside every web replica | The startup path seems like a convenient place for setup code | Run migrations as a separate Job so web Pods remain disposable and horizontally scalable |

## Quiz

Test your judgment on these architecture scenarios before moving into the refactoring exercise.

<details><summary>Your team moved a legacy monolith into a container and deployed it on Kubernetes. The app still writes uploads to `/app/uploads`, reads a hardcoded database URL, and exposes no readiness endpoint. Is it cloud native, and what would you change first?</summary>

It is containerized, but it is not yet cloud native in the operational sense. The local upload path violates stateless process design because Pod replacement can lose data, and the hardcoded database URL violates externalized configuration and backing-service attachment. I would first move durable files to object storage or another backing service, inject the database URL through a Secret, and add readiness so Services only route to instances that can handle traffic.
</details>

<details><summary>A checkout service has three replicas, but each Pod stores user sessions in memory. During a rolling update, some users lose carts. Which principle is being violated, and how should the design change?</summary>

The workload violates the stateless process expectation behind cloud native concurrency and disposability. Kubernetes is allowed to replace Pods during a rollout, so any data that must survive replacement cannot live only in one process memory space. The session state should move to a backing service such as Redis or a database, and the application should treat any replica as able to serve the next request.
</details>

<details><summary>A startup wants ten microservices for a two-week launch because "microservices are cloud native." The team has no tracing, no contract tests, and one product squad. How would you evaluate that design?</summary>

The design is likely premature because it adds distributed-system complexity before the team has boundaries, ownership, and operations in place. A modular monolith can still be cloud native if it uses external configuration, stdout logging, replicas, probes, and durable backing services. I would split only the capabilities that already have distinct scaling pressure, release cadence, failure impact, or ownership.
</details>

<details><summary>An engineer runs `k scale deployment checkout --replicas=5` during a traffic spike, but the manifest in Git still says three replicas. What risk did the team create?</summary>

The manual scale may be reasonable as a temporary incident action, but it created drift between actual state and declared desired state. The next automated apply can return the Deployment to three replicas with no obvious link to the incident decision. The durable fix is to update the version-controlled manifest or autoscaling policy so Kubernetes reconciliation reflects reviewed intent.
</details>

<details><summary>A liveness probe calls the database, payment gateway, and recommendation service. When the payment gateway slows down, Kubernetes restarts every checkout Pod. What is wrong with this probe design?</summary>

The liveness probe is checking dependency availability instead of whether the local process is alive and recoverable through restart. Restarting healthy checkout Pods during a payment outage removes capacity and can amplify the incident. Dependency checks usually belong in readiness or application-level degradation logic, while liveness should detect a stuck process that needs replacement.
</details>

<details><summary>A team runs schema migrations from the web container entrypoint. After scaling from one replica to three, startup becomes slow and sometimes fails due to migration locks. Which 12-factor idea applies?</summary>

This violates the separation between normal application processes and administrative processes. Web replicas should start quickly and be disposable, while migrations are one-off operational tasks with their own lifecycle and failure handling. In Kubernetes, the migration should run as a Job before or during the release process, and the web Deployment should start only the serving process.
</details>

<details><summary>A product page depends on a recommendation service. When recommendations fail, the whole page returns an error even though product details are available. Which cloud native failure pattern would improve the experience?</summary>

Graceful degradation would let the page render core product details while replacing recommendations with a generic list or hiding that section. Timeouts and circuit breakers would prevent the recommendation dependency from consuming all request time and capacity. The key is deciding which capabilities are optional during partial failure and encoding that business priority in application behavior.
</details>

## Hands-On Exercise: 12-Factor Refactoring

In this exercise, you will evaluate and refactor a traditional application deployment into a cloud native Kubernetes design. You do not need a full application repository to complete the reasoning work, but the commands assume you have a Kubernetes 1.35+ cluster available and the `k` alias already defined. Treat the scenario as an architecture review before you write the final manifest.

**Scenario**: You have inherited a monolithic Node.js application. Currently, it stores user uploads in a local `/app/uploads` directory, connects to a database at `localhost:5432`, writes logs to `/var/log/app.log`, and runs a migration script during every container startup. The product manager wants three replicas before the next campaign.

### Task 1: Identify the Anti-Patterns

Review the application's current state against the 12-factor and cloud native principles, and write down the operational consequence of each violation before choosing a fix.

- [ ] Identify the violation of Factor 4, Backing Services.
- [ ] Identify the violation of Factor 6, Processes and statelessness.
- [ ] Identify the violation of Factor 11, Logs.
- [ ] Identify the administrative-process problem created by startup migrations.

<details><summary>Solution guidance</summary>

The database connection should not point to `localhost:5432` unless the database is intentionally running in the same Pod, which is not the normal web workload pattern. Uploads under `/app/uploads` are local container state and can disappear during replacement or rescheduling. Logs should go to stdout and stderr so Kubernetes and cluster logging agents can collect them. Migrations should run as a Job, not inside every web replica.
</details>

### Task 2: Design the Cloud Native Solution

Plan how to adapt the application for Kubernetes before writing YAML, because the manifest should express a design decision rather than hide an unresolved application assumption.

- [ ] Reconfigure the app to read the database connection string from an environment variable supplied by a Secret.
- [ ] Change the application to output logs to stdout instead of a file under `/var/log`.
- [ ] Migrate local file uploads to an external object storage service.
- [ ] Move schema migrations into a Kubernetes Job that runs separately from web replicas.

<details><summary>Solution guidance</summary>

The same container image should run in dev, staging, and production, with environment-specific values supplied at release time. Object storage or another durable backing service removes node affinity from uploads. A separate Job gives the migration an explicit lifecycle and avoids duplicate migration attempts when the web Deployment scales horizontally. The web process becomes disposable, which allows Kubernetes to replace Pods safely.
</details>

### Task 3: Draft the Deployment Manifest

Write a basic Kubernetes Deployment YAML that implements the serving part of your design and leaves durable state, migrations, and environment-specific values outside the web replica.

- [ ] Define a `Deployment` with 3 replicas for concurrency.
- [ ] Inject the database URL through a `Secret` reference in the `env` section.
- [ ] Ensure no local volumes are mounted for stateful user uploads.
- [ ] Add readiness and liveness probes with different purposes.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dojo-shop
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dojo-shop
  template:
    metadata:
      labels:
        app: dojo-shop
    spec:
      containers:
        - name: web
          image: ghcr.io/example/dojo-shop:2.3.0
          ports:
            - containerPort: 8080
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: dojo-shop-db
                  key: url
            - name: UPLOAD_BUCKET
              value: dojo-shop-uploads
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            periodSeconds: 20
```

<details><summary>Solution guidance</summary>

The Deployment expresses concurrency with replicas, externalizes the database URL, and avoids mounting a local path for durable uploads. The readiness probe should represent whether the app can receive traffic, while liveness should represent whether the local process is stuck and needs restart. In a real system, you would also define the Secret, Service, resource requests, and rollout strategy.
</details>

### Task 4: Add the Migration Job

Separate the administrative process from the web process so normal serving Pods remain disposable, horizontally scalable, and safe to replace during a rollout.

- [ ] Define a `Job` that uses the same image but runs a migration command.
- [ ] Inject the same database Secret into the Job.
- [ ] Keep the Job separate from the web Deployment lifecycle.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: dojo-shop-migrate
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: ghcr.io/example/dojo-shop:2.3.0
          command: ["npm", "run", "migrate"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: dojo-shop-db
                  key: url
```

<details><summary>Solution guidance</summary>

The Job makes the migration visible as an administrative task rather than hiding it inside every web Pod. This helps operators see whether the migration succeeded, retry it intentionally, and avoid lock contention from multiple replicas. The Job still uses the same image, so build and release remain connected while run behavior stays separated.
</details>

### Task 5: Verify the Review

Use inspection commands to confirm the shape of the workload and connect each observed field back to one of the cloud native principles in this module.

- [ ] Run `k get deploy dojo-shop` and confirm three desired replicas.
- [ ] Run `k describe deploy dojo-shop` and confirm Secret-based environment configuration.
- [ ] Run `k logs -l app=dojo-shop --tail=20` and confirm logs are emitted through the container stream.
- [ ] Confirm the Deployment manifest does not include a local upload volume.

<details><summary>Solution guidance</summary>

The expected result is not just a running Pod; it is a workload whose behavior matches the cloud native contract. The app should be replaceable because durable state lives outside the container, configurable because environment values come from Kubernetes objects, observable because logs flow through stdout and stderr, and safer to scale because migrations no longer run in every replica.
</details>

### Success Criteria

- [ ] The design identifies the original backing-service, statelessness, logging, and admin-process violations.
- [ ] The Deployment uses three replicas without depending on local durable state.
- [ ] Database configuration is injected from a Secret instead of hardcoded in the image.
- [ ] Logs are expected on stdout or stderr rather than in a file inside the container.
- [ ] The migration runs as a separate Job.
- [ ] You can explain why this is more cloud native than simply placing the old app in a container.

## Next Module

[Module 3.2: CNCF Ecosystem](../module-3.2-cncf-ecosystem/) - Next you will map these cloud native principles to the CNCF projects and categories that implement them in real platforms.

## Sources

- [CNCF Cloud Native Definition](https://github.com/cncf/toc/blob/main/DEFINITION.md)
- [The Twelve-Factor App](https://12factor.net/)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Kubernetes Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Kubernetes StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [CNCF Cloud Native Interactive Landscape](https://landscape.cncf.io/)
