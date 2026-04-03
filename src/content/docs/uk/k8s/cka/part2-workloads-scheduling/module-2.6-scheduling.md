---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2.6: \u041f\u043b\u0430\u043d\u0443\u0432\u0430\u043d\u043d\u044f"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.6-scheduling
sidebar: 
  order: 7
lab: 
  id: cka-2.6-scheduling
  url: https://killercoda.com/kubedojo/scenario/cka-2.6-scheduling
  duration: "45 min"
  difficulty: advanced
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Критична тема на іспиті
>
> **Час на проходження**: 45-55 хвилин
>
> **Передумови**: Модуль 2.1 (Поди), Модуль 2.5 (Управління ресурсами)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Налаштувати** nodeSelector, node affinity та правила pod affinity/anti-affinity
- **Використовувати** taints та tolerations для контролю, які поди можуть запускатися на конкретних вузлах
- **Імплементувати** pod topology spread constraints для високої доступності між зонами
- **Дебажити** поди у стані Pending, читаючи події планувальника та зіставляючи їх з обмеженнями вузлів

---

## Чому цей модуль важливий

За замовчуванням планувальник розміщує Поди на будь-якій Ноді з доступними ресурсами. Але в продакшені вам потрібен контроль:
- Запускати Поди бази даних на Нодах із SSD
- Тримати певні Поди окремо для високої доступності
- Розподіляти навантаження між зонами доступності
- Резервувати Ноди для конкретних навантажень

Іспит CKA часто перевіряє обмеження планування. Вам потрібно вміти використовувати nodeSelector, правила спорідненості (affinity) та taints/tolerations.

> **Аналогія з організацією заходу**
>
> Уявіть планування як розсадження гостей на весіллі. **nodeSelector** — це «VIP-гості за столом 1». **Node affinity** — це «бажано ближче до сцени, але будь-де підійде». **Taints** — це зарезервовані столи з табличкою «Тільки для персоналу». **Tolerations** — це бейджі персоналу, які дозволяють сидіти за зарезервованими столами. **Anti-affinity** — це «не садіть колишніх за один стіл».

---

## Що ви дізнаєтесь

До кінця цього модуля ви зможете:
- Використовувати nodeSelector для простого вибору Нод
- Налаштовувати спорідненість (affinity) та анти-спорідненість (anti-affinity) Нод
- Застосовувати taints до Нод і tolerations до Подів
- Розподіляти Поди між доменами топології
- Діагностувати проблеми з плануванням

---

## Частина 1: nodeSelector

### 1.1 Найпростіший підхід

nodeSelector — це найпростіший спосіб обмежити Поди конкретними Нодами:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ssd-pod
spec:
  nodeSelector:
    disk: ssd              # Only schedule on nodes with this label
  containers:
  - name: nginx
    image: nginx
```

### 1.2 Робота з мітками Нод

```bash
# List node labels
kubectl get nodes --show-labels

# Label a node
kubectl label node worker-1 disk=ssd

# Remove a label
kubectl label node worker-1 disk-

# Overwrite a label
kubectl label node worker-1 disk=hdd --overwrite
```

### 1.3 Поширені вбудовані мітки

| Мітка | Опис |
|-------|------|
| `kubernetes.io/hostname` | Ім'я хосту Ноди |
| `kubernetes.io/os` | Операційна система (linux, windows) |
| `kubernetes.io/arch` | Архітектура (amd64, arm64) |
| `topology.kubernetes.io/zone` | Зона доступності хмари |
| `topology.kubernetes.io/region` | Регіон хмари |
| `node.kubernetes.io/instance-type` | Тип інстансу (хмара) |

```yaml
# Example: Schedule only on Linux nodes
spec:
  nodeSelector:
    kubernetes.io/os: linux
```

> **Чи знали ви?**
>
> Ви можете комбінувати кілька міток nodeSelector. Под буде розміщено лише на Нодах, які відповідають УСІМ міткам (логіка І).

---

## Частина 2: Спорідненість Нод (Node Affinity)

### 2.1 Навіщо спорідненість Нод?

Спорідненість Нод є виразнішою за nodeSelector:
- **М'які переваги** («бажано, але не обов'язково»)
- **Кілька варіантів відповідності** (логіка АБО)
- **Оператори** (In, NotIn, Exists, DoesNotExist, Gt, Lt)

### 2.2 Типи спорідненості

| Тип | Поведінка |
|-----|-----------|
| `requiredDuringSchedulingIgnoredDuringExecution` | Жорстка вимога (як nodeSelector) |
| `preferredDuringSchedulingIgnoredDuringExecution` | М'яка перевага |

> **Ключовий момент**: «IgnoredDuringExecution» означає, що якщо мітки зміняться після планування, Под залишиться на місці. Перепланування не відбувається.

### 2.3 Обов'язкова спорідненість (жорстка)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-required
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disk
            operator: In
            values:
            - ssd
            - nvme
  containers:
  - name: nginx
    image: nginx
```

### 2.4 Бажана спорідненість (м'яка)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-preferred
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80               # Higher weight = stronger preference
        preference:
          matchExpressions:
          - key: disk
            operator: In
            values:
            - ssd
      - weight: 20
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - us-west-1a
  containers:
  - name: nginx
    image: nginx
```

### 2.5 Оператори

| Оператор | Значення |
|----------|----------|
| `In` | Значення мітки є в наборі |
| `NotIn` | Значення мітки не є в наборі |
| `Exists` | Мітка існує (будь-яке значення) |
| `DoesNotExist` | Мітка не існує |
| `Gt` | Більше ніж (порівняння цілих чисел) |
| `Lt` | Менше ніж (порівняння цілих чисел) |

```yaml
# Example: Node must have "gpu" label with any value
matchExpressions:
  - key: gpu
    operator: Exists

# Example: Node must NOT be in zone us-east-1c
matchExpressions:
  - key: topology.kubernetes.io/zone
    operator: NotIn
    values:
    - us-east-1c
```

---

## Частина 3: Спорідненість та анти-спорідненість Подів

### 3.1 Навіщо спорідненість Подів?

Керуйте розміщенням Подів відносно інших Подів:
- **Спорідненість Подів**: «Розмістити поряд із Подами з міткою X» (сумісне розташування)
- **Анти-спорідненість Подів**: «Не розміщувати поряд із Подами з міткою X» (розподілення)

### 3.2 Приклад спорідненості Подів

«Розмістити цей Под на тій самій Ноді, що й Поди з app=cache»:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-pod
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: cache
        topologyKey: kubernetes.io/hostname    # Same node
  containers:
  - name: web
    image: nginx
```

### 3.3 Приклад анти-спорідненості Подів

«Не розміщувати на Нодах, де вже є Поди app=web»:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-pod
  labels:
    app: web
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: web
        topologyKey: kubernetes.io/hostname
  containers:
  - name: web
    image: nginx
```

### 3.4 Ключ топології (Topology Key)

`topologyKey` визначає «зону» для спорідненості:

| topologyKey | Значення |
|-------------|----------|
| `kubernetes.io/hostname` | Та сама Нода |
| `topology.kubernetes.io/zone` | Та сама зона доступності |
| `topology.kubernetes.io/region` | Той самий регіон |

```
┌────────────────────────────────────────────────────────────────┐
│     Анти-спорідненість із різними topologyKey                  │
│                                                                 │
│   topologyKey: kubernetes.io/hostname                          │
│   → Поди розподілені між Нодами (один на Ноду)                │
│                                                                 │
│   Нода1: [web-1]    Нода2: [web-2]    Нода3: [web-3]          │
│                                                                 │
│   topologyKey: topology.kubernetes.io/zone                     │
│   → Поди розподілені між зонами (один на зону)                │
│                                                                 │
│   Зона-A            Зона-B            Зона-C                  │
│   [web-1]           [web-2]           [web-3]                  │
│   Нода1,Нода2       Нода3,Нода4       Нода5,Нода6              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Порада до іспиту**
>
> Для розподілення реплік між Нодами використовуйте анти-спорідненість Подів з `topologyKey: kubernetes.io/hostname`. Для розподілення між зонами для високої доступності використовуйте `topology.kubernetes.io/zone`.

---

## Частина 4: Taints і Tolerations

### 4.1 Як працюють Taints

Taints застосовуються до **Нод** і відштовхують Поди, якщо Под не має відповідної toleration.

```
┌────────────────────────────────────────────────────────────────┐
│                   Taints і Tolerations                          │
│                                                                 │
│   Нода з taint: gpu=true:NoSchedule                            │
│   ┌─────────────────────────────────────────────┐              │
│   │                                             │              │
│   │  Звичайний Под:       ❌ Не може бути       │              │
│   │                       розміщений             │              │
│   │                                             │              │
│   │  Под із відповідною   ✅ Може бути          │              │
│   │  toleration:          розміщений             │              │
│   │                                             │              │
│   └─────────────────────────────────────────────┘              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Ефекти Taint

| Ефект | Поведінка |
|-------|-----------|
| `NoSchedule` | Поди не будуть розміщені (існуючі Поди залишаються) |
| `PreferNoSchedule` | М'яка версія — уникати, але дозволити за необхідності |
| `NoExecute` | Витіснити існуючі Поди, запобігти новому розміщенню |

### 4.3 Керування Taints

```bash
# Add taint to node
kubectl taint nodes worker-1 gpu=true:NoSchedule

# View taints
kubectl describe node worker-1 | grep Taints

# Remove taint (note the minus sign)
kubectl taint nodes worker-1 gpu=true:NoSchedule-

# Multiple taints
kubectl taint nodes worker-1 dedicated=ml:NoSchedule
kubectl taint nodes worker-1 gpu=nvidia:NoSchedule
```

### 4.4 Додавання Tolerations до Подів

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  tolerations:
  - key: "gpu"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  containers:
  - name: cuda-app
    image: nvidia/cuda
```

### 4.5 Оператори Toleration

| Оператор | Значення |
|----------|----------|
| `Equal` | Ключ і значення мають збігатися |
| `Exists` | Ключ існує (будь-яке значення підходить) |

```yaml
# Match specific value
tolerations:
- key: "gpu"
  operator: "Equal"
  value: "nvidia"
  effect: "NoSchedule"

# Match any value for key
tolerations:
- key: "gpu"
  operator: "Exists"
  effect: "NoSchedule"

# Tolerate all taints (wildcard)
tolerations:
- operator: "Exists"
```

### 4.6 Поширені сценарії використання Taint

| Сценарій використання | Приклад Taint |
|----------------------|---------------|
| GPU-Ноди | `gpu=true:NoSchedule` |
| Виділені Ноди | `dedicated=team-a:NoSchedule` |
| Ноди площини управління | `node-role.kubernetes.io/control-plane:NoSchedule` |
| Виведення Нод з обслуговування | `node.kubernetes.io/unschedulable:NoSchedule` |

> **Історія з практики: зниклі Поди**
>
> Один SRE додав taint `NoExecute` для обслуговування замість `NoSchedule`. Існуючі Поди були негайно витіснені, що спричинило збій продакшену. Знайте свої ефекти taint! Використовуйте `NoSchedule`, щоб запобігти новим Подам. Використовуйте `NoExecute` лише тоді, коли хочете витіснити запущені Поди.

---

## Частина 5: Обмеження розподілу топології Подів

### 5.1 Навіщо розподіл топології?

Рівномірно розподіляйте Поди між доменами відмов:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: spread-pod
  labels:
    app: web
spec:
  topologySpreadConstraints:
  - maxSkew: 1                              # Max difference between zones
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule        # Hard requirement
    labelSelector:
      matchLabels:
        app: web
  containers:
  - name: nginx
    image: nginx
```

### 5.2 Пояснення параметрів

| Параметр | Опис |
|----------|------|
| `maxSkew` | Максимально допустима різниця в кількості Подів між доменами |
| `topologyKey` | Ключ мітки, що визначає домени (зона, Нода тощо) |
| `whenUnsatisfiable` | `DoNotSchedule` (жорстко) або `ScheduleAnyway` (м'яко) |
| `labelSelector` | Які Поди враховувати при розподілі |

### 5.3 Візуалізація

```
┌────────────────────────────────────────────────────────────────┐
│              Розподіл топології (maxSkew: 1)                    │
│                                                                 │
│   Зона A          Зона B          Зона C                       │
│   [под][під]      [під]           [під]                        │
│   Кількість: 2    Кількість: 1    Кількість: 1                 │
│                                                                 │
│   Макс. різниця = 2-1 = 1 ≤ maxSkew ✓                         │
│                                                                 │
│   Прибуває новий Під — куди його можна розмістити?             │
│   Зона A: 3 Поди → різниця 3-1=2 > maxSkew ❌                 │
│   Зона B: 2 Поди → різниця 2-1=1 ≤ maxSkew ✓                 │
│   Зона C: 2 Поди → різниця 2-1=1 ≤ maxSkew ✓                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Частина 6: Послідовність прийняття рішень при плануванні

```
┌────────────────────────────────────────────────────────────────┐
│          Послідовність прийняття рішень при плануванні          │
│                                                                 │
│   Под створено                                                  │
│       │                                                         │
│       ▼                                                         │
│   Фільтрація Нод                                               │
│   ├── nodeSelector збігається?                                 │
│   ├── Обов'язкова спорідненість Нод збігається?               │
│   ├── Taints допущені?                                         │
│   ├── Ресурси доступні?                                        │
│   ├── Анти-спорідненість Подів задоволена?                    │
│   └── Обмеження розподілу топології виконані?                  │
│       │                                                         │
│       ▼                                                         │
│   Оцінка залишених Нод                                         │
│   ├── Бажана спорідненість Нод                                │
│   ├── Бажана спорідненість Подів                              │
│   └── Оптимізація ресурсів                                     │
│       │                                                         │
│       ▼                                                         │
│   Вибір Ноди з найвищим балом                                  │
│       │                                                         │
│       ▼                                                         │
│   Прив'язування Поду до Ноди                                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Частина 7: Діагностика планування

### 7.1 Поширені проблеми

| Симптом | Ймовірна причина | Команда для діагностики |
|---------|-----------------|------------------------|
| Pending (без подій) | Жодна Нода не відповідає обмеженням | `kubectl describe pod` |
| Pending (Insufficient) | Брак ресурсів | Перевірити ресурси Ноди |
| Pending (Taints) | Немає toleration для taint | Перевірити taints Ноди, tolerations Поду |
| Pending (Affinity) | Жодна Нода не відповідає правилам спорідненості | Спростити/прибрати спорідненість |

### 7.2 Команди для діагностики

```bash
# Check pod events
kubectl describe pod <pod-name> | grep -A10 Events

# Check node labels
kubectl get nodes --show-labels

# Check node taints
kubectl describe node <node> | grep Taints

# Check node resources
kubectl describe node <node> | grep -A10 "Allocated resources"

# Simulate scheduling
kubectl get pods -o wide  # See where pods landed
```

---

## Чи знали ви?

- **Ноди площини управління** за замовчуванням мають taint `node-role.kubernetes.io/control-plane:NoSchedule`. Ось чому звичайні Поди там не запускаються.

- **Спорідненості можна комбінувати**. Ви можете мати nodeAffinity, podAffinity і podAntiAffinity одночасно на одному Поді.

- **Кілька topologySpreadConstraints** об'єднуються через І (AND). Усі обмеження мають бути задоволені.

- **DaemonSets ігнорують taints** за замовчуванням для деяких системних taints. Саме так вони працюють на кожній Ноді.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|---------|
| Друкарська помилка в nodeSelector | Под залишається в стані Pending | Перевірте, чи мітка існує на цільовій Ноді |
| Відсутня toleration | Под не може бути розміщений на Ноді з taint | Додайте відповідну toleration |
| Неправильний topologyKey | Спорідненість працює не так, як очікувалося | Використовуйте правильний ключ мітки |
| NoExecute замість NoSchedule | Поди несподівано витіснені | Використовуйте NoSchedule лише для нових Подів |
| Занадто строга анти-спорідненість | Недостатньо Нод для всіх реплік | Використовуйте preferred або зменшіть кількість реплік |

---

## Тест

1. **Яка різниця між nodeSelector і спорідненістю Нод (node affinity)?**
   <details>
   <summary>Відповідь</summary>
   **nodeSelector** — це просте зіставлення ключ-значення (логіка І, мають збігатися всі). **Спорідненість Нод** є виразнішою: з операторами (In, NotIn, Exists), м'якими перевагами та кількома варіантами (логіка АБО в nodeSelectorTerms).
   </details>

2. **Нода має taint `gpu=nvidia:NoSchedule`. Що повинен мати Под, щоб бути розміщеним там?**
   <details>
   <summary>Відповідь</summary>
   Toleration, що відповідає taint:
   ```yaml
   tolerations:
   - key: "gpu"
     operator: "Equal"
     value: "nvidia"
     effect: "NoSchedule"
   ```
   Або використайте `operator: Exists`, щоб відповідати будь-якому значенню.
   </details>

3. **Що означає topologyKey: kubernetes.io/hostname в анти-спорідненості Подів?**
   <details>
   <summary>Відповідь</summary>
   Це означає «розподілити Поди між різними Нодами». Кожне ім'я хосту Ноди є окремим доменом топології. Правило анти-спорідненості запобігає запуску Подів із відповідними мітками на одній Ноді.
   </details>

4. **Під у стані Pending з подією «0/3 nodes are available: 1 node(s) had taint». Що не так?**
   <details>
   <summary>Відповідь</summary>
   Под не має tolerations для taint принаймні однієї Ноди. Або додайте відповідну toleration до Поду, або видаліть taint з Ноди.
   </details>

---

## Практична вправа

**Завдання**: Попрактикуйте всі техніки планування.

**Кроки**:

### Частина A: nodeSelector

1. **Додайте мітку Ноді та використайте nodeSelector**:
```bash
# Get a node name
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Label the node
kubectl label node $NODE disk=ssd

# Create pod with nodeSelector
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: ssd-pod
spec:
  nodeSelector:
    disk: ssd
  containers:
  - name: nginx
    image: nginx
EOF

# Verify placement
kubectl get pod ssd-pod -o wide

# Cleanup
kubectl delete pod ssd-pod
kubectl label node $NODE disk-
```

### Частина B: Taints і Tolerations

2. **Додайте taint та створіть Под з toleration**:
```bash
# Taint the node
kubectl taint nodes $NODE dedicated=special:NoSchedule

# Try to create pod without toleration
kubectl run no-toleration --image=nginx

# Check - should be Pending or on different node
kubectl get pod no-toleration -o wide

# Create pod with toleration
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: with-toleration
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "special"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
EOF

# Verify placement
kubectl get pod with-toleration -o wide

# Cleanup
kubectl delete pod no-toleration with-toleration
kubectl taint nodes $NODE dedicated-
```

### Частина C: Анти-спорідненість Подів

3. **Розподіліть Поди між Нодами**:
```bash
cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spread-deploy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spread
  template:
    metadata:
      labels:
        app: spread
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: spread
              topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx
        image: nginx
EOF

# Check pod distribution
kubectl get pods -l app=spread -o wide

# Cleanup
kubectl delete deployment spread-deploy
```

**Критерії успіху**:
- [ ] Вмієте використовувати nodeSelector
- [ ] Вмієте додавати/видаляти taints Нод
- [ ] Вмієте додавати tolerations до Подів
- [ ] Розумієте спорідненість та анти-спорідненість
- [ ] Вмієте діагностувати проблеми з плануванням

---

## Практичні вправи

### Вправа 1: nodeSelector (Ціль: 3 хвилини)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Label node
kubectl label node $NODE env=production

# Create pod with nodeSelector
kubectl run selector-test --image=nginx --dry-run=client -o yaml | \
  kubectl patch --dry-run=client -o yaml -f - \
  -p '{"spec":{"nodeSelector":{"env":"production"}}}' | kubectl apply -f -

# Or simpler - just use YAML
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: selector-test
spec:
  nodeSelector:
    env: production
  containers:
  - name: nginx
    image: nginx
EOF

# Verify
kubectl get pod selector-test -o wide

# Cleanup
kubectl delete pod selector-test
kubectl label node $NODE env-
```

### Вправа 2: Taints (Ціль: 5 хвилин)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Add taint
kubectl taint nodes $NODE app=critical:NoSchedule

# View taint
kubectl describe node $NODE | grep Taints

# Pod without toleration - will be Pending or elsewhere
kubectl run no-tol --image=nginx
kubectl get pod no-tol -o wide

# Pod with toleration
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: with-tol
spec:
  tolerations:
  - key: "app"
    operator: "Equal"
    value: "critical"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
EOF

kubectl get pod with-tol -o wide

# Cleanup
kubectl delete pod no-tol with-tol
kubectl taint nodes $NODE app-
```

### Вправа 3: Спорідненість Нод (Ціль: 5 хвилин)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE size=large

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: affinity-test
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: size
            operator: In
            values:
            - large
            - xlarge
  containers:
  - name: nginx
    image: nginx
EOF

kubectl get pod affinity-test -o wide

# Cleanup
kubectl delete pod affinity-test
kubectl label node $NODE size-
```

### Вправа 4: Анти-спорідненість Подів (Ціль: 5 хвилин)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anti-affinity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anti-test
  template:
    metadata:
      labels:
        app: anti-test
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: anti-test
            topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx
        image: nginx
EOF

# Check distribution (each pod on different node)
kubectl get pods -l app=anti-test -o wide

# Cleanup
kubectl delete deployment anti-affinity
```

### Вправа 5: Діагностика — Під у стані Pending (Ціль: 5 хвилин)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Create impossible scenario
kubectl taint nodes $NODE impossible=true:NoSchedule

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pending-pod
spec:
  nodeSelector:
    nonexistent: label
  containers:
  - name: nginx
    image: nginx
EOF

# Diagnose
kubectl get pod pending-pod
kubectl describe pod pending-pod | grep -A10 Events

# YOUR TASK: Why is it Pending? Fix it.

# Cleanup
kubectl delete pod pending-pod
kubectl taint nodes $NODE impossible-
```

<details>
<summary>Відповідь</summary>

Под у стані Pending з двох причин:
1. nodeSelector вимагає мітку `nonexistent=label`, якої немає на жодній Ноді
2. Усі Ноди мають taint, який Под не допускає

Виправте одним із способів:
- Додайте мітку до Ноди: `kubectl label node $NODE nonexistent=label`
- Додайте toleration та видаліть nodeSelector

</details>

### Вправа 6: Виклик — складне планування

Створіть Под, який:
1. Повинен працювати на Нодах із міткою `tier=frontend`
2. Бажано на Нодах із міткою `zone=us-east-1a`
3. Допускає taint `frontend=true:NoSchedule`

```bash
# YOUR TASK: Create this pod
```

<details>
<summary>Відповідь</summary>

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE tier=frontend zone=us-east-1a
kubectl taint nodes $NODE frontend=true:NoSchedule

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: complex-schedule
spec:
  tolerations:
  - key: "frontend"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tier
            operator: In
            values:
            - frontend
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - us-east-1a
  containers:
  - name: nginx
    image: nginx
EOF

kubectl get pod complex-schedule -o wide

# Cleanup
kubectl delete pod complex-schedule
kubectl label node $NODE tier- zone-
kubectl taint nodes $NODE frontend-
```

</details>

---

## Наступний модуль

[Модуль 2.7: ConfigMaps і Secrets](module-2.7-configmaps-secrets/) — Управління конфігурацією застосунків.
