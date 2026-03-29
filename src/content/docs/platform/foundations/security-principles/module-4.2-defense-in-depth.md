---
title: "Module 4.2: Defense in Depth"
slug: platform/foundations/security-principles/module-4.2-defense-in-depth
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: [Module 4.1: Security Mindset](../module-4.1-security-mindset/)
>
> **Track**: Foundations

---

**November 2013. The holiday shopping season begins at Target, America's second-largest discount retailer.**

Attackers have already been inside Target's network for over two weeks. They entered through a third-party HVAC vendor's compromised credentials, moved laterally through the network, and installed memory-scraping malware on point-of-sale systems across 1,797 stores.

For 19 days, the malware quietly captured credit card data as customers swiped their cards. Target's security team received alerts from their FireEye intrusion detection system. The alerts were ignored.

**By December 15th, attackers had exfiltrated 40 million credit card numbers and 70 million customer records.** Target's stock dropped 46% in the following months. The breach cost over $292 million in direct expenses. The CEO and CIO both resigned.

Target had security tools—firewalls, network segmentation, intrusion detection. But the layers weren't truly independent. Credentials from one system worked in others. Alerts weren't investigated. Network segments could reach each other. Each slice of Swiss cheese had holes, and the holes aligned perfectly.

This module teaches defense in depth—how to layer security controls so that when one fails (and it will), others still protect the system.

---

## Why This Module Matters

No security control is perfect. Firewalls get misconfigured. Authentication gets bypassed. Encryption keys get leaked. Any single layer of security will eventually fail.

**Defense in depth** is the practice of layering multiple independent security controls so that when one fails, others still protect the system. It's the difference between a house with just a locked front door and one with a locked door, alarm system, security cameras, and a safe for valuables.

This module teaches you how to design layered security—what layers exist, how they work together, and how to avoid common pitfalls that undermine defense in depth.

> **The Swiss Cheese Analogy**
>
> Imagine slices of Swiss cheese stacked together. Each slice has holes (vulnerabilities), but the holes are in different places. For an attack to succeed, the holes must align across all slices. Defense in depth means adding more slices—more layers with different vulnerabilities—so alignment becomes statistically unlikely.

---

## What You'll Learn

- The layers of defense in a modern system
- How to design independent security controls
- Network, application, and data layer security
- Common mistakes that undermine layered defense
- How Kubernetes implements defense in depth

---

## Part 1: The Security Layers

### 1.1 The Defense Stack

```
DEFENSE IN DEPTH LAYERS
═══════════════════════════════════════════════════════════════

                    ┌─────────────────────────┐
                    │    PHYSICAL SECURITY    │  Datacenter access, locks
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │    NETWORK SECURITY     │  Firewalls, segmentation
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │    HOST SECURITY        │  OS hardening, patching
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   APPLICATION SECURITY  │  Auth, input validation
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │     DATA SECURITY       │  Encryption, access control
                    └─────────────────────────┘

Each layer assumes the layer above it might be compromised.
```

### 1.2 Layer Independence

For defense in depth to work, layers must be **independent**:

```
LAYER INDEPENDENCE
═══════════════════════════════════════════════════════════════

DEPENDENT (weak)
─────────────────────────────────────────────────────────────
Firewall credentials → Same password as app admin
App server compromise → Attacker gets firewall access too

One compromise defeats multiple layers.

INDEPENDENT (strong)
─────────────────────────────────────────────────────────────
Firewall credentials → Hardware token + unique password
App credentials → Different identity provider
Database credentials → Rotated automatically, not known to app

Each layer has its own authentication, its own keys,
its own failure modes.
```

> **Try This (2 minutes)**
>
> Think about your system. Do you reuse:
> - Passwords across security boundaries?
> - SSH keys for multiple purposes?
> - Service accounts with broad access?
>
> Each reuse is a hidden dependency between security layers.

---

## Part 2: Network Security Layer

### 2.1 Network Segmentation

```
NETWORK SEGMENTATION
═══════════════════════════════════════════════════════════════

FLAT NETWORK (dangerous)
┌─────────────────────────────────────────────────────────────┐
│                       One Network                           │
│                                                             │
│  Web ◀──▶ App ◀──▶ DB ◀──▶ Admin ◀──▶ Dev ◀──▶ IoT       │
│                                                             │
│  Attacker compromises one device, can reach everything.    │
└─────────────────────────────────────────────────────────────┘

SEGMENTED NETWORK (defense in depth)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │    DMZ      │    │   App Tier  │    │   Data Tier │    │
│  │             │    │             │    │             │    │
│  │  [Web/LB]   │───▶│  [App Srv]  │───▶│    [DB]     │    │
│  │             │    │             │    │             │    │
│  │ Internet OK │    │ DMZ only    │    │ App only    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│        │                                                    │
│        X (blocked)──────────────────────────────────────▶  │
│                                                             │
│  Attacker in DMZ can't reach database directly.            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Firewall Rules

```
FIREWALL STRATEGY
═══════════════════════════════════════════════════════════════

DEFAULT DENY
─────────────────────────────────────────────────────────────
- Block everything by default
- Explicitly allow only what's needed
- Log blocked traffic (anomaly detection)

Rule: ALLOW TCP 443 from Internet to Web-Tier
Rule: ALLOW TCP 8080 from Web-Tier to App-Tier
Rule: ALLOW TCP 5432 from App-Tier to DB-Tier
Rule: DENY ALL (default)

COMMON MISTAKES
─────────────────────────────────────────────────────────────
✗ ALLOW ALL from Internal  → Flat network, defeats segmentation
✗ ALLOW TCP 0-65535       → Overly permissive port ranges
✗ Old rules never cleaned  → Accumulated holes
✗ No logging               → Attacks go unnoticed
```

### 2.3 Zero Trust Networking

```
ZERO TRUST NETWORK
═══════════════════════════════════════════════════════════════

Traditional perimeter:
    "Inside the network = trusted"

Zero trust:
    "Network location grants no trust"

Implementation:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Service A         Service B         Service C            │
│      │                  │                  │                │
│      │                  │                  │                │
│      └────────┬─────────┴────────┬─────────┘                │
│               │                  │                          │
│        [mTLS required]    [mTLS required]                  │
│               │                  │                          │
│       ┌───────▼──────┐   ┌───────▼──────┐                  │
│       │ Service Mesh │   │ Service Mesh │                  │
│       │   (Istio)    │   │   (Linkerd)  │                  │
│       └──────────────┘   └──────────────┘                  │
│                                                             │
│   Every service-to-service call:                           │
│   ✓ Mutually authenticated (both sides prove identity)     │
│   ✓ Encrypted (even on internal network)                   │
│   ✓ Authorized (policy checked per request)                │
│   ✓ Logged (audit trail)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 3: Application Security Layer

### 3.1 Input Validation

```
INPUT VALIDATION
═══════════════════════════════════════════════════════════════

ALL INPUT IS UNTRUSTED
─────────────────────────────────────────────────────────────
Even input from "internal" services—an attacker who compromises
one service shouldn't automatically compromise others.

VALIDATION CHECKLIST
─────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│ 1. TYPE VALIDATION                                          │
│    - Expected data type (string, int, email, UUID)?         │
│    - Does it parse correctly?                               │
│                                                             │
│ 2. LENGTH VALIDATION                                        │
│    - Minimum length (empty string attacks)?                 │
│    - Maximum length (buffer overflow, DoS)?                 │
│                                                             │
│ 3. FORMAT VALIDATION                                        │
│    - Matches expected pattern (regex)?                      │
│    - Valid characters only?                                 │
│                                                             │
│ 4. RANGE VALIDATION                                         │
│    - Within expected bounds (price > 0)?                    │
│    - Valid enum value?                                      │
│                                                             │
│ 5. BUSINESS VALIDATION                                      │
│    - Makes sense in context (quantity can't be negative)?   │
│    - User authorized for this value?                        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Output Encoding

```
OUTPUT ENCODING
═══════════════════════════════════════════════════════════════

Context determines encoding:

HTML CONTEXT
    <div>Hello, {{name}}</div>

    If name = "<script>alert('xss')</script>"
    Encode: &lt;script&gt;alert('xss')&lt;/script&gt;

JAVASCRIPT CONTEXT
    <script>var name = "{{name}}";</script>

    If name = "; alert('xss');//"
    Encode: \x3B\x20alert\x28\x27xss\x27\x29\x3B\x2F\x2F

SQL CONTEXT
    SELECT * FROM users WHERE name = '{{name}}'

    If name = "'; DROP TABLE users;--"
    Use parameterized queries instead!

URL CONTEXT
    <a href="/search?q={{query}}">

    If query = "<script>alert(1)</script>"
    Encode: %3Cscript%3Ealert%281%29%3C%2Fscript%3E

Wrong encoding = vulnerability. Use framework functions.
```

### 3.3 Authentication and Session Management

```
AUTHENTICATION LAYERS
═══════════════════════════════════════════════════════════════

LAYER 1: Something you know
    Password, PIN
    Weakness: Phishing, brute force, credential stuffing

LAYER 2: Something you have
    Phone (SMS, TOTP), hardware key (YubiKey)
    Weakness: SIM swapping, device theft

LAYER 3: Something you are
    Biometrics (fingerprint, face)
    Weakness: Can't be changed if compromised

DEFENSE IN DEPTH FOR AUTH
─────────────────────────────────────────────────────────────
    Password (Layer 1)
         +
    TOTP Code (Layer 2)
         +
    Device Trust (is this a known device?)
         +
    Risk Analysis (unusual location? time? behavior?)
         +
    Session Limits (timeout, single-use tokens)
```

> **War Story: The $8.5 Million Password Reset Hole**
>
> **August 2019.** A financial services startup had invested heavily in authentication security: complex passwords, hardware MFA tokens, device fingerprinting, IP reputation analysis. Their login flow was nearly impenetrable.
>
> A security researcher found the password reset flow. It sent a reset link via email—no MFA required. Email access alone was enough to bypass every layer of authentication protection.
>
> The researcher reported the vulnerability through their bug bounty program. Three weeks later, before the fix deployed, attackers exploited the same flaw. They compromised employee email accounts through phishing, used password reset to gain access to the main application, and exfiltrated customer financial data.
>
> **The breach affected 2.1 million customers and cost $8.5 million** in regulatory fines, customer notification, and credit monitoring services.
>
> They'd built defense in depth for login, but forgot that password reset is also an entry point. The backup authentication path had none of the protections of the primary path. Every authentication flow—login, password reset, account recovery, API authentication—needs the same layered protection.

---

## Part 4: Data Security Layer

### 4.1 Encryption Strategy

```
ENCRYPTION LAYERS
═══════════════════════════════════════════════════════════════

ENCRYPTION IN TRANSIT
─────────────────────────────────────────────────────────────
    Client ──[TLS]──▶ Load Balancer ──[mTLS]──▶ App ──[TLS]──▶ DB

    Protects: Network sniffing, man-in-the-middle
    Doesn't protect: Compromised endpoints

ENCRYPTION AT REST
─────────────────────────────────────────────────────────────
    ┌─────────────────────────────────────────────────────────┐
    │  Disk Volume: Encrypted with volume key                 │
    │  ┌─────────────────────────────────────────────────────┐│
    │  │  Database: Transparent Data Encryption              ││
    │  │  ┌─────────────────────────────────────────────────┐││
    │  │  │  Column: Sensitive fields encrypted separately  │││
    │  │  │  (SSN, credit cards)                            │││
    │  │  └─────────────────────────────────────────────────┘││
    │  └─────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────┘

    Protects: Physical theft, unauthorized disk access
    Doesn't protect: Authorized users, memory access

APPLICATION-LEVEL ENCRYPTION
─────────────────────────────────────────────────────────────
    App encrypts data before storing, decrypts after reading.
    Key never reaches database.

    Protects: Database compromise, DBAs
    Doesn't protect: Compromised application
```

### 4.2 Key Management

```
KEY MANAGEMENT
═══════════════════════════════════════════════════════════════

ANTI-PATTERN: Keys with data
┌─────────────────────────────────────────────────────────────┐
│                     Server                                  │
│                                                             │
│   data.db ←──── encrypted data                             │
│   keys.txt ←─── encryption keys                            │
│                                                             │
│   Attacker gets server = Attacker gets everything          │
└─────────────────────────────────────────────────────────────┘

PATTERN: Separate key management
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌──────────────────┐         ┌──────────────────┐       │
│   │    App Server    │         │   Key Vault      │       │
│   │                  │         │   (HashiCorp,    │       │
│   │   [encrypted     │◀──────▶ │    AWS KMS)      │       │
│   │    data]         │  fetch  │                  │       │
│   │                  │   key   │   [keys]         │       │
│   └──────────────────┘         └──────────────────┘       │
│                                        │                   │
│                                   Separate access          │
│                                   controls, audit          │
│                                                             │
│   Attacker gets app server ≠ Attacker gets keys           │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Data Classification

| Classification | Examples | Protection Level |
|----------------|----------|------------------|
| **Public** | Marketing content | Basic integrity |
| **Internal** | Employee directory | Access control |
| **Confidential** | Customer data, financials | Encryption + access control |
| **Restricted** | PII, payment data, secrets | Encryption + strict access + audit |

> **Try This (3 minutes)**
>
> Classify data in your system:
>
> | Data Type | Classification | Current Protection | Gap? |
> |-----------|----------------|-------------------|------|
> | User emails | | | |
> | Passwords | | | |
> | API keys | | | |
> | Log files | | | |

---

## Part 5: Defense in Depth in Kubernetes

### 5.1 Kubernetes Security Layers

```
KUBERNETES DEFENSE IN DEPTH
═══════════════════════════════════════════════════════════════

CLUSTER LAYER
┌─────────────────────────────────────────────────────────────┐
│  - API Server authentication (certificates, OIDC)          │
│  - RBAC for cluster operations                              │
│  - Network policies                                         │
│  - Pod Security Standards                                   │
│  - Secrets encryption at rest                               │
└─────────────────────────────────────────────────────────────┘
                              │
NAMESPACE LAYER               │
┌─────────────────────────────▼───────────────────────────────┐
│  - Namespace isolation                                      │
│  - Resource quotas                                          │
│  - Network policies (namespace-scoped)                      │
│  - ServiceAccount per namespace                             │
└─────────────────────────────────────────────────────────────┘
                              │
POD LAYER                     │
┌─────────────────────────────▼───────────────────────────────┐
│  - SecurityContext (non-root, read-only FS)                │
│  - Resource limits                                          │
│  - ServiceAccount with minimal permissions                  │
│  - No privileged containers                                 │
└─────────────────────────────────────────────────────────────┘
                              │
CONTAINER LAYER               │
┌─────────────────────────────▼───────────────────────────────┐
│  - Minimal base images (distroless, scratch)               │
│  - No unnecessary packages                                  │
│  - Image scanning                                           │
│  - Read-only root filesystem                                │
└─────────────────────────────────────────────────────────────┘
                              │
APPLICATION LAYER             │
┌─────────────────────────────▼───────────────────────────────┐
│  - Input validation                                         │
│  - Authentication/authorization                             │
│  - Secrets from vault (not env vars)                       │
│  - Least privilege database access                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Kubernetes Security Controls

```yaml
# Pod with defense in depth
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  serviceAccountName: app-minimal    # Least privilege
  securityContext:
    runAsNonRoot: true               # Not root
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: myapp:v1.0@sha256:abc...  # Image pinning
    securityContext:
      allowPrivilegeEscalation: false  # Can't become root
      readOnlyRootFilesystem: true     # Can't write to disk
      capabilities:
        drop: ["ALL"]                   # No special capabilities
    resources:
      limits:
        cpu: "500m"
        memory: "256Mi"              # Resource limits (DoS protection)
    volumeMounts:
    - name: tmp
      mountPath: /tmp                # Writable tmp if needed
  volumes:
  - name: tmp
    emptyDir: {}
```

### 5.3 Network Policies

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}      # All pods in namespace
  policyTypes:
  - Ingress

---
# Allow only specific traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
    ports:
    - protocol: TCP
      port: 8080
```

---

## Did You Know?

- **The "Swiss Cheese Model"** was developed by James Reason for accident causation analysis. It shows how multiple barriers, each with weaknesses, can prevent disasters when properly layered.

- **mTLS (mutual TLS)** was rare before service meshes. Now Istio and Linkerd make it the default for all service-to-service communication—encryption and authentication without application changes.

- **The Pentagon uses "air gaps"** (physically disconnected networks) for the most sensitive systems. Even sophisticated software-based defense in depth can't match physical isolation for high-value targets.

- **The 2013 Target breach** is a textbook defense-in-depth failure. Attackers compromised an HVAC vendor, used those credentials to access Target's network, then moved laterally to payment systems. Multiple security layers existed but were either misconfigured or ignored alerts—the intrusion detection system flagged the attack, but the alert wasn't investigated.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Single layer dependency | One compromise defeats everything | Independent controls per layer |
| Perimeter-only defense | Insiders and lateral movement | Zero trust, internal segmentation |
| Encrypted but keys exposed | Encryption provides no protection | Proper key management |
| Network security only | App vulnerabilities still exploitable | Application-layer controls too |
| Default allow policies | Too permissive | Default deny, explicit allow |
| Forgetting logging | Can't detect when layers fail | Log at every layer |

---

## Quiz

1. **Why must security layers be independent?**
   <details>
   <summary>Answer</summary>

   If layers share dependencies (credentials, keys, infrastructure), compromising one dependency compromises all layers simultaneously.

   Example of bad independence:
   - Firewall admin password: "Summer2024!"
   - App admin password: "Summer2024!"
   - Attacker gets one password → owns both layers

   Good independence:
   - Firewall: Hardware token + unique password
   - App: Different identity provider, MFA
   - Database: Automated credential rotation

   Each layer should have its own authentication, own encryption keys, and own failure modes.
   </details>

2. **What's the difference between encryption in transit and at rest?**
   <details>
   <summary>Answer</summary>

   **Encryption in transit** protects data as it moves between systems:
   - Implemented via TLS/SSL, mTLS
   - Protects against network sniffing, man-in-the-middle attacks
   - Data is encrypted only while moving; decrypted at endpoints

   **Encryption at rest** protects stored data:
   - Implemented via disk encryption, database encryption, application-level encryption
   - Protects against physical theft, unauthorized disk access
   - Data is encrypted on storage; decrypted when accessed

   Defense in depth uses both: Data is encrypted on disk AND encrypted when transmitted.
   </details>

3. **How do network policies implement defense in depth in Kubernetes?**
   <details>
   <summary>Answer</summary>

   Network policies create micro-segmentation within the cluster:

   1. **Default deny**: Block all traffic by default
   2. **Explicit allow**: Only permit required communication paths
   3. **Namespace isolation**: Pods can't talk across namespaces without explicit policy
   4. **Pod-level rules**: Only specific pods can reach specific services

   If an attacker compromises one pod, network policies limit lateral movement. They can't reach the database directly—they'd have to compromise the application pod that's allowed to connect.

   This is defense in depth because even if container security fails, network security provides another layer.
   </details>

4. **Why is key management often the weakest link in encryption?**
   <details>
   <summary>Answer</summary>

   Encryption is only as strong as key protection. Common failures:

   1. **Keys stored with data**: Attacker who gets data also gets keys
   2. **Keys in code/config**: Leaked through version control, logs
   3. **Keys never rotated**: Old keys accumulate, larger exposure window
   4. **Shared keys**: Too many systems know the key
   5. **No access control**: Anyone can read the key
   6. **No audit**: Don't know who accessed keys

   Proper key management:
   - Dedicated key management system (HashiCorp Vault, AWS KMS)
   - Automatic rotation
   - Access control and audit logging
   - Separation from application servers
   </details>

5. **A system has 5 independent security layers, each 90% effective. What's the probability an attack succeeds through all layers? What if the layers share a common credential that's 95% secure?**
   <details>
   <summary>Answer</summary>

   **Independent layers:**

   Probability attack succeeds = (1 - 0.90)^5 = 0.10^5 = 0.00001 = **0.001%**

   **Shared credential (dependent layers):**

   If the shared credential is compromised (5% chance), ALL layers fail:
   - Probability = 0.05 = **5%**

   The difference is dramatic:
   - Independent: 1 in 100,000 attacks succeeds
   - Dependent: 1 in 20 attacks succeeds

   This is why layer independence is critical. Shared credentials, shared keys, or shared infrastructure create hidden dependencies that undermine the entire defense strategy.
   </details>

6. **In the Target breach, attackers entered through an HVAC vendor and reached point-of-sale systems. What defense-in-depth principle failed, and how should it have been implemented?**
   <details>
   <summary>Answer</summary>

   **Failed principle: Network segmentation**

   The HVAC vendor's network access should have been isolated to only HVAC-related systems. Point-of-sale systems processing credit cards should have been in a completely separate network segment with no path from vendor networks.

   Proper implementation:

   1. **Segment by sensitivity**: Payment systems in PCI-compliant segment, vendor access in separate segment

   2. **Default deny between segments**: No traffic allowed between segments unless explicitly required

   3. **Jump hosts for cross-segment access**: If vendor needs limited access to other systems, require separate authentication through a monitored jump host

   4. **Alert on anomalous traffic**: HVAC systems don't need to talk to POS systems—any such traffic should generate alerts

   5. **Credential isolation**: Vendor credentials should work only in vendor segment, not anywhere else

   Target had some segmentation, but the segments could reach each other. True segmentation means the attack path simply doesn't exist.
   </details>

7. **Why does defense in depth recommend both a WAF (Web Application Firewall) at the network edge AND input validation in the application code?**
   <details>
   <summary>Answer</summary>

   Each provides different protection with different failure modes:

   **WAF (Network layer)**:
   - Blocks known attack patterns before reaching application
   - Can be updated quickly for new threats
   - Provides protection for all applications behind it
   - Weakness: Can be bypassed with encoding tricks, doesn't understand application context

   **Application input validation (Application layer)**:
   - Understands business logic (is this a valid order quantity?)
   - Can't be bypassed by network tricks
   - Specific to application requirements
   - Weakness: Developers might forget to validate some inputs

   Together:
   - WAF catches 90% of SQL injection attempts
   - The 10% that get through are caught by parameterized queries
   - Novel attacks might bypass WAF but hit application validation
   - Known attacks caught by WAF even if app has a bug

   This is Swiss cheese in action—different holes in different places.
   </details>

8. **A Kubernetes cluster has NetworkPolicies blocking pod-to-pod traffic, but an attacker compromised one pod and accessed another pod's data. What likely went wrong?**
   <details>
   <summary>Answer</summary>

   Several possibilities (defense in depth means checking all layers):

   1. **NetworkPolicy not enforced**: NetworkPolicies require a CNI plugin that supports them (Calico, Cilium, etc.). Default kubenet doesn't enforce policies—they exist but do nothing.

   2. **Policy gaps**: Default deny wasn't applied. Policies only block what's explicitly denied or allow what's explicitly allowed. Missing a default deny means unlisted traffic flows freely.

   3. **Bypassed via shared resources**: Pods might share:
      - A volume mount containing sensitive data
      - A service account token with excessive permissions
      - Access to the same external service (database, cache)

   4. **DNS/metadata access**: NetworkPolicy might block pod IPs but allow access to kube-dns or cloud metadata services, which can be used for data exfiltration.

   5. **Host network mode**: If the compromised pod ran with `hostNetwork: true`, NetworkPolicies don't apply—it's on the node's network, not the pod network.

   Defense in depth means: NetworkPolicy + pod security context + service account restrictions + secrets management + runtime security monitoring.
   </details>

---

## Hands-On Exercise

**Task**: Audit a system for defense in depth.

**Scenario**: Review the following architecture and identify missing layers:

```
Architecture:
                    Internet
                        │
                   [Firewall]
                        │
                   [Web Server] ─── serves static files
                        │
                   [App Server] ─── business logic
                        │
                   [Database] ─── PostgreSQL
```

**Part 1: Layer Inventory (10 minutes)**

Fill in current controls:

| Layer | Controls Present | Controls Missing |
|-------|------------------|------------------|
| Network | Firewall | |
| Host | | |
| Application | | |
| Data | | |

**Part 2: Attack Scenarios (10 minutes)**

For each attack, identify which layers would stop it:

| Attack | Layer 1 | Layer 2 | Layer 3 | Stopped? |
|--------|---------|---------|---------|----------|
| SQL injection | | | | |
| Stolen DB backup | | | | |
| Network sniffing | | | | |
| Compromised app server | | | | |

**Part 3: Recommendations (10 minutes)**

Propose controls to add:

| Gap | Proposed Control | Layer | Priority |
|-----|------------------|-------|----------|
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |

**Success Criteria**:
- [ ] All four layers inventoried
- [ ] At least 5 missing controls identified
- [ ] Attack scenarios analyzed with layer mapping
- [ ] Prioritized recommendations provided

---

## Further Reading

- **"Network Security Essentials"** - William Stallings. Comprehensive coverage of network security principles and protocols.

- **"Kubernetes Security"** - Liz Rice. Defense in depth specifically for Kubernetes environments.

- **NIST Cybersecurity Framework** - Framework for organizing security controls in layers.

---

## Key Takeaways Checklist

Before moving on, verify you can answer these:

- [ ] Can you explain the Swiss cheese model and why layer independence matters?
- [ ] Can you name and describe the five defense-in-depth layers (physical, network, host, application, data)?
- [ ] Do you understand network segmentation and why flat networks are dangerous?
- [ ] Can you explain zero trust networking and how mTLS implements it?
- [ ] Do you understand the difference between encryption in transit and at rest?
- [ ] Can you explain why key management is often the weakest link in encryption?
- [ ] Do you understand how Kubernetes implements defense in depth (cluster, namespace, pod, container layers)?
- [ ] Can you calculate the probability difference between independent vs dependent security layers?

---

## Next Module

[Module 4.3: Identity and Access Management](../module-4.3-identity-and-access/) - Authentication, authorization, and the principle of least privilege in practice.
