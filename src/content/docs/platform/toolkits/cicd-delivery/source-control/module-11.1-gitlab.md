---
revision_pending: false
title: "Module 11.1: GitLab - The Complete DevOps Platform"
slug: platform/toolkits/cicd-delivery/source-control/module-11.1-gitlab
sidebar:
  order: 2
---
## Complexity: [COMPLEX]
## Time to Complete: 50-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/) - CI/CD and security concepts
- [GitOps Discipline](/platform/disciplines/delivery-automation/gitops/) - Git-centric workflows
- Basic Docker/Kubernetes experience
- Git fundamentals (branches, merges, remotes)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy self-hosted GitLab on Kubernetes with HA configuration and integrated CI/CD runners**
- **Configure GitLab CI/CD pipelines with stages, jobs, security scanning, and container registry integration**
- **Implement GitLab's merge request workflows with approval gates, environments, and deployment tracking**
- **Evaluate the all-in-one DevOps platform tradeoffs against assembling a best-of-breed toolchain**

---

## Why This Module Matters

> **Hypothetical scenario:** An organization runs about 200 microservices. Each service lives in its own Git repository, CI lives in a Jenkins server, container images go to a separate registry, security scanning runs through yet another SaaS tool, and deployments are handled by a GitOps controller watching a distinct configuration repository. Every tool in the chain has its own authentication system, its own authorization model, its own audit trail, and its own dashboards. When something goes wrong in production — a bad deployment, a missed security check, a rollback that did not actually roll back — tracing the complete path from code commit to running container requires correlating logs and screenshots across half a dozen separate systems. The integration layer between the tools, the scripts and webhooks and token rotations that keep them talking to one another, becomes an invisible operational tax that nobody budgeted for and nobody owns.

This fragmentation is not a hypothetical edge case. It is the default outcome when a team assembles a delivery pipeline by bolting together specialized point tools, each chosen because it was best-in-class for its narrow job. The result is a toolchain that works well in each individual link but generates substantial coordination overhead at the seams.

GitLab offers a fundamentally different approach. Rather than giving you a Git host and expecting you to wire up CI, a container registry, security scanners, issue tracking, and deployment environments yourself, GitLab bundles all of these capabilities into a single application — one codebase, one authentication system, one permission model, one data store, one API surface, and one user interface. When a commit is pushed, the pipeline runs, the security scanners execute, the container image is built and pushed to the integrated registry, the merge request shows all results in one view, and the deployment is tracked against an environment that lives in the same system — all without a single webhook, integration script, or token handoff crossing a trust boundary between tools.

This integration comes with real tradeoffs. GitLab is a large, resource-intensive application. Its tight coupling means you cannot easily swap out one component for a superior alternative — you use GitLab CI or you do not, you use the GitLab container registry or you bring your own but lose the integrated MR view. The learning curve is steeper than using a simple Git forge and picking tools à la carte. Understanding these tradeoffs honestly — when the all-in-one model helps and when it hinders — is the durable engineering judgment this module teaches. The specific GitLab version, its tier structure, and its feature matrix will churn; the architectural question of integration-versus-flexibility will outlast any product.

---

## The All-in-One vs Best-of-Breed Decision

Every engineering team building a software delivery pipeline faces a fundamental architectural choice: adopt an integrated platform that covers the full lifecycle, or assemble a toolchain from specialized best-of-breed components. This decision is more durable than any particular vendor or version because it reflects an inherent tension between integration depth and selection flexibility.

An integrated platform — GitLab being the canonical example in the self-hosted space — ties source control, continuous integration, artifact storage, security scanning, project planning, and deployment tracking into a single application with a shared data model. The benefits are real and compound. A single authentication and authorization system means you define who can access what once, and every capability in the platform respects that definition. Auditability improves because every event — code push, pipeline execution, security finding, merge approval, deployment — writes to the same database and appears in the same audit log. The developer experience benefits from a single UI: a merge request shows the code diff, the pipeline status, the security scan results, the test coverage change, and the deployment preview URL all on one page, without the developer jumping between browser tabs. Operational overhead shrinks because there is no integration glue to maintain — no webhook relays between the Git host and the CI server, no token rotations for the registry plugin, no separate backup strategies for five different tools.

The costs of integration are equally real. You commit to the platform's opinion about how CI/CD should work, how the registry should be organized, and which security scanners are available. If your team strongly prefers a particular scanning engine that the platform does not support, or if your compliance requirements demand a specific artifact storage backend, you either adapt your requirements to the platform or you run the external tool alongside — reintroducing the integration tax you adopted the platform to avoid. The platform is a single application with a single upgrade cadence; when you upgrade GitLab, you upgrade CI, the registry, the wiki, and everything else simultaneously, for better (no version-skew bugs between components) and for worse (a regression in one area forces a difficult tradeoff between fixing that area and avoiding other changes).

The all-in-one model also concentrates operational risk. A misconfiguration that takes GitLab offline takes your source code, your CI/CD pipelines, your container registry, and your deployment history offline together. A best-of-breed stack might survive a Jenkins outage because developers can still push code and a manual deploy script can bridge the gap. An integrated platform demands that you invest heavily in its reliability — high availability, tested backups, and practiced disaster recovery — because the blast radius of failure is the entire delivery pipeline.

Beyond the architectural considerations, the all-in-one decision has organizational implications that compound over time. Hiring engineers who already know GitLab CI is harder than hiring engineers who know Git and are willing to learn a CI system. The platform's learning curve affects onboarding velocity. And the migration cost out of an integrated platform is always higher than migrating individual tools, because the platform spans the entire SDLC. Teams that adopt GitLab for its integration benefits should acknowledge that they are making a long-term commitment. The exit cost is not a reason to avoid the platform, but it is a reason to make the decision explicitly rather than letting it happen by accretion — one team adopts GitLab for CI, another starts using the registry because it is there, and before anyone has discussed it, the entire delivery pipeline depends on a single application whose full implications were never evaluated as a whole.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

> GitLab offers a free tier (GitLab CE, also available as SaaS Free) with core Git hosting, basic CI/CD (400 compute minutes/month on SaaS), and the container registry. Premium (paid) adds merge request approval rules, multi-approver policies, and code owner enforcement. Ultimate (top paid tier) adds DAST, fuzz testing, and portfolio management.
>
> On the SaaS side, GitLab.com hosts the platform; self-managed installations use either the Omnibus package (monolithic Linux deployment) or the cloud-native Helm chart for Kubernetes. GitHub offers comparable CI/CD via Actions (2000 free minutes/month for public repos, 500 for private on Free), and security scanning via GitHub Advanced Security (GHAS, paid add-on). Gitea and Forgejo — covered in Module 11.2 — provide lightweight self-hosted Git forges with optional Actions-based CI through Forgejo Actions (a Gitea Actions compatible runner). Their resource footprint is dramatically smaller: under 256 MB RAM for basic Git hosting, versus GitLab's minimum of roughly 4 GB.

The Rosetta below maps durable capabilities across platforms. The specific features within each cell will evolve; the capabilities themselves are the durable comparison points.

| Capability | GitLab | GitHub | Gitea / Forgejo |
|---|---|---|---|
| **Source control (SCM)** | Full Git hosting, per-project wikis, snippets | Full Git hosting, wikis, gists | Git hosting, wikis, lightweight |
| **Built-in CI/CD** | `.gitlab-ci.yml`, runners (Docker/K8s/shell), Auto DevOps, parent-child, DAG | GitHub Actions, workflow YAML, marketplace, matrix builds, reusable workflows | Forgejo Actions (compatible runner), lightweight CI; Gitea requires external runner |
| **Container registry** | Integrated per-project registry | Integrated (ghcr.io) | Built-in package registry (Forgejo), limited |
| **Security scanning** | SAST, dependency, container, secret detection, DAST (Ultimate tier) | CodeQL (free for public), GHAS (paid: SAST, secret scanning, dependency review) | Minimal built-in; external tooling recommended |
| **Issue tracking / planning** | Issues, boards, epics, roadmaps, milestones | Issues, projects (classic and v2), milestones | Issues, milestones, kanban boards, projects (Forgejo) |
| **Self-host option** | Yes — Omnibus or Helm chart (Kubernetes) | GitHub Enterprise Server (paid, VM appliance) | Native — single binary deployment, very low resource requirements |
| **Free-tier scope** | Unlimited private repos, 400 CI min/month (SaaS), 5 GB storage | Unlimited public/private repos, 2000 CI min/month (public), 500 (private), 500 MB packages | Fully open-source, self-host runtime costs only |

---

## GitLab Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GITLAB PLATFORM ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     GitLab Rails App                       │  │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────────┐  │  │
│  │  │  Git    │ Issues  │  Merge  │  CI/CD   │   Wiki      │  │  │
│  │  │  Repos  │ Boards  │Requests │ Pipelines│ Pages       │  │  │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────────┘  │  │
│  │                          │                                 │  │
│  │                          ▼                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              Sidekiq (Background Jobs)               │  │  │
│  │  │   CI jobs • Webhooks • Email • Imports • Analytics  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │                                  │
│  ┌────────────────────────────┼──────────────────────────────┐  │
│  │                            │                               │  │
│  │  ┌──────────┐    ┌────────┴────────┐    ┌──────────────┐ │  │
│  │  │PostgreSQL│    │     Redis       │    │ Gitaly       │ │  │
│  │  │(metadata)│    │ (cache, queue)  │    │(Git storage) │ │  │
│  │  └──────────┘    └─────────────────┘    └──────────────┘ │  │
│  │                                                           │  │
│  │  ┌──────────┐    ┌─────────────────┐    ┌──────────────┐ │  │
│  │  │Container │    │  Object Storage │    │  Runner      │ │  │
│  │  │ Registry │    │   (artifacts)   │    │  (CI exec)   │ │  │
│  │  └──────────┘    └─────────────────┘    └──────────────┘ │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The GitLab application is a Ruby on Rails monolith. This is not a pejorative term in context — it is an architectural description. A single process handles the web UI, the REST and GraphQL APIs, repository browsing, issue display, merge request rendering, and CI/CD pipeline configuration. Rails talks to PostgreSQL for structured metadata such as users, projects, issues, merge requests, and CI pipeline records. It talks to Redis for caching and job queuing. And it communicates with Gitaly, a separate gRPC service, for all Git repository operations. This separation is not accidental: each component has a distinct scaling profile and failure mode, and keeping them as separate services allows the operator to provision, monitor, and recover each one independently.

**Gitaly** exists because the straightforward approach of having the Rails app execute `git` commands directly on the filesystem does not scale to large installations. When Git operations run inside the Rails process, every `git clone`, `git fetch`, and `git push` consumes memory and CPU from the same Ruby process that is trying to serve web requests — a noisy-neighbor problem that degrades the user experience for everyone. Gitaly decouples Git execution from the web application: Rails sends gRPC requests to Gitaly nodes, which handle the heavy disk I/O and Git computation in isolation. For high availability, GitLab provides **Praefect**, a cluster manager that replicates Git data across multiple Gitaly nodes, distributes read requests for load balancing, and handles automatic failover when a Gitaly node becomes unhealthy.

**Sidekiq** is the background job processor. When you push code and GitLab needs to update the merge request diff, send webhook notifications, refresh project statistics, or enqueue a CI pipeline, these tasks go into Redis-backed queues and are picked up by Sidekiq worker processes. This separation is critical: the Rails web process should respond to HTTP requests quickly and never block on long-running work. Sidekiq absorbs that work and processes it asynchronously, with separate queues for different priority levels so that user-facing operations (like updating a merge request after a push) do not get stuck behind lower-priority analytics or housekeeping jobs.

For production deployments, the minimum viable topology separates each component. You need at least two Rails web pods behind a load balancer, two Sidekiq workers, a PostgreSQL database with streaming replication to a standby, Redis with Sentinel for automatic failover, Gitaly with Praefect for distributed Git storage, and object storage (S3-compatible, such as MinIO or AWS S3) for CI artifacts, uploads, LFS objects, and package registry files. The Helm chart packages all of these into a single `helm install` command. It supports deploying each component with its own resource requests, limits, pod disruption budgets, and horizontal pod autoscaling. But the underlying operational complexity of managing a distributed stateful application remains. Teams that underestimate it learn the lesson during their first production incident — a database failover that did not work as expected, a certificate that expired because nobody tracked it, or a GitLab upgrade that broke because a dependent chart was not updated first.

Upgrades deserve special attention because the Helm chart version is tightly coupled to the GitLab application version. You cannot upgrade the chart independently of the application, and skipping major versions during an upgrade (jumping from GitLab 15.x to 17.x, for instance) is unsupported. The upgrade path must follow each major version sequentially, and each step may require database migrations that can take hours on large instances. Teams running self-hosted GitLab on Kubernetes must budget regular maintenance windows — not for the application itself, which is routine, but for the underlying data migrations, chart compatibility checks, and inevitable troubleshooting when a migration step does not complete cleanly.

---

## GitLab CI/CD Pipeline Architecture

The `.gitlab-ci.yml` file at the root of a repository is the single source of truth for what happens when code is pushed. Its structure — stages, jobs, rules, needs — encodes the delivery pipeline as configuration rather than as a set of Jenkins Groovy scripts or a scattered collection of webhook targets. This declarative approach is the durable capability; the specific YAML keys and their semantics may evolve across GitLab releases, but the pattern of defining what should happen and letting the runner system figure out how and where to execute it persists.

A pipeline is organized into **stages** — named groups of jobs that run sequentially. Within a stage, jobs run in parallel. Across stages, the default behavior is sequential: all jobs in `build` must complete before any job in `test` starts. This linear model covers the majority of delivery pipelines, but GitLab provides two mechanisms for more complex dependency graphs.

The first is the **needs** keyword. A job can declare that it depends on specific earlier jobs rather than on the entire previous stage. This enables a directed acyclic graph (DAG) where, for example, the `deploy-production` job depends on `deploy-staging` and `security-gate` but does not wait for the entire `test` matrix to complete. The DAG approach shrinks pipeline cycle time by letting independent jobs run concurrently and dependent jobs start as soon as their specific prerequisites finish. The tradeoff is that a DAG is harder to reason about than a linear pipeline — when a failure occurs, tracing which jobs were skipped and which dependencies were satisfied requires more careful inspection than reading a flat stage log.

The second is **parent-child pipelines**. A parent pipeline triggers sub-pipelines defined in separate YAML files, each with its own stages and jobs. A monorepo with independent services can use this pattern so that a change to `services/api/` triggers only the API pipeline, while a change to `services/web/` triggers only the web pipeline. This avoids a single monolithic pipeline that rebuilds and retests everything on every push, at the cost of increased pipeline configuration complexity — each child pipeline is a separate file that must be maintained, reviewed, and kept in sync with its service's actual build requirements.

GitLab CI includes a template system — both project-level templates (reusable job definitions that other jobs extend) and instance-wide templates maintained by GitLab (the `Security/SAST.gitlab-ci.yml` include that pulls in a maintained security scanning configuration). The template system reduces repetition: define a `.docker_build` template once with the image, services, and login command, and every job that extends it inherits those settings. Templates compose with rules, which control when a job runs — only on merge requests, only on the default branch, only when certain files change, or only when a specific variable is set. Rules replace the older `only`/`except` syntax and provide finer-grained control over pipeline behavior.

A critical operational concern is **cache and artifact management**. Caches store dependencies (Python packages, Node modules, Go module cache) between pipeline runs to avoid re-downloading them on every push. Artifacts store job outputs (test reports, coverage data, build outputs) that downstream jobs consume. The distinction matters: caches are best-effort and may be evicted; artifacts are guaranteed to be available for the duration configured. Without explicit artifact expiration policies, pipeline storage grows without bound — a mistake that shows up as a surprise storage bill or a disk-full alert on the object storage bucket months after the pipeline was first configured.

---

## GitLab Runners

Runners are the execution agents that pick up CI jobs and run them. GitLab itself does not execute CI jobs — it schedules them and waits for runners to report results. This separation is architecturally important: the GitLab application can scale independently of CI execution capacity, and runners can be deployed wherever the work needs to happen (on Kubernetes, on bare-metal machines with GPUs, in air-gapped environments, or across multiple cloud regions).

The runner fleet is the "muscle" of the CI system. When CI feels slow, the problem is rarely in GitLab's scheduling logic. It is almost always in the runner layer — insufficient capacity, slow image pulls, or jobs queued behind long-running tasks. Monitoring runner throughput, queue depth, and job pickup latency gives early warning before developers start complaining. A common failure mode is "runner creep": each team adds its own runner with its own configuration, and over time the fleet becomes heterogeneous in ways no single person understands. Centralized runner management with tagged capabilities and shared autoscaling pools prevents this drift before it becomes a debugging nightmare.

Each runner registers with a GitLab instance and declares an **executor** type that determines how jobs are isolated and executed. The Docker executor runs each job in a fresh container, providing strong isolation but requiring that the runner host have a Docker daemon. The Kubernetes executor creates a pod per job, which is the natural choice when the runner itself runs on Kubernetes — it integrates with the cluster's scheduling, resource limits, and pod security policies. The shell executor runs jobs directly on the runner host, which is fast and avoids container overhead but provides no isolation between jobs — a job that modifies system files or exhausts disk space affects every other job on that runner. The choice of executor trades off isolation strength against startup latency and infrastructure complexity.

Runners can be tagged with labels that describe their capabilities (`gpu`, `large-disk`, `production-cluster`, `darwin`), and jobs can require specific tags so that a job needing a macOS build environment is not picked up by a Linux runner. This tagging system becomes essential as the runner fleet grows: without it, jobs land on random runners and fail intermittently with environment mismatches that are difficult to diagnose because they depend on which runner happened to be available at scheduling time.

For Kubernetes deployments, the GitLab Runner Helm chart deploys a manager pod that watches for pending CI jobs and creates executor pods in response. Autoscaling works through the cluster's own mechanisms — the runner can be configured with resource requests that trigger the cluster autoscaler when CI demand spikes. This model avoids maintaining a pool of always-on runner VMs, but it comes with cold-start latency: a pod has to be scheduled, pull its image, and start before the job can begin executing. For latency-sensitive pipelines, keeping a baseline of warm runners (minimum replica count above zero) trades resource cost for faster job pickup.

---

## Merge Requests and Delivery Governance

The merge request is GitLab's central abstraction for change control. It is not merely a pull request with a different name — it is the integration point where code review, CI/CD results, security scan findings, deployment previews, and approval decisions all converge into a single view. This convergence is where the all-in-one platform model shows its strongest advantage. A reviewer does not need to check Jenkins for CI status, Snyk for vulnerability findings, and a separate deployment dashboard for the review app URL. Everything appears in the merge request widget at the bottom of the MR page.

This unified view has a second-order benefit that is easy to overlook. When every check lives in its own system, engineers develop coping strategies: they learn which checks are "always green so ignore," which scanners "always flag false positives so dismiss," and which deployment previews "are always stale so skip." These heuristics are individually reasonable but collectively corrosive — they train the team to ignore automated signals. When all results converge in one view, with consistent presentation and severity labels, the signal-to-noise ratio improves not because there is less noise but because the noise is contextualized. A critical vulnerability finding next to a green test suite and a successful build tells a different story than the same finding in isolation in a dedicated security dashboard that nobody visits voluntarily.

**Approval rules** encode organizational policy into machine-enforced gates. A rule might require two approvals from the `backend-maintainers` group before merging, or one approval from `security-team` when the changed files touch the `auth/` or `crypto/` directories. **Code owners**, defined in a `.gitlab/CODEOWNERS` file (or `docs/CODEOWNERS` at the repository root), map file patterns to required approvers — the `*.tf` pattern mapped to `@platform-team` means no merge request changing Terraform configuration can land without platform team approval, regardless of who authored the change. These rules are not advisory; they block the merge button until satisfied.

**Environments and review apps** close the loop between code change and deployable artifact. When a pipeline deploys to an environment (declared with the `environment` key in `.gitlab-ci.yml`), GitLab records which commit is deployed where, provides a link to the running application, and maintains a deployment history timeline. Review apps take this further: each merge request gets its own ephemeral deployment, with a URL derived from the branch name, that exists only while the MR is open. A reviewer can click the "View app" button in the MR and interact with the actual running application — the changed code, in a real environment, with real dependencies — rather than evaluating a static diff or a set of test reports. When the MR is merged or closed, the review app environment is automatically stopped, and after a configurable delay, its resources are cleaned up.

**Protected branches and protected environments** provide defense in depth. A protected branch prevents force-pushes and requires specific roles to push or merge. A protected environment requires approval before any deployment targets it — separate from the MR approval, and scoped to the deployment operation itself, so that even a merged MR cannot automatically deploy to production without an explicit deployer action. This decoupling of merge approval from deploy approval recognizes that "this code is correct" and "now is the right time to deploy it" are different judgments that should be made by different actors at different moments.

---

## Integrated Registry, Packages, and Security

GitLab's container registry is built into every project — no separate service, no additional authentication configuration, no token rotation scripts. When a CI job runs, the variables `$CI_REGISTRY`, `$CI_REGISTRY_USER`, and `$CI_REGISTRY_PASSWORD` are automatically injected, giving the job push/pull access to the project's registry namespace. This integration eliminates a whole category of operational errors: expired credentials, misconfigured registry URLs, and permission mismatches between the CI system and the artifact store are simply not possible because there is no boundary between them.

The **package registry** extends this integration beyond containers. GitLab can host npm, Maven, PyPI, NuGet, Conan, and generic packages under the same project structure, with the same CI variable injection pattern. A Python project that publishes its wheel to the GitLab PyPI registry does not need to manage a separate PyPI server or API token — it uses `$CI_JOB_TOKEN` as the password and the project's registry URL as the index.

**Security scanning** is the third pillar of the integrated model. Rather than running a standalone scanner and uploading results to a separate dashboard, GitLab includes scanner templates that execute as CI jobs, produce standardized JSON reports, and feed findings directly into the merge request view and the project's security dashboard. The scanners include:

- **SAST (Static Application Security Testing)**: Analyzes source code without executing it, detecting patterns known to lead to vulnerabilities — SQL injection, cross-site scripting, hardcoded credentials, path traversal. Language-specific analyzers understand the semantics of Python, JavaScript, Go, Java, and others.
- **Dependency Scanning**: Cross-references declared dependencies against vulnerability databases (CVEs) to identify libraries with known security issues. Covers npm, pip, Maven, Bundler, Go modules, and others.
- **Secret Detection**: Scans the entire repository history and all branches for patterns that match API keys, tokens, private keys, and credentials. Runs both as a CI job and as a pre-receive hook option that can block a push before it lands on the server.
- **Container Scanning**: Runs Trivy against built container images to identify CVEs in OS packages and application dependencies inside the image.
- **DAST (Dynamic Application Security Testing)** and **API Fuzzing** (Ultimate tier): Test the running application by sending malformed requests and analyzing responses, catching vulnerabilities that only manifest at runtime.

The durable idea is not which specific scanner runs or which vulnerability database it queries. The durable idea is that security scanning moves left into the merge request — vulnerabilities are surfaced at review time, when the code is still in flight, rather than discovered weeks later by a periodic scan that produces a ticket no one prioritizes. The MR widget shows a security finding with a severity label and a "Create issue" button; blocking the merge on critical vulnerabilities turns security from an audit function into an engineering gate.

---

## Self-Hosted GitLab on Kubernetes

Running GitLab on Kubernetes is the standard path for organizations that want the platform's integration benefits while retaining full control over data residency, network topology, and infrastructure costs. The GitLab Helm chart packages the entire architecture — Rails, Sidekiq, Gitaly, the container registry, optional built-in PostgreSQL/Redis/MinIO, and the GitLab Runner — into a single Helm release.

The installation is not trivial. A minimal deployment requires roughly 4 GB of RAM and 2 CPU cores just for the application layer, plus storage for PostgreSQL (metadata), Gitaly (Git repositories), and object storage (artifacts, uploads, LFS). A production-grade deployment with high availability pushes resource requirements higher: multiple Rails and Sidekiq replicas, a PostgreSQL cluster with Patroni for automatic failover, Redis Sentinel, Praefect-managed Gitaly with at least three nodes, and dedicated object storage (not the bundled MinIO — it is intended for evaluation only).

```bash
# Add GitLab Helm repository
helm repo add gitlab https://charts.gitlab.io/
helm repo update

# Create values file
cat > gitlab-values.yaml << 'EOF'
global:
  hosts:
    domain: example.com
    gitlab:
      name: gitlab.example.com
    registry:
      name: registry.example.com

  ingress:
    class: nginx
    configureCertmanager: true

  # External PostgreSQL (recommended for production)
  psql:
    host: postgres.example.com
    port: 5432
    database: gitlabhq_production
    username: gitlab
    password:
      secret: gitlab-postgres-secret
      key: password

  # External Redis (recommended for production)
  redis:
    host: redis.example.com
    password:
      secret: gitlab-redis-secret
      key: password

  # Object storage for artifacts, uploads, etc.
  minio:
    enabled: false
  appConfig:
    object_store:
      enabled: true
      connection:
        secret: gitlab-object-storage
        key: connection
    artifacts:
      bucket: gitlab-artifacts
    uploads:
      bucket: gitlab-uploads
    packages:
      bucket: gitlab-packages
    lfs:
      bucket: gitlab-lfs

# GitLab Rails application
gitlab:
  webservice:
    replicas: 2
    resources:
      requests:
        memory: 2.5Gi
        cpu: 1
      limits:
        memory: 4Gi
        cpu: 2

  sidekiq:
    replicas: 2
    resources:
      requests:
        memory: 2Gi
        cpu: 500m

  gitaly:
    persistence:
      size: 100Gi
      storageClass: fast-ssd

# GitLab Runner
gitlab-runner:
  install: true
  runners:
    config: |
      [[runners]]
        [runners.kubernetes]
          namespace = "gitlab"
          image = "ubuntu:22.04"
          privileged = true
          [[runners.kubernetes.volumes.empty_dir]]
            name = "docker-certs"
            mount_path = "/certs/client"
            medium = "Memory"

# Container Registry
registry:
  enabled: true
  storage:
    secret: gitlab-registry-storage
    key: config

# Disable built-in dependencies for production
postgresql:
  install: false
redis:
  install: false
minio:
  install: false

# Prometheus monitoring
prometheus:
  install: false  # Use existing Prometheus
EOF

# Install GitLab
helm upgrade --install gitlab gitlab/gitlab \
  --namespace gitlab \
  --create-namespace \
  --values gitlab-values.yaml \
  --timeout 600s
```

The self-host-vs-SaaS tradeoff is the durable decision beneath this configuration surface. SaaS (GitLab.com) eliminates infrastructure operations entirely — no Helm charts, no database backups, no certificate rotations, no Kubernetes upgrades — at the cost of data residency control, network dependency, and per-user pricing that can exceed the infrastructure cost of self-hosting at large scale. Self-hosted on Kubernetes provides data sovereignty and marginal-cost economics at scale, but it adds ongoing operational burden: PostgreSQL maintenance, Redis failover testing, Gitaly storage expansion, Helm chart upgrades (which are version-locked and can span multiple major GitLab releases), and Kubernetes cluster management. The right answer depends on the organization's operational maturity, compliance requirements, and team size — there is no universal default.

For the GitLab Runner on Kubernetes, the executor creates a pod per CI job with configurable resource limits, service accounts for RBAC, and volume mounts for caching:

```yaml
# runner-values.yaml
gitlabUrl: https://gitlab.example.com
runnerRegistrationToken: "YOUR_REGISTRATION_TOKEN"

runners:
  config: |
    [[runners]]
      name = "kubernetes-runner"
      executor = "kubernetes"
      [runners.kubernetes]
        namespace = "gitlab-runners"
        image = "alpine:latest"
        privileged = false

        # Resource limits per job
        cpu_limit = "2"
        memory_limit = "4Gi"
        cpu_request = "500m"
        memory_request = "1Gi"

        # Service account for RBAC
        service_account = "gitlab-runner"

        # Cache configuration
        [[runners.kubernetes.volumes.pvc]]
          name = "cache"
          mount_path = "/cache"

rbac:
  create: true
  rules:
    - apiGroups: [""]
      resources: ["pods", "pods/exec", "secrets"]
      verbs: ["get", "list", "watch", "create", "delete"]

replicas: 2
```

---

## Pipeline Worked Example

The `.gitlab-ci.yml` below demonstrates a production-grade pipeline that exercises the concepts covered so far: stages, jobs, templates, rules, caching, artifacts, security scanner includes, environments, and manual deployment gates. The `bitnami/kubectl:latest` image used in earlier versions of this module has been moved to the `bitnamilegacy` namespace; deployments should use a maintained replacement such as the `alpine/k8s` image or a purpose-built image with the kubectl version matched to the target cluster.

```yaml
# .gitlab-ci.yml - Production-grade pipeline
stages:
  - validate
  - build
  - test
  - security
  - deploy

variables:
  DOCKER_TLS_CERTDIR: "/certs"
  # Cache configuration
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

# Default settings for all jobs
default:
  image: python:3.11-slim
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure
  interruptible: true  # Cancel on new commits

# Reusable job templates
.docker_build:
  image: docker:27.0
  services:
    - docker:27.0-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# ─────────────────────────────────────────────────────────────
# VALIDATE STAGE
# ─────────────────────────────────────────────────────────────
lint:
  stage: validate
  script:
    - pip install ruff
    - ruff check .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

yaml-lint:
  stage: validate
  image: cytopia/yamllint
  script:
    - yamllint -c .yamllint.yml .
  allow_failure: true

# ─────────────────────────────────────────────────────────────
# BUILD STAGE
# ─────────────────────────────────────────────────────────────
build-image:
  extends: .docker_build
  stage: build
  script:
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:latest
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
        --tag $CI_REGISTRY_IMAGE:latest
        --build-arg BUILDKIT_INLINE_CACHE=1
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      variables:
        PUSH_LATEST: "false"

# ─────────────────────────────────────────────────────────────
# TEST STAGE
# ─────────────────────────────────────────────────────────────
unit-tests:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/unit --cov=src --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
      junit: junit.xml

integration-tests:
  stage: test
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
    DATABASE_URL: "postgresql://test:***@postgres:5432/test"
    REDIS_URL: "redis://redis:6379"
  script:
    - pip install -r requirements.txt
    - pytest tests/integration
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# ─────────────────────────────────────────────────────────────
# SECURITY STAGE
# ─────────────────────────────────────────────────────────────
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/Container-Scanning.gitlab-ci.yml

# Override container scanning to use our image
container_scanning:
  variables:
    CS_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# Custom security gate
security-gate:
  stage: security
  image: alpine
  needs:
    - sast
    - dependency_scanning
    - secret_detection
    - container_scanning
  script:
    - |
      echo "Checking security scan results..."
      if [ -f gl-sast-report.json ]; then
        CRITICAL=$(cat gl-sast-report.json | jq '[.vulnerabilities[] | select(.severity=="Critical")] | length')
        if [ "$CRITICAL" -gt 0 ]; then
          echo "Found $CRITICAL critical vulnerabilities!"
          exit 1
        fi
      fi
  allow_failure: false

# ─────────────────────────────────────────────────────────────
# DEPLOY STAGE
# ─────────────────────────────────────────────────────────────
deploy-staging:
  stage: deploy
  image: alpine/k8s:1.35.0
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-production:
  stage: deploy
  image: alpine/k8s:1.35.0
  environment:
    name: production
    url: https://app.example.com
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual  # Require manual approval
  needs:
    - deploy-staging
    - security-gate
```

The pipeline uses `alpine/k8s:1.35.0` as the deployment image — a lightweight Alpine-based image with kubectl installed at a version matching the target Kubernetes cluster (1.35, the current standard for KubeDojo curriculum content). Earlier versions of this pipeline used `bitnami/kubectl:latest`, which was moved to the `bitnamilegacy` namespace in 2025. The `alpine/k8s` image provides the same `kubectl` binary in a maintained, regularly updated container that aligns with the Kubernetes release cadence.

---

## GitLab Security Scanning

```
┌─────────────────────────────────────────────────────────────────┐
│                 GITLAB SECURITY SCANNING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STATIC ANALYSIS (Before Runtime)                               │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                                                            ││
│  │  SAST              │ Dependency      │ Secret Detection   ││
│  │  ───────────────   │ Scanning        │ ─────────────────  ││
│  │  Source code       │ ──────────────  │ API keys, tokens   ││
│  │  vulnerabilities   │ CVEs in deps    │ passwords in code  ││
│  │  (SQL injection,   │ (npm, pip,      │ (prevents commits) ││
│  │  XSS, etc.)        │ maven, etc.)    │                    ││
│  │                    │                 │                    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  CONTAINER & INFRASTRUCTURE                                     │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                                                            ││
│  │  Container         │ IaC Scanning    │ License Scanning   ││
│  │  Scanning          │ ──────────────  │ ────────────────   ││
│  │  ──────────────    │ Terraform,      │ Compliance with    ││
│  │  CVEs in images    │ CloudFormation  │ license policies   ││
│  │  (Trivy-based)     │ misconfigs      │ (GPL, MIT, etc.)   ││
│  │                    │                 │                    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  DYNAMIC ANALYSIS (Runtime)                                     │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                                                            ││
│  │  DAST              │ API Fuzzing     │ Coverage Fuzzing   ││
│  │  ───────────────   │ ──────────────  │ ────────────────   ││
│  │  Tests running     │ Malformed API   │ Random input to    ││
│  │  application       │ requests        │ discover crashes   ││
│  │  (OWASP ZAP)       │                 │                    ││
│  │                    │                 │                    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The security scanning pipeline integration is configured with includes that pull maintained scanner templates. Each scanner runs as a separate CI job and produces a standardized JSON artifact that feeds the security dashboard and the merge request widget. The `security-gate` job shown earlier consumes these artifacts and enforces policy — blocking the pipeline when critical vulnerabilities are detected — without requiring a separate security tool to be queried or polled. The scanner templates themselves are maintained by GitLab, so scanner updates (new CVE databases, new language support, new detection rules) arrive automatically when the pipeline references the template include.

---

## Patterns and Anti-Patterns

### Patterns (do these)

**Start with the Helm chart for self-hosted deployments.** The cloud-native Helm chart is the supported, documented path for running GitLab on Kubernetes. Resist the urge to assemble GitLab from individual manifests — the chart encodes years of operational knowledge about component interactions, health checks, upgrade ordering, and secret management. Forking or rebuilding this configuration is almost always more expensive than starting from the chart and overriding only the values you need to change.

**Structure pipelines as parent-child when you have a monorepo with independent services.** A single monolithic `.gitlab-ci.yml` for a repository containing ten services forces every push to rebuild and retest all ten, regardless of what changed. Parent-child pipelines let each service define its own pipeline file, with the parent pipeline using `rules:changes` to trigger only the child pipelines whose paths were modified.

**Use DAG (`needs`) to shrink pipeline cycle time when correctness allows it.** A deployment job should not wait for the entire test matrix to complete if it only depends on the build and security gate jobs. Declare explicit `needs` relationships to let independent jobs run concurrently and let dependent jobs start as soon as their specific prerequisites finish.

**Define artifact expiration policies from day one.** CI artifacts are stored forever by default, and a pipeline that generates 50 MB of test reports per run will consume 5 GB of storage per 100 pipeline runs. Set `expire_in` on every job that produces artifacts, and configure instance-level cleanup policies for the `packages` and `container_registry` namespaces. Storage growth is silent until it is expensive.

**Tag runners by capability and require tags on jobs that need them.** Runners with GPUs, macOS runners, runners with access to specific VPCs — without tags, these specialized runners pick up generic jobs and waste expensive resources, while specialized jobs land on generic runners and fail. Every runner gets a tag set describing what it provides; every job that needs something special declares a matching tag requirement.

### Anti-Patterns (avoid these)

**Treating GitLab CI as Jenkins-in-YAML.** Porting Jenkins Groovy pipelines line-for-line into `.gitlab-ci.yml` produces brittle, hard-to-maintain YAML that fights against GitLab's declarative model. Jenkins scripts are imperative — do this, then that, then check this, then do that. GitLab CI is declarative — define jobs, their dependencies, and their conditions; let the runner engine handle execution ordering. A clean rewrite that respects the model produces a pipeline that is shorter, more readable, and easier to debug than a literal translation.

**Running a single Gitaly node in production.** Gitaly stores every Git repository on disk. A single-node Gitaly is a single point of failure for the entire platform: if that disk fails or the node becomes unreachable, all source code is unavailable, all CI pipelines stall, and all merge requests break. Deploy Praefect with at least three Gitaly replicas, verify that replication health is monitored, and test failover before you need it.

**Granting every user admin access because "it is faster."** GitLab's group-based RBAC supports fine-grained permissions — read-only access to one project, maintainer access to another, owner of a group. When everyone is an admin, the audit trail loses all meaning (every action is authorized), and a compromised credential grants total platform control. Least privilege applied from the start is far cheaper than retrofitting it after an incident.

**Ignoring the security dashboard because "scanners have too many false positives."** Security scanners do produce false positives, and dismissing them without review is the correct action for findings that are genuinely not exploitable. But ignoring the dashboard entirely means real vulnerabilities accumulate invisibly, and the engineering team only discovers them when an external audit or a breach forces a retrospective scan. Weekly triage — even just 30 minutes to review new critical and high findings — keeps the vulnerability backlog manageable.

**Deploying the bundled PostgreSQL, Redis, and MinIO to production.** The Helm chart includes optional in-cluster deployments of these dependencies for evaluation convenience. They are not configured for persistence, high availability, or backup. Production deployments must use external, managed instances of each dependency — a cloud-managed PostgreSQL service, an external Redis cluster, and S3-compatible object storage — with the chart configured to disable the bundled versions.

**Using `latest` tags for CI runner images.** A CI job that pulls `python:latest` or `docker:latest` can break between pipeline runs when a new image version changes behavior or drops a dependency. Pin image tags to specific versions (`python:3.12`, `docker:27.0`) and upgrade intentionally, testing the new tag in a non-critical pipeline before rolling it out broadly.

---

## Decision Framework

The choice between GitLab's all-in-one model and a best-of-breed toolchain is not a technical question with a correct answer — it is an organizational tradeoff that depends on team size, operational maturity, compliance requirements, and the cost of integration labor relative to the cost of platform rigidity. The framework below provides durable decision points, not tool-specific recommendations.

```mermaid
graph TD
    A[Start] --> B{Self-hosting required?}
    B -->|Yes| C{Team size?}
    B -->|No, SaaS is fine| D{Integration pain high?}
    C -->|Small team, ≤15| E{Gitea/Forgejo + external CI}
    C -->|Medium/large team| F{HA ops capability?}
    F -->|Yes, have SRE capacity| G[GitLab self-hosted on Kubernetes]
    F -->|No ops bandwidth| H[GitLab.com SaaS or managed hosting]
    D -->|Yes, managing 5+ tools| I[GitLab.com — single platform]
    D -->|No, toolchain is working| J{Any driver to change?}
    J -->|No| K[Stay with current toolchain]
    J -->|Yes| I
```

---

## Did You Know?

- **GitLab's Origin**: GitLab was started by Dmitriy Zaporozhets in Ukraine in 2011 as an open-source alternative to GitHub. The first commit landed in October 2011, and the project grew into one of the largest all-remote organizations worldwide. The company now spans more than 65 countries and maintains a public-facing handbook at handbook.gitlab.com that documents nearly every internal process.

- **Monthly Release Cadence**: GitLab ships a new version on the 22nd of every month, every month. This predictable rhythm lets teams plan upgrade windows far in advance. Every third Thursday, a new release arrives with a detailed changelog. Major version upgrades follow the same cadence rather than being separate disruptive events.

- **The Handbook-First Culture**: GitLab's internal handbook is publicly available at handbook.gitlab.com and spans over 2,000 pages. It contains procedures, onboarding guides, engineering workflows, and company policies. The handbook-first approach means decisions and processes are documented before they are announced. This creates an unusual degree of transparency about how a large DevOps platform company operates internally.

- **Meltano Spin-Out**: The open-source DataOps platform Meltano began as an internal GitLab project for managing data pipelines and analytics. It was spun out as an independent company in 2021. The spin-out demonstrates how the platform's extensibility model allows internal tools to grow into standalone, community-governed products.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Under-provisioned runners | Slow CI, job queues | Autoscaling runners on Kubernetes |
| No artifact cleanup | Storage costs explode | Pipeline artifact expiration policies |
| Monolithic pipelines | Slow, hard to debug | Parent-child pipelines, includes |
| Ignoring security dashboard | Vulnerabilities accumulate | Weekly triage, block MRs on critical |
| Single Gitaly node | Data loss risk, bottleneck | Praefect with 3+ Gitaly nodes |
| No backup strategy | Disaster recovery becomes extremely difficult | Automated backups to object storage |
| Everyone is admin | Security nightmare | Group-based RBAC, least privilege |
| No runner tagging | Jobs run on wrong runners | Tag runners by capability |

---

## Quiz

<details>
<summary>1. What is the difference between GitLab CE and EE?</summary>

**Answer**: GitLab CE (Community Edition) is the open-source core, containing Git hosting, basic CI/CD, the container registry, issues, and merge requests — all at no cost. GitLab EE (Enterprise Edition) is the same codebase with additional features activated by a license key. The paid tiers are:

- **Free**: Equivalent to CE feature set, available on both SaaS and self-managed.
- **Premium**: Adds merge request approval rules, multi-approver policies, code owner enforcement, and enhanced CI/CD capabilities.
- **Ultimate**: Adds the full security suite (DAST, API fuzzing, coverage-guided fuzz testing), portfolio management, and value stream analytics.

The architectural significance is that EE features are not a separate product — they are the same application, same API, same database schema, with additional capabilities unlocked by license. Migrating from CE to EE is an in-place operation, not a reinstall.
</details>

<details>
<summary>2. Explain the purpose of Gitaly and Praefect.</summary>

**Answer**:
- **Gitaly** is a gRPC service that handles all Git repository operations on behalf of the GitLab Rails application. Instead of Rails shelling out to the `git` binary directly — which would consume memory and CPU from the web process and create a noisy-neighbor problem — Rails sends gRPC requests to Gitaly nodes, which perform the heavy I/O and Git computation in isolation. This decoupling improves security (Gitaly does not need access to the Rails database) and scalability (Gitaly nodes can be scaled independently of the web tier).

- **Praefect** is a cluster manager that sits between the Rails application and multiple Gitaly nodes. It provides:
  - Replication of Git data across nodes for durability.
  - Automatic failover when a Gitaly node becomes unhealthy.
  - Read distribution across replicas for load balancing.
  - Strong consistency guarantees for write operations.

For high availability in production, deploy Praefect with at least three Gitaly nodes. Without Praefect, a single Gitaly node is a single point of failure for all source code access.
</details>

<details>
<summary>3. How do parent-child pipelines differ from multi-project pipelines, and when would you use each?</summary>

**Answer**: Both patterns trigger additional pipelines, but they serve different organizational structures.

**Parent-child pipelines** live within a single repository. The parent pipeline uses the `trigger` keyword to include child pipeline configuration from files in the same repository. The `strategy: depend` option makes the parent wait for children to complete, so the parent pipeline status reflects the full result. This pattern suits monorepos: each service gets its own `.gitlab-ci.yml`, and `rules:changes` ensures that only the services whose files changed are built and tested.

**Multi-project pipelines** span repository boundaries. A pipeline in repository A triggers a pipeline in repository B using `trigger: { project: group/repo-b, branch: main }`. This pattern suits deployment orchestration where the application code lives in one repository and the deployment configuration (Helm charts, Terraform, Kubernetes manifests) lives in another. When the application pipeline passes, it triggers the deployment repository's pipeline to roll out the new version.

The key distinction: parent-child pipelines share a repository and a CI configuration namespace; multi-project pipelines cross repository boundaries and require explicit project access tokens or CI job tokens for authorization.
</details>

<details>
<summary>4. What security scanners are available in GitLab and how do they feed into the merge request workflow?</summary>

**Answer**: GitLab includes a suite of security scanners integrated into the CI pipeline. The scanners produce standardized JSON reports that are consumed by the GitLab application and surfaced in the merge request widget, the security dashboard, and the vulnerability report.

| Scanner | Detects | Runs On |
|---------|---------|---------|
| SAST | Code vulnerabilities (SQL injection, XSS, etc.) | Source code |
| Dependency Scanning | CVEs in declared dependencies | Package manifest files |
| Secret Detection | Leaked API keys, tokens, credentials | All files, all branches |
| Container Scanning | CVEs in OS packages and app deps in images | Built container images |
| IaC Scanning | Misconfigurations in Terraform, CloudFormation, etc. | Infrastructure-as-code files |
| DAST | Runtime vulnerabilities | Running application |
| API Fuzzing | API security issues | API endpoints |
| License Scanning | License compliance issues | Declared dependencies |

Scanners run as CI jobs and upload findings to GitLab. In the merge request, the security widget shows new vulnerabilities introduced by the change, with severity labels and an option to dismiss (for false positives) or create an issue (for tracking remediation). Merge request approval rules can be configured to block merging when critical vulnerabilities are detected, coupling security review to the code review workflow.
</details>

<details>
<summary>5. How do you configure GitLab CI/CD runners for Docker builds, and what are the security tradeoffs between the options?</summary>

**Answer**: Building container images inside CI jobs requires the build tool (typically Docker) to run inside the job's execution environment. Two approaches exist, with different security profiles:

**Docker-in-Docker (DinD)** runs a Docker daemon as a service container alongside the job container. The job's `docker` CLI connects to this daemon via TLS. This approach requires the runner to be `privileged: true`, which grants the job container nearly unrestricted access to the host kernel — a significant security concern in multi-tenant environments. The setup is:
```yaml
image: docker:27.0
services:
  - docker:27.0-dind
variables:
  DOCKER_TLS_CERTDIR: "/certs"
```

**Kaniko** builds container images without a Docker daemon, running entirely in userspace. It does not require privileged mode, making it the safer choice for untrusted workloads or shared runner fleets. Kaniko parses the Dockerfile and executes each instruction in the container's userspace, pushing the resulting layers directly to the registry. The setup is:
```yaml
build:
  image:
    name: gcr.io/kaniko-project/executor:latest
    entrypoint: [""]
  script:
    - /kaniko/executor --context $CI_PROJECT_DIR --dockerfile Dockerfile
```

The tradeoff: DinD provides full Docker daemon capabilities (build caching, multi-stage builds with cache mounts) and is faster for repeated builds on the same runner; Kaniko is more secure but slower and has limited cache support. For production CI/CD on shared Kubernetes runners, prefer Kaniko or similar daemonless builders unless the additional Docker daemon capabilities are required and the security boundary between jobs is trusted.
</details>

<details>
<summary>6. What is the purpose of GitLab environments and review apps?</summary>

**Answer**: Environments in GitLab track which commit is deployed to which named target (staging, production, review/feature-branch) and provide a centralized deployment history.

A review app extends this concept by creating an ephemeral environment for each merge request. When a developer pushes a branch and opens an MR, the CI pipeline deploys the branch's code to a temporary environment with a unique URL (typically derived from the branch slug). The MR page shows a "View app" button linking directly to the running deployment.

The configuration uses the `environment` key:
```yaml
deploy:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.staging.example.com
    on_stop: stop_review
    auto_stop_in: 1 week
```

Benefits include: reviewers can interact with the actual running application rather than evaluating a static diff; designers and product managers can validate changes without setting up a local development environment; and when the MR is merged or closed, GitLab can automatically trigger a stop job that tears down the environment and cleans up resources. The `auto_stop_in` setting ensures that abandoned MRs do not accumulate indefinitely, draining cluster resources and generating cost.
</details>

<details>
<summary>7. How does GitLab's merge request approval workflow enforce delivery governance?</summary>

**Answer**: Merge request approvals encode organizational policy into machine-enforced gates that prevent merging until satisfied. The components are:

1. **Approval rules**: Define how many approvals are required and from whom. Rules can target specific users, groups, or roles. A rule requiring "2 approvals from backend-maintainers" blocks the merge until two distinct members of that group approve.

2. **Code owners**: Defined in a `CODEOWNERS` file (in `.gitlab/CODEOWNERS`, `docs/CODEOWNERS`, or the repository root), mapping file patterns to required approvers. The rule `*.tf @platform-team` means any MR touching Terraform files requires platform team approval, regardless of who authored the change.

3. **Security approvals**: When configured, critical security scan findings block the merge. The security gate in the CI pipeline produces a report, and the MR widget shows the findings count; if the policy says "block on critical," the merge button is disabled until findings are dismissed or remediated.

4. **Pipeline success**: The MR cannot be merged if the pipeline is not green. This couples code review to automated verification — a reviewer's approval is not sufficient if the tests are failing or the security gate flagged issues.

Settings also allow preventing self-approval (the author cannot approve their own MR) and resetting approvals when new commits are pushed (so a "reviewed, changes requested, re-pushed" cycle requires re-approval).
</details>

<details>
<summary>8. How should you evaluate whether GitLab's all-in-one platform approach fits your organization, versus assembling a best-of-breed toolchain?</summary>

**Answer**: The evaluation is an organizational tradeoff, not a technical one — both approaches can produce working delivery pipelines. The durable factors to assess are:

**Integration depth vs. selection flexibility.** GitLab's all-in-one model eliminates integration glue between source control, CI, registry, security scanning, and deployment tracking — a single authentication system, a single audit trail, a single upgrade cadence. The cost is that you commit to GitLab's opinion about how each of these capabilities works. If your team strongly prefers a specific scanning engine, artifact store, or CI model, the all-in-one platform either forces adaptation or reintroduces the integration tax with external tooling.

**Operational overhead vs. operational control.** SaaS (GitLab.com) eliminates infrastructure operations entirely at the cost of data residency control and network dependency. Self-hosted on Kubernetes provides data sovereignty and marginal-cost economics at scale, but adds ongoing operational burden: PostgreSQL maintenance, Redis failover, Gitaly storage management, Helm chart upgrades, and Kubernetes cluster management. The answer depends on the organization's SRE maturity and compliance requirements, not on feature comparisons.

**Team size and cognitive load.** A small team (under 15 engineers) may find GitLab's complexity disproportionate to the integration benefit — a lightweight solution like Gitea plus a CI runner may provide sufficient capability with dramatically lower operational overhead. A larger team with compliance requirements (SOC 2, FedRAMP, HIPAA) benefits proportionally more from the unified audit trail and policy enforcement that the integrated model provides.

**Lock-in concern.** Adopting GitLab as the single platform for the entire delivery pipeline concentrates dependency on one vendor and one application. The migration cost out of GitLab is higher than migrating individual tools because the platform spans the entire SDLC. This is not automatically a reason to avoid it — many organizations accept this concentration in exchange for reduced integration labor — but it should be an explicit, acknowledged decision rather than an accidental consequence of adoption.

There is no universal correct answer. The question is whether the cost of maintaining integration glue between specialized tools exceeds the cost of adapting your workflows to the platform's opinion.
</details>

---

## Hands-On Exercise

**Objective**: Deploy GitLab on a local Kubernetes cluster and create a complete CI/CD pipeline with integrated security scanning.

### Part 1: Deploy GitLab (Using kind for local testing)

```bash
# Create kind cluster with ingress support
cat > kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
EOF

kind create cluster --config kind-config.yaml --name gitlab

# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Add GitLab Helm repo
helm repo add gitlab https://charts.gitlab.io/
helm repo update

# Minimal GitLab for testing (NOT for production!)
cat > gitlab-minimal.yaml << 'EOF'
global:
  hosts:
    domain: 127.0.0.1.nip.io
    https: false
  ingress:
    configureCertmanager: false
    class: nginx
    tls:
      enabled: false

certmanager:
  install: false

gitlab-runner:
  install: false

nginx-ingress:
  enabled: false

prometheus:
  install: false

# Minimal resources for local testing
gitlab:
  webservice:
    minReplicas: 1
    maxReplicas: 1
  sidekiq:
    minReplicas: 1
    maxReplicas: 1
  gitaly:
    persistence:
      size: 5Gi
EOF

# Install (takes 5-10 minutes)
helm upgrade --install gitlab gitlab/gitlab \
  --namespace gitlab \
  --create-namespace \
  --values gitlab-minimal.yaml \
  --timeout 600s

# Get root password
kubectl get secret gitlab-gitlab-initial-root-password \
  -n gitlab \
  -o jsonpath='{.data.password}' | base64 -d && echo

# Access at: http://gitlab.127.0.0.1.nip.io
# Login: root / <password from above>
```

### Part 2: Create CI/CD Pipeline

```bash
# Create a sample project in GitLab UI, then clone it
git clone http://gitlab.127.0.0.1.nip.io/root/sample-app.git
cd sample-app

# Create application
cat > app.py << 'EOF'
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/')
def hello():
    return jsonify({"message": "Hello from GitLab CI!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

cat > requirements.txt << 'EOF'
flask==3.0.0
pytest==7.4.0
EOF

cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
EOF

# Create tests
mkdir -p tests
cat > tests/test_app.py << 'EOF'
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_hello(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'message' in response.json
EOF

# Create GitLab CI pipeline
cat > .gitlab-ci.yml << 'EOF'
stages:
  - validate
  - build
  - test
  - security
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

default:
  image: python:3.11-slim

cache:
  paths:
    - .cache/pip

# Lint Python code
lint:
  stage: validate
  script:
    - pip install ruff
    - ruff check .
  allow_failure: true

# Build container image
build:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# Run tests
test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/ -v --junitxml=junit.xml
  artifacts:
    reports:
      junit: junit.xml

# Security scanning (included templates)
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml

# Deploy to staging environment
deploy-staging:
  stage: deploy
  script:
    - echo "Deploying $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA to staging"
    # In real scenario: kubectl set image deployment/app ...
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
EOF

# Commit and push
git add .
git commit -m "Initial application with CI/CD pipeline"
git push origin main
```

### Part 3: Verify Pipeline Execution

1. Go to GitLab UI → Your project → CI/CD → Pipelines
2. Watch pipeline execute through stages
3. Check Security tab for scan results
4. Review artifacts and test reports

### Success Criteria

- [ ] GitLab running on Kubernetes
- [ ] Project created with CI/CD pipeline
- [ ] All pipeline stages pass (lint, build, test)
- [ ] Security scans execute (SAST, dependency, secrets)
- [ ] Container image pushed to GitLab Registry
- [ ] Environment created for staging deployment

---

## Next Module

Continue to [Module 11.2: Gitea & Forgejo](../module-11.2-gitea-forgejo/) to learn about lightweight, self-hosted Git alternatives that run in a fraction of GitLab's resources.

## Sources

- [GitLab CI/CD YAML reference](https://docs.gitlab.com/ee/ci/yaml/) — The authoritative reference for `.gitlab-ci.yml` keywords, stages, jobs, rules, needs, and includes.
- [GitLab Runner documentation](https://docs.gitlab.com/runner/) — Covers runner installation, registration, executor types (Docker, Kubernetes, shell), and autoscaling.
- [GitLab Runner Kubernetes executor](https://docs.gitlab.com/runner/executors/kubernetes.html) — Configuration reference for running CI jobs as Kubernetes pods.
- [GitLab Auto DevOps](https://docs.gitlab.com/ee/topics/autodevops/) — Documentation for GitLab's automatic CI/CD configuration and deployment workflow.
- [GitLab merge requests](https://docs.gitlab.com/ee/user/project/merge_requests/) — The merge request lifecycle, approval rules, code owners, and review workflow.
- [GitLab merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/) — Approval rule configuration, code owner enforcement, and security approval gates.
- [GitLab environments and deployments](https://docs.gitlab.com/ee/ci/environments/) — Environment tracking, review apps, deployment history, and auto-stop configuration.
- [GitLab review apps](https://docs.gitlab.com/ee/ci/review_apps/) — Ephemeral per-MR deployment environments and their lifecycle management.
- [GitLab Container Registry](https://docs.gitlab.com/ee/user/packages/container_registry/) — Built-in per-project container registry with CI variable injection.
- [GitLab Container Registry — build and push images](https://docs.gitlab.com/ee/user/packages/container_registry/build_and_push_images.html) — Concrete examples of Docker and Kaniko builds pushing to the GitLab registry.
- [GitLab application security](https://docs.gitlab.com/ee/user/application_security/) — Overview of integrated security scanning capabilities: SAST, DAST, dependency, container, secret detection, and fuzzing.
- [GitLab SAST](https://docs.gitlab.com/ee/user/application_security/sast/) — Static application security testing configuration and supported languages.
- [GitLab Dependency Scanning](https://docs.gitlab.com/ee/user/application_security/dependency_scanning/) — Dependency vulnerability scanning across package ecosystems.
- [GitLab Container Scanning](https://docs.gitlab.com/ee/user/application_security/container_scanning/) — Trivy-based container image vulnerability scanning.
- [GitLab Secret Detection](https://docs.gitlab.com/ee/user/application_security/secret_detection/) — Automatic detection of leaked credentials, tokens, and keys.
- [GitLab Helm chart](https://docs.gitlab.com/charts/) — Official cloud-native Helm chart for deploying GitLab on Kubernetes.
- [GitLab reference architectures](https://docs.gitlab.com/ee/administration/reference_architectures/) — Production-grade deployment topologies with sizing guidance.
- [GitLab CI/CD pipeline architectures](https://docs.gitlab.com/ee/ci/pipelines/pipeline_architectures.html) — Parent-child pipelines, multi-project pipelines, and DAG-based execution.
- [GitLab CI/CD components](https://docs.gitlab.com/ee/ci/components/) — Reusable pipeline configuration components and templates.
- [GitLab CI/CD downstream pipelines](https://docs.gitlab.com/ee/ci/pipelines/downstream_pipelines.html) — Multi-project and parent-child pipeline trigger configuration.
- [GitLab CI/CD merge request pipelines](https://docs.gitlab.com/ee/ci/pipelines/merge_request_pipelines.html) — Pipeline behavior specific to merge requests.
- [GitLab code owners](https://docs.gitlab.com/ee/user/project/codeowners/) — CODEOWNERS file syntax and enforcement for per-file required approvers.
- [GitLab Duo](https://docs.gitlab.com/ee/user/gitlab_duo/) — GitLab's AI-assisted features for code suggestions and workflow automation.
- [GitHub Actions documentation](https://docs.github.com/en/actions) — Comparable CI/CD platform for the best-of-breed comparison and Rosetta.
- [Forgejo Actions documentation](https://forgejo.org/docs/latest/user/actions/) — Comparable lightweight CI/CD for the Gitea/Forgejo ecosystem.
- [GitLab Docker-in-Docker CI configuration](https://docs.gitlab.com/ee/ci/docker/using_docker_images.html) — Official guidance on Docker builds within GitLab CI, including DinD and Kaniko options.
- [GitLab project repository settings](https://docs.gitlab.com/ee/user/project/repository/) — Protected branches, default branch configuration, and repository-level governance.
- [GitLab architecture overview](https://docs.gitlab.com/ee/development/architecture.html) — Internal architecture documentation covering the Rails application, Gitaly, Sidekiq, and component interactions.
