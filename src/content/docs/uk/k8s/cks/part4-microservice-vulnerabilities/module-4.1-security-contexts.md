---
title: "Модуль 4.1: Контексти безпеки"
slug: uk/k8s/cks/part4-microservice-vulnerabilities/module-4.1-security-contexts
sidebar:
  order: 1
---
> **Складність**: `[MEDIUM]` — основна навичка CKS
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: знання специфікації Pod для CKA, базові концепції безпеки Linux

---

## Чому цей модуль важливий

Контексти безпеки визначають налаштування привілеїв та контролю доступу для Pod та контейнерів. Вони є вашою першою лінією захисту від виходу з контейнера — контролюють, чи працюють контейнери від імені root, чи мають доступ до ресурсів хоста або підвищені привілеї.

CKS значною мірою тестує конфігурацію контексту безпеки.

---

## Що контролюють контексти безпеки

```
┌─────────────────────────────────────────────────────────────┐
│              ОБЛАСТЬ КОНТЕКСТУ БЕЗПЕКИ                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Рівень Pod (spec.securityContext):                        │
│  ├── runAsUser           - UID для всіх контейнерів       │
│  ├── runAsGroup          - GID для всіх контейнерів       │
│  ├── fsGroup             - GID для власності томів         │
│  ├── runAsNonRoot        - Запобігти запуску від root      │
│  ├── supplementalGroups  - Додаткове членство в групах     │
│  ├── seccompProfile      - Профіль Seccomp               │
│  └── sysctls             - Параметри ядра                 │
│                                                             │
│  Рівень контейнера (containers[].securityContext):         │
│  ├── runAsUser           - Перевизначити UID рівня Pod    │
│  ├── runAsGroup          - Перевизначити GID рівня Pod    │
│  ├── runAsNonRoot        - Перевірка для контейнера       │
│  ├── privileged          - Повний доступ до хоста (небезпечно!) │
│  ├── allowPrivilegeEscalation - Запобігти підвищенню привілеїв │
│  ├── capabilities        - Linux capabilities             │
│  ├── readOnlyRootFilesystem - Незмінний контейнер         │
│  ├── seccompProfile      - Seccomp для контейнера        │
│  └── seLinuxOptions      - Мітки SELinux                  │
│                                                             │
│  Налаштування контейнера ПЕРЕВИЗНАЧАЮТЬ налаштування Pod   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Критичні налаштування контексту безпеки

### runAsNonRoot

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: non-root-pod
spec:
  securityContext:
    runAsNonRoot: true  # Pod-level enforcement
  containers:
  - name: app
    image: nginx
    securityContext:
      runAsUser: 1000  # Must specify non-root UID
      runAsGroup: 1000

# If image tries to run as root (UID 0), pod fails to start:
# Error: container has runAsNonRoot and image will run as root
```

### allowPrivilegeEscalation

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-escalation
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false  # Prevent setuid, setgid

# This prevents:
# - setuid binaries from gaining privileges
# - Container processes from becoming root
# - Exploits that rely on privilege escalation
```

### readOnlyRootFilesystem

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readonly-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true  # Can't write to container filesystem
    volumeMounts:
    - name: tmp
      mountPath: /tmp  # Must provide writable volume for temp files
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
```

### privileged (УНИКАЙТЕ!)

```yaml
# НЕ РОБІТЬ ЦЕ у продакшені
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true  # Full access to host!

# privileged: true означає:
# - Доступ до всіх пристроїв хоста
# - Можливість завантажувати модулі ядра
# - Можливість змінювати iptables
# - Можливість повністю вийти з контейнера
# - ВИКОРИСТОВУЙТЕ ТІЛЬКИ для системних демонів (CNI, CSI drivers)
```

---

## Linux Capabilities

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX CAPABILITIES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Capabilities розділяють повноваження root на окремі        │
│  дрібнозернисті одиниці:                                    │
│                                                             │
│  CAP_NET_BIND_SERVICE  - Прив'язка до портів < 1024       │
│  CAP_NET_ADMIN         - Налаштування мережевих інтерфейсів │
│  CAP_NET_RAW           - Використання raw sockets (ping)  │
│  CAP_SYS_ADMIN         - Багато системних викликів (mount) │
│  CAP_SYS_PTRACE        - Налагодження інших процесів      │
│  CAP_CHOWN             - Зміна власника файлів             │
│  CAP_DAC_OVERRIDE      - Обхід прав доступу до файлів     │
│  CAP_SETUID/SETGID     - Зміна UID/GID                    │
│  CAP_KILL              - Надсилання сигналів будь-якому процесу │
│                                                             │
│  Типові capabilities контейнера (Docker):                  │
│  CHOWN, DAC_OVERRIDE, FOWNER, FSETID, KILL,              │
│  SETGID, SETUID, SETPCAP, NET_BIND_SERVICE, NET_RAW,      │
│  SYS_CHROOT, MKNOD, AUDIT_WRITE, SETFCAP                  │
│                                                             │
│  Найкраща практика: скинути ВСІ, додати лише потрібні      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Налаштування Capabilities

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: minimal-caps
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      capabilities:
        drop:
          - ALL  # Drop all capabilities
        add:
          - NET_BIND_SERVICE  # Only add what's needed
```

---

## Повний приклад захищеного Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
      requests:
        memory: "64Mi"
        cpu: "250m"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

---

## Контекст безпеки Pod проти контейнера

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mixed-context
spec:
  securityContext:
    runAsUser: 1000        # Default for all containers
    runAsGroup: 1000
  containers:
  - name: app
    image: myapp
    # Inherits runAsUser: 1000 from pod
  - name: sidecar
    image: sidecar
    securityContext:
      runAsUser: 2000      # Overrides pod-level setting
      # This container runs as UID 2000, not 1000
```

---

## Реальні сценарії іспиту

### Сценарій 1: Виправити Pod, що працює від root

```yaml
# До (небезпечно)
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: nginx

# Після (безпечно)
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
```

### Сценарій 2: Додати мінімальні Capabilities

```bash
# Pod потрібно прив'язатися до порту 80, але не повинен працювати від root
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-server
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: nginx
    image: nginx
    securityContext:
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE  # Allow binding to port 80
      allowPrivilegeEscalation: false
EOF
```

### Сценарій 3: Зробити файлову систему тільки для читання

```bash
# Add read-only filesystem with required writable mounts
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: readonly-nginx
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
EOF
```

---

## Налагодження проблем з контекстом безпеки

```bash
# Check pod's effective security context
kubectl get pod mypod -o yaml | grep -A 20 securityContext

# Check container's security context
kubectl get pod mypod -o jsonpath='{.spec.containers[0].securityContext}' | jq .

# Check if pod failed due to security context
kubectl describe pod mypod | grep -i error

# Common errors:
# "container has runAsNonRoot and image will run as root"
# "unable to write to read-only filesystem"
# "operation not permitted" (missing capability)
```

---

## Чи знали ви?

- **runAsNonRoot не обирає UID за вас.** Якщо образ запускається від root і ви встановили runAsNonRoot: true без runAsUser, Pod не запуститься.

- **Docker за замовчуванням скидає багато capabilities.** Контейнери не отримують повний набір привілеїв root навіть при запуску від UID 0 — але privileged: true повертає все назад.

- **Користувач nobody має UID 65534** на більшості систем. Це поширений вибір для runAsUser, коли у вас немає конкретного користувача.

- **fsGroup змінює власника тому.** Коли ви монтуєте том, Kubernetes змінює групового власника на fsGroup та встановлює права запису для групи.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| runAsNonRoot без runAsUser | Pod не запускається, якщо образ за замовчуванням root | Вказати runAsUser: 1000 |
| Використання privileged: true | Повний доступ до хоста | Ніколи не використовувати без необхідності |
| Не скидати capabilities | Надмірні дозволи | Скинути ALL, додати потрібне |
| Забути emptyDir з readOnly | Додаток не може писати тимчасові файли | Змонтувати записувані томи |
| Тільки контекст на рівні Pod | Контейнер може перевизначити | Встановити на обох рівнях |

---

## Тест

1. **Що станеться, якщо встановити runAsNonRoot: true, але образ запускається від root?**
   <details>
   <summary>Відповідь</summary>
   Pod не запуститься з помилкою "container has runAsNonRoot and image will run as root". Потрібно також вказати runAsUser з ненульовим UID.
   </details>

2. **Що запобігає allowPrivilegeEscalation: false?**
   <details>
   <summary>Відповідь</summary>
   Це запобігає отриманню додаткових привілеїв бінарними файлами setuid/setgid та блокує execve від отримання більше capabilities, ніж має батьківський процес.
   </details>

3. **Як скинути всі Linux capabilities та додати лише NET_BIND_SERVICE?**
   <details>
   <summary>Відповідь</summary>
   ```yaml
   securityContext:
     capabilities:
       drop: ["ALL"]
       add: ["NET_BIND_SERVICE"]
   ```
   </details>

4. **Яке додаткове налаштування потрібне при readOnlyRootFilesystem: true?**
   <details>
   <summary>Відповідь</summary>
   Потрібно змонтувати томи emptyDir для будь-яких шляхів, куди додаток повинен писати (наприклад, /tmp, /var/cache, /var/run).
   </details>

---

## Практична вправа

**Завдання**: Створити повністю захищений Pod.

```bash
# Step 1: Create an insecure pod first
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
EOF

# Step 2: Check its security context
kubectl get pod insecure -o yaml | grep -A 20 securityContext
# (Likely empty or minimal)

# Step 3: Create hardened version
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: hardened
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE
    volumeMounts:
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
  - name: tmp
    emptyDir: {}
EOF

# Step 4: Wait for pods
kubectl wait --for=condition=Ready pod/hardened --timeout=60s

# Step 5: Verify security context
kubectl get pod hardened -o jsonpath='{.spec.securityContext}' | jq .
kubectl get pod hardened -o jsonpath='{.spec.containers[0].securityContext}' | jq .

# Step 6: Test that writing to root filesystem fails
kubectl exec hardened -- touch /etc/test 2>&1 || echo "Write blocked (expected)"

# Step 7: Test that writable volume works
kubectl exec hardened -- touch /tmp/test && echo "Write to /tmp succeeded"

# Cleanup
kubectl delete pod insecure hardened
```

**Критерії успіху**: Захищений Pod запускається з усіма налаштуваннями безпеки.

---

## Підсумок

**Основні налаштування контексту безпеки**:
- `runAsNonRoot: true` + `runAsUser: 1000`
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- `capabilities: drop: [ALL]`

**Ніколи не використовуйте**:
- `privileged: true` (якщо це не абсолютно необхідно)
- Запуск від root без обґрунтування

**Найкращі практики**:
- Встановлюйте на обох рівнях — Pod та контейнера
- Скидайте всі capabilities, додавайте вибірково
- Монтуйте emptyDir для записуваних шляхів

**Поради для іспиту**:
- Знайте повний шаблон захищеного Pod
- Розумійте контекст Pod проти контейнера
- Вмійте налагоджувати поширені помилки

---

## Наступний модуль

[Модуль 4.2: Pod Security Admission](module-4.2-pod-security-admission/) — Застосування стандартів безпеки на рівні простору імен.
