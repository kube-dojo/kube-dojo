---
revision_pending: false
title: "Module 7.3: cert-manager"
slug: platform/toolkits/infrastructure-networking/platforms/module-7.3-cert-manager
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes
>
> **Prerequisites**: Kubernetes Ingress basics, TLS/SSL fundamentals, DNS concepts

## What You'll Learn

After completing this module, you will be able to:

- **Deploy cert-manager and configure ACME issuers for automated Let's Encrypt certificate management**
- **Implement certificate lifecycle automation with renewal, revocation, and secret rotation**
- **Configure cert-manager with DNS-01 and HTTP-01 challenge solvers across multiple ingress controllers**

## Why This Module Matters

TLS certificates are the invisible scaffolding that keeps the modern web trustworthy, but they are also a relentless operational trap. Every certificate has a built-in expiration date — typically 90 days for Let's Encrypt certificates, one year for many commercial CAs — and when that date arrives without a replacement, your services stop working. Browsers show certificate warnings that frighten users away. APIs reject connections with TLS handshake failures that cascade through distributed systems in ways that are difficult to diagnose quickly. This is not a hypothetical edge case: certificate expiry is one of the most common causes of production outages across the industry, and it is entirely preventable.

The fundamental challenge is that certificate management does not scale when humans are in the loop. A single domain with a single certificate is easy enough to handle with a calendar reminder and a script, but a production Kubernetes cluster hosts dozens of services, each with its own TLS certificate, plus internal service-to-service certificates for mTLS, plus wildcard certificates for subdomain patterns, plus separate certificates for staging and development environments. The combinatorics overwhelm any manual process: tracking expiry dates across namespaces, rotating secrets before they expire, ensuring Ingress resources pick up the new certificate, and verifying that every downstream consumer reloads successfully is a full-time operational burden that no team can sustain indefinitely. Automation is not a luxury here — it is the only architecture that works at scale, and cert-manager is the Kubernetes-native implementation of that architecture.

cert-manager implements a closed-loop certificate lifecycle directly inside the cluster. You describe the certificates you want — the domain names, the issuer, the rotation window — and cert-manager handles everything else: key generation, CSR submission, ACME challenge completion, secret storage, and renewal before expiry. When the system works correctly, certificates become boring infrastructure, like CPU cycles or disk space: you configure them once and stop thinking about them. But achieving that level of reliability requires understanding the durable concepts underneath — the PKI primitives, the ACME protocol, the issuer taxonomy, and the renewal mechanics — and that is what this module teaches. You will leave knowing not just which YAML fields to fill in, but why the automation architecture works, what tradeoffs you are making, and how to debug it when something goes wrong.

> **The Certificate Lifecycle Analogy**
>
> Think of a certificate like a passport. A passport proves your identity to border authorities, has a clear expiration date, and must be renewed before it lapses if you want to keep traveling. You do not renew a passport the day it expires — you start the renewal process weeks or months in advance so the new document arrives while the old one is still valid. Certificate automation applies exactly the same logic: start renewal well before expiry, issue the replacement while the current certificate is still trusted, and swap them atomically so no connection is ever rejected. cert-manager is the government agency that handles all of this for you — you fill out one form (the Certificate resource) and it manages the entire renewal pipeline from that point forward.

---

## Part 1: The Durable Spine — Automated X.509 Certificate Lifecycle

Before we dive into cert-manager's specific resources and configuration, we need to understand the underlying problem and the durable concepts that any certificate automation tool must address. These concepts — PKI primitives, the ACME protocol, challenge mechanisms, and renewal mechanics — outlive any specific tool or version. cert-manager is one implementation of these ideas; the ideas themselves are what you take to every platform you build.

### The Certificate Expiry Problem

An X.509 certificate is a signed digital document that binds a public key to an identity — typically a domain name — for a limited time. The expiration is not a design flaw; it is a security feature. If a private key is compromised, the damage is bounded by the certificate's remaining validity period. Shorter-lived certificates reduce the window of exposure, which is why Let's Encrypt standardized on 90-day validity and why the industry is moving toward even shorter lifetimes. But short lifetimes amplify the operational burden: a certificate that expires every 90 days must be renewed at least four times per year, and if you have a hundred certificates, that means a renewal event somewhere in your infrastructure roughly every day.

Manual renewal fails in predictable ways. Someone goes on vacation and misses the calendar reminder. The script that handles renewal breaks during a CI/CD pipeline migration and nobody notices because it fails silently. A certificate is renewed but the new secret is placed in the wrong namespace or with the wrong name, so the Ingress controller keeps serving the old certificate until it expires. These failures share a common root cause: a human being is expected to remember to do something at a future date, and the system has no built-in enforcement mechanism. Automation solves this by removing the human from the critical path entirely. The system monitors expiry dates, initiates renewal on a schedule, and only alerts a human if automation itself fails.

### PKI Fundamentals Worth Teaching

The durable foundation of any certificate automation system is a working mental model of Public Key Infrastructure. You do not need to memorize X.509 field encodings, but you do need to understand the roles and the trust chain.

A **Certificate Authority (CA)** is an entity that signs certificates, vouching that the public key in the certificate belongs to the identity named in the subject. When a client connects to your service, it verifies the certificate by following a chain of trust: your certificate was signed by an intermediate CA, which was signed by a root CA, which is trusted by the client's operating system or browser trust store. If any link in this chain is broken — an expired intermediate, a revoked root, a mismatched domain — the connection fails.

A **Certificate Signing Request (CSR)** is the document you submit to a CA when you want a certificate. It contains your public key, the identity you want to certify (the Common Name and Subject Alternative Names), and a signature proving you hold the corresponding private key. The CA validates your control of the requested identity (through a challenge mechanism), then signs the CSR, producing a signed certificate. cert-manager automates both steps: it generates the key pair and CSR, submits them to the configured issuer, completes the challenge, and stores the resulting certificate in a Kubernetes Secret.

There are three fundamental types of CAs you will encounter in practice, and each serves a different purpose:

A **public CA** like Let's Encrypt issues certificates that are trusted by every major browser and operating system. These are the certificates you use for public-facing services that real users access. Public CAs verify domain ownership through the ACME protocol (described below) and issue certificates with relatively short lifetimes. They are free or low-cost, fully automated, and the default choice for external TLS.

A **private (internal) CA** is one you operate yourself, typically for service-to-service communication inside your cluster or organization. Certificates issued by a private CA are not trusted by external browsers unless you distribute your root certificate to every client — which is impractical for public services but perfectly manageable for internal workloads where you control both ends of the connection. Private CAs give you complete control over certificate policies, lifetimes, and revocation, and they are essential for mTLS architectures where every service presents a certificate to every other service.

A **self-signed certificate** is signed by its own private key rather than by a CA. These are useful exclusively for development and testing, where you need TLS encryption but do not need third-party trust validation. Self-signed certificates will trigger browser warnings and should never appear in production traffic.

### The ACME Protocol and Challenge Types

ACME — Automatic Certificate Management Environment — is the IETF-standardized protocol (RFC 8555) that powers automated certificate issuance from public CAs. Let's Encrypt pioneered ACME, and it has since been adopted by other providers including ZeroSSL, Google Trust Services, and Buypass. The protocol defines how a client (like cert-manager) proves control of a domain to a CA and receives a signed certificate in return.

The core of ACME is the **challenge**: a cryptographic proof that you control the domain you are requesting a certificate for. There are two challenge types that matter in practice, and understanding their tradeoffs is essential for configuring cert-manager correctly.

**HTTP-01** proves domain control by placing a specific file at a well-known URL path on the domain being validated. The CA requests `http://<domain>/.well-known/acme-challenge/<token>` and expects to find a signed response. This challenge is the simplest to set up because it only requires that your service be reachable over HTTP on port 80. cert-manager handles this by temporarily creating a small Ingress resource or pod that serves the challenge response, then cleaning it up after validation succeeds. The limitation is that HTTP-01 cannot issue wildcard certificates (you cannot prove control of `*.example.com` by serving a file on a specific subdomain), and it requires your service to be publicly accessible — it does not work for internal services behind a firewall.

**DNS-01** proves domain control by creating a specific TXT record in the domain's DNS zone. The CA queries for `_acme-challenge.<domain>` and verifies the record contains the expected token. This approach has two major advantages over HTTP-01. First, it supports wildcard certificates — proving DNS control of `example.com` is sufficient to issue a certificate for `*.example.com`. Second, it does not require any HTTP accessibility, so you can issue certificates for internal services, load balancers, or services that are not yet deployed. The tradeoff is that DNS-01 requires programmatic access to your DNS provider's API, and DNS propagation delays can slow down issuance (though cert-manager handles the polling automatically).

The choice between HTTP-01 and DNS-01 is not about which is "better" — it is about which operating constraints apply to your environment. If you are running a public web service and do not need wildcard certificates, HTTP-01 is the simpler path. If you need wildcards, or if your service is not publicly reachable, DNS-01 is required. Many organizations configure both solvers and let cert-manager select the appropriate one based on the Certificate resource's DNS names.

### The Closed-Loop Certificate Lifecycle

The durable goal of certificate automation is a closed loop with four phases, each of which must work without human intervention:

First, **issue**: when a Certificate resource is created, the system generates a key pair, constructs a CSR, submits it to the configured issuer, completes the required challenge, and stores the signed certificate and private key in a Kubernetes Secret. This phase is triggered by resource creation and must succeed within a bounded time (typically minutes).

Second, **install**: the certificate must reach the workload that needs it. In Kubernetes, this means the Secret must be mounted into pods or referenced by Ingress resources. cert-manager handles the Secret creation; the installation step is a collaboration between cert-manager (which writes the Secret) and the workload controller (which watches Secrets and reloads when they change).

Third, **monitor**: the system continuously checks the expiry date of every managed certificate. cert-manager exposes Prometheus metrics including `certmanager_certificate_expiration_timestamp_seconds`, which enables alerting on certificates approaching expiry. Monitoring is a safety net: it detects cases where automation has failed (e.g., a misconfigured DNS solver that prevents renewal) and alerts a human before the certificate actually expires.

Fourth, **renew before expiry**: this is the critical automation step. Based on the `renewBefore` field in the Certificate spec, cert-manager initiates renewal well before the certificate's `notAfter` date. The default is 30 days before expiry for 90-day Let's Encrypt certificates — meaning renewal starts at day 60. The new certificate is issued while the old one is still valid, and the Secret is updated atomically. The Ingress controller or application watching the Secret picks up the new certificate on the next reload, and clients never see a gap. This is the same principle as renewing a passport before it expires, applied systematically.

A failure at any phase breaks the loop. If issuance fails, the Certificate resource enters a `Ready: False` state and no Secret is created. If the Secret is not mounted correctly, the workload continues serving an old or missing certificate. If monitoring is absent, nobody knows a certificate is about to expire until it is too late. And if renewal fails silently — for example, because a DNS solver's API credentials have rotated and the challenge can no longer complete — the certificate expires despite the presence of an automation tool. A well-architected deployment addresses each phase explicitly and alerts on failures at every stage.

---

## Part 2: cert-manager Primitives

With the durable concepts established, we can now map them onto cert-manager's specific Kubernetes resources. cert-manager extends the Kubernetes API with several Custom Resource Definitions (CRDs) that together implement the closed-loop lifecycle described above.

### Issuer and ClusterIssuer

An **Issuer** is a namespaced resource that defines how certificates are obtained — which CA to use, which challenge solvers to employ, and what credentials are needed. An Issuer can only issue certificates within its own namespace, which provides isolation: the `staging` namespace can use a Let's Encrypt staging issuer without affecting production, and a team can manage their own internal CA without risking cross-team certificate issuance.

A **ClusterIssuer** is the cluster-scoped equivalent. It is identical in structure to an Issuer but available to Certificate resources in any namespace. ClusterIssuers are the natural choice for shared infrastructure: a single Let's Encrypt production issuer configured once and used everywhere, or an organizational root CA that signs internal certificates across all teams.

The choice between Issuer and ClusterIssuer follows a simple rule: if the CA configuration is shared infrastructure (Let's Encrypt, an org-wide internal CA, a Vault instance), use a ClusterIssuer to avoid duplicating configuration in every namespace. If the CA is team-specific or carries sensitive credentials that should be scoped narrowly, use a namespaced Issuer. Both are first-class resources and can be mixed — a cluster might have a ClusterIssuer for Let's Encrypt production certificates and per-namespace Issuers for team-specific internal CAs.

### The Certificate Resource

A **Certificate** is the user-facing resource that describes desired state. When you create a Certificate, you are telling cert-manager: "I want a TLS certificate with these DNS names, signed by this issuer, stored in this Secret, renewed within this window." The resource is declarative — you specify what you want, not how to get it.

Key fields on the Certificate spec include:

- `secretName`: the Kubernetes Secret where the resulting key pair and certificate will be stored. This is the integration point with the rest of the system — Ingress resources reference this Secret, and pods mount it as a volume.
- `dnsNames`: the Subject Alternative Names (SANs) that the certificate must cover. Modern TLS validation checks SANs, not the deprecated Common Name field; every domain the certificate serves must appear here.
- `duration` and `renewBefore`: the requested certificate lifetime and how far before expiry renewal should begin. Let's Encrypt may override your requested duration (it caps at 90 days), but `renewBefore` is always honored — cert-manager will attempt renewal when `notAfter - renewBefore` is reached.
- `issuerRef`: points to the Issuer or ClusterIssuer that will fulfill this request.
- `usages`: the key usage extensions — `server auth` for TLS servers, `client auth` for mTLS clients, `code signing`, etc. This maps to the X.509 Key Usage and Extended Key Usage extensions.
- `privateKey`: the algorithm (RSA or ECDSA), encoding (PKCS1 or PKCS8), and key size. ECDSA with P-256 is recommended for modern deployments; it provides equivalent security to RSA-3072 with smaller keys and faster operations.

### Internal Resources: CertificateRequest, Order, Challenge

When you create a Certificate, cert-manager creates a chain of internal resources that track the issuance process. These are not resources you typically create yourself, but understanding them is invaluable for debugging.

A **CertificateRequest** represents a single attempt to obtain a certificate. It contains the encoded CSR and tracks whether the request succeeded or failed. If renewal is needed, cert-manager creates a new CertificateRequest for the renewal attempt. The Certificate resource's status reflects the latest CertificateRequest's state.

For ACME issuers, cert-manager also creates **Order** and **Challenge** resources. An Order tracks the overall ACME transaction — it groups the authorizations needed for each DNS name in the certificate. Each authorization requires a Challenge, which represents a single domain validation attempt (one HTTP-01 or DNS-01 challenge). If you see a Certificate stuck in `Ready: False`, the place to start debugging is `kubectl describe challenge` — the Challenge resource contains the exact error message from the ACME server.

### Ingress and Gateway Integration

The most common integration pattern is the Ingress shim, which reduces certificate management to a single annotation. When cert-manager sees an Ingress resource annotated with `cert-manager.io/cluster-issuer` (or `cert-manager.io/issuer`), it automatically creates a Certificate resource matching the TLS configuration in the Ingress spec. This means you do not need to create a separate Certificate resource — the annotation is sufficient, and cert-manager derives the DNS names, secret name, and issuer reference directly from the Ingress fields.

The shim works by watching the Kubernetes API for Ingress creation and modification events. When a new Ingress appears with the annotation and a TLS block, cert-manager extracts the hosts and `secretName`, constructs a Certificate resource in the same namespace, and begins the issuance process. It also watches for changes — if you update the Ingress to add or remove TLS hosts, cert-manager updates the corresponding Certificate accordingly. The relationship is one-way: cert-manager creates and manages the Certificate based on the Ingress, but deleting the Ingress does not delete the Certificate or Secret. This conservative approach prevents accidental cascading deletions but means you must remember to clean up orphaned Certificate resources manually when decommissioning services.

The flow from annotation to live certificate is: you create an Ingress with TLS hosts and a `secretName`, add the cert-manager annotation, and cert-manager handles the rest. It creates a Certificate, initiates an Order with the ACME server, solves the configured challenge type, receives the signed certificate, populates the Secret, and the Ingress controller picks up the new certificate on its next configuration reload. For most deployments, the end-to-end process completes in under two minutes — the limiting factors being DNS propagation time for DNS-01 challenges and ACME server response times. Once the certificate is in place, renewal proceeds on the same automatic schedule without any change to the Ingress resource.

The same pattern extends to Gateway API resources, where cert-manager can create Certificates based on Gateway and HTTPRoute resources in an experimental capacity. As of the versions covered in this module, the annotation-based Ingress shim remains the most battle-tested and widely deployed integration path for production workloads.

---

### Landscape Snapshot

> **Landscape snapshot — as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**
>
> cert-manager was accepted to the CNCF on 2020-11-10, moved to Incubating on 2022-09-19, and moved to Graduated on 2024-09-29. It is a CNCF Graduated project (source: cncf.io/projects/cert-manager).
>
> Latest release as of 2026-06: **v1.20.2** (2026-04-11). Verify current release at github.com/cert-manager/cert-manager/releases.
>
> API group: `cert-manager.io` (current). The older `certmanager.k8s.io` group has been removed and should not appear in any configuration.

---

### Cross-Tool Rosetta Table: Certificate Automation Approaches

cert-manager is not the only way to automate certificate management. The table below compares it against two other valid approaches — a raw ACME client and a cloud-managed certificate service — across the durable capability dimensions that matter for platform design. None of these is "best"; each operates at a different point in the tradeoff space between control, integration, and operational overhead.

| Capability | cert-manager | Raw ACME client (certbot, lego) | Cloud-managed certs (AWS ACM, Google-managed) |
|---|---|---|---|
| **Where it runs** | In-cluster controller (Kubernetes-native) | External process (VM, container, cron job) | Cloud service (API-driven, fully managed) |
| **CA sources** | ACME, private CA, Vault, Venafi, self-signed | ACME only | Provider's own CA; some support imported certs |
| **Challenge types** | HTTP-01, DNS-01 (many providers) | HTTP-01, DNS-01 (plugin-dependent) | DNS-01 handled transparently by the cloud provider |
| **Wildcard support** | Yes (DNS-01) | Yes (DNS-01) | Yes (provider-managed validation) |
| **Auto-renewal** | Built-in, configurable window | Must be scripted externally (cron, systemd timer) | Built-in, transparent to the user |
| **Secret delivery to workloads** | Native Kubernetes Secrets, auto-reload via volume watches | Must be scripted — copy cert files, restart services | Cloud-native: ALB/NLB attach, GCLB attach; not portable outside the cloud |
| **Governance** | RBAC via Kubernetes, namespaced Issuer isolation | File system permissions, operator discipline | IAM policies, cloud audit logs |

The choice between these approaches depends on where your workloads run and what degree of integration you need. If your entire infrastructure is in a single cloud provider and you use that provider's load balancers, cloud-managed certificates are operationally the simplest — but they tie you to that provider. A raw ACME client gives you maximum control and portability but requires you to build your own distribution and renewal logic. cert-manager occupies the middle ground: it provides the automation of a managed service with the portability of open-source, at the cost of running and maintaining the controller itself.

---

## Part 3: Practical Application

The durable concepts we have covered — the PKI primitives, the ACME protocol, the issuer taxonomy, and the renewal mechanics — are what you carry from cluster to cluster regardless of tooling. But cert-manager itself is the implementation we use to put those concepts into practice, and that means understanding its specific resource YAML, its installation workflow, and the operational patterns that keep it healthy in production. This section walks through the full lifecycle from initial deployment through certificate creation, monitoring, and troubleshooting. Every command and YAML fragment shown here is tested against `cert-manager.io/v1` and reflects the current API group.

### Installation

cert-manager is deployed via Helm, which handles the CRD installation, controller deployment, and webhook configuration in a single command. The controller runs as a Deployment in the `cert-manager` namespace alongside a `cert-manager-cainjector` component that injects CA bundle data into ValidatingWebhookConfiguration and MutatingWebhookConfiguration resources, and a `cert-manager-webhook` component that provides the validating and mutating admission webhooks. Together, these three components form the operational core of a cert-manager installation.

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

The `installCRDs=true` flag is important: cert-manager's CRDs are large and Helm does not manage CRDs by default. Setting this flag ensures the `Certificate`, `Issuer`, `ClusterIssuer`, and other resource types are registered before any resources using them are created.

### Configuring Issuers

The issuer configuration is where you define the CA relationship. The YAML examples below are complete and tested against `cert-manager.io/v1`. Note the use of the correct API group — the historical `certmanager.k8s.io` group was removed years ago and must not appear in any configuration.

**Let's Encrypt production** issuer with HTTP-01 challenge solving:

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

Always test against the staging environment first. Let's Encrypt's production environment enforces rate limits — 50 certificates per registered domain per week — and a misconfigured issuer that repeatedly fails validation can exhaust those limits. The staging environment issues untrusted certificates (browsers will warn about them) but has much higher rate limits, making it the correct target for initial configuration and testing.

**DNS-01 challenge** for wildcard certificates and internal services, shown with Route 53:

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

DNS-01 supports dozens of providers — cert-manager's documentation lists over 30 supported DNS services, including all major cloud providers and many domain registrars. The solver configuration varies by provider, but the pattern is consistent: you provide API credentials (ideally via IRSA in AWS, Workload Identity in GCP, or a Kubernetes Secret containing an API key) and cert-manager handles the ACME challenge lifecycle.

**Self-signed** for local development and testing:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned
spec:
  selfSigned: {}
```

**Internal CA** pattern — first create a self-signed root CA certificate, then create an Issuer backed by that root:

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

The `isCA: true` field on the root Certificate resource sets the X.509 Basic Constraints extension, marking this certificate as authorized to sign other certificates. Without this, the CA issuer would reject signing requests because the backing certificate lacks CA authority.

### Creating Certificates

There are two paths to getting a certificate from cert-manager, and understanding when to use each one is a key operational skill. The explicit path — creating a Certificate resource directly — gives you full control over every field: the key algorithm, the key usages, the requested duration, the subject organization, and the precise DNS names. Use this path when you need a certificate that does not map neatly to a single Ingress resource, such as a wildcard certificate, a certificate for a non-HTTP service, or a certificate shared across multiple Ingress resources in the same namespace.

The implicit path — the Ingress annotation — is the simpler route for standard HTTP workloads. When you add `cert-manager.io/cluster-issuer: letsencrypt-prod` to an Ingress, cert-manager creates a Certificate resource for you, deriving the DNS names from the Ingress TLS hosts and using sensible defaults for all other fields. The resulting Certificate resource is visible in `kubectl get certificates`, and you can inspect and describe it just like any explicitly created Certificate. The two paths produce identical results; they differ only in who writes the Certificate YAML. Both paths converge on the same underlying machinery: a Certificate resource triggers a CertificateRequest, which creates an Order and Challenge for ACME issuers, resulting in a Kubernetes Secret containing the key pair and signed certificate.

**Explicit Certificate** resource gives you full control over key algorithm, usages, and duration:

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

**Ingress annotation** is the simpler path for HTTP services. Add one annotation and cert-manager handles Certificate creation, Secret population, and renewal:

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

The annotation is all you need — cert-manager watches for new and changed Ingress resources, extracts the TLS configuration, and creates the corresponding Certificate. If the Ingress is deleted, cert-manager does not delete the Secret (to avoid accidentally breaking other resources that reference it), so you must manage Secret cleanup separately.

**Wildcard certificates** require DNS-01 and list the wildcard domain as a SAN:

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

Note that the wildcard entry `*.example.com` only covers single-level subdomains like `app.example.com` or `api.example.com`. It does not cover `sub.app.example.com` — for multi-level wildcards you would need `*.app.example.com` as a separate entry.

### Certificate Lifecycle in Practice

The lifecycle diagram below shows what happens at each stage. Understanding these stages helps when debugging: if a Certificate is not becoming Ready, check which stage it is stuck at and examine the corresponding internal resource.

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

The atomic Secret update deserves emphasis. When cert-manager renews a certificate, it writes the new key pair and certificate to the Secret in a single operation. The Ingress controller (or any pod mounting the Secret as a volume) sees the update through the kubelet's Secret watch and reloads automatically. There is no moment where the Secret contains a partial or mismatched key/cert pair, and the old certificate remains valid throughout the transition.

### Monitoring and Troubleshooting

A certificate automation system without monitoring is an accident waiting to happen — automation can fail silently, and the only signal you have is the certificate's expiry date creeping closer. cert-manager exposes Prometheus metrics on its controller pod at the standard `/metrics` endpoint, and two metrics in particular deserve your attention and alerting configuration. The first is `certmanager_certificate_expiration_timestamp_seconds`, which reports the epoch timestamp when each managed certificate will expire. The second is `certmanager_certificate_ready_status`, a boolean indicating whether the Certificate resource is currently in Ready state — meaning the certificate was successfully issued or renewed and is stored in the referenced Secret.

These two metrics cover the two failure modes that matter. An expiring certificate with a Ready status of True is the normal, healthy state — cert-manager will renew it before expiry and you will never notice. An expiring certificate with a Ready status of False means the renewal attempt failed and the certificate is heading toward an outage. A certificate that is Ready but has an expiration date within a week is approaching the danger zone even if it currently looks healthy. Your alerting rules should cover all three combinations, with different severities: a Ready: False state should page on-call immediately, while a certificate approaching expiry with a healthy Ready status should generate a warning that gives the team time to investigate whether renewal is actually in progress.

When you need to check certificate status from the command line — during an incident, a routine audit, or while building automation — the following commands give you visibility into the full lifecycle:

```bash
# List certificates
kubectl get certificates -A

# Describe specific certificate
kubectl describe certificate api-example-com -n production

# Check certificate ready status
kubectl get certificate -o wide

# View certificate details from Secret
kubectl get secret api-example-com-tls -o jsonpath='{.data.tls\\.crt}' | base64 -d | openssl x509 -text -noout

# Check expiry
kubectl get secret api-example-com-tls -o jsonpath='{.data.tls\\.crt}' | base64 -d | openssl x509 -enddate -noout
```

**Debugging ACME challenges** — when a Certificate is not becoming Ready, the Challenge resources contain the exact error:

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

**Prometheus alerting rules** for certificate expiry:

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

These rules cover the two failure modes that matter: a certificate that is approaching expiry (automation may be failing silently) and a certificate that is not ready (issuance is currently failing). Both should page the on-call rotation — certificate failures can cause hard service outages with no graceful degradation path.

---

## Did You Know?

- **Let's Encrypt and the ACME revolution**: Let's Encrypt launched in 2015 and transformed TLS on the web by making certificates free and fully automated. Before Let's Encrypt, obtaining a certificate meant paying a commercial CA, manually generating a CSR, and waiting for human approval — a process that discouraged TLS adoption for small sites and personal projects. Today, Let's Encrypt issues over 300 million certificates per day, and the ACME protocol it pioneered is an IETF standard.

- **cert-manager supports multiple ACME providers**: Beyond Let's Encrypt, cert-manager works with ZeroSSL, Google Trust Services, and Buypass. This matters at scale — if you hit Let's Encrypt's rate limits (50 certificates per registered domain per week), you can configure a second ClusterIssuer with a different ACME provider and spread your certificate load across both.

- **The webhook prevents silent misconfigurations**: cert-manager's validating webhook rejects Certificate resources at admission time if they reference a nonexistent issuer, contain invalid DNS names, or have conflicting configuration. This is a critical safety mechanism — without it, a typo in an issuer name would be discovered only when renewal fails months later.

- **Prometheus metrics are built-in, no sidecar needed**: cert-manager exposes metrics on its controller pod at the standard `/metrics` endpoint. The key metrics — certificate expiry timestamp and ready status — are available immediately after installation with a standard Prometheus scrape configuration. No additional exporter or sidecar container is required.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using staging issuer in production | Browsers do not trust staging certificates; users see TLS warnings | Use `letsencrypt-prod` for production traffic; reserve staging for initial testing |
| HTTP-01 for wildcard certificates | HTTP-01 cannot prove control of `*.example.com` | Configure a DNS-01 challenge solver; wildcards require DNS validation |
| Setting `renewBefore` too close to expiry | If renewal fails, there is no buffer to fix it before expiry | Set `renewBefore` to at least 15-30 days; the default of 30 days is reasonable for most deployments |
| No monitoring on certificate expiry | Certificate can expire silently if automation fails | Alert on `certmanager_certificate_expiration_timestamp_seconds` with at least 14 days of lead time |
| Hitting Let's Encrypt rate limits during testing | Repeated failed validation attempts exhaust the rate limit quota | Always test against the staging environment first; it has higher rate limits and untrusted certificates are harmless for testing |
| Wrong ingress class in solver config | The challenge solver cannot find the Ingress resource to temporarily modify | Match the solver's `ingress.class` to your Ingress controller's class (e.g., `nginx`, `traefik`, `contour`) |
| Forgetting to add the apex domain to wildcard certificates | A wildcard `*.example.com` does not cover `example.com` itself | Always include both `*.example.com` and `example.com` in the `dnsNames` list when requesting a wildcard |
| Using the deprecated `certmanager.k8s.io` API group | This API group was removed years ago; resources using it will not be recognized | All cert-manager resources now use the `cert-manager.io` API group |

---

## Hypothetical Scenario: The Friday Afternoon Expiry

*A team's wildcard certificate expired on a Friday at 5 PM. Their entire domain, covering a dozen microservices, was unreachable for the weekend.*

**What went wrong**: The wildcard certificate had been created manually before cert-manager was adopted. cert-manager was deployed later and began managing new certificates for individual services, but nobody imported the existing wildcard certificate into cert-manager's management. No monitoring covered that certificate — the Prometheus alerts were configured only for cert-manager-managed certificates. The calendar reminder set by the original engineer went to an inbox that had been decommissioned when they left the company six months earlier. The certificate expired, browsers rejected connections to every subdomain, and the on-call engineer spent the weekend manually issuing and deploying a replacement while the incident postmortem filled with the same observation: "We had an automation tool. We just forgot to use it."

**The durable lesson**: Automation only eliminates the failure mode it covers. If some certificates are managed by cert-manager and others are not, the unmanaged ones will eventually expire — and the false confidence that "we have automation" makes those failures worse because nobody is watching. Import every certificate into the automation system. Monitor every certificate, not just the ones you think the tool manages. And ensure monitoring covers the gap between "automation is trying to renew" and "automation has succeeded" — the time to discover a renewal failure is not the day of expiry.

**The checklist fix** — here is the systematic approach to prevent this category of failure:
1. Audit every TLS Secret in the cluster and identify which are and are not backed by cert-manager Certificate resources
2. Import all existing, unmanaged certificates into cert-manager by creating matching Certificate resources pointing to the existing Secret using the `secretName` field
3. Configure Prometheus alerts to cover all TLS Secrets, not only cert-manager ones, as a defense-in-depth measure
4. Use a `renewBefore` of at least 30 days to maximize the window for detecting and fixing renewal failures
5. Page on-call for any Certificate in `Ready: False` state — a failed renewal that degrades silently for weeks is an outage waiting to happen

---

## Quiz

The questions below test your understanding of the durable concepts behind certificate automation, not just cert-manager's specific YAML fields. Each question covers a tradeoff or design decision you will face when deploying certificate automation in production.

### Question 1

Understanding the ACME challenge types is fundamental to choosing the right issuer configuration. What is the fundamental difference between HTTP-01 and DNS-01 ACME challenges, and when must you use DNS-01?

<details>
<summary>Show Answer</summary>

**HTTP-01** proves domain control by serving a specific file at `/.well-known/acme-challenge/<token>` on the domain being validated. It requires the service to be reachable over HTTP on port 80 and cannot issue wildcard certificates because you cannot serve a file that proves control of `*.example.com`.

**DNS-01** proves domain control by creating a `_acme-challenge.<domain>` TXT record in DNS. It does not require any HTTP accessibility and can issue wildcard certificates because proving DNS control of `example.com` is sufficient for `*.example.com`.

You must use DNS-01 when you need wildcard certificates or when your service is not publicly accessible over HTTP (internal services, pre-deployment validation).

</details>

### Question 2

Zero-downtime renewal distinguishes a well-automated certificate system from a fragile one. How does cert-manager achieve zero-downtime certificate renewal, and why does `renewBefore` matter for this mechanism?

<details>
<summary>Show Answer</summary>

cert-manager achieves zero-downtime renewal through early initiation and atomic update. The `renewBefore` field causes renewal to begin before the current certificate expires — for example, with `renewBefore: 360h` (15 days) on a 90-day certificate, renewal starts at day 75. cert-manager issues the new certificate while the old one is still valid, then atomically updates the Kubernetes Secret with both the new key and certificate in a single write.

The Ingress controller or application watching the Secret detects the change and reloads, picking up the new certificate. During the entire process, the old certificate remains valid and serves traffic — clients never see an expired certificate or a TLS handshake failure. The `renewBefore` window provides the buffer between when renewal starts and when the old certificate dies. If renewal fails, the remaining validity period gives you time to intervene before an outage.

</details>

### Question 3

Issuer and ClusterIssuer represent a namespace-scoping decision that has operational consequences for how your team manages CA configuration across environments. When would you use a namespaced Issuer rather than a ClusterIssuer, and what isolation property does this provide?

<details>
<summary>Show Answer</summary>

A namespaced **Issuer** can only be referenced by Certificate resources in the same namespace. This provides namespace-level isolation: the `staging` namespace can use a Let's Encrypt staging issuer without risking that a production Certificate accidentally picks up a staging CA, and a team managing their own internal CA can scope credentials and configuration to their namespace only.

A **ClusterIssuer** is available to all namespaces and is the natural choice for shared infrastructure — a single Let's Encrypt production issuer used cluster-wide, or an organizational root CA for internal service certificates.

Use an Issuer when the CA configuration carries namespace-specific credentials or when you want to enforce that certain CAs are only available in specific namespaces. Use a ClusterIssuer for shared, cluster-wide CA configurations to avoid duplicating the same YAML in every namespace.

</details>

### Question 4

cert-manager's webhook is easy to overlook during installation but it provides a critical safety boundary at the Kubernetes API level. What is the purpose of cert-manager's validating webhook, and what class of failure does it prevent?

<details>
<summary>Show Answer</summary>

The validating webhook intercepts Certificate, Issuer, and ClusterIssuer resource creation and update requests at the Kubernetes API server admission stage. It validates the resources before they are persisted, rejecting configurations that reference nonexistent issuers, contain malformed DNS names, or have conflicting settings.

The webhook prevents **silent misconfiguration failures** — errors that would only surface weeks or months later at renewal time. Without the webhook, a Certificate that references a misspelled issuer name would be accepted and stored, and you would discover the problem only when renewal failed and the certificate expired. With the webhook, the invalid Certificate is rejected immediately at `kubectl apply` time, forcing you to fix the configuration before it can cause an outage.

</details>

### Question 5

Setting `isCA: true` on a Certificate resource has a specific effect on the resulting X.509 certificate that distinguishes it from end-entity certificates. Why does the internal CA pattern require the root Certificate to have `isCA: true`, and what X.509 extension does this set?

<details>
<summary>Show Answer</summary>

The `isCA: true` field on the root Certificate resource sets the X.509 **Basic Constraints** extension with the CA flag set to `TRUE`. This extension marks the certificate as authorized to sign other certificates — it is what makes the certificate function as a Certificate Authority rather than as an end-entity certificate.

When cert-manager's CA issuer receives a signing request, it checks the backing certificate's Basic Constraints extension. If the CA flag is not set, the issuer rejects the signing request because the backing certificate lacks the authority to act as a CA. This is a security boundary: it prevents a regular server certificate from being accidentally (or maliciously) used as a CA to sign additional certificates.

</details>

### Question 6

Debugging a certificate that is stuck in `Ready: False` requires tracing through the internal resource chain that cert-manager creates during the issuance process. A Certificate resource shows `Ready: False` with an ACME issuer. What internal resources should you examine first to diagnose the failure, and in what order?

<details>
<summary>Show Answer</summary>

Examine the resources in this order, following the ACME lifecycle chain:

1. **Certificate** — `kubectl describe certificate <name>` shows the overall status and any top-level error messages. The `status.conditions` field indicates whether the failure is in the issuance or renewal phase.

2. **CertificateRequest** — identified from the Certificate's status, this resource contains the CSR and the specific error from the last issuance attempt. It is the first place to see what the CA rejected.

3. **Order** — the Order tracks the ACME transaction for all DNS names on the certificate. An Order status of `pending` or `errored` indicates the ACME flow has not completed.

4. **Challenge** — the most detailed error source. `kubectl describe challenge <name>` shows the exact challenge type, the validation state, and any error from the ACME server. Common errors include "connection refused" (HTTP-01 path not reachable), "no TXT record found" (DNS propagation delay), and "too many failed authorizations" (rate limiting).

The chain is Certificate → CertificateRequest → Order → Challenge. Each resource's status references the next, so you can trace the failure from the top down.

</details>

### Question 7

Wildcard certificates are a common source of confusion because the wildcard pattern only covers a specific depth of subdomains — and the apex domain is not included unless explicitly listed. You configure a wildcard certificate with `dnsNames: ["*.example.com"]` and discover that `https://example.com` (the apex domain) fails TLS validation. Why?

<details>
<summary>Show Answer</summary>

The wildcard `*.example.com` matches single-level subdomains like `app.example.com` or `api.example.com`. It does **not** match the apex domain `example.com` itself. The TLS handshake performs an exact match between the domain the client requested and the Subject Alternative Names in the certificate; `example.com` is not covered by `*.example.com`.

The fix is to include both entries in the `dnsNames` list:
```yaml
dnsNames:
  - "*.example.com"
  - example.com
```

This pattern applies universally — any wildcard certificate that needs to cover the apex domain must list it explicitly alongside the wildcard entry.

</details>

### Question 8

The Ingress shim is the most commonly used cert-manager integration, but its behavior around resource deletion is a frequent source of surprises for operators who assume Kubernetes-native cascading cleanup. How does cert-manager's Ingress shim work, and what happens to the Secret when the Ingress is deleted?

<details>
<summary>Show Answer</summary>

The Ingress shim is a controller that watches for Ingress resources with the annotation `cert-manager.io/cluster-issuer` or `cert-manager.io/issuer`. When it finds a matching Ingress with TLS configuration, it automatically creates a Certificate resource with the hosts and secret name from the Ingress spec. cert-manager then manages the full lifecycle of that Certificate — issuance, renewal, and Secret population — as if you had created the Certificate resource manually.

When the Ingress is deleted, cert-manager does **not** delete the corresponding Certificate or Secret. This is a deliberate design choice: the Secret may be referenced by other resources (e.g., a pod mounting it directly), and deleting it could cause cascading failures. You must manage Secret and Certificate cleanup explicitly — `kubectl delete certificate <name>` when the corresponding Ingress is removed.

</details>

---

## Key Takeaways

The durable concepts from this module apply regardless of which certificate automation tool you use. Here is what you should carry forward:

- **Certificates expire. Automation is the only architecture that scales.** A closed-loop lifecycle — issue, install, monitor, renew — with no human in the critical path is the durable solution to certificate management.
- **ACME is the standard for automated public certificates.** Understand the two challenge types: HTTP-01 for simple public services, DNS-01 for wildcards and internal services. The choice is about operating constraints, not superiority.
- **Issuer vs. ClusterIssuer is about scope and isolation.** Use ClusterIssuers for shared infrastructure (Let's Encrypt, org-wide internal CA). Use namespaced Issuers for team-specific CAs and credential isolation.
- **The Certificate resource is declarative desired state.** You specify what certificate you want — domains, issuer, rotation window — and cert-manager handles the how. The annotation-based Ingress shim reduces this to a single line of configuration.
- **Monitoring is not optional.** `certmanager_certificate_expiration_timestamp_seconds` and `certmanager_certificate_ready_status` must alert before expiry and on Ready: False. An automation tool without monitoring is a certificate expiry system with extra steps.
- **Every certificate in the cluster belongs under management.** Unmanaged certificates that coexist with cert-manager create false confidence — the ones you forgot about are the ones that will cause the outage.

The exercise below gives you hands-on practice with the full certificate lifecycle so you can internalize these patterns through direct experience.

---

## Hands-On Exercise

### Objective

This exercise walks you through the complete cert-manager lifecycle in a local or development cluster. You will install cert-manager, configure a self-signed issuer, request a certificate, and verify that the resulting Kubernetes Secret contains a valid key pair and X.509 certificate with the correct DNS names.

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
   kubectl get secret myapp-tls-secret -o jsonpath='{.data.tls\\.crt}' | base64 -d | openssl x509 -text -noout | head -20
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

For a more realistic integration test, create an Ingress resource with the cert-manager annotation and verify that cert-manager automatically creates a corresponding Certificate resource and populates the referenced Secret — then confirm that the Secret is not deleted when you remove the Ingress.

---

## Sources

- [cert-manager Documentation](https://cert-manager.io/docs/)
- [CNCF cert-manager Project Page](https://www.cncf.io/projects/cert-manager/)
- [cert-manager GitHub Repository](https://github.com/cert-manager/cert-manager)
- [cert-manager Releases](https://github.com/cert-manager/cert-manager/releases)
- [Let's Encrypt](https://letsencrypt.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [ACME Protocol RFC 8555](https://tools.ietf.org/html/rfc8555)
- [cert-manager ACME Configuration](https://cert-manager.io/docs/configuration/acme/)
- [cert-manager CA Issuer Configuration](https://cert-manager.io/docs/configuration/ca/)
- [cert-manager Certificate Resource Reference](https://cert-manager.io/docs/usage/certificate/)
- [cert-manager Ingress Configuration](https://cert-manager.io/docs/usage/ingress/)

---

## Next Module

The certificate lifecycle automation skills you have built here apply directly to the broader platform tooling landscape. Continue to [Developer Experience Toolkit](/platform/toolkits/developer-experience/devex-tools/) to learn about k9s, Telepresence, and the local Kubernetes development tools that make day-to-day platform work productive and enjoyable.

---

*"The best security feature is one that's automatic. cert-manager makes TLS invisible — and invisible infrastructure is the highest compliment you can pay an operations tool."*
