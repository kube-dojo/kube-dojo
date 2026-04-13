---
title: "PCA — Prometheus Certified Associate"
slug: uk/k8s/pca/index
sidebar:
  order: 0
  label: "PCA"
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/k8s/pca/index.md"
---
> **Тест із варіантами відповідей** | 90 хвилин | Прохідний бал: 75% | $250 USD | **Сертифікація CNCF**

## Огляд

PCA (Prometheus Certified Associate) підтверджує ваше розуміння Prometheus, PromQL, інструментування (instrumentation) та ширшої екосистеми моніторингу Prometheus. Це **іспит на знання теорії** — запитання з варіантами відповідей, а не практичні завдання. Але не недооцінюйте його: Домен 3 (PromQL) становить 28% іспиту та вимагає вміння вільно читати, писати та відлагоджувати запити.

**KubeDojo покриває ~95% тем PCA** через існуючі модулі спостережуваності (observability) плюс два спеціалізовані модулі PCA, що детально розглядають глибину PromQL та специфіку інструментування і сповіщень (alerting).

> **Prometheus є стандартом де-факто для метрик у хмарних технологіях.** Створений у SoundCloud у 2012 році, він став другим проєктом CNCF (після Kubernetes), що офіційно завершив етап інкубації (graduated), і є фундаментом, на якому будуються майже всі інші інструменти моніторингу. PCA підтверджує найважливішу навичку спостережуваності: глибоке розуміння Prometheus.

---

## Спеціалізовані модулі PCA

Ці модулі охоплюють прогалини між існуючими модулями спостережуваності KubeDojo та вимогами іспиту PCA:

| # | Модуль | Тема | Покриті домени |
|---|--------|-------|-----------------|
| 1 | [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) | Селектори, rate, агрегація, гістограми, бінарні операції, підзапити, правила запису (recording rules) | Домен 3 (28%) |
| 2 | [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) | Клієнтські бібліотеки, типи метрик, угоди щодо найменувань, експортери, конфігурація Alertmanager | Домен 4 (16%) + Домен 5 (18%) |

---

## Домени іспиту

| Домен | Вага | Покриття KubeDojo |
|--------|--------|-------------------|
| Концепції спостережуваності | 18% | Відмінне (4 базові модулі) |
| Основи Prometheus | 20% | Відмінне (module-1.1-prometheus.md) |
| PromQL | 28% | Відмінне ([Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) + модуль основ) |
| Інструментування та експортери | 16% | Відмінне ([Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/)) |
| Сповіщення та дашборди | 18% | Відмінне ([Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) + модуль Grafana) |

---

## Домен 1: Концепції спостережуваності (18%)

### Компетенції
- **Розуміти** метрики, логи, трасування (traces) та зв'язки між ними
- **Відрізняти** моніторинг від спостережуваності (observability)
- **Розуміти** роль метрик в екосистемі спостережуваності
- **Знати** push та pull моделі та їх компромісів (trade-offs)

### Навчальний шлях KubeDojo

**Теорія (почніть звідси):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability/) | Що таке спостережуваність? Спостережуваність проти моніторингу | Пряма |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars/) | Метрики, логи, трасування — три стовпи | Пряма |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles/) | Принципи інструментування: що та як вимірювати | Пряма |
| [Observability 3.4](../../platform/foundations/observability-theory/module-3.4-from-data-to-insight/) | Від даних до інсайтів — створення дієвих метрик | Пряма |

**Інструменти (контекст):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Pull-модель, архітектура, TSDB, виявлення сервісів (service discovery) | Пряма |
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | OTel як стандарт інструментування, зв'язок із Prometheus | Часткова |

---

## Домен 2: Основи Prometheus (20%)

### Компетенції
- **Розуміти** архітектуру Prometheus (сервер, TSDB, Alertmanager, Pushgateway)
- **Налаштовувати** цілі збору метрик (scrape targets) та виявлення сервісів (service discovery)
- **Розуміти** pull-модель, інтервали збору метрик (scrape intervals) та застарілість (staleness)
- **Працювати** з мітками (labels), перейменуванням міток (relabeling) та метаданими метрик
- **Розгортати** Prometheus у Kubernetes (Operator, ServiceMonitor, PodMonitor)

### Навчальний шлях KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Архітектура, pull-модель, TSDB, виявлення сервісів, розгортання в K8s | Пряма |
| [SRE 1.2](../../platform/disciplines/core-platform/sre/module-1.2-slos/) | SLO та як Prometheus їх реалізує | Пряма |
| [SRE 1.3](../../platform/disciplines/core-platform/sre/module-1.3-error-budgets/) | Бюджети помилок, сповіщення про швидкість вичерпання (burn rate) — Prometheus на практиці | Пряма |

### Основні теми іспиту — Примітки щодо покриття
- **Архітектура Prometheus** — Повністю описана в module-1.1-prometheus.md (pull-модель, TSDB, Alertmanager, Pushgateway)
- **Виявлення сервісів** — Kubernetes SD, ServiceMonitor, PodMonitor, relabel_configs описані в модулі 1.1
- **Конфігурація збору метрик** — scrape_interval, scrape_timeout, honor_labels, metric_relabel_configs описані в модулі 1.1
- **Зберігання** — Внутрішня структура TSDB (blocks, WAL, compaction, retention) описана в модулі 1.1

---

## Домен 3: PromQL (28%)

> **Це найбільший домен.** Більше чверті ваших балів залежить від вільного володіння PromQL. Вам потрібно буде писати запити з нуля, відлагоджувати помилки та розуміти модель обчислення (evaluation model).

### Компетенції
- **Писати** селектори миттєвого вектора (instant vector) та вектора діапазону (range vector) з використанням відповідників міток (label matchers)
- **Правильно використовувати** rate(), irate(), increase() для лічильників (counters)
- **Застосовувати** оператори агрегації (sum, avg, count, topk) з by/without
- **Обчислювати** процентилі за допомогою histogram_quantile()
- **Використовувати** бінарні оператори та зіставлення векторів (on, ignoring, group_left)
- **Писати** правила запису (recording rules) для підвищення продуктивності
- **Розуміти** підзапити (subqueries) та модель обчислення

### Навчальний шлях KubeDojo

**Існуюче покриття:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Основи PromQL: селектори, rate, агрегація, гістограми | Часткова |
| [Інструменти SLO](../../platform/toolkits/observability-intelligence/observability/module-1.10-slo-tooling/) | PromQL для SLO (швидкість вичерпання, бюджети помилок) | Часткова |
| [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) | Повне покриття PromQL: усі типи селекторів, функції швидкості, агрегація, бінарні оператори, histogram_quantile, правила запису, підзапити | Пряма |

### Основні теми іспиту — Тепер покриті

Усе перелічене нижче висвітлено в [Модулі 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/):

- **Типи селекторів**: Миттєві вектори, вектори діапазону, відповідники міток (`=`, `!=`, `=~`, `!~`)
- **Функції швидкості**: `rate()` проти `irate()` проти `increase()` — коли використовувати кожну, обробка скидання лічильника
- **Оператори агрегації**: `sum`, `avg`, `min`, `max`, `count`, `topk`, `bottomk`, `quantile` з `by`/`without`
- **Бінарні оператори**: Арифметичні (`+`, `-`, `*`, `/`), порівняння (`>`, `<`, `==`), логічні (`and`, `or`, `unless`)
- **Зіставлення векторів**: `on()`, `ignoring()`, `group_left()`, `group_right()` для об'єднання метрик
- **Запити до гістограм**: `histogram_quantile()`, вибір кошиків (buckets), поведінка інтерполяції
- **Правила запису**: Угоди щодо найменувань (`level:metric:operations`), коли та навіщо їх використовувати
- **Підзапити**: Синтаксис `metric[range:resolution]`, випадки використання для сповіщень на основі агрегованих даних
- **Модифікатор offset**: Порівняння поточних значень з історичними даними

---

## Домен 4: Інструментування та експортери (16%)

### Компетенції
- **Розуміти** чотири типи метрик (Counter, Gauge, Histogram, Summary)
- **Інструментувати** застосунки за допомогою клієнтських бібліотек (Go, Python, Java)
- **Дотримуватися** угод щодо найменування метрик
- **Використовувати** експортери (node_exporter, blackbox_exporter, власні експортери)
- **Розуміти** формат кінцевої точки /metrics (OpenMetrics, формат експозиції Prometheus)

### Навчальний шлях KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles/) | Що інструментувати, принципи інструментування | Пряма |
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Огляд типів метрик, основи експортерів | Часткова |
| [OpenTelemetry](../../platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry/) | Інструментування за допомогою OTel SDK (додатковий підхід) | Часткова |
| [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) | Клієнтські бібліотеки (Go/Python/Java), угоди щодо найменувань, вибір типу метрики, глибоке занурення в експортери | Пряма |

### Основні теми іспиту — Тепер покриті

Усе перелічене нижче висвітлено в [Модулі 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/):

- **Чотири типи метрик**: Counter (монотонний), Gauge (збільшується/зменшується), Histogram (розподіл із кошиками), Summary (квантилі на стороні клієнта)
- **Коли використовувати який тип**: Структура прийняття рішень для вибору правильного типу метрики
- **Клієнтські бібліотеки**: Go (`prometheus/client_golang`), Python (`prometheus_client`), Java (`simpleclient`) з прикладами коду
- **Угоди щодо найменувань**: `<namespace>_<name>_<unit>_total`, суфікси одиниць виміру, найкращі практики роботи з мітками
- **Експортери**: node_exporter (обладнання/ОС), blackbox_exporter (зондування), власні експортери
- **Формат експозиції**: Текстовий формат Prometheus, формат OpenMetrics, метадані TYPE/HELP/UNIT

---

## Домен 5: Сповіщення та дашборди (18%)

### Компетенції
- **Налаштовувати** Alertmanager (дерево маршрутизації, отримувачі, пригнічення (inhibition), заглушення (silencing))
- **Писати** правила сповіщень із відповідними порогами та тривалістю `for`
- **Розуміти** стани сповіщень (pending, firing, resolved)
- **Створювати** ефективні дашборди у Grafana
- **Використовувати** правила запису для оптимізації запитів дашбордів

### Навчальний шлях KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Основи правил сповіщень, огляд Alertmanager | Часткова |
| [Grafana](../../platform/toolkits/observability-intelligence/observability/module-1.3-grafana/) | Дашборди, джерела даних, провізіонінг, змінні | Пряма |
| [SRE 1.2](../../platform/disciplines/core-platform/sre/module-1.2-slos/) | Філософія сповіщень на основі SLO | Пряма |
| [SRE 1.3](../../platform/disciplines/core-platform/sre/module-1.3-error-budgets/) | Сповіщення про швидкість вичерпання бюджету помилок | Пряма |
| [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) | Маршрутизація Alertmanager, отримувачі, пригнічення, заглушення, правила запису, патерни правил сповіщень | Пряма |

### Основні теми іспиту — Тепер покриті

- **Дерево маршрутизації Alertmanager** — Описано в [Модулі 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/): ієрархія маршрутів, `match`/`match_re`, `continue`, `group_by`
- **Отримувачі (Receivers)** — Налаштування Slack, PagerDuty, email, webhook
- **Правила пригнічення (Inhibition rules)** — Придушення залежних сповіщень при спрацюванні кореневого сповіщення
- **Заглушення (Silences)** — Тимчасове вимкнення сповіщень під час технічного обслуговування
- **Стани сповіщень** — Життєвий цикл `inactive` -> `pending` -> `firing` -> `resolved`
- **Правила запису (Recording rules)** — Угода щодо найменувань, коли використовувати, оптимізація продуктивності
- **Дашборди Grafana** — Описано в існуючому [модулі Grafana](../../platform/toolkits/observability-intelligence/observability/module-1.3-grafana/)

---

## Стратегія навчання

```
ШЛЯХ ПІДГОТОВКИ ДО PCA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1: Основи спостережуваності (Домен 1 — 18%)
├── Теорія спостережуваності 3.1-3.4 (існуючі модулі KubeDojo)
├── Розуміння метрик проти логів проти трасування
└── Досконале знання переваг та недоліків push та pull моделей

Тиждень 2: Основи Prometheus (Домен 2 — 20%)
├── Модуль Prometheus 1.1 (існуючий модуль KubeDojo)
├── Розгортання Prometheus у kind/minikube
├── Налаштування цілей збору, ServiceMonitor, PodMonitor
├── Розуміння внутрішньої структури TSDB (WAL, blocks, compaction)
└── Практика з relabel_configs

Тиждень 3-4: PromQL (Домен 3 — 28%!)
├── Модуль 1.1: Глибоке занурення в PromQL
├── Практика написання 20+ запитів на живому екземплярі Prometheus
├── Опанування rate() проти irate() проти increase()
├── Знання операторів агрегації з by/without
├── Практика з histogram_quantile() з різними конфігураціями кошиків
├── Розуміння бінарних операторів та зіставлення векторів
└── Написання правил запису

Тиждень 5: Інструментування та експортери (Домен 4 — 16%)
├── Модуль 1.2: Інструментування та сповіщення
├── Інструментування простого застосунку на Go або Python
├── Розгортання node_exporter, blackbox_exporter
├── Запам'ятовування угод щодо найменувань
└── Знання всіх чотирьох типів метрик та випадків їх використання

Тиждень 6: Сповіщення та дашборди (Домен 5 — 18%)
├── Модуль 1.2: Інструментування та сповіщення (розділи про сповіщення)
├── Модуль Grafana 1.3 (існуючий модуль KubeDojo)
├── Налаштування Alertmanager: маршрутизація, отримувачі, пригнічення
├── Написання правил сповіщень з відповідною тривалістю for
├── Створення дашбордів Grafana на основі запитів PromQL
└── Фінальний огляд: приділіть 50% часу Домену 3 (PromQL)
```

---

## Поради до іспиту

- **PromQL складає майже третину іспиту** — ви не складете його без вільного написання запитів. Практикуйтеся на реальному Prometheus, а не просто читайте документацію.
- **Вивчіть чотири типи метрик напам'ять** — Counter (тільки зростає), Gauge (зростає та зменшується), Histogram (кошики), Summary (квантилі). Знайте, коли використовувати кожен тип.
- **Функції rate() проти irate() часто тестуються** — `rate()` для дашбордів та сповіщень (згладжена), `irate()` для відлагодження (миттєва). Ніколи не використовуйте `irate()` у правилах сповіщень.
- **Дерево маршрутизації Alertmanager** — зрозумійте ієрархію: глобальний маршрут -> дочірні маршрути -> отримувачі. Параметри `group_by`, `group_wait`, `group_interval`, `repeat_interval`.
- **Угоди щодо найменувань мають значення** — `<namespace>_<name>_<unit>_total` для лічильників, `_seconds` замість `_milliseconds`, `_bytes` замість `_kilobytes`.
- **Правила запису (Recording rules)** — угода щодо найменувань: `level:metric:operations` (двокрапки, а не підкреслення). Знайте, коли вони покращують продуктивність.
- **Інтерполяція histogram_quantile()** — розумійте, що результати є оціночними значеннями, інтерпольованими між межами кошиків. Більше кошиків = вища точність.
- **Не нехтуйте виявленням сервісів (service discovery)** — ролі Kubernetes SD (pod, service, endpoints, node), `relabel_configs` для фільтрації та трансформації міток.

---

## Аналіз прогалин

Модулі спостережуваності KubeDojo разом із двома спеціалізованими модулями PCA забезпечують повне охоплення всіх п'яти доменів.

| Тема | Статус | Примітки |
|-------|--------|-------|
| Теорія спостережуваності (три стовпи) | Покрито | Існуючі базові модулі 3.1-3.4 |
| Архітектура та основи Prometheus | Покрито | Існуючий module-1.1-prometheus.md |
| Селектори PromQL та відповідники міток | Покрито | [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) |
| Функції rate/irate/increase | Покрито | [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) + module-1.1 |
| Оператори агрегації | Покрито | [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) |
| Бінарні оператори та зіставлення векторів | Покрито | [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) |
| histogram_quantile() | Покрито | [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) + module-1.1 |
| Правила запису (Recording rules) | Покрито | [Модуль 1.1: Глибоке занурення в PromQL](module-1.1-promql-deep-dive/) + module-1.1 |
| Клієнтські бібліотеки (Go/Python/Java) | Покрито | [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) |
| Угоди щодо найменування метрик | Покрито | [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) |
| Експортери (node, blackbox) | Покрито | [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) |
| Конфігурація Alertmanager | Покрито | [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) |
| Пригнічення та заглушення | Покрито | [Модуль 1.2: Інструментування та сповіщення](module-1.2-instrumentation-alerting/) |
| Дашборди Grafana | Покрито | Існуючий module-1.3-grafana.md |
| Дистанційний запис/читання Prometheus | Незначна прогалина | Перегляньте [документацію Prometheus щодо дистанційного зберігання](https://prometheus.io/docs/prometheus/latest/storage/#remote-storage-integrations) |
| Федерація Thanos/Cortex | Незначна прогалина | Поза межами PCA; коротко описано в модулі 1.1 |

---

## Основні навчальні ресурси

- **Документація Prometheus**: [prometheus.io/docs](https://prometheus.io/docs/) — головне джерело істини
- **Шпаргалка PromQL**: [promlabs.com/promql-cheat-sheet](https://promlabs.com/promql-cheat-sheet/) — швидка довідка
- **Тренінги PromLabs**: [promlabs.com](https://promlabs.com/) — тренінги з PromQL від Юліуса Вольца (співзасновника Prometheus)
- **Блог Robust Perception**: [robustperception.io/blog](https://www.robustperception.io/blog/) — глибокі занурення від Браяна Бразила
- **Сторінка PCA на CNCF**: [training.linuxfoundation.org](https://training.linuxfoundation.org/) — офіційні деталі іспиту
- **Prometheus Operator**: [prometheus-operator.dev](https://prometheus-operator.dev/) — розгортання в Kubernetes

---

## Супутні сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Напрямок спостережуваності (Observability):
├── KCNA (Cloud Native Associate) — включає основи спостережуваності
├── PCA (Prometheus Certified Associate) ← ВИ ТУТ
├── OTCA (OpenTelemetry Certified Associate) — стандарт інструментування
└── Майбутнє: Advanced Prometheus certification (TBD)

Додаткові сертифікації:
├── CKA (K8s Administrator) — розгортання/керування стеками моніторингу
├── CNPE (Platform Engineer) — 20% спостережуваність та експлуатація
└── CKS (K8s Security Specialist) — аудит логів, моніторинг виконання

Рекомендований порядок:
  KCNA → PCA → OTCA → CKA → CNPE
```

PCA природно поєднується з OTCA (OpenTelemetry Certified Associate) — PCA охоплює сторону зберігання та запитів (Prometheus, PromQL, Alertmanager), тоді як OTCA охоплює сторону інструментування та збору даних (OTel SDK, Collector). Разом вони підтверджують експертизу повного стеку спостережуваності.