---
title: "Module 5.7: Kube-Router - The Swiss Army Knife in a Single Binary"
slug: platform/toolkits/infrastructure-networking/networking/module-5.7-kube-router
sidebar:
  order: 8
revision_pending: false
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 55-70 minutes

## Learning Outcomes

- Explain CNI lifecycle, IPAM, plugin chaining, and Kubernetes pod-networking expectations.
- Compare overlay networking, native Layer 3 routing, BGP route distribution, and underlay requirements.
- Verify kube-router BGP routing, IPVS Service proxying, and NetworkPolicy enforcement.
- Test NetworkPolicy behavior and decide when Multus, Flannel, Calico, or Cilium changes the design.

## Why This Module Matters

Kubernetes networking can feel like three separate subjects wearing one trench coat: pod networking, Service load balancing, and NetworkPolicy enforcement. A cluster needs all three before it feels like a useful platform. Pods need routable addresses, Services need a stable virtual IP that can move traffic to changing endpoints, and teams need a way to restrict east-west traffic after workloads are running. Many production clusters split those jobs across multiple components, such as a CNI plugin for pod connectivity, kube-proxy for Services, and another policy engine for NetworkPolicy. Kube-router is interesting because it deliberately combines those jobs into one daemon, which makes it a good lens for learning the durable architecture underneath all CNI choices.

The durable lesson is not that kube-router is the right answer for every cluster. It is that every Kubernetes networking stack must answer the same questions: who assigns pod IPs, who makes those pod IPs reachable across nodes, who implements Service virtual IPs, and who enforces policy when a pod should not be allowed to talk to another pod. Kube-router answers those questions with standard Linux networking primitives: BGP for route distribution, GoBGP as the embedded BGP implementation, IPVS/LVS for Service proxying, and iptables plus ipset for NetworkPolicy. Once you understand those choices, Flannel, Calico, Cilium, and Multus become easier to compare without turning the conversation into a brand contest.

Hypothetical scenario: imagine a small bare-metal platform team that started with Flannel because it was simple. The cluster grew, teams began asking for NetworkPolicy, and the operations team noticed that Service troubleshooting always bounced between the CNI daemon, kube-proxy, and host firewall state. One option is to add another policy component and keep kube-proxy. Another option is to choose a plugin that owns routing, policy, and Services together. Kube-router is built for that second shape: fewer moving pieces, native Layer 3 routing where the fabric can support it, and a service proxy based on a kernel load balancer instead of a long chain of iptables rules.

The memorable analogy is a campus mail system. An overlay network is like putting every internal letter inside a second envelope addressed to the building where the recipient sits; it is flexible because the outside mailroom only needs to know building addresses, but every letter carries extra wrapping. BGP-based routing is like teaching the campus map where every department is located, so the original envelope can travel directly to the right building without being repackaged. Kube-router chooses the map-first approach for pod traffic, then adds an in-kernel load balancer for Service addresses and firewall rules for policy.

This module also matters because kube-router forces you to separate control plane from dataplane. BGP sessions, Kubernetes watches, and controller loops are control-plane mechanisms that decide what the node should know. Linux routes, IPVS virtual services, ipsets, and iptables chains are dataplane artifacts that affect packets. When those ideas blur together, debugging becomes guesswork. When they stay separate, you can ask precise questions: did Kubernetes record the desired state, did kube-router observe it, did the node program the expected object, and did the packet follow that object?

The comparison habit you build here transfers to every CNI conversation. A product page may lead with a feature, but the durable decision is usually about ownership boundaries. If one component owns pod routes, another owns Services, and a third owns policy, you need a clear mental map of how their failure modes interact. If one component owns all three, you need confidence in that component's behavior and rollback path. Kube-router gives you one compact case study for both sides of that tradeoff.

## Did You Know?

- **CNI is intentionally small**: The CNI specification focuses on adding and removing container network connectivity; Kubernetes builds a larger cluster model on top of that small interface.
- **Kubernetes Services are not magic IPs**: A service proxy watches Services and EndpointSlices, then programs the node data plane so packets for a virtual IP reach a backing endpoint.
- **BGP is about reachability**: In a kube-router cluster, BGP is not carrying application traffic; it is distributing route information so the Linux kernel can forward pod packets normally.
- **NetworkPolicy needs an enforcer**: Creating a NetworkPolicy object only records intent in the API server; enforcement depends on a CNI or policy component that watches those objects and programs the dataplane.

## Part 1: The CNI Contract Under Every Plugin

CNI stands for Container Network Interface, but it is better to think of it as a contract between a container runtime and executable plugins on the node. The runtime creates a pod sandbox and asks the configured CNI plugin chain to connect that sandbox to one or more networks. The plugin receives JSON configuration through stdin, runtime context through environment variables, and a command such as `ADD`, `DEL`, `CHECK`, or `VERSION`. The plugin then creates interfaces, assigns addresses, installs routes, and returns a structured result that later plugins in the chain can consume.

That small contract is why very different projects can all be "CNI plugins" while doing radically different things behind the scenes. Flannel can create an overlay fabric, Calico can program routes and policy, Cilium can load eBPF programs, Multus can call other CNI plugins as delegates, and kube-router can use the standard bridge and host-local plugins on the node while its daemon handles distributed routing state. Kubernetes does not require every implementation to have the same internals; it requires the resulting pod network to satisfy the Kubernetes networking model.

The CNI lifecycle matters operationally because failure modes often appear at the boundary between pod sandbox creation and node-level networking state. When `ADD` fails, the pod may sit in `ContainerCreating` because the runtime could not attach a working interface. When `DEL` fails, stale veth interfaces, IPAM reservations, or routes can remain behind. When `CHECK` is supported and used, it lets the runtime ask whether the network attachment still matches the declared configuration. A good platform engineer treats CNI errors as node networking errors with a lifecycle, not as random pod scheduling problems.

IPAM, or IP Address Management, is the part of the system that decides which pod IP a sandbox receives. Some CNI setups use `host-local` IPAM so each node allocates addresses from a node-specific CIDR; others use cluster-wide IPAM backed by Kubernetes custom resources, cloud APIs, or an external datastore. Kube-router can use the pod CIDR assigned to each node and then advertise that CIDR through BGP. The important separation is that assigning an address and making that address reachable are different jobs, even though some products package both jobs together.

CNI plugin chaining is another durable idea. A primary plugin may create the interface and assign the IP, while helper plugins add port mapping, bandwidth shaping, firewall behavior, or additional interfaces. Multus uses this idea more explicitly by acting as a meta-plugin that attaches multiple networks to a pod. Kube-router sits in the primary networking conversation because it can provide cluster pod routing, but you still need to understand chaining because Kubernetes nodes often combine a main CNI with loopback, portmap, tuning, or multi-network plugins.

## Part 2: The Kubernetes Pod-Networking Model

Kubernetes expects a flat pod network from the point of view of workloads. Every pod gets its own IP address, containers inside a pod share that network namespace, and pods should be able to communicate with other pods directly across nodes unless a NetworkPolicy or another intentional control blocks the connection. The packet may travel through tunnels, route tables, bridges, eBPF programs, or cloud networking devices, but the application should not have to know which node hosts the other pod or which host port maps to the container port.

This model is different from the classic Docker-on-one-host model where port publishing and host NAT were the normal way to expose containers. Kubernetes Services handle stable virtual addressing for groups of pods, while the pod network handles direct endpoint reachability. That distinction is central to debugging. If a pod cannot reach another pod IP, you look at the pod network and CNI dataplane. If a pod can reach endpoint IPs but not a ClusterIP, you look at the service proxy path. If the connection works until policy is applied, you look at NetworkPolicy selectors and enforcement state.

Kubernetes itself does not prescribe one dataplane. The API server stores pods, nodes, Services, EndpointSlices, and NetworkPolicies, but it does not push every route or firewall rule into the kernel. Node agents watch the API and reconcile local state. Kube-proxy is the traditional Service agent. CNI daemons or policy controllers are the pod-network and firewall agents. Kube-router combines several of these watches into one process, but the control-loop pattern is the same: observe desired state from Kubernetes, compare it with local Linux state, then repair drift.

The model also explains why "no NAT between pods" matters. If pod A connects to pod B by pod IP, pod B should see pod A's pod IP as the source, not the node IP after masquerading. Preserving pod identity makes logs, policy, and debugging more understandable. Some egress paths still use NAT when traffic leaves the cluster, and some Service paths may rewrite addresses depending on traffic policy, but the core pod-to-pod model is direct IP reachability. CNI choices are mostly different ways to deliver that promise over imperfect real networks.

## Part 3: Overlay, Native Layer 3 Routing, and Underlay Integration

The first major CNI design fork is whether the cluster hides pod networks behind an overlay or teaches the physical network how to reach pod CIDRs. Overlay networking encapsulates the original pod packet inside another packet whose outer source and destination are node IPs. VXLAN and IP-in-IP are common examples. The underlay only needs to route node IPs, so overlays are easy to deploy in networks that do not know anything about pod CIDRs. The tradeoff is extra packet headers, lower effective MTU, and another datapath to inspect when troubleshooting.

Native Layer 3 routing takes the opposite approach. Each node owns one or more pod CIDRs, and other nodes learn routes to those CIDRs. The original pod packet remains the packet being forwarded, and the Linux kernel sends it toward the node that owns the destination pod range. BGP is a common way to distribute those routes because it is already a routing protocol designed to exchange reachability information. Kube-router's network routes controller uses GoBGP to advertise pod CIDRs and learn peers' pod CIDRs, then installs routes into the host routing table.

Underlay-integrated networking goes one step further by involving routers, top-of-rack switches, cloud route tables, or a cloud-native CNI in pod reachability. The cluster may peer directly with network devices, update cloud APIs, or allocate pod IPs from the same address space that the VPC already understands. This can reduce encapsulation and make pods first-class network endpoints, but it requires stronger coordination with the network team or cloud provider. A design that works perfectly in a lab may fail in a production VPC if the fabric refuses to route arbitrary pod CIDRs.

MTU is where this design fork becomes painfully concrete. Ethernet payload size is finite. If an overlay adds an outer IP header, UDP header, and VXLAN header, the inner pod packet has less room unless the physical network supports a larger MTU. If the path MTU is wrong, small requests work while larger responses fragment or disappear. Native routing avoids overlay header overhead for pod-to-pod traffic, but it requires route distribution to be correct. Kube-router's appeal is strongest when you can route pod CIDRs natively or deliberately peer with infrastructure that can.

Flannel is the useful contrast. Its common VXLAN mode is intentionally simple: nodes exchange subnet lease information and encapsulate pod traffic between node IPs. That simplicity is a strength when you want a basic pod network and do not need policy enforcement in the same component. Kube-router chooses BGP and Linux routes instead, which removes the normal overlay wrapping in the direct-routing path but moves complexity into BGP session design, route filtering, and fabric compatibility. Neither model is universally superior; each pays a different operational cost.

## Part 4: Where Kube-Router Fits

Kube-router is an all-in-one Kubernetes networking daemon. With all major controllers enabled, it handles pod networking, Service proxying, NetworkPolicy enforcement, and a LoadBalancer IP allocator path for environments without a cloud load balancer. The durable design point is that it uses standard Linux building blocks instead of an overlay-first SDN dataplane: BGP routes for pod CIDR reachability, IPVS virtual services for Kubernetes Services, and iptables plus ipset for policy. You can also enable only selected controllers when you want kube-router to replace just one part of a stack.

The network routes controller is the part most people mean when they call kube-router an L3 CNI. Each node runs kube-router, learns the pod CIDR for that node, and advertises that route to BGP peers. By default, a small cluster can form a node-to-node mesh, where every kube-router instance peers with the others. Larger or fabric-integrated designs can use route reflectors or external routers so nodes do not all need to peer with every other node. The result should be ordinary host routes to remote pod CIDRs in the Linux routing table.

The network services controller is the kube-proxy replacement. It watches Services and EndpointSlices, then programs IPVS virtual servers and real servers so packets sent to a ClusterIP, NodePort, or supported external address are load-balanced to endpoints. This is conceptually the same job kube-proxy performs, but with a different Linux mechanism. Kube-router's service proxy is most relevant when you want IPVS behavior and you are already choosing kube-router for routing, or when you want to run only its service proxy beside another CNI after cleaning up kube-proxy state.

The network policy controller watches namespaces, pods, and NetworkPolicy objects, then translates policy selectors into ipsets and iptables rules. ipset matters because policies usually match groups of pod IPs, not one fixed address. A selector such as `app=frontend` may match many pods, and those pods can churn as Deployments roll. Instead of writing one long firewall rule chain per pod IP, kube-router can maintain hashed sets and reference those sets from iptables. The enforcement model is standard Kubernetes NetworkPolicy, which means L3/L4 allow rules rather than application-layer authorization.

Those three controllers can be enabled independently with flags such as `--run-router`, `--run-service-proxy`, and `--run-firewall`. That modularity is a practical migration tool. A team could use kube-router only for NetworkPolicy enforcement beside Flannel, only for IPVS Service proxying after removing kube-proxy, or as the full network stack in a new bare-metal cluster. The danger is accidental overlap: two components trying to own routes, Service virtual IPs, or firewall chains can create hard-to-debug behavior, so controller boundaries must be explicit.

## Landscape Snapshot

> **Landscape snapshot - as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**

Upstream GitHub releases show kube-router `v2.10.0` as the latest release, published on 2026-05-27. The release notes describe network policy hardening, broader IPv6 parity in the Network Routes Controller, EndpointSlice handling updates, Kubernetes client library refreshes, and GoBGP `v4.5.0` in the maintenance stack. Treat those as snapshot facts, not timeless curriculum content, and verify the release page before pinning production manifests or writing procurement documentation.

The project repository is under `cloudnativelabs/kube-router`, and the upstream documentation describes kube-router as a turnkey Kubernetes networking solution built around a single DaemonSet or binary. The project documentation says current bug fixes and security patches generally target the current major.minor release, with exceptional backports handled by request. The upstream kube-router docs do not present a CNCF project maturity level for kube-router itself, so if governance status matters to your organization, verify against the CNCF project list and the current upstream repository before making a decision.

Kube-router's documented feature set includes pod networking with direct routing through BGP and GoBGP, IPVS/LVS Service proxying with scheduling options, NetworkPolicy enforcement through iptables and ipset, DSR for selected external or LoadBalancer service paths, and optional advertisement of selected Service IPs to BGP peers. Some of those features are dataplane architecture choices that will remain useful to understand for years. Specific flags, defaults, manifests, and version compatibility are volatile and belong in runbooks that are checked against current upstream docs.

## Cross-CNI Rosetta Table

The table below compares durable capabilities, not market position. Read each row as a design question you would ask before selecting or operating a CNI stack. A plugin can be a strong fit for one row and a poor fit for another, and many real clusters combine more than one component, such as a primary CNI plus Multus for secondary interfaces.

| Capability | kube-router | Flannel | Calico | Cilium | Multus |
|---|---|---|---|---|---|
| Connectivity model | Native L3 routing with BGP for pod CIDRs; tunneling can be used for fallback cases | Simple L3 fabric, commonly VXLAN overlay between nodes | BGP routing, IP-in-IP, VXLAN, and other dataplane options depending on configuration | eBPF dataplane with encapsulation or native routing modes; BGP control plane can advertise routes outward | Meta-plugin; delegates connectivity to other CNI plugins |
| Encapsulation posture | Avoids encapsulation on direct routed paths; overlay/tunneling is situational | Overlay is common, especially VXLAN; host-gw/direct options exist in some deployments | Can run no-encap with routable fabric or encapsulate with IP-in-IP/VXLAN | Can run overlay or native routing; exact datapath depends on configuration | No dataplane by itself; secondary networks may be bridge, macvlan, SR-IOV, or another plugin |
| NetworkPolicy support | Standard Kubernetes NetworkPolicy through iptables, ipset, and conntrack | No built-in NetworkPolicy enforcement in the basic flannel dataplane | Kubernetes NetworkPolicy plus Calico policy APIs, depending on edition and configuration | Kubernetes NetworkPolicy plus Cilium policy features, including identity-aware and L7 options | Does not enforce policy by itself; depends on delegated plugins and network design |
| Service handling | Optional kube-proxy replacement using IPVS/LVS virtual services | Leaves Service proxying to kube-proxy or another component | Commonly works with kube-proxy; eBPF dataplane can replace kube-proxy in supported configurations | Can fully replace kube-proxy with eBPF service load balancing | Leaves Service handling to the default network and service proxy |
| IPAM relationship | Can use node pod CIDRs and CNI host-local behavior; advertises ownership with BGP | Allocates or records node subnet leases from a larger pod CIDR | Supports Calico IP pools and several IPAM patterns | Supports Kubernetes, cluster-scope, and cloud-integrated IPAM modes depending on environment | Delegates IPAM to the default and additional network plugins |
| Multi-NIC workloads | Not the primary purpose; use another plugin if pods need multiple interfaces | Not the primary purpose | Possible through additional tooling, but not the core role | Possible through additional integrations, but not the core role | Core purpose: attach multiple interfaces to a pod through delegate CNI plugins |
| Typical operating fit | Bare-metal or on-prem clusters where BGP routing, IPVS Services, and standard policy in one daemon are attractive | Simple pod connectivity where overlay simplicity matters more than built-in policy | Clusters needing flexible routing and Calico policy controls across many environments | Clusters needing eBPF dataplane features, rich observability, or advanced policy semantics | Network-function, storage, telecom, or specialized workloads needing secondary data interfaces |
| Governance and maturity signal | CloudNativeLabs GitHub project; verify current release and governance status upstream | flannel-io GitHub project; verify current maintenance status upstream | Project Calico by Tigera; verify current version and support model upstream | CNCF Graduated project; verify feature compatibility against current Cilium docs | Kubernetes Network Plumbing Working Group project; verify current release and deployment model upstream |

## Part 5: BGP Routing in Kube-Router

BGP is often introduced as "the protocol of the Internet," which can make it sound too heavy for a Kubernetes cluster. For kube-router, the relevant idea is simpler: BGP speakers exchange reachability information. A node can say, "I can reach pod CIDR `10.244.2.0/24` through my node IP," and peers can install that route. The pod packet does not ride inside the BGP session. BGP is the control-plane conversation that teaches each node's kernel where to send ordinary IP packets.

In a full-mesh kube-router cluster, every node peers with every other node. This is easy to reason about in small clusters because there is no central route distributor. The cost is that session count grows quickly as nodes are added. Route reflectors reduce the peer count by letting ordinary nodes peer with one or more reflector nodes, which then reflect learned routes to the rest of the cluster. External peering extends the same idea beyond Kubernetes nodes, allowing routers or top-of-rack switches to learn pod or Service routes when the network team intentionally supports that design.

The routing table is the most honest debugging surface for this part of kube-router. If pod A on node one cannot reach pod B on node two, you can check whether node one has a route for node two's pod CIDR, whether the next hop is the expected node IP, whether the reverse route exists, and whether the underlay can actually deliver traffic to that next hop. BGP session state is important, but the kernel route table tells you what packets will do after the route control plane has spoken.

External router peering is powerful because it can make pod CIDRs or selected Service VIPs reachable outside the cluster without a cloud load balancer. It is also where route hygiene becomes non-negotiable. You need a clear autonomous system number plan, explicit import and export policies, route filters, and agreement on what prefixes Kubernetes may advertise. Accidentally leaking pod CIDRs into the wrong network, or accepting a default route from a peer that should never provide one, can turn a CNI experiment into a fabric incident.

The native routing path is easiest when all nodes share a simple network where node IPs can reach each other and pod CIDR routes can be installed without fighting cloud provider restrictions. Clouds often have anti-spoofing, route table limits, or VPC behavior that prevents arbitrary pod IP routing unless the provider CNI is designed for it. That is why overlay plugins remain useful. A durable CNI decision starts with the fabric, not the plugin logo: can this network route pod CIDRs, and who owns that route table?

## Part 6: Service Proxying with IPVS/LVS

Kubernetes Services solve a different problem from pod routing. Pod IPs are ephemeral, but clients need a stable address for a logical application. A Service gives clients a virtual IP and port, while EndpointSlices describe the current backend endpoints. A service proxy watches those objects and programs the node dataplane so packets to the virtual IP are redirected or load-balanced to real endpoints. Kube-proxy is the standard implementation, but Kubernetes explicitly allows alternative service proxy implementations, and kube-router's network services controller is one of those alternatives.

In iptables mode, kube-proxy programs chains of netfilter rules. That mode is widely understood and works well for many clusters, but each Service and endpoint adds rule state that must be synchronized. The Kubernetes IPVS deep dive explains the scale motivation: large numbers of Services and endpoints create many iptables records, and updating those chains can become expensive. The key point is not a made-up latency number; it is the data structure difference. iptables is rule-chain oriented, while IPVS is a kernel load balancer designed around virtual services, real servers, and scheduling algorithms.

IPVS, or IP Virtual Server, implements Layer 4 load balancing inside the Linux kernel. Kube-router configures each Kubernetes Service as an IPVS virtual service and each endpoint as a real server. When a packet arrives for the Service virtual IP, IPVS selects a backend using a scheduling algorithm such as round robin, least connection, source hashing, destination hashing, shortest expected delay, or never queue. That makes Service behavior easier to inspect with `ipvsadm` because you can see virtual services and real servers directly.

Kube-router's IPVS proxy should not be understood as "faster because the module says so." The defensible claim is that IPVS was designed for load balancing and uses more appropriate data structures for Service lookup and scheduling than large linear firewall chains. The practical result is often better scaling behavior in clusters with many Services or endpoints, but you still need to test your workload, kernel, conntrack settings, and Service traffic patterns. Service proxy performance is affected by more than the proxy mode, including DNS, endpoint churn, node CPU, and network policy rules.

Direct Server Return changes the response path for specific external or LoadBalancer service scenarios. Normally, a service proxy node may receive a request, forward it to a backend pod, and remain in the response path. With DSR, kube-router can arrange for the backend to reply directly to the client, bypassing the service proxy on the return leg. That can be valuable for asymmetric traffic patterns where responses are much larger than requests, but it also comes with requirements around external IP ranges, tunneling details, MTU, port mapping, and workload compatibility.

There is one migration rule worth repeating: do not let kube-proxy and kube-router both own the same Service dataplane. If you use kube-router as the service proxy, remove or disable kube-proxy according to a tested plan, clean up old rules where appropriate, and verify IPVS state after the change. If you only want kube-router for routing or policy, leave `--run-service-proxy=false` and keep Service ownership elsewhere. Overlapping owners can create a cluster that sometimes works, which is worse than a cluster that fails loudly.

## Part 7: NetworkPolicy Through iptables and ipset

NetworkPolicy is an intent API. It describes which pods are allowed to communicate with which other pods or IP blocks at L3/L4, but the API server does not enforce that policy by itself. Enforcement depends on the networking implementation watching NetworkPolicy objects, resolving selectors to current pods, and programming the dataplane. Kube-router's network policy controller does this with iptables, ipset, and conntrack, which means policy decisions are enforced by the Linux packet filter on the node.

The default behavior of Kubernetes networking is allow-all traffic in a namespace until policies select pods for isolation. A default-deny policy is just a policy that selects pods and provides no allow rules for a direction. That model is easy to misunderstand because creating a policy for one app can change isolation only for selected pods and only for the directions named in `policyTypes`. Kube-router does not change those semantics; it implements the standard Kubernetes NetworkPolicy behavior with Linux primitives.

ipset is the piece that keeps selector-based policies manageable. A policy may allow traffic from all pods with `app=frontend` to all pods with `app=backend`. The membership of those groups changes as pods roll, restart, and reschedule. Kube-router can maintain sets of source and destination pod IPs, then reference those sets from iptables rules. Instead of creating one rule per source-destination pair, it can use set membership lookups that better match the dynamic nature of Kubernetes labels.

The limitation is that standard Kubernetes NetworkPolicy is not an application authorization system. It can match pods, namespaces, IP blocks, protocols, and ports, but it does not understand HTTP paths, JWT claims, gRPC methods, or database users. If you need L7-aware policy, DNS-aware egress controls, identity-based policy beyond the Kubernetes API, or rich flow observability, compare kube-router with Cilium, Calico policy features, or a service mesh. Kube-router's value is standard policy enforcement in the same daemon that handles routing and optional Services.

Troubleshooting policy should follow the same desired-state to local-state pattern as routing. First confirm the policy selects the destination pods you think it selects. Then confirm the source selector or namespace selector matches the clients. After that, inspect kube-router logs, ipsets, and iptables chains on the node hosting the destination pod. If the expected set membership is wrong, the issue may be labels, namespaces, or controller sync. If set membership is right but packets are dropped, inspect rule order, conntrack state, and whether traffic enters the expected chain.

## Part 8: Installation and Verification Patterns

The safest time to choose a full kube-router stack is during cluster creation, before another CNI and kube-proxy have written a lot of persistent node state. A kubeadm-style install would skip kube-proxy if kube-router will own Services, set a pod CIDR, and apply an upstream kube-router DaemonSet that matches the desired controller combination. In an existing cluster, treat the migration as a network change: drain nodes in stages, know how to roll back, and capture route, IPVS, iptables, and CNI configuration before changing ownership.

The following commands show the inspection pattern rather than a universal production manifest. Upstream manifests and flags change, so pin a tested kube-router image tag and read the current docs before applying anything to a real cluster. In a lab, you can apply the upstream all-service DaemonSet and then inspect whether nodes become ready, whether pod CIDR routes appear, whether IPVS virtual services exist, and whether NetworkPolicy changes produce ipset and iptables state. The important skill is verifying each controller's local artifact.

```bash
# Lab-only example: inspect current kube-router pods.
kubectl -n kube-system get pods -l k8s-app=kube-router -o wide

# Pick one kube-router pod for host-network inspection.
KR_POD="$(kubectl -n kube-system get pod -l k8s-app=kube-router \
  -o jsonpath='{.items[0].metadata.name}')"

# BGP-learned pod CIDR routes should appear when routing is enabled.
kubectl -n kube-system exec "$KR_POD" -- ip route show

# Service proxy ownership should be visible as IPVS virtual services.
kubectl -n kube-system exec "$KR_POD" -- ipvsadm -Ln

# NetworkPolicy enforcement should produce kube-router-related sets and rules.
kubectl -n kube-system exec "$KR_POD" -- ipset list -name
kubectl -n kube-system exec "$KR_POD" -- iptables -S | grep KUBE-ROUTER
```

When kube-router is installed as a full replacement, your verification should prove that all three planes work independently. Pod-to-pod traffic by pod IP proves the pod network and routes. Traffic to a Service ClusterIP proves the Service proxy path. A default-deny policy followed by a narrow allow policy proves NetworkPolicy enforcement. Do not accept "the pods are Ready" as sufficient proof, because node readiness can hide a broken Service path, and a working Service path can hide missing policy enforcement.

When kube-router is installed as a partial replacement, verification must prove that disabled controllers are truly disabled. If Flannel owns pod networking and kube-router only enforces NetworkPolicy, kube-router should not be programming competing pod routes. If another CNI owns routing and kube-router only replaces kube-proxy, the route table should remain under that CNI's control while IPVS state belongs to kube-router. Partial mode is useful precisely because it narrows ownership, so your checks should confirm that narrow boundary.

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Running kube-router's service proxy while kube-proxy still owns Services | Two controllers can program overlapping rules and virtual service state, producing intermittent or confusing Service behavior | Decide one Service owner, disable the other, and clean up old dataplane state during a staged migration |
| Treating BGP as a data tunnel | Teams look for encapsulated traffic in the wrong place and miss ordinary kernel route problems | Remember that BGP distributes reachability; inspect BGP sessions and the Linux routing table separately |
| Choosing native routing when the fabric cannot route pod CIDRs | Packets leave the node with pod source or destination addresses that the network refuses to forward | Confirm underlay behavior, route-table limits, anti-spoofing rules, and external peering requirements before deployment |
| Ignoring MTU during overlay fallback or DSR | Small probes pass while larger packets fragment or fail, especially when tunnels reduce effective payload size | Calculate MTU for the actual path, test larger payloads, and configure MSS or interface MTU deliberately |
| Assuming NetworkPolicy is enforced because YAML exists | Kubernetes stores the policy object even if the active CNI does not enforce it | Verify with a deny-and-allow test and inspect kube-router ipsets and iptables rules on the destination node |
| Using full-mesh BGP without a scale plan | Peer count and update chatter grow quickly as nodes are added, even though the early cluster looked simple | Plan route reflectors or external router peering before node growth makes full mesh uncomfortable |
| Migrating a live cluster without ownership inventory | Existing CNI files, kube-proxy rules, routes, and policy chains may survive and conflict with the new design | Capture current CNI config, kube-proxy mode, route tables, IPVS state, and firewall chains before making changes |
| Comparing CNIs by feature lists alone | A long feature matrix can hide fabric requirements, kernel requirements, operational skills, and migration risk | Compare capabilities against your network constraints, policy needs, Service ownership model, and team expertise |

## Quiz

### Question 1

A team says, "Kube-router is a CNI, so it must be the thing that directly assigns every pod IP." What is incomplete about that statement?

<details>
<summary>Show Answer</summary>

The statement mixes the CNI contract, IPAM, and distributed routing into one vague label. CNI is the runtime-to-plugin interface used when a pod sandbox is attached to the network, and IPAM is the responsibility that allocates an address for that sandbox. Kube-router can participate in pod networking by using node pod CIDRs and advertising those CIDRs with BGP, but address allocation and reachability are separate concerns. A correct explanation names the plugin lifecycle, the IPAM source, and the route distribution mechanism.

</details>

### Question 2

Why does kube-router's BGP design avoid the usual VXLAN overlay overhead when native routing is possible?

<details>
<summary>Show Answer</summary>

In native routing mode, kube-router advertises each node's pod CIDR to peers and installs learned routes into the Linux routing table. A packet from one pod to another remains the original pod packet; the kernel forwards it toward the node that owns the destination pod CIDR. VXLAN overlay mode wraps the original packet in an outer packet addressed between node IPs, which adds headers and reduces effective MTU. Kube-router avoids that wrapping only when the underlay can actually route the pod CIDR paths.

</details>

### Question 3

A small bare-metal cluster uses kube-router successfully, then grows and sees BGP session management become noisy. What design change should the team evaluate before blaming Kubernetes?

<details>
<summary>Show Answer</summary>

The team should evaluate moving away from node-to-node full mesh toward route reflectors or intentional external router peering. Full mesh is simple because every node learns directly from every other node, but the number of sessions grows quickly as the cluster grows. Route reflectors reduce the number of sessions ordinary nodes maintain while still distributing pod CIDR reachability. The team should also review route filters, autonomous system numbers, graceful restart behavior, and operational monitoring before changing peering topology.

</details>

### Question 4

What problem does kube-router's IPVS service proxy solve, and what claim should you avoid making without testing?

<details>
<summary>Show Answer</summary>

The IPVS service proxy solves the Kubernetes Service virtual IP problem by programming IPVS virtual services and real servers from Service and EndpointSlice state. Compared with iptables-mode kube-proxy, IPVS is a kernel load balancer designed for virtual services, scheduling algorithms, and efficient lookup structures, while iptables mode relies on rule chains that grow with Services and endpoints. You should avoid claiming a specific latency improvement without testing your kernel, workload, endpoint count, conntrack settings, and policy state in your own environment.

</details>

### Question 5

A cluster uses Flannel for pod connectivity and kube-proxy for Services. The team only wants standard Kubernetes NetworkPolicy. How could kube-router fit without replacing everything?

<details>
<summary>Show Answer</summary>

Kube-router can be run with only the firewall controller enabled, leaving routing to Flannel and Services to kube-proxy. In that mode, `--run-router=false`, `--run-service-proxy=false`, and `--run-firewall=true` express the ownership boundary. The team still needs to verify enforcement with a real deny-and-allow test and inspect kube-router's ipsets and iptables chains. The key is that partial deployment is valid only when disabled controllers truly stay out of the dataplane owned by other components.

</details>

### Question 6

Why is NetworkPolicy not enforced automatically by the Kubernetes API server?

<details>
<summary>Show Answer</summary>

The API server stores NetworkPolicy objects as desired state, but packet filtering happens on nodes where traffic actually flows. A networking implementation must watch policies, pods, and namespaces, resolve selectors into current endpoints, and program a dataplane such as iptables, nftables, eBPF, or a cloud firewall. Kube-router uses iptables and ipset for this job. Without an enforcing CNI or policy controller, policy YAML can exist in the cluster while traffic remains allowed by the default Kubernetes networking behavior.

</details>

### Question 7

What should you check before peering kube-router with external routers?

<details>
<summary>Show Answer</summary>

You should check which prefixes kube-router will advertise, which prefixes it is allowed to import, what autonomous system numbers are used, and whether route filters prevent accidental default-route import or broad pod CIDR export. You should also confirm that the physical or virtual network will forward pod IP traffic symmetrically enough for your workloads, and that monitoring can distinguish BGP session failure from ordinary packet loss. External peering is a network integration project, not just a Kubernetes manifest.

</details>

### Question 8

When would Multus appear in the same design conversation as kube-router even though it is not a replacement for kube-router?

<details>
<summary>Show Answer</summary>

Multus appears when pods need more than the default Kubernetes network interface, such as a storage data network, telecom data plane, SR-IOV interface, or separated management and workload networks. Kube-router can provide the default pod network, Service proxy, and policy enforcement, while Multus acts as a meta-plugin that calls additional CNI plugins for secondary interfaces. The two tools answer different questions: kube-router can own primary cluster networking, while Multus attaches extra networks to selected pods.

</details>

## Hands-On Exercise

This exercise is designed as an inspection lab rather than a production installation guide. You will create a disposable kind cluster without the default CNI and without kube-proxy, install kube-router from the upstream lab manifest, verify the three dataplane responsibilities, and then delete the cluster. Upstream manifests change, so use this lab to practice the mental model and consult current kube-router docs before adapting any command to a long-lived cluster.

### Objective

Deploy kube-router in a local test cluster, verify that pod networking produces routes, verify that Services appear in IPVS, and verify that NetworkPolicy changes alter connectivity. The goal is not to tune BGP for a laptop; the goal is to connect Kubernetes objects to the Linux artifacts kube-router programs on each node.

### Prerequisites

- [ ] `kind` is installed and can create Docker-backed clusters
- [ ] `kubectl` points to the kind cluster after creation
- [ ] The host can pull images from the public registries used by kind and kube-router
- [ ] You are using a disposable lab environment, not a shared production cluster

### Part 1: Create a Cluster Without Default CNI or kube-proxy

The cluster starts without a pod network and without kube-proxy so kube-router can own both responsibilities. Nodes may be `NotReady` until the CNI is installed, which is expected in this lab because kubelet cannot mark the pod network ready before a CNI writes valid node configuration.

```bash
cat > kind-kube-router.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  kubeProxyMode: none
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/16"
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

kind create cluster --config kind-kube-router.yaml --name kube-router-lab
kubectl get nodes -o wide
```

### Part 2: Install Kube-Router

Apply the upstream all-service DaemonSet for a lab cluster and wait for kube-router pods to become ready. For production, pin an image tag, review RBAC, review host mounts, and read the current upstream deployment guide instead of applying a moving branch manifest directly.

```bash
kubectl apply -f https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kube-router-all-service-daemonset.yaml

kubectl -n kube-system wait --for=condition=Ready \
  pod -l k8s-app=kube-router --timeout=180s

kubectl get nodes
```

### Part 3: Verify Routing and Service State

These checks connect the control-plane story to the node dataplane. Routes show whether pod CIDRs are reachable through node IPs, and IPVS state shows whether Services are being represented as virtual services with real endpoint servers.

```bash
KR_POD="$(kubectl -n kube-system get pod -l k8s-app=kube-router \
  -o jsonpath='{.items[0].metadata.name}')"

kubectl -n kube-system exec "$KR_POD" -- ip route show
kubectl -n kube-system exec "$KR_POD" -- ipvsadm -Ln
```

### Part 4: Create a Service and Test NetworkPolicy

This workload gives you one Service path and one policy path to test. The default-deny policy should block ingress to selected pods, and the allow policy should permit only the labeled client to reach the web pods on port 80.

```bash
kubectl create namespace kr-test

kubectl -n kr-test create deployment web --image=nginx:alpine --replicas=2
kubectl -n kr-test expose deployment web --port=80 --target-port=80
kubectl -n kr-test run client --image=busybox:1.36 --restart=Never -- sleep 3600
kubectl -n kr-test wait --for=condition=Available deployment/web --timeout=90s
kubectl -n kr-test wait --for=condition=Ready pod/client --timeout=60s

kubectl -n kr-test exec client -- wget -qO- --timeout=5 http://web

kubectl -n kr-test apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

kubectl -n kr-test exec client -- wget -qO- --timeout=5 http://web \
  && echo "unexpected allow" || echo "blocked as expected"

kubectl -n kr-test label pod client access=web

kubectl -n kr-test apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-client-to-web
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          access: web
    ports:
    - protocol: TCP
      port: 80
EOF

kubectl -n kr-test exec client -- wget -qO- --timeout=5 http://web
```

### Part 5: Inspect What Changed

After the workload and policies exist, inspect the Linux state again. You should be able to connect the Service to an IPVS virtual server and connect the NetworkPolicy to kube-router-created sets and firewall chains. Exact names can vary by version, so inspect patterns rather than memorizing one chain name from a lab.

```bash
kubectl -n kube-system exec "$KR_POD" -- ipvsadm -Ln
kubectl -n kube-system exec "$KR_POD" -- ipset list -name | grep KUBE
kubectl -n kube-system exec "$KR_POD" -- iptables -S | grep KUBE-ROUTER
```

### Success Criteria

- [ ] Nodes become `Ready` after kube-router is installed
- [ ] Pod-to-pod routing works by direct pod IP or through the test Service
- [ ] `ipvsadm -Ln` shows virtual service state for Kubernetes Services
- [ ] The default-deny policy blocks the unlabeled client path
- [ ] The allow policy restores access for the labeled client
- [ ] `ipset` and `iptables` inspection shows kube-router policy artifacts
- [ ] The lab cluster is deleted after testing

### Cleanup

```bash
kind delete cluster --name kube-router-lab
rm -f kind-kube-router.yaml
```

## Key Takeaways

Kube-router is most useful as a teaching case because it exposes the three jobs every Kubernetes networking stack must cover. Pod networking makes pod IPs reachable, Service proxying turns stable virtual IPs into endpoint traffic, and NetworkPolicy enforcement turns API intent into node-level packet decisions. Kube-router can do all three with one daemon, but the deeper lesson is how to verify each job separately.

Native Layer 3 routing and overlay networking are tradeoffs, not moral categories. Overlay networks are easy to deploy because the underlay only needs to route node IPs, while native routing avoids encapsulation overhead when the fabric can carry pod CIDRs. Kube-router's BGP design is attractive when your network can participate in that route model, and risky when your fabric, cloud, or operations process cannot support it.

IPVS service proxying changes the Service dataplane from rule-chain forwarding toward a kernel load-balancer model with virtual services, real servers, and scheduling algorithms. That can improve scaling characteristics compared with large iptables rule sets, but responsible engineering avoids invented benchmark claims and tests the actual workload. Service proxy ownership also must be exclusive: kube-proxy and kube-router should not both manage the same Service path.

Standard Kubernetes NetworkPolicy remains L3/L4 intent even when a capable plugin enforces it well. Kube-router's iptables and ipset approach is understandable with familiar Linux tools and is enough for many segmentation needs. If you need richer policy language, built-in flow observability, or application-layer decisions, compare the capability requirements against Cilium, Calico policy features, or service mesh controls rather than expecting standard NetworkPolicy to become something it is not.

## Sources

- [Kube-router official site](https://www.kube-router.io/)
- [Kube-router architecture docs](https://www.kube-router.io/docs/architecture/)
- [Kube-router user guide](https://www.kube-router.io/docs/user-guide/)
- [Kube-router DSR docs](https://www.kube-router.io/docs/dsr/)
- [Kube-router GitHub repository](https://github.com/cloudnativelabs/kube-router)
- [Kube-router release page](https://github.com/cloudnativelabs/kube-router/releases)
- [Kube-router how-it-works docs](https://github.com/cloudnativelabs/kube-router/blob/master/docs/how-it-works.md)
- [CNI specification](https://github.com/containernetworking/cni/blob/main/SPEC.md)
- [Kubernetes Services, Load Balancing, and Networking](https://kubernetes.io/docs/concepts/services-networking/)
- [Kubernetes Network Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/)
- [Kubernetes NetworkPolicy docs](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Kubernetes Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/)
- [Kubernetes IPVS-based load balancing deep dive](https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/)
- [Linux Virtual Server IPVS reference](https://kb.linuxvirtualserver.org/wiki/IPVS)
- [GoBGP repository](https://github.com/osrg/gobgp)
- [BGP RFC 4271](https://datatracker.ietf.org/doc/html/rfc4271)
- [Flannel repository](https://github.com/flannel-io/flannel)
- [Calico BGP peering docs](https://docs.tigera.io/calico/latest/networking/configuring/bgp)
- [Calico overlay networking docs](https://docs.tigera.io/calico/latest/networking/configuring/vxlan-ipip)
- [Cilium kube-proxy replacement docs](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/)
- [Cilium routing docs](https://docs.cilium.io/en/stable/network/concepts/routing/)
- [Cilium BGP control plane docs](https://docs.cilium.io/en/stable/network/bgp-control-plane/bgp-control-plane/)
- [Multus CNI repository](https://github.com/k8snetworkplumbingwg/multus-cni)
- [CNCF CNI project page](https://www.cncf.io/projects/container-network-interface-cni/)
- [CNCF announcement of Cilium graduation](https://www.cncf.io/announcements/2023/10/11/cloud-native-computing-foundation-announces-cilium-graduation/)

## Next Module

Continue to [Module 5.8: Multus](../module-5.8-multus/) to learn how Kubernetes attaches multiple networks to selected pods, or revisit [Module 5.5: Flannel](../module-5.5-flannel/) to compare overlay-first simplicity with kube-router's native Layer 3 routing model.
