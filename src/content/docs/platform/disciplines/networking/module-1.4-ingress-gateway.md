---
title: "Module 1.4: Ingress, Gateway API & Traffic Management"
slug: platform/disciplines/networking/module-1.4-ingress-gateway
sidebar:
  order: 5
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 55-65 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: CNI Architecture](../module-1.1-cni-architecture/) — Pod networking and Service concepts
- **Required**: [Advanced Networking foundations](../../foundations/advanced-networking/) — TLS, DNS, HTTP, load balancing
- **Recommended**: [Module 1.2: Network Policy Design](../module-1.2-network-policy-design/) — Understanding traffic flow
- **Helpful**: Experience with reverse proxies (NGINX, Traefik, HAProxy, or Envoy)

---

## Why This Module Matters

In September 2023, a retail company's entire storefront went down for 22 minutes during a flash sale because their single NGINX Ingress controller ran out of file descriptors. They had configured the Ingress for 50 backend services but never increased `worker_rlimit_nofile` beyond the default of 8192. At 140,000 concurrent connections, NGINX stopped accepting new connections. The Pods were healthy, the backends were fast, but no external traffic could reach them.

The fix was a one-line configuration change. But the deeper problem was architectural: a single Ingress controller was the chokepoint for all external traffic, with no rate limiting, no circuit breaking, and no fallback. The team had treated the Ingress controller as "just a reverse proxy" rather than a critical piece of infrastructure that deserved the same attention as the application it served.

The Kubernetes ecosystem has moved beyond the basic Ingress resource. The Gateway API (GA since v1.0 in 2023, now at v1.2+) provides a richer, role-oriented model for traffic management. This module covers both the legacy Ingress approach and the modern Gateway API, helping you choose the right ingress controller and configure production-grade traffic routing.

---

## Did You Know?

> The Kubernetes Ingress resource has been "frozen" since it reached GA in v1.19 (2020). No new features will be added to it — all innovation happens in the Gateway API. The Ingress resource will continue to be supported indefinitely but is considered a legacy API.

> Gateway API's `HTTPRoute` supports header-based routing, URL rewrites, request mirroring, and traffic splitting natively — features that required vendor-specific annotations in the Ingress resource. A single HTTPRoute manifest works across different Gateway implementations (NGINX, Envoy, Traefik) without annotation changes.

> The NGINX Ingress controller handles approximately 40% of all Kubernetes ingress traffic globally, making it one of the most widely deployed pieces of software in cloud infrastructure. However, there are TWO different NGINX Ingress controllers — the community `kubernetes/ingress-nginx` and the F5/NGINX Inc `nginxinc/kubernetes-ingress`. They have different configurations, different annotations, and different features.

> Envoy Gateway (the official Envoy-based Gateway API implementation) processes configuration changes in under 100ms, compared to NGINX Ingress which requires a full configuration reload (including establishing new worker processes) that takes 1-5 seconds depending on the number of backends.

---

## Ingress vs Gateway API

### The Ingress Resource (Legacy)

The Ingress resource provides basic HTTP/HTTPS routing:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: production
  annotations:
    # These are NGINX-specific — different controller = different annotations
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.example.com
      secretName: app-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-frontend
                port:
                  number: 80
```

**Problems with Ingress:**

| Problem | Description |
|---------|-------------|
| Vendor lock-in via annotations | Rate limiting, rewrites, auth — all in controller-specific annotations |
| Single persona | One resource controls both infra (TLS, LB) and app (routing) concerns |
| No TCP/UDP support | Only HTTP/HTTPS — can't route gRPC, databases, or raw TCP |
| No traffic splitting | Canary routing requires controller-specific annotations |
| Flat model | No concept of shared infrastructure that multiple teams can reference |

### The Gateway API (Modern)

Gateway API separates concerns by role:

```
┌─────────────────────────────────────────────────────────┐
│  Platform Team (Infra role)                              │
│                                                          │
│  GatewayClass — defines the controller implementation    │
│  Gateway — deploys and configures the actual proxy       │
│           (listeners, TLS, addresses)                    │
└──────────┬──────────────────────────────────────────────┘
           │  Platform team provides the Gateway
           │  App teams attach routes to it
┌──────────▼──────────────────────────────────────────────┐
│  Application Team (Dev role)                             │
│                                                          │
│  HTTPRoute — routes HTTP traffic to Services             │
│  GRPCRoute — routes gRPC traffic                         │
│  TLSRoute — routes TLS passthrough                       │
│  TCPRoute / UDPRoute — L4 routing                        │
└─────────────────────────────────────────────────────────┘
```

```yaml
# Platform team creates: GatewayClass + Gateway
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: production-gw-class
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller

---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
  namespace: gateway-infra
spec:
  gatewayClassName: production-gw-class
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        mode: Terminate
        certificateRefs:
          - kind: Secret
            name: wildcard-tls
            namespace: gateway-infra
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
          from: Same

---
# App team creates: HTTPRoute (in their own namespace)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: app-routes
  namespace: production     # App team's namespace
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-infra
      sectionName: https
  hostnames:
    - "app.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /api/v1
      backendRefs:
        - name: api-v1
          port: 8080
          weight: 90
        - name: api-v2
          port: 8080
          weight: 10           # 10% canary to v2
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: web-frontend
          port: 80
```

### Gateway API Route Types

| Route Type | GA Status | Purpose |
|-----------|-----------|---------|
| `HTTPRoute` | v1 (GA) | HTTP/HTTPS routing with path, header, method matching |
| `GRPCRoute` | v1 (GA) | gRPC service routing |
| `TLSRoute` | v1alpha2 | TLS passthrough (no termination) |
| `TCPRoute` | v1alpha2 | Raw TCP routing (databases, Redis) |
| `UDPRoute` | v1alpha2 | UDP routing (DNS, game servers) |

---

## Ingress Controller Comparison

### Feature Matrix

| Feature | NGINX Ingress | Traefik | Envoy Gateway | HAProxy Ingress | Contour |
|---------|:---:|:---:|:---:|:---:|:---:|
| Gateway API | Partial | Full | Full | Partial | Full |
| TCP/UDP | Yes | Yes | Yes | Yes | Yes |
| gRPC | Yes | Yes | Yes | Yes | Yes |
| Rate limiting | Annotation | Middleware | Policy | Annotation | Policy |
| Circuit breaking | No | Yes | Yes | No | Yes |
| mTLS (backend) | Annotation | File | Policy | Annotation | Policy |
| WASM plugins | No | Plugin | Yes | No | No |
| Config reload | Full reload | Hot | Hot | Hot | Hot |
| Protocol | NGINX | Go | Envoy | HAProxy | Envoy |
| Memory (idle) | ~90 MB | ~50 MB | ~120 MB | ~40 MB | ~70 MB |

### When to Choose Each

**NGINX Ingress** — Most documentation, largest community, easiest to find help. Choose when team knows NGINX, needs simple HTTP routing, and doesn't need advanced traffic management.

**Traefik** — Excellent auto-discovery, built-in dashboard, Let's Encrypt integration. Choose for dynamic environments with frequent Service changes.

**Envoy Gateway** — Most powerful Gateway API implementation, extensible via WASM and ExtProc. Choose for teams committed to Gateway API and needing advanced L7 features.

**HAProxy Ingress** — Best raw performance for high connection counts, lowest memory footprint. Choose for high-throughput, connection-heavy workloads.

**Contour** — Clean Gateway API implementation backed by Envoy, simpler than raw Envoy Gateway. Choose for teams that want Envoy without Envoy complexity.

---

## Traffic Management Patterns

### Pattern 1: Canary Routing with Gateway API

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: canary-route
  namespace: production
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-infra
  hostnames:
    - "api.example.com"
  rules:
    # Route internal testers to v2 (header-based)
    - matches:
        - headers:
            - name: X-Canary
              value: "true"
      backendRefs:
        - name: api-v2
          port: 8080
    # Route 5% of production traffic to v2 (weight-based)
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: api-v1
          port: 8080
          weight: 95
        - name: api-v2
          port: 8080
          weight: 5
```

### Pattern 2: Rate Limiting

With Envoy Gateway, rate limiting is a first-class BackendTrafficPolicy:

```yaml
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata:
  name: api-rate-limit
  namespace: production
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: HTTPRoute
      name: api-route
  rateLimit:
    type: Global
    global:
      rules:
        - clientSelectors:
            - headers:
                - name: X-API-Key
                  type: Distinct
          limit:
            requests: 100
            unit: Minute
        - limit:
            requests: 20
            unit: Minute
          # Default rate for unauthenticated traffic
```

With NGINX Ingress (annotation-based):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "50"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "5"
    nginx.ingress.kubernetes.io/limit-connections: "10"
    # Rate limit by client IP + API key header
    nginx.ingress.kubernetes.io/configuration-snippet: |
      limit_req_zone $http_x_api_key zone=apikey:10m rate=100r/m;
      limit_req zone=apikey burst=20 nodelay;
```

### Pattern 3: Circuit Breaking and Retries

```yaml
# Envoy Gateway BackendTrafficPolicy
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata:
  name: api-resilience
  namespace: production
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: HTTPRoute
      name: api-route
  circuitBreaker:
    maxConnections: 1024
    maxPendingRequests: 128
    maxRequests: 1024
  retry:
    numRetries: 3
    retryOn:
      - "5xx"
      - "reset"
      - "connect-failure"
    perRetry:
      timeout: "2s"
      backOff:
        baseInterval: "100ms"
        maxInterval: "1s"
  timeout:
    http:
      connectionIdleTimeout: "60s"
      requestTimeout: "30s"
```

### Pattern 4: URL Rewriting and Request Modification

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-rewrite
  namespace: production
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-infra
  hostnames:
    - "api.example.com"
  rules:
    # Rewrite /api/v1/* to /v1/*
    - matches:
        - path:
            type: PathPrefix
            value: /api/v1
      filters:
        - type: URLRewrite
          urlRewrite:
            path:
              type: ReplacePrefixMatch
              replacePrefixMatch: /v1
      backendRefs:
        - name: api-service
          port: 8080
    # Add request headers
    - matches:
        - path:
            type: PathPrefix
            value: /
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier:
            add:
              - name: X-Request-Source
                value: "gateway"
            set:
              - name: X-Forwarded-Proto
                value: "https"
      backendRefs:
        - name: web-frontend
          port: 80
```

### Pattern 5: Request Mirroring (Shadow Traffic)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mirror-route
  namespace: production
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-infra
  hostnames:
    - "api.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /api
      filters:
        - type: RequestMirror
          requestMirror:
            backendRef:
              name: api-v2-shadow    # Receives copy of traffic
              port: 8080
      backendRefs:
        - name: api-v1              # Serves actual response
          port: 8080
```

---

## TLS Termination Strategies

| Strategy | Where TLS Ends | Pros | Cons |
|----------|---------------|------|------|
| **Edge termination** | At the Gateway/Ingress | Simplest; centralized cert management | No encryption inside cluster |
| **Passthrough** | At the backend Pod | End-to-end encryption | Each service manages its own certs |
| **Re-encryption** | Gateway terminates, re-encrypts to backend | Encryption everywhere + centralized certs | Double TLS overhead |

### Edge Termination (Most Common)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
spec:
  gatewayClassName: envoy
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        mode: Terminate
        certificateRefs:
          - name: app-tls-cert
    - name: http-redirect
      protocol: HTTP
      port: 80
      # Redirect all HTTP to HTTPS
```

### TLS with cert-manager Automation

```yaml
# Certificate resource — cert-manager handles provisioning and renewal
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: app-tls
  namespace: gateway-infra
spec:
  secretName: app-tls-cert
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - "app.example.com"
    - "api.example.com"
    - "*.example.com"
  duration: 2160h    # 90 days
  renewBefore: 720h  # Renew 30 days before expiry
```

---

## Multi-Cluster Ingress

For applications spanning multiple clusters or regions, you need global load balancing in front of per-cluster gateways:

```
                    ┌──────────────────────┐
                    │   Global DNS / LB     │
                    │  (Cloud LB, Cloudflare│
                    │   Route53, etc.)      │
                    └─────┬───────┬─────────┘
                          │       │
              ┌───────────┘       └───────────┐
              │                               │
      ┌───────▼────────┐            ┌─────────▼──────┐
      │  Cluster A      │            │  Cluster B      │
      │  (us-east-1)    │            │  (eu-west-1)    │
      │                 │            │                  │
      │  ┌───────────┐  │            │  ┌───────────┐  │
      │  │ Gateway   │  │            │  │ Gateway   │  │
      │  │ (Envoy)   │  │            │  │ (Envoy)   │  │
      │  └─────┬─────┘  │            │  └─────┬─────┘  │
      │        │         │            │        │         │
      │  ┌─────▼─────┐  │            │  ┌─────▼─────┐  │
      │  │ Services  │  │            │  │ Services  │  │
      │  └───────────┘  │            │  └───────────┘  │
      └─────────────────┘            └─────────────────┘
```

Cloud provider solutions:
- **AWS**: Global Accelerator + ALB per cluster
- **GCP**: Multi-Cluster Gateway (native Gateway API)
- **Azure**: Front Door + Application Gateway per cluster

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using the wrong NGINX Ingress controller | Two different projects share similar names | Check the image: `registry.k8s.io/ingress-nginx/controller` (community) vs `nginx/nginx-ingress` (F5) |
| Not setting resource limits on ingress controller | Default resources are for small clusters | Set CPU/memory requests and limits; use HPA to autoscale under load |
| Mixing Ingress annotations from different controllers | Copy-paste from Stack Overflow without checking the controller | Standardize on one controller; document which annotations are valid |
| Using Ingress for non-HTTP traffic | Ingress only supports HTTP/HTTPS | Use Gateway API TCPRoute/UDPRoute or LoadBalancer Services for TCP/UDP |
| Not configuring timeouts | Default timeouts are often too long or too short | Set explicit read/write/idle timeouts matching your backend SLAs |
| Single ingress controller as SPOF | "It's just a deployment" mindset | Run 2+ replicas across zones; use PodDisruptionBudget with minAvailable: 1 |

---

## Hands-On Exercises

### Exercise 1: Deploy Gateway API with Envoy Gateway

```bash
# Create a kind cluster with port mappings
cat <<'EOF' > kind-gw.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8080
      - containerPort: 30443
        hostPort: 8443
EOF
kind create cluster --name gw-lab --config kind-gw.yaml

# Install Gateway API CRDs
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml

# Install Envoy Gateway
helm install eg oci://docker.io/envoyproxy/gateway-helm \
  --version v1.2.4 -n envoy-gateway-system --create-namespace

kubectl wait --timeout=5m -n envoy-gateway-system deployment/envoy-gateway \
  --for=condition=Available
```

**Task 1**: Create a GatewayClass and Gateway.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: lab-gateway-class
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller

---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: lab-gateway
  namespace: default
spec:
  gatewayClassName: lab-gateway-class
  listeners:
    - name: http
      protocol: HTTP
      port: 80
      allowedRoutes:
        namespaces:
          from: All
```

**Task 2**: Deploy two versions of an app and configure traffic splitting.

```bash
# Deploy v1 and v2
kubectl create deployment app-v1 --image=hashicorp/http-echo:0.2.3 -- -listen=:8080 -text="v1"
kubectl create deployment app-v2 --image=hashicorp/http-echo:0.2.3 -- -listen=:8080 -text="v2"
kubectl expose deployment app-v1 --port=8080
kubectl expose deployment app-v2 --port=8080
```

<details>
<summary>Solution: HTTPRoute with 80/20 split</summary>

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: app-split
  namespace: default
spec:
  parentRefs:
    - name: lab-gateway
  rules:
    - backendRefs:
        - name: app-v1
          port: 8080
          weight: 80
        - name: app-v2
          port: 8080
          weight: 20
```

</details>

**Task 3**: Verify the traffic split by sending 100 requests and counting responses.

```bash
# In kind, Envoy Gateway creates a LoadBalancer Service that stays in
# "Pending" state. Use port-forward to reach the gateway instead:
# Find the Envoy Gateway service created for your Gateway
GW_SVC=$(kubectl get svc -A -l gateway.envoyproxy.io/owning-gateway-name=lab-gateway \
  -o jsonpath='{.items[0].metadata.name}')
GW_NS=$(kubectl get svc -A -l gateway.envoyproxy.io/owning-gateway-name=lab-gateway \
  -o jsonpath='{.items[0].metadata.namespace}')

# Port-forward to the gateway service (run in background)
kubectl port-forward -n "$GW_NS" svc/"$GW_SVC" 8080:80 &
PF_PID=$!
sleep 2

# Send 100 requests and count v1 vs v2
for i in $(seq 1 100); do
  curl -s http://localhost:8080/ 2>/dev/null
done | sort | uniq -c
# Expected: ~80 "v1", ~20 "v2"

# Clean up port-forward
kill $PF_PID
```

### Exercise 2: Header-Based Routing

**Task**: Configure routing where requests with `X-Version: v2` header go to app-v2, all others go to app-v1.

<details>
<summary>Solution</summary>

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: header-route
  namespace: default
spec:
  parentRefs:
    - name: lab-gateway
  rules:
    - matches:
        - headers:
            - name: X-Version
              value: "v2"
      backendRefs:
        - name: app-v2
          port: 8080
    - backendRefs:
        - name: app-v1
          port: 8080
```

Test (with port-forward running as shown in Exercise 1, Task 3):
```bash
# Without header — v1
curl -s http://localhost:8080/
# With header — v2
curl -s -H "X-Version: v2" http://localhost:8080/
```

</details>

### Exercise 3: Request Mirroring

**Task**: Mirror all traffic to a shadow service for testing.

```bash
# Deploy shadow service
kubectl create deployment app-shadow --image=hashicorp/http-echo:0.2.3 -- -listen=:8080 -text="shadow"
kubectl expose deployment app-shadow --port=8080
```

<details>
<summary>Solution</summary>

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mirror-route
  namespace: default
spec:
  parentRefs:
    - name: lab-gateway
  rules:
    - filters:
        - type: RequestMirror
          requestMirror:
            backendRef:
              name: app-shadow
              port: 8080
      backendRefs:
        - name: app-v1
          port: 8080
```

Verify by checking shadow Pod logs:
```bash
kubectl logs -l app=app-shadow -f
# Should show incoming mirrored requests
```

</details>

**Success Criteria:**
- [ ] Deployed Gateway API with Envoy Gateway
- [ ] Created GatewayClass and Gateway
- [ ] Configured weight-based traffic splitting (80/20)
- [ ] Verified traffic split ratio with 100 requests
- [ ] Implemented header-based routing
- [ ] Set up request mirroring to a shadow service

---

## War Story

**The Certificate That Expired on Black Friday**

A major retail site used NGINX Ingress with a manually provisioned TLS certificate. The certificate expired at 00:00 UTC on Black Friday 2022. The team had a calendar reminder to renew it — but the engineer responsible was on vacation, and the reminder was in their personal calendar, not a shared one.

**Timeline:**
- **23:45 UTC (Thursday)** — Monitoring shows TLS certificate expiring in 15 minutes. Alert fires to Slack channel. On-call engineer is handling a different incident.
- **00:00 UTC (Friday)** — Certificate expires. All HTTPS connections fail with `ERR_CERT_DATE_INVALID`. Mobile apps show "connection not secure."
- **00:04** — On-call notices the Slack alert. Begins investigating.
- **00:11** — Engineer finds the cert is mounted from a Secret. Doesn't have access to the certificate authority to issue a new one. Begins escalation.
- **00:28** — Security team member reached. Issues emergency certificate via Let's Encrypt.
- **00:35** — New certificate Secret applied. NGINX Ingress reloads. Traffic resumes.

**Financial impact**: 35 minutes of complete HTTPS outage during the highest-traffic period of the year. $780K in lost revenue. Customer trust damage immeasurable.

**Lesson**: Never manage TLS certificates manually. Use cert-manager with automatic renewal. Set up certificate expiry monitoring with multiple notification channels. The `cert-manager` project includes a Prometheus metric `certmanager_certificate_expiration_timestamp_seconds` — alert when any certificate is within 14 days of expiry.

---

## Knowledge Check

<details>
<summary>1. What are the key advantages of Gateway API over the Ingress resource?</summary>

Gateway API provides: (1) **Role-oriented design** — separates infrastructure concerns (GatewayClass, Gateway) from application routing (HTTPRoute), enabling platform teams and app teams to work independently. (2) **Portable features** — traffic splitting, header matching, URL rewriting, and mirroring are built into the spec, not vendor-specific annotations. (3) **Multi-protocol support** — HTTPRoute, GRPCRoute, TCPRoute, UDPRoute cover protocols beyond HTTP. (4) **Cross-namespace routing** — Routes in one namespace can reference Gateways in another, with explicit permission controls. (5) **Status reporting** — Resources report their attachment status so you can see if a route is actually active.
</details>

<details>
<summary>2. What is the difference between the two NGINX Ingress controllers?</summary>

The **community** NGINX Ingress controller (`kubernetes/ingress-nginx`, image `registry.k8s.io/ingress-nginx/controller`) is maintained by the Kubernetes SIG-network team, uses NGINX open-source, and is the most widely deployed. The **F5/NGINX Inc** controller (`nginxinc/kubernetes-ingress`, image `nginx/nginx-ingress`) is maintained by F5, supports NGINX Plus features, and uses a different annotation scheme. They are NOT compatible — you cannot copy annotations between them. Always check which one you're using before following documentation.
</details>

<details>
<summary>3. Scenario: You need to send 5% of traffic to a new version for canary testing, but only for users with a specific cookie. Can you do this with Ingress? With Gateway API?</summary>

With standard **Ingress**: No. The Ingress spec has no concept of traffic splitting or cookie-based routing. Some controllers (like NGINX) support canary annotations (`nginx.ingress.kubernetes.io/canary-by-cookie`), but this is vendor-specific. With **Gateway API**: Yes, natively. Use an HTTPRoute with two rules — one matching the cookie header (routing to v2) and a default rule (routing to v1). This is portable across any Gateway API implementation.
</details>

<details>
<summary>4. Why should you use cert-manager instead of manually managing TLS certificates?</summary>

Manual certificate management fails because: (1) humans forget to renew — certificates expire during vacations, holidays, or incidents. (2) Manual processes don't scale — managing certs for 50+ services is operationally unsustainable. (3) No audit trail — who created the cert, when does it expire, who has the private key? cert-manager automates the entire lifecycle: provisioning, renewal (before expiry), and distribution as Kubernetes Secrets. It supports Let's Encrypt, Vault, AWS ACM, and other issuers. The Prometheus metrics enable alerting on expiry.
</details>

<details>
<summary>5. What is the Gateway API "role-oriented" model and why does it matter?</summary>

The Gateway API defines three roles: (1) **Infrastructure Provider** creates GatewayClass (what implementations are available). (2) **Platform Operator** creates Gateways (actual proxy deployments with listeners, TLS). (3) **Application Developer** creates Routes (HTTPRoute, GRPCRoute) that attach to Gateways. This separation matters because it enables self-service: app teams can define their own routing without needing cluster-admin access or modifying shared infrastructure. The Gateway's `allowedRoutes` field controls which namespaces can attach routes, providing security boundaries.
</details>

<details>
<summary>6. When would you choose TLS passthrough instead of edge termination?</summary>

TLS passthrough (the Gateway forwards encrypted traffic without decrypting) is needed when: (1) the backend must see the original client certificate for mutual TLS authentication (financial services, healthcare). (2) Regulatory compliance requires end-to-end encryption with no intermediate decryption. (3) The backend application manages its own certificates and you cannot change it. The trade-off is that the Gateway cannot inspect L7 content (HTTP headers, paths), so it can only route by SNI (Server Name Indication) hostname. You lose all HTTP-level features.
</details>

<details>
<summary>7. How does request mirroring work, and what is it used for?</summary>

Request mirroring (also called "shadow traffic") sends a copy of each incoming request to a secondary backend while still routing the original request to the primary backend. The response from the mirror is discarded — only the primary's response is returned to the client. This is used for: (1) testing a new service version with real production traffic without risk, (2) comparing response times or errors between old and new versions, (3) load testing a new backend with realistic traffic patterns. The client never sees the mirror's response, making it a zero-risk testing strategy.
</details>

<details>
<summary>8. Scenario: Your NGINX Ingress controller has 1 replica and is experiencing 5-second config reload times during deployments. What two changes should you make?</summary>

(1) **Scale to 2+ replicas** across different nodes/zones and add a PodDisruptionBudget. During a config reload, NGINX starts new worker processes while old ones drain — with a single replica, there's no redundancy if the reload fails. (2) **Consider switching to an Envoy-based controller** (Envoy Gateway, Contour) that performs hot configuration updates via xDS in under 100ms instead of full config file reloads. Alternatively, if staying with NGINX, reduce the reload frequency by batching config updates with `--sync-period` and increasing `worker_connections` and `worker_rlimit_nofile` to handle connection surges during reloads.
</details>

---

## Summary

The evolution from Ingress to Gateway API represents a maturation of Kubernetes traffic management. Key takeaways:

- **Gateway API is the future** — adopt it for new deployments. Use Ingress only when Gateway API support is missing in your chosen controller.
- **Choose your controller carefully** — NGINX for simplicity and community support, Envoy Gateway for advanced features, Traefik for dynamic environments.
- **Automate TLS** — cert-manager is non-negotiable. Never manage certificates manually.
- **Use traffic splitting** for safe deployments — weight-based canary, header-based routing, and request mirroring are built into Gateway API.
- **Plan for scale** — multiple replicas, resource limits, and HPA for your ingress/gateway controllers.

## What's Next

In [Module 1.5: Multi-Cluster & Hybrid Networking](../module-1.5-multi-cluster-networking/), you'll extend beyond a single cluster — connecting clusters across regions and clouds, implementing cross-cluster service discovery, and troubleshooting network issues that span cluster boundaries.
