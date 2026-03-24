# GCP Compute Engine
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: Module 2 (VPC Networking)

## Why This Module Matters

In December 2022, a fast-growing e-commerce company ran their annual holiday sale on Google Cloud. Their architecture was simple: a fleet of Compute Engine VMs behind an HTTP(S) load balancer, with a Cloud SQL database in the backend. At 9:01 AM on Black Friday, traffic spiked to 15x normal levels. The operations team had provisioned what they thought was enough capacity---24 VMs running `n1-standard-8` instances. Within minutes, all 24 VMs were at 100% CPU. The team scrambled to manually add more VMs, but each new VM took 3-4 minutes to boot, install dependencies, and register with the load balancer. By the time they had scaled to 60 VMs, they had lost an estimated $1.8 million in abandoned carts. The post-incident review revealed two failures: first, they were using individual VMs instead of Managed Instance Groups with autoscaling. Second, they were using an older machine family (`n1`) when the `n2` family offered 20% better price-performance. The CEO's summary was blunt: "We paid more for machines that were slower, and we could not scale them automatically."

This incident captures why Compute Engine is more than "just VMs." Choosing the right machine family, configuring instance templates, using Managed Instance Groups with autoscaling, and setting up global load balancing are the difference between an architecture that handles traffic spikes gracefully and one that collapses under load. Compute Engine is the foundational compute service in GCP---even GKE nodes, Cloud SQL instances, and Dataflow workers run on Compute Engine VMs under the hood.

In this module, you will learn how to select the right machine family for your workload, leverage preemptible and Spot VMs for massive cost savings, build golden images with custom images, configure Managed Instance Groups for automatic scaling and self-healing, and tie everything together with Cloud Load Balancing.

---

## Machine Families: Choosing the Right Hardware

GCP offers four machine families, each optimized for different workload characteristics. Selecting the wrong family is one of the most common ways to overspend.

### The Four Families

```text
  ┌───────────────────────────────────────────────────────────┐
  │                    Machine Families                         │
  │                                                             │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
  │  │  General      │  │  Compute     │  │  Memory      │     │
  │  │  Purpose      │  │  Optimized   │  │  Optimized   │     │
  │  │              │  │              │  │              │     │
  │  │  E2, N2, N2D │  │  C2, C2D,   │  │  M2, M3     │     │
  │  │  T2D, N1     │  │  C3, H3     │  │              │     │
  │  │              │  │              │  │              │     │
  │  │  Web servers  │  │  HPC, gaming │  │  SAP HANA,   │     │
  │  │  Dev/test     │  │  batch jobs  │  │  in-memory   │     │
  │  │  microservices│  │  scientific  │  │  databases   │     │
  │  │              │  │  simulations │  │              │     │
  │  └──────────────┘  └──────────────┘  └──────────────┘     │
  │                                                             │
  │  ┌──────────────┐                                          │
  │  │  Accelerator  │                                          │
  │  │  Optimized   │                                          │
  │  │              │                                          │
  │  │  A2, A3, G2  │                                          │
  │  │              │                                          │
  │  │  ML training  │                                          │
  │  │  inference    │                                          │
  │  │  video trans- │                                          │
  │  │  coding       │                                          │
  │  └──────────────┘                                          │
  └───────────────────────────────────────────────────────────┘
```

### General Purpose: The Workhorse

| Series | CPU | vCPU:Memory Ratio | Best For | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **E2** | Intel/AMD (automatic) | 1:4 (0.5 to 32 vCPUs) | Cost-sensitive, dev/test | Cheapest, shared-core options available |
| **N2** | Intel Cascade Lake/Ice Lake | 1:4 (2 to 128 vCPUs) | General production | Good balance, sustained use discounts |
| **N2D** | AMD EPYC | 1:4 (2 to 224 vCPUs) | Same as N2, prefer AMD | Often 10-15% cheaper than N2 |
| **T2D** | AMD EPYC | 1:4 (1 to 60 vCPUs) | Scale-out workloads | Best per-thread performance |
| **N1** | Intel Skylake/older | 1:3.75 | Legacy (avoid for new) | Still supported but outdated |

```bash
# Create a general-purpose VM
gcloud compute instances create web-server \
  --machine-type=e2-medium \
  --zone=us-central1-a \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-balanced

# List available machine types in a zone
gcloud compute machine-types list \
  --zones=us-central1-a \
  --filter="name~'^e2'" \
  --format="table(name, guestCpus, memoryMb)"
```

### Custom Machine Types

If predefined machine types do not fit your workload, GCP allows you to specify exact vCPU and memory combinations.

```bash
# Custom machine type: 6 vCPUs, 24GB RAM
gcloud compute instances create custom-vm \
  --custom-cpu=6 \
  --custom-memory=24GB \
  --zone=us-central1-a \
  --image-family=debian-12 \
  --image-project=debian-cloud

# Custom with extended memory (more than 8GB per vCPU)
gcloud compute instances create high-mem-vm \
  --custom-cpu=4 \
  --custom-memory=64GB \
  --custom-vm-type=n2 \
  --custom-extensions \
  --zone=us-central1-a \
  --image-family=debian-12 \
  --image-project=debian-cloud
```

Rules for custom machine types:
- vCPUs must be 1, or an even number between 2 and 224 (varies by series).
- Memory must be between 0.9 GB and 8 GB per vCPU (or up to 24 GB per vCPU with extended memory).
- Extended memory costs more per GB than standard memory.

### Shared-Core Machines

For lightweight workloads that do not need a full vCPU, E2 offers shared-core options:

| Type | vCPUs | Memory | Use Case | Cost (approx vs e2-medium) |
| :--- | :--- | :--- | :--- | :--- |
| `e2-micro` | 0.25 shared | 1 GB | Micro-services, tiny APIs | ~25% of e2-medium |
| `e2-small` | 0.5 shared | 2 GB | Low-traffic web, dev | ~50% of e2-medium |
| `e2-medium` | 1 shared | 4 GB | Moderate web, Jenkins agents | Baseline |

---

## Preemptible and Spot VMs: Saving 60-91%

### The Pricing Tiers

GCP offers three pricing tiers for the same hardware:

| Tier | Discount vs On-Demand | Max Lifetime | Guarantee | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **On-Demand** | 0% (baseline) | Unlimited | Will not be preempted | Production, stateful workloads |
| **Committed Use (CUD)** | 28-52% | 1 or 3 year term | Will not be preempted | Steady-state production |
| **Spot** | 60-91% | None (no 24h limit) | Can be preempted anytime | Batch, CI/CD, fault-tolerant |
| **Preemptible (legacy)** | 60-91% | 24 hours max | Preempted at 24h, or earlier | Use Spot instead (superset) |

**Spot VMs** replaced Preemptible VMs as the recommended ephemeral option. They offer the same discount but without the 24-hour maximum lifetime. Both can be preempted at any time with a 30-second warning.

```bash
# Create a Spot VM
gcloud compute instances create batch-worker \
  --machine-type=n2-standard-4 \
  --zone=us-central1-a \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --image-family=debian-12 \
  --image-project=debian-cloud

# termination-action options:
# STOP  - VM is stopped (can be restarted later if capacity available)
# DELETE - VM is deleted (for truly ephemeral workloads)

# Create with preemptible (legacy, avoid for new workloads)
gcloud compute instances create legacy-worker \
  --machine-type=n2-standard-4 \
  --zone=us-central1-a \
  --preemptible \
  --image-family=debian-12 \
  --image-project=debian-cloud
```

### Handling Preemption Gracefully

```bash
# Inside the VM: check if a preemption notice has been issued
# (the metadata server returns a termination timestamp 30s before preemption)
curl -s "http://metadata.google.internal/computeMetadata/v1/instance/preempted" \
  -H "Metadata-Flavor: Google"

# Create a shutdown script that handles graceful termination
gcloud compute instances create batch-worker \
  --machine-type=n2-standard-4 \
  --zone=us-central1-a \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --metadata=shutdown-script='#!/bin/bash
    echo "Preemption detected at $(date)" >> /var/log/preemption.log
    # Save checkpoint, flush buffers, deregister from load balancer
    /opt/app/save-checkpoint.sh
    /opt/app/deregister.sh'
```

### Committed Use Discounts (CUDs)

For steady-state production workloads, CUDs offer significant savings without any preemption risk.

| Commitment | Duration | Discount |
| :--- | :--- | :--- |
| **Resource-based** | 1 year | ~28% |
| **Resource-based** | 3 years | ~52% |
| **Spend-based** | 1 year | 25% (more flexible) |
| **Spend-based** | 3 years | 52% |

```bash
# Purchase a committed use discount (resource-based)
gcloud compute commitments create my-commitment \
  --region=us-central1 \
  --resources=vcpu=100,memory=400GB \
  --plan=36-month \
  --type=GENERAL_PURPOSE

# View existing commitments
gcloud compute commitments list --region=us-central1
```

Sustained Use Discounts (SUDs) apply automatically---no commitment required. If a VM runs for more than 25% of the month, GCP automatically applies increasing discounts. By the end of the month, you effectively get a ~20% discount for VMs that ran the entire time.

---

## Custom Images and Image Families

### Why Custom Images Matter

Every time you create a VM from a public image (like `debian-12`), you start with a bare OS. Installing your application, dependencies, and configuration on every new VM wastes time and creates inconsistency. Custom images solve this by baking your software into a reusable image.

```bash
# Step 1: Create a VM and configure it
gcloud compute instances create image-builder \
  --machine-type=e2-medium \
  --zone=us-central1-a \
  --image-family=debian-12 \
  --image-project=debian-cloud

# SSH in and install your software
gcloud compute ssh image-builder --zone=us-central1-a
# Inside the VM:
# sudo apt-get update && sudo apt-get install -y nginx nodejs npm
# sudo npm install -g your-app
# sudo systemctl enable nginx
# exit

# Step 2: Stop the VM (required for image creation)
gcloud compute instances stop image-builder --zone=us-central1-a

# Step 3: Create a custom image from the VM's disk
gcloud compute images create my-app-v1-0 \
  --source-disk=image-builder \
  --source-disk-zone=us-central1-a \
  --family=my-app \
  --description="My App v1.0 with nginx and Node.js"

# Step 4: Clean up the builder VM
gcloud compute instances delete image-builder --zone=us-central1-a --quiet
```

### Image Families

Image families are like a "latest" pointer for your custom images. When you create a new image in a family, it automatically becomes the default.

```bash
# Create new version in the same family
gcloud compute images create my-app-v1-1 \
  --source-disk=image-builder-v2 \
  --source-disk-zone=us-central1-a \
  --family=my-app

# Create a VM using the latest image in the family
gcloud compute instances create web-1 \
  --image-family=my-app \
  --zone=us-central1-a

# List images in a family
gcloud compute images list --filter="family=my-app" \
  --format="table(name, creationTimestamp, status)"

# Roll back: deprecate the latest image, making the previous one current
gcloud compute images deprecate my-app-v1-1 \
  --state=DEPRECATED \
  --replacement=my-app-v1-0
```

---

## Instance Templates and Managed Instance Groups

### Instance Templates

An instance template is a blueprint that defines the machine type, image, disks, network, and other settings for a VM. Templates are **immutable**---to change a setting, you create a new template.

```bash
# Create an instance template
gcloud compute instance-templates create web-template-v1 \
  --machine-type=e2-standard-2 \
  --image-family=my-app \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-balanced \
  --network=prod-vpc \
  --subnet=web-tier \
  --region=us-central1 \
  --no-address \
  --service-account=web-sa@my-project.iam.gserviceaccount.com \
  --scopes=cloud-platform \
  --tags=web-server \
  --metadata=startup-script='#!/bin/bash
    systemctl start nginx
    echo "$(hostname) ready" > /var/www/html/health'

# List templates
gcloud compute instance-templates list

# Create a new version (templates are immutable)
gcloud compute instance-templates create web-template-v2 \
  --machine-type=e2-standard-4 \
  --image-family=my-app \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-balanced \
  --network=prod-vpc \
  --subnet=web-tier \
  --region=us-central1 \
  --no-address \
  --service-account=web-sa@my-project.iam.gserviceaccount.com \
  --scopes=cloud-platform
```

### Managed Instance Groups (MIGs)

A MIG is a group of identical VMs created from an instance template. MIGs provide autoscaling, self-healing, rolling updates, and load balancer integration.

```bash
# Create a regional MIG (recommended: spans all zones in a region)
gcloud compute instance-groups managed create web-mig \
  --template=web-template-v1 \
  --size=3 \
  --region=us-central1 \
  --health-check=web-health-check \
  --initial-delay=120

# Create the health check first
gcloud compute health-checks create http web-health-check \
  --port=80 \
  --request-path=/health \
  --check-interval=10s \
  --timeout=5s \
  --healthy-threshold=2 \
  --unhealthy-threshold=3
```

### Autoscaling

```bash
# Add autoscaling to the MIG
gcloud compute instance-groups managed set-autoscaling web-mig \
  --region=us-central1 \
  --min-num-replicas=2 \
  --max-num-replicas=20 \
  --target-cpu-utilization=0.6 \
  --cool-down-period=120

# Scale based on HTTP load balancing utilization
gcloud compute instance-groups managed set-autoscaling web-mig \
  --region=us-central1 \
  --min-num-replicas=2 \
  --max-num-replicas=20 \
  --custom-metric-utilization=metric=loadbalancing.googleapis.com/https/request_count,utilization-target=1000,utilization-target-type=GAUGE

# View current autoscaling status
gcloud compute instance-groups managed describe web-mig \
  --region=us-central1 \
  --format="yaml(status.autoscaler)"
```

### Rolling Updates

MIGs support zero-downtime updates by gradually replacing instances with a new template.

```bash
# Start a rolling update to the new template
gcloud compute instance-groups managed rolling-action start-update web-mig \
  --version=template=web-template-v2 \
  --region=us-central1 \
  --max-surge=3 \
  --max-unavailable=0

# Canary update: run new template on a subset of instances
gcloud compute instance-groups managed rolling-action start-update web-mig \
  --version=template=web-template-v1 \
  --canary-version=template=web-template-v2,target-size=20% \
  --region=us-central1

# Monitor the update
gcloud compute instance-groups managed describe web-mig \
  --region=us-central1 \
  --format="yaml(status.versionTarget, status.isStable)"

# Roll back (just update back to the old template)
gcloud compute instance-groups managed rolling-action start-update web-mig \
  --version=template=web-template-v1 \
  --region=us-central1
```

| Update Parameter | Description | Recommended |
| :--- | :--- | :--- |
| `--max-surge` | Extra instances during update | 3 or 20% |
| `--max-unavailable` | Instances that can be offline | 0 (zero downtime) |
| `--replacement-method=SUBSTITUTE` | Create new, then delete old | Default (safest) |
| `--replacement-method=RECREATE` | Delete old, then create new | Only when IP must stay |
| `--minimal-action=REPLACE` | Replace entire VM | When image/template changes |
| `--minimal-action=RESTART` | Just restart existing VM | When only metadata changes |

### Self-Healing

When a health check fails, the MIG automatically recreates the unhealthy VM. This is the simplest form of self-healing in GCP.

```text
  Normal Operation:                    Self-Healing:
  ┌──────┐ ┌──────┐ ┌──────┐         ┌──────┐ ┌──────┐ ┌──────┐
  │ VM-1 │ │ VM-2 │ │ VM-3 │         │ VM-1 │ │ VM-2 │ │ VM-3 │
  │  OK   │ │  OK   │ │  OK  │         │  OK  │ │ FAIL │ │  OK  │
  └──────┘ └──────┘ └──────┘         └──────┘ └──┬───┘ └──────┘
                                                  │
                                           Health check fails
                                           3 consecutive times
                                                  │
                                                  ▼
                                        MIG deletes VM-2
                                        and creates VM-2-new
                                        from the template
```

---

## Cloud Load Balancing

GCP offers multiple load balancer types, but the most common is the **External Application Load Balancer** (formerly known as the External HTTP(S) Load Balancer).

### Load Balancer Types

| Type | Scope | Layer | Protocol | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **External Application LB** | Global | L7 | HTTP/HTTPS | Public web apps, APIs |
| **Internal Application LB** | Regional | L7 | HTTP/HTTPS | Internal microservices |
| **External Network LB** | Regional | L4 | TCP/UDP | Non-HTTP (gaming, VoIP) |
| **Internal Network LB** | Regional | L4 | TCP/UDP | Internal TCP/UDP services |
| **External Proxy Network LB** | Global | L4 | TCP/SSL | Global TCP with Anycast |

### Architecture of the External Application Load Balancer

```text
  Users (Internet)
       │
       ▼
  ┌─────────────────────────┐
  │  Google Global Anycast   │  ← Single IP, served from 100+ edge locations
  │  IP Address              │
  └────────────┬────────────┘
               │
  ┌────────────▼────────────┐
  │  URL Map                 │  ← Routes based on host/path
  │  /api/*  → backend-api   │     (e.g., /api → API MIG, /static → GCS bucket)
  │  /static → cdn-bucket    │
  │  /*      → backend-web   │
  └────────────┬────────────┘
               │
  ┌────────────▼────────────┐
  │  Backend Service         │  ← Health checks, session affinity,
  │  (or Backend Bucket)     │     connection draining
  └────────────┬────────────┘
               │
     ┌─────────┼──────────┐
     │                     │
  ┌──▼─────────┐  ┌───────▼────┐
  │ MIG         │  │ MIG         │
  │ us-central1 │  │ europe-west1│
  │ (3 VMs)     │  │ (3 VMs)     │
  └─────────────┘  └─────────────┘
```

### Setting Up a Global Load Balancer

```bash
# Step 1: Reserve a global static IP
gcloud compute addresses create web-lb-ip \
  --ip-version=IPV4 \
  --global

# Step 2: Create a health check for the backend service
gcloud compute health-checks create http web-lb-health \
  --port=80 \
  --request-path=/health

# Step 3: Create a backend service
gcloud compute backend-services create web-backend \
  --protocol=HTTP \
  --port-name=http \
  --health-checks=web-lb-health \
  --global

# Step 4: Add MIG backends to the backend service
gcloud compute backend-services add-backend web-backend \
  --instance-group=web-mig-us \
  --instance-group-region=us-central1 \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --global

gcloud compute backend-services add-backend web-backend \
  --instance-group=web-mig-eu \
  --instance-group-region=europe-west1 \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --global

# Step 5: Create a URL map
gcloud compute url-maps create web-url-map \
  --default-service=web-backend

# Step 6: Create an HTTPS target proxy with a managed SSL certificate
gcloud compute ssl-certificates create web-cert \
  --domains=www.example.com \
  --global

gcloud compute target-https-proxies create web-https-proxy \
  --url-map=web-url-map \
  --ssl-certificates=web-cert

# Step 7: Create a forwarding rule
gcloud compute forwarding-rules create web-https-rule \
  --address=web-lb-ip \
  --global \
  --target-https-proxy=web-https-proxy \
  --ports=443
```

### Named Ports

MIGs communicate port mappings through named ports. The backend service references a name (like "http"), and the MIG maps that name to an actual port number.

```bash
# Set named port on the MIG
gcloud compute instance-groups managed set-named-ports web-mig-us \
  --named-ports=http:80 \
  --region=us-central1

gcloud compute instance-groups managed set-named-ports web-mig-eu \
  --named-ports=http:80 \
  --region=europe-west1
```

---

## Disk Types and Storage

| Disk Type | IOPS (Read) | Throughput | Use Case | Cost |
| :--- | :--- | :--- | :--- | :--- |
| **pd-standard** | 0.75 per GB | 12 MB/s per GB | Bulk storage, logs | Lowest |
| **pd-balanced** | 6 per GB | 28 MB/s per GB | General purpose (default) | Medium |
| **pd-ssd** | 30 per GB | 48 MB/s per GB | Databases, high I/O | Higher |
| **pd-extreme** | Configurable | Configurable | SAP HANA, Oracle DB | Highest |
| **local-ssd** | 900K total | 9.4 GB/s total | Temp storage, caches | Included with VM |

```bash
# Create a VM with an additional SSD data disk
gcloud compute instances create db-server \
  --machine-type=n2-standard-8 \
  --zone=us-central1-a \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-balanced \
  --create-disk=name=data-disk,size=200GB,type=pd-ssd,auto-delete=no

# Create a snapshot (backup)
gcloud compute disks snapshot data-disk \
  --zone=us-central1-a \
  --snapshot-names=data-disk-backup-$(date +%Y%m%d)

# Schedule automatic snapshots
gcloud compute resource-policies create snapshot-schedule daily-snapshot \
  --region=us-central1 \
  --max-retention-days=14 \
  --start-time=02:00 \
  --daily-schedule
```

---

## Did You Know?

1. **GCP's global load balancer uses Anycast routing**, meaning a single IP address is advertised from over 100 Google edge locations worldwide. When a user in Tokyo connects to your load balancer IP, they are routed to the nearest Google edge, which then forwards the request to the closest healthy backend. This happens at the network layer---no DNS-based routing tricks needed.

2. **Spot VMs can save up to 91% compared to on-demand pricing**. The actual discount varies by machine type and region. For a batch processing job running `n2-standard-16` instances, the difference between on-demand ($0.7769/hr) and Spot ($0.07-0.23/hr) can mean the difference between a $5,000 monthly bill and a $500 one.

3. **Live migration is a GCP superpower that most users never notice**. When Google needs to perform host maintenance, your VMs are transparently migrated to another physical host with no reboot and typically less than a second of degraded performance. This is enabled by default on all standard VMs. Preemptible/Spot VMs do not support live migration---they are terminated instead.

4. **You can create a VM with up to 416 vCPUs and 12 TB of memory** using the M3 machine family. These ultra-high-memory machines are designed for SAP HANA, large in-memory databases, and genomics workloads. At full price, an `m3-megamem-128` costs over $21 per hour---which is still cheaper than buying equivalent on-premises hardware when you factor in a 3-year amortization.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using N1 machines for new workloads | N1 appears first in old tutorials | Use N2, N2D, or E2---they offer better price-performance |
| Not using Managed Instance Groups | Individual VMs seem simpler initially | Always use MIGs for production; they provide autoscaling and self-healing |
| Setting autoscaler min to 1 | Want to minimize cost | Min should be 2+ for high availability across zones |
| Not configuring health checks | Assumed MIG "just knows" when VMs are unhealthy | Create HTTP health checks with appropriate thresholds |
| Using external IPs on every VM | Easier to SSH directly | Use IAP tunneling; VMs should not have external IPs unless they serve public traffic |
| Ignoring Sustained Use Discounts | Assuming CUDs are the only option | SUDs apply automatically; check billing reports to see your effective discount |
| Choosing pd-standard for databases | It is the cheapest disk type | Use pd-ssd for any workload with latency requirements; pd-standard IOPS scales with disk size |
| Not setting shutdown scripts on Spot VMs | Assuming preemption never happens | Always implement graceful shutdown to save state and deregister from services |

---

## Quiz

<details>
<summary>1. What is the difference between a Spot VM and a Preemptible VM in GCP?</summary>

Spot VMs are the successor to Preemptible VMs and are the recommended choice for fault-tolerant workloads. The key differences: Preemptible VMs have a **maximum lifetime of 24 hours**---GCP will always terminate them after 24 hours even if capacity is available. Spot VMs have **no maximum lifetime**; they run indefinitely as long as capacity is available. Both can be preempted at any time with 30 seconds of warning, and both offer the same 60-91% discount. Spot VMs also support the `STOP` termination action (where the VM is stopped and can be restarted later), while Preemptible VMs are always deleted.
</details>

<details>
<summary>2. You have a MIG with 3 instances. One instance fails its health check 3 consecutive times. What happens?</summary>

The MIG's self-healing mechanism kicks in. The MIG detects that the instance has failed the configured health check threshold (3 consecutive failures in this case). It will **delete the unhealthy instance** and **create a new instance** from the instance template to replace it. The new instance must pass the health check after the `initial-delay` period before it is considered healthy. During this process, if the MIG is behind a load balancer, the load balancer stops sending traffic to the unhealthy instance as soon as its health check fails, ensuring users are not affected.
</details>

<details>
<summary>3. Why is a regional MIG generally preferred over a zonal MIG?</summary>

A regional MIG distributes instances across **all zones in a region**, providing protection against zone-level failures. If one zone experiences an outage, the MIG continues serving traffic from the remaining zones. A zonal MIG places all instances in a single zone, creating a single point of failure. Regional MIGs also integrate better with global load balancing and allow the autoscaler to place new instances in the zone with the most available capacity. The only reason to use a zonal MIG is when you need a specific feature that is zone-dependent, like attaching a local SSD that must be in the same zone.
</details>

<details>
<summary>4. How does a canary deployment work with a MIG rolling update?</summary>

A canary deployment in a MIG uses the `--canary-version` flag during a rolling update. You specify two versions: the primary (existing template) and the canary (new template) with a `target-size` percentage. For example, `--canary-version=template=web-v2,target-size=20%` will update 20% of instances to the new template while keeping 80% on the old template. You can then monitor the canary instances for errors or performance regressions. If the canary is healthy, you proceed with a full rollout. If not, you roll back by updating with only the old template. This allows you to test changes in production with limited blast radius.
</details>

<details>
<summary>5. What is the difference between pd-balanced, pd-ssd, and pd-standard persistent disks?</summary>

The three disk types differ in performance and cost. **pd-standard** (HDD-backed) offers the lowest IOPS (0.75 per GB) and throughput, suitable only for sequential reads/writes like log storage. **pd-balanced** offers moderate IOPS (6 per GB) and is the default recommended choice for general workloads---boot disks, web servers, and applications that do not have extreme I/O needs. **pd-ssd** offers the highest IOPS (30 per GB) and throughput, making it the right choice for databases, caches, and any latency-sensitive workload. All three are network-attached persistent disks that survive VM deletion and can be snapshotted.
</details>

<details>
<summary>6. What is live migration, and which VM types do NOT support it?</summary>

Live migration is a GCP feature that transparently moves a running VM from one physical host to another without rebooting the VM. Google triggers live migration during host maintenance events (hardware updates, security patches, etc.). The VM experiences less than a second of degraded performance during migration. **Preemptible VMs, Spot VMs, and VMs with GPUs attached** do not support live migration. Preemptible and Spot VMs are terminated instead of migrated. GPU VMs must be configured with `--maintenance-policy=TERMINATE` because GPU state cannot be migrated.
</details>

---

## Hands-On Exercise: Globally Load-Balanced App Across Two Regions

### Objective

Build a production-like architecture with MIGs in two regions behind a global HTTPS load balancer.

### Prerequisites

- `gcloud` CLI installed and authenticated
- A GCP project with billing enabled
- A custom VPC with subnets in `us-central1` and `europe-west1`

### Tasks

**Task 1: Create the Network Foundation**

<details>
<summary>Solution</summary>

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION_US=us-central1
export REGION_EU=europe-west1

# Create custom VPC
gcloud compute networks create web-vpc \
  --subnet-mode=custom \
  --bgp-routing-mode=global

# Create subnets
gcloud compute networks subnets create web-us \
  --network=web-vpc \
  --region=$REGION_US \
  --range=10.10.0.0/24 \
  --enable-private-ip-google-access

gcloud compute networks subnets create web-eu \
  --network=web-vpc \
  --region=$REGION_EU \
  --range=10.11.0.0/24 \
  --enable-private-ip-google-access

# Create firewall rules
gcloud compute firewall-rules create web-vpc-allow-http \
  --network=web-vpc \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=130.211.0.0/22,35.191.0.0/16 \
  --description="Allow health checks and LB traffic"

gcloud compute firewall-rules create web-vpc-allow-iap \
  --network=web-vpc \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=35.235.240.0/20
```
</details>

**Task 2: Create an Instance Template**

<details>
<summary>Solution</summary>

```bash
# Create instance template (uses startup script to install nginx)
gcloud compute instance-templates create web-template \
  --machine-type=e2-small \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=10GB \
  --boot-disk-type=pd-balanced \
  --network=web-vpc \
  --no-address \
  --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y nginx
    ZONE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google" | cut -d/ -f4)
    HOSTNAME=$(hostname)
    cat > /var/www/html/index.html <<HTMLEOF
    <h1>Hello from $HOSTNAME</h1>
    <p>Zone: $ZONE</p>
    <p>Served at: $(date)</p>
HTMLEOF
    cat > /var/www/html/health <<HTMLEOF
    OK
HTMLEOF
    systemctl restart nginx'

# Verify
gcloud compute instance-templates describe web-template \
  --format="yaml(properties.machineType, properties.networkInterfaces)"
```
</details>

**Task 3: Create Regional MIGs with Autoscaling**

<details>
<summary>Solution</summary>

```bash
# Create health check
gcloud compute health-checks create http web-hc \
  --port=80 \
  --request-path=/health \
  --check-interval=10s \
  --timeout=5s \
  --healthy-threshold=2 \
  --unhealthy-threshold=3

# Create MIG in US
gcloud compute instance-groups managed create web-mig-us \
  --template=web-template \
  --size=2 \
  --region=$REGION_US \
  --health-check=web-hc \
  --initial-delay=120

# Create MIG in EU
gcloud compute instance-groups managed create web-mig-eu \
  --template=web-template \
  --size=2 \
  --region=$REGION_EU \
  --health-check=web-hc \
  --initial-delay=120

# Set named ports
gcloud compute instance-groups managed set-named-ports web-mig-us \
  --named-ports=http:80 --region=$REGION_US

gcloud compute instance-groups managed set-named-ports web-mig-eu \
  --named-ports=http:80 --region=$REGION_EU

# Add autoscaling
for MIG_REGION in $REGION_US $REGION_EU; do
  MIG_NAME="web-mig-$(echo $MIG_REGION | cut -d- -f1)"
  [ "$MIG_REGION" = "$REGION_US" ] && MIG_NAME="web-mig-us"
  [ "$MIG_REGION" = "$REGION_EU" ] && MIG_NAME="web-mig-eu"

  gcloud compute instance-groups managed set-autoscaling $MIG_NAME \
    --region=$MIG_REGION \
    --min-num-replicas=2 \
    --max-num-replicas=10 \
    --target-cpu-utilization=0.6 \
    --cool-down-period=120
done
```
</details>

**Task 4: Create the Global Load Balancer**

<details>
<summary>Solution</summary>

```bash
# Reserve global IP
gcloud compute addresses create web-global-ip --ip-version=IPV4 --global

# Get the IP address
WEB_IP=$(gcloud compute addresses describe web-global-ip --global --format="get(address)")
echo "Load Balancer IP: $WEB_IP"

# Create backend service
gcloud compute backend-services create web-backend-svc \
  --protocol=HTTP \
  --port-name=http \
  --health-checks=web-hc \
  --global

# Add both MIGs as backends
gcloud compute backend-services add-backend web-backend-svc \
  --instance-group=web-mig-us \
  --instance-group-region=$REGION_US \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --global

gcloud compute backend-services add-backend web-backend-svc \
  --instance-group=web-mig-eu \
  --instance-group-region=$REGION_EU \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --global

# Create URL map
gcloud compute url-maps create web-url-map \
  --default-service=web-backend-svc

# Create HTTP target proxy (use HTTPS with cert in production)
gcloud compute target-http-proxies create web-http-proxy \
  --url-map=web-url-map

# Create forwarding rule
gcloud compute forwarding-rules create web-http-rule \
  --address=web-global-ip \
  --global \
  --target-http-proxy=web-http-proxy \
  --ports=80

echo "Load balancer will be available at http://$WEB_IP in 3-5 minutes"
```
</details>

**Task 5: Test and Verify**

<details>
<summary>Solution</summary>

```bash
# Wait for backends to become healthy (check every 30 seconds)
echo "Waiting for backends to become healthy..."
while true; do
  STATUS=$(gcloud compute backend-services get-health web-backend-svc --global 2>&1)
  HEALTHY=$(echo "$STATUS" | grep -c "HEALTHY" || true)
  echo "Healthy backends: $HEALTHY"
  if [ "$HEALTHY" -ge 4 ]; then
    echo "All backends healthy!"
    break
  fi
  sleep 30
done

# Test the load balancer (run multiple times to see different backends)
WEB_IP=$(gcloud compute addresses describe web-global-ip --global --format="get(address)")

for i in $(seq 1 6); do
  echo "--- Request $i ---"
  curl -s http://$WEB_IP
  echo
done

# Check backend health status
gcloud compute backend-services get-health web-backend-svc --global
```
</details>

**Task 6: Clean Up**

<details>
<summary>Solution</summary>

```bash
# Delete in reverse order of dependencies
gcloud compute forwarding-rules delete web-http-rule --global --quiet
gcloud compute target-http-proxies delete web-http-proxy --quiet
gcloud compute url-maps delete web-url-map --quiet
gcloud compute backend-services delete web-backend-svc --global --quiet
gcloud compute addresses delete web-global-ip --global --quiet

# Delete MIGs
gcloud compute instance-groups managed delete web-mig-us --region=$REGION_US --quiet
gcloud compute instance-groups managed delete web-mig-eu --region=$REGION_EU --quiet

# Delete health check and template
gcloud compute health-checks delete web-hc --quiet
gcloud compute instance-templates delete web-template --quiet

# Delete firewall rules and network
gcloud compute firewall-rules delete web-vpc-allow-http --quiet
gcloud compute firewall-rules delete web-vpc-allow-iap --quiet
gcloud compute networks subnets delete web-us --region=$REGION_US --quiet
gcloud compute networks subnets delete web-eu --region=$REGION_EU --quiet
gcloud compute networks delete web-vpc --quiet

echo "Cleanup complete."
```
</details>

### Success Criteria

- [ ] Custom VPC with subnets in two regions
- [ ] Instance template configured with startup script
- [ ] MIGs in both regions with health checks and autoscaling
- [ ] Global load balancer distributing traffic to both regions
- [ ] Multiple curl requests show responses from different VMs/zones
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 4: Cloud Storage (GCS)](module-4-gcs.md)** --- Master storage classes, lifecycle management, versioning, signed URLs, and the gsutil/gcloud commands you will use every day.
