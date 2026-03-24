# Module 5.3: DNS Deep Dive

## Complexity: [MEDIUM]
## Time to Complete: 40 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [CKA Module: DNS in Kubernetes](../../../k8s/cka/README.md) - Core DNS concepts, Service discovery basics
- [Module 5.1: Cilium](module-5.1-cilium.md) - Networking fundamentals
- Basic understanding of DNS (A records, CNAME, TTL)

---

## Why This Module Matters

*The VP of Engineering stared at the dashboard. Average API latency: 500ms. The application code took 12ms. Where were the other 488 milliseconds going?*

A mid-size SaaS company had been chasing this ghost for weeks. Their microservices were fast in isolation, but every cross-service call added mysterious overhead. They profiled the code. They tuned the database. They upgraded the network. Nothing helped.

Then a junior engineer ran `strace` on a simple HTTP call and saw it: five DNS queries fired before the actual resolution succeeded. Every single service-to-service call triggered five failed lookups before the sixth one returned an answer.

The culprit? Kubernetes' default `ndots:5` setting. When their Go service called `payments-api:8080`, the resolver dutifully tried `payments-api.default.svc.cluster.local`, then `payments-api.svc.cluster.local`, then `payments-api.cluster.local`, then `payments-api.us-east-1.compute.internal`, then `payments-api.ec2.internal`--all failures--before finally resolving the bare name. Five unnecessary round trips. On every request. Across 200 microservices making thousands of calls per second.

The fix was a two-line YAML change. Latency dropped from 500ms to 45ms overnight.

**This module teaches you** how to master CoreDNS configuration, eliminate DNS-related performance problems, and automate external DNS management--because DNS is the invisible backbone that can silently destroy your cluster's performance.

---

## Did You Know?

- **DNS is the #1 hidden performance killer in Kubernetes.** The default `ndots:5` setting means a lookup for `api.stripe.com` generates 5 failed queries before succeeding--multiplied across every outbound call in your cluster.
- **CoreDNS handles billions of queries daily** across Kubernetes clusters worldwide. It replaced kube-dns in Kubernetes 1.13 and processes every single service discovery request in your cluster.
- **NodeLocal DNSCache can reduce DNS latency by 10x.** By running a DNS cache on every node, queries that normally take 5-10ms round-trip to CoreDNS drop to sub-millisecond local lookups.
- **external-dns was born from frustration.** Engineers were tired of manually updating Route53 every time they created an Ingress. The project now supports 30+ DNS providers and manages millions of records automatically.

---

## CoreDNS Corefile Deep Dive

CoreDNS is configured through a file called the **Corefile**, stored in a ConfigMap named `coredns` in the `kube-system` namespace. Let's look at the default and then customize it.

### The Default Corefile

```bash
k get configmap coredns -n kube-system -o yaml
```

```
.:53 {
    errors
    health {
        lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
        max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

### Plugin Ordering Matters

CoreDNS processes plugins **in the order they appear in the Corefile**. This is critical--a misconfigured order can silently break DNS resolution.

| Plugin | Purpose | When to Customize |
|--------|---------|-------------------|
| `errors` | Log errors to stdout | Always keep first |
| `health` | Health check endpoint on :8080 | Rarely changed |
| `ready` | Readiness check endpoint on :8181 | Rarely changed |
| `kubernetes` | Resolve cluster Services/Pods | Zone or TTL tuning |
| `prometheus` | Expose metrics on :9153 | Leave enabled |
| `forward` | Forward unresolved queries upstream | Custom upstreams, split DNS |
| `cache` | Cache DNS responses | Increase for performance |
| `rewrite` | Rewrite queries before processing | Domain aliasing, migrations |
| `hosts` | Serve records from inline entries | Static overrides, testing |
| `file` | Serve records from a zone file | Advanced custom zones |
| `loop` | Detect and halt forwarding loops | Always keep |
| `reload` | Auto-reload Corefile on changes | Always keep |
| `loadbalance` | Randomize A/AAAA record order | Always keep |

### Customizing the Corefile

**Split DNS: Route internal domains to a private DNS server**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health { lameduck 5s }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
            ttl 30
        }
        prometheus :9153
        forward . /etc/resolv.conf { max_concurrent 1000 }
        cache 30
        loop
        reload
        loadbalance
    }
    corp.internal:53 {
        errors
        cache 60
        forward . 10.0.0.53 10.0.0.54
    }
```

This routes `*.corp.internal` queries to your corporate DNS servers while everything else goes through the normal resolution path.

**Rewrite plugin: Migrate service names without breaking callers**

```
rewrite name old-payment-svc.default.svc.cluster.local new-payment-svc.default.svc.cluster.local
```

This transparently redirects lookups for the old service name to the new one--invaluable during service migrations.

**Hosts plugin: Override specific records**

```
hosts {
    10.0.0.100 legacy-db.corp.internal
    10.0.0.101 legacy-cache.corp.internal
    fallthrough
}
```

The `fallthrough` directive is essential--without it, any query not matched by the hosts block will return NXDOMAIN instead of continuing to the next plugin.

---

## DNS Performance Optimization

### The ndots Problem

The `ndots` setting in `/etc/resolv.conf` controls when the resolver treats a name as fully qualified. The Kubernetes default is `ndots:5`, meaning any name with fewer than 5 dots gets the search domains appended first.

**What happens when your app calls `api.stripe.com` (2 dots, less than 5):**

```
1. api.stripe.com.default.svc.cluster.local  → NXDOMAIN (wasted)
2. api.stripe.com.svc.cluster.local          → NXDOMAIN (wasted)
3. api.stripe.com.cluster.local              → NXDOMAIN (wasted)
4. api.stripe.com.us-east-1.compute.internal → NXDOMAIN (wasted)
5. api.stripe.com.ec2.internal               → NXDOMAIN (wasted)
6. api.stripe.com.                           → SUCCESS (finally!)
```

Six queries instead of one. Multiply that by every external API call across every pod.

**Fix 1: Set ndots to 2 in your pod spec**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  dnsConfig:
    options:
      - name: ndots
        value: "2"
  containers:
    - name: app
      image: my-app:latest
```

With `ndots:2`, names with 2+ dots (like `api.stripe.com`) are tried as absolute names first. Internal service names like `my-svc` still get the search domains appended.

**Fix 2: Use FQDNs with trailing dots in your application**

```yaml
# In your app config, use trailing dots for external domains:
STRIPE_API_HOST: "api.stripe.com."
DATABASE_HOST: "db.us-east-1.rds.amazonaws.com."
```

The trailing dot tells the resolver "this is already fully qualified, do not append search domains." Zero wasted queries.

**Fix 3: Reduce search domains**

```yaml
spec:
  dnsConfig:
    searches:
      - default.svc.cluster.local
      - svc.cluster.local
    options:
      - name: ndots
        value: "2"
```

### NodeLocal DNSCache

NodeLocal DNSCache runs a lightweight DNS caching agent on every node as a DaemonSet. Instead of pods sending queries across the network to CoreDNS, they hit a local cache first.

**Why it matters:**
- Cache hits resolve in **<1ms** instead of 5-10ms network round trips
- Reduces load on CoreDNS pods dramatically
- Eliminates conntrack race conditions that cause intermittent DNS failures on busy nodes (the infamous `EAGAIN` bug)

**Deploy NodeLocal DNSCache:**

```bash
# Get your cluster DNS IP
CLUSTER_DNS=$(k get svc kube-dns -n kube-system -o jsonpath='{.spec.clusterIP}')

# Apply the NodeLocal DNSCache manifest (Kubernetes official addon)
# Replace __PILLAR__CLUSTER__DNS__ and __PILLAR__DNS__DOMAIN__ in the manifest
curl -s https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/dns/nodelocaldns/nodelocaldns.yaml \
  | sed "s/__PILLAR__CLUSTER__DNS__/$CLUSTER_DNS/g" \
  | sed "s/__PILLAR__DNS__DOMAIN__/cluster.local/g" \
  | sed "s/__PILLAR__LOCAL__DNS__/169.254.20.10/g" \
  | k apply -f -
```

**Verify it is running:**

```bash
k get pods -n kube-system -l k8s-app=node-local-dns
```

After deployment, pods on each node will resolve DNS through the local cache at `169.254.20.10` before falling through to CoreDNS.

---

## external-dns: Automatic DNS Record Management

external-dns watches Kubernetes resources (Ingress, Service, Gateway) and automatically creates DNS records in your cloud provider. No more manual Route53 clicks.

### How It Works

```
Ingress/Service/Gateway created
        ↓
external-dns detects the resource
        ↓
Reads annotations for hostname/TTL
        ↓
Creates/updates DNS record in provider (Route53, CloudFlare, etc.)
        ↓
Resource deleted → DNS record cleaned up
```

### Installation

```bash
# Add the Helm repo
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm repo update

# Install for AWS Route53
helm install external-dns external-dns/external-dns \
  --namespace external-dns \
  --create-namespace \
  --set provider.name=aws \
  --set policy=sync \
  --set registry=txt \
  --set txtOwnerId=my-cluster \
  --set domainFilters[0]=example.com
```

The `txtOwnerId` is critical in multi-cluster setups--it prevents one cluster from deleting records owned by another.

### Provider Configuration

| Provider | Auth Method | Key Setting |
|----------|-------------|-------------|
| **AWS Route53** | IRSA / IAM role | `provider.name=aws` |
| **Cloudflare** | API token | `--set cloudflare.apiToken=<token>` |
| **Google Cloud DNS** | Workload Identity / SA key | `provider.name=google` |
| **Azure DNS** | Managed Identity / SP | `provider.name=azure` |

### Annotations for Controlling Records

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    # Tell external-dns what hostname to create
    external-dns.alpha.kubernetes.io/hostname: app.example.com
    # Set a custom TTL (default is usually 300)
    external-dns.alpha.kubernetes.io/ttl: "60"
    # Create an alias record instead of CNAME (AWS-specific)
    external-dns.alpha.kubernetes.io/alias: "true"
spec:
  ingressClassName: nginx
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

**For Services (LoadBalancer type):**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-api
  annotations:
    external-dns.alpha.kubernetes.io/hostname: api.example.com
    external-dns.alpha.kubernetes.io/ttl: "120"
spec:
  type: LoadBalancer
  ports:
    - port: 443
      targetPort: 8443
  selector:
    app: my-api
```

external-dns reads the annotation, waits for the LoadBalancer to get an external IP/hostname, and creates the DNS record pointing to it.

---

## DNS Debugging Toolkit

When DNS breaks, everything breaks. Here is your troubleshooting arsenal.

### Quick Debug Commands

```bash
# Spin up a debug pod with DNS tools
k run dns-debug --image=registry.k8s.io/e2e-test-images/agnhost:2.39 \
  --restart=Never -- sleep 3600

# Test cluster DNS resolution
k exec dns-debug -- nslookup kubernetes.default.svc.cluster.local

# Test external resolution
k exec dns-debug -- nslookup google.com

# Detailed query with dig (shows timing and query path)
k exec dns-debug -- dig +search +all payments-api.default.svc.cluster.local

# Check what resolv.conf looks like inside the pod
k exec dns-debug -- cat /etc/resolv.conf

# Cleanup
k delete pod dns-debug --now
```

### CoreDNS Metrics

CoreDNS exposes Prometheus metrics on port 9153. The key ones to monitor:

```promql
# Query rate - how busy is CoreDNS?
rate(coredns_dns_requests_total[5m])

# Error rate - are queries failing?
rate(coredns_dns_responses_total{rcode="SERVFAIL"}[5m])

# Cache hit ratio - is caching effective?
coredns_cache_hits_total / (coredns_cache_hits_total + coredns_cache_misses_total)

# Latency - how fast are responses?
histogram_quantile(0.99, rate(coredns_dns_request_duration_seconds_bucket[5m]))
```

### Common DNS Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `SERVFAIL` on all external queries | Upstream DNS unreachable | Check `forward` plugin config and network policies |
| Intermittent `EAGAIN` / `connection refused` | conntrack table full on busy nodes | Deploy NodeLocal DNSCache |
| Resolution works, but takes 5+ seconds | ndots causing search domain expansion | Set `ndots:2` or use FQDNs with trailing dots |
| New Service not resolving | CoreDNS not watching the namespace | Check CoreDNS logs, ensure `kubernetes` plugin config |
| `NXDOMAIN` for valid Service | Wrong namespace in query | Use full `svc-name.namespace.svc.cluster.local` |
| DNS works in pods but not in init containers | Init container ran before CoreDNS was ready | Add `dnsPolicy: Default` or init container retry logic |

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix |
|---------|---------------|------------|
| Leaving `ndots:5` as default | Nobody reads the default resolv.conf | Set `ndots:2` in pod spec or use FQDNs with trailing dots |
| Editing CoreDNS ConfigMap without `reload` plugin | Expecting changes to apply instantly | Ensure `reload` is in the Corefile (it is by default) |
| Missing `fallthrough` in hosts/file plugins | Queries not matched by the plugin return NXDOMAIN | Always add `fallthrough` unless you want to terminate resolution |
| Setting DNS cache TTL too high | Stale records after Service recreation | Use 30s for cluster-internal, up to 300s for external |
| external-dns without `txtOwnerId` | Multiple clusters overwrite each other's records | Always set a unique owner ID per cluster |
| Not monitoring CoreDNS metrics | DNS degradation goes unnoticed until apps fail | Alert on SERVFAIL rate and p99 latency |
| Forgetting `dnsPolicy` when using `hostNetwork` | Pods with hostNetwork skip cluster DNS by default | Set `dnsPolicy: ClusterFirstWithHostNet` |

---

## Quiz

**Question 1:** Your pod calls `api.payment.example.com`. With the default `ndots:5`, how many DNS queries will be made before the name resolves?

<details>
<summary>Show Answer</summary>

**Six queries.** The name `api.payment.example.com` has 3 dots, which is less than 5. The resolver appends each search domain first (generating 5 NXDOMAIN responses), then tries the bare name as a last resort. Setting `ndots:2` or appending a trailing dot (`api.payment.example.com.`) would resolve it in one query.
</details>

**Question 2:** You add a custom server block to the CoreDNS Corefile for `corp.internal` but queries to `app.corp.internal` return SERVFAIL. What should you check first?

<details>
<summary>Show Answer</summary>

Check that the `forward` directive in the `corp.internal` block points to a reachable DNS server. Also verify that no NetworkPolicy is blocking CoreDNS pods from reaching the corporate DNS server IP. Run `k logs -n kube-system -l k8s-app=kube-dns` to see the actual error CoreDNS is returning.
</details>

**Question 3:** After deploying NodeLocal DNSCache, how do pods know to use the local cache instead of the CoreDNS ClusterIP?

<details>
<summary>Show Answer</summary>

NodeLocal DNSCache uses a link-local address (`169.254.20.10`) and modifies the node's iptables/ipvs rules to intercept traffic destined for the `kube-dns` ClusterIP. Pods continue to use the same ClusterIP in their `/etc/resolv.conf`, but the traffic is transparently redirected to the local cache. If the local cache is down, traffic falls through to CoreDNS normally.
</details>

**Question 4:** You deploy external-dns with `policy=sync` and notice DNS records disappearing. What is happening?

<details>
<summary>Show Answer</summary>

The `sync` policy means external-dns will **delete** any DNS records in the managed zone that do not correspond to a current Kubernetes resource. If you have manually created records or records from another source, `sync` will remove them. Use `policy=upsert-only` if you want external-dns to create and update records but never delete them. Alternatively, use `domainFilters` to restrict which domains external-dns manages.
</details>

---

## Hands-On Exercise: DNS Mastery Lab

### Objective

Customize CoreDNS, optimize DNS performance, and set up external-dns record management.

### Setup

```bash
# Create a kind cluster
kind create cluster --name dns-lab

# Deploy two test services
k create namespace app-team
k run web --image=nginx --port=80 -n app-team
k expose pod web --port=80 -n app-team
k run api --image=nginx --port=80 -n app-team
k expose pod api --port=80 -n app-team
```

### Part 1: CoreDNS Customization (10 min)

1. View the current CoreDNS Corefile:
```bash
k get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}'
```

2. Add a custom hosts entry that maps `legacy-db.corp.internal` to `10.96.0.100`:
```bash
k edit configmap coredns -n kube-system
```

Add before the `forward` line:
```
hosts {
    10.96.0.100 legacy-db.corp.internal
    fallthrough
}
```

3. Wait for CoreDNS to reload (check logs):
```bash
k logs -n kube-system -l k8s-app=kube-dns -f --tail=5
```

4. Verify the custom entry resolves:
```bash
k run dns-test --image=busybox:1.36 --restart=Never -- nslookup legacy-db.corp.internal
k logs dns-test
```

**Success criteria:** `nslookup` returns `10.96.0.100` for `legacy-db.corp.internal`.

### Part 2: DNS Performance Optimization (15 min)

1. Check the default resolv.conf inside a pod:
```bash
k run check-dns --image=busybox:1.36 --restart=Never -n app-team -- cat /etc/resolv.conf
k logs check-dns -n app-team
```

Note the `ndots:5` and the search domains listed.

2. Create a pod with optimized DNS settings:
```yaml
# Save as optimized-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: optimized-app
  namespace: app-team
spec:
  dnsConfig:
    options:
      - name: ndots
        value: "2"
    searches:
      - app-team.svc.cluster.local
      - svc.cluster.local
  containers:
    - name: app
      image: busybox:1.36
      command: ["sleep", "3600"]
```

```bash
k apply -f optimized-pod.yaml
```

3. Compare DNS behavior--verify internal resolution still works:
```bash
k exec optimized-app -n app-team -- nslookup web
k exec optimized-app -n app-team -- nslookup api.app-team.svc.cluster.local
```

4. Verify external resolution is faster (no wasted queries):
```bash
k exec optimized-app -n app-team -- nslookup google.com
```

**Success criteria:** Internal Services resolve correctly. External names resolve without search domain expansion.

### Part 3: external-dns Simulation (10 min)

Since external-dns requires a real DNS provider, we will simulate the setup and verify the configuration:

1. Install external-dns in dry-run mode:
```bash
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm repo update
helm install external-dns external-dns/external-dns \
  --namespace external-dns \
  --create-namespace \
  --set provider.name=aws \
  --set policy=upsert-only \
  --set registry=txt \
  --set txtOwnerId=dns-lab \
  --set dryRun=true \
  --set logLevel=debug
```

2. Create a Service with external-dns annotations:
```yaml
# Save as annotated-svc.yaml
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
  selector:
    app: api
```

```bash
k apply -f annotated-svc.yaml
```

3. Check external-dns logs to see it detecting the annotated resource:
```bash
k logs -n external-dns -l app.kubernetes.io/name=external-dns --tail=20
```

**Success criteria:** external-dns logs show it detected the annotated Service and would create an A/CNAME record for `api.example.com`.

### Cleanup

```bash
kind delete cluster --name dns-lab
```

---

## Further Reading

- [CoreDNS Manual](https://coredns.io/manual/toc/) - Official plugin reference
- [Kubernetes DNS Specification](https://github.com/kubernetes/dns/blob/master/docs/specification.md) - How cluster DNS must behave
- [external-dns Tutorials](https://kubernetes-sigs.github.io/external-dns/) - Provider-specific setup guides
- [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) - Official Kubernetes documentation

---

## Cross-References

- **CKA DNS Module** - Covers foundational DNS concepts: Service discovery, `dnsPolicy`, and basic CoreDNS configuration that this module builds upon
- [Module 5.1: Cilium](module-5.1-cilium.md) - Network fundamentals and CNI context
- [Module 5.2: Service Mesh](module-5.2-service-mesh.md) - mTLS and service-to-service communication
- [Module 1.1: Prometheus](../observability/module-1.1-prometheus.md) - Monitoring CoreDNS metrics

---

## Next Module

Continue to the next networking module or explore [Module 1.1: Prometheus](../observability/module-1.1-prometheus.md) to set up monitoring for the CoreDNS metrics discussed in this module.
