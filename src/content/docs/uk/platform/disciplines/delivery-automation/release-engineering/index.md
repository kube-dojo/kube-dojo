---
title: "Дисципліна Release Engineering"
sidebar:
  order: 1
  label: "Release Engineering"
en_commit: 47bf257c3ec7632099185c630faf64d73e48caea
---
**Як надійно доставляти програмне забезпечення у масштабі.**

Це НЕ базовий CI/CD — це розглядається в [Сучасному DevOps](../../../../prerequisites/modern-devops/module-1.3-cicd-pipelines/). Release Engineering фокусується на стратегії релізів, прогресивній доставці (progressive delivery), управлінні функціями (feature management) та координації релізів між багатьма сервісами та регіонами.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1.1 | [Стратегії релізів та прогресивна доставка](/uk/k8s/kcna/part4-application-delivery/module-4.3-release-strategies/) | 2 год | Blue/Green, Canary, Shadow, радіус ураження, міграції БД |
| 1.2 | [Просунутий Canary з Argo Rollouts](module-1.2-argo-rollouts/) | 3 год | Rollouts CRD, AnalysisRuns, просування на основі метрик |
| 1.3 | [Управління функціями у масштабі](module-1.3-feature-flags/) | 2.5 год | OpenFeature, Unleash, життєвий цикл прапорців, kill switches |
| 1.4 | [Оркестрація глобальних та мультирегіональних релізів](module-1.4-global-releases/) | 3 год | Ring deployments, ApplicationSets, перемикання трафіку |
| 1.5 | [Метрики Release Engineering](module-1.5-release-metrics/) | 2 год | Метрики DORA, здоров'я релізів, спостережуваність розгортань |

**Загальний час**: ~12.5 годин

---

## Передумови

- [CI/CD Конвеєри](../../../../prerequisites/modern-devops/module-1.3-cicd-pipelines/) — базові концепції конвеєрів
- [Kubernetes Deployments](../../../../prerequisites/kubernetes-basics/module-1.4-deployments/) — поступові оновлення
- Основи Prometheus/Grafana (для модулів про метрики)

## Що далі

Після Release Engineering переходьте до **[Chaos Engineering](../../reliability-security/chaos-engineering/)** — тестуйте ваші релізи за допомогою контрольованого впровадження відмов.
