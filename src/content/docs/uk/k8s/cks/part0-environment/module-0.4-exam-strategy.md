---
title: "Модуль 0.4: Стратегія іспиту CKS"
slug: uk/k8s/cks/part0-environment/module-0.4-exam-strategy
sidebar:
  order: 4
---
> **Складність**: `[ШВИДКО]` — Критично для успіху на іспиті
>
> **Час на виконання**: 20-25 хвилин
>
> **Передумови**: Сертифікація CKA, Модулі 0.1-0.3

---

## Чому цей модуль важливий

Іспит CKS — це 2 години, ~15-20 завдань, 67% для проходження. Тиск часу реальний. Багато кандидатів, які знають матеріал, провалюються, бо погано управляють часом або застрягають на складних завданнях.

Цей модуль адаптує стратегію трьох проходів для специфічних завдань з безпеки.

---

## Стратегія безпекових трьох проходів

```
┌─────────────────────────────────────────────────────────────┐
│              СТРАТЕГІЯ ТРЬОХ ПРОХОДІВ CKS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ПРОХІД 1: Швидкі перемоги безпеки (40-50 хв)             │
│  Ціль: 1-3 хв на завдання                                  │
│  ─────────────────────────────────────────────────────────  │
│  ✓ Створити/змінити NetworkPolicy                          │
│  ✓ Виправити проблему з правами RBAC                       │
│  ✓ Застосувати існуючий профіль AppArmor                   │
│  ✓ Встановити поля securityContext                         │
│  ✓ Увімкнути журналювання аудиту                           │
│  ✓ Запустити сканування Trivy, визначити вразливості       │
│                                                             │
│  ПРОХІД 2: Завдання з інструментами (40-50 хв)            │
│  Ціль: 4-6 хв на завдання                                  │
│  ─────────────────────────────────────────────────────────  │
│  ✓ Створити профіль seccomp з нуля                        │
│  ✓ Налаштувати Pod Security Admission                      │
│  ✓ Запустити kube-bench, виправити конкретні знахідки      │
│  ✓ Створити NetworkPolicy з правилами egress               │
│  ✓ Налаштувати ServiceAccount з мінімальними правами       │
│                                                             │
│  ПРОХІД 3: Складні сценарії (20-30 хв)                    │
│  Ціль: 7+ хв на завдання                                   │
│  ─────────────────────────────────────────────────────────  │
│  ✓ Написати власне правило Falco                           │
│  ✓ Розслідувати та відреагувати на інцидент виконання     │
│  ✓ Багатокрокове зміцнення кластера                        │
│  ✓ Складна NetworkPolicy (кілька Pod, просторів імен)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Класифікація завдань

Навчіться розпізнавати складність завдання за секунди:

### Завдання проходу 1 (Швидкі)

| Патерн | Приклад | Час |
|--------|---------|-----|
| "Встановити runAsNonRoot" | Додати поле до securityContext | 1-2 хв |
| "Створити NetworkPolicy, що дозволяє..." | Одне правило ingress/egress | 2-3 хв |
| "Надати дозвіл на..." | Створити Role/RoleBinding | 2-3 хв |
| "Застосувати профіль AppArmor" | Додати анотацію | 1-2 хв |
| "Сканувати образ з Trivy" | Виконати команду, повідомити знахідки | 2-3 хв |

### Завдання проходу 2 (Середні)

| Патерн | Приклад | Час |
|--------|---------|-----|
| "Створити профіль seccomp" | Написати JSON, послатися в pod | 4-5 хв |
| "Виправити всі збої kube-bench" | Кілька змін конфігурації | 5-6 хв |
| "Налаштувати PSA для простору імен" | Мітки + тестові Pod | 4-5 хв |
| "Обмежити ServiceAccount" | RBAC + налаштування automount | 4-5 хв |
| "NetworkPolicy з кількома правилами" | Ingress + egress | 5-6 хв |

### Завдання проходу 3 (Складні)

| Патерн | Приклад | Час |
|--------|---------|-----|
| "Написати правило Falco для виявлення..." | Власна умова + вивід | 7-10 хв |
| "Розслідувати інцидент" | Прочитати журнали, визначити причину, виправити | 8-12 хв |
| "Зміцнити кластер на основі..." | Кілька компонентів | 10-15 хв |
| "Ізолювати скомпрометований Pod" | NetworkPolicy + аналіз | 8-10 хв |

---

## Бюджет часу

```
┌─────────────────────────────────────────────────────────────┐
│              БЮДЖЕТ 120 ХВИЛИН                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  0:00  ─────── Початок проходу 1 ───────                   │
│  │                                                          │
│  │     Швидкі перемоги: RBAC, базова NetworkPolicy,        │
│  │     securityContext, анотації AppArmor                   │
│  │                                                          │
│  0:50  ─────── Початок проходу 2 ───────                   │
│  │                                                          │
│  │     Завдання з інструментами: seccomp, PSA,             │
│  │     виправлення kube-bench, складні NetworkPolicies,    │
│  │     зміцнення ServiceAccount                             │
│  │                                                          │
│  1:40  ─────── Початок проходу 3 ───────                   │
│  │                                                          │
│  │     Складні: правила Falco, розслідування інцидентів,   │
│  │     багатокрокове зміцнення                              │
│  │                                                          │
│  2:00  ─────── Кінець іспиту ───────                       │
│                                                             │
│  Залиште 5 хв в кінці для перевірки!                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Поради, специфічні для безпеки

### 1. Знайте свою документацію

```bash
# Bookmark these in exam browser:

# NetworkPolicy examples
kubernetes.io/docs/concepts/services-networking/network-policies/

# Pod Security Standards
kubernetes.io/docs/concepts/security/pod-security-standards/

# seccomp profiles
kubernetes.io/docs/tutorials/security/seccomp/

# AppArmor
kubernetes.io/docs/tutorials/security/apparmor/

# Trivy
aquasecurity.github.io/trivy/

# Falco
falco.org/docs/
```

### 2. Шаблонні команди напоготові

```bash
# Trivy scan
trivy image --severity HIGH,CRITICAL <image>

# kube-bench
./kube-bench run --targets=master

# Check AppArmor profiles
cat /sys/kernel/security/apparmor/profiles

# Check seccomp support
grep SECCOMP /boot/config-$(uname -r)

# Audit logs location
/var/log/kubernetes/audit.log
```

### 3. Поширені поля Security Context

```yaml
# Memorize this pattern
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

### 4. Патерни NetworkPolicy

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress

# Allow specific pod
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app
spec:
  podSelector:
    matchLabels:
      app: web
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - port: 80
```

---

## Поради щодо середовища іспиту

### Розташування інструментів безпеки

| Інструмент | Розташування на іспиті |
|------------|------------------------|
| Trivy | Попередньо встановлений або наданий |
| Falco | Працює в кластері або можна встановити |
| kube-bench | Завантажити або маніфест Job |
| kubesec | Може потребувати завантаження |

### Розташування файлів

| Файл | Шлях |
|------|------|
| Маніфест API server | `/etc/kubernetes/manifests/kube-apiserver.yaml` |
| Конфігурація kubelet | `/var/lib/kubelet/config.yaml` |
| Політика аудиту | `/etc/kubernetes/audit-policy.yaml` |
| Профілі seccomp | `/var/lib/kubelet/seccomp/` |
| Профілі AppArmor | `/etc/apparmor.d/` |

---

## Коли пропускати

**Пропускайте негайно, якщо**:
- Завдання вимагає інструмент, яким ви ніколи не користувалися
- Складне правило Falco з незнайомим синтаксисом
- Мульти-простір імен NetworkPolicy з нечіткими вимогами

**Поверніться, якщо дозволить час**. Часткові бали існують — здайте хоч щось.

---

## Контрольний список перевірки

Перед переходом до наступного завдання:

```bash
# For pods/deployments
kubectl get pods -n <namespace>  # Running?

# For NetworkPolicy
kubectl describe networkpolicy <name>  # Applied?

# For RBAC
kubectl auth can-i <verb> <resource> --as=<user>  # Works?

# For security context
kubectl get pod <name> -o yaml | grep -A 10 securityContext

# For Trivy
trivy image <image>  # Scans correctly?
```

---

## Чи знали ви?

- **67% прохідний бал означає, що можна пропустити ~5-6 завдань** з 15-20 і все ще пройти. Не панікуйте, якщо щось пропускаєте.

- **Часткові бали можливі.** Навіть неповні відповіді можуть принести бали. Завжди здавайте хоч щось.

- **Іспит з відкритими ресурсами.** Ваш виклик — знайти інформацію швидко, а не запам'ятати все.

- **Завдання з безпеки часто мають кілька правильних підходів.** Іспит перевіряє результат, а не точний метод.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Починати зі складних завдань | Витрачений час, втрачена впевненість | Стратегія трьох проходів |
| Не читати завдання повністю | Пропуск вимог | Читайте двічі перед тим, як друкувати |
| Забути простір імен | Зміни в неправильному просторі імен | Завжди `-n namespace` |
| Не перевіряти | Часткові рішення | Перевіряйте перед переходом |
| Надмірне ускладнення | Простого рішення було достатньо | Відповідайте вимогам точно |

---

## Тест

1. **У стратегії трьох проходів, які завдання слід робити першими?**
   <details>
   <summary>Відповідь</summary>
   Швидкі перемоги (Прохід 1): Прості виправлення RBAC, базові NetworkPolicies, доповнення securityContext, додавання анотацій AppArmor. Завдання на 1-3 хвилини кожне.
   </details>

2. **Скільки часу слід залишити на Прохід 3 (складні завдання)?**
   <details>
   <summary>Відповідь</summary>
   20-30 хвилин. Складні завдання на кшталт правил Falco та розслідування інцидентів потребують більше часу. Але не починайте з них — заробляйте бали швидкими перемогами спершу.
   </details>

3. **Що робити, якщо зустрічаєте повністю незнайоме завдання?**
   <details>
   <summary>Відповідь</summary>
   Позначте його та пропустіть. Поверніться в Проході 3, якщо дозволить час. Витратити 15 хвилин на одне завдання, яке не можете розв'язати, — це витрата часу, краще витраченого на завдання, які можете виконати.
   </details>

4. **Чому потрібно перевіряти кожне завдання перед переходом?**
   <details>
   <summary>Відповідь</summary>
   Часткові рішення не зараховуються. NetworkPolicy, яка не застосовується, Pod, який не запускається, або RBAC, що не працює, отримують нуль балів. Перевірка це виявляє.
   </details>

---

## Практична вправа

**Завдання**: Практикуйте управління часом із зразковими завданнями.

```bash
# Simulate exam conditions:
# Set a 15-minute timer for these 5 tasks
# START YOUR TIMER NOW!

# Task 1 (2 min): Create NetworkPolicy
kubectl create namespace secure

cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# Verify:
kubectl get networkpolicy -n secure

# Task 2 (2 min): Fix security context
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
  namespace: secure
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      runAsUser: 1000
      runAsNonRoot: true
EOF

# Verify:
kubectl get pod insecure-pod -n secure -o jsonpath='{.spec.containers[0].securityContext}'
echo ""

# Task 3 (3 min): RBAC
kubectl create serviceaccount app-sa -n secure

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: secure
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: secure
subjects:
- kind: ServiceAccount
  name: app-sa
  namespace: secure
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF

# Verify:
kubectl auth can-i list pods -n secure --as=system:serviceaccount:secure:app-sa

# Task 4 (4 min): Trivy scan
# (Requires Trivy installed - skip if not available)
trivy image --severity CRITICAL nginx:1.20 2>/dev/null || echo "Trivy not installed - would scan for CVEs"

# Task 5 (4 min): AppArmor
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web
  namespace: secure
  annotations:
    container.apparmor.security.beta.kubernetes.io/web: runtime/default
spec:
  containers:
  - name: web
    image: nginx:alpine
    securityContext:
      runAsNonRoot: false  # nginx needs root initially
EOF

# Verify:
kubectl get pod web -n secure -o jsonpath='{.metadata.annotations}'
echo ""

# STOP TIMER - How did you do?
echo "=== Task Summary ==="
kubectl get networkpolicy,pods,role,rolebinding,sa -n secure

# Cleanup
kubectl delete namespace secure
```

**Критерії успіху**: Виконайте щонайменше 4/5 завдань за 15 хвилин.

---

## Підсумок

**Стратегія трьох проходів для CKS**:
- Прохід 1 (50 хв): Швидкі перемоги — RBAC, базова NetworkPolicy, securityContext
- Прохід 2 (50 хв): Завдання з інструментами — seccomp, PSA, kube-bench
- Прохід 3 (20 хв): Складні — правила Falco, реагування на інциденти

**Ключові принципи**:
- Заробляйте бали рано швидкими перемогами
- Пропускайте незнайомі завдання, повертайтеся пізніше
- Перевіряйте кожне рішення
- Використовуйте документацію ефективно
- Залиште час для перевірки

**Пам'ятайте**: 67% для проходження. Ви можете пропустити деякі завдання і все ще успішно скласти.

---

## Частина 0 завершена!

Ви закінчили розділ **Налаштування середовища**. Тепер у вас є:
- Розуміння формату іспиту CKS та доменів
- Лабораторія безпеки з основними інструментами
- Вправність із Trivy, Falco, kube-bench
- Стратегія іспиту для завдань з безпеки

**Наступна частина**: [Частина 1: Налаштування кластера](../part1-cluster-setup/module-1.1-network-policies/) — Глибоке занурення в мережеву безпеку.
