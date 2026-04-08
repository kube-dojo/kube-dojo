---
title: "Основи GCP DevOps"
sidebar:
  order: 0
  label: "Основи GCP"
---
**Все, що вам потрібно для продуктивної роботи в Google Cloud — перш ніж торкатися GKE.**

Google створив GCP, щоб монетизувати інфраструктуру планетарного масштабу, яка забезпечує роботу Пошуку та YouTube. Цей трек охоплює основні сервіси GCP, які потрібні кожному інженеру DevOps: ідентифікація, мережа, обчислення, контейнери, безсерверні рішення, секрети, спостережуваність та CI/CD.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1 | [IAM та ієрархія ресурсів](module-2.1-iam/) | 2 год | Орг/Папка/Проєкт, сервісні акаунти, Workload Identity |
| 2 | [VPC та мережі](module-2.2-vpc/) | 3 год | Глобальні VPC, правила файрвола, Shared VPC |
| 3 | [Compute Engine](module-2.3-compute/) | 2.5 год | Сімейства машин, MIG, глобальне балансування навантаження |
| 4 | [Cloud Storage (GCS)](module-2.4-gcs/) | 1.5 год | Класи зберігання, життєвий цикл, підписані URL |
| 5 | [Cloud DNS](module-2.5-dns/) | 1.5 год | Публічні/приватні зони, пересилання, піринг |
| 6 | [Artifact Registry](module-2.6-artifact-registry/) | 1 год | Образи контейнерів, сканування, кешування |
| 7 | [Cloud Run](module-2.7-cloud-run/) | 2.5 год | Безсерверні контейнери, розділення трафіку |
| 8 | [Cloud Functions](module-2.8-cloud-functions/) | 2 год | Gen 2, Eventarc, подієво-орієнтовані шаблони |
| 9 | [Secret Manager](module-2.9-secret-manager/) | 1.5 год | Секрети, версії, інтеграція з IAM |
| 10 | [Cloud Operations](module-2.10-operations/) | 2.5 год | Логування, моніторинг, PromQL/MQL, алертинг |
| 11 | [Cloud Build та CI/CD](module-2.11-cloud-build/) | 2 год | cloudbuild.yaml, тригери, Cloud Deploy |
| 12 | [Архітектурні патерни GCP](module-2.12-patterns/) | 1.5 год | Landing zones, IAP, огляд Anthos |

**Загальний час**: ~23.5 години

---

## Передумови

- [Основи Cloud Native](../../prerequisites/cloud-native-101/)
- [Розеттський камінь гіперскейлерів](../hyperscaler-rosetta-stone/) — рекомендовано
