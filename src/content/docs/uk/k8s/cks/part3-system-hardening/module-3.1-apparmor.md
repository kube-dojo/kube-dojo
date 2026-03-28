---
title: "Модуль 3.1: AppArmor для контейнерів"
slug: uk/k8s/cks/part3-system-hardening/module-3.1-apparmor
sidebar:
  order: 1
---
> **Складність**: `[MEDIUM]` - Основа безпеки Linux
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Основи Linux, знання середовища виконання контейнерів

---

## Чому цей модуль важливий

AppArmor — це модуль безпеки Linux, який обмежує можливості застосунків: до яких файлів вони можуть звертатися, які мережеві операції можуть виконувати, які можливості (capabilities) можуть використовувати. При застосуванні до контейнерів AppArmor додає рівень безпеки поверх середовища виконання контейнерів.

CKS перевіряє вашу здатність створювати профілі AppArmor та застосовувати їх до Pod.

---

## Що таке AppArmor?

```
┌─────────────────────────────────────────────────────────────┐
│              ОГЛЯД APPARMOR                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AppArmor = Application Armor                              │
│  ─────────────────────────────────────────────────────────  │
│  • Система обов'язкового контролю доступу (MAC)            │
│  • Обмежує можливості кожної програми                      │
│  • За замовчуванням на Ubuntu, Debian                      │
│  • Альтернатива SELinux (RHEL/CentOS)                     │
│                                                             │
│  Як це працює:                                             │
│                                                             │
│  ┌─────────────────┐     ┌─────────────────┐              │
│  │  Застосунок     │────►│  Системний      │              │
│  │  (Контейнер)    │     │  виклик         │              │
│  └─────────────────┘     └────────┬────────┘              │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐              │
│                          │  Перевірка      │              │
│                          │  профілю        │              │
│                          │  AppArmor       │              │
│                          └────────┬────────┘              │
│                                   │                        │
│                      ┌────────────┴────────────┐          │
│                      ▼                         ▼          │
│                 ┌─────────┐              ┌─────────┐      │
│                 │ДОЗВОЛЕНО│              │ЗАБОРОНЕНО│      │
│                 └─────────┘              └─────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Режими AppArmor

```
┌─────────────────────────────────────────────────────────────┐
│              РЕЖИМИ ПРОФІЛЮ APPARMOR                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Режим примусу (Enforce)                                   │
│  └── Політика застосовується, порушення блокуються ТА      │
│      журналюються                                          │
│      aa-enforce /path/to/profile                           │
│                                                             │
│  Режим скарги (Complain)                                   │
│  └── Порушення політики журналюються, але НЕ блокуються    │
│      aa-complain /path/to/profile                          │
│      (Корисно для тестування нових профілів)               │
│                                                             │
│  Вимкнено/Без обмежень (Disabled/Unconfined)               │
│  └── Жодних обмежень не застосовується                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Перевірка статусу AppArmor

```bash
# Перевірити, чи увімкнено AppArmor
cat /sys/module/apparmor/parameters/enabled
# Вивід: Y (увімкнено) або N (вимкнено)

# Перевірити статус AppArmor
sudo aa-status

# Приклад виводу:
# apparmor module is loaded.
# 47 profiles are loaded.
# 47 profiles are in enforce mode.
#    /usr/bin/evince
#    /usr/sbin/cupsd
#    docker-default
# 0 profiles are in complain mode.
# 10 processes have profiles defined.

# Список завантажених профілів
sudo aa-status --profiles

# Перевірити, чи підтримує середовище виконання контейнерів AppArmor
docker info | grep -i apparmor
# Вивід: Security Options: apparmor
```

---

## Стандартний профіль контейнера

```bash
# Docker/containerd використовують профіль 'docker-default'
# Цей профіль:
# - Забороняє монтування файлових систем
# - Забороняє доступ до /proc/sys
# - Забороняє прямий доступ до мережі
# - Дозволяє звичайні операції контейнера

# Перевірити стандартний профіль
cat /etc/apparmor.d/containers/docker-default 2>/dev/null || \
  cat /etc/apparmor.d/docker 2>/dev/null
```

---

## Створення власних профілів AppArmor

### Розташування профілів

```bash
# Профілі AppArmor зберігаються в:
/etc/apparmor.d/

# Для Kubernetes, створюйте в:
/etc/apparmor.d/
# Профіль повинен бути завантажений на кожному вузлі, де може запуститися Pod
```

### Структура профілю

```
#include <tunables/global>

profile my-container-profile flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Правила доступу до файлів
  /etc/passwd r,                    # Читання /etc/passwd
  /var/log/myapp/** rw,            # Читання/запис у каталог журналів
  /tmp/** rw,                       # Читання/запис у tmp

  # Мережеві правила
  network inet tcp,                 # Дозволити TCP
  network inet udp,                 # Дозволити UDP

  # Правила можливостей (capabilities)
  capability net_bind_service,      # Дозволити прив'язку до портів < 1024

  # Правила заборони
  deny /etc/shadow r,               # Заборонити читання shadow
  deny /proc/sys/** w,              # Заборонити запис у /proc/sys
}
```

### Синтаксис правил

```
┌─────────────────────────────────────────────────────────────┐
│              СИНТАКСИС ПРАВИЛ APPARMOR                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Доступ до файлів:                                         │
│  ─────────────────────────────────────────────────────────  │
│  /path/to/file r,        # Читання                         │
│  /path/to/file w,        # Запис                           │
│  /path/to/file rw,       # Читання і запис                 │
│  /path/to/file a,        # Додавання (append)              │
│  /path/to/file ix,       # Виконання, успадкування профілю │
│  /path/to/dir/ r,        # Читання каталогу                │
│  /path/to/dir/** rw,     # Рекурсивне читання/запис        │
│                                                             │
│  Мережа:                                                   │
│  ─────────────────────────────────────────────────────────  │
│  network,                # Дозволити всю мережу            │
│  network inet,           # IPv4                            │
│  network inet6,          # IPv6                            │
│  network inet tcp,       # Тільки IPv4 TCP                 │
│  network inet udp,       # Тільки IPv4 UDP                 │
│                                                             │
│  Можливості (Capabilities):                                │
│  ─────────────────────────────────────────────────────────  │
│  capability dac_override,    # Обхід дозволів файлів       │
│  capability net_admin,       # Адміністрування мережі      │
│  capability sys_ptrace,      # Трасування процесів         │
│                                                             │
│  Заборона:                                                 │
│  ─────────────────────────────────────────────────────────  │
│  deny /path/file w,      # Явна заборона (журналюється)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Створення профілю для Kubernetes

### Крок 1: Написати профіль

```bash
# Створити профіль на кожному вузлі
sudo tee /etc/apparmor.d/k8s-deny-write << 'EOF'
#include <tunables/global>

profile k8s-deny-write flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Дозволити більшість операцій читання
  file,

  # Заборонити всі операції запису, крім /tmp
  deny /** w,
  /tmp/** rw,

  # Дозволити мережу
  network,
}
EOF
```

### Крок 2: Завантажити профіль

```bash
# Розібрати та завантажити профіль
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-write

# Переконатися, що він завантажений
sudo aa-status | grep k8s-deny-write

# Щоб видалити профіль
sudo apparmor_parser -R /etc/apparmor.d/k8s-deny-write
```

### Крок 3: Застосувати до Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secured-pod
  annotations:
    # Формат: container.apparmor.security.beta.kubernetes.io/<ім'я-контейнера>: <профіль>
    container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-write
spec:
  containers:
  - name: app
    image: nginx
```

---

## Значення посилань на профілі AppArmor

```yaml
# Формат анотації:
container.apparmor.security.beta.kubernetes.io/<ім'я-контейнера>: <посилання-на-профіль>

# Варіанти посилань на профіль:
# runtime/default    - Використовувати стандартний профіль середовища виконання
# localhost/<ім'я>   - Використовувати профіль, завантажений на вузлі з <ім'я>
# unconfined        - Без обмежень AppArmor (небезпечно!)
```

---

## Поширені профілі для контейнерів

### Заборона запису в кореневу файлову систему

```
#include <tunables/global>

profile k8s-readonly flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Читати все
  /** r,

  # Записувати тільки у конкретні шляхи
  /tmp/** rw,
  /var/tmp/** rw,
  /run/** rw,

  # Заборонити запис в інші місця
  deny /** w,

  network,
}
```

### Заборона мережевого доступу

```
#include <tunables/global>

profile k8s-deny-network flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  file,

  # Заборонити весь мережевий доступ
  deny network,
}
```

### Заборона доступу до чутливих файлів

```
#include <tunables/global>

profile k8s-deny-sensitive flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  file,
  network,

  # Заборонити доступ до чутливих файлів
  deny /etc/shadow r,
  deny /etc/gshadow r,
  deny /etc/sudoers r,
  deny /etc/sudoers.d/** r,
  deny /root/** rwx,
}
```

---

## Реальні сценарії іспиту

### Сценарій 1: Застосування наявного профілю

```bash
# Перевірити, чи завантажено профіль
sudo aa-status | grep my-profile

# Застосувати до Pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/my-profile
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

### Сценарій 2: Створення та застосування профілю

```bash
# Створити профіль, що забороняє запис у /etc
sudo tee /etc/apparmor.d/k8s-deny-etc-write << 'EOF'
#include <tunables/global>

profile k8s-deny-etc-write flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  file,
  network,
  deny /etc/** w,
}
EOF

# Завантажити профіль
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-etc-write

# Застосувати до Pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secured-nginx
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/k8s-deny-etc-write
spec:
  containers:
  - name: nginx
    image: nginx
EOF

# Перевірити
kubectl exec secured-nginx -- touch /etc/test
# Повинно завершитися невдачею через AppArmor
```

### Сценарій 3: Налагодження проблем AppArmor

```bash
# Перевірити події Pod
kubectl describe pod secured-pod | grep -i apparmor

# Перевірити, чи завантажено профіль на вузлі
ssh node1 'sudo aa-status | grep k8s'

# Перевірити журнали аудиту на відмови
sudo dmesg | grep -i apparmor | tail -10

# Або перевірити журнал аудиту
sudo journalctl -k | grep -i apparmor
```

---

## Чи знали ви?

- **Профілі AppArmor повинні бути завантажені на кожному вузлі**, де може запуститися Pod. DaemonSet допомагають розповсюджувати профілі.

- **Частина 'flags=(attach_disconnected,mediate_deleted)'** є необхідною для профілів контейнерів, оскільки контейнери можуть мати від'єднані шляхи та видалені файли.

- **AppArmor є стандартним для Ubuntu/Debian**, тоді як SELinux є стандартним для RHEL/CentOS. Іспит CKS використовує Ubuntu, тому фокус на AppArmor.

- **Ви можете генерувати профілі** за допомогою `aa-genprof` або `aa-logprof`, які моніторять поведінку застосунку та створюють профілі на основі спостережуваних дій.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Профіль не завантажено на вузлі | Pod не може запуститися | Завантажте на всі вузли |
| Неправильний формат анотації | Профіль не застосовується | Перевірте точний ключ анотації |
| Відсутні абстракції | Профіль занадто обмежувальний | Включіть базові абстракції |
| Використання 'unconfined' | Без захисту | Використовуйте мінімум runtime/default |
| Тестування без режиму скарги | Ламає застосунок | Спочатку тестуйте з aa-complain |

---

## Тест

1. **Яка анотація застосовує профіль AppArmor до контейнера?**
   <details>
   <summary>Відповідь</summary>
   `container.apparmor.security.beta.kubernetes.io/<ім'я-контейнера>: localhost/<ім'я-профілю>` — ім'я контейнера повинно збігатися з контейнером у специфікації Pod.
   </details>

2. **Як завантажити профіль AppArmor на вузлі?**
   <details>
   <summary>Відповідь</summary>
   `sudo apparmor_parser -r /etc/apparmor.d/<файл-профілю>` — прапорець -r перезавантажує, якщо вже завантажено.
   </details>

3. **Для чого використовується режим скарги (complain)?**
   <details>
   <summary>Відповідь</summary>
   Для тестування профілів без блокування. У режимі скарги AppArmor журналює порушення, але дозволяє їх, що дає змогу вдосконалити профіль перед примусовим застосуванням.
   </details>

4. **Що відбувається, якщо вказаний профіль AppArmor не існує на вузлі?**
   <details>
   <summary>Відповідь</summary>
   Pod не запуститься з помилкою, що вказує на неможливість знайти профіль. Kubelet перевіряє наявність профілю перед запуском контейнера.
   </details>

---

## Практична вправа

**Завдання**: Створити та застосувати профіль AppArmor, що забороняє мережевий доступ.

```bash
# Крок 1: Перевірити, що AppArmor увімкнено (виконати на вузлі)
cat /sys/module/apparmor/parameters/enabled
# Повинно вивести: Y

# Крок 2: Створити профіль
sudo tee /etc/apparmor.d/k8s-deny-network << 'EOF'
#include <tunables/global>

profile k8s-deny-network flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Дозволити файлові операції
  file,

  # Заборонити мережевий доступ
  deny network,
}
EOF

# Крок 3: Завантажити профіль
sudo apparmor_parser -r /etc/apparmor.d/k8s-deny-network

# Крок 4: Переконатися, що він завантажений
sudo aa-status | grep k8s-deny-network

# Крок 5: Створити Pod з профілем
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-network-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-network
spec:
  containers:
  - name: app
    image: curlimages/curl
    command: ["sleep", "3600"]
EOF

# Крок 6: Дочекатися Pod
kubectl wait --for=condition=Ready pod/no-network-pod --timeout=60s

# Крок 7: Тестувати, що мережа заблокована
kubectl exec no-network-pod -- curl -s https://kubernetes.io --connect-timeout 5
# Повинно завершитися невдачею через заборону мережі AppArmor

# Крок 8: Створити Pod без обмеження для порівняння
kubectl run network-allowed --image=curlimages/curl --rm -it --restart=Never -- \
  curl -s https://kubernetes.io -o /dev/null -w "%{http_code}"
# Повинно працювати (200)

# Очищення
kubectl delete pod no-network-pod
```

**Критерії успіху**: Pod з профілем AppArmor не може встановлювати мережеві з'єднання.

---

## Підсумок

**Основи AppArmor**:
- Обов'язковий контроль доступу Linux
- Обмеження на рівні програми
- Профілі завантажуються на вузлах

**Застосування профілю**:
```yaml
annotations:
  container.apparmor.security.beta.kubernetes.io/<контейнер>: localhost/<профіль>
```

**Поширені правила профілю**:
- `deny /path w,` — заборона запису
- `deny network,` — заборона мережі
- `capability X,` — дозвіл можливості

**Поради для іспиту**:
- Знайте формат анотації
- Практикуйте завантаження профілів
- Розумійте розташування профілів

---

## Наступний модуль

[Модуль 3.2: Профілі Seccomp](module-3.2-seccomp/) — Фільтрація системних викликів для контейнерів.
