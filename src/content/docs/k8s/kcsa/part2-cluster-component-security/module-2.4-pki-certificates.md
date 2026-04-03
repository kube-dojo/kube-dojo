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

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the Kubernetes PKI architecture and which certificates each component requires
2. **Assess** certificate security risks: expired certs, weak key sizes, and missing rotation
3. **Evaluate** certificate-based authentication flows between API server, kubelet, and etcd
4. **Identify** common PKI misconfigurations that lead to authentication failures or security gaps

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

> **Stop and think**: If the cluster CA private key is compromised, the attacker can generate certificates for any identity. Kubernetes has no built-in certificate revocation. How would you respond to a CA key compromise?

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

> **Pause and predict**: A new node needs a certificate to communicate with the API server, but it can't authenticate without a certificate. How does Kubernetes solve this chicken-and-egg problem?

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

1. **A certificate with CN=system:node:worker-5 and O=system:nodes expires at midnight. The kubelet on worker-5 has certificate rotation disabled. What symptoms will the cluster exhibit after midnight, and what's the blast radius?**
   <details>
   <summary>Answer</summary>
   After expiry, worker-5's kubelet cannot authenticate to the API server — TLS handshakes fail. Symptoms: pods scheduled on worker-5 continue running but become "orphaned" (no status updates), new pods won't be scheduled to that node, and the node enters NotReady status. Existing pods keep serving traffic but can't be managed (no exec, no log streaming, no deletion by the control plane). The blast radius is limited to worker-5 — other nodes are unaffected. Fix: manually renew the certificate (`kubeadm certs renew`) or enable `rotateCertificates: true` in kubelet config to prevent future occurrences. This is why certificate lifecycle monitoring is critical.
   </details>

2. **A security audit discovers that multiple clusters in your organization share the same cluster CA. The auditor flags this as a finding. Explain why sharing CAs across clusters is a security risk.**
   <details>
   <summary>Answer</summary>
   If clusters share a CA, a certificate signed for one cluster is valid in all clusters sharing that CA. A compromised certificate from cluster-dev (e.g., a developer's kubeconfig) could authenticate to cluster-prod because the API server trusts the same CA. This violates the principle of blast radius minimization — a breach in one cluster's PKI compromises all clusters. Each cluster should have its own independent CA so that certificates are only valid within their intended cluster. This is especially critical because Kubernetes lacks certificate revocation — a compromised cert remains valid until expiry.
   </details>

3. **Your cluster still has legacy ServiceAccount tokens (stored as Secrets, never expiring) from before the Kubernetes 1.24 upgrade. A security scan flags 200+ such tokens. What risk do they pose, and what's your remediation plan?**
   <details>
   <summary>Answer</summary>
   Legacy tokens are dangerous because they never expire, are not audience-bound (can be used against any service), and persist even after the pod that used them is deleted. If any legacy token is leaked (through logs, etcd access, or RBAC over-permission), the attacker has permanent API access until the token Secret is manually deleted. Remediation: identify all legacy token Secrets (`kubectl get secrets --field-selector type=kubernetes.io/service-account-token`), verify no running workloads depend on them (check volume mounts), delete the Secrets, and ensure all pods use bound service account tokens (projected volumes) which are time-limited, audience-bound, and auto-rotated.
   </details>

4. **An engineer creates a certificate signing request (CSR) with O=system:masters. Explain why approving this CSR is equivalent to granting cluster-admin access and what safeguards should exist.**
   <details>
   <summary>Answer</summary>
   The O (Organization) field in X.509 certificates maps to Kubernetes groups. The system:masters group is bound to the cluster-admin ClusterRole by default — any certificate with this group grants unrestricted access to all resources in all namespaces. Approving this CSR creates a permanent cluster-admin credential that's valid until the certificate expires (typically 1 year). Safeguards: restrict who can approve CSRs via RBAC (the `certificatesigningrequests/approval` subresource), implement manual review for any CSR containing system:masters, use short validity periods, and audit all approved CSRs. Most users should use group memberships that map to appropriately scoped roles, not system:masters.
   </details>

5. **Kubernetes cannot revoke certificates once signed. Given this limitation, what strategies can you use to minimize the damage if a client certificate is compromised?**
   <details>
   <summary>Answer</summary>
   Since there's no CRL or OCSP in Kubernetes, strategies include: (1) use short-lived certificates — shorter validity means the compromise window is smaller; (2) enable kubelet certificate rotation so node certs are frequently replaced; (3) for human users, prefer OIDC authentication over certificates — OIDC tokens are short-lived and can be revoked at the identity provider; (4) if a certificate is compromised, you can remove the user's RBAC bindings to deny authorization even though authentication succeeds; (5) rotate the cluster CA as a last resort — this invalidates ALL certificates but requires re-issuing every component certificate and is highly disruptive.
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
