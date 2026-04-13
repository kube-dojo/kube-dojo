---
title: "CBA - Certified Backstage Associate"
sidebar:
  order: 0
  label: "CBA"
slug: uk/k8s/cba/index
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/k8s/cba/index.md"
---
> **Тестовий іспит** | 90 хвилин | Прохідний бал: 66% | $250 USD | **Запущено у 2025 році**

## Огляд

CBA (Certified Backstage Associate) підтверджує ваше розуміння Backstage — внутрішнього порталу розробника (Internal Developer Portal, IDP), створеного Spotify, який наразі перебуває в інкубації CNCF. На відміну від сертифікацій з Kubernetes, CBA — це **не практичний іспит**, а тест з варіантами відповідей. Але не дозволяйте цьому ввести вас в оману: він перевіряє реальні знання з розробки. Вам потрібно розуміти TypeScript, React, архітектуру плагінів, YAML каталогу та розгортання в production, а не лише теорію.

**KubeDojo покриває ~90% тем CBA** через наш існуючий модуль Backstage toolkit, дисципліну Platform Engineering та три спеціалізовані модулі CBA, що охоплюють робочі процеси розробки, створення плагінів, а також каталог та інфраструктуру.

> **Ключова відмінність від інших сертифікацій CNCF**: CBA — це сертифікація для розробників. Вона перевіряє, чи можете ви *створювати та розширювати* Backstage, а не просто *використовувати* його. Сприймайте це як «CKAD для порталів розробника».

---

## Спеціалізовані модулі CBA

Ці модулі охоплюють прогалини між існуючим модулем Backstage toolkit у KubeDojo та вимогами іспиту CBA:

| # | Модуль | Тема | Охоплені домени |
|---|--------|-------|-----------------|
| 1 | [Модуль 1.1: Робочий процес розробника Backstage](module-1.1-backstage-dev-workflow/) | Структура монірепозиторію, основи TypeScript, збірка Docker, app-config, CLI | Домен 1 (24%) |
| 2 | [Модуль 1.2: Розробка плагінів Backstage — Кастомізація Backstage](module-1.2-backstage-plugin-development/) | Плагіни frontend/backend, React/MUI, дії scaffolder, теми, API | Домен 4 (32%) |
| 3 | [Модуль 1.3: Каталог та інфраструктура Backstage](module-1.3-backstage-catalog-infrastructure/) | Процесори сутностей, провайдери, анотації, auth, розгортання, усунення несправностей | Домени 2-3 (44%) |

---

## Деталі іспиту

| Деталь | Значення |
|--------|-------|
| **Сертифікація** | Certified Backstage Associate (CBA) |
| **Орган сертифікації** | The Linux Foundation / CNCF |
| **Формат** | Тести з варіантами відповідей (Multiple-choice) |
| **Тривалість** | 90 хвилин |
| **Кількість питань** | ~60 |
| **Прохідний бал** | 66% |
| **Вартість** | $250 USD (включає одну безкоштовну перездачу) |
| **Термін дії** | 3 роки |
| **Вимоги** | Відсутні (але наполегливо рекомендується досвід роботи з TypeScript/React) |
| **Прокторинг** | Онлайн-прокторинг через PSI |

---

## Домени іспиту

| Домен | Вага | Покриття в KubeDojo |
|--------|--------|-------------------|
| Кастомізація Backstage | 32% | Відмінно ([Модуль 1.2: Розробка плагінів Backstage — Кастомізація Backstage](module-1.2-backstage-plugin-development/) — React/MUI, плагіни, теми, scaffolder) |
| Робочий процес розробника Backstage | 24% | Відмінно ([Модуль 1.1: Робочий процес розробника Backstage](module-1.1-backstage-dev-workflow/) — монірепозиторій, TypeScript, Docker, CLI) |
| Інфраструктура Backstage | 22% | Відмінно ([Модуль 1.3: Каталог та інфраструктура Backstage](module-1.3-backstage-catalog-infrastructure/) — auth, розгортання, production) |
| Каталог Backstage | 22% | Відмінно ([Модуль 1.3: Каталог та інфраструктура Backstage](module-1.3-backstage-catalog-infrastructure/) — процесори, провайдери, анотації) |

---

## Домен 1: Робочий процес розробника Backstage (24%)

### Що перевіряє іспит
- **Створити** та **запустити** застосунок Backstage локально
- **Використовувати** основи TypeScript для розробки в Backstage
- **Розуміти** структуру монірепозиторію (packages/app, packages/backend)
- **Збирати** Docker-образи для Backstage
- **Керувати** робочими просторами через команди yarn
- **Розрізняти** конфігурації для розробки та production

### Шлях навчання KubeDojo

**Існуюче покриття:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Встановлення, `npx @backstage/create-app`, `yarn dev` | Частково — лише базове налаштування |

**Спеціалізований модуль CBA:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Модуль 1.1: Робочий процес розробника Backstage](module-1.1-backstage-dev-workflow/) | Структура монірепозиторію, основи TypeScript, збірка Docker, overlays для app-config, команди CLI | Пряма |

---

## Домен 2: Інфраструктура Backstage (22%)

### Що перевіряє іспит
- **Аналізувати** архітектуру фреймворку Backstage (розподіл frontend/backend)
- **Налаштовувати** систему конфігурації (ієрархія `app-config.yaml`)
- **Встановлювати** бази даних (SQLite для розробки, PostgreSQL для production)
- **Конфігурувати** провайдери автентифікації (GitHub, Okta, OIDC)
- **Розгортати** Backstage у Kubernetes
- **Розуміти** клієнт-серверну архітектуру та взаємодію через API
- **Налаштовувати** проксіювання запитів до зовнішніх сервісів

### Шлях навчання KubeDojo

**Існуюче покриття:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Діаграма архітектури, app-config.yaml, YAML для розгортання в K8s | Пряма |
| [Platform Eng 2.3](../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/) | Концепції IDP, чому портали важливі | Контекст |
| [Platform Eng 2.2](../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) | Принципи Developer Experience | Контекст |

**Спеціалізований модуль CBA:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Модуль 1.3: Каталог та інфраструктура Backstage](module-1.3-backstage-catalog-infrastructure/) | Провайдери автентифікації, проксі, міграції БД, посилення безпеки в production, backend-for-frontend | Пряма |

---

## Домен 3: Каталог Backstage (22%)

### Що перевіряє іспит
- **Використовувати** типи сутностей (Component, API, Resource, System, Domain, Group, User, Location, Template)
- **Описувати** структуру та поля `catalog-info.yaml`
- **Застосовувати** анотації та розуміти їх призначення
- **Розуміти** методи імпорту сутностей (статичний, discovery, процесори)
- **Налаштовувати** автоматизований імпорт (GitHub discovery, провайдери сутностей)
- **Визначати** зв’язки між сутностями (ownerOf, partOf, consumesApi, providesApi, dependsOn)
- **Діагностувати** проблеми каталогу (осиротілі сутності, помилки оновлення)
- **Знати** відомі анотації (`backstage.io/techdocs-ref`, `github.com/project-slug` тощо)

### Шлях навчання KubeDojo

**Існуюче покриття:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Типи сутностей, catalog-info.yaml, зв'язки, анотації, авто-discovery | Пряма |
| [Platform Eng 2.4](../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) | Концепція «Golden Paths» (шаблони використовують каталог) | Контекст |
| [Platform Eng 2.5](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/) | Концепції самообслуговування (self-service) | Контекст |

**Спеціалізований модуль CBA:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Модуль 1.3: Каталог та інфраструктура Backstage](module-1.3-backstage-catalog-infrastructure/) | Процесори сутностей, провайдери, всі анотації, усунення несправностей, тип Location, керування життєвим циклом | Пряма |

---

## Домен 4: Кастомізація Backstage (32%)

### Що перевіряє іспит
- **Розробляти** плагіни frontend (компоненти React)
- **Розробляти** плагіни backend (роутери Express)
- **Застосовувати** основи React для Backstage (hooks, state, props)
- **Використовувати** компоненти та стилізацію Material UI (MUI)
- **Працювати** з API плагінів Backstage (`createPlugin`, `createRoutableExtension`, `createApiRef`)
- **Створювати** власні теми
- **Додавати** сторінки та вкладки до перегляду сутності
- **Створювати** власні дії Scaffolder (custom actions)
- **Використовувати** точки розширення (Extension points) та перевизначення (overrides)

### Шлях навчання KubeDojo

**Існуюче покриття:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Backstage 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Огляд екосистеми плагінів, базовий приклад коду плагіна | Мінімальна |

**Спеціалізований модуль CBA:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Модуль 1.2: Розробка плагінів Backstage — Кастомізація Backstage](module-1.2-backstage-plugin-development/) | React/MUI, плагіни frontend/backend, дії scaffolder, теми, точки розширення | Пряма |

---

## Підсумок аналізу прогалин

Наш існуючий модуль Backstage (7.1) надає огляд інструментарію, а три спеціалізовані модулі CBA тепер поглиблено охоплюють іспит: робочі процеси розробки, створення плагінів, а також роботу з каталогом та інфраструктурою.

### Деталізація покриття

```
ПОКРИТТЯ CBA У KUBEDOJO
════════════════════════════════════════════════════════════════

Домен 1: Робочий процес розробника (24%) █████████░ ~90% покрито
Домен 2: Інфраструктура (22%)            █████████░ ~90% покрито
Домен 3: Каталог (22%)                  █████████░ ~90% покрито
Домен 4: Кастомізація Backstage (32%)   █████████░ ~90% покрито

Загальне виважене покриття:             ~90%
```

### Модулі CBA

| Модуль | Теми | Охоплені домени |
|--------|--------|-----------------|
| [Модуль 1.1: Робочий процес розробника Backstage](module-1.1-backstage-dev-workflow/) | Структура монірепозиторію, основи TypeScript, збірка Docker, overlays для app-config, команди CLI, локальний процес розробки | Домен 1 (24%) |
| [Модуль 1.2: Розробка плагінів Backstage — Кастомізація Backstage](module-1.2-backstage-plugin-development/) | Плагіни frontend (React/MUI), плагіни backend (Express), власні дії scaffolder, кастомні теми, точки розширення, API refs | Домен 4 (32%) |
| [Модуль 1.3: Каталог та інфраструктура Backstage](module-1.3-backstage-catalog-infrastructure/) | Процесори сутностей, провайдери сутностей, всі анотації, auth, розгортання в production, усунення несправностей | Домени 2-3 (44%) |

Ці три модулі разом з існуючим Модулем 7.1 забезпечують всебічну підготовку до CBA.

---

## Стратегія навчання

```
ШЛЯХ ПІДГОТОВКИ ДО CBA (4-тижневий план)
══════════════════════════════════════════════════════════════

Тиждень 1: Основи та Каталог (Домени 2-3, 44% іспиту)
├── Platform Engineering 2.1-2.3 (концепції IDP)
├── Backstage 7.1 (архітектура, каталог, шаблони)
├── Встановити Backstage локально, дослідити каталог
├── Попрактикуватися у написанні catalog-info.yaml для різних типів сутностей
└── Вивчити всі зв'язки між сутностями та анотації

Тиждень 2: Робочий процес розробника (Домен 1, 24% іспиту)
├── Налаштувати локальне середовище розробки Backstage
├── Дослідити монірепозиторій: packages/app, packages/backend
├── Зрозуміти ієрархію app-config.yaml та підстановку змінних оточення
├── Попрактикуватися у збірці Docker (host build + multi-stage)
├── Вивчити команди Backstage CLI
└── KubeDojo: Модуль 1.1: Робочий процес розробника Backstage

Тиждень 3: Кастомізація Backstage (Домен 4, 32% іспиту!)
├── Основи React: компоненти, hooks, props, state
├── Material UI: поширені компоненти, стилізація, пропс sx
├── Створити frontend-плагін з нуля
├── Створити backend-плагін з Express роутером
├── Створити власну дію scaffolder
└── KubeDojo: Модуль 1.2: Розробка плагінів Backstage — Кастомізація Backstage

Тиждень 4: Повторення та практика
├── Повторити всі 4 домени
├── Зосередитися на Домені 4 (32%) — найбільша вага
├── Попрактикуватися в усуненні несправностей каталогу
├── Переглянути прогалини в офіційній документації Backstage
└── Пройти пробні питання, якщо вони доступні
```

### Пріоритетність тем для навчання

У CBA кастомізація Backstage займає **32%** — майже третину іспиту. Разом із робочим процесом розробника (24%) це означає, що **56% іспиту стосується написання коду**. Якщо ви маєте досвід в Ops, виділіть додатковий час на React та TypeScript.

```
РОЗПОДІЛ ЧАСУ НА НАВЧАННЯ (за вагою іспиту)
══════════════════════════════════════════════════════════════

Кастомізація Backstage (32%)    ████████████████  ← Слабкі знання? Вивчіть найбільше
Робочий процес розробника (24%) ████████████
Каталог Backstage (22%)         ███████████
Інфраструктура Backstage (22%)  ███████████
```

---

## Поради до іспиту

- **Це іспит на читання коду.** Багато питань містять фрагменти коду TypeScript/React і запитують, що вони роблять. Ви не будете писати код, але ви повинні його *розуміти*.
- **Знайте API плагінів напам'ять.** `createPlugin`, `createRoutableExtension`, `createApiRef`, `createBackendPlugin` — знайте, що робить кожен із них і коли їх використовувати.
- **YAML каталогу перевіряється дуже ретельно.** Попрактикуйтеся писати `catalog-info.yaml` по пам'яті. Знайте кожен тип сутності, анотацію та тип зв'язку.
- **Не ігноруйте Material UI.** Питання перевіряють конкретні компоненти MUI (`Grid`, `Card`, `Table`, `InfoCard`) та спосіб їх використання в Backstage.
- **Зрозумійте ієрархію конфігурації.** Знайте, як `app-config.yaml`, `app-config.local.yaml` та `app-config.production.yaml` об'єднуються та перевизначаються. Знайте, як працює підстановка змінних оточення `${VAR}`.
- **Зосередьтеся на питанні «чому».** Іспит перевіряє розуміння архітектурних рішень: *чому* Backstage розділяє плагіни frontend та backend, *чому* каталог використовує дескрипторний формат, *чому* Software Templates використовують покроковий робочий процес.
- **Читайте офіційну документацію Backstage.** Іспит тісно пов'язаний з [backstage.io/docs](https://backstage.io/docs). Розділи «Getting Started» та «Plugin Development» є особливо важливими.
- **Знання TypeScript є обов'язковим.** Якщо ви не знаєте TypeScript, витратьте кілька днів на основи перед початком підготовки до CBA. Зосередьтеся на: types, interfaces, generics, async/await та імпорті модулів.

---

## Основні ресурси

- [Офіційна документація Backstage](https://backstage.io/docs/) — основне джерело навчання
- [GitHub-репозиторій Backstage](https://github.com/backstage/backstage) — читайте вихідний код плагінів
- [Backstage Storybook](https://backstage.io/storybook) — дивіться компоненти MUI в дії
- [Програма CBA від CNCF](https://github.com/cncf/curriculum) — офіційні цілі іспиту
- [Спільнота плагінів Backstage](https://backstage.io/plugins) — ознайомтеся з екосистемою

---

## Споріднені сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Портал розробника:
└── CBA (Backstage Associate) ← ВИ ТУТ

Platform Engineering:
├── KCNA (Cloud Native Associate) — основи K8s
├── CNPA (Platform Engineering Associate) — основи платформ
└── CNPE (Platform Engineer) — практична інженерія платформ

Kubernetes:
├── CKA (K8s Administrator) — адміністрування кластерів
├── CKAD (K8s Developer) — розгортання застосунків
└── CKS (K8s Security Specialist) — посилення безпеки
```

CBA добре поєднується з **CNPE** (Certified Cloud Native Platform Engineer). CNPE перевіряє вміння створювати платформи; CBA перевіряє вміння створювати портал, що знаходиться зверху. Разом вони підтверджують комплексні навички в Platform Engineering. Якщо ви йдете шляхом Kubestronaut, CBA є додатковою сертифікацією, яка поглиблює ваш досвід у інструментах платформ.

---

## Згадані модулі KubeDojo

| Модуль | Шлях | Релевантність до CBA |
|--------|------|---------------|
| Backstage 7.1 | [module-7.1-backstage.md](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Основа — архітектура, каталог, шаблони, огляд плагінів |
| Platform Eng 2.1 | [module-2.1-what-is-platform-engineering.md](../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/) | Контекст — що таке Platform Engineering |
| Platform Eng 2.2 | [module-2.2-developer-experience.md](../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/) | Контекст — принципи DevEx |
| Platform Eng 2.3 | [module-2.3-internal-developer-platforms.md](../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/) | Контекст — концепції IDP |
| Platform Eng 2.4 | [module-2.4-golden-paths.md](../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/) | Контекст — «Golden Paths» (шаблони) |
| Platform Eng 2.5 | [module-2.5-self-service-infrastructure.md](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/) | Контекст — концепції самообслуговування |
| Platform Eng 2.6 | [module-2.6-platform-maturity.md](../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/) | Контекст — моделі зрілості |