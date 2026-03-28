---
title: "Модуль 3.3: Зміцнення ядра Linux та ОС"
slug: uk/k8s/cks/part3-system-hardening/module-3.3-kernel-hardening
sidebar:
  order: 3
---
> **Складність**: `[MEDIUM]` - Системне адміністрування з фокусом на безпеку
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Базове адміністрування Linux, знання середовища виконання контейнерів

---

## Чому цей модуль важливий

Контейнери використовують спільне ядро хоста. Вразливість у ядрі може скомпрометувати всі контейнери на цьому хості. Зміцнення ОС хоста та налаштувань ядра зменшує поверхню атаки, яку контейнери можуть використати.

CKS перевіряє ваше розуміння заходів безпеки на рівні ОС.

---

## Проблема спільного ядра

```
┌─────────────────────────────────────────────────────────────┐
│              СПІЛЬНЕ ЯДРО КОНТЕЙНЕРІВ                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Контейнер A │  │ Контейнер B │  │ Контейнер C │        │
│  │  (nginx)    │  │  (redis)    │  │ (зловмисник?)│        │
│  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘        │
│        │                │                │                 │
│        └────────────────┼────────────────┘                 │
│                         │                                  │
│                         ▼                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    ЯДРО ХОСТА                         │ │
│  │                                                       │ │
│  │  Всі контейнери використовують ОДНЕ ядро             │ │
│  │  Експлойт ядра = компрометація ВСІХ контейнерів      │ │
│  │  Ескалація привілеїв = доступ до хоста                │ │
│  │                                                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                         │                                  │
│                         ▼                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    ОБЛАДНАННЯ                         │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Контрольний список зміцнення ОС хоста

### 1. Мінімізація встановлених пакетів

```bash
# Список встановлених пакетів
dpkg -l | wc -l  # Debian/Ubuntu
rpm -qa | wc -l  # RHEL/CentOS

# Видалення непотрібних пакетів
sudo apt remove --purge $(dpkg -l | grep -E 'games|office' | awk '{print $2}')

# Вузли Kubernetes повинні мати мінімум програм:
# - Середовище виконання контейнерів (containerd, CRI-O)
# - kubelet
# - kube-proxy (якщо не працює як Pod)
# - Мережеві утиліти
# - Агенти моніторингу
```

### 2. Вимкнення непотрібних сервісів

```bash
# Список працюючих сервісів
systemctl list-units --type=service --state=running

# Вимкнути непотрібні сервіси
sudo systemctl disable --now cups      # Друк
sudo systemctl disable --now avahi-daemon  # mDNS
sudo systemctl disable --now bluetooth  # Bluetooth

# Необхідні сервіси для збереження:
# - containerd або docker
# - kubelet
# - SSH (для управління)
# - NTP/chrony (синхронізація часу)
```

### 3. Підтримка системи в актуальному стані

```bash
# Перевірка оновлень безпеки (Ubuntu)
sudo apt update
sudo apt list --upgradable | grep -i security

# Застосування тільки оновлень безпеки
sudo unattended-upgrades

# Перевірка версії ядра
uname -r

# Перевірка відомих CVE ядра
# https://www.kernel.org/
```

---

## Параметри безпеки ядра

### Необхідні налаштування sysctl

```bash
# Переглянути поточні налаштування
sysctl -a | grep -E "net.ipv4|kernel" | head -20

# Рекомендовані налаштування безпеки
# Додати до /etc/sysctl.d/99-kubernetes-security.conf

# Вимкнути IP-форвардинг, якщо не потрібно (kubelet його потребує!)
# net.ipv4.ip_forward = 0  # Не вимикайте на вузлах K8s!

# Ігнорувати ICMP-перенаправлення
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Увімкнути захист від SYN-флуду
net.ipv4.tcp_syncookies = 1

# Журналювати підозрілі пакети
net.ipv4.conf.all.log_martians = 1

# Ігнорувати broadcast ping
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Вимкнути маршрутизацію від джерела
net.ipv4.conf.all.accept_source_route = 0

# Увімкнути ASLR
kernel.randomize_va_space = 2

# Обмежити доступ до dmesg
kernel.dmesg_restrict = 1

# Обмежити вказівники ядра
kernel.kptr_restrict = 1

# Застосувати налаштування
sudo sysctl -p /etc/sysctl.d/99-kubernetes-security.conf
```

### Специфічні налаштування Kubernetes

```bash
# /etc/sysctl.d/99-kubernetes.conf

# Необхідно для мережі Kubernetes
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# Для мережі Pod
net.ipv4.conf.all.forwarding = 1

# Відстеження з'єднань для сервісів
net.netfilter.nf_conntrack_max = 131072
```

---

## Захист /proc та /sys

```bash
# Обмеження доступу до інформації про процеси
# У /etc/fstab або параметрах монтування:
proc    /proc    proc    defaults,hidepid=2    0    0

# Параметри hidepid:
# 0 = за замовчуванням (всі користувачі бачать всі процеси)
# 1 = користувачі бачать тільки свої процеси
# 2 = користувачі не можуть бачити процеси інших користувачів

# Для контейнерів Kubernetes керує цими монтуваннями
# Але хост повинен обмежити доступ
```

---

## Зміцнення користувачів та дозволів

### Вимкнення SSH-входу під root

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
AllowUsers admin

# Перезапустити SSH
sudo systemctl restart sshd
```

### Видалення непотрібних користувачів

```bash
# Список користувачів, що можуть увійти
grep -v '/nologin\|/false' /etc/passwd

# Заблокувати непотрібні облікові записи
sudo usermod -L olduser

# Видалити користувача
sudo userdel -r unnecessaryuser
```

### Дозволи на файли

```bash
# Захист файлів kubelet
sudo chmod 600 /var/lib/kubelet/config.yaml
sudo chmod 600 /etc/kubernetes/kubelet.conf
sudo chown root:root /var/lib/kubelet/config.yaml

# Захист сертифікатів
sudo chmod 600 /etc/kubernetes/pki/*.key
sudo chmod 644 /etc/kubernetes/pki/*.crt
```

---

## Зміцнення файлової системи

### Параметри монтування

```bash
# Записи /etc/fstab з параметрами безпеки

# Окремі розділи для:
# /var/lib/containerd  - Дані контейнерів
# /var/log             - Журнали
# /tmp                 - Тимчасові файли

# Приклад безпечних параметрів монтування:
/dev/sda3  /var/lib/containerd  ext4  defaults,nodev,nosuid  0  2
/dev/sda4  /tmp                 ext4  defaults,nodev,nosuid,noexec  0  2
/dev/sda5  /var/log             ext4  defaults,nodev,nosuid,noexec  0  2

# Параметри:
# nodev   - Без файлів пристроїв
# nosuid  - Без setuid-виконуваних файлів
# noexec  - Без виконання
```

### Кореневий файлова система тільки для читання

```bash
# Для незмінної інфраструктури:
# Монтувати кореневу систему тільки для читання, використовувати overlay для записів

# Це часто обробляється дистрибутивом ОС
# (CoreOS, Flatcar, Talos тощо)
```

---

## Зміцнення середовища виконання контейнерів

### Безпека Containerd

```toml
# /etc/containerd/config.toml

[plugins."io.containerd.grpc.v1.cri"]
  # Вимкнути привілейовані контейнери (якщо можливо)
  # Примітка: Деякі системні Pod потребують привілеїв

  [plugins."io.containerd.grpc.v1.cri".containerd]
    # Використовувати native (не kata) для продуктивності
    default_runtime_name = "runc"

    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        # Увімкнути seccomp
        SystemdCgroup = true
```

### Безпека Docker (якщо використовується)

```bash
# /etc/docker/daemon.json
{
  "userns-remap": "default",
  "no-new-privileges": true,
  "seccomp-profile": "/etc/docker/seccomp.json",
  "icc": false,
  "live-restore": true
}
```

---

## Налаштування системи аудиту

### Увімкнення auditd

```bash
# Встановити auditd
sudo apt install auditd

# Налаштувати правила аудиту для безпеки контейнерів
# /etc/audit/rules.d/docker.rules

# Моніторинг демона Docker
-w /usr/bin/dockerd -k docker
-w /usr/bin/containerd -k containerd

# Моніторинг конфігурації Docker
-w /etc/docker -k docker-config

# Моніторинг каталогів контейнерів
-w /var/lib/docker -k docker-storage
-w /var/lib/containerd -k containerd-storage

# Моніторинг файлів Kubernetes
-w /etc/kubernetes -k kubernetes
-w /var/lib/kubelet -k kubelet

# Застосувати правила
sudo augenrules --load
```

---

## Реальні сценарії іспиту

### Сценарій 1: Перевірка налаштувань безпеки хоста

```bash
# Перевірити налаштування sysctl
sysctl net.ipv4.ip_forward
sysctl kernel.randomize_va_space

# Перевірити наявність непотрібних сервісів
systemctl list-units --type=service --state=running | wc -l

# Перевірити конфігурацію SSH
grep -E "PermitRootLogin|PasswordAuthentication" /etc/ssh/sshd_config
```

### Сценарій 2: Застосування зміцнення ядра

```bash
# Створити конфігурацію зміцнення
sudo tee /etc/sysctl.d/99-cks-hardening.conf << 'EOF'
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
EOF

# Застосувати
sudo sysctl -p /etc/sysctl.d/99-cks-hardening.conf

# Перевірити
sysctl kernel.dmesg_restrict
```

### Сценарій 3: Захист файлів kubelet

```bash
# Виправити дозволи конфігурації kubelet
sudo chmod 600 /var/lib/kubelet/config.yaml
sudo chown root:root /var/lib/kubelet/config.yaml

# Перевірити
ls -la /var/lib/kubelet/config.yaml
```

---

## Зведена таблиця зміцнення

| Область | Рекомендація | Команда/Конфігурація |
|---------|-------------|---------------------|
| Пакети | Мінімальне встановлення | Видалити невикористані пакети |
| Сервіси | Вимкнути невикористані | `systemctl disable <service>` |
| Оновлення | Регулярне оновлення | `apt update && apt upgrade` |
| SSH | Без root, тільки ключі | `/etc/ssh/sshd_config` |
| sysctl | Обмежувальні налаштування | `/etc/sysctl.d/*.conf` |
| Файли | Правильні дозволи | `chmod 600` для чутливих файлів |
| Аудит | Увімкнити auditd | `/etc/audit/rules.d/` |

---

## Чи знали ви?

- **Оптимізовані для контейнерів ОС**, такі як Flatcar, Talos та Bottlerocket, спеціально створені для запуску контейнерів з мінімальною поверхнею атаки.

- **ASLR (Address Space Layout Randomization)** значно ускладнює атаки переповнення буфера. Він увімкнений за замовчуванням у сучасних системах Linux.

- **Простори імен користувачів** можуть забезпечити додаткову ізоляцію, зіставляючи root контейнера з непривілейованим користувачем хоста. Увімкніть за допомогою `userns-remap` у Docker.

- **Динамічне оновлення ядра** (Ubuntu Livepatch, RHEL kpatch) дозволяє застосовувати патчі безпеки без перезавантаження.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Нерегулярне оновлення | Відомі CVE залишаються | Автоматичні оновлення |
| Стандартна конфігурація SSH | Вхід root, паролі | Зміцнення sshd_config |
| Занадто багато сервісів | Збільшена поверхня атаки | Мінімізація сервісів |
| Неправильні дозволи на файли | Несанкціонований доступ | Аудит дозволів |
| Без журналювання аудиту | Неможливо розслідувати інциденти | Увімкнення auditd |

---

## Тест

1. **Чому важливо, що контейнери використовують спільне ядро хоста?**
   <details>
   <summary>Відповідь</summary>
   Вразливість ядра може бути використана будь-яким контейнером для компрометації хоста та всіх інших контейнерів. Ядро є спільною межею безпеки.
   </details>

2. **Який параметр sysctl вмикає рандомізацію розташування адресного простору (ASLR)?**
   <details>
   <summary>Відповідь</summary>
   `kernel.randomize_va_space = 2` — значення 2 вмикає повну рандомізацію для стеку, VDSO, спільної пам'яті та сегментів даних.
   </details>

3. **Чому на хостах вузлів Kubernetes повинно бути мінімум пакетів?**
   <details>
   <summary>Відповідь</summary>
   Кожен встановлений пакет — це потенційна поверхня атаки. Менше пакетів означає менше вразливостей для оновлення та менше інструментів, доступних зловмисникам, які скомпрометували систему.
   </details>

4. **Який файл містить налаштування безпеки SSH-сервера?**
   <details>
   <summary>Відповідь</summary>
   `/etc/ssh/sshd_config` — налаштуйте `PermitRootLogin no` та `PasswordAuthentication no` для кращої безпеки.
   </details>

---

## Практична вправа

**Завдання**: Демонстрація концепцій зміцнення ядра за допомогою контекстів безпеки Kubernetes.

```bash
# Оскільки ми не можемо змінювати ядро хоста з Kubernetes, ми продемонструємо,
# як концепції зміцнення ядра перетворюються на безпеку контейнерів.

# Крок 1: Створити простір імен для тестування
kubectl create namespace kernel-test

# Крок 2: Розгорнути Pod БЕЗ зміцнення безпеки (небезпечна базова лінія)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
  namespace: kernel-test
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    # Без контексту безпеки = небезпечно!
EOF

# Крок 3: Розгорнути Pod ЗІ зміцненням безпеки (безпечний)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: kernel-test
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
EOF

# Дочекатися готовності Pod
kubectl wait --for=condition=Ready pod/insecure-pod -n kernel-test --timeout=60s
kubectl wait --for=condition=Ready pod/secure-pod -n kernel-test --timeout=60s

# Крок 4: Порівняти, що може кожен Pod
echo "=== Небезпечний Pod: Хто я? ==="
kubectl exec -n kernel-test insecure-pod -- id

echo "=== Безпечний Pod: Хто я? ==="
kubectl exec -n kernel-test secure-pod -- id

# Крок 5: Тест доступу до файлової системи
echo "=== Небезпечний Pod: Може записати у /tmp? ==="
kubectl exec -n kernel-test insecure-pod -- sh -c "echo 'test' > /tmp/test.txt && echo 'Write succeeded' || echo 'Write failed'"

echo "=== Безпечний Pod: Може записати у /tmp? (повинно завершитися невдачею - readOnlyRootFilesystem) ==="
kubectl exec -n kernel-test secure-pod -- sh -c "echo 'test' > /tmp/test.txt && echo 'Write succeeded' || echo 'Write blocked!'"

# Крок 6: Тест видимості процесів (демонструє концепцію hidepid)
echo "=== Небезпечний Pod: Список процесів ==="
kubectl exec -n kernel-test insecure-pod -- ps aux | head -5

echo "=== Безпечний Pod: Список процесів (обмежений вигляд) ==="
kubectl exec -n kernel-test secure-pod -- ps aux | head -5

# Крок 7: Перевірка доступу до proc
echo "=== Перевірка доступу до /proc у безпечному Pod ==="
kubectl exec -n kernel-test secure-pod -- cat /proc/1/cmdline 2>&1 | tr '\0' ' ' && echo ""

# Крок 8: Перевірка застосованого контексту безпеки
echo "=== Порівняння контекстів безпеки ==="
echo "Контекст безпеки небезпечного Pod:"
kubectl get pod insecure-pod -n kernel-test -o jsonpath='{.spec.securityContext}' && echo ""
echo "Контекст безпеки безпечного Pod:"
kubectl get pod secure-pod -n kernel-test -o jsonpath='{.spec.securityContext}' && echo ""

# Крок 9: Тест запобігання ескалації привілеїв (критичне зміцнення ядра)
echo "=== Тест запобігання ескалації привілеїв ==="
# Безпечний Pod повинен це заблокувати
kubectl exec -n kernel-test secure-pod -- sh -c "cat /etc/shadow 2>&1" || echo "Access denied (expected)"

# Крок 10: Перевірка sysctl хоста (якщо працює на реальному вузлі)
echo ""
echo "=== Перевірки ядра хоста (виконати на реальному вузлі) ==="
echo "Щоб перевірити на реальних вузлах кластера:"
echo "  sysctl kernel.randomize_va_space    # Повинно бути 2"
echo "  sysctl kernel.dmesg_restrict        # Повинно бути 1"
echo "  sysctl kernel.kptr_restrict         # Повинно бути 1 або 2"
echo "  sysctl net.ipv4.conf.all.accept_redirects  # Повинно бути 0"

# Очищення
echo ""
echo "=== Очищення ==="
kubectl delete namespace kernel-test

echo ""
echo "=== Вправа завершена ==="
echo "Продемонстровані ключові знання:"
echo "1. ✓ runAsNonRoot запобігає виконанню від root"
echo "2. ✓ readOnlyRootFilesystem блокує запис"
echo "3. ✓ Скидання capabilities обмежує syscall"
echo "4. ✓ allowPrivilegeEscalation=false запобігає ескалації"
echo "5. ✓ seccompProfile застосовує фільтрацію syscall"
```

**Критерії успіху**: Розгорнути небезпечний та безпечний Pod, спостерегти різницю в безпеці, зрозуміти, як контексти безпеки Pod реалізують концепції зміцнення ядра.

---

## Підсумок

**Принципи зміцнення ОС**:
- Мінімізуйте пакети та сервіси
- Підтримуйте систему в актуальному стані
- Обмежте доступ SSH
- Правильні дозволи на файли

**Зміцнення ядра**:
- Увімкніть ASLR (`kernel.randomize_va_space = 2`)
- Обмежте dmesg (`kernel.dmesg_restrict = 1`)
- Вимкніть небезпечні мережеві функції

**Середовище виконання контейнерів**:
- Увімкніть функції безпеки
- Використовуйте профілі seccomp
- Розгляньте простори імен користувачів

**Поради для іспиту**:
- Знайте ключові параметри sysctl
- Розумійте вимоги до дозволів файлів
- Вмійте перевіряти поточну конфігурацію

---

## Наступний модуль

[Модуль 3.4: Мережева безпека](module-3.4-network-security/) — Зміцнення мережі на рівні хоста.
