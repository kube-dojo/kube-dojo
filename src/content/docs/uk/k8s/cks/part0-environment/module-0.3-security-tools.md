---
title: "Модуль 0.3: Опанування інструментів безпеки"
slug: uk/k8s/cks/part0-environment/module-0.3-security-tools
sidebar:
  order: 3
---
> **Складність**: `[СЕРЕДНЯ]` — Основні інструменти іспиту
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Модуль 0.2 (Налаштування лабораторії безпеки)

---

## Чому цей модуль важливий

Три інструменти домінують у CKS: **Trivy**, **Falco** та **kube-bench**. Іспит очікує, що ви будете використовувати їх вправно — не просто виконувати базові команди, а інтерпретувати вивід, змінювати конфігурації та усувати проблеми.

Цей модуль формує цю вправність.

---

## Trivy: Сканування вразливостей образів

### Базове сканування

```bash
# Scan an image
trivy image nginx:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL nginx:latest

# Output as JSON (for automation)
trivy image -f json nginx:latest > scan-results.json

# Scan and fail if vulnerabilities found
trivy image --exit-code 1 --severity CRITICAL nginx:latest
```

### Розуміння виводу Trivy

```
┌─────────────────────────────────────────────────────────────┐
│              ПОЯСНЕННЯ ВИВОДУ TRIVY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  nginx:latest (debian 12.4)                                │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  Усього: 142 (UNKNOWN: 0, LOW: 89, MEDIUM: 42,            │
│              HIGH: 10, CRITICAL: 1)                        │
│                                                             │
│  ┌────────────┬──────────┬──────────┬─────────────────┐    │
│  │ Бібліотека │ ID вразл.│ Серйозн. │ Виправлена верс.│    │
│  ├────────────┼──────────┼──────────┼─────────────────┤    │
│  │ openssl    │ CVE-2024-│ CRITICAL │ 3.0.13-1        │    │
│  │            │ XXXX     │          │                 │    │
│  │ libcurl    │ CVE-2024-│ HIGH     │ 7.88.1-10+d12u6│    │
│  │            │ YYYY     │          │                 │    │
│  └────────────┴──────────┴──────────┴─────────────────┘    │
│                                                             │
│  Ключові стовпці:                                          │
│  - Бібліотека: Уражений пакет                              │
│  - ID вразливості: Ідентифікатор CVE (можна шукати)       │
│  - Серйозність: CRITICAL > HIGH > MEDIUM > LOW            │
│  - Виправлена версія: Оновіть до цієї версії              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Типи сканування

```bash
# Image scan (most common for CKS)
trivy image nginx:1.25

# Filesystem scan (scan local directory)
trivy fs /path/to/project

# Config scan (find misconfigurations in K8s YAML)
trivy config ./manifests/

# Kubernetes scan (scan running cluster)
trivy k8s --report summary cluster
```

### Практичні сценарії іспиту

```bash
# Scenario 1: Find images with CRITICAL vulnerabilities
trivy image --severity CRITICAL myregistry/myapp:v1.0

# Scenario 2: Scan all images in a namespace
for img in $(kubectl get pods -n production -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u); do
  echo "Scanning: $img"
  trivy image --severity HIGH,CRITICAL "$img"
done

# Scenario 3: CI/CD gate - fail build if vulnerabilities
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:latest

# Scenario 4: Generate report for compliance
trivy image -f json -o report.json nginx:latest
```

---

## Falco: Виявлення загроз у реальному часі

### Як працює Falco

```
┌─────────────────────────────────────────────────────────────┐
│              АРХІТЕКТУРА FALCO                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │ Системні виклики│ ← Кожен syscall проходить через ядро  │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  eBPF/Модуль    │ ← Драйвер Falco перехоплює події      │
│  │     ядра        │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  Рушій Falco    │ ← Порівнює події з правилами          │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  Файл правил    │ ← YAML-правила визначають підозрілу   │
│  │  /etc/falco/    │    поведінку                           │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  Вивід сповіщень│ ← stdout, файл, Slack тощо            │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Перегляд сповіщень Falco

```bash
# Check Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco -f

# Example alert:
# 14:23:45.123456789: Warning Shell spawned in container
#   (user=root container_id=abc123 container_name=nginx
#   shell=bash parent=entrypoint.sh cmdline=bash)
```

### Розуміння правил Falco

```yaml
# Falco rule structure
- rule: Terminal shell in container
  desc: A shell was spawned in a container
  condition: >
    spawned_process and
    container and
    shell_procs
  output: >
    Shell spawned in container
    (user=%user.name container=%container.name shell=%proc.name)
  priority: WARNING
  tags: [container, shell, mitre_execution]

# Key components:
# - rule: Name of the rule
# - desc: Human-readable description
# - condition: When to trigger (Falco filter syntax)
# - output: What to log when triggered
# - priority: EMERGENCY, ALERT, CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG
# - tags: Categories for filtering
```

### Поширені умови Falco

```yaml
# Detect shell in container
condition: spawned_process and container and shell_procs

# Detect sensitive file access
condition: >
  open_read and
  container and
  (fd.name startswith /etc/shadow or fd.name startswith /etc/passwd)

# Detect network connection
condition: >
  (evt.type in (connect, accept)) and
  container and
  fd.net != ""

# Detect privilege escalation
condition: >
  spawned_process and
  container and
  proc.name = sudo
```

### Зміна правил Falco

```bash
# Falco rules are in /etc/falco/
# - falco_rules.yaml: Default rules (don't edit)
# - falco_rules.local.yaml: Your custom rules

# Method 1: Helm values (RECOMMENDED — persists across restarts)
# Create a values file with custom rules
cat <<EOF > falco-custom-rules.yaml
customRules:
  custom-rules.yaml: |-
    - rule: Detect cat of sensitive files
      desc: Someone is reading sensitive files
      condition: >
        spawned_process and
        container and
        proc.name = cat and
        (proc.args contains "/etc/shadow" or proc.args contains "/etc/passwd")
      output: "Sensitive file read (user=%user.name file=%proc.args container=%container.name)"
      priority: WARNING
EOF

# Upgrade Falco with custom rules
helm upgrade falco falcosecurity/falco \
  --namespace falco \
  --reuse-values \
  -f falco-custom-rules.yaml

# Method 2: ConfigMap (alternative — also persists)
kubectl create configmap falco-custom-rules \
  --namespace falco \
  --from-literal=custom-rules.yaml='
- rule: Detect cat of sensitive files
  desc: Someone is reading sensitive files
  condition: >
    spawned_process and
    container and
    proc.name = cat and
    (proc.args contains "/etc/shadow" or proc.args contains "/etc/passwd")
  output: "Sensitive file read (user=%user.name file=%proc.args container=%container.name)"
  priority: WARNING
'

# Then reference the ConfigMap in Helm values or mount it manually
# Restart Falco pods to pick up changes
kubectl rollout restart daemonset/falco -n falco
```

> **Важливо**: Ніколи не змінюйте правила через exec у Pod Falco — ці зміни зникнуть при перезапуску Pod. Завжди використовуйте значення Helm або ConfigMaps, щоб власні правила зберігалися після оновлень та перезапусків.

### Тестування виявлення Falco

```bash
# Trigger shell detection
kubectl run test --image=nginx --restart=Never
kubectl exec -it test -- /bin/bash

# Check Falco logs for alert
kubectl logs -n falco -l app.kubernetes.io/name=falco | grep "shell"

# Cleanup
kubectl delete pod test
```

---

## kube-bench: Аудит CIS Benchmark

### Запуск kube-bench

```bash
# Run as Kubernetes Job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench

# Run specific checks
./kube-bench run --targets=master  # Control plane only
./kube-bench run --targets=node    # Worker nodes only
./kube-bench run --targets=etcd    # etcd only

# Run specific benchmark
./kube-bench run --benchmark cis-1.8  # CIS 1.8 benchmark
```

### Розуміння виводу kube-bench

```
┌─────────────────────────────────────────────────────────────┐
│              ПОЯСНЕННЯ ВИВОДУ KUBE-BENCH                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [INFO] 1 Control Plane Security Configuration             │
│  [INFO] 1.1 Control Plane Node Configuration Files         │
│                                                             │
│  [PASS] 1.1.1 Ensure API server pod file permissions       │
│  [PASS] 1.1.2 Ensure API server pod file ownership         │
│  [FAIL] 1.1.3 Ensure controller manager file permissions   │
│  [WARN] 1.1.4 Ensure scheduler pod file permissions        │
│                                                             │
│  Значення статусів:                                        │
│  [PASS] - Перевірка пройдена                               │
│  [FAIL] - Знайдена проблема безпеки, потрібно виправити    │
│  [WARN] - Потрібна ручна перевірка                         │
│  [INFO] - Лише інформаційне                                │
│                                                             │
│  Виправлення для 1.1.3:                                    │
│  Виконайте: chmod 600 /etc/kubernetes/manifests/controller.yaml│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Поширені помилки CIS та виправлення

| Перевірка | Проблема | Виправлення |
|-----------|----------|-------------|
| 1.2.1 | Увімкнена анонімна автентифікація | `--anonymous-auth=false` на API server |
| 1.2.6 | Немає журналювання аудиту | Налаштуйте політику аудиту та шлях журналу |
| 1.2.16 | Немає admission plugins | Увімкніть PodSecurity admission |
| 4.2.1 | Анонімна автентифікація kubelet | `--anonymous-auth=false` на kubelet |
| 4.2.6 | TLS не застосовується | Налаштуйте TLS-сертифікати kubelet |

```bash
# Fix API server anonymous auth
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --anonymous-auth=false

# Fix kubelet anonymous auth
# Edit /var/lib/kubelet/config.yaml
# Set: authentication.anonymous.enabled: false

# Restart kubelet after config changes
sudo systemctl restart kubelet
```

---

## kubesec: Статичний аналіз маніфестів

### Сканування маніфестів

```bash
# Scan a YAML file
kubesec scan deployment.yaml

# Scan from stdin
cat pod.yaml | kubesec scan /dev/stdin

# Example output:
# [
#   {
#     "score": -30,
#     "scoring": {
#       "passed": [...],
#       "critical": ["containers[] .securityContext .privileged == true"],
#       "advise": [...]
#     }
#   }
# ]
```

### Розуміння оцінок kubesec

```
┌─────────────────────────────────────────────────────────────┐
│              ОЦІНЮВАННЯ KUBESEC                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Діапазони оцінок:                                         │
│  ─────────────────────────────────────────────────────────  │
│  10+   : Добрий стан безпеки                               │
│  0-10  : Прийнятний, є простір для покращення              │
│  < 0   : Проблеми безпеки, потрібен перегляд               │
│  -30   : Критичні проблеми (напр., привілейований          │
│           контейнер)                                        │
│                                                             │
│  Модифікатори оцінки:                                      │
│  +1 : runAsNonRoot: true                                   │
│  +1 : readOnlyRootFilesystem: true                         │
│  +1 : resources.limits визначені                           │
│  -30: privileged: true (критично)                          │
│  -1 : немає securityContext                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **Trivy був створений Aqua Security** і зараз є найпопулярнішим сканером вразливостей з відкритим кодом. Він швидший за Clair та зручніший у використанні.

- **Falco обробляє мільйони подій на секунду**, використовуючи eBPF з майже нульовими накладними витратами. Спочатку він був створений Sysdig.

- **CIS Benchmarks** розробляються Центром інтернет-безпеки за участі експертів з безпеки з усього світу. Вони є де-факто стандартом для аудиту безпеки Kubernetes.

- **kubesec був створений Control Plane** (тією ж командою, яка стоїть за CNCF-сертифікованим навчанням з безпеки Kubernetes).

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Запам'ятовування лише команд | Потрібно інтерпретувати вивід | Практикуйте аналіз результатів |
| Ігнорування серйозності "MEDIUM" | Вони накопичують ризик | Переглядайте всі знахідки |
| Не налаштовуєте правила Falco | Стандартні правила можуть пропустити загрози | Додайте правила, специфічні для середовища |
| Пропуск практики виправлення | Іспит просить ВИПРАВИТИ проблеми | Практикуйте застосування виправлень |
| Запуск інструментів лише раз | Потрібна м'язова пам'ять | Інтегруйте в щоденну практику |

---

## Тест

1. **Який прапорець Trivy робить сканування невдалим, якщо знайдені CRITICAL вразливості?**
   <details>
   <summary>Відповідь</summary>
   `--exit-code 1 --severity CRITICAL`. Прапорець exit-code контролює, чи повертає Trivy ненульовий код при знахідках.
   </details>

2. **Де зазвичай розміщуються власні правила Falco?**
   <details>
   <summary>Відповідь</summary>
   `/etc/falco/falco_rules.local.yaml`. Стандартні правила у `falco_rules.yaml` не слід редагувати безпосередньо.
   </details>

3. **Що означає статус [FAIL] у виводі kube-bench?**
   <details>
   <summary>Відповідь</summary>
   Проблема конфігурації безпеки, яку слід виправити. kube-bench надає інструкції з виправлення для кожної невдалої перевірки.
   </details>

4. **Що означає від'ємна оцінка kubesec?**
   <details>
   <summary>Відповідь</summary>
   Проблеми безпеки, які потребують перегляду. Критичні проблеми на кшталт `privileged: true` можуть призвести до оцінок -30 або нижче.
   </details>

---

## Практична вправа

**Завдання**: Використайте всі чотири інструменти безпеки.

```bash
# 1. Scan an image with Trivy
echo "=== Trivy Scan ==="
trivy image --severity HIGH,CRITICAL nginx:1.25

# 2. Check Falco is detecting events
echo "=== Falco Test ==="
kubectl run falco-test --image=nginx --restart=Never
kubectl exec falco-test -- cat /etc/passwd
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=5
kubectl delete pod falco-test

# 3. Run kube-bench
echo "=== kube-bench ==="
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s
kubectl logs job/kube-bench | grep -E "^\[FAIL\]" | head -10
kubectl delete job kube-bench

# 4. Scan a manifest with kubesec
echo "=== kubesec Scan ==="
cat <<EOF | kubesec scan /dev/stdin
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
EOF
```

**Критерії успіху**: Запустіть усі інструменти, інтерпретуйте вивід, визначте проблеми безпеки.

---

## Підсумок

**Trivy** (Сканування образів):
- `trivy image <image>` — Базове сканування
- `--severity HIGH,CRITICAL` — Фільтр за серйозністю
- `--exit-code 1` — Невдача при знахідках

**Falco** (Виявлення в реальному часі):
- Моніторить системні виклики в реальному часі
- Правила визначають підозрілу поведінку
- Власні правила у `falco_rules.local.yaml`

**kube-bench** (CIS Benchmarks):
- Перевіряє кластер за стандартами CIS
- [FAIL] = потрібне виправлення
- Надає кроки виправлення

**kubesec** (Статичний аналіз):
- Оцінює YAML-маніфести
- Від'ємна оцінка = проблеми безпеки
- Швидка перевірка перед розгортанням

---

## Наступний модуль

[Модуль 0.4: Стратегія іспиту CKS](module-0.4-exam-strategy/) — Підхід до іспиту з фокусом на безпеку.
