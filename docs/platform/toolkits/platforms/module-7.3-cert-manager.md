# Module 7.3: cert-manager

> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

TLS certificates expire. When they do, your site goes down and users see scary warnings. cert-manager automates certificate lifecycle management in Kubernetes—requesting certificates from Let's Encrypt or your internal CA, renewing them before expiry, and injecting them into Ingresses and applications.

**What You'll Learn**:
- cert-manager architecture and issuers
- Automatic Let's Encrypt certificates
- Internal PKI with self-signed and CA issuers
- Certificate lifecycle management

**Prerequisites**:
- Kubernetes Ingress basics
- TLS/SSL fundamentals
- DNS concepts

---

## Why This Module Matters

A single expired certificate can cause a production outage. Manual certificate management doesn't scale—especially with microservices where you might have hundreds of internal certificates. cert-manager makes "set and forget" TLS possible, automatically renewing certificates 30 days before expiry.

> 💡 **Did You Know?** cert-manager was created by Jetstack and is now a CNCF graduated project. It manages millions of certificates across thousands of clusters worldwide. Before cert-manager, teams would set calendar reminders for certificate renewals. Now, certificates renew automatically—and you can sleep through the night.

---

## The Certificate Problem

```
MANUAL CERTIFICATE MANAGEMENT
════════════════════════════════════════════════════════════════════

1. Generate CSR
2. Submit to CA (Let's Encrypt, internal)
3. Complete challenge (DNS or HTTP)
4. Receive certificate
5. Create Kubernetes Secret
6. Configure Ingress to use Secret
7. Set reminder for 90 days (Let's Encrypt validity)
8. Repeat steps 1-6 before expiry
9. Hope you don't forget

Problems:
• Manual, error-prone
• Outages when certificates expire
• Doesn't scale with many services

═══════════════════════════════════════════════════════════════════

WITH CERT-MANAGER
════════════════════════════════════════════════════════════════════

1. Create Certificate resource
2. cert-manager does everything else:
   • Generates key pair
   • Creates CSR
   • Completes ACME challenge
   • Stores certificate in Secret
   • Renews automatically (30 days before expiry)

You: Deploy once, forget about certificates
```

---

## Architecture

```
CERT-MANAGER ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   CERT-MANAGER                              │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │ Controller  │  │  CA Injector │  │   Webhook   │        │ │
│  │  │ Manager     │  │  (optional)  │  │ (validation)│        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              │ Watches                           │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      RESOURCES                              │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │   Issuer/    │  │ Certificate  │  │  Secret      │     │ │
│  │  │ ClusterIssuer│  │              │  │ (tls.crt,key)│     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               │ ACME protocol
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CERTIFICATE AUTHORITY                          │
│                                                                  │
│  Let's Encrypt  │  Vault  │  Venafi  │  Internal CA            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Resources

| Resource | Scope | Description |
|----------|-------|-------------|
| **Issuer** | Namespace | CA configuration (how to get certs) |
| **ClusterIssuer** | Cluster-wide | Shared CA configuration |
| **Certificate** | Namespace | Request for a certificate |
| **CertificateRequest** | Internal | Created by cert-manager |
| **Order** | Internal | ACME order tracking |
| **Challenge** | Internal | ACME challenge tracking |

---

## Installation

```bash
# Install cert-manager via Helm
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Verify installation
kubectl get pods -n cert-manager
kubectl get crd | grep cert-manager
```

---

## Issuers

### Let's Encrypt (Production)

```yaml
# ClusterIssuer for Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    # Production server
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    # HTTP-01 challenge via ingress
    - http01:
        ingress:
          class: nginx
---
# Staging for testing (less rate limiting)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-staging-account-key
    solvers:
    - http01:
        ingress:
          class: nginx
```

### DNS-01 Challenge (Wildcard Support)

```yaml
# For wildcard certificates, use DNS-01
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-dns
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-dns-account-key
    solvers:
    - dns01:
        route53:
          region: us-west-2
          hostedZoneID: Z1234567890
          # Use IRSA or explicit credentials
```

### Self-Signed (Development)

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned
spec:
  selfSigned: {}
```

### Internal CA

```yaml
# First, create a CA certificate
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: internal-ca
  namespace: cert-manager
spec:
  isCA: true
  commonName: Internal CA
  secretName: internal-ca-secret
  privateKey:
    algorithm: ECDSA
    size: 256
  issuerRef:
    name: selfsigned
    kind: ClusterIssuer
---
# Then create issuer using that CA
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: internal-ca-issuer
spec:
  ca:
    secretName: internal-ca-secret
```

> 💡 **Did You Know?** Let's Encrypt has issued over 3 billion certificates since 2015. They pioneered the ACME protocol (Automatic Certificate Management Environment) which is now an IETF standard. cert-manager implements ACME, making free, automated TLS available to everyone.

---

## Creating Certificates

### Manual Certificate Resource

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-example-com
  namespace: production
spec:
  secretName: api-example-com-tls
  duration: 2160h    # 90 days
  renewBefore: 360h  # 15 days before expiry
  subject:
    organizations:
      - Example Corp
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  usages:
    - server auth
  dnsNames:
    - api.example.com
    - api-internal.example.com
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
```

### Automatic via Ingress Annotation

```yaml
# Just add annotation - cert-manager handles the rest
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: api-example-com-tls  # cert-manager creates this
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

### Wildcard Certificates

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-example-com
spec:
  secretName: wildcard-example-com-tls
  dnsNames:
    - "*.example.com"
    - example.com
  issuerRef:
    name: letsencrypt-dns  # Must use DNS-01 for wildcards
    kind: ClusterIssuer
```

---

## Certificate Lifecycle

```
CERTIFICATE LIFECYCLE
════════════════════════════════════════════════════════════════════

Day 0: Certificate Requested
─────────────────────────────────────────────────────────────────
1. User creates Certificate resource
2. cert-manager creates CertificateRequest
3. cert-manager creates Order (ACME)
4. cert-manager creates Challenge
5. Challenge solved (HTTP-01 or DNS-01)
6. CA issues certificate
7. Certificate stored in Secret

Day 1-60: Certificate Valid
─────────────────────────────────────────────────────────────────
• cert-manager monitors expiry
• Secret contains valid certificate
• Applications use certificate

Day 60: Renewal Begins (renewBefore: 30 days)
─────────────────────────────────────────────────────────────────
• cert-manager starts renewal process
• New certificate requested
• Old certificate still valid

Day 61-90: Certificate Renewed
─────────────────────────────────────────────────────────────────
• New certificate issued
• Secret updated atomically
• Ingress controller reloads
• Zero downtime

Day 90: Original Would Expire
─────────────────────────────────────────────────────────────────
• Already renewed - no impact
```

---

## Monitoring and Troubleshooting

### Check Certificate Status

```bash
# List certificates
kubectl get certificates -A

# Describe specific certificate
kubectl describe certificate api-example-com -n production

# Check certificate ready status
kubectl get certificate -o wide

# View certificate details from Secret
kubectl get secret api-example-com-tls -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout

# Check expiry
kubectl get secret api-example-com-tls -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -enddate -noout
```

### Debug ACME Challenges

```bash
# Check orders
kubectl get orders -A

# Check challenges
kubectl get challenges -A

# Describe failing challenge
kubectl describe challenge <challenge-name>

# Common issues:
# - DNS not propagated
# - HTTP challenge path blocked
# - Rate limiting
```

### Metrics and Alerting

```yaml
# Prometheus rule for expiring certificates
groups:
- name: cert-manager
  rules:
  - alert: CertificateExpiringSoon
    expr: certmanager_certificate_expiration_timestamp_seconds - time() < 7 * 24 * 3600
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Certificate {{ $labels.name }} expires in less than 7 days"

  - alert: CertificateNotReady
    expr: certmanager_certificate_ready_status{condition="False"} == 1
    for: 15m
    labels:
      severity: critical
    annotations:
      summary: "Certificate {{ $labels.name }} is not ready"
```

> 💡 **Did You Know?** cert-manager exposes Prometheus metrics out of the box. The most important one is `certmanager_certificate_expiration_timestamp_seconds`, which lets you alert on certificates expiring soon. Combined with `certmanager_certificate_ready_status`, you can catch issues before they cause outages.

> 💡 **Did You Know?** cert-manager supports multiple ACME providers beyond Let's Encrypt, including ZeroSSL, Google Trust Services, and Buypass. If you hit Let's Encrypt rate limits (which happens at scale), you can switch issuers with a single YAML change. Some organizations run multiple issuers simultaneously—Let's Encrypt for most certificates, ZeroSSL as a backup for rate-limited domains.

---

## Advanced Patterns

### Certificate Rotation for Pods

```yaml
# Mount certificate as volume with auto-reload
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: app
        volumeMounts:
        - name: tls
          mountPath: /etc/tls
          readOnly: true
      volumes:
      - name: tls
        secret:
          secretName: myapp-tls
```

```yaml
# Use projected volumes for automatic updates
volumes:
- name: tls
  projected:
    sources:
    - secret:
        name: myapp-tls
        items:
        - key: tls.crt
          path: cert.pem
        - key: tls.key
          path: key.pem
```

### mTLS Between Services

```yaml
# Client certificate for service-to-service auth
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: service-a-client-cert
spec:
  secretName: service-a-client-tls
  duration: 24h
  renewBefore: 8h
  usages:
    - client auth
  dnsNames:
    - service-a.default.svc.cluster.local
  issuerRef:
    name: internal-ca-issuer
    kind: ClusterIssuer
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using staging issuer in prod | Browsers don't trust staging certs | Use `letsencrypt-prod` for production |
| HTTP-01 for wildcard | Wildcards require DNS-01 | Configure DNS-01 challenge solver |
| No renewBefore | Renewal too close to expiry | Set renewBefore to 15-30 days |
| Not monitoring expiry | Surprise certificate failures | Alert on `certmanager_certificate_expiration_timestamp_seconds` |
| Rate limiting | Too many requests to Let's Encrypt | Use staging for testing, be patient |
| Wrong ingress class | Challenge solver can't find ingress | Match solver's ingress class to your controller |

---

## War Story: The Friday Afternoon Expiry

*A team's wildcard certificate expired on a Friday at 5 PM. Their entire domain was down for the weekend.*

**What went wrong**:
1. Certificate was manually created before cert-manager adoption
2. cert-manager managed other certificates, but not this one
3. No monitoring on certificate expiry
4. Calendar reminder was ignored (vacation)

**The fix**:
1. Import all existing certificates into cert-manager
2. Add alerting on all certificates, not just cert-manager managed
3. Use longer renewal windows (renewBefore: 30 days)
4. Page on-call, not just email

```bash
# Check ALL secrets with TLS certificates
kubectl get secrets -A -o json | jq -r '
  .items[] |
  select(.type=="kubernetes.io/tls") |
  .metadata.namespace + "/" + .metadata.name'
```

---

## Quiz

### Question 1
What's the difference between HTTP-01 and DNS-01 challenges?

<details>
<summary>Show Answer</summary>

**HTTP-01**:
- Prove domain ownership via HTTP endpoint
- Create `/.well-known/acme-challenge/<token>` path
- Requires ingress/public HTTP access
- Cannot do wildcard certificates
- Simpler to set up

**DNS-01**:
- Prove domain ownership via DNS TXT record
- Create `_acme-challenge.<domain>` TXT record
- Works without public HTTP access
- **Required for wildcard certificates**
- Needs DNS provider API access

Use HTTP-01 for simplicity, DNS-01 for wildcards or internal services.

</details>

### Question 2
How does cert-manager ensure zero-downtime certificate renewal?

<details>
<summary>Show Answer</summary>

1. **Early renewal**: `renewBefore` starts renewal before expiry (default 30 days)
2. **Atomic update**: New certificate stored in Secret atomically
3. **Ingress reload**: Controllers watch Secrets and reload on change
4. **Old cert valid**: Old certificate still valid during renewal window

Timeline:
- Day 0: Cert issued (90-day validity)
- Day 60: Renewal starts (renewBefore: 30 days)
- Day 61: New cert issued, Secret updated
- Day 90: Original would expire, but already renewed

No manual intervention, no downtime.

</details>

### Question 3
Why use ClusterIssuer instead of Issuer?

<details>
<summary>Show Answer</summary>

**Issuer** (namespaced):
- Only usable in its namespace
- Good for team-specific CAs
- More isolation

**ClusterIssuer** (cluster-wide):
- Usable from any namespace
- Good for shared Let's Encrypt config
- Less duplication

**Best practice**:
- ClusterIssuer for Let's Encrypt (everyone uses it)
- ClusterIssuer for internal CA (shared trust)
- Issuer for team-specific/sensitive CAs

</details>

---

## Hands-On Exercise

### Objective
Set up cert-manager with a self-signed issuer and create certificates.

### Environment Setup

```bash
# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Wait for ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s
```

### Tasks

1. **Verify installation**:
   ```bash
   kubectl get pods -n cert-manager
   ```

2. **Create self-signed ClusterIssuer**:
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: selfsigned-issuer
   spec:
     selfSigned: {}
   EOF
   ```

3. **Create a Certificate**:
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: Certificate
   metadata:
     name: myapp-tls
     namespace: default
   spec:
     secretName: myapp-tls-secret
     duration: 24h
     renewBefore: 8h
     dnsNames:
       - myapp.local
       - myapp.default.svc.cluster.local
     issuerRef:
       name: selfsigned-issuer
       kind: ClusterIssuer
   EOF
   ```

4. **Check Certificate status**:
   ```bash
   kubectl get certificate myapp-tls
   kubectl describe certificate myapp-tls
   ```

5. **Verify Secret created**:
   ```bash
   kubectl get secret myapp-tls-secret
   kubectl get secret myapp-tls-secret -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout | head -20
   ```

6. **Create internal CA** (for realistic setup):
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: Certificate
   metadata:
     name: internal-ca
     namespace: cert-manager
   spec:
     isCA: true
     commonName: My Internal CA
     secretName: internal-ca-secret
     privateKey:
       algorithm: ECDSA
       size: 256
     issuerRef:
       name: selfsigned-issuer
       kind: ClusterIssuer
   ---
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: internal-ca-issuer
   spec:
     ca:
       secretName: internal-ca-secret
   EOF
   ```

### Success Criteria
- [ ] cert-manager pods running
- [ ] ClusterIssuer created and ready
- [ ] Certificate created and Ready=True
- [ ] Secret contains tls.crt and tls.key
- [ ] Certificate shows correct DNS names

### Bonus Challenge
Create an Ingress with the cert-manager annotation and verify it automatically creates a Certificate and Secret.

---

## Further Reading

- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [ACME Protocol RFC](https://tools.ietf.org/html/rfc8555)

---

## Next Module

Continue to [Developer Experience Toolkit](../developer-experience/README.md) to learn about k9s, Telepresence, and local Kubernetes development.

---

*"The best security feature is one that's automatic. cert-manager makes TLS invisible."*
