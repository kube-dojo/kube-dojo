---
title: "Модуль 6.1: Журнали аудиту Kubernetes"
slug: uk/k8s/cks/part6-runtime-security/module-6.1-audit-logging
sidebar:
  order: 1
---
> **Складність**: `[MEDIUM]` — критична навичка CKS
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Основи API server, вільне володіння JSON/YAML

---

## Чому цей модуль важливий

Журнали аудиту записують всі запити до Kubernetes API server. Вони є вашим основним інструментом для розслідування інцидентів безпеки — хто що зробив, коли та звідки. Без журналів аудиту ви працюєте наосліп.

CKS значною мірою тестує конфігурацію та аналіз журналів аудиту.

---

## Що підлягає аудиту

```
┌─────────────────────────────────────────────────────────────┐
│              ЖУРНАЛИ АУДИТУ KUBERNETES                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Кожен API-запит логується:                                │
│                                                             │
│  ХТО (інформація про користувача):                         │
│  ├── user.username                                         │
│  ├── user.groups                                           │
│  └── serviceAccountName                                    │
│                                                             │
│  ЩО (деталі запиту):                                      │
│  ├── verb (create, get, list, delete тощо)                │
│  ├── resource (pods, secrets, deployments)                 │
│  ├── namespace                                             │
│  └── requestURI                                            │
│                                                             │
│  КОЛИ (час):                                               │
│  ├── requestReceivedTimestamp                              │
│  └── stageTimestamp                                        │
│                                                             │
│  ЗВІДКИ (джерело):                                         │
│  └── sourceIPs                                             │
│                                                             │
│  РЕЗУЛЬТАТ:                                                │
│  ├── responseStatus.code                                   │
│  └── responseStatus.reason                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Рівні аудиту

```
┌─────────────────────────────────────────────────────────────┐
│              РІВНІ АУДИТУ                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  None                                                      │
│  └── Не логувати цю подію                                  │
│                                                             │
│  Metadata                                                  │
│  └── Логувати лише метадані запиту                         │
│      (користувач, час, ресурс, дія)                        │
│      БЕЗ тіла запиту або відповіді                         │
│                                                             │
│  Request                                                   │
│  └── Логувати метадані + тіло запиту                       │
│      Корисно для операцій create/update                     │
│      БЕЗ тіла відповіді                                   │
│                                                             │
│  RequestResponse                                           │
│  └── Логувати метадані + тіло запиту + тіло відповіді     │
│      Найдетальніший, найбільші логи                        │
│      Використовуйте помірковано (може бути величезним)     │
│                                                             │
│  Вищі рівні = більші логи = більше сховища                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Етапи аудиту

```
┌─────────────────────────────────────────────────────────────┐
│              ЕТАПИ АУДИТУ                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RequestReceived                                           │
│  └── Щойно запит отримано                                  │
│      До будь-якої обробки                                  │
│                                                             │
│  ResponseStarted                                           │
│  └── Заголовки відповіді надіслано, тіло ще ні            │
│      Тільки для довготривалих запитів (watch, exec)        │
│                                                             │
│  ResponseComplete                                          │
│  └── Тіло відповіді повне, більше байтів не буде          │
│      Найпоширеніший етап для логування                     │
│                                                             │
│  Panic                                                     │
│  └── Паніка під час обробки запиту                         │
│      Завжди логується, коли трапляється                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Політика аудиту

### Базова структура політики аудиту

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Don't log read-only requests to certain endpoints
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
      - group: ""
        resources: ["endpoints", "services", "services/status"]

  # Log secrets at Metadata level only (don't log secret data!)
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]

  # Log pod changes at Request level
  - level: Request
    resources:
      - group: ""
        resources: ["pods"]
    verbs: ["create", "update", "patch", "delete"]

  # Log everything else at Metadata level
  - level: Metadata
    omitStages:
      - "RequestReceived"
```

### Рекомендована політика, орієнтована на безпеку

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Don't log requests to certain non-sensitive endpoints
  - level: None
    nonResourceURLs:
      - /healthz*
      - /version
      - /readyz
      - /livez

  # Don't log kube-system service account watches
  - level: None
    users:
      - "system:kube-controller-manager"
      - "system:kube-scheduler"
      - "system:serviceaccount:kube-system:*"
    verbs: ["get", "watch", "list"]

  # Log authentication failures
  - level: RequestResponse
    resources:
      - group: "authentication.k8s.io"
        resources: ["tokenreviews"]

  # Log secret access at metadata only (NEVER log secret data)
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  # Log RBAC changes (who changed permissions?)
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
    verbs: ["create", "update", "patch", "delete"]

  # Log pod exec/attach (potential shell access)
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]

  # Log node modifications
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["nodes", "nodes/status"]
    verbs: ["create", "update", "patch", "delete"]

  # Default: Metadata for everything else
  - level: Metadata
    omitStages:
      - "RequestReceived"
```

---

## Увімкнення журналів аудиту

### Налаштування API Server

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    # Audit policy file
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    # Log to file
    - --audit-log-path=/var/log/kubernetes/audit/audit.log
    # Log rotation
    - --audit-log-maxage=30        # days to keep
    - --audit-log-maxbackup=10     # files to keep
    - --audit-log-maxsize=100      # MB per file
    volumeMounts:
    - mountPath: /etc/kubernetes/audit-policy.yaml
      name: audit-policy
      readOnly: true
    - mountPath: /var/log/kubernetes/audit/
      name: audit-log
  volumes:
  - hostPath:
      path: /etc/kubernetes/audit-policy.yaml
      type: File
    name: audit-policy
  - hostPath:
      path: /var/log/kubernetes/audit/
      type: DirectoryOrCreate
    name: audit-log
```

### Перевірка конфігурації

```bash
# Check API server has audit flags
ps aux | grep kube-apiserver | grep audit

# Check audit log exists
ls -la /var/log/kubernetes/audit/

# Tail the audit log
tail -f /var/log/kubernetes/audit/audit.log | jq .
```

---

## Формат журналу аудиту

### Приклад запису журналу аудиту

```json
{
  "kind": "Event",
  "apiVersion": "audit.k8s.io/v1",
  "level": "RequestResponse",
  "auditID": "12345678-1234-1234-1234-123456789012",
  "stage": "ResponseComplete",
  "requestURI": "/api/v1/namespaces/default/pods",
  "verb": "create",
  "user": {
    "username": "admin",
    "groups": ["system:masters", "system:authenticated"]
  },
  "sourceIPs": ["192.168.1.100"],
  "userAgent": "kubectl/v1.28.0",
  "objectRef": {
    "resource": "pods",
    "namespace": "default",
    "name": "nginx-pod",
    "apiVersion": "v1"
  },
  "responseStatus": {
    "metadata": {},
    "code": 201
  },
  "requestReceivedTimestamp": "2024-01-15T10:30:00.000000Z",
  "stageTimestamp": "2024-01-15T10:30:00.100000Z"
}
```

---

## Аналіз журналів аудиту

### Пошук конкретних подій

```bash
# Find all secret accesses
cat audit.log | jq 'select(.objectRef.resource == "secrets")'

# Find all admin actions
cat audit.log | jq 'select(.user.username == "admin")'

# Find failed requests (non-2xx status)
cat audit.log | jq 'select(.responseStatus.code >= 400)'

# Find pod exec commands
cat audit.log | jq 'select(.objectRef.subresource == "exec")'

# Find requests from specific IP
cat audit.log | jq 'select(.sourceIPs[] == "192.168.1.100")'

# Find RBAC changes
cat audit.log | jq 'select(.objectRef.resource | test("role"))'
```

### Типові запити для розслідування

```bash
# Who created this pod?
cat audit.log | jq 'select(.objectRef.name == "suspicious-pod" and .verb == "create") | {user: .user.username, time: .requestReceivedTimestamp}'

# What did this user do?
cat audit.log | jq 'select(.user.username == "attacker") | {verb: .verb, resource: .objectRef.resource, name: .objectRef.name}'

# All exec into pods in last hour
cat audit.log | jq 'select(.objectRef.subresource == "exec" and .requestReceivedTimestamp > "2024-01-15T09:30:00Z")'

# Who accessed secrets?
cat audit.log | jq 'select(.objectRef.resource == "secrets" and .verb == "get") | {user: .user.username, secret: .objectRef.name, ns: .objectRef.namespace}'
```

---

## Реальні сценарії іспиту

### Сценарій 1: Увімкнення журналів аудиту

```bash
# Step 1: Create audit policy
sudo tee /etc/kubernetes/audit-policy.yaml << 'EOF'
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: None
    nonResourceURLs:
      - /healthz*
      - /version
      - /readyz

  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach"]

  - level: Metadata
    omitStages:
      - "RequestReceived"
EOF

# Step 2: Create log directory
sudo mkdir -p /var/log/kubernetes/audit

# Step 3: Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Step 4: Wait for API server restart
kubectl get nodes

# Step 5: Verify logs are created
ls /var/log/kubernetes/audit/
tail -1 /var/log/kubernetes/audit/audit.log | jq .
```

### Сценарій 2: Розслідування інциденту безпеки

```bash
# Question: Find who deleted the "important" secret from namespace "production"

# Search audit logs
cat /var/log/kubernetes/audit/audit.log | jq '
  select(
    .objectRef.resource == "secrets" and
    .objectRef.name == "important" and
    .objectRef.namespace == "production" and
    .verb == "delete"
  ) | {
    user: .user.username,
    groups: .user.groups,
    sourceIP: .sourceIPs[0],
    time: .requestReceivedTimestamp,
    userAgent: .userAgent
  }
'
```

### Сценарій 3: Створення політики для конфіденційних ресурсів

```yaml
# Audit policy that focuses on sensitive operations
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Skip health checks
  - level: None
    nonResourceURLs: ["/healthz*", "/readyz*", "/livez*"]

  # Log all secret operations
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  # Log all RBAC changes with full details
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["*"]
    verbs: ["create", "update", "patch", "delete"]

  # Log all pod exec/attach with full details
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]

  # Log namespace deletions
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["namespaces"]
    verbs: ["delete"]

  # Default
  - level: Metadata
```

---

## Чи знали ви?

- **Журнали аудиту можуть бути величезними**. Зайнятий кластер може генерувати гігабайти за день. Завжди налаштовуйте ротацію (`--audit-log-maxsize`, `--audit-log-maxbackup`).

- **Ніколи не логуйте дані секретів на рівні Request або RequestResponse**. Значення секретів будуть відкритим текстом у ваших журналах аудиту!

- **Журнали аудиту — ваш слід для криміналістики**. При інциденті безпеки це перше місце для перевірки. Без них ви не зможете довести, що сталося.

- **omitStages: ["RequestReceived"]** вдвічі зменшує обсяг логів. Вам рідко потрібен етап RequestReceived.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Без журналів аудиту | Немає криміналістичного сліду | Увімкніть негайно |
| Логування секретів на рівні Request | Дані секретів у логах | Використовуйте Metadata для секретів |
| Без ротації логів | Диск переповнюється | Встановіть maxsize, maxage, maxbackup |
| Занадто детальна політика | Величезні логи, шум | Використовуйте відповідні рівні |
| Не тестувати політику | Синтаксичні помилки | Застосуйте та перевірте появу логів |

---

## Тест

1. **Яка різниця між рівнями аудиту Metadata та RequestResponse?**
   <details>
   <summary>Відповідь</summary>
   Metadata логує лише метадані запиту (користувач, час, ресурс, дія). RequestResponse також логує повне тіло запиту та відповіді. RequestResponse генерує значно більші логи.
   </details>

2. **Чому секрети ніколи не слід логувати на рівні Request або RequestResponse?**
   <details>
   <summary>Відповідь</summary>
   Тому що значення секретів будуть записані відкритим текстом. Будь-хто з доступом до журналів аудиту зможе прочитати всі секрети. Завжди використовуйте рівень Metadata для секретів.
   </details>

3. **Які прапорці API server потрібні для увімкнення журналів аудиту?**
   <details>
   <summary>Відповідь</summary>
   `--audit-policy-file` (шлях до політики) та `--audit-log-path` (шлях до файлу логу). Необов'язково `--audit-log-maxsize`, `--audit-log-maxbackup`, `--audit-log-maxage` для ротації.
   </details>

4. **Як знайти всі команди pod exec у журналах аудиту?**
   <details>
   <summary>Відповідь</summary>
   `cat audit.log | jq 'select(.objectRef.subresource == "exec")'` — Pod exec логується як підресурс pods.
   </details>

---

## Практична вправа

**Завдання**: Створити та протестувати політику аудиту.

```bash
# Step 1: Create audit policy
cat <<'EOF' > /tmp/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: None
    nonResourceURLs:
      - /healthz*
      - /readyz*
      - /livez*

  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach"]

  - level: Request
    resources:
      - group: ""
        resources: ["pods"]
    verbs: ["create", "delete"]

  - level: Metadata
    omitStages:
      - "RequestReceived"
EOF

echo "=== Audit Policy Created ==="
cat /tmp/audit-policy.yaml

# Step 2: Validate policy syntax
echo "=== Validating Policy ==="
python3 -c "import yaml; yaml.safe_load(open('/tmp/audit-policy.yaml'))" && echo "Valid YAML"

# Step 3: Simulate audit log analysis
cat <<'EOF' > /tmp/sample-audit.json
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"Metadata","auditID":"1","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/secrets/db-password","verb":"get","user":{"username":"developer","groups":["developers"]},"sourceIPs":["10.0.0.5"],"objectRef":{"resource":"secrets","namespace":"default","name":"db-password"},"responseStatus":{"code":200},"requestReceivedTimestamp":"2024-01-15T10:00:00Z"}
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"RequestResponse","auditID":"2","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/pods/web/exec","verb":"create","user":{"username":"admin","groups":["system:masters"]},"sourceIPs":["10.0.0.1"],"objectRef":{"resource":"pods","namespace":"default","name":"web","subresource":"exec"},"responseStatus":{"code":101},"requestReceivedTimestamp":"2024-01-15T10:05:00Z"}
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"Request","auditID":"3","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/pods","verb":"delete","user":{"username":"attacker","groups":[]},"sourceIPs":["192.168.1.100"],"objectRef":{"resource":"pods","namespace":"default","name":"important-pod"},"responseStatus":{"code":200},"requestReceivedTimestamp":"2024-01-15T10:10:00Z"}
EOF

# Step 4: Analyze sample logs
echo "=== Finding Secret Access ==="
cat /tmp/sample-audit.json | jq 'select(.objectRef.resource == "secrets") | {user: .user.username, secret: .objectRef.name}'

echo "=== Finding Pod Exec ==="
cat /tmp/sample-audit.json | jq 'select(.objectRef.subresource == "exec") | {user: .user.username, pod: .objectRef.name}'

echo "=== Finding External IPs ==="
cat /tmp/sample-audit.json | jq 'select(.sourceIPs[] | startswith("192.")) | {user: .user.username, action: .verb, resource: .objectRef.resource}'

# Cleanup
rm -f /tmp/audit-policy.yaml /tmp/sample-audit.json
```

**Критерії успіху**: Зрозуміти конфігурацію політики аудиту та аналіз логів.

---

## Підсумок

**Рівні аудиту**:
- None (без логування)
- Metadata (хто, що, коли)
- Request (+ тіло запиту)
- RequestResponse (+ тіло відповіді)

**Ключова конфігурація**:
- `--audit-policy-file` (шлях до політики)
- `--audit-log-path` (шлях до логу)
- `--audit-log-maxsize/maxbackup/maxage` (ротація)

**Найкращі практики безпеки**:
- Використовуйте Metadata для секретів (ніколи не логуйте дані секретів)
- Логуйте pod/exec на рівні RequestResponse
- Логуйте зміни RBAC на рівні RequestResponse
- Налаштуйте ротацію логів

**Поради для іспиту**:
- Знайте YAML структуру політики
- Розумійте рівні аудиту
- Вмійте робити запити до логів з jq

---

## Наступний модуль

[Модуль 6.2: Безпека виконання з Falco](module-6.2-falco/) — Виявлення підозрілої поведінки контейнерів.
