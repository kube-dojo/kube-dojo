---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2.4: Jobs \u0442\u0430 CronJobs"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.4-jobs-cronjobs
sidebar: 
  order: 5
lab: 
  id: cka-2.4-jobs-cronjobs
  url: https://killercoda.com/kubedojo/scenario/cka-2.4-jobs-cronjobs
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[QUICK]` — Прості пакетні робочі навантаження
>
> **Час на проходження**: 30-40 хвилин
>
> **Передумови**: Модуль 2.1 (Поди)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** Jobs та CronJobs з відповідним паралелізмом, кількістю завершень та лімітами повторних спроб
- **Дебажити** невдалі Jobs, перевіряючи логи подів, коди виходу та політики перезапуску
- **Налаштувати** політики конкурентності CronJob та ліміти історії для продуктивного використання
- **Пояснити**, коли використовувати Jobs замість Deployments та наслідки кожного варіанта для пакетних навантажень

---

## Чому цей модуль важливий

Не всі робочі навантаження працюють безперервно. Деякі виконуються один раз і завершуються:
- Міграції баз даних
- Пакетна обробка
- Генерація звітів
- Операції резервного копіювання

**Jobs** обробляють одноразові завдання. **CronJobs** обробляють заплановані, повторювані завдання. Іспит CKA перевіряє створення Jobs із конкретними вимогами до завершення та пошук несправностей у невдалих Jobs.

> **Аналогія з менеджером завдань**
>
> Уявіть Jobs як завдання у списку справ. **Job** — це одне завдання: «Згенерувати щомісячний звіт». Коли виконано — ви відмічаєте його. **CronJob** — це повторюване завдання: «Генерувати щомісячний звіт 1-го числа кожного місяця». Менеджер завдань (Kubernetes) гарантує, що завдання виконається, повторить спробу у разі невдачі та відстежить завершення.

---

## Що ви дізнаєтесь

До кінця цього модуля ви зможете:
- Створювати Jobs для одноразових завдань
- Налаштовувати паралелізм та кількість завершень
- Обробляти збої та повторні спроби Jobs
- Створювати CronJobs для запланованих завдань
- Виконувати налагодження невдалих Jobs

---

## Частина 1: Jobs

### 1.1 Що таке Job?

Job створює Поди, які працюють до завершення. На відміну від Deployments (які підтримують Поди працюючими постійно), Jobs очікують, що Поди успішно завершаться.

```
┌────────────────────────────────────────────────────────────────┐
│                    Життєвий цикл Job                            │
│                                                                 │
│   Job створено                                                  │
│       │                                                         │
│       ▼                                                         │
│   Під створено ──────────────────────────────────────────┐     │
│       │                                                  │     │
│       ▼                                                  │     │
│   Під працює                                             │     │
│       │                                                  │     │
│       ├───► Exit 0 (Успіх) ──► Job завершено            │     │
│       │                                                  │     │
│       └───► Exit ≠ 0 (Збій) ──► Повторити? ─────────────►┘     │
│                                  (залежно від backoffLimit)     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Створення Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pi-calculation
spec:
  template:
    spec:
      containers:
      - name: pi
        image: perl
        command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never    # Обов'язково для Jobs
  backoffLimit: 4             # Повторити до 4 разів у разі збою
```

```bash
# Створити job імперативно
kubectl create job pi --image=perl -- perl -Mbignum=bpi -wle "print bpi(100)"

# Згенерувати YAML
kubectl create job pi --image=perl --dry-run=client -o yaml -- perl -Mbignum=bpi -wle "print bpi(100)"
```

### 1.3 Команди для Job

```bash
# Список jobs
kubectl get jobs

# Спостерігати за прогресом job
kubectl get jobs -w

# Опис job
kubectl describe job pi-calculation

# Отримати логи job
kubectl logs job/pi-calculation

# Видалити job (також видаляє Поди)
kubectl delete job pi-calculation
```

### 1.4 Політика перезапуску

Jobs потребують або `Never`, або `OnFailure`:

| Політика | Поведінка |
|----------|-----------|
| `Never` | Створити новий Під у разі збою |
| `OnFailure` | Перезапустити контейнер у тому самому Поді у разі збою |

```yaml
spec:
  template:
    spec:
      restartPolicy: Never      # Новий Під на кожен збій
      # restartPolicy: OnFailure  # Перезапуск того самого Поду
```

> **Чи знали ви?**
>
> З `restartPolicy: Never` невдалі спроби створюють нові Поди. З backoffLimit рівним 4, ви можете побачити 5 Подів (1 оригінальний + 4 повторні спроби). З `OnFailure` ви бачите менше Подів, оскільки контейнери перезапускаються на місці.

---

## Частина 2: Завершення та паралелізм Jobs

### 2.1 Запуск з кількома завершеннями

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  completions: 5          # Job вважається успішним, коли 5 Подів завершаться успішно
  parallelism: 2          # Запускати 2 Поди одночасно
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Processing item; sleep 5"]
      restartPolicy: Never
```

### 2.2 Шаблони паралелізму

| Шаблон | completions | parallelism | Поведінка |
|--------|-------------|-------------|-----------|
| Один Під | 1 (за замовчуванням) | 1 (за замовчуванням) | Один Під працює до завершення |
| Фіксовані завершення | N | M | M Подів працюють паралельно, поки N не завершаться успішно |
| Черга роботи | не задано | N | N Подів працюють, поки один не завершиться успішно |

```
┌────────────────────────────────────────────────────────────────┐
│              Completions=5, Parallelism=2                       │
│                                                                 │
│   Час ──────────────────────────────────────────────────►      │
│                                                                 │
│   Слот 1: [Під 1 ✓] [Під 3 ✓] [Під 5 ✓]                       │
│   Слот 2: [Під 2 ✓] [Під 4 ✓]                                  │
│                                                                 │
│   2 Поди працюють одночасно, поки не досягнуто 5 завершень     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 Приклади

```bash
# Запустити 10 завдань, 3 одночасно
kubectl create job batch --image=busybox -- sh -c "echo done; sleep 2"
kubectl patch job batch -p '{"spec":{"completions":10,"parallelism":3}}'

# Або створити з YAML
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 10
  parallelism: 3
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Task complete; sleep 2"]
      restartPolicy: Never
EOF

# Спостерігати за прогресом
kubectl get jobs parallel-job -w
```

---

## Частина 3: Обробка збоїв Job

### 3.1 backoffLimit

Контролює кількість повторних спроб:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: failing-job
spec:
  backoffLimit: 3           # Повторити 3 рази, потім — збій
  template:
    spec:
      containers:
      - name: fail
        image: busybox
        command: ["sh", "-c", "exit 1"]  # Завжди завершується збоєм
      restartPolicy: Never
```

### 3.2 activeDeadlineSeconds

Максимальний час виконання job:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: timeout-job
spec:
  activeDeadlineSeconds: 60    # Зупинити job через 60 секунд
  template:
    spec:
      containers:
      - name: long-task
        image: busybox
        command: ["sleep", "120"]  # Намагається працювати 2 хвилини
      restartPolicy: Never
```

### 3.3 Перевірка статусу Job

```bash
# Статус job
kubectl get job myjob
# NAME    COMPLETIONS   DURATION   AGE
# myjob   3/5           2m         5m

# Детальний статус
kubectl describe job myjob | grep -A5 "Pods Statuses"

# Перевірити невдалі Поди
kubectl get pods -l job-name=myjob --field-selector=status.phase=Failed
```

---

## Частина 4: CronJobs

### 4.1 Що таке CronJob?

CronJob створює Jobs за розкладом, подібно до cron у Linux.

```
┌────────────────────────────────────────────────────────────────┐
│                        CronJob                                  │
│                                                                 │
│   Розклад: "0 * * * *" (щогодини)                              │
│                                                                 │
│   1:00 ──► Створює Job ──► Створює Під ──► Завершено          │
│   2:00 ──► Створює Job ──► Створює Під ──► Завершено          │
│   3:00 ──► Створює Job ──► Створює Під ──► Завершено          │
│   ...                                                           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Синтаксис розкладу cron

```
┌───────────── хвилина (0 - 59)
│ ┌───────────── година (0 - 23)
│ │ ┌───────────── день місяця (1 - 31)
│ │ │ ┌───────────── місяць (1 - 12)
│ │ │ │ ┌───────────── день тижня (0 - 6) (Неділя = 0)
│ │ │ │ │
* * * * *
```

| Розклад | Опис |
|---------|------|
| `* * * * *` | Щохвилини |
| `0 * * * *` | Щогодини |
| `0 0 * * *` | Щодня опівночі |
| `0 0 * * 0` | Щонеділі опівночі |
| `*/5 * * * *` | Кожні 5 хвилин |
| `0 9-17 * * 1-5` | Щогодини з 9 до 17, Пн-Пт |

### 4.3 Створення CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "0 2 * * *"           # Щодня о 2:00
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command: ["sh", "-c", "echo Backup started; sleep 10; echo Backup done"]
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3   # Зберігати 3 записи успішних jobs
  failedJobsHistoryLimit: 1       # Зберігати 1 запис невдалого job
```

```bash
# Створити CronJob імперативно
kubectl create cronjob backup --image=busybox --schedule="0 2 * * *" -- sh -c "echo Backup done"

# Згенерувати YAML
kubectl create cronjob backup --image=busybox --schedule="*/5 * * * *" --dry-run=client -o yaml -- echo "hello"
```

### 4.4 Команди для CronJob

```bash
# Список CronJobs
kubectl get cronjobs
kubectl get cj           # Скорочена форма

# Опис
kubectl describe cronjob backup

# Вручну запустити job з CronJob
kubectl create job --from=cronjob/backup backup-manual

# Призупинити CronJob
kubectl patch cronjob backup -p '{"spec":{"suspend":true}}'

# Відновити CronJob
kubectl patch cronjob backup -p '{"spec":{"suspend":false}}'

# Видалити CronJob (також видаляє створені Jobs)
kubectl delete cronjob backup
```

### 4.5 Політика паралельності CronJob

```yaml
spec:
  concurrencyPolicy: Allow    # За замовчуванням — дозволити одночасні jobs
  # concurrencyPolicy: Forbid   # Пропустити, якщо попередній ще працює
  # concurrencyPolicy: Replace  # Зупинити попередній, запустити новий
```

| Політика | Поведінка |
|----------|-----------|
| `Allow` | Кілька Jobs можуть працювати одночасно |
| `Forbid` | Пропустити новий Job, якщо попередній ще працює |
| `Replace` | Зупинити поточний Job, запустити новий |

> **Порада до іспиту**
>
> Для запланованих завдань резервного копіювання використовуйте `concurrencyPolicy: Forbid`, щоб запобігти перекриттю запусків. Для швидких завдань, які не повинні перекриватися, `Replace` може бути кращим варіантом.

---

## Частина 5: Налагодження Jobs

### 5.1 Типові проблеми з Jobs

| Проблема | Симптом | Команда для діагностики |
|----------|---------|------------------------|
| Помилка завантаження образу | Під у стані ImagePullBackOff | `kubectl describe pod <pod>` |
| Збій команди | Job не завершується | `kubectl logs job/<job-name>` |
| Тайм-аут | Job зупинено | Перевірте `activeDeadlineSeconds` |
| Забагато повторних спроб | Кілька невдалих Подів | Перевірте `backoffLimit` |

### 5.2 Робочий процес налагодження

```bash
# 1. Перевірити статус job
kubectl get job myjob
kubectl describe job myjob

# 2. Знайти Поди, створені job
kubectl get pods -l job-name=myjob

# 3. Перевірити логи Подів
kubectl logs <pod-name>
kubectl logs job/myjob  # Автоматично обирає Під

# 4. Якщо ще працює, зайти в Під
kubectl exec -it <pod-name> -- /bin/sh

# 5. Перевірити події
kubectl get events --field-selector involvedObject.name=myjob
```

---

## Чи знали ви?

- **Jobs не видаляються автоматично** за замовчуванням. Встановіть `ttlSecondsAfterFinished` для автоматичного очищення завершених Jobs.

- **Часовий пояс CronJob** базується на часовому поясі controller-manager (зазвичай UTC). Плануйте розклади відповідно.

- **Поди Jobs залишаються** після завершення для перевірки логів. Видаліть Job, щоб очистити Поди.

- **Indexed Jobs** (Kubernetes 1.21+) призначають унікальні індекси Подам для шаблонів паралельної обробки.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Використання `restartPolicy: Always` | Job ніколи не завершується | Використовуйте `Never` або `OnFailure` |
| Відсутній backoffLimit | Нескінченні повторні спроби | Встановіть відповідний `backoffLimit` |
| Неправильний синтаксис cron | Job ніколи не запускається | Перевірте на crontab.guru |
| Не перевірено логи | Невідома причина збою | Завжди перевіряйте `kubectl logs job/name` |
| Перекриття CronJob | Конкуренція за ресурси | Встановіть `concurrencyPolicy: Forbid` |

---

## Тест

1. **Які параметри restartPolicy допустимі для Jobs?**
   <details>
   <summary>Відповідь</summary>
   `Never` або `OnFailure`. `Always` недопустимий для Jobs, оскільки Jobs очікують, що Поди завершаться.
   </details>

2. **Job має completions: 5 та parallelism: 2. Що відбувається?**
   <details>
   <summary>Відповідь</summary>
   Job запускає 2 Поди паралельно. Коли Поди успішно завершуються, запускаються нові Поди, поки не буде досягнуто 5 загальних успішних завершень.
   </details>

3. **Як вручну запустити CronJob?**
   <details>
   <summary>Відповідь</summary>
   `kubectl create job --from=cronjob/<cronjob-name> <job-name>`

   Це одразу створює Job із шаблону CronJob.
   </details>

4. **Що робить concurrencyPolicy: Forbid?**
   <details>
   <summary>Відповідь</summary>
   Якщо попередній Job від CronJob ще працює, коли настає час нового запланованого запуску, новий Job повністю пропускається.
   </details>

---

## Практична вправа

**Завдання**: Створити Jobs та CronJobs, обробити збої.

**Кроки**:

1. **Створити простий Job**:
```bash
kubectl create job hello --image=busybox -- echo "Hello from job"
kubectl get jobs
kubectl logs job/hello
kubectl delete job hello
```

2. **Створити Job з кількома завершеннями**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-processor
spec:
  completions: 5
  parallelism: 2
  template:
    spec:
      containers:
      - name: processor
        image: busybox
        command: ["sh", "-c", "echo Processing $(hostname); sleep 3"]
      restartPolicy: Never
EOF

kubectl get jobs batch-processor -w  # Спостерігати за завершеннями
kubectl get pods -l job-name=batch-processor
kubectl delete job batch-processor
```

3. **Створити Job, що завершується збоєм**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: failing-job
spec:
  backoffLimit: 2
  template:
    spec:
      containers:
      - name: fail
        image: busybox
        command: ["sh", "-c", "echo 'About to fail'; exit 1"]
      restartPolicy: Never
EOF

kubectl get jobs failing-job -w
kubectl get pods -l job-name=failing-job  # Кілька невдалих Подів
kubectl logs job/failing-job
kubectl delete job failing-job
```

4. **Створити CronJob**:
```bash
kubectl create cronjob minute-job --image=busybox --schedule="*/1 * * * *" -- date

# Зачекати, поки виконається
sleep 70
kubectl get cronjobs
kubectl get jobs
kubectl logs job/<job-name>  # Використайте фактичну назву job

kubectl delete cronjob minute-job
```

5. **Вручну запустити CronJob**:
```bash
kubectl create cronjob backup --image=busybox --schedule="0 0 * * *" -- echo "backup"

# Запустити вручну
kubectl create job --from=cronjob/backup backup-now
kubectl get jobs
kubectl logs job/backup-now

kubectl delete cronjob backup
kubectl delete job backup-now
```

**Критерії успіху**:
- [ ] Вмієте створювати Jobs імперативно та декларативно
- [ ] Розумієте completions та parallelism
- [ ] Вмієте налагоджувати невдалі Jobs
- [ ] Вмієте створювати CronJobs
- [ ] Вмієте вручну запускати CronJobs

---

## Практичні вправи

### Вправа 1: Швидкісний тест створення Job (Ціль: 2 хвилини)

```bash
# Створити job
kubectl create job quick --image=busybox -- echo "done"

# Зачекати завершення
kubectl wait --for=condition=complete job/quick --timeout=60s

# Перевірити логи
kubectl logs job/quick

# Очищення
kubectl delete job quick
```

### Вправа 2: Паралельний Job (Ціль: 3 хвилини)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel
spec:
  completions: 6
  parallelism: 3
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Pod: $HOSTNAME; sleep 5"]
      restartPolicy: Never
EOF

# Спостерігати
kubectl get pods -l job-name=parallel -w &
kubectl get job parallel -w &
sleep 30
kill %1 %2 2>/dev/null

# Очищення
kubectl delete job parallel
```

### Вправа 3: Job із тайм-аутом (Ціль: 3 хвилини)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: timeout-test
spec:
  activeDeadlineSeconds: 10
  template:
    spec:
      containers:
      - name: long-task
        image: busybox
        command: ["sleep", "60"]
      restartPolicy: Never
EOF

# Спостерігати за тайм-аутом job
kubectl get job timeout-test -w &
sleep 15
kill %1 2>/dev/null

# Перевірити статус
kubectl describe job timeout-test | grep -A3 "Conditions"

# Очищення
kubectl delete job timeout-test
```

### Вправа 4: Створення CronJob (Ціль: 2 хвилини)

```bash
# Створити CronJob
kubectl create cronjob every-minute --image=busybox --schedule="*/1 * * * *" -- date

# Перевірити
kubectl get cronjob every-minute

# Зачекати першого запуску
sleep 70

# Перевірити створені jobs
kubectl get jobs -l job-name

# Очищення
kubectl delete cronjob every-minute
```

### Вправа 5: Ручний запуск CronJob (Ціль: 2 хвилини)

```bash
# Створити CronJob (не запуститься найближчим часом)
kubectl create cronjob daily --image=busybox --schedule="0 0 * * *" -- echo "daily task"

# Запустити вручну
kubectl create job --from=cronjob/daily daily-manual-run

# Перевірити
kubectl get jobs
kubectl logs job/daily-manual-run

# Очищення
kubectl delete cronjob daily
kubectl delete job daily-manual-run
```

### Вправа 6: Пошук несправностей у невдалому Job (Ціль: 5 хвилин)

```bash
# Створити навмисно зламаний job
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: broken
spec:
  backoffLimit: 2
  template:
    spec:
      containers:
      - name: app
        image: busybox
        command: ["sh", "-c", "cat /nonexistent/file"]
      restartPolicy: Never
EOF

# Діагностика
kubectl get job broken
kubectl get pods -l job-name=broken
kubectl describe job broken
kubectl logs job/broken

# Відповідь: Яка помилка? Як би ви її виправили?

# Очищення
kubectl delete job broken
```

### Вправа 7: Завдання — Повний робочий процес Job

Створіть Job, який:
1. Виконує 4 завершення, 2 одночасно
2. Кожен Під виводить своє ім'я хоста та чекає 3 секунди
3. Має ліміт повторних спроб 2
4. Автоматично видаляється через 60 секунд

```bash
# ВАШЕ ЗАВДАННЯ: Створіть цей Job
```

<details>
<summary>Відповідь</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: challenge-job
spec:
  completions: 4
  parallelism: 2
  backoffLimit: 2
  ttlSecondsAfterFinished: 60
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo $HOSTNAME; sleep 3"]
      restartPolicy: Never
EOF

kubectl get job challenge-job -w
```

</details>

---

## Наступний модуль

[Модуль 2.5: Управління ресурсами](module-2.5-resource-management/) — Requests, limits та класи QoS.
