---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 1: \u0412\u0430\u0448 \u043f\u0435\u0440\u0448\u0438\u0439 \u043a\u043b\u0430\u0441\u0442\u0435\u0440"
sidebar:
  order: 2
---
> **Складність**: `[MEDIUM]` — потрібне практичне налаштування
>
> **Час на виконання**: 30–40 хвилин
>
> **Передумови**: Встановлений Docker, пройдений Cloud Native 101

---

## Чому цей модуль важливий

Перш ніж вивчати Kubernetes, потрібен кластер Kubernetes. Цей модуль допоможе створити робочий локальний кластер за кілька хвилин, щоб одразу почати практикуватися.

Ми використаємо **kind** (Kubernetes in Docker) — це швидко, легко й ідеально для навчання.

---

## Варіанти кластерів

### Для навчання (локально)

| Інструмент | Переваги | Недоліки |
|------------|----------|----------|
| **kind** | Швидкий, легкий, підтримує кілька нод | Потребує Docker |
| **minikube** | Багато функцій, різні драйвери | Важчий, більше налаштувань |
| **k3d** | k3s у Docker, дуже швидкий | Дещо відрізняється від стандартного K8s |
| **Docker Desktop** | Просто, якщо вже маєте | Обмежена конфігурація |

### Для продакшену (керовані)

| Сервіс | Провайдер |
|---------|-----------|
| EKS | AWS |
| GKE | Google Cloud |
| AKS | Azure |

**Рекомендація**: Використовуйте **kind** для цього курсу. Він найкраще відповідає екзаменаційному середовищу.

---

## Встановлення kind

### macOS

```bash
# Using Homebrew
brew install kind

# Or download binary
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-darwin-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Linux

```bash
# Download binary
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Windows

```powershell
# Using Chocolatey
choco install kind

# Or download from:
# https://kind.sigs.k8s.io/dl/latest/kind-windows-amd64
```

### Перевірка встановлення

```bash
kind version
# kind v0.20.0 go1.20.4 darwin/amd64
```

---

## Встановлення kubectl

kubectl — це інструмент командного рядка для взаємодії з Kubernetes.

### macOS

```bash
# Using Homebrew
brew install kubectl

# Or download binary
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
```

### Linux

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
```

### Перевірка встановлення

```bash
kubectl version --client
# Client Version: v1.28.0
```

---

## Створення першого кластера

### Простий кластер з однією нодою

```bash
# Create cluster
kind create cluster

# Output:
# Creating cluster "kind" ...
#  ✓ Ensuring node image (kindest/node:v1.27.3) 🖼
#  ✓ Preparing nodes 📦
#  ✓ Writing configuration 📜
#  ✓ Starting control-plane 🕹️
#  ✓ Installing CNI 🔌
#  ✓ Installing StorageClass 💾
# Set kubectl context to "kind-kind"
```

### Перевірка роботи

```bash
# Check cluster info
kubectl cluster-info
# Kubernetes control plane is running at https://127.0.0.1:xxxxx

# List nodes
kubectl get nodes
# NAME                 STATUS   ROLES           AGE   VERSION
# kind-control-plane   Ready    control-plane   60s   v1.27.3

# Check all pods (system)
kubectl get pods -A
# Shows kube-system pods running
```

---

## Кластер із кількома нодами (за бажанням)

Для більш реалістичного тестування створіть кластер із кількома нодами:

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
```

```bash
# Create multi-node cluster
kind create cluster --config kind-config.yaml --name multi-node

# Verify
kubectl get nodes
# NAME                       STATUS   ROLES           AGE   VERSION
# multi-node-control-plane   Ready    control-plane   60s   v1.27.3
# multi-node-worker          Ready    <none>          30s   v1.27.3
# multi-node-worker2         Ready    <none>          30s   v1.27.3
```

---

## Керування кластерами

```bash
# List clusters
kind get clusters

# Delete cluster
kind delete cluster                    # Delete "kind" cluster
kind delete cluster --name multi-node  # Delete named cluster

# Get cluster kubeconfig
kind get kubeconfig --name kind

# Export kubeconfig (if needed)
kind export kubeconfig --name kind
```

---

## Що у вас тепер є

```
┌─────────────────────────────────────────────────────────────┐
│              ВАШ КЛАСТЕР KIND                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Docker-контейнер                        │   │
│  │              "kind-control-plane"                    │   │
│  │                                                     │   │
│  │    ┌───────────────────────────────────────────┐   │   │
│  │    │         Площина управління                │   │   │
│  │    │  ┌─────────┐ ┌──────────┐ ┌───────────┐  │   │   │
│  │    │  │   API   │ │Scheduler │ │Controller │  │   │   │
│  │    │  │ Server  │ │          │ │  Manager  │  │   │   │
│  │    │  └─────────┘ └──────────┘ └───────────┘  │   │   │
│  │    │           ┌──────────┐                    │   │   │
│  │    │           │   etcd   │                    │   │   │
│  │    │           └──────────┘                    │   │   │
│  │    └───────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │    ┌───────────────────────────────────────────┐   │   │
│  │    │         Робочий вузол (той самий контейнер)│   │   │
│  │    │  ┌─────────┐ ┌──────────┐                │   │   │
│  │    │  │ kubelet │ │Container │                │   │   │
│  │    │  │         │ │ Runtime  │                │   │   │
│  │    │  └─────────┘ └──────────┘                │   │   │
│  │    │                                           │   │   │
│  │    │  Ваші Поди працюватимуть тут              │   │   │
│  │    └───────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Увесь кластер K8s працює всередині одного Docker-         │
│  контейнера (або кількох — для кластера з кількома нодами) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Перші команди

Тепер, коли у вас є кластер, спробуйте ці команди:

```bash
# See what's running in the cluster
kubectl get pods -A

# Get more detail on nodes
kubectl describe node kind-control-plane

# Check component health (componentstatuses is deprecated; use this instead)
kubectl get --raw='/readyz?verbose'

# View cluster events
kubectl get events -A
```

---

## Усунення проблем

### "Cannot connect to the Docker daemon"

```bash
# Ensure Docker is running
docker info

# If using Docker Desktop, make sure it's started
```

### "kind: command not found"

```bash
# Verify kind is in PATH
which kind

# If not, add to PATH or reinstall
```

### "kubectl: connection refused"

```bash
# Ensure cluster is running
kind get clusters
docker ps  # Should show kind container

# Check kubeconfig context
kubectl config current-context
# Should show "kind-kind" or your cluster name
```

---

## Чи знали ви?

- **kind розшифровується як «Kubernetes in Docker».** Він запускає ноди K8s як Docker-контейнери замість віртуальних машин.

- **kind створили для тестування самого Kubernetes.** Проєкт K8s використовує його для тестування K8s. Він достатньо надійний для цього.

- **Кожна нода kind — це Docker-контейнер**, у якому працюють systemd, kubelet і containerd.

- **Кластери kind зберігаються між перезапусками Docker.** Ваш кластер переживе перезавантаження (якщо ви його не видалите).

---

## Тест

1. **Що таке kind?**
   <details>
   <summary>Відповідь</summary>
   Kind (Kubernetes in Docker) — це інструмент для запуску локальних кластерів Kubernetes, де Docker-контейнери використовуються як ноди. Він легкий, швидкий та ідеальний для розробки й навчання.
   </details>

2. **Яка команда створює кластер kind?**
   <details>
   <summary>Відповідь</summary>
   `kind create cluster` створює кластер з однією нодою. Прапорець `--config` з YAML-файлом дозволяє створювати кластери з кількома нодами. Прапорець `--name` задає власну назву кластера.
   </details>

3. **Як перевірити, що кластер працює?**
   <details>
   <summary>Відповідь</summary>
   Виконайте `kubectl get nodes`, щоб побачити ноди, `kubectl cluster-info` — для адрес кластера, або `kubectl get pods -A` — щоб побачити всі системні Поди.
   </details>

4. **Як видалити кластер kind?**
   <details>
   <summary>Відповідь</summary>
   `kind delete cluster` видаляє типовий кластер. Прапорець `--name назва-кластера` видаляє конкретний іменований кластер.
   </details>

---

## Практична вправа

**Завдання**: Створіть, перевірте та видаліть кластер.

```bash
# 1. Create a cluster
kind create cluster --name practice

# 2. Verify nodes are ready
kubectl get nodes

# 3. List all pods in cluster
kubectl get pods -A

# 4. View cluster info
kubectl cluster-info

# 5. Delete the cluster
kind delete cluster --name practice

# 6. Verify it's gone
kind get clusters
```

**Критерії успіху**: Усі команди виконуються без помилок.

---

## Підсумок

Тепер у вас є робочий кластер Kubernetes:

**Встановлені інструменти**:
- kind — створює локальні кластери K8s
- kubectl — CLI для взаємодії з K8s

**Ключові команди**:
- `kind create cluster` — створити кластер
- `kind delete cluster` — видалити кластер
- `kubectl get nodes` — перевірити кластер

Ви готові починати роботу з Kubernetes!

---

## Наступний модуль

[Модуль 2: Основи kubectl](module-1.2-kubectl-basics/) — ваш інтерфейс командного рядка до Kubernetes.
