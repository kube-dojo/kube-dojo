---
title: "Module 2.1: Control Plane Security"
slug: k8s/kcsa/part2-cluster-component-security/module-2.1-control-plane-security
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Core knowledge
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: [Module 1.3: Security Principles](../part1-cloud-native-security/module-1.3-security-principles/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** API server, etcd, scheduler, and controller manager security configurations
2. **Assess** the impact of control plane compromise on cluster-wide security posture
3. **Identify** insecure control plane settings: anonymous auth, unencrypted etcd, permissive RBAC
4. **Explain** how to harden each control plane component following CIS benchmark recommendations

---

## Why This Module Matters

The control plane is the brain of Kubernetes. If it's compromised, an attacker controls your entire cluster—every pod, every secret, every workload. Understanding control plane security is critical not just for the exam, but for any production Kubernetes deployment.

This is one of the largest exam domains (22%) combined with node security and networking. Master this, and you're well on your way to passing.

---

## Control Plane Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CONTROL PLANE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API SERVER                        │   │
│  │  • Front door to the cluster                        │   │
│  │  • All requests go through here                     │   │
│  │  • Authentication, Authorization, Admission         │   │
│  └─────────────────────────────────────────────────────┘   │
│           │              │                │                 │
│           ▼              ▼                ▼                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │    ETCD     │ │  SCHEDULER  │ │ CONTROLLER MANAGER  │   │
│  │             │ │             │ │                     │   │
│  │ • Database  │ │ • Pod       │ │ • Reconciliation    │   │
│  │ • Secrets   │ │   placement │ │ • Built-in          │   │
│  │ • State     │ │             │ │   controllers       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│                                                             │
│  Each component has specific security requirements         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## API Server Security

The API server is the most critical component—it's the only component that communicates with etcd and the gateway for all cluster operations.

### Authentication

Who is making this request?

```
┌─────────────────────────────────────────────────────────────┐
│              API SERVER AUTHENTICATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHENTICATION METHODS                                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  X.509 CLIENT CERTIFICATES                          │   │
│  │  • Used by: kubelet, controller-manager, scheduler  │   │
│  │  • CN = username, O = groups                        │   │
│  │  • Managed by cluster PKI                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SERVICE ACCOUNT TOKENS                             │   │
│  │  • Used by: Pods                                    │   │
│  │  • JWT tokens, auto-mounted                         │   │
│  │  • Bound to specific audience and expiration        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  OIDC (OpenID Connect)                              │   │
│  │  • Used by: Human users                             │   │
│  │  • Integrates with identity providers               │   │
│  │  • Supports MFA through provider                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  WEBHOOK TOKEN AUTHENTICATION                       │   │
│  │  • Used by: Custom integrations                     │   │
│  │  • External service validates tokens                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: The API server processes every request through authentication, authorization, and admission — in that order. Why does order matter? What would happen if admission ran before authentication?

### Authorization

Is this identity allowed to perform this action?

```
┌─────────────────────────────────────────────────────────────┐
│              API SERVER AUTHORIZATION                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTHORIZATION MODES (in order of evaluation)              │
│                                                             │
│  NODE                                                       │
│  • Authorizes kubelet requests                             │
│  • Limited to resources for pods on that node              │
│                                                             │
│  RBAC (Most common)                                        │
│  • Role-based access control                               │
│  • Roles, ClusterRoles, Bindings                           │
│  • Fine-grained permissions                                │
│                                                             │
│  ABAC (Legacy)                                             │
│  • Attribute-based access control                          │
│  • File-based policies                                     │
│  • Requires API server restart to change                   │
│                                                             │
│  WEBHOOK                                                    │
│  • External authorization service                          │
│  • Custom policy engines (OPA/Gatekeeper)                  │
│                                                             │
│  Typical configuration: --authorization-mode=Node,RBAC     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Admission Control

Should this valid, authorized request be allowed?

```
┌─────────────────────────────────────────────────────────────┐
│              ADMISSION CONTROL FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Request → Authentication → Authorization → Admission      │
│                                                             │
│  ADMISSION CONTROLLERS                                      │
│                                                             │
│  MUTATING (modify requests)                                │
│  ├── DefaultStorageClass: Adds default storage class       │
│  ├── ServiceAccount: Adds default service account          │
│  └── Custom webhooks: Add sidecars, labels                 │
│                                                             │
│  VALIDATING (accept/reject requests)                       │
│  ├── PodSecurity: Enforces Pod Security Standards          │
│  ├── ValidatingAdmissionPolicy: CEL-based validation       │
│  └── Custom webhooks: Policy enforcement                   │
│                                                             │
│  SECURITY-CRITICAL ADMISSION CONTROLLERS                   │
│  ├── PodSecurity (PSA)                                     │
│  ├── NodeRestriction                                       │
│  ├── ValidatingAdmissionWebhook                            │
│  └── MutatingAdmissionWebhook                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### API Server Security Flags

Important security-related configuration:

| Flag | Purpose | Secure Setting | CIS Benchmark |
|------|---------|----------------|---------------|
| `--anonymous-auth` | Allow unauthenticated requests | `false` for production | CIS 1.2.1 |
| `--authorization-mode` | How to authorize requests | `Node,RBAC` | CIS 1.2.7, 1.2.8 |
| `--enable-admission-plugins` | Which admission controllers | Include `PodSecurity,NodeRestriction` | CIS 1.2.15, 1.2.16 |
| `--audit-log-path` | Where to write audit logs | Set to valid path | CIS 1.2.19 |
| `--tls-cert-file` | API server TLS certificate | Must be configured | CIS 1.2.26 |
| `--etcd-cafile` | CA to verify etcd | Must be configured | CIS 1.2.28 |

---

## etcd Security

etcd stores all cluster state, including secrets. Its security is paramount.

```
┌─────────────────────────────────────────────────────────────┐
│              ETCD SECURITY                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ETCD CONTAINS:                                            │
│  • All Kubernetes objects (pods, deployments, etc.)        │
│  • Secrets (base64 encoded by default)                     │
│  • ConfigMaps                                               │
│  • RBAC configuration                                      │
│  • Service account tokens                                  │
│                                                             │
│  IF ETCD IS COMPROMISED:                                   │
│  • All secrets exposed                                     │
│  • Cluster state can be modified                           │
│  • Complete cluster compromise                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### etcd Security Controls

```
┌─────────────────────────────────────────────────────────────┐
│              ETCD SECURITY CONTROLS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ACCESS CONTROL                                            │
│  ├── Only API server should access etcd                    │
│  ├── Network isolation (firewall, security groups)         │
│  ├── Client certificate authentication                     │
│  └── No direct access from pods                            │
│                                                             │
│  ENCRYPTION IN TRANSIT                                     │
│  ├── TLS for client-to-server (CIS 2.1)                    │
│  ├── TLS for peer-to-peer (CIS 2.3, 2.4)                   │
│  └── Mutual TLS (mTLS) preferred (CIS 2.2)                 │
│                                                             │
│  ENCRYPTION AT REST                                        │
│  ├── Kubernetes secrets encryption (CIS 1.2.31)            │
│  ├── Provider options: aescbc, aesgcm, kms                 │
│  ├── KMS integration for key management                    │
│  └── Envelope encryption pattern                           │
│                                                             │
│  BACKUP SECURITY                                           │
│  ├── Encrypt backups                                       │
│  ├── Secure backup storage                                 │
│  └── Test restore procedures                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Secrets Encryption at Rest

By default, Kubernetes secrets are only base64 encoded in etcd—not encrypted:

```yaml
# EncryptionConfiguration example
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-key>
      - identity: {}  # Fallback for reading unencrypted
```

| Provider | Description | Use Case |
|----------|-------------|----------|
| `identity` | No encryption | Never for production |
| `aescbc` | AES-CBC encryption | Good for self-managed |
| `aesgcm` | AES-GCM encryption | Faster than aescbc |
| `kms` | External key management | Best for compliance |

---

> **Pause and predict**: If an attacker compromises the scheduler, they can influence where pods are placed. How could this be exploited even without modifying the pods themselves?

## Scheduler Security

The scheduler decides where pods run. Its compromise could place pods strategically.

```
┌─────────────────────────────────────────────────────────────┐
│              SCHEDULER SECURITY                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SCHEDULER RESPONSIBILITIES                                │
│  • Selects nodes for unscheduled pods                     │
│  • Respects resource requests and limits                   │
│  • Honors affinity and anti-affinity rules                │
│  • Enforces taints and tolerations                         │
│                                                             │
│  SECURITY CONCERNS                                         │
│  ├── Runs with significant cluster privileges             │
│  ├── Compromise could influence pod placement              │
│  ├── Could bypass node isolation                          │
│  └── Could cause denial of service                        │
│                                                             │
│  SECURITY CONTROLS                                         │
│  ├── Client certificate authentication to API server      │
│  ├── Minimal RBAC permissions (built-in binding)          │
│  ├── Bind address to localhost (127.0.0.1) (CIS 1.4.2)    │
│  ├── Disable profiling if not needed (CIS 1.4.1)          │
│  ├── Run on dedicated control plane nodes                 │
│  └── Network isolation from workload nodes                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Controller Manager Security

The controller manager runs control loops that maintain desired state.

```
┌─────────────────────────────────────────────────────────────┐
│              CONTROLLER MANAGER SECURITY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTROLLERS INCLUDE:                                      │
│  • Node controller (node health)                           │
│  • Replication controller (pod replicas)                   │
│  • Endpoints controller (service endpoints)                │
│  • ServiceAccount controller (creates default SA)          │
│  • Many more...                                            │
│                                                             │
│  SECURITY CONCERNS                                         │
│  ├── Access to service account signing key                │
│  ├── Can create/delete pods and services                  │
│  ├── Manages node lifecycle                               │
│  └── Compromise = cluster-wide impact                     │
│                                                             │
│  KEY SECURITY FLAGS                                        │
│  ├── --use-service-account-credentials=true (CIS 1.3.3)   │
│  │   (Use separate SA for each controller)                 │
│  ├── --root-ca-file (CIS 1.3.5)                           │
│  │   (CA for verifying API server)                         │
│  └── --service-account-private-key-file (CIS 1.3.4)       │
│      (Key for signing SA tokens)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Control Plane Network Security

```
┌─────────────────────────────────────────────────────────────┐
│              CONTROL PLANE NETWORK                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RECOMMENDED ARCHITECTURE                                  │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │           PRIVATE SUBNET (Control Plane)           │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │    │
│  │  │   API   │ │  etcd   │ │ Sched   │ │  Ctrl   │  │    │
│  │  │  Server │ │         │ │         │ │   Mgr   │  │    │
│  │  └────┬────┘ └─────────┘ └─────────┘ └─────────┘  │    │
│  │       │                                            │    │
│  └───────┼────────────────────────────────────────────┘    │
│          │ (Only API server exposed)                       │
│          ▼                                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │           PRIVATE SUBNET (Worker Nodes)            │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐              │    │
│  │  │  Node 1 │ │  Node 2 │ │  Node 3 │              │    │
│  │  │ kubelet │ │ kubelet │ │ kubelet │              │    │
│  │  └─────────┘ └─────────┘ └─────────┘              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  SECURITY REQUIREMENTS:                                    │
│  • etcd: Only accessible from API server                   │
│  • API server: Accessible from nodes and admins           │
│  • Scheduler/CM: Only need to reach API server            │
│  • Private API endpoint preferred                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The API server processes thousands of requests per second** in busy clusters. Each request goes through authentication, authorization, and admission—all potential security checkpoints.

- **etcd was not designed for Kubernetes**—it's a general-purpose distributed key-value store. Kubernetes adapted it, which is why encryption at rest isn't enabled by default.

- **In managed Kubernetes**, you typically can't access etcd directly. The cloud provider manages it and provides encryption options through their configuration.

- **Node authorization mode** was added specifically to prevent compromised kubelets from accessing resources for pods on other nodes—a real attack vector.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Anonymous auth enabled | Anyone can query API | Disable `--anonymous-auth` |
| No etcd encryption | Secrets stored in clear text | Enable encryption at rest |
| etcd exposed to network | Direct access bypasses API security | Network isolation |
| Public API server endpoint | Exposed to internet attacks | Use private endpoint |
| Missing audit logging | Can't detect or investigate breaches | Enable audit logging |

---

## Quiz

1. **During a security audit, you discover the API server is configured with `--authorization-mode=AlwaysAllow`. The cluster has been running for months in production. What is the immediate risk, and what steps would you take to remediate without causing an outage?**
   <details>
   <summary>Answer</summary>
   AlwaysAllow means every authenticated request is authorized — any user or service account can perform any action, including reading all secrets, creating privileged pods, or modifying RBAC. Immediate risk is full cluster compromise if any credential is stolen. Remediation: first, audit existing RBAC roles and bindings to ensure they cover current needs. Then switch to `--authorization-mode=Node,RBAC` during a maintenance window. Node mode restricts kubelets to their own pods' resources, and RBAC enforces role-based permissions. Test in a staging cluster first, as switching modes may break workloads relying on implicit permissions.
   </details>

2. **Your team wants to enable encryption at rest for secrets in etcd. They configure the EncryptionConfiguration with `aescbc` as the first provider and `identity` as the fallback. A colleague asks: "Why keep `identity` at all?" Explain.**
   <details>
   <summary>Answer</summary>
   The `identity` provider as fallback allows the API server to read secrets that were stored before encryption was enabled — these older secrets are still in plaintext (identity-encoded) in etcd. Without the identity fallback, the API server would fail to decrypt any pre-existing unencrypted secrets, potentially breaking workloads. After enabling encryption, you should re-encrypt all existing secrets (`kubectl get secrets --all-namespaces -o json | kubectl replace -f -`) and then can optionally remove the identity fallback. The provider order matters: the first provider is used for writing (new secrets encrypted with aescbc), while all providers are tried for reading.
   </details>

3. **A penetration tester reports that they can query the etcd database directly from a compromised pod, bypassing the API server entirely. What misconfiguration allowed this, and what is the impact?**
   <details>
   <summary>Answer</summary>
   etcd is not properly network-isolated — it should only be accessible from the API server. The misconfiguration is either missing firewall rules between worker nodes and etcd, or etcd listening on a network interface accessible to pods. The impact is catastrophic: etcd contains all cluster state including secrets (potentially unencrypted), RBAC configuration, and service account tokens. The attacker can read every secret, modify cluster state, or destroy the cluster entirely. Fix: restrict etcd access to only the API server via network policies/firewalls, require mTLS client certificates for etcd access, and use private network interfaces.
   </details>

4. **The NodeRestriction admission controller limits what kubelets can modify. If a node is compromised, explain what the attacker can and cannot do with the kubelet's credentials when NodeRestriction is enabled vs. disabled.**
   <details>
   <summary>Answer</summary>
   With NodeRestriction enabled: the compromised kubelet can only access resources for pods scheduled on that specific node — it can read secrets mounted to those pods and modify those pods' status, but cannot access secrets for pods on other nodes, modify other nodes' pods, or change cluster-wide resources. Without NodeRestriction: the kubelet credentials can potentially access any pod's secrets, modify pods on other nodes, and the blast radius extends to the entire cluster. NodeRestriction implements least privilege for node credentials, making each node compromise a single-node incident rather than a cluster-wide one.
   </details>

5. **You notice that mutating admission webhooks run before validating admission webhooks in the API server request flow. A security team member asks whether a malicious mutating webhook could bypass a validating webhook's security checks. Is this possible?**
   <details>
   <summary>Answer</summary>
   No, this is not possible. The Kubernetes API server strictly enforces the admission control flow: all mutating admission webhooks execute *before* any validating admission webhooks. Because validating webhooks always run last, they inspect the final, fully mutated object exactly as it will be persisted to etcd. Even if a malicious mutating webhook attempts to inject a dangerous field (like `privileged: true`), the validating webhook will catch it and reject the request. This strict separation ensures there are no post-validation mutations, completely preventing mutation bypasses. To handle cases where a mutating webhook's changes might affect other mutating webhooks, Kubernetes uses a reinvocation policy (`reinvocationPolicy: IfNeeded`), but this only loops within the mutation phase; validation always remains the absolute final step.
   </details>
---

## Hands-On Exercise: Control Plane Security Assessment

**Scenario**: Review these API server flags and identify security issues:

```
kube-apiserver \
  --anonymous-auth=true \
  --authorization-mode=AlwaysAllow \
  --enable-admission-plugins=NamespaceLifecycle,ServiceAccount \
  --audit-log-path="" \
  --etcd-servers=http://etcd:2379
```

**Identify at least 4 security issues:**

<details>
<summary>Security Issues</summary>

1. **`--anonymous-auth=true`**
   - Allows unauthenticated requests
   - Should be `false` for production

2. **`--authorization-mode=AlwaysAllow`**
   - No authorization checking
   - Should be `Node,RBAC`

3. **Missing admission controllers**
   - No `PodSecurity` for pod security enforcement
   - No `NodeRestriction` for kubelet limitations
   - Should add security-focused admission controllers

4. **`--audit-log-path=""`**
   - No audit logging
   - Can't detect or investigate security incidents
   - Should point to a valid path

5. **`--etcd-servers=http://...`**
   - Unencrypted HTTP connection to etcd
   - Should use HTTPS with TLS certificates

</details>

---

## Summary

Control plane security is about protecting the brain of Kubernetes:

| Component | Key Security Controls |
|-----------|----------------------|
| **API Server** | TLS, authentication (certs, OIDC), RBAC authorization, admission control |
| **etcd** | Network isolation, TLS, encryption at rest, backup encryption |
| **Scheduler** | Certificate auth, network isolation, minimal privileges |
| **Controller Manager** | Certificate auth, separate service accounts per controller |

Key points:
- All requests flow through the API server
- etcd must be protected—it contains all secrets
- Use Node,RBAC authorization mode
- Enable security-focused admission controllers
- Encrypt etcd at rest

---

## Next Module

[Module 2.2: Node Security](../module-2.2-node-security/) - Securing worker nodes, kubelets, and container runtimes.