---
title: "Модуль 1.2: Основи kubectl"
slug: uk/prerequisites/kubernetes-basics/module-1.2-kubectl-basics
sidebar:
  order: 3
lab:
  id: "prereq-k8s-1.2-kubectl"
  url: "https://killercoda.com/kubedojo/scenario/prereq-k8s-1.2-kubectl"
  duration: "30 хв"
  difficulty: "beginner"
  environment: "kubernetes"
en_commit: "68c548ea6c0f246cc6ac716524e04ddee5baeccc"
en_file: "src/content/docs/prerequisites/kubernetes-basics/module-1.2-kubectl-basics.md"
---

> **Складність**: `[СЕРЕДНЯ]` — Основні команди для опанування
>
> **Час на проходження**: 40-45 хвилин
>
> **Передумови**: Модуль 1 (Перший запущений кластер)

---

Уявіть, що о 3-й годині ночі спрацьовує пейджер. Основний сервіс оплати вашої компанії не працює, і щохвилини випаровуються тисячі доларів. У вас є термінал і лише один інструмент: `kubectl`. Якщо ви точно знаєте, як надіслати запит до кластера, отримати логи та знайти несправний Pod, ви — герой. Якщо ж ви порпаєтеся в документації, намагаючись згадати прапорець для фільтрації простору імен (namespace), аварія триває. `kubectl` — це не просто CLI-інструмент; це ваша центральна нервова система для спілкування з Kubernetes.

## Що ви зможете зробити

Після завершення цього модуля ви зможете:
- **Орієнтуватися** в ресурсах Kubernetes за допомогою `kubectl get`, `kubectl describe` та `kubectl explain`
- **Створювати** ресурси як імперативно (швидкими командами), так і декларативно (через YAML-файли)
- **Налагоджувати** проблеми з ресурсами, використовуючи події `kubectl describe` та логи `kubectl logs`
- **Використовувати** форматування виводу (`-o wide`, `-o yaml`, `-o json`), щоб отримати необхідну інформацію

---

## Чому це важливо

kubectl — це ваш основний інтерфейс для роботи з Kubernetes. Кожна взаємодія — створення ресурсів, налагодження проблем, перевірка статусу — проходить через kubectl. Опанування цього інструменту є критично важливим як для щоденної роботи, так і для складання сертифікаційних іспитів.

**Збій через «неправильний контекст» (Реальна історія)**
У 2019 році відомий фінтех-стартап (назва прихована) пережив катастрофічний 45-хвилинний збій, який коштував приблизно 120 000 доларів втрачених транзакцій. Причиною була не складна мережева помилка чи вразливість нульового дня. Досвідчений інженер, маючи намір очистити ресурси в середовищі розробки (staging), виконав команду `kubectl delete namespace payments`. На жаль, його контекст `kubectl` все ще був налаштований на production. Оскільки `kubectl` виконує саме те, що ви йому кажете, щодо поточного активного контексту без жодної системи захисту, весь рівень маршрутизації платежів у production був миттєво видалений. Ось чому опанування керування контекстами `kubectl`, використання тестових запусків (dry-runs) та обережне виконання команд — це не лише про швидкість, а й про виживання.

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

> **Зупиніться та подумайте**: Якщо `kubectl get pods` виводить список Pod-ів, то яка команда, на вашу думку, виводить список вузлів (nodes), з яких складається ваш кластер?

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

> **Зупиніться та подумайте**: Що станеться, якщо ви запустите `kubectl apply -f .` у директорії, де є як коректні YAML-файли Kubernetes, так і звичайний текстовий файл `README.md`? (Він спробує застосувати все, видасть помилку на README, але все одно успішно застосує коректні YAML-файли).

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

> **Бонус: Синтаксис для досвідчених користувачів** (поверніться до цього, коли освоїте базу)
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

## Робота з просторами імен (Namespaces)

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
│  │ Ваш термінал    │                                       │
│  │ $ kubectl ...   │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ ~/.kube/config  │  ← Облікові дані, інформація про кластер│
│  │ (kubeconfig)    │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼  HTTPS                                         │
│  ┌─────────────────┐                                       │
│  │   API Server    │  ← Перевіряє, обробляє                │
│  │ (K8s кластер)   │                                       │
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

### Аліаси для оболонки (додайте в ~/.bashrc або ~/.zshrc)

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

## Шпаргалка

| Дія | Команда |
|:---|:---|
| Показати Pod-и | `kubectl get pods` |
| Усі простори імен | `kubectl get pods -A` |
| Детальна інформація | `kubectl describe pod NAME` |
| Переглянути логи | `kubectl logs NAME` |
| Доступ до оболонки | `kubectl exec -it NAME -- bash` |
| Прокидання портів | `kubectl port-forward pod/NAME 8080:80` |
| Створити з файлу | `kubectl apply -f file.yaml` |
| Видалити | `kubectl delete pod NAME` |
| Згенерувати YAML | `kubectl run NAME --image=IMG --dry-run=client -o yaml` |

---

## Практичні поради з передової

- **kubectl спілкується з API-сервером через HTTPS.** Усі команди — це виклики API. Ви могли б використовувати `curl` замість нього (але навіщо?).

- **`-o yaml` — це справжній скарб.** Отримайте будь-який ресурс у форматі YAML, змініть його та застосуйте назад. Це швидше, ніж писати з нуля.

- **`--dry-run=client -o yaml` генерує шаблони.** Ніколи не зазубрюйте структуру YAML — генеруйте її.

- **kubectl має вбудовану довідку.** `kubectl explain pod.spec.containers` показує документацію по полях.

---

## Типові помилки

| Помилка | Рішення |
|:---|:---|
| Забутий простір імен | Використовуйте `-n namespace` або встановіть його за замовчуванням |
| Неправильний контекст | Перевіряйте `kubectl config current-context` перед виконанням |
| Опичатки в назвах ресурсів | Використовуйте клавішу Tab для автодоповнення назв |
| Відсутність `-o yaml` для шаблонів | Завжди генеруйте шаблони через dry-run, не вчіть їх напам'ять |
| Використання `create` замість `apply` | `apply` є ідемпотентним і коректно обробляє оновлення, віддавайте перевагу йому |
| Видалення Pod-а замість його батьківського ресурсу | ReplicaSet миттєво створить Pod заново. Натомість видаляйте Deployment. |
| Забагато інформації в `kubectl get events` | Використовуйте `--sort-by='.metadata.creationTimestamp'` для хронології |
| Спроба змінити незмінні поля | Згенеруйте YAML, видаліть ресурс і застосуйте новий YAML замість `kubectl edit` |

---

## Контрольні запитання

1. **Вам повідомили, що Pod `payment-processor` постійно перезавантажується (crash-looping) у просторі імен `finance`. Вам потрібно переглянути логи попереднього екземпляра контейнера, щоб зрозуміти причину падіння. Яку команду ви виконаєте?**
   <details>
   <summary>Відповідь</summary>
   `kubectl logs payment-processor -n finance --previous`

   *Чому?* Прапорець `--previous` (або `-p`) є критично важливим для налагодження помилок CrashLoopBackOff. За замовчуванням `kubectl logs` показує логи лише того контейнера, що працює зараз. Коли контейнер падає і перезапускається, поточні логи можуть бути порожніми. `--previous` витягує логи з «мертвого» контейнера перед самим виходом.
   </details>

2. **Ви пишете скрипт для моніторингу IP-адрес усіх запущених Pod-ів у кластері, але вам потрібні лише чисті IP-адреси без заголовків чи зайвих колонок. Як витягнути саме це поле?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get pods -o jsonpath='{.items[*].status.podIP}'`

   *Чому?* Хоча `-o wide` показує IP-адресу, він включає заголовки, які важко розпарсити скриптом. `jsonpath` дозволяє орієнтуватися в структурі JSON відповіді API та витягувати саме потрібні дані.
   </details>

3. **Розробник просить вас оновити Deployment, щоб використовувати новий тег образу (`v2.1.0`). У нього немає оригінального YAML-файлу, і вам потрібно зробити це швидко, не ризикуючи допустити помилку в ручному сеансі `kubectl edit`. Яка найбезпечніша імперативна команда?**
   <details>
   <summary>Відповідь</summary>
   `kubectl set image deployment/myapp myapp=nginx:v2.1.0`

   *Чому?* Використання `kubectl set image` безпечніше за `kubectl edit`, бо виконує цільове атомарне оновлення без відкриття текстового редактора, де можна випадково змінити інші рядки.
   </details>

4. **Ви створили YAML-файл `app.yaml` і застосували його, але Pod поводиться некоректно і застряг у стані Pending. Ви хочете переглянути детальні події, пов'язані з цим конкретним Pod-ом. Що ви зробите?**
   <details>
   <summary>Відповідь</summary>
   `kubectl describe pod <pod-name>`

   *Чому?* Команда `kubectl describe` збирає дані з кількох кінцевих точок API, зокрема події кластера (Events). Якщо Pod застряг у `Pending` або `ImagePullBackOff`, `get` не скаже чому, а `describe` покаже конкретну скаргу планувальника (scheduler) або kubelet.
   </details>

5. **Ваша команда переходить на декларативний робочий процес GitOps. Вам потрібно створити складний Deployment, але ви хочете уникнути написання YAML з нуля, щоб не помилитися з відступами. Як змусити `kubectl` написати «скелет» за вас?**
   <details>
   <summary>Відповідь</summary>
   `kubectl create deployment myapp --image=nginx --dry-run=client -o yaml > myapp.yaml`

   *Чому?* Комбінація `--dry-run=client` та `-o yaml` — це ультимативний чит-код. Клієнт обробляє команду і форматує запит як YAML, але не відправляє його на сервер.
   </details>

6. **Ви розслідуєте проблему продуктивності й вам потрібно виконати інструмент діагностики мережі (`curl`) зсередини існуючого запущеного Pod-а з назвою `api-backend`. Як потрапити в інтерактивну оболонку всередині цього Pod-а?**
   <details>
   <summary>Відповідь</summary>
   `kubectl exec -it api-backend -- sh`

   *Чому?* Команда `kubectl exec` працює аналогічно до `docker exec`. Прапорці `-i` (інтерактивність) та `-t` (tty) виділяють термінальну сесію, щоб ви могли вводити команди й бачити результат у реальному часі.
   </details>

7. **Ви працюєте з двома різними кластерами: `dev-cluster` та `prod-cluster`. Ви хочете перевірити, на який кластер зараз вказують ваші команди `kubectl`, перш ніж випадково видалити критичний ресурс. Як це перевірити?**
   <details>
   <summary>Відповідь</summary>
   `kubectl config current-context`

   *Чому?* Файл `~/.kube/config` може містити дані для десятків кластерів. «Контекст» визначає, з яким кластером і користувачем спілкується `kubectl`. Перевірка контексту має стати м'язовою пам'яттю перед деструктивними командами.
   </details>

8. **Ви помітили, що Pod `cache-worker` зовсім не відповідає і застряг у стані `Terminating` понад 30 хвилин. Звичайні команди видалення просто «висять». Як примусово видалити його з API-сервера?**
   <details>
   <summary>Відповідь</summary>
   `kubectl delete pod cache-worker --force --grace-period=0`

   *Чому?* Іноді kubelet на вузлі втрачає зв'язок, залишаючи Pod у стані `Terminating`. Параметр `--grace-period=0` каже Kubernetes не чекати коректного завершення, а `--force` негайно видаляє об'єкт з бази даних API-сервера.
   </details>

---

## Практична вправа

**Завдання**: Попрактикуйтеся в основних командах kubectl.

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

**Критерії успіху**:
- [ ] Ви успішно створили новий простір імен `practice`.
- [ ] Ви розгорнули Pod `nginx` у просторі імен `practice`.
- [ ] Ви підтвердили, що Pod працює, вивівши список Pod-ів.
- [ ] Ви успішно отримали детальну інформацію за допомогою `describe`.
- [ ] Ви отримали логи запущеного контейнера.
- [ ] Ви виконали команду всередині контейнера і побачили результат.
- [ ] Ви вивели YAML-визначення Pod-а в термінал.
- [ ] Ви чисто видалили простір імен та весь його вміст.

---

## Підсумок

Основні команди kubectl:

**Інформація**:
- `kubectl get` — Список ресурсів
- `kubectl describe` — Детальна інформація
- `kubectl logs` — Вивід контейнера

**Створення**:
- `kubectl apply -f` — Створити/оновити з файлу
- `kubectl run` — Швидке створення Pod-а
- `kubectl create` — Створення ресурсів

**Зміна**:
- `kubectl edit` — Редагувати ресурс «наживо»
- `kubectl scale` — Змінити кількість реплік
- `kubectl delete` — Видалити ресурси

**Налагодження**:
- `kubectl exec` — Виконати команду в контейнері
- `kubectl port-forward` — Локальний доступ
- `kubectl logs` — Перегляд виводу

---

## Наступний модуль

[Модуль 1.3: Pods](../module-1.3-pods/) — атомарна одиниця Kubernetes.