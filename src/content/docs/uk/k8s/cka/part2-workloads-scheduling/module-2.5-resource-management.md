---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2.5: \u0423\u043f\u0440\u0430\u0432\u043b\u0456\u043d\u043d\u044f \u0440\u0435\u0441\u0443\u0440\u0441\u0430\u043c\u0438"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.5-resource-management
sidebar: 
  order: 6
lab: 
  id: cka-2.5-resource-management
  url: https://killercoda.com/kubedojo/scenario/cka-2.5-resource-management
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Критично для продакшн-навантажень
>
> **Час на виконання**: 40–50 хвилин
>
> **Передумови**: Модуль 2.1 (Поди), Модуль 2.2 (Deployments)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Налаштувати** ресурсні запити та ліміти для CPU та пам'яті й пояснити, як вони впливають на планування
- **Імплементувати** LimitRanges та ResourceQuotas для управління на рівні простору імен
- **Діагностувати** збої, пов'язані з ресурсами (OOMKilled, CPU throttling, Pending через нестачу ресурсів)
- **Спроєктувати** стратегію ресурсів, що балансує утилізацію кластера з надійністю застосунків

---

## Чому цей модуль важливий

У продакшні контейнери конкурують за ресурси. Без належного налаштування:
- Один під може «з'їсти» ресурси інших
- Вузли стають перевантаженими
- Застосунки падають випадково
- Налагодження перетворюється на кошмар

Управління ресурсами є необхідним для стабільності кластера. Іспит CKA перевіряє ваше розуміння requests, limits, класів QoS та їхнього впливу на планування.

> **Аналогія з готелем**
>
> Уявіть вузол Kubernetes як готель. **Requests** — це бронювання номерів — гарантована ємність, яку ви зарезервували. **Limits** — це правила максимальної завантаженості — перевищити їх не можна. Без бронювань (requests) гості б'ються за номери. Без лімітів одна компанія захоплює весь готель. Грамотне управління ресурсами гарантує, що кожен отримає те, що потрібно.

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Налаштовувати CPU та memory requests і limits
- Розуміти, як requests впливають на планування
- Розуміти, як limits забезпечують обмеження
- Працювати з класами QoS
- Використовувати LimitRange та ResourceQuota
- Змінювати ресурси подів на місці (K8s 1.35+)

---

## Чи знали ви?

- **In-Place Pod Resize тепер GA**: Починаючи з Kubernetes 1.35, ви можете змінювати CPU та memory requests/limits на працюючих подах **без їхнього перезапуску**. Ця функція була в альфа-версії з K8s 1.27 і стабілізувалася протягом 3 років. Використовуйте `kubectl patch`, щоб змінити розмір працюючого пода — жодного простою.

---

## Частина 1: Requests та Limits

### 1.1 Основи

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:          # Мінімально гарантовані ресурси
        memory: "128Mi"
        cpu: "100m"
      limits:            # Максимально дозволені ресурси
        memory: "256Mi"
        cpu: "500m"
```

### 1.2 Requests проти Limits

| Аспект | Requests | Limits |
|--------|----------|--------|
| Призначення | Гарантія для планування | Жорстка межа |
| Коли використовується | Планувальник обирає вузол | Середовище виконання контейнера |
| Недовикористання | Інші поди можуть використати залишок | Н/З |
| Перевищення | Н/З | Контейнер завершується (пам'ять) або обмежується (CPU) |

```
┌────────────────────────────────────────────────────────────────┐
│                    Requests проти Limits                        │
│                                                                 │
│   Пам'ять: 128Mi request, 256Mi limit                          │
│                                                                 │
│   0        128Mi      256Mi               Пам'ять вузла        │
│   ├─────────┼──────────┼───────────────────────────────────►   │
│   │         │          │                                       │
│   │ Зарезер-│ Може рос-│ OOMKilled при перевищенні            │
│   │ вовано  │ ти в цей │                                       │
│   │(гаранто-│ простір  │                                       │
│   │ вано)   │          │                                       │
│                                                                 │
│   CPU: 100m request, 500m limit                                │
│                                                                 │
│   0       100m       500m                  CPU вузла           │
│   ├─────────┼──────────┼───────────────────────────────────►   │
│   │         │          │                                       │
│   │ Зарезер-│ Може     │ Обмежується (не завершується)        │
│   │ вовано  │ зростати │                                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Одиниці виміру ресурсів

**CPU** (вимірюється в ядрах):
| Значення | Пояснення |
|----------|-----------|
| `1` | 1 ядро CPU |
| `1000m` | 1 ядро CPU (мілі-ядра) |
| `100m` | 0.1 ядра CPU (100 мілі-ядер) |
| `500m` | 0.5 ядра CPU |

**Пам'ять** (вимірюється в байтах):
| Значення | Пояснення |
|----------|-----------|
| `128Mi` | 128 мебібайтів (128 × 1024² байтів) |
| `1Gi` | 1 гібібайт |
| `256M` | 256 мегабайтів (256 × 1000² байтів) |

> **Підступність**: `Mi` (мебібайт) ≠ `M` (мегабайт). `128Mi` = 134 217 728 байтів. `128M` = 128 000 000 байтів. Використовуйте `Mi` для узгодженості.

---

## Частина 2: Як Requests впливають на планування

### 2.1 Рішення планувальника

Планувальник розміщує поди на вузлах із достатніми **доступними** ресурсами:

```bash
# Перевірити доступні ресурси вузла
kubectl describe node <node-name> | grep -A6 "Allocatable"

# Allocatable:
#   cpu:                2
#   memory:             4Gi
#   pods:               110
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Рішення планувальника                        │
│                                                                 │
│   Ємність вузла: 4Gi пам'яті                                  │
│   Вже запитано: 3Gi                                            │
│   Доступно: 1Gi                                                │
│                                                                 │
│   Під A запитує 2Gi пам'яті                                   │
│   → Не може бути розміщений (2Gi > 1Gi доступно)              │
│   → Під залишається в стані Pending                            │
│                                                                 │
│   Під B запитує 500Mi пам'яті                                  │
│   → Може бути розміщений (500Mi < 1Gi доступно)               │
│   → Під розміщено на вузлі                                     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Поди в стані Pending через ресурси

```bash
# Створити під із величезним request
kubectl run big-pod --image=nginx --requests="memory=100Gi"

# Перевірити статус
kubectl get pod big-pod
# NAME      READY   STATUS    RESTARTS   AGE
# big-pod   0/1     Pending   0          10s

# З'ясувати причину
kubectl describe pod big-pod | grep -A5 "Events"
# Warning  FailedScheduling  Insufficient memory
```

### 2.3 Тиск на ресурси

```bash
# Перевірити тиск на ресурси вузла
kubectl describe node <node-name> | grep -A10 "Conditions"
# MemoryPressure    False    KubeletHasSufficientMemory
# DiskPressure      False    KubeletHasNoDiskPressure
# PIDPressure       False    KubeletHasSufficientPID
```

---

## Частина 3: Як Limits забезпечуються

### 3.1 CPU Limits (обмеження)

Коли контейнер перевищує CPU limits:
- Використання CPU **обмежується** (throttling)
- Процес сповільнюється, але продовжує працювати
- Контейнер не завершується

```bash
# Контейнер намагається використати 2 CPU при ліміті 500m
# Отримує обмеження до 500m процесорного часу
```

### 3.2 Memory Limits (OOMKilled)

Коли контейнер перевищує memory limits:
- Контейнер **завершується** (OOMKilled)
- Під може перезапуститися залежно від restartPolicy
- У статусі пода з'являється `OOMKilled`

```bash
# Перевірити OOMKilled
kubectl describe pod <pod-name> | grep -A5 "Last State"
# Last State:  Terminated
#   Reason:    OOMKilled
#   Exit Code: 137

# Перевірити події
kubectl get events --field-selector reason=OOMKilling
```

### 3.3 Демонстрація «пожирача пам'яті»

```yaml
# Під, який буде завершений через OOMKilled
apiVersion: v1
kind: Pod
metadata:
  name: memory-hog
spec:
  containers:
  - name: memory-hog
    image: polinux/stress
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "200M", "--vm-hang", "1"]
    resources:
      limits:
        memory: "100Mi"     # Ліміт менший за 200M, які виділяє stress
```

> **Історія з поля бою: Тихий витік пам'яті**
>
> Під однієї команди постійно перезапускався випадковим чином. Жодних помилок у логах застосунку. Нарешті вони перевірили `kubectl describe pod` і побачили `OOMKilled`. У застосунку був витік пам'яті, який повільно поглинав пам'ять, доки не досягнув ліміту. Без ліміту він би обвалив увесь вузол. Limits врятували кластер, а логи виявили проблему.

---

## Частина 4: Класи QoS

### 4.1 Три класи QoS

Kubernetes призначає класи QoS на основі конфігурації ресурсів:

| Клас QoS | Умова | Пріоритет витіснення |
|-----------|-------|---------------------|
| **Guaranteed** | requests = limits для всіх контейнерів | Останній (найнижчий пріоритет) |
| **Burstable** | Встановлено хоча б один request або limit | Середній |
| **BestEffort** | Жодних requests чи limits | Перший (найвищий пріоритет) |

### 4.2 Guaranteed

Усі контейнери повинні мати requests = limits для CPU та пам'яті:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"    # Те саме, що й request
        cpu: "100m"        # Те саме, що й request
```

```bash
# Перевірити клас QoS
kubectl get pod guaranteed-pod -o jsonpath='{.status.qosClass}'
# Guaranteed
```

### 4.3 Burstable

Хоча б один request або limit, але не Guaranteed:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "128Mi"
      limits:
        memory: "256Mi"    # Відрізняється від request
```

### 4.4 BestEffort

Жодних специфікацій ресурсів:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod
spec:
  containers:
  - name: app
    image: nginx
    # Секція resources відсутня
```

### 4.5 QoS та витіснення

Коли на вузлі бракує ресурсів, kubelet витісняє поди:

```
Порядок витіснення (від першого до останнього):
1. BestEffort поди, що перевищують request
2. Burstable поди, що перевищують request
3. Burstable поди в межах request
4. Guaranteed поди (крайній захід)
```

> **Чи знали ви?**
>
> Навіть якщо ви встановите лише limits, Kubernetes автоматично встановить requests на те саме значення. Отже, `limits: {memory: 128Mi}` без requests робить під Guaranteed, а не Burstable!

---

## Частина 5: LimitRange

### 5.1 Що таке LimitRange?

LimitRange встановлює стандартні/мінімальні/максимальні обмеження ресурсів на рівні простору імен:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-memory-limits
  namespace: development
spec:
  limits:
  - type: Container
    default:           # Стандартні limits, якщо не вказано
      cpu: "500m"
      memory: "256Mi"
    defaultRequest:    # Стандартні requests, якщо не вказано
      cpu: "100m"
      memory: "128Mi"
    min:               # Мінімум дозволено
      cpu: "50m"
      memory: "64Mi"
    max:               # Максимум дозволено
      cpu: "1"
      memory: "1Gi"
```

### 5.2 Ефекти LimitRange

```bash
# Застосувати LimitRange до простору імен
kubectl apply -f limitrange.yaml

# Тепер створити під без ресурсів
kubectl run test --image=nginx -n development

# Перевірити — стандартні ресурси застосовані!
kubectl get pod test -n development -o yaml | grep -A10 resources
```

### 5.3 Типи LimitRange

| Тип | Застосовується до |
|-----|-------------------|
| `Container` | Окремих контейнерів |
| `Pod` | Суми всіх контейнерів у поді |
| `PersistentVolumeClaim` | Запитів на сховище PVC |

---

## Частина 6: ResourceQuota

### 6.1 Що таке ResourceQuota?

ResourceQuota обмежує загальну кількість ресурсів, спожитих у просторі імен:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: development
spec:
  hard:
    requests.cpu: "4"           # Загальні CPU requests
    requests.memory: "8Gi"      # Загальні memory requests
    limits.cpu: "8"             # Загальні CPU limits
    limits.memory: "16Gi"       # Загальні memory limits
    pods: "10"                  # Загальна кількість подів
    persistentvolumeclaims: "5" # Загальна кількість PVC
```

### 6.2 Перевірка використання квоти

```bash
# Переглянути квоту
kubectl get resourcequota -n development

# Детальний перегляд
kubectl describe resourcequota compute-quota -n development
# Name:            compute-quota
# Resource         Used    Hard
# --------         ----    ----
# limits.cpu       2       8
# limits.memory    4Gi     16Gi
# pods             5       10
```

### 6.3 Застосування квоти

```bash
# Якщо квоту перевищено
kubectl run new-pod --image=nginx -n development
# Error: exceeded quota: compute-quota, requested: pods=1, used: pods=10, limited: pods=10
```

> **Порада для іспиту**
>
> Якщо в просторі імен встановлено ResourceQuota, поди МУСЯТЬ вказувати resource requests/limits (або мати стандартні значення через LimitRange). Інакше створення пода завершиться помилкою.

---

## Частина 7: Практичне налаштування ресурсів

### 7.1 Вибір значень

```bash
# 1. Профілюйте свій застосунок
# Запустіть локально або в тестовому середовищі, щоб виміряти фактичне споживання

# 2. Встановіть requests трохи вище за середнє споживання
# Це гарантує розміщення пода

# 3. Встановіть limits для обробки сплесків
# Залиште запас для піків, але захистіть вузол
```

### 7.2 Типові шаблони

| Тип застосунку | Request | Limit | Співвідношення |
|----------------|---------|-------|----------------|
| Вебсервер | 100m CPU, 128Mi | 500m CPU, 512Mi | 1:5, 1:4 |
| Фоновий воркер | 200m CPU, 256Mi | 1 CPU, 1Gi | 1:5, 1:4 |
| База даних | 500m CPU, 1Gi | 2 CPU, 4Gi | 1:4, 1:4 |
| Кеш | 100m CPU, 512Mi | 200m CPU, 1Gi | 1:2, 1:2 |

### 7.3 Команди для налаштування ресурсів

```bash
# Створити з ресурсами
kubectl run nginx --image=nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=256Mi"

# Оновити наявний deployment
kubectl set resources deployment/nginx \
  -c nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=256Mi"

# Перевірити використання ресурсів (потрібен metrics-server)
kubectl top pods
kubectl top nodes
```

---

## Частина 8: Моніторинг ресурсів

### 8.1 kubectl top (потрібен metrics-server)

```bash
# Перевірити використання ресурсів вузла
kubectl top nodes
# NAME    CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# node1   250m         12%    1200Mi          60%

# Перевірити використання ресурсів подів
kubectl top pods
kubectl top pods -n kube-system
kubectl top pod nginx --containers
```

### 8.2 Команди describe

```bash
# Ємність вузла та доступні ресурси
kubectl describe node <node-name> | grep -A10 "Capacity"
kubectl describe node <node-name> | grep -A10 "Allocatable"

# Зведення використання ресурсів вузла
kubectl describe node <node-name> | grep -A10 "Allocated resources"
```

---

## Частина 9: Зміна ресурсів пода на місці (K8s 1.35+)

Починаючи з Kubernetes 1.35, ви можете **змінювати CPU та пам'ять** на працюючих подах без їхнього перезапуску. Ця функція стала GA після 3 років розробки.

### 9.1 Зміна розміру працюючого пода

```bash
# Перевірити поточні ресурси
k get pod nginx -o jsonpath='{.spec.containers[0].resources}'

# Змінити CPU та пам'ять без перезапуску
k patch pod nginx --subresource resize --patch '
{
  "spec": {
    "containers": [{
      "name": "nginx",
      "resources": {
        "requests": {"cpu": "200m", "memory": "256Mi"},
        "limits": {"cpu": "500m", "memory": "512Mi"}
      }
    }]
  }
}'

# Перевірити, чи зміну застосовано
k get pod nginx -o jsonpath='{.status.resize}'
# Очікувано: "" (порожнє означає зміну завершено)
# Якщо "InProgress": зміна застосовується
# Якщо "Infeasible": на вузлі недостатньо ресурсів
```

### 9.2 Політика зміни розміру

Контейнери можуть вказувати `resizePolicy` для контролю, чи потрібен перезапуск при зміні розміру:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resize-demo
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 256Mi
    resizePolicy:
    - resourceName: cpu
      restartPolicy: NotRequired    # Зміни CPU застосовуються наживо
    - resourceName: memory
      restartPolicy: RestartContainer # Зміни пам'яті перезапускають контейнер
```

> **Коли використовувати зміну розміру на місці**
>
> - **Вертикальне масштабування без простою**: Збільшуйте ресурси під час піків трафіку, зменшуйте після
> - **Підбір правильного розміру**: Коригуйте ресурси на основі спостережуваного використання без повторного розгортання
> - **Оптимізація витрат**: Зменшуйте надлишково виділені ресурси на працюючих навантаженнях
>
> Для автоматичної зміни розміру використовуйте **Vertical Pod Autoscaler (VPA)**, який тепер може використовувати зміну розміру на місці.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Requests не встановлено | Планування ігнорує потреби в ресурсах | Завжди встановлюйте requests |
| Limits занадто низькі | Часті OOMKill | Профілюйте застосунок і встановіть відповідні limits |
| Requests = Limits (завжди) | Немає можливості для сплесків | Залиште буфер між request і limit |
| Використання `M` замість `Mi` | Трохи неточні значення | Використовуйте `Mi` та `Gi` послідовно |
| Немає LimitRange у спільних просторах імен | Неконтрольовані поди | Встановіть стандартні значення для простору імен |

---

## Тест

1. **Що трапиться, коли контейнер перевищить ліміт пам'яті?**
   <details>
   <summary>Відповідь</summary>
   Контейнер буде завершено зі статусом OOMKilled. Під може перезапуститися залежно від restartPolicy.
   </details>

2. **Що трапиться, коли контейнер перевищить ліміт CPU?**
   <details>
   <summary>Відповідь</summary>
   Контейнер буде обмежено (throttled) — він отримає менше процесорного часу, але продовжить працювати. На відміну від пам'яті, перевищення CPU не призводить до завершення.
   </details>

3. **Під має requests, але не має limits. Який його клас QoS?**
   <details>
   <summary>Відповідь</summary>
   **Burstable**. Щоб отримати Guaranteed, requests мають дорівнювати limits для всіх контейнерів. BestEffort вимагає повної відсутності ресурсів.
   </details>

4. **Як встановити стандартні ліміти ресурсів для всіх подів у просторі імен?**
   <details>
   <summary>Відповідь</summary>
   Створити LimitRange у просторі імен зі значеннями `default` та `defaultRequest`.
   </details>

---

## Практична вправа

**Завдання**: Налаштувати ресурси, протестувати ліміти, зрозуміти QoS.

**Кроки**:

1. **Створити під з ресурсами**:
```bash
kubectl run resource-test --image=nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=200m,memory=256Mi"

kubectl get pod resource-test -o jsonpath='{.status.qosClass}'
# Burstable (бо requests ≠ limits)
```

2. **Створити Guaranteed під**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "100m"
EOF

kubectl get pod guaranteed -o jsonpath='{.status.qosClass}'
# Guaranteed
```

3. **Створити BestEffort під**:
```bash
kubectl run besteffort --image=nginx
kubectl get pod besteffort -o jsonpath='{.status.qosClass}'
# BestEffort
```

4. **Створити LimitRange**:
```bash
kubectl create namespace limits-test

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: limits-test
spec:
  limits:
  - type: Container
    default:
      cpu: "200m"
      memory: "128Mi"
    defaultRequest:
      cpu: "100m"
      memory: "64Mi"
EOF

# Створити під без ресурсів
kubectl run test-defaults --image=nginx -n limits-test

# Перевірити — стандартні значення застосовані!
kubectl get pod test-defaults -n limits-test -o yaml | grep -A8 resources
```

5. **Протестувати ResourceQuota**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: pod-quota
  namespace: limits-test
spec:
  hard:
    pods: "2"
EOF

# Створювати поди, доки квоту не буде перевищено
kubectl run pod1 --image=nginx -n limits-test
kubectl run pod2 --image=nginx -n limits-test
kubectl run pod3 --image=nginx -n limits-test  # Має завершитися помилкою

kubectl describe resourcequota pod-quota -n limits-test
```

6. **Очищення**:
```bash
kubectl delete pod resource-test guaranteed besteffort
kubectl delete namespace limits-test
```

**Критерії успіху**:
- [ ] Вмієте встановлювати requests і limits
- [ ] Розумієте різницю між застосуванням CPU та memory лімітів
- [ ] Вмієте визначати класи QoS
- [ ] Вмієте створювати LimitRange
- [ ] Вмієте створювати ResourceQuota

---

## Практичні вправи

### Вправа 1: Створення ресурсів (Ціль: 2 хвилини)

```bash
# Створити під з ресурсами
kubectl run web --image=nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=512Mi"

# Перевірити
kubectl get pod web -o jsonpath='{.spec.containers[0].resources}'

# Перевірити QoS
kubectl get pod web -o jsonpath='{.status.qosClass}'

# Очищення
kubectl delete pod web
```

### Вправа 2: Визначення класу QoS (Ціль: 3 хвилини)

```bash
# Створити три поди з різними класами QoS

# Guaranteed
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: qos-guaranteed
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "100Mi"
      limits:
        cpu: "100m"
        memory: "100Mi"
EOF

# Burstable
kubectl run qos-burstable --image=nginx --requests="cpu=100m"

# BestEffort
kubectl run qos-besteffort --image=nginx

# Перевірити всі класи QoS
for pod in qos-guaranteed qos-burstable qos-besteffort; do
  echo "$pod: $(kubectl get pod $pod -o jsonpath='{.status.qosClass}')"
done

# Очищення
kubectl delete pod qos-guaranteed qos-burstable qos-besteffort
```

### Вправа 3: LimitRange (Ціль: 5 хвилин)

```bash
kubectl create namespace lr-test

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit
  namespace: lr-test
spec:
  limits:
  - type: Container
    default:
      memory: "256Mi"
    defaultRequest:
      memory: "128Mi"
    min:
      memory: "64Mi"
    max:
      memory: "1Gi"
EOF

# Перевірити застосування стандартних значень
kubectl run default-test --image=nginx -n lr-test
kubectl get pod default-test -n lr-test -o jsonpath='{.spec.containers[0].resources}'

# Спробувати перевищити максимум
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: too-big
  namespace: lr-test
spec:
  containers:
  - name: app
    image: nginx
    resources:
      limits:
        memory: "2Gi"
EOF
# Має завершитися помилкою: перевищує максимум

# Очищення
kubectl delete namespace lr-test
```

### Вправа 4: ResourceQuota (Ціль: 5 хвилин)

```bash
kubectl create namespace quota-test

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: quota-test
spec:
  hard:
    requests.cpu: "1"
    requests.memory: "1Gi"
    limits.cpu: "2"
    limits.memory: "2Gi"
    pods: "3"
EOF

# Перевірити квоту
kubectl describe resourcequota compute-quota -n quota-test

# Створити поди (потрібні ресурси, бо існує квота)
kubectl run pod1 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"
kubectl run pod2 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"
kubectl run pod3 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"

# Спробувати перевищити
kubectl run pod4 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"
# Має завершитися помилкою: квоту перевищено

# Перевірити використання квоти
kubectl describe resourcequota compute-quota -n quota-test

# Очищення
kubectl delete namespace quota-test
```

### Вправа 5: Усунення проблем з ресурсами (Ціль: 5 хвилин)

```bash
# Створити під з недостатніми ресурсами
kubectl run pending-pod --image=nginx --requests="cpu=100,memory=100Gi"

# Перевірити, чому він у стані Pending
kubectl get pod pending-pod
kubectl describe pod pending-pod | grep -A5 "Events"

# Виправити, зменшивши requests
kubectl delete pod pending-pod
kubectl run pending-pod --image=nginx --requests="cpu=100m,memory=128Mi"

# Переконатися, що працює
kubectl get pod pending-pod

# Очищення
kubectl delete pod pending-pod
```

### Вправа 6: Оновлення ресурсів (Ціль: 3 хвилини)

```bash
# Створити deployment
kubectl create deployment resource-update --image=nginx --replicas=2

# Додати ресурси
kubectl set resources deployment/resource-update \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=200m,memory=256Mi"

# Перевірити (поди перезапустяться)
kubectl get pods -l app=resource-update -w &
sleep 10
kill %1 2>/dev/null

kubectl describe deployment resource-update | grep -A10 "Resources"

# Очищення
kubectl delete deployment resource-update
```

### Вправа 7: Завдання — Повне налаштування ресурсів

Створіть простір імен із:
1. LimitRange: стандартні 200m CPU, 256Mi пам'яті; максимум 1 CPU, 1Gi пам'яті
2. ResourceQuota: максимум 4 поди, 2 CPU загальних requests, 4Gi загальних memory requests
3. Розгорніть deployment із 2 репліками та відповідними ресурсами

```bash
# ВАШЕ ЗАВДАННЯ: Виконайте це налаштування
```

<details>
<summary>Відповідь</summary>

```bash
kubectl create namespace challenge

# LimitRange
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: limits
  namespace: challenge
spec:
  limits:
  - type: Container
    default:
      cpu: "200m"
      memory: "256Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "1"
      memory: "1Gi"
EOF

# ResourceQuota
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota
  namespace: challenge
spec:
  hard:
    pods: "4"
    requests.cpu: "2"
    requests.memory: "4Gi"
EOF

# Deployment
kubectl create deployment app --image=nginx --replicas=2 -n challenge

# Перевірити
kubectl get all -n challenge
kubectl describe resourcequota quota -n challenge

# Очищення
kubectl delete namespace challenge
```

</details>

---

## Наступний модуль

[Модуль 2.6: Планування](module-2.6-scheduling/) — Вибір вузла, спорідненість, taints та tolerations.
