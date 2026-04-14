---
title: "KCA - Kyverno Certified Associate"
sidebar:
  order: 0
  label: "KCA"
slug: uk/k8s/kca/index
en_commit: "7e01a3686e7eed601474920f79697275be77476d"
en_file: "src/content/docs/k8s/kca/index.md"
---
> **Тестовий іспит** | 90 хвилин | Прохідний бал: 75% | $250 USD | **Запущено у 2024 році**

## Огляд

KCA (Kyverno Certified Associate) підтверджує ваші навички використання Kyverno для керування політиками Kubernetes. На відміну від CKA/CKS, які базуються на виконанні практичних завдань, KCA — це **тестовий іспит** (multiple-choice). Але нехай це не вводить вас в оману: запитання насичені сценаріями та вимагають вміння читати, писати й налагоджувати реальні YAML-політики Kyverno.

**KubeDojo охоплює ~95% тем KCA** через наші існуючі треки Platform Engineering та CKS, а також два спеціалізовані модулі KCA, що розглядають розширені політики, операції CLI та керування політиками.

> **Чому KCA це важливо**: Kyverno — найпопулярніший YAML-орієнтований рушій політик в екосистемі Kubernetes. Оскільки організації переходять від підходу «розгортати швидко» до «розгортати безпечно», навички «політики як код» (policy-as-code) мають великий попит. KCA доводить, що ви можете забезпечувати управління (governance) без написання жодного рядка на Rego.

---

## Модулі, специфічні для KCA

Ці модулі охоплюють теми, що знаходяться між існуючим модулем KubeDojo про інструментарій Kyverno та вимогами іспиту KCA:

| # | Модуль | Тема | Охоплені домени |
|---|--------|-------|-----------------|
| 1 | [Модуль 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/) | verifyImages, вирази CEL, політики очищення, складні validate/mutate/generate | Домен 5 (32%) |
| 2 | [Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) | kyverno apply/test/jp, винятки з політик, метрики, розгортання в режимі HA | Домени 2, 3, 6 (40%) |

---

## Домени іспиту

| Домен | Вага | Покриття KubeDojo |
|--------|--------|-------------------|
| Основи Kyverno | 18% | Відмінне (модуль інструментарію Kyverno) |
| Встановлення, налаштування та оновлення | 18% | Добре (модуль Kyverno + модулі CKS) |
| Kyverno CLI | 12% | Відмінне ([Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) — apply/test/jp) |
| Застосування політик | 10% | Відмінне (модулі Kyverno + OPA) |
| Написання політик | 32% | Відмінне ([Модуль 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/) — CEL, verifyImages, cleanup) |
| Керування політиками | 10% | Відмінне ([Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) — exceptions, metrics, HA) |

---

## Домен 1: Основи Kyverno (18%)

### Компетенції
- **Зрозуміти** роль Kyverno як Kubernetes admission controller
- Типи політик: ClusterPolicy проти Policy (з обмеженням простору імен)
- Структура YAML політики Kyverno
- Як Kyverno інтегрується з Kubernetes API server через вебхуки (webhooks)

### Шлях навчання KubeDojo

**Основний модуль:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | Архітектура, модель політик, validate/mutate/generate | Пряма |
| [OPA & Gatekeeper 4.2](../../platform/toolkits/security-quality/security-tools/module-4.2-opa-gatekeeper/) | Концепції рушіїв політик, шаблони admission control | Контекст |

**Основи Kubernetes (admission controllers):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [CKS Admission Controllers](../../k8s/cks/part5-supply-chain-security/module-5.4-admission-controllers/) | ValidatingWebhookConfiguration, MutatingWebhookConfiguration | Пряма |
| [CKS Pod Security Admission](../../k8s/cks/part4-microservice-vulnerabilities/module-4.2-pod-security-admission/) | Вбудований admission control, PSA проти рушіїв політик | Контекст |
| [CKS API Server Security](../../k8s/cks/part2-cluster-hardening/module-2.3-api-server-security/) | Ланцюжок допуску (admission chain) API server | Контекст |

### Ключові концепції для засвоєння
- **Потік admission webhook**: API-запит -> мутуючі вебхуки -> валідуючі вебхуки -> збереження в etcd
- **ClusterPolicy** застосовується на рівні всього кластера; **Policy** має обмеження простору імен (однаковий синтаксис, різна область дії)
- Kyverno запускається як Deployment з кількома репліками, а не як DaemonSet
- Політики — це Kubernetes CRD, якими можна керувати через kubectl, GitOps, Helm як будь-яким іншим ресурсом

---

## Домен 2: Встановлення, налаштування та оновлення (18%)

### Компетенції
- **Встановити** Kyverno через Helm чарти
- **Зрозуміти** CRD Kyverno та їхній життєвий цикл
- **Налаштувати** RBAC для сервісних акаунтів (service accounts) Kyverno
- **Застосувати** шаблони розгортання високої доступності (HA)
- **Оновити** Kyverno між версіями

### Шлях навчання KubeDojo

**Kyverno-специфічні:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | Встановлення, значення Helm (values), базове налаштування | Пряма |

**Підтримуючі концепції Kubernetes:**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [CKS Kubernetes Upgrades](../../k8s/cks/part2-cluster-hardening/module-2.4-kubernetes-upgrades/) | Стратегії оновлення, розбіжність версій (version skew) | Контекст |
| [Helm & Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Шаблони встановлення, оновлення та відкату Helm | Пряма |

### Ключові концепції для засвоєння
- **Встановлення через Helm**: `helm install kyverno kyverno/kyverno -n kyverno --create-namespace`
- **Режим HA**: 3 репліки, pod anti-affinity, окремі контролери для вебхуків та фонових завдань
- **CRD**: ClusterPolicy, Policy, ClusterPolicyReport, PolicyReport, AdmissionReport, UpdateRequest
- **RBAC**: Kyverno потребує дозволів для спостереження (watch) та переліку (list) ресурсів, якими він керує
- **Налаштування вебхука**: `failurePolicy: Fail` проти `Ignore` — критично для стабільності продакшену
- **Фільтри ресурсів**: Виключення простору імен kyverno та системних ресурсів з оцінки політик

---

## Домен 3: Kyverno CLI (12%)

### Компетенції
- **Використовувати** `kyverno apply` для офлайн-тестування політик на ресурсах
- **Використовувати** `kyverno test` для юніт-тестування політик
- **Використовувати** `kyverno jp` для налагодження виразів JMESPath
- **Інтегрувати** Kyverno CLI в CI/CD конвеєри

### Шлях навчання KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | Основи CLI, інтеграція в CI/CD | Часткова |
| [Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) | kyverno apply/test/jp, винятки з політик, метрики, розгортання в режимі HA | Пряма |
| [DevSecOps 4.3](../../platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd/) | Безпека в CI/CD конвеєрах (шаблон policy-as-code) | Контекст |
| [CKS Static Analysis](../../k8s/cks/part5-supply-chain-security/module-5.3-static-analysis/) | Концепції сканування перед розгортанням | Контекст |

### Ключові концепції для засвоєння

```bash
# Apply a policy against a resource (offline, no cluster needed)
kyverno apply policy.yaml --resource deployment.yaml

# Run policy test suites
kyverno test ./tests/

# Debug JMESPath expressions (used in preconditions and variables)
kyverno jp query "request.object.metadata.labels.app" -i resource.json

# CI/CD pipeline usage -- fail the build if policies are violated
kyverno apply policies/ --resource manifests/ --detailed-results
```

- **`kyverno apply`**: Тестує політики на ресурсах без кластера. Важливо для підходу «shift-left».
- **`kyverno test`**: Запускає набори тестів, визначені в YAML. Кожен тест вказує політику, ресурс та очікуваний результат (pass/fail/skip).
- **`kyverno jp`**: Інтерактивний інструмент для запитів JMESPath. Безцінний для налагодження складних умов відповідності (match conditions).
- **Структура файлу тесту**: `kyverno-test.yaml` з полями `policies:`, `resources:` та `results:`.

---

## Домен 4: Застосування політик (10%)

### Компетенції
- **Використовувати** блоки `match` та `exclude` для вибору ресурсів
- **Таргетувати** конкретні типи ресурсів (kinds), простори імен, мітки (labels) та анотації
- **Застосовувати** preconditions для умовного виконання політик
- **Впорядковувати** політики та вирішувати конфлікти

### Шлях навчання KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | match/exclude, вибір ресурсів | Пряма |
| [OPA & Gatekeeper 4.2](../../platform/toolkits/security-quality/security-tools/module-4.2-opa-gatekeeper/) | Селектори обмежень (порівняння) | Контекст |

### Ключові концепції для засвоєння

```yaml
# Match/Exclude patterns
spec:
  rules:
  - name: require-labels
    match:
      any:
      - resources:
          kinds:
          - Pod
          namespaces:
          - production
          - staging
          selector:
            matchLabels:
              app.kubernetes.io/managed-by: helm
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
      - clusterRoles:
          - cluster-admin
```

- **`match.any`** = логіка АБО (відповідність будь-якій умові); **`match.all`** = логіка І (відповідність усім умовам)
- **`exclude`** має пріоритет над `match` — завжди обробляється після match
- **Preconditions**: Використовуйте вирази JMESPath для умовної логіки (`{{ request.object.metadata.annotations.\"skip-policy\" }}`)
- **Фільтри ресурсів**: Глобальні фільтри в Kyverno ConfigMap виключають ресурси з оцінки всіх політик

---

## Домен 5: Написання політик (32%)

> Це найбільший домен. Він вимагає глибокої практичної підготовки.

### Компетенції
- **Писати** правила **validate** (заборона невідповідних ресурсів)
- **Писати** правила **mutate** (автоматичне виправлення ресурсів при допуску)
- **Писати** правила **generate** (автоматичне створення супутніх ресурсів)
- **Писати** правила **verifyImages** (забезпечення підписів образів та атестацій)
- **Використовувати** **вирази CEL** у політиках (альтернатива JMESPath у Kubernetes 1.30+)
- **Писати** **політики очищення (cleanup)** (видалення ресурсів за TTL)

### Шлях навчання KubeDojo

**Добре висвітлено (validate, mutate, generate):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | Політики validate, mutate, generate з прикладами | Пряма |
| [Модуль 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/) | verifyImages, вирази CEL, політики очищення, складні шаблони | Пряма |
| [Security Mindset 4.1](../../platform/foundations/security-principles/module-4.1-security-mindset/) | Чому дотримання політик це важливо | Контекст |
| [Defense in Depth 4.2](../../platform/foundations/security-principles/module-4.2-defense-in-depth/) | Багатошарова модель безпеки | Контекст |

**Додаткова глибина (verifyImages, CEL, cleanup):**

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Supply Chain Security 4.4](../../platform/toolkits/security-quality/security-tools/module-4.4-supply-chain/) | Cosign, підпис образів, атестації (контекст verifyImages) | Пряма |
| [DevSecOps Supply Chain 4.4](../../platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security/) | Теорія ланцюжка постачання, SLSA, SBOM | Контекст |

### Ключові концепції для засвоєння

**Validate (заборона невідповідних ресурсів):**
```yaml
spec:
  validationFailureAction: Enforce  # Enforce = блок, Audit = warn only
  rules:
  - name: require-resource-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "CPU and memory limits are required."
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"
                cpu: "?*"
```

**Mutate (автоматичне виправлення при допуску):**
```yaml
spec:
  rules:
  - name: add-default-securitycontext
    match:
      any:
      - resources:
          kinds:
          - Pod
    mutate:
      patchStrategicMerge:
        spec:
          containers:
          - (name): "*"
            securityContext:
              runAsNonRoot: true
              readOnlyRootFilesystem: true
```

**Generate (автоматичне створення супутніх ресурсів):**
```yaml
spec:
  rules:
  - name: generate-networkpolicy
    match:
      any:
      - resources:
          kinds:
          - Namespace
    generate:
      kind: NetworkPolicy
      apiVersion: networking.k8s.io/v1
      name: default-deny-ingress
      namespace: "{{request.object.metadata.name}}"
      data:
        spec:
          podSelector: {}
          policyTypes:
          - Ingress
```

**verifyImages (забезпечення підписів образів) — розглядається в [Модулі 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/):**
```yaml
spec:
  rules:
  - name: verify-image-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "ghcr.io/myorg/*"
      attestors:
      - entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              ...
              -----END PUBLIC KEY-----
```

**Вирази CEL (альтернатива JMESPath) — розглядається в [Модулі 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/):**
```yaml
spec:
  rules:
  - name: check-replicas-cel
    match:
      any:
      - resources:
          kinds:
          - Deployment
    validate:
      cel:
        expressions:
        - expression: "object.spec.replicas >= 2"
          message: "Deployments must have at least 2 replicas"
```

**Політики очищення (видалення на основі TTL) — розглядається в [Модулі 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/):**
```yaml
apiVersion: kyverno.io/v2beta1
kind: ClusterCleanupPolicy
metadata:
  name: cleanup-stale-pods
spec:
  match:
    any:
    - resources:
        kinds:
        - Pod
        selector:
          matchLabels:
            environment: test
  conditions:
    any:
    - operator: Equals
      key: "{{ target.status.phase }}"
      value: Succeeded
  schedule: "*/30 * * * *"
```

### На чому зосередити увагу в цьому домені
1. Попрактикуйтеся писати всі 4 типи політики (validate, mutate, generate, verifyImages) з нуля
2. Зрозумійте різницю між `validationFailureAction: Enforce` та `Audit` — це часто перевіряється в тестах
3. Вивчіть основи JMESPath для підстановки змінних (`{{ request.object.* }}`)
4. Вивчіть вирази CEL — Kyverno додав підтримку CEL як альтернативу валідації на основі шаблонів
5. Зрозумійте політики очищення — видалення ресурсів за розкладом cron та умовами TTL

---

## Домен 6: Керування політиками (10%)

### Компетенції
- **Читати** та інтерпретувати PolicyReports та ClusterPolicyReports
- **Налаштовувати** винятки з політик (PolicyExceptions) для легітимних обходів
- **Моніторити** Kyverno за допомогою метрик (Prometheus)
- **Керувати** життєвим циклом політик (міграція audit -> enforce)

### Шлях навчання KubeDojo

| Модуль | Тема | Релевантність |
|--------|-------|-----------|
| [Kyverno 4.7](../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/) | Звіти про політики, режим аудиту | Пряма |
| [Prometheus](../../platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) | Метрики Prometheus, ServiceMonitor | Контекст |
| [SRE SLOs 1.2](../../platform/disciplines/core-platform/sre/module-1.2-slos/) | Вимірювання відповідності політикам як SLO | Контекст |
| [DevSecOps Fundamentals 4.1](../../platform/disciplines/reliability-security/devsecops/module-4.1-devsecops-fundamentals/) | Життєвий цикл policy-as-code | Контекст |

### Ключові концепції для засвоєння

**PolicyReports:**
```bash
# Перегляд результатів політик на рівні кластера
kubectl get clusterpolicyreport -o wide

# Перегляд результатів на рівні простору імен
kubectl get policyreport -n production -o wide

# Результати містять кількість pass/fail/warn/error/skip
```

**Винятки з політик (обхід для легітимних випадків):**
```yaml
apiVersion: kyverno.io/v2
kind: PolicyException
metadata:
  name: allow-privileged-cni
  namespace: kube-system
spec:
  exceptions:
  - policyName: disallow-privileged-containers
    ruleNames:
    - require-non-privileged
  match:
    any:
    - resources:
        kinds:
        - Pod
        namespaces:
        - kube-system
        names:
        - "calico-node-*"
```

**Метрики Kyverno (Prometheus):**
- `kyverno_admission_requests_total` — загальна кількість оброблених запитів допуску
- `kyverno_policy_results_total` — результати оцінки політик (pass/fail/error)
- `kyverno_policy_execution_duration_seconds` — затримка виконання політик
- Усі метрики доступні на `:8000/metrics` за замовчуванням

**Шаблон міграції Audit -> Enforce:**
1. Розгорніть політику з `validationFailureAction: Audit`
2. Відстежуйте PolicyReports на предмет порушень
3. Виправте існуючі порушення або створіть PolicyExceptions
4. Перемкніть на `validationFailureAction: Enforce`
5. Моніторте метрики допуску для виявлення заблокованих запитів

---

## Стратегія навчання

```
ШЛЯХ ПІДГОТОВКИ ДО KCA (рекомендований порядок)
══════════════════════════════════════════════════════════════

Тиждень 1: Основи та архітектура (18%)
├── Модуль Kyverno 4.7 у KubeDojo (почніть звідси)
├── Модуль CKS Admission Controllers
├── Модуль OPA & Gatekeeper (порівняння підходів)
└── Встановіть Kyverno у кластері kind

Тиждень 2: Встановлення та основи політик (18% + 10%)
├── Встановлення через Helm з кастомними values
├── Налаштування режиму HA (3 репліки)
├── Практика шаблонів match/exclude
├── Напишіть 10+ політик validate з нуля
└── Розгортання Kyverno через ArgoCD (шаблон GitOps)

Тиждень 3: Глибоке занурення у написання політик (32% — приділіть цьому найбільше часу!)
├── Політики Mutate (patchStrategicMerge, patchesJson6902)
├── Політики Generate (NetworkPolicy, ResourceQuota, LimitRange)
├── verifyImages з Cosign (використовуйте модуль supply chain у KubeDojo)
├── Вирази CEL (практика конвертації JMESPath -> CEL)
├── Політики очищення (видалення на основі TTL через cron)
└── Бібліотека політик Kyverno: вивчіть 20+ політик спільноти

Тиждень 4: CLI, керування та повторення (12% + 10%)
├── Команди CLI kyverno apply / test / jp
├── Написання наборів тестів kyverno-test.yaml
├── PolicyReports та ClusterPolicyReports
├── Винятки з політик для легітимних обходів
├── Метрики Prometheus та дашборди Grafana
└── Практичні питання іспиту, повторення слабких місць
```

---

## Поради до іспиту

- **Написання політик — це 32% іспиту** — ви ПОВИННІ вміти писати політики validate, mutate, generate та verifyImages по пам'яті
- **Знайте різницю між `Enforce` та `Audit`** — ця відмінність зустрічається в багатьох запитаннях
- **JMESPath — ваш друг** — практикуйте синтаксис змінних `{{ request.object.* }}`, доки він не стане автоматичним
- **CEL — це нова тема, що перевіряється** — іспит тестує підходи як з JMESPath, так і з CEL
- **Винятки з політик (Policy exceptions) проти exclude** — знайте, коли що використовувати (винятки для оперативних обходів; exclude для структурної фільтрації)
- **Команди CLI — це легкі бали** — запам'ятайте синтаксис `kyverno apply`, `kyverno test` та `kyverno jp`
- **Читайте бібліотеку політик** — багато екзаменаційних питань є варіаціями стандартних політик спільноти: [kyverno.io/policies](https://kyverno.io/policies/)

---

## Аналіз прогалин

Існуючі модулі KubeDojo разом із двома спеціалізованими модулями KCA тепер охоплюють ~95% навчальної програми KCA:

| Тема | Статус | Примітки |
|-------|--------|-------|
| Політики verifyImages | Охоплено | [Модуль 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/) — Cosign, атестації, перевірка образів |
| Вирази CEL у Kyverno | Охоплено | [Модуль 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/) — вирази валідації CEL |
| Політики очищення (cleanup) | Охоплено | [Модуль 1.1: Розширені політики Kyverno](module-1.1-advanced-kyverno-policies/) — ClusterCleanupPolicy, видалення за TTL |
| Глибоке занурення в Kyverno CLI | Охоплено | [Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) — команди apply, test, jp |
| Винятки з політик | Охоплено | [Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) — CRD PolicyException |
| Метрики Kyverno Prometheus | Охоплено | [Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) — метрики допуску, результатів та виконання політик |
| Деталі розгортання HA | Охоплено | [Модуль 1.2: Операції Kyverno та CLI](module-1.2-kyverno-operations-cli/) — репліки, anti-affinity, налаштування вебхука |

### Рекомендовані зовнішні ресурси
- **Документація Kyverno**: [kyverno.io/docs](https://kyverno.io/docs/) — авторитетне джерело для всіх доменів
- **Бібліотека політик Kyverno**: [kyverno.io/policies](https://kyverno.io/policies/) — 200+ готових політик для вивчення
- **Kyverno playground**: [playground.kyverno.io](https://playground.kyverno.io/) — тестуйте політики в браузері без кластера
- **Навчальна програма CNCF KCA**: [github.com/cncf/curriculum](https://github.com/cncf/curriculum) — офіційні цілі іспиту

---

## Супутні сертифікації

```
ШЛЯХ СЕРТИФІКАЦІЇ
══════════════════════════════════════════════════════════════

Початковий рівень:
├── KCNA (Cloud Native Associate) — основи K8s
├── KCSA (Security Associate) — основи безпеки
└── KCA (Kyverno Certified Associate) ← ВИ ТУТ

Професійний рівень:
├── CKA (K8s Administrator) — експлуатація кластерів
├── CKAD (K8s Developer) — розгортання застосунків
├── CKS (K8s Security Specialist) — зміцнення безпеки
└── CNPE (Platform Engineer) — платформа у масштабі

KCA природно поєднується з:
├── CKS — KCA дає глибину в рушіях політик, CKS охоплює ширшу безпеку
├── KCSA — KCA є практичним продовженням теорії KCSA
└── CNPE — Policy-as-code є базовою навичкою проектування платформ
```

KCA унікальний серед сертифікацій CNCF, оскільки зосереджений на **одному проекті** (Kyverno), а не на широкій галузі. Це робить його більш спеціалізованим, але й глибшим — очікуйте детальних запитань про специфічні функції Kyverno, яких не було б у CKS.
