---
title: "Модуль 1.3: Безпека Ingress"
slug: uk/k8s/cks/part1-cluster-setup/module-1.3-ingress-security
sidebar:
  order: 3
---
> **Складність**: `[СЕРЕДНЯ]` — Критична для безпеки зовнішнього доступу
>
> **Час на виконання**: 35-40 хвилин
>
> **Передумови**: Модуль 1.1 (Network Policies), знання Ingress з CKA

---

## Чому цей модуль важливий

Ingress — це місце, де ваш кластер зустрічається з інтернетом. Це вхідні двері — і зловмисники атакують вхідні двері. Неправильно налаштований TLS, відкриті панелі адміністратора та відсутні заголовки безпеки — поширені вразливості.

CKS тестує вашу здатність зміцнити конфігурації ingress за межами базової функціональності.

> **Примітка з безпеки**: Контролер ingress-nginx було виведено з експлуатації 31 березня 2026 року і він більше не отримує патчі безпеки. Якщо ваші кластери все ще використовують ingress-nginx, це **критичний ризик безпеки**. Мігруйте на підтримуваний контролер (Envoy Gateway, Traefik, Cilium, NGINX Gateway Fabric) та розгляньте впровадження Gateway API для нових розгортань. Принципи безпеки в цьому модулі рівною мірою стосуються конфігурацій Ingress та Gateway API.

---

## Поверхня атаки Ingress

```
┌─────────────────────────────────────────────────────────────┐
│              ПОВЕРХНЯ АТАКИ БЕЗПЕКИ INGRESS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Інтернет                                                   │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              КОНТРОЛЕР INGRESS                       │   │
│  │                                                      │   │
│  │  Вектори атак:                                      │   │
│  │  ⚠️  Немає TLS = дані відкриті при передачі        │   │
│  │  ⚠️  Слабкі версії TLS (TLS 1.0/1.1)               │   │
│  │  ⚠️  Відсутні заголовки безпеки                     │   │
│  │  ⚠️  Вразливості обходу шляху                       │   │
│  │  ⚠️  Відкриті ендпоінти статусу/метрик              │   │
│  │  ⚠️  Немає обмеження швидкості                      │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Сервіс App     │  │  Сервіс API     │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Конфігурація TLS

### Створення TLS Secrets

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=myapp.example.com"

# Create Kubernetes secret
kubectl create secret tls myapp-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n production

# Verify secret
kubectl get secret myapp-tls -n production -o yaml
```

### Ingress з TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-ingress
  namespace: production
  annotations:
    # Force HTTPS redirect
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # Enable HSTS
    nginx.ingress.kubernetes.io/hsts: "true"
    nginx.ingress.kubernetes.io/hsts-max-age: "31536000"
    nginx.ingress.kubernetes.io/hsts-include-subdomains: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

---

## Заголовки безпеки

### Основні заголовки

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hardened-ingress
  annotations:
    # Content Security Policy
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Referrer-Policy "strict-origin-when-cross-origin" always;
      add_header Content-Security-Policy "default-src 'self'" always;
spec:
  # ... rest of spec
```

```
┌─────────────────────────────────────────────────────────────┐
│              ПОЯСНЕННЯ ЗАГОЛОВКІВ БЕЗПЕКИ                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  X-Frame-Options: SAMEORIGIN                               │
│  └── Запобігає атакам clickjacking                         │
│                                                             │
│  X-Content-Type-Options: nosniff                           │
│  └── Запобігає підміні MIME-типу                           │
│                                                             │
│  X-XSS-Protection: 1; mode=block                           │
│  └── Увімкнення фільтрації XSS у браузері                 │
│                                                             │
│  Referrer-Policy: strict-origin-when-cross-origin          │
│  └── Контролює витік інформації про referrer               │
│                                                             │
│  Content-Security-Policy: default-src 'self'               │
│  └── Обмежує джерела завантаження ресурсів                 │
│                                                             │
│  Strict-Transport-Security (HSTS)                          │
│  └── Примусовий HTTPS на вказаний термін                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Примусове використання версії TLS

### Вимкнення слабких версій TLS

```yaml
# ConfigMap for nginx-ingress-controller
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
data:
  # Minimum TLS version
  ssl-protocols: "TLSv1.2 TLSv1.3"

  # Strong cipher suites only
  ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"

  # Enable HSTS globally
  hsts: "true"
  hsts-max-age: "31536000"
  hsts-include-subdomains: "true"
  hsts-preload: "true"
```

### Налаштування TLS для окремого Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: strict-tls-ingress
  annotations:
    # Require client certificate (mTLS)
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-secret: "production/ca-secret"

    # Specific TLS version for this ingress
    nginx.ingress.kubernetes.io/ssl-prefer-server-ciphers: "true"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
```

---

## Взаємний TLS (mTLS)

```
┌─────────────────────────────────────────────────────────────┐
│              ВЗАЄМНА АВТЕНТИФІКАЦІЯ TLS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Стандартний TLS:                                          │
│  Клієнт ──────► Сервер пред'являє сертифікат               │
│         ◄────── Клієнт перевіряє сервер                    │
│  (Одностороння перевірка)                                  │
│                                                             │
│  Взаємний TLS:                                             │
│  Клієнт ──────► Сервер пред'являє сертифікат               │
│         ◄────── Клієнт перевіряє сервер                    │
│  Клієнт ──────► Клієнт пред'являє сертифікат               │
│         ◄────── Сервер перевіряє клієнта                   │
│  (Двостороння перевірка)                                   │
│                                                             │
│  Випадки використання:                                     │
│  • Автентифікація між сервісами                            │
│  • API-клієнти з сертифікатами                             │
│  • Архітектури нульової довіри                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Налаштування mTLS

```bash
# Create CA secret for client verification
kubectl create secret generic ca-secret \
  --from-file=ca.crt=ca.crt \
  -n production
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mtls-ingress
  namespace: production
  annotations:
    # Enable client certificate verification
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    # CA to verify client certs
    nginx.ingress.kubernetes.io/auth-tls-secret: "production/ca-secret"
    # Depth of verification
    nginx.ingress.kubernetes.io/auth-tls-verify-depth: "1"
    # Pass client cert to backend
    nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
spec:
  tls:
  - hosts:
    - secure-api.example.com
    secretName: api-tls
  rules:
  - host: secure-api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-api
            port:
              number: 443
```

---

## Обмеження швидкості

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rate-limited-ingress
  annotations:
    # Limit requests per second
    nginx.ingress.kubernetes.io/limit-rps: "10"

    # Limit connections
    nginx.ingress.kubernetes.io/limit-connections: "5"

    # Burst allowance
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "5"

    # Custom error when rate limited
    nginx.ingress.kubernetes.io/server-snippet: |
      limit_req_status 429;
spec:
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
```

---

## Захист чутливих шляхів

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: protected-paths
  annotations:
    # Block access to sensitive paths
    nginx.ingress.kubernetes.io/server-snippet: |
      location ~ ^/(admin|metrics|health|debug) {
        deny all;
        return 403;
      }

    # Or require authentication
    nginx.ingress.kubernetes.io/auth-url: "https://auth.example.com/verify"
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app
            port:
              number: 80
```

### Використання NetworkPolicies з Ingress

```yaml
# Allow only ingress controller to reach backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-ingress-only
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
      podSelector:
        matchLabels:
          app.kubernetes.io/name: ingress-nginx
    ports:
    - port: 80
```

---

## Зміцнення контролера Ingress

### Безпечне розгортання контролера Ingress

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  template:
    spec:
      containers:
      - name: controller
        image: registry.k8s.io/ingress-nginx/controller:v1.9.0
        securityContext:
          # Don't run as root
          runAsNonRoot: true
          runAsUser: 101
          # Read-only filesystem
          readOnlyRootFilesystem: true
          # No privilege escalation
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
        # Resource limits
        resources:
          limits:
            cpu: "1"
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 256Mi
```

---

## Реальні сценарії іспиту

### Сценарій 1: Увімкнення TLS на Ingress

```bash
# Create TLS certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tls.key -out /tmp/tls.crt \
  -subj "/CN=webapp.example.com"

# Create secret
kubectl create secret tls webapp-tls \
  --cert=/tmp/tls.crt \
  --key=/tmp/tls.key \
  -n production

# Update existing ingress to use TLS
kubectl patch ingress webapp -n production --type=json -p='[
  {"op": "add", "path": "/spec/tls", "value": [
    {"hosts": ["webapp.example.com"], "secretName": "webapp-tls"}
  ]}
]'
```

### Сценарій 2: Примусове перенаправлення на HTTPS

```bash
# Add SSL redirect annotation
kubectl annotate ingress webapp -n production \
  nginx.ingress.kubernetes.io/ssl-redirect="true"
```

### Сценарій 3: Додавання заголовків безпеки

```bash
kubectl annotate ingress webapp -n production \
  nginx.ingress.kubernetes.io/configuration-snippet='
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
  '
```

---

## Чи знали ви?

- **Попереднє завантаження HSTS** додає ваш домен до вбудованого списку HTTPS-only у браузерах. Після додавання браузери ніколи не робитимуть HTTP-запити до вашого домену.

- **TLS 1.0 та 1.1 є застарілими.** Відповідність PCI-DSS вимагає мінімум TLS 1.2 з 2018 року.

- **nginx-ingress проти ingress-nginx**: Є ДВА контролери ingress, які часто плутають. `ingress-nginx` (kubernetes/ingress-nginx) — це офіційний; `nginx-ingress` — від NGINX Inc.

- **Let's Encrypt з cert-manager** може автоматизувати видачу TLS-сертифікатів. Багато виробничих кластерів використовують це замість ручного управління сертифікатами.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Немає TLS на ingress | Дані відкриті при передачі | Завжди налаштовуйте TLS |
| Самопідписані сертифікати в prod | Попередження браузера, немає довіри | Використовуйте належний CA (Let's Encrypt) |
| Відсутній заголовок HSTS | Можливі атаки даунгрейду | Увімкніть HSTS з довгим max-age |
| Відкритий ендпоінт /metrics | Витік інформації | Заблокуйте або автентифікуйте |
| Немає обмеження швидкості | Вразливість до DoS | Налаштуйте ліміти швидкості |

---

## Тест

1. **Яка анотація примусово перенаправляє HTTP на HTTPS у nginx-ingress?**
   <details>
   <summary>Відповідь</summary>
   `nginx.ingress.kubernetes.io/ssl-redirect: "true"` — перенаправляє всі HTTP-запити на HTTPS.
   </details>

2. **Яка мінімальна рекомендована версія TLS для виробництва?**
   <details>
   <summary>Відповідь</summary>
   TLS 1.2. TLS 1.0 та 1.1 є застарілими та мають відомі вразливості. TLS 1.3 є кращим, але 1.2 — мінімум для відповідності.
   </details>

3. **Який заголовок запобігає атакам clickjacking?**
   <details>
   <summary>Відповідь</summary>
   `X-Frame-Options: DENY` або `X-Frame-Options: SAMEORIGIN` — запобігають вбудовуванню сторінки в iframe на інших сайтах.
   </details>

4. **Як створити TLS secret у Kubernetes?**
   <details>
   <summary>Відповідь</summary>
   `kubectl create secret tls <name> --cert=<cert-file> --key=<key-file>` — тип secret `kubernetes.io/tls` і містить ключі `tls.crt` та `tls.key`.
   </details>

---

## Практична вправа

**Завдання**: Захистіть ingress за допомогою TLS та заголовків безпеки.

```bash
# Setup
kubectl create namespace secure-app
kubectl run webapp --image=nginx -n secure-app
kubectl expose pod webapp --port=80 -n secure-app

# Step 1: Create TLS certificate and secret
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=webapp.local"

kubectl create secret tls webapp-tls \
  --cert=tls.crt --key=tls.key \
  -n secure-app

# Step 2: Create secure ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webapp
  namespace: secure-app
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "DENY" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - webapp.local
    secretName: webapp-tls
  rules:
  - host: webapp.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: webapp
            port:
              number: 80
EOF

# Step 3: Verify configuration
kubectl describe ingress webapp -n secure-app

# Step 4: Test (add to /etc/hosts: 127.0.0.1 webapp.local)
# curl -k https://webapp.local -I | grep -E "X-Frame|X-Content|X-XSS"

# Cleanup
kubectl delete namespace secure-app
```

**Критерії успіху**: Ingress використовує TLS та повертає заголовки безпеки.

---

## Підсумок

**Вимоги TLS**:
- Завжди використовуйте TLS для зовнішнього трафіку
- Мінімум TLS 1.2, бажано TLS 1.3
- Зберігайте сертифікати у Kubernetes secrets

**Заголовки безпеки**:
- X-Frame-Options: Запобігання clickjacking
- X-Content-Type-Options: Запобігання підміні MIME
- HSTS: Примусовий HTTPS

**Обмеження швидкості**:
- Захист від DoS-атак
- Налаштування лімітів для окремого ingress

**Найкращі практики**:
- Примусове перенаправлення на HTTPS
- Використовуйте NetworkPolicies з ingress
- Захищайте чутливі шляхи
- Зміцнюйте Pod контролера ingress

---

## Наступний модуль

[Модуль 1.4: Захист метаданих вузлів](module-1.4-node-metadata/) — Захист сервісів метаданих хмарного провайдера.
