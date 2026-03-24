
  [watchdog] Output resumed after 204s stall

> **Складність**: `[MEDIUM]` - Вимагає концептуального розуміння
>
> **Час на проходження**: 35-45 хвилин
>
> **Передумови**: Модуль 0.1 (працюючий кластер)

---

## Чому цей модуль важливий

Кожна команда `kubectl`, яку ви запускаєте, звертається до площини управління. Кожен Под, для якого відбувається планування, кожен Сервіс, який маршрутизує трафік, кожен secret, який зберігає облікові дані — все це відбувається завдяки спільній роботі компонентів площини управління.

Коли пошук несправностей не дає результатів, коли для Подів не відбувається планування, коли ваш кластер "просто перестає працювати" — вам потрібно розуміти, що насправді керує вашим кластером. Іспит CKA перевіряє це. Реальні інциденти вимагають цього.

Цей модуль покаже вам систему зсередини.

> **Аналогія з управлінням повітряним рухом**
>
> Уявіть Kubernetes як аеропорт. Площина управління — це диспетчерська служба: вона не літає на літаках, але без неї ніщо не злетить. API-сервер — це диспетчерська вишка (єдина точка зв'язку). Планувальник (scheduler) вирішує, яку злітну смугу (робочий вузол) використовує кожен літак (Под). Controller manager контролює все і викликає допомогу, коли літаки відхиляються від плану польоту. etcd — це журнал польотів: кожне рішення записано, кожен стан відстежується. Робочі вузли (workers) — це злітно-посадкові смуги, куди фактично приземляються літаки.

---

## Що ви дізнаєтесь

До кінця цього модуля ви зрозумієте:
- Що робить (і чого не робить) кожен компонент площини управління
- Як вони взаємодіють між собою
- Що відбувається, коли кожен із компонентів виходить з ладу
- Як перевірити працездатність компонентів
- Де знаходяться журнали (logs) компонентів

---

## Частина 1: Огляд площини управління

### 1.1 Архітектура з першого погляду

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ПЛОЩИНА УПРАВЛІННЯ                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────────┐ │
│  │ API-сервер  │  │   etcd      │  │    Controller Manager        │ │
│  │ (kube-api)  │◄─┤ (сховище)   │  │  ┌────────────────────────┐  │ │
│  │             │  │             │  │  │ Deployment Controller  │  │ │
│  └──────┬──────┘  └─────────────┘  │  │ ReplicaSet Controller  │  │ │
│         │                          │  │ Node Controller        │  │ │
│         │ ┌─────────────────────┐  │  │ Job Controller         │  │ │
│         │ │    Планувальник     │  │  │ ... (40+ контролерів)  │  │ │
│         │ │  (kube-scheduler)   │  │  └────────────────────────┘  │ │
│         │ └─────────────────────┘  └──────────────────────────────┘ │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │ kubelet спілкується з API-сервером
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           РОБОЧІ ВУЗЛИ                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Вузол 1                     Вузол 2                     Вузол 3 ││
│  │ ┌─────────┐ ┌──────────┐   ┌─────────┐ ┌──────────┐            ││
│  │ │ kubelet │ │kube-proxy│   │ kubelet │ │kube-proxy│   ...      ││
│  │ └─────────┘ └──────────┘   └─────────┘ └──────────┘            ││
│  │ ┌──────────────────────┐   ┌──────────────────────┐            ││
│  │ │ Контейнерне середо-  │   │ Контейнерне середо-  │            ││
│  │ │ вище (containerd)    │   │ вище (containerd)    │            ││
│  │ └──────────────────────┘   └──────────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Площина управління чи Робочі вузли

| Компонент | Де працює | Призначення |
|-----------|---------|---------|
| kube-apiserver | Площина управління | API-шлюз, вся комунікація |
| etcd | Площина управління | Зберігання стану кластера |
| kube-scheduler | Площина управління | Рішення щодо розміщення Подів |
| kube-controller-manager | Площина управління | Цикли узгодження (reconciliation loops) |
| kubelet | Кожен вузол | Життєвий цикл контейнера |
| kube-proxy | Кожен вузол | Мережеві правила |
| Контейнерне середовище | Кожен вузол | Фактично запускає контейнери |

> **Чи знали ви?**
>
> У продакшені etcd часто працює на виділених машинах окремо від інших компонентів площини управління. Кластер etcd з трьох вузлів може обслуговувати тисячі вузлів Kubernetes. Система Borg від Google (попередник Kubernetes) надихнула на такий поділ.

---

## Частина 2: kube-apiserver — Вхідні двері

### 2.1 Що він робить

API-сервер — це **єдиний** компонент, який спілкується безпосередньо з etcd. Всі інші спілкуються з API-сервером.

```
┌─────────────────────────────────────────────────────────────────┐
│                 Всі шляхи ведуть до API-сервера                  │
│                                                                  │
│   kubectl ────────┐                                              │
│   Планувальник ───┼────► kube-apiserver ◄───► etcd              │
│   Контролери ─────┤                                              │
│   kubelet ────────┤                                              │
│   Dashboard ──────┘                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Основні обов'язки**:
- Аутентифікація запитів (хто ви?)
- Авторизація запитів (чи можете ви це зробити?)
- Валідація запитів (чи це дійсний YAML/JSON?)
- Збереження в etcd (збереження бажаного стану)
- Слугує як REST API кластера

### 2.2 Потік API-запитів

Коли ви запускаєте `kubectl create -f pod.yaml`:

```
1. kubectl → API Server: "Create this pod please"
2. API Server: Authentication check ✓
3. API Server: Authorization check ✓
4. API Server: Admission controllers run
5. API Server: Validation check ✓
6. API Server → etcd: "Store this pod spec"
7. API Server → kubectl: "Pod created (pending)"
```

Под ще не існує як працюючий контейнер — він просто збережений в etcd. Далі за справу беруться планувальник та kubelet.

### 2.3 Перевірка працездатності API-сервера

```bash
# Is the API server responding?
kubectl cluster-info

# Check API server component status (legacy)
kubectl get componentstatuses  # Deprecated, may not work on all clusters

# Modern health endpoints (preferred)
kubectl get --raw='/readyz?verbose'
kubectl get --raw='/livez?verbose'

# Direct health endpoint
kubectl get --raw='/healthz'

# Detailed health
kubectl get --raw='/healthz?verbose'
```

### 2.4 Журнали API-сервера

```bash
# If running as a static pod (kubeadm setup)
kubectl logs -n kube-system kube-apiserver-<control-plane-node>

# If running as systemd service
journalctl -u kube-apiserver

# Static pod manifest location
cat /etc/kubernetes/manifests/kube-apiserver.yaml
```

> **Підступ: API-сервер недоступний**
>
> Якщо API-сервер не працює, `kubectl` взагалі не функціонуватиме. Вам доведеться підключитися по SSH до вузла площини управління і перевірити журнали безпосередньо за допомогою `crictl` або `journalctl`. Це типовий сценарій пошуку несправностей на іспиті CKA.

---

## Частина 3: etcd — Джерело істини

### 3.1 Що він робить

etcd — це розподілене сховище пар "ключ-значення". Воно зберігає **весь** стан кластера:
- Усі визначення ресурсів (Поди, Сервіси, secrets тощо)
- Конфігурацію кластера
- Поточний стан усього

Якщо etcd втрачає дані, ваш кластер втрачає пам'ять.

### 3.2 Як Kubernetes використовує etcd

```
Key format: /registry/<resource-type>/<namespace>/<name>

Examples:
/registry/pods/default/nginx
/registry/services/kube-system/kube-dns
/registry/secrets/default/my-secret
/registry/deployments/production/web-app
```

### 3.3 Архітектура etcd

```
┌─────────────────────────────────────────────────────────────────┐
│                 Кластер etcd (Консенсус Raft)                    │
│                                                                  │
│   ┌───────────┐     ┌───────────┐     ┌───────────┐             │
│   │  etcd-1   │◄───►│  etcd-2   │◄───►│  etcd-3   │             │
│   │  (Лідер)  │     │(Підлеглий)│     │(Підлеглий)│             │
│   └───────────┘     └───────────┘     └───────────┘             │
│                                                                  │
│   Записи йдуть до лідера, реплікуються на підлеглих              │
│   Читання може йти з будь-якого вузла                            │
│   Витримує втрату 1 вузла (кворум = 2/3)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Перевірка працездатності etcd

```bash
# etcd member list (if you have etcdctl configured)
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Check etcd pod
kubectl get pods -n kube-system | grep etcd
kubectl logs -n kube-system etcd-<control-plane-node>
```

> **Чи знали ви?**
>
> etcd використовує алгоритм консенсусу Raft. Для його роботи потрібна більшість (кворум). Кластер із 3 вузлів витримує 1 збій. Кластер із 5 вузлів витримує 2 збої. Ось чому у продакшен-кластерах використовується непарна кількість вузлів etcd.

> **Бойова історія: Інцидент із заповненим диском etcd**
>
> Команда керувала кластером місяцями без моніторингу використання диска etcd. etcd зберігає історію всіх змін (для операцій спостереження — watch). Одного разу диск etcd заповнився. Весь кластер перейшов у режим "лише для читання" — жодних нових Подів, жодних оновлень, жодних видалень. Рішення? Екстрене очищення диска та увімкнення автостиснення (auto-compaction) etcd. Вони втратили 4 години продуктивності, тому що не контролювали диск об'ємом 10 ГБ.

---

## Частина 4: kube-scheduler — Сваха

### 4.1 Що він робить

Планувальник стежить за Подами, яким не призначено вузол, і знаходить для них найкращий варіант.

```
┌────────────────────────────────────────────────────────────────┐
│                      Процес планування                          │
│                                                                 │
│  1. Створено новий Под (без nodeName) ─────────────────┐       │
│                                                         │       │
│  2. Планувальник спостерігає за API-сервером            ▼       │
│     "Чи є Поди, що потребують планування?" ◄──────── Черга Подів│
│                                                                 │
│  3. Фільтрація: Які вузли МОЖУТЬ запустити цей Под?            │
│     - Чи достатньо CPU/пам'яті?                                 │
│     - Чи збігаються taints/tolerations?                         │
│     - Чи збігаються node selectors?                             │
│     - Чи задовольняються правила affinity?                      │
│                                                                 │
│  4. Оцінювання: Який вузол НАЙКРАЩИЙ?                          │
│     - Баланс ресурсів                                           │
│     - Розподіл по зонах                                         │
│     - Користувацькі пріоритети                                  │
│                                                                 │
│  5. Прив'язка: Призначення Пода вузлу-переможцю                │
│     Планувальник → API-сервер: "Под X йде на вузол Y"          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Фільтрація чи Оцінювання

**Фільтрація** (жорсткі обмеження): "Чи може цей вузол взагалі запустити Под?"
- Чи достатньо в нього ресурсів?
- Чи відповідає він nodeSelector?
- Чи толерує він taints вузла?
- Чи задовольняє він вимоги affinity?

**Оцінювання** (м'які обмеження): "Який із підходящих вузлів найкращий?"
- Збалансування використання ресурсів
- Розподіл Подів по доменах відмов
- Перевага вузлам із уже завантаженим образом
- Користувацькі плагіни оцінювання

### 4.3 Коли планування завершується невдачею

```bash
# Pod stuck in Pending
kubectl describe pod <pod-name>

# Look for Events section:
# "0/3 nodes are available: 1 node(s) had taint {node-role.kubernetes.io/control-plane: },
#  2 node(s) didn't match Pod's node affinity/selector"
```

Поширені причини:
- **Недостатньо ресурсів**: Жоден вузол не має достатньо CPU/пам'яті
- **Taints не толеруються**: Вузол має taints, Поду бракує tolerations
- **Affinity не задовольняється**: Под вимагає певних міток вузла
- **PVC не прив'язано**: Поду потрібне сховище, якого не існує

### 4.4 Перевірка працездатності планувальника

```bash
# Scheduler pod
kubectl get pods -n kube-system | grep scheduler
kubectl logs -n kube-system kube-scheduler-<control-plane-node>

# Scheduler leader election (in HA setups)
kubectl get endpoints kube-scheduler -n kube-system -o yaml
```

---

## Частина 5: kube-controller-manager — Узгоджувач

### 5.1 Що він робить

Controller manager запускає **контролери** — цикли узгодження, які стежать за поточним станом і працюють над досягненням бажаного стану.

```
┌────────────────────────────────────────────────────────────────┐
│                    Патерн циклу контролера                      │
│                                                                 │
│                    ┌─────────────────┐                         │
│                    │  Бажаний стан   │                         │
│                    │  (в etcd)       │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│                  Порівняти  │                                   │
│                             ▼                                   │
│            Чи поточний стан = бажаному стану?                   │
│                             │                                   │
│              ┌──────────────┴──────────────┐                   │
│              │ ТАК                    НІ   │                   │
│              ▼                             ▼                   │
│      Нічого не робити               Діяти                      │
│   (чекати та спостерігати)     (створити/видалити/оновити)     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Вбудовані контролери

Існує понад 40 контролерів. Основні з них:

| Контролер | За чим стежить | Що робить |
|------------|---------|------|
| **Deployment** | Деплойменти | Створює/оновлює ReplicaSets |
| **ReplicaSet** | ReplicaSets | Забезпечує правильну кількість Подів |
| **Node** | Вузли | Відстежує працездатність вузлів, виселяє Поди з мертвих вузлів |
| **Job** | Jobs | Створює Поди, відстежує завершення |
| **Endpoint** | Сервіси, Поди | Оновлює кінцеві точки Сервісів |
| **ServiceAccount** | Простори імен | Створює ServiceAccount за замовчуванням |
| **Namespace** | Простори імен | Очищає ресурси під час видалення простору імен |

### 5.3 Приклад: ReplicaSet Controller

```yaml
# You create this:
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: web
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
      - name: nginx
        image: nginx
```

```
Controller loop:
1. Watch: "ReplicaSet 'web' wants 3 pods"
2. Check: "How many pods with label 'app=web' exist?"
3. Compare: "0 exist, 3 desired"
4. Act: "Create 3 pods"
5. Repeat forever...

Later:
- Pod dies → Controller sees 2 pods → Creates 1 more
- You scale to 5 → Controller sees 3 pods → Creates 2 more
- You scale to 2 → Controller sees 5 pods → Deletes 3
```

### 5.4 Перевірка Controller Manager

```bash
# Controller manager pod
kubectl get pods -n kube-system | grep controller-manager
kubectl logs -n kube-system kube-controller-manager-<control-plane-node>

# Check for specific controller issues in logs
kubectl logs -n kube-system kube-controller-manager-<node> | grep -i "error\|failed"
```

> **Підступ: Controller Manager не працює**
>
> Якщо controller manager зупиняється, нічого активно не ламається одразу — існуючі Поди продовжують працювати. Але нічого нового не відбувається: Деплойменти не створюватимуть Поди, мертві Поди не будуть замінені, Jobs не запускатимуться. Кластер стає "замороженим".

---

## Частина 6: Компоненти вузла

### 6.1 kubelet — Агент вузла

kubelet працює на кожному вузлі (включаючи площину управління). Він відповідає за:
- Реєстрацію вузла в кластері
- Відстеження Подів, призначених його вузлу
- Запуск/зупинку контейнерів через контейнерне середовище
- Передачу статусу вузла та Подів назад до API-сервера
- Запуск проб liveness/readiness

```bash
# Check kubelet status
systemctl status kubelet

# kubelet logs
journalctl -u kubelet -f

# kubelet configuration
cat /var/lib/kubelet/config.yaml
```

### 6.2 kube-proxy — Мережевий сантехнік

kube-proxy працює на кожному вузлі. Він підтримує мережеві правила, щоб Сервіси працювали:
- Відстежує Сервіси та Endpoints
- Створює правила iptables/IPVS для пересилання трафіку
- Забезпечує роботу сервісів ClusterIP, NodePort, LoadBalancer

```bash
# Check kube-proxy
kubectl get pods -n kube-system | grep kube-proxy
kubectl logs -n kube-system kube-proxy-<id>

# See iptables rules kube-proxy created
iptables -t nat -L KUBE-SERVICES
```

### 6.3 Контейнерне середовище

Фактичне програмне забезпечення, яке запускає контейнери. Kubernetes підтримує:
- **containerd** (найпоширеніше, за замовчуванням у kubeadm)
- **CRI-O** (використовується в OpenShift)
- Docker (застаріло з версії K8s 1.24, але образи все ще працюють)

```bash
# Check containerd
systemctl status containerd
crictl ps  # List running containers
crictl images  # List images
```

---

## Частина 7: Збираємо все разом

### 7.1 Що відбувається при створенні Деплойменту

```bash
kubectl create deployment nginx --image=nginx --replicas=3
```

```
┌─────────────────────────────────────────────────────────────────┐
│ Хронологія подій                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 0ms    kubectl → API-сервер: "Створити Deployment nginx"        │
│ 5ms    API-сервер → etcd: Зберегти Deployment                   │
│                                                                  │
│ 10ms   Deployment Controller бачить новий Deployment            │
│ 15ms   Deployment Controller → API: "Створити ReplicaSet"       │
│ 20ms   API-сервер → etcd: Зберегти ReplicaSet                   │
│                                                                  │
│ 25ms   ReplicaSet Controller бачить новий ReplicaSet            │
│ 30ms   ReplicaSet Controller → API: "Створити Под 1, 2, 3"      │
│ 35ms   API-сервер → etcd: Зберегти 3 Поди (Pending)             │
│                                                                  │
│ 40ms   Планувальник бачить 3 Поди без планування                │
│ 50ms   Планувальник → API: "Под 1→node1, Под 2→node2, Под 3→node1"│
│ 55ms   API-сервер → etcd: Оновити Поди з nodeName               │
│                                                                  │
│ 60ms   kubelet на node1 бачить 2 Поди, призначені йому          │
│ 65ms   kubelet на node2 бачить 1 Под, призначений йому          │
│ 70ms   kubelets → containerd: "Запустити контейнери nginx"      │
│                                                                  │
│ 500ms  Контейнери працюють                                       │
│ 505ms  kubelets → API: "Поди в стані Running"                   │
│ 510ms  API-сервер → etcd: Оновити статус Подів                  │
│                                                                  │
│ Готово! kubectl get pods показує 3/3 Running                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **Статичні Поди (Static pods)** — це спеціальні Поди, якими керує безпосередньо kubelet, а не API-сервер. Компоненти площини управління (API-сервер, планувальник, controller manager, etcd) працюють як статичні Поди в кластерах kubeadm. Їхні маніфести знаходяться в каталозі `/etc/kubernetes/manifests/`.

- **API-сервер не має стану (stateless)**. Усе зберігається в etcd. Ви можете перезапустити API-сервер і нічого не втратите. Саме тому Kubernetes такий стійкий.

- **Контролери використовують вибір лідера (leader election)** у конфігураціях високої доступності (HA). Лише один controller manager є активним у певний момент часу, інші перебувають у режимі очікування. Те саме стосується планувальника.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|---------|----------|
| Думати, що kubelet працює в Поді | kubelet — це сервіс systemd | Перевірити за допомогою `systemctl status kubelet` |
| Ігнорування працездатності etcd | Проблеми etcd каскадно впливають на все | Моніторити метрики та диск etcd |
| Неперевірка журналів компонентів | Пропуск першопричини під час пошуку несправностей | Завжди перевіряти журнали у kube-system |
| Плутанина між площиною управління та робочим вузлом | Різні компоненти, різні проблеми | Знати, що де працює |
| Забування про статичні Поди | Неможливо видалити їх за допомогою kubectl | Редагувати/видаляти маніфест у `/etc/kubernetes/manifests/` |

---

## Тест

1. **Який компонент є єдиним, що взаємодіє безпосередньо з etcd?**
   <details>
   <summary>Відповідь</summary>
   kube-apiserver. Усі інші компоненти (планувальник, контролери, kubelet) взаємодіють через API-сервер, ніколи не напряму з etcd.
   </details>

2. **Под застряг у стані Pending. Який компонент слід дослідити в першу чергу?**
   <details>
   <summary>Відповідь</summary>
   kube-scheduler. Pending означає, що Поду ще не призначено вузол, а це робота планувальника. Перевірте журнали планувальника та запустіть `kubectl describe pod`, щоб побачити, чому планування не вдалося.
   </details>

3. **Ви видаляєте Под із ReplicaSet. Що відбувається і чому?**
   <details>
   <summary>Відповідь</summary>
   Автоматично створюється новий Под. ReplicaSet Controller безперервно відстежує Поди, що відповідають його селектору. Коли він бачить менше Подів, ніж потрібно (spec.replicas), він створює нові, щоб узгодити різницю.
   </details>

4. **Де знаходяться маніфести для статичних Подів площини управління?**
   <details>
   <summary>Відповідь</summary>
   У каталозі `/etc/kubernetes/manifests/` на вузлі площини управління. kubelet відстежує цей каталог і автоматично запускає/зупиняє Поди на основі розміщених там файлів YAML.
   </details>

---

## Практична вправа

**Завдання**: Дослідіть компоненти площини управління вашого кластера.

**Кроки**:

1. **Виведіть список усіх Подів площини управління**:
```bash
kubectl get pods -n kube-system
```

2. **Перевірте працездатність компонентів**:
```bash
kubectl get componentstatuses
kubectl get --raw='/healthz?verbose'
```

3. **Перегляньте конфігурацію API-сервера**:
```bash
# On control plane node
sudo cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -A5 "command:"
```

4. **Перевірте журнали планувальника на наявність недавньої активності**:
```bash
kubectl logs -n kube-system -l component=kube-scheduler --tail=20
```

5. **Спостерігайте за controller manager у дії**:
```bash
# Terminal 1: Watch controller logs
kubectl logs -n kube-system -l component=kube-controller-manager -f

# Terminal 2: Create and delete a deployment
kubectl create deployment test --image=nginx --replicas=2
kubectl delete deployment test
```

6. **Дослідіть etcd (за наявності)**:
```bash
# On control plane node with etcdctl
sudo ETCDCTL_API=3 etcdctl get /registry/namespaces/default \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

**Критерії успіху**:
- [ ] Можете ідентифікувати всі компоненти площини управління та їхні Поди
- [ ] Можете перевірити працездатність API-сервера
- [ ] Можете знайти та прочитати журнали компонентів площини управління
- [ ] Розумієте, що робить кожен компонент під час створення Пода

**Очищення**:
```bash
# Remove test deployment if created
kubectl delete deployment test --ignore-not-found
```

---

## Практичні вправи

### Вправа 1: Гонка з ідентифікації компонентів (Ціль: 2 хвилини)

Не заглядаючи в нотатки, визначте, який компонент відповідає за кожен сценарій:

| Сценарій | Компонент |
|----------|-----------|
| Зберігає весь стан кластера | ___ |
| Вирішує, на якому вузлі запустити новий Под | ___ |
| Аутентифікує запити kubectl | ___ |
| Створює Поди при зміні ReplicaSet | ___ |
| Повідомляє статус вузла площині управління | ___ |
| Підтримує правила iptables для Сервісів | ___ |

<details>
<summary>Відповіді</summary>

1. etcd
2. kube-scheduler
3. kube-apiserver
4. kube-controller-manager (ReplicaSet controller)
5. kubelet
6. kube-proxy

</details>

### Вправа 2: Пошук несправностей — Відсутній планувальник (Ціль: 5 хвилин)

**Сценарій**: Поди назавжди застрягли у стані Pending.

```bash
# Setup: Break the scheduler
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/

# Create a test pod
kubectl run drill-pod --image=nginx

# Observe the problem
kubectl get pods  # Pending forever
kubectl describe pod drill-pod | grep -A5 Events

# YOUR TASK: Diagnose and fix
# 1. What's missing?
# 2. How do you restore it?
```

<details>
<summary>Рішення</summary>

```bash
# Check control plane pods
kubectl get pods -n kube-system | grep scheduler  # Nothing!

# Restore scheduler
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/

# Wait for scheduler and verify
kubectl get pods -n kube-system | grep scheduler  # Running!
kubectl get pod drill-pod  # Now Running

# Cleanup
kubectl delete pod drill-pod
```

</details>

### Вправа 3: Пошук несправностей — Controller Manager не працює (Ціль: 5 хвилин)

**Сценарій**: Деплойменти створюють ReplicaSets, але Поди так і не з'являються.

```bash
# Setup
sudo mv /etc/kubernetes/manifests/kube-controller-manager.yaml /tmp/

# Create deployment
kubectl create deployment drill-deploy --image=nginx --replicas=3

# Observe
kubectl get deploy  # Shows 0/3 ready
kubectl get rs      # ReplicaSet exists but...
kubectl get pods    # No pods!

# YOUR TASK: Diagnose and fix
```

<details>
<summary>Рішення</summary>

```bash
# Check controller manager
kubectl get pods -n kube-system | grep controller  # Nothing!

# Restore controller manager
sudo mv /tmp/kube-controller-manager.yaml /etc/kubernetes/manifests/

# Watch pods appear
kubectl get pods -w  # 3 pods created

# Cleanup
kubectl delete deployment drill-deploy
```

</details>

### Вправа 4: Глибоке занурення у працездатність API-сервера (Ціль: 3 хвилини)

Перевірте працездатність API-сервера кількома методами:

```bash
# Method 1: Basic connectivity
kubectl cluster-info

# Method 2: Health endpoints
kubectl get --raw='/healthz'
kubectl get --raw='/readyz'
kubectl get --raw='/livez'

# Method 3: Detailed health
kubectl get --raw='/readyz?verbose' | grep -E "^\[|ok|failed"

# Method 4: Direct curl (from control plane)
curl -k https://localhost:6443/healthz

# Method 5: Check API server logs for errors
kubectl logs -n kube-system -l component=kube-apiserver --tail=20 | grep -i error
```

### Вправа 5: Спостереження за циклом узгодження (Ціль: 5 хвилин)

Побачте контролери в дії:

```bash
# Terminal 1: Watch controller manager logs
kubectl logs -n kube-system -l component=kube-controller-manager -f | grep -i "replicaset\|deployment"

# Terminal 2: Create, scale, delete deployment
kubectl create deployment watch-me --image=nginx --replicas=2
sleep 5
kubectl scale deployment watch-me --replicas=5
sleep 5
kubectl delete deployment watch-me

# Observe logs in Terminal 1 - see the controller react to each change
```

### Вправа 6: Дослідження etcd (Ціль: 5 хвилин)

Дослідіть, що зберігає etcd (вимагає etcdctl на площині управління):

```bash
# Set up etcdctl alias
export ETCDCTL_API=3
alias etcdctl='etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key'

# List all keys (be careful in production!)
etcdctl get / --prefix --keys-only | head -50

# Find all pods
etcdctl get /registry/pods --prefix --keys-only

# Get a specific pod's data
etcdctl get /registry/pods/default/<pod-name>
```

### Вправа 7: Виклик — Повний перезапуск площини управління

**Просунутий рівень**: Перезапустіть усі компоненти площини управління та перевірте відновлення кластера.

```bash
# WARNING: Only do this on practice clusters!

# 1. Note current state
kubectl get nodes
kubectl get pods -A | wc -l

# 2. Restart all control plane components
sudo systemctl restart kubelet
# Static pods will restart automatically

# 3. Wait and verify recovery
sleep 30
kubectl get nodes  # All Ready?
kubectl get pods -n kube-system  # All Running?

# 4. Test workload scheduling
kubectl run recovery-test --image=nginx
kubectl get pods  # Running?
kubectl delete pod recovery-test
```

---

## Наступний модуль

[Модуль 1.2: Інтерфейси розширення (CNI, CSI, CRI)](module-1.2-extension-interfaces.uk.md) — Як Kubernetes підключає мережі, сховища та контейнерні середовища.
