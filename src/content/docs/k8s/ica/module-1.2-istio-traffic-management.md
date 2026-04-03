---
title: "Module 1.2: Istio Traffic Management"
slug: k8s/ica/module-1.2-istio-traffic-management
sidebar:
  order: 3
---
## Complexity: `[COMPLEX]`
## Time to Complete: 60-75 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 1: Installation & Architecture](../module-1.1-istio-installation-architecture/) — Istio installation and sidecar injection
- [CKA Module 3.5: Gateway API](../cka/part3-services-networking/module-3.5-gateway-api/) — Kubernetes Gateway API basics
- Understanding of HTTP routing concepts (headers, paths, methods)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** VirtualService routing rules for header-based, path-based, and weighted traffic splitting across service versions
2. **Implement** canary and blue-green deployment patterns using DestinationRules with traffic policies and subset definitions
3. **Apply** resilience patterns (circuit breaking, retries, timeouts, fault injection) to harden service-to-service communication
4. **Debug** traffic routing issues using `istioctl proxy-config routes`, Kiali service graphs, and Envoy access logs

---

## Why This Module Matters

Traffic Management is **35% of the ICA exam** — the single largest domain. Combined with Resilience and Fault Injection (10%), traffic-related topics account for nearly half the exam. You must be able to write VirtualService, DestinationRule, and Gateway resources from memory, configure traffic splitting, inject faults, and set up resilience policies.

This is where Istio shines brightest. Without a service mesh, implementing canary deployments, circuit breaking, or fault injection requires application-level code changes or complex infrastructure. With Istio, it's a few lines of YAML applied to the mesh — the application never knows.

> **The Air Traffic Control Analogy**
>
> Think of Istio traffic management like air traffic control. Your services are airports. Without Istio, planes (requests) fly directly between airports with no coordination. With Istio, VirtualServices are the flight plans (where traffic goes), DestinationRules are the runway assignments (how traffic arrives), and Gateways are the international terminals (how traffic enters/leaves the mesh). Air traffic control doesn't modify the planes — it controls the routes.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Configure VirtualService for HTTP routing, traffic splitting, and fault injection
- Use DestinationRule for load balancing, circuit breaking, and connection pools
- Set up Gateway and ServiceEntry for ingress/egress traffic
- Implement canary deployments with weighted routing
- Configure retries, timeouts, and circuit breaking for resilience
- Inject faults (delays and aborts) for chaos testing
- Use traffic mirroring for safe testing in production

---

## Did You Know?

- **VirtualService doesn't create virtual anything**: Despite the name, VirtualService doesn't create a new service. It configures how traffic is routed *to* existing Kubernetes services. Think of it as a routing rule, not a resource.

- **Traffic splitting happens at the proxy, not the service**: When you set 80/20 canary split, each Envoy proxy independently makes weighted random choices. There's no central load balancer — it's distributed probabilistic routing.

- **Istio can route by any HTTP header**: Including custom headers, cookies, user-agent, and even source labels. This enables sophisticated patterns like "route requests from the QA team to the canary version" without touching application code.

---

## War Story: The Canary That Cooked the Kitchen

**Characters:**
- Priya: Senior SRE (5 years experience)
- Deployment: Payment service v2 with new fraud detection

**The Incident:**

Priya configured a 90/10 canary deployment for the payment service. V2 was getting 10% of traffic. Metrics looked great — latency was fine, error rate was zero. After 30 minutes, she shifted to 50/50. Still good. She went to 100%.

Within 5 minutes, the payment service started returning 503 errors. Not a few — 30% of all payment requests were failing. The team rolled back to v1 immediately, but the damage was done: $200K in failed transactions during a 7-minute window.

**What went wrong?**

The VirtualService was routing by weight correctly, but Priya had forgotten the DestinationRule. Without it, Istio used round-robin load balancing across all pods — both v1 and v2. The VirtualService said "send 100% to v2 subset," but there was no subset defined. Istio couldn't find the subset and returned 503.

**The missing piece:**

```yaml
# Priya had this VirtualService:
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: payment
spec:
  hosts:
  - payment
  http:
  - route:
    - destination:
        host: payment
        subset: v2    # ← References a subset...
      weight: 100

# But forgot this DestinationRule:
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: payment
spec:
  host: payment
  subsets:            # ← ...that must be defined here
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

**Lesson**: VirtualService and DestinationRule are a pair. If your VirtualService references subsets, you MUST have a matching DestinationRule. Always run `istioctl analyze` before applying traffic rules.

---

## Part 1: Core Resources

### 1.1 VirtualService

VirtualService defines **how** requests are routed to a service. It intercepts traffic at the Envoy proxy and applies routing rules before the request reaches the destination.

```
Without VirtualService:              With VirtualService:

Client ──► Service (round-robin)     Client ──► Envoy ──► VirtualService rules
                                                          ├── 80% → v1 pods
                                                          ├── 10% → v2 pods
                                                          └── 10% → v3 pods
```

**Basic VirtualService:**

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews                    # Which service this applies to
  http:
  - match:                     # Conditions (optional)
    - headers:
        end-user:
          exact: jason         # If header matches...
    route:
    - destination:
        host: reviews
        subset: v2             # ...route to v2
  - route:                     # Default route (no match = catch-all)
    - destination:
        host: reviews
        subset: v1
```

**Key fields:**

| Field | Purpose | Example |
|-------|---------|---------|
| `hosts` | Services this rule applies to | `["reviews"]`, `["*.example.com"]` |
| `http[].match` | Conditions for routing | Headers, URI, method, query params |
| `http[].route` | Where to send traffic | Service host + subset + weight |
| `http[].timeout` | Request timeout | `10s` |
| `http[].retries` | Retry configuration | `attempts: 3` |
| `http[].fault` | Fault injection | `delay`, `abort` |
| `http[].mirror` | Traffic mirroring | Send copy to another service |

### 1.2 DestinationRule

DestinationRule defines **policies** applied to traffic *after* routing has occurred. It configures load balancing, connection pools, outlier detection, and TLS settings for a destination.

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews                    # Which service
  trafficPolicy:                   # Global policies
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
    loadBalancer:
      simple: ROUND_ROBIN          # or LEAST_CONN, RANDOM, PASSTHROUGH
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
  subsets:                          # Named versions
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
    trafficPolicy:                 # Per-subset override
      loadBalancer:
        simple: LEAST_CONN
  - name: v3
    labels:
      version: v3
```

**Subsets** are named groups of pods selected by labels. VirtualService references subsets to route to specific versions.

### 1.3 Gateway

Gateway configures a load balancer at the edge of the mesh for incoming (ingress) or outgoing (egress) HTTP/TCP traffic. It binds to an Istio ingress/egress gateway workload.

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway           # Bind to Istio's ingress gateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "bookinfo.example.com"        # Accept traffic for this host
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "bookinfo.example.com"
    tls:
      mode: SIMPLE
      credentialName: bookinfo-tls   # K8s Secret with cert/key
```

**Connect Gateway to VirtualService:**

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "bookinfo.example.com"
  gateways:
  - bookinfo-gateway               # Reference the Gateway
  http:
  - match:
    - uri:
        prefix: /productpage
    route:
    - destination:
        host: productpage
        port:
          number: 9080
  - match:
    - uri:
        prefix: /reviews
    route:
    - destination:
        host: reviews
```

**Traffic flow with Gateway:**

```
Internet                    Mesh
                     ┌──────────────────────────────────────┐
                     │                                      │
Client ──► Gateway ──┼──► VirtualService ──► DestinationRule │
  (external)   │     │         │                    │        │
               │     │    Route rules          Load balance  │
          Istio Ingress   (path, header,       Subsets       │
          Gateway Pod      weight)             Circuit break │
                     │                                      │
                     └──────────────────────────────────────┘
```

### 1.4 ServiceEntry

ServiceEntry adds entries to Istio's internal service registry, letting you manage traffic to external services as if they were part of the mesh.

```yaml
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: external-api
spec:
  hosts:
  - api.external.com
  location: MESH_EXTERNAL             # Outside the mesh
  ports:
  - number: 443
    name: https
    protocol: TLS
  resolution: DNS
---
# Now you can apply traffic rules to external services!
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: external-api-timeout
spec:
  hosts:
  - api.external.com
  http:
  - timeout: 5s
    route:
    - destination:
        host: api.external.com
```

**Why ServiceEntry matters:**

By default, Istio allows all outbound traffic. But with `meshConfig.outboundTrafficPolicy.mode: REGISTRY_ONLY`, only registered services are accessible. ServiceEntry becomes required for external access.

---

## Part 2: Traffic Shifting (Canary Deployments)

### 2.1 Weighted Routing

The most common canary pattern — split traffic by percentage:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 80               # 80% to v1
    - destination:
        host: reviews
        subset: v2
      weight: 20               # 20% to v2
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

**Progressive rollout example:**

```bash
# Step 1: 90/10 split
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 90
    - destination:
        host: reviews
        subset: v2
      weight: 10
EOF

# Monitor error rates... then increase

# Step 2: 50/50 split
kubectl patch virtualservice reviews --type merge -p '
spec:
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 50
    - destination:
        host: reviews
        subset: v2
      weight: 50'

# Step 3: Full rollout
kubectl patch virtualservice reviews --type merge -p '
spec:
  http:
  - route:
    - destination:
        host: reviews
        subset: v2
      weight: 100'
```

### 2.2 Header-Based Routing

Route specific users or teams to a different version:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  # Rule 1: Route "jason" to v2
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2
  # Rule 2: Route requests with "canary: true" header to v3
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: reviews
        subset: v3
  # Rule 3: Everyone else goes to v1
  - route:
    - destination:
        host: reviews
        subset: v1
```

### 2.3 URI-Based Routing

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - bookinfo.example.com
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    route:
    - destination:
        host: productpage
        port:
          number: 9080
  - match:
    - uri:
        prefix: /api/v1/reviews
    route:
    - destination:
        host: reviews
        port:
          number: 9080
  - match:
    - uri:
        regex: "/api/v[0-9]+/ratings"
    route:
    - destination:
        host: ratings
        port:
          number: 9080
```

**Match types for URIs:**

| Type | Example | Matches |
|------|---------|---------|
| `exact` | `/productpage` | Only `/productpage` |
| `prefix` | `/api/v1` | `/api/v1`, `/api/v1/reviews`, etc. |
| `regex` | `/api/v[0-9]+` | `/api/v1`, `/api/v2`, etc. |

---

## Part 3: Fault Injection

Fault injection lets you test how your application handles failures — without actually breaking real services. This is how Netflix-style chaos engineering works at the mesh layer.

### 3.1 Delay Injection

Simulate network latency:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings
spec:
  hosts:
  - ratings
  http:
  - fault:
      delay:
        percentage:
          value: 100            # 100% of requests get delayed
        fixedDelay: 7s          # 7 second delay
    route:
    - destination:
        host: ratings
        subset: v1
```

**Selective delay — only affect specific users:**

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings
spec:
  hosts:
  - ratings
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    fault:
      delay:
        percentage:
          value: 100
        fixedDelay: 7s
    route:
    - destination:
        host: ratings
        subset: v1
  - route:
    - destination:
        host: ratings
        subset: v1
```

### 3.2 Abort Injection

Simulate HTTP errors:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings
spec:
  hosts:
  - ratings
  http:
  - fault:
      abort:
        percentage:
          value: 50              # 50% of requests get aborted
        httpStatus: 503          # Return 503 Service Unavailable
    route:
    - destination:
        host: ratings
        subset: v1
```

### 3.3 Combined Faults

Apply both delay and abort simultaneously:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings
spec:
  hosts:
  - ratings
  http:
  - fault:
      delay:
        percentage:
          value: 50
        fixedDelay: 5s
      abort:
        percentage:
          value: 10
        httpStatus: 500
    route:
    - destination:
        host: ratings
        subset: v1
```

This means: 50% of requests are delayed by 5s, and independently 10% return HTTP 500.

---

## Part 4: Resilience

### 4.1 Timeouts

Prevent requests from hanging indefinitely:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - timeout: 3s                 # Fail if no response within 3 seconds
    route:
    - destination:
        host: reviews
        subset: v1
```

### 4.2 Retries

Automatically retry failed requests:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - retries:
      attempts: 3               # Retry up to 3 times
      perTryTimeout: 2s         # Each attempt gets 2 seconds
      retryOn: 5xx,reset,connect-failure,retriable-4xx
    route:
    - destination:
        host: reviews
        subset: v1
```

**Common `retryOn` values:**

| Value | Retries When |
|-------|-------------|
| `5xx` | Server returns 5xx |
| `reset` | Connection reset |
| `connect-failure` | Can't connect |
| `retriable-4xx` | Specific 4xx codes (409) |
| `gateway-error` | 502, 503, 504 |

> **Warning**: Retries multiply load. 3 retries means a failing service gets 4x the traffic. Always combine retries with circuit breaking.

### 4.3 Circuit Breaking

Prevent cascading failures by stopping traffic to unhealthy instances:

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100       # Max TCP connections
      http:
        http1MaxPendingRequests: 10  # Max queued requests
        http2MaxRequests: 100        # Max concurrent requests
        maxRequestsPerConnection: 10 # Max requests per connection
        maxRetries: 3                # Max concurrent retries
    outlierDetection:
      consecutive5xxErrors: 5     # Eject after 5 consecutive 5xx
      interval: 10s              # Check every 10 seconds
      baseEjectionTime: 30s      # Eject for at least 30 seconds
      maxEjectionPercent: 50     # Don't eject more than 50% of hosts
  subsets:
  - name: v1
    labels:
      version: v1
```

**How circuit breaking works:**

```
                    Normal Operation
                    ┌─────────────────────┐
Requests ──────────►│ Connection Pool      │──► Service Pods
                    │ (100 max connections)│    ┌────┐ ┌────┐
                    └─────────────────────┘    │ v1 │ │ v1 │
                                               └────┘ └────┘

                    Circuit OPEN (overloaded)
                    ┌─────────────────────┐
Requests ──────────►│ Connection Pool FULL │──✗  (503 returned)
  (101st request)   │ (100/100 connections)│
                    └─────────────────────┘

                    Outlier Detection (unhealthy pod)
                    ┌─────────────────────┐
Requests ──────────►│ Outlier Detection    │──► ┌────┐
                    │ (5 consecutive 5xx)  │    │ v1 │ (healthy)
                    └─────────────────────┘    └────┘
                              │
                              └──✗ ┌────┐ (ejected for 30s)
                                   │ v1 │
                                   └────┘
```

### 4.4 Outlier Detection

Outlier detection ejects unhealthy instances from the load balancing pool:

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 3     # Eject after 3 errors
      interval: 15s              # Evaluation interval
      baseEjectionTime: 30s      # Min ejection duration
      maxEjectionPercent: 30     # Max % of hosts ejected
      minHealthPercent: 70       # Only eject if >70% healthy
```

---

## Part 5: Traffic Mirroring

Mirror (shadow) traffic to a service for testing without affecting the primary flow. The mirrored request is fire-and-forget — responses are discarded.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 100
    mirror:
      host: reviews
      subset: v2                 # Mirror to v2
    mirrorPercentage:
      value: 100                 # Mirror 100% of traffic
```

**Use cases for mirroring:**
- Test new version with real production traffic
- Compare v1 vs v2 responses without risk
- Load test a new deployment
- Capture real traffic patterns for debugging

---

## Part 6: Ingress Traffic

### 6.1 Configuring Ingress with Gateway

Complete example — expose an application to external traffic:

```yaml
# Step 1: Gateway (the front door)
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: httpbin-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "httpbin.example.com"
---
# Step 2: VirtualService (routing rules)
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: httpbin
spec:
  hosts:
  - "httpbin.example.com"
  gateways:
  - httpbin-gateway
  http:
  - match:
    - uri:
        prefix: /status
    - uri:
        prefix: /delay
    route:
    - destination:
        host: httpbin
        port:
          number: 8000
```

```bash
# Get the ingress gateway's external IP
export INGRESS_HOST=$(kubectl -n istio-system get service istio-ingressgateway \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway \
  -o jsonpath='{.spec.ports[?(@.name=="http2")].port}')

# For kind/minikube (NodePort):
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway \
  -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export INGRESS_HOST=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test
curl -H "Host: httpbin.example.com" http://$INGRESS_HOST:$INGRESS_PORT/status/200
```

### 6.2 TLS at Ingress

```yaml
# Create TLS secret
kubectl create -n istio-system secret tls httpbin-tls \
  --key=httpbin.key \
  --cert=httpbin.crt

---
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: httpbin-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "httpbin.example.com"
    tls:
      mode: SIMPLE                    # One-way TLS
      credentialName: httpbin-tls     # K8s Secret name
```

**TLS modes at Gateway:**

| Mode | Description |
|------|-------------|
| `SIMPLE` | Standard TLS (server cert only) |
| `MUTUAL` | mTLS (both client and server certs) |
| `PASSTHROUGH` | Forward encrypted traffic as-is (SNI routing) |
| `AUTO_PASSTHROUGH` | Like PASSTHROUGH with automatic SNI routing |
| `ISTIO_MUTUAL` | Use Istio's internal mTLS (for mesh-internal gateways) |

---

## Part 7: Egress Traffic

### 7.1 Controlling Outbound Traffic

By default, Istio sidecars allow all outbound traffic. To lock this down:

```yaml
# In IstioOperator or mesh config
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    outboundTrafficPolicy:
      mode: REGISTRY_ONLY          # Block unregistered external services
```

### 7.2 ServiceEntry for External Access

```yaml
# Allow access to an external API
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: google-api
spec:
  hosts:
  - "www.googleapis.com"
  ports:
  - number: 443
    name: https
    protocol: TLS
  location: MESH_EXTERNAL
  resolution: DNS
---
# Optional: Apply traffic policy to external service
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: google-api
spec:
  host: "www.googleapis.com"
  trafficPolicy:
    tls:
      mode: SIMPLE                 # Originate TLS to external service
```

### 7.3 Egress Gateway

Route external traffic through a dedicated egress gateway (for auditing/control):

```yaml
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: external-svc
spec:
  hosts:
  - external.example.com
  ports:
  - number: 443
    name: tls
    protocol: TLS
  location: MESH_EXTERNAL
  resolution: DNS
---
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: egress-gateway
spec:
  selector:
    istio: egressgateway
  servers:
  - port:
      number: 443
      name: tls
      protocol: TLS
    hosts:
    - external.example.com
    tls:
      mode: PASSTHROUGH
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: external-through-egress
spec:
  hosts:
  - external.example.com
  gateways:
  - mesh                          # Internal mesh traffic
  - egress-gateway                # Egress gateway
  tls:
  - match:
    - gateways:
      - mesh
      port: 443
      sniHosts:
      - external.example.com
    route:
    - destination:
        host: istio-egressgateway.istio-system.svc.cluster.local
        port:
          number: 443
  - match:
    - gateways:
      - egress-gateway
      port: 443
      sniHosts:
      - external.example.com
    route:
    - destination:
        host: external.example.com
        port:
          number: 443
```

---

## Common Mistakes

| Mistake | Symptom | Solution |
|---------|---------|----------|
| VirtualService references subset without DestinationRule | 503 errors, `no healthy upstream` | Always create DestinationRule with matching subsets |
| Weights don't sum to 100 | Rejected or unexpected distribution | Ensure all weights total exactly 100 |
| Gateway host doesn't match VirtualService host | Traffic doesn't reach the service | Hosts must match exactly between Gateway and VirtualService |
| Missing `gateways:` field in VirtualService | Works for mesh traffic, not ingress | Add `gateways: [gateway-name]` for external traffic |
| Retries without circuit breaking | Retry storm overwhelms failing service | Always pair retries with outlier detection |
| Timeout shorter than retries * perTryTimeout | Timeout kills retries prematurely | Set timeout >= attempts * perTryTimeout |
| ServiceEntry missing for external service | 502 errors when `REGISTRY_ONLY` mode | Add ServiceEntry for every external dependency |
| Wrong port in DestinationRule | Connection refused or silent routing failure | Match port numbers exactly with the Kubernetes Service |

---

## Quiz

Test your knowledge:

**Q1: What is the relationship between VirtualService and DestinationRule?**

<details>
<summary>Show Answer</summary>

**VirtualService** defines *where* traffic goes (routing rules: match conditions, weights, hosts).
**DestinationRule** defines *how* traffic arrives (policies: load balancing, circuit breaking, subsets, TLS).

VirtualService is applied first (routing decision), then DestinationRule (policy enforcement). If a VirtualService references a subset, the DestinationRule MUST define that subset.

</details>

**Q2: Write a VirtualService that sends 80% of traffic to v1 and 20% to v2 of the "productpage" service.**

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: productpage
spec:
  hosts:
  - productpage
  http:
  - route:
    - destination:
        host: productpage
        subset: v1
      weight: 80
    - destination:
        host: productpage
        subset: v2
      weight: 20
```

(Requires a DestinationRule with `v1` and `v2` subsets defined.)

</details>

**Q3: How do you inject a 5-second delay into 50% of requests to the ratings service?**

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings
spec:
  hosts:
  - ratings
  http:
  - fault:
      delay:
        percentage:
          value: 50
        fixedDelay: 5s
    route:
    - destination:
        host: ratings
```

</details>

**Q4: What is the difference between circuit breaking (connectionPool) and outlier detection?**

<details>
<summary>Show Answer</summary>

- **Connection pool (circuit breaking)**: Limits the *number* of connections/requests to a service. When limits are hit, new requests get 503. Protects the destination from overload.
- **Outlier detection**: Monitors individual endpoints for errors and *ejects* unhealthy ones from the pool. Remaining healthy endpoints still receive traffic.

Both are configured in DestinationRule. They complement each other: connection pool prevents overload, outlier detection removes bad instances.

</details>

**Q5: What does a Gateway resource actually do?**

<details>
<summary>Show Answer</summary>

Gateway configures a load balancer (typically the Istio ingress gateway pod) to accept traffic from outside the mesh. It specifies:
- Which ports to listen on
- Which protocols to accept (HTTP, HTTPS, TCP, TLS)
- Which hosts to accept traffic for
- TLS configuration (certificates, mTLS)

Gateway does NOT define routing — it must be paired with a VirtualService that references it via `gateways: [gateway-name]`.

</details>

**Q6: How do you restrict egress traffic to only registered services?**

<details>
<summary>Show Answer</summary>

Set the outbound traffic policy to `REGISTRY_ONLY`:

```yaml
meshConfig:
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY
```

Then register external services with ServiceEntry resources. Any traffic to unregistered external hosts will be blocked.

</details>

**Q7: What is traffic mirroring and when would you use it?**

<details>
<summary>Show Answer</summary>

Traffic mirroring sends a copy of live traffic to a secondary service. The mirrored traffic is fire-and-forget — responses from the mirror are discarded and don't affect the primary request.

Use cases:
- Testing a new version with real production traffic patterns
- Load testing without synthetic traffic
- Debugging by capturing real requests
- Comparing behavior between versions

```yaml
mirror:
  host: reviews
  subset: v2
mirrorPercentage:
  value: 100
```

</details>

**Q8: What happens if you configure retries with attempts: 3 and perTryTimeout: 2s, but the overall timeout is 3s?**

<details>
<summary>Show Answer</summary>

The overall timeout (3s) overrides the retry budget. With `perTryTimeout: 2s` and `attempts: 3`, you'd need 6s total for all retries. But the 3s timeout means at most the first attempt (2s) plus part of the second attempt can complete before the overall timeout kills the request.

**Best practice**: Set `timeout >= attempts * perTryTimeout` (in this case, >= 6s).

</details>

**Q9: What is a ServiceEntry and when is it required?**

<details>
<summary>Show Answer</summary>

ServiceEntry adds external services to Istio's internal service registry. It's required when:
1. `outboundTrafficPolicy.mode` is `REGISTRY_ONLY` (external traffic is blocked by default)
2. You want to apply Istio traffic rules (timeouts, retries, fault injection) to external services
3. You want to monitor external service traffic through Istio's observability features

Without `REGISTRY_ONLY`, ServiceEntry is optional but still useful for applying policies.

</details>

**Q10: Write a Gateway + VirtualService to expose the "frontend" service on HTTPS at frontend.example.com.**

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: frontend-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "frontend.example.com"
    tls:
      mode: SIMPLE
      credentialName: frontend-tls
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: frontend
spec:
  hosts:
  - "frontend.example.com"
  gateways:
  - frontend-gateway
  http:
  - route:
    - destination:
        host: frontend
        port:
          number: 80
```

(Requires a TLS secret named `frontend-tls` in `istio-system` namespace.)

</details>

**Q11: How do you route requests with the header `x-test: canary` to subset v2, and all other traffic to v1?**

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: myapp
spec:
  hosts:
  - myapp
  http:
  - match:
    - headers:
        x-test:
          exact: canary
    route:
    - destination:
        host: myapp
        subset: v2
  - route:
    - destination:
        host: myapp
        subset: v1
```

Match rules are evaluated top-to-bottom. The first match wins. The catch-all (no match) at the bottom handles everything else.

</details>

---

## Hands-On Exercise: Traffic Management with Bookinfo

### Objective
Deploy the Bookinfo application and practice traffic management operations: canary deployment, fault injection, and circuit breaking.

### Setup

```bash
# Ensure Istio is installed (from Module 1)
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled

# Deploy Bookinfo
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/bookinfo/platform/kube/bookinfo.yaml

# Wait for pods
kubectl wait --for=condition=ready pod --all -n default --timeout=120s

# Deploy all DestinationRules
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/bookinfo/networking/destination-rule-all.yaml

# Deploy the Gateway
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/bookinfo/networking/bookinfo-gateway.yaml

# Verify
istioctl analyze
```

### Task 1: Route All Traffic to v1

```bash
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
EOF
```

Verify by sending traffic — you should only see reviews WITHOUT stars:

```bash
# Port-forward to productpage
kubectl port-forward svc/productpage 9080:9080 &

# Send requests — should always be v1 (no stars)
for i in $(seq 1 10); do
  curl -s http://localhost:9080/productpage | grep -o "glyphicon-star" | wc -l
done
```

### Task 2: Canary — Send 20% to v2

```bash
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 80
    - destination:
        host: reviews
        subset: v2
      weight: 20
EOF
```

Verify — roughly 2 out of 10 requests should show black stars (v2):

```bash
for i in $(seq 1 20); do
  stars=$(curl -s http://localhost:9080/productpage | grep -o "glyphicon-star" | wc -l)
  echo "Request $i: $stars stars"
done
```

### Task 3: Inject a 3-second Delay

```bash
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings
spec:
  hosts:
  - ratings
  http:
  - fault:
      delay:
        percentage:
          value: 100
        fixedDelay: 3s
    route:
    - destination:
        host: ratings
        subset: v1
EOF
```

Verify — requests should take ~3 seconds longer:

```bash
time curl -s http://localhost:9080/productpage > /dev/null
# Should show ~3+ seconds
```

### Task 4: Circuit Breaking

```bash
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews-cb
spec:
  host: reviews
  trafficPolicy:
    connectionPool:
      http:
        http1MaxPendingRequests: 1
        http2MaxRequests: 1
        maxRequestsPerConnection: 1
    outlierDetection:
      consecutive5xxErrors: 1
      interval: 1s
      baseEjectionTime: 30s
      maxEjectionPercent: 100
EOF
```

Generate load to trigger circuit breaking:

```bash
# Install fortio (Istio's load testing tool)
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/httpbin/sample-client/fortio-deploy.yaml
kubectl wait --for=condition=ready pod -l app=fortio

# Send 20 concurrent connections
FORTIO_POD=$(kubectl get pods -l app=fortio -o jsonpath='{.items[0].metadata.name}')
kubectl exec $FORTIO_POD -c fortio -- fortio load -c 3 -qps 0 -n 30 -loglevel Warning \
  http://reviews:9080/reviews/1

# Look for "Code 503" responses — those are circuit breaker trips
```

### Success Criteria

- [ ] All traffic routes to reviews v1 (no stars) when configured
- [ ] ~20% of traffic shows stars when canary is configured
- [ ] Delay injection adds ~3 seconds to requests
- [ ] Circuit breaker returns 503 under concurrent load
- [ ] `istioctl analyze` shows no errors for all configurations

### Cleanup

```bash
kill %1  # Stop port-forward
kubectl delete virtualservice reviews ratings
kubectl delete destinationrule reviews-cb
```

---

## Next Module

Continue to [Module 3: Security & Troubleshooting](../module-1.3-istio-security-troubleshooting/) — covering mTLS, authorization policies, JWT authentication, and essential debugging commands.
