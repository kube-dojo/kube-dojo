---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2.7: ConfigMap \u0442\u0430 Secret"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.7-configmaps-secrets
sidebar: 
  order: 8
lab: 
  id: cka-2.7-configmaps-secrets
  url: https://killercoda.com/kubedojo/scenario/cka-2.7-configmaps-secrets
  duration: "45 min"
  difficulty: intermediate
  environment: kubernetes
---
**Складність:** `[MEDIUM]` | **Час на виконання:** 55 хвилин | **Вага CKA:** Частина 15%

## Передумови

Перш ніж починати цей модуль, переконайтеся, що ви:
- Пройшли [Модуль 2.1: Поди — поглиблено](module-2.1-pods/) (структура специфікації Пода)
- Пройшли [Модуль 2.2: Deployment](module-2.2-deployments/) (оновлення конфігурацій)
- Маєте працюючий кластер Kubernetes (kind або minikube)
- Розумієте основи змінних середовища

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Створити** ConfigMaps та Secrets з файлів, літералів та директорій
- **Змонтувати** конфігурацію як змінні середовища та volume mounts і пояснити, коли використовувати кожен спосіб
- **Імплементувати** незмінні ConfigMaps/Secrets та пояснити, коли незмінність важлива
- **Діагностувати** проблеми конфігурації (неправильний шлях монтування, відсутній ключ, помилки кодування base64)

---

## Чому цей модуль важливий

Кожному реальному застосунку потрібна конфігурація. Рядки підключення до бази даних, прапорці функціональності, API-ключі, сертифікати — все це не можна захардкодити. Kubernetes надає два примітиви для передачі конфігурації в Поди: **ConfigMap** для нечутливих даних і **Secret** для чутливих даних.

**На іспиті CKA** вам потрібно буде:
- Створювати ConfigMap та Secret із файлів, літералів і маніфестів
- Передавати їх як змінні середовища або змонтовані файли
- Оновлювати конфігурації без перебудови контейнерів
- Розуміти наслідки безпеки Secret

Помилка з цим у продакшені означає витік облікових даних або зламаний застосунок. Правильне налаштування — це безпечні та гнучкі розгортання.

---

## Чи знали ви?

- **Secret не зашифровані за замовчуванням** — вони лише закодовані в base64. Будь-хто з доступом до API може їх розкодувати. Шифрування у стані спокою потребує явного налаштування.

- **Оновлення ConfigMap поширюються автоматично**, якщо змонтовані як томи, але НЕ коли використовуються як змінні середовища. Змінні середовища потребують перезапуску Пода.

- **Обмеження 1 МБ** для ConfigMap і Secret існує тому, що вони зберігаються в etcd. Для більших конфігурацій потрібні інші рішення (зовнішні сховища конфігурацій, init-контейнери, що завантажують конфігурації).

---

## Аналогія з реальним світом

Уявіть ConfigMap і Secret як налаштування готельного номера:

- **ConfigMap** — це як меню обслуговування номерів, інструкції до Wi-Fi та список телеканалів. Усі можуть їх бачити, і вони змінюють враження гостя без ремонту кімнати.

- **Secret** — це як код сейфа та комбінація дверного замка. Вони мають залишатися приватними, і передача їх стороннім людям спричиняє серйозні проблеми.

Обидва відокремлені від самої кімнати (вашого образу контейнера) — вам не потрібно перебудовувати кімнату, щоб змінити меню або код сейфа.

---

## Розуміння ConfigMap

### Що зберігають ConfigMap

ConfigMap містять пари «ключ-значення» нечутливих конфігураційних даних:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  # Прості пари «ключ-значення»
  LOG_LEVEL: "debug"
  MAX_CONNECTIONS: "100"
  FEATURE_FLAGS: "new-ui,beta-api"

  # Цілі конфігураційні файли
  config.json: |
    {
      "database": {
        "host": "db.example.com",
        "port": 5432
      },
      "cache": {
        "enabled": true,
        "ttl": 300
      }
    }

  nginx.conf: |
    server {
      listen 80;
      server_name localhost;
      location / {
        root /usr/share/nginx/html;
      }
    }
```

Ключові концепції:
- **data**: рядкові пари «ключ-значення» (найпоширеніший варіант)
- **binaryData**: двійковий вміст, закодований у base64
- **immutable**: якщо встановлено `true`, запобігає змінам (оптимізація продуктивності)

### Створення ConfigMap

**Спосіб 1: З літеральних значень (улюблений на іспиті)**

```bash
# Одне значення
k create configmap app-config --from-literal=LOG_LEVEL=debug

# Кілька значень
k create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=MAX_CONNECTIONS=100 \
  --from-literal=CACHE_ENABLED=true
```

**Спосіб 2: З файлу**

```bash
# Створіть конфігураційний файл
cat > config.properties <<EOF
database.host=db.example.com
database.port=5432
cache.enabled=true
EOF

# Створіть ConfigMap із файлу
k create configmap app-config --from-file=config.properties

# Ключем стає ім'я файлу, значенням — вміст файлу
# Результат: data: { "config.properties": "database.host=db.example.com\n..." }
```

**Спосіб 3: З файлу з власним ключем**

```bash
# Вкажіть назву ключа
k create configmap app-config --from-file=app.conf=config.properties
# Результат: data: { "app.conf": "..." }
```

**Спосіб 4: З директорії**

```bash
# Усі файли в директорії стають ключами
k create configmap app-config --from-file=./config-dir/
```

**Спосіб 5: З env-файлу**

```bash
cat > config.env <<EOF
LOG_LEVEL=debug
MAX_CONNECTIONS=100
EOF

k create configmap app-config --from-env-file=config.env
# Кожен рядок стає окремою парою «ключ-значення» (не одним ключем із вмістом файлу)
```

### Використання ConfigMap у Подах

**Варіант 1: Як змінні середовища (конкретні ключі)**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: LOG_LEVEL           # Ім'я в контейнері
      valueFrom:
        configMapKeyRef:
          name: app-config      # Ім'я ConfigMap
          key: LOG_LEVEL        # Ключ у ConfigMap
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host
          optional: true        # Не падати, якщо ключ відсутній
```

**Варіант 2: Усі ключі як змінні середовища**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    envFrom:
    - configMapRef:
        name: app-config
      prefix: APP_              # Необов'язково: префікс для всіх змінних
```

Усі ключі ConfigMap стають змінними середовища. З префіксом `LOG_LEVEL` стає `APP_LOG_LEVEL`.

**Варіант 3: Як змонтований том (увесь ConfigMap)**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config    # Директорія з усіма файлами
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      # Кожен ключ стає файлом у /etc/config/
```

**Варіант 4: Монтування конкретних ключів як файлів**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: config-volume
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf      # Монтування одного файлу, а не директорії
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      items:
      - key: nginx.conf        # Ключ із ConfigMap
        path: nginx.conf       # Ім'я файлу в томі
```

### Поведінка оновлення ConfigMap

| Спосіб передачі | Автооновлення? | Примітки |
|-----------------|----------------|----------|
| Змінна середовища | Ні | Потребує перезапуску Пода |
| Монтування тому | Так | Затримка ~1 хвилина (синхронізація kubelet) |
| Монтування subPath | Ні | Потребує перезапуску Пода |

---

## Розуміння Secret

### Типи Secret

Kubernetes підтримує кілька типів Secret:

| Тип | Опис | Створюється автоматично? |
|-----|------|--------------------------|
| `Opaque` | Загальні пари «ключ-значення» | Ні (за замовчуванням) |
| `kubernetes.io/tls` | TLS-сертифікат + ключ | Ні |
| `kubernetes.io/dockerconfigjson` | Автентифікація Docker-реєстру | Ні |
| `kubernetes.io/service-account-token` | Токен ServiceAccount | Так |
| `kubernetes.io/basic-auth` | Ім'я користувача + пароль | Ні |
| `kubernetes.io/ssh-auth` | Приватний SSH-ключ | Ні |

### Створення Secret

**Спосіб 1: Загальний Secret із літералів**

```bash
# Значення автоматично кодуються в base64
k create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password='S3cur3P@ss!'
```

**Спосіб 2: З файлів**

```bash
# Створіть файли з обліковими даними
echo -n 'admin' > username.txt
echo -n 'S3cur3P@ss!' > password.txt

k create secret generic db-creds \
  --from-file=username=username.txt \
  --from-file=password=password.txt

# Видаліть файли
rm username.txt password.txt
```

**Спосіб 3: TLS Secret**

```bash
# З наявного сертифіката та ключа
k create secret tls app-tls \
  --cert=tls.crt \
  --key=tls.key
```

**Спосіб 4: Secret Docker-реєстру**

```bash
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@example.com
```

**Спосіб 5: З YAML (ручне кодування base64)**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
data:
  # Значення мають бути закодовані в base64
  username: YWRtaW4=           # echo -n 'admin' | base64
  password: UzNjdXIzUEBzcyE=   # echo -n 'S3cur3P@ss!' | base64
```

Або використовуйте `stringData` для звичайного тексту (Kubernetes закодує сам):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
stringData:
  username: admin              # Звичайний текст — Kubernetes закодує
  password: S3cur3P@ss!
```

### Використання Secret у Подах

**Варіант 1: Як змінні середовища**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
```

**Варіант 2: Усі ключі як змінні середовища**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    envFrom:
    - secretRef:
        name: db-creds
      prefix: DB_
```

**Варіант 3: Як змонтовані файли**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true           # Найкраща практика для Secret
  volumes:
  - name: secret-volume
    secret:
      secretName: db-creds
      defaultMode: 0400        # Обмежити права доступу
```

**Варіант 4: Монтування TLS-сертифіката**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: tls-certs
      mountPath: /etc/nginx/ssl
      readOnly: true
  volumes:
  - name: tls-certs
    secret:
      secretName: app-tls
      items:
      - key: tls.crt
        path: server.crt
      - key: tls.key
        path: server.key
        mode: 0400             # Обмежені права для приватного ключа
```

### Декодування Secret

```bash
# Переглянути закодовані значення
k get secret db-creds -o yaml

# Декодувати конкретний ключ
k get secret db-creds -o jsonpath='{.data.password}' | base64 -d

# Декодувати всі ключі
k get secret db-creds -o go-template='{{range $k,$v := .data}}{{$k}}: {{$v | base64decode}}{{"\n"}}{{end}}'
```

---

## Міркування щодо безпеки

### Secret не є справді секретними (за замовчуванням)

Base64 — це кодування, а не шифрування:

```bash
# Будь-хто може декодувати
echo 'UzNjdXIzUEBzcyE=' | base64 -d
# Вивід: S3cur3P@ss!
```

**Заходи безпеки:**

1. **RBAC**: обмежте, хто може читати Secret
2. **Шифрування у стані спокою**: увімкніть шифрування etcd
3. **Журнал аудиту**: відстежуйте доступ до Secret
4. **Зовнішні сховища секретів**: HashiCorp Vault, AWS Secrets Manager

### Змінні середовища проти монтування томів

| Аспект | Змінні середовища | Монтування томів |
|--------|-------------------|------------------|
| Видимість | `kubectl exec -- env` показує їх | Потрібно явно читати файли |
| Успадкування процесами | Дочірні процеси успадковують | Потрібно явно зчитувати |
| Ризик потрапляння до логів | Часто логуються випадково | Менша ймовірність потрапити до логів |
| Оновлення | Потребує перезапуску | Автооновлення (~1 хв) |

**Найкраща практика**: використовуйте монтування томів для чутливих Secret, щоб зменшити ризик випадкового розкриття.

### Незмінність Secret

Для продакшену розгляньте незмінні Secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds-v1
type: Opaque
immutable: true              # Не можна змінити
data:
  password: UzNjdXIzUEBzcyE=
```

Переваги:
- Запобігає випадковим змінам
- Продуктивність: kubelet не потребує стежити за оновленнями
- Версіонування: використовуйте іменування (v1, v2) для ротації

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Забули base64 у YAML | Некоректні дані Secret | Використовуйте `stringData` для звичайного тексту |
| Не використали `-n` з echo | Символ нового рядка в закодованому значенні | `echo -n 'value'` |
| Очікування оновлення змінних середовища | Застосунок використовує застарілу конфігурацію | Перезапустіть Под або використовуйте монтування тому |
| Захардкоджені Secret в образі | Ризик безпеки, негнучкість | Завжди використовуйте Secret |
| Коміт Secret до git | Облікові дані розкриті | Використовуйте `.gitignore`, зовнішні сховища |
| Надто широкі права RBAC | Будь-хто може читати Secret | Обмежте за допомогою Role/RoleBinding |
| Не встановлено readOnly для тому | Контейнер може змінити | Завжди `readOnly: true` |
| Ігнорування обмеження subPath | Конфігурація не оновлюється | Використовуйте повне монтування тому, коли можливо |

---

## Практична вправа

### Сценарій: Налаштування веб-застосунку

Вам потрібно розгорнути веб-застосунок із:
- Конфігураційним файлом (ConfigMap)
- Обліковими даними бази даних (Secret)
- Прапорцями функціональності (ConfigMap як змінні середовища)

### Завдання 1: Створення конфігурації

```bash
# Створіть простір імен
k create ns config-demo

# Створіть ConfigMap із конфігурацією застосунку
k create configmap app-config -n config-demo \
  --from-literal=LOG_LEVEL=info \
  --from-literal=CACHE_TTL=300 \
  --from-literal=FEATURE_NEW_UI=true

# Створіть конфігураційний файл nginx
cat > /tmp/nginx.conf <<EOF
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF

k create configmap nginx-config -n config-demo \
  --from-file=nginx.conf=/tmp/nginx.conf
```

### Завдання 2: Створення Secret

```bash
# Облікові дані бази даних
k create secret generic db-creds -n config-demo \
  --from-literal=DB_USER=appuser \
  --from-literal=DB_PASS='Pr0dP@ssw0rd!'

# Перевірка
k get secret db-creds -n config-demo -o yaml
```

### Завдання 3: Розгортання застосунку

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: webapp
  namespace: config-demo
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
    # Змінні середовища з ConfigMap
    envFrom:
    - configMapRef:
        name: app-config
      prefix: APP_
    # Змінні середовища з Secret
    env:
    - name: DATABASE_USER
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: DB_USER
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: DB_PASS
    volumeMounts:
    # Монтування конфігурації nginx
    - name: nginx-config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
    # Монтування Secret як файлів
    - name: db-creds
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: nginx-config
    configMap:
      name: nginx-config
  - name: db-creds
    secret:
      secretName: db-creds
      defaultMode: 0400
EOF
```

### Завдання 4: Перевірка конфігурації

```bash
# Перевірте, що Под запущений
k get pod webapp -n config-demo

# Перевірте змінні середовища
k exec webapp -n config-demo -- env | grep -E "APP_|DATABASE"

# Перевірте змонтований конфігураційний файл
k exec webapp -n config-demo -- cat /etc/nginx/conf.d/default.conf

# Перевірте, що файли Secret існують (не використовуйте cat у продакшені!)
k exec webapp -n config-demo -- ls -la /etc/secrets/

# Перевірте ендпоінт здоров'я nginx
k exec webapp -n config-demo -- curl -s localhost/health
```

### Завдання 5: Оновлення ConfigMap

```bash
# Оновіть значення ConfigMap
k edit configmap app-config -n config-demo
# Змініть LOG_LEVEL з info на debug

# Перевірте, чи оновилася змінна середовища (ні — потрібен перезапуск)
k exec webapp -n config-demo -- env | grep LOG_LEVEL
# Досі показує: APP_LOG_LEVEL=info

# Перезапустіть Под, щоб підхопити зміни
k delete pod webapp -n config-demo
# Створіть Под заново (виконайте команду apply ще раз)
```

### Критерії успіху

- [ ] Под запущений з усіма конфігураціями
- [ ] Змінні середовища видимі з правильним префіксом
- [ ] nginx.conf змонтований за правильним шляхом
- [ ] Файли Secret мають обмежені права доступу (0400)
- [ ] Ендпоінт здоров'я повертає OK

### Очищення

```bash
k delete ns config-demo
rm /tmp/nginx.conf
```

---

## Тест

### Запитання 1
Яка різниця між `--from-file` та `--from-env-file` при створенні ConfigMap?

<details>
<summary>Відповідь</summary>

**`--from-file`**: створює один ключ, де назва файлу — це ключ, а весь вміст файлу — значення.
```bash
k create configmap test --from-file=config.properties
# Результат: data: { "config.properties": "key1=value1\nkey2=value2" }
```

**`--from-env-file`**: розбирає файл і створює окремий ключ для кожного рядка.
```bash
k create configmap test --from-env-file=config.properties
# Результат: data: { "key1": "value1", "key2": "value2" }
```

Використовуйте `--from-env-file`, коли хочете кожну властивість як окремий ключ; використовуйте `--from-file`, коли хочете змонтувати файл цілком.
</details>

### Запитання 2
ConfigMap змонтований як том. Ви оновлюєте ConfigMap. Що відбувається?

<details>
<summary>Відповідь</summary>

**Змонтовані файли оновлюються автоматично** за допомогою kubelet, зазвичай протягом 60 секунд.

**Винятки:**
- Якщо використовується монтування `subPath`, оновлення НЕ поширюються
- Якщо ConfigMap позначений як `immutable: true`, його не можна оновити
- Застосунки мають перечитати файли, щоб побачити зміни (деякі кешують вміст файлів)

Для змінних середовища з ConfigMap необхідно перезапустити Под, щоб побачити оновлення.
</details>

### Запитання 3
Що не так із цим YAML для Secret?

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
data:
  password: MySecurePassword123
```

<details>
<summary>Відповідь</summary>

**Значення пароля не закодоване в base64.** Поле `data` вимагає значень, закодованих у base64.

Два способи виправити:

1. Закодуйте значення:
```yaml
data:
  password: TXlTZWN1cmVQYXNzd29yZDEyMw==
```

2. Використовуйте `stringData` замість цього (Kubernetes закодує автоматично):
```yaml
stringData:
  password: MySecurePassword123
```
</details>

### Запитання 4
Як декодувати значення Secret із командного рядка?

<details>
<summary>Відповідь</summary>

```bash
# Спосіб 1: Отримати конкретний ключ і декодувати
k get secret db-creds -o jsonpath='{.data.password}' | base64 -d

# Спосіб 2: Використання go-template для всіх ключів
k get secret db-creds -o go-template='{{range $k,$v := .data}}{{$k}}: {{$v | base64decode}}{{"\n"}}{{end}}'

# Спосіб 3: Переглянути весь Secret і декодувати вручну
k get secret db-creds -o yaml
echo 'base64string' | base64 -d
```
</details>

### Запитання 5
Чому краще монтувати Secret як файли, а не як змінні середовища?

<details>
<summary>Відповідь</summary>

**З міркувань безпеки:**

1. **Менша видимість**: `kubectl exec -- env` показує всі змінні середовища, а для файлів потрібно явне зчитування

2. **Без успадкування процесами**: дочірні процеси автоматично успадковують змінні середовища, потенційно розкриваючи Secret підпроцесам

3. **Ризик потрапляння до логів**: змінні середовища часто логуються випадково (логи налагодження, звіти про збої), вміст файлів — рідше

4. **Автооновлення**: Secret, змонтовані як томи, оновлюються автоматично (~1 хв), змінні середовища потребують перезапуску Пода

5. **Контроль прав доступу**: можна встановити обмежені права доступу до файлів (0400) для змонтованих файлів

</details>

### Запитання 6
Ви створили Secret за допомогою `echo 'password' | base64`. Коли ваш застосунок зчитує його, є зайвий символ. Що пішло не так?

<details>
<summary>Відповідь</summary>

**`echo` за замовчуванням додає символ нового рядка.** Закодоване значення містить `\n`.

```bash
# Неправильно — включає символ нового рядка
echo 'password' | base64
# cGFzc3dvcmQK (K наприкінці = закодований символ нового рядка)

# Правильно — використовуйте прапорець -n
echo -n 'password' | base64
# cGFzc3dvcmQ=
```

Коли застосунок декодує це, він отримує `password\n` замість `password`, що може зламати автентифікацію.
</details>

---

## Практичні вправи

Практикуйте ці сценарії в умовах іспитового обмеження часу.

### Вправа 1: Швидке створення ConfigMap
**Цільовий час:** 30 секунд

Створіть ConfigMap із назвою `web-config` з такими значеннями:
- `SERVER_PORT=8080`
- `DEBUG_MODE=false`

<details>
<summary>Відповідь</summary>

```bash
k create configmap web-config \
  --from-literal=SERVER_PORT=8080 \
  --from-literal=DEBUG_MODE=false
```
</details>

### Вправа 2: ConfigMap із файлу
**Цільовий час:** 45 секунд

Створіть файл `/tmp/app.properties` із вмістом:
```
db.host=localhost
db.port=5432
```
Потім створіть ConfigMap `app-props` із цього файлу.

<details>
<summary>Відповідь</summary>

```bash
cat > /tmp/app.properties <<EOF
db.host=localhost
db.port=5432
EOF

k create configmap app-props --from-file=/tmp/app.properties
```
</details>

### Вправа 3: Secret із літералів
**Цільовий час:** 30 секунд

Створіть Secret із назвою `api-key` з:
- `API_KEY=abc123secret`
- `API_SECRET=xyz789token`

<details>
<summary>Відповідь</summary>

```bash
k create secret generic api-key \
  --from-literal=API_KEY=abc123secret \
  --from-literal=API_SECRET=xyz789token
```
</details>

### Вправа 4: Под зі змінними середовища з ConfigMap
**Цільовий час:** 2 хвилини

Створіть Під `envpod` з образом `nginx`, який завантажує всі ключі з ConfigMap `web-config` як змінні середовища.

<details>
<summary>Відповідь</summary>

```bash
k run envpod --image=nginx --dry-run=client -o yaml > /tmp/pod.yaml
```

Відредагуйте, щоб додати `envFrom`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: envpod
spec:
  containers:
  - name: envpod
    image: nginx
    envFrom:
    - configMapRef:
        name: web-config
```

```bash
k apply -f /tmp/pod.yaml
```
</details>

### Вправа 5: Под із томом Secret
**Цільовий час:** 2 хвилини

Створіть Під `secretpod` з образом `nginx`, який монтує Secret `api-key` за шляхом `/etc/api-secrets` із доступом лише на читання.

<details>
<summary>Відповідь</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secretpod
spec:
  containers:
  - name: secretpod
    image: nginx
    volumeMounts:
    - name: secret-vol
      mountPath: /etc/api-secrets
      readOnly: true
  volumes:
  - name: secret-vol
    secret:
      secretName: api-key
```

```bash
k apply -f /tmp/secretpod.yaml
```
</details>

### Вправа 6: Декодування значення Secret
**Цільовий час:** 30 секунд

Витягніть і декодуйте значення `API_KEY` із Secret `api-key`.

<details>
<summary>Відповідь</summary>

```bash
k get secret api-key -o jsonpath='{.data.API_KEY}' | base64 -d
```
</details>

### Вправа 7: TLS Secret
**Цільовий час:** 1 хвилина

У вас є файли `server.crt` та `server.key`. Створіть TLS Secret із назвою `web-tls`.

<details>
<summary>Відповідь</summary>

```bash
# Якщо спочатку потрібно створити тестові файли:
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/CN=test"

# Створіть Secret
k create secret tls web-tls --cert=server.crt --key=server.key
```
</details>

### Вправа 8: Конкретний ключ як файл
**Цільовий час:** 2 хвилини

Створіть Під `configfile`, який монтує лише ключ `db.host` із ConfigMap `app-props` як файл `/etc/dbhost`.

<details>
<summary>Відповідь</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: configfile
spec:
  containers:
  - name: configfile
    image: nginx
    volumeMounts:
    - name: config-vol
      mountPath: /etc/dbhost
      subPath: db.host
  volumes:
  - name: config-vol
    configMap:
      name: app-props
      items:
      - key: db.host
        path: db.host
```

Зверніть увагу: для цього потрібно, щоб ConfigMap мав ключ `db.host`. Якщо ваш ConfigMap було створено з `--from-file`, ключем буде `app.properties` (назва файлу).
</details>

---

## Ключові висновки

1. **ConfigMap** зберігають нечутливу конфігурацію; **Secret** зберігають чутливі дані (але не зашифровані за замовчуванням)

2. **Способи створення**: `--from-literal`, `--from-file`, `--from-env-file`, YAML-маніфест

3. **Способи передачі**: змінні середовища (одна або всі), монтування томів (повне або конкретних ключів)

4. **Оновлення**: монтування томів оновлюються автоматично (~1 хв), змінні середовища потребують перезапуску Пода, монтування subPath не оновлюються

5. **Secret**: використовуйте `stringData` для звичайного тексту в YAML, завжди використовуйте `echo -n`, щоб уникнути проблем із символом нового рядка

6. **Безпека**: обмежте доступ RBAC, надавайте перевагу монтуванню томів над змінними середовища, розгляньте зовнішні сховища секретів для продакшену

---

## Що далі?

Вітаємо! Ви завершили всі модулі Частини 2: Робочі навантаження та планування.

**Наступний крок:** [Підсумковий тест Частини 2](part2-cumulative-quiz/) — перевірте свої знання з усіх тем Частини 2, перш ніж рухатися далі.

**Попереду в Частині 3:** Сервіси та мережа — як Поди взаємодіють між собою та із зовнішнім світом.

---

### Покажчик модулів Частини 2

Швидкі посилання для повторення:

| Модуль | Тема | Ключові навички |
|--------|------|-----------------|
| [2.1](module-2.1-pods/) | Поди — поглиблено | Багатоконтейнерні патерни, життєвий цикл, проби |
| [2.2](module-2.2-deployments/) | Deployment та ReplicaSet | Поступові оновлення, відкати, масштабування |
| [2.3](module-2.3-daemonsets-statefulsets/) | DaemonSet та StatefulSet | Навантаження на рівні вузла, застосунки зі станом |
| [2.4](module-2.4-jobs-cronjobs/) | Job та CronJob | Пакетна обробка, заплановані завдання |
| [2.5](module-2.5-resource-management/) | Управління ресурсами | Запити, ліміти, QoS, квоти |
| [2.6](module-2.6-scheduling/) | Планування | Спорідненість, taint, топологія |
| [2.7](module-2.7-configmaps-secrets/) | ConfigMap та Secret | Передача конфігурації |

**Порада для іспиту:** Частина 2 (Робочі навантаження та планування) — це 15% іспиту CKA. Опануйте `kubectl run`, `kubectl create deployment` та `kubectl create configmap/secret` для швидкого виконання завдань.
