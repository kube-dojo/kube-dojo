---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2.1: \u041f\u043e\u0433\u043b\u0438\u0431\u043b\u0435\u043d\u0435 \u0432\u0438\u0432\u0447\u0435\u043d\u043d\u044f \u041f\u043e\u0434\u0456\u0432"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.1-pods
sidebar: 
  order: 2
lab: 
  id: cka-2.1-pods
  url: https://killercoda.com/kubedojo/scenario/cka-2.1-pods
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[СЕРЕДНЯ]` — Основа для всіх робочих навантажень
>
> **Час на проходження**: 40-50 хвилин
>
> **Передумови**: Модуль 1.1 (Площина управління), Модуль 0.2 (Майстерність роботи з оболонкою)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** поди імперативно та декларативно з ресурсними запитами, пробами та контекстами безпеки
- **Дебажити** збої подів систематично (Pending → перевірити планування, CrashLoop → перевірити логи, ImagePull → перевірити реєстр)
- **Налаштувати** liveness, readiness та startup проби й пояснити, коли використовувати кожну з них
- **Пояснити** життєвий цикл пода (init-контейнери → основні контейнери → завершення) з періодами очікування

---

## Чому цей модуль важливий

Поди є **атомарною одиницею розгортання** в Kubernetes. Кожен запущений вами контейнер живе всередині пода. Кожен Деплоймент, StatefulSet, DaemonSet та Job створює поди. Якщо ви глибоко не розумієте поди, вам буде важко з усім іншим.

Іспит CKA перевіряє створення подів, усунення несправностей та патерни з кількома контейнерами. Вам потрібно буде швидко створювати поди, налагоджувати поди, що дають збій, і розуміти, як взаємодіють контейнери всередині пода.

> **Аналогія з квартирою**
>
> Уявіть под як квартиру. Контейнери — це співмешканці, які ділять квартиру. Вони мають спільну адресу (IP), спільний життєвий простір (мережевий простір імен) і можуть ділити сховище (томи). Вони мають власні кімнати (файлова система), але можуть легко спілкуватися один з одним (localhost). Коли квартиру зносять (под видаляється), всі співмешканці йдуть разом.

---

## Чому ви навчитеся

До кінця цього модуля ви зможете:
- Створювати поди за допомогою імперативних команд та YAML
- Розуміти життєвий цикл пода та його стани
- Налагоджувати поди за допомогою logs, exec та describe
- Створювати багатоконтейнерні поди (sidecar, init-контейнери)
- Розуміти основи мережевої взаємодії подів

---

## Частина 1: Основи Подів

### 1.1 Що таке Под?

Под — це:
- Найменша одиниця розгортання в Kubernetes
- Обгортка навколо одного або кількох контейнерів
- Контейнери, які мають спільну мережу та сховище
- Ефемерна сутність (може бути знищена та перестворена)

```
┌────────────────────────────────────────────────────────────────┐
│                             Под                                 │
│                                                                 │
│   ┌─────────────────┐    ┌─────────────────┐                   │
│   │   Контейнер 1   │    │   Контейнер 2   │                   │
│   │ (основний дод.) │    │   (sidecar)     │                   │
│   │                 │    │                 │                   │
│   │   Порт 8080     │    │   Порт 9090     │                   │
│   └─────────────────┘    └─────────────────┘                   │
│            │                      │                             │
│            └──────────┬───────────┘                             │
│                       │                                         │
│          Спільний мережевий простір імен                        │
│          • Однакова IP-адреса                                   │
│          • Зв'язок через localhost                              │
│          • Спільні порти (не можуть конфліктувати)              │
│                                                                 │
│          Спільні томи (опціонально)                             │
│          • Монтування того ж самого тому                        │
│          • Спільний доступ до даних між контейнерами            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Под проти Контейнера

| Аспект | Контейнер | Под |
|--------|-----------|-----|
| Одиниця | Один процес | Група контейнерів |
| Мережа | Власний мережевий простір імен | Спільний мережевий простір імен |
| IP-адреса | Немає (використовує адресу пода) | Одна на под |
| Сховище | Власна файлова система | Можуть мати спільні томи |
| Життєвий цикл | Керується подом | Керується Kubernetes |

### 1.3 Чому Поди, а не просто Контейнери?

Поди дозволяють:
1. **Спільне розміщення помічників**: Sidecar-контейнери для логування, проксіювання
2. **Спільні ресурси**: Контейнери, яким потрібно ділитися файлами або спілкуватися
3. **Атомарне планування**: Тісно пов'язані контейнери плануються разом
4. **Абстракція**: Kubernetes керує подами, а не чистими контейнерами

---

## Частина 2: Створення Подів

### 2.1 Імперативні команди (Швидко для іспиту)

```bash
# Create a simple pod
kubectl run nginx --image=nginx

# Create pod and expose port
kubectl run nginx --image=nginx --port=80

# Create pod with labels
kubectl run nginx --image=nginx --labels="app=web,env=prod"

# Create pod with environment variables
kubectl run nginx --image=nginx --env="ENV=production"

# Create pod with resource requests
kubectl run nginx --image=nginx --requests="cpu=100m,memory=128Mi"

# Create pod with resource limits
kubectl run nginx --image=nginx --limits="cpu=200m,memory=256Mi"

# Generate YAML without creating (essential for exam!)
kubectl run nginx --image=nginx --dry-run=client -o yaml > pod.yaml
```

### 2.2 Декларативний YAML

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
    env: production
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

```bash
# Apply the pod
kubectl apply -f pod.yaml
```

### 2.3 Основні операції з Подами

```bash
# List pods
kubectl get pods
kubectl get pods -o wide        # Show IP and node
kubectl get pods --show-labels  # Show labels

# Describe pod (detailed info)
kubectl describe pod nginx

# Get pod YAML
kubectl get pod nginx -o yaml

# Delete pod
kubectl delete pod nginx

# Delete pod immediately (skip graceful shutdown)
kubectl delete pod nginx --grace-period=0 --force

# Watch pods
kubectl get pods -w
```

> **Чи знали ви?**
>
> Патерн `--dry-run=client -o yaml` — ваш найкращий друг на іспиті. Він генерує валідний YAML, який ви можете модифікувати, позбавляючи вас від необхідності писати все з нуля. Опануйте цей патерн!

---

## Частина 3: Життєвий цикл Пода

### 3.1 Фази Пода

| Фаза | Опис |
|-------|-------------|
| **Pending** | Под прийнято, очікується планування або завантаження образів |
| **Running** | Под прив'язаний до вузла, принаймні один контейнер запущено |
| **Succeeded** | Всі контейнери успішно завершили роботу (exit 0) |
| **Failed** | Всі контейнери завершили роботу, принаймні один з помилкою |
| **Unknown** | Стан пода неможливо визначити (проблема зв'язку з вузлом) |

### 3.2 Стани Контейнера

| Стан | Опис |
|-------|-------------|
| **Waiting** | Ще не запущений (завантаження образу, застосування секретів) |
| **Running** | Виконується без проблем |
| **Terminated** | Завершив виконання (успішно або з помилкою) |

### 3.3 Візуалізація життєвого циклу

```
┌────────────────────────────────────────────────────────────────┐
│                   Життєвий цикл Пода                            │
│                                                                 │
│   Под створено                                                  │
│       │                                                         │
│       ▼                                                         │
│   ┌─────────┐     Немає доступного вузла                       │
│   │ Pending │◄────────────────────────────────┐                │
│   └────┬────┘                                 │                │
│        │ Заплановано на вузол                 │                │
│        ▼                                      │                │
│   ┌─────────┐     Збій контейнера             │                │
│   │ Running │────────────────────────────────►│                │
│   └────┬────┘                                 │                │
│        │                                      │                │
│        ├─────────────────────┐                │                │
│        │                     │                │                │
│        ▼                     ▼                │                │
│   ┌───────────┐        ┌────────┐            │                │
│   │ Succeeded │        │ Failed │            │                │
│   │ (exit 0)  │        │(exit≠0)│            │                │
│   └───────────┘        └────────┘            │                │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.4 Перевірка статусу Пода

```bash
# Quick status
kubectl get pod nginx
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   0          5m

# Detailed status
kubectl describe pod nginx | grep -A10 "Status:"

# Container states
kubectl get pod nginx -o jsonpath='{.status.containerStatuses[0].state}'

# Check why a pod is pending
kubectl describe pod nginx | grep -A5 "Events:"
```

---

## Частина 4: Налагодження Подів

### 4.1 Робочий процес налагодження

```
Проблема з Подом
    │
    ├── kubectl get pods (перевірка STATUS)
    │       │
    │       ├── Pending → kubectl describe (перевірка Events)
    │       │               └── ImagePullBackOff, Недостатньо ресурсів тощо.
    │       │
    │       ├── CrashLoopBackOff → kubectl logs (перевірка помилок додатку)
    │       │                        └── Збій додатку, відсутній конфіг тощо.
    │       │
    │       └── Працює, але не функціонує → kubectl exec (перевірка всередині)
    │                                       └── Проблеми з мережею, неправильний конфіг тощо.
    │
    └── kubectl describe pod (завжди корисно)
```

### 4.2 Перегляд логів

```bash
# Current logs
kubectl logs nginx

# Follow logs (like tail -f)
kubectl logs nginx -f

# Last 100 lines
kubectl logs nginx --tail=100

# Logs from last hour
kubectl logs nginx --since=1h

# Logs from specific container (multi-container pod)
kubectl logs nginx -c sidecar

# Previous container logs (after crash)
kubectl logs nginx --previous
```

### 4.3 Виконання команд у Подах

```bash
# Run a command
kubectl exec nginx -- ls /

# Interactive shell
kubectl exec -it nginx -- /bin/bash
kubectl exec -it nginx -- /bin/sh   # If bash not available

# Specific container in multi-container pod
kubectl exec -it nginx -c sidecar -- /bin/sh

# Run commands without shell
kubectl exec nginx -- cat /etc/nginx/nginx.conf
kubectl exec nginx -- env
kubectl exec nginx -- ps aux
```

### 4.4 Типові проблеми з Подами

| Симптом | Причина | Рішення |
|---------|-------|----------|
| `ImagePullBackOff` | Неправильна назва образу або немає доступу | Виправте назву образу, перевірте авторизацію реєстру |
| `CrashLoopBackOff` | Контейнер постійно падає | Перевірте логи на наявність помилок додатку |
| `Pending` (без подій) | Жоден вузол не має достатньо ресурсів | Звільніть ресурси або додайте вузли |
| `Pending` (планування) | Taints, правила affinity | Перевірте taints вузла та tolerations пода |
| `Running`, але не готовий | Збій readiness probe | Перевірте конфігурацію probe та додаток |
| `OOMKilled` | Нестача пам'яті | Збільште ліміти пам'яті |

### 4.5 Шпаргалка з команд налагодження

```bash
# The trinity of debugging
kubectl get pod nginx              # What's the status?
kubectl describe pod nginx         # What's happening? (events)
kubectl logs nginx                 # What does the app say?

# Deeper investigation
kubectl exec -it nginx -- /bin/sh  # Get inside
kubectl get events --sort-by='.lastTimestamp'  # Recent events
kubectl top pod nginx              # Resource usage (if metrics-server)
```

> **Бойова історія: Мовчазний збій**
>
> Молодший інженер витратив 3 години на налагодження того, чому його под не працював. `kubectl get pods` показував `Running`. Нарешті він виконав `kubectl describe pod` і побачив, що readiness probe завершувалася помилкою. Под працював, але не отримував трафік, оскільки не був готовий. Завжди перевіряйте стовпець `READY` та вивід describe!

---

## Частина 5: Багатоконтейнерні Поди

### 5.1 Чому кілька контейнерів?

Багатоконтейнерні поди призначені для контейнерів, які:
- Потребують спільних ресурсів (мережі, сховища)
- Мають тісно пов'язані життєві цикли
- Утворюють єдину цілісну одиницю обслуговування

### 5.2 Патерни з кількома контейнерами

```
┌────────────────────────────────────────────────────────────────┐
│             Патерни з кількома контейнерами                     │
│                                                                 │
│   Sidecar                    Ambassador             Adapter     │
│   ┌──────────────────┐       ┌──────────────────┐  ┌─────────┐ │
│   │ ┌────┐  ┌────┐   │       │ ┌────┐  ┌────┐   │  │┌────┐   │ │
│   │ │Осн.│  │Відп│   │       │ │Осн.│  │Про-│   │  ││Осн.│   │ │
│   │ │Дод.│──│Лог.│   │       │ │Дод.│──│ксі │──┼──││Дод.│   │ │
│   │ └────┘  └────┘   │       │ └────┘  └────┘   │  │└──┬─┘   │ │
│   │ Осн. + Помічник  │       │ Проксі вихідного │  │   │     │ │
│   └──────────────────┘       └──────────────────┘  │┌──▼──┐  │ │
│                                                    ││Адапт│  │ │
│   Приклади:                  Приклади:             ││Логів│  │ │
│   - Збирачі логів            - Проксі service mesh │└─────┘  │ │
│   - Перезавант. конфігів     - Проксі бази даних   │Трансфор.│ │
│   - Синхронізація Git        - Проксі авторизації  └─────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 Патерн Sidecar

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-sidecar
spec:
  containers:
  # Main application container
  - name: web
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx

  # Sidecar container - ships logs
  - name: log-shipper
    image: busybox
    command: ["sh", "-c", "tail -F /var/log/nginx/access.log"]
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx

  volumes:
  - name: logs
    emptyDir: {}
```

### 5.4 Init-контейнери

Init-контейнери запускаються **до** контейнерів додатку і повинні успішно завершитися:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  # Init containers run first, in order
  initContainers:
  - name: wait-for-db
    image: busybox
    command: ['sh', '-c', 'until nc -z db-service 5432; do echo waiting for db; sleep 2; done']

  - name: init-config
    image: busybox
    command: ['sh', '-c', 'echo "config initialized" > /config/ready']
    volumeMounts:
    - name: config
      mountPath: /config

  # App containers start after all init containers succeed
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: config
      mountPath: /config

  volumes:
  - name: config
    emptyDir: {}
```

### 5.5 Варіанти використання Init-контейнерів

| Варіант використання | Приклад |
|----------|---------|
| Очікування залежності | Очікування готовності бази даних |
| Налаштування конфігурації | Клонування git-репозиторію, генерація конфігу |
| Міграції бази даних | Запуск міграцій перед стартом додатку |
| Реєстрація в сервісі | Реєстрація екземпляра в зовнішній системі |
| Завантаження ресурсів | Отримання статичних файлів з S3 |

> **Чи знали ви?**
>
> Init-контейнери мають таку ж специфікацію, як і звичайні контейнери, але з іншою поведінкою перезапуску. Якщо init-контейнер зазнає невдачі, под перезапускається (якщо restartPolicy не Never). Init-контейнери не підтримують readiness probes, оскільки вони повинні завершитися, а не залишатися працюючими.

---

## Частина 6: Основи мережевої взаємодії Подів

### 6.1 Мережева модель Пода

```
┌────────────────────────────────────────────────────────────────┐
│                Мережева взаємодія Подів                         │
│                                                                 │
│   Кожен под отримує унікальну IP-адресу                        │
│   Контейнери в поді мають спільну IP-адресу                    │
│   Поди можуть спілкуватися з іншими подами (без NAT)           │
│                                                                 │
│   ┌───────────────────────┐    ┌───────────────────────┐       │
│   │ Под A (10.244.1.5)    │    │ Под B (10.244.2.8)    │       │
│   │ ┌─────┐    ┌─────┐    │    │ ┌─────┐              │       │
│   │ │ C1  │    │ C2  │    │    │ │ C1  │              │       │
│   │ │:80  │    │:9090│    │    │ │:8080│              │       │
│   │ └──┬──┘    └──┬──┘    │    │ └──┬──┘              │       │
│   │    │          │       │    │    │                 │       │
│   │    └────┬─────┘       │    │    │                 │       │
│   │         │ localhost   │    │    │                 │       │
│   └─────────┼─────────────┘    └────┼─────────────────┘       │
│             │                       │                          │
│             └───────────────────────┘                          │
│             Можуть звертатися один до одного напряму           │
│                10.244.1.5:80 ←→ 10.244.2.8:8080               │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Зв'язок контейнерів у Поді

```bash
# Containers in same pod communicate via localhost
# Container 1 (nginx on port 80)
# Container 2 can reach it at localhost:80

# Example: curl from sidecar to main app
kubectl exec -it pod-name -c sidecar -- curl localhost:80
```

### 6.3 Пошук IP-адрес Подів

```bash
# Get pod IP
kubectl get pod nginx -o wide
# NAME    READY   STATUS    IP           NODE
# nginx   1/1     Running   10.244.1.5   worker-1

# Get IP with jsonpath
kubectl get pod nginx -o jsonpath='{.status.podIP}'

# Get all pod IPs
kubectl get pods -o custom-columns='NAME:.metadata.name,IP:.status.podIP'
```

---

## Частина 7: Політики перезапуску

### 7.1 Варіанти політики перезапуску

| Політика | Поведінка | Варіант використання |
|--------|----------|----------|
| `Always` (за замовчуванням) | Перезапуск при будь-якому завершенні | Сервіси, що довго працюють |
| `OnFailure` | Перезапуск лише при ненульовому виході | Jobs, які повинні повторюватися при помилці |
| `Never` | Ніколи не перезапускати | Одноразові скрипти, налагодження |

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restart-demo
spec:
  restartPolicy: OnFailure   # Only restart if container fails
  containers:
  - name: worker
    image: busybox
    command: ["sh", "-c", "exit 1"]  # Will be restarted
```

### 7.2 Поведінка перезапуску

```bash
# Check restart count
kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   3          10m

# Describe shows restart details
kubectl describe pod nginx | grep -A5 "Last State"
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|----------|
| Використання тегу `latest` | Непередбачувані розгортання | Завжди вказуйте теги версій |
| Немає лімітів ресурсів | Под може спожити всі ресурси вузла | Завжди встановлюйте requests та limits |
| Ігнорування логів | Пропущена першопричина | Завжди перевіряйте `kubectl logs` |
| Невикористання `--dry-run` | Повільне створення YAML | Генеруйте шаблони за допомогою `--dry-run=client -o yaml` |
| Забутий прапорець `-c` | Неправильний контейнер у багатоконтейнерному поді | Вказуйте контейнер за допомогою `-c name` |

---

## Тест

1. **Яка команда генерує YAML пода без його створення?**
   <details>
   <summary>Відповідь</summary>
   `kubectl run nginx --image=nginx --dry-run=client -o yaml`

   Прапорець `--dry-run=client` запобігає створенню, а `-o yaml` виводить маніфест.
   </details>

2. **Под знаходиться в стані CrashLoopBackOff. Який перший крок налагодження?**
   <details>
   <summary>Відповідь</summary>
   `kubectl logs <pod-name> --previous`

   Це покаже логи з попереднього (завершеного з помилкою) екземпляра контейнера. Контейнер падає, тому `--previous` фіксує те, що сталося до збою.
   </details>

3. **Як контейнери в одному поді спілкуються між собою?**
   <details>
   <summary>Відповідь</summary>
   Через `localhost`. Контейнери в одному поді мають спільний мережевий простір імен, тому вони можуть звертатися один до одного через localhost, використовуючи свої відповідні порти.
   </details>

4. **Яка різниця між init-контейнерами та sidecar-контейнерами?**
   <details>
   <summary>Відповідь</summary>
   **Init-контейнери** запускаються перед контейнерами додатку, повинні успішно завершитися і виконуються послідовно. **Sidecar-контейнери** працюють поруч з основним контейнером протягом усього життєвого циклу пода.
   </details>

---

## Практичне завдання

**Завдання**: Створити та налагодити багатоконтейнерний под.

**Кроки**:

1. **Створіть под з init-контейнером та sidecar**:
```bash
cat > multi-container-pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  initContainers:
  - name: init-setup
    image: busybox
    command: ['sh', '-c', 'echo "Init complete" > /shared/init-status.txt']
    volumeMounts:
    - name: shared
      mountPath: /shared

  containers:
  - name: web
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared
      mountPath: /usr/share/nginx/html
    - name: logs
      mountPath: /var/log/nginx

  - name: log-reader
    image: busybox
    command: ['sh', '-c', 'tail -F /logs/access.log 2>/dev/null || sleep infinity']
    volumeMounts:
    - name: logs
      mountPath: /logs

  volumes:
  - name: shared
    emptyDir: {}
  - name: logs
    emptyDir: {}
EOF

kubectl apply -f multi-container-pod.yaml
```

2. **Спостерігайте за запуском пода**:
```bash
kubectl get pod webapp -w
# Watch init container complete, then main containers start
```

3. **Перевірте завершення init-контейнера**:
```bash
kubectl describe pod webapp | grep -A10 "Init Containers"
```

4. **Перевірте спільний том**:
```bash
# Init container created this file
kubectl exec webapp -c web -- cat /usr/share/nginx/html/init-status.txt
```

5. **Отримайте доступ до sidecar-контейнера**:
```bash
kubectl exec -it webapp -c log-reader -- /bin/sh
# Inside: ls /logs
exit
```

6. **Згенеруйте трафік та перегляньте логи**:
```bash
# Get pod IP
POD_IP=$(kubectl get pod webapp -o jsonpath='{.status.podIP}')

# Generate traffic from another pod
kubectl run curl --image=curlimages/curl --rm -it --restart=Never -- curl $POD_IP

# Check sidecar saw the log
kubectl logs webapp -c log-reader
```

7. **Налагоджуйте за допомогою логів**:
```bash
# Logs from specific container
kubectl logs webapp -c web
kubectl logs webapp -c log-reader

# Follow logs
kubectl logs webapp -c web -f
```

8. **Очищення**:
```bash
kubectl delete pod webapp
rm multi-container-pod.yaml
```

**Критерії успіху**:
- [ ] Вмію створювати поди імперативними командами
- [ ] Вмію генерувати YAML за допомогою `--dry-run=client -o yaml`
- [ ] Розумію фази життєвого циклу пода
- [ ] Вмію налагоджувати за допомогою logs, exec, describe
- [ ] Вмію створювати багатоконтейнерні поди з init та sidecar

---

## Практичні вправи

### Вправа 1: Тест на швидкість створення Подів (Ціль: 2 хвилини)

Створіть 5 різних подів якомога швидше:

```bash
# 1. Basic nginx pod
kubectl run nginx --image=nginx

# 2. Pod with labels
kubectl run labeled --image=nginx --labels="app=web,tier=frontend"

# 3. Pod with port
kubectl run webserver --image=nginx --port=80

# 4. Pod with environment variables
kubectl run envpod --image=nginx --env="ENV=production" --env="DEBUG=false"

# 5. Pod with resource requests
kubectl run limited --image=nginx --requests="cpu=100m,memory=128Mi" --limits="cpu=200m,memory=256Mi"

# Verify all pods
kubectl get pods

# Cleanup
kubectl delete pod nginx labeled webserver envpod limited
```

### Вправа 2: Генерація YAML (Ціль: 3 хвилини)

Згенеруйте та змініть YAML:

```bash
# Generate base YAML
kubectl run webapp --image=nginx:1.25 --port=80 --dry-run=client -o yaml > webapp.yaml

# View and verify
cat webapp.yaml

# Apply it
kubectl apply -f webapp.yaml

# Modify: add a label
kubectl label pod webapp tier=frontend

# Verify label
kubectl get pod webapp --show-labels

# Cleanup
kubectl delete -f webapp.yaml
rm webapp.yaml
```

### Вправа 3: Робочий процес налагодження Пода (Ціль: 5 хвилин)

Налагодьте под, що дає збій:

```bash
# Create a pod that will fail
kubectl run failing --image=nginx --command -- /bin/sh -c "exit 1"

# Check status
kubectl get pod failing
# STATUS: CrashLoopBackOff

# Debug step 1: describe
kubectl describe pod failing | tail -20

# Debug step 2: logs
kubectl logs failing --previous

# Debug step 3: check events
kubectl get events --field-selector involvedObject.name=failing

# Cleanup
kubectl delete pod failing
```

### Вправа 4: Багатоконтейнерний Под (Ціль: 5 хвилин)

```bash
# Create pod with sidecar
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-demo
spec:
  containers:
  - name: main
    image: nginx
    volumeMounts:
    - name: shared
      mountPath: /usr/share/nginx/html
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'while true; do date > /html/index.html; sleep 5; done']
    volumeMounts:
    - name: shared
      mountPath: /html
  volumes:
  - name: shared
    emptyDir: {}
EOF

# Wait for ready
kubectl wait --for=condition=ready pod/sidecar-demo --timeout=60s

# Test - sidecar writes timestamp that nginx serves
kubectl exec sidecar-demo -c main -- cat /usr/share/nginx/html/index.html

# Wait 5 seconds and check again - timestamp should change
sleep 5
kubectl exec sidecar-demo -c main -- cat /usr/share/nginx/html/index.html

# Cleanup
kubectl delete pod sidecar-demo
```

### Вправа 5: Init-контейнер (Ціль: 5 хвилин)

```bash
# Create pod with init container
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  initContainers:
  - name: init-download
    image: busybox
    command: ['sh', '-c', 'echo "Hello from init" > /work/message.txt']
    volumeMounts:
    - name: workdir
      mountPath: /work
  containers:
  - name: main
    image: busybox
    command: ['sh', '-c', 'cat /work/message.txt && sleep 3600']
    volumeMounts:
    - name: workdir
      mountPath: /work
  volumes:
  - name: workdir
    emptyDir: {}
EOF

# Watch init container complete
kubectl get pod init-demo -w

# Verify init worked
kubectl logs init-demo

# Check init container status
kubectl describe pod init-demo | grep -A5 "Init Containers"

# Cleanup
kubectl delete pod init-demo
```

### Вправа 6: Мережева взаємодія Подів (Ціль: 3 хвилини)

```bash
# Create two pods
kubectl run pod-a --image=nginx --port=80
kubectl run pod-b --image=busybox --command -- sleep 3600

# Wait for ready
kubectl wait --for=condition=ready pod/pod-a pod/pod-b --timeout=60s

# Get pod-a IP
POD_A_IP=$(kubectl get pod pod-a -o jsonpath='{.status.podIP}')
echo "Pod A IP: $POD_A_IP"

# From pod-b, reach pod-a
kubectl exec pod-b -- wget -qO- $POD_A_IP

# Cleanup
kubectl delete pod pod-a pod-b
```

### Вправа 7: Усунення несправностей - ImagePullBackOff (Ціль: 3 хвилини)

```bash
# Create pod with wrong image
kubectl run broken --image=nginx:nonexistent-tag

# Check status
kubectl get pod broken
# STATUS: ImagePullBackOff or ErrImagePull

# Diagnose
kubectl describe pod broken | grep -A10 "Events"

# Fix: update the image
kubectl set image pod/broken broken=nginx:1.25

# Verify fixed
kubectl get pod broken
kubectl wait --for=condition=ready pod/broken --timeout=60s

# Cleanup
kubectl delete pod broken
```

### Вправа 8: Виклик - Повний робочий процес з Подом

Не підглядаючи в рішення:

1. Створіть под з назвою `challenge` з nginx:1.25
2. Додайте мітки `app=web` та `env=test`
3. Увійдіть у под через exec і створіть файл `/tmp/test.txt` з текстом "Hello"
4. Отримайте IP-адресу пода
5. Перегляньте логи пода
6. Видаліть под

```bash
# YOUR TASK: Complete in under 3 minutes
```

<details>
<summary>Рішення</summary>

```bash
# 1. Create pod with labels
kubectl run challenge --image=nginx:1.25 --labels="app=web,env=test"

# 2. Wait for ready
kubectl wait --for=condition=ready pod/challenge --timeout=60s

# 3. Create file inside pod
kubectl exec challenge -- sh -c 'echo "Hello" > /tmp/test.txt'

# 4. Verify file
kubectl exec challenge -- cat /tmp/test.txt

# 5. Get IP
kubectl get pod challenge -o jsonpath='{.status.podIP}'

# 6. View logs
kubectl logs challenge

# 7. Delete
kubectl delete pod challenge
```

</details>

---

## Наступний модуль

[Модуль 2.2: Деплойменти та ReplicaSets](module-2.2-deployments/) — Поступові оновлення, відкати та масштабування.

