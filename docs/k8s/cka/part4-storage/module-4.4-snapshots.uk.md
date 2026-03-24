# Модуль 4.4: Знімки томів та клонування

> **Складність**: `[MEDIUM]` — Захист даних та клонування
>
> **Час на виконання**: 30–40 хвилин
>
> **Передумови**: Модуль 4.2 (PV та PVC), Модуль 4.3 (StorageClasses)

---

## Чому цей модуль важливий

Знімки томів надають копії ваших постійних даних на певний момент часу — це важливо для резервного копіювання, аварійного відновлення та створення тестових середовищ. Клонування томів дозволяє створювати нові томи з існуючих. На іспиті CKA можуть перевіряти ваше розуміння цих примітивів захисту даних, особливо оскільки вони стають все поширенішими у продакшен-середовищах Kubernetes.

> **Аналогія з фотоапаратом**
>
> Уявіть VolumeSnapshot як фотографію ваших даних у конкретний момент. Фото фіксує саме те, як виглядав ваш диск у цю мить. Пізніше ви можете використати це фото для відновлення диска до точного стану або створити новий диск, який починається як копія того моменту. VolumeSnapshotClass — це як налаштування фотоапарата — він визначає, як знімок створюється та зберігається.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Розуміти архітектуру знімків (VolumeSnapshotClass, VolumeSnapshot, VolumeSnapshotContent)
- Створювати VolumeSnapshots з існуючих PVC
- Відновлювати томи зі знімків
- Клонувати томи за допомогою dataSource
- Розуміти вимоги CSI для знімків

---

## Чи знали ви?

- **Знімки є інкрементальними**: Більшість бекендів сховища зберігають знімки як різницю від оригіналу, заощаджуючи місце
- **CSI є обов'язковим**: Застарілі вбудовані (in-tree) плагіни томів не підтримують знімки — вам потрібні CSI-драйвери
- **Copy-on-write**: Багато систем зберігання використовують CoW для знімків, що робить їх створення майже миттєвим
- **Відновлення між namespace**: VolumeSnapshotContent має область видимості кластера, що дозволяє реалізувати сценарії аварійного відновлення

---

## Частина 1: Архітектура знімків

### 1.1 Три ресурси знімків

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Архітектура знімків                                │
│                                                                       │
│   Подібно до моделі PV/PVC:                                          │
│                                                                       │
│   VolumeSnapshotClass         VolumeSnapshot        VolumeSnapshot   │
│   (область кластера)          (у namespace)         Content          │
│   ┌─────────────────┐         ┌─────────────┐      (область кластера)│
│   │ Визначає ЯК     │         │ Запит на    │      ┌─────────────┐  │
│   │ створюються     │         │ знімок      │      │ Фактичне    │  │
│   │ знімки          │◄────────│ конкретного │─────►│ посилання   │  │
│   │                 │         │ PVC         │      │ на знімок   │  │
│   │ - driver        │         │ - source    │      │             │  │
│   │ - deletionPolicy│         │ - class     │      │ - driver    │  │
│   └─────────────────┘         └─────────────┘      │ - handle    │  │
│                                                     └─────────────┘  │
│                                                                       │
│   Адмін створює               Розробник створює    Створюється       │
│   (раз на кластер)            (за потреби)         автоматично       │
│                                                    (контролером)     │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 Як це відповідає PV/PVC

| Зберігання | Знімки |
|------------|--------|
| StorageClass | VolumeSnapshotClass |
| PersistentVolume | VolumeSnapshotContent |
| PersistentVolumeClaim | VolumeSnapshot |

### 1.3 Передумови

Перед використанням знімків вам потрібно:
1. **CSI-драйвер**, що підтримує знімки (не всі підтримують)
2. **Контролер знімків**, розгорнутий у кластері
3. **CRD для знімків** встановлені
4. **VolumeSnapshotClass** створений

```bash
# Перевірити, чи встановлені CRD для знімків
k get crd | grep snapshot
# volumesnapshotclasses.snapshot.storage.k8s.io
# volumesnapshotcontents.snapshot.storage.k8s.io
# volumesnapshots.snapshot.storage.k8s.io

# Перевірити наявність контролера знімків
k get pods -n kube-system | grep snapshot
```

---

## Частина 2: VolumeSnapshotClass

### 2.1 Створення VolumeSnapshotClass

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
  annotations:
    snapshot.storage.kubernetes.io/is-default-class: "true"  # Опціонально
driver: ebs.csi.aws.com                    # Має збігатися з CSI-драйвером
deletionPolicy: Delete                      # Delete або Retain
parameters:                                 # Параметри, специфічні для драйвера
  # Приклад для деяких драйверів:
  # csi.storage.k8s.io/snapshotter-secret-name: snap-secret
  # csi.storage.k8s.io/snapshotter-secret-namespace: default
```

### 2.2 Політики видалення

| Політика | Поведінка |
|----------|----------|
| Delete | VolumeSnapshotContent та базовий знімок видаляються при видаленні VolumeSnapshot |
| Retain | VolumeSnapshotContent та знімок зберігаються після видалення VolumeSnapshot |

### 2.3 Приклади для хмарних провайдерів

**AWS EBS CSI**:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
```

**GCP PD CSI**:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: gcp-snapclass
driver: pd.csi.storage.gke.io
deletionPolicy: Delete
parameters:
  storage-locations: us-central1
```

**Azure Disk CSI**:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: azure-snapclass
driver: disk.csi.azure.com
deletionPolicy: Delete
parameters:
  incremental: "true"
```

---

## Частина 3: Створення знімків

### 3.1 Створення VolumeSnapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: data-snapshot
  namespace: production
spec:
  volumeSnapshotClassName: csi-snapclass   # Посилання на клас
  source:
    persistentVolumeClaimName: data-pvc    # PVC для знімка
```

### 3.2 Процес створення знімка

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Процес створення знімка                         │
│                                                                      │
│   1. Створити VolumeSnapshot                                        │
│          │                                                          │
│          ▼                                                          │
│   2. Контролер знімків перевіряє                                    │
│      - PVC існує                                                    │
│      - VolumeSnapshotClass існує                                    │
│      - CSI-драйвер підтримує знімки                                │
│          │                                                          │
│          ▼                                                          │
│   3. CSI-драйвер створює знімок на бекенді сховища                 │
│          │                                                          │
│          ▼                                                          │
│   4. VolumeSnapshotContent створено (автоматично)                   │
│          │                                                          │
│          ▼                                                          │
│   5. Статус VolumeSnapshot: readyToUse=true                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Перевірка статусу знімка

```bash
# Список знімків
k get volumesnapshot -n production
# NAME            READYTOUSE   SOURCEPVC   SOURCESNAPSHOTCONTENT   RESTORESIZE   SNAPSHOTCLASS
# data-snapshot   true         data-pvc                           10Gi          csi-snapclass

# Детальний статус
k describe volumesnapshot data-snapshot -n production

# Перевірити VolumeSnapshotContent
k get volumesnapshotcontent
```

### 3.4 Поля статусу знімка

```yaml
status:
  boundVolumeSnapshotContentName: snapcontent-xxxxx
  creationTime: "2024-01-15T10:30:00Z"
  readyToUse: true                        # Знімок готовий
  restoreSize: 10Gi                       # Розмір при відновленні
  error:                                  # Якщо невдача, тут повідомлення про помилку
```

---

## Частина 4: Відновлення зі знімків

### 4.1 Створення PVC зі знімка

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-data
  namespace: production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd              # StorageClass для нового PVC
  resources:
    requests:
      storage: 10Gi                       # Має бути >= розміру знімка
  dataSource:                             # Ключова частина!
    name: data-snapshot                   # Ім'я VolumeSnapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### 4.2 Процес відновлення

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Відновлення зі знімка                           │
│                                                                      │
│   VolumeSnapshot                    Новий PVC                        │
│   ┌─────────────┐                   ┌─────────────┐                 │
│   │ data-snap   │                   │ restored    │                 │
│   │             │                   │             │                 │
│   │ restoreSize:│◄──dataSource──────│ storage:    │                 │
│   │ 10Gi        │                   │ 10Gi        │                 │
│   └──────┬──────┘                   └──────┬──────┘                 │
│          │                                 │                         │
│          ▼                                 ▼                         │
│   VolumeSnapshotContent             Новий PV (з даними)             │
│   (містить дескриптор               (наданий зі                     │
│    знімка)                           знімка)                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Відновлення між namespace

VolumeSnapshotContent має область видимості кластера, тому можна відновлювати в різних namespace:

```yaml
# У namespace "dr-test"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dr-restore
  namespace: dr-test              # Інший namespace!
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
  dataSourceRef:                  # Використовуйте dataSourceRef для між-namespace
    name: data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
    namespace: production         # Вихідний namespace
```

**Примітка**: Відновлення між namespace потребує Kubernetes 1.26+ та відповідного RBAC.

---

## Частина 5: Клонування томів

### 5.1 Що таке клонування томів?

Клонування створює новий PVC з даними з існуючого PVC без попереднього створення знімка.

```
┌─────────────────────────────────────────────────────────────────────┐
│               Знімок vs Клон                                        │
│                                                                      │
│   ЗНІМОК                             КЛОН                           │
│   ──────                             ────                            │
│   PVC → Знімок → Новий PVC          PVC → Новий PVC (напряму)      │
│                                                                      │
│   Двокроковий процес                 Однокроковий процес            │
│   Резервна копія на момент часу      Негайна копія                  │
│   Можна відновити багато разів       Одна операція копіювання       │
│   Знімок зберігається               Немає проміжного артефакту     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Створення клону

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cloned-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi                 # Має бути >= вихідного PVC
  dataSource:                       # Клонування з існуючого PVC
    name: source-pvc                # Ім'я вихідного PVC
    kind: PersistentVolumeClaim     # Інший kind, ніж для знімка!
```

### 5.3 Вимоги до клонування

- Джерело та клон повинні бути в **одному namespace**
- Бекенд сховища повинен підтримувати клонування
- Розмір клону має бути >= розміру джерела
- Зазвичай потрібен той самий StorageClass

### 5.4 Випадки використання клонування

| Випадок використання | Опис |
|---------------------|------|
| Середовища dev/test | Клонування продакшен-даних для тестування |
| Резервні копії перед оновленням | Клонування перед ризикованими змінами |
| Аналіз даних | Клон для аналітики без впливу на продакшен |
| Паралельна обробка | Кілька клонів для паралельних навантажень |

---

## Частина 6: Найкращі практики

### 6.1 Стратегія резервного копіювання

```yaml
# Створення знімків за розкладом за допомогою CronJob або зовнішнього інструменту
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: daily-backup-2024-01-15
  labels:
    backup-type: daily
    source-pvc: database-data
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: database-data
```

### 6.2 Зберігання знімків

```bash
# Очищення старих знімків (концепція скрипта)
# Зберігати останні 7 щоденних, 4 щотижневих, 12 щомісячних

# Список знімків старших за 7 днів з міткою daily
k get volumesnapshot -l backup-type=daily --sort-by=.metadata.creationTimestamp
```

### 6.3 Консистентність додатків

Для консистентних знімків:
1. **Призупиніть запис** перед знімком (якщо можливо)
2. **Скиньте буфери** на диск
3. **Зробіть знімок** швидко
4. **Відновіть запис**

```bash
# Приклад: MySQL flush перед знімком
k exec mysql-pod -- mysql -e "FLUSH TABLES WITH READ LOCK;"
# Створіть знімок тут
k exec mysql-pod -- mysql -e "UNLOCK TABLES;"
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Немає CSI-драйвера | Знімки не підтримуються | Встановіть CSI-драйвер з підтримкою знімків |
| Відсутні CRD для знімків | Ресурс VolumeSnapshot невідомий | Встановіть CRD для знімків |
| Неправильний driver у SnapshotClass | Знімок тихо не вдається | Узгодьте driver з іменем CSI-драйвера |
| Розмір відновлення замалий | PVC не надається | Використовуйте розмір >= restoreSize |
| Клонування між namespace | Не дозволено | Клони повинні бути в тому самому namespace, що й джерело |
| Видалення вихідного PVC | Клони можуть зазнати невдачі | Переконайтесь, що клон завершено перед видаленням джерела |

---

## Тест

### Q1: Знімок vs Клон
Яка ключова різниця між відновленням зі знімка та клонуванням PVC?

<details>
<summary>Відповідь</summary>

**Відновлення зі знімка** використовує VolumeSnapshot як посередника — ви створюєте знімок, а потім створюєте новий PVC з цього знімка. Знімок зберігається і може бути використаний багаторазово.

**Клонування** створює новий PVC безпосередньо з існуючого PVC без проміжного знімка. Це однокроковий процес без постійного артефакту.

</details>

### Q2: Призначення VolumeSnapshotClass
Яку роль відіграє VolumeSnapshotClass?

<details>
<summary>Відповідь</summary>

VolumeSnapshotClass визначає **як** створюються знімки, подібно до того, як StorageClass визначає, як надаються PV. Він вказує:
- Який CSI-драйвер створює знімки
- Політику видалення (Delete або Retain)
- Параметри, специфічні для драйвера

</details>

### Q3: Передумови для знімків
Які три речі повинні бути встановлені, перш ніж ви зможете використовувати знімки томів?

<details>
<summary>Відповідь</summary>

1. **CRD для знімків** — визначення користувацьких ресурсів для VolumeSnapshot, VolumeSnapshotClass, VolumeSnapshotContent
2. **Контролер знімків** — відстежує ресурси VolumeSnapshot та керує життєвим циклом
3. **CSI-драйвер з підтримкою знімків** — фактичний драйвер, який створює знімки на бекенді сховища

</details>

### Q4: Відновлення між namespace
Чи можна відновити VolumeSnapshot в іншому namespace, ніж той, де він був створений?

<details>
<summary>Відповідь</summary>

**Так**, тому що VolumeSnapshotContent (який містить фактичне посилання на знімок) має область видимості кластера. Ви можете створити PVC в іншому namespace, який посилається на VolumeSnapshot за допомогою `dataSourceRef` з полем namespace (потрібен Kubernetes 1.26+).

</details>

### Q5: Поле dataSource
Яка різниця між використанням `kind: VolumeSnapshot` та `kind: PersistentVolumeClaim` у dataSource PVC?

<details>
<summary>Відповідь</summary>

- `kind: VolumeSnapshot` — відновлення зі знімка (створює новий том зі знімка)
- `kind: PersistentVolumeClaim` — клонування існуючого PVC (копіює дані напряму)

Обидва використовують поле dataSource, але створюють новий том по-різному.

</details>

---

## Практична вправа: Знімок та відновлення

### Передумови
Ця вправа потребує кластер з:
- CSI-драйвером, що підтримує знімки
- Встановленими контролером знімків та CRD

Якщо використовуєте kind або minikube, можливо, знадобиться встановити їх вручну.

### Завдання 1: Перевірити підтримку знімків

```bash
# Перевірити існування CRD
k get crd | grep snapshot

# Перевірити наявність VolumeSnapshotClass
k get volumesnapshotclass

# Якщо немає, потрібно створити на основі вашого CSI-драйвера
```

### Завдання 2: Створити тестові дані

```bash
# Створити namespace
k create ns snapshot-lab

# Створити PVC
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: source-data
  namespace: snapshot-lab
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard    # Використовуйте StorageClass вашого кластера
EOF

# Створити Под для запису даних
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-writer
  namespace: snapshot-lab
spec:
  containers:
  - name: writer
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Important data created at $(date)" > /data/important.txt; sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: source-data
EOF

# Зачекати, поки дані будуть записані
sleep 10
k exec -n snapshot-lab data-writer -- cat /data/important.txt
```

### Завдання 3: Створити VolumeSnapshotClass (за потреби)

```bash
# Приклад для AWS EBS CSI (змініть для вашого драйвера)
cat <<EOF | k apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com    # Змініть на ваш CSI-драйвер
deletionPolicy: Delete
EOF
```

### Завдання 4: Створити знімок

```bash
cat <<EOF | k apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: source-snapshot
  namespace: snapshot-lab
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: source-data
EOF

# Зачекати, поки знімок буде готовий
k get volumesnapshot -n snapshot-lab -w
# Зачекайте, поки READYTOUSE покаже "true"
```

### Завдання 5: "Пошкодити" оригінальні дані

```bash
# Імітувати втрату даних
k exec -n snapshot-lab data-writer -- sh -c 'echo "Corrupted!" > /data/important.txt'
k exec -n snapshot-lab data-writer -- cat /data/important.txt
# Показує: Corrupted!
```

### Завдання 6: Відновити зі знімка

```bash
# Видалити Под (щоб звільнити PVC)
k delete pod -n snapshot-lab data-writer

# Створити новий PVC зі знімка
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-data
  namespace: snapshot-lab
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 1Gi
  dataSource:
    name: source-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
EOF

# Створити Под для перевірки відновлених даних
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-reader
  namespace: snapshot-lab
spec:
  containers:
  - name: reader
    image: busybox:1.36
    command: ['sh', '-c', 'cat /data/important.txt; sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: restored-data
EOF

# Перевірити, що оригінальні дані відновлені
k logs -n snapshot-lab data-reader
# Має показати: Important data created at <оригінальна мітка часу>
```

### Критерії успіху
- [ ] VolumeSnapshotClass створено
- [ ] VolumeSnapshot показує readyToUse: true
- [ ] Новий PVC створено зі знімка
- [ ] Відновлені дані збігаються з оригіналом (не пошкоджена версія)

### Очищення

```bash
k delete ns snapshot-lab
k delete volumesnapshotclass csi-snapclass
```

---

## Практичні вправи

### Вправа 1: Список ресурсів знімків (1 хв)
```bash
# Завдання: Знайти всі ресурси, пов'язані зі знімками
k api-resources | grep snapshot
```

### Вправа 2: Створити VolumeSnapshotClass (2 хв)
```bash
# Завдання: Створити SnapshotClass для вашого CSI-драйвера з політикою Delete
```

### Вправа 3: Перевірити статус знімка (1 хв)
```bash
# Завдання: Перевірити, що знімок готовий до використання
k get volumesnapshot <name> -o jsonpath='{.status.readyToUse}'
```

### Вправа 4: Відновити зі знімка (2 хв)
```bash
# Завдання: Створити PVC зі знімка "backup-snap"
# Ключ: dataSource з kind: VolumeSnapshot
```

### Вправа 5: Клонувати PVC (2 хв)
```bash
# Завдання: Клонувати PVC "source-pvc" до "clone-pvc"
# Ключ: dataSource з kind: PersistentVolumeClaim
```

### Вправа 6: Знайти розмір знімка (1 хв)
```bash
# Завдання: Отримати розмір відновлення знімка
k get volumesnapshot <name> -o jsonpath='{.status.restoreSize}'
```

### Вправа 7: Перевірити VolumeSnapshotContent (1 хв)
```bash
# Завдання: Знайти VolumeSnapshotContent для VolumeSnapshot
k get volumesnapshot <name> -o jsonpath='{.status.boundVolumeSnapshotContentName}'
```

---

## Наступний модуль

Переходьте до [Модуль 4.5: Усунення несправностей зберігання](module-4.5-troubleshooting.uk.md), щоб дізнатися, як діагностувати та виправляти типові проблеми зберігання.
