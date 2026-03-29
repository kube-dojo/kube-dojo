---
title: "Module 2.5: GCP Cloud DNS"
slug: cloud/gcp-essentials/module-2.5-dns
sidebar:
  order: 6
---
**Complexity**: [MEDIUM] | **Time to Complete**: 1.5h | **Prerequisites**: Module 2.2 (VPC Networking)

## Why This Module Matters

In October 2021, a major social media company experienced a worldwide outage lasting over six hours. Billions of users could not access any of the company's services. The root cause was a routine BGP configuration change that accidentally withdrew the routes advertising the company's DNS nameservers. Because their DNS was unreachable, every subsequent DNS lookup for their domain failed. Even their internal tools for diagnosing and fixing the issue relied on the same DNS infrastructure, creating a devastating feedback loop. Engineers could not access internal dashboards, could not SSH into servers, and even physical access to data centers was impacted because the badge entry systems depended on the same network. The estimated revenue loss exceeded $100 million.

This incident is the most dramatic demonstration of a simple truth: **DNS is the foundation of everything on the internet.** When DNS works, nobody thinks about it. When DNS breaks, nothing works. Every HTTP request, every API call, every service-to-service communication in a microservices architecture begins with a DNS lookup. If you are running workloads on GCP, Cloud DNS is the managed service that resolves names for both your public-facing applications and your internal infrastructure.

In this module, you will learn how Cloud DNS works as a globally distributed, managed DNS service. You will understand the difference between public zones (for internet-facing domains) and private zones (for internal VPC name resolution). You will learn how DNS forwarding connects your GCP environment to on-premises DNS servers, and how peering zones allow DNS resolution across VPCs without exposing records to the broader network.

---

## DNS Fundamentals Review

Before diving into Cloud DNS, a quick refresher on how DNS resolution works is essential for understanding the configurations that follow.

```text
  User types: app.example.com
       │
       ▼
  ┌──────────────────┐
  │  Recursive        │     1. "Who knows about .com?"
  │  Resolver          │ ──────────────────────────────────>  Root DNS (.)
  │  (ISP / 8.8.8.8)  │ <──────────────────────────────────  "Ask .com TLD servers"
  │                    │
  │                    │     2. "Who knows about example.com?"
  │                    │ ──────────────────────────────────>  .com TLD servers
  │                    │ <──────────────────────────────────  "Ask ns-cloud-X.googledomains.com"
  │                    │
  │                    │     3. "What is app.example.com?"
  │                    │ ──────────────────────────────────>  Cloud DNS (authoritative)
  │                    │ <──────────────────────────────────  "34.120.55.100"
  └────────┬───────────┘
           │
           │  4. Returns 34.120.55.100
           ▼
       User connects to 34.120.55.100
```

### Record Types You Will Use

| Record Type | Purpose | Example |
| :--- | :--- | :--- |
| **A** | Maps hostname to IPv4 address | `app.example.com → 34.120.55.100` |
| **AAAA** | Maps hostname to IPv6 address | `app.example.com → 2600:1901::1` |
| **CNAME** | Alias to another hostname | `www.example.com → app.example.com` |
| **MX** | Mail server routing | `example.com → 10 mail.example.com` |
| **TXT** | Arbitrary text (SPF, DKIM, verification) | `example.com → "v=spf1 include:..."` |
| **NS** | Nameserver delegation | `example.com → ns-cloud-a1.googledomains.com` |
| **SOA** | Start of authority (zone metadata) | Serial number, refresh intervals |
| **SRV** | Service location (port + priority) | `_http._tcp.example.com → 0 5 80 app.example.com` |
| **PTR** | Reverse DNS (IP to hostname) | `100.55.120.34.in-addr.arpa → app.example.com` |

---

## Public Zones: Internet-Facing DNS

A public DNS zone in Cloud DNS makes your domain resolvable from anywhere on the internet. When you create a public zone, Google assigns it four authoritative nameservers from the `googledomains.com` pool.

### Creating a Public Zone

```bash
# Create a public managed zone
gcloud dns managed-zones create example-zone \
  --dns-name="example.com." \
  --description="Production DNS zone for example.com" \
  --visibility=public

# Note: The trailing dot after the domain name is required (DNS convention)

# View the assigned nameservers
gcloud dns managed-zones describe example-zone \
  --format="yaml(nameServers)"

# Output will be something like:
# nameServers:
# - ns-cloud-a1.googledomains.com.
# - ns-cloud-a2.googledomains.com.
# - ns-cloud-a3.googledomains.com.
# - ns-cloud-a4.googledomains.com.
#
# You must update your domain registrar's NS records to point to these.
```

### Managing DNS Records

```bash
# Start a transaction (atomic change set)
gcloud dns record-sets transaction start --zone=example-zone

# Add an A record pointing to a load balancer IP
gcloud dns record-sets transaction add "34.120.55.100" \
  --name="app.example.com." \
  --ttl=300 \
  --type=A \
  --zone=example-zone

# Add a CNAME for www
gcloud dns record-sets transaction add "app.example.com." \
  --name="www.example.com." \
  --ttl=300 \
  --type=CNAME \
  --zone=example-zone

# Add an MX record for email
gcloud dns record-sets transaction add "10 mail.example.com." \
  --name="example.com." \
  --ttl=3600 \
  --type=MX \
  --zone=example-zone

# Add a TXT record for domain verification
gcloud dns record-sets transaction add '"google-site-verification=abc123"' \
  --name="example.com." \
  --ttl=300 \
  --type=TXT \
  --zone=example-zone

# Execute the transaction (all changes are applied atomically)
gcloud dns record-sets transaction execute --zone=example-zone

# List all records in the zone
gcloud dns record-sets list --zone=example-zone \
  --format="table(name, type, ttl, rrdatas[0])"

# Abort a transaction (if you made a mistake before executing)
gcloud dns record-sets transaction abort --zone=example-zone
```

### Modifying and Deleting Records

```bash
# To modify a record, you must remove the old one and add the new one
# in the same transaction
gcloud dns record-sets transaction start --zone=example-zone

gcloud dns record-sets transaction remove "34.120.55.100" \
  --name="app.example.com." \
  --ttl=300 \
  --type=A \
  --zone=example-zone

gcloud dns record-sets transaction add "34.120.55.200" \
  --name="app.example.com." \
  --ttl=300 \
  --type=A \
  --zone=example-zone

gcloud dns record-sets transaction execute --zone=example-zone
```

### TTL Strategy

TTL (Time to Live) controls how long resolvers cache a DNS response. Choosing the right TTL is a trade-off between performance and agility.

| TTL | Duration | Use Case | Trade-off |
| :--- | :--- | :--- | :--- |
| **60** | 1 minute | Records that change during failover | More DNS queries, faster propagation |
| **300** | 5 minutes | General web application records | Good balance for most use cases |
| **3600** | 1 hour | Stable records (MX, NS) | Fewer queries, slow to change |
| **86400** | 1 day | Records that rarely change | Most efficient, very slow to propagate changes |

**Pro tip**: Before a planned migration, lower the TTL to 60 seconds at least 24 hours in advance (equal to the current TTL). This ensures that by migration time, all caches have the short TTL and will pick up the new IP quickly.

---

## Private Zones: Internal DNS

Private DNS zones are visible only from within specified VPC networks. They are essential for internal service discovery---allowing you to give friendly names to internal resources without exposing those names to the internet.

```text
  ┌────────────────────────────────────────────┐
  │  VPC: prod-vpc                              │
  │                                              │
  │  Private Zone: internal.example.com          │
  │                                              │
  │  ┌──────────┐     ┌──────────┐              │
  │  │ VM: web-1 │     │ VM: db-1  │             │
  │  │           │     │           │             │
  │  │ Resolves: │     │ 10.10.1.5 │             │
  │  │ db.internal│    │           │             │
  │  │ .example  │     │           │             │
  │  │ .com      │     │           │             │
  │  │ → 10.10.1.5│    │           │             │
  │  └──────────┘     └──────────┘              │
  │                                              │
  │  DNS queries to internal.example.com are     │
  │  answered by Cloud DNS (private zone).       │
  │  DNS queries to www.google.com go to         │
  │  public DNS as normal.                       │
  └────────────────────────────────────────────┘
```

### Creating a Private Zone

```bash
# Create a private managed zone visible to a specific VPC
gcloud dns managed-zones create internal-zone \
  --dns-name="internal.example.com." \
  --description="Internal DNS for prod VPC" \
  --visibility=private \
  --networks=prod-vpc

# Add internal records
gcloud dns record-sets transaction start --zone=internal-zone

gcloud dns record-sets transaction add "10.10.1.5" \
  --name="db.internal.example.com." \
  --ttl=300 \
  --type=A \
  --zone=internal-zone

gcloud dns record-sets transaction add "10.10.1.10" \
  --name="api.internal.example.com." \
  --ttl=300 \
  --type=A \
  --zone=internal-zone

gcloud dns record-sets transaction add "10.10.1.15" \
  --name="cache.internal.example.com." \
  --ttl=60 \
  --type=A \
  --zone=internal-zone

gcloud dns record-sets transaction execute --zone=internal-zone

# Verify resolution from within the VPC
gcloud compute ssh vm-in-prod-vpc --zone=us-central1-a \
  --command="dig db.internal.example.com +short"
```

### Making a Private Zone Visible to Multiple VPCs

```bash
# Add another VPC to the zone's visibility
gcloud dns managed-zones update internal-zone \
  --networks=prod-vpc,staging-vpc

# You can also add VPCs from other projects (cross-project visibility)
gcloud dns managed-zones update internal-zone \
  --networks=projects/project-a/global/networks/vpc-a,projects/project-b/global/networks/vpc-b
```

### Private Zone Resolution Order

When a VM in a VPC makes a DNS query, Cloud DNS resolves it in this order:

```text
1. Private zones attached to the VM's VPC
   (e.g., internal.example.com → private zone answers)

2. Forwarding zones (if configured)
   (e.g., corp.company.com → forwarded to on-premises DNS)

3. Peering zones (if configured)
   (e.g., partner.example.com → resolved via peered VPC)

4. Google public DNS
   (e.g., www.google.com → resolved via public DNS)
```

---

## DNS Forwarding: Hybrid Cloud DNS

DNS forwarding allows you to forward queries for specific domains to external DNS servers. This is critical in hybrid environments where on-premises resources have DNS records in on-premises DNS servers.

### Outbound Forwarding (GCP to On-Premises)

```text
  ┌──────────────────────────┐      ┌───────────────────────┐
  │  GCP VPC                  │      │  On-Premises           │
  │                            │      │                        │
  │  VM queries:               │      │  DNS Server             │
  │  db.corp.company.com       │      │  10.200.0.53            │
  │         │                  │      │                        │
  │         ▼                  │      │  Knows about:           │
  │  Cloud DNS checks:         │      │  *.corp.company.com     │
  │  "Is there a private zone?"│      │                        │
  │  "No → check forwarding"  │      │                        │
  │  "Yes! Forward to         │──────│→ Resolves and returns   │
  │   10.200.0.53"            │ VPN  │  10.200.5.20            │
  │                            │      │                        │
  └──────────────────────────┘      └───────────────────────┘
```

```bash
# Create a forwarding zone
gcloud dns managed-zones create corp-forwarding \
  --dns-name="corp.company.com." \
  --description="Forward queries to on-premises DNS" \
  --visibility=private \
  --networks=prod-vpc \
  --forwarding-targets="10.200.0.53,10.200.0.54"

# Forwarding with private routing (uses VPN/Interconnect, not internet)
gcloud dns managed-zones create corp-forwarding-private \
  --dns-name="corp.company.com." \
  --description="Forward queries via private routing" \
  --visibility=private \
  --networks=prod-vpc \
  --forwarding-targets="10.200.0.53[private],10.200.0.54[private]"
```

### Inbound Forwarding (On-Premises to GCP)

For on-premises systems to resolve GCP private DNS zones, you need to set up an **inbound DNS policy** that creates a forwarding IP in your VPC. On-premises DNS servers then forward queries to this IP.

```bash
# Create a DNS server policy with inbound forwarding enabled
gcloud dns policies create allow-inbound \
  --description="Allow inbound DNS forwarding from on-premises" \
  --networks=prod-vpc \
  --enable-inbound-forwarding

# View the inbound forwarder IPs (one per subnet)
gcloud compute addresses list \
  --filter="purpose=DNS_RESOLVER" \
  --format="table(name, address, subnetwork)"

# On your on-premises DNS server, create a conditional forwarder:
# Forward *.internal.example.com → <inbound forwarder IP>
```

### Alternative Forwarding via DNS Policies

DNS policies allow you to configure forwarding behavior at the VPC level instead of creating forwarding zones.

```bash
# Create a policy that forwards all DNS to custom nameservers
gcloud dns policies create custom-dns \
  --description="Use custom DNS servers for all resolution" \
  --networks=prod-vpc \
  --alternative-name-servers="10.200.0.53,10.200.0.54" \
  --enable-logging

# List DNS policies
gcloud dns policies list

# Delete a policy
gcloud dns policies delete custom-dns
```

---

## DNS Peering: Cross-VPC Resolution

DNS peering zones allow one VPC to resolve DNS names using another VPC's private zones, without creating a full VPC peering or sharing the zones directly. This is useful when you have a central "DNS hub" VPC.

```text
  ┌──────────────────────┐     DNS Peering     ┌──────────────────────┐
  │  VPC: app-vpc         │ ──────────────────> │  VPC: dns-hub-vpc     │
  │                        │                     │                        │
  │  VM queries:           │                     │  Has private zones:    │
  │  db.internal.com       │                     │  - internal.com        │
  │                        │                     │  - staging.internal.com│
  │  "I don't have a       │                     │                        │
  │   zone for this...     │                     │  Has forwarding zones: │
  │   but I peer with      │                     │  - corp.company.com    │
  │   dns-hub-vpc"        │                     │    → on-premises DNS   │
  └────────────────────────┘                     └────────────────────────┘
```

```bash
# Create a peering zone in app-vpc that peers with dns-hub-vpc
gcloud dns managed-zones create peer-to-hub \
  --dns-name="internal.com." \
  --description="Peer DNS resolution to hub VPC" \
  --visibility=private \
  --networks=app-vpc \
  --target-network=dns-hub-vpc \
  --target-project=shared-networking
```

### When to Use Which

| Scenario | Solution | Why |
| :--- | :--- | :--- |
| Internal names within a single VPC | Private zone | Simplest setup |
| Internal names shared across VPCs | Private zone with multiple networks | Direct, no peering needed |
| Centralized DNS management (hub-spoke) | DNS peering zones | Hub VPC manages all zones |
| On-premises to GCP resolution | Inbound forwarding policy | On-prem DNS forwards to GCP |
| GCP to on-premises resolution | Forwarding zone | Cloud DNS forwards to on-prem |
| Shared VPC with private DNS | Private zone on shared VPC | All service projects resolve automatically |

---

## DNSSEC: Securing DNS

DNSSEC (Domain Name System Security Extensions) protects against DNS spoofing by digitally signing DNS records. Cloud DNS supports DNSSEC for public zones.

```bash
# Enable DNSSEC on a public zone
gcloud dns managed-zones update example-zone \
  --dnssec-state=on

# View DNSSEC configuration (DS records to add at your registrar)
gcloud dns dns-keys list --zone=example-zone \
  --format="table(keyTag, type, algorithm, dsRecord())"

# Transfer the DS record to your domain registrar to complete the chain of trust
```

---

## DNS Logging

DNS query logging helps you understand what your workloads are resolving and detect anomalous behavior.

```bash
# Enable DNS logging via a policy
gcloud dns policies create logging-policy \
  --description="Enable DNS query logging" \
  --networks=prod-vpc \
  --enable-logging

# View DNS logs in Cloud Logging
gcloud logging read 'resource.type="dns_query"' \
  --limit=20 \
  --format="table(jsonPayload.queryName, jsonPayload.queryType, jsonPayload.responseCode, jsonPayload.sourceIP)"
```

---

## Did You Know?

1. **Cloud DNS guarantees 100% availability SLA**---one of the highest SLAs in all of GCP. It achieves this by using Google's global Anycast network, which means DNS queries are served from the nearest of hundreds of Google Points of Presence worldwide. Even if an entire region goes down, DNS continues to resolve from other locations.

2. **The maximum TTL you can set in Cloud DNS is 86,400 seconds (24 hours)**, but many recursive resolvers cache records for longer if the SOA record's minimum TTL suggests it. In practice, when you change a DNS record, expect full propagation to take up to 48 hours for some edge cases, even if your TTL is set to 300 seconds, because some resolvers do not respect TTLs strictly.

3. **Private zones override public zones for the same domain**. If you create a private zone for `example.com` in your VPC, VMs in that VPC will resolve `example.com` using the private zone and will NOT be able to reach the public `example.com` records. This is both a feature (for split-horizon DNS) and a trap (if you accidentally create a private zone for a domain you also need to reach publicly).

4. **Cloud DNS supports Response Policy Zones (RPZs)**, which let you override DNS responses for specific domains. This is effectively a DNS-level firewall---you can block known malicious domains by returning `NXDOMAIN` or redirect them to a sinkhole IP. Enterprises use RPZs to enforce security policies without deploying additional infrastructure.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Forgetting the trailing dot on DNS names | Not familiar with DNS convention | Always append `.` to fully qualified domain names in Cloud DNS |
| Creating a private zone for a public domain | Wanting split-horizon DNS without understanding the override | Only create private zones for domains you do not need to resolve publicly, or carefully manage the split |
| Setting TTL too high before a migration | Not planning the migration in advance | Lower TTL to 60 seconds at least 24 hours before the change |
| Not configuring DNS forwarding for hybrid setups | Assuming on-premises names "just work" | Create forwarding zones for each on-premises domain |
| Exposing private DNS to unauthorized VPCs | Adding too many networks to a private zone | Use DNS peering via a hub VPC instead of adding every VPC to every zone |
| Ignoring DNS logging | Not knowing the feature exists | Enable DNS logging on all production VPCs; invaluable for security investigations |
| Using CNAME at the zone apex | DNS standards prohibit it | Use an A record for the zone apex; CNAME works only for subdomains |
| Not setting up DNSSEC for public zones | Perceived as complex to configure | Cloud DNS makes it simple; enable it and add the DS record to your registrar |

---

## Quiz

<details>
<summary>1. What happens if you create a private DNS zone for "example.com" in a VPC, and you also have a public DNS zone for "example.com"?</summary>

The **private zone takes precedence** for VMs within that VPC. All DNS queries from VMs in the VPC for `example.com` and any subdomains will be resolved using the private zone, completely ignoring the public zone. This is called "split-horizon DNS." If the private zone does not contain a record for a specific subdomain (e.g., `app.example.com`), the query will return `NXDOMAIN` rather than falling through to the public zone. This behavior is intentional for security (preventing internal VMs from reaching untrusted external endpoints) but can be a trap if you need some records from the public zone.
</details>

<details>
<summary>2. How does DNS peering differ from simply adding multiple VPCs to a private zone?</summary>

When you add multiple VPCs to a private zone, each VPC gets direct visibility into the zone's records. This works but does not scale: if you have 50 VPCs and 20 private zones, you need to manage 1,000 zone-to-VPC bindings. **DNS peering** creates a delegation relationship where one VPC (the "consumer") forwards its DNS queries to another VPC (the "producer") for resolution. The consumer does not need to be listed on every private zone---it just peers with the hub VPC, which has access to all zones. This creates a clean hub-spoke architecture for DNS management.
</details>

<details>
<summary>3. An on-premises server needs to resolve a private Cloud DNS zone in GCP. What do you need to configure?</summary>

You need two things. First, create a **DNS server policy** with inbound forwarding enabled on the VPC where the private zone is attached (`--enable-inbound-forwarding`). This creates special forwarding IP addresses in each subnet. Second, configure your **on-premises DNS server** to forward queries for the private zone's domain to the inbound forwarding IP address. Traffic flows from the on-premises DNS server through the VPN or Cloud Interconnect to the inbound forwarder IP in GCP, which resolves the query against the private zone and returns the answer.
</details>

<details>
<summary>4. Why can you not create a CNAME record at the zone apex (e.g., "example.com" without a subdomain)?</summary>

The DNS specification (RFC 1034) prohibits CNAME records at the zone apex because the apex must also have SOA and NS records, and the CNAME specification states that no other record types can coexist with a CNAME. If you try to create a CNAME for `example.com.`, Cloud DNS will reject it. The solution is to use an **A record** (or AAAA record) at the apex pointing directly to your load balancer's IP address. Some DNS providers offer proprietary "ALIAS" or "ANAME" records that work around this limitation, but Cloud DNS does not---you must use A/AAAA records at the apex.
</details>

<details>
<summary>5. What is the purpose of DNS response policies (RPZs), and how might you use them for security?</summary>

Response Policy Zones (RPZs) allow you to override DNS responses for specific domains. You create a response policy with rules that match domain names and return custom responses (like `NXDOMAIN`, a sinkhole IP address, or passthrough to normal resolution). For security, you can use RPZs to block known malicious domains, phishing sites, or command-and-control servers by returning `NXDOMAIN` for those domains. This provides a DNS-level firewall without requiring agents on VMs or additional network appliances. RPZs are evaluated before normal DNS resolution.
</details>

<details>
<summary>6. You need to migrate a web application to a new IP address. The current DNS record has a TTL of 86400 (24 hours). What is the correct migration procedure?</summary>

The correct procedure involves multiple steps. First, **lower the TTL** from 86400 to 60 seconds at least 24-48 hours before the migration. This ensures that all caches worldwide will have the short TTL by migration time. Second, **perform the migration** by updating the A record to the new IP address. Because the TTL is now 60 seconds, most resolvers will pick up the new IP within 1-2 minutes. Third, **monitor** traffic on both the old and new IP for stragglers (some resolvers do not strictly respect TTLs). Fourth, after the migration is confirmed successful and all traffic has shifted, **increase the TTL** back to an appropriate value to reduce DNS query load.
</details>

---

## Hands-On Exercise: Public and Private DNS Zones

### Objective

Create and manage public and private DNS zones, demonstrate split-horizon DNS behavior, and configure DNS forwarding.

### Prerequisites

- `gcloud` CLI installed and authenticated
- A GCP project with billing enabled
- A custom VPC (from Module 2.2 or create one)

### Tasks

**Task 1: Create a Custom VPC and VM for Testing**

<details>
<summary>Solution</summary>

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1

# Enable DNS API
gcloud services enable dns.googleapis.com --project=$PROJECT_ID

# Create a VPC for testing (skip if you already have one)
gcloud compute networks create dns-test-vpc \
  --subnet-mode=custom

gcloud compute networks subnets create dns-test-subnet \
  --network=dns-test-vpc \
  --region=$REGION \
  --range=10.50.0.0/24

# Create firewall rule for IAP SSH
gcloud compute firewall-rules create dns-vpc-allow-iap \
  --network=dns-test-vpc \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=35.235.240.0/20

# Create a test VM
gcloud compute instances create dns-test-vm \
  --zone=${REGION}-a \
  --machine-type=e2-micro \
  --subnet=dns-test-subnet \
  --no-address \
  --image-family=debian-12 \
  --image-project=debian-cloud
```
</details>

**Task 2: Create a Public DNS Zone**

<details>
<summary>Solution</summary>

```bash
# Create a public zone (use a domain you own, or a test domain)
gcloud dns managed-zones create lab-public-zone \
  --dns-name="lab.example.com." \
  --description="Lab public DNS zone" \
  --visibility=public

# View the assigned nameservers
gcloud dns managed-zones describe lab-public-zone \
  --format="yaml(nameServers)"

# Add records via transaction
gcloud dns record-sets transaction start --zone=lab-public-zone

gcloud dns record-sets transaction add "34.120.55.100" \
  --name="web.lab.example.com." \
  --ttl=300 \
  --type=A \
  --zone=lab-public-zone

gcloud dns record-sets transaction add "web.lab.example.com." \
  --name="www.lab.example.com." \
  --ttl=300 \
  --type=CNAME \
  --zone=lab-public-zone

gcloud dns record-sets transaction execute --zone=lab-public-zone

# List records
gcloud dns record-sets list --zone=lab-public-zone \
  --format="table(name, type, ttl, rrdatas[0])"
```
</details>

**Task 3: Create a Private DNS Zone**

<details>
<summary>Solution</summary>

```bash
# Create a private zone for internal service discovery
gcloud dns managed-zones create lab-private-zone \
  --dns-name="internal.lab.com." \
  --description="Internal DNS for lab VPC" \
  --visibility=private \
  --networks=dns-test-vpc

# Add internal records
gcloud dns record-sets transaction start --zone=lab-private-zone

gcloud dns record-sets transaction add "10.50.0.10" \
  --name="db.internal.lab.com." \
  --ttl=60 \
  --type=A \
  --zone=lab-private-zone

gcloud dns record-sets transaction add "10.50.0.20" \
  --name="api.internal.lab.com." \
  --ttl=60 \
  --type=A \
  --zone=lab-private-zone

gcloud dns record-sets transaction add "10.50.0.30" \
  --name="cache.internal.lab.com." \
  --ttl=60 \
  --type=A \
  --zone=lab-private-zone

gcloud dns record-sets transaction execute --zone=lab-private-zone

# Test from the VM
gcloud compute ssh dns-test-vm --zone=${REGION}-a --tunnel-through-iap \
  --command="dig db.internal.lab.com +short && dig api.internal.lab.com +short"
```
</details>

**Task 4: Enable DNS Logging**

<details>
<summary>Solution</summary>

```bash
# Create a DNS policy with logging enabled
gcloud dns policies create dns-logging \
  --description="Enable DNS query logging" \
  --networks=dns-test-vpc \
  --enable-logging

# Generate some DNS queries from the VM
gcloud compute ssh dns-test-vm --zone=${REGION}-a --tunnel-through-iap \
  --command="dig db.internal.lab.com && dig www.google.com && dig api.internal.lab.com"

# Wait a moment for logs to appear, then query them
sleep 15
gcloud logging read 'resource.type="dns_query"' \
  --limit=10 \
  --format="table(jsonPayload.queryName, jsonPayload.queryType, jsonPayload.responseCode)"
```
</details>

**Task 5: Modify Records (Simulating a Migration)**

<details>
<summary>Solution</summary>

```bash
# Lower TTL first (migration preparation)
gcloud dns record-sets transaction start --zone=lab-private-zone

gcloud dns record-sets transaction remove "10.50.0.10" \
  --name="db.internal.lab.com." \
  --ttl=60 \
  --type=A \
  --zone=lab-private-zone

gcloud dns record-sets transaction add "10.50.0.11" \
  --name="db.internal.lab.com." \
  --ttl=60 \
  --type=A \
  --zone=lab-private-zone

gcloud dns record-sets transaction execute --zone=lab-private-zone

# Verify the change
gcloud compute ssh dns-test-vm --zone=${REGION}-a --tunnel-through-iap \
  --command="dig db.internal.lab.com +short"
# Should return 10.50.0.11
```
</details>

**Task 6: Clean Up**

<details>
<summary>Solution</summary>

```bash
# Delete DNS policies
gcloud dns policies delete dns-logging --quiet

# Delete record sets (must delete non-default records before zone)
gcloud dns record-sets transaction start --zone=lab-public-zone
gcloud dns record-sets transaction remove "34.120.55.100" \
  --name="web.lab.example.com." --ttl=300 --type=A --zone=lab-public-zone
gcloud dns record-sets transaction remove "web.lab.example.com." \
  --name="www.lab.example.com." --ttl=300 --type=CNAME --zone=lab-public-zone
gcloud dns record-sets transaction execute --zone=lab-public-zone

gcloud dns record-sets transaction start --zone=lab-private-zone
gcloud dns record-sets transaction remove "10.50.0.11" \
  --name="db.internal.lab.com." --ttl=60 --type=A --zone=lab-private-zone
gcloud dns record-sets transaction remove "10.50.0.20" \
  --name="api.internal.lab.com." --ttl=60 --type=A --zone=lab-private-zone
gcloud dns record-sets transaction remove "10.50.0.30" \
  --name="cache.internal.lab.com." --ttl=60 --type=A --zone=lab-private-zone
gcloud dns record-sets transaction execute --zone=lab-private-zone

# Delete zones
gcloud dns managed-zones delete lab-public-zone --quiet
gcloud dns managed-zones delete lab-private-zone --quiet

# Delete VM and network
gcloud compute instances delete dns-test-vm --zone=${REGION}-a --quiet
gcloud compute firewall-rules delete dns-vpc-allow-iap --quiet
gcloud compute networks subnets delete dns-test-subnet --region=$REGION --quiet
gcloud compute networks delete dns-test-vpc --quiet

echo "Cleanup complete."
```
</details>

### Success Criteria

- [ ] Public DNS zone created with A and CNAME records
- [ ] Private DNS zone created and resolvable from within the VPC
- [ ] DNS logging enabled and queries visible in Cloud Logging
- [ ] DNS record modified (simulated migration)
- [ ] Private zone records NOT resolvable from outside the VPC
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 2.6: Artifact Registry](module-2.6-artifact-registry/)** --- Learn how to store container images, scan for vulnerabilities, configure IAM-based access control, and set up upstream caching for public registries.
