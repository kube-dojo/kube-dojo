---
title: "Модуль 4.2: Pod Security Admission (PSA)"
slug: uk/k8s/cks/part4-microservice-vulnerabilities/module-4.2-pod-security-admission
sidebar:
  order: 2
---
> **Складність**: `[MEDIUM]` — основна навичка CKS
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Модуль 4.1 (Контексти безпеки), основи просторів імен

---

## Чому цей модуль важливий

Pod Security Admission (PSA) застосовує стандарти безпеки на рівні простору імен. Замість ручної перевірки контексту безпеки кожного Pod, PSA автоматично валідує Pod відповідно до визначених профілів безпеки та блокує невідповідні.

PSA замінив PodSecurityPolicy (видалено в Kubernetes 1.25). Це критична тема CKS.

---

## Стандарти безпеки Pod

```
┌─────────────────────────────────────────────────────────────┐
│              СТАНДАРТИ БЕЗПЕКИ POD                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Privileged (найбільш дозвільний)                          │
│  ─────────────────────────────────────────────────────────  │
│  • Без обмежень                                            │
│  • Для системних навантажень                               │
│  • CNI, CSI, агенти логування                              │
│                                                             │
│  Baseline (розумний стандарт)                               │
│  ─────────────────────────────────────────────────────────  │
│  • Запобігає відомим підвищенням привілеїв                 │
│  • Блокує hostNetwork, hostPID, hostIPC                    │
│  • Блокує привілейовані контейнери                         │
│  • Дозволяє запуск від root                                │
│                                                             │
│  Restricted (найбільш безпечний)                            │
│  ─────────────────────────────────────────────────────────  │
│  • Максимальна безпека                                      │
│  • Вимагає запуск не від root                              │
│  • Вимагає скидання ВСІХ capabilities                      │
│  • Вимагає файлову систему тільки для читання              │
│  • Вимагає профіль seccomp                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Режими PSA

```
┌─────────────────────────────────────────────────────────────┐
│              РЕЖИМИ ЗАСТОСУВАННЯ PSA                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  enforce                                                   │
│  └── Відхиляти Pod, що порушують політику                  │
│      (Створення Pod не вдається)                           │
│                                                             │
│  warn                                                      │
│  └── Дозволити, але показати попередження                   │
│      (Добре для міграції)                                  │
│                                                             │
│  audit                                                     │
│  └── Записати порушення в журнал аудиту                    │
│      (Pod все одно створюється)                            │
│                                                             │
│  Можна використовувати різні профілі для кожного режиму:  │
│  • enforce: baseline (блокувати очевидні проблеми)         │
│  • warn: restricted (показати, що не пройде)              │
│  • audit: restricted (логувати для перевірки)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Налаштування PSA через мітки

```yaml
# Apply PSA to a namespace using labels
apiVersion: v1
kind: Namespace
metadata:
  name: secure-ns
  labels:
    # Enforce baseline standard
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/enforce-version: latest

    # Warn on restricted violations
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest

    # Audit restricted violations
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

### Формат міток

```
pod-security.kubernetes.io/<MODE>: <PROFILE>
pod-security.kubernetes.io/<MODE>-version: <VERSION>

MODE:    enforce | warn | audit
PROFILE: privileged | baseline | restricted
VERSION: latest | v1.28 | v1.27 | etc.
```

---

## Вимоги профілів

### Обмеження профілю Baseline

```yaml
# Baseline блокує ці налаштування:
hostNetwork: true          # Blocked
hostPID: true              # Blocked
hostIPC: true              # Blocked
privileged: true           # Blocked
hostPorts: [80, 443]       # Blocked (hostPort)

# These capabilities blocked:
capabilities:
  add:
    - NET_ADMIN            # Blocked
    - SYS_ADMIN            # Blocked
    - ALL                  # Blocked

# Baseline ДОЗВОЛЯЄ:
runAsUser: 0               # Running as root OK
runAsNonRoot: false        # Not required
readOnlyRootFilesystem: false  # Not required
```

### Вимоги профілю Restricted

```yaml
# Restricted ВИМАГАЄ:
securityContext:
  runAsNonRoot: true               # Required
  allowPrivilegeEscalation: false  # Required
  seccompProfile:
    type: RuntimeDefault           # Required (or Localhost)
  capabilities:
    drop: ["ALL"]                  # Required

# For containers specifically:
containers:
- name: app
  securityContext:
    runAsNonRoot: true
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true   # Recommended but not required
    capabilities:
      drop: ["ALL"]
```

---

## Практичні приклади

### Створення простору імен з Restricted

```bash
# Create namespace with restricted enforcement
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
EOF
```

### Тестування застосування політики

```bash
# This pod will be REJECTED in restricted namespace
cat <<EOF | kubectl apply -f - -n production
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: nginx
EOF

# Error: pods "insecure-pod" is forbidden:
# violates PodSecurity "restricted:latest":
# allowPrivilegeEscalation != false,
# unrestricted capabilities,
# runAsNonRoot != true,
# seccompProfile

# This pod SUCCEEDS in restricted namespace
cat <<EOF | kubectl apply -f - -n production
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
EOF
```

---

## Винятки

### Винятки на рівні простору імен

```yaml
# Exempt specific namespaces in AdmissionConfiguration
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: PodSecurity
  configuration:
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: "baseline"
      enforce-version: "latest"
    exemptions:
      # Exempt kube-system namespace
      namespaces:
        - kube-system
      # Exempt specific users
      usernames:
        - system:serviceaccount:kube-system:*
      # Exempt specific runtime classes
      runtimeClasses:
        - gvisor
```

### Виключення системних просторів імен

```bash
# kube-system typically needs privileged access
kubectl label namespace kube-system pod-security.kubernetes.io/enforce=privileged --overwrite
```

---

## Стратегія міграції

```
┌─────────────────────────────────────────────────────────────┐
│              СТРАТЕГІЯ МІГРАЦІЇ PSA                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Фаза 1: Тільки аудит                                     │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/audit: restricted              │
│  • Всі Pod все ще створюються                              │
│  • Порушення логуються                                     │
│  • Перегляд журналів аудиту на проблеми                    │
│                                                             │
│  Фаза 2: Попередження та аудит                             │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/warn: restricted               │
│  pod-security.kubernetes.io/audit: restricted              │
│  • Розробники бачать попередження                          │
│  • Все ще неблокуючий режим                                │
│                                                             │
│  Фаза 3: Застосування Baseline, попередження Restricted    │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/enforce: baseline              │
│  pod-security.kubernetes.io/warn: restricted               │
│  • Блокування очевидних порушень                           │
│  • Попередження про restricted                              │
│                                                             │
│  Фаза 4: Повне застосування                                │
│  ─────────────────────────────────────────────────────────  │
│  pod-security.kubernetes.io/enforce: restricted            │
│  • Максимальна безпека                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Реальні сценарії іспиту

### Сценарій 1: Увімкнення режиму Restricted

```bash
# Apply restricted enforcement to namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest

# Verify label
kubectl get namespace production --show-labels
```

### Сценарій 2: Виправлення Pod для Restricted простору імен

```yaml
# Original pod (fails in restricted)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx

# Fixed pod (works in restricted)
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 101  # nginx user
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: nginx
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
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
```

### Сценарій 3: Налагодження відхилення PSA

```bash
# Check namespace labels
kubectl get namespace production -o yaml | grep -A10 labels

# Create pod and see detailed error
kubectl apply -f pod.yaml -n production 2>&1 | head -20

# Dry run to check without creating
kubectl apply -f pod.yaml -n production --dry-run=server
```

---

## Чи знали ви?

- **PSA замінив PodSecurityPolicy (PSP)**, який був оголошений застарілим у Kubernetes 1.21 та видалений у 1.25. PSA простіший і базується на мітках просторів імен.

- **Версія "latest"** слідує за версією Kubernetes. Використання "latest" означає, що політика оновлюється при оновленні Kubernetes.

- **Системні простори імен потребують privileged.** Pod у kube-system (CNI, CSI, kube-proxy) часто потребують доступ до хоста. Завжди виключайте або використовуйте рівень privileged.

- **PSA вбудований в API server** і увімкнений за замовчуванням з Kubernetes 1.25. Додаткова інсталяція не потрібна.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Застосування restricted до kube-system | Системні Pod не працюють | Використовуйте privileged для системних просторів імен |
| Без runAsNonRoot у restricted | Pod відхиляються | Додайте runAsNonRoot: true |
| Відсутній seccompProfile | Restricted вимагає його | Додайте RuntimeDefault |
| Не скинуті capabilities | Restricted вимагає скидання | Скиньте ALL |
| Пропуск фази warn | Раптові збої | Мігруйте поступово |

---

## Тест

1. **Які три стандарти безпеки Pod існують?**
   <details>
   <summary>Відповідь</summary>
   Privileged (без обмежень), Baseline (запобігає відомим підвищенням привілеїв) та Restricted (максимальна безпека). Кожен рівень прогресивно безпечніший.
   </details>

2. **Яка різниця між режимами enforce, warn та audit?**
   <details>
   <summary>Відповідь</summary>
   Enforce: Відхиляти Pod, що порушують. Warn: Дозволити, але показати попередження. Audit: Логувати в журнал аудиту, але дозволити. Можна використовувати різні профілі для кожного режиму.
   </details>

3. **Які поля контексту безпеки потрібні для профілю restricted?**
   <details>
   <summary>Відповідь</summary>
   runAsNonRoot: true, allowPrivilegeEscalation: false, capabilities.drop: ["ALL"] та seccompProfile.type: RuntimeDefault (або Localhost).
   </details>

4. **Як застосувати PSA до простору імен?**
   <details>
   <summary>Відповідь</summary>
   За допомогою міток: `pod-security.kubernetes.io/enforce: <profile>` та необов'язково `-version: latest` на просторі імен.
   </details>

---

## Практична вправа

**Завдання**: Налаштувати та протестувати Pod Security Admission.

```bash
# Step 1: Create namespace with baseline enforcement
kubectl create namespace psa-test
kubectl label namespace psa-test \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/warn=restricted

# Step 2: Verify labels
kubectl get namespace psa-test --show-labels

# Step 3: Test baseline allows regular pods
kubectl run baseline-test --image=nginx -n psa-test
kubectl get pod baseline-test -n psa-test

# Step 4: Test baseline blocks privileged
cat <<EOF | kubectl apply -f - -n psa-test
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
EOF
# Should be rejected

# Step 5: Upgrade to restricted
kubectl label namespace psa-test \
  pod-security.kubernetes.io/enforce=restricted --overwrite

# Step 6: Previous pod now shows warning at restricted level
# Delete and recreate
kubectl delete pod baseline-test -n psa-test
kubectl run restricted-test --image=nginx -n psa-test 2>&1 || echo "Rejected (expected)"

# Step 7: Create compliant pod
cat <<EOF | kubectl apply -f - -n psa-test
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
EOF

kubectl get pod compliant-pod -n psa-test

# Cleanup
kubectl delete namespace psa-test
```

**Критерії успіху**: Зрозуміти, як PSA блокує невідповідні Pod.

---

## Підсумок

**Стандарти безпеки Pod**:
- Privileged: Без обмежень
- Baseline: Блокує відомі підвищення привілеїв
- Restricted: Максимальна безпека

**Режими**:
- enforce: Блокувати порушення
- warn: Показувати попередження
- audit: Логувати порушення

**Необхідне для Restricted**:
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities.drop: ["ALL"]
- seccompProfile: RuntimeDefault

**Поради для іспиту**:
- Знайте формат міток простору імен
- Запам'ятайте вимоги restricted
- Мігруйте поступово (audit → warn → enforce)

---

## Наступний модуль

[Модуль 4.3: Управління секретами](module-4.3-secrets-management/) — Захист секретів Kubernetes.
