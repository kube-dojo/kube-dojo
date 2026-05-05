---
revision_pending: false
title: "Module 4.1: CI/CD Fundamentals"
slug: k8s/kcna/part4-application-delivery/module-4.1-ci-cd
sidebar:
  order: 2
---
# Module 4.1: CI/CD Fundamentals

> **Complexity**: `[MEDIUM]` - Delivery concepts
>
> **Time to Complete**: 55-70 minutes
>
> **Prerequisites**: Part 3 (Cloud Native Architecture), basic Git workflow, and Kubernetes workload concepts for version 1.35+

## Learning Outcomes

After completing this module, you will be able to make delivery decisions instead of merely naming delivery tools:

1. **Compare** Continuous Integration, Continuous Delivery, and Continuous Deployment and choose a release control model for a service.
2. **Design** a Kubernetes CI/CD pipeline that builds, tests, packages, stores, and deploys container images.
3. **Evaluate** CI/CD tools including Jenkins, GitHub Actions, GitLab CI, Tekton, Argo CD, Flux, and Argo Workflows against team constraints.
4. **Diagnose** GitOps, registry, and deployment strategy failures by tracing credentials, image tags, rollout signals, and rollback paths.

## Why This Module Matters

Delivery discipline decides how quickly a team can turn a known fix into a safe production change. When a critical CVE is announced for a widely-used dependency, every team running that dependency is suddenly racing the same clock: identify which images contain the library, rebuild with the patched version, validate, and roll the change to production. Teams with automated pipelines, image-tag traceability, and tested rollback paths can complete that loop in hours; teams with hand-edited servers, undocumented tags, and email approval chains spend a business day arguing over which container image is actually running while attackers scan the internet for unpatched targets.

The lesson is not that CI/CD magically prevents every outage. The lesson is that delivery discipline decides how quickly a team can turn a known fix into a safe production change. If the path from commit to cluster is manual, inconsistent, or dependent on one expert, every urgent change becomes a special event. If the path is automated, observable, and reversible, the team can focus on the actual risk: whether the new version behaves correctly under production conditions. KCNA includes CI/CD because cloud native operations assume that software changes are frequent, containerized, and coordinated through declarative systems rather than copied by hand onto long-lived machines.

This module teaches CI/CD as an operating model for Kubernetes applications. You will compare Continuous Integration, Continuous Delivery, and Continuous Deployment, then design the pipeline stages that move code from Git to a container registry and finally into a cluster. You will also evaluate common tools, explain why GitOps changes the security model, and diagnose deployment-strategy failures by watching the same signals that production teams use: image tags, rollout status, health metrics, and rollback paths. The goal is practical judgment, not tool fandom.

## What CI/CD Actually Promises

Continuous Integration, Continuous Delivery, and Continuous Deployment are often compressed into one acronym, but they control different risks. Continuous Integration reduces integration risk by asking developers to merge small changes frequently and letting automation build and test each change. Continuous Delivery reduces release-preparation risk by keeping every successful change deployable, even when a person still chooses the exact production moment. Continuous Deployment removes that final human release decision and sends every passing change to production automatically, which is powerful only when tests, observability, and rollback practices are mature enough to carry that responsibility.

Read the overview from top to bottom as a movement from feedback to readiness to automatic production change. The vocabulary matters for KCNA because a scenario may describe a team that can deploy any passing build but still uses a manual approval, and that is Continuous Delivery rather than Continuous Deployment. The same scenario may describe automated production rollout after every merge, which raises the bar for test coverage, progressive exposure, and monitoring.

```text
┌─────────────────────────────────────────────────────────────┐
│              CI/CD OVERVIEW                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTINUOUS INTEGRATION (CI)                               │
│  ─────────────────────────────────────────────────────────  │
│  Frequently merge code changes into a shared repository   │
│  Automatically build and test each change                 │
│                                                             │
│  Code → Build → Test → Merge                              │
│                                                             │
│  CONTINUOUS DELIVERY (CD)                                 │
│  ─────────────────────────────────────────────────────────  │
│  Automatically prepare code for release to production     │
│  Deployment is manual (button click)                      │
│                                                             │
│  CI → Package → Stage → [Manual Deploy]                  │
│                                                             │
│  CONTINUOUS DEPLOYMENT (CD)                               │
│  ─────────────────────────────────────────────────────────  │
│  Automatically deploy every change to production         │
│  No manual intervention                                   │
│                                                             │
│  The difference:                                          │
│  • Continuous Delivery: CAN deploy at any time           │
│  • Continuous Deployment: DOES deploy automatically      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Think of CI as the smoke alarm in a workshop. It does not ship the product, but it tells you quickly when a new part no longer fits with the rest of the machine. Continuous Delivery is the packed and inspected shipping dock: the product is ready, labeled, and waiting for a deliberate release decision. Continuous Deployment is the conveyor belt connected directly to outgoing trucks. That conveyor can be excellent when quality control is strong, but it is reckless when the team still discovers most failures after customers do.

> **Pause and predict**: Continuous Delivery means code is always ready to deploy with a manual trigger, while Continuous Deployment means every passing change deploys automatically. Which model would you choose for a service that processes refunds, and which failure signals would need to be trustworthy before you removed the manual approval?

The more automated the release decision becomes, the more the pipeline must encode human judgment. A team practicing Continuous Delivery can still pause a release because a product manager knows a high-traffic event starts in two hours. A team practicing Continuous Deployment needs automated rules that detect the same class of danger, such as elevated error rates, failing synthetic checks, or a payment-success drop during canary exposure. Automation is not the absence of judgment; it is judgment turned into repeatable checks.

KCNA questions usually stay conceptual, but production reality is concrete. A change that passes unit tests can still fail because the container image was built for the wrong architecture, the registry tag points to a stale digest, the Kubernetes Deployment never became available, or the database migration was not backward compatible. CI/CD reduces these risks by making each stage explicit and auditable. When an incident occurs, the team can ask which stage should have caught the problem and improve that stage rather than blaming the person who clicked deploy.

The biggest misunderstanding is believing that CI/CD is primarily a product selection exercise. Jenkins, GitHub Actions, GitLab CI, Tekton, Argo CD, and Flux can all support delivery, but none of them fixes an unclear release policy. Before choosing a tool, decide where code is reviewed, which tests block promotion, where images are stored, how manifests are changed, who can approve production, and how rollback is performed. Tools make those decisions executable; they do not replace them.

## Designing the Pipeline From Git to Cluster

A Kubernetes CI/CD pipeline is a chain of evidence. Each stage answers a question that the next stage should not have to ask again. Source control answers what changed and who reviewed it. Build answers whether the application and container image can be produced repeatably. Test answers whether the new artifact behaves well enough to continue. Package answers whether the immutable artifact and deployable manifests are available. Deploy answers whether the cluster converged to the intended state and whether users are healthy after traffic reaches the new version.

This pipeline diagram shows that CI/CD is more than a single deploy command. Notice that the package stage sits between test and deploy. In containerized delivery, this stage is where the pipeline pushes an image to a registry and often updates a Helm chart, Kustomize overlay, or raw manifest. Kubernetes does not build application code for you. It schedules containers from images that already exist, which means the delivery pipeline must create and store those images before the cluster can run them.

```text
┌─────────────────────────────────────────────────────────────┐
│              CI/CD PIPELINE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Code                                                      │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. SOURCE                                          │   │
│  │     Developer commits code to Git                   │   │
│  │     Triggers pipeline                               │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  2. BUILD                                           │   │
│  │     Compile code, resolve dependencies             │   │
│  │     Create container image                          │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  3. TEST                                            │   │
│  │     Unit tests, integration tests                   │   │
│  │     Security scans, linting                         │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  4. PACKAGE                                         │   │
│  │     Push container image to registry               │   │
│  │     Create Helm chart/manifests                    │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  5. DEPLOY                                          │   │
│  │     Deploy to staging/production                    │   │
│  │     Run smoke tests                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│    │                                                       │
│    ▼                                                       │
│  Production                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

In the source stage, Git is not merely a file store. It is the review boundary, audit record, and trigger point for automation. A pull request can require code review, signed commits, status checks, and branch protection before a change reaches the main branch. Those controls are part of CI/CD because they decide whether automation is allowed to spend compute on a candidate change and whether the resulting artifact should be trusted. For KCNA, connect Git to desired state and auditability, especially when you later compare push-based deployment with GitOps.

The build stage should produce the same result from the same inputs. That sounds obvious, but many delivery failures come from hidden dependencies: a package manager downloads a moving latest version, a base image tag changes under the team, or the build host contains a tool that is missing from the runner. Container builds make this easier to control because the output is an image with a digest, yet the Dockerfile or build configuration must still pin important inputs and run in a clean environment. A reproducible build lets the team debug the application instead of debugging the build machine.

The test stage should be layered rather than monolithic. Unit tests catch fast logic mistakes, integration tests catch contract mistakes between components, static analysis catches risky code patterns, image scans catch known vulnerable packages, and smoke tests catch whether the service starts and answers basic requests after deployment. A pipeline that waits until the end to run every test wastes time and delays feedback. A better design runs cheap checks early, expensive checks only after the artifact is promising, and environment-dependent checks once Kubernetes has something real to run.

Before running this mentally, predict which stage should fail if a Deployment references `ghcr.io/example/api:latest` but the registry now serves a different image than yesterday. The build may have succeeded, and the tests may have passed against the original artifact, but the package and deploy path lost immutability. A strong pipeline records the image digest, updates manifests with that digest or with a unique version tag, and lets Kubernetes pull exactly the artifact that passed validation. Mutable tags are convenient for demos; they are dangerous evidence in production.

The package stage is where container registries become central. A registry stores images so Kubernetes nodes can pull them when new Pods are scheduled. Public registries work for open images and simple learning environments, while private registries support access control, vulnerability scanning, replication, retention policies, and image signing. In a real organization, the registry is often the boundary between build infrastructure and runtime infrastructure. If an image is missing, blocked by policy, or tagged incorrectly, the cluster cannot compensate; Pods will wait, fail to pull, or run the wrong version.

```text
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER REGISTRIES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Where container images are stored                        │
│                                                             │
│  CI builds image → Push to registry → K8s pulls image    │
│                                                             │
│  Public registries:                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Docker Hub (docker.io)                                │
│  • GitHub Container Registry (ghcr.io)                   │
│  • Google Container Registry (gcr.io)                    │
│  • Quay.io                                               │
│                                                             │
│  Private registries:                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Harbor (CNCF Graduated)                               │
│  • AWS ECR                                               │
│  • Azure ACR                                             │
│  • Google Artifact Registry                              │
│                                                             │
│  Harbor features:                                         │
│  • Vulnerability scanning                                 │
│  • Image signing                                          │
│  • Role-based access                                      │
│  • Replication                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Deployment into Kubernetes should verify convergence, not just submit YAML. A command or controller can create a Deployment object successfully even when the new ReplicaSet never becomes available. Image pull errors, failed readiness probes, insufficient resources, and broken configuration can all appear after the API server accepts the desired state. That is why a human operator or automated controller should watch rollout status, events, Pod readiness, and application metrics. With the common alias `alias k=kubectl`, a learner can read examples such as `k rollout status deployment/web` and `k get pods -l app=web` as Kubernetes checks rather than generic shell commands.

This diagram captures why teams invest in this structure. The benefit is not merely speed, because fast delivery of broken changes is not progress. The deeper benefit is smaller change sets, shorter feedback loops, and better recovery. DORA research popularized four metrics that summarize this tradeoff: deployment frequency, lead time for changes, change failure rate, and mean time to recovery. High-performing teams improve speed and stability together because their delivery system makes changes easier to test, observe, and reverse.

```text
┌─────────────────────────────────────────────────────────────┐
│              CI/CD BENEFITS                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WITHOUT CI/CD:                                            │
│  ─────────────────────────────────────────────────────────  │
│  • Manual builds ("works on my machine")                  │
│  • Infrequent releases (big bang)                        │
│  • Manual testing (error-prone)                          │
│  • Long feedback loops                                    │
│  • Risky deployments                                      │
│                                                             │
│  WITH CI/CD:                                              │
│  ─────────────────────────────────────────────────────────  │
│  • Automated builds (reproducible)                       │
│  • Frequent releases (small changes)                     │
│  • Automated testing (consistent)                        │
│  • Fast feedback (minutes, not days)                     │
│  • Safe deployments (rollback ready)                     │
│                                                             │
│  Key metrics:                                              │
│  ─────────────────────────────────────────────────────────  │
│  • Deployment frequency (how often)                       │
│  • Lead time (commit to production)                       │
│  • Change failure rate (% that cause issues)             │
│  • Mean time to recovery (fix production issues)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A practical pipeline design begins with the failure you most need to prevent. For a documentation site, a build check and link checker may be the main gates. For a payment API, the pipeline may require contract tests, image scans, staged database migrations, canary analysis, and a rollback runbook before full promotion. The Kubernetes part of the pipeline should always answer three questions: which image will run, which manifests describe the desired state, and what evidence proves the cluster became healthy after the change.

## Evaluating CI/CD Tools and Kubernetes-Native Delivery

CI/CD tools differ less by whether they can run shell commands and more by where their control plane lives, how they manage credentials, how they model workflows, and how well they fit the team's source-control and cluster operations. Jenkins is deeply customizable and common in long-lived enterprises, but it requires operational care because plugins, controller availability, and credential storage become part of the platform. GitHub Actions and GitLab CI live close to repository workflows, which reduces onboarding friction for teams already using those platforms. Tekton models pipelines as Kubernetes resources, making it attractive when the platform team wants delivery primitives to run inside the cluster API itself.

| Tool | Description |
|------|-------------|
| **Jenkins** | Self-hosted, highly customizable |
| **GitHub Actions** | Built into GitHub |
| **GitLab CI** | Built into GitLab |
| **CircleCI** | Cloud-native CI/CD |
| **Travis CI** | Simple CI/CD |

This tool table is intentionally short, so treat it as a starting map rather than a buying guide. A KCNA-level comparison should ask operational questions: where does the runner execute, how are secrets stored, what triggers a pipeline, how does the tool authenticate to a registry, and whether the tool should talk directly to the cluster. A startup with most code in GitHub may choose GitHub Actions for CI because pull request checks are natural there. A regulated enterprise with years of shared pipeline libraries may keep Jenkins while tightening credential boundaries. A platform engineering group may choose Tekton because Kubernetes-native tasks can be packaged and reused across tenants.

Kubernetes-native CI/CD adds a second category of tools. Tekton builds and runs pipeline tasks as Kubernetes custom resources. Argo CD and Flux continuously reconcile declared desired state from Git into clusters. Argo Workflows runs directed workflows on Kubernetes and can support CI/CD or data-processing workloads. These tools are not identical, and KCNA expects you to distinguish build automation from GitOps reconciliation. Tekton can build and test; Argo CD and Flux usually deploy desired state; Argo Workflows orchestrates broader workflow graphs.

```text
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES-NATIVE CI/CD                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TEKTON (CNCF)                                            │
│  ─────────────────────────────────────────────────────────  │
│  • CI/CD as Kubernetes resources                          │
│  • Tasks, Pipelines, PipelineRuns                        │
│  • Cloud-native, serverless                               │
│                                                             │
│  ARGO CD (CNCF Graduated)                                 │
│  ─────────────────────────────────────────────────────────  │
│  • GitOps continuous delivery                             │
│  • Declarative, Git as source of truth                   │
│  • Sync cluster state with Git                           │
│                                                             │
│  FLUX (CNCF Graduated)                                    │
│  ─────────────────────────────────────────────────────────  │
│  • GitOps continuous delivery                             │
│  • Similar to Argo CD                                     │
│  • Tight Helm integration                                │
│                                                             │
│  ARGO WORKFLOWS (CNCF)                                    │
│  ─────────────────────────────────────────────────────────  │
│  • Workflow engine for Kubernetes                        │
│  • DAG-based workflows                                    │
│  • CI/CD and data pipelines                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The tool decision should follow the delivery boundary. If your CI system builds images and directly applies manifests with cluster administrator credentials, it sits on both sides of the boundary. That may be acceptable in a small lab, but it increases blast radius in production because a compromised CI account can mutate the cluster immediately. If CI builds an image and opens a pull request against a deployment repository, while a GitOps controller inside the cluster pulls the approved desired state, the boundary is narrower. The CI system needs registry and Git permissions; the cluster-writing power stays with the in-cluster controller.

Which approach would you choose here and why: a five-person team with one cluster and simple services, or a platform group supporting dozens of teams across regulated environments? The smaller team may value a simple integrated CI platform because operational overhead matters more than perfect separation. The platform group may value GitOps controllers, policy checks, and Kubernetes-native pipeline resources because the cost of one overprivileged credential is much higher. The right answer depends on risk, scale, and who must understand the delivery path at 2 a.m.

Tool evaluation also includes failure behavior. A hosted CI runner outage should not leave production constantly mutating in strange ways. A self-hosted Jenkins controller should be backed up because its job definitions, credentials, and plugin state may be critical. A Tekton cluster should have resource quotas so one team cannot starve shared workers. An Argo CD or Flux controller should expose reconciliation health so operators can see drift, authentication failures, or invalid manifests. Mature delivery teams do not ask whether a tool can deploy; they ask how it fails and how quickly the failure becomes visible.

KCNA will not require a full vendor comparison matrix, but it can ask which tool category fits a described model. If the scenario says pipelines are Kubernetes custom resources with Tasks and PipelineRuns, think Tekton. If it says the cluster continuously syncs from Git and treats Git as the source of truth, think Argo CD or Flux. If it says a repository-hosted workflow builds images on pull requests, think GitHub Actions or GitLab CI depending on the platform. If it says a highly customized self-hosted automation server runs many legacy jobs, Jenkins is a likely match.

## GitOps and the Security Boundary

Traditional CI/CD often uses a push model: an external system builds or packages a release, then pushes changes directly to the cluster. GitOps uses a pull model: a controller running in or near the cluster watches Git and reconciles the cluster toward the desired state stored there. The difference seems small until you analyze credentials. In the push model, the CI server needs credentials that can change the cluster. In the pull model, the in-cluster controller owns the cluster permissions, and external automation usually changes Git rather than calling the Kubernetes API directly.

This GitOps diagram shows the security and audit shift. In the traditional path, Git triggers CI, and CI pushes to the cluster. In the GitOps path, Git remains the source of truth, but the cluster-side agent pulls desired state and applies it. That means a production change should appear as a Git change, with review history, commit author, diff, and rollback through normal version-control operations. It also means cluster drift can be detected because the controller compares live state with the declared state.

```text
┌─────────────────────────────────────────────────────────────┐
│              GITOPS vs TRADITIONAL CI/CD                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRADITIONAL (Push-based):                                │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Git → CI Server → Push to Cluster                        │
│                                                             │
│  ┌──────┐    ┌─────────┐    ┌─────────────┐              │
│  │ Git  │ →  │   CI    │ →  │  Cluster    │              │
│  │      │    │ Server  │    │             │              │
│  └──────┘    └─────────┘    └─────────────┘              │
│                                                             │
│  • CI needs cluster credentials                           │
│  • External system pushes changes                         │
│                                                             │
│  GITOPS (Pull-based):                                     │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Git ← Pull from Cluster                                  │
│                                                             │
│  ┌──────┐              ┌─────────────┐                    │
│  │ Git  │ ←────────── │  Cluster    │                    │
│  │      │   agent     │  (Argo CD)  │                    │
│  └──────┘   pulls     └─────────────┘                    │
│                                                             │
│  • Cluster pulls from Git                                 │
│  • No external access needed                              │
│  • Git = source of truth                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The restaurant analogy from the earlier module remains useful when it is made operational. In a push-based system, the chef also walks into the dining room and places plates directly on tables, so the kitchen needs access to every table and a mistake affects the customer immediately. In a GitOps system, the chef places approved dishes on the pass, and a waiter assigned to the dining room checks the pass and serves tables according to the order. The waiter knows table state, can refuse a mismatched order, and leaves a visible trail of what was served.

GitOps does not remove the need for CI. A common pattern is CI builds the image, runs tests, pushes the image to a registry, and then updates a deployment repository with the new image tag or digest after approval. The GitOps controller observes that Git changed and reconciles the cluster. This split is clean because CI remains responsible for artifact quality, while the GitOps controller remains responsible for cluster convergence. When a release fails, the team can ask whether the artifact was bad, the desired state was wrong, or reconciliation failed.

The pull model improves security, but it introduces new operational questions. The controller needs read access to Git, write access to the Kubernetes resources it manages, and often permission to read Helm charts, Kustomize overlays, or private registries. If the controller has cluster-wide permissions for every namespace, it can still become a powerful target. A well-designed GitOps installation scopes controllers, service accounts, projects, namespaces, and repository access so teams can deploy what they own without mutating everything else in the cluster.

GitOps also changes how operators diagnose incidents. If a developer runs `k edit deployment web` during an emergency, the live cluster may recover temporarily, but the controller can later revert the manual edit because Git still says something else. That is not a bug; it is reconciliation doing its job. The lasting fix belongs in Git unless the team intentionally suspends reconciliation for a controlled break-glass procedure. KCNA scenarios often test this mental model: desired state lives in Git, live state should converge to it, and manual drift is temporary unless committed.

GitOps is strongest when the desired state is declarative and reviewable. Kubernetes fits that model because Deployments, Services, ConfigMaps, Ingress resources, and many custom resources are API objects with desired specifications. Some delivery tasks do not fit as neatly, especially one-time database migrations, external SaaS configuration, or imperative scripts that must run exactly once. Teams often combine GitOps with separate job orchestration or migration tooling rather than pretending every release concern is only a YAML diff.

## Deployment Strategies and Rollout Evidence

Once an artifact and desired state are ready, the delivery system still has to expose users to the new version. Kubernetes Deployments default to rolling updates, which gradually replace old Pods with new Pods while respecting availability constraints. Rolling updates are simple and resource efficient, but they can mix old and new versions during the rollout. Blue-green deployment runs two full environments or workload sets and switches traffic when the new one is ready. Canary deployment sends a small portion of traffic to the new version, watches real signals, and promotes only if the canary behaves well.

This deployment-strategy diagram connects rollout mechanics to operational tradeoffs. The key decision is blast radius. Rolling updates reduce downtime but may expose an increasing share of users before the team notices a defect. Blue-green deployments make rollback very fast, but they require enough capacity to run both versions during the switch. Canary deployments provide controlled exposure and real traffic feedback, but they require routing control and metrics that can distinguish the canary from the stable version.

```text
┌─────────────────────────────────────────────────────────────┐
│              DEPLOYMENT STRATEGIES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ROLLING UPDATE (Kubernetes default)                      │
│  ─────────────────────────────────────────────────────────  │
│  Gradually replace old pods with new                      │
│                                                             │
│  [v1][v1][v1] → [v1][v1][v2] → [v1][v2][v2] → [v2][v2][v2]│
│                                                             │
│  + Zero downtime                                          │
│  + Simple                                                  │
│  - Slow rollback                                          │
│                                                             │
│  BLUE-GREEN                                               │
│  ─────────────────────────────────────────────────────────  │
│  Run both versions, switch traffic instantly              │
│                                                             │
│  [Blue v1] ← traffic     [Blue v1]                        │
│  [Green v2]         →    [Green v2] ← traffic             │
│                                                             │
│  + Instant rollback                                       │
│  + Full testing before switch                             │
│  - Double resources needed                                │
│                                                             │
│  CANARY                                                   │
│  ─────────────────────────────────────────────────────────  │
│  Route small % of traffic to new version                  │
│                                                             │
│  [v1][v1][v1] ← 90% traffic                              │
│  [v2]         ← 10% traffic (canary)                     │
│                                                             │
│  + Test with real traffic                                 │
│  + Gradual rollout                                        │
│  + Quick rollback (just remove canary)                   │
│  - More complex setup                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Rolling updates are the Kubernetes default for Deployments, so they are the baseline strategy you should understand first. The Deployment controller creates a new ReplicaSet for the new Pod template and scales old and new ReplicaSets according to `maxUnavailable` and `maxSurge`. Readiness probes matter here because Kubernetes should not count a new Pod as available until it can serve traffic. If the readiness probe is missing or too shallow, the Deployment may continue rolling out a version that starts successfully but cannot handle real requests.

Blue-green deployment is valuable when switching traffic is safer than gradually replacing Pods. Suppose a new version changes an in-memory protocol between frontend and backend, and old and new versions should not be mixed. Running blue and green separately lets the team test the green environment, then switch a Service selector, Ingress route, or load balancer target. The cost is capacity and coordination. The team must ensure both environments point at compatible data stores or have a migration plan, because instant traffic rollback cannot undo a destructive schema change.

Canary deployment is a learning strategy as much as a release strategy. It asks the production environment a limited question: does this new version behave acceptably for a small slice of real users? The answer should come from metrics such as error rate, latency, saturation, and business outcomes, not only from whether Pods are Ready. A canary that serves one percent of traffic but doubles checkout failures should stop even if every Kubernetes object is green. That is why canary automation often integrates service mesh, ingress controller, or progressive delivery tooling with observability data.

> **Stop and think**: In a canary deployment, only a small percentage of users see the new version initially. If the canary shows increased error rates, you roll back and only that slice was affected. How does this difference in blast radius change your choice for a risky payment or authentication change?

| Strategy | Downtime | Rollback | Resource Cost | Complexity |
|----------|----------|----------|---------------|------------|
| **Rolling** | None | Slow | Normal | Low |
| **Blue-Green** | None | Instant | 2x during deploy | Medium |
| **Canary** | None | Fast | Slight increase | High |
| **Recreate** | Yes | Slow | Normal | Lowest |

This strategy comparison table makes the tradeoffs visible. Recreate is rarely the first choice for user-facing systems because it stops the old version before starting the new one, but it can be acceptable for internal tools or workloads that cannot safely run two versions at once. Rolling is often enough for stateless web services with strong readiness probes and backward-compatible changes. Blue-green is attractive when rollback speed is essential and capacity is available. Canary is strongest when the team can measure user impact accurately and control traffic routing precisely.

Deployment evidence should include both Kubernetes and application signals. Kubernetes can tell you whether Pods are scheduled, images are pulled, containers started, probes passed, and a rollout completed. Application telemetry tells you whether users are succeeding, latency is acceptable, and error budgets are being consumed. A pipeline that stops at `k rollout status` can miss a version that is technically available but functionally broken. A strong pipeline treats cluster convergence as necessary but not sufficient.

In a real incident, diagnose from the outside inward. If users cannot reach the service after a deployment, check traffic routing and Service endpoints before assuming the code is broken. If Pods are not Ready, inspect readiness probes, logs, and events. If Pods are stuck in image pull errors, inspect registry credentials, image names, tags, and digests. If a GitOps controller keeps reverting a manual fix, inspect the Git desired state and reconciliation logs. This diagnostic path keeps you from changing random settings while the actual failure is still visible.

## Patterns & Anti-Patterns

Strong CI/CD patterns make risk visible early and keep the production path boring. The first pattern is artifact immutability: build an image once, identify it by digest or a unique version tag, and promote that same artifact through environments. The second pattern is separated responsibility: CI proves the artifact and updates desired state, while a deployment controller or GitOps agent reconciles Kubernetes. The third pattern is progressive exposure: release to staging, then a small production slice, then a wider audience after metrics stay healthy. These patterns scale because they create evidence that different teams can inspect without relying on memory.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Immutable image promotion | Any service where production must run the tested artifact | The digest or unique tag ties tests to the runtime image | Add retention policies so important release images are not garbage-collected too early |
| GitOps reconciliation | Teams need auditability, drift detection, and narrower cluster credentials | Git becomes the reviewed desired state and the controller owns cluster writes | Scope repositories, namespaces, and controller permissions by team or environment |
| Progressive delivery | Changes have meaningful production risk but can be observed incrementally | Canary or staged rollout limits blast radius while collecting real signals | Requires traffic shaping and metrics that identify the new version clearly |
| Rollback rehearsals | Services have revenue, compliance, or availability commitments | Teams know whether rollback is image reversal, traffic switch, or Git revert | Test rollback paths before incidents, especially when schema migrations are involved |

Anti-patterns usually start as shortcuts that worked once. The most common is letting the CI server hold broad cluster credentials because it was faster than setting up a deployment boundary. Another is using mutable tags such as `latest` in production because the team wants simple manifests. A third is treating a green pipeline as proof of user health even when there are no post-deploy metrics. These shortcuts feel efficient until the team must explain which artifact was deployed, who approved it, and why rollback is not immediate.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| CI server as cluster superuser | A compromised runner or token can mutate production directly | Use least-privilege credentials or GitOps pull-based reconciliation |
| Mutable production tags | The cluster may run a different image than the one that passed tests | Deploy immutable digests or unique version tags |
| One giant release train | Many unrelated changes fail together and diagnosis slows down | Ship smaller changes behind feature flags or staged promotion |
| No post-deploy signal | The team discovers user-facing failure after support tickets arrive | Gate promotion on rollout, error, latency, and business metrics |
| Manual hotfix outside Git | GitOps or the next deploy overwrites the emergency change | Commit the durable fix to the desired-state repository |

The important habit is to convert each anti-pattern into a specific control rather than a slogan. "Automate everything" is too vague to help a team under pressure. "Every production image must be referenced by digest, and the GitOps repository must record the digest that passed staging" is actionable. "Have rollback" is vague. "For this service, rollback means reverting the image digest in Git and watching the Argo CD application return to Healthy within the agreed recovery target" is operational.

## Decision Framework

Use this framework when a scenario asks you to choose a CI/CD model, tool category, or deployment strategy. Start by identifying the release risk, then decide where the release decision belongs, then choose the tool boundary that supports that decision. If the service is low risk and the team needs fast feedback, CI plus Continuous Delivery may be enough. If the service is high risk or regulated, keep a manual approval, require stronger evidence, and prefer a deployment model that leaves a durable audit trail. If the organization needs cluster credential separation, evaluate GitOps before letting external CI mutate production.

| Decision Point | Choose This When | Avoid This When | Evidence to Watch |
|----------------|------------------|-----------------|-------------------|
| Continuous Delivery | Humans should choose the production moment after automation proves readiness | The team wants every merge to reach users immediately and has strong automated guards | Passing pipeline, approval record, staging smoke tests |
| Continuous Deployment | Every passing change should deploy automatically with automated rollback or halt criteria | Tests and production telemetry are weak, or changes require manual business timing | Error rate, latency, saturation, rollback automation |
| Push-based CI/CD | Small team, simple cluster access, and limited compliance pressure | CI compromise would create unacceptable production access | CI credential scope, audit logs, rollout status |
| GitOps pull model | Git audit, drift detection, and cluster credential boundaries matter | Desired state is mostly imperative scripts with weak declarative control | Reconciliation health, Git history, controller permissions |
| Rolling update | Stateless service, backward-compatible change, and normal resource budget | Mixed old and new versions are unsafe | Readiness, rollout progress, service-level metrics |
| Blue-green or canary | Risky change needs fast rollback or measured exposure | Capacity or traffic control cannot support the strategy | Version-specific metrics, traffic split, rollback time |

The flow is deliberately conservative. First, ask whether the team can prove the artifact is safe enough to deploy. If not, improve CI and test evidence before arguing about deployment automation. Second, ask whether production timing requires human context. If yes, Continuous Delivery is a better label than Continuous Deployment. Third, ask whether an external system should have cluster-changing credentials. If the answer is no, GitOps is usually the safer architecture. Fourth, ask how much blast radius the change can tolerate. That answer selects rolling, blue-green, canary, or recreate more reliably than personal preference.

This framework also helps during troubleshooting. If a release failed before an image existed, investigate build and registry stages. If an image existed but the cluster never changed, investigate desired-state updates, GitOps reconciliation, or CI deployment credentials. If the cluster changed but users failed, investigate rollout strategy and application metrics. If a rollback did not work, ask whether the rollback target was the artifact, the manifest, the traffic route, or the database state. Clear boundaries make the failure smaller.

Consider a worked example for an orders API that has three replicas, a private registry, and an Argo CD application watching a production manifest repository. A developer merges a change, CI builds `orders` from the commit, runs tests, scans the image, and pushes a digest to Harbor. The pipeline then opens a pull request that changes the Deployment image reference in the GitOps repository. After review, Argo CD sees the new desired state, applies it, and the operator watches `k rollout status deployment/orders` plus version-specific error metrics before calling the release complete.

If that release fails during image pull, the decision framework points away from source code first. The cluster has not started the new application, so debugging business logic is premature. The right evidence is in Pod events, image name spelling, registry reachability, pull secret scope, admission policy, and whether the digest exists in the registry project the namespace can access. This is the kind of diagnosis that prevents a team from rebuilding an image repeatedly when the actual fault is an expired registry credential.

If the Pods become Ready but checkout errors rise, the framework points in a different direction. The registry and Kubernetes scheduler did their job, and the rollout may even look complete from the Deployment controller's perspective. The failure is now in application behavior, configuration compatibility, downstream dependency access, or data migration safety. The release system should stop promotion, preserve logs and metrics for the bad version, and choose a rollback method that matches the deployment strategy rather than blindly applying another manifest.

If Argo CD reports OutOfSync immediately after a manual emergency edit, the framework explains why the cluster appears stubborn. GitOps is asserting that the reviewed desired state in Git owns the workload. A live edit can be useful for emergency observation, but it is not durable unless the same change reaches the watched repository or reconciliation is intentionally paused. This distinction is especially important for KCNA because it separates declarative operation from ad hoc administration, even when both use the Kubernetes API.

If the team wants to improve the pipeline after the incident, it should add the missing control at the stage that failed. An image-pull failure may require a pre-deploy registry access check or better pull-secret management. A bad application response may require stronger integration tests, canary analysis, or versioned metrics. A GitOps drift surprise may require a break-glass runbook and clearer ownership of the manifest repository. CI/CD maturity grows when post-incident actions strengthen the correct boundary instead of adding vague approval steps everywhere.

The exam-level takeaway is that CI/CD reasoning is causal. You are not expected to memorize every field of every tool, but you should be able to follow evidence from commit to image to manifest to cluster to user impact. When a question describes where the evidence stops, choose the stage, tool boundary, or deployment strategy that owns that evidence. That habit is exactly what production engineers do during real releases, and it is why the conceptual KCNA material still matters after the multiple-choice exam is over.

## Did You Know?

- **Continuous Deployment requires confidence** - You need comprehensive automated testing, observability, and rollback automation before every passing change can safely reach production without a human release button.

- **GitOps was coined by Weaveworks** - The term was popularized in 2017 by Weaveworks while describing Flux-style reconciliation from Git into Kubernetes clusters.

- **Canary comes from coal mining** - Miners used canaries to detect toxic gases, and deployment canaries borrow the idea by exposing a small audience before everyone is affected.

- **DORA metrics changed release conversations** - Deployment frequency, lead time for changes, change failure rate, and mean time to recovery let teams discuss delivery performance with measurable outcomes.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating Continuous Delivery and Continuous Deployment as the same thing | Both abbreviate to CD, and both rely on automated pipelines | Ask whether production still requires a manual release decision; if yes, call it Continuous Delivery |
| Deploying mutable image tags such as `latest` | The tag is convenient during demos and early development | Promote immutable digests or unique version tags that identify the artifact that passed tests |
| Giving CI broad production cluster credentials | It is the fastest way to make an early pipeline deploy | Use least privilege, environment-scoped credentials, or a GitOps controller that pulls approved state |
| Skipping registry and image-pull checks | The application tests passed, so the team assumes Kubernetes can run the image | Verify image names, digests, pull secrets, registry policy, and `ImagePullBackOff` events before debugging code |
| Calling a rollout successful after the API accepts YAML | `k apply` returned successfully, which feels like deployment success | Watch rollout status, Pod readiness, events, and application metrics before promoting or closing the change |
| Choosing canary without version-specific telemetry | Canary sounds safer, but the team cannot tell which version produced errors | Add labels, metrics, logs, and dashboards that separate stable and canary traffic before relying on the strategy |
| Manually hotfixing live resources under GitOps | An emergency edit appears faster than opening a reviewed Git change | Commit the durable fix to Git or intentionally suspend reconciliation with a documented break-glass path |

## Quiz

<details>
<summary>Your team can build, test, and package every merge automatically, but a release manager still chooses when production deploys. Compare Continuous Integration, Continuous Delivery, and Continuous Deployment, then name the model this team is using.</summary>

The team is practicing Continuous Integration because every merge is built and tested automatically, and it is practicing Continuous Delivery because every successful change is prepared for release. It is not practicing Continuous Deployment because a human still chooses the production moment. That manual gate may be appropriate for business timing, compliance, or high-risk services. The reasoning hinges on who or what makes the final production decision, not on whether the earlier pipeline stages are automated.
</details>

<details>
<summary>A Kubernetes service fails after a release because the running Pods pulled a different image than the one tested in staging. Design the pipeline control that should prevent this artifact mismatch.</summary>

The pipeline should build the image once, record its digest or unique version tag, push it to the registry, test that exact artifact, and update deployment manifests with the same immutable reference. Kubernetes should then pull the artifact that passed validation rather than a mutable tag that may now point elsewhere. This control belongs in the package and deploy boundary because the build already produced an image, but the release lost traceability. The fix is not simply more tests; it is artifact identity.
</details>

<details>
<summary>A security auditor objects that Jenkins stores administrator credentials for the production cluster. Evaluate whether GitOps with Argo CD or Flux would reduce the risk.</summary>

GitOps can reduce the risk by moving cluster mutation from the external CI server to an in-cluster controller with scoped Kubernetes permissions. Jenkins can build images and update Git, while Argo CD or Flux pulls the approved desired state and reconciles the cluster. This creates a clearer audit trail because production changes are Git commits, and it avoids giving the CI runner broad direct access to the Kubernetes API. The controller still needs careful permission scoping, so GitOps reduces risk only when it is configured with least privilege.
</details>

<details>
<summary>Your platform team is comparing Jenkins, GitHub Actions, GitLab CI, Tekton, Argo CD, Flux, and Argo Workflows. Which two questions best separate CI tools from GitOps deployment tools?</summary>

Ask where the workflow runs and whether the tool primarily proves artifacts or reconciles desired state into the cluster. Jenkins, GitHub Actions, GitLab CI, and Tekton are commonly used to build, test, scan, and package artifacts, although Tekton models that work as Kubernetes resources. Argo CD and Flux are GitOps deployment tools because they watch declared state and apply it to clusters. Argo Workflows runs general Kubernetes workflows, so it may support delivery tasks but is not the same category as a GitOps reconciler.
</details>

<details>
<summary>A payment service change has passed tests, but the business expects elevated traffic tonight. Diagnose whether Continuous Deployment is a good fit for this release.</summary>

Continuous Deployment may be a poor fit if the team lacks automated rules that understand the traffic event and business risk. Continuous Delivery would keep the artifact ready while preserving a manual release decision, allowing the team to wait until the risk window passes or add stricter canary controls. If the team already has excellent automated tests, version-specific metrics, canary analysis, and rollback automation, Continuous Deployment could still work. The decision depends on confidence in automated evidence, not on enthusiasm for automation.
</details>

<details>
<summary>A canary release sends a small traffic slice to version two, and Kubernetes says every Pod is Ready, but checkout success drops for canary users. What should the pipeline do?</summary>

The pipeline should halt promotion and roll back or remove the canary even though Kubernetes readiness is green. Readiness proves the Pod can serve according to its probe, but it does not prove the business transaction is healthy. Canary decisions should include application and business metrics such as error rate, latency, and checkout success. This is why progressive delivery depends on telemetry that identifies the new version separately from the stable version.
</details>

<details>
<summary>An engineer fixes a production Deployment with `k edit`, but Argo CD later changes it back. Diagnose what happened and how the durable fix should be made.</summary>

Argo CD reconciled the live cluster back to the desired state recorded in Git. The manual edit changed live state only, so it created drift rather than a durable production fix. The lasting correction should be committed to the Git repository that Argo CD watches, reviewed, and then reconciled into the cluster. In a true emergency, the team may suspend reconciliation temporarily, but that should be an intentional break-glass action with follow-up in Git.
</details>

## Hands-On Exercise: Trace a Kubernetes Delivery Path

This exercise is a reasoning lab you can complete with a local Kubernetes cluster, a shared practice cluster, or a paper design if you do not have cluster access. The point is to trace evidence across the delivery path rather than memorize a single tool. You will design a small pipeline, choose where credentials belong, decide how the image is identified, and define the rollout signals that would convince you the release is healthy. If you do use a cluster, set `alias k=kubectl` first so the examples match the shorthand used throughout this track.

### Setup

Use a simple web application repository in your own sandbox, or sketch the same objects in a document. If you have a Kubernetes 1.35+ cluster available, create a namespace such as `delivery-lab` and use a harmless public image for exploration. Do not use production credentials, real customer data, or private tokens. The design should be portable enough that another learner can read it and understand which stage owns each responsibility.

### Tasks

1. Map the source, build, test, package, and deploy stages for a service that runs as a Kubernetes Deployment.
2. Decide whether the service should use Continuous Delivery or Continuous Deployment, and write the release-control reason.
3. Choose a tool boundary: direct push from CI, GitOps with Argo CD or Flux, or Kubernetes-native CI with Tekton plus a GitOps controller.
4. Specify how the image moves through the registry, including whether manifests reference a unique tag or digest.
5. Choose rolling, blue-green, or canary rollout and list the Kubernetes and application signals required before promotion.
6. Diagnose one failure path: image pull error, failed readiness, GitOps drift, or canary metric regression.

<details>
<summary>Solution guidance</summary>

A strong answer separates artifact proof from cluster reconciliation. For example, GitHub Actions or GitLab CI can run tests, build the image, scan it, push it to GHCR or Harbor, and open a pull request that updates a manifest with an immutable image reference. Argo CD or Flux can then reconcile the approved desired state into the cluster. A lower-risk internal service might stop at Continuous Delivery with a manual promotion, while a mature team with excellent telemetry might choose Continuous Deployment for a small stateless service.

For rollout strategy, match the blast radius to the risk. A routine stateless change can use a rolling update with readiness probes, `k rollout status`, logs, and service metrics. A breaking routing or protocol change may justify blue-green if capacity exists. A risky customer-facing change may justify canary if traffic routing and version-specific metrics are available. For failure diagnosis, name the boundary first: registry and pull secret for image errors, Pod events and probes for readiness failures, Git desired state for Argo CD drift, and application telemetry for canary regression.
</details>

### Success Criteria

- [ ] I can compare Continuous Integration, Continuous Delivery, and Continuous Deployment and justify one release-control model.
- [ ] I can design a Kubernetes CI/CD pipeline that builds, tests, packages, stores, and deploys a container image.
- [ ] I can evaluate Jenkins, GitHub Actions, GitLab CI, Tekton, Argo CD, Flux, and Argo Workflows by responsibility and credential boundary.
- [ ] I can explain why a registry tag or digest must connect the tested artifact to the deployed workload.
- [ ] I can choose rolling, blue-green, or canary deployment based on blast radius, rollback speed, resource cost, and telemetry.
- [ ] I can diagnose GitOps drift, image pull failure, readiness failure, or canary regression by tracing the right evidence.

## Sources

- [Kubernetes documentation: Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes documentation: Updating a Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#updating-a-deployment)
- [Kubernetes documentation: Images](https://kubernetes.io/docs/concepts/containers/images/)
- [Kubernetes documentation: Pull an Image from a Private Registry](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
- [Kubernetes documentation: kubectl rollout](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/)
- [DORA: Software delivery performance metrics](https://dora.dev/guides/dora-metrics-four-keys/)
- [Jenkins documentation](https://www.jenkins.io/doc/)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [GitLab CI/CD documentation](https://docs.gitlab.com/ci/)
- [Tekton documentation](https://tekton.dev/docs/)
- [Argo CD documentation](https://argo-cd.readthedocs.io/en/stable/)
- [Flux documentation](https://fluxcd.io/flux/)
- [Argo Workflows documentation](https://argo-workflows.readthedocs.io/en/latest/)
- [Harbor documentation](https://goharbor.io/docs/)

## Next Module

[Module 4.2: Application Packaging](../module-4.2-application-packaging/) - Helm, Kustomize, and other tools for packaging Kubernetes applications so your delivery pipeline can promote repeatable desired state instead of loose YAML.
