---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 4.5: \u0423\u0441\u0443\u043d\u0435\u043d\u043d\u044f \u043d\u0435\u0441\u043f\u0440\u0430\u0432\u043d\u043e\u0441\u0442\u0435\u0439 \u0437\u0431\u0435\u0440\u0456\u0433\u0430\u043d\u043d\u044f"
slug: uk/k8s/cka/part4-storage/module-4.5-troubleshooting
sidebar: 
  order: 6
lab: 
  id: cka-4.5-troubleshooting
  url: https://killercoda.com/kubedojo/scenario/cka-4.5-troubleshooting
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — Діагностика та виправлення проблем зберігання
>
> **Час на виконання**: 35–45 хвилин
>
> **Передумови**: Модулі 4.1–4.4 (всі попередні модулі з зберігання)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Діагностувати** збої сховища систематично (PVC Pending, помилки монтування, проблеми ємності, відмова в доступі)
- **Простежити** ланцюжок виділення сховища від PVC → StorageClass → провізіонер → PV → монтування
- **Виправити** типові проблеми сховища: застряглі фіналайзери, осиротілі PV, відновлення після пошкодження файлової системи
- **Спроєктувати** чек-лист для усунення проблем сховища в сценаріях іспиту CKA

---

## Чому цей модуль важливий

Проблеми зберігання є одними з найпоширеніших у кластерах Kubernetes. Поди, що застрягли в ContainerCreating, PVC, які ніколи не прив'язуються, помилки дозволів та проблеми з ємністю можуть зупинити роботу додатків. На іспиті CKA активно перевіряють навички усунення несправностей, і проблеми зберігання з'являються часто. Цей модуль дає вам систематичний підхід до діагностики та виправлення проблем зберігання.

> **Аналогія з детективом**
>
> Усунення несправностей зберігання — це як бути детективом. Под не запускається — це злочин. Ваші інструменти — `kubectl describe`, `kubectl logs` та `kubectl get events` — ваша лупа, набір для зняття відбитків та опитування свідків. Ви слідуєте за доказами: Под → PVC → PV → StorageClass → CSI-драйвер. Кожен крок розкриває підказки, поки ви не знайдете винуватця.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Систематично усувати проблеми зберігання
- Налагоджувати проблеми прив'язки PVC
- Виправляти помилки монтування томів
- Діагностувати проблеми CSI-драйверів
- Вирішувати проблеми з дозволами та ємністю

---

## Чи знали ви?

- **Більшість проблем зберігання — це помилки конфігурації**: Неправильне ім'я StorageClass, невідповідні режими доступу або відсутні мітки спричиняють 80% проблем
- **Events — ваш найкращий друг**: `kubectl describe` показує нещодавні події, які часто містять точне повідомлення про помилку
- **CSI-драйвери мають власні логи**: Коли звичайні команди не допомагають, перевірте логи контролера та вузла CSI

---

## Частина 1: Фреймворк усунення несправностей

### 1.1 Шлях налагодження зберігання

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Шлях усунення несправностей зберігання             │
│                                                                      │
│   Проблема з Подом                                                   │
│       │                                                              │
│       ▼                                                              │
│   1. k describe pod <name>                                          │
│      └─► Перевірте секцію Events                                    │
│      └─► Перевірте помилки монтування томів                         │
│          │                                                          │
│          ▼                                                          │
│   2. k get pvc <name>                                               │
│      └─► Чи STATUS "Bound"?                                        │
│      └─► Якщо "Pending", перевірте Events                          │
│          │                                                          │
│          ▼                                                          │
│   3. k get pv                                                       │
│      └─► Чи існує відповідний PV?                                  │
│      └─► Чи STATUS "Available" або "Bound"?                        │
│          │                                                          │
│          ▼                                                          │
│   4. k get sc <storageclass>                                        │
│      └─► Чи існує StorageClass?                                    │
│      └─► Чи правильний provisioner?                                │
│          │                                                          │
│          ▼                                                          │
│   5. Перевірте CSI-драйвер                                         │
│      └─► Чи встановлений драйвер?                                  │
│      └─► Перевірте логи Подів драйвера                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Довідник ключових команд

```bash
# Налагодження на рівні Пода
k describe pod <pod-name>
k get pod <pod-name> -o yaml
k logs <pod-name>

# Налагодження PVC
k get pvc
k describe pvc <pvc-name>
k get pvc <pvc-name> -o yaml

# Налагодження PV
k get pv
k describe pv <pv-name>
k get pv <pv-name> -o yaml

# Налагодження StorageClass
k get sc
k describe sc <sc-name>

# Events (часто найкорисніші!)
k get events --sort-by='.lastTimestamp'
k get events --field-selector involvedObject.name=<pvc-name>

# Налагодження CSI
k get pods -n kube-system | grep csi
k logs -n kube-system <csi-pod> -c <container>
```

---

## Частина 2: Проблеми прив'язки PVC

### 2.1 PVC застряг у стані Pending

**Симптоми**: PVC показує `STATUS: Pending`, ніколи не стає Bound

```bash
k get pvc
# NAME     STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# my-pvc   Pending                                       fast-ssd
```

**Кроки налагодження**:
```bash
# Крок 1: Перевірити події
k describe pvc my-pvc
# Подивіться секцію Events на наявність помилок
```

### 2.2 Поширені причини Pending

**Причина 1: Немає відповідного PV (статичне надання)**
```
Events:
  Type     Reason              Message
  ----     ------              -------
  Normal   FailedBinding       no persistent volumes available for this claim
```

**Рішення**: Створіть PV, що відповідає вимогам PVC:
```bash
# Перевірте, що потрібно PVC
k get pvc my-pvc -o yaml | grep -A5 spec:

# Створіть відповідний PV або виправте PVC для відповідності існуючому PV
```

**Причина 2: StorageClass не існує**
```
Events:
  Type     Reason              Message
  ----     ------              -------
  Warning  ProvisioningFailed  storageclass.storage.k8s.io "fast-ssd" not found
```

**Рішення**:
```bash
# Список доступних StorageClasses
k get sc

# Виправте PVC для використання існуючого StorageClass
k patch pvc my-pvc -p '{"spec":{"storageClassName":"standard"}}'
# Примітка: Можливо, потрібно видалити та перестворити PVC
```

**Причина 3: Немає CSI-драйвера/provisioner**
```
Events:
  Type     Reason              Message
  ----     ------              -------
  Warning  ProvisioningFailed  failed to provision volume: no csi driver
```

**Рішення**: Встановіть необхідний CSI-драйвер для вашого бекенду сховища

**Причина 4: Режим WaitForFirstConsumer**
```bash
k get pvc my-pvc
# STATUS: Pending (це нормально, поки Под не використає його!)

k get sc fast-ssd -o jsonpath='{.volumeBindingMode}'
# WaitForFirstConsumer
```

**Рішення**: Це очікувана поведінка! Створіть Под, який використовує PVC, і він прив'яжеться.

### 2.3 Невідповідність режиму доступу

**Симптоми**: PVC не прив'язується, хоча PV існує

```bash
k get pv
# NAME   CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS
# pv-1   100Gi      RWO            Retain           Available

k get pvc
# NAME     STATUS    ACCESS MODES   STORAGECLASS
# my-pvc   Pending   RWX            manual
```

**Проблема**: PVC запитує RWX, PV пропонує лише RWO

**Рішення**:
```bash
# Варіант 1: Змінити PVC для відповідності PV
k delete pvc my-pvc
# Перестворити з RWO

# Варіант 2: Створити новий PV з RWX (якщо сховище підтримує)
```

### 2.4 Невідповідність StorageClass

```bash
k get pv pv-1 -o jsonpath='{.spec.storageClassName}'
# manual

k get pvc my-pvc -o jsonpath='{.spec.storageClassName}'
# fast
```

**Проблема**: PVC та PV мають різний storageClassName

**Рішення**: Вирівняйте storageClassName на обох ресурсах

---

## Частина 3: Помилки монтування томів

### 3.1 Под застряг у ContainerCreating

**Симптоми**: Под залишається в стані ContainerCreating

```bash
k get pods
# NAME     READY   STATUS              RESTARTS   AGE
# my-pod   0/1     ContainerCreating   0          5m
```

**Налагодження**:
```bash
k describe pod my-pod
# Шукайте помилки, пов'язані з томами, в Events
```

### 3.2 Поширені помилки монтування

**Помилка 1: PVC не знайдено**
```
Events:
  Warning  FailedMount  Unable to attach or mount volumes:
  persistentvolumeclaim "my-pvc" not found
```

**Рішення**:
```bash
# Перевірте, що PVC існує в тому самому namespace
k get pvc my-pvc -n <namespace>

# Виправте специфікацію Пода, якщо ім'я PVC неправильне
```

**Помилка 2: Том вже приєднаний до іншого вузла**
```
Events:
  Warning  FailedAttachVolume  Multi-Attach error for volume "pvc-xxx":
  Volume is already attached to node "node-1"
```

**Причина**: RWO том приєднаний до іншого вузла (типово під час збоїв вузлів)

**Рішення**:
```bash
# Зачекайте завершення старого Пода або примусово видаліть
k delete pod <old-pod> --force --grace-period=0

# Якщо використовуєте StatefulSet, можливо, потрібно видалити старе приєднання PV
k get volumeattachment
```

**Помилка 3: Відмова в дозволі**
```
Events:
  Warning  FailedMount  MountVolume.SetUp failed:
  mount failed: exit status 32, permission denied
```

**Рішення**:
```yaml
# Додайте securityContext до Пода
spec:
  securityContext:
    fsGroup: 1000        # ID групи для тому
  containers:
  - name: app
    securityContext:
      runAsUser: 1000    # ID користувача
```

**Помилка 4: hostPath не існує**
```
Events:
  Warning  FailedMount  hostPath type check failed:
  path /data/myapp does not exist
```

**Рішення**:
```yaml
# Використовуйте тип DirectoryOrCreate
volumes:
- name: data
  hostPath:
    path: /data/myapp
    type: DirectoryOrCreate    # Замість Directory
```

### 3.3 Тайм-аут монтування

```
Events:
  Warning  FailedMount  Unable to attach or mount volumes:
  timeout expired waiting for volumes to attach
```

**Причини**:
- CSI-драйвер не відповідає
- Бекенд сховища недоступний
- Проблеми з вузлом

**Налагодження**:
```bash
# Перевірте Поди CSI-драйвера
k get pods -n kube-system | grep csi

# Перевірте логи CSI-драйвера
k logs -n kube-system <csi-controller-pod> -c csi-provisioner

# Перевірте стан вузла
k describe node <node-name> | grep -A5 Conditions
```

---

## Частина 4: Проблеми з ємністю

### 4.1 Том заповнений

**Симптоми**: Помилки додатка про дисковий простір

**Налагодження**:
```bash
# Перевірте ємність PVC
k get pvc my-pvc
# CAPACITY: 10Gi

# Перевірте фактичне використання в Поді
k exec my-pod -- df -h /data
# Показує фактичне використання
```

**Рішення 1: Розширити PVC** (якщо StorageClass підтримує)
```bash
# Перевірте, чи дозволене розширення
k get sc <storageclass> -o jsonpath='{.allowVolumeExpansion}'
# true

# Розширте PVC
k patch pvc my-pvc -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'

# Моніторте статус розширення
k describe pvc my-pvc | grep -A5 Conditions
```

**Рішення 2: Очистити дані**
```bash
k exec my-pod -- rm -rf /data/tmp/*
```

### 4.2 Недостатня ємність

```
Events:
  Warning  ProvisioningFailed  insufficient capacity
```

**Причини**:
- Бекенд сховища заповнений
- Квота перевищена
- Регіональні обмеження ємності (хмара)

**Налагодження**:
```bash
# Перевірте ResourceQuota
k get resourcequota -n <namespace>

# Перевірте LimitRange
k get limitrange -n <namespace>

# Для хмари перевірте консоль хмари на ємність
```

---

## Частина 5: Проблеми з CSI-драйвером

### 5.1 CSI-драйвер не встановлений

**Симптоми**: PVC застряг у pending, події згадують CSI

```bash
k describe pvc my-pvc
# Events:
#   Warning  ProvisioningFailed  error getting CSI driver name
```

**Налагодження**:
```bash
# Список CSI-драйверів
k get csidrivers

# Перевірте, чи Поди драйвера працюють
k get pods -n kube-system | grep csi

# Перевірте об'єкти CSINode
k get csinode
```

### 5.2 CSI-драйвер у CrashLoop

```bash
k get pods -n kube-system | grep csi
# NAME                          READY   STATUS             RESTARTS
# ebs-csi-controller-xxx        0/6     CrashLoopBackOff   5
```

**Налагодження**:
```bash
# Перевірте логи
k logs -n kube-system ebs-csi-controller-xxx -c csi-provisioner
k logs -n kube-system ebs-csi-controller-xxx -c csi-attacher

# Поширені причини:
# - Відсутні хмарні облікові дані
# - Неправильні IAM-дозволи
# - Проблеми з мережевим з'єднанням
```

### 5.3 Дозволи CSI-драйвера

Для хмарного сховища CSI-драйверам потрібні відповідні дозволи:

**AWS**: IAM-роль з дозволами EBS
```bash
# Перевірте service account
k get sa -n kube-system ebs-csi-controller-sa -o yaml
# Шукайте анотацію eks.amazonaws.com/role-arn
```

**GCP**: Workload Identity або service account вузла
**Azure**: Managed Identity або service principal

---

## Частина 6: Швидкий довідник: Повідомлення про помилки

### 6.1 Шпаргалка повідомлень про помилки

| Повідомлення про помилку | Ймовірна причина | Швидке виправлення |
|-------------------------|-----------------|-------------------|
| `no persistent volumes available` | Немає відповідного PV для статичного надання | Створіть відповідний PV |
| `storageclass not found` | Неправильне ім'я StorageClass | Перевірте `k get sc` |
| `waiting for first consumer` | Режим WaitForFirstConsumer | Створіть Под, що використовує PVC |
| `Multi-Attach error` | RWO том на кількох вузлах | Спочатку видаліть старий Под |
| `permission denied` | Дозволи файлової системи | Встановіть fsGroup/runAsUser |
| `path does not exist` | hostPath відсутній | Використовуйте DirectoryOrCreate |
| `timeout waiting for volumes` | Проблема CSI-драйвера | Перевірте Поди/логи CSI |
| `insufficient capacity` | Немає місця в бекенді сховища | Розширте або очистіть |
| `volume is already attached` | Застаріле приєднання тому | Видаліть VolumeAttachment |

### 6.2 Швидкі команди налагодження

```bash
# Однорядкова перевірка типових проблем
echo "=== PVCs ===" && k get pvc && \
echo "=== PVs ===" && k get pv && \
echo "=== StorageClasses ===" && k get sc && \
echo "=== Нещодавні події ===" && k get events --sort-by='.lastTimestamp' | tail -20
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Не перевіряти Events | Пропуск фактичного повідомлення про помилку | Завжди `k describe` першим |
| Ігнорування namespace | PVC в іншому namespace, ніж Под | Перевірте відповідність namespace |
| Забули про WaitForFirstConsumer | Думати, що PVC зламаний, коли Pending | Перевірте volumeBindingMode |
| Видалення PVC перед Подом | Под не може коректно розмонтувати | Спочатку видаліть Под |
| Не перевіряти логи CSI | Загальні помилки приховують справжню причину | Перевірте Поди CSI-драйвера |
| Неправильний відступ YAML | Специфікація тому невалідна | Використовуйте `--dry-run=client -o yaml` |

---

## Тест

### Q1: Перший крок налагодження
Под застряг у ContainerCreating. Яку команду слід виконати першою?

<details>
<summary>Відповідь</summary>

```bash
k describe pod <pod-name>
```

Це показує секцію Events, яка зазвичай містить конкретне повідомлення про помилку, чому Под не може запуститися. Шукайте помилки, пов'язані з томами, як-от FailedMount або FailedAttach.

</details>

### Q2: Аналіз Pending PVC
PVC застряг у стані Pending. Як дізнатися, чому?

<details>
<summary>Відповідь</summary>

```bash
k describe pvc <pvc-name>
```

Перевірте секцію Events на наявність попереджень, як-от:
- "no persistent volumes available" — немає відповідного PV
- "storageclass not found" — неправильне ім'я SC
- "waiting for first consumer" — очікувано з WaitForFirstConsumer

</details>

### Q3: Помилка Multi-Attach
Ви бачите "Multi-Attach error for volume". Що це означає і як це виправити?

<details>
<summary>Відповідь</summary>

Помилка означає, що **RWO** (ReadWriteOnce) том вже приєднаний до іншого вузла, зазвичай від старого Пода, який не був коректно розмонтований.

Виправлення:
1. Знайдіть та видаліть старий Под: `k get pods -o wide`, щоб знайти Под, який використовує том
2. Якщо Под застряг при завершенні: `k delete pod <name> --force --grace-period=0`
3. Перевірте VolumeAttachment за потреби: `k get volumeattachment`

</details>

### Q4: WaitForFirstConsumer
PVC показує Pending, але немає помилок у подіях. StorageClass використовує WaitForFirstConsumer. Це проблема?

<details>
<summary>Відповідь</summary>

**Ні, це очікувана поведінка**. З WaitForFirstConsumer PVC залишається Pending, поки не буде заплановано Под, який його використовує. Це насправді бажано для зонального сховища, щоб забезпечити створення тому в тій самій зоні, що й Под.

Щоб продовжити, створіть Под, який посилається на PVC, і PV буде надано при плануванні Пода.

</details>

### Q5: Відмова в дозволі
Том монтується, але додаток отримує "permission denied" при записі. Що слід перевірити?

<details>
<summary>Відповідь</summary>

Перевірте security context Пода:

```yaml
spec:
  securityContext:
    fsGroup: <gid>      # Група для власності тому
  containers:
  - securityContext:
      runAsUser: <uid>   # Користувач, під яким працює контейнер
```

fsGroup повинен збігатися з GID, якому належать файли тому, або користувач контейнера повинен мати дозволи на запис.

</details>

### Q6: Пошук помилок CSI
Де шукати помилки CSI-драйвера?

<details>
<summary>Відповідь</summary>

```bash
# Знайдіть Поди CSI
k get pods -n kube-system | grep csi

# Перевірте логи контролера CSI
k logs -n kube-system <csi-controller-pod> -c csi-provisioner
k logs -n kube-system <csi-controller-pod> -c csi-attacher

# Перевірте логи CSI node plugin
k logs -n kube-system <csi-node-pod> -c csi-driver
```

Також перевірте `k get csidrivers` та `k get csinode` для статусу реєстрації драйвера.

</details>

---

## Практична вправа: Сценарії усунення несправностей зберігання

### Налаштування

```bash
# Створити namespace
k create ns storage-debug

# Ми створимо зламані конфігурації та виправимо їх
```

### Сценарій 1: PVC не прив'язується (неправильний StorageClass)

```bash
# Створити PVC з неправильним StorageClass
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: broken-pvc-1
  namespace: storage-debug
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: nonexistent-class
EOF

# Перевірити статус
k get pvc -n storage-debug broken-pvc-1

# Налагодження
k describe pvc -n storage-debug broken-pvc-1
# Шукайте: storageclass "nonexistent-class" not found

# Виправлення: Перелічіть доступні StorageClasses та перестворіть PVC
k get sc
k delete pvc -n storage-debug broken-pvc-1

# Перестворити з правильним StorageClass (використовуйте SC вашого кластера)
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: broken-pvc-1
  namespace: storage-debug
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard    # Використовуйте фактичне ім'я SC
EOF
```

### Сценарій 2: Под не може змонтувати (неправильне ім'я PVC)

```bash
# Створити валідний PVC
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: correct-pvc
  namespace: storage-debug
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# Створити Под з неправильним посиланням на PVC
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-1
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: wrong-pvc-name    # Це не існує!
EOF

# Перевірити статус Пода
k get pod -n storage-debug broken-pod-1
# STATUS: ContainerCreating

# Налагодження
k describe pod -n storage-debug broken-pod-1
# Шукайте: persistentvolumeclaim "wrong-pvc-name" not found

# Виправлення
k delete pod -n storage-debug broken-pod-1

cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-1
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: correct-pvc    # Виправлено!
EOF
```

### Сценарій 3: Помилка типу hostPath

```bash
# Створити Под зі строгим типом hostPath
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-2
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    hostPath:
      path: /tmp/nonexistent-path-xyz
      type: Directory    # Зазнає невдачі, якщо каталог не існує
EOF

# Налагодження
k describe pod -n storage-debug broken-pod-2
# Може показати: hostPath type check failed

# Виправлення: Використовуйте DirectoryOrCreate
k delete pod -n storage-debug broken-pod-2

cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-2
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    hostPath:
      path: /tmp/nonexistent-path-xyz
      type: DirectoryOrCreate    # Створює, якщо відсутній
EOF
```

### Критерії успіху
- [ ] Визначено помилку StorageClass з подій
- [ ] PVC виправлено для використання правильного StorageClass
- [ ] Визначено неправильне ім'я PVC з подій Пода
- [ ] Под виправлено для посилання на правильний PVC
- [ ] Зрозуміли вимоги до типів hostPath

### Очищення

```bash
k delete ns storage-debug
```

---

## Практичні вправи

### Вправа 1: Швидка перевірка статусу (1 хв)
```bash
# Завдання: Перевірити, чи всі PVC у namespace прив'язані
k get pvc -n <namespace>
# Шукайте будь-які, що не показують "Bound"
```

### Вправа 2: Знайти події PVC (1 хв)
```bash
# Завдання: Отримати події для конкретного PVC
k describe pvc <pvc-name> | grep -A20 Events
```

### Вправа 3: Перевірити том у Поді (2 хв)
```bash
# Завдання: Перевірити, що том правильно змонтований у Поді
k exec <pod> -- df -h
k exec <pod> -- ls -la /data
```

### Вправа 4: Налагодити ContainerCreating (2 хв)
```bash
# Завдання: Знайти, чому Под застряг у ContainerCreating
k describe pod <pod-name>
# Перевірте Events на помилки монтування
```

### Вправа 5: Перевірити статус CSI-драйвера (2 хв)
```bash
# Завдання: Перевірити, що CSI-драйвер працює
k get pods -n kube-system | grep csi
k get csidrivers
```

### Вправа 6: Знайти відповідний PV (2 хв)
```bash
# Завдання: Знайти, чому PVC не прив'язується до існуючого PV
k get pvc <pvc-name> -o yaml | grep -E 'storage:|accessModes:|storageClassName:'
k get pv <pv-name> -o yaml | grep -E 'storage:|accessModes:|storageClassName:'
# Порівняйте значення
```

### Вправа 7: Перевірити VolumeAttachments (1 хв)
```bash
# Завдання: Вивести всі приєднання томів
k get volumeattachment
# Корисно для налагодження помилок Multi-Attach
```

### Вправа 8: Отримати нещодавні події зберігання (1 хв)
```bash
# Завдання: Отримати нещодавні події, пов'язані з PVC
k get events --field-selector reason=FailedBinding
k get events --field-selector reason=ProvisioningFailed
```

---

## Підсумок: Контрольний список усунення несправностей зберігання

```
□ Под застряг? → k describe pod → перевірте Events
□ PVC Pending? → k describe pvc → перевірте Events
□ StorageClass існує? → k get sc
□ PV доступний? → k get pv
□ Режими доступу збігаються? → Порівняйте PVC та PV
□ StorageClassName збігається? → Порівняйте PVC та PV
□ CSI-драйвер працює? → k get pods -n kube-system | grep csi
□ Проблема з дозволами? → Перевірте securityContext fsGroup
□ Проблема з ємністю? → Перевірте квоти та бекенд сховища
```

---

## Наступні кроки

Вітаємо! Ви завершили Частину 4: Зберігання. Тепер ви повинні вміти:
- Налаштовувати томи (emptyDir, hostPath, projected)
- Працювати з PersistentVolumes та PersistentVolumeClaims
- Використовувати StorageClasses для динамічного надання
- Створювати та відновлювати зі знімків томів
- Усувати типові проблеми зберігання

Переходьте до [Кумулятивний тест Частини 4](part4-cumulative-quiz/), щоб перевірити свої знання, а потім до [Частина 5: Усунення несправностей](../part5-troubleshooting/).
