---
title: "Модуль 2.5: Обмеження доступу до API"
slug: uk/k8s/cks/part2-cluster-hardening/module-2.5-restricting-api-access
sidebar:
  order: 5
---
> **Складність**: `[MEDIUM]` - Необхідно для безпеки кластера
>
> **Час на виконання**: 35-40 хвилин
>
> **Передумови**: Модуль 2.3 (Безпека API-сервера), основи мережевих технологій

---

## Чому цей модуль важливий

API Kubernetes — це головна цінність: доступ до нього означає контроль над усім. Хоча RBAC контролює, що можуть робити автентифіковані користувачі, обмеження того, ХТО взагалі може досягти API, є не менш важливим.

Цей модуль охоплює мережеві та автентифікаційні обмеження доступу до API.

---

## Поверхня атаки доступу до API

```
┌─────────────────────────────────────────────────────────────┐
│              ПОВЕРХНЯ АТАКИ ДОСТУПУ ДО API                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Інтернет                                                  │
│     │                                                       │
│     ├──► API-сервер :6443  ← Відкритий?                    │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ВЕКТОРИ АТАК                            │   │
│  │                                                      │   │
│  │  1. Прямий доступ до API з інтернету                │   │
│  │     → Брутфорс автентифікації, експлуатація         │   │
│  │       вразливостей                                   │   │
│  │                                                      │   │
│  │  2. Скомпрометований Pod у кластері                 │   │
│  │     → Використовує змонтований токен для виклику API│   │
│  │                                                      │   │
│  │  3. Скомпрометований вузол                          │   │
│  │     → Використовує облікові дані kubelet             │   │
│  │                                                      │   │
│  │  4. Викрадений kubeconfig                           │   │
│  │     → Прямий доступ до кластера з будь-де           │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Мережеві обмеження

### Правила брандмауера (зовнішні)

```bash
# Дозволити доступ до API тільки з конкретних IP
# У хмарі: Security Groups, Firewall Rules, NSGs

# Приклад AWS Security Group:
# Вхідне правило: TCP 6443 з 10.0.0.0/8 (тільки внутрішні)

# iptables на вузлі API-сервера
sudo iptables -A INPUT -p tcp --dport 6443 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 6443 -s 192.168.1.0/24 -j ACCEPT  # VPN адміністратора
sudo iptables -A INPUT -p tcp --dport 6443 -j DROP
```

### Приватна точка доступу API

```yaml
# EKS: Увімкнути приватну точку доступу, вимкнути публічну
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config endpointPrivateAccess=true,endpointPublicAccess=false

# GKE: Приватний кластер
gcloud container clusters create private-cluster \
  --enable-private-endpoint \
  --master-ipv4-cidr 172.16.0.0/28

# AKS: Приватний кластер
az aks create \
  --name myAKSCluster \
  --enable-private-cluster
```

---

## Вбудовані мережеві обмеження Kubernetes

### NetworkPolicy для API-сервера (обмежено)

```yaml
# Примітка: NetworkPolicy не застосовується безпосередньо до API-сервера
# Але ви можете обмежити, які Pod можуть до нього звертатися

# Блокування прямого доступу Pod до IP API-сервера
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-api-direct
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Дозволити DNS
  - to:
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
  # Дозволити все, крім API-сервера
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.96.0.1/32  # IP сервісу Kubernetes
```

### Адреса прив'язки API-сервера

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    # Прив'язатися тільки до конкретного інтерфейсу
    - --bind-address=10.0.0.10  # Тільки внутрішній IP
    # Або прив'язатися до всіх (менш безпечно)
    - --bind-address=0.0.0.0
```

---

## Обмеження автентифікації

### Вимкнення анонімної автентифікації

```yaml
# Прапорець API-сервера
- --anonymous-auth=false

# Перевірка
curl -k https://<api-server>:6443/api/v1/namespaces
# Повинно повернути 401 Unauthorized
```

### Вимога клієнтського сертифіката

```yaml
# Вимагати клієнтські сертифікати (взаємний TLS)
- --client-ca-file=/etc/kubernetes/pki/ca.crt

# Клієнти повинні надати дійсний сертифікат, підписаний CA
# Це стандартна поведінка в кластерах kubeadm
```

### Валідація токенів

```yaml
# Налаштування автентифікації токенів
- --service-account-key-file=/etc/kubernetes/pki/sa.pub
- --service-account-issuer=https://kubernetes.default.svc

# Необов'язково: Зовнішній провайдер OIDC
- --oidc-issuer-url=https://accounts.example.com
- --oidc-client-id=kubernetes
- --oidc-username-claim=email
- --oidc-groups-claim=groups
```

---

## Автентифікація через вебхук

```
┌─────────────────────────────────────────────────────────────┐
│              АВТЕНТИФІКАЦІЯ ЧЕРЕЗ ВЕБХУК                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Запит ──► API-сервер ──► Вебхук ──► Відповідь             │
│                               │                             │
│                               ▼                             │
│                      ┌─────────────────┐                   │
│                      │ Сервіс          │                   │
│                      │ автентифікації   │                   │
│                      │                 │                   │
│                      │ - Валідація     │                   │
│                      │   токена        │                   │
│                      │ - Повернення   │                   │
│                      │   інформації   │                   │
│                      │   про          │                   │
│                      │   користувача  │                   │
│                      └─────────────────┘                   │
│                                                             │
│  Варіанти використання:                                    │
│  • Власні системи автентифікації                           │
│  • Інтеграція з SSO                                        │
│  • Додаткова логіка валідації                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Налаштування автентифікації через вебхук

```yaml
# Прапорці API-сервера
- --authentication-token-webhook-config-file=/etc/kubernetes/webhook-config.yaml
- --authentication-token-webhook-cache-ttl=2m

# /etc/kubernetes/webhook-config.yaml
apiVersion: v1
kind: Config
clusters:
- name: auth-service
  cluster:
    certificate-authority: /etc/kubernetes/pki/webhook-ca.crt
    server: https://auth.example.com/authenticate
users:
- name: api-server
  user:
    client-certificate: /etc/kubernetes/pki/webhook-client.crt
    client-key: /etc/kubernetes/pki/webhook-client.key
contexts:
- context:
    cluster: auth-service
    user: api-server
  name: webhook
current-context: webhook
```

---

## Обмеження швидкості API

### Контролер допуску EventRateLimit

```yaml
# Увімкнути контролер допуску
- --enable-admission-plugins=EventRateLimit
- --admission-control-config-file=/etc/kubernetes/admission-config.yaml

# /etc/kubernetes/admission-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: EventRateLimit
  path: /etc/kubernetes/event-rate-limit.yaml

# /etc/kubernetes/event-rate-limit.yaml
apiVersion: eventratelimit.admission.k8s.io/v1alpha1
kind: Configuration
limits:
- type: Namespace
  qps: 50
  burst: 100
- type: User
  qps: 10
  burst: 20
```

### Пріоритет та справедливість API

```yaml
# Kubernetes 1.20+: API Priority and Fairness
# Контролює черги та пріоритети запитів до API

# Перевірити поточні схеми потоків
kubectl get flowschemas

# Перевірити рівні пріоритету
kubectl get prioritylevelconfigurations

# Приклад: Знижений пріоритет для пакетних завдань
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: FlowSchema
metadata:
  name: batch-jobs-low-priority
spec:
  priorityLevelConfiguration:
    name: low-priority
  matchingPrecedence: 1000
  rules:
  - subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: batch-runner
        namespace: batch
    resourceRules:
    - apiGroups: ["batch"]
      resources: ["jobs"]
      verbs: ["*"]
```

---

## Аудит та моніторинг доступу до API

### Журналювання доступу до API

```yaml
# Політика аудиту для журналювання всіх спроб доступу до API
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Журналювати всі спроби автентифікації
- level: RequestResponse
  omitStages:
  - RequestReceived
  resources:
  - group: "authentication.k8s.io"

# Журналювати невдалі запити
- level: Metadata
  omitStages:
  - RequestReceived
```

### Моніторинг метрик API

```bash
# Перевірити метрики API-сервера
kubectl get --raw /metrics | grep apiserver_request

# Невдалі спроби автентифікації
kubectl get --raw /metrics | grep authentication_attempts

# Метрики обмеження швидкості
kubectl get --raw /metrics | grep apiserver_flowcontrol
```

---

## Реальні сценарії іспиту

### Сценарій 1: Обмеження API до внутрішньої мережі

```bash
# Перевірити поточну адресу прив'язки API-сервера
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep bind-address

# Відредагувати для прив'язки тільки до внутрішнього інтерфейсу
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Змінити:
# --bind-address=0.0.0.0
# На:
# --bind-address=10.0.0.10  # Внутрішній IP

# API-сервер перезапуститься автоматично
```

### Сценарій 2: Перевірка вимкнення анонімного доступу

```bash
# Тест анонімного доступу
curl -k https://<api-server>:6443/api/v1/namespaces

# Якщо анонімний доступ вимкнено, повинно бути:
# {"kind":"Status","apiVersion":"v1","status":"Failure","message":"Unauthorized",...}

# Якщо анонімний доступ увімкнено, може повернути список просторів імен або часткові дані
# Виправити, додавши --anonymous-auth=false до API-сервера
```

### Сценарій 3: Налаштування доступу до API для конкретних користувачів

```bash
# Створити kubeconfig для конкретного користувача з обмеженим мережевим доступом
kubectl config set-cluster restricted \
  --server=https://internal-api.example.com:6443 \
  --certificate-authority=/path/to/ca.crt

kubectl config set-credentials limited-user \
  --client-certificate=/path/to/user.crt \
  --client-key=/path/to/user.key

kubectl config set-context limited \
  --cluster=restricted \
  --user=limited-user
```

---

## Захист у глибину для API

```
┌─────────────────────────────────────────────────────────────┐
│              РІВНІ ЗАХИСТУ ДОСТУПУ ДО API                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Рівень 1: Мережа                                          │
│  └── Брандмауер, приватна точка доступу, VPN               │
│                                                             │
│  Рівень 2: TLS                                             │
│  └── Взаємний TLS, валідація сертифікатів                  │
│                                                             │
│  Рівень 3: Автентифікація                                  │
│  └── Без анонімного доступу, OIDC, клієнтські сертифікати  │
│                                                             │
│  Рівень 4: Авторизація                                     │
│  └── RBAC з найменшими привілеями                          │
│                                                             │
│  Рівень 5: Допуск                                          │
│  └── Обмеження швидкості, валідація                        │
│                                                             │
│  Рівень 6: Аудит                                           │
│  └── Журналювання всього доступу, моніторинг аномалій      │
│                                                             │
│  Всі рівні повинні бути активними!                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **API-сервер Kubernetes за замовчуванням прив'язується до 0.0.0.0**, що робить його доступним з усіх мережевих інтерфейсів. Це зручно, але потенційно небезпечно.

- **Хмарні провайдери пропонують приватні кластери**, де API-сервер не має публічного IP взагалі. Доступ тільки через VPN або бастіон-хости.

- **API Priority and Fairness** (APF) замінив старі обмеження max-in-flight у Kubernetes 1.20. Він забезпечує більш справедливе управління чергами під час перевантаження.

- **Деякі організації використовують API-шлюзи** перед API Kubernetes для додаткової безпеки, журналювання та обмеження швидкості.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Публічна точка доступу API | Будь-хто може спробувати автентифікацію | Приватна точка доступу + VPN |
| Без правил брандмауера | Мережева відкритість | Обмежити відомими IP |
| Увімкнена анонімна автентифікація | Неавтентифікований доступ | --anonymous-auth=false |
| Без обмеження швидкості | Вразливість до DoS | Контролер допуску EventRateLimit |
| Без моніторингу доступу | Неможливо виявити атаки | Увімкнути журналювання аудиту |

---

## Тест

1. **Як зробити API-сервер доступним тільки з внутрішньої мережі?**
   <details>
   <summary>Відповідь</summary>
   Встановити `--bind-address` на внутрішній IP, використовувати правила брандмауера для блокування зовнішнього доступу або скористатися функцією приватної точки доступу хмарного провайдера.
   </details>

2. **Що відбувається, коли анонімна автентифікація вимкнена і надходить неавтентифікований запит?**
   <details>
   <summary>Відповідь</summary>
   API-сервер повертає 401 Unauthorized. Запит відхиляється до будь-якої перевірки авторизації.
   </details>

3. **Яке призначення контролера допуску EventRateLimit?**
   <details>
   <summary>Відповідь</summary>
   Він обмежує швидкість подій (та інших запитів до API) на простір імен або користувача, запобігаючи DoS-атакам та надмірному навантаженню на API від некоректно працюючих клієнтів.
   </details>

4. **Чому слід поєднувати кілька обмежень доступу до API?**
   <details>
   <summary>Відповідь</summary>
   Захист у глибину. Мережеві обмеження запобігають доступу, але якщо їх обійти, автентифікація зупиняє неавтентифікованих користувачів, RBAC обмежує можливості автентифікованих користувачів, а аудит все журналює.
   </details>

---

## Практична вправа

**Завдання**: Аудит та перевірка обмежень доступу до API.

```bash
# Крок 1: Перевірити конфігурацію API-сервера
echo "=== Конфігурація API-сервера ==="
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -E "bind-address|anonymous-auth|authorization-mode"

# Крок 2: Тестувати анонімний доступ (зсередини кластера)
echo "=== Тест анонімного доступу ==="
kubectl run curlpod --image=curlimages/curl --rm -it --restart=Never -- \
  curl -sk https://kubernetes.default.svc/api/v1/namespaces 2>&1 | head -5

# Крок 3: Перевірити, чи доступний API ззовні
echo "=== Перевірка зовнішнього доступу ==="
API_IP=$(kubectl get svc kubernetes -o jsonpath='{.spec.clusterIP}')
echo "Внутрішній IP API-сервера: $API_IP"
# У продакшені також перевірте зовнішній IP/DNS

# Крок 4: Перевірити методи автентифікації
echo "=== Конфігурація автентифікації ==="
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -E "client-ca|oidc|token|webhook"

# Крок 5: Перевірити обмеження швидкості
echo "=== Обмеження швидкості ==="
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -E "EventRateLimit|admission-control"

# Крок 6: Переглянути схеми потоків (API Priority and Fairness)
echo "=== Схеми потоків ==="
kubectl get flowschemas --no-headers | head -5

# Критерії успіху:
# - Анонімний доступ заборонено
# - Налаштовано кілька методів автентифікації
# - Активне обмеження швидкості або APF
```

**Критерії успіху**: Визначити поточні обмеження доступу до API та переконатися, що анонімний доступ заблоковано.

---

## Підсумок

**Мережеві обмеження**:
- Приватні точки доступу API
- Правила брандмауера
- Доступ тільки через VPN

**Обмеження автентифікації**:
- Вимкнути анонімну автентифікацію
- Вимагати клієнтські сертифікати
- OIDC для автентифікації користувачів

**Обмеження швидкості**:
- Контролер допуску EventRateLimit
- API Priority and Fairness

**Захист у глибину**:
- Нашаровуйте всі обмеження
- Аудитуйте все
- Моніторте аномалії

**Поради для іспиту**:
- Знайте, як перевірити bind-address
- Розумійте наслідки anonymous-auth
- Практикуйте перевірку доступності API

---

## Частина 2 завершена!

Ви закінчили **Зміцнення кластера** (15% CKS). Тепер ви розумієте:
- Глибоке занурення в RBAC та запобігання ескалації
- Безпеку ServiceAccount та управління токенами
- Конфігурацію безпеки API-сервера
- Безпеку оновлень Kubernetes
- Обмеження доступу до API

**Наступна частина**: [Частина 3: Зміцнення системи](../part3-system-hardening/module-3.1-apparmor/) — AppArmor, seccomp та безпека на рівні ОС.
