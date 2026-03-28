---
title: "Модуль 6.4: Незмінна інфраструктура"
slug: uk/k8s/cks/part6-runtime-security/module-6.4-immutable-infrastructure
sidebar:
  order: 4
---
> **Складність**: `[MEDIUM]` — архітектура безпеки
>
> **Час на виконання**: 35-40 хвилин
>
> **Передумови**: Модуль 6.3 (Розслідування контейнерів), основи контейнерів

---

## Чому цей модуль важливий

Незмінна інфраструктура означає, що контейнери не змінюються після розгортання. Якщо зловмисник не може змінювати файли або встановлювати інструменти, його можливості суттєво обмежені. Файлові системи тільки для читання, не-root користувачі та мінімальні образи створюють глибокий захист.

CKS тестує конфігурацію незмінних контейнерів як основну практику безпеки.

---

## Що таке незмінна інфраструктура?

```
┌─────────────────────────────────────────────────────────────┐
│              ЗМІННА проти НЕЗМІННОЇ                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ЗМІННА (Традиційна):                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Програмне забезпечення оновлюється на місці             │
│  • Зміни конфігурації під час виконання                    │
│  • Постійний стан у контейнері                             │
│  • Дрейф між розгортаннями                                 │
│  • Зловмисники можуть змінювати та зберігати               │
│                                                             │
│  НЕЗМІННА (Cloud Native):                                   │
│  ─────────────────────────────────────────────────────────  │
│  • Новий образ для кожної зміни                            │
│  • Конфігурація через ConfigMaps/Secrets                   │
│  • Стан у зовнішніх системах (БД, сховище)                │
│  • Послідовні, відтворювані розгортання                    │
│  • Зміни не виживають після перезапуску                    │
│                                                             │
│  Переваги безпеки незмінної:                               │
│  ├── Шкідливе ПЗ не може зберегтися                       │
│  ├── Легше виявити зміни                                   │
│  ├── Відомий правильний стан завжди доступний              │
│  └── Швидше відновлення (просто перерозгорнути)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Реалізація незмінних контейнерів

### Файлова система тільки для читання

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: immutable-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true  # Can't write to container filesystem
    volumeMounts:
    - name: tmp
      mountPath: /tmp
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

### Що запобігає файлова система тільки для читання

```
┌─────────────────────────────────────────────────────────────┐
│              ЗАХИСТ ФАЙЛОВОЇ СИСТЕМИ ТІЛЬКИ ДЛЯ ЧИТАННЯ     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ЗАБЛОКОВАНІ дії:                                          │
│  ├── Встановлення пакетів (apt, yum, pip)                 │
│  ├── Завантаження шкідливого ПЗ (wget, curl на диск)      │
│  ├── Зміна системних файлів (/etc/passwd)                 │
│  ├── Створення персистентності (cron, init scripts)       │
│  ├── Веб-оболонки (не можна записати PHP/JSP файли)      │
│  └── Підробка логів (не можна змінити /var/log)           │
│                                                             │
│  ДОЗВОЛЕНІ дії:                                            │
│  ├── Запис у змонтовані томи emptyDir                     │
│  ├── Мережеві з'єднання                                    │
│  ├── Атаки на основі пам'яті                              │
│  └── Виконання процесів (існуючі бінарні файли)           │
│                                                             │
│  Глибокий захист: поєднуйте з іншими заходами             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Мінімальні базові образи

```
┌─────────────────────────────────────────────────────────────┐
│              ПОРІВНЯННЯ ПОВЕРХНІ АТАКИ                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Ubuntu повний (~80МБ встановлений):                       │
│  ├── bash, sh, dash                                        │
│  ├── apt, dpkg                                             │
│  ├── wget, curl                                            │
│  ├── python, perl                                          │
│  ├── mount, umount                                         │
│  └── 1000+ пакетів з CVE                                  │
│                                                             │
│  Alpine (~5МБ встановлений):                               │
│  ├── ash (busybox shell)                                   │
│  ├── apk                                                   │
│  └── ~50 пакетів                                           │
│                                                             │
│  Distroless (~2МБ встановлений):                           │
│  ├── БЕЗ оболонки                                         │
│  ├── БЕЗ менеджера пакетів                                │
│  ├── Тільки середовище виконання + додаток                 │
│  └── Мінімальна поверхня CVE                               │
│                                                             │
│  Менше інструментів = менше можливостей для зловмисників   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Приклад Distroless

```dockerfile
# Build stage
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o myapp

# Production stage - distroless
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]

# No shell - kubectl exec will fail!
# No package manager - can't install tools
# Running as non-root - limited privileges
```

---

## Контейнери без root

### Налаштування не-root

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nonroot-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
```

### Що запобігає не-root

```
┌─────────────────────────────────────────────────────────────┐
│              ЗАХИСТ НЕ-ROOT                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Як не-root, зловмисники НЕ МОЖУТЬ:                       │
│  ├── Прив'язуватися до портів < 1024                      │
│  ├── Змінювати /etc/passwd, /etc/shadow                    │
│  ├── Встановлювати пакети системно                         │
│  ├── Доступ до /proc/sys для параметрів ядра              │
│  ├── Завантажувати модулі ядра                             │
│  └── Монтувати файлові системи                             │
│                                                             │
│  З allowPrivilegeEscalation: false:                        │
│  ├── setuid бінарні файли не працюють                      │
│  ├── Не можна використовувати sudo/su                      │
│  └── Capabilities не можуть бути отримані                   │
│                                                             │
│  З capabilities drop ALL:                                  │
│  └── Навіть якщо root, дуже обмежені можливості            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Повний приклад незмінного Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fully-immutable
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
    image: gcr.io/distroless/static:nonroot

    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]

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
    - name: config
      mountPath: /etc/config
      readOnly: true

  volumes:
  - name: tmp
    emptyDir:
      medium: Memory  # tmpfs - in memory, not on disk
      sizeLimit: 10Mi
  - name: config
    configMap:
      name: app-config

  automountServiceAccountToken: false
```

---

## Застосування незмінності

### Pod Security Admission для Restricted

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
```

Профіль `restricted` вимагає:
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities.drop: ["ALL"]
- Встановлений seccompProfile

### OPA Gatekeeper для ReadOnly

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirereadonlyfilesystem
spec:
  crd:
    spec:
      names:
        kind: K8sRequireReadOnlyFilesystem
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirereadonlyfilesystem
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.readOnlyRootFilesystem
          msg := sprintf("Container %v must use readOnlyRootFilesystem", [container.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireReadOnlyFilesystem
metadata:
  name: require-readonly-fs
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production"]
```

---

## Реальні сценарії іспиту

### Сценарій 1: Зробити наявний Deployment незмінним

```yaml
# До (змінний)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  template:
    spec:
      containers:
      - name: nginx
        image: nginx

# Після (незмінний)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 101  # nginx user
        fsGroup: 101
      containers:
      - name: nginx
        image: nginx
        securityContext:
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
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
```

### Сценарій 2: Знайти змінні Pod

```bash
# Find pods without read-only filesystem
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.containers[].securityContext.readOnlyRootFilesystem != true) |
  "\(.metadata.namespace)/\(.metadata.name)"
'

# Find pods running as root
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.securityContext.runAsNonRoot != true) |
  "\(.metadata.namespace)/\(.metadata.name)"
'
```

### Сценарій 3: Тестування незмінності

```bash
# Create immutable pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: immutable-test
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: test
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
EOF

# Test: Can't write to root filesystem
kubectl exec immutable-test -- touch /test.txt
# Error: touch: /test.txt: Read-only file system

# Test: Can write to /tmp
kubectl exec immutable-test -- touch /tmp/test.txt
# Success

# Cleanup
kubectl delete pod immutable-test
```

---

## Чи знали ви?

- **Distroless образи не мають оболонки**, тому `kubectl exec` з bash/sh не працюватиме. Використовуйте `kubectl debug` з ефемерним контейнером для усунення проблем.

- **emptyDir з medium: Memory** створює tmpfs (файлова система в RAM). Це швидко і не зберігається на диск, але враховується в лімітах пам'яті контейнера.

- **Деякі додатки потребують записуваних каталогів** для тимчасових файлів, кешів або PID-файлів. Визначте їх під час розробки та змонтуйте томи emptyDir.

- **Навіть з файловою системою тільки для читання**, зловмисники все ще можуть запускати шкідливий код у пам'яті. Поєднуйте з профілями seccomp та мережевими політиками для глибокого захисту.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Без записуваного /tmp | Додаток не працює | Змонтуйте emptyDir для /tmp |
| Забуті шляхи nginx | Помилки 502 | Змонтуйте каталоги cache, run |
| Образ запускається від root | runAsNonRoot не вдається | Використовуйте не-root образ або вкажіть UID |
| Занадто малий emptyDir | Додаток не працює | Встановіть відповідний sizeLimit |
| Не тестувати локально | Сюрпризи у продакшені | Тестуйте незмінну конфігурацію в dev |

---

## Тест

1. **Що запобігає readOnlyRootFilesystem: true?**
   <details>
   <summary>Відповідь</summary>
   Запобігає будь-яким записам у кореневу файлову систему контейнера. Це блокує встановлення шкідливого ПЗ, підробку конфігурації та створення веб-оболонок. Додатки все ще можуть писати у змонтовані томи.
   </details>

2. **Чому поєднувати файлову систему тільки для читання з не-root?**
   <details>
   <summary>Відповідь</summary>
   Глибокий захист. Файлова система тільки для читання запобігає зміні файлів. Не-root запобігає привілейованим діям. Разом вони значно обмежують те, що зловмисник може зробити навіть після отримання виконання коду.
   </details>

3. **Як дозволити запис для додатків з файловою системою тільки для читання?**
   <details>
   <summary>Відповідь</summary>
   Змонтуйте томи emptyDir для каталогів, куди додаток повинен писати (як /tmp, /var/cache). Ці каталоги стають записуваними, тоді як решта файлової системи залишається тільки для читання.
   </details>

4. **Яка перевага distroless образів для незмінності?**
   <details>
   <summary>Відповідь</summary>
   Distroless образи не мають оболонки або менеджера пакетів, тому зловмисники не можуть легко встановити інструменти або досліджувати систему. Вони містять лише середовище виконання додатку, мінімізуючи поверхню атаки.
   </details>

---

## Практична вправа

**Завдання**: Створити та перевірити конфігурацію незмінного контейнера.

```bash
# Step 1: Create mutable pod for comparison
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: mutable-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
EOF

# Step 2: Create immutable pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: immutable-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
EOF

# Wait for pods
kubectl wait --for=condition=Ready pod/mutable-pod --timeout=60s
kubectl wait --for=condition=Ready pod/immutable-pod --timeout=60s

# Step 3: Test mutable pod
echo "=== Testing Mutable Pod ==="
kubectl exec mutable-pod -- touch /test.txt && echo "Write to / succeeded"
kubectl exec mutable-pod -- whoami

# Step 4: Test immutable pod
echo "=== Testing Immutable Pod ==="
kubectl exec immutable-pod -- touch /test.txt 2>&1 || echo "Write to / blocked (expected)"
kubectl exec immutable-pod -- touch /tmp/test.txt && echo "Write to /tmp succeeded"
kubectl exec immutable-pod -- whoami

# Step 5: Compare security contexts
echo "=== Security Comparison ==="
echo "Mutable pod security:"
kubectl get pod mutable-pod -o jsonpath='{.spec.containers[0].securityContext}'
echo ""
echo "Immutable pod security:"
kubectl get pod immutable-pod -o jsonpath='{.spec.securityContext}'
echo ""
kubectl get pod immutable-pod -o jsonpath='{.spec.containers[0].securityContext}'
echo ""

# Cleanup
kubectl delete pod mutable-pod immutable-pod
```

**Критерії успіху**: Зрозуміти конфігурацію незмінності та її ефекти.

---

## Підсумок

**Компоненти незмінності**:
- readOnlyRootFilesystem: true
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities.drop: ["ALL"]
- Мінімальні базові образи

**Що це запобігає**:
- Встановлення шкідливого ПЗ
- Підробка конфігурації
- Механізми персистентності
- Підвищення привілеїв

**Реалізація**:
- Монтуйте emptyDir для записуваних шляхів
- Використовуйте distroless образи
- Застосовуйте з PSA restricted
- Ретельно тестуйте

**Поради для іспиту**:
- Знайте поля контексту безпеки
- Розумійте використання emptyDir
- Вмійте виправляти змінні Pod
- Знайте типові шляхи додатків

---

## Частина 6 завершена!

Вітаємо! Ви завершили **Моніторинг, логування та безпеку середовища виконання** (20% CKS). Тепер ви розумієте:
- Конфігурацію та аналіз журналів аудиту Kubernetes
- Виявлення загроз під час виконання з Falco
- Техніки розслідування контейнерів
- Принципи незмінної інфраструктури

---

## Навчальну програму CKS завершено!

Ви пройшли всю навчальну програму CKS:

| Частина | Тема | Вага |
|---------|------|------|
| 0 | Налаштування середовища | - |
| 1 | Налаштування кластера | 10% |
| 2 | Зміцнення кластера | 15% |
| 3 | Зміцнення системи | 15% |
| 4 | Мінімізація вразливостей мікросервісів | 20% |
| 5 | Безпека ланцюга постачання | 20% |
| 6 | Моніторинг та безпека виконання | 20% |

**Наступні кроки**:
1. Переглянути слабкі місця
2. Практикуватися з killer.sh
3. Засікати час на вправах
4. Запланувати іспит!

Бажаємо успіхів з сертифікацією CKS!
