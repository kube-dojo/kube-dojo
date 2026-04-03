---
title: "Module 9.6: Search & Analytics Engines (OpenSearch / Elasticsearch)"
slug: cloud/managed-services/module-9.6-search
sidebar:
  order: 7
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2.5h | **Prerequisites**: Module 9.2 (Message Brokers), Kubernetes logging concepts, JSON/HTTP API basics

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy managed OpenSearch/Elasticsearch (Amazon OpenSearch, Elastic Cloud, Azure Cognitive Search) with Kubernetes ingestion pipelines**
- **Configure Fluentd or Vector to ship Kubernetes logs to managed search clusters with index lifecycle management**
- **Implement search-as-a-service patterns where Kubernetes applications query managed search indices via private endpoints**
- **Optimize search cluster sizing, shard strategies, and index templates for Kubernetes log and application data volumes**

---

## Why This Module Matters

In August 2023, a SaaS company running 200 microservices on EKS generated 12 TB of logs per day. They ran a self-managed Elasticsearch cluster on Kubernetes -- 9 data nodes, 3 master nodes, each on i3.2xlarge instances with local NVMe storage. Total monthly cost: $22,000 for compute alone. The cluster required a dedicated engineer spending roughly 30% of their time on shard rebalancing, index lifecycle management, JVM tuning, and version upgrades. When they attempted an upgrade from Elasticsearch 7.x to 8.x, a mapping incompatibility brought down the cluster for 4 hours. During those 4 hours, the security team could not search logs to investigate an active incident.

They migrated to Amazon OpenSearch Service (managed). The migration took three weeks. The managed service handles node replacement, automated snapshots, encryption, and version upgrades. The same engineer now spends 5% of their time on search operations. More importantly, the cluster has not had a single unplanned outage in 14 months. The lesson: running a distributed search cluster on Kubernetes is technically possible, but the operational overhead is enormous. Managed search services let you focus on what matters -- getting insights from your data.

This module teaches you how to ingest Kubernetes logs and metrics into managed search engines, configure index lifecycle management for cost optimization, design sharding and replication strategies, implement fine-grained access control, and optimize queries for operational analytics.

---

## Log Ingestion Architecture

### The Kubernetes Logging Pipeline

```
  +-------+  +-------+  +-------+
  | Pod A |  | Pod B |  | Pod C |  ... (hundreds of pods)
  +---+---+  +---+---+  +---+---+
      |          |          |
      v          v          v
  [Node Filesystem: /var/log/containers/]
      |
      v
  +-------------------+
  | DaemonSet:        |
  | Fluent Bit        |  (one per node)
  +--------+----------+
           |
           v
  +-------------------+
  | Buffer/Transform  |  (optional: Kafka, Kinesis)
  +--------+----------+
           |
           v
  +-------------------+
  | OpenSearch /      |
  | Elasticsearch     |
  +-------------------+
```

### Fluent Bit DaemonSet for Log Collection

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      tolerations:
        - operator: Exists
      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:3.2
          volumeMounts:
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: config
              mountPath: /fluent-bit/etc/
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: config
          configMap:
            name: fluent-bit-config
```

### Fluent Bit Configuration for OpenSearch

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Tag               kube.*
        Path              /var/log/containers/*.log
        Parser            cri
        DB                /var/log/flb_kube.db
        Mem_Buf_Limit     10MB
        Skip_Long_Lines   On
        Refresh_Interval  10

    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        Keep_Log            Off
        K8s-Logging.Parser  On
        K8s-Logging.Exclude On
        Labels              On
        Annotations         Off

    [FILTER]
        Name    modify
        Match   kube.*
        Add     cluster_name production-us-east-1

    [OUTPUT]
        Name            opensearch
        Match           kube.*
        Host            search-logs-abc123.us-east-1.es.amazonaws.com
        Port            443
        TLS             On
        AWS_Auth        On
        AWS_Region      us-east-1
        Index           k8s-logs
        Type            _doc
        Logstash_Format On
        Logstash_Prefix k8s-logs
        Retry_Limit     3
        Buffer_Size     5MB
        Generate_ID     On

  parsers.conf: |
    [PARSER]
        Name        cri
        Format      regex
        Regex       ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<log>.*)$
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L%z
```

### Buffering with Kafka for Resilience

For high-volume clusters, buffer logs through Kafka to prevent data loss when OpenSearch is slow or unavailable:

```
Fluent Bit --> Kafka Topic --> Logstash/Vector --> OpenSearch
```

```yaml
# Fluent Bit output to Kafka instead of direct to OpenSearch
# fluent-bit.conf (OUTPUT section)
[OUTPUT]
    Name        kafka
    Match       kube.*
    Brokers     kafka-bootstrap.messaging.svc:9092
    Topics      k8s-logs
    Timestamp_Key @timestamp
    rdkafka.compression.codec snappy
    rdkafka.message.max.bytes 1048576
```

---

## Setting Up Managed Search

### Amazon OpenSearch Service

```bash
# Create an OpenSearch domain
aws opensearch create-domain \
  --domain-name k8s-logs \
  --engine-version OpenSearch_2.13 \
  --cluster-config '{
    "InstanceType": "r6g.large.search",
    "InstanceCount": 3,
    "DedicatedMasterEnabled": true,
    "DedicatedMasterType": "m6g.large.search",
    "DedicatedMasterCount": 3,
    "ZoneAwarenessEnabled": true,
    "ZoneAwarenessConfig": {"AvailabilityZoneCount": 3}
  }' \
  --ebs-options '{
    "EBSEnabled": true,
    "VolumeType": "gp3",
    "VolumeSize": 500,
    "Iops": 3000,
    "Throughput": 250
  }' \
  --vpc-options '{
    "SubnetIds": ["subnet-aaa", "subnet-bbb", "subnet-ccc"],
    "SecurityGroupIds": ["sg-search"]
  }' \
  --encryption-at-rest-options Enabled=true \
  --node-to-node-encryption-options Enabled=true \
  --domain-endpoint-options EnforceHTTPS=true \
  --advanced-security-options '{
    "Enabled": true,
    "InternalUserDatabaseEnabled": false,
    "MasterUserOptions": {
      "MasterUserARN": "arn:aws:iam::123456789:role/OpenSearchAdmin"
    }
  }'
```

### GCP: Elastic Cloud on Google Cloud

```bash
# Using Elastic Cloud (managed Elasticsearch) with GKE
# Create deployment via Elastic Cloud API or console
# Then configure Fluent Bit to point to the Elastic Cloud endpoint

# Fluent Bit output for Elastic Cloud
# [OUTPUT]
#     Name  es
#     Match kube.*
#     Host  my-deployment.es.us-central1.gcp.cloud.es.io
#     Port  9243
#     TLS   On
#     Cloud_Auth elastic:password
#     Index k8s-logs
#     Logstash_Format On
```

---

## Index Lifecycle Management (ILM/ISM)

Without lifecycle management, indices grow forever. A single day of logs for a 200-pod cluster can be 50 GB. After a month, you have 1.5 TB of indices, most of which nobody searches.

### Lifecycle Phases

```
HOT phase (0-3 days)     WARM phase (3-30 days)    COLD phase (30-90 days)    DELETE
  - Fast SSD storage       - Cheaper storage          - Cheapest storage         - Gone
  - Full indexing           - Read-only                - Frozen (rarely queried)
  - All replicas            - Fewer replicas           - No replicas
  - Shard merging           - Force merge              - Searchable snapshot
```

### OpenSearch Index State Management (ISM) Policy

```bash
# Create ISM policy via OpenSearch API
curl -XPUT "https://search-logs.us-east-1.es.amazonaws.com/_plugins/_ism/policies/k8s-log-lifecycle" \
  -H "Content-Type: application/json" \
  -d '{
  "policy": {
    "description": "K8s log lifecycle: hot -> warm -> cold -> delete",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          {
            "rollover": {
              "min_index_age": "1d",
              "min_primary_shard_size": "30gb"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "warm",
            "conditions": { "min_index_age": "3d" }
          }
        ]
      },
      {
        "name": "warm",
        "actions": [
          {
            "replica_count": { "number_of_replicas": 1 }
          },
          {
            "force_merge": { "max_num_segments": 1 }
          }
        ],
        "transitions": [
          {
            "state_name": "cold",
            "conditions": { "min_index_age": "30d" }
          }
        ]
      },
      {
        "name": "cold",
        "actions": [
          {
            "replica_count": { "number_of_replicas": 0 }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": { "min_index_age": "90d" }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          { "delete": {} }
        ]
      }
    ],
    "ism_template": [
      {
        "index_patterns": ["k8s-logs-*"],
        "priority": 100
      }
    ]
  }
}'
```

### Index Template

```bash
curl -XPUT "https://search-logs.us-east-1.es.amazonaws.com/_index_template/k8s-logs" \
  -H "Content-Type: application/json" \
  -d '{
  "index_patterns": ["k8s-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.refresh_interval": "30s",
      "index.translog.durability": "async",
      "index.translog.sync_interval": "30s",
      "plugins.index_state_management.policy_id": "k8s-log-lifecycle"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "kubernetes": {
          "properties": {
            "namespace_name": { "type": "keyword" },
            "pod_name": { "type": "keyword" },
            "container_name": { "type": "keyword" },
            "labels": { "type": "object", "dynamic": true }
          }
        },
        "log": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
        "stream": { "type": "keyword" },
        "cluster_name": { "type": "keyword" },
        "level": { "type": "keyword" }
      }
    }
  }
}'
```

---

## Sharding and Replication Strategy

Sharding determines how data is distributed across nodes. Getting it wrong causes hot spots, uneven disk usage, and query performance problems.

### Shard Sizing Rules

| Rule | Guideline | Reason |
|------|-----------|--------|
| Shard size | 10-50 GB per shard | Too small = overhead, too large = slow queries and recovery |
| Shards per node | Max 20 per GB of JVM heap | 1000 shards on a node with 32 GB heap is the practical max |
| Shards per index | 1 shard per 30 GB of expected data | A 90 GB/day index needs ~3 primary shards |
| Total cluster shards | Monitor and alert above 10,000 | Cluster state overhead grows linearly with shard count |

### Calculating Shards for a Logging Workload

```
Given:
  - 200 pods generating ~60 GB of logs per day
  - 90-day retention
  - Daily index rollover

Calculation:
  - Daily data: 60 GB
  - Target shard size: 30 GB
  - Primary shards per index: ceil(60/30) = 2
  - Replicas: 1 (in hot phase)
  - Total shards per day: 2 primary + 2 replica = 4

  - 90 days retention:
    - Hot (3 days): 3 * 4 = 12 shards
    - Warm (27 days): 27 * 3 = 81 shards (reduced replicas)
    - Cold (60 days): 60 * 2 = 120 shards (no replicas)
    - Total: ~213 shards (well within limits)
```

### Preventing Shard Explosion

A common mistake is using one index per namespace per day. With 50 namespaces and daily rollover:

```
BAD:  50 namespaces * 3 shards * 2 (replicas) * 90 days = 27,000 shards!
GOOD: 1 index per day * 3 shards * 2 (replicas) * 90 days = 540 shards
```

Use a single index with a `namespace` field for filtering. Only create separate indices when access control requires it.

---

## Fine-Grained Access Control

In a multi-team environment, different teams should only see logs from their own namespaces.

### OpenSearch Security: Role-Based Access

```bash
# Create a role that restricts access to a specific namespace
curl -XPUT "https://search-logs.us-east-1.es.amazonaws.com/_plugins/_security/api/roles/team-payments" \
  -H "Content-Type: application/json" \
  -d '{
  "cluster_permissions": [],
  "index_permissions": [
    {
      "index_patterns": ["k8s-logs-*"],
      "allowed_actions": ["read", "search"],
      "dls": "{\"match\": {\"kubernetes.namespace_name\": \"payments\"}}",
      "fls": ["~kubernetes.labels.secret-hash"]
    }
  ]
}'
```

The `dls` (Document Level Security) field ensures that users with this role can only see log entries from the `payments` namespace. The `fls` (Field Level Security) hides specific sensitive fields.

### Mapping OIDC Groups to OpenSearch Roles

```bash
# Map an OIDC group to the role
curl -XPUT "https://search-logs.us-east-1.es.amazonaws.com/_plugins/_security/api/rolesmapping/team-payments" \
  -H "Content-Type: application/json" \
  -d '{
  "backend_roles": ["arn:aws:iam::123456789:role/TeamPaymentsRole"],
  "users": [],
  "hosts": []
}'
```

### Kubernetes RBAC to OpenSearch Role Matrix

| Kubernetes Namespace | OIDC Group | OpenSearch Role | Index Access |
|---------------------|------------|-----------------|-------------|
| payments | team-payments | team-payments | k8s-logs-* (DLS: namespace=payments) |
| frontend | team-frontend | team-frontend | k8s-logs-* (DLS: namespace=frontend) |
| platform | sre-team | sre-full-access | k8s-logs-* (no DLS, full access) |
| security | security-team | security-audit | k8s-logs-*, k8s-audit-* (full access) |

---

## Query Optimization

Search queries against log indices can be slow if not designed well. Here are patterns for efficient operational queries.

### Common Query Patterns

```bash
# Find errors in a specific namespace in the last hour
curl -XPOST "https://search-logs.us-east-1.es.amazonaws.com/k8s-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
  "query": {
    "bool": {
      "filter": [
        {"term": {"kubernetes.namespace_name": "payments"}},
        {"term": {"level": "error"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "sort": [{"@timestamp": {"order": "desc"}}],
  "size": 100
}'

# Aggregate error counts by pod over the last 24 hours
curl -XPOST "https://search-logs.us-east-1.es.amazonaws.com/k8s-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        {"term": {"level": "error"}},
        {"range": {"@timestamp": {"gte": "now-24h"}}}
      ]
    }
  },
  "aggs": {
    "by_pod": {
      "terms": {"field": "kubernetes.pod_name", "size": 20},
      "aggs": {
        "over_time": {
          "date_histogram": {"field": "@timestamp", "fixed_interval": "1h"}
        }
      }
    }
  }
}'
```

### Query Performance Tips

| Tip | Why It Helps |
|-----|-------------|
| Use `filter` context instead of `must` for exact matches | Filter context is cached and does not compute relevance scores |
| Narrow the time range as much as possible | OpenSearch skips indices outside the range entirely |
| Use `keyword` fields for exact matches, `text` for full-text | Querying a `text` field with an exact match scans every token |
| Limit `size` to what you actually need | Default is 10; requesting 10,000 forces scanning and sorting |
| Use `_source` filtering to return only needed fields | Large `_source` documents waste network bandwidth |
| Prefer `terms` query over multiple `term` queries | One `terms` query is faster than OR-ing multiple `term` queries |

```bash
# Efficient: return only needed fields
curl -XPOST "https://search-logs.us-east-1.es.amazonaws.com/k8s-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
  "_source": ["@timestamp", "log", "kubernetes.pod_name", "level"],
  "query": {
    "bool": {
      "filter": [
        {"terms": {"kubernetes.namespace_name": ["payments", "checkout"]}},
        {"range": {"@timestamp": {"gte": "now-15m"}}}
      ]
    }
  },
  "size": 50
}'
```

---

## OpenSearch Dashboards from Kubernetes

Deploy OpenSearch Dashboards (or Kibana) inside your cluster for log visualization.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opensearch-dashboards
  namespace: logging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: opensearch-dashboards
  template:
    metadata:
      labels:
        app: opensearch-dashboards
    spec:
      containers:
        - name: dashboards
          image: opensearchproject/opensearch-dashboards:2.13.0
          ports:
            - containerPort: 5601
          env:
            - name: OPENSEARCH_HOSTS
              value: '["https://search-logs-abc123.us-east-1.es.amazonaws.com:443"]'
            - name: SERVER_BASEPATH
              value: "/dashboards"
            - name: SERVER_REWRITEBASEPATH
              value: "true"
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: opensearch-dashboards
  namespace: logging
spec:
  selector:
    app: opensearch-dashboards
  ports:
    - port: 5601
      targetPort: 5601
```

---

## Did You Know?

1. **OpenSearch was forked from Elasticsearch 7.10.2 in 2021** after Elastic changed Elasticsearch's license from Apache 2.0 to SSPL (Server Side Public License). AWS, who had been offering Elasticsearch as a managed service, created the OpenSearch fork under the Apache 2.0 license. Today, OpenSearch has diverged significantly with unique features like observability plugins and anomaly detection.

2. **A single OpenSearch shard is a complete Lucene index** with its own inverted index, stored fields, and segment files. When you search across a 3-shard index, you are actually running 3 parallel Lucene searches and merging results. This is why shard count directly affects query latency -- each additional shard adds coordination overhead.

3. **The `force_merge` operation during the warm phase can reduce index size by 40-60%** because it compacts multiple Lucene segments into one. This also speeds up queries because there are fewer segments to search. But force merge is CPU-intensive and should only run on warm/cold indices that are no longer receiving writes.

4. **Document Level Security in OpenSearch evaluates a filter query on every search request**, which adds 5-15% overhead per query. For high-traffic dashboards, pre-filter by creating separate index aliases per team with built-in filters, which eliminates the per-query DLS evaluation.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Creating one index per namespace per day | Seems like good organization | Use a single daily index with namespace as a field; use DLS for access control |
| Not setting index lifecycle policies before production | "We will configure it later" | Define ISM/ILM policies before sending any data; retroactive migration is painful |
| Using `text` type for fields that need exact matching | Default dynamic mapping maps strings to `text` | Create explicit mappings with `keyword` type for namespace, pod name, level |
| Setting too many primary shards | "More shards = more parallelism" | Follow the 10-50 GB per shard rule; over-sharding wastes resources |
| Not buffering through Kafka for high-volume clusters | Direct ingestion seems simpler | Without a buffer, OpenSearch backpressure causes Fluent Bit to drop logs |
| Searching across all indices when only recent data is needed | Using wildcard `k8s-logs-*` without time filter | Always include a time range in queries; OpenSearch skips non-matching indices |
| Running force_merge on hot indices | Trying to optimize active indices | Only force_merge on read-only warm/cold indices; active indices will create new segments |
| Ignoring JVM heap pressure on managed clusters | "Managed means I do not need to worry" | Monitor JVMMemoryPressure; above 80% causes GC pauses and slow queries |

---

## Quiz

<details>
<summary>1. Why should you use a Kafka buffer between Fluent Bit and OpenSearch for high-volume clusters?</summary>

Kafka acts as a shock absorber between log producers and the search engine. If OpenSearch becomes slow (due to heavy queries, GC pauses, or a node failure), Fluent Bit without a buffer would either drop logs or back up memory on every node in the cluster. With Kafka in between, Fluent Bit writes to Kafka (which is designed for high-throughput writes), and a separate consumer reads from Kafka into OpenSearch at a rate that OpenSearch can handle. This decouples production from consumption and provides at-least-once delivery guarantees. Kafka also allows replaying logs if you need to re-index data.
</details>

<details>
<summary>2. Explain the difference between hot, warm, and cold phases in index lifecycle management.</summary>

Hot phase indices are actively receiving writes and frequent queries. They use fast storage (SSD), full replicas, and are optimized for write throughput (30-second refresh interval). Warm phase indices are read-only -- no new data arrives. They are force-merged to reduce segments, may have fewer replicas, and can use cheaper storage. Cold phase indices are rarely queried. They have no replicas (or use searchable snapshots), use the cheapest storage tier, and may be frozen to reduce memory overhead. Each phase trades query performance for cost savings, matching the access pattern of log data: recent logs are searched frequently, older logs rarely.
</details>

<details>
<summary>3. Why is creating one index per Kubernetes namespace per day a bad idea at scale?</summary>

With 50 namespaces and 3 primary shards per index (with 1 replica), a single day creates 300 shards. Over 90 days of retention, that is 27,000 shards. Each shard consumes cluster state memory, requires its own recovery tracking, and adds overhead to every cluster-level operation. OpenSearch clusters degrade significantly above 10,000-20,000 shards. Instead, use a single daily index with `namespace` as a keyword field and use Document Level Security for access control. This reduces shard count by 50x while providing the same logical separation.
</details>

<details>
<summary>4. What is Document Level Security (DLS) and when would you use it?</summary>

DLS is an OpenSearch security feature that appends a filter query to every search request made by a specific role. For example, a role with DLS filter `{"match": {"kubernetes.namespace_name": "payments"}}` will only ever see documents from the payments namespace, regardless of what the user searches for. Use it in multi-team environments where teams share the same indices but should only see their own data. The alternative -- separate indices per team -- causes shard explosion. DLS adds 5-15% query overhead, which is a worthwhile trade for the operational simplicity of shared indices.
</details>

<details>
<summary>5. Why should you use `filter` context instead of `must` for exact-match queries in OpenSearch?</summary>

In `bool` queries, `must` clauses calculate relevance scores for each matching document. `filter` clauses find matching documents but skip relevance scoring. For log queries where you want exact matches (specific namespace, time range, log level), relevance scoring is meaningless -- you are filtering, not ranking. Filter clauses are also cached by OpenSearch, so repeated queries with the same filters (common in dashboards) hit the cache instead of re-evaluating. For log analytics workloads, nearly every query component should be in the `filter` context.
</details>

<details>
<summary>6. How do you calculate the right number of primary shards for a daily log index?</summary>

Estimate the daily data volume and divide by the target shard size (10-50 GB). For 60 GB/day of logs, using a target of 30 GB per shard: ceil(60/30) = 2 primary shards. Do not over-shard "for future growth" because you can always increase shard count when you roll over to a new index. The rollover action in ISM/ILM creates a new index when the current one reaches a size or age threshold, giving you a natural point to adjust shard count. Start conservative and increase only when shards consistently exceed 50 GB.
</details>

---

## Hands-On Exercise: Log Pipeline with OpenSearch

This exercise uses OpenSearch running in kind to build a complete log ingestion and search pipeline.

### Setup

```bash
# Create kind cluster
kind create cluster --name search-lab

# Install OpenSearch using Helm (single-node for lab)
helm repo add opensearch https://opensearch-project.github.io/helm-charts/
helm install opensearch opensearch/opensearch \
  --namespace search --create-namespace \
  --set singleNode=true \
  --set replicas=1 \
  --set persistence.enabled=false \
  --set resources.requests.memory=1Gi \
  --set resources.limits.memory=1.5Gi \
  --set config.opensearch\\.yml."plugins.security.disabled"=true

k wait --for=condition=ready pod -l app.kubernetes.io/name=opensearch \
  --namespace search --timeout=180s

# Install OpenSearch Dashboards
helm install dashboards opensearch/opensearch-dashboards \
  --namespace search \
  --set opensearchHosts="http://opensearch-cluster-master:9200" \
  --set resources.requests.memory=512Mi
```

### Task 1: Create an Index Template

Create an index template for Kubernetes logs with proper field mappings.

<details>
<summary>Solution</summary>

```bash
k run opensearch-setup --rm -it --image=curlimages/curl -n search --restart=Never -- \
  curl -s -XPUT "http://opensearch-cluster-master:9200/_index_template/k8s-logs" \
  -H "Content-Type: application/json" \
  -d '{
    "index_patterns": ["k8s-logs-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.refresh_interval": "5s"
      },
      "mappings": {
        "properties": {
          "@timestamp": {"type": "date"},
          "level": {"type": "keyword"},
          "message": {"type": "text"},
          "kubernetes": {
            "properties": {
              "namespace": {"type": "keyword"},
              "pod": {"type": "keyword"},
              "container": {"type": "keyword"},
              "node": {"type": "keyword"}
            }
          }
        }
      }
    }
  }'
```
</details>

### Task 2: Ingest Sample Log Data

Push simulated Kubernetes log entries into the index.

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/ingest-logs.sh
#!/bin/sh
OPENSEARCH="http://opensearch-cluster-master:9200"

NAMESPACES="payments frontend api-gateway checkout analytics"
LEVELS="info info info info info info warn error error"
MESSAGES=(
  "Request processed successfully in 42ms"
  "Connection to database established"
  "Cache hit for product catalog"
  "User authentication completed"
  "Health check passed"
  "Processing batch job item 23 of 150"
  "Slow query detected: 2300ms for user lookup"
  "Connection refused: redis-master:6379"
  "NullPointerException in PaymentService.process"
)

# Create bulk index payload
BULK=""
for i in $(seq 1 500); do
  NS=$(echo $NAMESPACES | tr ' ' '\n' | shuf -n 1)
  LVL=$(echo $LEVELS | tr ' ' '\n' | shuf -n 1)
  MSG_IDX=$((RANDOM % 9))
  POD="${NS}-deployment-$(head -c 5 /dev/urandom | od -A n -t x1 | tr -d ' ')"
  TS=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

  BULK="${BULK}{\"index\":{\"_index\":\"k8s-logs-$(date +%Y.%m.%d)\"}}\n"
  BULK="${BULK}{\"@timestamp\":\"${TS}\",\"level\":\"${LVL}\",\"message\":\"Request $i processed\",\"kubernetes\":{\"namespace\":\"${NS}\",\"pod\":\"${POD}\",\"container\":\"app\",\"node\":\"worker-1\"}}\n"
done

printf "$BULK" | curl -s -XPOST "${OPENSEARCH}/_bulk" \
  -H "Content-Type: application/x-ndjson" \
  --data-binary @-

echo ""
echo "Ingested 500 log entries"

# Verify
curl -s "${OPENSEARCH}/k8s-logs-*/_count" | python3 -m json.tool 2>/dev/null || \
  curl -s "${OPENSEARCH}/k8s-logs-*/_count"
SCRIPT

k create configmap ingest-script -n search --from-file=/tmp/ingest-logs.sh
k run log-ingester --rm -it --image=curlimages/curl -n search --restart=Never \
  --overrides='{
    "spec": {
      "containers": [{
        "name": "ingester",
        "image": "python:3.12-slim",
        "command": ["/bin/sh", "-c", "pip install requests -q && python3 -c \"
import requests, random, json
from datetime import datetime

OPENSEARCH = \"http://opensearch-cluster-master:9200\"
namespaces = [\"payments\", \"frontend\", \"api-gateway\", \"checkout\", \"analytics\"]
levels = [\"info\"] * 6 + [\"warn\"] * 2 + [\"error\"] * 2

bulk = \"\"
for i in range(500):
    ns = random.choice(namespaces)
    lvl = random.choice(levels)
    ts = datetime.utcnow().strftime(\"%Y-%m-%dT%H:%M:%S.000Z\")
    idx = datetime.utcnow().strftime(\"k8s-logs-%Y.%m.%d\")
    doc = {\"@timestamp\": ts, \"level\": lvl, \"message\": f\"Request {i} processed in {random.randint(5,500)}ms\", \"kubernetes\": {\"namespace\": ns, \"pod\": f\"{ns}-deploy-{i:04d}\", \"container\": \"app\", \"node\": \"worker-1\"}}
    bulk += json.dumps({\"index\": {\"_index\": idx}}) + chr(10) + json.dumps(doc) + chr(10)

r = requests.post(f\"{OPENSEARCH}/_bulk\", data=bulk, headers={\"Content-Type\": \"application/x-ndjson\"})
print(f\"Bulk status: {r.status_code}\")
count = requests.get(f\"{OPENSEARCH}/{idx}/_count\").json()
print(f\"Total documents: {count.get(\"count\", 0)}\")
\""]
      }]
    }
  }'
```
</details>

### Task 3: Query for Errors by Namespace

Search for error-level logs and aggregate by namespace.

<details>
<summary>Solution</summary>

```bash
k run search-errors --rm -it --image=curlimages/curl -n search --restart=Never -- \
  curl -s -XPOST "http://opensearch-cluster-master:9200/k8s-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "bool": {
        "filter": [
          {"term": {"level": "error"}}
        ]
      }
    },
    "aggs": {
      "by_namespace": {
        "terms": {"field": "kubernetes.namespace", "size": 10}
      }
    }
  }'
```
</details>

### Task 4: Check Index Health and Stats

Query the cluster for index statistics and health.

<details>
<summary>Solution</summary>

```bash
# Index stats
k run check-stats --rm -it --image=curlimages/curl -n search --restart=Never -- \
  sh -c '
  echo "=== Cluster Health ==="
  curl -s "http://opensearch-cluster-master:9200/_cluster/health" | python3 -m json.tool 2>/dev/null

  echo ""
  echo "=== Index Stats ==="
  curl -s "http://opensearch-cluster-master:9200/k8s-logs-*/_stats/docs,store" | python3 -m json.tool 2>/dev/null

  echo ""
  echo "=== Shard Allocation ==="
  curl -s "http://opensearch-cluster-master:9200/_cat/shards/k8s-logs-*?v"
  '
```
</details>

### Success Criteria

- [ ] Index template is created with proper field mappings
- [ ] 500 log entries are ingested into the k8s-logs index
- [ ] Error aggregation query returns counts by namespace
- [ ] Cluster health and index stats are visible

### Cleanup

```bash
kind delete cluster --name search-lab
```

---

**Next Module**: [Module 9.7: Streaming Data Pipelines (MSK / Confluent / Dataflow)](../module-9.7-streaming/) -- Learn how to build streaming data pipelines with managed Kafka, compare managed vs in-cluster Strimzi, and process real-time events from Kubernetes workloads.
