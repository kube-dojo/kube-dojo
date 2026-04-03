---
title: "Module 10.9: Zero Trust Architecture in Hybrid Cloud"
slug: cloud/enterprise-hybrid/module-10.9-zero-trust
sidebar:
  order: 10
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2.5h | **Prerequisites**: Kubernetes Networking, Identity & Access Management, Service Mesh Basics

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Implement zero trust network architectures for Kubernetes using service mesh mTLS, network policies, and SPIFFE identities**
- **Configure workload identity verification with SPIFFE/SPIRE across multi-cluster and multi-cloud environments**
- **Deploy micro-segmentation policies that enforce least-privilege network access at the pod and service level**
- **Design end-to-end zero trust architectures that cover ingress, east-west, and egress traffic in Kubernetes clusters**

---

## Why This Module Matters

In February 2024, a pharmaceutical company with 4,500 employees and a traditional perimeter-based security model was breached through a contractor's compromised VPN credentials. The attacker used the VPN to access the internal network, then moved laterally across 14 systems over 18 days before being detected. They exfiltrated clinical trial data, patient records, and intellectual property valued at an estimated $340 million. The investigation revealed that once inside the VPN perimeter, the attacker had access to 83% of internal services because the security model assumed that anything inside the network was trusted.

This is the fundamental flaw of perimeter security: it creates a hard outer shell and a soft interior. A VPN gives you an all-or-nothing binary: you are either outside (no access) or inside (access to almost everything). In a world where contractors, remote employees, cloud services, and Kubernetes clusters all need varying levels of access, the perimeter model is dangerously inadequate.

Zero Trust flips this model. Instead of "trust everything inside the network," Zero Trust says "trust nothing, verify everything." Every request -- whether it comes from inside your data center, from a Kubernetes pod, from an employee's laptop, or from a cloud service -- must prove its identity, demonstrate it is authorized, and pass through policy evaluation before being granted access. In this module, you will learn the principles of Zero Trust architecture, how BeyondCorp and Identity-Aware Proxies work, how to implement micro-segmentation in Kubernetes, how to replace VPNs with modern access patterns, and how SLSA frameworks secure your CI/CD supply chain.

---

## Zero Trust Principles

### The Three Pillars

```text
┌──────────────────────────────────────────────────────────────┐
│                    ZERO TRUST PILLARS                          │
│                                                                │
│  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  1. VERIFY        │  │  2. LEAST       │  │  3. ASSUME   │ │
│  │     EXPLICITLY     │  │     PRIVILEGE    │  │     BREACH   │ │
│  │                    │  │                  │  │              │ │
│  │  - Identity        │  │  - Just-in-time │  │  - Segment   │ │
│  │  - Device health  │  │  - Just-enough   │  │  - Encrypt   │ │
│  │  - Location       │  │  - Time-limited  │  │  - Monitor   │ │
│  │  - Service ID     │  │  - Scope-limited │  │  - Detect    │ │
│  │  - Risk score     │  │  - Reviewed      │  │  - Respond   │ │
│  └──────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                                │
│  Trust is never binary. Trust is a spectrum that is            │
│  continuously evaluated based on real-time signals.            │
└──────────────────────────────────────────────────────────────┘
```

### Zero Trust vs Perimeter Security

| Aspect | Perimeter Security | Zero Trust |
| :--- | :--- | :--- |
| **Trust model** | Inside network = trusted | Nothing trusted by default |
| **Network access** | VPN grants broad access | Per-resource access based on identity + context |
| **Lateral movement** | Easy once inside | Micro-segmented, each service independently secured |
| **Authentication** | Once at VPN login | Continuous, per-request |
| **Authorization** | Network-level (IP, VLAN) | Application-level (identity, role, context) |
| **Encryption** | At the perimeter (TLS termination) | Everywhere (mTLS between all services) |
| **Monitoring** | Perimeter logs (firewall) | Every transaction logged and analyzed |
| **Kubernetes impact** | Cluster accessible via VPN | Each pod/service independently authenticated |

---

## BeyondCorp: Google's Zero Trust Implementation

Google pioneered Zero Trust at enterprise scale with BeyondCorp, their internal access model that eliminated the corporate VPN entirely. Every Google employee accesses internal applications the same way from any network -- there is no "corporate network" that grants additional trust.

### BeyondCorp Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│  BEYONDCORP ACCESS MODEL                                       │
│                                                                │
│  Employee (any network)                                        │
│       │                                                        │
│       │  HTTPS (always encrypted)                              │
│       ▼                                                        │
│  ┌─────────────────────────────────┐                          │
│  │  Identity-Aware Proxy (IAP)     │                          │
│  │                                  │                          │
│  │  Checks:                         │                          │
│  │  1. Identity (OIDC/SAML)        │                          │
│  │  2. Device trust (MDM enrolled?) │                          │
│  │  3. Context (location, time)    │                          │
│  │  4. Risk score (behavioral)     │                          │
│  │  5. Access policy (per-app)     │                          │
│  └────────────┬────────────────────┘                          │
│               │                                                │
│       ┌───────┴───────┐                                       │
│       │  ALLOW?        │                                       │
│       │  Yes → Proxy   │                                       │
│       │  to backend    │                                       │
│       │  No → 403      │                                       │
│       └───────┬────────┘                                       │
│               │                                                │
│  ┌────────────▼────────────────────┐                          │
│  │  Internal Application           │                          │
│  │  (K8s Service, VM, SaaS)       │                          │
│  │                                  │                          │
│  │  No public endpoint needed      │                          │
│  │  IAP handles all external access│                          │
│  └─────────────────────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
```

### Identity-Aware Proxy Implementations

| Provider | Service | How It Works |
| :--- | :--- | :--- |
| **GCP** | Cloud IAP | Built-in proxy for GCE, GKE, App Engine. Checks Google Identity + device trust via Endpoint Verification. |
| **AWS** | Verified Access | Evaluates identity (IAM Identity Center) + device posture (Jamf, CrowdStrike) per request. Runs at the VPC level. |
| **Azure** | Azure AD Application Proxy | Proxies requests to on-prem/cloud apps. Evaluates Conditional Access policies per request. |
| **Open Source** | Pomerium, OAuth2-proxy, Teleport | Self-hosted proxies with OIDC integration. Full control, requires operational effort. |

### AWS Verified Access for Kubernetes

```bash
# Create a Verified Access trust provider (connects to your IdP)
VA_TRUST=$(aws ec2 create-verified-access-trust-provider \
  --trust-provider-type user \
  --user-trust-provider-type oidc \
  --oidc-options '{
    "Issuer": "https://company.okta.com/oauth2/default",
    "AuthorizationEndpoint": "https://company.okta.com/oauth2/default/v1/authorize",
    "TokenEndpoint": "https://company.okta.com/oauth2/default/v1/token",
    "UserInfoEndpoint": "https://company.okta.com/oauth2/default/v1/userinfo",
    "ClientId": "0oa1234567abcdefg",
    "ClientSecret": "secret123",
    "Scope": "openid profile email groups"
  }' \
  --query 'VerifiedAccessTrustProvider.VerifiedAccessTrustProviderId' --output text)

# Create a Verified Access instance
VA_INSTANCE=$(aws ec2 create-verified-access-instance \
  --query 'VerifiedAccessInstance.VerifiedAccessInstanceId' --output text)

# Attach the trust provider to the instance
aws ec2 attach-verified-access-trust-provider \
  --verified-access-instance-id $VA_INSTANCE \
  --verified-access-trust-provider-id $VA_TRUST

# Create an endpoint that points to your K8s ingress
VA_GROUP=$(aws ec2 create-verified-access-group \
  --verified-access-instance-id $VA_INSTANCE \
  --query 'VerifiedAccessGroup.VerifiedAccessGroupId' --output text)

aws ec2 create-verified-access-endpoint \
  --verified-access-group-id $VA_GROUP \
  --endpoint-type load-balancer \
  --attachment-type vpc \
  --domain-certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/abc-123 \
  --application-domain dashboard.company.com \
  --endpoint-domain-prefix dashboard \
  --load-balancer-options '{
    "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/k8s-ingress/abc123",
    "Port": 443,
    "Protocol": "https",
    "SubnetIds": ["subnet-aaa", "subnet-bbb"]
  }' \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "ec2:*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "verified_access.groups": ["engineering"]
        }
      }
    }]
  }'
```

### Pomerium: Open-Source Identity-Aware Proxy for Kubernetes

```yaml
# Deploy Pomerium as an IAP in front of Kubernetes services
apiVersion: v1
kind: ConfigMap
metadata:
  name: pomerium-config
  namespace: pomerium
data:
  config.yaml: |
    authenticate_service_url: https://authenticate.company.com
    identity_provider: oidc
    identity_provider_url: https://company.okta.com/oauth2/default
    identity_provider_client_id: 0oa1234567abcdefg
    identity_provider_client_secret_file: /secrets/idp-client-secret

    policy:
      # ArgoCD: only platform engineers
      - from: https://argocd.company.com
        to: http://argocd-server.argocd.svc.cluster.local:80
        allowed_groups:
          - platform-engineers
        cors_allow_preflight: true
        preserve_host_header: true

      # Grafana: all engineers, read-only for non-SRE
      - from: https://grafana.company.com
        to: http://grafana.monitoring.svc.cluster.local:3000
        allowed_groups:
          - all-engineers
        set_request_headers:
          X-Grafana-Role: |
            {{- if .Groups | has "sre-team" -}}Admin{{- else -}}Viewer{{- end -}}

      # Backstage: all engineers
      - from: https://backstage.company.com
        to: http://backstage.backstage.svc.cluster.local:7007
        allowed_groups:
          - all-engineers

      # Kubernetes Dashboard: platform team only, with device trust
      - from: https://k8s-dashboard.company.com
        to: http://kubernetes-dashboard.kubernetes-dashboard.svc.cluster.local:443
        tls_skip_verify: true
        allowed_groups:
          - platform-engineers
        allowed_idp_claims:
          device_trust:
            - "managed"
```

---

## Micro-Segmentation in Kubernetes

Micro-segmentation applies the Zero Trust principle of "assume breach" at the network level. Instead of a flat network where any pod can talk to any other pod, micro-segmentation restricts communication to only explicitly allowed paths.

### Defense in Depth with Network Policies

```text
┌──────────────────────────────────────────────────────────────┐
│  MICRO-SEGMENTATION LAYERS                                     │
│                                                                │
│  Layer 1: Namespace Isolation                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ payments NS │  │ identity NS │  │ search NS   │          │
│  │ (default    │  │ (default    │  │ (default    │          │
│  │  deny all)  │  │  deny all)  │  │  deny all)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                                │
│  Layer 2: Service-Level Policies                               │
│  ┌─────────────┐       ┌─────────────┐                       │
│  │ frontend ──────────► │ backend     │  Only frontend can   │
│  │ (port 80)   │       │ (port 8080) │  reach backend        │
│  └─────────────┘       └──────┬──────┘                       │
│                                │                              │
│                        ┌───────▼──────┐                       │
│                        │ database     │  Only backend can     │
│                        │ (port 5432)  │  reach database       │
│                        └──────────────┘                       │
│                                                                │
│  Layer 3: mTLS (Service Mesh)                                  │
│  Every connection authenticated + encrypted                    │
│  SPIFFE identities verified per request                        │
│                                                                │
│  Layer 4: Application-Level Authorization                      │
│  HTTP method + path + headers checked per request             │
│  Istio AuthorizationPolicy or OPA                             │
└──────────────────────────────────────────────────────────────┘
```

### Comprehensive Network Policy Set

```yaml
# Layer 1: Default deny all ingress and egress in every namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: payments
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress

---
# Layer 2: Allow DNS resolution (required for all pods)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: payments
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to: []
      ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53

---
# Layer 2: Frontend can receive traffic from ingress controller
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-to-frontend
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: payment-frontend
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
          podSelector:
            matchLabels:
              app.kubernetes.io/name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080

---
# Layer 2: Frontend can talk to backend API only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-to-backend
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: payment-frontend
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: payment-backend
      ports:
        - protocol: TCP
          port: 8080

---
# Layer 2: Backend can talk to database only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-to-database
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: payment-backend
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: payment-database
      ports:
        - protocol: TCP
          port: 5432

---
# Layer 2: Backend can talk to external payment gateway
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-to-payment-gateway
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: payment-backend
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 203.0.113.0/24  # Payment gateway IP range
      ports:
        - protocol: TCP
          port: 443
```

### Istio Authorization Policies (Layer 4)

```yaml
# Only the payment-frontend service account can call the payment-backend
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: payment-backend-authz
  namespace: payments
spec:
  selector:
    matchLabels:
      app: payment-backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - "cluster.local/ns/payments/sa/payment-frontend"
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/v1/payments/*", "/api/v1/refunds/*"]
    - from:
        - source:
            principals:
              - "cluster.local/ns/monitoring/sa/prometheus"
      to:
        - operation:
            methods: ["GET"]
            paths: ["/metrics"]

---
# Deny all other access to payment-backend
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: payment-backend-deny-all
  namespace: payments
spec:
  selector:
    matchLabels:
      app: payment-backend
  action: DENY
  rules:
    - from:
        - source:
            notPrincipals:
              - "cluster.local/ns/payments/sa/payment-frontend"
              - "cluster.local/ns/monitoring/sa/prometheus"
```

---

## Removing VPNs: The Path to Zero Trust Access

### The VPN Replacement Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│  FROM VPN TO ZERO TRUST                                        │
│                                                                │
│  BEFORE (VPN):                                                 │
│  ┌──────────┐     ┌─────────┐     ┌──────────────────────┐   │
│  │ Employee  │────►│   VPN   │────►│  FLAT NETWORK        │   │
│  │ Laptop    │     │ Gateway │     │  (access to 83% of   │   │
│  └──────────┘     └─────────┘     │   internal services)  │   │
│                                    └──────────────────────┘   │
│                                                                │
│  AFTER (Zero Trust):                                           │
│  ┌──────────┐     ┌─────────────────┐     ┌──────────────┐   │
│  │ Employee  │────►│ Identity-Aware  │────►│ Only the ONE │   │
│  │ Laptop    │     │ Proxy           │     │ service they │   │
│  │           │     │                 │     │ need access  │   │
│  │ Checks:   │     │ Checks:         │     │ to           │   │
│  │ - Device  │     │ - Identity      │     │              │   │
│  │ - Posture │     │ - Authorization │     │ mTLS, logged │   │
│  │ - Cert    │     │ - Context       │     │ per-request  │   │
│  └──────────┘     └─────────────────┘     └──────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### kubectl Access Without VPN

```yaml
# Teleport for Zero Trust Kubernetes access
# teleport-kube-agent.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: teleport-kube-agent
  namespace: teleport
spec:
  replicas: 2
  selector:
    matchLabels:
      app: teleport-kube-agent
  template:
    metadata:
      labels:
        app: teleport-kube-agent
    spec:
      serviceAccountName: teleport-kube-agent
      containers:
        - name: teleport
          image: public.ecr.aws/gravitational/teleport-distroless:16
          args:
            - "--config=/etc/teleport/teleport.yaml"
          volumeMounts:
            - name: config
              mountPath: /etc/teleport
      volumes:
        - name: config
          configMap:
            name: teleport-config

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: teleport-config
  namespace: teleport
data:
  teleport.yaml: |
    version: v3
    teleport:
      join_params:
        token_name: kube-agent-token
        method: kubernetes
      proxy_server: teleport.company.com:443
    kubernetes_service:
      enabled: true
      listen_addr: 0.0.0.0:3027
      kube_cluster_name: eks-prod-east
      labels:
        environment: production
        provider: aws
        region: us-east-1
```

```bash
# Developer workflow: access kubectl without VPN
# 1. Login via browser-based SSO
tsh login --proxy=teleport.company.com

# 2. List available clusters
tsh kube ls
# Cluster             Labels
# ------------------- ----------------------------------
# eks-prod-east       environment=production provider=aws
# aks-staging-west    environment=staging   provider=azure
# onprem-legacy       environment=production provider=onprem

# 3. Connect to a cluster
tsh kube login eks-prod-east

# 4. Use kubectl normally (proxied through Teleport)
kubectl get pods -n payments

# Every command is:
# - Authenticated via SSO (no static kubeconfig)
# - Authorized per Teleport RBAC (namespace/verb restrictions)
# - Logged with session recording
# - Time-limited (session expires after configured duration)
```

---

## SLSA in Enterprise CI/CD

Supply chain security is a critical component of Zero Trust. SLSA (Supply-chain Levels for Software Artifacts) provides a framework for securing the CI/CD pipeline.

### SLSA Levels

| Level | Requirement | What It Prevents |
| :--- | :--- | :--- |
| **SLSA 1** | Build process documented | "How was this built?" is answerable |
| **SLSA 2** | Version-controlled build, authenticated provenance | Source tampering, build reproducibility |
| **SLSA 3** | Hardened build platform, non-falsifiable provenance | Compromised build system, forged attestations |
| **SLSA 4** | Two-person review, hermetic builds | Insider threats, dependency confusion |

### Implementing SLSA for Kubernetes Deployments

```yaml
# GitHub Actions pipeline with SLSA provenance
name: Build and Deploy with SLSA
on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write
  id-token: write    # Required for OIDC-based signing

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.build.outputs.digest }}

    steps:
      - uses: actions/checkout@v4

      - name: Build container image
        id: build
        run: |
          docker build -t ghcr.io/company/payment-service:${{ github.sha }} .
          DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/company/payment-service:${{ github.sha }} | cut -d@ -f2)
          echo "digest=$DIGEST" >> $GITHUB_OUTPUT

      - name: Push to registry
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/company/payment-service:${{ github.sha }}

      - name: Sign image with cosign (keyless)
        uses: sigstore/cosign-installer@v3
      - run: |
          cosign sign --yes \
            ghcr.io/company/payment-service@${{ steps.build.outputs.digest }}

      - name: Generate SLSA provenance
        uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v2.0.0
        with:
          image: ghcr.io/company/payment-service
          digest: ${{ steps.build.outputs.digest }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Verify signature before deploy
        run: |
          cosign verify \
            --certificate-identity-regexp='https://github.com/company/.*' \
            --certificate-oidc-issuer='https://token.actions.githubusercontent.com' \
            ghcr.io/company/payment-service@${{ needs.build.outputs.digest }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/payment-service \
            payment-service=ghcr.io/company/payment-service@${{ needs.build.outputs.digest }} \
            -n payments
```

```yaml
# Kyverno policy: only allow signed images from our CI/CD
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-slsa-provenance
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: verify-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/company/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/company/*"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: "https://rekor.sigstore.dev"
          mutateDigest: true
          verifyDigest: true
          required: true
```

---

## Did You Know?

1. Google's BeyondCorp project started in 2011 after Operation Aurora, a sophisticated cyberattack from China that compromised Google's internal systems through a VPN vulnerability. Google spent 8 years migrating from perimeter security to BeyondCorp, making the transition for over 100,000 employees. By 2019, no Google employee used a VPN for internal access. The total cost of the migration was estimated at over $500 million, but Google calculated it saved them $4 billion in prevented breach costs over the following 5 years.

2. The SLSA framework was created by Google in 2021 based on their internal "Binary Authorization for Borg" (BAB) system, which has been mandatory for all Google production deployments since 2013. Every binary running in Google's production environment must have verifiable provenance -- a cryptographically signed attestation of how, when, and where it was built. This prevented multiple insider threats and supply chain attacks that would have otherwise succeeded.

3. Network Policies in Kubernetes are implemented by the CNI plugin, not by Kubernetes itself. This means that if your CNI does not support Network Policies (like the default kubenet in some managed services or Flannel without extension), your NetworkPolicy resources are silently ignored -- they exist as objects but have zero enforcement. Calico, Cilium, and Azure CNI all support Network Policies. Always verify enforcement, not just resource creation.

4. Pomerium, the open-source Identity-Aware Proxy, was created by engineers who found that Google's BeyondCorp papers described a brilliant architecture but provided no open-source implementation. Pomerium reached 10,000 GitHub stars in 2024 and is used by organizations ranging from 50-person startups to Fortune 500 companies. The average Pomerium deployment replaces 3-5 VPN appliances, saving approximately $120,000/year in licensing costs.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Zero Trust without identity foundation** | Teams jump to micro-segmentation and IAP without first establishing strong identity (OIDC, device trust, service accounts). | Start with identity: deploy OIDC for humans, SPIFFE for services, device trust for endpoints. Then layer on micro-segmentation and IAP. |
| **Network Policies without default deny** | Teams add "allow" policies but never set the default deny baseline. Pods can still communicate freely on paths without explicit policies. | Always start with a default-deny NetworkPolicy in every namespace. Then add explicit allow policies for each legitimate communication path. |
| **mTLS in the mesh but plaintext sidecars** | Service mesh provides mTLS between proxies, but the connection from the proxy to the application container inside the same pod is plaintext on localhost. | This is expected behavior -- localhost traffic within a pod is considered trusted. If you need end-to-end encryption (e.g., for FIPS compliance), the application itself must implement TLS. |
| **VPN removal without alternative** | Security team removes the VPN before deploying IAP or Teleport. Developers cannot access anything. Shadow IT VPN tunnels appear. | Deploy the Zero Trust access layer first (IAP, Teleport). Run it in parallel with the VPN for 3-6 months. Only decommission the VPN after all access patterns are migrated. |
| **Image signing without admission enforcement** | CI/CD pipeline signs images with cosign, but no admission webhook verifies signatures. Unsigned images can still be deployed. | Deploy Kyverno or Gatekeeper with image verification policies. Signing without enforcement is security theater. |
| **Overly broad Istio AuthorizationPolicies** | Teams write policies with `action: ALLOW` that match too broadly, effectively allowing everything. The policy exists but does not restrict. | Use deny-by-default: start with an AuthorizationPolicy that denies all, then add specific allow rules for each legitimate path. Test with `istioctl analyze`. |

---

## Quiz

<details>
<summary>Question 1: Explain the difference between perimeter security and Zero Trust using a Kubernetes-specific example.</summary>

**Perimeter security**: A developer connects to the corporate VPN, which gives them network access to the Kubernetes API server. Once authenticated to the cluster (often via a shared kubeconfig), they can access any namespace because broad RBAC roles were granted for convenience. If their VPN credentials are compromised, the attacker has the same broad access.

**Zero Trust**: The developer accesses the Kubernetes cluster through an Identity-Aware Proxy (like Teleport or Pomerium). They authenticate via SSO with MFA. Their device must have an up-to-date OS and an MDM-enrolled certificate. Teleport checks their group membership and grants access only to specific namespaces with specific verbs (e.g., get/list pods in the payments namespace, no exec, no delete). The session is recorded and time-limited (expires after 8 hours). If their credentials are compromised, the attacker also needs their device, their MFA, and can only access the limited scope granted by the policy. No VPN, no broad network access.
</details>

<details>
<summary>Question 2: A team has deployed Network Policies with a default-deny rule, but pods can still communicate freely. What is the most likely cause?</summary>

The most likely cause is that **the CNI plugin does not support Network Policies**. NetworkPolicy resources are processed by the CNI plugin, not by the Kubernetes API server. If the cluster uses a CNI that does not implement the NetworkPolicy API (like Flannel without the Calico integration, or AWS VPC CNI without the network policy controller), the NetworkPolicy objects are stored in etcd but have no enforcement. The pods see no firewalling because there is no component enforcing the rules. To diagnose: (1) Check which CNI is installed (`kubectl get pods -n kube-system | grep -E 'calico|cilium|weave'`). (2) Verify the CNI supports Network Policies (check documentation). (3) Test enforcement: create a default-deny policy and verify that pods actually cannot communicate. On EKS, you need to enable the VPC CNI network policy feature or install Calico alongside VPC CNI.
</details>

<details>
<summary>Question 3: How does SLSA Level 3 protect against a compromised CI/CD system?</summary>

SLSA Level 3 requires a **hardened build platform** and **non-falsifiable provenance**. The build platform is isolated so that individual builds cannot influence each other or tamper with the build process. Provenance is generated by the build platform itself (not by the build script), and it is cryptographically signed in a way that the build script cannot forge. If an attacker compromises a CI/CD worker (e.g., injects malicious code into a build), the provenance will either: (1) accurately reflect that the build used a modified source (because provenance is generated independently of the build script), or (2) be absent (if the attacker tries to skip provenance generation, the admission webhook rejects the artifact). The key insight is that at SLSA 3, provenance is a property of the build platform, not of the build. The build cannot lie about its own origin.
</details>

<details>
<summary>Question 4: Your company wants to remove the corporate VPN and adopt Zero Trust. What is the migration plan? What should be deployed first?</summary>

Migration plan: (1) **First: Deploy identity foundation** -- ensure all employees use SSO with MFA, all devices are enrolled in MDM, and all Kubernetes service accounts use SPIFFE or workload identity. (2) **Second: Deploy Identity-Aware Proxy** (Pomerium, Teleport, or cloud-native IAP) in parallel with the VPN. Route a subset of applications through the IAP while the VPN remains available. (3) **Third: Migrate applications incrementally** -- start with low-risk internal tools (Grafana, Backstage), then move to development cluster access, then staging, then production. (4) **Fourth: Implement micro-segmentation** -- deploy default-deny Network Policies and service mesh AuthorizationPolicies. (5) **Fifth: Decommission VPN** -- after 3-6 months of parallel operation, with all access patterns migrated, shut down the VPN. Throughout: monitor access patterns, gather feedback from developers, and maintain an exception process for edge cases. The most common failure mode is rushing step 5 -- decommissioning the VPN before all legitimate access patterns are covered by the IAP.
</details>

<details>
<summary>Question 5: What is the relationship between Kubernetes Network Policies and Istio Authorization Policies? Do you need both?</summary>

**Network Policies** operate at **Layer 3/4** (IP addresses and ports). They control which pods can establish TCP/UDP connections to which other pods. They are enforced by the CNI plugin and work without a service mesh. **Istio Authorization Policies** operate at **Layer 7** (HTTP methods, paths, headers, service identities). They control what requests are allowed within an established connection. They require the Istio sidecar proxy.

**You need both** for defense in depth. Network Policies prevent unauthorized network connections from being established at all -- even if Istio is misconfigured or the sidecar is bypassed. Istio Authorization Policies provide fine-grained control that Network Policies cannot: allowing GET but denying DELETE, or allowing /api/v1/payments but denying /api/v1/admin. Network Policies are the coarse guard at the door; Istio policies are the fine-grained access control inside the room.
</details>

<details>
<summary>Question 6: An engineer argues that mTLS in Istio makes Network Policies unnecessary because "mTLS already verifies identity." Why is this wrong?</summary>

mTLS verifies the **identity** of the communicating parties (via SPIFFE certificates) and **encrypts** the traffic. But it does not **restrict** which communications can happen. By default, Istio's mTLS allows any service with a valid mesh certificate to communicate with any other service. mTLS ensures that the caller is who they claim to be; it does not ensure the caller is authorized for that specific action. You still need: (1) **AuthorizationPolicies** to restrict which identities can call which services (Layer 7). (2) **Network Policies** as a backup in case the Istio sidecar is bypassed (e.g., host-networked pods, init containers that run before the sidecar, or pods without the sidecar injected). mTLS is an authentication mechanism, not an authorization mechanism. Confusing the two is a common and dangerous mistake.
</details>

---

## Hands-On Exercise: Implement Zero Trust Micro-Segmentation

In this exercise, you will implement a multi-layered Zero Trust architecture in a kind cluster with Network Policies, RBAC, and simulated identity-aware access.

### Task 1: Create the Zero Trust Lab Cluster

<details>
<summary>Solution</summary>

```bash
# Create a cluster with Calico CNI for Network Policy enforcement
cat <<'EOF' > /tmp/zero-trust-cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: zero-trust-lab
networking:
  disableDefaultCNI: true
  podSubnet: 192.168.0.0/16
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

kind create cluster --config /tmp/zero-trust-cluster.yaml

# Install Calico for Network Policy enforcement
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml

# Wait for Calico to be ready
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n kube-system --timeout=120s
kubectl wait --for=condition=ready pod -l k8s-app=calico-kube-controllers -n kube-system --timeout=120s

echo "Cluster ready with Calico CNI (Network Policy support enabled)"
```

</details>

### Task 2: Deploy a Multi-Service Application

<details>
<summary>Solution</summary>

```bash
# Create namespaces
kubectl create namespace payments
kubectl create namespace monitoring

# Deploy a 3-tier application
cat <<'EOF' | kubectl apply -f -
# Frontend
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: payments
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: frontend
    spec:
      containers:
        - name: frontend
          image: nginx:1.27.3
          ports:
            - containerPort: 80
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: payments
spec:
  selector:
    app: frontend
  ports:
    - port: 80
---
# Backend API
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: payments
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        tier: backend
    spec:
      containers:
        - name: backend
          image: nginx:1.27.3
          ports:
            - containerPort: 80
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: payments
spec:
  selector:
    app: backend
  ports:
    - port: 80
---
# Database
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  namespace: payments
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
        tier: database
    spec:
      containers:
        - name: database
          image: nginx:1.27.3
          ports:
            - containerPort: 80
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: payments
spec:
  selector:
    app: database
  ports:
    - port: 80
EOF

kubectl wait --for=condition=ready pod -l app=frontend -n payments --timeout=60s
kubectl wait --for=condition=ready pod -l app=backend -n payments --timeout=60s
kubectl wait --for=condition=ready pod -l app=database -n payments --timeout=60s
```

</details>

### Task 3: Verify Flat Network (Before Zero Trust)

<details>
<summary>Solution</summary>

```bash
echo "=== BEFORE ZERO TRUST: Flat Network ==="
echo ""
echo "Test: Frontend → Backend (should succeed - legitimate)"
kubectl exec -n payments deploy/frontend -- curl -s --max-time 3 backend.payments.svc.cluster.local || echo "FAILED"

echo ""
echo "Test: Frontend → Database (should succeed - PROBLEM: frontend should not access DB directly)"
kubectl exec -n payments deploy/frontend -- curl -s --max-time 3 database.payments.svc.cluster.local || echo "FAILED"

echo ""
echo "Test: Database → Frontend (should succeed - PROBLEM: DB should not call frontend)"
kubectl exec -n payments deploy/database -- curl -s --max-time 3 frontend.payments.svc.cluster.local || echo "FAILED"

echo ""
echo "CONCLUSION: Without Network Policies, every pod can talk to every other pod."
echo "This is the 'soft interior' problem of perimeter security."
```

</details>

### Task 4: Apply Zero Trust Network Policies

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | kubectl apply -f -
# Step 1: Default deny ALL traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: payments
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
# Step 2: Allow DNS for all pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: payments
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
---
# Step 3: Frontend can receive from outside and send to backend only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-policy
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - {}  # Accept from any source (simulates ingress controller)
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: backend
      ports:
        - port: 80
    - ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
---
# Step 4: Backend accepts from frontend, can reach database only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - port: 80
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - port: 80
    - ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
---
# Step 5: Database accepts from backend only, no egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-policy
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: backend
      ports:
        - port: 80
  egress:
    - ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
EOF

echo "Network Policies applied:"
kubectl get networkpolicy -n payments
```

</details>

### Task 5: Verify Zero Trust Enforcement

<details>
<summary>Solution</summary>

```bash
echo "=== AFTER ZERO TRUST: Micro-Segmented Network ==="
echo ""

echo "Test 1: Frontend → Backend (SHOULD PASS - legitimate path)"
kubectl exec -n payments deploy/frontend -- curl -s --max-time 3 backend.payments.svc.cluster.local && echo "PASS" || echo "BLOCKED"

echo ""
echo "Test 2: Frontend → Database (SHOULD BLOCK - frontend must go through backend)"
kubectl exec -n payments deploy/frontend -- curl -s --max-time 3 database.payments.svc.cluster.local 2>&1 && echo "PASS (BAD!)" || echo "BLOCKED (GOOD!)"

echo ""
echo "Test 3: Backend → Database (SHOULD PASS - legitimate path)"
kubectl exec -n payments deploy/backend -- curl -s --max-time 3 database.payments.svc.cluster.local && echo "PASS" || echo "BLOCKED"

echo ""
echo "Test 4: Database → Frontend (SHOULD BLOCK - DB should not initiate connections)"
kubectl exec -n payments deploy/database -- curl -s --max-time 3 frontend.payments.svc.cluster.local 2>&1 && echo "PASS (BAD!)" || echo "BLOCKED (GOOD!)"

echo ""
echo "Test 5: Database → external internet (SHOULD BLOCK - DB must not reach internet)"
kubectl exec -n payments deploy/database -- curl -s --max-time 3 https://example.com 2>&1 && echo "PASS (BAD!)" || echo "BLOCKED (GOOD!)"

echo ""
echo "CONCLUSION: Only legitimate communication paths are allowed."
echo "Lateral movement is prevented. The blast radius of a compromise is contained."
```

</details>

### Clean Up

```bash
kind delete cluster --name zero-trust-lab
rm /tmp/zero-trust-cluster.yaml
```

### Success Criteria

- [ ] I deployed a multi-tier application in a flat network and verified unrestricted access
- [ ] I applied default-deny Network Policies to enforce Zero Trust
- [ ] I verified that only legitimate communication paths (frontend->backend->database) work
- [ ] I confirmed that unauthorized paths (frontend->database, database->frontend) are blocked
- [ ] I can explain the four layers of micro-segmentation
- [ ] I can describe how an Identity-Aware Proxy replaces a VPN
- [ ] I can explain how SLSA protects the CI/CD supply chain

---

## Next Module

With Zero Trust securing your infrastructure, it is time to optimize costs at enterprise scale. Head to [Module 10.10: FinOps at Enterprise Scale](../module-10.10-enterprise-finops/) to learn cloud economics, Enterprise Discount Programs, forecasting, chargeback models for shared clusters, and the true cost of multi-cloud operations.
