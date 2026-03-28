---
title: "Module 1.5: Multi-Cluster & Hybrid Networking"
slug: platform/disciplines/networking/module-1.5-multi-cluster-networking
sidebar:
  order: 6
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 60-70 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: CNI Architecture](../module-1.1-cni-architecture/) — CNI fundamentals, especially Cilium
- **Required**: [Module 1.4: Ingress & Gateway API](../module-1.4-ingress-gateway/) — Gateway API, multi-cluster ingress concepts
- **Recommended**: [Module 1.3: Service Mesh Strategy](../module-1.3-service-mesh-strategy/) — Multi-cluster mesh patterns
- **Helpful**: Experience with multiple Kubernetes clusters, VPNs, or cloud VPCs

---

## Why This Module Matters

In June 2023, a global payments company ran two Kubernetes clusters — one in us-east-1 (AWS) and one in eu-west-1. Each cluster was self-contained, with its own databases, caches, and application stacks. The company's European customers were routing through the US cluster because a DNS misconfiguration in their global load balancer pointed `payments.example.com` to the US cluster only.

When the US cluster experienced a 40-minute outage (AZ failure in us-east-1a), European customers lost service entirely even though the EU cluster was perfectly healthy. The company had invested $800K building the second cluster for disaster recovery, but the networking layer — the piece that connects clusters and routes traffic intelligently — was an afterthought. The failover was manual, undocumented, and had never been tested.

Multi-cluster networking is not just about connecting clusters. It's about building a resilient service topology where traffic flows to the right cluster based on latency, availability, and business rules. This module covers the tools, patterns, and operational practices that make multi-cluster Kubernetes work in production.

---

## Did You Know?

> Cilium ClusterMesh can connect up to 255 clusters in a single mesh with a shared Pod identity system. Pods in any cluster can reach Pods in any other cluster using standard Kubernetes Service names, with no application changes. Each cluster maintains its own control plane — there is no single point of failure.

> Submariner (a CNCF Sandbox project) creates encrypted tunnels between clusters using IPsec or WireGuard. It supports non-overlapping and overlapping Pod CIDRs through its Globalnet component, which assigns unique "global" IPs to exported Services. This means you can connect clusters that were provisioned with the same default 10.244.0.0/16 range.

> The `external-dns` project can synchronize Kubernetes Service and Ingress resources with over 30 DNS providers (Route53, CloudFlare, Google Cloud DNS, Azure DNS, etc.). In a multi-cluster setup, external-dns creates DNS records that point to Services in each cluster, enabling simple DNS-based failover — if a cluster goes down, its external-dns stops updating, and DNS TTL expiry routes traffic to the healthy cluster.

> Google's GKE Multi-Cluster Services (MCS) API was proposed as a Kubernetes Enhancement Proposal (KEP-1645) and is being standardized as the `ServiceExport`/`ServiceImport` pattern. When GA, it will provide a vendor-neutral way for clusters to share Services, replacing the current vendor-specific approaches.

---

## Multi-Cluster Networking Models

### Model 1: Flat Networking (Shared Pod CIDR Space)

All clusters share a routable Pod network. Pods can reach each other directly by IP.

```
┌─────────────────────┐     ┌─────────────────────┐
│  Cluster A           │     │  Cluster B           │
│  Pods: 10.1.0.0/16  │     │  Pods: 10.2.0.0/16  │
│                      │     │                      │
│  ┌───┐     ┌───┐    │     │  ┌───┐     ┌───┐    │
│  │ P │     │ P │    │     │  │ P │     │ P │    │
│  │.1 │────→│.5 │    │     │  │.3 │     │.7 │    │
│  └───┘     └───┘    │     │  └───┘     └───┘    │
│       └──────────────┼─────┼──→                   │
│  Direct Pod-to-Pod   │     │  Direct Pod-to-Pod   │
└─────────────────────┘     └─────────────────────┘
         │                             │
         └──────────┬──────────────────┘
                    │
          VPC Peering / VPN / Direct Connect
          (non-overlapping CIDRs required)
```

**Requirements:**
- Non-overlapping Pod, Service, and Node CIDRs across all clusters
- Network connectivity (VPC peering, VPN, dedicated interconnect)
- Routing rules for cross-cluster Pod CIDRs

**Best for**: Clusters in the same cloud provider/region where VPC peering is simple.

### Model 2: Overlay Networking (Tunneled)

Cross-cluster traffic is encapsulated in tunnels. Pod CIDRs can overlap.

```
┌─────────────────────┐     ┌─────────────────────┐
│  Cluster A           │     │  Cluster B           │
│  Pods: 10.244.0.0/16│     │  Pods: 10.244.0.0/16│
│  (same CIDR!)        │     │  (same CIDR!)        │
│                      │     │                      │
│  ┌────────────────┐  │     │  ┌────────────────┐  │
│  │ Submariner GW  │──┼─────┼──│ Submariner GW  │  │
│  │ (IPsec/WG)     │  │     │  │ (IPsec/WG)     │  │
│  └────────────────┘  │     │  └────────────────┘  │
│  Globalnet: 242.x    │     │  Globalnet: 243.x    │
└─────────────────────┘     └─────────────────────┘
```

**Requirements:**
- A tunnel solution (Submariner, WireGuard mesh)
- Gateway nodes with connectivity to other clusters
- Higher latency than flat networking (encapsulation overhead)

**Best for**: Clusters with overlapping CIDRs, different cloud providers, or restricted network environments.

### Model 3: Service-Level Connectivity

Only Services (not individual Pods) are shared across clusters. Traffic goes through a gateway.

```
┌──────────────────────┐     ┌──────────────────────┐
│  Cluster A            │     │  Cluster B            │
│                       │     │                       │
│  ┌──────────────┐    │     │  ┌──────────────┐    │
│  │ api-service   │◄───┼─────┼──│ payment-svc   │    │
│  │ (ClusterIP)  │    │     │  │ (exported)    │    │
│  └──────────────┘    │     │  └──────────────┘    │
│        ▲              │     │                       │
│  ServiceImport        │     │  ServiceExport        │
│  (from Cluster B)     │     │  (to Cluster A)       │
└──────────────────────┘     └──────────────────────┘
```

**Requirements:**
- Multi-cluster service discovery (MCS API, Istio, Cilium ClusterMesh)
- Gateway or proxy for cross-cluster traffic
- Only exported Services are reachable, not all Pods

**Best for**: Security-conscious environments where you want explicit control over what's shared.

### Choosing the Right Model

| Factor | Flat | Overlay | Service-Level |
|--------|:----:|:-------:|:-------------:|
| CIDR overlap OK | No | Yes | N/A |
| Performance | Best | Good (-5-10%) | Good |
| Security posture | Low (all Pods reachable) | Medium | Highest |
| Complexity | Low | Medium | Medium-High |
| Cross-cloud | Needs VPN/peering | Works anywhere | Works anywhere |

---

## Tool Deep Dives

### Cilium ClusterMesh

ClusterMesh connects Cilium-managed clusters with a shared identity system and cross-cluster Service discovery.

```bash
# Prerequisites: Cilium installed on both clusters with unique cluster IDs
# Cluster A:
cilium install --cluster-name cluster-a --cluster-id 1 \
  --set cluster.name=cluster-a \
  --set cluster.id=1

# Cluster B:
cilium install --cluster-name cluster-b --cluster-id 2 \
  --set cluster.name=cluster-b \
  --set cluster.id=2

# Enable ClusterMesh on both clusters
cilium clustermesh enable --service-type LoadBalancer
# (Use NodePort if no LoadBalancer available)

# Wait for ClusterMesh API server to be ready
cilium clustermesh status --wait

# Connect the clusters
cilium clustermesh connect --destination-context cluster-b
```

**Sharing Services across clusters:**

```yaml
# In Cluster B: annotate the Service to be global
apiVersion: v1
kind: Service
metadata:
  name: payment-service
  namespace: production
  annotations:
    service.cilium.io/global: "true"
    # Optional: prefer local endpoints, fall back to remote
    service.cilium.io/affinity: "local"
spec:
  selector:
    app: payment
  ports:
    - port: 8080
```

Once annotated, Pods in Cluster A can reach `payment-service.production.svc.cluster.local` and traffic will be load balanced across endpoints in both clusters.

```bash
# Verify cross-cluster connectivity
cilium clustermesh status
# Shows: connected clusters, shared services, endpoint counts

# View cross-cluster endpoints
kubectl get ciliumendpoints -A | grep -i payment
```

### Submariner

Submariner creates IPsec or WireGuard tunnels between clusters and supports the Multi-Cluster Services (MCS) API.

```bash
# Install subctl CLI
curl -Ls https://get.submariner.io | VERSION=0.23.1 bash

# Deploy the broker (coordination component) on Cluster A
subctl deploy-broker --kubeconfig kubeconfig-cluster-a

# Join Cluster A to the broker
subctl join broker-info.subm --kubeconfig kubeconfig-cluster-a \
  --clusterid cluster-a \
  --nattport 4500

# Join Cluster B
subctl join broker-info.subm --kubeconfig kubeconfig-cluster-b \
  --clusterid cluster-b \
  --nattport 4500

# Verify connectivity
subctl show all
subctl verify --kubeconfig kubeconfig-cluster-a \
  --toconfig kubeconfig-cluster-b --only connectivity
```

**Exporting Services with MCS API:**

```yaml
# In Cluster B: export the service
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: payment-service
  namespace: production
```

```yaml
# In Cluster A: the ServiceImport is created automatically
# Pods can now reach:
#   payment-service.production.svc.clusterset.local
# (Note: .clusterset.local instead of .cluster.local)
```

```bash
# Verify service export
kubectl get serviceexport -n production
kubectl get serviceimport -n production  # On the consuming cluster
```

### Skupper (Application-Layer Connectivity)

Skupper uses an application-layer Virtual Application Network (VAN) to connect services without VPN or special network configuration.

```bash
# Install Skupper CLI
curl https://skupper.io/install.sh | sh

# In Cluster A: initialize Skupper
skupper init --site-name cluster-a

# In Cluster B: initialize and create a link token
skupper init --site-name cluster-b
skupper token create cluster-b-token.yaml

# In Cluster A: use the token to establish the link
skupper link create cluster-b-token.yaml

# In Cluster B: expose a service
skupper expose deployment payment-service --port 8080

# In Cluster A: the service is now accessible
kubectl get services  # payment-service appears as a local ClusterIP
```

**When Skupper shines**: connecting Kubernetes clusters to non-Kubernetes workloads (VMs, bare metal), or connecting clusters across restrictive firewalls where VPN setup is impossible.

### Tool Comparison

| Feature | Cilium ClusterMesh | Submariner | Skupper |
|---------|:--:|:--:|:--:|
| Max clusters | 255 | 20-30 (practical) | 50+ |
| Connectivity | Direct (flat or tunnel) | IPsec/WireGuard tunnel | AMQP application layer |
| Overlapping CIDRs | No | Yes (Globalnet) | Yes |
| Network policies cross-cluster | Yes | No | No |
| MCS API (ServiceExport) | No (own annotation) | Yes | No (own model) |
| Non-K8s workloads | No | No | Yes |
| Requires CNI change | Yes (Cilium) | No (any CNI) | No (any CNI) |
| Performance overhead | Minimal | 5-10% (tunnel) | 10-20% (app layer) |

---

## DNS-Based Service Discovery

### CoreDNS for Internal Discovery

Kubernetes uses CoreDNS for in-cluster DNS. For multi-cluster, you can configure CoreDNS to forward queries for other clusters:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
        }
        # Forward queries for cluster-b services to cluster-b's DNS
        cluster-b.local:53 {
            forward . 10.100.0.10   # Cluster B's CoreDNS IP
        }
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
```

### external-dns for Global Discovery

external-dns synchronizes Kubernetes resources with external DNS providers:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: external-dns
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: external-dns
  template:
    metadata:
      labels:
        app: external-dns
    spec:
      serviceAccountName: external-dns
      containers:
        - name: external-dns
          image: registry.k8s.io/external-dns/external-dns:v0.15.1
          args:
            - --source=service
            - --source=ingress
            - --source=gateway-httproute   # Gateway API support
            - --provider=aws               # or google, azure, cloudflare
            - --domain-filter=example.com
            - --aws-zone-type=public
            - --txt-owner-id=cluster-a     # Unique per cluster
            - --policy=upsert-only         # Don't delete records
```

### DNS-Based Failover Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  Route53 (weighted routing)                                  │
│  api.example.com                                             │
│    ├── 50% → cluster-a.api.example.com (us-east-1)          │
│    └── 50% → cluster-b.api.example.com (eu-west-1)          │
│                                                              │
│  Health checks:                                              │
│    cluster-a: GET /healthz → 200 ✓                           │
│    cluster-b: GET /healthz → 200 ✓                           │
│                                                              │
│  If cluster-a fails health check:                            │
│    100% → cluster-b.api.example.com                          │
└─────────────────────────────────────────────────────────────┘
```

```bash
# AWS Route53 health check + weighted routing
aws route53 create-health-check --caller-reference "cluster-a-$(date +%s)" \
  --health-check-config '{
    "IPAddress": "203.0.113.10",
    "Port": 443,
    "Type": "HTTPS",
    "ResourcePath": "/healthz",
    "RequestInterval": 10,
    "FailureThreshold": 3
  }'
```

---

## Hybrid Cloud Connectivity

### VPN Connectivity

```
┌──────────────────┐          ┌──────────────────┐
│  Cloud (AWS)      │          │  On-Prem DC       │
│  VPC: 10.0.0.0/16│          │  Net: 172.16.0.0/12│
│                   │          │                    │
│  K8s Cluster      │  IPsec   │  K8s Cluster       │
│  Pods: 10.1.0.0/16│←────────→│  Pods: 10.2.0.0/16 │
│                   │  VPN     │                    │
│  AWS VPN Gateway  │          │  On-prem VPN GW    │
└──────────────────┘          └──────────────────┘
```

**Key considerations:**
- **Non-overlapping CIDRs** — Plan CIDR allocation across all environments
- **Bandwidth** — VPN throughput is typically 1-5 Gbps; Direct Connect/ExpressRoute for more
- **Latency** — VPN adds 1-5ms per hop; measure and account for in timeout configs
- **Reliability** — Use redundant VPN tunnels; monitor tunnel state

### CIDR Planning Template

| Environment | Node CIDR | Pod CIDR | Service CIDR |
|-------------|-----------|----------|-------------|
| Cluster A (us-east-1) | 10.0.0.0/16 | 10.1.0.0/16 | 10.96.0.0/16 |
| Cluster B (eu-west-1) | 10.10.0.0/16 | 10.11.0.0/16 | 10.97.0.0/16 |
| Cluster C (on-prem) | 172.16.0.0/16 | 172.17.0.0/16 | 172.18.0.0/16 |

**Rules:**
1. No overlap between any CIDR ranges across all clusters
2. Reserve space for future clusters (don't use /8 ranges on a single cluster)
3. Document all CIDRs in a central registry
4. Use Submariner Globalnet if you cannot avoid overlap (legacy clusters)

---

## Troubleshooting Cross-Cluster Networking

### Diagnostic Checklist

```bash
# 1. Can nodes in Cluster A reach nodes in Cluster B?
ping <cluster-b-node-ip>

# 2. Is the tunnel/peering established?
# Submariner:
subctl show connections
# Cilium ClusterMesh:
cilium clustermesh status

# 3. Can Pods resolve cross-cluster DNS?
kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup payment-service.production.svc.clusterset.local

# 4. Can Pods reach cross-cluster Services?
kubectl run net-test --rm -it --image=nicolaka/netshoot --restart=Never -- \
  curl -v http://payment-service.production.svc.clusterset.local:8080/healthz

# 5. Check for MTU issues (common with tunnels)
kubectl run mtu-test --rm -it --image=nicolaka/netshoot --restart=Never -- \
  ping -M do -s 1400 <remote-pod-ip>
# If this fails but ping -s 1300 works, you have an MTU issue

# 6. Check firewall rules
# Submariner needs: UDP 4500 (IPsec NAT-T), UDP 4490 (tunnel)
# Cilium ClusterMesh needs: TCP 2379 (etcd), TCP 4240 (health)
```

### Common Cross-Cluster Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| DNS resolution fails for `.clusterset.local` | Submariner CoreDNS plugin not installed | Run `subctl diagnose all` |
| Intermittent timeouts on large payloads | MTU mismatch (tunnel overhead) | Set MTU to 1400 (VXLAN) or 1380 (IPsec) |
| Service reachable from one cluster but not the other | Asymmetric routing or missing return route | Check route tables on gateway nodes |
| ClusterMesh shows "connected" but Services not shared | Missing `service.cilium.io/global` annotation | Add annotation and verify endpoint sync |
| VPN tunnel flaps | Keep-alive timeout too aggressive | Increase DPD interval, check cloud provider VPN limits |

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using the same Pod CIDR on all clusters | Default kubeadm/kind uses 10.244.0.0/16 everywhere | Plan CIDRs before cluster creation; use Submariner Globalnet if already deployed |
| Not testing failover | "We have two clusters, so we're HA" | Schedule monthly failover drills; automate DNS failover with health checks |
| Running multi-cluster without monitoring cross-cluster latency | Teams monitor per-cluster metrics but not cross-cluster | Add cross-cluster latency probes (blackbox exporter) and SLOs |
| Opening all ports between clusters | "Just open everything for now" | Whitelist only required ports: 4240, 2379 (Cilium), 4500, 4490 (Submariner) |
| Ignoring DNS TTL in failover | High TTL means DNS failover takes minutes, not seconds | Set TTL to 30-60s for records used in failover |
| Not documenting which Services are exported | Cross-cluster dependencies become invisible | Maintain a registry of exported Services with ownership |

---

## Hands-On Exercises

### Exercise 1: Multi-Cluster with Cilium ClusterMesh (kind)

```bash
# Create two kind clusters
cat <<'EOF' > cluster-a.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.1.0.0/16"
  serviceSubnet: "10.96.0.0/16"
nodes:
  - role: control-plane
  - role: worker
EOF

cat <<'EOF' > cluster-b.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: "10.2.0.0/16"
  serviceSubnet: "10.97.0.0/16"
nodes:
  - role: control-plane
  - role: worker
EOF

kind create cluster --name cluster-a --config cluster-a.yaml
kind create cluster --name cluster-b --config cluster-b.yaml
```

**Task 1**: Install Cilium on both clusters with unique cluster IDs.

```bash
# Cluster A
cilium install --context kind-cluster-a --cluster-name cluster-a --cluster-id 1 \
  --set cluster.name=cluster-a --set cluster.id=1

# Cluster B
cilium install --context kind-cluster-b --cluster-name cluster-b --cluster-id 2 \
  --set cluster.name=cluster-b --set cluster.id=2

# Wait for ready
cilium status --context kind-cluster-a --wait
cilium status --context kind-cluster-b --wait
```

**Task 2**: Enable ClusterMesh and connect the clusters.

```bash
cilium clustermesh enable --context kind-cluster-a --service-type NodePort
cilium clustermesh enable --context kind-cluster-b --service-type NodePort

cilium clustermesh status --context kind-cluster-a --wait
cilium clustermesh status --context kind-cluster-b --wait

cilium clustermesh connect --context kind-cluster-a --destination-context kind-cluster-b
```

**Task 3**: Deploy a global service and verify cross-cluster access.

```bash
# Deploy service in Cluster B
kubectl --context kind-cluster-b create namespace shared
kubectl --context kind-cluster-b run echo-server -n shared \
  --image=hashicorp/http-echo:0.2.3 -- -listen=:8080 -text="from-cluster-b"
kubectl --context kind-cluster-b expose pod echo-server -n shared --port=8080

# Annotate as global
kubectl --context kind-cluster-b annotate service echo-server -n shared \
  service.cilium.io/global="true"

# Create matching namespace in Cluster A
kubectl --context kind-cluster-a create namespace shared

# Test from Cluster A
kubectl --context kind-cluster-a run test -n shared --rm -it --restart=Never \
  --image=busybox:1.36 -- wget -qO- http://echo-server.shared.svc.cluster.local:8080
# Expected: "from-cluster-b"
```

### Exercise 2: DNS-Based Failover Simulation

```bash
# Deploy the same service in BOTH clusters
kubectl --context kind-cluster-a create namespace app
kubectl --context kind-cluster-a run web -n app --image=hashicorp/http-echo:0.2.3 \
  -- -listen=:8080 -text="cluster-a"
kubectl --context kind-cluster-a expose pod web -n app --port=8080

kubectl --context kind-cluster-b create namespace app
kubectl --context kind-cluster-b run web -n app --image=hashicorp/http-echo:0.2.3 \
  -- -listen=:8080 -text="cluster-b"
kubectl --context kind-cluster-b expose pod web -n app --port=8080

# Annotate both as global with local affinity
for CTX in kind-cluster-a kind-cluster-b; do
  kubectl --context $CTX annotate service web -n app \
    service.cilium.io/global="true" \
    service.cilium.io/affinity="local"
done
```

**Task**: Simulate a failure in Cluster A and verify traffic fails over to Cluster B.

```bash
# From Cluster A, traffic goes to local first
kubectl --context kind-cluster-a run test -n app --rm -it --restart=Never \
  --image=busybox:1.36 -- wget -qO- http://web.app.svc.cluster.local:8080
# Expected: "cluster-a" (local affinity)

# Delete the local Pod to simulate failure
kubectl --context kind-cluster-a delete pod web -n app

# Test again — should fail over to Cluster B
kubectl --context kind-cluster-a run test2 -n app --rm -it --restart=Never \
  --image=busybox:1.36 -- wget -qO- http://web.app.svc.cluster.local:8080
# Expected: "cluster-b" (failover)
```

### Exercise 3: Cross-Cluster Troubleshooting

**Task**: Intentionally break cross-cluster connectivity and diagnose it.

```bash
# Break connectivity by removing the ClusterMesh annotation
kubectl --context kind-cluster-b annotate service echo-server -n shared \
  service.cilium.io/global-

# From Cluster A, try to reach the service
kubectl --context kind-cluster-a run test -n shared --rm -it --restart=Never \
  --image=busybox:1.36 -- wget --timeout=3 -qO- http://echo-server.shared.svc.cluster.local:8080
# Expected: timeout (no local endpoint, global annotation removed)

# Diagnose
cilium clustermesh status --context kind-cluster-a
kubectl --context kind-cluster-a get endpoints echo-server -n shared
# Shows: no endpoints (service not global anymore)

# Fix: re-add annotation
kubectl --context kind-cluster-b annotate service echo-server -n shared \
  service.cilium.io/global="true"
```

**Success Criteria:**
- [ ] Two kind clusters running with Cilium and ClusterMesh connected
- [ ] Global service accessible from both clusters
- [ ] Local affinity routing verified (traffic prefers local cluster)
- [ ] Failover tested by deleting local Pod
- [ ] Cross-cluster connectivity diagnosed and repaired

---

## War Story

**The CIDR Collision That Nobody Saw Coming**

A logistics company acquired a competitor in 2023. Both companies ran Kubernetes. Both used the default Pod CIDR: `10.244.0.0/16`. Both used the default Service CIDR: `10.96.0.0/12`. The merger integration plan called for connecting the two Kubernetes environments within 90 days so that applications could be gradually migrated.

**Timeline:**
- **Week 1**: Network team discovers the CIDR overlap. Every Pod IP in Company A's cluster could conflict with a Pod IP in Company B's cluster.
- **Week 3**: Team evaluates options: (A) rebuild one cluster with new CIDRs ($300K, 4 weeks downtime risk), (B) use Submariner Globalnet to NAT cross-cluster traffic.
- **Week 5**: Submariner Globalnet deployed. Each cluster gets a unique GlobalCIDR (242.0.0.0/16 and 243.0.0.0/16). Cross-cluster Services are assigned global IPs from these ranges.
- **Week 8**: Integration testing reveals that Globalnet adds 2-3ms of latency per request due to double NAT. The payments service, which makes 6 cross-cluster calls per transaction, sees 12-18ms of added latency — enough to breach SLOs.
- **Week 12**: Team decides to rebuild Company B's cluster with non-overlapping CIDRs during a weekend maintenance window. Total cost: $180K in engineering time plus $50K in cloud compute for the parallel environment.

**Lesson**: CIDR allocation is a foundational decision that is extremely expensive to change later. Treat it like a database schema migration — plan it carefully at the beginning, document it centrally, and reserve enough address space for future growth. If you're starting fresh, use /16 ranges from the RFC 5737 documentation space (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) for test clusters and unique /16 blocks from 10.0.0.0/8 for each production cluster.

---

## Knowledge Check

<details>
<summary>1. What are the three multi-cluster networking models, and when would you choose each?</summary>

(1) **Flat networking** — Direct Pod-to-Pod routing via VPC peering or VPN. Best for clusters in the same cloud provider with non-overlapping CIDRs. Lowest latency, simplest, but requires CIDR planning. (2) **Overlay networking** — Tunneled connectivity (IPsec/WireGuard) between gateway nodes. Best when CIDRs overlap or clusters are in different providers. Adds 5-10% overhead. (3) **Service-level connectivity** — Only exported Services are reachable, not all Pods. Best for security-conscious environments where you want explicit control. Medium complexity but highest security.
</details>

<details>
<summary>2. How does Cilium ClusterMesh handle cross-cluster service discovery?</summary>

Cilium ClusterMesh uses a shared etcd-based **ClusterMesh API server** that synchronizes endpoint information across clusters. When a Service is annotated with `service.cilium.io/global: "true"`, its endpoints are shared with all connected clusters. Pods in any cluster can resolve the Service using the standard `<name>.<namespace>.svc.cluster.local` DNS name. Cilium's eBPF dataplane routes traffic to the appropriate endpoint — local or remote — based on the affinity configuration. With `affinity: local`, local endpoints are preferred; remote endpoints are used only when no local endpoints are available.
</details>

<details>
<summary>3. What is Submariner's Globalnet feature and why does it exist?</summary>

Globalnet solves the **overlapping Pod CIDR problem**. When two clusters use the same Pod CIDR (e.g., both use 10.244.0.0/16), direct routing is impossible because the same IP could exist in both clusters. Globalnet assigns each cluster a unique "global" CIDR (e.g., 242.0.0.0/16). When a Service is exported, it gets a global IP from this range. Cross-cluster traffic is NATed: source Pod IP is translated to a global IP, routed to the remote cluster, then NATed again to the actual Pod IP. The trade-off is added latency from the double NAT.
</details>

<details>
<summary>4. Why is DNS TTL important for multi-cluster failover?</summary>

When a cluster fails, DNS-based failover removes or deprioritizes the failed cluster's DNS records. However, clients and resolvers cache DNS responses for the duration of the TTL (Time To Live). If TTL is 300 seconds (5 minutes), clients continue sending traffic to the failed cluster for up to 5 minutes after the DNS record is updated. For fast failover, set TTL to 30-60 seconds. The trade-off is more DNS queries (higher load on DNS infrastructure and slightly higher latency for initial resolutions).
</details>

<details>
<summary>5. Scenario: You need to connect an on-premises Kubernetes cluster to an EKS cluster in AWS. The on-prem cluster uses 10.244.0.0/16 for Pods, and EKS uses the same range (aws-vpc-cni assigns VPC IPs, but you also have a secondary CIDR of 10.244.0.0/16). What are your options?</summary>

Three options: (1) **Submariner with Globalnet** — handles the CIDR overlap through NAT. Fastest to deploy but adds latency. (2) **Rebuild one cluster** with non-overlapping CIDRs. Best long-term but requires downtime or blue-green migration. (3) **Skupper** — operates at the application layer, so IP overlap doesn't matter. Services are exposed individually. Lower performance but simplest network-wise. For EKS specifically, consider switching to VPC-native IPs only (no secondary CIDR) and using Skupper or Submariner Globalnet for the cross-environment link.
</details>

<details>
<summary>6. What firewall ports need to be opened for Cilium ClusterMesh between two clusters?</summary>

Cilium ClusterMesh requires: (1) **TCP 2379** — etcd (ClusterMesh API server) for synchronizing endpoint and identity data between clusters. (2) **TCP 4240** — Cilium health checks between nodes. (3) **UDP 8472** (VXLAN) or **UDP 51871** (WireGuard) — for actual Pod-to-Pod data traffic, depending on the tunnel mode. (4) **TCP 4244** — Hubble relay, if using Hubble across clusters. Additionally, if using NodePort for the ClusterMesh API server, the assigned NodePort (typically 32379) must be reachable.
</details>

<details>
<summary>7. How does external-dns enable multi-cluster failover without any multi-cluster networking tool?</summary>

external-dns runs in each cluster and creates DNS records for Services/Ingresses. For failover: (1) Deploy the same Service in both clusters with the same hostname. (2) Configure external-dns with a unique `--txt-owner-id` per cluster so they don't conflict. (3) Use a DNS provider that supports health checks and weighted routing (Route53, Cloudflare). (4) Configure health checks for each cluster's endpoint. When a cluster goes down, its health check fails, and the DNS provider stops routing traffic to it. This provides cluster-level failover without any cross-cluster networking — each cluster operates independently. The limitation is that it only works for external traffic (ingress), not east-west Pod-to-Pod traffic.
</details>

<details>
<summary>8. What is the biggest risk of not planning CIDR allocation before deploying multiple clusters?</summary>

The biggest risk is **CIDR overlap**, which makes direct cross-cluster networking impossible and forces you into overlay solutions (Submariner Globalnet, Skupper) that add latency and complexity. Changing a cluster's Pod CIDR after deployment is effectively a full rebuild — you must drain all nodes, reconfigure the CNI, and recreate all Pods. For a production cluster with hundreds of services, this is a multi-day operation with significant outage risk. The cost of fixing CIDR overlap retroactively is 10-100x higher than planning it correctly from the start. Always maintain a centralized CIDR registry and allocate non-overlapping ranges for every cluster.
</details>

---

## Summary

Multi-cluster and hybrid networking extends Kubernetes beyond a single cluster boundary. The key decisions are:

1. **Choose your connectivity model** — flat (performance), overlay (flexibility), or service-level (security)
2. **Plan CIDRs first** — non-overlapping ranges across all clusters. This is the most important networking decision you'll make.
3. **Use the right tool** — Cilium ClusterMesh for Cilium shops, Submariner for CNI-agnostic clusters, Skupper for hybrid/non-K8s integration
4. **DNS is your failover mechanism** — external-dns + health checks for cluster-level failover, CoreDNS configuration for internal cross-cluster discovery
5. **Test failover regularly** — having two clusters is not HA until you've proven traffic shifts correctly when one fails

Multi-cluster networking is hard because it touches every layer — DNS, routing, encryption, identity, and service discovery. But it's essential for any organization running Kubernetes at scale or across regions.

## What's Next

Congratulations on completing the Kubernetes Networking discipline. You now have a comprehensive understanding of how traffic flows into, within, and between Kubernetes clusters.

**Recommended next tracks:**
- [SRE Discipline](../../disciplines/sre/) — Apply networking knowledge to reliability engineering
- [DevSecOps Discipline](../../disciplines/devsecops/) — Secure the networking layer in CI/CD
- [Service Mesh Toolkit](../../toolkits/service-mesh/) — Deep dive into specific mesh implementations
