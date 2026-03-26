---
title: "Module 3.4: DNS & Certificate Infrastructure"
slug: on-premises/networking/module-3.4-dns-certs
sidebar:
  order: 5
---

> **Complexity**: `[MEDIUM]` | Time: 45 minutes
>
> **Prerequisites**: [Module 3.3: Load Balancing](module-3.3-load-balancing/), [CKA: DNS](../../k8s/cka/part3-services-networking/module-3.3-dns/)

---

## Why This Module Matters

On AWS, Route 53 provides DNS and ACM provides TLS certificates — both fully managed, both automatic. On bare metal, you need to run your own DNS infrastructure and manage your own certificate authority. If DNS is wrong, nothing works. If certificates are wrong, everything is "untrusted."

A healthcare company deploying on-premises Kubernetes discovered this the hard way. They had CoreDNS inside the cluster for service discovery but forgot about external DNS — the names that humans and external systems use to reach services. Their monitoring system could not resolve `grafana.internal.company.com` because no DNS server was authoritative for `internal.company.com`. Their Jenkins pipelines failed because the internal container registry `registry.internal.company.com` had a self-signed certificate that curl rejected. Three weeks of "why doesn't this work?" traced back to: no DNS zone for internal names, and no trusted CA for internal certificates.

---

## What You'll Learn

- Internal DNS architecture (authoritative + recursive)
- Split-horizon DNS (internal vs external resolution)
- CoreDNS as external authoritative DNS
- Certificate management with cert-manager + internal CA
- HashiCorp Vault as a private PKI
- Automated certificate rotation for K8s components

---

## Internal DNS Architecture

### The Three DNS Layers

```
┌─────────────────────────────────────────────────────────────┐
│              DNS LAYERS FOR ON-PREM K8s                     │
│                                                               │
│  Layer 1: Kubernetes Internal DNS (CoreDNS in cluster)      │
│  ├── Resolves: service.namespace.svc.cluster.local          │
│  ├── Managed by: Kubernetes automatically                   │
│  └── Scope: pods and services within the cluster            │
│                                                               │
│  Layer 2: Internal Corporate DNS                            │
│  ├── Resolves: *.internal.company.com                       │
│  ├── Managed by: you (BIND, CoreDNS, PowerDNS)            │
│  └── Scope: internal services reachable by name             │
│      (grafana.internal.company.com → MetalLB VIP)          │
│                                                               │
│  Layer 3: External/Public DNS                               │
│  ├── Resolves: *.company.com (public)                       │
│  ├── Managed by: DNS provider (Cloudflare, Route53, etc.)  │
│  └── Scope: internet-facing services                        │
│                                                               │
│  Pod DNS resolution chain:                                   │
│  Pod → CoreDNS (L1) → Corporate DNS (L2) → Public DNS (L3)│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Split-Horizon DNS

Internal and external clients resolve the same name to different IPs:

```
┌─────────────────────────────────────────────────────────────┐
│              SPLIT-HORIZON DNS                               │
│                                                               │
│  Internal query: app.company.com                            │
│  └── Resolved by internal DNS: 10.0.50.10 (MetalLB VIP)   │
│                                                               │
│  External query: app.company.com                            │
│  └── Resolved by public DNS: 203.0.113.50 (public IP)     │
│                                                               │
│  Implementation:                                             │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │ Internal DNS │        │ Public DNS   │                  │
│  │ (BIND/CoreDNS)│        │ (Cloudflare) │                  │
│  │              │        │              │                  │
│  │ app.company  │        │ app.company  │                  │
│  │ → 10.0.50.10│        │ → 203.0.113.50│                 │
│  └──────────────┘        └──────────────┘                  │
│                                                               │
│  Corporate DNS servers: 10.0.10.1, 10.0.10.2              │
│  K8s CoreDNS forwards to corporate DNS for non-cluster names│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### CoreDNS Configuration for Forwarding

```yaml
# CoreDNS ConfigMap — forward non-cluster queries to corporate DNS
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
           lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
           ttl 30
        }
        # Forward internal domains to corporate DNS
        forward internal.company.com 10.0.10.1 10.0.10.2
        # Forward everything else to corporate DNS (which forwards to public)
        forward . 10.0.10.1 10.0.10.2
        cache 30
        loop
        reload
        loadbalance
    }
```

### External Authoritative DNS with CoreDNS

Run a second CoreDNS instance (outside the cluster) as the authoritative DNS for your internal zone:

```yaml
# CoreDNS config for internal.company.com zone
.:53 {
    file /etc/coredns/db.internal.company.com internal.company.com
    forward . 8.8.8.8 1.1.1.1  # Forward public queries upstream
    cache 300
    log
}
```

```dns
; /etc/coredns/db.internal.company.com
$ORIGIN internal.company.com.
$TTL 300

@       IN  SOA   ns1.internal.company.com. admin.company.com. (
              2024010101 ; Serial
              3600       ; Refresh
              900        ; Retry
              604800     ; Expire
              300 )      ; Minimum TTL

        IN  NS    ns1.internal.company.com.
        IN  NS    ns2.internal.company.com.

ns1     IN  A     10.0.10.1
ns2     IN  A     10.0.10.2

; Kubernetes services (MetalLB VIPs)
grafana     IN  A     10.0.50.10
argocd      IN  A     10.0.50.11
registry    IN  A     10.0.50.12
vault       IN  A     10.0.50.13

; Wildcard for ingress
*.apps      IN  A     10.0.50.20

; Infrastructure
api         IN  A     10.0.20.100  ; kube-vip API server VIP
```

---

## Certificate Infrastructure

### The Problem

On bare metal, there is no AWS ACM, no GCP Certificate Manager. You need TLS certificates for:

- **Kubernetes API server** (kubelet-to-API, kubectl-to-API)
- **etcd** (peer-to-peer, client-to-server)
- **Ingress** (HTTPS for user-facing services)
- **Service mesh** (mTLS between pods)
- **Internal tools** (Grafana, ArgoCD, Vault, Harbor)

### Option 1: cert-manager with Internal CA

```yaml
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml

# Create a self-signed root CA
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}

---
# Generate a CA certificate
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: internal-ca
  namespace: cert-manager
spec:
  isCA: true
  commonName: "KubeDojo Internal CA"
  secretName: internal-ca-secret
  duration: 87600h  # 10 years
  renewBefore: 8760h  # Renew 1 year before expiry
  privateKey:
    algorithm: ECDSA
    size: 256
  issuerRef:
    name: selfsigned-issuer
    kind: ClusterIssuer

---
# Create an issuer using the CA
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: internal-ca-issuer
spec:
  ca:
    secretName: internal-ca-secret

---
# Issue a certificate for an internal service
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: grafana-tls
  namespace: monitoring
spec:
  secretName: grafana-tls-secret
  duration: 8760h  # 1 year
  renewBefore: 720h  # Renew 30 days before expiry
  dnsNames:
    - grafana.internal.company.com
    - grafana.monitoring.svc.cluster.local
  issuerRef:
    name: internal-ca-issuer
    kind: ClusterIssuer
```

### Option 2: cert-manager with Vault PKI

HashiCorp Vault provides a more robust PKI with audit logging, short-lived certificates, and HSM backing:

```bash
# Enable Vault PKI secrets engine
vault secrets enable pki

# Configure max TTL
vault secrets tune -max-lease-ttl=87600h pki

# Generate root CA
vault write -field=certificate pki/root/generate/internal \
  common_name="KubeDojo Root CA" \
  ttl=87600h > root-ca.crt

# Enable intermediate PKI
vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=43800h pki_int

# Generate intermediate CA (signed by root)
vault write -format=json pki_int/intermediate/generate/internal \
  common_name="KubeDojo Intermediate CA" | jq -r '.data.csr' > intermediate.csr

vault write -format=json pki/root/sign-intermediate \
  csr=@intermediate.csr format=pem_bundle ttl=43800h \
  | jq -r '.data.certificate' > intermediate.crt

vault write pki_int/intermediate/set-signed certificate=@intermediate.crt

# Create a role for K8s certificates
vault write pki_int/roles/kubernetes \
  allowed_domains="internal.company.com,svc.cluster.local" \
  allow_subdomains=true \
  max_ttl=720h
```

```yaml
# cert-manager Vault issuer
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: vault-issuer
spec:
  vault:
    server: https://vault.internal.company.com:8200
    path: pki_int/sign/kubernetes
    auth:
      kubernetes:
        role: cert-manager
        mountPath: /v1/auth/kubernetes
        serviceAccountRef:
          name: cert-manager
```

### Distributing the Internal CA

For internal certificates to be trusted by browsers, tools, and pods, the CA certificate must be distributed:

```bash
# Add to system trust store (Ubuntu)
cp root-ca.crt /usr/local/share/ca-certificates/kubedojo-ca.crt
update-ca-certificates

# Add to pods (Kubernetes ConfigMap)
kubectl create configmap internal-ca \
  --from-file=ca.crt=root-ca.crt \
  -n default

# Mount in pods
volumes:
  - name: ca-certs
    configMap:
      name: internal-ca
volumeMounts:
  - name: ca-certs
    mountPath: /etc/ssl/certs/kubedojo-ca.crt
    subPath: ca.crt
```

---

## Did You Know?

- **Let's Encrypt certificates work on-premises too** — if your internal services have public DNS names and are reachable from the internet for HTTP-01 validation. For truly internal services, you need your own CA.

- **Kubernetes automatically rotates kubelet certificates** when `--rotate-certificates` is enabled. But etcd certificates, API server certificates, and webhook certificates require manual rotation or cert-manager.

- **The default Kubernetes CA certificate expires after 10 years** (kubeadm default). Many organizations will hit this limit on clusters deployed in 2015-2016. When it expires, every component that trusts it breaks simultaneously.

- **ACME protocol (used by Let's Encrypt) can work with internal CAs** via step-ca, an open source ACME server. This lets you use cert-manager's ACME issuer with your own private CA, getting automatic renewal without exposing anything to the internet.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No internal DNS server | Services only reachable by IP, not name | Run CoreDNS/BIND for internal zone |
| Self-signed certs everywhere | Every tool shows "untrusted", scripts need `--insecure` | Use a proper CA chain, distribute root CA |
| Forgetting cert rotation | Certificates expire, services stop | cert-manager with auto-renewal |
| Corporate DNS not redundant | Single DNS server = SPOF | At least 2 DNS servers, different racks |
| No split-horizon | Internal services resolved to public IPs | Separate internal/external DNS views |
| CA key on a shared server | CA compromise = all certs compromised | Vault + HSM for CA key protection |
| Not trusting CA in pods | Pods can't verify internal services | Mount CA cert via ConfigMap or init container |

---

## Quiz

### Question 1
A pod needs to reach `grafana.internal.company.com`. Trace the DNS resolution path.

<details>
<summary>Answer</summary>

1. **Pod's DNS resolver** (`/etc/resolv.conf`) points to CoreDNS cluster IP (e.g., 10.96.0.10)

2. **CoreDNS (in-cluster)** receives the query. It checks:
   - Is `grafana.internal.company.com` a Kubernetes service? No (not `*.svc.cluster.local`)
   - Forward rule: `forward internal.company.com 10.0.10.1 10.0.10.2`

3. **Corporate DNS** (10.0.10.1) receives the query. It is authoritative for `internal.company.com`:
   - Looks up zone file: `grafana IN A 10.0.50.10`
   - Returns: 10.0.50.10

4. **Pod** receives the answer and connects to 10.0.50.10 (MetalLB VIP for Grafana)

Total chain: Pod → CoreDNS (cluster) → Corporate DNS → Answer

If the CoreDNS forward rule for `internal.company.com` is missing, the query falls through to the generic forwarder (`. 10.0.10.1`) and still works — but having the explicit forward is clearer and prevents leaking internal names to public DNS if the generic forwarder uses 8.8.8.8.
</details>

### Question 2
Why use Vault PKI instead of a simple self-signed CA for internal certificates?

<details>
<summary>Answer</summary>

**Self-signed CA limitations:**
- CA private key stored in a Kubernetes Secret (accessible to cluster admins)
- No audit trail of which certificates were issued
- No revocation capability (CRL/OCSP)
- Renewing the CA requires manual intervention across all trust stores
- No role-based access control for certificate issuance

**Vault PKI advantages:**
- CA private key protected by Vault (sealed, audit-logged, optionally HSM-backed)
- Full audit trail of every certificate issued
- Short-lived certificates (hours instead of years) — reduces blast radius of compromise
- Role-based access: only cert-manager can issue K8s certs, only CI/CD can issue pipeline certs
- Automatic CRL/OCSP for revocation
- Integrates with cert-manager for automated renewal

**When self-signed CA is fine**: Dev/test environments, small clusters without compliance requirements.

**When Vault is needed**: Production, regulated industries, environments where certificate issuance must be audited.
</details>

### Question 3
Your cert-manager certificate shows `Ready: False` with reason `OrderFailed`. What do you check?

<details>
<summary>Answer</summary>

Debug steps:

```bash
# Check certificate status
kubectl describe certificate grafana-tls -n monitoring

# Check the order
kubectl get orders -n monitoring
kubectl describe order <order-name> -n monitoring

# Check the challenge (if ACME issuer)
kubectl get challenges -n monitoring

# Common causes:
# 1. Issuer not ready
kubectl describe clusterissuer internal-ca-issuer
# Check: Status.Conditions[0].Type == "Ready"

# 2. Secret not found (CA issuer)
kubectl get secret internal-ca-secret -n cert-manager
# If missing: the CA certificate was not created

# 3. DNS name not allowed by issuer
# Check Vault role's allowed_domains or CA issuer constraints

# 4. Vault authentication failed
# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager
```
</details>

### Question 4
You need HTTPS for `*.apps.internal.company.com` (wildcard). How do you set this up with cert-manager?

<details>
<summary>Answer</summary>

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-apps-tls
  namespace: ingress
spec:
  secretName: wildcard-apps-tls-secret
  duration: 2160h  # 90 days
  renewBefore: 360h  # Renew 15 days before expiry
  dnsNames:
    - "*.apps.internal.company.com"
    - "apps.internal.company.com"  # Also include the bare domain
  issuerRef:
    name: internal-ca-issuer
    kind: ClusterIssuer
```

The wildcard certificate is stored as a Kubernetes Secret and can be referenced by your ingress controller:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana
  namespace: monitoring
spec:
  tls:
    - hosts:
        - grafana.apps.internal.company.com
      secretName: wildcard-apps-tls-secret
  rules:
    - host: grafana.apps.internal.company.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: grafana
                port:
                  number: 3000
```

**Important**: The wildcard cert secret must be in the same namespace as the Ingress, or use a tool like `reflector` to copy it across namespaces.
</details>

---

## Hands-On Exercise: Internal DNS and Certificates

**Task**: Set up internal DNS resolution and issue a TLS certificate in a kind cluster.

```bash
# Create cluster
kind create cluster --name dns-lab

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=120s

# Create a self-signed CA
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: lab-ca
  namespace: cert-manager
spec:
  isCA: true
  commonName: "Lab CA"
  secretName: lab-ca-secret
  duration: 87600h
  issuerRef:
    name: selfsigned
    kind: ClusterIssuer
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: lab-ca-issuer
spec:
  ca:
    secretName: lab-ca-secret
EOF

# Wait for the CA to be ready
kubectl wait --for=condition=Ready certificate/lab-ca -n cert-manager --timeout=60s

# Issue a certificate for a test service
kubectl create namespace demo
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: demo-tls
  namespace: demo
spec:
  secretName: demo-tls-secret
  dnsNames:
    - demo.apps.lab.local
  issuerRef:
    name: lab-ca-issuer
    kind: ClusterIssuer
EOF

# Verify certificate was issued
kubectl get certificate demo-tls -n demo
# NAME       READY   SECRET            AGE
# demo-tls   True    demo-tls-secret   10s

# Inspect the certificate
kubectl get secret demo-tls-secret -n demo -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -text -noout | head -20

# Cleanup
kind delete cluster --name dns-lab
```

### Success Criteria
- [ ] cert-manager installed and running
- [ ] Self-signed CA created (ClusterIssuer ready)
- [ ] TLS certificate issued for `demo.apps.lab.local`
- [ ] Certificate contains correct DNS SANs
- [ ] Certificate is signed by the Lab CA (not self-signed)

---

## Next Module

Continue to [Module 4.1: Storage Architecture Decisions](../storage/module-4.1-storage-architecture/) to learn how to design storage for on-premises Kubernetes clusters.
