# Модуль 1.5: CRD та Оператори — розширення Kubernetes

> **Складність**: `[MEDIUM]` — нове в CKA 2025
>
> **Час на виконання**: 35-45 хвилин
>
> **Передумови**: Модуль 1.1 (розуміння площини управління)

---

## Чому цей модуль важливий

CRD та Оператори є **новими в навчальній програмі CKA 2025**.

Kubernetes постачається з вбудованими ресурсами: Поди, Деплойменти, Сервіси. Але що, якщо вам потрібен ресурс "Database", який автоматично обробляє резервні копії, аварійне перемикання та масштабування? Що, якщо ви хочете ресурс "Certificate", який автоматично поновлюється з Let's Encrypt?

Custom Resource Definitions (CRD) дозволяють створювати нові типи ресурсів. Оператори — це контролери, які керують цими користувацькими ресурсами. Разом вони є способом розширення екосистеми Kubernetes за межі ядра.

Саме так Prometheus, Cert-Manager, ArgoCD та сотні інших інструментів інтегруються з Kubernetes. Розуміння CRD та Операторів є необхідним для роботи з сучасним Kubernetes.

> **Аналогія з будівельними блоками**
>
> Уявіть Kubernetes як набір LEGO. Він постачається зі стандартними блоками (Поди, Сервіси). CRD — це користувацькі блоки, які ви проєктуєте самостійно — блок "Database", блок "Certificate". Оператори — це інструкції зі збирання, які знають, як поєднати ці блоки у працюючі системи. Ви не будуєте вручну — оператор слідує інструкціям автоматично.

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Розуміти, що таке CRD та Оператори
- Створювати та керувати Custom Resource Definitions
- Створювати екземпляри користувацьких ресурсів
- Розуміти патерн Оператора
- Працювати з поширеними операторами (cert-manager, prometheus)

---

## Частина 1: Custom Resource Definitions (CRD)

### 1.1 Що таке CRD?

CRD розширює API Kubernetes новим типом ресурсу.

```
Вбудовані ресурси:              Користувацькі ресурси (через CRD):
├── Pod                          ├── Certificate (cert-manager)
├── Deployment                   ├── Prometheus (prometheus-operator)
├── Service                      ├── PostgreSQL (postgres-operator)
├── ConfigMap                    ├── VirtualService (istio)
└── ...                          └── ВашВласнийРесурс
```

Після створення CRD ви можете використовувати `kubectl` для керування новим типом ресурсу так само, як вбудованими ресурсами:

```bash
# Вбудований ресурс
kubectl get pods

# Користувацький ресурс (після встановлення CRD)
kubectl get certificates
kubectl get prometheuses
kubectl get postgresqls
```

### 1.2 Структура CRD

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com    # <plural>.<group>
spec:
  group: stable.example.com            # API група
  versions:
    - name: v1                         # Версія API
      served: true                     # Увімкнути цю версію
      storage: true                    # Зберігати в etcd
      schema:
        openAPIV3Schema:               # Схема валідації
          type: object
          properties:
            spec:
              type: object
              properties:
                cronSpec:
                  type: string
                image:
                  type: string
                replicas:
                  type: integer
  scope: Namespaced                    # або Cluster
  names:
    plural: crontabs                   # kubectl get crontabs
    singular: crontab                  # kubectl get crontab
    kind: CronTab                      # Kind у YAML
    shortNames:
      - ct                             # kubectl get ct
```

### 1.3 Створення CRD

```bash
# Застосувати CRD
kubectl apply -f crontab-crd.yaml

# Перевірити, що він створений
kubectl get crd crontabs.stable.example.com

# Тепер можна створювати екземпляри
kubectl get crontabs
# No resources found (очікувано — ми ще не створили жодного)
```

> **Чи знали ви?**
>
> CRD зберігаються в etcd так само, як вбудовані ресурси. Після створення вони стають повноцінними громадянами API. Сервер API автоматично обробляє валідацію, RBAC та механізми спостереження (watch).

---

## Частина 2: Створення користувацьких ресурсів

### 2.1 Екземпляр користувацького ресурсу

Після існування CRD ви можете створювати екземпляри:

```yaml
apiVersion: stable.example.com/v1
kind: CronTab
metadata:
  name: my-cron-job
  namespace: default
spec:
  cronSpec: "* * * * */5"
  image: my-awesome-cron-image
  replicas: 3
```

```bash
kubectl apply -f my-crontab.yaml
kubectl get crontabs
kubectl get ct    # Використовуючи скорочену назву
kubectl describe crontab my-cron-job
```

### 2.2 Операції з користувацькими ресурсами

Усі стандартні операції kubectl працюють:

```bash
# Створити
kubectl apply -f crontab.yaml

# Перелічити
kubectl get crontabs -A

# Описати
kubectl describe crontab my-cron-job

# Редагувати
kubectl edit crontab my-cron-job

# Видалити
kubectl delete crontab my-cron-job

# Спостерігати
kubectl get crontabs -w

# Отримати як YAML
kubectl get crontab my-cron-job -o yaml
```

---

## Частина 3: Патерн Оператора

### 3.1 Що таке Оператор?

CRD сам по собі нічого не робить — це лише сховище даних. **Оператор** — це контролер, який:
1. Спостерігає за змінами в користувацьких ресурсах
2. Виконує дії для узгодження бажаного стану з фактичним

```
┌────────────────────────────────────────────────────────────────┐
│                     Патерн Оператора                            │
│                                                                 │
│   Ви створюєте:                                                │
│   ┌─────────────────────────────────────────┐                  │
│   │ apiVersion: databases.example.com/v1    │                  │
│   │ kind: PostgreSQL                        │                  │
│   │ spec:                                   │                  │
│   │   version: "15"                         │                  │
│   │   replicas: 3                           │                  │
│   │   storage: 100Gi                        │                  │
│   └─────────────────────────────────────────┘                  │
│                          │                                      │
│                          ▼                                      │
│   ┌─────────────────────────────────────────┐                  │
│   │         Оператор (Контролер)             │                  │
│   │                                          │                  │
│   │   Спостерігає за ресурсами PostgreSQL    │                  │
│   │   Створює:                               │                  │
│   │   • StatefulSet з 3 реплікаами           │                  │
│   │   • PVC для 100Gi сховища               │                  │
│   │   • Сервіси для з'єднань                │                  │
│   │   • Секрети для облікових даних          │                  │
│   │   • ConfigMap для конфігурації           │                  │
│   │                                          │                  │
│   │   Керує:                                 │                  │
│   │   • Автоматичне аварійне перемикання     │                  │
│   │   • Резервні копії                       │                  │
│   │   • Оновлення версій                     │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Компоненти Оператора

Оператор зазвичай містить:
1. **CRD** — визначають типи користувацьких ресурсів
2. **Контролер** — Деплоймент, що виконує логіку узгодження
3. **RBAC** — дозволи для керування ресурсами
4. **Вебхуки** (опціонально) — валідація та мутація

### 3.3 Цикл узгодження

```
┌─────────────────────────────────────────────────────────────┐
│                    Цикл узгодження                           │
│                                                              │
│   ┌───────────────┐                                         │
│   │ Спостерігати  │◄────────────────────────────────────┐   │
│   └──────┬────────┘                                     │   │
│          │ Подія: ресурс PostgreSQL змінився             │   │
│          ▼                                              │   │
│   ┌───────────────┐                                     │   │
│   │   Прочитати   │ Отримати поточний стан з кластера   │   │
│   └──────┬────────┘                                     │   │
│          │                                              │   │
│          ▼                                              │   │
│   ┌───────────────┐                                     │   │
│   │   Порівняти   │ Поточний стан vs. Бажаний стан      │   │
│   └──────┬────────┘                                     │   │
│          │                                              │   │
│          ▼                                              │   │
│   ┌───────────────┐                                     │   │
│   │    Діяти      │ Створити/Оновити/Видалити ресурси   │   │
│   └──────┬────────┘                                     │   │
│          │                                              │   │
│          └──────────────────────────────────────────►───┘   │
│                  Повторювати безкінечно                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

> **Історія з практики: База даних, що самовідновлюється**
>
> Одна компанія використовувала оператор PostgreSQL. О 3-й ночі основний вузол бази даних вийшов з ладу. Без втручання людини оператор виявив збій, підвищив репліку до основної, оновив ендпоінти сервісів і повідомив команду через Slack. Коли черговий інженер перевірив, все вже працювало. Загальний час простою: 90 секунд. Без оператора це було б 30-хвилинне ручне аварійне перемикання.

---

## Частина 4: Робота з реальними Операторами

### 4.1 cert-manager

cert-manager автоматизує керування TLS-сертифікатами:

```bash
# Встановити cert-manager (включає CRD)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Перевірити створені CRD
kubectl get crd | grep cert-manager
# certificates.cert-manager.io
# clusterissuers.cert-manager.io
# issuers.cert-manager.io
# ...
```

```yaml
# Створити ресурс Certificate
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: myapp-tls
  namespace: default
spec:
  secretName: myapp-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - myapp.example.com
```

Оператор cert-manager спостерігає за цим Certificate і:
1. Запитує сертифікат у Let's Encrypt
2. Завершує ACME challenge
3. Зберігає сертифікат у вказаному Secret
4. Автоматично поновлює перед закінченням терміну дії

### 4.2 Prometheus Operator

```bash
# Перевірити CRD Prometheus
kubectl get crd | grep monitoring.coreos.com
# prometheuses.monitoring.coreos.com
# servicemonitors.monitoring.coreos.com
# alertmanagers.monitoring.coreos.com
```

```yaml
# Створити екземпляр Prometheus
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: main
  namespace: monitoring
spec:
  replicas: 2
  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      team: frontend
```

### 4.3 Виявлення встановленого

```bash
# Перелічити всі CRD у кластері
kubectl get crd

# Переглянути всі користувацькі ресурси певного типу
kubectl get certificates -A

# Перевірити, чи працює оператор
kubectl get pods -A | grep operator
kubectl get pods -A | grep -E "cert-manager|prometheus"
```

---

## Частина 5: Поглиблене вивчення CRD

### 5.1 Валідація схеми

CRD можуть забезпечувати валідацію:

```yaml
schema:
  openAPIV3Schema:
    type: object
    required:
      - spec
    properties:
      spec:
        type: object
        required:
          - cronSpec
          - image
        properties:
          cronSpec:
            type: string
            pattern: '^(\d+|\*)(/\d+)?(\s+(\d+|\*)(/\d+)?){4}$'
          image:
            type: string
          replicas:
            type: integer
            minimum: 1
            maximum: 10
            default: 1
```

Тепер невалідні ресурси відхиляються:

```bash
# Це не пройде валідацію
kubectl apply -f bad-crontab.yaml
# Error: spec.replicas: Invalid value: 15: must be <= 10
```

### 5.2 Додаткові колонки виводу

Показати користувацькі колонки в `kubectl get`:

```yaml
versions:
  - name: v1
    additionalPrinterColumns:
      - name: Schedule
        type: string
        jsonPath: .spec.cronSpec
      - name: Replicas
        type: integer
        jsonPath: .spec.replicas
      - name: Age
        type: date
        jsonPath: .metadata.creationTimestamp
```

```bash
kubectl get crontabs
# NAME          SCHEDULE       REPLICAS   AGE
# my-cron-job   * * * * */5    3          5m
```

### 5.3 Підресурси

Увімкнення підресурсів status та scale:

```yaml
versions:
  - name: v1
    subresources:
      status: {}           # Увімкнути підресурс /status
      scale:               # Увімкнути kubectl scale
        specReplicasPath: .spec.replicas
        statusReplicasPath: .status.replicas
```

```bash
# Тепер це працює
kubectl scale crontab my-cron-job --replicas=5
```

---

## Частина 6: Namespaced vs. Cluster-Scoped

### 6.1 Типи області видимості

```yaml
# Namespaced (за замовчуванням)
scope: Namespaced
# Ресурси існують всередині простору імен
# kubectl get crontabs -n myapp

# Cluster-scoped
scope: Cluster
# Ресурси є загальнокластерними (як Nodes, PV)
# kubectl get clusterissuers (приклад cert-manager)
```

### 6.2 Коли використовувати кожен

| Область видимості | Коли використовувати | Приклади |
|-------------------|---------------------|----------|
| **Namespaced** | Ресурс належить команді/додатку | Certificate, Database, Application |
| **Cluster** | Ресурс є спільним/глобальним | ClusterIssuer, StorageProfile |

---

## Частина 7: Операції, релевантні для іспиту

### 7.1 Перевірка існуючих CRD

```bash
# Перелічити всі CRD
kubectl get crd

# Отримати деталі про CRD
kubectl describe crd certificates.cert-manager.io

# Побачити повне визначення CRD
kubectl get crd certificates.cert-manager.io -o yaml
```

### 7.2 Робота з користувацькими ресурсами

```bash
# Перелічити користувацькі ресурси
kubectl get <resource-name> -A

# Отримати конкретний ресурс
kubectl get certificate my-cert -o yaml

# Редагувати користувацький ресурс
kubectl edit certificate my-cert

# Видалити користувацький ресурс
kubectl delete certificate my-cert
```

### 7.3 Пошук ресурсів API

```bash
# Перелічити всі типи ресурсів (включно з користувацькими)
kubectl api-resources

# Фільтрувати за групою
kubectl api-resources --api-group=cert-manager.io

# Показати, чи є namespaced
kubectl api-resources --namespaced=true
```

---

## Чи знали ви?

- **OperatorHub.io** каталогізує сотні операторів. Шукайте те, що вам потрібно, перш ніж створювати власний.

- **Operator SDK** та **Kubebuilder** — це фреймворки для створення операторів на Go. Ви також можете створювати оператори на Python, Ansible або Helm.

- **OLM (Operator Lifecycle Manager)** керує встановленням та оновленням операторів. Саме його OpenShift використовує для встановлення операторів.

- **Фіналізатори** дозволяють користувацьким ресурсам запобігати видаленню, поки очищення не завершено. Саме так оператори забезпечують належне резервне копіювання баз даних перед видаленням.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Створення CR перед CRD | "resource not found" | Завжди встановлюйте CRD спочатку |
| Неправильна API група/версія | Валідація YAML не проходить | Перевірте CRD на правильний apiVersion |
| Забули встановити оператор | CR нічого не робить | CRD сам по собі не діє; потрібен оператор |
| Видалення CRD з існуючими CR | Втрата даних | Спочатку видаліть CR, потім CRD |
| Неправильне припущення про область видимості | Ресурс у неправильному місці | Перевірте область видимості CRD: Namespaced vs Cluster |

---

## Тест

1. **Яка різниця між CRD та CR?**
   <details>
   <summary>Відповідь</summary>
   **CRD (Custom Resource Definition)** визначає новий тип ресурсу — як шаблон. **CR (Custom Resource)** — це екземпляр цього типу — як об'єкт з шаблону. CRD визначає "Certificate", CR створює "my-app-certificate".
   </details>

2. **CRD встановлено, але при створенні CR нічого не відбувається. Чому?**
   <details>
   <summary>Відповідь</summary>
   CRD самі по собі є лише сховищем даних. **Оператор** (контролер) повинен працювати, щоб спостерігати за CR і виконувати дії. Без оператора CR зберігаються в etcd, але ніщо їх не узгоджує.
   </details>

3. **Як знайти всі типи користувацьких ресурсів у кластері?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get crd` перелічує всі Custom Resource Definitions. Для всіх типів ресурсів (вбудованих та користувацьких): `kubectl api-resources`.
   </details>

4. **Що означає `scope: Namespaced` проти `scope: Cluster` для CRD?**
   <details>
   <summary>Відповідь</summary>
   **Namespaced**: ресурси існують всередині простору імен, потрібно вказувати `-n` при запитах, можуть мати однакову назву в різних просторах імен.
   **Cluster**: ресурси є загальнокластерними, простір імен не потрібен, назви повинні бути унікальними в межах кластера.
   </details>

---

## Практична вправа

**Завдання**: Створити простий CRD та користувацькі ресурси.

**Кроки**:

1. **Створіть CRD для ресурсу "Website"**:
```bash
cat > website-crd.yaml << 'EOF'
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.stable.example.com
spec:
  group: stable.example.com
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required:
                - url
              properties:
                url:
                  type: string
                replicas:
                  type: integer
                  default: 1
      additionalPrinterColumns:
        - name: URL
          type: string
          jsonPath: .spec.url
        - name: Replicas
          type: integer
          jsonPath: .spec.replicas
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
  scope: Namespaced
  names:
    plural: websites
    singular: website
    kind: Website
    shortNames:
      - ws
EOF

kubectl apply -f website-crd.yaml
```

2. **Перевірте CRD**:
```bash
kubectl get crd websites.stable.example.com
kubectl api-resources | grep website
```

3. **Створіть екземпляр Website**:
```bash
cat > my-website.yaml << 'EOF'
apiVersion: stable.example.com/v1
kind: Website
metadata:
  name: company-site
  namespace: default
spec:
  url: https://example.com
  replicas: 3
EOF

kubectl apply -f my-website.yaml
```

4. **Працюйте з користувацьким ресурсом**:
```bash
# Перелічити вебсайти
kubectl get websites
kubectl get ws    # Скорочена назва

# Описати
kubectl describe website company-site

# Отримати як YAML
kubectl get website company-site -o yaml

# Редагувати
kubectl edit website company-site
```

5. **Створіть ще один вебсайт**:
```bash
cat > blog.yaml << 'EOF'
apiVersion: stable.example.com/v1
kind: Website
metadata:
  name: blog
spec:
  url: https://blog.example.com
  replicas: 2
EOF

kubectl apply -f blog.yaml
kubectl get ws
```

6. **Дослідіть встановлені оператори (якщо є)**:
```bash
# Перевірити cert-manager
kubectl get crd | grep cert-manager

# Перевірити prometheus operator
kubectl get crd | grep monitoring.coreos.com

# Перелічити всі CRD
kubectl get crd
```

7. **Очищення**:
```bash
kubectl delete website company-site blog
kubectl delete crd websites.stable.example.com
rm website-crd.yaml my-website.yaml blog.yaml
```

**Критерії успіху**:
- [ ] Вмію створювати CRD
- [ ] Вмію створювати екземпляри користувацьких ресурсів
- [ ] Вмію запитувати користувацькі ресурси через kubectl
- [ ] Розумію зв'язок між CRD та CR
- [ ] Знаю, як знайти CRD у кластері

---

## Практичні вправи

### Вправа 1: Дослідження CRD (Ціль: 3 хвилини)

Дослідіть існуючі CRD у вашому кластері:

```bash
# Перелічити всі CRD
kubectl get crd

# Отримати деталі про конкретний CRD
kubectl get crd <crd-name> -o yaml | head -50

# Перелічити екземпляри CRD
kubectl get <resource-name> -A

# Описати CRD
kubectl describe crd <crd-name>
```

### Вправа 2: Створення простого CRD (Ціль: 5 хвилин)

```bash
# Створити CRD
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: apps.example.com
spec:
  group: example.com
  names:
    kind: App
    listKind: AppList
    plural: apps
    singular: app
    shortNames:
      - ap
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                image:
                  type: string
                replicas:
                  type: integer
EOF

# Перевірити, що CRD існує
kubectl get crd apps.example.com

# Створити екземпляр
cat << 'EOF' | kubectl apply -f -
apiVersion: example.com/v1
kind: App
metadata:
  name: my-app
spec:
  image: nginx:1.25
  replicas: 3
EOF

# Запитати за скороченою назвою
kubectl get ap

# Очищення
kubectl delete app my-app
kubectl delete crd apps.example.com
```

### Вправа 3: CRD з валідацією (Ціль: 5 хвилин)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.stable.example.com
spec:
  group: stable.example.com
  names:
    kind: Database
    plural: databases
    singular: database
    shortNames:
      - db
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          required:
            - spec
          properties:
            spec:
              type: object
              required:
                - engine
                - version
              properties:
                engine:
                  type: string
                  enum:
                    - postgres
                    - mysql
                    - mongodb
                version:
                  type: string
                storage:
                  type: string
                  default: "10Gi"
EOF

# Спроба створити невалідний ресурс (повинна завершитися помилкою)
cat << 'EOF' | kubectl apply -f -
apiVersion: stable.example.com/v1
kind: Database
metadata:
  name: invalid-db
spec:
  engine: oracle  # Немає в enum!
  version: "14"
EOF

# Створити валідний ресурс
cat << 'EOF' | kubectl apply -f -
apiVersion: stable.example.com/v1
kind: Database
metadata:
  name: prod-db
spec:
  engine: postgres
  version: "14"
EOF

# Очищення
kubectl delete database prod-db
kubectl delete crd databases.stable.example.com
```

### Вправа 4: Пошук ресурсів, керованих операторами (Ціль: 3 хвилини)

```bash
# Знайти CRD від популярних операторів
kubectl get crd | grep -E "cert-manager|prometheus|istio|argocd"

# Якщо встановлено cert-manager
kubectl get certificates -A
kubectl get clusterissuers

# Якщо встановлено prometheus operator
kubectl get servicemonitors -A
kubectl get prometheusrules -A

# Загальне: знайти всі користувацькі ресурси
kubectl api-resources --api-group="" | head -20
kubectl api-resources | grep -v "^NAME"
```

### Вправа 5: Підресурс status у CRD (Ціль: 5 хвилин)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: tasks.work.example.com
spec:
  group: work.example.com
  names:
    kind: Task
    plural: tasks
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      subresources:
        status: {}
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                command:
                  type: string
            status:
              type: object
              properties:
                phase:
                  type: string
                completedAt:
                  type: string
EOF

# Створити завдання
cat << 'EOF' | kubectl apply -f -
apiVersion: work.example.com/v1
kind: Task
metadata:
  name: build-job
spec:
  command: "make build"
EOF

# Переглянути завдання
kubectl get task build-job -o yaml

# Очищення
kubectl delete task build-job
kubectl delete crd tasks.work.example.com
```

### Вправа 6: Усунення несправностей — CRD не знайдено (Ціль: 3 хвилини)

```bash
# Спроба створити ресурс для неіснуючого CRD
cat << 'EOF' | kubectl apply -f -
apiVersion: nonexistent.example.com/v1
kind: Widget
metadata:
  name: test
spec:
  size: large
EOF

# Error: no matches for kind "Widget"

# Діагностика
kubectl get crd | grep widget  # Нічого
kubectl api-resources | grep -i widget  # Нічого

# Рішення: CRD повинен бути створений перед ресурсами
# Спочатку створіть CRD, потім ресурс
```

### Вправа 7: Виклик — створіть власний CRD

Спроєктуйте та реалізуйте CRD для ресурсу "Backup" з:

- Група: `backup.example.com`
- Обов'язкові поля: `source`, `destination`, `schedule` (формат cron)
- Необов'язкове поле: `retention` (integer, за замовчуванням 7)
- Валідація: `schedule` має бути рядком

```bash
# ВАШЕ ЗАВДАННЯ: Створіть CRD та зразок ресурсу Backup
```

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backups.backup.example.com
spec:
  group: backup.example.com
  names:
    kind: Backup
    plural: backups
    shortNames:
      - bk
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          required:
            - spec
          properties:
            spec:
              type: object
              required:
                - source
                - destination
                - schedule
              properties:
                source:
                  type: string
                destination:
                  type: string
                schedule:
                  type: string
                retention:
                  type: integer
                  default: 7
EOF

cat << 'EOF' | kubectl apply -f -
apiVersion: backup.example.com/v1
kind: Backup
metadata:
  name: daily-db-backup
spec:
  source: /data/postgres
  destination: s3://backups/postgres
  schedule: "0 2 * * *"
  retention: 14
EOF

kubectl get bk
kubectl delete backup daily-db-backup
kubectl delete crd backups.backup.example.com
```

</details>

---

## Наступний модуль

[Модуль 1.6: RBAC](module-1.6-rbac.uk.md) — контроль доступу на основі ролей для захисту вашого кластера.
