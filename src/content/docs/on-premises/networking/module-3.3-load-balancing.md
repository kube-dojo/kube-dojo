---
title: "Module 3.3: Load Balancing Without Cloud"
slug: on-premises/networking/module-3.3-load-balancing
sidebar:
  order: 4
---

> **Complexity**: `[MEDIUM]` | Time: 60 minutes
>
> **Prerequisites**: [Module 3.2: BGP & Routing](../module-3.2-bgp-routing/), [MetalLB](../../platform/toolkits/infrastructure-networking/networking/module-5.4-metallb/)

---

## Why This Module Matters

When you create a Kubernetes Service of type `LoadBalancer` on AWS, an ALB or NLB appears within seconds. On bare metal, nothing happens. The Service stays in `Pending` forever because there is no cloud controller to provision a load balancer. Your Kubernetes cluster does not have the concept of "allocate a public IP and route traffic to my pods."

This is the single biggest operational gap between cloud and on-premises Kubernetes. Every application that needs external access — APIs, web frontends, gRPC services — needs a load balancing solution. On bare metal, you have three options: MetalLB (software-defined L2/BGP load balancer), kube-vip (lightweight VIP manager), or external hardware/software load balancers (HAProxy, Nginx, F5).

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Deploy** MetalLB in both L2 and BGP mode to provide LoadBalancer services on bare-metal Kubernetes
2. **Configure** external load balancers (HAProxy, Nginx, F5) to front Kubernetes Ingress controllers
3. **Design** a high-availability load balancing architecture with VIP failover and health checking
4. **Evaluate** L2 vs. BGP vs. external hardware load balancing tradeoffs for different traffic patterns and scale requirements

---

## What You'll Learn

- Why `type: LoadBalancer` does not work on bare metal by default
- MetalLB: L2 mode vs BGP mode and when to use each
- kube-vip: lightweight alternative for API server HA and service VIPs
- HAProxy + Keepalived: external load balancer for ingress
- How to combine these for a production architecture
- Common pitfalls and failure modes

---

## The LoadBalancer Problem

```
┌─────────────────────────────────────────────────────────────┐
│          SERVICE TYPE: LOADBALANCER                          │
│                                                               │
│  ON CLOUD (AWS/GCP/Azure):                                  │
│  kubectl create svc loadbalancer → Cloud Controller         │
│    → Creates ALB/NLB/Azure LB automatically                │
│    → Assigns external IP                                    │
│    → Routes traffic to node ports                           │
│    → Health checks, scaling, TLS termination               │
│    → Cost: $15-25/month per LB                             │
│                                                               │
│  ON BARE METAL:                                              │
│  kubectl create svc loadbalancer → ??? (no cloud controller)│
│    → Service stays "Pending" forever                        │
│    → No external IP assigned                                │
│    → No traffic reaches the service                         │
│                                                               │
│  SOLUTION:                                                    │
│  Install MetalLB (or kube-vip) to act as the LB controller │
│    → Assigns IPs from a configured pool                     │
│    → Announces IPs via L2 (ARP) or BGP                     │
│    → Traffic reaches nodes → kube-proxy → pods             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## MetalLB

MetalLB is the de facto standard load balancer for bare metal Kubernetes. It assigns external IPs to `LoadBalancer` services and announces them on the network.

### L2 Mode vs BGP Mode

```
┌─────────────────────────────────────────────────────────────┐
│              METALLB MODES                                   │
│                                                               │
│  L2 MODE (ARP/NDP):                                        │
│  ┌──────────────────────────────────┐                       │
│  │  One node responds to ARP for    │                       │
│  │  the VIP. All traffic goes to    │                       │
│  │  that single node.               │                       │
│  │                                  │                       │
│  │  Client → ARP "who has 10.0.50.1?" │                     │
│  │  Node 3 → "I do!" (elected leader)│                     │
│  │  Client → sends all traffic to    │                       │
│  │           Node 3 → kube-proxy     │                       │
│  │           → pods on any node      │                       │
│  └──────────────────────────────────┘                       │
│                                                               │
│  ✓ Simple: no switch configuration needed                   │
│  ✓ Works in any L2 network                                  │
│  ✗ Single node bottleneck (all traffic through one node)    │
│  ✗ Failover takes 10-30 seconds (gratuitous ARP)           │
│  ✗ No true load distribution across nodes                   │
│                                                               │
│  BGP MODE:                                                   │
│  ┌──────────────────────────────────┐                       │
│  │  All nodes announce the VIP via  │                       │
│  │  BGP. Switch uses ECMP to spread │                       │
│  │  traffic across multiple nodes.  │                       │
│  │                                  │                       │
│  │  Node 1 → BGP: "I have 10.0.50.1"│                      │
│  │  Node 2 → BGP: "I have 10.0.50.1"│                      │
│  │  Node 3 → BGP: "I have 10.0.50.1"│                      │
│  │  Switch → ECMP: split traffic    │                       │
│  │           across all 3 nodes     │                       │
│  └──────────────────────────────────┘                       │
│                                                               │
│  ✓ True load distribution across multiple nodes             │
│  ✓ Fast failover (BGP convergence: 1-3 seconds)           │
│  ✓ Scales with cluster size                                 │
│  ✗ Requires BGP-capable switches (most enterprise do)      │
│  ✗ Switch configuration needed                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: You create a Service of type LoadBalancer on your bare-metal cluster. It stays in "Pending" forever. Before reading the solution below, explain what is missing and why this works automatically on AWS but not on bare metal.

### MetalLB Installation and Configuration

```bash
# Install MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml

# Wait for MetalLB pods
kubectl wait --namespace metallb-system \
  --for=condition=Ready pod \
  --selector=app=metallb \
  --timeout=120s
```

### L2 Mode Configuration

```yaml
# IP address pool
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: external-pool
  namespace: metallb-system
spec:
  addresses:
    - 10.0.50.10-10.0.50.50  # 41 external IPs available

---
# L2 advertisement
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: external
  namespace: metallb-system
spec:
  ipAddressPools:
    - external-pool
  interfaces:
    - bond0  # Only respond on the production bond
```

> **Stop and think**: L2 mode sends all traffic through a single elected node. For a service handling 500 requests/second, this might be fine. But what if the service handles 50,000 requests/second at 1KB each -- that is 400 Mbps through a single node. At what point does this single-node bottleneck become a problem, and how does BGP mode solve it?

### BGP Mode Configuration

BGP mode eliminates the single-node bottleneck by having every node announce the VIP via BGP. The upstream switch uses ECMP (Equal-Cost Multi-Path) to distribute traffic across all announcing nodes, giving you true horizontal scaling of ingress bandwidth:

```yaml
# IP address pool
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: external-pool
  namespace: metallb-system
spec:
  addresses:
    - 10.0.50.10-10.0.50.50

---
# BGP advertisement
apiVersion: metallb.io/v1beta1
kind: BGPAdvertisement
metadata:
  name: external-bgp
  namespace: metallb-system
spec:
  ipAddressPools:
    - external-pool
  peers:
    - rack-a-tor

---
# BGP peer (ToR switch)
apiVersion: metallb.io/v1beta1
kind: BGPPeer
metadata:
  name: rack-a-tor
  namespace: metallb-system
spec:
  myASN: 64512
  peerASN: 64501
  peerAddress: 10.0.20.1
  nodeSelectors:
    - matchLabels:
        rack: rack-a
```

### Test LoadBalancer Service

```bash
# Create a test deployment
kubectl create deployment nginx --image=nginx --replicas=3

# Expose as LoadBalancer
kubectl expose deployment nginx --type=LoadBalancer --port=80

# Check external IP assignment
kubectl get svc nginx
# NAME    TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# nginx   LoadBalancer   10.96.45.123   10.0.50.10    80:31234/TCP   5s

# Test access
curl http://10.0.50.10
# <!DOCTYPE html>...
```

---

## kube-vip

kube-vip is a lightweight alternative that provides both API server HA (virtual IP for the control plane) and service load balancing:

```yaml
# kube-vip as static pod for API server HA
apiVersion: v1
kind: Pod
metadata:
  name: kube-vip
  namespace: kube-system
spec:
  hostNetwork: true
  containers:
    - name: kube-vip
      image: ghcr.io/kube-vip/kube-vip:v0.8.7
      args:
        - manager
      env:
        - name: vip_arp
          value: "true"
        - name: vip_interface
          value: bond0
        - name: address
          value: "10.0.20.100"  # Virtual IP for API server
        - name: port
          value: "6443"
        - name: vip_leaderelection
          value: "true"
        - name: svc_enable
          value: "true"  # Also handle LoadBalancer services
        - name: svc_election
          value: "true"
```

### kube-vip vs MetalLB

| Feature | kube-vip | MetalLB |
|---------|----------|---------|
| API server VIP | Yes (primary use case) | No |
| Service LB | Yes (basic) | Yes (full featured) |
| BGP mode | Yes | Yes |
| L2 mode | Yes (ARP) | Yes (ARP/NDP) |
| ECMP | No | Yes (via BGP) |
| IP pools | Basic | Advanced (per-namespace, auto-assign) |
| Community | Smaller | Larger, CNCF Sandbox |
| Best for | API server HA + simple LB | Production service load balancing |

**Common pattern**: Use kube-vip for API server HA VIP + MetalLB for service load balancing.

---

## External Load Balancers

For high-traffic production environments, an external load balancer in front of the K8s ingress provides:

```
┌─────────────────────────────────────────────────────────────┐
│         EXTERNAL LB ARCHITECTURE                             │
│                                                               │
│  Internet / Corporate Network                                │
│         │                                                    │
│    ┌────▼────┐                                              │
│    │ HAProxy │ (or F5, Nginx, Traefik)                      │
│    │ + Keep  │                                              │
│    │ alived  │ ← VIP: 10.0.50.1 (floats between 2 LBs)    │
│    └────┬────┘                                              │
│         │                                                    │
│    ┌────▼─────────────────────────────┐                     │
│    │      K8s Ingress Controllers     │                     │
│    │   (running on worker nodes)      │                     │
│    │                                  │                     │
│    │  ┌────────┐ ┌────────┐ ┌──────┐ │                     │
│    │  │Ingress │ │Ingress │ │Ingress│ │                     │
│    │  │Node 1  │ │Node 2  │ │Node 3│ │                     │
│    │  └────────┘ └────────┘ └──────┘ │                     │
│    └──────────────────────────────────┘                     │
│                                                               │
│  HAProxy health-checks each ingress node                    │
│  Keepalived provides VIP failover between 2 HAProxy         │
│  instances (active/standby)                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: You need to expose your Kubernetes API server for external kubectl access, route HTTPS traffic to your ingress controller, and provide a VIP that survives node failures. Which combination of kube-vip, MetalLB, and HAProxy would you use for each requirement?

### HAProxy Configuration

The HAProxy configuration below serves two purposes: it load-balances Kubernetes API server traffic across all control plane nodes (with health checking), and it fronts the ingress controller pods for HTTP/HTTPS traffic. The `check-ssl verify none` option on the API backend tells HAProxy to verify the backend is alive via HTTPS without validating the certificate (since K8s uses self-signed certs for health endpoints):

```bash
# /etc/haproxy/haproxy.cfg
global
    maxconn 50000
    log /dev/log local0

defaults
    mode tcp
    timeout connect 5s
    timeout client 30s
    timeout server 30s

# K8s API server load balancing
frontend k8s-api
    bind *:6443
    default_backend k8s-api-backend

backend k8s-api-backend
    option httpchk GET /healthz
    http-check expect status 200
    server cp-01 10.0.20.10:6443 check check-ssl verify none
    server cp-02 10.0.20.11:6443 check check-ssl verify none
    server cp-03 10.0.20.12:6443 check check-ssl verify none

# HTTP ingress
frontend http-ingress
    bind *:80
    default_backend ingress-http-backend

# HTTPS ingress (TLS passthrough to ingress controller)
frontend https-ingress
    bind *:443
    default_backend ingress-https-backend

backend ingress-http-backend
    balance roundrobin
    option httpchk GET /healthz
    server ingress-01 10.0.20.50:80 check
    server ingress-02 10.0.20.51:80 check
    server ingress-03 10.0.20.52:80 check

backend ingress-https-backend
    balance roundrobin
    server ingress-01 10.0.20.50:443 check port 80
    server ingress-02 10.0.20.51:443 check port 80
    server ingress-03 10.0.20.52:443 check port 80
```

---

## Production Architecture: Putting It All Together

```
┌─────────────────────────────────────────────────────────────┐
│         COMPLETE ON-PREM LB ARCHITECTURE                    │
│                                                               │
│  kube-vip:     API server VIP (10.0.20.100:6443)           │
│                Floats between 3 CP nodes                    │
│                                                               │
│  MetalLB:      Service LoadBalancer IPs (10.0.50.10-50)    │
│  (BGP mode)    Announced to ToR switches via BGP            │
│                ECMP across all nodes running the service    │
│                                                               │
│  HAProxy:      External ingress (optional, for high traffic)│
│  + Keepalived  VIP 10.0.50.1, health checks ingress nodes  │
│                TLS termination, rate limiting, WAF          │
│                                                               │
│  Ingress       Nginx Ingress Controller or Cilium Gateway   │
│  Controller:   Running on dedicated ingress nodes            │
│                Routes HTTP/gRPC to backend services         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **MetalLB was created because no cloud-equivalent existed** for bare metal. It started as a Google side project by David Anderson in 2017 and became a CNCF Sandbox project in 2021. Before MetalLB, the only options were NodePort (ugly), HostNetwork (limited), or expensive hardware load balancers.

- **L2 mode failover is slow because of ARP caching.** When the MetalLB leader fails, the new leader sends a gratuitous ARP to update the MAC table. But switches and routers cache ARP entries for 30-300 seconds. Until the cache expires, traffic goes to the old (dead) node. BGP mode avoids this entirely — route withdrawal is 1-3 seconds.

- **F5 BIG-IP costs $15,000-$100,000+ per appliance** depending on throughput and features. Many organizations use F5 for their on-prem ingress because "that's what we've always used." MetalLB + Nginx Ingress provides equivalent functionality for $0 in software cost.

- **kube-vip was created by Dan Finneran** specifically to solve the "chicken and egg" problem of API server HA. You need Kubernetes to run MetalLB, but you need a VIP to access Kubernetes. kube-vip runs as a static pod that starts before the cluster is fully operational.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using L2 mode at scale | Single-node bottleneck, slow failover | Use BGP mode for production |
| IP pool on wrong subnet | MetalLB VIPs unreachable from clients | VIP subnet must be routable from client network |
| No health checks on HAProxy | Traffic sent to dead ingress nodes | Always configure HTTP health checks |
| Overlapping IP pools | Multiple MetalLB instances assign same IP | Coordinate pools across clusters |
| Missing kube-vip for API | No HA for API server endpoint | Deploy kube-vip as static pod on all CP nodes |
| NodePort as permanent solution | Ports 30000-32767, non-standard | Invest in MetalLB or external LB |
| Single HAProxy (no Keepalived) | HAProxy failure = total ingress outage | Always pair HAProxy with Keepalived VIP |

---

## Quiz

### Question 1
You deploy MetalLB in L2 mode. Your service gets external IP 10.0.50.10. Only one of your 10 nodes is actually receiving the traffic. Is this normal?

<details>
<summary>Answer</summary>

**Yes, this is normal for L2 mode.** In L2 mode, MetalLB elects a single node as the "leader" for each VIP. That node responds to ARP requests for 10.0.50.10, so all traffic is sent to that one node. The node then uses kube-proxy to distribute traffic to pods across the cluster.

This is the fundamental limitation of L2 mode — it is a single-node bottleneck. If that node can handle the traffic, it works fine. If not, switch to BGP mode where all nodes announce the VIP and the switch uses ECMP to spread traffic.

For most services, L2 mode is fine. For high-throughput services (>10 Gbps), use BGP mode.
</details>

### Question 2
Your MetalLB BGP advertisement shows the VIP is announced to the ToR switch, but external clients cannot reach it. What do you check?

<details>
<summary>Answer</summary>

Debug checklist:

1. **Is the VIP subnet routable?** Check that the ToR switch has a route for 10.0.50.0/24 and is advertising it to upstream routers.

2. **Is the switch receiving the BGP route?** On the switch: `show bgp ipv4 unicast 10.0.50.10`. If no route, the BGP session may be down.

3. **Is MetalLB BGP session established?** `kubectl get bgppeer -n metallb-system -o yaml` — check session state.

4. **Is there a firewall blocking the traffic?** Check ACLs on the switch and any intermediate firewalls.

5. **Is kube-proxy running on the nodes?** MetalLB delivers traffic to the node, but kube-proxy forwards it to the pod. If kube-proxy is down, the node accepts the connection but drops it.

6. **Is the service endpoint healthy?** `kubectl get endpoints <svc-name>` — are there pods backing the service?

7. **Is the switch doing ECMP?** If ECMP is not configured, the switch may only send traffic to one next-hop even if multiple nodes announce the VIP.
</details>

### Question 3
Why would you use an external HAProxy instead of just MetalLB for your production ingress?

<details>
<summary>Answer</summary>

MetalLB provides L4 (TCP/UDP) load balancing — it assigns IPs and routes packets to nodes. It does not provide:

1. **TLS termination**: MetalLB passes raw TCP. HAProxy can terminate TLS, offloading certificate management from the ingress controller.

2. **L7 routing**: MetalLB cannot inspect HTTP headers, URLs, or cookies. HAProxy can route based on Host header, path, or other L7 attributes.

3. **Rate limiting / WAF**: MetalLB has no application-layer features. HAProxy can rate limit, block IPs, and integrate with WAF rules.

4. **Connection draining**: HAProxy gracefully drains connections during backend changes. MetalLB's BGP route withdrawal is abrupt.

5. **Centralized monitoring**: HAProxy provides detailed connection metrics, error rates, and response times. MetalLB only provides basic IP assignment metrics.

**Common architecture**: MetalLB assigns a VIP to the ingress controller (Nginx/Envoy). HAProxy sits in front as an additional layer for TLS termination, WAF, and enterprise requirements. For smaller deployments, MetalLB + Nginx Ingress is sufficient.
</details>

### Question 4
Your Kubernetes API server is at 10.0.20.10:6443 (single CP node). What happens if this node fails, and how does kube-vip solve it?

<details>
<summary>Answer</summary>

**Without kube-vip**: If 10.0.20.10 fails, all kubectl commands fail, all controllers lose API access, and no new scheduling occurs. The other CP nodes (10.0.20.11, 10.0.20.12) have working API servers but nothing is pointing at them. You must manually update kubeconfig and all references to the API server endpoint.

**With kube-vip**: A virtual IP (e.g., 10.0.20.100) floats between all CP nodes. kubeconfig points to 10.0.20.100:6443, not any specific node. When 10.0.20.10 fails:

1. kube-vip detects the leader failure (via leader election)
2. Another CP node (e.g., 10.0.20.11) becomes the new VIP holder
3. It sends a gratuitous ARP: "10.0.20.100 is now at my MAC"
4. Traffic seamlessly moves to the new leader
5. Failover time: 2-5 seconds

**This is why kube-vip should be one of the first things deployed** on any on-prem cluster with HA control plane.
</details>

---

## Hands-On Exercise: Deploy MetalLB

**Task**: Install MetalLB in a kind cluster and create a LoadBalancer service.

```bash
# Create kind cluster
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

# Install MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml
kubectl wait --namespace metallb-system \
  --for=condition=Ready pod --selector=app=metallb --timeout=120s

# Get the kind network subnet
docker network inspect kind -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
# Example: 172.18.0.0/16

# Configure IP pool (use IPs from the kind network)
kubectl apply -f - <<EOF
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

# Deploy a test app
kubectl create deployment web --image=nginx --replicas=3
kubectl expose deployment web --type=LoadBalancer --port=80

# Verify external IP is assigned
kubectl get svc web
# NAME   TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)       AGE
# web    LoadBalancer   10.96.x.x      172.18.255.200   80:31234/TCP  5s

# Test access
# On Linux, you can curl the MetalLB IP directly:
curl http://172.18.255.200

# On macOS/Windows, the Docker network is not directly reachable from the host.
# Use a container on the kind network instead:
docker run --network kind --rm curlimages/curl http://172.18.255.200
# Or exec into a kind node:
docker exec kind-control-plane curl -s http://172.18.255.200
# <!DOCTYPE html>...

# Cleanup
kind delete cluster
```

### Success Criteria
- [ ] MetalLB installed and running
- [ ] IP address pool configured
- [ ] LoadBalancer service gets an external IP (not Pending)
- [ ] External IP is reachable via curl
- [ ] Multiple replicas are serving traffic

---

## Next Module

Continue to [Module 3.4: DNS & Certificate Infrastructure](../module-3.4-dns-certs/) to learn how to run your own DNS and PKI for on-premises Kubernetes.
