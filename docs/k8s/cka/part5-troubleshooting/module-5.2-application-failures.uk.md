# Модуль 5.2: Збої додатків

> **Складність**: `[MEDIUM]` — Найпоширеніші сценарії усунення несправностей
>
> **Час на виконання**: 45–55 хвилин
>
> **Передумови**: Модуль 5.1 (Методологія усунення несправностей), Модуль 2.1–2.7 (Робочі навантаження)

---

## Чому цей модуль важливий

Збої додатків — це найпоширеніші проблеми, з якими ви зіткнетесь — і на іспиті, і на продакшні. Під, який не запускається, контейнер, що постійно падає, або Деплоймент, що не розгортається — це щоденні випадки. Опанування усунення збоїв додатків є критичним для будь-якого адміністратора Kubernetes.

> **Аналогія з рестораною кухнею**
>
> Уявіть Під'и як страви, що готуються на кухні. Іноді страва не вдається через поганий рецепт (неправильний образ), іноді відсутні інгредієнти (ConfigMap/Secret), іноді кухарю не вистачає місця (ресурси), а іноді страва просто не виходить (баг додатку). Кожний збій має різні симптоми й різні виправлення.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Усувати несправності Підів, що не запускаються
- Діагностувати контейнери у CrashLoopBackOff
- Виправляти помилки витягування образів
- Вирішувати проблеми з конфігурацією
- Обробляти обмеження ресурсів та OOM kill
- Налагоджувати проблеми з розгортанням Деплойментів

---

## Чи знали ви?

- **CrashLoopBackOff має експоненціальну затримку**: вона починається з 10с, потім 20с, 40с, аж до 5 хвилин між спробами перезапуску
- **Init-контейнери запускаються першими**: якщо init-контейнери не вдаються, основні контейнери ніколи не запустяться — багато хто забуває їх перевірити
- **ImagePullBackOff vs ErrImagePull**: ErrImagePull — це перший збій, ImagePullBackOff — після кількох повторних спроб

---

## Частина 1: Збої запуску Підів

### 1.1 Послідовність запуску Підів

Розуміння того, що відбувається при запуску Підів:

```
┌──────────────────────────────────────────────────────────────┐
│                ПОСЛІДОВНІСТЬ ЗАПУСКУ ПІДІВ                    │
│                                                               │
│   1. Розподіл        2. Підготовка        3. Запуск          │
│   ┌──────────┐     ┌──────────────┐    ┌──────────────┐     │
│   │ Pending  │────▶│ Container    │───▶│ Init-        │     │
│   │          │     │ Creating     │    │ контейнери   │     │
│   └──────────┘     └──────────────┘    └──────────────┘     │
│        │                  │                   │              │
│        ▼                  ▼                   ▼              │
│   • Вибір вузла      • Pull образів     • Запуск по черзі  │
│   • Перевірка        • Монтування       • Кожен має        │
│     ресурсів           томів              вийти з кодом 0   │
│   • Taints/affinity  • Налашт. мережі   • Тільки послідовно│
│                                                               │
│   4. Робота           5. Готовність                          │
│   ┌──────────────┐  ┌──────────────┐                        │
│   │ Основні      │─▶│ Readiness    │                        │
│   │ контейнери   │  │ проби пройшли│                        │
│   └──────────────┘  └──────────────┘                        │
│        │                   │                                 │
│        ▼                   ▼                                 │
│   • Запуск усіх      • Під позначений Ready                 │
│   • Запуск проб      • Доданий до Сервісу                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Pending — Проблеми розподілу

Коли Під застряг у Pending:

```bash
# Перевірити чому Під в Pending
k describe pod <pod> | grep -A 10 Events
```

**Типові причини**:

| Повідомлення | Причина | Рішення |
|--------------|---------|---------|
| `0/3 nodes available` | Немає відповідних вузлів | Перевірте taints, правила affinity |
| `Insufficient cpu` | Недостатньо CPU | Зменшіть requests або додайте потужностей |
| `Insufficient memory` | Недостатньо пам'яті | Зменшіть requests або додайте потужностей |
| `node(s) had taint that pod didn't tolerate` | Taints блокують | Додайте tolerations або видаліть taints |
| `node(s) didn't match node selector` | Неспівпадіння nodeSelector | Виправте мітки або selector |
| `persistentvolumeclaim not found` | PVC відсутній | Створіть PVC |
| `persistentvolumeclaim not bound` | Немає відповідного PV | Перевірте StorageClass, створіть PV |

**Команди для дослідження**:

```bash
# Перевірити ресурси вузлів
k describe nodes | grep -A 5 "Allocated resources"
k top nodes

# Перевірити taints вузлів
k get nodes -o custom-columns='NAME:.metadata.name,TAINTS:.spec.taints[*].key'

# Перевірити мітки вузлів (для nodeSelector)
k get nodes --show-labels
```

### 1.3 ContainerCreating — Проблеми підготовки

Коли Під застряг у ContainerCreating:

```bash
# Завжди перевіряйте Events першими
k describe pod <pod> | grep -A 15 Events
```

**Типові причини**:

| Повідомлення | Причина | Рішення |
|--------------|---------|---------|
| `pulling image` (зависло) | Повільний/великий образ | Зачекайте або використайте менший образ |
| `ImagePullBackOff` | Неправильне ім'я образу | Виправте посилання на образ |
| `ErrImagePull` | Помилка автентифікації реєстру | Перевірте imagePullSecrets |
| `MountVolume.SetUp failed` | Проблема монтування тому | Перевірте наявність PVC, ConfigMap, Secret |
| `configmap not found` | Відсутній ConfigMap | Створіть ConfigMap |
| `secret not found` | Відсутній Secret | Створіть Secret |
| `network not ready` | Проблеми з CNI | Перевірте Під'и CNI |

**Команди для дослідження**:

```bash
# Перевірити проблеми pull образів
k get events --field-selector involvedObject.name=<pod>

# Перевірити чи існують ConfigMap/Secret
k get configmap
k get secret

# Перевірити статус PVC
k get pvc
k describe pvc <name>
```

---

## Частина 2: Усунення несправностей падіння контейнерів

### 2.1 Розуміння CrashLoopBackOff

```
┌──────────────────────────────────────────────────────────────┐
│                    ЦИКЛ CRASHLOOPBACKOFF                      │
│                                                               │
│   Запуск контейнера ──▶ Падіння контейнера ──▶ Очікування ─┐│
│         ▲                                                   ││
│         └───────────────────────────────────────────────────┘│
│                                                               │
│   Час затримки:                                              │
│   1-ше падіння: чекати 10с                                   │
│   2-ге падіння: чекати 20с                                   │
│   3-тє падіння: чекати 40с                                   │
│   4-те падіння: чекати 80с                                   │
│   5-те падіння: чекати 160с                                  │
│   6-те+ падіння: чекати 300с (максимум 5 хв)                │
│                                                               │
│   Після 10 хвилин успішної роботи таймер скидається         │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Дослідження CrashLoopBackOff

**Покроковий підхід**:

```bash
# Крок 1: Перевірити статус Підів та кількість перезапусків
k get pod <pod>
# Дивіться на стовпець RESTARTS

# Крок 2: Перевірити події
k describe pod <pod> | grep -A 10 Events

# Крок 3: Перевірити поточний стан контейнера
k describe pod <pod> | grep -A 10 "State:"

# Крок 4: Перевірити ПОПЕРЕДНІ логи контейнера (критично!)
k logs <pod> --previous

# Крок 5: Перевірити код виходу
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
```

### 2.3 Розшифровка кодів виходу

| Код виходу | Сигнал | Значення | Типова причина |
|------------|--------|----------|----------------|
| 0 | - | Успіх | Нормальний вихід (не повинен викликати CrashLoop) |
| 1 | - | Помилка додатку | Логічна помилка, відсутній конфіг |
| 2 | - | Неправильне використання команди | Помилка скрипту |
| 126 | - | Команда не виконувана | Проблема з правами |
| 127 | - | Команда не знайдена | Неправильний entrypoint/command |
| 128+N | Сигнал N | Вбитий сигналом | Дивіться нижче |
| 137 | SIGKILL (9) | Примусово вбитий | OOMKilled, або `kill -9` |
| 139 | SIGSEGV (11) | Помилка сегментації | Баг додатку |
| 143 | SIGTERM (15) | Graceful завершення | Нормальне завершення |

### 2.4 Дослідження OOMKilled

Коли код виходу 137 або статус показує OOMKilled:

```bash
# Перевірити статус OOMKilled
k describe pod <pod> | grep -i oom

# Перевірити ліміти пам'яті
k get pod <pod> -o jsonpath='{.spec.containers[0].resources.limits.memory}'

# Перевірити фактичне використання пам'яті (якщо Під працює)
k top pod <pod>

# Виправлення: збільшити ліміт пам'яті
k patch deployment <name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

### 2.5 Типові причини CrashLoopBackOff

| Симптом | Діагноз | Виправлення |
|---------|---------|-------------|
| Код виходу 1 | Помилка додатку | Перевірте логи, виправте додаток |
| Код виходу 127 | Команда не знайдена | Виправте `command` або `args` у специфікації |
| Код виходу 137 + OOMKilled | Перевищення пам'яті | Збільште ліміт пам'яті |
| Код виходу 137 без OOM | Вбитий зовні | Перевірте liveness probe |
| Контейнер одразу завершується | Немає foreground-процесу | Додайте `sleep infinity` або виправте команду |
| Логи: «file not found» | Відсутній ConfigMap/Secret | Перевірте наявність монтувань |
| Логи: «permission denied» | Контекст безпеки | Виправте runAsUser або fsGroup |

---

## Частина 3: Помилки витягування образів

### 3.1 Типи помилок витягування образів

```
┌──────────────────────────────────────────────────────────────┐
│             ПОТІК ПОМИЛОК ВИТЯГУВАННЯ ОБРАЗІВ                 │
│                                                               │
│   Спроба витягнути ──▶ ErrImagePull ──▶ ImagePullBackOff    │
│        │                    │                    │            │
│        │                    │                    │            │
│   (Успіх)              (Перший збій)    (Повторні збої)      │
│                                                               │
│   Причини ErrImagePull:                                      │
│   • Образ не існує                                           │
│   • Реєстр недоступний                                       │
│   • Помилка автентифікації                                   │
│   • Ліміт запитів (Docker Hub)                               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Діагностика проблем з витягуванням образів

```bash
# Перевірити події для конкретної помилки
k describe pod <pod> | grep -A 5 "Failed to pull"

# Типові повідомлення про помилки:
# "manifest unknown" - Тег образу не існує
# "unauthorized" - Помилка автентифікації реєстру
# "timeout" - Реєстр недоступний
# "toomanyrequests" - Ліміт запитів
```

### 3.3 Виправлення проблем з витягуванням образів

**Неправильне ім'я/тег образу**:
```bash
# Перевірити поточний образ
k get pod <pod> -o jsonpath='{.spec.containers[0].image}'

# Виправити за допомогою set image
k set image deployment/<name> <container>=<correct-image>

# Або відредагувати напряму
k edit deployment <name>
```

**Автентифікація реєстру**:
```bash
# Створити секрет реєстру
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@example.com

# Додати до специфікації Підів
k patch serviceaccount default -p '{"imagePullSecrets":[{"name":"regcred"}]}'

# Або додати до конкретного Деплоймента
k patch deployment <name> -p '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"regcred"}]}}}}'
```

**Ліміт запитів Docker Hub**:
```bash
# Варіант 1: Використовувати автентифіковані запити
k create secret docker-registry dockerhub \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<token>

# Варіант 2: Використовувати альтернативний реєстр (gcr.io, quay.io)
# nginx:latest -> gcr.io/google-containers/nginx:latest
```

---

## Частина 4: Проблеми з конфігурацією

### 4.1 Відсутній ConfigMap/Secret

**Симптоми**:
- Під застряг у ContainerCreating
- Події показують «configmap not found» або «secret not found»

**Діагностика**:
```bash
# Перевірити які ConfigMaps/Secrets потрібні Підові
k get pod <pod> -o yaml | grep -A 5 "configMap\|secret"

# Перевірити їх наявність
k get configmap
k get secret

# Перевірити конкретний
k describe configmap <name>
```

**Виправлення**:
```bash
# Створити відсутній ConfigMap
k create configmap <name> --from-literal=key=value

# Створити відсутній Secret
k create secret generic <name> --from-literal=password=secret

# Якщо є файл з даними
k create configmap <name> --from-file=config.yaml
k create secret generic <name> --from-file=credentials.json
```

### 4.2 Неправильні ключі ConfigMap/Secret

**Симптоми**:
- Контейнер запускається, але додаток не працює
- Логи показують «file not found» або «key not found»

**Діагностика**:
```bash
# Перевірити які ключі є в ConfigMap
k get configmap <name> -o yaml

# Перевірити очікувані ключі Підів
k get pod <pod> -o yaml | grep -A 10 configMapKeyRef

# Порівняти очікувані з фактичними
```

**Виправлення**:
```bash
# Додати відсутній ключ до ConfigMap
k patch configmap <name> -p '{"data":{"missing-key":"value"}}'

# Або перестворити
k create configmap <name> --from-literal=key1=val1 --from-literal=key2=val2 --dry-run=client -o yaml | k apply -f -
```

### 4.3 Проблеми зі змінними середовища

```bash
# Перевірити змінні середовища в працюючому контейнері
k exec <pod> -- env

# Перевірити що визначено в специфікації
k get pod <pod> -o jsonpath='{.spec.containers[0].env[*]}'

# Типова проблема: ім'я ключа ConfigMap не збігається з ім'ям змінної середовища
# Перевірте за допомогою:
k get pod <pod> -o yaml | grep -A 5 valueFrom
```

---

## Частина 5: Збої розгортання Деплойментів

### 5.1 Застряглі Деплойменти

**Симптоми**:
- `k rollout status deployment/<name>` зависає
- Старий і новий ReplicaSets обидва існують
- Під'и не досягають стану Ready

```bash
# Перевірити статус Деплоймента
k get deployment <name>
k describe deployment <name>

# Перевірити ReplicaSets
k get rs -l app=<name>

# Перевірити Під'и з нового ReplicaSet
k get pods -l app=<name>
```

### 5.2 Типові проблеми з розгортанням

```
┌──────────────────────────────────────────────────────────────┐
│                  СТАНИ РОЗГОРТАННЯ ДЕПЛОЙМЕНТА                │
│                                                               │
│   Прогресує                     Застряг                      │
│   ┌──────────────┐           ┌──────────────┐                │
│   │ Новий RS     │           │ Новий RS     │                │
│   │ масштабується│           │ Під'и падають │                │
│   └──────────────┘           └──────────────┘                │
│         │                          │                          │
│         ▼                          ▼                          │
│   ┌──────────────┐           ┌──────────────┐                │
│   │ Старий RS    │           │ Старий RS    │                │
│   │ зменшується  │           │ ще працює    │                │
│   └──────────────┘           └──────────────┘                │
│                                                               │
│   Розгортання чекає поки нові Під'и стануть Ready            │
│   Якщо Під'и ніколи не Ready — розгортання зависає           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Дослідження**:
```bash
# Перевірити умови Деплоймента
k describe deployment <name> | grep -A 10 Conditions

# Перевірити Під'и нового ReplicaSet
NEW_RS=$(k get rs -l app=<name> --sort-by='.metadata.creationTimestamp' -o name | tail -1)
k describe $NEW_RS

# Перевірити чому Під'и не Ready
k get pods -l app=<name> | grep -v Running
k describe pod <failing-pod>
```

### 5.3 Відкат

Коли нова версія зламана:

```bash
# Перевірити історію розгортання
k rollout history deployment/<name>

# Відкотити до попередньої версії
k rollout undo deployment/<name>

# Відкотити до конкретної ревізії
k rollout undo deployment/<name> --to-revision=2

# Перевірити відкат
k rollout status deployment/<name>
```

### 5.4 Виправлення застряглих розгортань

```bash
# Варіант 1: Виправити проблему і дозволити розгортанню продовжитись
k set image deployment/<name> <container>=<fixed-image>

# Варіант 2: Відкат
k rollout undo deployment/<name>

# Варіант 3: Примусовий перезапуск (видаляє і перестворює Під'и)
k rollout restart deployment/<name>

# Варіант 4: Зменшити масштаб і збільшити (крайній варіант)
k scale deployment/<name> --replicas=0
k scale deployment/<name> --replicas=3
```

---

## Частина 6: Збої проб Readiness та Liveness

### 6.1 Огляд типів проб

```
┌──────────────────────────────────────────────────────────────┐
│                      ТИПИ ПРОБ                                │
│                                                               │
│   LIVENESS                      READINESS                     │
│   Чи контейнер живий?           Чи контейнер готовий?        │
│                                                               │
│   Дія при збої:                 Дія при збої:                │
│   ПЕРЕЗАПУСТИТИ контейнер       ВИДАЛИТИ з Сервісу            │
│                                                               │
│   Використовувати для:          Використовувати для:          │
│   • Виявлення deadlock          • Залежностей при запуску     │
│   • Зависших процесів           • Прогріву кешів             │
│                                                               │
│   Неправильний liveness         Неправильний readiness        │
│      = цикли падінь                = немає трафіку            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Діагностика збоїв проб

```bash
# Перевірити конфігурацію проб
k get pod <pod> -o yaml | grep -A 10 "livenessProbe\|readinessProbe"

# Перевірити збої проб у подіях
k describe pod <pod> | grep -i "unhealthy\|probe"

# Протестувати пробу вручну
k exec <pod> -- wget -qO- http://localhost:8080/health
k exec <pod> -- cat /tmp/healthy
```

### 6.3 Типові проблеми з пробами

| Проблема | Симптом | Виправлення |
|----------|---------|-------------|
| Неправильний порт | Проба не проходить, контейнер працює | Виправте порт у специфікації проби |
| Неправильний шлях | Помилки 404 у подіях | Виправте httpGet path |
| Занадто агресивна | Контейнери постійно перезапускаються | Збільшіть timeoutSeconds, periodSeconds |
| Відсутній initialDelaySeconds | Збій під час запуску | Додайте initialDelaySeconds |
| Додаток повільно запускається | CrashLoop при запуску | Використовуйте startupProbe |

**Виправлення таймінгу проб**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30   # Чекати 30с перед першою пробою
  periodSeconds: 10         # Проба кожні 10с
  timeoutSeconds: 5         # Тайм-аут після 5с
  failureThreshold: 3       # Перезапуск після 3 невдач
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Не перевіряти `--previous` | Не бачите причину падіння | Завжди перевіряйте попередні логи для CrashLoop |
| Ігнорування init-контейнерів | Основний контейнер ніколи не запускається | Перевіряйте логи init-контейнерів теж |
| Виправлення симптомів, а не причини | Проблема повторюється | Дослідіть кореневу причину перед виправленням |
| Неправильні одиниці ресурсів | Несподіваний OOM або тротлінг | Використовуйте правильні одиниці: Mi, Gi, m |
| Занадто агресивна liveness проба | Здорові контейнери вбиваються | Збільшіть тайм-аути та поріг збоїв |
| Забуті imagePullSecrets | Приватні образи не витягуються | Додайте секрети на рівні ServiceAccount або Підів |

---

## Тест

### Q1: Аналіз коду виходу
Контейнер має код виходу 1 з логами «Error: REDIS_HOST not set». Яке виправлення?

<details>
<summary>Відповідь</summary>

Додатку не вистачає обов'язкової змінної середовища. Виправте, додавши її:

```bash
k set env deployment/<name> REDIS_HOST=redis-service
```

Або перевірте, що ConfigMap/Secret, який повинен її надавати, існує і правильно посилається.

</details>

### Q2: Послідовність витягування образу
Яка різниця між ErrImagePull та ImagePullBackOff?

<details>
<summary>Відповідь</summary>

- **ErrImagePull**: Початковий збій витягування образу (перша спроба)
- **ImagePullBackOff**: Стан після кількох невдалих спроб витягування, з експоненціальною затримкою між повторами

ErrImagePull переходить у ImagePullBackOff після першого збою. Під чергується між спробою витягування і очікуванням.

</details>

### Q3: Діагностика Pending
Під у Pending з повідомленням «0/3 nodes are available: 3 Insufficient memory». Усі вузли мають 8 ГБ RAM. Що ви перевіряєте?

<details>
<summary>Відповідь</summary>

Перевірте:
1. Запит пам'яті Підів: `k get pod <pod> -o jsonpath='{.spec.containers[0].resources.requests.memory}'`
2. Виділені ресурси на вузлах: `k describe nodes | grep -A 5 "Allocated resources"`
3. Запити працюючих Підів: `k top nodes`

Запити від існуючих Підів плюс запит цього Підів перевищують доступну пам'ять. Або зменшіть запити, або додайте потужностей.

</details>

### Q4: Максимум CrashLoopBackOff
Який максимальний час затримки між спробами перезапуску контейнера?

<details>
<summary>Відповідь</summary>

**5 хвилин (300 секунд)**. Затримка подвоюється кожного разу: 10с, 20с, 40с, 80с, 160с, 300с. Вона залишається на 300с, поки контейнер не попрацює успішно 10 хвилин, тоді скидається.

</details>

### Q5: Збій init-контейнера
Основний контейнер ніколи не запускається, але в його логах немає помилок. Де шукати?

<details>
<summary>Відповідь</summary>

Перевірте **init-контейнери**:
```bash
k get pod <pod> -o jsonpath='{.spec.initContainers[*].name}'
k logs <pod> -c <init-container-name>
```

Init-контейнери запускаються першими і всі повинні завершитись успішно перед запуском основних контейнерів. Якщо init-контейнер не вдається, основний контейнер ніколи не розпочне роботу.

</details>

### Q6: Рішення про відкат
Деплоймент застряг посередині розгортання. Старий ReplicaSet має 2 Під'и, новий має 1 Під у CrashLoopBackOff. Яке найшвидше виправлення?

<details>
<summary>Відповідь</summary>

```bash
k rollout undo deployment/<name>
```

Це одразу відкотить до попередньої робочої версії. Потім можна спокійно дослідити збійний образ/конфігурацію.

</details>

---

## Практична вправа: Сценарії збоїв додатків

### Сценарій

Практика діагностики та виправлення різних збоїв додатків.

### Підготовка

```bash
# Створити namespace
k create ns app-debug-lab
```

### Сценарій 1: CrashLoopBackOff

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: crash-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Starting..."; exit 1']
EOF
```

**Завдання**: Знайдіть чому він падає і який код виходу має.

<details>
<summary>Рішення</summary>

```bash
k logs crash-app -n app-debug-lab --previous
k get pod crash-app -n app-debug-lab -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
# Код виходу 1 — команда явно завершується з помилкою
```

</details>

### Сценарій 2: Відсутній ConfigMap

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: config-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: nginx:1.25
    volumeMounts:
    - name: config
      mountPath: /etc/app
  volumes:
  - name: config
    configMap:
      name: app-settings
EOF
```

**Завдання**: Знайдіть чому він застряг у ContainerCreating та виправте.

<details>
<summary>Рішення</summary>

```bash
# Діагностика
k describe pod config-app -n app-debug-lab | grep -A 5 Events
# "configmap "app-settings" not found"

# Виправлення
k create configmap app-settings -n app-debug-lab --from-literal=key=value

# Перевірка
k get pod config-app -n app-debug-lab
```

</details>

### Сценарій 3: Неправильний тег образу

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: image-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: nginx:v99.99.99
EOF
```

**Завдання**: Діагностуйте та виправте збій витягування образу.

<details>
<summary>Рішення</summary>

```bash
# Діагностика
k describe pod image-app -n app-debug-lab | grep -A 5 "Failed\|Error"
# "manifest for nginx:v99.99.99 not found"

# Виправлення — видалити та перестворити з правильним образом
k delete pod image-app -n app-debug-lab
k run image-app -n app-debug-lab --image=nginx:1.25
```

</details>

### Сценарій 4: Обмеження ресурсів (OOM)

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: oom-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: progrium/stress
    args: ['--vm', '1', '--vm-bytes', '500M']
    resources:
      limits:
        memory: "100Mi"
EOF
```

**Завдання**: Діагностуйте чому контейнер постійно вбивається.

<details>
<summary>Рішення</summary>

```bash
# Діагностика
k describe pod oom-app -n app-debug-lab | grep -i oom
k get pod oom-app -n app-debug-lab -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'
# "OOMKilled"

# Контейнер намагається використати 500MB, але має ліміт лише 100Mi
# Виправлення: збільшити ліміт пам'яті або зменшити використання пам'яті додатком
```

</details>

### Критерії успіху

- [ ] Визначили код виходу crash-app як 1
- [ ] Створили відсутній ConfigMap для config-app
- [ ] Виправили неправильний тег образу для image-app
- [ ] Визначили статус OOMKilled для oom-app

### Очищення

```bash
k delete ns app-debug-lab
```

---

## Практичні вправи

### Вправа 1: Швидкий статус Підів (30 с)
```bash
# Завдання: Показати всі Під'и з кількістю перезапусків > 0
k get pods -A -o custom-columns='NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount' | awk '$2 > 0'
```

### Вправа 2: Попередні логи (30 с)
```bash
# Завдання: Отримати останні 50 рядків з попереднього екземпляра контейнера
k logs <pod> --previous --tail=50
```

### Вправа 3: Перевірка коду виходу (1 хв)
```bash
# Завдання: Отримати код виходу з контейнера, що впав
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
# Або з describe:
k describe pod <pod> | grep "Exit Code"
```

### Вправа 4: Виправлення образу (1 хв)
```bash
# Завдання: Оновити образ у Деплойменті
k set image deployment/<name> <container>=<new-image>
```

### Вправа 5: Створення відсутнього ConfigMap (1 хв)
```bash
# Завдання: Створити ConfigMap з літералу
k create configmap <name> --from-literal=key=value
# З файлу
k create configmap <name> --from-file=<filename>
```

### Вправа 6: Налагодження змінних середовища (1 хв)
```bash
# Завдання: Перевірити всі змінні середовища в працюючому контейнері
k exec <pod> -- env | sort
```

### Вправа 7: Відкат Деплоймента (1 хв)
```bash
# Завдання: Відкотити до попередньої версії
k rollout undo deployment/<name>
k rollout status deployment/<name>
```

### Вправа 8: Перевірка конфігурації проб (1 хв)
```bash
# Завдання: Переглянути конфігурацію проб
k get pod <pod> -o yaml | grep -A 15 livenessProbe
k get pod <pod> -o yaml | grep -A 15 readinessProbe
```

---

## Наступний модуль

Переходьте до [Модуль 5.3: Збої площини управління](module-5.3-control-plane.uk.md), щоб навчитися усувати несправності API-сервера, планувальника, controller manager та etcd.
