---
title: "AI/GPU інфраструктура на Kubernetes"
sidebar:
  order: 1
  label: "AI інфраструктура"
en_commit: 9da37a1d6ab83bf907291b9eb4d153ce184f73c3
---
**Інфраструктурна сторона AI — планування GPU, розподілене навчання та обслуговування LLM у масштабі.**

Ця дисципліна фокусується на інфраструктурних викликах запуску AI-навантажень на Kubernetes. Вона доповнює існуючу [дисципліну MLOps](../mlops/) (життєвий цикл моделей) та [набір інструментів ML Platforms](../../../toolkits/data-ai-platforms/ml-platforms/) (такі інструменти як Kubeflow, MLflow). Тут ви навчитеся підготовці GPU, їх ефективному плануванню, запуску розподіленого навчання та обслуговуванню моделей у продакшні.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1.1 | [Підготовка GPU та Device Plugins](module-1.1-gpu-provisioning/) | 3 год | GPU Operator, NFD, DCGM-Exporter |
| 1.2 | [Просунуте планування та спільне використання GPU](module-1.2-gpu-scheduling/) | 4 год | MIG, time-slicing, DRA, topology-aware |
| 1.3 | [Інфраструктура розподіленого навчання](module-1.3-distributed-training/) | 5 год | NCCL, Multus CNI, PyTorch Operator |
| 1.4 | [Високопродуктивне сховище для AI](module-1.4-ai-storage/) | 3 год | NVMe кешування, JuiceFS, Fluid/Alluxio |
| 1.5 | [Обслуговування LLM у масштабі](module-1.5-llm-serving/) | 4 год | vLLM, TGI, PagedAttention, KEDA |
| 1.6 | [Планування витрат та ємності](module-1.6-ai-cost/) | 3 год | Spot GPUs, Karpenter, Kueue, вартість ініференсу |

**Загальний час**: ~22 години

---

## Передумови

- Адміністрування Kubernetes (рівень CKA)
- Базові знання апаратного забезпечення Linux
- Знайомство з концепціями ML (корисно, але не обов'язково)
