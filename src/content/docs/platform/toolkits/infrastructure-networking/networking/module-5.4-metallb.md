---
qa_pending: true
title: "Module 5.4: MetalLB - Load Balancing for Bare-Metal Kubernetes"
slug: platform/toolkits/infrastructure-networking/networking/module-5.4-metallb
sidebar:
  order: 5
---

# Module 5.4: MetalLB - Load Balancing for Bare-Metal Kubernetes

> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: ~45 minutes

**Prerequisites**:

- Kubernetes Services, especially ClusterIP, NodePort, and LoadBalancer.
- Basic IP networking, including subnets, ARP, routing, and TCP ports.
- Helm basics for installing controllers into a Kubernetes cluster.
- A local kind or minikube cluster for the hands-on exercise.
- Optional: basic BGP vocabulary if you want to understand the production mode deeply.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Diagnose** why a bare-metal Kubernetes `LoadBalancer` Service remains in `<pending>` and identify which part of the service exposure chain is missing.
- **Configure** MetalLB address pools and advertisements for Layer 2 service exposure in a local or lab cluster.
- **Compare** Layer 2 and BGP modes using topology, failover, throughput, and operational ownership criteria.
- **Design** a safe IP allocation strategy that avoids DHCP overlap, tenant confusion, and silent address exhaustion.
- **Evaluate** whether MetalLB should expose individual applications directly, an Ingress controller, or a Gateway API implementation.

---

## Why This Module Matters

The platform team thought the migration would be boring, and boring was exactly what they wanted. Their payment gateway already ran on Kubernetes in the cloud, the manifests were reviewed, and the new on-prem cluster had passed its smoke tests. A developer applied the same Service manifest that worked in GKE, watched `kubectl get svc`, and waited for the familiar external IP to appear.

It did not appear. The Service stayed in `<pending>` through the standup, through lunch, through the end of the day, and through several increasingly nervous redeployments. Nothing in the workload logs looked broken because the workload was not broken. Kubernetes had accepted the Service, created the internal plumbing, and then stopped at the exact place where a cloud provider normally takes over.

By the second week, the team had worked around the problem with NodePorts. The application was reachable, but every new service needed firewall tickets, documentation drifted, and the network team had to ask why production traffic was being sent to random high ports on worker nodes. The cluster was technically functional, yet the operating model felt improvised.

The missing piece was not a Deployment setting or a kube-proxy flag. It was a load balancer implementation. Kubernetes defines `type: LoadBalancer` as an interface: "someone should assign an external IP and make traffic reach this Service." Cloud clusters include a controller that fulfills that interface by calling the provider API. Bare-metal clusters do not have that provider API unless you add something that can speak to your network.

MetalLB fills that gap. It watches for LoadBalancer Services, allocates an IP from a pool you own, and advertises that IP so clients outside the cluster can reach it. In small environments, it can do this with ordinary Layer 2 neighbor discovery. In larger environments, it can use BGP so routers learn service routes from the cluster itself.

A senior platform engineer needs more than the installation command. They need to understand where traffic enters the cluster, what node owns the advertised address, how failover happens, why IP pools must be coordinated with the network team, and when BGP changes the reliability model. This module builds that mental model before asking you to operate MetalLB.

---

## Core Content

## Part 1: The LoadBalancer Contract Kubernetes Does Not Fulfill Alone

A Kubernetes Service has two different jobs that are easy to confuse. Inside the cluster, it gives pods a stable virtual IP and a stable DNS name. Outside the cluster, a `LoadBalancer` Service asks some external system to create a reachable address and forward traffic into the cluster.

The first job is handled by Kubernetes networking components such as kube-proxy, IPVS, or eBPF dataplanes. The second job is intentionally delegated. Kubernetes can store a Service object that says `type: LoadBalancer`, but it cannot invent a physical network path without help from the environment around the cluster.

In a cloud cluster, that help comes from a cloud-controller-manager. When you create a LoadBalancer Service on AWS, Google Cloud, or Azure, a controller sees the Service and calls the provider API. The provider then creates a real load balancer, reserves an external IP, updates routing, and reports the IP back into the Service status.

In a bare-metal cluster, there is no provider API by default. The API server accepts the Service, the controller manager records that a LoadBalancer was requested, and then nothing allocates or announces an external address. That is why the `EXTERNAL-IP` column stays in `<pending>` even though the Service object itself is valid.

```ascii
CLOUD KUBERNETES                         BARE-METAL KUBERNETES
+----------------------+                 +----------------------+
| Service manifest     |                 | Service manifest     |
| type: LoadBalancer   |                 | type: LoadBalancer   |
+----------+-----------+                 +----------+-----------+
           |                                        |
           v                                        v
+----------------------+                 +----------------------+
| Cloud controller     |                 | No cloud controller  |
| watches the Service  |                 | implementation       |
+----------+-----------+                 +----------+-----------+
           |                                        |
           v                                        v
+----------------------+                 +----------------------+
| Provider API creates |                 | Service status stays |
| external LB and IP   |                 | EXTERNAL-IP pending  |
+----------+-----------+                 +----------------------+
           |
           v
+----------------------+
| Service receives     |
| a reachable address  |
+----------------------+
```

This is the first important design lesson: `LoadBalancer` is not a magic service type. It is a contract between Kubernetes and an infrastructure-specific implementation. If the implementation is absent, Kubernetes does not fail the Service because the Service definition is still syntactically and semantically valid.

You can see the symptom with a minimal Service. The examples in this module use `k` as a short alias for `kubectl`. If your shell does not already define it, run `alias k=kubectl` for the current terminal session.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echo
  template:
    metadata:
      labels:
        app: echo
    spec:
      containers:
        - name: echo
          image: hashicorp/http-echo:1.0
          args:
            - "-text=hello from bare metal"
          ports:
            - containerPort: 5678
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: echo
spec:
  type: LoadBalancer
  selector:
    app: echo
  ports:
    - name: http
      port: 80
      targetPort: 5678
```

```bash
k apply -f echo-deployment.yaml
k apply -f echo-service.yaml
k get svc echo
```

A bare-metal cluster without a load balancer implementation will show a Service similar to this. The cluster IP exists because Kubernetes owns that internal abstraction. The external IP is pending because no controller has allocated or advertised one.

```text
NAME   TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
echo   LoadBalancer   10.96.120.15    <pending>     80:31822/TCP   2m
```

> **Pause and predict:** If you changed this Service from `LoadBalancer` to `NodePort`, would that fix the missing external IP problem or merely bypass it? Before reading on, decide which component would receive traffic from outside the cluster and what operational burden that creates.

NodePort bypasses the missing load balancer by opening a high port on every node. That can be useful for debugging, but it pushes service discovery, firewall rules, and stable addressing onto people and runbooks. MetalLB exists so teams can keep the normal Kubernetes `LoadBalancer` contract instead of turning every production exposure into a custom NodePort exception.

| Service type | Who owns the stable address? | External reachability model | Typical bare-metal use |
|--------------|------------------------------|-----------------------------|------------------------|
| ClusterIP | Kubernetes control plane | Not reachable from outside the cluster | Internal app-to-app traffic |
| NodePort | Every node listens on a high port | Client connects to node IP plus assigned port | Debugging, simple labs, emergency bypass |
| LoadBalancer with cloud provider | Cloud load balancer controller | Provider allocates and routes an external IP | Managed Kubernetes in public cloud |
| LoadBalancer with MetalLB | MetalLB controller and speakers | MetalLB allocates and advertises an external IP | Bare-metal and self-managed clusters |

The distinction matters during incident response. If a Service is pending, inspecting pod logs will not answer the core question. You need to inspect the load balancer implementation, the address pool, and the advertisement path. The workload can be perfectly healthy while the network has no idea where the requested IP lives.

---

## Part 2: What MetalLB Adds to the Cluster

MetalLB has two responsibilities that map directly to the missing parts of the LoadBalancer contract. The controller allocates service IP addresses from configured pools. The speakers advertise those allocated IPs to the surrounding network so packets can reach a node in the cluster.

The controller is usually a Deployment because allocation is a control-plane decision. It watches Services and MetalLB custom resources, chooses an address, and writes that address into the Service status. The speakers run as a DaemonSet because advertisement is node-local work. Each node may need to answer ARP, send neighbor discovery messages, or establish BGP sessions.

```ascii
+---------------------------------------------------------------+
|                        Kubernetes API                         |
|                                                               |
|  Service: echo                                                |
|  type: LoadBalancer                                           |
|  status.loadBalancer.ingress: 192.168.50.240                  |
+------------------------------+--------------------------------+
                               ^
                               |
                 +-------------+-------------+
                 | MetalLB controller        |
                 | allocates IPs from pools  |
                 +-------------+-------------+
                               |
                               v
+------------------------------+--------------------------------+
|                 MetalLB custom resources                      |
|                                                               |
|  IPAddressPool        -> which IPs may be assigned             |
|  L2Advertisement      -> which pools are announced with ARP    |
|  BGPPeer              -> which routers speakers peer with      |
|  BGPAdvertisement     -> which pools are announced with BGP    |
+------------------------------+--------------------------------+
                               |
                               v
+-------------+        +-------------+        +-------------+
| Speaker     |        | Speaker     |        | Speaker     |
| on node-a   |        | on node-b   |        | on node-c   |
+------+------+        +------+------+        +------+------+
       |                      |                      |
       v                      v                      v
  Local network          Local network          Local network
  advertisement          advertisement          advertisement
```

The smallest useful MetalLB configuration has an `IPAddressPool` and an advertisement resource. The pool answers "which addresses may MetalLB assign?" The advertisement answers "how should those addresses be made reachable?" Leaving out either part creates a half-configured system.

For a lab or small flat network, the pool usually contains a range of addresses that are inside the local subnet but outside DHCP assignment. If your router hands out `192.168.1.100` through `192.168.1.199`, you might reserve `192.168.1.240` through `192.168.1.250` for service IPs. The exact range is an infrastructure decision, not a Kubernetes preference.

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
    - 192.168.1.240-192.168.1.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - default-pool
```

When this configuration exists, a new LoadBalancer Service can receive an external IP from the pool. MetalLB does not create a new appliance or proxy pod for every Service. It makes the IP reachable through the nodes that already run your cluster networking.

That design is powerful because it keeps service exposure Kubernetes-native. Application teams continue to request `type: LoadBalancer`. Platform teams control address ranges, advertisement methods, and operational policy. Network teams can see which address blocks are delegated to the cluster instead of reverse-engineering a collection of NodePorts.

It also means MetalLB is not a complete application routing layer. It does not replace an Ingress controller, Gateway API implementation, service mesh, or HTTP routing policy. MetalLB gets packets for an external IP to the cluster. What happens after the packet reaches the Service still depends on Kubernetes Services and the workloads behind them.

> **Active check:** You create an `IPAddressPool`, and `k get svc` now shows an external IP, but `curl` from your laptop times out. Which half of MetalLB is probably working, and which half should you inspect next? Explain your answer using allocation versus advertisement.

A practical diagnosis starts by separating state from reachability. If the Service status has an IP, allocation worked. If clients cannot reach that IP, inspect advertisement, node reachability, firewall rules, ARP or BGP state, and whether the selected node can forward traffic to healthy endpoints.

```bash
k get svc echo
k describe svc echo
k get ipaddresspools.metallb.io -n metallb-system
k get l2advertisements.metallb.io -n metallb-system
k get pods -n metallb-system -o wide
```

The MetalLB resources give you a clean boundary for ownership. Kubernetes users should not guess random IPs in Service manifests unless the platform team has documented an allowed pool and policy. The platform team should not allow a pool that overlaps DHCP, router addresses, node addresses, or addresses used by external appliances.

---

## Part 3: Layer 2 Mode, Simple Reachability with One Active Owner

Layer 2 mode is the easiest way to make MetalLB useful. It relies on the same neighbor discovery behavior that ordinary machines use on a local network. For IPv4, clients ask "who has this IP?" using ARP. For IPv6, they use Neighbor Discovery Protocol. One MetalLB speaker answers for the service IP.

The key phrase is "one speaker." In Layer 2 mode, a single node owns a given service IP at any moment. That node receives traffic for the IP and then Kubernetes service routing sends packets to the selected backend pods. The pods may live on the same node or on different nodes.

```ascii
LAYER 2 MODE FOR ONE SERVICE IP

+------------+       ARP request        +-----------------------+
| Client     | -----------------------> | Local network segment |
| 192.168.1.8| "Who has .240?"          +-----------+-----------+
+------------+                                      |
                                                    |
                                                    v
                                           +--------+--------+
                                           | node-b speaker  |
                                           | answers for IP  |
                                           | 192.168.1.240   |
                                           +--------+--------+
                                                    |
                                                    v
                                           +--------+--------+
                                           | kube-proxy or   |
                                           | eBPF service    |
                                           | routing         |
                                           +--------+--------+
                                                    |
                         +--------------------------+--------------------------+
                         |                          |                          |
                         v                          v                          v
                  +-------------+            +-------------+            +-------------+
                  | pod on      |            | pod on      |            | pod on      |
                  | node-a      |            | node-b      |            | node-c      |
                  +-------------+            +-------------+            +-------------+
```

The elected speaker is chosen deterministically by the MetalLB speakers. They do not need a central leader-election object for every IP. Each speaker can calculate which node should announce a service based on shared cluster information, and only the selected node responds for that address.

Failover is straightforward but not instantaneous. If the owning node disappears, another speaker begins announcing the IP. Clients and switches may still have cached the old MAC address for a short time, so traffic can pause until neighbor caches update. MetalLB sends updates to speed this along, but Layer 2 failover remains bounded by local network behavior.

Layer 2 mode is often the right starting point because it has a low coordination cost. You need an address range and a local subnet where nodes can answer for those addresses. You do not need router BGP configuration, autonomous system numbers, or ECMP policy. That makes it excellent for labs, edge clusters, homelabs, small offices, and controlled internal platforms.

The trade-off is throughput and node concentration. Since one node owns the IP for a Service, all traffic for that Service enters through that node. Kubernetes may still spread requests to pods across the cluster after traffic enters, but the first hop is not horizontally distributed. For high-throughput Services, that node can become the bottleneck.

A second trade-off is topology. Layer 2 mode assumes the relevant clients and nodes share a network segment where ARP or NDP behavior makes sense. If your cluster nodes sit behind routed boundaries, multiple VLANs, or strict network segmentation, BGP may fit the topology better.

| Layer 2 question | Good sign | Warning sign | Design response |
|------------------|-----------|--------------|-----------------|
| Are nodes on the same subnet as the service IPs? | Nodes can answer ARP for the pool | Service IP is on a distant routed network | Use a local pool or consider BGP |
| Is traffic volume modest? | One node can handle expected ingress | One Service may saturate a node NIC | Use BGP or another load balancer layer |
| Is fast failover critical? | Short interruption is acceptable | Seconds of disruption are unacceptable | Tune environment or use BGP |
| Can the network team reserve a pool? | Dedicated range outside DHCP exists | Address ownership is unclear | Stop and reserve addresses first |
| Is operational simplicity the priority? | Small team owns the cluster and subnet | Router policy must be centrally managed | Layer 2 may be the safer first step |

You should also understand the effect of `externalTrafficPolicy`. With the default `Cluster` policy, traffic can enter through the MetalLB-owning node and then be forwarded to pods anywhere in the cluster. This maximizes backend availability but may hide the original client IP depending on the dataplane and path.

With `externalTrafficPolicy: Local`, nodes only forward external traffic to local endpoints. This can preserve client source IPs for applications that need them, but it changes readiness and traffic distribution. If the MetalLB-owning node has no local pod for that Service, traffic may fail until ownership or endpoints change.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: echo-local
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local
  selector:
    app: echo
  ports:
    - name: http
      port: 80
      targetPort: 5678
```

> **Pause and predict:** In Layer 2 mode, imagine a Service uses `externalTrafficPolicy: Local`, and the elected speaker node has no matching backend pod. What symptom would a client see, and what two changes could you make to restore traffic?

The clean answers are to either schedule endpoints on nodes that can own the address or change the traffic policy back to `Cluster` when source IP preservation is not required. A less direct answer is to influence speaker eligibility with node selectors or pool scoping, but that should follow a deliberate design rather than a quick guess during an outage.

Layer 2 mode is not "toy mode." Many real clusters use it successfully because their traffic profile and topology are simple. The senior move is not to reject it because BGP sounds more advanced. The senior move is to recognize the bottleneck, failover, and subnet assumptions before they become production surprises.

---

## Part 4: BGP Mode, Routing-Based Distribution for Production Networks

BGP mode changes the relationship between the cluster and the network. Instead of one node answering neighbor discovery for a service IP, MetalLB speakers establish BGP sessions with routers. The speakers advertise routes for service IPs, and the router decides how to forward traffic based on its routing table.

BGP is the Border Gateway Protocol, the same family of routing protocol used across large networks and the Internet. In a datacenter, it is commonly used between servers, top-of-rack switches, and routing infrastructure. MetalLB uses BGP in a focused way: it tells routers that service IPs are reachable through cluster nodes.

```ascii
BGP MODE WITH ECMP

                  +-----------------------------+
                  | Top-of-rack router          |
                  | Route: 10.0.100.20/32       |
                  | next hops: node-a,node-b    |
                  |            node-c           |
                  +--------------+--------------+
                                 ^
              BGP session        |        BGP session
          +----------------------+----------------------+
          |                      |                      |
+---------+---------+  +---------+---------+  +---------+---------+
| node-a speaker    |  | node-b speaker    |  | node-c speaker    |
| announces service |  | announces service |  | announces service |
| IP reachability   |  | IP reachability   |  | IP reachability   |
+---------+---------+  +---------+---------+  +---------+---------+
          |                      |                      |
          v                      v                      v
+---------+---------+  +---------+---------+  +---------+---------+
| local backend or  |  | local backend or  |  | local backend or  |
| service routing   |  | service routing   |  | service routing   |
+-------------------+  +-------------------+  +-------------------+
```

When the router sees multiple equal-cost paths to the same service IP, it can use ECMP, or Equal-Cost Multi-Path routing. ECMP distributes flows across next hops, usually by hashing packet fields such as source IP, destination IP, and ports. This means traffic can enter through multiple nodes instead of a single elected owner.

This is the main production advantage of BGP mode. A high-traffic Service can use the aggregate ingress capacity of several nodes. If one node fails, its BGP session drops or its route is withdrawn, and the router removes that next hop from the forwarding table. The result is usually faster and cleaner failover than waiting for ARP caches to age out.

The cost is operational complexity. BGP requires router configuration, autonomous system numbers, peer addresses, route policy, and an agreement with the network team about what the cluster may advertise. A misconfigured BGP session can fail silently from the application team's perspective because the Kubernetes Service may still show an external IP while the router refuses or filters the route.

A minimal MetalLB BGP configuration defines the peer and the advertisement. The `myASN` is the autonomous system number MetalLB uses for the cluster side of the session. The `peerASN` and `peerAddress` identify the router. Real values must come from your network design.

```yaml
apiVersion: metallb.io/v1beta2
kind: BGPPeer
metadata:
  name: tor-router
  namespace: metallb-system
spec:
  myASN: 64500
  peerASN: 64501
  peerAddress: 10.0.0.1
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: production-services
  namespace: metallb-system
spec:
  addresses:
    - 10.0.100.0/24
---
apiVersion: metallb.io/v1beta1
kind: BGPAdvertisement
metadata:
  name: production-services
  namespace: metallb-system
spec:
  ipAddressPools:
    - production-services
```

This cluster-side configuration is only half the setup. The router must accept BGP sessions from the node addresses, allow the expected ASN relationship, and permit the service prefixes. In many organizations, the router configuration belongs to a different team and goes through a change process. Treat that as part of the production design, not an administrative inconvenience.

BGP also changes how you think about failure domains. A Layer 2 problem may affect one VLAN or one owning node. A BGP policy problem may affect route propagation beyond the local rack. If the network redistributes MetalLB routes into a broader routing domain, the blast radius of bad advertisements increases. That is why tight prefix filters and dedicated service ranges are non-negotiable.

| Criterion | Layer 2 mode | BGP mode |
|-----------|--------------|----------|
| Network dependency | Local subnet and neighbor discovery | BGP-capable routers and route policy |
| Traffic entry point | One node per service IP | Multiple nodes through router ECMP |
| Failover mechanism | New speaker answers ARP or NDP | Route withdrawal or BGP session failure |
| Throughput scaling | Limited by owning node ingress path | Can scale across announcing nodes |
| Operational owner | Mostly platform team plus IP reservation | Platform team and network team jointly |
| Common first use | Labs, edge, small clusters, simple sites | Production datacenters and high-traffic services |
| Main risk | Hidden single-node bottleneck | Bad route policy or unsafe advertisements |
| Best diagnostic signal | ARP or NDP ownership and speaker logs | BGP session state and router route table |

> **Active check:** Your team expects BGP mode to balance every HTTP request evenly across all nodes, but one node receives more traffic than the others. Why might that still be normal, and what does ECMP usually balance?

ECMP usually balances flows, not individual requests. If a few clients create long-lived connections, the hash may place those flows on the same node for a while. That is not necessarily a MetalLB bug. To evaluate distribution correctly, test with many clients and connections, then compare router next-hop counters and node-level traffic.

BGP mode is a strong fit when the cluster is part of a routed datacenter fabric. It is less attractive when the network team cannot support it, when route policy is opaque, or when the cluster serves a small amount of traffic on a simple subnet. A production-grade decision accounts for both technical capability and organizational ownership.

---

## Part 5: IP Address Management, Pool Design, and Tenant Boundaries

MetalLB makes external IPs feel easy, which is exactly why IP management must be deliberate. A pool is not just a list of numbers. It is a contract that says these addresses are reserved for Kubernetes Services, should not be assigned by DHCP, should not belong to physical appliances, and should be monitored like other scarce infrastructure.

The most common failure is overlap. If MetalLB advertises an address that DHCP later assigns to a laptop, printer, VM, or router interface, the network can become intermittently broken in ways that look random. One client may reach the Service, another may reach the wrong host, and packet captures show competing answers for the same IP.

A safer design starts outside Kubernetes. Reserve the range in IPAM, DHCP, router documentation, or whatever source of truth your organization uses. Label it as Kubernetes service IP space. Decide whether the range is shared by all teams or divided by namespace, environment, application class, or cluster.

```ascii
EXAMPLE ADDRESS PLAN FOR ONE SITE

+----------------------+----------------------+-----------------------------+
| Range                | Owner                | Purpose                     |
+----------------------+----------------------+-----------------------------+
| 192.168.20.1-20      | Network team         | Gateways and appliances     |
| 192.168.20.21-99     | Platform team        | Kubernetes node addresses   |
| 192.168.20.100-199   | DHCP                 | User and lab devices        |
| 192.168.20.200-219   | Platform team        | Ingress and Gateway VIPs    |
| 192.168.20.220-239   | Platform team        | App LoadBalancer Services   |
| 192.168.20.240-250   | Reserved             | Future expansion            |
+----------------------+----------------------+-----------------------------+
```

MetalLB supports multiple pools, which lets you encode operational intent. You might create one pool for shared ingress controllers, another for team-owned services, and another for temporary lab workloads. That separation makes review easier because a Service requesting a production-facing address should not accidentally consume a lab IP.

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: ingress-vips
  namespace: metallb-system
spec:
  addresses:
    - 192.168.20.200-192.168.20.219
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: app-services
  namespace: metallb-system
spec:
  addresses:
    - 192.168.20.220-192.168.20.239
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: site-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - ingress-vips
    - app-services
```

By default, MetalLB can assign from available pools automatically. For controlled environments, teams may request a specific address with annotations or `loadBalancerIP` patterns depending on Kubernetes and MetalLB behavior. Use that sparingly. Static requests are useful for DNS records and allowlists, but unmanaged static claims can turn the Service manifest into a shadow IPAM database.

A better platform pattern is to expose only a small number of stable addresses directly. For example, one LoadBalancer Service fronts an Ingress controller, and HTTP routing sends traffic to many applications. That consumes one or a few external IPs instead of one per application. It also concentrates TLS, access logs, WAF integration, and routing policy in one layer.

Some applications genuinely need their own LoadBalancer Service. Databases, non-HTTP protocols, dedicated appliances, and tenant-isolated gateways may not fit behind a shared Ingress. The point is not to forbid direct LoadBalancers. The point is to make the choice explicit so scarce IP space and network policy do not drift.

| Exposure pattern | IP consumption | Best fit | Operational caution |
|------------------|----------------|----------|---------------------|
| One shared Ingress controller | Low | Many HTTP apps using hostnames and paths | Ingress becomes a critical shared dependency |
| Gateway API with shared Gateway | Low to medium | Teams need delegated HTTP/TCP routing policy | Requires clear GatewayClass ownership |
| Direct LoadBalancer per app | Medium to high | Non-HTTP apps or strict isolation | Pool exhaustion and firewall sprawl |
| Direct LoadBalancer per tenant | Medium | Tenant-specific ingress boundaries | Needs tenant-aware address allocation policy |
| NodePort workaround | Low IP use, high port complexity | Short debugging windows | Avoid as a long-term production pattern |

> **Pause and predict:** A team asks for ten direct LoadBalancer Services for ten HTTP applications. What design would you propose first, and what question would make you approve direct LoadBalancers anyway?

A shared Ingress controller or Gateway is usually the first proposal for HTTP because hostnames and paths can route many applications through fewer IPs. Direct LoadBalancers may still be justified when applications require distinct network policies, separate appliances, non-HTTP protocols, tenant isolation, or independent failure domains that are worth the extra IP and operational cost.

Monitoring should include pool utilization and pending Services. A pending Service is not always an installation failure; it can also mean MetalLB has no eligible address left. Pool exhaustion is a capacity event, not just a Kubernetes error. Treat service IPs like any other finite platform resource.

---

## Part 6: Integrating MetalLB with Ingress, Gateway API, and Troubleshooting Flow

MetalLB is usually most valuable when paired with a higher-level traffic router. Ingress controllers and Gateway API implementations understand HTTP hosts, paths, TLS, and sometimes TCP or UDP routes. MetalLB gives those routers a stable external IP. The router then decides which backend Service receives each request.

```ascii
COMMON PRODUCTION PATTERN

+-----------+       +-------------------------------+
| Client    | ----> | MetalLB external IP           |
| browser   |       | 192.168.20.205                |
+-----------+       +---------------+---------------+
                                    |
                                    v
                    +---------------+---------------+
                    | LoadBalancer Service          |
                    | for ingress-nginx or Envoy    |
                    +---------------+---------------+
                                    |
                                    v
                    +---------------+---------------+
                    | Ingress or Gateway controller |
                    | host and path routing         |
                    +-------+---------------+-------+
                            |               |
                            v               v
                   +--------+-----+  +------+---------+
                   | app-a Service|  | app-b Service  |
                   +--------------+  +----------------+
```

This pattern keeps MetalLB focused. It does not need to know about `api.example.com`, `/checkout`, TLS certificates, canary routing, or application ownership. It only needs to make the external IP reachable. The Ingress or Gateway layer handles application-level routing.

For Gateway API, the same idea applies with more explicit role separation. The platform team installs a Gateway controller and exposes it through a LoadBalancer Service. Application teams attach routes to allowed Gateways. MetalLB remains the network address provider beneath that higher-level API.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gateway-envoy
  namespace: gateway-system
spec:
  type: LoadBalancer
  selector:
    app: gateway-envoy
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: https
      port: 443
      targetPort: 8443
```

When something breaks, debug from the outside inward. Start with whether the Service has an external IP. Then check whether the network can reach that IP. Then check whether Kubernetes can route to endpoints. Finally inspect the application. This order prevents a common mistake: reading application logs while the packet never reaches the cluster.

```ascii
TROUBLESHOOTING ORDER

+-----------------------------+
| 1. Service has external IP? |
+--------------+--------------+
               |
               v
+-----------------------------+
| 2. IP advertised correctly? |
|    ARP/NDP or BGP state     |
+--------------+--------------+
               |
               v
+-----------------------------+
| 3. Node can receive traffic?|
|    firewall, routes, policy |
+--------------+--------------+
               |
               v
+-----------------------------+
| 4. Service has endpoints?   |
|    selectors and readiness  |
+--------------+--------------+
               |
               v
+-----------------------------+
| 5. Application responds?    |
|    logs and protocol checks |
+-----------------------------+
```

The command sequence follows the same logic. Use Service status to validate allocation. Use MetalLB resources and pods to validate configuration. Use endpoint slices to validate backend readiness. Then test network reachability from the client side and, if needed, from a node.

```bash
k get svc -A
k describe svc echo
k get ipaddresspools.metallb.io -n metallb-system
k get l2advertisements.metallb.io -n metallb-system
k get bgppeers.metallb.io -n metallb-system
k get bgpadvertisements.metallb.io -n metallb-system
k get pods -n metallb-system -o wide
k get endpointslice -l kubernetes.io/service-name=echo
```

If the Service has no external IP, focus on allocation. Check whether an address pool exists, whether the pool has free addresses, whether the Service is eligible for the pool, and whether MetalLB controller logs show an assignment error. The network path does not matter yet because no address has been assigned.

If the Service has an external IP but clients cannot connect, focus on advertisement and traffic path. In Layer 2 mode, inspect ARP behavior from a client on the same network and confirm speakers are running on nodes. In BGP mode, inspect BGP session state and router route tables with the network team. In both modes, check host firewalls, switch policy, and whether the selected node can forward to Service endpoints.

If the client reaches the IP but receives a reset, timeout, or wrong response, move into Kubernetes service routing and application behavior. Verify selectors, endpoint readiness, target ports, NetworkPolicies, Ingress or Gateway routes, and application logs. MetalLB may have done its job even when the user-facing request still fails.

---

## Worked Example: Turning a Pending Gateway into a Reachable Service

A team operates a three-node bare-metal Kubernetes cluster in a small datacenter lab. They installed an Envoy-based Gateway controller and created a Service named `gateway-envoy` with `type: LoadBalancer`. The Gateway pods are healthy, the Service has a cluster IP, and internal tests from another pod work. External clients cannot connect because the Service shows `<pending>`.

The team first confirms that the problem is not the Gateway controller. The Deployment is available, the pods are ready, and the Service selector matches the pods. The Service has a NodePort because Kubernetes creates one as part of LoadBalancer handling, but no external IP appears. That points to a missing or broken load balancer implementation rather than an application-layer routing issue.

```bash
k get deploy -n gateway-system
k get pods -n gateway-system -o wide
k get svc gateway-envoy -n gateway-system
k get endpointslice -n gateway-system -l kubernetes.io/service-name=gateway-envoy
```

The network team has reserved `192.168.30.220` through `192.168.30.229` for Kubernetes service IPs. The cluster nodes are on the same Layer 2 segment, and this lab does not need multi-node ingress throughput. Based on those constraints, the platform team chooses MetalLB Layer 2 mode instead of BGP. The decision is not "Layer 2 is easier" alone; it is "Layer 2 matches the subnet, traffic, and ownership model."

They install MetalLB and define a pool plus advertisement. The pool uses only the reserved range, not the whole subnet. The advertisement names that pool so speakers know to answer for addresses allocated from it.

```bash
helm repo add metallb https://metallb.github.io/metallb
helm repo update
helm install metallb metallb/metallb \
  --namespace metallb-system \
  --create-namespace \
  --wait
```

```bash
k apply -f - <<'EOF'
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: gateway-services
  namespace: metallb-system
spec:
  addresses:
    - 192.168.30.220-192.168.30.229
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: gateway-services-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - gateway-services
EOF
```

Within a few seconds, the Service receives an address from the pool. That proves the allocation half is working. The team records the assigned IP in the DNS change request for the lab domain, but they do not stop there because an assigned IP does not automatically prove traffic can reach the cluster.

```bash
k get svc gateway-envoy -n gateway-system
```

```text
NAME            TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)                      AGE
gateway-envoy   LoadBalancer   10.96.183.91    192.168.30.220   80:31480/TCP,443:32218/TCP   18m
```

Next they test reachability from a workstation on the same subnet. A `curl` to port 80 returns the expected Gateway response. That confirms the advertisement and basic Service path. If it had failed, their next checks would have been ARP ownership, speaker pod placement, firewall rules, and endpoint readiness in that order.

```bash
curl -i http://192.168.30.220
```

The final review is about future operations. The team documents that `192.168.30.220-192.168.30.229` belongs to MetalLB, that the Gateway controller should normally consume one address from that range, and that direct application LoadBalancers require platform approval. This prevents a small lab fix from becoming untracked production sprawl later.

This worked example shows the complete reasoning chain: identify the missing implementation, choose an advertisement mode based on topology, configure the minimum resources, verify allocation separately from reachability, and document ownership of the address range. The hands-on exercise asks you to follow the same chain in a kind cluster.

---

## Did You Know?

1. MetalLB moved from older ConfigMap-based configuration to custom resources such as `IPAddressPool`, `L2Advertisement`, `BGPPeer`, and `BGPAdvertisement`, so older tutorials may describe a configuration style you should avoid for modern installs.

2. In Layer 2 mode, MetalLB does not create a separate load balancer appliance. It makes one cluster node answer for the service IP, then normal Kubernetes Service routing handles backend pod selection.

3. BGP mode usually distributes flows rather than individual HTTP requests, so traffic may not look perfectly even when ECMP is working correctly.

4. Lightweight Kubernetes distributions may ship with their own service load balancer implementation, so installing MetalLB without disabling or coordinating the built-in component can create controller conflicts.

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|--------------|-----|
| Creating a LoadBalancer Service and expecting bare metal to behave like a cloud cluster | The Service remains in `<pending>` because no controller allocates or advertises an external IP | Install and configure a load balancer implementation such as MetalLB |
| Defining an `IPAddressPool` without an advertisement resource | The intended address range exists, but services may not become reachable because MetalLB lacks an announcement method | Pair each usable pool with an `L2Advertisement` or `BGPAdvertisement` |
| Choosing a pool that overlaps DHCP, node IPs, or appliance addresses | Two systems may claim the same address, causing intermittent and confusing connectivity failures | Reserve service ranges in IPAM or DHCP before applying MetalLB configuration |
| Treating Layer 2 mode as multi-node ingress load balancing | All traffic for one service IP enters through one elected node, which can become a bottleneck | Use BGP with ECMP or place a higher-level load balancer in front when throughput requires it |
| Enabling BGP without router-side prefix filters | A bad configuration can advertise unintended routes beyond the cluster boundary | Use dedicated service prefixes, explicit route policy, and network-team review |
| Running MetalLB beside another service load balancer controller | Controllers may compete to update LoadBalancer Service status or expose the same workloads differently | Disable the built-in implementation or define a clear ownership boundary |
| Debugging application logs before checking Service allocation and advertisement | Time is wasted inside healthy pods while the packet never reaches the cluster | Debug from Service status to network advertisement to endpoints to application behavior |
| Giving every HTTP app a direct LoadBalancer by default | IP pools are exhausted and firewall rules sprawl across many services | Prefer a shared Ingress controller or Gateway API layer unless direct exposure is justified |

---

## Quiz

Test your ability to apply the MetalLB model to real operating scenarios. Each question describes a situation; answer by reasoning from allocation, advertisement, topology, and service routing.

**Q1: Your team deploys a `LoadBalancer` Service on a kubeadm cluster in a datacenter. The pods are ready, the Service has a cluster IP, and the `EXTERNAL-IP` column stays in `<pending>`. A developer proposes restarting the Deployment. What should you check instead, and why?**

<details>
<summary>Show Answer</summary>

Check whether the cluster has a load balancer implementation such as MetalLB, and then check whether MetalLB has an address pool with available addresses. Restarting the Deployment targets the application layer, but the symptom is in Service status allocation. Kubernetes accepted the Service, but no external controller has assigned an address.
</details>

**Q2: A Service has received `192.168.40.230` from MetalLB, but clients on the local subnet cannot connect. The application works from another pod using the ClusterIP. What part of the system should you investigate first?**

<details>
<summary>Show Answer</summary>

Investigate advertisement and network reachability first. Allocation worked because the Service has an external IP. In Layer 2 mode, check speaker pods, ARP ownership, subnet placement, and firewall rules. In BGP mode, check BGP session state and whether the router learned the route.
</details>

**Q3: A small edge site has three worker nodes on one flat subnet, modest traffic, and no network team available to configure routers. The team wants stable external IPs for a shared Ingress controller. Which MetalLB mode would you choose first, and what limitation would you document?**

<details>
<summary>Show Answer</summary>

Choose Layer 2 mode first because it matches the flat subnet and does not require router BGP configuration. Document that each service IP is owned by one node at a time, so ingress throughput for that IP is limited by the owning node and failover depends partly on neighbor cache updates.
</details>

**Q4: A production datacenter cluster exposes a high-traffic TCP service. In Layer 2 mode, node network metrics show one node receiving nearly all ingress traffic for the service while other nodes are mostly idle. What design change would you evaluate?**

<details>
<summary>Show Answer</summary>

Evaluate BGP mode with router ECMP, assuming the network infrastructure can support it. Layer 2 mode has one active owner for a service IP, so the observed single-node ingress path is expected. BGP can allow multiple nodes to advertise the same service IP as equal-cost next hops.
</details>

**Q5: A platform team creates a MetalLB pool from `192.168.10.100` to `192.168.10.150` because the range looks unused. Two days later, office laptops intermittently lose connectivity when certain Services are deployed. What likely went wrong, and how should the team fix the process?**

<details>
<summary>Show Answer</summary>

The MetalLB pool likely overlaps with DHCP or another address owner. The fix is to reserve service IP ranges in the organization's IPAM or DHCP configuration before applying MetalLB resources. The team should treat service IP pools as managed infrastructure, not as addresses guessed from a quiet moment on the network.
</details>

**Q6: Your team runs a Gateway API controller behind a `LoadBalancer` Service. One application team asks for a separate direct LoadBalancer for every HTTP service they own. What architecture would you recommend first, and what would justify an exception?**

<details>
<summary>Show Answer</summary>

Recommend routing the HTTP services through the shared Gateway first because it conserves IPs and centralizes HTTP routing, TLS, and policy. A direct LoadBalancer may be justified for non-HTTP protocols, strict tenant isolation, separate network policy boundaries, or an application-specific failure domain that cannot share the Gateway.
</details>

**Q7: In BGP mode, a traffic test from one client shows most requests reaching the same node. A teammate concludes ECMP is broken. What additional test or explanation should you provide before changing the MetalLB configuration?**

<details>
<summary>Show Answer</summary>

Explain that ECMP commonly balances flows using a hash, not individual HTTP requests. A single client or a small number of long-lived connections may map to the same next hop. Test with many clients or many independent connections, and compare router next-hop counters before concluding that BGP or ECMP is misconfigured.
</details>

**Q8: A Service uses `externalTrafficPolicy: Local` because the application needs client source IPs. After a node drain, the external IP still exists, but requests fail until pods are rescheduled. What interaction should you analyze?**

<details>
<summary>Show Answer</summary>

Analyze whether the node receiving external traffic has local ready endpoints for that Service. With `externalTrafficPolicy: Local`, a node should only send traffic to local backends. If the advertised or selected ingress node has no matching pod, traffic can fail even though the Service still has an external IP. Fix by ensuring endpoint placement matches exposure requirements or by using `Cluster` policy when source IP preservation is not required.
</details>

---

## Hands-On Exercise: MetalLB on kind with Layer 2 Mode

**Goal**: Deploy MetalLB into a kind cluster, configure an address pool from the kind Docker network, expose a test application with a LoadBalancer Service, and verify that the external IP is reachable from your host.

**Time**: ~20 minutes

**Scenario**: You are the platform engineer for a small lab cluster. Developers want to use standard `LoadBalancer` Services instead of NodePorts. Your job is to install the missing implementation, reserve a safe address range inside the kind network, and prove that allocation and reachability both work.

**Success Criteria**:

- [ ] A kind cluster named `metallb-lab` exists and `k get nodes` shows the node or nodes as `Ready`.
- [ ] MetalLB controller and speaker pods are running in the `metallb-system` namespace.
- [ ] An `IPAddressPool` exists with addresses from the kind Docker network.
- [ ] An `L2Advertisement` references the address pool.
- [ ] A test `LoadBalancer` Service receives an external IP instead of staying in `<pending>`.
- [ ] `curl` to the assigned external IP returns a response from the test application.
- [ ] You can explain whether you verified allocation, advertisement, or application behavior at each step.

### Step 1: Create a Fresh kind Cluster

Create an isolated cluster for the lab. If you already have a kind cluster with the same name, delete it first or choose a different name.

```bash
kind create cluster --name metallb-lab
k cluster-info --context kind-metallb-lab
k get nodes
```

The node should be `Ready` before you install MetalLB. If the node is not ready, fix the kind environment first because MetalLB depends on normal Kubernetes scheduling and networking.

### Step 2: Identify the kind Docker Network Subnet

kind nodes run as Docker containers attached to the `kind` network. MetalLB needs addresses from that network so your host can route to the assigned service IP.

```bash
docker network inspect kind -f '{{(index .IPAM.Config 0).Subnet}}'
```

A common output is `172.18.0.0/16`, but your machine may differ. Pick a small range inside that subnet that is unlikely to collide with existing containers, such as the high end of the range. The example below uses `172.18.255.200-172.18.255.250`; adjust it if your subnet is different.

```bash
docker network inspect kind -f '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{println}}{{end}}'
```

This second command helps you avoid obvious collisions with existing kind node container addresses. In a real datacenter, this step would be replaced by IPAM and DHCP reservation.

### Step 3: Install MetalLB with Helm

Install MetalLB into its own namespace and wait for the chart to finish. The controller performs allocation, and the speaker DaemonSet performs advertisement.

```bash
helm repo add metallb https://metallb.github.io/metallb
helm repo update
helm install metallb metallb/metallb \
  --namespace metallb-system \
  --create-namespace \
  --wait
```

Verify the pods before applying configuration. A controller pod and at least one speaker pod should be running.

```bash
k get pods -n metallb-system -o wide
```

If the pods are not running, inspect events before continuing. Applying address pools will not help if the MetalLB control plane is unavailable.

```bash
k get events -n metallb-system --sort-by=.lastTimestamp
```

### Step 4: Configure the Address Pool and L2 Advertisement

Apply an address pool that matches your kind subnet. If your subnet is not `172.18.0.0/16`, replace the range before running the command.

```bash
k apply -f - <<'EOF'
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: kind-pool
  namespace: metallb-system
spec:
  addresses:
    - 172.18.255.200-172.18.255.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: kind-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - kind-pool
EOF
```

Verify that both resources exist. This confirms the configuration is present, but it does not yet prove that any Service has consumed an address.

```bash
k get ipaddresspools.metallb.io -n metallb-system
k get l2advertisements.metallb.io -n metallb-system
```

### Step 5: Deploy a Test Application

Deploy a small HTTP echo server so the response is easy to recognize. This is better than relying on a large default web page because you can tell exactly which service answered.

```bash
k create deployment echo \
  --image=hashicorp/http-echo:1.0 \
  --port=5678 \
  -- -text="hello from MetalLB"
```

Expose it with a LoadBalancer Service. This is the same Kubernetes interface application teams expect to use on cloud clusters.

```bash
k expose deployment echo \
  --type=LoadBalancer \
  --port=80 \
  --target-port=5678
```

### Step 6: Verify Address Allocation

Check the Service. The `EXTERNAL-IP` should become an address from your configured pool. If it remains pending for more than a short delay, describe the Service and inspect MetalLB configuration before moving to connectivity tests.

```bash
k get svc echo
```

Example output:

```text
NAME   TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)        AGE
echo   LoadBalancer   10.96.84.120    172.18.255.200   80:31080/TCP   30s
```

Describe the Service if you need more detail. Events often reveal whether allocation failed because no pool matched or no addresses were available.

```bash
k describe svc echo
```

### Step 7: Test Connectivity from the Host

Store the assigned IP in a shell variable, then call it with `curl`. This verifies more than allocation. It proves your host can reach the MetalLB-advertised address and that Kubernetes can route to the backend pod.

```bash
EXTERNAL_IP="$(k get svc echo -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
echo "$EXTERNAL_IP"
curl "http://${EXTERNAL_IP}"
```

Expected response:

```text
hello from MetalLB
```

If `curl` fails, keep the troubleshooting order disciplined. First confirm the IP was assigned. Then confirm the MetalLB speaker is running. Then confirm the Service has endpoints. Only after those checks should you inspect the application container.

```bash
k get svc echo
k get pods -n metallb-system -o wide
k get endpointslice -l kubernetes.io/service-name=echo
k logs deploy/echo
```

### Step 8: Explain What You Built

Write a short explanation for yourself or your team using these prompts. The goal is to make sure the lab produced an operating model, not just a successful command transcript.

- [ ] Which Kubernetes object requested an external IP?
- [ ] Which MetalLB object defined the addresses that could be assigned?
- [ ] Which MetalLB object told speakers how to advertise those addresses?
- [ ] Which command proved that allocation worked?
- [ ] Which command proved that client reachability and backend routing worked?
- [ ] What would change if this lab needed multi-node ingress distribution in a production datacenter?

### Cleanup

Delete the lab cluster when you are finished.

```bash
kind delete cluster --name metallb-lab
```

---

## Next Module

[Module 5.5: Ingress Controllers](../module-5.5-ingress-controllers/) teaches the HTTP routing layer that commonly sits behind a MetalLB-provided external IP.
