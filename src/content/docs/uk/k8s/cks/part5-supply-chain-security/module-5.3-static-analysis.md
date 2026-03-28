---
title: "Модуль 5.3: Статичний аналіз з kubesec та OPA"
slug: uk/k8s/cks/part5-supply-chain-security/module-5.3-static-analysis
sidebar:
  order: 3
---
> **Складність**: `[MEDIUM]` — інструменти безпеки
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Модуль 5.2 (Сканування образів), основи маніфестів Kubernetes

---

## Чому цей модуль важливий

Статичний аналіз досліджує маніфести Kubernetes до розгортання, виявляючи помилки конфігурації на ранніх етапах. Інструменти на кшталт kubesec оцінюють рівень безпеки, тоді як OPA Gatekeeper застосовує політики під час допуску.

CKS тестує як ad-hoc аналіз (kubesec), так і застосування політик (OPA).

---

## Огляд статичного аналізу

```
┌─────────────────────────────────────────────────────────────┐
│              КОНВЕЄР СТАТИЧНОГО АНАЛІЗУ                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Розробник пише YAML                                       │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Статичний аналіз (Pre-commit/CI)                   │   │
│  │  ├── kubesec (оцінка безпеки)                      │   │
│  │  ├── Trivy (помилки конфігурації)                  │   │
│  │  ├── kube-linter (найкращі практики)               │   │
│  │  └── Checkov (політика як код)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Контролери допуску (під час розгортання)           │   │
│  │  ├── OPA Gatekeeper                                 │   │
│  │  ├── Kyverno                                        │   │
│  │  └── Pod Security Admission                         │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  Kubernetes API Server приймає/відхиляє                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## kubesec

kubesec аналізує маніфести Kubernetes та призначає оцінку безпеки.

### Встановлення

```bash
# Download binary
wget https://github.com/controlplaneio/kubesec/releases/download/v2.13.0/kubesec_linux_amd64.tar.gz
tar -xzf kubesec_linux_amd64.tar.gz
sudo mv kubesec /usr/local/bin/

# Or use Docker
docker run -i kubesec/kubesec:v2 scan /dev/stdin < pod.yaml

# Or use online API
curl -sSX POST --data-binary @pod.yaml https://v2.kubesec.io/scan
```

### Базове використання

```bash
# Scan a file
kubesec scan pod.yaml

# Scan from stdin
cat pod.yaml | kubesec scan -

# Scan multiple files
kubesec scan deployment.yaml service.yaml
```

### Розуміння виводу kubesec

```json
[
  {
    "object": "Pod/insecure-pod.default",
    "valid": true,
    "score": -30,
    "scoring": {
      "critical": [
        {
          "selector": "containers[] .securityContext .privileged == true",
          "reason": "Privileged containers can allow almost completely unrestricted host access",
          "points": -30
        }
      ],
      "advise": [
        {
          "selector": "containers[] .securityContext .runAsNonRoot == true",
          "reason": "Force the running image to run as a non-root user",
          "points": 1
        },
        {
          "selector": ".spec .serviceAccountName",
          "reason": "Service accounts restrict Kubernetes API access",
          "points": 3
        }
      ]
    }
  }
]
```

### Система оцінювання kubesec

```
┌─────────────────────────────────────────────────────────────┐
│              ОЦІНЮВАННЯ KUBESEC                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  КРИТИЧНІ (від'ємні бали):                                 │
│  ─────────────────────────────────────────────────────────  │
│  • privileged: true                    → -30 балів         │
│  • hostNetwork: true                   → -9 балів          │
│  • hostPID: true                       → -9 балів          │
│  • hostIPC: true                       → -9 балів          │
│  • capabilities.add: SYS_ADMIN         → -30 балів         │
│                                                             │
│  ПОЗИТИВНІ (покращення безпеки):                           │
│  ─────────────────────────────────────────────────────────  │
│  • runAsNonRoot: true                  → +1 бал            │
│  • runAsUser > 10000                   → +1 бал            │
│  • readOnlyRootFilesystem: true        → +1 бал            │
│  • capabilities.drop: ALL              → +1 бал            │
│  • resources.limits.cpu                → +1 бал            │
│  • resources.limits.memory             → +1 бал            │
│                                                             │
│  Оцінка > 0: Загалом прийнятно                             │
│  Оцінка < 0: Є критичні проблеми                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Приклади kubesec

### Небезпечний Pod

```yaml
# insecure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
```

```bash
kubesec scan insecure-pod.yaml
# Score: -30 (CRITICAL: privileged container)
```

### Безпечний Pod

```yaml
# secure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
```

```bash
kubesec scan secure-pod.yaml
# Score: 7+ (multiple security best practices)
```

---

## KubeLinter

KubeLinter — це інструмент статичного аналізу, що перевіряє маніфести Kubernetes на відповідність найкращим практикам та поширеним помилкам конфігурації. Він швидший та більш категоричний, ніж kubesec, зосереджений на безпеці розгортання.

```bash
# Install
curl -sL https://github.com/stackrox/kube-linter/releases/latest/download/kube-linter-linux -o kube-linter
chmod +x kube-linter

# Lint a manifest
./kube-linter lint deployment.yaml

# Lint an entire directory
./kube-linter lint manifests/

# List all available checks
./kube-linter checks list
```

KubeLinter виявляє проблеми як:
- Контейнери, що працюють від root
- Відсутні ліміти ресурсів
- Відсутні проби готовності/життєздатності
- Записувані кореневі файлові системи
- Привілейовані контейнери
- Відсутні мережеві політики

```bash
# Example output
deployment.yaml: (object: default/nginx apps/v1, Kind=Deployment)
  - container "nginx" does not have a read-only root file system
    (check: no-read-only-root-fs, remediation: Set readOnlyRootFilesystem to true)
  - container "nginx" has cpu limit 0 (check: unset-cpu-requirements)
  - container "nginx" is not set to runAsNonRoot (check: run-as-non-root)
```

> **kubesec проти KubeLinter**: kubesec оцінює загальний рівень безпеки (добре для аудитів). KubeLinter виявляє конкретні проблеми з конкретними рекомендаціями (добре для CI конвеєрів). Використовуйте обидва.

---

## OPA Gatekeeper

Open Policy Agent (OPA) Gatekeeper забезпечує застосування політик під час допуску.

### Архітектура

```
┌─────────────────────────────────────────────────────────────┐
│              АРХІТЕКТУРА OPA GATEKEEPER                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl apply -f pod.yaml                                 │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Kubernetes API Server                     │   │
│  │                    │                                 │   │
│  │           ValidatingWebhook                         │   │
│  │                    │                                 │   │
│  └────────────────────┼────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              OPA Gatekeeper                          │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  ConstraintTemplate (визначає політику)      │    │   │
│  │  │  напр., "K8sRequiredLabels"                  │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Constraint (застосовує політику)            │    │   │
│  │  │  напр., "require label: team"                │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│              Дозволити або відхилити запит                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Встановлення Gatekeeper

```bash
# Install using kubectl
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

# Verify installation
kubectl get pods -n gatekeeper-system
kubectl get crd | grep gatekeeper
```

### Створення політики

#### Крок 1: ConstraintTemplate

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels

        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }
```

#### Крок 2: Constraint

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-label
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production"]
  parameters:
    labels: ["team", "app"]
```

### Тестування політики

```bash
# This pod will be rejected
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: unlabeled-pod
  namespace: production
spec:
  containers:
  - name: nginx
    image: nginx
EOF
# Error: Missing required labels: {"app", "team"}

# This pod will be allowed
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: labeled-pod
  namespace: production
  labels:
    team: platform
    app: web
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

---

## Поширені політики Gatekeeper

### Блокування привілейованих контейнерів

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblockprivileged
spec:
  crd:
    spec:
      names:
        kind: K8sBlockPrivileged
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblockprivileged

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          container.securityContext.privileged == true
          msg := sprintf("Privileged container not allowed: %v", [container.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockPrivileged
metadata:
  name: block-privileged-containers
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
```

### Вимога Non-Root

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirenonroot
spec:
  crd:
    spec:
      names:
        kind: K8sRequireNonRoot
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirenonroot

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot
          msg := sprintf("Container must set runAsNonRoot: %v", [container.name])
        }
```

### Блокування тегу :latest

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblocklatesttag
spec:
  crd:
    spec:
      names:
        kind: K8sBlockLatestTag
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblocklatesttag

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          endswith(container.image, ":latest")
          msg := sprintf("Image with :latest tag not allowed: %v", [container.image])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not contains(container.image, ":")
          msg := sprintf("Image without tag (defaults to :latest) not allowed: %v", [container.image])
        }
```

---

## Реальні сценарії іспиту

### Сценарій 1: Сканування Pod з kubesec

```bash
# Create test pod
cat <<EOF > test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      privileged: true
EOF

# Scan with kubesec
kubesec scan test-pod.yaml

# Fix the pod based on kubesec recommendations
cat <<EOF > test-pod-fixed.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: nginx
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
EOF

kubesec scan test-pod-fixed.yaml
# Score should be positive now
```

### Сценарій 2: Створення політики Gatekeeper

```bash
# Create ConstraintTemplate
cat <<EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirelimits
spec:
  crd:
    spec:
      names:
        kind: K8sRequireLimits
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirelimits

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.memory
          msg := sprintf("Container must have memory limits: %v", [container.name])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.cpu
          msg := sprintf("Container must have CPU limits: %v", [container.name])
        }
EOF

# Create Constraint
cat <<EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireLimits
metadata:
  name: require-resource-limits
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production"]
EOF

# Test - this should fail
kubectl run test --image=nginx -n production
# Error: Container must have memory limits

# Test - this should succeed
kubectl run test --image=nginx -n production \
  --limits='memory=128Mi,cpu=500m'
```

### Сценарій 3: Аудит наявних порушень

```bash
# Check constraint status for violations
kubectl get k8srequiredlabels require-team-label -o yaml

# Look at the status.violations section
kubectl get constraints -A -o json | \
  jq '.items[] | {name: .metadata.name, violations: .status.totalViolations}'
```

---

## Чи знали ви?

- **kubesec був створений Control Plane** (раніше Aqua) і спеціально розроблений для оцінювання безпеки Kubernetes.

- **OPA використовує Rego** — спеціально створену мову політик. Вона декларативна та призначена для вираження складних політик контролю доступу.

- **Gatekeeper працює як ValidatingAdmissionWebhook**, що означає, що він може лише дозволяти або відхиляти запити — він не може їх змінювати. Для мутації використовуйте MutatingAdmissionWebhooks.

- **Gatekeeper підтримує режим аудиту**, який повідомляє про порушення без їх блокування. Чудово підходить для поступового впровадження нових політик.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Ігнорування попереджень kubesec | Розгортання мають відомі проблеми | Виправляйте критичні знахідки |
| Складні політики Rego | Важко налагоджувати | Почніть просто, ретельно тестуйте |
| Без винятків | Системні Pod блокуються | Використовуйте match.excludedNamespaces |
| Забутий режим аудиту | Порушення не застосовуються | Переведіть у enforce після тестування |
| Відсутні повідомлення про помилки | Користувачі плутаються | Додайте зрозумілі повідомлення про порушення |

---

## Тест

1. **Що означає від'ємна оцінка kubesec?**
   <details>
   <summary>Відповідь</summary>
   Від'ємна оцінка вказує на критичні проблеми безпеки, такі як привілейовані контейнери, hostNetwork або небезпечні capabilities. Ці проблеми потрібно виправити негайно.
   </details>

2. **Які два ресурси потрібні для створення політики Gatekeeper?**
   <details>
   <summary>Відповідь</summary>
   ConstraintTemplate (визначає логіку політики в Rego) та Constraint (застосовує політику до конкретних ресурсів). Шаблон багаторазовий, а constraints параметризують його.
   </details>

3. **Як тестувати політики Gatekeeper без блокування розгортань?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте режим аудиту, встановивши `enforcementAction: dryrun` на Constraint. Порушення записуються, але не блокуються.
   </details>

4. **Яку мову використовує OPA Gatekeeper для політик?**
   <details>
   <summary>Відповідь</summary>
   Rego — декларативна мова запитів, спеціально розроблена для вираження політик над складними ієрархічними даними.
   </details>

---

## Практична вправа

**Завдання**: Використати kubesec та створити політику Gatekeeper.

```bash
# Part 1: kubesec Analysis

# Create insecure pod
cat <<EOF > insecure.yaml
apiVersion: v1
kind: Pod
metadata:
  name: insecure
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true
EOF

# Scan with kubesec (using API if not installed locally)
echo "=== kubesec Scan (Insecure) ==="
curl -sSX POST --data-binary @insecure.yaml https://v2.kubesec.io/scan | jq '.[0].score'

# Create secure version
cat <<EOF > secure.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
EOF

echo "=== kubesec Scan (Secure) ==="
curl -sSX POST --data-binary @secure.yaml https://v2.kubesec.io/scan | jq '.[0].score'

# Part 2: Gatekeeper Policy (if Gatekeeper is installed)

# Check if Gatekeeper is installed
if kubectl get crd constrainttemplates.templates.gatekeeper.sh &>/dev/null; then
  echo "=== Creating Gatekeeper Policy ==="

  # Create ConstraintTemplate
  cat <<EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblockdefaultnamespace
spec:
  crd:
    spec:
      names:
        kind: K8sBlockDefaultNamespace
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblockdefaultnamespace
        violation[{"msg": msg}] {
          input.review.object.metadata.namespace == "default"
          msg := "Deployments to default namespace are not allowed"
        }
EOF

  # Create Constraint in dryrun mode
  cat <<EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockDefaultNamespace
metadata:
  name: block-default-namespace
spec:
  enforcementAction: dryrun
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
EOF

  echo "Policy created in dryrun mode"
else
  echo "Gatekeeper not installed, skipping policy creation"
fi

# Cleanup
rm -f insecure.yaml secure.yaml
```

**Критерії успіху**: Зрозуміти систему оцінювання kubesec та структуру політик Gatekeeper.

---

## Підсумок

**kubesec**:
- Інструмент оцінювання безпеки
- Від'ємна оцінка = критичні проблеми
- Додатна оцінка = найкращі практики безпеки
- Використовуйте в CI/CD конвеєрах

**OPA Gatekeeper**:
- Контролер допуску для політик
- ConstraintTemplate + Constraint
- Мова політик Rego
- Режим аудиту для тестування

**Найкращі практики**:
- Сканувати маніфести перед розгортанням
- Блокувати привілейовані контейнери
- Вимагати ліміти ресурсів
- Спочатку тестувати політики в режимі аудиту

**Поради для іспиту**:
- Знайте синтаксис команд kubesec
- Розумійте CRD Gatekeeper
- Вмійте писати базовий Rego

---

## Наступний модуль

[Модуль 5.4: Контролери допуску](module-5.4-admission-controllers/) — Власний контроль допуску для безпеки.
