---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 8: YAML \u0434\u043b\u044f Kubernetes"
sidebar:
  order: 9
---
> **Складність**: `[MEDIUM]` — Необхідна навичка
>
> **Час на виконання**: 35-40 хвилин
>
> **Передумови**: Попередні модулі (знайомство з ресурсами K8s)

---

## Чому цей модуль важливий

Кожен ресурс Kubernetes описується у YAML. Розуміння синтаксису YAML та структури ресурсів K8s є необхідним для:
- Написання маніфестів
- Розуміння прикладів та документації
- Налагодження помилок конфігурації
- Сертифікаційних іспитів

---

## Основи YAML

### Структура

```yaml
# This is a comment

# Scalars (simple values)
string: hello
number: 42
float: 3.14
boolean: true
null_value: null

# Lists (arrays)
items:
- item1
- item2
- item3

# Or inline
items: [item1, item2, item3]

# Maps (objects)
person:
  name: John
  age: 30

# Or inline
person: {name: John, age: 30}
```

### Правила відступів

```yaml
# YAML uses spaces, NOT tabs
# Typically 2 spaces per level

parent:
  child:
    grandchild: value

# Wrong (tabs will break):
parent:
	child:      # This is a tab - WRONG!
```

### Багаторядкові рядки

```yaml
# Literal block (preserves newlines)
literal: |
  Line 1
  Line 2
  Line 3

# Folded block (joins lines with spaces)
folded: >
  This is a
  very long
  sentence.
# Results in: "This is a very long sentence."
```

---

## Структура ресурсів Kubernetes

Кожен ресурс K8s має таку структуру:

```yaml
apiVersion: v1              # API version
kind: Pod                   # Resource type
metadata:                   # Resource metadata
  name: my-pod
  namespace: default
  labels:
    app: myapp
  annotations:
    description: "My pod"
spec:                       # Desired state (varies by resource)
  containers:
  - name: main
    image: nginx
status:                     # Current state (managed by K8s, read-only)
  phase: Running
```

### Обов'язкові поля

| Поле | Опис |
|------|------|
| `apiVersion` | Версія API для цього типу ресурсу |
| `kind` | Тип ресурсу |
| `metadata.name` | Унікальне ім'я в межах простору імен |
| `spec` | Бажаний стан (залежить від типу ресурсу) |

---

## Поширені версії API

| Ресурс | apiVersion |
|--------|------------|
| Pod, Service, ConfigMap, Secret | `v1` |
| Deployment, ReplicaSet | `apps/v1` |
| Ingress | `networking.k8s.io/v1` |
| NetworkPolicy | `networking.k8s.io/v1` |
| PersistentVolume, PVC | `v1` |
| StorageClass | `storage.k8s.io/v1` |
| Role, ClusterRole | `rbac.authorization.k8s.io/v1` |

```bash
# Find API version for any resource
kubectl api-resources | grep -i deployment
# deployments    deploy    apps/v1    true    Deployment
```

---

## Генерація YAML (не заучуйте!)

Ніколи не пишіть YAML з нуля — генеруйте його:

```bash
# Generate Pod YAML
kubectl run nginx --image=nginx --dry-run=client -o yaml

# Generate Deployment YAML
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml

# Generate Service YAML
kubectl expose deployment nginx --port=80 --dry-run=client -o yaml

# Save to file
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml
```

### Команда explain (документація)

```bash
# Get field documentation
kubectl explain pod
kubectl explain pod.spec
kubectl explain pod.spec.containers
kubectl explain pod.spec.containers.resources

# Recursive (all fields)
kubectl explain pod.spec --recursive | less
```

---

## Типові шаблони

### Шаблон Пода (у Деплойментах)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:                    # Pod template starts here
    metadata:
      labels:
        app: myapp             # Must match selector
    spec:
      containers:
      - name: main
        image: nginx:1.25
        ports:
        - containerPort: 80
```

### Змінні середовища

```yaml
containers:
- name: app
  image: myapp
  env:
  # Direct value
  - name: LOG_LEVEL
    value: "debug"
  # From ConfigMap
  - name: DB_HOST
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: database_host
  # From Secret
  - name: DB_PASS
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: password
```

### Монтування томів

```yaml
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: config
      mountPath: /etc/config
    - name: data
      mountPath: /data
  volumes:
  - name: config
    configMap:
      name: app-config
  - name: data
    persistentVolumeClaim:
      claimName: app-pvc
```

### Вимоги до ресурсів

```yaml
containers:
- name: app
  image: myapp
  resources:
    requests:
      memory: "64Mi"
      cpu: "250m"
    limits:
      memory: "128Mi"
      cpu: "500m"
```

---

## Декілька документів

```yaml
# First document
apiVersion: v1
kind: ConfigMap
metadata:
  name: config
data:
  key: value
---                          # Document separator
# Second document
apiVersion: v1
kind: Service
metadata:
  name: service
spec:
  # ...
---                          # Another document
apiVersion: apps/v1
kind: Deployment
# ...
```

```bash
# Apply all documents in file
kubectl apply -f multi-doc.yaml
```

---

## Валідація

```bash
# Server-side validation (dry-run)
kubectl apply -f pod.yaml --dry-run=server

# Client-side validation
kubectl apply -f pod.yaml --dry-run=client

# Validate without applying
kubectl create -f pod.yaml --dry-run=client --validate=true

# Check YAML syntax
kubectl apply -f pod.yaml --dry-run=client -o yaml
```

---

## Типові помилки YAML

### Відступи

```yaml
# WRONG - inconsistent indentation
spec:
  containers:
   - name: app    # 3 spaces
    image: nginx  # 4 spaces - ERROR!

# CORRECT
spec:
  containers:
  - name: app
    image: nginx
```

### Лапки

```yaml
# Some values need quotes

# WRONG - colon causes parsing error
message: Error: something failed

# CORRECT
message: "Error: something failed"

# Numbers that should be strings
port: "8080"   # If you need string, quote it
```

### Логічні значення

```yaml
# These are all true:
enabled: true
enabled: True
enabled: yes
enabled: on

# These are all false:
enabled: false
enabled: False
enabled: no
enabled: off

# Be careful with strings that look like booleans
value: "yes"    # This is string "yes"
value: yes      # This is boolean true
```

---

## Чи знали ви?

- **JSON — це валідний YAML.** YAML є надмножиною JSON. Ви можете вставляти JSON у YAML-файли.

- **K8s ігнорує невідомі поля** за замовчуванням. Помилки в назвах полів не викликають помилку — вони мовчки ігноруються.

- **`kubectl explain` — ваш найкращий друг.** Він показує документацію для будь-якого поля, отриману з API.

- **Серверний dry-run валідує відносно кластера.** Він виявляє більше помилок, ніж клієнтський.

---

## Тест

1. **Яка різниця між `--dry-run=client` і `--dry-run=server`?**
   <details>
   <summary>Відповідь</summary>
   Клієнтська валідація перевіряє лише синтаксис YAML. Серверна надсилає запит до API-сервера, який валідує відповідно до схеми та стану кластера (наприклад, перевіряє, чи існують посилання на ConfigMap).
   </details>

2. **Як знайти правильний apiVersion для ресурсу?**
   <details>
   <summary>Відповідь</summary>
   `kubectl api-resources | grep RESOURCE` показує групу/версію API. Або використовуйте `kubectl explain RESOURCE`, який показує версію вгорі.
   </details>

3. **Що означає `---` у YAML-файлі?**
   <details>
   <summary>Відповідь</summary>
   Роздільник документів. Один YAML-файл може містити декілька документів (ресурсів). `kubectl apply -f` обробляє всі документи у файлі.
   </details>

4. **Як переглянути документацію для конкретного поля?**
   <details>
   <summary>Відповідь</summary>
   `kubectl explain RESOURCE.FIELD.PATH`, наприклад, `kubectl explain pod.spec.containers.resources`
   </details>

---

## Практична вправа

**Завдання**: Попрактикуйтеся з генерацією та валідацією YAML.

```bash
# 1. Generate deployment YAML
kubectl create deployment web --image=nginx --replicas=3 --dry-run=client -o yaml > web.yaml

# 2. View it
cat web.yaml

# 3. Add resource limits (edit the file)
# Add under containers[0]:
#   resources:
#     requests:
#       memory: "64Mi"
#       cpu: "100m"
#     limits:
#       memory: "128Mi"
#       cpu: "200m"

# 4. Validate
kubectl apply -f web.yaml --dry-run=server

# 5. Apply
kubectl apply -f web.yaml

# 6. Verify
kubectl get deployment web

# 7. Generate service YAML
kubectl expose deployment web --port=80 --dry-run=client -o yaml > service.yaml

# 8. Apply service
kubectl apply -f service.yaml

# 9. Use explain
kubectl explain deployment.spec.strategy

# 10. Cleanup
kubectl delete -f web.yaml -f service.yaml
rm web.yaml service.yaml
```

**Критерії успіху**: Ресурси створено зі згенерованого YAML.

---

## Підсумок

**Основи YAML**:
- Пробіли для відступів (не табуляція)
- `-` для елементів списку
- `:` для пар ключ-значення
- `---` розділяє документи

**Структура ресурсів K8s**:
- apiVersion, kind, metadata, spec
- Використовуйте `kubectl explain` для документації полів
- Використовуйте `--dry-run=client -o yaml` для генерації

**Валідація**:
- `--dry-run=client` для синтаксису
- `--dry-run=server` для повної валідації

**Найкращі практики**:
- Ніколи не пишіть YAML з нуля
- Генеруйте, модифікуйте, застосовуйте
- Використовуйте `kubectl explain` якомога частіше

---

## Трек завершено!

Вітаємо! Ви завершили трек **Основи Kubernetes**. Тепер ви розумієте:

1. Налаштування локального кластера (kind)
2. Команди та шаблони kubectl
3. Поди — атомарна одиниця
4. Деплойменти — управління застосунками
5. Сервіси — стабільна мережа
6. ConfigMap та Secret — конфігурація
7. Простори імен та мітки — організація
8. YAML для Kubernetes — написання маніфестів

**Наступні кроки**:
- [Програма CKA](../../k8s/cka/part0-environment/module-0.1-cluster-setup/) — Сертифікація адміністратора
- [Програма CKAD](../../k8s/ckad/part0-environment/module-0.1-ckad-overview/) — Сертифікація розробника
- [Сучасні DevOps-практики](../modern-devops/module-1.1-infrastructure-as-code/) — Додаткові навички
