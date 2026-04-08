---
title: "Основи Azure DevOps"
sidebar:
  order: 0
  label: "Основи Azure"
---
**Все, що вам потрібно для продуктивної роботи в Microsoft Azure — перш ніж торкатися AKS.**

Microsoft створив Azure, щоб розширити можливості Windows Server, Active Directory та корпоративних ІТ у хмарі. Цей трек охоплює основні сервіси Azure, які потрібні кожному інженеру DevOps: ідентифікація (Entra ID), мережа, обчислення, контейнери, безсерверні рішення, секрети, спостережуваність та CI/CD.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1 | [Entra ID та Azure RBAC](module-3.1-entra-id/) | 2.5 год | Тенети, керовані ідентифікатори, RBAC |
| 2 | [Віртуальні мережі (VNet)](module-3.2-vnet/) | 3 год | NSG, ASG, VNet Peering, hub-and-spoke |
| 3 | [ВМ та VM Scale Sets](module-3.3-vms/) | 2 год | VMSS, зони доступності, Azure LB |
| 4 | [Blob Storage та Data Lake](module-3.4-blob/) | 1.5 год | Рівні доступу, SAS токени, доступ за ідентифікатором |
| 5 | [Azure DNS та Traffic Manager](module-3.5-dns/) | 1.5 год | Методи маршрутизації, основи Front Door |
| 6 | [ACR (реєстр контейнерів)](module-3.6-acr/) | 1 год | Задачі ACR, геореплікація, Private Link |
| 7 | [ACI та Container Apps](module-3.7-aci-aca/) | 3 год | Автономні контейнери, KEDA, Dapr |
| 8 | [Azure Functions](module-3.8-functions/) | 2 год | Тригери, прив'язки, Durable Functions |
| 9 | [Azure Key Vault](module-3.9-key-vault/) | 1.5 год | Секрети, ключі, сертифікати, керовані ідентифікатори |
| 10 | [Azure Monitor та Log Analytics](module-3.10-monitor/) | 2.5 год | KQL, алерти, App Insights |
| 11 | [CI/CD: Azure DevOps та GitHub Actions](module-3.11-cicd/) | 2 год | YAML конвеєри, OIDC, власні агенти |
| 12 | [ARM та Bicep](module-3.12-bicep/) | 1.5 год | Шаблони, модулі, розгортання What-If |

**Загальний час**: ~24 години

---

## Передумови

- [Основи Cloud Native](../../prerequisites/cloud-native-101/)
- [Розеттський камінь гіперскейлерів](../hyperscaler-rosetta-stone/) — рекомендовано
