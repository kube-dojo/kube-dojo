---
title: "Module 1.3: Ingress Security"
slug: k8s/cks/part1-cluster-setup/module-1.3-ingress-security
sidebar:
  order: 3
lab:
  id: cks-1.3-ingress-security
  url: https://killercoda.com/kubedojo/scenario/cks-1.3-ingress-security
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical for external access security
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 1.1 (Network Policies), CKA Ingress knowledge

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** TLS termination on Ingress resources with valid certificates
2. **Implement** security headers and rate limiting via Ingress annotations
3. **Audit** Ingress configurations for exposed admin panels and missing TLS enforcement
4. **Harden** Ingress controllers to prevent information leakage and unauthorized access

---

## Why This Module Matters

Ingress is where your cluster meets the internet. It's the front door—and attackers target front doors. Misconfigured TLS, exposed admin panels, and missing security headers are common vulnerabilities.

CKS tests your ability to harden ingress configurations beyond basic functionality.

> **Security Note**: The ingress-nginx controller was retired on March 31, 2026 and no longer receives security patches. If your clusters still use ingress-nginx, this is a **critical security risk**. Migrate to a maintained controller (Envoy Gateway, Traefik, Cilium, NGINX Gateway Fabric) and consider adopting Gateway API for new deployments. The security principles in this module apply equally to Ingress and Gateway API configurations.

---

## Ingress Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│              INGRESS SECURITY ATTACK SURFACE                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet                                                   │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              INGRESS CONTROLLER                      │   │
│  │                                                      │   │
│  │  Attack vectors:                                    │   │
│  │  ⚠️  No TLS = data exposed in transit              │   │
│  │  ⚠️  Weak TLS versions (TLS 1.0/1.1)               │   │
│  │  ⚠️  Missing security headers                       │   │
│  │  ⚠️  Path traversal vulnerabilities                │   │
│  │  ⚠️  Exposed status/metrics endpoints              │   │
│  │  ⚠️  No rate limiting                               │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   App Service   │  │   API Service   │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## TLS Configuration

### Creating TLS Secrets

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=myapp.example.com"

# Create Kubernetes secret
kubectl create secret tls myapp-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n production

# Verify secret
kubectl get secret myapp-tls -n production -o yaml
```

### Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-ingress
  namespace: production
  annotations:
    # Force HTTPS redirect
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # Enable HSTS
    nginx.ingress.kubernetes.io/hsts: "true"
    nginx.ingress.kubernetes.io/hsts-max-age: "31536000"
    nginx.ingress.kubernetes.io/hsts-include-subdomains: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

---

## Security Headers

### Essential Headers

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hardened-ingress
  annotations:
    # Content Security Policy
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Referrer-Policy "strict-origin-when-cross-origin" always;
      add_header Content-Security-Policy "default-src 'self'" always;
spec:
  # ... rest of spec
```

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY HEADERS EXPLAINED                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  X-Frame-Options: SAMEORIGIN                               │
│  └── Prevents clickjacking attacks                         │
│                                                             │
│  X-Content-Type-Options: nosniff                           │
│  └── Prevents MIME type sniffing                           │
│                                                             │
│  X-XSS-Protection: 1; mode=block                           │
│  └── Enables browser XSS filtering                         │
│                                                             │
│  Referrer-Policy: strict-origin-when-cross-origin          │
│  └── Controls referrer information leakage                 │
│                                                             │
│  Content-Security-Policy: default-src 'self'               │
│  └── Restricts resource loading sources                    │
│                                                             │
│  Strict-Transport-Security (HSTS)                          │
│  └── Forces HTTPS for specified duration                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## TLS Version Enforcement

### Disable Weak TLS Versions

```yaml
# ConfigMap for nginx-ingress-controller
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
data:
  # Minimum TLS version
  ssl-protocols: "TLSv1.2 TLSv1.3"

  # Strong cipher suites only
  ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"

  # Enable HSTS globally
  hsts: "true"
  hsts-max-age: "31536000"
  hsts-include-subdomains: "true"
  hsts-preload: "true"
```

### Per-Ingress TLS Settings

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: strict-tls-ingress
  annotations:
    # Require client certificate (mTLS)
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-secret: "production/ca-secret"

    # Specific TLS version for this ingress
    nginx.ingress.kubernetes.io/ssl-prefer-server-ciphers: "true"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
```

---

## Mutual TLS (mTLS)

```
┌─────────────────────────────────────────────────────────────┐
│              MUTUAL TLS AUTHENTICATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Standard TLS:                                             │
│  Client ──────► Server presents certificate                │
│         ◄────── Client verifies server                     │
│  (One-way verification)                                    │
│                                                             │
│  Mutual TLS:                                               │
│  Client ──────► Server presents certificate                │
│         ◄────── Client verifies server                     │
│  Client ──────► Client presents certificate                │
│         ◄────── Server verifies client                     │
│  (Two-way verification)                                    │
│                                                             │
│  Use cases:                                                │
│  • Service-to-service authentication                       │
│  • API clients with certificates                           │
│  • Zero-trust architectures                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Configure mTLS

```bash
# Create CA secret for client verification
kubectl create secret generic ca-secret \
  --from-file=ca.crt=ca.crt \
  -n production
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mtls-ingress
  namespace: production
  annotations:
    # Enable client certificate verification
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    # CA to verify client certs
    nginx.ingress.kubernetes.io/auth-tls-secret: "production/ca-secret"
    # Depth of verification
    nginx.ingress.kubernetes.io/auth-tls-verify-depth: "1"
    # Pass client cert to backend
    nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
spec:
  tls:
  - hosts:
    - secure-api.example.com
    secretName: api-tls
  rules:
  - host: secure-api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-api
            port:
              number: 443
```

---

## Rate Limiting

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rate-limited-ingress
  annotations:
    # Limit requests per second
    nginx.ingress.kubernetes.io/limit-rps: "10"

    # Limit connections
    nginx.ingress.kubernetes.io/limit-connections: "5"

    # Burst allowance
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "5"

    # Custom error when rate limited
    nginx.ingress.kubernetes.io/server-snippet: |
      limit_req_status 429;
spec:
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
```

---

## Protecting Sensitive Paths

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: protected-paths
  annotations:
    # Block access to sensitive paths
    nginx.ingress.kubernetes.io/server-snippet: |
      location ~ ^/(admin|metrics|health|debug) {
        deny all;
        return 403;
      }

    # Or require authentication
    nginx.ingress.kubernetes.io/auth-url: "https://auth.example.com/verify"
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app
            port:
              number: 80
```

### Using NetworkPolicies with Ingress

```yaml
# Allow only ingress controller to reach backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-ingress-only
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
      podSelector:
        matchLabels:
          app.kubernetes.io/name: ingress-nginx
    ports:
    - port: 80
```

---

## Ingress Controller Hardening

### Secure Ingress Controller Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  template:
    spec:
      containers:
      - name: controller
        image: registry.k8s.io/ingress-nginx/controller:v1.9.0
        securityContext:
          # Don't run as root
          runAsNonRoot: true
          runAsUser: 101
          # Read-only filesystem
          readOnlyRootFilesystem: true
          # No privilege escalation
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
        # Resource limits
        resources:
          limits:
            cpu: "1"
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 256Mi
```

---

## Real Exam Scenarios

### Scenario 1: Enable TLS on Ingress

```bash
# Create TLS certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tls.key -out /tmp/tls.crt \
  -subj "/CN=webapp.example.com"

# Create secret
kubectl create secret tls webapp-tls \
  --cert=/tmp/tls.crt \
  --key=/tmp/tls.key \
  -n production

# Update existing ingress to use TLS
kubectl patch ingress webapp -n production --type=json -p='[
  {"op": "add", "path": "/spec/tls", "value": [
    {"hosts": ["webapp.example.com"], "secretName": "webapp-tls"}
  ]}
]'
```

### Scenario 2: Force HTTPS Redirect

```bash
# Add SSL redirect annotation
kubectl annotate ingress webapp -n production \
  nginx.ingress.kubernetes.io/ssl-redirect="true"
```

### Scenario 3: Add Security Headers

```bash
kubectl annotate ingress webapp -n production \
  nginx.ingress.kubernetes.io/configuration-snippet='
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
  '
```

---

## Did You Know?

- **HSTS preloading** adds your domain to browsers' built-in HTTPS-only list. Once you're on it, browsers will never make HTTP requests to your domain.

- **TLS 1.0 and 1.1 are deprecated.** PCI-DSS compliance requires TLS 1.2 minimum since 2018.

- **nginx-ingress vs ingress-nginx**: There are TWO ingress controllers often confused. `ingress-nginx` (kubernetes/ingress-nginx) is the official one; `nginx-ingress` is from NGINX Inc.

- **Let's Encrypt with cert-manager** can automate TLS certificate issuance. Many production clusters use this instead of manual certificate management.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No TLS on ingress | Data exposed in transit | Always configure TLS |
| Using self-signed certs in prod | Browser warnings, no trust | Use proper CA (Let's Encrypt) |
| Missing HSTS header | Downgrade attacks possible | Enable HSTS with long max-age |
| Exposing /metrics endpoint | Information leakage | Block or authenticate |
| No rate limiting | DoS vulnerability | Configure rate limits |

---

## Quiz

1. **What annotation forces HTTP to HTTPS redirect in nginx-ingress?**
   <details>
   <summary>Answer</summary>
   `nginx.ingress.kubernetes.io/ssl-redirect: "true"` - This redirects all HTTP requests to HTTPS.
   </details>

2. **What is the minimum recommended TLS version for production?**
   <details>
   <summary>Answer</summary>
   TLS 1.2. TLS 1.0 and 1.1 are deprecated and have known vulnerabilities. TLS 1.3 is preferred but 1.2 is the minimum for compliance.
   </details>

3. **What header prevents clickjacking attacks?**
   <details>
   <summary>Answer</summary>
   `X-Frame-Options: DENY` or `X-Frame-Options: SAMEORIGIN` - These prevent the page from being embedded in iframes on other sites.
   </details>

4. **How do you create a TLS secret in Kubernetes?**
   <details>
   <summary>Answer</summary>
   `kubectl create secret tls <name> --cert=<cert-file> --key=<key-file>` - The secret type is `kubernetes.io/tls` and contains `tls.crt` and `tls.key` keys.
   </details>

---

## Hands-On Exercise

**Task**: Secure an ingress with TLS and security headers.

```bash
# Setup
kubectl create namespace secure-app
kubectl run webapp --image=nginx -n secure-app
kubectl expose pod webapp --port=80 -n secure-app

# Step 1: Create TLS certificate and secret
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=webapp.local"

kubectl create secret tls webapp-tls \
  --cert=tls.crt --key=tls.key \
  -n secure-app

# Step 2: Create secure ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webapp
  namespace: secure-app
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "DENY" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - webapp.local
    secretName: webapp-tls
  rules:
  - host: webapp.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: webapp
            port:
              number: 80
EOF

# Step 3: Verify configuration
kubectl describe ingress webapp -n secure-app

# Step 4: Test (add to /etc/hosts: 127.0.0.1 webapp.local)
# curl -k https://webapp.local -I | grep -E "X-Frame|X-Content|X-XSS"

# Cleanup
kubectl delete namespace secure-app
```

**Success criteria**: Ingress uses TLS and returns security headers.

---

## Summary

**TLS Requirements**:
- Always use TLS for external traffic
- Minimum TLS 1.2, prefer TLS 1.3
- Store certificates in Kubernetes secrets

**Security Headers**:
- X-Frame-Options: Prevent clickjacking
- X-Content-Type-Options: Prevent MIME sniffing
- HSTS: Force HTTPS

**Rate Limiting**:
- Protect against DoS attacks
- Configure per-ingress limits

**Best Practices**:
- Force HTTPS redirect
- Use NetworkPolicies with ingress
- Protect sensitive paths
- Harden ingress controller pod

---

## Next Module

[Module 1.4: Node Metadata Protection](../module-1.4-node-metadata/) - Protecting cloud provider metadata services.
