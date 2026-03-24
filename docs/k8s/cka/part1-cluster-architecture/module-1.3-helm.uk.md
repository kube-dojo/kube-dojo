# Модуль 1.3: Helm — менеджер пакетів Kubernetes

> **Складність**: `[MEDIUM]` — необхідна навичка для іспиту 2025
>
> **Час на виконання**: 40-50 хвилин
>
> **Передумови**: Модуль 0.1 (робочий кластер), базові знання YAML

---

## Чому цей модуль важливий

Helm — **новий у навчальній програмі CKA 2025**. Вас будуть тестувати з нього.

До Helm розгортання складного застосунку означало керування десятками YAML-файлів. Типовий вебзастосунок потребує Деплойментів, Сервісів, ConfigMap, Secret, Ingress, ServiceAccount, правил RBAC... усіх підтримуваних окремо, усіх потребуючих оновлення разом.

Helm пакує всі ці ресурси в один **chart** (чарт). Встановлення однією командою. Оновлення однією командою. Відкат однією командою. Ось чому Helm називають «менеджером пакетів для Kubernetes» — та сама концепція, що apt/yum/brew, але для ресурсів K8s.

> **Аналогія з магазином застосунків**
>
> Уявіть Helm як магазин застосунків. Замість того, щоб вручну завантажувати та налаштовувати програмне забезпечення по частинах, ви шукаєте те, що вам потрібно (nginx, prometheus, mysql), натискаєте «встановити», і все налаштовується правильно. Хочете кастомізувати? Змініть налаштування (values). Хочете оновити? Натисніть «оновити». Щось зламалося? Відкат до попередньої версії.

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Встановлювати та керувати застосунками за допомогою Helm
- Шукати та використовувати публічні чарти
- Кастомізувати розгортання за допомогою values
- Оновлювати та відкочувати релізи
- Розуміти структуру чартів (для усунення несправностей)

---

## Частина 1: Концепції Helm

### 1.1 Основна термінологія

| Термін | Визначення |
|--------|------------|
| **Chart** (чарт) | Пакет ресурсів Kubernetes (як .deb або .rpm) |
| **Release** (реліз) | Екземпляр чарту, що працює у вашому кластері |
| **Repository** (репозиторій) | Колекція чартів (як apt-репозиторій) |
| **Values** (значення) | Параметри конфігурації для кастомізації чарту |

### 1.2 Як працює Helm

```
┌────────────────────────────────────────────────────────────────┐
│                    Архітектура Helm                              │
│                                                                 │
│   Ви                                                            │
│    │                                                            │
│    │  helm install myapp bitnami/nginx                         │
│    ▼                                                            │
│   ┌──────────┐     ┌─────────────┐     ┌────────────────────┐  │
│   │  Helm    │────►│   Чарт     │────►│ Kubernetes API     │  │
│   │  CLI     │     │  (шаблон)  │     │ (створює ресурси)  │  │
│   └──────────┘     └─────────────┘     └────────────────────┘  │
│        │                                                        │
│        │  Values (кастомізація)                                 │
│        │  --set replicas=3                                     │
│        │  -f myvalues.yaml                                     │
│        ▼                                                        │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │ Реліз зберігається як Secret у кластері                   │ │
│   │ (відстежує версію, values, маніфести для відкату)         │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Helm 3 проти Helm 2

Helm 3 (поточний) прибрав Tiller — серверний компонент, що працював у кластері. Тепер Helm спілкується безпосередньо з API Kubernetes, використовуючи ваш kubeconfig. Це простіше та безпечніше.

```bash
# Helm 3 (поточний) - Tiller не потрібен
helm install myapp ./mychart

# Helm 2 (застарілий) - потребував Tiller
# Більше не використовуйте це
```

> **Чи знали ви?**
>
> Інформація про релізи Helm зберігається як Secret у вашому кластері. Виконайте `kubectl get secrets -l owner=helm`, щоб їх побачити. Саме так Helm відстежує, що встановлено, і забезпечує можливість відкату.

---

## Частина 2: Встановлення Helm

### 2.1 Встановлення Helm CLI

```bash
# macOS
brew install helm

# Linux (скрипт)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Linux (менеджер пакетів)
# Debian/Ubuntu
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm

# Перевірка встановлення
helm version
```

### 2.2 Додавання репозиторію

```bash
# Додати репозиторій Bitnami (популярні, добре підтримувані чарти)
helm repo add bitnami https://charts.bitnami.com/bitnami

# Додати інші поширені репозиторії
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Оновити індекс репозиторію
helm repo update

# Показати налаштовані репозиторії
helm repo list
```

---

## Частина 3: Робота з чартами

### 3.1 Пошук чартів

```bash
# Пошук в Artifact Hub (онлайн-реєстр)
helm search hub nginx

# Пошук у ваших доданих репозиторіях
helm search repo nginx

# Показати всі версії чарту
helm search repo bitnami/nginx --versions

# Отримати інформацію про конкретний чарт
helm show chart bitnami/nginx
helm show readme bitnami/nginx
helm show values bitnami/nginx  # Побачити всі параметри, що налаштовуються
```

### 3.2 Встановлення чарту

```bash
# Базове встановлення
helm install my-nginx bitnami/nginx
#           ^^^^^^^^  ^^^^^^^^^^^^^
#           назва      назва чарту
#           релізу

# Встановлення в конкретний простір імен
helm install my-nginx bitnami/nginx -n web --create-namespace

# Встановлення з кастомними значеннями
helm install my-nginx bitnami/nginx --set replicaCount=3

# Встановлення з файлом значень
helm install my-nginx bitnami/nginx -f myvalues.yaml

# Встановлення конкретної версії
helm install my-nginx bitnami/nginx --version 15.0.0

# Пробний запуск (подивитися, що буде створено)
helm install my-nginx bitnami/nginx --dry-run

# Згенерувати лише маніфести (без встановлення)
helm template my-nginx bitnami/nginx > manifests.yaml
```

### 3.3 Перегляд та інспекція релізів

```bash
# Показати всі релізи
helm list

# Показати в усіх просторах імен
helm list -A

# Показати включно з невдалими релізами
helm list --all

# Отримати статус релізу
helm status my-nginx

# Отримати values, використані для релізу
helm get values my-nginx

# Отримати всі values (включно зі значеннями за замовчуванням)
helm get values my-nginx --all

# Отримати маніфести, що були встановлені
helm get manifest my-nginx
```

> **Підступність: простір імен має значення**
>
> Релізи Helm прив'язані до простору імен. Якщо ви встановили в простір імен `web`, ви маєте вказувати `-n web` для всіх наступних команд, інакше отримаєте «release not found».

---

## Частина 4: Кастомізація за допомогою Values

### 4.1 Ієрархія Values

Values можна задавати кількома способами. Пріоритет (від найвищого до найнижчого):
1. Прапорці `--set` у командному рядку
2. Файли values через `-f` (пізніші файли перевизначають попередні)
3. Значення за замовчуванням у `values.yaml` чарту

```bash
# Приклад: Кілька способів задати кількість реплік
helm install my-nginx bitnami/nginx \
  -f base-values.yaml \
  -f production-values.yaml \
  --set replicaCount=5  # Цей виграє
```

### 4.2 Використання --set

```bash
# Просте значення
helm install my-nginx bitnami/nginx --set replicaCount=3

# Вкладене значення
helm install my-nginx bitnami/nginx --set service.type=NodePort

# Кілька значень
helm install my-nginx bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=NodePort \
  --set service.nodePorts.http=30080

# Значення масиву
helm install my-app ./mychart --set 'ingress.hosts[0]=example.com'

# Рядок, що виглядає як число (використовуйте лапки)
helm install my-app ./mychart --set 'version="1.0"'
```

### 4.3 Використання файлів Values

```yaml
# myvalues.yaml
replicaCount: 3

service:
  type: NodePort
  nodePorts:
    http: 30080

resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"

ingress:
  enabled: true
  hostname: myapp.example.com
```

```bash
# Використати файл values
helm install my-nginx bitnami/nginx -f myvalues.yaml
```

### 4.4 Перегляд значень за замовчуванням

```bash
# Побачити всі параметри, що налаштовуються
helm show values bitnami/nginx

# Зберегти у файл для довідки
helm show values bitnami/nginx > nginx-defaults.yaml
```

> **Порада до іспиту**
>
> Під час іспиту CKA використовуйте `helm show values <chart>`, щоб швидко побачити, що можна кастомізувати. Не запам'ятовуйте значення чартів — навчіться їх знаходити.

---

## Частина 5: Оновлення та відкат

### 5.1 Оновлення релізу

```bash
# Оновлення з новими значеннями
helm upgrade my-nginx bitnami/nginx --set replicaCount=5

# Оновлення з файлом значень
helm upgrade my-nginx bitnami/nginx -f newvalues.yaml

# Оновлення до нової версії чарту
helm upgrade my-nginx bitnami/nginx --version 16.0.0

# Оновити або встановити, якщо не існує
helm upgrade --install my-nginx bitnami/nginx

# Повторно використати values з попереднього релізу + нові значення
helm upgrade my-nginx bitnami/nginx --reuse-values --set replicaCount=5
```

### 5.2 Історія релізів

```bash
# Переглянути історію оновлень
helm history my-nginx

# Вивід:
# REVISION  STATUS      CHART           DESCRIPTION
# 1         superseded  nginx-15.0.0    Install complete
# 2         superseded  nginx-15.0.0    Upgrade complete
# 3         deployed    nginx-15.0.1    Upgrade complete
```

### 5.3 Відкат

```bash
# Відкат до попередньої ревізії
helm rollback my-nginx

# Відкат до конкретної ревізії
helm rollback my-nginx 1

# Пробний запуск відкату
helm rollback my-nginx 1 --dry-run
```

> **Бойова історія: Випадкове оновлення**
>
> Один інженер виконав `helm upgrade my-app ./chart` без вказівки values, випадково скинувши все до значень за замовчуванням. Облікові дані бази даних для продакшну? Зникли. Кастомні ліміти ресурсів? Зникли. Виправлення — `helm rollback my-app 1`, але знадобилося 20 хвилин, щоб зрозуміти, що сталося. Урок: завжди використовуйте `--reuse-values` або явно вказуйте всі значення при оновленні.

---

## Частина 6: Видалення

```bash
# Видалити реліз
helm uninstall my-nginx

# Видалити, але зберегти історію (дозволяє відкат)
helm uninstall my-nginx --keep-history

# Видалити в конкретному просторі імен
helm uninstall my-nginx -n web
```

---

## Частина 7: Структура чарту (для розуміння)

Вам не потрібно створювати чарти для CKA, але розуміння структури допомагає в усуненні несправностей.

```
mychart/
├── Chart.yaml          # Метадані (назва, версія, опис)
├── values.yaml         # Конфігурація за замовчуванням
├── charts/             # Залежності (підчарти)
├── templates/          # Шаблони маніфестів Kubernetes
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl    # Допоміжні шаблони
│   └── NOTES.txt       # Повідомлення після встановлення
└── README.md           # Документація
```

### 7.1 Як працюють шаблони

```yaml
# templates/deployment.yaml (спрощено)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-nginx
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
      - name: nginx
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

Значення з `values.yaml` або `--set` замінюють плейсхолдери `{{ }}`.

### 7.2 Налагодження шаблонів

```bash
# Побачити, який YAML буде згенеровано
helm template my-nginx bitnami/nginx -f myvalues.yaml

# Встановити з інформацією для налагодження
helm install my-nginx bitnami/nginx --debug --dry-run
```

---

## Частина 8: Типові сценарії на іспиті

### 8.1 Встановлення застосунку

```bash
# Завдання: Встановити nginx з 3 репліками, доступний через NodePort 30080

# Рішення:
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install web bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=NodePort \
  --set service.nodePorts.http=30080
```

### 8.2 Оновлення з новою конфігурацією

```bash
# Завдання: Оновити існуючий реліз nginx до 5 реплік

# Рішення:
helm upgrade web bitnami/nginx --reuse-values --set replicaCount=5

# Перевірка:
kubectl get deployment
```

### 8.3 Відкат після невдалого оновлення

```bash
# Завдання: Відкотити до попередньої робочої версії

# Рішення:
helm history web
helm rollback web

# Перевірка:
helm status web
```

---

## Чи знали ви?

- **Helm hooks** дозволяють запускати завдання до/після встановлення, оновлення або видалення. Чарти використовують це для міграцій баз даних, генерації сертифікатів тощо.

- **Helm використовує шаблони Go**. Синтаксис `{{ }}` — це мова шаблонів Go. Розуміння базового шаблонування Go допомагає при налагодженні складних чартів.

- **ChartMuseum** — це сервер репозиторіїв Helm з відкритим вихідним кодом. Організації використовують його для розміщення приватних чартів.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Забули `-n namespace` | Реліз не знайдено | Завжди вказуйте простір імен |
| Не використали `--reuse-values` | Values скидаються при оновленні | Використовуйте `--reuse-values` або вказуйте всі значення |
| Неправильний URL репозиторію | Чарт не знайдено | Перевірте `helm repo list`, `helm repo update` |
| Ігнорування dry-run | Створено неочікувані ресурси | Завжди `--dry-run` спочатку для складних змін |
| Не перевірили helm status | Не знаєте, чи вдалося встановлення | Виконайте `helm status <release>` після встановлення |

---

## Тест

1. **Яка команда показує всі параметри, що налаштовуються, для чарту?**
   <details>
   <summary>Відповідь</summary>
   `helm show values <chart-name>` відображає всі значення, які можна кастомізувати. Приклад: `helm show values bitnami/nginx`
   </details>

2. **Ви встановили реліз у простір імен «production», але `helm list` нічого не показує. Чому?**
   <details>
   <summary>Відповідь</summary>
   Релізи Helm прив'язані до простору імен. Вам потрібно вказати простір імен: `helm list -n production`. Або використати `helm list -A`, щоб побачити всі простори імен.
   </details>

3. **Як оновити реліз, зберігаючи існуючі values, змінюючи лише кількість реплік?**
   <details>
   <summary>Відповідь</summary>
   `helm upgrade my-release chart-name --reuse-values --set replicaCount=5`

   Прапорець `--reuse-values` зберігає всі раніше встановлені значення, а `--set` перевизначає лише вказане значення.
   </details>

4. **Яка різниця між `helm template` та `helm install --dry-run`?**
   <details>
   <summary>Відповідь</summary>
   `helm template` рендерить шаблони локально без підключення до кластера — він не може перевірити, чи ресурси вже існують, або чи типи API є дійсними.

   `helm install --dry-run` підключається до кластера, виконує валідацію, але не створює ресурси. Це точніший тест.
   </details>

---

## Практична вправа

**Завдання**: Розгорнути та керувати застосунком nginx за допомогою Helm.

**Кроки**:

1. **Додайте репозиторій Bitnami**:
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

2. **Знайдіть чарти nginx**:
```bash
helm search repo nginx
```

3. **Перегляньте значення за замовчуванням**:
```bash
helm show values bitnami/nginx | head -50
```

4. **Встановіть nginx з кастомними значеннями**:
```bash
helm install my-web bitnami/nginx \
  --set replicaCount=2 \
  --set service.type=ClusterIP \
  -n helm-demo --create-namespace
```

5. **Перевірте встановлення**:
```bash
helm list -n helm-demo
helm status my-web -n helm-demo
kubectl get all -n helm-demo
```

6. **Оновіть до 3 реплік**:
```bash
helm upgrade my-web bitnami/nginx \
  --reuse-values \
  --set replicaCount=3 \
  -n helm-demo
```

7. **Перевірте історію**:
```bash
helm history my-web -n helm-demo
```

8. **Відкотіть до ревізії 1**:
```bash
helm rollback my-web 1 -n helm-demo
kubectl get pods -n helm-demo  # Має показати 2 поди
```

9. **Отримайте використані values**:
```bash
helm get values my-web -n helm-demo
helm get values my-web -n helm-demo --all
```

10. **Очищення**:
```bash
helm uninstall my-web -n helm-demo
kubectl delete namespace helm-demo
```

**Критерії успіху**:
- [ ] Вмієте додавати репозиторії та шукати чарти
- [ ] Вмієте встановлювати чарти з кастомними значеннями
- [ ] Вмієте оновлювати релізи
- [ ] Вмієте переглядати історію та робити відкат
- [ ] Розумієте зв'язок між релізами та ресурсами Kubernetes

---

## Практичні вправи

### Вправа 1: Тест швидкості Helm (Ціль: 3 хвилини)

Виконайте ці завдання якомога швидше:

```bash
# 1. Додати репозиторій bitnami (якщо не додано)
helm repo add bitnami https://charts.bitnami.com/bitnami

# 2. Знайти redis
helm search repo redis

# 3. Показати доступні values для redis
helm show values bitnami/redis | head -50

# 4. Встановити redis з кастомною кількістю реплік
helm install my-redis bitnami/redis --set replica.replicaCount=2 --set auth.enabled=false

# 5. Показати релізи
helm list

# 6. Видалити
helm uninstall my-redis
```

### Вправа 2: Практика з файлом Values (Ціль: 5 хвилин)

```bash
# Створити файл values
cat << 'EOF' > nginx-values.yaml
replicaCount: 3
service:
  type: NodePort
  nodePorts:
    http: 30080
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "100m"
EOF

# Встановити з файлом values
helm install web bitnami/nginx -f nginx-values.yaml

# Перевірити, що values застосовані
kubectl get pods  # Має показати 3 репліки
kubectl get svc   # Має показати NodePort 30080

# Отримати використані values
helm get values web

# Очищення
helm uninstall web
rm nginx-values.yaml
```

### Вправа 3: Гонка оновлення та відкату (Ціль: 5 хвилин)

```bash
# Встановити початкову версію
helm install rollback-test bitnami/nginx --set replicaCount=2

# Оновити до 3 реплік
helm upgrade rollback-test bitnami/nginx --reuse-values --set replicaCount=3

# Перевірити
kubectl get pods | grep rollback-test | wc -l  # Має бути 3

# Перевірити історію
helm history rollback-test

# Відкотити до ревізії 1
helm rollback rollback-test 1

# Перевірити відкат
kubectl get pods | grep rollback-test | wc -l  # Має бути 2

# Очищення
helm uninstall rollback-test
```

### Вправа 4: Усунення несправностей — неправильні Values (Ціль: 5 хвилин)

```bash
# Підготовка: Встановити з «зламаними» values
helm install broken-nginx bitnami/nginx --set image.tag=nonexistent-tag

# Спостерігати проблему
kubectl get pods  # ImagePullBackOff

# ВАШЕ ЗАВДАННЯ: Виправити, оновивши з правильним тегом образу
```

<details>
<summary>Рішення</summary>

```bash
# Перевірити поточні values
helm get values broken-nginx

# Виправити оновленням
helm upgrade broken-nginx bitnami/nginx --reuse-values --set image.tag=1.25

# Перевірити
kubectl get pods  # Running!

# Очищення
helm uninstall broken-nginx
```

</details>

### Вправа 5: Dry Run та Template (Ціль: 3 хвилини)

```bash
# Побачити, що буде створено, без створення
helm install dry-test bitnami/nginx --dry-run

# Згенерувати лише YAML (для інспекції або GitOps)
helm template my-nginx bitnami/nginx > nginx-manifests.yaml
cat nginx-manifests.yaml | head -100

# Валідація YAML
kubectl apply -f nginx-manifests.yaml --dry-run=client

# Очищення
rm nginx-manifests.yaml
```

### Вправа 6: Керування кількома релізами (Ціль: 5 хвилин)

```bash
# Встановити кілька релізів
helm install prod-web bitnami/nginx --set replicaCount=3 -n production --create-namespace
helm install dev-web bitnami/nginx --set replicaCount=1 -n development --create-namespace
helm install staging-web bitnami/nginx --set replicaCount=2 -n staging --create-namespace

# Показати всі релізи в усіх просторах імен
helm list -A

# Отримати статус конкретного релізу
helm status prod-web -n production

# Очистити все
helm uninstall prod-web -n production
helm uninstall dev-web -n development
helm uninstall staging-web -n staging
kubectl delete ns production development staging
```

### Вправа 7: Виклик — встановлення без документації

Без перегляду документації виконайте це завдання:

**Завдання**: Встановити PostgreSQL з:
- Назва бази даних: myapp
- Ім'я користувача: appuser
- Пароль: secret123
- Сховище: 5Gi

```bash
# Підказка: Використовуйте helm show values, щоб знайти правильні параметри
helm show values bitnami/postgresql | grep -A5 -i "auth\|primary\|persistence"
```

<details>
<summary>Рішення</summary>

```bash
helm install mydb bitnami/postgresql \
  --set auth.database=myapp \
  --set auth.username=appuser \
  --set auth.password=secret123 \
  --set primary.persistence.size=5Gi

# Перевірити
kubectl get pods
kubectl get pvc

# Очищення
helm uninstall mydb
```

</details>

---

## Наступний модуль

[Модуль 1.4: Kustomize](module-1.4-kustomize.uk.md) — керування конфігурацією без шаблонів, нативна кастомізація Kubernetes.
