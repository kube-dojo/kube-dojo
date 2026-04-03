---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 1.7: \u041e\u0441\u043d\u043e\u0432\u0438 kubeadm \u2014 \u041f\u043e\u0447\u0430\u0442\u043a\u043e\u0432\u0435 \u043d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u043a\u043b\u0430\u0441\u0442\u0435\u0440\u0430"
slug: uk/k8s/cka/part1-cluster-architecture/module-1.7-kubeadm
sidebar: 
  order: 8
lab: 
  id: cka-1.7-kubeadm
  url: https://killercoda.com/kubedojo/scenario/cka-1.7-kubeadm
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Основи управління кластером
>
> **Час на виконання**: 35–45 хвилин
>
> **Передумови**: Модуль 1.1 (Площина управління), Модуль 1.2 (Інтерфейси розширення)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Оновити** кластер kubeadm безпечно (спочатку площина управління, потім робочі вузли, по одному)
- **Створити** резервну копію та відновити знімки etcd для аварійного відновлення
- **Керувати** сертифікатами kubeadm (перевірка терміну дії, оновлення, ротація)
- **Діагностувати** збої оновлення kubeadm, читаючи логи компонентів та перевіряючи сумісність версій

---

## Чому цей модуль важливий

kubeadm — це офіційний інструмент для створення кластерів Kubernetes. Середовище іспиту CKA використовує кластери на основі kubeadm, і вам потрібно розуміти, як вони працюють.

Хоча програма 2025 року **знижує пріоритет оновлення кластерів**, вам все одно потрібно знати:
- Як відбувається початкове налаштування кластерів
- Як приєднувати вузли
- Де розташовані компоненти площини управління
- Базові завдання обслуговування кластера

Розуміння kubeadm допомагає усувати неполадки кластера та розуміти, що відбувається «під капотом».

> **Аналогія з будівельним кресленням**
>
> Уявіть kubeadm як бригадира з кресленнями. Коли ви говорите «init», він слідує кресленням для побудови площини управління — закладає фундамент (сертифікати), зводить каркас (статичні Поди) та підключає комунікації (мережу). Коли прибувають робітники (вузли), він дає їм інструкції для приєднання до команди. Бригадир не будує будинок сам — він оркеструє процес.

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Розуміти, що робить kubeadm під час створення кластера
- Виконувати початкове налаштування вузла площини управління
- Приєднувати робочі вузли до кластера
- Розуміти статичні Поди та маніфести
- Виконувати базове управління вузлами

---

## Частина 1: Огляд kubeadm

### 1.1 Що робить kubeadm

kubeadm автоматизує налаштування кластера:

```
┌────────────────────────────────────────────────────────────────┐
│                   Процес kubeadm init                          │
│                                                                │
│   1. Попередні перевірки                                      │
│      └── Перевірка системних вимог (CPU, пам'ять, порти)      │
│                                                                │
│   2. Генерація сертифікатів                                   │
│      └── CA, API server, kubelet, etcd сертифікати            │
│      └── Зберігаються у /etc/kubernetes/pki/                  │
│                                                                │
│   3. Генерація файлів kubeconfig                              │
│      └── admin.conf, kubelet.conf, controller-manager.conf    │
│      └── Зберігаються у /etc/kubernetes/                      │
│                                                                │
│   4. Генерація маніфестів статичних Подів                     │
│      └── API server, controller-manager, scheduler, etcd      │
│      └── Зберігаються у /etc/kubernetes/manifests/            │
│                                                                │
│   5. Запуск kubelet                                           │
│      └── kubelet читає маніфести та запускає площину управління│
│                                                                │
│   6. Застосування конфігурації кластера                       │
│      └── CoreDNS, kube-proxy DaemonSet                        │
│                                                                │
│   7. Генерація токена приєднання                              │
│      └── Для приєднання робочих вузлів                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Чого kubeadm НЕ робить

- **Не встановлює середовище виконання контейнерів** (containerd) — це ви робите першим
- **Не встановлює kubelet/kubectl** — це ви встановлюєте першим
- **Не встановлює CNI-плагін** — ви застосовуєте його після init
- **Не налаштовує балансувальники навантаження** — це ваша інфраструктура
- **Не налаштовує високу доступність** — потрібна додаткова конфігурація

### 1.3 Передумови

Перед запуском kubeadm:

```bash
# Потрібно на ВСІХ вузлах:
# 1. Container runtime (containerd)
# 2. kubelet
# 3. kubeadm
# 4. kubectl (принаймні на площині управління)
# 5. Swap вимкнено
# 6. Необхідні порти відкриті
# 7. Унікальний hostname, MAC, product_uuid
```

---

## Частина 2: Ініціалізація кластера

### 2.1 Базовий kubeadm init

```bash
# Initialize control plane
sudo kubeadm init

# With specific pod network CIDR (required by some CNIs)
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# With specific API server address (for HA or custom networking)
sudo kubeadm init --apiserver-advertise-address=192.168.1.10

# With specific Kubernetes version
sudo kubeadm init --kubernetes-version=v1.35.0
```

### 2.2 Після init — Налаштування доступу kubectl

```bash
# For regular user (recommended)
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# For root user
export KUBECONFIG=/etc/kubernetes/admin.conf
```

### 2.3 Встановлення CNI-плагіна

```bash
# Without CNI, pods won't get IPs and CoreDNS won't start

# Calico
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/calico.yaml

# Flannel
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# Cilium
cilium install
```

### 2.4 Перевірка кластера

```bash
# Check nodes
kubectl get nodes
# NAME           STATUS   ROLES           AGE   VERSION
# control-plane  Ready    control-plane   5m    v1.35.0

# Check system pods
kubectl get pods -n kube-system
# Should see: coredns, etcd, kube-apiserver, kube-controller-manager,
#             kube-proxy, kube-scheduler, CNI pods
```

> **Чи знали ви?**
>
> Вивід `kubeadm init` містить команду `kubeadm join` з токеном. Цей токен закінчується через 24 години за замовчуванням. Збережіть його, інакше доведеться генерувати новий.

---

## Частина 3: Приєднання робочих вузлів

### 3.1 Команда приєднання

Після `kubeadm init` ви отримуєте команду приєднання:

```bash
# Example output from kubeadm init
kubeadm join 192.168.1.10:6443 --token abcdef.0123456789abcdef \
  --discovery-token-ca-cert-hash sha256:abc123...
```

Виконайте це на робочих вузлах:

```bash
# On worker node (as root)
sudo kubeadm join 192.168.1.10:6443 \
  --token abcdef.0123456789abcdef \
  --discovery-token-ca-cert-hash sha256:abc123...
```

### 3.2 Повторна генерація токенів приєднання

Якщо токен закінчився:

```bash
# On control plane - create new token
kubeadm token create --print-join-command

# Or manually:
# 1. Create token
kubeadm token create

# 2. Get CA cert hash
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | \
  openssl rsa -pubin -outform der 2>/dev/null | \
  openssl dgst -sha256 -hex | sed 's/^.* //'

# 3. Construct join command
kubeadm join <control-plane-ip>:6443 --token <new-token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

### 3.3 Перегляд та управління токенами

```bash
# List existing tokens
kubeadm token list

# Delete a token
kubeadm token delete <token>

# Create token with custom TTL
kubeadm token create --ttl 2h
```

---

## Частина 4: Розуміння статичних Подів

### 4.1 Що таке статичні Поди?

Статичні Поди управляються безпосередньо kubelet, а не API-сервером. Компоненти площини управління працюють як статичні Поди в кластерах kubeadm.

```bash
# Static pod manifests location
ls /etc/kubernetes/manifests/
# etcd.yaml
# kube-apiserver.yaml
# kube-controller-manager.yaml
# kube-scheduler.yaml
```

### 4.2 Як працюють статичні Поди

```
┌────────────────────────────────────────────────────────────────┐
│               Життєвий цикл статичного Пода                    │
│                                                                │
│   /etc/kubernetes/manifests/                                   │
│           │                                                    │
│           │ kubelet спостерігає за цією директорією            │
│           ▼                                                    │
│   ┌─────────────┐                                              │
│   │   kubelet   │                                              │
│   └──────┬──────┘                                              │
│          │                                                     │
│          │ Для кожного YAML-файлу:                            │
│          │ 1. Запустити контейнер                             │
│          │ 2. Підтримувати його роботу                        │
│          │ 3. Перезапустити при збої                           │
│          │ 4. Створити дзеркальний Под в API-сервері          │
│          ▼                                                     │
│   ┌─────────────────────────────────────────┐                  │
│   │ Контейнери площини управління            │                  │
│   │ • kube-apiserver                        │                  │
│   │ • kube-controller-manager               │                  │
│   │ • kube-scheduler                        │                  │
│   │ • etcd                                  │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Робота зі статичними Подами

```bash
# View static pod manifests
sudo cat /etc/kubernetes/manifests/kube-apiserver.yaml

# Modify a static pod (edit the manifest)
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# kubelet automatically restarts the pod

# "Delete" a static pod (remove the manifest)
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/
# kubelet stops the pod

# Restore it
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/
# kubelet starts the pod again
```

> **Підступність: kubectl delete не спрацює**
>
> Ви не можете видалити статичні Поди за допомогою `kubectl delete pod`. Вони негайно створюються заново, бо ними управляє kubelet. Щоб зупинити статичний Под, видаліть або перейменуйте його файл маніфесту.

---

## Частина 5: Структура директорій кластера

### 5.1 Ключові директорії

```
/etc/kubernetes/
├── admin.conf               # Конфігурація kubectl для адміністратора
├── controller-manager.conf  # kubeconfig для controller-manager
├── kubelet.conf             # kubeconfig для kubelet
├── scheduler.conf           # kubeconfig для scheduler
├── manifests/               # Визначення статичних Подів
│   ├── etcd.yaml
│   ├── kube-apiserver.yaml
│   ├── kube-controller-manager.yaml
│   └── kube-scheduler.yaml
└── pki/                     # Сертифікати
    ├── ca.crt               # CA кластера
    ├── ca.key
    ├── apiserver.crt        # Сертифікат API-сервера
    ├── apiserver.key
    ├── apiserver-kubelet-client.crt
    ├── front-proxy-ca.crt
    ├── sa.key               # Ключ підпису ServiceAccount
    ├── sa.pub
    └── etcd/                # Сертифікати etcd
        ├── ca.crt
        └── ...
```

### 5.2 Розташування сертифікатів

```bash
# Cluster CA
/etc/kubernetes/pki/ca.crt
/etc/kubernetes/pki/ca.key

# API Server
/etc/kubernetes/pki/apiserver.crt
/etc/kubernetes/pki/apiserver.key

# etcd CA (separate CA)
/etc/kubernetes/pki/etcd/ca.crt
/etc/kubernetes/pki/etcd/ca.key

# Check certificate expiration
kubeadm certs check-expiration
```

---

## Частина 6: Управління вузлами

### 6.1 Перегляд вузлів

```bash
# List nodes
kubectl get nodes

# Detailed info
kubectl get nodes -o wide

# Node details
kubectl describe node <node-name>
```

### 6.2 Виведення вузла з експлуатації (drain)

Перед обслуговуванням виведіть вузол з експлуатації для безпечного виселення Подів:

```bash
# Drain node (evict pods, mark unschedulable)
kubectl drain <node-name> --ignore-daemonsets

# If there are pods with local storage:
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Force (for pods without controllers):
kubectl drain <node-name> --ignore-daemonsets --force
```

### 6.3 Cordon та Uncordon

```bash
# Mark node unschedulable (no new pods)
kubectl cordon <node-name>

# Mark node schedulable again
kubectl uncordon <node-name>

# Check node status
kubectl get nodes
# NAME    STATUS                     ROLES    AGE   VERSION
# node1   Ready                      worker   10d   v1.35.0
# node2   Ready,SchedulingDisabled   worker   10d   v1.35.0  # cordoned
```

### 6.4 Видалення вузла

```bash
# 1. Drain the node first
kubectl drain <node-name> --ignore-daemonsets --force

# 2. Delete from cluster
kubectl delete node <node-name>

# 3. On the node itself, reset kubeadm
sudo kubeadm reset

# 4. Clean up
sudo rm -rf /etc/kubernetes/
sudo rm -rf /var/lib/kubelet/
sudo rm -rf /var/lib/etcd/
```

---

## Частина 7: kubeadm reset

### 7.1 Коли використовувати reset

Використовуйте `kubeadm reset` щоб:
- Видалити вузол із кластера
- Почати заново після невдалого init
- Повністю розібрати кластер

### 7.2 Процес скидання

```bash
# On the node to reset
sudo kubeadm reset

# This does:
# 1. Stops kubelet
# 2. Removes /etc/kubernetes/
# 3. Removes cluster state from etcd (if control plane)
# 4. Removes certificates
# 5. Cleans up iptables rules

# Additional cleanup you should do:
sudo rm -rf /etc/cni/net.d/
sudo rm -rf $HOME/.kube/config
sudo iptables -F && sudo iptables -t nat -F
```

---

## Частина 8: Типове усунення неполадок

### 8.1 kubelet не запускається

```bash
# Check kubelet status
systemctl status kubelet

# Check kubelet logs
journalctl -u kubelet -f

# Common issues:
# - Swap not disabled
# - Container runtime not running
# - Wrong container runtime socket
```

### 8.2 Площина управління не запускається

```bash
# Check container runtime
crictl ps

# Check static pod containers
crictl logs <container-id>

# Look for API server errors
sudo cat /var/log/pods/kube-system_kube-apiserver-*/kube-apiserver/*.log
```

### 8.3 Вузол не приєднується

```bash
# On the node, check logs
journalctl -u kubelet | tail -50

# Common issues:
# - Token expired
# - Wrong CA hash
# - Network connectivity to control plane
# - Firewall blocking port 6443
```

### 8.4 Сертифікати закінчились

```bash
# Check expiration
kubeadm certs check-expiration

# Renew all certificates
kubeadm certs renew all

# Restart control plane components
# (just move manifests and wait)
```

---

## Частина 9: Команди, релевантні для іспиту

### 9.1 Швидка довідка

```bash
# Initialize cluster
kubeadm init --pod-network-cidr=10.244.0.0/16

# Get join command
kubeadm token create --print-join-command

# Join worker
kubeadm join <control-plane>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>

# Check certificates
kubeadm certs check-expiration

# Drain node for maintenance
kubectl drain <node> --ignore-daemonsets

# Make node schedulable again
kubectl uncordon <node>

# Reset node
kubeadm reset
```

---

## Чи знали ви?

- **kubeadm не управляє kubelet**. kubelet працює як сервіс systemd. kubeadm генерує конфігурацію, але systemctl управляє сервісом.

- **Статичні Поди мають дзеркальні Поди**. API-сервер показує «дзеркальні» Поди для статичних Подів, щоб ви могли бачити їх через kubectl. Але управляти ними через API не можна.

- **Площини управління з високою доступністю** потребують зовнішніх балансувальників навантаження. kubeadm може ініціалізувати додаткові вузли площини управління, але балансування навантаження потрібно налаштовувати самостійно.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Запуск init з увімкненим swap | Init завершується невдачею | `swapoff -a` та видалити з /etc/fstab |
| Забули CNI після init | Поди залишаються у стані Pending | Встановіть CNI одразу після init |
| Токен закінчився | Не вдається приєднати вузли | `kubeadm token create --print-join-command` |
| Використання kubectl delete для статичних Подів | Поди постійно повертаються | Редагуйте/видаляйте маніфести у /etc/kubernetes/manifests/ |
| Не зробили drain перед обслуговуванням | Порушення роботи Подів | Завжди спочатку `kubectl drain` |

---

## Тест

1. **Де зберігаються маніфести статичних Подів площини управління?**
   <details>
   <summary>Відповідь</summary>
   `/etc/kubernetes/manifests/` на вузлі площини управління. kubelet спостерігає за цією директорією та управляє визначеними там Подами.
   </details>

2. **Ви втратили команду kubeadm join. Як отримати нову?**
   <details>
   <summary>Відповідь</summary>
   Виконайте `kubeadm token create --print-join-command` на площині управління. Це створить новий токен та виведе повну команду приєднання з хешем сертифіката CA.
   </details>

3. **Як заборонити планування нових Подів на вузлі без виселення існуючих Подів?**
   <details>
   <summary>Відповідь</summary>
   `kubectl cordon <node-name>` позначає вузол як непридатний для планування. Існуючі Поди продовжують працювати, але нові Поди не будуть плануватися на цьому вузлі.
   </details>

4. **Ви відредагували /etc/kubernetes/manifests/kube-apiserver.yaml. Що відбудеться далі?**
   <details>
   <summary>Відповідь</summary>
   kubelet виявить зміну файлу та автоматично перезапустить Под kube-apiserver з новою конфігурацією. Ручний перезапуск не потрібен.
   </details>

---

## Практична вправа

**Завдання**: Відпрацюйте операції управління вузлами.

> **Примітка**: Ця вправа потребує кластер з принаймні одним робочим вузлом. Якщо використовуєте minikube або kind, деякі операції можуть відрізнятися.

**Кроки**:

1. **Перегляд вузлів кластера**:
```bash
kubectl get nodes -o wide
```

2. **Дослідження вузла**:
```bash
kubectl describe node <node-name> | head -50
```

3. **Перевірка маніфестів статичних Подів** (на площині управління):
```bash
# If you have SSH access to control plane
ls /etc/kubernetes/manifests/
cat /etc/kubernetes/manifests/kube-apiserver.yaml | head -30
```

4. **Практика cordon/uncordon**:
```bash
# Cordon a worker node
kubectl cordon <worker-node>
kubectl get nodes
# Should show SchedulingDisabled

# Try to schedule a pod
kubectl run test-pod --image=nginx

# Check where it landed
kubectl get pods -o wide
# Won't be on cordoned node

# Uncordon
kubectl uncordon <worker-node>
kubectl get nodes
```

5. **Практика drain** (обережно у продакшені!):
```bash
# Create a deployment first
kubectl create deployment drain-test --image=nginx --replicas=2

# Check pod locations
kubectl get pods -o wide

# Drain a node with pods
kubectl drain <node-with-pods> --ignore-daemonsets

# Check pods moved
kubectl get pods -o wide

# Uncordon the node
kubectl uncordon <node-name>
```

6. **Перевірка сертифікатів** (на площині управління):
```bash
# If you have access to control plane
kubeadm certs check-expiration
```

7. **Генерація команди приєднання**:
```bash
# On control plane
kubeadm token create --print-join-command
```

8. **Очищення**:
```bash
kubectl delete deployment drain-test
kubectl delete pod test-pod
```

**Критерії успіху**:
- [ ] Вмієте переглядати та описувати вузли
- [ ] Розумієте різницю між cordon та drain
- [ ] Знаєте, де зберігаються маніфести статичних Подів
- [ ] Вмієте генерувати нові токени приєднання
- [ ] Розумієте процес kubeadm init

---

## Практичні вправи

### Вправа 1: Команди управління вузлами (Ціль: 3 хвилини)

```bash
# List nodes with details
kubectl get nodes -o wide

# Get node labels
kubectl get nodes --show-labels

# Describe a node
kubectl describe node <node-name> | head -50

# Check node conditions
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Check node resources
kubectl describe node <node-name> | grep -A10 "Allocated resources"
```

### Вправа 2: Cordon та Uncordon (Ціль: 5 хвилин)

```bash
# Cordon a node (prevent new pods)
kubectl cordon <worker-node>

# Verify
kubectl get nodes  # Shows SchedulingDisabled

# Try to schedule a pod
kubectl run cordon-test --image=nginx
kubectl get pods -o wide  # Won't be on cordoned node

# Uncordon
kubectl uncordon <worker-node>
kubectl get nodes  # Back to Ready

# Cleanup
kubectl delete pod cordon-test
```

### Вправа 3: Drain та відновлення (Ціль: 5 хвилин)

```bash
# Create test deployment
kubectl create deployment drain-test --image=nginx --replicas=3

# Wait for pods
kubectl wait --for=condition=available deployment/drain-test --timeout=60s
kubectl get pods -o wide

# Drain a worker node
kubectl drain <worker-node> --ignore-daemonsets --delete-emptydir-data

# Watch pods move to other nodes
kubectl get pods -o wide

# Uncordon the node
kubectl uncordon <worker-node>

# Cleanup
kubectl delete deployment drain-test
```

### Вправа 4: Управління токенами kubeadm (Ціль: 3 хвилини)

```bash
# List existing tokens
kubeadm token list

# Create a new token
kubeadm token create

# Create token with specific TTL
kubeadm token create --ttl 2h

# Generate full join command
kubeadm token create --print-join-command

# Delete a token
kubeadm token delete <token-id>
```

### Вправа 5: Дослідження статичних Подів (Ціль: 5 хвилин)

```bash
# Find static pod manifest directory
cat /var/lib/kubelet/config.yaml | grep staticPodPath
# Usually: /etc/kubernetes/manifests

# List static pod manifests
ls -la /etc/kubernetes/manifests/

# View one manifest
cat /etc/kubernetes/manifests/kube-apiserver.yaml | head -30

# Create your own static pod
cat << 'EOF' | sudo tee /etc/kubernetes/manifests/my-static-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-static-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
EOF

# Wait and verify (will have node name suffix)
sleep 10
kubectl get pods | grep my-static-pod

# Remove static pod
sudo rm /etc/kubernetes/manifests/my-static-pod.yaml
```

### Вправа 6: Перевірка сертифікатів (Ціль: 5 хвилин)

```bash
# Check certificate expiration (on control plane)
kubeadm certs check-expiration

# View certificate details
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | head -30

# Check all certificates
ls -la /etc/kubernetes/pki/

# Check CA certificate
openssl x509 -in /etc/kubernetes/pki/ca.crt -text -noout | grep -E "Subject:|Issuer:|Not"
```

### Вправа 7: Усунення неполадок — Вузол NotReady (Ціль: 5 хвилин)

```bash
# Simulate: Stop kubelet on a worker
# (Run on worker node)
sudo systemctl stop kubelet

# On control plane, diagnose
kubectl get nodes  # Shows NotReady
kubectl describe node <worker> | grep -A10 Conditions

# Check what's happening
kubectl get events --field-selector involvedObject.kind=Node

# Fix: Restart kubelet (on worker)
sudo systemctl start kubelet

# Verify recovery
kubectl get nodes -w
```

### Вправа 8: Виклик — Робочий процес обслуговування вузла

Виконайте повний робочий процес обслуговування:

1. Позначте вузол як недоступний для планування (cordon)
2. Виведіть усі навантаження (drain)
3. Симулюйте обслуговування (зачекайте 30 секунд)
4. Поверніть вузол у роботу (uncordon)
5. Переконайтеся, що Поди знову можуть плануватися

```bash
# YOUR TASK: Complete this without looking at solution
NODE_NAME=<your-worker-node>
kubectl create deployment maint-test --image=nginx --replicas=2

# Start timer - Target: 3 minutes total
```

<details>
<summary>Відповідь</summary>

```bash
NODE_NAME=worker-01  # Replace with your node

# 1. Cordon
kubectl cordon $NODE_NAME

# 2. Drain
kubectl drain $NODE_NAME --ignore-daemonsets --delete-emptydir-data

# 3. Verify pods moved
kubectl get pods -o wide

# 4. Simulate maintenance
echo "Performing maintenance..."
sleep 30

# 5. Uncordon
kubectl uncordon $NODE_NAME

# 6. Verify scheduling works
kubectl scale deployment maint-test --replicas=4
kubectl get pods -o wide  # Some should land on $NODE_NAME

# Cleanup
kubectl delete deployment maint-test
```

</details>

---

## Підсумок: Частина 1 завершена!

Вітаємо! Ви завершили **Частину 1: Архітектура кластера, встановлення та конфігурація**.

Тепер ви розумієте:
- Компоненти площини управління та як вони взаємодіють
- Інтерфейси розширення: CNI, CSI, CRI
- Helm для управління пакетами
- Kustomize для управління конфігурацією
- CRDs та Operators для розширення Kubernetes
- RBAC для контролю доступу
- kubeadm для управління кластером

### Індекс модулів Частини 1

Швидкі посилання для повторення:

| Модуль | Тема | Ключові навички |
|--------|------|----------------|
| [1.1](module-1.1-control-plane/) | Глибоке занурення в площину управління | Ролі компонентів, усунення неполадок, статичні Поди |
| [1.2](module-1.2-extension-interfaces/) | Інтерфейси розширення | CNI/CSI/CRI, crictl, усунення неполадок плагінів |
| [1.3](module-1.3-helm/) | Helm | Встановлення, оновлення, відкат, values |
| [1.4](module-1.4-kustomize/) | Kustomize | Base/overlay, патчі, `kubectl -k` |
| [1.5](module-1.5-crds-operators/) | CRDs та Operators | Створення CRDs, управління користувацькими ресурсами |
| [1.6](module-1.6-rbac/) | RBAC | Roles, bindings, ServiceAccounts, `can-i` |
| [1.7](module-1.7-kubeadm/) | Основи kubeadm | Init, join, cordon, drain, токени |

**Перед тим як рухатися далі**: Пройдіть [Кумулятивний тест Частини 1](part1-cumulative-quiz/), щоб перевірити засвоєння матеріалу.

---

## Наступні кроки

Переходьте до [Частини 2: Навантаження та планування](../part2-workloads-scheduling/) — Навчіться розгортати та управляти застосунками.

Ця частина охоплює 15% іспиту і безпосередньо базується на тому, що ви вивчили про архітектуру кластера.
