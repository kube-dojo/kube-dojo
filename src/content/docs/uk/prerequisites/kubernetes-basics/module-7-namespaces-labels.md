---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 7: \u041f\u0440\u043e\u0441\u0442\u043e\u0440\u0438 \u0456\u043c\u0435\u043d \u0442\u0430 \u043c\u0456\u0442\u043a\u0438"
sidebar:
  order: 8
---
> **Складність**: `[QUICK]` — Організаційні концепції
>
> **Час на виконання**: 25-30 хвилин
>
> **Передумови**: Модуль 3 (Поди), Модуль 4 (Деплойменти)

---

## Чому цей модуль важливий

З ростом кластерів організація стає критично важливою. Простори імен забезпечують ізоляцію та область видимості. Мітки дозволяють вибирати та організовувати ресурси. Разом вони роблять великі кластери керованими.

---

## Простори імен

### Що таке простори імен?

Простори імен — це віртуальні кластери всередині кластера:

```
┌─────────────────────────────────────────────────────────────┐
│              КЛАСТЕР KUBERNETES                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Простір імен:   │  │  Простір імен:   │               │
│  │    "frontend"    │  │    "backend"     │               │
│  │  ┌────┐ ┌────┐   │  │  ┌────┐ ┌────┐   │               │
│  │  │web │ │api │   │  │  │db  │ │cache│  │               │
│  │  └────┘ └────┘   │  │  └────┘ └────┘   │               │
│  │                  │  │                  │               │
│  │  Ізольовано від  │  │  Ізольовано від  │               │
│  │  інших просторів │  │  інших просторів │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐                                      │
│  │  Простір імен:   │  Стандартні простори імен:           │
│  │   "kube-system"  │  • default                          │
│  │  Системні поди   │  • kube-system                       │
│  └──────────────────┘  • kube-public                       │
│                        • kube-node-lease                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Створення просторів імен

```bash
# Create namespace
kubectl create namespace my-app
kubectl create ns my-app          # Short form

# View namespaces
kubectl get namespaces
kubectl get ns
```

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-app
  labels:
    team: backend
```

### Робота з просторами імен

```bash
# Run command in specific namespace
kubectl get pods -n my-app
kubectl get pods --namespace=my-app

# All namespaces
kubectl get pods -A
kubectl get pods --all-namespaces

# Set default namespace for context
kubectl config set-context --current --namespace=my-app

# Check current default
kubectl config view --minify | grep namespace
```

### Стандартні простори імен

| Простір імен | Призначення |
|-----------|---------|
| `default` | Куди потрапляють ресурси, якщо простір імен не вказано |
| `kube-system` | Системні компоненти (API-сервер, планувальник тощо) |
| `kube-public` | Публічно доступні дані |
| `kube-node-lease` | Дані heartbeat нод |

---

## Мітки

### Що таке мітки?

Мітки — це пари ключ-значення, прикріплені до ресурсів:

```yaml
metadata:
  name: my-pod
  labels:
    app: nginx
    environment: production
    team: frontend
    version: v1.2.3
```

### Використання міток

```bash
# Add labels when creating
kubectl run nginx --image=nginx --labels="app=nginx,env=prod"

# Add labels to existing resource
kubectl label pod nginx tier=frontend

# Remove label
kubectl label pod nginx tier-

# Update label (overwrite)
kubectl label pod nginx env=staging --overwrite
```

### Вибір за мітками

```bash
# Filter by single label
kubectl get pods -l app=nginx
kubectl get pods --selector=app=nginx

# Multiple labels (AND)
kubectl get pods -l app=nginx,env=prod

# Set-based selectors
kubectl get pods -l 'env in (prod, staging)'
kubectl get pods -l 'app notin (test)'
kubectl get pods -l 'tier'              # Has label
kubectl get pods -l '!tier'             # Doesn't have label

# Show labels
kubectl get pods --show-labels
```

---

## Мітки в дії

```
┌─────────────────────────────────────────────────────────────┐
│              ВИБІР ЗА МІТКАМИ                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Селектор сервісу:        Поди:                            │
│  ┌──────────────────┐    ┌──────────────────┐             │
│  │ selector:        │    │ labels:          │             │
│  │   app: nginx     │───►│   app: nginx     │  ✓ Збіг    │
│  │   tier: frontend │    │   tier: frontend │             │
│  └──────────────────┘    └──────────────────┘             │
│                          ┌──────────────────┐             │
│                          │ labels:          │             │
│                      ╳   │   app: nginx     │  ✗ Нема    │
│                          │                  │    tier     │
│                          └──────────────────┘             │
│                          ┌──────────────────┐             │
│                          │ labels:          │             │
│                      ╳   │   app: redis     │  ✗ Інший   │
│                          │   tier: frontend │     app    │
│                          └──────────────────┘             │
│                                                             │
│  Сервіс направляє трафік лише до подів, що                │
│  відповідають УСІМ міткам селектора                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Мітки проти анотацій

| Мітки | Анотації |
|--------|-------------|
| Використовуються для вибору | Використовуються для метаданих |
| Обмеження на ключ/значення | Можуть зберігати більші дані |
| Використовуються K8s внутрішньо | Для людей та інструментів |
| Обмежена кількість символів | Майже необмежений вміст |

```yaml
metadata:
  labels:                    # For selection
    app: nginx
    version: v1
  annotations:               # For metadata
    description: "Main web server"
    git-commit: "abc123"
    monitoring.enabled: "true"
```

---

## Найкращі практики

### Рекомендовані мітки

```yaml
metadata:
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/version: "1.25"
    app.kubernetes.io/component: frontend
    app.kubernetes.io/part-of: website
    app.kubernetes.io/managed-by: helm
```

### Стратегія просторів імен

```
Середовища розробки:
  - dev
  - staging
  - prod

За командами:
  - team-frontend
  - team-backend
  - team-data

За застосунками:
  - app-website
  - app-api
  - app-admin
```

---

## Чи знали ви?

- **Деякі ресурси не мають простору імен.** Ноди, PersistentVolume та самі простори імен мають область видимості кластера.

- **Мітки мають обмеження.** Ключі та значення мають ліміти на символи та вимоги до формату.

- **Простори імен не забезпечують безпеку за замовчуванням.** Поди в різних просторах імен можуть спілкуватися, якщо NetworkPolicy цього не обмежують.

- **Простір імен `default` — це пастка.** Використовуйте явні простори імен, щоб уникнути змішування непов'язаних ресурсів.

---

## Тест

1. **Яка різниця між мітками та анотаціями?**
   <details>
   <summary>Відповідь</summary>
   Мітки призначені для вибору (використовуються сервісами, деплойментами тощо) і мають обмеження формату. Анотації — для довільних метаданих (використовуються людьми та інструментами) і можуть зберігати більші дані.
   </details>

2. **Як побачити поди в усіх просторах імен?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get pods -A` або `kubectl get pods --all-namespaces`
   </details>

3. **Як вибрати поди з міткою app=nginx ТА env=prod?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get pods -l app=nginx,env=prod` (мітки через кому означають І)
   </details>

4. **Чи є простори імен межами безпеки?**
   <details>
   <summary>Відповідь</summary>
   Ні, не за замовчуванням. Поди можуть спілкуватися між просторами імен, якщо NetworkPolicy цього не обмежують. Простори імен — це організаційні межі, а не межі безпеки, без додаткової конфігурації.
   </details>

---

## Практична вправа

**Завдання**: Попрактикуватися з просторами імен та мітками.

```bash
# 1. Create namespaces
kubectl create namespace frontend
kubectl create namespace backend

# 2. Create pods with labels in different namespaces
kubectl run web --image=nginx -n frontend --labels="app=web,tier=frontend"
kubectl run api --image=nginx -n backend --labels="app=api,tier=backend"
kubectl run cache --image=redis -n backend --labels="app=cache,tier=backend"

# 3. List all pods
kubectl get pods -A

# 4. Filter by label
kubectl get pods -A -l tier=backend

# 5. Show labels
kubectl get pods -A --show-labels

# 6. Add label to existing pod
kubectl label pod web -n frontend version=v1

# 7. Set default namespace
kubectl config set-context --current --namespace=frontend
kubectl get pods  # Now shows frontend by default

# 8. Reset to default
kubectl config set-context --current --namespace=default

# 9. Cleanup
kubectl delete namespace frontend backend
```

**Критерій успіху**: Вмієте фільтрувати поди за простором імен та мітками.

---

## Підсумок

**Простори імен**:
- Віртуальні кластери всередині кластера
- Забезпечують область видимості та організацію
- Не є межами безпеки за замовчуванням
- Використовуйте `-n namespace` або `-A` для всіх

**Мітки**:
- Пари ключ-значення на ресурсах
- Дозволяють вибір (сервіси, деплойменти)
- Використовуйте `-l key=value` для фільтрації
- Кома розділяє умови І

**Найкращі практики**:
- Використовуйте змістовні назви просторів імен
- Дотримуйтесь єдиних конвенцій іменування міток
- Ніколи не працюйте в `default` для реальних навантажень

---

## Наступний модуль

[Модуль 8: YAML для Kubernetes](module-1.8-yaml-kubernetes/) — Написання та розуміння маніфестів K8s.
