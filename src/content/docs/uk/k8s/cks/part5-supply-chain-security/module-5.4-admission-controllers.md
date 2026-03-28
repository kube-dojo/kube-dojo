---
title: "Модуль 5.4: Контролери допуску"
slug: uk/k8s/cks/part5-supply-chain-security/module-5.4-admission-controllers
sidebar:
  order: 4
---
> **Складність**: `[MEDIUM]` — критична тема CKS
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Модуль 5.3 (Статичний аналіз), основи API server

---

## Чому цей модуль важливий

Контролери допуску — це охоронці, що перехоплюють API-запити до збереження об'єктів. Вони можуть валідувати, мутувати або відхиляти запити на основі власної логіки. Розуміння того, як увімкнути та налаштувати контролери допуску, є необхідним для безпеки кластера.

CKS тестує конфігурацію та використання контролерів допуску.

---

## Потік контролера допуску

```
┌─────────────────────────────────────────────────────────────┐
│              КОНВЕЄР КОНТРОЛЕРІВ ДОПУСКУ                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl create/apply                                       │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Автентифікація (хто це?)                           │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Авторизація (чи може це зробити?)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Мутуючий допуск (змінити запит)                    │   │
│  │  ├── MutatingAdmissionWebhook                       │   │
│  │  ├── DefaultStorageClass                            │   │
│  │  └── PodPreset (deprecated)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Валідуючий допуск (дозволити/відхилити)            │   │
│  │  ├── ValidatingAdmissionWebhook                     │   │
│  │  ├── PodSecurity (PSA)                              │   │
│  │  └── ResourceQuota                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  etcd (зберегти об'єкт)                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Вбудовані контролери допуску

### Критичні для безпеки контролери

```
┌─────────────────────────────────────────────────────────────┐
│              КОНТРОЛЕРИ ДОПУСКУ БЕЗПЕКИ                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PodSecurity (Kubernetes 1.25+)                            │
│  └── Застосовує стандарти безпеки Pod                      │
│      Замінив PodSecurityPolicy                             │
│                                                             │
│  NodeRestriction                                           │
│  └── Обмежує те, що можуть змінювати kubelet              │
│      Запобігає впливу скомпрометованих вузлів на інших    │
│                                                             │
│  AlwaysPullImages                                          │
│  └── Примусово завантажує образ при кожному запуску Pod    │
│      Запобігає використанню кешованих шкідливих образів    │
│                                                             │
│  ImagePolicyWebhook                                        │
│  └── Зовнішня перевірка образів                            │
│      Може блокувати непідписані або вразливі образи       │
│                                                             │
│  DenyServiceExternalIPs                                    │
│  └── Блокує Service externalIPs                            │
│      Запобігає атакам CVE-2020-8554                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Перевірка увімкнених контролерів

```bash
# On kubeadm clusters
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep enable-admission-plugins

# Or via API
kubectl get pod kube-apiserver-<node> -n kube-system -o yaml | \
  grep enable-admission-plugins
```

### Увімкнення додаткових контролерів

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    - --enable-admission-plugins=NodeRestriction,PodSecurity,AlwaysPullImages
    # Other flags...
```

---

## ValidatingAdmissionWebhook

ValidatingAdmissionWebhook викликає зовнішні сервіси для валідації запитів.

### Архітектура вебхука

```
┌─────────────────────────────────────────────────────────────┐
│              ПОТІК ВАЛІДУЮЧОГО ВЕБХУКА                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl apply -f pod.yaml                                 │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Kubernetes API Server                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         │  AdmissionReview запит (JSON)                    │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Сервіс вебхука (HTTPS)                      │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Валідація запиту                           │    │   │
│  │  │  • Перевірка підписів образів               │    │   │
│  │  │  • Перевірка контексту безпеки              │    │   │
│  │  │  • Власна бізнес-логіка                     │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         │  AdmissionReview відповідь                       │
│         │  { "allowed": true/false, "status": {...} }     │
│         ▼                                                   │
│  API Server дозволяє або відхиляє запит                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Створення ValidatingWebhookConfiguration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-validator
webhooks:
- name: pod-validator.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  clientConfig:
    service:
      name: pod-validator
      namespace: security
      path: /validate
    caBundle: <base64-encoded-ca-cert>
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["pods"]
  failurePolicy: Fail  # Fail or Ignore
  matchPolicy: Equivalent
  namespaceSelector:
    matchLabels:
      validate-pods: "true"
```

### Ключові опції конфігурації

```yaml
# failurePolicy: Що станеться, якщо вебхук недоступний
failurePolicy: Fail    # Reject request (secure but may block cluster)
failurePolicy: Ignore  # Allow request (less secure but more available)

# sideEffects: Чи має вебхук побічні ефекти?
sideEffects: None      # Safe to call multiple times
sideEffects: Unknown   # May have side effects

# timeoutSeconds: Скільки чекати на відповідь
timeoutSeconds: 10     # Default is 10 seconds

# namespaceSelector: До яких просторів імен застосовувати
namespaceSelector:
  matchLabels:
    env: production

# objectSelector: Які об'єкти валідувати
objectSelector:
  matchLabels:
    validate: "true"
```

---

## ImagePolicyWebhook

ImagePolicyWebhook валідує назви образів до створення Pod.

### Увімкнення ImagePolicyWebhook

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --enable-admission-plugins=ImagePolicyWebhook
    - --admission-control-config-file=/etc/kubernetes/admission/config.yaml
    volumeMounts:
    - mountPath: /etc/kubernetes/admission
      name: admission-config
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/admission
      type: DirectoryOrCreate
    name: admission-config
```

### Конфігурація ImagePolicyWebhook

```yaml
# /etc/kubernetes/admission/config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: ImagePolicyWebhook
  configuration:
    imagePolicy:
      kubeConfigFile: /etc/kubernetes/admission/kubeconfig
      allowTTL: 50
      denyTTL: 50
      retryBackoff: 500
      defaultAllow: false  # IMPORTANT: Deny by default
```

### kubeconfig для ImagePolicyWebhook

```yaml
# /etc/kubernetes/admission/kubeconfig
apiVersion: v1
kind: Config
clusters:
- name: image-checker
  cluster:
    certificate-authority: /etc/kubernetes/admission/ca.crt
    server: https://image-checker.security.svc:443/check
contexts:
- name: image-checker
  context:
    cluster: image-checker
current-context: image-checker
```

### Запит/Відповідь ImageReview

```json
// Request sent to webhook
{
  "apiVersion": "imagepolicy.k8s.io/v1alpha1",
  "kind": "ImageReview",
  "spec": {
    "containers": [
      {
        "image": "nginx:1.25"
      }
    ],
    "namespace": "production"
  }
}

// Response from webhook
{
  "apiVersion": "imagepolicy.k8s.io/v1alpha1",
  "kind": "ImageReview",
  "status": {
    "allowed": true,
    "reason": "Image signed and scanned"
  }
}
```

---

## MutatingAdmissionWebhook

MutatingWebhook змінює запити перед валідацією.

### Поширені випадки використання

```
┌─────────────────────────────────────────────────────────────┐
│              ВИПАДКИ ВИКОРИСТАННЯ МУТУЮЧОГО ВЕБХУКА          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Впровадження sidecar                                      │
│  └── Додавання контейнерів логування, моніторингу, безпеки │
│      (Istio, Linkerd service mesh)                         │
│                                                             │
│  Додавання типових міток/анотацій                          │
│  └── Автоматичне додавання міток team, cost-center         │
│                                                             │
│  Встановлення типового контексту безпеки                   │
│  └── Додавання runAsNonRoot: true якщо не вказано         │
│                                                             │
│  Додавання imagePullSecrets                                │
│  └── Автоматичне впровадження облікових даних реєстру      │
│                                                             │
│  Зміна запитів ресурсів                                    │
│  └── Встановлення типових memory/CPU якщо не вказано       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### MutatingWebhookConfiguration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: pod-mutator
webhooks:
- name: pod-mutator.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  clientConfig:
    service:
      name: pod-mutator
      namespace: security
      path: /mutate
    caBundle: <base64-encoded-ca-cert>
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  reinvocationPolicy: Never  # or IfNeeded
```

---

## Реальні сценарії іспиту

### Сценарій 1: Увімкнення AlwaysPullImages

```bash
# Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Find or add the --enable-admission-plugins flag
# Add AlwaysPullImages to the list:
# --enable-admission-plugins=NodeRestriction,PodSecurity,AlwaysPullImages

# Wait for API server to restart
kubectl get nodes

# Test: Pods should always pull images
kubectl run test --image=nginx
kubectl get pod test -o yaml | grep imagePullPolicy
# Should show "Always"
```

### Сценарій 2: Створення ValidatingWebhookConfiguration

```bash
# Create webhook configuration that blocks pods without labels
cat <<EOF | kubectl apply -f -
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: require-labels
webhooks:
- name: require-labels.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  clientConfig:
    service:
      name: label-validator
      namespace: default
      path: /validate
    caBundle: LS0tLS1CRUdJTi...  # Base64 CA cert
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      require-labels: "true"
EOF
```

### Сценарій 3: Налаштування ImagePolicyWebhook

```bash
# Create admission config directory
sudo mkdir -p /etc/kubernetes/admission

# Create admission configuration
sudo tee /etc/kubernetes/admission/admission-config.yaml << 'EOF'
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: ImagePolicyWebhook
  configuration:
    imagePolicy:
      kubeConfigFile: /etc/kubernetes/admission/kubeconfig
      allowTTL: 50
      denyTTL: 50
      retryBackoff: 500
      defaultAllow: false
EOF

# Create kubeconfig for webhook
sudo tee /etc/kubernetes/admission/kubeconfig << 'EOF'
apiVersion: v1
kind: Config
clusters:
- name: image-policy
  cluster:
    certificate-authority: /etc/kubernetes/admission/ca.crt
    server: https://image-policy.security.svc:443/check
contexts:
- name: image-policy
  context:
    cluster: image-policy
current-context: image-policy
EOF

# Update API server manifest to enable ImagePolicyWebhook
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --enable-admission-plugins=...,ImagePolicyWebhook
# Add: --admission-control-config-file=/etc/kubernetes/admission/admission-config.yaml
# Add volume mount for /etc/kubernetes/admission
```

---

## Рекомендації щодо контролерів допуску

```
┌─────────────────────────────────────────────────────────────┐
│              РЕКОМЕНДАЦІЇ КОНТРОЛЕРІВ ДОПУСКУ                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  УВІМКНУТИ (критичні для безпеки):                         │
│  ├── NodeRestriction (завжди)                              │
│  ├── PodSecurity (Kubernetes 1.25+)                        │
│  ├── AlwaysPullImages (мультитенантні кластери)            │
│  └── DenyServiceExternalIPs (якщо не потрібні)             │
│                                                             │
│  РОЗГЛЯНУТИ (залежно від вимог):                           │
│  ├── ImagePolicyWebhook (валідація образів)                │
│  ├── ValidatingAdmissionWebhook (власні політики)          │
│  └── MutatingAdmissionWebhook (типові значення)            │
│                                                             │
│  ВИМКНЕНО ЗА ЗАМОВЧУВАННЯМ (увімкнюйте обережно):         │
│  ├── AlwaysDeny (тільки для тестування)                    │
│  └── EventRateLimit (може зламати кластер)                 │
│                                                             │
│  ЗАСТАРІЛІ:                                                │
│  └── PodSecurityPolicy (видалено 1.25)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **Контролери допуску виконуються по порядку**: спочатку мутуючі вебхуки, потім валідуючі. Це дозволяє валідувати мутації.

- **failurePolicy є критичним**: Встановлення `Fail` безпечніше, але може спричинити збої всього кластера, якщо сервіс вебхука недоступний.

- **NodeRestriction запобігає захопленню вузла**: Він обмежує kubelet зміною лише Pod, що працюють на його вузлі, та власного об'єкту Node.

- **AlwaysPullImages впливає на продуктивність**: Кожен запуск Pod потребує завантаження образу, що збільшує затримку та навантаження на реєстр.

---

## Поширені помилки

| Помилка | Чому це шкідливо | Рішення |
|---------|-------------------|---------|
| failurePolicy: Ignore | Обхід перевірок безпеки | Використовуйте Fail з високою доступністю |
| Без namespaceSelector | Застосовується до всіх просторів імен | Виключіть kube-system |
| Тайм-аут вебхука занадто малий | Хибні збої | Встановіть 10-30 секунд |
| Не увімкнено NodeRestriction | Атаки скомпрометованих вузлів | Завжди вмикайте |
| defaultAllow: true | Непідписані образи дозволені | Встановіть false |

---

## Тест

1. **Яка різниця між Mutating та Validating admission вебхуками?**
   <details>
   <summary>Відповідь</summary>
   Мутуючі вебхуки можуть змінювати запит (додавати мітки, впроваджувати sidecar). Валідуючі вебхуки можуть лише дозволяти або відхиляти запити. Мутуючі виконуються перед валідуючими.
   </details>

2. **Що робить failurePolicy: Fail?**
   <details>
   <summary>Відповідь</summary>
   Якщо вебхук недоступний або перевищено тайм-аут, API-запит відхиляється. Це безпечніше, але може спричинити проблеми кластера, якщо сервіс вебхука не працює.
   </details>

3. **Як увімкнути контролер допуску в кластерах kubeadm?**
   <details>
   <summary>Відповідь</summary>
   Додайте його до прапорця `--enable-admission-plugins` у `/etc/kubernetes/manifests/kube-apiserver.yaml`. API server автоматично перезапуститься.
   </details>

4. **Що контролює налаштування defaultAllow у ImagePolicyWebhook?**
   <details>
   <summary>Відповідь</summary>
   Воно визначає, що відбувається, коли вебхук недоступний. `defaultAllow: false` відхиляє всі образи, якщо вебхук недосяжний (безпечніше).
   </details>

---

## Практична вправа

**Завдання**: Увімкнути контролери допуску та створити конфігурацію вебхука.

```bash
# Step 1: Check current admission controllers
echo "=== Current Admission Controllers ==="
kubectl get pod kube-apiserver-* -n kube-system -o yaml 2>/dev/null | \
  grep -A1 enable-admission-plugins || \
  echo "Check /etc/kubernetes/manifests/kube-apiserver.yaml on control plane"

# Step 2: Create a ValidatingWebhookConfiguration (dry-run)
cat <<EOF > webhook.yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: test-webhook
webhooks:
- name: test.webhook.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Ignore  # Using Ignore for testing
  clientConfig:
    url: "https://webhook.example.com/validate"
    caBundle: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJrVENDQVRlZ0F3SUJBZ0lJYzNrMGJHRnVaR1V3Q2dZSUtvWkl6ajBFQXdJd0l6RWhNQjhHQTFVRQpBeE1ZYXpOekxXTnNhV1Z1ZEMxallVQXhOekUwT0RRME5qRXdNQjRYRFRJME1EUXdOREUyTkRNeE1Gb1gKRFRJMU1EUXdOREUyTkRNeE1Gb3dJekVoTUI4R0ExVUVBeE1ZYXpOekxXTnNhV1Z1ZEMxallVQXhOekUwCk9EUTBOakV3V1RBVEJnY3Foa2pPUFFJQkJnZ3Foa2pPUFFNQkJ3TkNBQVRITCs5PT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      test-webhook: "enabled"
EOF

echo "=== Webhook Configuration ==="
cat webhook.yaml

# Step 3: List existing webhook configurations
echo "=== Existing Webhooks ==="
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations

# Step 4: Check built-in admission controller recommendations
echo "=== Recommended Security Controllers ==="
cat <<EOF
1. NodeRestriction - Limit kubelet permissions (ALWAYS enable)
2. PodSecurity - Pod Security Standards enforcement
3. AlwaysPullImages - Force image pulls (multi-tenant)
4. DenyServiceExternalIPs - Prevent CVE-2020-8554
EOF

# Cleanup
rm -f webhook.yaml
```

**Критерії успіху**: Зрозуміти конфігурацію контролерів допуску.

---

## Підсумок

**Типи контролерів допуску**:
- Вбудовані контролери (увімкнення через прапорець API server)
- ValidatingAdmissionWebhook (зовнішня валідація)
- MutatingAdmissionWebhook (зовнішня мутація)

**Ключові контролери безпеки**:
- NodeRestriction (завжди вмикайте)
- PodSecurity (PSA)
- AlwaysPullImages (мультитенантність)
- ImagePolicyWebhook (валідація образів)

**Конфігурація вебхука**:
- failurePolicy: Fail проти Ignore
- namespaceSelector для обмеження області
- Декларація sideEffects
- Налаштування тайм-ауту

**Поради для іспиту**:
- Знайте, як увімкнути контролери в API server
- Розумійте YAML конфігурації вебхука
- Пам'ятайте про наслідки failurePolicy

---

## Частина 5 завершена!

Ви завершили **Безпеку ланцюга постачання** (20% CKS). Тепер ви розумієте:
- Найкращі практики безпеки образів контейнерів
- Сканування образів з Trivy
- Статичний аналіз з kubesec та OPA
- Контролери допуску та вебхуки

**Наступна частина**: [Частина 6: Моніторинг, логування та безпека середовища виконання](../part6-runtime-security/module-6.1-audit-logging/) — Виявлення та реагування на інциденти безпеки.
