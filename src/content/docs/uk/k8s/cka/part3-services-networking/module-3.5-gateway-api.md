---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 3.5: Gateway API"
slug: uk/k8s/cka/part3-services-networking/module-3.5-gateway-api
sidebar: 
  order: 6
lab: 
  id: cka-3.5-gateway-api
  url: https://killercoda.com/kubedojo/scenario/cka-3.5-gateway-api
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — тема іспиту CKA
>
> **Час на виконання**: 45–55 хвилин
>
> **Передумови**: Модуль 3.4 (Ingress)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** ресурси Gateway, HTTPRoute та GRPCRoute для просунутого керування трафіком
- **Порівняти** Gateway API з Ingress та пояснити, коли використовувати кожен
- **Налаштувати** розділення трафіку, маршрутизацію на основі заголовків та дзеркалювання запитів
- **Пояснити** рольову модель Gateway API (провайдер інфраструктури, оператор кластера, розробник застосунку)

---

## Чому цей модуль важливий

Gateway API — це **поточний стандарт мережевої взаємодії в Kubernetes**. Він усуває обмеження Ingress, надаючи багатші можливості маршрутизації, рольовий дизайн та підтримку протоколів, окрім HTTP. Іспит CKA включає Gateway API як ключову компетенцію: «Use the Gateway API to manage Ingress traffic».

Оскільки **контролер ingress-nginx припинено** (31 березня 2026 року), а Gateway API перебуває у статусі GA з жовтня 2023 року, Gateway API є рекомендованим підходом для всіх нових розгортань. Кожен основний контролер ingress тепер підтримує його: Envoy Gateway, Istio, Cilium, Traefik, Kong та NGINX Gateway Fabric.

> **Примітка щодо міграції**: Якщо ви керуєте наявними ресурсами Ingress, інструмент **Ingress2Gateway 1.0** (випущений у березні 2026 року) конвертує ресурси Ingress та понад 30 анотацій ingress-nginx у еквіваленти Gateway API. Див. [офіційний посібник з міграції](https://gateway-api.sigs.k8s.io/guides/getting-started/migrating-from-ingress/).

> **Аналогія з аеропортом**
>
> Якщо Ingress — це один термінал аеропорту з однією стійкою реєстрації, то Gateway API — це сучасний аеропорт з окремими структурами: оператори інфраструктури керують злітно-посадковими смугами (Gateway), авіакомпанії керують своїми стійками реєстрації (HTTPRoute), а служба безпеки відповідає за політики (policies). Кожна роль має чіткі обов'язки.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Розуміти різницю між Ingress та Gateway API
- Створювати ресурси Gateway та HTTPRoute
- Налаштовувати маршрутизацію за шляхом та заголовками
- Розуміти рольову модель
- Використовувати Gateway API для керування трафіком

---

## Чи знали ви?

- **Gateway API — це офіційний стандарт**: Kubernetes SIG Network розробила Gateway API для усунення обмежень Ingress. Оскільки ingress-nginx припинено, а всі основні контролери підтримують Gateway API, він є виробничим стандартом.

- **Підтримка багатьох протоколів**: На відміну від Ingress (лише HTTP), Gateway API нативно підтримує TCP, UDP, TLS та gRPC.

- **Рольовий дизайн**: Gateway API розділяє зони відповідальності між постачальниками інфраструктури, операторами кластерів та розробниками застосунків.

- **Ingress2Gateway 1.0**: Випущений у березні 2026 року, цей офіційний інструмент міграції конвертує ресурси Ingress (включно з понад 30 анотаціями ingress-nginx) у Gateway API. Підтримує вивід для Envoy Gateway, kgateway та інших.

---

## Частина 1: Gateway API проти Ingress

### 1.1 Ключові відмінності

| Аспект | Ingress | Gateway API |
|--------|---------|-------------|
| Ресурси | 1 (Ingress) | Декілька (Gateway, HTTPRoute тощо) |
| Протоколи | HTTP/HTTPS | HTTP, HTTPS, TCP, UDP, TLS, gRPC |
| Рольова модель | Один ресурс | Розділення за ролями |
| Розширюваність | Анотації (непортативні) | Типізовані розширення (портативні) |
| Маршрутизація за заголовками | Залежить від контролера | Нативна підтримка |
| Розподіл трафіку | Залежить від контролера | Нативна підтримка |
| Статус | Stable | GA з v1.0 (жовт. 2023) |

### 1.2 Ієрархія ресурсів

```
┌────────────────────────────────────────────────────────────────┐
│                   Gateway API Resource Model                    │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                   GatewayClass                           │  │
│   │   (Визначає контролер — як IngressClass)                │  │
│   │   Створює: постачальник інфраструктури                   │  │
│   └─────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                      Gateway                             │  │
│   │   (Інфраструктура — слухачі, адреси)                    │  │
│   │   Створює: оператор кластера                            │  │
│   └─────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│               ┌─────────────┼─────────────┐                    │
│               │             │             │                    │
│               ▼             ▼             ▼                    │
│         ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│         │HTTPRoute │  │TCPRoute  │  │GRPCRoute │             │
│         │          │  │          │  │          │             │
│         │ Команда  │  │ Команда  │  │ Команда  │             │
│         │ застос.  │  │ застос.  │  │ застос.  │             │
│         └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│              │             │             │                    │
│              ▼             ▼             ▼                    │
│         ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│         │ Сервіси  │  │ Сервіси  │  │ Сервіси  │             │
│         └──────────┘  └──────────┘  └──────────┘             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Рольовий дизайн

| Роль | Ресурси | Обов'язки |
|------|---------|-----------|
| **Постачальник інфраструктури** | GatewayClass | Визначає спосіб реалізації шлюзів |
| **Оператор кластера** | Gateway, ReferenceGrant | Налаштовує інфраструктуру, мережеві політики |
| **Розробник застосунків** | HTTPRoute, TCPRoute | Визначає правила маршрутизації для застосунків |

---

## Частина 2: Встановлення Gateway API

### 2.1 Встановлення CRD

```bash
# Install Gateway API CRDs (required first)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# Verify CRDs are installed
kubectl get crd | grep gateway
# gatewayclasses.gateway.networking.k8s.io
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
```

### 2.2 Варіанти контролерів Gateway

| Контролер | Тип | Найкраще підходить для |
|-----------|-----|------------------------|
| **Istio** | Service mesh | Повнофункціональний, для користувачів service mesh |
| **Contour** | Автономний | Простий, швидкий |
| **nginx** | Автономний | Знайомий користувачам nginx |
| **Cilium** | Інтегрований з CNI | Продуктивність eBPF |
| **Traefik** | Автономний | Динамічна конфігурація |

### 2.3 Встановлення контролера Istio Gateway (приклад)

```bash
# Install Istio with Gateway API support
istioctl install --set profile=minimal

# Or for quick testing with kind/minikube, use Contour:
kubectl apply -f https://projectcontour.io/quickstart/contour-gateway.yaml
```

---

## Частина 3: GatewayClass та Gateway

### 3.1 GatewayClass

```yaml
# GatewayClass - created by infrastructure provider
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: example-gateway-class
spec:
  controllerName: example.io/gateway-controller
  description: "Example Gateway controller"
```

```bash
# List GatewayClasses
k get gatewayclass
k get gc               # Short form
```

### 3.2 Gateway

```yaml
# Gateway - created by cluster operator
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-gateway
  namespace: default
spec:
  gatewayClassName: example-gateway-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All        # Allow routes from all namespaces
```

### 3.3 Gateway з кількома слухачами

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: multi-listener-gateway
spec:
  gatewayClassName: example-gateway-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    hostname: "*.example.com"
    allowedRoutes:
      namespaces:
        from: All
  - name: https
    protocol: HTTPS
    port: 443
    hostname: "*.example.com"
    tls:
      mode: Terminate
      certificateRefs:
      - name: example-tls
        kind: Secret
    allowedRoutes:
      namespaces:
        from: Same       # Only routes from same namespace
```

### 3.4 Перевірка статусу Gateway

```bash
# Get gateway
k get gateway
k get gtw              # Short form

# Describe gateway (check conditions)
k describe gateway example-gateway

# Check if gateway is ready
k get gateway example-gateway -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

---

## Частина 4: HTTPRoute

### 4.1 Простий HTTPRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: simple-route
spec:
  parentRefs:
  - name: example-gateway       # Attach to this Gateway
  rules:
  - backendRefs:
    - name: web-service         # Target service
      port: 80
```

### 4.2 Маршрутизація за шляхом

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: path-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-service
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: web-service
      port: 80
```

### 4.3 Маршрутизація за хостом

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: host-route
spec:
  parentRefs:
  - name: example-gateway
  hostnames:
  - "api.example.com"
  - "api.example.org"
  rules:
  - backendRefs:
    - name: api-service
      port: 80
```

### 4.4 Маршрутизація за заголовками

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: header-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - headers:
      - name: X-Version
        value: v2
    backendRefs:
    - name: api-v2
      port: 80
  - matches:
    - headers:
      - name: X-Version
        value: v1
    backendRefs:
    - name: api-v1
      port: 80
```

### 4.5 Розподіл трафіку (Canary/Blue-Green)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: canary-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - backendRefs:
    - name: api-stable
      port: 80
      weight: 90           # 90% to stable
    - name: api-canary
      port: 80
      weight: 10           # 10% to canary
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Розподіл трафіку                              │
│                                                                 │
│   Вхідний трафік (100%)                                        │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    HTTPRoute                             │  │
│   │                                                          │  │
│   │   weight: 90          weight: 10                        │  │
│   │      │                    │                              │  │
│   │      ▼                    ▼                              │  │
│   │  ┌────────┐          ┌────────┐                         │  │
│   │  │ Stable │          │ Canary │                         │  │
│   │  │  (90%) │          │  (10%) │                         │  │
│   │  └────────┘          └────────┘                         │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Частина 5: Фільтри HTTPRoute

### 5.1 Модифікація заголовків запиту

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: header-filter-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
        - name: X-Custom-Header
          value: "added-by-gateway"
        remove:
        - X-Unwanted-Header
    backendRefs:
    - name: web-service
      port: 80
```

### 5.2 Перезапис URL

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: rewrite-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /old-api
    filters:
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /new-api
    backendRefs:
    - name: api-service
      port: 80
```

### 5.3 Перенаправлення запиту

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: redirect-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /old-path
    filters:
    - type: RequestRedirect
      requestRedirect:
        scheme: https
        hostname: new.example.com
        statusCode: 301
```

---

## Частина 6: Маршрутизація між просторами імен

### 6.1 ReferenceGrant

Дозволяє маршрутам в одному просторі імен посилатися на сервіси в іншому:

```yaml
# In the target namespace (where the service lives)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: ReferenceGrant
metadata:
  name: allow-routes-from-default
  namespace: backend-ns
spec:
  from:
  - group: gateway.networking.k8s.io
    kind: HTTPRoute
    namespace: default        # Allow routes from default namespace
  to:
  - group: ""
    kind: Service             # Allow referencing services
```

```yaml
# HTTPRoute in default namespace can now reference backend-ns service
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: cross-ns-route
  namespace: default
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - backendRefs:
    - name: backend-service
      namespace: backend-ns    # Cross-namespace reference
      port: 80
```

---

## Частина 7: Налаштування TLS

### 7.1 Gateway з термінацією TLS

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: tls-gateway
spec:
  gatewayClassName: example-gateway-class
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    hostname: secure.example.com
    tls:
      mode: Terminate
      certificateRefs:
      - name: secure-tls        # TLS secret
        kind: Secret
    allowedRoutes:
      namespaces:
        from: All
```

### 7.2 Режими TLS

| Режим | Поведінка |
|-------|-----------|
| `Terminate` | Gateway термінує TLS, надсилає HTTP до бекендів |
| `Passthrough` | Gateway пропускає TLS наскрізь, бекенд виконує термінацію |

---

## Частина 8: Діагностика Gateway API

### 8.1 Послідовність діагностики

```
Проблема з Gateway API?
    │
    ├── kubectl get gatewayclass (перевірити контролер)
    │
    ├── kubectl get gateway (перевірити статус)
    │       │
    │       └── Not Ready? → Перевірити conditions
    │
    ├── kubectl get httproute (перевірити чи прикріплено)
    │       │
    │       └── Не прикріплено? → Перевірити parentRefs
    │
    ├── kubectl describe httproute (перевірити conditions)
    │       │
    │       └── Помилки? → Виправити конфігурацію
    │
    └── Перевірити бекенд-сервіси
        kubectl get svc,endpoints
```

### 8.2 Основні команди

```bash
# List all Gateway API resources
k get gatewayclass,gateway,httproute

# Check Gateway status
k describe gateway example-gateway

# Check HTTPRoute status
k describe httproute my-route

# Get HTTPRoute conditions
k get httproute my-route -o jsonpath='{.status.parents[0].conditions}'
```

### 8.3 Типові проблеми

| Симптом | Причина | Рішення |
|---------|---------|---------|
| Gateway не Ready | Немає контролера | Встановити контролер Gateway |
| HTTPRoute не прикріплено | Неправильні parentRefs | Перевірити імʼя/простір імен Gateway |
| Помилки 404 | Немає відповідного правила | Перевірити конфігурацію шляху/хоста |
| Міжпросторова маршрутизація не працює | Відсутній ReferenceGrant | Створити ReferenceGrant |

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Відсутні CRD | Ресурси не розпізнаються | Спочатку встановити CRD Gateway API |
| Неправильний gatewayClassName | Gateway не обробляється | Точно вказати імʼя GatewayClass |
| Відсутні parentRefs | Маршрут не прикріплено | Додати parentRefs до HTTPRoute |
| Невідповідність просторів імен | Міжпросторова маршрутизація не працює | Створити ReferenceGrant |
| Неправильний тип шляху | Маршрути не збігаються | Використовувати PathPrefix, Exact або RegularExpression |

---

## Тест

1. **Яка основна різниця між Ingress та Gateway API?**
   <details>
   <summary>Відповідь</summary>
   Gateway API використовує кілька ресурсів з рольовим розділенням (GatewayClass, Gateway, HTTPRoute) і нативно підтримує багато протоколів. Ingress використовує один ресурс і покладається на анотації для розширених можливостей.
   </details>

2. **Хто зазвичай створює ресурс Gateway?**
   <details>
   <summary>Відповідь</summary>
   Оператор кластера створює Gateway. Постачальники інфраструктури створюють GatewayClass, а розробники застосунків створюють HTTPRoute.
   </details>

3. **Як налаштувати розподіл трафіку (90/10) у Gateway API?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте `weight` у backendRefs:
   ```yaml
   backendRefs:
   - name: stable
     weight: 90
   - name: canary
     weight: 10
   ```
   </details>

4. **Для чого використовується ReferenceGrant?**
   <details>
   <summary>Відповідь</summary>
   ReferenceGrant дозволяє ресурсам в одному просторі імен посилатися на ресурси в іншому просторі імен. Наприклад, дозволяє HTTPRoute у `default` маршрутизувати до Сервісу у `backend-ns`.
   </details>

5. **Як працює маршрутизація за заголовками у Gateway API?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте `matches.headers` у правилах HTTPRoute:
   ```yaml
   matches:
   - headers:
     - name: X-Version
       value: v2
   ```
   Це спрямовує запити з відповідними заголовками до конкретних бекендів.
   </details>

---

## Практична вправа

**Завдання**: Створити повну конфігурацію Gateway API з маршрутизацією.

**Кроки**:

1. **Встановити CRD Gateway API** (якщо не встановлено):
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

2. **Створити бекенд-сервіси**:
```bash
k create deployment api --image=nginx
k create deployment web --image=nginx
k expose deployment api --port=80
k expose deployment web --port=80
```

3. **Створити GatewayClass** (імітація — у реальному кластері контролер надає це):
```bash
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: example-class
spec:
  controllerName: example.io/gateway-controller
EOF
```

4. **Створити Gateway**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-gateway
spec:
  gatewayClassName: example-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

k get gateway
k describe gateway example-gateway
```

5. **Створити HTTPRoute з маршрутизацією за шляхом**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: app-routes
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: web
      port: 80
EOF

k get httproute
k describe httproute app-routes
```

6. **Створити HTTPRoute з розподілом трафіку**:
```bash
# Create canary deployment
k create deployment api-canary --image=nginx

k expose deployment api-canary --port=80

cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: canary-route
spec:
  parentRefs:
  - name: example-gateway
  hostnames:
  - "canary.example.com"
  rules:
  - backendRefs:
    - name: api
      port: 80
      weight: 90
    - name: api-canary
      port: 80
      weight: 10
EOF
```

7. **Переглянути всі ресурси**:
```bash
k get gatewayclass,gateway,httproute
```

8. **Очищення**:
```bash
k delete httproute app-routes canary-route
k delete gateway example-gateway
k delete gatewayclass example-class
k delete deployment api web api-canary
k delete svc api web api-canary
```

**Критерії успіху**:
- [ ] Розуміння ієрархії ресурсів Gateway API
- [ ] Вміння створювати Gateway та HTTPRoute
- [ ] Вміння налаштовувати маршрутизацію за шляхом
- [ ] Вміння налаштовувати розподіл трафіку
- [ ] Розуміння рольової моделі

---

## Практичні вправи

### Вправа 1: Перевірка встановлення Gateway API (Ціль: 2 хвилини)

```bash
# Check CRDs
k get crd | grep gateway

# List GatewayClasses
k get gatewayclass

# List Gateways
k get gateway -A

# List HTTPRoutes
k get httproute -A
```

### Вправа 2: Створення базового Gateway (Ціль: 3 хвилини)

```bash
# Create GatewayClass
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: drill-class
spec:
  controllerName: drill.io/controller
EOF

# Create Gateway
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: drill-gateway
spec:
  gatewayClassName: drill-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

# Verify
k get gateway drill-gateway
k describe gateway drill-gateway

# Cleanup
k delete gateway drill-gateway
k delete gatewayclass drill-class
```

### Вправа 3: HTTPRoute з маршрутизацією за шляхом (Ціль: 4 хвилини)

```bash
# Create services
k create deployment svc1 --image=nginx
k create deployment svc2 --image=nginx
k expose deployment svc1 --port=80
k expose deployment svc2 --port=80

# Create Gateway and GatewayClass
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: path-class
spec:
  controllerName: path.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: path-gateway
spec:
  gatewayClassName: path-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

# Create path-based HTTPRoute
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: path-route
spec:
  parentRefs:
  - name: path-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /service1
    backendRefs:
    - name: svc1
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /service2
    backendRefs:
    - name: svc2
      port: 80
EOF

# Verify
k describe httproute path-route

# Cleanup
k delete httproute path-route
k delete gateway path-gateway
k delete gatewayclass path-class
k delete deployment svc1 svc2
k delete svc svc1 svc2
```

### Вправа 4: Розподіл трафіку (Ціль: 4 хвилини)

```bash
# Create stable and canary
k create deployment stable --image=nginx
k create deployment canary --image=nginx
k expose deployment stable --port=80
k expose deployment canary --port=80

# Create Gateway resources
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: split-class
spec:
  controllerName: split.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: split-gateway
spec:
  gatewayClassName: split-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: split-route
spec:
  parentRefs:
  - name: split-gateway
  rules:
  - backendRefs:
    - name: stable
      port: 80
      weight: 80
    - name: canary
      port: 80
      weight: 20
EOF

# Verify
k describe httproute split-route

# Cleanup
k delete httproute split-route
k delete gateway split-gateway
k delete gatewayclass split-class
k delete deployment stable canary
k delete svc stable canary
```

### Вправа 5: Маршрутизація за заголовками (Ціль: 4 хвилини)

```bash
# Create versioned services
k create deployment v1 --image=nginx
k create deployment v2 --image=nginx
k expose deployment v1 --port=80
k expose deployment v2 --port=80

# Create Gateway resources with header routing
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: header-class
spec:
  controllerName: header.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: header-gateway
spec:
  gatewayClassName: header-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: header-route
spec:
  parentRefs:
  - name: header-gateway
  rules:
  - matches:
    - headers:
      - name: X-Version
        value: v2
    backendRefs:
    - name: v2
      port: 80
  - matches:
    - headers:
      - name: X-Version
        value: v1
    backendRefs:
    - name: v1
      port: 80
EOF

# Verify
k describe httproute header-route

# Cleanup
k delete httproute header-route
k delete gateway header-gateway
k delete gatewayclass header-class
k delete deployment v1 v2
k delete svc v1 v2
```

### Вправа 6: Маршрутизація за хостом (Ціль: 4 хвилини)

```bash
# Create services
k create deployment api --image=nginx
k create deployment web --image=nginx
k expose deployment api --port=80
k expose deployment web --port=80

# Create Gateway with host routing
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: host-class
spec:
  controllerName: host.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: host-gateway
spec:
  gatewayClassName: host-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
spec:
  parentRefs:
  - name: host-gateway
  hostnames:
  - "api.example.com"
  rules:
  - backendRefs:
    - name: api
      port: 80
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web-route
spec:
  parentRefs:
  - name: host-gateway
  hostnames:
  - "www.example.com"
  rules:
  - backendRefs:
    - name: web
      port: 80
EOF

# Verify
k get httproute

# Cleanup
k delete httproute api-route web-route
k delete gateway host-gateway
k delete gatewayclass host-class
k delete deployment api web
k delete svc api web
```

### Вправа 7: Виклик — повна конфігурація Gateway API

Без підглядання у рішення:

1. Встановити CRD Gateway API (за потреби)
2. Створити GatewayClass з імʼям `challenge-class`
3. Створити Gateway з імʼям `challenge-gateway` на порту 80
4. Створити розгортання: `frontend`, `backend`, `admin`
5. Створити HTTPRoutes:
   - `/admin` → сервіс admin
   - `/api` → сервіс backend
   - `/` → сервіс frontend
6. Перевірити, що всі ресурси створені
7. Очистити все

```bash
# YOUR TASK: Complete in under 8 minutes
```

<details>
<summary>Рішення</summary>

```bash
# 1. CRDs (if needed)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# 2-3. GatewayClass and Gateway
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: challenge-class
spec:
  controllerName: challenge.io/controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: challenge-gateway
spec:
  gatewayClassName: challenge-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF

# 4. Create deployments and services
k create deployment frontend --image=nginx
k create deployment backend --image=nginx
k create deployment admin --image=nginx
k expose deployment frontend --port=80
k expose deployment backend --port=80
k expose deployment admin --port=80

# 5. Create HTTPRoutes
cat << 'EOF' | k apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: challenge-routes
spec:
  parentRefs:
  - name: challenge-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /admin
    backendRefs:
    - name: admin
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: backend
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: frontend
      port: 80
EOF

# 6. Verify
k get gatewayclass,gateway,httproute

# 7. Cleanup
k delete httproute challenge-routes
k delete gateway challenge-gateway
k delete gatewayclass challenge-class
k delete deployment frontend backend admin
k delete svc frontend backend admin
```

</details>

---

## Наступний модуль

[Модуль 3.6: Network Policies](module-3.6-network-policies/) — Контроль взаємодії між подами.
