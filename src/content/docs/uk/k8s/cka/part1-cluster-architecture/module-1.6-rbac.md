---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 1.6: RBAC \u2014 \u0440\u043e\u043b\u044c\u043e\u0432\u0438\u0439 \u043a\u043e\u043d\u0442\u0440\u043e\u043b\u044c \u0434\u043e\u0441\u0442\u0443\u043f\u0443"
slug: uk/k8s/cka/part1-cluster-architecture/module-1.6-rbac
sidebar: 
  order: 7
lab: 
  id: cka-1.6-rbac
  url: https://killercoda.com/kubedojo/scenario/cka-1.6-rbac
  duration: "45 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Складність**: `[MEDIUM]` — часта тема на іспиті
>
> **Час на виконання**: 40-50 хвилин
>
> **Передумови**: Модуль 1.1 (Площина керування), розуміння просторів імен

---

## Що ви зможете робити

Після цього модуля ви зможете:
- **Налаштувати** Roles, ClusterRoles, RoleBindings та ClusterRoleBindings для доступу за принципом найменших привілеїв
- **Дебажити** помилки "forbidden", простежуючи ланцюжок RBAC (користувач → binding → role → дозвіл)
- **Спроєктувати** схему RBAC для кластера з кількома командами та ізоляцією просторів імен
- **Перевірити** існуючі правила RBAC для пошуку надмірно дозвільного доступу (wildcard verbs, cluster-admin bindings)

---

## Чому цей модуль важливий

У реальному кластері ви не хочете, щоб усі мали адміністративний доступ. Розробники повинні розгортати свої застосунки, але не видаляти продакшен-простори імен. CI/CD-системи повинні керувати деплойментами, але не читати секрети. Інструменти моніторингу повинні читати метрики, але не змінювати ресурси.

RBAC (рольовий контроль доступу) вирішує цю проблему. Саме так Kubernetes відповідає на питання: «Хто може робити що з якими ресурсами?»

Іспит CKA регулярно перевіряє RBAC. Вас попросять створити Ролі, ClusterRole та прив'язати їх до користувачів або Сервісних акаунтів. Освойтесь із цими концепціями — вони є ключовими для безпеки та щоденної роботи.

> **Аналогія з охоронцем**
>
> Уявіть RBAC як систему безпеки будівлі. **Роль** — це тип перепустки: «Перепустка розробника» дає доступ на поверхи 2-3, «Перепустка адміністратора» дає доступ на всі поверхи. **RoleBinding** — це видача конкретної перепустки: «Аліса отримує Перепустку розробника.» Система безпеки (API-сервер) перевіряє перепустку перед тим, як дозволити вхід на будь-який поверх (ресурс).

---

## Що ви вивчите

Після завершення цього модуля ви зможете:
- Розуміти концепції RBAC (Ролі, ClusterRole, прив'язки)
- Створювати Ролі та ClusterRole
- Прив'язувати ролі до користувачів, груп та Сервісних акаунтів
- Перевіряти дозволи за допомогою `kubectl auth can-i`
- Діагностувати проблеми з RBAC

---

## Частина 1: Концепції RBAC

### 1.1 Чотири ресурси RBAC

| Ресурс | Область дії | Призначення |
|--------|-------------|-------------|
| **Role** | Простір імен | Надає дозволи в межах простору імен |
| **ClusterRole** | Кластер | Надає дозволи на рівні всього кластера |
| **RoleBinding** | Простір імен | Прив'язує Role/ClusterRole до суб'єктів у просторі імен |
| **ClusterRoleBinding** | Кластер | Прив'язує ClusterRole до суб'єктів на рівні всього кластера |

### 1.2 Як працює RBAC

```
┌────────────────────────────────────────────────────────────────┐
│                     Потік RBAC                                    │
│                                                                   │
│   Суб'єкт              Роль                  Ресурси             │
│   (Хто?)               (Які дозволи?)        (Що саме?)          │
│                                                                   │
│   ┌─────────┐           ┌──────────────┐      ┌─────────────┐    │
│   │Користу- │           │    Роль      │      │   pods      │    │
│   │вач Аліса│◄─────────►│  дієслова:   │─────►│   services  │    │
│   └─────────┘  Зв'язано │  - get       │      │   secrets   │    │
│                 через   │  - list      │      └─────────────┘    │
│   ┌─────────┐ Binding   │  - create    │                          │
│   │Сервісний│           └──────────────┘                          │
│   │ акаунт  │                                                     │
│   └─────────┘                                                     │
│                                                                   │
│   ┌─────────┐                                                     │
│   │  Група  │                                                     │
│   └─────────┘                                                     │
│                                                                   │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Суб'єкти: хто отримує доступ

- **User** (Користувач): ідентичність людини (керується поза Kubernetes)
- **Group** (Група): колекція користувачів
- **ServiceAccount** (Сервісний акаунт): ідентичність для подів/застосунків

### 1.4 Дієслова: які дії дозволені

| Дієслово | Опис |
|----------|------|
| `get` | Прочитати один ресурс |
| `list` | Отримати список ресурсів (отримати всі) |
| `watch` | Спостерігати за змінами |
| `create` | Створити нові ресурси |
| `update` | Змінити існуючі ресурси |
| `patch` | Частково змінити ресурси |
| `delete` | Видалити ресурси |
| `deletecollection` | Видалити кілька ресурсів |

Поширені групи дієслів:
- **Тільки читання**: `get`, `list`, `watch`
- **Читання-запис**: `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`
- **Повний контроль**: `*` (усі дієслова)

---

## Частина 2: Ролі та ClusterRole

### 2.1 Створення Ролі (в межах простору імен)

```yaml
# role-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
  - apiGroups: [""]          # "" = основна API-група (pods, services тощо)
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

```bash
# Застосувати Роль
kubectl apply -f role-pod-reader.yaml

# Або створити імперативно
kubectl create role pod-reader \
  --verb=get,list,watch \
  --resource=pods \
  -n default
```

### 2.2 Створення ClusterRole (на рівні кластера)

```yaml
# clusterrole-node-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch"]
```

```bash
# Застосувати
kubectl apply -f clusterrole-node-reader.yaml

# Або імперативно
kubectl create clusterrole node-reader \
  --verb=get,list,watch \
  --resource=nodes
```

### 2.3 Кілька правил

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: dev
rules:
  # Поди: повний доступ
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec"]
    verbs: ["*"]

  # Деплойменти: повний доступ
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["*"]

  # Сервіси: створення та перегляд
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list", "create", "delete"]

  # ConfigMaps: тільки читання
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]

  # Secrets: немає доступу (не вказано = заборонено)
```

### 2.4 Довідник API-груп

| API-група | Ресурси |
|-----------|---------|
| `""` (основна) | pods, services, configmaps, secrets, namespaces, nodes, persistentvolumes |
| `apps` | deployments, replicasets, statefulsets, daemonsets |
| `batch` | jobs, cronjobs |
| `networking.k8s.io` | networkpolicies, ingresses |
| `rbac.authorization.k8s.io` | roles, clusterroles, rolebindings, clusterrolebindings |
| `storage.k8s.io` | storageclasses, volumeattachments |

```bash
# Знайти API-групу для будь-якого ресурсу
kubectl api-resources | grep deployment
# NAME         SHORTNAMES   APIVERSION   NAMESPACED   KIND
# deployments  deploy       apps/v1      true         Deployment
#                           ^^^^
#                           API-група — "apps"
```

> **Підступ: основна API-група**
>
> Основна API-група — це порожній рядок `""`. Ресурси на кшталт pods, services, configmaps використовують `apiGroups: [""]`, а не `apiGroups: ["core"]`.

---

## Частина 3: RoleBindings та ClusterRoleBindings

### 3.1 RoleBinding (в межах простору імен)

Прив'язує Роль або ClusterRole до суб'єктів у межах простору імен:

```yaml
# rolebinding-alice-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: alice-pod-reader
  namespace: default
subjects:
  - kind: User
    name: alice
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
# Імперативна команда
kubectl create rolebinding alice-pod-reader \
  --role=pod-reader \
  --user=alice \
  -n default
```

### 3.2 ClusterRoleBinding (на рівні кластера)

Прив'язує ClusterRole до суб'єктів на рівні всього кластера:

```yaml
# clusterrolebinding-bob-node-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: bob-node-reader
subjects:
  - kind: User
    name: bob
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
# Імперативна команда
kubectl create clusterrolebinding bob-node-reader \
  --clusterrole=node-reader \
  --user=bob
```

### 3.3 Прив'язка до кількох суб'єктів

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-team-access
  namespace: development
subjects:
  # Прив'язати до користувача
  - kind: User
    name: alice
    apiGroup: rbac.authorization.k8s.io

  # Прив'язати до групи
  - kind: Group
    name: developers
    apiGroup: rbac.authorization.k8s.io

  # Прив'язати до Сервісного акаунта
  - kind: ServiceAccount
    name: cicd-deployer
    namespace: development
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

### 3.4 Використання ClusterRole у RoleBinding

Потужний патерн: визначити ClusterRole один раз, прив'язати в конкретних просторах імен:

```yaml
# Використати вбудовану ClusterRole "edit" лише в просторі імен "production"
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: alice-edit-production
  namespace: production
subjects:
  - kind: User
    name: alice
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole     # Використовуємо ClusterRole
  name: edit            # Вбудована ClusterRole
  apiGroup: rbac.authorization.k8s.io

# Аліса може редагувати ресурси лише в просторі імен "production"
```

---

## Частина 4: Сервісні акаунти

### 4.1 Що таке Сервісні акаунти?

Сервісні акаунти надають ідентичність подам. Коли під запускається, він може використовувати дозволи свого Сервісного акаунта для взаємодії з API-сервером.

```bash
# Переглянути Сервісні акаунти
kubectl get serviceaccounts
kubectl get sa

# Кожний простір імен має Сервісний акаунт "default"
kubectl get sa default -o yaml
```

### 4.2 Створення Сервісного акаунта

```bash
# Створити Сервісний акаунт
kubectl create serviceaccount myapp-sa

# Або за допомогою YAML
cat > myapp-sa.yaml << 'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: default
EOF
kubectl apply -f myapp-sa.yaml
```

### 4.3 Прив'язка Ролей до Сервісних акаунтів

```bash
# Створити Роль
kubectl create role pod-reader \
  --verb=get,list,watch \
  --resource=pods

# Прив'язати до Сервісного акаунта
kubectl create rolebinding myapp-pod-reader \
  --role=pod-reader \
  --serviceaccount=default:myapp-sa
#                  ^^^^^^^^^^^^^^^^^
#                  формат простір_імен:ім'я
```

### 4.4 Використання Сервісного акаунта в Поді

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  serviceAccountName: myapp-sa    # Використати цей Сервісний акаунт
  containers:
  - name: myapp
    image: nginx
```

Тепер під має дозволи, надані `myapp-sa`.

> **Чи знали ви?**
>
> За замовчуванням поди використовують Сервісний акаунт `default` у своєму просторі імен. Цей акаунт зазвичай не має жодних дозволів. Завжди створюйте окремі Сервісні акаунти з мінімально необхідними дозволами.

---

## Частина 5: Вбудовані ClusterRole

Kubernetes постачається з корисними ClusterRole:

| ClusterRole | Дозволи |
|-------------|---------|
| `cluster-admin` | Повний доступ до всього (суперкористувач) |
| `admin` | Повний доступ у межах простору імен |
| `edit` | Читання/запис більшості ресурсів, без RBAC |
| `view` | Доступ тільки для читання більшості ресурсів |

```bash
# Переглянути всі вбудовані ClusterRole
kubectl get clusterroles | grep -v "^system:"

# Переглянути деталі ClusterRole
kubectl describe clusterrole edit
```

### Використання вбудованих ClusterRole

```bash
# Надати Алісі адміністративний доступ до простору імен "myapp"
kubectl create rolebinding alice-admin \
  --clusterrole=admin \
  --user=alice \
  -n myapp

# Надати Бобу доступ для перегляду в просторі імен "production"
kubectl create rolebinding bob-view \
  --clusterrole=view \
  --user=bob \
  -n production
```

---

## Частина 6: Перевірка дозволів

### 6.1 kubectl auth can-i

Перевірте, чи можете ви (або хтось інший) виконати дію:

```bash
# Перевірити свої дозволи
kubectl auth can-i create pods
kubectl auth can-i delete deployments
kubectl auth can-i '*' '*'  # Чи я адміністратор?

# Перевірити в конкретному просторі імен
kubectl auth can-i create pods -n production

# Перевірити для іншого користувача (потрібні права адміністратора)
kubectl auth can-i create pods --as=alice
kubectl auth can-i delete nodes --as=bob

# Перевірити для Сервісного акаунта
kubectl auth can-i list secrets --as=system:serviceaccount:default:myapp-sa
```

### 6.2 Переглянути всі дозволи

```bash
# Що я можу робити в цьому просторі імен?
kubectl auth can-i --list

# Що може Аліса?
kubectl auth can-i --list --as=alice

# Що може Сервісний акаунт?
kubectl auth can-i --list --as=system:serviceaccount:default:myapp-sa
```

### 6.3 Діагностика відмови в доступі

```bash
# Помилка: pods is forbidden
kubectl get pods
# Error: User "alice" cannot list resource "pods" in API group "" in namespace "default"

# Кроки діагностики:
# 1. Перевірте, які дозволи є у користувача
kubectl auth can-i --list --as=alice

# 2. Перевірте, які ролі прив'язані до користувача
kubectl get rolebindings -A -o wide | grep alice
kubectl get clusterrolebindings -o wide | grep alice

# 3. Перевірте правила ролі
kubectl describe role <role-name> -n <namespace>
kubectl describe clusterrole <clusterrole-name>
```

> **Бойова історія: таємниця 403**
>
> Інженер витратив години на діагностику, чому CI/CD-пайплайн не міг деплоїти. `kubectl auth can-i` показувала, що дозволи коректні. У чому була проблема? Сервісний акаунт був у просторі імен `cicd`, але RoleBinding був у просторі імен `production` з друкарською помилкою: `namespace: prduction`. Одна пропущена літера — години налагодження. Завжди перевіряйте простори імен у прив'язках двічі.

---

## Частина 7: Типові патерни RBAC

### 7.1 Доступ для розробника

```bash
# Створити простір імен
kubectl create namespace development

# Створити Сервісний акаунт
kubectl create serviceaccount developer -n development

# Прив'язати ClusterRole edit (читання/запис більшості ресурсів)
kubectl create rolebinding developer-edit \
  --clusterrole=edit \
  --serviceaccount=development:developer \
  -n development
```

### 7.2 Моніторинг тільки для читання

```bash
# Сервісний акаунт для інструментів моніторингу
kubectl create serviceaccount monitoring -n monitoring

# Доступ для читання на рівні всього кластера
kubectl create clusterrolebinding monitoring-view \
  --clusterrole=view \
  --serviceaccount=monitoring:monitoring
```

### 7.3 CI/CD деплоєр

```bash
# Створити роль тільки для деплойментів
kubectl create role deployer \
  --verb=get,list,watch,create,update,patch,delete \
  --resource=deployments,services,configmaps \
  -n production

# Прив'язати до CI/CD Сервісного акаунта
kubectl create rolebinding cicd-deployer \
  --role=deployer \
  --serviceaccount=cicd:pipeline \
  -n production
```

---

## Частина 8: Сценарії для іспиту

### 8.1 Швидке створення RBAC

```bash
# Завдання: Створити Роль, яка може get, list та watch поди і сервіси в просторі імен "app"

kubectl create role app-reader \
  --verb=get,list,watch \
  --resource=pods,services \
  -n app

# Завдання: Прив'язати роль до користувача "john"

kubectl create rolebinding john-app-reader \
  --role=app-reader \
  --user=john \
  -n app

# Перевірити
kubectl auth can-i get pods -n app --as=john
# yes
kubectl auth can-i delete pods -n app --as=john
# no
```

### 8.2 Сервісний акаунт з доступом на рівні кластера

```bash
# Завдання: Створити Сервісний акаунт "dashboard", який може переглядати поди в усіх просторах імен

kubectl create serviceaccount dashboard -n kube-system

kubectl create clusterrole pod-list \
  --verb=list \
  --resource=pods

kubectl create clusterrolebinding dashboard-pod-list \
  --clusterrole=pod-list \
  --serviceaccount=kube-system:dashboard
```

---

## Чи знали ви?

- **RBAC є адитивним**. Правила «заборонити» не існує. Якщо будь-яка Роль надає дозвіл — він дозволений. Ви не можете явно заблокувати доступ — ви можете лише не надавати його.

- **Агреговані ClusterRole** дозволяють об'єднувати кілька ClusterRole. Вбудовані ролі `admin`, `edit` та `view` є агрегованими — до них можна додавати додаткові правила.

- **system:* ClusterRole** призначені для внутрішніх компонентів Kubernetes. Не змінюйте їх, якщо не знаєте точно, що робите.

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Неправильна apiGroup | Роль не надає доступ | Перевірте `kubectl api-resources` для правильної групи |
| Відсутній простір імен у прив'язці | Неправильні дозволи | Завжди перевіряйте `-n namespace` |
| Забутий простір імен Сервісного акаунта | Прив'язка не працює | Використовуйте формат `простір_імен:ім'я` |
| Використання Role для кластерних ресурсів | Немає доступу до nodes, PV | Використовуйте ClusterRole для ресурсів на рівні кластера |
| Порожня apiGroup без лапок | Помилка YAML | Використовуйте `apiGroups: [""]` з лапками |
| Відсутнє дієслово `create` для субресурсів exec/attach | `kubectl exec` мовчки не працює (K8s 1.35+) | Додайте дієслово `create` до `pods/exec`, `pods/attach`, `pods/portforward` — див. примітку нижче |

> **Зміна в K8s 1.35: RBAC для WebSocket Streaming**
>
> Починаючи з Kubernetes 1.35, `kubectl exec`, `attach` та `port-forward` використовують WebSocket-з'єднання, які вимагають дієслова **`create`** для відповідного субресурсу (наприклад, `pods/exec`). Раніше потрібен був лише `get`. Існуючі політики RBAC, які надають `get pods/exec`, **мовчки перестануть працювати** — команди зависають або повертають помилки дозволів. Перевірте свої ClusterRole та Ролі:
>
> ```yaml
> # СТАРЕ (не працює в 1.35+):
> - resources: ["pods/exec"]
>   verbs: ["get"]
>
> # ВИПРАВЛЕНЕ:
> - resources: ["pods/exec", "pods/attach", "pods/portforward"]
>   verbs: ["get", "create"]
> ```

---

## Тест

1. **У чому різниця між Role та ClusterRole?**
   <details>
   <summary>Відповідь</summary>
   **Role** надає дозволи в межах конкретного простору імен. **ClusterRole** надає дозволи на рівні всього кластера або для ресурсів кластерного рівня (як-от Nodes). ClusterRole також можна прив'язати в одному просторі імен за допомогою RoleBinding.
   </details>

2. **Чи можна прив'язати ClusterRole за допомогою RoleBinding?**
   <details>
   <summary>Відповідь</summary>
   Так! Це поширений патерн. Коли ви прив'язуєте ClusterRole через RoleBinding, дозволи діють лише в межах цього простору імен. Це дозволяє визначити дозволи один раз (ClusterRole) і надавати їх вибірково (RoleBinding для кожного простору імен).
   </details>

3. **Поду потрібно отримати список Сервісів у своєму просторі імен. Що ви створюєте?**
   <details>
   <summary>Відповідь</summary>
   1. Створити Сервісний акаунт
   2. Створити Роль із `verbs: ["list"]` та `resources: ["services"]`
   3. Створити RoleBinding, що прив'язує Роль до Сервісного акаунта
   4. Встановити `serviceAccountName` у специфікації пода
   </details>

4. **Як перевірити, чи може користувач «alice» видаляти поди в просторі імен «production»?**
   <details>
   <summary>Відповідь</summary>
   `kubectl auth can-i delete pods -n production --as=alice`

   Ця команда імітує Алісу і перевіряє її дозволи відповідно до правил RBAC.
   </details>

---

## Практична вправа

**Завдання**: Налаштувати RBAC для команди розробників.

**Кроки**:

1. **Створити простір імен**:
```bash
kubectl create namespace dev-team
```

2. **Створити Сервісний акаунт**:
```bash
kubectl create serviceaccount dev-sa -n dev-team
```

3. **Створити Роль для розробників**:
```bash
kubectl create role developer \
  --verb=get,list,watch,create,update,delete \
  --resource=pods,deployments,services,configmaps \
  -n dev-team
```

4. **Прив'язати Роль до Сервісного акаунта**:
```bash
kubectl create rolebinding dev-sa-developer \
  --role=developer \
  --serviceaccount=dev-team:dev-sa \
  -n dev-team
```

5. **Перевірити дозволи**:
```bash
# Тестувати як Сервісний акаунт
kubectl auth can-i get pods -n dev-team \
  --as=system:serviceaccount:dev-team:dev-sa
# yes

kubectl auth can-i delete pods -n dev-team \
  --as=system:serviceaccount:dev-team:dev-sa
# yes

kubectl auth can-i get secrets -n dev-team \
  --as=system:serviceaccount:dev-team:dev-sa
# no (ми не надали доступ до секретів)

kubectl auth can-i get pods -n default \
  --as=system:serviceaccount:dev-team:dev-sa
# no (роль діє лише в просторі імен dev-team)
```

6. **Створити під з використанням Сервісного акаунта**:
```bash
cat > dev-pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: dev-shell
  namespace: dev-team
spec:
  serviceAccountName: dev-sa
  containers:
  - name: shell
    image: bitnami/kubectl
    command: ["sleep", "infinity"]
EOF

kubectl apply -f dev-pod.yaml
```

7. **Тестувати зсередини пода**:
```bash
kubectl exec -it dev-shell -n dev-team -- /bin/bash

# Усередині пода:
kubectl get pods              # Повинно працювати
kubectl get secrets           # Повинно не працювати (заборонено)
kubectl get pods -n default   # Повинно не працювати (заборонено)
exit
```

8. **Додати доступ для читання на рівні кластера** (бонус):
```bash
kubectl create clusterrolebinding dev-sa-view \
  --clusterrole=view \
  --serviceaccount=dev-team:dev-sa

# Тепер Сервісний акаунт може читати ресурси на рівні всього кластера
kubectl auth can-i get pods -n default \
  --as=system:serviceaccount:dev-team:dev-sa
# yes (але тільки читання)
```

9. **Очищення**:
```bash
kubectl delete namespace dev-team
kubectl delete clusterrolebinding dev-sa-view
rm dev-pod.yaml
```

**Критерії успіху**:
- [ ] Вміє створювати Ролі та ClusterRole
- [ ] Вміє створювати RoleBindings та ClusterRoleBindings
- [ ] Вміє прив'язувати до Users, Groups та Сервісних акаунтів
- [ ] Вміє перевіряти дозволи за допомогою `kubectl auth can-i`
- [ ] Розуміє різницю між областю дії простору імен та кластера

---

## Практичні вправи

### Вправа 1: Швидкісний тест RBAC (Ціль: 3 хвилини)

Створіть ресурси RBAC якомога швидше:

```bash
# Створити простір імен
kubectl create ns rbac-drill

# Створити Сервісний акаунт
kubectl create sa drill-sa -n rbac-drill

# Створити Роль (читання подів)
kubectl create role pod-reader --verb=get,list,watch --resource=pods -n rbac-drill

# Створити RoleBinding
kubectl create rolebinding drill-binding --role=pod-reader --serviceaccount=rbac-drill:drill-sa -n rbac-drill

# Тест
kubectl auth can-i get pods -n rbac-drill --as=system:serviceaccount:rbac-drill:drill-sa

# Очищення
kubectl delete ns rbac-drill
```

### Вправа 2: Тестування дозволів (Ціль: 5 хвилин)

```bash
kubectl create ns perm-test
kubectl create sa test-sa -n perm-test

# Створити обмежену роль
kubectl create role limited --verb=get,list --resource=pods,services -n perm-test
kubectl create rolebinding limited-binding --role=limited --serviceaccount=perm-test:test-sa -n perm-test

# Тестувати різні дозволи
echo "=== Тестуємо як test-sa ==="
kubectl auth can-i get pods -n perm-test --as=system:serviceaccount:perm-test:test-sa      # yes
kubectl auth can-i create pods -n perm-test --as=system:serviceaccount:perm-test:test-sa   # no
kubectl auth can-i get secrets -n perm-test --as=system:serviceaccount:perm-test:test-sa   # no
kubectl auth can-i get pods -n default --as=system:serviceaccount:perm-test:test-sa        # no
kubectl auth can-i get services -n perm-test --as=system:serviceaccount:perm-test:test-sa  # yes

# Очищення
kubectl delete ns perm-test
```

### Вправа 3: ClusterRole проти Role (Ціль: 5 хвилин)

```bash
# Створити простори імен
kubectl create ns ns-a
kubectl create ns ns-b
kubectl create sa cross-ns-sa -n ns-a

# Варіант 1: Role (в межах простору імен) — працює тільки в ns-a
kubectl create role ns-a-reader --verb=get,list --resource=pods -n ns-a
kubectl create rolebinding ns-a-binding --role=ns-a-reader --serviceaccount=ns-a:cross-ns-sa -n ns-a

# Тест
kubectl auth can-i get pods -n ns-a --as=system:serviceaccount:ns-a:cross-ns-sa  # yes
kubectl auth can-i get pods -n ns-b --as=system:serviceaccount:ns-a:cross-ns-sa  # no

# Варіант 2: ClusterRole + RoleBinding (прив'язка все ще в межах простору імен)
kubectl create clusterrole pod-reader-cluster --verb=get,list --resource=pods
kubectl create rolebinding ns-b-binding -n ns-b --clusterrole=pod-reader-cluster --serviceaccount=ns-a:cross-ns-sa

# Тепер може читати і ns-b
kubectl auth can-i get pods -n ns-b --as=system:serviceaccount:ns-a:cross-ns-sa  # yes

# Очищення
kubectl delete ns ns-a ns-b
kubectl delete clusterrole pod-reader-cluster
```

### Вправа 4: Усунення несправностей — відмова в доступі (Ціль: 5 хвилин)

```bash
# Підготовка: Створити SA з навмисно неправильною прив'язкою
kubectl create ns debug-rbac
kubectl create sa debug-sa -n debug-rbac
kubectl create role secret-reader --verb=get,list --resource=secrets -n debug-rbac
# НЕПРАВИЛЬНО: прив'язка ролі до іншого імені SA
kubectl create rolebinding wrong-binding --role=secret-reader --serviceaccount=debug-rbac:other-sa -n debug-rbac

# Користувач повідомляє: «Я не можу читати секрети!»
kubectl auth can-i get secrets -n debug-rbac --as=system:serviceaccount:debug-rbac:debug-sa
# no

# ВАШЕ ЗАВДАННЯ: Діагностувати та виправити
```

<details>
<summary>Рішення</summary>

```bash
# Перевірити, на що посилається rolebinding
kubectl get rolebinding wrong-binding -n debug-rbac -o yaml | grep -A5 subjects
# Показує: other-sa, а не debug-sa

# Виправити: Створити правильну прив'язку
kubectl delete rolebinding wrong-binding -n debug-rbac
kubectl create rolebinding correct-binding --role=secret-reader --serviceaccount=debug-rbac:debug-sa -n debug-rbac

# Перевірити
kubectl auth can-i get secrets -n debug-rbac --as=system:serviceaccount:debug-rbac:debug-sa
# yes

# Очищення
kubectl delete ns debug-rbac
```

</details>

### Вправа 5: Агреговані ClusterRole (Ціль: 5 хвилин)

```bash
# Створити агреговану роль
cat << 'EOF' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aggregate-reader
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]
EOF

# Вбудована ClusterRole 'view' автоматично включає правила з
# будь-якої ClusterRole з міткою aggregate-to-view: "true"

# Перевірити, що включає 'view'
kubectl get clusterrole view -o yaml | grep -A20 "rules:"

# Очищення
kubectl delete clusterrole aggregate-reader
```

### Вправа 6: RBAC для користувача (Ціль: 5 хвилин)

```bash
# Створити роль для гіпотетичного користувача "alice"
kubectl create ns alice-ns
kubectl create role alice-admin --verb='*' --resource='*' -n alice-ns
kubectl create rolebinding alice-is-admin --role=alice-admin --user=alice -n alice-ns

# Тестувати як Аліса
kubectl auth can-i create deployments -n alice-ns --as=alice      # yes
kubectl auth can-i delete pods -n alice-ns --as=alice             # yes
kubectl auth can-i get secrets -n default --as=alice              # no (інший простір імен)
kubectl auth can-i create namespaces --as=alice                   # no (кластерний рівень)

# Переглянути, що може Аліса
kubectl auth can-i --list -n alice-ns --as=alice

# Очищення
kubectl delete ns alice-ns
```

### Вправа 7: Виклик — налаштування мінімальних привілеїв

Створіть RBAC для «deployment-manager», який може:
- Створювати, оновлювати, видаляти Деплойменти в просторі імен `app`
- Переглядати (але не змінювати) Сервіси в просторі імен `app`
- Переглядати Поди в будь-якому просторі імен (тільки читання на рівні кластера)

```bash
kubectl create ns app
# ВАШЕ ЗАВДАННЯ: Створити необхідні Role, ClusterRole та прив'язки
```

<details>
<summary>Рішення</summary>

```bash
# Роль для керування деплойментами в просторі імен 'app'
kubectl create role deployment-manager \
  --verb=create,update,delete,get,list,watch \
  --resource=deployments \
  -n app

# Роль для перегляду сервісів у просторі імен 'app'
kubectl create role service-viewer \
  --verb=get,list,watch \
  --resource=services \
  -n app

# ClusterRole для перегляду подів на рівні всього кластера
kubectl create clusterrole pod-viewer \
  --verb=get,list,watch \
  --resource=pods

# Створити Сервісний акаунт
kubectl create sa deployment-manager -n app

# Прив'язати всі ролі
kubectl create rolebinding dm-deployments \
  --role=deployment-manager \
  --serviceaccount=app:deployment-manager \
  -n app

kubectl create rolebinding dm-services \
  --role=service-viewer \
  --serviceaccount=app:deployment-manager \
  -n app

kubectl create clusterrolebinding dm-pods \
  --clusterrole=pod-viewer \
  --serviceaccount=app:deployment-manager

# Тест
kubectl auth can-i create deployments -n app --as=system:serviceaccount:app:deployment-manager  # yes
kubectl auth can-i delete services -n app --as=system:serviceaccount:app:deployment-manager     # no
kubectl auth can-i get pods -n default --as=system:serviceaccount:app:deployment-manager        # yes

# Очищення
kubectl delete ns app
kubectl delete clusterrole pod-viewer
kubectl delete clusterrolebinding dm-pods
```

</details>

---

## Наступний модуль

[Модуль 1.7: Основи kubeadm](module-1.7-kubeadm/) — Початкове налаштування кластера та керування вузлами.
