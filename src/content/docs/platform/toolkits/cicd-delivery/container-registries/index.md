---
title: "Container Registries Toolkit"
sidebar:
  order: 1
  label: "Container Registries"
---
> **Toolkit Track** | 3 Modules | ~2.5 hours total

## Overview

The Container Registries Toolkit covers self-hosted container image storage beyond DockerHub. When rate limits, security requirements, or air-gapped environments make public registries impractical, you need your own. Harbor is the enterprise standard, Zot is the lightweight alternative, and Dragonfly solves the "deploy to 1000 nodes" problem.

This toolkit applies concepts from [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) and [Security Tools Toolkit](../../security-quality/security-tools/).

## Prerequisites

Before starting this toolkit:
- Docker fundamentals (building, pushing images)
- Basic Kubernetes experience
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) - Supply chain security
- Understanding of OCI image format

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 13.1 | [Harbor](module-13.1-harbor/) | `[COMPLEX]` | 50-60 min |
| 13.2 | [Zot](module-13.2-zot/) | `[MEDIUM]` | 40-45 min |
| 13.3 | [Dragonfly](module-13.3-dragonfly/) | `[COMPLEX]` | 45-50 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy Harbor** — Enterprise registry with scanning, RBAC, replication
2. **Run Zot** — Lightweight OCI-native registry
3. **Scale with Dragonfly** — P2P image distribution for massive clusters
4. **Choose the right solution** — Understand trade-offs for your environment

## Tool Selection Guide

```
WHICH CONTAINER REGISTRY?
─────────────────────────────────────────────────────────────────

"I need enterprise features: RBAC, scanning, replication"
└──▶ Harbor
     • CNCF Graduated project
     • Built-in Trivy scanning
     • Multi-tenancy with projects
     • Image signing, quotas, retention

"I want minimal footprint, just OCI compliance"
└──▶ Zot
     • Single binary, ~20MB
     • Full OCI spec compliance
     • No database required
     • Efficient for edge/IoT

"I need to pull images to 1000+ nodes fast"
└──▶ Dragonfly
     • P2P distribution
     • Prevents registry meltdown
     • Works with any registry
     • CNCF Incubating

"I'm using cloud provider"
└──▶ Managed registries
     • ECR (AWS)
     • GCR/Artifact Registry (GCP)
     • ACR (Azure)
     • Less control, less ops

COMPARISON MATRIX:
─────────────────────────────────────────────────────────────────
                    Harbor      Zot         Dragonfly    ECR/GCR
─────────────────────────────────────────────────────────────────
Self-hosted         ✓           ✓           ✓            ✗
Vulnerability scan  ✓ (Trivy)   Via proxy   ✗            ✓
RBAC               ✓           Basic       N/A          IAM
Replication        ✓           ✓           ✓✓           Limited
Air-gapped         ✓           ✓           ✓            ✗
Memory usage       2GB+        50MB        200MB+       N/A
OCI Artifacts      ✓           ✓           ✓            ✓
Image signing      ✓ (Notary)  ✓ (cosign)  ✓            ✓
Helm charts        ✓           ✓           ✓            ✓
P2P distribution   ✗           ✗           ✓✓           ✗
```

## The Container Registry Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTAINER REGISTRY LANDSCAPE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PUBLIC REGISTRIES                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  DockerHub      │  GHCR           │  Quay.io             │  │
│  │  (rate limits!) │  (GitHub native) │  (Red Hat)          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SELF-HOSTED                                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Harbor              Zot               Distribution       │  │
│  │  ┌─────────┐        ┌─────────┐       ┌─────────┐        │  │
│  │  │Enterprise│        │Minimal  │       │ Docker  │        │  │
│  │  │+ scanning│        │OCI-only │       │Registry │        │  │
│  │  │+ RBAC   │        │         │       │  (old)  │        │  │
│  │  └─────────┘        └─────────┘       └─────────┘        │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DISTRIBUTION LAYER                                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Dragonfly P2P                    Kraken (Uber)           │  │
│  │  ┌─────────────────────────────┐  ┌─────────────────────┐│  │
│  │  │ Nodes share image layers    │  │ Alternative P2P     ││  │
│  │  │ Reduces registry load 90%+  │  │ (less active)       ││  │
│  │  └─────────────────────────────┘  └─────────────────────┘│  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  CLOUD MANAGED                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ECR         │  GCR/Artifact    │  ACR         │  GHCR   │  │
│  │  (AWS)       │  Registry (GCP)   │  (Azure)     │ (GitHub)│  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Why Self-Host?

```
SELF-HOSTED REGISTRY DECISION TREE
─────────────────────────────────────────────────────────────────

Start here: Do you NEED to self-host?
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
Air-gapped?    Rate limits?    Compliance?
    │               │               │
    │ Yes           │ Yes           │ Yes
    ▼               ▼               ▼
Harbor/Zot     Harbor+cache    Harbor+scanning
(required)     (proxy mode)    (required)
    │               │               │
    │ No            │ No            │ No
    ▼               ▼               ▼
┌─────────────────────────────────────────────────┐
│ Consider managed registry (ECR/GCR/ACR)         │
│ • Less operational overhead                     │
│ • Integrated with cloud IAM                     │
│ • Pay for storage/transfer                      │
└─────────────────────────────────────────────────┘

SCALE DECISION:
─────────────────────────────────────────────────────────────────
Nodes < 100        →  Harbor/Zot alone is fine
Nodes 100-500      →  Consider caching proxy
Nodes 500+         →  Dragonfly P2P becomes essential
Nodes 1000+        →  P2P is the only way
```

## Study Path

```
Module 13.1: Harbor
     │
     │  Enterprise registry
     │  Scanning, RBAC, replication
     │  Most common choice
     ▼
Module 13.2: Zot
     │
     │  Lightweight alternative
     │  OCI-native, minimal
     │  Edge/IoT use cases
     ▼
Module 13.3: Dragonfly
     │
     │  P2P distribution
     │  Massive scale deployments
     │  Works with Harbor/any registry
     ▼
[Toolkit Complete] → K8s Distributions Toolkit
```

## Key Concepts

### OCI Image Specification

```
OCI IMAGE STRUCTURE
─────────────────────────────────────────────────────────────────

Image Reference: registry.example.com/myapp:v1.0.0
                 └──────┬──────┘ └──┬─┘ └─┬─┘
                     registry   repo   tag

Image Manifest:
┌─────────────────────────────────────────────────────────────┐
│ {                                                           │
│   "schemaVersion": 2,                                       │
│   "mediaType": "application/vnd.oci.image.manifest.v1+json",│
│   "config": {                                               │
│     "digest": "sha256:abc123...",                           │
│     "size": 7023                                            │
│   },                                                        │
│   "layers": [                                               │
│     { "digest": "sha256:def456...", "size": 32654321 },    │
│     { "digest": "sha256:ghi789...", "size": 16724 }        │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

Content-addressable: Layers are identified by SHA256 hash
Deduplication: Same layer in different images stored once
```

### Registry Operations

| Operation | Description | Example |
|-----------|-------------|---------|
| **Push** | Upload image to registry | `docker push registry/app:v1` |
| **Pull** | Download image from registry | `docker pull registry/app:v1` |
| **Catalog** | List all repositories | `curl /v2/_catalog` |
| **Tags** | List tags for repo | `curl /v2/app/tags/list` |
| **Manifest** | Get image metadata | `curl /v2/app/manifests/v1` |
| **Blob** | Get layer data | `curl /v2/app/blobs/sha256:...` |

## Common Architectures

### Single Datacenter

```
SINGLE DATACENTER ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                      Datacenter                             │
│                                                             │
│  ┌─────────────┐                                           │
│  │   Harbor    │◄──── CI/CD pushes images                  │
│  │  (primary)  │                                           │
│  └──────┬──────┘                                           │
│         │                                                   │
│         │ Pull                                              │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Kubernetes Cluster                      │   │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │   │
│  │  │Node │ │Node │ │Node │ │Node │ │Node │          │   │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Region with Replication

```
MULTI-REGION ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────┐     ┌─────────────────────┐
│   US-East (Primary) │     │   EU-West (Replica) │
│                     │     │                     │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │    Harbor     │──┼─────┼─▶│    Harbor     │  │
│  │   (primary)   │  │ sync│  │   (replica)   │  │
│  └───────────────┘  │     │  └───────────────┘  │
│         │           │     │         │           │
│         ▼           │     │         ▼           │
│   ┌─────────┐       │     │   ┌─────────┐       │
│   │   K8s   │       │     │   │   K8s   │       │
│   │ Cluster │       │     │   │ Cluster │       │
│   └─────────┘       │     │   └─────────┘       │
│                     │     │                     │
└─────────────────────┘     └─────────────────────┘

Benefits:
• Local pulls (low latency)
• Disaster recovery
• Regional compliance
```

### Large Scale with P2P

```
P2P DISTRIBUTION (DRAGONFLY)
─────────────────────────────────────────────────────────────────

                    ┌───────────────┐
                    │    Harbor     │
                    │   Registry    │
                    └───────┬───────┘
                            │
                    ┌───────┴───────┐
                    │   Dragonfly   │
                    │   Scheduler   │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │  Node 1 │◄───────▶│  Node 2 │◄───────▶│  Node 3 │
   │ (peer)  │         │ (peer)  │         │ (peer)  │
   └─────────┘         └─────────┘         └─────────┘
        ▲                   ▲                   ▲
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                     P2P layer sharing

Node 1 pulls from registry, shares with Node 2 & 3
Registry bandwidth: 1x (not 3x)
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Harbor | Deploy on K8s, create project, push/pull/scan |
| Zot | Run single binary, configure replication |
| Dragonfly | Deploy P2P layer, measure distribution speed |

## Cost Considerations

```
TOTAL COST OF OWNERSHIP
─────────────────────────────────────────────────────────────────

Harbor Self-hosted (100GB storage, 1000 pulls/day):
├── Compute: 2 vCPU, 4GB RAM ≈ $60/month
├── Storage: 100GB SSD ≈ $10/month
├── Bandwidth: Internal (free)
├── Engineering: 0.1 FTE ≈ $1,500/month
└── Total: ~$1,600/month

ECR (100GB storage, 1000 pulls/day):
├── Storage: 100GB × $0.10 = $10/month
├── Transfer: 50GB × $0.09 = $4.50/month (cross-region)
├── Engineering: Minimal
└── Total: ~$15/month + engineering savings

WHEN SELF-HOSTED WINS:
─────────────────────────────────────────────────────────────────
• Air-gapped requirement (no choice)
• High volume (>10TB storage, >100k pulls/day)
• Compliance requiring on-prem
• Multi-cloud (avoid vendor lock-in)

WHEN MANAGED WINS:
─────────────────────────────────────────────────────────────────
• Small-medium scale
• Single cloud provider
• Limited platform engineering capacity
• Standard compliance requirements
```

## Related Tracks

- **Before**: [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) — Supply chain security
- **Before**: [Security Tools Toolkit](../../security-quality/security-tools/) — Image scanning concepts
- **Related**: [CI/CD Pipelines Toolkit](../ci-cd-pipelines/) — Building images
- **Related**: [GitOps & Deployments](../gitops-deployments/) — Deploying images
- **After**: [K8s Distributions Toolkit](../../infrastructure-networking/k8s-distributions/) — Running workloads

---

*"Your container registry is the source of truth for what runs in production. Treat it with the same care as your Git repository."*
