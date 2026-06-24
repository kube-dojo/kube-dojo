---
title: "CCA — Cilium Certified Associate"
sidebar:
  order: 0
  label: "CCA"
slug: uk/k8s/cca
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/k8s/cca/index.md"
calque_review:
  reviewed_at: "2026-06-24"
  detector_version: "v2"
  status: "clean"
  flags_resolved: 0
  content_sha: "71e5d073515a9d963b30641facdc899b4a398592eae602fc64f6e71a94f0b3bb"
---
> **Іспит з вибором варіантів відповіді** | 90 хвилин | Прохідний бал: 66% | $250 USD | **Запущено у 2024 році**

## Огляд

CCA (Cilium Certified Associate) підтверджує фундаментальні знання про Cilium, мережеві можливості на базі eBPF, мережеві політики, спостережуваність (observability) та підключення між кластерами. Це **теоретичний іспит** із питаннями з вибором варіантів відповіді — без практичних завдань, проте глибоке розуміння концепцій Cilium є критично важливим.

**KubeDojo покриває ~90%+ тем CCA** через наші існуючі модулі інструментарію Platform Engineering, а також спеціалізований просунутий модуль Cilium. На цій сторінці наведено відповідність доменів CCA існуючим модулям.

> **Зараз Cilium є стандартним CNI** для GKE, EKS та AKS. Розуміння Cilium — це не лише підготовка до іспиту, а й базова навичка для будь-якого інженера Kubernetes.

---

## Домени іспиту

| Домен | Вага | Покриття у KubeDojo | Статус |
|-------|------|---------------------|--------|
| Architecture | 20% | Часткове — поглиблено у Модулі 1.1 | Покрито |
| Network Policy | 18% | Часткове — поглиблено у Модулі 1.1 | Покрито |
| Service Mesh | 16% | Добре (Gateway API розглянуто у Модулі 1.1) | Покрито |
| Observability | 10% | Добре (модуль Hubble) | Покрито |
| Installation & Configuration | 10% | Часткове — поглиблено у Модулі 1.1 | Покрито |
| Cluster Mesh | 10% | ПРОГАЛИНА — покрито у Модулі 1.1 | Покрито |
| eBPF | 10% | Добре (кілька існуючих модулів) | Покрито |
| BGP & External Networking | 6% | ПРОГАЛИНА — покрито у Модулі 1.1 | Покрито |

---

## Домен 1: Architecture (20%)

### Компетенції
- **Розуміти** архітектуру компонентів Cilium (agent, operator, Hubble, relay)
- **Знати**, як Cilium інтегрується з ядром Linux через eBPF
- **Розуміти** безпеку на основі ідентифікаторів та її відмінність від безпеки на основі IP
- **Вивчити** режими IPAM та варіанти шляху даних (data path)

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Cilium Toolkit](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/) | Огляд Cilium, основи eBPF, схема архітектури, безпека на основі ідентифікаторів | Пряма |
| [Module 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) | Глибоке занурення в Agent, Operator, Hubble, режими IPAM (cluster-pool, kubernetes, multi-pool) | Пряма |
| [eBPF Foundations](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/#part-2-enter-ebpf-programming-the-unprogrammable) | eBPF verifier, типи програм, карти (maps) | Пряма |

---

## Домен 2: Network Policy (18%)

### Компетенції
- **Написати** CiliumNetworkPolicy та CiliumClusterwideNetworkPolicy
- **Розуміти** застосування політики на рівнях L3/L4 та L7 (з підтримкою HTTP)
- **Порівняти** моделі політик на основі ідентифікаторів та на основі IP
- **Розуміти** режими застосування політик (default, always, never)
- **Створити** політики вихідного трафіку (egress) на основі DNS (FQDN)

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Cilium Toolkit](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/#part-5-network-policies-from-basic-to-wow) | Стандартна NetworkPolicy, CiliumNetworkPolicy, правила L7, egress на основі DNS, загальнокластерні політики | Пряма |
| [Module 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) | Порівняння CiliumNetworkPolicy та K8s NetworkPolicy, режими застосування політик, правила L7 з підтримкою HTTP, політики на основі сутностей (entities) | Пряма |
| [CKS Network Policies](../cks/) | Стандартна K8s NetworkPolicy (базові знання) | Допоміжна |

---

## Домен 3: Service Mesh (16%)

### Компетенції
- **Розуміти** модель Service Mesh від Cilium без використання sidecar-контейнерів
- **Знати** принципи інтеграції з Gateway API
- **Налаштувати** mTLS у Cilium (ідентифікатори SPIFFE)
- **Розуміти** балансування навантаження та управління трафіком

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Service Mesh Toolkit](../../platform/toolkits/infrastructure-networking/networking/module-5.2-service-mesh/) | Паттерни Service Mesh, sidecar проти sidecar-free, Gateway API | Пряма |
| [Cilium Toolkit](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/#part-8-transparent-encryption-with-wireguard) | Шифрування WireGuard, заміна kube-proxy | Часткова |
| [SPIFFE/SPIRE](../../platform/toolkits/security-quality/security-tools/module-4.8-spiffe-spire/) | Ідентифікація робочих навантажень, концепції mTLS | Допоміжна |

> Конфігурація Gateway API для Cilium (HTTPRoute, GRPCRoute з Cilium як контролером Gateway) тепер розглядається у [Модулі 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/). Для глибшого вивчення дивіться [документацію Cilium Gateway API](https://docs.cilium.io/en/stable/network/servicemesh/gateway-api/).

---

## Домен 4: Observability (10%)

### Компетенції
- **Використовувати** Hubble CLI для спостереження за потоками та фільтрації
- **Розуміти** архітектуру Hubble Relay та UI
- **Налаштувати** метрики Hubble для Prometheus
- **Інтерпретувати** дані мережевих потоків для діагностики несправностей

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Hubble Toolkit](../../platform/toolkits/observability-intelligence/observability/module-1.7-hubble/) | Архітектура Hubble, використання CLI, фільтрація потоків, інтерфейс користувача (UI), метрики Prometheus, сценарії діагностики | Пряма |
| [Cilium Toolkit](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/#part-6-hubble-seeing-the-invisible) | Команди Hubble CLI, структура виводу, сценарії налагодження, конфігурація метрик | Пряма |

---

## Домен 5: Installation & Configuration (10%)

### Компетенції
- **Встановити** Cilium за допомогою Cilium CLI та Helm
- **Налаштувати** заміну kube-proxy
- **Перевірити** коректність встановлення за допомогою `cilium status` та `cilium connectivity test`
- **Оновити** Cilium

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Cilium Toolkit](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/#installation-your-first-cilium-cluster) | Встановлення через Cilium CLI, встановлення з Helm values, тест підключення | Пряма |
| [Module 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) | Глибоке занурення в Cilium CLI (install, status, connectivity test, config), встановлення через Helm | Пряма |

---

## Домен 6: Cluster Mesh (10%)

### Компетенції
- **Розуміти** підключення між кластерами за допомогою Cluster Mesh
- **Налаштувати** глобальні сервіси та афінність сервісів (service affinity)
- **Розуміти** виявлення сервісів між кластерами
- **Знати** вимоги та обмеження Cluster Mesh

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Module 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) | Архітектура Cluster Mesh, глобальні сервіси, анотації афінності, виявлення сервісів у кількох кластерах, практичне налаштування | Пряма |

> **Це була ПРОГАЛИНА** в нашому існуючому контенті. Модуль 1.1 забезпечує повне покриття цієї теми.

---

## Домен 7: eBPF (10%)

### Компетенції
- **Розуміти** основи eBPF (програми, карти, верифікатор)
- **Знати**, як Cilium використовує eBPF для мережевої взаємодії, політик та спостережуваності
- **Порівняти** eBPF та iptables для обробки пакетів
- **Вивчити** основи XDP (eXpress Data Path)

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Cilium Toolkit](../../platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/#part-2-enter-ebpf-programming-the-unprogrammable) | Ментальна модель eBPF, верифікатор, порівняння потоків пакетів, програмування ядра | Пряма |
| [Module 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) | eBPF у контексті архітектури Cilium, dataplane | Допоміжна |

---

## Домен 8: BGP & External Networking (6%)

### Компетенції
- **Розуміти** налаштування BGP-пірингу за допомогою CiliumBGPPeeringPolicy
- **Анонсувати** CIDR Pod'ів та VIP-адреси Service зовнішнім маршрутизаторам
- **Анонсувати** IP-адреси LoadBalancer
- **Знати** базові концепції BGP (ASN, піринг, анонсування маршрутів)

### Навчальний шлях KubeDojo

| Модуль | Тема | Актуальність |
|--------|------|--------------|
| [Module 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) | CiliumBGPPeeringPolicy, конфігурація ASN, анонсування маршрутів, інтеграція з LoadBalancer | Пряма |

> **Це була ПРОГАЛИНА** в нашому існуючому контенті. Модуль 1.1 забезпечує повне покриття цієї теми.

---

## Стратегія навчання

```
ШЛЯХ ПІДГОТОВКИ ДО CCA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1: Основи (eBPF + Архітектура = 30%)
├── Модуль Cilium Toolkit (повне прочитання)
├── Модуль 1.1: Глибоке занурення в архітектуру
├── Зосередитись на: ролях agent та operator, моделі ідентифікаторів, IPAM
└── Лабораторна робота: Встановити Cilium у кластері kind, запустити тест підключення

Тиждень 2: Мережеві політики (18%)
├── Cilium Toolkit: розділи про Network Policy
├── Модуль 1.1: Режими застосування політик
├── Практика написання YAML для CiliumNetworkPolicy
└── Лабораторна робота: Правила "заборонити все за замовчуванням" + дозволяючі правила, політики L7 HTTP

Тиждень 3: Service Mesh + Спостережуваність (26%)
├── Модуль Service Mesh toolkit
├── Модуль Hubble toolkit (повністю)
├── Cilium Toolkit: розділи про Hubble
└── Лабораторна робота: Hubble observe з --verdict DROPPED, метрики Prometheus

Тиждень 4: Cluster Mesh + BGP + Повторення (16%)
├── Модуль 1.1: розділ Cluster Mesh
├── Модуль 1.1: розділ BGP
├── Повторення всіх контрольних запитань
└── Практика: Наскрізні сценарії діагностики несправностей
```

---

## Поради до іспиту

- **Це теоретичний іспит** — без роботи в терміналі, але концептуальна глибина є ключовою.
- **Досконало знайте архітектуру** — який компонент за що відповідає, де він запускається, скільки екземплярів.
- **CiliumNetworkPolicy проти K8s NetworkPolicy** — чітко розумійте, що саме додає Cilium (L7, FQDN, сутності, загальнокластерні політики).
- **Модель ідентифікаторів** — на іспиті часто зустрічаються питання про те, чому безпека на основі ідентифікаторів краща за безпека на основі IP.
- **Прапорці Hubble CLI** — знайте загальні фільтри (`--verdict`, `--from-pod`, `--to-pod`, `--protocol`).
- **Cluster Mesh** — розумійте вимоги (спільний CA, унікальні CIDR Pod'ів, зв'язність між кластерами).
- **BGP** — знайте, що робить CiliumBGPPeeringPolicy і коли її використовувати (анонсування IP-адрес LoadBalancer).
- **Режими застосування політик** — `default`, `always`, `never` та умови застосування кожного з них.

---

## Аналіз прогалин

| Тема | Статус | Примітки |
|------|--------|----------|
| Cilium Gateway API (HTTPRoute, GRPCRoute) | Покрито | Розглянуто у [Модулі 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) разом із модулем Service Mesh |
| Cilium Bandwidth Manager | Покрито | Розглянуто у [Модулі 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/); специфічна тема, низька вага на іспиті |
| Cilium Egress Gateway | Покрито | Розглянуто у [Модулі 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/); просунута функція, навряд чи буде активно тестуватися |
| CiliumL2AnnouncementPolicy | Покрито | Розглянуто у [Модулі 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/); анонсування на рівні L2, рідко зустрічається на іспиті |

Існуючі модулі інструментарію разом із Модулем 1.1 забезпечують всебічну підготовку до CCA.

---

## Індекс модулів

| # | Модуль | Теми | Складність |
|---|--------|------|------------|
| 1 | [Module 1.1: Advanced Cilium for CCA](module-1.1-advanced-cilium/) | Глибина архітектури, CiliumNetworkPolicy, Cluster Mesh, BGP, Cilium CLI | `[COMPLEX]` |

---

## Пов'язані сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Початковий рівень:
├── KCNA (Cloud Native Associate) — основи K8s
├── KCSA (Security Associate) — основи безпеки
└── CCA (Cilium Certified Associate) <-- ВИ ТУТ

Професійний рівень:
├── CKA (K8s Administrator) — операції з кластером
├── CKAD (K8s Developer) — розгортання застосунків
├── CKS (K8s Security Specialist) — зміцнення безпеки
└── CNPE (Platform Engineer) — інженерія платформ

Спеціаліст:
└── CKNE (K8s Network Engineer) — просунуті мережі (поглиблено охоплює Cilium)
```

CCA добре поєднується з KCNA (загальні знання K8s) та KCSA (основи безпеки). Якщо ви плануєте отримати CKNE пізніше, CCA дасть вам потужний старт у частині, що стосується Cilium.
