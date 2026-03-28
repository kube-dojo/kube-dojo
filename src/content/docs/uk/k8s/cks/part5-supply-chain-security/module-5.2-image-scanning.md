---
title: "Модуль 5.2: Сканування образів з Trivy"
slug: uk/k8s/cks/part5-supply-chain-security/module-5.2-image-scanning
sidebar:
  order: 2
---
> **Складність**: `[MEDIUM]` — критична навичка CKS
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Модуль 5.1 (Безпека образів), основи Docker

---

## Чому цей модуль важливий

Образи контейнерів часто містять вразливі пакети, якими можуть скористатися зловмисники. Сканування образів виявляє відомі вразливості (CVE) до того, як образи потраплять у продакшен. Trivy є стандартом де-факто для сканування безпеки контейнерів.

CKS перевіряє вашу здатність сканувати образи та інтерпретувати звіти про вразливості.

---

## Що таке Trivy?

```
┌─────────────────────────────────────────────────────────────┐
│              ОГЛЯД TRIVY                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Trivy = Універсальний сканер безпеки                      │
│  ─────────────────────────────────────────────────────────  │
│  • Відкритий код (Aqua Security)                           │
│  • Швидкий та точний                                       │
│  • Простий у використанні                                  │
│  • Працює офлайн (після початкового завантаження БД)       │
│                                                             │
│  Що сканує Trivy:                                          │
│  ├── Образи контейнерів                                    │
│  ├── Маніфести Kubernetes                                  │
│  ├── Terraform/CloudFormation                              │
│  ├── Git-репозиторії                                       │
│  └── Файлові системи                                       │
│                                                             │
│  Що знаходить Trivy:                                       │
│  ├── Вразливості пакетів ОС (CVE)                         │
│  ├── Залежності мов (npm, pip, gem)                        │
│  ├── Помилки конфігурації IaC                              │
│  ├── Секрети в коді                                        │
│  └── Проблеми відповідності ліцензій                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Встановлення Trivy

```bash
# Debian/Ubuntu
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install trivy

# macOS
brew install trivy

# Binary download
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
trivy --version
```

---

## Базове сканування образів

### Сканування образу контейнера

```bash
# Basic scan
trivy image nginx:1.25

# Scan with specific severity filter
trivy image --severity HIGH,CRITICAL nginx:1.25

# Scan and exit with error if vulnerabilities found
trivy image --exit-code 1 --severity CRITICAL nginx:1.25

# Scan local image (not from registry)
trivy image --input myimage.tar
```

### Розуміння виводу

```
nginx:1.25 (debian 12.2)
=========================
Total: 142 (UNKNOWN: 0, LOW: 85, MEDIUM: 42, HIGH: 12, CRITICAL: 3)

┌──────────────────┬────────────────┬──────────┬─────────────────────┬──────────────────┬─────────────────────────────────────┐
│     Library      │ Vulnerability  │ Severity │  Installed Version  │  Fixed Version   │                Title                │
├──────────────────┼────────────────┼──────────┼─────────────────────┼──────────────────┼─────────────────────────────────────┤
│ libssl3          │ CVE-2024-1234  │ CRITICAL │ 3.0.9-1             │ 3.0.9-2          │ OpenSSL: Remote code execution      │
│ curl             │ CVE-2024-5678  │ HIGH     │ 7.88.1-10           │ 7.88.1-11        │ curl: Buffer overflow in...         │
│ zlib1g           │ CVE-2024-9012  │ MEDIUM   │ 1:1.2.13-1          │                  │ zlib: Memory corruption             │
└──────────────────┴────────────────┴──────────┴─────────────────────┴──────────────────┴─────────────────────────────────────┘
```

---

## Рівні серйозності

```
┌─────────────────────────────────────────────────────────────┐
│              РІВНІ СЕРЙОЗНОСТІ CVE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CRITICAL (CVSS 9.0-10.0)                                  │
│  ─────────────────────────────────────────────────────────  │
│  • Віддалене виконання коду                                │
│  • Автентифікація не потрібна                              │
│  • Потребує негайних дій                                   │
│                                                             │
│  HIGH (CVSS 7.0-8.9)                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Значний вплив                                           │
│  • Може вимагати взаємодії користувача                     │
│  • Потрібно виправити найближчим часом                     │
│                                                             │
│  MEDIUM (CVSS 4.0-6.9)                                     │
│  ─────────────────────────────────────────────────────────  │
│  • Обмежений вплив                                         │
│  • Потребує конкретних умов                                │
│  • Плануйте виправлення                                    │
│                                                             │
│  LOW (CVSS 0.1-3.9)                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Незначний вплив                                         │
│  • Складно експлуатувати                                   │
│  • Виправляйте за зручності                               │
│                                                             │
│  UNKNOWN                                                   │
│  ─────────────────────────────────────────────────────────  │
│  • Оцінка CVSS ще не призначена                           │
│  • Оцінюйте вручну                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Розширені опції сканування

### Формати виводу

```bash
# Table format (default)
trivy image nginx:1.25

# JSON format (for CI/CD parsing)
trivy image --format json nginx:1.25 > results.json

# SARIF format (for GitHub Security)
trivy image --format sarif nginx:1.25 > results.sarif

# Template format
trivy image --format template --template "@contrib/html.tpl" nginx:1.25 > report.html
```

### Фільтрація результатів

```bash
# Only show vulnerabilities with fixes available
trivy image --ignore-unfixed nginx:1.25

# Ignore specific CVEs
trivy image --ignore-cve CVE-2024-1234,CVE-2024-5678 nginx:1.25

# Use .trivyignore file
echo "CVE-2024-1234" >> .trivyignore
trivy image nginx:1.25

# Only scan OS packages (skip language dependencies)
trivy image --vuln-type os nginx:1.25

# Only scan language dependencies
trivy image --vuln-type library node:20
```

### Опції сканування

```bash
# Skip database update (use cached)
trivy image --skip-db-update nginx:1.25

# Download database only (for air-gapped setup)
trivy image --download-db-only

# Scan from specific registry
trivy image --username user --password pass registry.example.com/myimage:1.0

# Scan with timeout
trivy image --timeout 10m large-image:1.0
```

---

## Сканування кластерів Kubernetes

### Сканування запущених навантажень

```bash
# Scan all images in cluster
trivy k8s --report summary cluster

# Scan specific namespace
trivy k8s --namespace production --report summary

# Scan and show all vulnerabilities
trivy k8s --report all --namespace default

# Output as JSON
trivy k8s --format json --output results.json cluster
```

### Сканування маніфестів Kubernetes

```bash
# Scan YAML files for misconfigurations
trivy config deployment.yaml

# Scan entire directory
trivy config ./manifests/

# Scan for both vulnerabilities and misconfigs
trivy fs --security-checks vuln,config ./
```

---

## Сканування на помилки конфігурації

```bash
# Scan Kubernetes manifests
trivy config pod.yaml

# Example misconfiguration output:
# pod.yaml
# ========
# Tests: 23 (SUCCESSES: 18, FAILURES: 5)
# Failures: 5 (UNKNOWN: 0, LOW: 1, MEDIUM: 2, HIGH: 2, CRITICAL: 0)
#
# HIGH: Container 'nginx' of Pod 'web' should set 'securityContext.runAsNonRoot' to true
# HIGH: Container 'nginx' of Pod 'web' should set 'securityContext.allowPrivilegeEscalation' to false
```

### Що перевіряє Trivy у Kubernetes

```
┌─────────────────────────────────────────────────────────────┐
│              ПЕРЕВІРКИ КОНФІГУРАЦІЇ KUBERNETES               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Безпека контейнерів:                                      │
│  ├── Запуск від root                                       │
│  ├── Дозволено підвищення привілеїв                       │
│  ├── Привілейовані контейнери                             │
│  ├── Відсутній securityContext                             │
│  └── Capabilities не скинуто                               │
│                                                             │
│  Управління ресурсами:                                     │
│  ├── Відсутні ліміти ресурсів                             │
│  ├── Відсутні запити ресурсів                             │
│  └── Необмежене використання ресурсів                     │
│                                                             │
│  Безпека мережі:                                           │
│  ├── hostNetwork увімкнено                                 │
│  ├── hostPID увімкнено                                     │
│  └── hostIPC увімкнено                                     │
│                                                             │
│  Безпека RBAC:                                             │
│  ├── Надмірно дозвільні ролі                              │
│  ├── Права з підстановочними знаками                      │
│  └── Прив'язки cluster-admin                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Інтеграція з CI/CD

### GitHub Actions

```yaml
name: Security Scan
on: push

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build image
      run: docker build -t myapp:${{ github.sha }} .

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'myapp:${{ github.sha }}'
        format: 'table'
        exit-code: '1'
        severity: 'CRITICAL,HIGH'
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t myapp:${BUILD_NUMBER} .'
            }
        }
        stage('Scan') {
            steps {
                sh '''
                    trivy image \
                        --exit-code 1 \
                        --severity CRITICAL,HIGH \
                        myapp:${BUILD_NUMBER}
                '''
            }
        }
    }
}
```

---

## Реальні сценарії іспиту

### Сценарій 1: Сканування образу та звіт про критичні CVE

```bash
# Scan image for critical vulnerabilities
trivy image --severity CRITICAL nginx:1.25

# Save report
trivy image --severity CRITICAL,HIGH --format json nginx:1.25 > report.json

# Count critical vulnerabilities
trivy image --severity CRITICAL --format json nginx:1.25 | \
  jq '.Results[].Vulnerabilities | length'
```

### Сценарій 2: Пошук образів без критичних вразливостей

```bash
# Scan multiple images, find one without criticals
for img in nginx:1.25 nginx:1.24 nginx:1.23-alpine; do
  echo "Scanning $img..."
  CRITICALS=$(trivy image --severity CRITICAL --format json --quiet "$img" | \
    jq '[.Results[]?.Vulnerabilities // [] | length] | add')
  echo "$img: $CRITICALS critical vulnerabilities"
done
```

### Сценарій 3: Сканування Deployment Kubernetes

```bash
# Create test deployment
cat <<EOF > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
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
EOF

# Scan for misconfigurations
trivy config deployment.yaml

# Scan image used in deployment
IMG=$(grep "image:" deployment.yaml | awk '{print $2}')
trivy image "$IMG"
```

### Сценарій 4: Генерація звіту лише з виправними вразливостями

```bash
# Show only vulnerabilities with available fixes
trivy image --ignore-unfixed --severity HIGH,CRITICAL nginx:1.25

# This helps prioritize what can actually be patched
```

---

## База даних Trivy

```bash
# Trivy vulnerability database location
ls ~/.cache/trivy/

# Update database
trivy image --download-db-only

# Check database freshness
trivy image --skip-db-update nginx:1.25  # Uses cached DB

# For air-gapped environments
# 1. Download on internet-connected machine
trivy image --download-db-only
# 2. Copy ~/.cache/trivy/db to air-gapped machine
# 3. Run with --skip-db-update
```

---

## Чи знали ви?

- **Trivy може сканувати образи контейнерів без Docker**, використовуючи containerd або аналізуючи tarball-файли образів безпосередньо.

- **База даних вразливостей оновлюється щодня**. Для продакшен CI/CD розгляньте кешування бази даних, щоб уникнути обмежень швидкості.

- **Trivy використовує кілька баз даних вразливостей**: NVD, Red Hat OVAL, Debian Security Tracker, Alpine SecDB та інші.

- **Trivy може виявляти секрети**, такі як ключі API, паролі та сертифікати, випадково включені в образи або код.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| Ігнорування HIGH серйозності | Можуть бути експлуатовані | Встановити поріг HIGH,CRITICAL |
| Стара база даних вразливостей | Пропуск нових CVE | Оновлювати БД у CI/CD |
| Сканування тільки при збірці | Дрейф з часом | Регулярні планові сканування |
| Не виправляти виправні CVE | Пропущені легкі перемоги | Спочатку --ignore-unfixed |
| Сканування з :latest | Результати змінюються | Використовуйте конкретні теги |

---

## Тест

1. **Яка команда сканує образ лише на CRITICAL та HIGH вразливості?**
   <details>
   <summary>Відповідь</summary>
   `trivy image --severity CRITICAL,HIGH <image>`. Прапорець --severity фільтрує результати, показуючи лише вказані рівні серйозності.
   </details>

2. **Як зробити, щоб CI/CD конвеєр завершувався з помилкою при знайдених критичних вразливостях?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте `trivy image --exit-code 1 --severity CRITICAL <image>`. Прапорець --exit-code 1 змушує trivy повертати код виходу 1, якщо знайдені вразливості, що відповідають критеріям.
   </details>

3. **Як сканувати лише вразливості, для яких є виправлення?**
   <details>
   <summary>Відповідь</summary>
   Використовуйте `trivy image --ignore-unfixed <image>`. Це фільтрує вразливості, для яких немає виправленої версії.
   </details>

4. **Що робить trivy config?**
   <details>
   <summary>Відповідь</summary>
   `trivy config` сканує файли конфігурації (маніфести Kubernetes, Terraform, Dockerfile тощо) на помилки конфігурації безпеки, а не CVE.
   </details>

---

## Практична вправа

**Завдання**: Сканувати образи та виявити проблеми безпеки.

```bash
# Step 1: Update Trivy database
trivy image --download-db-only

# Step 2: Scan nginx:latest for all vulnerabilities
echo "=== Full Scan of nginx:latest ==="
trivy image nginx:latest 2>/dev/null | head -30

# Step 3: Count vulnerabilities by severity
echo "=== Vulnerability Count ==="
trivy image --format json nginx:latest 2>/dev/null | \
  jq -r '.Results[].Vulnerabilities[]?.Severity' | sort | uniq -c

# Step 4: Find only CRITICAL with fixes
echo "=== Critical Vulnerabilities with Fixes ==="
trivy image --severity CRITICAL --ignore-unfixed nginx:latest

# Step 5: Compare with Alpine version
echo "=== Alpine Version Comparison ==="
trivy image --severity CRITICAL,HIGH nginx:alpine 2>/dev/null | head -20

# Step 6: Scan a Kubernetes manifest
cat <<EOF > test-pod.yaml
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

echo "=== Kubernetes Manifest Scan ==="
trivy config test-pod.yaml

# Step 7: Generate JSON report
trivy image --format json --output scan-report.json nginx:latest
echo "Report saved to scan-report.json"

# Cleanup
rm -f test-pod.yaml scan-report.json
```

**Критерії успіху**: Зрозуміти, як сканувати образи та інтерпретувати результати.

---

## Підсумок

**Основи Trivy**:
- `trivy image <name>` — Сканування образу контейнера
- `trivy config <file>` — Сканування конфігурацій
- `trivy k8s cluster` — Сканування Kubernetes

**Ключові прапорці**:
- `--severity CRITICAL,HIGH` — Фільтрація за серйозністю
- `--exit-code 1` — Збій CI/CD якщо знайдено
- `--ignore-unfixed` — Тільки виправні CVE
- `--format json` — Машиночитаний вивід

**Пріоритет серйозності**:
1. CRITICAL — Негайні дії
2. HIGH — Виправити найближчим часом
3. MEDIUM — Планувати виправлення
4. LOW — За зручності

**Поради для іспиту**:
- Знайте базові команди trivy
- Розумійте фільтрацію за серйозністю
- Вмійте аналізувати вивід сканування
- Знайте, як сканувати маніфести Kubernetes

---

## Наступний модуль

[Модуль 5.3: Статичний аналіз](module-5.3-static-analysis/) — Аналіз маніфестів Kubernetes на проблеми безпеки.
