---
title: "Cloud-Native Managed Services"
sidebar:
  order: 0
  label: "Managed Services"
---
**Integrating Kubernetes workloads with managed databases, message brokers, serverless functions, caching, search, and analytics services.**

Running everything inside your cluster is tempting -- until you experience a split-brain RabbitMQ, a corrupted self-managed Elasticsearch index, or a database pod stuck in Pending because its volume is in the wrong AZ. Managed services handle the hardest operational problems so your team can focus on application logic. But integration is not trivial: you need private networking, workload identity, connection pooling, autoscaling consumers, and cost optimization. This part teaches you how to connect Kubernetes to every major category of managed cloud service -- securely, efficiently, and reliably.

---

## Modules

| # | Module | Complexity | Time | What You'll Learn |
|---|--------|------------|------|-------------------|
| 1 | [Relational Database Integration (RDS / Cloud SQL / Flexible Server)](module-9.1-databases/) | `[MEDIUM]` | 2h | Private connectivity, connection pooling, credential rotation, schema migrations |
| 2 | [Managed Message Brokers & Event-Driven Kubernetes](module-9.2-message-brokers/) | `[COMPLEX]` | 2.5h | SQS/SNS, Pub/Sub, Service Bus, KEDA autoscaling, dead-letter queues |
| 3 | [Serverless Interoperability (Lambda / Cloud Functions / Knative)](module-9.3-serverless/) | `[COMPLEX]` | 2h | Serverless-Kubernetes boundary, event triggers, API Gateway routing, Knative |
| 4 | [Object Storage Patterns (S3 / GCS / Blob)](module-9.4-object-storage/) | `[MEDIUM]` | 2h | Workload identity, CSI drivers, pre-signed URLs, lifecycle policies, replication |
| 5 | [Advanced Caching Services (ElastiCache / Memorystore)](module-9.5-caching/) | `[COMPLEX]` | 2h | Redis vs Memcached, connection management, eviction strategies, cache hit optimization |
| 6 | [Search & Analytics Engines (OpenSearch / Elasticsearch)](module-9.6-search/) | `[COMPLEX]` | 2.5h | Log ingestion, index lifecycle management, sharding, fine-grained access control |
| 7 | [Streaming Data Pipelines (MSK / Confluent / Dataflow)](module-9.7-streaming/) | `[COMPLEX]` | 3h | Managed Kafka, partitioning, consumer lag, schema registries, stream processing |
| 8 | [Secrets Management Deep Dive](module-9.8-secrets-deep/) | `[COMPLEX]` | 2h | External Secrets Operator, Secrets Store CSI, HashiCorp Vault, dynamic secrets |
| 9 | [Cloud-Native API Gateways & WAF](module-9.9-api-gateways/) | `[COMPLEX]` | 2.5h | Cloud API gateways, WAF integration, rate limiting, OAuth2/OIDC, gRPC/WebSocket |
| 10 | [Data Warehousing & Analytics from Kubernetes](module-9.10-analytics/) | `[COMPLEX]` | 2.5h | BigQuery/Redshift/Snowflake, Airflow on Kubernetes, ephemeral compute, data pipelines |

**Total time**: ~23 hours

---

## Prerequisites

- [Cloud Architecture Patterns](../architecture-patterns/) -- cloud IAM, VPC topologies
- At least one provider deep dive ([EKS](../eks-deep-dive/), [GKE](../gke-deep-dive/), or [AKS](../aks-deep-dive/))
- Kubernetes networking basics (Services, Ingress, DNS)

## What's Next

After Managed Services, continue with:

- [Advanced Cloud Operations](../advanced-operations/) -- multi-account, DR, active-active, cost optimization at scale
- [Enterprise & Hybrid Cloud](../enterprise-hybrid/) -- landing zones, governance, compliance, fleet management
