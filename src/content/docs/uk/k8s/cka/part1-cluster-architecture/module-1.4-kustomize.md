---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 1.4: Kustomize \u2014 \u043a\u043e\u043d\u0444\u0456\u0433\u0443\u0440\u0430\u0446\u0456\u044f \u0431\u0435\u0437 \u0448\u0430\u0431\u043b\u043e\u043d\u0456\u0432"
slug: uk/k8s/cka/part1-cluster-architecture/module-1.4-kustomize
sidebar: 
  order: 5
lab: 
  id: cka-1.4-kustomize
  url: https://killercoda.com/kubedojo/scenario/cka-1.4-kustomize
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — необхідний навик для іспиту 2025 року
>
> **Час на виконання**: 35–45 хвилин
>
> **Передумови**: Модуль 0.1 (робочий кластер), базові знання YAML

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** Kustomize overlays для деплойментів у кількох середовищах (dev, staging, production)
- **Застосувати** патчі, префікси імен, мітки та трансформації ресурсів без зміни базових маніфестів
- **Порівняти** Kustomize та Helm і обрати правильний інструмент для різних сценаріїв
- **Дебажити** вихід Kustomize, рендерячи маніфести через `kubectl kustomize` перед застосуванням

---

## Чому цей модуль важливий

Kustomize — це **новинка в програмі CKA 2025**. Вас будуть перевіряти на цю тему.

Kustomize вирішує поширену проблему: у вас один і той самий застосунок розгорнутий у dev, staging та production, але кожне середовище потребує дещо іншої конфігурації — різну кількість реплік, різні обмеження ресурсів, різні теги образів.

Без Kustomize вам довелося б:
1. Підтримувати окремі YAML-файли для кожного середовища (кошмар дублювання)
2. Використовувати шаблони із заповнювачами (додає складності)

Kustomize використовує інший підхід: **накладання та патчі**. Починаєте з бази, нашаровуєте зміни для конкретного середовища зверху. Без шаблонізації. Чистий YAML. Вбудовано в kubectl.

> **Аналогія з прозорою плівкою**
>
> Уявіть Kustomize як прозорі плівки-накладки для проєктора. Ваш базовий слайд показує структуру застосунку. Для production ви накладаєте плівку, що додає "replicas: 10". Для dev — плівку, що змінює тег образу. Кожна накладка модифікує базу без її дублювання. Нашаровуйте стільки накладок, скільки потрібно.

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Створювати бази та оверлеї Kustomize
- Патчити ресурси без зміни оригіналів
- Використовувати типові трансформації (мітки, простори імен, префікси)
- Генерувати ConfigMap та Secret з файлів
- Застосовувати конфігурації Kustomize через kubectl

---

## Частина 1: Концепції Kustomize

### 1.1 Основна термінологія

| Термін | Визначення |
|--------|------------|
| **Base (база)** | Оригінальні, повторно використовувані визначення ресурсів |
| **Overlay (оверлей)** | Налаштування для конкретного середовища |
| **Patch (патч)** | Частковий YAML, що модифікує ресурс |
| **kustomization.yaml** | Маніфест, що визначає, що включити та трансформувати |

### 1.2 Структура каталогів

```
myapp/
├── base/                      # Спільні, повторно використовувані визначення
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
│
└── overlays/                  # Для конкретних середовищ
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patch-replicas.yaml
    │
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patch-resources.yaml
    │
    └── production/
        ├── kustomization.yaml
        ├── patch-replicas.yaml
        └── patch-resources.yaml
```

### 1.3 Як працює Kustomize

```
┌────────────────────────────────────────────────────────────────┐
│                     Потік Kustomize                              │
│                                                                 │
│   Базові ресурси                      Патчі оверлею             │
│   ┌─────────────────┐              ┌─────────────────┐         │
│   │ deployment.yaml │              │ patch-prod.yaml │         │
│   │ replicas: 1     │      +       │ replicas: 10    │         │
│   │ image: v1       │              │ image: v2       │         │
│   └─────────────────┘              └─────────────────┘         │
│            │                              │                     │
│            └──────────────┬───────────────┘                     │
│                           │                                     │
│                           ▼                                     │
│                    ┌─────────────┐                              │
│                    │  Kustomize  │                              │
│                    │ (злиття)    │                              │
│                    └──────┬──────┘                              │
│                           │                                     │
│                           ▼                                     │
│                    Фінальний результат                          │
│                    ┌─────────────────┐                          │
│                    │ deployment.yaml │                          │
│                    │ replicas: 10    │                          │
│                    │ image: v2       │                          │
│                    └─────────────────┘                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Чи знали ви?**
>
> Kustomize вбудовано в kubectl починаючи з версії v1.14. Вам не потрібно нічого додатково встановлювати — просто використовуйте `kubectl apply -k` або `kubectl kustomize`. Саме тому це улюблена тема на іспиті CKA: все працює одразу.

---

## Частина 2: Створення бази

### 2.1 Файл kustomization.yaml

Кожний каталог Kustomize потребує `kustomization.yaml`:

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
```

### 2.2 Базові ресурси

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
```

```yaml
# base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 80
```

### 2.3 Попередній перегляд базового виводу

```bash
# Подивитися, що генерує база
kubectl kustomize base/

# Або використовуючи kustomize безпосередньо
kustomize build base/
```

---

## Частина 3: Створення оверлеїв

### 3.1 Простий оверлей

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base    # Посилання на базу

namePrefix: dev-           # Префікс для всіх імен ресурсів
namespace: development     # Розмістити все в цьому просторі імен

commonLabels:
  environment: dev         # Додати цю мітку до всіх ресурсів
```

### 3.2 Оверлей для production з патчами

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
namespace: production

commonLabels:
  environment: production

patches:
  - path: patch-replicas.yaml
  - path: patch-resources.yaml
```

```yaml
# overlays/production/patch-replicas.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp     # Має збігатися з іменем базового ресурсу
spec:
  replicas: 10    # Перевизначити кількість реплік
```

```yaml
# overlays/production/patch-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: myapp
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
```

### 3.3 Попередній перегляд та застосування оверлеїв

```bash
# Попередній перегляд оверлею для production
kubectl kustomize overlays/production/

# Застосувати до кластера
kubectl apply -k overlays/production/

# Застосувати оверлей для dev
kubectl apply -k overlays/dev/
```

---

## Частина 4: Типові трансформери

### 4.1 namePrefix та nameSuffix

```yaml
# kustomization.yaml
namePrefix: prod-
nameSuffix: -v2

# Результат: deployment "myapp" стає "prod-myapp-v2"
```

### 4.2 namespace

```yaml
# kustomization.yaml
namespace: production

# Усі ресурси отримують namespace: production
```

### 4.3 commonLabels

```yaml
# kustomization.yaml
commonLabels:
  app.kubernetes.io/name: myapp
  app.kubernetes.io/env: production

# Додається до ВСІХ ресурсів (metadata.labels ТА selector)
```

### 4.4 commonAnnotations

```yaml
# kustomization.yaml
commonAnnotations:
  team: platform
  oncall: platform@example.com

# Додається до metadata.annotations усіх ресурсів
```

### 4.5 images

Зміна імен/тегів образів без патчингу:

```yaml
# kustomization.yaml
images:
  - name: nginx           # Оригінальне ім'я образу
    newName: my-registry/nginx
    newTag: "2.0"

# Змінює всі образи nginx на my-registry/nginx:2.0
```

---

## Частина 5: Стратегії патчингу

### 5.1 Strategic Merge Patch (за замовчуванням)

Зливає ваш патч із базою:

```yaml
# patches/add-sidecar.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: sidecar           # Додається до наявних контейнерів
        image: busybox
        command: ["sleep", "infinity"]
```

### 5.2 JSON 6902 Patch

Більш точний контроль за допомогою синтаксису JSON Patch:

```yaml
# kustomization.yaml
patches:
  - target:
      kind: Deployment
      name: myapp
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: add
        path: /metadata/annotations/patched
        value: "true"
```

### 5.3 Цільове застосування патчів

Цільовий вибір конкретних ресурсів:

```yaml
# kustomization.yaml
patches:
  - path: patch-replicas.yaml
    target:
      kind: Deployment
      name: myapp
```

Цільовий вибір за міткою:

```yaml
patches:
  - path: patch-memory.yaml
    target:
      kind: Deployment
      labelSelector: "tier=frontend"
```

---

## Частина 6: Генератори

### 6.1 Генератор ConfigMap

Генерація ConfigMap із файлів або літералів:

```yaml
# kustomization.yaml
configMapGenerator:
  - name: app-config
    literals:
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
    files:
      - config.properties

# Створює ConfigMap із хешованим суфіксом у назві
# наприклад, app-config-8h2k9d
```

### 6.2 Генератор Secret

```yaml
# kustomization.yaml
secretGenerator:
  - name: db-credentials
    literals:
      - username=admin
      - password=secret123
    type: Opaque

# Створює Secret із хешованим суфіксом у назві
```

### 6.3 Навіщо хешовані імена?

```
app-config-8h2k9d
            ^^^^^^
            хеш вмісту
```

Коли вміст ConfigMap змінюється, хеш змінюється, що змінює ім'я. Це запускає поступове оновлення (rolling update) подів, що використовують цей ConfigMap — вони автоматично виявляють нове посилання.

### 6.4 Вимкнення хеш-суфіксів

```yaml
# kustomization.yaml
configMapGenerator:
  - name: app-config
    literals:
      - KEY=value

generatorOptions:
  disableNameSuffixHash: true
```

---

## Частина 7: Приклад із реального життя

### 7.1 Повна структура каталогів

```
webapp/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── config/
│       └── nginx.conf
│
└── overlays/
    ├── dev/
    │   └── kustomization.yaml
    └── prod/
        ├── kustomization.yaml
        ├── patch-replicas.yaml
        └── secrets/
            └── db-password.txt
```

### 7.2 Базовий kustomization.yaml

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

configMapGenerator:
  - name: nginx-config
    files:
      - config/nginx.conf
```

### 7.3 Оверлей для production

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namespace: production
namePrefix: prod-

commonLabels:
  environment: production

images:
  - name: nginx
    newTag: "1.25-alpine"

patches:
  - path: patch-replicas.yaml

secretGenerator:
  - name: db-credentials
    files:
      - password=secrets/db-password.txt
```

---

## Частина 8: Інтеграція з kubectl

### 8.1 Основні команди

```bash
# Попередній перегляд виводу kustomization
kubectl kustomize <directory>

# Застосувати kustomization до кластера
kubectl apply -k <directory>

# Видалити ресурси з kustomization
kubectl delete -k <directory>

# Порівняти з поточним станом кластера
kubectl diff -k <directory>
```

### 8.2 Команди для іспиту

```bash
# Швидке застосування для іспиту
kubectl apply -k overlays/production/

# Перевірити, що було створено
kubectl get all -n production

# Якщо потрібно відлагодити
kubectl kustomize overlays/production/ | kubectl apply --dry-run=client -f -
```

---

## Частина 9: Kustomize проти Helm

| Аспект | Kustomize | Helm |
|--------|-----------|------|
| Підхід | Оверлей/патч | Шаблон |
| Складність вивчення | Нижча | Вища |
| Чистий YAML | Так | Ні (Go-шаблони) |
| Обмін пакетами | Каталоги | Charts |
| Відкат | Не вбудований | Вбудований |
| Найкраще для | Варіантів конфігурації | Складних застосунків |

**Використовуйте Kustomize, коли**: у вас власні маніфести і потрібні варіації для різних середовищ.

**Використовуйте Helm, коли**: встановлюєте сторонні застосунки або потребуєте шаблонізації.

> **Порада для іспиту**
>
> На іспиті CKA вас можуть попросити використати Helm або Kustomize. Знайте обидва інструменти. Для швидкої кастомізації середовищ Kustomize налаштовується швидше.

---

## Чи знали ви?

- **Kustomize був окремим інструментом** до того, як його вбудували в kubectl. Ви й досі можете встановити окремий `kustomize` для додаткових можливостей.

- **Argo CD та Flux** (інструменти GitOps) нативно розуміють Kustomize. Ваша структура оверлеїв стає вашою стратегією розгортання.

- **Можна поєднувати Helm та Kustomize**. Генеруйте маніфести з Helm, а потім налаштовуйте за допомогою оверлеїв Kustomize.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Неправильний шлях до бази | "resource not found" | Використовуйте відносні шляхи, як-от `../../base` |
| Забули kustomization.yaml | Помилки kubectl | Кожний каталог потребує цього файлу |
| Невідповідність імені патча | Патч не застосовується | metadata.name патча повинно збігатися з базою |
| Відсутній namespace | Ресурси в неправильному просторі імен | Додайте `namespace:` до оверлею |
| commonLabels ламає селектори | Невідповідність селекторів | Ретельно тестуйте, мітки впливають на селектори |

---

## Тест

1. **Яка різниця між базою та оверлеєм у Kustomize?**
   <details>
   <summary>Відповідь</summary>
   **База** містить оригінальні, повторно використовувані визначення ресурсів. **Оверлей** посилається на базу та додає налаштування для конкретного середовища (патчі, мітки, простори імен). Оверлеї модифікують бази без їх дублювання.
   </details>

2. **Як застосувати конфігурацію Kustomize до вашого кластера?**
   <details>
   <summary>Відповідь</summary>
   `kubectl apply -k <directory>`, де каталог містить файл kustomization.yaml. Приклад: `kubectl apply -k overlays/production/`
   </details>

3. **Чому Kustomize додає хеш-суфікс до згенерованих ConfigMap?**
   <details>
   <summary>Відповідь</summary>
   Хеш базується на вмісті ConfigMap. Коли вміст змінюється, хеш змінюється, що змінює ім'я ConfigMap. Поди, що посилаються на ConfigMap, виявляють нове ім'я та запускають поступове оновлення (rolling update), гарантуючи отримання нової конфігурації.
   </details>

4. **Вам потрібно змінити тег образу для production, не модифікуючи базу. Як?**
   <details>
   <summary>Відповідь</summary>
   Використайте трансформер `images` у kustomization.yaml вашого оверлею:
   ```yaml
   images:
     - name: nginx
       newTag: "1.25-production"
   ```
   Це змінює всі посилання на образ nginx без зміни базових файлів.
   </details>

---

## Практична вправа

**Завдання**: Створити структуру Kustomize для вебзастосунку з оверлеями dev та prod.

**Кроки**:

1. **Створіть структуру каталогів**:
```bash
mkdir -p webapp/base webapp/overlays/dev webapp/overlays/prod
```

2. **Створіть базовий deployment**:
```bash
cat > webapp/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: nginx:1.25
        ports:
        - containerPort: 80
EOF
```

3. **Створіть базовий service**:
```bash
cat > webapp/base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: webapp
spec:
  selector:
    app: webapp
  ports:
  - port: 80
EOF
```

4. **Створіть базовий kustomization**:
```bash
cat > webapp/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
EOF
```

5. **Створіть оверлей для dev**:
```bash
cat > webapp/overlays/dev/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: dev-
namespace: development
commonLabels:
  environment: dev
EOF
```

6. **Створіть оверлей для prod із патчем**:
```bash
cat > webapp/overlays/prod/patch-replicas.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 5
EOF

cat > webapp/overlays/prod/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: prod-
namespace: production
commonLabels:
  environment: production
images:
  - name: nginx
    newTag: "1.25-alpine"
patches:
  - path: patch-replicas.yaml
EOF
```

7. **Попередній перегляд та порівняння**:
```bash
echo "=== DEV ===" && kubectl kustomize webapp/overlays/dev/
echo "=== PROD ===" && kubectl kustomize webapp/overlays/prod/
```

8. **Застосуйте оверлей для dev**:
```bash
kubectl create namespace development
kubectl apply -k webapp/overlays/dev/
kubectl get all -n development
```

9. **Застосуйте оверлей для prod**:
```bash
kubectl create namespace production
kubectl apply -k webapp/overlays/prod/
kubectl get all -n production
```

**Критерії успіху**:
- [ ] Розуміння структури база vs оверлей
- [ ] Вмієте створювати файли kustomization.yaml
- [ ] Вмієте використовувати namePrefix, namespace, commonLabels
- [ ] Вмієте створювати та застосовувати патчі
- [ ] Вмієте переглядати вивід за допомогою `kubectl kustomize`

**Очищення**:
```bash
kubectl delete -k webapp/overlays/dev/
kubectl delete -k webapp/overlays/prod/
kubectl delete namespace development production
rm -rf webapp/
```

---

## Практичні вправи

### Вправа 1: Kustomize проти kubectl apply (Ціль: 2 хвилини)

Зрозумійте різницю:

```bash
# Створити базу
mkdir -p drill1/base
cat << 'EOF' > drill1/base/deployment.yaml
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

cat << 'EOF' > drill1/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
EOF

# Попередній перегляд vs застосування
kubectl kustomize drill1/base/          # Лише попередній перегляд
kubectl apply -k drill1/base/           # Справжнє застосування
kubectl get deploy nginx
kubectl delete -k drill1/base/
rm -rf drill1
```

### Вправа 2: Трансформація простору імен (Ціль: 3 хвилини)

```bash
mkdir -p drill2/base drill2/overlays/dev
cat << 'EOF' > drill2/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: nginx
EOF

cat << 'EOF' > drill2/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
EOF

cat << 'EOF' > drill2/overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namespace: dev-namespace
namePrefix: dev-
EOF

# Попередній перегляд — подивіться на трансформації
kubectl kustomize drill2/overlays/dev/

# Застосувати
kubectl create namespace dev-namespace
kubectl apply -k drill2/overlays/dev/
kubectl get deploy -n dev-namespace  # Показує dev-app

# Очищення
kubectl delete -k drill2/overlays/dev/
kubectl delete namespace dev-namespace
rm -rf drill2
```

### Вправа 3: Трансформація образу (Ціль: 3 хвилини)

```bash
mkdir -p drill3
cat << 'EOF' > drill3/deployment.yaml
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
      - name: web
        image: nginx:1.19
EOF

cat << 'EOF' > drill3/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
images:
  - name: nginx
    newTag: "1.25"
EOF

# Попередній перегляд — зверніть увагу, що образ змінився на nginx:1.25
kubectl kustomize drill3/

# Застосувати та перевірити
kubectl apply -k drill3/
kubectl get deploy web -o jsonpath='{.spec.template.spec.containers[0].image}'
# Вивід: nginx:1.25

# Очищення
kubectl delete -k drill3/
rm -rf drill3
```

### Вправа 4: Виправлення несправностей — зламана Kustomization (Ціль: 5 хвилин)

```bash
# Створити зламану kustomization
mkdir -p drill4
cat << 'EOF' > drill4/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml    # Файл не існує!
  - service.yaml       # Файл не існує!
commonLabels:
  app: myapp
EOF

# Спробувати зібрати — буде помилка
kubectl kustomize drill4/

# ВАШЕ ЗАВДАННЯ: Виправте, створивши відсутні файли
```

<details>
<summary>Рішення</summary>

```bash
cat << 'EOF' > drill4/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: nginx
EOF

cat << 'EOF' > drill4/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
EOF

# Тепер працює
kubectl kustomize drill4/
rm -rf drill4
```

</details>

### Вправа 5: Strategic Merge Patch (Ціль: 5 хвилин)

```bash
mkdir -p drill5/base drill5/overlay
cat << 'EOF' > drill5/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: nginx
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
EOF

cat << 'EOF' > drill5/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
EOF

# Створити патч для збільшення ресурсів у production
cat << 'EOF' > drill5/overlay/patch-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
EOF

cat << 'EOF' > drill5/overlay/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../base
patches:
  - path: patch-resources.yaml
EOF

# Попередній перегляд результату
kubectl kustomize drill5/overlay/
rm -rf drill5
```

### Вправа 6: Генератор ConfigMap (Ціль: 3 хвилини)

```bash
mkdir -p drill6
cat << 'EOF' > drill6/app.properties
DATABASE_URL=postgres://localhost:5432/mydb
LOG_LEVEL=info
FEATURE_FLAG=enabled
EOF

cat << 'EOF' > drill6/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
configMapGenerator:
  - name: app-config
    files:
      - app.properties
    literals:
      - EXTRA_KEY=extra-value
EOF

# Попередній перегляд — зверніть увагу на ConfigMap із хеш-суфіксом
kubectl kustomize drill6/
rm -rf drill6
```

### Вправа 7: Виклик — налаштування для кількох середовищ

Створіть повну структуру Kustomize для 3 середовищ без підглядання в рішення:

**Вимоги**:
- База: nginx deployment, service
- Dev: 1 репліка, простір імен `dev`, образ `nginx:1.24`
- Staging: 2 репліки, простір імен `staging`, образ `nginx:1.25`
- Prod: 5 реплік, простір імен `production`, образ `nginx:1.25`, додати обмеження ресурсів

```bash
mkdir -p challenge/{base,overlays/{dev,staging,prod}}
# ВАШЕ ЗАВДАННЯ: Створіть усі файли kustomization.yaml та ресурсів
```

<details>
<summary>Структура рішення</summary>

```
challenge/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── prod/
│       ├── kustomization.yaml
│       └── patch-resources.yaml
```

Протестуйте кожний: `kubectl kustomize challenge/overlays/dev/`

</details>

---

## Наступний модуль

[Модуль 1.5: CRD та Оператори](module-1.5-crds-operators/) — розширення Kubernetes за допомогою Custom Resource Definitions.
