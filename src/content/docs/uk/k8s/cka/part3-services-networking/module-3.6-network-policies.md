---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 3.6: \u041c\u0435\u0440\u0435\u0436\u0435\u0432\u0456 \u043f\u043e\u043b\u0456\u0442\u0438\u043a\u0438"
slug: uk/k8s/cka/part3-services-networking/module-3.6-network-policies
sidebar: 
  order: 7
lab: 
  id: cka-3.6-network-policies
  url: https://killercoda.com/kubedojo/scenario/cka-3.6-network-policies
  duration: "45 min"
  difficulty: advanced
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — файрволінг на рівні Подів
>
> **Час на виконання**: 45–55 хвилин
>
> **Передумови**: Модуль 3.1 (Сервіси), Модуль 2.1 (Поди)

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Написати** ресурси NetworkPolicy, що обмежують ingress та egress трафік між подами
- **Дебажити** з'єднання, заблоковані NetworkPolicies, використовуючи систематичний аналіз міток та селекторів
- **Спроєктувати** стратегію мережевої сегментації для багаторівневого застосунку (frontend, backend, база даних)
- **Пояснити** патерн default-deny та чому явні правила дозволу безпечніші за чорні списки

---

## Чому цей модуль важливий

За замовчуванням Kubernetes дозволяє всім Подам спілкуватися з усіма іншими Подами — це **пласка мережа** без обмежень. Мережеві політики дозволяють контролювати цей трафік, реалізуючи **мікросегментацію** для безпеки. Без мережевих політик скомпрометований Під може вільно спілкуватися з кожним іншим Подом у кластері.

Іспит CKA часто перевіряє мережеві політики. Вам потрібно буде створювати правила ingress/egress, розуміти селектори та швидко діагностувати проблеми з політиками.

> **Аналогія з багатоквартирним будинком**
>
> Уявіть кластер Kubernetes як багатоквартирний будинок, де всі двері квартир незамкнені. Будь-який мешканець може зайти до будь-якої іншої квартири. Мережеві політики — це як встановлення замків на двері та видача ключів лише конкретним людям. Ви вирішуєте, хто може увійти (ingress) і куди мешканці можуть ходити (egress).

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Розуміти, коли Поди ізольовані мережевими політиками
- Створювати правила ingress та egress
- Використовувати селектори Подів, просторів імен та IP-блоків
- Правильно дозволяти DNS-трафік
- Діагностувати проблеми з мережевими політиками

---

## Чи знали ви?

- **NetworkPolicy — це лише специфікація**: API-сервер приймає обʼєкти NetworkPolicy, але без CNI, який їх підтримує (наприклад, Calico, Cilium або Weave), вони ігноруються.

- **Заборона за замовчуванням — потужна штука**: Одна-єдина політика "заборонити все" миттєво блокує весь трафік до обраних Подів. Це поширений шаблон безпеки.

- **Порядок не має значення**: На відміну від традиційних файрволів, правила NetworkPolicy є адитивними. Якщо будь-яка політика дозволяє трафік — він дозволений. Правила "заборонити" не існує — лише відсутність "дозволити".

---

## Частина 1: Основи мережевих політик

### 1.1 Як працюють мережеві політики

```
┌────────────────────────────────────────────────────────────────┐
│                   Потік мережевої політики                        │
│                                                                 │
│   Без NetworkPolicy:                                            │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Усі Поди можуть спілкуватися з усіма (пласка мережа) │  │
│   │                                                          │  │
│   │  Під A ◄────────────────────────────► Під B             │  │
│   │    │                                    │               │  │
│   │    │◄──────────────────────────────────►│               │  │
│   │    │            Під C                   │               │  │
│   │    └──────────────────────────────────────►Під D        │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   З NetworkPolicy, що обирає Під B:                             │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Під B тепер ізольований (дозволено лише явний трафік)  │  │
│   │                                                          │  │
│   │  Під A ────────────────────────────X──► Під B           │  │
│   │    │                                    │               │  │
│   │    │◄──────────────────────────────────►│               │  │
│   │    │            Під C                   │               │  │
│   │    └──────────────────────────────────────►Під D        │  │
│   │                                                          │  │
│   │  (Ingress Поду B заблоковано, якщо явно не дозволено)   │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Ключові концепції

| Концепція | Опис |
|-----------|------|
| **Ingress** | Трафік, що ВХОДИТЬ до Поду |
| **Egress** | Трафік, що ВИХОДИТЬ з Поду |
| **podSelector** | Які Поди підпадають під політику |
| **Ізольовані Поди** | Поди, обрані будь-якою NetworkPolicy |
| **Адитивні правила** | Кілька політик = обʼєднання всіх правил |

### 1.3 Коли Поди ізольовані?

Під ізольований, коли:
1. NetworkPolicy обирає його (через `spec.podSelector`)
2. Тип політики відповідає напрямку трафіку (ingress/egress)

Після ізоляції:
- **Ізольований за ingress**: Дозволений лише трафік, явно дозволений правилами ingress
- **Ізольований за egress**: Дозволений лише трафік, явно дозволений правилами egress

```yaml
# Ця політика робить Поди з app=web ізольованими за INGRESS
# (вони все ще можуть створювати вихідні зʼєднання)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-ingress
spec:
  podSelector:
    matchLabels:
      app: web         # Обирає ці Поди
  policyTypes:
  - Ingress            # Впливає лише на ingress
```

---

## Частина 2: Базові мережеві політики

### 2.1 Заборонити весь Ingress (заборона за замовчуванням)

```yaml
# Заборонити весь вхідний трафік до Подів у просторі імен
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: production
spec:
  podSelector: {}        # Порожній = обрати ВСІ Поди
  policyTypes:
  - Ingress              # Без правил ingress = заборонити весь ingress
```

### 2.2 Заборонити весь Egress

```yaml
# Заборонити весь вихідний трафік з Подів у просторі імен
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-egress
  namespace: production
spec:
  podSelector: {}        # Усі Поди
  policyTypes:
  - Egress               # Без правил egress = заборонити весь egress
```

### 2.3 Заборонити все (обидва напрямки)

```yaml
# Повна блокіровка
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### 2.4 Дозволити весь Ingress

```yaml
# Явно дозволити весь ingress (корисно для перевизначення політик заборони)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - {}                   # Порожнє правило = дозволити все
```

### 2.5 Дозволити весь Egress

```yaml
# Явно дозволити весь egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - {}                   # Порожнє правило = дозволити все
```

---

## Частина 3: Селективні політики

### 3.1 Дозволити Ingress від конкретних Подів

```yaml
# Дозволити трафік від Подів з міткою app=frontend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
spec:
  podSelector:
    matchLabels:
      app: backend         # Ця політика застосовується до Подів backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend    # Дозволити трафік від Подів frontend
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Приклад селектора Подів                        │
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────┐             │
│   │  Під            │         │  Під            │             │
│   │  app: frontend  │────────►│  app: backend   │             │
│   │                 │    ✓    │                 │             │
│   └─────────────────┘         └─────────────────┘             │
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────┐             │
│   │  Під            │         │  Під            │             │
│   │  app: other     │────X───►│  app: backend   │             │
│   │                 │    ✗    │                 │             │
│   └─────────────────┘         └─────────────────┘             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Дозволити Ingress з простору імен

```yaml
# Дозволити трафік від усіх Подів у просторі імен "monitoring"
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring    # Простір імен повинен мати цю мітку
```

> **Важливо**: Простори імен потребують міток! Додайте їх за допомогою:
> ```bash
> k label namespace monitoring name=monitoring
> ```

### 3.3 Дозволити Ingress з IP-блоку

```yaml
# Дозволити трафік з конкретних діапазонів IP
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 192.168.1.0/24      # Дозволити цей діапазон
        except:
        - 192.168.1.100/32        # Окрім цієї IP-адреси
```

### 3.4 Дозволити Ingress на конкретних портах

```yaml
# Дозволити лише HTTP та HTTPS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-ports
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}            # Від будь-якого Поду
    ports:
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
```

---

## Частина 4: Комбінування селекторів

### 4.1 Логіка AND проти OR

```yaml
# Логіка OR: від Подів frontend АБО з простору імен monitoring
ingress:
- from:
  - podSelector:
      matchLabels:
        app: frontend
- from:
  - namespaceSelector:
      matchLabels:
        name: monitoring
```

```yaml
# Логіка AND: від Подів frontend У просторі імен monitoring
ingress:
- from:
  - podSelector:
      matchLabels:
        app: frontend
    namespaceSelector:
      matchLabels:
        name: monitoring
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Логіка селекторів                              │
│                                                                 │
│   Два окремих елементи "from" = OR                              │
│   - from:                                                       │
│     - podSelector: {app: A}     # Збіг з A                     │
│   - from:                                                       │
│     - podSelector: {app: B}     # АБО збіг з B                 │
│                                                                 │
│   Один елемент "from" = AND                                     │
│   - from:                                                       │
│     - podSelector: {app: A}     # Збіг з A                     │
│       namespaceSelector: {x: y}  # І в просторі імен з x=y     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Складний приклад

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: complex-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Правило 1: Дозволити від frontend у тому ж просторі імен
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8080
  # Правило 2: Дозволити від будь-якого Поду в просторі імен monitoring
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - port: 9090
  egress:
  # Правило 1: Дозволити до Подів database
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
  # Правило 2: Дозволити DNS
  - to:
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

---

## Частина 5: Політики Egress

### 5.1 Дозволити Egress до конкретних Подів

```yaml
# Backend може спілкуватися лише з database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
```

### 5.2 Дозволити DNS (критично!)

При обмеженні egress необхідно дозволити DNS, інакше Поди не зможуть розвʼязувати імена сервісів:

```yaml
# Дозволити DNS до kube-system
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

### 5.3 Дозволити зовнішній трафік

```yaml
# Дозволити egress до зовнішніх IP
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0        # Усі IP
        except:
        - 10.0.0.0/8           # Окрім приватних діапазонів
        - 172.16.0.0/12
        - 192.168.0.0/16
```

---

## Частина 6: Діагностика мережевих політик

### 6.1 Послідовність діагностики

```
Проблема з мережевою політикою?
    │
    ├── Чи підтримує CNI NetworkPolicy?
    │   (Calico, Cilium, Weave = так; Flannel = ні)
    │
    ├── kubectl get networkpolicy -n <namespace>
    │   (Список політик, що впливають на Поди)
    │
    ├── kubectl describe networkpolicy <name>
    │   (Перевірити селектори та правила)
    │
    ├── Перевірити відповідність міток Подів
    │   kubectl get pods --show-labels
    │
    ├── Перевірити мітки просторів імен (для namespaceSelector)
    │   kubectl get namespace --show-labels
    │
    └── Перевірити зʼєднання
        kubectl exec <pod> -- nc -zv <target> <port>
```

### 6.2 Корисні команди

```bash
# Список мережевих політик
k get networkpolicy
k get netpol                 # Скорочена форма

# Опис політики
k describe networkpolicy <name>

# Перевірити мітки Подів
k get pods --show-labels

# Перевірити мітки просторів імен
k get namespaces --show-labels

# Перевірити зʼєднання
k exec <pod> -- nc -zv <service> <port>
k exec <pod> -- wget --spider --timeout=1 http://<service>
k exec <pod> -- curl -s --max-time 1 http://<service>
```

### 6.3 Типові проблеми

| Симптом | Причина | Рішення |
|---------|---------|---------|
| Політика не застосовується | CNI не підтримує | Використовуйте Calico, Cilium або Weave |
| Не вдається розвʼязати DNS | Egress DNS заблоковано | Додайте правило egress для порту 53 |
| Міжпросторовий трафік заблоковано | namespaceSelector некоректний | Додайте мітки до просторів імен, перевірте селектор |
| Весь трафік заблоковано | Порожній podSelector у забороні | Створіть правила дозволу для потрібного трафіку |
| Поди все ще спілкуються | Мітки не збігаються | Перевірте відповідність podSelector міткам Подів |

---

## Частина 7: Поширені шаблони

### 7.1 Захист бази даних

```yaml
# Дозволити лише Подам backend доступ до бази даних
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-protection
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - port: 5432
```

### 7.2 Трирівневий застосунок

```yaml
# Веб-рівень — лише від ingress-контролера
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-policy
spec:
  podSelector:
    matchLabels:
      tier: web
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  policyTypes:
  - Ingress
---
# Рівень застосунку — лише від веб-рівня
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-policy
spec:
  podSelector:
    matchLabels:
      tier: app
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: web
  policyTypes:
  - Ingress
---
# Рівень БД — лише від рівня застосунку
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
spec:
  podSelector:
    matchLabels:
      tier: db
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: app
    ports:
    - port: 5432
  policyTypes:
  - Ingress
```

### 7.3 Ізоляція простору імен

```yaml
# Заборонити все за замовчуванням, потім дозволити лише в межах простору імен
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: namespace-isolation
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}      # Лише той самий простір імен
  egress:
  - to:
    - podSelector: {}      # Лише той самий простір імен
  - to:                    # Плюс DNS
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
```

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Використання непідтримуваного CNI | Політики ігноруються | Перейдіть на Calico, Cilium або Weave |
| Забули дозволити DNS egress | Поди не можуть розвʼязувати імена | Додайте egress для порту 53 UDP/TCP |
| Простори імен без міток | namespaceSelector не спрацьовує | Спочатку додайте мітки до просторів імен |
| Неправильна логіка селекторів | Занадто дозвільно/обмежувально | Перевірте AND проти OR (один from чи окремі) |
| Порожній масив ingress | Блокує весь ingress | Використовуйте `ingress: [{}]` для дозволу всього |

---

## Тест

1. **Що відбувається, коли NetworkPolicy обирає Під?**
   <details>
   <summary>Відповідь</summary>
   Під стає "ізольованим" для зазначених типів політики (Ingress/Egress). Трафік, який явно не дозволено правилами, забороняється.
   </details>

2. **Як заборонити весь вхідний трафік до Подів у просторі імен?**
   <details>
   <summary>Відповідь</summary>
   Створіть NetworkPolicy з порожнім `podSelector: {}` (обирає всі Поди), `policyTypes: [Ingress]` та без правил `ingress`.
   </details>

3. **Яка різниця між цими двома правилами ingress?**
   ```yaml
   # Версія A
   ingress:
   - from:
     - podSelector: {matchLabels: {app: a}}
     - namespaceSelector: {matchLabels: {name: x}}

   # Версія B
   ingress:
   - from:
     - podSelector: {matchLabels: {app: a}}
       namespaceSelector: {matchLabels: {name: x}}
   ```
   <details>
   <summary>Відповідь</summary>
   Версія A використовує логіку OR: дозволяє від Подів з `app=a` АБО від будь-якого Поду в просторі імен з `name=x`.
   Версія B використовує логіку AND: дозволяє лише від Подів з `app=a`, які також знаходяться в просторі імен з `name=x`.
   </details>

4. **Чому дозвіл DNS egress є важливим?**
   <details>
   <summary>Відповідь</summary>
   Подам потрібен DNS для розвʼязання імен сервісів. Без egress на порт 53 Поди не можуть знайти `my-service.default.svc.cluster.local`, що порушує виявлення сервісів.
   </details>

5. **NetworkPolicy створено, але трафік не блокується. Що не так?**
   <details>
   <summary>Відповідь</summary>
   Найімовірніше, плагін CNI не підтримує NetworkPolicy. Flannel, наприклад, не застосовує NetworkPolicy. Використовуйте Calico, Cilium або Weave.
   </details>

---

## Практична вправа

**Завдання**: Реалізувати мережеві політики для трирівневого застосунку.

**Кроки**:

1. **Створіть тестові Поди**:
```bash
# Створіть Поди з різними ролями
k run frontend --image=nginx --labels="tier=frontend"
k run backend --image=nginx --labels="tier=backend"
k run database --image=nginx --labels="tier=database"

# Зачекайте, поки Поди будуть готові
k wait --for=condition=ready pod/frontend pod/backend pod/database --timeout=60s
```

2. **Перевірте стандартну звʼязність** (все має працювати):
```bash
BACKEND_IP=$(k get pod backend -o jsonpath='{.status.podIP}')
k exec frontend -- wget --spider --timeout=1 http://$BACKEND_IP
# Має спрацювати
```

3. **Створіть політику заборони всього**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF
```

4. **Перевірте звʼязність** (має не спрацювати, якщо CNI підтримує):
```bash
k exec frontend -- wget --spider --timeout=1 http://$BACKEND_IP
# Має завершитися таймаутом (якщо CNI підтримує NetworkPolicy)
```

5. **Дозвольте frontend до backend**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - port: 80
EOF
```

6. **Перевірте знову**:
```bash
k exec frontend -- wget --spider --timeout=1 http://$BACKEND_IP
# Тепер має спрацювати

# Але database до backend все ще має бути заблоковано
DATABASE_IP=$(k get pod database -o jsonpath='{.status.podIP}')
k exec database -- wget --spider --timeout=1 http://$BACKEND_IP
# Має не спрацювати
```

7. **Дозвольте backend до database**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-database
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - port: 80
EOF
```

8. **Перелічіть усі політики**:
```bash
k get networkpolicy
k describe networkpolicy
```

9. **Очищення**:
```bash
k delete networkpolicy deny-all allow-frontend-to-backend allow-backend-to-database
k delete pod frontend backend database
```

**Критерії успіху**:
- [ ] Розуміння поведінки "дозволити все" без політик
- [ ] Вміння створювати політики заборони всього
- [ ] Вміння створювати селективні політики дозволу
- [ ] Розуміння відповідності селекторів Подів
- [ ] Вміння діагностувати проблеми з політиками

---

## Практичні вправи

### Вправа 1: Заборонити весь Ingress (Ціль: 2 хвилини)

```bash
# Створіть Під
k run test-pod --image=nginx --labels="app=test"

# Створіть заборону всього ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-ingress
spec:
  podSelector:
    matchLabels:
      app: test
  policyTypes:
  - Ingress
EOF

# Перевірте
k describe networkpolicy deny-ingress

# Очищення
k delete networkpolicy deny-ingress
k delete pod test-pod
```

### Вправа 2: Дозволити від конкретного Поду (Ціль: 3 хвилини)

```bash
# Створіть Поди
k run server --image=nginx --labels="role=server"
k run client --image=nginx --labels="role=client"
k run other --image=nginx --labels="role=other"

# Створіть політику, що дозволяє лише client
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-client
spec:
  podSelector:
    matchLabels:
      role: server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: client
    ports:
    - port: 80
EOF

# Перевірте політику
k describe networkpolicy allow-client

# Очищення
k delete networkpolicy allow-client
k delete pod server client other
```

### Вправа 3: Дозволити з простору імен (Ціль: 4 хвилини)

```bash
# Створіть простір імен з міткою
k create namespace allowed
k label namespace allowed name=allowed

# Створіть Поди
k run target --image=nginx --labels="app=target"
k run source --image=nginx -n allowed

# Створіть політику
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-namespace
spec:
  podSelector:
    matchLabels:
      app: target
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: allowed
EOF

# Перевірте
k describe networkpolicy allow-namespace

# Очищення
k delete networkpolicy allow-namespace
k delete pod target
k delete namespace allowed
```

### Вправа 4: Egress з DNS (Ціль: 4 хвилини)

```bash
# Створіть Під
k run egress-test --image=nginx --labels="app=egress"

# Створіть політику egress з DNS
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: egress-dns
spec:
  podSelector:
    matchLabels:
      app: egress
  policyTypes:
  - Egress
  egress:
  # Дозволити DNS
  - to:
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
  # Дозволити HTTPS
  - to: []
    ports:
    - port: 443
EOF

# Перевірте
k describe networkpolicy egress-dns

# Очищення
k delete networkpolicy egress-dns
k delete pod egress-test
```

### Вправа 5: Ingress на конкретних портах (Ціль: 3 хвилини)

```bash
# Створіть Під
k run web --image=nginx --labels="app=web"

# Дозволити лише порти 80 та 443
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-ports
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - ports:
    - port: 80
      protocol: TCP
    - port: 443
      protocol: TCP
EOF

# Перевірте
k describe networkpolicy web-ports

# Очищення
k delete networkpolicy web-ports
k delete pod web
```

### Вправа 6: Політика IP-блоку (Ціль: 3 хвилини)

```bash
# Створіть Під
k run ip-test --image=nginx --labels="app=ip-test"

# Створіть політику з IP-блоком
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ip-block
spec:
  podSelector:
    matchLabels:
      app: ip-test
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24
EOF

# Перевірте
k describe networkpolicy ip-block

# Очищення
k delete networkpolicy ip-block
k delete pod ip-test
```

### Вправа 7: Комбінований селектор AND (Ціль: 4 хвилини)

```bash
# Створіть простір імен
k create namespace restricted
k label namespace restricted name=restricted

# Створіть Під
k run secure --image=nginx --labels="app=secure"

# Створіть політику з логікою AND
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: and-policy
spec:
  podSelector:
    matchLabels:
      app: secure
  policyTypes:
  - Ingress
  ingress:
  - from:
    # AND: повинен бути Під frontend У просторі імен restricted
    - podSelector:
        matchLabels:
          role: frontend
      namespaceSelector:
        matchLabels:
          name: restricted
EOF

# Перевірте
k describe networkpolicy and-policy

# Очищення
k delete networkpolicy and-policy
k delete pod secure
k delete namespace restricted
```

### Вправа 8: Виклик — Повна мережева ізоляція

Без підглядання у рішення:

1. Створіть простір імен `secure` з міткою `zone=secure`
2. Створіть Поди: `app` (мітка: tier=app), `db` (мітка: tier=db)
3. Створіть політику заборони всього ingress
4. Дозвольте `app` приймати трафік від будь-якого Поду в кластері
5. Дозвольте `db` приймати трафік лише від Подів `app`, порт 5432
6. Перевірте за допомогою `kubectl describe`
7. Очистіть все

```bash
# ВАШЕ ЗАВДАННЯ: Виконайте менше ніж за 7 хвилин
```

<details>
<summary>Рішення</summary>

```bash
# 1. Створіть простір імен
k create namespace secure
k label namespace secure zone=secure

# 2. Створіть Поди
k run app -n secure --image=nginx --labels="tier=app"
k run db -n secure --image=nginx --labels="tier=db"

# 3. Заборонити весь ingress
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# 4. Дозволити app звідусіль
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app
  namespace: secure
spec:
  podSelector:
    matchLabels:
      tier: app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector: {}
EOF

# 5. Дозволити db лише від app
cat << 'EOF' | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-db
  namespace: secure
spec:
  podSelector:
    matchLabels:
      tier: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: app
    ports:
    - port: 5432
EOF

# 6. Перевірте
k get networkpolicy -n secure
k describe networkpolicy -n secure

# 7. Очищення
k delete namespace secure
```

</details>

---

## Наступний модуль

[Модуль 3.7: CNI та мережа кластера](module-3.7-cni/) — Розуміння Container Network Interface.
