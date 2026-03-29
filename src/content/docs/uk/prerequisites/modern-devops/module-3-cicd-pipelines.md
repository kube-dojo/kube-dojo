---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 3: CI/CD \u043a\u043e\u043d\u0432\u0435\u0454\u0440\u0438"
sidebar:
  order: 4
---
> **Складність**: `[MEDIUM]` — Необхідна автоматизація
>
> **Час на виконання**: 35–40 хвилин
>
> **Передумови**: Модуль 1 (IaC), базові знання Git

---

## Чому цей модуль важливий

Щоразу, коли ви пушите код, він має автоматично тестуватися, збиратися та готуватися до розгортання. CI/CD конвеєри усувають проблему «у мене на машині працює» і забезпечують стабільні, надійні релізи. Для застосунків у Kubernetes CI/CD — це спосіб збирати образи контейнерів і запускати розгортання.

---

## CI проти CD

```
┌─────────────────────────────────────────────────────────────┐
│              КОНВЕЄР CI/CD                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  БЕЗПЕРЕРВНА ІНТЕГРАЦІЯ (CI)                                │
│  "Зливайте код часто, перевіряйте кожну зміну"            │
│                                                             │
│  ┌─────┐    ┌──────┐    ┌─────┐    ┌─────────┐            │
│  │Пуш  │───►│Збірка│───►│Тест │───►│Артефакт │            │
│  │коду │    │      │    │     │    │(образ)  │            │
│  └─────┘    └──────┘    └─────┘    └─────────┘            │
│                                                             │
│  БЕЗПЕРЕРВНА ДОСТАВКА (CD)                                  │
│  "Завжди готовий до розгортання, деплой у прод одним       │
│   натисканням"                                              │
│                                                             │
│  ┌─────────┐    ┌───────────┐    ┌──────────┐            │
│  │Артефакт │───►│Деплой на  │───►│ Ручне    │            │
│  │(образ)  │    │Staging    │    │Підтвердж.│            │
│  └─────────┘    └───────────┘    └────┬─────┘            │
│                                       │                    │
│                                       ▼                    │
│                              ┌──────────────┐             │
│                              │Деплой у Prod │             │
│                              └──────────────┘             │
│                                                             │
│  БЕЗПЕРЕРВНЕ РОЗГОРТАННЯ                                    │
│  "Кожна зміна одразу потрапляє у продакшн"                │
│  (Те саме, що вище, але без кроку ручного підтвердження)  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Етапи CI конвеєра

### 1. Джерело

```yaml
# Trigger on code push
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

### 2. Збірка

```yaml
# Build the application
steps:
  - name: Build
    run: |
      npm install
      npm run build
```

### 3. Тестування

```yaml
# Run all tests
steps:
  - name: Unit Tests
    run: npm test

  - name: Integration Tests
    run: npm run test:integration

  - name: Lint
    run: npm run lint
```

### 4. Сканування безпеки

```yaml
# Scan for vulnerabilities
steps:
  - name: Security Scan
    run: |
      npm audit
      trivy fs .
```

### 5. Збірка образу

```yaml
# Create container image
steps:
  - name: Build Docker Image
    run: |
      docker build -t myapp:${{ github.sha }} .
      docker push myapp:${{ github.sha }}
```

---

## Огляд інструментів CI/CD

```
┌─────────────────────────────────────────────────────────────┐
│              ІНСТРУМЕНТИ CI/CD                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ХМАРНІ (SaaS)                                              │
│  ├── GitHub Actions     (інтегровано з GitHub)              │
│  ├── GitLab CI/CD       (інтегровано з GitLab)              │
│  ├── CircleCI           (хмарний, швидкий)                  │
│  └── Travis CI          (дружній до open source)            │
│                                                             │
│  САМОСТІЙНЕ РОЗГОРТАННЯ                                     │
│  ├── Jenkins            (найгнучкіший, найстаріший)        │
│  ├── GitLab Runner      (self-hosted GitLab CI)             │
│  ├── Drone              (контейнер-орієнтований)            │
│  └── Tekton             (Kubernetes-нативний)               │
│                                                             │
│  KUBERNETES-НАТИВНІ                                         │
│  ├── Tekton             (конвеєри як CRD)                   │
│  ├── Argo Workflows     (оркестрація робочих процесів)      │
│  └── JenkinsX           (Jenkins для K8s)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## GitHub Actions (найпопулярніший)

### Базовий робочий процес

```yaml
# .github/workflows/ci.yaml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Run lint
        run: npm run lint

  build:
    needs: test  # Only run if tests pass
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Push image
        run: |
          docker tag myapp:${{ github.sha }} ghcr.io/${{ github.repository }}:${{ github.sha }}
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### Ключові концепції

| Концепція | Опис |
|-----------|------|
| `workflow` | Налаштовуваний автоматизований процес |
| `job` | Набір кроків, що виконуються на одному раннері |
| `step` | Окреме завдання (команда або дія) |
| `action` | Повторно використовуваний блок коду |
| `runner` | Машина, що виконує робочий процес |
| `secrets` | Зашифровані змінні середовища |

---

## GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  image: node:20
  script:
    - npm ci
    - npm test
    - npm run lint
  cache:
    paths:
      - node_modules/

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $DOCKER_IMAGE .
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $DOCKER_IMAGE
  only:
    - main

deploy_staging:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$DOCKER_IMAGE
  environment:
    name: staging
  only:
    - main

deploy_production:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$DOCKER_IMAGE
  environment:
    name: production
  when: manual  # Requires click to deploy
  only:
    - main
```

---

## Конвеєр для Kubernetes

Типовий CI/CD конвеєр для Kubernetes:

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD КОНВЕЄР ДЛЯ KUBERNETES                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. КОД                                                     │
│     └── Розробник пушить у Git                             │
│                                                             │
│  2. ЗБІРКА                                                  │
│     ├── Запуск модульних тестів                             │
│     ├── Запуск інтеграційних тестів                         │
│     ├── Статичний аналіз (lint, безпека)                   │
│     └── Збірка образу контейнера                           │
│                                                             │
│  3. ПУБЛІКАЦІЯ                                              │
│     ├── Тегування образу SHA комміту                       │
│     ├── Пуш до реєстру контейнерів                         │
│     └── Сканування образу на вразливості                   │
│                                                             │
│  4. ОНОВЛЕННЯ МАНІФЕСТІВ                                    │
│     └── Оновлення Kubernetes YAML з новим тегом образу     │
│         (Для GitOps: коміт до GitOps-репозиторію)          │
│                                                             │
│  5. РОЗГОРТАННЯ                                             │
│     ├── GitOps: агент виявляє зміну і синхронізує          │
│     └── Або: конвеєр застосовує kubectl/helm               │
│                                                             │
│  6. ПЕРЕВІРКА                                               │
│     ├── Smoke-тести розгорнутого застосунку                │
│     └── Відкат у разі невдачі                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Повний приклад

```yaml
# .github/workflows/kubernetes.yaml
name: Kubernetes CI/CD

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go test ./...

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  update-manifests:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: myorg/gitops-repo
          token: ${{ secrets.GITOPS_TOKEN }}

      - name: Update image tag
        run: |
          cd apps/myapp
          kustomize edit set image myapp=${{ needs.build-and-push.outputs.image-tag }}

      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Update myapp to ${{ github.sha }}"
          git push
```

---

## Найкращі практики для конвеєрів

### 1. Швидкий зворотний зв'язок

```yaml
# Run quick checks first
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: npm run lint  # Fast, catches obvious issues

  unit-test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test      # Medium speed

  integration-test:
    needs: [lint, unit-test]  # Only if fast checks pass
    runs-on: ubuntu-latest
    steps:
      - run: npm run test:e2e  # Slow, but important
```

### 2. Кешування залежностей

```yaml
- name: Cache node modules
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### 3. Матричні збірки

```yaml
# Test on multiple versions
jobs:
  test:
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test
```

### 4. Захист секретів

```yaml
# Never echo secrets!
- name: Deploy
  env:
    KUBE_CONFIG: ${{ secrets.KUBECONFIG }}
  run: |
    echo "$KUBE_CONFIG" | base64 -d > kubeconfig
    kubectl --kubeconfig=kubeconfig apply -f manifests/
    rm kubeconfig  # Clean up
```

---

## Антипатерни CI/CD

| Антипатерн | Проблема | Рішення |
|------------|----------|---------|
| Ручні кроки | Людські помилки, повільно | Автоматизуйте все |
| Нестабільні тести | Ігнорування збоїв, втрата довіри | Виправте або видаліть нестабільні тести |
| Довгі конвеєри | Повільний зворотний зв'язок | Паралелізуйте, кешуйте |
| Деплой з ноутбука | Немає журналу аудиту | Завжди деплойте через конвеєр |
| Спільні облікові дані | Ризик безпеки | Окремі сервісні акаунти для кожного середовища |
| Немає плану відкату | Застрягнете зі зламаним релізом | Автоматизуйте відкат |

---

## Чи знали ви?

- **Jenkins понад 20 років** (розпочався як Hudson у 2004 році). Попри свій вік, він досі обслуговує мільйони конвеєрів щодня.

- **Раннери GitHub Actions** — це свіжі віртуальні машини для кожного завдання. Ви щоразу отримуєте чисте середовище, що запобігає проблемам «у мене на машині працює».

- **Найбільша CI система у світі** належить Google. Вона виконує мільйони збірок на день на розподіленій інфраструктурі тестування під назвою TAP (Test Automation Platform).

---

## Типові помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Тести всередині Docker-збірки | Повільні збірки, кешовані помилки тестів | Розділіть етапи тестування та збірки |
| Тег latest для базових образів | Непередбачувані збірки | Фіксуйте версії |
| Відсутність валідації YAML | Помилки під час виконання | Додайте крок валідації |
| Довготривалі гілки фіч | Конфлікти злиття | Короткі гілки, часті злиття |
| Пропуск CI для «малих змін» | Дрібні баги проковзують | CI для всього |

---

## Тест

1. **Яка різниця між Continuous Delivery та Continuous Deployment?**
   <details>
   <summary>Відповідь</summary>
   Continuous Delivery: кожна зміна готова до розгортання, але деплой у продакшн потребує ручного підтвердження. Continuous Deployment: кожна зміна автоматично потрапляє у продакшн (без ручного кроку).
   </details>

2. **Чому слід тегувати образи контейнерів SHA комміту замість «latest»?**
   <details>
   <summary>Відповідь</summary>
   SHA комміту забезпечує відстежуваність (точно знаєте, який код працює), дає змогу відкотити (розгорнути попередній SHA) та запобігає проблемам із кешуванням («latest» може бути кешований як стара версія).
   </details>

3. **Яке призначення кешування в CI конвеєрах?**
   <details>
   <summary>Відповідь</summary>
   Кешування повторно використовує витратні операції (наприклад, завантаження залежностей) між запусками конвеєра. Це значно прискорює конвеєри — часто з 10+ хвилин до 1–2 хвилин.
   </details>

4. **Як CI/CD інтегрується з GitOps?**
   <details>
   <summary>Відповідь</summary>
   CI збирає та пушить образи. Потім CI оновлює GitOps-репозиторій з новим тегом образу. GitOps-агент виявляє зміну та синхронізує з кластером. CI не взаємодіє з кластером напряму.
   </details>

---

## Практична вправа

**Завдання**: Створіть локальну симуляцію CI.

```bash
# This simulates what a CI pipeline does

# 1. Create project structure
mkdir -p ~/ci-demo
cd ~/ci-demo

# 2. Create a simple app
cat << 'EOF' > app.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

if __name__ == "__main__":
    print("Hello from CI demo!")
EOF

# 3. Create tests
cat << 'EOF' > test_app.py
import app

def test_add():
    assert app.add(2, 3) == 5

def test_subtract():
    assert app.subtract(5, 3) == 2
EOF

# 4. Create Dockerfile
cat << 'EOF' > Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
EOF

# 5. Simulate CI stages

echo "=== STAGE: Lint ==="
# In real CI: run linter
python3 -m py_compile app.py && echo "Lint passed!"

echo ""
echo "=== STAGE: Test ==="
# In real CI: pytest
pip3 install pytest -q 2>/dev/null
python3 -m pytest test_app.py -v

echo ""
echo "=== STAGE: Build ==="
# Build image
docker build -t ci-demo:$(git rev-parse --short HEAD 2>/dev/null || echo "local") .

echo ""
echo "=== STAGE: Security Scan ==="
# In real CI: trivy, snyk, etc.
echo "Scanning image... (simulated)"
echo "No vulnerabilities found!"

echo ""
echo "=== STAGE: Push ==="
echo "Would push to: registry/ci-demo:$(git rev-parse --short HEAD 2>/dev/null || echo "local")"
echo "(Skipping actual push for demo)"

# 6. Cleanup
cd ..
rm -rf ~/ci-demo

echo ""
echo "=== CI Pipeline Complete ==="
```

**Критерії успіху**: Зрозуміти етапи CI конвеєра.

---

## Підсумок

**CI/CD конвеєри** автоматизують шлях від коду до продакшну:

**CI (Безперервна інтеграція)**:
- Зливайте часто
- Збирайте та тестуйте кожну зміну
- Виявляйте проблеми рано

**CD (Безперервна доставка/розгортання)**:
- Завжди готовий до розгортання
- Автоматизований деплой
- Швидкий відкат

**Ключові практики**:
- Швидкий зворотний зв'язок (швидкі етапи першими)
- Кешування залежностей
- Захист секретів
- Незмінні артефакти (образи з тегами SHA)

**Для Kubernetes**:
- CI збирає та пушить образи
- Конвеєр оновлює маніфести (або GitOps-репозиторій)
- Розгортання виконується через kubectl/helm або GitOps-агент

---

## Наступний модуль

[Модуль 4: Основи спостережуваності](module-1.4-observability/) — Моніторинг, журналювання та трейсинг.
