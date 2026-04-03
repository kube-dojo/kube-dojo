---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 0.1: \u041d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u043a\u043b\u0430\u0441\u0442\u0435\u0440\u0430"
slug: uk/k8s/cka/part0-environment/module-0.1-cluster-setup
sidebar: 
  order: 1
lab: 
  id: cka-0.1-cluster-setup
  url: https://killercoda.com/kubedojo/scenario/cka-0.1-cluster-setup
  duration: "30 min"
  difficulty: beginner
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Займає час, але все просто, якщо дотримуватися кроків
>
> **Час на виконання**: 45-60 хвилин (вперше), 15-20 хвилин (коли вже знайомі)
>
> **Передумови**: Дві або більше машин (фізичні, віртуальні або хмарні інстанси)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** багатовузловий кластер kubeadm з нуля (площина управління + 2 робочих вузли)
- **Діагностувати** вузол у стані NotReady, перевіривши kubelet, CNI та стан системних подів
- **Відновити** кластер після збоїв (відсутній scheduler, аварія робочого вузла, прострочений токен)
- **Пояснити** робочий процес kubeadm init/join та що кожен компонент робить під час початкового завантаження

---

## Чому цей модуль важливий

Ви не можете практикувати адміністрування Kubernetes без кластера Kubernetes. Звучить очевидно, правда? Проте багато кандидатів на CKA повністю покладаються на керовані кластери (EKS, GKE, AKS) або одноновузлові середовища (minikube, kind), а потім впадають у ступор, коли на іспиті потрібно усунути несправності kubelet на робочому вузлі.

Іспит CKA проходить на **кластерах, розгорнутих за допомогою kubeadm**. Не на керованому Kubernetes. Не на Docker Desktop. На справжніх кластерах kubeadm з окремою площиною управління та робочими вузлами.

Цей модуль навчить вас будувати саме те, з чим ви зіткнетеся на іспиті.

> **Аналогія з оркестром**
>
> Уявіть кластер Kubernetes як оркестр. **Площина управління** — це диригент, який не грає на жодних інструментах (не запускає ваші застосунки), але координує все: хто коли грає, наскільки гучно, коли починати і закінчувати. **Робочі вузли** — це музиканти, вони виконують фактичну роботу зі створення музики (запуск контейнерів). Без диригента у вас хаос. Без музикантів — тиша. Вам потрібні обидва, щоб вони працювали разом, постійно спілкуючись.

---

## Що ви побудуєте

```
┌─────────────────────────────────────────────────────────────────┐
│                     Ваш тренувальний кластер                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│   │   cp-node   │    │  worker-01  │    │  worker-02  │       │
│   │ (управління)│    │             │    │             │       │
│   │             │    │             │    │             │       │
│   │ • API Server│    │ • kubelet   │    │ • kubelet   │       │
│   │ • etcd      │    │ • kube-proxy│    │ • kube-proxy│       │
│   │ • scheduler │    │ • containerd│    │ • containerd│       │
│   │ • ctrl-mgr  │    │             │    │             │       │
│   └─────────────┘    └─────────────┘    └─────────────┘       │
│         │                   │                   │             │
│         └───────────────────┴───────────────────┘             │
│                       Мережа подів (Calico)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**1 вузол площини управління + 2 робочі вузли** = реалістичний кластер для практики CKA.

---

## Виберіть свою інфраструктуру

Вам потрібно 3 машини. Ось ваші варіанти:

| Варіант | Переваги | Недоліки | Вартість |
|--------|------|------|------|
| **Віртуальні машини на Mac (UTM/Parallels)** | Локально, немає проблем з мережею | Вимогливі до ресурсів | Безкоштовно (UTM) |
| **Віртуальні машини на Linux (KVM/libvirt)** | Нативна продуктивність | Потрібен хост Linux | Безкоштовно |
| **Хмарні віртуальні машини (AWS/GCP/Azure)** | Найближче до середовища іспиту | Коштує грошей | ~$0.10/год |
| **Bare metal (фізичні сервери)** | Найкраща продуктивність | Потрібне обладнання | Вже наявне |
| **Кластер Raspberry Pi** | Цікавий проєкт, низьке енергоспоживання | Особливості архітектури ARM | ~$200 |

### Мінімальні характеристики для вузла

| Ресурс | Площина управління | Робочий вузол |
|----------|--------------|--------|
| CPU (Процесор) | 2 ядра | 2 ядра |
| RAM (Пам'ять) | 2 ГБ | 2 ГБ |
| Диск | 20 ГБ | 20 ГБ |
| ОС | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

> **Чи знали ви?**
>
> Середовище іспиту CKA використовує вузли на базі Ubuntu. Хоча Kubernetes працює на багатьох дистрибутивах, практика на Ubuntu означає менше сюрпризів у день іспиту.

---

## Частина 1: Підготовка всіх вузлів

Виконайте ці кроки на **ВСІХ ТРЬОХ вузлах** (площині управління ТА робочих вузлах).

### 1.1 Налаштування імен хостів

На кожному вузлі встановіть зрозуміле ім'я хоста:

```bash
# On control plane node
sudo hostnamectl set-hostname cp-node

# On first worker
sudo hostnamectl set-hostname worker-01

# On second worker
sudo hostnamectl set-hostname worker-02
```

### 1.2 Оновлення /etc/hosts

Додайте всі вузли до `/etc/hosts` на КОЖНІЙ машині:

```bash
sudo tee -a /etc/hosts << EOF
192.168.1.10  cp-node
192.168.1.11  worker-01
192.168.1.12  worker-02
EOF
```

Замініть IP-адреси на фактичні IP-адреси ваших вузлів.

### 1.3 Вимкнення файлу підкачки (Swap)

Kubernetes вимагає вимкнення файлу підкачки. Це не обговорюється.

```bash
# Disable swap immediately
sudo swapoff -a

# Disable swap permanently (survives reboot)
sudo sed -i '/ swap / s/^/#/' /etc/fstab
```

> **Бойова історія: Таємничий OOMKill**
>
> Команда витратила дні на налагодження того, чому їхні поди постійно завершувалися з помилкою OOMKilled, незважаючи на наявність достатньої кількості пам'яті. Винуватець? Був увімкнений файл підкачки. Коли kubelet повідомляв про обсяг пам'яті планувальнику, він не враховував підкачку, що призводило до надмірного планування та, зрештою, до нестачі пам'яті. Kubernetes не керує підкачкою — він очікує, що ви її вимкнете.

### 1.4 Завантаження модулів ядра

Для роботи мережі Kubernetes потрібні спеціальні модулі ядра:

```bash
# Load modules now
sudo modprobe overlay
sudo modprobe br_netfilter

# Ensure they load on boot
cat << EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
```

### 1.5 Налаштування Sysctl

Увімкніть пересилання IP-пакетів (IP forwarding) та bridge netfilter:

```bash
cat << EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply immediately
sudo sysctl --system
```

### 1.6 Перевірка cgroup v2

**Починаючи з Kubernetes 1.35, підтримка cgroup v1 вимкнена за замовчуванням.** Ваші вузли повинні використовувати cgroup v2, інакше kubelet не запуститься.

```bash
# Check cgroup version (must show "cgroup2fs")
stat -fc %T /sys/fs/cgroup
# Expected output: cgroup2fs

# If it shows "tmpfs", you're on cgroup v1 — you need a newer OS
# Affected: CentOS 7, RHEL 7, Ubuntu 18.04
# Supported: Ubuntu 22.04+, Debian 12+, RHEL 9+, Rocky 9+
```

> **Увага, критична зміна**: Якщо `stat -fc %T /sys/fs/cgroup` повертає `tmpfs` замість `cgroup2fs`, оновіть вашу ОС перед продовженням. Kubernetes 1.35 не запуститься на вузлах з cgroup v1.

### 1.7 Встановлення containerd

Kubernetes потребує середовища виконання контейнерів. Необхідно **containerd 2.0+** (1.35 — остання версія, що підтримує containerd 1.x):

```bash
# Install containerd (ensure version 2.0+)
sudo apt-get update
sudo apt-get install -y containerd

# Verify version
containerd --version
# Should be 2.0.0 or later

# Create default config
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Enable systemd cgroup driver (IMPORTANT!)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart containerd
sudo systemctl restart containerd
sudo systemctl enable containerd
```

> **Пастка: SystemdCgroup**
>
> Якщо ви пропустите налаштування `SystemdCgroup = true`, пізніше ви отримаєте незрозумілі помилки. kubelet та containerd повинні узгодити драйвер cgroup. Сучасні системи використовують systemd. Не пропустіть цей крок.

> **Пастка: containerd 2.0 та старі образи**
>
> containerd 2.0 припиняє підтримку образів Docker Schema 1. Якщо у вас є дуже старі образи (завантажені понад 5 років тому), їх не вдасться завантажити (pull). Зберіть їх наново або завантажте знову за допомогою сучасного Docker/buildkit.

### 1.8 Встановлення kubeadm, kubelet, kubectl

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes repository key
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add Kubernetes repository
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install components
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl

# Prevent automatic updates (version consistency matters)
sudo apt-mark hold kubelet kubeadm kubectl
```

### 1.9 Перевірка налаштувань

Виконайте на кожному вузлі:

```bash
# Check containerd
sudo systemctl status containerd

# Check kubelet (will be inactive until cluster is initialized)
sudo systemctl status kubelet

# Check kubeadm version
kubeadm version
```

---

## Частина 2: Ініціалізація площини управління

Виконайте ці кроки **ТІЛЬКИ на вузлі площини управління** (cp-node).

### 2.1 Ініціалізація кластера

```bash
sudo kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --control-plane-endpoint=cp-node:6443
```

Це займе 2-3 хвилини. Після завершення ви побачите такий вивід:

```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join cp-node:6443 --token abcdef.0123456789abcdef \
    --discovery-token-ca-cert-hash sha256:...
```

**ЗБЕРЕЖІТЬ КОМАНДУ ПРИЄДНАННЯ (JOIN COMMAND)!** Вона знадобиться вам для робочих вузлів.

### 2.2 Налаштування kubectl

Від імені звичайного користувача (не root):

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 2.3 Перевірка площини управління

```bash
kubectl get nodes
```

Вивід:
```
NAME      STATUS     ROLES           AGE   VERSION
cp-node   NotReady   control-plane   1m    v1.35.0
```

Вузол відображається як `NotReady`, оскільки ми ще не встановили мережевий плагін.

---

## Частина 3: Встановлення мережевого плагіна (CNI)

Kubernetes не постачається з вбудованою мережею. Ви повинні встановити плагін CNI. Ми будемо використовувати Calico (широко використовується, підходить для іспиту).

> **Чому Kubernetes не включає мережу?**
>
> Спочатку це всіх дивує. Kubernetes зробив свідомий вибір визначити мережеву *модель* (кожен под отримує IP-адресу, поди можуть взаємодіяти один з одним), але не *реалізовувати* її. Чому? Тому що потреби в мережі сильно відрізняються — комусь потрібні розширені політики, комусь висока продуктивність, комусь інтеграція з хмарою. Використовуючи стандарт CNI (Container Network Interface), Kubernetes дозволяє вам обирати. Calico, Flannel, Cilium, Weave — всі вони реалізують однаковий інтерфейс, але мають різні суперздібності. Це як USB: стандарт визначає, як підключатися, але ви самі обираєте пристрій.

**На вузлі площини управління:**

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```

Зачекайте, поки поди Calico будуть готові:

```bash
kubectl get pods -n kube-system -w
```

Через 1-2 хвилини перевірте статус вузла:

```bash
kubectl get nodes
```

Вивід:
```
NAME      STATUS   ROLES           AGE   VERSION
cp-node   Ready    control-plane   5m    v1.35.0
```

`Ready`! Площина управління працює.

---

## Частина 4: Приєднання робочих вузлів

Виконайте ці кроки на **КОЖНОМУ робочому вузлі** (worker-01 та worker-02).

### 4.1 Приєднання до кластера

Використовуйте команду приєднання з виводу `kubeadm init`:

```bash
sudo kubeadm join cp-node:6443 --token abcdef.0123456789abcdef \
    --discovery-token-ca-cert-hash sha256:...
```

> **Пастка: Термін дії токена закінчився?**
>
> Термін дії токенів закінчується через 24 години. Якщо ваш токен протермінований:
> ```bash
> # On control plane, generate new token
> kubeadm token create --print-join-command
> ```

### 4.2 Перевірка приєднання робочих вузлів

**На вузлі площини управління:**

```bash
kubectl get nodes
```

Вивід:
```
NAME        STATUS   ROLES           AGE   VERSION
cp-node     Ready    control-plane   10m   v1.35.0
worker-01   Ready    <none>          2m    v1.35.0
worker-02   Ready    <none>          1m    v1.35.0
```

Всі вузли у статусі `Ready`! Ваш кластер працює.

> **Бойова історія: Примарний вузол**
>
> Один інженер якось витратив годину, намагаючись з'ясувати, чому в його "3-вузловому кластері" відображаються лише 2 вузли. Він виконав `kubeadm join` на всіх трьох машинах. Виявилося, що він помилково запустив команду на вузлі площини управління (замість робочого вузла), яка непомітно завершилася невдачею, оскільки цей вузол вже був у кластері. Урок: завжди перевіряйте, до якого вузла ви підключені через SSH, перш ніж виконувати команди. Ім'я хоста у підказці вашого термінала — ваш друг.

### 4.3 Додавання міток до робочих вузлів (Необов'язково, але рекомендовано)

```bash
kubectl label node worker-01 node-role.kubernetes.io/worker=
kubectl label node worker-02 node-role.kubernetes.io/worker=
```

Тепер `kubectl get nodes` показує:
```
NAME        STATUS   ROLES           AGE   VERSION
cp-node     Ready    control-plane   10m   v1.35.0
worker-01   Ready    worker          3m    v1.35.0
worker-02   Ready    worker          2m    v1.35.0
```

---

## Частина 5: Перевірка вашого кластера

Виконайте ці тести, щоб переконатися, що все працює:

### 5.1 Розгортання тестового застосунку

```bash
kubectl create deployment nginx --image=nginx --replicas=3
kubectl expose deployment nginx --port=80 --type=NodePort
```

### 5.2 Перевірка розподілу подів між вузлами

```bash
kubectl get pods -o wide
```

Ви повинні побачити поди, що працюють на різних робочих вузлах:
```
NAME                     READY   STATUS    NODE
nginx-77b4fdf86c-abc12   1/1     Running   worker-01
nginx-77b4fdf86c-def34   1/1     Running   worker-02
nginx-77b4fdf86c-ghi56   1/1     Running   worker-01
```

### 5.3 Перевірка з'єднання

```bash
# Get NodePort
kubectl get svc nginx

# Test from any node
curl http://worker-01:<nodeport>
```

### 5.4 Очищення тестових ресурсів

```bash
kubectl delete deployment nginx
kubectl delete svc nginx
```

---

## Короткий довідник: Команди, які ви часто використовуватимете

```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes
kubectl get pods -A

# Check component health
kubectl get componentstatuses  # deprecated but still works

# SSH to nodes for troubleshooting
ssh worker-01 "sudo systemctl status kubelet"
ssh worker-01 "sudo journalctl -u kubelet -f"

# Reset a node (start over)
sudo kubeadm reset
```

---

## Чи знали ви?

- **kubeadm** був створений спеціально для того, щоб зробити налаштування кластера простим. До появи kubeadm налаштування Kubernetes передбачало ручну генерацію сертифікатів, написання unit-файлів systemd та ручне налаштування кожного компонента. Деякі люди досі роблять це ("Kubernetes the Hard Way") для навчання, але kubeadm є виробничим стандартом.

- **На іспиті CKA використовуються кластери kubeadm**. На іспиті ви не побачите керований Kubernetes (EKS/GKE/AKS). Все базується на kubeadm, тому практика з kubeadm є важливою.

- **containerd замінив Docker** як середовище виконання контейнерів за замовчуванням у Kubernetes 1.24. Docker все ще працює (через cri-dockerd), але containerd є простішим і саме з ним ви зіткнетеся на іспиті.

---

## Типові помилки

| Проблема | Причина | Рішення |
|---------|-------|----------|
| `kubelet` постійно перезапускається | Увімкнений файл підкачки (Swap) | `sudo swapoff -a` |
| Вузли застрягли у стані `NotReady` | Не встановлено CNI | Встановіть Calico/Flannel |
| `kubeadm init` зависає | Брандмауер блокує порти | Відкрийте порти 6443, 10250 |
| Термін дії токена закінчився | Токени діють 24 години | `kubeadm token create --print-join-command` |
| `connection refused` до API | Неправильний kubeconfig | Перевірте `~/.kube/config` |

---

## Тест

1. **Чому файл підкачки (swap) повинен бути вимкнений для Kubernetes?**
   <details>
   <summary>Відповідь</summary>
   Kubernetes очікує прямого управління пам'яттю. З увімкненим файлом підкачки kubelet не може точно звітувати про використання пам'яті, що призводить до надмірного планування та непередбачуваної поведінки. Планувальнику потрібна надійна інформація про пам'ять.
   </details>

2. **Яке призначення прапорця `--pod-network-cidr` у команді `kubeadm init`?**
   <details>
   <summary>Відповідь</summary>
   Він визначає діапазон IP-адрес для мережі подів. Плагін CNI (наприклад, Calico) використовує цей діапазон для призначення IP-адрес подам. Різні CNI мають різні вимоги — Calico є гнучким, але Flannel за замовчуванням вимагає 10.244.0.0/16.
   </details>

3. **Вузол відображається як `NotReady` після приєднання. Яка найімовірніша причина?**
   <details>
   <summary>Відповідь</summary>
   Плагін CNI не встановлений або не працює. Без CNI поди не можуть отримати мережеві адреси, і вузол повідомляє про стан NotReady. Перевірте статус подів CNI за допомогою `kubectl get pods -n kube-system`.
   </details>

4. **Вам потрібно додати новий робочий вузол, але ви втратили команду приєднання. Як її отримати?**
   <details>
   <summary>Відповідь</summary>
   Виконайте `kubeadm token create --print-join-command` на вузлі площини управління. Це згенерує новий токен та виведе повну команду приєднання.
   </details>

---

## Практична вправа

**Завдання**: Побудуйте свій тренувальний кластер, дотримуючись цього посібника.

**Критерії успіху**:
- [ ] 3 вузли у статусі `Ready` при виконанні `kubectl get nodes`
- [ ] Поди Calico працюють у просторі імен `kube-system`
- [ ] Можна розгорнути под і він буде запланований на робочий вузол
- [ ] Можна підключитися через SSH до робочого вузла і перевірити статус kubelet

**Перевірка**:
```bash
# All nodes ready?
kubectl get nodes | grep -c "Ready"  # Should output: 3

# Calico running?
kubectl get pods -n kube-system | grep calico

# Pods scheduling to workers?
kubectl run test --image=nginx
kubectl get pod test -o wide  # Should show worker node
kubectl delete pod test
```

---

## Практичні вправи

### Вправа 1: Перевірка працездатності вузла (Ціль: 2 хвилини)

Переконайтеся, що ваш кластер справний. Виконайте ці команди та підтвердьте очікуваний вивід:

```bash
# All nodes Ready?
kubectl get nodes
# Expected: 3 nodes, all STATUS=Ready

# All system pods running?
kubectl get pods -n kube-system | grep -v Running
# Expected: No output (all pods Running)

# Can schedule workloads?
kubectl run test --image=nginx --rm -it --restart=Never -- echo "Cluster healthy"
# Expected: "Cluster healthy" then pod deleted
```

### Вправа 2: Усунення несправностей - Вузол у стані NotReady (Ціль: 5 хвилин)

**Сценарій**: Змоделюйте ситуацію, коли вузол переходить у стан NotReady, і виправте це.

```bash
# On worker-01, stop kubelet
sudo systemctl stop kubelet

# On control plane, watch node status
kubectl get nodes -w
# Wait until worker-01 shows NotReady

# Diagnose the issue
kubectl describe node worker-01 | grep -A5 Conditions

# Fix: Restart kubelet on worker-01
sudo systemctl start kubelet

# Verify recovery
kubectl get nodes
```

**Чого ви навчилися**: працездатність kubelet безпосередньо впливає на статус вузла.

### Вправа 3: Усунення несправностей - Збій CNI (Ціль: 5 хвилин)

**Сценарій**: Поди застрягли у стані ContainerCreating після проблем з CNI.

```bash
# Create a test pod
kubectl run cni-test --image=nginx

# Check status (should be Running if CNI works)
kubectl get pod cni-test

# If ContainerCreating, diagnose:
kubectl describe pod cni-test | grep -A10 Events
kubectl get pods -n kube-system | grep calico

# Common fix: Restart CNI pods
kubectl delete pods -n kube-system -l k8s-app=calico-node

# Cleanup
kubectl delete pod cni-test
```

### Вправа 4: Скидання та відбудова (Ціль: 15 хвилин)

**Завдання**: Попрактикуйтеся у відновленні кластера, скинувши робочий вузол та приєднавши його знову.

```bash
# On worker-01: Reset the node
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d

# On control plane: Remove the node
kubectl delete node worker-01

# On control plane: Generate new join command
kubeadm token create --print-join-command

# On worker-01: Rejoin
sudo kubeadm join <command-from-above>

# Verify
kubectl get nodes
```

### Вправа 5: Завдання - Додавання третього робочого вузла (Ціль: 20 хвилин)

**Без підказок.** Використовуючи лише те, чого ви навчилися в цьому модулі:

1. Підготуйте нову віртуальну машину з такими ж базовими налаштуваннями
2. Приєднайте її до кластера як `worker-03`
3. Переконайтеся, що вона у стані Ready і на ній можуть плануватися поди
4. Додайте мітку `node-role.kubernetes.io/worker=`

<details>
<summary>Підказки (тільки якщо застрягли)</summary>

1. Виконайте всі кроки Частини 1 (1.1-1.8) на новому вузлі
2. Отримайте команду приєднання: `kubeadm token create --print-join-command`
3. Додайте мітку: `kubectl label node worker-03 node-role.kubernetes.io/worker=`

</details>

### Вправа 6: Полагодження зламаного кластера

**Сценарій**: Ваш колега щось зламав. Полагодьте це.

```bash
# Setup: Run this to break the cluster (on control plane)
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/

# Problem: New pods won't schedule
kubectl run broken-test --image=nginx
kubectl get pods  # STATUS: Pending forever

# YOUR TASK: Figure out why and fix it
# Hint: Check control plane components
```

<details>
<summary>Рішення</summary>

```bash
# Check what's running in kube-system
kubectl get pods -n kube-system
# Notice: No scheduler pod!

# Check manifest directory
ls /etc/kubernetes/manifests/
# Notice: kube-scheduler.yaml is missing

# Fix: Restore the scheduler
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/

# Wait for scheduler to restart
kubectl get pods -n kube-system | grep scheduler

# Verify pod now schedules
kubectl get pods  # Should transition to Running
kubectl delete pod broken-test
```

</details>

---

## Наступний модуль

[Модуль 0.2: Майстерність роботи в оболонці](module-0.2-shell-mastery/) — Псевдоніми (aliases), автодоповнення та оптимізація оболонки для швидкості.
