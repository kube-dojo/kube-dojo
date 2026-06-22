---
title: "CNPA — Certified Cloud Native Platform Engineering Associate"
sidebar:
  order: 1
  label: "CNPA"
revision_pending: false
en_commit: "f5818b32b6fe612e822ee4ff03ddeac95606e7ff"
en_file: "src/content/docs/k8s/cnpa/index.md"
calque_review:
  reviewed_at: "2026-06-22"
  detector_version: "v2"
  status: "reviewed"
  flags_resolved: 1
  content_sha: "0bf30c9bd21522d7231858b98b9734627eee9935b5b294bcc1afeea76b402d76"
---
> **Іспит із варіантами відповідей** | 120 хвилин | Прохідний бал: 75% | $250 USD

## Огляд

CNPA (Certified Cloud Native Platform Engineering Associate) підтверджує базові знання концепцій, практик та інструментів платформної інженерії в хмарній екосистемі. Це **іспит із варіантами відповідей** — вам потрібно розуміти концепції, а не налаштовувати живі кластери.

**KubeDojo охоплює ~80%+ тем CNPA** через наш наявний напрямок платформної інженерії. Ця сторінка зіставляє домени CNPA з наявними модулями, щоб ви могли підготуватися ефективно.

> **CNPA — це супутник CNPE рівня associate.** Якщо CNPE — це «доведи, що ти вмієш будувати платформу», то CNPA — це «доведи, що ти розумієш, що таке платформа і чому вона важлива». Спершу складіть CNPA, а потім переходьте до практичного CNPE.

---

## Модулі для підготовки до іспиту

| # | Модуль |
|---|--------|
| 1.1 | [Стратегія іспиту CNPA та огляд програми](./module-1.1-exam-strategy-and-blueprint-review/) |
| 1.2 | [Огляд основних засад платформи для CNPA](./module-1.2-core-platform-fundamentals-review/) |
| 1.3 | [Огляд доставки, API та спостережуваності для CNPA](./module-1.3-delivery-apis-and-observability-review/) |
| 1.4 | [Практичні питання CNPA, набір 1](./module-1.4-practice-questions-set-1/) |
| 1.5 | [Практичні питання CNPA, набір 2](./module-1.5-practice-questions-set-2/) |

---

## Домени іспиту

| Домен | Вага | Покриття KubeDojo |
|--------|--------|-------------------|
| Основні засади платформної інженерії | 36% | Відмінне (6 модулів дисципліни + 6 GitOps + 7 із набору інструментів) |
| Спостережуваність, безпека та відповідність платформи | 20% | Відмінне (4 модулі основ + 5 дисципліни + 10 із набору інструментів) |
| Безперервна доставка та платформна інженерія | 16% | Відмінне (6 модулів дисципліни + 7 із набору інструментів) |
| API платформи та надання інфраструктури | 12% | Відмінне (6 модулів дисципліни + 5 із набору інструментів) |
| IDP та досвід розробника | 8% | Відмінне (6 модулів дисципліни + 6 із набору інструментів) |
| Вимірювання вашої платформи | 8% | Добре (7 модулів дисципліни SRE + 2 із набору інструментів) |

---
## Домен 1: Основні засади платформної інженерії (36%)

### Компетенції
- Декларативне керування ресурсами
- Принципи та культура DevOps
- Середовища застосунків та їхній життєвий цикл
- Концепції архітектури платформи
- Безперервна інтеграція та безперервна доставка
- Засади GitOps

### Навчальний шлях KubeDojo

**Платформна інженерія (почніть звідси):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Platform Eng 2.1](../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/) | Що таке платформна інженерія? | Пряма |
| [Platform Eng 2.2](../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) | Досвід розробника (DevEx) | Пряма |
| [Platform Eng 2.3](../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/) | Внутрішні платформи розробника | Пряма |
| [Platform Eng 2.4](../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) | Золоті шляхи та второвані маршрути | Пряма |
| [Platform Eng 2.5](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/) | Самообслуговувана інфраструктура | Пряма |
| [Platform Eng 2.6](../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/) | Моделі зрілості платформи | Пряма |

**GitOps:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | Що таке GitOps? 4 принципи OpenGitOps | Пряма |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Стратегії репозиторіїв, моно- проти мульти-репозиторію | Пряма |
| [GitOps 3.3](../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/) | Патерни просування між середовищами | Пряма |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Виявлення дрейфу конфігурації та узгодження | Пряма |
| [GitOps 3.5](../../platform/disciplines/delivery-automation/gitops/module-3.5-secrets/) | Керування секретами в GitOps | Пряма |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | Мультикластерний GitOps | Пряма |

**Архітектура та IaC:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Distributed Systems 5.1](../../platform/foundations/distributed-systems/module-5.1-what-makes-systems-distributed/) | Засади розподілених систем | Пряма |
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Засади інфраструктури як коду | Пряма |
| [Systems Thinking 1.1](../../platform/foundations/systems-thinking/module-1.1-what-is-systems-thinking/) | Системне мислення для проєктування платформи | Часткова |

**Інструменти (концептуальне розуміння):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | ArgoCD: доставка через GitOps | Пряма |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | Flux CD: контролери GitOps | Пряма |
| [Helm & Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Декларативне пакування та кастомізація | Пряма |
| [Dagger](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.1-dagger/) | Проєктування конвеєра CI/CD | Пряма |
| [Tekton](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.2-tekton/) | Нативні для K8s конвеєри CI/CD | Пряма |
| [Argo Workflows](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.3-argo-workflows/) | Автоматизація робочих процесів | Пряма |
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Поступова доставка: canary, blue-green | Пряма |

---
## Домен 2: Спостережуваність, безпека та відповідність платформи (20%)

### Компетенції
- Засади спостережуваності (метрики, логи, трейси)
- Патерни безпечної комунікації
- Рушії політик та контролери допуску
- Концепції безпеки Kubernetes
- Безпека конвеєра CI/CD

### Навчальний шлях KubeDojo

**Теорія спостережуваності:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability/) | Що таке спостережуваність? | Пряма |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars/) | Метрики, логи, трейси | Пряма |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles/) | Принципи інструментування | Пряма |
| [Observability 3.4](../../platform/foundations/observability-theory/module-3.4-from-data-to-insight/) | Від даних до висновків | Пряма |

**Безпека:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Security 4.1](../../platform/foundations/security-principles/module-4.1-security-mindset/) | Мислення безпеки | Пряма |
| [Security 4.2](../../platform/foundations/security-principles/module-4.2-defense-in-depth/) | Багаторівневий захист | Пряма |
| [Security 4.3](../../platform/foundations/security-principles/module-4.3-identity-and-access/) | Керування ідентифікацією та доступом | Пряма |
| [DevSecOps 4.1](../../platform/disciplines/reliability-security/devsecops/module-4.1-devsecops-fundamentals/) | Засади DevSecOps | Пряма |
| [DevSecOps 4.3](../../platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd/) | Безпека в CI/CD | Пряма |

**Інструменти (знайте, що вони роблять):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Моніторинг на основі pull, PromQL | Пряма |
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | OTel Collector, автоінструментування | Пряма |
| [Grafana](../../platform/toolkits/observability-intelligence/observability/module-1.3-grafana/) | Дашборди, джерела даних | Пряма |
| [Loki](../../platform/toolkits/observability-intelligence/observability/module-1.4-loki/) | Агрегація логів, LogQL | Пряма |
| [Tracing](../../platform/toolkits/observability-intelligence/observability/module-1.5-tracing/) | Jaeger/Tempo, поширення контексту | Пряма |
| [OPA/Gatekeeper](../../platform/toolkits/security-quality/security-tools/module-4.2-opa-gatekeeper/) | Рушій політик, контроль допуску | Пряма |
| [Kyverno](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | Нативний для YAML рушій політик | Пряма |
| [SPIFFE/SPIRE](../../platform/toolkits/security-quality/security-tools/module-4.8-spiffe-spire/) | Ідентифікація робочих навантажень, mTLS | Пряма |
| [Service Mesh](../../platform/toolkits/infrastructure-networking/networking/module-5.2-service-mesh/) | mTLS у Istio/Linkerd | Пряма |
| [CKA RBAC](../../k8s/cka/part1-cluster-architecture/module-1.6-rbac/) | Засади RBAC | Пряма |

---
## Домен 3: Безперервна доставка та платформна інженерія (16%)

### Компетенції
- Концепції та проєктування CI-конвеєра
- Реагування на інциденти та керування ними
- Основи та робочі процеси GitOps

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | Що таке GitOps? Принципи OpenGitOps | Пряма |
| [GitOps 3.3](../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/) | Патерни просування між середовищами | Пряма |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Виявлення дрейфу конфігурації та узгодження | Пряма |
| [SRE 1.5](../../platform/disciplines/core-platform/sre/module-1.5-incident-management/) | Керування інцидентами | Пряма |
| [SRE 1.6](../../platform/disciplines/core-platform/sre/module-1.6-postmortems/) | Безвинні розбори інцидентів | Пряма |
| [DevSecOps 4.2](../../platform/disciplines/reliability-security/devsecops/module-4.2-shift-left-security/) | Зсув ліворуч (інтеграція з CI) | Часткова |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | ArgoCD: CRD Application, синхронізація, RBAC | Пряма |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | Flux CD: GitRepository, HelmRelease | Пряма |
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Стратегії поступової доставки | Пряма |
| [Dagger](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.1-dagger/) | Проєктування конвеєра CI/CD | Пряма |
| [Tekton](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.2-tekton/) | Нативні для K8s конвеєри CI/CD | Пряма |
| [Argo Workflows](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.3-argo-workflows/) | Автоматизація робочих процесів | Пряма |
| [Supply Chain](../../platform/toolkits/security-quality/security-tools/module-4.4-supply-chain/) | Sigstore/Cosign, підписування образів | Часткова |

---

## Домен 4: API платформи та надання інфраструктури (12%)

### Компетенції
- Патерн циклу узгодження
- Custom Resource Definitions (CRD)
- Провізіювання інфраструктури як коду
- Оператори Kubernetes

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Platform Eng 2.5](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/) | Самообслуговувана інфраструктура | Пряма |
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Інфраструктура як код | Пряма |
| [IaC 6.4](../../platform/disciplines/delivery-automation/iac/module-6.4-iac-at-scale/) | IaC у масштабі | Пряма |
| [Distributed Systems 5.2](../../platform/foundations/distributed-systems/module-5.2-consensus-and-coordination/) | Консенсус та координація (узгодження) | Часткова |
| [CKA CRDs](../../k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/) | Створення CRD та патерн оператора | Пряма |
| [CKA Extension Interfaces](../../k8s/cka/part1-cluster-architecture/module-1.2-extension-interfaces/) | Точки розширення K8s | Пряма |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Crossplane](../../platform/toolkits/infrastructure-networking/platforms/module-7.2-crossplane/) | XRD, Compositions, Providers | Пряма |
| [Kubebuilder](../../platform/toolkits/infrastructure-networking/platforms/module-3.4-kubebuilder/) | Створення власних операторів | Пряма |
| [Cluster API](../../platform/toolkits/infrastructure-networking/platforms/module-3.5-cluster-api/) | Декларативний життєвий цикл кластера | Пряма |
| [Helm & Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Декларативне пакування ресурсів | Часткова |
| [vCluster](../../platform/toolkits/infrastructure-networking/platforms/module-3.6-vcluster/) | Віртуальні кластери для надання інфраструктури | Часткова |

---
## Домен 5: IDP та досвід розробника (8%)

### Компетенції
- Каталоги сервісів та шаблони програмного забезпечення
- Портали розробника
- AI/ML в автоматизації платформи

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Platform Eng 2.2](../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) | Досвід розробника (DevEx) | Пряма |
| [Platform Eng 2.3](../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/) | Внутрішні платформи розробника | Пряма |
| [Platform Eng 2.4](../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) | Золоті шляхи та шаблони | Пряма |
| [Platform Eng 2.6](../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/) | Моделі зрілості платформи | Пряма |
| [AIOps 6.1](../../platform/disciplines/data-ai/aiops/module-6.1-aiops-foundations/) | Засади AIOps | Пряма |
| [AIOps 6.6](../../platform/disciplines/data-ai/aiops/module-6.6-auto-remediation/) | Автовиправлення за допомогою AI | Часткова |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Backstage](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Каталог ПЗ, шаблони, TechDocs | Пряма |
| [K9s CLI](../../platform/toolkits/developer-experience/devex-tools/module-8.1-k9s-cli/) | Інструменти CLI для розробника | Часткова |
| [Telepresence/Tilt](../../platform/toolkits/developer-experience/devex-tools/module-8.2-telepresence-tilt/) | Розробка у внутрішньому циклі | Часткова |
| [DevPod](../../platform/toolkits/developer-experience/devex-tools/module-8.4-devpod/) | Відтворювані середовища розробки | Часткова |
| [Gitpod/Codespaces](../../platform/toolkits/developer-experience/devex-tools/module-8.5-gitpod-codespaces/) | Хмарні середовища розробки | Часткова |
| [AIOps Tools](../../platform/toolkits/observability-intelligence/aiops-tools/module-10.3-observability-ai-features/) | Можливості спостережуваності на основі AI | Часткова |

---

## Домен 6: Вимірювання вашої платформи (8%)

### Компетенції
- Метрики DORA (частота розгортань, час від коміту до релізу, MTTR, частка невдалих змін)
- Метрики ефективності та впровадження платформи
- SLO та бюджети помилок для платформ

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [SRE 1.2](../../platform/disciplines/core-platform/sre/module-1.2-slos/) | SLO (SLI, SLA) | Пряма |
| [SRE 1.3](../../platform/disciplines/core-platform/sre/module-1.3-error-budgets/) | Бюджети помилок та швидкість їх вичерпання | Пряма |
| [SRE 1.4](../../platform/disciplines/core-platform/sre/module-1.4-toil-automation/) | Метрики рутинної праці та автоматизації | Пряма |
| [SRE 1.7](../../platform/disciplines/core-platform/sre/module-1.7-capacity-planning/) | Планування потужностей | Часткова |
| [Platform Eng 2.6](../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/) | Моделі зрілості платформи | Пряма |
| [Reliability 2.4](../../platform/foundations/reliability-engineering/module-2.4-measuring-and-improving-reliability/) | Вимірювання надійності | Пряма |
| [Reliability 2.5](../../platform/foundations/reliability-engineering/module-2.5-slos-slis-error-budgets/) | SLO, SLI, бюджети помилок (теорія) | Пряма |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [SLO Tooling](../../platform/toolkits/observability-intelligence/observability/module-1.10-slo-tooling/) | Sloth, Pyrra, дашборди бюджетів помилок | Пряма |
| [FinOps](../../platform/toolkits/developer-experience/scaling-reliability/module-6.4-finops-opencost/) | OpenCost, розподіл витрат, ефективність | Пряма |

---
## Стратегія підготовки

```
ШЛЯХ ПІДГОТОВКИ ДО CNPA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1-2: Основні засади (36% іспиту!)
├── Дисципліна «Платформна інженерія» (6 модулів)
├── Дисципліна GitOps (6 модулів)
├── IaC 6.1 (основи інфраструктури як коду)
└── Distributed Systems 5.1 (концепції архітектури)

Тиждень 3: Спостережуваність, безпека та відповідність (20%)
├── Основи «Теорія спостережуваності» (4 модулі)
├── Основи «Принципи безпеки» (4 модулі)
├── DevSecOps 4.1 + 4.3 (засади + безпека CI/CD)
└── Знайте свої інструменти: Prometheus, OTel, OPA, Kyverno

Тиждень 4: Безперервна доставка (16%)
├── Перегляньте модулі дисципліни GitOps (з тижня 1)
├── SRE 1.5 + 1.6 (реагування на інциденти + розбори)
├── Інструменти конвеєра CI/CD: Dagger, Tekton, Argo Workflows
└── ArgoCD + Flux (концептуальне розуміння)

Тиждень 5: API платформи та IDP (12% + 8%)
├── Модуль CKA «CRD/оператори» (цикл узгодження)
├── Crossplane + Kubebuilder (концептуально)
├── Backstage (каталоги сервісів, портали розробника)
└── AIOps 6.1 (AI/ML в автоматизації)

Тиждень 6: Вимірювання та повторення (8% + підготовка до іспиту)
├── Модулі SRE: SLO, бюджети помилок, рутинна праця
├── Концепції метрик DORA (перегляньте Platform Eng 2.6)
├── FinOps / OpenCost (ефективність платформи)
└── Повний огляд доменів, акцент на 36% основних засад
```

---

## Поради щодо іспиту

- **Це іспит із варіантами відповідей** — зосередьтеся на концептуальному розумінні, а не на практичному налаштуванні
- **Основні засади = 36% іспиту** — насамперед опануйте концепції платформної інженерії, GitOps та принципи DevOps
- **Знайте «чому», а не лише «що»** — розумійте, чому GitOps використовує узгодження на основі pull, чому платформам потрібні золоті шляхи тощо
- **Метрики DORA трапляються всюди** — знайте чотири ключові метрики й те, що вони вимірюють
- **Принципи GitOps** — запам'ятайте чотири принципи OpenGitOps (декларативний, версіонований, автоматизований, узгоджений)
- **Рушії політик** — розумійте OPA проти Kyverno на концептуальному рівні (коли який обирати)
- **Керування часом**: 120 хвилин для іспиту з варіантами відповідей — це щедро. Уважно читайте питання, позначайте ті, у яких сумніваєтеся, і перегляньте їх наприкінці.

---

## Аналіз прогалин

Наш напрямок платформної інженерії охоплює ~85%+ навчальної програми CNPA. Залишкові незначні прогалини:

| Тема | Статус | Примітки |
|-------|--------|-------|
| Впровадження метрик DORA | Покрито | Метрики DORA (частота розгортань, час від коміту до релізу, MTTR, частка невдалих змін) тепер охоплено в модулях дисципліни SRE поряд із SLO та бюджетами помилок |
| Культура та історія DevOps | Незначна прогалина | Модулі Platform Eng припускають контекст DevOps; хмарно-нативні модулі KCNA дають додаткове підґрунтя |
| Життєвий цикл середовища застосунку | Покрито | Розподілено між модулями GitOps про просування середовищ та IaC |

Ці прогалини незначні. 50+ модулів, зіставлених вище, забезпечують всеосяжну підготовку до CNPA.

---

## Пов'язані сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Початковий рівень:
├── KCNA (Cloud Native Associate) — засади K8s
├── KCSA (Security Associate) — засади безпеки
└── CNPA (Platform Engineering Associate) ← ВИ ТУТ

Професійний рівень:
├── CKA (K8s Administrator) — операції з кластером
├── CKAD (K8s Developer) — розгортання застосунків
├── CKS (K8s Security Specialist) — посилення безпеки
└── CNPE (Platform Engineer) — практична платформна інженерія

Спеціаліст (незабаром):
└── CKNE (K8s Network Engineer) — поглиблені мережі
```

CNPA — це природний трамплін до CNPE. CNPA перевіряє ваше концептуальне розуміння платформної інженерії; CNPE перевіряє вашу здатність будувати та експлуатувати платформи на практиці. Якщо ви склали CNPA, продовжуйте з модулями набору інструментів платформи KubeDojo, щоб напрацювати практичні навички для CNPE.
