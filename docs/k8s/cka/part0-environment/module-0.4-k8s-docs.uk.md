# Модуль 0.4: Навігація по kubernetes.io

> **Складність**: `[QUICK]` — Знайте, де що знаходиться, знаходьте швидко
>
> **Час на виконання**: 20-30 хвилин
>
> **Передумови**: Немає

---

## Чому цей модуль важливий

Під час іспиту CKA у вас є доступ до:
- **kubernetes.io/docs**
- **kubernetes.io/blog**
- **helm.sh/docs** (для Helm)
- **github.com/kubernetes** (для довідки)

Це іспит із відкритою книгою. Вам не потрібно запам'ятовувати схеми YAML. Але якщо ви витратите 3 хвилини на пошук прикладу NetworkPolicy, ви втратите половину часу на запитання.

Цей модуль навчить вас, де все знаходиться — щоб ви могли знайти це за секунди.

> **Аналогія з бібліотекою**
>
> Уявіть, що вам потрібен конкретний рецепт із бібліотеки. Ви можете блукати між полицями, сподіваючись випадково натрапити на нього. Або ви можете знати, що кулінарні книги знаходяться в секції 641.5, третя полиця зверху. Документація kubernetes.io — це ваша бібліотека. Блукання витрачає час. Знання розділів — Tasks для інструкцій, Reference для специфікацій, Concepts для теорії — це ваша система каталогів. Цей модуль дає вам карту.

> **Історія з практики: Пошук, що коштував 8 балів**
>
> Кандидат потребував приклад NetworkPolicy під час CKA. Він набрав "network policy" в рядку пошуку й отримав десятки результатів. Спочатку клікнув на Concepts (неправильно — теорія, без прикладів), потім на пост у блозі (цікаво, але не те, що потрібно), і нарешті знайшов сторінку Tasks. Загальний час: 4 хвилини. Він не встиг відповісти на останнє запитання. Пізніше він дізнався: Tasks → Administer Cluster → Declare Network Policy. Це 15-секундний пошук, якщо знаєш шлях.

---

## Частина 1: Структура документації

Документація Kubernetes має передбачувану структуру:

```
kubernetes.io/docs/
├── concepts/           ← Теорія, як речі працюють
├── tasks/              ← Покрокові інструкції
├── reference/          ← Специфікації API, kubectl, глосарій
└── tutorials/          ← Наскрізні навчальні посібники
```

### Що ви використовуватимете на іспиті

| Розділ | Для чого | Приклад |
|--------|----------|---------|
| **Tasks** | Як ЗРОБИТИ щось | "Configure a Pod to Use a ConfigMap" |
| **Reference** | Поля YAML, прапорці kubectl | "kubectl Cheat Sheet" |
| **Concepts** | Розуміння (рідко під час іспиту) | "What is a Service?" |

**Tasks** — ваше основне місце призначення під час іспиту.

---

## Частина 2: Збережіть ці URL-адреси

Це сторінки, які ви відвідуватимете найчастіше. Додайте їх у закладки зараз.

### Обов'язкові закладки

| Тема | URL |
|------|-----|
| **kubectl Cheat Sheet** | https://kubernetes.io/docs/reference/kubectl/cheatsheet/ |
| **Tasks (головна сторінка)** | https://kubernetes.io/docs/tasks/ |
| **Workloads** | https://kubernetes.io/docs/concepts/workloads/ |
| **Networking** | https://kubernetes.io/docs/concepts/services-networking/ |
| **Storage** | https://kubernetes.io/docs/concepts/storage/ |
| **Configuration** | https://kubernetes.io/docs/concepts/configuration/ |

### Найцінніші сторінки Tasks

| Потреба | Куди йти |
|---------|----------|
| Створити ConfigMap | Tasks → Configure Pods → Configure ConfigMaps |
| Створити Secret | Tasks → Configure Pods → Secrets |
| Створити PVC | Tasks → Configure Pods → Configure PersistentVolumeClaim |
| NetworkPolicy | Tasks → Administer Cluster → Network Policies |
| RBAC | Tasks → Administer Cluster → Using RBAC Authorization |
| Ingress | Tasks → Access Applications → Set Up Ingress |
| HPA | Tasks → Run Applications → Horizontal Pod Autoscale |

### Нове у 2025 — Знайте це

| Тема | URL |
|------|-----|
| **Gateway API** | https://kubernetes.io/docs/concepts/services-networking/gateway/ |
| **Helm** | https://helm.sh/docs/ |
| **Kustomize** | https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/ |

---

## Частина 3: Стратегія пошуку

Вбудований пошук працює, але часто швидше знати, де що знаходиться.

### Стратегія 1: Використовуйте рядок пошуку

1. Натисніть `/` або клікніть на іконку пошуку
2. Введіть ключові слова: "networkpolicy example"
3. Шукайте результати з **Tasks** в першу чергу

### Стратегія 2: Йдіть прямо до Tasks

Більшість відповідей на іспиті знаходяться в Tasks:

```
kubernetes.io/docs/tasks/
├── Administer a Cluster/
│   ├── Network Policies
│   ├── Using RBAC Authorization
│   └── Manage Resources
├── Configure Pods and Containers/
│   ├── Configure a Pod to Use a ConfigMap
│   ├── Configure a Pod to Use a Secret
│   └── Configure a Pod to Use a PersistentVolume
├── Access Applications in a Cluster/
│   └── Set up Ingress on Minikube with NGINX
└── Run Applications/
    └── Horizontal Pod Autoscaling
```

### Стратегія 3: kubectl explain

Швидше за будь-який вебсайт:

```bash
# See available fields for a resource
k explain pod.spec.containers

# Go deeper
k explain pod.spec.containers.resources
k explain pod.spec.containers.volumeMounts

# See all fields at once
k explain pod --recursive | grep -A5 "containers"
```

Це працює офлайн і показує точно, які поля доступні.

---

## Частина 4: Пошук прикладів YAML

### Патерн: Кожна сторінка Tasks має приклади

Коли ви знайдете сторінку Tasks, прокрутіть вниз. Там майже завжди є приклад YAML для копіювання.

Приклад: "Configure a Pod to Use a ConfigMap"
- Прокрутіть до "Define container environment variables using ConfigMap data"
- Скопіюйте YAML
- Модифікуйте під свої потреби

### Патерн: Шукайте розділ "What's next"

Внизу сторінок "What's next" посилається на пов'язані завдання. Якщо ви близько, але не зовсім те — перевірте ці посилання.

### Патерн: API Reference для деталей полів

Потрібно знати всі accessModes для PVC?

```
kubernetes.io/docs/reference/kubernetes-api/
├── Workload Resources/
├── Service Resources/
├── Config and Storage Resources/
│   └── PersistentVolumeClaim
└── ...
```

Або швидше:
```bash
k explain pvc.spec.accessModes
```

---

## Частина 5: Швидкий довідник розташувань

### NetworkPolicy

**Розташування**: Tasks → Administer a Cluster → Declare Network Policy

**Пряме посилання**: https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/

**Ключовий приклад**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 6379
```

### PersistentVolumeClaim

**Розташування**: Tasks → Configure Pods → Configure a Pod to Use a PersistentVolumeClaim

**Ключовий приклад**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### RBAC (Role + RoleBinding)

**Розташування**: Tasks → Administer a Cluster → Using RBAC Authorization

**Ключовий приклад**:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Ingress

**Розташування**: Concepts → Services, Load Balancing → Ingress

**Ключовий приклад**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: minimal-ingress
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

### Gateway API (Нове у 2025)

**Розташування**: Concepts → Services, Load Balancing → Gateway API

**Ключовий приклад**:
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: http-route
spec:
  parentRefs:
  - name: my-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /app
    backendRefs:
    - name: my-service
      port: 80
```

---

## Частина 6: Швидкісні вправи

Практикуйте пошук цих речей якнайшвидше:

### Вправа 1: Знайдіть приклад NetworkPolicy (Ціль: <30 секунд)
1. Перейдіть на kubernetes.io
2. Шукайте "network policy"
3. Клікніть перший результат з Tasks
4. Прокрутіть до прикладу YAML

### Вправа 2: Знайдіть accessModes для PVC (Ціль: <20 секунд)
```bash
k explain pvc.spec.accessModes
```
Або шукайте "PVC accessModes"

### Вправа 3: Знайдіть приклад RBAC Role (Ціль: <30 секунд)
1. Шукайте "RBAC"
2. Клікніть "Using RBAC Authorization"
3. Знайдіть "Role example"

### Вправа 4: Знайдіть синтаксис Helm Install (Ціль: <30 секунд)
1. Перейдіть на helm.sh/docs
2. Шукайте "install"
3. Знайдіть довідку команди `helm install`

---

## Чи знали ви?

- **Браузер на іспиті має обмежену кількість вкладок**. Ви не можете відкрити 20 вкладок, як зазвичай. Навчіться ефективно навігувати з меншою кількістю вкладок.

- **Пошук на kubernetes.io непоганий, але не ідеальний**. Іноді Google був би кращим, але на іспиті ви не можете ним скористатися. Практикуйте використання вбудованого пошуку.

- **`kubectl explain` не потребує інтернету**. Він читає з API-сервера вашого кластера. Це часто швидше, ніж пошук у документації.

- **Пости в блозі дозволені** (kubernetes.io/blog). Деякі складні теми мають чудові пояснення в блозі. Але Tasks зазвичай швидше для "як мені зробити X".

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Занадто широкий пошук | Занадто багато результатів | Використовуйте конкретні терміни: "networkpolicy ingress example" |
| Читання Concepts під час іспиту | Витрата часу | Йдіть прямо до Tasks |
| Запам'ятовування YAML | Непотрібне | Знайте, ДЕ знайти приклади |
| Невикористання kubectl explain | Повільно | `k explain` — миттєвий |
| Відкриття занадто багатьох вкладок | Браузер гальмує | Закривайте вкладки, з якими закінчили |

---

## Тест

1. **Де ви знаходите покрокові інструкції для конкретних завдань?**
   <details>
   <summary>Відповідь</summary>
   kubernetes.io/docs/tasks/ — Розділ Tasks містить інструкції з прикладами.
   </details>

2. **Який найшвидший спосіб побачити доступні поля для специфікації PVC?**
   <details>
   <summary>Відповідь</summary>
   `kubectl explain pvc.spec` — Працює офлайн, показує всі поля з описами.
   </details>

3. **Вам потрібен приклад Gateway API HTTPRoute. Де шукати?**
   <details>
   <summary>Відповідь</summary>
   kubernetes.io/docs/concepts/services-networking/gateway/ — Документація Gateway API з прикладами.
   </details>

4. **Пошук повертає занадто багато результатів для "network policy". Як звузити пошук?**
   <details>
   <summary>Відповідь</summary>
   Додайте конкретики: "network policy ingress example" або йдіть прямо до Tasks → Administer Cluster → Network Policies.
   </details>

---

## Практична вправа

**Завдання**: Практикуйте швидкий пошук документації.

**Завдання на час** (використовуйте секундомір):

1. **Знайдіть приклад ConfigMap** (Ціль: <30 сек)
   - Знайдіть повний YAML ConfigMap у документації

2. **Знайдіть приклад Secret з файлу** (Ціль: <45 сек)
   - Знайдіть, як створити Secret з файлу

3. **Знайдіть усі accessModes для PVC** (Ціль: <15 сек)
   - Використовуйте `kubectl explain`

4. **Знайдіть приклад HPA** (Ціль: <45 сек)
   - Знайдіть повний YAML HorizontalPodAutoscaler

5. **Знайдіть команду Helm upgrade** (Ціль: <30 сек)
   - Знайдіть документацію `helm upgrade`

**Критерії успіху**:
- [ ] Можете знайти сторінку ConfigMap Tasks за <30 секунд
- [ ] Можете знайти будь-який приклад YAML за <1 хвилину
- [ ] Вмієте використовувати kubectl explain
- [ ] Знаєте різницю між Tasks і Concepts

---

## Практичні вправи

### Вправа 1: Перегони по документації (цільовий час надано)

Відкрийте kubernetes.io й знайдіть якнайшвидше. Використовуйте секундомір.

| Завдання | Цільовий час |
|----------|-------------|
| Знайти приклад YAML NetworkPolicy | < 30 сек |
| Знайти приклад PVC з ReadWriteMany | < 45 сек |
| Знайти приклад RBAC RoleBinding | < 30 сек |
| Знайти приклад Ingress з TLS | < 45 сек |
| Знайти приклад HorizontalPodAutoscaler | < 45 сек |
| Знайти приклад Job з backoffLimit | < 30 сек |

Записуйте свій час. Повторюйте, поки не поб'єте всі цілі.

### Вправа 2: Опанування kubectl explain (Ціль: 2 хвилини загалом)

Без використання вебу знайдіть це, використовуючи лише `kubectl explain`:

```bash
# 1. What fields does a Pod spec have?
kubectl explain pod.spec | head -30

# 2. What are valid values for PVC accessModes?
kubectl explain pvc.spec.accessModes

# 3. What fields does a container have for health checks?
kubectl explain pod.spec.containers.livenessProbe

# 4. What's the structure of a NetworkPolicy spec?
kubectl explain networkpolicy.spec

# 5. How do you specify resource limits?
kubectl explain pod.spec.containers.resources
```

### Вправа 3: Знайти й застосувати (Ціль: 5 хвилин)

Використовуючи ЛИШЕ документацію kubernetes.io, знайдіть приклади та створіть:

```bash
# 1. Find a ConfigMap example and create one
# kubernetes.io → Tasks → Configure Pods → ConfigMaps

# 2. Find a Secret example and create one
# kubernetes.io → Tasks → Configure Pods → Secrets

# 3. Find a NetworkPolicy example and create one
# kubernetes.io → Tasks → Administer Cluster → Network Policies

# Verify all three exist
kubectl get cm,secret,netpol

# Cleanup
kubectl delete cm --all
kubectl delete secret --all  # careful: leaves default secrets
kubectl delete netpol --all
```

### Вправа 4: Пошук по документації Helm (Ціль: 3 хвилини)

Знайдіть це на helm.sh/docs:

```bash
# 1. How do you install a chart from a repo?
# Answer: helm install [RELEASE] [CHART]

# 2. How do you see values available for a chart?
# Answer: helm show values [CHART]

# 3. How do you rollback to a previous release?
# Answer: helm rollback [RELEASE] [REVISION]

# 4. How do you list all releases?
# Answer: helm list

# 5. How do you upgrade with new values?
# Answer: helm upgrade [RELEASE] [CHART] -f values.yaml
```

### Вправа 5: Глибоке занурення в Gateway API (Ціль: 5 хвилин)

Gateway API — нова тема в CKA 2025. Знайдіть це в документації:

```bash
# 1. Find the HTTPRoute example
# kubernetes.io → Concepts → Services → Gateway API

# 2. Find what parentRefs means in HTTPRoute
kubectl explain httproute.spec.parentRefs  # If Gateway API CRDs installed

# 3. Find the difference between Gateway and HTTPRoute
# Gateway = infrastructure (like LoadBalancer)
# HTTPRoute = routing rules (like Ingress rules)
```

### Вправа 6: Усунення проблем — Неправильна документація

**Сценарій**: Ви знайшли YAML, який виглядає правильним, але він не працює.

```bash
# You found this "Ingress" example but it fails
cat << 'EOF' > wrong-ingress.yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: test-ingress
spec:
  backend:
    serviceName: testsvc
    servicePort: 80
EOF

kubectl apply -f wrong-ingress.yaml
# ERROR: no matches for kind "Ingress" in version "extensions/v1beta1"

# YOUR TASK: Find the CORRECT API version in current docs
# Hint: The docs example is outdated. Find current version.
```

<details>
<summary>Рішення</summary>

Старий API `extensions/v1beta1` був застарілий. Поточна версія:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress
spec:
  defaultBackend:
    service:
      name: testsvc
      port:
        number: 80
```

**Урок**: Завжди перевіряйте, що apiVersion у документації відповідає версії вашого кластера. Використовуйте `kubectl api-resources | grep ingress`, щоб побачити доступні версії.

</details>

### Вправа 7: Швидкісний челендж по документації

Встановіть таймер на 10 хвилин. Виконайте якомога більше:

1. [ ] Створіть Под з обмеженнями ресурсів (знайдіть у документації)
2. [ ] Створіть Деплоймент з 3 реплікаами (знайдіть у документації)
3. [ ] Створіть Сервіс типу LoadBalancer (знайдіть у документації)
4. [ ] Створіть ConfigMap з файлу (знайдіть у документації)
5. [ ] Створіть PVC зі сховищем на 1Gi (знайдіть у документації)
6. [ ] Створіть Job, що виконується один раз (знайдіть у документації)
7. [ ] Створіть CronJob, що запускається щохвилини (знайдіть у документації)
8. [ ] Створіть NetworkPolicy, що дозволяє лише порт 80 (знайдіть у документації)

```bash
# Validate each one works
kubectl apply -f <file> --dry-run=client
```

Результат: Скільки ви виконали за 10 хвилин?
- 8: Відмінно — готові до іспиту
- 6-7: Добре — продовжуйте практикувати
- 4-5: Потрібна робота — повторюйте вправу щодня
- <4: Перегляньте структуру документації знову

---

## Наступний модуль

[Модуль 0.5: Стратегія іспиту — Метод трьох проходів](module-0.5-exam-strategy.uk.md) — Стратегія, що максимізує ваш бал.
