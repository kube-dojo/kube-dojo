---
title: "\u0421\u0443\u043a\u0443\u043f\u043d\u0438\u0439 \u0442\u0435\u0441\u0442 \u0447\u0430\u0441\u0442\u0438\u043d\u0438 5: \u0421\u0435\u0440\u0432\u0456\u0441\u0438 \u0442\u0430 \u043c\u0435\u0440\u0435\u0436\u0430"
sidebar:
  order: 4
calque_review:
  reviewed_at: "2026-06-24"
  detector_version: "v2"
  status: "reviewed"
  flags_resolved: 7
  content_sha: "15e7f7c86694a9fbfadd05ecfbf52a005a2aa1a271e452466a2af9ae2d9c9aa4"
---
> **Обмеження часу**: 20 хвилин (імітація тиску іспиту)
>
> **Прохідний бал**: 80% (8/10 питань)

Цей тест перевіряє ваше володіння:
- Типами Сервісів та виявленням
- Маршрутизацією Інгресу
- Мережевими політиками

---

## Інструкції

1. Спробуйте відповісти на кожне питання, не дивлячись на відповіді
2. Засікайте час — швидкість важлива для CKAD
3. Використовуйте лише `kubectl` та `kubernetes.io/docs`
4. Перевіряйте відповіді після завершення всіх питань

---

## Питання

### Питання 1: Створити ClusterIP Сервіс
**[2 хвилини]**

Створіть Деплоймент з назвою `web-app` із 3 репліками, використовуючи nginx. Відкрийте його за допомогою ClusterIP Сервісу з назвою `web-service` на порті 80.

<details>
<summary>Відповідь</summary>

```bash
k create deployment web-app --image=nginx --replicas=3
k expose deployment web-app --name=web-service --port=80 --target-port=80
```

</details>

---

### Питання 2: Створити NodePort Сервіс
**[2 хвилини]**

Створіть NodePort Сервіс з назвою `external-web`, що відкриває деплоймент `web-app` на NodePort 30080.

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: external-web
spec:
  type: NodePort
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
EOF
```

Або видалити наявний сервіс і створити заново:
```bash
k expose deployment web-app --name=external-web --type=NodePort --port=80 --target-port=80
# Потім патч для конкретного nodePort
k patch svc external-web -p '{"spec":{"ports":[{"port":80,"targetPort":80,"nodePort":30080}]}}'
```

</details>

---

### Питання 3: DNS Сервісу
**[1 хвилина]**

Як Под у просторі імен `frontend` може звернутися до Сервісу з назвою `api` у просторі імен `backend` через DNS?

<details>
<summary>Відповідь</summary>

```
api.backend
# або
api.backend.svc
# або повний FQDN
api.backend.svc.cluster.local
```

</details>

---

### Питання 4: Зневадження зʼєднання Сервісу
**[2 хвилини]**

Сервіс з назвою `my-svc` не має точок доступу. Які команди ви виконаєте для діагностики проблеми?

<details>
<summary>Відповідь</summary>

```bash
# Перевірити точки доступу
k get endpoints my-svc

# Отримати селектор сервісу
k describe svc my-svc | grep Selector

# Перевірити мітки подів
k get pods --show-labels

# Перевірити, що селектор збігається з мітками подів
# Якщо невідповідність — виправити селектор або мітки подів
```

</details>

---

### Питання 5: Простий Інгрес
**[3 хвилини]**

Створіть Інгрес з назвою `app-ingress`, що маршрутизує трафік для хосту `myapp.example.com` до Сервісу з назвою `app-service` на порті 80.

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
EOF
```

</details>

---

### Питання 6: Інгрес на основі шляху
**[3 хвилини]**

Створіть Інгрес з назвою `multi-path` для хосту `shop.example.com`, що:
- Маршрутизує `/api` до `api-svc:8080`
- Маршрутизує `/web` до `web-svc:80`

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-path
spec:
  rules:
  - host: shop.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 8080
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-svc
            port:
              number: 80
EOF
```

</details>

---

### Питання 7: Мережева політика типової заборони
**[2 хвилини]**

Створіть мережеву політику з назвою `deny-all`, що забороняє весь вхідний трафік до подів у просторі імен `secure`.

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF
```

</details>

---

### Питання 8: Дозволити конкретні поди
**[3 хвилини]**

Створіть мережеву політику з назвою `allow-frontend`, що:
- Застосовується до подів з міткою `tier=backend`
- Дозволяє вхідний трафік лише від подів з міткою `tier=frontend`
- Лише на порті 8080

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - protocol: TCP
      port: 8080
EOF
```

</details>

---

### Питання 9: Селектор простору імен
**[2 хвилини]**

Створіть мережеву політику, що дозволяє вхідний трафік до подів з міткою `app=db` лише від подів у просторах імен з міткою `env=production`.

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-from-prod
spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          env: production
EOF
```

</details>

---

### Питання 10: Політика вихідного трафіку
**[3 хвилини]**

Створіть мережеву політику, що:
- Застосовується до подів з міткою `role=web`
- Дозволяє вихідний трафік лише до подів з міткою `role=api` на порті 8080
- Дозволяє вихідний трафік до DNS (kube-dns) для розвʼязання імен

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-egress
spec:
  podSelector:
    matchLabels:
      role: web
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          role: api
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
EOF
```

</details>

---

## Оцінювання

| Правильних відповідей | Бал | Статус |
|-----------------------|-----|--------|
| 10/10 | 100% | Відмінно — готові до іспиту |
| 8–9/10 | 80–90% | Добре — потрібен незначний огляд |
| 6–7/10 | 60–70% | Перегляньте слабкі місця |
| <6/10 | <60% | Поверніться до модулів частини 5 |

---

## Прибирання

```bash
k delete deployment web-app 2>/dev/null
k delete svc web-service external-web 2>/dev/null
k delete ingress app-ingress multi-path 2>/dev/null
k delete netpol deny-all allow-frontend db-from-prod web-egress 2>/dev/null
```

---

## Ключові висновки

Якщо ви набрали менше 80%, перегляньте ці теми:

- **Помилка в П1–2**: Перегляньте Модуль 5.1 (Сервіси) — типи сервісів та створення
- **Помилка в П3–4**: Перегляньте Модуль 5.1 (Сервіси) — DNS та зневадження
- **Помилка в П5–6**: Перегляньте Модуль 5.2 (Інгрес) — правила маршрутизації
- **Помилка в П7–10**: Перегляньте Модуль 5.3 (Мережеві політики) — селектори та правила

---

## Навчальну програму CKAD завершено!

Вітаємо із завершенням усіх модулів навчальної програми CKAD:

- **Частина 1**: Проєктування та створення застосунків (Поди, Джоби, багатоконтейнерні шаблони)
- **Частина 2**: Розгортання застосунків (Деплойменти, Helm, Kustomize)
- **Частина 3**: Спостережуваність застосунків (Проби, Логування, Зневадження)
- **Частина 4**: Середовище застосунків (ConfigMap, Секрети, Безпека)
- **Частина 5**: Сервіси та мережа (Сервіси, Інгрес, Мережеві політики)

### Подальші кроки

1. **Практикуйтесь, практикуйтесь, практикуйтесь** — швидкість важлива для CKAD
2. **Використовуйте killer.sh** для реалістичної симуляції іспиту
3. **Перегляньте слабкі місця** — зосередьтесь на темах, де ви набрали найменше
4. **Опануйте імперативні команди** — це заощадить час на іспиті

Успіхів на іспиті CKAD!
