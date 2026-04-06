---
title: "Module 4.4: Cloud-Native Networking and VPC Topologies"
slug: cloud/architecture-patterns/module-4.4-vpc-topologies
sidebar:
  order: 5
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 3.5 hours
>
> **Prerequisites**: [Module 4.1: Managed vs Self-Managed Kubernetes](../module-4.1-managed-vs-selfmanaged/), [Module 4.2: Multi-Cluster and Multi-Region Architectures](../module-4.2-multi-cluster/)
>
> **Track**: Cloud Architecture Patterns

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design cloud-native VPC/VNet topologies optimized for Kubernetes cluster networking across availability zones**
- **Configure CIDR planning strategies that accommodate pod networking, service ranges, and future cluster growth**
- **Implement private cluster architectures with private API endpoints and VPC-native routing**
- **Compare overlay vs native CNI networking models across EKS (VPC CNI), GKE (Dataplane V2), and AKS (Azure CNI)**

---

## Why This Module Matters

**September 2022. A logistics company running 14 Kubernetes clusters on AWS.**

The platform team got a Slack message at 2:15 AM: "Pods stuck in ContainerCreating." The on-call engineer checked. Eighteen pods were waiting to be scheduled, and every attempt to create a new pod failed with the same error: `failed to assign an IP address to the pod`. The error was clear but the cause wasn't obvious -- the nodes had available CPU and memory.

The root cause took three hours to diagnose. The EKS clusters used the VPC CNI plugin in its default mode, where every pod receives a real VPC IP address. The team had provisioned their subnets with /24 CIDR blocks -- 251 usable IPs per subnet. Each m5.2xlarge node could attach 4 Elastic Network Interfaces with 15 IPs each, consuming 60 IPs per node. With 12 nodes in the subnet, they needed 720 IPs. The subnet had 251.

The cluster had been slowly approaching this limit for months. Node autoscaling added more nodes, each consuming more IPs. Nobody monitored subnet IP utilization. When the threshold was crossed, new pods couldn't get IPs, deployments failed, and the horizontal pod autoscaler's scale-up attempts made the problem worse by requesting more pods that couldn't get IPs.

The fix was an emergency subnet expansion -- adding secondary CIDR blocks to the VPC and creating new, larger subnets. This is a disruptive change in production. Nodes had to be drained and relaunched in the new subnets. The full recovery took 11 hours.

This incident was entirely preventable with proper IPAM planning. In this module, you'll learn to design VPC topologies that accommodate Kubernetes' IP consumption patterns from day one, architect egress and ingress correctly, and connect multiple environments without the subnet overlaps that make peering impossible.

---

## VPC Design for Kubernetes: IPAM Fundamentals

IP Address Management (IPAM) for Kubernetes is different from traditional infrastructure. In a VM-based world, each machine gets one IP. In Kubernetes with VPC-native networking (the default on all major managed platforms), each *pod* gets its own VPC IP address. This fundamentally changes how you plan subnets.

### How Many IPs Does Kubernetes Actually Need?

```
IP CONSUMPTION: TRADITIONAL VS KUBERNETES
═══════════════════════════════════════════════════════════════

Traditional (VM-based):
  10 servers = 10 IPs
  Planning: /24 subnet (251 IPs) lasts years

Kubernetes (VPC CNI, per-pod IP):
  10 nodes × 30 pods each = 300 pod IPs + 10 node IPs = 310 IPs
  Planning: /24 subnet (251 IPs) exhausted before you reach 10 nodes

Kubernetes (VPC CNI with prefix delegation):
  10 nodes × 110 pods each = 1,100 pod IPs + 10 node IPs = 1,110 IPs
  Planning: Need /20 (4,091 IPs) minimum for a medium cluster

Kubernetes (overlay network, e.g., Calico VXLAN):
  10 nodes = 10 VPC IPs (pods use overlay, invisible to VPC)
  Planning: /24 subnet is fine, but overlay adds network latency
```

### The VPC CNI IP Consumption Model (AWS)

On EKS with the default VPC CNI plugin, every pod gets a VPC IP address. Here's exactly how IPs are consumed per node:

```
AWS VPC CNI: IP ALLOCATION PER NODE
═══════════════════════════════════════════════════════════════

Instance type: m5.2xlarge
  Max ENIs: 4
  Max IPs per ENI: 15
  Max pods: (4 ENIs × (15 IPs - 1)) + 2 = 58 pods

How it works:
  ┌──────────────────────────────────────────────────────┐
  │ Node: m5.2xlarge                                      │
  │                                                      │
  │  ENI 0 (primary)         ENI 1                       │
  │  ┌─────────────────┐    ┌─────────────────┐          │
  │  │ IP 1: node addr │    │ IP 1: ENI addr  │          │
  │  │ IP 2: pod-a     │    │ IP 2: pod-f     │          │
  │  │ IP 3: pod-b     │    │ IP 3: pod-g     │          │
  │  │ ...             │    │ ...             │          │
  │  │ IP 15: pod-n    │    │ IP 15: pod-z    │          │
  │  └─────────────────┘    └─────────────────┘          │
  │                                                      │
  │  ENI 2                   ENI 3                       │
  │  ┌─────────────────┐    ┌─────────────────┐          │
  │  │ IP 1: ENI addr  │    │ IP 1: ENI addr  │          │
  │  │ IP 2: pod-aa    │    │ IP 2: pod-ff    │          │
  │  │ ...             │    │ ...             │          │
  │  │ IP 15: pod-nn   │    │ IP 15: pod-zz   │          │
  │  └─────────────────┘    └─────────────────┘          │
  │                                                      │
  │  Total IPs consumed from VPC: 60                     │
  │  (4 ENIs × 15 IPs each)                             │
  └──────────────────────────────────────────────────────┘

With prefix delegation (recommended):
  Each ENI gets /28 prefixes (16 IPs) instead of individual IPs
  Max pods: 110 (Kubernetes limit, not ENI limit)
  IPs consumed: Still 60 from VPC perspective, but each
  /28 prefix provides 16 pod IPs from the prefix space
  Effective: 110 pods using far fewer VPC-level IPs
```

```bash
# Enable prefix delegation on EKS (recommended for new clusters)
kubectl set env daemonset aws-node \
  -n kube-system \
  ENABLE_PREFIX_DELEGATION=true \
  WARM_PREFIX_TARGET=1

# Check current IP allocation on a node
kubectl get node ip-10-0-1-42.ec2.internal -o json | \
  jq '.status.allocatable["vpc.amazonaws.com/pod-eni"] // .status.capacity["vpc.amazonaws.com/PrivateIPv4Address"]'
```

### Guided Worked Example: Subnet Calculation

Let's walk through sizing a subnet for a new production cluster.

**The Scenario:**
You are provisioning an EKS cluster using VPC CNI (without prefix delegation). The cluster will scale up to 20 worker nodes (m5.large, which support up to 3 ENIs and 10 IPs per ENI). You want to ensure the subnet can handle this maximum capacity plus 100% headroom for future growth.

**Step 1: Calculate IPs per node**
An m5.large can attach 3 ENIs, each with 10 IPs.
Total IPs per node = 3 * 10 = 30 IPs.

**Step 2: Calculate total IPs for maximum capacity**
20 nodes * 30 IPs/node = 600 IPs required from the VPC.

**Step 3: Add headroom**
100% headroom means we need space for 1,200 IPs.

**Step 4: Select the subnet CIDR**
- A /24 provides 251 usable IPs (Too small)
- A /23 provides 507 usable IPs (Too small)
- A /22 provides 1,019 usable IPs (Too small)
- A /21 provides 2,043 usable IPs (Perfect)

For this cluster, a /21 subnet is the minimum safe choice to guarantee 1,200 IPs are available even if other resources are deployed in the same subnet.

### Subnet Sizing Guide

| Cluster Size | Nodes | Pods (est.) | VPC CNI (standard) | VPC CNI (prefix delegation) | Overlay |
|-------------|-------|-------------|--------------------|-----------------------------|---------|
| Small (dev) | 3-5 | ~100 | /24 (tight) | /24 (comfortable) | /27 |
| Medium | 10-20 | ~500 | /21 minimum | /23 | /25 |
| Large | 50-100 | ~3,000 | /19 minimum | /21 | /24 |
| Very Large | 200+ | ~10,000 | /17 minimum | /19 | /23 |

**The golden rule: always provision subnets at least 2x larger than your current needs.** IP address space is free. Expanding subnets later is painful.

> **Pause and predict**: If you use a /24 subnet (251 IPs) for a cluster configured with Calico VXLAN (overlay) and scale to 50 nodes running 2,000 pods total, will you exhaust the VPC subnet? Why or why not?

---

## Overlay vs Underlay: The Networking Architecture Choice

This is the foundational networking decision for your Kubernetes clusters. It affects performance, IP consumption, observability, and cloud integration.

### Underlay (VPC-Native / Flat Networking)

Pods get real VPC IP addresses. Cloud network infrastructure routes pod traffic natively.

```
UNDERLAY NETWORKING (VPC CNI)
═══════════════════════════════════════════════════════════════

  ┌─────────── VPC: 10.0.0.0/16 ────────────────────────┐
  │                                                      │
  │  Node A (10.0.1.10)           Node B (10.0.1.20)    │
  │  ┌────────────────┐          ┌────────────────┐      │
  │  │ Pod 1: 10.0.1.15│         │ Pod 3: 10.0.1.25│     │
  │  │ Pod 2: 10.0.1.16│         │ Pod 4: 10.0.1.26│     │
  │  └────────┬────────┘         └────────┬────────┘     │
  │           │                           │              │
  │  ─────────┴───────────────────────────┴──────────    │
  │                    VPC Router                        │
  │  Pod-to-pod traffic: Routed natively by VPC          │
  │  No encapsulation. No tunnel. Full line speed.       │
  └──────────────────────────────────────────────────────┘

  Cloud load balancers → target pods directly by IP
  Cloud security groups → applied to pod IPs
  VPC Flow Logs → show individual pod traffic
  Network ACLs → filter pod traffic natively
```

### Overlay (Encapsulated Networking)

Pods get IPs from a separate, private address space. Traffic between nodes is encapsulated in tunnels (VXLAN, Geneve, or IP-in-IP).

```
OVERLAY NETWORKING (Calico VXLAN)
═══════════════════════════════════════════════════════════════

  ┌─────────── VPC: 10.0.0.0/16 ────────────────────────┐
  │                                                      │
  │  Node A (10.0.1.10)           Node B (10.0.1.20)    │
  │  ┌────────────────┐          ┌────────────────┐      │
  │  │ Pod 1: 192.168.│          │ Pod 3: 192.168.│      │
  │  │  1.15 (overlay)│          │  2.25 (overlay)│      │
  │  │ Pod 2: 192.168.│          │ Pod 4: 192.168.│      │
  │  │  1.16 (overlay)│          │  2.26 (overlay)│      │
  │  └───────┬────────┘          └────────┬───────┘      │
  │          │                            │              │
  │          ▼                            ▼              │
  │    VXLAN Tunnel ════════════════ VXLAN Tunnel        │
  │    Outer: 10.0.1.10 → 10.0.1.20                     │
  │    Inner: 192.168.1.15 → 192.168.2.25               │
  │                                                      │
  │  VPC only sees: Node A (10.0.1.10) → Node B         │
  │  VPC cannot see: Individual pod traffic              │
  └──────────────────────────────────────────────────────┘

  Cloud load balancers → must target nodes (extra hop)
  Cloud security groups → applied to nodes, not pods
  VPC Flow Logs → show node-to-node, not pod-to-pod
  Network ACLs → cannot filter individual pod traffic
```

### Decision Matrix

| Factor | Underlay (VPC CNI) | Overlay (Calico/Cilium VXLAN) |
|--------|-------------------|-------------------------------|
| Performance | Native wire speed, no overhead | 5-15% throughput overhead (encapsulation) |
| IP consumption | High (1 VPC IP per pod) | Low (pods use private range) |
| Cloud integration | Full (LB targets pods, SGs per pod) | Limited (LB targets nodes, SGs per node) |
| Observability | VPC Flow Logs show pod traffic | Need CNI-level logs for pod traffic |
| Multi-cluster | VPC peering routes pod IPs natively | Overlay IPs not routable cross-VPC by default |
| Subnet planning | Critical (must plan for pod growth) | Simple (overlay range is independent) |
| Network policy | Enforced at VPC + Calico/Cilium | Enforced at CNI level only |
| Best for | Cloud-native apps needing deep cloud integration | Multi-cloud, IP-constrained environments |

Most teams on a single cloud provider should use underlay (VPC-native) networking with prefix delegation. The cloud integration benefits -- direct pod targeting by load balancers, security group per pod, native VPC Flow Logs -- outweigh the IP planning overhead.

---

## Private Cluster Architectures: Securing the API Server

By default, managed Kubernetes services like EKS and GKE provision the cluster API server endpoint with a public IP address. This means `kubectl` commands traverse the public internet to reach your cluster. For enterprise environments, this is often unacceptable.

### Endpoint Access Modes

When configuring your cluster, you have three primary architectural choices for the API server endpoint:

1. **Public Only (Default but Risky)**
   The API server is accessible from the internet. Security relies entirely on Kubernetes RBAC and IAM authentication. If a vulnerability is found in the API server itself, your cluster is immediately exposed to the world.

2. **Public and Private (The Compromise)**
   The API server has both a public IP and a private IP within your VPC. Nodes use the private IP to communicate with the control plane, keeping node-to-control-plane traffic off the internet. Developers can still use the public endpoint from their laptops (often restricted by a CIDR allowlist).

3. **Private Only (Enterprise Standard)**
   The API server only has a private IP within your VPC. There is no public routing to the control plane. This is the most secure posture but requires additional architecture for developer access.

### Implementing Private-Only Access

When you choose a fully private cluster, how do developers and CI/CD pipelines run `kubectl apply`? You must provide a secure path into the VPC:

- **VPN / Direct Connect:** Developers connect to the corporate VPN, which is peered to the VPC. Traffic flows privately.
- **Bastion Host:** A hardened EC2 instance in a public subnet. Users SSH into the bastion (or use AWS Systems Manager Session Manager) and run `kubectl` from there.
- **CI/CD Runners in VPC:** GitHub Actions runners or GitLab runners are deployed as EC2 instances or pods within the VPC itself, allowing them to communicate natively with the private API server.

```bash
# EKS: Update cluster to Private-Only mode
aws eks update-cluster-config \
  --name production-cluster \
  --resources-vpc-config endpointPublicAccess=false,endpointPrivateAccess=true
```

> **Stop and think**: If you switch an existing cluster to "Private Only" without having a VPN or Bastion host set up, what will happen to your current `kubectl` session? How will the worker nodes be affected?

---

## Egress Architecture: How Traffic Leaves Your Cluster

Every pod that calls an external API, downloads a package, or talks to a SaaS service needs an egress path. This path has cost, security, and compliance implications.

### NAT Gateway: The Default (and Expensive) Path

```
NAT GATEWAY EGRESS
═══════════════════════════════════════════════════════════════

  Pod (10.0.2.15)                            Internet
  ┌──────────┐                               ┌──────────┐
  │ curl     │──▶ Route Table ──▶ NAT GW ──▶│ api.     │
  │ api.com  │    0.0.0.0/0       (public    │ example  │
  └──────────┘    → nat-gw-id     subnet)    │ .com     │
                                   │          └──────────┘
                                   ▼
                              Elastic IP
                              52.1.2.3
                              (your public IP)

  Cost:
    NAT Gateway hourly: $0.045/hr × 730 hrs = $32.85/mo
    Data processing: $0.045/GB
    At 1TB/month egress: $32.85 + $45.00 = $77.85/mo per AZ

    With 3 AZs: $233.55/mo JUST for NAT
    (plus standard data transfer charges on top)
```

NAT Gateways are the single most expensive surprise in AWS Kubernetes deployments. A medium cluster pulling container images, calling external APIs, and sending logs to a SaaS observability platform can easily generate 5-10 TB of NAT data processing per month.

### Reducing NAT Costs

```
COST-OPTIMIZED EGRESS ARCHITECTURE
═══════════════════════════════════════════════════════════════

Strategy 1: VPC Endpoints (eliminate NAT for AWS services)
  ┌──────────┐                    ┌──────────────────┐
  │ Pod      │──▶ VPC Endpoint ──▶│ S3 (no NAT)      │
  │          │    (Gateway type)  │ Free data path    │
  └──────────┘                    └──────────────────┘

  ┌──────────┐                    ┌──────────────────┐
  │ Pod      │──▶ VPC Endpoint ──▶│ ECR (no NAT)     │
  │          │    (Interface type)│ $0.01/hr + free   │
  └──────────┘    $7.30/mo each   │ data processing  │
                                  └──────────────────┘

Strategy 2: ECR pull-through cache (reduce image pulls)
  First pull: ECR → upstream registry → cache
  Subsequent: ECR → local cache (in-VPC, no NAT)

Strategy 3: NAT Instance (cheaper for low traffic)
  t4g.nano: $3.02/mo (vs $32.85/mo for NAT GW)
  Trade-off: No HA, lower bandwidth, you manage it
```

```bash
# Create VPC endpoints for common AWS services
# These eliminate NAT Gateway data processing charges

# S3 Gateway Endpoint (free)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-private-1 rtb-private-2

# ECR API endpoint (Interface type, $7.30/mo)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.ecr.api \
  --subnet-ids subnet-private-1a subnet-private-1b \
  --security-group-ids sg-vpce-ecr

# ECR Docker endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.ecr.dkr \
  --subnet-ids subnet-private-1a subnet-private-1b \
  --security-group-ids sg-vpce-ecr

# CloudWatch Logs endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.logs \
  --subnet-ids subnet-private-1a subnet-private-1b \
  --security-group-ids sg-vpce-logs

# STS endpoint (needed for IRSA token exchange)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.sts \
  --subnet-ids subnet-private-1a subnet-private-1b \
  --security-group-ids sg-vpce-sts
```

> **Pause and predict**: Your monthly AWS bill shows a $4,000 charge for NAT Gateway Data Processing. Your cluster heavily uses S3 and DynamoDB. What single architectural change would drastically reduce this cost tomorrow without changing any application code?

### Egress for Compliance: Proxy-Based Egress

Some regulated environments require all egress traffic to flow through an inspection proxy. This provides URL-level filtering, TLS inspection, and logging.

```
PROXY-BASED EGRESS
═══════════════════════════════════════════════════════════════

  Pod → Proxy (Squid/Envoy) → Internet
         │
         ├── Allow: api.stripe.com (payment processor)
         ├── Allow: registry.npmjs.org (package registry)
         ├── Allow: *.datadog.com (observability)
         ├── Block: * (everything else)
         │
         └── Full URL logging for audit trail

  Implementation:
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ Pod      │────▶│ Egress   │────▶│ NAT GW   │──▶ Internet
  │          │     │ Proxy    │     │          │
  │ HTTP_    │     │ (Envoy)  │     └──────────┘
  │ PROXY=   │     │ - Allow  │
  │ proxy:   │     │   list   │
  │ 3128     │     │ - Logging│
  └──────────┘     │ - TLS    │
                   │   inspect│
                   └──────────┘
```

```yaml
# Kubernetes: Force egress through proxy using NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    # Allow DNS
    - to: []
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # Allow traffic to egress proxy only
    - to:
        - podSelector:
            matchLabels:
              app: egress-proxy
      ports:
        - protocol: TCP
          port: 3128
    # Allow in-cluster traffic
    - to:
        - namespaceSelector: {}
```

---

## Ingress Architecture: How Traffic Reaches Your Cluster

Ingress is the mirror of egress. It's how external traffic reaches your Kubernetes services. The architecture differs significantly between cloud providers and use cases.

### Cloud Load Balancer Integration

```
INGRESS PATH: CLOUD LB → KUBERNETES
═══════════════════════════════════════════════════════════════

Option A: NLB → NodePort (L4)
  ┌────────┐     ┌──────┐     ┌──────┐     ┌─────┐
  │ Client │────▶│ NLB  │────▶│ Node │────▶│ Pod │
  └────────┘     │ (L4) │     │ Port │     └─────┘
                 └──────┘     │30080 │
                              └──────┘
  Pros: Simple, preserves source IP
  Cons: Extra hop (NodePort), uneven distribution

Option B: NLB → Pod IP directly (L4, IP target mode)
  ┌────────┐     ┌──────┐                   ┌─────┐
  │ Client │────▶│ NLB  │──────────────────▶│ Pod │
  └────────┘     │ (L4) │   (pod IP is LB   │10.0.│
                 └──────┘    target)         │1.42 │
                                             └─────┘
  Pros: No extra hop, even distribution, lower latency
  Cons: Requires VPC CNI (underlay networking)

Option C: ALB → Pod IP (L7, via Ingress/Gateway API)
  ┌────────┐     ┌──────┐                   ┌─────┐
  │ Client │────▶│ ALB  │──────────────────▶│ Pod │
  └────────┘     │ (L7) │   (TLS terminated  │     │
                 │ WAF  │    at ALB, routes  │     │
                 │ Auth │    by path/host)   └─────┘
                 └──────┘
  Pros: L7 routing, WAF integration, auth offloading
  Cons: ALB cost ($16/mo + LCU charges)
```

### Gateway API: The Modern Standard

```yaml
# Gateway API is replacing Ingress as the standard
# More expressive, role-oriented, portable

# Infrastructure admin creates the Gateway
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
  namespace: infrastructure
  annotations:
    # AWS: Use ALB
    service.beta.kubernetes.io/aws-load-balancer-type: "external"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  gatewayClassName: aws-alb  # or istio, cilium, nginx, etc.
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        mode: Terminate
        certificateRefs:
          - name: production-tls
            namespace: infrastructure
      allowedRoutes:
        namespaces:
          from: Selector
          selector:
            matchLabels:
              gateway-access: "true"
---
# Application team creates HTTPRoutes
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: payment-api-route
  namespace: production
spec:
  parentRefs:
    - name: production-gateway
      namespace: infrastructure
  hostnames:
    - "api.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /v1/payments
      backendRefs:
        - name: payment-api
          port: 8080
          weight: 100
    - matches:
        - path:
            type: PathPrefix
            value: /v1/orders
      backendRefs:
        - name: order-api
          port: 8080
          weight: 100
```

### WAF Integration

Web Application Firewall (WAF) should sit in front of any public-facing Kubernetes service.

```bash
# AWS WAF with ALB Ingress Controller
# The ALB created by the Ingress controller can have WAF attached

# Create a WAF Web ACL
aws wafv2 create-web-acl \
  --name production-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules '[
    {
      "Name": "RateLimit",
      "Priority": 1,
      "Action": {"Block": {}},
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimit"
      }
    },
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 2,
      "OverrideAction": {"None": {}},
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRules"
      }
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=production-waf
```

---

## VPC Peering and Transit Gateways

When you have multiple VPCs (dev, staging, production, shared services), they need to communicate. The two primary mechanisms are VPC Peering and Transit Gateways.

### VPC Peering: Simple, Point-to-Point

```
VPC PEERING: DIRECT CONNECTIONS
═══════════════════════════════════════════════════════════════

  2 VPCs = 1 peering connection
  3 VPCs = 3 peering connections
  4 VPCs = 6 peering connections
  N VPCs = N×(N-1)/2 connections

  ┌─────────────┐         ┌─────────────┐
  │ Production  │◀──────▶│ Staging     │
  │ 10.1.0.0/16│         │ 10.2.0.0/16│
  └──────┬──────┘         └──────┬──────┘
         │                       │
         │    ┌─────────────┐    │
         └───▶│ Shared Svc  │◀──┘
              │ 10.10.0.0/16│
              └─────────────┘

  3 VPCs = 3 peering connections. Manageable.

  With 10 VPCs:
  10 × 9 / 2 = 45 peering connections.
  Not manageable.
```

### Transit Gateway: Hub-and-Spoke

```
TRANSIT GATEWAY: CENTRALIZED ROUTING
═══════════════════════════════════════════════════════════════

  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Prod     │  │ Staging  │  │ Dev      │  │ Shared   │
  │10.1.0/16│  │10.2.0/16│  │10.3.0/16│  │10.10.0/16│
  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │              │              │              │
       └──────────────┼──────────────┼──────────────┘
                      │              │
              ┌───────▼──────────────▼───────┐
              │       Transit Gateway         │
              │                               │
              │  Route Tables:                │
              │    Prod → Shared, Staging     │
              │    Staging → Shared, Prod     │
              │    Dev → Shared only          │
              │    Shared → All               │
              │                               │
              │  + On-Premises via VPN/DX     │
              └───────────────────────────────┘

  Any number of VPCs: 1 TGW attachment per VPC.
  Centralized routing policies.
  Route table segmentation (Dev can't reach Prod).
```

```bash
# Create a Transit Gateway
aws ec2 create-transit-gateway \
  --description "Production TGW" \
  --options "AmazonSideAsn=64512,AutoAcceptSharedAttachments=disable,DefaultRouteTableAssociation=disable,DefaultRouteTablePropagation=disable,DnsSupport=enable"

# Attach VPCs
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-12345 \
  --vpc-id vpc-prod \
  --subnet-ids subnet-prod-1a subnet-prod-1b

aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-12345 \
  --vpc-id vpc-staging \
  --subnet-ids subnet-staging-1a subnet-staging-1b

# Create separate route tables for segmentation
aws ec2 create-transit-gateway-route-table \
  --transit-gateway-id tgw-12345 \
  --tags Key=Name,Value=prod-routes

aws ec2 create-transit-gateway-route-table \
  --transit-gateway-id tgw-12345 \
  --tags Key=Name,Value=dev-routes
```

### Transit Gateway Costs

| Component | Cost |
|-----------|------|
| TGW per hour per AZ attachment | $0.05/hr (~$36.50/mo) |
| Data processing | $0.02/GB |
| 5 VPCs, 2 AZs each | $365/mo just for attachments |
| 1 TB cross-VPC traffic | $20/mo data processing |

Transit Gateway is worth it when you have 4+ VPCs or need centralized routing policies. Below that, VPC Peering is cheaper and simpler.

---

## On-Premises Connectivity

Connecting Kubernetes clusters to on-premises data centers requires choosing between VPN (encrypted over internet) and Direct Connect (dedicated private link).

```
CONNECTIVITY OPTIONS
═══════════════════════════════════════════════════════════════

Option 1: Site-to-Site VPN
  ┌────────────┐    IPSec Tunnel     ┌────────────┐
  │ On-Prem    │◀═══════════════════▶│ AWS VPC    │
  │ Datacenter │    (over internet)  │ / TGW      │
  └────────────┘                     └────────────┘
  Cost: $0.05/hr (~$36.50/mo) + data transfer
  Bandwidth: Up to 1.25 Gbps per tunnel (2 tunnels for HA)
  Latency: Variable (internet-dependent)
  Setup time: Hours

Option 2: AWS Direct Connect
  ┌────────────┐    Dedicated Fiber   ┌────────────┐
  │ On-Prem    │◀═══════════════════▶│ AWS DX     │
  │ Datacenter │    (private circuit) │ Location   │
  └────────────┘                     └────────────┘
  Cost: $0.30/hr (1Gbps port) + data transfer
  Bandwidth: 1, 10, or 100 Gbps dedicated
  Latency: Consistent (no internet hops)
  Setup time: Weeks to months

Option 3: Direct Connect + VPN Backup
  Primary: Direct Connect (high bandwidth, consistent latency)
  Backup: Site-to-Site VPN (automatic failover if DX fails)
  Best for: Production workloads needing reliability + performance
```

### The Critical Point: Non-Overlapping CIDRs

When connecting cloud VPCs to on-premises networks, CIDR overlap is the most common and painful mistake. If your on-prem network uses `10.0.0.0/8` and your VPC also uses `10.0.0.0/16`, routing breaks. Traffic destined for `10.0.1.5` could mean a pod in your cluster or a server in your data center.

```
THE OVERLAPPING CIDR DISASTER
═══════════════════════════════════════════════════════════════

Before peering (everyone used 10.0.0.0/16):

  On-Prem: 10.0.0.0/8        VPC Prod: 10.0.0.0/16
  Server: 10.0.1.50           Pod: 10.0.1.50

  Peering attempt → REJECTED
  "CIDR blocks overlap. Cannot create peering connection."

  Fix: Re-IP one side. In production. With zero downtime.
  Difficulty: Nightmare. This is a multi-month project.


Correct planning from day one:

  On-Prem:     172.16.0.0/12  (172.16.0.0 - 172.31.255.255)
  AWS Prod:    10.1.0.0/16
  AWS Staging: 10.2.0.0/16
  AWS Dev:     10.3.0.0/16
  GCP:         10.100.0.0/16
  Azure:       10.200.0.0/16

  No overlaps. Everything can peer with everything.
```

---

## Did You Know?

- **AWS NAT Gateway data processing charges are the number one surprise cost for Kubernetes teams.** A single EKS cluster pulling container images, sending logs to Datadog, and communicating with managed services can generate $500-$2,000/month in NAT charges alone. VPC endpoints for S3, ECR, CloudWatch, and STS can reduce this by 60-80%.

- **The maximum number of IP addresses in a single AWS VPC is 65,536** (a /16 CIDR block). With secondary CIDRs, you can add up to 4 additional blocks, but many teams hit IP limits long before that because they under-sized their subnets. GCP has it easier: VPC subnets can span 8,000+ IP addresses across regions automatically.

- **Kubernetes pod-to-pod traffic within the same AZ on AWS is free**, but cross-AZ traffic costs $0.01/GB in each direction ($0.02/GB round trip). For a cluster spanning 3 AZs with chatty microservices, this adds up. Topology-aware routing (topology.kubernetes.io/zone) can reduce cross-AZ traffic by preferring same-zone backends.

- **The Gateway API specification reached GA (v1.0) in October 2023** after three years of development. Unlike the Ingress resource (which was never formally versioned and has inconsistent behavior across controllers), Gateway API has formal conformance tests. Every conformant implementation must behave identically for the same configuration, making it truly portable across providers.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using /24 subnets for EKS | Treating K8s like VMs where each host gets one IP | Size subnets for pod count: /20 or larger for production clusters |
| Not enabling prefix delegation | Using default VPC CNI settings | Enable `ENABLE_PREFIX_DELEGATION=true` on aws-node DaemonSet. Reduces IP consumption dramatically |
| Skipping VPC endpoints | Don't realize NAT Gateway processes AWS service traffic | Create Gateway endpoints (S3, DynamoDB) and Interface endpoints (ECR, STS, CloudWatch) |
| Overlapping CIDRs across environments | Using default 10.0.0.0/16 everywhere | Plan a global IPAM scheme before creating the first VPC. Document it. Enforce it |
| Single NAT Gateway (one AZ) | "We only need one" | Deploy NAT Gateway per AZ for HA. One NAT GW failure shouldn't break all egress |
| No network policies | "We'll add them later" | Start with a default-deny policy per namespace. Explicitly allow required traffic |
| ALB per service | Each Ingress creates a new ALB ($16/mo each) | Use a shared ALB with path-based or host-based routing. One ALB can serve many services |
| Ignoring cross-AZ transfer costs | Free within AZ, $0.02/GB cross-AZ seems small | At 10TB/month cross-AZ: $200/month. Use topology-aware routing to keep traffic local |

---

## Quiz

<details>
<summary>1. An EKS cluster uses VPC CNI (default mode, no prefix delegation) with m5.xlarge nodes. Each node has 4 ENIs with 15 IPs each. The subnet is a /24 (251 usable IPs). How many nodes can fit before IP exhaustion?</summary>

Each m5.xlarge node consumes 60 VPC IPs (4 ENIs x 15 IPs) because the default VPC CNI attaches all possible ENIs and secondary IPs to ensure rapid pod scheduling. With 251 usable IPs in a /24 subnet, you can fit 251 / 60 = 4.18, so only 4 nodes before exhaustion. The 5th node would fail to acquire all its necessary ENI IPs, preventing new pods from being scheduled on it. In practice, because some IPs are consumed by internal load balancers or VPC endpoints, you might hit the limit even sooner, which is why a /24 is dangerously small for EKS.
</details>

<details>
<summary>2. Your application team is building a microservice that heavily reads from AWS S3 and pushes metrics to CloudWatch. During a cost audit, you notice a massive spike in NAT Gateway data processing charges. What specific architectural changes should you implement to eliminate these costs?</summary>

You should implement VPC Gateway endpoints for S3 and VPC Interface endpoints for CloudWatch. Gateway endpoints are free and route traffic to S3 directly over the AWS network, bypassing the NAT Gateway completely. Interface endpoints create an ENI in your subnet for services like CloudWatch, redirecting traffic privately for a small hourly fee that is vastly cheaper than NAT data processing. By routing this heavy internal traffic directly through endpoints, the NAT Gateway is bypassed, eliminating the data processing charges associated with those services.
</details>

<details>
<summary>3. A security compliance auditor mandates that every individual pod's network traffic must be fully logged and subject to VPC-level Network ACLs. Your current clusters run on standard EC2 instances. Which network architecture must you choose to satisfy this requirement?</summary>

You must choose an Underlay (VPC-Native) networking architecture, such as the AWS VPC CNI. With underlay networking, every pod receives a native IP address from the VPC subnet. Because the traffic is not encapsulated in tunnels (like it would be with an overlay network such as VXLAN), the VPC fabric sees every packet's true source and destination IP. This visibility allows VPC Flow Logs to record individual pod traffic and enables Network ACLs to filter traffic at the pod IP level, directly satisfying the auditor's requirements.
</details>

<details>
<summary>4. Your company has 8 VPCs that need to communicate. You are debating between using VPC Peering or a Transit Gateway. Why is Transit Gateway the better architectural choice for this scenario?</summary>

With 8 VPCs, a full mesh of VPC Peering would require 28 separate peering connections (8 x 7 / 2), each needing custom route table entries and complex security group management. Adding a 9th VPC later would require 8 more distinct peering connections, creating an operational nightmare. Transit Gateway simplifies this by acting as a central hub where each VPC only requires a single attachment. Route tables are managed centrally on the Transit Gateway, allowing for clean network segmentation and vastly simpler scaling as new environments are added.
</details>

<details>
<summary>5. A team plans to connect their AWS VPCs to an on-premises data center using a Site-to-Site VPN. Both the AWS environments and the on-premises network use the 10.0.0.0/8 CIDR range. What routing problem will occur, and how must it be resolved?</summary>

Direct routing will fail because the CIDR ranges perfectly overlap, meaning the routers cannot determine whether a packet destined for `10.0.1.5` belongs to a cloud pod or an on-premises server. To fix this without re-IPing either side, you must deploy a NAT solution at the network boundary. The VPN configuration would need to NAT the on-premises 10.x range to a non-overlapping range (such as 100.64.0.0/10) from the perspective of the cloud VPC. The most sustainable long-term solution, however, is to plan a global IPAM scheme before creating infrastructure to ensure environments utilize entirely distinct CIDR blocks.
</details>

<details>
<summary>6. Your e-commerce platform spans three Availability Zones. During a load test, you notice that cross-AZ data transfer costs are excessively high, even though the total number of requests is expected. You are currently using default Kubernetes Services for internal routing. How can you modify the Kubernetes configuration to reduce this cloud infrastructure cost?</summary>

You should implement topology-aware routing by adding the `service.kubernetes.io/topology-mode: Auto` annotation to your Kubernetes Services. By default, kube-proxy distributes internal service traffic randomly across all healthy endpoints in the cluster, meaning roughly 67% of traffic crosses AZ boundaries in a 3-AZ setup. Topology-aware routing instructs kube-proxy to prefer routing traffic to backend pods located in the exact same Availability Zone as the client pod. This change keeps the majority of internal traffic local to the AZ, drastically reducing the $0.01/GB cross-AZ data transfer fees while also slightly improving request latency.
</details>

---

## Hands-On Exercise: Design a Multi-Environment Subnet Plan

You're designing the network architecture for a company that runs Kubernetes across three environments (development, staging, production) plus a shared services VPC. The company also has an on-premises data center that must connect to all cloud environments.

### Context

- Cloud provider: AWS, us-east-1
- On-premises data center CIDR: 172.16.0.0/12
- Each environment runs EKS with VPC CNI (prefix delegation enabled)
- Production: 50 nodes, ~2,500 pods
- Staging: 15 nodes, ~500 pods
- Development: 10 nodes, ~300 pods
- Shared services: monitoring stack, CI/CD, artifact registry
- Future: eu-west-1 region for production DR

### Task 1: Design the Global CIDR Allocation

Create a non-overlapping CIDR scheme that accommodates all current and future environments without conflicts.

<details>
<summary>Solution</summary>

```
GLOBAL CIDR ALLOCATION
═══════════════════════════════════════════════════════════════

On-Premises (existing):
  172.16.0.0/12         (172.16.0.0 - 172.31.255.255)

AWS us-east-1:
  10.1.0.0/16           Production VPC       (65,536 IPs)
  10.2.0.0/16           Staging VPC          (65,536 IPs)
  10.3.0.0/16           Development VPC      (65,536 IPs)
  10.10.0.0/16          Shared Services VPC  (65,536 IPs)

AWS eu-west-1 (future DR):
  10.101.0.0/16         Production DR VPC    (65,536 IPs)
  10.110.0.0/16         Shared Services DR   (65,536 IPs)

Reserved for future regions:
  10.201.0.0/16         Asia-Pacific Prod
  10.210.0.0/16         Asia-Pacific Shared

Reserved for other cloud providers:
  10.50.0.0/16          GCP (if needed)
  10.60.0.0/16          Azure (if needed)

Kubernetes Pod CIDRs (if using overlay -- not needed with VPC CNI):
  192.168.0.0/16        Reserved, not used with VPC CNI

Key design decisions:
  - First octet after 10. encodes the purpose
  - 1-9: environments, 10-19: shared services
  - 100+: DR regions mirror primary with +100 offset
  - 200+: additional regions
  - 50-60: other clouds
  - No overlap with on-prem 172.16.0.0/12
```
</details>

### Task 2: Design Subnet Layout for the Production VPC

Create the subnet layout for the production VPC (10.1.0.0/16) across 3 AZs, with separate tiers for pods, nodes, and internal load balancers.

<details>
<summary>Solution</summary>

```
PRODUCTION VPC: 10.1.0.0/16
═══════════════════════════════════════════════════════════════

Availability Zone us-east-1a:
  10.1.0.0/19     Pod subnet (8,190 IPs)     ← EKS pods
  10.1.32.0/22    Node subnet (1,022 IPs)    ← EC2 instances
  10.1.36.0/24    Internal LB (251 IPs)      ← NLB/ALB
  10.1.37.0/24    Public subnet (251 IPs)    ← NAT GW, bastion
  10.1.38.0/24    VPC endpoints (251 IPs)    ← Interface endpoints
  10.1.39.0/24    Reserved (future use)

Availability Zone us-east-1b:
  10.1.64.0/19    Pod subnet (8,190 IPs)
  10.1.96.0/22    Node subnet (1,022 IPs)
  10.1.100.0/24   Internal LB (251 IPs)
  10.1.101.0/24   Public subnet (251 IPs)
  10.1.102.0/24   VPC endpoints (251 IPs)
  10.1.103.0/24   Reserved

Availability Zone us-east-1c:
  10.1.128.0/19   Pod subnet (8,190 IPs)
  10.1.160.0/22   Node subnet (1,022 IPs)
  10.1.164.0/24   Internal LB (251 IPs)
  10.1.165.0/24   Public subnet (251 IPs)
  10.1.166.0/24   VPC endpoints (251 IPs)
  10.1.167.0/24   Reserved

Total pod IPs: 3 × 8,190 = 24,570
  Supports: 50 nodes × 110 pods = 5,500 pods (using <25%)
  Growth capacity: ~4x before needing subnet expansion

Why /19 for pods?
  50 nodes × 110 max pods = 5,500 pod IPs needed now
  /19 per AZ = 8,190 IPs per AZ = 24,570 total
  Leaves ~75% headroom for growth

Why separate pod and node subnets?
  - Different security groups for pods vs nodes
  - Pods need VPC CNI with prefix delegation
  - Nodes have SSH access, pods don't
  - Monitoring IP exhaustion separately is easier
```
</details>

### Task 3: Design the Transit Gateway Routing

Configure the Transit Gateway route tables to enforce environment isolation: development cannot reach production directly.

<details>
<summary>Solution</summary>

```
TRANSIT GATEWAY ROUTE TABLE DESIGN
═══════════════════════════════════════════════════════════════

TGW Route Table: production-routes
  Associated: Production VPC
  Routes:
    10.10.0.0/16 → Shared Services attachment    (monitoring, CI/CD)
    10.2.0.0/16  → Staging attachment             (for promotion testing)
    172.16.0.0/12 → On-prem VPN attachment        (database migration)
    # NO route to 10.3.0.0/16 (Development)       ← ISOLATION

TGW Route Table: staging-routes
  Associated: Staging VPC
  Routes:
    10.10.0.0/16 → Shared Services attachment
    10.1.0.0/16  → Production attachment           (read replicas)
    172.16.0.0/12 → On-prem VPN attachment
    # NO route to 10.3.0.0/16 (Development)

TGW Route Table: development-routes
  Associated: Development VPC
  Routes:
    10.10.0.0/16 → Shared Services attachment     (CI/CD, registry)
    # NO route to 10.1.0.0/16 (Production)        ← ISOLATION
    # NO route to 10.2.0.0/16 (Staging)           ← ISOLATION
    # NO route to 172.16.0.0/12 (On-prem)         ← ISOLATION

TGW Route Table: shared-services-routes
  Associated: Shared Services VPC
  Routes:
    10.1.0.0/16  → Production attachment
    10.2.0.0/16  → Staging attachment
    10.3.0.0/16  → Development attachment
    172.16.0.0/12 → On-prem VPN attachment
    # Shared services can reach everything (monitoring, CI/CD)

TGW Route Table: onprem-routes
  Associated: VPN attachment
  Routes:
    10.1.0.0/16  → Production attachment
    10.2.0.0/16  → Staging attachment
    10.10.0.0/16 → Shared Services attachment
    # NO route to 10.3.0.0/16 (Development)
```

This design enforces: Development is completely isolated from Production, Staging, and on-prem. It can only reach Shared Services (for pulling images, CI/CD). Production and Staging can reach each other (for promotion testing) and on-prem (for database connectivity). Shared Services is the hub that can reach everything.
</details>

### Task 4: Calculate the Monthly Networking Cost

Estimate the monthly cost for the complete network architecture, including NAT Gateways, Transit Gateway, VPC endpoints, and data transfer.

<details>
<summary>Solution</summary>

| Component | Quantity | Unit Cost | Monthly Cost |
|-----------|----------|-----------|-------------|
| NAT Gateway (prod, 3 AZs) | 3 | $32.85/mo | $98.55 |
| NAT Gateway (staging, 2 AZs) | 2 | $32.85/mo | $65.70 |
| NAT Gateway (dev, 1 AZ) | 1 | $32.85/mo | $32.85 |
| NAT data processing (est. 2TB total) | 2,000 GB | $0.045/GB | $90.00 |
| Transit Gateway attachments (4 VPCs x 2 AZs avg) | 8 | $36.50/mo | $292.00 |
| TGW VPN attachment | 1 | $36.50/mo | $36.50 |
| TGW data processing (est. 500GB) | 500 GB | $0.02/GB | $10.00 |
| VPC endpoints - S3 Gateway (all VPCs) | 4 | Free | $0.00 |
| VPC endpoints - Interface (ECR, STS, CW per VPC) | 12 | $7.30/mo per AZ | $175.20 |
| Cross-AZ data transfer (est. 3TB) | 3,000 GB | $0.02/GB | $60.00 |
| Site-to-Site VPN | 1 | $36.50/mo | $36.50 |
| **Total Monthly Network Cost** | | | **$897.30** |

**Cost optimization opportunities:**
- Replace dev NAT GW with a t4g.nano NAT instance: save $29.83/mo
- Use VPC endpoints to reduce NAT data processing: save ~$40/mo
- Enable topology-aware routing to reduce cross-AZ: save ~$20/mo
- Consolidate dev+staging VPC endpoints: save $87.60/mo
- **Optimized total: ~$720/mo**
</details>

### Success Criteria

- [ ] Global CIDR scheme has no overlaps between any environments or on-premises
- [ ] Production subnet plan accommodates 4x growth without re-architecting
- [ ] Pod and node subnets are separated with appropriate sizing
- [ ] Transit Gateway routing enforces development isolation from production
- [ ] VPC endpoints reduce NAT Gateway dependency for AWS service traffic
- [ ] Cost estimate includes all networking components

---

## Next Module

This is the final module in the Cloud Architecture Patterns series. You now have the knowledge to design Kubernetes deployments that are well-managed (Module 4.1), resilient across regions (Module 4.2), secured with identity federation (Module 4.3), and networked correctly from day one (Module 4.4). Consider exploring the [Platform Engineering Track](../../platform/) for deeper dives into GitOps, observability, and security tooling.