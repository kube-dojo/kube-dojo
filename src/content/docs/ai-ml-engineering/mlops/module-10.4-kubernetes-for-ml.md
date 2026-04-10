---
title: "Kubernetes for ML"
slug: ai-ml-engineering/mlops/module-10.4-kubernetes-for-ml
sidebar:
  order: 1105
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 6-8
> **Migrated from neural-dojo** — pending pipeline polish

## The Black Friday Meltdown

**Seattle. November 24, 2023. 6:02 AM.**

The recommendation engine at ShopSmart was supposed to handle Black Friday traffic. It didn't.

At 6:00 AM sharp, traffic spiked 40x. The single ML inference server—running on a beefy EC2 instance—handled the first 60 seconds heroically. By 6:02, response times hit 30 seconds. By 6:05, the server crashed entirely.

Elena Martinez, the DevOps lead, scrambled to spin up more instances manually. By the time each new server was configured and running, the backlog had grown worse. Every minute of downtime cost the company an estimated $180,000 in lost sales.

The post-mortem was brutal: "We had one server. When it died, everything died with it."

The solution? Kubernetes. The following year, ShopSmart ran their recommendation engine on a Kubernetes cluster that automatically scaled from 3 pods to 47 pods during the Black Friday rush—and back down to 3 when traffic subsided. No manual intervention. No downtime. The entire infrastructure bill? 40% lower than the year before.

> "Kubernetes isn't about containers. It's about never getting paged at 6 AM on Black Friday again."
> — Elena Martinez, speaking at KubeCon 2024

This module teaches you how to run ML workloads on Kubernetes—so your models can scale with demand, recover from failures, and let you sleep through Black Friday.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Understand Kubernetes architecture and core concepts
- Deploy ML inference services on Kubernetes
- Configure GPU scheduling with NVIDIA GPU Operator
- Manage resources (CPU, memory, GPU) for ML workloads
- Implement autoscaling for inference services
- Set up persistent storage for models and data

---

## Why This Module Matters

### The Scaling Challenge

Think of your ML model like a restaurant. When it's just you cooking for friends, a home kitchen works fine. But when you need to serve 10,000 customers per hour, you need a commercial kitchen: standardized stations, multiple cooks, a system for handling rush hour, and the ability to bring in extra staff when needed.

Kubernetes is that commercial kitchen for ML models. It handles the orchestration—scheduling workloads, scaling up and down, recovering from failures, and managing resources—so you can focus on the food (your model).

Your ML model works great on your laptop. Now you need to:
- Serve 10,000 requests per second
- Handle traffic spikes during peak hours
- Deploy updates without downtime
- Run across multiple servers
- Manage GPU resources efficiently

```
THE PRODUCTION ML SCALING PROBLEM
=================================

Single Server:
┌─────────────────┐
│   ML Model      │  ← What happens when this dies?
│   (1 instance)  │  ← Can't handle 10K req/sec
└─────────────────┘  ← No GPU sharing

Kubernetes Solution:
┌─────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Pod 1   │  │ Pod 2   │  │ Pod 3   │  │ Pod N   │   │
│  │(replica)│  │(replica)│  │(replica)│  │(replica)│   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│       ↑            ↑            ↑            ↑         │
│       └────────────┴────────────┴────────────┘         │
│                         │                               │
│                  Load Balancer                          │
│                         │                               │
│                    Autoscaler                           │
│            (scale based on CPU/GPU/queue)               │
└─────────────────────────────────────────────────────────┘
```

**Did You Know?** Google runs over 2 billion containers per week using Borg, the internal predecessor to Kubernetes. When Google open-sourced Kubernetes in 2014, they brought 15 years of container orchestration experience. The name "Kubernetes" (κυβερνήτης) is Greek for "helmsman" or "pilot."

### What Kubernetes Solves for ML

```
┌─────────────────────────────────────────────────────────────────────┐
│                 KUBERNETES BENEFITS FOR ML                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. SCALABILITY                                                     │
│     Auto-scale from 1 to 100 replicas based on load                │
│     Handle traffic spikes without manual intervention               │
│                                                                     │
│  2. HIGH AVAILABILITY                                               │
│     If a pod dies, Kubernetes restarts it automatically            │
│     Spread replicas across nodes for fault tolerance                │
│                                                                     │
│  3. GPU MANAGEMENT                                                  │
│     Schedule ML workloads on GPU nodes                              │
│     Share GPUs across multiple pods (MIG, time-slicing)            │
│                                                                     │
│  4. RESOURCE EFFICIENCY                                             │
│     Pack multiple workloads on same hardware                        │
│     Set limits to prevent noisy neighbors                           │
│                                                                     │
│  5. DEPLOYMENT FLEXIBILITY                                          │
│     Rolling updates, canary deployments, blue-green                 │
│     Rollback instantly if deployment fails                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ️ Kubernetes Architecture

### Core Components

```
KUBERNETES CLUSTER ARCHITECTURE
================================

┌─────────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  API Server  │  │  Scheduler   │  │  Controller  │              │
│  │              │  │              │  │   Manager    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         │                │                  │                       │
│         └────────────────┴──────────────────┘                       │
│                          │                                          │
│                    ┌─────┴─────┐                                    │
│                    │   etcd    │  (cluster state database)          │
│                    └───────────┘                                    │
└─────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   WORKER NODE   │  │   WORKER NODE   │  │   GPU NODE      │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │  kubelet  │  │  │  │  kubelet  │  │  │  │  kubelet  │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │kube-proxy │  │  │  │kube-proxy │  │  │  │kube-proxy │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │ Container │  │  │  │ Container │  │  │  │  NVIDIA   │  │
│  │  Runtime  │  │  │  │  Runtime  │  │  │  │  Runtime  │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
│                 │  │                 │  │  ┌───────────┐  │
│  [Pod][Pod]     │  │  [Pod][Pod]     │  │  │    GPU    │  │
│                 │  │                 │  │  └───────────┘  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Key Concepts

Think of Kubernetes concepts like a shipping company:

- **Pod** = A shipping container (holds your cargo/application)
- **Deployment** = The fleet manager (ensures the right number of containers are running)
- **Service** = The loading dock (a stable address where trucks can pick up cargo)
- **ConfigMap** = The shipping manifest (what's inside, where it's going)
- **Secret** = The locked safe (valuable cargo that needs protection)
- **PersistentVolume** = The warehouse (storage that exists even when containers move)
- **Namespace** = Different wings of the warehouse (isolation between teams)

```yaml
# Pod: Smallest deployable unit (one or more containers)
# Deployment: Manages replica sets and rolling updates
# Service: Stable network endpoint for pods
# ConfigMap: Configuration data
# Secret: Sensitive data (API keys, passwords)
# PersistentVolume: Storage that outlives pods
# Namespace: Virtual cluster for isolation

CONCEPT HIERARCHY
=================

Namespace (isolation boundary)
    │
    └── Deployment (manages replicas)
            │
            └── ReplicaSet (ensures N pods running)
                    │
                    └── Pod (runs containers)
                            │
                            └── Container (your app)
```

**Did You Know?** The Kubernetes "control loop" pattern is inspired by control theory in engineering. The controller continuously compares the desired state (specified in YAML) with the actual state (observed in cluster), and takes actions to reconcile any differences. This is why Kubernetes is "declarative"—you tell it what you want, not how to get there.

---

##  Core Kubernetes Objects

Understanding Kubernetes objects is like learning the vocabulary of a new language. Each object type has a specific purpose, and they compose together to build sophisticated systems. Let's walk through each one, starting with the simplest and building up to more complex abstractions.

### Pod

The smallest deployable unit in Kubernetes—and the most fundamental concept to understand. A Pod is a wrapper around one or more containers that share networking and storage. Usually you'll run one container per Pod, but there are cases (like sidecars for logging or service meshes) where multiple containers make sense.

Think of a Pod like an apartment unit in a building. The apartment (Pod) has its own address and utilities, and the people living inside (containers) share the kitchen and bathroom. They can talk to each other easily, but communicating with people in other apartments requires going through the building's hallways (the cluster network).

```yaml
# pod.yaml - Basic ML inference pod
apiVersion: v1
kind: Pod
metadata:
  name: ml-inference
  labels:
    app: sentiment-classifier
spec:
  containers:
  - name: model
    image: myregistry/sentiment:v1.0
    ports:
    - containerPort: 8000
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
    env:
    - name: MODEL_PATH
      value: "/models/sentiment.pt"
    volumeMounts:
    - name: model-storage
      mountPath: /models
  volumes:
  - name: model-storage
    persistentVolumeClaim:
      claimName: model-pvc
```

### Deployment

A Deployment is Kubernetes' way of managing the lifecycle of your Pods. Rather than creating Pods directly (which would be fragile—if a Pod dies, it's gone), you create a Deployment that declares "I want 3 copies of this Pod running at all times." The Deployment controller watches over your Pods like a shepherd watching sheep: if one wanders off (crashes), the shepherd fetches it back (restarts the Pod).

Deployments also handle updates gracefully. When you push a new version of your model, the Deployment can roll it out gradually—starting new Pods with the new version while keeping old ones running, then terminating old Pods only after new ones are healthy. If something goes wrong, you can roll back with a single command.

```yaml
# deployment.yaml - ML inference deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-classifier
  labels:
    app: sentiment-classifier
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sentiment-classifier
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: sentiment-classifier
    spec:
      containers:
      - name: model
        image: myregistry/sentiment:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
```

### Service

Here's a problem: Pods come and go. They get new IP addresses when they restart. If your application needs to talk to your ML inference service, how does it find it?

Enter the Service. A Service provides a stable network endpoint—a fixed IP address and DNS name—that routes traffic to healthy Pods matching a selector. Think of it like a phone number that forwards to whoever is on call. The doctors rotate, but the number stays the same.

Services also handle load balancing. When you have 10 replicas of your inference server, the Service distributes requests across all of them automatically. No need to implement client-side load balancing or maintain a list of server IPs.

```yaml
# service.yaml - Expose deployment
apiVersion: v1
kind: Service
metadata:
  name: sentiment-service
spec:
  selector:
    app: sentiment-classifier
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP  # Internal only

---
# For external access
apiVersion: v1
kind: Service
metadata:
  name: sentiment-service-external
spec:
  selector:
    app: sentiment-classifier
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer  # Gets external IP
```

### Service Types

```
SERVICE TYPES
=============

ClusterIP (default):
┌─────────────────────────────────┐
│         Cluster Only            │
│  Internal IP: 10.96.0.1:80     │
│  Only accessible within cluster │
└─────────────────────────────────┘

NodePort:
┌─────────────────────────────────┐
│  External: <NodeIP>:30000-32767 │
│  Opens port on every node       │
└─────────────────────────────────┘

LoadBalancer:
┌─────────────────────────────────┐
│  External: Cloud Load Balancer  │
│  Gets public IP from cloud      │
│  (AWS ELB, GCP LB, Azure LB)   │
└─────────────────────────────────┘

Ingress (not a Service, but related):
┌─────────────────────────────────┐
│  HTTP/HTTPS routing             │
│  Path-based: /api → service-a   │
│              /ml  → service-b   │
└─────────────────────────────────┘
```

---

##  GPU Scheduling for ML

### The GPU Challenge

GPUs are expensive resources. Kubernetes needs to:
1. Know which nodes have GPUs
2. Schedule GPU workloads appropriately
3. Prevent over-allocation
4. Support GPU sharing (optional)

### NVIDIA GPU Operator

```
NVIDIA GPU OPERATOR COMPONENTS
==============================

┌─────────────────────────────────────────────────────────────────┐
│                     GPU NODE                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  GPU Operator                            │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │   │
│  │  │ NVIDIA Driver │  │ Container     │  │ Device      │  │   │
│  │  │ (Auto-install)│  │ Toolkit       │  │ Plugin      │  │   │
│  │  └───────────────┘  └───────────────┘  └─────────────┘  │   │
│  │                                                          │   │
│  │  ┌───────────────┐  ┌───────────────┐                   │   │
│  │  │ DCGM Exporter │  │ GPU Feature   │                   │   │
│  │  │ (Monitoring)  │  │ Discovery     │                   │   │
│  │  └───────────────┘  └───────────────┘                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    GPU Hardware                          │   │
│  │  [GPU 0: A100 80GB] [GPU 1: A100 80GB]                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Did You Know?** NVIDIA's A100 GPU introduced Multi-Instance GPU (MIG) technology, which can partition a single GPU into up to 7 isolated instances. This means 7 different ML models can run on one A100 with guaranteed isolation—no noisy neighbor problems. MIG is particularly useful for inference workloads.

### Requesting GPUs

```yaml
# gpu-pod.yaml - Request GPU resources
apiVersion: v1
kind: Pod
metadata:
  name: gpu-training
spec:
  containers:
  - name: trainer
    image: pytorch/pytorch:2.0.1-cuda11.8-cudnn8-runtime
    resources:
      limits:
        nvidia.com/gpu: 1  # Request 1 GPU
    command: ["python", "train.py"]
  # Ensure scheduling on GPU node
  nodeSelector:
    accelerator: nvidia-tesla-a100
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```

### GPU Resource Types

```yaml
# Different GPU configurations
resources:
  limits:
    # Whole GPU
    nvidia.com/gpu: 1

    # MIG (Multi-Instance GPU) - A100 only
    nvidia.com/mig-1g.5gb: 1   # 1/7 of A100
    nvidia.com/mig-2g.10gb: 1  # 2/7 of A100
    nvidia.com/mig-3g.20gb: 1  # 3/7 of A100

    # Time-slicing (shared GPU)
    # Configured via GPU Operator config
```

### GPU Scheduling Strategy

```yaml
# Training job - needs dedicated GPU
apiVersion: batch/v1
kind: Job
metadata:
  name: model-training
spec:
  template:
    spec:
      containers:
      - name: trainer
        image: myregistry/trainer:v1
        resources:
          limits:
            nvidia.com/gpu: 4  # 4 GPUs for distributed training
            memory: "64Gi"
            cpu: "16"
      restartPolicy: Never
      # Use GPU node pool
      nodeSelector:
        node-pool: gpu-training
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

---

##  Resource Management

### Resource Requests vs Limits

Think of requests and limits like renting an apartment. The request is your base rent—the space you're guaranteed even when the building is full. The limit is the maximum space you can expand into if your neighbors aren't using theirs.

If you set a request of 1GB memory, Kubernetes guarantees you that 1GB. If you set a limit of 2GB, you can burst up to 2GB when available—but if you try to use more than your limit, you get evicted (OOMKilled).

```
REQUESTS VS LIMITS
==================

requests: What the container is GUARANTEED
limits:   Maximum the container CAN use

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  requests.memory: 1Gi    limits.memory: 2Gi                    │
│  ├──────────────────────┼─────────────────────┤                │
│  0                      1Gi                  2Gi               │
│  │◄─── Guaranteed ─────►│◄─── Burstable ────►│                │
│                                                                 │
│  If pod exceeds limit → OOMKilled (Out of Memory)              │
│  If pod exceeds request but under limit → OK (if available)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

CPU: Throttled (not killed) if exceeds limit
Memory: OOMKilled if exceeds limit
GPU: Cannot exceed limit (hard boundary)
```

### QoS Classes

```yaml
# Guaranteed QoS (highest priority)
# requests == limits for all containers
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "500m"

# Burstable QoS (medium priority)
# requests < limits
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

# BestEffort QoS (lowest priority, evicted first)
# No requests or limits specified
resources: {}
```

### Resource Quotas

```yaml
# Limit resources per namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ml-team-quota
  namespace: ml-team
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    limits.cpu: "200"
    limits.memory: "400Gi"
    requests.nvidia.com/gpu: "8"
    pods: "50"
    persistentvolumeclaims: "20"
```

---

##  Autoscaling for ML

Autoscaling is where Kubernetes really shines for ML workloads. Instead of guessing how many inference servers you'll need or paying for peak capacity 24/7, you let Kubernetes adjust resources based on actual demand.

Think of autoscaling like a concert venue that can magically add or remove seats. For a Tuesday night jazz performance, you might only need 100 seats. For a Saturday rock concert, you need 10,000. Instead of building a permanent 10,000-seat venue (expensive, mostly empty), you have a venue that expands and contracts based on ticket sales.

### Horizontal Pod Autoscaler (HPA)

The Horizontal Pod Autoscaler watches metrics (CPU, memory, or custom metrics like queue length) and adjusts the number of Pod replicas accordingly. When CPU usage exceeds your target, HPA spins up more Pods. When it drops, HPA terminates excess Pods. This is "horizontal" scaling—adding more instances of the same thing, like hiring more workers rather than buying a faster machine.

```yaml
# hpa.yaml - Scale based on CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sentiment-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sentiment-classifier
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### Custom Metrics for ML

```yaml
# Scale based on inference queue length
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inference-server
  minReplicas: 1
  maxReplicas: 50
  metrics:
  # Custom metric from Prometheus
  - type: Pods
    pods:
      metric:
        name: inference_queue_length
      target:
        type: AverageValue
        averageValue: "10"  # Scale when queue > 10 per pod
  # GPU utilization (requires DCGM)
  - type: External
    external:
      metric:
        name: dcgm_gpu_utilization
      target:
        type: AverageValue
        averageValue: "80"
```

### Vertical Pod Autoscaler (VPA)

Adjust resource requests/limits automatically.

```yaml
# vpa.yaml - Auto-tune resources
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ml-inference-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-inference
  updatePolicy:
    updateMode: "Auto"  # Or "Off" for recommendations only
  resourcePolicy:
    containerPolicies:
    - containerName: model
      minAllowed:
        cpu: "100m"
        memory: "256Mi"
      maxAllowed:
        cpu: "4"
        memory: "8Gi"
```

---

##  Persistent Storage for ML

### Storage Architecture

```
KUBERNETES STORAGE MODEL
========================

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Pod                                                            │
│  ┌─────────────────┐                                           │
│  │   Container     │                                           │
│  │  /models (mount)│ ──────┐                                   │
│  └─────────────────┘       │                                   │
│                            │                                   │
│  PersistentVolumeClaim     │                                   │
│  ┌─────────────────┐       │                                   │
│  │   model-pvc     │ ◄─────┘                                   │
│  │   10Gi, RWO     │                                           │
│  └────────┬────────┘                                           │
│           │ binds to                                           │
│           ▼                                                    │
│  PersistentVolume                                              │
│  ┌─────────────────┐                                           │
│  │   model-pv      │                                           │
│  │   NFS/EBS/GCS   │                                           │
│  └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### PersistentVolumeClaim for Models

```yaml
# pvc.yaml - Request storage for models
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage
spec:
  accessModes:
    - ReadWriteOnce  # RWO: Single node read-write
  resources:
    requests:
      storage: 50Gi
  storageClassName: fast-ssd  # SSD for fast model loading

---
# For shared model access (multiple pods)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-models
spec:
  accessModes:
    - ReadOnlyMany  # ROX: Multiple nodes read-only
  resources:
    requests:
      storage: 100Gi
  storageClassName: nfs  # NFS for shared access
```

### Access Modes

```
ACCESS MODES
============

ReadWriteOnce (RWO):
- Single node can mount as read-write
- Use for: Training checkpoints, single-replica inference

ReadOnlyMany (ROX):
- Multiple nodes can mount as read-only
- Use for: Shared models across inference replicas

ReadWriteMany (RWX):
- Multiple nodes can mount as read-write
- Use for: Distributed training, shared logs
- Requires: NFS, CephFS, GlusterFS

ReadWriteOncePod (RWOP):
- Single pod can mount as read-write
- K8s 1.22+ only
```

---

##  ML Deployment Patterns

### Pattern 1: Simple Inference Service

```yaml
# Complete inference deployment
apiVersion: v1
kind: Namespace
metadata:
  name: ml-inference

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: model-config
  namespace: ml-inference
data:
  MODEL_NAME: "sentiment-classifier"
  MODEL_VERSION: "v1.0"
  MAX_BATCH_SIZE: "32"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-api
  namespace: ml-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sentiment-api
  template:
    metadata:
      labels:
        app: sentiment-api
    spec:
      containers:
      - name: api
        image: myregistry/sentiment:v1.0
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: model-config
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60

---
apiVersion: v1
kind: Service
metadata:
  name: sentiment-api
  namespace: ml-inference
spec:
  selector:
    app: sentiment-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Pattern 2: GPU Training Job

```yaml
# Training job with GPU
apiVersion: batch/v1
kind: Job
metadata:
  name: bert-finetuning
  namespace: ml-training
spec:
  backoffLimit: 3
  template:
    spec:
      containers:
      - name: trainer
        image: myregistry/bert-trainer:v1
        command: ["python", "train.py"]
        args:
          - "--epochs=10"
          - "--batch-size=32"
          - "--learning-rate=2e-5"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "4"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: checkpoints
          mountPath: /checkpoints
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: training-data
      - name: checkpoints
        persistentVolumeClaim:
          claimName: checkpoints
      restartPolicy: OnFailure
      nodeSelector:
        accelerator: nvidia-tesla-v100
```

### Pattern 3: Model A/B Testing

```yaml
# Canary deployment with Istio
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: sentiment-routing
spec:
  hosts:
  - sentiment-api
  http:
  - match:
    - headers:
        x-model-version:
          exact: "v2"
    route:
    - destination:
        host: sentiment-api-v2
  - route:
    - destination:
        host: sentiment-api-v1
        weight: 90
    - destination:
        host: sentiment-api-v2
        weight: 10  # 10% traffic to new model
```

---

##  Networking Deep Dive for ML Services

### Understanding How Traffic Reaches Your Model

Think of Kubernetes networking like a corporate mail room. External traffic arrives at the building (LoadBalancer), gets sorted by department (Ingress/Service), and is delivered to specific desks (Pods). For ML services, understanding this flow is critical because latency matters—every millisecond of network delay reduces throughput.

**Did You Know?** At Google, the average inference latency budget is 50ms. Of that, 10-15ms is typically network overhead within Kubernetes. Teams that optimize their networking configurations see 40% latency improvements without touching their models.

### Service Types Explained

```
KUBERNETES SERVICE TYPES FOR ML
===============================

                    Internet
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              LoadBalancer Service                    │
│  (External IP: 34.89.xxx.xxx, Port 80)             │
│  Use for: Production inference endpoints            │
│  Cost: $18/month on GKE                             │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                NodePort Service                      │
│  (Any node IP, Port 30000-32767)                    │
│  Use for: Development/testing, on-prem clusters    │
│  Cost: Free                                          │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│               ClusterIP Service                      │
│  (Internal only: 10.0.xxx.xxx)                      │
│  Use for: Internal microservices, model chaining   │
│  Cost: Free                                          │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
                   ┌─────┐
                   │ Pod │
                   └─────┘
```

### DNS Resolution: How Pods Find Each Other

When your inference service needs to call a feature store:

```python
# Inside your pod, use DNS names
import requests

# Same namespace - just use service name
response = requests.get("http://feature-store:8080/features")

# Different namespace - use full DNS
response = requests.get("http://feature-store.ml-services.svc.cluster.local:8080/features")

# Format: <service>.<namespace>.svc.cluster.local
```

### Network Policies for ML Security

Imagine you're running a multi-tenant ML platform. You don't want the finance team's model accessing the healthcare team's data. Network policies are like firewalls at the pod level:

```yaml
# Only allow traffic from the API gateway to inference pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: inference-isolation
  namespace: ml-production
spec:
  podSelector:
    matchLabels:
      app: inference-service
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: api-gateway
    - podSelector:
        matchLabels:
          role: gateway
    ports:
    - port: 8000
      protocol: TCP
```

**Did You Know?** According to a 2023 Kubernetes security survey, only 23% of production clusters use network policies. Yet 67% of security incidents in Kubernetes involve unauthorized pod-to-pod communication. For ML workloads handling sensitive data (healthcare, finance), network policies aren't optional—they're compliance requirements.

### Latency Optimization Strategies

For ML inference, every millisecond counts. Here's how to optimize:

**1. Pod Anti-Affinity for Client Proximity**

```yaml
# Spread inference pods across zones for client proximity
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: inference
        topologyKey: topology.kubernetes.io/zone
```

**2. Service Topology for Local Traffic**

```yaml
# Route to pods in same zone first (reduces cross-zone latency)
apiVersion: v1
kind: Service
metadata:
  name: inference-local
spec:
  selector:
    app: inference
  topologyKeys:
  - "topology.kubernetes.io/zone"
  - "*"  # Fall back to any pod if none in zone
```

**3. Connection Pooling Configuration**

```python
# In your inference service, configure HTTP keep-alive
import httpx

# Create a client with connection pooling
client = httpx.Client(
    limits=httpx.Limits(
        max_keepalive_connections=100,
        max_connections=200,
        keepalive_expiry=30.0
    ),
    timeout=10.0
)

# Reuse connections across requests
response = client.post("http://feature-store:8080/features", json=data)
```

---

##  Essential kubectl Commands

```bash
# CLUSTER INFO
kubectl cluster-info
kubectl get nodes
kubectl get nodes -o wide  # With IPs

# DEPLOYMENTS
kubectl get deployments
kubectl describe deployment <name>
kubectl scale deployment <name> --replicas=5
kubectl rollout status deployment <name>
kubectl rollout history deployment <name>
kubectl rollout undo deployment <name>

# PODS
kubectl get pods
kubectl get pods -o wide  # With node info
kubectl describe pod <name>
kubectl logs <pod-name>
kubectl logs <pod-name> -f  # Follow
kubectl logs <pod-name> --previous  # Previous container
kubectl exec -it <pod-name> -- bash  # Shell into pod

# SERVICES
kubectl get services
kubectl describe service <name>
kubectl port-forward service/<name> 8080:80  # Local access

# GPU NODES
kubectl get nodes -l accelerator=nvidia
kubectl describe node <gpu-node> | grep -A5 "Allocated resources"

# RESOURCES
kubectl top nodes
kubectl top pods
kubectl get resourcequota

# DEBUGGING
kubectl get events --sort-by='.lastTimestamp'
kubectl describe pod <pod-name>  # Check Events section
kubectl logs <pod-name> --all-containers
```

---

##  Production War Stories: Kubernetes Lessons Learned

### The Pod That Wouldn't Die

**Austin. April 2023. Fintech startup running fraud detection.**

The ML team deployed their fraud detection model to Kubernetes. Everything looked good—pods running, service responding. Then they noticed something strange: the model was using a cached version of their feature transformer, one that was 3 versions old.

They pushed a new image. Rolled out the deployment. Checked the logs. Still using the old transformer.

**The investigation took 6 hours.** The problem? They'd configured a PersistentVolumeClaim with ReadWriteOnce (RWO) mode, and the old pod had locked the volume. New pods were starting, but they were mounting a cached copy because the original volume was busy.

Worse, the old pod was stuck in "Terminating" state because its graceful shutdown was waiting for an HTTP connection that would never close (a bug in the health check handler).

```yaml
# The fix: Add proper termination handling
spec:
  terminationGracePeriodSeconds: 30
  containers:
  - name: model
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 5"]  # Allow connections to drain
```

**Financial impact**: 6 hours of debugging at senior engineer rates ($1,500), plus the soft cost of delayed fraud detection (unmeasured but significant).

**Lesson**: Always test your rolling update behavior. Simulate the update, watch pods terminate and recreate, verify the new version is actually running. Kubernetes "working" doesn't mean your application is working.

> **Did You Know?** A 2023 Kubernetes reliability survey found that 34% of production incidents were caused by pod lifecycle issues—containers not shutting down cleanly, health checks misconfigured, or volume contention. Proper terminationGracePeriodSeconds and preStop hooks prevent most of these.

---

### The GPU Scheduling Disaster

**San Francisco. January 2023. AI startup building image generation.**

The inference team requested 1 GPU per pod: `nvidia.com/gpu: 1`. Simple, right?

During a traffic spike, the Horizontal Pod Autoscaler scaled from 5 to 15 pods. But only 8 GPUs were available in the cluster. The remaining 7 pods sat in "Pending" state indefinitely.

Meanwhile, the 8 running pods were overwhelmed—queue times exceeded 60 seconds, users abandoned the app, and the support inbox exploded.

**The root cause**: HPA didn't know about GPU constraints. It saw high CPU usage and said "scale up!" It had no way to know that scaling was pointless without more GPUs.

**The fix involved three changes**:

1. **Cluster Autoscaler**: Automatically add GPU nodes when pods are pending
   ```yaml
   # Cluster Autoscaler config
   scaleDownEnabled: true
   scaleDownDelayAfterAdd: 10m
   scaleDownUnneededTime: 10m
   expanderName: priority  # Prefer GPU nodes for GPU workloads
   ```

2. **Resource-aware HPA**: Custom metrics that account for GPU availability
   ```yaml
   - type: External
     external:
       metric:
         name: gpu_nodes_available
       target:
         type: Value
         value: "1"  # Only scale if GPUs are available
   ```

3. **PodDisruptionBudget**: Ensure minimum capacity during scaling
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   spec:
     minAvailable: 5  # Always keep at least 5 pods
   ```

**Financial impact**: 2 hours of degraded service during peak traffic = estimated $45,000 in lost revenue.

**Lesson**: HPA is blind to infrastructure constraints. For GPU workloads, you need Cluster Autoscaler or custom metrics that understand resource availability, not just demand.

---

### The Memory Leak That Killed Christmas

**New York. December 2023. E-commerce recommendation engine.**

The team had carefully sized their pods: 2GB memory request, 4GB limit. In testing, memory usage stabilized around 2.5GB. Perfect—plenty of headroom.

On December 23rd, two days before Christmas, pods started getting OOMKilled. One at a time at first, then in waves. The autoscaler kept replacing them, but new pods would die within an hour.

**The forensic analysis**: The model loaded fine and ran fine for most requests. But certain edge cases—particularly gift recommendation queries with very long shopping histories—caused memory to spike to 5GB temporarily. When multiple users hit these edge cases simultaneously, pods exceeded their limits and died.

**The solution was multi-layered**:

1. **Increased limits with monitoring**:
   ```yaml
   resources:
     requests:
       memory: "2Gi"
     limits:
       memory: "8Gi"  # Increased headroom
   ```

2. **Added memory-based HPA**:
   ```yaml
   - type: Resource
     resource:
       name: memory
       target:
         type: Utilization
         averageUtilization: 60  # Scale before hitting limits
   ```

3. **Application-level fix**: Added request batching and memory guards
   ```python
   @memory_guard(max_mb=4000)
   def generate_recommendations(user_history):
       if len(user_history) > 1000:
           user_history = user_history[-1000:]  # Truncate
       # ... process
   ```

**Financial impact**: 4 hours of intermittent outages during peak shopping season = $2.1M in estimated lost revenue.

**Lesson**: Memory limits protect the cluster, but they can kill your pods. Always set limits higher than your worst-case usage, monitor memory patterns over time, and add application-level guards for edge cases.

---

##  Common Mistakes and How to Avoid Them

### Mistake 1: No Resource Requests or Limits

**Wrong**:
```yaml
containers:
- name: model
  image: mymodel:v1
  # No resources specified!
```

**Problem**: Kubernetes treats this as "BestEffort" QoS class—your pod is the first to be evicted under memory pressure. Also, the scheduler can't make intelligent placement decisions.

**Right**:
```yaml
containers:
- name: model
  image: mymodel:v1
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
```

Always specify resources. For ML workloads, start with 2x the average usage as your limit.

---

### Mistake 2: Using Latest Tag

**Wrong**:
```yaml
image: mymodel:latest
```

**Problem**: `latest` is mutable. If you rollback, you might not actually rollback—you'll get whatever `latest` points to now. Also, Kubernetes caches images, so different nodes might have different versions of `latest`.

**Right**:
```yaml
image: mymodel:v1.2.3-abc123
imagePullPolicy: IfNotPresent
```

Always use immutable tags. Include git SHA for traceability.

---

### Mistake 3: Missing Health Checks

**Wrong**:
```yaml
containers:
- name: model
  image: mymodel:v1
  # No health checks!
```

**Problem**: Kubernetes thinks your pod is healthy even when it's stuck, crashed, or serving errors. Traffic keeps flowing to dead pods.

**Right**:
```yaml
containers:
- name: model
  readinessProbe:
    httpGet:
      path: /ready
      port: 8000
    initialDelaySeconds: 30
    periodSeconds: 10
  livenessProbe:
    httpGet:
      path: /live
      port: 8000
    initialDelaySeconds: 60
    periodSeconds: 30
    failureThreshold: 3
```

- **readinessProbe**: Is the pod ready to receive traffic?
- **livenessProbe**: Is the pod alive and should it be restarted if not?

For ML: readiness should check that the model is loaded. Liveness should check that the process is responsive.

---

### Mistake 4: Ignoring Pod Disruption Budgets

**Wrong**:
```yaml
# No PDB defined
# During cluster upgrade, ALL your pods get evicted simultaneously
```

**Problem**: Node maintenance, cluster upgrades, and spot instance preemption can kill all your pods at once if you don't protect them.

**Right**:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ml-inference-pdb
spec:
  minAvailable: 2  # Always keep at least 2 pods
  selector:
    matchLabels:
      app: ml-inference
```

For production ML, always have a PDB. Set minAvailable to at least 50% of your normal replica count.

---

### Mistake 5: Wrong Service Type

**Wrong**:
```yaml
spec:
  type: LoadBalancer  # Creates external LB even for internal services
```

**Problem**: LoadBalancer creates cloud load balancers ($$$), exposes your service to the internet, and adds latency for internal traffic.

**Right**:
```yaml
# For internal services
spec:
  type: ClusterIP

# For external APIs
spec:
  type: LoadBalancer
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"  # Internal LB
```

Use ClusterIP for internal services. Use LoadBalancer only for external APIs, and consider internal load balancers where possible.

---

##  Economics of Kubernetes for ML

### Cost Comparison: Manual Scaling vs Kubernetes

| Scenario | Manual Scaling | Kubernetes + HPA |
|----------|----------------|------------------|
| **Peak capacity provisioning** | | |
| Servers for peak load (100 req/s) | 20 servers | 5-20 servers (auto-scale) |
| Monthly infrastructure cost | $40,000 | $15,000 avg |
| Utilization rate | 25% avg | 70% avg |
| **Operations** | | |
| On-call incidents (monthly) | 8 | 2 |
| Engineer time responding | 16 hours | 4 hours |
| Deployment time | 2 hours | 5 minutes |
| **Annual Total** | | |
| Infrastructure | $480,000 | $180,000 |
| Operations (at $150/hr) | $28,800 | $7,200 |
| **Total** | **$508,800** | **$187,200** |
| **Savings** | | **$321,600 (63%)** |

### GPU Cost Optimization with Kubernetes

| Strategy | Without K8s | With K8s | Savings |
|----------|-------------|----------|---------|
| **GPU Utilization** | | | |
| Single-tenant VMs | 30% avg utilization | N/A | Baseline |
| Kubernetes scheduling | N/A | 60% avg utilization | 50% fewer GPUs needed |
| **Spot/Preemptible** | | | |
| On-demand A100s | $4/hour each | N/A | Baseline |
| Spot + K8s preemption handling | N/A | $1.20/hour each | 70% savings |
| **Right-sizing** | | | |
| Fixed instance types | Oversized 40% of time | VPA recommendations | 25% cost reduction |

### Hidden Value: Developer Productivity

```
KUBERNETES ROI FOR ML TEAMS
───────────────────────────

┌────────────────────────────────────────────────────────────┐
│  Activity                    │  Before K8s  │  After K8s   │
├────────────────────────────────────────────────────────────┤
│  Deploy new model version    │  2 hours     │  5 minutes   │
│  Scale for traffic spike     │  30 minutes  │  Automatic   │
│  Investigate prod issue      │  2 hours     │  30 minutes  │
│  Set up new ML service       │  1 day       │  2 hours     │
│  Run A/B test                │  1 day       │  15 minutes  │
├────────────────────────────────────────────────────────────┤
│  Weekly ML engineering time  │  20 hours    │  5 hours     │
│  Annual savings (team of 5)  │              │  3,900 hours │
│  Value at $150/hour          │              │  $585,000    │
└────────────────────────────────────────────────────────────┘
```

> **Did You Know?** According to the 2023 CNCF Survey, organizations using Kubernetes report 50% faster deployment frequencies and 23% lower infrastructure costs compared to traditional deployments. For ML teams specifically, the benefits are even larger due to GPU scheduling and autoscaling capabilities.

---

## ️ Cloud Provider Comparison for ML Workloads

### Choosing the Right Managed Kubernetes

When deploying ML workloads, your choice of Kubernetes provider significantly impacts costs, GPU availability, and operational complexity. Each major cloud provider has distinct strengths for ML use cases.

### Google Kubernetes Engine (GKE)

GKE is often considered the gold standard for Kubernetes—Google invented Kubernetes, after all. For ML teams, the key advantages are:

**Strengths:**
- **Autopilot mode**: Google manages node provisioning entirely. You just deploy pods, and GKE creates the right nodes automatically. For ML teams without dedicated DevOps, this reduces operational burden by 80%.
- **TPU integration**: If you're doing heavy training, GKE has native TPU support. TPU v4 pods can train GPT-3-scale models 2x faster than comparable A100 setups.
- **Vertex AI integration**: Tight integration with Google's ML platform for model serving, training pipelines, and feature stores.

**Pricing for ML (2024):**
- A100 (40GB): $3.67/hour (on-demand), $1.10/hour (spot)
- T4: $0.35/hour (on-demand), $0.11/hour (spot)
- GKE Autopilot surcharge: ~20% over standard

**Best for:** Teams wanting minimal operations overhead, TensorFlow-heavy workloads, organizations already on Google Cloud.

### Amazon EKS

EKS has the largest GPU fleet availability, which matters when you need to scale quickly.

**Strengths:**
- **GPU variety**: Access to A100s, H100s, Trainium chips, and Inferentia accelerators
- **SageMaker integration**: Seamless connection to AWS's ML platform
- **Karpenter**: AWS's advanced node provisioning tool that scales GPU nodes faster than standard Cluster Autoscaler

**Pricing for ML (2024):**
- A100 (40GB): $4.10/hour (on-demand), $1.23/hour (spot)
- Inferentia2: $1.10/hour (optimized for inference, 50% cheaper than GPUs for supported models)
- EKS control plane: $72/month flat fee

**Best for:** Large-scale training jobs requiring many GPUs, organizations already on AWS, teams wanting inference cost optimization with Inferentia.

**Did You Know?** Amazon's internal ML infrastructure runs on EKS. The Alexa team processes over 100 million inference requests per day using Kubernetes orchestration, with automatic scaling handling 10x traffic spikes during peak hours like Christmas morning.

### Azure Kubernetes Service (AKS)

AKS has strong enterprise features and the best Windows container support (if that matters for your stack).

**Strengths:**
- **Confidential computing**: For healthcare and finance ML workloads requiring data privacy during inference
- **Azure ML integration**: Tight coupling with Azure's ML platform
- **No control plane fee**: Unlike EKS, AKS doesn't charge for the control plane

**Pricing for ML (2024):**
- A100 (40GB): $3.95/hour (on-demand), $1.19/hour (spot)
- NC-series (V100): $3.06/hour (on-demand)
- Control plane: Free

**Best for:** Enterprise ML with compliance requirements, organizations on Microsoft stack, Windows-based ML pipelines.

### Cost Comparison: Running 100 A100-Hours Monthly

| Provider | On-Demand | Spot (70% workload) | Annual Cost |
|----------|-----------|---------------------|-------------|
| GKE | $367 | $161 | $4,092 |
| EKS | $410 | $179 | $4,572 |
| AKS | $395 | $173 | $4,404 |

### Multi-Cloud Considerations

Some organizations run Kubernetes across multiple clouds for:
- **GPU availability**: When one cloud is out of A100s, fail over to another
- **Vendor lock-in mitigation**: Avoid dependence on single provider
- **Regional compliance**: Data sovereignty requirements

Tools like Cluster API and Rancher help manage multi-cloud Kubernetes deployments, but the operational complexity increases significantly. For most ML teams, we recommend starting single-cloud and only going multi-cloud if you have a specific requirement.

---

##  Interview Preparation: Kubernetes for ML

### Q1: "How would you deploy an ML model to Kubernetes?"

**Strong Answer**:
"I'd approach this in three layers: containerization, Kubernetes resources, and operational concerns.

First, I'd containerize the model with a proper Dockerfile—multi-stage build, non-root user, health check endpoints. The image would include the model loading code and an HTTP server like FastAPI or Flask.

For Kubernetes resources, I'd create a Deployment with 3+ replicas for high availability, specifying resource requests and limits based on profiled usage. I'd add readinessProbe that checks if the model is loaded and livenessProbe that verifies the process is responsive. A Service exposes the deployment, either ClusterIP for internal access or LoadBalancer for external APIs.

For operations, I'd configure HPA to scale based on CPU usage, typically targeting 70%. For GPU workloads, I'd use custom metrics like inference queue length. I'd add a PodDisruptionBudget to ensure at least 2 replicas during upgrades.

For model updates, I'd use rolling deployments with maxSurge=1 and maxUnavailable=0 to ensure zero downtime. For major model changes, I might use a canary deployment with traffic splitting to validate the new model before full rollout."

### Q2: "How does GPU scheduling work in Kubernetes?"

**Strong Answer**:
"GPU scheduling in Kubernetes requires the NVIDIA GPU Operator, which consists of several components working together.

The NVIDIA device plugin runs as a DaemonSet on GPU nodes and advertises GPU resources to the Kubernetes scheduler. When you specify `nvidia.com/gpu: 1` in your pod spec, the scheduler finds a node with available GPU capacity and assigns the pod there.

The key constraint is that GPUs are allocated as whole units by default—you can't request 0.5 GPUs. However, there are ways to share GPUs:

Multi-Instance GPU (MIG) on A100s lets you partition a physical GPU into up to 7 isolated instances, each with guaranteed memory and compute. You'd request specific MIG profiles like `nvidia.com/mig-1g.5gb`.

Time-slicing allows multiple pods to share a GPU by switching between them, but without memory isolation—useful for inference workloads with bursty usage.

For scheduling strategy, I typically use nodeSelectors or tolerations to ensure GPU workloads land on GPU nodes and non-GPU workloads don't waste expensive GPU capacity. I also configure the Cluster Autoscaler to spin up GPU nodes on demand when pods are pending for GPU resources."

### Q3: "Explain the difference between resource requests and limits."

**Strong Answer**:
"Requests and limits serve different purposes in Kubernetes resource management.

Requests are what your container is guaranteed to receive. The scheduler uses requests to decide where to place pods—it won't schedule a pod on a node unless the node has enough unrequested resources. Think of it as reserving capacity.

Limits are the maximum your container can use. If a container tries to exceed its memory limit, it gets OOMKilled. If it exceeds its CPU limit, it gets throttled.

For ML workloads, I set requests based on typical steady-state usage and limits based on peak usage plus headroom. For example, if my inference server typically uses 1.5GB memory but spikes to 3GB during batch processing, I'd set requests to 2GB and limits to 4GB.

The ratio between requests and limits determines your QoS class:
- Guaranteed (requests == limits): Highest priority, never evicted unless node is critical
- Burstable (requests < limits): Can use extra resources when available, evicted under pressure
- BestEffort (no requests or limits): Lowest priority, first to be evicted

For production ML, I always use Guaranteed or Burstable. BestEffort is too risky—your inference pods could be evicted during a traffic spike, exactly when you need them most."

### Q4: "How would you handle model updates with zero downtime?"

**Strong Answer**:
"I'd use Kubernetes' built-in rolling update strategy, but with ML-specific considerations.

In the Deployment spec, I'd configure:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

maxUnavailable: 0 ensures we never reduce capacity below the current replica count. maxSurge: 1 means we add one new pod at a time with the new model version.

The critical piece for ML is the readinessProbe. Standard health checks just verify the process is running, but ML models need time to load—sometimes minutes for large models. My readinessProbe checks an endpoint that returns 200 only after the model is loaded and warmed up:

```python
@app.get("/ready")
def ready():
    if not model_loaded:
        raise HTTPException(503)
    # Optional: run a warmup inference
    _ = model.predict(warmup_input)
    return {"ready": True}
```

For major model changes, I'd use a canary deployment. Deploy the new model version as a separate Deployment, route 5% of traffic to it using Istio or a similar service mesh, monitor error rates and latency, then gradually increase traffic if metrics look good.

If something goes wrong, Kubernetes makes rollback trivial: `kubectl rollout undo deployment/my-model`. It reverts to the previous ReplicaSet, which still exists for exactly this purpose."

### System Design: ML Inference Platform on Kubernetes

**Prompt**: "Design a Kubernetes-based ML inference platform that serves multiple models to 10,000 requests per second with GPU acceleration."

**Strong Answer**:

"I'd design this with five main components:

**1. Cluster Architecture**:
```
Kubernetes Cluster (3 AZs for HA)
├── Control Plane (managed - EKS/GKE/AKS)
├── CPU Node Pool (c5.2xlarge × 10)
│   └── API gateways, load balancers, monitoring
├── GPU Node Pool (p4d.24xlarge × 8)
│   └── A100 GPUs for inference
│   └── Spot instances with preemption handling
└── Cluster Autoscaler
    └── Scale GPU nodes 4-16 based on pending pods
```

**2. Model Serving Layer**:
```yaml
# Per-model deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-model
spec:
  replicas: 4
  selector:
    matchLabels:
      app: sentiment-model
  template:
    spec:
      containers:
      - name: model
        image: registry/sentiment:v2.1
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 60
```

**3. Traffic Management**:
```
Ingress (NGINX or Istio)
├── /models/sentiment → sentiment-service
├── /models/classification → classification-service
└── /models/embedding → embedding-service

HPA per model:
- Scale 2-20 replicas
- Target: 70% GPU utilization OR queue length < 10
- Cooldown: 5 minutes for scale-down
```

**4. Capacity Planning for 10K RPS**:
```
Per GPU: ~1,500 req/s (depends on model)
10K req/s ÷ 1,500 = ~7 GPUs active
With 70% utilization target: 10 GPUs
With headroom for spikes: 12-16 GPUs available

Node pool: 8 × p4d.24xlarge = 64 A100s total
Active pods: 12-16 (normal), up to 40 (peak)
```

**5. Observability**:
```
Prometheus + Grafana
├── GPU utilization (DCGM exporter)
├── Request latency (p50, p95, p99)
├── Queue depth
└── Error rates

Alerts:
- GPU utilization > 85% for 5 min
- Latency p99 > 500ms
- Error rate > 1%
- Pods in Pending > 2 min
```

**Cost Estimate**:
- GPU nodes (8 × p4d.24xlarge spot): ~$25,000/month
- CPU nodes (10 × c5.2xlarge): ~$2,500/month
- Load balancers, storage: ~$1,000/month
- **Total: ~$28,500/month for 10K RPS**

This scales horizontally—add more GPU nodes and pods for higher throughput."

---

##  Hands-On Exercises

### Exercise 1: Deploy Inference Service

Create a Kubernetes deployment for an ML inference API:
- 3 replicas
- Health checks
- Resource limits
- LoadBalancer service

**Complete Implementation:**

```yaml
# inference-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-inference
  labels:
    app: ml-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ml-inference
  template:
    metadata:
      labels:
        app: ml-inference
    spec:
      containers:
      - name: inference
        image: your-registry/ml-model:v1.0.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: MODEL_PATH
          value: "/models/latest"
        - name: WORKERS
          value: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: ml-inference-lb
spec:
  type: LoadBalancer
  selector:
    app: ml-inference
  ports:
  - port: 80
    targetPort: 8000
```

**Deploy and verify:**

```bash
# Apply the deployment
kubectl apply -f inference-deployment.yaml

# Watch pods come up
kubectl get pods -w -l app=ml-inference

# Check service external IP
kubectl get svc ml-inference-lb

# Test the endpoint
curl http://<EXTERNAL-IP>/predict -d '{"input": [1,2,3]}'
```

### Exercise 2: GPU Training Job

Create a Job for model training:
- Request 1 GPU
- Mount data volume
- Save checkpoints

**Complete Implementation:**

```yaml
# training-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: model-training-job
spec:
  backoffLimit: 3  # Retry up to 3 times on failure
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: trainer
        image: your-registry/trainer:v1.0.0
        command: ["python", "train.py"]
        args:
        - "--epochs=100"
        - "--batch-size=32"
        - "--checkpoint-dir=/checkpoints"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "4000m"
        volumeMounts:
        - name: training-data
          mountPath: /data
        - name: checkpoints
          mountPath: /checkpoints
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        - name: WANDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: wandb-secret
              key: api-key
      volumes:
      - name: training-data
        persistentVolumeClaim:
          claimName: training-data-pvc
      - name: checkpoints
        persistentVolumeClaim:
          claimName: checkpoint-pvc
      nodeSelector:
        gpu: "true"
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

**Monitor training:**

```bash
# Watch job progress
kubectl get jobs -w

# View training logs
kubectl logs -f job/model-training-job

# Check GPU utilization (if nvidia-smi available)
kubectl exec -it $(kubectl get pod -l job-name=model-training-job -o name) -- nvidia-smi
```

### Exercise 3: Autoscaling

Configure HPA for inference service:
- Scale 2-10 replicas
- Target 70% CPU
- Custom queue metric

**Complete Implementation:**

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60  # Scale down at most 50% per minute
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15  # Can double every 15 seconds
      - type: Pods
        value: 4
        periodSeconds: 15  # Or add 4 pods every 15 seconds
```

**Test autoscaling:**

```bash
# Apply HPA
kubectl apply -f hpa.yaml

# Watch HPA decisions
kubectl get hpa ml-inference-hpa -w

# Generate load for testing
kubectl run -it --rm load-test --image=busybox -- \
  /bin/sh -c "while true; do wget -q -O- http://ml-inference-lb/predict; done"

# Watch pods scale
kubectl get pods -l app=ml-inference -w
```

---

##  Debugging and Troubleshooting

### Common Debugging Scenarios

**Did You Know?** The average Kubernetes debugging session takes 47 minutes according to a 2023 CNCF survey. Teams that implement proper logging and observability reduce this to under 10 minutes. The most common issues? OOMKilled pods (32%), image pull errors (28%), and misconfigured probes (19%).

### Scenario 1: Pod Stuck in Pending

When your ML pod won't start, it's usually a resource issue:

```bash
# Check pod status
kubectl describe pod <pod-name>

# Look for these messages:
# "0/3 nodes are available: 3 Insufficient nvidia.com/gpu"
# "0/3 nodes are available: 3 Insufficient memory"

# Solutions:
# 1. Check cluster capacity
kubectl describe nodes | grep -A5 "Allocated resources"

# 2. Check GPU availability
kubectl describe nodes | grep -A3 "nvidia.com/gpu"

# 3. Reduce resource requests or add nodes
```

### Scenario 2: OOMKilled - The Memory Assassin

ML workloads are notorious for OOMKills:

```bash
# Check if pod was killed for memory
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].lastState}'

# If OOMKilled, increase limits:
resources:
  limits:
    memory: "8Gi"  # Was 4Gi, model needs more

# Pro tip: Set memory request = limit for ML workloads
# This prevents overcommitment and makes OOM behavior predictable
```

### Scenario 3: Slow Model Loading

Large models (BERT, GPT-2, etc.) take time to load:

```yaml
# Increase initialDelaySeconds for probes
livenessProbe:
  initialDelaySeconds: 120  # Give model 2 min to load
  periodSeconds: 30

readinessProbe:
  initialDelaySeconds: 60
  periodSeconds: 10
  failureThreshold: 6  # Try 6 times before giving up
```

### The Kubernetes Debugging Cheat Sheet

```bash
# Pod won't start?
kubectl describe pod <name>
kubectl get events --sort-by='.lastTimestamp'

# Pod keeps restarting?
kubectl logs <pod> --previous  # Logs from crashed container

# Service not reachable?
kubectl get endpoints <service-name>  # Should show pod IPs

# Everything looks fine but still broken?
kubectl exec -it <pod> -- /bin/sh  # Get a shell and investigate
```

**Did You Know?** Kelsey Hightower, one of the original Kubernetes developers at Google, recommends the "three kubectl commands" approach: `kubectl get`, `kubectl describe`, and `kubectl logs`. He says: "If you can't debug with these three commands, you're probably over-engineering your manifests."

---

##  Further Reading

### Documentation
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [Kubeflow](https://www.kubeflow.org/)

### Tools
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [k9s](https://k9scli.io/) - Terminal UI for K8s
- [Lens](https://k8slens.dev/) - K8s IDE

### ML on Kubernetes
- [Seldon Core](https://www.seldon.io/) - ML deployment
- [KServe](https://kserve.github.io/) - Serverless inference
- [Ray on Kubernetes](https://docs.ray.io/en/latest/cluster/kubernetes/)

---

##  Knowledge Check

Test your understanding with these review questions:

### 1. What is a Pod and how does it differ from a container?

**Answer**: A Pod is the smallest deployable unit in Kubernetes—it's a wrapper around one or more containers that share storage, network, and a specification for how to run. Think of a Pod like an apartment: containers are the rooms that share the same address (IP), utilities (volumes), and lease agreement (lifecycle). Unlike a standalone Docker container, pods provide coordinated multi-container patterns (sidecars, init containers) and integrate with Kubernetes scheduling, networking, and storage systems.

### 2. How do you request GPU resources in Kubernetes?

**Answer**: You request GPUs using the `nvidia.com/gpu` resource in your pod spec. This requires the NVIDIA GPU Operator installed on your cluster. The request looks like:
```yaml
resources:
  limits:
    nvidia.com/gpu: 1  # Request exactly 1 GPU
```
GPUs are allocated as whole units by default. For GPU sharing, you can use Multi-Instance GPU (MIG) on A100s or time-slicing with the `nvidia.com/gpu.shared` resource.

### 3. What's the difference between requests and limits?

**Answer**: Requests are the guaranteed minimum resources your container receives—the scheduler uses these to place pods on nodes with sufficient capacity. Limits are the maximum resources your container can use. Exceeding memory limits causes OOMKill; exceeding CPU limits causes throttling. For ML workloads, set requests based on steady-state usage and limits with ~50% headroom for peaks. Setting requests equal to limits gives you the "Guaranteed" QoS class—highest priority and never evicted except during node failure.

### 4. How does HPA scale ML inference services?

**Answer**: HorizontalPodAutoscaler (HPA) watches metrics and adjusts the replica count of your Deployment. By default, it scales based on CPU utilization. For ML inference, you typically configure:
- CPU target: 70% average utilization
- Custom metrics: inference queue length, request latency p99
- Scale-up behavior: fast (stabilizationWindowSeconds: 0)
- Scale-down behavior: slow (stabilizationWindowSeconds: 300) to avoid thrashing

HPA checks metrics every 15 seconds and makes scaling decisions based on the ratio of current to desired metric values.

### 5. What access mode would you use for shared model storage?

**Answer**: Use `ReadWriteMany` (RWX) access mode when multiple pods need to read from the same model storage simultaneously—which is common for inference services running multiple replicas. If only one pod needs access, `ReadWriteOnce` (RWO) is simpler and more widely supported. For model versioning scenarios where pods should read but never write, `ReadOnlyMany` (ROX) provides an extra safety layer. Not all storage backends support RWX—NFS, Azure Files, and some cloud file systems do, but many block storage options only support RWO.

---

## ⏭️ Next Steps

You now understand Kubernetes for ML! Key takeaways:
- Pods are the smallest unit, Deployments manage replicas
- GPU scheduling requires NVIDIA GPU Operator
- Resource requests guarantee capacity, limits cap usage
- HPA scales based on CPU, memory, or custom metrics
- PVCs provide persistent storage for models

**Up Next**: Module 47 - FastAPI for ML Serving

---

_Module 46 Complete! You now understand Kubernetes for ML!_
_"Kubernetes: Because your model deserves to scale."_
