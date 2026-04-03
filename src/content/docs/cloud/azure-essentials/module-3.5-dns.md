---
title: "Module 3.5: Azure DNS & Traffic Manager"
slug: cloud/azure-essentials/module-3.5-dns
sidebar:
  order: 6
---
**Complexity**: [MEDIUM] | **Time to Complete**: 1.5h | **Prerequisites**: Module 3.2 (Virtual Networks)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Azure DNS zones with record sets for public-facing and private VNet-linked name resolution**
- **Implement Traffic Manager profiles with priority, weighted, and performance routing for multi-region failover**
- **Deploy Azure Private DNS zones for VNet-internal service discovery across peered virtual networks**
- **Design DNS architectures combining Azure DNS, Traffic Manager, and Front Door for global traffic distribution**

---

## Why This Module Matters

In October 2021, a global logistics company migrated their customer-facing portal from on-premises to Azure. They deployed the application across East US and West Europe regions for redundancy. On launch day, everything worked---until the East US deployment experienced a database connection pool exhaustion at peak hours. Instead of seamlessly routing users to the healthy West Europe deployment, all users saw errors. The problem was simple: they had configured Azure DNS with A records pointing directly to the East US public IP. There was no traffic routing layer to detect the failure and redirect traffic. Adding Azure Traffic Manager with health probes took 15 minutes to configure, but the 3-hour outage had already cost them their biggest customer---a shipping company that processed 40,000 packages per day through the portal. That single customer represented $2.4 million in annual revenue.

DNS is the invisible infrastructure that underpins every internet interaction. When it works, nobody thinks about it. When it fails, nothing works. In Azure, DNS is not just about resolving names to IP addresses---it is a critical component of high availability, traffic routing, and hybrid cloud architecture. Azure DNS handles public-facing domain resolution, Private DNS Zones handle name resolution within your virtual networks, and Traffic Manager uses DNS-based routing to distribute traffic across regions and endpoints.

In this module, you will learn how Azure DNS zones work for both public and private scenarios, how Traffic Manager routes traffic using different algorithms, and how Azure Front Door provides a modern alternative with layer-7 capabilities. By the end, you will understand how to design a DNS architecture that keeps your applications reachable even when entire regions fail.

---

## Azure DNS: Public Zones

Azure DNS allows you to host your DNS zones on Azure's global anycast network of name servers. When you host your zone in Azure DNS, your DNS records are served from Microsoft's worldwide network of DNS servers, providing low latency and high availability.

### How DNS Zones Work

A DNS zone is a container for all the DNS records for a specific domain. When you create a zone for `example.com` in Azure DNS, Azure assigns four name servers (in the format `ns1-XX.azure-dns.com`, `ns2-XX.azure-dns.net`, `ns3-XX.azure-dns.org`, `ns4-XX.azure-dns.info`).

```bash
# Create a DNS zone
az network dns zone create \
  --resource-group myRG \
  --name example.com

# View the assigned name servers
az network dns zone show \
  --resource-group myRG \
  --name example.com \
  --query nameServers -o tsv
```

After creating the zone, you must update your domain registrar's NS records to point to the Azure name servers. Until you do this, DNS queries for your domain will not reach Azure.

### Common Record Types

```bash
# A record: Maps a name to an IPv4 address
az network dns record-set a add-record \
  --resource-group myRG \
  --zone-name example.com \
  --record-set-name www \
  --ipv4-address 20.50.100.150

# AAAA record: Maps a name to an IPv6 address
az network dns record-set aaaa add-record \
  --resource-group myRG \
  --zone-name example.com \
  --record-set-name www \
  --ipv6-address 2603:1030:800:5::1

# CNAME record: Maps a name to another name (alias)
az network dns record-set cname set-record \
  --resource-group myRG \
  --zone-name example.com \
  --record-set-name blog \
  --cname blog.wordpress.com

# MX record: Mail exchange
az network dns record-set mx add-record \
  --resource-group myRG \
  --zone-name example.com \
  --record-set-name "@" \
  --exchange mail.example.com \
  --preference 10

# TXT record: Arbitrary text (SPF, DKIM, verification)
az network dns record-set txt add-record \
  --resource-group myRG \
  --zone-name example.com \
  --record-set-name "@" \
  --value "v=spf1 include:spf.protection.outlook.com -all"

# List all records in a zone
az network dns record-set list \
  --resource-group myRG \
  --zone-name example.com -o table
```

### Alias Records

Azure DNS supports **alias records**, which point directly to an Azure resource (like a Load Balancer, Traffic Manager profile, or CDN endpoint) instead of an IP address. The key advantage: when the resource's IP changes, the DNS record updates automatically.

```bash
# Create an alias record pointing to a Load Balancer public IP
LB_PIP_ID=$(az network public-ip show -g myRG -n web-lb-pip --query id -o tsv)

az network dns record-set a create \
  --resource-group myRG \
  --zone-name example.com \
  --name app \
  --target-resource "$LB_PIP_ID"
```

```text
    Traditional A Record vs Alias Record:

    Traditional:
    app.example.com → A → 20.50.100.150 (static IP)
    Problem: If the LB IP changes, DNS is stale until you update it.

    Alias Record:
    app.example.com → Alias → /subscriptions/.../publicIPAddresses/web-lb-pip
    Advantage: Azure DNS automatically resolves to the current IP.
              Also supports zone apex (example.com, not just www.example.com).
```

---

## Azure Private DNS Zones

Private DNS Zones provide name resolution within your Virtual Networks without exposing records to the public internet. This is essential for internal service discovery---your web servers need to find your database by name (`db.internal.example.com`), not by memorizing IP addresses that change when you redeploy.

### How Private DNS Zones Work

```text
    ┌─────────────────────────────────────────────────────────────┐
    │                  Private DNS Zone:                           │
    │              internal.example.com                            │
    │                                                             │
    │  Records:                                                   │
    │    db.internal.example.com     → 10.0.2.10                  │
    │    cache.internal.example.com  → 10.0.2.20                  │
    │    api.internal.example.com    → 10.0.1.15                  │
    │                                                             │
    │  Linked VNets:                                              │
    │    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
    │    │  hub-vnet     │  │  spoke1-vnet  │  │  spoke2-vnet  │    │
    │    │  (auto-reg)   │  │  (resolve)    │  │  (resolve)    │    │
    │    └──────────────┘  └──────────────┘  └──────────────┘    │
    │                                                             │
    │  auto-reg = VMs auto-register their DNS names               │
    │  resolve  = VMs can resolve names but do not auto-register  │
    └─────────────────────────────────────────────────────────────┘
```

```bash
# Create a private DNS zone
az network private-dns zone create \
  --resource-group myRG \
  --name internal.example.com

# Link the private DNS zone to a VNet (with auto-registration)
az network private-dns link vnet create \
  --resource-group myRG \
  --zone-name internal.example.com \
  --name hub-link \
  --virtual-network hub-vnet \
  --registration-enabled true    # VMs in this VNet auto-register

# Link to spoke VNets (resolution only, no auto-registration)
az network private-dns link vnet create \
  --resource-group myRG \
  --zone-name internal.example.com \
  --name spoke1-link \
  --virtual-network spoke1-vnet \
  --registration-enabled false

# Manually add a record
az network private-dns record-set a add-record \
  --resource-group myRG \
  --zone-name internal.example.com \
  --record-set-name db \
  --ipv4-address 10.0.2.10

# List records in the private zone
az network private-dns record-set list \
  --resource-group myRG \
  --zone-name internal.example.com -o table
```

**Auto-registration** is a powerful feature: when enabled on a VNet link, every VM created in that VNet automatically gets a DNS record in the private zone. When the VM is deleted, the record is automatically removed. This eliminates the need to manually manage internal DNS records.

### Private DNS and Private Endpoints

Private Endpoints are a mechanism to access Azure PaaS services (Storage, SQL, Key Vault, etc.) over a private IP address in your VNet instead of over the public internet. When you create a private endpoint, you need a Private DNS Zone to resolve the service's FQDN to the private IP.

```bash
# Example: Private endpoint for a storage account
# Step 1: Create the private endpoint
az network private-endpoint create \
  --resource-group myRG \
  --name storage-pe \
  --vnet-name hub-vnet \
  --subnet private-endpoints \
  --private-connection-resource-id "$STORAGE_ACCOUNT_ID" \
  --group-id blob \
  --connection-name storage-connection

# Step 2: Create the private DNS zone for blob storage
az network private-dns zone create \
  --resource-group myRG \
  --name privatelink.blob.core.windows.net

# Step 3: Link the DNS zone to your VNet
az network private-dns link vnet create \
  --resource-group myRG \
  --zone-name privatelink.blob.core.windows.net \
  --name hub-dns-link \
  --virtual-network hub-vnet \
  --registration-enabled false

# Step 4: Create DNS zone group (auto-manages DNS records)
az network private-endpoint dns-zone-group create \
  --resource-group myRG \
  --endpoint-name storage-pe \
  --name default \
  --private-dns-zone "privatelink.blob.core.windows.net" \
  --zone-name blob
```

After this setup, when a VM in hub-vnet resolves `yourstorage.blob.core.windows.net`, the response is the private IP of the private endpoint (e.g., 10.0.5.4) instead of the public IP. Traffic stays entirely within Azure's backbone.

---

## Azure Traffic Manager: DNS-Based Global Load Balancing

Traffic Manager is a DNS-based traffic routing service that distributes traffic across global endpoints. It works at the DNS layer (Layer 7 of DNS, technically)---when a client resolves your domain, Traffic Manager returns the IP of the most appropriate endpoint based on the routing method you configure.

### How Traffic Manager Works

```text
    ┌──────────┐
    │  Client  │
    └────┬─────┘
         │ 1. DNS query: app.trafficmanager.net
         ▼
    ┌──────────────────┐
    │  Traffic Manager │  2. Evaluates:
    │                  │     - Health probes
    │                  │     - Routing method
    │                  │     - Endpoint priority
    └────────┬─────────┘
             │ 3. Returns IP of best endpoint
             │    (DNS CNAME → endpoint IP)
             ▼
    ┌────────────────┐  ┌────────────────┐
    │  East US       │  │  West Europe   │
    │  20.50.100.1   │  │  20.73.200.1   │
    │  (healthy)     │  │  (healthy)     │
    └────────────────┘  └────────────────┘
         │
         │ 4. Client connects directly to endpoint
         │    (Traffic Manager is NOT in data path)
         ▼
    Traffic Manager only handles DNS resolution.
    Actual HTTP/TCP traffic goes directly
    from client to endpoint.
```

**Critical insight**: Traffic Manager is **not** a proxy or a load balancer. It only participates in the DNS resolution step. After that, the client connects directly to the endpoint. This means Traffic Manager cannot see HTTP headers, cannot terminate SSL, and cannot cache content. For those features, you need Azure Front Door.

### Routing Methods

| Method | How It Routes | Best For |
| :--- | :--- | :--- |
| **Priority** | Always sends to highest-priority healthy endpoint | Active/passive failover |
| **Weighted** | Distributes traffic by weight (e.g., 80/20) | Canary deployments, A/B testing |
| **Performance** | Routes to the closest endpoint (by latency) | Global apps needing low latency |
| **Geographic** | Routes based on the client's geographic location | Data sovereignty, regional compliance |
| **MultiValue** | Returns multiple healthy IPs (client chooses) | Increase availability with client-side retry |
| **Subnet** | Routes based on client's source IP range | VIP customers, partner-specific endpoints |

```bash
# Create a Traffic Manager profile with Priority routing
az network traffic-manager profile create \
  --resource-group myRG \
  --name app-tm-profile \
  --routing-method Priority \
  --unique-dns-name app-kubedojo \
  --ttl 30 \
  --protocol HTTPS \
  --port 443 \
  --path "/health" \
  --interval 10 \
  --timeout 5 \
  --max-failures 3

# Add primary endpoint (East US)
az network traffic-manager endpoint create \
  --resource-group myRG \
  --profile-name app-tm-profile \
  --name eastus-endpoint \
  --type azureEndpoints \
  --target-resource-id "$EASTUS_PIP_ID" \
  --priority 1 \
  --endpoint-status Enabled

# Add secondary endpoint (West Europe)
az network traffic-manager endpoint create \
  --resource-group myRG \
  --profile-name app-tm-profile \
  --name westeurope-endpoint \
  --type azureEndpoints \
  --target-resource-id "$WESTEUROPE_PIP_ID" \
  --priority 2 \
  --endpoint-status Enabled

# Check endpoint health status
az network traffic-manager endpoint list \
  --resource-group myRG \
  --profile-name app-tm-profile \
  --type azureEndpoints \
  --query '[].{Name:name, Status:endpointStatus, Monitor:endpointMonitorStatus, Priority:priority}' -o table

# Test DNS resolution
nslookup app-kubedojo.trafficmanager.net
```

### Traffic Manager with Weighted Routing (Canary Deployments)

```bash
# Create a profile for canary deployment
az network traffic-manager profile create \
  --resource-group myRG \
  --name canary-tm-profile \
  --routing-method Weighted \
  --unique-dns-name canary-kubedojo \
  --ttl 10 \
  --protocol HTTPS \
  --port 443 \
  --path "/health"

# Stable version gets 90% of traffic
az network traffic-manager endpoint create \
  --resource-group myRG \
  --profile-name canary-tm-profile \
  --name stable \
  --type externalEndpoints \
  --target stable.example.com \
  --weight 90

# Canary version gets 10% of traffic
az network traffic-manager endpoint create \
  --resource-group myRG \
  --profile-name canary-tm-profile \
  --name canary \
  --type externalEndpoints \
  --target canary.example.com \
  --weight 10
```

**War Story**: A retail company used Traffic Manager with Performance routing for their global storefront. During a product launch, their East US deployment became overloaded. Traffic Manager's health probes detected the degradation and automatically started routing new DNS queries to West Europe. The failover happened transparently---customers experienced a brief increase in latency (transatlantic vs same-region) but zero downtime. The engineering team had 45 minutes of breathing room to scale up East US before most users even noticed the region switch.

---

## Azure Front Door: The Modern Alternative

Azure Front Door is a global, scalable entry point for web applications. Unlike Traffic Manager (DNS only), Front Door operates at Layer 7 (HTTP/HTTPS) and sits in the data path. It acts as a reverse proxy, providing SSL termination, caching, WAF, and intelligent routing.

```text
    Traffic Manager vs Front Door:

    Traffic Manager:
    Client → DNS query → TM returns endpoint IP → Client connects to endpoint
    (TM is NOT in the data path)

    Front Door:
    Client → HTTPS → Front Door PoP → (cache hit? return) → Backend origin
    (Front Door IS in the data path, can inspect/modify HTTP)

    ┌──────────┐     HTTPS      ┌───────────────┐     HTTPS     ┌──────────┐
    │  Client  │ ─────────────► │  Front Door   │ ────────────► │  Origin  │
    │          │ ◄───────────── │  (PoP Edge)   │ ◄──────────── │  Server  │
    └──────────┘   Response     │               │   Response    └──────────┘
                                │ - SSL offload │
                                │ - WAF         │
                                │ - Caching     │
                                │ - Compression │
                                │ - URL rewrite │
                                └───────────────┘
```

| Feature | Traffic Manager | Azure Front Door |
| :--- | :--- | :--- |
| **Layer** | DNS (returns IP) | HTTP/HTTPS (reverse proxy) |
| **In data path** | No | Yes |
| **SSL termination** | No | Yes |
| **Caching** | No | Yes (edge caching) |
| **WAF** | No | Yes (built-in) |
| **URL path routing** | No | Yes |
| **Session affinity** | No (DNS round-robin) | Yes (cookie-based) |
| **Health probes** | TCP, HTTP, HTTPS | HTTP, HTTPS (with custom headers) |
| **Protocol support** | Any (TCP/UDP/HTTP) | HTTP/HTTPS only |
| **Cost** | ~$0.36/million queries | ~$35/month + per-request |
| **Failover speed** | DNS TTL dependent (30-300s) | Near-instant (<30s) |

```bash
# Create an Azure Front Door profile (Standard tier)
az afd profile create \
  --resource-group myRG \
  --profile-name app-frontdoor \
  --sku Standard_AzureFrontDoor

# Add an endpoint
az afd endpoint create \
  --resource-group myRG \
  --profile-name app-frontdoor \
  --endpoint-name app-endpoint \
  --enabled-state Enabled

# Add an origin group (backend pool)
az afd origin-group create \
  --resource-group myRG \
  --profile-name app-frontdoor \
  --origin-group-name app-origins \
  --probe-request-type GET \
  --probe-protocol Https \
  --probe-path "/health" \
  --probe-interval-in-seconds 10 \
  --sample-size 4 \
  --successful-samples-required 3

# Add origins (backends)
az afd origin create \
  --resource-group myRG \
  --profile-name app-frontdoor \
  --origin-group-name app-origins \
  --origin-name eastus-origin \
  --host-name eastus-app.azurewebsites.net \
  --origin-host-header eastus-app.azurewebsites.net \
  --http-port 80 \
  --https-port 443 \
  --priority 1 \
  --weight 1000

# Add a route
az afd route create \
  --resource-group myRG \
  --profile-name app-frontdoor \
  --endpoint-name app-endpoint \
  --route-name default-route \
  --origin-group app-origins \
  --supported-protocols Https \
  --patterns-to-match "/*" \
  --forwarding-protocol HttpsOnly
```

### When to Choose Which

Use **Traffic Manager** when:
- You need non-HTTP routing (TCP, UDP services)
- You want the simplest, cheapest global routing
- Your endpoints handle SSL themselves
- You need Geographic routing for compliance

Use **Azure Front Door** when:
- You need SSL termination at the edge
- You want a Web Application Firewall (WAF)
- You need edge caching for static content
- You want sub-second failover (not DNS-TTL dependent)
- You need URL-based routing (e.g., `/api/*` to one backend, `/static/*` to another)

---

## Did You Know?

1. **Azure DNS hosts over 100 million DNS zones** as of 2024, making it one of the largest authoritative DNS providers in the world. Azure DNS uses anycast networking, meaning queries are automatically routed to the closest DNS server. The result is typical query latency under 20 milliseconds from anywhere on the planet.

2. **Traffic Manager health probes come from specific well-known IP ranges** published by Microsoft. If your backend has IP-based firewall rules, you must whitelist these IPs or your health probes will fail and Traffic Manager will mark your endpoint as degraded. The IP ranges are published in the Azure IP Ranges JSON file, under the `AzureTrafficManager` service tag.

3. **Azure Front Door has over 192 edge locations (Points of Presence)** across 109 metro areas worldwide as of 2025. When a user in Tokyo accesses your app through Front Door, the TLS handshake terminates at a Tokyo PoP. This reduces the round-trip time for the SSL negotiation from ~200ms (to a US backend) to ~5ms (to a local PoP). The PoP then maintains a persistent, optimized connection to your origin backend.

4. **Private DNS Zone auto-registration has a limit of one registration-enabled link per VNet.** A VNet can be linked to multiple Private DNS Zones for resolution, but only one zone can have auto-registration enabled. This prevents conflicts where multiple zones try to register the same VM name. If you need records in multiple zones, use one zone for auto-registration and manually create records in the others.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Forgetting to update NS records at the domain registrar after creating an Azure DNS zone | Azure creates the zone and records, but has no authority over the domain until NS records are delegated | After creating the zone, copy the four Azure NS records and update them at your domain registrar. Verify with `nslookup -type=NS example.com`. |
| Setting Traffic Manager TTL too high (300s default) | Higher TTL reduces DNS query costs | For failover scenarios, set TTL to 10-30 seconds. High TTL means clients cache stale IPs and do not fail over for minutes after an endpoint goes down. |
| Using Traffic Manager when Front Door is more appropriate | Traffic Manager is simpler and cheaper to set up | If you need SSL termination, WAF, caching, or sub-second failover, Front Door is worth the extra cost. Traffic Manager's failover speed is limited by DNS TTL. |
| Not linking Private DNS Zones to all VNets that need resolution | Only the initial VNet is linked during creation | Every VNet that needs to resolve private DNS names must be explicitly linked to the zone. Forgetting a spoke VNet means VMs in that spoke cannot resolve internal names. |
| Using CNAME records at the zone apex (e.g., example.com) | RFC 1034 prohibits CNAME at the zone apex, but teams need it for services like Front Door | Use Azure DNS alias records instead. Alias records can point to Azure resources at the zone apex without violating the RFC. |
| Not configuring health probes on Traffic Manager endpoints | Endpoints default to "Enabled" which means Traffic Manager assumes they are healthy | Always configure health probes with a meaningful path (like /health) that checks actual application readiness, not just that the server is responding. |
| Ignoring the DNS propagation delay when making changes | DNS changes appear instant in the portal | Changes propagate to the Azure DNS servers within 60 seconds, but clients and intermediate DNS resolvers may cache the old record for up to the TTL duration. Plan maintenance windows accordingly. |
| Creating separate private DNS zones per VNet instead of shared zones | Teams independently create zones with the same name | Use centralized Private DNS Zones linked to all VNets. If each team creates their own `internal.company.com` zone, records are fragmented and inconsistent. |

---

## Quiz

<details>
<summary>1. What is the difference between a standard A record and an Azure DNS alias record?</summary>

A standard A record maps a hostname to a static IP address. If the IP changes (e.g., you recreate a Load Balancer), you must manually update the record. An alias record maps a hostname to an Azure resource ID (like a public IP, Traffic Manager profile, or CDN endpoint). Azure DNS automatically resolves the alias to the resource's current IP address. If the IP changes, the DNS response updates automatically. Additionally, alias records can be used at the zone apex (e.g., `example.com`), while CNAME records cannot. Alias records also support automatic TTL inheritance from the target resource.
</details>

<details>
<summary>2. You have VMs in three VNets (hub, spoke1, spoke2). VMs in all three VNets need to resolve names in a Private DNS Zone. What must you configure?</summary>

You must create VNet links from the Private DNS Zone to all three VNets. Create one link with auto-registration enabled (typically the hub VNet, where shared services like databases are deployed) so VMs automatically get DNS records. Create two additional links with auto-registration disabled (for spoke1 and spoke2) so VMs in those VNets can resolve names in the zone but do not auto-register. Only one VNet link per zone can have auto-registration enabled, so spoke VMs that need DNS records must have them created manually or through automation.
</details>

<details>
<summary>3. Traffic Manager uses Priority routing with two endpoints: East US (priority 1) and West Europe (priority 2). The East US endpoint fails a health probe. What happens?</summary>

Traffic Manager stops returning the East US endpoint's IP in DNS responses and starts returning the West Europe endpoint's IP instead. The speed of this failover depends on two factors: the probe configuration (how quickly Traffic Manager detects the failure, based on interval, timeout, and tolerated number of failures) and the DNS TTL (how long clients cache the old DNS response). With a TTL of 30 seconds and default probe settings (30-second interval, 10-second timeout, 3 tolerated failures), failover takes approximately 90-120 seconds from the time the endpoint actually fails.
</details>

<details>
<summary>4. When should you choose Azure Front Door over Traffic Manager for global traffic routing?</summary>

Choose Front Door when you need any of these capabilities that Traffic Manager lacks: SSL/TLS termination at the edge (reducing latency for the TLS handshake), Web Application Firewall for DDoS and injection protection, edge caching for static content, URL path-based routing (sending /api to one backend and /images to another), session affinity via cookies, or near-instant failover (Front Door detects failures and reroutes within seconds, independent of DNS TTL). Choose Traffic Manager when you need non-HTTP protocol support, geographic routing for compliance, or the simplest and cheapest global routing.
</details>

<details>
<summary>5. What is the purpose of Private DNS Zone integration with Private Endpoints?</summary>

When you create a Private Endpoint for an Azure PaaS service (like Storage or SQL), the service gets a private IP address in your VNet. But the service's public FQDN (e.g., `mystorage.blob.core.windows.net`) still resolves to its public IP by default. The Private DNS Zone integration creates a record in a zone like `privatelink.blob.core.windows.net` that resolves the service's FQDN to its private IP instead. When a VM in a linked VNet queries `mystorage.blob.core.windows.net`, Azure DNS chains the resolution through the privatelink zone and returns the private IP, ensuring all traffic stays within the VNet and never traverses the public internet.
</details>

<details>
<summary>6. A team has a Traffic Manager profile with Performance routing and a TTL of 300 seconds. They notice that failover takes over 5 minutes. How can they reduce failover time?</summary>

Reduce the TTL to 10-30 seconds. With a 300-second TTL, clients cache the DNS response for up to 5 minutes. Even after Traffic Manager detects an endpoint failure and starts returning a different IP, clients continue using the cached (stale) IP until the TTL expires. Additionally, reduce the probe interval from the default 30 seconds to 10 seconds, reduce the probe timeout, and lower the tolerated number of failures from 3 to 2. Together, these changes can bring failover time from over 5 minutes down to approximately 30-60 seconds. For even faster failover, consider Azure Front Door, which is not limited by DNS TTL.
</details>

---

## Hands-On Exercise: Public DNS Zone with Traffic Manager Failover

In this exercise, you will create a public DNS zone, set up a Traffic Manager profile with Priority routing and health probes, and simulate a failover.

**Prerequisites**: Azure CLI installed and authenticated. You do not need a real domain for this exercise---we will work entirely within the `trafficmanager.net` namespace.

### Task 1: Create the Resource Group and Two Simulated Endpoints

We will use Azure Container Instances as lightweight web servers to act as our "regional endpoints."

```bash
RG="kubedojo-dns-lab"
LOCATION_PRIMARY="eastus2"
LOCATION_SECONDARY="westeurope"

az group create --name "$RG" --location "$LOCATION_PRIMARY"

# Primary endpoint: a simple web server in East US 2
az container create \
  --resource-group "$RG" \
  --name primary-web \
  --image mcr.microsoft.com/azuredocs/aci-helloworld \
  --dns-name-label "kubedojo-primary-$(openssl rand -hex 4)" \
  --location "$LOCATION_PRIMARY" \
  --ports 80

# Secondary endpoint: a simple web server in West Europe
az container create \
  --resource-group "$RG" \
  --name secondary-web \
  --image mcr.microsoft.com/azuredocs/aci-helloworld \
  --dns-name-label "kubedojo-secondary-$(openssl rand -hex 4)" \
  --location "$LOCATION_SECONDARY" \
  --ports 80

# Get their FQDNs
PRIMARY_FQDN=$(az container show -g "$RG" -n primary-web --query ipAddress.fqdn -o tsv)
SECONDARY_FQDN=$(az container show -g "$RG" -n secondary-web --query ipAddress.fqdn -o tsv)
echo "Primary: $PRIMARY_FQDN"
echo "Secondary: $SECONDARY_FQDN"
```

<details>
<summary>Verify Task 1</summary>

```bash
curl -s "http://$PRIMARY_FQDN" | head -5
curl -s "http://$SECONDARY_FQDN" | head -5
```

Both should return HTML content.
</details>

### Task 2: Create a Traffic Manager Profile

```bash
TM_DNS="kubedojo-tm-$(openssl rand -hex 4)"

az network traffic-manager profile create \
  --resource-group "$RG" \
  --name app-tm \
  --routing-method Priority \
  --unique-dns-name "$TM_DNS" \
  --ttl 10 \
  --protocol HTTP \
  --port 80 \
  --path "/" \
  --interval 10 \
  --timeout 5 \
  --max-failures 2

echo "Traffic Manager DNS: ${TM_DNS}.trafficmanager.net"
```

<details>
<summary>Verify Task 2</summary>

```bash
az network traffic-manager profile show -g "$RG" -n app-tm \
  --query '{DNS:dnsConfig.fqdn, Routing:trafficRoutingMethod, TTL:dnsConfig.ttl}' -o table
```
</details>

### Task 3: Add Endpoints to Traffic Manager

```bash
# Add primary endpoint (priority 1)
az network traffic-manager endpoint create \
  --resource-group "$RG" \
  --profile-name app-tm \
  --name primary \
  --type externalEndpoints \
  --target "$PRIMARY_FQDN" \
  --priority 1 \
  --endpoint-status Enabled

# Add secondary endpoint (priority 2)
az network traffic-manager endpoint create \
  --resource-group "$RG" \
  --profile-name app-tm \
  --name secondary \
  --type externalEndpoints \
  --target "$SECONDARY_FQDN" \
  --priority 2 \
  --endpoint-status Enabled
```

<details>
<summary>Verify Task 3</summary>

```bash
az network traffic-manager endpoint list -g "$RG" --profile-name app-tm \
  --type externalEndpoints \
  --query '[].{Name:name, Target:target, Priority:priority, MonitorStatus:endpointMonitorStatus}' -o table
```

Both endpoints should show with their respective priorities. MonitorStatus may take a minute to populate.
</details>

### Task 4: Test Normal Operation

```bash
# Resolve the Traffic Manager DNS name
nslookup "${TM_DNS}.trafficmanager.net"

# Access the app through Traffic Manager
curl -s "http://${TM_DNS}.trafficmanager.net" | head -5

# You should see the primary endpoint's response
```

<details>
<summary>Verify Task 4</summary>

The nslookup should resolve to the primary endpoint's IP address. The curl should return the primary web server's content. All traffic goes to priority 1 (primary) because both endpoints are healthy.
</details>

### Task 5: Simulate Failover

```bash
# Disable the primary endpoint (simulating a regional outage)
az network traffic-manager endpoint update \
  --resource-group "$RG" \
  --profile-name app-tm \
  --name primary \
  --type externalEndpoints \
  --endpoint-status Disabled

# Wait for the change to propagate (TTL is 10 seconds)
echo "Waiting 15 seconds for DNS propagation..."
sleep 15

# Verify Traffic Manager now routes to secondary
nslookup "${TM_DNS}.trafficmanager.net"
curl -s "http://${TM_DNS}.trafficmanager.net" | head -5

# Check endpoint status
az network traffic-manager endpoint list -g "$RG" --profile-name app-tm \
  --type externalEndpoints \
  --query '[].{Name:name, Status:endpointStatus, MonitorStatus:endpointMonitorStatus}' -o table
```

<details>
<summary>Verify Task 5</summary>

After disabling the primary endpoint, the DNS resolution should now return the secondary endpoint's IP address. The curl should return the secondary web server's content. The endpoint list should show primary as Disabled and secondary as Enabled with Online monitor status.
</details>

### Task 6: Restore and Verify

```bash
# Re-enable the primary endpoint
az network traffic-manager endpoint update \
  --resource-group "$RG" \
  --profile-name app-tm \
  --name primary \
  --type externalEndpoints \
  --endpoint-status Enabled

# Wait for propagation
sleep 15

# Verify traffic returns to primary
nslookup "${TM_DNS}.trafficmanager.net"
curl -s "http://${TM_DNS}.trafficmanager.net" | head -5
```

<details>
<summary>Verify Task 6</summary>

Traffic should return to the primary endpoint (priority 1) once it is re-enabled and health probes confirm it is healthy. This demonstrates the complete failover and failback cycle.
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
```

### Success Criteria

- [ ] Two web servers deployed in different Azure regions
- [ ] Traffic Manager profile created with Priority routing and 10-second TTL
- [ ] Both endpoints added with correct priorities
- [ ] Normal operation confirmed (traffic routes to primary)
- [ ] Failover verified (disabling primary routes traffic to secondary)
- [ ] Failback verified (re-enabling primary restores original routing)

---

## Next Module

[Module 3.6: Azure Container Registry (ACR)](../module-3.6-acr/) --- Learn how to store, manage, and secure your container images with Azure Container Registry, including authentication, ACR Tasks for automated builds, and geo-replication.
