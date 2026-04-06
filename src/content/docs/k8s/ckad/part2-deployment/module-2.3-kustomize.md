---
title: "Модуль 2.3: Kustomize"
slug: uk/k8s/ckad/part2-deployment/module-2.3-kustomize
sidebar: 
  order: 3
lab: 
  id: ckad-2.3-kustomize
  url: https://killercoda.com/kubedojo/scenario/ckad-2.3-kustomize
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
en_commit: "manual_sync"
---
> **Складність**: `[MEDIUM]` — кастомізація Kubernetes без шаблонів
>
> **Час на виконання**: 40–50 хвилин
>
> **Передумови**: Модуль 2.1 (Деплойменти), базове розуміння YAML

---

## Що ви зможете робити

Після завершення цього модуля ви зможете:
- **Побудувати** оверлеї Kustomize, що кастомізують базові ресурси для різних середовищ
- **Застосувати** патчі та трансформації за допомогою `kubectl apply -k` без модифікації оригінального YAML
- **Порівняти** Kustomize та Helm і обрати правильний інструмент для конкретного сценарію розгортання
- **Діагностувати** проблеми рендерингу Kustomize за допомогою `kubectl kustomize` для попереднього перегляду результату

---

## Чому цей модуль важливий

Kustomize дозволяє кастомізувати ресурси Kubernetes без шаблонів. Замість змінних і логіки (як у Helm) Kustomize використовує оверлеї та патчі для модифікації базових конфігурацій. Він вбудований у kubectl (`kubectl apply -k`), що робить його зручним для іспиту.

CKAD тестує Kustomize для:
- Створення та застосування кастомізацій
- Використання оверлеїв для різних середовищ
- Патчінг ресурсів
- Керування ConfigMaps та Secrets

> **Аналогія з наклейками**
>
> Уявіть, що купуєте ноутбук. Базовий ноутбук (базові ресурси) однаковий для всіх. Але ви додаєте наклейки, скіни та аксесуари (оверлеї), щоб зробити його своїм. Ви не перебудовуєте ноутбук — ви його кастомізуєте. Kustomize працює так само: зберігайте базові ресурси Kubernetes чистими, а потім застосовуйте оверлеї для dev/staging/prod.

---

## Основи Kustomize

### Ключові концепції

| Концепція | Опис |
|-----------|------|
| **Base** | Оригінальні, немодифіковані ресурси Kubernetes |
| **Overlay** | Кастомізації, що накладаються поверх бази |
| **Patch** | Модифікації конкретних полів |
| **kustomization.yaml** | Файл, що визначає, що кастомізувати |

### Як працює Kustomize

```
┌─────────────────────────────────────────────────────────┐
│                    Потік Kustomize                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  База                      Оверлей                      │
│  ┌─────────────┐        ┌─────────────┐                │
│  │ deployment  │───────▶│  + репліки  │                │
│  │   service   │        │  + env vars │                │
│  │  configmap  │        │  + мітки   │                │
│  └─────────────┘        └─────────────┘                │
│         │                     │                         │
│         └─────────┬───────────┘                         │
│                   ▼                                     │
│            ┌─────────────┐                              │
│            │ Об'єднані   │                              │
│            │  ресурси    │                              │
│            └─────────────┘                              │
│                   │                                     │
│                   ▼                                     │
│         kubectl apply -k ./                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Створення кастомізації

### Базова структура

```
my-app/
├── kustomization.yaml
├── deployment.yaml
└── service.yaml
```

### kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
```

### Застосування через kubectl

```bash
# Попередній перегляд того, що буде застосовано
kubectl kustomize ./my-app/

# Застосувати кастомізацію
kubectl apply -k ./my-app/

# Видалити ресурси
kubectl delete -k ./my-app/
```

---

## Типові трансформації

### Додати мітки до всіх ресурсів

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

commonLabels:
  app: my-app
  environment: production
```

### Додати анотації

```yaml
commonAnnotations:
  owner: team-platform
  managed-by: kustomize
```

### Додати префікс/суфікс до імені

```yaml
namePrefix: prod-
nameSuffix: -v1
```

Результат: `deployment` стає `prod-deployment-v1`

### Встановити простір імен

```yaml
namespace: production
```

Усі ресурси будуть розгорнуті в цьому просторі імен.

---

> **Stop and think**: Ви додаєте `namePrefix: prod-` до вашого kustomization.yaml. Deployment з іменем `web-app` посилається на Service з іменем `web-app`. Після застосування Kustomize, чи отримає посилання на Service всередині Deployment також префікс? Подумайте, що зламається, якщо цього не станеться.

## ConfigMaps та Secrets

### Генерація ConfigMap

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=info
  - API_URL=http://api.example.com
```

### Генерація ConfigMap з файлів

```yaml
configMapGenerator:
- name: app-config
  files:
  - config.properties
  - settings.json
```

### Генерація Secrets

```yaml
secretGenerator:
- name: db-credentials
  literals:
  - username=admin
  - password=secret123

# Або з файлів
secretGenerator:
- name: tls-certs
  files:
  - tls.crt
  - tls.key
  type: kubernetes.io/tls
```

> **Pause and predict**: Kustomize додає хеш-суфікс до згенерованих ConfigMaps (наприклад, `app-config-abc123`). Чому це корисно? Підказка: подумайте, що відбувається, коли ви оновлюєте ConfigMap і вам потрібно, щоб Pods підхопили зміни.

### Поведінка ConfigMap/Secret

За замовчуванням Kustomize додає хеш-суфікс до згенерованих ConfigMaps/Secrets:
- `app-config` стає `app-config-abc123`
- Посилання оновлюються автоматично

Вимкнути:
```yaml
generatorOptions:
  disableNameSuffixHash: true
```

---

## Образи

### Перевизначення тегів образів

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

images:
- name: nginx
  newTag: "1.21"

- name: myapp
  newName: my-registry.com/myapp
  newTag: v2.0.0
```

---

## Патчі

### Strategic Merge Patch

Додавання або модифікація полів:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 5
```

### Патч із файлу

```yaml
patches:
- path: increase-replicas.yaml
```

**increase-replicas.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
```

### JSON Patch

Для точних модифікацій:

```yaml
patches:
- target:
    kind: Deployment
    name: my-app
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 5
    - op: add
      path: /metadata/labels/version
      value: v2
```

> **Stop and think**: Ваш оверлей посилається на `../../base`, але базовий каталог був перейменований на `common`. Яку помилку ви отримаєте і як швидко ви зможете її діагностувати?

### Патч для всіх Деплойментів

```yaml
patches:
- target:
    kind: Deployment
  patch: |-
    - op: add
      path: /spec/template/spec/containers/0/resources
      value:
        limits:
          memory: 256Mi
          cpu: 200m
```

---

## Оверлеї

### Структура каталогів

```
my-app/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── overlays/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── prod/
│       └── kustomization.yaml
```

### Базовий kustomization.yaml

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
```

### Dev-оверлей

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: dev-
namespace: development

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 1

images:
- name: my-app
  newTag: dev-latest
```

### Prod-оверлей

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: prod-
namespace: production

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 5

images:
- name: my-app
  newTag: v1.2.3

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=warn
  - ENABLE_DEBUG=false
```

### Застосування оверлеїв

```bash
# Застосувати dev
kubectl apply -k overlays/dev/

# Застосувати prod
kubectl apply -k overlays/prod/

# Попередній перегляд
kubectl kustomize overlays/prod/
```

---

## Швидкий довідник для іспиту

```bash
# Попередній перегляд кастомізації
kubectl kustomize ./

# Застосувати кастомізацію
kubectl apply -k ./

# Видалити кастомізацію
kubectl delete -k ./

# Переглянути конкретний оверлей
kubectl kustomize overlays/prod/
```

### Мінімальний kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
```

### Типові кастомізації

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

namespace: my-namespace
namePrefix: prod-

commonLabels:
  app: my-app

images:
- name: nginx
  newTag: "1.21"

configMapGenerator:
- name: config
  literals:
  - KEY=value
```

---

## Чи знали ви?

- **Kustomize вбудований у kubectl** починаючи з версії 1.14. Вам не потрібно встановлювати нічого додаткового — просто використовуйте `kubectl apply -k`.

- **Хеш-суфікси на ConfigMaps/Secrets забезпечують поширення оновлень.** Коли вміст змінюється, хеш змінюється, створюючи новий ConfigMap. Деплойменти, що на нього посилаються, автоматично оновлюються.

- **Kustomize проти Helm**: Kustomize простіший (без шаблонів, без змінних), тоді як Helm потужніший (умови, цикли, пакування). Використовуйте Kustomize для простих оверлеїв; Helm — для складних застосунків.

---

## Типові помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Неправильний шлях до бази | Ресурси не знайдені | Використовуйте відносні шляхи (`../../base`) |
| Невідповідність імені цілі патчу | Патч не застосовується | Збігайте точне ім'я ресурсу |
| Відсутній `apiVersion` у kustomization | Недійсний файл | Завжди вказуйте версію |
| Забули секцію `resources` | Нічого не розгорнуто | Перелічіть усі файли ресурсів |
| Не переглянули перед застосуванням | Несподівані результати | Завжди спочатку виконуйте `kubectl kustomize` |

---

## Тест

1. **Ви налаштували базовий каталог з Deployment та Service, де Deployment посилається на Service за іменем `web-app`. В оверлеї ви додали `namePrefix: prod-`. Після застосування (`kubectl apply -k`), і Deployment, і Service отримують імена `prod-web-app`. Чому Deployment все ще успішно знаходить Service, хоча ви не змінювали змінні середовища чи конфігурацію всередині контейнерів вручну?**
   <details>
   <summary>Відповідь</summary>
   Kustomize глибоко розуміє семантику ресурсів Kubernetes та їхні взаємозв'язки. Коли застосовується трансформація на кшталт `namePrefix`, інструмент автоматично сканує та оновлює відповідні перехресні посилання всередині інших ресурсів. Це означає, що посилання на Service у специфікації Deployment також отримують префікс `prod-` без жодного ручного втручання. Така поведінка гарантує цілісність конфігурації та дозволяє легко розгортати ізольовані середовища, уникаючи конфліктів імен.
   </details>

2. **Ви оновили файл властивостей, який використовується для генерації ConfigMap у вашому kustomization.yaml, і виконали `kubectl apply -k`. Проте ваші існуючі Pods продовжують використовувати старі налаштування і не перезапускаються. Під час перевірки конфігурації виявилося, що хтось додав `disableNameSuffixHash: true`. Чому ця опція призвела до такої поведінки?**
   <details>
   <summary>Відповідь</summary>
   За замовчуванням Kustomize генерує унікальний хеш-суфікс для імен ConfigMap та Secret, який змінюється при будь-якій модифікації їхнього вмісту. Цей механізм змушує Deployment розпізнати зміну в специфікації Pod (оскільки ім'я ConfigMap змінилося), що ініціює автоматичне ковзне оновлення. Опція `disableNameSuffixHash: true` вимикає генерацію цього хешу, залишаючи ім'я ConfigMap статичним. Як наслідок, хоча сам ConfigMap оновлюється в кластері, Deployment не бачить жодних змін у своїй конфігурації, і старі Pods продовжують працювати без перезапуску.
   </details>

3. **Ви створили оверлей для production, який містить патч (`patches:`) для збільшення кількості реплік у Deployment з іменем `backend`. Однак при спробі виконати `kubectl kustomize` ви отримуєте помилку, що ціль для патчу не знайдена. Базовий маніфест має `name: backend`, але в оверлеї ви також вказали `namePrefix: prod-`. У чому полягає помилка при визначенні цілі (target) у патчі?**
   <details>
   <summary>Відповідь</summary>
   У блоці `target` для патчу необхідно завжди вказувати оригінальне ім'я ресурсу з базового маніфесту (у цьому випадку `backend`), а не його фінальне ім'я після застосування префіксів. Kustomize працює за певним порядком: він спочатку знаходить об'єкти за їхніми базовими іменами та застосовує до них патчі, і лише потім додає глобальні префікси чи суфікси. Це дизайнерське рішення дозволяє патчам бути універсальними та не залежати від того, які саме трансформації імен застосовуються в конкретному оверлеї.
   </details>

4. **Ваш базовий kustomization.yaml містить секцію `images:`, яка перевизначає тег образу `nginx` на `1.21`. Ваш dev-оверлей посилається на цю базу і також має секцію `images:`, де тег для `nginx` встановлено як `1.22`. Крім того, в dev-оверлеї є патч, який явно прописує `image: nginx:1.20` для контейнера. Який тег образу буде використано у фінальному маніфесті і чому?**
   <details>
   <summary>Відповідь</summary>
   У фінальному маніфесті буде використано тег `1.22`, визначений у блоці `images:` dev-оверлею. Kustomize обробляє трансформації у визначеному порядку: спочатку застосовуються базові налаштування, потім накладаються патчі, і наприкінці виконуються спеціальні трансформатори (такі як `images:`, `namePrefix:`). Оскільки директива `images:` спрацьовує останньою, вона перезапише будь-які значення, вказані безпосередньо в базових ресурсах або додані через патчі. Крім того, налаштування в оверлеї завжди мають вищий пріоритет над аналогічними налаштуваннями в базі.
   </details>

---

## Практична вправа

**Завдання**: Створити повну конфігурацію Kustomize з базою та оверлеями.

**Частина 1: Створення бази**

```bash
mkdir -p /tmp/kustomize-demo/base
cd /tmp/kustomize-demo

# Створити деплоймент
cat << 'EOF' > base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF

# Створити сервіс
cat << 'EOF' > base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  selector:
    app: web
  ports:
  - port: 80
EOF

# Створити базову кастомізацію
cat << 'EOF' > base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
- service.yaml
EOF
```

**Частина 2: Створення Dev-оверлею**

```bash
mkdir -p overlays/dev

cat << 'EOF' > overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: dev-
namespace: development

images:
- name: nginx
  newTag: "1.21"

configMapGenerator:
- name: app-config
  literals:
  - ENV=development
  - DEBUG=true
EOF
```

**Частина 3: Створення Prod-оверлею**

```bash
mkdir -p overlays/prod

cat << 'EOF' > overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: prod-
namespace: production

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web-app
    spec:
      replicas: 3

images:
- name: nginx
  newTag: "1.22"

configMapGenerator:
- name: app-config
  literals:
  - ENV=production
  - DEBUG=false
EOF
```

**Частина 4: Попередній перегляд та застосування**

```bash
# Попередній перегляд dev
kubectl kustomize overlays/dev/

# Попередній перегляд prod
kubectl kustomize overlays/prod/

# Застосувати dev (спочатку створити простір імен)
kubectl create ns development
kubectl apply -k overlays/dev/

# Перевірити
kubectl get all -n development

# Очищення
kubectl delete -k overlays/dev/
kubectl delete ns development
```

---

## Практичні вправи

### Вправа 1: Базова кастомізація (Ціль: 3 хвилини)

```bash
mkdir -p /tmp/drill1 && cd /tmp/drill1

# Створити деплоймент
cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Створити кастомізацію
cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
namespace: default
commonLabels:
  environment: test
EOF

# Попередній перегляд
kubectl kustomize ./

# Застосувати
kubectl apply -k ./

# Очищення
kubectl delete -k ./
```

### Вправа 2: Перевизначення образу (Ціль: 2 хвилини)

```bash
mkdir -p /tmp/drill2 && cd /tmp/drill2

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: nginx:1.19
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
images:
- name: nginx
  newTag: "1.22"
EOF

# Перевірити, що образ змінився
kubectl kustomize ./ | grep image

# Очищення
cd /tmp && rm -rf drill2
```

### Вправа 3: Генератор ConfigMap (Ціль: 3 хвилини)

```bash
mkdir -p /tmp/drill3 && cd /tmp/drill3

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: nginx
        envFrom:
        - configMapRef:
            name: app-config
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
configMapGenerator:
- name: app-config
  literals:
  - DATABASE_URL=postgres://localhost
  - LOG_LEVEL=debug
EOF

# Попередній перегляд — зверніть увагу на хеш-суфікс
kubectl kustomize ./

# Очищення
cd /tmp && rm -rf drill3
```

### Вправа 4: Патчі (Ціль: 4 хвилини)

```bash
mkdir -p /tmp/drill4 && cd /tmp/drill4

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web
    spec:
      replicas: 3
      template:
        spec:
          containers:
          - name: nginx
            resources:
              limits:
                memory: 128Mi
                cpu: 100m
EOF

# Перевірити, що патч застосовано
kubectl kustomize ./

# Очищення
cd /tmp && rm -rf drill4
```

### Вправа 5: Префікс імені та простір імен (Ціль: 2 хвилини)

```bash
mkdir -p /tmp/drill5 && cd /tmp/drill5

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
namePrefix: staging-
namespace: staging
commonLabels:
  env: staging
EOF

# Перевірити трансформації
kubectl kustomize ./

# Очищення
cd /tmp && rm -rf drill5
```

### Вправа 6: Повний сценарій з оверлеями (Ціль: 6 хвилин)

```bash
mkdir -p /tmp/drill6/{base,overlays/dev,overlays/prod}
cd /tmp/drill6

# База
cat << 'EOF' > base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: my-api:latest
        ports:
        - containerPort: 8080
EOF

cat << 'EOF' > base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
EOF

# Dev-оверлей
cat << 'EOF' > overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: dev-
namespace: dev
images:
- name: my-api
  newTag: dev-latest
EOF

# Prod-оверлей
cat << 'EOF' > overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: prod-
namespace: prod
images:
- name: my-api
  newTag: v1.0.0
patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: api
    spec:
      replicas: 3
EOF

# Порівняти виведення
echo "=== DEV ===" && kubectl kustomize overlays/dev/
echo "=== PROD ===" && kubectl kustomize overlays/prod/

# Очищення
cd /tmp && rm -rf drill6
```

---

## Наступний модуль

[Модуль 2.4: Стратегії деплойменту](module-2.4-deployment-strategies/) — патерни blue/green, canary та ковзного розгортання.