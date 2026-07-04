---
title: "Дисципліна Data Engineering на Kubernetes"
sidebar:
  order: 1
  label: "Data Engineering"
en_commit: 47bf257c3ec7632099185c630faf64d73e48caea
---
**Запуск інфраструктури даних на Kubernetes — бази даних, черги, потокова обробка та аналітика.**

Data Engineering на Kubernetes фокусується на викликах запуску систем зі станом (stateful) у динамічному середовищі. Ця дисципліна охоплює архітектуру сховищ, оператори для баз даних, масштабування потокових платформ та управління життєвим циклом даних. Ви навчитеся перетворювати Kubernetes на надійну платформу для ваших даних.

---

## Модулі

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1.1 | [Stateful на Kubernetes: Основи](module-1.1-stateful-fundamentals/) | 3 год | PV/PVC, StorageClasses, StatefulSets, Local Persistence |
| 1.2 | [Оператори для баз даних](module-1.2-db-operators/) | 4 год | CloudNativePG, Zalando Postgres, PGO, MySQL Operator |
| 1.3 | [Стрімінг даних (Kafka на K8s)](/uk/cloud/managed-services/module-9.7-streaming/) | 5 год | Strimzi, партиціонування, вирівнювання навантаження, Quotas |
| 1.4 | [NoSQL та аналітичні БД](/uk/cloud/managed-services/module-9.10-analytics/) | 4 год | ClickHouse (Altinity), MongoDB, Cassandra, Vector DBs |
| 1.5 | [Оркестрація та якість даних](module-1.5-data-orchestration/) | 3 год | Airflow на K8s, Spark on K8s, перевірки якості (Great Expectations) |
| 1.6 | [Бекап та відновлення даних](module-1.6-data-resilience/) | 3 год | Velero, Kasten (K10), архітектура DR для даних |

**Загальний час**: ~22 години

---

## Передумови

- Адміністрування Kubernetes (рівень CKA)
- Розуміння Kubernetes Storage (PV/PVC)
- Базові знання SQL та архітектури баз даних
