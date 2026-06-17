---
revision_pending: false
title: "Module 5.3: DNS Deep Dive"
slug: platform/toolkits/infrastructure-networking/networking/module-5.3-dns-deep-dive
sidebar:
  order: 4
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 75-90 minutes
>
> **Track**: Toolkits

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Trace** a pod DNS lookup from application code through the pod resolver, CoreDNS, recursive resolvers, and authoritative DNS.
- **Configure** CoreDNS safely by reading the Corefile, choosing the right plugin behavior, and separating cluster DNS from conditional forwarding.
- **Explain** how Kubernetes Service DNS names, headless Services, Pod DNS, `dnsPolicy`, `dnsConfig`, search domains, and `ndots` work together.
- **Diagnose** DNS latency and failure signatures with `dig`, `nslookup`, CoreDNS logs, Prometheus metrics, and NodeLocal DNSCache reasoning.
- **Design** external DNS integration using split-horizon DNS, conditional forwarding, and ExternalDNS without giving Kubernetes more authority than intended.

## Why This Module Matters

Hypothetical scenario: a checkout service calls three internal APIs and one external payment endpoint on every request. The application code is ordinary, the network path is healthy, and the database is not slow, yet the user-facing request sometimes stalls before any HTTP connection opens. A packet capture shows repeated DNS questions for names that will never exist, followed by the one answer the application actually needed. The incident is not a packet-routing mystery; it is a resolver policy mystery.

Kubernetes makes service discovery feel simple because a pod can call `orders` and receive an address for a Service in the same namespace. That convenience hides a layered system: the application library calls the libc or language resolver, the resolver reads `/etc/resolv.conf`, the query reaches CoreDNS, CoreDNS decides whether the name belongs to the cluster, and anything outside the cluster is forwarded toward recursive DNS. A platform engineer who treats this as one black box will miss the difference between a broken Service, a slow upstream resolver, an expensive search path, and an overloaded cluster DNS deployment.

The useful mental model is a post office with several sorting desks. The pod resolver is the local clerk that decides whether the name is already complete or needs local suffixes attached. CoreDNS is the campus mailroom that knows every Kubernetes Service and Pod naming rule. Recursive resolvers are the regional sorting centers that know how to ask the public DNS hierarchy. Authoritative servers are the final offices that own a zone and can answer for it. A delay at any desk looks like "DNS is slow" unless you know which desk handled the envelope.

This module matters because DNS sits before almost every network connection. A single missing `fallthrough`, a forwarding loop, an over-broad search list, or a saturated CoreDNS cache can make healthy services appear unreliable. The goal is not to memorize every CoreDNS plugin. The goal is to know how Kubernetes DNS is assembled, how to reason from a symptom to the layer that produced it, and how to make DNS changes that are specific enough to solve the problem without turning the cluster resolver into an accidental global DNS authority.

## DNS Fundamentals Before Kubernetes

DNS begins with a question from a stub resolver. In a container, the stub resolver is usually part of the application runtime or the C library that the runtime calls. It does not know the whole DNS tree. It reads a small resolver configuration, chooses a nameserver, applies options such as search domains and `ndots`, and sends a query for a record type. That small decision point is why Kubernetes DNS behavior can change without touching CoreDNS: the pod may ask a different question before CoreDNS ever sees anything.

A recursive resolver does the wider work. If it has no fresh cached answer, it walks the hierarchy by asking root servers, then top-level-domain servers, then the authoritative servers for the zone that owns the name. Those upstream steps are usually iterative from the recursive resolver's perspective: each authoritative layer gives a delegation or an answer, and the recursive resolver continues until it has enough information to respond to the original client. The pod does not perform that full walk; it delegates the hard work to the recursive resolver reached through CoreDNS or the node resolver.

Authoritative DNS is different from recursive DNS because authority is about ownership, not effort. An authoritative server for `example.com` can answer for records in that zone because the parent zone delegated authority to it. A recursive resolver may know the answer only because it looked it up earlier and cached it. This distinction matters in Kubernetes when CoreDNS serves `cluster.local`: for cluster names, CoreDNS is authoritative from the pod's point of view because it is the component that knows the Kubernetes API objects behind those names. For public names, CoreDNS is usually a forwarder toward recursive infrastructure.

Record types are the vocabulary of that conversation. `A` records map names to IPv4 addresses, while `AAAA` records map names to IPv6 addresses. `CNAME` records make one name an alias for another name, and clients must follow the target to find address records. `SRV` records describe a named service endpoint with a port and protocol, which is especially useful for headless Services and named ports. `PTR` records support reverse lookups, `TXT` records carry text metadata used by ownership and verification systems, and `NS` records identify the nameservers that are authoritative for a zone.

Caching is DNS's performance bargain. Every positive answer carries a TTL, and a resolver may reuse that answer until the TTL expires. Negative answers can also be cached, which means a temporary missing name can remain missing for clients even after the record appears. TTL is not a propagation timer and it is not an invalidation guarantee. It is a maximum age that cooperative caches should respect. In a cluster, short TTLs make changes visible sooner but increase query volume, while long TTLs reduce query volume but make endpoint or external-record changes linger longer.

Kubernetes adds a second kind of dynamism on top of DNS TTLs. Services, EndpointSlices, Pods, and namespaces can change faster than traditional DNS zones. CoreDNS watches the Kubernetes API and answers from that live state, but clients and intermediate caches still obey resolver behavior and TTLs. When you debug, keep those two clocks separate: the Kubernetes object may already be correct, while a client cache still holds the previous DNS answer, or the client may be asking a search-expanded name that never corresponds to the object you inspected.

## Kubernetes Cluster DNS Model

Kubernetes standardizes the DNS names that workloads can expect, while the concrete DNS server implementation is typically CoreDNS. A normal Service receives names under the cluster domain, commonly shaped as `<service>.<namespace>.svc.cluster.local`. A pod in the same namespace can often use only `<service>` because its resolver search list appends namespace and cluster suffixes. That convenience is valuable, but it also means a short name is not one query. It is a query plan generated from the pod's resolver configuration.

For a normal ClusterIP Service, DNS returns address records for the Service virtual IP. Clients connect to that stable virtual address, and kube-proxy, eBPF service handling, or the provider dataplane sends traffic to a backend endpoint. The DNS layer does not pick the individual backend pod in that case. It names the Service abstraction. This is why changing endpoints behind a ClusterIP Service does not require clients to rediscover every Pod IP through DNS.

Headless Services behave differently because they have no ClusterIP. When a Service is headless, DNS can return endpoint addresses directly, and clients may see multiple address records for the backing pods. For named ports, DNS can also expose `SRV` records that include the port and target name. This pattern is useful when the client protocol expects to discover individual peers, such as clustered databases or systems that need stable per-pod identities. It is also easier to misuse, because clients must tolerate endpoint churn and multiple answers.

Pod DNS exists, but it should not be your first service discovery primitive. Kubernetes can expose Pod-related names, and StatefulSet pods can receive stable DNS names when combined with a headless Service and predictable hostnames. That does not make arbitrary Pod DNS a replacement for Services. A direct Pod name couples clients to workload placement and lifecycle. Use Service DNS for ordinary application dependencies, and reserve stable per-pod DNS for software that genuinely models peers instead of interchangeable replicas.

The cluster domain is configurable, but `cluster.local` remains the conventional default in many clusters. Platform code should not assume that suffix blindly. Operators sometimes change the domain during bootstrap, and multi-cluster designs may use different domains to avoid ambiguity. A chart, operator, or application that hard-codes `cluster.local` can work in the first cluster and fail in the second. Prefer Kubernetes-provided environment, explicit configuration, or fully documented assumptions when a workload truly needs the complete DNS name.

The important design rule is that Kubernetes DNS describes Kubernetes objects, not every possible enterprise name. CoreDNS can forward, rewrite, and host static records, but the cluster DNS path should stay narrow enough that a mistake does not break unrelated corporate or public DNS. Treat cluster DNS as service discovery for the cluster first, then add carefully scoped forwarding for names that the cluster must reach. If you turn CoreDNS into a general-purpose enterprise resolver, you inherit enterprise DNS blast radius inside every pod.

## CoreDNS Architecture and the Corefile

CoreDNS is a DNS server built around plugins. In Kubernetes, it usually runs as a Deployment in `kube-system`, serves through a Service commonly named `kube-dns`, and reads a ConfigMap that contains a `Corefile`. The `kube-dns` Service name is historical compatibility; the serving pods are commonly CoreDNS pods. That naming mismatch is a source of confusion, so distinguish the Service name from the implementation when you read manifests, dashboards, and incident notes.

The Corefile is not just a text blob. It defines server blocks, the zones those blocks serve, and plugin directives inside each block. A server block such as `.:53` means CoreDNS is listening for DNS on port `53` and can handle the root zone from the perspective of that block. Another block such as `corp.internal:53` can match only a private suffix and forward it to corporate DNS. CoreDNS chooses the most specific matching server block before the configured plugin chain handles the query.

One subtle but important correction: the physical order of plugin lines in the Corefile is not the same thing as execution order. CoreDNS uses the compiled plugin order from its build configuration, while the Corefile decides which plugins are active and how they are configured. You should still keep a conventional, readable Corefile order, because humans maintain it during incidents. Do not rely on moving `cache` above `kubernetes` in the Corefile as if it rewired the runtime pipeline.

A common Kubernetes Corefile has a `kubernetes` block for the cluster domain, a `forward` directive for names outside the cluster, `cache` for reuse, `loop` to detect forwarding loops, `reload` to apply ConfigMap updates, and readiness or health plugins for operational checks. The exact text varies by distribution, managed service, and release. Read the actual ConfigMap before changing behavior. Do not paste a blog Corefile over a managed cluster's Corefile unless you know which provider-specific assumptions you are removing.

```bash
kubectl get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}'
```

The `kubernetes` plugin is the bridge from DNS to the Kubernetes API. It watches Services, EndpointSlices, namespaces, and related objects, then synthesizes answers for cluster names. Options inside that block can control zones, reverse lookup fallthrough, pod record behavior, and TTLs. If Service names fail but public names still resolve, the `kubernetes` plugin path is one of the first places to inspect. If public names fail but Services resolve, the forwarding path is usually more suspicious.

The `forward` plugin sends queries onward when CoreDNS is not authoritative for the name. In a basic cluster, it forwards to nameservers from `/etc/resolv.conf`, which often means the node or cloud provider resolver. In a split DNS cluster, you may add a more specific server block for a private suffix, then forward only that suffix to corporate resolvers. Specificity is the safety valve: forward `corp.internal` to the corporate resolver, not every query, unless CoreDNS is intentionally your only recursive path.

The `cache` plugin reduces repeated work, but caching is not free magic. It can lower load and latency for repeated answers, yet it also makes stale answers possible until TTLs expire. It can cache negative answers too, which is helpful during typo storms but surprising when a just-created name still appears missing. Cache tuning should start from observed query volume, answer churn, and failure mode. Raising TTLs because DNS feels busy can hide a deeper query amplification problem.

The `hosts` and `rewrite` plugins are powerful because they can change answers without changing Kubernetes objects. Use them sparingly. A `hosts` block can provide a small static override, but it needs `fallthrough` if unmatched names should continue to later handling. A `rewrite` rule can help with a controlled migration from one name to another, but it can also hide stale application configuration for months. In platform systems, every rewrite should have an owner, an expiry expectation, and a test that proves it still matters.

The `loop`, `reload`, `health`, and `ready` plugins are operational guardrails. `loop` protects against obvious self-forwarding loops at startup, `reload` lets CoreDNS reload changed configuration, `health` exposes process health, and `ready` reports whether plugins that support readiness are prepared to serve. These plugins do not make a bad DNS design good, but they make failures easier to detect and safer to roll out. Removing them to make a minimal Corefile is rarely worth the loss of visibility.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> CoreDNS is a CNCF Graduated project and is the default cluster DNS implementation used by Kubernetes, replacing kube-dns in that default role. The CoreDNS homepage, CNCF project page, and GitHub release list do not always present volatile release data in the same way; during verification, the GitHub releases page listed `v1.14.4` as latest and also showed `v1.14.3` as an April 22, 2026 release. Commonly documented CoreDNS plugins include `kubernetes`, `forward`, `cache`, `hosts`, `rewrite`, `loop`, `reload`, `health`, `ready`, `prometheus`, `errors`, and `loadbalance`, but the true roster for a running binary is whatever was compiled into that binary.

## Resolution Inside a Pod

Inside a pod, `/etc/resolv.conf` is the map the resolver follows. A typical ClusterFirst pod has a `nameserver` pointing at the cluster DNS Service IP, a `search` line containing namespace and cluster suffixes, and an `options` line containing `ndots:5`. The nameserver tells the resolver where to send questions. The search list tells it which suffixes to append to names that are not treated as complete. The `ndots` value decides when a name is tried as absolute before search expansion.

```text
nameserver 10.96.0.10
search app-team.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

The `ndots:5` default is the classic Kubernetes DNS amplification trap. A name with fewer than five dots is tried through every search domain before the resolver tries the absolute name. If an application asks for `api.example.com`, the resolver may first ask for `api.example.com.app-team.svc.cluster.local`, then `api.example.com.svc.cluster.local`, then `api.example.com.cluster.local`, and only then ask for `api.example.com` as an absolute name. The exact count follows the search list, and separate `A` and `AAAA` lookups can multiply the work further.

This behavior is not a Kubernetes bug. It is a resolver policy chosen to make short in-cluster names convenient. The cost appears when applications make many external calls using names that contain dots but fewer than `ndots`. Each failed search-expanded query consumes client time, CoreDNS work, cache space, and upstream forwarding effort. The safest fix depends on the workload: use a trailing dot for known external fully qualified names, lower `ndots` for pods that mostly call external services, or use complete in-cluster names for cross-namespace dependencies.

`dnsPolicy` controls how Kubernetes builds the pod resolver file. `ClusterFirst` is the normal policy for workloads that should use cluster DNS. `Default` makes the pod inherit DNS settings from the node, which is useful for certain host-oriented workloads but bypasses normal cluster service discovery. `None` lets you specify the resolver configuration through `dnsConfig`, and it should be used only when you are prepared to own every consequence. `ClusterFirstWithHostNet` exists because host-networked pods need an explicit way to keep cluster DNS behavior.

`dnsConfig` is the pod-level override mechanism. You can add searches, nameservers, and options such as `ndots`, but the merge behavior depends on policy and platform limits. Use it like a scalpel. A namespace-wide mutation that changes every pod to `ndots:1` may reduce external query expansion and break workloads that depended on short multi-label internal names. A targeted pod spec or workload class is safer because you can tie the change to a known access pattern.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: external-heavy-client
  namespace: app-team
spec:
  dnsPolicy: ClusterFirst
  dnsConfig:
    options:
      - name: ndots
        value: "2"
  containers:
    - name: client
      image: busybox:1.36
      command: ["sleep", "3600"]
```

Search domains also shape cross-namespace behavior. From a pod in namespace `payments`, the short name `api` first means `api.payments.svc.cluster.local`, not `api.default.svc.cluster.local`. If you want a Service in another namespace, use at least `api.default` or the full `api.default.svc.cluster.local`. This convention is valuable because it keeps local names short, but it can hide mistakes when the same Service name exists in several namespaces and a caller silently reaches the local one.

The trailing dot is the most precise way to say a name is already complete. A resolver query for `api.example.com.` should not receive search suffixes. This is useful in application configuration for stable external dependencies, especially high-volume clients. It is less friendly for humans and some libraries normalize it away, so test the runtime you actually use. The idea is simple: if you know the name is public and complete, do not ask the resolver to guess local alternatives first.

## Service and Pod DNS Records in Practice

A Service DNS record is a contract between the Kubernetes API and clients, but the contract differs by Service type. For a normal ClusterIP Service, clients receive the Service IP and let the dataplane handle backend selection. For a headless Service, clients receive endpoint addresses and must handle multiple answers, changing answers, and failed peers. For an ExternalName Service, Kubernetes returns a `CNAME` to another DNS name rather than creating a cluster IP. Each pattern is valid, but each places different responsibility on clients.

`SRV` records appear when a Service has named ports. A query for a service name plus protocol and port label can return the port number and target host. This is helpful for clients that discover not just "where is the service" but "which port should I use for this named service." For headless Services, SRV targets may identify individual endpoints, which is why StatefulSet and headless-Service combinations are common for software that expects stable peers.

Pod DNS is more specialized. Some clusters expose pod-address-style names under a pod DNS zone, and StatefulSet pods can have stable names when the pod has a hostname and subdomain tied to a headless Service. The reliable platform rule is to decide whether the client needs a service abstraction or a peer identity. If replicas are interchangeable, use a Service. If the software protocol needs a specific peer with durable identity, design the headless Service and StatefulSet naming deliberately.

Reverse DNS and `PTR` records are often overlooked because most application traffic does not need them. They matter for older protocols, audit trails, and some network appliances that perform reverse lookups. CoreDNS can fall through reverse zones such as `in-addr.arpa` and `ip6.arpa` when Kubernetes has no answer. That fallthrough behavior prevents CoreDNS from becoming a dead end for reverse lookups outside the cluster. If reverse lookups fail, inspect both CoreDNS reverse-zone handling and upstream resolver authority.

ExternalName Services deserve special caution. They create a Kubernetes object that returns a `CNAME` to an external name, but they do not provide a proxy, health check, TLS policy, or traffic control by themselves. They are a naming convenience, not a service mesh and not a load balancer. They can be useful for migration or abstraction, but they can also confuse clients that do not expect a CNAME chain or that use the original hostname for TLS verification.

## Performance and Scale

DNS becomes a cluster latency source because it sits on the critical path before connections. It also concentrates demand: every pod can ask the same small set of CoreDNS pods for answers. A busy workload rollout, a batch job wave, or a retry storm can create a synchronized spike. If most of those queries are search-expanded misses, CoreDNS spends resources proving that many names do not exist. Caching helps, but a cache is less effective when the workload generates a large variety of unique failed names.

The first performance lever is query shape. Before scaling CoreDNS, look at whether clients are asking avoidable questions. External names without trailing dots, high `ndots`, long search lists, and libraries that resolve on every request all increase load. A pod that opens a new connection for every operation may also resolve more often than a client that pools connections. Platform teams should measure DNS request rate by zone, response code, and client workload before assuming more replicas are the answer.

The second lever is cache behavior. CoreDNS cache settings influence how often repeated answers are served locally. Positive caching reduces repeated successful lookups. Negative caching reduces repeated misses. Prefetch-like behavior can keep hot records warm in some configurations. The tradeoff is staleness and memory. A cache tuned for stable external dependencies may not fit a fast-changing headless Service. Treat cache changes as operational changes with rollback plans, not as harmless performance toggles.

The third lever is topology. If a pod on one node must send every DNS query across the overlay to a CoreDNS pod on another node, even a healthy cluster adds network hops and conntrack work. CoreDNS replicas spread across nodes can help, but Kubernetes Service routing may still send traffic across nodes. Topology-aware routing and provider dataplanes can improve this, yet they do not remove every node-local bottleneck. This is where NodeLocal DNSCache becomes important.

NodeLocal DNSCache runs a lightweight DNS caching agent on each node as a DaemonSet and listens on a link-local address. Pods still use familiar DNS behavior, but queries can hit the local agent before reaching the central CoreDNS Service. Cache hits avoid a network hop. Cache misses can be forwarded to cluster DNS or upstream resolvers according to configuration. The local agent also gives operators node-level DNS metrics, which is valuable when one node or one workload causes a query storm.

The deeper reason NodeLocal DNSCache exists is not only "local cache is faster." It also reduces exposure to UDP conntrack and DNAT races on busy nodes. In the classic path, a pod sends UDP DNS to the kube-dns Service IP, kube-proxy translates that virtual IP to an endpoint, and conntrack tracks the flow. Under pressure, races and dropped UDP responses can create long tail latency, often seen as roughly five-second lookup stalls when clients wait and retry. NodeLocal DNSCache avoids that path for local DNS handling and uses iptables `NOTRACK` rules so selected DNS traffic skips connection tracking.

This does not make NodeLocal DNSCache a universal button. It adds a DaemonSet, node-level iptables behavior, and another CoreDNS-like configuration surface. You need to account for host networking, provider dataplanes, eBPF modes, dual-stack clusters, and managed-service support. The right question is not "is NodeLocal always faster?" The right question is "does our cluster show DNS query volume, tail latency, conntrack pressure, or cross-node DNS traffic that a node-local cache would directly address?"

Autopath is another optimization, but it solves a different part of the problem. The CoreDNS autopath plugin can reduce client-side search path expansion by helping the server answer with knowledge of the pod's namespace search path. That can reduce repeated search queries for names that ultimately map to a later suffix. It also increases coupling between DNS answers and pod metadata, so it needs careful testing, observability, and compatibility checks. Use autopath when you have measured search expansion and understand its operational constraints.

## Troubleshooting DNS Failures

Good DNS troubleshooting starts inside the failing pod or a debug pod in the same namespace. The resolver file tells you what question the client is likely to ask, and `dig` or `nslookup` tells you whether the DNS path can answer that question. Do not start by editing CoreDNS. First prove whether the short name, fully qualified Service name, external name, and nameserver all behave as expected from the same network and namespace context as the application.

```bash
kubectl run dns-tools \
  --image=ghcr.io/nicolaka/netshoot:latest \
  --restart=Never \
  -- sleep 3600

kubectl wait --for=condition=Ready pod/dns-tools --timeout=120s
kubectl exec dns-tools -- cat /etc/resolv.conf
kubectl exec dns-tools -- nslookup kubernetes.default.svc.cluster.local
kubectl exec dns-tools -- dig +search +tries=1 +timeout=2 kubernetes.default.svc.cluster.local A
kubectl delete pod dns-tools --now
```

When a short Service name fails, test the fully qualified Service name next. If the FQDN works and the short name fails, the problem is search path or namespace expectation. If neither works, inspect the Service, EndpointSlices, and CoreDNS logs. If cluster names work but external names fail, inspect the `forward` path and upstream reachability. If external names work from nodes but not pods, inspect NetworkPolicy, egress policy, or CoreDNS-to-upstream connectivity.

CoreDNS logs can be useful, but logging every query in a busy cluster can create its own load and noise. Prefer targeted logging during a short window or in a temporary reproduction cluster when possible. Error logs, reload messages, readiness failures, and loop detection messages are higher-signal than raw query logs. If you need query-level evidence, decide in advance what name, namespace, and time window you are trying to catch, then turn logging back down after the capture.

Prometheus metrics are the long-term view. Query request rates show load, response codes show whether failures are `NXDOMAIN`, `SERVFAIL`, or timeouts, and duration histograms show tail behavior. Cache hit and miss metrics show whether the cache is helping or merely observing a stream of unique misses. Segment metrics by server, zone, and response code where labels allow it. An alert on CoreDNS pod restarts alone will miss the more common failure mode: CoreDNS is running, but resolution quality is degrading.

```promql
rate(coredns_dns_requests_total[5m])
rate(coredns_dns_responses_total{rcode="SERVFAIL"}[5m])
rate(coredns_dns_responses_total{rcode="NXDOMAIN"}[5m])
histogram_quantile(0.99, rate(coredns_dns_request_duration_seconds_bucket[5m]))
coredns_cache_hits_total / (coredns_cache_hits_total + coredns_cache_misses_total)
```

Failure signatures often point to the layer. `NXDOMAIN` for a short name may be a namespace or search-path mistake. `SERVFAIL` for all external names often points at forwarding, upstream resolver health, or a loop. Intermittent multi-second stalls under load suggest UDP loss, conntrack pressure, overloaded CoreDNS pods, or search amplification. A name that works in one namespace and not another usually means the caller relied on short-name search behavior rather than a fully qualified Service name.

Be careful with "DNS works on the node" as proof. Node resolution may use the node's own resolver, while pods use cluster DNS. Host-networked pods may follow different policy from ordinary pods. A debug pod in the wrong namespace can hide search-list problems. A `dig` command that asks the full name directly can hide application behavior that asks a short name first. A rigorous test reproduces the pod policy, namespace, resolver options, and exact queried name.

## External Integration: Conditional Forwarding, Split Horizon, and ExternalDNS

Kubernetes clusters rarely live alone. Workloads may need private corporate names, cloud-provider internal names, public SaaS names, and names created from Kubernetes Ingress or Gateway resources. The platform decision is where each name should be owned. Cluster-local names belong in Kubernetes DNS. Corporate private zones usually belong in existing enterprise DNS. Public application names usually belong in an external authoritative provider. CoreDNS can connect these worlds, but it should not blur ownership boundaries.

Conditional forwarding, sometimes called stub-domain behavior in Kubernetes docs, sends a specific suffix to a specific upstream resolver. A Corefile block for `corp.internal` can forward that suffix to corporate DNS while leaving cluster names and public names on their normal paths. This is split-horizon DNS when the answer differs depending on whether the client is inside or outside a network boundary. The security and reliability point is scope: send only the suffix that needs special handling to the special resolver.

```text
corp.internal:53 {
    errors
    cache 60
    forward . 10.0.0.53 10.0.0.54
}
```

Split horizon creates debugging work because the same name can have different answers from different locations. That is sometimes exactly what you want. Internal clients may resolve a private address, while public clients resolve a public address. The danger appears when engineers compare answers from a laptop, a node, a pod, and a CI runner without realizing they are in different DNS views. Document the intended view for each suffix, and include a debug command that queries from inside the cluster.

ExternalDNS solves a different problem. It watches Kubernetes resources such as Services, Ingresses, and Gateway-related resources, then creates or updates DNS records in an external provider according to configuration and annotations. This is useful because the load balancer address or ingress target often becomes known only after the Kubernetes resource is created. ExternalDNS turns that event into DNS provider state, but the provider remains authoritative. Kubernetes is the source of desired records; it is not serving the public zone itself.

The key ExternalDNS safety settings are domain scope, ownership registry, and deletion policy. Domain filters keep the controller away from zones it should not manage. TXT ownership records let multiple controllers or clusters avoid fighting over the same names. An upsert-only policy can prevent accidental deletion when you are first adopting the controller, while a sync policy can clean up stale records once ownership boundaries are proven. These are governance choices, not just Helm values.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: public-api
  namespace: app-team
  annotations:
    external-dns.alpha.kubernetes.io/hostname: api.example.com
    external-dns.alpha.kubernetes.io/ttl: "120"
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: public-api
```

The durable principle is to align DNS authority with operational authority. If the platform team owns cluster service discovery, CoreDNS should answer cluster names. If the network team owns corporate zones, CoreDNS should forward those suffixes rather than copy records. If application teams own public hostnames through Kubernetes resources, ExternalDNS can automate provider records within a narrow domain filter. The worst design is an undocumented mix where the same name can be rewritten, forwarded, cached, and externally managed by different teams.

## Patterns & Anti-Patterns

The strongest DNS platforms share a small number of habits. They keep cluster-local naming boring, make exceptions explicit, measure query behavior before changing resolver policy, and document ownership for each suffix. None of those habits requires an exotic tool. They require treating DNS as a production dependency rather than a bootstrap detail that disappears after the cluster comes up.

| Pattern | Why It Works | Example |
|---------|--------------|---------|
| Use fully qualified Service names for cross-namespace dependencies | It avoids accidental resolution to the caller's namespace and makes ownership clear | `payments.api.svc.cluster.local` instead of `payments` |
| Scope conditional forwarding by suffix | It sends only the private zone to private resolvers and keeps public lookup behavior ordinary | Forward `corp.internal` instead of forwarding `.` |
| Measure search expansion before changing `ndots` | It separates real query amplification from guesses and avoids breaking local-name expectations | Compare `dig +search` output with CoreDNS metrics |
| Treat CoreDNS changes as platform releases | It forces review, rollback, and observability for a shared dependency | Test Corefile changes in staging before production |

Anti-patterns usually come from making DNS convenient for one workload by making it ambiguous for every workload. A rewrite that helps one migration can become permanent hidden coupling. A global `dnsConfig` mutation can reduce one latency symptom and surprise another application. A broad ExternalDNS domain filter can turn an application annotation into public DNS authority. DNS feels small because records are small, but the blast radius is large because every caller trusts the same naming layer.

| Anti-Pattern | Why It Fails | Better Approach |
|--------------|--------------|-----------------|
| Using CoreDNS as the catch-all enterprise resolver | Cluster DNS inherits unrelated corporate resolver failures and policy disputes | Forward only required private suffixes |
| Lowering `ndots` everywhere without workload analysis | Short internal names and multi-label service assumptions can change behavior | Apply targeted pod `dnsConfig` where access patterns justify it |
| Hiding migrations with permanent `rewrite` rules | Applications never update their real configuration and future operators miss the dependency | Use time-bound rewrites with owners and removal dates |
| Running ExternalDNS with broad zone authority on day one | Misannotations or controller bugs can affect unrelated records | Start with domain filters, TXT ownership, and conservative policy |

Use a simple decision framework when you change DNS. First, identify the name category: cluster Service, stable pod peer, private enterprise suffix, public application hostname, or external dependency. Second, identify the authority: Kubernetes API, corporate DNS, public DNS provider, or application configuration. Third, choose the narrowest mechanism that connects the two: Service DNS, headless Service, conditional forwarding, trailing-dot FQDN, pod `dnsConfig`, NodeLocal DNSCache, or ExternalDNS. Fourth, write the rollback before you apply the change, because DNS failures tend to look like every application failed at once.

| Decision | Choose This When | Avoid This When |
|----------|------------------|-----------------|
| Service DNS | Replicas are interchangeable behind a Kubernetes Service | Clients need stable peer identity |
| Headless Service | Clients must discover individual peers or named ports | Clients cannot handle endpoint churn |
| Pod `dnsConfig` | One workload has a known resolver access pattern | You are trying to fix the whole cluster without data |
| NodeLocal DNSCache | You see DNS load, tail latency, conntrack pressure, or cross-node DNS paths | Your provider dataplane or operations model cannot support it safely |
| ExternalDNS | Kubernetes resources should drive external provider records in a controlled zone | The zone contains records Kubernetes must never own |

## Did You Know?

- **CoreDNS still often hides behind the `kube-dns` Service name.** Many clusters keep that Service name for compatibility, so dashboards and commands may say `kube-dns` even when the backing pods run CoreDNS.
- **A trailing dot changes resolver behavior.** `api.example.com.` tells the resolver the name is already absolute, which can bypass search-domain expansion for external names when the application preserves the dot.
- **A headless Service moves responsibility to the client.** DNS can return pod endpoint addresses directly, but the client must handle multiple answers, changing endpoints, and failed peers.
- **Negative answers can be cached.** Repeated `NXDOMAIN` responses are not always fresh proof that an object is missing; a resolver may be reusing a negative cached answer until its TTL behavior permits another lookup.

## Common Mistakes

| Mistake | Why It Happens | How to Fix |
|---------|---------------|------------|
| Assuming the Corefile line order is execution order | The Corefile is readable configuration, but CoreDNS execution follows compiled plugin ordering | Use documented plugin behavior and test the resulting answers |
| Leaving external-heavy clients on default `ndots:5` | Names with fewer than five dots traverse the search list before absolute lookup | Use trailing-dot FQDNs or targeted `dnsConfig` after testing |
| Calling a cross-namespace Service by short name | The caller's namespace is searched first, so the wrong local Service may win | Use `<service>.<namespace>` or the full Service DNS name |
| Adding a `hosts` override without `fallthrough` | Unmatched names can stop at the override block and return unexpected misses | Add `fallthrough` unless the block intentionally owns the whole suffix |
| Treating ExternalName as traffic management | It returns a DNS alias but does not add health checks, retries, or TLS policy | Use it only as a naming abstraction and document client behavior |
| Forwarding all DNS to a private resolver | Corporate DNS outages or policy changes become cluster-wide application outages | Forward only the private suffixes that require that resolver |
| Enabling ExternalDNS without tight ownership controls | A broad controller can create, update, or delete records outside its intended scope | Use domain filters, TXT registry ownership, and conservative deletion policy |
| Debugging from the wrong namespace or network mode | DNS behavior depends on `dnsPolicy`, search list, and pod context | Reproduce from a pod with the same namespace and resolver policy |

## Quiz

**Question 1:** A pod in namespace `checkout` can resolve `payments.checkout.svc.cluster.local`, but it fails when the application calls only `payments`. What should you check first?

<details>
<summary>Show Answer</summary>

Check the pod's `/etc/resolv.conf` and confirm the search list includes the namespace and service suffixes you expect. If the fully qualified Service name works, CoreDNS and the Service record are probably healthy. The failure is likely in resolver policy, namespace context, or application normalization of the name. This is why tracing the lookup from the pod resolver is the first outcome in this module.
</details>

**Question 2:** An application makes many calls to `api.example.com`, and CoreDNS metrics show many `NXDOMAIN` responses ending in `svc.cluster.local`. What resolver behavior is probably causing the extra queries?

<details>
<summary>Show Answer</summary>

The likely cause is search-domain expansion under the default `ndots:5` resolver option. Because `api.example.com` has fewer than five dots, the resolver tries each search suffix before the absolute name. A trailing dot or targeted `dnsConfig` can reduce that work, but you should verify the application runtime preserves the intended name. The durable lesson is to diagnose the question being asked, not only the answer returned.
</details>

**Question 3:** You add a CoreDNS block for `corp.internal`, but all external names start failing after the rollout. What CoreDNS design mistake should you suspect?

<details>
<summary>Show Answer</summary>

Suspect that the forwarding change became too broad or introduced a forwarding loop. Conditional forwarding should be scoped to the private suffix, while the ordinary `.` path should still forward public names through the normal resolver path. Inspect the actual Corefile, CoreDNS logs, and `SERVFAIL` metrics before changing more settings. This question maps to the outcome about configuring CoreDNS safely rather than treating the ConfigMap as a text snippet to paste over.
</details>

**Question 4:** A busy cluster shows intermittent DNS stalls during rollout waves, and node metrics show conntrack pressure. Why might NodeLocal DNSCache help?

<details>
<summary>Show Answer</summary>

NodeLocal DNSCache can serve cache hits on the same node and reduce traffic through the central kube-dns Service path. More importantly, its node-local path and iptables `NOTRACK` behavior reduce exposure to UDP conntrack DNAT races that can create long lookup tails. It is still an operational component that must fit the cluster dataplane. Use it when the measured failure mode matches DNS load, tail latency, or conntrack pressure.
</details>

**Question 5:** A team wants stable DNS names for each replica of a clustered database. Should you use a normal ClusterIP Service or a headless Service, and why?

<details>
<summary>Show Answer</summary>

Use a headless Service when the client genuinely needs individual peer identities rather than a single virtual Service address. DNS can return endpoint records and SRV data that let the database discover specific peers. The client must tolerate multiple answers, changing endpoints, and failed pods. For ordinary stateless replicas, a normal ClusterIP Service is simpler and safer.
</details>

**Question 6:** ExternalDNS is installed with access to a large public zone, and a test Ingress annotation creates an unexpected public record. Which controls should be tightened first?

<details>
<summary>Show Answer</summary>

Tighten `domainFilters`, registry ownership, and deletion policy before giving the controller broad authority. ExternalDNS should manage only the suffixes that Kubernetes resources are allowed to own. TXT ownership helps separate multiple clusters or controllers, while conservative policy reduces deletion risk during adoption. This aligns external DNS automation with explicit operational authority.
</details>

**Question 7:** A platform review finds a permanent CoreDNS `rewrite` from an old service name to a new one. The rewrite still works, so why might it still be a problem?

<details>
<summary>Show Answer</summary>

A permanent rewrite hides stale application configuration and makes future incidents harder to reason about. New operators may not know that clients are using an old name, and the rewrite can interfere with later naming changes. A rewrite should have an owner, a reason, and an expected removal path. DNS compatibility tools are useful during migrations, but they should not become undocumented platform behavior.
</details>

## Hands-On

This lab is designed to be safe on a disposable kind, minikube, or sandbox cluster. It inspects DNS behavior, creates a simple Service, and reads CoreDNS configuration without requiring you to edit the production Corefile. If you adapt it for a shared cluster, use a temporary namespace and clean up every object at the end.

```bash
kubectl create namespace dns-lab
kubectl create deployment web --image=nginx:stable-alpine --port=80 -n dns-lab
kubectl expose deployment web --port=80 --target-port=80 -n dns-lab

kubectl run dns-tools \
  --image=ghcr.io/nicolaka/netshoot:latest \
  --restart=Never \
  -n dns-lab \
  -- sleep 3600

kubectl wait --for=condition=Ready pod/dns-tools -n dns-lab --timeout=120s
kubectl exec -n dns-lab dns-tools -- cat /etc/resolv.conf
kubectl exec -n dns-lab dns-tools -- nslookup web
kubectl exec -n dns-lab dns-tools -- nslookup web.dns-lab.svc.cluster.local
kubectl exec -n dns-lab dns-tools -- dig +search +tries=1 +timeout=2 api.example.com A
kubectl get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}'
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
```

Record what you see before changing anything. The resolver file should show the nameserver, search list, and `ndots` option used by the debug pod. The short Service lookup and the fully qualified lookup should both resolve to the Service path. The external `dig +search` command should show whether the resolver performs search expansion before reaching the absolute public name. The Corefile output should let you identify the `kubernetes`, `forward`, `cache`, `loop`, `reload`, `health`, and `ready` behavior in your actual cluster.

For a deeper exercise, create a second debug pod with a targeted `dnsConfig` and compare the resolver file rather than editing the whole cluster. This shows the difference between workload-specific resolver policy and platform-wide DNS behavior. It also reinforces the safest way to tune `ndots`: change one workload with a known access pattern, observe it, and then decide whether the pattern deserves a reusable platform default.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-tools-ndots-two
  namespace: dns-lab
spec:
  dnsPolicy: ClusterFirst
  dnsConfig:
    options:
      - name: ndots
        value: "2"
  containers:
    - name: dns-tools
      image: ghcr.io/nicolaka/netshoot:latest
      command: ["sleep", "3600"]
```

```bash
kubectl apply -f dns-tools-ndots-two.yaml
kubectl wait --for=condition=Ready pod/dns-tools-ndots-two -n dns-lab --timeout=120s
kubectl exec -n dns-lab dns-tools-ndots-two -- cat /etc/resolv.conf
kubectl exec -n dns-lab dns-tools-ndots-two -- dig +search +tries=1 +timeout=2 api.example.com A
```

Success criteria:

- [ ] You captured `/etc/resolv.conf` from a pod and identified the nameserver, search list, and `ndots` value.
- [ ] You resolved the test Service by short name and by full Service DNS name from the same namespace.
- [ ] You compared default resolver behavior with a pod that sets `ndots:2` and explained the difference in search expansion.
- [ ] You located the live CoreDNS Corefile and identified the plugin blocks responsible for cluster names, forwarding, caching, health, readiness, loop detection, and reloads.
- [ ] You checked CoreDNS logs or metrics and wrote one sentence explaining whether the observed symptom points to Service DNS, forwarding, search expansion, or upstream resolution.

Clean up the lab namespace when you are finished. If you created the second pod from a local YAML file, deleting the namespace removes both debug pods, the Service, and the deployment. The command below intentionally avoids touching CoreDNS or any shared cluster configuration.

```bash
kubectl delete namespace dns-lab
```

## Sources

- [CoreDNS homepage](https://coredns.io/)
- [CoreDNS manual](https://coredns.io/manual/toc/)
- [CoreDNS releases](https://github.com/coredns/coredns/releases)
- [CNCF CoreDNS project page](https://www.cncf.io/projects/coredns/)
- [CoreDNS Kubernetes plugin](https://coredns.io/plugins/kubernetes/)
- [CoreDNS forward plugin](https://coredns.io/plugins/forward/)
- [CoreDNS cache plugin](https://coredns.io/plugins/cache/)
- [CoreDNS hosts plugin](https://coredns.io/plugins/hosts/)
- [CoreDNS rewrite plugin](https://coredns.io/plugins/rewrite/)
- [CoreDNS loop plugin](https://coredns.io/plugins/loop/)
- [CoreDNS reload plugin](https://coredns.io/plugins/reload/)
- [CoreDNS health plugin](https://coredns.io/plugins/health/)
- [CoreDNS ready plugin](https://coredns.io/plugins/ready/)
- [CoreDNS autopath plugin](https://coredns.io/plugins/autopath/)
- [Kubernetes v1.35: DNS for Services and Pods](https://v1-35.docs.kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Kubernetes v1.35: Customizing DNS Service](https://v1-35.docs.kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/)
- [Kubernetes v1.35: Debugging DNS Resolution](https://v1-35.docs.kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)
- [Kubernetes v1.35: NodeLocal DNSCache](https://v1-35.docs.kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/)
- [NodeLocal DNSCache KEP](https://github.com/kubernetes/enhancements/blob/master/keps/sig-network/1024-nodelocal-cache-dns/README.md)
- [Kubernetes DNS specification](https://github.com/kubernetes/dns/blob/master/docs/specification.md)
- [NodeLocal DNSCache source: iptables NOTRACK rules](https://github.com/kubernetes/dns/blob/master/cmd/node-cache/app/cache_app.go)
- [ExternalDNS documentation](https://kubernetes-sigs.github.io/external-dns/latest/)
- [ExternalDNS annotations](https://kubernetes-sigs.github.io/external-dns/latest/docs/annotations/annotations/)
- [ExternalDNS AWS tutorial](https://kubernetes-sigs.github.io/external-dns/latest/docs/tutorials/aws/)

## Next Module

Continue with [Module 5.4: MetalLB](../module-5.4-metallb/) to connect Kubernetes Service discovery with load balancer address management for bare-metal and private infrastructure clusters.
