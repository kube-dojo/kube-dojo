# VMs & VM Scale Sets
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Module 2 (Virtual Networks)

## Why This Module Matters

In November 2020, a SaaS company running their entire production workload on a single Azure VM in the East US region experienced an outage that lasted 9 hours. The VM's host server had a hardware failure. Because the company had not configured Availability Zones, had no VM Scale Set, and had no load balancer, their application was completely offline. Their customers, many of whom were running end-of-month financial reports, could not access the platform. The post-incident review revealed that the monthly cost to run their single D4s_v3 VM was $140. Adding a second VM in a different Availability Zone behind a Standard Load Balancer would have added $165/month. A $165/month insurance policy could have prevented a $420,000 revenue loss and a wave of customer churn.

Virtual machines remain the workhorse of cloud computing. Even in a world of containers, serverless functions, and managed services, VMs are the foundation that most of those higher-level services are built on. Understanding VM sizes, high availability constructs, disk types, and auto-scaling is fundamental to running reliable workloads on Azure. When you need full control over the operating system, when you are running software that cannot be containerized, or when you need specific hardware (like GPUs or high-memory instances), VMs are the answer.

In this module, you will learn how to choose the right VM size for your workload, how Availability Zones and Availability Sets protect you from infrastructure failures, how Managed Disks work, and how VM Scale Sets automate horizontal scaling. By the end, you will deploy a highly available web tier across multiple Availability Zones behind a Standard Load Balancer.

---

## Choosing the Right VM Size

Azure offers hundreds of VM sizes, organized into families based on the workload type they are optimized for. Choosing the right VM size is one of the most impactful decisions you will make---oversizing wastes money, undersizing causes performance problems.

### VM Size Families

| Family | Prefix | Optimized For | Example Use Cases |
| :--- | :--- | :--- | :--- |
| **General Purpose** | B, D, Ds | Balanced CPU-to-memory ratio | Web servers, small databases, dev/test |
| **Compute Optimized** | F, Fs | High CPU-to-memory ratio | Batch processing, gaming servers, CI/CD agents |
| **Memory Optimized** | E, Es, M | High memory-to-CPU ratio | Large databases, in-memory caches, SAP HANA |
| **Storage Optimized** | L, Ls | High disk throughput and IOPS | Data warehouses, large transactional databases |
| **GPU** | NC, ND, NV | GPU-accelerated workloads | ML training, rendering, video encoding |
| **High Performance** | HB, HC, HX | Fastest CPUs, InfiniBand networking | Scientific simulation, financial modeling |

### Understanding VM Size Naming

Azure VM sizes follow a naming convention that tells you a lot if you know how to read it:

```text
    Standard_D4s_v5

    Standard   = VM tier (Standard or Basic)
    D          = Family (General Purpose)
    4          = vCPUs
    s          = Premium SSD capable
    _v5        = Generation (hardware version)

    Other suffixes:
    a = AMD processor      (Standard_D4as_v5)
    d = Local temp disk     (Standard_D4ds_v5)
    i = Isolated (dedicated host)
    l = Low memory
    p = ARM-based (Ampere)  (Standard_D4ps_v5)
```

```bash
# List all available VM sizes in a region
az vm list-sizes --location eastus2 -o table

# Filter for D-series v5 sizes
az vm list-sizes --location eastus2 \
  --query "[?starts_with(name, 'Standard_D') && contains(name, 'v5')].{Name:name, vCPUs:numberOfCores, MemoryGB:memoryInMB}" \
  -o table

# Check what sizes are available for a specific VM (for resizing)
az vm list-vm-resize-options -g myRG -n myVM -o table
```

### The B-Series: Burstable VMs

The B-series deserves special attention because it is the most cost-effective option for workloads that do not need sustained CPU. B-series VMs accumulate CPU credits when idle and spend them during bursts.

```text
    B-Series CPU Credit Model:

    CPU Usage
    100% ─────────────────────────────────────────────────
         │            ▓▓▓▓ Burst         ▓▓▓▓ Burst
         │            ▓▓▓▓ (spending     ▓▓▓▓
         │            ▓▓▓▓  credits)      ▓▓▓▓
    20%  │────────────▓▓▓▓────────────────▓▓▓▓──── Baseline
         │ ░░░░░░░░░░ ▓▓▓▓ ░░░░░░░░░░░░░ ▓▓▓▓
         │ ░ Earning ░ ▓▓▓▓ ░ Earning  ░░ ▓▓▓▓
         │ ░ credits ░      ░ credits  ░░
    0%   └──────────────────────────────────────── Time

    Below baseline = earning credits
    Above baseline = spending credits
    Credits depleted = throttled to baseline
```

A Standard_B2s (2 vCPUs, 4 GB RAM) costs about $30/month, while an equivalent Standard_D2s_v5 costs about $70/month. For a dev/test VM that sits idle 80% of the time, B-series saves you 57%.

**War Story**: A team running 15 CI/CD build agents on D4s_v5 instances (4 vCPUs, 16 GB, ~$140/month each) was spending $2,100/month. They analyzed their build patterns and found that agents were busy only 25% of the time, with builds coming in bursts. Switching to B4ms instances (same specs, burstable) at ~$67/month each cut their compute bill to $1,005/month---a 52% reduction with no performance impact on build times.

---

## High Availability: Availability Zones vs Availability Sets

Azure provides two mechanisms to protect your VMs from infrastructure failures. Understanding the difference is essential for designing reliable systems.

### Availability Zones (AZs)

An Availability Zone is a physically separate location within an Azure region. Each zone has independent power, cooling, and networking. If a fire destroys Zone 1, Zones 2 and 3 continue operating. Azure guarantees a **99.99% SLA** for VMs deployed across two or more zones.

```text
    Azure Region: East US 2
    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
    │  │   Zone 1    │  │   Zone 2    │  │   Zone 3    │ │
    │  │             │  │             │  │             │ │
    │  │  [VM-1]     │  │  [VM-2]     │  │  [VM-3]     │ │
    │  │             │  │             │  │             │ │
    │  │  Own power  │  │  Own power  │  │  Own power  │ │
    │  │  Own cooling│  │  Own cooling│  │  Own cooling│ │
    │  │  Own network│  │  Own network│  │  Own network│ │
    │  └─────────────┘  └─────────────┘  └─────────────┘ │
    │                                                     │
    │  Low-latency interconnect between zones (<2ms)      │
    └─────────────────────────────────────────────────────┘
```

### Availability Sets

An Availability Set distributes VMs across **Fault Domains** (separate physical racks) and **Update Domains** (groups that Azure reboots sequentially during maintenance). Availability Sets provide a **99.95% SLA**.

```text
    Availability Set (3 Fault Domains, 5 Update Domains)
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    │   Fault Domain 0    FD 1           FD 2         │
    │   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
    │   │ Rack 1   │   │ Rack 2   │   │ Rack 3   │   │
    │   │          │   │          │   │          │   │
    │   │ VM-1(UD0)│   │ VM-2(UD1)│   │ VM-3(UD2)│   │
    │   │ VM-4(UD3)│   │ VM-5(UD4)│   │          │   │
    │   │          │   │          │   │          │   │
    │   └──────────┘   └──────────┘   └──────────┘   │
    │                                                 │
    │   During maintenance, Azure reboots one UD      │
    │   at a time: UD0, then UD1, then UD2, etc.      │
    └─────────────────────────────────────────────────┘
```

### When to Use Which

| Criteria | Availability Zones | Availability Sets |
| :--- | :--- | :--- |
| **SLA** | 99.99% | 99.95% |
| **Protection against** | Data center-level failure | Rack-level failure, planned maintenance |
| **Latency between instances** | ~1-2ms (cross-zone) | <1ms (same data center) |
| **Region support** | Most major regions, but not all | All regions |
| **Cost** | No extra charge for the VM, but cross-zone data transfer costs | No extra charge |
| **Recommendation** | Use whenever the region supports zones | Use only when zones are unavailable |

```bash
# Create a VM in a specific Availability Zone
az vm create \
  --resource-group myRG \
  --name web-vm-1 \
  --image Ubuntu2204 \
  --size Standard_D2s_v5 \
  --zone 1 \
  --admin-username azureuser \
  --generate-ssh-keys

# Create a VM in a different zone
az vm create \
  --resource-group myRG \
  --name web-vm-2 \
  --image Ubuntu2204 \
  --size Standard_D2s_v5 \
  --zone 2 \
  --admin-username azureuser \
  --generate-ssh-keys

# Create an Availability Set (when zones are not available)
az vm availability-set create \
  --resource-group myRG \
  --name web-avset \
  --platform-fault-domain-count 3 \
  --platform-update-domain-count 5
```

---

## Managed Disks: Storage for Your VMs

Every Azure VM needs at least one disk: the **OS disk**. Most production VMs also have one or more **data disks**. Azure Managed Disks abstract away the storage account management, giving you a simple, reliable disk resource.

### Disk Types

| Type | IOPS (max) | Throughput (max) | Use Case | Cost (128 GB) |
| :--- | :--- | :--- | :--- | :--- |
| **Standard HDD** | 500 | 60 MB/s | Backups, dev/test, infrequent access | ~$5/month |
| **Standard SSD** | 6,000 | 750 MB/s | Web servers, light databases | ~$10/month |
| **Premium SSD** | 7,500 | 250 MB/s | Production databases, high IOPS | ~$19/month |
| **Premium SSD v2** | 80,000 | 1,200 MB/s | Tier-1 databases, demanding workloads | ~$10+/month (pay per IOPS/throughput) |
| **Ultra Disk** | 160,000 | 4,000 MB/s | SAP HANA, transaction-heavy databases | ~$67+/month |

```bash
# Create a VM with a Premium SSD OS disk and a 256 GB data disk
az vm create \
  --resource-group myRG \
  --name db-vm \
  --image Ubuntu2204 \
  --size Standard_D4s_v5 \
  --os-disk-size-gb 64 \
  --storage-sku Premium_LRS \
  --data-disk-sizes-gb 256 \
  --admin-username azureuser \
  --generate-ssh-keys

# Add another data disk to an existing VM
az vm disk attach \
  --resource-group myRG \
  --vm-name db-vm \
  --name db-data-disk-2 \
  --size-gb 512 \
  --sku Premium_LRS \
  --new

# List disks attached to a VM
az vm show -g myRG -n db-vm \
  --query '{OSDisk:storageProfile.osDisk.name, DataDisks:storageProfile.dataDisks[].{Name:name, SizeGB:diskSizeGb, Type:managedDisk.storageAccountType}}' -o json
```

### Disk Encryption

Azure encrypts all Managed Disks at rest by default using platform-managed keys (PMK). For additional control, you can use:

- **Customer-managed keys (CMK)**: You manage the encryption key in Azure Key Vault
- **Azure Disk Encryption (ADE)**: Uses BitLocker (Windows) or DM-Crypt (Linux) for OS-level encryption
- **Confidential disk encryption**: For confidential VMs, encrypts the disk with a key tied to the VM's TPM

```bash
# Enable Azure Disk Encryption on a Linux VM
az vm encryption enable \
  --resource-group myRG \
  --name db-vm \
  --disk-encryption-keyvault myKeyVault \
  --volume-type All

# Check encryption status
az vm encryption show --resource-group myRG --name db-vm -o table
```

---

## VM Extensions and Cloud-Init: Automating Configuration

Manually SSHing into VMs to install software is fragile and does not scale. Azure provides two mechanisms for automated configuration: **VM Extensions** and **cloud-init**.

### Cloud-Init

Cloud-init is the industry standard for cross-platform cloud instance initialization. It runs during the first boot of a VM and can install packages, write files, run commands, and configure services.

```yaml
# cloud-init.yaml
#cloud-config
package_update: true
package_upgrade: true

packages:
  - nginx
  - curl
  - jq

write_files:
  - path: /var/www/html/index.html
    content: |
      <!DOCTYPE html>
      <html>
      <body>
        <h1>Hello from KubeDojo VM</h1>
        <p>Hostname: HOSTNAME_PLACEHOLDER</p>
        <p>Zone: ZONE_PLACEHOLDER</p>
      </body>
      </html>

runcmd:
  - hostnamectl set-hostname $(curl -s -H Metadata:true "http://169.254.169.254/metadata/instance/compute/name?api-version=2021-02-01&format=text")
  - HOSTNAME=$(hostname)
  - ZONE=$(curl -s -H Metadata:true "http://169.254.169.254/metadata/instance/compute/zone?api-version=2021-02-01&format=text")
  - sed -i "s/HOSTNAME_PLACEHOLDER/$HOSTNAME/" /var/www/html/index.html
  - sed -i "s/ZONE_PLACEHOLDER/$ZONE/" /var/www/html/index.html
  - systemctl enable nginx
  - systemctl start nginx
```

```bash
# Create a VM with cloud-init
az vm create \
  --resource-group myRG \
  --name web-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --custom-data @cloud-init.yaml \
  --admin-username azureuser \
  --generate-ssh-keys
```

### VM Extensions

VM Extensions are small applications that provide post-deployment configuration and automation. They are Azure-native and can be managed through ARM templates, CLI, or the portal.

```bash
# Install the Custom Script Extension to run a script
az vm extension set \
  --resource-group myRG \
  --vm-name web-vm \
  --name CustomScript \
  --publisher Microsoft.Azure.Extensions \
  --settings '{"commandToExecute":"apt-get update && apt-get install -y docker.io && systemctl enable docker"}'

# Install the Azure Monitor Agent
az vm extension set \
  --resource-group myRG \
  --vm-name web-vm \
  --name AzureMonitorLinuxAgent \
  --publisher Microsoft.Azure.Monitor \
  --enable-auto-upgrade true

# List extensions on a VM
az vm extension list -g myRG --vm-name web-vm -o table
```

---

## VM Scale Sets (VMSS): Horizontal Auto-Scaling

A VM Scale Set is a group of identical, load-balanced VMs that can automatically scale in and out based on demand or a schedule. Think of it as a fleet of VMs managed as a single resource.

### VMSS Architecture

```text
    ┌──────────────────────────────────────────────────────────┐
    │                 VM Scale Set: web-vmss                    │
    │                                                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
    │  │  Instance 0 │  │  Instance 1 │  │  Instance 2 │      │
    │  │  Zone 1     │  │  Zone 2     │  │  Zone 3     │      │
    │  │             │  │             │  │             │      │
    │  │  nginx      │  │  nginx      │  │  nginx      │      │
    │  │  app code   │  │  app code   │  │  app code   │      │
    │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
    │         │                │                │              │
    │         └────────────────┼────────────────┘              │
    │                          │                                │
    │              ┌───────────┴───────────┐                    │
    │              │   Standard Load       │                    │
    │              │   Balancer (Layer 4)  │                    │
    │              │   or App Gateway (L7) │                    │
    │              └───────────┬───────────┘                    │
    │                          │                                │
    │              Autoscale Rules:                             │
    │              - CPU > 70% for 5 min → add 2 instances     │
    │              - CPU < 30% for 10 min → remove 1 instance  │
    │              - Min: 2, Max: 20, Default: 3               │
    └──────────────────────────────────────────────────────────┘
```

### Orchestration Modes

VMSS has two orchestration modes:

| Feature | Uniform (Legacy) | Flexible (Recommended) |
| :--- | :--- | :--- |
| **VM model** | All VMs identical | Mix of VM sizes and configs |
| **Zones** | Spread across zones | Spread across zones |
| **Manual VMs** | Cannot add existing VMs | Can add existing VMs |
| **Instance protection** | Limited | Full control |
| **Networking** | VMSS-managed NICs | Standard NICs |
| **Fault domains** | Configurable (max 5) | Max spreading (recommended) |

```bash
# Create a VMSS in Flexible orchestration mode across Availability Zones
az vmss create \
  --resource-group myRG \
  --name web-vmss \
  --image Ubuntu2204 \
  --vm-sku Standard_B2s \
  --instance-count 3 \
  --zones 1 2 3 \
  --orchestration-mode Flexible \
  --admin-username azureuser \
  --generate-ssh-keys \
  --custom-data @cloud-init.yaml \
  --lb-sku Standard \
  --upgrade-policy-mode Automatic

# Configure autoscale rules
az monitor autoscale create \
  --resource-group myRG \
  --resource web-vmss \
  --resource-type Microsoft.Compute/virtualMachineScaleSets \
  --name web-autoscale \
  --min-count 2 \
  --max-count 20 \
  --count 3

# Scale out when CPU > 70% for 5 minutes
az monitor autoscale rule create \
  --resource-group myRG \
  --autoscale-name web-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 2

# Scale in when CPU < 30% for 10 minutes
az monitor autoscale rule create \
  --resource-group myRG \
  --autoscale-name web-autoscale \
  --condition "Percentage CPU < 30 avg 10m" \
  --scale in 1

# View VMSS instances
az vmss list-instances -g myRG -n web-vmss -o table

# View autoscale settings
az monitor autoscale show -g myRG -n web-autoscale -o json
```

---

## Azure Load Balancer: Distributing Traffic

Azure Load Balancer operates at Layer 4 (TCP/UDP) and distributes incoming traffic across healthy VM instances. There are two SKUs:

| Feature | Basic (being retired) | Standard |
| :--- | :--- | :--- |
| **Backend pool size** | Up to 300 instances | Up to 1,000 instances |
| **Health probes** | TCP, HTTP | TCP, HTTP, HTTPS |
| **Availability Zones** | Not supported | Zone-redundant or zonal |
| **SLA** | No SLA | 99.99% |
| **Security** | Open by default | Closed by default (requires NSG) |
| **Cost** | Free | ~$18/month + data processing |
| **Outbound rules** | Limited | Full control |

```bash
# The VMSS creation command above automatically creates a Standard LB.
# To create one manually:

# Create public IP for the load balancer
az network public-ip create \
  --resource-group myRG \
  --name web-lb-pip \
  --sku Standard \
  --zone 1 2 3    # Zone-redundant

# Create load balancer
az network lb create \
  --resource-group myRG \
  --name web-lb \
  --sku Standard \
  --frontend-ip-name web-frontend \
  --backend-pool-name web-backend \
  --public-ip-address web-lb-pip

# Create health probe
az network lb probe create \
  --resource-group myRG \
  --lb-name web-lb \
  --name http-probe \
  --protocol Http \
  --port 80 \
  --path /health \
  --interval 15 \
  --threshold 2

# Create load balancing rule
az network lb rule create \
  --resource-group myRG \
  --lb-name web-lb \
  --name http-rule \
  --frontend-ip-name web-frontend \
  --backend-pool-name web-backend \
  --protocol Tcp \
  --frontend-port 80 \
  --backend-port 80 \
  --probe-name http-probe \
  --idle-timeout 4 \
  --enable-tcp-reset true

# IMPORTANT: Standard LB is "secure by default" -- you MUST create an NSG
# to allow traffic, or the health probes and client traffic will be blocked.
```

---

## Did You Know?

1. **Azure VMs have a "host maintenance" event roughly every 4-6 weeks** where Azure needs to update the physical host. For most VM sizes, Azure uses memory-preserving maintenance that pauses the VM for less than 30 seconds. But for some GPU and high-performance VM sizes, a full reboot is required. You can subscribe to Scheduled Events via the Instance Metadata Service to get 15 minutes of advance warning before maintenance begins.

2. **The Standard_B1ls VM (1 vCPU, 0.5 GB RAM) costs approximately $3.80 per month** and is the cheapest VM Azure offers. It is surprisingly useful for lightweight workloads like a bastion host, a DNS forwarder, or a small cron job runner. Many teams overlook it because 0.5 GB seems too small, but for a process that uses 100 MB of RAM, it is more than enough.

3. **VM Scale Sets in Flexible orchestration mode can mix different VM sizes in the same scale set** since late 2023. This means you can have a baseline of Standard_D4s_v5 instances and burst with Standard_D4as_v5 (AMD) instances if Intel capacity is constrained. This is particularly useful during regional capacity shortages where a single VM size might not be available.

4. **When you stop (deallocate) a VM, you stop paying for compute but continue paying for the OS disk and any data disks.** A 128 GB Premium SSD costs about $19/month whether the VM is running or not. Teams that "save money" by stopping 50 VMs every night still pay $950/month for the disks. To truly eliminate disk costs, you need to delete the disks and recreate the VMs from images or snapshots.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Running production on a single VM without HA | The application "works fine" and adding redundancy seems like overkill | Use at least 2 VMs across Availability Zones behind a Standard Load Balancer. The cost is minimal compared to downtime. |
| Choosing a VM size based only on vCPU count | Developers assume "4 vCPUs = 4 vCPUs" regardless of family | Different families have different CPU architectures, clock speeds, and memory ratios. Benchmark your workload on candidate sizes before committing. |
| Using Standard HDD for production workloads | It is the cheapest option and "seems fast enough in testing" | Standard HDD has only 500 IOPS max. Under production load, disk I/O becomes the bottleneck. Use Premium SSD minimum for production. |
| Not configuring a health probe on the load balancer | The default TCP probe on the backend port "seems to work" | Use an HTTP health probe that checks your application's /health endpoint. A TCP probe only verifies the port is open, not that your app is healthy. |
| Forgetting to create an NSG when using Standard Load Balancer | Basic LB allows traffic by default, so teams assume Standard does too | Standard LB blocks all traffic unless an NSG explicitly allows it. Always create an NSG that permits traffic on the load balancer's frontend port. |
| Scaling up (bigger VM) instead of scaling out (more VMs) | Scaling up is simpler and requires no architecture changes | Scaling up hits a ceiling and creates a single point of failure. Design for horizontal scaling with VMSS from the start. |
| Using cloud-init for complex configuration that takes 15+ minutes | Cloud-init runs on first boot and there is no timeout feedback | For complex configurations, build a custom VM image with Packer or Azure Image Builder. Use cloud-init only for lightweight, last-mile configuration. |
| Not tagging VMs with cost allocation metadata | It seems like busywork during initial deployment | Without tags, you cannot attribute costs to teams or projects. Enforce tagging with Azure Policy. At minimum, tag with environment, team, and project. |

---

## Quiz

<details>
<summary>1. What is the difference between an Availability Zone and an Availability Set?</summary>

An Availability Zone is a physically separate data center within an Azure region, with independent power, cooling, and networking. VMs spread across zones are protected from entire data center failures (99.99% SLA). An Availability Set distributes VMs across Fault Domains (different racks in the same data center) and Update Domains (groups rebooted sequentially during maintenance). Availability Sets protect against rack-level failures and planned maintenance but not data center-level failures (99.95% SLA). Always prefer Availability Zones when the region supports them.
</details>

<details>
<summary>2. A B2s VM is running at 5% CPU most of the time but occasionally bursts to 100% for 2 minutes. Is this a good use case for B-series? Why?</summary>

Yes, this is an ideal B-series use case. B-series VMs accumulate CPU credits when running below their baseline (20% for B2s). During the long periods at 5% CPU, the VM is earning credits. When it bursts to 100% for 2 minutes, it spends those accumulated credits. As long as the burst duration and frequency do not exceed the credit balance, the VM performs identically to a non-burstable VM during bursts but costs 50-60% less. If the bursts were sustained for 30+ minutes or happened every few minutes, you would exhaust credits and get throttled.
</details>

<details>
<summary>3. You stop (deallocate) an Azure VM. What do you still pay for?</summary>

You continue paying for all Managed Disks attached to the VM (OS disk and data disks), any public IP addresses associated with the VM (Standard SKU public IPs are charged even when unassigned; Basic SKU IPs are not charged when unassigned), and any reserved IP addresses. You stop paying for the compute (vCPU and memory). For a VM with a 128 GB Premium SSD OS disk and a 256 GB data disk, you would still pay approximately $38/month even while the VM is deallocated.
</details>

<details>
<summary>4. Why does a Standard Load Balancer require an NSG to allow traffic, while a Basic Load Balancer does not?</summary>

Standard Load Balancer follows the "secure by default" design principle. All inbound traffic is blocked unless explicitly allowed by an NSG rule. This prevents accidental exposure of backend services. Basic Load Balancer was designed earlier with an "open by default" model where all traffic was allowed unless blocked. Microsoft recommends Standard LB for all new deployments because the secure-by-default approach aligns with zero-trust networking principles. Basic LB is being retired.
</details>

<details>
<summary>5. What is the advantage of using Flexible orchestration mode for VM Scale Sets compared to Uniform mode?</summary>

Flexible orchestration allows you to mix different VM sizes within the same scale set, add existing standalone VMs to the scale set, use standard networking features (including individual NSGs per NIC), and get better fault domain spreading. Uniform mode requires all VMs to be identical and manages networking at the VMSS level. Flexible mode is the recommended approach for all new VMSS deployments because it provides more control, better integration with other Azure services, and supports the gradual migration of existing VMs into a scale set.
</details>

<details>
<summary>6. You need to deploy a VM that runs a PostgreSQL database with high IOPS requirements (20,000+ IOPS). Which disk type should you choose and why?</summary>

Premium SSD v2 is the best choice for this scenario. Standard Premium SSD tops out at 7,500 IOPS for a single disk. Premium SSD v2 allows you to independently configure IOPS (up to 80,000) and throughput (up to 1,200 MB/s), and you only pay for what you provision. This makes it more cost-effective than Ultra Disk for most database workloads. Ultra Disk (up to 160,000 IOPS) would be overkill unless you need more than 80,000 IOPS or 4,000 MB/s throughput. You could also stripe multiple Premium SSDs using LVM/RAID, but Premium SSD v2 is simpler and often cheaper.
</details>

---

## Hands-On Exercise: HA Web Tier on VMSS Across Availability Zones with Standard LB

In this exercise, you will deploy a highly available web application using a VM Scale Set spread across three Availability Zones, with a Standard Load Balancer distributing traffic and autoscale rules based on CPU utilization.

**Prerequisites**: Azure CLI installed and authenticated.

### Task 1: Create the Resource Group and Network

```bash
RG="kubedojo-vmss-lab"
LOCATION="eastus2"

az group create --name "$RG" --location "$LOCATION"

# Create a VNet and subnet for the VMSS
az network vnet create \
  --resource-group "$RG" \
  --name web-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name web-subnet \
  --subnet-prefix 10.0.1.0/24
```

<details>
<summary>Verify Task 1</summary>

```bash
az network vnet show -g "$RG" -n web-vnet --query '{AddressSpace:addressSpace.addressPrefixes[0], Subnet:subnets[0].name}' -o table
```
</details>

### Task 2: Create a Cloud-Init Configuration

```bash
cat > /tmp/web-cloud-init.yaml << 'CLOUDINIT'
#cloud-config
package_update: true
packages:
  - nginx
  - curl

write_files:
  - path: /var/www/html/index.html
    content: |
      <!DOCTYPE html>
      <html><body>
      <h1>KubeDojo VMSS Lab</h1>
      <p>Instance: INSTANCE_ID</p>
      <p>Zone: ZONE_ID</p>
      </body></html>

  - path: /var/www/html/health
    content: "OK"

runcmd:
  - INSTANCE=$(curl -s -H Metadata:true "http://169.254.169.254/metadata/instance/compute/name?api-version=2021-02-01&format=text")
  - ZONE=$(curl -s -H Metadata:true "http://169.254.169.254/metadata/instance/compute/zone?api-version=2021-02-01&format=text")
  - sed -i "s/INSTANCE_ID/$INSTANCE/" /var/www/html/index.html
  - sed -i "s/ZONE_ID/$ZONE/" /var/www/html/index.html
  - systemctl enable nginx
  - systemctl restart nginx
CLOUDINIT
```

<details>
<summary>Verify Task 2</summary>

```bash
cat /tmp/web-cloud-init.yaml | head -5
```

You should see the cloud-config header.
</details>

### Task 3: Create the VMSS with Standard Load Balancer

```bash
az vmss create \
  --resource-group "$RG" \
  --name web-vmss \
  --image Ubuntu2204 \
  --vm-sku Standard_B2s \
  --instance-count 3 \
  --zones 1 2 3 \
  --orchestration-mode Flexible \
  --admin-username azureuser \
  --generate-ssh-keys \
  --custom-data /tmp/web-cloud-init.yaml \
  --lb-sku Standard \
  --lb web-lb \
  --vnet-name web-vnet \
  --subnet web-subnet \
  --upgrade-policy-mode Automatic
```

<details>
<summary>Verify Task 3</summary>

```bash
az vmss show -g "$RG" -n web-vmss \
  --query '{Name:name, SKU:sku.name, Capacity:sku.capacity, Zones:zones}' -o table
```

You should see 3 instances across zones 1, 2, and 3.
</details>

### Task 4: Configure NSG and Health Probe

```bash
# Get the NSG name created by VMSS
NSG_NAME=$(az network nsg list -g "$RG" --query '[0].name' -o tsv)

# Allow HTTP traffic inbound
az network nsg rule create \
  --resource-group "$RG" \
  --nsg-name "$NSG_NAME" \
  --name AllowHTTP \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes Internet \
  --destination-port-ranges 80

# Update the LB health probe to use HTTP
LB_PROBE=$(az network lb probe list -g "$RG" --lb-name web-lb --query '[0].name' -o tsv)
az network lb probe update \
  --resource-group "$RG" \
  --lb-name web-lb \
  --name "$LB_PROBE" \
  --protocol Http \
  --port 80 \
  --path /health
```

<details>
<summary>Verify Task 4</summary>

```bash
az network lb probe show -g "$RG" --lb-name web-lb -n "$LB_PROBE" \
  --query '{Protocol:protocol, Port:port, Path:requestPath}' -o table
```

You should see HTTP probe on port 80 with path /health.
</details>

### Task 5: Configure Autoscale Rules

```bash
VMSS_ID=$(az vmss show -g "$RG" -n web-vmss --query id -o tsv)

# Create autoscale setting
az monitor autoscale create \
  --resource-group "$RG" \
  --resource "$VMSS_ID" \
  --resource-type Microsoft.Compute/virtualMachineScaleSets \
  --name web-autoscale \
  --min-count 2 \
  --max-count 10 \
  --count 3

# Scale out: CPU > 70% for 5 minutes → add 2 instances
az monitor autoscale rule create \
  --resource-group "$RG" \
  --autoscale-name web-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 2

# Scale in: CPU < 25% for 10 minutes → remove 1 instance
az monitor autoscale rule create \
  --resource-group "$RG" \
  --autoscale-name web-autoscale \
  --condition "Percentage CPU < 25 avg 10m" \
  --scale in 1
```

<details>
<summary>Verify Task 5</summary>

```bash
az monitor autoscale show -g "$RG" -n web-autoscale \
  --query '{Min:profiles[0].capacity.minimum, Max:profiles[0].capacity.maximum, Default:profiles[0].capacity.default, RuleCount:profiles[0].rules|length(@)}' -o table
```

You should see min 2, max 10, default 3, and 2 rules.
</details>

### Task 6: Test the Deployment

```bash
# Get the public IP of the load balancer
LB_IP=$(az network public-ip list -g "$RG" --query '[0].ipAddress' -o tsv)
echo "Load Balancer IP: $LB_IP"

# Test the web server (run multiple times to see different instances)
for i in $(seq 1 6); do
  echo "Request $i:"
  curl -s "http://$LB_IP" | grep -o 'Instance: [^<]*\|Zone: [^<]*'
  echo "---"
done

# Check health endpoint
curl -s "http://$LB_IP/health"
```

<details>
<summary>Verify Task 6</summary>

You should see responses from different instances across different zones. The Instance and Zone values should vary as the load balancer distributes requests. The health endpoint should return "OK".
</details>

### Cleanup

```bash
az group delete --name "$RG" --yes --no-wait
```

### Success Criteria

- [ ] VMSS created with 3 instances across Availability Zones 1, 2, and 3
- [ ] Standard Load Balancer distributing HTTP traffic to VMSS instances
- [ ] HTTP health probe configured on /health endpoint
- [ ] NSG rule allowing inbound HTTP traffic from the internet
- [ ] Autoscale rules configured (scale out at 70% CPU, scale in at 25% CPU)
- [ ] curl requests to the LB IP show responses from different instances and zones

---

## Next Module

[Module 4: Azure Blob Storage & Data Lake](module-4-blob.md) --- Learn how Azure stores unstructured data at massive scale, from hot-tier serving to cold archival, with SAS tokens and identity-based access control.
