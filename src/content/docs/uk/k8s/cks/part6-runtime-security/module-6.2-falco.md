---
title: "Модуль 6.2: Безпека виконання з Falco"
slug: uk/k8s/cks/part6-runtime-security/module-6.2-falco
sidebar:
  order: 2
---
> **Складність**: `[MEDIUM]` — критична навичка CKS
>
> **Час на виконання**: 50-55 хвилин
>
> **Передумови**: Модуль 6.1 (Журнали аудиту), основи системних викликів Linux

---

## Чому цей модуль важливий

Журнали аудиту повідомляють, що сталося через API. Falco повідомляє, що відбувається всередині контейнерів під час виконання. Він виявляє підозрілі системні виклики, доступ до файлів та мережеву активність, які можуть свідчити про злом.

CKS вимагає розуміння Falco для виявлення загроз під час виконання.

---

## Що таке Falco?

```
┌─────────────────────────────────────────────────────────────┐
│              ОГЛЯД FALCO                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Falco = Рушій безпеки виконання                           │
│  ─────────────────────────────────────────────────────────  │
│  • Відкритий код (CNCF graduated)                          │
│  • Видимість на рівні ядра                                 │
│  • Сповіщення в реальному часі                             │
│  • Гнучко налаштовувані правила                            │
│                                                             │
│  Як працює Falco:                                          │
│                                                             │
│  Контейнер ──► syscalls ──► Ядро ──► Драйвер Falco        │
│                                               │             │
│                                               ▼             │
│                                       ┌──────────────┐     │
│                                       │ Рушій Falco  │     │
│                                       │  ┌────────┐  │     │
│                                       │  │Правила │  │     │
│                                       │  └────────┘  │     │
│                                       └──────┬───────┘     │
│                                              │              │
│                                              ▼              │
│                                       Сповіщення/Логи      │
│                                                             │
│  Виявляє:                                                  │
│  ├── Оболонку, запущену в контейнері                      │
│  ├── Читання конфіденційних файлів (/etc/shadow)          │
│  ├── Підвищення привілеїв процесу                         │
│  ├── Неочікувані мережеві з'єднання                       │
│  └── Спроби виходу з контейнера                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Встановлення Falco

### У Kubernetes (DaemonSet)

```bash
# Add Falco Helm repo
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install Falco
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# Check installation
kubectl get pods -n falco
```

### На хості Linux

```bash
# Add Falco repository (Debian/Ubuntu)
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] https://download.falco.org/packages/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/falcosecurity.list

# Install
sudo apt update && sudo apt install -y falco

# Start Falco
sudo systemctl start falco
sudo systemctl enable falco

# View logs
sudo journalctl -u falco -f
```

---

## Архітектура Falco

```
┌─────────────────────────────────────────────────────────────┐
│              КОМПОНЕНТИ FALCO                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Драйвер (модуль ядра або eBPF)                           │
│  ─────────────────────────────────────────────────────────  │
│  • Захоплює системні виклики з ядра                        │
│  • Мінімальні накладні витрати                             │
│  • Варіанти: модуль ядра, eBPF probe, userspace           │
│                                                             │
│  Рушій (libsinsp + libscap)                                │
│  ─────────────────────────────────────────────────────────  │
│  • Обробляє події системних викликів                       │
│  • Збагачує метаданими контейнера/K8s                     │
│  • Оцінює відповідно до правил                             │
│                                                             │
│  Рушій правил                                              │
│  ─────────────────────────────────────────────────────────  │
│  • Визначення правил на основі YAML                       │
│  • Умови з використанням синтаксису фільтрів Falco        │
│  • Налаштовувані пріоритети та виходи                     │
│                                                             │
│  Канали виводу                                             │
│  ─────────────────────────────────────────────────────────  │
│  • stdout/stderr                                           │
│  • Файл                                                    │
│  • Syslog                                                  │
│  • HTTP webhook (Falcosidekick)                           │
│  • gRPC                                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Правила Falco

### Структура правила

```yaml
# A Falco rule has these components:
- rule: <name>
  desc: <description>
  condition: <filter expression>
  output: <output message with fields>
  priority: <severity level>
  tags: [list, of, tags]
  enabled: true/false
```

### Приклади вбудованих правил

```yaml
# Detect shell spawned in container
- rule: Terminal shell in container
  desc: A shell was used as the entrypoint/exec point into a container
  condition: >
    spawned_process and container and
    shell_procs and proc.tty != 0
  output: >
    A shell was spawned in a container
    (user=%user.name container=%container.name shell=%proc.name
    parent=%proc.pname cmdline=%proc.cmdline)
  priority: NOTICE
  tags: [container, shell, mitre_execution]

# Detect sensitive file read
- rule: Read sensitive file untrusted
  desc: Attempt to read sensitive files from untrusted process
  condition: >
    sensitive_files and open_read and
    not proc.name in (allowed_readers)
  output: >
    Sensitive file opened (user=%user.name command=%proc.cmdline
    file=%fd.name container=%container.name)
  priority: WARNING
  tags: [filesystem, mitre_credential_access]

# Detect unexpected outbound connection
- rule: Unexpected outbound connection
  desc: Container making outbound connection to internet
  condition: >
    outbound and container and
    not allowed_outbound
  output: >
    Unexpected outbound connection (container=%container.name
    command=%proc.cmdline connection=%fd.name)
  priority: WARNING
  tags: [network, mitre_command_and_control]
```

---

## Синтаксис фільтрів Falco

### Поширені поля

```yaml
# Process fields
proc.name          # Process name (e.g., "bash")
proc.pname         # Parent process name
proc.cmdline       # Full command line
proc.pid           # Process ID
proc.ppid          # Parent process ID
proc.exepath       # Executable path

# User fields
user.name          # Username
user.uid           # User ID

# Container fields
container.name     # Container name
container.id       # Container ID
container.image    # Image name
k8s.pod.name       # Kubernetes pod name
k8s.ns.name        # Kubernetes namespace

# File fields
fd.name            # File/socket name
fd.directory       # Directory name
fd.filename        # Base filename

# Network fields
fd.sip             # Source IP
fd.dip             # Destination IP
fd.sport           # Source port
fd.dport           # Destination port
```

### Оператори та макроси

```yaml
# Operators
=, !=              # Equality
<, <=, >, >=       # Comparison
contains           # String contains
startswith         # String starts with
endswith           # String ends with
in                 # List membership
pmatch             # Prefix match for paths

# Logical operators
and, or, not

# Built-in macros
spawned_process    # A new process was spawned
open_read          # File opened for reading
open_write         # File opened for writing
container          # Event from a container
outbound           # Outbound network connection
inbound            # Inbound network connection
```

---

## Власні правила

### Створення власних правил

```yaml
# /etc/falco/rules.d/custom-rules.yaml

# Detect kubectl exec
- rule: kubectl exec into pod
  desc: Detect kubectl exec or attach to a pod
  condition: >
    spawned_process and container and
    proc.name in (bash, sh, ash) and
    proc.pname in (runc, containerd-shim)
  output: >
    kubectl exec detected (user=%user.name pod=%k8s.pod.name
    namespace=%k8s.ns.name command=%proc.cmdline)
  priority: WARNING
  tags: [k8s, exec]

# Detect crypto miner
- rule: Detect cryptocurrency miner
  desc: Detect process names associated with crypto mining
  condition: >
    spawned_process and
    proc.name in (xmrig, cpuminer, minerd, cgminer, bfgminer)
  output: >
    Cryptocurrency miner detected (process=%proc.name
    cmdline=%proc.cmdline container=%container.name)
  priority: CRITICAL
  tags: [cryptomining]

# Detect container escape via mount
- rule: Container escape via mount
  desc: Detect attempts to escape container via host filesystem mount
  condition: >
    container and
    (evt.type = mount or evt.type = umount) and
    not proc.name in (mount, umount)
  output: >
    Container mount attempt (command=%proc.cmdline
    container=%container.name)
  priority: CRITICAL
  tags: [container_escape]
```

### Використання списків та макросів

```yaml
# Define a list
- list: allowed_processes
  items: [nginx, python, node, java]

# Define a macro
- macro: in_allowed_processes
  condition: proc.name in (allowed_processes)

# Use in rule
- rule: Unexpected process in production
  desc: Non-whitelisted process running in production namespace
  condition: >
    spawned_process and
    container and
    k8s.ns.name = "production" and
    not in_allowed_processes
  output: >
    Unexpected process (proc=%proc.name pod=%k8s.pod.name
    namespace=%k8s.ns.name)
  priority: WARNING
```

---

## Конфігурація Falco

### Основна конфігурація

```yaml
# /etc/falco/falco.yaml

# Output configuration
json_output: true
json_include_output_property: true

# Buffered outputs
buffered_outputs: false

# File output
file_output:
  enabled: true
  keep_alive: false
  filename: /var/log/falco/events.json

# Stdout output
stdout_output:
  enabled: true

# Syslog output
syslog_output:
  enabled: false

# HTTP output (webhook)
http_output:
  enabled: true
  url: http://falcosidekick:2801

# Rules files
rules_file:
  - /etc/falco/falco_rules.yaml
  - /etc/falco/falco_rules.local.yaml
  - /etc/falco/rules.d
```

### Рівні пріоритету

```yaml
# Рівні пріоритету Falco (від найвищого до найнижчого)
EMERGENCY   # Система непрацездатна
ALERT       # Необхідні негайні дії
CRITICAL    # Критичні умови
ERROR       # Умови помилки
WARNING     # Попередження
NOTICE      # Нормальні, але значущі
INFO        # Інформаційні повідомлення
DEBUG       # Повідомлення рівня налагодження
```

---

## Реальні сценарії іспиту

### Сценарій 1: Виявлення оболонки в контейнері

```bash
# Check if Falco is running
sudo systemctl status falco

# Create rule to detect shell
cat <<EOF | sudo tee /etc/falco/rules.d/shell-detection.yaml
- rule: Shell in container
  desc: Detect shell spawned in container
  condition: >
    spawned_process and
    container and
    proc.name in (bash, sh, ash, zsh)
  output: >
    Shell spawned (container=%container.name shell=%proc.name
    cmdline=%proc.cmdline user=%user.name)
  priority: WARNING
  tags: [shell, container]
EOF

# Restart Falco
sudo systemctl restart falco

# Test by exec into a pod
kubectl exec -it nginx-pod -- /bin/bash

# Check Falco logs
sudo grep "Shell spawned" /var/log/falco/events.json | jq .
```

### Сценарій 2: Виявлення доступу до конфіденційних файлів

```yaml
# /etc/falco/rules.d/sensitive-files.yaml
- list: sensitive_files
  items:
    - /etc/shadow
    - /etc/passwd
    - /etc/kubernetes/pki
    - /var/run/secrets/kubernetes.io

- rule: Access to sensitive files
  desc: Detect reads of sensitive system files
  condition: >
    open_read and
    fd.name in (sensitive_files)
  output: >
    Sensitive file accessed (file=%fd.name user=%user.name
    process=%proc.name container=%container.name)
  priority: WARNING
  tags: [filesystem, sensitive]
```

### Сценарій 3: Сповіщення про мережеву активність

```yaml
# /etc/falco/rules.d/network-rules.yaml
- rule: Unexpected outbound connection
  desc: Container making unexpected outbound connection
  condition: >
    outbound and
    container and
    fd.dport in (22, 23, 3389)
  output: >
    Suspicious outbound connection (container=%container.name
    process=%proc.cmdline dest=%fd.sip:%fd.dport)
  priority: CRITICAL
  tags: [network, lateral_movement]
```

---

## Аналіз виводу Falco

### Аналіз JSON виводу Falco

```bash
# View recent alerts
tail -100 /var/log/falco/events.json | jq .

# Count alerts by rule
cat /var/log/falco/events.json | jq -r '.rule' | sort | uniq -c | sort -rn

# Find critical alerts
cat /var/log/falco/events.json | jq 'select(.priority == "Critical")'

# Find alerts from specific namespace
cat /var/log/falco/events.json | jq 'select(.output_fields["k8s.ns.name"] == "production")'

# Find shell alerts
cat /var/log/falco/events.json | jq 'select(.rule | contains("shell"))'
```

---

## Чи знали ви?

- **Falco використовує eBPF** (extended Berkeley Packet Filter) як типовий драйвер у новіших версіях. eBPF безпечніший та більш портативний, ніж модулі ядра.

- **Falco є проєктом CNCF зі статусом graduated**, що означає готовність до продакшену та широке впровадження. Це стандарт де-факто для безпеки виконання Kubernetes.

- **Правила Falco подібні до фільтрів Sysdig**. Sysdig (компанія, що стоїть за Falco) створила синтаксис фільтрів.

- **Falcosidekick** — супутній інструмент, що маршрутизує сповіщення Falco до Slack, Teams, PagerDuty, SIEM-систем та 40+ інших виходів.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Занадто багато увімкнених правил | Втома від сповіщень | Почніть з критичних правил |
| Не налаштовані правила | Хибні спрацювання | Додайте винятки для відомої поведінки |
| Ігнорування сповіщень | Пропущені зломи | Налаштуйте належний конвеєр сповіщень |
| Правила не завантажені | Немає виявлення | Перевірте /var/log/falco на помилки |
| Відсутні метадані контейнера | Важко розслідувати | Переконайтеся, що збагачення K8s увімкнено |

---

## Тест

1. **Що моніторить Falco для виявлення загроз?**
   <details>
   <summary>Відповідь</summary>
   Falco моніторить системні виклики (syscalls) з ядра. Він перехоплює виклики як open, exec, connect тощо та оцінює їх відповідно до правил.
   </details>

2. **Яка різниця між правилом Falco та макросом?**
   <details>
   <summary>Відповідь</summary>
   Правило визначає повне виявлення з умовою, виводом та пріоритетом. Макрос — це багаторазовий фрагмент умови, який можна використовувати в кількох правилах.
   </details>

3. **Як додати власні правила Falco без зміни файлу типових правил?**
   <details>
   <summary>Відповідь</summary>
   Створіть файли в каталозі `/etc/falco/rules.d/`. Falco автоматично завантажує всі YAML файли з цього каталогу.
   </details>

4. **Які поля Falco ідентифікують контекст Kubernetes?**
   <details>
   <summary>Відповідь</summary>
   `k8s.pod.name`, `k8s.ns.name`, `k8s.deployment.name`, `container.name`, `container.id`, `container.image`.
   </details>

---

## Практична вправа

**Завдання**: Створити та протестувати правила Falco для типових загроз.

```bash
# Step 1: Check if Falco is available
which falco && falco --version || echo "Falco not installed"

# Step 2: Create custom rules file
cat <<'EOF' > /tmp/custom-falco-rules.yaml
# Custom security rules

- rule: Shell spawned in container
  desc: Shell process started in container
  condition: >
    spawned_process and
    container and
    proc.name in (bash, sh, ash, zsh, csh, fish)
  output: >
    Shell spawned (container=%container.name shell=%proc.name
    user=%user.name cmdline=%proc.cmdline pod=%k8s.pod.name)
  priority: WARNING
  tags: [shell, container]

- rule: Package manager in container
  desc: Package manager executed in running container
  condition: >
    spawned_process and
    container and
    proc.name in (apt, apt-get, yum, dnf, apk, pip, npm)
  output: >
    Package manager used (container=%container.name
    command=%proc.cmdline user=%user.name)
  priority: NOTICE
  tags: [package, container]

- rule: Write to /etc in container
  desc: Write to /etc directory detected
  condition: >
    container and
    open_write and
    fd.directory = /etc
  output: >
    Write to /etc (container=%container.name file=%fd.name
    process=%proc.name user=%user.name)
  priority: WARNING
  tags: [filesystem, container]

- rule: Outbound SSH connection
  desc: Outbound SSH connection from container
  condition: >
    container and
    outbound and
    fd.dport = 22
  output: >
    Outbound SSH (container=%container.name dest=%fd.sip:%fd.dport
    process=%proc.cmdline)
  priority: WARNING
  tags: [network, ssh]
EOF

echo "=== Custom Rules Created ==="
cat /tmp/custom-falco-rules.yaml

# Step 3: Validate rules syntax
echo "=== Validating Rules ==="
python3 -c "import yaml; yaml.safe_load(open('/tmp/custom-falco-rules.yaml'))" && echo "Valid YAML"

# Step 4: Demonstrate rule analysis
echo "=== Rule Analysis ==="
echo "Rules created:"
grep "^- rule:" /tmp/custom-falco-rules.yaml | sed 's/- rule:/  -/'

echo ""
echo "Priority levels used:"
grep "priority:" /tmp/custom-falco-rules.yaml | sort | uniq

# Cleanup
rm -f /tmp/custom-falco-rules.yaml
```

**Критерії успіху**: Зрозуміти структуру правил Falco та аналіз сповіщень.

---

## Підсумок

**Основи Falco**:
- Моніторинг безпеки виконання
- Інспекція системних викликів на рівні ядра
- Виявлення загроз на основі правил
- Сповіщення в реальному часі

**Компоненти правил**:
- condition (вираз фільтра)
- output (повідомлення сповіщення з полями)
- priority (рівень серйозності)
- tags (категоризація)

**Типові виявлення**:
- Оболонка в контейнері
- Доступ до конфіденційних файлів
- Використання менеджера пакетів
- Неочікувані мережеві з'єднання

**Поради для іспиту**:
- Знайте синтаксис правил
- Розумійте поширені поля
- Вмійте створювати власні правила
- Знайте, як аналізувати сповіщення

---

## Наступний модуль

[Модуль 6.3: Розслідування контейнерів](module-6.3-container-investigation/) — Аналіз підозрілої поведінки контейнерів.
