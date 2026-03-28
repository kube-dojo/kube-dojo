---
title: "Трек Platform Engineering"
sidebar:
  order: 1
  label: "Platform Engineering"
---
> **За межами сертифікацій** — глибокі знання практиків SRE, Platform Engineering, DevSecOps та MLOps.

---

## Чому цей трек існує

Сертифікації Kubernetes навчають вас, *як* використовувати Kubernetes. Цей трек навчає, *як запускати production-системи* на Kubernetes — дисципліни, принципи та інструменти, що відрізняють операторів від практиків.

Це для тих, хто:
- Має основи Kubernetes (або сертифікації)
- Хоче зрозуміти теорію, а не лише інструменти
- Потребує приймати технологічні рішення на роботі
- Хоче впроваджувати найкращі практики, а не просто складати іспити

---

## Структура

```
platform/
├── foundations/        # Теорія, що не змінюється
│   ├── systems-thinking/
│   ├── reliability-engineering/
│   ├── observability-theory/
│   ├── security-principles/
│   └── distributed-systems/
│
├── disciplines/        # Прикладні практики
│   ├── sre/
│   ├── platform-engineering/
│   ├── gitops/
│   ├── iac/
│   ├── devsecops/
│   ├── mlops/
│   └── aiops/
│
└── toolkits/           # Поточні інструменти (еволюціонуватимуть)
    ├── observability/      # Prometheus, OTel, Grafana
    ├── gitops-deployments/ # ArgoCD, Flux, Helm
    ├── ci-cd-pipelines/    # Dagger, Tekton, Argo Workflows
    ├── iac-tools/          # Terraform, OpenTofu, Pulumi
    ├── security-tools/     # Vault, OPA, Falco
    ├── networking/         # Cilium, Service Mesh
    ├── scaling-reliability/ # Karpenter, KEDA, Velero
    ├── platforms/          # Backstage, Crossplane
    ├── developer-experience/ # K9s, Telepresence
    ├── ml-platforms/       # Kubeflow, MLflow
    └── aiops-tools/        # Виявлення аномалій, AIOps
```

---

## Порядок вивчення

### Почніть з основ

Теорія, що застосовується всюди. Прочитайте це першим — вона не змінюється.

| Трек | Чому починати тут |
|------|-------------------|
| [Системне мислення](foundations/systems-thinking/) | Ментальні моделі для складних систем |
| [Надійність інженерних систем](foundations/reliability-engineering/) | Теорія відмов, резервування, ризик |
| [Розподілені системи](foundations/distributed-systems/) | CAP, консенсус, узгодженість |
| [Теорія спостережуваності](foundations/observability-theory/) | Що вимірювати і чому |
| [Принципи безпеки](foundations/security-principles/) | Zero trust, моделювання загроз |

### Потім оберіть дисципліну

Прикладні практики — як виконувати роботу.

| Дисципліна | Найкраще для |
|------------|-------------|
| [SRE](disciplines/sre/) | Операції, надійність, чергування |
| [Platform Engineering](disciplines/platform-engineering/) | Досвід розробника, самообслуговування |
| [GitOps](disciplines/gitops/) | Розгортання, узгодження |
| [Infrastructure as Code](disciplines/iac/) | Патерни IaC, тестування, дрейф конфігурації |
| [DevSecOps](disciplines/devsecops/) | Інтеграція безпеки, комплаєнс |
| [MLOps](disciplines/mlops/) | Життєвий цикл ML, обслуговування моделей |
| [AIOps](disciplines/aiops/) | Операції на базі AI, автоматизація |

### Використовуйте набори інструментів за потребою

Інструменти змінюються. Використовуйте їх як довідник при впровадженні.

| Набір інструментів | Коли використовувати |
|--------------------|---------------------|
| [Спостережуваність](toolkits/observability/) | Налаштування моніторингу/трейсингу |
| [GitOps та розгортання](toolkits/gitops-deployments/) | Впровадження ArgoCD/Flux |
| [CI/CD конвеєри](toolkits/ci-cd-pipelines/) | Dagger, Tekton, Argo Workflows |
| [Інструменти IaC](toolkits/iac-tools/) | Terraform, OpenTofu, Pulumi, Ansible |
| [Інструменти безпеки](toolkits/security-tools/) | Політики, секрети, безпека середовища виконання |
| [Мережа](toolkits/networking/) | Cilium, Service Mesh |
| [Масштабування та надійність](toolkits/scaling-reliability/) | Karpenter, KEDA, Velero |
| [Платформи](toolkits/platforms/) | Побудова внутрішніх платформ |
| [Досвід розробника](toolkits/developer-experience/) | K9s, Telepresence |
| [ML-платформи](toolkits/ml-platforms/) | ML-інфраструктура |
| [Інструменти AIOps](toolkits/aiops-tools/) | Виявлення аномалій, AIOps |

---

## Формат модулів

Кожен модуль включає:

- **Чому це важливо** — мотивація з реального світу
- **Теорія** — принципи та ментальні моделі
- **Поточний ландшафт** — інструменти, що це реалізують
- **Практика** — практична реалізація
- **Найкращі практики** — як виглядає якісна робота
- **Типові помилки** — антипатерни, яких слід уникати
- **Додаткове читання** — книги, доповіді, наукові статті

---

## Статус

✅ **Цей трек завершено** — 102 модулі в основах, дисциплінах та наборах інструментів.

| Розділ | Модулі | Статус |
|--------|--------|--------|
| Основи | 19 | ✅ Завершено |
| Дисципліни | 43 | ✅ Завершено |
| Набори інструментів | 40 | ✅ Завершено |

---

## Передумови

Перед початком цього треку ви повинні мати:
- Основи Kubernetes (або пройдені [Передумови](../prerequisites/))
- Деякий production-досвід (корисно, але не обов'язково)
- Цікавість до "чому", а не лише "як"

---

*"Інструменти змінюються. Принципи — ні."*
