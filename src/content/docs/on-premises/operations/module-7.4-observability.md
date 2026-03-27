---
title: "Module 7.4: Observability Without Cloud Services"
slug: on-premises/operations/module-7.4-observability
sidebar:
  order: 5
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 7.3: Node Failure & Auto-Remediation](module-7.3-node-remediation/), [Module 4.1: Storage Architecture](../storage/module-4.1-storage-architecture/)

---

## Why This Module Matters

In November 2023, an e-commerce company migrated from AWS EKS to on-premises Kubernetes. Their cloud setup had been straightforward: CloudWatch for logs, CloudWatch Metrics for monitoring, X-Ray for tracing, and PagerDuty for alerting. One AWS bill covered everything. When they moved to bare metal, the infrastructure team assumed they could replicate this stack in a weekend. They deployed a single Prometheus instance, pointed Grafana at it, and called it done.

Three months later, Prometheus crashed. It had been ingesting 800,000 samples per second across 400 nodes, and its local storage had grown to 1.2TB. The 15-day retention consumed all available disk space on the monitoring node. When Prometheus restarted, it took 45 minutes to replay the WAL (Write-Ahead Log), during which there was zero monitoring visibility. The team later discovered that Prometheus had been silently dropping samples for a week due to memory pressure, so their dashboards had gaps nobody noticed. Meanwhile, container logs were being written to local disk and rotated away after 24 hours -- they had no centralized logging at all.

The rebuild took six weeks: Prometheus with Thanos for long-term storage and high availability, Loki for centralized logging, a proper Alertmanager cluster with on-call rotation, and IPMI exporters for hardware-level metrics. Total cost: $15,000 in additional hardware and 240 engineering hours. The lesson: observability on bare metal is not a weekend project. It is a production system that requires the same care as the workloads it monitors.

---

## What You'll Learn

- Self-hosted Prometheus architecture with Thanos for long-term storage
- Grafana deployment at scale (dashboards, provisioning, multi-tenancy)
- Loki for centralized logging (replacing CloudWatch/Stackdriver)
- Alertmanager configuration with on-call rotation
- IPMI exporter for hardware-level monitoring
- Capacity planning for the monitoring stack itself

---

## Prometheus + Thanos Architecture

A single Prometheus instance cannot scale to large bare metal clusters. Thanos extends Prometheus with global querying, long-term storage, and high availability.

```
+---------------------------------------------------------------+
|         PROMETHEUS + THANOS ARCHITECTURE                       |
|                                                                |
|  Per-cluster Prometheus instances (scraping):                  |
|                                                                |
|  ┌──────────┐  ┌──────────┐  ┌──────────┐                    |
|  │Prometheus│  │Prometheus│  │Prometheus│                    |
|  │  (HA-a)  │  │  (HA-b)  │  │ (infra)  │                    |
|  │ workers  │  │ workers  │  │ctrl+stor │                    |
|  │  1-50    │  │  1-50    │  │          │                    |
|  └────┬─────┘  └────┬─────┘  └────┬─────┘                    |
|       │ sidecar      │ sidecar     │ sidecar                   |
|  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐                    |
|  │  Thanos  │  │  Thanos  │  │  Thanos  │                    |
|  │ Sidecar  │  │ Sidecar  │  │ Sidecar  │                    |
|  └────┬─────┘  └────┬─────┘  └────┬─────┘                    |
|       │              │              │                           |
|       ▼              ▼              ▼                           |
|  ┌─────────────────────────────────────────┐                   |
|  │          Thanos Query (global)          │                   |
|  │  Deduplicates HA pairs, fans out       │                   |
|  └─────────────┬───────────────────────────┘                   |
|                │                                                |
|       ┌────────┴────────┐                                      |
|       ▼                 ▼                                      |
|  ┌─────────┐    ┌──────────────┐                               |
|  │ Grafana │    │ Thanos Store │──> Object Storage (MinIO)     |
|  │         │    │   Gateway    │    (long-term, cheap)         |
|  └─────────┘    └──────────────┘                               |
|                                                                |
|  ┌──────────────┐                                              |
|  │Thanos Compact│  Downsamples old data:                       |
|  │              │  raw -> 5m -> 1h                              |
|  └──────────────┘  Saves 90%+ storage                          |
+---------------------------------------------------------------+
```

### Prometheus Configuration for Bare Metal

```yaml
# prometheus.yaml — optimized for bare metal
global:
  scrape_interval: 30s        # 15s is overkill for most bare metal
  evaluation_interval: 30s
  external_labels:
    cluster: production
    replica: ha-a              # for Thanos deduplication

# Scrape configs for bare metal targets
scrape_configs:
  # Kubernetes service discovery
  - job_name: kubelet
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  # Node exporter (system metrics)
  - job_name: node-exporter
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      - source_labels: [__meta_kubernetes_endpoints_name]
        regex: node-exporter
        action: keep

  # IPMI exporter (hardware metrics)
  # BMCs speak IPMI, not HTTP — use the multi-target exporter pattern
  # where Prometheus scrapes the ipmi-exporter and passes the BMC address
  # as a URL parameter (similar to blackbox-exporter)
  - job_name: ipmi
    static_configs:
      - targets:
          - bmc-worker-01
          - bmc-worker-02
          # ... all BMC addresses (no port — these are IPMI targets)
    metrics_path: /ipmi
    params:
      module: [default]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: ipmi-exporter:9290   # the actual exporter service

  # SMART disk metrics (via standalone smartctl_exporter)
  # Note: if using Node Exporter's textfile collector for SMART data,
  # remove this job — the metrics are already scraped by the node-exporter job above
  - job_name: smartmon
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - source_labels: [__address__]
        regex: (.+):(.+)
        target_label: __address__
        replacement: $1:9633
    metrics_path: /metrics
```

### Thanos Sidecar Deployment

Deploy each Prometheus as a StatefulSet with a Thanos sidecar container. Key Prometheus flags for Thanos compatibility:
- `--storage.tsdb.retention.time=48h` (short local retention, Thanos handles long-term)
- `--storage.tsdb.min-block-duration=2h` and `--storage.tsdb.max-block-duration=2h` (required for Thanos block upload)
- `--web.enable-lifecycle` (allows Thanos sidecar to trigger reloads)

The sidecar uploads completed TSDB blocks to object storage (MinIO) and serves real-time data via the Thanos StoreAPI. Configure the object store connection in a Secret with S3-compatible endpoint, bucket name, and credentials.

---

## Loki for Centralized Logging

Loki replaces CloudWatch Logs and Stackdriver Logging. Unlike Elasticsearch, Loki indexes only metadata (labels), not the full log text, making it dramatically cheaper to operate.

```
+---------------------------------------------------------------+
|              LOKI LOGGING ARCHITECTURE                         |
|                                                                |
|  ┌──────────┐  ┌──────────┐  ┌──────────┐                    |
|  │ Promtail │  │ Promtail │  │ Promtail │  (DaemonSet)       |
|  │ worker-01│  │ worker-02│  │ worker-03│  Tails container   |
|  │          │  │          │  │          │  logs from          |
|  └────┬─────┘  └────┬─────┘  └────┬─────┘  /var/log/pods/   |
|       │              │              │                          |
|       └──────────────┼──────────────┘                          |
|                      ▼                                         |
|              ┌──────────────┐                                  |
|              │   Loki       │  Stores log streams              |
|              │   (3 pods,   │  indexed by labels only          |
|              │    HA mode)  │  (namespace, pod, container)     |
|              └──────┬───────┘                                  |
|                     │                                          |
|                     ▼                                          |
|              ┌──────────────┐                                  |
|              │ Object Store │  Chunks stored in MinIO          |
|              │   (MinIO)    │  or local filesystem             |
|              └──────────────┘                                  |
|                                                                |
|              ┌──────────────┐                                  |
|              │   Grafana    │  Query logs alongside metrics    |
|              │              │  using LogQL                     |
|              └──────────────┘                                  |
+---------------------------------------------------------------+
```

### Loki Deployment

```yaml
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    s3:
      endpoint: minio.storage.svc.cluster.local:9000
      bucketnames: loki-chunks
      access_key_id: ${MINIO_ACCESS_KEY}
      secret_access_key: ${MINIO_SECRET_KEY}
      insecure: true
      s3forcepathstyle: true

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: s3
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 30d           # keep logs for 30 days
  max_query_lookback: 30d
  ingestion_rate_mb: 10           # per-tenant ingestion rate
  per_stream_rate_limit: 3MB

storage_config:
  tsdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
```

Promtail runs as a DaemonSet, mounting `/var/log` and `/var/log/pods` as read-only host volumes. It tails container logs and ships them to Loki with labels extracted from the Kubernetes metadata (namespace, pod, container name).

---

## Alertmanager Without PagerDuty

On-premises environments often cannot use cloud-based alerting services due to network isolation or compliance requirements. Alertmanager supports direct integrations.

### Alertmanager Configuration

Alertmanager routes alerts based on labels. Configure multiple receivers with escalation:

- **Hardware critical alerts** (`severity=critical, category=hardware`): webhook to on-call system + email, repeat every 15 minutes
- **Application critical alerts**: webhook + email, repeat every 30 minutes
- **Warnings**: email only, repeat every 24 hours

Group alerts by `alertname`, `cluster`, and `namespace` to reduce noise. Use `group_wait: 30s` to batch alerts that fire simultaneously (e.g., multiple nodes in the same rack losing power).

### Self-Hosted On-Call with Grafana OnCall

```
+---------------------------------------------------------------+
|            SELF-HOSTED ON-CALL STACK                           |
|                                                                |
|  Alertmanager                                                  |
|       │                                                        |
|       ▼ webhook                                                |
|  Grafana OnCall (open-source, self-hosted)                     |
|       │                                                        |
|       ├──> Slack notification                                  |
|       ├──> Email notification                                  |
|       ├──> Phone call (via Twilio integration)                 |
|       └──> SMS (via Twilio integration)                        |
|                                                                |
|  On-call schedules:                                            |
|  - Primary: rotates weekly                                     |
|  - Secondary: backup, rotates opposite week                    |
|  - Escalation: if no ack in 10 min, page secondary            |
|  - If no ack in 20 min, page engineering manager               |
|                                                                |
+---------------------------------------------------------------+
```

---

## IPMI Exporter for Hardware Monitoring

The IPMI exporter exposes BMC sensor data as Prometheus metrics, giving you visibility into temperatures, fan speeds, voltages, and PSU status.

### Deploying IPMI Exporter

Deploy the `prometheuscommunity/ipmi-exporter` as a Deployment in the monitoring namespace. Configure it with BMC credentials stored in a Kubernetes Secret, using the `LAN_2_0` driver with `bmc`, `ipmi`, and `dcmi` collectors. Prometheus scrapes each BMC address through the exporter's `/ipmi` endpoint.

### Key IPMI Metrics to Monitor

```
+---------------------------------------------------------------+
|         CRITICAL IPMI METRICS                                  |
|                                                                |
|  Metric                        Alert Threshold                 |
|  ─────────────────────────────────────────────────             |
|  ipmi_temperature_celsius      > 85 (CPU)                     |
|    {name="CPU Temp"}           > 45 (ambient)                  |
|                                                                |
|  ipmi_fan_speed_rpm            < 1000 (fan failure)            |
|    {name="Fan 1"}                                              |
|                                                                |
|  ipmi_voltage_volts            +/- 10% of nominal              |
|    {name="12V"}                (11.4V warning)                 |
|                                                                |
|  ipmi_power_watts              > 90% of PSU rated              |
|    {name="System Power"}       capacity                        |
|                                                                |
|  ipmi_sensor_state             != 0 (any critical state)       |
|    {name="PSU Status"}                                         |
|                                                                |
+---------------------------------------------------------------+
```

---

## Capacity Planning for Monitoring

The monitoring stack itself needs resources. Undersizing it leads to the monitoring system failing when you need it most.

### Sizing Guidelines

```
+---------------------------------------------------------------+
|       MONITORING STACK SIZING (per 100 nodes)                  |
|                                                                |
|  Component        CPU    Memory    Disk     Notes              |
|  ────────────────────────────────────────────────              |
|  Prometheus (x2)  4 CPU  16 GB     200 GB   HA pair, 48h ret  |
|  Thanos Query     2 CPU   4 GB       -      Stateless         |
|  Thanos Store GW  2 CPU   8 GB      50 GB   Cache for S3      |
|  Thanos Compact   2 CPU   4 GB     100 GB   Downsampling      |
|  Loki (x3)        2 CPU   8 GB      50 GB   HA mode           |
|  Grafana (x2)     1 CPU   2 GB       -      HA pair           |
|  Alertmanager(x3) 0.5CPU  1 GB       -      HA cluster        |
|  MinIO (x4)       2 CPU   8 GB    1000 GB   Object store      |
|  ────────────────────────────────────────────────              |
|  Total           ~30 CPU  ~90 GB   ~1.6 TB                    |
|                                                                |
|  Rule of thumb: dedicate 3-5% of cluster resources             |
|  to observability                                               |
+---------------------------------------------------------------+
```

### Prometheus Cardinality Management

```bash
# Find high-cardinality metrics (top 20)
curl -s http://prometheus:9090/api/v1/status/tsdb | jq '
  .data.seriesCountByMetricName |
  sort_by(-.value) |
  .[0:20] |
  .[] | "\(.name): \(.value) series"'

# Common offenders on bare metal:
# container_* metrics with high pod churn
# node_* metrics with many disk/interface labels
# Custom metrics with unbounded label values (IP addresses, user IDs)
```

---

## Did You Know?

- **Prometheus was created at SoundCloud in 2012** and donated to the CNCF in 2016. It was the second project to graduate after Kubernetes itself. Its pull-based scraping model was inspired by Google's Borgmon, which monitored Borg (the predecessor to Kubernetes) internally at Google.

- **Thanos was named after the Marvel villain** because it brings balance to the Prometheus universe -- specifically, it balances the trade-off between local retention (fast queries) and long-term storage (cheap, durable). The project started at Improbable (a gaming technology company) in 2017.

- **Loki processes logs 10-100x cheaper than Elasticsearch** for the same volume because it indexes only labels (namespace, pod, container), not the full log text. The trade-off is that full-text search requires scanning chunks -- which is slower for ad-hoc queries but perfectly fast for targeted queries like "show me logs from pod X in namespace Y."

- **IPMI (Intelligent Platform Management Interface) was first released in 1998** by Intel, HP, NEC, and Dell. Despite being nearly 30 years old, it remains the standard for out-of-band server management. The protocol runs on a dedicated BMC (Baseboard Management Controller) chip with its own network interface, CPU, and memory -- essentially a computer within your computer that runs even when the main system is powered off.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Single Prometheus instance | SPOF: crash = no monitoring | Deploy HA pair with Thanos deduplication |
| 15-day local retention | Fills disk, crashes Prometheus | Use 48h local + Thanos for long-term |
| No log aggregation | Logs lost on container restart or node failure | Deploy Loki + Promtail DaemonSet |
| Alertmanager singleton | Missed alerts if Alertmanager crashes | Deploy 3-node Alertmanager cluster |
| Monitoring on same nodes as workloads | Resource contention during incidents | Dedicated monitoring nodes or guaranteed resources |
| No IPMI monitoring | Hardware failures are invisible until node goes down | Deploy IPMI exporter for temperature, PSU, fan metrics |
| Unbounded label cardinality | Prometheus OOM from millions of series | Drop high-cardinality labels via relabeling |
| No monitoring-of-monitoring | Monitoring stack fails silently | External black-box probe (ping from outside cluster) |

---

## Quiz

### Question 1
Your Prometheus instance is ingesting 500,000 samples per second with 30-second scrape intervals across 200 bare metal nodes. You need 1 year of metrics retention. How do you architect this?

<details>
<summary>Answer</summary>

**Architecture: Prometheus HA pair + Thanos with MinIO object storage.**

**Sizing calculation:**
- 500,000 samples/sec * 2 bytes/sample (TSDB compressed) = ~1 MB/s
- Per day: 1 MB/s * 86,400 = ~84 GB/day
  (The 2 bytes/sample figure already accounts for Prometheus TSDB compression;
  raw uncompressed samples are 16 bytes each)
- 48-hour local retention: ~168 GB per Prometheus instance
- 1 year in Thanos with downsampling:
  - Raw (first 30 days): 84 GB * 30 = ~2.5 TB
  - 5-minute downsampled (30-365 days): ~400 GB
  - 1-hour downsampled (optional, for very old data): ~60 GB
  - Total object storage: ~3 TB

**Architecture:**
1. **2x Prometheus** (HA pair, same config, external_labels differ only by `replica`)
2. **2x Thanos Sidecar** (one per Prometheus, uploads blocks to MinIO)
3. **1x Thanos Query** (deduplicates HA pair, queries both local and store)
4. **1x Thanos Store Gateway** (serves queries from MinIO)
5. **1x Thanos Compactor** (downsamples: raw -> 5m -> 1h)
6. **MinIO cluster** (4 nodes, erasure coding, 4 TB usable)

**Why not just increase Prometheus retention?**
- 1 year at 84 GB/day = ~30 TB local disk -- expensive NVMe
- Prometheus queries slow down with large TSDB
- No HA: disk failure = data loss
- MinIO with erasure coding is cheaper and fault-tolerant
</details>

### Question 2
Your Loki cluster is receiving logs from 200 nodes, but queries for logs older than 2 days are extremely slow (30+ seconds). What is likely wrong and how do you fix it?

<details>
<summary>Answer</summary>

**Likely causes and fixes:**

1. **No chunk caching**: Loki reads chunks from object storage (MinIO) for every query. Without a cache, this means network I/O for every request.
   ```yaml
   # Add chunk cache in loki-config.yaml
   chunk_store_config:
     chunk_cache_config:
       memcached:
         host: memcached.monitoring.svc
         service: memcached
   ```

2. **Too few label indexes**: If most logs have the same label set (e.g., only `namespace` and `pod`), Loki must scan large chunks to filter.
   ```yaml
   # Add more labels in Promtail
   pipeline_stages:
     - labels:
         level:     # extract log level (info, error, warn)
         component: # extract component name from log line
   ```

3. **Large chunk size**: Default chunk target size might be too large for your ingestion rate.
   ```yaml
   ingester:
     chunk_target_size: 1572864  # 1.5 MB (default)
     # Consider reducing for faster queries at the cost of more chunks
   ```

4. **Object storage latency**: MinIO might be slow due to disk I/O contention.
   - Check MinIO disk I/O: `iostat -x 1`
   - Ensure MinIO has dedicated disks (not shared with Ceph or other workloads)

5. **Missing TSDB index**: Ensure you are using the TSDB index (not BoltDB) for better query performance.
   ```yaml
   schema_config:
     configs:
       - store: tsdb  # not boltdb-shipper
   ```

**Quick win**: Deploy a Memcached cluster (3 pods, 4 GB each) for chunk caching. This alone typically reduces query times by 5-10x for historical data.
</details>

### Question 3
Your Alertmanager sends alerts via email, but the SMTP server is on the corporate network and your Kubernetes cluster is in a separate datacenter VLAN. Alerts are being silently dropped. How do you diagnose and fix this?

<details>
<summary>Answer</summary>

**Diagnosis:**

1. **Check Alertmanager logs:**
   ```bash
   kubectl logs -n monitoring alertmanager-0 | grep -i "error\|fail\|smtp"
   # Look for: "connection refused", "timeout", "TLS handshake"
   ```

2. **Test SMTP connectivity from within the cluster:**
   ```bash
   kubectl run smtp-test --image=busybox --restart=Never -- sh -c \
     "nc -zv smtp.internal 587; echo exit code: $?"
   ```

3. **Check network policies or firewall rules** blocking port 587 from the monitoring namespace.

**Fix options:**

1. **Open firewall**: Allow port 587 from monitoring VLAN to corporate VLAN.

2. **Deploy a local SMTP relay** inside the cluster:
   ```yaml
   # Deploy Postfix as an SMTP relay in the monitoring namespace
   # Configure it to relay through the corporate SMTP server
   # Alertmanager sends to local relay (in-cluster, no firewall issue)
   # Relay forwards to corporate SMTP (firewall rule needed only for relay pod)
   ```

3. **Use webhook instead of email**: Deploy a webhook receiver that posts to Slack, Teams, or a custom notification service.

4. **Alertmanager -> Grafana OnCall -> Twilio**: If email is unreliable, use a notification chain that does not depend on corporate SMTP.

**Prevention**: Always test alerting during initial setup. Send a test alert and verify it arrives:
```bash
# Manually fire a test alert
curl -X POST http://alertmanager:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test alert from setup verification"}}]'
```
</details>

### Question 4
You are building the monitoring stack for a new 150-node bare metal cluster. The infrastructure team asks: "Can we just use the existing Datadog agents?" What are the trade-offs of Datadog vs self-hosted on bare metal?

<details>
<summary>Answer</summary>

**Trade-offs:**

| Factor | Datadog | Self-hosted (Prometheus/Thanos/Loki) |
|--------|---------|--------------------------------------|
| **Cost** | $23/host/month * 150 = $41,400/year (infrastructure plan) | $15,000 hardware + ~$5,000/year ops |
| **Setup time** | Days | Weeks |
| **Maintenance** | Zero (SaaS) | Ongoing (upgrades, capacity, failures) |
| **Data residency** | Data leaves your network | Data stays on-premises |
| **Network dependency** | Requires internet egress | Works air-gapped |
| **Retention** | 15 months (paid tier) | Unlimited (limited by storage) |
| **Customization** | Limited to Datadog features | Full control |
| **Hardware metrics** | Requires custom integration | IPMI exporter built for this |
| **Compliance** | May not meet data sovereignty requirements | Full control over data location |

**Recommendation depends on context:**

- **Use Datadog if**: Budget allows, no data sovereignty requirements, small team without monitoring expertise, internet egress is available.

- **Use self-hosted if**: Data must stay on-premises (healthcare, finance, government), air-gapped environment, cost-sensitive at scale (150+ nodes), team has Prometheus expertise, need deep hardware-level monitoring (IPMI, SMART).

- **Hybrid option**: Datadog for application APM/tracing, self-hosted Prometheus for infrastructure and hardware metrics. This gives you the best APM with full hardware visibility.

Most on-premises Kubernetes deployments choose self-hosted because the primary reason for running on-premises (data control, compliance, cost) also applies to monitoring data.
</details>

---

## Hands-On Exercise: Deploy a Monitoring Stack

**Task**: Deploy Prometheus, Grafana, and Alertmanager on a kind cluster.

### Setup

```bash
# Create a kind cluster
kind create cluster --name monitoring-lab

# Install kube-prometheus-stack via Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin \
  --set prometheus.prometheusSpec.retention=24h
```

### Steps

1. **Verify all components are running:**
   ```bash
   kubectl get pods -n monitoring
   ```

2. **Access Grafana:**
   ```bash
   kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
   # Open http://localhost:3000 (admin/admin)
   ```

3. **Explore the pre-built dashboards** for node metrics, pod metrics, and Kubernetes components.

4. **Create a test alert:**
   ```bash
   kubectl apply -f - <<'EOF'
   apiVersion: monitoring.coreos.com/v1
   kind: PrometheusRule
   metadata:
     name: test-alert
     namespace: monitoring
     labels:
       release: monitoring    # Required for Prometheus Operator to discover this rule
   spec:
     groups:
       - name: test
         rules:
           - alert: HighCPU
             expr: node_cpu_seconds_total > 0
             for: 1m
             labels:
               severity: warning
             annotations:
               summary: "Test alert: CPU is being used"
   EOF
   ```

5. **Verify the alert fires in Alertmanager:**
   ```bash
   kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093
   # Open http://localhost:9093
   ```

### Success Criteria

- [ ] Prometheus is scraping all cluster targets
- [ ] Grafana shows node and pod metrics on dashboards
- [ ] Alertmanager is receiving and displaying alerts
- [ ] Understand the difference between Prometheus local storage and Thanos long-term storage
- [ ] Can explain why IPMI exporter is essential for bare metal but irrelevant in the cloud

### Cleanup

```bash
kind delete cluster --name monitoring-lab
```

---

## Next Module

Continue to [Module 7.5: Capacity Expansion & Hardware Refresh](../operations/module-7.5-capacity-expansion/) to learn how to add new racks, handle mixed CPU generations, and plan hardware refresh cycles.
