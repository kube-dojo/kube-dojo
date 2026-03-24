# Модуль 4.3: StorageClasses та динамічне надання

> **Складність**: `[MEDIUM]` — Автоматизація надання сховища
>
> **Час на виконання**: 35–45 хвилин
>
> **Передумови**: Модуль 4.2 (PV та PVC), Модуль 1.2 (CSI)

---

## Чому цей модуль важливий

У Модулі 4.2 ви вручну створювали PersistentVolumes перед створенням PersistentVolumeClaims. Це не масштабується — уявіть адміністратора, який створює сотні PV для кожного запиту на сховище! StorageClasses забезпечують **динамічне надання**: створіть PVC, і Kubernetes автоматично надає базове сховище. На іспиті CKA перевіряють як розуміння StorageClasses, так і налаштування динамічного надання.

> **Аналогія з торговим автоматом**
>
> Уявіть статичне надання як замовлення меблів на замовлення — хтось повинен їх виготовити, перш ніж ви зможете ними скористатися. Динамічне надання — це як торговий автомат: ви обираєте, що хочете (StorageClass), вставляєте запит (PVC), і отримуєте сховище (PV). StorageClass — це торговий автомат — він знає, як виробляти різні типи сховища на вимогу.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Розуміти, як StorageClasses забезпечують динамічне надання
- Створювати та налаштовувати StorageClasses
- Встановлювати StorageClass за замовчуванням для кластера
- Використовувати параметри для налаштування наданого сховища
- Розуміти режими прив'язки томів
- Усувати проблеми динамічного надання

---

## Чи знали ви?

- **Хмарні кластери мають значення за замовчуванням**: GKE, EKS та AKS постачаються з попередньо налаштованими StorageClasses за замовчуванням, які надають хмарне сховище
- **kind/minikube теж мають provisioners**: Навіть локальні кластери включають динамічні provisioners (rancher.io/local-path для kind, k8s.io/minikube-hostpath для minikube)
- **StorageClasses є незмінними**: Після створення ви не можете змінити StorageClass — потрібно видалити та створити заново

---

## Частина 1: Розуміння StorageClasses

### 1.1 Статичне vs динамічне надання

```
┌──────────────────────────────────────────────────────────────────────┐
│               Статичне vs динамічне надання                           │
│                                                                       │
│   СТАТИЧНЕ (Ручне)                    ДИНАМІЧНЕ (Автоматичне)        │
│   ───────────────                     ────────────────────            │
│                                                                       │
│   1. Адмін створює PV                 1. Адмін створює StorageClass   │
│      │                                   │                            │
│      ▼                                   ▼                            │
│   2. Розробник створює PVC            2. Розробник створює PVC        │
│      │                                   │                            │
│      ▼                                   ▼                            │
│   3. Kubernetes прив'язує             3. Provisioner створює PV       │
│      PVC до існуючого PV                 │                            │
│                                          ▼                            │
│                                       4. Kubernetes прив'язує PVC    │
│                                          до нового PV                │
│                                                                       │
│   Плюс: Повний контроль              Плюс: Самообслуговування,      │
│   Мінус: Адмін — вузьке місце              масштабованість           │
│                                       Мінус: Менше контролю на том   │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 Компоненти StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"  # Опціонально
provisioner: kubernetes.io/aws-ebs    # Хто створює сховище
parameters:                            # Налаштування, специфічні для provisioner
  type: gp3
  iopsPerGB: "10"
reclaimPolicy: Delete                  # Що відбувається при видаленні PVC
volumeBindingMode: WaitForFirstConsumer  # Коли надавати
allowVolumeExpansion: true             # Чи можна змінити розмір пізніше?
mountOptions:                          # Параметри монтування для томів
  - debug
```

### 1.3 Поширені Provisioners

| Provisioner | Хмара/Платформа | Тип сховища |
|-------------|----------------|-------------|
| kubernetes.io/aws-ebs | AWS | Томи EBS |
| kubernetes.io/gce-pd | GCP | Persistent Disk |
| kubernetes.io/azure-disk | Azure | Managed Disk |
| kubernetes.io/azure-file | Azure | Azure Files |
| ebs.csi.aws.com | AWS (CSI) | EBS через CSI |
| pd.csi.storage.gke.io | GCP (CSI) | PD через CSI |
| rancher.io/local-path | kind | Локальний шлях |
| k8s.io/minikube-hostpath | minikube | Шлях хоста |

---

## Частина 2: Створення StorageClasses

### 2.1 Базовий StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

### 2.2 AWS EBS StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ebs
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iopsPerGB: "50"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789:key/abc-123"
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 2.3 GCP Persistent Disk StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd    # Для HA
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 2.4 Azure Disk StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium
provisioner: disk.csi.azure.com
parameters:
  storageaccounttype: Premium_LRS
  kind: Managed
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 2.5 Локальна розробка (kind/minikube)

**kind** (використовує local-path-provisioner):
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-path
provisioner: rancher.io/local-path
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

**minikube**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: k8s.io/minikube-hostpath
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

---

## Частина 3: StorageClass за замовчуванням

### 3.1 Встановлення за замовчуванням

Лише один StorageClass повинен бути за замовчуванням. Позначте його анотацією:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"  # Магічна анотація
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
```

Або змініть існуючий патчем:
```bash
k patch storageclass standard -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "true"}}}'
```

### 3.2 Перевірка StorageClass за замовчуванням

```bash
k get sc
# NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE
# standard (default)   kubernetes.io/aws-ebs   Delete          WaitForFirstConsumer
# fast-ssd             kubernetes.io/aws-ebs   Delete          Immediate
```

### 3.3 PVC без StorageClass

Коли PVC не вказує `storageClassName`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  # storageClassName не вказано — використовується за замовчуванням!
```

**Поведінка**:
- Якщо StorageClass за замовчуванням існує — використовується він, запускається динамічне надання
- Якщо за замовчуванням немає — PVC залишається Pending, поки не з'явиться відповідний PV

### 3.4 Відмова від динамічного надання

Щоб явно уникнути динамічного надання:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: static-only-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: ""    # Порожній рядок = без динамічного надання
```

---

## Частина 4: Режими прив'язки томів

### 4.1 Immediate vs WaitForFirstConsumer

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Режими прив'язки томів                              │
│                                                                       │
│   IMMEDIATE                         WAITFORFIRSTCONSUMER              │
│   ─────────                         ────────────────────              │
│                                                                       │
│   PVC створено                      PVC створено                     │
│       │                                 │                             │
│       ▼                                 ▼                             │
│   PV надано                         PVC залишається Pending           │
│   негайно                               │                             │
│       │                                 │                             │
│       │                             Под заплановано                   │
│       │                                 │                             │
│       │                                 ▼                             │
│       │                             PV надано                         │
│       │                             (у тій самій зоні, що й Под)     │
│       │                                 │                             │
│       ▼                                 ▼                             │
│   Под заплановано                   Под може використовувати сховище  │
│   (може зазнати невдачі,                                             │
│    якщо неправильна зона!)                                           │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Чому WaitForFirstConsumer важливий

**Проблема з Immediate**:
```
Вузол: us-east-1a           Вузол: us-east-1b
┌─────────────┐           ┌─────────────┐
│             │           │    Под      │  ← Планувальник розміщує Под тут
│             │           │   (потребує │
│             │           │   сховища)  │
└─────────────┘           └─────────────┘
      ↑
      │
   Том EBS                ✗ Том у неправильній зоні!
   (наданий               ✗ Под не може запуститися!
    негайно в 1a)
```

**Рішення з WaitForFirstConsumer**:
```
Вузол: us-east-1a           Вузол: us-east-1b
┌─────────────┐           ┌─────────────┐
│             │           │    Под      │  ← Планувальник розміщує Под тут
│             │           │   (потребує │
│             │           │   сховища)  │
└─────────────┘           └─────────────┘
                                ↑
                                │
                          Том EBS        ✓ Том у правильній зоні!
                          (наданий       ✓ Под запускається успішно!
                           в 1b ПІСЛЯ
                           планування Пода)
```

### 4.3 Коли використовувати кожен режим

| Режим | Випадок використання |
|-------|---------------------|
| Immediate | NFS, розподілене сховище, сховище без зон |
| WaitForFirstConsumer | Зональне сховище (EBS, GCE PD, Azure Disk), локальне сховище |

---

## Частина 5: Розширення томів

### 5.1 Увімкнення розширення томів

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: expandable
provisioner: kubernetes.io/aws-ebs
allowVolumeExpansion: true    # Має бути true для зміни розміру PVC
parameters:
  type: gp3
```

### 5.2 Розширення PVC

```bash
# Оригінальний PVC з 10Gi
k get pvc my-claim
# NAME       STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# my-claim   Bound    pv-001   10Gi       RWO            expandable

# Змінити для запиту більше місця
k patch pvc my-claim -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'

# Або відредагувати вручну
k edit pvc my-claim
# Змініть spec.resources.requests.storage на 20Gi
```

### 5.3 Процес розширення

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Процес розширення PVC                              │
│                                                                      │
│   1. Редагування  ──► 2. Контролер змінює       ──► 3. Розширення  │
│      PVC (збільшити    розмір базового сховища       файлової       │
│       розмір)          (напр., том EBS)               системи       │
│                                                      (при монтув.) │
│                                                                      │
│   Статус показує:                                                    │
│   - "Resizing" — зміна розміру бекенду сховища                      │
│   - "FileSystemResizePending" — очікування монтування Подом         │
│                                                                      │
│   ⚠️  Примітка: Розширення потребує перезапуску Пода для деяких     │
│                 provisioners                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.4 Перевірка статусу розширення

```bash
k describe pvc my-claim

# Шукайте conditions:
# Conditions:
#   Type                      Status
#   ----                      ------
#   FileSystemResizePending   True     # Очікування розширення файлової системи
#   Resizing                  True     # Зміна розміру бекенду
```

**Важливо**: Ви можете лише **збільшувати** розмір PVC. Зменшення не підтримується!

---

## Частина 6: Параметри StorageClass

### 6.1 Довідник параметрів

Параметри специфічні для provisioner. Поширені приклади:

**AWS EBS (CSI)**:
```yaml
parameters:
  type: gp3                    # gp2, gp3, io1, io2, st1, sc1
  iopsPerGB: "50"              # Для gp3/io1/io2
  throughput: "250"            # Для gp3 (MiB/s)
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:..."
  fsType: ext4                 # ext4, xfs
```

**GCP PD (CSI)**:
```yaml
parameters:
  type: pd-ssd                 # pd-standard, pd-ssd, pd-balanced
  replication-type: none       # none, regional-pd
  disk-encryption-kms-key: "projects/..."
  fsType: ext4
```

**Azure Disk (CSI)**:
```yaml
parameters:
  storageaccounttype: Premium_LRS   # Standard_LRS, Premium_LRS, StandardSSD_LRS
  kind: Managed                      # Managed, Dedicated, Shared
  cachingMode: ReadOnly
  fsType: ext4
```

### 6.2 Параметри монтування

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: with-mount-options
provisioner: kubernetes.io/aws-ebs
mountOptions:
  - debug
  - noatime
  - nodiratime
parameters:
  type: gp3
  fsType: ext4
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Кілька StorageClasses за замовчуванням | Непередбачувана поведінка | Лише один повинен бути за замовчуванням |
| Неправильний provisioner для платформи | PVC залишається Pending назавжди | Використовуйте правильний provisioner для вашої хмари |
| Режим Immediate з зональним сховищем | Поди не можуть змонтувати томи | Використовуйте WaitForFirstConsumer |
| Забули allowVolumeExpansion | Неможливо змінити розмір PVC пізніше | Завжди встановлюйте true, якщо не навмисно |
| Неправильні параметри для provisioner | Надання не вдається | Перевірте документацію provisioner |
| Спроба зменшити PVC | Не підтримується | Працює лише розширення |

---

## Тест

### Q1: StorageClass за замовчуванням
Що відбувається, коли ви створюєте PVC без вказівки storageClassName у кластері зі StorageClass за замовчуванням?

<details>
<summary>Відповідь</summary>

PVC автоматично використовує **StorageClass за замовчуванням** і запускає динамічне надання. Новий PV буде створений автоматично provisioner-ом.

</details>

### Q2: Відмова від динамічного надання
Як створити PVC, який явно не використовує динамічне надання?

<details>
<summary>Відповідь</summary>

Встановіть `storageClassName: ""` (порожній рядок) у специфікації PVC. Це запобігає використанню будь-якого StorageClass, включно з тим, що за замовчуванням, і PVC буде прив'язуватися лише до вручну створених PV.

</details>

### Q3: WaitForFirstConsumer
Чому WaitForFirstConsumer важливий для хмарного сховища, як-от AWS EBS?

<details>
<summary>Відповідь</summary>

Томи EBS є **специфічними для зони**. З прив'язкою Immediate том може бути наданий в іншій зоні, ніж та, де заплановано Под, що спричинить помилки монтування. WaitForFirstConsumer відкладає надання до після планування Пода, забезпечуючи створення тому в тій самій зоні, що й Под.

</details>

### Q4: Розширення тому
PVC використовує StorageClass з `allowVolumeExpansion: false`. Чи можна його розширити?

<details>
<summary>Відповідь</summary>

**Ні**. Розширення тому повинно бути увімкнене на StorageClass до того, як PVC можна буде розширити. Ви не можете змінити цей параметр після створення PVC (хіба що перестворите StorageClass і PVC).

</details>

### Q5: Визначення за замовчуванням
Як перевірити, який StorageClass є за замовчуванням?

<details>
<summary>Відповідь</summary>

```bash
k get sc
```
StorageClass за замовчуванням покаже `(default)` поруч зі своїм ім'ям. Або перевірте анотацію:
```bash
k get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

</details>

### Q6: Різниця політик повернення
Яка практична різниця між reclaimPolicy Delete та Retain у StorageClasses?

<details>
<summary>Відповідь</summary>

- **Delete**: При видаленні PVC динамічно наданий PV та базове сховище автоматично видаляються. Підходить для dev/test.
- **Retain**: При видаленні PVC PV стає "Released", але сховище зберігається. Адміністратор повинен вручну очистити. Підходить для продакшен-даних.

</details>

---

## Практична вправа: Динамічне надання

### Сценарій
Налаштуйте StorageClass та перевірте, що динамічне надання працює правильно.

### Передумови
Вам потрібен кластер із працюючим storage provisioner. Kind та minikube мають вбудовані provisioners.

### Завдання 1: Перевірити існуючі StorageClasses

```bash
# Подивитися, що доступно
k get sc

# Перевірити, чи є за замовчуванням
k get sc -o custom-columns='NAME:.metadata.name,PROVISIONER:.provisioner,DEFAULT:.metadata.annotations.storageclass\.kubernetes\.io/is-default-class'
```

### Завдання 2: Створити StorageClass

```bash
cat <<EOF | k apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: rancher.io/local-path    # Для kind; змініть для вашого кластера
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
```

### Завдання 3: Створити PVC з використанням StorageClass

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: fast
EOF

# Перевірте статус — має бути Pending (очікує споживача)
k get pvc dynamic-pvc
```

### Завдання 4: Створити Под для запуску надання

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: dynamic-pod
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Dynamically provisioned!" > /data/message; sleep 3600']
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: dynamic-pvc
EOF
```

### Завдання 5: Перевірити динамічне надання

```bash
# PVC тепер має бути Bound
k get pvc dynamic-pvc
# STATUS: Bound

# PV було створено автоматично
k get pv
# Має показати динамічно названий PV, як-от pvc-xxxxx

# Перевірити деталі PV
k get pv -o jsonpath='{.items[0].spec.storageClassName}'
# Має показати: fast

# Перевірити, що Под працює
k exec dynamic-pod -- cat /data/message
```

### Завдання 6: Перевірити StorageClass за замовчуванням (опціонально)

```bash
# Зробити наш StorageClass за замовчуванням
k patch sc fast -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "true"}}}'

# Створити PVC без storageClassName
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: default-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  # storageClassName не вказано — використовується за замовчуванням!
EOF

# Перевірити, що використовується клас за замовчуванням
k get pvc default-pvc -o jsonpath='{.spec.storageClassName}'
# Має показати: fast
```

### Критерії успіху
- [ ] StorageClass створено успішно
- [ ] PVC залишається Pending до створення Пода (WaitForFirstConsumer)
- [ ] PV автоматично створюється при плануванні Пода
- [ ] Под може записувати дані на динамічно надане сховище
- [ ] Розуміння зв'язку між SC → PVC → PV

### Очищення

```bash
k delete pod dynamic-pod
k delete pvc dynamic-pvc default-pvc
k delete sc fast
```

---

## Практичні вправи

### Вправа 1: Список StorageClasses (1 хв)
```bash
# Завдання: Вивести всі StorageClasses та визначити за замовчуванням
k get sc
```

### Вправа 2: Створити базовий StorageClass (2 хв)
```bash
# Завдання: Створити StorageClass "slow" з provisioner rancher.io/local-path
# reclaimPolicy: Retain
```

### Вправа 3: Встановити StorageClass за замовчуванням (1 хв)
```bash
# Завдання: Зробити StorageClass "standard" за замовчуванням
# Використовуйте анотацію: storageclass.kubernetes.io/is-default-class: "true"
```

### Вправа 4: PVC з конкретним StorageClass (2 хв)
```bash
# Завдання: Створити PVC "data-pvc", що запитує 5Gi з StorageClass "fast"
```

### Вправа 5: PVC без динамічного надання (2 хв)
```bash
# Завдання: Створити PVC, який не використовуватиме жоден StorageClass
# Підказка: storageClassName: ""
```

### Вправа 6: Перевірити, чому PVC у стані Pending (2 хв)
```bash
# Завдання: Діагностувати, чому PVC застряг у стані Pending
k describe pvc <name>
# Перевірте секцію Events на наявність помилок
```

### Вправа 7: Увімкнути розширення тому (2 хв)
```bash
# Завдання: Створити StorageClass з увімкненим розширенням тому
# Ключове поле: allowVolumeExpansion: true
```

### Вправа 8: Перевірити режим прив'язки (1 хв)
```bash
# Завдання: Перевірити volumeBindingMode StorageClass "standard"
k get sc standard -o jsonpath='{.volumeBindingMode}'
```

---

## Наступний модуль

Переходьте до [Модуль 4.4: Знімки томів та клонування](module-4.4-snapshots.uk.md), щоб дізнатися про функції резервного копіювання та захисту даних.
