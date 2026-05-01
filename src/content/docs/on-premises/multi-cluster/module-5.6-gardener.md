---
title: "Module 5.6: Gardener — Open-Source Kubernetes-as-a-Service at Scale"
description: "Design and operate Kubernetes cluster fleets at SAP scale using Gardener's Gardens/Seeds/Shoots architecture, provider extensions, and cluster lifecycle automation."
slug: on-premises/multi-cluster/module-5.6-gardener
sidebar:
  order: 56
---

# Module 5.6: Gardener — Open-Source Kubernetes-as-a-Service at Scale

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: K8s Basics (CKA-level understanding), [Module 5.3: Cluster API on Bare Metal](../module-5.3-cluster-api-bare-metal/), basic understanding of multi-cluster concepts

For command examples, this module uses `k` as a short alias for `kubectl`.
Create it once in your shell with `alias k=kubectl` before running the hands-on work.

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Design** a Gardener landscape that separates Garden, Seed, and Shoot responsibilities for a multi-tenant cluster fleet.
2. **Evaluate** when Gardener is a better fit than Cluster API or Crossplane for an internal Kubernetes-as-a-Service platform.
3. **Implement** a declarative Shoot lifecycle using provider, Kubernetes version, networking, worker, maintenance, and deletion settings.
4. **Diagnose** failed Shoot reconciliations by tracing Gardenlet, extension controllers, etcd-druid, and Shoot status conditions.
5. **Compare** Gardener's extension, quota, dashboard, and operational models against a hand-built kubeadm fleet.

---

## Why This Module Matters

A large enterprise platform team starts with good intentions.
Each product group wants Kubernetes, and the central infrastructure team wants to help without blocking delivery.
The first few clusters are built by careful engineers with kubeadm, Terraform, and a long checklist.
One cluster runs payments experiments, another runs a supply-chain service, and another hosts a partner API.
Each team gets root-like power over its own cluster because that feels like autonomy.
At cluster number six, this still feels manageable.
At cluster number sixteen, upgrade planning becomes a spreadsheet.
At cluster number twenty-eight, an expired certificate takes one production environment offline for hours.
At cluster number sixty, the platform team can no longer answer a basic question quickly: which clusters are behind on patch versions, which nodes are running unsupported images, and which teams own them?

The direct financial pain usually appears during day-2 operations, not during the first install.
One outage begins when a product team postpones a minor Kubernetes upgrade because its cluster has a custom kubeadm flag no other cluster uses.
Another begins when a network plugin is patched manually in one region but not in another.
A third begins when a cloud credential rotates in the infrastructure account but no one updates the matching cluster controller secret.
The bill is paid in engineer time, incident fatigue, customer credits, and delayed product work.
The root problem is not that kubeadm is bad.
The root problem is that hand-operated clusters turn into unique pets faster than people expect.

Gardener was built for the point where "we can script this" stops being enough.
SAP has publicly described running Gardener for thousands of conformant Kubernetes clusters across major hyperscalers, private clouds, and acquired infrastructure.
Recent public talks and community material describe production-scale fleets that reach the order of 10,000+ Shoot clusters and 2+ billion Kubernetes API calls per day.
At that scale, the platform problem is no longer "how do I create a cluster?"
The problem becomes "how do I offer cluster creation, upgrades, recovery, observability, quota, and credential rotation as a repeatable product?"
Gardener's answer is to make Kubernetes clusters themselves into Kubernetes-managed resources.

This module teaches Gardener as a control-plane operating model, not as a logo on a diagram.
You will see why a centralized management plane becomes necessary above roughly twenty clusters, how Gardens, Seeds, and Shoots divide responsibility, and how provider extensions keep Gardener from hard-coding every infrastructure provider into its core.
You will also run through a complete local lifecycle using the `gardener-local` provider on kind.
The end goal is practical: provision, scale, upgrade, rotate credentials for, and delete a Shoot through the Gardener API.

---

## 1. The Fleet Problem Gardener Solves

Most Kubernetes teams begin with a single-cluster mental model.
The control plane is installed on a few machines, nodes join it, workloads land on nodes, and operators patch the cluster in place.
That model is useful while a team is learning Kubernetes because it keeps all moving parts visible.
It breaks down when a platform team needs to offer many clusters to many teams.
The problem shifts from building a cluster to managing a fleet.

A fleet has different failure modes than a single cluster.
One cluster can be inspected directly.
One hundred clusters need inventory, policy, upgrade automation, and a consistent status model.
One cluster can tolerate a manual exception.
One hundred clusters turn manual exceptions into permanent entropy.
One cluster can be upgraded by an expert.
One thousand clusters need the upgrade process encoded in controllers that can retry, pause, roll forward, and explain progress.

The "snowflake cluster" anti-pattern appears when each team modifies its cluster by hand.
One team pins a network plugin version because of a one-time bug.
Another team changes admission settings during an incident and forgets to document the reason.
Another team installs a custom machine image outside the approved image catalog.
Each change may be locally sensible.
Together, the fleet becomes impossible to reason about.
The next upgrade is no longer a planned operation; it is a negotiation with history.

Gardener treats this as a product design problem.
End users should be able to request a conformant Kubernetes cluster without becoming experts in etcd backup, cloud controller configuration, node image rollout, or control-plane sizing.
Platform operators should be able to define the menu of supported regions, machine types, operating systems, Kubernetes versions, and network plugins.
Controllers should reconcile the desired state continuously, the same way Kubernetes reconciles Deployments and StatefulSets.
That is the core idea behind Gardener.

Gardener is not merely a cluster installer.
It is an open-source Kubernetes-as-a-Service control plane.
It creates clusters, updates clusters, monitors cluster health, manages cluster credentials, handles backups, and deletes infrastructure when a cluster is no longer needed.
It offers this through Kubernetes APIs rather than a separate ticketing workflow.
The main user-facing object is a `Shoot`.
A Shoot is a tenant Kubernetes cluster described declaratively.

The reason a centralized control plane becomes necessary around twenty clusters is coordination cost.
Below that level, a small team can often remember who owns each cluster and when the next upgrade is due.
Above that level, humans stop being a reliable database.
You need a place where desired state, ownership, quota, provider policy, and status are all visible.
Gardener's Garden cluster becomes that management hub.
It is the source of truth for Shoot resources, Projects, CloudProfiles, quotas, and operational status.

Gardener's design also recognizes that cluster control planes are just workloads.
An API server is a process.
A scheduler is a process.
A controller manager is a process.
Etcd is a stateful service.
If those components can run as pods in another Kubernetes cluster, a platform team can use Kubernetes scheduling, health checks, resource requests, autoscaling, network policy, and observability to manage them.
This is the idea behind hosted control planes.
Gardener applies it at fleet scale.

The hosted-control-plane model changes the cost shape of a cluster fleet.
Traditional self-managed clusters often dedicate control-plane machines to every tenant cluster.
That can waste resources when clusters are small or idle.
Gardener places many Shoot control planes into Seed clusters as regular pods.
Those pods can share Seed capacity while tenant workloads continue to run on separate Shoot worker nodes.
The tenant still gets a Kubernetes API endpoint and a kubeconfig.
The control plane simply lives somewhere more efficient and more operable.

Pause and predict: what do you think happens if a product team can create clusters quickly but there is no central policy for allowed Kubernetes versions?
The likely result is not innovation; it is version drift.
Some teams will lag because upgrades are inconvenient.
Other teams will jump early because a new feature looks attractive.
The platform team then supports too many combinations of API behavior, node images, and add-ons.
Gardener prevents that drift by letting operators publish supported versions through CloudProfiles and maintenance policies.

The important tradeoff is that Gardener is opinionated.
It expects a platform team to run a real management service.
It expects operators to define supported infrastructure and lifecycle rules.
It expects tenant clusters to be reconciled by Gardener rather than hand-edited into unique shapes.
That is exactly why it works for Kubernetes-as-a-Service.
The platform team is not just giving users raw automation.
It is giving them a managed product with boundaries.

### A Fleet Mental Model

Think of a small restaurant kitchen.
One chef can remember every order for a few tables.
At peak service, memory is not a system.
The kitchen needs tickets, stations, inventory, timing, and expediters.
Gardener plays the expeditor role for Kubernetes clusters.
It does not cook every dish itself.
It coordinates the stations that know how to provision infrastructure, bootstrap machines, run control planes, issue credentials, and report health.

The lesson for on-premises and hybrid platforms is direct.
If your organization needs clusters across OpenStack, VMware, Equinix Metal, or bare-metal-backed environments, you should not let every team assemble its own lifecycle stack.
You should decide whether you are building a framework, a generic infrastructure API, or a full Kubernetes-as-a-Service product.
Gardener is aimed at the third option.
It is designed for platform teams that want to offer clusters as a standardized service.

---

## 2. Architecture: Gardens, Seeds, and Shoots

Gardener uses botanical names, but the architecture is concrete.
There are three primary tiers.
The Garden cluster is the management hub.
Seed clusters are execution environments.
Shoot clusters are the tenant Kubernetes clusters that users consume.
Once those roles are clear, the rest of the system becomes much easier to reason about.

The Garden cluster stores the desired state of the fleet.
It hosts the Gardener API server, Gardener controller manager, scheduler, admission components, and CRDs such as `Shoot`, `Seed`, `Project`, `CloudProfile`, and `Quota`.
When a user creates a Shoot manifest, the object is created in the Garden cluster.
The Garden cluster does not usually run tenant application workloads.
It is the management brain of the landscape.

A Seed cluster hosts Shoot control planes.
It runs a component called Gardenlet.
Gardenlet is the per-Seed agent that watches the Garden for Shoots assigned to that Seed and reconciles the required control-plane resources.
A Seed can host the control planes for many Shoots.
In large landscapes, a Seed is commonly aligned to a provider, region, or failure domain so the control plane is close to the tenant cluster's worker infrastructure.
That placement reduces latency and makes failure boundaries easier to discuss.

A Shoot cluster is the tenant-facing Kubernetes cluster.
The user receives a kubeconfig for the Shoot.
The user's workloads run on Shoot worker nodes.
The Shoot API server, controller manager, scheduler, etcd, autoscaler, and supporting system components are not usually running on those worker nodes.
They run as pods in the Seed.
This is the most important architectural distinction in Gardener.

```text
+------------------------------ Garden Cluster ------------------------------+
| Gardener API server                                                        |
| Gardener controller manager                                                |
| Scheduler, admission, Projects, CloudProfiles, Quotas                      |
|                                                                            |
|  Shoot CRs: dev-a, prod-a, data-lab, partner-api                           |
+---------------------------+------------------------------------------------+
                            |
                            | Gardenlet watches assigned Shoots
                            v
+------------------------------ Seed Cluster --------------------------------+
| Namespace shoot--team-a--prod-a                                            |
|   kube-apiserver pod   kube-scheduler pod   controller-manager pod         |
|   etcd managed by etcd-druid   vpn-seed   monitoring   logging             |
|                                                                            |
| Namespace shoot--team-b--data-lab                                          |
|   another hosted control plane, also running as regular pods               |
+---------------------------+------------------------------------------------+
                            |
                            | API endpoint and reconciliation target
                            v
+------------------------------ Shoot Cluster -------------------------------+
| Tenant worker nodes                                                        |
| Application pods                                                           |
| DaemonSets, Services, Ingresses, PersistentVolumes                         |
| Users interact here through the Shoot kubeconfig                           |
+---------------------------------------------------------------------------+
```

The diagram shows why Gardener can achieve high density.
Control planes become pods.
Pods can be scheduled, restarted, monitored, and resourced by Kubernetes.
Instead of dedicating three virtual machines to every control plane, the platform can bin-pack many control planes into Seed clusters.
This does not remove the need for capacity planning.
It moves capacity planning to the Seed tier, where operators can manage it centrally.

Control-plane-as-pods also simplifies day-2 operations.
If a kube-apiserver needs a new image, Gardenlet can update a Deployment in the Seed namespace.
If etcd needs backup configuration, etcd-druid can reconcile it as Kubernetes resources.
If monitoring needs a dashboard, the Seed monitoring stack can expose it next to the control-plane namespace.
The operational surface becomes Kubernetes-native.

The Garden and Seed relationship is intentionally asymmetric.
The Garden holds the desired state and policy.
The Seed performs the work for assigned Shoots.
If a Seed becomes unhealthy, the Garden can show that Seed's conditions and prevent new Shoots from being scheduled there.
If a Shoot reconciliation fails, the status is reflected back through the Shoot object.
This creates a single fleet view while keeping execution distributed.

Shoots are isolated by namespaces in the Seed.
A typical Seed namespace name encodes the Project and Shoot name, such as `shoot--team-a--prod-a`.
Inside that namespace, the platform will find Deployments, StatefulSets, Secrets, ConfigMaps, Services, and monitoring resources for that Shoot's control plane.
This is useful during incident response because operators can move from a tenant-facing problem to the exact Seed namespace that hosts the control-plane components.

The user does not need to target the Seed for normal work.
The user targets the Shoot API endpoint.
Gardener publishes connection details through Shoot status and kubeconfig mechanisms.
The `.status.advertisedAddresses` field is important because it tells clients which API server addresses are advertised for the Shoot.
In many landscapes, this includes an external endpoint, an internal endpoint, or endpoints shaped by exposure settings.
When a kubeconfig is issued, it uses those advertised addresses to reach the right API server.

The Garden cluster should be treated as critical infrastructure.
If the Garden is unavailable, existing Shoot clusters may continue running, but lifecycle operations are impaired.
Users may not be able to create new Shoots, trigger maintenance, or inspect current fleet status through Gardener.
The Garden therefore deserves high availability, backup, access control, and change discipline.
It is not a casual admin cluster.

Seed clusters also need strict operational boundaries.
They host many tenant control planes.
A bad change in a Seed can affect many Shoots at once.
This is why operators scale Seeds horizontally rather than placing every Shoot in one giant Seed.
Multiple Seeds create failure boundaries and make capacity expansion less dramatic.
They also let a platform align Shoots with provider regions, data-sovereignty requirements, or network constraints.

### Worked Example: Finding a Shoot's Control Plane

Suppose a tenant says their API requests are timing out.
The tenant can still see nodes with a stale kubeconfig, but new `k get pods` calls fail intermittently.
The platform operator should not start by SSHing into every worker node.
The operator should locate the Shoot in the Garden, identify its Seed, and inspect the Seed namespace that hosts the control plane.
That path matches the architecture.

```bash
alias k=kubectl

k -n garden-team-a get shoot prod-a -o wide
k -n garden-team-a get shoot prod-a -o jsonpath='{.status.seedName}{"\n"}'
k -n shoot--team-a--prod-a get pods
k -n shoot--team-a--prod-a get deploy,sts,svc
```

The first command asks the Garden about the tenant cluster.
The second command finds the Seed assignment.
The third and fourth commands target the Seed namespace, assuming your kubeconfig now points to that Seed.
This shift from Garden view to Seed execution view is a common operator motion in Gardener.

### War Story: The Control Plane Was Healthy, the Endpoint Was Not

A platform team once spent an incident looking at worker nodes because users reported that a Shoot was unreachable.
The nodes were healthy, CoreDNS was fine, and application pods were running.
The real problem was in the Seed namespace: the control-plane Service endpoint had changed after an ingress-controller rollout, but a DNS record had not reconciled cleanly.
Because the team treated the Shoot like a normal self-hosted cluster, they inspected the wrong layer first.
After they adopted a Garden-to-Seed-to-Shoot checklist, the same class of incident became much faster to diagnose.

---

## 3. Extensibility Without Turning Core Into a Cloud Catalog

Gardener must work across many infrastructure providers.
The list includes AWS, GCP, Azure, OpenStack, Equinix Metal, VMware vSphere, and other environments.
It also needs operating system choices such as Garden Linux, Ubuntu, and Flatcar.
It needs networking choices such as Calico, Cilium, and Weave.
If all of that logic lived inside the Gardener core repository, the project would become a tightly coupled cloud catalog.
Every provider bug would require core changes.
Every provider release would risk the central control plane.
Gardener avoids this with an extension model.

The extension framework uses Kubernetes admission webhooks, CRDs, and controllers.
Gardener core stays focused on the lifecycle model.
Provider extensions reconcile provider-specific resources.
An AWS extension knows how to create AWS infrastructure.
An OpenStack extension knows how to map a Shoot's desired state to OpenStack networks, routers, servers, and load balancers.
A vSphere extension knows the vSphere concepts it must manage.
The core does not need to know those details.

This is similar to the way Kubernetes itself delegates storage to CSI drivers and networking to CNI plugins.
The central API defines the shape of the desired state.
Specialized controllers handle the provider-specific action.
That division is not just clean architecture.
It is a scaling mechanism for the contributor community.
Provider experts can move at provider speed without forcing every provider concern into Gardener core.

Gardener extension resources commonly live in the `extensions.gardener.cloud` API group.
During Shoot reconciliation, Gardenlet creates extension resources such as `Infrastructure`, `Worker`, `ControlPlane`, `Network`, `DNSRecord`, `BackupBucket`, and others as needed.
The relevant extension controller watches those resources and reconciles the external system.
Status flows back through those resources and then into the Shoot status.
This gives operators a layered debugging path.

The admission webhook piece matters because provider-specific validation often cannot be expressed in the generic Shoot schema alone.
For example, a provider may support only certain machine families in a region.
Another provider may require a specific network shape for dual-stack clusters.
An OS extension may validate image names and versions.
A network extension may reject incompatible pod CIDR settings.
Admission webhooks catch these mistakes early, before a long reconciliation fails halfway through infrastructure creation.

The CloudProfile connects platform policy to extension behavior.
Operators publish allowed machine types, regions, zones, Kubernetes versions, volume types, and machine images through CloudProfiles.
Tenant Shoot manifests reference those choices.
This prevents every team from inventing its own machine catalog.
It also lets the platform retire versions in a controlled way.
The CloudProfile is the menu; the Shoot is the order.

### Conceptual Outline: Writing a Minimal Provider Extension

A minimal provider extension starts with a narrow contract between Gardener and provider-specific code.
You define provider-specific configuration types, register them with Kubernetes schemes, and implement controllers for the extension resources your provider supports.
You add admission webhooks to validate provider configuration.
You publish controller images and Helm charts so the extension can be installed into a Seed.
Then you test reconciliation from a small Shoot manifest.

At a conceptual level, the extension has these responsibilities:

1. Validate provider-specific Shoot configuration.
2. Reconcile infrastructure resources such as networks, subnets, routes, security rules, and load balancers.
3. Reconcile worker machines or delegate to a machine-controller integration.
4. Report status in a form Gardenlet can use.
5. Clean up external resources during Shoot deletion.

The following YAML is not a full provider extension.
It shows the kind of provider-specific configuration that would be embedded under a Shoot or CloudProfile for an extension to consume.

```yaml
apiVersion: core.gardener.cloud/v1beta1
kind: Shoot
metadata:
  name: local
  namespace: garden-local
spec:
  cloudProfile:
    name: local
  region: local
  provider:
    type: local
    infrastructureConfig:
      apiVersion: local.provider.extensions.gardener.cloud/v1alpha1
      kind: InfrastructureConfig
      networks:
        workers: 10.250.0.0/16
    controlPlaneConfig:
      apiVersion: local.provider.extensions.gardener.cloud/v1alpha1
      kind: ControlPlaneConfig
  kubernetes:
    version: 1.35.2
```

The provider `type` is the handoff point.
Gardener core can recognize that this Shoot wants a `local` provider.
The local provider extension understands the `InfrastructureConfig` and `ControlPlaneConfig` objects.
That is how Gardener stays IaaS-agnostic while still supporting real provider behavior.

### Network and OS Extensions

Network extensions follow the same principle.
A Shoot can select a networking type such as `calico` or `cilium`.
The selected extension reconciles the network plugin and provider-specific network details.
This keeps networking variation out of the core lifecycle controller.
It also lets a platform team standardize network plugins by CloudProfile and policy.

OS extensions let operators support approved node operating systems.
Garden Linux is common in Gardener landscapes because it is optimized for cloud-native infrastructure use.
Ubuntu and Flatcar are also typical options.
The important point is not which image is fashionable.
The important point is that machine image choices are managed as platform policy.
Users should not paste arbitrary image IDs into every Shoot manifest.

### War Story: Provider Logic in the Wrong Place

A team building its own multi-cluster platform once placed AWS, OpenStack, and vSphere logic inside one controller.
The controller grew provider flags, conditional code, custom retries, and provider-specific cleanup paths.
Every provider release required retesting the whole controller.
When the vSphere API returned a new transient error shape, AWS cluster creation was delayed because the shared controller release was frozen.
Gardener's extension model exists to avoid that kind of coupling.
Provider-specific behavior belongs in provider-specific controllers.

Before running this in a real landscape, what output would you expect if a Shoot requests a machine type that the CloudProfile does not allow?
The best outcome is an early admission or validation error.
The worst outcome is a half-created cloud environment that fails after resources already exist.
Gardener's admission and extension model is designed to move that feedback earlier.

---

## 4. Cluster Lifecycle: Provisioning, Day-2 Operations, and Deprovisioning

The central pedagogical fork in this module is the Shoot lifecycle.
If you can read a Shoot manifest and predict the reconciliation path, Gardener stops feeling mysterious.
If you cannot, Gardener looks like a large collection of controllers with botanical names.
We will walk the manifest from intent to running cluster, then through scaling, upgrading, credential rotation, and deletion.

A Shoot manifest expresses a tenant cluster as desired state.
It defines the provider, region, Kubernetes version, networking, workers, maintenance behavior, and optional settings.
The user creates it in a Project namespace in the Garden cluster.
Gardener validates the request.
The scheduler assigns the Shoot to a Seed that can host it.
Gardenlet on that Seed reconciles the cluster.

Here is a complete illustrative Shoot manifest for the local provider.
The exact local example in the Gardener repository can change, so treat this as a teaching manifest.
The hands-on section uses the repository-provided example.

```yaml
apiVersion: core.gardener.cloud/v1beta1
kind: Shoot
metadata:
  name: local
  namespace: garden-local
spec:
  cloudProfile:
    name: local
  secretBindingName: local
  region: local
  purpose: evaluation
  provider:
    type: local
    workers:
      - name: worker
        minimum: 1
        maximum: 2
        maxSurge: 1
        maxUnavailable: 0
        machine:
          type: local
          image:
            name: gardenlinux
            version: 1.35.0
          architecture: amd64
        volume:
          type: default
          size: 20Gi
        zones:
          - "0"
  kubernetes:
    version: 1.35.2
    kubeAPIServer:
      requests:
        maxMutatingInflight: 200
        maxNonMutatingInflight: 400
  networking:
    type: calico
    pods: 10.244.0.0/16
    services: 10.96.0.0/12
    nodes: 10.250.0.0/16
  maintenance:
    timeWindow:
      begin: 030000+0000
      end: 040000+0000
    autoUpdate:
      kubernetesVersion: true
      machineImageVersion: true
  hibernation:
    enabled: false
```

The `spec.provider` section tells Gardener which provider extension must participate.
For a real AWS Shoot, `type` would be `aws`.
For OpenStack, it would be `openstack`.
For vSphere, it would be `vsphere`.
The provider section also contains worker pool definitions.
Worker pools describe the desired machine count range, machine type, machine image, volume shape, zones, and rollout behavior.

The `spec.kubernetes.version` field is the desired Kubernetes version for the Shoot.
In this module, examples use Kubernetes 1.35 or newer.
In a production landscape, the version must be allowed by the CloudProfile.
This is a policy gate, not just a convenience.
It prevents tenants from creating versions the platform does not support.

The `spec.networking` section defines pod, service, and node CIDR ranges plus the network plugin type.
These ranges are not cosmetic.
Overlapping CIDRs can break VPN connectivity, service routing, and hybrid network integration.
On-premises teams should treat these ranges as part of the platform IP address plan.
The network extension and provider extension may both validate pieces of this section.

The `spec.workers` or provider worker entries determine the data-plane shape.
Gardener reconciles worker machines through provider integration and machine controllers.
The `minimum` and `maximum` fields define autoscaling boundaries.
The `maxSurge` and `maxUnavailable` fields define rollout safety.
For production worker pools, `maxUnavailable: 0` is often used when capacity allows because it avoids planned node loss during rolling updates.

The `spec.maintenance.autoUpdate.kubernetesVersion: true` setting allows Gardener to perform Kubernetes version updates during the maintenance window when a newer supported patch or configured target is available.
This is one of the clearest differences between Gardener and a simple provisioning script.
The cluster is not just created and abandoned.
It remains under lifecycle management.
The maintenance window gives tenants predictability while preserving platform control.

When the Shoot is created, Gardenlet starts reconciliation.
It creates a namespace for the Shoot control plane in the Seed.
It asks provider extensions to create infrastructure.
It creates or updates control-plane Deployments and StatefulSets.
It configures etcd through etcd-druid.
It prepares networking, DNS, VPN, monitoring, logging, and worker resources.
Each step updates status and conditions so operators can see where the process is stuck.

The status path is as important as the create path.
Gardener surfaces high-level Shoot conditions such as API server availability, control-plane health, node health, system component health, and observability component health.
Operators should read those before diving into logs.
Conditions tell you which part of the reconciliation graph is failing.
Logs tell you why that part is failing.

### Kubeconfig Issuance and Advertised Addresses

Users need a kubeconfig to access the Shoot.
Gardener supports short-lived admin kubeconfig access through the Shoot API and related tooling.
The Shoot status contains advertised addresses that identify how the Shoot API server should be reached.
These addresses may differ by landscape configuration.
A private on-premises landscape might advertise internal addresses.
A public cloud landscape might advertise an external endpoint.
Hybrid setups may expose both depending on policy.

The important operational point is that a kubeconfig is not just a static file someone uploads once.
It is derived from Gardener-managed cluster state and credential policy.
If advertised addresses change, clients may need a fresh kubeconfig.
If credentials rotate, old clients may stop working.
That is desirable when credentials are revoked intentionally.

```bash
k -n garden-local get shoot local -o jsonpath='{.status.advertisedAddresses}{"\n"}'
k -n garden-local get shoot local -o jsonpath='{.status.conditions}{"\n"}'
```

These commands inspect the high-level state from the Garden.
They are often more useful than immediately reading pod logs because they summarize the reconciled result.
If the API server is unavailable, the advertised address and API server condition narrow the search quickly.

### Etcd Management Through etcd-druid

Every Kubernetes cluster depends on etcd.
At fleet scale, etcd cannot be an afterthought.
Gardener uses etcd-druid to manage etcd clusters for Shoots.
etcd-druid reconciles etcd resources, backup settings, restore behavior, and operational details around etcd lifecycle.
This lets Gardenlet delegate a complex stateful subsystem to a controller designed for it.

Backups usually target object storage such as S3, GCS, or Azure Blob Storage.
In an on-premises environment, the target might be an S3-compatible object store.
The key requirement is not the vendor.
The key requirement is that backup storage outlives the Seed and is protected from accidental deletion.
Losing the Seed and the only backup target at the same time is a platform design failure.

The following YAML illustrates the shape of an etcd backup configuration.
Exact fields can vary by Gardener and extension version, so check your landscape API reference before applying it.

```yaml
apiVersion: druid.gardener.cloud/v1alpha1
kind: Etcd
metadata:
  name: etcd-main
  namespace: shoot--local--local
spec:
  replicas: 1
  backup:
    store:
      provider: S3
      container: gardener-etcd-backups
      prefix: shoots/local/local
      secretRef:
        name: etcd-backup
    fullSnapshotSchedule: "0 */6 * * *"
    deltaSnapshotPeriod: 5m
```

The schedule and delta period should match the recovery point objective of the platform.
A development Shoot may tolerate a wider backup interval.
A production database platform may not.
The backup policy must be decided before an incident.
During an incident, the only useful backup policy is the one already running.

### Certificate and Credential Rotation

Gardener handles many credentials for a Shoot.
There are cluster certificate authorities, client credentials, service account keys, SSH keypairs, VPN credentials, and etcd encryption keys.
Rotating them is a staged operation because clients and components need time to trust new material before old material disappears.
Gardener exposes rotation operations through Shoot annotations and status fields.

For a full rotation, the operator starts the first phase, waits for the prepared state, updates external clients as required, and then completes the rotation.
For specific credentials, Gardener offers more targeted operations.
The point is to rotate with observable state, not with ad hoc secret replacement.

```bash
k -n garden-local annotate shoot local gardener.cloud/operation=rotate-credentials-start
k -n garden-local get shoot local -o jsonpath='{.status.credentials.rotation}{"\n"}'
k -n garden-local annotate shoot local gardener.cloud/operation=rotate-credentials-complete
```

Some landscapes wrap these operations with `gardenctl` commands for day-to-day use.
The exercise uses `gardenctl rotate-kubeconfig` because that is the desired operator workflow in this module.
If your installed gardenctl build does not expose that exact subcommand, use the documented Shoot credential-rotation annotations and the Shoot access API as the equivalent path.
The underlying principle remains the same: rotate through Gardener, observe status, and verify that old credentials no longer authenticate.

### Version Updates and Worker Rollouts

Kubernetes upgrades are multi-step.
The control plane must move first.
Then node components roll forward within Kubernetes version-skew rules.
Gardener encodes this sequence so tenants do not invent their own upgrade order.
When `spec.kubernetes.version` changes to a supported version such as `1.35.3`, Gardenlet updates control-plane components, waits for health, and then rolls worker nodes.

```bash
k -n garden-local patch shoot local --type merge \
  -p '{"spec":{"kubernetes":{"version":"1.35.3"}}}'

k -n garden-local get shoot local -w
```

Watching the Shoot status is more meaningful than watching only nodes.
The Shoot status shows the lifecycle operation progress.
If a control-plane component fails first, node status may not tell the story.
If a worker rollout fails later, the Shoot conditions and worker machine status point to the next layer.

### Graceful Deletion

Shoot deletion is not `rm -rf` for clusters.
Gardener needs to drain workload nodes, delete cloud or local infrastructure, remove provider resources, clean up DNS records, clean up backup resources if policy allows, and remove Seed control-plane resources.
Deletion is itself a reconciliation.
If finalizers remain, Gardener is usually waiting for a cleanup step.

The deletion flow should be explicit in production.
Many landscapes require a confirmation annotation before a Shoot can be deleted.
That extra step prevents a casual delete from removing a tenant cluster.
After confirmation, deletion should be watched through Shoot status and provider resources until all external infrastructure is gone.

```bash
k -n garden-local annotate shoot local confirmation.gardener.cloud/deletion=true
k -n garden-local delete shoot local
k -n garden-local get shoot local -w
```

If deletion stalls, do not immediately remove finalizers.
First inspect Shoot status, Gardenlet logs, extension resources, and external infrastructure.
Removing finalizers can orphan provider resources.
The better path is to fix the failed cleanup dependency and let reconciliation finish.

---

## 5. Multi-Tenancy, Dashboard, and Daily Operations

Gardener is built for many teams sharing one managed cluster service.
That makes tenancy a first-class concern.
The Project is the main tenant boundary in the Garden.
A Project maps to a namespace, commonly prefixed with `garden-`.
Shoots live inside Project namespaces.
Cloud credentials, quota objects, project membership, and dashboard visibility are also organized around Projects.

Project membership can be based on users, groups, and ServiceAccounts.
ServiceAccount-based membership matters for automation.
A CI system or GitOps controller should not use a human admin kubeconfig.
It should use a technical identity with only the roles required for its Project.
This supports clear audit trails and easier credential rotation.

Gardener commonly distinguishes project roles such as admin, viewer, and member.
An admin can manage project resources and Shoots.
A viewer can inspect state without changing it.
A member can perform day-to-day actions within the Project, depending on the exact role mapping configured by the landscape.
The exact RBAC bindings are operator-controlled, but the principle is stable: tenant access is scoped through Project namespaces and Gardener roles.

CloudProfiles are operator-managed templates for what tenants are allowed to request.
They define regions, zones, machine types, volume types, machine images, Kubernetes versions, and provider-specific constraints.
The CloudProfile is one of Gardener's strongest multi-tenancy tools because it prevents tenants from bypassing platform standards.
If a machine type is not listed, it is not part of the service catalog.
If a Kubernetes version is not supported, users should not be able to select it.

Quota objects cap per-project resource consumption.
Without quotas, a tenant with automation could create too many Shoots or too many worker nodes and exhaust Seed or provider capacity.
Quotas are not only about cost.
They are also about blast-radius control.
A quota turns a runaway automation bug into a bounded problem.

```yaml
apiVersion: core.gardener.cloud/v1beta1
kind: Quota
metadata:
  name: team-a-quota
  namespace: garden-team-a
spec:
  scope:
    apiVersion: core.gardener.cloud/v1beta1
    kind: Project
  metrics:
    cpu: "80"
    gpu: "0"
    memory: 320Gi
    storage.standard: 2Ti
```

Admission policy is another layer.
Many Kubernetes teams know Kyverno as a policy engine for Kubernetes resources.
Gardener has its own admission plugin system for Gardener API behavior.
Do not confuse the two.
Kyverno can still be useful inside Garden, Seed, or Shoot clusters depending on your governance model, but Gardener-specific admission plugins are the native way to validate and default Gardener resources.
The best platforms use the right admission layer for the right API.

The Gardener Dashboard gives tenants and operators a web view of Projects, Shoots, Seed health, cluster status, credentials, and monitoring links.
It is not a replacement for GitOps or API-driven workflows.
It is a visibility and operations surface.
For many teams, the dashboard is how they discover whether a Shoot is healthy, which version it runs, and where to find the monitoring entry points.
For operators, it is a quick way to scan fleet health before drilling into CLI details.

gardenctl is the operations-focused CLI.
It helps target Garden, Seed, and Shoot clusters without manually stitching kubeconfigs together.
For a user who works across many Shoots, this matters.
Manual kubeconfig management becomes error-prone when names are similar and incidents are active.
gardenctl gives operators a safer targeting workflow.

```bash
gardenctl target --garden local --project local --shoot local
eval "$(gardenctl kubectl-env bash)"
k get nodes
```

The target command selects the Garden, Project, and Shoot.
The `kubectl-env` command updates the shell environment so `k` points at the targeted cluster.
This makes it clear which cluster you are operating on.
In production, always confirm the target before changing resources.

Useful daily gardenctl motions include listing Shoots, switching to a Shoot kubeconfig, inspecting the current target, opening a node SSH session, and triggering approved maintenance flows if your version and landscape support those commands.
Because gardenctl evolves, use `gardenctl --help` and the gardenctl-v2 docs for exact syntax in your environment.
The operational pattern is stable even when subcommands change.

```bash
gardenctl target --garden local --project local
gardenctl target --garden local --project local --shoot local
gardenctl kubeconfig
gardenctl ssh <shoot-node-name>
```

### War Story: The Wrong Kubeconfig

A senior operator once patched a staging namespace while believing they were targeting development.
The namespace names matched because the platform used identical app names across clusters.
The mistake did not cause customer impact, but it showed how weak manual context handling was.
After that incident, the team required explicit target prompts and gardenctl-based targeting for fleet operations.
The fix was not more memory.
The fix was a workflow that made the current target visible and repeatable.

Which approach would you choose for a GitOps controller that creates Shoots: a human admin kubeconfig, a Project-scoped ServiceAccount, or a Garden-wide admin token?
The Project-scoped ServiceAccount is the right starting point.
It limits the blast radius to the intended Project and can be rotated independently.
Garden-wide credentials should be reserved for platform automation that truly needs that scope.

---

## 6. Production Operations at Scale

Production Gardener operations are mostly about controlling shared failure domains.
A single Shoot failure affects one tenant cluster.
A Seed failure can affect hundreds of Shoot control planes.
A Garden failure can affect fleet lifecycle management.
The platform design must reflect those different blast radii.

Etcd backup is the first production concern.
Every Shoot control plane depends on etcd state.
The backup target should be outside the Seed's failure domain.
In public cloud, that often means object storage with versioning and retention.
In private cloud, it may mean S3-compatible storage backed by a separate storage system.
A backup that disappears with the Seed is not a real recovery plan.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: etcd-backup
  namespace: shoot--local--local
type: Opaque
stringData:
  endpoint: https://s3.example.internal
  region: local
  accessKeyID: AKIAIOSFODNN7EXAMPLE
  secretAccessKey: your-secret-access-key-here
```

The example uses placeholder credentials.
Do not copy real provider keys into Git.
Use your platform's approved secret management flow.
The teaching point is the separation of concerns: etcd-druid needs a backup store, and the platform must make that store durable, monitored, and recoverable.

Monitoring is the second concern.
Gardener ships an integrated monitoring stack for Gardener-managed components.
Prometheus collects metrics and powers alerting.
Alertmanager routes alerts.
Plutono provides dashboards.
Gardener uses Plutono because it is an Apache-licensed fork of Grafana from the last Apache-licensed Grafana line.
That licensing choice matters for projects that need an Apache-compatible distribution path.

Gardener's observability stack also includes logging components.
Older material may refer to Loki directly, while current Gardener documentation describes Vali, a Loki fork, as part of its logging stack.
The operational point is that Shoot control-plane logs are collected from the Seed side, where the control-plane pods run.
If an API server pod crashes, the logs are in the Seed context, not on the tenant worker nodes.

Out-of-the-box alerting is valuable because it encodes platform knowledge.
A platform team should not discover from scratch that API server availability, etcd leader changes, VPN connectivity, node readiness, and control-plane component health are important.
Gardener ships alert rules for common managed-component failures.
Teams should tune routing and severity, but they should avoid deleting alerts simply because they are noisy.
Noise usually means thresholds, ownership, or missing runbooks need work.

Incident response often requires node access.
Gardener supports SSH flows to Shoot nodes, commonly through gardenctl.
In hosted-control-plane architectures, the access path may involve the Seed and bastion-style connectivity rather than direct public SSH to every node.
This is a good thing.
Direct public SSH to all worker nodes is a large attack surface and an operational mess.
The bastion flow gives operators controlled access while preserving fleet policy.

```bash
gardenctl target --garden local --project local --shoot local
gardenctl ssh <shoot-node-name>
```

Use SSH for node-level diagnosis, not as a configuration management system.
If you fix a node by hand and do not encode the fix in the Shoot, CloudProfile, image, or extension, the next rollout may remove it.
Gardener's reconciliation model is declarative.
Operational changes should flow back into declarative state.

Scaling Seeds horizontally is the third concern.
One Seed can manage many Shoots, but "can" is not the same as "should place everything there."
As Shoot count grows, operators should add Seeds by region, provider, workload class, or tenant criticality.
A production platform might use separate Seeds for regulated workloads, high-churn development clusters, and production clusters.
This keeps noisy tenants away from sensitive ones and makes incident impact easier to bound.

Failed reconciliation recovery is the fourth concern.
Gardener controllers retry, but retrying a permanent configuration error will not make it succeed.
Operators need a dead-letter mindset.
A Shoot stuck in `Reconciling` for twenty minutes needs structured triage: check Shoot conditions, last operation, Gardenlet logs, extension resource status, Seed capacity, provider API errors, and quota.
Do not restart controllers randomly.
Find the controller that owns the failing step.

```bash
k -n garden-local describe shoot local
k -n garden-local get shoot local -o jsonpath='{.status.lastOperation}{"\n"}'
k -n garden-local get shoot local -o jsonpath='{.status.conditions}{"\n"}'
k -n garden get pods -l app=gardenlet
```

The exact Gardenlet namespace depends on your landscape.
The principle is to start with status and then follow ownership.
If the status says infrastructure is failing, inspect the provider extension resources and logs.
If it says API server availability is failing, inspect the control-plane namespace in the Seed.
If it says every node is not ready, inspect worker machine resources and node bootstrap.

### Production Readiness Checklist

- [ ] Garden cluster is highly available and backed up.
- [ ] Each Seed has capacity alerts and clear ownership.
- [ ] Shoot etcd backups target durable storage outside the Seed failure domain.
- [ ] CloudProfiles publish only supported Kubernetes versions, machine images, and regions.
- [ ] Project quotas are enforced before tenants receive automation credentials.
- [ ] Dashboard and gardenctl access are integrated with the organization's identity provider.
- [ ] Alertmanager routes distinguish operator-facing and tenant-facing alerts.
- [ ] Incident runbooks follow Garden to Seed to Shoot ownership.

---

## Patterns & Anti-Patterns

### Patterns

| Pattern | When to Use | Why It Works | Scaling Considerations |
|---|---|---|---|
| Hosted control planes in regional Seeds | You manage many tenant clusters across providers or regions | Control planes run as pods, so Kubernetes manages their scheduling, restart, and resource isolation | Add Seeds before one Seed becomes a massive shared failure domain |
| CloudProfile as service catalog | Tenants need self-service without arbitrary infrastructure choices | Operators publish supported versions, regions, zones, machine images, and machine types | Review profiles every release cycle so deprecated choices disappear cleanly |
| Project-scoped automation identities | GitOps or CI creates Shoots for one team | ServiceAccounts limit permissions to the Project namespace and make audit trails clearer | Rotate technical credentials and avoid sharing one identity across Projects |
| Maintenance windows with automatic patching | Teams need predictable upgrades without manual tickets | Gardener can reconcile supported version updates during agreed windows | Separate production and development windows to prevent synchronized fleet disruption |
| Seed-per-failure-domain placement | A platform spans multiple regions, providers, or tenant classes | Seed placement keeps control planes close to workers and bounds incidents | Track Seed saturation with metrics, not with anecdotes |

### Anti-Patterns

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|---|---|---|---|
| Snowflake Shoots | Each cluster behaves differently during upgrades and incidents | Teams treat cluster admin access as a customization surface | Put supported variation into CloudProfiles and extension configuration |
| One giant Seed | A single Seed incident affects too many control planes | Early success with one Seed hides future blast radius | Add Seeds by provider, region, and tenant criticality |
| Manual finalizer removal | External resources are orphaned or backups disappear unexpectedly | Deletion feels stuck and pressure rises during cleanup | Diagnose the failing cleanup step and let reconciliation finish |
| Unbounded Project creation | Tenants exhaust provider quota or Seed capacity | Self-service launches before quota policy | Create Project quotas before handing out automation identities |
| Treating dashboard clicks as source of truth | Changes are hard to review and repeat | The dashboard is convenient for urgent edits | Use GitOps for desired state and dashboard for visibility |
| Ignoring advertised addresses | Kubeconfigs fail after endpoint or exposure changes | Operators assume the API endpoint is fixed forever | Inspect Shoot status and reissue kubeconfigs through Gardener workflows |

---

## Decision Framework

Gardener, Cluster API, and Crossplane all use Kubernetes-style APIs, but they optimize for different platform products.
Choosing between them is mostly about the level of abstraction you want to own.
Gardener is a Kubernetes-as-a-Service product.
Cluster API is a composable cluster lifecycle framework.
Crossplane is a generic infrastructure control plane that can also provision clusters.

| Dimension | Gardener | Cluster API | Crossplane | Winner-context |
|---|---|---|---|---|
| Abstraction level | Full managed Kubernetes-as-a-Service with Projects, Shoots, Seeds, dashboard, maintenance, and quotas | Cluster lifecycle building blocks for management and workload clusters | Universal control plane for cloud resources, services, and clusters | Gardener when users need a cluster service, CAPI when platform engineers want primitives, Crossplane when all infrastructure should be modeled in Kubernetes |
| Extension mechanism | Provider, OS, network, DNS, and backup extensions via Gardener APIs, webhooks, and controllers | Infrastructure, bootstrap, and control-plane providers | Providers and compositions for many resource types | Gardener for opinionated cluster service extensions, CAPI for lifecycle controller composition, Crossplane for broad IaC composition |
| Opinionatedness | High | Medium | Medium to low depending on compositions | Gardener wins when consistency matters more than unlimited shape freedom |
| Production readiness | Designed from SAP-scale production experience and hosted control planes | Strong ecosystem but requires assembly and platform ownership | Strong for infrastructure orchestration, cluster quality depends on provider and composition | Gardener for thousands of managed clusters, CAPI for teams that will build their own platform, Crossplane for multi-resource infrastructure platforms |
| Multi-tenancy | Projects, quotas, dashboard, roles, and service accounts are native platform concepts | Possible through management-cluster design but not a complete product by default | Possible through Crossplane claims and namespaces | Gardener when tenant cluster self-service is the product |
| Community ecosystem | Smaller than CAPI, focused on managed cluster service | Broad Kubernetes SIG ecosystem and many providers | Broad provider ecosystem across cloud services | CAPI for maximum cluster-lifecycle ecosystem breadth, Crossplane for resource breadth |
| Bare-metal support | Possible through provider extensions and integrations such as MetalStack or Equinix Metal | Strong with Metal3 and related providers | Possible through providers but often requires composition work | CAPI when you want to own bare-metal lifecycle mechanics, Gardener when you want a managed service layer above provider integration |
| Cloud-managed Kubernetes target | Gardener creates conformant Kubernetes clusters as a service, not just wrapping EKS/GKE/AKS | Can manage clusters through providers depending on implementation | Can request managed services and clusters as resources | Crossplane wins when managed cloud services and clusters are both part of one IaC API |

Use Gardener when your platform team wants a batteries-included, opinionated Kubernetes-as-a-Service for many internal teams.
Use it when the service must include lifecycle automation, dashboard visibility, quota, maintenance, extension-driven providers, and hosted control planes.
It is strongest when the question is, "How do we operate thousands of tenant Kubernetes clusters consistently?"

Use Cluster API when you want to build your own lifecycle platform from composable parts.
It is a strong fit when you want direct ownership of cluster controller choices, bootstrap strategy, and infrastructure providers.
It gives you a framework, not a complete internal cluster product.
That distinction is useful if your requirements are unusual and your team is ready to own the assembly.

Use Crossplane when Kubernetes is your universal infrastructure language.
It is a strong fit when a team wants to model databases, networks, IAM, object storage, and clusters through one control-plane API.
It can provision clusters, but its center of gravity is broader infrastructure composition.
If the platform product is "all infrastructure through claims," Crossplane deserves serious evaluation.

```mermaid
flowchart TD
    A[What are you building?] --> B{Primary product is tenant Kubernetes clusters?}
    B -->|Yes| C{Need opinionated lifecycle, quota, dashboard, maintenance?}
    C -->|Yes| D[Choose Gardener]
    C -->|No| E[Evaluate Cluster API]
    B -->|No| F{Need Kubernetes API for many infrastructure services?}
    F -->|Yes| G[Choose Crossplane]
    F -->|No| H[Use provider-native tooling or Terraform-style IaC]
    E --> I{Want to own lifecycle controller assembly?}
    I -->|Yes| J[Cluster API fits]
    I -->|No| D
```

The practical on-premises choice is often not exclusive.
A platform may use Cluster API or provider automation underneath a Gardener extension.
A platform may use Crossplane to create supporting infrastructure that Gardener then uses.
The key is to avoid making tenants learn every layer.
The tenant-facing product should stay simple even if the platform internals are sophisticated.

---

## Did You Know?

1. Gardener's first open-source commit was published on January 10, 2018, after the project began inside SAP in 2017.
2. SAP authors stated in the Kubernetes blog that Gardener was already managing thousands of conformant clusters across major hyperscalers and private clouds by late 2019.
3. A single Seed can host control planes for hundreds of Shoots because the Shoot control planes run as Kubernetes pods rather than dedicated master machines.
4. Plutono is used in Gardener's observability stack because it preserves an Apache-licensed dashboard path from the Grafana 7.5 line.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Treating a Shoot like a self-hosted kubeadm cluster | Operators forget that the control plane runs in the Seed | Start every incident by locating the Shoot, Seed, and Seed namespace |
| Allowing arbitrary Kubernetes versions | Self-service is launched before CloudProfile governance is complete | Publish only supported 1.35+ versions and use maintenance windows |
| Skipping Project quotas | Early tenant adoption looks small enough to manage by trust | Define Quota objects before issuing automation credentials |
| Removing finalizers during stuck deletion | The delete appears frozen and pressure builds | Inspect Shoot status, extension resources, and Gardenlet logs first |
| Using one shared automation identity | It is faster than creating Project-scoped ServiceAccounts | Use per-Project ServiceAccounts and rotate them independently |
| Debugging worker nodes before checking control-plane pods | Traditional cluster habits dominate incident response | Follow Garden status to Seed namespace to Shoot workers |
| Placing every Shoot on one Seed | Initial capacity is enough and growth feels gradual | Add Seeds by region, provider, or tenant criticality before saturation |

---

## Quiz

<details>
<summary>Your Shoot cluster has been stuck in Reconciling for 20 minutes after creation. What do you check first, and why?</summary>

Start with the Shoot status in the Garden namespace: `k -n <project-namespace> describe shoot <name>` and the `.status.lastOperation` plus `.status.conditions` fields.
Those fields identify which lifecycle stage is failing before you read logs.
If the failure points to infrastructure, inspect extension resources and provider extension logs.
If it points to API server availability, move to the Seed namespace that hosts the Shoot control plane.
This avoids guessing across every layer of the architecture.

</details>

<details>
<summary>A tenant asks to run Kubernetes 1.36.1, but your platform has validated only 1.35 patch releases. How should Gardener enforce the platform decision?</summary>

The supported versions should be encoded in the CloudProfile and admission behavior, not handled as a manual review comment.
If 1.36.1 is not approved, it should not be selectable in the tenant's Shoot manifest.
This keeps version policy consistent across Projects and automation paths.
When the platform validates 1.36 later, operators can update the CloudProfile and maintenance policy.

</details>

<details>
<summary>After a Seed upgrade, several Shoots report API server availability problems, but tenant worker nodes are still Ready. Where do you focus?</summary>

Focus on the Seed layer because the affected API servers run as pods in Seed namespaces.
Worker readiness can remain green for a while even when new API requests fail.
Inspect the affected Shoot control-plane namespaces, kube-apiserver pods, Services, ingress or exposure components, and Seed-level networking.
The common timing across multiple Shoots also suggests a shared Seed dependency rather than separate tenant workload failures.

</details>

<details>
<summary>Your platform team wants one API to create object storage buckets, databases, IAM roles, and Kubernetes clusters. Is Gardener the best center of gravity?</summary>

Gardener is not the best center of gravity for generic infrastructure orchestration.
It is focused on Kubernetes-as-a-Service.
Crossplane is usually a better fit when the product is a universal infrastructure API for many resource types.
Gardener may still manage clusters, but Crossplane can compose the surrounding cloud services.

</details>

<details>
<summary>A developer deletes a Shoot and the object remains with finalizers. They ask you to remove the finalizers manually. What do you do?</summary>

Do not remove finalizers as the first response.
Finalizers usually mean a cleanup step has not finished, such as deprovisioning infrastructure, removing DNS records, or deleting backup resources according to policy.
Inspect the Shoot status, Gardenlet logs, and provider extension resources to find the failing cleanup step.
Only use finalizer removal as a last-resort recovery action after documenting orphaned resources and cleanup responsibility.

</details>

<details>
<summary>A security team requires regular kubeconfig credential rotation for tenant clusters. How should that be implemented in Gardener?</summary>

Use Gardener's Shoot credential-rotation workflow rather than replacing kubeconfig files by hand.
Depending on the landscape and CLI version, that may be exposed through gardenctl or through documented Shoot annotations such as rotation start and completion operations.
Track `.status.credentials.rotation` so the team can see whether rotation is prepared, completing, or completed.
After rotation, verify that newly issued credentials work and old credentials no longer authenticate.

</details>

<details>
<summary>Your organization already uses Cluster API successfully on bare metal. When would you still introduce Gardener?</summary>

Introduce Gardener when the platform product must become a managed, multi-tenant Kubernetes-as-a-Service rather than a lifecycle toolkit.
CAPI is excellent when the platform team wants to own the assembly of providers, bootstrap, and control-plane mechanics.
Gardener adds Projects, quotas, dashboard workflows, maintenance automation, hosted control planes, and a higher-level Shoot API.
The decision depends on whether tenants need a service product or platform engineers need building blocks.

</details>

---

## Hands-On Exercise

In this exercise, you will run a local Gardener landscape using the `gardener-local` provider.
The local provider runs on kind, so you do not need a real cloud account.
The goal is an end-to-end lifecycle: provision, inspect, scale, upgrade, rotate credentials, and delete a Shoot through the Gardener API.

Your apex outcome is a complete end-to-end cluster lifecycle operated declaratively through Gardener.
You should be able to explain which layer is responsible for each step.

### Setup Notes

You need Docker, kind, Go tooling required by Gardener, `kubectl`, and enough local resources.
The official local setup guide recommends generous CPU, memory, and disk allocation because the Garden, Seed, and Shoot run on the same machine.
Close other heavy workloads before starting.

Create the `k` alias before beginning:

```bash
alias k=kubectl
```

### Task 1: Bootstrap a Local Gardener Environment

Clone Gardener and start the local kind-based landscape.

```bash
git clone https://github.com/gardener/gardener.git
cd gardener
make kind-up gardener-up
```

Set your kubeconfig to the local Garden cluster if the script does not do it for your shell.

```bash
export KUBECONFIG="$PWD/example/gardener-local/kind/local/kubeconfig"
k get ns
k get apiservices | grep gardener
k get seeds
```

Verify that the Gardener API server is registered and the local Seed exists.
The local setup commonly uses one kind cluster as both Garden and Seed for simplicity.

<details>
<summary>Solution and success criteria for Task 1</summary>

You should see Gardener API services registered and a Seed named `local`.
If `k get seeds` fails, confirm that `KUBECONFIG` points at `example/gardener-local/kind/local/kubeconfig`.
If the API service exists but reports unavailable, wait for the Gardener API server and controller pods to become ready.

- [ ] `k get ns` returns namespaces from the local kind cluster.
- [ ] `k get apiservices | grep gardener` shows Gardener API services.
- [ ] `k get seeds` lists the local Seed.
- [ ] You can explain why the same kind cluster can act as Garden and Seed in the local setup.

</details>

### Task 2: Inspect the Garden Cluster State

List all Seeds, their conditions, and current Shoots.

```bash
k get seeds -o wide
k get shoots -A
k -n garden get pods | grep gardenlet
```

If your local setup places Gardenlet in a different namespace, find it with labels:

```bash
k get pods -A | grep gardenlet
```

Observe that Gardenlet is the Seed-side agent responsible for reconciling assigned Shoots.
This is the component you will inspect during many reconciliation failures.

<details>
<summary>Solution and success criteria for Task 2</summary>

You should see the local Seed and either no Shoots yet or the sample Shoots you created earlier.
Gardenlet should be running because it is the actor that turns Shoot desired state into Seed-hosted control planes and provider resources.
If Gardenlet is missing, the Seed will not reconcile Shoots.

- [ ] `k get seeds -o wide` shows the local Seed.
- [ ] `k get shoots -A` works even if no Shoots exist yet.
- [ ] You located the Gardenlet pod.
- [ ] You can describe why Gardenlet runs per Seed.

</details>

### Task 3: Create a Shoot Cluster

Apply the example Shoot manifest from the local provider.

```bash
k apply -f example/provider-local/shoot.yaml
k -n garden-local get shoot local -w
```

Watch the Shoot progress through lifecycle states such as `Creating`, `Reconciling`, and `Ready`.
Time the provisioning process on your machine.
Local resource pressure can make this slower than expected.

After the Shoot becomes ready, inspect its advertised addresses and conditions.

```bash
k -n garden-local get shoot local -o jsonpath='{.status.advertisedAddresses}{"\n"}'
k -n garden-local get shoot local -o jsonpath='{.status.conditions}{"\n"}'
```

<details>
<summary>Solution and success criteria for Task 3</summary>

The Shoot should eventually become healthy.
If it remains in `Reconciling`, describe the Shoot and inspect the last operation.
Then inspect Gardenlet and provider-local logs.
The most common local causes are insufficient Docker resources, image pull delays, or local networking issues.

- [ ] `k -n garden-local get shoot local` shows the Shoot.
- [ ] The Shoot reaches a healthy or ready state.
- [ ] You captured how long local provisioning took.
- [ ] You inspected advertised addresses and conditions.

</details>

### Task 4: Scale the Worker Pool and Trigger a Rolling Node Update

Edit the worker pool minimum and maximum values in the Shoot manifest.
For example, change the first worker pool to allow two workers.

```bash
cp example/provider-local/shoot.yaml /tmp/shoot-local.yaml
```

Edit `/tmp/shoot-local.yaml` so the first worker pool has values like these:

```yaml
minimum: 1
maximum: 2
```

Reapply the manifest and watch the Shoot.

```bash
k apply -f /tmp/shoot-local.yaml
k -n garden-local get shoot local -w
```

Then patch a worker pool machine image version to trigger a node rolling update.
Use a version supported by your local CloudProfile.
The example below is illustrative; inspect your CloudProfile first.

```bash
k get cloudprofile local -o yaml | grep -A20 machineImages
k -n garden-local patch shoot local --type merge \
  -p '{"spec":{"provider":{"workers":[{"name":"worker","machine":{"image":{"name":"gardenlinux","version":"1.35.1"}}}]}}}'
```

<details>
<summary>Solution and success criteria for Task 4</summary>

The Shoot should reconcile after the worker pool change.
The autoscaler may not add a node unless there is pending workload demand, but the desired bounds should update.
The machine image patch should trigger a worker rollout if the image version is valid and different from the current version.
If the patch is rejected, use the versions listed in the local CloudProfile.

- [ ] Worker minimum and maximum values changed in the Shoot spec.
- [ ] The Shoot reconciled after reapply.
- [ ] You checked supported machine image versions before patching.
- [ ] You observed rollout behavior or a clear validation error.

</details>

### Task 5: Trigger a Kubernetes Version Upgrade

Patch the Shoot Kubernetes version to a newer supported 1.35 patch version.
Confirm the target version exists in the CloudProfile before patching.

```bash
k get cloudprofile local -o yaml | grep -A30 versions
k -n garden-local patch shoot local --type merge \
  -p '{"spec":{"kubernetes":{"version":"1.35.3"}}}'
k -n garden-local get shoot local -w
```

Watch the sequence.
The control plane should reconcile before workers roll.
After the Shoot returns to ready, acquire or refresh your Shoot kubeconfig using the local setup helper or gardenctl workflow for your environment.
Then verify the upgraded cluster.

```bash
./hack/usage/generate-admin-kubeconf.sh > /tmp/local-shoot-kubeconfig.yaml
KUBECONFIG=/tmp/local-shoot-kubeconfig.yaml k version
KUBECONFIG=/tmp/local-shoot-kubeconfig.yaml k get nodes
```

<details>
<summary>Solution and success criteria for Task 5</summary>

The upgrade should proceed only if the requested version is supported by the CloudProfile.
If `1.35.3` is not available in your local checkout, select another supported 1.35+ patch version from the CloudProfile.
After reconciliation, `k version` against the Shoot kubeconfig should report the new server version.
Node rollout may take longer than control-plane rollout because nodes must be recreated or updated safely.

- [ ] You verified the target version in the CloudProfile.
- [ ] You patched `spec.kubernetes.version`.
- [ ] The Shoot returned to ready.
- [ ] The refreshed kubeconfig can query the upgraded Shoot.

</details>

### Task 6: Rotate Kubeconfig Credentials and Delete the Shoot

Use gardenctl to target the local Shoot before changing credentials, because this step makes the active Garden, Project, and Shoot explicit in your shell. Treat the target selection as part of the safety procedure, not as a convenience shortcut.

```bash
gardenctl target --garden local --project local --shoot local
eval "$(gardenctl kubectl-env bash)"
k get ns
```

Rotate the Shoot's kubeconfig credentials with the operator workflow requested for this module, then watch the Shoot status rather than assuming the command completed every phase instantly. Credential rotation is a reconciled lifecycle operation, so status is the source of truth.

```bash
gardenctl rotate-kubeconfig --garden local --project local --shoot local
```

If your installed gardenctl does not provide that exact command, use the Gardener credential-rotation annotations shown below as the equivalent API-level path. This keeps the exercise aligned with Gardener's reconciliation model while avoiding dependence on one particular gardenctl release.

```bash
k --kubeconfig "$PWD/example/gardener-local/kind/local/kubeconfig" \
  -n garden-local annotate shoot local gardener.cloud/operation=rotate-credentials-start

k --kubeconfig "$PWD/example/gardener-local/kind/local/kubeconfig" \
  -n garden-local get shoot local -o jsonpath='{.status.credentials.rotation}{"\n"}'

k --kubeconfig "$PWD/example/gardener-local/kind/local/kubeconfig" \
  -n garden-local annotate shoot local gardener.cloud/operation=rotate-credentials-complete
```

Verify that a newly issued kubeconfig works.
Then verify that the old kubeconfig fails once the rotation has completed and old credentials are no longer accepted.
Finally, delete the Shoot cleanly.

```bash
k --kubeconfig "$PWD/example/gardener-local/kind/local/kubeconfig" \
  -n garden-local annotate shoot local confirmation.gardener.cloud/deletion=true

k --kubeconfig "$PWD/example/gardener-local/kind/local/kubeconfig" \
  -n garden-local delete shoot local

k --kubeconfig "$PWD/example/gardener-local/kind/local/kubeconfig" \
  -n garden-local get shoot local -w
```

<details>
<summary>Solution and success criteria for Task 6</summary>

The rotation should be visible in Shoot credential rotation status.
A fresh kubeconfig should work after rotation.
The old kubeconfig should fail once the relevant credential material has been invalidated.
Deletion should remove the Shoot and its Seed-hosted control-plane resources.
If deletion stalls, inspect the Shoot status and extension cleanup logs before touching finalizers.

- [ ] You targeted the Shoot through gardenctl or equivalent kubeconfig workflow.
- [ ] Credential rotation status changed on the Shoot.
- [ ] A fresh kubeconfig worked after rotation.
- [ ] The old kubeconfig no longer authenticated after completion.
- [ ] The Shoot was deleted with deletion confirmation.
- [ ] No local Shoot remains in `k -n garden-local get shoots`.

</details>

### Exercise Debrief

You have now operated the full lifecycle that matters in a managed cluster service.
You created desired state in the Garden.
Gardenlet reconciled execution in the Seed.
The local provider created the Shoot.
You inspected status, changed worker configuration, upgraded Kubernetes, rotated credentials, and deleted the cluster.
That is the mental model to carry into real providers.

In production, the same lifecycle has stronger policy around identity, quota, backup, network ranges, and Seed placement.
The local provider removes cloud account friction, but it does not remove the architecture.
Garden, Seed, Shoot, extension, status, and reconciliation remain the same concepts.

---

## Next Module

Next: Karmada/Liqo + kube-vip for multi-cluster on-prem federation, where you will compare cluster lifecycle management with workload placement and cross-cluster service continuity.

---

## Sources

- [Gardener project homepage](https://gardener.cloud/)
- [Official Gardener documentation](https://gardener.cloud/docs/)
- [Gardener main repository](https://github.com/gardener/gardener)
- [etcd-druid repository](https://github.com/gardener/etcd-druid)
- [Gardener Dashboard repository](https://github.com/gardener/dashboard)
- [gardenctl-v2 repository](https://github.com/gardener/gardenctl-v2)
- [Current Gardener local setup documentation](https://gardener.cloud/docs/gardener/deployment/getting_started_locally/)
- [Gardener extension documentation](https://gardener.cloud/docs/extensions/)
- [Gardener architecture concepts](https://github.com/gardener/gardener/blob/master/docs/concepts/architecture.md)
- [CNCF landscape entry for Gardener](https://landscape.cncf.io/?item=provisioning--automation-configuration--gardener)
- [CNCF webinar: managing thousands of clusters with Gardener](https://www.cncf.io/online-programs/cncf-live-webinar-how-we-manage-thousands-of-clusters-with-minimal-efforts-using-gardener/)
- [SAP Open Source and InnerSource publications](https://pages.community.sap.com/topics/open-source/publications)
- [Kubernetes blog by SAP authors: Gardener Project Update](https://kubernetes.io/blog/2019/12/02/gardener-project-update/)
- [Kubernetes blog by SAP authors: Gardener - The Kubernetes Botanist](https://kubernetes.io/blog/2018/05/17/gardener/)
- [Gardener Shoot credential rotation](https://gardener.cloud/docs/gardener/shoot-operations/shoot_credentials_rotation/)
- [Gardener Shoot access documentation](https://gardener.cloud/docs/gardener/shoot/shoot_access/)
- [Gardener Project documentation](https://gardener.cloud/docs/getting-started/project/)
- [Gardener observability components](https://gardener.cloud/docs/getting-started/observability/components/)
- [Gardener monitoring stack](https://gardener.cloud/docs/gardener/monitoring-stack/)
- [Plutono repository](https://github.com/credativ/plutono)
