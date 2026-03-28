---
title: "Модуль 1.5: Безпека GUI (Kubernetes Dashboard)"
slug: uk/k8s/cks/part1-cluster-setup/module-1.5-gui-security
sidebar:
  order: 5
---
> **Складність**: `[СЕРЕДНЯ]` — Поширена поверхня атаки
>
> **Час на виконання**: 30-35 хвилин
>
> **Передумови**: Знання RBAC з CKA, Модуль 1.1 (Network Policies)

---

## Чому цей модуль важливий

Kubernetes Dashboard був сумнозвісним вектором атаки. У 2018 році кластер Kubernetes Tesla був скомпрометований через відкритий dashboard — зловмисники використали його для майнінгу криптовалюти. Неправильно налаштований dashboard дає зловмисникам повний контроль над кластером зі зручним GUI.

CKS тестує вашу здатність захистити або обмежити веб-доступ до кластера.

---

## Ризик Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│              СЦЕНАРІЙ АТАКИ ЧЕРЕЗ DASHBOARD                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Поширена неправильна конфігурація:                        │
│                                                             │
│  Інтернет ────► Dashboard (відкритий) ────► Повний доступ  │
│                                              до кластера!  │
│                                                             │
│  Що йде не так:                                            │
│  ─────────────────────────────────────────────────────────  │
│  1. Dashboard відкритий без автентифікації                  │
│  2. Dashboard використовує cluster-admin ServiceAccount    │
│  3. Кнопка "Пропустити" дозволяє анонімний доступ         │
│  4. Немає NetworkPolicy, що обмежує доступ                 │
│                                                             │
│  Результат:                                                │
│  ⚠️  Будь-хто може переглядати secrets                     │
│  ⚠️  Будь-хто може розгортати Pod (криптомайнери!)        │
│  ⚠️  Будь-хто може видаляти ресурси                       │
│  ⚠️  Повна компрометація кластера                          │
│                                                             │
│  Реальний інцидент: Tesla (2018)                           │
│  └── Зловмисники майнили крипто через відкритий dashboard  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Варіанти безпеки Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│              РЕЖИМИ ДОСТУПУ ДО DASHBOARD                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Варіант 1: Не встановлювати його                          │
│  ─────────────────────────────────────────────────────────  │
│  Найбезпечніше. Використовуйте kubectl замість цього.     │
│  CLI безпечніший за GUI.                                   │
│                                                             │
│  Варіант 2: Доступ тільки для читання                      │
│  ─────────────────────────────────────────────────────────  │
│  Dashboard може переглядати, але не змінювати.             │
│  Використовуйте мінімальні дозволи RBAC.                  │
│                                                             │
│  Варіант 3: Тільки автентифікований доступ                 │
│  ─────────────────────────────────────────────────────────  │
│  Обов'язковий вхід по токену або kubeconfig.               │
│  Без кнопки "Пропустити".                                  │
│                                                             │
│  Варіант 4: Тільки внутрішній доступ                       │
│  ─────────────────────────────────────────────────────────  │
│  Потрібен kubectl proxy або port-forward.                  │
│  Без зовнішнього доступу.                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Безпечне встановлення Dashboard

### Крок 1: Розгортання Dashboard

```bash
# Official dashboard installation
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Verify deployment
kubectl get pods -n kubernetes-dashboard
kubectl get svc -n kubernetes-dashboard
```

### Крок 2: Створення мінімального ServiceAccount

```yaml
# Read-only dashboard service account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-readonly
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-readonly
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dashboard-readonly
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dashboard-readonly
subjects:
- kind: ServiceAccount
  name: dashboard-readonly
  namespace: kubernetes-dashboard
```

### Крок 3: Отримання токена доступу

```bash
# Create token for the service account
kubectl create token dashboard-readonly -n kubernetes-dashboard

# Or create a long-lived secret (older method)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-readonly-token
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/service-account.name: dashboard-readonly
type: kubernetes.io/service-account-token
EOF

# Get the token
kubectl get secret dashboard-readonly-token -n kubernetes-dashboard -o jsonpath='{.data.token}' | base64 -d
```

---

## Методи доступу

### Метод 1: kubectl proxy (Найбезпечніший)

```bash
# Start proxy (only accessible from localhost)
kubectl proxy

# Access dashboard at:
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### Метод 2: Port Forward

```bash
# Forward dashboard port
kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443

# Access at https://localhost:8443
# Use token to authenticate
```

### Метод 3: NodePort (Менш безпечний)

```yaml
# Expose dashboard as NodePort
apiVersion: v1
kind: Service
metadata:
  name: kubernetes-dashboard-nodeport
  namespace: kubernetes-dashboard
spec:
  type: NodePort
  selector:
    k8s-app: kubernetes-dashboard
  ports:
  - port: 443
    targetPort: 8443
    nodePort: 30443
```

**Увага**: NodePort відкриває доступ на всіх вузлах. Використовуйте NetworkPolicy для обмеження доступу!

---

## Обмеження доступу до Dashboard

### NetworkPolicy для Dashboard

```yaml
# Only allow access from specific namespace/pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-access
  namespace: kubernetes-dashboard
spec:
  podSelector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  policyTypes:
  - Ingress
  ingress:
  # Only from admin namespace
  - from:
    - namespaceSelector:
        matchLabels:
          name: admin-access
    ports:
    - port: 8443
```

### Вимкнення кнопки "Пропустити"

Dashboard має кнопку "Пропустити", яка дозволяє анонімний доступ. Вимкніть її:

```yaml
# In dashboard deployment, add argument
spec:
  containers:
  - name: kubernetes-dashboard
    args:
    - --auto-generate-certificates
    - --namespace=kubernetes-dashboard
    - --enable-skip-login=false  # Disable skip button
```

Або пропатчіть існуюче розгортання:

```bash
kubectl patch deployment kubernetes-dashboard -n kubernetes-dashboard \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--enable-skip-login=false"}]'
```

---

## Ingress для Dashboard (Виробниче середовище)

Якщо потрібно відкрити dashboard зовні:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kubernetes-dashboard
  namespace: kubernetes-dashboard
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # Client certificate authentication
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-secret: "kubernetes-dashboard/ca-secret"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - dashboard.example.com
    secretName: dashboard-tls
  rules:
  - host: dashboard.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kubernetes-dashboard
            port:
              number: 443
```

---

## Контрольний список безпеки

```
┌─────────────────────────────────────────────────────────────┐
│              КОНТРОЛЬНИЙ СПИСОК БЕЗПЕКИ DASHBOARD           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  □ Чи дійсно потрібен dashboard?                           │
│    └── Розгляньте kubectl або Lens замість цього           │
│                                                             │
│  □ Мінімальні дозволи RBAC                                 │
│    └── Ніколи не використовуйте cluster-admin             │
│    └── Тільки для читання, якщо можливо                    │
│                                                             │
│  □ Кнопка "Пропустити" вимкнена                            │
│    └── --enable-skip-login=false                           │
│                                                             │
│  □ Доступ обмежений                                        │
│    └── kubectl proxy або port-forward                      │
│    └── NetworkPolicy, що обмежує джерело                   │
│                                                             │
│  □ Якщо відкритий зовні                                    │
│    └── TLS обов'язковий                                    │
│    └── Клієнтські сертифікати mTLS                        │
│    └── Доступ тільки через VPN                             │
│                                                             │
│  □ Тільки автентифікація по токену                         │
│    └── Короткоживучі токени бажані                        │
│    └── Без базової автентифікації                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Реальні сценарії іспиту

### Сценарій 1: Обмеження RBAC Dashboard

```bash
# Check current dashboard permissions
kubectl get clusterrolebinding | grep dashboard
kubectl describe clusterrolebinding kubernetes-dashboard

# If using cluster-admin, create restricted role instead
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-viewer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "nodes"]
  verbs: ["get", "list"]
EOF

# Update binding
kubectl delete clusterrolebinding kubernetes-dashboard
kubectl create clusterrolebinding kubernetes-dashboard \
  --clusterrole=dashboard-viewer \
  --serviceaccount=kubernetes-dashboard:kubernetes-dashboard
```

### Сценарій 2: Вимкнення анонімного доступу

```bash
# Patch dashboard to disable skip
kubectl patch deployment kubernetes-dashboard -n kubernetes-dashboard \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--enable-skip-login=false"}]'

# Verify
kubectl get deployment kubernetes-dashboard -n kubernetes-dashboard -o yaml | grep skip
```

### Сценарій 3: Застосування NetworkPolicy

```bash
# Create NetworkPolicy to restrict access
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-restrict
  namespace: kubernetes-dashboard
spec:
  podSelector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          dashboard-access: "true"
EOF
```

---

## Альтернативи Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│              АЛЬТЕРНАТИВИ DASHBOARD                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl (CLI)                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Найбезпечніший — використовує kubeconfig               │
│  • Повна функціональність                                  │
│  • Придатний до скриптів                                   │
│                                                             │
│  Lens (Десктопний застосунок)                               │
│  ─────────────────────────────────────────────────────────  │
│  • Локальний GUI-застосунок                                │
│  • Використовує ваш kubeconfig                             │
│  • Без компонентів на стороні кластера                     │
│                                                             │
│  K9s (Термінальний UI)                                     │
│  ─────────────────────────────────────────────────────────  │
│  • GUI на базі терміналу                                   │
│  • Використовує ваш kubeconfig                             │
│  • Дуже ефективний для операцій                            │
│                                                             │
│  Rancher/OpenShift Console                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Корпоративного рівня                                    │
│  • Вбудована автентифікація                                │
│  • Безпечніший за дизайном                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **Порушення Tesla у 2018 році** сталося через те, що їхній Kubernetes dashboard був відкритий без захисту паролем. Зловмисники розгорнули контейнери для криптомайнінгу.

- **Dashboard v2.0+** вимкнув кнопку "Пропустити" за замовчуванням. Старіші версії мали її увімкненою, роблячи анонімний доступ тривіально легким.

- **Самі Pod dashboard** потребують дозволів RBAC для читання ресурсів кластера. Обмеження ServiceAccount dashboard обмежує те, що можуть бачити користувачі.

- **kubectl proxy** є безпечним, оскільки він прив'язується лише до localhost та використовує ваші облікові дані kubeconfig. Dashboard бачить ваші дозволи, а не підвищені.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Використання cluster-admin для dashboard | Повний доступ для зловмисників | Створіть мінімальний RBAC |
| Відкриття через LoadBalancer | Доступ з публічного інтернету | Використовуйте kubectl proxy |
| Залишена увімкненою кнопка "Пропустити" | Можливий анонімний доступ | --enable-skip-login=false |
| Немає NetworkPolicy | Будь-який Pod може дістатися до dashboard | Обмежте джерела ingress |
| Не оновлюється dashboard | Відомі вразливості | Тримайте оновленим |

---

## Тест

1. **Який найбезпечніший спосіб доступу до Kubernetes Dashboard?**
   <details>
   <summary>Відповідь</summary>
   Використання `kubectl proxy` — він прив'язується лише до localhost та використовує ваші облікові дані kubeconfig. Dashboard успадковує ваші дозволи RBAC.
   </details>

2. **Який аргумент вимикає кнопку "Пропустити" в dashboard?**
   <details>
   <summary>Відповідь</summary>
   `--enable-skip-login=false` — додайте це до аргументів контейнера dashboard, щоб запобігти анонімному доступу.
   </details>

3. **Чому dashboard не повинен використовувати ServiceAccount cluster-admin?**
   <details>
   <summary>Відповідь</summary>
   Cluster-admin має повний доступ до всього. Якщо dashboard скомпрометований, зловмисники отримують повний контроль над кластером. Використовуйте мінімальні дозволи замість цього.
   </details>

4. **Що сталося під час порушення Kubernetes Tesla?**
   <details>
   <summary>Відповідь</summary>
   Tesla відкрила свій Kubernetes dashboard без автентифікації. Зловмисники отримали до нього доступ, виявили облікові дані AWS у змінних середовища та використали ресурси кластера для криптомайнінгу.
   </details>

---

## Практична вправа

**Завдання**: Захистіть встановлення Kubernetes Dashboard.

```bash
# Step 1: Install dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Step 2: Wait for deployment
kubectl wait --for=condition=available deployment/kubernetes-dashboard -n kubernetes-dashboard --timeout=120s

# Step 3: Create restricted ServiceAccount
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-readonly
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dashboard-readonly
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dashboard-readonly
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dashboard-readonly
subjects:
- kind: ServiceAccount
  name: dashboard-readonly
  namespace: kubernetes-dashboard
EOF

# Step 4: Disable skip button
kubectl patch deployment kubernetes-dashboard -n kubernetes-dashboard \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--enable-skip-login=false"}]'

# Step 5: Create NetworkPolicy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-ingress
  namespace: kubernetes-dashboard
spec:
  podSelector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  policyTypes:
  - Ingress
  ingress: []  # Deny all ingress - only kubectl proxy works
EOF

# Step 6: Get token for readonly user
kubectl create token dashboard-readonly -n kubernetes-dashboard

# Step 7: Access via proxy
kubectl proxy &
echo "Access dashboard at: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"

# Cleanup
kubectl delete namespace kubernetes-dashboard
```

**Критерії успіху**: Dashboard вимагає токен, кнопка "Пропустити" вимкнена, NetworkPolicy обмежує доступ.

---

## Підсумок

**Ризики Dashboard**:
- Повний доступ до кластера при неправильній конфігурації
- Кнопка "Пропустити" дозволяє анонімний доступ
- Публічний доступ запрошує атаки

**Заходи безпеки**:
- Мінімальний RBAC (ніколи cluster-admin)
- Вимкнення кнопки "Пропустити"
- Використання kubectl proxy для доступу
- Обмеження через NetworkPolicy

**Найкращі практики**:
- Розгляньте відмову від встановлення dashboard
- Використовуйте kubectl, Lens або K9s замість цього
- Якщо потрібен, серйозно обмежте доступ
- Тільки автентифікація по токену

**Поради для іспиту**:
- Знайте, як створити мінімальний ServiceAccount
- Знайте аргумент кнопки "Пропустити"
- Розумійте, що kubectl proxy є найбезпечнішим

---

## Частина 1 завершена!

Ви закінчили **Налаштування кластера** (10% CKS). Тепер ви розумієте:
- Network Policies для сегментації
- CIS Benchmarks з kube-bench
- Ingress TLS та заголовки безпеки
- Захист сервісу метаданих
- Зміцнення безпеки Dashboard

**Наступна частина**: [Частина 2: Зміцнення кластера](../part2-cluster-hardening/module-2.1-rbac-deep-dive/) — RBAC, ServiceAccounts та безпека API.
