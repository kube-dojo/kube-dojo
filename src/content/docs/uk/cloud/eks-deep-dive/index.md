---
title: "Глибоке занурення в AWS EKS"
slug: uk/cloud/eks-deep-dive
sidebar:
  order: 0
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/cloud/eks-deep-dive/index.md"
---
**Kubernetes рівня продакшн на AWS — від архітектури до оптимізації витрат.**

EKS — це найпоширеніший керований сервіс Kubernetes. Цей трек охоплює повний шлях до продакшну: архітектуру control plane, мережеву взаємодію VPC CNI (та як уникнути вичерпання IP-адрес), IAM на рівні Pod за допомогою IRSA та Pod Identity, роботу зі сховищами даних EBS/EFS/S3, а також експлуатацію в продакшні за допомогою Karpenter, обсервабіліті та управління витратами.

---

## Модулі

| # | Модуль | Час | Що ви дізнаєтесь |
|---|--------|------|-------------------|
| 1 | [Модуль 5.1: Архітектура EKS та Control Plane](module-5.1-eks-architecture/) | 2.5г | API-ендпоїнти, node groups проти Fargate, EKS Add-ons, Access Entries |
| 2 | [Модуль 5.2: Глибоке занурення в мережу EKS (VPC CNI)](module-5.2-eks-networking/) | 3.5г | Розподіл IP-адрес, Prefix Delegation, Custom Networking, Security Groups для Pod-ів |
| 3 | [Модуль 5.3: Ідентифікація в EKS: IRSA проти Pod Identity](module-5.3-eks-identity/) | 1.5г | IAM на рівні Pod, федерація OIDC, міграція з IRSA на Pod Identity |
| 4 | [Модуль 5.4: Сховища та управління даними в EKS](module-5.4-eks-storage/) | 2г | EBS CSI, EFS CSI, Mountpoint для S3, стійкість StatefulSet до збоїв AZ |
| 5 | [Модуль 5.5: EKS у продакшні: масштабування, обсервабіліті та витрати](module-5.5-eks-production/) | 3г | Karpenter, Spot-інстанси, Container Insights, Kubecost |

**Загальний час**: ~12.5 годин

---

## Передумови

- [Основи AWS DevOps](../aws-essentials/) — фундаментальні знання IAM, VPC, EC2, S3
- [Шаблони хмарної архітектури](../architecture-patterns/) — компроміси керованого K8s, мультикластерність, інтеграція IAM

## Що далі

Після завершення курсу EKS Deep Dive ознайомтеся з мультихмарними шаблонами або перейдіть до [треку з розробки платформ (Platform Engineering)](../../platform/).