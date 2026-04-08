---
title: "Глибоке занурення в AWS EKS"
sidebar:
  order: 0
---
**Промисловий Kubernetes в AWS — від архітектури до оптимізації витрат.**

EKS — найпопулярніший керований сервіс Kubernetes. Цей трек охоплює повний шлях до продакшну: архітектура control plane, мережа VPC CNI (і як уникнути вичерпання IP), IAM на рівні подів через IRSA та Pod Identity, сховища EBS/EFS/S3, а також операційну роботу з Karpenter, спостережуваність та управління витратами.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1 | [Архітектура та Control Plane EKS](module-5.1-eks-architecture/) | 2.5 год | API ендпоінти, групи вузлів vs Fargate, EKS Add-ons, Access Entries |
| 2 | [Мережа EKS: Глибоке занурення (VPC CNI)](module-5.2-eks-networking/) | 3.5 год | Розподіл IP, Prefix Delegation, кастомні мережі, Security Groups для подів |
| 3 | [Ідентифікація в EKS: IRSA vs Pod Identity](module-5.3-eks-identity/) | 1.5 год | IAM на рівні подів, федерація OIDC, міграція на Pod Identity |
| 4 | [Сховища та управління даними в EKS](module-5.4-eks-storage/) | 2 год | EBS CSI, EFS CSI, Mountpoint для S3, стійкість StatefulSet до збоїв AZ |
| 5 | [EKS у продакшні: Масштабування та витрати](module-5.5-eks-production/) | 3 год | Karpenter, Spot-екземпляри, Container Insights, Kubecost |

**Загальний час**: ~12.5 годин

---

## Передумови

- [Основи AWS DevOps](../aws-essentials/) — IAM, VPC, EC2, S3
- [Архітектурні патерни хмар](../architecture-patterns/) — компроміси керованого K8s, мультикластер, інтеграція IAM

## Що далі

Після «Глибокого занурення в EKS» досліджуйте мультихмарні патерни або **[Трек платформної інженерії](../../platform/)**.
