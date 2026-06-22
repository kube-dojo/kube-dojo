---
title: "CNPE — Сертифікований інженер хмарних платформ (Certified Cloud Native Platform Engineer)"
sidebar:
  order: 1
  label: "CNPE"
revision_pending: false
en_commit: "f5818b32b6fe612e822ee4ff03ddeac95606e7ff"
en_file: "src/content/docs/k8s/cnpe/index.md"
---
> **Іспит на основі практичних завдань** | 120 хвилин | Прохідний бал: уточнюється | $445 USD | **Запущено в листопаді 2025 року**

## Огляд

Сертифікація CNPE (Certified Cloud Native Platform Engineer) підтверджує навички проєктування, побудови та експлуатації внутрішніх платформ для розробників (Internal Developer Platforms) на базі Kubernetes. Це **практичний іспит** — ви налаштовуватимете реальну інфраструктуру, а не відповідатимете на запитання з варіантами відповідей.

**KubeDojo охоплює ~90% тем CNPE** через наш наявний напрямок Platform Engineering. Ця сторінка зіставляє домени CNPE з наявними модулями, щоб ви могли готуватися ефективно.

> **На відміну від інших сертифікацій**, CNPE НЕ прив'язана до конкретної версії K8s. Вона перевіряє практики інженерії платформ, а не суто навички роботи з kubectl. Уявіть її як «CKA для платформних команд».

---

## Модулі для підготовки до іспиту

| # | Модуль |
|---|--------|
| 1.1 | [Стратегія іспиту CNPE та середовище](./module-1.1-exam-strategy-and-environment/) |
| 1.2 | [Лабораторна CNPE: GitOps і доставка](./module-1.2-gitops-and-delivery-lab/) |
| 1.3 | [Лабораторна CNPE: платформні API та самообслуговування](./module-1.3-platform-apis-and-self-service-lab/) |
| 1.4 | [Лабораторна CNPE: спостережуваність, безпека та експлуатація](./module-1.4-observability-security-and-operations-lab/) |
| 1.5 | [Повний пробний іспит CNPE](./module-1.5-full-mock-exam/) |

---

## Домени іспиту

| Домен | Вага | Покриття KubeDojo |
|--------|--------|-------------------|
| GitOps і безперервна доставка | 25% | Відмінне (6 модулів дисциплін + 7 модулів інструментів) |
| Платформні API та самообслуговування | 25% | Відмінне (6 модулів дисциплін + 4 модулі інструментів) |
| Спостережуваність та експлуатація | 20% | Відмінне (4 базові + 7 дисциплінарних + 10 інструментальних модулів) |
| Архітектура платформи | 15% | Відмінне (7 базових + 3 дисциплінарні модулі) |
| Безпека та політики | 15% | Відмінне (4 базові + 6 дисциплінарних + 6 інструментальних модулів) |

---

## Домен 1: GitOps і безперервна доставка (25%)

### Компетенції
- Впровадження робочих процесів GitOps для розгортання застосунків та інфраструктури
- Побудова та налаштування конвеєрів CI/CD, інтегрованих із Kubernetes
- Розгортання застосунків із застосуванням стратегій прогресивної доставки (blue/green, canary)

### Навчальний шлях KubeDojo

**Теорія (почніть звідси):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | Що таке GitOps? 4 принципи OpenGitOps | Пряма |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Стратегії репозиторіїв, моно- проти мульти-репозиторію | Пряма |
| [GitOps 3.3](../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/) | Патерни просування між середовищами | Пряма |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Виявлення дрейфу та узгодження | Пряма |
| [GitOps 3.5](../../platform/disciplines/delivery-automation/gitops/module-3.5-secrets/) | Керування секретами в GitOps | Пряма |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | Багатокластерний GitOps | Пряма |

**Інструменти (практика):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | ArgoCD: Application CRD, синхронізація, RBAC, ApplicationSet | Пряма |
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Прогресивна доставка: canary, blue-green, аналіз | Пряма |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | Flux CD: 5 контролерів, GitRepository, HelmRelease | Пряма |
| [Helm і Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Пакування та кастомізація | Пряма |
| [Dagger](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.1-dagger/) | Проєктування конвеєрів CI/CD | Пряма |
| [Tekton](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.2-tekton/) | Конвеєри CI/CD, нативні для K8s | Пряма |
| [Argo Workflows](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.3-argo-workflows/) | Автоматизація робочих процесів | Пряма |

---
## Домен 2: Платформні API та самообслуговування (25%)

### Компетенції
- Проєктування та створення CRD для платформних сервісів
- Впровадження надання ресурсів за принципом самообслуговування за допомогою платформних API
- Використання операторів Kubernetes для автоматизації платформи
- Використання фреймворків автоматизації для надання ресурсів за принципом самообслуговування

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Platform Eng 2.1](../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/) | Що таке інженерія платформ? | Пряма |
| [Platform Eng 2.2](../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) | Досвід розробника (DevEx) | Пряма |
| [Platform Eng 2.3](../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/) | Внутрішні платформи для розробників | Пряма |
| [Platform Eng 2.4](../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) | Золоті шляхи та второвані дороги | Пряма |
| [Platform Eng 2.5](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/) | Інфраструктура самообслуговування | Пряма |
| [Platform Eng 2.6](../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/) | Моделі зрілості платформи | Пряма |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Backstage](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Каталог ПЗ, шаблони, TechDocs | Пряма |
| [Crossplane](../../platform/toolkits/infrastructure-networking/platforms/module-7.2-crossplane/) | XRD, композиції, провайдери | Пряма |
| [Kubebuilder](../../platform/toolkits/infrastructure-networking/platforms/module-3.4-kubebuilder/) | Побудова власних операторів | Пряма |
| [Cluster API](../../platform/toolkits/infrastructure-networking/platforms/module-3.5-cluster-api/) | Декларативний життєвий цикл кластера | Пряма |
| [vCluster](../../platform/toolkits/infrastructure-networking/platforms/module-3.6-vcluster/) | Віртуальні кластери для самообслуговування | Пряма |
| [CKA CRDs](../../k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/) | Створення CRD та патерн оператора | Пряма |

---

## Домен 3: Спостережуваність та експлуатація (20%)

### Компетенції
- Впровадження рішень для моніторингу, оповіщення, логування та трейсингу
- Вимірювання ефективності платформи за допомогою метрик розгортання (DORA)
- Діагностика та усунення проблем платформи

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability/) | Що таке спостережуваність? | Пряма |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars/) | Метрики, логи, трейси | Пряма |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles/) | Принципи інструментування | Пряма |
| [SRE 1.1](../../platform/disciplines/core-platform/sre/module-1.1-what-is-sre/) | Що таке SRE? | Пряма |
| [SRE 1.2](../../platform/disciplines/core-platform/sre/module-1.2-slos/) | SLO (SLI, SLA) | Пряма |
| [SRE 1.3](../../platform/disciplines/core-platform/sre/module-1.3-error-budgets/) | Бюджети помилок та швидкість їх вичерпання | Пряма |
| [SRE 1.5](../../platform/disciplines/core-platform/sre/module-1.5-incident-management/) | Керування інцидентами | Пряма |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Моніторинг за моделлю pull, PromQL, ServiceMonitor | Пряма |
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | OTel Collector, автоматичне інструментування | Пряма |
| [Grafana](../../platform/toolkits/observability-intelligence/observability/module-1.3-grafana/) | Дашборди, джерела даних, конфігурування | Пряма |
| [Loki](../../platform/toolkits/observability-intelligence/observability/module-1.4-loki/) | Агрегація логів, LogQL | Пряма |
| [Tracing](../../platform/toolkits/observability-intelligence/observability/module-1.5-tracing/) | Jaeger/Tempo, поширення контексту | Пряма |
| [SLO Tooling](../../platform/toolkits/observability-intelligence/observability/module-1.10-slo-tooling/) | Sloth, Pyrra, дашборди бюджету помилок | Пряма |
| [Continuous Profiling](../../platform/toolkits/observability-intelligence/observability/module-1.9-continuous-profiling/) | Parca, Pyroscope (4-й стовп) | Часткова |
| [FinOps](../../platform/toolkits/developer-experience/scaling-reliability/module-6.4-finops-opencost/) | OpenCost, розподіл витрат, оптимізація розмірів | Пряма |

---
## Домен 4: Архітектура платформи (15%)

### Компетенції
- Застосування найкращих практик для мережі, зберігання та обчислень
- Використання рішень для керування витратами з метою оптимізації розмірів та масштабування
- Оптимізація використання ресурсів за умов багатоорендності

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Systems Thinking 1.1](../../platform/foundations/systems-thinking/module-1.1-what-is-systems-thinking/) | Системне мислення для архітекторів | Часткова |
| [Distributed Systems 5.1](../../platform/foundations/distributed-systems/module-5.1-what-makes-systems-distributed/) | Основи розподілених систем | Пряма |
| [Distributed Systems 5.2](../../platform/foundations/distributed-systems/module-5.2-consensus-and-coordination/) | Консенсус та координація | Пряма |
| [Reliability 2.3](../../platform/foundations/reliability-engineering/module-2.3-redundancy-and-fault-tolerance/) | Резервування та відмовостійкість | Пряма |
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Інфраструктура як код | Пряма |
| [IaC 6.4](../../platform/disciplines/delivery-automation/iac/module-6.4-iac-at-scale/) | IaC у великих масштабах | Пряма |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Karpenter](../../platform/toolkits/developer-experience/scaling-reliability/module-6.1-karpenter/) | Автомасштабування, оптимізація розмірів | Пряма |
| [KEDA](../../platform/toolkits/developer-experience/scaling-reliability/module-6.2-keda/) | Автомасштабування на основі подій | Пряма |
| [FinOps](../../platform/toolkits/developer-experience/scaling-reliability/module-6.4-finops-opencost/) | Керування витратами, OpenCost | Пряма |
| [vCluster](../../platform/toolkits/infrastructure-networking/platforms/module-3.6-vcluster/) | Багатоорендність із віртуальними кластерами | Пряма |
| [Cilium](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/) | Мережа на основі eBPF, політики | Пряма |

---

## Домен 5: Безпека та політики (15%)

### Компетенції
- Налаштування безпечного зв'язку між сервісами
- Застосування RBAC та засобів контролю безпеки
- Формування аудиторських журналів та забезпечення відповідності вимогам (SBOM)
- Використання рушіїв політик та контролерів допуску
- Інтеграція сканування безпеки в конвеєри

### Навчальний шлях KubeDojo

**Теорія:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Security 4.1](../../platform/foundations/security-principles/module-4.1-security-mindset/) | Мислення в категоріях безпеки | Пряма |
| [Security 4.2](../../platform/foundations/security-principles/module-4.2-defense-in-depth/) | Багаторівневий захист | Пряма |
| [DevSecOps 4.1](../../platform/disciplines/reliability-security/devsecops/module-4.1-devsecops-fundamentals/) | Основи DevSecOps | Пряма |
| [DevSecOps 4.2](../../platform/disciplines/reliability-security/devsecops/module-4.2-shift-left-security/) | Безпека за принципом зсуву ліворуч | Пряма |
| [DevSecOps 4.3](../../platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd/) | Безпека в CI/CD | Пряма |
| [DevSecOps 4.4](../../platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/) | Безпека ланцюга постачання, SBOM | Пряма |
| [DevSecOps 4.5](../../platform/disciplines/reliability-security/devsecops/module-4.5-runtime-security/) | Безпека під час виконання | Пряма |

**Інструменти:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [OPA/Gatekeeper](../../platform/toolkits/security-quality/security-tools/module-4.2-opa-gatekeeper/) | Рушій політик (Rego), контроль допуску | Пряма |
| [Kyverno](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | Рушій політик, нативний для YAML | Пряма |
| [Falco](../../platform/toolkits/security-quality/security-tools/module-4.3-falco/) | Виявлення загроз під час виконання | Пряма |
| [Supply Chain](../../platform/toolkits/security-quality/security-tools/module-4.4-supply-chain/) | Sigstore/Cosign, підписування образів, SBOM | Пряма |
| [Vault і ESO](../../platform/toolkits/security-quality/security-tools/module-4.1-vault-eso/) | Керування секретами | Пряма |
| [SPIFFE/SPIRE](../../platform/toolkits/security-quality/security-tools/module-4.8-spiffe-spire/) | Ідентичність робочих навантажень, mTLS | Пряма |
| [Service Mesh](../../platform/toolkits/infrastructure-networking/networking/module-5.2-service-mesh/) | mTLS у Istio/Linkerd | Пряма |

---
## Стратегія підготовки

```
ШЛЯХ ПІДГОТОВКИ ДО CNPE (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1-2: Основи
├── Дисципліна Platform Engineering (6 модулів)
├── Основа Security Principles (4 модулі)
└── Основа Observability Theory (4 модулі)

Тиждень 3-4: GitOps і CD (25% іспиту!)
├── Дисципліна GitOps (6 модулів)
├── Інструментальні модулі ArgoCD + Flux
└── Argo Rollouts (прогресивна доставка)

Тиждень 5-6: Платформні API та самообслуговування (25% іспиту!)
├── Інструментальні модулі Backstage + Crossplane
├── Модуль CKA CRDs/Operators
├── Модуль Kubebuilder (побудуйте оператор)
└── vCluster для багатоорендності

Тиждень 7-8: Спостережуваність та експлуатація (20%)
├── Дисципліна SRE (SLO, бюджети помилок, інциденти)
├── Інструменти Prometheus + OTel + Grafana + Loki
├── SLO Tooling (Sloth/Pyrra)
└── FinOps / OpenCost

Тиждень 9-10: Безпека та політики (15%)
├── Дисципліна DevSecOps (5 модулів)
├── OPA/Gatekeeper + Kyverno
├── Безпека ланцюга постачання (Sigstore/SBOM)
└── SPIFFE/SPIRE + mTLS у Service Mesh

Тиждень 11-12: Архітектура і практика (15%)
├── Основа Distributed Systems
├── Karpenter + KEDA (автомасштабування)
├── Chaos Engineering (тестування стійкості)
└── Пробні вправи, аналог killer.sh
```

---

## Поради щодо іспиту

- **Це практичний іспит** — ви налаштовуватимете реальні кластери, а не відповідатимете на теоретичні запитання
- **Зосередьтеся на ArgoCD та Crossplane** — це найбільш ретельно перевірювані інструменти (GitOps + самообслуговування = 50% іспиту)
- **Знайте свої CRD** — проєктування та створення CRD є базовою навичкою
- **Практикуйте PromQL** — вам доведеться писати запити та створювати оповіщення
- **Політики RBAC + OPA/Kyverno** — безпека перевіряється на реальних сценаріях примусового застосування політик
- **Керування часом**: 120 хвилин на ~15-20 завдань. Закладайте ~6-8 хвилин на завдання.

---

## Аналіз прогалин

Наш напрямок Platform Engineering охоплює ~95%+ навчальної програми CNPE. Решта незначних прогалин:

| Тема | Стан | Примітки |
|-------|--------|-------|
| Argo Events (автоматизація на основі подій) | Охоплено | Див. [Argo Events](../capa/module-1.2-argo-events/) у напрямку CAPA — EventSource, Sensor, EventBus, Triggers |
| Впровадження метрик DORA | Охоплено | Метрики DORA тепер охоплено в модулях дисципліни SRE; SLO та бюджети помилок забезпечують рамки вимірювання |
| Ієрархічні простори імен | Незначна прогалина (нішева тема) | Нішева тема багатоорендності, навряд чи критична для іспиту; модуль vCluster охоплює альтернативи багатоорендності |

Ці прогалини незначні. 60+ модулів, зіставлених вище, забезпечують всебічну підготовку до CNPE.

---

## Суміжні сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Початковий рівень:
├── KCNA (Cloud Native Associate) — основи K8s
├── KCSA (Security Associate) — основи безпеки
└── CNPA (Platform Engineering Associate) — основи платформ

Професійний рівень:
├── CKA (K8s Administrator) — операції з кластером
├── CKAD (K8s Developer) — розгортання застосунків
├── CKS (K8s Security Specialist) — посилення безпеки
└── CNPE (Platform Engineer) ← ВИ ТУТ

Спеціаліст (незабаром):
└── CKNE (K8s Network Engineer) — складна мережа
```

Сертифікація CNPE доповнює CKA/CKS, перевіряючи навички платформного рівня, а не операції на рівні кластера. Якщо ви завершили напрямки CKA + Platform Engineering у KubeDojo, ви добре підготовлені.



