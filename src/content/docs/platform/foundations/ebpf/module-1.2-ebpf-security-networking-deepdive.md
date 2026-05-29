---
citations_verified: true
title: "Module 1.2: eBPF Security & Networking Deep-Dive"
slug: platform/foundations/ebpf/module-1.2-ebpf-security-networking-deepdive
sidebar:
  order: 2
---

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 70-85 minutes
>
> **Prerequisites**: [eBPF Fundamentals](module-1.1-ebpf-fundamentals/) (hooks, maps, verifier — assumed, not re-taught). For tool context, skim [Cilium overview](/platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/) and [Tetragon overview](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/) first; this module covers what those overviews skip: kernel datapath mechanics.
>
> **Track**: Foundations

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Trace** a pod-to-Service packet through Cilium's eBPF datapath (socket redirect, tc, conntrack maps) and contrast that path with kube-proxy iptables traversal.
2. **Explain** why Cilium's kube-proxy replacement uses BPF service maps for ClusterIP/NodePort handling, what breaks when kube-proxy and Cilium replacement coexist, and how to validate or roll back a migration using documented Cilium steps.
3. **Separate** L3/L4 identity-aware policy enforced in the BPF datapath from L7 HTTP policy delegated to Envoy, including when each layer should own a decision.
4. **Choose** Tetragon hook families (kprobe, tracepoint, LSM) for a given enforcement goal, articulate TOCTOU risk on syscall hooks, and contrast kernel `Sigkill` with userspace-only alerting.

---

## Why This Module Matters

[Module 5.1: Cilium](/platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/) teaches you to *operate* Cilium: install with Helm, write `CiliumNetworkPolicy`, debug drops with Hubble, and flip `kubeProxyReplacement=true`. [Module 4.5: Tetragon](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/) teaches you to *deploy* runtime security: install the DaemonSet, author `TracingPolicy` YAML, and observe `Sigkill` in action. Neither module is written to answer the question an on-call platform engineer asks at 3 AM when packets vanish but `kubectl get pods` is green: **which BPF program on which hook made this verdict, and what map entry did it read?**

That question is the gap this module fills. [eBPF Fundamentals](module-1.1-ebpf-fundamentals/) already gave you the generic hook table (XDP, tc, cgroup, LSM) and the program/map/helper lifecycle. Here you apply that vocabulary to the two production stacks most teams deploy together: **Cilium's networking datapath** and **Tetragon's enforcement datapath**. You will not learn another `cilium install` flag parade; you will learn what the agent compiles into the kernel and why that design differs from iptables kube-proxy and from Falco-style userspace detection. The module is intentionally cross-linked to toolkit overviews so you can descend from operations to mechanisms in one sitting without duplicating install guides or CRD field references that drift with product releases.

> **The Datapath vs Dashboard Analogy**
>
> A car dashboard tells you speed, fuel, and warnings. The engine, transmission, and brakes determine what actually happens when you press the pedal. Cilium's CLI and Hubble are the dashboard; XDP/tc programs, service LB maps, and CT maps are the engine. Tetragon's `TracingPolicy` CRD is the dashboard; kprobes, tracepoints, and LSM BPF programs are the engine. This module is for engineers who need to open the hood.

---

## Positioning: What You Already Know vs What We Add

| Topic | Covered in overview modules | Added here (kernel layer) |
|-------|----------------------------|---------------------------|
| Cilium install, Hubble, identity labels | [5.1 Cilium](/platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/) | Hook placement: where identity and policy verdicts attach in tc/socket paths |
| kube-proxy pain, `kubeProxyReplacement` Helm value | 5.1 Part 7 | BPF `lb` service map lookup model; coexistence/rollback hazards per Cilium docs |
| L7 HTTP policies, Envoy | 5.1 policy sections | Layer split: BPF denies L3/L4 early; Envoy parses L7 when redirected |
| TracingPolicy YAML, `Sigkill` demos | [4.5 Tetragon](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/) | kprobe vs tracepoint vs `lsmhooks`; TOCTOU; kernel kill vs userspace alert |
| Verifier, maps, hook families | [1.1 eBPF Fundamentals](module-1.1-ebpf-fundamentals/) | Assumed prerequisite — not repeated |

Read the table as a routing guide: if your question is "how do I install," open 5.1 or 4.5; if your question is "what did the kernel do to this packet or syscall," stay in this module. The split mirrors how platform teams staff ownership — network engineering for Cilium values and datapath health, security engineering for Tetragon policies — while kernel/datapath literacy is shared foundation work both groups need after 1.1.

---

## Part 1: Cilium's eBPF Datapath — Where Packets and Sockets Meet Policy

Cilium's datapath is not one monolithic BPF program. It is a **pipeline** of programs and maps maintained by the per-node agent, fed by Kubernetes state (Pods, Services, NetworkPolicies, identities), and attached at multiple hook families described in [Cilium's BPF architecture reference](https://docs.cilium.io/en/stable/reference-guides/bpf/architecture/). The upstream documentation states that **tc and XDP** are the two main networking subsystems for attached BPF programs: XDP runs at the earliest driver receive point with minimal metadata, while tc runs later with richer packet context and access to more helpers — a deliberate performance-versus-context trade-off documented in the same guide.

For Kubernetes workloads, most pod traffic is handled through **socket-level and tc programs** rather than only XDP. Socket-level BPF (cgroup and skb hooks tied to pod sockets) lets Cilium associate traffic with **endpoint identity** before expensive stack traversal. tc programs perform forwarding, NAT, policy verdicts, and encapsulation on the `skb` path. XDP remains important for NodePort acceleration, DDoS-style early drops, and optional XDP acceleration of kube-proxy replacement paths — `cilium-dbg status --verbose` reports `XDP Acceleration: Enabled|Disabled` under kube-proxy replacement details per [Kubernetes without kube-proxy](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/).

### Packet and socket path (conceptual)

```text
                    INGRESS (to pod / Service backend)
                    ===================================

[NIC] --> (optional XDP: early drop / LB accel)
            |
            v
        tc ingress (BPF: policy L3/L4, DNAT, tunnel decap)
            |
            v
        Linux stack routing / conntrack
            |
            v
        tc egress OR socket cgroup hook (identity, SNAT, policy)
            |
            v
        Pod network namespace (veth/tunnel)

                    CONTRAST: kube-proxy iptables path
                    ===================================

[NIC] --> netfilter PREROUTING (KUBE-SERVICES chain walk)
            --> per-Service chain --> per-Endpoint chain
            --> possible userspace proxy path
            --> POSTROUTING / conntrack

Each Service/Endpoint change can rewrite large chain sets (5.1 documents
rule-count growth). Cilium's agent updates BPF maps instead of rewriting
thousands of iptables rules on every Endpoints event.
```

**Conntrack in BPF maps:** Connection tracking for the datapath is not only Linux `nf_conntrack`. Cilium maintains **BPF CT maps** for connection state used by forwarding and policy. [Issue #11742](https://github.com/cilium/cilium/issues/11742) (referenced in 1.1) illustrates operational reality: stale or maximum-lifetime CT entries in Cilium's map can drop traffic while traditional conntrack counters look healthy — debugging requires `cilium bpf ct list` (or current equivalent) rather than only `conntrack -L`.

**Identity in maps, not IPs in rules:** Overview module 5.1 explains identity labels for operators. At the kernel layer, the agent allocates a numeric **security identity** and programs map keys so tc/socket programs ask "may identity A reach identity B on port P?" without embedding pod IPs in iptables-style rules. That is how scaling to many replicas avoids per-IP rule explosion at the policy layer — the lookup is map-based on identity IDs, not a linear chain walk.

### Socket-level enforcement

Socket-level programs attach at cgroup or skb points associated with pod sockets. They can influence **which address/port a socket may bind or connect to** and enforce policy closer to the workload than only on raw ingress packets. This matters for:

- Correct attribution when NAT has rewritten addresses on the wire.
- Per-workload egress control without relying solely on post-NAT packet headers.
- kube-proxy replacement features that use **socket LB** (documented dependency: Cilium's kube-proxy replacement depends on the socket-LB feature per [kube-proxy-free guide](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/)).

When debugging, combine Hubble (flow + policy verdict) with agent map dumps. Hubble tells you *what* was denied; map and program attachment state tells you *whether the datapath the agent thought it programmed matches the kernel*.

### Endpoint, identity, and policy map choreography

On each node, the Cilium agent maintains an **endpoint** object per local pod with a numeric **security identity** derived from Kubernetes labels. Policy is not stored as thousands of iptables tuples; it is compiled into BPF maps that answer a compact question at hook time: given source identity S, destination identity D, protocol, and port, is this flow allowed, denied, or redirected? The [Cilium terminology guide](https://docs.cilium.io/en/stable/overview/intro/terminology/) describes identities as cluster-wide numeric identifiers shared by all pods with the same label set, which is why scaling replicas does not multiply policy rows the way per-IP rules would.

The agent watches Kubernetes and atomically updates maps when Pods, Services, or policies change. From an operator's perspective the update is closer to editing a routing table than rewriting a script; from the kernel's perspective each packet still pays only the cost of map lookup and BPF execution at the hook. When Hubble prints `policy-verdict:none DROPPED`, the teaching moment is that the verdict name refers to a BPF policy map miss or explicit deny bit, not an iptables chain name you can grep in `iptables-save`.

**Predict before you read on:** a new Deployment can reach the API server and resolve DNS, yet fail pod-to-pod to an existing Service. In one sentence, name the Cilium object you inspect first (identity, policy map, or CT map) and why. Write it down, then compare with the quiz on identity mismatch later in this module.

### tcx and the evolving tc attachment surface

Linux 6.6+ introduced **tcx** as a traffic-control attachment surface for BPF programs ([eBPF tcx program type](https://docs.ebpf.io/linux/program-type/BPF_PROG_TYPE_SCHED_CLS/)). Cilium's documentation and codebase continue to center on **tc** hooks for the bulk of forwarding and policy because tc sees `skb` context with L3/L4 fields populated. Platform teams should treat tcx as part of the same design family: a programmable point in the traffic-control layer, not a separate product. When upgrading node kernels, re-validate datapath feature flags after agent upgrades because hook availability and helper sets can shift across kernel versions even when Helm values are unchanged.

### Debugging the datapath during incidents

When Hubble shows intermittent drops, collect three layers of evidence in parallel rather than guessing. First, the flow record: source and destination identity, protocol, port, interface, and `policy-verdict`. Second, the agent's view of programming: `cilium-dbg endpoint list` for local pods, `cilium-dbg policy get` for policy entries affecting those identities, and `cilium-dbg bpf ct list global` (or version-appropriate CT dump) when resets or stale sessions are suspected. Third, the Kubernetes object layer: label selectors on NetworkPolicy and CiliumNetworkPolicy, EndpointSlices for the Service, and whether a recent Deployment changed labels (minting a new identity). This ordering prevents the common mistake of tweaking Service definitions when the datapath is enforcing a policy map entry that still references an old identity.

### XDP acceleration in kube-proxy replacement context

`cilium-dbg status --verbose` reports whether **XDP Acceleration** is enabled for kube-proxy replacement. XDP attaches at the NIC driver's earliest receive point; when acceleration is on, some NodePort and Service paths can be handled with lower per-packet overhead than tc-only handling for eligible traffic. When acceleration is off, the same logical Service frontends still exist in BPF maps — packets simply traverse more stack before hitting tc programs. Operators should not treat "XDP disabled" as "kube-proxy replacement broken," but they should document expected CPU profiles for NodePort-heavy workloads because acceleration is a performance knob, not a correctness requirement, per the kube-proxy replacement details section in Cilium's documentation.

For kube-proxy replacement specifically, validate that the node's Service frontends exist before chasing application logs. A missing frontend in `cilium-dbg service list` is an agent programming or Kubernetes watch problem. A present frontend with drops is policy, backend readiness, or CT state. NodePort issues often narrow to **devices** and SNAT/DSR mode rather than ClusterIP programming. Document the commands that worked on your Cilium version in your internal runbook because subcommand names drift between `cilium`, `cilium-dbg`, and `cilium bpf` wrappers.

---

## Part 2: kube-proxy Replacement — Maps Instead of Rule Explosion

kube-proxy is the Kubernetes control-plane component that programs per-node datapath state so Service VIPs reach backends. In iptables mode it materializes that state as netfilter rules. In ipvs mode it uses ipset and IPVS tables. Cilium's replacement keeps the Kubernetes API contract (ClusterIP, NodePort, LoadBalancer, Endpoints) but implements forwarding in BPF maps probed by the agent's programs. The mental model shift for SRE teams is that **Service updates become map writes**, not chain rewrites. That is why large Endpoint churn events show up as latency spikes in iptables clusters but often as short agent reconciliation work in BPF clusters — the asymptotics differ even when single-packet latency looks similar in micro-benchmarks.

### Why iptables/kube-proxy does not scale (mechanism)

kube-proxy in iptables mode implements Service VIPs by installing netfilter rules. The Kubernetes [nftables kube-proxy blog](https://kubernetes.io/blog/2025/02/28/nftables-kube-proxy/) describes the core problem for large clusters: matching can degrade toward **O(n) chain walks** as Services and Endpoints grow, and full rule reprogramming on updates adds latency and connection disruption risk. Module 5.1 narrates that pain from an operator perspective; the mechanism is **linear rule evaluation and bulk rewrite**, not a mysterious "Kubernetes slowness."

### What Cilium installs instead

With `kubeProxyReplacement=true`, the Cilium agent programs **eBPF load-balancing maps** that map Service IP/port (and NodePort variants) to backend endpoints. On each relevant packet or socket operation, BPF performs a **hash or Maglev lookup** (configurable via `loadBalancer.algorithm`) rather than traversing `KUBE-SVC-*` chains. The [kube-proxy-free documentation](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/) shows validation: after replacement, `iptables-save | grep KUBE-SVC` is empty while `cilium-dbg service list` shows BPF-managed frontends and backends.

```text
Service VIP + port  --->  BPF LB map lookup  --->  backend IP:port
                              |
                              +-- Maglev (optional): consistent
                                  backend selection per 5-tuple;
                                  documented for external (N-S) traffic
```

**Maglev** (optional) precomputes lookup tables per Service so backend churn causes minimal reassignment — documented with table-size primes and `maglev.hashSeed` requirements in the same guide. **Random** algorithm uses less memory but lacks that consistency property.

**East-west vs north-south:** In-cluster (E-W) connections can be bound to backends at socket connect time without the same Maglev path used for external NodePort traffic — the upstream docs distinguish these behaviors explicitly. Misunderstanding that split leads to "works from outside, weird from inside" bug reports that are design, not random flakiness.

### SNAT, DSR, and hybrid modes at the kernel

Default NodePort handling in Cilium's kube-proxy replacement uses **SNAT** on the node that receives external traffic when backends live elsewhere: the node forwards on behalf of the client, and return traffic hairpins through that node. **DSR (Direct Server Return)** lets backends reply directly to clients using the Service IP as source on SYN paths, preserving client source IP for policy on the backend node and reducing load on the ingress node. DSR trades complexity for path efficiency: cloud providers may block the required forwarding patterns, MTU may need adjustment, and only some dispatch encodings (IPv4 option, Geneve, etc.) work per routing mode — see the DSR tables in [kube-proxy-free](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/#direct-server-return-dsr).

**Hybrid** mode uses DSR for TCP and SNAT for UDP when you want TCP client IP preservation without UDP MTU issues. **Annotation-based** modes let individual Services opt into DSR while the cluster default remains SNAT. Operators should choose mode deliberately in design docs, not only via Helm defaults, because the mode defines what Hubble will show for reverse-path flows and which source IP selectors remain meaningful on backend nodes.

### Performance claims discipline

Do not quote unverified "10x faster" microsecond numbers in runbooks. Acceptable statements anchored in primary sources:

- iptables-mode kube-proxy: rule-set growth and O(n)-style matching concerns — [Kubernetes nftables kube-proxy post](https://kubernetes.io/blog/2025/02/28/nftables-kube-proxy/).
- Cilium: BPF map lookups for service translation; optional Maglev; socket LB — [Cilium kube-proxy-free](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/) and [BPF architecture](https://docs.cilium.io/en/stable/reference-guides/bpf/architecture/).
- Published benchmarks: cite a specific Isovalent/Cilium benchmark page if your organization requires numbers; otherwise describe mechanisms and measure in *your* cluster.

### Coexistence hazard (critical for migrations)

Cilium warns that running **kube-proxy and eBPF replacement in parallel on an already-serving cluster** breaks existing connections because NAT tables are independent. New clusters may coexist briefly on nodes not yet serving traffic, but migration must treat kube-proxy removal as a **planned cutover**, not a silent toggle. See the warning block in [Kubernetes without kube-proxy](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/).

### Socket LB and east-west behavior

The same guide states that Cilium's eBPF kube-proxy replacement **depends on the socket-LB feature**. Socket-level load balancing can bind pod connections to Service backends without the same Maglev path used for some north-south NodePort traffic. That split explains common tickets where external NodePort access misbehaves while in-cluster ClusterIP access works, or the reverse when `devices` and NodePort bindings disagree. `cilium-dbg status --verbose` under **KubeProxyReplacement Details** lists socket LB, protocols, devices, SNAT/DSR mode, and whether **XDP Acceleration** is enabled — treat that block as the ground truth during incidents, not assumptions from an older blog post.

### Incident pattern: peak traffic and iptables choke points

The Kubernetes project's [nftables kube-proxy article](https://kubernetes.io/blog/2025/02/28/nftables-kube-proxy/) documents the mechanism: iptables-mode matching cost grows with rule volume, and bulk reprogramming on Endpoint changes can disturb existing flows. Cilium's [kube-proxy-free guide](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/) describes the remediation model — BPF service maps probed on packet/socket paths instead of `KUBE-*` chain rewrites — and the coexistence hazard when both datapaths run in parallel. The anonymized pattern below is composed from those documented failure modes, not a single named customer outage.

A retail-style platform enters peak week with thousands of Services and rapid Endpoint churn. kube-proxy in iptables mode holds very large per-node rule sets. Endpoint updates trigger multi-second `iptables-restore` windows during which new connections to some ClusterIPs fail sporadically while long-lived sessions survive. API server metrics stay green; only cross-Service calls fail. tcpdump shows SYNs arriving; SYN-ACKs for VIP paths do not. The architectural remediation is datapath replacement: program BPF service maps, remove kube-proxy during a maintenance window, validate with `cilium-dbg service list` and empty `KUBE-SVC` chains, and keep Hubble `policy-verdict` visible during pool drains. If the failure mode is instead wrong **identity** membership after a label change, replacing kube-proxy will not help — fix policy selectors and identity maps first.

---

## Part 3: NetworkPolicy Layers — BPF L3/L4 vs Envoy L7

Kubernetes NetworkPolicy is IP/port oriented. Cilium implements those semantics in the **BPF datapath** using identities derived from labels, so allow/deny for TCP/UDP ports happens in tc/socket programs without a sidecar on every packet.

**L7 policy is a different program domain.** HTTP method/path/header rules require parsing application-layer data. Cilium implements L7 by **redirecting eligible flows to Envoy** (Cilium's L7 proxy), documented in [Layer 7 policy](https://docs.cilium.io/en/stable/security/policy/layer7/). The split:

| Layer | Where decision runs | What it can see | Typical cost |
|-------|---------------------|-----------------|--------------|
| L3/L4 (incl. identity) | BPF tc/socket | IPs/ports/protocol, identity IDs | Per-packet BPF cost; no HTTP parsing |
| L7 HTTP/gRPC | Envoy on redirected flow | Methods, paths, headers | Proxy memory/CPU; not on every pod path by default |

```text
Pod A --> BPF policy (L4 allow TCP 443) --> if L7 rule exists -->
              redirect to Envoy listener --> match :method :path -->
              forward or deny --> Pod B

Proxy/L7 policy denies (HTTP 403, DNS REFUSED per Cilium L7 docs) with
flat app errors often mean probes or metrics paths the app never saw (5.1 quiz scenario).
```

**Design takeaway:** Put port/protocol constraints in BPF. Put HTTP semantics in L7 only when needed. Every L7 rule is a redirection and parsing commitment — not a free extension of `NetworkPolicy`.

### gRPC and non-HTTP L7

The Layer 7 documentation centers on HTTP because it is the most common Kubernetes ingress protocol. gRPC runs over HTTP/2 and can be governed by L7 rules where Cilium's proxy supports the needed visibility. When your API is binary gRPC without path-level rules you can express, prefer L4 policy plus application authZ rather than forcing an L7 policy model that does not match the protocol. The kernel datapath still delivers packets to the proxy when L7 is enabled; the proxy must understand the framing. Misapplied L7 policy is a frequent source of "mysterious" partial outages where only some RPC methods fail because path rules do not cover them.

### DNS-aware policy stays in the agent, not in tc alone

Module 5.1 discusses DNS-based egress policies at the toolkit layer. At kernel depth, DNS policy integrates with the agent's knowledge of allowed names and translates that knowledge into datapath state over time. A pod's first UDP 53 query may race policy programming; operators should expect brief windows during policy churn. Combine DNS policy changes with Hubble DNS visibility rather than assuming the first query after apply succeeds if the name was previously denied.

Cluster Mesh and identity-based security across clusters rely on the same identity map replication between clusters; the overview in 5.1 covers operator workflows. At kernel depth, remember that **policy is evaluated on numeric identities programmed into maps**, and Cluster Mesh extends that identity space — debugging cross-cluster drops still begins with Hubble policy verdict plus identity IDs, not with `iptables -L`. When a remote cluster's identity is unknown locally, policy may treat it as `world` or a configured remote identity class depending on Helm settings — the failure mode looks like a policy deny with unfamiliar numeric IDs in Hubble, not like a routing blackhole, because encapsulation and tunnel datapath programming are separate BPF programs from policy maps but both must be healthy for cross-cluster traffic to succeed.

### When Envoy enters the path

Layer 7 policies in Cilium require parsing HTTP or other application protocols. The datapath marks flows that need L7 inspection and **redirects them to Envoy** listeners managed by the agent. Packets that match only port/protocol rules can remain on the fast BPF path without parsing HTTP headers. Operators should expect higher CPU and latency on redirected flows and should treat L7 rules as product features with cost, not as syntactic sugar on `NetworkPolicy`. The [Layer 7 policy documentation](https://docs.cilium.io/en/stable/security/policy/layer7/) is explicit that non-matching HTTP requests are denied at the proxy, which is why metrics can show drops without application error logs when probes hit unlisted paths.

---

## Part 4: Tetragon Kernel Enforcement — Hooks and Kill Paths

[Module 4.5](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/) shows `TracingPolicy` with `kprobes` and `action: Sigkill`. This section explains **which kernel attachment implements those actions** and when to prefer LSM hooks — material 4.5 does not cover (no LSM discussion in that module).

Falco (4.5's comparison baseline) typically consumes syscall events from a kernel module or eBPF probe into a userspace engine that parses rules and emits alerts. Even when Falco uses eBPF for collection, the default **enforcement** story is external: Kubernetes admission, SOAR playbooks, or manual response. Tetragon's differentiator is running selectors and actions in the BPF program at the hook: `Override` can deny before the syscall completes; `Sigkill` terminates the process synchronously but does not always prevent the triggering operation (see below). Neither approach replaces the other without thought: Falco's rule language and ecosystem integrations are mature for detection; Tetragon's sweet spot is low-latency enforcement on well-scoped policies you are willing to test aggressively in `Post` mode first.

### kprobes and tracepoints

Per [Tetragon hook points](https://tetragon.cilium.io/docs/concepts/tracing-policy/hooks/):

- **kprobes** attach to kernel functions (including syscalls via `syscall: true`). They are flexible but **kernel-version and architecture sensitive** (`sys_write` vs `__arm64_sys_write` portability rules apply).
- **tracepoints** are static, generally **more stable across kernel versions**, and suit syscall observability (`raw_syscalls`, `syscalls` subsystems).

Tetragon documents a critical security engineering point: hooking a **syscall kprobe** can create **TOCTOU** races when arguments point to user memory — the attacker may mutate buffers after the probe runs but before the kernel consumes them. For enforcement on file paths or credentials, hook a later **`security_*` LSM function** where the kernel operates on copied-in kernel memory ([hooks documentation warning](https://tetragon.cilium.io/docs/concepts/tracing-policy/hooks/)).

### LSM BPF hooks

When `CONFIG_BPF_LSM=y` and `bpf` appears in `/sys/kernel/security/lsm`, Tetragon supports `spec.lsmhooks` with hooks like `file_open` and `bprm_check_security` ([LSM BPF section](https://tetragon.cilium.io/docs/concepts/tracing-policy/hooks/#lsm-bpf)). LSM programs participate in the kernel's mandatory access control hook list — appropriate when policy must see **resolved kernel objects** (`struct file`, `linux_binprm`) rather than raw user pointers.

| Hook style | Stability | Enforcement strength | Typical use |
|------------|-----------|----------------------|-------------|
| kprobe on syscall | Lower portability | Strong (Sigkill/Override) | Lab policies, known kernels |
| tracepoint | Higher portability | Observe + filter | Broad syscall telemetry |
| LSM BPF | Needs BPF LSM enabled | Strongest semantic match for MAC-style rules | Block `file_open` on `/etc/shadow` |

### Sigkill: kernel path vs userspace alert

**Userspace alert path (Falco-style):** syscall event copied to ring buffer → agent → alert → human or SOAR → maybe kill later.

**Tetragon `action: Sigkill` on a match:** BPF program at hook runs selectors → enforcement sends **SIGKILL** to the process in the enforcement path documented for TracingPolicy actions (4.5 describes exit code 137 on blocked exec). The mechanism is kernel-driven kill, not an external `kubectl delete pod`.

**SIGKILL caveat (read before relying on kill for prevention):** Per [Tetragon enforcement](https://tetragon.io/docs/concepts/enforcement/), sending a signal terminates the process synchronously but **does not always stop the triggering operation** — for example, a `SIGKILL` on a `write()` syscall does not guarantee the data was not written. **SIGKILL fires after the kernel hook executes**; for `open()`/`exec()`-class syscalls the side effect may have already started before the signal is delivered. To ensure the operation is not completed, combine `Sigkill` with `Override`, or prefer **LSM hooks** (`file_open`, `bprm_check_security`) where the kernel evaluates policy on copied-in kernel objects **before** the syscall returns — stronger for true prevention than syscall kprobes alone.

Other actions (`Post` for observability-only, `Override` returning errors) change whether you block or only record. Production rollouts should start with `Post`, validate selectors, then enable `Sigkill` on narrow policies — the same staged discipline as LSM policies in 1.1.

### Tracepoint portability for syscall telemetry

When kprobe symbol names drift between kernel versions, tracepoints under `raw_syscalls` or `syscalls` provide a more stable observability surface at the cost of less granular function-level context. Tetragon's hook documentation shows reading tracepoint formats from `/sys/kernel/tracing/events/.../format` to learn field indices. For platform teams standardizing on a single Kubernetes node image version, kprobes are acceptable for tightly scoped enforcement; for heterogeneous fleets (EKS with varied AMIs), tracepoints and LSM hooks reduce policy breakage on upgrade day. Document the chosen strategy in your security architecture note so reviewers do not mix hook families across environments without justification.

### Exporting enforcement events without diluting signal

Tetragon can export to stdout, files, or gRPC consumers. Kernel `Sigkill` events are high-signal but low-volume compared to observe-all syscall streams. Route enforcement events to a dedicated index or topic with retention distinct from verbose telemetry. Correlate `process_kprobe` or `process_lsm` event types with Kubernetes pod UIDs in the agent enrichment path so SOC playbooks do not rely on host PID alone after container restarts. The agent boundary matters: killing is kernel-side; ticketing is user-space — design runbooks that expect sub-second kill latency but minutes-long human response, and do not use kill latency as a substitute for ticket SLA.

### Choosing hooks for a requirement

| Requirement | Prefer | Avoid |
|-------------|--------|-------|
| Block execution of `/tmp/evil` before exec completes | LSM `bprm_check_security` via `bpf_lsm` (Linux 5.7+) | `sched_process_exec` tracepoint (post-event: observe or kill-after only, not pre-block); bare `sys_execve` kprobe with path pointer only |
| Kill cryptominer by binary name | kprobe/tracepoint on `sched_process_exec` with vetted args | Over-broad `Sigkill` on `sys_openat` |
| Audit only | tracepoint + `Post` | `Sigkill` on noisy hooks |
| Block connect to IP | kprobe `security_socket_connect` with BTF types | Userspace-only IP sets without kernel enforcement |

### Enforcement mode and the userspace agent boundary

Tetragon's agent loads BPF programs, applies Kubernetes-aware filters (namespaces, labels, binaries), and exports events to stdout, files, or gRPC consumers. **Enforcement** still occurs in the kernel when a selector matches and an action runs; the agent is not the kill switch for `Sigkill`. That distinction matters for latency budgeting: you do not need a round trip to user space to terminate a process, but you still need agent health to **observe** and **audit** what the kernel did. Pair Tetragon with SIEM export only after you validate selector precision in `Post` mode — the [TracingPolicy concepts page](https://tetragon.cilium.io/docs/concepts/tracing-policy/) warns that powerful low-level policies require kernel literacy to avoid TOCTOU and false-positive outages.

### Liz Rice framing: observe close to the event, enforce even closer

In *Learning eBPF* (O'Reilly), Liz Rice emphasizes that eBPF's value is running small verified programs at the point where kernel events already occur. Cilium applies that principle to packets and sockets. Tetragon applies it to syscalls and LSM decisions. The platform lesson is not "replace all security tools with BPF." The lesson is to know which layer owns the decision so you do not implement packet policy in an application sidecar or implement syscall enforcement only in a log pipeline that reacts seconds later.

### Example enforcement policy shape (LSM vs kprobe)

Module 4.5 shows kprobe-based `TracingPolicy` with `Sigkill` on `sys_execve`. For enforcement on sensitive file opens, the Tetragon docs recommend `lsmhooks` with `file_open` when BPF LSM is enabled — the hook sees a `struct file` in kernel memory. A staging policy might use `matchActions: Post` on `bprm_check_security` with `resolve: mm.owner.real_parent.comm` to learn parent process names before enabling `Sigkill`. The YAML shape differs from kprobes: `spec.lsmhooks` instead of `spec.kprobes`, and selectors use `matchBinaries` plus `matchArgs` on resolved paths. Treat 4.5 as the catalog of actions; treat this section as the hook-placement rationale you need when 4.5's kprobe examples are too brittle on your kernel matrix.

---

## Part 5: Operating Cilium and Tetragon on the Same Nodes

Most enterprise platforms run Cilium and Tetragon as DaemonSets on the same Linux workers. They share eBPF infrastructure (maps, verifier, BTF, cgroup mounts) but **do not share programs**: networking datapath programs and security hook programs are loaded independently. Capacity planning must account for combined map memory, CPU at high PPS, and event export volume. The [Cilium component overview](https://docs.cilium.io/en/stable/overview/component-overview/) separates the per-node agent (datapath + policy + Hubble observer) from cluster-level operator concerns; Tetragon's agent similarly loads hooks locally while optional operators manage CRDs.

**Privilege and cgroup mounts:** Cilium's kube-proxy-free install may auto-mount cgroup v2 under `/run/cilium/cgroupv2` for socket-LB attachment. Tetragon requires sufficient capability to load tracing and enforcement programs. Conflicts are rare but show up as agent CrashLoopBackOff on nodes with hardened seccomp or AppArmor profiles that block `bpf()` syscalls. Standardize a **node profile** that allows verified BPF loaders for both products rather than approving them independently.

**Event volume discipline:** Hubble can generate rich per-flow records. Tetragon can generate per-syscall or per-hook events. Enabling both at maximum verbosity on high-churn nodes can starve disk and CPU even when the kernel keeps forwarding packets. Use Hubble's drop-only filters for steady-state monitoring. Use Tetragon `Post` and narrow selectors before exporting everything to Kafka. The kernel cost of a dropped packet is paid once; the observability cost of logging every allowed flow is paid for every packet you choose to record.

**Defense in depth without double kills:** Module 4.5 positions Tetragon alongside Falco. At the kernel layer, avoid two enforcement products attaching to the same syscall with conflicting actions unless you have a documented precedence model. A Falco alert plus a Tetragon `Sigkill` on the same behavior creates operator confusion about which system "owned" the kill. Prefer Falco or Tetragon for enforcement per event class, not both, unless one is strictly observe-only.

**Upgrade ordering:** Upgrade Cilium and Tetragon on a canary node pool before the fleet. Kernel upgrades require revalidation of both stacks because BTF and hook availability change together. After kernel bumps, run `cilium-dbg status` and `tetra probes` on the canary before promoting. Document minimum kernel versions from both products' release notes in the same matrix row so platform tickets do not cite only one vendor's compatibility table.

**Identity-aware security meets identity-aware networking:** Cilium's security identity for a pod is the same conceptual object policy uses for allow/deny. Tetragon can filter on Kubernetes namespace and labels in selectors. Align naming in runbooks: "identity 48291" in Hubble is the same class of label-derived ID discussed in 5.1. Tetragon events should include Kubernetes metadata when the agent has API access — correlate a Tetragon `sched_process_exec` event with a Hubble drop on the same pod by UID/namespace rather than only by IP after NAT.

**When not to combine features on day one:** Teams new to eBPF should not enable kube-proxy replacement, Cluster Mesh, L7 policy, WireGuard encryption, and Tetragon `Sigkill` enforcement in one change window. Each feature adds map state and failure modes. Sequence learning: observe with Hubble and Tetragon `Post`, stabilize networking replacement, then tighten security enforcement, then add L7 policy only where HTTP semantics require it.

---

## Part 6: Migration Playbook — kube-proxy Replacement on kind

Use a lab cluster only. Production migrations need change windows, connection draining, and rollback runbooks beyond this exercise.

### Phase 0 — Prerequisites

Use a kind cluster with a recent kernel (5.10+ recommended for full kube-proxy replacement features), install the Cilium CLI locally, and read the warning blocks in [Kubernetes without kube-proxy](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/) about breaking existing connections when removing kube-proxy on live clusters. Greenfield kind labs skip kube-proxy deletion drama; brownfield production clusters must treat the warning as a hard change-window requirement, not boilerplate.

### Phase 0b — Kernel and BTF expectations for both stacks

Cilium and Tetragon both rely on BTF-backed CO-RE style loading for portability across kernel builds. Tetragon LSM hooks additionally require `CONFIG_BPF_LSM=y` and `bpf` in `/sys/kernel/security/lsm` as documented in [Tetragon hook points](https://tetragon.cilium.io/docs/concepts/tracing-policy/hooks/). Before standardizing a node image, verify those config flags on a sample node. Missing BPF LSM does not block Cilium networking, but it blocks `lsmhooks` enforcement policies you may have planned from this module's Tetragon section.

### Phase 1 — Create kube-proxy-free kind cluster and install Cilium

kind must disable the default CNI and kube-proxy before Cilium can own Service datapath programming. Per [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/) and [Cilium kube-proxy-free](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/), set `networking.disableDefaultCNI: true` and `networking.kubeProxyMode: "none"`, then install Cilium with `kubeProxyReplacement=true` and explicit API server reachability (`k8sServiceHost` / `k8sServicePort`) because no kube-proxy programs the `kubernetes` Service.

```bash
cat > kind-ebpf-kpr.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  kubeProxyMode: none
nodes:
- role: control-plane
EOF

kind create cluster --name ebpf-kpr-lab --config kind-ebpf-kpr.yaml

# Control-plane container IP — required when kube-proxy is absent (Cilium agent needs apiserver endpoint)
API_SERVER_IP=$(docker inspect "ebpf-kpr-lab-control-plane" \
  -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

cilium install --version 1.16.0 \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost="${API_SERVER_IP}" \
  --set k8sServicePort=6443

kubectl -n kube-system rollout status ds/cilium --timeout=120s
```

### Phase 2 — Validate kube-proxy-free datapath

```bash
# kube-proxy must not be running on a greenfield lab cluster
kubectl -n kube-system get ds kube-proxy 2>&1 | grep -q NotFound && echo "kube-proxy absent: OK"

kubectl -n kube-system exec ds/cilium -- cilium-dbg status | grep -i KubeProxyReplacement

kubectl -n kube-system exec ds/cilium -- cilium-dbg status --verbose | grep -A2 "KubeProxyReplacement Details"

# On the kind node: no KUBE-SVC iptables chains when replacement is active
docker exec ebpf-kpr-lab-control-plane iptables-save | grep KUBE-SVC || echo "KUBE-SVC chains empty: OK"
```

Expect `KubeProxyReplacement: True`, socket LB details per current Cilium version output, and empty `KUBE-SVC` iptables chains on the node.

### Phase 3 — Service proof

```bash
kubectl create deployment nginx --image=nginx --replicas=2
kubectl expose deployment nginx --port=80 --type=ClusterIP

kubectl -n kube-system exec ds/cilium -- cilium-dbg service list | grep -E "Frontend|nginx"

kubectl run curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s -o /dev/null -w "%{http_code}\n" http://nginx.default.svc.cluster.local
```

### Phase 4 — Brownfield sequence (reference only)

On an **existing** cluster already running kube-proxy:

1. Install/upgrade Cilium with `kubeProxyReplacement=true` but expect parallel NAT hazard until kube-proxy is removed.
2. Schedule maintenance: drain workloads or accept brief disruption.
3. Delete `kube-proxy` DaemonSet and ConfigMap per Cilium docs; run documented `iptables-save | grep -v KUBE | iptables-restore` cleanup on nodes.
4. Validate `cilium-dbg service list` and application probes.
5. **Rollback:** reinstall kube-proxy from your distribution manifests, disable `kubeProxyReplacement`, restart Cilium — plan this before cutover.

### Phase 5 — Measure (no fabricated benchmarks)

Record **your** before/after: `iptables-save | wc -l`, Service update latency from control plane logs, and connection error rate during Endpoint churn tests. Store results in your internal runbook; do not paste marketing multipliers without a cited benchmark run ID.

### Reading `cilium-dbg service list` like a BPF map dump

The kube-proxy-free guide's NodePort example shows multiple frontend rows for one Service: a ClusterIP frontend, a `0.0.0.0:NodePort` frontend, and per-device IP rows for each node interface that participates in NodePort. Each row lists backend IDs and backend IP:port tuples. When debugging, compare the frontend you think clients use against the backends Kubernetes reports in `kubectl get endpoints`. A correct programming with zero backends means Kubernetes Endpoints are empty, not that BPF is broken. Multiple NodePort frontends exist because external clients may enter via different node IPs; missing device rows after enabling a secondary NIC is the classic "works on node A, fails on node B" symptom tied to `devices` Helm configuration. Teach on-call engineers to screenshot `service list` and Hubble drops together — the frontend/backend section is the kube-proxy replacement equivalent of `iptables-save | grep KUBE-SVC`, and it should be the first attachment to incident tickets after kube-proxy removal.

### Phase 6 — Lab cleanup

```bash
kind delete cluster --name ebpf-kpr-lab
```

Deleting the kind cluster avoids stale kubeconfig contexts. If you installed Tetragon only for this lab, remove the Helm release before reusing the cluster name so CRDs and agents do not collide with a future Cilium-only exercise.

### Troubleshooting decision tree (datapath vs policy)

When Service connectivity fails after enabling kube-proxy replacement, walk this order before rolling back: confirm `KubeProxyReplacement: True` on the affected node; confirm the Service frontend exists in `cilium-dbg service list` with expected backends; curl the ClusterIP from a pod on the same node and a remote node; if only NodePort fails, inspect **devices** and SNAT/DSR mode in verbose status; if only some pods fail, compare **security identities** and Hubble `policy-verdict` rather than restarting kube-proxy (which should already be absent). When Tetragon appears to "do nothing," verify BPF LSM is enabled for `lsmhooks`, confirm the policy domain (`kubectl` vs static file) with `tetra tracingpolicy domains`, and ensure you are not comparing `Post` events to `Sigkill` expectations.

### Production cutover checklist (brownfield)

Document these steps in your change ticket before execution: backup current kube-proxy manifests; record baseline `iptables-save | wc -l` and a sample `iptables-save | grep KUBE-SVC` line count; enable Cilium kube-proxy replacement in Helm with `k8sServiceHost` and `k8sServicePort` set correctly for kubeadm clusters without kube-proxy (per guide); roll Cilium DaemonSet; delete kube-proxy DaemonSet and ConfigMap during the window; run per-node iptables cleanup from the guide; validate `cilium-dbg service list` for critical Services; run application synthetic probes; watch Hubble drop counters for policy surprises; keep rollback artifacts (kube-proxy YAML, prior Cilium Helm values) for 24 hours. Post-cutover, remove obsolete runbooks that reference `iptables-save` as the first Service debug step — your first hop is BPF maps and Hubble.

---

## Did You Know?

- **Cilium's BPF architecture guide** states XDP runs at the earliest driver receive point while tc runs later with richer metadata — the product uses both layers rather than picking a single hook for every feature ([BPF architecture](https://docs.cilium.io/en/stable/reference-guides/bpf/architecture/)).
- **kube-proxy replacement** in Cilium depends on socket-LB and can expose per-node **XDP Acceleration** state in `cilium-dbg status --verbose`, which is distinct from "Cilium installed" alone ([kube-proxy-free](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/)).
- **Tetragon documents TOCTOU** risk for syscall kprobes and recommends LSM `security_*` hooks when enforcement must see kernel-resident objects ([hook points](https://tetragon.cilium.io/docs/concepts/tracing-policy/hooks/)).
- **Maglev consistent hashing** for Cilium's BPF load balancer is optional and uses prime-sized lookup tables per Service — changing table size triggers agent restarts and temporary backend selection drift ([Maglev section](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/#maglev-consistent-hashing)).

The four items above are not trivia for certification exams; they are the questions senior engineers ask when deciding whether a production incident is datapath programming, policy identity, hook stability, or load-balancer algorithm configuration. Keep them in runbooks adjacent to links to 5.1 and 4.5 for Helm and CRD syntax so operators do not conflate mechanism with installation procedure. When a vendor blog cites a large performance multiplier without linking a reproducible benchmark configuration, treat it as marketing until your team reproduces the measurement on your node SKU, kernel version, Cilium build, Tetragon build, node count, concurrency profile, packet size distribution, protocol mix, and traffic mix.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Enabling kube-proxy replacement without removing kube-proxy on live clusters | Split NAT tables; broken existing connections per Cilium docs | Follow documented delete/cleanup sequence in a maintenance window |
| Debugging drops with only `iptables -L` | Cilium verdicts live in BPF maps and Hubble, not kube-proxy chains | `hubble observe --verdict DROPPED` + `cilium bpf policy` / CT map dumps |
| Applying L7 policy for port-only needs | Unnecessary Envoy redirection; surprise drops on `/metrics` | Enforce L4 in BPF; add L7 only for HTTP semantics |
| `Sigkill` on syscall kprobe with user pointer paths | TOCTOU bypass or false kills | Prefer LSM hooks or later kernel functions per Tetragon docs |
| Assuming XDP handles all pod policy | Most pod policy is tc/socket, not only XDP | Read `cilium-dbg status --verbose` for XDP acceleration scope |
| Treating CT issues as only Linux conntrack | Cilium CT map state can diverge | Inspect BPF CT maps; see 1.1 issue #11742 pattern |
| Quoting uncited "10x faster" in designs | Unverifiable SLO claims | Cite specific benchmark or measure locally |
| Skipping `devices` for NodePort on multi-NIC nodes | External traffic misses BPF LB device binding | Align `devices` with interfaces receiving NodePort traffic (5.1 quiz) |

---

## Quiz

1. **Why does Cilium attach BPF programs at both tc and socket levels instead of only XDP?**

   <details>
   <summary>Answer</summary>
   XDP runs earliest with minimal metadata — excellent for early drop/acceleration but insufficient context for many pod identity and socket-associated decisions. tc programs see richer `skb` context for forwarding, NAT, and policy. Socket-level hooks tie decisions to workload sockets for connect/bind policy and socket LB used by kube-proxy replacement. The pipeline combines hook strengths rather than forcing one attachment point.

   </details>

2. **What changes in the kernel when kube-proxy replacement is active versus iptables kube-proxy?**

   <details>
   <summary>Answer</summary>
   iptables kube-proxy installs and periodically rewrites `KUBE-*` netfilter chains per Service/Endpoint. Cilium programs BPF service maps probed on packet/socket paths for VIP→backend translation. Updates target map entries rather than full iptables restores, addressing rule explosion and update latency described in Kubernetes and Cilium documentation — without assuming a specific numeric speedup unless measured.

   </details>

3. **When should L7 policy live in Envoy instead of BPF tc programs?**

   <details>
   <summary>Answer</summary>
   When the decision requires application-layer fields (HTTP method, path, headers, gRPC metadata). BPF excels at L3/L4 and identity-based port policy. L7 rules need parsing beyond cheap per-packet BPF work, so Cilium redirects matching flows to Envoy per Layer 7 policy docs. Port-only restrictions should stay in BPF.

   </details>

4. **Why does Tetragon document TOCTOU risk for syscall kprobes but recommend LSM hooks for enforcement?**

   <details>
   <summary>Answer</summary>
   Syscall kprobes may read user-space pointers before the kernel copies data into kernel memory; an attacker can mutate that memory after the probe. LSM `security_*` hooks run on kernel-resident structures (e.g., resolved files), closing that race for enforcement decisions.

   </details>

5. **What is the operational difference between Tetragon `Post` and `Sigkill` actions?**

   <details>
   <summary>Answer</summary>
   `Post` emits events without terminating the workload — suitable for staging policies. `Sigkill` triggers synchronous kernel-level process termination (typically exit 137) when selectors match, but per [Tetragon enforcement](https://tetragon.io/docs/concepts/enforcement/) it does not always prevent the triggering syscall side effect — combine with `Override` or use LSM hooks for true deny-before-completion. Falco-style userspace alerting reacts after the fact; Tetragon kill is faster but not equivalent to MAC-style LSM deny.

   </details>

6. **You enabled kube-proxy replacement but NodePort from outside the cluster fails intermittently. Pod-to-pod works. Name two configuration areas to inspect first.**

   <details>
   <summary>Answer</summary>
   Check `cilium-dbg status` for which **devices** participate in kube-proxy replacement and NodePort handling — multi-NIC clusters often need explicit `devices` alignment. Check load-balancer mode (SNAT vs DSR) and whether return paths or cloud source/destination checks break DSR. These are explicit BPF LB binding issues, not generic "Cilium broken" failures.

   </details>

7. **How do identity-based policy lookups differ from labeling pods by IP in iptables rules?**

   <details>
   <summary>Answer</summary>
   Cilium assigns a numeric security identity to label sets and programs policy maps keyed by identity pairs. Scaling replicas with the same labels reuses one identity instead of adding per-pod IP rules. iptables kube-proxy/network plugins without identity still scale IP/port rules linearly with endpoints.

   </details>

8. **Why must kube-proxy be removed carefully during migration, per Cilium warnings?**

   <details>
   <summary>Answer</summary>
   Parallel kube-proxy and eBPF replacement maintain independent NAT/state tables. Existing flows can break because neither side is aware of the other's translations. Migration requires a controlled cutover (delete kube-proxy, cleanup residual iptables rules, validate BPF services), not leaving both active on serving nodes.

   </details>

---

## Hands-On Exercise: Observe LB Maps and a Staged Tetragon Policy

**Task:** Correlate Cilium service map entries with kube-proxy replacement status, then deploy an observe-only Tetragon policy before any `Sigkill` policy. Work through the numbered steps below on a disposable kind cluster, then run the verification commands and check off the success criteria when each outcome is proven.

1. Complete Part 6 Phases 1–3 on kind.
2. Run `kubectl -n kube-system exec ds/cilium -- cilium-dbg bpf lb list` (command name may vary slightly by version; use `cilium-dbg bpf -h` if subcommand differs).
3. Scale `nginx` to three replicas; re-run `cilium-dbg service list` and note backend count change without `iptables-save` growth for `KUBE-SVC`.
4. Install Tetragon: `helm repo add cilium https://helm.cilium.io/ && helm install tetragon cilium/tetragon -n kube-system`
5. Apply this observe-only `sched_process_exec` tracepoint policy (from [Tetragon hooks](https://tetragon.cilium.io/docs/concepts/tracing-policy/hooks/)):

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: lab-exec-observe
spec:
  tracepoints:
    - subsystem: sched
      event: sched_process_exec
      raw: true
      args:
        - index: 2
          type: linux_binprm
      selectors:
        - matchActions:
            - action: Post
```

```bash
cat <<'EOF' > lab-exec-observe.yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: lab-exec-observe
spec:
  tracepoints:
    - subsystem: sched
      event: sched_process_exec
      raw: true
      args:
        - index: 2
          type: linux_binprm
      selectors:
        - matchActions:
            - action: Post
EOF
kubectl apply -f lab-exec-observe.yaml
kubectl run exec-probe --rm -it --restart=Never --image=busybox:1.36 -- /bin/true
kubectl exec -n kube-system ds/tetragon -c tetragon -- tetra getevents -o compact | grep sched_process_exec | head
```
6. Document in three sentences: where Service VIP translation happened (userspace agent → BPF map), and why you used `Post` before `Sigkill`.

Run verification commands after the steps complete:

```bash
kubectl -n kube-system exec ds/cilium -- cilium-dbg status | grep -E "KubeProxyReplacement|Socket"
kubectl -n kube-system exec ds/tetragon -c tetragon -- tetra probes | head -20
```

After the lab, write a short internal note comparing one iptables-era debugging habit you will stop using and one BPF-era command you will default to instead. Examples: replace "grep KUBE-SVC first" with "`cilium-dbg service list` first"; replace "tcpdump before policy identity" with "Hubble `policy-verdict` before tcpdump." The note is complete when another engineer could follow it without reading this module.

Mark the lab complete when all of the following are true:

- [ ] `KubeProxyReplacement: True` on all nodes in the lab cluster.
- [ ] `cilium-dbg service list` shows ClusterIP frontend for the test nginx Service.
- [ ] In-cluster curl to the Service VIP returns HTTP 200.
- [ ] You can explain one reason parallel kube-proxy and Cilium replacement is unsafe on serving clusters.
- [ ] Tetragon emits at least one `sched_process_exec` event in `Post` mode before enabling `Sigkill`.

---

## Next Module

Continue to toolkit operations: [Cilium 5.1](/platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/) for Hubble-first debugging and policy authoring, [Tetragon 4.5](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/) for TracingPolicy catalogs, [Advanced Cilium](/k8s/cca/module-1.1-advanced-cilium/) for certification-depth topics, and [Hubble](/platform/toolkits/observability-intelligence/observability/module-1.7-hubble/) for flow observability. Revisit [eBPF Fundamentals](module-1.1-ebpf-fundamentals/) when you need verifier, CO-RE, or map-pressure vocabulary that applies to any BPF workload, not only Cilium and Tetragon.

---

## Sources

- [Cilium BPF architecture](https://docs.cilium.io/en/stable/reference-guides/bpf/architecture/) — tc/XDP roles, maps, tail calls
- [Cilium terminology](https://docs.cilium.io/en/stable/overview/intro/terminology/) — security identity model
- [Kubernetes without kube-proxy](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/) — socket LB, migration warnings, Maglev/DSR, validation commands
- [Cilium Layer 7 policy](https://docs.cilium.io/en/stable/security/policy/layer7/) — Envoy redirection for HTTP policy
- [Cilium component overview](https://docs.cilium.io/en/stable/overview/component-overview/) — agent, operator, datapath division
- [Kubernetes blog: nftables kube-proxy](https://kubernetes.io/blog/2025/02/28/nftables-kube-proxy/) — iptables rule scaling and lookup cost
- [Cilium issue #11742](https://github.com/cilium/cilium/issues/11742) — BPF CT map pressure example
- [Tetragon TracingPolicy concepts](https://tetragon.cilium.io/docs/concepts/tracing-policy/) — policy model and enforcement mode
- [Tetragon hook points](https://tetragon.cilium.io/docs/concepts/tracing-policy/hooks/) — kprobes, tracepoints, LSM BPF, TOCTOU guidance
- [Tetragon enforcement](https://tetragon.io/docs/concepts/enforcement/) — `Override` vs signal/SIGKILL; signal does not always stop the triggering operation
- [kind cluster configuration](https://kind.sigs.k8s.io/docs/user/configuration/) — `disableDefaultCNI`, `kubeProxyMode: none`
- [eBPF tcx program type reference](https://docs.ebpf.io/linux/program-type/BPF_PROG_TYPE_SCHED_CLS/) — tc attachment evolution
- Liz Rice, *Learning eBPF* (O'Reilly) — hook and map mental models for deeper study
