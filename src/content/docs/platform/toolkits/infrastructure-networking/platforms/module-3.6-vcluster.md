---
revision_pending: false
title: "Module 3.6: vCluster"
slug: platform/toolkits/infrastructure-networking/platforms/module-3.6-vcluster
sidebar:
  order: 7
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: ~40 minutes

## Overview

Every developer wants their own Kubernetes cluster, and every platform team wants to avoid paying for a separate control plane per team. vCluster creates fully functional virtual Kubernetes clusters inside namespaces of a host cluster, giving tenants their own API server and control-plane semantics while scheduling real workloads on shared nodes. This module teaches the multi-tenancy spectrum first, then vCluster mechanics, so you can choose isolation levels deliberately instead of defaulting to expensive fleet sprawl. You will learn vCluster architecture including virtual control planes, syncers, and host relationships; installation paths through the CLI and Helm; the resource synchronization and isolation model; practical use cases spanning development environments, CI/CD, and multi-tenant platforms; and a Rosetta comparison against namespaces, Hierarchical Namespaces, Capsule, and dedicated clusters. Bring working knowledge of Pods, Deployments, Services, and Namespaces, basic kubectl and Helm usage, and the multi-tenancy framing from [Security Principles](/platform/foundations/security-principles/) so tenancy trade-offs feel familiar before you virtualize control planes.

---

## What You'll Be Able to Do

When you finish this module, you should be able to explain and execute the following outcomes in a real platform context:

- **Deploy virtual Kubernetes clusters within host clusters for lightweight multi-tenancy isolation**
- **Configure vcluster resource isolation, network policies, and synced resource mappings**
- **Implement vcluster for development environments, CI/CD testing, and multi-tenant platform offerings**
- **Compare vcluster's virtual cluster approach against namespaces and separate clusters for isolation trade-offs**

## Why This Module Matters

Kubernetes multi-tenancy is one of the hardest problems in platform engineering because the API is cluster-scoped by design. Namespaces were never meant to be security boundaries against malicious or careless tenants; they partition object names and RBAC scopes, but they still share one API server, one set of cluster-scoped admission webhooks, and one global CRD registry. When two teams install conflicting operators or a broken webhook rejects every Pod create cluster-wide, namespace labels do not save you. Dedicated clusters solve that blast-radius problem, but each cluster carries control-plane cost, upgrade cadence, credential sprawl, and operational attention that scales poorly when dozens of teams each want "their own cluster" for experimentation.

Virtual clusters sit in the middle of that spectrum. A tenant receives something that behaves like a real cluster—own API server, own namespaces, own RBAC, own CRDs—while the host cluster still owns nodes, the container runtime, the CNI, CSI storage classes, and physical isolation boundaries. Platform teams can offer cluster-shaped self-service without provisioning a new cloud control plane for every pull request. Developers get kubectl contexts that feel familiar, and operators retain a single fleet to patch, monitor, and back up. The trade-off is honest: you gain control-plane isolation and speed, but you do not get separate kernels or separate cloud accounts unless you add those layers yourself.

If you are building an Internal Developer Platform, understanding where vCluster fits on the tenancy spectrum is more valuable than memorizing Helm values. The decision is not "vCluster or nothing." It is "shared namespace with guardrails," "virtual cluster per tenant," "Capsule or HNC-enhanced namespaces," or "separate cluster per environment"—each with different cost, isolation, and operational profiles. This module gives you the mental model to defend that choice in architecture reviews and to implement the virtual-cluster path when it is the right fit.

## Did You Know?

- **Virtual etcd is not mandatory**: vCluster can back virtual cluster state with embedded etcd, SQLite, or an external PostgreSQL datastore depending on Helm values and scale requirements, which matters when you are planning memory overhead for hundreds of dev clusters on one host.
- **Pod names are rewritten on the host**: When the syncer copies a Pod from the virtual cluster to the host namespace, it encodes virtual metadata into the host object name so collisions cannot occur between tenants sharing one host namespace per vCluster instance.
- **Nodes are mirrored, not duplicated**: Virtual clusters typically see host nodes as read-only objects synced from the host API, so tenants understand capacity and scheduling constraints without gaining permission to drain or taint real infrastructure.
- **Distro choice is configurable**: The virtual control plane can run different Kubernetes distributions—commonly k3s, upstream Kubernetes, or k0s—so you can match distro features to tenant needs; verify the current default and supported versions in upstream docs rather than assuming one distro forever.

## Hypothetical scenario: Thirty Clusters, Runaway Cost, Zero Sleep

A mid-stage startup had thirty development teams, and each team demanded its own Kubernetes cluster for isolation after a bad incident where one team's broken admission webhook took down staging for everyone. The platform team obliged. Thirty managed Kubernetes clusters in two regions each carried control-plane fees, baseline node pools, ingress controllers, cert-manager installs, and monitoring agents duplicated across the fleet. A small platform group spent most of its time patching clusters and answering access tickets instead of building reusable platform capabilities.

They consolidated onto two regional host clusters and offered self-service virtual clusters instead of self-service cloud accounts. Developers still received isolated API servers, could install their own CRDs, and could experiment with cluster-admin inside their virtual boundary. Monthly infrastructure spend dropped sharply because one host fleet replaced dozens of control planes, while developer experience improved because cluster creation became a namespace-scoped operation rather than a ticket-driven provisioning workflow. The lesson is not that virtual clusters are free magic. The lesson is that throwing hardware at a tenancy problem without mapping isolation requirements to the spectrum usually buys cost without fixing the underlying shared-API failure modes namespaces cannot address.

## The Kubernetes Multi-Tenancy Spectrum

Before installing vCluster, map what "tenant isolation" must mean for your organization. Kubernetes documentation describes multi-tenancy as a spectrum of techniques rather than a single product switch. At the weakest end, multiple teams share one cluster and rely on namespaces, RBAC, ResourceQuotas, LimitRanges, and NetworkPolicies to stay out of each other's way. This works when teams trust each other, workloads are homogeneous, and no tenant needs to install cluster-scoped operators. Cost is minimal because there is only one control plane and one set of nodes. Blast radius is cluster-wide for CRDs, webhooks, and many security configurations.

One step stronger, namespace-enhancement projects add policy and hierarchy without giving each tenant a separate API server. Hierarchical Namespaces (HNC) let you nest namespaces, propagate policies, and delegate subtree administration so a platform team can hand a subtree to an application team with clearer boundaries than flat namespaces provide. Capsule runs as a multi-tenant operator on a shared cluster: tenants receive isolated namespaces grouped into Tenants, with policies enforced by the Capsule controller rather than by separate apiservers. Both approaches keep a single Kubernetes API and reduce coordination cost, but they cannot fully isolate CRD installation or webhook registration because those remain cluster-scoped concerns on one apiserver.

Virtual clusters add a lightweight control plane inside a host namespace. Each tenant kubectl talks to a virtual API server that stores namespaced and cluster-scoped objects in virtual etcd—or another backing store—and a syncer projects selected workloads into the host. Tenants experience cluster-admin semantics inside their boundary. The host still schedules Pods on shared nodes unless you combine virtual clusters with node pools, taints, or separate host clusters for stronger separation. At the strongest end of the spectrum, separate physical or logical clusters—whether created by Cluster API, managed Kubernetes, or hand-built kubeadm—offer the highest isolation: distinct control planes, cloud accounts, networking accounts, and upgrade windows. Cost and provisioning latency rise accordingly.

```
MULTI-TENANCY SPECTRUM (ISOLATION vs COST)
==========================================================================

LOW ISOLATION                                              HIGH ISOLATION
LOW COST                                                   HIGH COST
    │                                                            │
    ▼                                                            ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Shared       │   │ HNC /        │   │ vCluster     │   │ Separate     │
│ namespaces   │   │ Capsule      │   │ (virtual     │   │ clusters     │
│ + RBAC       │   │ enhanced     │   │  control     │   │ (EKS/GKE/    │
│ + quotas     │   │ namespaces   │   │  plane)      │   │  kind fleet) │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
     │                    │                    │                    │
  One API            One API              One API per            One API per
  server             server +             tenant inside          physical/logical
                     policy layer         host namespace         cluster
```

Platform engineers should document which tier they are selling to each audience. Internal trusted platform squads might live on enhanced namespaces. Partner or research tenants who install arbitrary operators belong on virtual clusters or separate clusters. Regulatory workloads that require account-level separation may still mandate separate clusters even if virtual clusters are technically sufficient for API isolation. The spectrum is a design tool, not a popularity contest.

Choosing a tenancy tier starts with threat modeling and product promises rather than installation convenience. Ask whether tenants are trusted colleagues, paying customers, or automated jobs with arbitrary code execution. Ask whether they must install cluster-scoped operators, custom admission webhooks, or API aggregation layers that register new API groups. Ask whether compliance auditors care about shared cloud accounts, shared kernels, or only about logical API separation. Answers map cleanly to spectrum positions: trusted homogeneous teams with namespace-scoped operators fit enhanced namespaces; teams that demand kubectl cluster-admin and Helm installs of arbitrary charts fit virtual clusters; regulated production environments with hard per-customer billing boundaries often still require separate clusters or at least separate host clusters per tier.

Migration paths also differ. Moving from flat namespaces to Capsule or HNC is mostly policy and hierarchy work on one API. Moving from namespaces to virtual clusters introduces new host namespaces, new kubeconfig endpoints, and new sync semantics tenants must learn. Moving from virtual clusters to separate clusters is often a export-and-reimport story for tenant YAML plus new infrastructure provisioning. Document the direction you expect growth to take so you do not paint teams into a tier that cannot evolve without replatforming. Many organizations standardize on virtual clusters for self-service dev and CI while keeping production on dedicated clusters, which is a valid hybrid rather than a failure to pick one winner.

Operational ownership should be explicit in the tier decision. Host cluster upgrades, ingress availability, CNI bugs, and node pool capacity remain platform responsibilities for every tier except fully separate clusters where tenants might own more stack layers. Virtual clusters add syncer health, virtual API availability, and chart version management to the platform SLO. When developers say they want "a cluster," clarify whether they are asking for operational isolation, API isolation, or billing isolation because only some combinations are true per tier. That conversation prevents the hypothetical scenario where thirty full clusters were purchased when thirty virtual apiservers on two hosts would have met the stated isolation requirement at lower control-plane cost.

## How a Virtual Cluster Works Inside a Host Namespace

A vCluster instance is not a simulation or a kubectl alias. It is a real, lightweight Kubernetes control plane running as Pods inside a dedicated namespace on the host—for example `vcluster-team-alpha`. Those Pods include a virtual API server, controller manager components for the chosen distro, and a backing store. When a tenant runs `kubectl apply`, the request hits the virtual API server, controllers reconcile objects into virtual storage, and the syncer watches virtual objects that must become real workloads on the host.

```
vCLUSTER ARCHITECTURE
════════════════════════════════════════════════════════════════════

HOST CLUSTER (real Kubernetes)
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Namespace: vcluster-team-alpha                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  VIRTUAL CLUSTER (team-alpha)                              │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │  │
│  │  │  API Server  │  │  Controller  │  │  etcd / SQLite │   │  │
│  │  │  (tenant     │  │  Manager     │  │  / PostgreSQL  │   │  │
│  │  │   distro)    │  │              │  │  (virtual)     │   │  │
│  │  └──────┬───────┘  └──────────────┘  └────────────────┘   │  │
│  │         │                                                  │  │
│  │  ┌──────▼───────┐                                          │  │
│  │  │   Syncer     │  Copies selected resources virtual → host │  │
│  │  └──────┬───────┘                                          │  │
│  └─────────┼──────────────────────────────────────────────────┘  │
│            ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Host Pods (scheduled on host nodes, names rewritten)       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Namespace: vcluster-team-beta (another isolated virtual CP)     │
└──────────────────────────────────────────────────────────────────┘
```

The tenant's kubeconfig points at the virtual API server, usually via port-forward or an ingress rule managed by the platform. From the tenant perspective, `kubectl get namespaces` shows only virtual namespaces such as `default`, `kube-system`, and whatever they created. Host namespaces like `kube-system` on the physical cluster are invisible. Conversely, a host administrator listing Pods in `vcluster-team-alpha` sees control-plane Pods plus synced workload Pods with encoded names. That asymmetry is the core isolation trick: two different API views over overlapping infrastructure.

| Component | Role |
|-----------|------|
| **Virtual API Server** | Accepts tenant kubectl traffic and stores objects in virtual storage |
| **Virtual Controller Manager** | Runs workload controllers inside the virtual cluster boundary |
| **Backing Store** | Persists virtual cluster state (embedded etcd, SQLite, or external DB) |
| **Syncer** | Translates virtual objects into host objects and syncs status back |
| **Host kubelet / scheduler** | Actually runs containers on host nodes for synced Pods |

### The Syncer Lifecycle for a Pod

When a developer creates a Deployment in the virtual cluster, the sequence is concrete and repeatable. The virtual API server records the Deployment. The virtual controller manager creates ReplicaSet and Pod objects in virtual storage. The syncer observes those Pods and creates corresponding Pod objects in the host namespace, rewriting names and labels so they cannot collide with another virtual cluster on the same host. The host scheduler assigns the Pod to a node. The host kubelet starts containers. Status changes propagate backward through the syncer so `kubectl get pods` inside the virtual cluster shows Ready conditions that match reality.

Services, Endpoints, PersistentVolumeClaims, ConfigMaps, Secrets referenced by Pods, and Ingresses commonly sync to the host by default so networking and storage integrate with the host CNI and CSI. Namespaces inside the virtual cluster, CRDs, ClusterRoles, and webhooks registered only in the virtual API generally stay inside virtual storage unless you explicitly configure broader sync rules. Misunderstanding that split is a common source of incidents: a Service that exists only virtually cannot receive traffic from the host ingress controller until sync is enabled and host networking is aligned.

Distro selection inside the virtual control plane is a platform design choice with tenant-facing consequences. k3s-based virtual clusters reduce resource footprint and bundle useful defaults, which helps dense dev hosts. Upstream Kubernetes distros maximize fidelity for teams testing conformance-sensitive controllers. k0s offers another lightweight path with different packaging assumptions. Host Kubernetes version and virtual distro version can diverge within supported skew bounds, which is valuable for upgrade rehearsal but confusing if tenants assume their virtual version equals the host version printed on node labels mirrored from the host API.

Backing store selection interacts with density and durability goals. Embedded etcd inside the virtual control plane is familiar and supports full Kubernetes semantics, yet memory per instance adds up when hundreds of CI clusters exist concurrently. SQLite and external PostgreSQL options trade slightly different operational models for lower per-instance overhead or centralized state management. Platform teams running external databases must secure connectivity, backup, and restore paths for that datastore because it becomes as critical as host etcd for tenant availability. Whatever store you pick, document restore drills: tenants will treat virtual clusters as disposable in CI and semi-durable in development, and both modes need tested deletion and recovery procedures.

The syncer is not a passive copy engine; it translates object semantics between APIs. Labels and annotations may be added or rewritten so host controllers can distinguish synced objects. Name rewriting prevents collisions when multiple virtual clusters create Pods named `nginx-abc123` in virtual `default` namespaces. Owner references and garbage collection paths differ between APIs, so orphaned host objects after partial failures require platform runbooks. When debugging sync delays, measure queue depth and reconcile latency on syncer Pods rather than assuming instant translation. High churn CI clusters creating thousands of objects per hour stress this path more than long-lived development clusters with modest object counts.

## Installing and Operating vCluster

Day-to-day operations combine the vCluster CLI for developer ergonomics with Helm for GitOps and platform automation. The CLI wraps namespace creation, chart installation, and kubeconfig context switching so a developer can type `vcluster create dev` and land inside a fresh cluster in seconds. Platform teams more often install the chart from a pipeline, pin versions, and inject values that enforce sync defaults, resource limits, and distro choices per tenant tier.

### Install the vCluster CLI

```bash
# macOS
brew install loft-sh/tap/vcluster

# Linux (amd64)
curl -L -o vcluster "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-linux-amd64"
chmod +x vcluster
sudo mv vcluster /usr/local/bin/

# Verify installation
vcluster --version
```

Verify the printed version against [github.com/loft-sh/vcluster/releases](https://github.com/loft-sh/vcluster/releases) before documenting it in runbooks. Pin CI pipelines to explicit release artifacts rather than `latest` redirects when reproducibility matters.

### Install via Helm for automation

```bash
helm repo add loft-sh https://charts.loft.sh
helm repo update
```

Helm installation is how platforms integrate vCluster with Argo CD or Flux. The chart deploys control-plane Pods, configures the syncer, and exposes values for distro selection, backing store, and sync mappings. Treat the chart version as part of your platform compatibility matrix alongside host Kubernetes version.

### Quick start with the CLI

```bash
# Create a virtual cluster named "dev" in namespace vcluster-dev
vcluster create dev

# kubectl now targets the virtual API server
kubectl get namespaces

# Create resources inside the virtual cluster
kubectl create namespace my-app
kubectl create deployment nginx --image=nginx -n my-app
kubectl get pods -n my-app
```

The create command creates the host namespace, installs the virtual control plane, and switches kubeconfig context. Developers experience a blank cluster except for virtual system namespaces. Platform engineers should still apply ResourceQuotas and NetworkPolicies on the host namespace before advertising self-service widely.

### Helm values for GitOps

```yaml
controlPlane:
  distro:
    k8s:
      enabled: true
  backingStore:
    etcd:
      embedded:
        enabled: true
  coredns:
    enabled: true
sync:
  toHost:
    pods:
      enabled: true
    services:
      enabled: true
    persistentvolumeclaims:
      enabled: true
  fromHost:
    nodes:
      enabled: true
    storageClasses:
      enabled: true
```

Distro and version fields change across chart releases. Read the chart README and upstream docs for the exact values schema on your target version instead of copying stale version strings from old modules. The pattern—pick distro, pick backing store, declare sync directions—remains stable even when field names shift slightly.

### Connecting, listing, and deleting

```bash
vcluster connect dev
vcluster connect dev --update-current=false -- kubectl get pods
vcluster list
vcluster disconnect
vcluster delete dev
```

`vcluster connect` is the bridge between platform-provisioned instances and developer laptops. For CI jobs, pass `--update-current=false` and invoke kubectl with the connect wrapper so parallel jobs do not fight over the default context. Deletion should remove the virtual control plane and synced objects according to chart hooks; validate cleanup in staging because orphaned host Pods waste capacity silently.

## Resource Synchronization and Isolation

Understanding default sync behavior is how you prevent "it worked in kubectl but nothing reachable" support tickets. The syncer is configurable, but defaults favor practicality: workloads and their networking/storage dependencies copy to the host, while tenant-scoped configuration objects often remain virtual.

| Resource | Direction | Behavior |
|----------|-----------|----------|
| **Pods** | virtual → host | Synced; containers run on host nodes |
| **Services** | virtual → host | Synced for host CNI integration |
| **Endpoints** | virtual → host | Synced with Services |
| **PersistentVolumeClaims** | virtual → host | Synced; uses host StorageClasses |
| **ConfigMaps / Secrets** | virtual → host | Synced when referenced by synced Pods |
| **Ingresses** | virtual → host | Synced when external access required |
| **Nodes** | host → virtual | Synced read-only for visibility |
| **StorageClasses** | host → virtual | Synced read-only |
| **Namespaces (virtual)** | isolated | Exist only in virtual storage |
| **CRDs** | isolated | Per-virtual-cluster CRD registry |
| **RBAC (ClusterRoles)** | isolated | Virtual cluster RBAC separate from host |
| **Admission webhooks (virtual)** | isolated | Registered only on virtual API server |

```
ISOLATION BOUNDARY
════════════════════════════════════════════════════════════════════

ISOLATED (per virtual cluster)     SHARED (from host)
─────────────────────────────      ─────────────────────────
CRDs                               Node capacity / kernel
RBAC (Roles, ClusterRoles)         Container runtime
Admission webhooks (virtual API)   CNI dataplane
Namespaces (virtual)               CSI drivers
ServiceAccounts (virtual)          Physical networks
API server config                  Ingress controller (host)
Controller managers                Load balancers (host)

Tenants can install Helm charts and operators inside the virtual API
without registering CRDs on the host—unless you explicitly widen sync.
```

Network isolation is not automatic just because API servers differ. Pods from different virtual clusters on the same host still share a CNI unless NetworkPolicies on host namespaces or additional segmentation block traffic. Node isolation is also shared: a noisy neighbor on the host kernel can still impact others unless you use dedicated node pools or separate host clusters for hard boundaries. vCluster solves control-plane tenancy; you still engineer data-plane tenancy deliberately.

## Use Cases for Development, CI/CD, and Multi-Tenant Platforms

Virtual clusters shine when tenants need cluster semantics quickly and repeatedly. Development environments are the canonical case: each engineer or team receives an isolated API where they can create namespaces, install CRDs, grant themselves cluster-admin inside the virtual boundary, and break things without registering a webhook on the host. Provisioning time is seconds instead of the minutes required to create a cloud cluster, and teardown is namespace deletion rather than cloud API orchestration.

CI/CD pipelines benefit the same way. A pipeline can create `ci-${BUILD_ID}`, apply manifests, run integration tests against a real API server, and delete the instance when the job finishes. Failed jobs do not leave cluster-scoped debris on the host because the virtual control plane disappears with the instance. Pipelines should still cap parallelism on one host because hundreds of simultaneous virtual clusters stress etcd, syncer CPU, and node capacity.

Multi-tenant platform offerings map cleanly onto virtual clusters when your product promise is "a cluster" rather than "a namespace." A platform API can accept a TeamCluster custom resource, render Helm values, and commit them to GitOps. Tenants receive kubeconfig credentials scoped to their virtual API. You implement quotas at the host namespace layer with ResourceQuotas and LimitRanges, and you implement policy at the host with admission on objects that sync. The implement path for development environments, CI/CD testing, and multi-tenant platform offerings is therefore the same toolchain—CLI or Helm—with different TTL, quota, and networking guardrails per tier.

```bash
# CI pattern: ephemeral cluster per build
vcluster create "ci-${BUILD_ID}" --connect=false
vcluster connect "ci-${BUILD_ID}" -- kubectl apply -f manifests/
vcluster connect "ci-${BUILD_ID}" -- kubectl wait --for=condition=ready pod -l app=myapp --timeout=120s
vcluster connect "ci-${BUILD_ID}" -- ./run-integration-tests.sh
vcluster delete "ci-${BUILD_ID}"
```

Upgrade testing is another strong fit. A host running Kubernetes 1.34 can host a virtual cluster running a different distro version for compatibility experiments. You validate controllers and manifests against the target version before rolling host upgrades. Always confirm supported version skew in upstream documentation because virtual distros follow their own release cadence.

Ephemeral per-pull-request environments illustrate how virtual clusters compress provisioning workflows. A GitOps controller or portal can create a virtual cluster named after the pull request, apply manifests from the branch, run smoke tests, publish logs, and delete the instance when the pull request closes. The alternative—provisioning a cloud cluster per pull request—often fails economically and socially because platform teams cannot absorb the API rate and credential overhead. Virtual clusters shift the bottleneck to host capacity and sensible concurrency limits, which platform engineers can govern with quotas and pipeline throttles rather than cloud account sprawl.

Teams experimenting with new CRDs and operators benefit because registration happens against the virtual API server. A tenant can install a custom operator, create cluster-scoped CRDs, and iterate on webhook configurations without asking platform approval for host-wide CRD installs. That accelerates research and vendor evaluations. Platform teams should still scan synced objects landing on the host and enforce policy with host admission because malicious or misconfigured operators inside the virtual boundary can still produce dangerous synced Pods. The win is containment of API registration, not automatic trust of workload content.

Training and onboarding labs use the same mechanics. Instructor provisioned virtual clusters give each student an isolated sandbox for the duration of a course module. Mistakes destroy only that virtual control plane. Compared with shared namespaces where students must coordinate object names, virtual clusters reduce support noise and mirror the cluster UX students will see in production tools. Record lab image versions and chart pins so exercises remain reproducible across semesters because drifting defaults frustrate both instructors and automated graders.

## Limits and Honest Trade-offs

Virtual clusters are not a replacement for every separate-cluster requirement. Compliance regimes that mandate separate cloud accounts, separate KMS keys, or separate audit boundaries may still require physical cluster separation regardless of API isolation. Kernel and hardware faults remain shared unless nodes are dedicated. Backup strategy must cover both host etcd and any external virtual backing stores you configure. Disaster recovery runbooks need steps for "virtual cluster corrupted" and "host cluster lost" because tenants depend on both layers.

Operational monitoring should include syncer health, virtual API latency, and host namespace quota utilization. A tenant who creates thousands of objects quickly can stress syncer throughput even while remaining inside abstract quota limits if those limits are misconfigured. Platform SLOs should measure end-to-end Pod readiness from the tenant API, not only host node health.

Cost savings come from consolidating control planes, not from eliminating nodes. Workloads still need CPU and memory on host workers. Savings appear when you retire duplicate managed control planes, duplicated ingress stacks, and duplicated platform agents. If every virtual cluster still requests large node pools, your bill remains workload-driven. Capacity planning shifts from "clusters times control-plane fee" to "host nodes times utilization," which is usually cheaper but not free.

Document tenant expectations in platform SLAs so virtual cluster offerings remain honest. State clearly that host maintenance windows apply to all tenants on a host, that ingress and DNS are shared services, and that noisy neighbor mitigation depends on quotas and policies operators configure rather than magic isolation. When tenants understand the shared dataplane, they make better choices about resource requests and escalation paths. When platform teams understand virtual clusters are control-plane virtualization—not full hardware multitenancy—they architect complementary guardrails instead of overselling isolation guarantees that namespaces never provided either.

## Rosetta Table: Tenancy Approaches Compared

Use this table when stakeholders ask how vCluster compares to namespace tooling and separate clusters. Rows describe capabilities tenants care about; columns describe approaches at different spectrum positions without declaring a universal winner.

| Tenancy capability | vCluster | Namespaces + HNC | Capsule | Separate clusters |
|--------------------|----------|------------------|---------|-------------------|
| Separate API server per tenant | Yes (virtual) | No | No | Yes (physical) |
| Install tenant-specific CRDs safely | Yes (virtual API) | No (cluster-wide) | Limited (policy-bound) | Yes |
| Isolate admission webhooks per tenant | Yes (virtual API) | No | Partial (Capsule policies) | Yes |
| Cluster-admin semantics for tenant | Yes (inside virtual boundary) | No | No (delegated namespace admin) | Yes |
| Provision new tenant quickly | Seconds | Instant | Seconds (namespace/Tenant) | Minutes to hours |
| Control-plane cost per tenant | Low (Pods in host NS) | None extra | Low (operator only) | High |
| Node/kernel isolation | Shared (unless node pools) | Shared | Shared | Can be dedicated |
| Network isolation default | Shared CNI; policy required | Shared CNI; policy required | Shared CNI; policy required | Often separate VPC/VNet |
| Different Kubernetes versions per tenant | Yes (virtual distro) | No | No | Yes |
| Regulatory account separation | No (host account) | No | No | Yes |

HNC helps organizations that need subtree delegation and policy inheritance without new apiservers. Capsule helps teams that want a Tenant abstraction with guardrails on a shared cluster. vCluster helps when tenants expect kubectl against their own API and operators that register cluster-scoped types. Separate clusters remain the right answer when the requirement is account-level or hardware-level separation, not merely API convenience. Revisit this table during architecture reviews when someone proposes "just give everyone a namespace" for a tenant who already asked to install a service mesh operator with cluster-scoped CRDs.

> **Landscape snapshot — as of 2026-06**
>
> vCluster is **not** a CNCF project. It is open-source under Apache-2.0, created and maintained by Loft Labs at [github.com/loft-sh/vcluster](https://github.com/loft-sh/vcluster). A commercial **vCluster Platform** product exists alongside the OSS core—treat the OSS engine and the commercial management layer as distinct offerings; do not present the vendor product as vendor-neutral or CNCF-hosted. Latest release as of 2026-06: **v0.35.0** (2026-06-16); verify current tags at [github.com/loft-sh/vcluster/releases](https://github.com/loft-sh/vcluster/releases). vCluster can run different distros (k3s, upstream Kubernetes, k0s) as the virtual control plane; verify the current default against upstream docs rather than asserting one distro as universal default.

## Platform Integration Patterns

Self-service platforms combine vCluster with portals and GitOps. [Backstage](../module-7.1-backstage/) templates can render Helm values and open a merge request. Argo CD or Flux reconciles the chart into the host cluster. Credentials return to the developer through the portal or an secrets integration. The following diagram shows the control flow without implying every organization must adopt all components.

```
SELF-SERVICE PLATFORM FLOW
════════════════════════════════════════════════════════════════════

Developer                    Platform Team
    │                             │
    │  Request virtual cluster    │
    │  (Backstage template)       │
    ▼                             │
┌─────────────┐                   │
│  Backstage  │                   │
│  Template   │                   │
└──────┬──────┘                   │
       │ Opens MR                 │
       ▼                          ▼
┌─────────────────────────────────────────┐
│  GitOps repository                      │
│  clusters/team-alpha/vcluster-values.yaml │
└──────────────────┬──────────────────────┘
                   │ Argo CD sync
                   ▼
┌─────────────────────────────────────────┐
│  Host cluster                           │
│  namespace vcluster-team-alpha          │
└──────────────────┬──────────────────────┘
                   │ kubeconfig delivery
                   ▼
           Developer uses virtual API
```

Resource quotas on the host namespace remain the primary economic guardrail. Without them, a virtual cluster can schedule until the host is starved.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: vcluster-team-alpha-quota
  namespace: vcluster-team-alpha
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
    services: "20"
    persistentvolumeclaims: "10"
```

Pair quotas with NetworkPolicies that default-deny cross-namespace traffic on the host, then allow only platform ingress paths. Document that ingress controllers and DNS still run on the host so platform teams own their upgrade and availability.

This pattern ties to [Platform Engineering Discipline](/platform/disciplines/core-platform/platform-engineering/) principles: golden paths, self-service, and reduced cognitive load. vCluster is the engine; GitOps and portals are how you make it safe at scale.

## Security, RBAC, and Tenant Boundaries

Virtual clusters change where RBAC applies, not whether RBAC exists. Inside the virtual API, ClusterRoles and Roles behave like any Kubernetes cluster: a tenant admin can grant broad permissions within the virtual boundary without receiving equivalent permissions on the host API. Host administrators still hold cluster-admin on the physical cluster and must treat synced objects as tenant-owned workloads living in designated namespaces. The security model is therefore two-layer: virtual RBAC governs what tenants can request through their API, and host RBAC plus admission policy governs what actually lands on shared infrastructure.

Platform teams should issue kubeconfig credentials that point only to the virtual API server for tenant users. Break-glass host access remains platform-only and should be audited because host admins can read synced Secrets in tenant namespaces unless additional encryption or secret sync policies are configured. When syncing Secrets to the host for Pod consumption, assume host administrators with namespace read can inspect them. For sensitive tenants, evaluate secret sync settings, encryption at rest on the host, and whether separate host clusters are warranted.

Admission control also splits across layers. Webhooks registered in the virtual cluster affect virtual API requests only. Host admission controllers still evaluate synced objects before they persist on the host API. A policy engine like OPA Gatekeeper or Kyverno on the host should enforce organizational guardrails—allowed registries, required labels, pod security levels—even when tenants have cluster-admin inside their virtual cluster. Document this clearly in tenant agreements so "cluster-admin" inside a virtual cluster never implies bypass of enterprise policy on the host.

Network policy design follows the same split. Default-deny NetworkPolicies on each `vcluster-*` host namespace prevent Pods from different virtual clusters from talking across namespace boundaries on the shared CNI. Ingress traffic typically enters through the host ingress controller targeting synced Services. If tenants need private service connectivity patterns, coordinate port ranges, DNS names, and TLS certificates at the host layer because the dataplane is shared even when APIs are separate.

## Debugging When Sync or Scheduling Fails

Support tickets for virtual clusters often arrive as "my Pod is Pending" or "my Service has no endpoints" even when the virtual API shows objects created successfully. Start debugging from the tenant perspective with `kubectl describe pod` inside the virtual cluster, then switch to the host namespace and locate the synced Pod by labels or rewritten name. If the virtual Pod exists but no host Pod appears, sync is disabled for Pods, the syncer is unhealthy, or admission on the host rejected the translated object. Check syncer Pod logs in the host namespace and verify Helm values for `sync.toHost.pods.enabled`.

If the host Pod exists but stays Pending, the problem is ordinary Kubernetes scheduling: insufficient CPU, taints, PVC binding failures, or priority classes on the host. The virtual scheduler does not place workloads on nodes directly; host scheduling decides. Teach tenant-facing runbooks to mention node capacity on the host because virtual `kubectl get nodes` shows mirrored nodes but cannot fix host capacity shortages without platform intervention.

When Services lack endpoints, trace Endpoints objects on both APIs. A virtual Service without synced Endpoints on the host cannot receive traffic from host ingress. Confirm Endpoints sync, selector labels on Pods survived translation, and readiness probes succeed on host kubelets. Ingress issues often trace to missing ingress sync or an ingress class on the host that tenants did not reference in their virtual Ingress objects.

API connectivity problems separate from workload problems. If `vcluster connect` fails, verify control-plane Pods are Ready, port-forward or ingress paths are healthy, and client certificates in kubeconfig match the virtual API server serving certificate. Version skew between CLI and chart can also manifest as confusing connect errors, so align CLI and chart versions in platform documentation. Keep a staging host cluster where platform engineers reproduce tenant issues with the same chart version production uses.

## Capacity Planning for Shared Host Fleets

Host fleet sizing shifts from counting clusters to counting peak concurrent virtual clusters and their summed quotas. Each virtual control plane consumes memory and CPU for API server, controllers, syncer, and backing store Pods. Embedded etcd per instance is convenient but multiplies memory overhead; SQLite or external databases trade operational complexity for denser packing on development hosts. Model control-plane overhead per instance in staging by creating representative virtual clusters and observing steady-state resource usage before promising hundreds of instances on one host.

Workload capacity still dominates long-term cost. Sum `ResourceQuota` hard limits across tenant namespaces and compare against host node allocatable resources, leaving headroom for system Pods, ingress, monitoring agents, and cluster autoscaling buffers. Autoscaling host nodes helps workload bursts but does not remove control-plane overhead per virtual cluster. For CI-heavy platforms, schedule concurrency limits so pipelines do not create unbounded virtual clusters during peak commit hours.

Storage planning must account for synced PVCs using host StorageClasses. Tenants choose StorageClasses mirrored from the host; platform teams should document which classes are safe for ephemeral CI versus durable development data. Backup policies should state whether tenant etcd snapshots, host etcd backups, or application-level backups cover disaster recovery. A virtual cluster deletion without backups loses virtual-only objects immediately while synced PVC data may persist on the host unless reclaim policies and finalizers are understood.

Upgrade sequencing matters for fleet stability. Upgrade host Kubernetes during maintenance windows with a tested matrix against pinned vCluster chart versions. Then roll chart upgrades tenant-by-tenant or namespace-by-namespace if required by breaking changes. Communicate distro version changes inside virtual clusters when tenants depend on specific Kubernetes feature gates. A documented compatibility matrix between host version, chart version, and virtual distro version prevents Friday-night surprises when a tenant requests a distro feature the syncer translation does not yet support.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No ResourceQuota on host namespace | One virtual cluster consumes all host CPU and memory | Apply quotas before enabling self-service |
| Assuming default network isolation | Cross-tenant traffic possible on shared CNI | Add NetworkPolicies on host namespaces |
| Running embedded etcd for every dev instance at scale | Memory overhead accumulates per virtual cluster | Use SQLite or shared DB tiers for dev; etcd for demanding tenants |
| Leaving CI virtual clusters behind after failed jobs | Orphaned control planes waste resources | TTL controllers or pipeline delete steps |
| Enabling ingress sync without host ingress plan | Services exist but are unreachable externally | Coordinate synced Ingresses with host ingress controller |
| Over-syncing CRDs or secrets to host | Unexpected cluster-wide objects and policy drift | Start from defaults; widen sync deliberately |
| Selling virtual clusters for account-separation compliance | Audit scope still includes host account | Match product tier to regulatory requirements |
| Pinning chart versions only in docs, not in GitOps | Drift between environments breaks tenants | Version charts in repo with tested matrix |

## Quiz

These questions test whether you can reason about tenancy trade-offs and sync behavior, not whether you memorized one Helm chart from a screenshot. Read each answer fully because the explanations connect spectrum positioning to operational consequences you will see in platform on-call rotations.

<details>
<summary>1. What role does the syncer play in vCluster architecture?</summary>

The syncer watches objects in virtual storage and creates or updates corresponding objects on the host cluster for resource types configured to sync—commonly Pods, Services, PVCs, and Ingresses. It also propagates status from host objects back to virtual objects so tenant kubectl output matches runtime reality. Without the syncer, the virtual API would be a hollow simulation with no containers running. The syncer is therefore the bridge between tenant intent (virtual API) and platform execution (host kubelet and CNI).
</details>

<details>
<summary>2. Why choose vCluster over plain namespace multi-tenancy for untrusted tenants?</summary>

Namespaces share one API server, one CRD registry, and cluster-scoped admission webhooks. A tenant who installs a broken webhook or conflicting CRD can impact every other tenant. vCluster gives each tenant a separate virtual API server and virtual control plane inside a host namespace, so CRDs, webhooks, and ClusterRoles remain inside the virtual boundary. Namespaces remain appropriate for trusted teams with simple workloads. vCluster fits when tenants need cluster-admin semantics or operator installation without host-wide side effects.
</details>

<details>
<summary>3. Where do Pods created in a virtual cluster actually execute?</summary>

They execute on the host cluster's nodes. The virtual controller manager creates Pod objects in virtual storage, the syncer copies them into the host namespace with rewritten names, the host scheduler assigns nodes, and host kubelets run containers. Tenants never schedule directly against host kubelets; they schedule against the virtual API, which the syncer translates. That is why node capacity, runtime classes, and taints on the host still matter to tenant workloads even though tenants cannot see host control-plane Pods.
</details>

<details>
<summary>4. How should a platform team implement vCluster for development environments and CI/CD testing on a multi-tenant platform?</summary>

Provision one virtual cluster per developer or per CI job using the CLI or Helm chart, apply ResourceQuotas and NetworkPolicies on each host namespace, integrate creation with GitOps or a portal for multi-tenant offerings, and enforce TTL deletion for CI instances. Development environments get longer-lived instances with moderate quotas; CI jobs get ephemeral names and aggressive cleanup. Multi-tenant platforms expose kubeconfig scoped to the virtual API and document that host ingress and storage classes are shared services. Testing and implementation both require validating sync defaults so Services and Ingresses behave as tenants expect.
</details>

<details>
<summary>5. What isolation does vCluster not provide by default?</summary>

vCluster does not provide separate Linux kernels, separate cloud accounts, or automatic network segmentation. Tenants share host nodes and the CNI unless operators add node pools, taints, or NetworkPolicies. A host kernel panic or noisy neighbor on a node can still affect multiple tenants. Regulatory account separation is also not automatic because billed infrastructure remains in the host account. Teams must add those layers explicitly or choose separate clusters when those boundaries are mandatory.
</details>

<details>
<summary>6. How do HNC and Capsule differ from vCluster on the tenancy spectrum?</summary>

HNC and Capsule enhance namespace hierarchy and policy on a single shared API server. They reduce coordination cost and improve delegation compared with flat namespaces, but they do not give each tenant a separate API server or isolated CRD registry. vCluster adds a virtual control plane per tenant inside a host namespace. Choose HNC or Capsule when one API is acceptable with stronger policy. Choose vCluster when tenants need cluster-shaped APIs and cluster-scoped resources without provisioning a new physical cluster.
</details>

<details>
<summary>7. When should you still prefer separate physical clusters over virtual clusters?</summary>

Prefer separate clusters when requirements include distinct cloud accounts, dedicated hardware, hard network perimeters, or compliance scopes that treat shared control-plane hosting as insufficient. Separate clusters also simplify blast-radius stories when every environment must upgrade independently with zero coupling to a host fleet. Virtual clusters win on speed and control-plane cost when API-level isolation suffices and shared nodes are acceptable. The decision should be requirement-driven, not based on which tool is newer.
</details>

## Hands-On Exercise

This exercise walks you through creating a virtual cluster on a local kind host, deploying a sample application inside the virtual API, inspecting synced objects from the host perspective, proving API isolation between two virtual clusters, and deleting both instances cleanly. Budget roughly thirty minutes and at least four gigabytes of free memory so the host cluster, virtual control plane, and nginx replicas can start without eviction pressure.

### Environment Setup

```bash
kind create cluster --name vcluster-host
brew install loft-sh/tap/vcluster
```

Use kind or minikube as the host cluster. Confirm `kubectl cluster-info` reports the kind endpoint before creating virtual clusters so you do not accidentally target a production context. If you lack Homebrew on Linux, download the vCluster binary from the GitHub releases page and place it on your PATH manually.

### Tasks

Start by creating a virtual cluster named `my-vcluster`, which provisions the control-plane Pods inside namespace `vcluster-my-vcluster` on the host and switches your kubeconfig to the virtual API server endpoint.

```bash
vcluster create my-vcluster
```

Inside the virtual cluster, list namespaces to confirm you see only virtual system namespaces, then create namespace `demo` and a two-replica nginx Deployment. Wait until `kubectl get pods -n demo` reports Running containers, which proves the virtual controllers and syncer translated your Deployment into host Pods.

```bash
kubectl get namespaces
kubectl create namespace demo
kubectl create deployment web --image=nginx --replicas=2 -n demo
kubectl get pods -n demo
```

Disconnect from the virtual cluster with `vcluster disconnect` and list Pods in the host namespace `vcluster-my-vcluster`. You should observe control-plane Pods plus synced workload Pods whose names encode virtual metadata, demonstrating that the host scheduler and kubelet run tenant containers even though the tenant kubectl session never referenced the host API directly.

```bash
vcluster disconnect
kubectl get pods -n vcluster-my-vcluster
```

Create a second virtual cluster named `my-vcluster-2`, list namespaces while connected to it, and verify that namespace `demo` from the first virtual cluster does not appear. Disconnect again to return to the host context, confirming that separate virtual apiservers maintain separate object stores even though both instances share the same physical kind nodes underneath.

```bash
vcluster create my-vcluster-2
kubectl get namespaces
vcluster disconnect
```

Finish by deleting both virtual clusters so host namespaces and control-plane Pods are removed. Confirm `kubectl get namespaces | grep vcluster` on the host returns nothing after deletion, which validates that your cleanup scripts for CI and development environments can rely on `vcluster delete` rather than manual object surgery.

```bash
vcluster delete my-vcluster
vcluster delete my-vcluster-2
```

Record the chart and CLI versions you used when the exercise succeeds.

### Success Criteria

- [ ] Virtual cluster created and accessible via kubectl
- [ ] Namespace and Deployment created inside virtual cluster
- [ ] Host cluster shows synced Pods with rewritten names
- [ ] Second virtual cluster cannot see first cluster's namespaces
- [ ] Both virtual clusters deleted without orphaned host namespaces

## Sources

- [vCluster documentation](https://www.vcluster.com/docs) — Official docs for architecture, installation, sync configuration, and operations.
- [github.com/loft-sh/vcluster](https://github.com/loft-sh/vcluster) — Source repository, issues, and contribution guide for the OSS engine.
- [github.com/loft-sh/vcluster releases](https://github.com/loft-sh/vcluster/releases) — Published versions and release artifacts; verify current tags before pinning CI.
- [kubernetes.io: Multi-tenancy](https://kubernetes.io/docs/concepts/security/multi-tenancy/) — Kubernetes guidance on tenancy models and isolation expectations.
- [kubernetes.io: Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) — Baseline namespace semantics that virtual clusters extend.
- [kubernetes.io: RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) — Authorization model on shared and virtual apiservers.
- [github.com/kubernetes-sigs/hierarchical-namespaces](https://github.com/kubernetes-sigs/hierarchical-namespaces) — HNC project for namespace hierarchy and policy propagation.
- [projectcapsule.dev](https://projectcapsule.dev/) — Capsule multi-tenant operator overview and concepts.
- [capsule.clastix.io](https://capsule.clastix.io/) — Capsule documentation site with installation and Tenant guides.
- [charts.loft.sh](https://charts.loft.sh) — Helm chart repository for vCluster platform installs.
- [vCluster 0.35.0 docs](https://www.vcluster.com/docs/vcluster/0.35.0/) — Version-specific documentation tree matching the 2026-06 release line.
- [github.com/loft-sh/vcluster tree main/docs](https://github.com/loft-sh/vcluster/tree/main/docs) — Upstream docs source alongside tagged releases.
- [Loft blog](https://loft.sh/blog) — Engineering posts on multi-tenancy patterns and virtual cluster operations.

## Cross-References

- [Module 7.1: Backstage](../module-7.1-backstage/) — Build a self-service portal that provisions vClusters
- [Module 7.2: Crossplane](../module-7.2-crossplane/) — Combine with Crossplane for full infrastructure self-service
- [Platform Engineering Discipline](/platform/disciplines/core-platform/platform-engineering/) — The principles behind self-service platforms
- [Security Principles](/platform/foundations/security-principles/) — Multi-tenancy and isolation theory

## Next Module

Continue to [Module 7.1: Backstage](../module-7.1-backstage/) to learn how to build an Internal Developer Portal that ties vCluster provisioning into a self-service experience.
