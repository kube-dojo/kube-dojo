---
title: "Модуль 6.3: Розслідування контейнерів"
slug: uk/k8s/cks/part6-runtime-security/module-6.3-container-investigation
sidebar:
  order: 3
---
> **Складність**: `[MEDIUM]` — навички реагування на інциденти
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Модуль 6.2 (Falco), основи процесів Linux

---

## Чому цей модуль важливий

Коли ви отримуєте сповіщення безпеки, потрібно швидко розслідувати. Які процеси запущені? Які файли були змінені? Які мережеві з'єднання існують? Розслідування контейнерів — це критична навичка реагування на інциденти.

CKS тестує вашу здатність розслідувати підозрілу поведінку контейнерів.

---

## Послідовність розслідування

```
┌─────────────────────────────────────────────────────────────┐
│              ПОСЛІДОВНІСТЬ РОЗСЛІДУВАННЯ КОНТЕЙНЕРІВ         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. ВИЯВИТИ                                                │
│     └── Сповіщення від Falco, журналів аудиту, моніторингу │
│                                                             │
│  2. ІДЕНТИФІКУВАТИ                                         │
│     └── Який Pod/контейнер? Який вузол?                    │
│                                                             │
│  3. РОЗСЛІДУВАТИ                                           │
│     ├── Запущені процеси                                   │
│     ├── Мережеві з'єднання                                 │
│     ├── Зміни файлів                                       │
│     └── Активність користувачів                            │
│                                                             │
│  4. ІЗОЛЮВАТИ                                              │
│     ├── Ізоляція за допомогою NetworkPolicy                │
│     ├── Зупинка контейнера                                 │
│     └── Збереження доказів                                  │
│                                                             │
│  5. ВИПРАВИТИ                                              │
│     ├── Виправити вразливість                              │
│     ├── Оновити образ                                      │
│     └── Розгорнути чисту заміну                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Інструменти розслідування

### Команди kubectl

```bash
# List pods with status
kubectl get pods -o wide

# Get pod details
kubectl describe pod suspicious-pod

# Get pod YAML (check securityContext, volumes)
kubectl get pod suspicious-pod -o yaml

# Check pod logs
kubectl logs suspicious-pod
kubectl logs suspicious-pod --previous  # Previous container

# Check events
kubectl get events --field-selector involvedObject.name=suspicious-pod
```

### Розслідування всередині контейнера

```bash
# Execute into container
kubectl exec -it suspicious-pod -- /bin/bash
# Or without bash
kubectl exec -it suspicious-pod -- /bin/sh

# List running processes
kubectl exec suspicious-pod -- ps aux
kubectl exec suspicious-pod -- ps -ef

# Check network connections
kubectl exec suspicious-pod -- netstat -tulnp
kubectl exec suspicious-pod -- ss -tulnp

# Check open files
kubectl exec suspicious-pod -- ls -la /proc/1/fd/

# Check environment variables (may contain secrets!)
kubectl exec suspicious-pod -- env

# Check mounted filesystems
kubectl exec suspicious-pod -- mount
kubectl exec suspicious-pod -- df -h

# Check recent file modifications
kubectl exec suspicious-pod -- find / -mmin -60 -type f 2>/dev/null
```

---

## Розслідування процесів

### Використання файлової системи /proc

```bash
# Inside container, examine process details
# Process 1 is usually the main container process

# Command line
cat /proc/1/cmdline | tr '\0' ' '

# Current working directory
ls -la /proc/1/cwd

# Executable path
ls -la /proc/1/exe

# Environment variables
cat /proc/1/environ | tr '\0' '\n'

# Open files
ls -la /proc/1/fd/

# Memory maps (loaded libraries)
cat /proc/1/maps

# Network connections
cat /proc/1/net/tcp
cat /proc/1/net/tcp6
```

### Використання crictl (на вузлі)

```bash
# List containers
sudo crictl ps

# Get container ID for pod
CONTAINER_ID=$(sudo crictl ps --name suspicious-pod -q)

# Inspect container
sudo crictl inspect $CONTAINER_ID

# Get container PID
PID=$(sudo crictl inspect $CONTAINER_ID | jq '.info.pid')

# Access container's namespace from host
sudo nsenter -t $PID -p -n ps aux
sudo nsenter -t $PID -p -n netstat -tulnp
```

---

## Мережеве розслідування

### Зсередини контейнера

```bash
# Check listening ports
netstat -tulnp
ss -tulnp

# Check established connections
netstat -an | grep ESTABLISHED
ss -s

# Check routing table
route -n
ip route

# DNS configuration
cat /etc/resolv.conf

# Check iptables rules (if accessible)
iptables -L -n
```

### З хоста

```bash
# Find container network namespace
CONTAINER_ID=$(sudo crictl ps --name suspicious-pod -q)
PID=$(sudo crictl inspect $CONTAINER_ID | jq '.info.pid')

# Enter container's network namespace
sudo nsenter -t $PID -n netstat -tulnp
sudo nsenter -t $PID -n ss -tulnp

# Check for connections to suspicious IPs
sudo nsenter -t $PID -n ss -tnp | grep -E "(22|23|3389)"
```

---

## Розслідування файлової системи

### Перевірка змін

```bash
# Recent file modifications
find / -mmin -30 -type f 2>/dev/null | head -50

# Files modified today
find / -mtime 0 -type f 2>/dev/null

# Check for suspicious files in /tmp
ls -la /tmp/
ls -la /var/tmp/
ls -la /dev/shm/

# Check for hidden files
find / -name ".*" -type f 2>/dev/null

# Check for setuid/setgid binaries
find / -perm -4000 -type f 2>/dev/null
find / -perm -2000 -type f 2>/dev/null

# Check crontabs
cat /etc/crontab
ls -la /etc/cron.d/
crontab -l
```

### Перевірка відомих шаблонів атак

```bash
# Cryptocurrency miners often use these
find / -name "*xmrig*" 2>/dev/null
find / -name "*minerd*" 2>/dev/null

# Web shells
find / -name "*.php" -exec grep -l "eval\|base64_decode\|system\|passthru" {} \; 2>/dev/null

# Suspicious shell history
cat /root/.bash_history
cat /home/*/.bash_history

# Check for reverse shells
netstat -an | grep -E ":(4444|5555|6666|7777|8888|9999)"
```

---

## Ефемерні контейнери налагодження

Коли контейнер не має оболонки або інструментів, використовуйте контейнери налагодження.

```bash
# Add debug container to running pod
kubectl debug -it suspicious-pod --image=busybox --target=main-container

# Or create a copy of the pod with debug container
kubectl debug suspicious-pod --copy-to=debug-pod --container=debugger --image=ubuntu

# Debug node issues
kubectl debug node/worker-1 -it --image=ubuntu
```

---

## Реальні сценарії іспиту

### Сценарій 1: Розслідування підозрілого процесу

```bash
# Alert: Crypto miner detected in pod "app" in namespace "production"

# Step 1: Get pod details
kubectl get pod app -n production -o wide

# Step 2: Check running processes
kubectl exec -n production app -- ps aux

# Step 3: Check network connections
kubectl exec -n production app -- netstat -tulnp

# Step 4: Check recent file modifications
kubectl exec -n production app -- find /tmp -mmin -60

# Step 5: Document findings and delete pod
kubectl delete pod app -n production
```

### Сценарій 2: Розслідування мережевої ексфільтрації

```bash
# Alert: Outbound connection to suspicious IP from pod "data-processor"

# Step 1: Check current connections
kubectl exec data-processor -- ss -tnp

# Step 2: Check for data staging
kubectl exec data-processor -- ls -la /tmp/
kubectl exec data-processor -- ls -la /var/tmp/

# Step 3: Isolate the pod with NetworkPolicy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-data-processor
spec:
  podSelector:
    matchLabels:
      app: data-processor
  policyTypes:
  - Egress
  egress: []  # Block all egress
EOF
```

### Сценарій 3: Підробка файлової системи

```bash
# Alert: Write to /etc detected in container

# Step 1: Check what was modified
kubectl exec suspicious-pod -- find /etc -mmin -30 -type f

# Step 2: Check file contents
kubectl exec suspicious-pod -- cat /etc/passwd

# Step 3: Compare with original image
IMAGE=$(kubectl get pod suspicious-pod -o jsonpath='{.spec.containers[0].image}')
kubectl run compare --image=$IMAGE --rm -it -- cat /etc/passwd

# Step 4: Check for persistence mechanisms
kubectl exec suspicious-pod -- crontab -l
kubectl exec suspicious-pod -- ls -la /etc/cron.d/
```

---

## Збереження доказів

```bash
# Export pod YAML
kubectl get pod suspicious-pod -o yaml > pod-evidence.yaml

# Export logs
kubectl logs suspicious-pod > pod-logs.txt
kubectl logs suspicious-pod --previous > pod-logs-previous.txt

# Export events
kubectl get events --field-selector involvedObject.name=suspicious-pod > events.txt

# If possible, create filesystem snapshot
kubectl exec suspicious-pod -- tar -czf - / > container-filesystem.tar.gz
```

---

## Чи знали ви?

- **Ефемерні контейнери налагодження** (kubectl debug) з'явилися в Kubernetes 1.18 і стали стабільними в 1.25. Вони ідеально підходять для розслідування distroless образів.

- **Контейнери використовують спільне ядро хоста**, але мають окремі представлення /proc. Кожен /proc контейнера показує лише його власні процеси.

- **nsenter** дозволяє увійти до будь-якого простору імен Linux. В поєднанні з PID контейнера можна отримати доступ до мережевих, монтування та PID просторів імен контейнера з хоста.

- **Файлова система тільки для читання не запобігає всім записам**. Зловмисники все ще можуть писати в змонтовані томи, /tmp (якщо tmpfs) та /dev/shm.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Негайне видалення Pod | Докази втрачені | Спочатку розслідуйте |
| Без мережевої ізоляції | Атака продовжується | Спочатку застосуйте NetworkPolicy |
| Відсутні логи | Неможливо відтворити хронологію | Експортуйте перед видаленням |
| Не перевірені всі контейнери | Багатоконтейнерні Pod | Перевірте sidecar також |
| Забуті попередні логи | Перший контейнер впав | Використовуйте прапорець --previous |

---

## Тест

1. **Як перевірити запущені процеси в контейнері без доступу через exec?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте `kubectl debug` для створення ефемерного контейнера налагодження, або використовуйте `crictl inspect` та `nsenter` з вузла для входу до просторів імен контейнера.
   </details>

2. **Яка команда знаходить файли, змінені за останні 30 хвилин?**
   <details>
   <summary>Відповідь</summary>
   `find / -mmin -30 -type f 2>/dev/null`. Прапорець `-mmin` визначає хвилини, а `-mtime` визначає дні.
   </details>

3. **Як ізолювати підозрілий Pod під час розслідування?**
   <details>
   <summary>Відповідь</summary>
   Застосувати NetworkPolicy з порожніми правилами egress для блокування всього вихідного трафіку. Це запобігає ексфільтрації даних під час розслідування.
   </details>

4. **Яка перевага використання ефемерних контейнерів налагодження?**
   <details>
   <summary>Відповідь</summary>
   Вони працюють з distroless образами, що не мають оболонки, використовують спільні простори імен цільового контейнера для повної видимості та не змінюють оригінальний контейнер.
   </details>

---

## Практична вправа

**Завдання**: Практика технік розслідування контейнерів.

```bash
# Step 1: Create a "suspicious" pod for investigation
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: suspicious-app
  labels:
    app: suspicious
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "
      echo 'suspicious data' > /tmp/exfil.txt &&
      while true; do sleep 10; done
    "]
EOF

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/suspicious-app --timeout=60s

# Step 2: Investigate processes
echo "=== Running Processes ==="
kubectl exec suspicious-app -- ps aux

# Step 3: Check network
echo "=== Network Configuration ==="
kubectl exec suspicious-app -- cat /etc/resolv.conf

# Step 4: Check for recent file modifications
echo "=== Recent File Modifications ==="
kubectl exec suspicious-app -- find / -mmin -10 -type f 2>/dev/null

# Step 5: Check /tmp for suspicious files
echo "=== /tmp Contents ==="
kubectl exec suspicious-app -- ls -la /tmp/
kubectl exec suspicious-app -- cat /tmp/exfil.txt

# Step 6: Create isolation NetworkPolicy
echo "=== Creating Isolation Policy ==="
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-suspicious
spec:
  podSelector:
    matchLabels:
      app: suspicious
  policyTypes:
  - Egress
  - Ingress
  egress: []
  ingress: []
EOF

echo "Pod isolated with NetworkPolicy"

# Step 7: Preserve evidence
echo "=== Preserving Evidence ==="
kubectl get pod suspicious-app -o yaml > /tmp/pod-evidence.yaml
kubectl logs suspicious-app > /tmp/pod-logs.txt
echo "Evidence saved to /tmp/"

# Cleanup
kubectl delete pod suspicious-app
kubectl delete networkpolicy isolate-suspicious
rm -f /tmp/pod-evidence.yaml /tmp/pod-logs.txt

echo "=== Investigation Complete ==="
```

**Критерії успіху**: Зрозуміти команди розслідування та послідовність дій.

---

## Підсумок

**Кроки розслідування**:
1. Виявити (сповіщення, логи)
2. Ідентифікувати (Pod, простір імен, вузол)
3. Розслідувати (процеси, мережа, файли)
4. Ізолювати (NetworkPolicy, ізоляція)
5. Виправити (видалити, перерозгорнути)

**Ключові команди**:
- `kubectl exec` для виконання команд
- `kubectl debug` для контейнерів налагодження
- `kubectl logs` для логів додатків
- `crictl` та `nsenter` на вузлах

**Що перевіряти**:
- Запущені процеси (ps aux)
- Мережеві з'єднання (netstat, ss)
- Зміни файлів (find -mmin)
- Змінні середовища (env)

**Поради для іспиту**:
- Знайте синтаксис kubectl exec
- Розумійте файлову систему /proc
- Вмійте ізолювати Pod
- Пам'ятайте про збереження доказів

---

## Наступний модуль

[Модуль 6.4: Незмінна інфраструктура](module-6.4-immutable-infrastructure/) — Побудова контейнерів, які не можна змінити під час виконання.
