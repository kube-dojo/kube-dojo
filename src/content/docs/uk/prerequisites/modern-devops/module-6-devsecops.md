---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 6: \u041f\u0440\u0430\u043a\u0442\u0438\u043a\u0438 \u0431\u0435\u0437\u043f\u0435\u043a\u0438 (DevSecOps)"
sidebar:
  order: 7
---
> **Складність**: `[MEDIUM]` — Необхідне мислення безпеки
>
> **Час на виконання**: 35-40 хвилин
>
> **Передумови**: Концепції CI/CD (Модуль 3)

---

## Чому цей модуль важливий

Безпека раніше була другорядною — команда, яка казала «ні» наприкінці розробки. Це не працює у хмарних середовищах, де ви деплоїте кілька разів на день. DevSecOps інтегрує безпеку на кожному етапі життєвого циклу розробки. Для середовищ Kubernetes, де неправильна конфігурація — ризик безпеки №1, це критично.

---

## Що таке DevSecOps?

DevSecOps — це **безпека, інтегрована в DevOps**, а не прикручена потім.

```
┌─────────────────────────────────────────────────────────────┐
│          ТРАДИЦІЙНИЙ ПІДХІД vs DEVSECOPS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Традиційна безпека:                                        │
│  ┌─────┐    ┌─────┐    ┌──────────┐    ┌─────────────┐   │
│  │ Роз │───►│ QA  │───►│ Перевірка│───►│ Продакшн    │   │
│  └─────┘    └─────┘    │ безпеки  │    └─────────────┘   │
│                        └──────────┘                        │
│                             │                               │
│                        Вузьке місце!                        │
│                        "Повертайтесь і виправляйте"        │
│                                                             │
│  DevSecOps:                                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Безпека на КОЖНОМУ етапі                           │  │
│  │                                                      │  │
│  │  План → Код → Збірка → Тест → Деплой → Моніторинг │  │
│  │    ↑      ↑      ↑       ↑       ↑         ↑       │  │
│  │  Модель SAST   SCA   DAST   Скан    Безпека       │  │
│  │  загроз      (залежн.)     конфіг.  середовища    │  │
│  │                                                      │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Ключовий зсув: Безпека — це справа кожного               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Філософія Shift Left

«Shift Left» означає знаходити проблеми безпеки раніше:

```
┌─────────────────────────────────────────────────────────────┐
│          ВАРТІСТЬ ВИПРАВЛЕННЯ ПРОБЛЕМ БЕЗПЕКИ               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Вартість                                                   │
│  виправлення                                                │
│       │                                                     │
│   $$$│                                         ┌────┐      │
│      │                                    ┌────┤    │      │
│      │                               ┌────┤    │    │      │
│    $$│                          ┌────┤    │    │    │      │
│      │                     ┌────┤    │    │    │    │      │
│     $│                ┌────┤    │    │    │    │    │      │
│      │           ┌────┤    │    │    │    │    │    │      │
│      │      ┌────┤    │    │    │    │    │    │    │      │
│      └──────┴────┴────┴────┴────┴────┴────┴────┴────┴──►   │
│           Код  Збірка Тест Стейдж Прод Злам                │
│                                                             │
│  Знайти рано = дешеве виправлення                          │
│  Знайти на продакшні = дороге виправлення                  │
│  Знайти після зламу = катастрофа                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Безпека в CI/CD пайплайні

```
┌─────────────────────────────────────────────────────────────┐
│              БЕЗПЕЧНИЙ CI/CD ПАЙПЛАЙН                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PRE-COMMIT                                              │
│     ├── Сканування секретів (запобігання коміту секретів)  │
│     └── git-secrets, detect-secrets                         │
│                                                             │
│  2. СТАТИЧНИЙ АНАЛІЗ (SAST)                                │
│     ├── Сканування коду на вразливості                     │
│     └── Semgrep, SonarQube, CodeQL                         │
│                                                             │
│  3. СКАНУВАННЯ ЗАЛЕЖНОСТЕЙ (SCA)                            │
│     ├── Перевірка залежностей на відомі CVE                │
│     └── npm audit, Snyk, Dependabot                        │
│                                                             │
│  4. СКАНУВАННЯ КОНТЕЙНЕРІВ                                  │
│     ├── Сканування образів на вразливості                  │
│     └── Trivy, Grype, Clair                                │
│                                                             │
│  5. СКАНУВАННЯ КОНФІГУРАЦІЇ                                 │
│     ├── Перевірка Kubernetes YAML на помилки конфігурації  │
│     └── KubeLinter, Checkov, Kubescape                     │
│                                                             │
│  6. ДИНАМІЧНИЙ АНАЛІЗ (DAST)                                │
│     ├── Тестування запущеного застосунку                   │
│     └── OWASP ZAP, Burp Suite                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Безпека контейнерів

### 1. Безпека образів

```dockerfile
# BAD: Large attack surface, runs as root
FROM ubuntu:latest
RUN apt-get update && apt-get install -y nginx
COPY app /app
CMD ["nginx"]

# GOOD: Minimal image, non-root user
FROM nginx:1.25-alpine
RUN adduser -D -u 1000 appuser
COPY --chown=appuser:appuser app /app
USER appuser
EXPOSE 8080
```

### 2. Сканування образів

```bash
# Trivy - most popular open-source scanner
trivy image nginx:1.25

# Example output:
# nginx:1.25 (debian 12.0)
# Total: 142 (UNKNOWN: 0, LOW: 89, MEDIUM: 45, HIGH: 7, CRITICAL: 1)
```

### 3. Підписування образів

```bash
# Sign images to ensure they haven't been tampered with
# Using cosign (sigstore)
cosign sign myregistry/myapp:v1.0

# Verify before deploying
cosign verify myregistry/myapp:v1.0
```

---

## Безпека Kubernetes

### Типові помилки конфігурації

```yaml
# BAD: Overly permissive pod
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: myapp
    securityContext:
      privileged: true          # Never do this!
      runAsUser: 0              # Don't run as root
    volumeMounts:
    - name: host
      mountPath: /host          # Don't mount host filesystem
  volumes:
  - name: host
    hostPath:
      path: /

# GOOD: Secure pod configuration
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: myapp
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
```

### Стандарти безпеки Pod

Kubernetes 1.25+ використовує Pod Security Standards:

```yaml
# Enforce security standards at namespace level
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

| Рівень | Опис |
|--------|------|
| privileged | Без обмежень (небезпечно) |
| baseline | Мінімальні обмеження, запобігає відомим ескалаціям |
| restricted | Дуже обмежений, дотримується найкращих практик |

---

## Управління секретами

### Проблема

```yaml
# NEVER DO THIS
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_PASSWORD: "supersecret123"  # In Git history forever!
```

### Рішення

```
┌─────────────────────────────────────────────────────────────┐
│           ВАРІАНТИ УПРАВЛІННЯ СЕКРЕТАМИ                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Зовнішні менеджери секретів                            │
│     ├── HashiCorp Vault         (найпопулярніший)         │
│     ├── AWS Secrets Manager                               │
│     ├── Azure Key Vault                                   │
│     └── Google Secret Manager                             │
│                                                             │
│  2. Kubernetes-нативні                                     │
│     ├── Sealed Secrets         (шифрування для Git)       │
│     ├── External Secrets       (синхронізація з менедж.)  │
│     └── SOPS                   (шифрування YAML файлів)  │
│                                                             │
│  3. Ін'єкція під час виконання                             │
│     ├── Vault Agent Sidecar                              │
│     └── CSI Secret Store Driver                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Приклад Sealed Secrets

```bash
# Install sealed-secrets controller
# Then create sealed secrets that can be committed to Git

kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# sealed-secret.yaml can be committed
# Only the cluster can decrypt it
```

---

## Мережева безпека

```yaml
# Network Policy: Only allow specific traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

---

## Інструменти сканування безпеки

### KubeLinter (конфігурація)

```bash
# Scan Kubernetes YAML for issues
kube-linter lint deployment.yaml

# Example output:
# deployment.yaml: (object: myapp apps/v1, Kind=Deployment)
# - container "app" does not have a read-only root file system
# - container "app" is not set to runAsNonRoot
```

### Kubescape (комплексний)

```bash
# Full security scan against frameworks like NSA-CISA
kubescape scan framework nsa

# Scans for:
# - Misconfigurations
# - RBAC issues
# - Network policies
# - Image vulnerabilities
```

### Trivy (все включено)

```bash
# Scan container image
trivy image myapp:v1

# Scan Kubernetes manifests
trivy config .

# Scan running cluster
trivy k8s --report summary cluster
```

---

## Безпека під час виконання

```
┌─────────────────────────────────────────────────────────────┐
│              БЕЗПЕКА ПІД ЧАС ВИКОНАННЯ                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Виявлення: Що відбувається прямо зараз?                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Falco (CNCF)                                        │  │
│  │  - Моніторить системні виклики                      │  │
│  │  - Виявляє аномальну поведінку                      │  │
│  │  - Сповіщає про події безпеки                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Приклади правил Falco:                                    │
│  - Shell запущений у контейнері                            │
│  - Читання чутливого файлу (/etc/shadow)                  │
│  - Вихідне з'єднання на незвичний порт                    │
│  - Процес запущений від root                               │
│                                                             │
│  Запобігання: Не допустити поганих речей                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  OPA Gatekeeper / Kyverno                           │  │
│  │  - Застосування політик                             │  │
│  │  - Контроль допуску                                 │  │
│  │  - Блокування невідповідних ресурсів                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Найкращі практики RBAC

```yaml
# Principle of least privilege
# Give only the permissions needed

# BAD: Cluster admin for everything
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: developer-admin
subjects:
- kind: User
  name: developer@company.com
roleRef:
  kind: ClusterRole
  name: cluster-admin    # Too much power!

# GOOD: Namespace-scoped, minimal permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: developer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: development
subjects:
- kind: User
  name: developer@company.com
roleRef:
  kind: Role
  name: developer
```

---

## Чи знали ви?

- **Понад 90% інцидентів безпеки Kubernetes** спричинені неправильною конфігурацією, а не zero-day експлойтами. Сканування на помилки конфігурації є ціннішим, ніж більшість людей думає.

- **Вразливість Log4Shell (2021)** могла бути виявлена скануванням залежностей. Компанії з хорошими практиками SCA дізналися протягом кількох годин, які застосунки були вражені.

- **Falco обробляє мільярди подій** у компаніях на кшталт Shopify. Він може виявити запуск shell у контейнері за мілісекунди.

---

## Типові помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Секрети в Git | Постійне розкриття | Використовуйте менеджери секретів |
| Запуск від root | Ризик виходу з контейнера | Завжди runAsNonRoot |
| Немає мережевих політик | Бічне переміщення | Політики заборони за замовчуванням |
| Тег latest | Неможливість відстеження вразливостей | Вказуйте конкретні версії |
| Немає сканування образів | Невідомі вразливості | Скануйте в CI/CD |
| Cluster-admin скрізь | Радіус ураження | RBAC з мінімальними привілеями |

---

## Тест

1. **Що означає «Shift Left» у DevSecOps?**
   <details>
   <summary>Відповідь</summary>
   Знаходження проблем безпеки раніше в життєвому циклі розробки (ближче до коду, далі від продакшну). Раннє виявлення дешевше й швидше виправити, ніж знаходження проблем на продакшні.
   </details>

2. **Чому контейнери не повинні працювати від root?**
   <details>
   <summary>Відповідь</summary>
   Якщо зловмисник скомпрометує контейнер, запуск від root полегшує вихід з контейнера. Контейнери без root обмежують радіус ураження компрометації.
   </details>

3. **Яка різниця між SAST і DAST?**
   <details>
   <summary>Відповідь</summary>
   SAST (статичний аналіз) сканує вихідний код без його запуску. DAST (динамічний аналіз) тестує запущений застосунок. SAST знаходить проблеми коду; DAST знаходить вразливості під час виконання, такі як SQL-ін'єкція.
   </details>

4. **Яку проблему вирішують Sealed Secrets?**
   <details>
   <summary>Відповідь</summary>
   Sealed Secrets дозволяють зберігати зашифровані секрети в Git. Тільки кластер може їх розшифрувати. Це уможливлює GitOps робочі процеси, де все, включно з секретами, перебуває під контролем версій.
   </details>

---

## Практична вправа

**Завдання**: Практика сканування безпеки Kubernetes.

```bash
# 1. Create an insecure deployment
cat << 'EOF' > insecure-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insecure-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: insecure
  template:
    metadata:
      labels:
        app: insecure
    spec:
      containers:
      - name: app
        image: nginx:latest
        securityContext:
          privileged: true
          runAsUser: 0
        ports:
        - containerPort: 80
EOF

# 2. Scan with kubectl (basic check)
kubectl apply -f insecure-deployment.yaml --dry-run=server
# Note: This won't catch security issues, just syntax

# 3. If you have trivy installed:
# trivy config insecure-deployment.yaml

# 4. Manual security checklist:
echo "Security Review Checklist:"
echo "[ ] Image uses specific tag (not :latest)"
echo "[ ] Container runs as non-root"
echo "[ ] privileged: false"
echo "[ ] Resource limits set"
echo "[ ] readOnlyRootFilesystem: true"
echo "[ ] Capabilities dropped"

# 5. Create a secure version
cat << 'EOF' > secure-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secure
  template:
    metadata:
      labels:
        app: secure
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: app
        image: nginx:1.25-alpine
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        ports:
        - containerPort: 8080
        resources:
          limits:
            memory: "128Mi"
            cpu: "500m"
          requests:
            memory: "64Mi"
            cpu: "250m"
EOF

# 6. Compare the two
echo "=== Insecure vs Secure ==="
diff insecure-deployment.yaml secure-deployment.yaml || true

# 7. Cleanup
rm insecure-deployment.yaml secure-deployment.yaml
```

**Критерій успіху**: Розуміння небезпечних та безпечних конфігурацій.

---

## Підсумок

**DevSecOps** інтегрує безпеку на кожному етапі:

**Ключові концепції**:
- Shift Left: Знаходьте проблеми рано
- Безпека як код
- Автоматизоване сканування
- Мінімальні привілеї

**Безпека CI/CD**:
- SAST: Сканування вихідного коду
- SCA: Сканування залежностей
- Сканування контейнерів: Сканування образів
- Сканування конфігурації: Сканування Kubernetes YAML

**Безпека Kubernetes**:
- Стандарти безпеки Pod
- Мережеві політики
- RBAC (мінімальні привілеї)
- Управління секретами

**Інструменти**:
- Trivy: Образи та конфігурації
- KubeLinter/Kubescape: Конфігурації K8s
- Falco: Виявлення під час виконання
- Vault/Sealed Secrets: Управління секретами

**Мислення**: Безпека — це справа кожного, а не лише команди безпеки.

---

## Трек завершено!

Вітаємо! Ви завершили трек передумов **Сучасні практики DevOps**. Тепер ви розумієте:

1. Інфраструктура як код
2. Робочі процеси GitOps
3. CI/CD пайплайни
4. Основи спостережуваності
5. Концепції платформної інженерії
6. Практики безпеки (DevSecOps)

**Наступні кроки**:
- [Навчальний план CKA](../../k8s/cka/part0-environment/module-0.1-cluster-setup/) — Сертифікація адміністратора
- [Навчальний план CKAD](../../k8s/ckad/part0-environment/module-0.1-ckad-overview/) — Сертифікація розробника
- [Філософія та дизайн](../philosophy-design/module-1.1-why-kubernetes-won/) — Чому Kubernetes?
