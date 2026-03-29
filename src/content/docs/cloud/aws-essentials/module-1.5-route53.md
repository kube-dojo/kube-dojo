---
title: "Module 1.5: Route 53 & DNS Management"
slug: cloud/aws-essentials/module-1.5-route53
sidebar:
  order: 6
---
## Complexity: [MEDIUM]
## Time to Complete: 1.5 hours

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 1.2: VPC & Networking Foundations](../module-1.2-vpc/)
- Basic understanding of domain names and how browsers resolve URLs
- AWS account with at least one registered domain (or willingness to register one ~$12/year)
- AWS CLI configured with appropriate permissions

---

## Why This Module Matters

In October 2021, Facebook disappeared from the internet. Not figuratively -- literally. For six hours, the company's DNS records were unreachable because a routine BGP configuration change accidentally withdrew the routes to Facebook's DNS servers. The result: 3.5 billion users locked out, an estimated $100 million in lost revenue, and employees unable to enter their own buildings because badge systems depended on internal DNS. The stock dropped 4.9% that day.

DNS is the invisible foundation of every internet application. When it works, nobody thinks about it. When it fails, nothing else matters -- your beautifully architected microservices, your multi-region deployment, your zero-downtime release strategy -- all of it becomes unreachable if users cannot resolve your domain name.

AWS Route 53 is Amazon's managed DNS service, named after the port that DNS traffic runs on (port 53). It handles over a trillion DNS queries per month across AWS's global network of edge locations. In this module, you will learn how Route 53 works, how to configure hosted zones and records, how to implement sophisticated routing policies for multi-region architectures, and how to keep your DNS infrastructure healthy with automated health checks. By the end, you will have built a multi-region active-passive failover configuration -- the kind of setup that would have saved Facebook's engineers a very bad day.

---

## How DNS Actually Works

Before we touch Route 53, let us make sure the foundation is solid. DNS is often described as "the phone book of the internet," but that analogy undersells it. A better analogy: DNS is the postal system of the internet -- it translates human-friendly addresses (like `api.yourapp.com`) into machine-routable IP addresses (like `54.231.128.12`).

Here is what happens when a user types your domain into their browser:

```
                    User's Browser
                         |
                    [1] Query: api.yourapp.com?
                         |
                         v
                  Local DNS Resolver          <-- ISP or corporate resolver
                  (Recursive Resolver)             (e.g., 8.8.8.8)
                         |
           [2] Not in cache? Ask root servers
                         |
                         v
                   Root Name Servers          <-- 13 root server clusters worldwide
                   (., root zone)
                         |
           [3] "Try .com TLD servers"
                         |
                         v
                  TLD Name Servers            <-- Managed by Verisign for .com
                  (.com zone)
                         |
           [4] "Try ns-123.awsdns-45.com"
                         |
                         v
              Authoritative Name Server       <-- THIS IS ROUTE 53
              (yourapp.com zone)
                         |
           [5] "api.yourapp.com = 54.231.128.12"
                         |
                         v
                  Local DNS Resolver
                         |
           [6] Returns IP to browser (cached for TTL)
                         |
                         v
                    User's Browser
                    Connects to 54.231.128.12
```

Route 53 lives at step 4-5 in this chain. It is the **authoritative name server** for your domains. When any resolver in the world asks "where is api.yourapp.com?", Route 53 answers.

### DNS Record Types You Need to Know

| Record Type | Purpose | Example | When to Use |
|-------------|---------|---------|-------------|
| A | Maps name to IPv4 address | `api.example.com -> 54.231.128.12` | Direct IP mapping |
| AAAA | Maps name to IPv6 address | `api.example.com -> 2600:1f18:...` | IPv6 endpoints |
| CNAME | Maps name to another name | `www.example.com -> example.com` | Aliases (cannot be used at zone apex) |
| ALIAS | Route 53 extension of A/AAAA | `example.com -> d1234.cloudfront.net` | AWS resources at zone apex |
| MX | Mail exchange servers | `example.com -> mail.example.com (priority 10)` | Email routing |
| TXT | Arbitrary text | `example.com -> "v=spf1 include:_spf.google.com"` | SPF, DKIM, domain verification |
| NS | Name server delegation | `example.com -> ns-123.awsdns-45.com` | Zone delegation |
| SOA | Start of Authority | Zone metadata | Automatically managed by Route 53 |
| SRV | Service locator | `_sip._tcp.example.com -> sip.example.com:5060` | Service discovery |
| CAA | Certificate Authority Authorization | `example.com -> 0 issue "letsencrypt.org"` | Restrict who can issue TLS certs |

The **ALIAS record** deserves special attention. Standard DNS does not allow a CNAME at the zone apex (the naked domain like `example.com`). But you often want your naked domain pointing to a load balancer or CloudFront distribution. Route 53's ALIAS record solves this -- it functions like a CNAME but returns an A/AAAA record, so it works at the zone apex. And queries against ALIAS records pointing to AWS resources are free.

---

## Hosted Zones: Public and Private

A **hosted zone** is a container for DNS records for a single domain. Think of it as a DNS configuration file for one domain and its subdomains.

### Public Hosted Zones

Public hosted zones answer DNS queries from the entire internet. When you register a domain or transfer DNS management to Route 53, you create a public hosted zone.

```bash
# Create a public hosted zone
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference "$(date +%s)" \
  --hosted-zone-config Comment="Production domain"

# List all hosted zones
aws route53 list-hosted-zones

# Get details of a specific zone (replace with your zone ID)
aws route53 get-hosted-zone --id Z0123456789ABCDEFGHIJ
```

When Route 53 creates a public hosted zone, it automatically assigns four name servers from different TLD domains (e.g., `ns-123.awsdns-45.com`, `ns-456.awsdns-78.net`, `ns-789.awsdns-12.org`, `ns-1012.awsdns-34.co.uk`). This four-TLD spread ensures that even if one TLD's infrastructure has issues, your DNS still works.

### Private Hosted Zones

Private hosted zones answer queries only from within one or more associated VPCs. They are essential for internal service discovery -- giving friendly names to internal resources without exposing them to the internet.

```bash
# Create a private hosted zone associated with a VPC
aws route53 create-hosted-zone \
  --name internal.yourcompany.com \
  --caller-reference "$(date +%s)" \
  --vpc VPCRegion=us-east-1,VPCId=vpc-0abc123def456 \
  --hosted-zone-config Comment="Internal services",PrivateZone=true

# Associate additional VPCs with the private hosted zone
aws route53 associate-vpc-with-hosted-zone \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --vpc VPCRegion=us-west-2,VPCId=vpc-0xyz789ghi012
```

A common pattern is split-horizon DNS: the same domain name resolves to different IPs depending on whether the query comes from inside or outside your VPC. For example, `api.yourapp.com` might resolve to a public ALB IP for external users, but to a private IP for services running inside the VPC. This reduces latency and avoids unnecessary trips through the internet gateway.

```
Split-Horizon DNS Architecture:

External User                          Internal Service (in VPC)
     |                                       |
     | Query: api.yourapp.com                | Query: api.yourapp.com
     v                                       v
 Public Hosted Zone                    Private Hosted Zone
 api.yourapp.com -> 54.231.128.12      api.yourapp.com -> 10.0.1.50
 (Public ALB IP)                       (Private ALB IP)
     |                                       |
     v                                       v
 Traffic goes through Internet          Traffic stays inside VPC
 -> ALB -> Target Group                 -> Internal ALB -> Target Group
```

### Hosted Zone Costs

Route 53 pricing is straightforward but can surprise you at scale:

| Component | Cost |
|-----------|------|
| Hosted zone | $0.50/month per zone (first 25 zones) |
| Standard queries | $0.40 per million queries |
| Latency-based routing queries | $0.60 per million queries |
| ALIAS queries to AWS resources | Free |
| Health checks | $0.50/month (basic), $0.75/month (HTTPS + string matching) |
| Domain registration | $12-40/year depending on TLD |

That ALIAS-queries-are-free detail matters. If you can use an ALIAS record instead of a CNAME, you save on query costs and get zone-apex support. Always prefer ALIAS for AWS resources.

---

## Creating and Managing DNS Records

Let us create some records. Route 53 uses a change-batch system where you submit JSON describing the changes you want.

### Basic Record Creation

```bash
# Create an A record pointing to an EC2 instance
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "app.example.com",
          "Type": "A",
          "TTL": 300,
          "ResourceRecords": [
            {"Value": "54.231.128.12"}
          ]
        }
      }
    ]
  }'

# Create an ALIAS record pointing to an ALB
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "example.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z35SXDOTRQ7X7K",
            "DNSName": "my-alb-123456789.us-east-1.elb.amazonaws.com",
            "EvaluateTargetHealth": true
          }
        }
      }
    ]
  }'
```

Notice the `UPSERT` action in the second example. This is idempotent -- it creates the record if it does not exist, or updates it if it does. Production automation should always prefer `UPSERT` over `CREATE` to avoid failures when re-running scripts.

### TTL: The Caching Knob You Must Understand

TTL (Time to Live) controls how long resolvers cache your DNS records, in seconds. It is one of the most misunderstood settings in DNS:

| TTL Value | Use Case | Trade-off |
|-----------|----------|-----------|
| 60 seconds | Active failover, during migrations | High query volume, higher cost |
| 300 seconds (5 min) | Standard production records | Good balance for most apps |
| 3600 seconds (1 hour) | Stable records (MX, TXT) | Lower cost, slower changes |
| 86400 seconds (24 hours) | Records that never change | Lowest cost, very slow propagation |

A critical lesson: **lower your TTL before making changes.** If your TTL is 24 hours and you need to migrate to a new IP, some resolvers will not see the change for a full day. The standard playbook:

1. 48 hours before change: Lower TTL to 60 seconds
2. Wait for old TTL to expire (24 hours)
3. Make the IP change
4. Verify the change has propagated
5. Raise TTL back to the normal value

```bash
# Step 1: Lower TTL before migration
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "54.231.128.12"}]
      }
    }]
  }'

# Step 2 (after old TTL expires): Change the IP
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "52.86.200.34"}]
      }
    }]
  }'
```

---

## Routing Policies

This is where Route 53 goes from "managed DNS" to "intelligent traffic management." Routing policies determine how Route 53 responds to queries, enabling everything from simple round-robin to sophisticated multi-region failover.

### Simple Routing

One record, one or more values. If multiple values exist, Route 53 returns all of them in random order and the client picks one.

```bash
# Simple routing: single value
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {"Value": "54.231.128.12"},
          {"Value": "54.231.128.13"},
          {"Value": "54.231.128.14"}
        ]
      }
    }]
  }'
```

### Weighted Routing

Distribute traffic across resources in proportions you control. Ideal for blue-green deployments, A/B testing, and gradual migrations.

```bash
# 90% of traffic to production, 10% to canary
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "app.example.com",
          "Type": "A",
          "SetIdentifier": "production",
          "Weight": 90,
          "TTL": 60,
          "ResourceRecords": [{"Value": "54.231.128.12"}]
        }
      },
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "app.example.com",
          "Type": "A",
          "SetIdentifier": "canary",
          "Weight": 10,
          "TTL": 60,
          "ResourceRecords": [{"Value": "52.86.200.34"}]
        }
      }
    ]
  }'
```

A weight of 0 means the record is never returned unless all other records also have weight 0. This is useful for "dark launching" -- creating a record you can activate later by changing its weight.

### Latency-Based Routing

Route 53 routes traffic to the region with the lowest latency for the requester. AWS maintains a database of latency measurements between internet networks and AWS regions.

```bash
# Latency-based: US East endpoint
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "us-east-1",
        "Region": "us-east-1",
        "TTL": 60,
        "ResourceRecords": [{"Value": "54.231.128.12"}]
      }
    }]
  }'

# Latency-based: EU West endpoint
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "eu-west-1",
        "Region": "eu-west-1",
        "TTL": 60,
        "ResourceRecords": [{"Value": "52.17.200.45"}]
      }
    }]
  }'
```

Users in New York get routed to `us-east-1`. Users in London get `eu-west-1`. Users in Tokyo might get either, depending on which has lower measured latency from their ISP.

### Failover Routing

Active-passive failover. Route 53 returns the primary record unless its health check fails, then switches to secondary.

```bash
# Primary record with health check
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "SetIdentifier": "primary",
        "Failover": "PRIMARY",
        "TTL": 60,
        "HealthCheckId": "abcdef12-3456-7890-abcd-ef1234567890",
        "ResourceRecords": [{"Value": "54.231.128.12"}]
      }
    }]
  }'

# Secondary record (failover target)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "SetIdentifier": "secondary",
        "Failover": "SECONDARY",
        "TTL": 60,
        "ResourceRecords": [{"Value": "52.86.200.34"}]
      }
    }]
  }'
```

### Routing Policy Decision Matrix

```
Which routing policy should I use?

[Do you need failover?]
    |-- YES --> [Active-Active or Active-Passive?]
    |               |-- Active-Passive --> FAILOVER routing
    |               |-- Active-Active  --> LATENCY routing + health checks
    |
    |-- NO --> [Do you need geographic control?]
                   |-- YES --> [Compliance/data residency?]
                   |               |-- YES --> GEOLOCATION routing
                   |               |-- NO  --> LATENCY routing
                   |
                   |-- NO --> [Do you need traffic splitting?]
                                  |-- YES --> WEIGHTED routing
                                  |-- NO  --> SIMPLE routing
```

---

## Health Checks

Health checks are what make routing policies intelligent. Without them, Route 53 will happily send traffic to dead endpoints.

### Creating Health Checks

```bash
# HTTP health check against an endpoint
aws route53 create-health-check \
  --caller-reference "app-health-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTP",
    "FullyQualifiedDomainName": "app.example.com",
    "Port": 80,
    "ResourcePath": "/health",
    "RequestInterval": 30,
    "FailureThreshold": 3
  }'

# HTTPS health check with string matching
aws route53 create-health-check \
  --caller-reference "api-health-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTPS_STR_MATCH",
    "FullyQualifiedDomainName": "api.example.com",
    "Port": 443,
    "ResourcePath": "/health",
    "SearchString": "\"status\":\"healthy\"",
    "RequestInterval": 10,
    "FailureThreshold": 2
  }'

# Calculated health check (combines multiple checks)
aws route53 create-health-check \
  --caller-reference "combined-health-$(date +%s)" \
  --health-check-config '{
    "Type": "CALCULATED",
    "ChildHealthChecks": [
      "abcdef12-3456-7890-abcd-ef1234567890",
      "12345678-abcd-ef12-3456-7890abcdef12"
    ],
    "HealthThreshold": 1
  }'
```

### How Health Checks Work

Route 53 health checkers run from data centers in multiple AWS regions. By default, they check your endpoint every 30 seconds from about 15 locations worldwide. The endpoint is considered healthy if at least 18% of health checkers (roughly 3 out of 15) report it as healthy.

```
Route 53 Health Check Architecture:

  Health Checkers (15+ global locations)

  [US-East] ----> /health --> 200 OK    = Healthy
  [US-West] ----> /health --> 200 OK    = Healthy
  [EU-West] ----> /health --> 200 OK    = Healthy
  [AP-South] ---> /health --> 503 Error  = Unhealthy
  [SA-East] ----> /health --> 200 OK    = Healthy
  ...

  Result: 4/5 healthy (80%) > 18% threshold = ENDPOINT HEALTHY

  When checkers report unhealthy:
  - If < 18% report healthy --> Route 53 marks endpoint UNHEALTHY
  - Failover routing activates secondary record
  - Weighted/latency routing removes endpoint from responses
  - CloudWatch alarm triggers (if configured)
```

### Health Check Types

| Type | What It Checks | Best For |
|------|---------------|----------|
| HTTP/HTTPS | Endpoint returns 2xx/3xx | Web applications |
| HTTP_STR_MATCH / HTTPS_STR_MATCH | Response body contains a string | APIs returning JSON status |
| TCP | TCP connection succeeds | Databases, non-HTTP services |
| CALCULATED | Aggregates child health checks | Complex multi-component systems |
| CLOUDWATCH_METRIC | Based on CloudWatch alarm state | Internal resources not reachable from internet |

The `CLOUDWATCH_METRIC` type is crucial for private resources. Health checkers run from the public internet and cannot reach resources inside your VPC. For those, you create a CloudWatch alarm that monitors the resource, then create a health check that watches that alarm.

---

## DNSSEC: Signing Your Zone

DNSSEC (Domain Name System Security Extensions) protects against DNS spoofing by cryptographically signing records. Without DNSSEC, an attacker performing a man-in-the-middle attack could return false DNS records, redirecting your users to malicious servers.

Route 53 supports DNSSEC for public hosted zones. Enabling it involves creating a Key Signing Key (KSK) backed by AWS KMS:

```bash
# Step 1: Create a KMS key for DNSSEC (must be in us-east-1)
aws kms create-key \
  --region us-east-1 \
  --description "DNSSEC KSK for example.com" \
  --key-usage SIGN_VERIFY \
  --key-spec ECC_NIST_P256 \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "Allow Route 53 DNSSEC",
        "Effect": "Allow",
        "Principal": {"Service": "dnssec-route53.amazonaws.com"},
        "Action": ["kms:DescribeKey", "kms:GetPublicKey", "kms:Sign"],
        "Resource": "*"
      },
      {
        "Sid": "Allow key administration",
        "Effect": "Allow",
        "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
        "Action": "kms:*",
        "Resource": "*"
      }
    ]
  }'

# Step 2: Enable DNSSEC signing
aws route53 create-key-signing-key \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --name example-com-ksk \
  --key-management-service-arn arn:aws:kms:us-east-1:123456789012:key/abcd1234-ef56-7890-abcd-ef1234567890 \
  --status ACTIVE

# Step 3: Enable DNSSEC for the zone
aws route53 enable-hosted-zone-dnssec \
  --hosted-zone-id Z0123456789ABCDEFGHIJ
```

After enabling DNSSEC, you must establish a chain of trust by adding a DS (Delegation Signer) record to the parent zone (your domain registrar). If your domain is registered with Route 53, this is straightforward. If it is registered elsewhere, you will need to add the DS record manually through your registrar's interface.

A warning: enabling DNSSEC is easy, but getting it wrong can make your domain unreachable. Always test with a staging domain first.

---

## Did You Know?

1. **Route 53 has a 100% uptime SLA** -- one of the very few AWS services with this guarantee. It achieves this through a global anycast network of over 200 edge locations. AWS has never had a complete Route 53 outage since its launch in December 2010, making it one of the most reliable services in all of cloud computing.

2. **The name "Route 53" is a double reference.** Obviously, DNS runs on port 53. But it is also a nod to US Route 66, the famous American highway -- connecting the concept of "routing" traffic across the internet to routing cars across the country. AWS engineers love their naming easter eggs.

3. **Route 53 processes over 1 trillion DNS queries per month**, making it one of the largest authoritative DNS systems on Earth. Despite this scale, the median query response time is under 1 millisecond from the nearest edge location. For comparison, blinking your eye takes about 300 milliseconds.

4. **ALIAS records were invented by AWS** because standard DNS could not solve the zone-apex CNAME problem. The IETF later formalized a similar concept as the ANAME record type in RFC drafts, but as of 2026, ALIAS remains an AWS-specific extension. Other providers have their own variants: Cloudflare calls theirs "CNAME flattening" and Google Cloud DNS uses "routing records."

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Forgetting to lower TTL before migrations | TTL is set-and-forget for most teams | Create a migration runbook that starts with TTL reduction 48 hours before any DNS change |
| Using CNAME at zone apex | CNAME seems like the right record type for aliasing | Use Route 53 ALIAS records for zone apex. They function like CNAMEs but return A/AAAA records |
| No health checks on failover records | Health checks cost extra and seem optional | Failover routing without health checks is pointless -- Route 53 will never trigger failover. Always attach health checks to primary records |
| Health check endpoint behind security group | Health checkers come from AWS public IPs that are blocked | Add Route 53 health checker IP ranges to your security group. AWS publishes these in their ip-ranges.json |
| DNSSEC enabled without DS record at registrar | You enable signing but forget the chain of trust | Incomplete DNSSEC is worse than no DNSSEC -- DNSSEC-validating resolvers will refuse to resolve your domain. Always complete the DS record step |
| Private hosted zone not associated with VPC | Zone created but queries return NXDOMAIN | Associate the private hosted zone with every VPC that needs to resolve those records |
| Using Route 53 for internal service discovery without considering alternatives | It is the obvious choice for DNS | For Kubernetes workloads, CoreDNS handles internal resolution natively. Route 53 private zones are better for cross-VPC or hybrid-cloud discovery |
| Setting all weights to 0 in weighted routing | Trying to disable traffic to all endpoints | When all weights are 0, Route 53 returns all records equally. To truly stop traffic, delete the records or use a health check |

---

## Quiz

<details>
<summary>1. What is the key difference between a CNAME record and a Route 53 ALIAS record?</summary>

A CNAME record creates an alias from one domain name to another, but it cannot be used at the zone apex (e.g., `example.com` without a subdomain). This is a fundamental DNS protocol limitation, not a Route 53 restriction. An ALIAS record is a Route 53 extension that functions similarly to a CNAME but returns an A or AAAA record in the response. This means it works at the zone apex and, when pointing to AWS resources, the queries are free. Use ALIAS whenever you are pointing to AWS services like ALB, CloudFront, or S3 website endpoints.
</details>

<details>
<summary>2. You have a latency-based routing configuration with endpoints in us-east-1 and eu-west-1. A user in Brazil resolves your domain. Which endpoint do they get?</summary>

They get whichever endpoint has lower measured latency from their network location. Route 53 maintains a latency database based on measurements from various internet networks to AWS regions. For a user in Brazil (Sao Paulo area), us-east-1 (Virginia) is typically closer than eu-west-1 (Ireland) in terms of network latency, so they would most likely be routed to the US East endpoint. However, this is not guaranteed -- if the user's ISP has better peering with European networks, they could be routed to eu-west-1. Latency-based routing uses actual network measurements, not geographic distance.
</details>

<details>
<summary>3. Your health check shows an endpoint as healthy, but users report the application is returning errors. What could be wrong?</summary>

The most common cause is that the health check endpoint (`/health`) returns 200 OK even when the application is degraded. A basic HTTP health check only verifies that the server responds with a 2xx or 3xx status code -- it does not check application logic. To fix this, use an HTTPS_STR_MATCH health check that validates the response body contains a specific string (e.g., `"status":"healthy"`). Your health endpoint should perform meaningful checks -- database connectivity, cache availability, downstream service reachability -- and return an error status when any critical dependency is down.
</details>

<details>
<summary>4. Why must DNSSEC KMS keys be created in us-east-1, even if your hosted zone serves a global audience?</summary>

Route 53 is a global service, but its DNSSEC signing infrastructure operates from us-east-1. The KMS key used for the Key Signing Key (KSK) must be accessible from Route 53's signing operations, which are centralized in that region. This is an AWS architectural decision, not a DNS protocol requirement. The signed records are then distributed globally through Route 53's anycast network. This does not affect performance for end users because the signing happens when records are updated, not when queries are resolved.
</details>

<details>
<summary>5. You configure weighted routing with three records: A (weight 70), B (weight 20), and C (weight 10). What percentage of DNS queries return record B?</summary>

Record B receives 20% of queries. Route 53 calculates the probability as: weight of the record divided by the sum of all weights. In this case: 20 / (70 + 20 + 10) = 20 / 100 = 20%. The weights do not need to sum to 100 -- they are ratios. You could achieve the same distribution with weights 7, 2, and 1. Route 53 evaluates these weights on every query, so the distribution is statistical over time, not deterministic for individual requests.
</details>

<details>
<summary>6. How does Route 53 handle health checks for resources inside a private VPC that are not reachable from the internet?</summary>

Route 53 health checkers operate from public internet locations, so they cannot directly reach private VPC resources. The solution is to use a CLOUDWATCH_METRIC health check. You configure a CloudWatch alarm that monitors the internal resource (e.g., CPU utilization on an RDS instance, or a custom metric from a Lambda function performing internal checks). Then you create a Route 53 health check of type CLOUDWATCH_METRIC that watches the state of that alarm. When the alarm enters ALARM state, Route 53 marks the endpoint as unhealthy. This bridges the gap between Route 53's public health checking and your private infrastructure.
</details>

<details>
<summary>7. Your failover configuration has a primary record in us-east-1 and a secondary in us-west-2. The primary health check fails. How quickly will traffic shift to the secondary?</summary>

The failover timing depends on several factors. With default health check settings (30-second intervals, failure threshold of 3), it takes about 90 seconds for health checkers to declare the endpoint unhealthy. Then Route 53 updates the DNS response almost immediately. However, DNS resolvers may have cached the old (primary) record for up to the TTL duration. If your TTL is 60 seconds, total failover time is roughly 90 seconds (health check) + up to 60 seconds (TTL expiration) = approximately 2.5 minutes. To minimize this, use a 10-second request interval (costs more) and a low TTL like 30-60 seconds on your failover records.
</details>

---

## Hands-On Exercise: Multi-Region Active-Passive Failover

In this exercise, you will build a production-grade DNS failover configuration. We will simulate two regional endpoints and configure Route 53 to automatically fail over when the primary becomes unhealthy.

### Setup

You will need an AWS account and a registered domain (or a hosted zone you can experiment with). We will use placeholder values that you should replace with your actual resources.

```bash
# Set your variables
export DOMAIN="example.com"
export HOSTED_ZONE_ID="Z0123456789ABCDEFGHIJ"
export PRIMARY_IP="54.231.128.12"    # Replace with your us-east-1 resource IP
export SECONDARY_IP="52.86.200.34"   # Replace with your us-west-2 resource IP
```

### Task 1: Create Health Checks for Both Regions

Create HTTP health checks for the primary and secondary endpoints.

<details>
<summary>Solution</summary>

```bash
# Create health check for primary (us-east-1)
PRIMARY_HC=$(aws route53 create-health-check \
  --caller-reference "primary-hc-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTP",
    "IPAddress": "'"${PRIMARY_IP}"'",
    "Port": 80,
    "ResourcePath": "/health",
    "RequestInterval": 10,
    "FailureThreshold": 2
  }' \
  --query 'HealthCheck.Id' --output text)

echo "Primary health check ID: ${PRIMARY_HC}"

# Create health check for secondary (us-west-2)
SECONDARY_HC=$(aws route53 create-health-check \
  --caller-reference "secondary-hc-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTP",
    "IPAddress": "'"${SECONDARY_IP}"'",
    "Port": 80,
    "ResourcePath": "/health",
    "RequestInterval": 10,
    "FailureThreshold": 2
  }' \
  --query 'HealthCheck.Id' --output text)

echo "Secondary health check ID: ${SECONDARY_HC}"
```
</details>

### Task 2: Configure Failover Routing Records

Create the primary and secondary failover records, associating each with its health check.

<details>
<summary>Solution</summary>

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id ${HOSTED_ZONE_ID} \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "failover-demo.'"${DOMAIN}"'",
          "Type": "A",
          "SetIdentifier": "primary-us-east-1",
          "Failover": "PRIMARY",
          "TTL": 60,
          "HealthCheckId": "'"${PRIMARY_HC}"'",
          "ResourceRecords": [{"Value": "'"${PRIMARY_IP}"'"}]
        }
      },
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "failover-demo.'"${DOMAIN}"'",
          "Type": "A",
          "SetIdentifier": "secondary-us-west-2",
          "Failover": "SECONDARY",
          "TTL": 60,
          "HealthCheckId": "'"${SECONDARY_HC}"'",
          "ResourceRecords": [{"Value": "'"${SECONDARY_IP}"'"}]
        }
      }
    ]
  }'
```
</details>

### Task 3: Verify the Configuration

Query your DNS record and confirm it resolves to the primary IP.

<details>
<summary>Solution</summary>

```bash
# Query the record using dig
dig failover-demo.${DOMAIN} +short

# Expected output: primary IP (54.231.128.12)

# Test with Route 53's built-in DNS test
aws route53 test-dns-answer \
  --hosted-zone-id ${HOSTED_ZONE_ID} \
  --record-name failover-demo.${DOMAIN} \
  --record-type A

# Verify health check status
aws route53 get-health-check-status --health-check-id ${PRIMARY_HC}
aws route53 get-health-check-status --health-check-id ${SECONDARY_HC}
```
</details>

### Task 4: Simulate a Failover

Stop the primary endpoint's health check path and observe Route 53 failing over. Since you may not have actual servers, you can update the health check to point to an unreachable IP.

<details>
<summary>Solution</summary>

```bash
# Simulate primary failure by updating health check to an unreachable IP
aws route53 update-health-check \
  --health-check-id ${PRIMARY_HC} \
  --ip-address 192.0.2.1  # TEST-NET address, guaranteed unreachable

# Wait for health check to fail (about 30 seconds with 10s interval + threshold of 2)
echo "Waiting 45 seconds for health check to fail..."
sleep 45

# Check health status
aws route53 get-health-check-status --health-check-id ${PRIMARY_HC}

# Query DNS again -- should now return secondary IP
dig failover-demo.${DOMAIN} +short

# Expected output: secondary IP (52.86.200.34)
```
</details>

### Task 5: Add CloudWatch Alarm for Health Check Monitoring

Create a CloudWatch alarm that notifies you when a failover occurs.

<details>
<summary>Solution</summary>

```bash
# Create an SNS topic for alerts
TOPIC_ARN=$(aws sns create-topic --name dns-failover-alerts \
  --query 'TopicArn' --output text)

# Subscribe your email
aws sns subscribe \
  --topic-arn ${TOPIC_ARN} \
  --protocol email \
  --notification-endpoint your-email@example.com

# Create CloudWatch alarm on the primary health check
aws cloudwatch put-metric-alarm \
  --alarm-name "Route53-Primary-Unhealthy" \
  --alarm-description "Primary endpoint health check failed - failover active" \
  --namespace "AWS/Route53" \
  --metric-name "HealthCheckStatus" \
  --dimensions Name=HealthCheckId,Value=${PRIMARY_HC} \
  --statistic Minimum \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --alarm-actions ${TOPIC_ARN}
```
</details>

### Task 6: Clean Up

Remove all the resources you created to avoid ongoing costs.

<details>
<summary>Solution</summary>

```bash
# Delete the DNS records
aws route53 change-resource-record-sets \
  --hosted-zone-id ${HOSTED_ZONE_ID} \
  --change-batch '{
    "Changes": [
      {
        "Action": "DELETE",
        "ResourceRecordSet": {
          "Name": "failover-demo.'"${DOMAIN}"'",
          "Type": "A",
          "SetIdentifier": "primary-us-east-1",
          "Failover": "PRIMARY",
          "TTL": 60,
          "HealthCheckId": "'"${PRIMARY_HC}"'",
          "ResourceRecords": [{"Value": "'"${PRIMARY_IP}"'"}]
        }
      },
      {
        "Action": "DELETE",
        "ResourceRecordSet": {
          "Name": "failover-demo.'"${DOMAIN}"'",
          "Type": "A",
          "SetIdentifier": "secondary-us-west-2",
          "Failover": "SECONDARY",
          "TTL": 60,
          "HealthCheckId": "'"${SECONDARY_HC}"'",
          "ResourceRecords": [{"Value": "'"${SECONDARY_IP}"'"}]
        }
      }
    ]
  }'

# Delete health checks
aws route53 delete-health-check --health-check-id ${PRIMARY_HC}
aws route53 delete-health-check --health-check-id ${SECONDARY_HC}

# Delete CloudWatch alarm
aws cloudwatch delete-alarms --alarm-names "Route53-Primary-Unhealthy"

# Delete SNS topic
aws sns delete-topic --topic-arn ${TOPIC_ARN}
```
</details>

### Success Criteria

- [ ] Two health checks created (primary and secondary)
- [ ] Failover routing records created and pointing to correct IPs
- [ ] DNS resolves to primary IP when primary is healthy
- [ ] DNS resolves to secondary IP when primary health check fails
- [ ] CloudWatch alarm configured to alert on failover events
- [ ] All resources cleaned up after exercise

---

## Next Module

Next up: **[Module 1.6: Elastic Container Registry (ECR)](../module-1.6-ecr/)** -- Learn to store, manage, and secure your container images with AWS's native registry. You will set up lifecycle policies, vulnerability scanning, and cross-account sharing -- essential foundations before deploying containers to ECS or EKS.
