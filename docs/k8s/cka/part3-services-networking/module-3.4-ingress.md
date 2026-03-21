# Module 3.4: Ingress

> **Complexity**: `[MEDIUM]` - HTTP/HTTPS routing
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 3.1 (Services), Module 3.3 (DNS)

---

## Why This Module Matters

While Services expose applications to the network, Ingress provides **HTTP/HTTPS routing** with features like path-based routing, virtual hosts, and TLS termination. Instead of exposing many NodePorts, you expose one Ingress controller that routes traffic based on URLs.

The CKA exam tests Ingress creation, path routing, and understanding how Ingress connects to Services. You'll need to create Ingress resources quickly and debug routing issues.

> **Important: Ingress-NGINX Controller Retirement**
>
> The popular **ingress-nginx controller** reached end-of-life on **March 31, 2026**. After this date, it receives no releases, bug fixes, or security patches. However, the **Ingress API itself** (`networking.k8s.io/v1`) is **NOT deprecated** and remains fully supported in Kubernetes. You should learn Ingress (it's still on the exam and widely deployed) but use **Gateway API** (Module 3.5) for new deployments. Alternative controllers that support both Ingress and Gateway API include **Envoy Gateway**, **Traefik**, **Kong**, **Cilium**, and **NGINX Gateway Fabric**.
>
> If you're migrating from ingress-nginx, use the **Ingress2Gateway 1.0** tool to convert Ingress resources to Gateway API resources: `kubectl krew install ingress2gateway`

> **The Hotel Reception Analogy**
>
> Think of Ingress as a hotel reception desk. Guests (HTTP requests) arrive at the main entrance (single IP). The receptionist (Ingress controller) asks where they want to go—Room 101 (path `/api`) goes to the API service, Room 202 (path `/web`) goes to the web service. One entry point, intelligent routing inside.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand Ingress vs LoadBalancer vs NodePort
- Create Ingress resources with path and host rules
- Configure TLS termination
- Debug Ingress routing issues
- Work with different Ingress controllers

---

## Did You Know?

- **Ingress requires a controller**: The Ingress resource does nothing by itself. You need an Ingress controller (like Envoy Gateway, Traefik, or Kong) to actually route traffic.

- **Gateway API is the recommended successor**: Gateway API (covered in Module 3.5) is now GA and the recommended standard for new deployments. Ingress remains supported and widely deployed, but new projects should prefer Gateway API.

- **One Ingress, many services**: A single Ingress resource can route to dozens of backend services based on paths and hostnames.

- **Ingress-NGINX is retired**: The once-dominant ingress-nginx controller reached end-of-life on March 31, 2026. The Ingress2Gateway 1.0 tool helps migrate existing Ingress resources to Gateway API.

---

## Part 1: Ingress Architecture

### 1.1 How Ingress Works

```
┌────────────────────────────────────────────────────────────────┐
│                   Ingress Architecture                          │
│                                                                 │
│   External Traffic                                              │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │            Load Balancer / NodePort                      │  │
│   │            (Ingress Controller's Service)                │  │
│   └────────────────────────┬────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Ingress Controller                          │  │
│   │              (nginx, traefik, etc.)                     │  │
│   │                                                          │  │
│   │   Reads Ingress resources and configures routing        │  │
│   └─────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│               ┌─────────────┼─────────────┐                    │
│               │             │             │                    │
│               ▼             ▼             ▼                    │
│         ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│         │ Service  │  │ Service  │  │ Service  │             │
│         │   /api   │  │   /web   │  │   /docs  │             │
│         └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│              │             │             │                    │
│              ▼             ▼             ▼                    │
│         ┌──────┐      ┌──────┐      ┌──────┐                 │
│         │ Pods │      │ Pods │      │ Pods │                 │
│         └──────┘      └──────┘      └──────┘                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Ingress vs Other Options

| Feature | NodePort | LoadBalancer | Ingress |
|---------|----------|--------------|---------|
| Layer | L4 (TCP/UDP) | L4 (TCP/UDP) | L7 (HTTP/HTTPS) |
| Path routing | No | No | Yes |
| Virtual hosts | No | No | Yes |
| TLS termination | No | Limited | Yes |
| Cost | Free | $ per LB | One controller for many services |
| External IP | Node IP:Port | Cloud LB IP | Controller's IP |

### 1.3 Components Needed

| Component | Purpose | Who Creates |
|-----------|---------|-------------|
| Ingress Controller | Actually routes traffic | Cluster admin |
| Ingress Resource | Defines routing rules | Developer |
| Backend Services | Target services | Developer |
| TLS Secret | HTTPS certificates | Developer/cert-manager |

---

## Part 2: Ingress Controllers

### 2.1 Popular Ingress Controllers

| Controller | Description | Best For |
|------------|-------------|----------|
| **nginx** | Most common, feature-rich | General use |
| **traefik** | Auto-discovery, modern | Dynamic environments |
| **haproxy** | High performance | High-traffic sites |
| **contour** | Envoy-based | Service mesh users |
| **AWS ALB** | Native AWS integration | AWS environments |

### 2.2 Installing nginx Ingress Controller (kind/minikube)

```bash
# For kind
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# For minikube
minikube addons enable ingress

# Verify installation
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### 2.3 Check Ingress Controller Status

```bash
# Check pods
k get pods -n ingress-nginx

# Check service
k get svc -n ingress-nginx

# Check IngressClass
k get ingressclass
```

---

## Part 3: Creating Ingress Resources

### 3.1 Simple Ingress (Single Service)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-ingress
spec:
  ingressClassName: nginx            # Which controller to use
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service        # Target service
            port:
              number: 80             # Service port
```

### 3.2 Path-Based Routing

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: default-service
            port:
              number: 80
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Path-Based Routing                            │
│                                                                 │
│   Request: http://mysite.com/api/users                         │
│                        │                                        │
│                        ▼                                        │
│   ┌────────────────────────────────────────────────────────┐   │
│   │                    Ingress                              │   │
│   │                                                         │   │
│   │   /api/*  ──────────► api-service                      │   │
│   │   /web/*  ──────────► web-service                      │   │
│   │   /*      ──────────► default-service                  │   │
│   │                                                         │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.3 Path Types

| PathType | Behavior | Example |
|----------|----------|---------|
| `Exact` | Exact match only | `/api` matches `/api`, not `/api/` |
| `Prefix` | Prefix match | `/api` matches `/api`, `/api/users` |
| `ImplementationSpecific` | Controller decides | Varies by controller |

### 3.4 Host-Based Routing (Virtual Hosts)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: virtual-host-ingress
spec:
  ingressClassName: nginx
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
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Host-Based Routing                            │
│                                                                 │
│   api.example.com  ──────────► api-service                     │
│   web.example.com  ──────────► web-service                     │
│   *.example.com    ──────────► default-service (if configured) │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.5 Combining Host and Path Routing

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: combined-ingress
spec:
  ingressClassName: nginx
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
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
  - host: admin.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-service
            port:
              number: 80
```

---

## Part 4: TLS/HTTPS Configuration

### 4.1 Creating TLS Secret

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=example.com"

# Create secret
k create secret tls example-tls --cert=tls.crt --key=tls.key

# Or using kubectl
k create secret tls example-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

### 4.2 Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - example.com
    - www.example.com
    secretName: example-tls      # TLS secret name
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 4.3 TLS Configuration Flow

```
┌────────────────────────────────────────────────────────────────┐
│                   TLS Termination                               │
│                                                                 │
│   Client (HTTPS)                                               │
│        │                                                        │
│        │ TLS/SSL encrypted                                     │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Ingress Controller                          │  │
│   │              (TLS terminates here)                       │  │
│   │                                                          │  │
│   │   Uses certificate from Secret: example-tls             │  │
│   └─────────────────────────────────────────────────────────┘  │
│        │                                                        │
│        │ Plain HTTP (inside cluster)                           │
│        ▼                                                        │
│   ┌──────────────────┐                                         │
│   │     Service      │                                         │
│   │     (port 80)    │                                         │
│   └──────────────────┘                                         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 5: Ingress Annotations

### 5.1 Common nginx Annotations

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: annotated-ingress
  annotations:
    # Rewrite URL path
    nginx.ingress.kubernetes.io/rewrite-target: /

    # SSL redirect
    nginx.ingress.kubernetes.io/ssl-redirect: "true"

    # Timeouts
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"

    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "10"

    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 5.2 URL Rewriting

```yaml
# Route /app/(.*)  to backend /($1)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rewrite-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /app/(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: web-service
            port:
              number: 80
```

---

## Part 6: Debugging Ingress

### 6.1 Debugging Workflow

```
Ingress Not Working?
    │
    ├── kubectl get ingress (check ADDRESS)
    │       │
    │       ├── No ADDRESS → Controller not processing
    │       │                Check IngressClass
    │       │
    │       └── Has ADDRESS → Continue debugging
    │
    ├── kubectl describe ingress (check events)
    │       │
    │       └── Errors? → Fix configuration
    │
    ├── Check backend service
    │   kubectl get svc,endpoints
    │       │
    │       └── No endpoints? → Service has no pods
    │
    ├── Check Ingress controller logs
    │   kubectl logs -n ingress-nginx <controller-pod>
    │
    └── Test from inside cluster
        kubectl run test --rm -it --image=curlimages/curl -- \
          curl <service>
```

### 6.2 Common Ingress Commands

```bash
# List ingresses
k get ingress
k get ing              # Short form

# Describe ingress
k describe ingress my-ingress

# Get ingress YAML
k get ingress my-ingress -o yaml

# Check IngressClass
k get ingressclass

# Check Ingress controller pods
k get pods -n ingress-nginx

# View controller logs
k logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### 6.3 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| No ADDRESS assigned | No Ingress controller | Install ingress controller |
| ADDRESS assigned but 404 | Path doesn't match | Check path and pathType |
| 503 Service Unavailable | No endpoints | Check service selector/pods |
| SSL error | Wrong/missing TLS secret | Verify secret exists and matches host |
| Wrong IngressClass | Multiple controllers | Specify correct ingressClassName |

---

## Part 7: Default Backend

### 7.1 Configuring Default Backend

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: default-backend-ingress
spec:
  ingressClassName: nginx
  defaultBackend:                    # Catch-all
    service:
      name: default-service
      port:
        number: 80
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
              number: 80
```

Requests that don't match any rule go to the `defaultBackend`.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No IngressClass | Controller doesn't process | Add `ingressClassName` to spec |
| Wrong pathType | Routes don't match | Use `Prefix` for most cases |
| Service port mismatch | 503 errors | Match Ingress port to Service port |
| TLS secret wrong namespace | SSL errors | Secret must be in same namespace as Ingress |
| Missing Ingress controller | No ADDRESS assigned | Install controller first |

---

## Quiz

1. **What's the difference between Ingress and LoadBalancer service?**
   <details>
   <summary>Answer</summary>
   Ingress is Layer 7 (HTTP/HTTPS) routing with path/host-based rules, while LoadBalancer is Layer 4 (TCP/UDP) with no routing intelligence. Ingress can serve many services with one external IP.
   </details>

2. **An Ingress shows no ADDRESS. What's the likely cause?**
   <details>
   <summary>Answer</summary>
   No Ingress controller is installed, or the `ingressClassName` doesn't match any installed controller. Install an Ingress controller and verify the IngressClass.
   </details>

3. **What's the difference between `pathType: Prefix` and `pathType: Exact`?**
   <details>
   <summary>Answer</summary>
   `Prefix` matches any path starting with the specified prefix (`/api` matches `/api/users`). `Exact` requires an exact match (`/api` only matches `/api`, not `/api/`).
   </details>

4. **How do you configure HTTPS for an Ingress?**
   <details>
   <summary>Answer</summary>
   1. Create a TLS secret with certificate and key
   2. Add a `tls` section to the Ingress spec with the hosts and secretName
   3. The Ingress controller handles TLS termination
   </details>

5. **Requests to `/app/users` should reach the backend as `/users`. How?**
   <details>
   <summary>Answer</summary>
   Use the rewrite annotation: `nginx.ingress.kubernetes.io/rewrite-target: /$1` with path `/app/(.*)` and `pathType: ImplementationSpecific`.
   </details>

---

## Hands-On Exercise

**Task**: Create an Ingress with multiple services and TLS.

**Steps**:

1. **Create backend services**:
```bash
# API service
k create deployment api --image=nginx
k expose deployment api --port=80

# Web service
k create deployment web --image=nginx
k expose deployment web --port=80
```

2. **Create path-based Ingress**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-path-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF
```

3. **Check Ingress**:
```bash
k get ingress
k describe ingress multi-path-ingress
```

4. **Test routing** (if ingress controller is installed):
```bash
# Get ingress address
INGRESS_IP=$(k get ingress multi-path-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test paths (from inside cluster if needed)
k run test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -H "Host: example.com" http://$INGRESS_IP/api
```

5. **Create host-based Ingress**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF
```

6. **Create TLS secret** (self-signed for testing):
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=example.com"

k create secret tls example-tls --cert=tls.crt --key=tls.key
```

7. **Create TLS Ingress**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - secure.example.com
    secretName: example-tls
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF
```

8. **Cleanup**:
```bash
k delete ingress multi-path-ingress host-ingress tls-ingress
k delete deployment api web
k delete svc api web
k delete secret example-tls
rm tls.key tls.crt
```

**Success Criteria**:
- [ ] Can create path-based routing Ingress
- [ ] Can create host-based routing Ingress
- [ ] Can configure TLS on Ingress
- [ ] Understand IngressClass
- [ ] Can debug Ingress issues

---

## Practice Drills

### Drill 1: Basic Ingress (Target: 3 minutes)

```bash
# Create service
k create deployment drill-app --image=nginx
k expose deployment drill-app --port=80

# Create Ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: drill-app
            port:
              number: 80
EOF

# Check
k get ingress drill-ingress
k describe ingress drill-ingress

# Cleanup
k delete ingress drill-ingress
k delete deployment drill-app
k delete svc drill-app
```

### Drill 2: Multi-Path Ingress (Target: 4 minutes)

```bash
# Create services
k create deployment api --image=nginx
k create deployment web --image=nginx
k expose deployment api --port=80
k expose deployment web --port=80

# Create Ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-path
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF

# Verify
k describe ingress multi-path

# Cleanup
k delete ingress multi-path
k delete deployment api web
k delete svc api web
```

### Drill 3: Host-Based Ingress (Target: 4 minutes)

```bash
# Create services
k create deployment app1 --image=nginx
k create deployment app2 --image=nginx
k expose deployment app1 --port=80
k expose deployment app2 --port=80

# Create Ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-based
spec:
  ingressClassName: nginx
  rules:
  - host: app1.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1
            port:
              number: 80
  - host: app2.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2
            port:
              number: 80
EOF

# Verify
k get ingress host-based
k describe ingress host-based

# Cleanup
k delete ingress host-based
k delete deployment app1 app2
k delete svc app1 app2
```

### Drill 4: TLS Ingress (Target: 5 minutes)

```bash
# Create service
k create deployment secure-app --image=nginx
k expose deployment secure-app --port=80

# Generate certificate
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -subj "/CN=secure.local"

# Create secret
k create secret tls tls-secret --cert=tls.crt --key=tls.key

# Create Ingress with TLS
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - secure.local
    secretName: tls-secret
  rules:
  - host: secure.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-app
            port:
              number: 80
EOF

# Verify
k describe ingress tls-ingress

# Cleanup
k delete ingress tls-ingress
k delete deployment secure-app
k delete svc secure-app
k delete secret tls-secret
rm tls.key tls.crt
```

### Drill 5: Check IngressClass (Target: 2 minutes)

```bash
# List IngressClasses
k get ingressclass

# Describe
k describe ingressclass nginx

# Check which is default
k get ingressclass -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.ingressclass\.kubernetes\.io/is-default-class}{"\n"}{end}'
```

### Drill 6: Ingress with Annotations (Target: 4 minutes)

```bash
# Create service
k create deployment annotated-app --image=nginx
k expose deployment annotated-app --port=80

# Create Ingress with annotations
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: annotated-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: annotated-app
            port:
              number: 80
EOF

# Check annotations
k get ingress annotated-ingress -o yaml | grep -A5 annotations

# Cleanup
k delete ingress annotated-ingress
k delete deployment annotated-app
k delete svc annotated-app
```

### Drill 7: Debug Ingress (Target: 4 minutes)

```bash
# Create Ingress with wrong service name (intentionally broken)
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: broken-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nonexistent-service
            port:
              number: 80
EOF

# Debug
k describe ingress broken-ingress
# Look for warnings about backend

# Check ingress controller logs (if installed)
k logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=10

# Fix: create the missing service
k create deployment fix-app --image=nginx
k expose deployment fix-app --port=80 --name=nonexistent-service

# Verify
k describe ingress broken-ingress

# Cleanup
k delete ingress broken-ingress
k delete deployment fix-app
k delete svc nonexistent-service
```

### Drill 8: Challenge - Complete Ingress Setup

Without looking at solutions:

1. Create deployments: `api` and `frontend` (nginx)
2. Expose both as ClusterIP services on port 80
3. Create Ingress with:
   - Path `/api` routes to api service
   - Path `/` routes to frontend service
   - Host: `myapp.local`
4. Create TLS secret and add HTTPS
5. Verify with describe
6. Cleanup everything

```bash
# YOUR TASK: Complete in under 7 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. Create deployments
k create deployment api --image=nginx
k create deployment frontend --image=nginx

# 2. Expose as ClusterIP
k expose deployment api --port=80
k expose deployment frontend --port=80

# 3. Create Ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: challenge-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
EOF

# 4. Add TLS
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -subj "/CN=myapp.local"
k create secret tls myapp-tls --cert=tls.crt --key=tls.key

# Update Ingress with TLS
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: challenge-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.local
    secretName: myapp-tls
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
EOF

# 5. Verify
k describe ingress challenge-ingress

# 6. Cleanup
k delete ingress challenge-ingress
k delete deployment api frontend
k delete svc api frontend
k delete secret myapp-tls
rm tls.key tls.crt
```

</details>

---

## Next Module

[Module 3.5: Gateway API](module-3.5-gateway-api.md) - The next generation of Kubernetes ingress.
