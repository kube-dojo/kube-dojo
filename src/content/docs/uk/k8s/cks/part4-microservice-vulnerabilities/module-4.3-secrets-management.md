---
title: "Модуль 4.3: Управління секретами"
slug: uk/k8s/cks/part4-microservice-vulnerabilities/module-4.3-secrets-management
sidebar:
  order: 3
---
> **Складність**: `[MEDIUM]` — критична навичка CKS
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Модуль 4.2 (Pod Security Admission), основи RBAC

---

## Чому цей модуль важливий

Kubernetes Secrets зберігають конфіденційні дані, такі як паролі, ключі API та сертифікати. За замовчуванням вони лише кодуються в base64 (не шифруються!) і доступні будь-кому з відповідними дозволами RBAC. Належне управління секретами запобігає витоку облікових даних та підвищенню привілеїв.

CKS значною мірою тестує практики безпеки секретів.

---

## Проблеми безпеки секретів

```
┌─────────────────────────────────────────────────────────────┐
│              БЕЗПЕКА СЕКРЕТІВ ЗА ЗАМОВЧУВАННЯМ               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Base64 — це НЕ шифрування!                                │
│  ─────────────────────────────────────────────────────────  │
│  $ echo "mysecretpassword" | base64                        │
│  bXlzZWNyZXRwYXNzd29yZAo=                                  │
│                                                             │
│  $ echo "bXlzZWNyZXRwYXNzd29yZAo=" | base64 -d            │
│  mysecretpassword                                          │
│                                                             │
│  Проблеми секретів за замовчуванням:                        │
│  ├── Зберігаються нешифрованими в etcd                     │
│  ├── Видимі для всіх з дозволом get secrets                │
│  ├── Відображаються в специфікаціях Pod (kubectl describe) │
│  ├── Можуть потрапити в журнали аудиту                     │
│  └── Монтуються як текстові файли в контейнерах           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Створення секретів

### Generic Secret

```bash
# From literal values
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secretpass123

# From files
kubectl create secret generic ssh-key \
  --from-file=id_rsa=/path/to/id_rsa \
  --from-file=id_rsa.pub=/path/to/id_rsa.pub

# From env file
kubectl create secret generic app-config \
  --from-env-file=secrets.env
```

### TLS Secret

```bash
# Create TLS secret
kubectl create secret tls web-tls \
  --cert=server.crt \
  --key=server.key
```

### Docker Registry Secret

```bash
# Create registry credential
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=password \
  --docker-email=user@example.com
```

---

## Використання секретів у Pod

### Змінні середовища

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-env-pod
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
```

### Монтування томів (рекомендовано)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-volume-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
      # Optional: set specific permissions
      defaultMode: 0400
```

### Чому монтування томів краще

```
┌─────────────────────────────────────────────────────────────┐
│              ЗМІННІ СЕРЕДОВИЩА проти МОНТУВАННЯ ТОМІВ        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Змінні середовища:                                        │
│  ├── Видимі в /proc/<pid>/environ                          │
│  ├── Можуть потрапити до дочірніх процесів                 │
│  ├── Часто логуються додатками                             │
│  └── Видимі в 'docker inspect'                             │
│                                                             │
│  Монтування томів:                                         │
│  ├── Файли з обмеженими правами доступу                    │
│  ├── tmpfs (у пам'яті, не записуються на диск)            │
│  ├── Автоматично оновлюються при зміні секрету             │
│  └── Контрольований доступ через права файлів              │
│                                                             │
│  Найкраща практика: завжди використовуйте монтування томів │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Шифрування у стані спокою

### Перевірка поточного стану шифрування

```bash
# Check API server configuration
ps aux | grep kube-apiserver | grep encryption-provider-config

# Or check the manifest
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep encryption
```

### Увімкнення шифрування etcd

```yaml
# /etc/kubernetes/enc/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      # aescbc - recommended for production
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      # identity is the fallback (unencrypted)
      - identity: {}
```

### Генерація ключа шифрування

```bash
# Generate random 32-byte key
head -c 32 /dev/urandom | base64

# Example output (use your own!):
# K8sSecretEncryptionKey1234567890ABCDEF==
```

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
    # Add this flag
    - --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml
    volumeMounts:
    # Mount the encryption config
    - mountPath: /etc/kubernetes/enc
      name: enc
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/enc
      type: DirectoryOrCreate
    name: enc
```

### Перевірка роботи шифрування

```bash
# Create a test secret
kubectl create secret generic test-encryption --from-literal=mykey=myvalue

# Read directly from etcd (on control plane)
ETCDCTL_API=3 etcdctl get /registry/secrets/default/test-encryption \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key | hexdump -C

# If encrypted: You'll see random bytes, not readable text
# If NOT encrypted: You'll see "mykey" and "myvalue" in plain text
```

### Повторне шифрування наявних секретів

```bash
# After enabling encryption, re-encrypt all existing secrets
kubectl get secrets -A -o json | kubectl replace -f -
```

---

## Провайдери шифрування

```
┌─────────────────────────────────────────────────────────────┐
│              ПРОВАЙДЕРИ ШИФРУВАННЯ                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  identity (за замовчуванням)                                │
│  └── Без шифрування, відкрите зберігання                   │
│                                                             │
│  aescbc (рекомендований)                                   │
│  └── AES-CBC з доповненням PKCS#7                          │
│      Надійний, широко підтримуваний                        │
│                                                             │
│  aesgcm                                                    │
│  └── Автентифіковане шифрування AES-GCM                    │
│      Швидший, потрібна ротація ключів кожні 200K записів   │
│                                                             │
│  kms                                                       │
│  └── Зовнішній KMS провайдер (AWS KMS, Azure Key Vault)   │
│      Найкращий для продакшену, ключі не потрапляють в etcd │
│                                                             │
│  secretbox                                                 │
│  └── XSalsa20 + Poly1305                                   │
│      Надійний, фіксований розмір nonce                     │
│                                                             │
│  Порядок має значення: перший провайдер шифрує нові секрети│
│  Всі перелічені провайдери можуть дешифрувати              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## RBAC для секретів

### Обмеження доступу до секретів

```yaml
# Only allow access to specific secrets
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["app-config", "db-creds"]  # Specific secrets only
  verbs: ["get"]
```

### Небезпечні шаблони RBAC

```yaml
# НЕ РОБІТЬ ЦЕ - надає доступ до ВСІХ секретів
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dangerous-role
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]  # Can read ALL secrets cluster-wide!
```

### Аудит доступу до секретів

```bash
# Find who can access secrets
kubectl auth can-i get secrets --as=system:serviceaccount:default:default
kubectl auth can-i list secrets --as=system:serviceaccount:kube-system:default

# List all roles that can access secrets
kubectl get clusterroles -o json | jq '.items[] | select(.rules[]?.resources[]? == "secrets") | .metadata.name'
```

---

## Запобігання витоку секретів

### Вимкнення автоматичного монтування секретів

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-automount-pod
spec:
  automountServiceAccountToken: false  # Don't mount SA token
  containers:
  - name: app
    image: nginx
```

### Використання монтування тільки для читання

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readonly-secrets
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true  # Prevent modification
  volumes:
  - name: secrets
    secret:
      secretName: app-secrets
      defaultMode: 0400  # Read-only for owner
```

---

## Реальні сценарії іспиту

### Сценарій 1: Увімкнення шифрування etcd

```bash
# Step 1: Create encryption config directory
sudo mkdir -p /etc/kubernetes/enc

# Step 2: Generate encryption key
ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)

# Step 3: Create encryption config
sudo tee /etc/kubernetes/enc/encryption-config.yaml << EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}
EOF

# Step 4: Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Add to command:
# - --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml

# Add volume mount:
# volumeMounts:
# - mountPath: /etc/kubernetes/enc
#   name: enc
#   readOnly: true

# Add volume:
# volumes:
# - hostPath:
#     path: /etc/kubernetes/enc
#     type: DirectoryOrCreate
#   name: enc

# Step 5: Wait for API server to restart
kubectl get nodes  # Wait until this works

# Step 6: Re-encrypt existing secrets
kubectl get secrets -A -o json | kubectl replace -f -
```

### Сценарій 2: Виправлення RBAC для секретів

```bash
# Find ServiceAccount with too much secret access
kubectl get rolebindings,clusterrolebindings -A -o json | \
  jq -r '.items[] | select(.roleRef.name | contains("secret")) |
         "\(.metadata.namespace // "cluster")/\(.metadata.name) -> \(.roleRef.name)"'

# Create restrictive role
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-secret-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["app-config"]  # Only this secret
  verbs: ["get"]
EOF
```

### Сценарій 3: Створення секрету з файлу

```bash
# Create secret containing certificate
kubectl create secret generic tls-cert \
  --from-file=tls.crt=./server.crt \
  --from-file=tls.key=./server.key \
  -n production

# Use in pod with volume mount
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: tls
      mountPath: /etc/tls
      readOnly: true
  volumes:
  - name: tls
    secret:
      secretName: tls-cert
      defaultMode: 0400
EOF
```

---

## Зовнішнє управління секретами

```
┌─────────────────────────────────────────────────────────────┐
│              ЗОВНІШНІ РІШЕННЯ ДЛЯ СЕКРЕТІВ                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HashiCorp Vault                                           │
│  └── Галузевий стандарт, багаті можливості                 │
│      Vault Agent Injector для Kubernetes                   │
│                                                             │
│  AWS Secrets Manager + External Secrets Operator           │
│  └── Нативна інтеграція з AWS                              │
│      Синхронізує секрети AWS до Kubernetes                  │
│                                                             │
│  Azure Key Vault                                           │
│  └── Нативне рішення Azure                                 │
│      Доступний CSI driver                                  │
│                                                             │
│  Sealed Secrets (Bitnami)                                  │
│  └── Шифрування секретів для зберігання в Git              │
│      Тільки кластер може дешифрувати                       │
│                                                             │
│  Примітка: Зовнішні рішення НЕ входять до іспиту CKS,     │
│  але їх розуміння демонструє зрілість у безпеці            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **Base64 — це лише кодування**, а не шифрування. Будь-хто може його декодувати. Іспит CKS перевіряє, чи розумієте ви цю критичну відмінність.

- **etcd зберігає секрети відкритим текстом за замовчуванням**. Без шифрування у стані спокою будь-хто з доступом до etcd може прочитати всі секрети кластера.

- **Секрети, змонтовані як томи**, зберігаються в tmpfs (пам'яті), а не на диску. Вони безпечніші за змінні середовища.

- **Порядок конфігурації шифрування має значення**. Нові секрети шифруються першим провайдером. Всі перелічені провайдери можуть дешифрувати, що дозволяє ротацію ключів.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Вважати base64 безпечним | Дані відкриті | Увімкнути шифрування у стані спокою |
| Використовувати змінні середовища | Витік у логи | Використовувати монтування томів |
| Широкий RBAC для секретів | Будь-який Pod може прочитати | Використовувати resourceNames |
| Не перешифровувати після увімкнення | Старі секрети нешифровані | Виконати kubectl replace |
| Секрети в Git | Постійний витік | Використовувати Sealed Secrets |

---

## Тест

1. **Чи є кодування base64 шифруванням?**
   <details>
   <summary>Відповідь</summary>
   Ні! Base64 — це зворотне кодування, а не шифрування. Будь-хто може декодувати його за допомогою `base64 -d`. Секрети потребують шифрування у стані спокою для справжньої безпеки.
   </details>

2. **Де слід зберігати конфігурацію шифрування?**
   <details>
   <summary>Відповідь</summary>
   На вузлі площини управління, зазвичай `/etc/kubernetes/enc/encryption-config.yaml`, із посиланням через прапорець API server `--encryption-provider-config`.
   </details>

3. **Чому монтування томів переважає над змінними середовища для секретів?**
   <details>
   <summary>Відповідь</summary>
   Монтування томів: зберігаються в tmpfs (пам'яті), мають права доступу до файлів, автоматично оновлюються при зміні секрету. Змінні середовища: видимі в /proc, можуть потрапити до дочірніх процесів, часто логуються.
   </details>

4. **Як перевірити, що секрети зашифровані в etcd?**
   <details>
   <summary>Відповідь</summary>
   Прочитати безпосередньо з etcd за допомогою etcdctl. Якщо зашифровано, ви побачите випадкові байти. Якщо не зашифровано, ви побачите значення секретів відкритим текстом.
   </details>

---

## Практична вправа

**Завдання**: Увімкнути шифрування у стані спокою та перевірити його роботу.

```bash
# Step 1: Check current encryption status
ps aux | grep kube-apiserver | grep encryption-provider-config || echo "Not configured"

# Step 2: Create test secret BEFORE encryption
kubectl create secret generic pre-encryption --from-literal=test=beforeencryption

# Step 3: Create encryption config (on control plane node)
sudo mkdir -p /etc/kubernetes/enc

ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)
sudo tee /etc/kubernetes/enc/encryption-config.yaml << EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}
EOF

# Step 4: Backup API server manifest
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/kube-apiserver.yaml.bak

# Step 5: Edit API server manifest (add encryption config)
# Add: --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml
# Add volume and volumeMount for /etc/kubernetes/enc

# Step 6: Wait for API server restart
sleep 30
kubectl get nodes

# Step 7: Create test secret AFTER encryption
kubectl create secret generic post-encryption --from-literal=test=afterencryption

# Step 8: Re-encrypt pre-existing secret
kubectl get secret pre-encryption -o json | kubectl replace -f -

# Step 9: Verify in etcd (if you have access)
# Encrypted secrets show random bytes, not plain text

# Cleanup
kubectl delete secret pre-encryption post-encryption
```

**Критерії успіху**: Розуміти конфігурацію та перевірку шифрування.

---

## Підсумок

**Проблеми безпеки секретів**:
- Base64 — це НЕ шифрування
- etcd зберігає відкритий текст за замовчуванням
- Змінні середовища мають витоки

**Найкращі практики**:
- Увімкнути шифрування у стані спокою (aescbc)
- Використовувати монтування томів, а не змінні середовища
- Обмежити RBAC за допомогою resourceNames
- Перешифрувати після увімкнення шифрування

**Налаштування шифрування**:
- Створити EncryptionConfiguration
- Додати прапорець API server
- Перезапустити API server
- Перешифрувати наявні секрети

**Поради для іспиту**:
- Знайте формат конфігурації шифрування
- Розумійте порядок провайдерів
- Вмійте перевірити роботу шифрування

---

## Наступний модуль

[Модуль 4.4: Ізоляція середовища виконання](module-4.4-runtime-sandboxing/) — gVisor та Kata Containers для ізоляції контейнерів.
