---
title: "Модуль 1.1: Поглиблене вивчення Network Policies"
slug: uk/k8s/cks/part1-cluster-setup/module-1.1-network-policies
sidebar:
  order: 1
---
> **Складність**: `[СЕРЕДНЯ]` — Ключова навичка CKS
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Знання мережі з CKA, базовий досвід з NetworkPolicy

---

## Чому цей модуль важливий

NetworkPolicies — це фаєрвол Kubernetes. За замовчуванням усі Pod можуть спілкуватися з усіма іншими Pod — кошмар безпеки. NetworkPolicies дозволяють точно визначити, які Pod можуть спілкуватися з якими, блокуючи латеральний рух у разі компрометації.

CKS серйозно тестує NetworkPolicies. Ви повинні писати їх швидко та правильно під тиском іспиту.

---

## Проблема за замовчуванням

```
┌─────────────────────────────────────────────────────────────┐
│              МЕРЕЖА KUBERNETES ЗА ЗАМОВЧУВАННЯМ             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Без NetworkPolicies:                                      │
│                                                             │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐           │
│    │ Web Pod │◄───►│ API Pod │◄───►│ DB Pod  │           │
│    └────┬────┘     └────┬────┘     └────┬────┘           │
│         │               │               │                  │
│         └───────────────┼───────────────┘                  │
│                         │                                  │
│         ┌───────────────┼───────────────┐                  │
│         │               │               │                  │
│    ┌────┴────┐     ┌────┴────┐     ┌────┴────┐           │
│    │Зловмис- │◄───►│Будь-який│◄───►│ Secrets │           │
│    │ник Pod  │     │   Pod   │     │  Pod    │           │
│    └─────────┘     └─────────┘     └─────────┘           │
│                                                             │
│  ❌ Кожен Pod може дістатися до кожного іншого Pod         │
│  ❌ Скомпрометований Pod = доступ до всього                │
│  ❌ Немає мережевої сегментації                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Основи NetworkPolicy

### Як вони працюють

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: example
  namespace: default
spec:
  # Which pods this policy applies to
  podSelector:
    matchLabels:
      app: web

  # Which directions to control
  policyTypes:
  - Ingress  # Incoming traffic
  - Egress   # Outgoing traffic

  # What's allowed IN
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 80

  # What's allowed OUT
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
```

### Ключові концепції

```
┌─────────────────────────────────────────────────────────────┐
│              МЕНТАЛЬНА МОДЕЛЬ NETWORKPOLICY                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  podSelector: ДО КОГО застосовується ця політика?          │
│               (Порожній = усі Pod у просторі імен)         │
│                                                             │
│  policyTypes: ЯКІ напрямки трафіку контролювати?           │
│               - Лише Ingress                               │
│               - Лише Egress                                │
│               - Обидва                                     │
│                                                             │
│  ingress.from: ХТО може надсилати трафік ДО обраних Pod?   │
│                                                             │
│  egress.to: КУДИ обрані Pod можуть надсилати трафік?       │
│                                                             │
│  ports: ЯКІ порти дозволені?                               │
│         (Пропущено = усі порти)                            │
│                                                             │
│  КРИТИЧНО: Немає правил ingress/egress = ЗАБОРОНИТИ ВСЕ   │
│            (якщо вказано policyType)                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Основні патерни

### Патерн 1: Заборонити все за замовчуванням

```yaml
# Deny all ingress traffic to namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: secure
spec:
  podSelector: {}  # All pods
  policyTypes:
  - Ingress
  # No ingress rules = deny all ingress
---
# Deny all egress traffic from namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Egress
  # No egress rules = deny all egress
---
# Deny BOTH ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Патерн 2: Дозволити конкретний Pod-to-Pod

```yaml
# Allow frontend pods to access api pods on port 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### Патерн 3: Дозволити з простору імен

```yaml
# Allow any pod from 'monitoring' namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-monitoring
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
```

### Патерн 4: Дозволити до зовнішнього CIDR

```yaml
# Allow egress to specific IP range
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24  # Except this subnet
    ports:
    - port: 443
```

### Патерн 5: Дозволити DNS (Критично!)

```yaml
# Allow DNS - ALWAYS needed for egress policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

---

## Комбінування селекторів

### Логіка AND проти OR

```yaml
# OR: Allow from EITHER namespace OR pods with label
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        env: prod
  - podSelector:
      matchLabels:
        role: frontend

# AND: Allow from pods with label IN namespace with label
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        env: prod
    podSelector:
      matchLabels:
        role: frontend
```

```
┌─────────────────────────────────────────────────────────────┐
│              ПРАВИЛА КОМБІНУВАННЯ СЕЛЕКТОРІВ                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Два елементи списку = OR                                  │
│  - from:                                                   │
│    - namespaceSelector: ...    # АБО                       │
│    - podSelector: ...          # Збіг з будь-яким          │
│                                                             │
│  Один елемент, кілька селекторів = AND                     │
│  - from:                                                   │
│    - namespaceSelector: ...    # І                          │
│      podSelector: ...          # Обидва повинні збігатися  │
│                                                             │
│  ⚠️  Це поширена пастка на іспиті!                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Реальні сценарії іспиту

### Сценарій 1: Ізоляція бази даних

```yaml
# Only API pods can reach database on port 5432
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-isolation
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - port: 5432
  egress: []  # No egress allowed
```

### Сценарій 2: Багаторівневий застосунок

```yaml
# Web tier: only from ingress controller
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-policy
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - port: 80

# API tier: only from web tier
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
  namespace: app
spec:
  podSelector:
    matchLabels:
      tier: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: web
    ports:
    - port: 8080

# DB tier: only from API tier
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: app
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
          tier: api
    ports:
    - port: 5432
```

### Сценарій 3: Блокування сервісу метаданих

```yaml
# Block access to cloud metadata (169.254.169.254)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
```

---

## Налагодження NetworkPolicies

```bash
# List policies in namespace
kubectl get networkpolicies -n production

# Describe policy details
kubectl describe networkpolicy db-isolation -n production

# Check if CNI supports NetworkPolicies
# (Calico, Cilium, Weave support them; Flannel doesn't!)
kubectl get pods -n kube-system | grep -E "calico|cilium|weave"

# Test connectivity
kubectl exec -it frontend-pod -- nc -zv api-pod 8080
kubectl exec -it frontend-pod -- curl -s api-pod:8080

# Check pod labels (policies match on labels!)
kubectl get pod -n production --show-labels
```

---

## Чи знали ви?

- **NetworkPolicies є адитивними.** Якщо кілька політик обирають Pod, застосовується об'єднання всіх правил. Ви не можете використати одну політику для перевизначення іншої.

- **Поведінка за замовчуванням — дозволити все.** NetworkPolicies лише обмежують — вони не дозволяють явно. Pod без політик, що його обирають, дозволяє весь трафік.

- **DNS часто забувають.** Коли ви додаєте політики egress, Pod не можуть вирішувати DNS, якщо ви явно не дозволите UDP/TCP 53 до kube-dns.

- **Не всі CNI підтримують NetworkPolicies.** Flannel не підтримує. Calico, Cilium та Weave підтримують. Перевірте свій кластер!

- **Cilium виходить за межі NetworkPolicies.** Cilium підтримує стандартні Kubernetes NetworkPolicies плюс власний CRD `CiliumNetworkPolicy` для фільтрації L7 (HTTP/gRPC), DNS-обізнаних політик та **прозорого Pod-to-Pod шифрування** (WireGuard або IPsec) без будь-яких змін у застосунку. Якщо ваше середовище іспиту CKS використовує Cilium, ви отримуєте мережеве шифрування фактично безкоштовно:

```yaml
# Enable Cilium transparent encryption (cluster-level)
# In Cilium Helm values or ConfigMap:
encryption:
  enabled: true
  type: wireguard  # or ipsec
```

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Забути DNS egress | Pod не можуть вирішувати імена | Завжди дозволяйте DNS з політиками egress |
| Неправильна логіка селектора | Політика не відповідає потрібним Pod | AND = один елемент, OR = окремі елементи |
| Відсутні мітки простору імен | namespaceSelector не збігається | Позначте простори імен мітками |
| Тестування з неправильного Pod | Думає, що політика не працює | Перевірте, що мітки вихідного Pod збігаються |
| CNI не підтримує NP | Політика існує, але не застосовується | Використовуйте Calico, Cilium або Weave |

---

## Тест

1. **Що станеться, якщо NetworkPolicy вказує `policyTypes: [Ingress]`, але не має правил `ingress`?**
   <details>
   <summary>Відповідь</summary>
   Весь вхідний трафік до обраних Pod заборонений. Вказання policyType без правил означає "заборонити все для цього типу".
   </details>

2. **Як дозволити трафік від будь-якого Pod у конкретному просторі імен?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте `namespaceSelector` з мітками, що відповідають цьому простору імен. Простір імен повинен мати мітку для вибору, наприклад, `namespaceSelector: {matchLabels: {name: monitoring}}`.
   </details>

3. **Яка різниця між двома елементами `from` та двома селекторами в одному елементі `from`?**
   <details>
   <summary>Відповідь</summary>
   Два елементи `from` = OR (збіг з будь-яким). Два селектори в одному елементі = AND (збіг з обома). Це критично для складних політик.
   </details>

4. **Чому політики egress часто ламають вирішення DNS?**
   <details>
   <summary>Відповідь</summary>
   DNS використовує UDP порт 53 до Pod kube-dns. Політики egress, які явно не дозволяють це, блокують DNS, ламаючи вирішення імен для уражених Pod.
   </details>

---

## Практична вправа

**Завдання**: Створіть NetworkPolicies для трирівневого застосунку.

```bash
# Setup
kubectl create namespace exercise
kubectl label namespace exercise name=exercise

# Create pods
kubectl run web --image=nginx -n exercise -l tier=web
kubectl run api --image=nginx -n exercise -l tier=api
kubectl run db --image=nginx -n exercise -l tier=db

# Wait for pods
kubectl wait --for=condition=Ready pod --all -n exercise

# Task 1: Create default deny all ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: exercise
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

# Verify: api can't reach db anymore
kubectl exec -n exercise web -- curl -s --connect-timeout 2 db || echo "Blocked (expected)"

# Task 2: Allow web -> api on port 80
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
  namespace: exercise
spec:
  podSelector:
    matchLabels:
      tier: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: web
    ports:
    - port: 80
EOF

# Task 3: Allow api -> db on port 80
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
  namespace: exercise
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
          tier: api
    ports:
    - port: 80
EOF

# Verify
kubectl exec -n exercise web -- curl -s --connect-timeout 2 api  # Should work
kubectl exec -n exercise api -- curl -s --connect-timeout 2 db   # Should work
kubectl exec -n exercise web -- curl -s --connect-timeout 2 db   # Should fail

# Cleanup
kubectl delete namespace exercise
```

**Критерії успіху**: Web може дістатися до API, API може дістатися до DB, Web не може безпосередньо дістатися до DB.

---

## Підсумок

**Основи NetworkPolicy**:
- `podSelector`: До яких Pod застосовується політика
- `policyTypes`: Ingress, Egress або обидва
- `ingress/egress`: Який трафік дозволений

**Критичні патерни**:
- Заборона за замовчуванням: `podSelector: {}` без правил
- Завжди дозволяйте DNS з політиками egress
- AND проти OR: Один елемент = AND, окремі елементи = OR

**Поради для іспиту**:
- Правильно позначайте Pod та простори імен
- Тестуйте з'єднання після застосування політик
- Пам'ятайте: немає політики = дозволити все

---

## Наступний модуль

[Модуль 1.2: CIS Benchmarks](module-1.2-cis-benchmarks/) — Аудит безпеки кластера з kube-bench.
