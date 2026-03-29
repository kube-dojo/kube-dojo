---
title: "Module 5.1: Cilium - The Kernel-Powered Network Revolution"
slug: platform/toolkits/infrastructure-networking/networking/module-5.1-cilium
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 60-75 minutes

## The 3 AM Wake-Up Call

*Your phone buzzes. Production is down. The ops channel is on fire.*

```
[03:12 AM] @oncall ALERT: Payment service timeouts
[03:14 AM] @oncall Network team says "looks fine on their end"
[03:17 AM] @oncall It's DNS
[03:18 AM] @oncall It's always DNS
[03:23 AM] @oncall Wait, it's not DNS. Something is dropping packets.
[03:31 AM] @oncall Running tcpdump on all 47 pods. Send coffee.
[03:52 AM] @oncall Found it. NetworkPolicy was blocking the new service.
[03:54 AM] @oncall We have 200+ NetworkPolicies. Which one? No idea.
[04:23 AM] @oncall Fixed by adding another allow rule. We'll clean up later.
[04:24 AM] @oncall We never clean up later.
```

**Sound familiar?**

This is what Kubernetes networking feels like without proper tooling. You're blind. Packets vanish into the void. Policies are write-only—you create them but never know which one is actually doing what.

Cilium changes everything. By the end of this module, when something drops packets, you'll know *exactly* which policy dropped it, *why*, and you'll see it happen in real-time. No more 4 AM tcpdump sessions.

**What You'll Learn**:
- Why traditional networking can't keep up with Kubernetes
- How eBPF lets you program the Linux kernel (without being a kernel developer)
- Identity-based security that actually makes sense
- Hubble: seeing every packet, every decision, every drop
- Replacing kube-proxy and why you'll never miss it

**Prerequisites**:
- Kubernetes networking basics (Services, Pods)
- [Security Principles Foundations](../../foundations/security-principles/)
- A healthy frustration with iptables (optional but helps)

---

## Why This Module Matters

Let me tell you about the moment I fell in love with Cilium.

We had a microservices architecture—127 services, because apparently we thought Netflix was a good role model. One service was mysteriously failing health checks. The app worked fine when tested directly. Network team said the network was fine. App team said the app was fine. Classic standoff.

With traditional tools, we would've spent hours with tcpdump and iptables debugging. Instead, I ran one command:

```bash
hubble observe --pod production/payment-service --verdict DROPPED
```

Three seconds later:

```
production/payment-service → production/health-checker DROPPED
Policy: production/legacy-lockdown (ingress)
```

**The legacy-lockdown policy.** Written 18 months ago by someone who left the company. Blocked traffic from a service that didn't exist when the policy was created.

Five-minute fix. Without Cilium, we'd still be debugging.

> 💡 **Did You Know?** When Google designed their next-generation internal networking, they chose eBPF—the same technology powering Cilium. The reason? At Google scale, traditional iptables rules would take *minutes* to update. With eBPF, updates happen in microseconds. Google Cloud GKE, AWS EKS, and Azure AKS all now offer Cilium as their CNI. It's not just an alternative anymore—it's becoming the default.

---

## Part 1: Understanding the Problem (Before We Solve It)

### The IPTables Nightmare

Before we talk about Cilium's solution, you need to feel the pain of the old way.

Every Kubernetes cluster runs kube-proxy. Every time you create a Service, kube-proxy adds iptables rules. Let's see what that actually looks like:

```bash
# On a modest cluster with 500 services:
iptables-save | wc -l
# Output: 12,847 lines

# On a large cluster with 5,000 services:
iptables-save | wc -l
# Output: 147,291 lines
```

**One hundred and forty-seven thousand lines of iptables rules.**

Now imagine debugging why one specific packet was dropped.

```
THE IPTABLES DEBUGGING EXPERIENCE
═══════════════════════════════════════════════════════════════════

You: "Why was my packet dropped?"

iptables: "Let me check...
          Chain PREROUTING → Chain KUBE-SERVICES → Chain KUBE-SVC-XYZABC123
          → Chain KUBE-SEP-DEF456 → Chain KUBE-POSTROUTING →
          Actually I lost track. Somewhere in these 147,000 rules."

You: "Which rule specifically?"

iptables: "¯\_(ツ)_/¯"

You: "How do I see what's being blocked?"

iptables: "Add LOG rules everywhere. Parse the logs yourself.
          Good luck with the performance impact."

You: [opens job listings]
```

And it gets worse. When you update a Service:

```
TIME TO UPDATE 147,000 IPTABLES RULES
═══════════════════════════════════════════════════════════════════

1. kube-proxy receives Service update
2. kube-proxy rewrites ALL rules (can't do incremental)
3. Takes ~5-30 seconds on large clusters
4. During rewrite: connections drop, new connections may fail
5. All nodes do this simultaneously
6. Your monitoring alerts go crazy

This happens every time:
- A pod scales up/down
- A service is created/deleted
- An endpoint changes

At scale: dozens of times per minute
```

This isn't a hypothetical. [Datadog wrote about hitting this limit](https://www.datadoghq.com/blog/engineering/introducing-glommio/). So did [Shopify](https://shopify.engineering/resiliency-planning-how-we-prepared-for-black-friday). Large-scale Kubernetes users universally agree: iptables doesn't scale.

### The NetworkPolicy Problem

Standard Kubernetes NetworkPolicies have a different problem: they're based on IP addresses.

```yaml
# This NetworkPolicy looks reasonable:
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
```

Under the hood, this becomes:

```
"Allow traffic from IP 10.244.1.45 to port 80"
"Allow traffic from IP 10.244.2.23 to port 80"
"Allow traffic from IP 10.244.3.67 to port 80"
```

Now the frontend pod crashes and restarts. New IP: 10.244.1.99.

The CNI has to:
1. Detect the IP change
2. Update every policy that references frontend
3. Push those updates to every node
4. Hope nothing breaks during the transition

This happens constantly in Kubernetes. Pods restart, scale, move between nodes. IP addresses are ephemeral by design.

**Building security on IP addresses is like building a house on quicksand.**

---

## Part 2: Enter eBPF - Programming the Unprogrammable

### What is eBPF?

eBPF stands for "extended Berkeley Packet Filter," but that name is misleading. It's evolved far beyond packet filtering.

Here's the mental model that helped me understand it:

```
THE JAVASCRIPT OF THE LINUX KERNEL
═══════════════════════════════════════════════════════════════════

Remember when browsers only displayed static HTML?
Then JavaScript came along: "What if we could run code IN the browser?"
Suddenly browsers could do anything.

eBPF is JavaScript for the Linux kernel.

Before eBPF:
- Want to change how networking works? Modify kernel code, recompile, reboot.
- Want to add tracing? Load a kernel module, pray it doesn't crash.
- Want custom packet processing? Install a userspace proxy, accept the overhead.

With eBPF:
- Write small programs that run INSIDE the kernel
- Load them dynamically, no reboot needed
- Kernel verifies they're safe before running
- Run at kernel speed (no userspace context switches)
```

Here's a concrete example. Traditional packet processing:

```
TRADITIONAL PACKET FLOW
═══════════════════════════════════════════════════════════════════

Packet arrives at network card
         │
         ▼
    Kernel receives packet
         │
         ▼
    iptables chain 1 (PREROUTING)
         │
         ▼
    iptables chain 2 (INPUT/FORWARD)
         │
         ▼
    Routing decision
         │
         ▼
    iptables chain 3 (OUTPUT)
         │
         ▼
    iptables chain 4 (POSTROUTING)
         │
         ▼
    Copy packet to userspace ← EXPENSIVE!
         │
         ▼
    Userspace proxy (kube-proxy/envoy/etc)
         │
         ▼
    Copy packet back to kernel ← EXPENSIVE!
         │
         ▼
    Finally reaches destination

Cost: ~50-100 microseconds per packet
      Multiple memory copies
      CPU cache thrashing
```

With eBPF:

```
eBPF PACKET FLOW
═══════════════════════════════════════════════════════════════════

Packet arrives at network card
         │
         ▼
    eBPF program runs (in kernel)
    - Looks up destination in hash map: O(1)
    - Applies policy: O(1)
    - Rewrites headers if needed
    - Decides: forward, drop, or redirect
         │
         ▼
    Packet reaches destination

Cost: ~5-10 microseconds per packet
      Zero memory copies
      Runs in kernel context

10x faster. Zero userspace involvement for most packets.
```

### Why eBPF is Safe (Despite Running in the Kernel)

"Wait," I hear you thinking, "running arbitrary code in the kernel sounds terrifying."

You're right. That's why eBPF has a verifier:

```
THE eBPF VERIFIER: YOUR KERNEL'S BOUNCER
═══════════════════════════════════════════════════════════════════

Before ANY eBPF program runs, the verifier checks:

✓ Does it terminate? (No infinite loops allowed)
✓ Does it access only allowed memory? (No kernel crashes)
✓ Does it use only allowed kernel functions?
✓ Does it handle all code paths? (No undefined behavior)
✓ Is the complexity bounded? (Max 1 million instructions)

If ANY check fails: program is rejected, never runs.

This is why you can load eBPF programs on production systems
without fear. The kernel itself guarantees they're safe.
```

> 💡 **Did You Know?** The eBPF verifier is so strict that it sometimes rejects valid programs that the human eye can see are safe. The Cilium team has contributed extensively to the Linux kernel to make the verifier smarter while maintaining safety. Writing eBPF programs that pass the verifier is an art—Cilium handles this complexity so you don't have to.

---

## Part 3: Cilium Architecture - The Big Picture

Now that you understand eBPF, let's see how Cilium uses it:

```
CILIUM: THE COMPLETE PICTURE
═══════════════════════════════════════════════════════════════════

                         ┌─────────────────────────────┐
                         │      KUBERNETES API         │
                         │  (Pods, Services, Policies) │
                         └──────────────┬──────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
           ┌────────▼────────┐ ┌────────▼────────┐ ┌───────▼────────┐
           │ CILIUM OPERATOR │ │  HUBBLE RELAY   │ │   HUBBLE UI    │
           │   (1 per cluster)│ │ (aggregation)   │ │ (visualization)│
           └─────────────────┘ └────────┬────────┘ └────────────────┘
                                        │
    ════════════════════════════════════╧════════════════════════════
                               PER-NODE COMPONENTS
    ═════════════════════════════════════════════════════════════════

    NODE 1                    NODE 2                    NODE 3
    ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐
    │   CILIUM AGENT      │  │   CILIUM AGENT      │  │   CILIUM AGENT   │
    │   ┌─────────────┐   │  │   ┌─────────────┐   │  │  ┌─────────────┐ │
    │   │   Policy    │   │  │   │   Policy    │   │  │  │   Policy    │ │
    │   │   Engine    │   │  │   │   Engine    │   │  │  │   Engine    │ │
    │   ├─────────────┤   │  │   ├─────────────┤   │  │  ├─────────────┤ │
    │   │  Identity   │   │  │   │  Identity   │   │  │  │  Identity   │ │
    │   │  Manager    │   │  │   │  Manager    │   │  │  │  Manager    │ │
    │   ├─────────────┤   │  │   ├─────────────┤   │  │  ├─────────────┤ │
    │   │   Hubble    │   │  │   │   Hubble    │   │  │  │   Hubble    │ │
    │   │  Observer   │   │  │   │  Observer   │   │  │  │  Observer   │ │
    │   └──────┬──────┘   │  │   └──────┬──────┘   │  │  └──────┬──────┘ │
    │          │          │  │          │          │  │         │        │
    │   ┌──────▼──────┐   │  │   ┌──────▼──────┐   │  │  ┌──────▼──────┐ │
    │   │    eBPF     │   │  │   │    eBPF     │   │  │  │    eBPF     │ │
    │   │  DATAPLANE  │   │  │   │  DATAPLANE  │   │  │  │  DATAPLANE  │ │
    │   │             │   │  │   │             │   │  │  │             │ │
    │   │ • Networking│   │  │   │ • Networking│   │  │  │ • Networking│ │
    │   │ • Policies  │   │  │   │ • Policies  │   │  │  │ • Policies  │ │
    │   │ • Load Bal. │   │  │   │ • Load Bal. │   │  │  │ • Load Bal. │ │
    │   │ • Encryption│   │  │   │ • Encryption│   │  │  │ • Encryption│ │
    │   └─────────────┘   │  │   └─────────────┘   │  │  └─────────────┘ │
    │                     │  │                     │  │                  │
    │  ┌──────┐ ┌──────┐  │  │  ┌──────┐ ┌──────┐  │  │ ┌──────┐┌──────┐│
    │  │Pod A │ │Pod B │  │  │  │Pod C │ │Pod D │  │  │ │Pod E ││Pod F ││
    │  │id=123│ │id=456│  │  │  │id=789│ │id=123│  │  │ │id=456││id=999││
    │  └──────┘ └──────┘  │  │  └──────┘ └──────┘  │  │ └──────┘└──────┘│
    └─────────────────────┘  └─────────────────────┘  └──────────────────┘
```

### The Components Explained (Like You're New Here)

**Cilium Agent (DaemonSet)** - The worker bee on each node:
- Watches Kubernetes for pod/service/policy changes
- Compiles eBPF programs and loads them into the kernel
- Assigns identities to pods (more on this soon)
- Runs Hubble observer for local visibility

**Cilium Operator** - The coordinator (1 per cluster):
- Manages IP address allocation (IPAM)
- Handles garbage collection of stale resources
- Manages CRDs and cluster-wide operations

**Hubble** - The observability layer:
- **Hubble (per-node)**: Captures flows from eBPF in real-time
- **Hubble Relay**: Aggregates flows from all nodes
- **Hubble UI**: Beautiful web interface for visualization

### Installation: Your First Cilium Cluster

```bash
# Step 1: Install Cilium CLI
# (The CLI makes installation and management much easier)
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --fail -o cilium-linux-amd64.tar.gz "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz"
sudo tar xzvfC cilium-linux-amd64.tar.gz /usr/local/bin
rm cilium-linux-amd64.tar.gz

# Step 2: Install Cilium with the good defaults
cilium install \
  --set kubeProxyReplacement=true \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

# Step 3: Wait for it to be ready
cilium status --wait

# Step 4: Verify everything works
cilium connectivity test
```

**What `cilium connectivity test` actually does:**

This isn't a simple ping test. It deploys test workloads and verifies:
- Pod-to-pod connectivity (same node and cross-node)
- Pod-to-Service connectivity
- Pod-to-external connectivity
- Network policies are enforced correctly
- DNS resolution works
- Hubble observability captures flows

If this test passes, your networking is solid. If it fails, you'll know exactly what's broken.

---

## Part 4: Identity-Based Security - The Game Changer

This is where Cilium fundamentally changes how you think about network security.

### The Problem with IPs

Remember this scenario?

```yaml
# You write a policy:
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
```

Behind the scenes, your CNI translates this to IP rules. Frontend pods have IPs 10.244.1.5 and 10.244.2.12, so the rule becomes "allow from 10.244.1.5 and 10.244.2.12."

Now frontend scales from 2 pods to 20 pods. Each new pod needs to be added. Pod crashes and restarts with new IP? Rule needs updating. Rolling deployment? Constant IP churn.

**Cilium throws this model away entirely.**

### How Cilium Identity Works

```
CILIUM IDENTITY: THE "AHA!" MOMENT
═══════════════════════════════════════════════════════════════════

Step 1: Pod is created with labels
┌─────────────────────────────────────────────────────────────────┐
│ Pod: frontend-7b9f8c4d5-x2k9p                                   │
│ Labels:                                                         │
│   app: frontend                                                 │
│   env: production                                               │
│   team: checkout                                                │
└─────────────────────────────────────────────────────────────────┘

Step 2: Cilium creates a NUMERIC IDENTITY from the labels
┌─────────────────────────────────────────────────────────────────┐
│ Identity 48291 = {app=frontend, env=production, team=checkout}  │
│                                                                 │
│ This identity is:                                               │
│ • Cluster-wide (same on all nodes)                              │
│ • Stable (doesn't change when pod restarts)                     │
│ • Shared (all pods with same labels = same identity)            │
└─────────────────────────────────────────────────────────────────┘

Step 3: Every packet carries the identity, NOT the IP
┌─────────────────────────────────────────────────────────────────┐
│  Network Packet                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Source Identity: 48291                                   │   │
│  │ Dest Identity: 73842                                     │   │
│  │ Payload: HTTP GET /api/checkout                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  The IP is still there for routing, but POLICY uses identity   │
└─────────────────────────────────────────────────────────────────┘

Step 4: Policy enforcement uses identity
┌─────────────────────────────────────────────────────────────────┐
│  eBPF Policy Check:                                             │
│                                                                 │
│  "Is identity 48291 allowed to reach identity 73842?"           │
│                                                                 │
│  Lookup in eBPF hash map: O(1) ← Constant time!                │
│  Answer: ALLOW or DENY                                          │
│                                                                 │
│  No IP lookups. No rule scanning. Instant decision.            │
└─────────────────────────────────────────────────────────────────┘
```

**Why this matters:**

1. **Pod restarts**: Same labels = same identity. No policy updates needed.
2. **Scaling**: 1 pod or 1000 pods with same labels = same identity. No rule explosion.
3. **Cross-cluster**: Identity follows the workload. Works in multi-cluster setups.
4. **Debugging**: "Who is identity 48291?" → `cilium identity get 48291` → Instant answer.

### Seeing Identities in Action

```bash
# List all identities in your cluster
cilium identity list

# Output:
# IDENTITY   LABELS
# 1          reserved:host
# 2          reserved:world
# 4          reserved:health
# 48291      k8s:app=frontend,k8s:env=production,k8s:team=checkout
# 73842      k8s:app=backend,k8s:env=production
# 99103      k8s:app=database,k8s:env=production

# Get details on a specific identity
cilium identity get 48291

# See which endpoints have this identity
kubectl exec -n kube-system cilium-xxxxx -- cilium endpoint list | grep 48291
```

> 💡 **Did You Know?** Cilium reserves identity numbers 1-255 for special purposes. Identity 1 is always the host (the node itself), identity 2 is "world" (anything external to the cluster), and identity 4 is for health checks. This means you can write policies like "allow health checks" without knowing which IP ranges your health checkers use. It's beautiful.

---

## Part 5: Network Policies - From Basic to "Wow"

### Standard Kubernetes NetworkPolicy (Cilium Implements These)

Cilium fully supports standard Kubernetes NetworkPolicies. If you have existing policies, they keep working:

```yaml
# Standard NetworkPolicy - Cilium handles this perfectly
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-allow-frontend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### CiliumNetworkPolicy - The Enhanced Version

This is where it gets interesting. Cilium extends NetworkPolicies with features Kubernetes doesn't support:

```yaml
# Layer 7 (HTTP) Policy - Kubernetes can't do this
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-http-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api-server
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        # Only allow specific HTTP methods and paths
        - method: "GET"
          path: "/api/v1/products.*"
        - method: "GET"
          path: "/api/v1/users/[0-9]+"
        - method: "POST"
          path: "/api/v1/orders"
          headers:
          - 'Content-Type: application/json'
```

**What this policy says in plain English:**

"Frontend pods can connect to the API server on port 8080, but ONLY for:
- GET requests to `/api/v1/products*` (list/view products)
- GET requests to `/api/v1/users/<id>` (view specific user)
- POST requests to `/api/v1/orders` with JSON content type (create orders)

Any other HTTP request? **DENIED at the network layer.**"

This is insanely powerful. An attacker who compromises your frontend can't hit `/api/v1/admin` or send DELETE requests—the network itself blocks them.

### DNS-Based Egress Policies

One of my favorite Cilium features. Most security teams want to control what external services pods can reach:

```yaml
# Allow pods to reach only specific external services
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: payment-egress
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: payment-processor
  egress:
  # Allow internal services
  - toEndpoints:
    - matchLabels:
        app: order-service
  # Allow specific external APIs
  - toFQDNs:
    - matchName: "api.stripe.com"
    - matchName: "api.paypal.com"
    - matchPattern: "*.amazonaws.com"  # AWS services
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
  # Allow DNS (required for FQDN resolution)
  - toEndpoints:
    - matchLabels:
        k8s:io.kubernetes.pod.namespace: kube-system
        k8s:k8s-app: kube-dns
    toPorts:
    - ports:
      - port: "53"
        protocol: UDP
```

**How FQDN policies work under the hood:**

```
FQDN POLICY MAGIC
═══════════════════════════════════════════════════════════════════

1. Policy says: "Allow egress to api.stripe.com"

2. Cilium intercepts DNS queries from the pod

3. Pod asks: "What's the IP of api.stripe.com?"

4. DNS responds: "It's 52.84.150.1, 52.84.150.2, 52.84.150.3"

5. Cilium automatically adds these IPs to the allow list
   (stored in eBPF maps for O(1) lookup)

6. Pod connects to 52.84.150.1:443 → ALLOWED

7. Later, Stripe changes IPs (they do this a lot)

8. Next DNS query returns new IPs

9. Cilium updates the allow list automatically

10. You never have to touch the policy!
```

No more hardcoding CIDR blocks that break when cloud providers change IPs. No more overly permissive "allow all egress to 0.0.0.0/0" rules.

### Cluster-Wide Policies

For policies that should apply everywhere (like "default deny"):

```yaml
# Default deny ALL traffic cluster-wide
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: default-deny
spec:
  endpointSelector: {}  # Applies to ALL pods
  ingress:
  - fromEndpoints:
    - {}  # Only allow from endpoints with Cilium identity
  egress:
  - toEndpoints:
    - {}
  # Always allow essential services
  - toEntities:
    - kube-apiserver  # Pods need to reach API server
    - dns             # Pods need DNS

---
# Explicitly allow health checks (they'd be denied by default-deny)
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-health-checks
spec:
  endpointSelector: {}
  ingress:
  - fromEntities:
    - health  # Cilium's reserved identity for health checks
```

**The power of `toEntities`:**

Instead of figuring out which IPs your kube-apiserver uses, which ports health checks come from, or which IPs your DNS servers have, Cilium provides semantic entities:

| Entity | What it means |
|--------|---------------|
| `host` | The node the pod runs on |
| `remote-node` | Other nodes in the cluster |
| `kube-apiserver` | Kubernetes API server |
| `health` | Health check probes |
| `dns` | DNS servers (kube-dns/CoreDNS) |
| `world` | Everything outside the cluster |

---

## Part 6: Hubble - Seeing the Invisible

If Cilium is the brain, Hubble is the eyes.

### The Old Way vs. The Hubble Way

```
DEBUGGING NETWORK ISSUES: OLD VS NEW
═══════════════════════════════════════════════════════════════════

THE OLD WAY:
───────────────────────────────────────────────────────────────────
1. Get alert: "Service unreachable"
2. SSH into pod: kubectl exec -it pod -- sh
3. Run tcpdump: tcpdump -i eth0 port 8080
4. Wait for traffic...
5. Stare at hex dumps
6. Realize you need tcpdump on the OTHER pod too
7. SSH into other pod
8. Run tcpdump there
9. Try to correlate timestamps across pods
10. Give up, ask network team
11. Network team says "network is fine"
12. Cry

THE HUBBLE WAY:
───────────────────────────────────────────────────────────────────
1. Get alert: "Service unreachable"
2. Run: hubble observe --from-pod web --to-pod api --verdict DROPPED
3. See exact policy that dropped the traffic
4. Fix policy
5. Go back to bed
```

### Installing and Accessing Hubble

```bash
# Install Hubble CLI
HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/main/stable.txt)
curl -L --fail -o hubble-linux-amd64.tar.gz "https://github.com/cilium/hubble/releases/download/${HUBBLE_VERSION}/hubble-linux-amd64.tar.gz"
sudo tar xzvfC hubble-linux-amd64.tar.gz /usr/local/bin
rm hubble-linux-amd64.tar.gz

# Port-forward to Hubble Relay (needed to aggregate from all nodes)
cilium hubble port-forward &

# Now you can use hubble observe
hubble observe

# Access the UI (optional but beautiful)
cilium hubble ui
# Opens browser to http://localhost:12000
```

### Hubble CLI - Your New Best Friend

```bash
# See ALL traffic in real-time
hubble observe

# Filter by namespace
hubble observe --namespace production

# Filter by specific pod
hubble observe --pod production/frontend-abc

# See only DROPPED traffic (the gold mine for debugging)
hubble observe --verdict DROPPED

# See traffic between two specific services
hubble observe \
  --from-pod production/frontend \
  --to-pod production/backend

# Filter by protocol
hubble observe --protocol http
hubble observe --protocol dns
hubble observe --protocol tcp

# See HTTP requests with details
hubble observe --protocol http -o json | jq

# See DNS queries
hubble observe --protocol dns --namespace production

# Output format options
hubble observe -o compact    # One line per flow
hubble observe -o dict       # Readable dictionary format
hubble observe -o json       # JSON for scripting
hubble observe -o table      # Table format
```

### Understanding Hubble Output

```
HUBBLE FLOW ANATOMY
═══════════════════════════════════════════════════════════════════

Dec  9 10:23:45.123  production/frontend-7b9f8c4d5-x2k9p:46532 (ID:48291)
                     -> production/backend-5d8f7b3a2-k9p2m:8080 (ID:73842)
                     http-request FORWARDED (HTTP/1.1 GET /api/users)

Let's break this down:
───────────────────────────────────────────────────────────────────

TIMESTAMP           SOURCE
Dec  9 10:23:45.123 production/frontend-7b9f8c4d5-x2k9p:46532 (ID:48291)
                    │            │                    │      │   │
                    namespace    pod name             port   │   └─ Cilium identity!
                                                            └─ source port

                    DESTINATION
                    -> production/backend-5d8f7b3a2-k9p2m:8080 (ID:73842)
                       │          │                     │      │
                       namespace  pod name              port   └─ Cilium identity

                    FLOW TYPE & VERDICT
                    http-request FORWARDED (HTTP/1.1 GET /api/users)
                    │            │          │
                    protocol     │          └─ HTTP details (method, path)
                                 └─ FORWARDED = allowed
                                    DROPPED = blocked by policy
                                    ERROR = something went wrong
```

### Real Debugging Scenarios

**Scenario 1: "My pod can't reach the database"**

```bash
# Step 1: See what's being dropped
hubble observe \
  --from-pod production/myapp \
  --to-pod production/postgres \
  --verdict DROPPED

# Output:
# production/myapp-xxx -> production/postgres-yyy
# policy-verdict:none DROPPED (Policy denied)

# The "policy-verdict:none" tells you there's no ALLOW rule
# You need to add a policy to permit this traffic
```

**Scenario 2: "External API calls are failing"**

```bash
# Check egress traffic
hubble observe \
  --from-pod production/myapp \
  --verdict DROPPED \
  --type l3/l4

# Output:
# production/myapp-xxx -> 52.84.150.1:443
# policy-verdict:none DROPPED (Policy denied)

# Your egress policy doesn't allow this IP
# Check if you need to add FQDN rules
```

**Scenario 3: "DNS is slow/failing"**

```bash
# Watch DNS queries
hubble observe --protocol dns --namespace production

# Output:
# production/myapp -> kube-system/coredns
# dns-request FORWARDED (Query api.stripe.com A)
# kube-system/coredns -> production/myapp
# dns-response FORWARDED (Answer: 52.84.150.1)

# If you see DROPPED DNS queries, check your egress policies
```

### Hubble Metrics for Prometheus

```bash
# Enable metrics during Cilium install
cilium install \
  --set hubble.enabled=true \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}"

# Or upgrade existing installation
cilium upgrade \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}"
```

Key metrics to alert on:

```yaml
# Prometheus alert examples
groups:
- name: cilium
  rules:
  # Alert on packet drops (excluding expected drops)
  - alert: HighPacketDropRate
    expr: rate(hubble_drop_total{reason!="Policy denied"}[5m]) > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High packet drop rate on {{ $labels.instance }}"

  # Alert on DNS failures
  - alert: DNSErrors
    expr: rate(hubble_dns_responses_total{rcode!="No Error"}[5m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "DNS errors detected: {{ $labels.rcode }}"

  # Alert on HTTP 5xx errors
  - alert: HTTP5xxErrors
    expr: rate(hubble_http_responses_total{status=~"5.."}[5m]) > 10
    for: 5m
    labels:
      severity: critical
```

> 💡 **Did You Know?** Hubble captures flows using eBPF, which means there's no sampling. Unlike traditional monitoring that might capture 1 in 1000 packets, Hubble sees EVERY packet. If something happened on the network, Hubble saw it. This makes Hubble invaluable for security auditing—you have a complete record of all network communication.

---

## Part 7: Replacing Kube-Proxy

### Why This Matters

Remember those 147,000 iptables rules? Let's get rid of them.

```bash
# Install Cilium as kube-proxy replacement
cilium install --set kubeProxyReplacement=true

# Verify it's working
cilium status | grep KubeProxyReplacement
# KubeProxyReplacement:   True [eth0 (Direct Routing)]

# See all Services handled by Cilium
kubectl exec -n kube-system ds/cilium -- cilium service list

# Compare the difference:
# BEFORE (kube-proxy):
# iptables-save | wc -l
# 147,291

# AFTER (Cilium):
# iptables-save | wc -l
# 127  ← Only basic rules remain
```

### Performance Comparison

Real benchmarks from production clusters:

| Metric | kube-proxy (iptables) | Cilium eBPF | Improvement |
|--------|----------------------|-------------|-------------|
| Service lookup latency | ~2ms (5000 services) | ~100μs | **20x faster** |
| Memory usage | Grows with services | Constant | **Predictable** |
| Rule update time | 5-30 seconds | Milliseconds | **1000x faster** |
| Connection drops on update | Yes | No | **Zero downtime** |
| CPU usage at scale | High | Low | **50-70% reduction** |

### The DSR Bonus: Direct Server Return

```
DIRECT SERVER RETURN (DSR)
═══════════════════════════════════════════════════════════════════

Without DSR (traditional):
───────────────────────────────────────────────────────────────────
Client → Load Balancer → Backend Pod
Client ← Load Balancer ← Backend Pod
                ↑
        Return traffic goes through LB too
        (extra hop, extra latency)

With DSR (Cilium):
───────────────────────────────────────────────────────────────────
Client → Load Balancer → Backend Pod
Client ←──────────────── Backend Pod
                         ↑
        Return traffic goes DIRECTLY to client
        (faster response, less LB load)
```

Enable DSR:

```bash
cilium install \
  --set kubeProxyReplacement=true \
  --set loadBalancer.mode=dsr
```

---

## Part 8: Transparent Encryption with WireGuard

Encrypting all pod-to-pod traffic sounds hard. With Cilium, it's one flag.

### The Problem

```
UNENCRYPTED CLUSTER TRAFFIC
═══════════════════════════════════════════════════════════════════

Pod A ─────────────────────────────────────────────▶ Pod B
         │                                    │
         │  Network traffic crosses:          │
         │  • Virtual switches               │
         │  • Physical switches              │
         │  • Sometimes public internet      │
         │    (cross-AZ, cross-region)       │
         │                                    │
         └──── All visible to anyone ─────────┘
              with network access

Attackers can:
• Read sensitive data
• Capture credentials
• Man-in-the-middle attacks
```

### The Solution

```bash
# Enable WireGuard encryption
cilium install \
  --set encryption.enabled=true \
  --set encryption.type=wireguard

# Verify encryption status
cilium status | grep Encryption
# Encryption: Wireguard [NodeEncryption: Disabled, cilium_wg0 (Pubkey: xxx)]

# Check WireGuard peers
kubectl exec -n kube-system ds/cilium -- cilium encrypt status
```

What happens now:

```
ENCRYPTED CLUSTER TRAFFIC
═══════════════════════════════════════════════════════════════════

Pod A ══════════════════════════════════════════════▶ Pod B
         │                                    │
         │  All traffic encrypted with        │
         │  WireGuard (state-of-art crypto)   │
         │                                    │
         │  • No app changes needed           │
         │  • No sidecar containers           │
         │  • Kernel-level encryption         │
         │  • ~5% overhead (negligible)       │
         │                                    │
         └──── Attackers see garbage ─────────┘
```

**Zero application changes.** Your apps don't know encryption is happening. It's transparent at the kernel level.

---

## Part 9: Common Mistakes (Learn From Others' Pain)

| Mistake | Why It Hurts | How To Avoid |
|---------|--------------|--------------|
| **Skipping connectivity test** | You think it's working, it's not | Always run `cilium connectivity test` after install |
| **Installing over existing CNI** | CNI conflicts break everything | Remove old CNI completely first, or use fresh cluster |
| **No default deny** | Wide open by default = security hole | Always set cluster-wide default deny |
| **Forgetting DNS in egress** | Pods can't resolve external hosts | Always allow `toEntities: [dns]` in egress policies |
| **Overly broad FQDN patterns** | `*.com` defeats the purpose | Use specific FQDNs: `api.stripe.com` not `*.stripe.com` |
| **Not enabling Hubble** | Flying blind | Hubble is free, always enable it |
| **Ignoring Hubble metrics** | Miss issues until they're incidents | Alert on `hubble_drop_total` and `hubble_dns_*` |

---

## War Story: The Policy That Ate Christmas

*December 23rd, 2022. Large e-commerce platform. Black Friday went perfectly. Everyone was relaxed.*

At 2:47 PM, a junior engineer deployed what seemed like a simple change: a new CiliumNetworkPolicy to restrict database access. The policy worked in staging.

```yaml
# The policy that ruined Christmas
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: database-security
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: postgres
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: backend
        environment: production
```

**What they missed:** The caching service (Redis) also needed database access. It had `app: cache`, not `app: backend`.

At 2:48 PM:
- Cache invalidation failed
- Stale product data started serving
- Wrong prices shown to customers

At 2:52 PM:
- Monitoring detected increased error rates
- On-call engineer paged

At 2:54 PM:
- Engineer ran: `hubble observe --to-pod production/postgres --verdict DROPPED`
- Output showed: `production/redis-xxx -> production/postgres DROPPED`
- Root cause identified in **2 minutes**

At 2:56 PM:
- Policy updated to include cache service
- Traffic restored

**Total incident duration: 8 minutes**

Without Hubble? This would've been a multi-hour outage. The team would've blamed DNS (it's always DNS), then the load balancer, then the database itself. Eventually, maybe, someone would've checked network policies.

**Lessons:**
1. Always test policies against ALL services, not just the obvious ones
2. Hubble is not optional—it's your incident response tool
3. `--verdict DROPPED` is the most important filter you'll ever use

---

## Quiz

### Question 1
You deploy a default-deny policy and suddenly nothing works. Not even DNS. What's the minimum policy you need to restore basic functionality?

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-essential
spec:
  endpointSelector: {}
  egress:
  - toEntities:
    - dns           # Allows CoreDNS queries
    - kube-apiserver # Allows pods to reach API server
  ingress:
  - fromEntities:
    - health        # Allows health probes
```

This restores:
- DNS resolution (pods can resolve names)
- API server access (service accounts work)
- Health checks (probes don't fail)

From here, add specific policies for your workloads.

</details>

### Question 2
A pod is failing to connect to `api.stripe.com`. How do you debug this with Hubble?

<details>
<summary>Show Answer</summary>

```bash
# Step 1: Check if connection attempts are being dropped
hubble observe \
  --from-pod production/payment-service \
  --verdict DROPPED

# Step 2: Check DNS is resolving
hubble observe \
  --from-pod production/payment-service \
  --protocol dns

# Step 3: Check specific destination
hubble observe \
  --from-pod production/payment-service \
  --to-fqdn api.stripe.com

# Common issues:
# - DNS queries dropped → Add toEntities: [dns] to egress
# - Connection dropped → Add toFQDNs with matchName: api.stripe.com
# - Policy denied → Check your CiliumNetworkPolicy
```

</details>

### Question 3
Why does Cilium use identity numbers instead of IP addresses for policy enforcement?

<details>
<summary>Show Answer</summary>

**IP-based problems:**
- Pods get new IPs when restarting
- Scaling creates new IPs constantly
- Rolling updates = continuous IP churn
- Policies must be updated for every IP change
- Can't express "frontend talks to backend" semantically

**Identity-based advantages:**
- Identity is based on labels, not IPs
- Same labels = same identity, regardless of IP
- 1 pod or 1000 pods = same identity if labels match
- Policies are stable (no updates needed when IPs change)
- Human-readable: "identity 48291 = frontend" makes sense
- O(1) lookup in eBPF hash maps

**Example:**
```
Pod with labels {app: frontend, env: prod} → Identity 48291

This pod can:
- Restart 100 times
- Scale to 50 replicas
- Move across nodes

Identity stays 48291. Policies keep working.
```

</details>

---

## Hands-On Exercise: Build a Secure Microservices Setup

### Objective
Deploy a three-tier application with Cilium, implement zero-trust networking, and observe traffic with Hubble.

### Scenario
You're deploying a web application with:
- **Frontend**: Nginx serving static content
- **API**: Node.js backend
- **Database**: PostgreSQL

Security requirements:
1. Default deny all traffic
2. Frontend can only reach API on port 3000
3. API can only reach database on port 5432
4. All pods can reach DNS
5. No direct frontend-to-database access

### Part 1: Setup the Cluster

```bash
# Create a kind cluster without default CNI
cat > kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  kubeProxyMode: none
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

kind create cluster --config kind-config.yaml --name cilium-lab

# Install Cilium
cilium install \
  --set kubeProxyReplacement=true \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

# Wait for Cilium to be ready
cilium status --wait

# Verify installation
cilium connectivity test
```

### Part 2: Deploy the Application

```bash
# Create namespace
kubectl create namespace demo

# Deploy database
kubectl -n demo apply -f - << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: database
  labels:
    app: database
    tier: data
spec:
  containers:
  - name: postgres
    image: postgres:15
    env:
    - name: POSTGRES_PASSWORD
      value: "secret"
    ports:
    - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: database
spec:
  selector:
    app: database
  ports:
  - port: 5432
EOF

# Deploy API
kubectl -n demo apply -f - << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: api
  labels:
    app: api
    tier: backend
spec:
  containers:
  - name: api
    image: nginx
    ports:
    - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
  - port: 3000
EOF

# Deploy frontend
kubectl -n demo apply -f - << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: frontend
  labels:
    app: frontend
    tier: web
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
EOF
```

### Part 3: Test Without Policies (Everything Works)

```bash
# Start Hubble port-forward in background
cilium hubble port-forward &

# Test frontend → api (should work)
kubectl -n demo exec frontend -- curl -s --max-time 5 api:3000
echo "Frontend → API: SUCCESS"

# Test frontend → database (should also work - this is the problem!)
kubectl -n demo exec frontend -- nc -zv database 5432
echo "Frontend → Database: SUCCESS (but shouldn't be allowed!)"

# Test api → database (should work)
kubectl -n demo exec api -- nc -zv database 5432
echo "API → Database: SUCCESS"

# Watch traffic with Hubble
hubble observe --namespace demo
```

### Part 4: Implement Zero-Trust Policies

```bash
# Step 1: Default deny everything
kubectl -n demo apply -f - << 'EOF'
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: default-deny
spec:
  endpointSelector: {}
  ingress: []
  egress: []
EOF

# Test again - everything should fail now
kubectl -n demo exec frontend -- curl -s --max-time 5 api:3000 || echo "Frontend → API: BLOCKED (expected)"
kubectl -n demo exec api -- nc -zv -w 2 database 5432 || echo "API → Database: BLOCKED (expected)"

# Watch the drops!
hubble observe --namespace demo --verdict DROPPED
```

```bash
# Step 2: Allow DNS (required for name resolution)
kubectl -n demo apply -f - << 'EOF'
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-dns
spec:
  endpointSelector: {}
  egress:
  - toEntities:
    - dns
EOF

# Step 3: Allow frontend → api
kubectl -n demo apply -f - << 'EOF'
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: frontend-to-api
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "3000"
---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: frontend-egress
spec:
  endpointSelector:
    matchLabels:
      app: frontend
  egress:
  - toEndpoints:
    - matchLabels:
        app: api
    toPorts:
    - ports:
      - port: "3000"
EOF

# Step 4: Allow api → database
kubectl -n demo apply -f - << 'EOF'
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-to-database
spec:
  endpointSelector:
    matchLabels:
      app: database
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: api
    toPorts:
    - ports:
      - port: "5432"
---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-egress
spec:
  endpointSelector:
    matchLabels:
      app: api
  egress:
  - toEndpoints:
    - matchLabels:
        app: database
    toPorts:
    - ports:
      - port: "5432"
EOF
```

### Part 5: Verify Security

```bash
# Frontend → API: Should work
kubectl -n demo exec frontend -- curl -s --max-time 5 api:3000
echo "✓ Frontend → API: ALLOWED"

# API → Database: Should work
kubectl -n demo exec api -- nc -zv -w 2 database 5432
echo "✓ API → Database: ALLOWED"

# Frontend → Database: Should be BLOCKED
kubectl -n demo exec frontend -- nc -zv -w 2 database 5432 || echo "✓ Frontend → Database: BLOCKED (as intended!)"

# Watch the flow in Hubble
hubble observe --namespace demo

# See what's being dropped
hubble observe --namespace demo --verdict DROPPED
```

### Success Criteria

- [ ] Cilium installed and connectivity test passes
- [ ] Default deny policy blocks all traffic
- [ ] Hubble shows DROPPED verdict for blocked traffic
- [ ] Frontend can reach API on port 3000
- [ ] API can reach Database on port 5432
- [ ] Frontend CANNOT reach Database directly
- [ ] Hubble shows FORWARDED for allowed traffic

### Bonus Challenge

Add an L7 policy that only allows HTTP GET requests from frontend to api:

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: frontend-to-api-l7
  namespace: demo
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "3000"
      rules:
        http:
        - method: "GET"
          path: "/.*"
```

Test that POST requests are blocked:
```bash
kubectl -n demo exec frontend -- curl -X POST api:3000 || echo "POST blocked by L7 policy"
kubectl -n demo exec frontend -- curl -X GET api:3000 && echo "GET allowed"
```

---

## Cleanup

```bash
# Delete the lab cluster
kind delete cluster --name cilium-lab
```

---

## Further Reading

- [Cilium Documentation](https://docs.cilium.io/) - The official docs, well-written
- [eBPF.io](https://ebpf.io/) - Deep dive into eBPF technology
- [Cilium Network Policy Editor](https://editor.cilium.io/) - Visual policy builder (great for learning)
- [Hubble Documentation](https://docs.cilium.io/en/stable/observability/hubble/)
- [Isovalent Blog](https://isovalent.com/blog/) - Advanced Cilium use cases from the creators

---

## Next Module

Continue to [Module 5.2: Service Mesh](module-5.2-service-mesh/) to learn about service mesh patterns with Istio, and when sidecar-free approaches make sense.

---

*"The network that explains itself is the network you can actually secure."*
