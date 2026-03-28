---
title: "Модуль 4.4: Ізоляція середовища виконання"
slug: uk/k8s/cks/part4-microservice-vulnerabilities/module-4.4-runtime-sandboxing
sidebar:
  order: 4
---
> **Складність**: `[MEDIUM]` — Поглиблена ізоляція контейнерів
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Модуль 4.3 (Управління секретами), концепції середовища виконання контейнерів

---

## Чому цей модуль важливий

Стандартні контейнери безпосередньо використовують ядро хоста. Якщо зловмисник експлуатує вразливість ядра зсередини контейнера, він може вийти на хост і скомпрометувати всі навантаження. Ізоляція середовища виконання додає додатковий шар ізоляції між контейнерами та ядром.

CKS перевіряє ваше розуміння технік ізоляції контейнерів.

---

## Проблема ізоляції контейнерів

```
┌─────────────────────────────────────────────────────────────┐
│              СТАНДАРТНА ІЗОЛЯЦІЯ КОНТЕЙНЕРІВ                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Стандартні контейнери (runc):                              │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Контейнер A │  │ Контейнер B │  │ Контейнер C │        │
│  │             │  │             │  │ (зловмисник) │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                 │
│                          ▼                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    ЯДРО ХОСТА                         │ │
│  │                                                       │ │
│  │  Експлойт ядра з будь-якого контейнера               │ │
│  │  = Доступ до ВСІХ контейнерів та хоста               │ │
│  │                                                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  Єдина точка відмови: спільне ядро                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Рішення для ізоляції

```
┌─────────────────────────────────────────────────────────────┐
│              ВАРІАНТИ ІЗОЛЯЦІЇ СЕРЕДОВИЩА ВИКОНАННЯ          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  gVisor (runsc)                                            │
│  ─────────────────────────────────────────────────────────  │
│  • Ядро в просторі користувача, написане на Go            │
│  • Перехоплює системні виклики, реалізує в просторі       │
│    користувача                                             │
│  • Низькі накладні витрати, середня ізоляція              │
│  • Підходить для: ненадійних навантажень, мультитенантності│
│                                                             │
│  Kata Containers                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Легка ВМ для кожного контейнера                        │
│  • Справжнє ядро Linux для кожного контейнера             │
│  • Вищі накладні витрати, максимальна ізоляція            │
│  • Підходить для: суворих вимог до ізоляції               │
│                                                             │
│  Firecracker                                               │
│  ─────────────────────────────────────────────────────────  │
│  • Технологія мікроВМ (використовується AWS Lambda)       │
│  • Мінімальний монітор віртуальних машин                  │
│  • Швидке завантаження, малий розмір                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Архітектура gVisor

```
┌─────────────────────────────────────────────────────────────┐
│              АРХІТЕКТУРА gVisor (runsc)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                    Контейнер                          │ │
│  │                    Додаток                            │ │
│  └───────────────────────┬───────────────────────────────┘ │
│                          │ системні виклики                │
│                          ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │            gVisor Sentry (простір користувача)         │ │
│  │                                                       │ │
│  │  • Реалізує ~300 системних викликів Linux             │ │
│  │  • Працює в просторі користувача, не в ядрі          │ │
│  │  • Написаний на Go (безпечна пам'ять)                │ │
│  │  • Не може бути експлуатований через CVE ядра        │ │
│  │                                                       │ │
│  └───────────────────────┬───────────────────────────────┘ │
│                          │ обмежені системні виклики       │
│                          ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                    Ядро хоста                          │ │
│  │                                                       │ │
│  │  Sentry використовує лише ~50 системних викликів      │ │
│  │  Значно менша поверхня атаки                         │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Архітектура Kata Containers

```
┌─────────────────────────────────────────────────────────────┐
│              АРХІТЕКТУРА KATA CONTAINERS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Контейнер A   │  │   Контейнер B   │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                           │
│           ▼                    ▼                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │    Гостьова ВМ  │  │    Гостьова ВМ  │                  │
│  │  ┌───────────┐  │  │  ┌───────────┐  │                  │
│  │  │ Гостьове  │  │  │  │ Гостьове  │  │                  │
│  │  │  ядро     │  │  │  │  ядро     │  │                  │
│  │  └───────────┘  │  │  └───────────┘  │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                           │
│           └────────┬───────────┘                           │
│                    ▼                                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │        Гіпервізор (QEMU/Cloud Hypervisor)            │ │
│  └──────────────────────────────────────────────────────┘ │
│                    │                                       │
│                    ▼                                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    Ядро хоста                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  Кожен контейнер має власне ядро — повна ізоляція        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## RuntimeClass

Kubernetes використовує RuntimeClass для визначення середовища виконання контейнерів.

### Визначення RuntimeClass

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc  # Name in containerd config
---
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata-qemu  # Name in containerd config
```

### Використання RuntimeClass у Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-pod
spec:
  runtimeClassName: gvisor  # Use gVisor instead of runc
  containers:
  - name: app
    image: nginx
```

---

## Встановлення gVisor

### На вузлі

```bash
# Add gVisor repository (Debian/Ubuntu)
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list

# Install
sudo apt update && sudo apt install -y runsc

# Verify
runsc --version
```

### Налаштування containerd

```toml
# /etc/containerd/config.toml

# Add after [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc.options]
  TypeUrl = "io.containerd.runsc.v1.options"
```

### Перезапуск containerd

```bash
sudo systemctl restart containerd
```

### Створення RuntimeClass

```bash
cat <<EOF | kubectl apply -f -
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF
```

---

## Використання gVisor

### Створення ізольованого Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gvisor-test
spec:
  runtimeClassName: gvisor
  containers:
  - name: test
    image: nginx
```

### Перевірка роботи gVisor

```bash
# Create the pod
kubectl apply -f gvisor-pod.yaml

# Check runtime
kubectl get pod gvisor-test -o jsonpath='{.spec.runtimeClassName}'
# Output: gvisor

# Inside the container, check kernel version
kubectl exec gvisor-test -- uname -a
# Output shows "gVisor" instead of host kernel version

# Check dmesg (gVisor intercepts this)
kubectl exec gvisor-test -- dmesg 2>&1 | head -5
# Output shows gVisor's simulated kernel messages
```

---

## Обмеження gVisor

```
┌─────────────────────────────────────────────────────────────┐
│              ОБМЕЖЕННЯ gVisor                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Не всі системні виклики підтримуються:                   │
│  ├── Деякі розширені системні виклики не реалізовано       │
│  ├── Може зламати деякі додатки                           │
│  └── Перевіряйте сумісність перед використанням            │
│                                                             │
│  Накладні витрати на продуктивність:                       │
│  ├── ~5-15% для обчислювальних навантажень                │
│  ├── Вищі для навантажень з інтенсивним вводом/виводом    │
│  └── Перехоплення системних викликів має вартість          │
│                                                             │
│  Несумісний з:                                             │
│  ├── Мережею хоста (hostNetwork: true)                    │
│  ├── PID простором імен хоста (hostPID: true)             │
│  ├── Привілейованими контейнерами                         │
│  └── Деякими типами томів                                 │
│                                                             │
│  Підходить для:                                            │
│  ├── Вебдодатків                                           │
│  ├── Мікросервісів                                         │
│  ├── Ненадійних навантажень                                │
│  └── Мультитенантних середовищ                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Планування з RuntimeClass

### NodeSelector для RuntimeClass

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
scheduling:
  nodeSelector:
    gvisor.kubernetes.io/enabled: "true"  # Only schedule on these nodes
  tolerations:
  - key: "gvisor"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

### Забезпечення правильних вузлів для навантажень

```bash
# Label nodes that have gVisor installed
kubectl label node worker1 gvisor.kubernetes.io/enabled=true

# Now pods with runtimeClassName: gvisor will only schedule on labeled nodes
```

---

## Реальні сценарії іспиту

### Сценарій 1: Створення та використання RuntimeClass

```bash
# Step 1: Create RuntimeClass
cat <<EOF | kubectl apply -f -
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF

# Step 2: Create pod using RuntimeClass
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: untrusted-workload
spec:
  runtimeClassName: gvisor
  containers:
  - name: app
    image: nginx
EOF

# Step 3: Verify
kubectl get pod untrusted-workload -o yaml | grep runtimeClassName
kubectl exec untrusted-workload -- uname -a  # Shows gVisor
```

### Сценарій 2: Пошук Pod без ізоляції

```bash
# Find all pods without runtimeClassName
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.runtimeClassName == null) |
  "\(.metadata.namespace)/\(.metadata.name)"
'

# Find pods with specific RuntimeClass
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.runtimeClassName == "gvisor") |
  "\(.metadata.namespace)/\(.metadata.name)"
'
```

### Сценарій 3: Застосування RuntimeClass для простору імен

```yaml
# Use a ValidatingAdmissionPolicy (K8s 1.28+) or OPA/Gatekeeper
# Example with namespace annotation for documentation

apiVersion: v1
kind: Namespace
metadata:
  name: untrusted-workloads
  labels:
    security.kubernetes.io/sandbox-required: "true"
```

---

## Порівняння: runc проти gVisor проти Kata

```
┌───────────────────────────────────────────────────────────────────┐
│                    ПОРІВНЯННЯ СЕРЕДОВИЩ ВИКОНАННЯ                  │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│ Характеристика  │ runc (типовий)  │ gVisor          │ Kata        │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ Ізоляція        │ Лише простори   │ Ядро в просторі │ ВМ на Pod   │
│                 │ імен            │ користувача     │             │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ Спільне ядро    │ Спільне         │ Перехоплене     │ Не спільне  │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ Накладні витрати│ Мінімальні      │ Низькі-Середні  │ Середні-Вис.│
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ Час запуску     │ ~100мс          │ ~200мс          │ ~500мс      │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ Пам'ять         │ Низька          │ Низька-Середня  │ Вища        │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ Сумісність      │ Повна           │ Більшість       │ Більшість   │
├─────────────────┼─────────────────┼─────────────────┼─────────────┤
│ Випадок         │ Загальний       │ Ненадійні       │ Висока      │
│ використання    │                 │ навантаження    │ безпека     │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
```

---

## Чи знали ви?

- **gVisor був розроблений Google** і використовується в Google Cloud Run та інших сервісах GCP. Він перехоплює близько 300 системних викликів Linux і реалізує їх у просторі користувача.

- **Kata Containers об'єднав Intel Clear Containers та Hyper runV**. Він використовує той самий інтерфейс OCI, що й runc, тому є заміною без додаткових змін.

- **Назва handler у RuntimeClass** повинна збігатися з назвою середовища виконання, налаштованого в containerd/CRI-O. Типові назви: `runsc` (gVisor), `kata-qemu` або `kata` (Kata).

- **AWS Fargate використовує Firecracker** — іншу технологію мікроВМ, подібну до Kata, але оптимізовану для швидкого часу завантаження.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Неправильна назва handler | Pod не може бути розміщений | Збігається з конфігурацією containerd |
| Немає RuntimeClass | Використовується типовий runc | Спочатку створити RuntimeClass |
| gVisor на несумісному навантаженні | Додаток падає | Спочатку перевірити сумісність |
| Відсутній node selector | Розміщення на неправильному вузлі | Використовуйте scheduling в RuntimeClass |
| Очікування повної підтримки системних викликів | Додаток не працює | Перевірте таблицю системних викликів gVisor |

---

## Тест

1. **Яка основна перевага безпеки gVisor?**
   <details>
   <summary>Відповідь</summary>
   gVisor перехоплює системні виклики в просторі користувача, тому вразливості ядра хоста не можуть бути безпосередньо експлуатовані з контейнера. Це зменшує поверхню атаки з ~300+ системних викликів до ~50.
   </details>

2. **Як Kata Containers досягає ізоляції?**
   <details>
   <summary>Відповідь</summary>
   Kata запускає кожен контейнер (або Pod) у легкій ВМ з власним ядром Linux. Системні виклики контейнера йдуть до гостьового ядра, а не до ядра хоста, забезпечуючи апаратний рівень ізоляції.
   </details>

3. **Який ресурс Kubernetes визначає середовище виконання контейнерів?**
   <details>
   <summary>Відповідь</summary>
   RuntimeClass. Він зіставляє назву (використовується в специфікації Pod) з handler (налаштованим у containerd). Pod посилаються на нього через `spec.runtimeClassName`.
   </details>

4. **Які обмеження gVisor?**
   <details>
   <summary>Відповідь</summary>
   Не всі системні виклики підтримуються, деякі додатки можуть не працювати, вищі накладні витрати на ввід/вивід, несумісність з hostNetwork/hostPID/привілейованими контейнерами.
   </details>

---

## Практична вправа

**Завдання**: Створити та використати RuntimeClass для ізольованих навантажень.

```bash
# Step 1: Check if gVisor is available (on lab environment)
runsc --version 2>/dev/null || echo "gVisor not installed (expected in exam environment)"

# Step 2: Check existing RuntimeClasses
kubectl get runtimeclass

# Step 3: Create RuntimeClass (works even if gVisor not installed)
cat <<EOF | kubectl apply -f -
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF

# Step 4: Create pod without sandboxing
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: standard-pod
spec:
  containers:
  - name: test
    image: busybox
    command: ["sleep", "3600"]
EOF

# Step 5: Create pod with sandboxing
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-pod
spec:
  runtimeClassName: gvisor
  containers:
  - name: test
    image: busybox
    command: ["sleep", "3600"]
EOF

# Step 6: Compare pod specs
echo "=== Standard Pod ==="
kubectl get pod standard-pod -o jsonpath='{.spec.runtimeClassName}'
echo ""

echo "=== Sandboxed Pod ==="
kubectl get pod sandboxed-pod -o jsonpath='{.spec.runtimeClassName}'
echo ""

# Step 7: List all RuntimeClasses
kubectl get runtimeclass -o wide

# Cleanup
kubectl delete pod standard-pod sandboxed-pod
kubectl delete runtimeclass gvisor
```

**Критерії успіху**: Зрозуміти налаштування RuntimeClass та призначення Pod.

---

## Підсумок

**Навіщо ізоляція?**
- Контейнери використовують спільне ядро хоста
- Експлойт ядра = вихід на хост
- Ізоляція додає додатковий шар

**gVisor**:
- Ядро в просторі користувача
- Перехоплює системні виклики
- Низькі накладні витрати
- Підходить для ненадійних навантажень

**Kata Containers**:
- ВМ для кожного контейнера
- Повна ізоляція ядра
- Вищі накладні витрати
- Максимальна безпека

**RuntimeClass**:
- Абстракція Kubernetes для середовищ виконання
- Handler збігається з конфігурацією containerd
- Pod використовує `runtimeClassName`

**Поради для іспиту**:
- Знайте формат YAML RuntimeClass
- Розумійте компроміси gVisor проти Kata
- Вмійте застосувати RuntimeClass до Pod

---

## Частина 4 завершена!

Ви завершили **Мінімізація вразливостей мікросервісів** (20% CKS). Тепер ви розумієте:
- Контексти безпеки для Pod та контейнерів
- Стандарти Pod Security Admission
- Управління секретами та шифрування
- Ізоляцію середовища виконання з gVisor

**Наступна частина**: [Частина 5: Безпека ланцюга постачання](../part5-supply-chain-security/module-5.1-image-security/) — Захист образів контейнерів та ланцюга постачання програмного забезпечення.
