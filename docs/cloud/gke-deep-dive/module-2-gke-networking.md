# GKE Networking: Dataplane V2 and Gateway API
**Complexity**: [COMPLEX] | **Time to Complete**: 3h | **Prerequisites**: Module 1 (GKE Architecture)

## Why This Module Matters

In September 2023, a healthcare SaaS company running on GKE discovered that their network policies were not being enforced. A penetration tester demonstrated that a compromised pod in the `staging` namespace could freely communicate with pods in the `production` namespace, despite NetworkPolicy resources that should have blocked cross-namespace traffic. The root cause: the cluster was using the legacy iptables-based kube-proxy dataplane, which does not enforce Kubernetes NetworkPolicy at all. The team had assumed that creating NetworkPolicy resources was sufficient---they did not realize that enforcement requires a CNI that supports it. The compliance violation cost them a SOC 2 audit failure, delaying a $2.3 million enterprise deal by four months. The fix took 30 minutes: enable Dataplane V2 on their next cluster creation. The business impact lasted a quarter.

GKE networking is where Kubernetes meets Google's global network infrastructure. The decisions you make about cluster networking---VPC-native mode, Dataplane V2, load balancing strategy, and Gateway API configuration---determine your application's performance, security, and cost. A misconfigured network can leave your pods exposed, introduce unnecessary latency, or rack up egress charges that dwarf your compute costs.

In this module, you will learn how VPC-native clusters use alias IPs to give pods routable addresses, how Dataplane V2 replaces iptables with eBPF for faster and more observable networking, how Cloud Load Balancing integrates with GKE, and how the Gateway API provides a more expressive routing model than Ingress. By the end, you will configure Dataplane V2 network policies and set up a Gateway API canary deployment.

---

## VPC-Native Clusters and Alias IPs

Every modern GKE cluster should be VPC-native. This is the default since GKE 1.21 and is required for features like Dataplane V2, Private Google Access for pods, and VPC flow logs for pod traffic.

### How Alias IPs Work

In a VPC-native cluster, each node receives a **primary IP** from the subnet and a **secondary IP range** (alias range) for its pods. This means pods get IP addresses that are routable within the VPC---no NAT, no overlay network.

```text
  VPC: 10.0.0.0/16
  ┌────────────────────────────────────────────────────────┐
  │                                                        │
  │  Subnet: 10.0.0.0/24 (Node IPs)                      │
  │  ┌─────────────────┐  ┌─────────────────┐            │
  │  │ Node A           │  │ Node B           │            │
  │  │ IP: 10.0.0.2     │  │ IP: 10.0.0.3     │            │
  │  │                   │  │                   │            │
  │  │ Alias: 10.4.0.0  │  │ Alias: 10.4.1.0  │            │
  │  │   /24 (pods)      │  │   /24 (pods)      │            │
  │  │ ┌────┐ ┌────┐    │  │ ┌────┐ ┌────┐    │            │
  │  │ │Pod │ │Pod │    │  │ │Pod │ │Pod │    │            │
  │  │ │.2  │ │.3  │    │  │ │.5  │ │.8  │    │            │
  │  │ └────┘ └────┘    │  │ └────┘ └────┘    │            │
  │  └─────────────────┘  └─────────────────┘            │
  │                                                        │
  │  Secondary Range "pods": 10.4.0.0/14                  │
  │  Secondary Range "services": 10.8.0.0/20              │
  └────────────────────────────────────────────────────────┘
```

### Why This Matters for Networking

| Feature | VPC-Native (Alias IPs) | Routes-Based (Legacy) |
| :--- | :--- | :--- |
| **Pod IPs routable in VPC** | Yes (directly) | No (requires custom routes) |
| **Max pods per cluster** | Limited by IP range size | Limited to 300 custom routes |
| **Network Policy support** | Full (Dataplane V2) | Limited |
| **Private Google Access for pods** | Yes | No |
| **VPC Flow Logs for pods** | Yes | No |
| **Peering/VPN compatibility** | Full | Route export required |

```bash
# Verify your cluster is VPC-native
gcloud container clusters describe my-cluster \
  --region=us-central1 \
  --format="yaml(ipAllocationPolicy)"

# Expected output includes:
#   useIpAliases: true
#   clusterSecondaryRangeName: pods
#   servicesSecondaryRangeName: services
```

### IP Address Planning

Poor IP planning is the number one networking regret for teams that scale. You cannot resize secondary ranges after cluster creation.

```text
  Planning Guide:
  ┌──────────────────────────────────────────────────────┐
  │  Each node gets a /24 from the pod range by default  │
  │  = 256 IPs per node (110 pods max + overhead)        │
  │                                                      │
  │  For 100 nodes: you need 100 x /24 = /17 minimum    │
  │  For 500 nodes: you need 500 x /24 = /15 minimum    │
  │                                                      │
  │  Services range:                                     │
  │  /20 = 4,096 services (usually sufficient)           │
  │  /16 = 65,536 services (very large clusters)         │
  └──────────────────────────────────────────────────────┘
```

```bash
# Create a cluster with explicit IP planning for scale
gcloud container clusters create large-cluster \
  --region=us-central1 \
  --num-nodes=2 \
  --network=prod-vpc \
  --subnetwork=gke-subnet \
  --cluster-secondary-range-name=gke-pods \
  --services-secondary-range-name=gke-services \
  --enable-ip-alias \
  --max-pods-per-node=64 \
  --default-max-pods-per-node=64

# Reducing max-pods-per-node from 110 to 64 means each node
# needs a /26 instead of a /24, saving IP space
```

---

## Dataplane V2: eBPF-Powered Networking

Dataplane V2 is GKE's modern networking stack, built on **Cilium** and **eBPF**. It replaces the traditional kube-proxy + iptables approach with a programmable, kernel-level dataplane.

### Why eBPF Changes Everything

Traditional Kubernetes networking uses iptables rules for service routing and kube-proxy for load balancing. This works, but it has fundamental limitations:

```text
  Legacy (iptables/kube-proxy):
  ┌─────────────────────────────────────────────────────┐
  │  Packet arrives at node                             │
  │       │                                             │
  │       ▼                                             │
  │  iptables chain (linear scan)                       │
  │  Rule 1: no match                                   │
  │  Rule 2: no match                                   │
  │  Rule 3: no match                                   │
  │  ...                                                │
  │  Rule 5,000: MATCH → DNAT to pod IP                │
  │       │                                             │
  │  O(n) performance: more services = slower routing   │
  └─────────────────────────────────────────────────────┘

  Dataplane V2 (eBPF):
  ┌─────────────────────────────────────────────────────┐
  │  Packet arrives at node                             │
  │       │                                             │
  │       ▼                                             │
  │  eBPF hash map lookup                               │
  │  Key: {dest IP, dest port}                          │
  │  Value: backend pod IP                              │
  │       │                                             │
  │  O(1) performance: constant time regardless of      │
  │  number of services                                 │
  └─────────────────────────────────────────────────────┘
```

### Dataplane V2 Benefits

| Capability | iptables/kube-proxy | Dataplane V2 |
| :--- | :--- | :--- |
| **Service routing** | O(n) linear scan | O(1) hash lookup |
| **Network Policy enforcement** | Requires Calico add-on | Built-in (Cilium) |
| **Network Policy logging** | Not available | Built-in |
| **Kernel bypass** | No | Yes (XDP for some paths) |
| **Observability** | Basic conntrack | Rich eBPF flow logs |
| **Scale limit** | ~5,000 services practical | 25,000+ services tested |
| **FQDN-based policies** | Not supported | Supported |

### Enabling Dataplane V2

```bash
# Dataplane V2 is enabled at cluster creation time
gcloud container clusters create dpv2-cluster \
  --region=us-central1 \
  --num-nodes=2 \
  --enable-dataplane-v2 \
  --enable-ip-alias \
  --release-channel=regular

# For Autopilot clusters, Dataplane V2 is enabled by default
gcloud container clusters create-auto dpv2-autopilot \
  --region=us-central1

# Verify Dataplane V2 is active
kubectl -n kube-system get pods -l k8s-app=cilium -o wide
```

### Network Policies with Dataplane V2

With Dataplane V2, NetworkPolicy resources are enforced without any additional CNI installation. This is the feature that the healthcare company in our opening story was missing.

```yaml
# Deny all ingress to production namespace by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress

---
# Allow only the API gateway to reach backend pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-gateway
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          role: gateway
      podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080

---
# Allow DNS resolution for all pods (critical, often forgotten)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

### Network Policy Logging

Dataplane V2 can log allowed and denied connections, which is invaluable for debugging and compliance.

```bash
# Enable network policy logging on the cluster
gcloud container clusters update dpv2-cluster \
  --region=us-central1 \
  --enable-network-policy-logging

# View logs in Cloud Logging
gcloud logging read \
  'resource.type="k8s_node" AND jsonPayload.disposition="deny"' \
  --limit=10 \
  --format="table(timestamp, jsonPayload.src.pod_name, jsonPayload.dest.pod_name, jsonPayload.disposition)"
```

**War Story**: A platform team enabled network policy logging and discovered that their monitoring agent (Datadog) was making 3,000 denied connections per minute to pods in restricted namespaces. The agent had broad scrape targets configured, and every denied connection generated a log entry. Before enabling logging in production, test in a staging environment to understand the log volume---it can be surprisingly high.

---

## Cloud Load Balancing Integration

GKE integrates tightly with Google Cloud Load Balancing. When you create a Kubernetes Service or Ingress, GKE provisions the corresponding Google Cloud load balancer components automatically.

### Service Types and Their Load Balancers

```text
  Kubernetes Concept          GCP Resource Created
  ─────────────────          ────────────────────
  Service type: ClusterIP  → Nothing (internal only)
  Service type: NodePort   → Nothing (opens port on nodes)
  Service type: LoadBalancer → Network Load Balancer (L4)
  Ingress (external)        → Application Load Balancer (L7)
  Gateway (external)        → Application Load Balancer (L7)
```

| Service Type | Layer | Scope | Use Case |
| :--- | :--- | :--- | :--- |
| **LoadBalancer** | L4 (TCP/UDP) | Regional (default) | Non-HTTP, gRPC without path routing |
| **Ingress** (GKE Ingress) | L7 (HTTP/S) | Global | HTTP routing with host/path rules |
| **Gateway** (Gateway API) | L7 (HTTP/S) | Global or Regional | Modern alternative to Ingress |
| **Internal LoadBalancer** | L4 | Regional | Internal services, not internet-facing |
| **Internal Ingress** | L7 | Regional | Internal HTTP routing |

### External Network Load Balancer (L4)

```yaml
# Simple L4 load balancer
apiVersion: v1
kind: Service
metadata:
  name: game-server
spec:
  type: LoadBalancer
  selector:
    app: game-server
  ports:
  - port: 7777
    targetPort: 7777
    protocol: UDP
```

```bash
# Check the provisioned load balancer
kubectl get svc game-server -o wide
# The EXTERNAL-IP column shows the Google Cloud LB IP

# View the underlying GCP forwarding rule
gcloud compute forwarding-rules list \
  --filter="description~game-server"
```

### GKE Ingress (L7)

GKE Ingress creates a Google Cloud Application Load Balancer (formerly HTTP(S) Load Balancer) with features like SSL termination, URL-based routing, and Cloud CDN integration.

```yaml
# Multi-service Ingress with path-based routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    kubernetes.io/ingress.global-static-ip-name: web-static-ip
    networking.gke.io/managed-certificates: web-cert
    kubernetes.io/ingress.class: gce
spec:
  defaultBackend:
    service:
      name: frontend
      port:
        number: 80
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: api-service
            port:
              number: 8080
      - path: /static/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: static-assets
            port:
              number: 80
```

---

## Gateway API: The Future of Kubernetes Routing

The Gateway API is a Kubernetes-native evolution of Ingress that provides richer routing capabilities, better role separation, and a more consistent experience across implementations. GKE fully supports the Gateway API and it is the recommended approach for new deployments.

### Why Gateway API Over Ingress

```text
  Ingress Model (flat):
  ┌──────────────────────────────────────┐
  │  Ingress Resource                    │
  │  (mixes infra config + routing)      │
  │                                      │
  │  - TLS config (infra team concern)   │
  │  - Host rules (app team concern)     │
  │  - Path rules (app team concern)     │
  │  - Backend refs (app team concern)   │
  │                                      │
  │  ONE resource, ONE owner = conflict  │
  └──────────────────────────────────────┘

  Gateway API Model (layered):
  ┌──────────────────────────────────────┐
  │  GatewayClass (cluster admin)        │
  │  "Which load balancer implementation"│
  └──────────────┬───────────────────────┘
                 │
  ┌──────────────▼───────────────────────┐
  │  Gateway (infra/platform team)       │
  │  "Listener config, TLS, IP address"  │
  └──────────────┬───────────────────────┘
                 │
  ┌──────────────▼───────────────────────┐
  │  HTTPRoute (app team)                │
  │  "Host matching, path routing,       │
  │   headers, canary weights"           │
  └──────────────────────────────────────┘
```

### GKE Gateway Classes

GKE provides several pre-installed GatewayClasses:

| GatewayClass | Load Balancer Type | Scope | Use Case |
| :--- | :--- | :--- | :--- |
| `gke-l7-global-external-managed` | Global external ALB | Global | Public-facing web apps |
| `gke-l7-regional-external-managed` | Regional external ALB | Regional | Region-specific apps |
| `gke-l7-rilb` | Regional internal ALB | Regional | Internal microservices |
| `gke-l7-gxlb` | Classic global external ALB | Global | Legacy, avoid for new |

```bash
# List available GatewayClasses in your cluster
kubectl get gatewayclass

# Enable the Gateway API on an existing cluster
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --gateway-api=standard
```

### Setting Up a Gateway

```yaml
# Step 1: Create the Gateway (platform/infra team)
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: external-gateway
  namespace: infra
spec:
  gatewayClassName: gke-l7-global-external-managed
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - kind: Secret
        name: tls-cert
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            gateway-access: "true"
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            gateway-access: "true"
```

```yaml
# Step 2: Create an HTTPRoute (app team)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: store-route
  namespace: store
  labels:
    gateway: external-gateway
spec:
  parentRefs:
  - kind: Gateway
    name: external-gateway
    namespace: infra
  hostnames:
  - "store.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: store-api
      port: 8080
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: store-frontend
      port: 80
```

### Canary Deployments with Gateway API

The Gateway API natively supports traffic splitting by weight---something that required Istio or custom annotations with Ingress.

```yaml
# Canary: send 90% to stable, 10% to canary
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: store-api-canary
  namespace: store
spec:
  parentRefs:
  - kind: Gateway
    name: external-gateway
    namespace: infra
  hostnames:
  - "store.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: store-api-stable
      port: 8080
      weight: 90
    - name: store-api-canary
      port: 8080
      weight: 10
```

To gradually shift traffic, update the weights:

```bash
# Move to 50/50
kubectl patch httproute store-api-canary -n store --type=merge -p '{
  "spec": {
    "rules": [{
      "matches": [{"path": {"type": "PathPrefix", "value": "/api"}}],
      "backendRefs": [
        {"name": "store-api-stable", "port": 8080, "weight": 50},
        {"name": "store-api-canary", "port": 8080, "weight": 50}
      ]
    }]
  }
}'

# Promote canary to 100%
kubectl patch httproute store-api-canary -n store --type=merge -p '{
  "spec": {
    "rules": [{
      "matches": [{"path": {"type": "PathPrefix", "value": "/api"}}],
      "backendRefs": [
        {"name": "store-api-canary", "port": 8080, "weight": 100}
      ]
    }]
  }
}'
```

### Header-Based Routing

Gateway API also supports routing based on HTTP headers, which is useful for testing in production.

```yaml
# Route requests with X-Canary: true header to canary service
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: store-api-header-routing
  namespace: store
spec:
  parentRefs:
  - kind: Gateway
    name: external-gateway
    namespace: infra
  hostnames:
  - "store.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
      headers:
      - name: X-Canary
        value: "true"
    backendRefs:
    - name: store-api-canary
      port: 8080
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: store-api-stable
      port: 8080
```

---

## Private Service Connect for GKE

Private Service Connect (PSC) allows you to access the GKE control plane through a private endpoint within your VPC, eliminating exposure to the public internet.

```bash
# Create a private cluster with PSC
gcloud container clusters create private-cluster \
  --region=us-central1 \
  --num-nodes=1 \
  --enable-private-nodes \
  --enable-private-endpoint \
  --master-ipv4-cidr=172.16.0.0/28 \
  --enable-ip-alias \
  --enable-master-authorized-networks \
  --master-authorized-networks=10.0.0.0/8

# With PSC (newer approach, recommended):
gcloud container clusters create psc-cluster \
  --region=us-central1 \
  --num-nodes=1 \
  --enable-private-nodes \
  --private-endpoint-subnetwork=psc-subnet \
  --enable-ip-alias
```

```text
  Private Cluster with PSC:
  ┌─────────────────────────────────────────────────────┐
  │  Google-Managed VPC                                 │
  │  ┌─────────────────────────────────────┐           │
  │  │  GKE Control Plane                  │           │
  │  │  (API Server, etcd, etc.)           │           │
  │  └──────────────┬──────────────────────┘           │
  │                 │ Private Service Connect           │
  └─────────────────┼───────────────────────────────────┘
                    │
  ┌─────────────────▼───────────────────────────────────┐
  │  Customer VPC                                       │
  │  ┌──────────────────┐                              │
  │  │  PSC Endpoint     │  ← Private IP in your VPC   │
  │  │  10.0.5.2         │     for control plane access │
  │  └──────────────────┘                              │
  │                                                     │
  │  ┌──────────────────┐                              │
  │  │  GKE Nodes        │  ← No public IPs            │
  │  │  10.0.0.0/24      │                              │
  │  └──────────────────┘                              │
  └─────────────────────────────────────────────────────┘
```

### Private Cluster Considerations

| Consideration | Impact | Solution |
| :--- | :--- | :--- |
| Nodes cannot pull from internet | Container images fail | Use Artifact Registry (in same region) or configure Cloud NAT |
| kubectl from local machine blocked | Cannot manage cluster | Use Cloud Shell, a bastion VM, or VPN/Interconnect |
| Webhooks from control plane to nodes | Admission webhooks may fail | Ensure firewall allows control plane CIDR to node ports |
| Cloud Build access | CI/CD pipelines cannot reach API | Use private pools or GKE deploy via Cloud Deploy |

```bash
# Set up Cloud NAT for private nodes to pull images
gcloud compute routers create nat-router \
  --network=prod-vpc \
  --region=us-central1

gcloud compute routers nats create nat-config \
  --router=nat-router \
  --region=us-central1 \
  --auto-allocate-nat-external-ips \
  --nat-all-subnet-ip-ranges
```

---

## Did You Know?

1. **Dataplane V2 uses the same eBPF technology that powers Meta's (Facebook's) entire network stack.** Meta processes over 600 billion eBPF events per day across their fleet. In GKE, Dataplane V2's eBPF programs are compiled and loaded into the Linux kernel at node boot, where they intercept and process packets before they ever reach userspace. This is why Dataplane V2 can achieve 26% lower latency than iptables-based routing in benchmarks with 10,000+ services.

2. **A single GKE cluster can support up to 65,000 nodes and 400,000 pods.** The practical networking limit is usually IP exhaustion rather than cluster capacity. A /14 pod CIDR gives you roughly 262,144 pod IPs. If each node uses a /24 for pods (the default for 110 max pods per node), you can support about 1,024 nodes before running out of pod IPs. Planning your IP ranges at cluster creation is one of the few decisions you truly cannot change later.

3. **The Gateway API was designed by a cross-vendor working group** including engineers from Google, Red Hat, HashiCorp, and VMware. The key insight was that Ingress combined infrastructure concerns (TLS, IP addresses) with application concerns (routing rules) in a single resource, making it impossible to safely delegate to different teams. Gateway API's three-tier model (GatewayClass, Gateway, HTTPRoute) maps directly to the cluster admin, platform team, and application team roles that exist in most organizations.

4. **GKE's Global Application Load Balancer uses Google's Maglev system**, which was published as a research paper in 2016. Maglev is a distributed software load balancer that runs on commodity servers at Google's edge PoPs. It uses consistent hashing to achieve connection persistence without shared state between load balancer instances. A single Maglev machine can handle 10 million packets per second, and the system has been running Google's production traffic since 2008.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Creating a routes-based cluster instead of VPC-native | Following outdated tutorials | Always use `--enable-ip-alias`; it is the default for new clusters but verify |
| Assuming NetworkPolicy works without Dataplane V2 | Creating policies without enforcement | Enable Dataplane V2 at cluster creation; without it, policies are ignored |
| Undersizing the pod CIDR | Not calculating node count x pods per node | Plan for 3-5x your current node count; you cannot expand the range later |
| Forgetting DNS egress in NetworkPolicy | Writing a deny-all egress policy without DNS exception | Always include a rule allowing UDP/TCP port 53 to kube-dns pods |
| Using Ingress annotations for advanced routing | Trying to do canary/header routing with GKE Ingress | Switch to Gateway API which natively supports traffic splitting and header matching |
| Not enabling Cloud NAT for private clusters | Private nodes cannot reach the internet | Configure Cloud NAT on the VPC router before creating private clusters |
| Mixing GKE Ingress and Gateway API on the same cluster | Both create load balancer resources | Choose one approach per cluster; Gateway API is the recommended path forward |
| Ignoring network policy logging | Deploying policies without validation | Enable network policy logging and review denied connections before enforcing broadly |

---

## Quiz

<details>
<summary>1. What is the fundamental difference between iptables-based routing and eBPF-based routing in Dataplane V2?</summary>

iptables-based routing uses a **linear chain of rules** that the kernel evaluates sequentially for every packet. When you have 5,000 Services, there are thousands of iptables rules, and each packet must traverse this chain until a match is found. This is O(n) complexity. Dataplane V2 uses eBPF **hash maps** compiled directly into the kernel. Service routing becomes a hash table lookup: the kernel hashes the destination IP and port, looks up the backend pod in O(1) constant time, and rewrites the packet. This means routing performance does not degrade as you add more services. In benchmarks, the difference becomes measurable at around 1,000 services and dramatic at 10,000+.
</details>

<details>
<summary>2. Why must you always include a DNS egress rule when writing deny-all egress NetworkPolicies?</summary>

When you create a NetworkPolicy with `policyTypes: ["Egress"]` and no egress rules, you block **all** outbound traffic from the selected pods, including DNS resolution. Pods resolve service names (like `my-service.default.svc.cluster.local`) by querying the kube-dns (CoreDNS) pods on UDP port 53. Without a DNS exception, pods cannot resolve any service names, and virtually all application functionality breaks. The fix is to always include an egress rule allowing traffic to kube-dns pods on both UDP and TCP port 53. TCP is needed for DNS responses larger than 512 bytes.
</details>

<details>
<summary>3. How does the Gateway API separate concerns between infrastructure and application teams?</summary>

The Gateway API uses a **three-tier resource model**. The **GatewayClass** is managed by the cluster administrator and defines which load balancer implementation to use. The **Gateway** is managed by the infrastructure or platform team and configures listeners (ports, protocols, TLS certificates) and which namespaces are allowed to attach routes. The **HTTPRoute** (or TCPRoute, GRPCRoute) is managed by the application team and defines routing rules like path matching, header matching, and backend service references. This separation means the app team can update their routing without touching infrastructure configuration, and the platform team can enforce policies (like "only namespaces with label X can use this gateway") without knowing about individual routes.
</details>

<details>
<summary>4. What happens if you create a regional cluster with a /24 pod CIDR?</summary>

A /24 CIDR provides only 256 IP addresses for pods. Since each node in a VPC-native cluster gets its own /24 slice by default (for up to 110 pods), a /24 pod CIDR can only support **1 node**. If your regional cluster has 3 zones with 2 nodes each (6 nodes total), you need at least a /21 for the pod range. If you plan to scale to 50 nodes, you need a /18 or larger. The cluster creation will succeed, but you will hit scheduling failures when the pod CIDR is exhausted and new pods cannot get IPs. This is not recoverable---you must create a new cluster with a larger range.
</details>

<details>
<summary>5. How does traffic splitting work in Gateway API canary deployments?</summary>

Gateway API supports traffic splitting through the `weight` field on `backendRefs` within an HTTPRoute rule. You specify multiple backend services with different weights (e.g., 90 for stable, 10 for canary). The load balancer distributes incoming requests proportionally based on these weights. Unlike Istio's traffic splitting, which happens at the sidecar level, GKE Gateway API traffic splitting happens at the **Google Cloud Load Balancer** level, meaning there is no additional proxy hop. You update the weights by patching the HTTPRoute resource, and the load balancer reconfigures within seconds. This makes canary deployments a first-class feature without requiring a service mesh.
</details>

<details>
<summary>6. Why is Private Service Connect (PSC) preferred over the legacy private cluster approach for control plane access?</summary>

The legacy private cluster model uses VPC peering between your VPC and the Google-managed VPC hosting the control plane. VPC peering has limitations: it is non-transitive (peered networks cannot reach each other through your VPC), consumes a peering slot (limit of 25 per VPC), and the master-ipv4-cidr range must not overlap with any existing ranges. PSC instead creates a **forwarding rule** in your VPC that routes traffic to the control plane through a Private Service Connect endpoint. This avoids VPC peering entirely, supports transitive connectivity through VPN/Interconnect, does not consume a peering slot, and gives you a private IP in your own subnet for the control plane. PSC is the recommended approach for all new private clusters.
</details>

---

## Hands-On Exercise: Dataplane V2 Network Policies and Gateway API Canary

### Objective

Create a GKE cluster with Dataplane V2, enforce network policies between namespaces, and set up a Gateway API canary deployment with traffic splitting.

### Prerequisites

- `gcloud` CLI installed and authenticated
- A GCP project with billing enabled and the GKE API enabled
- `kubectl` installed

### Tasks

**Task 1: Create a GKE Cluster with Dataplane V2 and Gateway API**

<details>
<summary>Solution</summary>

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1

# Create a cluster with Dataplane V2 and Gateway API enabled
gcloud container clusters create net-demo \
  --region=$REGION \
  --num-nodes=1 \
  --machine-type=e2-standard-2 \
  --enable-dataplane-v2 \
  --enable-ip-alias \
  --release-channel=regular \
  --gateway-api=standard \
  --workload-pool=$PROJECT_ID.svc.id.goog

# Get credentials
gcloud container clusters get-credentials net-demo --region=$REGION

# Verify Dataplane V2 (Cilium pods running)
kubectl -n kube-system get pods -l k8s-app=cilium

# Verify Gateway API CRDs are installed
kubectl get gatewayclass
```
</details>

**Task 2: Deploy Two Namespaces with Applications**

<details>
<summary>Solution</summary>

```bash
# Create namespaces
kubectl create namespace frontend
kubectl create namespace backend
kubectl label namespace frontend role=frontend gateway-access=true
kubectl label namespace backend role=backend

# Deploy backend app
kubectl apply -n backend -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        version: stable
    spec:
      containers:
      - name: api
        image: hashicorp/http-echo
        args: ["-text=API v1 (stable)", "-listen=:8080"]
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: api-stable
spec:
  selector:
    app: api
    version: stable
  ports:
  - port: 8080
    targetPort: 8080
EOF

# Deploy canary version of backend
kubectl apply -n backend -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
      version: canary
  template:
    metadata:
      labels:
        app: api
        version: canary
    spec:
      containers:
      - name: api
        image: hashicorp/http-echo
        args: ["-text=API v2 (canary)", "-listen=:8080"]
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: api-canary
spec:
  selector:
    app: api
    version: canary
  ports:
  - port: 8080
    targetPort: 8080
EOF

# Deploy frontend
kubectl apply -n frontend -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.27
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
EOF

# Verify all pods running
kubectl get pods -n frontend
kubectl get pods -n backend
```
</details>

**Task 3: Enforce Network Policies with Dataplane V2**

<details>
<summary>Solution</summary>

```bash
# Default deny all ingress in the backend namespace
kubectl apply -n backend -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# Test: frontend cannot reach backend (should timeout)
kubectl run test-curl --rm -it --restart=Never \
  -n frontend --image=curlimages/curl -- \
  curl -s --connect-timeout 5 http://api-stable.backend:8080 || echo "Connection blocked (expected)"

# Allow frontend namespace to reach backend API
kubectl apply -n backend -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 8080
EOF

# Test again: frontend CAN reach backend now
kubectl run test-curl2 --rm -it --restart=Never \
  -n frontend --image=curlimages/curl -- \
  curl -s --connect-timeout 5 http://api-stable.backend:8080

# Test: a random namespace still cannot reach backend
kubectl create namespace attacker
kubectl run test-curl3 --rm -it --restart=Never \
  -n attacker --image=curlimages/curl -- \
  curl -s --connect-timeout 5 http://api-stable.backend:8080 || echo "Connection blocked (expected)"
kubectl delete namespace attacker
```
</details>

**Task 4: Set Up Gateway API with Canary Traffic Splitting**

<details>
<summary>Solution</summary>

```bash
# Create a Gateway
kubectl apply -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: demo-gateway
  namespace: backend
spec:
  gatewayClassName: gke-l7-global-external-managed
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: Same
EOF

# Create an HTTPRoute with canary traffic splitting (90/10)
kubectl apply -n backend -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-canary-route
spec:
  parentRefs:
  - kind: Gateway
    name: demo-gateway
    namespace: backend
  rules:
  - backendRefs:
    - name: api-stable
      port: 8080
      weight: 90
    - name: api-canary
      port: 8080
      weight: 10
EOF

# Wait for the Gateway to get an IP (takes 2-5 minutes)
echo "Waiting for Gateway IP..."
while true; do
  GW_IP=$(kubectl get gateway demo-gateway -n backend \
    -o jsonpath='{.status.addresses[0].value}' 2>/dev/null)
  if [ -n "$GW_IP" ] && [ "$GW_IP" != "" ]; then
    echo "Gateway IP: $GW_IP"
    break
  fi
  echo "Still provisioning..."
  sleep 15
done

# Test traffic splitting (run 20 requests, expect ~18 stable, ~2 canary)
echo "Sending 20 requests to $GW_IP..."
for i in $(seq 1 20); do
  curl -s http://$GW_IP
  echo ""
done | sort | uniq -c | sort -rn
```
</details>

**Task 5: Shift Canary Traffic to 50/50 and Then Promote**

<details>
<summary>Solution</summary>

```bash
# Shift to 50/50
kubectl apply -n backend -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-canary-route
spec:
  parentRefs:
  - kind: Gateway
    name: demo-gateway
    namespace: backend
  rules:
  - backendRefs:
    - name: api-stable
      port: 8080
      weight: 50
    - name: api-canary
      port: 8080
      weight: 50
EOF

echo "Waiting 30 seconds for LB to reconfigure..."
sleep 30

# Test again
GW_IP=$(kubectl get gateway demo-gateway -n backend \
  -o jsonpath='{.status.addresses[0].value}')
echo "50/50 split results:"
for i in $(seq 1 20); do
  curl -s http://$GW_IP
done | sort | uniq -c | sort -rn

# Full promotion to canary
kubectl apply -n backend -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-canary-route
spec:
  parentRefs:
  - kind: Gateway
    name: demo-gateway
    namespace: backend
  rules:
  - backendRefs:
    - name: api-canary
      port: 8080
      weight: 100
EOF

sleep 30

echo "Full canary promotion results:"
for i in $(seq 1 10); do
  curl -s http://$GW_IP
done
```
</details>

**Task 6: Clean Up**

<details>
<summary>Solution</summary>

```bash
# Delete the cluster (this removes all resources)
gcloud container clusters delete net-demo \
  --region=$REGION --quiet

echo "Cluster deleted. Verify no orphaned load balancer resources:"
gcloud compute forwarding-rules list --filter="description~net-demo"
gcloud compute target-http-proxies list --filter="description~net-demo"
```
</details>

### Success Criteria

- [ ] Cluster created with Dataplane V2 and Gateway API enabled
- [ ] Cilium pods running in kube-system namespace
- [ ] Network policy blocks cross-namespace traffic by default
- [ ] Network policy allows frontend-to-backend traffic on port 8080
- [ ] Gateway API HTTPRoute splits traffic 90/10 between stable and canary
- [ ] Traffic shifting to 50/50 and full promotion works correctly
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 3: GKE Workload Identity and Security](module-3-gke-identity.md)** --- Learn how to securely connect pods to GCP services without storing credentials, enforce binary authorization for trusted images, and leverage GKE's security posture dashboard.
