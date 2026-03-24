# Module 13.3: Dragonfly - P2P Image Distribution at Scale

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 minutes

## Overview

What happens when you deploy to 1,000 nodes simultaneously? Your registry melts. Every node requests the same layers, creating a thundering herd that saturates bandwidth and brings deployments to a crawl. Dragonfly solves this with peer-to-peer distribution: the first node pulls from the registry, then shares with neighboring nodes, who share with their neighbors. Your registry sees 1 request instead of 1,000.

This module teaches you to deploy Dragonfly for massive-scale container image distribution.

## Prerequisites

- Understanding of container registries (Harbor or Zot)
- Kubernetes fundamentals (DaemonSets, Services)
- Basic networking concepts (P2P, BitTorrent-like protocols)
- [DevSecOps Discipline](../../disciplines/devsecops/README.md) - Supply chain concepts

## Why This Module Matters

Traditional registry architectures hit a wall at scale:

```
THE THUNDERING HERD PROBLEM
─────────────────────────────────────────────────────────────────────────────

Traditional Pull:                    P2P Pull (Dragonfly):

     Registry                             Registry
        │                                    │
        │ 1000 requests                      │ ~10 requests
        │                                    │
   ┌────┴────┐                          ┌────┴────┐
   │         │                          │         │
   ▼         ▼                          ▼         ▼
┌─────┐   ┌─────┐                    ┌─────┐◄──►┌─────┐
│Node1│   │Node2│   ...              │Node1│    │Node2│
└─────┘   └─────┘                    └──┬──┘    └──┬──┘
   │         │                          │          │
   ▼         ▼                          ▼          ▼
┌─────┐   ┌─────┐                    ┌─────┐◄──►┌─────┐
│Node3│   │Node4│                    │Node3│    │Node4│
└─────┘   └─────┘                    └─────┘    └─────┘

1000-node deploy time: 30 min        1000-node deploy time: 3 min
Registry bandwidth: 1000x            Registry bandwidth: ~10x
Failure mode: Registry overload      Failure mode: Graceful degradation
```

Dragonfly makes the impossible possible: deploying to thousands of nodes in minutes, not hours.

## Did You Know?

- **Origin**: Dragonfly was created at Alibaba to solve their Singles' Day scaling problems—imagine deploying to 10,000+ nodes for the world's largest shopping event
- **CNCF Incubating**: Graduated from sandbox in 2020, widely adopted in production
- **Bandwidth Savings**: Organizations report 90%+ reduction in registry egress bandwidth
- **Not Just Images**: Dragonfly can distribute any large file—ML models, datasets, artifacts
- **Ant Group Scale**: Handles distribution to hundreds of thousands of nodes daily

## Dragonfly Architecture

```
DRAGONFLY ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                         ┌─────────────────────────────────────┐
                         │              Manager                │
                         │                                     │
                         │  • Cluster coordination             │
                         │  • Scheduler selection              │
                         │  • Metrics & monitoring             │
                         │  • Peer discovery                   │
                         └────────────────┬────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
           ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
           │   Scheduler    │    │   Scheduler    │    │   Scheduler    │
           │   (Region A)   │    │   (Region B)   │    │   (Region C)   │
           │                │    │                │    │                │
           │ • Seed peer    │    │ • Seed peer    │    │ • Seed peer    │
           │ • Task mgmt    │    │ • Task mgmt    │    │ • Task mgmt    │
           │ • Piece sched  │    │ • Piece sched  │    │ • Piece sched  │
           └───────┬────────┘    └───────┬────────┘    └───────┬────────┘
                   │                     │                     │
          ┌────────┴────────┐   ┌────────┴────────┐   ┌────────┴────────┐
          │                 │   │                 │   │                 │
          ▼                 ▼   ▼                 ▼   ▼                 ▼
     ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
     │  Dfdaemon│      │  Dfdaemon│      │  Dfdaemon│      │  Dfdaemon│
     │ (Node 1)│◄────▶│ (Node 2)│◄────▶│ (Node 3)│◄────▶│ (Node 4)│
     │         │      │         │      │         │      │         │
     │ • Peer  │      │ • Peer  │      │ • Peer  │      │ • Peer  │
     │ • Proxy │      │ • Proxy │      │ • Proxy │      │ • Proxy │
     │ • Cache │      │ • Cache │      │ • Cache │      │ • Cache │
     └─────────┘      └─────────┘      └─────────┘      └─────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
     ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
     │Container│      │Container│      │Container│      │Container│
     │ Runtime │      │ Runtime │      │ Runtime │      │ Runtime │
     └─────────┘      └─────────┘      └─────────┘      └─────────┘

COMPONENT ROLES:
─────────────────────────────────────────────────────────────────────────────
Manager     • Central coordination for multiple schedulers
            • Stores cluster topology and peer information
            • REST API for management operations

Scheduler   • Regional coordinator and seed peer
            • First to download from source registry
            • Breaks files into pieces and coordinates distribution
            • Tracks which peers have which pieces

Dfdaemon    • Runs on every node as DaemonSet
            • Intercepts container runtime pulls
            • Downloads pieces from scheduler or other peers
            • Shares downloaded pieces with other peers
            • Caches content locally
```

### How P2P Distribution Works

```
P2P PIECE DISTRIBUTION
─────────────────────────────────────────────────────────────────────────────

Image layer: [======================================] 100MB

Split into pieces:
[====][====][====][====][====][====][====][====][====][====]
  P1    P2    P3    P4    P5    P6    P7    P8    P9   P10
 10MB  10MB  10MB  10MB  10MB  10MB  10MB  10MB  10MB  10MB

Distribution timeline:
─────────────────────────────────────────────────────────────────────────────

T=0: Scheduler downloads from registry
     Scheduler: [P1][P2][P3][P4][P5][P6][P7][P8][P9][P10]
     Node A:    [  ][  ][  ][  ][  ][  ][  ][  ][  ][  ]
     Node B:    [  ][  ][  ][  ][  ][  ][  ][  ][  ][  ]
     Node C:    [  ][  ][  ][  ][  ][  ][  ][  ][  ][  ]

T=1: Scheduler shares pieces with nodes
     Scheduler: [P1][P2][P3][P4][P5][P6][P7][P8][P9][P10]
     Node A:    [P1][  ][P3][  ][  ][  ][  ][  ][  ][  ] ← from scheduler
     Node B:    [  ][P2][  ][P4][  ][  ][  ][  ][  ][  ] ← from scheduler
     Node C:    [  ][  ][  ][  ][P5][P6][  ][  ][  ][  ] ← from scheduler

T=2: Nodes share pieces with each other
     Scheduler: [P1][P2][P3][P4][P5][P6][P7][P8][P9][P10]
     Node A:    [P1][P2][P3][P4][P5][P6][  ][  ][  ][  ] ← P2,P4 from B, P5,P6 from C
     Node B:    [P1][P2][P3][P4][P5][P6][  ][  ][  ][  ] ← P1,P3 from A, P5,P6 from C
     Node C:    [P1][P2][P3][P4][P5][P6][  ][  ][  ][  ] ← P1-P4 from A,B

T=3: Continue until all nodes have all pieces
     All nodes: [P1][P2][P3][P4][P5][P6][P7][P8][P9][P10] ✓

Registry bandwidth used: 100MB (scheduler only)
Without P2P: 300MB (100MB × 3 nodes)
Savings: 66%

At 1000 nodes:
Registry bandwidth with Dragonfly: ~100MB
Registry bandwidth without: 100GB
Savings: 99%+
```

## Deploying Dragonfly

### Prerequisites

```bash
# Create kind cluster with enough nodes to demonstrate P2P
cat <<EOF | kind create cluster --name dragonfly-lab --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
- role: worker
EOF

# Verify nodes
kubectl get nodes
```

### Option 1: Helm Deployment (Recommended)

```bash
# Add Dragonfly Helm repository
helm repo add dragonfly https://dragonflyoss.github.io/helm-charts/
helm repo update

# Create namespace
kubectl create namespace dragonfly-system

# Create values file
cat > dragonfly-values.yaml <<EOF
manager:
  replicas: 1
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  metrics:
    enable: true

scheduler:
  replicas: 1
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  config:
    verbose: true

seedPeer:
  replicas: 1
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  config:
    verbose: true

dfdaemon:
  # Runs on every node
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  config:
    verbose: true
    proxy:
      registryMirror:
        # Proxy all registries through Dragonfly
        dynamic: true
        url: https://index.docker.io
      proxies:
        - regx: blobs/sha256.*

# For containerd runtime
containerRuntime:
  containerd:
    enable: true
    injectConfigPath: true
    registries:
      - hostNamespace: docker.io
        serverAddr: https://index.docker.io
        capabilities: ["pull", "resolve"]

# Enable console UI
jaeger:
  enable: false

mysql:
  enable: true
  primary:
    resources:
      requests:
        cpu: 100m
        memory: 256Mi

redis:
  enable: true
  master:
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
EOF

# Install Dragonfly
helm install dragonfly dragonfly/dragonfly \
  --namespace dragonfly-system \
  -f dragonfly-values.yaml \
  --wait

# Verify all components are running
kubectl -n dragonfly-system get pods

# Expected output:
# dragonfly-dfdaemon-xxxxx     Running (one per node)
# dragonfly-manager-xxxxx      Running
# dragonfly-mysql-xxxxx        Running
# dragonfly-redis-xxxxx        Running
# dragonfly-scheduler-xxxxx    Running
# dragonfly-seed-peer-xxxxx    Running
```

### Option 2: Manual Deployment

For understanding the components:

```yaml
# manager.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dragonfly-manager
  namespace: dragonfly-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dragonfly-manager
  template:
    metadata:
      labels:
        app: dragonfly-manager
    spec:
      containers:
      - name: manager
        image: dragonflyoss/manager:v2.1.0
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 65003
          name: grpc
        env:
        - name: DRAGONFLY_MANAGER_DATABASE_TYPE
          value: mysql
        - name: DRAGONFLY_MANAGER_DATABASE_MYSQL_HOST
          value: mysql
        volumeMounts:
        - name: config
          mountPath: /etc/dragonfly
      volumes:
      - name: config
        configMap:
          name: dragonfly-manager-config
---
# scheduler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dragonfly-scheduler
  namespace: dragonfly-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dragonfly-scheduler
  template:
    metadata:
      labels:
        app: dragonfly-scheduler
    spec:
      containers:
      - name: scheduler
        image: dragonflyoss/scheduler:v2.1.0
        ports:
        - containerPort: 8002
          name: http
        - containerPort: 65002
          name: grpc
        volumeMounts:
        - name: config
          mountPath: /etc/dragonfly
      volumes:
      - name: config
        configMap:
          name: dragonfly-scheduler-config
---
# dfdaemon.yaml (DaemonSet - runs on every node)
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: dragonfly-dfdaemon
  namespace: dragonfly-system
spec:
  selector:
    matchLabels:
      app: dragonfly-dfdaemon
  template:
    metadata:
      labels:
        app: dragonfly-dfdaemon
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: dfdaemon
        image: dragonflyoss/dfdaemon:v2.1.0
        securityContext:
          privileged: true
        ports:
        - containerPort: 65001
          name: grpc
        - containerPort: 65002
          name: proxy
        volumeMounts:
        - name: config
          mountPath: /etc/dragonfly
        - name: containerd-socket
          mountPath: /run/containerd/containerd.sock
        - name: cache
          mountPath: /var/lib/dragonfly
      volumes:
      - name: config
        configMap:
          name: dragonfly-dfdaemon-config
      - name: containerd-socket
        hostPath:
          path: /run/containerd/containerd.sock
      - name: cache
        hostPath:
          path: /var/lib/dragonfly
          type: DirectoryOrCreate
```

## Configuring Container Runtime Integration

### containerd Configuration

Dragonfly integrates with containerd by configuring registry mirrors:

```toml
# /etc/containerd/config.toml (on each node)
version = 2

[plugins."io.containerd.grpc.v1.cri".registry]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
      endpoint = ["http://127.0.0.1:65001", "https://index.docker.io"]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."gcr.io"]
      endpoint = ["http://127.0.0.1:65001", "https://gcr.io"]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."ghcr.io"]
      endpoint = ["http://127.0.0.1:65001", "https://ghcr.io"]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."harbor.example.com"]
      endpoint = ["http://127.0.0.1:65001", "https://harbor.example.com"]
```

The Helm chart handles this automatically with `containerRuntime.containerd.enable: true`.

### Docker Configuration (Legacy)

```json
{
  "registry-mirrors": ["http://127.0.0.1:65001"],
  "insecure-registries": ["127.0.0.1:65001"]
}
```

## Dragonfly Configuration

### Dfdaemon Configuration

```yaml
# dfdaemon config
server:
  # Listen address
  listen:
    ip: 0.0.0.0
    port: 65001

# Scheduler connection
scheduler:
  manager:
    enable: true
    netAddrs:
      - type: tcp
        addr: dragonfly-manager.dragonfly-system.svc:65003
    refreshInterval: 5m

# Proxy configuration
proxy:
  # Enable registry proxy
  registryMirror:
    # Dynamic proxying for all registries
    dynamic: true
    # Default upstream
    url: https://index.docker.io
    # Insecure registries
    insecure: false

  # Specific proxy rules
  proxies:
    # Only proxy blob downloads (not manifests)
    - regx: blobs/sha256.*
    # Or proxy everything
    # - regx: .*

# Peer configuration
download:
  # Piece size for P2P distribution
  pieceSize: 4Mi
  # Concurrent download limit
  concurrentPieceCount: 16
  # Total rate limit
  totalRateLimit: 2Gi
  # Per-peer rate limit
  perPeerRateLimit: 512Mi

# Cache configuration
storage:
  # Local cache directory
  taskExpireTime: 6h
  diskGCThreshold: 50Gi
  diskGCThresholdPercent: 0.8

# Security
security:
  # Disable for testing, enable in production
  autoIssueCert: false
```

### Scheduler Configuration

```yaml
# scheduler config
server:
  listen:
    ip: 0.0.0.0
    port: 8002
  advertiseIP: 0.0.0.0

# Scheduling algorithm configuration
scheduler:
  # Algorithm: default or ml (machine learning based)
  algorithm: default

  # Back-to-source configuration
  backToSourceCount: 3

  # Retry configuration
  retryBackToSourceLimit: 5
  retryLimit: 10
  retryInterval: 1s

# Piece configuration
pieceDownloadTimeout: 30s

# Manager connection
manager:
  enable: true
  addr: dragonfly-manager.dragonfly-system.svc:65003
  schedulerClusterID: 1
```

## Integrating with Harbor

Dragonfly works seamlessly with Harbor as the upstream registry:

```
DRAGONFLY + HARBOR ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                    ┌─────────────────────────────────────┐
                    │              Harbor                 │
                    │         (Source of Truth)           │
                    │  • Image storage                    │
                    │  • Vulnerability scanning           │
                    │  • RBAC / Authentication           │
                    └────────────────┬────────────────────┘
                                     │
                                     │ Authenticated pull
                                     │ (only by scheduler)
                                     ▼
                    ┌─────────────────────────────────────┐
                    │         Dragonfly Scheduler         │
                    │            (Seed Peer)              │
                    │  • Downloads once from Harbor      │
                    │  • Splits into pieces              │
                    │  • Coordinates P2P distribution    │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │ Dfdaemon  │◄──▶│ Dfdaemon  │◄──▶│ Dfdaemon  │
            │ (Node 1)  │    │ (Node 2)  │    │ (Node N)  │
            └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
                  │                │                │
                  ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │ Container │    │ Container │    │ Container │
            │  Runtime  │    │  Runtime  │    │  Runtime  │
            └───────────┘    └───────────┘    └───────────┘
```

Configure dfdaemon for Harbor with authentication:

```yaml
# dfdaemon config with Harbor
proxy:
  registryMirror:
    dynamic: true
    url: https://harbor.example.com

  # Harbor credentials for authenticated pulls
  registries:
    - url: https://harbor.example.com
      host: harbor.example.com
      username: robot$dragonfly
      password: ${HARBOR_ROBOT_PASSWORD}
      insecure: false

  proxies:
    - regx: blobs/sha256.*
      useHTTPS: true
```

## Monitoring Dragonfly

### Prometheus Metrics

Dragonfly exposes comprehensive metrics:

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dragonfly
  namespace: dragonfly-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: dragonfly
  endpoints:
  - port: metrics
    interval: 30s
```

Key metrics:

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `dragonfly_dfdaemon_download_task_total` | Total download tasks | N/A |
| `dragonfly_dfdaemon_download_traffic_total` | Bytes downloaded | N/A |
| `dragonfly_dfdaemon_upload_traffic_total` | Bytes uploaded to peers | N/A |
| `dragonfly_dfdaemon_proxy_request_total` | Proxy requests | > 1000/min |
| `dragonfly_scheduler_download_peer_total` | Active peers | N/A |
| `dragonfly_scheduler_download_piece_cost_seconds` | Piece download latency | > 10s |
| `dragonfly_manager_peer_total` | Total registered peers | N/A |

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Dragonfly Overview",
    "panels": [
      {
        "title": "P2P Traffic Ratio",
        "targets": [{
          "expr": "sum(rate(dragonfly_dfdaemon_upload_traffic_total[5m])) / sum(rate(dragonfly_dfdaemon_download_traffic_total[5m]))"
        }],
        "description": "Higher is better - more P2P, less registry load"
      },
      {
        "title": "Back-to-Source Rate",
        "targets": [{
          "expr": "rate(dragonfly_dfdaemon_download_task_total{type=\"back_to_source\"}[5m])"
        }],
        "description": "Downloads directly from registry (should be low)"
      },
      {
        "title": "Active Peers per Scheduler",
        "targets": [{
          "expr": "dragonfly_scheduler_download_peer_total"
        }]
      },
      {
        "title": "Download Latency P99",
        "targets": [{
          "expr": "histogram_quantile(0.99, rate(dragonfly_scheduler_download_piece_cost_seconds_bucket[5m]))"
        }]
      }
    ]
  }
}
```

### Dragonfly Console

Dragonfly includes a web console for visualization:

```bash
# Port-forward to manager console
kubectl -n dragonfly-system port-forward svc/dragonfly-manager 8080:8080

# Open browser to http://localhost:8080
```

The console shows:
- Cluster topology
- Active downloads
- Peer connections
- Task history
- Configuration

## Advanced Configuration

### Multi-Cluster Distribution

```
MULTI-CLUSTER WITH DRAGONFLY
─────────────────────────────────────────────────────────────────────────────

                        ┌─────────────────┐
                        │  Harbor (HQ)    │
                        └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   Cluster A     │ │   Cluster B     │ │   Cluster C     │
    │   (US-East)     │ │   (EU-West)     │ │   (AP-South)    │
    │                 │ │                 │ │                 │
    │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
    │  │ Scheduler │  │ │  │ Scheduler │  │ │  │ Scheduler │  │
    │  └─────┬─────┘  │ │  └─────┬─────┘  │ │  └─────┬─────┘  │
    │        │        │ │        │        │ │        │        │
    │  ┌─────┴─────┐  │ │  ┌─────┴─────┐  │ │  ┌─────┴─────┐  │
    │  │ Dfdaemons │  │ │  │ Dfdaemons │  │ │  │ Dfdaemons │  │
    │  │ (100 nodes)│ │ │  │ (200 nodes)│ │ │  │ (150 nodes)│ │
    │  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
    └─────────────────┘ └─────────────────┘ └─────────────────┘

Each cluster has its own scheduler that:
1. Pulls from Harbor (once per cluster)
2. Distributes via P2P within the cluster
3. Shares peer information with manager

Harbor sees: 3 pulls (one per cluster)
Without Dragonfly: 450 pulls (one per node)
```

### Preheating (Pre-distribution)

Proactively distribute images before deployment:

```bash
# Preheat an image across the cluster
curl -X POST "http://dragonfly-manager:8080/api/v1/preheat" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "image",
    "url": "harbor.example.com/production/myapp:v2.0.0",
    "scope": "all_peers",
    "headers": {
      "Authorization": "Bearer ${TOKEN}"
    }
  }'

# Check preheat status
curl "http://dragonfly-manager:8080/api/v1/preheat/{job_id}"
```

Create preheat CronJob for critical images:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: preheat-base-images
  namespace: dragonfly-system
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: preheat
            image: curlimages/curl
            command:
            - /bin/sh
            - -c
            - |
              for IMAGE in \
                "harbor.example.com/library/nginx:1.25" \
                "harbor.example.com/library/alpine:3.19" \
                "harbor.example.com/base/python:3.12"; do
                curl -X POST "http://dragonfly-manager:8080/api/v1/preheat" \
                  -H "Content-Type: application/json" \
                  -d "{\"type\":\"image\",\"url\":\"$IMAGE\"}"
              done
          restartPolicy: OnFailure
```

### Rate Limiting

Protect network bandwidth:

```yaml
# Per-node rate limiting in dfdaemon config
download:
  # Total download rate limit per node
  totalRateLimit: 1Gi
  # Rate limit for each peer connection
  perPeerRateLimit: 200Mi

# Scheduler-level rate limiting
scheduler:
  # Limit concurrent back-to-source downloads
  backToSourceCount: 5
```

## War Story: The Alibaba Singles' Day

This is Dragonfly's origin story—solving the largest deployment challenge on Earth.

**The Challenge**:
Singles' Day (11/11) is the world's biggest shopping event. Alibaba needed to:
- Deploy updates to 10,000+ nodes
- Complete in under 10 minutes
- Handle traffic spikes of millions of requests/second
- Zero downtime during peak shopping

**The Traditional Approach (Failed)**:

```
10,000 nodes × 500MB image = 5TB bandwidth
Single registry: 500MB/s max throughput
Time: 10,000 seconds = 2.7 hours

Result: Deployments timed out. Services couldn't scale.
```

**The Dragonfly Solution**:

```
Initial seed: 500MB (1 download to scheduler)
P2P distribution: Each node downloads ~500MB but shares with 10 peers
Effective bandwidth: Multiplied by peer count
Time: < 5 minutes for 10,000 nodes
```

**Key Optimizations**:
1. **Intelligent piece scheduling**: Hot pieces distributed first
2. **Locality awareness**: Prefer peers in same rack/zone
3. **Preheating**: Popular images pre-distributed
4. **Back-pressure**: Rate limiting prevented network saturation

**The Results**:
- Deployment time: 2.7 hours → 5 minutes
- Registry bandwidth: 95% reduction
- Success rate: 99.99%
- Scaled to 100,000+ nodes in subsequent years

**The Lesson**: At massive scale, P2P isn't an optimization—it's the only way.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No piece size tuning | Poor performance on slow networks | Adjust `pieceSize` based on RTT |
| Proxying manifests | Authentication issues, extra latency | Only proxy blob downloads |
| No cache cleanup | Disk fills up | Configure `diskGCThreshold` |
| Single scheduler | Bottleneck for large clusters | Deploy multiple schedulers by region |
| No rate limiting | Network saturation | Set `totalRateLimit` and `perPeerRateLimit` |
| Skipping preheating | Cold cache on deploy | Preheat critical images |
| No monitoring | Silent failures | Enable metrics, set up alerts |
| Wrong containerd config | Falls back to direct pull | Verify mirror configuration |

## Quiz

Test your understanding of Dragonfly:

<details>
<summary>1. How does Dragonfly reduce registry bandwidth consumption?</summary>

**Answer**: Dragonfly uses peer-to-peer distribution. The scheduler (seed peer) downloads from the registry once, then splits content into pieces. Nodes download pieces from the scheduler and each other. Each piece is downloaded from the registry only once, then shared among peers. At 1000 nodes, this reduces registry load from 1000x to ~1x.
</details>

<details>
<summary>2. What is the role of the dfdaemon component?</summary>

**Answer**: Dfdaemon runs on every node as a DaemonSet. It: (1) Intercepts container runtime pull requests via proxy, (2) Downloads pieces from scheduler or peers, (3) Uploads pieces to other requesting peers, (4) Caches downloaded content locally, (5) Reports status to scheduler for coordination.
</details>

<details>
<summary>3. Why should you only proxy blob downloads, not manifests?</summary>

**Answer**: Manifests are small (~KB) and contain image metadata including digests. Proxying manifests: (1) Adds latency for minimal gain, (2) Can cause authentication issues if manifest endpoint differs, (3) Digests in manifests must match—corruption breaks pulls. Blobs (layers) are large (~MB-GB) and benefit from P2P distribution.
</details>

<details>
<summary>4. What is preheating and when should you use it?</summary>

**Answer**: Preheating proactively distributes images before they're needed. Use it for: (1) Critical production images before deployment, (2) Base images used by many applications, (3) Large ML models before inference starts, (4) After security updates to popular images. Preheating ensures the first deploy doesn't suffer cold-cache latency.
</details>

<details>
<summary>5. How does Dragonfly integrate with Harbor?</summary>

**Answer**: Dragonfly sits between the container runtime and Harbor. Configure dfdaemon to proxy Harbor URLs with credentials. The scheduler authenticates to Harbor once, downloads images, then distributes via P2P. Nodes never contact Harbor directly—all traffic goes through dfdaemon → scheduler → Harbor. This preserves Harbor's security (RBAC, scanning) while adding P2P scale.
</details>

<details>
<summary>6. What metrics indicate healthy P2P distribution?</summary>

**Answer**: Key health indicators: (1) High P2P traffic ratio (upload/download > 0.5), (2) Low back-to-source rate (most pulls from peers), (3) Low piece download latency (<5s P99), (4) High peer utilization (peers actively sharing). Problems: High back-to-source = cache misses; low upload = peers not sharing.
</details>

<details>
<summary>7. How do you size a Dragonfly deployment?</summary>

**Answer**: Sizing guidelines: (1) Manager: 1 per cluster, 256MB-1GB RAM, (2) Scheduler: 1 per 500-1000 nodes or per region, 256MB-512MB RAM each, (3) Dfdaemon: 1 per node (DaemonSet), 256MB-512MB RAM, disk cache 10-50GB, (4) Seed peers: 1-3 for large clusters, beefy network. Scale schedulers for more parallelism.
</details>

<details>
<summary>8. What happens if Dragonfly fails during a pull?</summary>

**Answer**: Dragonfly has graceful degradation. If dfdaemon can't reach scheduler or peers, it falls back to direct registry pull (back-to-source). The container runtime sees a successful pull regardless. Temporary Dragonfly failures don't break deployments—they just lose P2P benefits. Configure `retryLimit` and `retryInterval` for transient issues.
</details>

## Hands-On Exercise: Deploy Dragonfly and Measure P2P Benefits

### Objective
Deploy Dragonfly on a multi-node cluster and measure the bandwidth savings from P2P distribution.

### Environment Setup

```bash
# Create kind cluster with 4 nodes
cat <<EOF | kind create cluster --name dragonfly-lab --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
- role: worker
EOF

# Verify nodes
kubectl get nodes
```

### Step 1: Deploy Dragonfly

```bash
# Add Helm repo
helm repo add dragonfly https://dragonflyoss.github.io/helm-charts/
helm repo update

# Create namespace
kubectl create namespace dragonfly-system

# Create minimal values for testing
cat > dragonfly-values.yaml <<EOF
manager:
  replicas: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"

scheduler:
  replicas: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"

seedPeer:
  replicas: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"

dfdaemon:
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"
  config:
    proxy:
      registryMirror:
        dynamic: true
        url: https://index.docker.io
      proxies:
        - regx: blobs/sha256.*

containerRuntime:
  containerd:
    enable: false  # kind handles this differently

mysql:
  enable: true
  primary:
    resources:
      requests:
        memory: "128Mi"

redis:
  enable: true
  master:
    resources:
      requests:
        memory: "128Mi"
EOF

# Install Dragonfly
helm install dragonfly dragonfly/dragonfly \
  --namespace dragonfly-system \
  -f dragonfly-values.yaml

# Wait for deployment (this takes a few minutes)
kubectl -n dragonfly-system wait --for=condition=ready pod -l app.kubernetes.io/name=dragonfly --timeout=300s

# Verify all pods are running
kubectl -n dragonfly-system get pods
```

### Step 2: Configure Test Environment

```bash
# Get dfdaemon proxy address
DFDAEMON_PORT=$(kubectl -n dragonfly-system get svc dragonfly-dfdaemon -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "65001")

# For testing, we'll create a deployment that uses the dfdaemon proxy
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: pull-test-script
  namespace: default
data:
  test.sh: |
    #!/bin/bash
    echo "Starting pull test at \$(date)"
    echo "Node: \$(hostname)"

    # Record start time
    START=\$(date +%s.%N)

    # Pull image (this goes through dfdaemon if configured)
    crictl pull docker.io/library/nginx:1.25-alpine

    # Record end time
    END=\$(date +%s.%N)

    # Calculate duration
    DURATION=\$(echo "\$END - \$START" | bc)
    echo "Pull completed in \${DURATION}s"
EOF
```

### Step 3: Test Without P2P (Baseline)

```bash
# Create test pods on each worker node
for i in 1 2 3; do
  kubectl run pull-test-$i \
    --image=busybox \
    --restart=Never \
    --overrides="{\"spec\":{\"nodeName\":\"dragonfly-lab-worker$([[ $i -gt 1 ]] && echo $i || echo '')\"}}" \
    --command -- sh -c "time wget -q https://index.docker.io/v2/ && sleep infinity" &
done
wait

# Check pods are scheduled to different nodes
kubectl get pods -o wide | grep pull-test
```

### Step 4: Test With P2P

```bash
# Deploy test pods that simulate large image pulls
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: p2p-test
  namespace: default
spec:
  selector:
    matchLabels:
      app: p2p-test
  template:
    metadata:
      labels:
        app: p2p-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
EOF

# Watch pods start on all nodes
kubectl get pods -l app=p2p-test -o wide -w

# Check Dragonfly metrics
kubectl -n dragonfly-system port-forward svc/dragonfly-manager 8080:8080 &
sleep 2

# Get download statistics
curl -s http://localhost:8080/api/v1/tasks | jq '.[] | {id, state, contentLength}' | head -20
```

### Step 5: Verify P2P Distribution

```bash
# Check dfdaemon logs for P2P activity
kubectl -n dragonfly-system logs -l component=dfdaemon --tail=50 | grep -E "(peer|piece|download)"

# Check scheduler logs
kubectl -n dragonfly-system logs -l component=scheduler --tail=50 | grep -E "(task|peer)"

# Get metrics
kubectl -n dragonfly-system port-forward svc/dragonfly-scheduler 8002:8002 &
sleep 2

curl -s http://localhost:8002/metrics | grep dragonfly
```

### Step 6: Measure Bandwidth Savings

```bash
# Calculate P2P efficiency
echo "Checking Dragonfly metrics..."

# Get traffic stats from dfdaemon
for pod in $(kubectl -n dragonfly-system get pods -l component=dfdaemon -o name); do
  echo "Stats for $pod:"
  kubectl -n dragonfly-system exec $pod -- cat /var/lib/dragonfly/stats.json 2>/dev/null || echo "  No stats available"
done

# The key metric is: bytes from peers vs bytes from source
# Higher peer percentage = better P2P distribution
```

### Success Criteria

- [ ] Dragonfly components deployed (manager, scheduler, dfdaemon)
- [ ] DaemonSet pods running on all nodes
- [ ] P2P traffic visible in dfdaemon logs
- [ ] Metrics endpoint returning data
- [ ] Subsequent pulls faster than first pull

### Cleanup

```bash
# Kill port-forwards
pkill -f "port-forward"

# Delete test resources
kubectl delete daemonset p2p-test
kubectl delete pods -l run=pull-test

# Delete Dragonfly
helm uninstall dragonfly -n dragonfly-system
kubectl delete namespace dragonfly-system

# Delete cluster
kind delete cluster --name dragonfly-lab
```

## Key Takeaways

1. **P2P solves the thundering herd**: Registry sees 1 request instead of N
2. **Three components**: Manager (coordination), Scheduler (seed/scheduling), Dfdaemon (per-node agent)
3. **Works with any registry**: Harbor, Zot, DockerHub, private registries
4. **Proxy configuration is key**: Only proxy blobs, not manifests
5. **Preheating prevents cold starts**: Push images to the mesh before deployment
6. **Rate limiting protects networks**: Configure per-node and per-peer limits
7. **Graceful degradation**: Falls back to direct pull if P2P fails
8. **Monitor P2P ratio**: High peer traffic = successful distribution
9. **Scale schedulers by region**: Reduce latency for large clusters
10. **Origin story matters**: Born from Alibaba's extreme scale requirements

## Next Steps

You've completed the Container Registries toolkit! You now understand:
- **Harbor**: Enterprise registry with scanning, RBAC, replication
- **Zot**: Minimal OCI-native registry for edge and simplicity
- **Dragonfly**: P2P distribution for massive scale

Continue to the [K8s Distributions Toolkit](../k8s-distributions/README.md) to explore k3s, k0s, and other lightweight Kubernetes distributions.

---

*"At scale, peer-to-peer isn't an optimization—it's the only architecture that works."*
