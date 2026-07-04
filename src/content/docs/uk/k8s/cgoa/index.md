---
title: "CGOA — Сертифікований спеціаліст із GitOps"
sidebar:
  order: 1
  label: "CGOA"
calque_review:
  reviewed_at: "2026-06-25"
  detector_version: "v2"
  status: "clean"
  flags_resolved: 0
  content_sha: "83c267450c10da80d5dbda3ab1d27dfb02219b5e787a2c41d179a4e4a6768daa"
en_commit: f5818b32b6fe612e822ee4ff03ddeac95606e7ff
---
> **Іспит із множинним вибором** | 90 хвилин | Прохідний бал: 75% | $250 USD

## Огляд

CGOA (Certified GitOps Associate) підтверджує ваше розуміння принципів, патернів і пов'язаних практик GitOps. Це **теоретичний іспит** — питання з множинним вибором, без доступу до терміналу. Це як «KCNA для GitOps».

**KubeDojo охоплює ~90%+ тем CGOA** через нашу наявну програму Platform Engineering. Ця сторінка зіставляє домени CGOA з наявними модулями, щоб ви могли готуватися ефективно.

> **Гарна новина**: Якщо ви вже опрацювали нашу дисципліну GitOps та набори інструментів, то вже подолали найскладніші частини. Цей іспит перевіряє розуміння концепцій, а не практичні навички — але наші практичні модулі дають глибоке розуміння, яке робить теоретичні питання легкими.

---

## Модулі для підготовки до іспиту

| № | Модуль |
|---|--------|
| 1.1 | [Огляд стратегії та плану іспиту CGOA](./module-1.1-exam-strategy-and-blueprint-review/) |
| 1.2 | [Огляд принципів GitOps для CGOA](./module-1.2-gitops-principles-review/) |
| 1.3 | [Огляд патернів та інструментарію CGOA](./module-1.3-patterns-and-tooling-review/) |
| 1.4 | [Практичні питання CGOA, набір 1](./module-1.4-practice-questions-set-1/) |
| 1.5 | [Практичні питання CGOA, набір 2](./module-1.5-practice-questions-set-2/) |

---

## Домени іспиту

| Домен | Вага | Охоплення в KubeDojo |
|--------|--------|-------------------|
| Термінологія GitOps | 20% | Відмінне (модулі дисципліни GitOps) |
| Принципи GitOps | 30% | Відмінне (модулі дисципліни GitOps + IaC) |
| Пов'язані практики | 16% | Відмінне (модулі IaC, DevOps, CI/CD, DevSecOps) |
| Патерни GitOps | 20% | Відмінне (модулі просування, дрейфу, прогресивної доставки) |
| Інструментарій | 14% | Відмінне (модулі ArgoCD, Flux, Helm, Kustomize) |

---

## Домен 1: Термінологія GitOps (20%)

### Компетенції
- Концепції безперервної доставки та розгортання
- Декларативний та імперативний підходи
- Бажаний стан і сховища стану
- Виявлення та виправлення дрейфу
- Цикли узгодження

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | Що таке GitOps? 4 принципи OpenGitOps, ключова термінологія | Пряма |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Виявлення дрейфу та цикли узгодження | Пряма |
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Декларативний vs імперативний підхід, концепції бажаного стану | Пряма |
| [IaC 6.5](../../platform/disciplines/delivery-automation/iac/module-6.5-drift-remediation/) | Стратегії виправлення дрейфу | Пряма |
| [Modern DevOps: GitOps](../../prerequisites/modern-devops/module-1.2-gitops/) | Огляд GitOps для початківців | Допоміжна |

---

## Домен 2: Принципи GitOps (30%)

### Компетенції
- **Декларативність**: Бажаний стан описується декларативно
- **Версіонованість і незмінність**: Бажаний стан зберігається у версіонованому, незмінному джерелі істини
- **Автоматичне витягування**: Агенти автоматично витягують бажаний стан
- **Постійне узгодження**: Агенти постійно відстежують і узгоджують фактичний стан

> Це домен із найбільшою вагою. Знайте [принципи OpenGitOps v1.0](https://opengitops.dev/) напам'ять.

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | 4 принципи OpenGitOps — детальний розбір | Пряма |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Git як версіоноване, незмінне джерело істини; стратегії репозиторіїв | Пряма |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Постійне узгодження та виявлення дрейфу | Пряма |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | Доставка на основі витягування між кластерами | Пряма |
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Декларативна конфігурація, керування станом | Пряма |
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | Узгодження на основі витягування на практиці (Application CRD, політики синхронізації) | Пряма |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | Узгодження на основі витягування з 5 контролерами | Пряма |

---

## Домен 3: Пов'язані практики (16%)

### Компетенції
- Конфігурація як код (CaC)
- Інфраструктура як код (IaC)
- Культура та практики DevOps
- Конвеєри CI/CD та їхній зв'язок із GitOps

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Основи IaC, декларативна інфраструктура | Пряма |
| [IaC 6.4](../../platform/disciplines/delivery-automation/iac/module-6.4-iac-at-scale/) | IaC у масштабі, керування конфігурацією | Пряма |
| [IaC 6.2](../../platform/disciplines/delivery-automation/iac/module-6.2-iac-testing/) | Тестування інфраструктурного коду | Допоміжна |
| [IaC 6.3](../../platform/disciplines/delivery-automation/iac/module-6.3-iac-security/) | Безпека в IaC | Допоміжна |
| [Modern DevOps: IaC](../../prerequisites/modern-devops/module-1.1-infrastructure-as-code/) | Огляд IaC для початківців | Допоміжна |
| [Modern DevOps: CI/CD](../../prerequisites/modern-devops/module-1.3-cicd-pipelines/) | Основи конвеєрів CI/CD | Пряма |
| [Modern DevOps: DevSecOps](../../prerequisites/modern-devops/module-1.6-devsecops/) | Культура DevOps/DevSecOps | Допоміжна |
| [DevSecOps 4.3](../../platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd/) | Проєктування конвеєрів CI/CD та інтеграція безпеки | Допоміжна |
| [Cloud Native Ecosystem](../../prerequisites/cloud-native-101/module-1.4-cloud-native-ecosystem/) | Ландшафт CNCF, хмарно-орієнтовані практики | Допоміжна |
| [Dagger](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.1-dagger/) | Сучасне проєктування конвеєрів CI/CD | Допоміжна |
| [Tekton](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.2-tekton/) | CI/CD, орієнтований на K8s | Допоміжна |

---

## Домен 4: Патерни GitOps (20%)

### Компетенції
- Патерни розгортання та випуску (blue-green, canary, rolling)
- Стратегії прогресивної доставки
- Узгодження на основі витягування vs на основі подій
- Стратегії просування між середовищами
- Патерни репозиторіїв (монорепо, полірепо)

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Монорепо vs полірепо, патерн app-of-apps | Пряма |
| [GitOps 3.3](../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/) | Патерни просування між середовищами (dev/staging/prod) | Пряма |
| [GitOps 3.5](../../platform/disciplines/delivery-automation/gitops/module-3.5-secrets/) | Патерни керування секретами в робочих процесах GitOps | Пряма |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | Патерни розгортання на кілька кластерів | Пряма |
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Прогресивна доставка: canary, blue-green, аналітичні запуски | Пряма |
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | ApplicationSet, хвилі синхронізації, гачки, модель на основі витягування | Пряма |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | Узгодження на основі подій, контролер сповіщень | Пряма |
| [Helm & Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Патерни налаштування маніфестів для просування | Пряма |

---

## Домен 5: Інструментарій (14%)

### Компетенції
- Формати маніфестів (YAML, JSON, Helm charts, Kustomize overlays)
- Керування сховищем стану (репозиторії Git)
- Рушії узгодження (ArgoCD, Flux)

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | Application CRD, політики синхронізації, RBAC, ApplicationSet | Пряма |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | GitRepository, HelmRelease, Kustomization, 5 контролерів | Пряма |
| [Helm & Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Helm charts, Kustomize overlays, пакування маніфестів | Пряма |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Git як сховище стану, патерни структури репозиторію | Пряма |
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Інструментарій прогресивної доставки | Пряма |

---

## Стратегія підготовки

```
ШЛЯХ ПІДГОТОВКИ ДО CGOA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1: Основи GitOps (охоплює Домени 1 + 2 = 50% іспиту!)
├── GitOps 3.1 — Що таке GitOps, принципи OpenGitOps
├── IaC 6.1 — Декларативний vs імперативний підхід, бажаний стан
├── GitOps 3.4 — Виявлення дрейфу та узгодження
└── IaC 6.5 — Стратегії виправлення дрейфу

Тиждень 2: Патерни GitOps (Домен 4 = 20%)
├── GitOps 3.2 — Стратегії репозиторіїв (монорепо vs полірепо)
├── GitOps 3.3 — Патерни просування між середовищами
├── GitOps 3.5 — Керування секретами в GitOps
└── GitOps 3.6 — GitOps для кількох кластерів

Тиждень 3: Глибоке занурення в інструменти (Домен 5 = 14%)
├── Модуль ArgoCD (узгодження на основі витягування)
├── Модуль Flux (узгодження на основі подій)
├── Helm & Kustomize (формати маніфестів)
└── Argo Rollouts (прогресивна доставка)

Тиждень 4: Пов'язані практики + Повторення (Домен 3 = 16%)
├── Modern DevOps: Конвеєри CI/CD
├── IaC 6.2-6.4 (тестування, безпека, масштаб)
├── DevSecOps 4.3 (безпека в CI/CD)
└── Повторення всіх доменів, фокус на термінології
```

> **Порада**: Домени 1 і 2 разом складають **50% іспиту** й обидва охоплюються одним набором модулів. Закріпіть принципи OpenGitOps і термінологію в першу чергу — це найвища віддача від часу підготовки.

---

## Поради для іспиту

- **Це теоретичний іспит** — без терміналу, без kubectl. Вам потрібно *розуміти* концепції, а не виконувати їх. Але наші практичні модулі дають глибше розуміння, ніж саме читання.
- **Знайте 4 принципи OpenGitOps напам'ять** — Декларативність, Версіонованість і незмінність, Автоматичне витягування, Постійне узгодження. Очікуйте кількох питань, що перевіряють нюанси кожного з них.
- **Pull vs push — ключова відмінність** — розумійте, чому модель на основі витягування (агент у кластері опитує Git) є способом GitOps, і чим відрізняється модель на основі подій (тригери через вебхуки).
- **ArgoCD vs Flux** — знайте архітектурні відмінності (один контролер vs 5 спеціалізованих контролерів), а не лише те, що обидва «роблять GitOps».
- **Прогресивна доставка — це не те саме, що CI/CD** — canary/blue-green/rolling є стратегіями *випуску*, відокремленими від конвеєра *збірки/тестування*.
- **Декларативність != YAML** — декларативність означає описувати *що*, а не *як*. Іспит може перевіряти цю відмінність.
- **90 хвилин — це щедро** — на ~60 питань із множинним вибором у вас ~1,5 хв на питання. Позначайте й пропускайте все, у чому не впевнені.
- **Прохідний бал 75%** — ви можете пропустити приблизно 1 із 4 питань. Не панікуйте через кілька невідомих.

---

## Аналіз прогалин

Наявна програма Platform Engineering від KubeDojo охоплює переважну більшість тем CGOA. Ось що залишається:

| Тема | Статус | Примітки |
|-------|--------|-------|
| Деталі специфікації OpenGitOps | Повністю охоплено | GitOps 3.1 охоплює всі 4 принципи з офіційної специфікації |
| Відмінність Configuration as Code (CaC) від IaC | Незначна прогалина | Модулі IaC глибоко охоплюють IaC; CaC як окрема концепція (конфігурація застосунку vs інфраструктура) явно не виділена, але неявно охоплена |
| Історія та походження GitOps | Незначна прогалина | GitOps 3.1 ймовірно охоплює походження від Weaveworks/Alexis Richardson, але іспит може питати конкретні історичні деталі |
| Порівняння моделей CD push vs pull | Охоплено | GitOps 3.1 + модулі ArgoCD/Flux порівнюють моделі |
| Формати маніфестів YAML/JSON/Jsonnet | Охоплено | Модуль Helm & Kustomize охоплює YAML та Helm; Jsonnet коротко згадується в модулі Helm/Kustomize |

**Нові модулі не потрібні.** 6 модулів дисципліни GitOps, 4 модулі інструментарію GitOps, 6 модулів IaC та допоміжні модулі передумов/CI-CD забезпечують комплексну підготовку до CGOA.

---

## Пов'язані сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Рівень Associate:
├── KCNA (Cloud Native Associate) — Основи K8s
├── KCSA (Security Associate) — Основи безпеки
└── CGOA (GitOps Associate) ← ВИ ТУТ

Рівень Professional:
├── CKA (K8s Administrator) — Операції з кластером
├── CKAD (K8s Developer) — Розгортання застосунків
├── CKS (K8s Security Specialist) — Посилення безпеки
└── CNPE (Platform Engineer) — Повний набір платформних навичок

Specialist (Очікується):
└── CKNE (K8s Network Engineer) — Просунуті мережі
```

CGOA природно поєднується з KCNA — разом вони охоплюють основи Kubernetes та доставку через GitOps. Якщо ви йдете шляхом Kubestronaut, знання CGOA безпосередньо підтримують CKA (розгортання, випуски) та CNPE (GitOps становить 25% цього іспиту).
