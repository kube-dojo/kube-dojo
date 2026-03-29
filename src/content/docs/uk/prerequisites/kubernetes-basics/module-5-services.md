---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 5: \u0421\u0435\u0440\u0432\u0456\u0441\u0438 \u2014 \u0441\u0442\u0430\u0431\u0456\u043b\u044c\u043d\u0430 \u043c\u0435\u0440\u0435\u0436\u0430"
sidebar:
  order: 6
---
> **Складність**: `[MEDIUM]` — основна концепція мережі
>
> **Час на виконання**: 35–40 хвилин
>
> **Передумови**: Модуль 4 (Деплойменти)

---

## Чому цей модуль важливий

Поди ефемерні — вони з'являються й зникають, кожен з іншою IP-адресою. Сервіси забезпечують стабільну мережу: фіксовану IP-адресу та DNS-ім'я, які маршрутизують трафік до ваших Подів, незалежно від їхньої кількості чи частоти змін.

---

## Проблема, яку розв'язують Сервіси

```
┌─────────────────────────────────────────────────────────────┐
│              БЕЗ СЕРВІСІВ                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IP Подів постійно змінюються:                              │
│                                                             │
│  Час 0:  [Под: 10.1.0.5]                                   │
│  Час 1:  Под впав, створено новий                           │
│  Час 2:  [Под: 10.1.0.9]   ← Інша IP-адреса!              │
│                                                             │
│  Проблема: Як інші застосунки знайдуть ваш Под?            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│              З СЕРВІСАМИ                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Сервіс: my-app.default.svc.cluster.local                  │
│           ClusterIP: 10.96.0.100 (стабільна!)               │
│                    │                                        │
│           ┌────────┴────────┐                              │
│           ▼                 ▼                               │
│  [Под: 10.1.0.5]   [Под: 10.1.0.9]                         │
│                                                             │
│  Сервіс маршрутизує до здорових подів, IP не мають значення │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Створення Сервісів

### Імперативний спосіб (швидкий)

```bash
# Expose a deployment
kubectl expose deployment nginx --port=80

# With specific type
kubectl expose deployment nginx --port=80 --type=NodePort

# Check the service
kubectl get services
kubectl get svc              # Short form
```

### Декларативний спосіб (для продакшену)

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  selector:
    app: nginx               # Match pod labels
  ports:
  - port: 80                 # Service port
    targetPort: 80           # Container port
  type: ClusterIP            # Default type
```

```bash
kubectl apply -f service.yaml
```

---

## Типи Сервісів

### ClusterIP (за замовчуванням)

Доступ лише всередині кластера:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: internal-api
spec:
  type: ClusterIP            # Default, can omit
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080
```

```bash
# Access from within cluster only
curl http://internal-api:80
```

### NodePort

Відкриває сервіс на IP кожної ноди через статичний порт:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080          # Optional: 30000-32767
```

```bash
# Access from outside cluster
curl http://<node-ip>:30080
```

### LoadBalancer

Створює зовнішній балансувальник навантаження (хмарні середовища):

```yaml
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
    targetPort: 80
```

```bash
# Get external IP (cloud only)
kubectl get svc web-lb
# EXTERNAL-IP column shows the load balancer IP
```

---

## Діаграма Сервісів

```
┌─────────────────────────────────────────────────────────────┐
│              ТИПИ СЕРВІСІВ                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ClusterIP (лише внутрішній)                               │
│  ┌─────────────────────────────────────┐                  │
│  │  ClusterIP:80 ──► Pod:8080          │                  │
│  │               ──► Pod:8080          │                  │
│  │  (Доступний лише всередині кластера)│                  │
│  └─────────────────────────────────────┘                  │
│                                                             │
│  NodePort (зовнішній через ноду)                           │
│  ┌─────────────────────────────────────┐                  │
│  │  <NodeIP>:30080 ──► ClusterIP:80 ──► Pods             │
│  │  (Доступний ззовні)                │                  │
│  └─────────────────────────────────────┘                  │
│                                                             │
│  LoadBalancer (зовнішній через хмару)                      │
│  ┌─────────────────────────────────────┐                  │
│  │  <ExternalIP>:80 ──► NodePort ──► ClusterIP ──► Pods  │
│  │  (Хмарний провайдер керує LB)      │                  │
│  └─────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Виявлення Сервісів (DNS)

Kubernetes створює DNS-записи для Сервісів:

```
<service-name>.<namespace>.svc.cluster.local
```

```bash
# From any pod, you can reach:
curl nginx                           # Same namespace
curl nginx.default                   # Explicit namespace
curl nginx.default.svc               # More explicit
curl nginx.default.svc.cluster.local # Full FQDN
```

### Приклад

```bash
# Create deployment and service
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80

# Test DNS from another pod
kubectl run test --image=busybox --rm -it -- wget -qO- nginx
# Returns nginx HTML!

# Test with full DNS name
kubectl run test --image=busybox --rm -it -- nslookup nginx.default.svc.cluster.local
```

---

## Селектори: як Сервіси знаходять Поди

Сервіси використовують селектори за мітками:

```yaml
# Service
spec:
  selector:
    app: nginx
    tier: frontend

# Pod (must match ALL labels)
metadata:
  labels:
    app: nginx
    tier: frontend
```

```bash
# Check what pods a service targets
kubectl get endpoints nginx
# Shows IP:Port of matched pods
```

---

## Мапінг портів

```yaml
spec:
  ports:
  - port: 80           # Service port (what clients use)
    targetPort: 8080   # Container port (where app listens)
    protocol: TCP      # TCP (default) or UDP
```

```
┌─────────────────────────────────────────────────────────────┐
│  Клієнт ──► Сервіс:80 ──► Под:8080                         │
│                │                 │                          │
│             "port"         "targetPort"                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **Сервіси використовують iptables або IPVS.** kube-proxy налаштовує правила, які маршрутизують IP Сервісів до IP Подів. Жоден проксі-процес не обробляє кожне з'єднання окремо.

- **ClusterIP — віртуальна адреса.** Жоден мережевий інтерфейс не має цієї IP-адреси. Вона існує лише в правилах iptables.

- **NodePort використовує ВСІ ноди.** Навіть ноди без цільових подів коректно маршрутизують трафік.

- **Сервіси балансують випадково** за замовчуванням. Кожне з'єднання може потрапити на інший под.

---

## Типові помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Селектор не збігається з мітками подів | Сервіс не має ендпоінтів | Перевірте `kubectl get endpoints` |
| Неправильний targetPort | Відмова з'єднання | Вкажіть порт, на якому слухає контейнер |
| Використання IP пода замість сервісу | Зламається при перезапуску пода | Завжди використовуйте ім'я сервісу |

---

## Тест

1. **Чому варто використовувати Сервіси замість IP-адрес Подів?**
   <details>
   <summary>Відповідь</summary>
   IP-адреси Подів змінюються при перезапуску. Сервіси надають стабільну IP-адресу та DNS-ім'я, які зберігаються незалежно від того, які поди працюють. Вони також балансують навантаження між кількома подами.
   </details>

2. **Яка різниця між ClusterIP та NodePort?**
   <details>
   <summary>Відповідь</summary>
   ClusterIP доступний лише всередині кластера. NodePort відкриває сервіс на IP кожної ноди через статичний порт (30000–32767), що робить його доступним ззовні кластера.
   </details>

3. **Як Сервіси знаходять, до яких Подів маршрутизувати трафік?**
   <details>
   <summary>Відповідь</summary>
   За селекторами міток. Поле `selector` Сервісу вказує мітки. Лише поди з відповідними мітками отримують трафік. Перевірте `kubectl get endpoints`, щоб побачити відповідні поди.
   </details>

4. **Яке DNS-ім'я може використати под, щоб звернутися до Сервісу з ім'ям "api" у просторі імен "backend"?**
   <details>
   <summary>Відповідь</summary>
   `api.backend`, `api.backend.svc` або повне `api.backend.svc.cluster.local`. З того самого простору імен достатньо просто `api`.
   </details>

---

## Практична вправа

**Завдання**: Створіть деплоймент і відкрийте до нього доступ через Сервіс.

```bash
# 1. Create deployment
kubectl create deployment web --image=nginx --replicas=3

# 2. Expose as ClusterIP
kubectl expose deployment web --port=80

# 3. Check service
kubectl get svc web
kubectl get endpoints web

# 4. Test from within cluster
kubectl run test --image=busybox --rm -it -- wget -qO- web

# 5. Create NodePort service
kubectl expose deployment web --port=80 --type=NodePort --name=web-external

# 6. Get NodePort
kubectl get svc web-external
# Note the port in 30000-32767 range

# 7. Cleanup
kubectl delete deployment web
kubectl delete svc web web-external
```

**Критерії успіху**: Внутрішній сервіс працює, ендпоінти показують IP-адреси подів.

---

## Підсумок

Сервіси забезпечують стабільну мережу:

**Типи**:
- ClusterIP — лише внутрішній (за замовчуванням)
- NodePort — зовнішній через порт ноди
- LoadBalancer — зовнішній через хмарний балансувальник навантаження

**Ключові концепції**:
- Селектори відповідають міткам подів
- DNS-імена для виявлення сервісів
- Мапінг портів (port → targetPort)
- Ендпоінти показують відповідні поди

**Команди**:
- `kubectl expose deployment NAME --port=PORT`
- `kubectl get svc`
- `kubectl get endpoints`

---

## Наступний модуль

[Модуль 6: ConfigMaps та Secrets](module-1.6-configmaps-secrets/) — керування конфігурацією.
