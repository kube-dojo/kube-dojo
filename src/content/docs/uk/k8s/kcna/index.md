---
title: "Навчальна програма KCNA"
sidebar:
  order: 1
  label: "KCNA"
---
> **Kubernetes and Cloud Native Associate** - Сертифікація початкового рівня з основ хмарних технологій

## Про KCNA

KCNA — це іспит з **множинним вибором відповідей** (не практичний), який перевіряє базові знання Kubernetes та хмарних технологій. Ідеально підходить для тих, хто тільки починає знайомитися з хмарними технологіями, або як підготовка до CKA/CKAD.

| Аспект | Деталі |
|--------|--------|
| **Формат** | Множинний вибір |
| **Тривалість** | 90 хвилин |
| **Питання** | ~60 питань |
| **Прохідний бал** | 75% |
| **Термін дії** | 3 роки |

## Структура програми

*Оновлено листопад 2025 — Спостережуваність об'єднано з Хмарною архітектурою*

| Частина | Тема | Вага | Модулі |
|---------|------|------|--------|
| [Частина 0](part0-introduction/) | Вступ | - | 2 |
| [Частина 1](part1-kubernetes-fundamentals/) | Основи Kubernetes | 44% | 8 |
| [Частина 2](part2-container-orchestration/) | Оркестрація контейнерів | 28% | 4 |
| [Частина 3](part3-cloud-native-architecture/) | Хмарна архітектура | 12% | 8 |
| [Частина 4](part4-application-delivery/) | Доставка застосунків | 16% | 2 |
| **Всього** | | **100%** | **24** |

## Огляд модулів

### Частина 0: Вступ (2 модулі)
- [0.1 Огляд KCNA](part0-introduction/module-0.1-kcna-overview/) - Формат іспиту та домени
- [0.2 Стратегія підготовки](part0-introduction/module-0.2-study-strategy/) - Техніки для іспиту з множинним вибором

### Частина 1: Основи Kubernetes (8 модулів) — 44%
- [1.1 Що таке Kubernetes](part1-kubernetes-fundamentals/module-1.1-what-is-kubernetes/) - Призначення та архітектура
- [1.2 Основи контейнерів](part1-kubernetes-fundamentals/module-1.2-container-fundamentals/) - Концепції контейнерів
- [1.3 Площина управління](part1-kubernetes-fundamentals/module-1.3-control-plane/) - API server, etcd, scheduler
- [1.4 Компоненти вузлів](part1-kubernetes-fundamentals/module-1.4-node-components/) - kubelet, kube-proxy
- [1.5 Поди](part1-kubernetes-fundamentals/module-1.5-pods/) - Базова одиниця навантаження
- [1.6 Ресурси навантажень](part1-kubernetes-fundamentals/module-1.6-workload-resources/) - Deployments, StatefulSets
- [1.7 Сервіси](part1-kubernetes-fundamentals/module-1.7-services/) - Типи сервісів та виявлення
- [1.8 Простори імен та мітки](part1-kubernetes-fundamentals/module-1.8-namespaces-labels/) - Організація

### Частина 2: Оркестрація контейнерів (4 модулі) — 28%
- [2.1 Планування](part2-container-orchestration/module-2.1-scheduling/) - Як Поди призначаються на вузли
- [2.2 Масштабування](part2-container-orchestration/module-2.2-scaling/) - HPA, VPA, Cluster Autoscaler
- [2.3 Зберігання](part2-container-orchestration/module-2.3-storage/) - PV, PVC, StorageClass
- [2.4 Конфігурація](part2-container-orchestration/module-2.4-configuration/) - ConfigMaps та Secrets

### Частина 3: Хмарна архітектура (8 модулів) — 12%
*Включає спостережуваність (об'єднано листопад 2025)*

- [3.1 Принципи хмарних технологій](part3-cloud-native-architecture/module-3.1-cloud-native-principles/) - 12-factor apps
- [3.2 Екосистема CNCF](part3-cloud-native-architecture/module-3.2-cncf-ecosystem/) - Проєкти та ландшафт
- [3.3 Хмарні патерни](part3-cloud-native-architecture/module-3.3-patterns/) - Service mesh, GitOps
- [3.4 Основи спостережуваності](part3-cloud-native-architecture/module-3.4-observability-fundamentals/) - Метрики, логи, трейси
- [3.5 Інструменти спостережуваності](part3-cloud-native-architecture/module-3.5-observability-tools/) - Prometheus, Grafana, Jaeger
- [3.8 AI/ML у хмарних технологіях](part3-cloud-native-architecture/module-3.8-ai-ml-cloud-native/) - AI/LLM навантаження, планування GPU, обслуговування моделей
- [3.9 WebAssembly](part3-cloud-native-architecture/module-3.9-webassembly/) - Wasm як альтернатива контейнерам, WASI, SpinKube
- [3.10 Зелені обчислення та сталий розвиток](part3-cloud-native-architecture/module-3.10-green-computing/) - Вуглецево-орієнтоване планування, ефективність ресурсів

### Частина 4: Доставка застосунків (2 модулі) — 16%
- [4.1 Основи CI/CD](part4-application-delivery/module-4.1-ci-cd/) - Конвеєри та розгортання
- [4.2 Пакування застосунків](part4-application-delivery/module-4.2-application-packaging/) - Helm та Kustomize

## Як користуватися цією програмою

1. **Дотримуйтесь порядку** - Модулі базуються один на одному
2. **Читайте активно** - Не просто переглядайте, а розумійте концепції
3. **Проходьте вікторини** - Кожен модуль має запитання для перевірки
4. **Вивчайте діаграми** - Візуальне навчання важливе для множинного вибору
5. **Зосередьтеся на "чому"** - KCNA перевіряє розуміння, а не команди

## Ключові відмінності від CKA/CKAD

| Аспект | KCNA | CKA/CKAD |
|--------|------|----------|
| Формат | Множинний вибір | Практична лабораторія |
| Фокус | Концепції | Команди |
| Складність | Початковий рівень | Професійний |
| Доступ до Kubernetes | Немає | Повний кластер |

## Аналіз прогалин (оновлення листопад 2025)

Оновлення навчальної програми KCNA у листопаді 2025 року ввело кілька нових тем, які є незначними розділами іспиту, але варті уваги:

- **AI/LLM навантаження на Kubernetes** — Запуск навантажень виведення та навчання, планування GPU, обслуговування моделей
- **WebAssembly (Wasm)** — Wasm як легка альтернатива контейнерам, WASI, SpinKube
- **Зелені обчислення** — Вуглецево-орієнтоване планування, ефективність ресурсів, сталий розвиток у хмарних технологіях

Ці теми становлять невеликий відсоток питань, але вказують напрямок розвитку хмарної екосистеми. Дивіться модулі 3.8-3.10 вище.

## Поради для підготовки

- **Розумійте, а не заучуйте** - Іспит перевіряє концепції
- **Знайте проєкти CNCF** - Особливо ті, що мають статус graduated
- **Зосередьтеся на частинах 1 та 2** - Вони становлять 72% іспиту разом
- **Вивчайте діаграми** - Візуалізація допомагає з множинним вибором
- **Проходьте пробні тести** - Звикайте до формату

## Почніть навчання

Почніть з [Частини 0: Вступ](part0-introduction/module-0.1-kcna-overview/), щоб зрозуміти формат іспиту, а потім продовжуйте кожну частину по порядку.

Успіхів на вашому шляху до KCNA!
