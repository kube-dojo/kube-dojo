---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 0.2: \u041c\u0430\u0439\u0441\u0442\u0435\u0440\u043d\u0456\u0441\u0442\u044c \u0440\u043e\u0431\u043e\u0442\u0438 \u0437 \u0442\u0435\u0440\u043c\u0456\u043d\u0430\u043b\u043e\u043c"
slug: uk/k8s/cka/part0-environment/module-0.2-shell-mastery
sidebar: 
  order: 2
lab: 
  id: cka-0.2-shell-mastery
  url: https://killercoda.com/kubedojo/scenario/cka-0.2-shell-mastery
  duration: "30 min"
  difficulty: intermediate
  environment: ubuntu
---
> **Складність**: `[QUICK]` — Налаштуйте один раз, користуйтесь завжди
>
> **Час на виконання**: 15-20 хвилин
>
> **Передумови**: Модуль 0.1 (працюючий кластер)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Налаштувати** аліаси kubectl та bash completion, щоб зекономити 5-10 хвилин на іспиті CKA
- **Використовувати** комбінації клавіш оболонки (Ctrl+R, `!!`, tab completion), щоб не набирати команди повторно
- **Створити** персональну конфігурацію `.bashrc`, що прискорює роботу з kubectl у 3 рази
- **Відновити** роботу після помилок в оболонці за допомогою пошуку по історії та редагування команд

---

## Чому цей модуль важливий

На іспиті CKA у вас приблизно **7 хвилин на питання в середньому**. Кожне натискання клавіші має значення. Різниця між набором `kubectl get pods --all-namespaces` і `k get po -A` невелика, але помножте це на 50+ команд kubectl — і ви заощадите 5-10 хвилин.

5-10 хвилин — це ціле питання. А може й два.

Цей модуль налаштує ваш термінал для максимальної швидкості.

> **Аналогія з піт-стопом Формули 1**
>
> У Формулі 1 піт-стопи вигрують або програють за частки секунди. Команда не імпровізує — кожен рух відрепетирований, кожен інструмент на своєму місці, кожна дія доведена до автоматизму. Налаштування вашого терміналу — це ваша піт-команда. Аліаси — це ваші заздалегідь підготовлені інструменти. Автодоповнення — це ваша натренована м'язова пам'ять. Без підготовки ви метушитесь. З нею — ви міняєте шини за 2 секунди, поки інші ще шукають ключ.

---

## Що ви налаштуєте

```
До:    kubectl get pods --namespace kube-system --output wide
Після: k get po -n kube-system -o wide

До:    kubectl describe pod nginx-deployment-abc123
Після: k describe po nginx<TAB>  → автодоповнення повної назви

До:    kubectl config use-context production-cluster
Після: kx production<TAB>  → перемикання контексту з автодоповненням
```

---

## Частина 1: Автодоповнення kubectl

Це **обов'язково**. Автодоповнення економить більше часу, ніж будь-який аліас.

### 1.1 Увімкнення Bash Completion

```bash
# Install bash-completion if not present
sudo apt-get install -y bash-completion

# Enable kubectl completion
echo 'source <(kubectl completion bash)' >> ~/.bashrc

# Apply now
source ~/.bashrc
```

### 1.2 Перевірка автодоповнення

```bash
kubectl get <TAB><TAB>
```

Ви маєте побачити список ресурсів (pods, deployments, services тощо).

```bash
kubectl get pods -n kube<TAB>
```

Має автодоповнитись до `kube-system`.

```bash
kubectl describe pod cal<TAB>
```

Має автодоповнитись до повної назви Поду Calico.

> **Чи знали ви?**
>
> Середовище іспиту CKA має попередньо встановлене bash completion. Але якщо ви практикуєтесь без нього, ви набудете погані звички (запам'ятовування повних назв ресурсів, ручний набір усього). Завжди практикуйтесь з увімкненим автодоповненням.

---

## Частина 2: Основні аліаси

### 2.1 Головний аліас

```bash
# The most important alias
echo 'alias k=kubectl' >> ~/.bashrc

# Enable completion for the alias too
echo 'complete -o default -F __start_kubectl k' >> ~/.bashrc

source ~/.bashrc
```

Тепер `k get pods` працює так само як `kubectl get pods`, з повним автодоповненням.

### 2.2 Скорочення типів ресурсів

kubectl вже підтримує скорочені назви. Запам'ятайте їх:

| Повна назва | Скорочення | Приклад |
|-----------|-------|---------|
| pods | po | `k get po` |
| deployments | deploy | `k get deploy` |
| services | svc | `k get svc` |
| namespaces | ns | `k get ns` |
| nodes | no | `k get no` |
| configmaps | cm | `k get cm` |
| secrets | (немає) | `k get secrets` |
| persistentvolumes | pv | `k get pv` |
| persistentvolumeclaims | pvc | `k get pvc` |
| serviceaccounts | sa | `k get sa` |
| replicasets | rs | `k get rs` |
| daemonsets | ds | `k get ds` |
| statefulsets | sts | `k get sts` |
| ingresses | ing | `k get ing` |
| networkpolicies | netpol | `k get netpol` |
| storageclasses | sc | `k get sc` |

Це не аліаси — вони вбудовані в kubectl. Використовуйте їх.

### 2.3 Рекомендовані додаткові аліаси

Додайте до вашого `~/.bashrc`:

```bash
# Faster common operations
alias kgp='kubectl get pods'
alias kgpa='kubectl get pods -A'
alias kgs='kubectl get svc'
alias kgn='kubectl get nodes'
alias kgd='kubectl get deploy'

# Describe shortcuts
alias kdp='kubectl describe pod'
alias kds='kubectl describe svc'
alias kdn='kubectl describe node'

# Logs
alias kl='kubectl logs'
alias klf='kubectl logs -f'

# Apply/Delete
alias ka='kubectl apply -f'
alias kd='kubectl delete -f'

# Context and namespace
alias kx='kubectl config use-context'
alias kn='kubectl config set-context --current --namespace'

# Quick debug pod
alias krun='kubectl run debug --image=busybox --rm -it --restart=Never --'
```

### 2.4 Застосування всіх аліасів

```bash
source ~/.bashrc
```

---

## Частина 3: Перемикання контексту та простору імен

На іспиті CKA використовуються **декілька кластерів**. Вам доведеться постійно перемикати контексти.

> **Бойова історія: Помилка на $15,000**
>
> DevOps-інженер хотів видалити тестовий простір імен у staging-кластері. Він набрав `kubectl delete ns payment-service` і натиснув Enter. А потім відчув, як серце завмерло — він був у production-контексті. 47 Подів, що обслуговували реальних клієнтів, зникли. Відновлення тривало 3 години. Рішення? Тепер він налаштував `PS1` так, щоб показувати поточний контекст у командному рядку, виділений червоним, коли це production. Контекстна обізнаність — це не опція, це виживання.

### 3.1 Розуміння контекстів

```bash
# List all contexts
kubectl config get-contexts

# See current context
kubectl config current-context

# Switch context
kubectl config use-context <context-name>
```

### 3.2 Швидке перемикання контексту

З аліасом `kx`:

```bash
kx prod<TAB>     # Autocompletes to production-context
kx staging<TAB>  # Autocompletes to staging-context
```

### 3.3 Перемикання простору імен

Замість того, щоб щоразу набирати `-n namespace`:

```bash
# Set default namespace for current context
kn kube-system

# Now all commands default to kube-system
k get po  # Shows kube-system pods

# Switch back to default
kn default
```

> **Увага: Неправильний кластер**
>
> Помилка №1 на іспиті — розв'язання задач у неправильному кластері. Кожне питання вказує контекст. **Завжди перемикайте контекст першим.** Доведіть це до автоматизму:
> 1. Прочитайте питання
> 2. Перемкніть контекст
> 3. Потім розв'язуйте

---

## Частина 4: Змінні середовища

### 4.1 Скорочення для Dry-Run

Ви будете постійно генерувати YAML-шаблони:

```bash
export do='--dry-run=client -o yaml'

# Usage
k run nginx --image=nginx $do > pod.yaml
k create deploy nginx --image=nginx $do > deploy.yaml
k expose deploy nginx --port=80 $do > svc.yaml
```

### 4.2 Примусове видалення (використовуйте обережно)

```bash
export now='--force --grace-period=0'

# Usage (when you need instant deletion)
k delete po nginx $now
```

### 4.3 Додавання до .bashrc

```bash
echo "export do='--dry-run=client -o yaml'" >> ~/.bashrc
echo "export now='--force --grace-period=0'" >> ~/.bashrc
source ~/.bashrc
```

---

## Частина 5: Повне налаштування .bashrc

Ось усе разом. Додайте до вашого `~/.bashrc`:

```bash
# ============================================
# Kubernetes CKA Exam Shell Configuration
# ============================================

# kubectl completion
source <(kubectl completion bash)

# Core alias
alias k=kubectl
complete -o default -F __start_kubectl k

# Get shortcuts
alias kgp='kubectl get pods'
alias kgpa='kubectl get pods -A'
alias kgs='kubectl get svc'
alias kgn='kubectl get nodes'
alias kgd='kubectl get deploy'
alias kgpv='kubectl get pv'
alias kgpvc='kubectl get pvc'

# Describe shortcuts
alias kdp='kubectl describe pod'
alias kds='kubectl describe svc'
alias kdn='kubectl describe node'
alias kdd='kubectl describe deploy'

# Logs
alias kl='kubectl logs'
alias klf='kubectl logs -f'

# Apply/Delete
alias ka='kubectl apply -f'
alias kd='kubectl delete -f'

# Context and namespace
alias kx='kubectl config use-context'
alias kn='kubectl config set-context --current --namespace'

# Quick debug
alias krun='kubectl run debug --image=busybox --rm -it --restart=Never --'

# Environment variables
export do='--dry-run=client -o yaml'
export now='--force --grace-period=0'

# ============================================
```

---

## Частина 6: Тест швидкості

Засікайте час на цих командах. Цільовий час у дужках.

### Без оптимізації
```bash
kubectl get pods --all-namespaces --output wide      # (5+ seconds typing)
kubectl describe pod <pod-name>                       # (3+ seconds + finding name)
kubectl config use-context production                 # (3+ seconds)
```

### З оптимізацією
```bash
k get po -A -o wide                                   # (<2 seconds)
kdp <TAB>                                             # (<1 second with autocomplete)
kx prod<TAB>                                          # (<1 second)
```

### Генерація YAML-шаблону
```bash
# Without
kubectl run nginx --image=nginx --dry-run=client -o yaml > nginx.yaml  # (6+ seconds)

# With
k run nginx --image=nginx $do > nginx.yaml                              # (<2 seconds)
```

---

## Чи знали ви?

- **Термінал іспиту має попередньо встановлене kubectl completion**, але ваших аліасів там не буде. Деякі кандидати запам'ятовують короткий скрипт налаштування аліасів, щоб набрати його на початку іспиту. Це займає 30 секунд і економить значно більше.

- **`kubectl explain`** — ваш найкращий друг. Замість пошуку в документації:
  ```bash
  k explain pod.spec.containers
  k explain deploy.spec.strategy
  ```
  Це працює офлайн і швидше за браузер.

- **Ви можете запустити `kubectl` з `--help` для будь-якої підкоманди**:
  ```bash
  k create --help
  k run --help
  k expose --help
  ```
  Приклади у виводі `--help` часто є саме тим, що вам потрібно.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|----------|
| Не використовувати автодоповнення | Повільно, друкарські помилки | Завжди `<TAB>` |
| Забувати `-A` для всіх просторів імен | Пропуск ресурсів | За замовчуванням використовуйте `-A` при пошуку |
| Набирати повні назви ресурсів | Повільно | Використовуйте скорочення: `po`, `svc`, `deploy` |
| Неправильний контекст | Робота в неправильному кластері | Завжди `kx` першим |
| Не використовувати `$do` | Ручний набір dry-run | Експортуйте змінну |

---

## Тест

1. **Що робить ця команда: `k get po -A -o wide`?**
   <details>
   <summary>Відповідь</summary>
   Виводить список усіх Подів у всіх просторах імен з розширеною інформацією (нода, IP тощо). `-A` — скорочення для `--all-namespaces`, `-o wide` показує додаткові стовпці.
   </details>

2. **Як швидко згенерувати YAML Деплойменту без його створення?**
   <details>
   <summary>Відповідь</summary>
   `k create deploy nginx --image=nginx --dry-run=client -o yaml > deploy.yaml`
   Або з аліасом: `k create deploy nginx --image=nginx $do > deploy.yaml`
   </details>

3. **Що потрібно зробити першим, починаючи нове питання іспиту?**
   <details>
   <summary>Відповідь</summary>
   Перемкнутися на правильний контекст. Кожне питання вказує, який кластер використовувати. Робота в неправильному кластері — типова помилка на іспиті.
   </details>

4. **Яке скорочення для persistentvolumeclaims?**
   <details>
   <summary>Відповідь</summary>
   `pvc` — як у `k get pvc`
   </details>

---

## Практична вправа

**Завдання**: Налаштуйте свій термінал і перевірте покращення швидкості.

**Підготовка**:
```bash
# Add all configurations to ~/.bashrc (use the complete setup from Part 5)
source ~/.bashrc
```

**Тест швидкості**:
1. Засікіть час на отримання списку всіх Подів у всіх просторах імен
2. Засікіть час на опис Поду (використовуйте автодоповнення)
3. Засікіть час на генерацію YAML Деплойменту
4. Засікіть час на перемикання контексту

**Критерії успіху**:
- [ ] `k get po -A` працює
- [ ] Автодоповнення Tab працює для назв Подів
- [ ] Змінна `$do` встановлена
- [ ] Можете перемкнути контекст за <2 секунди

**Перевірка**:
```bash
# Test alias
k get no

# Test completion (should show options)
k get <TAB><TAB>

# Test variable
echo $do  # Should output: --dry-run=client -o yaml

# Test YAML generation
k run test --image=nginx $do
```

---

## Практичні вправи

### Вправа 1: Тест швидкості — базові команди (Ціль: 30 секунд кожна)

Засікайте час. Якщо будь-яка займає >30 секунд, практикуйтесь до автоматизму.

```bash
# 1. List all pods in all namespaces with wide output
# Target command: k get po -A -o wide

# 2. Get all nodes
# Target command: k get no

# 3. Describe a pod (use autocomplete for name)
# Target command: kdp <TAB>

# 4. Switch to kube-system namespace
# Target command: kn kube-system

# 5. Generate deployment YAML without creating
# Target command: k create deploy nginx --image=nginx $do
```

### Вправа 2: Перегони з перемиканням контексту (Ціль: 1 хвилина загалом)

```bash
# Setup: Create multiple contexts to practice
kubectl config set-context practice-1 --cluster=kubernetes --user=kubernetes-admin
kubectl config set-context practice-2 --cluster=kubernetes --user=kubernetes-admin
kubectl config set-context practice-3 --cluster=kubernetes --user=kubernetes-admin

# TIMED DRILL: Switch between contexts as fast as possible
# Start timer now!

kx practice-1
kubectl config current-context  # Verify

kx practice-2
kubectl config current-context  # Verify

kx practice-3
kubectl config current-context  # Verify

kx kubernetes-admin@kubernetes  # Back to default
kubectl config current-context  # Verify

# Stop timer. Target: <1 minute for all 4 switches + verifications
```

### Вправа 3: Спринт генерації YAML (Ціль: 3 хвилини)

Згенеруйте всі ці YAML-файли за допомогою змінної `$do`. Не створюйте ресурси, лише генеруйте файли.

```bash
# 1. Pod
k run nginx --image=nginx $do > pod.yaml

# 2. Deployment
k create deploy web --image=nginx --replicas=3 $do > deploy.yaml

# 3. Service (ClusterIP)
k create svc clusterip my-svc --tcp=80:80 $do > svc-clusterip.yaml

# 4. Service (NodePort)
k create svc nodeport my-np --tcp=80:80 $do > svc-nodeport.yaml

# 5. ConfigMap
k create cm my-config --from-literal=key=value $do > cm.yaml

# 6. Secret
k create secret generic my-secret --from-literal=password=secret123 $do > secret.yaml

# Verify all files exist and are valid
ls -la *.yaml
kubectl apply -f . --dry-run=client

# Cleanup
rm -f *.yaml
```

### Вправа 4: Усунення неполадок — аліаси не працюють

**Сценарій**: Ваші аліаси перестали працювати. Діагностуйте та виправте.

```bash
# Setup: Break the aliases
unalias k 2>/dev/null
unset do

# Test: These should fail
k get nodes  # Command not found
echo $do     # Empty

# YOUR TASK: Fix without looking at the solution

# Verify fix worked:
k get nodes
echo $do
```

<details>
<summary>Рішення</summary>

```bash
# Option 1: Re-source bashrc
source ~/.bashrc

# Option 2: Manually set (if bashrc is broken)
alias k=kubectl
complete -o default -F __start_kubectl k
export do='--dry-run=client -o yaml'

# Verify
k get nodes
echo $do
```

</details>

### Вправа 5: Тест пам'яті на скорочені назви ресурсів

Не підглядаючи в таблицю, напишіть команди зі скороченнями:

```bash
# 1. Get all deployments → k get ____
# 2. Get all daemonsets → k get ____
# 3. Get all statefulsets → k get ____
# 4. Get all persistentvolumes → k get ____
# 5. Get all persistentvolumeclaims → k get ____
# 6. Get all configmaps → k get ____
# 7. Get all serviceaccounts → k get ____
# 8. Get all ingresses → k get ____
# 9. Get all networkpolicies → k get ____
# 10. Get all storageclasses → k get ____
```

<details>
<summary>Відповіді</summary>

```bash
k get deploy
k get ds
k get sts
k get pv
k get pvc
k get cm
k get sa
k get ing
k get netpol
k get sc
```

</details>

### Вправа 6: Виклик — власний набір аліасів

Створіть власні аліаси для підвищення продуктивності для цих сценаріїв:

1. Показати логи Поду з мітками часу
2. Спостерігати за Подами в поточному просторі імен
3. Отримати події, відсортовані за часом
4. Зайти в Под через bash
5. Прокинути порт на 8080

```bash
# Add to ~/.bashrc:
alias klt='kubectl logs --timestamps'
alias kw='kubectl get pods -w'
alias kev='kubectl get events --sort-by=.lastTimestamp'
alias kex='kubectl exec -it'
alias kpf='kubectl port-forward'

source ~/.bashrc

# Test each one
```

### Вправа 7: Симуляція іспиту — перші 2 хвилини

Практикуйте те, що ви б зробили на самому початку іспиту CKA:

```bash
# Timer starts NOW

# Step 1: Set up aliases (type from memory)
alias k=kubectl
complete -o default -F __start_kubectl k
export do='--dry-run=client -o yaml'
export now='--force --grace-period=0'

# Step 2: Verify setup
k get nodes
echo $do

# Step 3: Check available contexts
kubectl config get-contexts

# Timer stop. Target: <2 minutes
```

---

## Наступний модуль

[Модуль 0.3: Vim для YAML](module-0.3-vim-yaml/) — Необхідне налаштування Vim для ефективного редагування YAML-файлів.
