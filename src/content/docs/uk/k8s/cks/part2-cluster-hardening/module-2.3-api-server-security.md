---
title: "Модуль 2.3: Безпека API-сервера"
slug: uk/k8s/cks/part2-cluster-hardening/module-2.3-api-server-security
sidebar:
  order: 3
---
> **Складність**: `[COMPLEX]` - Критичний компонент інфраструктури
>
> **Час на виконання**: 45-50 хвилин
>
> **Передумови**: Знання API-сервера з CKA, Модуль 1.2 (CIS Benchmarks)

---

## Чому цей модуль важливий

API-сервер — це парадний вхід площини управління. Кожна команда `kubectl`, кожен контролер, кожен вузол — усі звертаються до API-сервера. Його компрометація означає компрометацію всього кластера.

CKS перевіряє вашу здатність зміцнювати конфігурацію API-сервера та розуміти його межі безпеки.

---

## Потік автентифікації API-сервера

```
┌─────────────────────────────────────────────────────────────┐
│              ПОТІК ЗАПИТУ ДО API-СЕРВЕРА                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Запит ───────────────────────────────────────────────►    │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ Автентифікація  │  Хто ви?                              │
│  │ (authn)         │  - Сертифікати X.509                  │
│  │                 │  - Bearer-токени                      │
│  │                 │  - Токени ServiceAccount              │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ Авторизація     │  Чи маєте ви дозвіл?                  │
│  │ (authz)         │  - RBAC                               │
│  │                 │  - Node authorizer                    │
│  │                 │  - Webhook                            │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ Контроль        │  Чи треба змінити/відхилити?          │
│  │ допуску         │  - Мутуючі вебхуки                   │
│  │                 │  - Валідуючі вебхуки                  │
│  │                 │  - PodSecurity                        │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │    etcd         │  Зберегти ресурс                      │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Критичні прапорці API-сервера

### Прапорці автентифікації

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    # Вимкнути анонімну автентифікацію
    - --anonymous-auth=false

    # Автентифікація клієнтським сертифікатом
    - --client-ca-file=/etc/kubernetes/pki/ca.crt

    # Автентифікація bootstrap-токеном (для приєднання вузлів)
    - --enable-bootstrap-token-auth=true

    # Автентифікація токеном ServiceAccount
    - --service-account-key-file=/etc/kubernetes/pki/sa.pub
    - --service-account-issuer=https://kubernetes.default.svc
```

### Прапорці авторизації

```yaml
    # Режими авторизації (порядок має значення!)
    - --authorization-mode=Node,RBAC
    # Node: авторизація kubelet
    # RBAC: контроль доступу на основі ролей
    # Не використовуйте: AlwaysAllow (небезпечно!)
```

### Прапорці контролера допуску

```yaml
    # Увімкнути необхідні контролери допуску
    - --enable-admission-plugins=NodeRestriction,PodSecurity,EventRateLimit

    # Вимкнути ризиковані контролери допуску
    - --disable-admission-plugins=AlwaysAdmit
```

---

## Критичні налаштування безпеки

```
┌─────────────────────────────────────────────────────────────┐
│              КРИТИЧНІ НАЛАШТУВАННЯ API-СЕРВЕРА              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  anonymous-auth=false                                      │
│  └── Запобігає неавтентифікованому доступу до API          │
│                                                             │
│  authorization-mode=Node,RBAC                              │
│  └── Ніколи не використовуйте AlwaysAllow                 │
│  └── Режим Node обмежує kubelet власними ресурсами         │
│                                                             │
│  enable-admission-plugins=PodSecurity                      │
│  └── Забезпечує дотримання стандартів безпеки Pod          │
│                                                             │
│  audit-log-path=<шлях>                                     │
│  └── Записує всі запити до API                             │
│                                                             │
│  insecure-port=0 (застаріло, але перевіряйте!)             │
│  └── Вимкнено небезпечний HTTP-порт                        │
│                                                             │
│  profiling=false                                           │
│  └── Вимикає точки доступу профілювання                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Журналювання аудиту

### Увімкнення журналювання аудиту

```yaml
# Прапорці API-сервера
- --audit-policy-file=/etc/kubernetes/audit-policy.yaml
- --audit-log-path=/var/log/kubernetes/audit.log
- --audit-log-maxage=30
- --audit-log-maxbackup=10
- --audit-log-maxsize=100
```

### Політика аудиту

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Журналювати невдалі автентифікації
  - level: Metadata
    omitStages:
    - RequestReceived

  # Журналювати доступ до секретів
  - level: RequestResponse
    resources:
    - group: ""
      resources: ["secrets"]

  # Журналювати всі операції з Pod
  - level: Request
    resources:
    - group: ""
      resources: ["pods"]
    verbs: ["create", "update", "patch", "delete"]

  # Журналювати зміни RBAC
  - level: RequestResponse
    resources:
    - group: "rbac.authorization.k8s.io"

  # Пропускати шумні події
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
    - group: ""
      resources: ["endpoints", "services"]
```

### Рівні журналу аудиту

```
┌─────────────────────────────────────────────────────────────┐
│              РІВНІ ЖУРНАЛУ АУДИТУ                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  None                                                      │
│  └── Не журналювати цю подію                               │
│                                                             │
│  Metadata                                                  │
│  └── Журналювати метадані запиту (користувач, час, ресурс) │
│  └── Не журналювати тіло запиту чи відповіді               │
│                                                             │
│  Request                                                   │
│  └── Журналювати метадані та тіло запиту                   │
│  └── Не журналювати тіло відповіді                         │
│                                                             │
│  RequestResponse                                           │
│  └── Журналювати все: метадані, запит, відповідь           │
│  └── Найбільш детальний, використовуйте вибірково          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Контроль доступу до API-сервера

### Обмеження мережевого доступу до API-сервера

```yaml
# Прапорці API-сервера для прив'язки до конкретної адреси
- --advertise-address=10.0.0.10
- --bind-address=0.0.0.0  # Або конкретний IP

# У продакшені використовуйте правила брандмауера для обмеження доступу
# iptables -A INPUT -p tcp --dport 6443 -s 10.0.0.0/8 -j ACCEPT
# iptables -A INPUT -p tcp --dport 6443 -j DROP
```

### Контролер допуску NodeRestriction

```yaml
# Увімкнути NodeRestriction (обмежує, що можуть змінювати kubelet)
- --enable-admission-plugins=NodeRestriction

# Що він запобігає:
# - Kubelet можуть змінювати тільки Pod, заплановані на них
# - Kubelet можуть змінювати тільки свій власний об'єкт Node
# - Kubelet не можуть змінювати мітки інших вузлів
```

---

## Шифрування у стані спокою

### Увімкнення шифрування etcd

```yaml
# Створити конфігурацію шифрування
# /etc/kubernetes/enc/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: <base64-encoded-32-byte-key>
    - identity: {}  # Резервний варіант для читання старих незашифрованих даних
```

```yaml
# Прапорець API-сервера
- --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml

# Монтування конфігурації
volumeMounts:
- name: enc
  mountPath: /etc/kubernetes/enc
  readOnly: true
volumes:
- name: enc
  hostPath:
    path: /etc/kubernetes/enc
```

### Перевірка шифрування

```bash
# Створити секрет
kubectl create secret generic test-secret --from-literal=key=value

# Перевірити etcd безпосередньо (повинно бути зашифровано)
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/test-secret | hexdump -C | head

# Повинні бути видно зашифровані дані, а не звичайний текст
```

---

## Безпечний зв'язок з kubelet

```yaml
# Прапорці API-сервера для безпечного зв'язку з kubelet
- --kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt
- --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
- --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key

# Увімкнення HTTPS для kubelet (на стороні kubelet)
# /var/lib/kubelet/config.yaml
serverTLSBootstrap: true
```

---

## Реальні сценарії іспиту

### Сценарій 1: Вимкнення анонімної автентифікації

```bash
# Перевірити поточне налаштування
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep anonymous

# Відредагувати маніфест API-сервера
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Додати до секції command:
# - --anonymous-auth=false

# Дочекатися перезапуску API-сервера
kubectl get pods -n kube-system -w
```

### Сценарій 2: Увімкнення журналювання аудиту

```bash
# Створити політику аудиту
sudo tee /etc/kubernetes/audit-policy.yaml <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: RequestResponse
  resources:
  - group: "rbac.authorization.k8s.io"
EOF

# Створити каталог для журналів
sudo mkdir -p /var/log/kubernetes

# Відредагувати маніфест API-сервера
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Додати прапорці:
# - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# - --audit-log-path=/var/log/kubernetes/audit.log
# - --audit-log-maxage=30
# - --audit-log-maxbackup=3
# - --audit-log-maxsize=100

# Додати монтування томів для політики та журналів
```

### Сценарій 3: Перевірка режиму авторизації

```bash
# Перевірити режим авторизації
kubectl get pods -n kube-system kube-apiserver-* -o yaml | grep authorization-mode

# Повинно бути: --authorization-mode=Node,RBAC
# НЕ повинно бути: AlwaysAllow
```

---

## Контрольний список зміцнення API-сервера

```bash
#!/bin/bash
# api-server-audit.sh

echo "=== Аудит безпеки API-сервера ==="

# Отримати Pod API-сервера
POD=$(kubectl get pods -n kube-system -l component=kube-apiserver -o name | head -1)

# Перевірити анонімну автентифікацію
echo "Анонімна автентифікація:"
kubectl get $POD -n kube-system -o yaml | grep -E "anonymous-auth" || echo "  Не встановлено явно (перевірте значення за замовчуванням)"

# Перевірити режим авторизації
echo "Режим авторизації:"
kubectl get $POD -n kube-system -o yaml | grep -E "authorization-mode"

# Перевірити плагіни допуску
echo "Плагіни допуску:"
kubectl get $POD -n kube-system -o yaml | grep -E "enable-admission-plugins"

# Перевірити журналювання аудиту
echo "Журналювання аудиту:"
kubectl get $POD -n kube-system -o yaml | grep -E "audit-log-path" || echo "  Не налаштовано"

# Перевірити шифрування
echo "Шифрування у стані спокою:"
kubectl get $POD -n kube-system -o yaml | grep -E "encryption-provider-config" || echo "  Не налаштовано"

# Перевірити профілювання
echo "Профілювання:"
kubectl get $POD -n kube-system -o yaml | grep -E "profiling=false" || echo "  Може бути увімкнено"
```

---

## Чи знали ви?

- **Небезпечний порт (--insecure-port)** було повністю видалено в Kubernetes 1.24. До цього він надавав неавтентифікований доступ до API на localhost.

- **Режим авторизації Node** призначений спеціально для kubelet. Він обмежує їх доступ тільки до ресурсів, пов'язаних з Pod, запланованими на їхньому вузлі.

- **Журнали аудиту можна надсилати через вебхуки** для моніторингу безпеки в реальному часі. Багато організацій використовують це для інтеграції з SIEM.

- **API-сервер не має стану** — всі дані зберігаються в etcd. Ви можете запускати кілька API-серверів для високої доступності.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Увімкнена анонімна автентифікація | Неавтентифікований доступ | --anonymous-auth=false |
| Авторизація AlwaysAllow | Відсутність контролю доступу | Використовуйте Node,RBAC |
| Без журналювання аудиту | Неможливо розслідувати інциденти | Налаштуйте політику аудиту |
| Незашифрований etcd | Секрети у відкритому тексті | Увімкніть шифрування у стані спокою |
| Відсутній NodeRestriction | Kubelet можуть змінювати будь-який Pod | Увімкніть плагін допуску |

---

## Тест

1. **Які режими авторизації слід налаштувати для продакшену?**
   <details>
   <summary>Відповідь</summary>
   `--authorization-mode=Node,RBAC` — Node authorizer обмежує доступ kubelet, RBAC забезпечує контроль доступу на основі ролей. Ніколи не використовуйте AlwaysAllow.
   </details>

2. **Що робить плагін допуску NodeRestriction?**
   <details>
   <summary>Відповідь</summary>
   Він обмежує kubelet можливістю змінювати тільки Pod, заплановані на їхньому вузлі, та їхній власний об'єкт Node. Запобігає впливу скомпрометованого kubelet на інші вузли.
   </details>

3. **Як перевірити, що шифрування etcd працює?**
   <details>
   <summary>Відповідь</summary>
   Прочитати секрет безпосередньо з etcd за допомогою etcdctl. Дані повинні виглядати зашифрованими (не звичайний текст). Команда включає префікс ключа шифрування у вивід.
   </details>

4. **Який рівень журналу аудиту записує тіло запиту та відповіді?**
   <details>
   <summary>Відповідь</summary>
   `RequestResponse` — це найбільш детальний рівень, який захоплює все. Використовуйте його вибірково для чутливих ресурсів, таких як секрети та RBAC.
   </details>

---

## Практична вправа

**Завдання**: Аудит та перевірка конфігурації безпеки API-сервера.

```bash
# Ця вправа перевіряє наявну конфігурацію
# (Зміна API-сервера потребує доступу до площини управління)

# Крок 1: Отримати конфігурацію API-сервера
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml > /tmp/apiserver.yaml

# Крок 2: Перевірити налаштування автентифікації
echo "=== Автентифікація ==="
grep -E "anonymous-auth|client-ca-file" /tmp/apiserver.yaml

# Крок 3: Перевірити налаштування авторизації
echo "=== Авторизація ==="
grep -E "authorization-mode" /tmp/apiserver.yaml

# Крок 4: Перевірити плагіни допуску
echo "=== Плагіни допуску ==="
grep -E "enable-admission-plugins|disable-admission-plugins" /tmp/apiserver.yaml

# Крок 5: Перевірити конфігурацію аудиту
echo "=== Аудит ==="
grep -E "audit-log|audit-policy" /tmp/apiserver.yaml

# Крок 6: Перевірити шифрування
echo "=== Шифрування ==="
grep -E "encryption-provider" /tmp/apiserver.yaml

# Крок 7: Тестувати анонімний доступ (повинен завершитися невдачею при правильній конфігурації)
echo "=== Тест анонімного доступу ==="
curl -k https://$(kubectl get svc kubernetes -o jsonpath='{.spec.clusterIP}')/api/v1/namespaces 2>/dev/null | head -5

# Очікуваний вивід для безпечного кластера:
# {
#   "kind": "Status",
#   "apiVersion": "v1",
#   "status": "Failure",
#   "message": "Unauthorized"
# }

# Очищення
rm /tmp/apiserver.yaml
```

**Критерії успіху**: Визначити поточні налаштування безпеки та переконатися, що анонімний доступ заборонено.

---

## Підсумок

**Критичні налаштування API-сервера**:
- `--anonymous-auth=false`
- `--authorization-mode=Node,RBAC`
- `--enable-admission-plugins=NodeRestriction,PodSecurity`
- `--audit-log-path=<шлях>`

**Рівні безпеки**:
1. Автентифікація (хто ви)
2. Авторизація (що ви можете робити)
3. Контроль допуску (чи дозволити/змінити)

**Журналювання аудиту**:
- Чотири рівні: None, Metadata, Request, RequestResponse
- Журналюйте чутливі операції (секрети, RBAC)
- Зберігайте журнали безпечно

**Поради для іспиту**:
- Знайте, де знаходиться маніфест API-сервера
- Розумійте синтаксис прапорців
- Практикуйте читання політик аудиту

---

## Наступний модуль

[Модуль 2.4: Оновлення Kubernetes](module-2.4-kubernetes-upgrades/) — Питання безпеки при оновленні кластерів.
