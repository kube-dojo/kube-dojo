---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 4: \u0414\u0435\u043f\u043b\u043e\u0439\u043c\u0435\u043d\u0442\u0438 \u2014 \u0423\u043f\u0440\u0430\u0432\u043b\u0456\u043d\u043d\u044f \u0437\u0430\u0441\u0442\u043e\u0441\u0443\u043d\u043a\u0430\u043c\u0438"
sidebar:
  order: 5
---
> **Складність**: `[MEDIUM]` — Основи управління навантаженнями
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Модуль 3 (Поди)

---

## Чому цей модуль важливий

У продакшені ви ніколи не створюєте Поди напряму. Ви використовуєте Деплойменти. Деплойменти керують Подами за вас — автоматично обробляючи масштабування, оновлення та самовідновлення.

---

## Навіщо потрібні Деплойменти?

Поди самі по собі мають проблеми:

```
┌─────────────────────────────────────────────────────────────┐
│          ПОДИ БЕЗ ДЕПЛОЙМЕНТУ vs З ДЕПЛОЙМЕНТОМ             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ГОЛИЙ ПОД:                                                │
│  - Под помирає → залишається мертвим                       │
│  - Нода падає → Под втрачено                               │
│  - Не можна легко масштабувати                              │
│  - Оновлення потребує ручного видалення/створення          │
│                                                             │
│  З ДЕПЛОЙМЕНТОМ:                                            │
│  - Под помирає → автоматично перестворюється               │
│  - Нода падає → переплановується на іншу                   │
│  - Масштабування однією командою                           │
│  - Поступові оновлення без простою                         │
│  - Відкат до попередніх версій                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Створення Деплойментів

### Імперативний спосіб (для швидкого тестування)

```bash
# Create deployment
kubectl create deployment nginx --image=nginx

# With replicas
kubectl create deployment nginx --image=nginx --replicas=3

# Dry run to see YAML
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml
```

### Декларативний спосіб (для продакшену)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 3                    # Number of pod copies
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

```bash
kubectl apply -f deployment.yaml
```

---

## Архітектура Деплойменту

```
┌─────────────────────────────────────────────────────────────┐
│              ІЄРАРХІЯ ДЕПЛОЙМЕНТУ                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   ДЕПЛОЙМЕНТ                         │   │
│  │  - Визначає бажаний стан                            │   │
│  │  - Керує ReplicaSet-ами                             │   │
│  │  - Обробляє оновлення/відкати                       │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   REPLICASET                        │   │
│  │  - Забезпечує роботу N подів                        │   │
│  │  - Створюється/керується Деплойментом               │   │
│  │  - Зазвичай з ним не взаємодіють напряму            │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                     │
│         ┌─────────────┼─────────────┐                      │
│         ▼             ▼             ▼                      │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐               │
│  │    ПОД    │ │    ПОД    │ │    ПОД    │               │
│  │   nginx   │ │   nginx   │ │   nginx   │               │
│  └───────────┘ └───────────┘ └───────────┘               │
│                                                             │
│  replicas: 3 → 3 поди підтримуються автоматично            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Типові операції

### Перегляд Деплойментів

```bash
# List deployments
kubectl get deployments
kubectl get deploy              # Short form

# Detailed info
kubectl describe deployment nginx

# See related resources
kubectl get deploy,rs,pods
```

### Масштабування

```bash
# Scale up/down
kubectl scale deployment nginx --replicas=5

# Or edit YAML and apply
kubectl edit deployment nginx
# Change replicas, save

# Watch pods scale
kubectl get pods -w
```

### Оновлення (поступове розгортання)

```bash
# Update image
kubectl set image deployment/nginx nginx=nginx:1.26

# Or edit deployment
kubectl edit deployment nginx

# Watch rollout
kubectl rollout status deployment nginx

# View rollout history
kubectl rollout history deployment nginx
```

### Відкат

```bash
# Undo last change
kubectl rollout undo deployment nginx

# Rollback to specific revision
kubectl rollout history deployment nginx
kubectl rollout undo deployment nginx --to-revision=2
```

---

## Стратегія поступового оновлення (Rolling Update)

Деплойменти оновлюють Поди поступово:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max extra pods during update
      maxUnavailable: 25%  # Max pods that can be unavailable
```

```
┌─────────────────────────────────────────────────────────────┐
│          ПРОЦЕС ПОСТУПОВОГО ОНОВЛЕННЯ                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Початковий стан (3 репліки, v1):                          │
│  [v1] [v1] [v1]                                            │
│                                                             │
│  Оновлення до v2 починається:                              │
│  [v1] [v1] [v1] [v2]    ← Новий под створено               │
│                                                             │
│  Новий под готовий:                                        │
│  [v1] [v1] [v2] [v2]    ← Старий под зупинено              │
│                                                             │
│  Продовження:                                              │
│  [v1] [v2] [v2] [v2]                                       │
│                                                             │
│  Завершено:                                                │
│  [v2] [v2] [v2]         ← Усі поди оновлено               │
│                                                             │
│  Нуль простою! Трафік обслуговувався протягом усього       │
│  процесу.                                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Пояснення YAML Деплойменту

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 3                    # Desired pod count
  selector:
    matchLabels:
      app: nginx                 # Must match template labels
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:                      # Pod template (same as Pod spec)
    metadata:
      labels:
        app: nginx               # Labels for service discovery
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

---

## Самовідновлення в дії

```bash
# Create deployment
kubectl create deployment nginx --image=nginx --replicas=3

# See pods
kubectl get pods

# Delete a pod
kubectl delete pod <pod-name>

# Immediately check again
kubectl get pods
# A new pod is already being created!

# The deployment maintains desired state
kubectl get deployment nginx
# READY shows 3/3
```

---

## Чи знали ви?

- **Деплойменти не керують Подами напряму.** Вони керують ReplicaSet-ами, які керують Подами. Це забезпечує можливість відкату.

- **Кожне оновлення створює новий ReplicaSet.** Старі ReplicaSet-и зберігаються (з 0 реплік) для історії відкатів.

- **`maxSurge: 0, maxUnavailable: 0` — неможлива комбінація.** Не можна оновити без створення нових подів або зупинки старих.

- **`kubectl rollout restart`** запускає нове розгортання без зміни специфікації. Корисно для завантаження нових образів з тим самим тегом.

---

## Типові помилки

| Помилка | Наслідки | Рішення |
|---------|----------|---------|
| Селектор не відповідає міткам шаблону | Деплоймент не керуватиме подами | Переконайтеся, що мітки збігаються |
| Використання тегу :latest | Неможливий осмислений відкат | Використовуйте конкретні теги версій |
| Відсутність лімітів ресурсів | Може вплинути на інші навантаження | Завжди встановлюйте ресурси |
| Не чекати завершення розгортання | Проблеми можуть виявитись пізніше | Використовуйте `rollout status` |

---

## Тест

1. **Який зв'язок між Деплойментом, ReplicaSet та Подом?**
   <details>
   <summary>Відповідь</summary>
   Деплоймент керує ReplicaSet-ами. ReplicaSet керує Подами. Ви взаємодієте з Деплойментами — вони автоматично обробляють решту. ReplicaSet-и забезпечують відкат, зберігаючи старі версії.
   </details>

2. **Що станеться, якщо видалити Под, яким керує Деплоймент?**
   <details>
   <summary>Відповідь</summary>
   Деплоймент (через ReplicaSet) автоматично створить новий Под, щоб підтримувати бажану кількість реплік. Це і є самовідновлення.
   </details>

3. **Як виконати відкат Деплойменту до попередньої версії?**
   <details>
   <summary>Відповідь</summary>
   `kubectl rollout undo deployment DEPLOYMENT_NAME`. Для конкретної ревізії: `kubectl rollout undo deployment DEPLOYMENT_NAME --to-revision=N`.
   </details>

4. **Що контролює `maxSurge` під час поступового оновлення?**
   <details>
   <summary>Відповідь</summary>
   Максимальну кількість подів, які можуть бути створені понад бажану кількість реплік під час оновлення. `maxSurge: 25%` з 4 репліками дозволяє тимчасово мати 5 подів.
   </details>

---

## Практична вправа

**Завдання**: Створіть Деплоймент, масштабуйте його, оновіть і виконайте відкат.

```bash
# 1. Create deployment
kubectl create deployment web --image=nginx:1.24

# 2. Scale to 3 replicas
kubectl scale deployment web --replicas=3

# 3. Verify
kubectl get deploy,rs,pods

# 4. Update image
kubectl set image deployment/web nginx=nginx:1.25

# 5. Watch rollout
kubectl rollout status deployment web

# 6. Check history
kubectl rollout history deployment web

# 7. Simulate problem - rollback
kubectl rollout undo deployment web

# 8. Verify rollback
kubectl get deployment web -o jsonpath='{.spec.template.spec.containers[0].image}'
# Should show nginx:1.24

# 9. Cleanup
kubectl delete deployment web
```

**Критерії успіху**: Деплоймент, масштабування, оновлення та відкат працюють коректно.

---

## Підсумок

Деплойменти керують вашими застосунками:

**Можливості**:
- Декларативні оновлення
- Поступові оновлення (нуль простою)
- Можливість відкату
- Самовідновлення
- Легке масштабування

**Основні команди**:
- `kubectl create deployment`
- `kubectl scale deployment`
- `kubectl set image`
- `kubectl rollout status`
- `kubectl rollout undo`

**Найкращі практики**:
- Завжди використовуйте Деплойменти (не голі Поди)
- Використовуйте конкретні теги образів
- Встановлюйте запити/ліміти ресурсів

---

## Наступний модуль

[Модуль 5: Сервіси](module-1.5-services/) — Стабільна мережева взаємодія для ваших Подів.
