---
title: "\u0416\u0443\u0440\u043d\u0430\u043b \u0437\u043c\u0456\u043d"
template: splash
sidebar:
  order: 2
---
## 16 квітня 2026 — ZTT, AI/ML, підготовка до сертифікацій і маршрути навчання

### Zero to Terminal посилено
- теоретичну частину `Zero to Terminal` доведено до суворішого стандарту рев’ю
- ранні лабораторні роботи перевірено й підтягнуто, а не залишено прихованим боргом
- українську синхронізацію ZTT переведено на `translation-v2`

### Розширено шлях AI/ML для learner-ів
Трек AI/ML тепер має чіткий local-first шлях, а не стрибок одразу в велику інфраструктуру.

Нові модулі:
- Home AI Workstation Fundamentals
- Reproducible Python, CUDA, and ROCm Environments
- Notebooks, Scripts, and Project Layouts
- Home-Scale RAG Systems
- Notebooks to Production for ML/LLMs
- Small-Team Private AI Platform
- Single-GPU Local Fine-Tuning
- Multi-GPU Home-Lab Fine-Tuning
- Local Inference Stack for Learners
- Home AI Operations and Cost Model

### Закрито прогалини у сертифікаційній підготовці
Додано окремі exam-prep модулі для:
- `LFCS`
- `CNPE`
- `CNPA`
- `CGOA`

### Поліпшено навігацію між треками
Оновлено ключові хаби, щоб learner-и могли переходити між треками без здогадок:
- головна сторінка
- сертифікації Kubernetes
- Cloud
- Platform Engineering
- On-Premises
- AI/ML Engineering

### Поліпшено внутрішню інфраструктуру доставки
- посилено маршрутизацію review/patch у v2 pipeline
- `translation-v2` тепер керує українською синхронізацією через чергу
- локальний monitor/API показує детальніший стан черг, а не лише підсумкові лічильники

---
## Березень 2026 — Переклад передумов + Оновлення екосистеми + 21 сертифікація

### Переклад українською — Передумови завершено!

Усі модулі передумов тепер доступні українською:

- **Основи Kubernetes** (8 модулів): Перший кластер, kubectl, Поди, Деплойменти, Сервіси, ConfigMaps & Secrets, Простори імен та мітки, YAML для Kubernetes
- **Сучасний DevOps** (6 модулів): Інфраструктура як код, GitOps, CI/CD конвеєри, Спостережуваність, Платформна інженерія, DevSecOps

Разом із раніше перекладеними модулями (Від нуля до терміналу, Філософія та дизайн, Cloud Native 101), усі **33 модулі передумов** тепер доступні українською.

---

## Березень 2026 — Оновлення екосистеми + Перевірка якості + 21 сертифікація

**Найбільше оновлення з моменту запуску KubeDojo.** 40+ нових модулів, 30+ оновлених, кожен модуль перевірено на якість, покриття розширено до 21 сертифікації.

### 21 трек сертифікацій

KubeDojo тепер охоплює кожну хмарну сертифікацію з каталогу Linux Foundation:

| Рівень | Сертифікації |
|--------|-------------|
| **Ядро K8s** | [KCNA](../k8s/kcna/), [KCSA](../k8s/kcsa/), [CKA](../k8s/cka/), [CKAD](../k8s/ckad/), [CKS](../k8s/cks/) |
| **Спеціаліст** | [CNPE](../k8s/cnpe/), [CNPA](../k8s/cnpa/) |
| **За інструментом** | [PCA](../k8s/pca/), [ICA](../k8s/ica/), [CCA](../k8s/cca/), [CBA](../k8s/cba/), [OTCA](../k8s/otca/), [KCA](../k8s/kca/), [CAPA](../k8s/capa/), [CGOA](../k8s/cgoa/) |
| **Інше** | [LFCS](../k8s/lfcs/), [FinOps](/uk/platform/disciplines/business-value/finops/) |

### Підтримка Kubernetes 1.35 «Timbernetes»

KubeDojo тепер повністю узгоджений з **Kubernetes 1.35** (випущений у грудні 2025):

- **Оновлення версії**: Усі приклади налаштування кластера, kubeadm та оновлення змінено з 1.31 на 1.35
- **cgroup v2 обов'язковий**: Модуль налаштування кластера тепер охоплює вимогу cgroup v2 (v1 вимкнено за замовчуванням)
- **containerd 2.0**: Оновлені рекомендації щодо середовища виконання для containerd 2.0+
- **In-Place Pod Resize (GA)**: Новий розділ у керуванні ресурсами, що охоплює динамічне налаштування CPU/пам'яті
- **Gateway API як стандарт**: Переформатовано з «майбутнього» на поточний рекомендований підхід
- **Відставка Ingress-NGINX**: Додано інструкції з міграції для треків CKA, CKAD та CKS
- **Застарілість IPVS**: Оновлено мережеві модулі з рекомендацією nftables
- **Зміна WebSocket RBAC**: Критична зламна зміна задокументована в модулі RBAC

### Нові модулі

#### Треки сертифікацій
| Модуль | Трек | Опис |
|--------|------|------|
| [Autoscaling (HPA/VPA)](../k8s/cka/part2-workloads-scheduling/module-2.9-autoscaling/) | CKA | Горизонтальне та вертикальне автомасштабування Подів із практичним навантажувальним тестуванням |
| [etcd-operator v0.2.0](/uk/k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/) | Platform | Офіційний оператор etcd — керування TLS, керовані оновлення |
| [Навчальний шлях CNPE](../k8s/cnpe/) | CNPE | Зіставлення 60+ наявних модулів із доменами нової сертифікації CNPE |

#### Набір інструментів платформної інженерії — 15 нових модулів
| Модуль | Категорія | Опис |
|--------|-----------|------|
| [**FinOps та OpenCost**](../platform/toolkits/developer-experience/scaling-reliability/module-6.4-finops-opencost/) | Масштабування | Оптимізація витрат K8s, правильний вибір ресурсів, очищення неактивного |
| [**Kyverno**](/uk/platform/toolkits/security-quality/code-quality/module-12.5-trivy/) | Безпека | YAML-рідний рушій політик — валідація, мутація, генерація |
| [**Хаос-інженерія**](/uk/platform/disciplines/reliability-security/chaos-engineering/) | Масштабування | LitmusChaos + Chaos Mesh практика з плануванням GameDay |
| [**Створення операторів**](../platform/toolkits/infrastructure-networking/platforms/module-3.4-kubebuilder/) | Платформи | Kubebuilder з нуля — побудова оператора WebApp |
| [**Безперервне профілювання**](../platform/toolkits/observability-intelligence/observability/module-1.9-continuous-profiling/) | Спостережуваність | Parca + Pyroscope — 4-й стовп спостережуваності |
| [**Інструменти SLO**](/uk/k8s/kcsa/part5-platform-security/module-5.4-security-tooling/) | Спостережуваність | Sloth + Pyrra — мост від теорії SRE до практики |
| [**Cluster API**](/uk/cloud/enterprise-hybrid/module-10.6-cluster-api/) | Платформи | Декларативне керування життєвим циклом кластерів K8s (CAPI) |
| [**vCluster**](../platform/toolkits/infrastructure-networking/platforms/module-3.6-vcluster/) | Платформи | Віртуальні кластери K8s для мультиорендності за 1/10 вартості |
| [**Rook/Ceph**](../platform/toolkits/infrastructure-networking/storage/module-16.1-rook-ceph/) | Сховище | Розподілене сховище — блокове, файлова система та об'єктне з одного кластера |
| [**MinIO**](../platform/toolkits/infrastructure-networking/storage/module-16.2-minio/) | Сховище | S3-сумісне об'єктне сховище на K8s |
| [**Longhorn**](../platform/toolkits/infrastructure-networking/storage/module-16.3-longhorn/) | Сховище | Легке розподілене блокове сховище з резервним копіюванням та аварійним відновленням |
| [**Планування GPU**](../platform/toolkits/data-ai-platforms/ml-platforms/module-9.7-gpu-scheduling/) | ML-платформи | NVIDIA GPU Operator, time-slicing, MIG, моніторинг |
| [**Поглиблене DNS**](/uk/k8s/cks/part2-cluster-hardening/module-2.1-rbac-deep-dive/) | Мережі | Налаштування CoreDNS, external-dns, оптимізація ndots |
| [**MetalLB**](../platform/toolkits/infrastructure-networking/networking/module-5.4-metallb/) | Мережі | Балансування навантаження для bare-metal — режими L2 та BGP |
| [**SPIFFE/SPIRE**](/uk/platform/toolkits/security-quality/code-quality/module-12.5-trivy/) | Безпека | Криптографічна ідентифікація навантажень для мереж з нульовою довірою |

### Узгодження з іспитом CKS

Перевірено наші модулі CKS відповідно до оновлення іспиту CNCF у жовтні 2024 та заповнено виявлені прогалини:
- Додано **шифрування Cilium Pod-to-Pod** (WireGuard/IPsec) до модуля мережевих політик
- Додано розділ **KubeLinter** до модуля статичного аналізу
- Оновлено передумову CKS: CKA більше не повинен бути активним — достатньо складеного будь-коли

### Перевірка якості («Випробування KubeDojo»)

Кожен модуль у KubeDojo був перевірений **Gemini AI** як рецензент-опонент:

- **329 модулів перевірено** у 4 фазах
- **95%+ отримали 9.5–10/10** за «Шкалою Доджо» (Перевірка настрою, Захист від новачків, Живий тест, Фактор запам'ятовуваності)
- **7 модулів покращено** з драматичними вступами, виправлено сухий «академічний» тон
- **1 заготовку розширено** з 43 рядків до 788 рядків (CKA Networking Data Path)
- Старіші модулі передумов підтягнуто до якості новіших модулів платформи

### Співпраця Claude–Gemini

Це оновлення було створено завдяки новаторській **мульти-ШІ співпраці**:
- **Claude** (Opus 4.6) відповідав за реалізацію — написання модулів, оновлення контенту, керування Issue
- **Gemini** (3 Flash) виступав як рецензент-опонент — виявляв технічні помилки, позначав сухий контент, пропонував покращення
- Комунікація через **ai_agent_bridge** — брокер повідомлень на базі SQLite для структурованих процесів рецензування
- Кожне Issue було перевірене Gemini перед закриттям
- Gemini виявив 2 технічні неточності (версіонування StatefulSet, значення trafficDistribution), які були виправлені до злиття

### У цифрах

| Показник | Кількість |
|----------|-----------|
| Нових модулів | 18 |
| Оновлених модулів | 30+ |
| Модулів перевірено на якість | 329 |
| Створено й закрито Issue на GitHub | 25 |
| Рядків нового контенту | ~12 000 |
| Загальна кількість модулів | 329 |
| Треків | 10 (CKA, CKAD, CKS, KCNA, KCSA, CNPE, Platform, Linux, IaC, Prerequisites) |

---

## Грудень 2025 — Початковий випуск

KubeDojo стартував із 311 модулями, що охоплюють усі 5 сертифікацій Kubestronaut, а також платформну інженерію, Linux та поглиблене вивчення IaC. Повну історію проєкту дивіться у [журналі комітів](https://github.com/kube-dojo/kube-dojo.github.io/commits/main).
