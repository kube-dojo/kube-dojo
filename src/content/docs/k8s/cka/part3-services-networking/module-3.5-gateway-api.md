---
title: "Module 3.5: Gateway API"
slug: k8s/cka/part3-services-networking/module-3.5-gateway-api
sidebar:
  order: 6
lab:
  id: cka-3.5-gateway-api
  url: https://killercoda.com/kubedojo/scenario/cka-3.5-gateway-api
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - CKA exam topic
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 3.4 (Ingress)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Create** Gateway, HTTPRoute, and GRPCRoute resources for advanced traffic management
- **Compare** Gateway API with Ingress and explain when to use each
- **Configure** traffic splitting, header-based routing, and request mirroring
- **Explain** the Gateway API role model (infrastructure provider, cluster operator, application developer)

---

## Why This Module Matters

Gateway API is the **current standard for Kubernetes networking**. It addresses limitations of Ingress by providing richer routing capabilities, role-oriented design, and support for protocols beyond HTTP. The CKA exam includes Gateway API as a core competency: "Use the Gateway API to manage Ingress traffic."

With the **ingress-nginx controller retired** (March 31, 2026) and Gateway API GA since October 2023, Gateway API is the recommended approach for all new deployments. Every major ingress controller now supports it: Envoy Gateway, Istio, Cilium, Traefik, Kong, and NGINX Gateway Fabric.

> **Migration Note**: If you're managing existing Ingress resources, the **Ingress2Gateway 1.0** tool (released March 2026) converts Ingress resources and 30+ ingress-nginx annotations to Gateway API equivalents. See the [official migration guide](https://gateway-api.sigs.k8s.io/guides/getting-started/migrating-from-ingress/).

> **The Airport Analogy**
>
> If Ingress is like a single airport terminal with one check-in desk, Gateway API is like a modern airport with separate entities: infrastructure operators manage the runways (Gateway), airlines manage their check-in counters (HTTPRoute), and security handles policies (policies). Each role has clear responsibilities.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand the difference between Ingress and Gateway API
- Create Gateway and HTTPRoute resources
- Configure path and header-based routing
- Understand the role-oriented model
- Use Gateway API for traffic management

---

## Did You Know?

- **Gateway API is the official standard**: The Kubernetes SIG Network designed Gateway API to replace Ingress limitations. With ingress-nginx retired and all major controllers supporting Gateway API, it's the production standard.

- **Multi-protocol support**: Unlike Ingress (HTTP only), Gateway API supports TCP, UDP, TLS, and gRPC natively.

- **Role-oriented design**: Gateway API separates concerns between infrastructure providers, cluster operators, and application developers.

- **Ingress2Gateway 1.0**: Released March 2026, this official migration tool converts Ingress resources (including 30+ ingress-nginx annotations) to Gateway API. Supports output for Envoy Gateway, kgateway, and others.

---

## Part 1: Gateway API vs Ingress

### 1.1 Key Differences

| Aspect | Ingress | Gateway API |
|--------|---------|-------------|
| Resources | 1 (Ingress) | Multiple (Gateway, HTTPRoute, etc.) |
| Protocols | HTTP/HTTPS | HTTP, HTTPS, TCP, UDP, TLS, gRPC |
| Role model | Single resource | Separated by role |
| Extensibility | Annotations (non-portable) | Typed extensions (portable) |
| Header routing | Controller-specific | Native support |
| Traffic splitting | Controller-specific | Native support |
| Status | Stable | GA since v1.0 (Oct 2023) |

### 1.2 Resource Hierarchy

```
┌────────────────────────────────────────────────────────────────┐
│                   Gateway API Resource Model                    │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                   GatewayClass                           │  │
│   │   (Defines controller - like IngressClass)              │  │
│   │   Created by: Infrastructure Provider                    │  │
│   └─────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                      Gateway                             │  │
│   │   (Infrastructure - listeners, addresses)                │  │
│   │   Created by: Cluster Operator                          │  │
│   └─────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│               ┌─────────────┼─────────────┐                    │
│               │             │             │                    │
│               ▼             ▼             ▼                    │
│         ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│         │HTTPRoute │  │TCPRoute  │  │GRPCRoute │             │
│         │          │  │          │  │          │             │
│         │ App team │  │ App team │  │ App team │             │
│         └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│              │             │             │                    │
│              ▼             ▼             ▼                    │
│         ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│         │ Services │  │ Services │  │ Services │             │
│         └──────────┘  └──────────┘  └──────────┘             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: In a large organization, the platform team manages infrastructure and the app teams manage their own routing. With Ingress, both teams edit the same resource type. What problems does this cause, and how does Gateway API's resource model solve them?

### 1.3 Role-Oriented Design

| Role | Resources | Responsibilities |
|------|-----------|-----------------|
| **Infrastructure Provider** | GatewayClass | Defines how gateways are implemented |
| **Cluster Operator** | Gateway, ReferenceGrant | Configures infrastructure, network policies |
| **Application Developer** | HTTPRoute, TCPRoute | Defines routing rules for applications |

---

## Part 2: Installing Gateway API

### 2.1 Installing the CRDs

```bash
# Install Gateway API CRDs (required first)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# Verify CRDs are installed
kubectl get crd | grep gateway
# gatewayclasses.gateway.networking.k8s.io
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
```

### 2.2 Gateway Controller Options

| Controller | Type | Best For |
|------------|------|----------|
| **Istio** | Service mesh | Full-featured, service mesh users |
| **Contour** | Standalone | Simple, fast |
| **nginx** | Standalone | Familiar to nginx users |
| **Cilium** | CNI-integrated | eBPF performance |
| **Traefik** | Standalone | Dynamic configuration |

### 2.3 Installing Istio Gateway Controller (Example)

```bash
# Install Istio with Gateway API support
istioctl install --set profile=minimal

# Or for quick testing with kind/minikube, use Contour:
kubectl apply -f https://projectcontour.io/quickstart/contour-gateway.yaml
```

---

## Part 3: GatewayClass and Gateway

### 3.1 GatewayClass

```yaml
# GatewayClass - created by infrastructure provider
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: example-gateway-class
spec:
  controllerName: example.io/gateway-controller
  description: "Example Gateway controller"
```

```bash
# List GatewayClasses
k get gatewayclass
k get gc               # Short form
```

### 3.2 Gateway

```yaml
# Gateway - created by cluster operator
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-gateway
  namespace: default
spec:
  gatewayClassName: example-gateway-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All        # Allow routes from all namespaces
```

### 3.3 Gateway with Multiple Listeners

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: multi-listener-gateway
spec:
  gatewayClassName: example-gateway-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    hostname: "*.example.com"
    allowedRoutes:
      namespaces:
        from: All
  - name: https
    protocol: HTTPS
    port: 443
    hostname: "*.example.com"
    tls:
      mode: Terminate
      certificateRefs:
      - name: example-tls
        kind: Secret
    allowedRoutes:
      namespaces:
        from: Same       # Only routes from same namespace
```

### 3.4 Checking Gateway Status

```bash
# Get gateway
k get gateway
k get gtw              # Short form

# Describe gateway (check conditions)
k describe gateway example-gateway

# Check if gateway is ready
k get gateway example-gateway -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

---

## Part 4: HTTPRoute

### 4.1 Simple HTTPRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: simple-route
spec:
  parentRefs:
  - name: example-gateway       # Attach to this Gateway
  rules:
  - backendRefs:
    - name: web-service         # Target service
      port: 80
```

### 4.2 Path-Based Routing

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: path-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-service
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: web-service
      port: 80
```

### 4.3 Host-Based Routing

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: host-route
spec:
  parentRefs:
  - name: example-gateway
  hostnames:
  - "api.example.com"
  - "api.example.org"
  rules:
  - backendRefs:
    - name: api-service
      port: 80
```

### 4.4 Header-Based Routing

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: header-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - headers:
      - name: X-Version
        value: v2
    backendRefs:
    - name: api-v2
      port: 80
  - matches:
    - headers:
      - name: X-Version
        value: v1
    backendRefs:
    - name: api-v1
      port: 80
```

> **Stop and think**: You want to roll out a new version of your API to 10% of users. With a standard Kubernetes Deployment, you could adjust replica counts (9 old, 1 new), but that couples scaling with routing. How does Gateway API's traffic splitting decouple these concerns?

### 4.5 Traffic Splitting (Canary/Blue-Green)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: canary-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - backendRefs:
    - name: api-stable
      port: 80
      weight: 90           # 90% to stable
    - name: api-canary
      port: 80
      weight: 10           # 10% to canary
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Traffic Splitting                             │
│                                                                 │
│   Incoming Traffic (100%)                                      │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    HTTPRoute                             │  │
│   │                                                          │  │
│   │   weight: 90          weight: 10                        │  │
│   │      │                    │                              │  │
│   │      ▼                    ▼                              │  │
│   │  ┌────────┐          ┌────────┐                         │  │
│   │  │ Stable │          │ Canary │                         │  │
│   │  │  (90%) │          │  (10%) │                         │  │
│   │  └────────┘          └────────┘                         │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 5: HTTPRoute Filters

### 5.1 Request Header Modification

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: header-filter-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
        - name: X-Custom-Header
          value: "added-by-gateway"
        remove:
        - X-Unwanted-Header
    backendRefs:
    - name: web-service
      port: 80
```

### 5.2 URL Rewrite

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: rewrite-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /old-api
    filters:
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /new-api
    backendRefs:
    - name: api-service
      port: 80
```

### 5.3 Request Redirect

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: redirect-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /old-path
    filters:
    - type: RequestRedirect
      requestRedirect:
        scheme: https
        hostname: new.example.com
        statusCode: 301
```

### 5.4 Request Mirroring

Request mirroring allows you to duplicate traffic and send a copy to another backend without affecting the primary response. This is useful for safely testing new versions with live production traffic.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mirror-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - filters:
    - type: RequestMirror
      requestMirror:
        backendRef:
          name: api-canary
          port: 80
    backendRefs:
    - name: api-stable
      port: 80
```

---

## Part 6: GRPCRoute

Gateway API provides native support for gRPC traffic through the `GRPCRoute` resource, allowing you to route requests based on gRPC services and methods rather than HTTP paths.

### 6.1 Simple GRPCRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: grpc-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - method:
        service: myapp.v1.MyService
        method: MyMethod
    backendRefs:
    - name: grpc-backend
      port: 50051
```

> **Stop and think**: Why would you use a dedicated `GRPCRoute` instead of just an `HTTPRoute`, given that gRPC uses HTTP/2? A dedicated resource allows the gateway to parse the specific protobuf service and method structures natively, making configuration much less error-prone than manual HTTP path matching.

---

> **What would happen if**: An HTTPRoute in namespace `team-a` tries to reference a Service in namespace `team-b`, but no ReferenceGrant exists in `team-b`. Does the route silently fail, return an error, or route somewhere unexpected?

## Part 7: Cross-Namespace Routing

### 7.1 ReferenceGrant

Allows routes in one namespace to reference services in another:

```yaml
# In the target namespace (where the service lives)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: ReferenceGrant
metadata:
  name: allow-routes-from-default
  namespace: backend-ns
spec:
  from:
  - group: gateway.networking.k8s.io
    kind: HTTPRoute
    namespace: default        # Allow routes from default namespace
  to:
  - group: ""
    kind: Service             # Allow referencing services
```

```yaml
# HTTPRoute in default namespace can now reference backend-ns service
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: cross-ns-route
  namespace: default
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - backendRefs:
    - name: backend-service
      namespace: backend-ns    # Cross-namespace reference
      port: 80
```

---

## Part 8: TLS Configuration

### 8.1 Gateway with TLS Termination

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: tls-gateway
spec:
  gatewayClassName: example-gateway-class
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    hostname: secure.example.com
    tls:
      mode: Terminate
      certificateRefs:
      - name: secure-tls        # TLS secret
        kind: Secret
    allowedRoutes:
      namespaces:
        from: All
```

### 8.2 TLS Modes

| Mode | Behavior |
|------|----------|
| `Terminate` | Gateway terminates TLS, sends HTTP to backends |
| `Passthrough` | Gateway passes TLS through, backend handles termination |

---

## Part 9: Debugging Gateway API

### 9.1 Debugging Workflow

```
Gateway API Issue?
    │
    ├── kubectl get gatewayclass (check controller)
    │
    ├── kubectl get gateway (check status)
    │       │
    │       └── Not Ready? → Check conditions
    │
    ├── kubectl get httproute (check if attached)
    │       │
    │       └── Not attached? → Check parentRefs
    │
    ├── kubectl describe httproute (check conditions)
    │       │
    │       └── Errors? → Fix configuration
    │
    └── Check backend services
        kubectl get svc,endpoints
```

### 9.2 Common Commands

```bash
# List all Gateway API resources
k get gatewayclass,gateway,httproute

# Check Gateway status
k describe gateway example-gateway

# Check HTTPRoute status
k describe httproute my-route

# Get HTTPRoute conditions
k get httproute my-route -o jsonpath='{.status.parents[0].conditions}'
```

### 9.3 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Gateway not Ready | No controller | Install Gateway controller |
| HTTPRoute not attached | Wrong parentRefs | Check Gateway name/namespace |
| 404 errors | No matching rule | Check path/host configuration |
| Cross-namespace fails | Missing ReferenceGrant | Create ReferenceGrant |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Missing CRDs | Resources not recognized | Install Gateway API CRDs first |
| Wrong gatewayClassName | Gateway not processed | Match GatewayClass name exactly |
| Missing parentRefs | Route not attached | Add parentRefs to HTTPRoute |
| Namespace mismatch | Cross-ns routing fails | Create ReferenceGrant |
| Wrong path type | Routes don't match | Use PathPrefix, Exact, or RegularExpression |

---

## Quiz

1. **Your team is migrating from ingress-nginx (now retired) to Gateway API. A colleague asks why you can't just keep using Ingress resources with a different controller. What limitations of Ingress does Gateway API solve that would justify the migration effort?**
   <details>
   <summary>Answer</summary>
   Ingress relies on controller-specific annotations for advanced features (rewrite rules, rate limiting, header routing), making configurations non-portable between controllers. Gateway API provides these features natively: traffic splitting with `weight`, header-based routing with `matches.headers`, URL rewriting with `URLRewrite` filters, and cross-namespace routing with `ReferenceGrant`. It also supports TCP, UDP, gRPC, and TLS natively (not just HTTP). The role-oriented model (GatewayClass/Gateway/HTTPRoute) lets platform teams manage infrastructure separately from app teams managing routes, improving security and separation of concerns.
   </details>

2. **You are a cluster operator. The security team requires that only the `payments` namespace can create HTTPRoutes that attach to the production Gateway, while all other namespaces can use the staging Gateway. How do you configure this?**
   <details>
   <summary>Answer</summary>
   On the production Gateway, set the listener's `allowedRoutes.namespaces.from: Selector` with a `namespaceSelector` matching a label like `gateway-access: production`, then label only the `payments` namespace with that label. On the staging Gateway, set `allowedRoutes.namespaces.from: All`. This way, only HTTPRoutes in the `payments` namespace can attach to the production Gateway. If a team in another namespace tries to reference the production Gateway in their HTTPRoute's `parentRefs`, the route will not be accepted and the status conditions will show it was rejected.
   </details>

3. **You are deploying a canary release. The stable version handles 95% of traffic and the canary handles 5%. After monitoring for an hour, you want to shift to 50/50. With a Deployment-based approach, you would need to scale replicas. How does Gateway API handle this differently, and what is the advantage?**
   <details>
   <summary>Answer</summary>
   With Gateway API, you change the `weight` values in the HTTPRoute's `backendRefs` from `95/5` to `50/50`. The key advantage is that traffic splitting is decoupled from scaling. You can have 10 stable pods and 2 canary pods but still send 50% of traffic to each -- the gateway handles the distribution. With Deployment-based canary (adjusting replica counts), you would need 5 stable and 5 canary pods to achieve 50/50, forcing you to over-provision the canary. Gateway API lets you scale each version independently based on actual load, not traffic percentage.
   </details>

4. **An app team creates an HTTPRoute that references a backend Service in a different namespace, but traffic returns 404. The HTTPRoute status shows "ResolvedRefs: False". What is missing and how do you fix it?**
   <details>
   <summary>Answer</summary>
   A `ReferenceGrant` is missing in the target namespace. Gateway API requires explicit permission for cross-namespace references as a security measure. Create a ReferenceGrant in the backend Service's namespace that allows HTTPRoutes from the app team's namespace to reference Services. Without it, the gateway controller refuses to resolve the backend reference. This is a deliberate security feature -- unlike Ingress where any namespace could reference any Service, Gateway API enforces explicit trust boundaries between namespaces.
   </details>

5. **You need to route requests to API v2 only when the header `X-API-Version: 2` is present, otherwise default to v1. With Ingress, this required a controller-specific annotation. Write the Gateway API HTTPRoute rules and explain why this is more portable.**
   <details>
   <summary>Answer</summary>
   Create an HTTPRoute with two rules: the first matches `headers: [{name: X-API-Version, value: "2"}]` and routes to the v2 backend; the second has no header match (default) and routes to v1. The more specific match (with header) takes priority. This is more portable because `matches.headers` is part of the Gateway API spec, not an annotation. Any conformant Gateway API implementation (Envoy Gateway, Cilium, Traefik, Kong) will handle it identically. With Ingress, you would use something like `nginx.ingress.kubernetes.io/canary-header: X-API-Version` which only works with nginx and has completely different syntax on other controllers.
   </details>

---

## Hands-On Exercise

**Task**: Create a complete Gateway API setup with routing.

**Steps**:

1. **Install Gateway API CRDs** (if not installed):
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

2. **Create backend services**:
```bash
k create deployment api --image=nginx
k create deployment web --image=nginx
k expose deployment api --port=80
k expose deployment web --port=80
```

3. **Create GatewayClass** (simulated - in real cluster, controller provides this):
```bash
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: example-class
spec:
  controllerName: example.io/gateway-controller
EOF
```

4. **Create Gateway**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-gateway
spec:
  gatewayClassName: example-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

k get gateway
k describe gateway example-gateway
```

5. **Create HTTPRoute with path routing**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: app-routes
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: web
      port: 80
EOF

k get httproute
k describe httproute app-routes
```

6. **Create HTTPRoute with traffic splitting**:
```bash
# Create canary deployment
k create deployment api-canary --image=nginx

k expose deployment api-canary --port=80

cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: canary-route
spec:
  parentRefs:
  - name: example-gateway
  hostnames:
  - "canary.example.com"
  rules:
  - backendRefs:
    - name: api
      port: 80
      weight: 90
    - name: api-canary
      port: 80
      weight: 10
EOF
```

7. **View all resources**:
```bash
k get gatewayclass,gateway,httproute
```

8. **Cleanup**:
```bash
k delete httproute app-routes canary-route
k delete gateway example-gateway
k delete gatewayclass example-class
k delete deployment api web api-canary
k delete svc api web api-canary
```

**Success Criteria**:
- [ ] Understand Gateway API resource hierarchy
- [ ] Can create Gateway and HTTPRoute
- [ ] Can configure path-based routing
- [ ] Can configure traffic splitting
- [ ] Understand role-oriented model

---

## Practice Drills

### Drill 1: Check Gateway API Installation (Target: 2 minutes)

```bash
# Check CRDs
k get crd | grep gateway

# List GatewayClasses
k get gatewayclass

# List Gateways
k get gateway -A

# List HTTPRoutes
k get httproute -A
```

### Drill 2: Create Basic Gateway (Target: 3 minutes)

```bash
# Create GatewayClass
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: drill-class
spec:
  controllerName: drill.io/controller
EOF

# Create Gateway
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: drill-gateway
spec:
  gatewayClassName: drill-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

# Verify
k get gateway drill-gateway
k describe gateway drill-gateway

# Cleanup
k delete gateway drill-gateway
k delete gatewayclass drill-class
```

### Drill 3: Path-Based HTTPRoute (Target: 4 minutes)

```bash
# Create services
k create deployment svc1 --image=nginx
k create deployment svc2 --image=nginx
k expose deployment svc1 --port=80
k expose deployment svc2 --port=80

# Create Gateway and GatewayClass
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: path-class
spec:
  controllerName: path.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: path-gateway
spec:
  gatewayClassName: path-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

# Create path-based HTTPRoute
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: path-route
spec:
  parentRefs:
  - name: path-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /service1
    backendRefs:
    - name: svc1
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /service2
    backendRefs:
    - name: svc2
      port: 80
EOF

# Verify
k describe httproute path-route

# Cleanup
k delete httproute path-route
k delete gateway path-gateway
k delete gatewayclass path-class
k delete deployment svc1 svc2
k delete svc svc1 svc2
```

### Drill 4: Traffic Splitting (Target: 4 minutes)

```bash
# Create stable and canary
k create deployment stable --image=nginx
k create deployment canary --image=nginx
k expose deployment stable --port=80
k expose deployment canary --port=80

# Create Gateway resources
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: split-class
spec:
  controllerName: split.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: split-gateway
spec:
  gatewayClassName: split-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: split-route
spec:
  parentRefs:
  - name: split-gateway
  rules:
  - backendRefs:
    - name: stable
      port: 80
      weight: 80
    - name: canary
      port: 80
      weight: 20
EOF

# Verify
k describe httproute split-route

# Cleanup
k delete httproute split-route
k delete gateway split-gateway
k delete gatewayclass split-class
k delete deployment stable canary
k delete svc stable canary
```

### Drill 5: Header-Based Routing (Target: 4 minutes)

```bash
# Create versioned services
k create deployment v1 --image=nginx
k create deployment v2 --image=nginx
k expose deployment v1 --port=80
k expose deployment v2 --port=80

# Create Gateway resources with header routing
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: header-class
spec:
  controllerName: header.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: header-gateway
spec:
  gatewayClassName: header-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: header-route
spec:
  parentRefs:
  - name: header-gateway
  rules:
  - matches:
    - headers:
      - name: X-Version
        value: v2
    backendRefs:
    - name: v2
      port: 80
  - matches:
    - headers:
      - name: X-Version
        value: v1
    backendRefs:
    - name: v1
      port: 80
EOF

# Verify
k describe httproute header-route

# Cleanup
k delete httproute header-route
k delete gateway header-gateway
k delete gatewayclass header-class
k delete deployment v1 v2
k delete svc v1 v2
```

### Drill 6: Host-Based Routing (Target: 4 minutes)

```bash
# Create services
k create deployment api --image=nginx
k create deployment web --image=nginx
k expose deployment api --port=80
k expose deployment web --port=80

# Create Gateway with host routing
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: host-class
spec:
  controllerName: host.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: host-gateway
spec:
  gatewayClassName: host-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
spec:
  parentRefs:
  - name: host-gateway
  hostnames:
  - "api.example.com"
  rules:
  - backendRefs:
    - name: api
      port: 80
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web-route
spec:
  parentRefs:
  - name: host-gateway
  hostnames:
  - "www.example.com"
  rules:
  - backendRefs:
    - name: web
      port: 80
EOF

# Verify
k get httproute

# Cleanup
k delete httproute api-route web-route
k delete gateway host-gateway
k delete gatewayclass host-class
k delete deployment api web
k delete svc api web
```

### Drill 7: Challenge - Complete Gateway API Setup

Without looking at solutions:

1. Install Gateway API CRDs (if needed)
2. Create a GatewayClass named `challenge-class`
3. Create a Gateway named `challenge-gateway` on port 80
4. Create deployments: `frontend`, `backend`, `admin`
5. Create HTTPRoutes:
   - `/admin` → admin service
   - `/api` → backend service
   - `/` → frontend service
6. Verify all resources are created
7. Cleanup everything

```bash
# YOUR TASK: Complete in under 8 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. CRDs (if needed)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# 2-3. GatewayClass and Gateway
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: challenge-class
spec:
  controllerName: challenge.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: challenge-gateway
spec:
  gatewayClassName: challenge-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

# 4. Create deployments and services
k create deployment frontend --image=nginx
k create deployment backend --image=nginx
k create deployment admin --image=nginx
k expose deployment frontend --port=80
k expose deployment backend --port=80
k expose deployment admin --port=80

# 5. Create HTTPRoutes
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: challenge-routes
spec:
  parentRefs:
  - name: challenge-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /admin
    backendRefs:
    - name: admin
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: backend
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: frontend
      port: 80
EOF

# 6. Verify
k get gatewayclass,gateway,httproute

# 7. Cleanup
k delete httproute challenge-routes
k delete gateway challenge-gateway
k delete gatewayclass challenge-class
k delete deployment frontend backend admin
k delete svc frontend backend admin
```

</details>

---

## Next Module

[Module 3.6: Network Policies](../module-3.6-network-policies/) - Controlling pod-to-pod communication.