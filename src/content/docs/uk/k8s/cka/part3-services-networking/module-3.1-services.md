---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 3.1: \u0421\u0435\u0440\u0432\u0456\u0441\u0438 \u2014 ClusterIP, NodePort, LoadBalancer"
slug: uk/k8s/cka/part3-services-networking/module-3.1-services
sidebar: 
  order: 2
lab: 
  id: cka-3.1-services
  url: https://killercoda.com/kubedojo/scenario/cka-3.1-services
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` - Базова концепція мережі
>
> **Час на проходження**: 45-55 хвилин
>
> **Передумови**: Модуль 2.1 (Поди), Модуль 2.2 (Деплойменти)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** ClusterIP, NodePort та LoadBalancer сервіси й пояснити потік трафіку для кожного
- **Дебажити** з'єднання сервісів, перевіряючи endpoints, селектори та правила kube-proxy
- **Простежити** запит від клієнта через Service до Pod, використовуючи правила iptables/IPVS
- **Пояснити**, як kube-proxy реалізує балансування навантаження сервісів у режимах iptables та IPVS

---

## Чому цей модуль важливий

Поди є ефемерними — вони з'являються та зникають, а їхні IP-адреси змінюються. Сервіси забезпечують **стабільну мережу** для ваших додатків. Без сервісів вам довелося б вручну відстежувати кожну IP-адресу пода, що неможливо при масштабуванні.

На іспиті CKA Сервіси перевіряються дуже ретельно. Вам потрібно буде швидко створювати сервіси, відкривати доступ до деплойментів, налагоджувати підключення до сервісів та розуміти, коли використовувати кожен тип сервісу.

> **Аналогія з рестораном**
>
> Уявіть собі ресторан (ваш додаток). Поди — це окремі кухарі — вони можуть змінювати зміни, хворіти або їх можуть замінити. Номер телефону ресторану (Сервіс) залишається незмінним незалежно від того, які кухарі працюють. Клієнти телефонують на той самий номер, і дзвінок перенаправляється до доступного кухаря. Це саме те, що роблять Сервіси у Kubernetes.

---

## Що ви дізнаєтесь

До кінця цього модуля ви зможете:
- Розуміти чотири типи сервісів і коли використовувати кожен з них
- Створювати сервіси імперативно та декларативно
- Відкривати доступ до деплойментів та подів
- Налагоджувати проблеми з підключенням до сервісів
- Використовувати селектори для націлювання на правильні поди

---

## Чи знали ви?

- **Сервіси з'явилися раніше за Поди**: Концепція стабільних IP-адрес сервісів була розроблена ще до того, як у Kubernetes з'явилися поди. Засновники знали, що ефемерним подам потрібні стабільні кінцеві точки.

- **Віртуальні IP-адреси — це магія**: IP-адрес ClusterIP не існує на жодному мережевому інтерфейсі. Вони є "віртуальними" IP-адресами, які kube-proxy перехоплює та маршрутизує за допомогою правил iptables або nftables. (Примітка: режим IPVS застарів у K8s 1.35 — nftables є рекомендованою заміною.)

- **Діапазон NodePort можна налаштувати**: Діапазон за замовчуванням 30000-32767 можна змінити за допомогою прапорця `--service-node-port-range` на API-сервері, хоча більшість кластерів дотримуються значень за замовчуванням.

---

## Частина 1: Основи Сервісів

### 1.1 Чому Сервіси?

```
┌────────────────────────────────────────────────────────────────┐
│                     Проблема                                    │
│                                                                 │
│   Клієнт хоче отримати доступ до "web app"                     │
│                                                                 │
│   ┌─────────────────────────────────────────────────────┐      │
│   │  Под: web-abc123   IP: 10.244.1.5   ← Створено      │      │
│   │  Под: web-def456   IP: 10.244.2.8   ← Працює        │      │
│   │  Под: web-ghi789   IP: 10.244.1.12  ← Створено      │      │
│   │  Под: web-abc123   IP: 10.244.1.5   ← Видалено!     │      │
│   │  Под: web-xyz999   IP: 10.244.3.2   ← Новий под     │      │
│   └─────────────────────────────────────────────────────┘      │
│                                                                 │
│   Яку IP-адресу має використовувати клієнт? Вони змінюються!   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                     Рішення: Сервіси                            │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐    │
│   │            Сервіс: web-service                         │    │
│   │            ClusterIP: 10.96.45.123                    │    │
│   │            (Ніколи не змінюється!)                     │    │
│   │                                                        │    │
│   │     Селектор: app=web                                  │    │
│   │         │                                              │    │
│   │         ├──► Под: web-def456 (10.244.2.8)             │    │
│   │         ├──► Под: web-ghi789 (10.244.1.12)            │    │
│   │         └──► Под: web-xyz999 (10.244.3.2)             │    │
│   └───────────────────────────────────────────────────────┘    │
│                                                                 │
│   Клієнт завжди використовує 10.96.45.123 - Kubernetes все інше│
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Компоненти Сервісу

| Компонент | Опис |
|-----------|-------------|
| **ClusterIP** | Стабільна внутрішня IP-адреса для сервісу |
| **Selector** | Мітки, що визначають, на які поди маршрутизувати |
| **Port** | Порт, на якому слухає сервіс |
| **TargetPort** | Порт на подах, куди пересилається трафік |
| **Endpoints** | Фактичні IP-адреси подів, що підтримують сервіс |

### 1.3 Як працюють Сервіси

```
┌────────────────────────────────────────────────────────────────┐
│                   Потік запитів до Сервісу                      │
│                                                                 │
│   1. Клієнт надсилає запит на IP-адресу Сервісу (10.96.45.123:80)│
│                         │                                       │
│                         ▼                                       │
│   2. kube-proxy (на кожному вузлі) перехоплює                   │
│                         │                                       │
│                         ▼                                       │
│   3. kube-proxy використовує правила iptables/nftables          │
│                         │                                       │
│                         ▼                                       │
│   4. Запит пересилається на одну з IP-адрес пода                │
│      (балансування навантаження - round robin за замовчуванням) │
│                         │                                       │
│                         ▼                                       │
│   5. Под отримує запит на targetPort                            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Частина 2: Типи Сервісів

### 2.1 Чотири типи Сервісів

| Тип | Область дії | Варіант використання | Частота на іспиті |
|------|-------|----------|----------------|
| **ClusterIP** | Лише внутрішня | Зв'язок між подами | ⭐⭐⭐⭐⭐ |
| **NodePort** | Зовнішня через IP вузла | Розробка, тестування | ⭐⭐⭐⭐ |
| **LoadBalancer** | Зовнішня через хмарний БН | Продакшн у хмарі | ⭐⭐⭐ |
| **ExternalName** | DNS-псевдонім | Зовнішні сервіси | ⭐⭐ |

### 2.2 ClusterIP (За замовчуванням)

```yaml
# Internal-only access - most common type
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: ClusterIP           # Default, can be omitted
  selector:
    app: web                # Match pods with label app=web
  ports:
  - port: 80                # Service listens on port 80
    targetPort: 8080        # Forward to pod port 8080
```

```
┌────────────────────────────────────────────────────────────────┐
│                     Сервіс ClusterIP                            │
│                                                                 │
│   Доступно лише зсередини кластера                             │
│                                                                 │
│   ┌────────────────┐        ┌────────────────┐                │
│   │  Інший Под     │───────►│  ClusterIP     │                │
│   │  (клієнт)      │        │  10.96.45.123  │                │
│   └────────────────┘        │                │                │
│                             │  ┌──────────┐  │                │
│                             │  │ Под      │  │                │
│                             │  │ app=web  │  │                │
│   ┌────────────────┐        │  └──────────┘  │                │
│   │  Зовнішній     │───X───►│                │                │
│   │  (заблоковано) │        │  ┌──────────┐  │                │
│   └────────────────┘        │  │ Под      │  │                │
│                             │  │ app=web  │  │                │
│                             │  └──────────┘  │                │
│                             └────────────────┘                │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 NodePort

```yaml
# Exposes service on each node's IP at a static port
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80              # ClusterIP port (internal)
    targetPort: 8080      # Pod port
    nodePort: 30080       # External port (30000-32767)
```

```
┌────────────────────────────────────────────────────────────────┐
│                     Сервіс NodePort                             │
│                                                                 │
│   Зовнішній доступ через <NodeIP>:<NodePort>                   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    Кластер                               │  │
│   │                                                          │  │
│   │  Вузол 1 (192.168.1.10)    Вузол 2 (192.168.1.11)      │  │
│   │  ┌──────────────────┐      ┌──────────────────┐        │  │
│   │  │ :30080 ──────────┼──────┼─► Под (app=web)  │        │  │
│   │  └──────────────────┘      └──────────────────┘        │  │
│   │                                                          │  │
│   └─────────────────────────────────────────────────────────┘  │
│                 ▲                          ▲                   │
│                 │                          │                   │
│   Зовнішній: 192.168.1.10:30080  АБО 192.168.1.11:30080       │
│             (Обидва працюють!)                                  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.4 LoadBalancer

```yaml
# Creates external load balancer (cloud provider)
apiVersion: v1
kind: Service
metadata:
  name: web-lb
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Сервіс LoadBalancer                           │
│                                                                 │
│   Хмарний провайдер створює зовнішній балансувальник навантаження│
│                                                                 │
│   ┌──────────────────┐                                         │
│   │   Інтернет       │                                         │
│   └────────┬─────────┘                                         │
│            │                                                    │
│            ▼                                                    │
│   ┌──────────────────┐     Зовнішня IP-адреса: 34.85.123.45    │
│   │   Хмарний БН     │                                         │
│   │   (AWS/GCP/Azure)│                                         │
│   └────────┬─────────┘                                         │
│            │                                                    │
│            ▼                                                    │
│   ┌──────────────────────────────────────────────────┐         │
│   │             NodePort (автоматично створений)      │         │
│   │                      │                            │         │
│   │        ┌─────────────┼─────────────┐             │         │
│   │        ▼             ▼             ▼             │         │
│   │    ┌──────┐     ┌──────┐     ┌──────┐           │         │
│   │    │ Под  │     │ Под  │     │ Под  │           │         │
│   │    └──────┘     └──────┘     └──────┘           │         │
│   └──────────────────────────────────────────────────┘         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.5 ExternalName

```yaml
# DNS alias to external service (no proxying)
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: database.example.com   # Returns CNAME record
  # No selector - points to external DNS name
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Сервіс ExternalName                           │
│                                                                 │
│   DNS-псевдонім — без ClusterIP, без проксіювання              │
│                                                                 │
│   ┌────────────────┐                                           │
│   │  Под           │                                           │
│   │                │──► DNS: external-db.default.svc           │
│   │                │          │                                │
│   └────────────────┘          │ Повертає CNAME                 │
│                               ▼                                │
│                     database.example.com                       │
│                               │                                │
│                               ▼                                │
│                     ┌──────────────────┐                       │
│                     │  Зовнішня БД     │                       │
│                     │  (поза K8s)      │                       │
│                     └──────────────────┘                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Частина 3: Створення Сервісів

### 3.1 Імперативні команди (Швидко для іспиту)

```bash
# Expose a deployment (most common exam task)
k expose deployment nginx --port=80 --target-port=8080 --name=nginx-svc

# Expose with NodePort
k expose deployment nginx --port=80 --type=NodePort --name=nginx-np

# Expose a pod
k expose pod nginx --port=80 --name=nginx-pod-svc

# Generate YAML without creating
k expose deployment nginx --port=80 --dry-run=client -o yaml > svc.yaml

# Create service for existing pods by selector
k create service clusterip my-svc --tcp=80:8080
```

### 3.2 Опції команди Expose

```bash
# Full syntax
k expose deployment <name> \
  --port=<service-port> \
  --target-port=<pod-port> \
  --type=<ClusterIP|NodePort|LoadBalancer> \
  --name=<service-name> \
  --protocol=<TCP|UDP>

# Examples
k expose deployment web --port=80 --target-port=8080
k expose deployment web --port=80 --type=NodePort
k expose deployment web --port=80 --type=LoadBalancer
```

### 3.3 Декларативний YAML

```yaml
# Complete service example
apiVersion: v1
kind: Service
metadata:
  name: web-service
  labels:
    app: web
spec:
  type: ClusterIP
  selector:
    app: web              # MUST match pod labels
    tier: frontend
  ports:
  - name: http            # Named port (good practice)
    port: 80              # Service port
    targetPort: 8080      # Pod port (can be name or number)
    protocol: TCP         # TCP (default) or UDP
```

### 3.4 Сервіси з кількома портами

```yaml
# Service with multiple ports
apiVersion: v1
kind: Service
metadata:
  name: multi-port-svc
spec:
  selector:
    app: web
  ports:
  - name: http            # Required when multiple ports
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
  - name: metrics
    port: 9090
    targetPort: 9090
```

---

## Частина 4: Виявлення Сервісів (Service Discovery)

### 4.1 Виявлення на основі DNS

Кожен сервіс отримує запис DNS:
- `<service-name>` - в межах одного Простору імен
- `<service-name>.<namespace>` - між Просторами імен
- `<service-name>.<namespace>.svc.cluster.local` - повністю визначене ім'я

```bash
# From a pod in the same namespace
curl web-service

# From a pod in different namespace
curl web-service.production

# Fully qualified (always works)
curl web-service.production.svc.cluster.local
```

### 4.2 Змінні середовища

Kubernetes впроваджує інформацію про сервіс у поди:

```bash
# Environment variables for service "web-service"
WEB_SERVICE_SERVICE_HOST=10.96.45.123
WEB_SERVICE_SERVICE_PORT=80

# Note: Only works for services created BEFORE the pod
```

### 4.3 Пошук Сервісів

```bash
# List services
k get services
k get svc                    # Short form

# Get service details
k describe svc web-service

# Get service endpoints
k get endpoints web-service

# Get service YAML
k get svc web-service -o yaml

# Find service ClusterIP
k get svc web-service -o jsonpath='{.spec.clusterIP}'
```

---

## Частина 5: Селектори та Ендпоінти (Endpoints)

### 5.1 Як працюють Селектори

```yaml
# Service selector MUST match pod labels exactly
# Service:
spec:
  selector:
    app: web
    tier: frontend

# Pod (will be selected):
metadata:
  labels:
    app: web
    tier: frontend
    version: v2          # Extra labels OK

# Pod (will NOT be selected - missing tier):
metadata:
  labels:
    app: web
    version: v2
```

### 5.2 Ендпоінти

Ендпоінти автоматично створюються, коли поди відповідають селектору:

```bash
# View endpoints (pod IPs backing the service)
k get endpoints web-service
# NAME          ENDPOINTS                         AGE
# web-service   10.244.1.5:8080,10.244.2.8:8080   5m

# Detailed endpoint info
k describe endpoints web-service
```

### 5.3 Сервіс без Селектора

Створення сервісу, який вказує на ручні ендпоінти:

```yaml
# Service without selector
apiVersion: v1
kind: Service
metadata:
  name: external-service
spec:
  ports:
  - port: 80
    targetPort: 80
---
# Manual endpoints
apiVersion: v1
kind: Endpoints
metadata:
  name: external-service    # Must match service name
subsets:
- addresses:
  - ip: 192.168.1.100      # External IP
  - ip: 192.168.1.101
  ports:
  - port: 80
```

Варіант використання: Вказування на зовнішні бази даних або сервіси поза кластером.

---

## Частина 6: Налагодження Сервісів

### 6.1 Робочий процес налагодження Сервісу

```
Сервіс не працює?
    │
    ├── kubectl get svc (перевірити існування сервісу)
    │       │
    │       └── Перевірити TYPE, CLUSTER-IP, EXTERNAL-IP, PORT
    │
    ├── kubectl get endpoints <svc> (перевірити ендпоінти)
    │       │
    │       ├── Немає ендпоінтів? → Селектор не відповідає подам
    │       │                       Перевірити мітки подів
    │       │
    │       └── Ендпоінти існують? → Поди не відповідають
    │                                Перевірити стан подів
    │
    ├── kubectl describe svc <svc> (перевірити селектор)
    │       │
    │       └── Переконатися, що селектор відповідає міткам подів
    │
    └── Протестувати зсередини кластера:
        kubectl run test --rm -it --image=busybox -- wget -qO- <svc>
```

### 6.2 Типові проблеми Сервісів

| Симптом | Причина | Рішення |
|---------|-------|----------|
| Немає ендпоінтів | Селектор не відповідає подам | Виправити селектор або мітки подів |
| З'єднання відхилено | Под не слухає на targetPort | Перевірити конфігурацію порту пода |
| Тайм-аут | Под не працює або постійно перезапускається (crashlooping) | Спочатку налагодити проблеми з подом |
| NodePort недоступний | Брандмауер блокує порт | Перевірити правила брандмауера вузла |
| Неправильний тип сервісу | Використання ClusterIP для зовнішнього доступу | Змінити на NodePort/LoadBalancer |

### 6.3 Команди налагодження

```bash
# Check service and endpoints
k get svc,endpoints

# Verify selector matches pods
k get pods --selector=app=web

# Test connectivity from within cluster
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://web-service

# Test with curl
k run test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s http://web-service

# Check DNS resolution
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web-service

# Check port on pod directly
k exec <pod> -- netstat -tlnp
```

> **Бойова історія: Невідповідність селектора**
>
> Розробник витратив години на налагодження, чому його сервіс не мав ендпоінтів. Деплоймент використовував `app: web-app`, але селектор сервісу був `app: webapp` (без дефіса). Різниця в один символ = нульове підключення. Завжди копіюйте селектори!

---

## Частина 7: Прив'язка сеансу Сервісу (Session Affinity)

### 7.1 Опції Session Affinity

```yaml
# Sticky sessions - route same client to same pod
apiVersion: v1
kind: Service
metadata:
  name: sticky-service
spec:
  selector:
    app: web
  sessionAffinity: ClientIP      # None (default) or ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800      # 3 hours (default)
  ports:
  - port: 80
```

### 7.2 Коли використовувати Session Affinity

| Сценарій | Використовувати прив'язку? |
|----------|---------------|
| API без стану (Stateless) | Ні (за замовчуванням) |
| Кошик покупок у пам'яті пода | Так (але краще: використовувати Redis) |
| З'єднання WebSocket | Так |
| Сеанси автентифікації в пам'яті | Так (але краще: зовнішнє сховище) |

---

## Розподіл трафіку (Traffic Distribution) (K8s 1.35+)

Kubernetes 1.35 перевів розподіл трафіку **PreferSameNode** у статус GA (загальна доступність), що дає вам точний контроль над тим, куди маршрутизується трафік сервісу:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: latency-sensitive
spec:
  selector:
    app: cache
  ports:
  - port: 6379
  trafficDistribution: PreferSameNode  # Route to local node first
```

| Значення | Поведінка |
|-------|----------|
| `PreferSameNode` | Суворо надавати перевагу кінцевим точкам на тому самому вузлі, повертатися до віддалених (GA у 1.35) |
| `PreferClose` | Надавати перевагу топологічно близьким кінцевим точкам — в одній зоні під час використання топологічно-обізнаної маршрутизації |

Це особливо корисно для робочих навантажень, чутливих до затримок, таких як кеші, sidecar-контейнери та локальні сервіси вузлів.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|----------|
| Невідповідність селектора | Сервіс не має ендпоінтів | Переконайтеся, що селектор точно відповідає міткам подів |
| Плутанина між Port та TargetPort | З'єднання відхилено | Port = сервіс, TargetPort = под |
| Відсутній тип сервісу | Немає доступу ззовні | Вкажіть NodePort або LoadBalancer |
| Використання ClusterIP зовні | Тайм-аут з'єднання | ClusterIP є лише внутрішнім |
| Забули Простір імен | Сервіс не знайдено | Використовуйте FQDN для запитів між просторами імен |

---

## Тест

1. **У чому різниця між `port` та `targetPort` у сервісі?**
   <details>
   <summary>Відповідь</summary>
   `port` — це порт, на якому слухає сервіс. `targetPort` — це порт на поді, який отримує трафік. Приклад: Сервіс слухає на 80, пересилає на 8080 пода.
   </details>

2. **Сервіс показує "No endpoints" (Немає ендпоінтів). Що є найімовірнішою причиною?**
   <details>
   <summary>Відповідь</summary>
   Селектор сервісу не відповідає міткам жодного запущеного пода. Перевірте, чи селектор точно збігається з мітками подів, використовуючи `k get pods --show-labels`.
   </details>

3. **Як отримати доступ до сервісу ClusterIP з-поза меж кластера?**
   <details>
   <summary>Відповідь</summary>
   Прямо ніяк. ClusterIP призначений лише для внутрішнього використання. Вам потрібно або:
   - Змінити тип на NodePort або LoadBalancer
   - Використати `kubectl port-forward`
   - Отримати доступ через Інгрес (Ingress) або Gateway
   </details>

4. **Яка команда відкриває доступ до деплойменту як до сервісу NodePort на порту 80?**
   <details>
   <summary>Відповідь</summary>
   `k expose deployment <name> --port=80 --type=NodePort`

   NodePort буде призначено автоматично (30000-32767), якщо не вказано інше.
   </details>

5. **Яке DNS-ім'я може використовувати под у просторі імен "prod", щоб дістатися до сервісу "api" у просторі імен "staging"?**
   <details>
   <summary>Відповідь</summary>
   `api.staging` або повне FQDN `api.staging.svc.cluster.local`
   </details>

---

## Практичні вправи

**Завдання**: Створити та налагодити сервіси для багаторівневого додатку.

**Кроки**:

1. **Створити деплоймент бекенду**:
```bash
k create deployment backend --image=nginx --replicas=2
k set env deployment/backend APP=backend
```

2. **Правильно призначити мітки подам**:
```bash
k label deployment backend tier=backend
```

3. **Відкрити доступ до бекенду як ClusterIP**:
```bash
k expose deployment backend --port=80 --name=backend-svc
```

4. **Перевірити сервіс**:
```bash
k get svc backend-svc
k get endpoints backend-svc
```

5. **Створити деплоймент фронтенду**:
```bash
k create deployment frontend --image=nginx --replicas=2
```

6. **Відкрити доступ до фронтенду як NodePort**:
```bash
k expose deployment frontend --port=80 --type=NodePort --name=frontend-svc
```

7. **Протестувати внутрішнє підключення**:
```bash
# From a test pod, reach the backend service
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://backend-svc
```

8. **Протестувати між просторами імен**:
```bash
# Create another namespace and test
k create namespace other
k run test -n other --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://backend-svc.default
```

9. **Налагодити зламаний сервіс**:
```bash
# Create a service with wrong selector
k create service clusterip broken-svc --tcp=80:80
# Check endpoints (should be empty)
k get endpoints broken-svc
# Fix by creating proper service
k delete svc broken-svc
k expose deployment backend --port=80 --name=broken-svc --selector=app=backend
k get endpoints broken-svc
```

10. **Очищення**:
```bash
k delete deployment frontend backend
k delete svc backend-svc frontend-svc broken-svc
k delete namespace other
```

**Критерії успіху**:
- [ ] Вміє створювати сервіси ClusterIP та NodePort
- [ ] Розуміє різницю між port та targetPort
- [ ] Вміє налагоджувати сервіси без ендпоінтів
- [ ] Може отримувати доступ до сервісів між просторами імен
- [ ] Розуміє, коли використовувати кожен тип сервісу

---

## Практичні вправи

### Вправа 1: Швидкість створення Сервісу (Ціль: 2 хвилини)

Створіть сервіси для деплойменту якомога швидше:

```bash
# Setup
k create deployment drill-app --image=nginx --replicas=2

# Create ClusterIP service
k expose deployment drill-app --port=80 --name=drill-clusterip

# Create NodePort service
k expose deployment drill-app --port=80 --type=NodePort --name=drill-nodeport

# Verify both
k get svc drill-clusterip drill-nodeport

# Generate YAML
k expose deployment drill-app --port=80 --dry-run=client -o yaml > svc.yaml

# Cleanup
k delete deployment drill-app
k delete svc drill-clusterip drill-nodeport
rm svc.yaml
```

### Вправа 2: Сервіс з кількома портами (Ціль: 3 хвилини)

```bash
# Create deployment
k create deployment multi-port --image=nginx

# Create multi-port service from YAML
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: multi-port-svc
spec:
  selector:
    app: multi-port
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: https
    port: 443
    targetPort: 443
EOF

# Verify
k describe svc multi-port-svc

# Cleanup
k delete deployment multi-port
k delete svc multi-port-svc
```

### Вправа 3: Виявлення Сервісів (Ціль: 3 хвилини)

```bash
# Create service
k create deployment web --image=nginx
k expose deployment web --port=80

# Test DNS resolution
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web

# Test full FQDN
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default.svc.cluster.local

# Test connectivity
k run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s http://web

# Cleanup
k delete deployment web
k delete svc web
```

### Вправа 4: Налагодження Ендпоінтів (Ціль: 4 хвилини)

```bash
# Create deployment with specific labels
k create deployment endpoint-test --image=nginx
k label deployment endpoint-test tier=web --overwrite

# Create service with WRONG selector (intentionally broken)
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: broken-endpoints
spec:
  selector:
    app: wrong-label    # This won't match!
  ports:
  - port: 80
EOF

# Observe: no endpoints
k get endpoints broken-endpoints
# ENDPOINTS: <none>

# Debug: check what selector should be
k get pods --show-labels

# Fix: delete and recreate with correct selector
k delete svc broken-endpoints
k expose deployment endpoint-test --port=80 --name=fixed-endpoints

# Verify: endpoints exist now
k get endpoints fixed-endpoints

# Cleanup
k delete deployment endpoint-test
k delete svc fixed-endpoints
```

### Вправа 5: Доступ між Просторами імен (Ціль: 3 хвилини)

```bash
# Create service in default namespace
k create deployment app --image=nginx
k expose deployment app --port=80

# Create other namespace
k create namespace testing

# Access from other namespace - short form
k run test -n testing --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://app.default

# Access with FQDN
k run test -n testing --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://app.default.svc.cluster.local

# Cleanup
k delete deployment app
k delete svc app
k delete namespace testing
```

### Вправа 6: Специфічний порт NodePort (Ціль: 3 хвилини)

```bash
# Create deployment
k create deployment nodeport-test --image=nginx

# Create NodePort with specific port
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: specific-nodeport
spec:
  type: NodePort
  selector:
    app: nodeport-test
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080    # Specific port
EOF

# Verify port
k get svc specific-nodeport
# Should show 80:30080/TCP

# Cleanup
k delete deployment nodeport-test
k delete svc specific-nodeport
```

### Вправа 7: Сервіс ExternalName (Ціль: 2 хвилини)

```bash
# Create ExternalName service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: external-api
spec:
  type: ExternalName
  externalName: api.example.com
EOF

# Check the service (no ClusterIP!)
k get svc external-api
# Note: CLUSTER-IP shows as <none>

# Test DNS resolution
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup external-api
# Shows CNAME to api.example.com

# Cleanup
k delete svc external-api
```

### Вправа 8: Виклик - Повний робочий процес Сервісу

Без підглядання у рішення:

1. Створіть деплоймент `challenge-app` з nginx, 3 репліки
2. Відкрийте доступ як сервіс ClusterIP на порту 80
3. Перевірте, чи ендпоінти показують 3 IP-адреси подів
4. Масштабуйте деплоймент до 5 реплік
5. Перевірте, чи ендпоінти тепер показують 5 IP-адрес подів
6. Змініть тип сервісу на NodePort
7. Отримайте номер NodePort
8. Очистіть усе

```bash
# YOUR TASK: Complete in under 5 minutes
```

<details>
<summary>Відповідь</summary>

```bash
# 1. Create deployment
k create deployment challenge-app --image=nginx --replicas=3

# 2. Expose as ClusterIP
k expose deployment challenge-app --port=80

# 3. Verify 3 endpoints
k get endpoints challenge-app

# 4. Scale to 5
k scale deployment challenge-app --replicas=5

# 5. Verify 5 endpoints
k get endpoints challenge-app

# 6. Change to NodePort (delete and recreate)
k delete svc challenge-app
k expose deployment challenge-app --port=80 --type=NodePort

# 7. Get NodePort
k get svc challenge-app -o jsonpath='{.spec.ports[0].nodePort}'

# 8. Cleanup
k delete deployment challenge-app
k delete svc challenge-app
```

</details>

---

## Наступний модуль

[Модуль 3.2: Ендпоінти та EndpointSlices](module-3.2-endpoints/) - Глибоке занурення в те, як сервіси відстежують поди.
