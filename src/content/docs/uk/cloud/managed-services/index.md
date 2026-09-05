---
title: "Хмарні керовані сервіси"
slug: uk/cloud/managed-services
sidebar:
  order: 0
  label: "Керовані сервіси"
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/cloud/managed-services/index.md"
---

**Інтеграція робочих навантажень Kubernetes із керованими базами даних, брокерами повідомлень, serverless-функціями, кешуванням, пошуком та аналітикою.**

Запуск всього всередині кластера спокусливий — доки ви не зіткнетеся зі split-brain у RabbitMQ, пошкодженим індексом Elasticsearch або Pod бази даних у Pending через неправильну AZ. Керовані (managed) сервіси вирішують найскладніші задачі експлуатації, щоб ваша команда могла зосередитися на логіці додатків. Але інтеграція нетривіальна: потрібні приватні мережі, workload identity, connection pooling, автоскейлінг та оптимізація витрат. Ця частина навчить вас підключати Kubernetes до основних категорій керованих хмарних сервісів — безпечно, ефективно та надійно.

---

## Модулі

| # | Модуль | Складність | Час | Чого ви навчитеся |
|---|--------|------------|------|-------------------|
| 1 | [Інтеграція реляційних баз даних (RDS / Cloud SQL / Flexible Server)](module-9.1-databases/) | `[MEDIUM]` | 2 год | Приватне підключення, connection pooling, ротація облікових даних, міграції схем |
| 2 | [Керовані брокери повідомлень та Event-Driven Kubernetes](module-9.2-message-brokers/) | `[COMPLEX]` | 2.5 год | SQS/SNS, Pub/Sub, Service Bus, автоскейлінг KEDA, dead-letter черги |
| 3 | [Взаємодія із Serverless (Lambda / Cloud Functions / Knative)](module-9.3-serverless/) | `[COMPLEX]` | 2 год | Межа між Serverless та Kubernetes, тригери подій, маршрутизація API Gateway, Knative |
| 4 | [Патерни об'єктного сховища (S3 / GCS / Blob)](module-9.4-object-storage/) | `[MEDIUM]` | 2 год | Workload identity, драйвери CSI, pre-signed URL, політики життєвого циклу, реплікація |
| 5 | [Просунуті сервіси кешування (ElastiCache / Memorystore)](module-9.5-caching/) | `[COMPLEX]` | 2 год | Redis проти Memcached, керування з'єднаннями, стратегії витіснення (eviction), оптимізація cache hit |
| 6 | [Пошукові та аналітичні рушії (OpenSearch / Elasticsearch)](module-9.6-search/) | `[COMPLEX]` | 2.5 год | Збір логів (log ingestion), керування життєвим циклом індексів, шардування, контроль доступу |
| 7 | [Конвеєри потокових даних (MSK / Confluent / Dataflow)](module-9.7-streaming/) | `[COMPLEX]` | 3 год | Керований Kafka, партиціювання, затримка споживачів (consumer lag), реєстри схем, обробка потоків |
| 8 | [Глибоке занурення в керування секретами](module-9.8-secrets-deep/) | `[COMPLEX]` | 2 год | External Secrets Operator, Secrets Store CSI, HashiCorp Vault, динамічні секрети |
| 9 | [Cloud-Native API Gateways та WAF](module-9.9-api-gateways/) | `[COMPLEX]` | 2.5 год | Хмарні API-шлюзи, інтеграція з WAF, rate limiting, OAuth2/OIDC, gRPC/WebSocket |
| 10 | [Сховища даних та аналітика з Kubernetes](module-9.10-analytics/) | `[COMPLEX]` | 2.5 год | BigQuery/Redshift/Snowflake, Airflow на Kubernetes, ефемерні обчислення, конвеєри даних |

**Загальний час**: ~23 години

---

## Попередні вимоги

- [Патерни хмарної архітектури](../architecture-patterns/) — хмарний IAM, топології VPC
- Щонайменше одне глибоке занурення в провайдера ([EKS](../eks-deep-dive/), [GKE](../gke-deep-dive/), або [AKS](../aks-deep-dive/))
- Основи мережі Kubernetes (Services, Ingress, DNS)

## Що далі

Після керованих сервісів продовжуйте з:

- [Просунуті хмарні операції](../advanced-operations/) — мультиакаунти, DR, active-active, оптимізація витрат у масштабі
- [Корпоративні та гібридні хмари](../enterprise-hybrid/) — landing zones, управління (governance), відповідність стандартам, керування парком кластерів (fleet management)