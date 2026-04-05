---
title: "Module 1.2: Virtual Private Cloud (VPC) & Core Networking"
slug: cloud/aws-essentials/module-1.2-vpc
sidebar:
  order: 3
---
**Complexity**: [COMPLEX] | **Time to Complete**: 3h | **Prerequisites**: Module 1.1, Linux Networking

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design multi-AZ VPC architectures with public and private subnets that support high-availability workloads**
- **Configure Security Groups and Network ACLs to implement defense-in-depth network segmentation**
- **Explain VPC peering and Transit Gateway architectures for connecting multiple VPCs at scale**
- **Diagnose routing table misconfigurations and connectivity failures between subnets, NAT Gateways, and internet gateways**

---

## Why This Module Matters

In 2018, a major cryptocurrency exchange discovered unauthorized access to their internal administration tools. The attackers had bypassed the external web application firewall entirely. How? The engineering team had deployed a temporary EC2 instance to test a new database migration script. To make it easy to SSH into, they attached a security group allowing port 22 from `0.0.0.0/0` and placed it in a public subnet, effectively hanging a server containing administrative database credentials directly on the public internet. The attackers brute-forced the SSH key within hours, pivoted to the private subnets holding the primary databases, and triggered a massive localized outage while attempting to exfiltrate data.

This scenario highlights the unforgiving nature of cloud networking. Amazon Virtual Private Cloud (VPC) is the logical isolation boundary for your AWS infrastructure. It is your private slice of the cloud. Without a correctly designed VPC architecture, your databases are a single misconfiguration away from the public internet, and your internal traffic is exposed to lateral movement.

In this module, you will learn how to design a resilient, highly available network topology. You will understand the critical distinction between public and private subnets, master the routing logic that controls traffic flow, and learn how to implement defense-in-depth using Security Groups and Network ACLs. Finally, you will explore how to connect multiple VPCs at scale. Mastering VPC is not just about connecting servers; it is about building the moats, walls, and bridges that protect your entire cloud footprint.

---

## Anatomy of a VPC: CIDR Blocks and Subnets

A VPC is a logically isolated virtual network defined by a primary IPv4 Classless Inter-Domain Routing (CIDR) block (e.g., `10.0.0.0/16`). This block determines the total pool of IP addresses available within the VPC.

Think of CIDR notation as choosing how big your plot of land is before you build anything on it. The number after the slash tells you how many bits of the address are fixed (the "network" portion), and the remaining bits are yours to assign to individual resources (the "host" portion).

### Quick CIDR Reference

| CIDR | Total IPs | Usable IPs (AWS) | Typical Use |
| :--- | :--- | :--- | :--- |
| `/16` | 65,536 | Varies* | Large production VPC |
| `/20` | 4,096 | 4,091 | Medium VPC or large subnet |
| `/24` | 256 | 251 | Standard subnet |
| `/28` | 16 | 11 | Minimal subnet (smallest AWS allows) |

AWS allows VPC CIDR blocks between `/16` (largest) and `/28` (smallest). You can also add secondary CIDR blocks to an existing VPC if you run out of address space, but planning upfront is always better than retrofitting later.

**IP planning matters more than you think.** If you plan to peer VPCs together or connect them via Transit Gateway, their CIDR blocks must not overlap. The most common regret teams have at scale is "we used `10.0.0.0/16` for every VPC and now we cannot connect them." Plan a non-overlapping scheme from day one:

```text
Production VPC:   10.1.0.0/16
Staging VPC:      10.2.0.0/16
Development VPC:  10.3.0.0/16
Shared Services:  10.10.0.0/16
```

### Subnets: Slicing the Network

You cannot launch an EC2 instance directly into a VPC. You must launch it into a **Subnet**. Subnets are smaller blocks of IPs carved out of the VPC's CIDR range.

Crucially, **a subnet must reside entirely within one Availability Zone (AZ)**. It cannot span across AZs. To achieve high availability, you must deploy resources across multiple subnets located in different AZs.

```text
VPC: 10.0.0.0/16 (65,536 IPs)
├── Availability Zone: us-east-1a
│   ├── Subnet A (Public):  10.0.1.0/24  (251 usable IPs)
│   ├── Subnet B (Private): 10.0.2.0/24  (251 usable IPs)
│   └── Subnet C (Data):    10.0.3.0/24  (251 usable IPs)
├── Availability Zone: us-east-1b
│   ├── Subnet D (Public):  10.0.11.0/24 (251 usable IPs)
│   ├── Subnet E (Private): 10.0.12.0/24 (251 usable IPs)
│   └── Subnet F (Data):    10.0.13.0/24 (251 usable IPs)
└── Availability Zone: us-east-1c
    ├── Subnet G (Public):  10.0.21.0/24 (251 usable IPs)
    ├── Subnet H (Private): 10.0.22.0/24 (251 usable IPs)
    └── Subnet I (Data):    10.0.23.0/24 (251 usable IPs)
```

**Why three tiers?** Production architectures typically separate workloads into layers:

- **Public subnets** -- Load balancers, bastion hosts, NAT Gateways
- **Private subnets** -- Application servers, containers, compute
- **Data subnets** -- Databases (RDS, ElastiCache), sensitive storage

This layering enforces the principle of least privilege at the network level: the internet can reach the public tier, the public tier can reach the private tier, and only the private tier can reach the data tier.

> **AWS Reserved IPs**: AWS reserves the first 4 and the last 1 IP address in every subnet for internal networking purposes. In a `/24` (256 IPs), the reserved addresses are:
>
> - `.0` -- Network address
> - `.1` -- VPC router
> - `.2` -- Reserved (DNS server is at VPC base CIDR + 2, e.g. `10.0.0.2`)
> - `.3` -- Reserved for future use
> - `.255` -- Broadcast address (AWS does not support broadcast, but reserves it)
>
> This gives you **251 usable IPs**, not 256.

---

## Routing: How Traffic Finds Its Way

Every subnet in a VPC is associated with exactly one **Route Table**. The route table is a set of rules (called routes) that determine where network traffic is directed. If you do not explicitly associate a subnet with a route table, it uses the VPC's **Main Route Table**.

### The Default Route Table

Every VPC comes with a Main Route Table containing a single route:

| Destination | Target | Purpose |
| :--- | :--- | :--- |
| `10.0.0.0/16` | `local` | All traffic within the VPC stays internal |

This `local` route is immutable -- you cannot remove or modify it. It ensures that any resource in the VPC can communicate with any other resource in the VPC (subject to security group and NACL rules).

### Public vs. Private Subnets: The Route Table Distinction

What makes a subnet "public" or "private"? It is **not** a configuration flag on the subnet itself. There is no checkbox labeled "Make this subnet public." The distinction is determined entirely by the **Route Table** associated with the subnet.

- **Public Subnet**: A subnet is public if its route table has a route directing internet-bound traffic (`0.0.0.0/0`) to an **Internet Gateway (IGW)**. An IGW is a highly available, horizontally scaled VPC component that provides a connection to the public internet.
- **Private Subnet**: A subnet is private if it does *not* have a route to an IGW. Instances here cannot be reached from the public internet, even if they have public IP addresses assigned.

Here is what the route tables look like side by side:

**Public Subnet Route Table:**

| Destination | Target |
| :--- | :--- |
| `10.0.0.0/16` | `local` |
| `0.0.0.0/0` | `igw-abc123` |

**Private Subnet Route Table:**

| Destination | Target |
| :--- | :--- |
| `10.0.0.0/16` | `local` |
| `0.0.0.0/0` | `nat-xyz789` |

**Data Subnet Route Table (most restrictive):**

| Destination | Target |
| :--- | :--- |
| `10.0.0.0/16` | `local` |

Notice: the data tier has no route to the internet at all. Not through an IGW, not through a NAT. Complete isolation.

### Traffic Flow: Public Subnet

Here is how a request from the internet reaches an EC2 instance in a public subnet:

```text
Internet User
      │
      ▼
┌──────────────┐
│ Internet     │
│ Gateway (IGW)│
└──────┬───────┘
       │  Route table says: 10.0.0.0/16 → local
       ▼
┌──────────────────────────────────────────┐
│         NACL (Subnet Boundary)           │
│  Evaluates inbound rules sequentially    │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│      Security Group (Instance Level)     │
│  Checks: Is port 443 allowed inbound?   │
└──────────────────┬───────────────────────┘
                   │
                   ▼
            ┌─────────────┐
            │ EC2 Instance│
            │ 10.0.1.10   │
            │ (Public IP: │
            │  54.x.x.x)  │
            └─────────────┘
```

The return traffic follows the reverse path. Because Security Groups are **stateful**, the response is automatically allowed out. But if a NACL is in the path, you must have explicit outbound rules (NACLs are **stateless**).

### The Internet Gateway (IGW)

The IGW deserves a closer look because it is often misunderstood:

- It performs **1:1 NAT** between an instance's private IP and its associated public/Elastic IP
- It is **not** a bottleneck -- it is horizontally scaled and redundant by design
- It imposes **no bandwidth limits** of its own (your bandwidth limit comes from the instance type)
- You can only attach **one IGW per VPC**
- Creating an IGW alone does nothing -- you must also attach it to the VPC and add a route to it

---

## NAT Gateways: Outbound Access for Private Resources

If a database in a private subnet needs to download security patches from the internet, or an application server needs to call an external API, how does it do so without a route to the IGW?

The solution is a **Network Address Translation (NAT) Gateway**.

### How NAT Gateway Works

1. You deploy a NAT Gateway into a **public subnet** (it needs IGW access).
2. You allocate an **Elastic IP** address and assign it to the NAT Gateway.
3. You configure the route table of the **private subnet** to send internet-bound traffic (`0.0.0.0/0`) to the NAT Gateway.
4. The NAT Gateway receives the traffic, translates the private IP to its own Elastic IP, forwards the traffic out through the IGW, receives the response, translates it back, and sends it to the private instance.

This allows private instances to **initiate outbound connections** while remaining completely **unreachable from inbound connections** originating on the internet.

### NAT Gateway Traffic Flow

```text
Private Instance (10.0.2.50)
      │
      │ Outbound request to https://api.example.com
      ▼
┌──────────────────────────────────────────┐
│  Private Subnet Route Table              │
│  0.0.0.0/0 → nat-xyz789                 │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│          NAT Gateway                     │
│  (Lives in PUBLIC subnet)                │
│  Translates: 10.0.2.50 → 52.x.x.x (EIP)│
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  Public Subnet Route Table               │
│  0.0.0.0/0 → igw-abc123                 │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│          Internet Gateway                │
└──────────────────┬───────────────────────┘
                   │
                   ▼
            ┌─────────────┐
            │  Internet   │
            │ api.example │
            │   .com      │
            └─────────────┘
```

The response follows the exact reverse path. The IGW sends it to the NAT Gateway's Elastic IP, the NAT Gateway translates the destination back to `10.0.2.50`, and delivers it to the private instance.

### NAT Gateway: High Availability Pattern

A single NAT Gateway resides in a single AZ. If that AZ fails, all private subnets routing through it lose internet access. For production workloads, deploy one NAT Gateway per AZ:

```text
AZ-1a:  NAT-GW-1 (in Public-Subnet-1a)  ← Private-Subnet-1a routes here
AZ-1b:  NAT-GW-2 (in Public-Subnet-1b)  ← Private-Subnet-1b routes here
AZ-1c:  NAT-GW-3 (in Public-Subnet-1c)  ← Private-Subnet-1c routes here
```

Each private subnet's route table points to the NAT Gateway in its own AZ. This means each AZ is self-contained for outbound internet access.

### NAT Gateway vs. NAT Instance

Before NAT Gateways existed as a managed service, teams ran their own NAT on EC2 instances. You may still encounter this in legacy environments:

| Feature | NAT Gateway | NAT Instance |
| :--- | :--- | :--- |
| **Managed by** | AWS | You |
| **Availability** | Redundant within AZ | Single instance (you manage failover) |
| **Bandwidth** | Up to 100 Gbps | Depends on instance type |
| **Maintenance** | None | You patch the OS and software |
| **Security Groups** | Cannot associate | Can associate |
| **Cost** | ~$0.045/hr + data | Instance cost + data |
| **Use today?** | Yes (recommended) | Only for very specific edge cases |

### VPC Endpoints: Bypassing NAT Entirely

For traffic to AWS services (S3, DynamoDB, SQS, etc.), you often do not need NAT at all. **VPC Endpoints** create a private connection from your VPC directly to the AWS service, keeping traffic on the internal AWS backbone:

- **Gateway Endpoint** (S3, DynamoDB): Free. Adds a route to your route table. No ENI needed.
- **Interface Endpoint** (everything else, via PrivateLink): Creates an ENI in your subnet. Costs ~$0.01/hr + data charges.

Using VPC Endpoints for heavy-traffic services like S3 can save thousands of dollars per month in NAT Gateway data processing charges.

---

## Network Security: Security Groups vs. NACLs

AWS provides two distinct layers of firewall protection within a VPC. Understanding the difference is crucial for troubleshooting network connectivity -- and it is one of the most commonly tested topics in AWS certifications.

### Security Groups (SGs)

Security Groups act as **stateful**, instance-level firewalls.

- **Attachment**: Attached directly to Network Interfaces (ENIs), such as those on EC2 instances, RDS databases, Lambda functions in VPCs, or ELB nodes.
- **Stateful**: If you send a request out from an instance, the response traffic for that request is automatically allowed to flow in, regardless of inbound rules. You do not need to think about ephemeral ports.
- **Rules**: You specify **Allow** rules only. Any traffic not explicitly allowed is implicitly denied. There is no way to write a "Deny" rule in a Security Group.
- **Evaluation**: All rules are evaluated before deciding whether to allow traffic (order does not matter).
- **Chaining**: Instead of using IP addresses, SGs can reference other SGs. You can configure the database SG to "allow traffic on port 3306 from the web-tier SG," automatically accommodating auto-scaling without IP management.
- **Limit**: Up to 5 SGs per ENI (adjustable). Each SG can have up to 60 inbound + 60 outbound rules.

> **Pause and predict**: Web Server A needs to communicate with Database B on port 5432. Both are in the same VPC but different subnets. What is the most secure way to configure the Security Group attached to Database B to allow this traffic?
>
> <details>
> <summary>View Answer</summary>
> Add an inbound rule to Database B's Security Group that allows TCP port 5432, with the <strong>source set to the Security Group ID</strong> attached to Web Server A (e.g., <code>sg-0abcd1234</code>). This ensures that only resources possessing Web Server A's Security Group can connect, regardless of what subnet they are in. It automatically scales as Web Servers are added or removed, without ever needing to manage individual IP addresses. Never use <code>0.0.0.0/0</code> or even the VPC CIDR as the source for database access, as this violates the principle of least privilege.
> </details>

**Example: Chained Security Group Architecture**

```text
Internet
    │
    ▼
┌───────────────────────────┐
│  ALB Security Group       │
│  Inbound: 443 from 0.0.0.0/0 │
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────┐
│  App Security Group       │
│  Inbound: 8080 from sg-alb│
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────┐
│  DB Security Group        │
│  Inbound: 5432 from sg-app│
└───────────────────────────┘
```

Each layer only trusts the layer directly above it. If an attacker compromises the ALB, they still cannot reach the database directly because the DB security group only allows connections from `sg-app`, not `sg-alb`.

### Network Access Control Lists (NACLs)

NACLs act as **stateless**, subnet-level firewalls.

- **Attachment**: Attached to the Subnet boundary. All traffic entering or leaving the subnet must pass through the NACL before reaching any Security Group.
- **Stateless**: Return traffic must be **explicitly allowed**. If you allow outbound HTTP traffic to the internet, you must create a corresponding inbound rule allowing traffic on ephemeral ports (1024-65535) so the response can enter the subnet.
- **Rules**: Support both **Allow** and **Deny** rules, evaluated in order based on rule numbers (lower numbers evaluated first). Once a match is found, evaluation stops.
- **Default NACL**: Every VPC comes with a default NACL that allows all inbound and outbound traffic. Custom NACLs start by denying everything.
- **Use Case**: Primarily used as a secondary defense layer, such as instantly blocking a specific malicious IP address block from entering the subnet at all.

### Security Groups vs. NACLs: Complete Comparison

| Feature | Security Group | Network ACL |
| :--- | :--- | :--- |
| **Operates at** | Instance (ENI) level | Subnet level |
| **State** | Stateful | Stateless |
| **Rule type** | Allow only | Allow AND Deny |
| **Rule evaluation** | All rules evaluated together | Rules evaluated in order (lowest number first) |
| **Default behavior** | Denies all inbound, allows all outbound | Default NACL allows all; custom NACLs deny all |
| **Return traffic** | Automatically allowed | Must be explicitly allowed (ephemeral ports!) |
| **Applies to** | Only resources assigned to the SG | All resources in the subnet |
| **SG references** | Can reference other SGs | Cannot reference SGs (IP/CIDR only) |
| **Rule limit** | 60 inbound + 60 outbound per SG | 20 inbound + 20 outbound (adjustable) |
| **Typical use** | Primary firewall for every resource | Subnet-wide IP blocking, compliance |

> **Stop and think**: A junior engineer configures a NACL with Rule #100 allowing all traffic from 0.0.0.0/0 and Rule #50 denying all traffic from 10.0.0.5/32. An instance at 10.0.0.5 attempts to send traffic into the subnet. What happens and why?
>
> <details>
> <summary>View Answer</summary>
> The traffic is <strong>denied</strong>. NACL rules are evaluated sequentially starting from the lowest rule number. Rule #50 explicitly denies the traffic from <code>10.0.0.5</code>. Once a matching rule is found, the evaluation stops immediately, so the Allow rule at #100 is never processed for this specific traffic. This is why rule numbering matters — always place Deny rules at lower numbers than Allow rules.
> </details>

### Defense in Depth: Both Layers Working Together

```text
                      Internet
                          │
                          ▼
              ┌───────────────────┐
              │  Internet Gateway │
              └─────────┬─────────┘
                        │
           ┌────────────▼────────────┐
           │    NACL (Subnet level)  │ ← Layer 1: Block bad IPs,
           │    Rule 10: DENY        │   enforce subnet-wide policy
           │      198.51.100.0/24    │
           │    Rule 100: ALLOW ALL  │
           └────────────┬────────────┘
                        │
           ┌────────────▼────────────┐
           │  Security Group (ENI)   │ ← Layer 2: Fine-grained
           │  Allow: 443 from 0.0.0.0/0 │   per-resource control
           │  Allow: 22 from 10.0.0.0/16│
           └────────────┬────────────┘
                        │
                        ▼
                  ┌───────────┐
                  │    EC2    │
                  └───────────┘
```

*War Story: A junior engineer modified a NACL attached to a database private subnet, forgetting that NACLs are stateless. They added an outbound rule allowing traffic to the web subnet, but forgot to add the inbound rule allowing the ephemeral port response. Suddenly, the web servers reported massive database timeout errors, despite the Security Groups being perfectly configured. The Security Groups were happily allowing traffic (stateful!), but the NACL was silently dropping the return packets at the subnet boundary. It took two hours of debugging before someone thought to check the NACLs. Stateful SGs are forgiving; stateless NACLs require exact precision.*

---

## VPC Flow Logs: Seeing Your Traffic

You cannot troubleshoot what you cannot see. **VPC Flow Logs** capture metadata about IP traffic going to and from network interfaces in your VPC. They do not capture packet contents (that is what packet capture tools are for), but they tell you:

- Source and destination IP addresses
- Source and destination ports
- Protocol (TCP, UDP, ICMP)
- Number of packets and bytes
- Whether the traffic was **ACCEPT**ed or **REJECT**ed
- The action taken (by SGs and NACLs)

Flow Logs can be enabled at three levels:

1. **VPC level** -- Captures traffic for all ENIs in the VPC
2. **Subnet level** -- Captures traffic for all ENIs in the subnet
3. **ENI level** -- Captures traffic for a specific network interface

Logs can be published to **CloudWatch Logs**, **S3**, or **Kinesis Data Firehose**.

### Reading a Flow Log Entry

```text
2 123456789012 eni-abc123 10.0.1.50 203.0.113.25 443 49152 6 25 5000 1620140761 1620140821 ACCEPT OK
```

| Field | Value | Meaning |
| :--- | :--- | :--- |
| Version | `2` | Flow log version |
| Account ID | `123456789012` | AWS account |
| ENI | `eni-abc123` | Network interface |
| Source IP | `10.0.1.50` | Where the traffic came from |
| Dest IP | `203.0.113.25` | Where it was going |
| Dest Port | `443` | HTTPS |
| Source Port | `49152` | Ephemeral port (client) |
| Protocol | `6` | TCP |
| Packets | `25` | Number of packets |
| Bytes | `5000` | Total bytes |
| Start | `1620140761` | Unix timestamp |
| End | `1620140821` | Unix timestamp |
| Action | `ACCEPT` | Traffic was allowed |
| Status | `OK` | Logging is working |

If you see `REJECT` in the action field, you know either a Security Group or NACL blocked the traffic. Flow Logs are your first stop when debugging "I cannot connect to X."

---

## Connecting VPCs: Peering and Transit Gateway

As infrastructure grows, isolating workloads across multiple AWS accounts and multiple VPCs becomes the standard architectural pattern. How do you connect them?

### VPC Peering

VPC Peering is a one-to-one networking connection between two VPCs that enables routing traffic between them using private IPv4 or IPv6 addresses.

- Traffic stays entirely on the global AWS backbone (no internet routing).
- Works **cross-account** and **cross-region**.
- **Non-Transitive**: If VPC A is peered with VPC B, and VPC B is peered with VPC C, VPC A **cannot** talk to VPC C through B. You must create an explicit peering connection between A and C.
- **No overlapping CIDRs**: You cannot peer two VPCs if any of their CIDR blocks overlap.

> **Stop and think**: You have three VPCs: Dev, Test, and Prod. The Dev VPC is peered with the Test VPC, and the Test VPC is peered with the Prod VPC. An engineer tries to ping an EC2 instance in Prod directly from an EC2 instance in Dev. Does the ping succeed? Why or why not?
>
> <details>
> <summary>View Answer</summary>
> <strong>No, the ping will fail.</strong> VPC Peering is strictly non-transitive. The connection from Dev to Test does not carry over or route through to Prod. To allow the Dev VPC to communicate with the Prod VPC, you must establish an explicit, direct peering connection between them. Alternatively, if managing many connections, you could use a Transit Gateway as a central hub, which does support transitive routing between attached VPCs.
> </details>

**Number of peering connections**: With N VPCs in a full mesh, you need N*(N-1)/2 connections. For 5 VPCs, that is 10 connections. For 20 VPCs, that is 190 connections. This is where peering breaks down.

### AWS Transit Gateway (TGW)

When you have dozens or hundreds of VPCs, managing a full-mesh peering network becomes an operational nightmare. Transit Gateway acts as a highly scalable central hub (a virtual router). You connect all your VPCs, VPNs, and Direct Connects to the central TGW. Routing domains and route tables managed centrally on the TGW control traffic flow, dramatically simplifying network topology.

```text
VPC Peering (Full Mesh):          Transit Gateway (Hub-and-Spoke):

  VPC-A ──── VPC-B                  VPC-A ──┐
    │ \      / │                    VPC-B ──┤
    │  \    /  │                    VPC-C ──┼── Transit Gateway
    │   \  /   │                    VPC-D ──┤
    │    \/    │                    VPN   ──┘
  VPC-C ──── VPC-D
                                    4 attachments vs. 6 peerings
  6 peering connections             Central route management
  6 route table updates per VPC     One route table update per VPC
```

Transit Gateway supports:

- Up to 5,000 attachments per TGW
- Multiple route tables for network segmentation (e.g., Prod VPCs cannot route to Dev VPCs)
- Cross-region peering (TGW-to-TGW)
- Bandwidth up to 50 Gbps per VPC attachment

---

## DNS in a VPC: Route 53 Resolver

Every VPC comes with a built-in DNS server at the base of the VPC CIDR range plus two (e.g., `10.0.0.2` for a `10.0.0.0/16` VPC). This is called the **Amazon-provided DNS** or **AmazonProvidedDNS**.

By default, this DNS server:

- Resolves public DNS hostnames to public IPs
- Resolves private hosted zone records (if `enableDnsHostnames` and `enableDnsSupport` are both true)
- Resolves internal instance hostnames (e.g., `ip-10-0-1-50.ec2.internal`)

For hybrid environments (connecting your VPC to an on-premises data center), **Route 53 Resolver** provides:

- **Inbound Endpoints**: Allow on-premises DNS servers to resolve records in your VPC private hosted zones
- **Outbound Endpoints**: Allow VPC resources to forward DNS queries to your on-premises DNS servers

---

## Did You Know?

1. When you provision a NAT Gateway, you are charged both an hourly rate (~$0.045/hr, or ~$32/month) and a per-gigabyte data processing fee (~$0.045/GB). A team transferring 10 TB/month through a NAT Gateway would pay ~$450 in data processing alone, on top of the hourly fee. Massive data transfers traversing a NAT Gateway can quickly become one of the most expensive items on your AWS bill. Use VPC Endpoints (PrivateLink) to route traffic to AWS services (like S3 or DynamoDB) over the internal network to avoid NAT costs.

2. An Internet Gateway (IGW) is not a physical appliance or a single point of failure; it is a horizontally scaled, redundant, and highly available AWS managed component with no bandwidth constraints. You never need to "size" an IGW or worry about it failing -- AWS handles all of that.

3. VPC Flow Logs can capture information about the IP traffic going to and from network interfaces in your VPC. This data is invaluable for security analysis and for diagnosing why traffic is failing to reach an instance. A single Flow Log entry can tell you whether the traffic was accepted or rejected, instantly narrowing whether the problem is a Security Group, NACL, or route table issue.

4. You can share subnets across different AWS accounts within an Organization using **AWS Resource Access Manager (RAM)**. This allows you to have a central "Networking Account" that manages the VPC and subnets, while application teams deploy instances into those subnets from their own accounts. This pattern (called VPC sharing) dramatically reduces the number of VPCs you need to manage and eliminates the need for VPC peering between teams in the same environment.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Overlapping CIDR blocks** | Creating every VPC with the default `172.31.0.0/16` or always using `10.0.0.0/16`. | Plan your IP addressing strategy carefully before creating any VPCs. Document CIDR assignments. You cannot peer two VPCs if their CIDR blocks overlap. |
| **Databases in public subnets** | "I need to connect to it from my laptop using DBeaver." | Deploy databases in private subnets. Use AWS Systems Manager Session Manager (SSM) or a Bastion host in a public subnet to securely tunnel traffic to the database. |
| **Security Groups allowing `0.0.0.0/0` indiscriminately** | Trying to get an application working quickly by turning off the firewall. | Practice least privilege. Restrict inbound traffic to specific IP ranges or, better yet, reference specific upstream Security Groups (like an ALB SG). |
| **NAT Gateways in private subnets** | Assuming the NAT goes "with" the private instances it serves. | The NAT Gateway must sit in a **public** subnet so it has a route to the Internet Gateway. The private subnet route table points to the NAT Gateway. |
| **Forgetting ephemeral ports in NACLs** | Thinking stateless NACLs work like stateful Security Groups. | If you implement strict NACLs, always ensure you have rules allowing inbound return traffic on ports `1024-65535`. Without these, response packets are silently dropped. |
| **Using peering for full-mesh topologies** | It works fine for 3 VPCs, but becomes unmanageable at 15. | Transition to AWS Transit Gateway when connecting more than a handful of VPCs to simplify routing and management. |
| **Single-AZ NAT Gateway** | Deploying one NAT Gateway and routing all private subnets through it. | Deploy one NAT Gateway per AZ for production workloads. If the AZ hosting a single NAT Gateway fails, all private subnets lose internet access. |
| **Not enabling VPC Flow Logs** | "We will enable them when something goes wrong." | Enable Flow Logs from day one. You cannot retroactively capture traffic that already happened. When an incident occurs, you need the historical data. Send them to S3 for cost-effective long-term storage. |

---

## Quiz

<details>
<summary>Question 1: You launch an EC2 instance into a subnet, attach an Elastic IP (public IP), and ensure the Security Group allows inbound SSH (port 22). However, your SSH connection times out. What is the most likely architectural cause?</summary>

The subnet the EC2 instance resides in is a **Private Subnet**. Even though the instance has a public IP address, the Subnet's Route Table does not have a route to an Internet Gateway (IGW). Without a route to the IGW, internet traffic cannot enter or leave the subnet. The fix is to add a route `0.0.0.0/0 → igw-xxx` to the subnet's route table, or move the instance to a subnet that already has this route.
</details>

<details>
<summary>Question 2: An application in a private subnet needs to upload logs to Amazon S3. You want to accomplish this securely without the traffic traversing the public internet and without incurring NAT Gateway data processing charges. What should you configure?</summary>

You should configure a **VPC Gateway Endpoint** for Amazon S3. This creates a private connection from your VPC to the S3 service, keeping all traffic on the internal AWS network. Gateway endpoints are free and require a route table update, unlike Interface endpoints (PrivateLink) which use an ENI and incur hourly charges. The route table entry will look like: `pl-xxxxx (S3 prefix list) → vpce-xxx`.
</details>

<details>
<summary>Question 3: Your company's primary application is hosted entirely within a single Availability Zone (us-east-1a) when a massive power failure takes the data center offline. What architectural pattern would have prevented the resulting total application outage, and how does it work?</summary>

To prevent a total outage, you should design a **multi-AZ architecture** by spanning your VPC and deploying redundant resources across multiple Availability Zones. An Availability Zone represents one or more discrete data centers with redundant power, networking, and connectivity. If an entire AZ goes offline due to a massive infrastructure failure, resources deployed in the other AZs within the same VPC will continue to operate. This ensures the application remains highly available and fault-tolerant. Best practice dictates using at least two AZs, with three AZs recommended for production workloads.
</details>

<details>
<summary>Question 4: You have a private subnet with a NAT Gateway providing internet access. You check VPC Flow Logs and see traffic from your instance to an external API being ACCEPTED, but the application reports connection timeouts. What should you investigate?</summary>

The Flow Log `ACCEPT` means the **Security Group and NACL** allowed the traffic — but it does not mean the traffic actually reached the destination. First, verify the route tables to ensure the private subnet routes `0.0.0.0/0` to the NAT Gateway, and the public subnet routes it to the IGW. Second, check if the NAT Gateway is in the `available` state with an attached Elastic IP. Third, ensure the NACL on the private subnet explicitly allows inbound return traffic on ephemeral ports (1024-65535). Finally, verify if the external API is reachable and not blocking your NAT Gateway's Elastic IP.
</details>

<details>
<summary>Question 5: Your engineering team needs to connect private subnets to both Amazon S3 and AWS Systems Manager (SSM) without using the public internet. They are confused about which endpoint types to deploy to optimize for cost and compatibility. How should they choose between a VPC Gateway Endpoint and a VPC Interface Endpoint for these services?</summary>

The team should use a **Gateway Endpoint** for Amazon S3 and an **Interface Endpoint** for AWS Systems Manager. Gateway Endpoints are available exclusively for S3 and DynamoDB, adding a route directly to your route table without incurring any hourly or data charges. Interface Endpoints (PrivateLink) must be used for most other AWS services, including SSM, as they create an Elastic Network Interface (ENI) with a private IP in your subnet. Interface Endpoints cost approximately $0.01 per hour per AZ plus data processing charges, but they crucially support Security Groups and provide a resolvable DNS hostname. Using Gateway Endpoints whenever possible optimizes costs, while Interface Endpoints provide the necessary connectivity for the rest of the AWS ecosystem.
</details>

---

## Hands-On Exercise: Production-Grade VPC Architecture

In this exercise, you will use the AWS CLI to build a complete production-ready VPC: spanning three Availability Zones, with public subnets for load balancers, private subnets for application servers, NAT Gateways for outbound access, layered security groups, and a restrictive NACL.

**What you will build:**

```text
┌─────────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16 (Dojo-Prod-VPC)                              │
│                                                                 │
│  ┌─────────── AZ: us-east-1a ───────────┐                      │
│  │ Public:  10.0.1.0/24  [ALB, NAT-GW]  │                      │
│  │ Private: 10.0.10.0/24 [App Servers]   │                      │
│  └───────────────────────────────────────┘                      │
│                                                                 │
│  ┌─────────── AZ: us-east-1b ───────────┐                      │
│  │ Public:  10.0.2.0/24  [ALB, NAT-GW]  │                      │
│  │ Private: 10.0.20.0/24 [App Servers]   │                      │
│  └───────────────────────────────────────┘                      │
│                                                                 │
│  Security: ALB-SG → App-SG → DB-SG (chained)                   │
│  NACL: Block known-bad CIDR on private subnets                  │
│  Internet: IGW → Public Subnets → NAT-GW → Private Subnets     │
└─────────────────────────────────────────────────────────────────┘
```

### Task 1: Create the VPC and Enable DNS

First, establish the network boundary.

```bash
# 1. Create the VPC (10.0.0.0/16)
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' \
  --output text)

# 2. Name the VPC
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=Dojo-Prod-VPC

# 3. Enable DNS hostnames (required for VPC Endpoints and private DNS)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}'
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support '{"Value":true}'

# 4. Verify
aws ec2 describe-vpcs --vpc-ids $VPC_ID \
  --query 'Vpcs[0].{VpcId:VpcId, CIDR:CidrBlock, State:State}' \
  --output table
```

### Task 2: Create and Attach the Internet Gateway

```bash
# 1. Create the Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

# 2. Attach it to the VPC
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# 3. Tag it
aws ec2 create-tags --resources $IGW_ID --tags Key=Name,Value=Dojo-Prod-IGW

echo "IGW $IGW_ID attached to VPC $VPC_ID"
```

### Task 3: Create the Subnets Across Two AZs

We will create four subnets: two public and two private, spread across two Availability Zones.

```bash
# Define availability zones (adjust if your default region is different)
AZ1="us-east-1a"
AZ2="us-east-1b"

# --- Public Subnets ---

PUB_SUB1_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone $AZ1 \
  --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $PUB_SUB1_ID --tags Key=Name,Value=Public-Subnet-AZ1

PUB_SUB2_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone $AZ2 \
  --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $PUB_SUB2_ID --tags Key=Name,Value=Public-Subnet-AZ2

# --- Private Subnets ---

PRIV_SUB1_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.10.0/24 \
  --availability-zone $AZ1 \
  --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $PRIV_SUB1_ID --tags Key=Name,Value=Private-Subnet-AZ1

PRIV_SUB2_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.20.0/24 \
  --availability-zone $AZ2 \
  --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $PRIV_SUB2_ID --tags Key=Name,Value=Private-Subnet-AZ2

# Verify all subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[*].{SubnetId:SubnetId, AZ:AvailabilityZone, CIDR:CidrBlock, Name:Tags[?Key==`Name`].Value|[0]}' \
  --output table
```

### Task 4: Configure Public Routing

The main route table is private by default. We create a separate route table for the public subnets.

```bash
# 1. Create a Public Route Table
PUB_RT_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-tags --resources $PUB_RT_ID --tags Key=Name,Value=Public-Route-Table

# 2. Add a route to the Internet Gateway for all internet-bound traffic
aws ec2 create-route \
  --route-table-id $PUB_RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

# 3. Associate the Public Route Table with both Public Subnets
aws ec2 associate-route-table --subnet-id $PUB_SUB1_ID --route-table-id $PUB_RT_ID
aws ec2 associate-route-table --subnet-id $PUB_SUB2_ID --route-table-id $PUB_RT_ID

# 4. Enable auto-assign public IPs for the public subnets
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB1_ID --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB2_ID --map-public-ip-on-launch

# 5. Verify the route table
aws ec2 describe-route-tables --route-table-ids $PUB_RT_ID \
  --query 'RouteTables[0].Routes[*].{Destination:DestinationCidrBlock, Target:GatewayId||NatGatewayId}' \
  --output table
```

### Task 5: Configure NAT Gateways for Private Subnets

For production, deploy one NAT Gateway per AZ for high availability.

```bash
# 1. Allocate Elastic IPs for the NAT Gateways
EIP1_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
EIP2_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)

# 2. Create NAT Gateway in Public Subnet AZ1
NAT1_ID=$(aws ec2 create-nat-gateway \
  --subnet-id $PUB_SUB1_ID \
  --allocation-id $EIP1_ALLOC \
  --query 'NatGateway.NatGatewayId' --output text)
aws ec2 create-tags --resources $NAT1_ID --tags Key=Name,Value=NAT-GW-AZ1

# 3. Create NAT Gateway in Public Subnet AZ2
NAT2_ID=$(aws ec2 create-nat-gateway \
  --subnet-id $PUB_SUB2_ID \
  --allocation-id $EIP2_ALLOC \
  --query 'NatGateway.NatGatewayId' --output text)
aws ec2 create-tags --resources $NAT2_ID --tags Key=Name,Value=NAT-GW-AZ2

echo "Waiting for NAT Gateways to become available (~60 seconds)..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT1_ID $NAT2_ID
echo "NAT Gateways are ready."

# 4. Create Private Route Table for AZ1
PRIV_RT1_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-tags --resources $PRIV_RT1_ID --tags Key=Name,Value=Private-Route-Table-AZ1
aws ec2 create-route --route-table-id $PRIV_RT1_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT1_ID
aws ec2 associate-route-table --subnet-id $PRIV_SUB1_ID --route-table-id $PRIV_RT1_ID

# 5. Create Private Route Table for AZ2
PRIV_RT2_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-tags --resources $PRIV_RT2_ID --tags Key=Name,Value=Private-Route-Table-AZ2
aws ec2 create-route --route-table-id $PRIV_RT2_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT2_ID
aws ec2 associate-route-table --subnet-id $PRIV_SUB2_ID --route-table-id $PRIV_RT2_ID
```

> **Cost Warning**: NAT Gateways cost ~$0.045/hr each. Two NAT Gateways running 24/7 cost ~$65/month before data charges. Delete them when you finish this exercise!

### Task 6: Configure Layered Security Groups

Create a three-tier security group chain: ALB, Application, and Database.

```bash
# --- ALB Security Group (public-facing) ---
ALB_SG_ID=$(aws ec2 create-security-group \
  --group-name Dojo-ALB-SG \
  --description "Allow HTTP/HTTPS from internet" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 create-tags --resources $ALB_SG_ID --tags Key=Name,Value=Dojo-ALB-SG

# --- App Security Group (only accepts from ALB) ---
APP_SG_ID=$(aws ec2 create-security-group \
  --group-name Dojo-App-SG \
  --description "Allow port 8080 from ALB only" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $APP_SG_ID --protocol tcp --port 8080 --source-group $ALB_SG_ID
aws ec2 create-tags --resources $APP_SG_ID --tags Key=Name,Value=Dojo-App-SG

# --- DB Security Group (only accepts from App tier) ---
DB_SG_ID=$(aws ec2 create-security-group \
  --group-name Dojo-DB-SG \
  --description "Allow port 5432 from App only" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $DB_SG_ID --protocol tcp --port 5432 --source-group $APP_SG_ID
aws ec2 create-tags --resources $DB_SG_ID --tags Key=Name,Value=Dojo-DB-SG

# Verify the chain
echo "=== ALB SG ==="
aws ec2 describe-security-groups --group-ids $ALB_SG_ID \
  --query 'SecurityGroups[0].IpPermissions[*].{Port:FromPort, Source:IpRanges[0].CidrIp||UserIdGroupPairs[0].GroupId}' \
  --output table
echo "=== App SG ==="
aws ec2 describe-security-groups --group-ids $APP_SG_ID \
  --query 'SecurityGroups[0].IpPermissions[*].{Port:FromPort, Source:UserIdGroupPairs[0].GroupId}' \
  --output table
echo "=== DB SG ==="
aws ec2 describe-security-groups --group-ids $DB_SG_ID \
  --query 'SecurityGroups[0].IpPermissions[*].{Port:FromPort, Source:UserIdGroupPairs[0].GroupId}' \
  --output table
```

### Task 7: Create a Custom NACL for the Private Subnets

Add a NACL that blocks a known-bad IP range while allowing all other traffic.

```bash
# 1. Create a custom NACL
NACL_ID=$(aws ec2 create-network-acl \
  --vpc-id $VPC_ID \
  --query 'NetworkAcl.NetworkAclId' --output text)
aws ec2 create-tags --resources $NACL_ID --tags Key=Name,Value=Private-Subnet-NACL

# 2. Add Deny rule for a known-bad CIDR (evaluated first due to low rule number)
aws ec2 create-network-acl-entry --network-acl-id $NACL_ID \
  --rule-number 50 --protocol -1 --rule-action deny \
  --ingress --cidr-block 198.51.100.0/24

# 3. Add Allow rule for all other inbound traffic
aws ec2 create-network-acl-entry --network-acl-id $NACL_ID \
  --rule-number 100 --protocol -1 --rule-action allow \
  --ingress --cidr-block 0.0.0.0/0

# 4. Add Allow rule for all outbound traffic
aws ec2 create-network-acl-entry --network-acl-id $NACL_ID \
  --rule-number 100 --protocol -1 --rule-action allow \
  --egress --cidr-block 0.0.0.0/0

# 5. Associate with private subnets
aws ec2 replace-network-acl-association \
  --association-id $(aws ec2 describe-network-acls \
    --filters "Name=association.subnet-id,Values=$PRIV_SUB1_ID" \
    --query 'NetworkAcls[0].Associations[?SubnetId==`'$PRIV_SUB1_ID'`].NetworkAclAssociationId' \
    --output text) \
  --network-acl-id $NACL_ID

aws ec2 replace-network-acl-association \
  --association-id $(aws ec2 describe-network-acls \
    --filters "Name=association.subnet-id,Values=$PRIV_SUB2_ID" \
    --query 'NetworkAcls[0].Associations[?SubnetId==`'$PRIV_SUB2_ID'`].NetworkAclAssociationId' \
    --output text) \
  --network-acl-id $NACL_ID

echo "Custom NACL $NACL_ID associated with private subnets"
```

### Task 8: Enable VPC Flow Logs

```bash
# Create a CloudWatch Log Group for Flow Logs
aws logs create-log-group --log-group-name /vpc/dojo-prod-flow-logs

# Enable VPC Flow Logs (requires an IAM role with permissions -- see note below)
# In production, you would create an IAM role. For this exercise, we use S3 delivery:
FLOW_LOG_ID=$(aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $VPC_ID \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/dojo-prod-flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/VPCFlowLogRole \
  --query 'FlowLogIds[0]' --output text)

echo "Flow Logs enabled: $FLOW_LOG_ID"
```

> **Note**: The `create-flow-logs` command requires an IAM role that allows the VPC Flow Log service to publish to CloudWatch Logs. If you do not have this role set up, you can skip this task or deliver logs to an S3 bucket instead using `--log-destination-type s3 --log-destination arn:aws:s3:::your-bucket-name`.

### Clean Up

**Important**: Delete resources in reverse order of dependency to avoid errors. NAT Gateways take 1-2 minutes to delete.

```bash
# 1. Delete Flow Logs
aws ec2 delete-flow-logs --flow-log-ids $FLOW_LOG_ID
aws logs delete-log-group --log-group-name /vpc/dojo-prod-flow-logs

# 2. Delete NAT Gateways (they take ~60s to fully delete)
aws ec2 delete-nat-gateway --nat-gateway-id $NAT1_ID
aws ec2 delete-nat-gateway --nat-gateway-id $NAT2_ID
echo "Waiting for NAT Gateways to delete..."
sleep 60

# 3. Release Elastic IPs
aws ec2 release-address --allocation-id $EIP1_ALLOC
aws ec2 release-address --allocation-id $EIP2_ALLOC

# 4. Delete Security Groups (order does not matter since they reference each other by ID)
aws ec2 delete-security-group --group-id $DB_SG_ID
aws ec2 delete-security-group --group-id $APP_SG_ID
aws ec2 delete-security-group --group-id $ALB_SG_ID

# 5. Delete custom NACL (subnets revert to default NACL)
aws ec2 delete-network-acl --network-acl-id $NACL_ID

# 6. Delete routes from private route tables, then delete them
aws ec2 delete-route --route-table-id $PRIV_RT1_ID --destination-cidr-block 0.0.0.0/0
aws ec2 delete-route --route-table-id $PRIV_RT2_ID --destination-cidr-block 0.0.0.0/0
aws ec2 delete-route --route-table-id $PUB_RT_ID --destination-cidr-block 0.0.0.0/0

# 7. Delete subnets (this automatically disassociates route tables)
aws ec2 delete-subnet --subnet-id $PUB_SUB1_ID
aws ec2 delete-subnet --subnet-id $PUB_SUB2_ID
aws ec2 delete-subnet --subnet-id $PRIV_SUB1_ID
aws ec2 delete-subnet --subnet-id $PRIV_SUB2_ID

# 8. Delete route tables
aws ec2 delete-route-table --route-table-id $PUB_RT_ID
aws ec2 delete-route-table --route-table-id $PRIV_RT1_ID
aws ec2 delete-route-table --route-table-id $PRIV_RT2_ID

# 9. Detach and delete IGW, then VPC
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID
aws ec2 delete-vpc --vpc-id $VPC_ID

echo "All resources cleaned up."
```

### Success Criteria

- [ ] I created a VPC with a `/16` CIDR block and enabled DNS hostnames
- [ ] I carved the VPC into 4 subnets spread across 2 Availability Zones
- [ ] I created an Internet Gateway and a custom route table to make two subnets public
- [ ] I deployed NAT Gateways in each public subnet for HA outbound access from private subnets
- [ ] I created separate private route tables per AZ, each pointing to its own NAT Gateway
- [ ] I implemented a three-tier chained Security Group architecture (ALB -> App -> DB)
- [ ] I created a custom NACL that blocks a specific CIDR range on the private subnets
- [ ] I enabled VPC Flow Logs for traffic visibility
- [ ] I successfully cleaned up all resources to avoid ongoing charges

---

## Next Module

With the network foundation laid, it is time to deploy servers into those subnets. Head to [Module 1.3: EC2 & Compute](../module-1.3-ec2/).