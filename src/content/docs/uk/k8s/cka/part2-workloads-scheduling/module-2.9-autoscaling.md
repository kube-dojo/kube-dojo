---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2.9: \u0410\u0432\u0442\u043e\u043c\u0430\u0441\u0448\u0442\u0430\u0431\u0443\u0432\u0430\u043d\u043d\u044f \u0440\u043e\u0431\u043e\u0447\u0438\u0445 \u043d\u0430\u0432\u0430\u043d\u0442\u0430\u0436\u0435\u043d\u044c"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.9-autoscaling
sidebar: 
  order: 10
lab: 
  id: cka-2.9-autoscaling
  url: https://killercoda.com/kubedojo/scenario/cka-2.9-autoscaling
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — тема іспиту CKA
>
> **Час на виконання**: 40–50 хвилин
>
> **Передумови**: Модуль 2.2 (Deployments), Модуль 2.5 (Управління ресурсами)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Налаштувати** Horizontal Pod Autoscaler (HPA) з метриками CPU та кастомними метриками
- **Пояснити** алгоритм рішень HPA (цільова утилізація, швидкість масштабування, cooldown)
- **Дебажити** HPA, що не масштабує, перевіряючи metrics-server, поточну та цільову утилізацію й події
- **Порівняти** HPA, VPA та cluster autoscaler і пояснити, коли використовувати кожен

---

## Чому цей модуль важливий

Статична кількість реплік — це або витрата грошей, або причина збоїв. Занадто багато реплік — марнування ресурсів. Занадто мало — користувачі отримують помилки під час сплесків трафіку. Автомасштабування динамічно регулює потужність залежно від реального навантаження.

На іспиті CKA перевіряють вашу здатність створювати та налаштовувати HorizontalPodAutoscaler. Вам потрібно буде робити це швидко в умовах обмеженого часу.

> **Аналогія з термостатом**
>
> Horizontal Pod Autoscaler — це як розумний термостат. Ви встановлюєте бажану «температуру» (цільове використання CPU), і система автоматично вмикає більше «обігрівачів» (Подів), коли холодно (високе навантаження), та вимикає їх, коли тепло (низьке навантаження). Ви не регулюєте опалення вручну — термостат робить це на основі поточних показників.

---

## Чи знали ви?

- **HPA перевіряє метрики кожні 15 секунд** за замовчуванням (налаштовується через `--horizontal-pod-autoscaler-sync-period`). Рішення про масштабування базуються на середньому значенні метрики по всіх Подах.

- **HPA має період охолодження**: після масштабування вгору HPA чекає 3 хвилини, перш ніж розглядати масштабування вниз (налаштовується). Це запобігає «флапінгу» — швидкому масштабуванню то вгору, то вниз.

- **metrics-server є обов'язковим**: HPA не може працювати без встановленого в кластері metrics-server. Він надає метрики CPU/пам'яті, які потрібні HPA. Це поширена пастка в практичних середовищах.

- **VPA + зміна розміру Подів на місці (K8s 1.35)**: Vertical Pod Autoscaler тепер може використовувати зміну розміру Подів на місці для коригування CPU/пам'яті без перезапуску Подів — справжній прорив для stateful-навантажень.

---

## Частина 1: Horizontal Pod Autoscaler (HPA)

### 1.1 Передумови: metrics-server

HPA потребує metrics-server для зчитування використання CPU/пам'яті:

```bash
# Check if metrics-server is installed
k top nodes
# If "error: Metrics API not available", install it:

# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For local clusters (kind/minikube), you may need to add --kubelet-insecure-tls
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

# Verify it works
k top nodes
k top pods
```

### 1.2 Створення HPA

**Імперативний спосіб (швидкий для іспиту):**

```bash
# Create HPA: scale between 2-10 replicas, target 80% CPU
k autoscale deployment web --min=2 --max=10 --cpu-percent=80

# Verify
k get hpa
# NAME   REFERENCE        TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# web    Deployment/web   12%/80%   2         10        2          30s
```

**Декларативний спосіб:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
```

### 1.3 Як HPA приймає рішення

```
┌──────────────────────────────────────────────────────────────────┐
│            Цикл рішень HPA (кожні 15 секунд)                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Зчитати поточні значення метрик із metrics-server             │
│                    │                                              │
│                    ▼                                              │
│  2. Обчислити: бажане = ceil(поточне * (фактичне / цільове))      │
│     Приклад: 3 Поди з 90% CPU, ціль 50%                          │
│     бажане = ceil(3 * (90/50)) = ceil(5.4) = 6 Подів             │
│                    │                                              │
│                    ▼                                              │
│  3. Обмежити діапазоном min/max                                   │
│     min: 2, max: 10 → результат: 6 (у межах діапазону)           │
│                    │                                              │
│                    ▼                                              │
│  4. Масштабувати deployment до 6 реплік                           │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 Моніторинг HPA

```bash
# Check HPA status
k get hpa web-hpa
k describe hpa web-hpa

# Watch scaling events
k get hpa -w

# Check events for scaling decisions
k get events --field-selector reason=SuccessfulRescale
```

---

## Частина 2: Навантажувальне тестування HPA

```bash
# Deploy a test app with resource requests
k create deployment web --image=nginx --replicas=1
k set resources deployment web --requests=cpu=100m,memory=128Mi --limits=cpu=200m,memory=256Mi

# Create HPA
k autoscale deployment web --min=1 --max=5 --cpu-percent=50

# Generate load (in another terminal)
k run load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://web; done"

# Watch HPA respond
k get hpa web -w
# You should see CPU% increase and replicas scale up

# Stop load
k delete pod load-generator

# Watch HPA scale back down (after cooldown)
k get hpa web -w
```

---

## Частина 3: Vertical Pod Autoscaler (VPA)

VPA автоматично коригує requests/limits CPU та пам'яті на основі спостережуваного використання. На відміну від HPA (більше Подів), VPA змінює *розмір* кожного Пода.

### 3.1 Коли використовувати VPA проти HPA

| Сценарій | Що використовувати |
|----------|-------------------|
| Stateless вебзастосунки | HPA (додати більше Подів) |
| Бази даних, кеші | VPA (більші Поди — не можна легко додати репліки) |
| Невідомі потреби в ресурсах | VPA у режимі recommend спершу |
| Пакетні завдання | VPA (підібрати правильний розмір Подів) |
| Поєднати обидва | HPA на користувацьких метриках + VPA на ресурсах |

### 3.2 Режими VPA

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  updatePolicy:
    updateMode: "Auto"  # Options: Off, Initial, Recreate, Auto
```

| Режим | Поведінка |
|-------|----------|
| `Off` | VPA лише рекомендує — нічого не змінює (безпечний для аудиту) |
| `Initial` | Встановлює ресурси тільки при створенні Подів (не для запущених) |
| `Recreate` | Видаляє та перестворює Поди з новими ресурсами |
| `Auto` | Використовує зміну розміру на місці (K8s 1.35+), якщо можливо; інакше — перестворення |

> **K8s 1.35 + VPA**: З GA-статусом зміни розміру Подів на місці, VPA у режимі `Auto` тепер може коригувати CPU та пам'ять запущених Подів без перезапуску — значне покращення для stateful-навантажень.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Немає metrics-server | HPA показує `<unknown>` у цілях | Спершу встановіть metrics-server |
| Немає resource requests у Подів | HPA не може обчислити використання | Завжди встановлюйте `requests` |
| Min = Max реплік | HPA не може масштабувати | Встановіть різні min та max |
| Ціль CPU занадто низька (напр., 10%) | Масштабує надто агресивно, марнує ресурси | Починайте з 50–80% |
| Використання HPA + VPA на одній метриці | Конфлікт — обидва намагаються коригувати | Використовуйте HPA для масштабування, VPA для підбору розміру (різні метрики) |
| Забули про cooldown | Дивуються, чому HPA не масштабує вниз одразу | Стандартне вікно стабілізації — 5 хв |

---

## Тест

1. **Що потрібно HPA для роботи?**
   <details>
   <summary>Відповідь</summary>
   metrics-server має бути встановлений для надання метрик CPU/пам'яті. Без нього HPA показує `<unknown>` для поточних значень і не може приймати рішення про масштабування.
   </details>

2. **Створіть HPA для deployment `api`, який масштабує від 3 до 15 Подів при 70% CPU.**
   <details>
   <summary>Відповідь</summary>
   `kubectl autoscale deployment api --min=3 --max=15 --cpu-percent=70`
   </details>

3. **Яка різниця між HPA та VPA?**
   <details>
   <summary>Відповідь</summary>
   HPA масштабує *горизонтально* — додає/видаляє репліки Подів на основі метрик. VPA масштабує *вертикально* — коригує requests CPU/пам'яті окремих Подів. HPA — для stateless-застосунків; VPA — для stateful-навантажень або підбору правильного розміру.
   </details>

4. **Чому не варто використовувати HPA та VPA на одній метриці CPU?**
   <details>
   <summary>Відповідь</summary>
   Вони конфліктуватимуть: HPA намагається додати Поди, щоб зменшити CPU на кожен Під, тоді як VPA намагається збільшити CPU на кожен Під. Використовуйте HPA для масштабування реплік, а VPA для підбору розміру ресурсів — на різних метриках.
   </details>

---

## Практична вправа

**Завдання: Автомасштабування вебзастосунку**

Налаштуйте deployment, сконфігуруйте HPA, згенеруйте навантаження та перевірте масштабування.

```bash
# 1. Create deployment with resource requests
k create deployment challenge-web --image=nginx --replicas=1
k set resources deployment challenge-web \
  --requests=cpu=50m,memory=64Mi --limits=cpu=100m,memory=128Mi

# 2. Expose it
k expose deployment challenge-web --port=80

# 3. Create HPA: 2-8 replicas, 50% CPU target
k autoscale deployment challenge-web --min=2 --max=8 --cpu-percent=50

# 4. Verify HPA is working
k get hpa challenge-web
# Should show TARGETS and current replica count

# 5. Generate load
k run load --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://challenge-web; done"

# 6. Watch scaling happen
k get hpa challenge-web -w
# Wait until you see replicas increase

# 7. Stop load and watch scale-down
k delete pod load
k get hpa challenge-web -w
# Replicas should decrease after cooldown (5 min)

# 8. Cleanup
k delete deployment challenge-web
k delete svc challenge-web
k delete hpa challenge-web
```

**Критерії успіху:**
- [ ] HPA створено з правильними min/max/target
- [ ] Репліки масштабуються вгору під навантаженням
- [ ] Репліки масштабуються вниз після зняття навантаження
- [ ] Немає `<unknown>` у цілях HPA

---

## Наступний модуль

Повернутися до [Огляд частини 2](../part2-workloads-scheduling/).
