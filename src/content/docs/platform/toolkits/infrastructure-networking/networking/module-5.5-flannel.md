---
title: "Module 5.5: Flannel - Overlay Networking from the Ground Up"
slug: platform/toolkits/infrastructure-networking/networking/module-5.5-flannel
sidebar:
  order: 6
revision_pending: false
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 60-75 minutes

**Hypothetical scenario:** An on-call rotation spends three days chasing intermittent failures in a Kubernetes cluster where small API responses succeed but large file uploads stall mid-transfer, and every layer from application logs to node health checks initially looks healthy.

```
[Day 1, 09:14 AM]
@backend-lead    File uploads are failing intermittently.
@backend-lead    But only large files. Small files work fine.
@sre-team        Define "large."
@backend-lead    Anything over... I don't know, maybe 1400 bytes?
@sre-team        Checking network.

[Day 1, 02:30 PM]
@sre-team        tcpdump shows the packets leaving the source pod.
@sre-team        tcpdump shows the packets never arriving at the dest pod.
@sre-team        They just... vanish. In the middle of the cluster.

[Day 3, 11:46 AM]
@sre-team        FOUND IT.
@sre-team        Node MTU is 1500. VXLAN overlay adds a 50-byte header.
@sre-team        Effective pod MTU should be 1450. But Flannel was configured
                 with the default 1500.
@sre-team        Any packet over 1450 bytes gets silently dropped after
                 encapsulation because it exceeds the physical NIC MTU.
@sre-team        One line fix: set pod MTU to 1450 in the Flannel config.
```

That team learned something the hard way: overlay networking adds bytes to every packet, and if you do not account for that overhead, large payloads can disappear without a clear error. Small API calls keep working, which makes the failure look random until you understand the MTU math. This module teaches the durable CNI and pod-networking concepts first, then uses Flannel as a transparent example you can trace hop by hop.

**Prerequisites:** You should already understand Kubernetes Pods and Services, how CNI plugins attach networks to sandboxes, and basic TCP/IP including MTU and routing. The [Linux Networking fundamentals](/linux/foundations/networking/) module covers bridges and veth pairs that Flannel relies on. The hands-on exercise uses a local kind cluster with Docker available on your workstation.

---

## What You'll Be Able to Do

After completing this module, you will be able to deploy, configure, and reason about Flannel as one CNI option among several peers, using capability-based comparison rather than habit or tutorial defaults.

- **Deploy Flannel as a simple overlay network for Kubernetes clusters using VXLAN or host-gw backends**
- **Configure Flannel's network backends and MTU settings for performance across different network topologies**
- **Explain why Flannel does not enforce NetworkPolicy and how Canal or a policy-capable CNI fills that gap**
- **Compare Flannel's connectivity model against Calico, Cilium, and kube-router using capability-based criteria**

---

## Why This Module Matters

Every Container Network Interface (CNI) plugin answers the same fundamental question: how does a pod on one node reach a pod on another node with a stable, routable IP, without breaking Kubernetes' flat networking model? The [CNI specification](https://github.com/containernetworking/cni/blob/main/SPEC.md) defines a small contract — `ADD`, `DEL`, and optional `CHECK` operations — that the kubelet invokes when pods start or stop. The plugin creates interfaces, assigns addresses through IP Address Management (IPAM), and installs routes or tunnels so traffic can flow. Flannel is one of the oldest implementations of that contract for Kubernetes, originally developed at CoreOS and now maintained by the [flannel-io community](https://github.com/flannel-io/flannel).

Flannel's value in this curriculum is pedagogical before it is prescriptive. It implements the simplest useful overlay: assign each node a pod subnet, wrap cross-node pod traffic in an encapsulation header (classically VXLAN), and let the physical network carry node-to-node packets it already understands. That transparency makes Flannel an excellent lens for learning concepts that outlive any single vendor — overlays versus routed underlays, MTU overhead, subnet allocation, and the separation between connectivity and policy enforcement.

You will also learn where Flannel deliberately stops. It connects pods; it does not implement [Kubernetes NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/). It does not replace kube-proxy for Service load balancing. It does not provide flow observability or BGP integration with your datacenter fabric. Those gaps are not oversights — they reflect a design choice to stay small. Understanding that boundary helps you decide when Flannel (or Flannel plus a policy engine) fits, and when a fuller CNI such as Calico or Cilium is a better match.

> **The Postal-Wrap Analogy**
>
> Think of pod traffic as a letter addressed to another pod. The physical network only knows how to deliver mail to building addresses (node IPs), not to individual desks (pod IPs). An overlay wraps your letter inside a larger envelope addressed to the remote building. The post office handles the outer envelope; the receiving building opens it and delivers the inner letter locally. VXLAN is that outer envelope — and like real packaging, it adds thickness you must subtract from your maximum letter size (MTU).

---

## Core Content

## Part 1: The CNI Model and Kubernetes Pod Networking

Kubernetes declares four networking requirements that every CNI must satisfy in practice: every pod receives its own IP address; pods can talk to other pods without Network Address Translation (NAT); pods on the same node can communicate; and pods on different nodes can communicate. The first three requirements are handled locally on each node through virtual ethernet (veth) pairs, bridges, and IPAM. The fourth requirement — cross-node pod reachability — is where CNIs diverge in architecture and operational cost.

The kubelet does not embed networking logic itself. When a sandbox is created, the runtime asks the configured CNI plugin chain to run. A typical Flannel deployment uses a meta-plugin that reads cluster state written by `flanneld`, then delegates to the `bridge` plugin for local veth creation and address assignment. The separation of concerns matters: `flanneld` owns the overlay control plane (subnets, routes, tunnel endpoints), while the CNI `ADD` handler owns per-pod interface plumbing. If either side is misconfigured, symptoms show up in different places — cluster-wide routing failures versus single pods stuck in `ContainerCreating`.

Two broad strategies exist for cross-node connectivity, and most production CNIs pick one or combine them. **Overlay / encapsulation** wraps pod frames inside UDP or IP headers so the underlay only routes between node IPs. **L3 routing** advertises pod CIDRs into the physical network (static routes, BGP, or host-gateway routes) so pod packets travel without an extra header. Overlays tolerate arbitrary L3 topologies at the cost of encapsulation overhead and MTU reduction. Routed models avoid encapsulation but require the network fabric to accept pod prefixes — feasible on bare metal with cooperative routers, often impractical in default cloud VPC layouts.

Service traffic follows a different path. ClusterIP, NodePort, and LoadBalancer Services are implemented by kube-proxy (iptables, IPVS, or an eBPF replacement), not by Flannel. Flannel ensures pod A can reach pod B's IP; kube-proxy ensures pod A can reach a Service virtual IP that may fan out to many backends. When debugging connectivity, always ask whether the failure is pod-to-pod (CNI) or client-to-Service (kube-proxy / dataplane). Mixing the two layers in one investigation creates false leads.

Multus and other multi-network CNIs extend the model by chaining multiple CNI `ADD` calls so a pod can attach to several interfaces. Flannel in its common deployment owns the primary `eth0` pod interface only. Secondary networks for specialized traffic (storage, RDMA, tenant isolation) require additional plugins and coordination. If your architecture mentions Multus, treat Flannel as one link in a chain rather than the entire story.

The CNI `CHECK` operation, when implemented, lets the kubelet verify that a pod's network namespace still matches expectations after restarts or live migrations. Flannel's focus on basic connectivity means operational health is often inferred from node readiness and DaemonSet status rather than per-pod CHECK results. Knowing which health signals your platform actually emits prevents false confidence during partial failures.

---

## Part 2: Why Overlay Networks Exist

Consider two nodes on a physical network that knows only node IPs. Node A hosts a pod at `10.244.0.5` and Node B hosts a pod at `10.244.1.8`. The pod CIDR `10.244.0.0/16` is invisible to upstream routers unless you configure them explicitly. If Pod A sends directly to `10.244.1.8`, the first router that lacks a matching route drops the packet or misroutes it. You either teach the physical network about every pod subnet (host-gw or BGP-style routing) or you encapsulate pod traffic inside packets the network already knows how to deliver.

Flannel's default VXLAN backend chooses encapsulation. The source node wraps the inner Ethernet frame in an outer IP/UDP header addressed from its own node IP to the destination node IP. Switches and routers forward the outer packet normally. The destination node decapsulates and injects the inner frame into its local bridge, which delivers to the target pod's veth. From the pod's perspective, the network looks flat; from the datacenter's perspective, only node IPs matter on the wire.

```
Node A (10.0.1.10)                    Node B (10.0.1.11)
+------------------+                  +------------------+
| Pod: 10.244.0.5  |                  | Pod: 10.244.1.8  |
+------------------+                  +------------------+
        |                                      ^
   Physical Network (10.0.1.0/24)
   Routes node IPs only — not 10.244.0.0/16
```

This design trades simplicity for overhead. Encapsulation consumes header bytes on every cross-node packet, which shrinks the effective Maximum Transmission Unit (MTU) available to applications. It also adds CPU cost for encapsulation and decapsulation on each node. For many clusters — especially labs, edge nodes, and small production environments — that trade is acceptable. For high-throughput or latency-sensitive workloads on flat L2 networks, a routed backend may perform better if your topology supports it.

Cloud provider networks sometimes impose their own MTU below 1500 on instance interfaces or overlay networks inside the VPC. Always measure from the node (`ip link show eth0`) rather than assuming Ethernet defaults. If the underlay MTU is 1450 because you sit inside another encapsulation layer, subtract VXLAN overhead again for pod MTU — compounding tunnels is common in nested virtualization and some managed Kubernetes offerings.

---

## Part 3: VXLAN Encapsulation and the Packet Walk

VXLAN (Virtual Extensible LAN) wraps a complete L2 frame inside a UDP datagram. In Flannel's default configuration, the VXLAN device is typically named `flannel.1` and listens on UDP port 8472 (Flannel's historical default, distinct from the IANA-assigned VXLAN port 4789 used elsewhere). The inner frame preserves pod MAC and IP addresses; the outer header uses node IPs so the underlay can route without pod-specific knowledge.

```
Original Pod-to-Pod Packet:
+-------------------------------------------------------+
| Inner Ethernet | Inner IP      | TCP/UDP | Payload    |
| (14 bytes)     | (20 bytes)    | (8-20)  | (variable) |
+-------------------------------------------------------+

After VXLAN Encapsulation (typical overhead ~50 bytes):
+------------------------------------------------------------------+
| Outer Ethernet | Outer IP | Outer UDP | VXLAN Hdr | Inner Frame |
| (14 bytes)     | (20 B)   | (8 B)     | (8 B)     | (as above)  |
+------------------------------------------------------------------+
```

If the physical NIC MTU is 1500 bytes, the largest inner IP payload a pod should emit without fragmentation is roughly 1450 bytes after accounting for VXLAN overhead (exact numbers depend on whether you count inner Ethernet and options headers). When pod interfaces still advertise MTU 1500, applications may send 1500-byte frames that become 1550 bytes on the wire after encapsulation, leading to silent drops when Path MTU Discovery fails or the Don't Fragment bit is set.

Tracing a cross-node flow builds intuition that transfers to any CNI, because every plugin must solve the same local attachment problem even when the remote transport differs. When you can narrate each hop from application socket to remote application socket, you can bisect failures quickly instead of guessing.

```
Pod A (10.244.0.5)              Pod B (10.244.1.8)
Node 1 (10.0.1.10)             Node 2 (10.0.1.11)

     [Pod A]                         [Pod B]
       | 1. App sends to 10.244.1.8      ^ 10. Delivered
       v                                 |
   veth (pod) -> veth (host) -> cni0 bridge
       | 4. Route: remote subnet via flannel.1
       v
   flannel.1 VTEP — 5. Encap to Node 2 UDP 8472
       |
   eth0 ===== physical network =====> eth0 on Node 2
       |
   flannel.1 — 6. Decap -> cni0 -> veth -> Pod B
```

Each hop is a potential failure point: missing routes, down tunnel device, firewall blocking UDP 8472, or incorrect subnet.env consumed by the CNI plugin. Flannel's simplicity means you can inspect these hops with standard Linux tools (`ip route`, `ip -d link`, `tcpdump`) without learning a proprietary CLI first.

Path MTU Discovery (PMTUD) complicates overlay debugging because applications may never see explicit errors when intermediate hops drop oversized packets. TCP stacks might retransmit with smaller segments eventually, masking the root cause as intermittent slowness rather than hard failure. UDP-based protocols and gRPC streams with large initial windows suffer more visibly. Teaching developers that `1450` bytes is a safe upper bound for VXLAN-backed pod networks prevents teams from spending days in application-level profiling when the network layer already knows the answer.

Hardware offload and checksum behavior can differ between encapsulated and non-encapsulated traffic on some NIC drivers. If performance tuning becomes necessary, profile on representative nodes with `iperf3` or your workload's native benchmarks rather than assuming a fixed percentage overhead from documentation. The pedagogical point remains: overlays always cost something — bytes on the wire and CPU cycles in software — even when the exact magnitude depends on your hardware generation and packet size distribution.

---

## Part 4: Flannel Architecture

Flannel splits responsibilities between a cluster-level daemon and a per-pod CNI plugin. **`flanneld`** runs as a DaemonSet on every node. It watches the Kubernetes API for Node objects, reads each node's `spec.podCIDR`, configures the selected backend device, writes `/run/flannel/subnet.env`, and programs routes to remote pod subnets. The **Flannel CNI binary** executes on each pod create: it reads `subnet.env`, delegates to `bridge` (or similar) for veth creation, assigns an address from the local `/24` (by default), and attaches the host veth to `cni0`.

```
+------------------------------------------------------------------+
|                     Kubernetes API Server                         |
|  Stores: Node.spec.podCIDR (subnet per node)                     |
+------------------------------------------------------------------+
         | watches                          |
         v                                  v
+----------------+                  +----------------+
| flanneld       |                  | flanneld       |
| Node 1         |                  | Node 2         |
| - subnet lease |                  | - subnet lease |
| - flannel.1    |                  | - flannel.1    |
| - subnet.env   |                  | - subnet.env   |
+----------------+                  +----------------+
```

When `kubeadm init --pod-network-cidr=10.244.0.0/16` runs, the controller manager allocates a pod CIDR block per node — commonly a `/24` per node inside the cluster `/16`. Node 1 might receive `10.244.0.0/24`, Node 2 `10.244.1.0/24`, and so on. flanneld on Node 1 installs a connected route for local pods via `cni0` and overlay routes for remote `/24`s via `flannel.1`. When a new node joins, all flanneld instances update their forwarding databases; no central SDN controller is required beyond the Kubernetes API.

The `/run/flannel/subnet.env` file bridges control plane and CNI data plane: flanneld writes it after learning the node's lease, and the CNI plugin reads it synchronously during each pod `ADD` so address assignment stays consistent with overlay routes.

```bash
FLANNEL_NETWORK=10.244.0.0/16
FLANNEL_SUBNET=10.244.0.1/24
FLANNEL_MTU=1450
FLANNEL_IPMASQ=true
```

`FLANNEL_MTU` propagates to pod interfaces when correctly configured — this is the knob that prevents the hypothetical MTU incident at the top of the module. `FLANNEL_IPMASN=true` enables masquerading for traffic leaving the pod network when needed for external connectivity. Because `subnet.env` lives on tmpfs, a node reboot races flanneld startup against kubelet pod creation; the Flannel DaemonSet uses elevated priority so the file usually exists before workload pods schedule.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**
>
> - **Upstream repository:** [github.com/flannel-io/flannel](https://github.com/flannel-io/flannel) under Apache-2.0.
> - **Latest tagged release at time of writing:** [v0.28.5](https://github.com/flannel-io/flannel/releases/tag/v0.28.5) (June 2026); confirm on the releases page before pinning manifests.
> - **Maintainers:** community-governed team listed in [GOVERNANCE.md](https://github.com/flannel-io/flannel/blob/master/GOVERNANCE.md) (maintainer affiliations and names change — check OWNERS).
> - **Default install manifest:** `kube-flannel.yml` from the latest GitHub release; default pod CIDR in docs is often `10.244.0.0/16` — must match `kubeadm` `--pod-network-cidr`.
> - **Backends documented upstream:** `vxlan` (default), `host-gw`, `wireguard`, plus cloud-specific backends — see [backends.md](https://github.com/flannel-io/flannel/blob/master/Documentation/backends.md).
> - **CNCF status:** Flannel is not a CNCF graduated project; treat governance and release cadence as vendor-community maintained, not as a formal CNCF conformance guarantee.
> - **Bundled in k3s:** Rancher k3s uses Flannel as its default CNI unless reconfigured — verify in current k3s networking docs for your version.

---

## Part 5: Backend Tradeoffs — VXLAN, host-gw, and WireGuard

Flannel selects a backend in its configuration (`net-conf.json` in the ConfigMap). The backend determines how inter-node pod traffic is carried.

**VXLAN (default)** creates the `flannel.1` device and encapsulates in UDP. It works when nodes can reach each other on L3 regardless of subnet layout, which is why cloud and hybrid clusters often start here. Overhead is typically quoted in the single-digit percent range for throughput, but your mileage depends on packet size, CPU, and whether hardware offload is available — do not treat informal percentages as benchmarks.

**host-gw** installs static routes pointing remote pod subnets at peer node IPs on the underlay interface. Packets leave without an encapsulation header, so MTU stays at the physical NIC value and CPU overhead is lower. The constraint is strict: nodes must share an L2 domain (same broadcast domain). If a router separates `10.0.1.0/24` from `10.0.2.0/24`, host-gw cannot magically bridge pod subnets without cooperating router routes.

**WireGuard** encrypts inter-node traffic using the WireGuard kernel module. It adds header overhead (plan for roughly 60 bytes when sizing MTU) in exchange for confidentiality on the wire. Useful when you need encryption in transit but are not ready to adopt a full zero-trust CNI.

| Feature | VXLAN | host-gw | WireGuard |
|---------|-------|---------|-----------|
| **Network requirement** | L3 between nodes | L2 same subnet | L3 between nodes |
| **Encapsulation** | UDP/VXLAN | None | WireGuard tunnel |
| **Encryption** | No | No | Yes |
| **Typical MTU reduction (1500 NIC)** | ~50 bytes | 0 | ~60 bytes |
| **Suggested pod MTU** | 1450 | 1500 | 1440 |
| **Cloud-friendly** | Usually yes | Depends on L2 layout | Usually yes |

Choose VXLAN when topology is unknown or spans routed subnets. Choose host-gw when all nodes share flat L2 and you want minimal overhead. Choose WireGuard when encryption between nodes is required and operators accept MTU tuning.

Some environments expose backend selection as a day-one cluster decision because changing backends later requires cordoning nodes, draining workloads, and reconciling routes across the fleet. Document the chosen backend, MTU, and firewall rules in your platform standard so application teams inherit consistent constraints. Backend migration from VXLAN to host-gw is not a ConfigMap tweak when your physical topology lacks L2 adjacency — validate topology before chasing performance tuning.

---

## Part 6: The NetworkPolicy Gap

[NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) is a Kubernetes API for declaring which pods may talk to which others. The API server validates and stores policies; a CNI or companion agent must translate them into dataplane rules (iptables, eBPF, or hardware ACLs). **Flannel does not implement that translation.** Policies you create will appear in `kubectl get networkpolicy` but will not drop or allow packets unless another component enforces them.

This creates a dangerous illusion: security reviews see policies in Git, auditors see resources in the cluster, yet traffic flows unchanged. Teams that need segmentation must add a policy engine. **Canal** combines Flannel for networking with Calico Felix for policy enforcement — historically distributed as a manifest pairing both. Alternatively, migrate to a CNI that natively supports NetworkPolicy (Calico, Cilium, kube-router with policy enabled, Weave Net in community maintenance).

Flannel is therefore a strong fit for learning, single-tenant labs, and environments where perimeter controls substitute for pod-level segmentation — provided that choice is explicit. It is a poor fit as the sole CNI when compliance requires demonstrable micro-segmentation between workloads on the same cluster.

Policy enforcement engines translate Kubernetes label selectors into dataplane rules. Without such a translator, policies remain declarative documentation. Security assessments should include a live test — for example, attempting a connection that a policy should block — rather than relying on object existence in etcd. Flannel-only clusters fail that test unless Canal or another enforcer is present.

---

## Part 7: Cross-CNI Capability Comparison

Compare CNIs by durable capabilities, not marketing labels. This table summarizes architectural differences; verify feature details against each project's current documentation before designing a production cluster.

| Capability | Flannel | Calico | Cilium | kube-router |
|------------|---------|--------|--------|-------------|
| **Primary connectivity model** | Overlay (VXLAN default) or L2 host routes | Routed / BGP or overlay / eBPF options | eBPF-native with overlay or routing modes | BGP on-node routing |
| **Encapsulation default** | VXLAN UDP 8472 | Optional IPIP/VXLAN depending on mode | Optional VXLAN/GENEVE | Typically none (BGP) |
| **NetworkPolicy enforcement** | No (use Canal or replace CNI) | Yes (Kubernetes + Calico CRDs) | Yes (identity-aware, L7 options) | Optional ipset/iptables policy |
| **Service dataplane** | Delegates to kube-proxy | Can integrate eBPF replacement | Can replace kube-proxy | Can replace kube-proxy |
| **IPAM** | host-local / delegated | Calico IPAM blocks | Cilium IPAM | kube-router + host-local |
| **Multi-NIC / secondary networks** | No | Limited / with Multus | With Multus | With Multus |
| **Observability** | Manual tcpdump / conntrack | Flow logs / policy dashboards | Hubble flows | Metrics / limited flow |
| **Typical sweet spot** | Simple overlay connectivity | Policy + BGP datacenter integration | eBPF performance + policy + mesh | Lightweight BGP router CNI |
| **Governance (verify upstream)** | flannel-io community | Tigera / Project Calico | Isovalent / Cilium community | CloudNativeLabs community |

No row declares a universal winner. A kind lab benefiting from transparent overlays differs from a regulated multi-tenant platform requiring policy and audit trails. Use the table to shortlist candidates, then validate with your network team on MTU, routing, and firewall requirements.

When reading vendor comparisons outside this curriculum, strip adjectives like "leading" or "standard" and rewrite the sentence in capability form: does the CNI enforce policy, does it require BGP, does it depend on kernel modules, does it replace kube-proxy? Those questions survive vendor marketing cycles. Flannel's row is intentionally narrow — strong connectivity teaching tool, weak on policy and observability — which clarifies when to pair it with other components or replace it entirely.

---

## Part 8: Installing and Operating Flannel

**kubeadm bootstrap** remains the common path: initialize with a pod CIDR that matches Flannel's configuration, then apply the release manifest.

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

If the CIDR mismatches, nodes may receive PodCIDRs outside Flannel's configured `Network`, producing routes that never converge. Helm installation is also supported via the [flannel-io chart repository](https://github.com/flannel-io/flannel) — pin chart and image versions rather than floating `latest` in production.

For learning, kind clusters disable the default CNI so you can install Flannel explicitly and observe the transition from `NotReady` nodes to a functioning pod network. The same manifest URL used in production labs works locally; differences appear in interface names and underlay MTU inside Docker networks rather than in Flannel's core logic.

To set MTU explicitly, edit the Flannel ConfigMap (`kube-flannel-cfg`) rather than hard-coding values in application manifests. Centralizing MTU in Flannel configuration ensures new pods inherit the correct interface setting through CNI `ADD` rather than requiring each Deployment to mount sysctls or init containers.

```json
{
  "Network": "10.244.0.0/16",
  "Backend": {
    "Type": "vxlan",
    "VNI": 1,
    "Port": 8472
  }
}
```

Set `"MTU": 1450` at the network or backend level per [configuration documentation](https://github.com/flannel-io/flannel/blob/master/Documentation/configuration.md), then restart the DaemonSet. Document the chosen MTU in runbooks so application teams know maximum safe payload sizes.

Upgrades deserve the same discipline as initial install. Flannel DaemonSet updates roll node by node; during rollout, expect brief windows where routes or tunnel state differ between versions if release notes mention backend default changes. Read the [release changelog](https://github.com/flannel-io/flannel/releases) before bumping images in production, and stage on a representative cluster that mirrors your topology (multi-NIC nodes, dual-stack, or host-gw if you use it). Pin image digests in manifests rather than mutable tags when your GitOps pipeline promotes networking components separately from application releases.

Operational ownership should name who maintains the Flannel ConfigMap, who approves CIDR changes, and who validates firewall tickets for UDP 8472 between node subnets. Networking components without clear owners drift — MTU defaults survive cluster migrations, stale `--iface` flags persist after hardware refreshes, and tutorial manifests linger long after security requirements outgrow them. Flannel's simplicity reduces moving parts but does not eliminate the need for platform governance.

---

## Part 9: Troubleshooting Overlay Networks

**MTU mismatches** present as large payload failures while small health checks pass. Reproduce with `ping -s <size> -M do` between pod IPs on different nodes; the working size plus headers should align with `FLANNEL_MTU`. Compare pod interface MTU, `flannel.1` MTU, and physical NIC MTU, and remember that nested overlays or cloud provider encapsulation may lower the underlay MTU before Flannel subtracts its own overhead.

**Cross-node isolation with healthy local traffic** often implicates firewall rules blocking UDP 8472, stale routes after node replacement, or flanneld selecting the wrong `--iface` when multiple NICs exist. Compare `kubectl -n kube-flannel logs` against `ip -d link show flannel.1` and route tables on both nodes, and verify that the node IP flanneld advertises matches the address peers use to reach that host.

**Subnet exhaustion** appears when more nodes need `/24` blocks than the cluster CIDR provides — a `/16` yields at most 256 `/24` subnets. Plan CIDR size at cluster birth; expanding later is painful and often requires rebuilding the cluster or executing manual migrations that downtime windows rarely accommodate.

**CNI races after reboot** occur when kubelet creates pods before flanneld repopulates `subnet.env`. Ensure flanneld starts with sufficient priority, and treat transient `ContainerCreating` errors after node boot as timing issues until flanneld logs confirm subnet.env was written.

**DNS and Service failures masquerading as CNI issues** show up when operators test with Service names but the CoreDNS pods themselves cannot schedule because the CNI was down. Always validate pod-to-pod IP connectivity before chasing Service or DNS paths, because kube-proxy and CoreDNS depend on a working pod network underneath.

---

## Part 10: IPAM, Subnet Math, and Cluster Sizing

Flannel inherits cluster-wide IP planning from Kubernetes node allocation rather than inventing a separate IPAM product. When the controller manager assigns `spec.podCIDR` per node, it effectively reserves non-overlapping slices of the cluster network. The default pattern — a `/24` per node inside a `/16` — is easy to reason about but easy to outgrow. Two hundred fifty-six nodes exhaust a `/16` if each consumes one `/24`; expanding later requires cordoning, draining, and rebuilding networking state in ways most teams prefer to avoid.

Within a node's `/24`, the bridge plugin typically assigns addresses from the usable host range, skipping network and broadcast addresses depending on configuration. Running more than roughly two hundred fifty pods on one node exceeds a single `/24`; while rare on bare metal, dense batch workloads or poorly configured autoscaling can approach limits. Monitoring IP consumption on busy nodes is therefore part of capacity planning, not an exotic edge case.

Dual-stack clusters add another planning dimension. If nodes receive both IPv4 and IPv6 PodCIDRs, flanneld must configure backends that understand both address families. Misaligned family configuration produces asymmetric symptoms — IPv4 pod traffic works while IPv6 fails, or vice versa — that look like application bugs until you inspect `spec.podCIDRs` and backend capabilities together.

Masquerading (`FLANNEL_IPMASQ=true`) affects how pods reach external destinations outside the pod CIDR. SNAT rewrites source addresses so upstream routers see node IPs instead of unroutable pod prefixes. This behavior interacts with network policies, audit logging, and external firewalls that key on source IP. Document whether your platform expects pod IPs to appear on the wire or node IPs after masquerading.

---

## Part 11: Canal and the Two-Layer CNI Pattern

Canal is not a third independent CNI so much as a **composition pattern**: keep Flannel's overlay connectivity while adding Calico Felix components that enforce policy. The historical [Canal manifest](https://raw.githubusercontent.com/projectcalico/calico/master/manifests/canal.yaml) bundled Flannel DaemonSets with Calico policy controllers. Operationally you still manage overlay MTU and UDP 8472 paths, but you gain Kubernetes NetworkPolicy enforcement and optionally Calico-specific policy CRDs if enabled.

The two-layer pattern teaches an architectural lesson that applies beyond Canal. **Connectivity** and **policy** are separable concerns. Some organizations standardize on one vendor for both; others mix — for example, a cloud VPC CNI for connectivity plus a policy sidecar. Flannel makes the separation obvious because it implements only the first layer. When evaluating any CNI, ask explicitly: which component creates routes/tunnels, which component enforces policy, and which component implements Services?

Migrating from plain Flannel to Canal is less disruptive than replacing Flannel entirely, but it is not zero-touch. Policy enforcement can suddenly block traffic that previously flowed. Roll out default-allow baselines, stage policies in audit or log-only modes where available, and maintain a rollback manifest. Treat policy enablement as a traffic-changing event worthy of change control, not a silent addon.

---

## Part 12: Decision Framework — When Flannel Fits

Use Flannel when your primary goal is **understandable overlay connectivity** with minimal moving parts: learning environments, CI clusters, edge nodes with constrained resources, or early-stage platforms where security relies on namespace isolation and perimeter controls rather than micro-segmentation. Flannel also fits when k3s or another distribution ships it as the default and your team has not yet standardized an alternative — provided you consciously accept the NetworkPolicy gap.

Re-evaluate Flannel when requirements appear that it does not natively satisfy: mandatory pod-level segmentation for compliance, BGP integration with datacenter ToR switches, identity-aware L7 policy, replacement of kube-proxy at scale, or deep flow telemetry for incident response. Those requirements do not imply Flannel was a mistake earlier; they indicate the platform matured. Many teams start with Flannel or Canal, then migrate to Calico or Cilium when policy and observability become first-class.

Migration paths typically progress from **Flannel (connectivity only)** to **Canal (connectivity + policy)** to **full Calico or Cilium** when BGP, eBPF dataplanes, or service mesh integration enter scope. Each step increases operational surface area. Budget time for MTU revalidation, firewall updates, and policy baselines during transitions. Never run two CNIs concurrently without a documented cutover plan — overlapping DaemonSets corrupt routes and IPAM state in difficult-to-debug ways.

Platform standards should also record **egress expectations**: whether workloads reach the internet via masqueraded node IPs, whether a firewall team sees pod CIDRs on internal links, and whether east-west traffic must be encrypted at the CNI layer or by a service mesh. Flannel answers east-west connectivity; it does not by itself satisfy encryption or egress auditing requirements. Making those gaps explicit during architecture review avoids retrofitting security controls after hundreds of workloads depend on promiscuous flat connectivity.

---

## Part 13: Observability and Debugging Without a GUI

Flannel ships without a first-class flow observability product comparable to Cilium Hubble or Calico flow logs. That omission reinforces its teaching value: you learn to use Linux and Kubernetes primitives directly. Start from pod symptoms, confirm IP and node placement, test pod-to-pod across nodes, then descend to node-level tools.

On the source node, `ip route get <dest-pod-ip>` shows which interface the kernel selects. Cross-node destinations should egress via `flannel.1` or the configured backend device. `tcpdump -i flannel.1 -n udp port 8472` confirms encapsulation leaving the node. On the destination, mirror the capture to verify decapsulated inner packets arrive. If outer UDP never appears, suspect firewall or wrong `PublicIP`/`InternalIP` selection in flanneld arguments.

Inside pods, `ip addr`, `ip route`, and `traceroute` to remote pod IPs reveal whether the problem is local routing or remote return path. Remember that NetworkPolicy absence means denials will not appear as policy verdicts — if traffic fails, it is connectivity, application, or kube-proxy — not hidden policy drops.

Document a standard triage checklist in your runbook: (1) Are both pods Running with IPs? (2) Same node or different? (3) Do node routes include remote pod CIDR via Flannel device? (4) Is UDP 8472 open? (5) Does MTU test with `ping -M do` pass at expected size? (6) Are Services involved? If yes, split the investigation to kube-proxy rules before blaming Flannel.

Correlating Kubernetes events with node-level state accelerates incidents. A pod stuck in `ContainerCreating` with CNI errors often coincides with missing `subnet.env` or a flanneld crash loop after an upgrade. Capture `kubectl -n kube-flannel get pods`, node `journalctl` for kubelet CNI messages, and the first failing `ADD` from `/var/log/` CNI directories when enabled. Building a timeline — upgrade applied, flanneld restarted, first pod failure — prevents rolling back the wrong component.

For platform engineers onboarding from cloud-managed Kubernetes, Flannel's explicit routes and tunnel devices demystify what managed CNIs hide behind the provider console. That transparency is worth preserving in internal training even if production eventually selects a different CNI. Understanding overlays makes you a better consumer of any network product because you know which questions to ask in architecture reviews.

---

## Did You Know?

1. Flannel predates the modern CNI specification and was later adapted to the standard CNI plugin interface — that history explains why control plane (`flanneld`) and data plane (CNI `ADD`) remain separate processes.

2. VXLAN was designed for datacenter VLAN scale limits (roughly 4,094 VLAN IDs versus millions of VXLAN network identifiers), but Kubernetes adopted it primarily to tunnel L2 pod frames across L3 underlays — not because clusters exhaust VLAN space.

3. Flannel's default VXLAN port 8472 differs from the IANA VXLAN port 4789; firewall playbooks copied from generic VXLAN docs may block Flannel while appearing correct on paper.

4. k3s ships Flannel by default, which means many engineers' first encounter with pod networking is an overlay model — verify current k3s release notes if you assume a different default CNI.

---

## Common Mistakes

| Mistake | What Goes Wrong | How to Fix |
|---------|-----------------|------------|
| Forgetting `--pod-network-cidr` during `kubeadm init` | Nodes lack `spec.podCIDR`; flanneld cannot configure subnets | Reinitialize with matching CIDR or carefully patch node PodCIDRs and Flannel config together |
| Mismatch between kubeadm CIDR and Flannel `Network` | Routes point to wrong prefixes; partial connectivity | Align both sides to the same CIDR before workloads start |
| Ignoring VXLAN MTU overhead | Silent drops for payloads above ~1450 bytes on 1500 MTU NICs | Set `FLANNEL_MTU` and backend MTU to physical MTU minus encapsulation overhead |
| Assuming NetworkPolicy works with Flannel alone | Policies exist in API but traffic is unchanged | Add Canal, Calico, Cilium, or another enforcement layer |
| Installing two CNIs without removing the first | Duplicate interfaces, conflicting routes, unpredictable IPAM | Fully remove old CNI manifests and binaries before installing another |
| Using host-gw across routed subnets | Remote pod traffic blackholed at intermediate routers | Switch to VXLAN/WireGuard or add pod routes on routers |
| Blocking UDP 8472 between nodes | flanneld healthy but cross-node pod traffic fails | Open inter-node firewall for Flannel's VXLAN port |
| Scaling beyond pod CIDR size | New nodes never receive PodCIDR allocations | Choose a larger cluster CIDR at creation time (for example `/14`) |

---

## Quiz

**Question 1:** Your physical network MTU is 9000 (jumbo frames). What pod MTU should you target for Flannel VXLAN?

<details>
<summary>Show Answer</summary>

Approximately **8950 bytes** if VXLAN overhead is about 50 bytes (9000 minus 50). Measure on your environment: inner headers and options can shift the exact safe value. Set Flannel MTU and verify with `ping -M do` between pods on different nodes.
</details>

**Question 2:** You apply a default-deny NetworkPolicy in a Flannel-only cluster where no Calico or other policy agent runs. Does application traffic stop immediately after the policy is admitted by the API server?

<details>
<summary>Show Answer</summary>

**No.** Flannel provides connectivity only. The API stores the policy, but no Flannel component enforces it. Use Canal or migrate to a policy-capable CNI to enforce rules.
</details>

**Question 3:** Compare Flannel's VXLAN backend with the host-gw backend in terms of encapsulation, topology requirements, and MTU impact on a cluster whose worker nodes all share one flat L2 subnet.

<details>
<summary>Show Answer</summary>

VXLAN encapsulates pod frames in UDP for transport across L3 networks, adding overhead. host-gw installs direct routes to remote pod subnets via peer node IPs without encapsulation, requiring nodes on the same L2 subnet (or explicit router cooperation).
</details>

**Question 4:** Pod on Node 1 sends to a pod on Node 2 via VXLAN. What destination IP appears in the outer header?

<details>
<summary>Show Answer</summary>

**Node 2's underlay IP** (for example its `InternalIP`). The outer packet is node-to-node; inner headers retain pod IPs invisible to intermediate routers until decapsulation.
</details>

**Question 5:** A new node joins; pods on it cannot reach existing pods, but flanneld logs are clean. What should you check?

<details>
<summary>Show Answer</summary>

**UDP 8472 connectivity** and firewall paths between the new node and existing nodes. flanneld can reach the API server while the VXLAN data plane remains blocked. Test with `nc -zu` or equivalent from node to node.
</details>

**Question 6:** Your platform team plans three hundred worker nodes using `--pod-network-cidr=10.244.0.0/16` with the default one `/24` per node allocation model. At what scale does this design break, and what planning change fixes it at cluster creation time?

<details>
<summary>Show Answer</summary>

**Subnet exhaustion:** a `/16` supports 256 `/24` blocks. Nodes beyond that will not receive PodCIDRs. Use a larger CIDR at init (for example `/14`) or smaller per-node prefixes if supported.
</details>

**Question 7:** Nodes live on `10.0.1.0/24` and `10.0.2.0/24` separated by a router. A colleague proposes switching from VXLAN to host-gw for performance. Good idea?

<details>
<summary>Show Answer</summary>

**No** unless routers advertise pod CIDRs. host-gw assumes L2 adjacency; routed subnets without pod routes will drop traffic. Stay on VXLAN or implement BGP/static pod routes on the router.
</details>

**Question 8:** A developer reports that ClusterIP Services fail while direct pod IP connections succeed in a Flannel cluster. Where should you investigate first relative to Flannel's responsibilities versus kube-proxy?

<details>
<summary>Show Answer</summary>

Flannel handles **pod-to-pod IP connectivity**. kube-proxy (or an eBPF replacement) implements **Service VIP load balancing**. A working CNI does not by itself fix Service routing issues — debug each layer separately.
</details>

---

## Hands-On Exercise: Deploy Flannel, Test Connectivity, and Probe MTU

**Objective:** Deploy Flannel on a three-node kind cluster, verify cross-node pod communication, reproduce MTU boundary behavior, and confirm that NetworkPolicy objects are stored but not enforced. Budget twenty to twenty-five minutes and ensure Docker, kind, and kubectl are installed locally.

### Step 1: Create a Multi-Node kind Cluster Without a CNI

```bash
cat <<'EOF' > /tmp/kind-flannel.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.244.0.0/16"
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

kind create cluster --config /tmp/kind-flannel.yaml --name flannel-lab
kubectl get nodes
```

Until a CNI plugin assigns pod subnets and creates tunnel devices, kind nodes correctly remain in `NotReady` state because the kubelet cannot satisfy the pod network readiness condition.

### Step 2: Install Flannel

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
kubectl -n kube-flannel wait pod --all --for=condition=Ready --timeout=120s
kubectl get nodes
```

### Step 3: Deploy Test Pods on Different Nodes

```bash
kubectl create namespace flannel-test

cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pod-a
  namespace: flannel-test
spec:
  nodeName: flannel-lab-worker
  containers:
    - name: netshoot
      image: nicolaka/netshoot
      command: ["sleep", "3600"]
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-b
  namespace: flannel-test
spec:
  nodeName: flannel-lab-worker2
  containers:
    - name: netshoot
      image: nicolaka/netshoot
      command: ["sleep", "3600"]
EOF

kubectl -n flannel-test wait pod --all --for=condition=Ready --timeout=60s
```

### Step 4: Verify Cross-Node Connectivity and MTU

```bash
POD_B_IP=$(kubectl -n flannel-test get pod pod-b -o jsonpath='{.status.podIP}')
kubectl -n flannel-test exec pod-a -- ping -c 3 "$POD_B_IP"
kubectl -n flannel-test exec pod-a -- cat /sys/class/net/eth0/mtu
```

### Step 5: Probe the MTU Boundary

```bash
kubectl -n flannel-test exec pod-a -- ping -c 1 -s 1422 -M do "$POD_B_IP"
kubectl -n flannel-test exec pod-a -- ping -c 1 -s 1423 -M do "$POD_B_IP"
```

When pod MTU is 1450, the 1423-byte payload ping should fail or error while the 1422-byte test succeeds, demonstrating how encapsulation shrinks the safe maximum payload by roughly fifty bytes on standard Ethernet.

### Step 6: Confirm NetworkPolicy Is Not Enforced

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: flannel-test
spec:
  podSelector: {}
  policyTypes:
    - Ingress
EOF

kubectl -n flannel-test exec pod-a -- ping -c 2 "$POD_B_IP"
kubectl -n flannel-test delete networkpolicy deny-all-ingress
```

Even after creating a default-deny ingress policy, cross-node pings should continue to succeed because Flannel provides connectivity only and does not install policy rules in the dataplane.

### Success Criteria

- [ ] kind cluster created with three nodes and default CNI disabled
- [ ] Flannel DaemonSet running and all nodes `Ready`
- [ ] Cross-node ping between `pod-a` and `pod-b` succeeds
- [ ] MTU boundary demonstrated with `-s 1422` succeeding and `-s 1423` failing
- [ ] NetworkPolicy created but not enforced (ping still works)

### Cleanup

```bash
kind delete cluster --name flannel-lab
rm /tmp/kind-flannel.yaml
```

---

## Key Takeaways

1. **The durable lesson is the CNI model:** IPAM plus local veth plumbing plus inter-node connectivity strategy — Flannel is one implementation, not the definition of pod networking.

2. **Overlays wrap pod packets in node-routable envelopes.** VXLAN is Flannel's default envelope; account for ~50 bytes when sizing MTU.

3. **Flannel optimizes for operational simplicity, not policy or observability.** Treat NetworkPolicy as requiring another component.

4. **Backend choice follows topology:** VXLAN for general L3, host-gw for flat L2 performance, WireGuard when encryption between nodes matters.

5. **Debug in layers:** pod-to-pod (CNI routes and tunnels) versus pod-to-Service (kube-proxy or eBPF replacement).

6. **Compare CNIs on capabilities** — connectivity model, policy, service dataplane, IPAM — rather than popularity claims.

Closing the loop on the opening scenario: once pod MTU matches encapsulation overhead, large uploads succeed because every frame fits on the wire after VXLAN wrapping. The fix is small in lines of configuration but large in diagnostic effort if your team lacks the overlay mental model this module builds. Carry that lesson into design reviews — ask for MTU documentation whenever a new tunnel or CNI backend enters the architecture, and validate with bounded ping tests after every network change. Treat Flannel as the first chapter in pod networking literacy, not the final word on how your production platform should connect and secure workloads at scale. When you later read Calico BGP guides or Cilium eBPF docs, the vocabulary — pod CIDR, encapsulation overhead, policy enforcement plane, kube-proxy boundary — will already feel familiar because you learned it on a CNI small enough to hold in working memory. That familiarity is the durable return on investing time in Flannel even if your production standard eventually selects a different plugin. You will debug faster because you know which layer owns each hop in the path from pod to pod across nodes in your cluster.

---

## Next Module

Continue to **[Module 5.6: Calico](../module-5.6-calico/)** for routed/BGP networking, comprehensive NetworkPolicy, and eBPF dataplane options — the natural next step once overlay basics are solid.

---

## Sources

- [github.com/flannel-io/flannel](https://github.com/flannel-io/flannel) — Upstream repository, issue tracker, and release artifacts for kube-flannel manifests.
- [github.com/flannel-io/flannel releases v0.28.5](https://github.com/flannel-io/flannel/releases/tag/v0.28.5) — Tagged release page for version pinning and changelog verification.
- [github.com/flannel-io/flannel Documentation/backends.md](https://github.com/flannel-io/flannel/blob/master/Documentation/backends.md) — Authoritative backend types (vxlan, host-gw, wireguard) and configuration fields.
- [github.com/flannel-io/flannel Documentation/kubernetes.md](https://github.com/flannel-io/flannel/blob/master/Documentation/kubernetes.md) — Kubernetes deployment notes and interaction with kubeadm PodCIDR.
- [github.com/flannel-io/flannel Documentation/configuration.md](https://github.com/flannel-io/flannel/blob/master/Documentation/configuration.md) — Network configuration, MTU, and net-conf.json structure.
- [github.com/flannel-io/flannel Documentation/troubleshooting.md](https://github.com/flannel-io/flannel/blob/master/Documentation/troubleshooting.md) — Common failure modes and diagnostic commands.
- [github.com/flannel-io/flannel GOVERNANCE.md](https://github.com/flannel-io/flannel/blob/master/GOVERNANCE.md) — Maintainer community and governance model.
- [github.com/containernetworking/cni SPEC.md](https://github.com/containernetworking/cni/blob/main/SPEC.md) — CNI ADD/DEL/CHECK contract that all Kubernetes CNIs implement.
- [kubernetes.io cluster networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/) — Official Kubernetes networking model and CNI requirement.
- [kubernetes.io NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — NetworkPolicy API semantics and enforcement prerequisites.
- [projectcalico/calico canal.yaml](https://raw.githubusercontent.com/projectcalico/calico/master/manifests/canal.yaml) — Canal manifest combining Flannel networking with Calico policy controller.
- [docs.cilium.io stable documentation](https://docs.cilium.io/en/stable/) — Cilium reference for comparison on eBPF dataplane and policy.
- [github.com/cloudnativelabs/kube-router](https://github.com/cloudnativelabs/kube-router) — kube-router project combining BGP routing, optional policy, and service proxy.
