---
title: "Модуль 1.2: CIS Benchmarks та kube-bench"
slug: uk/k8s/cks/part1-cluster-setup/module-1.2-cis-benchmarks
sidebar:
  order: 2
---
> **Складність**: `[СЕРЕДНЯ]` — Ключова навичка аудиту безпеки
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Модуль 0.3 (Інструменти безпеки), базове адміністрування кластера

---

## Чому цей модуль важливий

CIS Kubernetes Benchmark — це золотий стандарт для конфігурації безпеки кластера. Це не суб'єктивна думка — це консенсус експертів з безпеки з усього світу щодо того, як слід зміцнювати Kubernetes.

kube-bench автоматизує перевірку вашого кластера за цими стандартами. Іспит CKS перевіряє вашу здатність запускати його, інтерпретувати результати та виправляти збої.

---

## Що таке CIS?

```
┌─────────────────────────────────────────────────────────────┐
│              ЦЕНТР ІНТЕРНЕТ-БЕЗПЕКИ                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CIS (Center for Internet Security)                        │
│  ├── Некомерційна організація                              │
│  ├── Розробляє найкращі практики безпеки                   │
│  └── Публікує стандарти для багатьох технологій            │
│                                                             │
│  CIS Kubernetes Benchmark                                  │
│  ├── 200+ перевірок безпеки                                │
│  ├── Оновлюється для кожної версії Kubernetes              │
│  ├── Охоплює площину управління, вузли, політики           │
│  └── Визнаний галуззю стандарт                             │
│                                                             │
│  Чому це важливо:                                          │
│  ├── Вимоги відповідності (SOC2, PCI-DSS)                 │
│  ├── Об'єктивне вимірювання безпеки                        │
│  ├── Стандартизоване між організаціями                      │
│  └── Зручна документація для аудиторів                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Огляд kube-bench

kube-bench — це інструмент з відкритим кодом, що перевіряє кластери Kubernetes за стандартами CIS.

```
┌─────────────────────────────────────────────────────────────┐
│              АРХІТЕКТУРА KUBE-BENCH                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │ kube-bench  │────►│ Перевірки   │────►│ Результати  │  │
│  │  Бінарник   │     │ CIS (YAML)  │     │             │  │
│  └─────────────┘     └─────────────┘     └─────────────┘  │
│         │                                       │          │
│         ▼                                       ▼          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                 Що перевіряється:                    │  │
│  │  • Конфігурація API server                          │  │
│  │  • Налаштування Controller manager                  │  │
│  │  • Налаштування Scheduler                           │  │
│  │  • Конфігурація etcd                                │  │
│  │  • Конфігурація kubelet                             │  │
│  │  • Дозволи файлів                                   │  │
│  │  • Мережеві політики                                │  │
│  │  • Безпека Pod                                      │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Запуск kube-bench

### Метод 1: Як Kubernetes Job

```bash
# Apply the kube-bench job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Wait for completion
kubectl wait --for=condition=complete job/kube-bench --timeout=120s

# View results
kubectl logs job/kube-bench

# Cleanup
kubectl delete job kube-bench
```

### Метод 2: Запуск безпосередньо на вузлі

```bash
# Download kube-bench
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.7.0/kube-bench_0.7.0_linux_amd64.tar.gz -o kube-bench.tar.gz
tar -xvf kube-bench.tar.gz

# Run on control plane node
./kube-bench run --targets=master

# Run on worker node
./kube-bench run --targets=node

# Run specific check
./kube-bench run --targets=master --check=1.2.1

# Run with specific benchmark version
./kube-bench run --benchmark=cis-1.8
```

### Метод 3: Запуск у Docker

```bash
# Run against local kubelet
docker run --rm -v /etc:/node/etc:ro \
  -v /var:/node/var:ro \
  aquasec/kube-bench:latest run --targets=node
```

---

## Розуміння виводу kube-bench

```
┌─────────────────────────────────────────────────────────────┐
│              СТРУКТУРА ВИВОДУ KUBE-BENCH                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [INFO] 1 Control Plane Security Configuration             │
│  [INFO] 1.1 Control Plane Node Configuration Files         │
│                                                             │
│  [PASS] 1.1.1 Ensure API server pod specification file     │
│               permissions are set to 600 or more restrictive│
│                                                             │
│  [FAIL] 1.1.2 Ensure API server pod specification file     │
│               ownership is set to root:root                 │
│                                                             │
│  [WARN] 1.1.3 Ensure controller manager pod specification  │
│               file permissions are set to 600              │
│                                                             │
│  Легенда статусів:                                         │
│  ─────────────────────────────────────────────────────────  │
│  [PASS] - Перевірка пройдена, конфігурація безпечна        │
│  [FAIL] - Знайдена проблема безпеки, ПОТРІБНО виправити    │
│  [WARN] - Потрібна ручна перевірка                         │
│  [INFO] - Інформаційне, не перевірка                       │
│                                                             │
│  Виправлення (показується для збоїв):                      │
│  Виконайте наступну команду на площині управління:         │
│  chown root:root /etc/kubernetes/manifests/kube-apiserver.yaml│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Структура CIS Benchmark

Стандарт організований у розділи:

```
┌─────────────────────────────────────────────────────────────┐
│              РОЗДІЛИ CIS KUBERNETES BENCHMARK               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Компоненти площини управління                          │
│     1.1 Файли конфігурації вузлів площини управління       │
│     1.2 API Server                                         │
│     1.3 Controller Manager                                 │
│     1.4 Scheduler                                          │
│                                                             │
│  2. etcd                                                   │
│     2.1 Конфігурація вузла etcd                            │
│                                                             │
│  3. Конфігурація площини управління                        │
│     3.1 Автентифікація та авторизація                      │
│     3.2 Журналювання                                       │
│                                                             │
│  4. Робочі вузли                                           │
│     4.1 Файли конфігурації робочих вузлів                  │
│     4.2 Kubelet                                            │
│                                                             │
│  5. Політики                                               │
│     5.1 RBAC та Service Accounts                           │
│     5.2 Безпека Pod                                        │
│     5.3 Мережеві політики                                  │
│     5.4 Управління Secrets                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Поширені збої CIS та виправлення

### Категорія 1.2: API Server

```yaml
# 1.2.1 - Ensure anonymous authentication is disabled
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --anonymous-auth=false  # Add this

# 1.2.5 - Ensure kubelet certificate authority is set
    - --kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt

# 1.2.6 - Ensure authorization mode is not AlwaysAllow
    - --authorization-mode=Node,RBAC  # Not AlwaysAllow

# 1.2.10 - Ensure admission plugins include EventRateLimit
    - --enable-admission-plugins=NodeRestriction,EventRateLimit

# 1.2.16 - Ensure PodSecurity admission is enabled
    - --enable-admission-plugins=NodeRestriction,PodSecurity

# 1.2.20 - Ensure audit logging is enabled
    - --audit-log-path=/var/log/kubernetes/audit.log
    - --audit-log-maxage=30
    - --audit-log-maxbackup=10
    - --audit-log-maxsize=100
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
```

### Категорія 1.3: Controller Manager

```yaml
# 1.3.2 - Ensure profiling is disabled
# Edit /etc/kubernetes/manifests/kube-controller-manager.yaml
spec:
  containers:
  - command:
    - kube-controller-manager
    - --profiling=false

# 1.3.6 - Ensure RotateKubeletServerCertificate is true
    - --feature-gates=RotateKubeletServerCertificate=true
```

### Категорія 4.2: Kubelet

```yaml
# Fix kubelet settings in /var/lib/kubelet/config.yaml

# 4.2.1 - Ensure anonymous authentication is disabled
authentication:
  anonymous:
    enabled: false

# 4.2.2 - Ensure authorization mode is not AlwaysAllow
authorization:
  mode: Webhook

# 4.2.4 - Ensure read-only port is disabled
readOnlyPort: 0

# 4.2.6 - Ensure TLS is configured
tlsCertFile: /var/lib/kubelet/pki/kubelet.crt
tlsPrivateKeyFile: /var/lib/kubelet/pki/kubelet.key

# After changes, restart kubelet
sudo systemctl restart kubelet
```

### Виправлення дозволів файлів

```bash
# 1.1.1-1.1.4: Control plane manifest file permissions
chmod 600 /etc/kubernetes/manifests/kube-apiserver.yaml
chmod 600 /etc/kubernetes/manifests/kube-controller-manager.yaml
chmod 600 /etc/kubernetes/manifests/kube-scheduler.yaml
chmod 600 /etc/kubernetes/manifests/etcd.yaml

# 1.1.5-1.1.8: Ensure ownership is root:root
chown root:root /etc/kubernetes/manifests/*.yaml

# 4.1.1-4.1.2: Kubelet config permissions
chmod 600 /var/lib/kubelet/config.yaml
chown root:root /var/lib/kubelet/config.yaml
```

---

## Реальні сценарії іспиту

### Сценарій 1: Виправлення конкретних збоїв kube-bench

```bash
# Run kube-bench and filter for failures
./kube-bench run --targets=master 2>&1 | grep -A 5 "\[FAIL\]"

# Example output:
# [FAIL] 1.2.6 Ensure --authorization-mode argument includes Node
# Remediation:
# Edit the API server pod specification file
# /etc/kubernetes/manifests/kube-apiserver.yaml
# and set --authorization-mode=Node,RBAC

# Fix by editing API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --authorization-mode=Node,RBAC

# Wait for API server to restart
kubectl get pods -n kube-system -w
```

### Сценарій 2: Генерація звіту в JSON

```bash
# Generate JSON output for parsing
./kube-bench run --json > kube-bench-results.json

# Filter critical failures
cat kube-bench-results.json | jq '.Controls[].tests[].results[] | select(.status=="FAIL")'

# Count failures by section
cat kube-bench-results.json | jq '.Controls[].tests[].results[] | select(.status=="FAIL")' | jq -s 'length'
```

### Сценарій 3: Перевірка конкретного розділу

```bash
# Run only control plane checks
./kube-bench run --targets=master --check=1.2

# Run only kubelet checks
./kube-bench run --targets=node --check=4.2

# Run specific check number
./kube-bench run --check=1.2.6
```

---

## Автоматизація виправлень

### Скрипт для виправлення поширених проблем

```bash
#!/bin/bash
# cis-remediation.sh - Fix common CIS failures

echo "Fixing file permissions..."
chmod 600 /etc/kubernetes/manifests/*.yaml 2>/dev/null
chmod 600 /var/lib/kubelet/config.yaml 2>/dev/null

echo "Fixing file ownership..."
chown root:root /etc/kubernetes/manifests/*.yaml 2>/dev/null
chown root:root /var/lib/kubelet/config.yaml 2>/dev/null

echo "Checking API server configuration..."
if ! grep -q "anonymous-auth=false" /etc/kubernetes/manifests/kube-apiserver.yaml; then
    echo "WARNING: anonymous-auth not disabled"
fi

if ! grep -q "audit-log-path" /etc/kubernetes/manifests/kube-apiserver.yaml; then
    echo "WARNING: audit logging not configured"
fi

echo "Checking kubelet configuration..."
if grep -q "anonymous:\s*enabled:\s*true" /var/lib/kubelet/config.yaml; then
    echo "WARNING: kubelet anonymous auth enabled"
fi

echo "Done. Re-run kube-bench to verify fixes."
```

---

## Рівні CIS Benchmark

```
┌─────────────────────────────────────────────────────────────┐
│              РІВНІ ПРОФІЛЮ CIS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Рівень 1 — Базова безпека                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Можна впровадити без значного операційного впливу       │
│  • Базові контролі безпеки                                 │
│  • Слід застосовувати до ВСІХ кластерів                    │
│  • Приклади:                                               │
│    - Вимкнути анонімну автентифікацію                      │
│    - Увімкнути RBAC                                        │
│    - Встановити дозволи файлів                             │
│                                                             │
│  Рівень 2 — Посилена безпека                               │
│  ─────────────────────────────────────────────────────────  │
│  • Може вимагати більше планування для впровадження        │
│  • Може вплинути на деякі робочі навантаження             │
│  • Для середовищ з високим рівнем безпеки                  │
│  • Приклади:                                               │
│    - Увімкнути журналювання аудиту                         │
│    - Обмежити доступ до API server                         │
│    - Впровадити мережеві політики                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **CIS benchmarks оновлюються регулярно.** Кожна версія Kubernetes отримує свою версію стандарту. kube-bench автоматично визначає, яку використовувати.

- **kube-bench був створений Aqua Security,** тією ж компанією, що стоїть за Trivy. Вони є основними контрибуторами інструментарію безпеки Kubernetes.

- **Не всі рекомендації CIS стосуються керованого Kubernetes.** GKE, EKS та AKS мають модифіковані стандарти, оскільки ви не можете змінювати налаштування площини управління.

- **Стандарт є публічним та безкоштовним.** Ви можете завантажити повний CIS Kubernetes Benchmark PDF з cisecurity.org (потрібна безкоштовна реєстрація).

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Запуск kube-bench лише раз | Відбувається дрейф безпеки | Плануйте регулярні сканування |
| Ігнорування елементів [WARN] | Вони все ще можуть бути проблемами | Перевірте кожне попередження |
| Виправлення без розуміння | Може зламати кластер | Уважно читайте інструкцію з виправлення |
| Не перезапускати після виправлень | Зміни не набувають чинності | Перезапустіть уражений компонент |
| Пропуск дозволів файлів | Легкі бали на іспиті | Завжди перевіряйте власника/дозволи |

---

## Тест

1. **Що означає статус [FAIL] у виводі kube-bench?**
   <details>
   <summary>Відповідь</summary>
   Проблема конфігурації безпеки, що порушує CIS benchmark і повинна бути виправлена. kube-bench надає інструкції з виправлення для кожного збою.
   </details>

2. **Де зазвичай вносяться зміни конфігурації API server?**
   <details>
   <summary>Відповідь</summary>
   У `/etc/kubernetes/manifests/kube-apiserver.yaml` для кластерів kubeadm. Pod API server автоматично перезапуститься при зміні цього файлу.
   </details>

3. **Яка команда запускає kube-bench лише для площини управління?**
   <details>
   <summary>Відповідь</summary>
   `./kube-bench run --targets=master` — запускає лише перевірки площини управління (розділи 1.x, 2.x, 3.x).
   </details>

4. **Після виправлення конфігурації kubelet, що потрібно зробити?**
   <details>
   <summary>Відповідь</summary>
   Перезапустити сервіс kubelet за допомогою `sudo systemctl restart kubelet`, щоб зміни набули чинності.
   </details>

---

## Практична вправа

**Завдання**: Запустіть kube-bench, визначте збої та виправте їх.

```bash
# Step 1: Run kube-bench as a job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s

# Step 2: Capture all failures
kubectl logs job/kube-bench | grep -E "^\[FAIL\]" > failures.txt
cat failures.txt

# Step 3: Pick one failure and find its remediation
kubectl logs job/kube-bench | grep -A 10 "$(head -1 failures.txt)"

# Step 4: Apply the fix (example: file permissions)
# SSH to control plane node
# sudo chmod 600 /etc/kubernetes/manifests/kube-apiserver.yaml

# Step 5: Re-run kube-bench to verify fix
kubectl delete job kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s
kubectl logs job/kube-bench | grep -E "^\[FAIL\]" | wc -l

# The failure count should decrease

# Cleanup
kubectl delete job kube-bench
```

**Критерії успіху**: Успішно виправте щонайменше один збій CIS benchmark та перевірте за допомогою kube-bench.

---

## Підсумок

**CIS Benchmarks**:
- Галузевий стандарт безпеки Kubernetes
- 200+ перевірок площини управління, вузлів, політик
- Два рівні: базовий (Рівень 1) та посилений (Рівень 2)

**kube-bench**:
- Автоматизує перевірку CIS benchmark
- Запускається як Job, бінарник або контейнер
- Надає інструкції з виправлення збоїв

**Поширені виправлення**:
- Дозволи файлів (chmod 600)
- Власність (chown root:root)
- Прапорці API server (редагування маніфесту)
- Конфігурація kubelet (потрібен перезапуск)

**Поради для іспиту**:
- Знайте, як запускати kube-bench
- Розумійте формат виводу
- Практикуйте застосування поширених виправлень
- Пам'ятайте перезапускати після змін

---

## Наступний модуль

[Модуль 1.3: Безпека Ingress](module-1.3-ingress-security/) — Захист контролерів ingress та завершення TLS.
