---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 5.7: \u041b\u043e\u0433\u0443\u0432\u0430\u043d\u043d\u044f \u0442\u0430 \u043c\u043e\u043d\u0456\u0442\u043e\u0440\u0438\u043d\u0433"
slug: uk/k8s/cka/part5-troubleshooting/module-5.7-logging-monitoring
sidebar: 
  order: 8
lab: 
  id: cka-5.7-logging-monitoring
  url: https://killercoda.com/kubedojo/scenario/cka-5.7-logging-monitoring
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Основні навички спостережуваності
>
> **Час на виконання**: 40–50 хвилин
>
> **Передумови**: Модуль 5.1 (Методологія), Модулі 5.2–5.6 (специфіка усунення несправностей)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Запитати** логи контейнерів за допомогою kubectl logs з вибором контейнера, попередніми логами та режимом слідкування
- **Відстежити** використання ресурсів кластера за допомогою kubectl top (вузли та поди) та пояснити metrics-server
- **Імплементувати** sidecar-логування для застосунків, що пишуть у файли замість stdout
- **Дебажити** проблеми metrics-server та пояснити, як метрики ресурсів надходять від kubelet до API server

---

## Чому цей модуль важливий

Логи та метрики — це ваші очі для розуміння того, що відбувається в кластері. Без них усунення несправностей — це вгадування. Розуміння того, як отримувати доступ до логів контейнерів, інтерпретувати події та використовувати метрики для визначення проблем з ресурсами, є фундаментальним для ефективної роботи з Kubernetes.

> **Аналогія з камерами спостереження**
>
> Логи — це як записи камер спостереження — вони фіксують що сталось і коли. Події — це як звіти про інциденти охоронця — помітні випадки, записані на папері. Метрики — це як датчики будівлі — температура, заповнюваність, споживання енергії. Разом вони розповідають повну історію того, що відбувається у вашому кластері.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Ефективно отримувати доступ та фільтрувати логи контейнерів
- Розуміти події Kubernetes та їх значення
- Використовувати kubectl top для метрик ресурсів
- Орієнтуватись у розташуванні логів на вузлах
- Застосовувати стратегії логування для усунення несправностей

---

## Чи знали ви?

- **Логи йдуть у stdout/stderr**: Kubernetes захоплює те, що контейнери пишуть у stdout та stderr — це єдина «магія» логування
- **Події зберігаються в etcd**: події — це звичайні об'єкти Kubernetes з TTL за замовчуванням 1 година
- **Metrics Server не встановлений за замовчуванням**: kubectl top вимагає запущеного Metrics Server
- **Ротація логів — завдання kubelet**: kubelet ротує логи контейнерів на основі налаштувань розміру та кількості

---

## Частина 1: Логи контейнерів

### 1.1 Як працює логування контейнерів

```
┌──────────────────────────────────────────────────────────────┐
│                  ПОТІК ЛОГУВАННЯ КОНТЕЙНЕРІВ                  │
│                                                               │
│   Контейнер                                                   │
│   ┌────────────────────────────────────────────────────┐     │
│   │  Додаток                                           │     │
│   │       │                                             │     │
│   │       ├── stdout ──────┐                           │     │
│   │       │                │                           │     │
│   │       └── stderr ──────┼────▶ Container runtime    │     │
│   │                        │      захоплює вивід       │     │
│   └────────────────────────────────────────────────────┘     │
│                            │                                  │
│                            ▼                                  │
│   Файлова система вузла                                      │
│   /var/log/containers/<pod>_<ns>_<container>-<id>.log        │
│                            │                                  │
│                            ▼                                  │
│   kubectl logs (читає ці файли через kubelet API)            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Базові команди для логів

```bash
# Переглянути логи Підів (один контейнер)
k logs <pod>

# Переглянути логи конкретного контейнера (багатоконтейнерний Під)
k logs <pod> -c <container>

# Слідкувати за логами в реальному часі
k logs <pod> -f

# Показати останні N рядків
k logs <pod> --tail=50

# Показати логи за час
k logs <pod> --since=1h
k logs <pod> --since=30m

# Показати логи з мітками часу
k logs <pod> --timestamps

# Комбінувати параметри
k logs <pod> --tail=100 --timestamps -f
```

### 1.3 Логи багатоконтейнерних Підів

```bash
# Перелік контейнерів у Підові
k get pod <pod> -o jsonpath='{.spec.containers[*].name}'

# Отримати логи конкретного контейнера
k logs <pod> -c <container>

# Отримати логи всіх контейнерів
k logs <pod> --all-containers=true

# Отримати логи init-контейнерів
k logs <pod> -c <init-container>
```

### 1.4 Логи попереднього контейнера

Критично для усунення несправностей CrashLoopBackOff:

```bash
# Отримати логи попереднього екземпляра контейнера (після падіння)
k logs <pod> --previous
k logs <pod> -c <container> --previous

# Це показує що було записано перед тим, як контейнер загинув
# Критично для розуміння чому він впав
```

### 1.5 Логи за мітками/селекторами

```bash
# Логи всіх Підів з міткою
k logs -l app=nginx

# Логи всіх Підів Деплоймента
k logs deployment/my-deployment

# Слідкувати за логами всіх відповідних Підів
k logs -l app=nginx -f

# З ім'ям контейнера для багатоконтейнерних Підів
k logs -l app=nginx -c <container>
```

---

## Частина 2: Події Kubernetes

### 2.1 Розуміння подій

```
┌──────────────────────────────────────────────────────────────┐
│                    ПОДІЇ KUBERNETES                           │
│                                                               │
│   Події генеруються:                                         │
│   • Планувальником (рішення про розподіл)                   │
│   • kubelet (життєвий цикл контейнерів)                     │
│   • Контролерами (управління ресурсами)                      │
│   • API-сервером (операції API)                              │
│                                                               │
│   Типи подій:                                                │
│   • Normal:  Інформаційні, все працює як очікувалось        │
│   • Warning: Щось неочікуване, може потребувати уваги       │
│                                                               │
│   Важливо: події зникають приблизно через 1 годину          │
│   за замовчуванням!                                          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Перегляд подій

```bash
# Усі події в поточному namespace
k get events

# Усі події по всьому кластеру
k get events -A

# Сортування за часом (найновіші останні)
k get events --sort-by='.lastTimestamp'

# Сортування за часом (найновіші перші)
k get events --sort-by='.lastTimestamp' | tac

# Фільтр за типом
k get events --field-selector type=Warning

# Події для конкретного об'єкта
k get events --field-selector involvedObject.name=<pod-name>

# Спостерігати за подіями в реальному часі
k get events -w
```

### 2.3 Типові причини подій

| Причина | Тип | Що це означає |
|---------|-----|---------------|
| Scheduled | Normal | Під призначений на вузол |
| Pulled | Normal | Образ успішно витягнуто |
| Created | Normal | Контейнер створений |
| Started | Normal | Контейнер запущений |
| Killing | Normal | Контейнер завершується |
| FailedScheduling | Warning | Не вдалось знайти відповідний вузол |
| FailedMount | Warning | Монтування тому збоїло |
| Unhealthy | Warning | Проба не пройшла |
| BackOff | Warning | Контейнер падає, затримка |
| FailedCreate | Warning | Контролер не зміг створити Під |
| Evicted | Warning | Під евіктований з вузла |
| OOMKilling | Warning | Контейнер вбитий через OOM |

### 2.4 Події у виводі describe

```bash
# Події з'являються у виводі describe
k describe pod <pod>
# Шукайте секцію Events внизу

k describe node <node>
# Показує події на рівні вузла

k describe pvc <pvc>
# Показує події прив'язки тому
```

---

## Частина 3: Метрики ресурсів

### 3.1 Metrics Server

```
┌──────────────────────────────────────────────────────────────┐
│                    METRICS SERVER                             │
│                                                               │
│   Вузли                      Metrics Server                  │
│   ┌──────────┐            ┌──────────────┐                   │
│   │ kubelet  │────────────│ Збирає       │                   │
│   │ /metrics │            │ агрегує      │                   │
│   └──────────┘            │ надає доступ │                   │
│                           └──────┬───────┘                   │
│                                  │                           │
│                           metrics.k8s.io API                  │
│                                  │                           │
│                                  ▼                           │
│                           kubectl top                        │
│                                                               │
│   Без Metrics Server → kubectl top не працює                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Перевірка Metrics Server

```bash
# Перевірити чи Metrics Server встановлений
k -n kube-system get pods | grep metrics-server

# Перевірити metrics API
k get apiservices | grep metrics

# Якщо не встановлений, команди top не працюватимуть
k top nodes  # Error: Metrics API not available
```

### 3.3 Використання kubectl top

```bash
# Використання ресурсів вузлів
k top nodes

# Використання ресурсів Підів (поточний namespace)
k top pods

# Використання ресурсів Підів (усі namespace)
k top pods -A

# Сортування за CPU
k top pods --sort-by=cpu

# Сортування за пам'яттю
k top pods --sort-by=memory

# Використання по контейнерах
k top pods --containers

# Конкретний Під
k top pod <pod-name>
```

### 3.4 Інтерпретація метрик

```
┌──────────────────────────────────────────────────────────────┐
│                  ІНТЕРПРЕТАЦІЯ МЕТРИК                         │
│                                                               │
│   NAME         CPU(cores)   MEMORY(bytes)                    │
│   my-pod       100m         256Mi                            │
│                                                               │
│   CPU: 100m = 100 мілікорів = 0.1 ядра CPU                 │
│        1000m = 1 ядро                                        │
│                                                               │
│   Пам'ять: Mi = мебібайти (1024 * 1024 байт)               │
│            Gi = гібібайти                                    │
│                                                               │
│   Порівняйте з requests/limits:                              │
│   Якщо використання >> requests: може бути OOMKilled        │
│   Якщо використання >> limit: буде OOMKilled або CPU        │
│   тротлінг                                                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.5 Порівняння ресурсів

```bash
# Порівняти фактичне використання vs запити
# Крок 1: Отримати запити
k get pod <pod> -o jsonpath='{.spec.containers[0].resources.requests}'

# Крок 2: Отримати фактичне використання
k top pod <pod>

# Якщо фактичне >> запити — Під недозапитаний
# Якщо фактичне << запити — Під перезапитаний
```

---

## Частина 4: Логи на рівні вузла

### 4.1 Розташування логів на вузлах

```
┌──────────────────────────────────────────────────────────────┐
│               РОЗТАШУВАННЯ ЛОГІВ НА ВУЗЛІ                    │
│                                                               │
│   Логи контейнерів:                                          │
│   /var/log/containers/<pod>_<ns>_<container>-<id>.log        │
│                                                               │
│   Логи Підів (symlinks):                                     │
│   /var/log/pods/<ns>_<pod>_<uid>/                            │
│                                                               │
│   Логи kubelet:                                              │
│   journalctl -u kubelet                                       │
│                                                               │
│   Логи container runtime:                                    │
│   journalctl -u containerd                                    │
│   journalctl -u docker (якщо використовується docker)       │
│                                                               │
│   Системні логи:                                             │
│   /var/log/syslog або /var/log/messages                      │
│   journalctl                                                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Доступ до логів вузла

```bash
# Спочатку SSH на вузол
ssh <node>

# Логи контейнерів напряму
ls /var/log/containers/
tail -f /var/log/containers/<pod>*.log

# Логи kubelet
journalctl -u kubelet -f
journalctl -u kubelet --since "10 minutes ago"
journalctl -u kubelet | grep -i error

# Логи container runtime
journalctl -u containerd -f

# Системні повідомлення
dmesg | tail -50
journalctl -xe
```

### 4.3 Логи компонентів площини управління

На вузлах площини управління:

```bash
# Якщо використовуються статичні Під'и (kubeadm)
# Логи доступні через kubectl
k -n kube-system logs kube-apiserver-<node>
k -n kube-system logs kube-scheduler-<node>
k -n kube-system logs kube-controller-manager-<node>
k -n kube-system logs etcd-<node>

# Або напряму на вузлі через journalctl (якщо сервіси systemd)
journalctl -u kube-apiserver
journalctl -u kube-scheduler
journalctl -u kube-controller-manager
journalctl -u etcd
```

---

## Частина 5: Стратегії логування для усунення несправностей

### 5.1 Робочий процес аналізу логів

```
┌──────────────────────────────────────────────────────────────┐
│              РОБОЧИЙ ПРОЦЕС АНАЛІЗУ ЛОГІВ                    │
│                                                               │
│   1. Починайте з подій                                       │
│      k describe <resource> | grep -A 20 Events               │
│                                                               │
│   2. Перевірте останні події по кластеру                     │
│      k get events --sort-by='.lastTimestamp' | tail          │
│                                                               │
│   3. Отримайте логи контейнера                               │
│      k logs <pod>                                             │
│      k logs <pod> --previous  (якщо впав)                   │
│                                                               │
│   4. Фільтруйте помилки                                     │
│      k logs <pod> | grep -i error                            │
│      k logs <pod> | grep -i exception                        │
│                                                               │
│   5. Перевірте час                                            │
│      k logs <pod> --timestamps --since=10m                   │
│                                                               │
│   6. Перевірте пов'язані компоненти                          │
│      Проблеми Підів: перевірте вузол                        │
│      Проблеми мережі: перевірте CNI, kube-proxy             │
│      Проблеми DNS: перевірте CoreDNS                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Фільтрація виводу логів

```bash
# Пошук помилок
k logs <pod> | grep -i error
k logs <pod> | grep -i exception
k logs <pod> | grep -i fatal

# Виключення шуму
k logs <pod> | grep -v "INFO"
k logs <pod> | grep -v "health check"

# Складні фільтри
k logs <pod> | grep -E "error|warning|failed"

# З мітками часу та фільтрацією
k logs <pod> --timestamps | grep "2024-01-15T10:3"

# Підрахунок появ помилок
k logs <pod> | grep -c error
```

### 5.3 Аналіз логів кількох Підів

```bash
# Логи всіх Підів Деплоймента
k logs deployment/<name> --all-containers

# Агрегація логів з кількох Підів за мітками
k logs -l app=frontend --all-containers

# Використання stern (не вбудований, але корисний)
# stern <pod-name-pattern>

# Обхідний шлях: цикл по Під'ах
for pod in $(k get pods -l app=nginx -o name); do
  echo "=== $pod ==="
  k logs $pod --tail=5
done
```

### 5.4 Кореляція подій та логів

```bash
# Отримати час події
k get events --field-selector involvedObject.name=my-pod

# Запам'ятайте мітку часу, потім перевірте логи навколо того часу
k logs my-pod --since-time="2024-01-15T10:30:00Z"

# Або використайте відносний час
k logs my-pod --since=5m
```

---

## Частина 6: Шаблони моніторингу

### 6.1 Проактивні команди моніторингу

```bash
# Швидка перевірка здоров'я кластера
k get nodes
k get pods -A | grep -v Running
k top nodes
k get events -A --field-selector type=Warning

# Створити простий скрипт моніторингу
watch -n 5 'kubectl get pods -A | grep -v Running | grep -v Completed'
```

### 6.2 Виявлення тиску на ресурси

```bash
# Перевірити тиск на вузли
k describe nodes | grep -E "MemoryPressure|DiskPressure|PIDPressure"

# Перевірити Під'и, що використовують надмірно ресурсів
k top pods -A --sort-by=memory | head -10
k top pods -A --sort-by=cpu | head -10

# Перевірити Під'и в Pending (може означати нестачу ресурсів)
k get pods -A --field-selector=status.phase=Pending
```

### 6.3 Налагодження з тимчасовими Під'ами

```bash
# Створити debug-Під з мережевими інструментами
k run debug --image=nicolaka/netshoot --rm -it --restart=Never -- bash

# Простий debug-Під
k run debug --image=busybox:1.36 --rm -it --restart=Never -- sh

# Debug з конкретним service account
k run debug --image=busybox:1.36 --rm -it --restart=Never --serviceaccount=<sa> -- sh

# Debug у конкретному namespace
k run debug -n <namespace> --image=busybox:1.36 --rm -it --restart=Never -- sh
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Забути `--previous` | Не бачите логи падіння | Використовуйте `--previous` для CrashLoopBackOff |
| Не фільтрувати логи | Занадто багато шуму | Використовуйте grep, `--since`, `--tail` |
| Ігнорування подій | Пропуск очевидних підказок | Завжди перевіряйте події першими |
| Пропуск багатоконтейнерних | Логи не того контейнера | Використовуйте `-c <container>` або `--all-containers` |
| Події зникли | Немає історичних даних | Перевіряйте логи одразу після інциденту |
| Немає Metrics Server | kubectl top не працює | Встановіть Metrics Server |

---

## Тест

### Q1: Попередні логи
Коли ви використовуєте `kubectl logs --previous`?

<details>
<summary>Відповідь</summary>

Використовуйте `--previous` коли контейнер **впав і перезапустився**. Він показує логи **попереднього екземпляра** контейнера перед його загибеллю. Критично для усунення несправностей CrashLoopBackOff — без нього ви бачите лише логи новозапущеного (ймовірно, знову падаючого) контейнера.

```bash
k logs <pod> --previous
```

</details>

### Q2: Зберігання подій
Як довго зберігаються події Kubernetes за замовчуванням?

<details>
<summary>Відповідь</summary>

**1 годину** за замовчуванням. Події зберігаються в etcd з TTL. Після закінчення терміну вони збираються збирачем сміття. Тому важливо перевіряти події одразу після інциденту — докази зникають.

Тривалість зберігання можна змінити прапорцем API-сервера `--event-ttl`.

</details>

### Q3: Metrics Server
kubectl top pods повертає «metrics not available». Що не так?

<details>
<summary>Відповідь</summary>

**Metrics Server не встановлений** або не працює. kubectl top вимагає запущеного Metrics Server.

Перевірте:
```bash
k -n kube-system get pods | grep metrics-server
k get apiservices | grep metrics.k8s.io
```

Встановіть Metrics Server, якщо відсутній.

</details>

### Q4: Логи багатоконтейнерних Підів
Як отримати логи всіх контейнерів у Підові?

<details>
<summary>Відповідь</summary>

```bash
k logs <pod> --all-containers=true
```

Або вкажіть кожний контейнер окремо:
```bash
k logs <pod> -c container1
k logs <pod> -c container2
```

Спочатку перелічіть контейнери:
```bash
k get pod <pod> -o jsonpath='{.spec.containers[*].name}'
```

</details>

### Q5: Розташування логів
Де зберігаються логи контейнерів на вузлі?

<details>
<summary>Відповідь</summary>

```
/var/log/containers/<pod>_<namespace>_<container>-<id>.log
```

Насправді це symlinks на реальні файли логів, якими керує container runtime. kubelet відповідає за ротацію логів.

Ви можете отримати до них прямий доступ через SSH на вузол.

</details>

### Q6: Події vs Логи
Коли ви перевіряєте події vs логи?

<details>
<summary>Відповідь</summary>

**Події** першими — для:
- Проблем розподілу (чому Під не розподілений)
- Життєвого циклу контейнерів (створення, запуск, зупинка)
- Монтування томів
- Витягування образів
- Загального розуміння «що сталось»

**Логи** другими — для:
- Проблем на рівні додатку
- Чому додаток збоїть
- Детальних повідомлень про помилки
- Stack trace
- «Що робить додаток»

Події розповідають про операції Kubernetes; логи розповідають про поведінку додатку.

</details>

---

## Практична вправа: Аналіз логів та метрик

### Сценарій

Практика використання логів та метрик для усунення несправностей.

### Підготовка

```bash
# Створити тестовий namespace
k create ns logging-lab

# Створити Під, що генерує логи
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: log-generator
  namespace: logging-lab
spec:
  containers:
  - name: logger
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      i=0
      while true; do
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Log message $i"
        if [ $((i % 5)) -eq 0 ]; then
          echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Something went wrong at iteration $i" >&2
        fi
        i=$((i+1))
        sleep 2
      done
EOF

# Створити Під, що падає, для демонстрації --previous
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: crashy-pod
  namespace: logging-lab
spec:
  containers:
  - name: crasher
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      echo "Starting up..."
      sleep 5
      echo "About to crash!"
      exit 1
EOF
```

### Завдання 1: Базові операції з логами

```bash
# Переглянути логи
k logs -n logging-lab log-generator

# Слідкувати за логами
k logs -n logging-lab log-generator -f
# (Ctrl+C для зупинки)

# Останні 10 рядків
k logs -n logging-lab log-generator --tail=10

# З мітками часу
k logs -n logging-lab log-generator --tail=10 --timestamps
```

### Завдання 2: Фільтрація логів

```bash
# Знайти лише помилки
k logs -n logging-lab log-generator | grep ERROR

# Підрахувати помилки
k logs -n logging-lab log-generator | grep -c ERROR

# Виключити повідомлення INFO
k logs -n logging-lab log-generator | grep -v INFO
```

### Завдання 3: Логи попереднього контейнера

```bash
# Зачекати поки crashy-pod впаде та перезапуститься
k get pod -n logging-lab crashy-pod -w

# Коли покаже CrashLoopBackOff або перезапуски, перевірте попередні логи
k logs -n logging-lab crashy-pod --previous
```

### Завдання 4: Аналіз подій

```bash
# Усі події в namespace
k get events -n logging-lab --sort-by='.lastTimestamp'

# Описати Під для подій
k describe pod -n logging-lab crashy-pod | grep -A 10 Events

# Спостерігати за новими подіями
k get events -n logging-lab -w
```

### Завдання 5: Метрики (якщо Metrics Server встановлений)

```bash
# Метрики вузлів
k top nodes

# Метрики Підів
k top pods -n logging-lab

# Усі Під'и за пам'яттю
k top pods -A --sort-by=memory | head
```

### Критерії успіху

- [ ] Переглянули логи в реальному часі зі слідкуванням
- [ ] Відфільтрували логи за помилками
- [ ] Отримали логи попереднього контейнера
- [ ] Проаналізували події для інформації про падіння
- [ ] Використали kubectl top (якщо Metrics Server доступний)

### Очищення

```bash
k delete ns logging-lab
```

---

## Практичні вправи

### Вправа 1: Перегляд останніх N логів (30 с)
```bash
# Завдання: Показати останні 20 рядків логів
k logs <pod> --tail=20
```

### Вправа 2: Логи з мітками часу (30 с)
```bash
# Завдання: Показати логи з мітками часу
k logs <pod> --timestamps
```

### Вправа 3: Логи попереднього контейнера (30 с)
```bash
# Завдання: Отримати логи контейнера, що впав
k logs <pod> --previous
```

### Вправа 4: Логи багатоконтейнерних Підів (1 хв)
```bash
# Завдання: Отримати логи конкретного контейнера
k get pod <pod> -o jsonpath='{.spec.containers[*].name}'
k logs <pod> -c <container-name>
```

### Вправа 5: Останні події (30 с)
```bash
# Завдання: Показати події, відсортовані за часом
k get events --sort-by='.lastTimestamp'
```

### Вправа 6: Попереджувальні події (30 с)
```bash
# Завдання: Показати лише попереджувальні події
k get events --field-selector type=Warning
```

### Вправа 7: Метрики вузлів (30 с)
```bash
# Завдання: Показати використання ресурсів вузлів
k top nodes
```

### Вправа 8: Метрики Підів відсортовані (30 с)
```bash
# Завдання: Показати Під'и з найбільшим споживанням пам'яті
k top pods -A --sort-by=memory | head
```

---

## Підсумок Частини 5

Вітаємо із завершенням Частини 5: Усунення несправностей! Ви вивчили:

1. **Методологію**: Систематичний підхід до діагностики
2. **Збої додатків**: Проблеми Підів, контейнерів та Деплойментів
3. **Площину управління**: API-сервер, планувальник, controller manager, etcd
4. **Робочі вузли**: kubelet, runtime та ресурси вузлів
5. **Мережу**: Зв'язок Підів, DNS та CNI
6. **Сервіси**: ClusterIP, NodePort, LoadBalancer, Ingress
7. **Логування та моніторинг**: Логи, події та метрики

З 30% ваги іспиту CKA усунення несправностей є критичним. Практикуйте вправи, поки вони не стануть автоматичними.

---

## Наступні кроки

Переходьте до [Частина 6: Пробні іспити](../part6-mock-exams/), щоб перевірити свої знання на реалістичних сценаріях іспиту.
