---
title: "Module 3.2: Virtual Networks (VNet)"
slug: cloud/azure-essentials/module-3.2-vnet
sidebar:
  order: 3
---
**Complexity**: [COMPLEX] | **Time to Complete**: 3h | **Prerequisites**: Module 3.1 (Entra ID & RBAC)

## Why This Module Matters

In June 2023, an e-commerce platform running on Azure experienced a complete outage during their biggest sale of the year. The root cause was breathtakingly simple: a developer in the platform team had changed the address space of a spoke VNet from `10.1.0.0/16` to `10.2.0.0/16` to "clean up the IP scheme." What they did not realize was that this change broke the VNet peering connection to the hub network, which contained the shared DNS resolver and the VPN gateway connecting to their on-premises payment processing system. Every microservice lost DNS resolution simultaneously. The payment gateway became unreachable. The outage lasted 4 hours and 22 minutes, costing the company an estimated $3.8 million in lost revenue and eroding customer trust during their most critical business period.

Networking in Azure is invisible when it works and catastrophic when it breaks. Unlike compute resources that you can scale up with a button click, or storage that you can provision in seconds, networking mistakes often cascade across your entire infrastructure. A misconfigured Network Security Group can silently block traffic for hours before anyone notices. An overlapping address space between two VNets makes peering impossible. A missing route table entry sends production traffic into a black hole.

In this module, you will learn Azure networking from the ground up. You will understand VNets and subnets, how Network Security Groups filter traffic, how VNet peering connects separate networks, and how to design the hub-and-spoke topology that forms the backbone of enterprise Azure deployments. By the end, you will be able to design and implement a multi-VNet architecture where spoke networks route all egress traffic through a central hub---a pattern you will encounter in virtually every production Azure environment.

---

## VNets and Subnets: Your Private Network in the Cloud

An Azure Virtual Network (VNet) is a logically isolated network in Azure that closely mirrors a traditional network you would operate in your own data center. Think of a VNet as renting an empty floor in an office building. The floor is yours---you decide how to divide it into rooms (subnets), who can enter and leave (NSGs), and which floors you want to connect to (peering).

### VNet Fundamentals

Every VNet has an **address space** defined using CIDR notation. This is the range of private IP addresses available for use within the VNet. Azure supports the standard RFC 1918 private address ranges:

| Range | CIDR | Available Addresses | Typical Use |
| :--- | :--- | :--- | :--- |
| 10.0.0.0 - 10.255.255.255 | 10.0.0.0/8 | ~16.7 million | Large enterprise networks |
| 172.16.0.0 - 172.31.255.255 | 172.16.0.0/12 | ~1 million | Medium-sized deployments |
| 192.168.0.0 - 192.168.255.255 | 192.168.0.0/16 | ~65,000 | Small networks, labs |

A VNet is **regional**---it exists in a single Azure region. A VNet in East US and a VNet in West Europe are completely separate, isolated networks. To connect them, you need VNet peering (which we will cover shortly).

```bash
# Create a VNet with a /16 address space (65,536 addresses)
az network vnet create \
  --resource-group myRG \
  --name hub-vnet \
  --address-prefix 10.0.0.0/16 \
  --location eastus2

# You can add multiple address spaces to a single VNet
az network vnet update \
  --resource-group myRG \
  --name hub-vnet \
  --add addressSpace.addressPrefixes "10.100.0.0/16"
```

### Subnets: Dividing Your Network

Subnets are subdivisions of your VNet's address space. Every Azure resource that needs a private IP address (VMs, load balancers, private endpoints, etc.) must be placed in a subnet. Subnets serve two purposes: **organization** (grouping related resources) and **security** (applying NSGs at the subnet level).

```text
    ┌─────────────────────────────────────────────────────────┐
    │              VNet: hub-vnet (10.0.0.0/16)               │
    │                                                         │
    │  ┌─────────────────┐  ┌─────────────────┐              │
    │  │   Subnet:       │  │   Subnet:       │              │
    │  │   frontend      │  │   backend       │              │
    │  │   10.0.1.0/24   │  │   10.0.2.0/24   │              │
    │  │   251 usable    │  │   251 usable    │              │
    │  │                 │  │                 │              │
    │  │  [VM] [VM] [VM] │  │  [VM] [DB]      │              │
    │  └─────────────────┘  └─────────────────┘              │
    │                                                         │
    │  ┌─────────────────┐  ┌─────────────────────────────┐  │
    │  │   Subnet:       │  │   Subnet:                   │  │
    │  │ AzureFirewallSubnet│  │   GatewaySubnet             │  │
    │  │   10.0.3.0/26   │  │   10.0.255.0/27             │  │
    │  │   59 usable     │  │   27 usable                 │  │
    │  │                 │  │                             │  │
    │  │  [AZ Firewall]  │  │  [VPN GW] or [ExpressRoute] │  │
    │  └─────────────────┘  └─────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘

    Note: Azure reserves 5 IPs per subnet:
    .0 (network), .1 (gateway), .2 & .3 (DNS), .255 (broadcast)
    So a /24 gives 256 - 5 = 251 usable addresses.
```

**Critical detail**: Azure reserves **5 IP addresses** in every subnet. For a /24 subnet (256 addresses), you get 251 usable. For a /27 (32 addresses), you get 27. For a /29 (8 addresses), you get only 3. This matters when you are sizing subnets for services like AKS that consume many IPs.

Some subnets have **special names** that Azure requires for specific services:

| Subnet Name | Required For | Minimum Size |
| :--- | :--- | :--- |
| `GatewaySubnet` | VPN Gateway, ExpressRoute Gateway | /27 recommended |
| `AzureFirewallSubnet` | Azure Firewall | /26 required |
| `AzureFirewallManagementSubnet` | Azure Firewall (forced tunneling) | /26 required |
| `AzureBastionSubnet` | Azure Bastion | /26 or larger |
| `RouteServerSubnet` | Azure Route Server | /27 required |

```bash
# Create subnets within the VNet
az network vnet subnet create \
  --resource-group myRG \
  --vnet-name hub-vnet \
  --name frontend \
  --address-prefix 10.0.1.0/24

az network vnet subnet create \
  --resource-group myRG \
  --vnet-name hub-vnet \
  --name backend \
  --address-prefix 10.0.2.0/24

# Create the special GatewaySubnet
az network vnet subnet create \
  --resource-group myRG \
  --vnet-name hub-vnet \
  --name GatewaySubnet \
  --address-prefix 10.0.255.0/27

# List all subnets in a VNet
az network vnet subnet list --resource-group myRG --vnet-name hub-vnet -o table
```

---

## Network Security Groups (NSGs): Your Subnet-Level Firewall

A Network Security Group is a stateful firewall that filters network traffic to and from Azure resources. NSGs contain **security rules** that allow or deny traffic based on source, destination, port, and protocol. You can attach an NSG to a **subnet** (recommended) or to a **network interface** (for granular per-VM control).

### How NSG Rules Are Evaluated

NSG rules have a **priority** (100-4096, lower number = higher priority). Azure evaluates rules from lowest priority number to highest and stops at the first match.

```text
    Inbound Traffic Evaluation:

    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │  Subnet NSG  │ ──> │   NIC NSG    │ ──> │   Resource   │
    │  (if exists) │     │  (if exists) │     │   (VM, etc)  │
    └──────────────┘     └──────────────┘     └──────────────┘

    Both NSGs must ALLOW the traffic. If either denies it, traffic is dropped.

    Outbound Traffic Evaluation:

    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │   Resource   │ ──> │   NIC NSG    │ ──> │  Subnet NSG  │
    │   (VM, etc)  │     │  (if exists) │     │  (if exists) │
    └──────────────┘     └──────────────┘     └──────────────┘

    Note: For outbound, NIC NSG is evaluated FIRST, then Subnet NSG.
```

Every NSG includes **default rules** that you cannot delete:

| Priority | Name | Direction | Action | Source | Destination |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 65000 | AllowVnetInBound | Inbound | Allow | VirtualNetwork | VirtualNetwork |
| 65001 | AllowAzureLoadBalancerInBound | Inbound | Allow | AzureLoadBalancer | * |
| 65500 | DenyAllInBound | Inbound | Deny | * | * |
| 65000 | AllowVnetOutBound | Outbound | Allow | VirtualNetwork | VirtualNetwork |
| 65001 | AllowInternetOutBound | Outbound | Allow | * | Internet |
| 65500 | DenyAllOutBound | Outbound | Deny | * | * |

The `VirtualNetwork` service tag includes the VNet address space, all peered VNet address spaces, and on-premises address spaces connected via VPN/ExpressRoute. This is important---by default, all traffic within the VNet (and peered VNets) is allowed.

```bash
# Create an NSG
az network nsg create \
  --resource-group myRG \
  --name frontend-nsg

# Allow HTTPS inbound from the internet
az network nsg rule create \
  --resource-group myRG \
  --nsg-name frontend-nsg \
  --name AllowHTTPS \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes Internet \
  --destination-port-ranges 443

# Allow SSH only from your IP
MY_IP=$(curl -s ifconfig.me)
az network nsg rule create \
  --resource-group myRG \
  --nsg-name frontend-nsg \
  --name AllowSSH \
  --priority 110 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes "$MY_IP/32" \
  --destination-port-ranges 22

# Associate NSG with a subnet
az network vnet subnet update \
  --resource-group myRG \
  --vnet-name hub-vnet \
  --name frontend \
  --network-security-group frontend-nsg

# View effective NSG rules for a VM's NIC
az network nic list-effective-nsg \
  --resource-group myRG \
  --name myVM-nic -o table
```

### Application Security Groups (ASGs)

ASGs let you group VMs logically and write NSG rules using those groups instead of explicit IP addresses. This is powerful when you have dynamic environments where VMs are created and destroyed frequently.

```bash
# Create ASGs
az network asg create --resource-group myRG --name web-servers
az network asg create --resource-group myRG --name db-servers

# Create NSG rule using ASGs instead of IPs
az network nsg rule create \
  --resource-group myRG \
  --nsg-name backend-nsg \
  --name AllowWebToDb \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-asgs web-servers \
  --destination-asgs db-servers \
  --destination-port-ranges 5432

# Associate a VM's NIC with an ASG
az network nic ip-config update \
  --resource-group myRG \
  --nic-name web-vm-nic \
  --name ipconfig1 \
  --application-security-groups web-servers
```

**War Story**: A team at a healthcare company had 200+ NSG rules referencing individual IP addresses. Every time a VM was replaced (which happened weekly due to immutable infrastructure practices), someone had to update the NSG rules. They frequently forgot, causing intermittent connectivity failures that took hours to diagnose. Switching to ASGs reduced their NSG rules from 200+ to 18, and new VMs automatically inherited the correct network access by simply being associated with the right ASG.

---

## VNet Peering: Connecting Networks

VNet peering creates a direct, high-bandwidth, low-latency connection between two VNets. Traffic between peered VNets travels over the Microsoft backbone network---it never touches the public internet. Peering works across regions (called **global VNet peering**) and even across Azure subscriptions and Entra ID tenants.

### How Peering Works

Peering is **non-transitive**. If VNet A is peered with VNet B, and VNet B is peered with VNet C, VNet A **cannot** reach VNet C through VNet B (unless you configure User-Defined Routes to force it, which is exactly what the hub-and-spoke topology does).

```text
    Non-Transitive Peering:

    ┌───────┐     peered      ┌───────┐     peered      ┌───────┐
    │ VNet A│ ◄─────────────► │ VNet B│ ◄─────────────► │ VNet C│
    └───────┘                 └───────┘                 └───────┘

    A can reach B: YES
    B can reach C: YES
    A can reach C: NO (peering is not transitive)


    Hub-and-Spoke with Transit:

    ┌─────────┐          ┌──────────────┐          ┌─────────┐
    │ Spoke A │ ◄──────► │     Hub      │ ◄──────► │ Spoke B │
    │         │          │ (NVA/Firewall)│          │         │
    └─────────┘          └──────────────┘          └─────────┘

    A can reach B: YES (traffic routes through Hub's NVA/Firewall)
    Requires: UDR on spoke subnets + "Allow Forwarded Traffic" on peering
```

```bash
# Create two VNets
az network vnet create -g myRG -n spoke1-vnet --address-prefix 10.1.0.0/16 --location eastus2
az network vnet create -g myRG -n spoke2-vnet --address-prefix 10.2.0.0/16 --location eastus2

# Get VNet resource IDs
HUB_VNET_ID=$(az network vnet show -g myRG -n hub-vnet --query id -o tsv)
SPOKE1_VNET_ID=$(az network vnet show -g myRG -n spoke1-vnet --query id -o tsv)

# Create peering: Hub → Spoke1
az network vnet peering create \
  --resource-group myRG \
  --name hub-to-spoke1 \
  --vnet-name hub-vnet \
  --remote-vnet "$SPOKE1_VNET_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic \
  --allow-gateway-transit    # Hub shares its gateway with spokes

# Create peering: Spoke1 → Hub
az network vnet peering create \
  --resource-group myRG \
  --name spoke1-to-hub \
  --vnet-name spoke1-vnet \
  --remote-vnet "$HUB_VNET_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic \
  --use-remote-gateways      # Spoke uses Hub's gateway

# Verify peering status
az network vnet peering list -g myRG --vnet-name hub-vnet -o table
```

Key peering flags explained:

| Flag | Meaning |
| :--- | :--- |
| `--allow-vnet-access` | Allow traffic between the peered VNets (almost always yes) |
| `--allow-forwarded-traffic` | Accept traffic that did not originate in the peer VNet (needed for transit routing) |
| `--allow-gateway-transit` | Set on the hub---lets spokes use the hub's VPN/ExpressRoute gateway |
| `--use-remote-gateways` | Set on the spoke---tells it to use the hub's gateway for on-prem connectivity |

**Critical rule**: Peered VNets **cannot have overlapping address spaces**. If hub-vnet uses `10.0.0.0/16` and spoke1-vnet also uses `10.0.0.0/16`, peering creation will fail. Plan your IP address scheme carefully before you start building.

---

## Azure Firewall and Route Tables: Controlling Traffic Flow

### User-Defined Routes (UDRs)

By default, Azure routes traffic between subnets within a VNet and between peered VNets automatically using **system routes**. But in a hub-and-spoke topology, you want spoke traffic to go through a firewall or network virtual appliance (NVA) in the hub. This is where User-Defined Routes come in.

A **Route Table** is a collection of routes that you associate with a subnet. When a route table is associated with a subnet, it overrides the default system routes.

```bash
# Create a route table for spoke subnets
az network route-table create \
  --resource-group myRG \
  --name spoke-route-table \
  --disable-bgp-route-propagation true

# Add a default route that sends all traffic to the hub firewall
az network route-table route create \
  --resource-group myRG \
  --route-table-name spoke-route-table \
  --name default-to-firewall \
  --address-prefix 0.0.0.0/0 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.3.4    # Azure Firewall's private IP

# Associate route table with spoke subnet
az network vnet subnet update \
  --resource-group myRG \
  --vnet-name spoke1-vnet \
  --name workload \
  --route-table spoke-route-table
```

### Azure Firewall

Azure Firewall is a managed, cloud-based network security service. Unlike NSGs (which operate at Layer 3/4), Azure Firewall can inspect traffic at Layer 7 (application level), performing URL filtering, TLS inspection, and threat intelligence-based filtering.

```text
    ┌──────────────────────────────────────────────────────────┐
    │                  Azure Firewall Features                 │
    ├──────────────────┬───────────────────────────────────────┤
    │  NSG (Layer 3/4) │  Azure Firewall (Layer 3-7)          │
    ├──────────────────┼───────────────────────────────────────┤
    │ IP-based rules   │ IP, FQDN, URL-based rules            │
    │ Port filtering   │ Port + protocol + app inspection     │
    │ Stateful         │ Stateful + threat intelligence       │
    │ Free             │ ~$912/month (Standard) + data costs  │
    │ Per-subnet       │ Centralized (hub)                    │
    │ No logging       │ Full diagnostic logging              │
    │ No TLS inspect   │ TLS inspection (Premium)             │
    └──────────────────┴───────────────────────────────────────┘
```

```bash
# Create Azure Firewall subnet (must be named exactly AzureFirewallSubnet)
az network vnet subnet create \
  --resource-group myRG \
  --vnet-name hub-vnet \
  --name AzureFirewallSubnet \
  --address-prefix 10.0.3.0/26

# Create public IP for the firewall
az network public-ip create \
  --resource-group myRG \
  --name fw-public-ip \
  --sku Standard \
  --allocation-method Static

# Create Azure Firewall
az network firewall create \
  --resource-group myRG \
  --name hub-firewall \
  --location eastus2 \
  --sku AZFW_VNet \
  --tier Standard

# Configure the firewall IP
az network firewall ip-config create \
  --resource-group myRG \
  --firewall-name hub-firewall \
  --name fw-ipconfig \
  --public-ip-address fw-public-ip \
  --vnet-name hub-vnet

# Get the firewall's private IP (for route tables)
FW_PRIVATE_IP=$(az network firewall show -g myRG -n hub-firewall \
  --query "ipConfigurations[0].privateIPAddress" -o tsv)
echo "Firewall private IP: $FW_PRIVATE_IP"

# Create a network rule collection (allow spoke-to-spoke traffic)
az network firewall network-rule create \
  --resource-group myRG \
  --firewall-name hub-firewall \
  --collection-name "spoke-to-spoke" \
  --priority 200 \
  --action Allow \
  --name "allow-all-spokes" \
  --protocols Any \
  --source-addresses "10.1.0.0/16" "10.2.0.0/16" \
  --destination-addresses "10.1.0.0/16" "10.2.0.0/16" \
  --destination-ports "*"

# Create an application rule (allow outbound HTTPS to specific FQDNs)
az network firewall application-rule create \
  --resource-group myRG \
  --firewall-name hub-firewall \
  --collection-name "allowed-websites" \
  --priority 300 \
  --action Allow \
  --name "allow-updates" \
  --protocols Https=443 \
  --source-addresses "10.1.0.0/16" "10.2.0.0/16" \
  --fqdn-tags "AzureKubernetesService" \
  --target-fqdns "*.ubuntu.com" "packages.microsoft.com"
```

---

## VPN Gateway vs ExpressRoute: Connecting to On-Premises

When you need to connect your Azure VNets to an on-premises data center (or another cloud), you have two options.

| Feature | VPN Gateway | ExpressRoute |
| :--- | :--- | :--- |
| **Connection type** | IPSec/IKE over public internet | Private, dedicated connection via partner |
| **Bandwidth** | Up to 10 Gbps (VpnGw5) | Up to 100 Gbps |
| **Latency** | Variable (internet-dependent) | Predictable, low latency |
| **Encryption** | Built-in IPSec | Not encrypted by default (add MACsec or VPN) |
| **Cost** | Lower (~$140-1,250/month for gateway) | Higher ($200-10,000+/month for circuit) |
| **Setup time** | Minutes to hours | Weeks (requires provider provisioning) |
| **SLA** | 99.9% (single) / 99.95% (active-active) | 99.95% (standard) / 99.99% (premium) |
| **Best for** | Dev/test, small offices, quick setup | Production, compliance, high-throughput |

```bash
# Create a VPN Gateway (takes 30-45 minutes to provision)
az network vnet-gateway create \
  --resource-group myRG \
  --name hub-vpn-gateway \
  --vnet hub-vnet \
  --gateway-type Vpn \
  --vpn-type RouteBased \
  --sku VpnGw2 \
  --generation Generation2 \
  --public-ip-addresses vpn-gw-pip \
  --no-wait

# Check provisioning status
az network vnet-gateway show -g myRG -n hub-vpn-gateway --query provisioningState -o tsv
```

**War Story**: A retail company chose VPN Gateway for their production Azure connectivity to save money. During Black Friday, the IPSec tunnel became saturated at 1.2 Gbps, causing database replication lag between on-premises and Azure that led to inventory discrepancies. Customers were buying items that were already out of stock. The company switched to ExpressRoute within three weeks, but the damage to customer trust during the holiday season was already done. The lesson: for production workloads with significant data transfer, the cost of ExpressRoute is almost always justified.

---

## The Hub-and-Spoke Topology: Enterprise Standard

The hub-and-spoke architecture is the most common network topology for enterprise Azure deployments. It centralizes shared services (firewall, VPN gateway, DNS, monitoring) in a hub VNet and connects workload VNets (spokes) via peering.

```text
    ┌──────────────────────────────────────────────────────────────────┐
    │                        Hub VNet (10.0.0.0/16)                    │
    │                                                                  │
    │   ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
    │   │ Azure       │  │ VPN Gateway  │  │ Azure Bastion        │   │
    │   │ Firewall    │  │ or Express-  │  │ (secure remote       │   │
    │   │ 10.0.3.0/26 │  │ Route GW     │  │  access)             │   │
    │   │             │  │ 10.0.255.0/27│  │ 10.0.4.0/26          │   │
    │   └──────┬──────┘  └──────┬───────┘  └──────────────────────┘   │
    │          │                │                                      │
    │          │    ┌───────────┘                                      │
    │          │    │    ┌────────────────┐                            │
    │          │    │    │ DNS Resolver   │                            │
    │          │    │    │ 10.0.5.0/24   │                            │
    │          │    │    └────────────────┘                            │
    └──────────┼────┼─────────────────────────────────────────────────┘
               │    │
     ┌─────────┴────┴─────────────────────────────────────────────┐
     │                    VNet Peering                             │
     ├──────────────────────────┬──────────────────────────────────┤
     │                          │                                  │
     ▼                          ▼                                  │
    ┌────────────────────┐   ┌────────────────────┐               │
    │ Spoke 1: App       │   │ Spoke 2: Data      │               │
    │ (10.1.0.0/16)      │   │ (10.2.0.0/16)      │               │
    │                    │   │                    │               │
    │ ┌────────────────┐ │   │ ┌────────────────┐ │               │
    │ │ App Subnet     │ │   │ │ DB Subnet      │ │               │
    │ │ 10.1.1.0/24    │ │   │ │ 10.2.1.0/24    │ │               │
    │ │ UDR → Firewall │ │   │ │ UDR → Firewall │ │               │
    │ └────────────────┘ │   │ └────────────────┘ │               │
    └────────────────────┘   └────────────────────┘               │
                                                                   │
                              On-Premises Network ◄────────────────┘
                              (via VPN / ExpressRoute)
```

Benefits of hub-and-spoke:
1. **Cost savings**: Shared services (firewall, gateway) are deployed once in the hub
2. **Security**: All spoke egress flows through the central firewall for inspection
3. **Separation of concerns**: Each team gets their own spoke VNet with their own RBAC
4. **Scalability**: Add new spokes without modifying existing infrastructure
5. **Compliance**: Centralized logging and traffic inspection

---

## Did You Know?

1. **Azure VNet peering traffic between regions is not free.** Intra-region peering (same region) has no data transfer charges, but global VNet peering (cross-region) costs $0.01-$0.035 per GB depending on the regions involved. A company running 50 TB of cross-region replication per month learned this the hard way when they received a $1,750 networking bill they had not budgeted for.

2. **Azure reserves exactly 5 IP addresses in every subnet**, regardless of size. In a /28 subnet (16 addresses), you lose 5 to Azure, leaving only 11 usable. The reserved addresses are: the network address (.0), Azure's default gateway (.1), Azure DNS mapping (.2 and .3), and the broadcast address (last address). This is more than AWS reserves (which takes only the first 4 and the last 1).

3. **NSG flow logs can generate enormous amounts of data.** A moderately busy VNet with 50 VMs can produce over 200 GB of NSG flow logs per month. At Log Analytics ingestion rates of roughly $2.76 per GB, that is $552/month just for network flow logging. Many teams enable flow logs during an investigation and forget to turn them off, leading to surprise bills months later.

4. **Azure Firewall's minimum cost is approximately $912 per month** (Standard SKU) even with zero traffic, because you pay for the deployment hours. Premium SKU starts at roughly $1,278 per month. For dev/test environments, many teams use NSGs alone or deploy a Linux VM running iptables as a lightweight alternative, saving thousands per month at the cost of operational complexity.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Overlapping address spaces between VNets that need to peer | Poor IP address planning, especially when multiple teams create VNets independently | Create a centralized IP Address Management (IPAM) spreadsheet or use Azure IPAM. Plan your entire address scheme before creating any VNets. |
| Not enabling "Allow Forwarded Traffic" on peering | The default is disabled, and the peering "works" for direct traffic, so it seems fine | For hub-and-spoke with transit routing, both sides of the peering need `--allow-forwarded-traffic`. The hub also needs `--allow-gateway-transit`. |
| Putting the Azure Firewall in a subnet not named "AzureFirewallSubnet" | The requirement is not obvious until deployment fails | Azure Firewall requires the subnet to be named exactly `AzureFirewallSubnet` with a minimum size of /26. This is a hard-coded requirement. |
| Creating subnets that are too small for the workload | Developers estimate VM count but forget about internal load balancers, private endpoints, and future growth | Size subnets at least 2x your current need. For AKS, remember each pod gets an IP (Azure CNI), so a 50-node cluster with 30 pods per node needs 1,500+ IPs. |
| Not associating NSGs with subnets (relying only on NIC-level NSGs) | NIC-level NSGs seem more granular and therefore "better" | Subnet-level NSGs provide a consistent security baseline. Use ASGs for per-VM differentiation within a subnet. NIC-level NSGs should be the exception, not the rule. |
| Forgetting to create the return peering (only creating one direction) | VNet peering requires a link in both directions, but Azure does not warn you until traffic fails | Always create peering in pairs. Script it so both sides are created in the same deployment. |
| Using the default `AllowInternetOutBound` without a firewall in production | The default NSG rule allows all outbound internet traffic | In production, create a route table with `0.0.0.0/0` pointing to a firewall/NVA. This overrides the default outbound route through Azure's internet gateway. |
| Not planning for DNS resolution across peered VNets | VMs in peered VNets cannot resolve each other's private DNS names by default | Deploy Azure Private DNS Zones linked to all VNets, or use a centralized DNS resolver in the hub VNet. |

---

## Quiz

<details>
<summary>1. A VNet has the address space 10.0.0.0/16. You create a subnet with the prefix 10.0.1.0/24. How many usable IP addresses does this subnet have?</summary>

251 usable IP addresses. A /24 subnet has 256 total addresses, but Azure reserves 5: the network address (10.0.1.0), Azure's internal default gateway (10.0.1.1), Azure DNS IP space (10.0.1.2 and 10.0.1.3), and the broadcast address (10.0.1.255). This leaves 256 - 5 = 251 addresses available for your resources.
</details>

<details>
<summary>2. VNet A is peered with VNet B, and VNet B is peered with VNet C. Can a VM in VNet A communicate with a VM in VNet C? Why or why not?</summary>

No, not by default. VNet peering is non-transitive. Even though A is connected to B and B is connected to C, traffic from A does not automatically flow through B to reach C. To enable this, you need to deploy a network virtual appliance (NVA) or Azure Firewall in VNet B, create User-Defined Routes in VNet A and VNet C that route traffic through the NVA, and enable "Allow Forwarded Traffic" on all peering connections. This is exactly what the hub-and-spoke topology achieves.
</details>

<details>
<summary>3. What is the difference between an NSG and Azure Firewall? When would you use each?</summary>

NSGs operate at Layer 3/4 (IP addresses and ports) and are free. They are applied at the subnet or NIC level and filter traffic based on source/destination IP, port, and protocol. Azure Firewall operates at Layers 3-7, supports FQDN filtering, URL filtering, TLS inspection (Premium), and threat intelligence. It costs roughly $912+/month. Use NSGs for basic subnet-level traffic filtering in all environments. Use Azure Firewall when you need centralized egress control, FQDN-based rules, compliance logging, or advanced threat detection. Most production environments use both: NSGs on subnets for defense-in-depth and Azure Firewall in the hub for centralized inspection.
</details>

<details>
<summary>4. Why must the Azure Firewall subnet be named exactly "AzureFirewallSubnet"?</summary>

This is a hard-coded requirement in the Azure resource provider for Azure Firewall. When you deploy Azure Firewall, the resource provider looks for a subnet with this exact name in the specified VNet. If it does not find it, the deployment fails. This pattern is used for several Azure services (GatewaySubnet, AzureBastionSubnet, RouteServerSubnet) to ensure that the service gets a dedicated subnet with appropriate sizing and that no other resources are accidentally placed in the service's subnet.
</details>

<details>
<summary>5. You deploy a hub-and-spoke topology. Spoke VMs can reach the internet but cannot reach VMs in other spokes. What is likely missing?</summary>

The most likely issue is the Azure Firewall (or NVA) in the hub does not have a network rule allowing spoke-to-spoke traffic. The UDR on the spoke subnets routes all traffic (0.0.0.0/0) to the firewall, and the firewall is forwarding internet traffic but does not have a rule to allow traffic between the spoke address ranges (e.g., 10.1.0.0/16 to 10.2.0.0/16). Add a network rule on the firewall that allows the spoke address spaces to communicate with each other. Also verify that "Allow Forwarded Traffic" is enabled on all peering connections.
</details>

<details>
<summary>6. What is the purpose of Application Security Groups (ASGs), and how do they improve on traditional NSG rules?</summary>

ASGs let you group VMs by function (e.g., "web-servers", "db-servers") and write NSG rules using those groups instead of explicit IP addresses. This is a major improvement because VM IP addresses change frequently (especially in auto-scaling scenarios), and maintaining IP-based rules is error-prone and labor-intensive. With ASGs, you associate a VM's NIC with an ASG, and the NSG rules automatically apply. When a new VM joins the ASG, it immediately gets the correct network access without any rule changes. This reduces rule count, eliminates manual IP management, and makes NSG rules self-documenting.
</details>

<details>
<summary>7. When should you choose ExpressRoute over VPN Gateway for hybrid connectivity?</summary>

Choose ExpressRoute when you need predictable latency (internet-based VPN latency varies), high bandwidth (over 1-2 Gbps consistently), compliance requirements for private connectivity (some regulations mandate that data must not traverse the public internet), or when your workloads are latency-sensitive (like database replication or real-time analytics). Choose VPN Gateway when you need quick setup (minutes vs weeks), cost is a primary concern, bandwidth needs are under 1 Gbps, or for dev/test environments. Many enterprises use both: ExpressRoute as the primary connection and VPN Gateway as a backup failover path.
</details>

---

## Hands-On Exercise: Hub-and-Spoke with VNet Peering and Spoke Egress via Hub

In this exercise, you will build a hub-and-spoke network topology with two spokes, configure VNet peering, and set up route tables so all spoke egress traffic flows through the hub.

**Prerequisites**: Azure CLI installed and authenticated, sufficient quota for VMs and public IPs.

### Task 1: Create the Hub VNet with Subnets

```bash
RG="kubedojo-network-lab"
LOCATION="eastus2"

# Create resource group
az group create --name "$RG" --location "$LOCATION"

# Create hub VNet
az network vnet create \
  --resource-group "$RG" \
  --name hub-vnet \
  --address-prefix 10.0.0.0/16 \
  --location "$LOCATION"

# Create hub subnets
az network vnet subnet create -g "$RG" --vnet-name hub-vnet \
  --name shared-services --address-prefix 10.0.1.0/24

az network vnet subnet create -g "$RG" --vnet-name hub-vnet \
  --name AzureFirewallSubnet --address-prefix 10.0.3.0/26
```

<details>
<summary>Verify Task 1</summary>

```bash
az network vnet show -g "$RG" -n hub-vnet \
  --query '{AddressSpace:addressSpace.addressPrefixes, Subnets:subnets[].{Name:name, Prefix:addressPrefix}}' -o json
```

You should see the hub VNet with two subnets.
</details>

### Task 2: Create Two Spoke VNets

```bash
# Spoke 1: Application workloads
az network vnet create -g "$RG" -n spoke1-vnet \
  --address-prefix 10.1.0.0/16 --location "$LOCATION"
az network vnet subnet create -g "$RG" --vnet-name spoke1-vnet \
  --name workload --address-prefix 10.1.1.0/24

# Spoke 2: Data workloads
az network vnet create -g "$RG" -n spoke2-vnet \
  --address-prefix 10.2.0.0/16 --location "$LOCATION"
az network vnet subnet create -g "$RG" --vnet-name spoke2-vnet \
  --name workload --address-prefix 10.2.1.0/24
```

<details>
<summary>Verify Task 2</summary>

```bash
az network vnet list -g "$RG" --query '[].{Name:name, AddressSpace:addressSpace.addressPrefixes[0]}' -o table
```

You should see three VNets: hub-vnet (10.0.0.0/16), spoke1-vnet (10.1.0.0/16), spoke2-vnet (10.2.0.0/16).
</details>

### Task 3: Create VNet Peering (Hub to Both Spokes)

```bash
# Get VNet resource IDs
HUB_ID=$(az network vnet show -g "$RG" -n hub-vnet --query id -o tsv)
SPOKE1_ID=$(az network vnet show -g "$RG" -n spoke1-vnet --query id -o tsv)
SPOKE2_ID=$(az network vnet show -g "$RG" -n spoke2-vnet --query id -o tsv)

# Hub ↔ Spoke1 peering
az network vnet peering create -g "$RG" --vnet-name hub-vnet \
  --name hub-to-spoke1 --remote-vnet "$SPOKE1_ID" \
  --allow-vnet-access --allow-forwarded-traffic

az network vnet peering create -g "$RG" --vnet-name spoke1-vnet \
  --name spoke1-to-hub --remote-vnet "$HUB_ID" \
  --allow-vnet-access --allow-forwarded-traffic

# Hub ↔ Spoke2 peering
az network vnet peering create -g "$RG" --vnet-name hub-vnet \
  --name hub-to-spoke2 --remote-vnet "$SPOKE2_ID" \
  --allow-vnet-access --allow-forwarded-traffic

az network vnet peering create -g "$RG" --vnet-name spoke2-vnet \
  --name spoke2-to-hub --remote-vnet "$HUB_ID" \
  --allow-vnet-access --allow-forwarded-traffic
```

<details>
<summary>Verify Task 3</summary>

```bash
az network vnet peering list -g "$RG" --vnet-name hub-vnet \
  --query '[].{Name:name, PeeringState:peeringState, AllowForwarded:allowForwardedTraffic}' -o table
```

Both peerings should show `Connected` state with `AllowForwarded: True`.
</details>

### Task 4: Deploy a Simulated NVA in the Hub

For this exercise, we will use a Linux VM with IP forwarding enabled as a simulated network virtual appliance, instead of a full Azure Firewall (which takes 15+ minutes to deploy and costs money).

```bash
# Create NVA VM in hub shared-services subnet
az vm create \
  --resource-group "$RG" \
  --name hub-nva \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --vnet-name hub-vnet \
  --subnet shared-services \
  --private-ip-address 10.0.1.4 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-address hub-nva-pip

# Enable IP forwarding on the NIC (required for routing)
NVA_NIC=$(az vm show -g "$RG" -n hub-nva --query 'networkProfile.networkInterfaces[0].id' -o tsv)
az network nic update --ids "$NVA_NIC" --ip-forwarding true

# Enable IP forwarding inside the VM
az vm run-command invoke -g "$RG" -n hub-nva \
  --command-id RunShellScript \
  --scripts "sudo sysctl -w net.ipv4.ip_forward=1 && echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf && sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE"
```

<details>
<summary>Verify Task 4</summary>

```bash
az network nic show --ids "$NVA_NIC" --query '{IPForwarding:enableIPForwarding, PrivateIP:ipConfigurations[0].privateIPAddress}' -o table
```

IP forwarding should be `True` and the private IP should be `10.0.1.4`.
</details>

### Task 5: Create Route Tables for Spoke Egress via Hub

```bash
# Create route table
az network route-table create -g "$RG" -n spoke-udr \
  --disable-bgp-route-propagation true

# Default route: all traffic goes to the NVA
az network route-table route create -g "$RG" \
  --route-table-name spoke-udr \
  --name default-to-hub \
  --address-prefix 0.0.0.0/0 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.1.4

# Spoke1-to-Spoke2 route via NVA
az network route-table route create -g "$RG" \
  --route-table-name spoke-udr \
  --name spoke1-to-spoke2 \
  --address-prefix 10.2.0.0/16 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.1.4

# Spoke2-to-Spoke1 route via NVA
az network route-table route create -g "$RG" \
  --route-table-name spoke-udr \
  --name spoke2-to-spoke1 \
  --address-prefix 10.1.0.0/16 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.1.4

# Associate route table with both spoke subnets
az network vnet subnet update -g "$RG" --vnet-name spoke1-vnet \
  --name workload --route-table spoke-udr

az network vnet subnet update -g "$RG" --vnet-name spoke2-vnet \
  --name workload --route-table spoke-udr
```

<details>
<summary>Verify Task 5</summary>

```bash
az network route-table route list -g "$RG" --route-table-name spoke-udr -o table
```

You should see three routes, all with next-hop type `VirtualAppliance` and next-hop IP `10.0.1.4`.
</details>

### Task 6: Deploy Test VMs and Verify Connectivity

```bash
# Create a VM in each spoke
az vm create -g "$RG" -n spoke1-vm --image Ubuntu2204 --size Standard_B1s \
  --vnet-name spoke1-vnet --subnet workload --admin-username azureuser \
  --generate-ssh-keys --public-ip-address spoke1-vm-pip --no-wait

az vm create -g "$RG" -n spoke2-vm --image Ubuntu2204 --size Standard_B1s \
  --vnet-name spoke2-vnet --subnet workload --admin-username azureuser \
  --generate-ssh-keys --public-ip-address spoke2-vm-pip --no-wait

# Wait for VMs to be created
az vm wait -g "$RG" -n spoke1-vm --created
az vm wait -g "$RG" -n spoke2-vm --created

# Get spoke2 VM private IP
SPOKE2_PRIVATE_IP=$(az vm show -g "$RG" -n spoke2-vm -d --query privateIps -o tsv)

# Test connectivity from spoke1 to spoke2 (through the hub NVA)
az vm run-command invoke -g "$RG" -n spoke1-vm \
  --command-id RunShellScript \
  --scripts "ping -c 3 $SPOKE2_PRIVATE_IP && echo 'SUCCESS: Spoke-to-spoke via hub' || echo 'FAIL: No connectivity'"

# Verify traffic goes through the NVA by checking traceroute
az vm run-command invoke -g "$RG" -n spoke1-vm \
  --command-id RunShellScript \
  --scripts "traceroute -n -m 5 $SPOKE2_PRIVATE_IP"
```

<details>
<summary>Verify Task 6</summary>

The ping should succeed, and the traceroute should show a hop through `10.0.1.4` (the hub NVA) before reaching the spoke2 VM. This confirms that spoke-to-spoke traffic is flowing through the hub as designed.
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
```

### Success Criteria

- [ ] Hub VNet created with shared-services and AzureFirewallSubnet
- [ ] Two spoke VNets created with non-overlapping address spaces
- [ ] VNet peering established bidirectionally between hub and both spokes
- [ ] NVA VM deployed in hub with IP forwarding enabled
- [ ] Route table created directing spoke traffic through hub NVA
- [ ] Spoke-to-spoke connectivity verified (traffic flows through hub)

---

## Next Module

[Module 3.3: VMs & VM Scale Sets](module-3.3-vms/) --- Learn how to deploy and manage virtual machines in Azure, from choosing the right VM size to building highly available workloads with VM Scale Sets and Availability Zones.
