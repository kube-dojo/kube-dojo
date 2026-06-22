---
title: "Розширення Kubernetes"
sidebar:
  order: 0
  label: "Розширення Kubernetes"
revision_pending: false
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/k8s/extending/index.md"
calque_review:
  reviewed_at: "2026-06-22"
  detector_version: "v2"
  status: "clean"
  flags_resolved: 0
  content_sha: "fe3f6d77e3da91a4a8c5c34d1569bff2575aa57c4d4d115b0a7cb23118bf7d08"
---
**Будуйте НА Kubernetes, а не просто ВИКОРИСТОВУЙТЕ його.**

Цей напрямок призначений для інженерів, яким потрібно розширювати саму платформу Kubernetes — писати власні контролери, оператори, вебхуки допуску та плагіни планувальника. У цьому й полягає різниця між користувачем K8s та будівничим платформи на основі K8s.

Усі модулі містять реальний код мовою Go, придатний до компіляції.

---

## Модулі

| # | Модуль | Час | Що ви побудуєте |
|---|--------|------|-------------------|
| 1.1 | [Архітектура API та розширюваність](module-1.1-api-deep-dive/) | 3 год | Програма на Go з Informer із client-go |
| 1.2 | [Поглиблене вивчення CRD](module-1.2-crds-advanced/) | 3 год | Складний CRD із валідацією, версіонуванням, субресурсами |
| 1.3 | [Контролери з client-go](module-1.3-controllers-client-go/) | 5 год | Власний контролер з нуля (без фреймворків) |
| 1.4 | [Kubebuilder та оператори](module-1.4-kubebuilder/) | 4 год | Згенерований оператор із Reconciler |
| 1.5 | [Розробка операторів: поглиблений рівень](module-1.5-advanced-operators/) | 5 год | Finalizers, Conditions, Events, envtest |
| 1.6 | [Вебхуки допуску](module-1.6-admission-webhooks/) | 4 год | Мутаційний вебхук, що впроваджує sidecar |
| 1.7 | [Плагіни планувальника](module-1.7-scheduler-plugins/) | 4 год | Власний плагін Score + вторинний планувальник |
| 1.8 | [Агрегація API](module-1.8-api-aggregation/) | 5 год | Сервер розширення API (Extension API Server) |

**Загальний час**: ~33 години

---

## Передумови

- Сертифікація CKA або еквівалентний досвід роботи з Kubernetes
- Програмування мовою Go (від базового до середнього рівня)
- [Модуль CKA 1.5: CRD та оператори](../cka/part1-cluster-architecture/module-1.5-crds-operators/) є вступом — цей напрямок занурюється значно глибше
