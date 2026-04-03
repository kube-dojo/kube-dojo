---
title: "Module 8.2: Hybrid Cloud Connectivity"
slug: on-premises/resilience/module-8.2-hybrid-connectivity
sidebar:
  order: 3
---

> **Complexity**: `[ADVANCED]` | Time: 60 minutes
>
> **Prerequisites**: [Datacenter Networking](../../on-premises/networking/module-3.1-datacenter-networking/), [Module 8.1: Multi-Site & Disaster Recovery](../resilience/module-8.1-multi-site-dr/)

---

## Why This Module Matters

A global retail company ran customer-facing applications on AWS EKS but kept inventory management on-premises due to latency requirements -- warehouse scanners needed sub-5ms response times. For two years, their cloud and on-prem clusters operated as isolated islands with separate CI/CD pipelines, monitoring, service discovery, and network policies.

When a product launch required real-time inventory checks from the cloud storefront to the on-prem API, the team patched together public internet endpoints and manual firewall rules. It took six weeks and was fragile -- response times varied 40-400ms. During Black Friday, a BGP route leak by an upstream ISP made the endpoint unreachable for 47 minutes. The storefront showed "out of stock" for items sitting in warehouses.

The company then invested three months in proper hybrid connectivity: a dedicated interconnect, WireGuard tunnels, Submariner for cross-cluster service discovery, and Istio for unified traffic management. The next Black Friday ran without incident. Inventory API latency was a consistent 8ms.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** hybrid connectivity between on-premises and cloud Kubernetes clusters using dedicated interconnects and encrypted tunnels
2. **Configure** Submariner or Cilium ClusterMesh for cross-cluster service discovery and pod-to-pod communication
3. **Design** network architectures that provide consistent latency between on-premises and cloud workloads with proper failover
4. **Troubleshoot** hybrid connectivity issues including BGP route leaks, tunnel MTU problems, and cross-cluster DNS resolution failures

---

## What You'll Learn

- VPN tunnel options for on-prem to cloud (WireGuard and IPsec)
- Dedicated interconnect services (Direct Connect, ExpressRoute, Cloud Interconnect)
- Submariner for multi-cluster Kubernetes networking
- Istio service mesh spanning cloud and on-prem clusters
- Consistent policy enforcement with OPA/Gatekeeper across environments

---

## VPN Tunnels: WireGuard and IPsec

```
  On-Prem DC                              Cloud VPC
  ┌──────────────────┐                   ┌──────────────────┐
  │ Pod CIDR:         │                   │ Pod CIDR:         │
  │  10.244.0.0/16    │    Encrypted     │  10.100.0.0/16    │
  │                    │    Tunnel       │                    │
  │ ┌──────────────┐  │◄───────────────►│ ┌──────────────┐  │
  │ │ WireGuard GW │  │                  │ │ WireGuard GW │  │
  │ │ 203.0.113.10 │  │                  │ │ 198.51.100.5 │  │
  │ └──────────────┘  │                  │ └──────────────┘  │
  └──────────────────┘                   └──────────────────┘
```

| Factor | WireGuard | IPsec (IKEv2) |
|--------|-----------|---------------|
| **Code complexity** | ~4,000 lines | ~400,000 lines |
| **Performance** | 1-3 Gbps per core | 0.5-1.5 Gbps per core |
| **Latency overhead** | ~0.5ms | ~1-2ms |
| **Configuration** | Simple (key pair, endpoint, allowed IPs) | Complex (certs, proposals, policies) |
| **Cloud native support** | Manual setup | Native (AWS/Azure VPN Gateway) |
| **Key rotation** | Built-in (every 2 minutes) | Manual or via IKE rekey |

### WireGuard Configuration

```bash
# On the on-prem gateway node
apt-get install -y wireguard
wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key

cat > /etc/wireguard/wg0.conf <<EOF
[Interface]
Address = 10.200.0.1/24
ListenPort = 51820
PrivateKey = $(cat /etc/wireguard/private.key)
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT

[Peer]
PublicKey = <CLOUD_GATEWAY_PUBLIC_KEY>
Endpoint = 198.51.100.5:51820
AllowedIPs = 10.100.0.0/16, 172.20.0.0/16
PersistentKeepalive = 25
EOF

systemctl enable --now wg-quick@wg0

# Add routes for cross-cluster communication
ip route add 10.100.0.0/16 via 10.200.0.1 dev wg0
ip route add 172.20.0.0/16 via 10.200.0.1 dev wg0
```

---

## Dedicated Interconnects

VPN tunnels run over the public internet. Dedicated interconnects provide private, low-latency connections.

```
  On-Prem DC       Colocation Meet-Me Room     Cloud Provider
  ┌────────┐       ┌──────────────┐            ┌──────────┐
  │ Router │──────►│ Cross Connect│───────────►│ Cloud    │
  └────────┘ Dark  └──────────────┘  Private   │ Router   │
              Fiber                   Peering   └──────────┘
              1-100 Gbps
```

| Feature | AWS Direct Connect | Azure ExpressRoute | GCP Cloud Interconnect |
|---------|-------------------|-------------------|----------------------|
| **Bandwidth** | 1, 10, 100 Gbps | 50 Mbps - 100 Gbps | 10, 100 Gbps |
| **Latency** | <5ms typical | <5ms typical | <5ms typical |
| **Setup time** | 2-4 weeks | 2-4 weeks | 1-3 weeks |
| **Monthly cost (10G)** | ~$2,200/port | ~$5,000/port | ~$1,700/port |

**Use interconnect** when: >1 Gbps sustained traffic, <5ms latency required, or compliance demands a private path. **Use VPN** for <100 Mbps, non-critical, or DR-only traffic.

---

## Submariner: Multi-Cluster Networking

Submariner connects Kubernetes clusters so pods and services in one cluster can reach those in another, handling cross-cluster DNS, encrypted tunnels, and service discovery.

```
  Cluster A (On-Prem)                    Cluster B (Cloud)
  ┌──────────────────────┐              ┌──────────────────────┐
  │ Gateway Engine       │  IPsec /     │ Gateway Engine       │
  │ (tunnel endpoint)   ◄┼──tunnel────►┼─(tunnel endpoint)    │
  │                      │              │                      │
  │ Lighthouse (DNS)    ◄┼──svc sync──►┼─Lighthouse (DNS)     │
  │                      │              │                      │
  │ Pod: curl nginx.ns.  │              │ Pod: nginx (svc)     │
  │ svc.clusterset.local │              │                      │
  └──────────────────────┘              └──────────────────────┘
```

### Install Submariner

```bash
# Install subctl
curl -Ls https://get.submariner.io | VERSION=v0.18.0 bash

# Deploy broker and join clusters
kubectl config use-context on-prem-cluster
subctl deploy-broker
subctl join broker-info.subm --clusterid on-prem --natt=false --cable-driver libreswan

kubectl config use-context cloud-cluster
subctl join broker-info.subm --clusterid cloud --natt=true --cable-driver libreswan

# Export a service for cross-cluster access
subctl export service nginx-service -n production

# From the other cluster, reach it via:
#   nginx-service.production.svc.clusterset.local
subctl show all
```

**Requirements**: non-overlapping pod/service CIDRs, gateway nodes with routable IPs, UDP ports 500 and 4500 open, supported CNIs (Calico, Flannel, Canal, OVN-Kubernetes).

---

## Unified Service Mesh with Istio

Istio adds traffic management, observability, and mTLS security across clusters.

```
  On-Prem (Primary)                    Cloud (Remote)
  ┌────────────────────┐              ┌────────────────────┐
  │ istiod              │──config────►│ istiod (remote)    │
  │ East-West GW       ◄┼──mTLS─────►┼─East-West GW       │
  │ ┌────┐ ┌────┐      │              │ ┌────┐ ┌────┐     │
  │ │A v1│ │ B  │      │              │ │A v2│ │ C  │     │
  │ └────┘ └────┘      │              │ └────┘ └────┘     │
  └────────────────────┘              └────────────────────┘
  svc-A traffic: 80% on-prem (v1), 20% cloud (v2)
```

A shared root CA is required for cross-cluster mTLS. Without it, sidecars in different clusters cannot verify each other's certificates and all cross-cluster traffic fails with 503 errors even though network connectivity works.

### Setting Up Multi-Cluster Istio

```bash
# 1. Generate a shared root CA
mkdir -p certs
openssl req -new -x509 -nodes -days 3650 \
  -keyout certs/root-key.pem -out certs/root-cert.pem \
  -subj "/O=KubeDojo/CN=Root CA"

# 2. Create per-cluster intermediate CAs from the shared root
for CLUSTER in on-prem cloud; do
  openssl genrsa -out certs/${CLUSTER}-ca-key.pem 4096
  openssl req -new -key certs/${CLUSTER}-ca-key.pem \
    -out certs/${CLUSTER}-ca-csr.pem -subj "/O=KubeDojo/CN=${CLUSTER} CA"
  openssl x509 -req -days 3650 -CA certs/root-cert.pem -CAkey certs/root-key.pem \
    -set_serial "0x$(openssl rand -hex 8)" \
    -in certs/${CLUSTER}-ca-csr.pem -out certs/${CLUSTER}-ca-cert.pem
done

# 3. Install Istio on the primary cluster with the shared CA
kubectl create namespace istio-system
kubectl create secret generic cacerts -n istio-system \
  --from-file=ca-cert.pem=certs/on-prem-ca-cert.pem \
  --from-file=ca-key.pem=certs/on-prem-ca-key.pem \
  --from-file=root-cert.pem=certs/root-cert.pem \
  --from-file=cert-chain.pem=certs/on-prem-ca-cert.pem

istioctl install -y -f - <<EOF
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      meshID: kubedojo-mesh
      multiCluster:
        clusterName: on-prem
      network: on-prem-network
EOF
```

### Cross-Cluster Traffic Routing

```yaml
# VirtualService for weighted routing between on-prem and cloud
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: svc-a
  namespace: production
spec:
  hosts:
  - svc-a.production.svc.cluster.local
  http:
  - route:
    - destination:
        host: svc-a.production.svc.cluster.local
        subset: on-prem
      weight: 80
    - destination:
        host: svc-a.production.svc.cluster.local
        subset: cloud
      weight: 20
```

---

## Consistent Policy with OPA/Gatekeeper

When workloads span environments, policy drift is inevitable without enforcement.

```
  Git Repository (single source of truth)
  ├── no-privileged.yaml
  ├── allowed-registries.yaml
  └── require-resource-limits.yaml
           │
     ArgoCD syncs to both
     ┌─────┴─────┐
     ▼           ▼
  On-Prem     Cloud
  (identical) (identical)
```

```yaml
# ConstraintTemplate: enforce allowed image registries
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sallowedregistries
spec:
  crd:
    spec:
      names:
        kind: K8sAllowedRegistries
      validation:
        openAPIV3Schema:
          type: object
          properties:
            registries:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sallowedregistries
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not startswith(container.image, input.parameters.registries[_])
        msg := sprintf("Container '%v' uses image '%v' from unauthorized registry",
          [container.name, container.image])
      }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRegistries
metadata:
  name: allowed-registries
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    registries:
    - "registry.internal.example.com/"
    - "gcr.io/distroless/"
    - "registry.k8s.io/"
```

Sync policies to all clusters via ArgoCD Applications pointing to the same Git repository.

---

## Did You Know?

1. **WireGuard is in the Linux kernel since 5.6** (March 2020). Linus Torvalds called it a "work of art" compared to IPsec. At ~4,000 lines of code versus IPsec's ~400,000, its attack surface is dramatically smaller.

2. **AWS Direct Connect locations are not AWS datacenters.** They are colocation facilities (Equinix, CoreSite). Your router connects to an AWS router via a physical fiber patch cable in a shared "meet-me room."

3. **Submariner's name references submarine cables** connecting continents. Created by Rancher Labs (now SUSE), it is a CNCF Sandbox project supporting both IPsec and WireGuard as cable drivers.

4. **Istio's locality-aware load balancing** prefers local endpoints over remote ones automatically, reducing cross-cluster traffic by 60-80% in typical deployments.

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Overlapping pod CIDRs | Default CNIs use 10.244.0.0/16 | Plan unique CIDRs per cluster before deployment |
| Single VPN gateway | "We'll add HA later" | Deploy gateways in active-passive pairs from day one |
| Ignoring MTU in tunnels | Encapsulation adds 50-70 bytes | Set MTU to 1400 on tunnel interfaces |
| No encryption between clusters | "Private network" | Always encrypt; even private networks can be compromised |
| No shared root CA for Istio | Each cluster auto-generates its own | Create shared root CA before installing Istio |
| Manual per-cluster policies | "Only two clusters" | Use GitOps; drift begins with the first manual change |

---

## Quiz

### Question 1
On-prem K8s uses pod CIDR 10.244.0.0/16. Your EKS cluster also uses 10.244.0.0/16. What breaks when you connect them via WireGuard?

<details>
<summary>Answer</summary>

CIDR overlap. Traffic to 10.244.x.x routes locally instead of through the tunnel. Fix options: (1) Rebuild one cluster with a different CIDR (cleanest). (2) Use Submariner with Globalnet, which assigns virtual global IPs from a non-overlapping range. (3) NAT at the gateway (fragile, breaks source IP visibility). Lesson: always plan unique CIDRs across all clusters.
</details>

### Question 2
Your VPN tunnel has 50ms RTT and 200 Mbps. The DB team wants PostgreSQL streaming replication to cloud. What concerns should you raise?

<details>
<summary>Answer</summary>

(1) **Bandwidth**: A write-heavy DB generating 50-100 MB/s of WAL would saturate 200 Mbps. Lag grows unbounded. (2) **Latency**: Synchronous replication adds 50ms per transaction commit -- impractical at scale. (3) **Reliability**: VPN over internet has variable latency; reconnections cause lag spikes. Recommendations: upgrade to Direct Connect (1 Gbps+), use asynchronous replication, or consider logical replication for lower bandwidth.
</details>

### Question 3
Submariner is deployed. `curl nginx.production.svc.clusterset.local` fails with DNS error. Debugging steps?

<details>
<summary>Answer</summary>

(1) Check Submariner pods are Running: `kubectl get pods -n submariner-operator`. (2) Check ServiceExport exists on source cluster and ServiceImport on destination. (3) Verify Lighthouse plugin is in CoreDNS config. (4) Check `subctl show connections` for "connected" status. (5) Test full DNS name with `nslookup`. (6) Check for CIDR overlap if Globalnet is not enabled.
</details>

### Question 4
Why is a shared root CA necessary for Istio multi-cluster?

<details>
<summary>Answer</summary>

Istio uses mTLS between all sidecars. Cross-cluster, sidecar A presents a cert signed by Cluster A's CA. Sidecar B must verify that cert. Without a shared root CA, Cluster B does not trust Cluster A's CA, so the TLS handshake fails. Symptoms: `ping` works but Istio services return 503. Fix: generate one root CA, derive per-cluster intermediate CAs, distribute root-cert.pem to all clusters before installing Istio.
</details>

---

## Hands-On Exercise: Cross-Cluster Service Discovery

**Objective**: Connect two kind clusters with Submariner and access a service across clusters.

```bash
# 1. Create clusters with unique CIDRs
cat <<EOF | kind create cluster --name cluster-a --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  podSubnet: "10.10.0.0/16"
  serviceSubnet: "10.110.0.0/16"
nodes:
- role: control-plane
- role: worker
EOF

cat <<EOF | kind create cluster --name cluster-b --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  podSubnet: "10.20.0.0/16"
  serviceSubnet: "10.120.0.0/16"
nodes:
- role: control-plane
- role: worker
EOF

# 2. Deploy Submariner
curl -Ls https://get.submariner.io | VERSION=v0.18.0 bash
kubectl config use-context kind-cluster-a
subctl deploy-broker
subctl join broker-info.subm --clusterid cluster-a --natt=false
kubectl config use-context kind-cluster-b
subctl join broker-info.subm --clusterid cluster-b --natt=false

# 3. Deploy and export a service on cluster-b
kubectl create namespace web
kubectl create deployment nginx --image=nginx:1.27 -n web --replicas=2
kubectl expose deployment nginx -n web --port=80
subctl export service nginx -n web

# 4. Test from cluster-a
kubectl config use-context kind-cluster-a
kubectl run test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s http://nginx.web.svc.clusterset.local
```

### Success Criteria
- [ ] Two kind clusters with non-overlapping CIDRs
- [ ] Submariner broker deployed and both clusters joined
- [ ] nginx service exported from cluster-b
- [ ] curl from cluster-a reaches nginx on cluster-b
- [ ] `subctl show connections` shows "connected"

---

## Next Module

Continue to [Module 8.3: Cloud Repatriation & Migration](../resilience/module-8.3-cloud-repatriation/) to learn how to move workloads from cloud to on-premises, translating cloud services to their on-prem equivalents.
