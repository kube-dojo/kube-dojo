# Модуль 1.2: Інтерфейси розширення — CNI, CSI, CRI

> **Складність**: `[MEDIUM]` - Концептуальний із практичними елементами
>
> **Час на проходження**: 30-40 хвилин
>
> **Передумови**: Модуль 1.1 (Площина управління)

---

## Чому цей модуль важливий

Насправді Kubernetes не знає, як запускати контейнери, налаштовувати мережу чи надавати сховища. Здивовані?

Kubernetes створений як **модульна (pluggable)** система. Він визначає *інтерфейси* — контракти, які кажуть: "Якщо ви реалізуєте ці функції, я буду вас використовувати". Саме тому ви можете запускати Kubernetes із Docker, containerd або CRI-O. З Calico, Cilium або Flannel. З AWS EBS, GCP PD або локальним сховищем.

Навчальна програма CKA 2025 року спеціально вимагає розуміння CNI, CSI та CRI. Вам потрібно знати, що це таке, навіщо вони існують і як шукати несправності, коли вони дають збій.

> **Аналогія з USB-портом**
>
> Уявіть ці інтерфейси як USB-порти. Вашому комп'ютеру не потрібно знати особливості кожної коли-небудь створеної миші, клавіатури чи накопичувача — йому просто потрібна сумісність з USB. Аналогічно, Kubernetes визначає інтерфейси CNI/CSI/CRI, і будь-який сумісний плагін працюватиме. Хочете замінити мережевий плагін? Відключіть один, підключіть інший. Той самий кластер, інша реалізація.

---

## Що ви дізнаєтесь

До кінця цього модуля ви зрозумієте:
- Що таке CNI, CSI та CRI
- Чому Kubernetes використовує архітектуру плагінів
- Поширені реалізації кожного з них
- Як перевірити, які плагіни використовує ваш кластер
- Основи пошуку несправностей для кожного з них

---

## Частина 1: Архітектура плагінів

### 1.1 Чому плагіни?

```
┌────────────────────────────────────────────────────────────────┐
│                   Філософія Kubernetes                          │
│                                                                 │
│   "Робіть одну річ добре, дозвольте іншим робити решту"         │
│                                                                 │
│   Ядро Kubernetes:                                             │
│   ✓ Управління API та ресурсами                                │
│   ✓ Планування та оркестрація                                  │
│   ✓ Патерни контролерів                                        │
│   ✓ Узгодження бажаного стану                                  │
│                                                                 │
│   НЕ ядро Kubernetes (делеговано плагінам):                    │
│   ✗ Деталі контейнерного середовища                            │
│   ✗ Реалізація мережі                                          │
│   ✗ Надання сховища                                            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

Переваги:
- **Вибір**: Використовуйте найкращий інструмент для вашого середовища
- **Інновації**: Нові плагіни без зміни ядра Kubernetes
- **Спеціалізація**: Постачальники мереж зосереджуються на мережах, постачальники сховищ — на сховищах
- **Портативність**: Той самий Kubernetes, інша інфраструктура

### 1.2 Три основні інтерфейси

| Інтерфейс | Призначення | З ким спілкується kubelet |
|-----------|---------|------------------|
| **CRI** (Container Runtime Interface) | Запуск контейнерів | containerd, CRI-O |
| **CNI** (Container Network Interface) | Мережа Подів | Calico, Cilium, Flannel |
| **CSI** (Container Storage Interface) | Постійне сховище | AWS EBS, GCP PD, Ceph |

---

## Частина 2: CRI — Інтерфейс контейнерного середовища

### 2.1 Що він робить

CRI визначає, як kubelet взаємодіє з контейнерними середовищами. Без CRI kubelet потребував би користувацького коду для кожного середовища.

```
┌────────────────────────────────────────────────────────────────┐
│                         Потік CRI                               │
│                                                                 │
│   kubelet                                                       │
│      │                                                          │
│      │  CRI (gRPC)                                             │
│      │  "Створити контейнер з образом X"                       │
│      │  "Запустити контейнер Y"                                │
│      │  "Зупинити контейнер Z"                                 │
│      ▼                                                          │
│   ┌─────────────────┐    або   ┌─────────────────┐             │
│   │   containerd    │          │     CRI-O       │             │
│   └────────┬────────┘          └────────┬────────┘             │
│            │                            │                       │
│            ▼                            ▼                       │
│       ┌─────────┐                  ┌─────────┐                 │
│       │  runc   │                  │  runc   │                 │
│       └─────────┘                  └─────────┘                 │
│            │                            │                       │
│            ▼                            ▼                       │
│       Контейнери Linux             Контейнери Linux             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Поширені контейнерні середовища

| Середовище | Опис | Де використовується |
|---------|-------------|---------|
| **containerd** | Галузевий стандарт, випускник CNCF | за замовчуванням у kubeadm, GKE, EKS, AKS |
| **CRI-O** | Орієнтоване на Kubernetes, легке | OpenShift, деякі корпоративні рішення |
| **Docker** | ⚠️ Застаріле в K8s 1.24 | Спадкові (legacy) кластери |

> **Чи знали ви?**
>
> Припинення підтримки Docker викликало паніку у 2020 році, але вона була перебільшена. Образи Docker все ще працюють усюди — вони сумісні з OCI. Змінилося те, що kubelet більше не взаємодіє безпосередньо з демоном Docker. Більшість користувачів не помітили жодного впливу, тому що Docker створює образи, а containerd їх запускає.

### 2.3 Перевірка вашого контейнерного середовища

```bash
# What runtime is kubelet using?
kubectl get nodes -o wide
# Look at CONTAINER-RUNTIME column

# On a node, check containerd
systemctl status containerd
crictl info

# List running containers
crictl ps

# List images
crictl images

# Inspect a container
crictl inspect <container-id>
```

### 2.4 Пошук несправностей CRI

```bash
# Container runtime not responding
systemctl status containerd
journalctl -u containerd -f

# kubelet can't talk to runtime
journalctl -u kubelet | grep -i "runtime"

# Check CRI socket
ls -la /var/run/containerd/containerd.sock

# Verify kubelet configuration
cat /var/lib/kubelet/config.yaml | grep -i container
```

> **Підступ: crictl чи docker**
>
> На сучасних кластерах команди `docker` не працюють, тому що Docker не запущено. Використовуйте замість нього `crictl` — це CLI, сумісний з CRI, який взаємодіє безпосередньо з containerd.

---

## Частина 3: CNI — Мережевий інтерфейс контейнерів

### 3.1 Що він робить

CNI керує мережею Подів:
- Призначає IP-адреси Подам
- Налаштовує маршрути між Подами
- Створює мережеві простори імен
- Реалізує мережеві політики (деякі плагіни)

```
┌────────────────────────────────────────────────────────────────┐
│                       Потік CNI                                 │
│                                                                 │
│   1. kubelet створює пісочницю Пода (контейнер pause)          │
│   2. kubelet викликає плагін CNI: "Налаштувати мережу для Пода X"│
│   3. Плагін CNI:                                               │
│      - Створює пару veth (віртуальний ethernet)                │
│      - Призначає IP з пулу                                     │
│      - Налаштовує маршрути                                     │
│      - Підключає Под до мережі кластера                        │
│   4. Под тепер може спілкуватися з іншими Подами               │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Поширені плагіни CNI

| Плагін | Основні особливості | Складність |
|--------|--------------|------------|
| **Calico** | NetworkPolicy, BGP-маршрутизація, висока продуктивність | Середня |
| **Cilium** | На основі eBPF, спостережуваність, безпека | Вища |
| **Flannel** | Проста оверлейна мережа | Низька |
| **Weave** | Шифрування, просте налаштування | Низька |
| **AWS VPC CNI** | Нативна мережа VPC | Специфічно для AWS |

### 3.3 Як встановлюються плагіни CNI

Плагіни CNI зазвичай складаються з:
1. **Бінарного файлу** у `/opt/cni/bin/`
2. **Конфігурації** в `/etc/cni/net.d/`
3. **DaemonSet**, який працює на кожному вузлі (для агентів, специфічних для плагіна)

```bash
# List CNI binaries
ls /opt/cni/bin/

# List CNI configurations (first file wins!)
ls /etc/cni/net.d/

# Check the active CNI config
cat /etc/cni/net.d/10-calico.conflist  # Example for Calico
```

### 3.4 Перевірка статусу CNI

```bash
# What CNI is running?
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel|weave"

# Check CNI pod logs
kubectl logs -n kube-system -l k8s-app=calico-node --tail=50

# Verify pod IP allocation
kubectl get pods -o wide  # Check IP column

# Test pod-to-pod connectivity
kubectl exec pod-a -- ping <pod-b-ip>
```

### 3.5 Пошук несправностей CNI

```bash
# Pods stuck in ContainerCreating
kubectl describe pod <pod-name>
# Look for: "failed to set up sandbox container network"

# Check CNI configuration exists
ls -la /etc/cni/net.d/

# Check CNI binary exists
ls -la /opt/cni/bin/

# Check CNI agent logs
kubectl logs -n kube-system -l k8s-app=calico-node -c calico-node

# Node network issues
ip addr show  # Check interfaces
ip route     # Check routes
```

> **Бойова історія: Відсутній CNI**
>
> Молодший інженер розгорнув кластер kubeadm, але пропустив крок встановлення CNI. Поди назавжди застрягли у стані ContainerCreating із загадковими помилками "network not ready". Рішення полягало в одній команді: `kubectl apply -f calico.yaml`. Урок: kubeadm дає вам кластер, CNI дає вам мережу. Обидва є обов'язковими.

---

## Частина 4: CSI — Інтерфейс сховища контейнерів

### 4.1 Що він робить

CSI керує постійним сховищем:
- Надає томи (створює фактичні диски)
- Підключає томи до вузлів
- Монтує томи у Поди
- Робить знімки (snapshots) і клони

```
┌────────────────────────────────────────────────────────────────┐
│                        Потік CSI                                │
│                                                                 │
│   Створено PersistentVolumeClaim                               │
│            │                                                    │
│            ▼                                                    │
│   StorageClass визначає драйвер CSI                            │
│            │                                                    │
│            ▼                                                    │
│   CSI Controller (Deployment у kube-system)                    │
│   "Надати том об'ємом 10Gi з AWS EBS"                          │
│            │                                                    │
│            ▼                                                    │
│   Хмарний провайдер: Створює фактичний диск                    │
│            │                                                    │
│            ▼                                                    │
│   PersistentVolume створено та прив'язано                      │
│            │                                                    │
│            ▼                                                    │
│   Под заплановано на вузол                                     │
│            │                                                    │
│            ▼                                                    │
│   Плагін CSI Node: Підключає та монтує диск                    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Компоненти CSI

```
┌────────────────────────────────────────────────────────────────┐
│                   Архітектура CSI                               │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              CSI Controller (Deployment)                 │  │
│   │  - Працює як Поди у kube-system                         │  │
│   │  - Займається наданням, підключенням/відключенням       │  │
│   │  - Зазвичай 1-3 репліки                                 │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Плагін CSI Node (DaemonSet)                 │  │
│   │  - Працює на кожному вузлі                              │  │
│   │  - Займається монтуванням/розмонтуванням                │  │
│   │  - Реєструє вузол із драйвером CSI                      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Поширені драйвери CSI

| Драйвер | Сховище | Середовище |
|--------|---------|-------------|
| **ebs.csi.aws.com** | AWS EBS | AWS EKS |
| **pd.csi.storage.gke.io** | GCP Persistent Disk | GKE |
| **disk.csi.azure.com** | Azure Disk | AKS |
| **csi.vsphere.vmware.com** | vSphere | VMware |
| **rook-ceph.rbd.csi.ceph.com** | Ceph RBD | Локальне (on-premises) |
| **hostpath.csi.k8s.io** | Local path | Розробка |

### 4.4 Перевірка статусу CSI

```bash
# List CSI drivers in cluster
kubectl get csidrivers

# Check CSI pods
kubectl get pods -n kube-system | grep csi

# View StorageClasses (use CSI drivers)
kubectl get storageclasses
kubectl describe storageclass <name>

# Check PV provisioner
kubectl get pv -o jsonpath='{.items[*].spec.csi.driver}'
```

### 4.5 Пошук несправностей CSI

```bash
# PVC stuck in Pending
kubectl describe pvc <pvc-name>
# Look for: Events showing provisioning errors

# Check CSI controller logs
kubectl logs -n kube-system -l app=ebs-csi-controller -c ebs-plugin

# Check CSI node logs
kubectl logs -n kube-system -l app=ebs-csi-node -c ebs-plugin

# Verify CSI driver registered
kubectl get csinodes
kubectl describe csinode <node-name>
```

> **Чи знали ви?**
>
> До появи CSI Kubernetes мав "in-tree" (вбудовані) плагіни сховищ — код, "зашитий" у сам Kubernetes для кожного постачальника сховищ. Це було нежиттєздатно. CSI дозволяє постачальникам сховищ розробляти драйвери незалежно, випускаючи їх за власним графіком, а не за циклом випусків Kubernetes.

---

## Частина 5: Короткий довідник

### 5.1 Підсумок щодо інтерфейсів

| Інтерфейс | З ким спілкується Kubernetes | Що надає плагін | Розташування конфігурації |
|-----------|--------------------|--------------------|-----------------|
| CRI | Контейнерне середовище | Життєвий цикл контейнера | `/var/run/containerd/` |
| CNI | Мережевий плагін | IP-адреси Подів, маршрутизацію, політики | `/etc/cni/net.d/` |
| CSI | Драйвер сховища | Надання томів, монтування | CRD драйверів CSI |

### 5.2 Шпаргалка з пошуку несправностей

```bash
# ===== CRI Issues =====
# Symptom: Pods won't start, "container runtime not running"
systemctl status containerd
journalctl -u containerd
crictl info

# ===== CNI Issues =====
# Symptom: Pods stuck in ContainerCreating, "network not ready"
ls /etc/cni/net.d/
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel"
kubectl logs -n kube-system <cni-pod>

# ===== CSI Issues =====
# Symptom: PVC stuck in Pending, "provisioning failed"
kubectl get csidrivers
kubectl describe pvc <name>
kubectl logs -n kube-system <csi-controller-pod>
```

---

## Чи знали ви?

- **Порядок файлів конфігурації CNI має значення**. Kubernetes використовує перший файл за алфавітом у `/etc/cni/net.d/`. Ось чому ви бачите файли з назвами на кшталт `10-calico.conflist` — число забезпечує порядок.

- **CSI замінив Flexvolume**. Flexvolume був попередником, але він вимагав плагінів на кожному вузлі та мав проблеми з безпекою. CSI працює як контейнеризовані робочі навантаження.

- **Cilium використовує eBPF** замість iptables для мережі. Це робить його швидшим та більш спостережуваним, але вимагає сучасного ядра Linux (4.9+).

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|----------|
| Забути встановити CNI | Поди застрягли у ContainerCreating | Встановити плагін CNI після kubeadm init |
| Кілька конфігурацій CNI | Використовується неправильний плагін | Видалити старі конфігурації, залишити одну |
| Неправильний драйвер CSI | PVC не прив'язується | Підібрати StorageClass відповідно до вашої інфраструктури |
| Ігнорування журналів контролера CSI | Неможливо діагностувати надання ресурсів | Завжди перевіряти журнали контролера та плагіна вузла |
| Використання docker на нових кластерах | Команду не знайдено | Використовувати crictl |

---

## Тест

1. **Яка різниця між CNI та CSI?**
   <details>
   <summary>Відповідь</summary>
   CNI (Мережевий інтерфейс контейнерів) керує мережею Подів — призначенням IP-адрес, маршрутизацією та мережевими політиками. CSI (Інтерфейс сховища контейнерів) керує постійним сховищем — наданням, підключенням і монтуванням томів.
   </details>

2. **Де зберігаються конфігураційні файли CNI?**
   <details>
   <summary>Відповідь</summary>
   У каталозі `/etc/cni/net.d/` на кожному вузлі. Використовується перший файл за алфавітом, ось чому файли зазвичай мають префікси з чисел, наприклад `10-calico.conflist`.
   </details>

3. **Под застряг у стані ContainerCreating з помилкою "network plugin not ready". Що слід перевірити?**
   <details>
   <summary>Відповідь</summary>
   1. Перевірити, чи працюють Поди CNI: `kubectl get pods -n kube-system | grep -E "calico|cilium|flannel"`
   2. Перевірити наявність конфігурації CNI: `ls /etc/cni/net.d/`
   3. Перевірити наявність бінарних файлів CNI: `ls /opt/cni/bin/`
   4. Перевірити журнали Подів CNI на наявність помилок
   </details>

4. **Чому Kubernetes припинив підтримку Docker як контейнерного середовища?**
   <details>
   <summary>Відповідь</summary>
   Docker не був сумісний з CRI — він вимагав "прошарку" (dockershim), вбудованого в kubelet. Підтримка цього прошарку була обтяжливою. containerd і CRI-O реалізують CRI нативно, спрощуючи архітектуру. Образи Docker все ще працюють, оскільки вони сумісні з OCI.
   </details>

---

## Практична вправа

**Завдання**: Дослідіть конфігурацію CNI та CRI вашого кластера.

**Кроки**:

1. **Визначте ваше контейнерне середовище**:
```bash
kubectl get nodes -o wide
# Note the CONTAINER-RUNTIME column
```

2. **Дослідіть CRI**:
```bash
# On a node (SSH or kubectl debug node)
crictl info
crictl ps
crictl images | head -10
```

3. **Визначте ваш плагін CNI**:
```bash
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel|weave"
```

4. **Перевірте конфігурацію CNI**:
```bash
# On a node
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/*.conflist | head -30
```

5. **Перевірте мережу Подів**:
```bash
# Create two pods
kubectl run test1 --image=nginx
kubectl run test2 --image=nginx

# Get their IPs
kubectl get pods -o wide

# Test connectivity
kubectl exec test1 -- curl -s <test2-ip>:80
```

6. **Перевірте драйвери CSI** (за наявності):
```bash
kubectl get csidrivers
kubectl get storageclasses
```

**Критерії успіху**:
- [ ] Можете визначити використовуване контейнерне середовище
- [ ] Можете використовувати crictl для перевірки контейнерів
- [ ] Можете ідентифікувати плагін CNI та його конфігурацію
- [ ] Розумієте шлях мережевої взаємодії між Подами
- [ ] Знаєте, де шукати журнали кожного інтерфейсу

**Очищення**:
```bash
kubectl delete pod test1 test2
```

---

## Практичні вправи

### Вправа 1: Ідентифікація інтерфейсів (Ціль: 2 хвилини)

Зіставте кожен інструмент/плагін з його інтерфейсом:

| Інструмент/Плагін | Інтерфейс (CRI/CNI/CSI) |
|-------------|-------------------------|
| containerd | ___ |
| Calico | ___ |
| AWS EBS driver | ___ |
| CRI-O | ___ |
| Cilium | ___ |
| Rook-Ceph | ___ |

<details>
<summary>Відповіді</summary>

1. CRI - Інтерфейс контейнерного середовища
2. CNI - Мережевий інтерфейс контейнерів
3. CSI - Інтерфейс сховища контейнерів
4. CRI - Інтерфейс контейнерного середовища
5. CNI - Мережевий інтерфейс контейнерів
6. CSI - Інтерфейс сховища контейнерів

</details>

### Вправа 2: Пошук несправностей CRI — Контейнерне середовище не працює (Ціль: 5 хвилин)

```bash
# Setup: Stop containerd (WARNING: breaks cluster temporarily!)
# Only do on practice nodes you can restart!
sudo systemctl stop containerd

# Observe the damage
kubectl get nodes  # Node becomes NotReady
kubectl describe node <your-node> | grep -A5 Conditions

# YOUR TASK: Restore containerd and verify recovery
```

<details>
<summary>Рішення</summary>

```bash
sudo systemctl start containerd
sudo systemctl status containerd

# Wait for node to recover
kubectl get nodes -w  # Watch until Ready

# Verify containers running
sudo crictl ps
```

</details>

### Вправа 3: Пошук несправностей CNI — Поди застрягли у ContainerCreating (Ціль: 5 хвилин)

```bash
# Setup: Temporarily break CNI config
sudo mv /etc/cni/net.d/10-calico.conflist /tmp/

# Create a test pod
kubectl run cni-broken --image=nginx

# Observe
kubectl get pods  # ContainerCreating forever
kubectl describe pod cni-broken | grep -A10 Events

# YOUR TASK: Diagnose and fix
```

<details>
<summary>Рішення</summary>

```bash
# Check CNI config directory
ls /etc/cni/net.d/  # Empty!

# Restore CNI config
sudo mv /tmp/10-calico.conflist /etc/cni/net.d/

# Delete stuck pod and recreate
kubectl delete pod cni-broken --force --grace-period=0
kubectl run cni-fixed --image=nginx
kubectl get pods  # Running!

# Cleanup
kubectl delete pod cni-fixed
```

</details>

### Вправа 4: Майстерність використання crictl (Ціль: 3 хвилини)

Попрактикуйтесь у використанні команд crictl:

```bash
# 1. List all running containers
sudo crictl ps

# 2. List all pods (sandbox containers)
sudo crictl pods

# 3. Get container logs
sudo crictl logs <container-id>

# 4. Inspect a container
sudo crictl inspect <container-id> | head -50

# 5. List images
sudo crictl images

# 6. Get runtime info
sudo crictl info
```

### Вправа 5: Дослідження драйверів CSI (Ціль: 3 хвилини)

Дослідіть драйвери CSI у вашому кластері:

```bash
# List all CSI drivers
kubectl get csidrivers

# Get details on a driver
kubectl describe csidriver <driver-name>

# Check CSI nodes
kubectl get csinodes
kubectl describe csinode <node-name>

# View StorageClasses using CSI
kubectl get sc -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.provisioner}{"\n"}{end}'
```

### Вправа 6: Надання ресурсів CSI — Створення PVC за допомогою StorageClass (Ціль: 5 хвилин)

Відпрацюйте повний робочий процес CSI від PVC до змонтованого тому:

```bash
# Check available StorageClasses
kubectl get sc

# Create a PVC using the default StorageClass
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: csi-test-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  # storageClassName: standard  # Uncomment to use specific class
EOF

# Watch the PVC get bound (CSI provisioner creates PV)
kubectl get pvc csi-test-pvc -w

# Check the dynamically provisioned PV
kubectl get pv

# Create a pod that uses the PVC
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: csi-test-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: csi-test-pvc
EOF

# Wait for pod to be ready
kubectl wait --for=condition=ready pod/csi-test-pod --timeout=60s

# Verify the volume is mounted
kubectl exec csi-test-pod -- df -h /data

# Write test data
kubectl exec csi-test-pod -- sh -c "echo 'CSI works!' > /data/test.txt"
kubectl exec csi-test-pod -- cat /data/test.txt

# Cleanup
kubectl delete pod csi-test-pod
kubectl delete pvc csi-test-pvc
```

### Вправа 7: Перевірка підключення до мережі (Ціль: 5 хвилин)

Переконайтеся, що CNI працює правильно:

```bash
# Create pods on different nodes
kubectl run net-test-1 --image=nginx --overrides='{"spec":{"nodeName":"worker-01"}}'
kubectl run net-test-2 --image=nginx --overrides='{"spec":{"nodeName":"worker-02"}}'

# Wait for running
kubectl wait --for=condition=ready pod/net-test-1 pod/net-test-2 --timeout=60s

# Get IPs
POD1_IP=$(kubectl get pod net-test-1 -o jsonpath='{.status.podIP}')
POD2_IP=$(kubectl get pod net-test-2 -o jsonpath='{.status.podIP}')

# Test cross-node connectivity
kubectl exec net-test-1 -- curl -s --connect-timeout 5 $POD2_IP:80
kubectl exec net-test-2 -- curl -s --connect-timeout 5 $POD1_IP:80

# Cleanup
kubectl delete pod net-test-1 net-test-2
```

### Вправа 8: Виклик — Ідентифікуйте всі плагіни

Без документації ідентифікуйте всі плагіни у вашому кластері:

```bash
# 1. Find container runtime
kubectl get nodes -o wide | awk '{print $NF}'

# 2. Find CNI plugin
ls /etc/cni/net.d/
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel|weave"

# 3. Find CSI drivers
kubectl get csidrivers
kubectl get sc

# Write down what you found - this is exam knowledge!
```

---

## Наступний модуль

[Модуль 1.3: Helm](module-1.3-helm.uk.md) — Управління пакунками для Kubernetes, розгортання застосунків за допомогою чартів.
