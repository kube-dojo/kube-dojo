---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2: \u041e\u0441\u043d\u043e\u0432\u0438 kubectl"
sidebar:
  order: 3
---
> **Складність**: `[MEDIUM]` — Основні команди, які потрібно опанувати
>
> **Час на виконання**: 40–45 хвилин
>
> **Передумови**: Модуль 1 (Перший кластер запущено)

---

## Чому цей модуль важливий

kubectl — це ваш основний інтерфейс до Kubernetes. Кожна взаємодія — створення ресурсів, налагодження проблем, перевірка статусу — відбувається через kubectl. Опанування цього інструменту є необхідним як для щоденної роботи, так і для сертифікаційних іспитів.

---

## Структура команди kubectl

```
kubectl [command] [TYPE] [NAME] [flags]

Examples:
kubectl get pods                    # List all pods
kubectl get pod nginx              # Get specific pod
kubectl get pods -o wide           # More output columns
kubectl describe pod nginx         # Detailed info
kubectl delete pod nginx           # Delete resource
```

---

## Основні команди

### Отримання інформації

```bash
# List resources
kubectl get pods                   # Pods in current namespace
kubectl get pods -A                # Pods in all namespaces
kubectl get pods -n kube-system    # Pods in specific namespace
kubectl get pods -o wide           # More columns (node, IP)
kubectl get pods -o yaml           # Full YAML output
kubectl get pods -o json           # JSON output

# Common resource types
kubectl get nodes                  # Cluster nodes
kubectl get deployments           # Deployments
kubectl get services              # Services
kubectl get all                   # Common resources
kubectl get events                # Cluster events

# Describe (detailed info)
kubectl describe pod nginx
kubectl describe node kind-control-plane
kubectl describe deployment myapp
```

### Створення ресурсів

```bash
# From YAML file
kubectl apply -f pod.yaml
kubectl apply -f .                  # All YAML files in directory
kubectl apply -f https://example.com/resource.yaml  # From URL

# Imperatively (quick creation)
kubectl run nginx --image=nginx
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80

# Generate YAML without creating
kubectl run nginx --image=nginx --dry-run=client -o yaml
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml
```

### Зміна ресурсів

```bash
# Apply changes
kubectl apply -f updated-pod.yaml

# Edit live resource
kubectl edit deployment nginx

# Patch resource
kubectl patch deployment nginx -p '{"spec":{"replicas":3}}'

# Scale
kubectl scale deployment nginx --replicas=5

# Set image
kubectl set image deployment/nginx nginx=nginx:1.25
```

### Видалення ресурсів

```bash
# Delete by name
kubectl delete pod nginx
kubectl delete deployment nginx

# Delete from file
kubectl delete -f pod.yaml

# Delete all of a type
kubectl delete pods --all
kubectl delete pods --all -n my-namespace

# Force delete (stuck pods)
kubectl delete pod nginx --force --grace-period=0
```

---

## Формати виводу

```bash
# Default (table)
kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   0          5m

# Wide (more columns)
kubectl get pods -o wide
# NAME    READY   STATUS    RESTARTS   AGE   IP           NODE
# nginx   1/1     Running   0          5m    10.244.0.5   kind-control-plane

# YAML
kubectl get pod nginx -o yaml

# JSON
kubectl get pod nginx -o json

```

> **Бонус: Синтаксис для досвідчених** (поверніться до цього, коли освоїте основи)
>
> ```bash
> # Custom columns (great for dashboards)
> kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase
>
> # JSONPath (extract specific fields — exam gold!)
> kubectl get pod nginx -o jsonpath='{.status.podIP}'
> kubectl get pods -o jsonpath='{.items[*].metadata.name}'
> ```

---

## Робота з просторами імен

```bash
# List namespaces
kubectl get namespaces
kubectl get ns

# Set default namespace
kubectl config set-context --current --namespace=my-namespace

# Create namespace
kubectl create namespace my-namespace

# Run command in specific namespace
kubectl get pods -n kube-system
kubectl get pods --namespace=my-namespace

# All namespaces
kubectl get pods -A
kubectl get pods --all-namespaces
```

---

## Команди для налагодження

```bash
# View logs
kubectl logs nginx                  # Current logs
kubectl logs nginx -f               # Follow (stream) logs
kubectl logs nginx --tail=100       # Last 100 lines
kubectl logs nginx -c container1    # Specific container
kubectl logs nginx --previous       # Previous instance logs

# Execute command in container
kubectl exec nginx -- ls /          # Run command
kubectl exec -it nginx -- bash      # Interactive shell
kubectl exec -it nginx -- sh        # If bash not available

# Port forwarding
kubectl port-forward pod/nginx 8080:80
kubectl port-forward svc/nginx 8080:80
# Access at localhost:8080

# Copy files
kubectl cp nginx:/etc/nginx/nginx.conf ./nginx.conf
kubectl cp ./local-file.txt nginx:/tmp/
```

---

## Корисні прапорці

```bash
# Watch (auto-refresh)
kubectl get pods -w
kubectl get pods --watch

# Labels and selectors
kubectl get pods -l app=nginx
kubectl get pods --selector=app=nginx,tier=frontend

# Sort output
kubectl get pods --sort-by=.metadata.creationTimestamp
kubectl get pods --sort-by=.status.startTime

# Field selectors
kubectl get pods --field-selector=status.phase=Running
kubectl get pods --field-selector=spec.nodeName=kind-control-plane

# Show labels
kubectl get pods --show-labels

# Output to file
kubectl get pod nginx -o yaml > pod.yaml
```

---

## Конфігурація та контекст

```bash
# View current config
kubectl config view
kubectl config current-context

# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context kind-kind
kubectl config use-context my-cluster

# Set default namespace for context
kubectl config set-context --current --namespace=default
```

---

## Візуалізація: Як працює kubectl

```
┌─────────────────────────────────────────────────────────────┐
│              ЯК ПРАЦЮЄ kubectl                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │   Ваш термінал  │                                       │
│  │   $ kubectl ... │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │   ~/.kube/config│  ← Облікові дані, інфо про кластер   │
│  │   (kubeconfig)  │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼  HTTPS                                         │
│  ┌─────────────────┐                                       │
│  │   API Server    │  ← Валідує, обробляє                  │
│  │   (K8s кластер) │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │    Відповідь    │  ← YAML/JSON/Таблиця                  │
│  │                 │                                       │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Корисні скорочення

### Аліаси оболонки (додайте до ~/.bashrc або ~/.zshrc)

```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kaf='kubectl apply -f'
alias kdel='kubectl delete'
alias klog='kubectl logs'
alias kexec='kubectl exec -it'
```

### Автодоповнення kubectl

```bash
# Bash
source <(kubectl completion bash)
echo 'source <(kubectl completion bash)' >> ~/.bashrc

# Zsh
source <(kubectl completion zsh)
echo 'source <(kubectl completion zsh)' >> ~/.zshrc

# With alias
complete -F __start_kubectl k  # Bash
compdef k=kubectl              # Zsh
```

---

## Коротка довідка

| Дія | Команда |
|-----|---------|
| Список подів | `kubectl get pods` |
| Всі простори імен | `kubectl get pods -A` |
| Детальна інформація | `kubectl describe pod NAME` |
| Перегляд логів | `kubectl logs NAME` |
| Доступ до оболонки | `kubectl exec -it NAME -- bash` |
| Перенаправлення порту | `kubectl port-forward pod/NAME 8080:80` |
| Створити з файлу | `kubectl apply -f file.yaml` |
| Видалити | `kubectl delete pod NAME` |
| Згенерувати YAML | `kubectl run NAME --image=IMG --dry-run=client -o yaml` |

---

## Чи знали ви?

- **kubectl спілкується з API-сервером через HTTPS.** Всі команди — це API-виклики. Ви могли б використовувати `curl` замість цього (але навіщо?).

- **`-o yaml` — це золото на іспиті.** Отримайте будь-який ресурс у форматі YAML, змініть його, застосуйте назад. Швидше, ніж писати з нуля.

- **`--dry-run=client -o yaml` генерує шаблони.** Ніколи не запам'ятовуйте структуру YAML — генеруйте її.

- **kubectl має вбудовану довідку.** `kubectl explain pod.spec.containers` показує документацію полів.

---

## Типові помилки

| Помилка | Рішення |
|---------|---------|
| Забули вказати простір імен | Використовуйте `-n namespace` або встановіть типовий |
| Неправильний контекст | `kubectl config use-context` |
| Друкарські помилки в назвах ресурсів | Використовуйте автодоповнення табуляцією |
| Не використовуєте `-o yaml` для шаблонів | Завжди генеруйте, не запам'ятовуйте |
| Використовуєте `create` замість `apply` | `apply` є ідемпотентним, надавайте йому перевагу |

---

## Тест

1. **Як переглянути всі поди у всіх просторах імен?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get pods -A` або `kubectl get pods --all-namespaces`
   </details>

2. **Як згенерувати YAML для пода без його створення?**
   <details>
   <summary>Відповідь</summary>
   `kubectl run nginx --image=nginx --dry-run=client -o yaml`
   </details>

3. **Як отримати інтерактивну оболонку у запущеному контейнері?**
   <details>
   <summary>Відповідь</summary>
   `kubectl exec -it POD_NAME -- bash` (або `-- sh`, якщо bash недоступний)
   </details>

4. **Як стежити за логами в реальному часі?**
   <details>
   <summary>Відповідь</summary>
   `kubectl logs POD_NAME -f` або `kubectl logs POD_NAME --follow`
   </details>

---

## Практична вправа

**Завдання**: Практика основних команд kubectl.

```bash
# 1. Create a namespace
kubectl create namespace practice

# 2. Run a pod in that namespace
kubectl run nginx --image=nginx -n practice

# 3. List pods in the namespace
kubectl get pods -n practice

# 4. Get detailed info
kubectl describe pod nginx -n practice

# 5. View logs
kubectl logs nginx -n practice

# 6. Execute a command
kubectl exec nginx -n practice -- nginx -v

# 7. Get YAML output
kubectl get pod nginx -n practice -o yaml

# 8. Delete everything
kubectl delete namespace practice
```

**Критерії успіху**: Всі команди виконуються без помилок.

---

## Підсумок

Основні команди kubectl:

**Інформація**:
- `kubectl get` — Список ресурсів
- `kubectl describe` — Детальна інформація
- `kubectl logs` — Вивід контейнера

**Створення**:
- `kubectl apply -f` — Створити/оновити з файлу
- `kubectl run` — Швидке створення пода
- `kubectl create` — Створення ресурсів

**Зміна**:
- `kubectl edit` — Редагувати активний ресурс
- `kubectl scale` — Змінити кількість реплік
- `kubectl delete` — Видалити ресурси

**Налагодження**:
- `kubectl exec` — Виконати команди в контейнері
- `kubectl port-forward` — Локальний доступ
- `kubectl logs` — Переглянути вивід

---

## Наступний модуль

[Модуль 3: Поди](module-1.3-pods/) — Атомарна одиниця Kubernetes.
