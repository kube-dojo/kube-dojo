---
title: "Модуль 2.3: DaemonSets та StatefulSets"
slug: uk/k8s/cka/part2-workloads-scheduling/module-2.3-daemonsets-statefulsets
sidebar: 
  order: 4
lab: 
  id: cka-2.3-daemonsets-statefulsets
  url: https://killercoda.com/kubedojo/scenario/cka-2.3-daemonsets-statefulsets
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
en_commit: "0db65d452c40cd0d7f3715378f49ec94bfd032fb"
en_file: "src/content/docs/k8s/cka/part2-workloads-scheduling/module-2.3-daemonsets-statefulsets.md"---
> **Складність**: `[MEDIUM]` — Спеціалізовані шаблони навантажень
>
> **Час на проходження**: 40-50 хвилин
>
> **Передумови**: Модуль 2.1 (Поди), Модуль 2.2 (Деплойменти)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Розгорнути** DaemonSets для сервісів на рівні вузлів та StatefulSets для stateful-застосунків
- **Пояснити**, як іменування подів StatefulSet, прив'язка PVC та упорядковане розгортання відрізняються від Deployments
- **Налаштувати** tolerations DaemonSet для запуску на вузлах площини управління за потреби
- **Діагностувати** проблеми StatefulSet (застрягла прив'язка PVC, збої упорядкованого розгортання, DNS headless service)

---

## Чому цей модуль важливий

Деплойменти чудово працюють для застосунків без стану, але не все є stateless. Деякі навантаження мають особливі вимоги:

- **DaemonSets**: Коли вам потрібен рівно один Под на кожному вузлі (збір логів, моніторинг, мережеві плагіни)
- **StatefulSets**: Коли Поди потребують стабільних ідентичностей і постійного сховища (бази даних, розподілені системи)

Іспит CKA перевіряє ваше розуміння того, коли використовувати кожен контролер і як їх діагностувати. Знання правильного інструменту для кожного завдання — ключова навичка адміністратора.

> **Аналогія зі спеціалізованими командами**
>
> Уявіть свій кластер як лікарню. **Деплойменти** — це терапевти: їх може бути скільки завгодно, вони взаємозамінні, і пацієнтам байдуже, до якого саме потрапити. **DaemonSets** — це охоронці: потрібен рівно один на кожному вході (вузлі), не більше й не менше. **StatefulSets** — це хірурги: кожен має унікальну ідентичність, власні виділені інструменти (сховище), і пацієнти звертаються конкретно до «доктора Сміта» (стабільна мережева ідентичність).

---

## Що ви дізнаєтесь

До кінця цього модуля ви зможете:
- Створювати та керувати DaemonSets
- Розуміти, коли використовувати DaemonSets замість Деплойментів
- Створювати та керувати StatefulSets
- Розуміти стабільну мережеву ідентичність і сховище
- Діагностувати проблеми DaemonSet та StatefulSet

---

## Частина 1: DaemonSets

### 1.1 Що таке DaemonSet?

DaemonSet гарантує, що **всі (або деякі) вузли запускають копію Пода**.

```
┌────────────────────────────────────────────────────────────────┐
│                       DaemonSet                                 │
│                                                                 │
│   Вузол 1             Вузол 2             Вузол 3              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌─────────┐ │      │
│   │ │ DS Под  │ │     │ │ DS Под  │ │     │ │ DS Под  │ │      │
│   │ │(fluentd)│ │     │ │(fluentd)│ │     │ │(fluentd)│ │      │
│   │ └─────────┘ │     │ └─────────┘ │     │ └─────────┘ │      │
│   │             │     │             │     │             │      │
│   │ [Поди App] │     │ [Поди App] │     │ [Поди App] │      │
│   │             │     │             │     │             │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                 │
│   Коли Вузол 4 приєднується → DaemonSet автоматично створює Под│
│   Коли Вузол 2 від'єднується → Под видаляється                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Типові випадки використання DaemonSet

| Випадок використання | Приклад |
|----------------------|---------|
| Збір логів | Fluentd, Filebeat |
| Моніторинг вузлів | Node Exporter, Datadog agent |
| Мережеві плагіни | Calico, Cilium, Weave |
| Демони сховища | GlusterFS, Ceph |
| Агенти безпеки | Falco, Sysdig |

### 1.3 Створення DaemonSet

```yaml
# fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  labels:
    app: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluentd:v1.16
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

```bash
kubectl apply -f fluentd-daemonset.yaml
```

> **Зупиніться та подумайте**: У вас кластер з 5 вузлів, і ви створюєте DaemonSet. Потім до кластера приєднується 6-й вузол. Що відбувається автоматично? А тепер уявіть, що ви робите те саме з Deployment, встановленим на 5 реплік — що відбувається, коли приєднується 6-й вузол?

### 1.4 DaemonSet проти Деплойменту

| Аспект | DaemonSet | Деплоймент |
|--------|-----------|------------|
| Кількість Подів | Один на вузол (автоматично) | Вказана кількість реплік |
| Планування | Обходить планувальник | Використовує планувальник |
| Додавання вузла | Автоматично створює Под | Жодних автоматичних дій |
| Випадок використання | Сервіси рівня вузла | Навантаження застосунків |

### 1.5 Команди для DaemonSet

```bash
# Список DaemonSets
kubectl get daemonsets
kubectl get ds           # Скорочена форма

# Опис DaemonSet
kubectl describe ds fluentd

# Перевірка Подів, створених DaemonSet
kubectl get pods -l app=fluentd -o wide

# Видалення DaemonSet
kubectl delete ds fluentd
```

> **Чи знали ви?**
>
> DaemonSets за замовчуванням ігнорують більшість обмежень планування. Вони навіть запускаються на вузлах площини управління, якщо немає taints, які цьому перешкоджають. Використовуйте `nodeSelector` або `tolerations` для контролю розміщення.

---

## Частина 2: Планування DaemonSet

### 2.1 Запуск на конкретних вузлах

Використовуйте `nodeSelector`, щоб запускати лише на певних вузлах:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ssd-monitor
spec:
  selector:
    matchLabels:
      app: ssd-monitor
  template:
    metadata:
      labels:
        app: ssd-monitor
    spec:
      nodeSelector:
        disk: ssd            # Тільки вузли з цим лейблом
      containers:
      - name: monitor
        image: busybox
        command: ["sleep", "infinity"]
```

```bash
# Додати лейбл до вузла
kubectl label node worker-1 disk=ssd

# DaemonSet запускається лише на вузлах з лейблом
kubectl get pods -l app=ssd-monitor -o wide
```

### 2.2 Толерування Taints

DaemonSets часто потребують запуску на вузлах з taints:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      tolerations:
      # Толерування taint площини управління
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      # Толерування всіх taints (запуск скрізь)
      - operator: Exists
      containers:
      - name: monitor
        image: prom/node-exporter
```

### 2.3 Стратегія оновлення

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  updateStrategy:
    type: RollingUpdate        # За замовчуванням
    rollingUpdate:
      maxUnavailable: 1        # Оновлення по одному вузлу за раз
  selector:
    matchLabels:
      app: fluentd
  template:
    # ...
```

| Стратегія | Поведінка |
|-----------|----------|
| `RollingUpdate` | Поступове оновлення Подів, по одному вузлу за раз |
| `OnDelete` | Оновлення лише після ручного видалення Пода |

---

## Частина 3: StatefulSets

### 3.1 Що таке StatefulSet?

StatefulSets керують застосунками зі станом та забезпечують:
- **Стабільні, унікальні мережеві ідентифікатори**
- **Стабільне, постійне сховище**
- **Впорядковане, коректне розгортання та масштабування**

```
┌────────────────────────────────────────────────────────────────┐
│                       StatefulSet                               │
│                                                                 │
│   На відміну від Деплойментів, Поди мають стабільні            │
│   ідентичності:                                                │
│                                                                 │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│   │    web-0      │  │    web-1      │  │    web-2      │      │
│   │  (завжди 0)   │  │  (завжди 1)   │  │  (завжди 2)   │      │
│   │               │  │               │  │               │      │
│   │ PVC: data-0   │  │ PVC: data-1   │  │ PVC: data-2   │      │
│   │ DNS: web-0... │  │ DNS: web-1... │  │ DNS: web-2... │      │
│   └───────────────┘  └───────────────┘  └───────────────┘      │
│                                                                 │
│   Якщо web-1 зупиняється і перезапускається:                   │
│   - Все ще має ім'я web-1 (не web-3)                           │
│   - Повторно підключає PVC data-1                              │
│   - Те саме DNS-ім'я: web-1.nginx.default.svc.cluster.local   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Випадки використання StatefulSet

| Випадок використання | Приклад |
|----------------------|---------|
| Бази даних | PostgreSQL, MySQL, MongoDB |
| Розподілені системи | Kafka, Zookeeper, etcd |
| Пошукові системи | Elasticsearch |
| Черги повідомлень | RabbitMQ |

> **Зупиніться та подумайте**: Якщо ви видалите Під `web-1` зі StatefulSet, яке ім'я отримає замінюючий Під — `web-1` чи `web-3`? Що станеться з PVC, який був прив'язаний до `web-1`?

### 3.3 Вимоги StatefulSet

StatefulSets вимагають **Headless Service** для мережевої ідентичності:

```yaml
# Headless Service (обов'язковий)
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None          # Це робить його headless
  selector:
    app: nginx
---
# StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx       # Повинен посилатися на headless service
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
        volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:    # Створює PVC для кожного Пода
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

### 3.4 Стабільна мережева ідентичність

```bash
# DNS-імена Подів відповідають шаблону:
# <ім'я-пода>.<ім'я-сервісу>.<namespace>.svc.cluster.local

# Для StatefulSet "web" з headless service "nginx":
web-0.nginx.default.svc.cluster.local
web-1.nginx.default.svc.cluster.local
web-2.nginx.default.svc.cluster.local

# Інші Поди можуть звертатися до конкретних екземплярів:
curl web-0.nginx
curl web-1.nginx
```

### 3.5 Стабільне сховище

```bash
# Кожен Под отримує власний PVC з іменем:
# <volumeClaimTemplates.name>-<ім'я-пода>
data-web-0
data-web-1
data-web-2

# При перезапуску Під повторно підключає свій конкретний PVC
# Дані зберігаються між перезапусками Пода
```

> **Чи знали ви?**
>
> Коли ви видаляєте StatefulSet, PVC НЕ видаляються автоматично. Це функція безпеки — ваші дані зберігаються. Щоб очистити сховище, вручну видаліть PVC після видалення StatefulSet.

---

## Частина 4: Операції з StatefulSet

### 4.1 Впорядковане створення та видалення

```
Масштабування вгору (0 → 3):
web-0 створено й готово → web-1 створено й готово → web-2 створено

Масштабування вниз (3 → 1):
web-2 завершено → web-1 завершено → web-0 залишається

Кожен Під очікує, поки попередній буде в стані Running та Ready
```

### 4.2 Політика керування Подами

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  podManagementPolicy: OrderedReady   # За замовчуванням — послідовно
  # podManagementPolicy: Parallel     # Всі одночасно (як Деплоймент)
```

| Політика | Поведінка |
|----------|----------|
| `OrderedReady` | Послідовне створення/видалення (за замовчуванням) |
| `Parallel` | Всі Поди створюються/видаляються одночасно |

> **Подумайте**: Ви запускаєте StatefulSet з 3 репліками для кластера баз даних. Ви хочете протестувати нову версію лише на одній репліці, перш ніж розгортати її на всіх. Як би ви використали поле `partition` для досягнення канарейкового розгортання? Який Під оновлюється першим — web-0 чи web-2?

### 4.3 Стратегія оновлення

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2          # Оновлювати лише Поди >= 2
```

**Partition** дає змогу робити канаркові розгортання:
- З `partition: 2` лише web-2 отримує оновлення
- web-0 та web-1 залишаються на старій версії
- Корисно для тестування оновлень на підмножині Подів

### 4.4 Команди для StatefulSet

```bash
# Список StatefulSets
kubectl get statefulsets
kubectl get sts           # Скорочена форма

# Опис
kubectl describe sts web

# Масштабування
kubectl scale sts web --replicas=5

# Перевірка Подів (зверніть увагу на впорядковані імена)
kubectl get pods -l app=nginx

# Перевірка PVC (один на кожен Під)
kubectl get pvc

# Видалення StatefulSet (PVC залишаються!)
kubectl delete sts web

# Ручне видалення PVC
kubectl delete pvc data-web-0 data-web-1 data-web-2
```

---

## Частина 5: Деплоймент проти StatefulSet

### 5.1 Порівняння

| Аспект | Деплоймент | StatefulSet |
|--------|------------|-------------|
| Імена Подів | Випадковий суфікс (nginx-5d5dd5d5fb-xyz) | Порядковий індекс (web-0, web-1) |
| Мережева ідентичність | Немає (використовуйте Service) | Стабільний DNS для кожного Пода |
| Сховище | Спільне або відсутнє | Виділений PVC для кожного Пода |
| Порядок масштабування | Будь-який порядок | Послідовний (впорядкований) |
| Поступове оновлення | Випадковий порядок | Зворотний порядок (N-1 першим) |
| Випадок використання | Застосунки без стану | Застосунки зі станом |

### 5.2 Коли що використовувати

```
┌────────────────────────────────────────────────────────────────┐
│              Вибір правильного контролера                       │
│                                                                 │
│   Чи потребує кожен Під унікальну ідентичність?                │
│         │                                                       │
│         ├── Ні ──► Чи потрібен один Під на кожному вузлі?      │
│         │                │                                      │
│         │                ├── Так ──► DaemonSet                 │
│         │                │                                      │
│         │                └── Ні ──► Деплоймент                 │
│         │                                                       │
│         └── Так ──► Чи потрібне постійне сховище?              │
│                          │                                      │
│                          └── Так/Ні ──► StatefulSet            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Історія з практики: Катастрофа з базою даних**
>
> Одна команда розгорнула PostgreSQL за допомогою Деплойменту з PVC. Все працювало — поки Під не було переплановано на інший вузол. Новий Під отримав іншу IP-адресу, реплікація зламалася, і резервний сервер не міг знайти основний. Перехід на StatefulSet зі стабільною мережевою ідентичністю вирішив усе. Використовуйте правильний інструмент!

---

## Частина 6: Headless Services — глибоке занурення

### 6.1 Що таке Headless Service?

Service з `clusterIP: None`. Замість балансування навантаження DNS повертає IP-адреси окремих Подів.

```yaml
# Звичайний Service
apiVersion: v1
kind: Service
metadata:
  name: nginx-regular
spec:
  selector:
    app: nginx
  ports:
  - port: 80
# DNS: nginx-regular → ClusterIP (з балансуванням)

---
# Headless Service
apiVersion: v1
kind: Service
metadata:
  name: nginx-headless
spec:
  clusterIP: None           # Headless!
  selector:
    app: nginx
  ports:
  - port: 80
# DNS: nginx-headless → Повертає всі IP Подів
# DNS: web-0.nginx-headless → IP конкретного Пода
```

### 6.2 Порівняння DNS-резолюції

```bash
# Звичайний service — повертає ClusterIP
nslookup nginx-regular
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name: nginx-regular.default.svc.cluster.local
# Address: 10.96.100.50  (ClusterIP)

# Headless service — повертає IP Подів
nslookup nginx-headless
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name: nginx-headless.default.svc.cluster.local
# Address: 10.244.1.5  (IP Пода)
# Address: 10.244.2.6  (IP Пода)
# Address: 10.244.3.7  (IP Пода)
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| StatefulSet без headless Service | Поди не отримують стабільних DNS-імен | Створіть headless Service з відповідним selector |
| Видалення StatefulSet з очікуванням автоочищення PVC | Дані залишаються, квота сховища витрачається | Вручну видаліть PVC, якщо дані не потрібні |
| Використання Деплойменту для баз даних | Немає стабільної ідентичності, проблеми зі сховищем | Використовуйте StatefulSet для навантажень зі станом |
| DaemonSet на всіх вузлах несподівано | Запускається й на площині управління | Додайте відповідні tolerations/nodeSelector |
| Неправильне serviceName у StatefulSet | DNS-резолюція не працює | Переконайтеся, що serviceName відповідає імені headless Service |

---

## Тест

1. **Що гарантує запуск рівно одного Пода на кожному вузлі?**
   <details>
   <summary>Відповідь</summary>
   **DaemonSet**. Він автоматично створює Під на кожному вузлі (або на вибраних вузлах через nodeSelector) і видаляє Поди при видаленні вузлів.
   </details>

2. **Навіщо StatefulSets потрібен headless Service?**
   <details>
   <summary>Відповідь</summary>
   Headless Service (clusterIP: None) надає стабільні DNS-імена для кожного Пода. Без нього Поди не мали б передбачуваних мережевих ідентичностей. Формат DNS: `<ім'я-пода>.<ім'я-сервісу>.<namespace>.svc.cluster.local`.
   </details>

3. **Що відбувається з PVC при видаленні StatefulSet?**
   <details>
   <summary>Відповідь</summary>
   PVC **НЕ** видаляються автоматично. Це функція безпеки для збереження даних. Вам потрібно вручну видалити PVC, якщо ви хочете звільнити сховище.
   </details>

4. **Чим масштабування StatefulSet відрізняється від Деплойменту?**
   <details>
   <summary>Відповідь</summary>
   StatefulSets масштабуються **послідовно**. Масштабування вгору: web-0, потім web-1, потім web-2 (кожен очікує, поки попередній буде Ready). Масштабування вниз: у зворотному порядку. Деплойменти масштабують Поди паралельно.
   </details>

---

## Практична вправа

**Завдання**: Створити DaemonSet і StatefulSet, зрозуміти їхню поведінку.

**Кроки**:

### Частина A: DaemonSet

1. **Створіть DaemonSet**:
```bash
cat > node-monitor-ds.yaml << 'EOF'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      containers:
      - name: monitor
        image: busybox
        command: ["sh", "-c", "while true; do echo $(hostname); sleep 60; done"]
        resources:
          limits:
            memory: 50Mi
            cpu: 50m
EOF

kubectl apply -f node-monitor-ds.yaml
```

2. **Перевірте, що на кожному вузлі рівно один Під**:
```bash
kubectl get pods -l app=node-monitor -o wide
kubectl get ds node-monitor
# DESIRED = CURRENT = READY = кількість вузлів
```

3. **Перегляньте логи Пода конкретного вузла**:
```bash
kubectl logs -l app=node-monitor --all-containers
```

4. **Очищення DaemonSet**:
```bash
kubectl delete ds node-monitor
rm node-monitor-ds.yaml
```

### Частина B: StatefulSet

1. **Створіть headless Service і StatefulSet**:
```bash
cat > statefulset-demo.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  clusterIP: None
  selector:
    app: nginx
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
EOF

kubectl apply -f statefulset-demo.yaml
```

2. **Спостерігайте за впорядкованим створенням**:
```bash
kubectl get pods -l app=nginx -w
# web-0 Running, потім web-1, потім web-2
```

3. **Перевірте стабільну мережеву ідентичність**:
```bash
# Створіть тестовий Під
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-0.nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-1.nginx
```

4. **Масштабуйте вниз і спостерігайте за порядком**:
```bash
kubectl scale sts web --replicas=1
kubectl get pods -l app=nginx -w
# web-2 завершується, потім web-1
```

5. **Масштабуйте назад вгору**:
```bash
kubectl scale sts web --replicas=3
kubectl get pods -l app=nginx -w
# web-1 створюється, потім web-2
```

6. **Очищення**:
```bash
kubectl delete -f statefulset-demo.yaml
rm statefulset-demo.yaml
```

**Критерії успіху**:
- [ ] Можете створювати DaemonSets
- [ ] Розумієте поведінку «один Під на вузол»
- [ ] Можете створювати StatefulSets з headless Services
- [ ] Розумієте впорядковане масштабування
- [ ] Знаєте, коли використовувати кожен контролер

---

## Практичні вправи

### Вправа 1: Створення DaemonSet (Ціль: 3 хвилини)

```bash
# Створіть DaemonSet
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      containers:
      - name: collector
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Перевірка
kubectl get ds log-collector
kubectl get pods -l app=log-collector -o wide

# Очищення
kubectl delete ds log-collector
```

### Вправа 2: DaemonSet з nodeSelector (Ціль: 5 хвилин)

```bash
# Додайте лейбл до вузла
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE disk=ssd

# Створіть DaemonSet з nodeSelector
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ssd-only
spec:
  selector:
    matchLabels:
      app: ssd-only
  template:
    metadata:
      labels:
        app: ssd-only
    spec:
      nodeSelector:
        disk: ssd
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Перевірка — повинен запуститися лише на вузлі з лейблом
kubectl get pods -l app=ssd-only -o wide

# Очищення
kubectl delete ds ssd-only
kubectl label node $NODE disk-
```

### Вправа 3: Базовий StatefulSet (Ціль: 5 хвилин)

```bash
# Створіть headless service та StatefulSet
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  clusterIP: None
  selector:
    app: db
  ports:
  - port: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
      - name: postgres
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Спостерігайте за впорядкованим створенням
kubectl get pods -l app=db -w &
sleep 30
kill %1

# Перевірте імена
kubectl get pods -l app=db

# Очищення
kubectl delete sts db
kubectl delete svc db
```

### Вправа 4: Тест DNS для StatefulSet (Ціль: 5 хвилин)

```bash
# Створіть StatefulSet з headless service
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  clusterIP: None
  selector:
    app: nginx
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Дочекайтеся готовності
kubectl wait --for=condition=ready pod/web-0 pod/web-1 --timeout=60s

# Тест DNS-резолюції
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-0.nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-1.nginx

# Очищення
kubectl delete sts web
kubectl delete svc nginx
```

### Вправа 5: Порядок масштабування StatefulSet (Ціль: 3 хвилини)

```bash
# Створіть StatefulSet
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: order-test
spec:
  clusterIP: None
  selector:
    app: order-test
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: order
spec:
  serviceName: order-test
  replicas: 1
  selector:
    matchLabels:
      app: order-test
  template:
    metadata:
      labels:
        app: order-test
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Масштабуйте вгору і спостерігайте за порядком
kubectl scale sts order --replicas=3
kubectl get pods -l app=order-test -w &
sleep 30
kill %1

# Масштабуйте вниз і спостерігайте за зворотним порядком
kubectl scale sts order --replicas=1
kubectl get pods -l app=order-test -w &
sleep 30
kill %1

# Очищення
kubectl delete sts order
kubectl delete svc order-test
```

### Вправа 6: Діагностика — DaemonSet не запускається на вузлі

```bash
# Додайте taint до вузла
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl taint node $NODE special=true:NoSchedule

# Створіть DaemonSet без toleration
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: no-toleration
spec:
  selector:
    matchLabels:
      app: no-toleration
  template:
    metadata:
      labels:
        app: no-toleration
    spec:
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Перевірка — не запуститься на вузлі з taint
kubectl get pods -l app=no-toleration -o wide
kubectl get ds no-toleration

# ВАШЕ ЗАВДАННЯ: Виправити, додавши toleration
# (Видаліть і створіть заново з toleration)

# Очищення
kubectl delete ds no-toleration
kubectl taint node $NODE special-
```

<details>
<summary>Рішення</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: with-toleration
spec:
  selector:
    matchLabels:
      app: with-toleration
  template:
    metadata:
      labels:
        app: with-toleration
    spec:
      tolerations:
      - key: special
        operator: Equal
        value: "true"
        effect: NoSchedule
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

kubectl get pods -l app=with-toleration -o wide
kubectl delete ds with-toleration
```

</details>

### Вправа 7: Завдання — Визначте правильний контролер

Для кожного сценарію визначте, що використовувати — Деплоймент, DaemonSet чи StatefulSet:

1. Веб-застосунок з 5 репліками
2. Збирач логів на кожному вузлі
3. Кластер бази даних PostgreSQL
4. REST API сервіс
5. Prometheus node exporter
6. Кластер Kafka
7. nginx reverse proxy

<details>
<summary>Відповіді</summary>

1. **Деплоймент** — Веб-застосунок без стану
2. **DaemonSet** — Потрібен один на кожному вузлі
3. **StatefulSet** — Потребує стабільної ідентичності та сховища
4. **Деплоймент** — REST API без стану
5. **DaemonSet** — Агент моніторингу на кожному вузлі
6. **StatefulSet** — Розподілена система зі стабільною ідентичністю
7. **Деплоймент** — Проксі без стану (якщо не потрібен конкретний екземпляр)

</details>

---

## Наступний модуль

[Модуль 2.4: Jobs та CronJobs](module-2.4-jobs-cronjobs/) — Пакетні навантаження та заплановані завдання.
