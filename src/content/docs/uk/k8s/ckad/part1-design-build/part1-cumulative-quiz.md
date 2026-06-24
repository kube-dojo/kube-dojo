---
title: "\u041f\u0456\u0434\u0441\u0443\u043c\u043a\u043e\u0432\u0438\u0439 \u0442\u0435\u0441\u0442 \u0427\u0430\u0441\u0442\u0438\u043d\u0438 1: \u041f\u0440\u043e\u0454\u043a\u0442\u0443\u0432\u0430\u043d\u043d\u044f \u0442\u0430 \u0437\u0431\u0456\u0440\u043a\u0430 \u0437\u0430\u0441\u0442\u043e\u0441\u0443\u043d\u043a\u0456\u0432"
sidebar:
  order: 5
calque_review:
  reviewed_at: "2026-06-24"
  detector_version: "v2"
  status: "reviewed"
  flags_resolved: 2
  content_sha: "e24dd428729bc9672ee736867424ec61d6cea46dffb90c06ab3a7bcd5ce1cbe7"
---
> **Обмеження часу**: 25 хвилин (симуляція тиску іспиту)
>
> **Прохідний бал**: 80% (8/10 запитань)

Цей тест перевіряє ваше володіння:
- Образами контейнерів
- Jobs та CronJobs
- Підами з кількома контейнерами (sidecar, init, ambassador)
- Томами (emptyDir, ConfigMap, Secret, PVC)

---

## Інструкції

1. Спробуйте відповісти на кожне запитання, не заглядаючи у відповіді
2. Засікайте час — швидкість важлива для CKAD
3. Використовуйте лише `kubectl` та `kubernetes.io/docs`
4. Перевірте відповіді після завершення всіх запитань

---

## Запитання

### Запитання 1: Проблема із завантаженням образу
**[2 хвилини]**

Под застряг у `ImagePullBackOff`:

```bash
k get pods
# NAME      READY   STATUS             RESTARTS   AGE
# broken    0/1     ImagePullBackOff   0          5m
```

Визначте проблему та виправте її. Під повинен запускати nginx версії 1.21.

<details>
<summary>Відповідь</summary>

```bash
# Діагностика
k describe pod broken | grep -A5 Events
# Шукайте: failed to pull image

# Перевірити поточний образ
k get pod broken -o jsonpath='{.spec.containers[0].image}'
# Ймовірно неправильний тег або друкарська помилка

# Виправлення (видалити та створити заново або пропатчити)
k delete pod broken
k run broken --image=nginx:1.21
```

</details>

---

### Запитання 2: Створення Job
**[2 хвилини]**

Створіть Job з назвою `backup-job`, який:
- Використовує образ `busybox`
- Виконує команду `echo "Backup completed at $(date)"`
- Має backoff limit 2

<details>
<summary>Відповідь</summary>

```bash
# Згенерувати та модифікувати
k create job backup-job --image=busybox --dry-run=client -o yaml -- sh -c 'echo "Backup completed at $(date)"' > job.yaml

# Додати backoffLimit: 2 до spec, потім застосувати
# Або напряму:
cat << 'EOF' | k apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: backup-job
spec:
  backoffLimit: 2
  template:
    spec:
      containers:
      - name: backup
        image: busybox
        command: ["sh", "-c", "echo Backup completed at $(date)"]
      restartPolicy: Never
EOF
```

</details>

---

### Запитання 3: Розклад CronJob
**[2 хвилини]**

Створіть CronJob з назвою `cleanup`, який:
- Запускається кожні 30 хвилин
- Використовує образ `busybox`
- Виводить "Cleanup running"
- Має `concurrencyPolicy: Forbid`

<details>
<summary>Відповідь</summary>

```bash
# Імперативно, потім пропатчити
k create cronjob cleanup --image=busybox --schedule="*/30 * * * *" -- echo "Cleanup running"
k patch cronjob cleanup -p '{"spec":{"concurrencyPolicy":"Forbid"}}'

# Або YAML:
cat << 'EOF' | k apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup
spec:
  schedule: "*/30 * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: busybox
            command: ["echo", "Cleanup running"]
          restartPolicy: OnFailure
EOF
```

</details>

---

### Запитання 4: Під з кількома контейнерами
**[3 хвилини]**

Створіть Під з назвою `sidecar-pod` з:
- Основний контейнер: образ `nginx`
- Sidecar-контейнер: образ `busybox`, що виконує `tail -f /var/log/nginx/access.log`
- Обидва контейнери ділять том, змонтований у `/var/log/nginx`

<details>
<summary>Відповідь</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-pod
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx
  - name: sidecar
    image: busybox
    command: ["tail", "-f", "/var/log/nginx/access.log"]
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx
  volumes:
  - name: logs
    emptyDir: {}
```

```bash
k apply -f sidecar-pod.yaml
```

</details>

---

### Запитання 5: Init-контейнер
**[3 хвилини]**

Створіть Під з назвою `init-pod`, який:
- Має init-контейнер, що створює файл `/work/ready.txt` зі вмістом "initialized"
- Основний контейнер (nginx) монтує ту саму директорію

<details>
<summary>Відповідь</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-pod
spec:
  initContainers:
  - name: init
    image: busybox
    command: ["sh", "-c", "echo initialized > /work/ready.txt"]
    volumeMounts:
    - name: workdir
      mountPath: /work
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: workdir
      mountPath: /work
  volumes:
  - name: workdir
    emptyDir: {}
```

Перевірка:
```bash
k exec init-pod -- cat /work/ready.txt
```

</details>

---

### Запитання 6: ConfigMap як том
**[2 хвилини]**

Створіть ConfigMap з назвою `web-content` з ключем `index.html`, що містить "Hello CKAD".

Потім створіть Під з назвою `web-server`, який:
- Використовує образ nginx
- Монтує ConfigMap у `/usr/share/nginx/html`

<details>
<summary>Відповідь</summary>

```bash
# Створити ConfigMap
k create cm web-content --from-literal=index.html="Hello CKAD"

# Створити Під
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-server
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
  volumes:
  - name: html
    configMap:
      name: web-content
EOF

# Перевірка
k exec web-server -- curl localhost
```

</details>

---

### Запитання 7: Том Secret
**[2 хвилини]**

Створіть Secret з назвою `db-creds` з:
- `username=admin`
- `password=secret123`

Змонтуйте його тільки для читання у Під з назвою `secret-pod` у `/etc/db`

<details>
<summary>Відповідь</summary>

```bash
# Створити secret
k create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secret123

# Створити Під
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secret-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    volumeMounts:
    - name: secrets
      mountPath: /etc/db
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
EOF

# Перевірка
k exec secret-pod -- cat /etc/db/password
```

</details>

---

### Запитання 8: Паралельний Job
**[3 хвилини]**

Створіть Job з назвою `parallel-job`, який:
- Виконує 6 завершень
- З паралелізмом 2
- Використовує busybox для виведення "Processing"

<details>
<summary>Відповідь</summary>

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 6
  parallelism: 2
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["echo", "Processing"]
      restartPolicy: Never
```

Перевірка:
```bash
k get pods -l job-name=parallel-job -w
# Повинні бачити 2 Піди одночасно, 6 загалом
```

</details>

---

### Запитання 9: Виправлення Підa з кількома контейнерами
**[3 хвилини]**

Наступний Під не запускається. Визначте та виправте проблему:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: broken-multi
spec:
  initContainers:
  - name: init
    image: busybox
    command: ["sleep", "infinity"]  # Проблема!
  containers:
  - name: main
    image: nginx
```

<details>
<summary>Відповідь</summary>

**Проблема**: Init-контейнер виконує `sleep infinity` і ніколи не завершується. Init-контейнери повинні завершитися (вийти з кодом 0), щоб основні контейнери запустилися.

**Виправлення**: Змініть команду init-контейнера на таку, що завершується:

```yaml
initContainers:
- name: init
  image: busybox
  command: ["echo", "Init done"]
```

</details>

---

### Запитання 10: PVC та Під
**[3 хвилини]**

Створіть PVC з назвою `data-pvc`, що запитує 100Mi сховища.

Потім створіть Під з назвою `storage-pod`, який:
- Використовує образ nginx
- Монтує PVC у `/data`

Запишіть файл у `/data/test.txt` для перевірки збереження.

<details>
<summary>Відповідь</summary>

```bash
# Створити PVC
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 100Mi
EOF

# Створити Під
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: data-pvc
EOF

# Перевірка
k exec storage-pod -- sh -c "echo 'persistent' > /data/test.txt"
k exec storage-pod -- cat /data/test.txt
```

</details>

---

## Оцінювання

| Правильних відповідей | Бал | Статус |
|-----------------------|-----|--------|
| 10/10 | 100% | Відмінно — готові до іспиту |
| 8–9/10 | 80–90% | Добре — потрібне незначне повторення |
| 6–7/10 | 60–70% | Повторіть слабкі теми |
| <6/10 | <60% | Перегляньте модулі Частини 1 |

---

## Очищення

```bash
k delete pod broken sidecar-pod init-pod web-server secret-pod storage-pod broken-multi 2>/dev/null
k delete job backup-job parallel-job 2>/dev/null
k delete cronjob cleanup 2>/dev/null
k delete cm web-content 2>/dev/null
k delete secret db-creds 2>/dev/null
k delete pvc data-pvc 2>/dev/null
```

---

## Наступна частина

[Частина 2: Розгортання застосунків](/uk/k8s/ckad/part2-deployment/module-2.1-deployments/) — Деплойменти, Helm, Kustomize та стратегії розгортання.
