# Кумулятивний тест Частини 4: Зберігання

> **Обмеження часу**: 30 хвилин
>
> **Прохідний бал**: 80% (20/25 питань)
>
> **Формат**: Множинний вибір та коротка відповідь

Цей тест охоплює всі модулі Частини 4:
- Модуль 4.1: Томи
- Модуль 4.2: PersistentVolumes та PersistentVolumeClaims
- Модуль 4.3: StorageClasses та динамічне надання
- Модуль 4.4: Знімки томів та клонування
- Модуль 4.5: Усунення несправностей зберігання

---

## Секція 1: Томи (5 питань)

### Q1: Час життя emptyDir
Коли видаляється том emptyDir?

<details>
<summary>Відповідь</summary>

Коли **Под видаляється з вузла** (видалення, витіснення або збій вузла). emptyDir переживає перезапуски контейнера, але не видалення Пода. Дані прив'язані до життєвого циклу Пода, а не контейнера.

</details>

### Q2: emptyDir з підтримкою пам'яттю
Яка конфігурація створює emptyDir з підтримкою RAM замість диска?

<details>
<summary>Відповідь</summary>

```yaml
volumes:
- name: cache
  emptyDir:
    medium: Memory
    sizeLimit: 100Mi    # Важливо встановити ліміт!
```

emptyDir з підтримкою пам'яттю враховується в ліміті пам'яті контейнера.

</details>

### Q3: Безпека hostPath
Чому hostPath вважається ризиком безпеки у продакшені?

<details>
<summary>Відповідь</summary>

hostPath монтує файлову систему вузла до Пода, що може:
- Дозволити втечу контейнера на вузол
- Відкрити конфіденційні файли вузла (облікові дані, конфігурації)
- Дозволити запис шкідливих файлів на вузол
- Обійти ізоляцію контейнера

Більшість Pod Security Policies/Standards блокують hostPath.

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

### Q5: Обмеження subPath
Яке ключове обмеження використання subPath при монтуванні ConfigMaps або Secrets?

<details>
<summary>Відповідь</summary>

**Монтування subPath не оновлюються автоматично** при зміні джерельного ConfigMap або Secret. Звичайні монтування томів отримують оновлення автоматично (протягом ~1 хвилини), але монтування subPath потребують перезапуску Пода для відображення змін.

</details>

---

## Секція 2: PersistentVolumes та PVC (6 питань)

### Q6: Область видимості PV
PersistentVolumes належать до namespace чи мають область видимості кластера?

<details>
<summary>Відповідь</summary>

**Область видимості кластера**. PersistentVolumes доступні в усьому кластері та не належать жодному namespace. PersistentVolumeClaims належать до namespace.

</details>

### Q7: Скорочення режимів доступу
Що означають RWO, ROX та RWX?

<details>
<summary>Відповідь</summary>

- **RWO** — ReadWriteOnce: Один вузол може монтувати для читання-запису
- **ROX** — ReadOnlyMany: Кілька вузлів можуть монтувати тільки для читання
- **RWX** — ReadWriteMany: Кілька вузлів можуть монтувати для читання-запису

</details>

### Q8: Політики повернення
Що відбувається з PV з `reclaimPolicy: Retain`, коли його PVC видаляється?

<details>
<summary>Відповідь</summary>

PV переходить у стан **Released**. Дані зберігаються, і PV не стає автоматично доступним для нових claims. Адміністратор повинен:
1. Створити резервну копію даних за потреби
2. Очистити базове сховище
3. Видалити claimRef, щоб зробити PV знову Available (або видалити/перестворити PV)

</details>

### Q9: Розмір при прив'язці PV
PVC запитує 20Gi. Доступні PV: 10Gi, 50Gi та 100Gi. Який прив'яжеться?

<details>
<summary>Відповідь</summary>

**50Gi**. Kubernetes обирає найменший PV, що задовольняє запит. 10Gi замалий. Між 50Gi та 100Gi 50Gi мінімізує витрачену ємність.

</details>

### Q10: Вимога до Local PV
Яка спеціальна конфігурація потрібна для локального PersistentVolume?

<details>
<summary>Відповідь</summary>

**nodeAffinity**. Локальні PV повинні вказувати, на якому вузлі знаходиться сховище:

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

### Q11: Зробити Released PV доступним
Як зробити Released PV знову доступним для нових claims?

<details>
<summary>Відповідь</summary>

Видаліть claimRef:

```bash
k patch pv <pv-name> -p '{"spec":{"claimRef": null}}'
```

Це очищує прив'язку та змінює статус з Released на Available.

</details>

---

## Секція 3: StorageClasses (5 питань)

### Q12: StorageClass за замовчуванням
Як позначити StorageClass як за замовчуванням для кластера?

<details>
<summary>Відповідь</summary>

Додайте анотацію:

```yaml
metadata:
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
```

Або патч існуючого:
```bash
k patch sc <name> -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "true"}}}'
```

</details>

### Q13: Відмова від динамічного надання
Як створити PVC, який не використовує жоден StorageClass (без динамічного надання)?

<details>
<summary>Відповідь</summary>

Встановіть `storageClassName: ""` (порожній рядок):

```yaml
spec:
  storageClassName: ""
```

Це явно вимикає динамічне надання та вимагає ручної прив'язки PV.

</details>

### Q14: WaitForFirstConsumer
Чому `volumeBindingMode: WaitForFirstConsumer` важливий для хмарного сховища?

<details>
<summary>Відповідь</summary>

Хмарне сховище, як-от EBS, GCE PD та Azure Disk, є **специфічним для зони**. З прив'язкою Immediate том може бути наданий в іншій зоні, ніж та, де заплановано Под, що спричинить помилки монтування.

WaitForFirstConsumer відкладає надання до після планування Пода, забезпечуючи створення тому в тій самій зоні, що й Под.

</details>

### Q15: Розширення тому
Яке поле StorageClass потрібно встановити для дозволу зміни розміру PVC?

<details>
<summary>Відповідь</summary>

```yaml
allowVolumeExpansion: true
```

Без цього PVC не можуть бути розширені після створення.

</details>

### Q16: PVC без storageClassName
Що відбувається, коли ви створюєте PVC без вказівки storageClassName?

<details>
<summary>Відповідь</summary>

Якщо в кластері існує **StorageClass за замовчуванням**, він буде використаний і відбудеться динамічне надання. Якщо за замовчуванням немає, PVC залишиться Pending, поки не буде вручну створено відповідний PV.

</details>

---

## Секція 4: Знімки та клонування (5 питань)

### Q17: Ресурси знімків
Які три основні ресурси, пов'язані зі знімками?

<details>
<summary>Відповідь</summary>

1. **VolumeSnapshotClass** — визначає, як створюються знімки (область кластера)
2. **VolumeSnapshot** — запит на знімок PVC (у namespace)
3. **VolumeSnapshotContent** — фактичне посилання на знімок (область кластера)

Подібний патерн до StorageClass, PVC та PV.

</details>

### Q18: Передумови для знімків
Що повинно бути встановлене, перш ніж ви зможете використовувати знімки томів?

<details>
<summary>Відповідь</summary>

1. **CRD для знімків** — визначення користувацьких ресурсів
2. **Контролер знімків** — керує життєвим циклом знімків
3. **CSI-драйвер з підтримкою знімків** — фактично створює знімки

Застарілі вбудовані (in-tree) плагіни томів не підтримують знімки.

</details>

### Q19: Відновлення зі знімка
Яке поле в специфікації PVC вказує, що він має бути створений зі знімка?

<details>
<summary>Відповідь</summary>

Поле **dataSource**:

```yaml
spec:
  dataSource:
    name: snapshot-name
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

</details>

### Q20: Клон vs Знімок
Яка різниця між клонуванням PVC та відновленням зі знімка?

<details>
<summary>Відповідь</summary>

**Клонування** (`kind: PersistentVolumeClaim` у dataSource):
- Пряма копія з PVC до нового PVC
- Без проміжного артефакту
- Однокроковий процес

**Відновлення зі знімка** (`kind: VolumeSnapshot` у dataSource):
- Два кроки: створити знімок, потім відновити
- Знімок зберігається і може бути використаний повторно
- Можливість резервного копіювання на момент часу

</details>

### Q21: Обмеження namespace для клонування
Чи можна клонувати PVC з іншого namespace?

<details>
<summary>Відповідь</summary>

**Ні**. Клонування PVC вимагає, щоб джерело та призначення були в **одному namespace**. Клонування між namespace не підтримується.

Для копіювання даних між namespace використовуйте VolumeSnapshots (VolumeSnapshotContent має область видимості кластера).

</details>

---

## Секція 5: Усунення несправностей (4 питання)

### Q22: Перший крок налагодження
Под застряг у ContainerCreating. Яку команду виконати першою?

<details>
<summary>Відповідь</summary>

```bash
k describe pod <pod-name>
```

Перевірте секцію Events на наявність помилок, пов'язаних з томами, як-от FailedMount, FailedAttach або конкретних повідомлень про помилки щодо PVC.

</details>

### Q23: Налагодження Pending PVC
PVC застряг у стані Pending. Яка команда розкриє причину?

<details>
<summary>Відповідь</summary>

```bash
k describe pvc <pvc-name>
```

Секція Events покаже:
- "no persistent volumes available" — немає відповідного PV
- "storageclass not found" — неправильне ім'я SC
- Немає подій, але StorageClass використовує WaitForFirstConsumer — очікувано, створіть Под

</details>

### Q24: Помилка Multi-Attach
Що означає "Multi-Attach error" і як це виправити?

<details>
<summary>Відповідь</summary>

Помилка означає, що **RWO том приєднаний до кількох вузлів**, зазвичай від старого Пода, який не був коректно розмонтований.

Виправлення:
1. Видаліть старий Под, що використовує том
2. Якщо застряг: `k delete pod <name> --force --grace-period=0`
3. Перевірте VolumeAttachments: `k get volumeattachment`

</details>

### Q25: Виправлення відмови в дозволі
Под монтує том, але отримує "permission denied" при записі. Яке ймовірне виправлення?

<details>
<summary>Відповідь</summary>

Встановіть securityContext Пода:

```yaml
spec:
  securityContext:
    fsGroup: 1000        # ID групи для файлів тому
  containers:
  - name: app
    securityContext:
      runAsUser: 1000    # ID користувача в контейнері
```

fsGroup забезпечує доступність тому для користувача контейнера.

</details>

---

## Оцінювання

Підрахуйте правильні відповіді:

| Бал | Результат |
|-----|----------|
| 23–25 | Відмінно! Готові до Частини 5 |
| 20–22 | Добре. Перегляньте пропущені теми, потім продовжуйте |
| 16–19 | Перегляньте відповідні модулі перед продовженням |
| <16 | Повторно вивчіть модулі Частини 4 |

---

## Ресурси для повторення

Якщо ви набрали менше 80%, перегляньте ці модулі:

- **Питання про томи (Q1–Q5)**: [Модуль 4.1](module-4.1-volumes.uk.md)
- **Питання про PV/PVC (Q6–Q11)**: [Модуль 4.2](module-4.2-pv-pvc.uk.md)
- **Питання про StorageClass (Q12–Q16)**: [Модуль 4.3](module-4.3-storageclasses.uk.md)
- **Питання про знімки (Q17–Q21)**: [Модуль 4.4](module-4.4-snapshots.uk.md)
- **Питання про усунення несправностей (Q22–Q25)**: [Модуль 4.5](module-4.5-troubleshooting.uk.md)

---

## Наступна частина

Переходьте до [Частина 5: Усунення несправностей](../part5-troubleshooting/README.md), щоб вивчити систематичні підходи до діагностики та виправлення проблем кластерів Kubernetes.
