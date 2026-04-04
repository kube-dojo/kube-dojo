---
title: "Модуль 1.4: Томи для розробників"
slug: k8s/ckad/part1-design-build/module-1.4-volumes
sidebar:
  order: 4
lab:
  id: ckad-1.4-volumes
  url: https://killercoda.com/kubedojo/scenario/ckad-1.4-volumes
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
en_commit: 0000000000000000000000000000000000000000
---
> **Складність**: `[MEDIUM]` — Необхідний для застосунків зі збереженням стану
>
> **Час на виконання**: 40–50 хвилин
>
> **Передумови**: Модуль 1.3 (Піди з кількома контейнерами)

---

## Результати навчання

Після завершення цього модуля ви зможете:
- **Створити** Піди з томами emptyDir, hostPath та PersistentVolumeClaim
- **Налаштувати** монтування томів для обміну даними між контейнерами в одному Поді
- **Діагностувати** помилки монтування томів, включно з проблемами прав доступу та відсутніми PVC
- **Пояснити** різницю між ефемерними та постійними томами та коли використовувати кожен

---

## Чому цей модуль важливий

Контейнери ефемерні — при перезапуску всі дані втрачаються. Для реальних застосунків потрібне постійне зберігання: бази даних потребують надійних даних, застосунки потребують спільних файлів, а контейнерам потрібні способи обміну даними.

CKAD тестує практичне використання томів: монтування ConfigMaps, обмін даними між контейнерами та використання постійного зберігання. Ви не будете керувати StorageClasses (це CKA), але будете використовувати PersistentVolumeClaims.

> **Аналогія зі шухлядою стола**
>
> Файлова система контейнера — як дошка для записів — корисна, поки ви поруч, але стирається, коли ви йдете. Том `emptyDir` — як спільний стіл у кімнаті для нарад — усі учасники наради можуть ним користуватися, але він очищується, коли нарада закінчується. PersistentVolume — як ваша шухляда стола — вона ваша, зберігається між робочими днями і містить ваші важливі файли.

---

## Типи томів для розробників

### Короткий довідник

| Тип тому | Збереження | Спільний доступ | Сценарій використання |
|----------|------------|-----------------|----------------------|
| `emptyDir` | Час життя Підa | Між контейнерами | Тимчасовий простір, кеші |
| `hostPath` | Час життя вузла | Ні | Доступ до вузла (лише для розробки) |
| `configMap` | Час життя кластера | Тільки читання | Конфігураційні файли |
| `secret` | Час життя кластера | Тільки читання | Чутливі дані |
| `persistentVolumeClaim` | Поза Підом | Залежить | Бази даних, застосунки зі збереженням стану |
| `projected` | Різне | Тільки читання | Об'єднання кількох джерел |

---

## emptyDir: Тимчасове спільне сховище

`emptyDir` створюється при запуску Підa і видаляється при видаленні Підa. Ідеальний для:
- Обміну файлами між контейнерами
- Тимчасового простору для обчислень
- Кешів

### Базовий emptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: emptydir-demo
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "echo 'Hello' > /data/message && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /data
  - name: reader
    image: busybox
    command: ["sh", "-c", "cat /data/message && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /data
  volumes:
  - name: shared
    emptyDir: {}
```

### emptyDir в оперативній пам'яті

Для швидкого тимчасового простору:

```yaml
volumes:
- name: cache
  emptyDir:
    medium: Memory      # Використовує RAM замість диска
    sizeLimit: 100Mi    # Обмеження використання пам'яті
```

---

## Томи ConfigMap

Монтуйте ConfigMaps як файли. Кожен ключ стає файлом.

### Створення ConfigMap

```bash
# З літералів
k create configmap app-config \
  --from-literal=log_level=debug \
  --from-literal=api_url=http://api.example.com

# З файлу
k create configmap nginx-config --from-file=nginx.conf
```

### Монтування як том

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-demo
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "cat /config/log_level && sleep 3600"]
    volumeMounts:
    - name: config
      mountPath: /config
  volumes:
  - name: config
    configMap:
      name: app-config
```

Результат:
```
/config/
├── log_level     # Містить "debug"
└── api_url       # Містить "http://api.example.com"
```

> **Зупиніться та подумайте**: Коли ви монтуєте ConfigMap як том до `/etc/app`, що станеться з будь-якими існуючими файлами, які вже знаходяться в `/etc/app` всередині образу контейнера? Що робити, якщо ви хочете додати лише один файл, не видаляючи решту?

### Монтування конкретних ключів

```yaml
volumes:
- name: config
  configMap:
    name: app-config
    items:
    - key: log_level
      path: logging/level.txt   # Власний шлях
```

### SubPath: Монтування одного файлу без перезапису

```yaml
volumeMounts:
- name: config
  mountPath: /etc/app/config.yaml    # Конкретний файл
  subPath: config.yaml               # Ключ з ConfigMap
```

---

## Томи Secret

Як ConfigMaps, але для чутливих даних. Змонтовані файли зберігаються в tmpfs (в оперативній пам'яті).

### Створення Secret

```bash
k create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secret123
```

### Монтування Secret

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-demo
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "cat /secrets/password && sleep 3600"]
    volumeMounts:
    - name: db-secrets
      mountPath: /secrets
      readOnly: true
  volumes:
  - name: db-secrets
    secret:
      secretName: db-creds
```

### Права доступу до файлів

```yaml
volumes:
- name: db-secrets
  secret:
    secretName: db-creds
    defaultMode: 0400    # Тільки читання для власника
```

---

## PersistentVolumeClaim (PVC)

Для даних, що переживають перезапуски Підів. Як розробник, ви запитуєте сховище через PVC; кластер його забезпечує.

### Створення PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
  - ReadWriteOnce         # RWO, ROX, RWX
  resources:
    requests:
      storage: 1Gi
  # storageClassName: fast  # Необов'язково: конкретний клас
```

> **Подумайте**: Ви розробляєте Pod, який записує завантаження користувачів у том. Якщо Pod аварійно завершує роботу і перепризначається на інший вузол, що станеться із завантаженими файлами за допомогою `emptyDir` проти `PersistentVolumeClaim`? Ця відмінність є критичною для іспиту.

### Режими доступу

| Режим | Скорочення | Опис |
|-------|------------|------|
| `ReadWriteOnce` | RWO | Один вузол може монтувати для читання-запису |
| `ReadOnlyMany` | ROX | Багато вузлів можуть монтувати тільки для читання |
| `ReadWriteMany` | RWX | Багато вузлів можуть монтувати для читання-запису |

### Використання PVC у Подi

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pvc-demo
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: data-pvc
```

### Імперативне створення PVC

```bash
# Прямої імперативної команди немає, але YAML пишеться швидко
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
EOF
```

---

## Projected-томи

Об'єднують кілька джерел в одну точку монтування.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-demo
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "ls -la /projected && sleep 3600"]
    volumeMounts:
    - name: all-config
      mountPath: /projected
  volumes:
  - name: all-config
    projected:
      sources:
      - configMap:
          name: app-config
      - secret:
          name: app-secrets
      - downwardAPI:
          items:
          - path: "labels"
            fieldRef:
              fieldPath: metadata.labels
```

---

## Типові паттерни томів

### Паттерн 1: Спільний тимчасовий простір

```yaml
spec:
  containers:
  - name: processor
    image: processor
    volumeMounts:
    - name: scratch
      mountPath: /tmp/work
  - name: uploader
    image: uploader
    volumeMounts:
    - name: scratch
      mountPath: /data
  volumes:
  - name: scratch
    emptyDir: {}
```

### Паттерн 2: Конфігурація + Секрети

```yaml
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: config
      mountPath: /etc/app
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: app-config
  - name: secrets
    secret:
      secretName: app-secrets
```

### Паттерн 3: Init-контейнер готує дані

```yaml
spec:
  initContainers:
  - name: download
    image: curlimages/curl
    command: ["curl", "-o", "/data/app.tar", "http://example.example.com/app.tar"]
    volumeMounts:
    - name: app-data
      mountPath: /data
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: app-data
      mountPath: /app
  volumes:
  - name: app-data
    emptyDir: {}
```

---

> **Що станеться, якщо**: Ви оновите ConfigMap, змонтований як том у запущеному Pod за допомогою `subPath`. Чи побачить Pod оновлені значення? А що щодо без `subPath`? Розуміння цієї різниці може заощадити ваш час на налагодження під час іспиту.

## Усунення проблем з томами

### Перевірка статусу тому

```bash
# Томи Підa
k describe pod myapp | grep -A10 Volumes

# Статус PVC
k get pvc

# Деталі PVC
k describe pvc data-pvc
```

### Типові проблеми

| Симптом | Причина | Рішення |
|---------|---------|---------|
| Pod застряг у Pending | PVC не прив'язано | Перевірте наявність PV |
| Відмова у доступі | Неправильний режим/користувач | Встановіть `securityContext.fsGroup` |
| Файл не знайдено | Неправильний mountPath | Перевірте відповідність шляхів |
| ConfigMap не оновлюється | Змонтовані файли кешуються | Перезапустіть Під або обережно використовуйте subPath |

### Виправлення проблем з правами доступу

```yaml
spec:
  securityContext:
    fsGroup: 1000    # ID групи для файлів тому
  containers:
  - name: app
    image: myapp
    securityContext:
      runAsUser: 1000
```

---

## Чи знали ви?

- **ConfigMaps та Secrets є зрештою узгодженими.** Коли ви їх оновлюєте, Піди бачать зміни протягом хвилини — але НЕ якщо ви використали монтування через `subPath`. Монтування subPath — це знімки, що не оновлюються автоматично.

- **emptyDir за замовчуванням використовує диск вузла**, але може використовувати RAM (`medium: Memory`). Томи в оперативній пам'яті швидші, але враховуються в лімітах пам'яті контейнера.

- **Видалення PVC блокується**, якщо Pod його використовує. Спочатку видаліть Pod, потім PVC. Встановіть `persistentVolumeReclaimPolicy: Delete` для автоматичного видалення базового сховища при видаленні PVC.

---

## Типові помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Забули `volumeMounts` | Том визначено, але не змонтовано | Додайте mount до контейнера |
| Неправильний `mountPath` | Файли з'являються у неочікуваному місці | Ретельно перевірте шляхи |
| Використання `subPath` для оновлень у реальному часі | Оновлення не поширюються | Уникайте subPath або перезапустіть Під |
| PVC з неправильним режимом доступу | Багатовузлові застосунки не працюють | Використовуйте RWX для спільного доступу |
| Відсутнє визначення тому | Під не запускається | Визначте том у `spec.volumes` |

---

## Тест

1.  **Pod розробника кешує оброблені мініатюри в `/tmp/cache`. Щоразу, коли Pod перезапускається, кеш втрачається, а мініатюри потрібно генерувати заново, що спричиняє 5-хвилинний період запуску. Вони використовують том `emptyDir`. Чи є `emptyDir` правильним вибором тут, чи їм слід перейти на PVC?**
    <details>
    <summary>Відповідь</summary>
    Це залежить від того, чи потрібно кешу виживати після перезапуску Pod. `emptyDir` прив'язаний до життєвого циклу Pod — дані втрачаються, коли Pod видаляється або перепризначається. Якщо 5-хвилинний період запуску неприйнятний, перейдіть на `PersistentVolumeClaim` з режимом доступу `ReadWriteOnce`. Однак, якщо Pod рідко перезапускається і кеш можна відновити, `emptyDir` простіший і не споживає постійного зберігання. Для проміжного рішення використовуйте `emptyDir` з `medium: Memory` для швидшої продуктивності кешу протягом життєвого циклу Pod, приймаючи те, що перезапуски очищають його.
    </details>

2.  **Вашому застосунку потрібен файл конфігурації за адресою `/etc/app/config.yaml`, але монтування ConfigMap до `/etc/app` видаляє інші файли, які вже знаходяться в цьому каталозі. Як змонтувати лише один файл конфігурації, не перезаписуючи вміст каталогу?**
    <details>
    <summary>Відповідь</summary>
    Використовуйте `subPath` у монтуванні тому:
    ```yaml
    volumeMounts:
    - name: config
      mountPath: /etc/app/config.yaml
      subPath: config.yaml
    ```
    Це монтує лише конкретний ключ як один файл, зберігаючи всі інші файли в `/etc/app`. Однак, пам'ятайте про компроміс: монтування `subPath` не отримують автоматичних оновлень при зміні ConfigMap. Якщо вам потрібні оперативні оновлення конфігурації, змонтуйте весь ConfigMap до іншого каталогу (наприклад, `/config`) і нехай ваш застосунок читає звідти.
    </details>

3.  **Ви розгортаєте веб-застосунок з 3 репліками, яким усім потрібно читати та записувати в одне спільне файлове сховище для завантажень користувачів. Ваш PVC використовує `ReadWriteOnce`. Користувачі повідомляють, що завантаження іноді зникають. Що не так?**
    <details>
    <summary>Відповідь</summary>
    `ReadWriteOnce` (RWO) дозволяє лише одному вузлу монтувати том для читання-запису. Якщо ваші 3 репліки знаходяться на різних вузлах, лише Pods на одному вузлі можуть фактично записувати. Pods на інших вузлах або не можуть змонтувати, або монтують лише для читання, що призводить до втрати завантажень. Перейдіть на режим доступу `ReadWriteMany` (RWX), який вимагає сховища, що підтримує його (NFS, EFS, Azure Files тощо). Не всі StorageClass підтримують RWX — перевірте за допомогою `kubectl get storageclass` та документації вашого кластера.
    </details>

4.  **Pod має змонтовані томи `configMap` та `secret`. Після оновлення Secret за допомогою `kubectl edit secret`, Pod все ще показує старі значення secret. Том ConfigMap в тому ж Pod АВТОМАТИЧНО оновлюється. Що пояснює цю невідповідність?**
    <details>
    <summary>Відповідь</summary>
    Secret, ймовірно, змонтований за допомогою `subPath`, тоді як ConfigMap змонтований як повний каталог. Монтування `subPath` — це знімки, зроблені під час запуску Pod і ніколи не оновлюються автоматично — це стосується як ConfigMaps, так і Secrets. Монтування повного каталогу є зрештою узгодженими та оновлюються приблизно протягом 60 секунд. Щоб виправити, або видаліть монтування `subPath`, або перезапустіть Pod, щоб він отримав нові значення Secret. У виробництві багато команд використовують `kubectl rollout restart`, щоб змусити Pods перемонтувати оновлені Secrets.
    </details>

---

## Практична вправа

**Завдання**: Створити повний застосунок з кількома типами томів.

**Сценарій**: Побудуйте застосунок, що:
1. Використовує ConfigMap для конфігурації
2. Використовує Secret для облікових даних
3. Використовує emptyDir для спільного кешу між контейнерами
4. Використовує PVC для постійних даних

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
data:
  config.json: |
    {"logLevel": "info", "cacheEnabled": true}
---
apiVersion: v1
kind: Secret
metadata:
  name: app-creds
type: Opaque
stringData:
  api-key: super-secret-key
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 100Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: volumes-app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/app
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
    - name: cache
      mountPath: /tmp/cache
    - name: data
      mountPath: /data
  - name: cache-warmer
    image: busybox
    command: ["sh", "-c", "while true; do echo 'Cache data' > /cache/warm; sleep 30; done"]
    volumeMounts:
    - name: cache
      mountPath: /cache
  volumes:
  - name: config
    configMap:
      name: app-settings
  - name: secrets
    secret:
      secretName: app-creds
  - name: cache
    emptyDir: {}
  - name: data
    persistentVolumeClaim:
      claimName: app-data
```

**Перевірка:**
```bash
# Застосувати всі ресурси
k apply -f volumes-app.yaml

# Перевірити, що Під працює
k get pod volumes-app

# Перевірити монтування
k exec volumes-app -c app -- ls -la /etc/app
k exec volumes-app -c app -- ls -la /etc/secrets
k exec volumes-app -c app -- ls -la /tmp/cache
k exec volumes-app -c app -- ls -la /data

# Перевірити, що PVC прив'язано
k get pvc app-data

# Очищення
k delete pod volumes-app
k delete pvc app-data
k delete configmap app-settings
k delete secret app-creds
```

---

## Практичні вправи

### Вправа 1: Спільний emptyDir (Ціль: 3 хвилини)

```bash
# Створити Під зі спільним emptyDir
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: shared-pod
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "echo hello > /shared/msg && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /shared
  - name: reader
    image: busybox
    command: ["sh", "-c", "sleep 5 && cat /shared/msg && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /shared
  volumes:
  - name: shared
    emptyDir: {}
EOF

# Перевірити, що спільний доступ працює
k logs shared-pod -c reader

# Очищення
k delete pod shared-pod
```

### Вправа 2: Том ConfigMap (Ціль: 3 хвилини)

```bash
# Створити ConfigMap
k create configmap web-config --from-literal=index.html="Welcome to CKAD!"

# Створити Під з ConfigMap
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web
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
      name: web-config
EOF

# Перевірити вміст
k exec web -- cat /usr/share/nginx/html/index.html

# Очищення
k delete pod web
k delete cm web-config
```

### Вправа 3: Том Secret (Ціль: 3 хвилини)

```bash
# Створити Secret
k create secret generic db-pass --from-literal=password=mysecret

# Змонтувати у Під
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secret-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "cat /secrets/password && sleep 3600"]
    volumeMounts:
    - name: creds
      mountPath: /secrets
      readOnly: true
  volumes:
  - name: creds
    secret:
      secretName: db-pass
EOF

# Перевірити, що secret змонтовано
k logs secret-pod

# Очищення
k delete pod secret-pod
k delete secret db-pass
```

### Вправа 4: Використання PVC (Ціль: 4 хвилини)

```bash
# Створити PVC
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 50Mi
EOF

# Використати у Піді
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pvc-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: test-pvc
EOF

# Перевірити, що PVC прив'язано
k get pvc test-pvc

# Записати дані
k exec pvc-pod -- sh -c "echo 'Persistent!' > /data/test.txt"
k exec pvc-pod -- cat /data/test.txt

# Очищення
k delete pod pvc-pod
k delete pvc test-pvc
```

### Вправа 5: Projected-том (Ціль: 4 хвилини)

```bash
# Створити джерела
k create cm proj-config --from-literal=config=value
k create secret generic proj-secret --from-literal=secret=hidden

# Створити Під з projected-томом
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: proj-pod
  labels:
    app: projected
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "ls -la /projected && sleep 3600"]
    volumeMounts:
    - name: combined
      mountPath: /projected
  volumes:
  - name: combined
    projected:
      sources:
      - configMap:
          name: proj-config
      - secret:
          name: proj-secret
EOF

# Перевірити об'єднані файли
k exec proj-pod -- ls /projected

# Очищення
k delete pod proj-pod
k delete cm proj-config
k delete secret proj-secret
```

### Вправа 6: Повне завдання з томами (Ціль: 6 хвилин)

**Створіть з пам'яті — без підказок:**

Створіть Під `data-processor`, що:
1. Init-контейнер завантажує "дані" (симуляція через echo)
2. Основний контейнер обробляє дані (nginx)
3. Sidecar логує статус обробки
4. Використовує emptyDir для спільних даних
5. Монтує ConfigMap з налаштуваннями обробки

<details>
<summary>Відповідь</summary>

```bash
# Створити ConfigMap
k create cm processing-config --from-literal=mode=fast

# Створити Під
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-processor
spec:
  initContainers:
  - name: downloader
    image: busybox
    command: ["sh", "-c", "echo 'Downloaded data' > /data/input.txt"]
    volumeMounts:
    - name: data
      mountPath: /data
  containers:
  - name: processor
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
    - name: config
      mountPath: /etc/config
  - name: logger
    image: busybox
    command: ["sh", "-c", "while true; do echo Processing $(cat /data/input.txt); sleep 5; done"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
  - name: config
    configMap:
      name: processing-config
EOF

# Перевірка
k get pod data-processor
k logs data-processor -c logger
k exec data-processor -c processor -- cat /etc/config/mode

# Очищення
k delete pod data-processor
k delete cm processing-config
```

</details>

---

## Наступний модуль

[Підсумковий тест Частини 1](../part1-cumulative-quiz/) — Перевірте свої знання з проєктування та збірки застосунків.
