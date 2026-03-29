---
title: "Module 2.4: PKI and Certificates"
slug: k8s/kcsa/part2-cluster-component-security/module-2.4-pki-certificates
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 2.3: Network Security](../module-2.3-network-security/)

---

## Why This Module Matters

Kubernetes relies heavily on TLS certificates for authentication and encryption. Every component—API server, kubelet, etcd—uses certificates to prove its identity and encrypt communications. Understanding Kubernetes PKI helps you troubleshoot authentication issues and assess cluster security.

Certificate mismanagement is a common source of both security vulnerabilities and operational problems.

---

## Kubernetes PKI Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES PKI                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                      CLUSTER CA                             │
│                          │                                  │
│            ┌─────────────┼─────────────┐                   │
│            │             │             │                    │
│            ▼             ▼             ▼                    │
│      ┌─────────┐   ┌─────────┐   ┌─────────┐              │
│      │ API     │   │ etcd    │   │ Front   │              │
│      │ Server  │   │ CA      │   │ Proxy   │              │
│      │ cert    │   │         │   │ CA      │              │
│      └─────────┘   └─────────┘   └─────────┘              │
│            │                                                │
│            ├── kubelet client certs                        │
│            ├── controller-manager client cert              │
│            ├── scheduler client cert                       │
│            └── admin/user client certs                     │
│                                                             │
│  SEPARATE CAs:                                             │
│  • Cluster CA - signs most certificates                    │
│  • etcd CA - can be separate for isolation                 │
│  • Front Proxy CA - for aggregation layer                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Certificate Types in Kubernetes

### Server Certificates

Prove the identity of servers (components others connect to):

| Component | Certificate Purpose |
|-----------|-------------------|
| API Server | Proves identity to clients |
| etcd | Proves identity to API server |
| Kubelet | Proves identity for its server API |

### Client Certificates

Prove identity when connecting to servers:

| Client | Connects To | CN (Common Name) | O (Organization/Groups) |
|--------|-------------|------------------|------------------------|
| kubelet | API Server | system:node:nodename | system:nodes |
| controller-manager | API Server | system:kube-controller-manager | |
| scheduler | API Server | system:kube-scheduler | |
| admin | API Server | kubernetes-admin | system:masters |

### The CN and O Fields

Certificate fields map to Kubernetes identity:

```
┌─────────────────────────────────────────────────────────────┐
│              CERTIFICATE → KUBERNETES IDENTITY              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  X.509 CERTIFICATE                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Subject:                                           │   │
│  │    CN = system:node:worker-1                        │   │
│  │    O  = system:nodes                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│  KUBERNETES IDENTITY                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Username: system:node:worker-1                     │   │
│  │  Groups:   ["system:nodes"]                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  CN (Common Name) → Kubernetes username                    │
│  O  (Organization) → Kubernetes groups (can have multiple) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Certificate Generation

### Cluster CA

The cluster CA is the root of trust:

```
┌─────────────────────────────────────────────────────────────┐
│              CLUSTER CA                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LOCATION (kubeadm clusters):                              │
│  • /etc/kubernetes/pki/ca.crt (public certificate)         │
│  • /etc/kubernetes/pki/ca.key (private key - PROTECT!)     │
│                                                             │
│  CA COMPROMISE = CLUSTER COMPROMISE                        │
│  If the CA private key is stolen:                          │
│  • Attacker can generate any certificate                   │
│  • Can impersonate any user, node, or component            │
│  • Full cluster access                                     │
│                                                             │
│  PROTECT THE CA KEY:                                       │
│  • Restrict file permissions (600)                         │
│  • Restrict access to control plane nodes                  │
│  • Consider HSM for production                             │
│  • Audit any access                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### kubeadm Certificate Locations

```
/etc/kubernetes/pki/
├── ca.crt, ca.key                    # Cluster CA
├── apiserver.crt, apiserver.key      # API Server
├── apiserver-kubelet-client.crt/key  # API → kubelet
├── front-proxy-ca.crt/key            # Aggregation layer CA
├── front-proxy-client.crt/key        # Aggregation client
├── etcd/
│   ├── ca.crt, ca.key                # etcd CA
│   ├── server.crt, server.key        # etcd server
│   ├── peer.crt, peer.key            # etcd peer communication
│   └── healthcheck-client.crt/key    # Health check client
└── sa.key, sa.pub                    # ServiceAccount signing
```

---

## Certificate Lifecycle

### Expiration

Certificates expire—this is a security feature but requires management:

```
┌─────────────────────────────────────────────────────────────┐
│              CERTIFICATE EXPIRATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TYPICAL VALIDITY PERIODS:                                 │
│  • Cluster CA: 10 years (kubeadm default)                  │
│  • Component certs: 1 year (kubeadm default)               │
│  • kubelet client certs: 1 year                            │
│                                                             │
│  WHEN CERTIFICATES EXPIRE:                                 │
│  • Component can't authenticate                            │
│  • TLS connections fail                                    │
│  • Cluster operations break                                │
│                                                             │
│  CERTIFICATE ROTATION:                                     │
│  • Automatic: kubelet auto-rotation (if enabled)           │
│  • Manual: kubeadm certs renew                            │
│  • Managed K8s: Provider handles it                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Checking Certificate Expiration

```bash
# kubeadm clusters
kubeadm certs check-expiration

# Manual check with openssl
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -dates
```

---

## Service Account Tokens

Service accounts use a different mechanism than certificates:

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE ACCOUNT TOKENS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LEGACY TOKENS (pre-1.24)                                  │
│  • Stored in Secrets                                       │
│  • Never expire                                            │
│  • Mounted to all pods automatically                       │
│  • Security risk!                                          │
│                                                             │
│  BOUND SERVICE ACCOUNT TOKENS (1.24+)                      │
│  • JWTs signed by API server                               │
│  • Time-limited (default 1 hour)                           │
│  • Audience-bound                                          │
│  • Automatically rotated                                   │
│  • Projected into pods via volume                          │
│                                                             │
│  TOKEN PROJECTION EXAMPLE:                                 │
│  ┌───────────────────────────────────────────────────┐    │
│  │  volumes:                                         │    │
│  │  - name: token                                    │    │
│  │    projected:                                     │    │
│  │      sources:                                     │    │
│  │      - serviceAccountToken:                       │    │
│  │          expirationSeconds: 3600                  │    │
│  │          audience: api                            │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Bound Token Benefits

| Legacy Tokens | Bound Tokens |
|--------------|--------------|
| Never expire | Time-limited |
| Any audience | Audience-bound |
| Stored in Secret | Projected volume |
| Manual rotation | Auto-rotation |
| Persist after pod deletion | Invalidated with pod |

---

## TLS Bootstrap

How new nodes join the cluster securely:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBELET TLS BOOTSTRAP                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROBLEM: New node needs certificate to talk to API server │
│           But how does it get the certificate?             │
│                                                             │
│  SOLUTION: Bootstrap tokens                                │
│                                                             │
│  1. Node starts with bootstrap token                       │
│     (limited permissions, short-lived)                     │
│                                                             │
│  2. Node connects to API server                            │
│     ├── Authenticates with bootstrap token                 │
│     └── Requests certificate signing (CSR)                 │
│                                                             │
│  3. CSR approved (auto or manual)                          │
│     └── API server signs certificate                       │
│                                                             │
│  4. Node receives signed certificate                       │
│     └── Uses cert for all future communication            │
│                                                             │
│  5. Kubelet auto-rotates certificate before expiry         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### CSR Approval

Certificate Signing Requests can be approved:
- **Automatically**: By csrapproving controller
- **Manually**: By admin via `kubectl certificate approve`

```
┌─────────────────────────────────────────────────────────────┐
│              CSR SECURITY CONSIDERATIONS                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTO-APPROVAL RISKS:                                      │
│  • If bootstrap token is compromised, attacker can get     │
│    valid node certificate                                  │
│  • Rogue node could join cluster                           │
│                                                             │
│  MITIGATIONS:                                              │
│  • Short-lived bootstrap tokens                            │
│  • Node authorization mode limits what node certs can do   │
│  • Network controls on who can reach API server            │
│  • Monitor for unexpected CSRs                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Certificate Security Best Practices

```
┌─────────────────────────────────────────────────────────────┐
│              CERTIFICATE SECURITY CHECKLIST                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROTECT PRIVATE KEYS                                      │
│  ☐ CA key has restricted permissions (600)                 │
│  ☐ CA key accessible only to necessary processes           │
│  ☐ Consider HSM for CA key in production                   │
│                                                             │
│  MANAGE EXPIRATION                                         │
│  ☐ Monitor certificate expiration dates                    │
│  ☐ Enable kubelet certificate rotation                     │
│  ☐ Plan for CA rotation before expiry                      │
│                                                             │
│  MINIMIZE TRUST                                            │
│  ☐ Use separate CA for etcd (optional)                     │
│  ☐ Don't share CA across clusters                          │
│  ☐ Revoke compromised certificates                         │
│                                                             │
│  USE SHORT-LIVED CREDENTIALS                               │
│  ☐ Bound service account tokens                            │
│  ☐ Short-lived user certificates where possible            │
│  ☐ Rotate credentials regularly                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Kubernetes can't revoke certificates** - there's no built-in CRL or OCSP. A compromised certificate is valid until it expires. This is why short-lived certificates matter.

- **The system:masters group** grants cluster-admin access. Any certificate with `O=system:masters` has full cluster control. Guard this carefully.

- **Service account token projection** was introduced to fix the long-standing security issue of non-expiring tokens stored in Secrets.

- **In managed Kubernetes**, you typically never see the CA private key. The provider manages PKI, which is actually more secure for most organizations.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| CA key accessible to many | Full cluster compromise if leaked | Restrict to minimal access |
| Ignoring cert expiration | Cluster stops working | Monitor and rotate proactively |
| Using O=system:masters freely | Too many full admins | Use appropriate groups |
| Legacy service account tokens | Never expire, persist after pod deletion | Use bound tokens (1.24+) |
| Same CA across clusters | Compromise affects all clusters | Separate CAs per cluster |

---

## Quiz

1. **What happens when a certificate's CN is set to "system:node:worker-1" and O is set to "system:nodes"?**
   <details>
   <summary>Answer</summary>
   The certificate authenticates as username "system:node:worker-1" in the group "system:nodes". This is the standard identity format for kubelet certificates.
   </details>

2. **Why can't Kubernetes revoke certificates?**
   <details>
   <summary>Answer</summary>
   Kubernetes has no built-in Certificate Revocation List (CRL) or OCSP support. Once a certificate is signed, it remains valid until expiration. This is why short-lived certificates and certificate rotation are important.
   </details>

3. **What is the purpose of TLS bootstrap?**
   <details>
   <summary>Answer</summary>
   TLS bootstrap allows new nodes to securely join the cluster. The node uses a bootstrap token to request a certificate signing, and once approved, receives a proper certificate for ongoing API server communication.
   </details>

4. **What's the key difference between legacy service account tokens and bound tokens?**
   <details>
   <summary>Answer</summary>
   Legacy tokens never expire and are stored in Secrets. Bound tokens are time-limited (typically 1 hour), audience-bound, and projected into pods via volumes. Bound tokens are more secure.
   </details>

5. **What group grants full cluster-admin access via certificate authentication?**
   <details>
   <summary>Answer</summary>
   system:masters. Any certificate with O=system:masters in the subject has full administrative access to the cluster.
   </details>

---

## Hands-On Exercise: Certificate Analysis

**Scenario**: Analyze this certificate output and answer the questions:

```
Certificate:
    Subject: CN = system:kube-controller-manager
    Issuer: CN = kubernetes
    Validity
        Not Before: Jan  1 00:00:00 2024 GMT
        Not After : Jan  1 00:00:00 2025 GMT
    Subject Public Key Info:
        Public Key Algorithm: rsaEncryption
```

**Questions:**

1. What Kubernetes username will this certificate authenticate as?
2. What groups will this user be in?
3. When does this certificate expire?
4. What issued this certificate?

<details>
<summary>Answers</summary>

1. **Username**: `system:kube-controller-manager` (from CN field)

2. **Groups**: None from the certificate itself (no O field). The user may have additional group memberships via RBAC but the certificate doesn't grant any groups.

3. **Expiration**: January 1, 2025 (Not After field)

4. **Issuer**: The cluster CA (CN = kubernetes is the default kubeadm CA name)

</details>

---

## Summary

Kubernetes PKI is foundational to cluster security:

| Concept | Key Points |
|---------|------------|
| **Cluster CA** | Root of trust - protect the private key |
| **Certificate Identity** | CN = username, O = groups |
| **Expiration** | Certificates expire - monitor and rotate |
| **Service Account Tokens** | Use bound tokens (1.24+) for better security |
| **TLS Bootstrap** | Secure way for new nodes to join |

Key security practices:
- Protect CA private keys
- Monitor certificate expiration
- Enable kubelet certificate rotation
- Use bound service account tokens
- Don't share CAs across clusters

---

## Next Module

[Module 3.1: Pod Security](../part3-security-fundamentals/module-3.1-pod-security/) - SecurityContext, Pod Security Standards, and container-level security.
