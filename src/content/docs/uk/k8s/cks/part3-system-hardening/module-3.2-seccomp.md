---
title: "Модуль 3.2: Профілі Seccomp"
slug: uk/k8s/cks/part3-system-hardening/module-3.2-seccomp
sidebar:
  order: 2
---
> **Складність**: `[MEDIUM]` - Безпека на рівні системи
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Модуль 3.1 (AppArmor), знання системних викликів Linux

---

## Чому цей модуль важливий

Seccomp (Secure Computing Mode) обмежує, які системні виклики може виконувати процес. Контейнери використовують системні виклики для взаємодії з ядром — файлові операції, мережеві з'єднання, управління процесами. Обмеження системних викликів драматично зменшує поверхню атаки.

CKS перевіряє вашу здатність застосовувати та створювати профілі seccomp.

---

## Що таке Seccomp?

```
┌─────────────────────────────────────────────────────────────┐
│              ОГЛЯД SECCOMP                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Seccomp = Secure Computing Mode                           │
│  ─────────────────────────────────────────────────────────  │
│  • Функція ядра Linux (з версії 2.6.12)                    │
│  • Фільтрує системні виклики на рівні ядра                 │
│  • Дуже низькі накладні витрати                             │
│  • Працює з Docker, containerd, CRI-O                      │
│                                                             │
│  Застосунок ──► syscall ──► Фільтр Seccomp ──► Ядро       │
│                                    │                        │
│                           ┌────────┴────────┐              │
│                           ▼                 ▼              │
│                     ┌─────────┐       ┌─────────┐          │
│                     │ ДОЗВОЛИТИ│      │ЗАБЛОКУВАТИ│         │
│                     │ виконати │      │ або ВБИТИ│          │
│                     └─────────┘       └─────────┘          │
│                                                             │
│  Дії при збігу системного виклику:                         │
│  • SCMP_ACT_ALLOW  - Дозволити системний виклик            │
│  • SCMP_ACT_ERRNO  - Заблокувати, повернути помилку        │
│  • SCMP_ACT_KILL   - Вбити процес                          │
│  • SCMP_ACT_TRAP   - Надіслати сигнал SIGSYS               │
│  • SCMP_ACT_LOG    - Журналювати та дозволити              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Seccomp проти AppArmor

```
┌─────────────────────────────────────────────────────────────┐
│              SECCOMP проти APPARMOR                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Seccomp                    │ AppArmor                     │
│  ──────────────────────────────────────────────────────────│
│  Фільтрує syscall           │ Фільтрує доступ до          │
│                              │ файлів/мережі               │
│  Дуже низький рівень        │ Вищий рівень абстракції      │
│  JSON-профілі               │ Текстові профілі             │
│  Не враховує шляхи файлів   │ Правила на основі шляхів    │
│  Легковісний                │ Складніші правила             │
│  Захист у глибину           │ Захист у глибину              │
│                                                             │
│  Найкраща практика: Використовуйте ОБИДВА разом           │
│  Seccomp: Блокувати небезпечні syscall                     │
│  AppArmor: Контролювати доступ до ресурсів                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Стандартний профіль Seccomp

Kubernetes 1.22+ застосовує профіль `RuntimeDefault` за замовчуванням, коли налаштовано Pod Security Admission.

```bash
# Перевірити, чи застосовано стандартний seccomp
kubectl get pod mypod -o jsonpath='{.spec.securityContext.seccompProfile}'

# Профіль RuntimeDefault зазвичай блокує:
# - keyctl (ключове сховище ядра)
# - ptrace (трасування процесів)
# - personality (зміна домену виконання)
# - unshare (маніпуляції з просторами імен)
# - mount/umount (монтування файлових систем)
# - clock_settime (зміна системного часу)
# Та близько 40+ інших небезпечних syscall
```

---

## Розташування профілів Seccomp

```bash
# Kubernetes шукає профілі в:
/var/lib/kubelet/seccomp/

# Шлях профілю у специфікації Pod є відносним до цього каталогу
# Приклад: profiles/my-profile.json
# Повний шлях: /var/lib/kubelet/seccomp/profiles/my-profile.json

# Створити каталог, якщо він не існує
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
```

---

## Структура профілю

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_AARCH64"
  ],
  "syscalls": [
    {
      "names": [
        "accept",
        "access",
        "arch_prctl",
        "bind",
        "brk"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": [
        "ptrace"
      ],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

### Пояснення полів профілю

```
┌─────────────────────────────────────────────────────────────┐
│              ПОЛЯ ПРОФІЛЮ SECCOMP                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  defaultAction                                             │
│  └── Що робити для syscall, не вказаних явно               │
│      SCMP_ACT_ALLOW = дозволити за замовчуванням           │
│      (білий список інших)                                   │
│      SCMP_ACT_ERRNO = заборонити за замовчуванням          │
│      (чорний список інших)                                  │
│                                                             │
│  architectures                                             │
│  └── Архітектури CPU для застосування (x86_64, arm64 тощо)│
│                                                             │
│  syscalls                                                  │
│  └── Масив правил syscall:                                 │
│      names: ["syscall1", "syscall2"]                      │
│      action: SCMP_ACT_ALLOW | SCMP_ACT_ERRNO | тощо       │
│      errnoRet: номер помилки для повернення (необов'язково)│
│      args: фільтр за аргументами syscall (необов'язково)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Застосування Seccomp у Kubernetes

### Метод 1: Контекст безпеки Pod (рекомендований)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault  # Використовувати стандартний профіль середовища виконання
  containers:
  - name: app
    image: nginx
```

### Метод 2: Локальний профіль

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/custom.json  # Відносно /var/lib/kubelet/seccomp/
  containers:
  - name: app
    image: nginx
```

### Метод 3: Профіль на рівні контейнера

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      seccompProfile:
        type: RuntimeDefault
  - name: sidecar
    image: busybox
    securityContext:
      seccompProfile:
        type: Localhost
        localhostProfile: profiles/sidecar.json
```

---

## Типи профілів Seccomp

```yaml
# RuntimeDefault - Стандартний профіль середовища виконання контейнера
seccompProfile:
  type: RuntimeDefault

# Localhost - Власний профіль з файлової системи вузла
seccompProfile:
  type: Localhost
  localhostProfile: profiles/my-profile.json

# Unconfined - Без фільтрації seccomp (небезпечно!)
seccompProfile:
  type: Unconfined
```

---

## Створення власних профілів

### Профіль, що блокує ptrace

```json
// /var/lib/kubelet/seccomp/profiles/deny-ptrace.json
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

### Профіль, що дозволяє тільки конкретні syscall

```json
// /var/lib/kubelet/seccomp/profiles/minimal.json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close",
        "fstat", "lseek", "mmap", "mprotect",
        "munmap", "brk", "exit_group"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### Профіль, що журналює підозрілі виклики

```json
// /var/lib/kubelet/seccomp/profiles/audit.json
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["ptrace", "process_vm_readv", "process_vm_writev"],
      "action": "SCMP_ACT_LOG"
    },
    {
      "names": ["mount", "umount2", "pivot_root"],
      "action": "SCMP_ACT_ERRNO"
    }
  ]
}
```

---

## Реальні сценарії іспиту

### Сценарій 1: Застосування RuntimeDefault

```yaml
# Створити Pod з seccomp RuntimeDefault
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx
EOF

# Перевірити
kubectl get pod secure-pod -o jsonpath='{.spec.securityContext.seccompProfile}' | jq .
```

### Сценарій 2: Застосування власного профілю

```bash
# Створити профіль на вузлі
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
sudo tee /var/lib/kubelet/seccomp/profiles/block-chmod.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["chmod", "fchmod", "fchmodat"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
EOF

# Застосувати до Pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-chmod-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/block-chmod.json
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
EOF

# Тест — chmod заблоковано
kubectl exec no-chmod-pod -- chmod 777 /tmp
# Повинно завершитися невдачею з "Operation not permitted"
```

### Сценарій 3: Налагодження проблем Seccomp

```bash
# Перевірити, чи застосовано seccomp
kubectl get pod mypod -o yaml | grep -A5 seccompProfile

# Перевірити журнали аудиту вузла на відмови seccomp
sudo dmesg | grep -i seccomp
sudo journalctl | grep -i seccomp

# Поширені повідомлення про помилки
# "seccomp: syscall X denied"
# "operation not permitted"
```

---

## Пошук syscall, що використовуються застосунком

```bash
# Використати strace для пошуку syscall (на тестовій системі, не у продакшені)
strace -c -f <command>

# Приклад виводу:
# % time     seconds  usecs/call     calls    errors syscall
# ------ ----------- ----------- --------- --------- ----------------
#  25.00    0.000010           0        50           read
#  25.00    0.000010           0        30           write
#  12.50    0.000005           0        20           open
# ...

# Або використати sysdig
sysdig -p "%proc.name %syscall.type" container.name=mycontainer
```

---

## Чи знали ви?

- **Стандартний профіль seccomp Docker** блокує близько 44 syscall з 300+. Це гарна базова лінія, але може потребувати налаштування.

- **Seccomp-bpf (Berkeley Packet Filter)** — це сучасна реалізація. Вона дозволяє складну логіку фільтрації, що виходить за межі простого дозволу/заборони.

- **Зламати профіль seccomp** надзвичайно складно. На відміну від AppArmor, який іноді можна обійти через символічні посилання, seccomp працює на рівні системних викликів.

- **Профіль `RuntimeDefault` став стандартним** у Kubernetes 1.22 з Pod Security Admission. До цього контейнери працювали без обмежень.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Неправильний шлях профілю | Pod не запускається | Перевірте /var/lib/kubelet/seccomp/ |
| Відсутній syscall | Застосунок аварійно завершується | Спочатку проведіть аудит з strace |
| Використання Unconfined | Без захисту | Використовуйте мінімум RuntimeDefault |
| Профіль не на всіх вузлах | Збій планування Pod | Використовуйте DaemonSet для розгортання |
| Синтаксична помилка JSON | Профіль не завантажується | Перевірте валідність JSON |

---

## Тест

1. **Який стандартний профіль seccomp у Kubernetes 1.22+?**
   <details>
   <summary>Відповідь</summary>
   `RuntimeDefault` — стандартний профіль середовища виконання контейнера. Він застосовується, коли Pod Security Admission налаштовано відповідним чином.
   </details>

2. **Де слід розміщувати власні профілі seccomp?**
   <details>
   <summary>Відповідь</summary>
   `/var/lib/kubelet/seccomp/` — профілі вказуються відносно цього каталогу у специфікаціях Pod.
   </details>

3. **Що робить `SCMP_ACT_ERRNO`?**
   <details>
   <summary>Відповідь</summary>
   Він блокує системний виклик та повертає помилку процесу, що викликає. Процес не аварійно завершується, але операція зазнає невдачі.
   </details>

4. **Як застосувати профіль seccomp до конкретного контейнера в Pod з кількома контейнерами?**
   <details>
   <summary>Відповідь</summary>
   Встановити `securityContext.seccompProfile` на рівні контейнера замість рівня Pod. Кожен контейнер може мати свій власний профіль.
   </details>

---

## Практична вправа

**Завдання**: Створити та застосувати профіль seccomp, що блокує syscall ptrace.

```bash
# Крок 1: Створити каталог профілів на вузлі
sudo mkdir -p /var/lib/kubelet/seccomp/profiles

# Крок 2: Створити профіль
sudo tee /var/lib/kubelet/seccomp/profiles/no-ptrace.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
EOF

# Крок 3: Переконатися, що файл існує
cat /var/lib/kubelet/seccomp/profiles/no-ptrace.json

# Крок 4: Створити Pod з профілем
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-ptrace-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/no-ptrace.json
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
EOF

# Крок 5: Дочекатися Pod
kubectl wait --for=condition=Ready pod/no-ptrace-pod --timeout=60s

# Крок 6: Переконатися, що seccomp застосовано
kubectl get pod no-ptrace-pod -o jsonpath='{.spec.securityContext.seccompProfile}' | jq .

# Крок 7: Тест — ptrace має бути заблоковано
# (strace використовує ptrace внутрішньо)
kubectl exec no-ptrace-pod -- strace -f echo test 2>&1 || echo "strace blocked (expected)"

# Крок 8: Створити Pod для порівняння без обмеження seccomp
kubectl run allowed-pod --image=busybox --rm -it --restart=Never -- \
  sh -c "ls /proc/self/status && echo 'No seccomp issues'"

# Очищення
kubectl delete pod no-ptrace-pod
```

**Критерії успіху**: Pod працює, але операції ptrace заблоковані.

---

## Підсумок

**Основи Seccomp**:
- Фільтр syscall ядра Linux
- Профілі на основі JSON
- Низькі витрати, високий рівень безпеки

**Типи профілів**:
- `RuntimeDefault` — стандартний профіль середовища виконання
- `Localhost` — власний профіль
- `Unconfined` — без фільтрації (уникайте!)

**Розташування профілів**:
- `/var/lib/kubelet/seccomp/`
- Шлях у специфікації Pod є відносним

**Дії**:
- `SCMP_ACT_ALLOW` — дозволити syscall
- `SCMP_ACT_ERRNO` — заблокувати з помилкою
- `SCMP_ACT_KILL` — вбити процес

**Поради для іспиту**:
- Знайте синтаксис профілю
- Практикуйте створення профілів
- Розумійте RuntimeDefault

---

## Наступний модуль

[Модуль 3.3: Зміцнення ядра Linux](module-3.3-kernel-hardening/) — Зменшення поверхні атаки ОС.
