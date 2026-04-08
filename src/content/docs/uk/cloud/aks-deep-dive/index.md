---
title: "Глибоке занурення в Azure AKS"
sidebar:
  order: 0
---
**Промисловий Kubernetes в Azure — від пулів вузлів до масштабування через KEDA.**

AKS — найбільш динамічний керований сервіс Kubernetes, тісно інтегрований з екосистемою Azure. Цей трек охоплює архітектуру пулів вузлів та інтеграцію з Entra ID, чотири моделі мережі CNI (Kubenet, Azure CNI, CNI Overlay, Cilium), безпеку без паролів через Workload Identity та Key Vault, а також операційну роботу з Container Insights, Managed Prometheus та масштабуванням KEDA.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1 | [Архітектура AKS та управління вузлами](module-7.1-aks-architecture/) | 2 год | Системні/користувацькі пули, VMSS, зони доступності, RBAC |
| 2 | [Просунуті мережі AKS](module-7.2-aks-networking/) | 3.5 год | Kubenet vs Azure CNI vs Overlay vs Cilium, політики, Private Link |
| 3 | [Workload Identity та безпека в AKS](module-7.3-aks-identity/) | 1.5 год | Entra Workload Identity, Secrets Store CSI, Azure Policy |
| 4 | [Сховища, моніторинг та масштабування в AKS](module-7.4-aks-production/) | 2.5 год | Azure Disks/Files, Container Insights, Managed Prometheus, KEDA |

**Загальний час**: ~9.5 годин

---

## Передумови

- [Основи Azure DevOps](../azure-essentials/) — Entra ID, VNets, ВМ, Сховища
- [Архітектурні патерни хмар](../architecture-patterns/) — компроміси керованого K8s, мультикластер, інтеграція IAM

## Що далі

Після «Глибокого занурення в AKS» досліджуйте мультихмарні патерни або **[Трек платформної інженерії](../../platform/)**.
