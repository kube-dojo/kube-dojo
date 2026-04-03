---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 3.4: \u0406\u043d\u0433\u0440\u0435\u0441"
slug: uk/k8s/cka/part3-services-networking/module-3.4-ingress
sidebar: 
  order: 5
lab: 
  id: cka-3.4-ingress
  url: https://killercoda.com/kubedojo/scenario/cka-3.4-ingress
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[СЕРЕДНЯ]` — HTTP/HTTPS маршрутизація
>
> **Час на проходження**: 45-55 хвилин
>
> **Передумови**: Модуль 3.1 (Сервіси), Модуль 3.3 (DNS)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** ресурси Ingress з правилами маршрутизації на основі шляхів та хостів
- **Налаштувати** TLS-термінацію на Ingress за допомогою Secrets
- **Розгорнути** та налаштувати Ingress controller (NGINX) і пояснити його роль відносно ресурсу Ingress
- **Дебажити** збої маршрутизації Ingress, перевіряючи логи контролера, бекенд-сервіси та анотації

---

## Чому цей модуль важливий

Хоча Сервіси відкривають застосунки в мережу, Інгрес забезпечує **HTTP/HTTPS маршрутизацію** з такими можливостями, як маршрутизація на основі шляхів, віртуальні хости та TLS-термінація. Замість того, щоб відкривати багато NodePort-ів, ви відкриваєте один Інгрес-контролер, який маршрутизує трафік на основі URL-адрес.

Іспит CKA перевіряє створення Інгресу, маршрутизацію шляхів та розуміння того, як Інгрес з'єднується з Сервісами. Вам потрібно буде швидко створювати ресурси Інгресу та налагоджувати проблеми маршрутизації.

> **Важливо: Завершення підтримки Ingress-NGINX Controller**
>
> Популярний **ingress-nginx controller** досяг кінця підтримки **31 березня 2026 року**. Після цієї дати він не отримує нових релізів, виправлень помилок чи патчів безпеки. Однак **сам Ingress API** (`networking.k8s.io/v1`) **НЕ застарілий** і залишається повністю підтримуваним у Kubernetes. Вам варто вивчити Інгрес (він досі є на іспиті та широко використовується), але для нових розгортань використовуйте **Gateway API** (Модуль 3.5). Альтернативні контролери, які підтримують і Ingress, і Gateway API, включають **Envoy Gateway**, **Traefik**, **Kong**, **Cilium** та **NGINX Gateway Fabric**.
>
> Якщо ви мігруєте з ingress-nginx, використовуйте інструмент **Ingress2Gateway 1.0** для перетворення ресурсів Інгресу на ресурси Gateway API: `kubectl krew install ingress2gateway`

> **Аналогія з рецепцією готелю**
>
> Уявіть Інгрес як стійку рецепції готелю. Гості (HTTP-запити) прибувають через головний вхід (одна IP-адреса). Рецепціоніст (Інгрес-контролер) запитує, куди вони хочуть потрапити — Кімната 101 (шлях `/api`) веде до API-сервісу, Кімната 202 (шлях `/web`) веде до веб-сервісу. Одна точка входу, інтелектуальна маршрутизація всередині.

---

## Чому ви навчитеся

До кінця цього модуля ви зможете:
- Розуміти різницю між Інгресом, LoadBalancer та NodePort
- Створювати ресурси Інгресу з правилами шляхів та хостів
- Налаштовувати TLS-термінацію
- Налагоджувати проблеми маршрутизації Інгресу
- Працювати з різними Інгрес-контролерами

---

## Чи знали ви?

- **Інгрес потребує контролер**: Ресурс Інгресу сам по собі нічого не робить. Вам потрібен Інгрес-контролер (наприклад, Envoy Gateway, Traefik або Kong), щоб фактично маршрутизувати трафік.

- **Gateway API — рекомендований наступник**: Gateway API (розглядається в Модулі 3.5) тепер у статусі GA і є рекомендованим стандартом для нових розгортань. Інгрес залишається підтримуваним і широко використовується, але для нових проєктів варто надавати перевагу Gateway API.

- **Один Інгрес — багато сервісів**: Один ресурс Інгресу може маршрутизувати трафік до десятків бекенд-сервісів на основі шляхів та імен хостів.

- **Ingress-NGINX вже не підтримується**: Колись домінантний ingress-nginx controller досяг кінця підтримки 31 березня 2026 року. Інструмент Ingress2Gateway 1.0 допомагає мігрувати наявні ресурси Інгресу на Gateway API.

---

## Частина 1: Архітектура Інгресу

### 1.1 Як працює Інгрес

```
┌────────────────────────────────────────────────────────────────┐
│                   Архітектура Інгресу                            │
│                                                                 │
│   Зовнішній трафік                                              │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │            Load Balancer / NodePort                      │  │
│   │            (Сервіс Інгрес-контролера)                   │  │
│   └────────────────────────┬────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Інгрес-контролер                            │  │
│   │              (nginx, traefik тощо)                      │  │
│   │                                                          │  │
│   │   Читає ресурси Інгресу та налаштовує маршрутизацію     │  │
│   └─────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│               ┌─────────────┼─────────────┐                    │
│               │             │             │                    │
│               ▼             ▼             ▼                    │
│         ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│         │ Сервіс   │  │ Сервіс   │  │ Сервіс   │             │
│         │   /api   │  │   /web   │  │   /docs  │             │
│         └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│              │             │             │                    │
│              ▼             ▼             ▼                    │
│         ┌──────┐      ┌──────┐      ┌──────┐                 │
│         │ Поди │      │ Поди │      │ Поди │                 │
│         └──────┘      └──────┘      └──────┘                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Інгрес проти інших варіантів

| Можливість | NodePort | LoadBalancer | Інгрес |
|------------|----------|--------------|--------|
| Рівень | L4 (TCP/UDP) | L4 (TCP/UDP) | L7 (HTTP/HTTPS) |
| Маршрутизація шляхів | Ні | Ні | Так |
| Віртуальні хости | Ні | Ні | Так |
| TLS-термінація | Ні | Обмежена | Так |
| Вартість | Безоплатно | $ за LB | Один контролер для багатьох сервісів |
| Зовнішній IP | IP вузла:Порт | IP хмарного LB | IP контролера |

### 1.3 Необхідні компоненти

| Компонент | Призначення | Хто створює |
|-----------|-------------|-------------|
| Інгрес-контролер | Фактично маршрутизує трафік | Адміністратор кластера |
| Ресурс Інгресу | Визначає правила маршрутизації | Розробник |
| Бекенд-сервіси | Цільові сервіси | Розробник |
| TLS Secret | HTTPS-сертифікати | Розробник/cert-manager |

---

## Частина 2: Інгрес-контролери

### 2.1 Популярні Інгрес-контролери

| Контролер | Опис | Найкраще для |
|-----------|------|--------------|
| **nginx** | Найпоширеніший, багатий на можливості | Загальне використання |
| **traefik** | Автоматичне виявлення, сучасний | Динамічні середовища |
| **haproxy** | Висока продуктивність | Високонавантажені сайти |
| **contour** | На основі Envoy | Користувачі service mesh |
| **AWS ALB** | Нативна інтеграція з AWS | Середовища AWS |

### 2.2 Встановлення nginx Інгрес-контролера (kind/minikube)

```bash
# Для kind
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Для minikube
minikube addons enable ingress

# Перевірка встановлення
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### 2.3 Перевірка стану Інгрес-контролера

```bash
# Перевірити поди
k get pods -n ingress-nginx

# Перевірити сервіс
k get svc -n ingress-nginx

# Перевірити IngressClass
k get ingressclass
```

---

## Частина 3: Створення ресурсів Інгресу

### 3.1 Простий Інгрес (один Сервіс)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-ingress
spec:
  ingressClassName: nginx            # Який контролер використовувати
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service        # Цільовий сервіс
            port:
              number: 80             # Порт сервісу
```

### 3.2 Маршрутизація на основі шляхів

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: default-service
            port:
              number: 80
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Маршрутизація на основі шляхів                │
│                                                                 │
│   Запит: http://mysite.com/api/users                           │
│                        │                                        │
│                        ▼                                        │
│   ┌────────────────────────────────────────────────────────┐   │
│   │                    Інгрес                               │   │
│   │                                                         │   │
│   │   /api/*  ──────────► api-service                      │   │
│   │   /web/*  ──────────► web-service                      │   │
│   │   /*      ──────────► default-service                  │   │
│   │                                                         │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.3 Типи шляхів

| PathType | Поведінка | Приклад |
|----------|-----------|---------|
| `Exact` | Тільки точний збіг | `/api` збігається з `/api`, але не з `/api/` |
| `Prefix` | Збіг за префіксом | `/api` збігається з `/api`, `/api/users` |
| `ImplementationSpecific` | Вирішує контролер | Залежить від контролера |

### 3.4 Маршрутизація на основі хостів (віртуальні хости)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: virtual-host-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Маршрутизація на основі хостів                │
│                                                                 │
│   api.example.com  ──────────► api-service                     │
│   web.example.com  ──────────► web-service                     │
│   *.example.com    ──────────► default-service (якщо налашт.)  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.5 Поєднання маршрутизації за хостом та шляхом

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: combined-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
  - host: admin.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-service
            port:
              number: 80
```

---

## Частина 4: Налаштування TLS/HTTPS

### 4.1 Створення TLS Secret

```bash
# Згенерувати самопідписаний сертифікат (для тестування)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=example.com"

# Створити секрет
k create secret tls example-tls --cert=tls.crt --key=tls.key

# Або за допомогою kubectl
k create secret tls example-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

### 4.2 Інгрес з TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - example.com
    - www.example.com
    secretName: example-tls      # Назва TLS-секрету
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 4.3 Потік TLS-конфігурації

```
┌────────────────────────────────────────────────────────────────┐
│                   TLS-термінація                                │
│                                                                 │
│   Клієнт (HTTPS)                                               │
│        │                                                        │
│        │ TLS/SSL шифрування                                    │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Інгрес-контролер                            │  │
│   │              (TLS термінується тут)                      │  │
│   │                                                          │  │
│   │   Використовує сертифікат із Secret: example-tls        │  │
│   └─────────────────────────────────────────────────────────┘  │
│        │                                                        │
│        │ Звичайний HTTP (всередині кластера)                   │
│        ▼                                                        │
│   ┌──────────────────┐                                         │
│   │     Сервіс       │                                         │
│   │     (порт 80)    │                                         │
│   └──────────────────┘                                         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Частина 5: Анотації Інгресу

### 5.1 Поширені анотації nginx

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: annotated-ingress
  annotations:
    # Перезапис URL-шляху
    nginx.ingress.kubernetes.io/rewrite-target: /

    # SSL-перенаправлення
    nginx.ingress.kubernetes.io/ssl-redirect: "true"

    # Тайм-аути
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"

    # Обмеження швидкості
    nginx.ingress.kubernetes.io/limit-rps: "10"

    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 5.2 Перезапис URL

```yaml
# Маршрутизувати /app/(.*)  до бекенду /($1)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rewrite-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /app/(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: web-service
            port:
              number: 80
```

---

## Частина 6: Налагодження Інгресу

### 6.1 Процес налагодження

```
Інгрес не працює?
    │
    ├── kubectl get ingress (перевірити ADDRESS)
    │       │
    │       ├── Немає ADDRESS → Контролер не обробляє
    │       │                   Перевірте IngressClass
    │       │
    │       └── Є ADDRESS → Продовжуйте налагодження
    │
    ├── kubectl describe ingress (перевірити події)
    │       │
    │       └── Помилки? → Виправити конфігурацію
    │
    ├── Перевірити бекенд-сервіс
    │   kubectl get svc,endpoints
    │       │
    │       └── Немає endpoints? → Сервіс не має подів
    │
    ├── Перевірити логи Інгрес-контролера
    │   kubectl logs -n ingress-nginx <controller-pod>
    │
    └── Тест зсередини кластера
        kubectl run test --rm -it --image=curlimages/curl -- \
          curl <service>
```

### 6.2 Поширені команди для Інгресу

```bash
# Список інгресів
k get ingress
k get ing              # Скорочена форма

# Деталі інгресу
k describe ingress my-ingress

# Отримати YAML інгресу
k get ingress my-ingress -o yaml

# Перевірити IngressClass
k get ingressclass

# Перевірити поди Інгрес-контролера
k get pods -n ingress-nginx

# Переглянути логи контролера
k logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### 6.3 Поширені проблеми

| Симптом | Причина | Рішення |
|---------|---------|---------|
| ADDRESS не призначено | Немає Інгрес-контролера | Встановити Інгрес-контролер |
| ADDRESS є, але 404 | Шлях не збігається | Перевірити path та pathType |
| 503 Service Unavailable | Немає endpoints | Перевірити selector сервісу/поди |
| Помилка SSL | Неправильний/відсутній TLS-секрет | Переконатися, що секрет існує та відповідає хосту |
| Неправильний IngressClass | Кілька контролерів | Вказати правильний ingressClassName |

---

## Частина 7: Бекенд за замовчуванням

### 7.1 Налаштування бекенду за замовчуванням

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: default-backend-ingress
spec:
  ingressClassName: nginx
  defaultBackend:                    # Перехоплення всього
    service:
      name: default-service
      port:
        number: 80
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

Запити, що не відповідають жодному правилу, спрямовуються до `defaultBackend`.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Немає IngressClass | Контролер не обробляє | Додати `ingressClassName` до spec |
| Неправильний pathType | Маршрути не збігаються | Використовуйте `Prefix` для більшості випадків |
| Невідповідність порту сервісу | Помилки 503 | Порт Інгресу має збігатися з портом Сервісу |
| TLS-секрет у неправильному просторі імен | Помилки SSL | Секрет має бути в тому ж просторі імен, що й Інгрес |
| Відсутній Інгрес-контролер | ADDRESS не призначено | Спочатку встановити контролер |

---

## Тест

1. **У чому різниця між Інгресом та Сервісом типу LoadBalancer?**
   <details>
   <summary>Відповідь</summary>
   Інгрес — це маршрутизація на рівні L7 (HTTP/HTTPS) з правилами на основі шляхів/хостів, тоді як LoadBalancer — це рівень L4 (TCP/UDP) без інтелектуальної маршрутизації. Інгрес може обслуговувати багато сервісів з однією зовнішньою IP-адресою.
   </details>

2. **Інгрес не показує ADDRESS. Яка ймовірна причина?**
   <details>
   <summary>Відповідь</summary>
   Не встановлено Інгрес-контролер, або `ingressClassName` не відповідає жодному встановленому контролеру. Встановіть Інгрес-контролер та перевірте IngressClass.
   </details>

3. **У чому різниця між `pathType: Prefix` та `pathType: Exact`?**
   <details>
   <summary>Відповідь</summary>
   `Prefix` збігається з будь-яким шляхом, що починається з вказаного префікса (`/api` збігається з `/api/users`). `Exact` вимагає точного збігу (`/api` збігається тільки з `/api`, але не з `/api/`).
   </details>

4. **Як налаштувати HTTPS для Інгресу?**
   <details>
   <summary>Відповідь</summary>
   1. Створити TLS-секрет із сертифікатом та ключем
   2. Додати секцію `tls` до spec Інгресу з хостами та secretName
   3. Інгрес-контролер виконає TLS-термінацію
   </details>

5. **Запити до `/app/users` мають потрапляти до бекенду як `/users`. Як це зробити?**
   <details>
   <summary>Відповідь</summary>
   Використати анотацію перезапису: `nginx.ingress.kubernetes.io/rewrite-target: /$1` з шляхом `/app/(.*)` та `pathType: ImplementationSpecific`.
   </details>

---

## Практична вправа

**Завдання**: Створити Інгрес із кількома сервісами та TLS.

**Кроки**:

1. **Створити бекенд-сервіси**:
```bash
# API-сервіс
k create deployment api --image=nginx
k expose deployment api --port=80

# Веб-сервіс
k create deployment web --image=nginx
k expose deployment web --port=80
```

2. **Створити Інгрес на основі шляхів**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-path-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF
```

3. **Перевірити Інгрес**:
```bash
k get ingress
k describe ingress multi-path-ingress
```

4. **Тестування маршрутизації** (якщо Інгрес-контролер встановлено):
```bash
# Отримати адресу Інгресу
INGRESS_IP=$(k get ingress multi-path-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Тестування шляхів (зсередини кластера, якщо потрібно)
k run test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -H "Host: example.com" http://$INGRESS_IP/api
```

5. **Створити Інгрес на основі хостів**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF
```

6. **Створити TLS-секрет** (самопідписаний для тестування):
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=example.com"

k create secret tls example-tls --cert=tls.crt --key=tls.key
```

7. **Створити TLS Інгрес**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - secure.example.com
    secretName: example-tls
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF
```

8. **Прибирання**:
```bash
k delete ingress multi-path-ingress host-ingress tls-ingress
k delete deployment api web
k delete svc api web
k delete secret example-tls
rm tls.key tls.crt
```

**Критерії успіху**:
- [ ] Вмію створювати Інгрес із маршрутизацією за шляхами
- [ ] Вмію створювати Інгрес із маршрутизацією за хостами
- [ ] Вмію налаштовувати TLS на Інгресі
- [ ] Розумію IngressClass
- [ ] Вмію налагоджувати проблеми Інгресу

---

## Практичні вправи

### Вправа 1: Базовий Інгрес (Ціль: 3 хвилини)

```bash
# Створити сервіс
k create deployment drill-app --image=nginx
k expose deployment drill-app --port=80

# Створити Інгрес
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: drill-app
            port:
              number: 80
EOF

# Перевірити
k get ingress drill-ingress
k describe ingress drill-ingress

# Прибирання
k delete ingress drill-ingress
k delete deployment drill-app
k delete svc drill-app
```

### Вправа 2: Інгрес із кількома шляхами (Ціль: 4 хвилини)

```bash
# Створити сервіси
k create deployment api --image=nginx
k create deployment web --image=nginx
k expose deployment api --port=80
k expose deployment web --port=80

# Створити Інгрес
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-path
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF

# Перевірити
k describe ingress multi-path

# Прибирання
k delete ingress multi-path
k delete deployment api web
k delete svc api web
```

### Вправа 3: Інгрес на основі хостів (Ціль: 4 хвилини)

```bash
# Створити сервіси
k create deployment app1 --image=nginx
k create deployment app2 --image=nginx
k expose deployment app1 --port=80
k expose deployment app2 --port=80

# Створити Інгрес
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-based
spec:
  ingressClassName: nginx
  rules:
  - host: app1.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1
            port:
              number: 80
  - host: app2.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2
            port:
              number: 80
EOF

# Перевірити
k get ingress host-based
k describe ingress host-based

# Прибирання
k delete ingress host-based
k delete deployment app1 app2
k delete svc app1 app2
```

### Вправа 4: TLS Інгрес (Ціль: 5 хвилин)

```bash
# Створити сервіс
k create deployment secure-app --image=nginx
k expose deployment secure-app --port=80

# Згенерувати сертифікат
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -subj "/CN=secure.local"

# Створити секрет
k create secret tls tls-secret --cert=tls.crt --key=tls.key

# Створити Інгрес із TLS
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - secure.local
    secretName: tls-secret
  rules:
  - host: secure.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-app
            port:
              number: 80
EOF

# Перевірити
k describe ingress tls-ingress

# Прибирання
k delete ingress tls-ingress
k delete deployment secure-app
k delete svc secure-app
k delete secret tls-secret
rm tls.key tls.crt
```

### Вправа 5: Перевірка IngressClass (Ціль: 2 хвилини)

```bash
# Список IngressClass
k get ingressclass

# Деталі
k describe ingressclass nginx

# Перевірити, який є типовим
k get ingressclass -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.ingressclass\.kubernetes\.io/is-default-class}{"\n"}{end}'
```

### Вправа 6: Інгрес із анотаціями (Ціль: 4 хвилини)

```bash
# Створити сервіс
k create deployment annotated-app --image=nginx
k expose deployment annotated-app --port=80

# Створити Інгрес із анотаціями
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: annotated-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: annotated-app
            port:
              number: 80
EOF

# Перевірити анотації
k get ingress annotated-ingress -o yaml | grep -A5 annotations

# Прибирання
k delete ingress annotated-ingress
k delete deployment annotated-app
k delete svc annotated-app
```

### Вправа 7: Налагодження Інгресу (Ціль: 4 хвилини)

```bash
# Створити Інгрес із неправильною назвою сервісу (навмисно зламаний)
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: broken-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nonexistent-service
            port:
              number: 80
EOF

# Налагодження
k describe ingress broken-ingress
# Шукайте попередження про бекенд

# Перевірити логи Інгрес-контролера (якщо встановлено)
k logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=10

# Виправлення: створити відсутній сервіс
k create deployment fix-app --image=nginx
k expose deployment fix-app --port=80 --name=nonexistent-service

# Перевірити
k describe ingress broken-ingress

# Прибирання
k delete ingress broken-ingress
k delete deployment fix-app
k delete svc nonexistent-service
```

### Вправа 8: Виклик — Повне налаштування Інгресу

Без підглядання у рішення:

1. Створити деплойменти: `api` та `frontend` (nginx)
2. Відкрити обидва як ClusterIP-сервіси на порту 80
3. Створити Інгрес із:
   - Шлях `/api` маршрутизує до api-сервісу
   - Шлях `/` маршрутизує до frontend-сервісу
   - Хост: `myapp.local`
4. Створити TLS-секрет та додати HTTPS
5. Перевірити за допомогою describe
6. Прибрати все

```bash
# ВАШЕ ЗАВДАННЯ: Виконайте за 7 хвилин
```

<details>
<summary>Рішення</summary>

```bash
# 1. Створити деплойменти
k create deployment api --image=nginx
k create deployment frontend --image=nginx

# 2. Відкрити як ClusterIP
k expose deployment api --port=80
k expose deployment frontend --port=80

# 3. Створити Інгрес
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: challenge-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
EOF

# 4. Додати TLS
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -subj "/CN=myapp.local"
k create secret tls myapp-tls --cert=tls.crt --key=tls.key

# Оновити Інгрес із TLS
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: challenge-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.local
    secretName: myapp-tls
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
EOF

# 5. Перевірити
k describe ingress challenge-ingress

# 6. Прибирання
k delete ingress challenge-ingress
k delete deployment api frontend
k delete svc api frontend
k delete secret myapp-tls
rm tls.key tls.crt
```

</details>

---

## Наступний модуль

[Модуль 3.5: Gateway API](module-3.5-gateway-api/) — Наступне покоління Kubernetes Інгресу.
