---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 4.1: \u0422\u043e\u043c\u0438 (Volumes)"
slug: uk/k8s/cka/part4-storage/module-4.1-volumes
sidebar: 
  order: 2
lab: 
  id: cka-4.1-volumes
  url: https://killercoda.com/kubedojo/scenario/cka-4.1-volumes
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Основа для всіх концепцій зберігання даних
>
> **Час на виконання**: 35–45 хвилин
>
> **Передумови**: Модуль 2.1 (Поди), Модуль 2.7 (ConfigMaps та Secrets)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Налаштувати** emptyDir, hostPath та projected volumes і пояснити, коли використовувати кожен
- **Змонтувати** томи в контейнери за конкретними шляхами з доступом тільки для читання або читання-запису
- **Пояснити** життєвий цикл томів (прив'язаний до пода, не до контейнера) та гарантії збереження даних
- **Дебажити** збої монтування томів, перевіряючи події, шляхи та дозволи

---

## Чому цей модуль важливий

Контейнери є ефемерними — коли вони перезапускаються, всі дані втрачаються. Томи вирішують цю проблему, надаючи постійне або спільне сховище, яке переживає перезапуски контейнерів. На іспиті CKA вам потрібно буде налаштовувати різні типи томів для обміну даними між контейнерами, кешування тимчасових файлів та впровадження конфігурації.

> **Аналогія з картотечною шафою**
>
> Уявіть контейнер як робочий стіл зі шухлядами, які спорожнюються щоразу, коли ви йдете з роботи. Том — це як картотечна шафа в кутку — вона зберігає ваші файли навіть коли вас немає. Деякі шафи спільні між столами (emptyDir), деякі — це загальне сховище будівлі (PV), а деякі — просто дзеркала корпоративного довідника (configMap/secret projected volumes).

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Розуміти, навіщо потрібні томи
- Використовувати emptyDir для тимчасового спільного сховища
- Використовувати hostPath для сховища на рівні вузла (та знати його ризики)
- Використовувати projected volumes для впровадження конфігурації
- Розуміти життєвий цикл томів та коли дані зберігаються

---

## Чи знали ви?

- **emptyDir у пам'яті**: Ви можете підтримувати emptyDir оперативною пам'яттю замість диска за допомогою `medium: Memory` — чудово для конфіденційних тимчасових файлів, які ніколи не повинні потрапляти на диск
- **Projected volumes поєднують 4 джерела**: configMap, secret, downwardAPI та serviceAccountToken — усе це можна проєктувати в один каталог
- **hostPath заборонений у продакшені**: Більшість політик безпеки (включно з Pod Security Standards) блокують hostPath, оскільки він відкриває файлову систему вузла для подів

---

## Частина 1: Розуміння томів

### 1.1 Проблема зберігання даних у контейнерах

Контейнери мають ізольовану файлову систему. Коли контейнер падає і перезапускається:

```
┌──────────────────────────────────────────────────────────────┐
│ Перезапуск контейнера = Втрата даних                          │
│                                                               │
│   Контейнер v1             Контейнер v2 (після перезапуску)  │
│   ┌─────────────────┐       ┌─────────────────┐              │
│   │ /app            │       │ /app            │              │
│   │ ├── config.yml  │  ──→  │ ├── config.yml  │ (з образу)   │
│   │ └── data/       │       │ └── data/       │              │
│   │     └── cache   │       │     └── (пусто!)│              │
│   └─────────────────┘       └─────────────────┘              │
│                                                               │
│   Дані часу виконання ЗНИКЛИ після перезапуску                │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Як томи вирішують цю проблему

Томи надають сховище, яке існує поза файловою системою контейнера:

```
┌──────────────────────────────────────────────────────────────┐
│ З томами = Дані зберігаються                                  │
│                                                               │
│   Контейнер v1             Контейнер v2 (після перезапуску)  │
│   ┌─────────────────┐       ┌─────────────────┐              │
│   │ /app            │       │ /app            │              │
│   │ ├── config.yml  │       │ ├── config.yml  │              │
│   │ └── data/ ──────┼───┐   │ └── data/ ──────┼───┐          │
│   └─────────────────┘   │   └─────────────────┘   │          │
│                         │                         │          │
│                         ▼                         ▼          │
│                    ┌────────────────────────────────┐        │
│                    │        Том (спільний)           │        │
│                    │    └── cache (все ще тут!)     │        │
│                    └────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

### 1.3 Огляд типів томів

| Тип тому | Час життя | Використання | Збереження даних |
|----------|-----------|--------------|------------------|
| emptyDir | Час життя Пода | Тимчасове сховище, обмін між контейнерами | Втрачається при видаленні Пода |
| hostPath | Час життя вузла | Дані рівня вузла, DaemonSets | Зберігається на вузлі |
| configMap | Час життя ConfigMap | Файли конфігурації | Керується ConfigMap |
| secret | Час життя Secret | Облікові дані | Керується Secret |
| projected | Час життя джерела | Кілька джерел в одному монтуванні | Залежить від джерел |
| persistentVolumeClaim | Час життя PV | Постійні дані | Переживає видалення Пода |
| image | Час життя образу | Вміст OCI-образу як том тільки для читання (K8s 1.35+) | Тільки для читання, завантажується з реєстру |

> **Нове в K8s 1.35: Image Volumes (GA)**
>
> Image volumes дозволяють завантажити OCI-образ з реєстру та змонтувати його вміст безпосередньо як том тільки для читання. Жодних init-контейнерів або bootstrap-скриптів не потрібно. Ідеально для ML-моделей, пакетів конфігурації або статичних ресурсів:
>
> ```yaml
> volumes:
> - name: model-data
>   image:
>     reference: registry.example.com/ml-models/bert:v2
>     pullPolicy: IfNotPresent
> ```

---

## Частина 2: Томи emptyDir

### 2.1 Що таке emptyDir?

Том emptyDir створюється, коли Под призначається на вузол, і існує доки Под працює на цьому вузлі. Він починається порожнім — звідси й назва.

**Ключові характеристики**:
- Створюється при запуску Пода на вузлі
- Видаляється, коли Под видаляється з вузла (з будь-якої причини)
- Спільний для всіх контейнерів у Поді
- Може бути підтриманий диском або пам'яттю (tmpfs)

### 2.2 Базове використання emptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-data
spec:
  containers:
  - name: writer
    image: busybox
    command: ['sh', '-c', 'echo "Hello from writer" > /data/message; sleep 3600']
    volumeMounts:
    - name: shared-storage
      mountPath: /data
  - name: reader
    image: busybox
    command: ['sh', '-c', 'sleep 5; cat /data/message; sleep 3600']
    volumeMounts:
    - name: shared-storage
      mountPath: /data
  volumes:
  - name: shared-storage
    emptyDir: {}
```

### 2.3 emptyDir з підтримкою пам'яттю

Для конфіденційних тимчасових даних або швидшого введення-виведення:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: memory-backed
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'sleep 3600']
    volumeMounts:
    - name: tmpfs-volume
      mountPath: /cache
  volumes:
  - name: tmpfs-volume
    emptyDir:
      medium: Memory        # Використовує RAM замість диска
      sizeLimit: 100Mi      # Важливо! Обмежте використання пам'яті
```

**Коли використовувати emptyDir з підтримкою пам'яттю**:
- Тимчасові облікові дані, які не повинні потрапляти на диск
- Високошвидкісне кешування
- Тимчасовий простір для обчислень

**Увага**: Томи з підтримкою пам'яттю враховуються в ліміті пам'яті контейнера!

### 2.4 Обмеження розміру emptyDir

```yaml
volumes:
- name: cache
  emptyDir:
    sizeLimit: 500Mi    # Обмежити використання диска
```

Якщо Под перевищить обмеження розміру, його буде витіснено.

---

## Частина 3: Томи hostPath

### 3.1 Що таке hostPath?

hostPath монтує файл або каталог з файлової системи хост-вузла до Пода.

```
┌─────────────────────────────────────────────────────────────┐
│                         Вузол                                │
│                                                              │
│   Файлова система вузла    Под                               │
│   ┌─────────────────┐       ┌─────────────────────────┐     │
│   │ /var/log/       │       │  Контейнер              │     │
│   │   └── pods/     │◄──────│  /host-logs/ ◄────┐     │     │
│   │       └── *.log │       │                   │     │     │
│   └─────────────────┘       │  volumeMounts:    │     │     │
│                             │    mountPath:     │     │     │
│   /data/                    │      /host-logs ──┘     │     │
│   └── myapp/        ◄───────│                         │     │
│       └── config    │       └─────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Конфігурація hostPath

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-example
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /host-data; sleep 3600']
    volumeMounts:
    - name: host-volume
      mountPath: /host-data
      readOnly: true           # Хороша практика для безпеки
  volumes:
  - name: host-volume
    hostPath:
      path: /var/log           # Шлях на вузлі
      type: Directory          # Має бути каталогом
```

### 3.3 Типи hostPath

| Тип | Поведінка |
|-----|-----------|
| `""` (порожній) | Жодних перевірок перед монтуванням |
| `DirectoryOrCreate` | Створити каталог, якщо відсутній |
| `Directory` | Має існувати, має бути каталогом |
| `FileOrCreate` | Створити файл, якщо відсутній |
| `File` | Має існувати, має бути файлом |
| `Socket` | Має існувати, має бути UNIX-сокетом |
| `CharDevice` | Має існувати, має бути символьним пристроєм |
| `BlockDevice` | Має існувати, має бути блоковим пристроєм |

### 3.4 Ризики безпеки hostPath

**Чому hostPath є небезпечним**:

```yaml
# НЕБЕЗПЕЧНО — Ніколи не робіть цього у продакшені!
volumes:
- name: root-access
  hostPath:
    path: /                    # Доступ до всієї файлової системи вузла!
    type: Directory
```

**Ризики**:
- Втеча контейнера на вузол
- Читання конфіденційних файлів вузла (/etc/shadow, облікові дані kubelet)
- Запис шкідливих файлів на вузол
- Зміна конфігурації вузла

**Безпечне використання hostPath**:
- DaemonSets, яким потрібен доступ до вузла (збирачі логів, агенти моніторингу)
- Налагодження на рівні вузла (тимчасово)
- Доступ до Docker-сокета для CI/CD (використовуйте з крайньою обережністю)

### 3.5 hostPath у DaemonSets

Легітимне використання hostPath — збір логів:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      name: log-collector
  template:
    metadata:
      labels:
        name: log-collector
    spec:
      containers:
      - name: collector
        image: fluentd:latest
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true          # Тільки для читання заради безпеки
        - name: containers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
          type: Directory
      - name: containers
        hostPath:
          path: /var/lib/docker/containers
          type: Directory
```

---

## Частина 4: Projected Volumes

### 4.1 Що таке Projected Volumes?

Projected volumes поєднують кілька джерел томів в один каталог. Це корисно, коли вам потрібні configMaps, secrets та дані downwardAPI в одному місці.

```
┌──────────────────────────────────────────────────────────────┐
│ Projected Volume                                              │
│                                                               │
│   Джерела:                        Точка монтування:           │
│   ┌─────────────┐                 /etc/config/                │
│   │ ConfigMap A │─────┐           ├── app.conf     (з A)      │
│   └─────────────┘     │           ├── db.conf      (з A)      │
│   ┌─────────────┐     │           ├── password     (з B)      │
│   │ Secret B    │─────┼────────→  ├── api-key      (з B)      │
│   └─────────────┘     │           ├── labels       (з C)      │
│   ┌─────────────┐     │           └── annotations  (з C)      │
│   │ DownwardAPI │─────┘                                       │
│   └─────────────┘                                             │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Конфігурація Projected Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-volume-demo
  labels:
    app: demo
    version: v1
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls -la /etc/config; sleep 3600']
    volumeMounts:
    - name: all-config
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: all-config
    projected:
      sources:
      # Джерело 1: ConfigMap
      - configMap:
          name: app-config
          items:
          - key: app.properties
            path: app.conf
      # Джерело 2: Secret
      - secret:
          name: app-secrets
          items:
          - key: password
            path: credentials/password
      # Джерело 3: Downward API
      - downwardAPI:
          items:
          - path: labels
            fieldRef:
              fieldPath: metadata.labels
          - path: cpu-limit
            resourceFieldRef:
              containerName: app
              resource: limits.cpu
```

### 4.3 Проєктування токена Service Account

Сучасний Kubernetes використовує проєктовані токени service account замість застарілих токенів:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: service-account-projection
spec:
  serviceAccountName: my-service-account
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
      readOnly: true
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600     # Короткоживучий токен
          audience: api               # Цільова аудиторія
```

### 4.4 Випадки використання Projected Volume

| Випадок використання | Поєднані джерела |
|---------------------|------------------|
| Пакет конфігурації додатка | configMap + secret |
| Ідентифікація Пода | serviceAccountToken + downwardAPI |
| Повне впровадження конфігурації | configMap + secret + downwardAPI |
| Конфігурація sidecar | Кілька configMaps |

---

## Частина 5: Томи ConfigMap та Secret

### 5.1 ConfigMap як том

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
      listen 80;
      location / {
        root /usr/share/nginx/html;
      }
    }
---
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: nginx-config
      # Опціонально: вибрати конкретні ключі
      items:
      - key: nginx.conf
        path: default.conf     # Перейменувати файл
```

### 5.2 Secret як том

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-certs
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
---
apiVersion: v1
kind: Pod
metadata:
  name: tls-app
spec:
  containers:
  - name: app
    image: nginx:1.25
    volumeMounts:
    - name: certs
      mountPath: /etc/tls
      readOnly: true
  volumes:
  - name: certs
    secret:
      secretName: tls-certs
      defaultMode: 0400       # Обмежені дозволи
```

### 5.3 Автооновлення для томів ConfigMap/Secret

Коли змонтовані як томи (не змінні середовища), ConfigMaps та Secrets оновлюються автоматично:

```
┌──────────────────────────────────────────────────────────────┐
│ Поведінка оновлення                                           │
│                                                               │
│ ConfigMap/Secret оновлено ───→ Том оновлено (протягом ~1 хв) │
│                                                               │
│ ⚠️  Застереження:                                             │
│     • Використовує атомарну заміну через symlink              │
│     • subPath монтування НЕ оновлюються автоматично           │
│     • Додаток повинен виявити зміни та перезавантажитись       │
│     • Період синхронізації kubelet впливає на затримку        │
└──────────────────────────────────────────────────────────────┘
```

### 5.4 Монтування subPath (без автооновлення)

Коли потрібно змонтувати один файл у існуючий каталог:

```yaml
volumeMounts:
- name: config
  mountPath: /etc/nginx/nginx.conf    # Один файл
  subPath: nginx.conf                  # Ключ із ConfigMap
  readOnly: true
```

**Увага**: Монтування subPath не отримують оновлень при зміні ConfigMap/Secret!

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| emptyDir для постійних даних | Дані втрачаються при видаленні Пода | Використовуйте PVC |
| hostPath у продакшені | Вразливість безпеки | Використовуйте PVC або уникайте повністю |
| Немає sizeLimit на emptyDir | Под може заповнити диск вузла | Завжди встановлюйте sizeLimit |
| subPath з очікуванням оновлень | Зміни конфігурації не відображаються | Використовуйте повне монтування або перезапустіть Под |
| Memory emptyDir без ліміту | OOM kills | Встановіть sizeLimit, враховуйте в ліміті пам'яті |
| hostPath type: "" | Жодної валідації, тихі збої | Використовуйте явний тип, наприклад Directory |

---

## Тест

### Q1: Час життя тому
Що станеться з даними emptyDir, коли контейнер падає, але Под продовжує працювати?

<details>
<summary>Відповідь</summary>

Дані emptyDir **зберігаються**. Час життя emptyDir прив'язаний до Пода, а не до контейнера. Лише коли Под видаляється або витісняється з вузла, emptyDir видаляється.

</details>

### Q2: emptyDir з підтримкою пам'яттю
Що є ключовим фактором при використанні `emptyDir.medium: Memory`?

<details>
<summary>Відповідь</summary>

emptyDir з підтримкою пам'яттю враховується в ліміті пам'яті контейнера. Необхідно встановити sizeLimit, щоб запобігти проблемам з OOM, і загальний обсяг повинен вміщуватись у виділену пам'ять Пода.

</details>

### Q3: Безпека hostPath
Чому тип hostPath `""` (порожній рядок) є ризикованим?

<details>
<summary>Відповідь</summary>

Тип `""` не виконує жодних перевірок перед монтуванням. Шлях може не існувати, може бути неправильного типу (файл замість каталогу) або може бути символічним посиланням на неочікуване місце. Використовуйте явні типи, такі як `Directory` або `File`, для валідації.

</details>

### Q4: Джерела Projected Volume
Назвіть чотири типи джерел, які можна поєднати в projected volume.

<details>
<summary>Відповідь</summary>

1. **configMap** — дані ConfigMap
2. **secret** — дані Secret
3. **downwardAPI** — метадані Пода та інформація про ресурси
4. **serviceAccountToken** — проєктовані токени service account

</details>

### Q5: Автооновлення ConfigMap
ConfigMap змонтований як том. Ви оновлюєте ConfigMap. Що повинен зробити додаток?

<details>
<summary>Відповідь</summary>

Додаток повинен **виявити зміни та перезавантажити** конфігурацію. Хоча Kubernetes автоматично оновлює файли в змонтованому томі (протягом ~1 хвилини), додаток повинен відстежувати зміни та перезавантажуватись — це не відбувається автоматично. Як альтернатива — перезапустіть Под для застосування змін.

</details>

### Q6: Поведінка subPath
Навіщо використовувати subPath і який компроміс?

<details>
<summary>Відповідь</summary>

Використовуйте subPath для монтування одного файлу з ConfigMap/Secret у існуючий каталог без перезапису інших файлів. Компроміс полягає в тому, що монтування subPath **не оновлюються автоматично** при зміні джерела — потрібно перезапустити Под.

</details>

---

## Практична вправа: Обмін даними між контейнерами через томи

### Сценарій
Створіть Под з двома контейнерами, які обмінюються даними через томи. Один контейнер записує логи, інший їх обробляє.

### Налаштування

```bash
# Створити namespace
k create ns volume-lab

# Створити мультиконтейнерний Под
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: log-processor
  namespace: volume-lab
spec:
  containers:
  # Контейнер-записувач — генерує логи
  - name: writer
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      i=0
      while true; do
        echo "\$(date): Log entry \$i" >> /logs/app.log
        i=\$((i+1))
        sleep 5
      done
    volumeMounts:
    - name: log-volume
      mountPath: /logs
  # Контейнер-читач — обробляє логи
  - name: reader
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      echo "Waiting for logs..."
      sleep 10
      tail -f /logs/app.log
    volumeMounts:
    - name: log-volume
      mountPath: /logs
      readOnly: true
  volumes:
  - name: log-volume
    emptyDir:
      sizeLimit: 50Mi
EOF
```

### Завдання

1. **Перевірте, що Под працює**:
```bash
k get pod log-processor -n volume-lab
```

2. **Перевірте, що записувач створює логи**:
```bash
k exec -n volume-lab log-processor -c writer -- cat /logs/app.log
```

3. **Перевірте, що читач бачить логи**:
```bash
k logs -n volume-lab log-processor -c reader
```

4. **Перевірте спільний доступ до тому**:
```bash
# Записати від записувача
k exec -n volume-lab log-processor -c writer -- sh -c 'echo "TEST MESSAGE" >> /logs/app.log'

# Прочитати від читача
k exec -n volume-lab log-processor -c reader -- tail -1 /logs/app.log
```

5. **Перевірте розташування emptyDir на вузлі** (для розуміння):
```bash
k get pod log-processor -n volume-lab -o jsonpath='{.status.hostIP}'
# emptyDir знаходиться в /var/lib/kubelet/pods/<pod-uid>/volumes/kubernetes.io~empty-dir/log-volume
```

### Критерії успіху
- [ ] Под працює з обома контейнерами
- [ ] Записувач створює записи логів кожні 5 секунд
- [ ] Читач бачить логи, записані записувачем
- [ ] Дані зберігаються після перезапуску контейнера (перевірте за допомогою `k exec ... -- kill 1`)

### Додатковий виклик

Додайте третій контейнер, який моніторить використання диска спільного тому та записує попередження, коли використання перевищує 80%.

### Очищення

```bash
k delete ns volume-lab
```

---

## Практичні вправи

Практикуйте ці сценарії для готовності до іспиту:

### Вправа 1: Створити Под з emptyDir (2 хв)
```bash
# Завдання: Створити Под з томом emptyDir, змонтованим у /cache
# Підказка: k run cache-pod --image=busybox --dry-run=client -o yaml > pod.yaml
# Потім додайте секцію volumes
```

### Вправа 2: emptyDir з підтримкою пам'яттю (2 хв)
```bash
# Завдання: Створити emptyDir з підтримкою RAM та лімітом 64Mi
# Ключові поля: emptyDir.medium: Memory, emptyDir.sizeLimit: 64Mi
```

### Вправа 3: hostPath тільки для читання (2 хв)
```bash
# Завдання: Змонтувати /var/log з хоста як том тільки для читання
# Важливо: Завжди використовуйте readOnly: true для hostPath, коли можливо
```

### Вправа 4: Projected Volume (3 хв)
```bash
# Завдання: Створити projected volume, що поєднує:
# - ConfigMap "app-config"
# - Secret "app-secrets"
# Змонтувати у /etc/app
```

### Вправа 5: Том ConfigMap з Items (2 хв)
```bash
# Завдання: Змонтувати лише ключ "app.conf" з ConfigMap як "config.yaml"
# Використовуйте configMap.items для вибору та перейменування
```

### Вправа 6: Монтування subPath (2 хв)
```bash
# Завдання: Змонтувати один файл з ConfigMap у /etc/myapp/config.yaml
# Без перезапису інших файлів у /etc/myapp
```

### Вправа 7: Обмін томами між контейнерами (3 хв)
```bash
# Завдання: Створити Под з 2 контейнерами, що спільно використовують emptyDir
# Контейнер 1 записує у /shared/data.txt
# Контейнер 2 читає з /shared/data.txt
```

### Вправа 8: Налагодження проблем монтування томів (2 хв)
```bash
# Дано: Под застряг у стані ContainerCreating
# Завдання: Визначити, чи це проблема монтування тому
# Команди: k describe pod, перевірте секцію Events
```

---

## Наступний модуль

Переходьте до [Модуль 4.2: PersistentVolumes та PersistentVolumeClaims](module-4.2-pv-pvc/), щоб дізнатися про постійне сховище, яке переживає видалення Пода.
