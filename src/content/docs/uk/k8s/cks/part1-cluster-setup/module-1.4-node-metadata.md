---
title: "Модуль 1.4: Захист метаданих вузлів"
slug: uk/k8s/cks/part1-cluster-setup/module-1.4-node-metadata
sidebar:
  order: 4
---
> **Складність**: `[СЕРЕДНЯ]` — Критична навичка безпеки, специфічна для хмари
>
> **Час на виконання**: 30-35 хвилин
>
> **Передумови**: Модуль 1.1 (Network Policies), розуміння хмарних провайдерів

---

## Чому цей модуль важливий

Сервіси метаданих хмарних провайдерів (наприклад, 169.254.169.254 AWS) відкривають чутливу інформацію: облікові дані IAM, ідентифікатор інстансу та конфігураційні дані. Скомпрометований Pod може запитати цей ендпоінт і потенційно підвищити привілеї або отримати доступ до хмарних ресурсів.

Це улюблений вектор атаки. Порушення Capital One у 2019 році використовувало саме цю вразливість.

---

## Атака через метадані

```
┌─────────────────────────────────────────────────────────────┐
│              ВЕКТОР АТАКИ ЧЕРЕЗ СЕРВІС МЕТАДАНИХ           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │  Скомпромето-   │                                       │
│  │  ваний          │                                       │
│  │  застосунок Pod │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           │ curl http://169.254.169.254/latest/meta-data/  │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              СЕРВІС МЕТАДАНИХ                        │   │
│  │                                                      │   │
│  │  Повертає:                                          │   │
│  │  • ID інстансу                                      │   │
│  │  • Приватний IP                                     │   │
│  │  • Облікові дані ролі IAM                           │   │
│  │  • User data (може містити секрети!)                │   │
│  │  • Конфігурація VPC                                 │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Наслідки:                                                 │
│  ⚠️  Зловмисник отримує тимчасові облікові дані AWS       │
│  ⚠️  Може отримати доступ до S3 бакетів, баз даних тощо  │
│  ⚠️  Латеральний рух через хмарні ресурси                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Ендпоінти метаданих за провайдером

| Хмарний провайдер | Ендпоінт метаданих | Шлях до облікових даних |
|-------------------|---------------------|-------------------------|
| AWS | 169.254.169.254 | /latest/meta-data/iam/security-credentials/ |
| GCP | 169.254.169.254 | /computeMetadata/v1/ |
| Azure | 169.254.169.254 | /metadata/identity/oauth2/token |
| DigitalOcean | 169.254.169.254 | /metadata/v1/ |

Усі використовують одну IP-адресу: **169.254.169.254** (link-local адреса)

---

## Метод захисту 1: NetworkPolicy

Блокування вихідного трафіку до IP метаданих за допомогою NetworkPolicy:

```yaml
# Block access to metadata service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
  namespace: production
spec:
  podSelector: {}  # All pods in namespace
  policyTypes:
  - Egress
  egress:
  # Allow all EXCEPT metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
```

### Дозвіл DNS з блокуванням метаданих

```yaml
# More complete: block metadata but allow DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-metadata-allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
  # Allow all other traffic except metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
```

---

## Метод захисту 2: iptables на вузлах

Налаштування правил iptables на кожному вузлі для блокування доступу до метаданих:

```bash
# Block metadata access from pods (run on each node)
iptables -A OUTPUT -d 169.254.169.254 -j DROP

# Or more specifically, block from pod network
iptables -I FORWARD -s 10.244.0.0/16 -d 169.254.169.254 -j DROP

# Make persistent (varies by OS)
iptables-save > /etc/iptables/rules.v4
```

### DaemonSet для правил iptables

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: metadata-blocker
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: metadata-blocker
  template:
    metadata:
      labels:
        app: metadata-blocker
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: blocker
        image: alpine
        command:
        - /bin/sh
        - -c
        - |
          apk add iptables
          iptables -C FORWARD -d 169.254.169.254 -j DROP 2>/dev/null || \
          iptables -I FORWARD -d 169.254.169.254 -j DROP
          sleep infinity
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN"]
      tolerations:
      - operator: "Exists"
```

---

## Метод захисту 3: Функції хмарного провайдера

### AWS IMDSv2 (Рекомендований)

AWS Instance Metadata Service v2 вимагає сесійний токен, що ускладнює прямий доступ з Pod:

```bash
# IMDSv2 requires PUT request first to get token
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Then use token in subsequent requests
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/
```

Налаштування вузлів для обов'язкового IMDSv2:

```bash
# AWS CLI to enforce IMDSv2 on instance
aws ec2 modify-instance-metadata-options \
  --instance-id i-1234567890abcdef0 \
  --http-tokens required \
  --http-put-response-hop-limit 1
```

### Приховування метаданих GCP

```bash
# Enable metadata concealment on GKE node pool
gcloud container node-pools update POOL_NAME \
  --cluster=CLUSTER_NAME \
  --workload-metadata=GKE_METADATA
```

### Azure Instance Metadata Service (IMDS)

Azure вимагає спеціальні заголовки:

```bash
# Azure IMDS requires Metadata header
curl -H "Metadata:true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01"
```

---

## Тестування доступу до метаданих

### Перевірка, що Pod не може отримати доступ до метаданих

```bash
# Create test pod
kubectl run test-pod --image=curlimages/curl --rm -it --restart=Never -- \
  curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/

# Expected: Connection timeout or refused
# If you see instance metadata, protection isn't working!
```

### Перевірка застосування NetworkPolicy

```bash
# List network policies
kubectl get networkpolicies -n production

# Describe specific policy
kubectl describe networkpolicy block-metadata -n production

# Check if pod is selected by policy
kubectl get pod test-pod -n production --show-labels
```

---

## Повний приклад захисту

```yaml
# Apply to every namespace that runs workloads
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-metadata
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS resolution
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
  # Allow cluster internal communication
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8
  # Allow external but block metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.0.0/16  # Block entire link-local range
```

---

## Реальні сценарії іспиту

### Сценарій 1: Блокування доступу до метаданих для простору імен

```bash
# Create NetworkPolicy to block metadata
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-cloud-metadata
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
EOF

# Verify
kubectl get networkpolicy block-cloud-metadata -n production
```

### Сценарій 2: Тестування та перевірка блокування

```bash
# Create test pod
kubectl run metadata-test --image=curlimages/curl -n production --rm -it --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/ || echo "BLOCKED (expected)"
```

### Сценарій 3: Дозвіл доступу для конкретного Pod

```yaml
# Most pods blocked, but monitoring pod needs metadata
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring-metadata
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: cloud-monitor
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0  # All traffic including metadata
```

---

## Ешелонована оборона

```
┌─────────────────────────────────────────────────────────────┐
│              РІВНІ ЗАХИСТУ МЕТАДАНИХ                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Рівень 1: NetworkPolicy                                   │
│  └── Блокування вихідного трафіку до 169.254.169.254       │
│                                                             │
│  Рівень 2: IMDSv2 хмарного провайдера                     │
│  └── Обов'язкові сесійні токени                            │
│                                                             │
│  Рівень 3: iptables рівня вузла                            │
│  └── Блокування на мережевому рівні                        │
│                                                             │
│  Рівень 4: Безпека Pod                                     │
│  └── Обмеження мережі хоста                                │
│                                                             │
│  Рівень 5: Мінімальний IAM                                 │
│  └── Ролі вузлів з найменшими привілеями                  │
│                                                             │
│  Найкраща практика: Використовуйте ДЕКІЛЬКА рівнів        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **Порушення Capital One у 2019 році** розкрило 100 мільйонів записів клієнтів через SSRF до сервісу метаданих. Зловмисник отримав облікові дані IAM та отримав доступ до S3 бакетів.

- **169.254.0.0/16 — це link-local.** Ця підмережа зарезервована для локального мережевого зв'язку та ніколи не маршрутизується в інтернеті. Хмарні провайдери використовують її для метаданих, бо вона доступна з будь-якого інстансу без маршрутизації.

- **Kubernetes сам використовує метадані** на хмарних провайдерах для інформації про вузли. Блокування системних компонентів від метаданих може порушити функціональність кластера.

- **AWS IMDSv2 з hop limit 1** запобігає контейнерам дістатися до метаданих, оскільки запит проходить через кілька мережевих стрибків (контейнер → вузол → сервіс метаданих).

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Забути DNS з політикою egress | Pod не можуть вирішувати імена | Завжди дозволяйте DNS egress |
| Блокування метаданих для kube-system | Ламає хмарні інтеграції | Обережно виключайте системні простори імен |
| Використання лише NetworkPolicy | Не всі CNI застосовують її | Використовуйте декілька рівнів захисту |
| Тестування з неправильного простору імен | Політика там не застосована | Тестуйте з простору імен з політикою |
| Блокування усього діапазону link-local | Може зламати інші сервіси | Почніть лише з 169.254.169.254/32 |

---

## Тест

1. **Яку IP-адресу використовують хмарні сервіси метаданих?**
   <details>
   <summary>Відповідь</summary>
   169.254.169.254 — це link-local адреса, яку використовують AWS, GCP, Azure та інші хмарні провайдери для своїх сервісів метаданих інстансів.
   </details>

2. **Чому блокування доступу до метаданих важливе для безпеки?**
   <details>
   <summary>Відповідь</summary>
   Сервіс метаданих відкриває чутливу інформацію, включаючи облікові дані IAM. Скомпрометований Pod може запитати цей ендпоінт для отримання облікових даних та доступу до хмарних ресурсів, уможливлюючи латеральний рух та підвищення привілеїв.
   </details>

3. **Який ресурс Kubernetes використовується для блокування вихідного трафіку до IP метаданих?**
   <details>
   <summary>Відповідь</summary>
   NetworkPolicy з правилами egress, що використовує ipBlock з except для 169.254.169.254/32.
   </details>

4. **Що таке AWS IMDSv2 і чому він допомагає?**
   <details>
   <summary>Відповідь</summary>
   Instance Metadata Service версії 2 вимагає сесійний токен, отриманий через PUT-запит, перед доступом до метаданих. З hop limit 1 контейнери не можуть отримати токени, оскільки їхні запити проходять через кілька стрибків.
   </details>

---

## Практична вправа

**Завдання**: Заблокуйте доступ до метаданих та перевірте захист.

```bash
# Setup namespace
kubectl create namespace metadata-test

# Step 1: Verify metadata is accessible (before protection)
kubectl run check-before --image=curlimages/curl -n metadata-test --rm -it --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/ && echo "ACCESSIBLE" || echo "BLOCKED"

# Note: In non-cloud environments, you'll see "BLOCKED" already

# Step 2: Apply metadata blocking NetworkPolicy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
  namespace: metadata-test
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - to: []
    ports:
    - port: 53
      protocol: UDP
  # Allow all except metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
EOF

# Step 3: Verify policy exists
kubectl get networkpolicy -n metadata-test
kubectl describe networkpolicy block-metadata -n metadata-test

# Step 4: Test metadata is blocked
kubectl run check-after --image=curlimages/curl -n metadata-test --rm -it --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/ && echo "ACCESSIBLE" || echo "BLOCKED"

# Step 5: Verify other egress still works
kubectl run check-external --image=curlimages/curl -n metadata-test --rm -it --restart=Never -- \
  curl -s --connect-timeout 3 https://kubernetes.io -o /dev/null -w "%{http_code}" && echo " OK"

# Cleanup
kubectl delete namespace metadata-test
```

**Критерії успіху**: IP метаданих заблоковано, але зовнішній доступ працює.

---

## Підсумок

**Ризик сервісу метаданих**:
- Відкриває облікові дані IAM та дані інстансу
- Доступний з будь-якого Pod за замовчуванням
- Основний вектор атаки (порушення Capital One)

**Методи захисту**:
1. NetworkPolicy, що блокує 169.254.169.254
2. Примусове використання IMDSv2 хмарного провайдера
3. Правила iptables на рівні вузла
4. Безпека Pod (без hostNetwork)

**Найкращі практики**:
- Застосуйте захист до всіх просторів імен з робочими навантаженнями
- Пам'ятайте дозволити DNS egress
- Використовуйте декілька рівнів захисту
- Перевірте ефективність блокування

**Поради для іспиту**:
- Знайте, як написати NetworkPolicy з пам'яті
- Розумійте синтаксис ipBlock з except
- Пам'ятайте, що DNS — це UDP порт 53

---

## Наступний модуль

[Модуль 1.5: Безпека GUI](module-1.5-gui-security/) — Захист Kubernetes Dashboard та веб-інтерфейсів.
