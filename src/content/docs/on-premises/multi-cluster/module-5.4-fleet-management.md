---
title: "Fleet Management"
description: "Architecting, deploying, and operating multi-cluster management planes on bare metal using OCM, Fleet, and Argo CD."
slug: on-premises/multi-cluster/module-5.4-fleet-management
sidebar:
  order: 54
---

# Fleet Management

Operating a single bare-metal Kubernetes cluster is an exercise in node and component lifecycle management. Operating fifty, five hundred, or five thousand clusters requires a fundamental shift in architecture. Standard GitOps tools designed for single-cluster continuous delivery break down under the N×M connection matrix required for fleet-wide policy and workload distribution.

Fleet management platforms provide a centralized control plane to register, select, and configure fleets of Kubernetes clusters dynamically, treating clusters as cattle rather than pets.

## Learning Outcomes

*   **Differentiate** between infrastructure lifecycle management (Cluster API) and workload/policy fleet management (OCM, Fleet, Karmada).
*   **Evaluate** push-based vs. pull-based fleet architectures regarding bare-metal network topologies and firewall constraints.
*   **Implement** Open Cluster Management (OCM) to bootstrap a hub-and-spoke fleet topology.
*   **Formulate** cluster placement rules based on custom hardware labels and capacity metrics.
*   **Diagnose** common fleet failures, including agent disconnections, API server exhaustion, and CRD version skew.

## The Fleet Management Architecture

Scaling GitOps across multiple bare-metal clusters introduces distinct operational bottlenecks. If you run one Argo CD or Flux instance per cluster, you face configuration drift in the CD tooling itself. If you run a centralized Argo CD instance and push to hundreds of clusters, the central controller must maintain active credentials and network routes to every remote API server.

Fleet management separates *what* needs to be deployed from *where* it should be deployed.

### Push vs. Pull Architectures

The most critical architectural decision in fleet management is the network direction of the control loop.

```mermaid
flowchart TD
    subgraph Push-Based [Push-Based (e.g., Default Argo CD, Karmada)]
        HubA[Central Control Plane] -->|HTTPS POST| SpokeA1[Spoke API Server]
        HubA -->|HTTPS POST| SpokeA2[Spoke API Server]
    end

    subgraph Pull-Based [Pull-Based (e.g., OCM, Rancher Fleet)]
        SpokeB1[Spoke Agent] -->|HTTPS GET/WATCH| HubB[Central Control Plane]
        SpokeB2[Spoke Agent] -->|HTTPS GET/WATCH| HubB
    end
```

**Push-Based:**
The central control plane authenticates against the spoke cluster's API server.
*   *Pros:* No agent installation required on the spoke. Immediate actuation.
*   *Cons:* Requires the spoke API server to be reachable from the central hub. In bare-metal environments, spoke clusters are often deployed at the edge, behind strict NAT or firewalls without inbound ingress. Storing hundreds of high-privileged `kubeconfig` files centrally creates a massive security blast radius.

**Pull-Based:**
An agent runs on the spoke cluster and connects outbound to the central hub to retrieve configurations.
*   *Pros:* Works seamlessly through NAT and firewalls (outbound TCP/443 only). No inbound ports required on the spoke. Compromising a spoke only exposes that specific cluster.
*   *Cons:* Requires managing the lifecycle of the agent itself. Slightly higher latency due to polling/watch mechanisms.

> **Stop and think**: Why might a pull-based architecture be considered fundamentally more secure for edge deployments than a centralized push-based one, even if network traversal is not an issue?

### Ecosystem Comparison

| Tool | Architecture | Primary Abstraction | Best Use Case |
| :--- | :--- | :--- | :--- |
| **Argo CD ApplicationSets** | Push (usually) | `ApplicationSet`, `ClusterGenerator` | 10-50 clusters on flat networks. Developer-centric GitOps. The controller is merged into core Argo CD. |
| **Rancher Fleet** | Pull | `GitRepo`, `Bundle`, `ClusterGroup` | Edge deployments (1000+ clusters). Tight integration with Rancher. (Proprietary, non-CNCF project). |
| **Open Cluster Management** | Pull | `ManagedCluster`, `ManifestWork`, `Placement` | Bare metal, complex dynamic targeting, policy orchestration. (CNCF Sandbox project). |
| **Karmada** | Push/Pull | `PropagationPolicy`, `ResourceBinding` | Multi-cloud federation, stretching a single deployment across clusters. (CNCF Incubating project). |

:::note
**Cluster API (CAPI) vs. Fleet Management**
CAPI provisions the *infrastructure* (machines, control planes, etcd). Fleet management provisions the *payload* (workloads, policies, RBAC). While CAPI provides a `Cluster` CRD, fleet managers use their own constructs (e.g., `ManagedCluster`) to handle the post-provisioning lifecycle. You typically use CAPI to create the cluster, and a post-hook triggers the fleet manager agent installation.
:::

## Open Cluster Management (OCM) Deep Dive

Open Cluster Management (a CNCF Sandbox project, currently at stable v1.2.0) is the defacto standard for bare-metal fleet management requiring high customizability. It uses a strict hub-and-spoke, pull-based architecture, typically leveraging gRPC for hub-spoke communication.

### Core Components

1.  **Hub Cluster**: Runs the OCM control plane (Registration, Work, and Placement controllers). It does not run workloads.
2.  **Klusterlet**: The agent running on the Managed (Spoke) Cluster. It initiates the connection to the Hub, creates a Certificate Signing Request (CSR), and pulls `ManifestWork`.
3.  **ManagedCluster**: A cluster-scoped CRD on the Hub representing a registered spoke.
4.  **ManifestWork**: A CRD placed in a dedicated namespace on the Hub (e.g., `cluster1-ns`). The Klusterlet watches this specific namespace, pulls the manifests, and applies them locally.
5.  **Placement**: Defines rules for selecting `ManagedClusters` based on labels, claims (e.g., Kubernetes version, hardware type), or scores.

### Cluster Registration Flow

Bootstrapping trust on bare metal without a cloud provider IAM requires a cryptographic handshake.

1.  The Hub admin generates a bootstrap token.
2.  The Klusterlet starts on the spoke using the bootstrap token. It connects to the Hub and submits a CSR.
3.  The Klusterlet creates a `ManagedCluster` request on the Hub.
4.  The Hub admin (or an automated operator) approves the CSR and sets `hubAcceptsClient: true` on the `ManagedCluster`.
5.  The Hub generates a unique client certificate for the Klusterlet. The Klusterlet drops the bootstrap token and authenticates using mTLS going forward.

:::tip
In production bare metal, automate CSR approval using a custom controller that verifies the spoke's hardware attestation (e.g., TPM quotes) or checks the IP address against a known-good CMDB (NetBox) before setting `hubAcceptsClient: true`.
:::

## Argo CD ApplicationSets at Scale

While OCM handles the "how to deliver", Argo CD (now stable at v3.x) is often still used for "what to deliver". `ApplicationSets` allow you to template Argo CD `Applications` across multiple clusters. The ApplicationSet controller is no longer standalone and is fully integrated into core Argo CD.

When operating at fleet scale (100+ clusters), rely on the **Matrix Generator** combined with a Git directory structure, rather than configuring each cluster explicitly.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: fleet-prometheus
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
    - matrix:
        generators:
          - git:
              repoURL: https://github.com/org/fleet-config.git
              revision: HEAD
              directories:
                - path: workloads/prometheus/*
          - cluster:
              selector:
                matchLabels:
                  environment: production
                  hardware: bare-metal
  template:
    metadata:
      name: '{{.path.basename}}-prometheus'
    spec:
      project: default
      source:
        repoURL: https://github.com/org/fleet-config.git
        targetRevision: HEAD
        path: '{{.path.path}}'
        helm:
          valueFiles:
            - values.yaml
            - 'values-{{.name}}.yaml'
      destination:
        server: '{{.server}}'
        namespace: monitoring
```

**Production Gotcha:** By default, Argo CD connects to remote clusters via push. If you integrate Argo CD with OCM, you can use the OCM Pull Model. OCM provides an `argocd-pull-integration` controller that translates Argo CD `Applications` on the Hub into `ManifestWorks` that the Klusterlet pulls, giving you GitOps UX with a Pull-based network topology.

## Policy Distribution and Centralized Audit

Fleet management is not just workloads; it is governance. Distributing Kyverno or OPA Gatekeeper policies across 500 bare-metal clusters requires strict consistency.

Use OCM's `Policy` framework (governance-policy-propagator) to distribute CRDs.

1.  **PlacementBinding**: Binds a Policy to a Placement rule.
2.  **ConfigurationPolicy**: Instructs the Klusterlet to enforce the existence of specific Kubernetes resources (e.g., a Kyverno `ClusterPolicy`).
3.  **Status Sync**: The Klusterlet reports the compliance status of the policy back to the Hub.

For audit logs, do not rely on querying the hub. Configure fluent-bit/Vector via a fleet-wide DaemonSet to ship standard API audit logs directly from the spoke control plane nodes to a centralized SIEM (e.g., OpenSearch or Splunk) independent of the fleet management control channel.

## Hands-on Lab

In this lab, you will deploy an Open Cluster Management (OCM) hub, register a spoke cluster, and deploy a workload dynamically using a `ManifestWork`.

### Prerequisites

*   `kind` (Kubernetes in Docker)
*   `kubectl` (v1.35+)
*   `clusteradm` (OCM CLI, install via `curl -L https://raw.githubusercontent.com/open-cluster-management-io/clusteradm/main/install.sh | bash`)

### Step 1: Provision the Clusters

Create two independent Kubernetes clusters to simulate a bare-metal Hub and Spoke.

```bash
kind create cluster --name hub
kind create cluster --name spoke1
```

### Step 2: Initialize the Hub

Switch your context to the hub cluster and initialize the OCM control plane.

```bash
kubectl config use-context kind-hub
clusteradm init --wait
```

*Verification:*
```bash
kubectl get po -n open-cluster-management
```
*Expected Output:* You should see `cluster-manager` pods in `Running` state.

### Step 3: Extract the Join Command

Extract the bootstrap token command from the Hub.

```bash
clusteradm get token
```
Copy the output command. It will look similar to:
`clusteradm join --hub-token <token> --hub-apiserver <https://ip:port> --cluster-name <cluster_name>`

### Step 4: Join the Spoke Cluster

Because we are running in `kind`, the spoke needs the internal Docker IP of the hub API server. Find it:
```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' hub-control-plane
```
*(Assume it is 172.18.0.2 for this example)*

Switch to the spoke cluster and run the join command, modifying the IP and naming the cluster `spoke1`.

```bash
kubectl config use-context kind-spoke1

clusteradm join \
  --hub-token <YOUR_TOKEN> \
  --hub-apiserver https://172.18.0.2:6443 \
  --cluster-name spoke1 \
  --force-internal-endpoint-lookup \
  --wait
```

### Step 5: Accept the Spoke on the Hub

The Spoke has initiated a CSR and created a `ManagedCluster` record. You must approve it on the Hub.

```bash
kubectl config use-context kind-hub
clusteradm accept --clusters spoke1
```

*Verification:*
```bash
kubectl get managedclusters
```
*Expected Output:* `spoke1` should show `JOINED=True`, `AVAILABLE=True`.

### Step 6: Deploy a Workload via ManifestWork

Create a `ManifestWork` on the Hub to deploy Nginx to the spoke. Note that the namespace on the Hub *must* match the name of the managed cluster (`spoke1`).

```bash
cat <<EOF | kubectl apply -f -
apiVersion: work.open-cluster-management.io/v1
kind: ManifestWork
metadata:
  name: deploy-nginx
  namespace: spoke1
spec:
  workload:
    manifests:
      - apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: nginx-fleet
          namespace: default
        spec:
          replicas: 2
          selector:
            matchLabels:
              app: nginx
          template:
            metadata:
              labels:
                app: nginx
            spec:
              containers:
              - name: nginx
                image: nginx:1.27
EOF
```

### Step 7: Verify on the Spoke

Switch back to the spoke and verify the Klusterlet pulled and applied the manifest.

```bash
kubectl config use-context kind-spoke1
kubectl get deployments -n default
```
*Expected Output:* `nginx-fleet` is deployed and running 2 replicas.

> **Pause and predict**: If an administrator deletes the `ManagedCluster` resource from the Hub while the spoke is temporarily offline, what will happen to the Nginx workload when the spoke comes back online and the Klusterlet reconnects?

### Troubleshooting the Lab

*   **Spoke stays in `AVAILABLE=Unknown`**: The Klusterlet cannot reach the Hub API server. Verify the Docker networking and the `--hub-apiserver` IP provided during the `join` command. Check logs with `kubectl logs -n open-cluster-management-agent -l app=klusterlet --context kind-spoke1`.
*   **ManifestWork is not applying**: Check the `Status` field of the `ManifestWork` on the hub: `kubectl get manifestwork deploy-nginx -n spoke1 -o yaml`. OCM reports the exact remote API server error back to the hub.

## Practitioner Gotchas

1.  **Etcd Limit Exhaustion on ManifestWorks**: A `ManifestWork` encapsulates Kubernetes manifests inside a CRD. Etcd has a hard limit of 1.5MB per object. If you attempt to distribute a massive CRD installation (like Prometheus Operator bundled with all PrometheusRules) in a single `ManifestWork`, the Hub API server will reject it. *Fix: Split large deployments into multiple `ManifestWorks` or use the fleet manager to deploy a lightweight Helm/Argo Application that pulls the heavy manifests directly from Git on the spoke.*
2.  **Agent Disconnection and Orphaned Resources**: If a Spoke cluster goes offline or the Klusterlet crashes, the Hub marks the cluster as unavailable. If an administrator deletes the `ManagedCluster` from the Hub while the spoke is disconnected, the Klusterlet (upon reconnecting) will garbage collect (delete) all workloads it previously deployed. *Fix: Explicitly configure `deleteOption: Orphan` on critical `ManifestWorks` if you want workloads to survive fleet unregistration.*
3.  **Hub API Server QPS Overload**: In a pull architecture, thousands of Klusterlets constantly watch the Hub for `ManifestWork` changes. After a Hub control plane restart, all agents reconnect simultaneously, causing a thundering herd that can crash the Hub API server. *Fix: Heavily tune the `--max-requests-inflight` and `--max-mutating-requests-inflight` on the Hub API server, and ensure Klusterlets are configured with jittered sync intervals.*
4.  **CRD Version Skew**: Distributing a `ManifestWork` containing an older API version (like a `v1beta2` FlowSchema) to a fleet spanning Kubernetes 1.28 and 1.35 will fail on the newer clusters where the API has been removed. *Fix: Use Placement rules to segment clusters by Kubernetes version (`kube-version` claim) and maintain version-specific ManifestWork templates.*

## Quiz

**1. You are managing 300 bare-metal Kubernetes clusters deployed in retail store backrooms. The stores sit behind strict corporate firewalls that deny all inbound connections. Which fleet architecture must you adopt?**
*   A) Push-based, utilizing Argo CD centralized controllers to connect to store API servers via NodePorts.
*   B) Push-based, utilizing Karmada `PropagationPolicies` to inject manifests via SSH tunnels.
*   C) Pull-based, utilizing Open Cluster Management or Rancher Fleet agents that poll the central hub.
*   D) Pull-based, configuring Cluster API (CAPI) on the hub to sync workloads to the workload clusters.

*Correct Answer: C*
*Rationale:* A pull-based architecture requires only outbound network connections from the spoke clusters to the central hub, completely bypassing the need to open inbound firewall ports at the remote retail locations. In edge environments where you lack control over the local network ingress, an agent polling the central control plane is the only reliable communication path. Furthermore, this approach enhances security by ensuring the central hub does not hold highly privileged credentials for hundreds of remote API servers. Option D is incorrect because Cluster API provisions the underlying infrastructure, not the workload syncing mechanisms.

**2. An application team needs to deploy an application only to bare-metal clusters that possess GPU hardware and are located in the EU region. Using Open Cluster Management, how is this dynamically achieved?**
*   A) Create a `ManifestWork` containing a NodeSelector for `gpu=true` and `region=eu`.
*   B) Create a `Placement` rule on the Hub that selects `ManagedClusters` matching the required cluster claims/labels.
*   C) Create a separate Argo CD `Application` manually for every EU cluster and hardcode the GPU requirements.
*   D) Configure the Klusterlet on EU clusters to ignore `ManifestWorks` that do not contain GPU workloads.

*Correct Answer: B*
*Rationale:* Open Cluster Management leverages `Placement` rules on the hub cluster to dynamically select target `ManagedClusters` based on their labels or cluster claims. By abstracting the target selection into a distinct Placement API, the fleet manager can automatically route workloads to any cluster that meets the hardware and geographic criteria without manual intervention. Attempting to manage this at the workload level via NodeSelectors (Option A) would still push the workload to clusters without GPUs, where it would simply pend indefinitely. Hardcoding individual applications (Option C) completely negates the scalability benefits of a centralized fleet management system.

**3. You have deployed a `ManifestWork` containing 50 ConfigMaps and a massive set of custom Prometheus Rules. The `kubectl apply` command fails against the Hub cluster with an API server error, though the YAML is syntactically valid. What is the most likely cause?**
*   A) The Spoke cluster lacks the memory to run the ConfigMaps.
*   B) The `ManifestWork` exceeded the Hub's etcd object size limit (typically 1.5MB).
*   C) The Klusterlet agent timed out while parsing the Prometheus Rules.
*   D) The Hub cluster requires a `StorageClass` to store `ManifestWorks`.

*Correct Answer: B*
*Rationale:* A `ManifestWork` encapsulates all target Kubernetes resources as nested JSON within its own Custom Resource Definition structure. Etcd imposes a hard limit on the size of a single object (typically 1.5MB), meaning massive payloads will be rejected by the hub's API server before they ever reach the spoke clusters. To circumvent this, platform engineers must split large configurations across multiple `ManifestWorks` or use the fleet manager to bootstrap a lightweight continuous delivery agent that pulls the heavy manifests directly from a Git repository. Option C is incorrect because the failure occurs at the hub API server during the initial apply, not during the Klusterlet's retrieval phase.

**4. The `hubAcceptsClient` field on an OCM `ManagedCluster` resource is currently set to `false`. What state is the cluster registration in?**
*   A) The Spoke cluster has successfully joined but has no active `ManifestWorks`.
*   B) The Klusterlet agent has crashed on the Spoke cluster.
*   C) The Spoke has submitted a Certificate Signing Request (CSR), but the Hub administrator has not yet authorized the spoke to join.
*   D) The Hub API server is currently unreachable due to network partition.

*Correct Answer: C*
*Rationale:* In a zero-trust bare-metal environment, setting `hubAcceptsClient: true` serves as the explicit authorization step for a new cluster joining the fleet. Until this boolean is flipped, the hub control plane will not approve the Certificate Signing Request (CSR) generated by the spoke's Klusterlet agent during the initial bootstrap phase. The spoke cluster remains in a pending state, unable to pull `ManifestWorks` or report its status. Automating this approval process via hardware attestation or an external source of truth is a critical day-two operation for large-scale fleets.

**5. A centralized Argo CD instance is configured with a `ClusterGenerator` ApplicationSet pushing to 200 bare-metal clusters. The Argo CD `application-controller` begins OOMKilling and logs show connection timeouts to remote clusters. What is the architectural root cause?**
*   A) Argo CD requires an Enterprise license to manage more than 100 clusters.
*   B) The push-based model forces the controller to maintain active client connections and RBAC watches across 200 remote API servers, exhausting resources.
*   C) The remote bare-metal clusters are returning incompatible Kubernetes API versions.
*   D) The `ClusterGenerator` is deprecated in favor of the `ListGenerator`.

*Correct Answer: B*
*Rationale:* A pure push-based fleet architecture requires the central control plane to actively establish and maintain concurrent connections to every remote cluster's API server. As the fleet scales, this N×M connection matrix rapidly consumes memory and network sockets on the centralized controller, leading to resource exhaustion and OOMKill events. To mitigate this at scale, organizations often pivot to a pull-based model or shard their push-based controllers across multiple instances. The ApplicationSet controller natively supports scaling across multiple clusters, but the underlying push mechanism fundamentally hits infrastructure limits sooner than decoupled pull agents.

## Further Reading

*   [Open Cluster Management Official Documentation](https://open-cluster-management.io/concepts/)
*   [Argo CD ApplicationSets Architecture](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/)
*   [Rancher Fleet: GitOps at Scale](https://fleet.rancher.io/architecture)
*   [Karmada: Multi-Cloud and Multi-Cluster Kubernetes](https://karmada.io/docs/core-concepts/architecture)