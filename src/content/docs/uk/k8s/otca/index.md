---
title: "OTCA — Сертифікований спеціаліст із OpenTelemetry"
sidebar:
  order: 0
  label: "OTCA"
---
> **Іспит із множинним вибором** | 90 хвилин | Прохідний бал: 75% | $250 USD | **Сертифікація CNCF**

## Огляд

OTCA (OpenTelemetry Certified Associate) підтверджує ваше розуміння концепцій OpenTelemetry, архітектури та екосистеми OTel. На відміну від CKA/CKS, це **іспит на знання** — питання з множинним вибором, а не практичні завдання. Але нехай це вас не вводить в оману: Домен 2 (API та SDK) становить 46% іспиту й вимагає глибокого розуміння TracerProvider, MeterProvider, обробників спанів, стратегій відбору (sampling) та внутрішньої будови поширення контексту.

**KubeDojo охоплює ~90% тем OTCA** через наявні модулі спостережуваності плюс два спеціалізовані модулі OTCA, що охоплюють внутрішню будову конвеєрів SDK та просунуту конфігурацію Collector.

> **OpenTelemetry — другий за активністю проєкт CNCF** після Kubernetes. Якщо ви працюєте зі спостережуваністю в будь-якій ролі, OTCA підтверджує найважливішу навичку: розуміння універсального стандарту телеметрії.

---

## Модулі, специфічні для OTCA

Ці модулі охоплюють області між наявними модулями спостережуваності KubeDojo та вимогами іспиту OTCA:

| № | Модуль | Тема | Охоплені домени |
|---|--------|-------|-----------------|
| 1 | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) | TracerProvider, MeterProvider, обробники спанів, відбір (sampling), поширення контексту | Домен 2 (46%) |
| 2 | [Просунутий OTel Collector](module-1.2-otel-collector-advanced/) | Конвеєри Collector, патерни розгортання, конектори, дистрибутиви | Домен 3 (26%) |

---

## Домени іспиту

| Домен | Вага | Охоплення в KubeDojo |
|--------|--------|-------------------|
| Основи спостережуваності | 18% | Відмінне (4 базові модулі) |
| OTel API та SDK | 46% | Відмінне ([Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) + оглядовий модуль) |
| OTel Collector | 26% | Відмінне ([Просунутий OTel Collector](module-1.2-otel-collector-advanced/) + оглядовий модуль) |
| Екосистема | 10% | Добре (охоплено в кількох модулях) |

---

## Домен 1: Основи спостережуваності (18%)

### Компетенції
- Розуміння трьох стовпів спостережуваності (метрики, логи, трейси)
- Застосування семантичних конвенцій для узгодженої телеметрії
- Розрізнення підходів до інструментування (автоматичне vs ручне)
- Розуміння сигналів та їхніх взаємозв'язків

### Шлях навчання в KubeDojo

**Теорія (почніть тут):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability/) | Що таке спостережуваність? Спостережуваність vs моніторинг | Пряма |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars/) | Метрики, логи, трейси — три стовпи | Пряма |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles/) | Принципи інструментування: автоматичне vs ручне, що вимірювати | Пряма |
| [Observability 3.4](../../platform/foundations/observability-theory/module-3.4-from-data-to-insight/) | Від даних до інсайту | Часткова |

**Інструменти (контекст):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | Огляд архітектури OTel, сигнали, автоінструментування | Пряма |
| [Tracing](../../platform/toolkits/observability-intelligence/observability/module-1.5-tracing/) | Концепції розподіленого трейсингу, Jaeger/Tempo | Пряма |
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Основи метрик, типи метрик, PromQL | Часткова |

### Ключові теми іспиту — додаткове вивчення
- **Семантичні конвенції** — Охоплено в [Глибокому зануренні в OTel SDK](module-1.1-otel-sdk-deep-dive/); доповніть [офіційним довідником semconv](https://opentelemetry.io/docs/specs/semconv/)
- **Взаємозв'язки сигналів** — Зразки (exemplars), що пов'язують метрики з трейсами, охоплено в [Глибокому зануренні в OTel SDK](module-1.1-otel-sdk-deep-dive/)
- **Семантика Resource vs атрибут** — Resource описує сутність, атрибути описують подію — охоплено в [Глибокому зануренні в OTel SDK](module-1.1-otel-sdk-deep-dive/)

---

## Домен 2: OTel API та SDK (46%)

> **Це і є іспит.** Майже половина вашого балу надходить із цього домену. Вам потрібно розуміти архітектуру конвеєра SDK на рівні глибшому, ніж «він збирає телеметрію».

### Компетенції
- Розуміння моделі даних OTel (трейси, метрики, логи, baggage)
- Налаштування TracerProvider, MeterProvider та LoggerProvider
- Розуміння обробників спанів (Simple vs Batch) та їхніх компромісів
- Впровадження стратегій відбору (AlwaysOn, AlwaysOff, TraceIdRatio, ParentBased)
- Робота з поширенням контексту (W3C TraceContext, B3, Baggage)
- Розуміння інструментів метрик (Counter, Histogram, Gauge, UpDownCounter)
- Налаштування експортерів та конвеєрів SDK
- Використання агента OTel для автоінструментування

### Шлях навчання в KubeDojo

**Наявне охоплення:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | Огляд OTel SDK, основи автоінструментування | Часткова |
| [Tracing](../../platform/toolkits/observability-intelligence/observability/module-1.5-tracing/) | Спани, контекст трейсу, основи поширення | Часткова |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles/) | Теорія та принципи інструментування | Часткова |
| [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) | TracerProvider, MeterProvider, обробники спанів, відбір, поширення контексту, інструменти метрик | Пряма |

### Ключові теми іспиту — тепер охоплені

Усе нижченаведене охоплено в [Глибокому зануренні в OTel SDK](module-1.1-otel-sdk-deep-dive/):

- **Конвеєр TracerProvider**: `TracerProvider` -> `SpanProcessor` -> `SpanExporter` — як спани проходять шлях від створення до експорту
- **Конвеєр MeterProvider**: `MeterProvider` -> `MetricReader` -> `MetricExporter` — експорт метрик push vs pull
- **Конвеєр LoggerProvider**: `LoggerProvider` -> `LogRecordProcessor` -> `LogRecordExporter`
- **Обробники спанів**: `SimpleSpanProcessor` (синхронний, для налагодження) vs `BatchSpanProcessor` (асинхронний, для production) — знайте компроміси напам'ять
- **Стратегії відбору**: `AlwaysOnSampler`, `AlwaysOffSampler`, `TraceIdRatioBasedSampler`, `ParentBasedSampler`, відбір на вході (head) vs на виході (tail)
- **Внутрішня будова поширення контексту**: `TextMapPropagator`, `TextMapGetter/Setter`, інжекція/екстракція, композитні пропагатори
- **Інструменти метрик детально**: синхронні (Counter, UpDownCounter, Histogram) та асинхронні (ObservableCounter, ObservableGauge, ObservableUpDownCounter), темпоральність агрегації
- **Зразки (exemplars)**: пов'язування метрик із вибірками трейсів
- **Baggage**: наскрізні дані, що поширюються через контекст (не самі телеметричні дані)
- **Конфігурація SDK**: змінні середовища (`OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES_SAMPLER`), програмна конфігурація vs конфігурація через файли

---

## Домен 3: OTel Collector (26%)

### Компетенції
- Розуміння архітектури Collector та патернів розгортання
- Налаштування приймачів (receivers), обробників (processors) та експортерів (exporters)
- Побудова конвеєрів для трейсів, метрик і логів
- Розгортання Collector як агента (DaemonSet) vs шлюзу (Deployment)
- Розуміння дистрибутивів Collector (core vs contrib)

### Шлях навчання в KubeDojo

**Наявне охоплення:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | Огляд Collector, основи receiver/processor/exporter | Часткова |
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Контекст приймача/експортера Prometheus | Часткова |
| [Tracing](../../platform/toolkits/observability-intelligence/observability/module-1.5-tracing/) | Концепції конвеєра трейсів | Часткова |
| [Просунутий OTel Collector](module-1.2-otel-collector-advanced/) | Конфігурація конвеєрів, патерни розгортання, конектори, дистрибутиви, обробники | Пряма |

### Ключові теми іспиту — тепер охоплені

Усе нижченаведене охоплено в [Просунутому OTel Collector](module-1.2-otel-collector-advanced/):

- **Глибоке занурення в конфігурацію Collector**: повний YAML конвеєра (receivers, processors, exporters, service.pipelines)
- **Патерни розгортання**: Агент (sidecar/DaemonSet) vs Шлюз (Deployment) — коли використовувати кожен
- **Дистрибутиви Collector**: `otelcol` (core) vs `otelcol-contrib` (200+ компонентів) vs власні збірки через `ocb` (OpenTelemetry Collector Builder)
- **Ключові обробники (processors)**: `batch`, `memory_limiter`, `filter`, `attributes`, `resource`, `tail_sampling`, `transform`
- **Компонент конектор (connector)**: з'єднує два конвеєри (напр., конектор `spanmetrics` генерує RED-метрики з трейсів)
- **Протокол OTLP**: транспорти gRPC та HTTP/protobuf
- **OTel Operator для Kubernetes**: впровадження автоінструментування, керування CRD Collector
- **Справність і спостережуваність**: власні метрики Collector, розширення `zpages`, розширення перевірки справності

---

## Домен 4: Екосистема (10%)

### Компетенції
- Розуміння статусу проєкту OpenTelemetry та рівнів зрілості
- Знання стабільності сигналів (трейси = стабільні, метрики = стабільні, логи = стабільні, профілювання = у розробці)
- Розуміння OTLP (OpenTelemetry Protocol) та його ролі
- Знання зв'язку між OTel та CNCF
- Розуміння інтеграцій із бекендами та вендорної нейтральності

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | Огляд проєкту OTel, статус у CNCF, архітектура | Пряма |
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability/) | Ландшафт та еволюція спостережуваності | Часткова |
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Prometheus як бекенд метрик OTel | Часткова |
| [Tracing](../../platform/toolkits/observability-intelligence/observability/module-1.5-tracing/) | Jaeger/Tempo як бекенди трейсів OTel | Часткова |
| [Continuous Profiling](../../platform/toolkits/observability-intelligence/observability/module-1.9-continuous-profiling/) | Сигнал профілювання (найновіше доповнення) | Часткова |

### Ключові теми іспиту — примітки щодо охоплення

- **Деталі протоколу OTLP** — Охоплено в [Просунутому OTel Collector](module-1.2-otel-collector-advanced/) (транспорти gRPC, HTTP/protobuf, OTLP/JSON)
- **OpenTelemetry Operator для Kubernetes** — Охоплено в [Просунутому OTel Collector](module-1.2-otel-collector-advanced/) (впровадження автоінструментування, CRD Collector)
- **Модель зрілості сигналів** — Доповніть [сторінкою статусу OTel](https://opentelemetry.io/status/); трейси/метрики/логи = стабільні, профілювання = у розробці
- **Структура спільноти** — SIGи, мовні SIGи, SIG Collector, процес специфікації; ознайомтеся з [документами спільноти OTel](https://opentelemetry.io/community/)
- **Гарантії сумісності** — Що означає «стабільний» для API vs SDK vs компонентів Collector; ознайомтеся зі [специфікацією версіонування OTel](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/)

---

## Стратегія підготовки

```
ШЛЯХ ПІДГОТОВКИ ДО OTCA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1: Основи спостережуваності (Домен 1 — 18%)
├── Observability Theory 3.1-3.4 (наявні модулі KubeDojo)
├── Ознайомтеся з семантичними конвенціями: https://opentelemetry.io/docs/specs/semconv/
└── Зрозумійте типи сигналів та їхні взаємозв'язки

Тиждень 2-3: OTel API та SDK (Домен 2 — 46%!)
├── Модуль OTel 1.2 (наявний огляд KubeDojo)
├── Документація OTel: https://opentelemetry.io/docs/concepts/
├── Вивчіть конвеєри TracerProvider/MeterProvider/LoggerProvider
├── Практика: інструментуйте простий застосунок вашою улюбленою мовою
├── Глибоке занурення: стратегії відбору (ParentBased поверх TraceIdRatio)
├── Глибоке занурення: поширення контексту (заголовки W3C TraceContext)
└── Запам'ятайте: параметри конфігурації через змінні середовища

Тиждень 4: OTel Collector (Домен 3 — 26%)
├── Розгорніть Collector локально (Docker або K8s)
├── Побудуйте конвеєри: receivers -> processors -> exporters
├── Практика: патерни розгортання agent vs gateway
├── Налаштуйте: обробники batch, memory_limiter, filter
├── Знайте: дистрибутиви core vs contrib, збирач ocb
└── Вивчіть компонент конектор (spanmetrics, count)

Тиждень 5: Екосистема + Повторення (Домен 4 — 10%)
├── Прочитайте сторінки статусу проєкту OTel
├── Зрозумійте протокол OTLP (транспорти gRPC + HTTP)
├── Повторіть OpenTelemetry Operator для Kubernetes
├── Практичні питання іспиту (див. ресурси нижче)
└── Фінальне повторення: зосередьте 60% часу на Домені 2 + Домені 3
```

---

## Поради для іспиту

- **Домен 2 — це майже половина іспиту** — ви не складете без ґрунтовних знань SDK. Розумійте патерн конвеєра provider/processor/exporter для всіх трьох типів сигналів.
- **Знайте конфігурацію** — змінні середовища, такі як `OTEL_SERVICE_NAME`, `OTEL_TRACES_SAMPLER`, `OTEL_EXPORTER_OTLP_ENDPOINT`, активно перевіряються.
- **Розумійте компроміси відбору** — відбір на вході (head, на боці SDK, дешевший) vs відбір на виході (tail, на боці Collector, розумніший, але потребує всіх спанів).
- **Конфігурація Collector — це YAML** — знайте структуру: `receivers`, `processors`, `exporters`, `connectors`, `extensions`, `service.pipelines`.
- **Не плутайте API та SDK** — API визначає інтерфейси (безпечні для бібліотек), SDK їх реалізує (налаштовується застосунками). Бібліотеки використовують API; застосунки конфігурують SDK.
- **Baggage — це НЕ телеметрія** — це поширення контексту для даних застосунку, а не даних спостережуваності. Цю відмінність часто перевіряють.
- **Вивчайте специфікацію** — іспит перевіряє концепції OTel, а не конкретні мовні реалізації. Зосередьтеся на мовно-незалежній специфікації.

---

## Аналіз прогалин

Модулі спостережуваності KubeDojo плюс два спеціалізовані модулі OTCA тепер забезпечують комплексне охоплення всіх чотирьох доменів.

| Тема | Статус | Примітки |
|-------|--------|-------|
| Три стовпи / теорія спостережуваності | Охоплено | Наявні базові модулі 3.1-3.4 |
| Семантичні конвенції | Охоплено | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) |
| Конвеєри TracerProvider / MeterProvider | Охоплено | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) |
| Обробники спанів (Simple vs Batch) | Охоплено | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) |
| Стратегії відбору (head vs tail) | Охоплено | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) |
| Внутрішня будова поширення контексту | Охоплено | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) |
| Інструменти метрик (синхронні vs асинхронні) | Охоплено | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) |
| Зразки (exemplars) | Охоплено | [Глибоке занурення в OTel SDK](module-1.1-otel-sdk-deep-dive/) |
| Глибоке занурення в конфігурацію Collector | Охоплено | [Просунутий OTel Collector](module-1.2-otel-collector-advanced/) |
| Патерни розгортання Collector | Охоплено | [Просунутий OTel Collector](module-1.2-otel-collector-advanced/) |
| Конектори Collector | Охоплено | [Просунутий OTel Collector](module-1.2-otel-collector-advanced/) |
| Деталі протоколу OTLP | Охоплено | [Просунутий OTel Collector](module-1.2-otel-collector-advanced/) |
| OTel Operator для Kubernetes | Охоплено | [Просунутий OTel Collector](module-1.2-otel-collector-advanced/) |
| Рівні зрілості сигналів | Незначна прогалина | Див. [сторінку статусу OTel](https://opentelemetry.io/status/) для актуальних рівнів зрілості сигналів |

---

## Основні навчальні ресурси

- **Документація OpenTelemetry**: [opentelemetry.io/docs](https://opentelemetry.io/docs/) — основне джерело істини
- **Специфікація OTel**: [github.com/open-telemetry/opentelemetry-specification](https://github.com/open-telemetry/opentelemetry-specification) — іспит перевіряє концепції специфікації
- **Документація OTel Collector**: [opentelemetry.io/docs/collector](https://opentelemetry.io/docs/collector/)
- **Семантичні конвенції**: [opentelemetry.io/docs/specs/semconv](https://opentelemetry.io/docs/specs/semconv/)
- **Сторінка CNCF OTCA**: [training.linuxfoundation.org](https://training.linuxfoundation.org/) — офіційні деталі іспиту

---

## Пов'язані сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Напрям спостережуваності:
├── KCNA (Cloud Native Associate) — включає основи спостережуваності
├── OTCA (OTel Certified Associate) ← ВИ ТУТ
└── Майбутнє: Просунута сертифікація OTel (TBD)

Доповнювальні сертифікації:
├── CKA (K8s Administrator) — розгортання та керування стеками спостережуваності
├── CNPE (Platform Engineer) — 20% спостережуваність та операції
└── PCA (Prometheus Certified Associate) — глибока експертиза метрик

Рекомендований порядок:
  KCNA → OTCA → PCA → CKA → CNPE
```

OTCA природно поєднується з PCA (Prometheus Certified Associate) — разом вони охоплюють повний конвеєр метрик від інструментування (OTel) до зберігання та запитів (Prometheus/PromQL). Якщо ви завершили модулі інструментарію спостережуваності KubeDojo, ви маєте фору в обох.
