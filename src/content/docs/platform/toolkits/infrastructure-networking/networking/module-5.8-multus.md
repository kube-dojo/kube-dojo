---
title: "Module 5.8: Multus CNI — Multi-Network Pods for Specialized Workloads"
slug: platform/toolkits/infrastructure-networking/networking/module-5.8-multus
sidebar:
  order: 9
revision_pending: false
---

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 55-70 minutes

## The Pod That Needed Three Networks

Kubernetes was designed around a simple and powerful networking assumption: every pod gets exactly one network interface on one flat, routable network. For web applications serving HTTP APIs behind a Service, this model is not merely adequate — it is elegant. A pod boots, gets an IP from the cluster's CNI plugin, and every other pod in the cluster can reach it by that IP. The Service abstraction layers load balancing and discovery on top, and NetworkPolicy governs what can talk to what. This is the Kubernetes networking model, and for the vast majority of workloads it works beautifully.

But the world runs on more than HTTP APIs. A telecom provider deploying their 5G packet core on Kubernetes discovers that each network function — the Access and Mobility Management Function (AMF), the Session Management Function (SMF), the User Plane Function (UPF) — needs three physically separate network paths. A high-frequency trading system requires a market data feed on a dedicated interface that delivers sub-microsecond latency, isolated from the corporate management network. A high-performance computing cluster running MPI jobs across hundreds of nodes uses RDMA over InfiniBand — a network fabric that the kernel network stack was never designed to touch. A storage appliance demands a dedicated iSCSI network that never, under any circumstances, shares bandwidth with application traffic, because a storage backup saturating the management link will cause dropped control-plane packets and cascading failures.

These workloads all converge on the same requirement: **multiple, isolated network interfaces with different performance characteristics, attached to the same pod**. The standard Kubernetes networking model — one interface per pod, managed by one CNI plugin — was not designed for this. It was designed for the web-application use case, and for that use case it remains outstanding. But when an architect shows up with a 3GPP specification that mandates physical separation of signaling and user data planes, the single-interface model becomes a non-starter. This is not a hypothetical edge case — it is the central architectural challenge of running telecommunications workloads, financial trading systems, and high-performance computing on Kubernetes. Multus exists to solve exactly this problem.

Multus is a **meta-plugin** for the Container Network Interface (CNI). It does not replace your cluster's primary CNI — it wraps it. The primary CNI (Calico, Cilium, Flannel, or any other) continues to provide the default pod network on `eth0`. Multus adds the ability to attach additional network interfaces — `net1`, `net2`, `net3`, and beyond — by delegating to other CNI plugins such as macvlan, ipvlan, bridge, host-device, or SR-IOV. Each additional interface can live on a different physical network, use a different IPAM strategy, and deliver different performance characteristics. The result is a pod with multiple network identities, each serving a distinct purpose, all managed through standard Kubernetes APIs and operated by the same control plane.

By the end of this module, you will understand why the single-network model breaks down for specialized workloads, how Multus delegates to other CNI plugins to create multi-homed pods, how to define secondary networks with the NetworkAttachmentDefinition custom resource, and how to avoid the pitfalls that catch nearly every team on their first deployment. You will also see where Multus fits in the broader CNI ecosystem — what it does well, what it does not do, and when the complexity it introduces is justified.

---

## What You'll Learn

After completing this module, you will be able to:

- **Deploy Multus CNI to attach multiple network interfaces to Kubernetes pods**
- **Configure NetworkAttachmentDefinitions for SR-IOV, Macvlan, and IPVLAN secondary networks**
- **Implement Multus with Whereabouts IPAM for consistent IP address management across interfaces**
- **Evaluate multi-network pod architectures for NFV, telco, and data-intensive workload requirements**

## Prerequisites

Before starting this module, you should be comfortable with Kubernetes networking fundamentals — the pod networking model, Services, and the CNI plugin architecture. Experience with a specific CNI such as Cilium or Calico is helpful but not required. You will also need a working understanding of Linux networking: interfaces, VLANs, bridges, the routing table, and the `ip` command suite. Familiarity with container networking and Linux network namespaces will help you follow the architectural discussion, particularly the sections on how delegates create interfaces inside pod network namespaces.

---

## Why This Module Matters

Kubernetes networking is one of the most successful abstractions in modern infrastructure. Every pod gets an IP. Pods communicate without NAT. Services provide discovery and load balancing. NetworkPolicy enforces segmentation. For a web application — a set of stateless replicas behind a Service, speaking HTTP to each other and to a database — this abstraction is complete. You rarely need to think about what happens below the CNI layer.

But step outside the web-application pattern and the picture changes dramatically. A User Plane Function in a 5G core processes millions of subscriber data sessions per second. Each session carries real-time voice, video, or data traffic that must meet strict latency and throughput guarantees. The UPF needs a management interface for orchestration and health checks — standard Kubernetes networking works fine for that. It needs a signaling interface for control-plane protocols like PFCP — isolated from management traffic, because a control-plane delay could cause call drops across the entire network. And it needs a user data plane interface capable of line-rate packet forwarding at 25 or 100 Gbps, bypassing the Linux kernel network stack entirely, because every microsecond of added latency degrades call quality for millions of subscribers.

This is not a contrived example. Every major telecommunications provider deploying 5G on Kubernetes — and there are many — faces this exact multi-interface requirement. The 3GPP specifications that define 5G architecture mandate separation of the control plane (signaling) from the user plane (data), and in many deployments these planes must traverse physically distinct network infrastructure for compliance, performance, and security reasons. A single network interface shared by all traffic types cannot satisfy these requirements.

The same pattern appears in financial trading, where market data feeds demand dedicated, low-latency interfaces isolated from order-entry and management traffic. It appears in high-performance computing, where MPI jobs communicate over RDMA fabrics that bypass the kernel entirely. It appears in storage systems, where iSCSI or NVMe-oF traffic needs guaranteed bandwidth that cannot be starved by application I/O on the primary network. In every case, the answer is the same: the pod needs more than one network.

Multus provides this capability by acting as a CNI meta-plugin — a CNI that calls other CNIs. It does not replace your existing networking stack. It extends it. Your cluster continues to use Calico, Cilium, or Flannel as the default pod network. Multus adds additional interfaces by delegating to secondary CNI plugins — macvlan for L2-attached interfaces on specific VLANs, ipvlan for environments where MAC address limits apply, bridge for node-local L2 connectivity, SR-IOV for hardware-accelerated data planes, and host-device for passing physical interfaces directly into pods. Each secondary network is defined through a NetworkAttachmentDefinition CRD, and pods request them through a simple annotation.

This pattern — a meta-plugin that composes the work of other CNI plugins — is not a hack. It is a deliberate design that respects the CNI specification's support for plugin chaining. The CNI spec was written with the understanding that no single plugin could satisfy every networking requirement, and that operators would sometimes need to compose multiple plugins for a single pod. Multus is the most widely deployed implementation of that composition pattern. Understanding how it works, when to use it, and — critically — when the complexity it introduces is not justified, is essential knowledge for any platform engineer working with Kubernetes at scale.

---

## Part 1: The CNI Model and Where Multus Fits

Before diving into Multus itself, we need to understand the Container Network Interface (CNI) model that it extends. CNI is not a product or a single piece of software. It is a specification — maintained by the CNCF as an incubating project — that defines how container runtimes call network plugins to configure container networking. The specification is deliberately minimal. It defines only the interface: an executable binary that the container runtime calls with a JSON configuration on standard input, and that returns a JSON result on standard output. That is the entire contract.

### How a CNI Plugin Configures a Pod's Network

When the kubelet creates a pod, it calls the configured CNI plugin with an `ADD` command. The plugin receives the pod's network namespace path, the container ID, and its own configuration (read from a file in `/etc/cni/net.d/`). The plugin is responsible for creating a network interface inside the pod's network namespace, assigning it an IP address (either from its own IPAM logic or by calling a separate IPAM plugin), setting up routes, and returning the result to the kubelet. When the pod is deleted, the kubelet calls the plugin again with a `DEL` command, and the plugin tears down the interface and releases the IP.

This model has several important properties. First, the plugin is a standalone binary — it runs as a child process of the kubelet, not as a daemon. Second, the plugin is stateless from the kubelet's perspective: each `ADD` call must produce a valid network configuration based only on the input JSON. Third, the plugin is responsible for IP address management (IPAM), either directly or by delegating to a separate IPAM binary. These properties make CNI plugins simple, composable, and easy to reason about — but they also create challenges for multi-network scenarios, which we will explore shortly.

### The Kubernetes Networking Model and Its Single-Interface Assumption

The Kubernetes networking model, defined separately from CNI, imposes three requirements: every pod gets its own IP address, pods on a node can communicate with all pods on all nodes without NAT, and agents on a node (such as the kubelet) can communicate with all pods on that node. These requirements are satisfied by having a CNI plugin that creates a flat, routable pod network — an overlay network using VXLAN or IP-in-IP encapsulation, a routed network using BGP or host routes, or a simple bridge network in small clusters.

The important thing to notice is that the Kubernetes model says nothing about how many interfaces a pod may have. The single-interface assumption is a consequence of how the kubelet invokes CNI: it calls one plugin, once, for each pod. That plugin creates one interface — typically `eth0` — and returns. The pod is on the network. This is entirely adequate for the web-application use case that Kubernetes was originally designed to serve. But the CNI specification, to its credit, anticipated that this would not always be enough. The spec supports calling multiple plugins in sequence for the same pod, with each plugin receiving the result of the previous one. This is the plugin-chaining mechanism that Multus exploits.

### How Plugin Chaining Enables Multi-Homed Pods

In the standard CNI flow, the kubelet calls a single CNI plugin and the pod gets one interface. With plugin chaining, the kubelet calls a chain of plugins — or, more commonly, it calls a single meta-plugin that internally calls a chain of plugins. The meta-plugin acts as the single CNI that the kubelet knows about. To the kubelet, nothing has changed: it calls one binary, receives one result, and the pod is networked. But inside that one binary, multiple CNI plugins have been invoked, each creating a separate interface in the pod's network namespace.

Multus implements this pattern as a production-grade meta-plugin. It reads its own configuration from `/etc/cni/net.d/`, which specifies the default network delegate (the cluster's primary CNI) and any additional delegates for secondary networks. When the kubelet calls Multus for a pod, Multus first calls the default delegate to create `eth0`. Then it reads the pod's annotations to discover any additional networks the pod has requested. For each requested network, Multus looks up the corresponding NetworkAttachmentDefinition — a Kubernetes CRD that wraps a CNI plugin configuration — and calls the specified delegate plugin. Each delegate creates one additional interface (`net1`, `net2`, etc.) in the pod's network namespace. Multus collects all the results, merges them, and returns the combined network status to the kubelet.

This delegation model is the key architectural insight behind Multus. Multus does not know how to create a macvlan interface. It does not know how to assign an SR-IOV virtual function to a pod. It does not know how to configure a Linux bridge. It delegates all of that work to plugins that do know — the standard macvlan, ipvlan, bridge, host-device, and SR-IOV CNI plugins. Multus is purely an orchestrator. It sequences the calls, resolves the configurations, handles errors, and merges the results. The actual network plumbing is performed by the delegate plugins, each of which is a standalone CNI plugin that can be tested, updated, and reasoned about independently.

This separation of concerns — Multus as orchestrator, delegate plugins as workers — is what makes the architecture robust. You can add a new type of secondary network by writing or installing a CNI plugin that understands it, without touching Multus at all. You can upgrade your primary CNI independently of your secondary network configuration. And you can debug a secondary network problem by isolating the specific delegate plugin that is failing, using the same CNI debugging techniques you would use for a single-network pod.

---

## Part 2: The Multi-Network Architecture

### The Decision to Go Multi-Homed

Adding a second network interface to a pod is not a decision to take lightly. Each additional interface adds complexity to the pod's routing table, to your debugging workflow, to your security model, and to your operational procedures. Before reaching for Multus, exhaust the alternatives. If your goal is traffic isolation, Kubernetes NetworkPolicy — enforced by a CNI like Calico or Cilium — can segment traffic without adding interfaces. If your goal is performance, consider whether tuning your primary CNI (adjusting MTU, switching from VXLAN to BGP routing, or moving to an eBPF-based data plane like Cilium's) can get you close enough to your target without the complexity of multi-homing. Multus is the right answer when no amount of tuning the default network will satisfy your requirements — typically because you need physically separate network paths, hardware-accelerated interfaces, or compliance-mandated network segregation at Layer 2.

### The Four Canonical Use Cases

**Traffic separation by concern.** Different traffic types have fundamentally different requirements, and sharing a single network interface forces all traffic to compete for the same link. Management traffic (health checks, metrics scraping, log shipping) is bursty and latency-tolerant. Signaling traffic (control-plane protocols like SCTP in 5G or FIX in financial trading) demands low latency and high reliability. User data traffic (voice, video, market data) demands high throughput with predictable latency. Storage traffic (iSCSI, NFS, NVMe-oF) demands consistent bandwidth and cannot tolerate congestion from application I/O. A single interface shared by all four traffic types means that a log-shipping burst can delay a signaling message, or a storage backup can starve user data. Multiple interfaces eliminate this contention by giving each traffic class its own link.

**Hardware-accelerated performance.** The Linux kernel network stack is general-purpose and well-optimized, but it imposes a per-packet processing cost that becomes a bottleneck at high packet rates. For line-rate packet processing at 25, 40, or 100 Gbps, you need to bypass the kernel entirely. SR-IOV (Single Root I/O Virtualization) makes this possible by creating Virtual Functions (VFs) on the physical NIC — lightweight PCIe functions that can be assigned directly to a pod's network namespace. The pod's application talks to the NIC hardware directly through a userspace driver like DPDK, without the kernel ever touching the packets. This delivers throughput at line rate and latency measured in microseconds, not tens of microseconds. The cost is that you lose all kernel networking features on that interface — no iptables, no connection tracking, no NetworkPolicy enforcement. You are trading features for performance, and that tradeoff only makes sense on the high-performance data plane, not on the management interface.

**Regulatory and compliance isolation.** Some industry regulations mandate physical network separation at Layer 2. PCI DSS requires that cardholder data traverse dedicated network segments. HIPAA requires isolation of networks carrying protected health information. 3GPP specifications for telecommunications mandate separation of signaling and user data planes. MiFID II in financial services requires dedicated networks for audit trails. You cannot satisfy "this traffic must stay on VLAN 100 connected to physical switch port Gi0/24" with an overlay network — you need a direct connection to the physical infrastructure. Multus, combined with a macvlan or SR-IOV delegate, gives pods that direct connection.

**Legacy infrastructure integration.** Kubernetes rarely exists in a vacuum. Production environments include bare-metal database servers on specific VLANs, network appliances (firewalls, load balancers, intrusion detection systems) expecting traffic on particular subnets, monitoring infrastructure that taps specific physical segments, and non-Kubernetes workloads that pods must communicate with on existing networks. Multus lets pods join these existing networks on their own terms, without requiring a re-architecture of the entire infrastructure to fit Kubernetes' single-network model. A pod can have one interface on the Kubernetes overlay for cluster-internal communication, and another interface on a corporate VLAN for reaching legacy services.

### What Multus Does Not Do

Understanding Multus' limitations is as important as understanding its capabilities. Multus does not provide any network connectivity itself — it delegates everything. If you deploy Multus without a default CNI plugin, your pods will have no network at all. If you define a NetworkAttachmentDefinition that references a CNI plugin you have not installed, pod creation will fail with a CNI error. If you expect Kubernetes Services to work on secondary networks, you will be disappointed — Services operate exclusively on the default `eth0` network, and there is no built-in mechanism for service discovery or load balancing on secondary interfaces. Multus does not enforce NetworkPolicy on secondary networks — that responsibility falls to the delegate plugin (if it supports policy) or to external network controls. And Multus does not provide DNS for secondary networks — pod-to-pod communication on a secondary interface requires IP-level addressing, static IP reservations with Whereabouts, or custom service discovery built by your application.

---

## Part 3: NetworkAttachmentDefinition — The Interface Contract

The NetworkAttachmentDefinition (often shortened to `net-attach-def`) is a Kubernetes Custom Resource Definition that tells Multus about a secondary network. It is the primary API surface you interact with when configuring Multus. A NetworkAttachmentDefinition wraps a standard CNI plugin configuration in a Kubernetes resource, associating it with a name and a namespace. Pods reference it by name through an annotation.

The design of NetworkAttachmentDefinition is itself a standard — the Kubernetes Network Custom Resource Definition De-facto Standard — proposed and maintained by the Network Plumbing Working Group (NPWG). The NPWG is the community group behind Multus, the SR-IOV device plugin, Whereabouts IPAM, and several other multi-network projects. The `net-attach-def` format has become the de-facto standard for defining secondary networks in Kubernetes, adopted by projects beyond the NPWG ecosystem.

### Macvlan — The Workhorse Secondary Network

Macvlan creates virtual interfaces that each have their own MAC address and share a physical parent interface. Each macvlan sub-interface appears to the external network as a separate device on the same L2 segment. This is the most common secondary network type because it maps cleanly to existing VLAN-based network architectures.

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "macvlan",
    "master": "eth0",
    "mode": "bridge",
    "ipam": {
      "type": "whereabouts",
      "range": "172.16.1.0/24",
      "range_start": "172.16.1.100",
      "range_end": "172.16.1.200"
    }
  }'
```

The `master` field specifies the physical interface on the node that the macvlan sub-interfaces attach to. This is an important point: the master interface must exist on every node where pods using this network might be scheduled. If a pod lands on a node that lacks the named master interface, pod creation will fail. The `mode` field controls how macvlan sub-interfaces communicate with each other and with the external network. The `bridge` mode — the most common — allows sub-interfaces on the same parent to communicate directly through a virtual switch in the kernel, and also allows them to reach external hosts through the physical interface. The `vepa` mode (Virtual Ethernet Port Aggregator) forces all traffic, even between sub-interfaces on the same parent, to go through an external switch — useful when you want switch-level policy enforcement on inter-pod traffic. The `private` mode prevents sub-interfaces on the same parent from communicating with each other entirely, providing maximum isolation. The `passthru` mode dedicates the entire parent interface to a single sub-interface — a single-tenant, high-performance configuration.

A critical limitation of macvlan: **the host cannot communicate directly with its own macvlan sub-interfaces**. This is a deliberate kernel design choice, not a bug. Traffic from the host's physical interface to a macvlan sub-interface on the same parent is blocked at the kernel level. If your node needs to communicate with pods on the macvlan network — for health checks, metrics scraping, or any other reason — you must route that traffic through an external switch, or use a different network type (such as a bridge). This catches every team on their first Multus deployment. Plan for it.

### IPvlan — Shared MAC, Different IPs

IPvlan is similar to macvlan in that it creates virtual interfaces on a parent, but with one key difference: all IPvlan sub-interfaces share the parent's MAC address. This matters in environments that restrict the number of MAC addresses per switch port — common in cloud environments (AWS, some OpenStack configurations) and in data centers with port-security enabled on access switches.

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: ipvlan-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "ipvlan",
    "master": "eth0",
    "mode": "l2",
    "ipam": {
      "type": "whereabouts",
      "range": "10.10.1.0/24",
      "range_start": "10.10.1.100",
      "range_end": "10.10.1.200"
    }
  }'
```

IPvlan supports three modes. `l2` mode operates at Layer 2: all sub-interfaces share the parent's MAC, and traffic is switched based on IP addresses. Broadcast and multicast traffic is delivered to all sub-interfaces. `l3` mode operates at Layer 3: the parent interface acts as a router, and traffic between subnets is routed. There is no broadcast or multicast in L3 mode — useful when you want to prevent broadcast storms in large deployments. `l3s` mode extends L3 mode with iptables and connection tracking support, enabling features like NAT and stateful firewalling on IPvlan interfaces.

Choose IPvlan over macvlan when your switch infrastructure limits MAC addresses per port (cloud environments), when you need more than roughly 512 virtual interfaces on a single parent (macvlan creates a unique MAC per interface, which can overflow switch MAC tables), or when you want L3 routing between subnets without L2 broadcast traffic. Choose macvlan when you need each sub-interface to appear as a distinct device with its own MAC address — for example, when your network monitoring tools track devices by MAC, or when you are integrating with DHCP servers that assign leases by MAC.

### Bridge — Node-Local L2 Connectivity

The bridge plugin creates a Linux bridge on the node and attaches pod interfaces to it. Pods on the same node connected to the same bridge can communicate at Layer 2. By default, the bridge network is node-local — pods on different nodes cannot reach each other over the bridge without additional configuration (VXLAN tunneling, or connecting the bridge to a physical interface).

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: bridge-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "bridge",
    "bridge": "mybridge0",
    "isGateway": true,
    "ipMasq": true,
    "ipam": {
      "type": "whereabouts",
      "range": "10.20.0.0/24"
    }
  }'
```

The bridge plugin is most useful for development and testing environments where you want a simple, isolated secondary network without physical infrastructure dependencies. It is also useful for connecting pods to node-local resources — a sidecar that needs to communicate with the main container over a dedicated, non-routable link, for example. In production, bridge networks are typically replaced by macvlan or SR-IOV configurations that provide multi-node connectivity through physical infrastructure.

### SR-IOV — Bypassing the Kernel for Line-Rate Performance

SR-IOV creates Virtual Functions (VFs) on a physical NIC and passes them directly into pod network namespaces. The pod's application communicates with the NIC hardware directly, without the kernel network stack touching the packets. This delivers line-rate throughput (25, 40, 100 Gbps) with predictable, single-digit microsecond latency. The tradeoff is that kernel networking features — iptables, connection tracking, NetworkPolicy — are not available on SR-IOV interfaces. You are trading the entire kernel networking stack for raw hardware performance.

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: sriov-net
  namespace: default
  annotations:
    k8s.v1.cni.cncf.io/resourceName: intel.com/sriov_netdevice
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "sriov",
    "vlan": 1000,
    "ipam": {
      "type": "whereabouts",
      "range": "192.168.100.0/24"
    }
  }'
```

SR-IOV requires additional components beyond Multus and the base CNI plugins: the **SR-IOV Network Device Plugin**, which discovers SR-IOV-capable NICs on each node and advertises their Virtual Functions as extended Kubernetes resources; the **SR-IOV CNI Plugin**, which moves VFs into pod network namespaces and configures them; and a **compatible NIC** with SR-IOV support (Intel X710/XXV710/E810 series, Mellanox ConnectX-4/5/6/7, Broadcom BCM57xx). Pods request VFs through Kubernetes resource requests and limits, specifying the resource name that the device plugin advertises. The scheduler ensures that pods land on nodes with available VFs, and Multus delegates to the SR-IOV CNI plugin to move the allocated VF into the pod's network namespace.

The typical SR-IOV deployment pattern is to use it only for the high-performance data plane. The pod's management interface (`eth0`) remains on the standard Kubernetes overlay network, handled by the default CNI. The SR-IOV interface carries only the performance-critical traffic — user data in a 5G UPF, market data in a trading system, MPI messages in an HPC job. This pattern gives you the best of both worlds: standard Kubernetes networking for orchestration and manageability, and hardware-accelerated networking for the data path that demands it.

---

## Part 4: Whereabouts IPAM — Solving Cluster-Wide IP Coordination

When you have a single pod network, IP address management is straightforward. Your CNI plugin's IPAM component assigns addresses from a cluster-wide pool, and it has full visibility into which addresses are in use. When you add secondary networks through Multus, IPAM becomes more complicated. Each secondary network has its own IP address space, and the delegate plugin's IPAM component needs to assign addresses consistently across all nodes.

The default `host-local` IPAM plugin, which ships with most CNI distributions, manages IP allocations per node. Each node maintains a local database of assigned IPs. This works correctly when every node has a distinct IP range — but secondary networks often share a single subnet across all nodes. If Node 1 assigns `172.16.1.10` to Pod A from a shared `/24` range, and Node 2 independently assigns `172.16.1.10` to Pod B from the same range, you have an IP conflict. Two pods on different nodes believe they own the same IP address. Traffic to that IP becomes unpredictable — sometimes reaching Pod A, sometimes Pod B, sometimes neither.

**Whereabouts** solves this by storing IP allocations as Kubernetes Custom Resources, giving every node in the cluster a shared view of the allocation state. Before assigning an IP, a node checks the Whereabouts CR for that network to see which IPs are already taken. If the desired IP is free, Whereabouts writes a new allocation record. If it is taken, Whereabouts tries the next IP. This optimistic-locking approach — read the current state, write a new allocation, retry on conflict — works without a separate coordination service or database. IP allocations are Kubernetes-native objects that can be inspected, backed up, and garbage-collected with standard Kubernetes tooling.

Whereabouts supports range-based allocation (define a start and end of the pool within a subnet), IP exclusions (reserve specific IPs for gateways or existing hosts), overlapping ranges across different NetworkAttachmentDefinitions with different namespaces, and automatic garbage collection of IPs from deleted pods via a cron job. It is the recommended IPAM plugin for secondary networks in production Multus deployments, and it integrates transparently — you specify `"type": "whereabouts"` in the IPAM section of your NetworkAttachmentDefinition instead of `"type": "host-local"`, and the rest of the configuration is identical.

---

## Part 5: Pod Annotations — Requesting Additional Networks

Pods request secondary networks through the `k8s.v1.cni.cncf.io/networks` annotation. The annotation value is a comma-separated list of NetworkAttachmentDefinition names, or a JSON array for more advanced control.

The simplest form requests one additional network:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-net-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: app
    image: alpine
    command: ["sleep", "infinity"]
```

This pod will have two interfaces: `eth0` from the default CNI, and `net1` from the macvlan NetworkAttachmentDefinition. Additional networks are numbered sequentially — a pod requesting `macvlan-conf, bridge-conf` would get `eth0`, `net1`, and `net2`.

The JSON format gives you fine-grained control over interface names, specific IP addresses, and namespace-qualified network references:

```yaml
annotations:
  k8s.v1.cni.cncf.io/networks: '[
    {
      "name": "macvlan-conf",
      "namespace": "default",
      "interface": "mgmt1",
      "ips": ["172.16.1.50"]
    },
    {
      "name": "sriov-net",
      "namespace": "default",
      "interface": "data0"
    }
  ]'
```

The `interface` field lets you name the secondary interface something meaningful — `mgmt1`, `data0`, `storage` — instead of the default `net1`, `net2` scheme. The `ips` field requests a specific IP address, which must fall within the NetworkAttachmentDefinition's configured IPAM range and must not already be allocated to another pod. The `namespace` field references a NetworkAttachmentDefinition in a namespace other than the pod's own — network definitions in the `kube-system` namespace, for example, are accessible to pods in any namespace.

After the pod starts, Multus writes the network configuration result back to the pod as the `k8s.v1.cni.cncf.io/network-status` annotation. This annotation contains a JSON array describing every interface attached to the pod — its name, IP addresses, MAC address, DNS configuration, and which network definition it came from. Use this annotation to verify that all requested networks were attached correctly, and to discover the assigned IPs.

---

## Landscape Snapshot

> **Landscape snapshot — as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**

Multus is maintained by the **Kubernetes Network Plumbing Working Group (NPWG)**, a community group hosted under the `k8snetworkplumbingwg` GitHub organization. As of June 2026, the latest release is **v4.3.0**, which introduced the thick plugin architecture (a DaemonSet-based deployment model with a shim binary on each node that communicates with a local Multus daemon). The project has approximately 2,900 GitHub stars and 42 repositories under the NPWG organization, including companion projects: Whereabouts (cluster-wide IPAM), the SR-IOV Network Device Plugin, the SR-IOV CNI Plugin, the OVS CNI Plugin, and the RDMA CNI Plugin. Multus is present on the CNCF Landscape under the Cloud Native Network category but is not a formally accepted CNCF project (Sandbox, Incubating, or Graduated). The NetworkAttachmentDefinition CRD format is a de-facto standard — not an official Kubernetes API — proposed by the NPWG and adopted by multiple multi-network projects. Governance is community-driven through the NPWG, with significant contributions from Intel (the original creator), Red Hat, and individual maintainers.

---

## Cross-CNI Rosetta

Where does Multus sit relative to the CNI plugins you already know? This table compares common CNIs across durable capabilities. Multus is a meta-plugin — it does not compete with Flannel, Calico, or Cilium. It works alongside them.

| Capability | Multus | Flannel | Calico | Cilium |
|---|---|---|---|---|
| **Role** | Meta-plugin (calls other CNIs) | Pod network (overlay) | Pod network + policy | Pod network + policy + observability |
| **Connectivity model** | Delegates to default + secondary CNIs | VXLAN or host-gw overlay | IP-in-IP, VXLAN, or BGP routing | eBPF-based routing or VXLAN/Geneve overlay |
| **Encapsulation** | None (delegates) | VXLAN (default) or host-gw (no encap) | IP-in-IP (default), VXLAN, or none (BGP) | VXLAN or Geneve (overlay mode); none (native routing) |
| **NetworkPolicy support** | Only on default network (via delegate) | No native support | Full Kubernetes NetworkPolicy + Calico global policies | Full Kubernetes NetworkPolicy + CiliumNetworkPolicy (L7) |
| **Service handling** | Only on default network | kube-proxy (iptables/IPVS) | kube-proxy or eBPF-based replacement | eBPF-based (replaces kube-proxy entirely) |
| **IPAM** | Per-network (delegates to each delegate's IPAM) | host-local (per-node ranges) | Calico IPAM (cluster-wide, block-based) | ClusterPool or Kubernetes-hosted IPAM |
| **Multi-NIC** | Core capability — its reason for existing | None | None (single-interface only) | None (single-interface only) |
| **Typical use case** | Telco, HPC, finance — workloads needing multiple physical network paths | Simple clusters prioritizing ease of setup | Enterprise policy-driven networking at scale | Zero-trust networking with deep observability and L7 policy |
| **Maturity / governance** | NPWG community project, v4.3.0 (2026) | CNCF Graduated, widely deployed | CNCF Graduated, enterprise adoption | CNCF Graduated, eBPF-based, rapidly growing |

This comparison makes clear that Multus is not a replacement for any of the other CNIs. It is a layer above them. You cannot run Multus without a default CNI — it would have nothing to delegate the `eth0` creation to. In practice, a Multus deployment typically combines Multus (as the kubelet's CNI) with Calico or Cilium (as the default network delegate) and macvlan/SR-IOV (as secondary network delegates). Multus orchestrates; the delegates do the actual network configuration.

---

## Did You Know?

- **Multus means "many" in Latin.** The name reflects the project's core purpose: giving a pod many network interfaces instead of the standard single interface. The project was originally created by Intel engineers working on telecommunications workloads — the canonical 5G network function use case drove the initial design.
- **The "thin" vs "thick" plugin distinction in Multus is about where the logic lives.** In thin mode (the original design, pre-v4.0), the entire Multus logic runs as a CNI binary invoked by the kubelet. Each pod creation spawns a Multus process. In thick mode (the default since v4.0), a lightweight shim binary runs on each node, and the heavy lifting is done by a long-running Multus daemon deployed as a DaemonSet. Thick mode supports features like Prometheus metrics and makes upgrades easier — you update the DaemonSet instead of replacing binaries on every node — at the cost of slightly higher resource consumption.
- **Macvlan's host-to-subinterface communication restriction is a kernel design decision, not a bug.** The Linux kernel explicitly prevents the parent interface from communicating with its own macvlan sub-interfaces. This is by design: macvlan creates virtual interfaces that appear as separate devices on the wire, and the kernel enforces this separation at the software level. If you need host-to-pod communication on a secondary network, use a bridge instead of macvlan, or add a second physical interface on the host connected to the same VLAN.
- **Whereabouts uses optimistic locking, not a distributed lock manager.** When two pods on different nodes request IPs simultaneously, both nodes may read the same allocation state, both may decide the same IP is free, and both may try to write an allocation for the same IP. The Kubernetes API server serializes writes — one will succeed and the other will get a conflict error. The failing node retries with the next available IP. This "read, try, retry-on-conflict" approach works without a separate coordination service, relying on the Kubernetes API's consistency guarantees instead.

---

## Common Mistakes

| Mistake | What Happens | Solution |
|---|---|---|
| Assuming Kubernetes Services work on secondary networks | A Service selects pods, but traffic only routes to `eth0` IPs. Secondary interface IPs are invisible to kube-proxy and CoreDNS. | Use application-level service discovery, external load balancers, or static IP reservations for secondary-network communication. |
| Using `host-local` IPAM across multiple nodes on the same subnet | Different nodes independently assign the same IP to different pods, causing silent IP conflicts and unreachable pods. | Use Whereabouts for cluster-wide IP coordination on secondary networks. |
| Specifying the wrong `master` interface in macvlan/ipvlan configs | Pod creation fails with "master field is not valid" or the interface attaches to the wrong NIC. Interface names vary by Linux distribution and hardware. | Run `ip link show` on every node to verify interface names. Use node labels and node-selectors if interface names differ across hardware. |
| Expecting the node to reach pods on macvlan interfaces | Health checks or metrics scraping from the node to macvlan pods fail. Traffic from the host to its own macvlan sub-interfaces is blocked by the kernel. | Use a bridge network for host-to-pod traffic, or route through an external switch. Plan for this limitation before deploying. |
| Putting NetworkAttachmentDefinition in a different namespace than the pod without qualifying it | Pod creation fails with "cannot find network `macvlan-conf`" because the annotation references a network not visible in the pod's namespace. | Create NetworkAttachmentDefinitions in the same namespace as the pods, or use JSON annotation format with an explicit `"namespace"` field. |
| Not requesting SR-IOV resources in the pod spec | The pod is scheduled normally, but no VF is allocated. The SR-IOV CNI plugin has nothing to attach. | Add `resources.requests` and `resources.limits` for the SR-IOV resource name (e.g., `intel.com/sriov_netdevice`) in every pod that uses an SR-IOV network. |
| Ignoring routing table configuration in multi-interface pods | Traffic destined for subnet A leaves via the wrong interface, or response packets take a different path than request packets (asymmetric routing), breaking TCP connections. | Inspect the routing table with `ip route show` inside the pod. Use the `default-route` annotation option or configure policy-based routing if the pod needs non-default routing behavior. |
| Deleting or misconfiguring the default CNI while Multus is installed | Multus always calls the default delegate first to create `eth0`. If this delegate breaks, every pod in the cluster — not just multi-network ones — fails to get networking. | Treat your default CNI with the same care as before Multus. Multus depends on it for the primary pod network. Monitor the default CNI's health independently. |

---

## Quiz

Test your understanding of Multus and multi-network pods.

**Question 1**: Multus is described as a "meta-plugin." What does this mean in terms of what Multus does and does not do?

<details>
<summary>Show Answer</summary>

A meta-plugin is a CNI plugin that does not configure networks itself. Instead, it calls other CNI plugins (delegates) and orchestrates their execution. Multus receives the CNI invocation from the kubelet, calls the default network delegate to create `eth0`, then reads the pod's annotations to discover additional networks, looks up the corresponding NetworkAttachmentDefinitions, and calls the specified delegate plugins for each one. Multus itself does not create interfaces, assign IPs, or configure routes — it delegates all of that to the plugins it calls. This is the key architectural property: Multus is purely an orchestrator. You must have the delegate plugins installed separately (your default CNI for `eth0`, and whichever secondary plugins — macvlan, ipvlan, bridge, SR-IOV — you configure in your NetworkAttachmentDefinitions).
</details>

**Question 2**: A pod has the annotation `k8s.v1.cni.cncf.io/networks: macvlan-conf, bridge-conf`. How many network interfaces will the pod have, and how are they named by default?

<details>
<summary>Show Answer</summary>

The pod will have **three** interfaces by default: `eth0` (always present, created by the cluster's default CNI delegate), `net1` (the macvlan interface from `macvlan-conf`), and `net2` (the bridge interface from `bridge-conf`). Secondary networks are numbered sequentially starting from `net1`. Custom interface names can be specified using the JSON annotation format with an `"interface"` field — for example, naming the macvlan interface `mgmt1` and the bridge interface `data0` instead of the default `net1` and `net2`.
</details>

**Question 3**: Why can a Linux host (the node) not communicate directly with a pod's macvlan interface, and what alternatives exist if host-to-pod communication on the secondary network is required?

<details>
<summary>Show Answer</summary>

This is a deliberate kernel-level restriction, not a bug. The Linux kernel explicitly prevents the macvlan parent interface from communicating with its child sub-interfaces. Traffic from the host's physical interface to a macvlan sub-interface on the same parent is blocked in the kernel. This is by design — macvlan creates virtual interfaces that appear as separate devices on the wire, and the kernel enforces this separation at the software level. Alternatives: (1) Route traffic through an external switch — the host sends traffic out the physical port, the switch sends it back, and it arrives at the macvlan sub-interface. (2) Use a bridge network instead of macvlan — the bridge plugin does not have this restriction and allows host-to-pod communication on the secondary bridge. (3) Add a second physical interface on the host connected to the same VLAN, and use that interface for host-to-pod traffic. The best approach depends on your topology: if an external switch is between the host and the macvlan network, option 1 works naturally. If the host needs direct access (for health checks or metrics scraping), option 2 or 3 is better.
</details>

**Question 4**: What problem does Whereabouts solve that the built-in `host-local` IPAM cannot, and how does it solve it without a separate coordination service?

<details>
<summary>Show Answer</summary>

The `host-local` IPAM plugin manages IP allocations independently per node. Each node has its own local database of assigned IPs and its own view of the subnet. When multiple nodes share the same IP range for a secondary network, two nodes can independently assign the same IP to different pods, creating an IP conflict — two pods on different nodes both believe they own `172.16.1.10`. Packets to that IP may reach either pod unpredictably. Whereabouts solves this by storing IP allocations as Kubernetes Custom Resources, giving every node a shared, cluster-wide view of the allocation state. Before assigning an IP, a node reads the Whereabouts CR to see which IPs are taken. If the desired IP is free, it writes a new allocation record. If two nodes try to allocate the same IP simultaneously, the Kubernetes API server serializes their writes — one succeeds, the other gets a conflict error and retries with the next available IP. This optimistic-locking approach relies on Kubernetes' built-in consistency guarantees rather than an external coordination service or distributed lock manager.
</details>

**Question 5**: You create a Kubernetes Service that selects pods running a 5G User Plane Function (UPF). The UPF processes user data traffic on its SR-IOV interface (`net2` at 25 Gbps). Will the Service route user-plane traffic to the SR-IOV interface?

<details>
<summary>Show Answer</summary>

No. Kubernetes Services operate exclusively on the default pod network (`eth0`). A Service's Endpoints object lists only the pod's primary IP address — the one assigned by the default CNI. kube-proxy (or its eBPF replacement) programs forwarding rules only for that primary IP. The SR-IOV interface's IP address is completely invisible to the Service abstraction. If you expose a ClusterIP or NodePort Service targeting these UPF pods, traffic will arrive on `eth0`, not on the SR-IOV data plane. This is a critical architectural constraint when evaluating multi-network pod designs for NFV and telco workloads: you must plan for data-plane routing outside Kubernetes. For example, a 5G Session Management Function (SMF) would be configured to instruct gNBs (base stations) to send user-plane traffic directly to the UPF pod's SR-IOV IP address, bypassing the Kubernetes Service layer entirely. This is standard practice in 5G deployments: Kubernetes Services manage the control plane, while data-plane routing is handled by the telecommunications application logic.
</details>

**Question 6**: When would you choose IPvlan over Macvlan for a secondary network, and what tradeoffs does this choice involve?

<details>
<summary>Show Answer</summary>

Choose IPvlan over Macvlan when: (1) Your environment restricts the number of MAC addresses per switch port — common in cloud environments (AWS, GCP) and data centers with port-security enabled. IPvlan shares the parent interface's single MAC address across all sub-interfaces, so you never exceed MAC limits. (2) You need more than roughly 512 virtual interfaces on a single parent — Macvlan creates a unique MAC per sub-interface, which can overflow switch MAC address tables at scale. IPvlan scales to thousands of sub-interfaces without adding MAC table entries. (3) You want L3 routing mode — IPvlan's L3 mode provides routing between subnets without L2 broadcast traffic, which eliminates broadcast storms in large deployments. The tradeoff is that IPvlan sub-interfaces share a MAC address, so they are not distinguishable by MAC on the wire. If your network monitoring, DHCP server, or security tools rely on per-device MAC addresses, Macvlan is the better choice. If your infrastructure does not care about MAC diversity and you value simplicity at scale, IPvlan wins.
</details>

**Question 7**: You install Multus and configure a NetworkAttachmentDefinition for a macvlan secondary network. Pods that request the secondary network successfully get both `eth0` and `net1`. Then someone runs `kubectl delete` on the default CNI DaemonSet by mistake. What happens to pods — both those with secondary networks and those without?

<details>
<summary>Show Answer</summary>

Everything breaks. Multus always calls the default network delegate first to create `eth0`. If the default CNI is unavailable — its binaries deleted, its daemon stopped, its configuration corrupted — the default delegate call fails. Multus cannot proceed. Even pods that do not request any secondary networks still rely on Multus to call the default delegate for `eth0`. New pods will fail to start with a CNI error. Existing pods will continue running with their existing interfaces, but any pod restart or rescheduling will fail. The secondary networks are irrelevant to this failure mode — the default network is the critical dependency. This is why you should monitor your default CNI's health independently of Multus, and why removing or replacing the default CNI requires a coordinated migration (typically involving tainting nodes, draining pods, and reinstalling) rather than a simple DaemonSet deletion.
</details>

**Question 8**: A pod has three interfaces: `eth0` (management, 10.244.1.5), `net1` (signaling, 172.16.1.10), and `net2` (user data, 192.168.100.5). The pod's routing table shows the default route via `eth0`. Traffic to 172.16.1.50 is correctly routed via `net1`. What happens when the pod sends traffic to 8.8.8.8, and why is this routing behavior important?

<details>
<summary>Show Answer</summary>

Traffic to 8.8.8.8 (or any destination not covered by a more specific route) follows the default route via `eth0` — the management interface. This is the correct and intended behavior. The default route should always go through the default network (`eth0`) because that is the interface with full network reachability — Internet access, cluster DNS, the Kubernetes API server. Secondary interfaces typically have limited routing scope: `net1` might only reach the 172.16.1.0/24 signaling VLAN, and `net2` might only reach the 192.168.100.0/24 data plane. If the default route were accidentally set through a secondary interface with limited scope, the pod would lose access to the Kubernetes API, DNS, and the Internet. Multus sets the default route through `eth0` by design. You can override this with the `default-route` annotation option if a secondary interface truly should be the default gateway, but this is unusual and should only be done when you understand the full routing implications.
</details>

---

## Hands-On Exercise: Multus with Macvlan on kind

### What You'll Build

A kind cluster with Multus installed, where pods get both a primary network (via kindnet, kind's default CNI) and a secondary Macvlan network. You will deploy pods with and without the secondary network, verify interface counts, test connectivity on both networks independently, and confirm that pods without the secondary network cannot reach it.

### Part 1: Create a kind Cluster

```bash
# Create a kind cluster with one control-plane and two workers
cat <<'EOF' | kind create cluster --name multus-lab --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

# Verify all nodes are ready
kubectl get nodes
```

### Part 2: Install Multus

```bash
# Install Multus using the thick plugin DaemonSet
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset-thick.yml

# Wait for Multus pods to be ready on all nodes
kubectl rollout status daemonset/kube-multus-ds -n kube-system --timeout=120s

# Confirm Multus pods are running
kubectl get pods -n kube-system -l app=multus
```

### Part 3: Create a NetworkAttachmentDefinition

```bash
# Create a Macvlan NetworkAttachmentDefinition
kubectl apply -f - <<'EOF'
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "macvlan",
    "master": "eth0",
    "mode": "bridge",
    "ipam": {
      "type": "host-local",
      "subnet": "172.16.1.0/24",
      "rangeStart": "172.16.1.100",
      "rangeEnd": "172.16.1.200"
    }
  }'
EOF

# Verify the NetworkAttachmentDefinition was created
kubectl get net-attach-def
```

> **Note**: We use `host-local` IPAM here for simplicity. In production, install Whereabouts and use `"type": "whereabouts"` to avoid IP conflicts across nodes. For this single-node-subnet lab exercise, host-local works because the range is large enough to avoid collisions.

### Part 4: Deploy Pods with Multiple Networks

```bash
# Create Pod A (with secondary network)
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-a
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: toolbox
    image: nicolaka/netshoot
    command: ["sleep", "infinity"]
EOF

# Create Pod B (with secondary network)
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-b
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: toolbox
    image: nicolaka/netshoot
    command: ["sleep", "infinity"]
EOF

# Create Pod C (without secondary network — control)
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-c
spec:
  containers:
  - name: toolbox
    image: nicolaka/netshoot
    command: ["sleep", "infinity"]
EOF

# Wait for all pods to be ready
kubectl wait --for=condition=Ready pod/pod-a pod/pod-b pod/pod-c --timeout=120s
```

### Part 5: Verify Multi-Network Connectivity

```bash
# Check interfaces on all pods
echo "=== Pod A interfaces (should have eth0 AND net1) ==="
kubectl exec pod-a -- ip addr show

echo "=== Pod B interfaces (should have eth0 AND net1) ==="
kubectl exec pod-b -- ip addr show

echo "=== Pod C interfaces (should have ONLY eth0) ==="
kubectl exec pod-c -- ip addr show

# Inspect the network status annotation
echo "=== Pod A network status ==="
kubectl get pod pod-a -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/network-status}'
```

```bash
# Test connectivity on the secondary network
POD_B_SECONDARY_IP=$(kubectl exec pod-b -- ip -4 addr show net1 | grep inet | awk '{print $2}' | cut -d/ -f1)
echo "Pod B secondary IP: $POD_B_SECONDARY_IP"

echo "=== Ping on secondary network (net1 to net1) ==="
kubectl exec pod-a -- ping -c 3 -I net1 "$POD_B_SECONDARY_IP"

# Test connectivity on the primary network
POD_B_PRIMARY_IP=$(kubectl get pod pod-b -o jsonpath='{.status.podIP}')
echo "Pod B primary IP: $POD_B_PRIMARY_IP"

echo "=== Ping on primary network (eth0 to eth0) ==="
kubectl exec pod-a -- ping -c 3 "$POD_B_PRIMARY_IP"
```

### Part 6: Verify Isolation

```bash
# Pod C does NOT have a secondary network — it should not reach the macvlan subnet
POD_A_SECONDARY_IP=$(kubectl exec pod-a -- ip -4 addr show net1 | grep inet | awk '{print $2}' | cut -d/ -f1)
echo "Pod A secondary IP: $POD_A_SECONDARY_IP"

echo "=== Pod C trying to reach secondary network (should fail) ==="
kubectl exec pod-c -- ping -c 3 -W 2 "$POD_A_SECONDARY_IP" || echo "Expected failure: Pod C has no route to the macvlan subnet"

# But Pod C CAN reach Pod A on the primary network
POD_A_PRIMARY_IP=$(kubectl get pod pod-a -o jsonpath='{.status.podIP}')
echo "=== Pod C reaching Pod A on primary network (should succeed) ==="
kubectl exec pod-c -- ping -c 3 "$POD_A_PRIMARY_IP"
```

### Part 7: Inspect Routing

```bash
# See the routing table inside a multi-network pod
echo "=== Pod A routing table ==="
kubectl exec pod-a -- ip route show

# Observe: default route via eth0, specific subnet route via net1
# This ensures internet/API-server traffic stays on the management network
```

### Success Criteria

- [ ] Multus DaemonSet is running on all three nodes
- [ ] NetworkAttachmentDefinition `macvlan-conf` is created in the default namespace
- [ ] Pod A and Pod B each have two interfaces (`eth0` and `net1`)
- [ ] Pod C has only one interface (`eth0`)
- [ ] Pod A can ping Pod B on the secondary network via the `net1` interface
- [ ] Pod A can ping Pod B on the primary network via the `eth0` interface
- [ ] Pod C cannot reach Pod A's secondary IP (no route to the macvlan subnet)
- [ ] Pod C can reach Pod A's primary IP (standard Kubernetes networking works normally)
- [ ] The `network-status` annotation on Pod A shows both networks with correct IPs
- [ ] The routing table in Pod A shows the default route via `eth0` and the subnet route via `net1`

### Bonus Challenge

Create a second NetworkAttachmentDefinition using the `bridge` type on a different subnet (e.g., `10.30.0.0/24`). Attach both `macvlan-conf` and the new bridge network to a pod so it has three interfaces total (`eth0`, `net1`, `net2`). Verify all three interfaces are present, have IPs from the correct subnets, and that the pod can communicate on each network independently.

---

## Cleanup

```bash
# Delete the lab cluster to free resources
kind delete cluster --name multus-lab
```

---

## Key Takeaways

1. **Multus is a meta-plugin, not a network provider.** It orchestrates other CNI plugins — your default CNI for `eth0` and secondary plugins (macvlan, ipvlan, bridge, SR-IOV) for additional interfaces — but does not configure any network itself. You cannot use Multus without a working default CNI.

2. **Multi-homing is for specialized workloads, not general-purpose applications.** If your pods serve HTTP behind a Service, you almost certainly do not need Multus. The additional complexity is justified only when you need physically separate network paths, hardware-accelerated interfaces, or compliance-mandated network segregation that cannot be satisfied by the single-interface model.

3. **Kubernetes Services and DNS only work on the default network.** Any secondary network communication requires IP-level addressing, static IP reservations (via Whereabouts), or custom application-level service discovery. This is the most common operational surprise for teams new to Multus.

4. **Whereabouts is essential for cluster-wide IP coordination on secondary networks.** The default `host-local` IPAM works per-node and will produce IP conflicts when multiple nodes share a subnet. Whereabouts uses Kubernetes CRs to maintain a shared allocation state without an external coordination service.

5. **Every secondary network type has a specific tradeoff.** Macvlan gives each pod a unique MAC but blocks host-to-pod communication. IPvlan shares a MAC and scales to more interfaces but is less visible to MAC-based tooling. Bridge provides node-local L2 with host communication but requires additional configuration for multi-node reachability. SR-IOV delivers line-rate performance but sacrifices all kernel networking features on that interface.

---

## Sources

- [Multus CNI GitHub Repository](https://github.com/k8snetworkplumbingwg/multus-cni) — Source code, documentation, and issue tracker for the Multus meta-plugin
- [Network Plumbing Working Group](https://github.com/k8snetworkplumbingwg) — The NPWG GitHub organization, home of Multus and related multi-network projects
- [Multus Quickstart Guide](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/quickstart.md) — Official step-by-step installation and configuration guide
- [Multus How-To Guide](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/how-to-use.md) — Detailed usage guide covering NetworkAttachmentDefinitions and pod annotations
- [Whereabouts IPAM](https://github.com/k8snetworkplumbingwg/whereabouts) — Cluster-wide IP address management for secondary networks
- [SR-IOV Network Device Plugin](https://github.com/k8snetworkplumbingwg/sriov-network-device-plugin) — Discovers and advertises SR-IOV Virtual Functions as Kubernetes resources
- [SR-IOV CNI Plugin](https://github.com/k8snetworkplumbingwg/sriov-cni) — Moves SR-IOV VFs into pod network namespaces
- [CNI Specification (CNCF Incubating)](https://github.com/containernetworking/cni/blob/main/SPEC.md) — The Container Network Interface specification that Multus and all delegate plugins implement
- [Kubernetes Networking Model](https://kubernetes.io/docs/concepts/services-networking/) — Official Kubernetes documentation on the pod networking model
- [Kubernetes Network Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/) — Overview of CNI plugins and how they integrate with Kubernetes
- [NPWG De-Facto Standard for Network CRDs](https://github.com/k8snetworkplumbingwg/multi-net-spec) — The multi-network specification repository maintained by the NPWG
- [Multus Thick Plugin Documentation](https://github.com/k8snetworkplumbingwg/multus-cni/blob/master/docs/thick-plugin.md) — Architecture and deployment guide for the thick (DaemonSet-based) plugin mode

---

## Next Module

Continue to [Module 5.2: Service Mesh](../module-5.2-service-mesh/) to learn about traffic management, mutual TLS, and when service mesh patterns complement or overlap with multi-network architectures.
