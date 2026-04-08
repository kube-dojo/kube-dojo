---
title: "Модуль 1.6: ConfigMaps та Secrets"
slug: uk/prerequisites/kubernetes-basics/module-1.6-configmaps-secrets
sidebar:
  order: 7
en_commit: "ec136095bc46058a8485bbb10335ebad1586b3ca"
en_file: "src/content/docs/prerequisites/kubernetes-basics/module-1.6-configmaps-secrets.md"
---
> **Складність**: `[СЕРЕДНЯ]` — Важливе керування конфігурацією
>
> **Час на виконання**: 35-40 хвилин
>
> **Попередні вимоги**: Модуль 3 (Pods)

Кожен великий злам хмарної безпеки починається однаково — з облікових даних, яких там не мало бути.

Уявіть, що у вас є веб-застосунок із жорстко закодованими (hardcoded) обліковими даними бази даних у вихідному коді. Якщо цей код буде скомпрометовано, зловмисник отримає ключі від вашої бази даних. У Модулі 1.3 ви дізналися, як запускати застосунки в Pods. Але як передавати конфігурацію та конфіденційні дані цим Pods без перезбирання образу контейнера щоразу, коли змінюється пароль? Давайте виправимо цей жорстко закодований пароль.

---

## Що ви зможете зробити

Після цього модуля ви зможете:
- **Створити** ConfigMaps та Secrets і впровадити їх у Pods як змінні оточення або змонтовані файли
- **Пояснити**, чому конфігурація має бути відокремлена від коду (принцип застосунку 12 факторів)
- **Обрати** між ConfigMaps та Secrets залежно від конфіденційності даних
- **Оновити** конфігурацію динамічно без перезбирання образів контейнерів
- **Визначити** три прогалини в безпеці при стандартній обробці Secrets та описати способи їх усунення

---

## Чому це важливо

Застосункам потрібна конфігурація: URL-адреси баз даних, прапорці функцій (feature flags), API-ключі, облікові дані. Жорстке кодування цих даних в образах контейнерів — це погана практика. ConfigMaps та Secrets дозволяють керувати конфігурацією окремо від коду вашого застосунку.

Сприймайте ConfigMaps як публічне меню ресторану: воно час від часу змінюється, будь-хто може його прочитати, і воно повідомляє персоналу, що готувати. Secrets — це замкнений сейф із рецептом секретного соусу: ви даєте доступ лише тим кухарям, яким він дійсно потрібен.

---

## ConfigMaps vs Secrets

```text
┌─────────────────────────────────────────────────────────────┐
│              CONFIGMAPS vs SECRETS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap                     │  Secret                    │
│  ─────────────────────────────│────────────────────────────│
│  Неконфіденційні дані          │  Конфіденційні дані        │
│  Зберігання у відкритому виді  │  Кодування Base64          │
│  Оточення, файли конфігурації  │  Паролі, токени, ключі     │
│                                │                            │
│  Приклади:                     │  Приклади:                 │
│  • Рівні логування             │  • Паролі бази даних       │
│  • Прапорці функцій            │  • API-ключі               │
│  • Вміст файлів конфігурації   │  • TLS-сертифікати         │
│                                                             │
│  Примітка: Secrets НЕ зашифровані за замовчуванням!         │
│  Base64 — це кодування, а не шифрування.                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Зупиніться та подумайте**: Вашому застосунку потрібен прапорець функції (`ENABLE_BETA=true`) та пароль до бази даних. Який об'єкт має зберігати кожен із них і чому?

---

## ConfigMaps

ConfigMaps зберігають неконфіденційні дані у вигляді пар ключ-значення.

### Створення ConfigMaps

```bash
# З літеральних значень
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=ENVIRONMENT=staging

# З файлу
kubectl create configmap nginx-config --from-file=nginx.conf

# З директорії (кожен файл стає ключем)
kubectl create configmap configs --from-file=./config-dir/

# Перегляд ConfigMap
kubectl get configmap app-config -o yaml
```

### YAML для ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "debug"
  ENVIRONMENT: "staging"
  config.json: |
    {
      "database": "localhost",
      "port": 5432
    }
```

### Використання ConfigMaps

**Як змінні оточення:**

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
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: LOG_LEVEL
    # Або всі ключі одночасно:
    envFrom:
    - configMapRef:
        name: app-config
```

> **Зупиніться та поміркуйте**: В яких випадках ви б монтували конфігурацію як файл, а не використовували змінні оточення?

**Як volume (файли):**

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
    - name: config
      mountPath: /etc/nginx/conf.d
  volumes:
  - name: config
    configMap:
      name: nginx-config
```

---

## Secrets

Тепер, коли ви вмієте створювати ConfigMaps, давайте поговоримо про їхнього потайливого родича. Secrets діють за тим самим принципом, що й ConfigMaps, але з двома ключовими відмінностями: ви посилаєтеся на них за допомогою `secretKeyRef` замість `configMapKeyRef`, а їхні значення мають бути закодовані в base64.

### Створення Secrets

```bash
# З літеральних значень
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=secret123

# З файлу
kubectl create secret generic tls-cert \
  --from-file=cert.pem \
  --from-file=key.pem

# Перегляд secret (закодований у base64)
kubectl get secret db-creds -o yaml

# Декодування значення
kubectl get secret db-creds -o jsonpath='{.data.password}' | base64 -d
```

### YAML для Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque              # Загальний тип secret
data:                     # Закодовано в Base64
  username: YWRtaW4=      # echo -n 'admin' | base64
  password: c2VjcmV0MTIz  # echo -n 'secret123' | base64
---
# Або використовуйте stringData для відкритого тексту (K8s закодує його)
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
stringData:               # Відкритий текст, автоматичне кодування
  username: admin
  password: secret123
```

### Використання Secrets

**Як змінні оточення:**

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
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: username
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
```

**Як volume (файли):**

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
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
```

---

## Візуалізація

```text
┌─────────────────────────────────────────────────────────────┐
│              ВИКОРИСТАННЯ CONFIGMAP/SECRET                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap/Secret                                          │
│  ┌─────────────────────┐                                   │
│  │ data:               │                                   │
│  │   KEY1: value1      │                                   │
│  │   KEY2: value2      │                                   │
│  └──────────┬──────────┘                                   │
│             │                                               │
│    ┌────────┴────────┐                                     │
│    ▼                 ▼                                      │
│                                                             │
│  Як змінні           Як Volume                              │
│  оточення            (Файли)                                │
│  ┌────────────┐     ┌────────────────────┐                │
│  │ env:       │     │ /etc/config/       │                │
│  │   KEY1=val1│     │   KEY1  (файл)     │                │
│  │   KEY2=val2│     │   KEY2  (файл)     │                │
│  └────────────┘     └────────────────────┘                │
│                                                             │
│  Використовуйте     Використовуйте                         │
│  envFrom для        volumes для                            │
│  простих ключ-знач  файлів конфігурації                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Практичний приклад: Рефакторинг жорстко закодованої конфігурації

Давайте розберемо, як провести рефакторинг застосунку, який має жорстко закодовані налаштування.

**1. Визначте точки конфігурації**: Застосунок підключається до бази даних за адресою `localhost:5432` з паролем `supersecret` і використовує TTL кешування `3600`.

**2. Розділіть за рівнем конфіденційності**: TTL кешу не є конфіденційним, тому він має бути в ConfigMap. Пароль бази даних є дуже конфіденційним, тому він має потрапити в Secret.

**3. Створіть об'єкти**:

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
data:
  CACHE_TTL: "3600"
---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
stringData:
  DB_PASSWORD: "supersecret"
```

**4. Змонтуйте їх у Pod**:

```yaml
# Pod, що використовує обидва об'єкти
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
  - name: app
    image: myapp:v1
    envFrom:
    - configMapRef:
        name: app-settings
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: DB_PASSWORD
```

---

## Реальність продакшну: Безпечна робота із Secrets

У 2019 році кілька стартапів постраждали від серйозних зламів, оскільки розробники зафіксували (committed) свої `.env` файли з відкритими паролями баз даних у публічних репозиторіях Git. Зберігання звичайних YAML-файлів Secrets у Git створює таку саму вразливість.

У продакшн-середовищі ви повинні усунути три основні прогалини в безпеці стандартних Secrets у Kubernetes:

1. **Secrets лише закодовані в Base64, а не зашифровані**. Будь-хто, хто може переглянути Secret, може легко його декодувати.
   *Усунення*: Увімкніть шифрування під час зберігання (Encryption at Rest) на сервері API Kubernetes, щоб secrets шифрувалися перед записом у базу даних `etcd`.
2. **Ви не можете фіксувати (commit) відкриті Secrets у Git**.
   *Усунення*: Використовуйте такі інструменти, як **Sealed Secrets** (які шифрують secret так, що його безпечно зберігати в Git, а кластер дешифрує його) або **External Secrets Operator** (який динамічно отримує secrets від хмарних провайдерів, таких як AWS Secrets Manager або HashiCorp Vault).
3. **Змінні оточення можуть витекти**. Якщо застосунок падає, інструменти звітування про збої часто вивантажують усі змінні оточення в логи.
   *Усунення*: Монтуйте secrets як файли за допомогою volumes. Набагато важче випадково розкрити змонтований файл, ніж змінну оточення, а файли динамічно оновлюються при зміні Secret без необхідності перезапуску Pod.

---

## Чи знали ви?

- **Оновлення ConfigMap/Secret не перезапускає Pods автоматично.** Змонтовані volumes оновлюються (це може тривати до хвилини), але змінні оточення потребують перезапуску Pod, щоб отримати нові значення.
- **Максимальний розмір — 1 МБ.** І ConfigMaps, і Secrets обмежені 1 МБ даних, щоб запобігти роздуванню бази даних `etcd`.
- **Secrets зберігаються в etcd.** Будь-хто з доступом до etcd може їх прочитати. Використовуйте керування доступом на основі ролей (RBAC), щоб суворо обмежити доступ до Secrets.

> **Зупиніться та поміркуйте**: Колега каже, що Secrets безпечні, тому що вони закодовані в base64. Що б ви відповіли?

---

## Типові помилки

| Помилка | Наслідок | Рішення |
|---------|----------|---------|
| Фіксація (commit) secrets у Git | 100% компрометація облікових даних, що вимагає негайної ротації | Використовуйте sealed-secrets або зовнішнє керування секретами |
| Думка, що base64 = зашифровано | Хибне відчуття безпеки; будь-хто з доступом на читання може їх декодувати | Увімкніть шифрування під час зберігання в etcd |
| Невикористання stringData | Висока ймовірність помилок ручного кодування base64 або зайвих пробілів | Використовуйте `stringData` для відкритого тексту |
| Жорстке кодування в образах | Багатохвилинні затримки розгортання лише для зміни одного значення конфігурації | Використовуйте ConfigMaps/Secrets |

---

## Контрольні запитання

1. **Розробник оновлює ConfigMap, який впроваджено в запущений Pod як змінну оточення, але застосунок не бачить нового значення. Чому?**
   <details>
   <summary>Відповідь</summary>
   Змінні оточення зчитуються лише під час запуску контейнера. Оновлення ConfigMap не перезапускає Pod автоматично. Щоб отримати нову змінну оточення, Pod потрібно видалити та створити заново (або перезапустити через Deployment rollout). Якби ConfigMap був змонтований як volume, вміст файлу оновився б динамічно.
   </details>

2. **Ви переглядаєте YAML-файл колеги для Kubernetes і помічаєте, що він зберіг API-ключ продакшну в ConfigMap. Чому це проблема і як це виправити?**
   <details>
   <summary>Відповідь</summary>
   ConfigMaps призначені для неконфіденційних даних. Будь-хто з базовим доступом до простору імен може мати дозвіл на читання ConfigMaps, що розкриє API-ключ. Його слід перенести в Secret, а доступ до Secrets має бути суворо обмежений за допомогою RBAC. Крім того, у кластері має бути налаштовано шифрування під час зберігання (encryption at rest) для Secrets.
   </details>

3. **Ваша команда безпеки проводить сканування вразливостей і виявляє, що у разі збою застосунку пароль бази даних виводиться в логи збоїв. Як можна змінити спосіб передачі Secret, щоб це виправити?**
   <details>
   <summary>Відповідь</summary>
   Застосунок, ймовірно, отримує Secret як змінну оточення, які інструменти дампу збоїв часто логують за замовчуванням. Рішення полягає в тому, щоб натомість змонтувати Secret як volume (файл). Застосунок зможе прочитати файл під час запуску, а засоби звітування про збої не будуть автоматично логувати вміст змонтованих файлів.
   </details>

4. **Цей YAML має серйозну проблему. Яку саме?**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: db-creds
   data:
     password: mysecretpassword
   ```
   <details>
   <summary>Відповідь</summary>
   YAML використовує поле `data`, але містить відкритий текст (`mysecretpassword`). Поле `data` очікує значення, закодовані в base64. Створення Secret або завершиться помилкою, або застосунок отримає сміття при декодуванні. Розробнику слід або вручну закодувати пароль у base64, або змінити ключ із `data` на `stringData`.
   </details>

---

## Практична вправа

**Завдання**: Створити та використати ConfigMaps та Secrets.

```bash
# 1. Створення ConfigMap
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=debug \
  --from-literal=APP_NAME=myapp

# 2. ТОЧКА ПРИЙНЯТТЯ РІШЕННЯ: Створіть secret.
# Чи використаєте ви --from-literal або створите YAML-файл із stringData? 
# Для швидкості тут використаємо CLI:
kubectl create secret generic app-secret \
  --from-literal=DB_PASS=secretpassword

# 3. Створення Pod, що використовує обидва об'єкти
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: config-test
spec:
  containers:
  - name: test
    image: busybox
    command: ['sh', '-c', 'env && sleep 3600']
    envFrom:
    - configMapRef:
        name: app-config
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: DB_PASS
EOF

# 4. Перевірка наявності змінних оточення
kubectl logs config-test | grep -E "LOG_LEVEL|APP_NAME|DB_PASSWORD"
```

**Критерії успіху**: Логи Pod показують усі три змінні оточення, заповнені правильними значеннями.

### Додаткове міні-завдання

Замість впровадження ConfigMap як змінної оточення через `envFrom`, змініть YAML-файл Pod `config-test`, щоб змонтувати `app-config` як volume у `/etc/app-config`. 

Коли Pod запуститься, перевірте наявність файлів, виконавши:
`kubectl exec config-test -- ls -l /etc/app-config`

Потім очистьте ваші ресурси:
```bash
kubectl delete pod config-test
kubectl delete configmap app-config
kubectl delete secret app-secret
```

---

## Підсумок

ConfigMaps та Secrets виносять конфігурацію назовні, дозволяючи відокремити код від змінних, специфічних для середовища.

**ConfigMaps**:
- Неконфіденційні дані
- Зберігання у відкритому вигляді
- Використовуйте для значень конфігурації, прапорців функцій та неконфіденційних файлів

**Secrets**:
- Конфіденційні дані
- Кодування Base64 (НЕ зашифровані за замовчуванням)
- Використовуйте для паролів, API-ключів, токенів та сертифікатів

**Шаблони використання**:
- Змінні оточення (`env`, `envFrom`) — прості у використанні, але статичні та схильні до витоку в логах збоїв
- Монтування volumes (файли) — динамічно оновлюються і загалом безпечніші

---

## Наступний модуль

[Модуль 1.7: Namespaces та Labels](../module-1.7-namespaces-labels/) — Організація вашого кластера.