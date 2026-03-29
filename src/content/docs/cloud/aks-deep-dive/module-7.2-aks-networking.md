---
title: "Module 7.2: AKS Advanced Networking"
slug: cloud/aks-deep-dive/module-7.2-aks-networking
sidebar:
  order: 3
---
**Complexity**: [COMPLEX] | **Time to Complete**: 3.5h | **Prerequisites**: [Module 7.1: AKS Architecture & Node Management](../module-7.1-aks-architecture/)

## Why This Module Matters

In February 2024, a European e-commerce platform migrated from a legacy monolith to a microservices architecture running on AKS. The team chose the default Kubenet networking plugin because it seemed simpler and required fewer IP addresses. Everything worked fine in their three-service staging environment. Three months after going to production with 85 microservices, the platform started experiencing intermittent 5-second delays on inter-service calls. The delays worsened under load. After two weeks of fruitless application debugging, a network engineer finally traced the problem: Kubenet uses user-defined routes (UDRs) and a bridge network on each node, meaning every pod-to-pod call crossing node boundaries required an extra hop through the Azure routing table. With 85 services generating thousands of cross-node calls per second, the UDR route table hit its update limit, causing route propagation delays that manifested as those mysterious 5-second pauses. The migration to Azure CNI took three weeks and required a complete cluster rebuild---a cost of roughly $180,000 in engineering time and lost revenue during the transition.

Networking is the decision you make early and pay for late. The choice between Azure CNI, Kubenet, CNI Overlay, and the newer CNI Powered by Cilium determines your IP address consumption, pod-to-pod latency, network policy capabilities, and even which Azure services can communicate directly with your pods. Get it wrong and you face an expensive re-architecture. Get it right and your network becomes invisible---which is exactly what a network should be.

In this module, you will understand every AKS networking model in depth, compare network policy engines (Azure Network Policy Manager, Calico, and Cilium), learn when to use Application Gateway Ingress Controller versus NGINX, architect private clusters with Private Link, and connect your cluster to Azure API Management. The hands-on exercise has you deploying CNI Powered by Cilium with L7-aware egress domain filtering---the most advanced networking setup AKS offers.

---

## The Four Networking Models: How Pods Get Their IP Addresses

The single most consequential networking decision in AKS is which Container Network Interface (CNI) plugin to use. This choice affects IP address consumption, network performance, and which features are available. Let us break down all four options.

### Kubenet: The Simple (but Limited) Choice

Kubenet assigns pods IP addresses from a virtual network space that is separate from the Azure VNet. Each node gets a single IP address from the VNet subnet, and pods on that node receive addresses from a private 10.244.0.0/16 range managed by a local bridge. Traffic between pods on different nodes is routed through Azure UDRs.

```text
    Azure VNet: 10.1.0.0/16
    ┌─────────────────────────────────────────────────────────────┐
    │  Subnet: 10.1.1.0/24                                       │
    │                                                             │
    │  Node A (10.1.1.4)          Node B (10.1.1.5)               │
    │  ┌─────────────────┐       ┌─────────────────┐              │
    │  │ cbr0 bridge     │       │ cbr0 bridge     │              │
    │  │ 10.244.0.0/24   │       │ 10.244.1.0/24   │              │
    │  │                 │       │                 │              │
    │  │ Pod: 10.244.0.5 │       │ Pod: 10.244.1.8 │              │
    │  │ Pod: 10.244.0.6 │       │ Pod: 10.244.1.9 │              │
    │  └────────┬────────┘       └────────┬────────┘              │
    │           │                          │                       │
    │           └──── UDR route table ─────┘                       │
    │                 10.244.0.0/24 → 10.1.1.4                    │
    │                 10.244.1.0/24 → 10.1.1.5                    │
    └─────────────────────────────────────────────────────────────┘
```

Kubenet conserves IP addresses---if you have 100 pods across 3 nodes, you only consume 3 VNet IPs. But the trade-offs are severe for production workloads:

- **No direct VNet connectivity for pods**: Azure services (like Azure SQL with VNet service endpoints) cannot reach pod IPs directly.
- **UDR limits**: Azure supports a maximum of 400 routes per route table. With large clusters, you can hit this limit.
- **Performance overhead**: Every cross-node packet traverses the UDR routing layer, adding latency.
- **No Windows node support**: Kubenet only works with Linux nodes.

### Azure CNI: Direct VNet Integration

Azure CNI assigns every pod an IP address directly from the VNet subnet. Each pod is a first-class citizen on the Azure network---accessible by any Azure resource that can reach the VNet, without NAT or routing tricks.

```text
    Azure VNet: 10.1.0.0/16
    ┌─────────────────────────────────────────────────────────────┐
    │  Subnet: 10.1.1.0/22 (1,024 addresses - you need a lot!)  │
    │                                                             │
    │  Node A (10.1.1.4)          Node B (10.1.1.5)               │
    │  ┌─────────────────┐       ┌─────────────────┐              │
    │  │ Pod: 10.1.1.10  │       │ Pod: 10.1.1.40  │              │
    │  │ Pod: 10.1.1.11  │       │ Pod: 10.1.1.41  │              │
    │  │ Pod: 10.1.1.12  │       │ Pod: 10.1.1.42  │              │
    │  │ ...              │       │ ...              │              │
    │  │ Pod: 10.1.1.39  │       │ Pod: 10.1.1.69  │              │
    │  └─────────────────┘       └─────────────────┘              │
    │                                                             │
    │  30 IPs reserved per node (even if only 5 pods running)     │
    └─────────────────────────────────────────────────────────────┘
```

The critical issue with Azure CNI is IP address consumption. By default, AKS pre-allocates IPs for the maximum number of pods each node can run (set by `--max-pods`, default 30). A 10-node cluster with the default setting consumes 300 VNet IPs plus 10 for the nodes themselves---310 total. If you have a /24 subnet (254 usable IPs), you cannot even run 10 nodes.

**Dynamic IP allocation** (Azure CNI with dynamic allocation) mitigates this. Instead of pre-allocating, it assigns IPs only when pods are actually created. This reduces waste but still requires careful subnet planning.

```bash
# Azure CNI with dynamic IP allocation
az aks create \
  --resource-group rg-aks-prod \
  --name aks-cni-dynamic \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --vnet-subnet-id "/subscriptions/{sub}/resourceGroups/rg-network/providers/Microsoft.Network/virtualNetworks/vnet-prod/subnets/aks-nodes" \
  --pod-subnet-id "/subscriptions/{sub}/resourceGroups/rg-network/providers/Microsoft.Network/virtualNetworks/vnet-prod/subnets/aks-pods" \
  --zones 1 2 3
```

### Azure CNI Overlay: Best of Both Worlds

CNI Overlay was introduced to solve the IP exhaustion problem while maintaining most of the benefits of Azure CNI. Nodes get IPs from the VNet subnet (just like Kubenet), but pods get IPs from a private overlay network (default 10.244.0.0/16). The magic is that pod-to-pod traffic uses an overlay tunnel, not UDRs, so you do not hit route table limits.

```text
    Azure VNet: 10.1.0.0/16
    ┌─────────────────────────────────────────────────────────────┐
    │  Node Subnet: 10.1.1.0/24 (only node IPs here)            │
    │                                                             │
    │  Node A (10.1.1.4)          Node B (10.1.1.5)               │
    │  ┌─────────────────┐       ┌─────────────────┐              │
    │  │ Overlay network  │       │ Overlay network  │              │
    │  │ Pod: 10.244.0.5  │       │ Pod: 10.244.1.8  │              │
    │  │ Pod: 10.244.0.6  │       │ Pod: 10.244.1.9  │              │
    │  └────────┬────────┘       └────────┬────────┘              │
    │           │    VXLAN/GENEVE tunnel    │                       │
    │           └──────────────────────────┘                       │
    │                                                             │
    │  Pod IPs are NOT routable from outside the cluster           │
    │  (use Services or Ingress to expose workloads)               │
    └─────────────────────────────────────────────────────────────┘
```

The trade-off: pod IPs are not directly routable from the VNet. Azure services that rely on direct pod IP connectivity (like certain VNet service endpoint configurations) will not work. For most microservices architectures where external traffic enters through a load balancer or ingress controller, this is perfectly fine.

```bash
# Create an AKS cluster with CNI Overlay
az aks create \
  --resource-group rg-aks-prod \
  --name aks-cni-overlay \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --pod-cidr 10.244.0.0/16 \
  --zones 1 2 3
```

### Azure CNI Powered by Cilium: The Future

CNI Powered by Cilium replaces the traditional Azure CNI dataplane with Cilium's eBPF-based dataplane. This gives you all the benefits of CNI Overlay (efficient IP usage) plus Cilium's advanced features: eBPF-based packet processing (no iptables), L7 network policies, transparent encryption, and DNS-aware egress filtering.

```text
    ┌─────────────────────────────────────────────────────────────┐
    │  Traditional Networking Stack    vs.   Cilium eBPF Stack    │
    │                                                             │
    │  Application                          Application           │
    │       │                                    │                │
    │       ▼                                    ▼                │
    │  Socket Layer                         Socket Layer          │
    │       │                                    │                │
    │       ▼                                    ▼                │
    │  iptables rules (thousands!)          eBPF programs         │
    │       │                               (compiled, fast)      │
    │       ▼                                    │                │
    │  Netfilter conntrack                       ▼                │
    │       │                               Direct to NIC         │
    │       ▼                               (bypass iptables      │
    │  Network Interface                     entirely)            │
    │                                                             │
    │  O(n) rule evaluation                 O(1) hash lookups     │
    └─────────────────────────────────────────────────────────────┘
```

This is the model Microsoft is actively investing in, and it is the recommended choice for new clusters as of 2025. The eBPF dataplane is not just faster---it fundamentally changes how packet processing scales. With iptables, adding more services linearly increases the number of rules every packet must traverse. With eBPF, lookups are hash-based and remain constant regardless of the number of services.

```bash
# Create an AKS cluster with CNI Powered by Cilium
az aks create \
  --resource-group rg-aks-prod \
  --name aks-cilium \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-dataplane cilium \
  --pod-cidr 10.244.0.0/16 \
  --zones 1 2 3 \
  --tier standard
```

### The Decision Matrix

| Feature | Kubenet | Azure CNI | CNI Overlay | CNI + Cilium |
| :--- | :--- | :--- | :--- | :--- |
| **VNet IPs per pod** | No (bridge IPs) | Yes | No (overlay IPs) | No (overlay IPs) |
| **IP consumption** | Low (node IPs only) | High (node + pod IPs) | Low (node IPs only) | Low (node IPs only) |
| **Max pods/node** | 250 | 250 | 250 | 250 |
| **Network policy engine** | Calico only | Azure NPM, Calico, Cilium | Azure NPM, Calico, Cilium | Cilium (native) |
| **eBPF dataplane** | No | No | No | Yes |
| **L7 network policies** | No | No | No | Yes |
| **Windows nodes** | No | Yes | Yes | Yes (preview) |
| **Direct pod VNet routing** | No (UDR) | Yes | No | No |
| **Recommended for new clusters** | No | Only if direct VNet routing needed | Good | Best |

---

## Network Policies: Controlling East-West Traffic

By default, every pod in a Kubernetes cluster can communicate with every other pod. This flat network is convenient for development but a security nightmare in production. Network policies let you define rules that control which pods can talk to which other pods.

AKS supports three network policy engines, and the choice is made at cluster creation time---you cannot change it later without rebuilding the cluster.

### Azure Network Policy Manager (Azure NPM)

Azure NPM implements Kubernetes NetworkPolicy resources using Azure-native constructs (iptables on Linux, HNS policies on Windows). It is the simplest option and supports all standard Kubernetes NetworkPolicy fields.

```yaml
# Block all ingress to pods in the database namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: database
spec:
  podSelector: {}
  policyTypes:
    - Ingress

---
# Allow only the API namespace to reach the database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
  namespace: database
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              team: api
      ports:
        - protocol: TCP
          port: 5432
```

### Calico: The Ecosystem Standard

Calico extends the standard Kubernetes NetworkPolicy with its own CRD-based policies that support additional features: global policies (apply across all namespaces), ordered policy evaluation, and CIDR-based rules for controlling traffic to external destinations.

```yaml
# Calico GlobalNetworkPolicy: deny egress to the internet except DNS
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: deny-egress-except-dns
spec:
  order: 100
  selector: "app != 'internet-proxy'"
  types:
    - Egress
  egress:
    - action: Allow
      protocol: UDP
      destination:
        ports:
          - 53
    - action: Allow
      protocol: TCP
      destination:
        ports:
          - 53
    - action: Allow
      destination:
        nets:
          - 10.0.0.0/8
    - action: Deny
```

### Cilium Network Policies: L7-Aware Security

Cilium policies operate at both L3/L4 (like traditional network policies) and L7 (HTTP, gRPC, Kafka, DNS). This means you can write policies that allow a pod to make GET requests to a specific API path but deny POST requests. You can also filter DNS queries, allowing pods to resolve only specific domain names.

```yaml
# CiliumNetworkPolicy: allow HTTP GET to /api/v1/products only
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-product-reads
  namespace: frontend
spec:
  endpointSelector:
    matchLabels:
      app: web-frontend
  egress:
    - toEndpoints:
        - matchLabels:
            app: product-api
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              - method: GET
                path: "/api/v1/products.*"
```

```yaml
# CiliumNetworkPolicy: DNS-based egress filtering
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-specific-domains
  namespace: backend
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  egress:
    - toFQDNs:
        - matchName: "api.stripe.com"
        - matchName: "api.paypal.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
    - toEndpoints:
        - matchLabels:
            "k8s:io.kubernetes.pod.namespace": kube-system
            "k8s:k8s-app": kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: ANY
          rules:
            dns:
              - matchPattern: "*.stripe.com"
              - matchPattern: "*.paypal.com"
```

This DNS-aware policy is transformative for security. Instead of maintaining IP allowlists for external services (which change constantly), you specify domain names. Cilium intercepts DNS queries, resolves them, and dynamically creates IP-based rules. If Stripe changes their API server IP, your policy automatically adapts.

---

## Ingress: Getting Traffic Into Your Cluster

AKS supports two primary ingress controllers as managed add-ons: Application Gateway Ingress Controller (AGIC) and the NGINX-based web application routing add-on.

### Application Gateway Ingress Controller (AGIC)

AGIC uses Azure Application Gateway (a layer-7 load balancer) as the ingress controller. The controller runs inside your cluster, watches for Kubernetes Ingress resources, and configures the Application Gateway accordingly.

```text
    Internet
        │
        ▼
    ┌──────────────────┐
    │ Azure Application │     WAF protection, SSL termination,
    │ Gateway (L7 LB)  │     path-based routing, autoscaling
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │          AKS Cluster                  │
    │                                      │
    │  ┌────────────┐  ┌────────────────┐  │
    │  │  AGIC Pod   │  │  Backend Pods  │  │
    │  │ (watches    │  │  (your apps)   │  │
    │  │  Ingress    │  │                │  │
    │  │  resources) │  │                │  │
    │  └────────────┘  └────────────────┘  │
    └──────────────────────────────────────┘
```

AGIC shines when you need Web Application Firewall (WAF) protection, SSL offloading at scale, or native integration with Azure services like Azure Front Door. It does not run an in-cluster proxy---traffic goes directly from the Application Gateway to the backend pods (if using Azure CNI with direct pod routing) or through the node's IP.

```bash
# Enable AGIC add-on with a new Application Gateway
az aks enable-addons \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --addons ingress-appgw \
  --appgw-name appgw-aks \
  --appgw-subnet-cidr "10.1.2.0/24"
```

### NGINX Ingress (Web Application Routing Add-on)

The web application routing add-on deploys an NGINX-based ingress controller managed by AKS. It integrates with Azure DNS for automatic DNS record creation and Azure Key Vault for TLS certificate management.

```bash
# Enable the web application routing add-on
az aks enable-addons \
  --resource-group rg-aks-prod \
  --name aks-prod-westeurope \
  --addons web_application_routing

# Verify the ingress controller is running
k get pods -n app-routing-system
```

```yaml
# Ingress resource using the web application routing add-on
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payment-api
  namespace: payments
  annotations:
    kubernetes.azure.com/tls-cert-keyvault-uri: "https://kv-aks-prod.vault.azure.net/certificates/payment-api-tls"
spec:
  ingressClassName: webapprouting.kubernetes.azure.com
  rules:
    - host: payments.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: payment-api
                port:
                  number: 8080
  tls:
    - hosts:
        - payments.example.com
      secretName: payment-api-tls
```

### When to Use Which

| Criteria | AGIC (App Gateway) | Web App Routing (NGINX) |
| :--- | :--- | :--- |
| **WAF protection** | Built-in (WAF v2) | Need external WAF or ModSecurity |
| **SSL termination scale** | Handles thousands of certs natively | Slower at high cert counts |
| **Custom NGINX config** | Not applicable | Full NGINX configuration available |
| **gRPC support** | Limited | Full support |
| **WebSocket support** | Yes | Yes |
| **Cost** | Application Gateway pricing (can be expensive) | Included in node cost |
| **Best for** | Enterprise apps with WAF requirements | General-purpose microservices |

---

## Private Clusters and Private Link: Hiding the API Server

By default, the AKS API server has a public endpoint. Anyone on the internet can attempt to reach it (authentication still blocks unauthorized access, but the endpoint is discoverable). For regulated industries and security-conscious organizations, this is unacceptable.

A private AKS cluster moves the API server behind an Azure Private Endpoint. The API server gets a private IP address in your VNet, and the public endpoint is disabled entirely.

```text
    Internet                    Your Azure VNet: 10.1.0.0/16
    ┌─────────┐                ┌─────────────────────────────────────┐
    │         │     ╳ BLOCKED  │                                     │
    │ Attacker│────────────╳   │  ┌──────────────────────────────┐   │
    │         │                │  │ Private Endpoint: 10.1.3.4   │   │
    └─────────┘                │  │ (AKS API Server)             │   │
                               │  └──────────────┬───────────────┘   │
    ┌─────────────────────┐    │                 │                   │
    │ Azure DevOps /      │    │  ┌──────────────▼───────────────┐   │
    │ GitHub Actions       │───┼─►│ Self-hosted build agent       │   │
    │ (with private agent) │    │  │ (runs in VNet)               │   │
    └─────────────────────┘    │  └──────────────────────────────┘   │
                               │                                     │
    ┌─────────────────────┐    │  ┌──────────────────────────────┐   │
    │ Developer laptop    │    │  │ AKS Nodes                     │   │
    │ (with VPN)          │────┼─►│ (communicate via private DNS) │   │
    └─────────────────────┘    │  └──────────────────────────────┘   │
                               └─────────────────────────────────────┘
```

```bash
# Create a private AKS cluster
az aks create \
  --resource-group rg-aks-prod \
  --name aks-private \
  --enable-private-cluster \
  --private-dns-zone system \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-dataplane cilium \
  --zones 1 2 3

# Verify the API server is private
az aks show -g rg-aks-prod -n aks-private \
  --query "apiServerAccessProfile" -o json
```

The `--private-dns-zone system` option creates an Azure Private DNS Zone in the MC_ resource group. AKS nodes resolve the API server FQDN through this private zone, getting the private IP instead of a public one. For the developer workstations and CI/CD agents to access the cluster, they must be on the VNet (or peered VNet) and have DNS resolution configured to use the private zone.

### API Management Integration

For clusters that need to expose APIs externally with enterprise-grade management, Azure API Management (APIM) sits in front of the cluster and provides rate limiting, authentication, request/response transformation, caching, and developer portal features.

```bash
# Create API Management instance in the same VNet
az apim create \
  --name apim-aks-prod \
  --resource-group rg-aks-prod \
  --publisher-name "Contoso" \
  --publisher-email "platform@contoso.com" \
  --sku-name Developer \
  --virtual-network Internal \
  --virtual-network-type Internal

# Import an API from your AKS service
az apim api import \
  --resource-group rg-aks-prod \
  --service-name apim-aks-prod \
  --path "/payments" \
  --api-id "payment-api" \
  --specification-format OpenApiJson \
  --specification-url "http://payment-api.payments.svc.cluster.local:8080/openapi.json"
```

---

## Egress Control: Managing Outbound Traffic

By default, AKS nodes use an Azure Load Balancer with outbound rules for internet access. Every node shares a pool of public IPs for outbound connections. For production clusters, you often need more control: which pods can reach the internet, which domains they can access, and what source IP they present.

### Azure NAT Gateway

For predictable outbound IPs (important when whitelisting with external partners), attach a NAT Gateway to your AKS subnet:

```bash
# Create a NAT Gateway with a static public IP
az network public-ip create \
  --resource-group rg-aks-prod \
  --name pip-aks-egress \
  --sku Standard \
  --allocation-method Static

az network nat gateway create \
  --resource-group rg-aks-prod \
  --name natgw-aks \
  --public-ip-addresses pip-aks-egress \
  --idle-timeout 10

# Associate with the AKS subnet
az network vnet subnet update \
  --resource-group rg-aks-prod \
  --vnet-name vnet-prod \
  --name aks-nodes \
  --nat-gateway natgw-aks
```

### Azure Firewall for Centralized Egress

For enterprise environments, Azure Firewall or a third-party NVA provides centralized egress with FQDN filtering, threat intelligence, and logging:

```bash
# Route all egress through Azure Firewall
az network route-table create \
  --resource-group rg-aks-prod \
  --name rt-aks-egress

az network route-table route create \
  --resource-group rg-aks-prod \
  --route-table-name rt-aks-egress \
  --name default-route \
  --address-prefix 0.0.0.0/0 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.1.4.4  # Azure Firewall private IP
```

---

## Did You Know?

1. **Azure CNI Powered by Cilium replaces kube-proxy entirely.** In a traditional AKS cluster, kube-proxy maintains iptables rules on every node to implement Kubernetes Services. With Cilium, kube-proxy is not deployed at all. Cilium handles service routing using eBPF maps, which provide O(1) lookup performance compared to iptables' O(n) rule traversal. On clusters with over 5,000 services, this difference can reduce service routing latency by more than 60%.

2. **The maximum number of pods per node in AKS is 250, regardless of CNI plugin.** This is an Azure VMSS limitation, not a Kubernetes one. However, most teams find that 110 (the default for Azure CNI) is optimal. Going higher means more IP addresses consumed per node (with Azure CNI) and more kubelet overhead for pod lifecycle management.

3. **AKS Private Link costs nothing beyond the standard cluster pricing.** The Private Endpoint for the API server is included in the AKS service at no additional charge. However, the operational cost is significant---you need VPN or ExpressRoute connectivity for developer access, self-hosted CI/CD agents in the VNet, and proper DNS configuration. Many teams underestimate this operational overhead.

4. **Cilium's eBPF-based network policies are enforced at the kernel level before the packet reaches the application.** This means a compromised application cannot bypass network policies by manipulating its own network stack. Traditional iptables-based policies operate in the same kernel namespace, but eBPF programs are loaded and verified by the kernel itself, providing a stronger isolation boundary.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Choosing Azure CNI without sizing subnets for pod IP consumption | Teams use existing small subnets from on-prem thinking | Calculate: (max_nodes x max_pods_per_node) + max_nodes. Use /20 or larger for production Azure CNI |
| Using Kubenet for production workloads with many services | It worked fine in dev with 5 services | Use CNI Overlay or CNI Powered by Cilium for production. Kubenet has inherent scaling limits |
| Not deploying network policies at all | "We'll add security later" | Deploy default-deny policies from day one. It is far easier to allowlist than to retroactively lock down |
| Mixing network policy engines (e.g., applying Calico CRDs on a Cilium cluster) | Confusion about which engine is active | Check your cluster's network policy setting; only use CRDs for the active engine |
| Creating a private cluster without planning for CI/CD access | Developers can kubectl from laptops, so CI/CD should work too | Private clusters block all public access. Deploy self-hosted agents in the VNet or use AKS command invoke |
| Deploying AGIC without understanding Application Gateway pricing | AGIC seems like the "enterprise" choice | Application Gateway WAF v2 costs $325+/month base. Use web application routing add-on unless you specifically need WAF |
| Not configuring egress control | Default load balancer outbound rules are "good enough" | Use NAT Gateway for static IPs. Use Azure Firewall for FQDN filtering. Pods should not have unrestricted internet access |
| Ignoring DNS resolution in private clusters | kubectl works from the VNet but not from CI/CD agents | Ensure all clients can resolve the private DNS zone. Use conditional DNS forwarding or Azure Private DNS resolver |

---

## Quiz

<details>
<summary>1. What is the key architectural difference between Azure CNI and CNI Overlay?</summary>

Azure CNI assigns every pod an IP address directly from the Azure VNet subnet, making pods first-class network citizens reachable by any VNet-connected resource. CNI Overlay assigns pods IP addresses from a separate overlay network (default 10.244.0.0/16), and only nodes get VNet IPs. This means CNI Overlay uses far fewer VNet IPs (only one per node instead of one per pod), but pod IPs are not directly routable from outside the cluster. For most microservices architectures where traffic enters through a load balancer or ingress controller, CNI Overlay is the better choice because it eliminates IP exhaustion concerns.
</details>

<details>
<summary>2. Why does Azure CNI Powered by Cilium not deploy kube-proxy?</summary>

Cilium replaces kube-proxy's functionality entirely using eBPF programs. Instead of maintaining iptables rules for Service routing (which kube-proxy does), Cilium programs eBPF maps directly in the Linux kernel. These maps provide O(1) hash-based lookups for service resolution, compared to iptables' O(n) sequential rule evaluation. This means service routing performance remains constant regardless of how many services exist in the cluster. Eliminating kube-proxy also removes a component that consumes CPU and memory on every node and can become a bottleneck in large clusters.
</details>

<details>
<summary>3. How do Cilium L7 network policies differ from standard Kubernetes NetworkPolicy?</summary>

Standard Kubernetes NetworkPolicy operates at L3/L4---it can filter by source/destination IP, namespace, pod label, and port number. Cilium L7 policies extend this to the application layer: you can filter HTTP traffic by method and path (e.g., allow GET /api/products but deny DELETE), filter gRPC by service and method name, filter Kafka by topic, and filter DNS queries by domain name. This allows much more granular security. For example, a payment service can be restricted to only resolve and connect to api.stripe.com on port 443, with all other DNS queries and egress connections blocked.
</details>

<details>
<summary>4. What happens when you create a private AKS cluster, and how does it affect CI/CD pipelines?</summary>

A private AKS cluster places the API server behind an Azure Private Endpoint, giving it a private IP address within your VNet. The public endpoint is disabled entirely. This means the API server is unreachable from the internet, including from cloud-hosted CI/CD services like GitHub Actions or Azure DevOps hosted agents. To run kubectl commands against a private cluster from CI/CD, you must either deploy self-hosted build agents within the VNet (or a peered VNet), use the `az aks command invoke` feature (which tunnels commands through the Azure management plane), or set up VPN connectivity between your CI/CD environment and the VNet.
</details>

<details>
<summary>5. When should you choose AGIC over the web application routing (NGINX) add-on?</summary>

Choose AGIC when you specifically need Web Application Firewall (WAF) protection, which Application Gateway provides natively with OWASP rule sets and bot protection. AGIC is also the better choice when you need to handle thousands of TLS certificates at scale, require native integration with Azure Front Door for global load balancing, or need the traffic to bypass the cluster entirely (Application Gateway routes directly to pod IPs on Azure CNI). For general-purpose microservices that need standard ingress with gRPC support, custom NGINX configuration, or cost-effective routing, the web application routing add-on is sufficient and significantly cheaper.
</details>

<details>
<summary>6. What is the purpose of a NAT Gateway in AKS egress architecture?</summary>

A NAT Gateway provides predictable, static outbound IP addresses for all traffic leaving the AKS subnet. Without it, AKS uses the Azure Load Balancer's outbound rules, which may assign traffic to different public IPs from a pool, and the IP allocation can change. A static outbound IP is essential when external partners or SaaS providers whitelist your traffic by source IP address. NAT Gateway also provides higher SNAT port allocation (up to 64,512 ports per public IP) compared to the load balancer's default, preventing SNAT exhaustion in clusters with many outbound connections.
</details>

<details>
<summary>7. Why can you not change the network policy engine after cluster creation?</summary>

The network policy engine is deeply integrated into the cluster's networking stack. Azure NPM uses iptables rules and Azure-native constructs. Calico installs its own DaemonSet (calico-node) with BGP peering and Felix for policy enforcement. Cilium replaces kube-proxy entirely and loads eBPF programs into the kernel. Switching engines would require tearing down one engine's state (rules, routes, eBPF programs) and installing another, which cannot be done safely on a running cluster without risking network connectivity loss for all pods. This is why the decision matters so much at cluster creation time.
</details>

---

## Hands-On Exercise: CNI Powered by Cilium with L7 Egress Domain Filtering

In this exercise, you will deploy an AKS cluster with CNI Powered by Cilium and implement L7-aware egress policies that restrict pods to specific external domains.

### Prerequisites

- Azure CLI with aks-preview extension (`az extension add --name aks-preview`)
- An Azure subscription with Contributor access
- kubectl and kubelogin installed

### Task 1: Deploy AKS with CNI Powered by Cilium

Create a cluster with the Cilium dataplane and verify it is operational.

<details>
<summary>Solution</summary>

```bash
# Create a resource group
az group create --name rg-aks-cilium --location westeurope

# Create the cluster with Cilium
az aks create \
  --resource-group rg-aks-cilium \
  --name aks-cilium-lab \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-dataplane cilium \
  --pod-cidr 10.244.0.0/16 \
  --node-count 3 \
  --node-vm-size Standard_D4s_v5 \
  --zones 1 2 3 \
  --tier standard \
  --generate-ssh-keys

# Get credentials
az aks get-credentials -g rg-aks-cilium -n aks-cilium-lab --overwrite-existing

# Verify Cilium is running
k get pods -n kube-system -l k8s-app=cilium -o wide

# Verify kube-proxy is NOT running (Cilium replaces it)
k get pods -n kube-system -l component=kube-proxy
# Expected: No resources found

# Check Cilium status
k exec -n kube-system -l k8s-app=cilium -- cilium status --brief
```

</details>

### Task 2: Deploy Test Workloads

Deploy a frontend and backend service with clearly defined communication requirements.

<details>
<summary>Solution</summary>

```bash
# Create namespaces
k create namespace frontend
k create namespace backend

# Deploy backend (payment service that needs to reach Stripe)
k apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
        - name: payment
          image: curlimages/curl:8.5.0
          command: ["sleep", "infinity"]
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: payment-service
  namespace: backend
spec:
  selector:
    app: payment-service
  ports:
    - port: 8080
      targetPort: 8080
EOF

# Deploy frontend (web app that calls the payment service)
k apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
  namespace: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-frontend
  template:
    metadata:
      labels:
        app: web-frontend
    spec:
      containers:
        - name: web
          image: curlimages/curl:8.5.0
          command: ["sleep", "infinity"]
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
EOF

# Verify pods are running
k get pods -n backend
k get pods -n frontend
```

</details>

### Task 3: Apply Default-Deny Network Policies

Lock down both namespaces with default-deny policies before adding allowlists.

<details>
<summary>Solution</summary>

```yaml
# Save as default-deny.yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: default-deny-all
  namespace: backend
spec:
  endpointSelector: {}
  ingress:
    - {}
  egress:
    - {}

---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: default-deny-all
  namespace: frontend
spec:
  endpointSelector: {}
  ingress:
    - {}
  egress:
    - {}
```

```bash
# Apply the deny-all policies
k apply -f default-deny.yaml

# Verify that the payment service can no longer reach the internet
PAYMENT_POD=$(k get pod -n backend -l app=payment-service -o jsonpath='{.items[0].metadata.name}')
k exec -n backend "$PAYMENT_POD" -- curl -s --max-time 5 https://httpbin.org/get
# Expected: timeout (connection blocked)
```

Note: The default-deny policy above uses empty ingress/egress rules, which blocks everything that is not explicitly allowed by another policy. This is the recommended starting point for any production namespace.

</details>

### Task 4: Implement L7 Egress Domain Filtering

Allow the payment service to reach only specific external domains (Stripe and the cluster's DNS).

<details>
<summary>Solution</summary>

```yaml
# Save as payment-egress-policy.yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: payment-egress-domains
  namespace: backend
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  egress:
    # Allow DNS resolution for permitted domains only
    - toEndpoints:
        - matchLabels:
            "k8s:io.kubernetes.pod.namespace": kube-system
            "k8s:k8s-app": kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: ANY
          rules:
            dns:
              - matchPattern: "*.stripe.com"
              - matchPattern: "api.stripe.com"
              - matchPattern: "httpbin.org"
    # Allow HTTPS to resolved Stripe IPs
    - toFQDNs:
        - matchName: "api.stripe.com"
        - matchName: "httpbin.org"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
    # Allow communication within the cluster
    - toEndpoints:
        - matchLabels:
            "k8s:io.kubernetes.pod.namespace": frontend
```

```bash
k apply -f payment-egress-policy.yaml

# Test: payment service can reach httpbin.org (our stand-in for Stripe)
k exec -n backend "$PAYMENT_POD" -- curl -s --max-time 10 https://httpbin.org/get | head -5
# Expected: success (JSON response)

# Test: payment service CANNOT reach google.com
k exec -n backend "$PAYMENT_POD" -- curl -s --max-time 5 https://www.google.com
# Expected: timeout (domain not in allowlist)

# Test: payment service CANNOT reach example.com
k exec -n backend "$PAYMENT_POD" -- curl -s --max-time 5 https://example.com
# Expected: timeout (domain not in allowlist)
```

</details>

### Task 5: Allow Frontend-to-Backend Communication

Configure policies so the frontend can reach the payment service on port 8080 but nothing else.

<details>
<summary>Solution</summary>

```yaml
# Save as frontend-to-backend.yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: frontend-to-payment
  namespace: frontend
spec:
  endpointSelector:
    matchLabels:
      app: web-frontend
  egress:
    # Allow DNS
    - toEndpoints:
        - matchLabels:
            "k8s:io.kubernetes.pod.namespace": kube-system
            "k8s:k8s-app": kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: ANY
    # Allow reaching payment service in backend namespace
    - toEndpoints:
        - matchLabels:
            "k8s:io.kubernetes.pod.namespace": backend
            app: payment-service
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP

---
# Update backend ingress to allow frontend traffic
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend-ingress
  namespace: backend
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  ingress:
    - fromEndpoints:
        - matchLabels:
            "k8s:io.kubernetes.pod.namespace": frontend
            app: web-frontend
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
```

```bash
k apply -f frontend-to-backend.yaml

# Verify the Cilium policies are loaded
k get ciliumnetworkpolicies -A

# Check Cilium's policy enforcement status
k exec -n kube-system -l k8s-app=cilium -- cilium endpoint list
```

</details>

### Task 6: Verify the Complete Security Posture

Run a comprehensive test to confirm all policies are working as expected.

<details>
<summary>Solution</summary>

```bash
PAYMENT_POD=$(k get pod -n backend -l app=payment-service -o jsonpath='{.items[0].metadata.name}')
FRONTEND_POD=$(k get pod -n frontend -l app=web-frontend -o jsonpath='{.items[0].metadata.name}')

echo "=== Test 1: Payment service -> httpbin.org (should SUCCEED) ==="
k exec -n backend "$PAYMENT_POD" -- curl -s --max-time 10 -o /dev/null -w "%{http_code}" https://httpbin.org/get

echo ""
echo "=== Test 2: Payment service -> google.com (should FAIL) ==="
k exec -n backend "$PAYMENT_POD" -- curl -s --max-time 5 -o /dev/null -w "%{http_code}" https://www.google.com || echo "BLOCKED"

echo ""
echo "=== Test 3: Frontend -> internet (should FAIL) ==="
k exec -n frontend "$FRONTEND_POD" -- curl -s --max-time 5 -o /dev/null -w "%{http_code}" https://httpbin.org/get || echo "BLOCKED"

echo ""
echo "=== Test 4: Cilium policy verdict log ==="
k exec -n kube-system -l k8s-app=cilium -- cilium monitor --type policy-verdict --last 10
```

</details>

### Success Criteria

- [ ] AKS cluster running with CNI Powered by Cilium (kube-proxy absent)
- [ ] Cilium agent pods healthy on all nodes
- [ ] Default-deny CiliumNetworkPolicies applied in both namespaces
- [ ] Payment service can resolve and reach api.stripe.com / httpbin.org on port 443
- [ ] Payment service cannot reach any other external domain (google.com, example.com)
- [ ] Frontend can reach payment-service on port 8080
- [ ] Frontend cannot reach the internet directly
- [ ] Cilium policy verdict logs show allowed and denied connections

---

## Next Module

[Module 7.3: AKS Workload Identity & Security](../module-7.3-aks-identity/) --- Learn how to eliminate hardcoded credentials entirely using Entra Workload Identity, federated identity credentials, and the Secrets Store CSI Driver with Azure Key Vault integration.
