---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 6: ConfigMaps \u0442\u0430 Secrets"
sidebar:
  order: 7
---
> **Складність**: `[MEDIUM]` — Основи керування конфігурацією
>
> **Час на виконання**: 35–40 хвилин
>
> **Передумови**: Модуль 3 (Поди)

---

## Чому цей модуль важливий

Застосунки потребують конфігурації: URL-адреси баз даних, прапорці функцій, API-ключі, облікові дані. Жорстко прописувати їх у образах контейнерів — погана практика. ConfigMaps та Secrets дозволяють керувати конфігурацією окремо від коду вашого застосунку.

---

## ConfigMaps проти Secrets

```
┌─────────────────────────────────────────────────────────────┐
│              CONFIGMAPS проти SECRETS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap                     │  Secret                    │
│  ─────────────────────────────│────────────────────────────│
│  Нечутливі дані               │  Чутливі дані             │
│  Зберігання у відкритому тексті│  Кодування Base64         │
│  Середовище, конфіг-файли      │  Паролі, токени, ключі    │
│                                │                            │
│  Приклади:                     │  Приклади:                │
│  • Рівні логування             │  • Паролі до баз даних    │
│  • Прапорці функцій            │  • API-ключі              │
│  • Вміст конфіг-файлів         │  • TLS-сертифікати        │
│                                                             │
│  Увага: Secrets НЕ шифруються за замовчуванням!             │
│  Base64 — це кодування, а не шифрування.                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ConfigMaps

### Створення ConfigMaps

```bash
# З літеральних значень
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=ENVIRONMENT=staging

# З файлу
kubectl create configmap nginx-config --from-file=nginx.conf

# З директорії (кожен файл стає ключем)
kubectl create configmap configs --from-file=./config-dir/

# Перегляд ConfigMap
kubectl get configmap app-config -o yaml
```

### ConfigMap YAML

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "debug"
  ENVIRONMENT: "staging"
  config.json: |
    {
      "database": "localhost",
      "port": 5432
    }
```

### Використання ConfigMaps

**Як змінні середовища:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    env:
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: LOG_LEVEL
    # Або всі ключі одразу:
    envFrom:
    - configMapRef:
        name: app-config
```

**Як том (файли):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d
  volumes:
  - name: config
    configMap:
      name: nginx-config
```

---

## Secrets

### Створення Secrets

```bash
# З літеральних значень
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secret123

# З файлу
kubectl create secret generic tls-cert \
  --from-file=cert.pem \
  --from-file=key.pem

# Перегляд secret (закодований у base64)
kubectl get secret db-creds -o yaml

# Декодування значення
kubectl get secret db-creds -o jsonpath='{.data.password}' | base64 -d
```

### Secret YAML

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque              # Загальний тип secret
data:                     # Закодовано у Base64
  username: YWRtaW4=      # echo -n 'admin' | base64
  password: c2VjcmV0MTIz  # echo -n 'secret123' | base64
---
# Або використовуйте stringData для відкритого тексту (K8s закодує його)
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
stringData:               # Відкритий текст, автоматичне кодування
  username: admin
  password: secret123
```

### Використання Secrets

**Як змінні середовища:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
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
```

**Як том (файли):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
```

---

## Візуалізація

```
┌─────────────────────────────────────────────────────────────┐
│          ВИКОРИСТАННЯ CONFIGMAP/SECRET                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap/Secret                                          │
│  ┌─────────────────────┐                                   │
│  │ data:               │                                   │
│  │   KEY1: value1      │                                   │
│  │   KEY2: value2      │                                   │
│  └──────────┬──────────┘                                   │
│             │                                               │
│    ┌────────┴────────┐                                     │
│    ▼                 ▼                                      │
│                                                             │
│  Як змінні           Як том                                │
│  середовища          (файли)                               │
│  ┌────────────┐     ┌────────────────────┐                │
│  │ env:       │     │ /etc/config/       │                │
│  │   KEY1=val1│     │   KEY1  (файл)     │                │
│  │   KEY2=val2│     │   KEY2  (файл)     │                │
│  └────────────┘     └────────────────────┘                │
│                                                             │
│  envFrom для         volumes для                           │
│  простих пар         конфіг-файлів                         │
│  ключ-значення                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Практичний приклад

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
data:
  LOG_LEVEL: "info"
  CACHE_TTL: "3600"
---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
stringData:
  DB_PASSWORD: "supersecret"
  API_KEY: "abc123"
---
# Под, що використовує обидва
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
  - name: app
    image: myapp:v1
    envFrom:
    - configMapRef:
        name: app-settings
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: DB_PASSWORD
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: API_KEY
```

---

## Чи знали ви?

- **Secrets НЕ шифруються у стані спокою за замовчуванням.** Вони лише закодовані у base64. Увімкніть шифрування у стані спокою для справжньої безпеки.

- **Оновлення ConfigMap/Secret не перезапускають поди автоматично.** Змонтовані томи оновлюються, але змінні середовища потребують перезапуску пода.

- **Максимальний розмір — 1 МБ.** І ConfigMaps, і Secrets обмежені 1 МБ даних.

- **Secrets зберігаються в etcd.** Будь-хто з доступом до etcd може їх прочитати. Використовуйте RBAC для обмеження доступу.

---

## Типові помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Коміт секретів у Git | Порушення безпеки | Використовуйте sealed-secrets або зовнішнє керування секретами |
| Думати, що base64 = шифрування | Хибна безпека | Увімкніть шифрування у стані спокою |
| Не використовувати stringData | Помилки при ручному кодуванні base64 | Використовуйте `stringData` для відкритого тексту |
| Жорстке кодування в образах | Неможливо змінити без перезбірки | Використовуйте ConfigMaps/Secrets |

---

## Тест

1. **Яка різниця між ConfigMaps та Secrets?**
   <details>
   <summary>Відповідь</summary>
   ConfigMaps призначені для нечутливих конфігураційних даних (відкритий текст). Secrets — для чутливих даних (закодовані у base64). Обидва можна використовувати як змінні середовища або монтувати як файли.
   </details>

2. **Як декодувати значення Secret?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get secret NAME -o jsonpath='{.data.KEY}' | base64 -d`. Дані закодовані у base64, а не зашифровані.
   </details>

3. **Що відбувається з подами при оновленні ConfigMap?**
   <details>
   <summary>Відповідь</summary>
   Якщо змонтовано як том — файли оновлюються автоматично (може зайняти до хвилини). Змінні середовища не оновлюються — поди потрібно перезапустити для отримання нових значень.
   </details>

4. **Яка перевага використання `stringData` у Secrets?**
   <details>
   <summary>Відповідь</summary>
   Ви можете писати відкритий текст, і Kubernetes автоматично кодує його у base64. Не потрібно ручного кодування — менше помилок.
   </details>

---

## Практична вправа

**Завдання**: Створіть та використайте ConfigMaps та Secrets.

```bash
# 1. Створіть ConfigMap
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=APP_NAME=myapp

# 2. Створіть Secret
kubectl create secret generic app-secret \
  --from-literal=DB_PASS=secretpassword

# 3. Створіть под, що використовує обидва
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: config-test
spec:
  containers:
  - name: test
    image: busybox
    command: ['sh', '-c', 'env && sleep 3600']
    envFrom:
    - configMapRef:
        name: app-config
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: DB_PASS
EOF

# 4. Перевірте змінні середовища
kubectl logs config-test | grep -E "LOG_LEVEL|APP_NAME|DB_PASSWORD"

# 5. Очищення
kubectl delete pod config-test
kubectl delete configmap app-config
kubectl delete secret app-secret
```

**Критерії успіху**: У логах пода відображаються всі змінні середовища.

---

## Підсумок

ConfigMaps та Secrets виносять конфігурацію назовні:

**ConfigMaps**:
- Нечутливі дані
- Зберігання у відкритому тексті
- Використовуйте для конфігураційних значень та файлів

**Secrets**:
- Чутливі дані
- Кодування Base64 (НЕ шифрування)
- Використовуйте для паролів, ключів, токенів

**Шаблони використання**:
- Змінні середовища (env, envFrom)
- Монтування томів (файли)

---

## Наступний модуль

[Модуль 7: Простори імен та мітки](module-1.7-namespaces-labels/) — Організація вашого кластера.
