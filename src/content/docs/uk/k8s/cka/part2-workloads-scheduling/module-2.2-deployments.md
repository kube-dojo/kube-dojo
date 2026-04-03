---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2.2: \u0414\u0435\u043f\u043b\u043e\u0439\u043c\u0435\u043d\u0442\u0438 \u0442\u0430 ReplicaSets"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.2-deployments
sidebar: 
  order: 3
lab: 
  id: cka-2.2-deployments
  url: https://killercoda.com/kubedojo/scenario/cka-2.2-deployments
  duration: "45 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[СЕРЕДНЯ]` — Основна тема іспиту
>
> **Час на проходження**: 45-55 хвилин
>
> **Передумови**: Модуль 2.1 (Поди)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** Deployments зі стратегією rolling update та налаштувати maxSurge/maxUnavailable
- **Виконати** розгортання, відкати та перегляд історії в умовах обмеженого часу CKA
- **Діагностувати** застрягле розгортання, перевіряючи статус ReplicaSet, події подів та доступність ресурсів
- **Пояснити** ланцюжок володіння Deployment → ReplicaSet → Pod та чому старі ReplicaSets зберігаються

---

## Чому цей модуль важливий

У продакшені ви ніколи не запускаєте окремі поди. Ви використовуєте **Деплойменти**.

Деплойменти є найпоширенішим ресурсом робочого навантаження. Вони забезпечують:
- Запуск кількох реплік вашого додатку
- Поступові оновлення (rolling updates) з нульовим часом простою
- Автоматичні відкати, коли щось іде не так
- Масштабування (збільшення та зменшення кількості)

Іспит CKA перевіряє створення деплойментів, виконання поступових оновлень, масштабування та відкатів. Це фундаментальні навички, які ви будете використовувати щодня.

> **Аналогія з менеджером автопарку**
>
> Уявіть Деплоймент як менеджера автопарку в компанії таксі. Менеджер не керує таксі безпосередньо — він керує водіями (подами). Якщо водій бере лікарняний (под падає), менеджер призначає заміну. Якщо попит зростає (масштабування), менеджер наймає більше водіїв. Під час оновлення транспортних засобів (поступове оновлення), менеджер поступово міняє старі автомобілі на нові, гарантуючи, що у клієнтів завжди є доступні поїздки.

---

## Чому ви навчитеся

До кінця цього модуля ви зможете:
- Створювати Деплойменти та керувати ними
- Розуміти, як працюють ReplicaSets
- Виконувати поступові оновлення та відкати
- Горизонтально масштабувати додатки
- Призупиняти та відновлювати деплойменти

---

## Частина 1: Основи Деплойменту

### 1.1 Ієрархія Деплойменту

```
┌────────────────────────────────────────────────────────────────┐
│                   Ієрархія Деплойменту                          │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                     Деплоймент                           │  │
│   │  - Бажаний стан (репліки, образ, стратегія)             │  │
│   │  - Керує ReplicaSets                                    │  │
│   └────────────────────────┬────────────────────────────────┘  │
│                            │ створює та керує                   │
│                            ▼                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    ReplicaSet                            │  │
│   │  - Забезпечує роботу N реплік                           │  │
│   │  - Створює/видаляє поди для бажаної кількості           │  │
│   └────────────────────────┬────────────────────────────────┘  │
│                            │ створює та керує                   │
│                            ▼                                    │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│   │  Под 1  │  │  Под 2  │  │  Под 3  │  │  Под N  │          │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Чому не просто ReplicaSets?

| Функція | ReplicaSet | Деплоймент |
|---------|------------|------------|
| Підтримка кількості реплік | ✅ | ✅ |
| Поступові оновлення | ❌ | ✅ |
| Відкат | ❌ | ✅ |
| Історія оновлень | ❌ | ✅ |
| Призупинення/Відновлення | ❌ | ✅ |

**Правило**: Завжди використовуйте Деплойменти. Ніколи не створюйте ReplicaSets безпосередньо.

### 1.3 Специфікація Деплойменту

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3                    # Desired pod count
  selector:                      # How to find pods to manage
    matchLabels:
      app: nginx
  template:                      # Pod template
    metadata:
      labels:
        app: nginx               # Must match selector
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
```

> **Критично**: Значення `spec.selector.matchLabels` має збігатися з `spec.template.metadata.labels`. Якщо вони не збігаються, Деплоймент не керуватиме подами.

---

## Частина 2: Створення Деплойментів

### 2.1 Імперативні команди (Швидко для іспиту)

```bash
# Create deployment
kubectl create deployment nginx --image=nginx

# Create with specific replicas
kubectl create deployment nginx --image=nginx --replicas=3

# Create with port
kubectl create deployment nginx --image=nginx --port=80

# Generate YAML (essential for exam!)
kubectl create deployment nginx --image=nginx --replicas=3 --dry-run=client -o yaml > deploy.yaml
```

### 2.2 З YAML

```yaml
# nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
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
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
```

```bash
kubectl apply -f nginx-deployment.yaml
```

### 2.3 Перегляд Деплойментів

```bash
# List deployments
kubectl get deployments
kubectl get deploy          # Short form

# Detailed view
kubectl get deploy -o wide

# Describe deployment
kubectl describe deployment nginx

# Get deployment YAML
kubectl get deployment nginx -o yaml

# Check rollout status
kubectl rollout status deployment/nginx
```

> **Чи знали ви?**
>
> Команда `kubectl rollout status` блокує виконання до завершення розгортання. Вона ідеально підходить для CI/CD конвеєрів — якщо розгортання завершиться помилкою, команда завершить роботу з ненульовим статусом.

---

## Частина 3: ReplicaSets під капотом

### 3.1 Як працюють ReplicaSets

Коли ви створюєте Деплоймент:
1. Контролер Деплойменту створює ReplicaSet
2. Контролер ReplicaSet створює поди
3. ReplicaSet гарантує, що бажана кількість реплік збігається з фактичною

```bash
# Create a deployment
kubectl create deployment nginx --image=nginx --replicas=3

# See the ReplicaSet created
kubectl get replicasets
# NAME               DESIRED   CURRENT   READY   AGE
# nginx-5d5dd5d5fb   3         3         3       30s

# See pods with owner reference
kubectl get pods --show-labels
```

### 3.2 Іменування ReplicaSet

```
nginx-5d5dd5d5fb
^     ^
|     |
|     └── Хеш шаблону пода
|
└── Назва Деплойменту
```

Коли ви оновлюєте деплоймент, створюється новий ReplicaSet з іншим хешем.

### 3.3 Не керуйте ReplicaSets безпосередньо

```bash
# Don't do this - let Deployment manage ReplicaSets
kubectl scale replicaset nginx-5d5dd5d5fb --replicas=5  # BAD

# Do this instead
kubectl scale deployment nginx --replicas=5             # GOOD
```

---

## Частина 4: Масштабування

### 4.1 Ручне масштабування

```bash
# Scale to specific replicas
kubectl scale deployment nginx --replicas=5

# Scale to zero (stop all pods)
kubectl scale deployment nginx --replicas=0

# Scale multiple deployments
kubectl scale deployment nginx webapp --replicas=3
```

### 4.2 Редагування Деплойменту

```bash
# Edit deployment directly
kubectl edit deployment nginx
# Change spec.replicas and save

# Or patch
kubectl patch deployment nginx -p '{"spec":{"replicas":5}}'
```

### 4.3 Перевірка масштабування

```bash
# Watch pods scale
kubectl get pods -w

# Check deployment status
kubectl get deployment nginx
# NAME    READY   UP-TO-DATE   AVAILABLE   AGE
# nginx   5/5     5            5           10m

# Detailed status
kubectl rollout status deployment/nginx
```

---

## Частина 5: Поступові оновлення

### 5.1 Стратегія оновлення

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 4
  strategy:
    type: RollingUpdate           # Default strategy
    rollingUpdate:
      maxSurge: 1                 # Max pods over desired during update
      maxUnavailable: 1           # Max pods unavailable during update
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
        image: nginx:1.25
```

### 5.2 Візуалізація поступового оновлення

```
┌────────────────────────────────────────────────────────────────┐
│                  Поступове оновлення                            │
│                  (maxSurge=1, maxUnavailable=1)                │
│                                                                 │
│   Бажано: 4 репліки                                            │
│                                                                 │
│   Крок 1: Початок зі старої версії                             │
│   [v1] [v1] [v1] [v1]                                          │
│                                                                 │
│   Крок 2: Створення 1 нового пода (maxSurge=1)                 │
│   [v1] [v1] [v1] [v1] [v2-creating]                            │
│                                                                 │
│   Крок 3: v2 готовий, завершення 1 старого (maxUnavailable=1)  │
│   [v1] [v1] [v1] [v2] [v1-terminating]                         │
│                                                                 │
│   Крок 4: Продовження оновлення                                │
│   [v1] [v1] [v2] [v2] [v1-terminating]                         │
│                                                                 │
│   Крок 5: Продовження оновлення                                │
│   [v1] [v2] [v2] [v2] [v1-terminating]                         │
│                                                                 │
│   Крок 6: Завершено                                            │
│   [v2] [v2] [v2] [v2]                                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 Запуск оновлень

```bash
# Update image (triggers rolling update)
kubectl set image deployment/nginx nginx=nginx:1.26

# Update with record (saves command in history)
kubectl set image deployment/nginx nginx=nginx:1.26 --record

# Update environment variable
kubectl set env deployment/nginx ENV=production

# Update resources
kubectl set resources deployment/nginx -c nginx --limits=cpu=200m,memory=512Mi

# Edit deployment (any change to pod template triggers update)
kubectl edit deployment nginx
```

### 5.4 Спостереження за оновленнями

```bash
# Watch rollout progress
kubectl rollout status deployment/nginx

# Watch pods during update
kubectl get pods -w

# Watch ReplicaSets
kubectl get rs -w
```

> **Порада до іспиту**
>
> Під час іспиту використовуйте `kubectl set image` для швидкого оновлення. Це швидше, ніж редагувати YAML. Додайте `--record`, щоб зберегти команду в історії розгортань.

---

## Частина 6: Відкати

### 6.1 Перегляд історії розгортань

```bash
# View history
kubectl rollout history deployment/nginx

# View specific revision
kubectl rollout history deployment/nginx --revision=2
```

### 6.2 Виконання відкату

```bash
# Rollback to previous version
kubectl rollout undo deployment/nginx

# Rollback to specific revision
kubectl rollout undo deployment/nginx --to-revision=2

# Verify rollback
kubectl rollout status deployment/nginx
kubectl get deployment nginx -o wide
```

### 6.3 Як працює відкат

```
┌────────────────────────────────────────────────────────────────┐
│                     Процес відкату                              │
│                                                                 │
│   Перед відкатом:                                              │
│   ┌─────────────────────────────────────────────────┐          │
│   │ ReplicaSet v1  (репліки: 0)  ← стара версія    │          │
│   │ ReplicaSet v2  (репліки: 4)  ← поточна         │          │
│   └─────────────────────────────────────────────────┘          │
│                                                                 │
│   kubectl rollout undo deployment/nginx                        │
│                                                                 │
│   Після відкату:                                               │
│   ┌─────────────────────────────────────────────────┐          │
│   │ ReplicaSet v1  (репліки: 4)  ← відновлено      │          │
│   │ ReplicaSet v2  (репліки: 0)  ← зменшено        │          │
│   └─────────────────────────────────────────────────┘          │
│                                                                 │
│   Деплоймент зберігає старі ReplicaSets для можливості відкату │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.4 Керування історією

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  revisionHistoryLimit: 10    # Keep 10 old ReplicaSets (default)
  # Set to 0 to disable rollback capability
```

> **Бойова історія: Випадковий простій продакшену**
>
> Команда розгорнула зламаний образ у продакшені. Почалася паніка. Інженер, який знав про `kubectl rollout undo`, врятував ситуацію за лічені секунди. Інженер, який не знав, витратив 20 хвилин, намагаючись з'ясувати попередній тег образу. Знайте свої команди відкату!

---

## Частина 7: Призупинення та Відновлення

### 7.1 Навіщо призупиняти?

Призупиніть деплоймент, щоб:
- Внести кілька змін без запуску кількох розгортань
- Згрупувати оновлення
- Виконувати налагодження без створення нових подів

### 7.2 Використання призупинення/відновлення

```bash
# Pause deployment
kubectl rollout pause deployment/nginx

# Make multiple changes (no rollout triggered)
kubectl set image deployment/nginx nginx=nginx:1.26
kubectl set resources deployment/nginx -c nginx --limits=cpu=200m
kubectl set env deployment/nginx ENV=production

# Resume - triggers single rollout with all changes
kubectl rollout resume deployment/nginx

# Watch the rollout
kubectl rollout status deployment/nginx
```

---

## Частина 8: Стратегія Recreate

### 8.1 Коли використовувати Recreate

Використовуйте `Recreate`, коли:
- Додаток не може виконувати кілька версій одночасно
- Несумісність схеми бази даних між версіями
- Обмежені ресурси (неможливо запустити додаткові поди)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
spec:
  replicas: 1
  strategy:
    type: Recreate          # All pods deleted, then new pods created
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: db
        image: postgres:15
```

### 8.2 Recreate проти RollingUpdate

| Аспект | RollingUpdate | Recreate |
|--------|---------------|----------|
| Час простою | Нуль (якщо налаштовано правильно) | Так |
| Використання ресурсів | Вище під час оновлення | Без змін |
| Складність | Вища | Проста |
| Варіант використання | Додатки без стану (Stateless) | Зі станом (Stateful), несумісні версії |

---

## Частина 9: Умови Деплойменту (Conditions)

### 9.1 Перевірка умов

```bash
# View conditions
kubectl get deployment nginx -o jsonpath='{.status.conditions[*].type}'

# Detailed conditions
kubectl describe deployment nginx | grep -A10 Conditions
```

### 9.2 Типові умови

| Умова | Значення |
|-----------|---------|
| `Available` | Доступна мінімальна кількість реплік |
| `Progressing` | Виконується розгортання |
| `ReplicaFailure` | Не вдалося створити поди |

---

## Чи знали ви?

- **Деплойменти є декларативними**: Ви вказуєте бажаний стан, Kubernetes з'ясовує, як його досягти.

- **ReplicaSets є незмінними (immutable)**: Коли ви оновлюєте Деплоймент, створюється новий ReplicaSet. Старий зберігається для відкату.

- **Стратегія за замовчуванням — RollingUpdate** з `maxSurge: 25%` та `maxUnavailable: 25%`.

- **`--record` застарів** у нових версіях, але все ще працює. Тепер анотації відстежують зміни автоматично.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|----------|
| Мітки не збігаються з селектором | Деплоймент не керує подами | Переконайтеся, що `selector.matchLabels` збігається з `template.metadata.labels` |
| Відсутні ліміти ресурсів | Поди можуть виснажити інші робочі навантаження | Завжди встановлюйте requests та limits |
| Відкат без перевірки | Може відновити зламану версію | Спочатку перевірте `rollout history --revision=N` |
| Використання тегу `latest` | Розгортання може не запуститися | Використовуйте теги конкретних версій |
| Неперевірене розгортання | Припущення успіху | Завжди виконуйте `rollout status` |

---

## Тест

1. **Що відбувається при оновленні образу Деплойменту?**
   <details>
   <summary>Відповідь</summary>
   Запускається поступове оновлення (rolling update): створюється новий ReplicaSet з новим образом. Поди поступово створюються в новому ReplicaSet, тоді як поди в старому ReplicaSet завершуються, контролюючись `maxSurge` та `maxUnavailable`.
   </details>

2. **Як відкотити деплоймент до ревізії 3?**
   <details>
   <summary>Відповідь</summary>
   `kubectl rollout undo deployment/nginx --to-revision=3`

   Це збільшує масштаб ReplicaSet з ревізії 3 і зменшує поточний ReplicaSet.
   </details>

3. **Яка різниця між стратегіями RollingUpdate та Recreate?**
   <details>
   <summary>Відповідь</summary>
   **RollingUpdate**: Поступово замінює старі поди новими, підтримуючи доступність. **Recreate**: Спочатку завершує всі існуючі поди, потім створює нові — викликає час простою.
   </details>

4. **Вам потрібно змінити образ, ресурси та змінні середовища. Як зробити одне розгортання замість трьох?**
   <details>
   <summary>Відповідь</summary>
   ```bash
   kubectl rollout pause deployment/nginx
   kubectl set image deployment/nginx nginx=nginx:1.26
   kubectl set resources deployment/nginx -c nginx --limits=cpu=200m
   kubectl set env deployment/nginx ENV=production
   kubectl rollout resume deployment/nginx
   ```
   </details>

---

## Практичне завдання

**Завдання**: Повний життєвий цикл деплойменту — створення, масштабування, оновлення, відкат.

**Кроки**:

1. **Створіть деплоймент**:
```bash
kubectl create deployment webapp --image=nginx:1.24 --replicas=3
kubectl rollout status deployment/webapp
```

2. **Перевірте деплоймент та ReplicaSet**:
```bash
kubectl get deployment webapp
kubectl get replicaset
kubectl get pods -l app=webapp
```

3. **Масштабуйте деплоймент**:
```bash
kubectl scale deployment webapp --replicas=5
kubectl get pods -w  # Watch pods scale up
```

4. **Оновіть образ (поступове оновлення)**:
```bash
kubectl set image deployment/webapp nginx=nginx:1.25 --record
kubectl rollout status deployment/webapp
```

5. **Перевірте історію розгортань**:
```bash
kubectl rollout history deployment/webapp
kubectl get replicaset  # Notice two ReplicaSets now
```

6. **Розгорніть "погану" версію**:
```bash
kubectl set image deployment/webapp nginx=nginx:broken --record
kubectl rollout status deployment/webapp  # Will hang or fail
kubectl get pods  # Some in ImagePullBackOff
```

7. **Відкотіться до попередньої версії**:
```bash
kubectl rollout undo deployment/webapp
kubectl rollout status deployment/webapp
kubectl get pods  # Back to healthy state
```

8. **Перевірте історію та відкотіться до конкретної ревізії**:
```bash
kubectl rollout history deployment/webapp
kubectl rollout undo deployment/webapp --to-revision=1
kubectl rollout status deployment/webapp
```

9. **Очищення**:
```bash
kubectl delete deployment webapp
```

**Критерії успіху**:
- [ ] Вмію створювати деплойменти імперативно та декларативно
- [ ] Розумію ієрархію Деплоймент → ReplicaSet → Под
- [ ] Вмію масштабувати деплойменти
- [ ] Вмію виконувати поступові оновлення
- [ ] Вмію робити відкат до попередніх версій
- [ ] Розумію історію розгортань

---

## Практичні вправи

### Вправа 1: Тест на швидкість створення Деплойменту (Ціль: 2 хвилини)

```bash
# Create deployment
kubectl create deployment nginx --image=nginx:1.25 --replicas=3

# Verify
kubectl rollout status deployment/nginx
kubectl get deploy nginx
kubectl get rs
kubectl get pods -l app=nginx

# Cleanup
kubectl delete deployment nginx
```

### Вправа 2: Поступове оновлення (Ціль: 3 хвилини)

```bash
# Create deployment
kubectl create deployment web --image=nginx:1.24 --replicas=4

# Wait for ready
kubectl rollout status deployment/web

# Update image
kubectl set image deployment/web nginx=nginx:1.25

# Watch the rollout
kubectl rollout status deployment/web

# Verify new image
kubectl get deployment web -o jsonpath='{.spec.template.spec.containers[0].image}'

# Cleanup
kubectl delete deployment web
```

### Вправа 3: Відкат (Ціль: 3 хвилини)

```bash
# Create deployment
kubectl create deployment app --image=nginx:1.24 --replicas=3
kubectl rollout status deployment/app

# Update 1
kubectl set image deployment/app nginx=nginx:1.25 --record
kubectl rollout status deployment/app

# Update 2 (bad version)
kubectl set image deployment/app nginx=nginx:bad --record
# Don't wait - it will fail

# Check history
kubectl rollout history deployment/app

# Rollback
kubectl rollout undo deployment/app
kubectl rollout status deployment/app

# Verify rolled back
kubectl get deployment app -o jsonpath='{.spec.template.spec.containers[0].image}'
# Should be nginx:1.25

# Cleanup
kubectl delete deployment app
```

### Вправа 4: Масштабування (Ціль: 2 хвилини)

```bash
# Create deployment
kubectl create deployment scale-test --image=nginx --replicas=2

# Scale up
kubectl scale deployment scale-test --replicas=5
kubectl get pods -l app=scale-test

# Scale down
kubectl scale deployment scale-test --replicas=1
kubectl get pods -l app=scale-test

# Scale to zero
kubectl scale deployment scale-test --replicas=0
kubectl get pods -l app=scale-test  # No pods

# Scale back up
kubectl scale deployment scale-test --replicas=3

# Cleanup
kubectl delete deployment scale-test
```

### Вправа 5: Призупинення та Відновлення (Ціль: 3 хвилини)

```bash
# Create deployment
kubectl create deployment paused --image=nginx:1.24 --replicas=2
kubectl rollout status deployment/paused

# Pause
kubectl rollout pause deployment/paused

# Make multiple changes (no rollout triggered)
kubectl set image deployment/paused nginx=nginx:1.25
kubectl set env deployment/paused ENV=production
kubectl set resources deployment/paused -c nginx --requests=cpu=100m

# Check - still old image
kubectl get deployment paused -o jsonpath='{.spec.template.spec.containers[0].image}'

# Resume - single rollout
kubectl rollout resume deployment/paused
kubectl rollout status deployment/paused

# Verify all changes applied
kubectl get deployment paused -o yaml | grep -E "image:|ENV|cpu"

# Cleanup
kubectl delete deployment paused
```

### Вправа 6: Стратегія Recreate (Ціль: 3 хвилини)

```bash
# Create deployment with Recreate strategy
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recreate-demo
spec:
  replicas: 3
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: recreate-demo
  template:
    metadata:
      labels:
        app: recreate-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.24
EOF

kubectl rollout status deployment/recreate-demo

# Update - watch all pods terminate then new ones create
kubectl set image deployment/recreate-demo nginx=nginx:1.25

# Watch pods (all old terminate, then all new create)
kubectl get pods -w -l app=recreate-demo

# Cleanup
kubectl delete deployment recreate-demo
```

### Вправа 7: Генерація та модифікація YAML (Ціль: 5 хвилин)

```bash
# Generate YAML
kubectl create deployment myapp --image=nginx:1.25 --replicas=3 --dry-run=client -o yaml > myapp.yaml

# View generated YAML
cat myapp.yaml

# Add resource limits using sed or edit
cat << 'EOF' >> myapp.yaml
---
# Note: Need to edit the file properly, this is just for demonstration
EOF

# Apply the deployment
kubectl apply -f myapp.yaml

# Update via edit
kubectl edit deployment myapp
# Change replicas to 5, save

# Verify
kubectl get deployment myapp

# Cleanup
kubectl delete -f myapp.yaml
rm myapp.yaml
```

### Вправа 8: Виклик - Повний життєвий цикл

Не підглядаючи в рішення, виконайте цей робочий процес менш ніж за 5 хвилин:

1. Створіть деплоймент `lifecycle-test` з nginx:1.24, 3 репліки
2. Масштабуйте до 5 реплік
3. Оновіть до nginx:1.25
4. Перевірте історію розгортань
5. Оновіть до nginx:1.26
6. Відкотіться до nginx:1.24 (ревізія 1)
7. Видаліть деплоймент

```bash
# YOUR TASK: Complete the workflow
```

<details>
<summary>Рішення</summary>

```bash
# 1. Create
kubectl create deployment lifecycle-test --image=nginx:1.24 --replicas=3
kubectl rollout status deployment/lifecycle-test

# 2. Scale
kubectl scale deployment lifecycle-test --replicas=5

# 3. Update to 1.25
kubectl set image deployment/lifecycle-test nginx=nginx:1.25 --record
kubectl rollout status deployment/lifecycle-test

# 4. Check history
kubectl rollout history deployment/lifecycle-test

# 5. Update to 1.26
kubectl set image deployment/lifecycle-test nginx=nginx:1.26 --record
kubectl rollout status deployment/lifecycle-test

# 6. Rollback to revision 1
kubectl rollout undo deployment/lifecycle-test --to-revision=1
kubectl rollout status deployment/lifecycle-test

# Verify it's 1.24
kubectl get deployment lifecycle-test -o jsonpath='{.spec.template.spec.containers[0].image}'

# 7. Delete
kubectl delete deployment lifecycle-test
```

</details>

---

## Наступний модуль

[Модуль 2.3: DaemonSets та StatefulSets](module-2.3-daemonsets-statefulsets/) — Спеціалізовані контролери робочих навантажень.
