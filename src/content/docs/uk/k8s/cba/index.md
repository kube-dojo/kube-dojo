---
title: "CBA — Сертифікований спеціаліст із Backstage"
sidebar:
  order: 0
  label: "CBA"
---
> **Іспит із множинним вибором** | 90 хвилин | Прохідний бал: 75% | $250 USD | **Сертифікація CNCF**

## Огляд

CBA (Certified Backstage Associate) підтверджує знання екосистеми Backstage, архітектури порталів розробника (Internal Developer Portals - IDP) та плагінів. Це **теоретичний іспит** — питання з множинним вибором, що перевіряють ваше розуміння того, як Backstage допомагає зменшити когнітивне навантаження розробників та впровадити "золоті шляхи" (golden paths).

**KubeDojo охоплює ~90% тем CBA** через дисципліну Platform Engineering та набір інструментів платформ.

> **Backstage є ядром платформної інженерії.** Створений у Spotify, він став проєктом CNCF Graduated у 2024 році. Це галузевий стандарт для побудови порталів розробника, який об'єднує інфраструктуру, документацію та сервіси в єдиному інтерфейсі.

---

## Модулі, специфічні для CBA

Цей модуль заповнює прогалину між загальними знаннями платформ та специфікою Backstage:

| # | Модуль | Тема | Охоплені домени |
|---|--------|-------|-----------------|
| 1 | [Глибоке занурення в Backstage](module-1.1-backstage-deep-dive/) | Software Catalog (entities), Software Templates (Scaffolder), TechDocs, архітектура плагінів, аутентифікація та дозволи | Домени 1-5 |

---

## Домени іспиту

| Домен | Вага | Охоплення в KubeDojo |
|--------|--------|-------------------|
| Концепції IDP та Backstage | 20% | Відмінне ([Platform Engineering 2.1](../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/)) |
| Software Catalog | 25% | Відмінне ([Глибоке занурення в Backstage](module-1.1-backstage-deep-dive/)) |
| Software Templates (Scaffolder) | 20% | Відмінне ([Глибоке занурення в Backstage](module-1.1-backstage-deep-dive/)) |
| TechDocs | 15% | Відмінне ([Глибоке занурення в Backstage](module-1.1-backstage-deep-dive/)) |
| Екосистема та Плагіни | 20% | Відмінне ([Platforms Toolkit 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/)) |

---

## Домен 1: Концепції IDP та Backstage (20%)

### Компетенції
- Розуміння проблем "фрагментації інструментів" та когнітивного навантаження
- Визначення Internal Developer Portal (IDP) та його ролі в Platform Engineering
- Історія Backstage та його шлях у CNCF
- Ключові переваги: виявлення сервісів, самообслуговування, стандартизація

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Platform Engineering 2.1](../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/) | Що таке IDP? Чому Backstage? | Пряма |
| [Platform Engineering 2.2](../../platform/disciplines/core-platform/platform-engineering/module-2.2-golden-paths/) | Золоті шляхи та когнітивне навантаження | Пряма |

---

## Домен 2: Software Catalog (25%)

### Компетенції
- Розуміння моделі даних Catalog (Entities: Component, API, Resource, Group, User, System, Domain)
- Робота з файлами `catalog-info.yaml`
- Розуміння зв'язків (relationships) між сутностями (owner, dependsOn, providesApi)
- Процес реєстрації (Ingestion) та процесори (Processors)

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Глибоке занурення в Backstage](module-1.1-backstage-deep-dive/) | Entity Model та дизайн каталогу | Пряма |
| [Platforms Toolkit 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Практична робота з каталогом | Пряма |

---

## Домен 3: Software Templates (Scaffolder) (20%)

### Компетенції
- Створення нових проєктів через Software Templates (Golden Paths)
- Розуміння структури `template.yaml` (parameters, steps, outputs)
- Використання Scaffolder Actions (fetch:template, publish:github тощо)
- Воркфлоу самообслуговування для розробників

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Глибоке занурення в Backstage](module-1.1-backstage-deep-dive/) | Написання власних шаблонів (Scaffolder) | Пряма |
| [Platform Engineering 2.5](../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service/) | Забезпечення самообслуговування | Пряма |

---

## Домен 4: TechDocs (15%)

### Компетенції
- Філософія "Docs-like-code"
- Архітектура TechDocs: Build, Publish, Storage
- Використання Markdown та інтеграція з репозиторіями Git
- Переваги централізованої документації в порталі

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Глибоке занурення в Backstage](module-1.1-backstage-deep-dive/) | TechDocs конвеєр та візуалізація | Пряма |

---

## Домен 5: Екосистема та Плагіни (20%)

### Компетенції
- Архітектура плагінів (Frontend vs. Backend плагіни)
- Використання Core Features (Home, Search, Explore)
- Інтеграція із зовнішніми інструментами (ArgoCD, GitHub Actions, Snyk, Kubernetes)
- Конфігурація через `app-config.yaml`

### Шлях навчання в KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Platforms Toolkit 7.1](../../platform/toolkits/infrastructure-networking/platforms/module-7.1-backstage/) | Встановлення та налаштування плагінів | Пряма |

---

## Стратегія підготовки

```
ШЛЯХ ПІДГОТОВКИ ДО CBA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1: Теорія Платформ та IDP (20%)
├── Модулі Platform Engineering (2.1 - 2.2)
├── Модуль Platforms Toolkit 7.1 (Backstage Intro)
└── Практика: Запустіть Backstage локально через `npx @backstage/create-app`

Тиждень 2: Software Catalog (25%)
├── Модуль "Глибоке занурення в Backstage" (Catalog)
├── Практика: Напишіть 5 різних `catalog-info.yaml` (Component, System, API)
└── Вивчіть: Як сутності пов'язані між собою через `owner` та `system`

Тиждень 3: Scaffolder та Templates (20%)
├── Модуль "Глибоке занурення в Backstage" (Templates)
├── Практика: Створіть шаблон, що робить коміт у GitHub репозиторій
└── Вивчіть: Синтаксис `parameters` та доступні дії (actions)

Тиждень 4: TechDocs та Екосистема (15% + 20%)
├── Модуль "Глибоке занурення в Backstage" (TechDocs)
├── Практика: Налаштуйте плагін Kubernetes або ArgoCD
└── Огляд: Як працює `app-config.yaml` та змінні оточення
```

---

## Поради для іспиту

- **EntityKinds** — Знайте різницю між `Component`, `System`, `Domain`, `Resource`, `API`. Це база каталогу.
- **Scaffolder Actions** — Розумійте, що таке вбудовані дії (built-in actions) та як Scaffolder взаємодіє з Git провайдерами.
- **Docs-like-code** — Розумійте архітектурний потік TechDocs (Markdown в Git -> CI збірка -> Storage -> Backstage Frontend).
- **Owner relationship** — Кожна сутність у каталозі ПОВИННА мати власника (`Group` або `User`).
- **Плагіни** — Знайте, що Backstage — це лише фреймворк, а вся функціональність додається через плагіни.

---

## Пов'язані сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Associate Рівень:
├── KCNA (Cloud Native Associate) — Основи
├── CGOA (GitOps Associate) — Доставка
└── CBA (Backstage Associate) ← ВИ ТУТ

Professional Рівень:
├── CNPE (Platform Engineer) — Backstage є головним інструментом
└── CKAD (K8s Developer) — Розробники є кінцевими користувачами Backstage
```

CBA — це ключова сертифікація для **Platform Engineers**, оскільки вона підтверджує знання основного інструменту для побудови внутрішніх платформ.
