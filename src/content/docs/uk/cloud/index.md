---
title: "Хмара"
sidebar:
  order: 1
---
**Опануйте гіперскейлери, на яких працюють ваші кластери Kubernetes.**

Kubernetes не існує у вакуумі. Він працює на AWS, GCP або Azure — і вам потрібно знати хмарну платформу під ним. Цей трек проведе вас від основ хмарних технологій до production-grade керованого Kubernetes.

---

## Шлях навчання

```
Rosetta Stone (крос-провайдерні концепції)
        │
        ├── AWS Essentials (12 модулів)
        ├── GCP Essentials (12 модулів)
        └── Azure Essentials (12 модулів)
                │
                ▼
        Architecture Patterns (4 модулі)
                │
                ├── EKS Deep Dive (5 модулів)
                ├── GKE Deep Dive (5 модулів)
                └── AKS Deep Dive (4 модулі)
                        │
                        ▼
                Advanced Operations (10 модулів)
                Managed Services (10 модулів)
                Enterprise & Hybrid (10 модулів)
```

**Оберіть свого провайдера** — вам не потрібні всі три. Вивчіть основи хмари, яку використовуєте, а потім заглибтеся в її кероване рішення Kubernetes.

---

## Розділи

| Розділ | Модулі | Опис |
|--------|--------|------|
| [Hyperscaler Rosetta Stone](hyperscaler-rosetta-stone/) | 1 | Зіставлення концепцій між провайдерами |
| [AWS Essentials](aws-essentials/) | 12 | IAM, VPC, EC2, S3, Route53, ECR, ECS, Lambda, Secrets, CloudWatch, CI/CD, CloudFormation |
| [GCP Essentials](gcp-essentials/) | 12 | IAM, VPC, Compute, Cloud Storage, DNS, Artifact Registry, Cloud Run, Functions, Secret Manager, Monitoring, Cloud Build, Deployment Manager |
| [Azure Essentials](azure-essentials/) | 12 | Entra ID, VNet, VMs, Blob Storage, Azure DNS, ACR, ACI, Functions, Key Vault, Monitor, DevOps, Bicep |
| [Architecture Patterns](architecture-patterns/) | 4 | Керований vs самокерований, мультикластер, хмарний IAM, топології VPC |
| [EKS Deep Dive](eks-deep-dive/) | 5 | Архітектура EKS, мережа, ідентифікація, автомасштабування, production |
| [GKE Deep Dive](gke-deep-dive/) | 5 | Архітектура GKE, мережа, Workload Identity, Autopilot, Fleet |
| [AKS Deep Dive](aks-deep-dive/) | 4 | Архітектура AKS, мережа, ідентифікація, production |
| [Advanced Operations](advanced-operations/) | 10 | Мульти-акаунт, транзитні хаби, міжкластерна мережа, DR, active-active |
| [Managed Services](managed-services/) | 10 | Бази даних, кешування, обмін повідомленнями, ML-сервіси, аналітика |
| [Enterprise & Hybrid](enterprise-hybrid/) | 10 | Landing zones, гібридне підключення, комплаєнс, міграція, управління флотом |

**85 модулів загалом.** Не все стосується Kubernetes — треки основ охоплюють автономні контейнери, безсерверні рішення та випадки, коли K8s — надмірне рішення.

---

## Передумови

- [Основи](../prerequisites/) — Cloud Native 101, Docker, базовий K8s
- [Поглиблене вивчення Linux](../linux/) — рекомендовано для модулів з мережі та безпеки
