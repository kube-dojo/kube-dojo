# Module 5.2: Ingress

> **Complexity**: `[MEDIUM]` - Important for external access, multiple concepts
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 5.1 (Services), understanding of HTTP and DNS

---

## Why This Module Matters

Ingress provides HTTP/HTTPS routing from outside the cluster to Services inside. Instead of exposing multiple LoadBalancer Services (expensive) or using NodePorts (ugly URLs), Ingress gives you host/path-based routing with a single entry point.

The CKAD exam tests:
- Creating Ingress resources
- Host-based and path-based routing
- TLS termination
- Understanding Ingress controllers

> **The Hotel Reception Analogy**
>
> Ingress is like a hotel reception desk. Guests (requests) arrive at one entrance (Ingress) and ask for different services: "restaurant" goes to the dining room Service, "spa" goes to the wellness Service, "room 203" goes to a specific guest Service. The receptionist (Ingress controller) routes everyone to the right place based on what they ask for.

---

## Ingress Components

### Ingress Controller

The **Ingress Controller** is a pod that watches Ingress resources and configures routing. Common controllers:

- **Envoy Gateway** (reference Gateway API implementation)
- **Traefik** (supports both Ingress and Gateway API)
- **Kong** (supports both Ingress and Gateway API)
- **Cilium** (CNI with built-in Ingress and Gateway API support)
- **NGINX Gateway Fabric** (successor to ingress-nginx)

> **Note**: The popular **ingress-nginx** controller was retired on March 31, 2026 and no longer receives updates. For new deployments, use **Gateway API** (see CKA Module 3.5) with one of the controllers above.

**Important**: Ingress resources do nothing without a controller!

```bash
# Check if you have an Ingress controller
k get pods -n ingress-nginx
# or
k get pods -A | grep -i ingress
```

### Ingress Resource

The **Ingress** is a Kubernetes resource defining routing rules:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

---

## Path Types

### Prefix (Most Common)

Matches URL path prefix:

```yaml
pathType: Prefix
path: /api
# Matches: /api, /api/, /api/users, /api/users/123
```

### Exact

Matches exact path only:

```yaml
pathType: Exact
path: /api
# Matches: /api only
# Does NOT match: /api/, /api/users
```

### ImplementationSpecific

Depends on IngressClass (controller-specific).

---

## Routing Patterns

### Host-Based Routing

Different hosts to different services:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-routing
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

### Path-Based Routing

Different paths to different services:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-routing
spec:
  rules:
  - host: example.com
    http:
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
```

### Default Backend

Catch-all for unmatched requests:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: with-default
spec:
  defaultBackend:
    service:
      name: default-service
      port:
        number: 80
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

---

## TLS/HTTPS

### Create TLS Secret

```bash
# Create TLS secret from cert and key
k create secret tls my-tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

### Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  tls:
  - hosts:
    - secure.example.com
    secretName: my-tls-secret
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-service
            port:
              number: 80
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    Ingress Flow                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet                                                   │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────┐                   │
│  │     Ingress Controller              │                   │
│  │     (nginx, traefik, etc.)          │                   │
│  │                                      │                   │
│  │  Reads Ingress rules                │                   │
│  │  Routes based on host/path          │                   │
│  └─────────────────────────────────────┘                   │
│     │                                                       │
│     │ api.example.com/users                                │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────┐                   │
│  │         Ingress Resource            │                   │
│  │                                      │                   │
│  │  rules:                             │                   │
│  │  - host: api.example.com            │                   │
│  │    paths:                           │                   │
│  │    - /users → user-svc:80           │                   │
│  │    - /orders → order-svc:80         │                   │
│  │  - host: web.example.com            │                   │
│  │    paths:                           │                   │
│  │    - / → frontend-svc:80            │                   │
│  └─────────────────────────────────────┘                   │
│     │                                                       │
│     ▼                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ user-svc │  │order-svc │  │frontend  │                 │
│  │   :80    │  │   :80    │  │svc :80   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## IngressClass

Specifies which controller handles the Ingress:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: nginx    # Which controller
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

```bash
# List available IngressClasses
k get ingressclass
```

---

## Annotations

Controller-specific behavior via annotations:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: annotated-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

Common NGINX annotations:
- `nginx.ingress.kubernetes.io/rewrite-target`: URL rewriting
- `nginx.ingress.kubernetes.io/ssl-redirect`: Force HTTPS
- `nginx.ingress.kubernetes.io/proxy-body-size`: Max request body

---

## Quick Reference

```bash
# Create Ingress imperatively (limited)
k create ingress my-ingress \
  --rule="host.example.com/path=service:port"

# View Ingress
k get ingress
k describe ingress NAME

# Get Ingress address
k get ingress NAME -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Check IngressClass
k get ingressclass

# View controller logs
k logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

---

## Did You Know?

- **Ingress is just a configuration, not a service.** The actual routing is done by the Ingress controller pods.

- **Multiple Ingress resources can exist for the same host.** Controllers typically merge them.

- **The `kubernetes.io/ingress.class` annotation is deprecated.** Use `spec.ingressClassName` instead (Kubernetes 1.18+).

- **Ingress can't route non-HTTP traffic.** For TCP/UDP, use LoadBalancer Services or the newer Gateway API.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No Ingress controller installed | Ingress does nothing | Install nginx-ingress or similar |
| Wrong pathType | Routes don't match | Use `Prefix` for most cases |
| Service name/port mismatch | 503 errors | Verify service exists and port matches |
| Missing host in rules | Matches all hosts | Add explicit host or use carefully |
| TLS secret in wrong namespace | TLS fails | Secret must be in same namespace as Ingress |

---

## Quiz

1. **What's the difference between an Ingress resource and an Ingress controller?**
   <details>
   <summary>Answer</summary>
   An Ingress resource is a Kubernetes object defining routing rules. An Ingress controller is a running pod that reads Ingress resources and configures actual routing (like NGINX configuration).
   </details>

2. **How do you route traffic to different services based on URL path?**
   <details>
   <summary>Answer</summary>
   Use multiple paths in the Ingress rules:
   ```yaml
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
   ```
   </details>

3. **What's required for HTTPS termination in Ingress?**
   <details>
   <summary>Answer</summary>
   A TLS Secret containing the certificate and key, referenced in the Ingress spec:
   ```yaml
   spec:
     tls:
     - hosts:
       - example.com
       secretName: tls-secret
   ```
   </details>

4. **What happens if no Ingress controller is installed?**
   <details>
   <summary>Answer</summary>
   Ingress resources are created but have no effect. No routing happens because there's nothing watching and implementing the rules.
   </details>

---

## Hands-On Exercise

**Task**: Create Ingress with path-based routing.

**Setup:**
```bash
# Create two deployments
k create deployment web --image=nginx
k create deployment api --image=nginx

# Create services
k expose deployment web --port=80
k expose deployment api --port=80

# Wait for pods
k wait --for=condition=Ready pod -l app=web --timeout=60s
k wait --for=condition=Ready pod -l app=api --timeout=60s
```

**Part 1: Simple Ingress**
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-ingress
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF

k get ingress simple-ingress
k describe ingress simple-ingress
```

**Part 2: Path-Based Routing**
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-ingress
spec:
  rules:
  - http:
      paths:
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
EOF

k describe ingress path-ingress
```

**Part 3: Host-Based Routing**
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-ingress
spec:
  rules:
  - host: web.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
  - host: api.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
EOF

k describe ingress host-ingress
```

**Cleanup:**
```bash
k delete ingress simple-ingress path-ingress host-ingress
k delete deployment web api
k delete svc web api
```

---

## Practice Drills

### Drill 1: Simple Ingress (Target: 2 minutes)

```bash
k create deployment drill1 --image=nginx
k expose deployment drill1 --port=80

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill1
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: drill1
            port:
              number: 80
EOF

k get ingress drill1
k delete ingress drill1 deploy drill1 svc drill1
```

### Drill 2: Host-Based Routing (Target: 3 minutes)

```bash
k create deployment app1 --image=nginx
k create deployment app2 --image=nginx
k expose deployment app1 --port=80
k expose deployment app2 --port=80

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill2
spec:
  rules:
  - host: app1.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1
            port:
              number: 80
  - host: app2.local
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

k describe ingress drill2
k delete ingress drill2 deploy app1 app2 svc app1 app2
```

### Drill 3: Path-Based Routing (Target: 3 minutes)

```bash
k create deployment frontend --image=nginx
k create deployment backend --image=nginx
k expose deployment frontend --port=80
k expose deployment backend --port=80

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill3
spec:
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /frontend
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
      - path: /backend
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 80
EOF

k get ingress drill3
k delete ingress drill3 deploy frontend backend svc frontend backend
```

### Drill 4: Ingress with Default Backend (Target: 3 minutes)

```bash
k create deployment default-app --image=nginx
k create deployment api-app --image=nginx
k expose deployment default-app --port=80
k expose deployment api-app --port=80

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill4
spec:
  defaultBackend:
    service:
      name: default-app
      port:
        number: 80
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-app
            port:
              number: 80
EOF

k describe ingress drill4
k delete ingress drill4 deploy default-app api-app svc default-app api-app
```

### Drill 5: Create Ingress Imperatively (Target: 2 minutes)

```bash
k create deployment drill5 --image=nginx
k expose deployment drill5 --port=80

# Create ingress imperatively
k create ingress drill5 --rule="drill5.local/=drill5:80"

k get ingress drill5
k describe ingress drill5

k delete ingress drill5 deploy drill5 svc drill5
```

### Drill 6: Ingress with TLS (Target: 4 minutes)

```bash
# Create self-signed cert (for demo)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tls.key -out /tmp/tls.crt \
  -subj "/CN=secure.local" 2>/dev/null

# Create TLS secret
k create secret tls drill6-tls --cert=/tmp/tls.crt --key=/tmp/tls.key

k create deployment drill6 --image=nginx
k expose deployment drill6 --port=80

cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill6
spec:
  tls:
  - hosts:
    - secure.local
    secretName: drill6-tls
  rules:
  - host: secure.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: drill6
            port:
              number: 80
EOF

k describe ingress drill6

k delete ingress drill6 secret drill6-tls deploy drill6 svc drill6
rm /tmp/tls.key /tmp/tls.crt
```

---

## Next Module

[Module 5.3: NetworkPolicies](module-5.3-networkpolicies.md) - Control pod-to-pod communication.
