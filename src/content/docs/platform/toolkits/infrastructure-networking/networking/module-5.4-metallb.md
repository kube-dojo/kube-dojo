---
title: "Module 5.4: MetalLB - Load Balancing for Bare-Metal Kubernetes"
slug: platform/toolkits/infrastructure-networking/networking/module-5.4-metallb
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: ~35 minutes

## The Dreaded "Pending" That Wouldn't Go Away

*Three weeks. Three weeks of LoadBalancer services stuck in Pending.*

```
[Week 1, Monday]
@platform-team  Just deployed our first on-prem Kubernetes cluster!
@platform-team  Moving the payment gateway from cloud to our datacenter.
@dev-lead       Sweet. I'll deploy the app. Same manifests as GKE, right?
@dev-lead       ...why is the Service stuck on <pending>?
@platform-team  Probably just needs a minute.

[Week 1, Friday]
@dev-lead       Still pending. I've restarted everything. Twice.
@platform-team  The YAML looks fine. It works on GKE.
@dev-lead       "Works on GKE" doesn't help me here.

[Week 2, Wednesday]
@dev-lead       I switched everything to NodePort. It's ugly but it works.
@platform-team  We now have 14 services on random high ports. The firewall
                team is going to love us.
@firewall-team  We do not love you.

[Week 3, Thursday]
@new-hire       Hey, has anyone heard of MetalLB?
@new-hire       It gives you LoadBalancer services on bare metal.
@platform-team  ...
@dev-lead       ...
@platform-team  Install it. Install it right now.

[Week 3, Thursday, 20 minutes later]
@new-hire       Done. All 14 services have external IPs.
@dev-lead       I'm buying you lunch for a month.
```

That new hire saved the team from an architectural dead end. The problem was never Kubernetes--it was that nobody told them LoadBalancer services need an external implementation, and clouds just hide that fact from you.

**What You'll Learn**:
- Why LoadBalancer services don't work on bare metal out of the box
- How MetalLB fills the gap with Layer 2 and BGP modes
- Configuring IP address pools, advertisements, and failover
- When to choose L2 vs BGP (and why it matters)
- Integrating MetalLB with Ingress controllers and Gateway API

**Prerequisites**:
- Kubernetes Services (ClusterIP, NodePort, LoadBalancer) -- see [CKA Module 3.1: Services](../../../../k8s/cka/part3-services-networking/module-3.1-services/)
- Basic networking concepts (IP addresses, ARP, TCP/IP)
- Helm basics for installation
- A kind or minikube cluster for the exercise

---

## Why This Module Matters

In the cloud, creating a LoadBalancer Service is magic. You write `type: LoadBalancer`, and within seconds, AWS gives you an ELB, GCP gives you a Network LB, Azure gives you a Load Balancer. Behind the scenes, a cloud controller manager talks to the provider API and provisions real infrastructure.

On bare metal, there is no cloud API. There is no magical load balancer fairy. When you create a LoadBalancer Service, Kubernetes dutifully sets the type and then waits. And waits. And waits. The EXTERNAL-IP column says `<pending>` forever, because nothing is listening for that request.

This is not a bug. It is by design. Kubernetes defines the *interface* (`type: LoadBalancer`), but the *implementation* is pluggable. Cloud providers ship their own. Bare metal ships nothing.

MetalLB is that missing piece. It watches for LoadBalancer Services, assigns IP addresses from a pool you define, and announces those IPs to the network so traffic can reach your cluster. It turns bare-metal Kubernetes into a first-class citizen for external traffic.

> **Did You Know?**
>
> 1. MetalLB was created by Google engineer Dave Anderson in 2017 because he was frustrated that his home lab cluster couldn't use LoadBalancer services. A personal itch became one of the most-used bare-metal Kubernetes tools in production.
>
> 2. As of v0.13, MetalLB uses custom resources (IPAddressPool, L2Advertisement, BGPAdvertisement) instead of a ConfigMap. Older tutorials still reference the ConfigMap approach--if you see `config` in a ConfigMap, you are reading outdated documentation.
>
> 3. Lightweight distributions like [k3s](../k8s-distributions/module-14.1-k3s/) and [k0s](../k8s-distributions/module-14.2-k0s/) ship with their own built-in load balancer (Klipper LB for k3s, for example). MetalLB is the standard choice when you need more control, BGP support, or are running upstream Kubernetes or kubeadm clusters.
>
> 4. MetalLB became a CNCF Sandbox project in 2021, signaling broad community adoption. Major companies including Equinix Metal and Scaleway run it in production to provide LoadBalancer services across thousands of bare-metal nodes.

---

## Part 1: Why Bare Metal Needs MetalLB

### The Cloud vs Bare-Metal Gap

```
CLOUD KUBERNETES                         BARE-METAL KUBERNETES
─────────────────                        ──────────────────────

  kubectl create svc                       kubectl create svc
  type: LoadBalancer                       type: LoadBalancer
         │                                        │
         ▼                                        ▼
  Cloud Controller Manager                 Nothing. Silence. Void.
         │                                        │
         ▼                                        ▼
  Cloud API provisions                     EXTERNAL-IP: <pending>
  a real load balancer                     ...forever
         │
         ▼
  EXTERNAL-IP: 34.120.x.x
```

The LoadBalancer service type is part of the Kubernetes specification, but the spec says nothing about *how* to implement it. That is the job of an external controller. In the cloud, the cloud-controller-manager handles it. On bare metal, you need MetalLB.

### What MetalLB Actually Does

MetalLB runs as a set of pods in your cluster and does two things:

1. **Address allocation** -- When a LoadBalancer Service is created, MetalLB assigns it an external IP from a pool you configure.
2. **Address advertisement** -- MetalLB announces that IP to the local network so that external clients can route traffic to it.

The "how" of advertisement is where MetalLB's two modes come in.

---

## Part 2: Layer 2 Mode -- Simple and Effective

### How It Works

In Layer 2 (L2) mode, MetalLB uses standard ARP (IPv4) or NDP (IPv6) to announce IP addresses. One node in the cluster becomes the "owner" of each service IP by responding to ARP requests for that address. All traffic for that IP flows to the owning node, which then uses kube-proxy (or Cilium) to distribute it to the backend pods.

```
LAYER 2 MODE
─────────────────────────────────────────────────────
  Client sends ARP: "Who has 192.168.1.240?"
         │
         ▼
  MetalLB speaker on Node 2 responds:
  "That's me! MAC: aa:bb:cc:dd:ee:ff"
         │
         ▼
  All traffic for 192.168.1.240 → Node 2
         │
         ▼
  kube-proxy on Node 2 distributes to backend pods
  (which may be on Node 1, Node 2, or Node 3)
```

### Speaker Election

MetalLB runs a "speaker" DaemonSet on every node. For each service IP, speakers use a deterministic hash to elect one node as the leader. Only the leader responds to ARP requests.

If the leader node goes down, the remaining speakers detect the failure and a new leader is elected. The new leader sends a gratuitous ARP to update the network's ARP caches, and traffic shifts to the new node. Failover typically takes 10-30 seconds depending on client ARP cache timeouts.

### L2 Mode Trade-offs

**Strengths**:
- Zero network infrastructure requirements--works on any flat L2 network
- No router configuration needed
- Dead simple to set up

**Weaknesses**:
- Single node bottleneck: all traffic for a service IP goes through one node
- Failover is not instant (ARP cache expiry)
- Does not scale horizontally for bandwidth-heavy services

---

## Part 3: BGP Mode -- Production-Grade Load Distribution

### How It Works

In BGP mode, MetalLB peers with your network routers using the Border Gateway Protocol. Every node establishes a BGP session with the router and announces service IPs. The router sees multiple paths to the same IP and uses ECMP (Equal-Cost Multi-Path) to distribute traffic across all announcing nodes.

```
BGP MODE
─────────────────────────────────────────────────────
  MetalLB speakers peer with Top-of-Rack router

  Node 1 ──BGP──▶ Router: "I can reach 192.168.1.240"
  Node 2 ──BGP──▶ Router: "I can reach 192.168.1.240"
  Node 3 ──BGP──▶ Router: "I can reach 192.168.1.240"

  Router ECMP table:
  192.168.1.240 → Node 1 (cost: 1)
                → Node 2 (cost: 1)
                → Node 3 (cost: 1)

  Traffic is distributed across all three nodes!
```

### Why BGP Matters for Production

With ECMP, traffic is spread evenly across nodes. There is no single-node bottleneck. If a node goes down, the BGP session drops and the router removes that path from its ECMP table within seconds. Failover is fast and clean, limited only by BGP hold timers (typically 3-10 seconds).

---

## Part 4: L2 vs BGP Decision Guide

| Criteria | Layer 2 | BGP |
|----------|---------|-----|
| **Network requirements** | Flat L2 network, no special hardware | BGP-capable router (ToR switch) |
| **Setup complexity** | Minimal | Requires router configuration |
| **Traffic distribution** | Single node per service | All nodes via ECMP |
| **Failover speed** | 10-30 seconds (ARP cache) | 3-10 seconds (BGP hold timer) |
| **Scalability** | Limited by single-node bandwidth | Scales with node count |
| **Best for** | Dev/test, small clusters, homelab | Production, high traffic |
| **Router config needed** | No | Yes (BGP peering, ECMP) |

**Rule of thumb**: Start with L2 mode. Move to BGP when you need horizontal traffic distribution or faster failover, and when your network team can configure BGP peering on the router.

---

## Part 5: Installation and Configuration

### Installing MetalLB via Helm

```bash
# Add the MetalLB Helm repo
helm repo add metallb https://metallb.github.io/metallb
helm repo update

# Install into its own namespace
helm install metallb metallb/metallb \
  --namespace metallb-system \
  --create-namespace \
  --wait
```

Verify the installation:

```bash
k get pods -n metallb-system
# NAME                                  READY   STATUS    RESTARTS
# metallb-controller-5f9bb7cdb-x7kfn   1/1     Running   0
# metallb-speaker-7gqrt                 1/1     Running   0
# metallb-speaker-kd4v2                 1/1     Running   0
# metallb-speaker-wn8bx                 1/1     Running   0
```

The **controller** handles IP allocation. The **speakers** (DaemonSet) handle network advertisement.

### Configuring an IP Address Pool (L2 Mode)

```yaml
# ip-address-pool.yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
    - 192.168.1.240-192.168.1.250   # Range of IPs to assign
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - default-pool
```

```bash
k apply -f ip-address-pool.yaml
```

That is it. Any LoadBalancer Service created in the cluster will now receive an IP from `192.168.1.240-192.168.1.250`.

### Configuring BGP Mode

```yaml
# bgp-config.yaml
apiVersion: metallb.io/v1beta2
kind: BGPPeer
metadata:
  name: router-peer
  namespace: metallb-system
spec:
  myASN: 64500         # Your cluster's AS number
  peerASN: 64501       # Your router's AS number
  peerAddress: 10.0.0.1 # Router IP
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: bgp-pool
  namespace: metallb-system
spec:
  addresses:
    - 10.0.100.0/24
---
apiVersion: metallb.io/v1beta1
kind: BGPAdvertisement
metadata:
  name: bgp-advert
  namespace: metallb-system
spec:
  ipAddressPools:
    - bgp-pool
```

---

## Part 6: Integration with Ingress and Gateway API

MetalLB does not replace Ingress controllers or Gateway API -- it complements them. A common production pattern:

```
                   MetalLB assigns external IP
                          │
                          ▼
Internet ──▶ LoadBalancer Service (e.g., 192.168.1.240)
                          │
                          ▼
              Ingress Controller (nginx, Traefik)
              or Gateway API (Envoy, Cilium)
                          │
                ┌─────────┼─────────┐
                ▼         ▼         ▼
            app-a       app-b     app-c
```

Your Ingress controller runs as a Deployment with a `type: LoadBalancer` Service. MetalLB gives that Service an external IP. The Ingress controller then routes traffic to backend services based on hostnames and paths.

This pattern works identically with Kubernetes [Gateway API](../../../../k8s/cka/part3-services-networking/module-3.5-gateway-api/)--the Gateway resource gets a LoadBalancer Service, and MetalLB assigns the IP.

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| IP pool overlaps with DHCP range | Two devices claim the same IP, intermittent connectivity | Coordinate with network team; use IPs outside the DHCP scope |
| Forgetting to create L2Advertisement or BGPAdvertisement | IPs are assigned but never announced; traffic cannot reach the cluster | Always pair an IPAddressPool with an advertisement resource |
| Using old ConfigMap-based configuration | Works on older versions but breaks on v0.13+ | Migrate to CRD-based config (IPAddressPool, L2Advertisement) |
| Running MetalLB alongside k3s Klipper LB | Both controllers fight over LoadBalancer services | Disable Klipper (`--disable servicelb`) before installing MetalLB |
| Expecting L2 mode to load-balance across nodes | All traffic hits a single node | Use BGP mode with ECMP for true multi-node distribution |
| IP pool exhaustion with no monitoring | New services get stuck on Pending again | Size your pool appropriately; set alerts on pool utilization |

---

## Quiz

Test your understanding before moving on.

**Q1: Why do LoadBalancer services stay "Pending" on bare-metal clusters?**

<details>
<summary>Show Answer</summary>

There is no cloud controller manager to provision an external load balancer. The LoadBalancer service type requires an external implementation to allocate and advertise IPs. On bare metal, nothing fulfills that role unless you install something like MetalLB.
</details>

**Q2: In L2 mode, what happens when the node owning a service IP goes down?**

<details>
<summary>Show Answer</summary>

The remaining MetalLB speakers detect the failure and elect a new leader node for that service IP. The new leader sends a gratuitous ARP to update network ARP caches and begins responding to ARP requests for the IP. Failover takes approximately 10-30 seconds depending on client ARP cache timeouts.
</details>

**Q3: Why might you choose BGP mode over L2 mode?**

<details>
<summary>Show Answer</summary>

BGP mode provides true load distribution across multiple nodes via ECMP, faster failover (3-10 seconds vs 10-30 seconds), and better scalability for high-traffic workloads. L2 mode funnels all traffic for a given service through a single node, which becomes a bottleneck at scale.
</details>

**Q4: You install MetalLB and create an IPAddressPool, but LoadBalancer services still show Pending. What did you forget?**

<details>
<summary>Show Answer</summary>

You forgot to create an L2Advertisement or BGPAdvertisement resource. An IPAddressPool alone only defines which IPs are available. You must also create an advertisement resource to tell MetalLB how to announce those IPs to the network.
</details>

**Q5: Your team runs k3s and wants to use MetalLB. What must you do first?**

<details>
<summary>Show Answer</summary>

Disable k3s's built-in Klipper LB by starting k3s with `--disable servicelb`. Otherwise, both MetalLB and Klipper will compete to handle LoadBalancer services, causing unpredictable behavior. See [Module 14.1: k3s](../k8s-distributions/module-14.1-k3s/) for details.
</details>

---

## Hands-On Exercise: MetalLB on kind

**Goal**: Deploy MetalLB in L2 mode on a kind cluster, create a LoadBalancer service, and reach it from your host.

**Time**: ~15 minutes

**Success Criteria**: `curl` returns a response from the service using the MetalLB-assigned external IP.

### Step 1: Create a kind Cluster

```bash
kind create cluster --name metallb-lab
```

### Step 2: Determine the kind Docker Network Range

kind runs inside Docker. We need IPs from the same Docker bridge network.

```bash
# Get the kind network subnet
docker network inspect kind -f '{{(index .IPAM.Config 0).Subnet}}'
# Example output: 172.18.0.0/16

# Pick an unused range within that subnet (e.g., 172.18.255.200-172.18.255.250)
```

### Step 3: Install MetalLB

```bash
helm repo add metallb https://metallb.github.io/metallb
helm repo update
helm install metallb metallb/metallb \
  --namespace metallb-system \
  --create-namespace \
  --wait
```

### Step 4: Configure IP Pool and L2 Advertisement

Adjust the IP range based on your kind network from Step 2:

```bash
kubectl apply -f - <<'EOF'
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: kind-pool
  namespace: metallb-system
spec:
  addresses:
    - 172.18.255.200-172.18.255.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: kind-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - kind-pool
EOF
```

### Step 5: Deploy a Test Application

```bash
k create deployment web --image=nginx --port=80
k expose deployment web --type=LoadBalancer --port=80
```

### Step 6: Verify the External IP

```bash
k get svc web
# NAME   TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE
# web    LoadBalancer   10.96.45.123   172.18.255.200   80:31234/TCP   10s
```

The EXTERNAL-IP should no longer say `<pending>`. If it does, wait a few seconds and check again.

### Step 7: Test Connectivity

```bash
curl http://172.18.255.200
# You should see the default nginx welcome page HTML
```

### Cleanup

```bash
kind delete cluster --name metallb-lab
```

If you completed this exercise successfully, you have just solved the exact problem that kept that team stuck for three weeks. Not bad for 15 minutes.

---

## Next Steps

- **[Module 5.1: Cilium](../module-5.1-cilium/)** -- MetalLB handles external traffic; Cilium handles everything inside the cluster
- **[Module 5.2: Service Mesh](../module-5.2-service-mesh/)** -- For mTLS and advanced traffic management after traffic enters the cluster
- **[CKA Module 3.1: Services](../../../../k8s/cka/part3-services-networking/module-3.1-services/)** -- Deep dive into Kubernetes service types
- **[CKA Module 3.5: Gateway API](../../../../k8s/cka/part3-services-networking/module-3.5-gateway-api/)** -- The next-generation Ingress that pairs well with MetalLB
- **[Module 14.1: k3s](../k8s-distributions/module-14.1-k3s/)** / **[Module 14.2: k0s](../k8s-distributions/module-14.2-k0s/)** -- Lightweight distros with built-in LB alternatives

---

*"The difference between a toy cluster and a production cluster is often just one missing component. MetalLB is that component for bare-metal load balancing."*
