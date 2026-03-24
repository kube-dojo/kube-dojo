# Модуль 3.3: DNS та CoreDNS

> **Складність**: `[MEDIUM]` — критичний компонент інфраструктури
>
> **Час на виконання**: 40–50 хвилин
>
> **Передумови**: Модуль 3.1 (Сервіси), Модуль 3.2 (Endpoints)

---

## Чому цей модуль важливий

DNS — це спосіб, яким Поди знаходять Сервіси. Щоразу, коли Под робить запит до `my-service`, DNS перетворює це ім'я на IP-адресу. Якщо DNS зламається — вся система виявлення Сервісів у кластері перестане працювати. Розуміння CoreDNS є ключовим для діагностики проблем зі з'єднанням.

Іспит CKA перевіряє вміння діагностувати DNS, налаштовувати CoreDNS і розуміти, як Kubernetes розв'язує імена. Вам потрібно буде усувати проблеми DNS та розуміти ієрархію розв'язання імен.

> **Аналогія з телефонною книгою**
>
> DNS — це телефонна книга вашого кластера. Замість того, щоб запам'ятовувати, що «web-service» живе за IP 10.96.45.123, ви просто набираєте «web-service», а DNS шукає номер за вас. CoreDNS — це телефоніст, який веде цю книгу й відповідає на запити.

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Розуміти, як працює DNS у Kubernetes
- Діагностувати проблеми з розв'язанням DNS
- Налаштовувати CoreDNS
- Використовувати різні формати DNS-імен
- Відлагоджувати Поди з проблемами DNS

---

## Чи знали ви?

- **CoreDNS замінив kube-dns**: до Kubernetes 1.11, за DNS відповідав kube-dns. CoreDNS швидший, гнучкіший і використовує плагіни для розширення функціональності.

- **DNS — ціль №1 для діагностики**: більшість «мережевих проблем» — це насправді проблеми DNS. Якщо сумніваєтесь — перевіряйте DNS першим!

- **Поди отримують DNS-конфігурацію автоматично**: kubelet додає `/etc/resolv.conf` у кожний Под, вказуючи на DNS-сервіс кластера.

---

## Частина 1: Архітектура DNS

### 1.1 Як працює DNS у Kubernetes

```
┌────────────────────────────────────────────────────────────────┐
│                   Архітектура DNS у Kubernetes                  │
│                                                                 │
│   ┌────────────────┐                                           │
│   │      Под       │                                           │
│   │                │                                           │
│   │ curl web-svc   │                                           │
│   │      │         │                                           │
│   │      ▼         │                                           │
│   │ /etc/resolv.conf                                           │
│   │ nameserver 10.96.0.10  ──────────────────────┐            │
│   │ search default.svc...                         │            │
│   └────────────────┘                              │            │
│                                                   │            │
│                                                   ▼            │
│   ┌──────────────────────────────────────────────────────────┐│
│   │              Сервіс CoreDNS (10.96.0.10)                 ││
│   │                                                           ││
│   │  ┌─────────┐ ┌─────────┐                                 ││
│   │  │CoreDNS  │ │CoreDNS  │  (2 репліки за замовчуванням)    ││
│   │  │  Под    │ │  Под    │                                 ││
│   │  └────┬────┘ └────┬────┘                                 ││
│   │       │           │                                       ││
│   │       └─────┬─────┘                                       ││
│   │             ▼                                             ││
│   │    Запит: web-svc.default.svc.cluster.local               ││
│   │             │                                             ││
│   │             ▼                                             ││
│   │    Відповідь: 10.96.45.123 (ClusterIP Сервісу)           ││
│   └──────────────────────────────────────────────────────────┘│
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Компоненти CoreDNS

| Компонент | Розташування | Призначення |
|-----------|-------------|-------------|
| Deployment CoreDNS | Простір імен `kube-system` | Запускає Поди CoreDNS |
| Сервіс CoreDNS | Простір імен `kube-system` | Стабільна IP-адреса для DNS-запитів (зазвичай 10.96.0.10) |
| ConfigMap Corefile | Простір імен `kube-system` | Конфігурація CoreDNS |
| /etc/resolv.conf Пода | Кожний Под | Вказує на Сервіс CoreDNS |

### 1.3 DNS-конфігурація Пода

Кожний Под отримує це автоматично:

```bash
# Всередині будь-якого Пода
cat /etc/resolv.conf

# Вивід:
nameserver 10.96.0.10           # IP Сервісу CoreDNS
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

| Поле | Призначення |
|------|-------------|
| `nameserver` | IP-адреса Сервісу CoreDNS |
| `search` | Домени, що додаються при розв'язанні коротких імен |
| `ndots:5` | Якщо ім'я має менше 5 крапок — спочатку спробувати search-домени |

---

## Частина 2: Формати DNS-імен

### 2.1 DNS-імена Сервісів

```
┌────────────────────────────────────────────────────────────────┐
│                   Іменування DNS для Сервісів                  │
│                                                                 │
│   Повний формат (FQDN):                                       │
│   <сервіс>.<простір-імен>.svc.<домен-кластера>                │
│                                                                 │
│   Приклад: web-svc.production.svc.cluster.local                │
│            ───────  ──────────  ───  ─────────────             │
│               │        │         │        │                    │
│           сервіс   простір    фіксований  домен               │
│                    імен       суфікс   кластера               │
│                                        (типовий)              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Скорочені імена (search-домени)

```bash
# З Пода в Просторі імен "default", звернення до "web-svc" в "default":
curl web-svc                    # ✓ Працює (той самий Простір імен)
curl web-svc.default            # ✓ Працює
curl web-svc.default.svc        # ✓ Працює
curl web-svc.default.svc.cluster.local  # ✓ Працює (FQDN)

# З Пода в Просторі імен "default", звернення до "api" в "production":
curl api                        # ✗ Не працює (інший Простір імен)
curl api.production             # ✓ Працює (між Просторами імен)
curl api.production.svc.cluster.local   # ✓ Працює (FQDN)
```

### 2.3 Як працюють search-домени

```
┌────────────────────────────────────────────────────────────────┐
│                   Розв'язання через search-домени              │
│                                                                 │
│   Під у Просторі імен "default" розв'язує "web-svc":          │
│                                                                 │
│   search default.svc.cluster.local svc.cluster.local ...      │
│                                                                 │
│   Крок 1: Спроба web-svc.default.svc.cluster.local            │
│           └── Знайдено! Повертає IP                            │
│                                                                 │
│   Якщо не знайдено:                                            │
│   Крок 2: Спроба web-svc.svc.cluster.local                    │
│   Крок 3: Спроба web-svc.cluster.local                        │
│   Крок 4: Спроба web-svc (зовнішній DNS)                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.4 DNS-імена Подів

Поди також отримують DNS-імена:

```
┌────────────────────────────────────────────────────────────────┐
│                   DNS-імена Подів                               │
│                                                                 │
│   IP Пода: 10.244.1.5                                          │
│   DNS: 10-244-1-5.default.pod.cluster.local                    │
│        ──────────  ───────  ───  ─────────────                 │
│          IP з      простір  pod  домен кластера                │
│          дефісами  імен                                         │
│                                                                 │
│   Для Подів StatefulSet із headless-сервісом:                  │
│   DNS: web-0.web-svc.default.svc.cluster.local                 │
│        ─────  ───────  ───────  ───                            │
│        ім'я   headless  простір                                │
│        Пода   сервіс    імен                                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Частина 3: Конфігурація CoreDNS

### 3.1 Перегляд компонентів CoreDNS

```bash
# Перевірити Поди CoreDNS
k get pods -n kube-system -l k8s-app=kube-dns

# Перевірити Deployment CoreDNS
k get deployment coredns -n kube-system

# Перевірити Сервіс CoreDNS
k get svc kube-dns -n kube-system
# Примітка: Сервіс називається "kube-dns" для зворотної сумісності

# Переглянути конфігурацію CoreDNS
k get configmap coredns -n kube-system -o yaml
```

### 3.2 Розуміння Corefile

```yaml
# ConfigMap CoreDNS
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors                          # Логувати помилки
        health {                         # Ендпоінт перевірки стану
            lameduck 5s
        }
        ready                           # Ендпоінт готовності
        kubernetes cluster.local in-addr.arpa ip6.arpa {  # Плагін K8s
            pods insecure               # DNS-розв'язання Подів
            fallthrough in-addr.arpa ip6.arpa
            ttl 30                      # TTL кешу
        }
        prometheus :9153                # Метрики
        forward . /etc/resolv.conf {    # Переспрямування зовнішнього DNS
            max_concurrent 1000
        }
        cache 30                        # Кешування відповідей
        loop                            # Виявлення циклів
        reload                          # Автоматичне перезавантаження конфігурації
        loadbalance                     # Round-robin DNS
    }
```

### 3.3 Основні плагіни Corefile

| Плагін | Призначення |
|--------|-------------|
| `kubernetes` | Розв'язує імена Сервісів та Подів Kubernetes |
| `forward` | Переспрямовує зовнішні запити на upstream DNS |
| `cache` | Кешує відповіді для зменшення навантаження |
| `errors` | Логує помилки DNS |
| `health` | Надає ендпоінт перевірки стану |
| `prometheus` | Відкриває метрики |
| `loop` | Виявляє та розриває DNS-цикли |

### 3.4 Налаштування CoreDNS

```yaml
# Додати власні DNS-записи
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        # ... наявна конфігурація ...

        # Додати власні хости
        hosts {
            10.0.0.1 custom.example.com
            fallthrough
        }

        # Переспрямувати конкретний домен на власний DNS
        forward example.com 10.0.0.53
    }
```

```bash
# Після редагування перезапустіть CoreDNS
k rollout restart deployment coredns -n kube-system
```

---

## Частина 4: Діагностика DNS

### 4.1 Алгоритм діагностики DNS

```
Проблема з DNS?
    │
    ├── Крок 1: Тест зсередини Пода
    │   k run test --rm -it --image=busybox:1.36 -- nslookup <сервіс>
    │       │
    │       ├── Працює? → DNS в порядку, проблема в іншому
    │       │
    │       └── Не працює? → Продовжуємо діагностику
    │
    ├── Крок 2: Перевірити, чи працює CoreDNS
    │   k get pods -n kube-system -l k8s-app=kube-dns
    │       │
    │       └── Не запущено? → Виправити Deployment CoreDNS
    │
    ├── Крок 3: Перевірити логи CoreDNS
    │   k logs -n kube-system -l k8s-app=kube-dns
    │       │
    │       └── Помилки? → Перевірити конфігурацію Corefile
    │
    ├── Крок 4: Перевірити resolv.conf Пода
    │   k exec <pod> -- cat /etc/resolv.conf
    │       │
    │       └── Неправильний nameserver? → Перевірити конфігурацію kubelet
    │
    └── Крок 5: Тест зовнішнього DNS
        k run test --rm -it --image=busybox:1.36 -- nslookup google.com
            │
            └── Не працює? → Перевірити директиву forward у Corefile
```

### 4.2 Типові DNS-команди

```bash
# Тестування DNS зсередини кластера
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup kubernetes

# Тест конкретного Сервісу
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web-svc.default.svc.cluster.local

# Тест із вказанням DNS-сервера
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web-svc 10.96.0.10

# Перевірити resolv.conf
k exec <pod> -- cat /etc/resolv.conf

# Перевірити логи CoreDNS
k logs -n kube-system -l k8s-app=kube-dns --tail=50

# Переконатися, що CoreDNS відповідає
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup kubernetes.default.svc.cluster.local
```

### 4.3 Под для діагностики DNS

Використовуйте Под із розширеним набором інструментів:

```bash
# Створити Под для діагностики
k run dns-debug --image=nicolaka/netshoot --restart=Never -- sleep 3600

# Використовувати для діагностики
k exec -it dns-debug -- dig web-svc.default.svc.cluster.local
k exec -it dns-debug -- host web-svc
k exec -it dns-debug -- nslookup web-svc

# Очищення
k delete pod dns-debug
```

### 4.4 Типові проблеми DNS

| Симптом | Причина | Рішення |
|---------|---------|---------|
| `NXDOMAIN` | Сервіс не існує | Перевірте ім'я Сервісу та Простір імен |
| `Server failure` | CoreDNS не працює | Перевірте Поди CoreDNS |
| Тайм-аут | Мережева проблема до CoreDNS | Перевірте мережу Подів, CNI |
| Повертається неправильна IP | Застарілий кеш | Перезапустіть CoreDNS, перевірте TTL кешу |
| Зовнішні домени не працюють | Неправильна конфігурація forward | Перевірте директиву forward у Corefile |

---

## Частина 5: DNS-політики

### 5.1 DNS-політики Подів

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-policy-demo
spec:
  dnsPolicy: ClusterFirst    # За замовчуванням
  containers:
  - name: app
    image: nginx
```

| Політика | Поведінка |
|----------|-----------|
| `ClusterFirst` (за замовчуванням) | Використовувати DNS кластера, якщо не знайдено — DNS вузла |
| `Default` | Використовувати DNS-налаштування вузла (успадковані від хоста) |
| `ClusterFirstWithHostNet` | Використовувати DNS кластера навіть із `hostNetwork: true` |
| `None` | Без DNS-конфігурації, потрібно вказати dnsConfig |

### 5.2 Власна DNS-конфігурація

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns
spec:
  dnsPolicy: "None"          # Обов'язково для власної конфігурації
  dnsConfig:
    nameservers:
    - 1.1.1.1                # Власний DNS-сервер
    - 8.8.8.8
    searches:
    - custom.local           # Власний search-домен
    - svc.cluster.local
    options:
    - name: ndots
      value: "2"             # Власне значення ndots
  containers:
  - name: app
    image: nginx
```

### 5.3 Використання hostNetwork із DNS

```yaml
# Под з мережею хоста, але все одно з DNS кластера
apiVersion: v1
kind: Pod
metadata:
  name: host-network-pod
spec:
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet   # Важливо!
  containers:
  - name: app
    image: nginx
```

---

## Частина 6: SRV-записи

### 6.1 Що таке SRV-записи?

SRV-записи містять інформацію про порт разом з IP:

```bash
# Запит SRV-запису для Сервісу
dig SRV web-svc.default.svc.cluster.local

# Повертає:
# _http._tcp.web-svc.default.svc.cluster.local. 30 IN SRV 0 100 80 web-svc.default.svc.cluster.local.
```

### 6.2 Іменовані порти та SRV-записи

```yaml
# Сервіс з іменованим портом
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  selector:
    app: web
  ports:
  - name: http          # Іменований порт
    port: 80
    targetPort: 8080
```

```bash
# Формат SRV-запису: _<ім'я-порту>._<протокол>.<сервіс>.<простір-імен>.svc.cluster.local
# Запит:
dig SRV _http._tcp.web-svc.default.svc.cluster.local
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Використання неправильного Простору імен | Помилка `NXDOMAIN` | Використовуйте FQDN або перевірте Простір імен |
| Пропущено `.svc` | Розв'язання не працює | Використовуйте `сервіс.простір-імен` або FQDN |
| CoreDNS не працює | Весь DNS не працює | Перевірте Поди в `kube-system` |
| Неправильна dnsPolicy | Під не може розв'язувати імена | Використовуйте `ClusterFirst` для Сервісів кластера |
| Редагування неправильного ConfigMap | Конфігурація не застосована | Редагуйте ConfigMap `coredns` у `kube-system` |

---

## Тест

1. **Який DNS-сервер Поди використовують за замовчуванням?**
   <details>
   <summary>Відповідь</summary>
   Сервіс CoreDNS у Просторі імен kube-system, зазвичай з IP 10.96.0.10. Це налаштовується через `/etc/resolv.conf`, який додає kubelet.
   </details>

2. **Як Під у Просторі імен "app" може звернутися до Сервісу "db" у Просторі імен "data"?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте `db.data` або FQDN `db.data.svc.cluster.local`. Коротке ім'я `db` саме по собі не працюватиме з іншого Простору імен.
   </details>

3. **Де зберігається конфігурація CoreDNS?**
   <details>
   <summary>Відповідь</summary>
   У ConfigMap з іменем `coredns` у Просторі імен `kube-system`. Конфігурація знаходиться в ключі `Corefile`.
   </details>

4. **Що означає `ndots:5` у `/etc/resolv.conf`?**
   <details>
   <summary>Відповідь</summary>
   Якщо запит має менше 5 крапок — спочатку спробувати додати search-домени, перш ніж запитувати ім'я як абсолютне. Це оптимізує розв'язання для імен Kubernetes на кшталт `web-svc.default.svc.cluster.local` (4 крапки).
   </details>

5. **Під не може розв'язати `google.com`. Що ймовірно не так?**
   <details>
   <summary>Відповідь</summary>
   Директива `forward` у Corefile CoreDNS може бути налаштована неправильно, або немає мережевого шляху від кластера до зовнішніх DNS-серверів. Перевірте Corefile та мережеве з'єднання Подів.
   </details>

---

## Практична вправа

**Завдання**: Діагностика та розуміння DNS у Kubernetes.

**Кроки**:

1. **Перевірте, чи працює CoreDNS**:
```bash
k get pods -n kube-system -l k8s-app=kube-dns
k get svc -n kube-system kube-dns
```

2. **Перегляньте конфігурацію CoreDNS**:
```bash
k get configmap coredns -n kube-system -o yaml
```

3. **Створіть тестовий Сервіс**:
```bash
k create deployment web --image=nginx
k expose deployment web --port=80
```

4. **Перевірте розв'язання DNS**:
```bash
# Коротке ім'я
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web

# З Простором імен
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default

# FQDN
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default.svc.cluster.local
```

5. **Перевірте resolv.conf Пода**:
```bash
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  cat /etc/resolv.conf
```

6. **Перевірте DNS між Просторами імен**:
```bash
# Створіть Сервіс в іншому Просторі імен
k create namespace other
k create deployment db -n other --image=nginx
k expose deployment db -n other --port=80

# Розв'язання з Простору імен default
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup db.other
```

7. **Перевірте зовнішній DNS**:
```bash
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup google.com
```

8. **Перевірте логи CoreDNS**:
```bash
k logs -n kube-system -l k8s-app=kube-dns --tail=20
```

9. **Очищення**:
```bash
k delete deployment web
k delete svc web
k delete namespace other
```

**Критерії успіху**:
- [ ] Можете перевірити, що CoreDNS працює
- [ ] Розумієте формати DNS-імен
- [ ] Можете розв'язувати Сервіси за коротким іменем та FQDN
- [ ] Можете розв'язувати Сервіси між Просторами імен
- [ ] Можете діагностувати проблеми DNS

---

## Практичні вправи

### Вправа 1: Основи DNS (Ціль: 3 хвилини)

```bash
# Створити Сервіс
k create deployment dns-test --image=nginx
k expose deployment dns-test --port=80

# Перевірити всі формати імен
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  sh -c 'nslookup dns-test && nslookup dns-test.default && nslookup dns-test.default.svc.cluster.local'

# Очищення
k delete deployment dns-test
k delete svc dns-test
```

### Вправа 2: Перевірка стану CoreDNS (Ціль: 2 хвилини)

```bash
# Перевірити Поди
k get pods -n kube-system -l k8s-app=kube-dns -o wide

# Перевірити Сервіс
k get svc kube-dns -n kube-system

# Перевірити Deployment
k get deployment coredns -n kube-system

# Переглянути логи
k logs -n kube-system -l k8s-app=kube-dns --tail=10
```

### Вправа 3: Розв'язання між Просторами імен (Ціль: 3 хвилини)

```bash
# Створити Сервіси у двох Просторах імен
k create namespace ns1
k create namespace ns2
k create deployment app1 -n ns1 --image=nginx
k create deployment app2 -n ns2 --image=nginx
k expose deployment app1 -n ns1 --port=80
k expose deployment app2 -n ns2 --port=80

# З ns1 звернутися до ns2 (і навпаки)
k run test -n ns1 --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup app2.ns2

k run test -n ns2 --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup app1.ns1

# Очищення
k delete namespace ns1 ns2
```

### Вправа 4: Перевірка DNS-конфігурації Пода (Ціль: 2 хвилини)

```bash
# Створити Под
k run dns-check --image=busybox:1.36 --command -- sleep 3600

# Перевірити його DNS-конфігурацію
k exec dns-check -- cat /etc/resolv.conf

# Переконатися, що nameserver збігається з Сервісом kube-dns
k get svc kube-dns -n kube-system -o jsonpath='{.spec.clusterIP}'

# Очищення
k delete pod dns-check
```

### Вправа 5: ConfigMap CoreDNS (Ціль: 3 хвилини)

```bash
# Переглянути Corefile
k get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}'

# Описати ConfigMap
k describe configmap coredns -n kube-system

# Перевірити, які плагіни увімкнено
k get configmap coredns -n kube-system -o yaml | grep -E "kubernetes|forward|cache"
```

### Вправа 6: DNS headless-сервісу (Ціль: 4 хвилини)

```bash
# Створити Deployment
k create deployment headless-test --image=nginx --replicas=3

# Створити headless-сервіс
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless-svc
spec:
  clusterIP: None
  selector:
    app: headless-test
  ports:
  - port: 80
EOF

# Звичайний Сервіс повертає одну IP
# Headless повертає всі IP Подів
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-svc
# Повинен повернути кілька IP-адрес

# Очищення
k delete deployment headless-test
k delete svc headless-svc
```

### Вправа 7: Власна DNS-політика (Ціль: 4 хвилини)

```bash
# Створити Під з власним DNS
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  dnsPolicy: None
  dnsConfig:
    nameservers:
    - 8.8.8.8
    searches:
    - custom.local
    options:
    - name: ndots
      value: "2"
  containers:
  - name: app
    image: busybox:1.36
    command: ["sleep", "3600"]
EOF

# Перевірити власний resolv.conf
k exec custom-dns-pod -- cat /etc/resolv.conf
# Повинен показати 8.8.8.8 та custom.local

# Зверніть увагу: не буде розв'язувати Сервіси кластера!
k exec custom-dns-pod -- nslookup kubernetes
# Не спрацює

# Очищення
k delete pod custom-dns-pod
```

### Вправа 8: Діагностика проблеми DNS (Ціль: 4 хвилини)

```bash
# Створити Сервіс
k create deployment web --image=nginx
k expose deployment web --port=80

# Імітація алгоритму діагностики
# Крок 1: Тест із Пода
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web
# Повинен працювати

# Крок 2: Тест FQDN
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default.svc.cluster.local
# Повинен працювати

# Крок 3: Перевірити CoreDNS
k get pods -n kube-system -l k8s-app=kube-dns

# Крок 4: Перевірити логи
k logs -n kube-system -l k8s-app=kube-dns --tail=5

# Очищення
k delete deployment web
k delete svc web
```

### Вправа 9: Виклик — повний робочий процес DNS

Без підглядання у рішення:

1. Переконайтесь, що CoreDNS працює
2. Створіть Deployment `challenge` з nginx
3. Опублікуйте його як Сервіс
4. Перевірте розв'язання DNS коротким іменем, з Простором імен та FQDN
5. Створіть такий самий Сервіс у новому Просторі імен `test`
6. Розв'яжіть між Просторами імен
7. Перегляньте логи CoreDNS
8. Очистіть все

```bash
# ВАШЕ ЗАВДАННЯ: Виконайте за 5 хвилин
```

<details>
<summary>Відповідь</summary>

```bash
# 1. Перевірити CoreDNS
k get pods -n kube-system -l k8s-app=kube-dns

# 2. Створити Deployment
k create deployment challenge --image=nginx

# 3. Опублікувати
k expose deployment challenge --port=80

# 4. Перевірити формати DNS
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  sh -c 'nslookup challenge; nslookup challenge.default; nslookup challenge.default.svc.cluster.local'

# 5. Створити в новому Просторі імен
k create namespace test
k create deployment challenge -n test --image=nginx
k expose deployment challenge -n test --port=80

# 6. Розв'язання між Просторами імен
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup challenge.test

# 7. Переглянути логи
k logs -n kube-system -l k8s-app=kube-dns --tail=10

# 8. Очищення
k delete deployment challenge
k delete svc challenge
k delete namespace test
```

</details>

---

## Наступний модуль

[Модуль 3.4: Ingress](module-3.4-ingress.uk.md) — HTTP-маршрутизація та зовнішній доступ до Сервісів.
