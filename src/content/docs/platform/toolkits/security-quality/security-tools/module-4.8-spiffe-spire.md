---
title: "Module 4.8: SPIFFE/SPIRE - Cryptographic Workload Identity"
slug: platform/toolkits/security-quality/security-tools/module-4.8-spiffe-spire
sidebar:
  order: 9
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~50 minutes

## Overview

SPIFFE (Secure Production Identity Framework for Everyone) is an open standard for workload identity, and SPIRE (the SPIFFE Runtime Environment) is the reference implementation. Together they give every workload a cryptographically verifiable identity -- no more shared secrets, no more long-lived credentials, no more hoping that a network boundary is enough.

**What You'll Learn**:
- The SPIFFE identity model: SPIFFE IDs, SVIDs, trust domains
- SPIRE architecture: Server, Agent, workload attestation
- Deploying SPIRE on Kubernetes with Helm
- Registering workloads and inspecting X.509 SVIDs
- Zero-configuration mTLS between services using SPIFFE
- How SPIFFE compares to ServiceAccount tokens, cert-manager, and service mesh identity

**Prerequisites**:
- [Security Principles Foundations](../../foundations/security-principles/)
- Kubernetes security fundamentals (ServiceAccounts, RBAC)
- TLS and mTLS basics (what certificates are, how mutual authentication works)
- [Module 7.3: cert-manager](../platforms/module-7.3-cert-manager/) (recommended)

---

## Why This Module Matters

It was 2 AM when the incident channel lit up. An attacker had compromised a single container in a staging namespace -- a forgotten debug pod with default ServiceAccount credentials. From there, they moved laterally. The staging ServiceAccount token worked against internal APIs that only checked "is this a valid token?" not "should this specific workload be calling me?" Within three hours, the attacker had read production database credentials from a config service that trusted anything inside the cluster network.

The post-mortem was brutal. The CISO asked one question: "Can we prove, cryptographically, which workload is calling which?" The answer was no. Kubernetes ServiceAccount tokens told you *what namespace and ServiceAccount* a pod used, but they were never designed to be a universal workload identity. Any pod with the same ServiceAccount got the same token. There was no attestation that the binary running inside the container was what it claimed to be.

The team adopted SPIFFE/SPIRE within a month. Every workload got a unique, short-lived X.509 certificate -- automatically rotated, automatically attested, zero developer friction. The lateral movement attack vector was gone. If a workload could not present a valid SVID for its registered identity, no service would talk to it.

> **Did You Know?**
> - SPIFFE graduated as a CNCF Incubating project and is used in production at Bloomberg, ByteDance, Uber, and Pinterest -- organizations running hundreds of thousands of workloads.
> - SPIRE can issue SVIDs that expire in as little as one hour. Compare that to Kubernetes ServiceAccount tokens that, before the TokenRequest API, never expired at all.
> - SPIFFE is designed to work across heterogeneous environments. A SPIRE trust domain can span Kubernetes clusters, VMs, bare metal, and serverless -- giving every workload the same identity framework regardless of where it runs.
> - The SPIFFE Workload API requires no secrets to bootstrap. A workload never holds a private key file on disk -- SPIRE delivers the key material through a Unix domain socket, and the agent attests the caller's identity using kernel-level process information.

---

## SPIFFE Core Concepts

Before touching SPIRE, you need to understand the four pillars of SPIFFE.

### SPIFFE ID

A SPIFFE ID is a URI that uniquely identifies a workload:

```
spiffe://trust-domain/path

Examples:
spiffe://production.example.com/ns/payments/sa/api-server
spiffe://staging.example.com/ns/frontend/sa/web
spiffe://example.com/host/db-primary
```

The **trust domain** is the root of trust (like a certificate authority's domain). The **path** is flexible -- in Kubernetes, it typically encodes the namespace and service account.

### SVID (SPIFFE Verifiable Identity Document)

An SVID is the proof of identity. It comes in two forms:

| SVID Type | Format | Use Case |
|-----------|--------|----------|
| **X.509-SVID** | X.509 certificate with SPIFFE ID in SAN URI | mTLS connections, long-running services |
| **JWT-SVID** | Signed JWT token with SPIFFE ID as subject | API calls, service-to-service auth over HTTP |

### Trust Domain

A trust domain is an identity namespace backed by a single SPIRE Server (or HA cluster). Workloads within the same trust domain inherently trust each other's certificates. Cross-domain trust requires explicit federation.

### Workload API

The Workload API is a local gRPC endpoint (Unix domain socket) that workloads call to get their SVIDs. The workload never provides credentials -- the SPIRE Agent identifies the caller by inspecting its process metadata (PID, cgroups, container ID) and checking it against registration entries.

```
SPIFFE IDENTITY MODEL
════════════════════════════════════════════════════════════════

  Trust Domain: production.example.com
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  Workload A                    Workload B                │
  │  ┌────────────────────┐        ┌────────────────────┐   │
  │  │ SPIFFE ID:         │        │ SPIFFE ID:         │   │
  │  │ spiffe://prod...   │        │ spiffe://prod...   │   │
  │  │   /ns/pay/sa/api   │        │   /ns/orders/sa/db │   │
  │  │                    │        │                    │   │
  │  │ X.509 SVID:        │  mTLS  │ X.509 SVID:        │   │
  │  │ ┌──────────────┐   │◄──────►│ ┌──────────────┐   │   │
  │  │ │ Cert (1h TTL)│   │        │ │ Cert (1h TTL)│   │   │
  │  │ │ Private Key  │   │        │ │ Private Key  │   │   │
  │  │ │ Trust Bundle │   │        │ │ Trust Bundle │   │   │
  │  │ └──────────────┘   │        │ └──────────────┘   │   │
  │  └────────────────────┘        └────────────────────┘   │
  │           ▲                              ▲              │
  │           │ Workload API                 │              │
  │           │ (Unix socket)                │              │
  │  ┌────────┴──────────────────────────────┴───────────┐  │
  │  │              SPIRE Agent (per node)                │  │
  │  │  - Attests workloads via kernel/container info     │  │
  │  │  - Caches and rotates SVIDs                       │  │
  │  └───────────────────────┬───────────────────────────┘  │
  │                          │                               │
  │  ┌───────────────────────┴───────────────────────────┐  │
  │  │              SPIRE Server                          │  │
  │  │  - Certificate Authority                           │  │
  │  │  - Registration entries database                   │  │
  │  │  - Node attestation                                │  │
  │  └───────────────────────────────────────────────────┘  │
  └──────────────────────────────────────────────────────────┘
```

---

## SPIRE Architecture

### SPIRE Server

The Server is the brain of SPIRE. It:

- Acts as the **Certificate Authority** -- signs SVIDs for workloads
- Stores **registration entries** -- the mapping of "which workloads get which SPIFFE IDs"
- Performs **node attestation** -- verifies that Agents are running on legitimate nodes
- Manages **trust bundles** -- the CA certificates that workloads use to verify peers

### SPIRE Agent

The Agent runs on every node (DaemonSet in Kubernetes). It:

- Performs **workload attestation** -- identifies which container is requesting an identity
- Exposes the **Workload API** -- a Unix domain socket that workloads connect to
- **Caches SVIDs** -- rotates certificates before they expire, no workload restarts needed
- Communicates with the Server to fetch signed certificates

### Registration Entries

A registration entry tells SPIRE: "A workload matching these selectors should receive this SPIFFE ID." In Kubernetes, selectors include:

- `k8s:ns:payments` -- workload runs in the `payments` namespace
- `k8s:sa:api-server` -- workload uses the `api-server` ServiceAccount
- `k8s:pod-label:app:frontend` -- workload has the label `app=frontend`
- `k8s:container-name:api` -- specific container within a pod

---

## Deploying SPIRE on Kubernetes

### Installation via Helm

```bash
# Create a kind cluster for the lab
kind create cluster --name spire-lab

# Add the SPIRE Helm repository
helm repo add spire https://spiffe.github.io/helm-charts-hardened/
helm repo update

# Install the SPIRE stack (server + agent + SPIFFE CSI driver)
helm install spire spire/spire \
  --namespace spire-system \
  --create-namespace \
  --set global.spire.trustDomain=example.org \
  --set global.spire.clusterName=spire-lab \
  --wait --timeout 300s

# Verify all components are running
kubectl get pods -n spire-system
```

You should see:
- `spire-server-0` -- the SPIRE Server (StatefulSet)
- `spire-agent-xxxxx` -- one Agent pod per node (DaemonSet)
- `spiffe-csi-driver-xxxxx` -- CSI driver for projecting the Workload API socket

### Verify the Server is healthy

```bash
# Check the SPIRE Server health
kubectl exec -n spire-system spire-server-0 -- \
  spire-server healthcheck

# List registered agents (nodes)
kubectl exec -n spire-system spire-server-0 -- \
  spire-server agent list
```

---

## Registering Workloads

### Create a Registration Entry

Registration entries map Kubernetes selectors to SPIFFE IDs.

```bash
# Register: pods in namespace "payments" with SA "api-server"
# get the SPIFFE ID spiffe://example.org/ns/payments/sa/api-server
kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry create \
    -spiffeID spiffe://example.org/ns/payments/sa/api-server \
    -parentID spiffe://example.org/spire/agent/k8s_psat/spire-lab \
    -selector k8s:ns:payments \
    -selector k8s:sa:api-server \
    -ttl 3600

# Register a second workload for cross-service mTLS
kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry create \
    -spiffeID spiffe://example.org/ns/orders/sa/order-service \
    -parentID spiffe://example.org/spire/agent/k8s_psat/spire-lab \
    -selector k8s:ns:orders \
    -selector k8s:sa:order-service \
    -ttl 3600

# List all registration entries
kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry show
```

### Deploy a Test Workload

```yaml
# test-workload.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: payments
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-server
  namespace: payments
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: payments
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      serviceAccountName: api-server
      containers:
      - name: app
        image: ghcr.io/spiffe/spiffe-helper:latest
        command: ["sleep", "infinity"]
        volumeMounts:
        - name: spiffe-workload-api
          mountPath: /spiffe-workload-api
          readOnly: true
      volumes:
      - name: spiffe-workload-api
        csi:
          driver: "csi.spiffe.io"
          readOnly: true
```

```bash
kubectl apply -f test-workload.yaml

# Wait for the pod to be ready
kubectl wait --for=condition=ready pod -l app=api-server \
  -n payments --timeout=60s
```

### Inspect the SVID

```bash
# Fetch the SVID from inside the workload
kubectl exec -n payments deploy/api-server -- \
  /opt/spire/bin/spire-agent api fetch x509 \
    -socketPath /spiffe-workload-api/spire-agent.sock \
    -write /tmp/

# View the certificate details
kubectl exec -n payments deploy/api-server -- \
  openssl x509 -in /tmp/svid.0.pem -text -noout | head -30
```

You will see the SPIFFE ID in the Subject Alternative Name (SAN) field:

```
X509v3 Subject Alternative Name:
    URI:spiffe://example.org/ns/payments/sa/api-server
```

The certificate is short-lived (TTL matches your registration entry), automatically rotated by the Agent, and the private key never touches disk in the traditional sense -- it is delivered through the Workload API socket.

---

## mTLS with SPIFFE: Zero-Configuration Mutual Authentication

The real power of SPIFFE is what happens when two workloads need to talk securely. Neither workload needs to know about certificates, CAs, or key management. They just call the Workload API, get their SVID, and use it.

```
ZERO-CONFIG mTLS FLOW
════════════════════════════════════════════════════════════════

  Payment Service                      Order Service
  ┌──────────────────┐                ┌──────────────────┐
  │ 1. Fetch my SVID │                │ 1. Fetch my SVID │
  │    from Agent    │                │    from Agent    │
  │                  │                │                  │
  │ 2. TLS handshake │───────────────►│ 2. TLS handshake │
  │    Present X.509 │◄───────────────│    Present X.509 │
  │    SVID as cert  │                │    SVID as cert  │
  │                  │                │                  │
  │ 3. Verify peer's │                │ 3. Verify peer's │
  │    SVID against  │                │    SVID against  │
  │    trust bundle  │                │    trust bundle  │
  │                  │                │                  │
  │ 4. Check SPIFFE  │                │ 4. Check SPIFFE  │
  │    ID is allowed │                │    ID is allowed │
  └──────────────────┘                └──────────────────┘
         │                                    │
         ▼                                    ▼
  Both sides verified ──► Encrypted channel established
```

Libraries like `go-spiffe` (Go), `java-spiffe` (Java), and `py-spiffe` (Python) handle the entire flow with a few lines of code:

```go
// Go example using go-spiffe
source, err := workloadapi.NewX509Source(ctx,
    workloadapi.WithClientOptions(
        workloadapi.WithAddr("unix:///spiffe-workload-api/spire-agent.sock"),
    ),
)
defer source.Close()

// Create mTLS server -- no cert files, no CA config
tlsConfig := tlsconfig.MTLSServerConfig(source, source,
    tlsconfig.AuthorizeID(
        spiffeid.RequireIDFromString("spiffe://example.org/ns/payments/sa/api-server"),
    ),
)
server := &http.Server{TLSConfig: tlsConfig}
```

No certificate files. No CA paths. No renewal cron jobs. SPIRE handles rotation, and the library handles verification. The developer only specifies *which* SPIFFE IDs are allowed to connect.

---

## Comparison: Workload Identity Approaches

| Feature | K8s ServiceAccount Tokens | SPIFFE/SPIRE | Istio Service Identity | cert-manager |
|---------|--------------------------|-------------|----------------------|-------------|
| **Identity format** | JWT (bound to SA) | X.509 cert or JWT with SPIFFE URI | X.509 cert with SPIFFE URI | X.509 cert (custom SAN) |
| **Scope** | Single cluster | Multi-cluster, multi-cloud, VMs | Single mesh | Single cluster |
| **Auto-rotation** | Yes (TokenRequest API) | Yes (Agent handles it) | Yes (Envoy sidecar) | Yes (with renewal) |
| **mTLS** | No (token-based only) | Yes (native) | Yes (via Envoy proxy) | Yes (manual config) |
| **Workload attestation** | None (any pod with SA gets token) | Kernel-level (PID, cgroups, container) | Proxy-level (Envoy identity) | None |
| **Non-K8s workloads** | No | Yes (VMs, bare metal, serverless) | Limited (VM support experimental) | Partial (any cert requester) |
| **Developer effort** | Zero (auto-mounted) | Low (CSI driver mounts socket) | Zero (sidecar injection) | Medium (cert requests, mounts) |
| **CNCF status** | Core K8s | Incubating | Graduated (Istio) | Graduated |
| **Best for** | K8s API auth | Universal workload identity | Service mesh environments | Certificate lifecycle mgmt |

**When to choose SPIFFE/SPIRE**: You need workload identity that spans Kubernetes and non-Kubernetes environments, you want attestation beyond "same ServiceAccount", or you are building a zero-trust architecture without committing to a full service mesh.

**When to stick with ServiceAccount tokens**: Your workloads only need to authenticate to the Kubernetes API, and you are not doing service-to-service mTLS.

**When Istio is better**: You already run a service mesh and want identity, traffic management, and observability in one package. Istio actually uses SPIFFE IDs internally -- SPIRE can serve as a pluggable CA for Istio.

> See [Module 5.2: Service Mesh](../networking/module-5.2-service-mesh/) for how Istio handles identity through Envoy sidecars. See [Module 7.3: cert-manager](../platforms/module-7.3-cert-manager/) for certificate lifecycle management. For CKS exam topics on workload identity, refer to the [CKS Security Track](../../../k8s/cks/).

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using overly broad selectors | Every pod in a namespace gets the same SPIFFE ID | Combine `k8s:ns` with `k8s:sa` or `k8s:pod-label` for precise identity |
| Setting long TTLs on SVIDs | Compromised certificates remain valid for hours or days | Keep TTL short (1 hour or less); SPIRE handles rotation transparently |
| Forgetting to register workloads | Pod starts but gets no SVID; Workload API returns empty | Always create registration entries before deploying workloads |
| Hardcoding trust bundle paths | Breaks when trust bundle rotates | Use the Workload API to fetch trust bundles dynamically |
| Running SPIRE Server without HA | Server crash means no new SVIDs can be issued | Run SPIRE Server as a StatefulSet with 3+ replicas and a shared datastore |
| Not configuring upstream CA | SPIRE uses a self-signed CA that is hard to audit | Plug in an upstream CA (Vault, AWS PCA, cert-manager) for enterprise PKI integration |
| Ignoring federation for multi-cluster | Workloads in different clusters cannot verify each other | Configure SPIRE federation between trust domains |

---

## Quiz

### Question 1
What is a SPIFFE ID and what does it look like?

<details>
<summary>Show Answer</summary>

A SPIFFE ID is a URI that uniquely identifies a workload. It follows the format:

```
spiffe://trust-domain/path
```

For example: `spiffe://production.example.com/ns/payments/sa/api-server`

The trust domain identifies the issuing authority, and the path identifies the specific workload. Unlike a DNS name, a SPIFFE ID is embedded in a cryptographic document (SVID) and can be verified.

</details>

### Question 2
What is the difference between an X.509-SVID and a JWT-SVID, and when would you use each?

<details>
<summary>Show Answer</summary>

**X.509-SVID**: An X.509 certificate with the SPIFFE ID encoded in the SAN URI extension. Used for mTLS connections between services, especially for long-running TCP connections. The private key is held in memory by the workload.

**JWT-SVID**: A signed JWT token with the SPIFFE ID as the subject claim. Used for HTTP API authentication, especially when passing identity through proxies or load balancers that terminate TLS. JWT-SVIDs are single-use and cannot establish mTLS.

Use X.509-SVIDs for service-to-service mTLS. Use JWT-SVIDs when you need to pass identity through intermediaries or when a downstream service needs to verify identity without mutual TLS.

</details>

### Question 3
How does SPIRE's workload attestation differ from Kubernetes ServiceAccount token authentication?

<details>
<summary>Show Answer</summary>

**Kubernetes ServiceAccount tokens**: Any pod assigned a ServiceAccount receives the same token. There is no verification that the container binary is legitimate -- only that the pod was scheduled with that ServiceAccount.

**SPIRE workload attestation**: The SPIRE Agent inspects kernel-level properties of the calling process (PID, cgroups, container ID, namespace, service account, pod labels). It verifies these properties against registration entries. Even if an attacker compromises a pod and creates a rogue process, that process must match the exact selectors in the registration entry to receive an SVID.

SPIRE attestation is more granular and harder to spoof because it operates below the Kubernetes abstraction layer.

</details>

### Question 4
You deploy SPIRE and register a workload, but the pod logs show "no identity issued" when calling the Workload API. What are three things to check?

<details>
<summary>Show Answer</summary>

1. **Registration entry selectors**: Verify the entry's selectors (namespace, ServiceAccount, labels) match the pod's actual metadata. Use `spire-server entry show` to list entries and compare.

2. **SPIRE Agent is running on the node**: The Agent DaemonSet must have a pod scheduled on the same node as the workload. Check `kubectl get pods -n spire-system -o wide` and verify the Agent is running on the workload's node.

3. **Workload API socket is mounted**: The SPIFFE CSI driver must be installed and the pod must mount the volume. Verify the `csi.spiffe.io` volume is in the pod spec and the mount path matches what the application expects.

Other checks: ensure the parent ID in the registration entry matches the Agent's SPIFFE ID, and verify the SPIRE Server is healthy and reachable by the Agent.

</details>

---

## Hands-On Exercise

### Objective

Deploy SPIRE on a kind cluster, register two workloads with distinct SPIFFE IDs, verify that each receives a valid X.509-SVID, and confirm the certificate contents.

### Environment Setup

```bash
# Create a kind cluster
kind create cluster --name spire-lab

# Install SPIRE via Helm
helm repo add spire https://spiffe.github.io/helm-charts-hardened/
helm repo update
helm install spire spire/spire \
  --namespace spire-system \
  --create-namespace \
  --set global.spire.trustDomain=example.org \
  --set global.spire.clusterName=spire-lab \
  --wait --timeout 300s

# Verify SPIRE components are running
kubectl get pods -n spire-system
kubectl exec -n spire-system spire-server-0 -- \
  spire-server healthcheck
```

### Tasks

1. **Create two namespaces with ServiceAccounts**:
   ```bash
   kubectl create namespace payments
   kubectl create serviceaccount api-server -n payments
   kubectl create namespace orders
   kubectl create serviceaccount order-service -n orders
   ```

2. **Register both workloads with SPIRE**:
   ```bash
   # Get the agent's SPIFFE ID for the parentID
   AGENT_ID=$(kubectl exec -n spire-system spire-server-0 -- \
     spire-server agent list -output json | jq -r '.[0].id.path')

   kubectl exec -n spire-system spire-server-0 -- \
     spire-server entry create \
       -spiffeID spiffe://example.org/ns/payments/sa/api-server \
       -parentID spiffe://example.org${AGENT_ID} \
       -selector k8s:ns:payments \
       -selector k8s:sa:api-server \
       -ttl 3600

   kubectl exec -n spire-system spire-server-0 -- \
     spire-server entry create \
       -spiffeID spiffe://example.org/ns/orders/sa/order-service \
       -parentID spiffe://example.org${AGENT_ID} \
       -selector k8s:ns:orders \
       -selector k8s:sa:order-service \
       -ttl 3600
   ```

3. **Deploy test workloads** (use the YAML from the "Deploy a Test Workload" section, adapting for both namespaces).

4. **Verify SVIDs are issued**:
   ```bash
   # Check the payments workload
   kubectl exec -n payments deploy/api-server -- \
     /opt/spire/bin/spire-agent api fetch x509 \
       -socketPath /spiffe-workload-api/spire-agent.sock \
       -write /tmp/

   kubectl exec -n payments deploy/api-server -- \
     openssl x509 -in /tmp/svid.0.pem -text -noout
   ```

5. **Confirm the SPIFFE ID in the certificate SAN**:
   ```bash
   kubectl exec -n payments deploy/api-server -- \
     openssl x509 -in /tmp/svid.0.pem -text -noout \
     | grep -A1 "Subject Alternative Name"
   # Expected: URI:spiffe://example.org/ns/payments/sa/api-server
   ```

6. **List all registration entries**:
   ```bash
   kubectl exec -n spire-system spire-server-0 -- \
     spire-server entry show
   ```

### Success Criteria

- [ ] SPIRE Server and Agent pods are running in `spire-system`
- [ ] Two registration entries exist with distinct SPIFFE IDs
- [ ] The payments workload has an X.509-SVID with `spiffe://example.org/ns/payments/sa/api-server` in the SAN
- [ ] The orders workload has an X.509-SVID with `spiffe://example.org/ns/orders/sa/order-service` in the SAN
- [ ] Certificate TTL is 1 hour (3600 seconds)
- [ ] `spire-server healthcheck` returns healthy

### Bonus Challenge

Configure the SPIRE Server to use cert-manager as an upstream CA instead of the built-in self-signed CA. This integrates SPIRE into your existing PKI. Refer to the [SPIRE upstream authority documentation](https://spiffe.io/docs/latest/deploying/spire_server/#upstream-authority) and [Module 7.3: cert-manager](../platforms/module-7.3-cert-manager/).

---

## Further Reading

- [SPIFFE Specification](https://spiffe.io/docs/latest/spiffe-about/overview/)
- [SPIRE Documentation](https://spiffe.io/docs/latest/spire-about/)
- [SPIRE Helm Charts](https://github.com/spiffe/helm-charts-hardened)
- [go-spiffe Library](https://github.com/spiffe/go-spiffe) -- mTLS in a few lines of Go
- [CNCF SPIFFE Project Page](https://www.cncf.io/projects/spiffe/)
- [Module 5.2: Service Mesh](../networking/module-5.2-service-mesh/) -- Istio uses SPIFFE IDs internally
- [Module 7.3: cert-manager](../platforms/module-7.3-cert-manager/) -- Certificate lifecycle management
- CKS Exam: [Workload Identity](../../../k8s/cks/) -- ServiceAccount tokens and identity concepts

---

## Next Module

Return to the [Security Tools README]() to review all security toolkit modules, or continue to the [Networking Toolkit](../networking/) for service mesh and Cilium.

---

*"Identity is the new perimeter. If you cannot cryptographically prove who is talking to whom, your zero-trust architecture is just a PowerPoint slide."*
