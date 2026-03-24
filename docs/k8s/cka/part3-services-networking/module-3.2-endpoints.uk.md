# Модуль 3.2: Ендпоінти та EndpointSlices

> **Складність**: `[MEDIUM]` - Розуміння механіки сервісів
>
> **Час на проходження**: 30-40 хвилин
>
> **Передумови**: Модуль 3.1 (Сервіси)

---

## Чому цей модуль важливий

Коли ви створюєте Сервіс, Kubernetes автоматично створює об'єкт Endpoints, який відстежує, які IP-адреси подів мають отримувати трафік. Розуміння ендпоінтів має вирішальне значення для вирішення проблем із сервісами — коли сервіс не має ендпоінтів, трафік нікуди не йде.

Іспит CKA перевіряє вашу здатність до усунення несправностей сервісів, і перевірка ендпоінтів — це ваш основний інструмент налагодження. Ви також зіткнетеся з EndpointSlices, новішою та більш масштабованою версією Endpoints.

> **Аналогія з телефонною книгою**
>
> Якщо Сервіс — це номер телефону (стабільний), то Ендпоінти — це записи в телефонній книзі, які відображають цей номер на реальних людей (поди). Коли ви телефонуєте за номером, телефонна система шукає в книзі, хто зараз доступний, і з'єднує вас. Kubernetes робить те саме — IP-адреса Сервісу шукається в Ендпоінтах (Endpoints), щоб знайти доступні IP-адреси подів.

---

## Що ви дізнаєтесь

До кінця цього модуля ви зможете:
- Розуміти, як Ендпоінти з'єднують Сервіси з Подами
- Налагоджувати сервіси, перевіряючи ендпоінти
- Створювати ручні ендпоінти для зовнішніх сервісів
- Розуміти EndpointSlices та їхні переваги
- Працювати з headless сервісами та розуміти їхню унікальну поведінку ендпоінтів

---

## Чи знали ви?

- **Ендпоінти можуть бути величезними**: У кластерах з тисячами подів один об'єкт Endpoints може містити тисячі IP-адрес. Це викликало проблеми з продуктивністю, що призвело до створення EndpointSlices.

- **EndpointSlices — це майбутнє**: Починаючи з Kubernetes 1.21, EndpointSlices використовуються за замовчуванням. Кожен зріз (slice) містить до 100 ендпоінтів, що робить оновлення набагато ефективнішими.

- **Контролери відстежують ендпоінти**: Багато контролерів (наприклад, контролери Інгрес (Ingress)) відстежують Ендпоінти, щоб знати, куди маршрутизувати трафік. Коли ендпоінти змінюються, таблиці маршрутизації оновлюються автоматично.

---

## Частина 1: Основи Ендпоінтів

### 1.1 Що таке Ендпоінти?

Ендпоінти — це клей між Сервісами та Подами:

```
┌────────────────────────────────────────────────────────────────┐
│                   Сервіс → Ендпоінти → Поди                     │
│                                                                 │
│   ┌──────────────────┐    ┌──────────────────┐                │
│   │    Сервіс        │    │    Ендпоінти     │                │
│   │    web-svc       │    │    web-svc       │                │
│   │                  │    │                  │                │
│   │  селектор:       │───►│  subsets:        │                │
│   │    app: web      │    │  - addresses:    │                │
│   │                  │    │    - 10.244.1.5  │───► Под 1      │
│   │  порти:          │    │    - 10.244.2.8  │───► Под 2      │
│   │  - port: 80      │    │    - 10.244.1.12 │───► Под 3      │
│   │                  │    │    ports:        │                │
│   │                  │    │    - port: 8080  │                │
│   └──────────────────┘    └──────────────────┘                │
│                                                                 │
│   Ендпоінти автоматично створюються та оновлюються контролером  │
│   ендпоінтів                                                    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Життєвий цикл Ендпоінта

```
┌────────────────────────────────────────────────────────────────┐
│                   Контролер ендпоінтів                          │
│                                                                 │
│   Відстежує: Поди та Сервіси                                   │
│   Оновлює: об'єкти Endpoints                                   │
│                                                                 │
│   Под створено (мітка: app=web)                                │
│       │                                                         │
│       ▼                                                         │
│   Контролер знаходить Сервіс із селектором app=web             │
│       │                                                         │
│       ▼                                                         │
│   Додає IP-адресу Пода до Ендпоінтів Сервісу                   │
│                                                                 │
│   Под видалено або він не пройшов перевірку готовності (Readiness)│
│       │                                                         │
│       ▼                                                         │
│   Видаляє IP-адресу Пода з Ендпоінтів                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Перегляд Ендпоінтів

```bash
# List all endpoints
k get endpoints
k get ep                    # Short form

# Get specific endpoint
k get endpoints web-svc

# Detailed view
k describe endpoints web-svc

# Get endpoints as YAML
k get endpoints web-svc -o yaml

# Wide output with pod IPs
k get endpoints -o wide
```

### 1.4 Структура Ендпоінта

```yaml
# What an Endpoints object looks like
apiVersion: v1
kind: Endpoints
metadata:
  name: web-svc           # Must match Service name
  namespace: default
subsets:
- addresses:              # Ready pod IPs
  - ip: 10.244.1.5
    nodeName: worker-1
    targetRef:
      kind: Pod
      name: web-abc123
      namespace: default
  - ip: 10.244.2.8
    nodeName: worker-2
    targetRef:
      kind: Pod
      name: web-def456
      namespace: default
  notReadyAddresses:      # Pods not passing readiness probe
  - ip: 10.244.1.12
    nodeName: worker-1
    targetRef:
      kind: Pod
      name: web-ghi789
      namespace: default
  ports:
  - port: 8080
    protocol: TCP
```

---

## Частина 2: Налагодження з використанням Ендпоінтів

### 2.1 Немає Ендпоінтів = Немає Трафіку

```bash
# Service exists but has no endpoints
k get svc web-svc
# NAME      TYPE        CLUSTER-IP     PORT(S)
# web-svc   ClusterIP   10.96.45.123   80/TCP

k get endpoints web-svc
# NAME      ENDPOINTS   AGE
# web-svc   <none>      5m     ← Problem!
```

### 2.2 Типові причини відсутності Ендпоінтів

| Симптом | Причина | Команда для налагодження | Рішення |
|---------|-------|---------------|----------|
| `<none>` ендпоінтів | Жоден под не відповідає селектору | `k get pods --show-labels` | Виправити селектор або мітки подів |
| `<none>` ендпоінтів | Поди не працюють (not running) | `k get pods` | Виправити проблеми з подами |
| `<none>` ендпоінтів | Поди в іншому просторі імен | `k get pods -A` | Перевірити Простір імен |
| Часткові ендпоінти | Деякі поди не готові (not ready) | `k describe endpoints` | Перевірити проби готовності (readiness probes) |

### 2.3 Робочий процес налагодження

```bash
# Step 1: Check if endpoints exist
k get endpoints web-svc
# If <none>, proceed to step 2

# Step 2: Check service selector
k get svc web-svc -o yaml | grep -A5 selector
# selector:
#   app: web

# Step 3: Find pods with matching labels
k get pods --selector=app=web
# Should list pods backing the service

# Step 4: If no pods found, check what labels pods have
k get pods --show-labels
# Compare with service selector

# Step 5: If pods exist but not in endpoints, check pod status
k get pods
# Look for pods that aren't Running

# Step 6: Check for readiness probe failures
k describe pod <pod-name> | grep -A10 Readiness
```

### 2.4 Ендпоінти з не готовими подами (NotReady Pods)

```bash
# Describe shows both ready and not-ready addresses
k describe endpoints web-svc

# Output:
# Name:         web-svc
# Subsets:
#   Addresses:          10.244.1.5,10.244.2.8
#   NotReadyAddresses:  10.244.1.12
#   Ports:
#     Name     Port  Protocol
#     ----     ----  --------
#     <unset>  8080  TCP
```

Поди у `NotReadyAddresses` **не** отримують трафік.

---

## Частина 3: Ручні Ендпоінти

### 3.1 Коли використовувати Ручні Ендпоінти

Створюйте ендпоінти вручну, коли потрібно вказати на:
- Зовнішні бази даних поза Kubernetes
- Сервіси в інших кластерах
- Ресурси на основі IP-адрес, які не є подами

### 3.2 Створення Ручних Ендпоінтів

```yaml
# Step 1: Create service WITHOUT selector
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  ports:
  - port: 5432
    targetPort: 5432
  # No selector! This is intentional.
---
# Step 2: Create Endpoints with same name
apiVersion: v1
kind: Endpoints
metadata:
  name: external-db     # Must match service name exactly
subsets:
- addresses:
  - ip: 192.168.1.100   # External database IP
  - ip: 192.168.1.101   # Backup database IP
  ports:
  - port: 5432
```

```bash
# Apply both
k apply -f external-db.yaml

# Verify
k get svc,endpoints external-db

# Now pods can reach external DB via:
# external-db.default.svc.cluster.local:5432
```

### 3.3 Варіанти використання Ручних Ендпоінтів

```yaml
# Example: External API endpoint
apiVersion: v1
kind: Service
metadata:
  name: external-api
spec:
  ports:
  - port: 443
---
apiVersion: v1
kind: Endpoints
metadata:
  name: external-api
subsets:
- addresses:
  - ip: 52.84.123.45     # External API server
  ports:
  - port: 443
```

---

## Частина 4: EndpointSlices

### 4.1 Чому EndpointSlices?

```
┌────────────────────────────────────────────────────────────────┐
│                   Проблема Ендпоінтів                           │
│                                                                 │
│   Великий Сервіс з 5000 подів                                  │
│                                                                 │
│   Один об'єкт Endpoints:                                       │
│   - Містить усі 5000 IP-адрес                                  │
│   - Будь-яка зміна пода = оновлення всього об'єкта             │
│   - Великий обсяг даних надсилається всім спостерігачам        │
│   - Навантаження на API-сервер та etcd                         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   Рішення з EndpointSlices                      │
│                                                                 │
│   Ті ж 5000 подів розділені на 50 зрізів (slices)              │
│                                                                 │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐      ┌─────────┐        │
│   │ Зріз 1  │ │ Зріз 2  │ │ Зріз 3  │ ...  │ Зріз 50 │        │
│   │ 100 IP  │ │ 100 IP  │ │ 100 IP  │      │ 100 IP  │        │
│   └─────────┘ └─────────┘ └─────────┘      └─────────┘        │
│                                                                 │
│   Зміна пода = оновлення лише відповідного зрізу               │
│   Невеликий обсяг даних, мінімальне навантаження на API-сервер │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Структура EndpointSlice

```yaml
# What an EndpointSlice looks like
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: web-svc-abc12      # Auto-generated name
  labels:
    kubernetes.io/service-name: web-svc
addressType: IPv4
ports:
- name: ""
  port: 8080
  protocol: TCP
endpoints:
- addresses:
  - 10.244.1.5
  conditions:
    ready: true
    serving: true
    terminating: false
  nodeName: worker-1
  targetRef:
    kind: Pod
    name: web-abc123
    namespace: default
- addresses:
  - 10.244.2.8
  conditions:
    ready: true
  nodeName: worker-2
```

### 4.3 Перегляд EndpointSlices

```bash
# List all EndpointSlices
k get endpointslices
k get eps                   # Short form (might conflict with endpoints)

# Get EndpointSlices for a service
k get endpointslices -l kubernetes.io/service-name=web-svc

# Detailed view
k describe endpointslice web-svc-abc12

# Get as YAML
k get endpointslice web-svc-abc12 -o yaml
```

### 4.4 Порівняння Ендпоінтів (Endpoints) та EndpointSlices

| Аспект | Endpoints | EndpointSlices |
|--------|-----------|----------------|
| Макс. кількість записів | Необмежено (але проблематично) | 100 на зріз |
| Область оновлення | Весь об'єкт | Один зріз |
| Версія API | v1 | discovery.k8s.io/v1 |
| За замовчуванням з | Завжди | Kubernetes 1.21 |
| Підтримка Dual-stack | Обмежена | Повна підтримка IPv4/IPv6 |
| Підказки топології | Ні | Так |

---

## Частина 5: Headless Сервіси

### 5.1 Що таке Headless Сервіс?

Headless сервіс не має ClusterIP. DNS повертає безпосередньо IP-адреси подів.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: headless-svc
spec:
  clusterIP: None          # This makes it headless
  selector:
    app: web
  ports:
  - port: 80
```

### 5.2 Поведінка Headless Сервісу

```
┌────────────────────────────────────────────────────────────────┐
│                   Звичайний Сервіс проти Headless Сервісу       │
│                                                                 │
│   Звичайний Сервіс (ClusterIP: 10.96.45.123)                   │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  DNS: web-svc.default.svc → 10.96.45.123 (IP Сервісу)   │  │
│   │  Клієнт → IP Сервісу → kube-proxy → випадковий Под      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   Headless Сервіс (clusterIP: None)                            │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  DNS: web-svc.default.svc →                             │  │
│   │       10.244.1.5 (Под 1)                                │  │
│   │       10.244.2.8 (Под 2)                                │  │
│   │       10.244.1.12 (Под 3)                               │  │
│   │  Клієнт отримує ВСІ IP-адреси подів, сам обирає одну    │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 Варіанти використання Headless Сервісу

| Варіант використання | Чому Headless? |
|----------|---------------|
| StatefulSets | Потрібно звертатися до конкретних подів (pod-0, pod-1) |
| Балансування навантаження на боці клієнта | Клієнту потрібні всі IP-адреси для реалізації власного балансування |
| Виявлення сервісів (Service discovery) | Виявлення всіх інстансів бекенду |
| Кластери баз даних | Потрібне пряме підключення до конкретного вузла |

### 5.4 Ендпоінти Headless Сервісу

```bash
# Endpoints still track pods
k get endpoints headless-svc
# NAME           ENDPOINTS
# headless-svc   10.244.1.5,10.244.2.8,10.244.1.12

# DNS returns multiple A records
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-svc

# Output:
# Name:    headless-svc.default.svc.cluster.local
# Address: 10.244.1.5
# Address: 10.244.2.8
# Address: 10.244.1.12
```

---

## Частина 6: Топологія Сервісів та Підказки Топології (Topology Hints)

### 6.1 Топологічно-обізнана маршрутизація

EndpointSlices підтримують підказки топології для маршрутизації з урахуванням зон:

```yaml
# EndpointSlice with hints
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: web-svc-abc12
endpoints:
- addresses:
  - 10.244.1.5
  zone: us-east-1a          # Pod is in this zone
  hints:
    forZones:
    - name: us-east-1a      # Prefer traffic from same zone
```

### 6.2 Увімкнення Підказок Топології

```yaml
# Service with topology hints
apiVersion: v1
kind: Service
metadata:
  name: web-svc
  annotations:
    service.kubernetes.io/topology-mode: Auto   # Enable hints
spec:
  selector:
    app: web
  ports:
  - port: 80
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|----------|
| Неправильне ім'я ендпоінта | Ендпоінти не пов'язані з сервісом | Ім'я має точно збігатися з ім'ям сервісу |
| Друкарська помилка в селекторі | Немає ендпоінтів | Двічі перевірте селектори міток |
| Відсутній targetRef | Неможливо відстежити ендпоінт до пода | Включіть targetRef у ручні ендпоінти |
| Ігнорування NotReadyAddresses | Думаєте, що поди здорові | Перевіряйте вивід команди describe на наявність не готових (not-ready) подів |
| Плутанина між endpoints/endpointslices | Отримуєте неправильні дані | Використовуйте обидві команди для налагодження |

---

## Тест

1. **Чому сервіс може показувати `<none>` для ендпоінтів?**
   <details>
   <summary>Відповідь</summary>
   Селектор сервісу не відповідає міткам жодних запущених подів, АБО жоден под з відповідними мітками не перебуває у стані Running.
   </details>

2. **Як створити ендпоінти для зовнішнього сервісу?**
   <details>
   <summary>Відповідь</summary>
   1. Створіть Сервіс без селектора
   2. Створіть об'єкт Endpoints з таким самим ім'ям, як і у сервісу
   3. Додайте зовнішні IP-адреси до `subsets` в Endpoints
   </details>

3. **Яка різниця між `addresses` та `notReadyAddresses` в ендпоінтах?**
   <details>
   <summary>Відповідь</summary>
   `addresses` містить IP-адреси подів, які готові та приймають трафік. `notReadyAddresses` містить IP-адреси подів, які не проходять свою пробу готовності (readiness probe) та не будуть отримувати трафік.
   </details>

4. **Чому були впроваджені EndpointSlices?**
   <details>
   <summary>Відповідь</summary>
   Для кращої обробки великих сервісів. Один об'єкт Endpoints для тисяч подів викликав проблеми з продуктивністю. EndpointSlices розділяють ендпоінти на частини по 100, тому оновлення впливають лише на один зріз (slice).
   </details>

5. **Що робить сервіс "headless" і що особливого в його ендпоінтах?**
   <details>
   <summary>Відповідь</summary>
   Встановлення `clusterIP: None` робить сервіс headless. Його ендпоінти повертаються безпосередньо через DNS (кілька A-записів) замість використання віртуального ClusterIP.
   </details>

---

## Практичні вправи

**Завдання**: Налагодити сервіс з проблемами ендпоінтів.

**Кроки**:

1. **Створити деплоймент**:
```bash
k create deployment web --image=nginx --replicas=3
```

2. **Створити сервіс з неправильним селектором**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: broken-service
spec:
  selector:
    app: webapp          # Wrong! Should be "web"
  ports:
  - port: 80
EOF
```

3. **Спостерігати за проблемою**:
```bash
k get endpoints broken-service
# Shows: <none>
```

4. **Налагодити проблему**:
```bash
# Check what selector the service has
k get svc broken-service -o yaml | grep -A2 selector

# Check what labels the pods have
k get pods --show-labels

# Find the mismatch!
```

5. **Виправити сервіс**:
```bash
k delete svc broken-service
k expose deployment web --port=80 --name=broken-service
```

6. **Переконатися, що ендпоінти існують**:
```bash
k get endpoints broken-service
# Should show 3 pod IPs
```

7. **Перевірити також EndpointSlices**:
```bash
k get endpointslices -l kubernetes.io/service-name=broken-service
```

8. **Протестувати з headless сервісом**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless-web
spec:
  clusterIP: None
  selector:
    app: web
  ports:
  - port: 80
EOF

# Check DNS returns multiple IPs
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-web
```

9. **Очищення**:
```bash
k delete deployment web
k delete svc broken-service headless-web
```

**Критерії успіху**:
- [ ] Вміє знаходити відсутні ендпоінти
- [ ] Вміє налагоджувати невідповідності селекторів
- [ ] Розуміє різницю між endpoints та endpointslices
- [ ] Вміє створювати headless сервіси
- [ ] Розуміє відмінності у поведінці DNS

---

## Практичні вправи

### Вправа 1: Перевірка Ендпоінтів (Ціль: 2 хвилини)

```bash
# Setup
k create deployment drill --image=nginx --replicas=2
k expose deployment drill --port=80

# Check endpoints
k get endpoints drill

# Get detailed endpoint info
k describe endpoints drill

# Get as YAML (see pod IPs)
k get endpoints drill -o yaml

# Check EndpointSlices
k get endpointslices -l kubernetes.io/service-name=drill

# Cleanup
k delete deployment drill
k delete svc drill
```

### Вправа 2: Налагодження відсутніх Ендпоінтів (Ціль: 3 хвилини)

```bash
# Create deployment
k create deployment debug-app --image=nginx

# Create service with typo in selector
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: debug-svc
spec:
  selector:
    app: debug-apps    # Typo: extra 's'
  ports:
  - port: 80
EOF

# Observe problem
k get endpoints debug-svc
# <none>

# Debug
k get pods --show-labels
k get svc debug-svc -o jsonpath='{.spec.selector}'

# Fix
k delete svc debug-svc
k expose deployment debug-app --port=80 --name=debug-svc

# Verify
k get endpoints debug-svc

# Cleanup
k delete deployment debug-app
k delete svc debug-svc
```

### Вправа 3: Ручні Ендпоінти (Ціль: 4 хвилини)

```bash
# Create service without selector
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: external-svc
spec:
  ports:
  - port: 80
EOF

# Check - no endpoints yet
k get endpoints external-svc

# Create manual endpoints
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Endpoints
metadata:
  name: external-svc
subsets:
- addresses:
  - ip: 1.2.3.4
  - ip: 5.6.7.8
  ports:
  - port: 80
EOF

# Verify endpoints
k get endpoints external-svc
k describe endpoints external-svc

# Cleanup
k delete svc external-svc
k delete endpoints external-svc
```

### Вправа 4: Headless Сервіс (Ціль: 3 хвилини)

```bash
# Create deployment
k create deployment headless-test --image=nginx --replicas=3

# Create headless service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless
spec:
  clusterIP: None
  selector:
    app: headless-test
  ports:
  - port: 80
EOF

# Verify no ClusterIP
k get svc headless
# CLUSTER-IP should be "None"

# Check endpoints (still exist!)
k get endpoints headless

# Test DNS - should return multiple IPs
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless

# Cleanup
k delete deployment headless-test
k delete svc headless
```

### Вправа 5: Аналіз EndpointSlice (Ціль: 3 хвилини)

```bash
# Create deployment
k create deployment slice-test --image=nginx --replicas=3
k expose deployment slice-test --port=80

# Get EndpointSlice name
k get endpointslices -l kubernetes.io/service-name=slice-test

# Describe it
SLICE_NAME=$(k get endpointslices -l kubernetes.io/service-name=slice-test -o jsonpath='{.items[0].metadata.name}')
k describe endpointslice $SLICE_NAME

# Get YAML
k get endpointslice $SLICE_NAME -o yaml

# Note the endpoints array with conditions

# Cleanup
k delete deployment slice-test
k delete svc slice-test
```

### Вправа 6: Готовність (Readiness) та Ендпоінти (Ціль: 4 хвилини)

```bash
# Create pod with failing readiness probe
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: unready-pod
  labels:
    app: unready
spec:
  containers:
  - name: nginx
    image: nginx
    readinessProbe:
      httpGet:
        path: /nonexistent
        port: 80
      initialDelaySeconds: 1
      periodSeconds: 2
EOF

# Create service
k expose pod unready-pod --port=80 --name=unready-svc

# Wait a moment, then check endpoints
sleep 10
k get endpoints unready-svc
# Should be <none> or empty!

# Check why
k describe endpoints unready-svc
# Look for notReadyAddresses

# Check pod status
k get pod unready-pod
# Not ready due to probe

# Cleanup
k delete pod unready-pod
k delete svc unready-svc
```

### Вправа 7: Масштабування та відстеження Ендпоінтів (Ціль: 3 хвилини)

```bash
# Create deployment
k create deployment watch-test --image=nginx --replicas=1
k expose deployment watch-test --port=80

# Watch endpoints in terminal 1 (or background)
k get endpoints watch-test -w &

# Scale up and observe endpoints change
k scale deployment watch-test --replicas=5
sleep 5

# Scale down
k scale deployment watch-test --replicas=2
sleep 5

# Bring watch to foreground and stop
fg
# Ctrl+C

# Cleanup
k delete deployment watch-test
k delete svc watch-test
```

### Вправа 8: Виклик - Повний робочий процес Ендпоінтів

Без підглядання у рішення:

1. Створіть деплоймент `ep-challenge` з 3 репліками nginx
2. Створіть сервіс, який навмисно має неправильний селектор
3. З'ясуйте, чому ендпоінти порожні
4. Виправте сервіс
5. Створіть headless сервіс для цього ж деплойменту
6. Переконайтеся, що DNS повертає 3 IP-адреси для headless сервісу
7. Створіть ручні ендпоінти для IP-адреси 10.0.0.1
8. Очистіть усе

```bash
# YOUR TASK: Complete in under 6 minutes
```

<details>
<summary>Відповідь</summary>

```bash
# 1. Create deployment
k create deployment ep-challenge --image=nginx --replicas=3

# 2. Create service with wrong selector
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: wrong-svc
spec:
  selector:
    app: wrong
  ports:
  - port: 80
EOF

# 3. Diagnose
k get endpoints wrong-svc
# <none>
k get pods --show-labels
# Labels show app=ep-challenge, not app=wrong

# 4. Fix
k delete svc wrong-svc
k expose deployment ep-challenge --port=80 --name=fixed-svc
k get endpoints fixed-svc
# Shows 3 IPs

# 5. Create headless service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless-challenge
spec:
  clusterIP: None
  selector:
    app: ep-challenge
  ports:
  - port: 80
EOF

# 6. Verify DNS
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-challenge
# Should show 3 IPs

# 7. Manual endpoints
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: manual-svc
spec:
  ports:
  - port: 80
---
apiVersion: v1
kind: Endpoints
metadata:
  name: manual-svc
subsets:
- addresses:
  - ip: 10.0.0.1
  ports:
  - port: 80
EOF
k get endpoints manual-svc

# 8. Cleanup
k delete deployment ep-challenge
k delete svc fixed-svc headless-challenge manual-svc
k delete endpoints manual-svc
```

</details>

---

## Наступний модуль

[Модуль 3.3: DNS та CoreDNS](module-3.3-dns.uk.md) - Глибоке занурення у Kubernetes DNS та виявлення сервісів.
