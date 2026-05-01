---
title: "Module 5.7: Multi-Cluster On-Prem — Karmada Federation + Liqo Offload + kube-vip Virtual IPs"
description: "Design and operate the layered on-prem multi-cluster stack: kube-vip for virtual IPs, Karmada for federation policy, and Liqo for transparent cross-cluster offloading."
slug: on-premises/multi-cluster/module-5.7-multi-cluster-on-prem
sidebar:
  order: 57
---

# Module 5.7: Multi-Cluster On-Prem — Karmada Federation + Liqo Offload + kube-vip Virtual IPs

> **Complexity**: `[COMPLEX]` | Time: 60-70 minutes
>
> **Prerequisites**: K8s basics at CKA level, networking fundamentals, BGP or L2 familiarity helpful, Module 5.6 Gardener recommended, and at least one of Modules 5.3, 5.4, or 5.5 for multi-cluster context.

For command examples, this module uses `k` as a short alias for `kubectl`. Create it once in your shell with `alias k=kubectl` before running the hands-on work. All Kubernetes examples assume Kubernetes 1.35+ behavior unless a tool-specific command says otherwise.

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Design** an on-prem multi-cluster architecture that separates VIP advertisement, workload placement, and pod networking into clear layers.
2. **Compare** kube-vip L2 and BGP modes for control-plane HA and `LoadBalancer` Services in bare-metal environments.
3. **Evaluate** Karmada and Liqo placement models and choose the right tool for policy-driven federation or transparent workload offloading.
4. **Implement** a GitOps-driven multi-cluster deployment pattern using ApplicationSet generators and Karmada propagation policy.
5. **Diagnose** failover, ARP, BGP, peering, and namespace offloading failures across a two-cluster on-prem fleet.

---

## Why This Module Matters

At 02:15 on a Monday, a regional manufacturer loses the private cloud zone that hosts its warehouse API. The application itself is healthy in the second site. The container images are already cached there. The database has a tested replica.

The operators can even reach the second cluster by kubeconfig. Yet the warehouse scanners keep calling the dead site because the original `LoadBalancer` Service never had a real load balancer behind it. The cloud migration plan assumed EKS-style integration: create a Service, let the provider allocate a VIP, publish DNS, and move on. On-prem, there was no ALB, no managed network load balancer, no Route 53 health check, and no global front door like Google Front End.

The cluster had Kubernetes APIs, but the surrounding network promises were missing. The outage lasted hours because every layer had been treated as somebody else's problem. Networking expected Kubernetes to publish routes. Kubernetes expected a cloud controller to assign external IPs.

The application team expected GitOps to place workloads in both sites. GitOps expected clusters to be interchangeable. None of those expectations were wrong in a public-cloud cluster. Together, they were wrong on bare metal.

This module is about closing that gap without pretending on-prem behaves like a hyperscaler. You will build a layered mental model. kube-vip gives each cluster real L4 addresses for the API server and Services. Karmada gives the fleet a policy-driven control plane for scheduling, propagation, override, and failover.

Liqo gives teams a different abstraction: remote capacity appears as virtual nodes and namespaces can extend across cluster boundaries. The skill is not memorizing three tools. The skill is deciding which layer owns which responsibility, then debugging the failure when the layers disagree.

---

## 1. Why On-Prem Multi-Cluster Needs Different Tools Than Cloud

Cloud Kubernetes hides a large amount of infrastructure behind a small YAML object. When a team creates `type: LoadBalancer` in EKS, AKS, or GKE, the cloud controller talks to the provider API. That provider API allocates a load balancer, attaches nodes or network endpoints, opens firewall rules, and writes an external address back into Service status. When the same team creates an Ingress, another controller may create an ALB, Application Gateway, or Google Cloud load balancer.

DNS automation then points a name at the provider-managed endpoint. This is why a cloud quickstart feels so simple. The cluster is only one part of the system. The cloud is quietly supplying identity, routing, L4 or L7 balancing, health checks, IAM, quotas, logging sinks, and API-driven inventory.

On-premises clusters do not get those services by default. A rack of servers may have excellent switches, routers, firewalls, and storage. It does not automatically have a Kubernetes-aware load balancer. It does not automatically have a global identity plane that lets one cluster impersonate a workload in another cluster.

It does not automatically have a regional control plane that can decide where replicas should run when a site fails. That means multi-cluster is not a feature you add at the end. It is part of the platform design from the beginning. The first missing cloud primitive is the external load balancer.

Without it, `type: LoadBalancer` commonly remains in `EXTERNAL-IP: <pending>`. The Kubernetes Service object exists, but no system outside the cluster has claimed responsibility for making that IP reachable. kube-vip fills that gap by advertising virtual IPs from cluster nodes using ARP in L2 mode or BGP in L3 mode. It can advertise the control-plane endpoint for kubeadm HA.

It can also advertise application Service addresses when paired with kube-vip's cloud provider. Those are separate use cases and should be designed separately. The second missing cloud primitive is the cross-region policy plane. In a cloud provider, cluster identity, service accounts, tags, IAM roles, and provider APIs often become the glue that decides who can deploy where.

On-prem, you usually own that glue. Karmada supplies Kubernetes-native policy objects for fleet placement. Its `Cluster`, `PropagationPolicy`, `OverridePolicy`, and binding resources let a platform team express where workloads should land and how they should change per cluster. The third missing cloud primitive is the global control plane.

GKE has a mature global networking and control-plane story around Google infrastructure. EKS can lean on AWS accounts, Route 53, ALB, NLB, IAM, and Global Accelerator patterns. An on-prem fleet has clusters, networks, and identities that are often assembled from different vendors and operational teams. Federation must therefore be explicit.

It is not an afterthought. It is an architecture. There is also a cultural difference. Public-cloud clusters tend to have a clear provider boundary.

If a load balancer fails, the incident splits into provider state, controller state, and application state. On-prem, the same incident may involve Kubernetes operators, network engineers, firewall administrators, storage teams, and application owners. The platform must create shared language across those teams. This module uses three layers for that shared language.

The first layer is VIP advertisement. The second layer is multi-cluster orchestration. The third layer is pod networking inside each cluster. Do not collapse those layers into one tool.

That collapse is the beginning of most painful incidents. Pause and predict: what do you think happens if a team installs Karmada but leaves every `LoadBalancer` Service in `<pending>` on the member clusters? The answer is that Karmada may distribute the manifests correctly while users still cannot reach the applications.

Federation does not replace L4 reachability. It decides where objects go. Another system must make the resulting endpoints usable.

---

## 2. kube-vip Foundation

kube-vip is the bottom layer in this design. It is not a fleet scheduler. It is not a GitOps controller. It is not a service mesh.

It is a virtual IP and load-balancer implementation for Kubernetes environments that do not have a cloud provider assigning addresses for them. The core idea is simple. A VIP is an IP address that can move between nodes. Clients connect to the VIP rather than to a specific node.

If the node currently holding the VIP fails, another node takes ownership and advertises the new location. The details depend heavily on whether the network learns that location through ARP or BGP. In L2 mode, kube-vip uses ARP announcements. One kube-vip instance becomes leader for a VIP.

That leader places the VIP on a node interface and sends gratuitous ARP messages so neighbors update their IP-to-MAC mapping. This is attractive for small subnets because the routers do not need BGP configuration. It also means the VIP can usually live only inside the broadcast domain where ARP works. L2 mode is operationally friendly until the broadcast domain becomes too large or too noisy.

ARP flooding, stale ARP caches, switch security features, and virtual-switch behavior can all stretch failover time. Some environments limit gratuitous ARP updates. Others rate-limit them. When that happens, kube-vip may elect a new leader quickly while clients continue sending packets to the old MAC address.

In BGP mode, kube-vip speaks to routers. Instead of telling nearby hosts "this IP is at this MAC," it tells network peers "this node can reach this VIP prefix." That makes BGP the better fit for routed data centers, multi-rack designs, and active-active site patterns. It also introduces router configuration, AS numbers, peer reachability, route filters, and BGP session health.

BGP mode trades L2 simplicity for L3 control. kube-vip has two distinct jobs that are easy to confuse. The first job is the Kubernetes control-plane VIP. For kubeadm HA, the API server endpoint should be stable even if one control-plane node fails.

kube-vip can run as a static pod on every control-plane node and advertise that stable API VIP before the cluster is fully bootstrapped. That is why static pods matter. They are started by the kubelet directly from local manifest files, so they do not require the Kubernetes API to already be healthy. The second job is Service `LoadBalancer` VIPs.

After the cluster is running, users want Services to receive external IPs. kube-vip can advertise those Service addresses. The kube-vip cloud provider can allocate addresses from configured ranges and write them into the Service status. Then kube-vip advertises the assigned address through ARP or BGP.

That makes kube-vip a bare-metal alternative to MetalLB for teams that want one project to handle both control-plane VIPs and Service VIPs. The two jobs share mechanics but not risk. If the control-plane VIP breaks, operators may lose access to the cluster API. If a Service VIP breaks, an application endpoint is affected.

Treat those as separate failure domains. Use separate addresses. Use separate monitoring.

Document which VIPs are allowed to move between which nodes. Here is a static-pod manifest shaped for kubeadm control-plane HA with ARP mode. In production, generate the current manifest with the matching kube-vip version, then review the output before placing it under `/etc/kubernetes/manifests/`.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-vip
  namespace: kube-system
spec:
  containers:
    - name: kube-vip
      image: ghcr.io/kube-vip/kube-vip:v0.8.9
      args:
        - manager
      env:
        - name: vip_arp
          value: "true"
        - name: port
          value: "6443"
        - name: vip_interface
          value: "eth0"
        - name: vip_cidr
          value: "32"
        - name: cp_enable
          value: "true"
        - name: cp_namespace
          value: kube-system
        - name: vip_ddns
          value: "false"
        - name: svc_enable
          value: "false"
        - name: address
          value: "192.168.30.10"
        - name: prometheus_server
          value: ":2112"
      securityContext:
        capabilities:
          add:
            - NET_ADMIN
            - NET_RAW
      volumeMounts:
        - mountPath: /etc/kubernetes/admin.conf
          name: kubeconfig
  hostNetwork: true
  volumes:
    - hostPath:
        path: /etc/kubernetes/admin.conf
      name: kubeconfig
```

The manifest shows the important shape rather than a universal copy-paste answer. `hostNetwork: true` allows the pod to manipulate the node network. The VIP address is explicit. The interface is explicit.

The capability set is network-focused. The service feature is off here because this example is about the API server endpoint. For Service VIPs, deploy kube-vip as a DaemonSet after the cluster is ready and install the kube-vip cloud provider. The cloud provider assigns addresses.

The kube-vip DaemonSet advertises them. That split gives the Kubernetes Service controller a normal place to write status. A useful production runbook has three checks. First, check leader election.

Second, check whether the VIP is present on exactly the expected node or advertised by the expected BGP speakers. Third, check whether upstream network state changed. Kubernetes events alone are not enough. You must inspect the network.

Common kube-vip gotchas are predictable. ARP mode can suffer when switches suppress gratuitous ARP. Large L2 domains can make failover noisy. Split-brain can happen if two nodes believe they are leader for the same VIP.

BGP mode can fail quietly if the AS number, peer address, router ID, source address, or route filter is wrong. ECMP can spray connections across nodes in ways the application path did not expect. Before running this in production, what output do you expect from `ip addr show`, `arp -an`, and `show bgp` on your routers after a VIP failover? If the team cannot answer, the runbook is not ready.

---

## 3. Karmada: Federation as Control Plane

Karmada sits above individual clusters. Its job is to make Kubernetes resources fleet-aware without requiring every application team to hand-apply the same manifest to every cluster. Think of it as a Kubernetes-compatible control plane that stores desired state for many member clusters. You talk to Karmada with Kubernetes APIs.

Karmada then decides where resources should be placed and creates work objects for member clusters. The main Karmada resource types form a pipeline. `Cluster` represents a joined member cluster. It stores mode, readiness, capacity, labels, and taints.

`PropagationPolicy` selects namespaced resources and describes placement rules. `ClusterPropagationPolicy` does the same at cluster scope. `OverridePolicy` changes selected fields when a resource is propagated to specific clusters. `ResourceBinding` records the scheduling result for one selected resource.

Those objects are not decorative. They are the audit trail for why a workload landed where it did. If a Deployment appears in the wrong cluster, do not start by editing the member cluster. Start at the Karmada policy and binding.

The control plane contains familiar pieces. `karmada-apiserver` is the Kubernetes-compatible API endpoint. ETCD stores Karmada API objects. `karmada-scheduler` selects clusters for resources.

`karmada-controller-manager` runs controllers that watch policies, create bindings, create work objects, aggregate status, and manage cluster state. Additional components handle webhook, aggregated API, metrics, and member-cluster agents depending on installation mode. Karmada supports push and pull registration modes. In push mode, the Karmada control plane connects directly to the member cluster API server.

This is simple when the control plane can reach every member cluster. It is common in a single data center or a well-routed internal network. In pull mode, a `karmada-agent` runs in the member cluster. The agent watches its execution space in Karmada and pulls work down to the cluster.

Pull mode is useful when member clusters cannot be directly reached from the hub or when firewall rules strongly favor outbound connections from the cluster. Do not choose push or pull as a style preference. Choose it from network reality. If the hub cannot reliably initiate connections to a remote API server, push mode will become a recurring incident.

If your security team wants every member cluster to hold only a scoped agent credential, pull mode may be easier to approve. If you need simple local testing, push mode is usually faster. Placement starts with `PropagationPolicy`. The policy selects resources by API version, kind, name, namespace, and labels.

Then it expresses placement through cluster affinity, spread constraints, replica scheduling strategy, tolerations, and failover behavior. Cluster affinity narrows the candidate set. Weight-based scheduling decides how replicas should be divided when more than one cluster is eligible. Failover controls how Karmada reacts when a cluster becomes unhealthy or tainted for eviction. Here is a policy that selects an `nginx` Deployment in the `demo` namespace and divides replicas between two clusters with explicit weights.

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: nginx-fleet-policy
  namespace: demo
spec:
  resourceSelectors:
    - apiVersion: apps/v1
      kind: Deployment
      name: nginx
  placement:
    clusterAffinity:
      clusterNames:
        - kind-cluster-a
        - kind-cluster-b
    replicaScheduling:
      replicaSchedulingType: Divided
      replicaDivisionPreference: Weighted
      weightPreference:
        staticWeightList:
          - targetCluster:
              clusterNames:
                - kind-cluster-a
            weight: 1
          - targetCluster:
              clusterNames:
                - kind-cluster-b
            weight: 2
    spreadConstraints:
      - spreadByField: cluster
        maxGroups: 2
        minGroups: 2
  failover:
    cluster:
      purgeMode: Gracefully
```

This policy encodes intent. Cluster B receives more weight, but both clusters are candidates. If Cluster A becomes unavailable and Karmada failover is enabled, replicas can be rescheduled according to the failover behavior and the remaining candidate clusters. The `ResourceBinding` then becomes the diagnostic object that shows the final placement decision.

Karmada differs from the older Kubefed v2 model in both ambition and maintenance reality. Kubefed v2 focused on federated resource types and template, placement, and override resources. It taught the ecosystem useful lessons but did not become the dominant multi-cluster control plane. Karmada keeps a Kubernetes-native API experience while building richer scheduling, propagation, failover, status aggregation, and large-fleet behavior.

The operational message is simple: do not use old Kubefed habits as your design baseline. Evaluate Karmada as its own control plane. A practical Karmada debugging path is short and repeatable. Check the `Cluster` readiness and taints.

Check the `PropagationPolicy` selector. Check the `ResourceBinding` scheduling result. Check the generated `Work` objects. Then check the member cluster. Most teams reverse that order and waste time staring at a Deployment that Karmada is continuously reconciling.

---

## 4. Liqo: Federation as Continuum

Liqo approaches multi-cluster from a different direction. Instead of making a central policy plane the primary abstraction, it makes remote resources appear inside a local cluster. A remote cluster becomes a virtual node. Pods can be scheduled to that virtual node.

Namespaces can be extended. Selected resources are reflected. The goal is transparent multi-cluster execution: existing workload YAML should need little or no change. This is a powerful mental shift.

With Karmada, the fleet control plane decides where a resource should be propagated. With Liqo, a local cluster can consume capacity from a peer. The local Kubernetes scheduler sees virtual capacity and places pods as if the remote cluster were part of the local resource pool. The remote side receives reflected resources and runs the actual pods.

Peering is the relationship that makes this possible. Modern Liqo describes peering as a resource and service consumption relationship. One cluster acts as consumer. The other acts as provider.

Bidirectional behavior is built by creating peerings in both directions. That is important because a peering is not automatically symmetric. In-band peering is useful when the operator machine can reach both clusters and Liqo can configure the required authentication and networking flow directly. Out-of-band peering is useful when connectivity or organizational boundaries require exchanging generated artifacts through another channel.

In production, the choice often comes down to firewall policy and who is allowed to hold kubeconfigs for both sides at the same time. Virtual nodes are how Liqo becomes visible to Kubernetes users. After peering, the consumer cluster can show a node that represents the provider cluster. The virtual node advertises shared CPU, memory, pod capacity, labels, and taints.

The default taints are intentional. They keep ordinary pods from accidentally leaving the cluster until namespace offloading or runtime class rules allow it. Namespace mapping is the next key idea. When a namespace is offloaded, Liqo extends that namespace to selected remote clusters.

Resources required by the pod can be reflected. That includes objects such as ConfigMaps, Secrets, and Services according to Liqo's reflection behavior and configuration. The developer continues working in the original namespace. The remote namespace acts as the hosting side where the offloaded pod actually runs.

Network reflection makes the pattern usable. If pods move to another cluster but cannot reach the Services and endpoints they expect, transparency breaks. Liqo creates cross-cluster networking components so offloaded workloads can communicate across cluster boundaries.

That does not remove the need for network design. It creates a Kubernetes-native path for workloads whose YAML was not written for multi-cluster. A basic peering command looks like this:

```bash
liqoctl peer \
  --kubeconfig "$HOME/.kube/kind-cluster-a" \
  --context kind-kind-cluster-a \
  --remote-kubeconfig "$HOME/.kube/kind-cluster-b" \
  --remote-context kind-kind-cluster-b \
  --gw-server-service-type NodePort \
  --skip-confirm
```

After peering, a virtual node should appear from the consumer side.

```bash
KUBECONFIG="$HOME/.kube/kind-cluster-a" k get nodes -o wide
```

Expected shape:

```text
NAME                                      STATUS   ROLES           AGE   VERSION
kind-cluster-a-control-plane             Ready    control-plane   18m   v1.35.x
kind-cluster-a-worker                    Ready    <none>          18m   v1.35.x
liqo-remote-kind-cluster-b               Ready    agent           3m    v1.35.x
```

The exact virtual node name can vary by Liqo version and cluster identity. The operational signal is that the node is present, Ready, and labeled as a Liqo virtual node. If it is missing, inspect peering status before debugging pod scheduling. Transparent does not mean invisible to operators.

Transparent means application YAML can remain mostly unchanged. Operators still need to understand authentication bootstrap, gateway Services, tunnel MTU, namespace offloading strategy, reflected resources, and remote capacity quotas. Liqo makes cross-cluster execution feel natural to developers. It does not remove the platform responsibility for isolation and reachability.

---

## 5. Karmada vs Liqo Decision Matrix

Karmada and Liqo both solve multi-cluster problems. They do not solve the same problem in the same way. Choosing between them by popularity or installation ease is a mistake. Choose by the control model you want users to experience.

Karmada is strongest when the platform team wants explicit placement policy. It is good when auditability matters. It is good when different clusters need different overrides. It is good when failover behavior must be expressed centrally.

It is good when RBAC, fleet policy, and resource propagation should be managed through a hub control plane. Liqo is strongest when the application team wants remote capacity with minimal manifest change. It is good when burst, overflow, edge-to-core, or temporary drain workflows matter. It is good when the developer can keep thinking in terms of a namespace while the platform makes that namespace span clusters.

It is good when virtual nodes fit the team’s mental model better than fleet placement rules. Both tools can coexist. In a real on-prem platform, kube-vip can provide VIPs in every cluster. Karmada can propagate platform workloads and shared services according to policy.

Liqo can offload selected namespaces for burst or site drain scenarios. The coexistence rule is to avoid making both tools responsible for the same workload at the same time. Use labels, namespaces, ownership rules, and GitOps boundaries to keep responsibilities clear.

| Dimension | Karmada | Liqo | Design Guidance |
|---|---|---|---|
| Primary abstraction | Fleet control plane and policy | Virtual nodes and extended namespaces | Pick Karmada when the hub should decide; pick Liqo when the source cluster should consume remote capacity. |
| Workload YAML impact | Usually paired with policy objects | Existing workload YAML often stays the same | Liqo wins for zero-change portability; Karmada wins when policy is part of the release artifact. |
| Placement model | `PropagationPolicy`, affinities, spread, weights, failover | Kubernetes scheduler targets virtual nodes after namespace offloading | Use Karmada for explicit fleet placement; use Liqo for scheduler-native offload. |
| Failure behavior | Central failover and cluster taints | Drain, offload, and reschedule through virtual node behavior | Karmada is clearer for audited DR policy; Liqo is smoother for regional drain of a namespace. |
| RBAC and governance | Strong hub-level governance model | Source-cluster governance plus peering controls | Karmada fits central platform teams; Liqo fits capacity-sharing agreements. |
| Network expectation | Member clusters must receive propagated objects and expose their own Services | Cross-cluster networking is part of the experience | Do not expect Karmada to create network tunnels; do not expect Liqo to replace fleet policy. |
| Best fit | Regulated fleet placement, shared add-ons, controlled failover | Burst, edge offload, namespace mobility, transparent portability | Many platforms use both in different namespaces. |

Here is a practical decision rule. If the question starts with "which clusters should receive this application and with what overrides," start with Karmada. If the question starts with "can this namespace keep its YAML but borrow remote capacity," start with Liqo. If the question starts with "why is the external IP pending," neither tool is the answer. Start with kube-vip or another bare-metal load-balancer implementation.

---

## 6. Layered Architecture Pattern

The central design fork in on-prem multi-cluster is whether the team treats the stack as one magical federation layer or as three separate layers. Use the separate-layer model. kube-vip sits below the fleet tools. It gives each cluster L4 reachability for the API server and Service VIPs.

Karmada or Liqo sits above that and decides how workloads or capacity cross cluster boundaries. Each cluster's CNI handles pod networking inside the cluster. If Liqo is enabled, its networking components extend selected cross-cluster paths. If Karmada is enabled, each member cluster still exposes its own Service through its own networking and VIP layer.

```text
+--------------------------------------------------------------------------------+
|                         Multi-Cluster Platform Layer                            |
|                                                                                |
|  Karmada: PropagationPolicy, OverridePolicy, ResourceBinding, failover          |
|  Liqo: peering, virtual nodes, namespace offloading, resource reflection        |
+-----------------------------------------+--------------------------------------+
                                          |
                 workload placement       |       transparent offload
                                          |
+---------------------------+             |             +------------------------+
| Cluster A                 |             |             | Cluster B              |
|                           |             |             |                        |
| +-----------------------+ |             |             | +--------------------+ |
| | kube-vip VIP Layer    | |             |             | | kube-vip VIP Layer | |
| | API VIP + Service VIP | |             |             | | API VIP + Service  | |
| +-----------------------+ |             |             | +--------------------+ |
| +-----------------------+ |             |             | +--------------------+ |
| | CNI Pod Network       | |<-- Liqo --> | <-- Liqo -->| | CNI Pod Network    | |
| | Calico/Cilium/etc.    | |   tunnel    |   tunnel    | | Calico/Cilium/etc. | |
| +-----------------------+ |             |             | +--------------------+ |
| +-----------------------+ |             |             | +--------------------+ |
| | Nodes and workloads   | |             |             | | Nodes and workloads| |
| +-----------------------+ |             |             | +--------------------+ |
+---------------------------+             |             +------------------------+
                                          |
                         Routed or L2 data center network
```

The example interaction is concrete. A platform engineer applies a Deployment and Service to the Karmada control plane. A `PropagationPolicy` selects that Deployment and sends it to Cluster B. Cluster B creates the Deployment and its Service locally.

The Service is `type: LoadBalancer`. The kube-vip cloud provider in Cluster B allocates a VIP. The kube-vip DaemonSet in Cluster B advertises that VIP through ARP or BGP. No cloud load balancer exists in either cluster.

Nothing in Karmada magically publishes a routed IP. Nothing in kube-vip decides fleet placement. That separation is healthy. It means the network team can reason about VIP advertisement.

The platform team can reason about placement policy. The application team can reason about Service and Deployment behavior. When an incident happens, the layers give you a diagnostic order. Is the workload placed in the expected cluster?

If not, inspect Karmada or Liqo. Is the Service assigned a VIP? If not, inspect the kube-vip cloud provider and address pool. Is the VIP advertised?

If not, inspect kube-vip leader election, ARP, or BGP. Do packets arrive but pods do not respond? Inspect kube-proxy, CNI, NetworkPolicy, endpoint health, and application readiness. The layered model also prevents overreach.

A team may want one tool to do everything because one tool feels easier to explain. That simplicity is usually temporary. At scale, a single overloaded abstraction makes every failure ambiguous.

Keep the layers explicit. Document ownership at each layer. Test each layer independently.

---

## 7. GitOps Pattern for Multi-Cluster

GitOps becomes more important as clusters multiply. Manual commands do not scale across a fleet. Neither does one repository per cluster when every repository repeats the same application with tiny differences. The goal is to keep one source of truth while still allowing cluster-specific parameters.

Argo CD ApplicationSet is a common answer. Its generators create many `Application` resources from a template. A cluster generator can fan out to clusters registered in Argo CD. A list generator can make a small explicit fleet.

A matrix generator can combine environments, applications, and clusters. For a Karmada pattern, Argo CD can deploy to the Karmada API server rather than to each member cluster directly. The repository contains ordinary Kubernetes manifests plus Karmada policies. ApplicationSet creates one application per fleet slice or environment.

Karmada then propagates selected resources to member clusters. This avoids per-cluster repositories while preserving fleet placement in policy. Here is a compact ApplicationSet that deploys one application template for two fleet environments.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: fleet-nginx
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: prod
            destinationName: karmada-prod
            path: apps/nginx/overlays/prod
          - env: stage
            destinationName: karmada-stage
            path: apps/nginx/overlays/stage
  template:
    metadata:
      name: nginx-{{env}}
    spec:
      project: default
      source:
        repoURL: https://github.com/example-org/platform-apps.git
        targetRevision: main
        path: "{{path}}"
      destination:
        name: "{{destinationName}}"
        namespace: demo
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

The overlay can include both the Deployment and the Karmada policy.

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: nginx-prod-placement
  namespace: demo
spec:
  resourceSelectors:
    - apiVersion: apps/v1
      kind: Deployment
      name: nginx
    - apiVersion: v1
      kind: Service
      name: nginx
  placement:
    clusterAffinity:
      labelSelector:
        matchLabels:
          environment: prod
    spreadConstraints:
      - spreadByField: cluster
        minGroups: 2
        maxGroups: 2
```

In this pattern, Argo CD owns desired state in the Karmada control plane. Karmada owns propagation to member clusters. Member clusters own runtime reconciliation of the resulting Kubernetes objects. kube-vip owns VIP assignment and advertisement inside each member cluster.

The Liqo GitOps pattern looks different. Argo CD can deploy ordinary manifests to the source cluster. The namespace offloading configuration decides whether pods from that namespace may land on virtual nodes. The application repository may not need per-cluster overlays at all.

Instead, the platform repository owns Liqo peering, namespace offloading, resource quotas, and labels. That makes Liqo attractive when the application team should not need to learn a fleet policy language. The risk is hidden placement. If developers see only the source namespace, they may not realize their pods are running in another failure domain.

Use labels, dashboards, alerts, and resource views that make offloaded execution visible. GitOps should reduce ambiguity, not create it. Pause and predict: if Argo CD syncs a Deployment to Karmada and Karmada propagates it to Cluster B, where should you look for drift?

There are three places. Look at the Git desired state, the Karmada object and binding, and the member cluster object. The system is only healthy when all three agree about the intended state.

---

## 8. Disaster Recovery and Traffic Shaping

Disaster recovery in this stack is not one feature. It is the choreography of several layers. kube-vip handles VIP movement and route advertisement. Karmada handles cluster-aware workload failover.

Liqo handles namespace offloading and drain-style movement when the source cluster can still participate. Your runbook should say which layer acts first for each failure type. For active-active service exposure across sites, kube-vip BGP is the stronger fit. Each site can advertise the same VIP or site-specific VIPs to upstream routers.

If two BGP peers announce the same /32 and the upstream network accepts equal-cost paths, ECMP can distribute traffic. If one site fails and withdraws the route, the upstream network converges to the remaining site. That looks simple on a whiteboard. In production, ECMP must be tested with the actual application traffic.

Long-lived TCP sessions, asymmetric routing, stateful firewalls, and source NAT behavior can all affect results. For Karmada failover, the key signal is cluster health and taints. Karmada can mark clusters unavailable and use taints such as not-ready or unreachable to prevent scheduling or trigger eviction behavior when failover features are enabled. `DisruptionPolicy` and related failover configuration should be treated as application policy.

Some workloads can tolerate immediate replacement. Others need graceful purge, state preservation, or manual database promotion. Do not enable failover semantics without defining what happens to state. For Liqo, the regional-drain story is different.

If Cluster A is degrading but still reachable, you can offload a namespace to Cluster B and let pods reschedule through the virtual node abstraction. That is useful for maintenance, capacity pressure, and edge-site evacuation. It is less useful when Cluster A has already disappeared and no control plane can coordinate the drain. Liqo is strongest before total failure.

Karmada is stronger when a fleet control plane must react to member-cluster health. Consider a concrete failure scenario. Two sites run the same stateless API. Cluster A is near the warehouse floor.

Cluster B is in a nearby data center. Both clusters run kube-vip. Karmada places four replicas across both clusters with a higher weight on Cluster A. Liqo is configured for a batch-processing namespace that can borrow Cluster B capacity during maintenance.

At 01:20, the top-of-rack switch in Site A begins dropping packets. The first symptom is not a pod failure. It is BGP session flapping from kube-vip speakers to the upstream router. The router withdraws and re-adds the VIP route.

Clients see intermittent connection resets. The network team confirms the route flap. The platform team taints Cluster A in Karmada or waits for health detection, depending on the runbook. Karmada stops placing new work there and starts moving eligible replicas to Cluster B.

Cluster B's kube-vip advertises the Service VIP for the copy running there. For the batch namespace, the team uses Liqo offloading or drain behavior before shutting down local nodes. Each action is layer-specific. Nobody asks Liqo to fix BGP.

Nobody asks kube-vip to decide workload policy. Nobody asks Karmada to tunnel pod traffic. That separation makes the incident manageable. The best DR tests are not happy-path demos.

Test BGP peer loss. Test stale ARP cache behavior. Test Karmada cluster `Ready` becoming `Unknown`.

Test a member cluster that is reachable from users but unreachable from the Karmada hub. Test Liqo peering where the gateway Service is reachable but the tunnel MTU breaks larger packets. DR confidence comes from failure evidence, not architecture diagrams.

---

## 9. Production Concerns

Production multi-cluster operations are mostly about visibility, identity, scaling, and network edge cases. The tools work only as well as those foundations. Observability must be fleet-aware. Per-cluster Prometheus is useful for local debugging.

It is not enough for questions like "which cluster is losing Karmada work propagation latency" or "which site has kube-vip leader churn." Use a global metrics layer such as Thanos or Grafana Mimir to query across clusters. Keep cluster labels on every metric path. For Karmada, scrape control-plane metrics, scheduler metrics, controller-manager metrics, API server metrics, and member-cluster status.

For kube-vip, alert on leader changes, BGP session state, VIP advertisement failures, and Service assignment failures. For Liqo, alert on peering status, virtual node readiness, gateway health, offloading status, and tunnel packet loss. Security starts with cross-cluster identity. Karmada needs kubeconfigs or agents that can apply resources to member clusters.

Those credentials should be scoped, rotated, and stored with the same care as production cluster-admin access. Push mode often means the hub holds credentials that reach into members. Pull mode moves more responsibility to the member agent. Neither mode is automatically acceptable to every security team.

Design the trust model explicitly. Liqo performs authentication bootstrap between clusters and establishes a peering relationship that allows resource consumption. That relationship should be approved like any other capacity-sharing or trust boundary. Use mTLS where the tool supports it.

Constrain which namespaces can offload. Constrain which remote clusters can receive workloads. Decide whether Secrets are allowed to reflect across boundaries. Document who can create or modify peering resources.

Network security is not optional. kube-vip ARP mode means nodes can claim VIPs on a subnet. That is powerful and potentially disruptive if address ranges are not controlled. BGP mode means Kubernetes nodes or pods can influence routing.

Use route filters, prefix limits, BGP authentication where supported, and router-side policy. Monitor not just Kubernetes objects but the actual routing state. Scaling Karmada is a control-plane engineering problem. ETCD compaction and defragmentation matter when many propagated resources and bindings churn.

Scheduler throughput matters when many workloads are rescheduled after a site event. Controller-manager worker counts and API QPS settings matter when clusters reconnect after a network partition. Status aggregation can become expensive if every workload reports frequently across many clusters. Treat the Karmada control plane like a production Kubernetes control plane, not a sidecar.

kube-vip BGP has its own sharp edges. ECMP asymmetry can send request and response paths through different firewalls. BGP session flaps can create short but frequent outages. Route dampening can punish a speaker that flaps too often.

Peer configuration errors can make a VIP appear healthy in Kubernetes while absent from the network. If ARP mode is used, ARP cache TTL and switch behavior affect failover perception. Tune the network with the network team, not in a Kubernetes-only meeting. Operational ownership should be written down.

The platform team usually owns Karmada and Liqo control planes. The cluster team owns kube-vip manifests and address pools. The network team owns BGP peers, route policy, VLANs, and firewall paths.

The application team owns readiness, state behavior, and whether failover is acceptable. Good on-prem multi-cluster platforms make those boundaries explicit. Weak platforms discover them during incidents.

---

## Patterns & Anti-Patterns

### Patterns

| Pattern | When to Use | Why It Works | Scaling Consideration |
|---|---|---|---|
| VIP below federation | Every on-prem multi-cluster fleet | Fleet placement does not matter unless each cluster can expose reachable endpoints | Standardize address pools and route policy before onboarding many teams. |
| Karmada for platform-owned placement | Shared add-ons, regulated apps, controlled failover | Placement and overrides become auditable Kubernetes resources | Watch binding and work object volume as clusters and resources grow. |
| Liqo for namespace offload | Burst, regional drain, edge-to-core movement | Existing workload YAML can keep using a local namespace model | Keep offloading policies visible so teams know where pods actually run. |
| GitOps through the hub | Teams need one repo and many clusters | ApplicationSet can render fleet applications while Karmada handles propagation | Avoid mixing direct-to-member and hub-driven ownership for the same object. |

### Anti-Patterns

| Anti-Pattern | Why Teams Fall Into It | Better Alternative |
|---|---|---|
| Treating `LoadBalancer` as automatic on bare metal | Cloud experience trains teams to expect provider integration | Install and test kube-vip or another bare-metal load-balancer layer first. |
| Letting Karmada and Liqo both manage the same namespace | Both tools can make workloads appear elsewhere | Split by namespace, label, or application ownership. |
| Using BGP without router-side guardrails | Kubernetes teams can make routing changes faster than network review | Use prefix filters, peer limits, and change windows for routing policy. |
| Hiding virtual nodes from developers | Transparency is mistaken for secrecy | Show offloaded pods, virtual-node labels, and remote cluster identity in dashboards. |
| Putting all Services behind one ARP leader | It is the default in many simple examples | Use per-Service election or BGP where traffic distribution matters. |

---

## Decision Framework

Use this flow when designing an on-prem multi-cluster feature.

```text
Start
  |
  v
Do users need an external IP for a Service or API endpoint?
  |
  +-- yes --> Design kube-vip or equivalent VIP advertisement first.
  |
  +-- no ----+
            |
            v
Do you need central policy for where resources land?
  |
  +-- yes --> Use Karmada policies, bindings, overrides, and failover.
  |
  +-- no ----+
            |
            v
Do you want an existing namespace to borrow remote capacity?
  |
  +-- yes --> Use Liqo peering, virtual nodes, and namespace offloading.
  |
  +-- no ----+
            |
            v
Can plain per-cluster GitOps solve it?
  |
  +-- yes --> Keep the design simple and avoid federation for this workload.
  |
  +-- no --> Revisit requirements and define the missing layer explicitly.
```

The framework is intentionally blunt. Most poor designs begin by jumping directly to federation. Federation is not a substitute for an IP address. It is not a substitute for DNS.

It is not a substitute for application state design. It is a tool for controlling where Kubernetes resources or capacity relationships exist. Use Karmada when the platform needs strong placement.

Use Liqo when the namespace should stretch. Use kube-vip when the cluster needs a reachable VIP. Use all three only when each has a separate job.

---

## Did You Know?

1. kube-vip supports both control-plane VIPs and Service `LoadBalancer` VIPs, but those are separate features that can be enabled independently.

2. Karmada's current architecture includes a Kubernetes-compatible API server, ETCD, scheduler, and controller manager, so operating it resembles operating a real control plane.

3. Liqo peering is directional: a consumer can offload to a provider, and bidirectional behavior requires configuring the reverse relationship as well.

4. Kubernetes `type: LoadBalancer` relies on an implementation outside the Service object to allocate and publish an address, which is why bare-metal clusters often show `<pending>` until a controller such as kube-vip cloud provider is installed.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Installing Karmada before proving Service VIP reachability | Federation feels like the bigger problem, so teams skip the network base | Create a test `LoadBalancer` Service in every member cluster and verify the VIP from outside the cluster first. |
| Reusing the control-plane VIP range for application Services | The address plan starts as a lab shortcut | Separate API VIPs, internal Service VIPs, and external Service VIPs into documented pools. |
| Choosing ARP mode across routed sites | ARP works in the first rack and gets copied into the WAN design | Use BGP or site-local VIPs with DNS/GSLB when crossing L3 boundaries. |
| Treating Liqo virtual nodes like ordinary physical nodes | The scheduler output looks familiar | Check Liqo labels, taints, namespace offloading status, and remote capacity before assuming local-node behavior. |
| Debugging propagated workloads only in member clusters | The failed object is visible there, so operators start there | Trace Karmada `PropagationPolicy`, `ResourceBinding`, and `Work` before editing the member copy. |
| Allowing Secret reflection without a policy review | Transparent offload makes cross-cluster data movement easy | Define which namespaces may reflect Secrets and audit peering permissions. |
| Ignoring BGP route state during kube-vip incidents | Kubernetes events look green | Check router sessions, advertised prefixes, route filters, and ECMP paths as part of the runbook. |

---

## Quiz

<details>
<summary>Your team propagated a Deployment with Karmada, and the pods are healthy in Cluster B, but users still cannot connect to the Service. What do you check first?</summary>

Start by separating placement from reachability. Karmada has already done its part if the Deployment and Service exist in Cluster B. Check whether the Service in Cluster B has an external VIP, then check kube-vip cloud provider logs and kube-vip advertisement state. If a VIP exists, inspect ARP or BGP state from the network side before changing Karmada policy.

</details>

<details>
<summary>A site uses kube-vip ARP mode, and failover works in one switch but takes much longer in another. How do you diagnose it?</summary>

Compare Kubernetes leader election timing with network convergence timing. If leadership changes quickly but clients keep using the old MAC address, the problem is likely ARP propagation, cache behavior, or switch policy. Check gratuitous ARP handling, ARP cache TTL, port security, and virtual-switch features. The fix belongs in network behavior as much as in Kubernetes configuration.

</details>

<details>
<summary>An application team wants zero-change workload portability into a second cluster for short capacity bursts. Should you start with Karmada or Liqo?</summary>

Start with Liqo if the key requirement is keeping the existing workload YAML and letting a namespace consume remote capacity. The virtual-node model fits burst and offload use cases well. Karmada is better when the platform wants explicit propagation policy, overrides, and audited placement decisions. The important guardrail is making offloaded execution visible to operators and developers.

</details>

<details>
<summary>A regulated workload must run only in clusters labeled `zone=internal` and needs a different image registry per cluster. Which pattern fits?</summary>

Karmada is the better fit. Use cluster affinity in `PropagationPolicy` to restrict placement and `OverridePolicy` to adjust image registry or other fields per cluster. That keeps placement and mutation in auditable policy objects. Liqo could move pods, but it is not the cleanest tool for central compliance-driven placement and override rules.

</details>

<details>
<summary>During a WAN degradation, Cluster A is still reachable by its own users but the Karmada hub cannot reach its API server. What design question does this expose?</summary>

It exposes the push-versus-pull registration decision. Push mode depends on the hub reaching the member API server. If that path is unreliable or blocked by policy, pull mode with a member-side agent may be more resilient for control-plane communication. The workload data path and the federation management path should be tested separately.

</details>

<details>
<summary>Your network team reports ECMP asymmetry after enabling kube-vip BGP from two sites. What should the platform team evaluate before changing replicas?</summary>

Evaluate whether request and response traffic cross the same stateful devices. ECMP can distribute flows across equal routes, but firewalls, NAT, and long-lived TCP sessions may not tolerate path changes. Check router hashing, firewall state tables, source NAT behavior, and whether the application needs sticky routing. Replica count changes will not fix a routing symmetry problem.

</details>

<details>
<summary>A namespace is offloaded with Liqo, but pods remain pending instead of landing on the virtual node. What should you inspect?</summary>

Inspect namespace offloading status, virtual-node readiness, taints, tolerations, runtime class settings, and remote capacity. Liqo virtual nodes are intentionally protected from accidental scheduling. Also check peering health and whether the provider accepted the resource slice. The local scheduler can only use remote capacity that Liqo has made eligible.

</details>

---

## Hands-On Exercise

This lab builds the layered model on a laptop-friendly setup. The full production version needs two real Kubernetes clusters, routed or L2 reachability between them, and network equipment where you can verify ARP or BGP state. The minimal version uses two kind clusters with Calico and kube-vip Service VIP behavior.

Calico BGP is simulated at the cluster layer because a laptop kind environment does not provide real top-of-rack routers. The point is to practice the object model, verification flow, and failure thinking. Use a clean terminal with these tools installed:

- `kind`
- `kubectl`
- `helm`
- `docker`
- `jq`
- `curl`

Create the `k` alias now:

```bash
alias k=kubectl
```

Create kubeconfig paths for the two clusters:

```bash
export KUBECONFIG_A="$HOME/.kube/kind-cluster-a"
export KUBECONFIG_B="$HOME/.kube/kind-cluster-b"
export VIP_RANGE_A="172.18.255.200-172.18.255.210"
export VIP_RANGE_B="172.18.255.220-172.18.255.230"
```

### Task 1: Bootstrap Two kind Clusters with Calico and kube-vip

Create a kind configuration that disables the default CNI so Calico can be installed.

```bash
cat > /tmp/kind-calico-a.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: 10.244.0.0/16
nodes:
  - role: control-plane
  - role: worker
EOF

cat > /tmp/kind-calico-b.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: 10.245.0.0/16
nodes:
  - role: control-plane
  - role: worker
EOF

kind create cluster --name cluster-a --config /tmp/kind-calico-a.yaml --kubeconfig "$KUBECONFIG_A"
kind create cluster --name cluster-b --config /tmp/kind-calico-b.yaml --kubeconfig "$KUBECONFIG_B"
```

Install Calico on both clusters.

```bash
for kubeconfig in "$KUBECONFIG_A" "$KUBECONFIG_B"; do
  KUBECONFIG="$kubeconfig" k apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.31.0/manifests/calico.yaml
  KUBECONFIG="$kubeconfig" k -n kube-system rollout status daemonset/calico-node --timeout=240s
  KUBECONFIG="$kubeconfig" k -n kube-system rollout status deployment/calico-kube-controllers --timeout=240s
done
```

Install kube-vip cloud provider and kube-vip DaemonSet on each cluster.

```bash
for kubeconfig in "$KUBECONFIG_A" "$KUBECONFIG_B"; do
  KUBECONFIG="$kubeconfig" k apply -f https://kube-vip.io/manifests/rbac.yaml
  KUBECONFIG="$kubeconfig" k apply -f https://raw.githubusercontent.com/kube-vip/kube-vip-cloud-provider/main/manifest/kube-vip-cloud-controller.yaml
done

KUBECONFIG="$KUBECONFIG_A" k create configmap kubevip \
  --namespace kube-system \
  --from-literal range-global="$VIP_RANGE_A"

KUBECONFIG="$KUBECONFIG_B" k create configmap kubevip \
  --namespace kube-system \
  --from-literal range-global="$VIP_RANGE_B"

docker run --rm ghcr.io/kube-vip/kube-vip:v0.8.9 manifest daemonset \
  --interface eth0 \
  --services \
  --arp \
  --leaderElection \
  --inCluster \
  --taint \
  | KUBECONFIG="$KUBECONFIG_A" k apply -f -

docker run --rm ghcr.io/kube-vip/kube-vip:v0.8.9 manifest daemonset \
  --interface eth0 \
  --services \
  --arp \
  --leaderElection \
  --inCluster \
  --taint \
  | KUBECONFIG="$KUBECONFIG_B" k apply -f -
```

Create a test Service in each cluster.

```bash
for kubeconfig in "$KUBECONFIG_A" "$KUBECONFIG_B"; do
  KUBECONFIG="$kubeconfig" k create deployment vip-test --image=nginx:1.27 --replicas=1
  KUBECONFIG="$kubeconfig" k expose deployment vip-test --port=80 --target-port=80 --type=LoadBalancer
  KUBECONFIG="$kubeconfig" k rollout status deployment/vip-test --timeout=180s
  KUBECONFIG="$kubeconfig" k get svc vip-test -o wide
done
```

<details>
<summary>Solution and success criteria for Task 1</summary>

The key result is that each cluster has a `LoadBalancer` Service with an assigned external IP from its configured range. In a laptop kind environment, reachability from the host may depend on Docker networking and host routes. For this exercise, assignment plus kube-vip pod health is the minimal success signal. On real bare metal, also verify reachability from a machine outside the cluster subnet.

- [ ] Both kind clusters exist and report Ready nodes.
- [ ] Calico pods are Running in both clusters.
- [ ] kube-vip cloud provider is Running in both clusters.
- [ ] kube-vip DaemonSet pods are Running in both clusters.
- [ ] A `LoadBalancer` Service receives a VIP in both clusters.

</details>

### Task 2: Install Liqo and Peer Cluster A to Cluster B

Install `liqoctl` if it is not already present.

```bash
if ! command -v liqoctl >/dev/null 2>&1; then
  LIQO_VERSION="v1.0.2"
  OS="$(uname | tr '[:upper:]' '[:lower:]')"
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
  esac
  curl --fail -LS "https://github.com/liqotech/liqo/releases/download/${LIQO_VERSION}/liqoctl-${OS}-${ARCH}.tar.gz" | tar -xz
  sudo install -o root -g root -m 0755 liqoctl /usr/local/bin/liqoctl
fi
```

Install Liqo on both clusters.

```bash
liqoctl install --kubeconfig "$KUBECONFIG_A" --context kind-cluster-a --skip-confirm
liqoctl install --kubeconfig "$KUBECONFIG_B" --context kind-cluster-b --skip-confirm

liqoctl info --kubeconfig "$KUBECONFIG_A" --context kind-cluster-a
liqoctl info --kubeconfig "$KUBECONFIG_B" --context kind-cluster-b
```

Peer Cluster A to Cluster B.

```bash
liqoctl peer \
  --kubeconfig "$KUBECONFIG_A" \
  --context kind-cluster-a \
  --remote-kubeconfig "$KUBECONFIG_B" \
  --remote-context kind-cluster-b \
  --gw-server-service-type NodePort \
  --skip-confirm
```

Verify a virtual node appears in Cluster A.

```bash
KUBECONFIG="$KUBECONFIG_A" k get nodes -o wide
KUBECONFIG="$KUBECONFIG_A" k get nodes -l liqo.io/type=virtual-node -o wide
```

<details>
<summary>Solution and success criteria for Task 2</summary>

The expected result is a Ready virtual node in Cluster A representing Cluster B. If no virtual node appears, inspect `liqoctl info`, peering status, gateway Service type, and whether both kind clusters can reach each other through Docker networking. The `NodePort` gateway type avoids relying on cloud load balancers inside the kind lab.

- [ ] `liqoctl info` reports Liqo installed in both clusters.
- [ ] The `liqoctl peer` command completes without an error.
- [ ] Cluster A shows a Liqo virtual node for Cluster B.
- [ ] The virtual node reports allocatable CPU, memory, and pod capacity.

</details>

### Task 3: Install Karmada and Join Both Clusters

Install `karmadactl` if it is not already present.

```bash
if ! command -v karmadactl >/dev/null 2>&1; then
  KARMADA_VERSION="v1.17.0"
  OS="$(uname | tr '[:upper:]' '[:lower:]')"
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
  esac
  curl --fail -L "https://github.com/karmada-io/karmada/releases/download/${KARMADA_VERSION}/karmadactl-${OS}-${ARCH}.tgz" -o /tmp/karmadactl.tgz
  tar -xzf /tmp/karmadactl.tgz -C /tmp
  sudo install -o root -g root -m 0755 /tmp/karmadactl /usr/local/bin/karmadactl
fi
```

Initialize Karmada in Cluster A for the lab.

```bash
karmadactl init \
  --kubeconfig "$KUBECONFIG_A" \
  --context kind-cluster-a \
  --karmada-data "$HOME/.karmada-lab"
```

Export the generated Karmada kubeconfig path.

```bash
export KARMADA_KUBECONFIG="$HOME/.karmada-lab/karmada-apiserver.config"
```

Join both clusters in push mode for the minimal lab.

```bash
karmadactl join kind-cluster-a \
  --kubeconfig "$KARMADA_KUBECONFIG" \
  --cluster-kubeconfig "$KUBECONFIG_A" \
  --cluster-context kind-cluster-a

karmadactl join kind-cluster-b \
  --kubeconfig "$KARMADA_KUBECONFIG" \
  --cluster-kubeconfig "$KUBECONFIG_B" \
  --cluster-context kind-cluster-b
```

Verify clusters from the Karmada context.

```bash
KUBECONFIG="$KARMADA_KUBECONFIG" k get clusters
KUBECONFIG="$KARMADA_KUBECONFIG" k get clusters -o yaml
```

<details>
<summary>Solution and success criteria for Task 3</summary>

Both clusters should appear as Karmada `Cluster` objects. The lab uses push mode because the local Karmada control plane can reach both kind API servers. If Cluster B does not become Ready, check whether the kubeconfig context name is correct and whether Karmada can connect to the member API server endpoint.

- [ ] Karmada control-plane pods are Running in Cluster A.
- [ ] `KARMADA_KUBECONFIG` points to the generated Karmada API server kubeconfig.
- [ ] `k get clusters` against Karmada shows `kind-cluster-a`.
- [ ] `k get clusters` against Karmada shows `kind-cluster-b`.
- [ ] Both clusters report Ready or provide a clear diagnostic condition.

</details>

### Task 4: Propagate nginx Across Both Clusters

Create the workload and Service in the Karmada API server.

```bash
KUBECONFIG="$KARMADA_KUBECONFIG" k create namespace demo

KUBECONFIG="$KARMADA_KUBECONFIG" k -n demo create deployment nginx \
  --image=nginx:1.27 \
  --replicas=4

KUBECONFIG="$KARMADA_KUBECONFIG" k -n demo expose deployment nginx \
  --port=80 \
  --target-port=80 \
  --type=LoadBalancer
```

Apply a PropagationPolicy.

```bash
cat > /tmp/nginx-propagationpolicy.yaml <<'EOF'
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: nginx-spread
  namespace: demo
spec:
  resourceSelectors:
    - apiVersion: apps/v1
      kind: Deployment
      name: nginx
    - apiVersion: v1
      kind: Service
      name: nginx
  placement:
    clusterAffinity:
      clusterNames:
        - kind-cluster-a
        - kind-cluster-b
    replicaScheduling:
      replicaSchedulingType: Divided
      replicaDivisionPreference: Weighted
      weightPreference:
        staticWeightList:
          - targetCluster:
              clusterNames:
                - kind-cluster-a
            weight: 1
          - targetCluster:
              clusterNames:
                - kind-cluster-b
            weight: 1
    spreadConstraints:
      - spreadByField: cluster
        minGroups: 2
        maxGroups: 2
EOF

KUBECONFIG="$KARMADA_KUBECONFIG" k apply -f /tmp/nginx-propagationpolicy.yaml
```

Verify member clusters and bindings.

```bash
KUBECONFIG="$KARMADA_KUBECONFIG" k -n demo get propagationpolicy
KUBECONFIG="$KARMADA_KUBECONFIG" k -n demo get resourcebinding

KUBECONFIG="$KUBECONFIG_A" k -n demo get deploy,pods,svc -o wide
KUBECONFIG="$KUBECONFIG_B" k -n demo get deploy,pods,svc -o wide
```

<details>
<summary>Solution and success criteria for Task 4</summary>

The Deployment and Service should exist in both member clusters. The replica division may take a short time to settle. The `ResourceBinding` is the key Karmada diagnostic object because it records how the selected resource was scheduled. If pods exist but the Service has no VIP, return to Task 1 and fix the kube-vip layer before changing Karmada.

- [ ] The `demo` namespace exists in the Karmada API server.
- [ ] The `nginx-spread` PropagationPolicy exists.
- [ ] A `ResourceBinding` exists for the propagated Deployment.
- [ ] nginx pods run in Cluster A.
- [ ] nginx pods run in Cluster B.
- [ ] The propagated Service receives a VIP in each member cluster.

</details>

### Task 5: Simulate Cluster A Failure and Observe Karmada Failover

For a lab-safe failure, mark Cluster A with a `NoSchedule` taint first.

```bash
karmadactl taint clusters kind-cluster-a \
  site-failure=planned:NoSchedule \
  --kubeconfig "$KARMADA_KUBECONFIG"

KUBECONFIG="$KARMADA_KUBECONFIG" k get cluster kind-cluster-a -o yaml
```

For eviction-style testing, enable the relevant Karmada failover features in a dedicated lab only, then use `NoExecute` taints.

```bash
karmadactl taint clusters kind-cluster-a \
  site-failure=planned:NoExecute \
  --kubeconfig "$KARMADA_KUBECONFIG" \
  --overwrite
```

Observe the binding and member clusters.

```bash
KUBECONFIG="$KARMADA_KUBECONFIG" k -n demo get resourcebinding -o yaml
KUBECONFIG="$KUBECONFIG_A" k -n demo get pods -o wide
KUBECONFIG="$KUBECONFIG_B" k -n demo get pods -o wide
```

Remove the taint after the test.

```bash
karmadactl taint clusters kind-cluster-a site-failure- \
  --kubeconfig "$KARMADA_KUBECONFIG"
```

<details>
<summary>Solution and success criteria for Task 5</summary>

The exact failover behavior depends on enabled Karmada feature gates and policy configuration. At minimum, `NoSchedule` should prevent new placements on Cluster A. With eviction behavior enabled and policy configured, eligible workload placement should move away from the tainted cluster. Do not test destructive failover semantics against stateful applications until state preservation and database promotion are defined.

- [ ] Cluster A shows the expected taint in Karmada.
- [ ] Karmada placement no longer selects Cluster A for new work.
- [ ] The `ResourceBinding` changes or records the scheduling effect.
- [ ] Cluster B becomes the remaining healthy target for eligible replicas.
- [ ] The test taint is removed after observation.

</details>

### Task 6: Enable Liqo Namespace Offloading for an Existing Namespace

Create an application namespace in Cluster A.

```bash
KUBECONFIG="$KUBECONFIG_A" k create namespace burst

KUBECONFIG="$KUBECONFIG_A" k -n burst create deployment worker \
  --image=nginx:1.27 \
  --replicas=2

KUBECONFIG="$KUBECONFIG_A" k -n burst rollout status deployment/worker --timeout=180s
```

Enable offloading for the namespace.

```bash
liqoctl offload namespace burst \
  --kubeconfig "$KUBECONFIG_A" \
  --context kind-cluster-a \
  --pod-offloading-strategy LocalAndRemote \
  --skip-confirm
```

Scale the workload and observe scheduling.

```bash
KUBECONFIG="$KUBECONFIG_A" k -n burst scale deployment worker --replicas=6
KUBECONFIG="$KUBECONFIG_A" k -n burst get pods -o wide
KUBECONFIG="$KUBECONFIG_A" k get nodes -l liqo.io/type=virtual-node -o wide
KUBECONFIG="$KUBECONFIG_B" k get pods --all-namespaces -o wide | grep burst || true
```

<details>
<summary>Solution and success criteria for Task 6</summary>

The goal is to see Cluster A scheduling eligible pods onto the Liqo virtual node that represents Cluster B. Cluster B should show the hosted pods in the reflected namespace. If pods remain local, inspect the namespace offloading object, virtual-node taints, scheduler events, and shared resource capacity. This is a different pathway from Karmada propagation: the source cluster scheduler is making use of remote virtual capacity.

- [ ] The `burst` namespace exists in Cluster A.
- [ ] Liqo namespace offloading is enabled for `burst`.
- [ ] Cluster A shows the virtual node as a scheduling target.
- [ ] Some eligible pods schedule onto the virtual node when capacity and policy allow it.
- [ ] Cluster B shows the hosted offloaded pods or reflected namespace resources.

</details>

### Exercise Debrief

You have now touched every layer. kube-vip assigned Service VIPs inside each cluster. Liqo created a virtual-node relationship so Cluster A could consume Cluster B capacity.

Karmada created a hub-level policy and binding so a workload could be propagated across both clusters. Those are different powers. They become reliable only when the team keeps them separate and tests their interactions.

---

## Next Module

Next: OpenStack on K8s, where you will connect on-prem Kubernetes platform design to infrastructure services running on Kubernetes itself.

---

## Sources

- [Karmada documentation](https://karmada.io/docs/)
- [Karmada architecture](https://karmada.io/docs/core-concepts/architecture/)
- [Karmada cluster registration](https://karmada.io/docs/userguide/clustermanager/cluster-registration/)
- [Karmada resource propagating](https://karmada.io/docs/v1.13/userguide/scheduling/resource-propagating/)
- [Karmada cluster failover](https://karmada.io/docs/userguide/failover/cluster-failover/)
- [Karmada failover analysis](https://karmada.io/docs/userguide/failover/failover-analysis)
- [Karmada GitHub repository](https://github.com/karmada-io/karmada)
- [Liqo documentation](https://docs.liqo.io/)
- [Liqo peer command](https://docs.liqo.io/en/latest/usage/liqoctl/liqoctl_peer.html)
- [Liqo namespace offloading](https://docs.liqo.io/en/latest/usage/namespace-offloading.html)
- [Liqo GitHub repository](https://github.com/liqotech/liqo)
- [kube-vip documentation](https://kube-vip.io/docs/)
- [kube-vip static pods](https://kube-vip.io/docs/installation/static/)
- [kube-vip ARP mode](https://kube-vip.io/docs/modes/arp/)
- [kube-vip cloud provider](https://kube-vip.io/docs/usage/cloud-provider/)
- [kube-vip GitHub repository](https://github.com/kube-vip/kube-vip)
- [Kubernetes Service documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Argo CD ApplicationSet generators](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/)
- [Argo CD ApplicationSet user guide](https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/)
- [Thanos quick tutorial](https://thanos.io/tip/thanos/quick-tutorial.md/)
- [Grafana Mimir documentation](https://grafana.com/docs/mimir/latest/)
