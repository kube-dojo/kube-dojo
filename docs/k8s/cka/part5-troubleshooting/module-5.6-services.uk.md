# Модуль 5.6: Усунення несправностей Сервісів

> **Складність**: `[MEDIUM]` — Критично для доступності додатків
>
> **Час на виконання**: 45–55 хвилин
>
> **Передумови**: Модуль 5.5 (Усунення мережевих несправностей), Модуль 3.1–3.4 (Сервіси)

---

## Чому цей модуль важливий

Сервіси — це спосіб, яким додатки відкриваються в Kubernetes — і внутрішньо, і зовнішньо. Коли Сервіс не працює, додатки стають недоступними. Розуміння різних типів Сервісів та їхніх режимів збоїв є критичним для підтримки доступності додатків.

> **Аналогія з ресепшн**
>
> Kubernetes Сервіс — це як ресепшн. ClusterIP — це внутрішня стійка — тільки люди всередині будівлі можуть нею скористатися. NodePort відкриває вікно на вулицю. LoadBalancer встановлює цілком новий публічний вхід. Ingress — як лобі-директорія, що направляє людей до різних стійок залежно від їхнього запиту. Кожний має різні способи зламатися.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Усувати несправності ClusterIP Сервісів
- Виправляти проблеми доступності NodePort
- Діагностувати проблеми LoadBalancer
- Налагоджувати конфігурацію Ingress
- Визначати проблеми kube-proxy

---

## Чи знали ви?

- **IP Сервісів — віртуальні**: адреси ClusterIP не існують на жодному інтерфейсі — це просто правила в iptables/IPVS
- **Діапазон NodePort**: за замовчуванням 30000–32767. Можна змінити прапорцем API-сервера, але рідко потрібно
- **LoadBalancer включає NodePort**: Сервіси LoadBalancer автоматично отримують ClusterIP І NodePort
- **Headless-Сервіси не мають ClusterIP**: встановлення `clusterIP: None` повертає IP Підів безпосередньо в DNS

---

## Частина 1: Огляд архітектури Сервісів

### 1.1 Типи Сервісів

```
┌──────────────────────────────────────────────────────────────┐
│                     ТИПИ СЕРВІСІВ                             │
│                                                               │
│   ClusterIP (за замовчуванням)                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ Тільки внутрішній, віртуальний IP, без зовнішнього  │    │
│   │ доступу                                              │    │
│   └─────────────────────────────────────────────────────┘    │
│                            ▲                                  │
│                            │ Будується на                     │
│   NodePort                 │                                  │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ ClusterIP + порт на кожному вузлі (30000–32767)     │    │
│   └─────────────────────────────────────────────────────┘    │
│                            ▲                                  │
│                            │ Будується на                     │
│   LoadBalancer             │                                  │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ ClusterIP + NodePort + хмарний балансувальник        │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
│   ExternalName                                                │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ DNS CNAME запис, без проксі, тільки резолвінг імен  │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Роль kube-proxy

```
┌──────────────────────────────────────────────────────────────┐
│                    ФУНКЦІЯ KUBE-PROXY                         │
│                                                               │
│   Сервіс створено                                            │
│        │                                                      │
│        ▼                                                      │
│   kube-proxy спостерігає за API-сервером                     │
│        │                                                      │
│        ▼                                                      │
│   Програмує правила на кожному вузлі:                       │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ Режим iptables: правила iptables -t nat             │    │
│   │ Режим IPVS:    віртуальні сервери в ядрі            │    │
│   └─────────────────────────────────────────────────────┘    │
│        │                                                      │
│        ▼                                                      │
│   Трафік до ClusterIP → перенаправлення на IP Підів         │
│                                                               │
│   Якщо kube-proxy збоїть → Сервіси перестають працювати     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Частина 2: Усунення несправностей ClusterIP

### 2.1 Контрольний список ClusterIP

Коли ClusterIP Сервіс не працює:

```
┌──────────────────────────────────────────────────────────────┐
│            УСУНЕННЯ НЕСПРАВНОСТЕЙ CLUSTERIP                  │
│                                                               │
│   □ Сервіс існує і має правильні порти                      │
│   □ Endpoints існують (selector збігається з Під'ами)       │
│   □ Під'и в стані Ready                                     │
│   □ Target port збігається з портом контейнера              │
│   □ Під реально слухає на порту                             │
│   □ kube-proxy працює на вузлах                             │
│   □ NetworkPolicy не блокує трафік                          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Покрокова діагностика

```bash
# 1. Перевірити що Сервіс існує
k get svc my-service
k describe svc my-service

# 2. Перевірити endpoints (КРИТИЧНО)
k get endpoints my-service
# Немає endpoints = проблема з selector або readiness Підів

# 3. Перевірити що selector збігається з Під'ами
k get svc my-service -o jsonpath='{.spec.selector}'
# Порівняти з:
k get pods --show-labels

# 4. Перевірити що Під'и Ready
k get pods -l <selector>
# Усі повинні показувати Ready (напр., 1/1)

# 5. Перевірити що Під слухає на порту
k exec <pod> -- netstat -tlnp
# Або: k exec <pod> -- ss -tlnp

# 6. Тестувати напряму за IP Підів
k exec <client-pod> -- wget -qO- http://<pod-ip>:<container-port>
```

### 2.3 Типові проблеми ClusterIP

| Проблема | Симптом | Перевірте | Виправлення |
|----------|---------|-----------|-------------|
| Немає endpoints | Connection refused | `k get ep` | Виправити selector або мітки Підів |
| Неправильний targetPort | Тайм-аут/refused | Порівняти порт з контейнером | Виправити targetPort |
| Під не Ready | Відсутні endpoints | `k get pods` | Виправити readiness пробу |
| Додаток не слухає | Прямий доступ до Підів збоїть | `netstat` у контейнері | Виправити додаток |
| kube-proxy не працює | Усі Сервіси збоять | Під'и kube-proxy | Перезапустити kube-proxy |

### 2.4 Глибоке занурення в конфігурацію портів

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: myapp
  ports:
  - port: 80          # Порт для доступу клієнтів до Сервісу
    targetPort: 8080  # Порт на Підові/контейнері
    protocol: TCP     # TCP (за замовчуванням) або UDP
    name: http        # Необов'язкове ім'я
```

```bash
# Перевірити маппінг
k get svc my-service -o yaml | grep -A 5 ports:

# Перевірити що контейнер слухає на targetPort
k exec <pod> -- sh -c 'netstat -tlnp 2>/dev/null || ss -tlnp'
```

---

## Частина 3: Усунення несправностей NodePort

### 3.1 Контрольний список NodePort

```
┌──────────────────────────────────────────────────────────────┐
│             УСУНЕННЯ НЕСПРАВНОСТЕЙ NODEPORT                   │
│                                                               │
│   Усі перевірки ClusterIP, плюс:                             │
│                                                               │
│   □ NodePort у допустимому діапазоні (30000–32767)           │
│   □ Firewall вузла дозволяє порт                            │
│   □ Security group хмари дозволяє порт                      │
│   □ Вузол доступний на порту                                │
│   □ Тестування з правильним IP вузла                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Тестування NodePort

```bash
# Отримати значення NodePort
k get svc my-service -o jsonpath='{.spec.ports[0].nodePort}'

# Отримати IP вузлів
k get nodes -o wide

# Тест ззовні кластера
curl http://<node-ip>:<nodeport>

# Тест зсередини кластера (теж повинен працювати)
k exec <pod> -- wget -qO- http://<node-ip>:<nodeport>

# Тест усіх вузлів (NodePort працює на будь-якому вузлі)
for node_ip in $(k get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'); do
  curl -s --connect-timeout 2 http://${node_ip}:<nodeport> && echo "OK: $node_ip" || echo "FAIL: $node_ip"
done
```

### 3.3 Типові проблеми NodePort

| Проблема | Симптом | Перевірте | Виправлення |
|----------|---------|-----------|-------------|
| Firewall блокує | Тайм-аут ззовні | `iptables -L -n` | Відкрити порт у firewall |
| Cloud SG блокує | Тайм-аут ззовні | Хмарна консоль | Додати правило security group |
| Неправильний IP вузла | Connection refused | `k get nodes -o wide` | Використати правильний IP (internal vs external) |
| Конфлікт порту | Створення Сервісу збоїть | `netstat -tlnp` на вузлі | Використати інший nodePort |
| externalTrafficPolicy | Працює лише на деяких вузлах | Перевірити політику | Встановити Cluster або виправити endpoints |

### 3.4 externalTrafficPolicy

```yaml
spec:
  type: NodePort
  externalTrafficPolicy: Local  # Відповідають лише вузли з Під'ами
  # проти
  externalTrafficPolicy: Cluster  # Усі вузли відповідають (за замовчуванням)
```

```bash
# Перевірити поточну політику
k get svc my-service -o jsonpath='{.spec.externalTrafficPolicy}'

# З політикою Local перевірте на яких вузлах є Під'и
k get pods -l <selector> -o wide
# Тільки ці IP вузлів відповідатимуть на NodePort
```

---

## Частина 4: Усунення несправностей LoadBalancer

### 4.1 Вимоги LoadBalancer

```
┌──────────────────────────────────────────────────────────────┐
│               ВИМОГИ LOADBALANCER                            │
│                                                               │
│   Хмарне середовище:                                         │
│   • Cloud controller manager працює                         │
│   • Правильні хмарні облікові дані налаштовані              │
│   • Хмарний провайдер підтримує LoadBalancer                │
│                                                               │
│   On-premises:                                                │
│   • MetalLB або подібне рішення встановлено                 │
│   • Пул IP-адрес налаштований                               │
│                                                               │
│   Без цього → LoadBalancer залишається Pending назавжди     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Перевірка статусу LoadBalancer

```bash
# Перевірити чи зовнішній IP призначено
k get svc my-service
# Стовпець EXTERNAL-IP повинен показувати IP, а не <pending>

# Отримати детальний статус
k describe svc my-service

# Перевірити події на помилки
k get events --field-selector involvedObject.name=my-service

# Тестувати IP LoadBalancer
curl http://<external-ip>:<port>
```

### 4.3 Типові проблеми LoadBalancer

| Проблема | Симптом | Перевірте | Виправлення |
|----------|---------|-----------|-------------|
| Немає cloud controller | Залишається Pending | Check cloud-controller-manager | Встановити/налаштувати CCM |
| Квота перевищена | Залишається Pending | Хмарна консоль | Запросити збільшення квоти |
| Неправильні анотації | LB неправильно налаштований | Анотації Сервісу | Виправити хмарні анотації |
| Security group | Не можна дістатись LB | Хмарні правила безпеки | Відкрити порти LB |
| MetalLB не встановлений | Залишається Pending (bare metal) | Під'и MetalLB | Встановити MetalLB |

### 4.4 Налагодження LoadBalancer у хмарі

```bash
# Для AWS
k describe svc my-service | grep "LoadBalancer Ingress"
aws elb describe-load-balancers

# Для GCP
k describe svc my-service
gcloud compute forwarding-rules list

# Перевірити логи cloud controller manager
k -n kube-system logs -l component=cloud-controller-manager
```

---

## Частина 5: Усунення несправностей Ingress

### 5.1 Архітектура Ingress

```
┌──────────────────────────────────────────────────────────────┐
│                     ПОТІК INGRESS                             │
│                                                               │
│   Зовнішній запит                                            │
│        │                                                      │
│        ▼                                                      │
│   Ingress Controller (nginx, traefik тощо)                   │
│        │                                                      │
│        │ Читає ресурси Ingress                               │
│        ▼                                                      │
│   Зіставляє правила host/path                                │
│        │                                                      │
│        ▼                                                      │
│   Маршрутизує до бекенд-Сервісу                             │
│        │                                                      │
│        ▼                                                      │
│   Під                                                        │
│                                                               │
│   Ingress Controller відсутній → правила Ingress не діють   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Кроки усунення несправностей Ingress

```bash
# 1. Перевірити що Ingress Controller працює
k -n ingress-nginx get pods  # Для nginx-ingress
# Або перевірте namespace вашого конкретного ingress controller

# 2. Перевірити що ресурс Ingress існує
k get ingress my-ingress
k describe ingress my-ingress

# 3. Перевірити наявність бекенд-Сервісу
k get svc <backend-service>

# 4. Перевірити події Ingress
k describe ingress my-ingress | grep -A 10 Events

# 5. Перевірити логи Ingress Controller
k -n ingress-nginx logs -l app.kubernetes.io/name=ingress-nginx

# 6. Тестувати з правильним заголовком Host
curl -H "Host: myapp.example.com" http://<ingress-ip>
```

### 5.3 Типові проблеми Ingress

| Проблема | Симптом | Перевірте | Виправлення |
|----------|---------|-----------|-------------|
| Немає Ingress Controller | 404 або нічого | Під'и контролера | Встановити Ingress Controller |
| Неправильний ingressClassName | Правила ігноруються | `spec.ingressClassName` | Зіставити клас контролера |
| Бекенд-Сервіс відсутній | Помилка 503 | `k get svc` | Створити бекенд-Сервіс |
| Відсутній TLS secret | Помилки TLS | `k get secret` | Створити TLS secret |
| Неправильний заголовок host | 404 | Тест з прапорцем -H | Використати правильне ім'я хосту |
| Неспівпадіння типу path | 404 на підшляхах | Перевірити pathType | Використати Prefix або Exact |

### 5.4 Типи шляхів Ingress

```yaml
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix   # /api, /api/, /api/v1 — усі збігаються
      - path: /exact
        pathType: Exact    # Збігається лише /exact
      - path: /
        pathType: Prefix   # Перехоплює все
```

### 5.5 Тестування Ingress

```bash
# Отримати IP/hostname Ingress
k get ingress my-ingress

# Тест із конкретним заголовком host
curl -v -H "Host: myapp.example.com" http://<ingress-ip>/path

# Тест TLS
curl -v -H "Host: myapp.example.com" https://<ingress-ip>/path -k

# Перевірити конфігурацію Ingress Controller (nginx)
k -n ingress-nginx exec <controller-pod> -- cat /etc/nginx/nginx.conf | grep -A 20 "server_name myapp"
```

---

## Частина 6: Усунення несправностей kube-proxy

### 6.1 Режими kube-proxy

```
┌──────────────────────────────────────────────────────────────┐
│                   РЕЖИМИ KUBE-PROXY                           │
│                                                               │
│   Режим iptables (за замовчуванням)                          │
│   • Використовує правила iptables для маршрутизації          │
│   • Добре для < 1000 Сервісів                                │
│   • Перевірка: iptables -t nat -L                            │
│                                                               │
│   Режим IPVS                                                  │
│   • Використовує ядерний IPVS для балансування               │
│   • Краще для великої кількості Сервісів                     │
│   • Перевірка: ipvsadm -Ln                                   │
│                                                               │
│   Якщо kube-proxy збоїть → маршрутизація Сервісів ламається │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Перевірка kube-proxy

```bash
# Перевірити Під'и kube-proxy
k -n kube-system get pods -l k8s-app=kube-proxy

# Перевірити логи kube-proxy
k -n kube-system logs -l k8s-app=kube-proxy

# Перевірити конфігурацію kube-proxy
k -n kube-system get configmap kube-proxy -o yaml

# Перевірити правила iptables (на вузлі)
sudo iptables -t nat -L KUBE-SERVICES | head -20

# Перевірити IPVS (якщо використовується режим IPVS)
sudo ipvsadm -Ln
```

### 6.3 Типові проблеми kube-proxy

| Проблема | Симптом | Перевірте | Виправлення |
|----------|---------|-----------|-------------|
| Не працює | Усі Сервіси збоять | Перевірити Під'и | Перезапустити DaemonSet |
| Неправильний режим | Неочікувана поведінка | ConfigMap | Переналаштувати режим |
| Застарілі правила | Зміни Сервісів не відображаються | iptables на вузлі | Перезапустити kube-proxy |
| conntrack заповнений | Випадкові розриви з'єднань | dmesg для conntrack | Збільшити ліміт conntrack |

### 6.4 Виправлення kube-proxy

```bash
# Перезапустити Під'и kube-proxy
k -n kube-system rollout restart daemonset kube-proxy

# Перевірити помилки в логах
k -n kube-system logs -l k8s-app=kube-proxy --since=5m | grep -i error

# Перевірити що правила iptables існують для Сервісу
sudo iptables -t nat -L KUBE-SERVICES | grep <service-cluster-ip>

# Примусова синхронізація (видалити і дозволити kube-proxy перестворити)
# Це деструктивно — використовуйте обережно
k -n kube-system delete pod -l k8s-app=kube-proxy
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Не перевіряти endpoints першими | Пропуск справжньої проблеми | Завжди починайте з `k get endpoints` |
| Плутанина port vs targetPort | Неправильна конфігурація портів | port=доступ до Сервісу, targetPort=контейнер |
| Тестування NodePort з неправильного IP | З'єднання не працює | Використовуйте IP вузла, а не IP Підів |
| Відсутній Ingress Controller | Правила Ingress ігноруються | Перевірте що контролер встановлений |
| Неправильний ingressClassName | Правила не підхоплюються | Зіставте ім'я класу контролера |
| Ігнорування kube-proxy | Звинувачення додатку або мережі | Перевірте Під'и та логи kube-proxy |

---

## Тест

### Q1: Сервіс без endpoints
`k get svc nginx` показує ClusterIP, але `k get endpoints nginx` показує `<none>`. Що не так?

<details>
<summary>Відповідь</summary>

Selector Сервісу не збігається з жодними **Ready** Під'ами. Або:
1. Немає Підів з відповідними мітками
2. Під'и є, але не Ready (не пройшли readiness пробу)
3. Selector у Сервісі неправильний

Налагодження:
```bash
k get svc nginx -o jsonpath='{.spec.selector}'
k get pods --show-labels | grep <expected-labels>
```

</details>

### Q2: NodePort не працює
Створено Сервіс NodePort. `curl http://node:30080` не відповідає ззовні, але працює зсередини кластера. Чому?

<details>
<summary>Відповідь</summary>

**Firewall або security group** блокує NodePort від зовнішнього доступу. Перевірте:
- iptables вузла: `sudo iptables -L INPUT`
- Cloud security groups (AWS, GCP, Azure)
- Network ACL

NodePort вимагає щоб порт був відкритий на всіх вузлах з мережі-джерела.

</details>

### Q3: LoadBalancer у Pending
Сервіс типу LoadBalancer залишається `<pending>` для EXTERNAL-IP. Що ви перевіряєте?

<details>
<summary>Відповідь</summary>

Перевірте чи cloud controller manager працює та налаштований:
```bash
k -n kube-system get pods | grep cloud-controller
k get events --field-selector involvedObject.name=<service>
```

Якщо on-premises/bare-metal — потрібен MetalLB або подібне:
```bash
k -n metallb-system get pods
```

Немає хмарної інтеграції = LoadBalancer залишається pending.

</details>

### Q4: Ingress 404
Ingress налаштований, але всі запити повертають 404. Що перевірити першим?

<details>
<summary>Відповідь</summary>

Перевірте чи **Ingress Controller встановлений** і Ingress має правильний **ingressClassName**:

```bash
# Перевірити ingress controller
k get pods -A | grep -i ingress

# Перевірити клас Ingress
k get ingress <name> -o yaml | grep ingressClassName

# Переглянути доступні класи
k get ingressclass
```

Без Ingress Controller ресурси Ingress не діють.

</details>

### Q5: Port vs TargetPort
Сервіс має `port: 80, targetPort: 3000`. Контейнер працює на порту 80. Чи працюватиме це?

<details>
<summary>Відповідь</summary>

**Ні.** Трафік досягає Сервісу на порту 80, але перенаправляється на порт контейнера 3000, де нічого не слухає.

Виправте один з варіантів:
1. Змініть `targetPort: 80` щоб збігався з контейнером
2. Змініть контейнер слухати на 3000

</details>

### Q6: Режим kube-proxy
Як перевірити в якому режимі працює kube-proxy?

<details>
<summary>Відповідь</summary>

```bash
# Перевірити ConfigMap
k -n kube-system get configmap kube-proxy -o yaml | grep mode

# Або перевірити логи Підів
k -n kube-system logs -l k8s-app=kube-proxy | grep "Using"

# Типові режими: iptables (за замовчуванням), ipvs
```

</details>

---

## Практична вправа: Сценарії усунення несправностей Сервісів

### Сценарій

Практика діагностики та виправлення проблем Сервісів.

### Підготовка

```bash
# Створити тестовий namespace
k create ns service-lab

# Створити Деплоймент
cat <<EOF | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: service-lab
spec:
  replicas: 2
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
        image: nginx:1.25
        ports:
        - containerPort: 80
EOF
```

### Завдання 1: Створення та тестування ClusterIP Сервісу

```bash
# Створити Сервіс
k -n service-lab expose deployment web --port=80

# Створити тестовий Під
k -n service-lab run client --image=busybox:1.36 --command -- sleep 3600

# Тестувати з'єднання
k -n service-lab exec client -- wget -qO- http://web

# Перевірити endpoints
k -n service-lab get endpoints web
```

### Завдання 2: Симуляція неспівпадіння selector

```bash
# Зламати Сервіс
k -n service-lab patch svc web -p '{"spec":{"selector":{"app":"broken"}}}'

# Тест (повинен збоїти)
k -n service-lab exec client -- wget -qO- --timeout=2 http://web

# Перевірити endpoints (повинні бути порожні)
k -n service-lab get endpoints web

# Діагностика
k -n service-lab get svc web -o jsonpath='{.spec.selector}'
k -n service-lab get pods --show-labels

# Виправлення
k -n service-lab patch svc web -p '{"spec":{"selector":{"app":"web"}}}'

# Перевірка
k -n service-lab get endpoints web
k -n service-lab exec client -- wget -qO- --timeout=2 http://web
```

### Завдання 3: Створення NodePort Сервісу

```bash
# Створити NodePort Сервіс
k -n service-lab expose deployment web --type=NodePort --name=web-nodeport --port=80

# Отримати NodePort
k -n service-lab get svc web-nodeport

# Отримати IP вузла
k get nodes -o wide

# Тест зсередини кластера
k -n service-lab exec client -- wget -qO- --timeout=2 http://<node-ip>:<nodeport>
```

### Завдання 4: Неправильна конфігурація портів

```bash
# Створити Сервіс з неправильним targetPort
cat <<EOF | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: wrong-port
  namespace: service-lab
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080  # Неправильно! nginx слухає на 80
EOF

# Тест (повинен збоїти)
k -n service-lab exec client -- wget -qO- --timeout=2 http://wrong-port

# Діагностика
k -n service-lab get endpoints wrong-port  # Має endpoints
k -n service-lab exec client -- wget -qO- --timeout=2 http://<pod-ip>:80  # Працює
k -n service-lab exec client -- wget -qO- --timeout=2 http://<pod-ip>:8080  # Збоїть

# Виправлення
k -n service-lab patch svc wrong-port -p '{"spec":{"ports":[{"port":80,"targetPort":80}]}}'

# Перевірка
k -n service-lab exec client -- wget -qO- --timeout=2 http://wrong-port
```

### Критерії успіху

- [ ] Створили та протестували ClusterIP Сервіс
- [ ] Визначили та виправили неспівпадіння selector
- [ ] Створили та протестували NodePort Сервіс
- [ ] Діагностували та виправили неправильний targetPort

### Очищення

```bash
k delete ns service-lab
```

---

## Практичні вправи

### Вправа 1: Перевірка деталей Сервісу (30 с)
```bash
# Завдання: Переглянути конфігурацію Сервісу
k get svc <service> -o yaml
```

### Вправа 2: Перевірка endpoints (30 с)
```bash
# Завдання: Перелічити endpoints Сервісу
k get endpoints <service>
k describe endpoints <service>
```

### Вправа 3: Отримати значення NodePort (30 с)
```bash
# Завдання: Знайти NodePort Сервісу
k get svc <service> -o jsonpath='{.spec.ports[0].nodePort}'
```

### Вправа 4: Тест з'єднання Сервісу (1 хв)
```bash
# Завдання: Тест HTTP до Сервісу
k exec <pod> -- wget -qO- --timeout=2 http://<service>
```

### Вправа 5: Виправлення неспівпадіння selector (2 хв)
```bash
# Завдання: Оновити selector Сервісу
k patch svc <service> -p '{"spec":{"selector":{"app":"correct-label"}}}'
```

### Вправа 6: Перевірка Ingress Controller (1 хв)
```bash
# Завдання: Перевірити що Ingress Controller працює
k get pods -A | grep -i ingress
k get ingressclass
```

### Вправа 7: Перевірка kube-proxy (1 хв)
```bash
# Завдання: Перевірити статус kube-proxy
k -n kube-system get pods -l k8s-app=kube-proxy
k -n kube-system logs -l k8s-app=kube-proxy --tail=20
```

### Вправа 8: Тест Ingress із заголовком Host (1 хв)
```bash
# Завдання: Тестувати правило Ingress
curl -H "Host: <hostname>" http://<ingress-ip>
```

---

## Наступний модуль

Переходьте до [Модуль 5.7: Логування та моніторинг](module-5.7-logging-monitoring.uk.md), щоб навчитися використовувати логи та метрики для усунення несправностей.
