---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 3: \u041f\u043e\u0434\u0438 \u2014 \u0430\u0442\u043e\u043c\u0430\u0440\u043d\u0430 \u043e\u0434\u0438\u043d\u0438\u0446\u044f"
sidebar:
  order: 4
---
> **Складність**: `[MEDIUM]` — основна концепція, потрібна практика
>
> **Час на виконання**: 40–45 хвилин
>
> **Передумови**: Модуль 2 (основи kubectl)

---

## Чому цей модуль важливий

Поди — найменша одиниця розгортання в Kubernetes. Кожен контейнер, який ви запускаєте в K8s, працює всередині Пода. Розуміння Подів є фундаментальним — усе інше будується на цій концепції.

---

## Що таке Под?

Под — це обгортка навколо одного або кількох контейнерів:

```
┌─────────────────────────────────────────────────────────────┐
│                          ПОД                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Под                               │   │
│  │  ┌─────────────┐     ┌─────────────┐               │   │
│  │  │  Контейнер  │     │  Контейнер  │ (додатковий) │   │
│  │  │ (основний)  │     │  (sidecar)  │               │   │
│  │  └─────────────┘     └─────────────┘               │   │
│  │                                                     │   │
│  │  Спільне:                                          │   │
│  │  • Мережевий простір імен (та сама IP, localhost)  │   │
│  │  • Томи зберігання                                 │   │
│  │  • Життєвий цикл Пода                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Контейнери в Поді:                                        │
│  - Мають спільну IP-адресу                                 │
│  - Можуть спілкуватися через localhost                     │
│  - Мають спільні змонтовані томи                           │
│  - Плануються разом на одному вузлі                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Ключові моменти

- **Один контейнер на Под — це типово.** Багатоконтейнерні Поди використовуються для конкретних патернів (sidecar, adapter).
- **Поди ефемерні.** Їх можуть зупинити й замінити в будь-який момент.
- **Под отримує унікальну IP-адресу.** Інші Поди можуть звертатися до нього за цією IP.
- **Поди не самовідновлюються.** Якщо Под помирає, він залишається мертвим (якщо ним не керує контролер).

---

## Створення Подів

### Імперативний спосіб (швидке тестування)

```bash
# Simple pod
kubectl run nginx --image=nginx

# With port
kubectl run nginx --image=nginx --port=80

# With labels
kubectl run nginx --image=nginx --labels="app=web,tier=frontend"

# Dry run to see YAML
kubectl run nginx --image=nginx --dry-run=client -o yaml
```

### Декларативний спосіб (продакшн-підхід)

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
```

```bash
kubectl apply -f pod.yaml
```

---

## Структура YAML для Пода

```yaml
apiVersion: v1          # API version
kind: Pod               # Resource type
metadata:               # Metadata
  name: nginx           # Pod name (required)
  namespace: default    # Namespace (optional, defaults to current)
  labels:               # Key-value pairs for selection
    app: nginx
    environment: dev
  annotations:          # Non-identifying metadata
    description: "My nginx pod"
spec:                   # Desired state
  containers:           # List of containers
  - name: nginx         # Container name
    image: nginx:1.25   # Container image
    ports:              # Exposed ports
    - containerPort: 80
    env:                # Environment variables
    - name: MY_VAR
      value: "my-value"
    resources:          # Resource requests/limits
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
```

---

## Життєвий цикл Пода

```
┌─────────────────────────────────────────────────────────────┐
│              СТАНИ ЖИТТЄВОГО ЦИКЛУ ПОДА                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pending ──► Running ──► Succeeded/Failed                  │
│     │           │                                           │
│     │           ▼                                           │
│     │       Unknown (вузол втратив зв'язок)               │
│     │                                                       │
│     ▼                                                       │
│  Failed (помилка завантаження образу тощо)                │
│                                                             │
│  СТАНИ:                                                    │
│  • Pending    - Очікує планування або завантаження образу  │
│  • Running    - Принаймні один контейнер працює            │
│  • Succeeded  - Усі контейнери завершилися успішно         │
│  • Failed     - Принаймні один контейнер завершився з помилкою │
│  • Unknown    - Неможливо визначити стан (проблеми з вузлом) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Стани контейнерів

```bash
kubectl get pod nginx -o jsonpath='{.status.containerStatuses[0].state}'
```

- **Waiting**: Контейнер ще не запущений (завантаження образу тощо)
- **Running**: Контейнер виконується
- **Terminated**: Контейнер завершив роботу (успішно або з помилкою)

---

## Типові операції з Подами

### Перегляд Подів

```bash
# List pods
kubectl get pods
kubectl get pods -o wide          # More info (IP, node)
kubectl get pods --show-labels    # Show labels

# Detailed info
kubectl describe pod nginx

# Watch pod status
kubectl get pods -w
```

### Налагодження Подів

```bash
# View logs
kubectl logs nginx
kubectl logs nginx -f             # Follow
kubectl logs nginx --previous     # Previous container instance

# Execute commands
kubectl exec nginx -- ls /
kubectl exec -it nginx -- bash    # Interactive shell

# Get events
kubectl get events --field-selector involvedObject.name=nginx
```

### Доступ до Подів

```bash
# Port forward
kubectl port-forward pod/nginx 8080:80
# Now access at localhost:8080

# Get pod IP
kubectl get pod nginx -o jsonpath='{.status.podIP}'
```

### Зміна Подів

```bash
# Edit (limited for pods)
kubectl edit pod nginx

# Delete and recreate
kubectl delete pod nginx
kubectl apply -f pod.yaml

# Force delete stuck pod
kubectl delete pod nginx --force --grace-period=0
```

---

## Змінні середовища

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: env-demo
spec:
  containers:
  - name: demo
    image: busybox
    command: ['sh', '-c', 'echo $GREETING $NAME && sleep 3600']
    env:
    - name: GREETING
      value: "Hello"
    - name: NAME
      value: "Kubernetes"
```

```bash
kubectl apply -f env-demo.yaml
kubectl logs env-demo
# Output: Hello Kubernetes
```

---

## Запити та ліміти ресурсів

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: demo
    image: nginx
    resources:
      requests:          # Minimum guaranteed
        memory: "64Mi"
        cpu: "250m"      # 0.25 CPU cores
      limits:            # Maximum allowed
        memory: "128Mi"
        cpu: "500m"
```

```
┌─────────────────────────────────────────────────────────────┐
│              ЗАПИТИ vs ЛІМІТИ                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ЗАПИТ = Мінімум гарантованих ресурсів                     │
│  - Використовується для прийняття рішень при плануванні    │
│  - Под не буде заплановано, якщо вузол не має цих ресурсів │
│                                                             │
│  ЛІМІТ = Максимум дозволених ресурсів                      │
│  - Контейнер може використовувати до цієї кількості        │
│  - CPU: обмежується при перевищенні                        │
│  - Пам'ять: OOMKilled при перевищенні                      │
│                                                             │
│  Приклад:                                                   │
│  requests:                                                  │
│    cpu: "250m"     # 0.25 ядра гарантовано                 │
│    memory: "64Mi"  # 64 МБ гарантовано                     │
│  limits:                                                    │
│    cpu: "500m"     # Може використати до 0.5 ядра          │
│    memory: "128Mi" # Зупиняється при перевищенні 128 МБ    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **IP-адреси Подів є внутрішніми для кластера.** Ви не можете отримати доступ до IP Пода ззовні кластера напряму.

- **Поди — це худоба, а не домашні улюбленці.** Вони створені для заміни. Ніколи не покладайтеся на існування конкретного Пода.

- **localhost працює між контейнерами в Поді.** Вони мають спільний мережевий простір імен.

- **Под без контролера називають «голим».** Якщо він помирає, ніщо його не відтворить. Завжди використовуйте Деплойменти у продакшні.

---

## Типові помилки

| Помилка | Чим шкодить | Розв'язання |
|---------|-------------|-------------|
| Використання Подів напряму | Немає самовідновлення чи масштабування | Використовуйте Деплойменти |
| Без лімітів ресурсів | Може позбавити ресурсів інші Поди | Завжди встановлюйте ресурси |
| Використання тегу :latest | Непередбачувані версії | Використовуйте конкретні теги |
| Ігнорування статусу Пода | Пропуск збоїв | Перевіряйте `kubectl get pods` |

---

## Тест

1. **Що таке Под?**
   <details>
   <summary>Відповідь</summary>
   Под — це найменша одиниця розгортання в Kubernetes — обгортка навколо одного або кількох контейнерів, які мають спільну мережу та сховище. Контейнери в Поді мають спільну IP-адресу й можуть спілкуватися через localhost.
   </details>

2. **Чому не варто використовувати «голі» Поди у продакшні?**
   <details>
   <summary>Відповідь</summary>
   «Голі» Поди не самовідновлюються. Якщо Под помирає або вузол виходить з ладу — Под зникає. Використовуйте Деплойменти або інші контролери, які автоматично відтворюють Поди після збою.
   </details>

3. **Яка різниця між запитами та лімітами ресурсів?**
   <details>
   <summary>Відповідь</summary>
   Запити — це гарантований мінімум ресурсів (використовуються для планування). Ліміти — це максимуми (застосовуються під час виконання). CPU понад ліміт = обмеження. Пам'ять понад ліміт = OOMKilled.
   </details>

4. **Як контейнери в одному Поді спілкуються між собою?**
   <details>
   <summary>Відповідь</summary>
   Через localhost. Контейнери в Поді мають спільний мережевий простір імен, тому вони можуть використовувати localhost або 127.0.0.1 з різними портами.
   </details>

---

## Практична вправа

**Завдання**: Створити, переглянути та налагодити Под.

```bash
# 1. Create pod YAML
cat << 'EOF' > my-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: demo
spec:
  containers:
  - name: demo
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
EOF

# 2. Create the pod
kubectl apply -f my-pod.yaml

# 3. Watch it start
kubectl get pods -w

# 4. Get detailed info
kubectl describe pod my-pod

# 5. View logs
kubectl logs my-pod

# 6. Execute command in pod
kubectl exec my-pod -- nginx -v

# 7. Port forward and test
kubectl port-forward pod/my-pod 8080:80 &
curl localhost:8080
kill %1  # Stop port-forward

# 8. Cleanup
kubectl delete -f my-pod.yaml
rm my-pod.yaml
```

**Критерії успіху**: Под працює, логи видно, port-forward працює.

---

## Підсумок

Поди — це фундамент:

**Що вони собою являють**:
- Найменша одиниця розгортання
- Обгортка навколо контейнерів
- Спільна мережа та сховище

**Ключові операції**:
- `kubectl run` / `kubectl apply -f`
- `kubectl get pods`
- `kubectl describe pod`
- `kubectl logs`
- `kubectl exec`

**Найкращі практики**:
- Використовуйте контролери (Деплойменти), а не «голі» Поди
- Встановлюйте запити та ліміти ресурсів
- Використовуйте конкретні теги образів

---

## Наступний модуль

[Модуль 4: Деплойменти](module-1.4-deployments/) — керування застосунками у масштабі.
