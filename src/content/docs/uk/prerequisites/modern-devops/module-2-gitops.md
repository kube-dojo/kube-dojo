---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 2: GitOps"
sidebar:
  order: 3
---
> **Складність**: `[MEDIUM]` — Ключовий операційний патерн
>
> **Час на виконання**: 30-35 хвилин
>
> **Передумови**: Модуль 1 (Інфраструктура як код), основи Git

---

## Чому цей модуль важливий

GitOps доводить Інфраструктуру як код до її логічного завершення: Git стає єдиним джерелом істини для всього. Зміни інфраструктури відбуваються через pull request'и, а не прямі команди. Цей патерн стає стандартом для операцій з Kubernetes і значно підвищить вашу ефективність.

---

## Що таке GitOps?

GitOps — це операційна модель, де:

1. **Git є джерелом істини** для бажаного стану системи
2. **Зміни відбуваються через Git** (коміти, pull request'и)
3. **Автоматизовані агенти** синхронізують фактичний стан із Git
4. **Дрейф конфігурації автоматично виправляється** до стану в Git

```
┌─────────────────────────────────────────────────────────────┐
│              ТРАДИЦІЙНИЙ vs GITOPS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Традиційний CI/CD (Push-модель):                          │
│  ┌──────┐    ┌─────┐    ┌─────────┐    ┌─────────┐       │
│  │ Розр │───►│ Git │───►│   CI    │───►│ Кластер │       │
│  └──────┘    └─────┘    │ Пайплайн│    └─────────┘       │
│                         └─────────┘                        │
│  CI-пайплайн пушить у кластер (потрібні облікові дані)     │
│                                                             │
│  GitOps (Pull-модель):                                     │
│  ┌──────┐    ┌─────┐    ┌─────────┐    ┌─────────┐       │
│  │ Розр │───►│ Git │◄───│  GitOps │───►│ Кластер │       │
│  └──────┘    └─────┘    │  Агент  │    └─────────┘       │
│                         └─────────┘                        │
│  Агент тягне з Git і застосовує (агент живе в кластері)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чотири принципи GitOps

### 1. Декларативний

Все описується декларативно:

```yaml
# Не "запусти 3 nginx поди"
# А "бажаний стан — 3 nginx поди"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  # ...
```

### 2. Версіонований та незмінний

Усі зміни проходять через Git:

```bash
git log --oneline manifests/
a1b2c3d Scale web to 5 replicas
d4e5f6g Add redis cache
g7h8i9j Initial deployment

# Every change is:
# - Versioned (commit hash)
# - Immutable (can't change history)
# - Attributed (who made it)
# - Reviewable (PR history)
```

### 3. Автоматичне витягування

Агенти безперервно витягують і застосовують зміни:

```
┌─────────────────────────────────────────────────────────────┐
│  Цикл GitOps-агента (кожні 30 секунд — 5 хвилин):         │
│                                                             │
│  1. Перевірити Git на наявність змін                        │
│  2. Порівняти стан у Git зі станом кластера                │
│  3. Якщо є різниця: застосувати зміни до кластера          │
│  4. Повторити                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Безперервне узгодження

Дрейф конфігурації автоматично виправляється:

```bash
# Someone manually edits production
kubectl scale deployment web --replicas=10

# GitOps agent detects drift
# Git says 3 replicas, cluster has 10
# Agent corrects: scales back to 3

# Result: Git always wins
```

---

## Інструменти GitOps

### Argo CD

Найпопулярніший інструмент GitOps для Kubernetes:

```
┌─────────────────────────────────────────────────────────────┐
│              АРХІТЕКТУРА ARGO CD                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │              КЛАСТЕР KUBERNETES                  │       │
│  │                                                  │       │
│  │  ┌──────────────────────────────────────────┐  │       │
│  │  │           ARGO CD                         │  │       │
│  │  │  ┌────────────┐  ┌────────────────────┐ │  │       │
│  │  │  │ API Сервер │  │ Контролер          │ │  │       │
│  │  │  │            │  │ застосунків        │ │  │       │
│  │  │  └────────────┘  │ (цикл синхрон.)   │ │  │       │
│  │  │                  └─────────┬──────────┘ │  │       │
│  │  │  ┌────────────┐            │            │  │       │
│  │  │  │ Веб-       │            │            │  │       │
│  │  │  │ інтерфейс  │            │            │  │       │
│  │  │  └────────────┘            │            │  │       │
│  │  └────────────────────────────┼────────────┘  │       │
│  │                               │                │       │
│  │         ┌─────────────────────┘                │       │
│  │         ▼                                      │       │
│  │    ┌─────────┐  ┌─────────┐  ┌─────────┐     │       │
│  │    │ Заст. 1 │  │ Заст. 2 │  │ Заст. 3 │     │       │
│  │    │(синхр.) │  │(синхр.) │  │(синхр.) │     │       │
│  │    └─────────┘  └─────────┘  └─────────┘     │       │
│  │                                               │       │
│  └───────────────────────────────────────────────┘       │
│                         ▲                                 │
│                         │ витягує маніфести               │
│                    ┌────┴────┐                           │
│                    │   Git   │                           │
│                    │  Репо   │                           │
│                    └─────────┘                           │
│                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Flux CD

Альтернатива, що отримала статус Graduated у CNCF:

```yaml
# Flux GitRepository
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/myorg/my-app
  ref:
    branch: main

---
# Flux Kustomization (applies manifests)
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./kubernetes
  prune: true
  sourceRef:
    kind: GitRepository
    name: my-app
```

### Порівняння

| Функція | Argo CD | Flux CD |
|---------|---------|---------|
| Інтерфейс | Гарний веб-дашборд | Орієнтований на CLI |
| Мультитенантність | Вбудована | Через простори імен |
| RBAC | Комплексний | Kubernetes-нативний |
| Підтримка Helm | Першокласна | Через контролери |
| Крива навчання | Помірна | Крутіша |
| Статус у CNCF | Graduated | Graduated |

---

## Структура репозиторію

### Монорепо (все разом)

```bash
gitops-repo/
├── apps/
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── backend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── database/
│       └── statefulset.yaml
├── infrastructure/
│   ├── ingress-nginx/
│   ├── cert-manager/
│   └── monitoring/
└── clusters/
    ├── production/
    │   └── kustomization.yaml
    └── staging/
        └── kustomization.yaml
```

### Полірепо (окремі репозиторії)

```bash
# App repos (developers own)
frontend-app/
  └── kubernetes/
      ├── deployment.yaml
      └── service.yaml

# GitOps repo (ops owns)
gitops-config/
  └── clusters/
      ├── production/
      │   └── apps.yaml  # References app repos
      └── staging/
          └── apps.yaml
```

---

## Робочий процес GitOps

```
┌─────────────────────────────────────────────────────────────┐
│              РОБОЧИЙ ПРОЦЕС РОЗГОРТАННЯ GITOPS              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Розробник вносить зміну                                │
│     └── Оновлює deployment.yaml (новий тег образу)         │
│                                                             │
│  2. Створює Pull Request                                    │
│     └── PR запускає: лінтинг, валідацію, сканування безпеки│
│                                                             │
│  3. Рев'ю та затвердження                                  │
│     └── Команда переглядає, коментує, затверджує            │
│                                                             │
│  4. Зливання до main                                       │
│     └── Git тепер має новий бажаний стан                   │
│                                                             │
│  5. GitOps-агент виявляє зміну                             │
│     └── Порівнює стан у Git зі станом кластера             │
│                                                             │
│  6. Агент застосовує зміну                                  │
│     └── kubectl apply (або Helm upgrade тощо)              │
│                                                             │
│  7. Кластер досягає нового стану                           │
│     └── Нові Поди запущені, старі Поди завершені           │
│                                                             │
│  Час від зливання до розгортання: ~30 секунд — 5 хвилин    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Автоматизація оновлення образів

Сучасні інструменти GitOps можуть автоматично оновлювати теги образів:

```yaml
# Argo CD Image Updater annotation
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: myapp=myrepo/myapp
    argocd-image-updater.argoproj.io/myapp.update-strategy: semver

# Flux Image Automation
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageUpdateAutomation
metadata:
  name: flux-system
spec:
  interval: 1m
  sourceRef:
    kind: GitRepository
    name: flux-system
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        email: fluxcdbot@users.noreply.github.com
        name: fluxcdbot
      messageTemplate: 'Update image to {{.NewTag}}'
    push:
      branch: main
```

```
Процес:
1. CI збирає новий образ: myapp:v1.2.3
2. Пушить до реєстру
3. GitOps виявляє новий тег
4. Оновлює Git-репо з новим тегом
5. Синхронізує кластер з новим образом

Повністю автоматизовано, повністю задокументовано в Git!
```

---

## Просування між середовищами

```
┌─────────────────────────────────────────────────────────────┐
│              ПРОСУВАННЯ МІЖ СЕРЕДОВИЩАМИ                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  environments/                                              │
│  ├── base/                 # Спільна конфігурація          │
│  │   ├── deployment.yaml                                   │
│  │   └── service.yaml                                      │
│  ├── dev/                  # Перевизначення для dev        │
│  │   └── kustomization.yaml  (replicas: 1, image: latest) │
│  ├── staging/              # Перевизначення для staging    │
│  │   └── kustomization.yaml  (replicas: 2, image: v1.2.3) │
│  └── prod/                 # Перевизначення для prod       │
│      └── kustomization.yaml  (replicas: 5, image: v1.2.2) │
│                                                             │
│  Процес просування:                                        │
│  1. Зміни спочатку йдуть до dev (автодеплой)              │
│  2. Просування до staging (PR: оновити тег образу)        │
│  3. Просування до prod (PR: оновити тег образу)           │
│                                                             │
│  Кожне просування — це Git-коміт = повний аудит-трейл     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Відкат у GitOps

Відкат — це просто `git revert`:

```bash
# Production has a bug!

# Option 1: Revert the commit
git revert abc123
git push

# GitOps agent syncs: old version restored
# Time to rollback: < 5 minutes

# Option 2: Use Argo CD UI
# Click "Rollback" on the application
# Argo reverts to previous sync state

# All rollbacks are tracked in Git history
git log --oneline
def456 Revert "Deploy v1.2.3"  # ← Rollback recorded
abc123 Deploy v1.2.3           # ← Bad deployment
```

---

## Чи знали ви?

- **Термін "GitOps" був придуманий компанією Weaveworks** у 2017 році. Все почалося з публікації в блозі, де описувалося, як вони керували кластерами Kubernetes.

- **GitOps усуває `kubectl apply` з вашого робочого процесу.** У чистому GitOps-середовищі жодна людина ніколи не виконує kubectl у продакшені. Усі зміни проходять через Git.

- **Назва Argo CD** походить з грецької міфології. Арго — це корабель, на якому Ясон та аргонавти вирушили у подорож. CD означає Continuous Delivery (безперервна доставка).

---

## Типові помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Ручний kubectl у продакшені | Обходить аудит-трейл, спричиняє дрейф конфігурації | Використовуйте тільки GitOps-агента |
| Секрети в Git | Порушення безпеки | Використовуйте sealed-secrets або зовнішні секрети |
| Відсутність процесу рев'ю PR | Погані зміни потрапляють у прод | Вимагайте затвердження |
| Занадто часта синхронізація | Нестабільність кластера | Інтервали 1-5 хвилин |
| Відсутність перевірок стану | Зламані розгортання залишаються | Налаштуйте проби готовності |

---

## Тест

1. **У чому ключова різниця між push-моделлю та pull-моделлю розгортання?**
   <details>
   <summary>Відповідь</summary>
   Push-модель: CI-пайплайн пушить зміни до кластера (потрібні облікові дані кластера). Pull-модель (GitOps): агент у кластері тягне з Git і застосовує (тільки агент потребує доступу до кластера). GitOps безпечніший, бо облікові дані залишаються в кластері.
   </details>

2. **Що станеться, якщо хтось вручну змінить продакшен у GitOps-середовищі?**
   <details>
   <summary>Відповідь</summary>
   GitOps-агент виявляє дрейф конфігурації між Git (бажаний стан) і кластером (фактичний стан), а потім виправляє кластер, щоб він відповідав Git. Ручні зміни автоматично скасовуються.
   </details>

3. **Як виконати відкат розгортання в GitOps?**
   <details>
   <summary>Відповідь</summary>
   `git revert <commit>` і push. GitOps-агент синхронізує скасований стан до кластера. Все відстежується в історії Git.
   </details>

4. **Чому GitOps безпечніший за традиційний CI/CD?**
   <details>
   <summary>Відповідь</summary>
   У традиційному CI/CD пайплайни потребують облікових даних кластера (поза кластером). У GitOps тільки агент (всередині кластера) має облікові дані. Жодних облікових даних у CI-системах — нічого витікати.
   </details>

---

## Практична вправа

**Завдання**: Випробуйте концепції GitOps без встановлення Argo CD.

```bash
# This simulates GitOps behavior manually
# In real GitOps, an agent does this automatically

# 1. Create a "Git repo" (directory)
mkdir -p ~/gitops-demo/manifests
cd ~/gitops-demo

# 2. Create initial desired state
cat << 'EOF' > manifests/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitops-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gitops-demo
  template:
    metadata:
      labels:
        app: gitops-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.24
EOF

# 3. Apply (simulate GitOps sync)
kubectl apply -f manifests/

# 4. Verify
kubectl get deployment gitops-demo

# 5. Simulate drift (manual change)
kubectl scale deployment gitops-demo --replicas=5

# 6. Check drift
kubectl get deployment gitops-demo
# Shows 5 replicas

# 7. Reconcile (simulate GitOps correction)
kubectl apply -f manifests/
# Back to 2 replicas!

# 8. Make a "Git change"
sed -i '' 's/nginx:1.24/nginx:1.25/' manifests/deployment.yaml

# 9. Apply new state (simulate GitOps sync)
kubectl apply -f manifests/

# 10. Verify update
kubectl get deployment gitops-demo -o jsonpath='{.spec.template.spec.containers[0].image}'
# Shows nginx:1.25

# 11. Cleanup
kubectl delete -f manifests/
rm -rf ~/gitops-demo
```

**Критерії успіху**: Зрозуміти синхронізацію та виправлення дрейфу конфігурації.

---

## Підсумок

**GitOps** — це операційна модель для сучасного Kubernetes:

**Основні принципи**:
- Git — єдине джерело істини
- Зміни через pull request'и
- Автоматична синхронізація з кластером
- Дрейф конфігурації автоматично виправляється

**Інструменти**:
- Argo CD: повнофункціональний, чудовий інтерфейс
- Flux CD: Graduated у CNCF, Kubernetes-нативний

**Переваги**:
- Повний аудит-трейл (історія Git)
- Простий відкат (git revert)
- Краща безпека (немає доступу CI до кластера)
- Самодокументований (стан у Git)

**Ключова ідея**: У GitOps ви ніколи не виконуєте `kubectl apply` у продакшені. Ви комітите до Git, а агент робить все інше.

---

## Наступний модуль

[Модуль 3: CI/CD Пайплайни](module-1.3-cicd-pipelines/) — Автоматизація збірки, тестування та розгортання.
