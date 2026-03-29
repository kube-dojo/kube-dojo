---
title: "Module 9.9: Cloud-Native API Gateways & WAF"
slug: cloud/managed-services/module-9.9-api-gateways
sidebar:
  order: 10
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2.5h | **Prerequisites**: Module 9.3 (Serverless Interoperability), Kubernetes Ingress and Services, HTTP/TLS basics

## Why This Module Matters

In October 2023, a B2B SaaS company exposed their API through a Kubernetes NGINX Ingress controller. They had rate limiting configured in NGINX annotations and felt secure. During a product launch, a competitor's automated scraping bot hit their pricing API at 50,000 requests per second from 12,000 different IP addresses -- a distributed scraping attack that looked like legitimate traffic. The NGINX rate limiter, configured per-IP, was useless against distributed attacks. The API pods were overwhelmed, legitimate customers got 503 errors for 45 minutes, and three enterprise deals fell through.

The postmortem identified the missing layer: a Web Application Firewall (WAF) with bot detection, combined with an API gateway that could enforce global rate limits (not just per-IP), authenticate requests before they reach the cluster, and block known attack patterns. The NGINX Ingress was doing routing -- but routing alone is not security.

This module teaches you the difference between cloud API gateways and the Kubernetes Gateway API, how to integrate WAF protection with your cluster, rate limiting strategies that actually work against distributed attacks, OAuth2/OIDC integration for API authentication, and how to handle gRPC and WebSocket traffic through gateways.

---

## Cloud API Gateways vs Kubernetes Gateway API

These are not competing technologies. They operate at different layers and solve different problems.

### Where Each Lives

```
Internet
    |
    v
+------------------------+
| Cloud API Gateway      |  <-- Layer 7: Auth, WAF, rate limit, caching
| (AWS API GW, GCP API   |      Managed by cloud provider
|  GW, Azure APIM)       |      Outside the cluster
+------------------------+
    |
    v
+------------------------+
| K8s Gateway API /      |  <-- Layer 7: Routing, TLS termination,
| Ingress Controller     |      traffic splitting
| (Envoy, NGINX, Istio)  |      Inside the cluster
+------------------------+
    |
    v
+------------------------+
| K8s Services / Pods    |  <-- Your application
+------------------------+
```

### Feature Comparison

| Feature | Cloud API Gateway | K8s Gateway API | K8s Ingress |
|---------|------------------|-----------------|-------------|
| WAF integration | Native | Manual (requires sidecar) | Not available |
| Global rate limiting | Built-in (per key, per plan) | Via extension (e.g., Envoy RLS) | Basic (per-IP annotation) |
| OAuth2/OIDC | Built-in (JWT validation) | Via extension or middleware | OAuth2 Proxy sidecar |
| API versioning | Path/header-based routing | HTTPRoute path matching | Path-based only |
| Usage plans / throttling | Built-in (API keys, quotas) | Not native | Not available |
| WebSocket support | Yes (with limitations) | Full | Full |
| gRPC support | Yes (AWS, GCP) | Full (GRPCRoute) | Annotation-dependent |
| Cost | Per-request pricing | Compute cost of controller | Compute cost of controller |
| Custom domain + TLS | Managed certificates | cert-manager integration | cert-manager integration |

### When to Use Each

| Scenario | Recommended Approach |
|----------|---------------------|
| Public API with usage plans, API keys, monetization | Cloud API Gateway |
| Internal service-to-service routing | K8s Gateway API |
| Public-facing web application | Cloud API Gateway (WAF) + K8s Gateway API (routing) |
| Multi-protocol (HTTP + gRPC + WebSocket) | K8s Gateway API |
| Simple path-based routing, small team | K8s Ingress (sufficient) |

---

## Kubernetes Gateway API

The Gateway API is the successor to the Ingress resource. It provides more expressive routing, protocol support, and role separation.

### Core Resources

```
                        +-------------------+
                        | GatewayClass      |  <-- Infra provider
                        | (who provides it) |
                        +--------+----------+
                                 |
                        +--------+----------+
                        | Gateway           |  <-- Platform team
                        | (listeners, TLS)  |
                        +--------+----------+
                                 |
               +-----------------+-----------------+
               |                 |                 |
    +----------+---+  +----------+---+  +----------+---+
    | HTTPRoute    |  | GRPCRoute    |  | TCPRoute     |
    | (HTTP rules) |  | (gRPC rules) |  | (TCP rules)  |
    +--------------+  +--------------+  +--------------+
         App team          App team          App team
```

### Gateway and HTTPRoute

```yaml
# Platform team creates the Gateway
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
  namespace: gateway-system
spec:
  gatewayClassName: envoy
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        mode: Terminate
        certificateRefs:
          - name: wildcard-tls
            kind: Secret
      allowedRoutes:
        namespaces:
          from: Selector
          selector:
            matchLabels:
              gateway-access: "true"
    - name: http-redirect
      protocol: HTTP
      port: 80
---
# App team creates HTTPRoutes in their namespace
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-routes
  namespace: production
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-system
  hostnames:
    - "api.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /api/v1/orders
      backendRefs:
        - name: order-service
          port: 8080
          weight: 100
    - matches:
        - path:
            type: PathPrefix
            value: /api/v1/products
      backendRefs:
        - name: product-service
          port: 8080
          weight: 90
        - name: product-service-canary
          port: 8080
          weight: 10
    - matches:
        - path:
            type: PathPrefix
            value: /api/v2/products
          headers:
            - name: X-Beta-User
              value: "true"
      backendRefs:
        - name: product-service-v2
          port: 8080
```

### GRPCRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: grpc-services
  namespace: production
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-system
  hostnames:
    - "grpc.example.com"
  rules:
    - matches:
        - method:
            service: orders.OrderService
      backendRefs:
        - name: order-grpc-service
          port: 9090
    - matches:
        - method:
            service: products.ProductService
      backendRefs:
        - name: product-grpc-service
          port: 9090
```

---

## WAF Integration

A Web Application Firewall inspects HTTP traffic and blocks known attack patterns (SQL injection, XSS, path traversal, bot traffic).

### Cloud WAF Architecture

```
  Internet
      |
      v
  +--------+
  | WAF    |  Block: SQLi, XSS, bot, geo-restrict
  +--------+
      |
      v
  +--------+
  | API GW |  Auth, rate limit, cache
  +--------+
      |
      v
  +--------+
  | K8s    |  Route to pods
  | Gateway|
  +--------+
```

### AWS WAF with ALB Ingress

```bash
# Create WAF Web ACL
aws wafv2 create-web-acl \
  --name k8s-api-protection \
  --scope REGIONAL \
  --default-action '{"Allow":{}}' \
  --rules '[
    {
      "Name": "AWS-AWSManagedRulesCommonRuleSet",
      "Priority": 1,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRuleSet"
      }
    },
    {
      "Name": "AWS-AWSManagedRulesSQLiRuleSet",
      "Priority": 2,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesSQLiRuleSet"
        }
      },
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "SQLiRuleSet"
      }
    },
    {
      "Name": "RateLimit-Global",
      "Priority": 3,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": {"Block": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimit"
      }
    }
  ]' \
  --visibility-config '{
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "k8s-api-waf"
  }'

# Associate WAF with ALB (used by AWS Load Balancer Controller)
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:us-east-1:123456789:regional/webacl/k8s-api-protection/abc123 \
  --resource-arn arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/app/k8s-alb/abc123
```

### AWS Load Balancer Controller Ingress with WAF

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:us-east-1:123456789:regional/webacl/k8s-api-protection/abc123
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789:certificate/abc123
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8080
```

### GCP Cloud Armor with GKE Ingress

```bash
# Create Cloud Armor security policy
gcloud compute security-policies create api-protection \
  --description "WAF for K8s API"

# Add OWASP rules
gcloud compute security-policies rules create 1000 \
  --security-policy api-protection \
  --expression "evaluatePreconfiguredExpr('sqli-v33-stable')" \
  --action deny-403

gcloud compute security-policies rules create 1001 \
  --security-policy api-protection \
  --expression "evaluatePreconfiguredExpr('xss-v33-stable')" \
  --action deny-403

# Rate limiting
gcloud compute security-policies rules create 1002 \
  --security-policy api-protection \
  --expression "true" \
  --action throttle \
  --rate-limit-threshold-count 100 \
  --rate-limit-threshold-interval-sec 60 \
  --conform-action allow \
  --exceed-action deny-429 \
  --enforce-on-key IP
```

```yaml
# GKE BackendConfig for Cloud Armor
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: api-backend-config
  namespace: production
spec:
  securityPolicy:
    name: api-protection
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: production
  annotations:
    cloud.google.com/backend-config: '{"default": "api-backend-config"}'
spec:
  selector:
    app: api-server
  ports:
    - port: 8080
```

---

## Rate Limiting That Actually Works

Per-IP rate limiting fails against distributed attacks. Effective rate limiting requires multiple strategies.

### Rate Limiting Strategies

| Strategy | Blocks | Does Not Block |
|----------|--------|---------------|
| Per-IP | Single-source floods | Distributed attacks (botnet) |
| Per-API-key | Abusive API consumers | Unauthenticated attacks |
| Per-user (JWT claim) | Abusive authenticated users | Bot traffic |
| Global (total RPS) | DDoS beyond capacity | Targeted abuse within limits |
| Per-path | Abuse of expensive endpoints | Wide-spectrum attacks |

### Envoy Rate Limit Service

For Kubernetes-native rate limiting, deploy an Envoy rate limit service:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ratelimit
  namespace: gateway-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ratelimit
  template:
    metadata:
      labels:
        app: ratelimit
    spec:
      containers:
        - name: ratelimit
          image: envoyproxy/ratelimit:master
          ports:
            - containerPort: 8080
            - containerPort: 8081
            - containerPort: 6070
          env:
            - name: RUNTIME_ROOT
              value: /data
            - name: RUNTIME_SUBDIRECTORY
              value: ratelimit
            - name: REDIS_SOCKET_TYPE
              value: tcp
            - name: REDIS_URL
              value: redis-master.cache.svc:6379
            - name: USE_STATSD
              value: "false"
          volumeMounts:
            - name: config
              mountPath: /data/ratelimit/config
      volumes:
        - name: config
          configMap:
            name: ratelimit-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ratelimit-config
  namespace: gateway-system
data:
  config.yaml: |
    domain: production
    descriptors:
      # Global rate limit: 10,000 RPS total
      - key: generic_key
        value: global
        rate_limit:
          unit: second
          requests_per_unit: 10000
      # Per-API-key limit: 100 RPS
      - key: header_match
        value: api-key
        rate_limit:
          unit: second
          requests_per_unit: 100
      # Expensive endpoint: 10 RPS per user
      - key: header_match
        value: expensive-endpoint
        descriptors:
          - key: user_id
            rate_limit:
              unit: second
              requests_per_unit: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ratelimit
  namespace: gateway-system
spec:
  selector:
    app: ratelimit
  ports:
    - name: grpc
      port: 8081
```

---

## OAuth2/OIDC Proxying

Instead of implementing authentication in every service, use an authentication proxy at the gateway level.

### OAuth2 Proxy Architecture

```
  Client (with cookie/token)
       |
       v
  +-----------------+
  | OAuth2 Proxy    |  Validates token, redirects to IdP
  | (or gateway     |  if unauthenticated
  |  built-in)      |
  +--------+--------+
           |
           | X-Forwarded-User: alice@example.com
           | X-Forwarded-Groups: engineering,admin
           v
  +-----------------+
  | Application Pod |  Trusts headers from proxy
  +-----------------+
```

### OAuth2 Proxy Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: auth
spec:
  replicas: 2
  selector:
    matchLabels:
      app: oauth2-proxy
  template:
    metadata:
      labels:
        app: oauth2-proxy
    spec:
      containers:
        - name: oauth2-proxy
          image: quay.io/oauth2-proxy/oauth2-proxy:v7.7.0
          args:
            - --provider=oidc
            - --oidc-issuer-url=https://accounts.google.com
            - --client-id=$(CLIENT_ID)
            - --client-secret=$(CLIENT_SECRET)
            - --cookie-secret=$(COOKIE_SECRET)
            - --email-domain=example.com
            - --upstream=http://api-service.production.svc:8080
            - --http-address=0.0.0.0:4180
            - --pass-authorization-header=true
            - --set-xauthrequest=true
            - --cookie-secure=true
            - --cookie-samesite=lax
          env:
            - name: CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: oauth2-proxy-config
                  key: client-id
            - name: CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: oauth2-proxy-config
                  key: client-secret
            - name: COOKIE_SECRET
              valueFrom:
                secretKeyRef:
                  name: oauth2-proxy-config
                  key: cookie-secret
          ports:
            - containerPort: 4180
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: oauth2-proxy
  namespace: auth
spec:
  selector:
    app: oauth2-proxy
  ports:
    - port: 4180
```

### JWT Validation at the Gateway (Without Proxy)

Cloud API Gateways can validate JWT tokens directly without a separate proxy:

```bash
# AWS API Gateway: JWT Authorizer
aws apigatewayv2 create-authorizer \
  --api-id $API_ID \
  --authorizer-type JWT \
  --name oidc-auth \
  --identity-source '$request.header.Authorization' \
  --jwt-configuration '{
    "Audience": ["api.example.com"],
    "Issuer": "https://login.microsoftonline.com/TENANT_ID/v2.0"
  }'

# Attach to route
aws apigatewayv2 update-route \
  --api-id $API_ID \
  --route-id $ROUTE_ID \
  --authorization-type JWT \
  --authorizer-id $AUTH_ID
```

### Envoy Gateway JWT Authentication

```yaml
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: SecurityPolicy
metadata:
  name: jwt-auth
  namespace: gateway-system
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: api-routes
  jwt:
    providers:
      - name: google
        issuer: https://accounts.google.com
        audiences:
          - api.example.com
        remoteJWKS:
          uri: https://www.googleapis.com/oauth2/v3/certs
        claimToHeaders:
          - claim: email
            header: X-User-Email
          - claim: groups
            header: X-User-Groups
```

---

## gRPC and WebSocket Through Gateways

### gRPC Requirements

gRPC uses HTTP/2 with long-lived streams. Not all gateways handle this correctly.

| Gateway | gRPC Support | Configuration |
|---------|-------------|---------------|
| AWS ALB | Yes (HTTP/2) | Target group protocol: gRPC |
| AWS API Gateway | Yes (HTTP API) | Integration type: HTTP_PROXY with gRPC |
| GCP GCLB | Yes (HTTP/2) | Backend service protocol: HTTP2 |
| Azure App Gateway v2 | Yes (HTTP/2) | Backend protocol: HTTP/2 |
| Envoy Gateway | Yes (native) | GRPCRoute resource |
| NGINX Ingress | Yes | `nginx.org/grpc-services` annotation |

```yaml
# ALB Ingress for gRPC
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grpc-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/backend-protocol-version: GRPC
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
    - host: grpc.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: grpc-service
                port:
                  number: 9090
```

### WebSocket Support

WebSockets require connection upgrades that some gateways handle differently:

```yaml
# Gateway API: WebSocket works with HTTPRoute (connection upgrade is automatic)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: websocket-route
  namespace: production
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-system
  hostnames:
    - "ws.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /ws
      backendRefs:
        - name: websocket-service
          port: 8080
```

```yaml
# NGINX Ingress: Requires explicit timeout configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: websocket-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/connection-proxy-header: "keep-alive"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$request_uri"
spec:
  rules:
    - host: ws.example.com
      http:
        paths:
          - path: /ws
            pathType: Prefix
            backend:
              service:
                name: websocket-service
                port:
                  number: 8080
```

---

## Did You Know?

1. **AWS WAF processes over 1.5 trillion web requests per month** across all its customers. The top three attack types blocked are SQL injection (34%), cross-site scripting (28%), and path traversal (19%). AWS maintains a team of security researchers who update managed rule sets weekly based on emerging threats.

2. **The Kubernetes Gateway API was released as v1.0 (GA) in October 2023** after three years of development. It replaced the Ingress resource, which had been the standard since Kubernetes 1.1 (2015). The main motivation was that Ingress relied heavily on non-standard annotations, making configurations vendor-specific and non-portable.

3. **gRPC was created by Google in 2015** and uses Protocol Buffers for serialization. It is 5-10x faster than REST/JSON for structured data exchange because Protobuf is a binary format (smaller payloads) and HTTP/2 enables multiplexing (multiple requests on one connection). Over 60% of inter-service communication at Google uses gRPC.

4. **OAuth2 Proxy was originally created by Bitly** (the URL shortening company) in 2014 as "Google Auth Proxy." It was renamed and expanded to support OIDC, GitHub, Azure AD, and other providers. It is now the most widely used authentication proxy in Kubernetes, with over 9,000 GitHub stars and millions of downloads.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using only per-IP rate limiting | Simplest to configure | Layer multiple strategies: per-IP, per-API-key, per-user, global ceiling |
| Not putting WAF in front of the cluster | "Our API validates input" | WAF catches attacks that bypass application validation; defense in depth |
| Implementing auth in every microservice | "Each service should be independent" | Centralize auth at the gateway; pass identity headers downstream |
| Using Ingress annotations for complex routing | Ingress was designed for simple routing | Migrate to Gateway API for path/header matching, traffic splitting, cross-namespace routing |
| Setting WebSocket timeouts too low | Default NGINX proxy timeout is 60 seconds | Increase `proxy-read-timeout` and `proxy-send-timeout` to 3600+ for WebSocket |
| Exposing gRPC without TLS | "It is internal" | gRPC metadata (headers) can contain sensitive data; always use TLS |
| Not testing WAF rules in count mode first | Eager to block attacks | Deploy WAF rules in count/monitor mode, review false positives, then switch to block |
| Putting cloud API Gateway and K8s Ingress on the same path without understanding the layers | "One gateway is enough" | Understand that cloud API GW handles edge concerns (WAF, auth, rate limit) and K8s Gateway handles internal routing |

---

## Quiz

<details>
<summary>1. What is the fundamental difference between a cloud API gateway and the Kubernetes Gateway API?</summary>

A cloud API gateway (AWS API Gateway, GCP API Gateway, Azure APIM) runs outside the Kubernetes cluster as a managed service. It handles edge concerns: WAF, authentication, rate limiting, API key management, and usage plans. The Kubernetes Gateway API runs inside the cluster as a controller (Envoy, NGINX, Istio). It handles routing: path-based routing, header matching, traffic splitting, TLS termination, and protocol-specific routing (HTTP, gRPC, TCP). In production, you often use both: the cloud gateway for security and the Kubernetes gateway for routing. They are complementary layers, not competitors.
</details>

<details>
<summary>2. Why does per-IP rate limiting fail against distributed attacks?</summary>

Per-IP rate limiting blocks a single IP address after it exceeds a threshold. Distributed attacks (botnets, residential proxies) use thousands of different IP addresses, each staying below the per-IP limit. If your limit is 100 requests per second per IP, an attacker with 10,000 IPs can send 1,000,000 requests per second while every individual IP stays under the limit. Effective defense requires layered rate limiting: per-IP (catches simple floods), per-API-key or per-user (catches application-level abuse), and global ceiling (protects total capacity).
</details>

<details>
<summary>3. Explain why WAF rules should be deployed in count/monitor mode before switching to block mode.</summary>

WAF rules use pattern matching that can produce false positives -- blocking legitimate requests that happen to match an attack pattern. For example, a SQL injection rule might block a legitimate search query containing the word "SELECT" or "UNION." Deploying in count mode lets you see what would be blocked without actually blocking it. You can review the matched requests, identify false positives, add exceptions for legitimate patterns, and then confidently switch to block mode. Deploying directly in block mode risks breaking legitimate traffic, which is often worse than the attack you are trying to prevent.
</details>

<details>
<summary>4. How does the Kubernetes Gateway API improve on the Ingress resource?</summary>

The Ingress resource had three main limitations: (1) complex configurations required non-standard annotations that were different for every controller vendor, making configs non-portable; (2) no support for protocols beyond HTTP (no native gRPC, TCP, or UDP routing); (3) no role separation -- a single resource handled both infrastructure concerns (TLS, listeners) and application concerns (routes). The Gateway API solves all three: it uses typed resources (GatewayClass, Gateway, HTTPRoute, GRPCRoute) instead of annotations, supports multiple protocols natively, and separates infrastructure (Gateway, managed by platform teams) from routing (Routes, managed by application teams).
</details>

<details>
<summary>5. When would you use OAuth2 Proxy versus JWT validation at the gateway?</summary>

OAuth2 Proxy is needed when you have browser-based applications that use the OAuth2 Authorization Code flow with cookies. The proxy handles the redirect to the identity provider, token exchange, and cookie management. JWT validation at the gateway is for API clients that already have a JWT token (obtained through client credentials, device flow, or a frontend that handles the OAuth flow). Gateway JWT validation just checks the token signature and claims -- it does not handle the OAuth flow itself. Use OAuth2 Proxy for user-facing web apps; use gateway JWT validation for API-to-API communication and mobile apps.
</details>

<details>
<summary>6. What special considerations exist for routing gRPC traffic through API gateways?</summary>

gRPC requires HTTP/2 support (not HTTP/1.1), which not all gateways handle correctly. The gateway must support HTTP/2 end-to-end or at minimum for the backend connection. gRPC uses `application/grpc` content type, which some WAF rules may block as unexpected. gRPC services use a single HTTP/2 connection with multiplexed streams, so connection-based rate limiting is ineffective -- you need stream-based or request-based limiting. Additionally, gRPC health checking uses a different protocol than HTTP health checks, requiring the gateway to support gRPC health checking or fall back to TCP checks.
</details>

---

## Hands-On Exercise: Gateway API with Rate Limiting

### Setup

```bash
# Create kind cluster with extra ports
cat > /tmp/kind-gateway.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
      - containerPort: 443
        hostPort: 8443
  - role: worker
  - role: worker
EOF

kind create cluster --name gateway-lab --config /tmp/kind-gateway.yaml

# Install Gateway API CRDs
k apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml

# Install Envoy Gateway
helm install eg oci://docker.io/envoyproxy/gateway-helm \
  --version v1.2.0 \
  --namespace envoy-gateway-system --create-namespace

k wait --for=condition=ready pod -l control-plane=envoy-gateway \
  --namespace envoy-gateway-system --timeout=120s
```

### Task 1: Create a Gateway and Backend Services

Deploy two backend services and a Gateway.

<details>
<summary>Solution</summary>

```yaml
# Backend services
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo-v1
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echo
      version: v1
  template:
    metadata:
      labels:
        app: echo
        version: v1
    spec:
      containers:
        - name: echo
          image: hashicorp/http-echo
          args: ["-text=Hello from v1", "-listen=:8080"]
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: echo-v1
spec:
  selector:
    app: echo
    version: v1
  ports:
    - port: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo-v2
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: echo
      version: v2
  template:
    metadata:
      labels:
        app: echo
        version: v2
    spec:
      containers:
        - name: echo
          image: hashicorp/http-echo
          args: ["-text=Hello from v2 (canary)", "-listen=:8080"]
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: echo-v2
spec:
  selector:
    app: echo
    version: v2
  ports:
    - port: 8080
---
# Gateway
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: eg
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: lab-gateway
  namespace: default
spec:
  gatewayClassName: eg
  listeners:
    - name: http
      protocol: HTTP
      port: 80
```

```bash
k apply -f /tmp/gateway-setup.yaml
k wait --for=condition=programmed gateway/lab-gateway --timeout=60s
```
</details>

### Task 2: Configure HTTPRoutes with Traffic Splitting

Create an HTTPRoute that sends 80% of traffic to v1 and 20% to v2.

<details>
<summary>Solution</summary>

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: echo-route
  namespace: default
spec:
  parentRefs:
    - name: lab-gateway
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: echo-v1
          port: 8080
          weight: 80
        - name: echo-v2
          port: 8080
          weight: 20
```

```bash
k apply -f /tmp/httproute.yaml

# Get the gateway's external address
GW_IP=$(k get gateway lab-gateway -o jsonpath='{.status.addresses[0].value}')
echo "Gateway IP: $GW_IP"

# Test traffic splitting (send 20 requests)
for i in $(seq 1 20); do
  k run curl-$i --rm -it --image=curlimages/curl --restart=Never -- \
    curl -s http://$GW_IP/ 2>/dev/null
done
```
</details>

### Task 3: Add Header-Based Routing

Add a rule that routes requests with `X-Version: v2` header to the v2 service.

<details>
<summary>Solution</summary>

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: echo-route
  namespace: default
spec:
  parentRefs:
    - name: lab-gateway
  rules:
    # Header-based routing (higher priority)
    - matches:
        - headers:
            - name: X-Version
              value: v2
      backendRefs:
        - name: echo-v2
          port: 8080
    # Default: traffic split
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: echo-v1
          port: 8080
          weight: 80
        - name: echo-v2
          port: 8080
          weight: 20
```

```bash
k apply -f /tmp/httproute-headers.yaml

GW_IP=$(k get gateway lab-gateway -o jsonpath='{.status.addresses[0].value}')

# Test header-based routing
k run header-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s -H "X-Version: v2" http://$GW_IP/
# Should always return "Hello from v2 (canary)"
```
</details>

### Task 4: Simulate Rate Limiting with a Test Client

Send rapid requests and observe behavior under load.

<details>
<summary>Solution</summary>

```bash
# Deploy a load generator
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: load-test
spec:
  restartPolicy: Never
  containers:
    - name: load
      image: curlimages/curl
      command:
        - /bin/sh
        - -c
        - |
          GW_IP=$(getent hosts lab-gateway-eg.default.svc.cluster.local | awk '{print $1}')
          # If gateway service is not resolvable, use the gateway IP
          GW_IP=${GW_IP:-$(cat /tmp/gw-ip 2>/dev/null)}

          echo "Sending 100 rapid requests..."
          SUCCESS=0
          FAIL=0
          for i in $(seq 1 100); do
            STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://echo-v1:8080/ 2>/dev/null)
            if [ "$STATUS" = "200" ]; then
              SUCCESS=$((SUCCESS + 1))
            else
              FAIL=$((FAIL + 1))
            fi
          done
          echo "Results: $SUCCESS successful, $FAIL failed/rate-limited"
EOF

k wait --for=condition=ready pod/load-test --timeout=30s
sleep 10
k logs load-test
```
</details>

### Success Criteria

- [ ] Gateway is created and programmed
- [ ] HTTPRoute splits traffic ~80/20 between v1 and v2
- [ ] Header-based routing sends X-Version: v2 requests to v2
- [ ] Load test completes and shows request results

### Cleanup

```bash
kind delete cluster --name gateway-lab
```

---

**Next Module**: [Module 9.10: Data Warehousing & Analytics from Kubernetes](module-9.10-analytics/) -- Learn how to connect Kubernetes workloads to BigQuery, Redshift, and Snowflake, orchestrate data pipelines with Airflow, and control analytics costs.
