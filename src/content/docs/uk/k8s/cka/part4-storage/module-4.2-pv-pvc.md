---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 4.2: PersistentVolumes \u0442\u0430 PersistentVolumeClaims"
slug: uk/k8s/cka/part4-storage/module-4.2-pv-pvc
sidebar: 
  order: 3
lab: 
  id: cka-4.2-pv-pvc
  url: https://killercoda.com/kubedojo/scenario/cka-4.2-pv-pvc
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Основна абстракція зберігання
>
> **Час на виконання**: 40–50 хвилин
>
> **Передумови**: Модуль 4.1 (Томи), Модуль 1.2 (CSI)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** PersistentVolumes та PersistentVolumeClaims з відповідними режимами доступу та класами сховища
- **Пояснити** життєвий цикл PV (Available → Bound → Released → Deleted) та політики повернення
- **Дебажити** PVC у стані Pending, перевіряючи StorageClass, ємність, режими доступу та node affinity
- **Імплементувати** статичне виділення для локального сховища та динамічне виділення за допомогою StorageClasses

---

## Чому цей модуль важливий

Персистентні томи (PV) та PersistentVolumeClaims (PVC) — це основа постійного зберігання в Kubernetes. Вони розділяють надання сховища та його споживання, дозволяючи адміністраторам керувати сховищем незалежно від розробників, які його використовують. На іспиті CKA активно перевіряють створення PV/PVC, прив'язку та усунення несправностей.

> **Аналогія з орендою квартири**
>
> Уявіть сховище як оренду квартири. **Персистентний том (PV)** — це сама квартира — вона існує незалежно від того, живе там хтось чи ні. **PersistentVolumeClaim** — це заява орендаря, в якій вказані його потреби: «Мені потрібні 2 спальні, центральне розташування, паркомісце». Керуючий будинком (Kubernetes) зіставляє заяви з доступними квартирами. Орендарю (Поду) не потрібно знати, яку саме квартиру він отримав — лише що вона відповідає його вимогам.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Створювати PersistentVolumes вручну
- Створювати PersistentVolumeClaims для запиту сховища
- Розуміти процес прив'язки між PV та PVC
- Налаштовувати режими доступу та політики повернення
- Використовувати PVC у Подах
- Усувати типові проблеми PV/PVC

---

## Чи знали ви?

- **PV мають кластерний масштаб**: На відміну від більшості ресурсів, Персистентні томи не належать жодному простору імен — вони доступні в усьому кластері
- **Прив'язка є постійною**: Після прив'язки PVC до PV ця прив'язка є ексклюзивною, поки PVC не буде видалено (або PV не буде повернуто)
- **Розмір має значення по-іншому**: PVC, що запитує 5Gi, може прив'язатися до PV на 100Gi, якщо ближчого збігу немає — додатковий простір зарезервований, але потенційно витрачений даремно

---

## Частина 1: Розуміння моделі PV/PVC

### 1.1 Абстракція зберігання

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Модель абстракції PV/PVC                           │
│                                                                       │
│   Адміністратор кластера              Розробник                       │
│   ┌─────────────┐                      ┌─────────────┐               │
│   │ Надає       │                      │ Запитує     │               │
│   │ сховище     │                      │ сховище     │               │
│   └──────┬──────┘                      └──────┬──────┘               │
│          │                                    │                       │
│          ▼                                    ▼                       │
│   ┌─────────────┐      Прив'язка      ┌─────────────┐               │
│   │ Persistent  │◄───────────────────►│ Persistent  │               │
│   │ Volume (PV) │                      │ VolumeClaim │               │
│   │             │                      │ (PVC)       │               │
│   │ 100Gi NFS   │                      │ 50Gi RWO    │               │
│   └──────┬──────┘                      └──────┬──────┘               │
│          │                                    │                       │
│          │    Фізичне сховище                 │  Монтування в Под     │
│          ▼                                    ▼                       │
│   ┌─────────────┐                      ┌─────────────┐               │
│   │   NFS       │                      │    Под      │               │
│   │   Сервер    │─────────────────────►│  /data      │               │
│   └─────────────┘                      └─────────────┘               │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 Навіщо таке розділення?

| Питання | Хто відповідає | Ресурс |
|---------|---------------|--------|
| Яке сховище доступне? | Адміністратор | PersistentVolume |
| Скільки сховища потрібно? | Розробник | PersistentVolumeClaim |
| Куди монтувати? | Розробник | Специфікація Пода |
| Деталі бекенду сховища | Адміністратор | PV + StorageClass |

### 1.3 Життєвий цикл PV/PVC

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Життєвий цикл PV/PVC                            │
│                                                                      │
│   PV створено ──► Available ──► Bound ──► Released ──► [Повернення] │
│       │              │            │           │            │         │
│       │              │            │           │            │         │
│       │         PVC створено     PVC         PVC       Retain/      │
│       │         та знайдено      існує      видалено   Delete/      │
│       │         збіг                                   Recycle      │
│                                                                      │
│   Фази PV:                                                           │
│   • Available: Готовий до прив'язки                                   │
│   • Bound: Пов'язаний з PVC                                          │
│   • Released: PVC видалено, очікує повернення                        │
│   • Failed: Автоматичне повернення не вдалось                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Частина 2: Створення PersistentVolumes

### 2.1 Специфікація PV

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs-data
  labels:
    type: nfs
    environment: production
spec:
  capacity:
    storage: 100Gi                    # Розмір тому
  volumeMode: Filesystem              # Filesystem або Block
  accessModes:
    - ReadWriteMany                   # Може бути змонтований кількома вузлами
  persistentVolumeReclaimPolicy: Retain   # Що відбувається при звільненні
  storageClassName: manual            # Має збігатися з PVC (або порожній)
  mountOptions:
    - hard
    - nfsvers=4.1
  nfs:                                # Конфігурація, специфічна для бекенду
    path: /exports/data
    server: nfs-server.example.com
```

### 2.2 Режими доступу

| Режим | Скорочення | Опис |
|-------|-----------|------|
| ReadWriteOnce | RWO | Читання-запис на одному вузлі |
| ReadOnlyMany | ROX | Тільки читання на кількох вузлах |
| ReadWriteMany | RWX | Читання-запис на кількох вузлах |
| ReadWriteOncePod | RWOP | Читання-запис для одного Пода (K8s 1.22+) |

**Підтримка залежить від бекенду**:
- **NFS**: RWO, ROX, RWX
- **AWS EBS**: лише RWO
- **GCE PD**: RWO, ROX
- **Azure Disk**: лише RWO
- **Local**: лише RWO

### 2.3 Політики повернення

| Політика | Поведінка | Випадок використання |
|----------|----------|---------------------|
| Retain | PV зберігається після видалення PVC | Продакшен-дані, ручне очищення |
| Delete | PV та базове сховище видаляються | Динамічне надання, dev/test |
| Recycle | Базове очищення (`rm -rf /data/*`) | **Застаріло** — не використовуйте |

### 2.4 Режими тому

```yaml
spec:
  volumeMode: Filesystem    # За замовчуванням — монтується як каталог
  # АБО
  volumeMode: Block         # Необроблений блоковий пристрій (для баз даних)
```

### 2.5 Поширені типи PV

**hostPath PV** (лише для тестування):
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-hostpath
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: manual
  hostPath:
    path: /mnt/data
    type: DirectoryOrCreate
```

**NFS PV**:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  nfs:
    server: 192.168.1.100
    path: /exports/share
```

**Local PV** (специфічний для вузла):
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local
spec:
  capacity:
    storage: 200Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:                        # Обов'язково для локальних томів!
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker-node-1
```

---

## Частина 3: Створення PersistentVolumeClaims

### 3.1 Специфікація PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-claim
  namespace: production              # PVC належать до namespace!
spec:
  accessModes:
    - ReadWriteOnce                  # Має збігатися або бути підмножиною PV
  volumeMode: Filesystem
  resources:
    requests:
      storage: 50Gi                  # Мінімальний необхідний розмір
  storageClassName: manual           # Збігається зі storageClassName PV
  selector:                          # Опціонально: обрати конкретні PV
    matchLabels:
      type: nfs
      environment: production
```

### 3.2 Правила прив'язки

PVC прив'язується до PV, коли:
1. **storageClassName** збігається (або обидва порожні)
2. **accessModes**, що запитуються, доступні в PV
3. **resources.requests.storage** <= ємність PV
4. **selector** (якщо вказано) збігається з мітками PV

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Рішення про прив'язку                          │
│                                                                      │
│   Запит PVC             Доступний PV       Збіг?                    │
│   ─────────────        ────────────        ──────                    │
│   50Gi RWO             100Gi RWO           ✓ Розмір OK, режим OK    │
│   50Gi RWX             100Gi RWO           ✗ Невідповідність режиму │
│   50Gi RWO manual      100Gi RWO fast      ✗ Невідповідність SC     │
│   50Gi RWO             30Gi RWO            ✗ Розмір замалий         │
│                                                                      │
│   Примітка: PVC може прив'язатися до більшого PV, але не меншого   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Створення PVC через kubectl

```bash
# Швидкий спосіб створення PVC (обмежені параметри)
cat <<EOF | k apply -f -
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
  storageClassName: standard
EOF
```

### 3.4 Перевірка статусу PVC

```bash
# Список PVC
k get pvc
# NAME       STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# my-claim   Bound    pv-001   10Gi       RWO            standard

# Детальний перегляд
k describe pvc my-claim

# Перевірити, до якого PV прив'язано
k get pvc my-claim -o jsonpath='{.spec.volumeName}'
```

---

## Частина 4: Використання PVC у Подах

### 4.1 Базовий Под з PVC

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-storage
spec:
  containers:
  - name: app
    image: nginx:1.25
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-claim              # Посилання на ім'я PVC
```

### 4.2 PVC у Deployments

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.25
        volumeMounts:
        - name: shared-data
          mountPath: /data
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-pvc        # Має бути RWX для кількох реплік
```

**Важливо**: Для Deployments з кількома репліками вам потрібно:
- PVC з режимом доступу `ReadWriteMany`, АБО
- StatefulSet з volumeClaimTemplates (кожна репліка отримує власний PVC)

### 4.3 Монтування PVC тільки для читання

```yaml
volumes:
- name: data
  persistentVolumeClaim:
    claimName: my-claim
    readOnly: true                     # Монтувати тільки для читання
```

---

## Частина 5: Зіставлення PV/PVC за допомогою селекторів

### 5.1 Вибір на основі міток

```yaml
# PV з мітками
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-fast-ssd
  labels:
    type: ssd
    speed: fast
    region: us-east
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  storageClassName: ""                # Порожній для ручної прив'язки
  hostPath:
    path: /mnt/ssd
---
# PVC, що обирає конкретний PV
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fast-storage-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: ""                # Має збігатися з PV
  selector:
    matchLabels:
      type: ssd
      speed: fast
    matchExpressions:
    - key: region
      operator: In
      values:
        - us-east
        - us-west
```

### 5.2 Прямий вибір тому

Примусова прив'язка PVC до конкретного PV за іменем:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: specific-pv-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: ""
  volumeName: pv-fast-ssd             # Прив'язатися до цього конкретного PV
```

---

## Частина 6: Звільнення та очищення PV

### 6.1 Розуміння стану Released

Коли PVC видаляється:
```
PVC видалено ──► Статус PV змінюється на "Released"
                     │
                     ├── Retain: Дані збережені, PV не можна повторно використати
                     │           Адміністратор повинен вручну очистити
                     │
                     └── Delete: PV та сховище видаляються автоматично
```

### 6.2 Повернення звільненого PV

```bash
# Перевірити статус PV
k get pv pv-data
# NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS     CLAIM
# pv-data   100Gi      RWO            Retain           Released   default/old-claim

# Видалити посилання на claim, щоб зробити PV доступним знову
k patch pv pv-data -p '{"spec":{"claimRef": null}}'

# Перевірити, що він Available
k get pv pv-data
# STATUS: Available
```

### 6.3 Ручне видалення даних

Для політики Retain дані залишаються на сховищі. Кроки очищення:
1. Створіть резервну копію даних за потреби
2. Видаліть дані з базового сховища
3. Видаліть claimRef (як вище) або видаліть/перестворіть PV

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| PVC застряг у Pending | Немає відповідного PV | Перевірте storageClassName, розмір, режими доступу |
| Невідповідність режиму доступу | PVC запитує RWX, PV має лише RWO | Використовуйте сумісні режими доступу |
| Невідповідність StorageClass | PVC та PV мають різний storageClassName | Вирівняйте storageClassName або використовуйте "" для обох |
| Видалили PVC, втратили дані | Політика повернення була Delete | Використовуйте Retain для важливих даних |
| Не можна повторно використати Released PV | claimRef все ще встановлений | Патч PV для видалення claimRef |
| Local PV без nodeAffinity | Под не може знайти том | Додайте обов'язкову секцію nodeAffinity |
| PVC у неправильному namespace | Под не може посилатися на нього | PVC повинні бути в тому самому namespace, що й Под |

---

## Тест

### Q1: Область видимості PV
PersistentVolumes належать до namespace чи мають кластерний масштаб?

<details>
<summary>Відповідь</summary>

**Область видимості кластера**. PersistentVolumes не належать жодному простору імен — вони доступні в усьому кластері. PersistentVolumeClaims належать до namespace і можуть використовуватися лише Подами в тому самому namespace.

</details>

### Q2: Розмір при прив'язці
PVC запитує 20Gi. Доступні PV: 10Gi, 50Gi та 100Gi. Який прив'яжеться?

<details>
<summary>Відповідь</summary>

**50Gi** — Kubernetes обирає найменший PV, який задовольняє запит. 10Gi замалий. Між 50Gi та 100Gi кращим збігом є 50Gi для мінімізації витраченого простору.

</details>

### Q3: Сумісність режимів доступу
Чи може PVC, що запитує `ReadWriteOnce`, прив'язатися до PV з `ReadWriteMany`?

<details>
<summary>Відповідь</summary>

**Так**. Запитувані режими доступу PVC повинні бути підмножиною того, що пропонує PV. RWX включає можливості RWO, тому запит RWO може бути задоволений PV з RWX.

</details>

### Q4: Звільнений PV
PV показує статус "Released". Що це означає і що відбувається далі?

<details>
<summary>Відповідь</summary>

"Released" означає, що прив'язаний PVC було видалено, але PV все ще має claimRef. З політикою **Retain** PV залишається Released, поки адміністратор вручну не очистить claimRef. З політикою **Delete** PV та базове сховище автоматично видаляються.

</details>

### Q5: Порожній рядок StorageClass
Яка різниця між `storageClassName: ""` та відсутністю storageClassName?

<details>
<summary>Відповідь</summary>

- `storageClassName: ""` (порожній рядок): Прив'язуватися лише до PV без storageClassName, вимкнути динамічне надання
- Не вказано: Використовувати StorageClass кластера за замовчуванням (якщо існує), може запустити динамічне надання

Для ручної прив'язки PV до PVC явно встановіть `storageClassName: ""` на обох.

</details>

### Q6: Вимоги до Local PV
Яка спеціальна конфігурація потрібна для локального PersistentVolume?

<details>
<summary>Відповідь</summary>

Локальні PV потребують **nodeAffinity** для вказівки, на якому вузлі знаходиться сховище. Без цього Поди можуть бути заплановані на вузли без доступу до локального сховища.

```yaml
nodeAffinity:
  required:
    nodeSelectorTerms:
    - matchExpressions:
      - key: kubernetes.io/hostname
        operator: In
        values:
        - specific-node-name
```

</details>

---

## Практична вправа: Статичне надання PV

### Сценарій
Створіть PV та PVC, потім використайте сховище в Поді. Перевірте, що дані зберігаються після видалення Пода.

### Налаштування

```bash
# Створити namespace
k create ns pv-lab
```

### Завдання 1: Створити PersistentVolume

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: lab-pv
  labels:
    lab: storage
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/lab-pv-data
    type: DirectoryOrCreate
EOF
```

Перевірка:
```bash
k get pv lab-pv
# STATUS має бути "Available"
```

### Завдання 2: Створити PersistentVolumeClaim

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lab-pvc
  namespace: pv-lab
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  storageClassName: manual
  selector:
    matchLabels:
      lab: storage
EOF
```

Перевірка прив'язки:
```bash
k get pvc -n pv-lab
# STATUS має бути "Bound"

k get pv lab-pv
# CLAIM має показувати "pv-lab/lab-pvc"
```

### Завдання 3: Використати PVC у Поді

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
  namespace: pv-lab
spec:
  containers:
  - name: writer
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Data written at \$(date)" > /data/timestamp.txt; sleep 3600']
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: lab-pvc
EOF
```

### Завдання 4: Перевірити збереження даних

```bash
# Перевірити записані дані
k exec -n pv-lab storage-pod -- cat /data/timestamp.txt

# Видалити Под
k delete pod -n pv-lab storage-pod

# Перестворити Под
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod-v2
  namespace: pv-lab
spec:
  containers:
  - name: reader
    image: busybox:1.36
    command: ['sh', '-c', 'cat /data/timestamp.txt; sleep 3600']
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: lab-pvc
EOF

# Перевірити, що дані збереглися
k logs -n pv-lab storage-pod-v2
# Має показати оригінальну мітку часу
```

### Завдання 5: Перевірити стан Released

```bash
# Видалити PVC (Под треба видалити спочатку)
k delete pod -n pv-lab storage-pod-v2
k delete pvc -n pv-lab lab-pvc

# Перевірити статус PV
k get pv lab-pv
# STATUS має бути "Released" (через політику Retain)

# Зробити PV доступним знову
k patch pv lab-pv -p '{"spec":{"claimRef": null}}'

k get pv lab-pv
# STATUS має бути "Available"
```

### Критерії успіху
- [ ] PV створено та показує "Available"
- [ ] PVC створено та прив'язано до PV
- [ ] Под може записувати дані на змонтований том
- [ ] Дані зберігаються після видалення Пода
- [ ] PV показує "Released" після видалення PVC
- [ ] PV можна знову зробити "Available"

### Очищення

```bash
k delete ns pv-lab
k delete pv lab-pv
```

---

## Практичні вправи

### Вправа 1: Створити PV (2 хв)
```bash
# Завдання: Створити PV на 5Gi з доступом RWO, політикою Retain, storageClassName "slow"
# Бекенд: hostPath /mnt/data
```

### Вправа 2: Створити PVC (1 хв)
```bash
# Завдання: Створити PVC, що запитує 2Gi з RWO, storageClassName "slow"
```

### Вправа 3: Перевірити прив'язку (1 хв)
```bash
# Завдання: Перевірити, що PVC прив'язаний до правильного PV
# Команди: k get pvc, k get pv, перевірте стовпець CLAIM
```

### Вправа 4: Селектор PVC (2 хв)
```bash
# Завдання: Створити PVC, який прив'язується лише до PV з міткою "tier: gold"
# Використовуйте selector.matchLabels
```

### Вправа 5: Под з PVC (2 хв)
```bash
# Завдання: Створити Под, що монтує PVC "data-pvc" в /app/data
# Образ: nginx
```

### Вправа 6: Усунення несправності Pending PVC (2 хв)
```bash
# Дано: PVC застряг у стані Pending
# Завдання: Визначити, чому він не прив'язується
# Перевірте: k describe pvc, подивіться на Events
```

### Вправа 7: Повернення Released PV (1 хв)
```bash
# Завдання: Зробити "Released" PV знову доступним
# Команда: k patch pv <name> -p '{"spec":{"claimRef": null}}'
```

### Вправа 8: Local PV з nodeAffinity (3 хв)
```bash
# Завдання: Створити локальний PV, який працює лише на вузлі "worker-1"
# Включіть обов'язкову секцію nodeAffinity
```

---

## Наступний модуль

Переходьте до [Модуль 4.3: StorageClasses та динамічне надання](module-4.3-storageclasses/), щоб дізнатися про автоматичне створення PV.
