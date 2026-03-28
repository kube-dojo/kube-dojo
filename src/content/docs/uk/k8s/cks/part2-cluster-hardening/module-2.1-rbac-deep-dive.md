---
title: "Модуль 2.1: Глибоке занурення в RBAC"
slug: uk/k8s/cks/part2-cluster-hardening/module-2.1-rbac-deep-dive
sidebar:
  order: 1
---
> **Складність**: `[MEDIUM]` - Основна навичка безпеки
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Знання RBAC з CKA, основи ServiceAccount

---

## Чому цей модуль важливий

RBAC — це механізм контролю доступу в Kubernetes. На CKA ви навчилися створювати Role та RoleBinding. CKS йде глибше: ви повинні перевіряти RBAC на надмірні дозволи, розуміти шляхи ескалації привілеїв та впроваджувати принцип найменших привілеїв.

Неправильно налаштований RBAC є однією з найпоширеніших вразливостей Kubernetes.

---

## Огляд RBAC

```
┌─────────────────────────────────────────────────────────────┐
│              КОМПОНЕНТИ RBAC                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Role/ClusterRole                                          │
│  └── Визначає ЯКІ дії дозволені                           │
│      ├── apiGroups: ["", "apps", "batch"]                  │
│      ├── resources: ["pods", "deployments"]                │
│      └── verbs: ["get", "list", "create", "delete"]        │
│                                                             │
│  RoleBinding/ClusterRoleBinding                            │
│  └── Визначає ХТОСЕ отримує дозволи                       │
│      ├── subjects: [users, groups, serviceaccounts]        │
│      └── roleRef: [Role або ClusterRole]                   │
│                                                             │
│  Область дії:                                              │
│  ├── Role + RoleBinding = обмежено простором імен           │
│  ├── ClusterRole + ClusterRoleBinding = на весь кластер    │
│  └── ClusterRole + RoleBinding = багаторазове використання │
│      в просторі імен                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Небезпечні шаблони RBAC

### Шаблон 1: Дозволи з підстановочними знаками

```yaml
# НЕБЕЗПЕЧНО: Дозволяє все
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: too-permissive
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]

# ЧОМУ ЦЕ ПОГАНО:
# - Еквівалентно cluster-admin
# - Може отримати доступ до секретів, змінювати RBAC, видаляти будь-що
# - Порушує принцип найменших привілеїв
```

### Шаблон 2: Доступ до секретів

```yaml
# НЕБЕЗПЕЧНО: Може читати всі секрети
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]

# ЧОМУ ЦЕ ПОГАНО:
# - Секрети містять паролі, токени, сертифікати
# - Один секрет може скомпрометувати цілі застосунки
# - Слід обмежувати доступ до конкретних секретів
```

### Шаблон 3: Ескалація RBAC

```yaml
# НЕБЕЗПЕЧНО: Може змінювати RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: rbac-modifier
rules:
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings"]
  verbs: ["create", "update", "patch"]

# ЧОМУ ЦЕ ПОГАНО:
# - Може надати собі cluster-admin
# - Атака ескалації привілеїв
# - Тільки адміністратори повинні змінювати RBAC
```

### Шаблон 4: Створення Pod з привілеями

```yaml
# НЕБЕЗПЕЧНО: Може створювати Pod (потенційна ескалація)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-creator
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["create"]

# ЧОМУ ЦЕ ПОГАНО:
# - Може створювати привілейовані Pod
# - Може монтувати токени ServiceAccount
# - Може вийти з контейнера на вузол
# - Потребує Pod Security для безпеки
```

---

## Приклади найменших привілеїв

### Добре: Доступ до конкретних ресурсів

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-viewer
  namespace: production
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

### Добре: Обмеження за іменами ресурсів

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: specific-configmap-reader
  namespace: app
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config", "feature-flags"]  # Тільки ці!
  verbs: ["get"]
```

### Добре: Тільки субресурси

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-executor
  namespace: debug
rules:
- apiGroups: [""]
  resources: ["pods/exec"]  # Тільки exec, без повного доступу до Pod
  verbs: ["create"]
```

---

## Аудит RBAC

### Пошук надмірно дозвільних ролей

```bash
# Список всіх ClusterRole з підстановочними дозволами
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    (.verbs[]? == "*") or
    (.resources[]? == "*") or
    (.apiGroups[]? == "*")
  ) | .metadata.name'

# Пошук ролей, що можуть читати секрети
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    (.resources[]? | contains("secrets")) and
    ((.verbs[]? == "get") or (.verbs[]? == "*"))
  ) | .metadata.name'

# Пошук ролей, що можуть змінювати RBAC
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    (.apiGroups[]? == "rbac.authorization.k8s.io") and
    ((.verbs[]? == "create") or (.verbs[]? == "update") or (.verbs[]? == "*"))
  ) | .metadata.name'
```

### Перевірка дозволів користувача

```bash
# Що може конкретний користувач?
kubectl auth can-i --list --as=system:serviceaccount:default:myapp

# Чи може користувач створювати привілейовані Pod?
kubectl auth can-i create pods --as=developer

# Чи може користувач читати секрети?
kubectl auth can-i get secrets --as=system:serviceaccount:app:backend

# У конкретному просторі імен
kubectl auth can-i delete deployments -n production --as=developer
```

### Пошук прив'язок до небезпечних ролей

```bash
# Хто має cluster-admin?
kubectl get clusterrolebindings -o json | jq -r '
  .items[] |
  select(.roleRef.name == "cluster-admin") |
  "\(.metadata.name): \(.subjects[]?.name // "unknown")"'

# Список всіх ClusterRoleBinding
kubectl get clusterrolebindings -o wide

# Опис підозрілої прив'язки
kubectl describe clusterrolebinding suspicious-binding
```

---

## Запобігання ескалації RBAC

```
┌─────────────────────────────────────────────────────────────┐
│              ШЛЯХИ ЕСКАЛАЦІЇ RBAC                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Пряма ескалація:                                          │
│  ─────────────────────────────────────────────────────────  │
│  1. Створення/оновлення ClusterRoleBinding                 │
│     → Прив'язати себе до cluster-admin                     │
│                                                             │
│  2. Створення/оновлення ClusterRole                        │
│     → Додати дозволи *                                     │
│                                                             │
│  Непряма ескалація:                                        │
│  ─────────────────────────────────────────────────────────  │
│  3. Створення Pod у будь-якому просторі імен               │
│     → Змонтувати привілейований ServiceAccount             │
│                                                             │
│  4. Створення Pod з доступом до вузла                      │
│     → Прочитати облікові дані kubelet                      │
│                                                             │
│  5. Імпертсонація користувачів                             │
│     → Діяти як cluster-admin                               │
│                                                             │
│  Запобігання:                                              │
│  ─────────────────────────────────────────────────────────  │
│  • Ніколи не надавайте права на зміну RBAC без обмежень    │
│  • Використовуйте Pod Security Admission                   │
│  • Регулярно перевіряйте дієслова ескалації                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Дієслова Escalate та Bind

```yaml
# Дієслово 'bind' дозволяє створювати прив'язки до ролей,
# навіть без дозволів, які надає роль
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterrolebindings"]
  verbs: ["create"]  # Плюс...
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles"]
  verbs: ["bind"]  # ...це дозволяє прив'язуватися до будь-якої ролі!

# Дієслово 'escalate' дозволяє надавати дозволи,
# яких користувач не має
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles"]
  verbs: ["escalate"]  # Може додавати будь-які дозволи до ролей!
```

---

## Найкращі практики

```
┌─────────────────────────────────────────────────────────────┐
│              НАЙКРАЩІ ПРАКТИКИ RBAC                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Найменші привілеї                                      │
│     └── Надавайте тільки те, що потрібно                   │
│     └── Віддавайте перевагу Role замість ClusterRole       │
│     └── Використовуйте resourceNames де можливо            │
│                                                             │
│  2. Без підстановочних знаків                              │
│     └── Ніколи не використовуйте "*" у продакшені         │
│     └── Вказуйте конкретні ресурси та дієслова             │
│                                                             │
│  3. Регулярний аудит                                       │
│     └── Перевіряйте прив'язки cluster-admin                │
│     └── Контролюйте доступ до секретів                     │
│     └── Моніторте зміни RBAC                               │
│                                                             │
│  4. Ізоляція просторів імен                                │
│     └── Один ServiceAccount на застосунок                  │
│     └── Ролі обмежені простором імен                       │
│                                                             │
│  5. Захист ресурсів RBAC                                   │
│     └── Тільки адміністратори кластера змінюють RBAC       │
│     └── Перевіряйте дієслова bind/escalate                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Реальні сценарії іспиту

### Сценарій 1: Зменшення дозволів

```bash
# Дано: ServiceAccount з надмірними дозволами
# Завдання: Зменшити до тільки get/list pods

# Перевірити поточні дозволи
kubectl auth can-i --list --as=system:serviceaccount:app:backend -n app

# Знайти RoleBinding
kubectl get rolebindings -n app -o wide

# Перевірити роль
kubectl get role backend-role -n app -o yaml

# Створити обмежену роль
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: app
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
EOF

# Перевірити
kubectl auth can-i delete pods --as=system:serviceaccount:app:backend -n app
# Повинно повернути "no"
```

### Сценарій 2: Пошук та видалення небезпечної прив'язки

```bash
# Знайти, хто має cluster-admin
kubectl get clusterrolebindings -o json | jq -r '
  .items[] |
  select(.roleRef.name == "cluster-admin") |
  .metadata.name'

# Видалити невідповідну прив'язку
kubectl delete clusterrolebinding developer-admin
```

### Сценарій 3: Створення ролі з найменшими привілеями

```bash
# Вимога: Застосунку потрібно читати ConfigMap та створювати події
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-role
  namespace: myapp
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-binding
  namespace: myapp
subjects:
- kind: ServiceAccount
  name: myapp-sa
  namespace: myapp
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

---

## Налагодження RBAC

```bash
# Тестувати як конкретний користувач
kubectl auth can-i create pods --as=jane

# Тестувати як ServiceAccount
kubectl auth can-i get secrets --as=system:serviceaccount:default:myapp

# Список всіх дозволів
kubectl auth can-i --list --as=jane

# Чому користувач може/не може щось робити?
kubectl auth can-i create pods --as=jane -v=5

# Перевірити, хто може робити щось
kubectl auth who-can create pods
kubectl auth who-can delete secrets -n production
```

---

## Чи знали ви?

- **Kubernetes не має правила 'deny' (заборонити).** RBAC працює виключно за принципом додавання — ви можете лише надавати дозволи, але не забороняти їх явно. Щоб обмежити доступ, просто не надавайте його.

- **Група 'system:masters'** жорстко закодована з правами cluster-admin. Ви не можете прибрати їх через RBAC. Якщо хтось у цій групі, він має повний доступ.

- **Дієслова 'escalate' та 'bind'** були додані спеціально для запобігання ескалації привілеїв. До Kubernetes 1.12 будь-хто, хто міг створювати RoleBinding, міг прив'язатися до cluster-admin!

- **Агреговані ClusterRole** (такі як admin, edit, view) автоматично включають правила з інших ролей, позначених міткою агрегації. Саме так CRD розширюють вбудовані ролі.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Надання cluster-admin розробникам | Повний доступ до всього | Використовуйте edit або власні ролі |
| Використання ClusterRole, коли достатньо Role | Надмірна область дії | Віддавайте перевагу обмеженню простором імен |
| Підстановочні знаки у продакшені | Відсутність контролю доступу | Вказуйте конкретні дозволи |
| Відсутність аудиту прив'язок | Невідомо, хто має доступ | Регулярні перевірки RBAC |
| Ігнорування стандартних ServiceAccount | Стандартний SA може мати дозволи | Вимкніть автомонтування, використовуйте окремий SA |

---

## Тест

1. **Яка різниця між Role та ClusterRole?**
   <details>
   <summary>Відповідь</summary>
   Role обмежена простором імен і може надавати дозволи лише в межах простору імен. ClusterRole діє на весь кластер і може надавати дозволи на ресурси рівня кластера (наприклад, вузли) або використовуватися з RoleBinding для багаторазових дозволів у межах простору імен.
   </details>

2. **Як перевірити, які дозволи має ServiceAccount?**
   <details>
   <summary>Відповідь</summary>
   `kubectl auth can-i --list --as=system:serviceaccount:<namespace>:<sa-name>` — ця команда показує всі дозволи ServiceAccount.
   </details>

3. **Чому дозволи з підстановочними знаками (*) небезпечні?**
   <details>
   <summary>Відповідь</summary>
   Підстановочні знаки надають доступ до всіх ресурсів, дієслів або груп API — включаючи секрети, ресурси RBAC та чутливі системні компоненти. Фактично вони надають рівень доступу cluster-admin.
   </details>

4. **Для чого потрібні дієслова 'bind' та 'escalate'?**
   <details>
   <summary>Відповідь</summary>
   Це дієслова запобігання ескалації привілеїв. 'bind' дозволяє створювати прив'язки до ролей з дозволами, яких у вас немає. 'escalate' дозволяє змінювати ролі, додаючи дозволи, яких у вас немає. Обидва повинні бути суворо контрольованими.
   </details>

---

## Практична вправа

**Завдання**: Аудит та виправлення надмірних дозволів RBAC.

```bash
# Підготовка: Створення конфігурації з надмірними дозволами
kubectl create namespace rbac-test
kubectl create serviceaccount admin-app -n rbac-test

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: overpermissive
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-app-binding
subjects:
- kind: ServiceAccount
  name: admin-app
  namespace: rbac-test
roleRef:
  kind: ClusterRole
  name: overpermissive
  apiGroup: rbac.authorization.k8s.io
EOF

# Завдання 1: Перевірити дозволи
kubectl auth can-i --list --as=system:serviceaccount:rbac-test:admin-app

# Завдання 2: Перевірити, чи може він читати секрети (не повинен!)
kubectl auth can-i get secrets --as=system:serviceaccount:rbac-test:admin-app

# Завдання 3: Створити обмежену роль (тільки Pod у просторі імен)
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-manager
  namespace: rbac-test
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "create", "delete"]
EOF

# Завдання 4: Замінити ClusterRoleBinding на RoleBinding
kubectl delete clusterrolebinding admin-app-binding

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: admin-app-binding
  namespace: rbac-test
subjects:
- kind: ServiceAccount
  name: admin-app
  namespace: rbac-test
roleRef:
  kind: Role
  name: pod-manager
  apiGroup: rbac.authorization.k8s.io
EOF

# Завдання 5: Переконатися, що дозволи тепер обмежені
kubectl auth can-i get secrets --as=system:serviceaccount:rbac-test:admin-app
# Повинно повернути "no"

kubectl auth can-i get pods --as=system:serviceaccount:rbac-test:admin-app -n rbac-test
# Повинно повернути "yes"

kubectl auth can-i get pods --as=system:serviceaccount:rbac-test:admin-app -n default
# Повинно повернути "no" (обмежено простором імен)

# Очищення
kubectl delete namespace rbac-test
kubectl delete clusterrole overpermissive
```

**Критерії успіху**: ServiceAccount може керувати лише Pod у своєму власному просторі імен.

---

## Підсумок

**Принципи безпеки RBAC**:
- Завжди найменші привілеї
- Без підстановочних знаків у продакшені
- Віддавайте перевагу Role замість ClusterRole
- Використовуйте resourceNames де можливо

**Небезпечні шаблони**:
- Дозволи з підстановочними знаками (*, *)
- Доступ до секретів без потреби
- Права на зміну RBAC
- Дієслова bind/escalate

**Команди аудиту**:
- `kubectl auth can-i --list --as=...`
- `kubectl auth who-can <verb> <resource>`
- Перевірка ClusterRoleBinding до cluster-admin

**Поради для іспиту**:
- Знайте, як зменшити дозволи
- Практикуйте пошук надмірно дозвільних ролей
- Розумійте шляхи ескалації

---

## Наступний модуль

[Модуль 2.2: Безпека ServiceAccount](module-2.2-serviceaccount-security/) — Зміцнення ServiceAccount та управління токенами.
