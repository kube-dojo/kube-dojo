---
title: "CAPA — Certified Argo Project Associate"
slug: uk/k8s/capa
sidebar:
  order: 0
  label: "CAPA"
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/k8s/capa/index.md"
---

> **Іспит у форматі тестів (multiple-choice)** | 90 хвилин | Прохідний бал: 75% | $250 USD | **Сертифікація CNCF**

## Огляд

CAPA (Certified Argo Project Associate) підтверджує знання чотирьох проєктів Argo: Argo Workflows, Argo CD, Argo Rollouts та Argo Events. Це **теоретичний іспит** — тести з декількома варіантами відповідей, що перевіряють ваше розуміння концепцій, архітектури та паттернів використання Argo.

**KubeDojo покриває ~95% тем CAPA** через існуючі модулі toolkit та дисциплін Platform Engineering, а також два спеціалізовані модулі CAPA, що охоплюють просунуті теми Argo Workflows та Argo Events.

> **Проєкт Argo є другим за популярністю серед graduated проєктів CNCF** після самого Kubernetes. Понад 300 організацій використовують Argo у продакшені, включаючи Intuit (його творця), Tesla, Google, Red Hat та GitHub. Розуміння всієї екосистеми Argo — а не лише ArgoCD — стає базовою навичкою для команд платформ Kubernetes.

---

## Домени іспиту

| Домен | Вага | Покриття KubeDojo |
|--------|--------|-------------------|
| Argo Workflows | 36% | Відмінне (модуль toolkit + [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/)) |
| Argo CD | 34% | Відмінне (1 модуль toolkit + 6 модулів дисциплін) |
| Argo Rollouts | 18% | Відмінне (1 спеціалізований модуль toolkit) |
| Argo Events | 12% | Відмінне ([Модуль 1.2: Argo Events — автоматизація на основі подій для Kubernetes](module-1.2-argo-events/)) |

---

## Спеціалізовані модулі CAPA

Ці модулі охоплюють області між існуючим контентом Platform Engineering у KubeDojo та вимогами іспиту CAPA:

| # | Модуль | Тема | Релевантність |
|---|--------|-------|-----------|
| 1 | [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) | Всі 7 типів шаблонів, артефакти, CronWorkflows, мемоїзація, lifecycle hooks | Домен 1 (36%) |
| 2 | [Модуль 1.2: Argo Events — автоматизація на основі подій для Kubernetes](module-1.2-argo-events/) | Архітектура EventSource, Sensor, Trigger, EventBus, автоматизація на основі подій | Домен 4 (12%) |

---

## Домен 1: Argo Workflows (36%)

### Компетенції
- **Розуміти** Workflow CRD та його життєвий цикл
- **Використовувати** всі 7 типів шаблонів (container, script, resource, suspend, DAG, steps, HTTP)
- **Налаштовувати** передачу артефактів між кроками workflow
- **Будувати** структури workflow на основі DAG та кроків (steps)
- **Планувати** запуск workflow за допомогою CronWorkflow
- **Використовувати** параметри, змінні та конфігурації на рівні workflow

### Шлях навчання KubeDojo

**Основний модуль:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Argo Workflows](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.3-argo-workflows/) | Workflow CRD, DAG/steps, шаблони, параметри | Пряма |
| [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) | Всі 7 типів шаблонів, артефакти, CronWorkflows, повторні спроби, мемоїзація | Пряма |

### Додаткові теми для вивчення

Існуючий модуль Argo Workflows добре охоплює архітектуру, DAG, кроки та параметри. Для CAPA переконайтеся, що ви також вивчили:

| Тема | Що потрібно знати | Ресурс для вивчення |
|-------|-------------|----------------|
| **Всі 7 типів шаблонів** | container, script, resource, suspend, DAG, steps, HTTP — коли використовувати кожен з них | [Argo Docs: Templates](https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/#template-types) |
| **Артефакти** | Репозиторії артефактів S3/GCS/MinIO, передача артефактів між кроками, `inputs.artifacts` / `outputs.artifacts` | [Argo Docs: Artifacts](https://argo-workflows.readthedocs.io/en/latest/walk-through/artifacts/) |
| **CronWorkflow** | Синтаксис планування, політики конкурентності, обробка часових поясів | [Argo Docs: CronWorkflows](https://argo-workflows.readthedocs.io/en/latest/cron-workflows/) |
| **WorkflowTemplate** | Шаблони для повторного використання, `templateRef`, рівень кластера порівняно з рівнем простору імен | [Argo Docs: WorkflowTemplates](https://argo-workflows.readthedocs.io/en/latest/workflow-templates/) |
| **Шаблон Resource** | Створення/патчинг ресурсів K8s зсередини workflow | [Argo Docs: Resource Template](https://argo-workflows.readthedocs.io/en/latest/walk-through/kubernetes-resources/) |
| **Стратегії повторних спроб** | `retryStrategy`, експоненціальна затримка (backoff), обробка збоїв вузлів та Pod | [Argo Docs: Retries](https://argo-workflows.readthedocs.io/en/latest/retries/) |

### Ключові концепції для іспиту

```
ARGO WORKFLOWS — 7 ТИПІВ ШАБЛОНІВ
══════════════════════════════════════════════════════════════

container     → Запускає контейнер (найпоширеніший)
script        → контейнер + вбудований скрипт (поле source)
resource      → Створює/патчить ресурси K8s (як kubectl apply)
suspend       → Призупиняє workflow, очікує на ручне підтвердження або завершення часу
dag           → Визначає завдання з графом залежностей
steps         → Визначає послідовні/паралельні групи кроків
http          → Виконує HTTP-запити (додано у v3.4)

ЖИТТЄВИЙ ЦИКЛ WORKFLOW
══════════════════════════════════════════════════════════════
Pending → Running → Succeeded/Failed/Error

ПОТІК АРТЕФАКТІВ
══════════════════════════════════════════════════════════════
Крок A (outputs.artifacts.data) → Репозиторій артефактів (S3/MinIO) → Крок B (inputs.artifacts.data)
```

---

## Домен 2: Argo CD (34%)

### Компетенції
- **Розуміти** Application CRD та його життєвий цикл синхронізації
- **Налаштовувати** політики синхронізації (auto-sync, self-heal, prune)
- **Використовувати** ApplicationSet для розгортання у декількох кластерах/середовищах
- **Впроваджувати** паттерн App-of-Apps
- **Налаштовувати** RBAC за допомогою проєктів та ролей
- **Керувати** розгортанням у декількох кластерах за допомогою Argo CD

### Шлях навчання KubeDojo

**Теорія (почніть звідси):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | Що таке GitOps? 4 принципи OpenGitOps | Пряма |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Стратегії репозиторіїв, моно- чи мульти-репозиторії | Пряма |
| [GitOps 3.3](../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/) | Паттерни просування по середовищах | Пряма |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Виявлення відхилень (drift detection) та узгодження | Пряма |
| [GitOps 3.5](../../platform/disciplines/delivery-automation/gitops/module-3.5-secrets/) | Керування секретами у GitOps | Пряма |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | GitOps у декількох кластерах | Пряма |

**Інструменти (практика):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | Application CRD, політики синхронізації, RBAC, ApplicationSet, App-of-Apps | Пряма |

### Ключові концепції для іспиту

```yaml
ARGO CD APPLICATION CRD
══════════════════════════════════════════════════════════════
apiVersion: argoproj.io/v1alpha1
kind: Application
spec:
  source:       → ЗВІДКИ брати маніфести (Git-репозиторій, Helm-чарт, OCI)
  destination:  → КУДИ розгортати (кластер + простір імен)
  project:      → Межа RBAC (які джерела, призначення та ресурси дозволені)
  syncPolicy:   → ЯК синхронізувати (автоматично/вручну, prune, self-heal)

SYNC STATUS проти HEALTH STATUS
══════════════════════════════════════════════════════════════
Sync:   Synced / OutOfSync        (чи відповідає кластер стану в Git?)
Health: Healthy / Degraded / Progressing / Missing / Suspended

ГЕНЕРАТОРИ APPLICATIONSET (знайте їх усі!)
══════════════════════════════════════════════════════════════
list          → Статичний список кластерів/значень
cluster       → Автоматичне виявлення зареєстрованих кластерів
git           → Генерація застосунків зі структури директорій або файлів
matrix        → Комбінування двох генераторів (декартів добуток)
merge         → Комбінування генераторів з логікою перевизначення
pull-request  → Генерація застосунків з PR (preview-середовища)
scm-provider  → Виявлення репозиторіїв з організацій GitHub/GitLab

ПАТТЕРН APP-OF-APPS
══════════════════════════════════════════════════════════════
Root Application
├── Application: frontend (→ git/apps/frontend)
├── Application: backend  (→ git/apps/backend)
├── Application: database (→ git/apps/database)
└── Application: monitoring (→ git/apps/monitoring)

Один "батьківський" Application керує маніфестами "дочірніх" Application.
Розгортайте цілі платформи за допомогою одного Application.
```

---

## Домен 3: Argo Rollouts (18%)

### Компетенції
- **Налаштовувати** стратегії розгортання canary та blue-green
- **Писати** AnalysisTemplates для автоматичного відкату (rollback)
- **Інтегрувати** з провайдерами керування трафіком (Istio, Nginx, ALB)
- **Розуміти** життєвий цикл Rollout CRD та потік просування (promotion)

### Шлях навчання KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Canary, blue-green, шаблони аналізу, керування трафіком | Пряма |

### Ключові концепції для іспиту

```yaml
ROLLOUT CRD (замінює Deployment)
══════════════════════════════════════════════════════════════
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:                    АБО   blueGreen:
      steps:                          activeService: active-svc
      - setWeight: 10                 previewService: preview-svc
      - pause: {duration: 5m}        autoPromotionEnabled: false
      - analysis:                     prePromotionAnalysis: ...
          templates: [...]            postPromotionAnalysis: ...

CANARY проти BLUE-GREEN
══════════════════════════════════════════════════════════════
Canary:     Поступове перемикання трафіку (10% → 30% → 60% → 100%)
Blue-Green: Повністю паралельне середовище, миттєве перемикання

ANALYSIS TEMPLATES
══════════════════════════════════════════════════════════════
AnalysisTemplate     → Обмежений простором імен, визначає запити метрик
ClusterAnalysisTemplate → Рівня кластера, спільний для різних просторів імен
AnalysisRun          → Екземпляр шаблону (як Job для CronJob)

Провайдери: Prometheus, Datadog, NewRelic, Wavefront, CloudWatch, Web (універсальний)

КЕРУВАННЯ ТРАФІКОМ
══════════════════════════════════════════════════════════════
Без контролера трафіку: Розподіл лише на основі співвідношення Pod
З Istio/Nginx/ALB:   Точне керування відсотком трафіку
```

---

## Домен 4: Argo Events (12%)

### Компетенції
- **Розуміти** архітектуру EventSource, Sensor та Trigger
- **Налаштовувати** джерела подій (webhook, S3, Kafka, GitHub, cron тощо)
- **Писати** Sensors з фільтрами подій та залежностями
- **Запускати** Argo Workflows, ресурси K8s або HTTP-ендпоінти на основі подій

### Шлях навчання KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Модуль 1.2: Argo Events — автоматизація на основі подій для Kubernetes](module-1.2-argo-events/) | Архітектура EventSource, Sensor, EventBus, Trigger, паттерни на основі подій | Пряма |

### Ресурси для вивчення

| Ресурс | Що він охоплює |
|----------|---------------|
| [Argo Events Docs: Concepts](https://argoproj.github.io/argo-events/concepts/architecture/) | Архітектура, EventSource, Sensor, EventBus |
| [Argo Events Docs: EventSource](https://argoproj.github.io/argo-events/eventsources/setup/webhook/) | Налаштування джерел подій |
| [Argo Events Docs: Sensors](https://argoproj.github.io/argo-events/sensors/triggers/argo-workflow/) | Налаштування Trigger, фільтри, залежності |
| [Argo Events Quick Start](https://argoproj.github.io/argo-events/quick_start/) | Практичне налаштування та перший конвеєр подій |

### Ключові концепції для іспиту

```
АРХІТЕКТУРА ARGO EVENTS
══════════════════════════════════════════════════════════════

EventSource → EventBus (NATS/Jetstream/Kafka) → Sensor → Trigger

EventSource:  Підключається до зовнішніх систем, генерує події
EventBus:     Транспортний рівень (за замовчуванням NATS Streaming)
Sensor:       Прослуховує EventBus, оцінює фільтри та залежності
Trigger:      Дія, що виконується при виконанні умов сенсора

ДЖЕРЕЛА ПОДІЙ (знайте основні)
══════════════════════════════════════════════════════════════
webhook       → HTTP-ендпоінт, що отримує POST-запити
github        → Webhooks GitHub (події push, PR, release)
s3            → Сповіщення бакета S3 (створення об'єкта, видалення)
kafka         → Споживач топіка Kafka
calendar/cron → Події за часом (як CronWorkflow, але на основі подій)
sns/sqs       → Сервіси повідомлень AWS
resource      → Зміни ресурсів Kubernetes (watch API)
slack         → Повідомлення/команди Slack
amqp          → Повідомлення RabbitMQ

ЗАЛЕЖНОСТІ ТА ФІЛЬТРИ СЕНСОРА
══════════════════════════════════════════════════════════════
dependencies:
- name: webhook-dep
  eventSourceName: my-webhook
  eventName: example
  filters:
    data:
    - path: body.action        # Фільтр за вмістом події
      type: string
      value: ["opened"]

ТИПИ ТРИГЕРІВ
══════════════════════════════════════════════════════════════
Argo Workflow    → Запуск Workflow (найчастіше в екосистемі Argo)
K8s Object       → Створення/оновлення будь-якого ресурсу K8s
HTTP             → Виклик зовнішнього HTTP-ендпоінта
AWS Lambda       → Виклик функції Lambda
Slack            → Надсилання сповіщення у Slack
Log              → Логування події (для налагодження)

ПОШИРЕНИЙ ПАТТЕРН: GitHub Push → Argo Workflow
══════════════════════════════════════════════════════════════
EventSource (GitHub webhook)
    ↓ подія push
EventBus (NATS)
    ↓
Sensor (фільтри: branch=main)
    ↓
Trigger (запускає Argo Workflow для CI/CD)
```

---

## Стратегія підготовки

```
ШЛЯХ ПІДГОТОВКИ ДО CAPA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1-2: Основи GitOps + Argo CD (34% іспиту!)
├── Модулі дисципліни GitOps 3.1-3.6 (теорія)
├── Модуль toolkit ArgoCD (практика)
├── Фокус: Application CRD, політики синхронізації, ApplicationSet
└── Практика: Розгортання застосунків, налаштування auto-sync та RBAC

Тиждень 3-4: Argo Workflows (36% іспиту!)
├── Модуль toolkit Argo Workflows (практика)
├── Додатково: Всі 7 типів шаблонів (див. ресурси Домену 1)
├── Практика: Побудова DAG, передача артефактів, використання CronWorkflow
└── Поглиблення: WorkflowTemplate, повторні спроби, шаблони ресурсів

Тиждень 5: Argo Rollouts (18%)
├── Модуль toolkit Argo Rollouts (практика)
├── Фокус: Canary проти blue-green, AnalysisTemplate
└── Практика: Розгортання canary з аналізом Prometheus

Тиждень 6: Argo Events (12%) + Повторення
├── Самостійне навчання: Документація Argo Events (див. ресурси Домену 4)
├── Практика: Налаштування конвеєра webhook → sensor → workflow
├── Фокус: Типи EventSource, фільтри Sensor, типи Trigger
└── Перегляд усіх доменів, розв'язання пробних тестів
```

---

## Поради до іспиту

- **Це теоретичний іспит** — терміналу не буде, але практичний досвід допоможе швидше аналізувати питання.
- **Argo Workflows + Argo CD = 70% іспиту** — приділіть цьому найбільше часу.
- **Знайте поля CRD** — іспит перевіряє, чи розумієте ви функцію кожного поля в spec (наприклад, `syncPolicy.automated.selfHeal` проти `syncPolicy.automated.prune`).
- **Типи шаблонів мають значення** — очікуйте питань щодо відмінностей між 7 типами шаблонів Argo Workflows та випадків їхнього використання.
- **Генератори ApplicationSet** — знайте всі типи генераторів та сценарії їхнього використання (особливо list, cluster, git, matrix).
- **AnalysisTemplate проти ClusterAnalysisTemplate** — розумійте різницю в області видимості та коли який використовувати.
- **Архітектура Argo Events** — навіть при вазі 12%, очікуйте 5-6 питань щодо потоку EventSource/Sensor/Trigger.
- **Потрібні базові знання Kubernetes** — CAPA передбачає, що ви знаєте CRD, RBAC, Services та ConfigMaps.

---

## Аналіз прогалин

Існуючі модулі KubeDojo разом із двома спеціалізованими модулями CAPA тепер покривають ~95% навчальної програми CAPA:

| Тема | Домен | Вплив на вагу | Статус | Примітки |
|-------|--------|---------------|--------|-------|
| Argo Events | Домен 4 | 12% | Покрито | [Модуль 1.2: Argo Events — автоматизація на основі подій для Kubernetes](module-1.2-argo-events/) — EventSource, Sensor, EventBus, Triggers |
| Типи шаблонів Argo Workflows (всі 7) | Домен 1 | Частина 36% | Покрито | [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) — всі 7 типів шаблонів |
| Артефакти Argo Workflows | Домен 1 | Частина 36% | Покрито | [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) — налаштування артефактів S3/MinIO |
| CronWorkflow | Домен 1 | Частина 36% | Покрито | [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) — планування, політики конкурентності |
| Exit handlers / lifecycle hooks | Домен 1 | Частина 36% | Покрито | [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) |
| Синхронізація / мемоїзація | Домен 1 | Частина 36% | Покрито | [Модуль 1.1: Advanced Argo Workflows](module-1.1-advanced-argo-workflows/) |

Усі чотири домени Argo тепер повністю охоплені існуючими модулями KubeDojo.

---

## Супутні сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ ARGO ТА GITOPS
══════════════════════════════════════════════════════════════

Рівень Associate:
├── KCNA (Cloud Native Associate) — основи K8s
└── CAPA (Argo Project Associate) ← ВИ ТУТ

Рівень Professional:
├── CKA (K8s Administrator) — адміністрування кластерів
├── CKAD (K8s Developer) — розгортання застосунків
└── CNPE (Platform Engineer) — Platform engineering (багато Argo CD)

Доповнюючі треки KubeDojo:
├── Дисципліна GitOps — теорія, що стоїть за реалізацією Argo
├── Platform Engineering — де місце Argo у загальній картині
└── DevSecOps — безпека у CI/CD (поєднується з Argo Workflows)
```

CAPA підтверджує знання специфіки Argo, тоді як CNPE перевіряє ширші навички Platform Engineering. Якщо ви плануєте отримати обидві, почніть з CAPA — глибокі знання Argo безпосередньо стануть у пригоді в домені GitOps іспиту CNPE (це 25% того іспиту).