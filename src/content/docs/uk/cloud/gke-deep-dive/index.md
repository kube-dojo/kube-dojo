---
title: "Глибоке занурення в GCP GKE"
sidebar:
  order: 0
---
**Промисловий Kubernetes в Google Cloud — від Autopilot до управління флотом.**

GKE — це найбільш технологічне кероване рішення Kubernetes, з функціями на кшталт Autopilot, Dataplane V2 (eBPF) та управління флотом, що виходять далеко за межі стандартного Kubernetes. Цей трек охоплює вибір архітектури (Standard vs Autopilot), мережу з Dataplane V2 та Gateway API, Workload Identity та Binary Authorization, варіанти сховищ, а також мультикластерні операції з Fleet та Managed Prometheus.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1 | [Архітектура GKE: Standard vs Autopilot](module-6.1-gke-architecture/) | 2 год | Режими кластера, канали оновлень, регіональні vs зональні |
| 2 | [Мережа GKE: Dataplane V2 та Gateway API](module-6.2-gke-networking/) | 3 год | VPC-native кластери, eBPF, Cloud Load Balancing, Gateway API |
| 3 | [Workload Identity та безпека в GKE](module-6.3-gke-identity/) | 2.5 год | Workload Identity Federation, Binary Authorization, Shielded Nodes |
| 4 | [Сховища в GKE](module-6.4-gke-storage/) | 2 год | Persistent Disks, Filestore, Cloud Storage FUSE, Backup for GKE |
| 5 | [Спостережуваність GKE та Fleet Management](module-6.5-gke-fleet/) | 3 год | Cloud Operations, Managed Prometheus, Fleet, Multi-Cluster Services |

**Загальний час**: ~12.5 годин

---

## Передумови

- [Основи GCP DevOps](../gcp-essentials/) — IAM, VPC, Compute Engine
- [Архітектурні патерни хмар](../architecture-patterns/) — компроміси керованого K8s, мультикластер, інтеграція IAM

## Що далі

Після «Глибокого занурення в GKE» досліджуйте мультихмарні патерни або **[Трек платформної інженерії](../../platform/)**.
