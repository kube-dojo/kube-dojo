---
title: "\u041f\u0456\u0434\u0441\u0443\u043c\u043a\u043e\u0432\u0438\u0439 \u0442\u0435\u0441\u0442 \u0447\u0430\u0441\u0442\u0438\u043d\u0438 4: \u0421\u0435\u0440\u0435\u0434\u043e\u0432\u0438\u0449\u0435 \u0437\u0430\u0441\u0442\u043e\u0441\u0443\u043d\u043a\u0456\u0432, \u043a\u043e\u043d\u0444\u0456\u0433\u0443\u0440\u0430\u0446\u0456\u044f \u0442\u0430 \u0431\u0435\u0437\u043f\u0435\u043a\u0430"
sidebar:
  order: 7
calque_review:
  reviewed_at: "2026-06-24"
  detector_version: "v2"
  status: "reviewed"
  flags_resolved: 13
  content_sha: "5b8822680595d31144f13b476afd82623e59b2c64b2e3383707c2546f8ff9c58"
---
> **Обмеження часу**: 25 хвилин (симуляція тиску іспиту)
>
> **Прохідний бал**: 80% (8/10 запитань)

Цей тест перевіряє ваші знання з:
- ConfigMaps та Secrets
- Вимог та лімітів ресурсів
- SecurityContexts
- Сервісних акаунтів
- Custom Resource Definitions

---

## Інструкції

1. Спробуйте відповісти на кожне запитання без підглядання відповідей
2. Засікайте час — швидкість важлива для CKAD
3. Використовуйте лише `kubectl` та `kubernetes.io/docs`
4. Перевірте відповіді після завершення всіх запитань

---

## Запитання

### Запитання 1: ConfigMap з літералів
**[2 хвилини]**

Створіть ConfigMap з назвою `app-settings` з такими значеннями:
- `LOG_LEVEL=debug`
- `MAX_CONNECTIONS=100`
- `ENVIRONMENT=staging`

<details>
<summary>Відповідь</summary>

```bash
k create configmap app-settings \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=MAX_CONNECTIONS=100 \
  --from-literal=ENVIRONMENT=staging
```

</details>

---

### Запитання 2: Secret як змінна оточення
**[3 хвилини]**

Створіть Secret з назвою `db-creds` зі значеннями `username=admin` та `password=secret123`. Потім створіть Под з назвою `db-client` з nginx, який має ці значення як змінні оточення `DB_USER` та `DB_PASS`.

<details>
<summary>Відповідь</summary>

```bash
k create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secret123

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: db-client
spec:
  containers:
  - name: nginx
    image: nginx
    env:
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: username
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
EOF
```

</details>

---

### Запитання 3: Ліміти ресурсів
**[2 хвилини]**

Створіть Под з назвою `limited-pod` з nginx, який має:
- Запит пам'яті: 128Mi
- Ліміт пам'яті: 256Mi
- Запит CPU: 100m
- Ліміт CPU: 200m

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: limited-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
EOF
```

</details>

---

### Запитання 4: SecurityContext — Запуск від не-root
**[3 хвилини]**

Створіть Под з назвою `secure-pod` з busybox, який:
- Працює від користувача з ID 1000
- Працює від групи з ID 3000
- Має `fsGroup` встановлений у 2000
- Виконує команду `id && sleep 3600`

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: busybox
    image: busybox
    command: ['sh', '-c', 'id && sleep 3600']
EOF
```

Перевірка: `k logs secure-pod` має показати `uid=1000 gid=3000 groups=2000,3000`

</details>

---

### Запитання 5: ConfigMap як том
**[3 хвилини]**

Створіть ConfigMap з назвою `nginx-config` з таким вмістом:
```
server {
    listen 8080;
    location / {
        return 200 'ConfigMap works!\n';
    }
}
```

Потім створіть Под з назвою `nginx-custom`, який монтує цей ConfigMap до `/etc/nginx/conf.d/default.conf`.

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' > /tmp/default.conf
server {
    listen 8080;
    location / {
        return 200 'ConfigMap works!\n';
    }
}
EOF

k create configmap nginx-config --from-file=/tmp/default.conf

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx-custom
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: default.conf
  volumes:
  - name: config
    configMap:
      name: nginx-config
EOF
```

</details>

---

### Запитання 6: Сервісний акаунт
**[2 хвилини]**

Створіть Сервісний акаунт з назвою `app-sa` та Под з назвою `app-pod` з nginx, який використовує цей Сервісний акаунт.

<details>
<summary>Відповідь</summary>

```bash
k create sa app-sa

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  serviceAccountName: app-sa
  containers:
  - name: nginx
    image: nginx
EOF

# Перевірка
k get pod app-pod -o jsonpath='{.spec.serviceAccountName}'
```

</details>

---

### Запитання 7: Декодування Secret
**[1 хвилина]**

Secret з назвою `api-secret` існує з ключем `api-key`. Як декодувати та відобразити його значення?

<details>
<summary>Відповідь</summary>

```bash
k get secret api-secret -o jsonpath='{.data.api-key}' | base64 -d
echo  # новий рядок
```

</details>

---

### Запитання 8: Видалення capabilities
**[3 хвилини]**

Створіть Под з назвою `minimal-caps` з nginx, який:
- Видаляє ВСІ capabilities
- Додає лише capability `NET_BIND_SERVICE`
- Запобігає ескалації привілеїв

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: minimal-caps
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
EOF
```

</details>

---

### Запитання 9: Клас QoS
**[2 хвилини]**

Створіть Под з назвою `guaranteed-pod` з nginx, який має клас QoS Guaranteed. Яка конфігурація ресурсів потрібна?

<details>
<summary>Відповідь</summary>

Для QoS Guaranteed запити повинні дорівнювати лімітам як для CPU, так і для пам'яті:

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "100m"
EOF

# Перевірка
k get pod guaranteed-pod -o jsonpath='{.status.qosClass}'
# Має вивести: Guaranteed
```

</details>

---

### Запитання 10: Custom Resource
**[3 хвилини]**

Враховуючи, що CRD для `databases.example.com` існує, створіть Custom Resource:
- Назва: `production-db`
- Kind: `Database`
- apiVersion: `example.com/v1`
- spec.engine: `postgres`
- spec.replicas: `3`

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: example.com/v1
kind: Database
metadata:
  name: production-db
spec:
  engine: postgres
  replicas: 3
EOF

# Перевірка
k get databases
k describe database production-db
```

</details>

---

## Оцінювання

| Правильних відповідей | Бал | Статус |
|-----------------------|-----|--------|
| 10/10 | 100% | Відмінно — готові до іспиту |
| 8–9/10 | 80–90% | Добре — потрібен незначний перегляд |
| 6–7/10 | 60–70% | Перегляньте слабкі місця |
| <6/10 | <60% | Поверніться до модулів частини 4 |

---

## Очищення

```bash
k delete configmap app-settings nginx-config 2>/dev/null
k delete secret db-creds api-secret 2>/dev/null
k delete pod db-client limited-pod secure-pod nginx-custom app-pod minimal-caps guaranteed-pod 2>/dev/null
k delete sa app-sa 2>/dev/null
k delete database production-db 2>/dev/null
```

---

## Ключові висновки

Якщо ви набрали менше 80%, перегляньте ці теми:

- **Помилки в Q1, Q5**: Перегляньте [Модуль 4.1](/uk/k8s/ckad/part4-environment/module-4.1-configmaps/) (ConfigMaps) — створення та монтування томів
- **Помилки в Q2, Q7**: Перегляньте [Модуль 4.2](/uk/k8s/ckad/part4-environment/module-4.2-secrets/) (Secrets) — змінні оточення та декодування
- **Помилки в Q3, Q9**: Перегляньте [Модуль 4.3](/uk/k8s/ckad/part4-environment/module-4.3-resources/) (Ресурси) — запити, ліміти, QoS
- **Помилки в Q4, Q8**: Перегляньте [Модуль 4.4](/uk/k8s/ckad/part4-environment/module-4.4-securitycontext/) (SecurityContexts) — користувач/група, capabilities
- **Помилки в Q6**: Перегляньте [Модуль 4.5](/uk/k8s/ckad/part4-environment/module-4.5-serviceaccounts/) (Сервісні акаунти) — створення та призначення
- **Помилки в Q10**: Перегляньте [Модуль 4.6](/uk/k8s/ckad/part4-environment/module-4.6-crds/) (CRDs) — власні ресурси

---

## Наступна частина

[Частина 5: Сервіси та мережа](/uk/k8s/ckad/part5-networking/module-5.1-services/) — Сервіси, Ingress та мережеві політики.
