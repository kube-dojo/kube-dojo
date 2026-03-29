---
title: "Module 1.3: Elastic Compute Cloud (EC2) & Compute Foundations"
slug: cloud/aws-essentials/module-1.3-ec2
sidebar:
  order: 4
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: Module 1.2

## Why This Module Matters

In late 2021, an e-commerce startup launched their highly anticipated Black Friday sale. They had built their application on large EC2 instances and anticipated heavy traffic, so they provisioned twenty massive servers manually the night before. However, the traffic surge was three times larger than expected. The servers hit 100% CPU utilization within minutes. By the time the engineering team logged in, spun up new instances manually, installed the application dependencies, and registered them with the load balancer, two hours had passed. The website was unresponsive, carts were abandoned, and the startup lost an estimated two million dollars in sales.

This disaster was entirely preventable. The engineers treated their cloud servers like physical hardware—static, precious, and requiring manual care. They failed to leverage the "Elastic" in Elastic Compute Cloud.

Amazon EC2 is not just virtual machines in the cloud; it is a programmable compute fabric. When used correctly, EC2 allows your infrastructure to expand and contract dynamically based on real-time demand, ensuring you have enough capacity to handle spikes without paying for idle servers during quiet periods. In this module, you will learn how to automate server provisioning using AMIs and User Data, understand the underlying storage mechanics with EBS, and combine Auto Scaling Groups with Application Load Balancers to build self-healing, highly available compute clusters that scale without human intervention. You will learn to treat servers as ephemeral commodities, not permanent pets.

## The Building Blocks of Compute

To launch an EC2 instance, you must make a series of configuration choices that define its performance profile, cost, and lifecycle. Each choice has trade-offs. Understanding those trade-offs is what separates someone who "uses EC2" from someone who architects with it.

### Instance Types and Families

AWS offers hundreds of instance types optimized to fit different use cases. They are categorized by family:
*   **General Purpose (e.g., t3, m6i)**: Balanced compute, memory, and network resources. Good for web servers, code repositories, and small to medium databases. T-series instances are "burstable"—they accumulate CPU credits during idle time and spend them during bursts. If your application has steady moderate usage with occasional spikes, T-series can be significantly cheaper than fixed-performance instances.
*   **Compute Optimized (e.g., c6i, c6g)**: High ratio of vCPUs to memory. Ideal for batch processing, media transcoding, scientific modeling, machine learning inference, and high-performance web servers that need raw CPU horsepower.
*   **Memory Optimized (e.g., r6i, x2idn)**: Designed for workloads that process large data sets in memory, such as relational databases, Redis/Memcached caches, in-memory analytics, and real-time big data processing with Apache Spark.
*   **Storage Optimized (e.g., i3, d3)**: High sequential read/write access to very large data sets on local storage. Designed for data warehousing, distributed file systems (HDFS), and log processing systems.
*   **Accelerated Computing (e.g., p4d, g5)**: Use hardware accelerators (GPUs or custom chips) for floating-point calculations, graphics processing, or machine learning model training.

#### Decoding the Instance Name

An instance name like `m6i.xlarge` follows a consistent naming scheme:

```text
m    6    i    .    xlarge
|    |    |         |
|    |    |         +-- Size (nano, micro, small, medium, large, xlarge, 2xlarge...)
|    |    +------------ Additional attribute (i = Intel, g = Graviton, a = AMD, d = local NVMe)
|    +----------------- Generation (higher = newer, better price-performance)
+---------------------- Family (m = general, c = compute, r = memory, t = burstable)
```

Understanding the naming convention lets you read any instance type at a glance, even ones you have never encountered before.

### Instance Type Comparison Table

The table below compares commonly used instance types across the four most popular families. Prices shown are approximate On-Demand hourly rates in `us-east-1` as of 2025 and will vary over time.

| Instance Type | Family | vCPUs | Memory (GiB) | Network (Gbps) | On-Demand $/hr | Best Use Cases |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `t3.micro` | Burstable GP | 2 | 1 | Up to 5 | ~$0.0104 | Dev/test, microservices, low-traffic sites |
| `t3.medium` | Burstable GP | 2 | 4 | Up to 5 | ~$0.0416 | Small web apps, CI/CD agents, staging environments |
| `t3.xlarge` | Burstable GP | 4 | 16 | Up to 5 | ~$0.1664 | Medium web apps, small databases, application servers |
| `m6i.large` | General Purpose | 2 | 8 | Up to 12.5 | ~$0.096 | Production web servers, mid-size databases, backend APIs |
| `m6i.xlarge` | General Purpose | 4 | 16 | Up to 12.5 | ~$0.192 | App servers, enterprise applications, container hosts |
| `m6i.2xlarge` | General Purpose | 8 | 32 | Up to 12.5 | ~$0.384 | Large application servers, medium databases, EKS nodes |
| `c6i.large` | Compute Optimized | 2 | 4 | Up to 12.5 | ~$0.085 | Batch processing, build servers, game servers |
| `c6i.xlarge` | Compute Optimized | 4 | 8 | Up to 12.5 | ~$0.170 | Video encoding, scientific computing, ML inference |
| `c6i.2xlarge` | Compute Optimized | 8 | 16 | Up to 12.5 | ~$0.340 | High-perf computing, ad serving, real-time analytics |
| `r6i.large` | Memory Optimized | 2 | 16 | Up to 12.5 | ~$0.126 | Redis/Memcached, small in-memory DBs |
| `r6i.xlarge` | Memory Optimized | 4 | 32 | Up to 12.5 | ~$0.252 | PostgreSQL/MySQL, medium caches, real-time analytics |
| `r6i.2xlarge` | Memory Optimized | 8 | 64 | Up to 12.5 | ~$0.504 | Large relational databases, Elasticsearch, SAP HANA |

**Key insight**: Notice how `t3.medium` and `m6i.large` both offer 2 vCPUs—but the `m6i.large` provides 8 GiB of memory (double the `t3.medium`'s 4 GiB at the same vCPU count) and consistent performance without credit-based throttling. For production workloads that need reliable performance, General Purpose M-series instances usually make more sense than burstable T-series, despite the slightly higher hourly cost.

*Note on Graviton: Instance families ending in 'g' (like m6g, c6g, r6g) use AWS Graviton processors (ARM architecture) rather than x86. They generally offer 20-40% better price-performance ratios compared to their Intel equivalents. If your application stack supports ARM (most Linux workloads, containers, and interpreted languages do), Graviton instances are almost always the smarter choice.*

### Purchasing Options

How you pay for compute dramatically impacts your architecture and your monthly bill. Choosing the wrong purchasing model for a workload is one of the easiest ways to burn money in AWS.

*   **On-Demand**: Pay for compute capacity by the second with no long-term commitments. Most expensive, but maximum flexibility. Use for spiky, unpredictable workloads and applications that cannot be interrupted.
*   **Reserved Instances (RIs)**: Commit to a specific instance type in a specific region for a 1-year or 3-year term. Offers significant discounts compared to On-Demand. Standard RIs can be sold in the Reserved Instance Marketplace if your needs change.
*   **Savings Plans**: A more flexible alternative to RIs. Instead of committing to a specific instance type, you commit to a consistent amount of usage measured in dollars per hour (e.g., "$10/hour of compute for 1 year"). This commitment applies across any instance family, size, OS, or region. Typically the best default choice for steady-state workloads.
*   **Spot Instances**: Request spare Amazon EC2 computing capacity at steep discounts. The catch? AWS can reclaim the instance with a 2-minute warning if capacity is needed elsewhere. Use for stateless, fault-tolerant, flexible workloads (e.g., image processing queues, CI/CD runners, big data analytics).
*   **Dedicated Hosts**: A physical EC2 server dedicated for your use. Required for licensing models that require per-socket or per-core visibility (e.g., Windows Server, Oracle Database), or for compliance requirements that prohibit multi-tenant hardware.

#### Purchasing Options Comparison Table

| Option | Discount vs On-Demand | Commitment | Interruption Risk | Best For |
| :--- | :---: | :--- | :---: | :--- |
| **On-Demand** | 0% (baseline) | None | None | Unpredictable workloads, short-term projects |
| **Savings Plan (1yr)** | ~30-40% | $/hr for 1 year | None | Steady-state production workloads |
| **Savings Plan (3yr)** | ~50-60% | $/hr for 3 years | None | Long-running stable infrastructure |
| **Reserved Instance (1yr, All Upfront)** | ~40% | Specific instance, 1 year | None | Known, fixed-size workloads |
| **Reserved Instance (3yr, All Upfront)** | ~60-72% | Specific instance, 3 years | None | Databases, core infrastructure |
| **Spot Instances** | ~60-90% | None | **Yes** (2-min warning) | Batch jobs, CI/CD, data processing |
| **Dedicated Hosts** | Varies | 1 or 3 years (or On-Demand) | None | License compliance, regulatory isolation |

**Cost example**: A single `m6i.xlarge` running 24/7 for a year at On-Demand rates costs approximately $0.192/hr x 8,760 hrs = **$1,682/year**. With a 3-year Savings Plan (all upfront), that same compute drops to roughly **$672/year**—a 60% savings. With Spot pricing (assuming ~70% average discount), an equivalent workload costs roughly **$504/year**, but you must design for interruptions.

*The golden rule of EC2 cost optimization: use Savings Plans for your baseline, On-Demand for unpredictable burst, and Spot for anything that can tolerate interruption. Never run a stable production workload on pure On-Demand for more than a few weeks without evaluating a commitment.*

### Storage: Elastic Block Store (EBS)

While instances have temporary local storage (Instance Store), persistent storage requires Amazon EBS. EBS volumes are network-attached block storage drives that persist independently from the life of an instance. Think of them as USB drives you can plug into any server in the same Availability Zone.

*   **gp3 (General Purpose SSD)**: The default for most workloads. Provides a baseline of 3,000 IOPS and 125 MiB/s throughput, with the ability to provision up to 16,000 IOPS and 1,000 MiB/s independently of storage capacity. This decoupling is a major improvement over gp2, which tied IOPS directly to volume size.
*   **gp2 (General Purpose SSD, Legacy)**: The previous generation. IOPS scale with volume size (3 IOPS per GiB). Still widely used, but gp3 is almost always cheaper and more flexible for new deployments.
*   **io2 Block Express (Provisioned IOPS SSD)**: Designed for mission-critical, high-performance databases requiring sub-millisecond latency and up to 256,000 IOPS. Expensive, but necessary for I/O-intensive transactional workloads.
*   **st1 (Throughput Optimized HDD)**: Low-cost magnetic storage optimized for large sequential workloads like log processing, data warehousing, and streaming. Cannot be a boot volume.
*   **sc1 (Cold HDD)**: The lowest-cost option, designed for infrequently accessed data. Cannot be a boot volume.

#### EBS Snapshots

You can create point-in-time backups of EBS volumes, which are stored incrementally in Amazon S3. The first snapshot captures the entire volume; subsequent snapshots only capture changed blocks, making them storage-efficient.

Key capabilities:
*   **Cross-AZ**: Use a snapshot to create a new volume in any AZ within the same region.
*   **Cross-Region**: Copy a snapshot to another region for disaster recovery.
*   **Sharing**: Share snapshots with other AWS accounts.
*   **Fast Snapshot Restore (FSR)**: Pre-warm a snapshot so that volumes created from it deliver full performance immediately, without the usual first-access latency penalty.

```bash
# Create a snapshot of an EBS volume
aws ec2 create-snapshot \
    --volume-id vol-0123456789abcdef0 \
    --description "Daily backup - production DB" \
    --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=prod-db-daily}]'

# List snapshots you own
aws ec2 describe-snapshots --owner-ids self \
    --query 'Snapshots[*].[SnapshotId,VolumeId,StartTime,State]' \
    --output table

# Create a volume from a snapshot in a different AZ
aws ec2 create-volume \
    --snapshot-id snap-0123456789abcdef0 \
    --availability-zone us-east-1b \
    --volume-type gp3
```

## Automating the Boot Process: AMIs and User Data

If you are logging into a server to run `apt-get install` or modify configuration files manually, you are creating a "pet." In cloud architecture, we want "cattle"—servers that are easily replaceable and identical. The distinction matters enormously: when a pet gets sick, you nurse it back to health; when cattle gets sick, you replace it with a healthy one. Auto Scaling only works if every instance is interchangeable.

### Amazon Machine Images (AMIs)

An AMI provides the information required to launch an instance. It includes the operating system, the architecture type (x86 or ARM), and a snapshot of the root volume.

Instead of configuring a server from scratch every time, a common pattern is "Golden Image" baking:
1. Launch a base Linux AMI.
2. Install your application, security agents, and dependencies.
3. Create a custom AMI from that instance.
4. Launch all future instances directly from your custom AMI—they boot in seconds, fully configured.

```bash
# Find the latest Amazon Linux 2023 AMI
aws ssm get-parameters \
    --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
    --query 'Parameters[0].Value' --output text

# Find the latest Ubuntu 22.04 AMI
aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text

# Create a custom AMI from a running instance
aws ec2 create-image \
    --instance-id i-0123456789abcdef0 \
    --name "MyApp-GoldenImage-$(date +%Y%m%d)" \
    --description "App v2.3 with security agents" \
    --no-reboot

# List your custom AMIs
aws ec2 describe-images --owners self \
    --query 'Images[*].[ImageId,Name,CreationDate]' \
    --output table
```

**Golden Image pipeline in practice**: Production teams typically automate this with HashiCorp Packer or EC2 Image Builder. A CI/CD pipeline builds a new AMI nightly (or on every application release), tests it, and updates the Launch Template. The ASG then gradually rolls out instances using the new AMI.

### User Data and Cloud-Init

If you don't want to bake a custom AMI for every minor configuration change, use **User Data**.

When launching an instance, you can pass a shell script in the User Data field. The `cloud-init` service running on the EC2 instance executes this script with root privileges during the final stages of the initial boot process. It is the perfect place to fetch the latest application code from S3, start services, or register the instance with a configuration management tool.

```bash
#!/bin/bash
# Example User Data script
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Deployed via User Data</h1>" > /var/www/html/index.html
```

A more production-ready User Data script that fetches configuration from Parameter Store and signals success:

```bash
#!/bin/bash
set -euo pipefail

# Log everything for debugging
exec > >(tee /var/log/user-data.log) 2>&1
echo "User Data script started at $(date)"

# Install application
yum update -y
yum install -y httpd aws-cli jq

# Fetch configuration from Parameter Store
APP_VERSION=$(aws ssm get-parameter --name /myapp/version --query 'Parameter.Value' --output text --region us-east-1)
DB_ENDPOINT=$(aws ssm get-parameter --name /myapp/db-endpoint --query 'Parameter.Value' --output text --region us-east-1)

# Download application from S3
aws s3 cp "s3://my-deploy-bucket/releases/${APP_VERSION}/app.tar.gz" /tmp/
tar -xzf /tmp/app.tar.gz -C /var/www/html/

# Write config file
cat << CONF > /var/www/html/config.json
{
    "db_endpoint": "$DB_ENDPOINT",
    "app_version": "$APP_VERSION"
}
CONF

# Start web server
systemctl start httpd
systemctl enable httpd

echo "User Data script completed at $(date)"
```

**Debugging tip**: If your User Data script fails silently, SSH into the instance and check `/var/log/cloud-init-output.log`. This file contains the stdout and stderr of your script. Alternatively, add explicit logging as shown above.

### Golden Image vs. User Data: When to Use Which

| Approach | Boot Time | Flexibility | Maintenance | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Golden AMI** | Fast (seconds) | Low — rebuild to change | AMI pipeline needed | Stable base, infrequent changes |
| **User Data only** | Slow (minutes) | High — change at launch | Simple script | Rapid iteration, dev/test |
| **Hybrid (recommended)** | Medium | Balanced | Both pipelines | Production: AMI for base + User Data for config |

The hybrid approach is what most production teams adopt. Bake the OS, security agents, and application runtime into the AMI (things that rarely change). Use User Data to pull the latest application version and environment-specific configuration at boot time (things that change frequently).

## Scaling the Fleet: ASG and ALB

A single EC2 instance is a single point of failure. Modern architectures distribute load across a fleet of instances. The combination of an Application Load Balancer and an Auto Scaling Group is the fundamental pattern for highly available compute in AWS.

### Architecture Overview

```text
                          Internet
                             |
                    +--------+--------+
                    | Application     |
                    | Load Balancer   |
                    | (ALB)           |
                    +--------+--------+
                             |
             +---------------+---------------+
             |               |               |
     +-------+------+ +-----+------+ +------+-------+
     | Target Group | | Target     | | Target       |
     | Instance A   | | Group      | | Group        |
     | (AZ-1a)      | | Instance B | | Instance C   |
     |              | | (AZ-1b)    | | (AZ-1a)      |
     +--------------+ +------------+ +--------------+
             |               |               |
             +---------------+---------------+
                             |
                    +--------+--------+
                    | Auto Scaling    |
                    | Group (ASG)     |
                    |                 |
                    | Min: 2          |
                    | Desired: 3      |
                    | Max: 10         |
                    |                 |
                    | Launch Template |
                    | - AMI           |
                    | - Instance Type |
                    | - Security Grp  |
                    | - User Data     |
                    +-----------------+

    Scaling Policy (CloudWatch):
    - CPU > 70% for 3 min  --> Add 2 instances
    - CPU < 30% for 10 min --> Remove 1 instance
```

### Application Load Balancer (ALB)

An ALB operates at Layer 7 (HTTP/HTTPS). It receives incoming traffic and distributes it across multiple targets (like EC2 instances) in multiple Availability Zones. ALBs are themselves highly available—AWS runs them across multiple AZs behind the scenes.

Key features:

*   **Health Checks**: The ALB constantly polls a specific endpoint (e.g., `/health`) on your instances. If an instance fails the check, the ALB stops sending traffic to it until it recovers. You configure the path, port, protocol, healthy/unhealthy thresholds, and check interval.
*   **Path-Based Routing**: ALBs can inspect the URL path to route traffic to different target groups. For example, `/api/*` goes to backend instances while `/images/*` goes to a separate rendering fleet.
*   **Host-Based Routing**: Route traffic based on the `Host` header. A single ALB can serve `api.example.com`, `app.example.com`, and `admin.example.com`, each routing to a different target group.
*   **Sticky Sessions**: When enabled, the ALB uses a cookie to route a user's requests to the same target for the duration of their session. Useful for stateful applications, but consider externalizing session state to ElastiCache or DynamoDB instead.
*   **Connection Draining**: When a target is deregistered (e.g., during scale-in or deployment), the ALB waits for in-flight requests to complete before fully removing it. The default deregistration delay is 300 seconds.

```bash
# Create a target group with custom health check settings
aws elbv2 create-target-group \
    --name MyApp-TG \
    --protocol HTTP --port 80 \
    --vpc-id vpc-0123456789abcdef0 \
    --health-check-path /health \
    --health-check-interval-seconds 15 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --query 'TargetGroups[0].TargetGroupArn' --output text

# Check the health of targets in a target group
aws elbv2 describe-target-health \
    --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/MyApp-TG/abc123 \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Description]' \
    --output table
```

### Auto Scaling Groups (ASG)

An ASG contains a collection of EC2 instances that are treated as a logical grouping for automatic scaling and management.

You define a **Launch Template** (specifying the AMI, instance type, security groups, and user data) and attach it to the ASG.

The ASG monitors the health of its instances and ensures the group maintains a specified state:
*   **Self-Healing (Desired Capacity)**: If you set Desired Capacity to 3, and an instance crashes or is terminated, the ASG automatically launches a replacement using the Launch Template to bring the count back to 3.
*   **Dynamic Scaling**: You can configure scaling policies tied to CloudWatch metrics. For example: "If average CPU utilization exceeds 70% for 3 minutes, launch 2 more instances. If it drops below 30%, terminate 1 instance."
*   **Predictive Scaling**: AWS can analyze historical traffic patterns and proactively scale the fleet before a predicted traffic surge, rather than reacting after the fact. Useful for workloads with predictable daily or weekly patterns.
*   **Scheduled Scaling**: If you know traffic spikes every weekday at 9 AM, you can pre-schedule scale-out actions. Cheaper and more responsive than reactive scaling.

When an ASG is linked to an ALB, newly launched instances are automatically registered with the load balancer and begin receiving traffic as soon as they pass health checks.

#### Scaling Policies in Depth

```bash
# Create a Target Tracking scaling policy (the simplest and most common)
# This policy keeps average CPU at ~60% by adding/removing instances automatically
aws autoscaling put-scaling-policy \
    --auto-scaling-group-name DojoWebASG \
    --policy-name TargetCPU60 \
    --policy-type TargetTrackingScaling \
    --target-tracking-configuration '{
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ASGAverageCPUUtilization"
        },
        "TargetValue": 60.0,
        "ScaleInCooldown": 300,
        "ScaleOutCooldown": 60
    }'

# Create a scaling policy based on ALB request count per target
aws autoscaling put-scaling-policy \
    --auto-scaling-group-name DojoWebASG \
    --policy-name TargetRequestCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-configuration '{
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ALBRequestCountPerTarget",
            "ResourceLabel": "app/DojoWebALB/abc123/targetgroup/DojoWebTG/def456"
        },
        "TargetValue": 1000.0
    }'

# View current scaling activities
aws autoscaling describe-scaling-activities \
    --auto-scaling-group-name DojoWebASG \
    --query 'Activities[*].[StartTime,StatusCode,Description]' \
    --output table --max-items 5
```

**Cooldown periods matter**: The `ScaleOutCooldown` (default 300s) prevents the ASG from launching a storm of new instances before the previous batch has had time to warm up and reduce load. Setting it too low causes thrashing; setting it too high causes sluggish response. For web apps behind an ALB, 60-120 seconds for scale-out and 300 seconds for scale-in is a reasonable starting point.

## EC2 Lifecycle Management with the CLI

Beyond launching and terminating instances, the AWS CLI gives you full lifecycle control. Here are operations you will use regularly.

```bash
# Launch a single instance with detailed configuration
aws ec2 run-instances \
    --image-id ami-0123456789abcdef0 \
    --instance-type t3.medium \
    --key-name my-keypair \
    --security-group-ids sg-0123456789abcdef0 \
    --subnet-id subnet-0123456789abcdef0 \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=WebServer-01},{Key=Environment,Value=Production}]' \
    --user-data file://userdata.sh \
    --iam-instance-profile Name=WebServerRole \
    --query 'Instances[0].InstanceId' --output text

# List running instances with useful details
aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,PrivateIpAddress,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' \
    --output table

# Stop an instance (EBS data preserved, public IP released unless Elastic IP)
aws ec2 stop-instances --instance-ids i-0123456789abcdef0

# Start a stopped instance
aws ec2 start-instances --instance-ids i-0123456789abcdef0

# Resize an instance (must be stopped first)
aws ec2 stop-instances --instance-ids i-0123456789abcdef0
aws ec2 wait instance-stopped --instance-ids i-0123456789abcdef0
aws ec2 modify-instance-attribute \
    --instance-id i-0123456789abcdef0 \
    --instance-type '{"Value": "m6i.xlarge"}'
aws ec2 start-instances --instance-ids i-0123456789abcdef0

# Terminate an instance (permanent — EBS root volume deleted by default)
aws ec2 terminate-instances --instance-ids i-0123456789abcdef0

# Connect to an instance via SSM (no SSH key or open port 22 required)
aws ssm start-session --target i-0123456789abcdef0
```

## Instance Metadata Service (IMDS)

Every EC2 instance has access to a special HTTP endpoint at `169.254.169.254` that provides information about the instance itself. This metadata is invaluable for bootstrapping scripts that need to know "who am I?" and "where am I?"

```bash
# IMDSv2 (token-based, more secure — always use this)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Get basic instance identity
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4

# Get the IAM role credentials (never hardcode creds — use this instead)
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/MyInstanceRole
```

**Security note**: Always enforce IMDSv2 (token-based) and disable IMDSv1. The older IMDSv1 is vulnerable to Server-Side Request Forgery (SSRF) attacks, which is exactly how the 2019 Capital One breach occurred. An attacker exploited a misconfigured WAF to query the metadata service and steal IAM role credentials.

```bash
# Enforce IMDSv2 on an existing instance
aws ec2 modify-instance-metadata-options \
    --instance-id i-0123456789abcdef0 \
    --http-tokens required \
    --http-endpoint enabled

# Enforce IMDSv2 in a Launch Template
aws ec2 create-launch-template \
    --launch-template-name SecureTemplate \
    --launch-template-data '{
        "MetadataOptions": {
            "HttpTokens": "required",
            "HttpEndpoint": "enabled",
            "HttpPutResponseHopLimit": 1
        }
    }'
```

## Did You Know?

1.  Amazon EC2 Mac instances actually utilize physically unmodified Apple Mac mini computers integrated directly into the AWS Nitro System, allowing developers to natively run macOS workloads in the cloud for iOS application compilation. You rent the entire physical Mac mini for a minimum of 24 hours.
2.  If you use an Elastic IP (EIP) address and it is attached to a running EC2 instance, it is free. However, if you reserve an EIP and let it sit idle (unattached), AWS charges you an hourly fee to prevent IPv4 address hoarding. As of February 2024, AWS also charges $0.005/hr for *every* public IPv4 address, even those actively attached to running instances—a change that caught many teams off guard.
3.  The AWS Nitro System is a combination of dedicated hardware and a lightweight hypervisor. It offloads network, storage, and security functions to dedicated custom chips, delivering nearly all of the server's compute and memory resources directly to your instances, eliminating traditional hypervisor overhead. Pre-Nitro instances (like m4, c4) lost 5-10% of resources to the hypervisor.
4.  A single Auto Scaling Group can use mixed instance types and mixed purchasing options simultaneously. You can configure an ASG to run 60% On-Demand (for baseline capacity) and 40% Spot (for cost-optimized burst capacity) across multiple instance families, letting AWS pick the cheapest available Spot option at any given moment. This "instance diversification" strategy dramatically reduces the chance of Spot interruptions.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Losing data on termination** | By default, the root EBS volume is set to "Delete on Termination". Engineers assume stopping is the same as terminating. | Store critical, persistent data on a secondary EBS volume with `DeleteOnTermination=false`, or design applications to be stateless and store data in RDS or S3. |
| **Hardcoding IP addresses** | Legacy applications expect static IPs for internal communication, or developers note down instance IPs in config files. | In an Auto Scaling environment, IPs change constantly. Use internal load balancers, service discovery (Cloud Map), or Route 53 private hosted zones. |
| **Storing AWS credentials on EC2** | Developers put `~/.aws/credentials` on the server so their scripts work, or bake access keys into AMIs. | This is a massive security risk. Always attach an IAM Role (Instance Profile) to the EC2 instance to provide secure, temporary credentials that rotate automatically. |
| **Ignoring Spot Instances for stateless workloads** | "We just use On-Demand for everything because it is simpler." | CI/CD build agents, batch processing jobs, and worker queues are inherently interruptible. Using Spot instances for these workloads can slash compute costs by 60-90%. |
| **Baking secrets into AMIs** | Setting passwords or API keys during the image build process because it "keeps things simple." | Anyone who can launch the AMI has the secrets. Inject secrets at runtime using User Data scripts that fetch them from AWS Secrets Manager or Systems Manager Parameter Store. |
| **Failing to configure ASG health checks** | The ASG relies on standard EC2 status checks, which only verify if the VM is running, not if the application is healthy. | Configure the ASG to use ELB Health Checks. If the web server crashes but the VM stays up, the ASG will terminate and replace the zombie instance. |
| **Using IMDSv1 instead of IMDSv2** | IMDSv1 is the legacy default and "just works" without tokens. Teams never update the setting. | Enforce IMDSv2 (`http-tokens required`) on all instances and in all Launch Templates. IMDSv1 is vulnerable to SSRF attacks that can leak IAM credentials. |
| **Not setting a Health Check Grace Period** | The ASG starts health checking immediately after launch, before the application has finished bootstrapping. | Set `--health-check-grace-period` to at least the time your User Data script takes to complete (typically 120-300 seconds). Without this, the ASG terminates healthy instances that are still booting. |

## Quiz

<details>
<summary>Question 1: You need to design an architecture for a video rendering application. The rendering jobs are pulled from an SQS queue. If a server goes offline mid-render, the job simply returns to the queue to be picked up by another server. The rendering requires significant CPU power but has a tight budget. What EC2 purchasing option is best?</summary>
Spot Instances. Because the workload is completely stateless, fault-tolerant, and driven by a queue, it perfectly handles the 2-minute interruption notice of Spot instances. This provides access to powerful compute resources (like C6i instances) at a fraction of the On-Demand cost. To further reduce interruption risk, configure the fleet to diversify across multiple instance types (c6i, c5, c5a, c6g) and multiple Availability Zones.
</details>

<details>
<summary>Question 2: You launch an EC2 instance with a User Data script that updates the OS packages and installs Node.js. An hour later, you stop the instance and start it again. Will the User Data script run a second time?</summary>
No. By default, the `cloud-init` User Data script only executes once per instance lifecycle, specifically during the very first boot. Stopping and starting the instance does not re-trigger it. If you need a script to run on every boot, you must use a cloud-init `#cloud-boothook` or place the script in `/var/lib/cloud/scripts/per-boot/`.
</details>

<details>
<summary>Question 3: Your Auto Scaling Group has a Minimum capacity of 2, a Maximum of 10, and a Desired capacity of 4. An Availability Zone experiences a localized failure, bringing down two of your instances. What will the Auto Scaling Group do?</summary>
The ASG health checks will detect that two instances have failed. Because the Desired capacity is set to 4, the ASG will automatically launch two new instances in the remaining healthy Availability Zones to restore the fleet count to the desired state. The ASG also performs AZ rebalancing, so once the failed AZ recovers, new instances may be launched there during subsequent scaling activities to restore even distribution.
</details>

<details>
<summary>Question 4: You attach an EBS volume to an EC2 instance in `us-east-1a`. You take a snapshot of the volume. A few days later, the instance is terminated. Can you use the snapshot to create a new volume for an instance in `us-east-1b`?</summary>
Yes. While EBS volumes are tied to a specific Availability Zone, EBS snapshots are stored regionally in Amazon S3. You can use a snapshot taken in `us-east-1a` to instantly provision a new volume in `us-east-1b` (or any other AZ within the `us-east-1` region). You can even copy the snapshot to a different region entirely.
</details>

<details>
<summary>Question 5: What is the primary operational benefit of using a Launch Template over a legacy Launch Configuration for an Auto Scaling Group?</summary>
Launch Templates support versioning. You can create a new version of a template (e.g., updating the AMI ID to a newly patched image) and update the ASG to use the new version, or set it to always use the "Latest" version. Legacy Launch Configurations were immutable; changing anything required creating an entirely new configuration and updating the ASG. Launch Templates also support additional features like mixed instance types, Spot/On-Demand mix, and multiple network interfaces.
</details>

<details>
<summary>Question 6: An Application Load Balancer is routing traffic to a target group of EC2 instances. One instance suddenly starts returning HTTP 500 errors due to a memory leak in the application. How does the ALB handle this?</summary>
Assuming the ALB health check is configured to look for an HTTP 200 response on a specific path, the ALB will notice the instance failing health checks after the configured unhealthy threshold is exceeded. It will mark the instance as "Unhealthy" and immediately stop routing new user traffic to it, directing all traffic to the remaining healthy instances. If the ASG uses ELB health checks, it will then terminate the unhealthy instance and launch a replacement.
</details>

<details>
<summary>Question 7: You have a production web application running on m6i.large instances. Traffic is very predictable: low overnight, ramps up at 8 AM, peaks at noon, and drops off at 6 PM. What scaling strategy should you use?</summary>
Use a combination of Scheduled Scaling and Target Tracking. Configure a scheduled action to scale out before 8 AM (e.g., increase desired capacity from 2 to 6 at 7:45 AM) and scale in at 6 PM. Layer a Target Tracking policy on top (targeting 60% CPU utilization) to handle any unexpected traffic deviations. Scheduled scaling handles the predictable pattern; target tracking handles the unpredictable variance.
</details>

<details>
<summary>Question 8: A developer creates a custom AMI that includes their application and all dependencies. They share this AMI with another AWS account. The second account launches an instance from this AMI, but it fails with a "snapshot not found" error. What went wrong?</summary>
The AMI references EBS snapshots. When sharing an AMI across accounts, you must also share the underlying EBS snapshots that the AMI references. If the AMI's EBS snapshots are not shared (or if they are encrypted with a KMS key that the other account does not have permission to use), the launch will fail. The fix is to share both the AMI and its associated snapshots, and if encrypted, grant the target account access to the KMS key.
</details>

## Hands-On Exercise: Auto-Scaling Web Fleet

In this exercise, we will create a Launch Template with a bootstrapping script, and deploy it behind an Application Load Balancer using an Auto Scaling Group. You will then generate load to trigger scaling and observe the ASG in action.

*(Prerequisite: You need the VPC and Subnet IDs from Module 1.2. We will assume standard default VPC if you deleted them).*

### Task 1: Create the User Data Script and Security Group
First, we define what the instance will look like and how it behaves on boot.

```bash
# Get Default VPC
VPC_ID=$(aws ec2 describe-vpcs --filter "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)
echo "VPC: $VPC_ID"

# Create a Security Group for the ALB (allow port 80 from the internet)
ALB_SG=$(aws ec2 create-security-group \
    --group-name DojoALB-SG \
    --description "Allow HTTP to ALB" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0

# Create a Security Group for web servers (allow port 80 ONLY from the ALB SG)
WEB_SG=$(aws ec2 create-security-group \
    --group-name DojoWeb-SG \
    --description "Allow HTTP from ALB only" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress \
    --group-id $WEB_SG --protocol tcp --port 80 --source-group $ALB_SG

echo "ALB SG: $ALB_SG"
echo "Web SG: $WEB_SG"

# Create the bootstrap script
cat << 'USERDATA' > userdata.sh
#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/user-data.log) 2>&1

yum update -y
yum install -y httpd stress-ng

# Enable and start Apache
systemctl start httpd
systemctl enable httpd

# Get instance metadata (IMDSv2)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/instance-id)
AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/placement/availability-zone)
INSTANCE_TYPE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/instance-type)

# Create a web page that identifies this specific instance
cat << HTML > /var/www/html/index.html
<!DOCTYPE html>
<html>
<head><title>KubeDojo EC2 Lab</title></head>
<body style="font-family: Arial; padding: 40px; text-align: center;">
    <h1>Hello from EC2!</h1>
    <table style="margin: auto; text-align: left;">
        <tr><td><strong>Instance ID:</strong></td><td>$INSTANCE_ID</td></tr>
        <tr><td><strong>Availability Zone:</strong></td><td>$AZ</td></tr>
        <tr><td><strong>Instance Type:</strong></td><td>$INSTANCE_TYPE</td></tr>
        <tr><td><strong>Boot Time:</strong></td><td>$(date)</td></tr>
    </table>
</body>
</html>
HTML

# Create a health check endpoint
echo "OK" > /var/www/html/health

echo "User Data completed successfully at $(date)"
USERDATA
```

### Task 2: Create the Launch Template
A Launch Template defines the blueprint for the ASG.

```bash
# Find the latest Amazon Linux 2023 AMI
AMI_ID=$(aws ssm get-parameters \
    --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
    --query 'Parameters[0].Value' --output text)
echo "AMI: $AMI_ID"

# Create Launch Template data (base64 encode the userdata)
cat << EOF > template-data.json
{
    "ImageId": "$AMI_ID",
    "InstanceType": "t3.micro",
    "SecurityGroupIds": ["$WEB_SG"],
    "UserData": "$(base64 -i userdata.sh)",
    "MetadataOptions": {
        "HttpTokens": "required",
        "HttpEndpoint": "enabled"
    },
    "TagSpecifications": [
        {
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Name", "Value": "DojoWeb"},
                {"Key": "Project", "Value": "KubeDojo-EC2-Lab"}
            ]
        }
    ]
}
EOF

# Create the Launch Template
aws ec2 create-launch-template \
    --launch-template-name DojoWebTemplate \
    --version-description "v1-initial" \
    --launch-template-data file://template-data.json
```

### Task 3: Create the Load Balancer Infrastructure
Before creating the ASG, we need a target group and the ALB itself.

```bash
# Get Subnet IDs for the Default VPC (need at least 2 AZs)
SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=default-for-az,Values=true" \
    --query 'Subnets[0:2].SubnetId' --output text)
SUBNET_1=$(echo $SUBNETS | awk '{print $1}')
SUBNET_2=$(echo $SUBNETS | awk '{print $2}')
echo "Subnet 1: $SUBNET_1"
echo "Subnet 2: $SUBNET_2"

# Create Target Group with custom health check
TG_ARN=$(aws elbv2 create-target-group \
    --name DojoWebTG \
    --protocol HTTP --port 80 \
    --vpc-id $VPC_ID \
    --health-check-path /health \
    --health-check-interval-seconds 15 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --query 'TargetGroups[0].TargetGroupArn' --output text)
echo "Target Group: $TG_ARN"

# Create ALB (Internet-facing)
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name DojoWebALB \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $ALB_SG \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text)
echo "ALB: $ALB_ARN"

# Wait for ALB to provision (takes ~2 mins)
echo "Waiting for ALB to become active..."
aws elbv2 wait load-balancer-available --load-balancer-arns $ALB_ARN

# Create Listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN

# Get ALB DNS Name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --query 'LoadBalancers[0].DNSName' --output text)
echo "ALB DNS: http://$ALB_DNS"
```

### Task 4: Create the Auto Scaling Group
Link the Launch Template to the Target Group.

```bash
# Create ASG spanning two subnets, desired capacity 2
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name DojoWebASG \
    --launch-template LaunchTemplateName=DojoWebTemplate,Version='$Latest' \
    --min-size 2 --max-size 6 --desired-capacity 2 \
    --vpc-zone-identifier "$SUBNET_1,$SUBNET_2" \
    --target-group-arns $TG_ARN \
    --health-check-type ELB \
    --health-check-grace-period 180 \
    --tags Key=Name,Value=DojoWeb-ASG,PropagateAtLaunch=false

# Add a Target Tracking scaling policy (scale based on CPU)
aws autoscaling put-scaling-policy \
    --auto-scaling-group-name DojoWebASG \
    --policy-name DojoTargetCPU50 \
    --policy-type TargetTrackingScaling \
    --target-tracking-configuration '{
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ASGAverageCPUUtilization"
        },
        "TargetValue": 50.0,
        "ScaleInCooldown": 300,
        "ScaleOutCooldown": 60
    }'

echo "ASG created with scaling policy. Waiting for instances to launch..."
```

### Task 5: Verify and Test

```bash
# Check instance status (wait ~2 minutes for instances to boot)
aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names DojoWebASG \
    --query 'AutoScalingGroups[0].[DesiredCapacity,Instances[*].[InstanceId,HealthStatus,AvailabilityZone]]' \
    --output table

# Check target health in the ALB
aws elbv2 describe-target-health \
    --target-group-arn $TG_ARN \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
    --output table

# Test the ALB endpoint (run multiple times to see different instance IDs)
curl http://$ALB_DNS
curl http://$ALB_DNS
curl http://$ALB_DNS
```

Open the DNS name in a browser. Refresh a few times to see the traffic balancing between different instances—you should see different Instance IDs and Availability Zones in the response.

### Task 6: Trigger Auto Scaling (Optional)

To observe scaling in action, SSH into one of the instances (or use SSM Session Manager) and generate CPU load:

```bash
# From inside an EC2 instance, generate CPU stress for 5 minutes
stress-ng --cpu 2 --timeout 300s

# From your local machine, watch the ASG react (run every 30 seconds)
watch -n 30 "aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names DojoWebASG \
    --query 'AutoScalingGroups[0].[DesiredCapacity,Instances[*].[InstanceId,HealthStatus]]' \
    --output table"

# Check scaling activity log
aws autoscaling describe-scaling-activities \
    --auto-scaling-group-name DojoWebASG \
    --query 'Activities[*].[StartTime,StatusCode,Description]' \
    --output table --max-items 5
```

Within a few minutes of the CPU load exceeding the 50% target, you should see the ASG launch additional instances automatically.

### Task 7: Test Self-Healing

Manually terminate one of the instances and watch the ASG replace it:

```bash
# Get an instance ID from the ASG
INSTANCE_TO_KILL=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names DojoWebASG \
    --query 'AutoScalingGroups[0].Instances[0].InstanceId' --output text)

echo "Terminating $INSTANCE_TO_KILL to test self-healing..."
aws ec2 terminate-instances --instance-ids $INSTANCE_TO_KILL

# Watch the ASG detect the failure and launch a replacement
watch -n 15 "aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names DojoWebASG \
    --query 'AutoScalingGroups[0].Instances[*].[InstanceId,HealthStatus,LifecycleState]' \
    --output table"
```

The ASG should detect the terminated instance within 1-2 health check cycles and automatically launch a replacement to maintain the desired capacity of 2.

### Clean Up

**Important**: Always clean up to avoid ongoing charges.

```bash
# Step 1: Delete ASG (force-delete terminates all instances)
aws autoscaling delete-auto-scaling-group \
    --auto-scaling-group-name DojoWebASG --force-delete
echo "ASG deletion initiated. Waiting for instances to terminate..."
sleep 30

# Step 2: Delete ALB and Listener (listener is deleted with the ALB)
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
echo "Waiting for ALB to be deleted..."
sleep 30

# Step 3: Delete Target Group (must wait for ALB to be fully gone)
aws elbv2 delete-target-group --target-group-arn $TG_ARN

# Step 4: Delete Launch Template
aws ec2 delete-launch-template --launch-template-name DojoWebTemplate

# Step 5: Delete Security Groups (must wait for instances to fully terminate)
echo "Waiting for instances to fully terminate before deleting security groups..."
sleep 60
aws ec2 delete-security-group --group-id $WEB_SG
aws ec2 delete-security-group --group-id $ALB_SG

# Step 6: Clean up local files
rm -f userdata.sh template-data.json

echo "Cleanup complete!"
```

### Success Criteria

- [ ] I successfully created separate Security Groups for the ALB and web servers (defense in depth).
- [ ] I created a Launch Template with User Data, IMDSv2 enforcement, and proper tagging.
- [ ] I created an ALB with a Target Group using a custom health check path (`/health`).
- [ ] I created an Auto Scaling Group with a Target Tracking scaling policy.
- [ ] I hit the ALB DNS name in a browser and verified that my User Data script successfully configured the web servers, showing different Instance IDs on refresh.
- [ ] I observed the ASG self-heal by terminating an instance and watching a replacement launch automatically.

## Next Module

Now that you have stateless compute, you need a place to store massive amounts of unstructured data. Head to [Module 1.4: S3 & Object Storage](../module-1.4-s3/).
