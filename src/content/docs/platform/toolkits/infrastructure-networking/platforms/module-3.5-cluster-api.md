---
qa_pending: true
title: "Module 3.5: Cluster API (CAPI)"
slug: platform/toolkits/infrastructure-networking/platforms/module-3.5-cluster-api
sidebar:
  order: 6
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~75 minutes

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a Cluster API management topology that separates management-plane responsibilities from workload-cluster responsibilities.
- **Debug** failed cluster provisioning by tracing `Cluster`, infrastructure, bootstrap, control-plane, and `Machine` resources through their reconciliation status.
- **Evaluate** when Cluster API, Terraform, Crossplane, managed Kubernetes services, or a fleet manager should own different parts of the cluster lifecycle.
- **Implement** local Cluster API lifecycle operations with the Docker provider, including create, inspect, scale, upgrade planning, and teardown.
- **Recommend** guardrails for production Cluster API fleets, including GitOps review, management-cluster backups, machine health checks, and safe deletion controls.

## Why This Module Matters

At 2:00 AM, a platform engineer at a payments company watched the incident channel fill with messages that all pointed back to one mistake: cluster upgrades were still being handled like individual maintenance projects. One engineer had upgraded a staging cluster successfully, copied most of the same commands into production, and hit an etcd membership problem on the third control-plane node. The failure was not only a command typo. The real failure was that every cluster had become a slightly different snowflake, with upgrade notes in tickets, bootstrap flags in old runbooks, and recovery knowledge stored in whoever happened to be on call.

That company did not need another wiki page explaining how to run `kubeadm upgrade`. It needed a way to declare what a cluster should look like, review that desired state before it changed production, and let controllers perform repeatable lifecycle operations. Cluster API, usually shortened to CAPI, applies the Kubernetes control-loop model to Kubernetes clusters themselves. Instead of treating clusters as special infrastructure that only humans can change, CAPI models clusters, machines, bootstrap configuration, and control planes as Kubernetes API objects.

This matters because platform teams rarely fail at cluster lifecycle management due to ignorance of one command. They fail because the workflow does not scale across environments, regions, providers, versions, and teams. A declarative lifecycle model lets the team ask better operational questions: what should exist, what currently exists, what controller owns the difference, and what evidence shows reconciliation is stuck. Those questions are easier to automate, review, audit, and teach than a collection of manual runbooks.

Throughout this module, you will start with the mental model of one management cluster managing one workload cluster, then add providers, templates, health checks, GitOps, and production boundaries. The goal is not to memorize every CAPI custom resource. The goal is to reason like a platform engineer who can inspect a broken cluster lifecycle, decide which component owns the failure, and design a safer fleet-management workflow.

## Core Content

## 1. The Control-Loop Model for Clusters

Cluster API starts with a simple but powerful idea: a Kubernetes cluster can manage other Kubernetes clusters by watching desired-state objects and reconciling infrastructure until reality matches the API. The cluster running the CAPI controllers is called the **management cluster**. The clusters it creates and maintains are called **workload clusters**. The management cluster stores the desired state, runs the controllers, and talks to infrastructure providers, while workload clusters run application workloads for teams.

This separation is the first design decision to understand, because it shapes every later operation. If the management cluster also runs business workloads, then a noisy application, bad deployment, or resource shortage can damage the very control plane responsible for repairing other clusters. Production CAPI installations therefore treat the management cluster as platform infrastructure. It should be small, protected, backed up, monitored, and changed through the same review process used for other high-impact platform systems.

```text
CLUSTER API OPERATING MODEL
==========================================================================

┌────────────────────────────────────────────────────────────────────────┐
│                         MANAGEMENT CLUSTER                            │
│                                                                        │
│  Desired state lives here: Cluster, MachineDeployment, templates,      │
│  MachineHealthCheck, provider-specific infrastructure resources.       │
│                                                                        │
│  ┌──────────────────────┐       ┌──────────────────────────────────┐   │
│  │ CAPI core controllers│       │ Provider controllers             │   │
│  │ reconcile generic    │──────▶│ create cloud VMs, networks,      │   │
│  │ cluster objects.     │       │ load balancers, and bootstrap.   │   │
│  └──────────────────────┘       └──────────────────────────────────┘   │
│                                                                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ provisions, upgrades, scales, deletes
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         WORKLOAD CLUSTERS                              │
│                                                                        │
│  prod-us-east             prod-eu-west             staging             │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
│  │ apps run here│         │ apps run here│         │ tests run here│    │
│  │ CNI installed│         │ CNI installed│         │ CNI installed │    │
│  └──────────────┘         └──────────────┘         └──────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

The management cluster does not magically become more important because it has more nodes. Its importance comes from the state it stores and the controllers it runs. If you lose a stateless web application, you can redeploy it from Git. If you lose the management cluster without a backup or a move plan, you may lose the authoritative API objects that describe every workload cluster. That does not necessarily destroy the workload clusters immediately, but it can leave the platform team unable to perform controlled upgrades, repairs, and deletions.

CAPI also changes how you debug cluster lifecycle problems. In a manual workflow, an engineer asks, "Which command failed?" In CAPI, the better question is, "Which resource is not reaching the condition that its owner expects?" A `Cluster` may wait for infrastructure. A control-plane object may wait for bootstrap data. A `Machine` may wait for an infrastructure machine. A workload cluster may wait for a CNI before nodes become fully usable. Debugging becomes a traversal across related resources and conditions.

> **Pause and predict:** If the management cluster is healthy, the cloud instances exist, and the workload cluster nodes still show `NotReady`, which part of the lifecycle is least likely to be the root cause: infrastructure provisioning, bootstrap, control-plane creation, or post-create cluster add-ons? Write your prediction before reading the next paragraph.

In that scenario, infrastructure provisioning is less likely to be the immediate blocker because machines already exist. Bootstrap and control-plane creation may still be involved, but a common post-create issue is missing networking. CAPI can create machines and form a Kubernetes control plane, but most providers do not install a CNI by default unless you explicitly add that step with a tool such as ClusterResourceSet, a GitOps application, or a bootstrap extension. Nodes can exist and still be unusable for application Pods until networking is installed.

The most useful mental model is to treat CAPI as a graph of owners and references. Generic CAPI resources describe lifecycle intent, while provider-specific resources know how to act on a particular infrastructure platform. When reconciliation gets stuck, you move along that graph in the same direction the controllers use: from `Cluster` to infrastructure cluster, from control plane to control-plane machines, from worker `MachineDeployment` to `MachineSet`, then to individual `Machine` and infrastructure machine objects.

| Concept | What It Owns | What It Usually Waits For | Debugging Signal |
|---|---|---|---|
| Management cluster | CAPI API objects and controllers | Provider controllers and credentials | Provider pods, CRDs, controller logs |
| Workload cluster | Application workloads and add-ons | Machines, CNI, kubeconfig access | Node readiness and cluster health |
| Reconciliation loop | Difference between desired and actual state | Referenced objects and external APIs | Conditions, events, owner references |
| Provider controller | Platform-specific infrastructure actions | Credentials, quotas, images, networks | Provider resource status and cloud events |

The table above is more than vocabulary. It is the structure you will use during an outage. If a `MachineDeployment` says it wants five replicas but only three machines exist, you inspect its `MachineSet`. If the `MachineSet` created machines but those machines have no infrastructure references ready, you inspect the provider-specific machine objects. If those objects show cloud API errors, the problem is no longer a Kubernetes scheduling problem. It is an infrastructure-provider reconciliation problem surfaced through Kubernetes status.

## 2. Providers and Resource Anatomy

CAPI stays portable by splitting cluster lifecycle work across provider types. The **core provider** defines generic resources such as `Cluster`, `Machine`, `MachineDeployment`, and `MachineSet`. An **infrastructure provider** creates platform resources such as virtual machines, networks, load balancers, security groups, or Docker containers. A **bootstrap provider** creates the instructions that turn a machine into a Kubernetes node. A **control-plane provider** manages control-plane machines, API server endpoints, and often etcd membership.

This split prevents CAPI from becoming one giant controller full of cloud-specific logic. The core controllers can reason about machines, ownership, and rollout behavior without knowing the details of EC2, Azure VM Scale Sets, vSphere templates, or bare-metal provisioning. Provider controllers handle those details behind API objects such as `AWSCluster`, `AzureMachineTemplate`, `VSphereMachineTemplate`, or `DockerCluster`. The result is a shared lifecycle model with provider-specific implementations.

```text
CAPI RESOURCE RELATIONSHIPS
==========================================================================

Cluster: team-payments-prod
│
├── InfrastructureCluster: AWSCluster/team-payments-prod
│   ├── VPC, subnets, security groups, load balancer
│   └── API endpoint published back to Cluster.status
│
├── ControlPlane: KubeadmControlPlane/team-payments-prod-control-plane
│   ├── KubeadmConfigTemplate for control-plane bootstrap data
│   ├── AWSMachineTemplate for control-plane instance settings
│   └── Machine objects for individual control-plane nodes
│
└── MachineDeployment: team-payments-prod-workers
    ├── MachineSet: rollout generation for worker nodes
    ├── KubeadmConfigTemplate for worker bootstrap data
    ├── AWSMachineTemplate for worker instance settings
    └── Machine objects for individual worker nodes
```

A `Cluster` is the top-level object that ties the lifecycle together. It normally references an infrastructure cluster object and a control-plane object. It also defines cluster network settings, such as Pod and Service CIDRs, that bootstrap components need when forming the workload cluster. The `Cluster` object is where you look for broad lifecycle readiness, but it is not where every failure detail lives. The details are often attached to lower-level resources as conditions and events.

A `MachineDeployment` is intentionally similar to a Kubernetes `Deployment`. It manages a desired number of worker machines through `MachineSet` objects, and those `MachineSet` objects manage individual `Machine` objects. That similarity is useful because it lets platform engineers reuse rollout intuition they already have from application deployments. A version change or template change creates a new rollout generation. The system creates replacement machines, waits for them to become ready, and then removes old machines according to rollout rules and health signals.

A `Machine` is the bridge between Kubernetes lifecycle intent and a real node. It references bootstrap configuration and an infrastructure machine. The bootstrap side answers, "How should this machine become a Kubernetes node?" The infrastructure side answers, "What real compute instance should exist?" The `Machine` becomes ready only when those pieces come together and the node joins the workload cluster successfully. When debugging, this makes the `Machine` one of the most valuable resources to inspect.

| Provider Type | Main Responsibility | Common Default | Failure Example |
|---|---|---|---|
| Core provider | Owns generic lifecycle objects and rollouts | Cluster API core controllers | `MachineDeployment` cannot create expected `MachineSet` |
| Infrastructure provider | Creates platform compute, network, and endpoint resources | CAPA, CAPZ, CAPV, CAPD, CAPM3 | Cloud quota prevents VM creation |
| Bootstrap provider | Generates node join configuration and initialization data | Kubeadm Bootstrap Provider, often called CABPK | Bootstrap secret never becomes available |
| Control-plane provider | Manages control-plane nodes and etcd-aware changes | Kubeadm Control Plane, often called KCP | Control-plane rollout pauses because etcd is unhealthy |

The default kubeadm-based stack is common because many learners already understand kubeadm from Kubernetes administration. `KubeadmControlPlane` manages the control plane, while the kubeadm bootstrap provider generates configuration for control-plane and worker nodes. That does not mean kubeadm is the only path. Some environments use Talos, k0s, MicroK8s, or other providers that express different operating-system and bootstrap choices while still participating in the same high-level CAPI lifecycle.

Provider choice is a production architecture decision, not just an installation option. The Docker provider, CAPD, is excellent for local learning and controller development because it uses Docker containers as machines. It is not a production provider. CAPA for AWS, CAPZ for Azure, CAPG for Google Cloud, CAPV for vSphere, CAPM3 for bare metal, and CAPO for OpenStack each expose different operational assumptions around images, networking, identity, quotas, and load balancers.

| Provider | Short Name | Infrastructure Target | Typical Use | Production Fit |
|---|---|---|---|---|
| AWS | CAPA | EC2, ELB, VPC, IAM-related integration | Cloud fleet clusters | Strong when AWS foundations are standardized |
| Azure | CAPZ | Azure VMs, VMSS, networking, load balancers | Enterprise Azure platforms | Strong when identity and networking are prepared |
| Google Cloud | CAPG | Compute Engine, networking, load balancers | GCP-hosted clusters | Strong when project and network models are clear |
| vSphere | CAPV | vSphere virtual machines and templates | Private cloud and datacenter Kubernetes | Strong when golden images and networks are mature |
| Metal3 | CAPM3 | Bare metal through Ironic | On-premises physical clusters | Strong but operationally demanding |
| Docker | CAPD | Docker containers as machines | Local development and training | Not for production workload clusters |
| OpenStack | CAPO | OpenStack compute and networking | Private cloud environments | Strong when OpenStack operations are stable |
| Hetzner | CAPH | Hetzner cloud and server options | Cost-sensitive cloud clusters | Community-driven, evaluate support needs |

A senior platform engineer evaluates providers through the entire lifecycle, not only cluster creation. Ask how credentials are stored, how images are built, how API endpoints are exposed, how failed machines are detected, how upgrades work, and how deletion behaves under partial failure. A provider that can create a demo cluster in ten minutes may still be a poor fit if it cannot express your network topology, image-hardening process, or compliance controls.

> **Pause and decide:** Your team wants CAPI on vSphere, but each application team currently builds its own VM template with different container runtimes and OS hardening. Would you start by writing CAPI manifests, or by standardizing machine images first? Decide which dependency is more important and explain the operational risk you are reducing.

The safer answer is to standardize the machine images first, or at least establish the image contract before scaling CAPI usage. CAPI can reconcile machines repeatedly, but it cannot make inconsistent base images behave like a consistent platform. If worker nodes boot with different kernel modules, container runtimes, kubelet flags, or security settings, a declarative lifecycle system will reproduce that inconsistency faster. Automation amplifies both good standards and bad drift.

## 3. Worked Example: Trace a Stuck Docker Workload Cluster

Before you build a cluster yourself, it helps to see how an experienced operator traces a failed lifecycle. In this worked example, a team uses CAPD for local testing. They created a management cluster, initialized CAPI, generated a Docker workload cluster, and applied the manifest. After several minutes, `clusterctl describe cluster` shows the cluster as not fully ready, and the worker node is not usable.

The first move is not to delete everything and try again. The first move is to inspect the owner graph. CAPI exposes progress through resources, conditions, and events. You want to know whether the `Cluster` is waiting for infrastructure, whether the control plane is initialized, whether machines exist, and whether the workload cluster has the add-ons needed for node readiness.

```bash
# In this module, kubectl commands use the short alias k after this point.
alias k=kubectl

# Start at the top-level cluster and inspect the condition summary.
clusterctl describe cluster my-workload

# See the main CAPI resources in the management cluster.
k get clusters,machinedeployments,machines

# Inspect the Cluster conditions when the summary is not enough.
k describe cluster my-workload
```

Suppose the output shows that the control plane is initialized and the worker `Machine` exists, but the node in the workload cluster is `NotReady`. That narrows the problem. The infrastructure provider has done enough to create a machine. Bootstrap has done enough for the node to attempt joining. The next check is whether the workload cluster has a CNI. With CAPD and many generated examples, the cluster lifecycle and the cluster add-on lifecycle are separate concerns.

```bash
# Fetch the workload cluster kubeconfig from the management cluster.
clusterctl get kubeconfig my-workload > my-workload.kubeconfig

# Inspect nodes from the workload cluster perspective.
k --kubeconfig my-workload.kubeconfig get nodes -o wide

# Inspect Pod scheduling and networking symptoms.
k --kubeconfig my-workload.kubeconfig get pods -A
k --kubeconfig my-workload.kubeconfig describe node \
  "$(k --kubeconfig my-workload.kubeconfig get nodes -o jsonpath='{.items[0].metadata.name}')"
```

A node that reports networking plugin errors is not a CAPI machine-creation failure. It is a post-create add-on gap. In a production setup, you would not ask operators to remember this step manually. You would install a CNI through a GitOps application, ClusterResourceSet where appropriate, or another controlled add-on mechanism that runs after the workload cluster API becomes available. The important lesson is that CAPI manages cluster infrastructure lifecycle, while cluster add-ons still need an explicit lifecycle owner.

Now imagine a different symptom: no `Machine` objects appear for the worker pool. That points back to the `MachineDeployment` and `MachineSet` path. You would inspect selector matching, template references, rollout status, and controller events in the management cluster. If machines appear but infrastructure machines do not become ready, you inspect the provider-specific machine object and the provider controller logs. Each symptom moves you to a different part of the graph.

```bash
# Worker rollout path in the management cluster.
k get machinedeployment
k describe machinedeployment my-workload-md-0

# MachineSet and Machine path for a stuck worker rollout.
k get machinesets
k describe machineset -l cluster.x-k8s.io/cluster-name=my-workload

# Provider controller logs are useful when object status shows an external error.
k -n capd-system logs deploy/capd-controller-manager
```

This worked example demonstrates a repeatable debugging pattern. Start with the highest-level object to understand the current phase. Follow owner references and conditions downward until you find the resource whose status contains a concrete blocker. Then decide whether the blocker belongs to CAPI core, the infrastructure provider, bootstrap, control-plane management, workload-cluster add-ons, or the external platform. That discipline prevents random command execution during incidents.

The same pattern applies across providers, although the object names differ. On AWS, a stuck infrastructure machine may point to IAM, AMI, subnet, security group, or quota problems. On vSphere, it may point to template, datastore, folder, or network mapping problems. On bare metal, it may point to inspection, provisioning, hardware state, or BMC credentials. The generic graph stays stable, while the provider-specific leaf nodes reveal the platform details.

| Symptom | First Object to Inspect | Likely Area | Useful Next Evidence |
|---|---|---|---|
| `Cluster` never gets an API endpoint | Infrastructure cluster object | Load balancer or control-plane endpoint | Provider status, events, controller logs |
| Control plane exists but workers never appear | `MachineDeployment` and `MachineSet` | Worker rollout or template reference | Selectors, template names, owner references |
| Machines exist but provider machines are not ready | Provider-specific machine object | Cloud or virtualization platform | Quota, image, network, credentials, logs |
| Nodes join but remain `NotReady` | Workload cluster nodes and Pods | CNI or add-on lifecycle | Node conditions, kube-system Pods |
| Upgrade starts but old nodes remain | Control plane or `MachineDeployment` rollout | Drain, health, disruption, version skew | Rollout conditions, PodDisruptionBudgets, events |

Notice that this table does not recommend memorizing every command. It recommends asking which layer owns the symptom. That distinction is what moves the learner from beginner to practitioner. Beginners often see "cluster not ready" as one problem. Senior engineers split it into desired state, controller ownership, external platform state, node bootstrap, workload-cluster readiness, and add-on lifecycle.

## 4. Hands-On Walkthrough with CAPD

The Docker provider gives you a safe local environment for practicing lifecycle operations. CAPD creates Docker containers that behave like machines for a Kubernetes cluster. You should treat this as a learning and development provider only. It teaches the CAPI control model, object graph, and rollout workflow without requiring a cloud account, but it does not represent production-grade availability, networking, storage, or security.

Before running the commands, verify that Docker, `kind`, `kubectl`, and `clusterctl` are installed. The examples below target Kubernetes v1.35 or newer where your provider supports it. If a provider release does not yet support the newest patch version, use a supported v1.35 patch value from that provider's release notes. The key principle is to keep the management cluster, provider versions, and workload Kubernetes versions inside supported compatibility ranges.

```bash
# Install clusterctl on Linux amd64. On macOS or another architecture,
# adjust the release asset name for your operating system and CPU.
curl -L \
  "https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/clusterctl-$(uname -s | tr '[:upper:]' '[:lower:]')-amd64" \
  -o clusterctl

chmod +x clusterctl
sudo mv clusterctl /usr/local/bin/clusterctl

clusterctl version
kind version
kubectl version --client
```

Create a management cluster with `kind`, then initialize CAPI with the Docker infrastructure provider. This management cluster is just for the lab, so a single local kind cluster is fine. In production, you would design the management cluster with stronger availability, backup, identity, network, and access-control boundaries.

```bash
kind create cluster --name capi-management

clusterctl init --infrastructure docker

k get pods -A
k -n capi-system get deploy
k -n capd-system get deploy
k -n capi-kubeadm-bootstrap-system get deploy
k -n capi-kubeadm-control-plane-system get deploy
```

Do not move on just because the command returned. Wait until provider controller Deployments are available. CAPI depends on multiple controllers, and a missing provider controller creates confusing downstream symptoms. The management cluster should have core CAPI controllers, Docker provider controllers, kubeadm bootstrap controllers, and kubeadm control-plane controllers before you apply a workload cluster manifest.

```bash
k wait --for=condition=Available deployment \
  -n capi-system --all --timeout=180s

k wait --for=condition=Available deployment \
  -n capd-system --all --timeout=180s

k wait --for=condition=Available deployment \
  -n capi-kubeadm-bootstrap-system --all --timeout=180s

k wait --for=condition=Available deployment \
  -n capi-kubeadm-control-plane-system --all --timeout=180s
```

Generate a workload cluster manifest instead of writing every object by hand. The generated manifest is not magic. It is a teaching artifact you should inspect. You will see a `Cluster`, a Docker infrastructure cluster, a kubeadm control-plane object, infrastructure templates, bootstrap templates, and a worker `MachineDeployment`. That generated file is often the easiest way to learn which objects a provider expects.

```bash
clusterctl generate cluster my-workload \
  --flavor development \
  --kubernetes-version v1.35.0 \
  --control-plane-machine-count 1 \
  --worker-machine-count 2 \
  > my-workload-cluster.yaml

k apply --dry-run=client -f my-workload-cluster.yaml

k apply -f my-workload-cluster.yaml
```

Now watch reconciliation from the management cluster. The point is not to stare at a spinner. The point is to connect changing object status to the lifecycle phases you learned earlier. First the cluster infrastructure appears. Then the control plane becomes available. Then worker machines join. Finally, workload-cluster readiness depends on add-ons such as the CNI.

```bash
clusterctl describe cluster my-workload

k get clusters
k get kubeadmcontrolplanes
k get machinedeployments
k get machines -w
```

When the workload cluster API is reachable, fetch its kubeconfig and inspect nodes. You may see nodes before they are fully ready. That is expected in a bare cluster that still needs networking. Install a CNI suitable for the lab, then verify that nodes and system Pods stabilize. The exact CNI version should be chosen from the CNI project's current compatibility matrix when you run this in a real environment.

```bash
clusterctl get kubeconfig my-workload > my-workload.kubeconfig

k --kubeconfig my-workload.kubeconfig get nodes

k --kubeconfig my-workload.kubeconfig apply -f \
  https://raw.githubusercontent.com/projectcalico/calico/v3.30.0/manifests/calico.yaml

k --kubeconfig my-workload.kubeconfig get pods -A
k --kubeconfig my-workload.kubeconfig wait --for=condition=Ready nodes --all --timeout=300s
```

Scale the worker pool by changing the desired state on the `MachineDeployment`. This is the moment where CAPI feels familiar to Kubernetes users. You are not manually creating containers, joining nodes, or editing provider state. You are changing the desired replica count and letting controllers create machines, bootstrap them, and join them to the workload cluster.

```bash
k patch machinedeployment my-workload-md-0 \
  --type merge \
  -p '{"spec":{"replicas":4}}'

k get machinedeployments
k get machines -w

k --kubeconfig my-workload.kubeconfig get nodes
```

> **Pause and predict:** After you patch the worker `MachineDeployment` from two replicas to four, which object should change first: the workload cluster `Node` list or the management cluster `Machine` list? Predict the order, then run the commands above and compare the result.

The management cluster `Machine` list should change before the workload cluster `Node` list. CAPI must create desired machine objects, the infrastructure provider must create backing compute, bootstrap data must be used, and only then can kubelet join the workload cluster as a node. That order matters during troubleshooting. If you expect nodes first, you may inspect the workload cluster too early and miss the controller progress visible in the management cluster.

Plan an upgrade carefully instead of applying it casually. In CAPI, a Kubernetes version change commonly triggers rolling replacement rather than an in-place upgrade of existing machines. The control plane must respect Kubernetes version-skew policy, etcd health, and disruption constraints. Worker pools then roll forward through new machines. For a local lab, you can inspect the manifest fields and discuss the rollout; for production, you would validate provider support, image availability, add-on compatibility, and rollback strategy before changing the version.

```bash
# Inspect current versions across the CAPI objects.
k get kubeadmcontrolplane my-workload-control-plane -o jsonpath='{.spec.version}{"\n"}'
k get machinedeployment my-workload-md-0 -o jsonpath='{.spec.template.spec.version}{"\n"}'

# Example only: patch to a supported target version after checking provider compatibility.
k patch kubeadmcontrolplane my-workload-control-plane \
  --type merge \
  -p '{"spec":{"version":"v1.35.1"}}'

k patch machinedeployment my-workload-md-0 \
  --type merge \
  -p '{"spec":{"template":{"spec":{"version":"v1.35.1"}}}}'
```

Do not treat deletion as an afterthought. Cluster deletion is a high-impact lifecycle operation because CAPI finalizers coordinate teardown across machines and provider resources. In a lab, deletion demonstrates cleanup. In production, deletion should be gated through Git review, protected branches, admission policy, or manual approvals. A single deleted `Cluster` object can cascade into real infrastructure deletion if the provider and finalizers are healthy.

```bash
k delete cluster my-workload

k get clusters
k get machines -w

kind delete cluster --name capi-management
```

After cleanup, reflect on which steps were lifecycle operations and which steps were add-on operations. Creating the workload cluster, scaling machines, and deleting machines were CAPI lifecycle operations. Installing Calico was an add-on operation against the workload cluster. A mature platform has an owner for both. CAPI without add-on management creates empty clusters. Add-on management without lifecycle control leaves teams with hand-built infrastructure.

## 5. ClusterClass, GitOps, and Fleet Design

Individual CAPI manifests become repetitive as soon as you manage more than a few clusters. Without a template mechanism, every team copies a pile of YAML, edits names and sizes, and gradually introduces drift. `ClusterClass` addresses that problem by defining reusable cluster topology. A cluster can then reference a class and provide variables such as version, control-plane replicas, worker pools, and provider-specific values.

ClusterClass is not just a convenience feature. It is a fleet-governance tool. By controlling the classes available to teams, a platform group can standardize supported shapes such as `dev-small`, `prod-regional`, or `regulated-prod`. Those classes can encode infrastructure templates, control-plane strategy, machine deployment classes, and patches. Application teams can request clusters through a smaller interface, while platform engineers retain control over the deeper lifecycle contract.

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: team-payments-prod
  namespace: default
spec:
  topology:
    class: standard-production
    version: v1.35.0
    controlPlane:
      replicas: 3
    workers:
      machineDeployments:
        - class: default-worker
          name: worker-pool
          replicas: 6
```

This small `Cluster` object can produce many underlying resources when the referenced `ClusterClass` exists. The learner should not mistake small YAML for simple behavior. The class hides complexity, which is useful only when the class is well designed, versioned, documented, and tested. If the class changes carelessly, every cluster using it may be affected. That makes ClusterClass changes similar to API changes in a platform product.

A good fleet design separates foundations from cluster lifecycle. Many teams still use Terraform for base cloud resources such as accounts, projects, IAM boundaries, DNS zones, network foundations, and shared observability destinations. CAPI then owns Kubernetes cluster lifecycle inside those foundations. Crossplane may expose databases, queues, buckets, and other cloud services to developers through Kubernetes APIs. These tools overlap at the edge, but they are strongest when each owns the lifecycle it understands best.

| Dimension | Cluster API | Terraform | Crossplane |
|---|---|---|---|
| Primary model | Kubernetes CRDs and controllers | HCL configuration and state | Kubernetes CRDs and controllers |
| Reconciliation style | Continuous controller reconciliation | Planned apply workflow | Continuous controller reconciliation |
| Strongest scope | Kubernetes cluster lifecycle | General infrastructure foundations | Cloud services exposed through Kubernetes APIs |
| State location | Management cluster etcd | Terraform state backend | Kubernetes etcd |
| Drift behavior | Controllers keep checking desired state | Detected during plan or refresh | Controllers keep checking desired state |
| Cluster upgrade support | Built into CAPI lifecycle model | Usually scripted or module-specific | Depends on composition and provider |
| Best fit | Fleet cluster lifecycle | Accounts, networks, IAM, shared foundations | Self-service cloud resources |

The practical boundary is usually organizational. Terraform is often controlled by infrastructure engineers who own accounts, networks, and identity. CAPI is often controlled by platform engineers who own cluster lifecycle and Kubernetes reliability. Crossplane is often used to expose selected cloud resources through a platform API. A mature platform can use all three without forcing one tool to own everything.

GitOps fits naturally because CAPI resources are Kubernetes objects. An Argo CD or Flux installation can point at a repository of cluster definitions and apply them to the management cluster. This creates a reviewable path for cluster creation, scaling, and upgrades. However, deletion must be handled cautiously. Automated pruning that is reasonable for ordinary application manifests can become dangerous when the resource being pruned represents an entire cluster and its infrastructure.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cluster-fleet
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example-org/cluster-fleet
    targetRevision: main
    path: clusters
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: false
      selfHeal: true
```

The `prune: false` setting in this example is intentional. It prevents a Git removal or path mistake from automatically deleting cluster resources. Some teams eventually implement controlled deletion workflows, but they do so with explicit approvals and safeguards. Cluster lifecycle is different from application rollout because the blast radius includes nodes, load balancers, persistent infrastructure, and sometimes customer-facing environments.

Production fleet design also needs backup and move planning. CAPI includes `clusterctl move`, which can move CAPI objects from one management cluster to another during management-cluster migration. That capability is valuable, but it is not a replacement for disciplined backups, tested restore procedures, and clear runbooks. If the management cluster fails, the workload clusters may keep running, but your ability to manage them declaratively depends on recovering or reconstructing the management state.

```text
FLEET MANAGEMENT WITH GITOPS AND CAPI
==========================================================================

┌────────────────────┐       pull request        ┌──────────────────────┐
│ Platform repository│──────────────────────────▶│ Review and policy     │
│ clusters/*.yaml    │                           │ branch protection     │
└─────────┬──────────┘                           └──────────┬───────────┘
          │ merged desired state                             │
          ▼                                                   ▼
┌────────────────────┐       apply objects        ┌──────────────────────┐
│ GitOps controller  │──────────────────────────▶│ Management cluster    │
│ Argo CD or Flux    │                           │ CAPI controllers      │
└────────────────────┘                           └──────────┬───────────┘
                                                            │ reconcile
                                                            ▼
                                               ┌──────────────────────────┐
                                               │ Workload cluster fleet    │
                                               │ dev, staging, production  │
                                               └──────────────────────────┘
```

GitOps also gives you a teaching and audit advantage. Every cluster version bump, replica change, template update, and class migration can be reviewed as a diff. Reviewers can ask whether the target Kubernetes version is supported, whether worker pools will roll safely, whether CNI and ingress add-ons are compatible, and whether deletion protections are in place. That discussion is much better than discovering a risky change from a shell history after an outage.

## 6. Production Operations and Senior-Level Trade-Offs

The senior-level question is not "Can CAPI create a cluster?" The senior-level question is "Should CAPI be the lifecycle owner for this cluster, and what operational contract makes that safe?" CAPI works best when the platform team can standardize provider credentials, images, networks, Kubernetes versions, add-on installation, observability, backup, and deletion policy. If those pieces are chaotic, CAPI may create clusters quickly while exposing deeper organizational inconsistency.

Start production design with failure domains. A management cluster should be more reliable than a throwaway lab cluster, but it should not become a giant shared application cluster. Run only the controllers and tools needed for lifecycle management. Restrict who can modify CAPI resources. Monitor controller health, reconciliation latency, provider API errors, and management-cluster etcd health. Back up the management cluster and test restore or move operations before you depend on them during an incident.

Machine health checks turn node failure into declarative remediation. A `MachineHealthCheck` can identify unhealthy machines and trigger replacement. That is powerful, but it needs careful thresholds. Aggressive remediation during a network partition or provider outage can make a bad situation worse by deleting machines that are temporarily unreachable. The right design considers failure domains, maximum unhealthy percentages, node startup time, and whether the provider can actually create replacements during the incident.

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineHealthCheck
metadata:
  name: worker-health
  namespace: default
spec:
  clusterName: my-workload
  selector:
    matchLabels:
      cluster.x-k8s.io/deployment-name: my-workload-md-0
  unhealthyConditions:
    - type: Ready
      status: "False"
      timeout: 300s
    - type: Ready
      status: Unknown
      timeout: 300s
  maxUnhealthy: 40%
  nodeStartupTimeout: 10m
```

This example is intentionally moderate rather than heroic. It allows remediation but avoids replacing everything at once. The correct values depend on workload tolerance, provider speed, cluster size, and failure-domain layout. For a small development cluster, faster replacement may be acceptable. For a large production cluster under a regional infrastructure incident, conservative thresholds may prevent additional disruption.

Upgrades require the same discipline. CAPI makes rolling replacement easier, but it does not eliminate Kubernetes version-skew policy, add-on compatibility, storage driver compatibility, workload disruption, or provider image readiness. A safe upgrade plan starts with a test cluster using the same ClusterClass or templates, validates add-ons, checks workload PodDisruptionBudgets, upgrades control planes before workers, and watches conditions during rollout. Automation makes upgrades repeatable; it does not make compatibility optional.

| Operation | Desired-State Change | Main Risk | Senior-Level Guardrail |
|---|---|---|---|
| Create cluster | Add a `Cluster` or topology object | Wrong network, image, or credentials | Preflight validation and reviewed templates |
| Scale workers | Change `MachineDeployment.spec.replicas` | Capacity, quota, or workload imbalance | Quota checks and autoscaling policy alignment |
| Upgrade control plane | Change control-plane version | etcd health or API disruption | Test cluster, backups, skew checks, staged rollout |
| Upgrade workers | Change worker template version | Workload eviction and add-on compatibility | PDB review, canary pool, observability |
| Remediate machine | MachineHealthCheck replaces nodes | Over-remediation during partial outage | Conservative thresholds and failure-domain awareness |
| Delete cluster | Delete `Cluster` desired state | Accidental infrastructure teardown | Manual approval, no automatic prune, backups |

The most common senior trade-off is where to draw the line between self-service and platform control. Full self-service can let teams create clusters quickly, but it can also create cost, security, and reliability problems if every team chooses its own versions and topology. Full central control can preserve standards but create a ticket queue. ClusterClass, policy engines, GitOps review, and admission controls let the platform team expose safe choices instead of unlimited choices.

CAPI also competes and cooperates with managed Kubernetes services. A team using EKS, AKS, or GKE may not need CAPI to create every cluster if the managed service lifecycle already satisfies their needs. However, CAPI can still be attractive for hybrid fleets, on-premises environments, consistent APIs across providers, or cases where the platform team wants Kubernetes-native lifecycle control. The decision should be based on operational requirements, not tool enthusiasm.

Rancher, Gardener, and vendor platforms solve overlapping fleet-management problems with different abstractions. Some use CAPI underneath. Others provide their own lifecycle model, UI, policy, or multi-cluster management layer. A platform engineer should evaluate whether the team needs a low-level Kubernetes-native lifecycle API, a higher-level product experience, or both. CAPI is a strong foundation, but it is not automatically the entire platform.

Finally, production CAPI requires clear incident ownership. If a cluster fails to provision because a subnet is exhausted, does the platform team own it, or does the networking team? If a provider controller cannot authenticate to the cloud API, who rotates credentials? If a workload cluster has no CNI, is that a CAPI failure or an add-on pipeline failure? These questions should be answered before the first production outage, not during it.

## Did You Know?

- Cluster API is developed under Kubernetes SIG Cluster Lifecycle, the same general community area responsible for lifecycle tooling such as kubeadm, which is why the project emphasizes Kubernetes-style reconciliation rather than one-time provisioning scripts.
- CAPD, the Docker infrastructure provider, creates local Docker-container-backed machines for development and learning, but it is deliberately not a production infrastructure provider.
- ClusterClass lets a platform team expose a smaller cluster request interface while hiding provider templates, bootstrap templates, and rollout mechanics behind a reviewed topology.
- `clusterctl move` can help migrate CAPI management objects between management clusters, but it should be practiced and documented before it is needed in a real recovery scenario.

## Common Mistakes

| Mistake | Why It Hurts | Better Practice |
|---|---|---|
| Running application workloads on the management cluster | Application incidents can consume resources or damage the control plane that manages every workload cluster | Keep the management cluster dedicated to lifecycle controllers, GitOps, policy, and required platform tooling |
| Treating CAPD as a production provider | Docker containers do not provide production-grade infrastructure semantics, availability, or isolation for real workloads | Use CAPD for local learning and provider development, then choose CAPA, CAPZ, CAPV, CAPM3, CAPO, or another production provider |
| Forgetting the CNI after cluster creation | Machines may exist and nodes may join, but Pods cannot run correctly without cluster networking | Install networking through a controlled add-on lifecycle such as GitOps, ClusterResourceSet where suitable, or a platform add-on pipeline |
| Enabling automatic GitOps pruning for cluster definitions | A bad commit or path removal can cascade into workload cluster deletion and infrastructure teardown | Disable automatic prune for cluster fleet applications and require explicit approval for deletion workflows |
| Ignoring management-cluster backup and move procedures | Losing the management cluster can leave workload clusters running but unmanaged through the desired-state API | Back up etcd and CAPI resources, test restore, and document `clusterctl move` for planned migrations |
| Upgrading versions without validating add-ons and images | CAPI can roll machines, but incompatible CNI, CSI, ingress, or machine images can break the new version | Test the same templates in a staging cluster and validate provider support, images, and add-on compatibility before production |
| Setting aggressive MachineHealthCheck thresholds | Temporary network or provider issues can trigger unnecessary mass replacement and increase disruption | Tune `maxUnhealthy`, timeouts, and failure-domain strategy based on cluster size, provider speed, and workload tolerance |
| Copying provider manifests per team without templates | Small differences accumulate into version, image, network, and security drift across the fleet | Use ClusterClass or controlled templates so teams request supported shapes instead of editing deep provider YAML |

## Quiz

**Q1: Your team applies a CAPD workload cluster manifest. After several minutes, `k get machines` in the management cluster shows one control-plane machine and two worker machines, but `k --kubeconfig workload.kubeconfig get nodes` shows nodes stuck as `NotReady`. What should you check first, and why?**

<details>
<summary>Show Answer</summary>

Check the workload cluster's node conditions and system Pods for networking symptoms, then verify whether a CNI has been installed. The machines already exist, so infrastructure provisioning is probably not the first suspect. A bare workload cluster can form enough for nodes to join while still lacking the networking add-on required for Pods and node readiness. This is a post-create add-on lifecycle problem unless the node conditions point back to bootstrap or kubelet failure.
</details>

**Q2: A platform team wants to let application teams request production clusters through pull requests. The first proposal gives every team full access to edit provider-specific machine templates. What design would you recommend instead, and what risk does it reduce?**

<details>
<summary>Show Answer</summary>

Recommend exposing reviewed ClusterClass options or controlled templates with a limited set of variables, such as version, worker count, region, and approved machine classes. This preserves self-service while reducing drift in images, networks, bootstrap settings, and security posture. Full access to deep provider templates makes every cluster a special case and makes upgrades or incident response harder across the fleet.
</details>

**Q3: During a production upgrade, the control plane rolls successfully, but worker replacement stalls because old nodes cannot drain. Which evidence would you gather before changing CAPI settings, and why?**

<details>
<summary>Show Answer</summary>

Inspect the worker `MachineDeployment` conditions, individual `Machine` events, workload Pods on the old nodes, and PodDisruptionBudgets that may block eviction. Also check whether the new machines are ready and whether add-ons are healthy on the upgraded version. Changing rollout or health settings without understanding drain blockers can hide the real workload availability issue and may create unnecessary disruption.
</details>

**Q4: A security reviewer objects that CAPI stores fleet desired state in the management cluster's etcd. Your team currently has no tested backup process for that cluster. What operational change should block production adoption until it is solved?**

<details>
<summary>Show Answer</summary>

Establish and test management-cluster backup and recovery, including CAPI resources and any required secrets or provider credentials. The team should also document management-cluster migration with `clusterctl move` where appropriate. Without a recovery path, losing the management cluster can leave workload clusters running but difficult to upgrade, repair, or delete declaratively.
</details>

**Q5: A team asks whether Terraform should be removed now that CAPI can create clusters. Their cloud foundation includes accounts, VPCs, DNS zones, and shared IAM boundaries managed by Terraform. How would you divide ownership between the tools?**

<details>
<summary>Show Answer</summary>

Keep Terraform or an equivalent foundation tool for broad infrastructure foundations such as accounts, networks, DNS, and IAM boundaries. Use CAPI for Kubernetes cluster lifecycle inside those prepared foundations. This division lets each tool manage the lifecycle it understands best: Terraform for general infrastructure composition and CAPI for continuous Kubernetes cluster reconciliation, rollout, and remediation.
</details>

**Q6: A MachineHealthCheck replaces several workers during a short provider-network outage, increasing customer impact. What was likely wrong with the remediation design, and how would you adjust it?**

<details>
<summary>Show Answer</summary>

The health check was probably too aggressive for the cluster size, failure-domain layout, or provider behavior. Adjust timeouts, `maxUnhealthy`, and remediation assumptions so temporary partitions do not trigger broad replacement. Also verify whether the provider can create replacements during the same class of outage. Remediation should improve recovery under realistic failure modes, not amplify an external incident.
</details>

**Q7: An engineer deletes a cluster YAML file from the Git repository, and Argo CD is configured with automatic pruning for the fleet application. What could happen, and what control should have prevented it?**

<details>
<summary>Show Answer</summary>

Argo CD could delete the corresponding `Cluster` object from the management cluster, causing CAPI finalizers and provider controllers to tear down workload-cluster machines and infrastructure. Fleet applications should normally disable automatic prune and require an explicit deletion workflow with review and approval. Cluster deletion has a much larger blast radius than ordinary application manifest pruning.
</details>

**Q8: A vSphere CAPI pilot succeeds in development, but production clusters built from different VM templates behave inconsistently after scaling. Some nodes use different kubelet flags and container runtime settings. What should the platform team fix before expanding the rollout?**

<details>
<summary>Show Answer</summary>

The team should standardize and version the machine image contract before scaling CAPI usage. CAPI can reliably create more machines, but it cannot make inconsistent base images behave consistently. Golden images, runtime configuration, hardening standards, and provider templates should be controlled so automation reproduces a known-good node shape.
</details>

## Hands-On Exercise

**Scenario:** Your platform team is evaluating Cluster API for a standardized internal cluster service. You need to prove that you can create a local workload cluster, debug its lifecycle through CAPI resources, scale it, and write a short production-readiness recommendation.

1. Create a local management cluster with `kind` named `capi-management`, then initialize CAPI with the Docker infrastructure provider.
2. Verify that the CAPI core, Docker infrastructure, kubeadm bootstrap, and kubeadm control-plane controller Deployments are available before creating a workload cluster.
3. Generate a workload cluster named `dev-cluster` with one control-plane machine and one worker machine, using a Kubernetes v1.35-compatible version supported by your installed provider.
4. Apply the generated manifest, then use `clusterctl describe cluster dev-cluster` and `k get clusters,machinedeployments,machines` to trace lifecycle progress from the management cluster.
5. Fetch the workload cluster kubeconfig, inspect node readiness, and install a CNI if the nodes are not ready because networking is missing.
6. Scale the worker `MachineDeployment` from one worker to three workers, then observe the order in which `Machine` objects and workload-cluster `Node` objects appear.
7. Write a short upgrade plan for the cluster that lists version compatibility, image availability, add-on compatibility, disruption controls, and rollback or recovery assumptions.
8. Delete `dev-cluster`, verify that machines disappear from the management cluster, and then delete the local management cluster.

**Success Criteria:**

- [ ] The management cluster exists and all required provider controller Deployments become available before workload cluster creation.
- [ ] The generated workload cluster manifest is inspected with `--dry-run=client` before being applied.
- [ ] `clusterctl describe cluster dev-cluster` is used to explain at least two lifecycle phases visible through CAPI conditions.
- [ ] The workload cluster kubeconfig is retrieved and node readiness is verified from the workload cluster's perspective.
- [ ] A CNI is installed if node conditions show that networking is the blocker for readiness.
- [ ] The worker pool is scaled to three workers by patching the `MachineDeployment`, not by manually creating nodes.
- [ ] The learner records whether `Machine` objects or workload-cluster `Node` objects appear first during scale-out and explains why.
- [ ] The cleanup removes the workload cluster and the local management cluster without leaving CAPI lab resources running.

**Production Design Challenge:**

Write a one-page recommendation for how your organization should adopt CAPI beyond the lab. Include the intended management-cluster ownership model, provider choice, base-image strategy, GitOps review process, deletion guardrails, backup plan, MachineHealthCheck stance, and the boundary between Terraform foundations and CAPI cluster lifecycle. Your recommendation should be specific enough that another platform engineer could challenge the trade-offs, not just agree with general statements.

**Next Module**: [Module 7.1: Backstage](../module-7.1-backstage/) - Build an Internal Developer Portal to give developers self-service access to platform capabilities.
