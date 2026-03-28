---
title: "Модуль 5.1: Безпека образів контейнерів"
slug: uk/k8s/cks/part5-supply-chain-security/module-5.1-image-security
sidebar:
  order: 1
---
> **Складність**: `[MEDIUM]` — основна навичка CKS
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Основи Docker/контейнерів, Модуль 0.3 (Інструменти безпеки)

---

## Чому цей модуль важливий

Образи контейнерів є основою ваших навантажень. Вразливий базовий образ, шкідливий пакет або неправильно налаштований Dockerfile можуть скомпрометувати весь кластер. Атаки на ланцюг постачання націлені на програмне забезпечення ще до його запуску.

CKS значною мірою тестує безпеку образів — сканування, захист та перевірку.

---

## Ризики безпеки образів

```
┌─────────────────────────────────────────────────────────────┐
│              РИЗИКИ ОБРАЗІВ КОНТЕЙНЕРІВ                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Вразливі базові образи                                    │
│  ├── CVE в пакетах ОС (glibc, openssl тощо)              │
│  ├── Застарілі середовища виконання (Python, Node, Java)  │
│  └── Непотрібні інструменти (wget, curl, shells)          │
│                                                             │
│  Атаки на ланцюг постачання                                │
│  ├── Скомпрометовані реєстри пакетів (npm, PyPI)          │
│  ├── Тайпсквотинг (python vs pytbon)                      │
│  └── Шкідливі базові образи на Docker Hub                 │
│                                                             │
│  Помилки конфігурації образів                              │
│  ├── Запуск від root                                       │
│  ├── Включення секретів у шари                            │
│  └── Файли з відкритим доступом для всіх                  │
│                                                             │
│  Мутабельність тегів                                       │
│  ├── :latest може змінитися без попередження               │
│  └── Теги можуть бути перезаписані шкідливими образами    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Вибір базового образу

### Вибір безпечних базових образів

```
┌─────────────────────────────────────────────────────────────┐
│              ВАРІАНТИ БАЗОВИХ ОБРАЗІВ                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Distroless (Google) — НАЙБЕЗПЕЧНІШИЙ                      │
│  ─────────────────────────────────────────────────────────  │
│  • Без оболонки, без менеджера пакетів                     │
│  • Тільки середовище виконання додатку                     │
│  • Мінімальна поверхня атаки                               │
│  • gcr.io/distroless/static                               │
│  • gcr.io/distroless/base                                 │
│  • gcr.io/distroless/java17                               │
│                                                             │
│  Alpine — МАЛИЙ та БЕЗПЕЧНИЙ                               │
│  ─────────────────────────────────────────────────────────  │
│  • ~5МБ базовий образ                                      │
│  • musl libc (не glibc)                                   │
│  • Менеджер пакетів apk                                    │
│  • Можливі проблеми сумісності                            │
│                                                             │
│  Slim варіанти — ЗБАЛАНСОВАНИЙ                              │
│  ─────────────────────────────────────────────────────────  │
│  • python:3.11-slim, node:20-slim                         │
│  • Видалені інструменти розробки та документація           │
│  • Все ще має доступ до оболонки                          │
│                                                             │
│  Повні образи — УНИКАЙТЕ у продакшені                     │
│  ─────────────────────────────────────────────────────────  │
│  • ubuntu:22.04, debian:12                                │
│  • Багато непотрібних пакетів                              │
│  • Велика поверхня атаки                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Порівняння розмірів образів

```bash
# Check image sizes
docker images | grep -E "nginx|distroless|alpine"

# Typical sizes:
# nginx:latest          ~190MB
# nginx:alpine          ~40MB
# gcr.io/distroless/base ~20MB
# gcr.io/distroless/static ~2MB
```

---

## Найкращі практики безпеки Dockerfile

### Приклад безпечного Dockerfile

```dockerfile
# Use specific version, not :latest
FROM python:3.11-slim-bookworm AS builder

# Don't run as root during build (when possible)
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM gcr.io/distroless/python3-debian12

# Copy from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

WORKDIR /app
COPY . .

# Run as non-root
USER nonroot

# Don't expose unnecessary ports
EXPOSE 8080

# Use exec form, not shell form
ENTRYPOINT ["python", "app.py"]
```

### Антипатерни безпеки

```dockerfile
# BAD: Using latest tag
FROM ubuntu:latest

# BAD: Running as root (implicit)
# No USER directive

# BAD: Including secrets
ENV API_KEY=supersecret123

# BAD: Installing unnecessary tools
RUN apt-get update && apt-get install -y \
    curl wget vim nano git ssh

# BAD: Shell form (vulnerable to shell injection)
ENTRYPOINT /bin/sh -c "python app.py $ARGS"

# BAD: World-readable sensitive files
COPY config.yaml /etc/config/
# Should set permissions explicitly
```

---

## Багатоетапна збірка

Багатоетапна збірка зменшує поверхню атаки, виключаючи інструменти збірки з продакшен-образів.

```dockerfile
# Build stage - has all tools
FROM golang:1.21 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o myapp

# Production stage - minimal
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]
```

### Переваги

```
┌─────────────────────────────────────────────────────────────┐
│              ПЕРЕВАГИ БАГАТОЕТАПНОЇ ЗБІРКИ                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  До (одноетапна):                                          │
│  ├── golang:1.21 базовий (~800МБ)                         │
│  ├── Включає компілятор, інструменти                       │
│  └── Всі залежності збірки                                 │
│                                                             │
│  Після (багатоетапна):                                      │
│  ├── distroless/static (~2МБ)                              │
│  ├── Тільки скомпільований бінарний файл                   │
│  └── Без оболонки, інструментів, менеджера пакетів        │
│                                                             │
│  Поверхня атаки зменшена на 99%+                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Теги та дайджести образів

### Проблема з тегами

```bash
# Tags are mutable - same tag, different content!
docker pull nginx:1.25  # Today: image A
docker pull nginx:1.25  # Tomorrow: image B (patched)

# :latest is worst - changes constantly
docker pull nginx:latest  # ???

# Tags can be maliciously overwritten in compromised registries
```

### Використання дайджестів образів

```yaml
# SECURE: Using SHA256 digest
apiVersion: v1
kind: Pod
metadata:
  name: secure-nginx
spec:
  containers:
  - name: nginx
    # Immutable reference - can never change
    image: nginx@sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
```

### Пошук дайджесту образу

```bash
# Get digest when pulling
docker pull nginx:1.25
# Output: Digest: sha256:0d17b565...

# Or inspect existing image
docker inspect nginx:1.25 | jq -r '.[0].RepoDigests'

# Or use crane/skopeo
crane digest nginx:1.25
skopeo inspect docker://nginx:1.25 | jq -r '.Digest'
```

---

## Приватні реєстри

### Використання приватного реєстру

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-app
spec:
  containers:
  - name: app
    image: registry.company.com/myapp:1.0
  imagePullSecrets:
  - name: registry-creds
```

### Створення секрету реєстру

```bash
kubectl create secret docker-registry registry-creds \
  --docker-server=registry.company.com \
  --docker-username=user \
  --docker-password=password \
  --docker-email=user@company.com
```

### Типові ImagePullSecrets для ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
imagePullSecrets:
- name: registry-creds
```

---

## Політики завантаження образів

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pull-policy-demo
spec:
  containers:
  - name: app
    image: myapp:1.0
    imagePullPolicy: Always  # Always pull from registry
    # Options:
    # Always - Pull every time (good for :latest)
    # IfNotPresent - Use local if exists (default for tagged)
    # Never - Only use local image
```

### Рекомендації щодо політик

```
┌─────────────────────────────────────────────────────────────┐
│              ПОЛІТИКИ ЗАВАНТАЖЕННЯ ОБРАЗІВ                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Always                                                    │
│  └── Використовуйте для: :latest тег, мутабельні теги     │
│      Гарантує останню версію, але вимагає доступ до реєстру│
│                                                             │
│  IfNotPresent (типово)                                     │
│  └── Використовуйте для: незмінних тегів (v1.2.3), дайдж. │
│      Швидше, використовує кешовані образи                  │
│                                                             │
│  Never                                                     │
│  └── Використовуйте для: попередньо завантажені образи     │
│      Образ повинен існувати на вузлі                       │
│                                                             │
│  Найкраща практика: конкретні теги + IfNotPresent          │
│  Або: дайджести для максимальної безпеки                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Реальні сценарії іспиту

### Сценарій 1: Виправлення небезпечного посилання на образ

```yaml
# До (небезпечно)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx:latest  # Mutable!
    imagePullPolicy: IfNotPresent

# Після (безпечно)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx@sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
    imagePullPolicy: IfNotPresent
```

### Сценарій 2: Використання приватного реєстру

```bash
# Create registry secret
kubectl create secret docker-registry private-reg \
  --docker-server=gcr.io \
  --docker-username=_json_key \
  --docker-password="$(cat key.json)" \
  -n production

# Create pod using private image
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: private-app
  namespace: production
spec:
  containers:
  - name: app
    image: gcr.io/myproject/myapp:1.0
  imagePullSecrets:
  - name: private-reg
EOF
```

### Сценарій 3: Пошук Pod з тегом :latest

```bash
# Find all pods using :latest tag
kubectl get pods -A -o json | jq -r '
  .items[] |
  .spec.containers[] |
  select(.image | contains(":latest") or (contains(":") | not)) |
  "\(.name): \(.image)"
'
```

---

## Контрольний список аналізу Dockerfile

```bash
# Questions to ask when reviewing Dockerfile:

# 1. Base image security
grep "^FROM" Dockerfile
# Is it using :latest? A known vulnerable version?
# Is it from a trusted source?

# 2. Running as root?
grep "^USER" Dockerfile
# No USER directive = running as root

# 3. Secrets in image?
grep -E "ENV.*KEY|ENV.*SECRET|ENV.*PASSWORD" Dockerfile
grep -E "COPY.*\.env|COPY.*secret" Dockerfile

# 4. Unnecessary tools installed?
grep -E "curl|wget|vim|nano|ssh|git" Dockerfile

# 5. Using exec form?
grep "^ENTRYPOINT\|^CMD" Dockerfile
# Shell form: ENTRYPOINT /bin/sh -c "..."
# Exec form: ENTRYPOINT ["...", "..."]
```

---

## Чи знали ви?

- **Docker Hub обмежує** неавтентифіковані завантаження до 100 за 6 годин. Багато продакшен-збоїв були спричинені досягненням цих обмежень.

- **Distroless образи не мають оболонки**, що означає неможливість exec для налагодження. Використовуйте ефемерні контейнери налагодження (`kubectl debug`).

- **Шари образів є спільними**. Якщо кілька Pod використовують той самий базовий образ, цей шар зберігається лише один раз на вузлі.

- **Alpine використовує musl libc** замість glibc. Деякі додатки можуть мати проблеми сумісності, особливо ті, що використовують DNS-резолюцію або певні патерни потоків.

- **K8s 1.35: Облікові дані завантаження образів тепер перевіряються для кожного Pod** (KubeletEnsureSecretPulledImages, увімкнено за замовчуванням). Навіть якщо образ кешований локально, kubelet повторно валідує облікові дані. Налаштовується через `imagePullCredentialsVerificationPolicy`: `AlwaysVerify` (типово), `NeverVerify` або `NeverVerifyAllowlistedImages`.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Використання :latest | Непередбачувані розгортання | Використовуйте конкретні теги або дайджести |
| Без директиви USER | Контейнер запускається від root | Додайте USER nonroot |
| Секрети в ENV | Видимі в історії образу | Використовуйте секрети під час виконання |
| Повні базові образи | Велика поверхня атаки | Використовуйте slim/distroless |
| Без pull policy | Можуть використовуватися застарілі образи | Встановіть явну політику |

---

## Тест

1. **Чому слід уникати тега :latest?**
   <details>
   <summary>Відповідь</summary>
   Тег :latest є мутабельним — він може вказувати на різні образи з часом. Це робить розгортання непередбачуваними і може ввести вразливості або критичні зміни без вашого відома.
   </details>

2. **Яка перевага використання distroless образів?**
   <details>
   <summary>Відповідь</summary>
   Distroless образи містять лише середовище виконання додатку, без оболонки, менеджера пакетів або непотрібних інструментів. Це значно зменшує поверхню атаки і ускладнює зловмисникам експлуатацію контейнера.
   </details>

3. **Як використовувати дайджести образів у Kubernetes?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте формат `image: name@sha256:digest` замість `image: name:tag`. Наприклад: `nginx@sha256:0d17b565...`. Дайджести є незмінними і гарантують, що ви завжди отримаєте точно той самий образ.
   </details>

4. **Чому багатоетапна збірка безпечніша?**
   <details>
   <summary>Відповідь</summary>
   Багатоетапна збірка виключає інструменти збірки, компілятори та залежності з кінцевого образу. Включається лише скомпільований додаток, що зменшує поверхню атаки та розмір образу.
   </details>

---

## Практична вправа

**Завдання**: Проаналізувати та захистити розгортання образу контейнера.

```bash
# Step 1: Find pods using :latest or no tag
echo "=== Pods with potentially insecure images ==="
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.containers[].image | (contains(":latest") or (contains(":") | not))) |
  "\(.metadata.namespace)/\(.metadata.name): \(.spec.containers[].image)"
'

# Step 2: Create insecure pod for testing
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: nginx:latest
    imagePullPolicy: Always
EOF

# Step 3: Get the actual digest of the image
kubectl get pod insecure-pod -o jsonpath='{.status.containerStatuses[0].imageID}'
# This shows the actual digest being used

# Step 4: Create secure version with digest
# (Use the digest from step 3 or pull fresh)
DIGEST=$(kubectl get pod insecure-pod -o jsonpath='{.status.containerStatuses[0].imageID}' | sed 's/docker-pullable:\/\///')

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  containers:
  - name: app
    image: ${DIGEST}
    imagePullPolicy: IfNotPresent
EOF

# Step 5: Verify
kubectl get pod secure-pod -o jsonpath='{.spec.containers[0].image}'

# Cleanup
kubectl delete pod insecure-pod secure-pod
```

**Критерії успіху**: Зрозуміти ризики тегів образів та як використовувати дайджести.

---

## Підсумок

**Принципи безпеки образів**:
- Використовуйте конкретні теги, не :latest
- Надавайте перевагу дайджестам для незмінності
- Обирайте мінімальні базові образи
- Багатоетапна збірка для продакшену

**Ієрархія базових образів** (від найбезпечнішого до найменш безпечного):
1. Distroless
2. Alpine
3. Slim варіанти
4. Повні дистрибутиви

**Безпека Dockerfile**:
- Не-root USER
- Exec-форма для ENTRYPOINT/CMD
- Без секретів в ENV
- Мінімум пакетів

**Поради для іспиту**:
- Вмійте ідентифікувати небезпечні образи
- Розумійте політики завантаження
- Вмійте конвертувати теги в дайджести

---

## Наступний модуль

[Модуль 5.2: Сканування образів з Trivy](module-5.2-image-scanning/) — Пошук вразливостей в образах контейнерів.
