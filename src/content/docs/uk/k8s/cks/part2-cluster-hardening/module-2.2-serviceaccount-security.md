---
title: "Модуль 2.2: Безпека ServiceAccount"
slug: uk/k8s/cks/part2-cluster-hardening/module-2.2-serviceaccount-security
sidebar:
  order: 2
---
> **Складність**: `[MEDIUM]` - Критично для безпеки навантажень
>
> **Час на виконання**: 40-45 хвилин
>
> **Передумови**: Модуль 2.1 (Глибоке занурення в RBAC), знання ServiceAccount з CKA

---

## Чому цей модуль важливий

Кожен Pod працює від імені ServiceAccount. За замовчуванням це ServiceAccount 'default' з автоматично змонтованими обліковими даними. Якщо Pod скомпрометовано, зловмисник отримує ці облікові дані — потенційно з доступом до API Kubernetes.

CKS перевіряє вашу здатність зміцнювати ServiceAccount та мінімізувати ризики.

---

## Проблема ServiceAccount

```
┌─────────────────────────────────────────────────────────────┐
│              РИЗИК СТАНДАРТНОГО SERVICEACCOUNT              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  За замовчуванням:                                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Pod                               │   │
│  │                                                      │   │
│  │  Токен змонтовано за шляхом:                        │   │
│  │  /var/run/secrets/kubernetes.io/serviceaccount/     │   │
│  │                                                      │   │
│  │  Містить:                                           │   │
│  │  ├── token  (JWT для автентифікації API)            │   │
│  │  ├── ca.crt (сертифікат CA кластера)               │   │
│  │  └── namespace (простір імен Pod)                   │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Сценарій атаки:                                           │
│  1. Зловмисник компрометує застосунок                      │
│  2. Читає токен з файлової системи                         │
│  3. Використовує токен для виклику API Kubernetes          │
│  4. Залежно від RBAC, може отримати доступ до секретів,   │
│     Pod тощо                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Вимкнення автоматичного монтування токена

### Метод 1: На рівні ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp
  namespace: production
automountServiceAccountToken: false  # Вимкнути для всіх Pod, що використовують цей SA
```

### Метод 2: На рівні Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  serviceAccountName: myapp
  automountServiceAccountToken: false  # Перевизначити тільки для цього Pod
  containers:
  - name: app
    image: myapp:1.0
```

### Метод 3: Оновлення стандартного ServiceAccount

```bash
# Оновити стандартний ServiceAccount у просторі імен
kubectl patch serviceaccount default -n production \
  -p '{"automountServiceAccountToken": false}'

# Перевірити
kubectl get sa default -n production -o yaml
```

---

## Створення окремих ServiceAccount

```yaml
# Один ServiceAccount на застосунок
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-api
  namespace: production
automountServiceAccountToken: false
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: frontend-app
  namespace: production
automountServiceAccountToken: false
---
# Pod, що використовує окремий SA
apiVersion: v1
kind: Pod
metadata:
  name: backend
  namespace: production
spec:
  serviceAccountName: backend-api
  containers:
  - name: app
    image: backend:1.0
```

---

## API TokenRequest (Прив'язані токени)

Kubernetes 1.22+ за замовчуванням використовує прив'язані токени — короткоживучі токени, прив'язані до аудиторії, які є більш безпечними ніж довгоживучі секрети.

```
┌─────────────────────────────────────────────────────────────┐
│              ПРИВ'ЯЗАНІ vs ЗАСТАРІЛІ ТОКЕНИ                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Застарілий токен (на основі Secret)                       │
│  ─────────────────────────────────────────────────────────  │
│  • Довгоживучий (ніколи не закінчується)                   │
│  • Зберігається як Secret                                  │
│  • Не прив'язаний до життєвого циклу Pod                  │
│  • Працює навіть після видалення Pod                       │
│                                                             │
│  Прив'язаний токен (TokenRequest API)                      │
│  ─────────────────────────────────────────────────────────  │
│  • Короткоживучий (налаштовуваний термін дії)              │
│  • Прив'язаний до конкретного Pod                          │
│  • Стає недійсним після видалення Pod                      │
│  • Прив'язаний до аудиторії                                │
│  • За замовчуванням у K8s 1.22+                            │
│                                                             │
│  Прив'язані токени автоматично оновлюються kubelet!        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Створення прив'язаного токена вручну

```bash
# Створити короткоживучий токен (1 година)
kubectl create token myapp-sa -n production --duration=1h

# Створити токен з конкретною аудиторією
kubectl create token myapp-sa -n production --audience=api.example.com
```

### Проєктований том для прив'язаного токена

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  serviceAccountName: myapp-sa
  automountServiceAccountToken: false  # Вимкнути стандартне монтування
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
      readOnly: true
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600  # 1 година
          audience: api.example.com  # Конкретна аудиторія
```

---

## Найкращі практики ServiceAccount

```
┌─────────────────────────────────────────────────────────────┐
│              КОНТРОЛЬНИЙ СПИСОК БЕЗПЕКИ SERVICEACCOUNT      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  □ Вимкнути автомонтування для стандартного ServiceAccount  │
│    kubectl patch sa default -p                             │
│    '{"automountServiceAccountToken": false}'               │
│                                                             │
│  □ Створити окремий ServiceAccount для кожного застосунку  │
│    Один SA на навантаження, без спільного використання     │
│                                                             │
│  □ Монтувати токен тільки коли потрібно                    │
│    Більшість застосунків не потребують доступу до API K8s  │
│                                                             │
│  □ Використовувати прив'язані токени з терміном дії        │
│    Короткоживучі, прив'язані до аудиторії                  │
│                                                             │
│  □ Мінімальні дозволи RBAC                                 │
│    Тільки те, що застосунку дійсно потрібно                │
│                                                             │
│  □ Аудит використання ServiceAccount                       │
│    Які SA мають який доступ                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Аудит ServiceAccount

### Пошук Pod зі змонтованим токеном

```bash
# Список всіх Pod з їхніми ServiceAccount
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name} -> {.spec.serviceAccountName}{"\n"}{end}'

# Перевірити, чи увімкнено автомонтування
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.automountServiceAccountToken != false) |
  "\(.metadata.namespace)/\(.metadata.name): automount enabled"'
```

### Пошук ServiceAccount з дозволами

```bash
# Список всіх RoleBinding/ClusterRoleBinding для ServiceAccount
kubectl get rolebindings,clusterrolebindings -A -o json | jq -r '
  .items[] |
  .subjects[]? |
  select(.kind == "ServiceAccount") |
  "\(.namespace)/\(.name)"' | sort -u

# Перевірити дозволи конкретного SA
kubectl auth can-i --list --as=system:serviceaccount:default:myapp
```

### Перевірка застарілих токенів у Secret

```bash
# Знайти секрети типу ServiceAccount token
kubectl get secrets -A -o json | jq -r '
  .items[] |
  select(.type == "kubernetes.io/service-account-token") |
  "\(.metadata.namespace)/\(.metadata.name)"'
```

---

## Реальні сценарії іспиту

### Сценарій 1: Вимкнення автомонтування токена

```bash
# Вимкнути для стандартного SA у просторі імен production
kubectl patch serviceaccount default -n production \
  -p '{"automountServiceAccountToken": false}'

# Створити новий SA з вимкненим автомонтуванням
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: webapp-sa
  namespace: production
automountServiceAccountToken: false
EOF
```

### Сценарій 2: Виправлення Pod, що використовує стандартний SA

```bash
# Перевірити, який SA використовує Pod
kubectl get pod myapp -n production -o jsonpath='{.spec.serviceAccountName}'

# Якщо використовується default, створити окремий SA
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: production
automountServiceAccountToken: false
EOF

# Перестворити Pod з новим SA (не можна змінити SA у працюючому Pod)
kubectl get pod myapp -n production -o yaml > pod.yaml
# Відредагувати pod.yaml: встановити serviceAccountName: myapp-sa
kubectl delete pod myapp -n production
kubectl apply -f pod.yaml
```

### Сценарій 3: Створення SA з мінімальними дозволами

```bash
# Створити SA для застосунку, якому потрібно тільки читати ConfigMap
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: config-reader
  namespace: production
automountServiceAccountToken: true  # Потребує доступу до API
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config"]  # Тільки конкретний ConfigMap
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: config-reader-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: config-reader
  namespace: production
roleRef:
  kind: Role
  name: configmap-reader
  apiGroup: rbac.authorization.k8s.io
EOF
```

---

## Глибше про безпеку токенів

### Дослідження токена

```bash
# Отримати токен з працюючого Pod
kubectl exec myapp -- cat /var/run/secrets/kubernetes.io/serviceaccount/token

# Декодувати JWT (без верифікації)
TOKEN=$(kubectl exec myapp -- cat /var/run/secrets/kubernetes.io/serviceaccount/token)
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .
```

### Вміст токена

```json
{
  "aud": ["https://kubernetes.default.svc"],
  "exp": 1704067200,  // Час закінчення
  "iat": 1703980800,  // Час видачі
  "iss": "https://kubernetes.default.svc",
  "kubernetes.io": {
    "namespace": "production",
    "pod": {
      "name": "myapp-abc123",
      "uid": "..."
    },
    "serviceaccount": {
      "name": "myapp-sa",
      "uid": "..."
    }
  },
  "sub": "system:serviceaccount:production:myapp-sa"
}
```

---

## Чи знали ви?

- **TokenRequest API** було представлено в Kubernetes 1.12 і стало стандартним у 1.22. Він значно безпечніший за старі токени на основі секретів.

- **Прив'язані токени оновлюються автоматично** kubelet до закінчення терміну дії. Застосункам не потрібно обробляти оновлення — файл оновлюється на місці.

- **Стандартний ServiceAccount** існує автоматично в кожному просторі імен. Його зміна впливає на всі Pod, які не вказують ServiceAccount.

- **Деякі контролери потребують доступу до API** — оператори, вебхуки допуску та застосунки, що працюють з Kubernetes. Вони легітимно потребують змонтованих токенів з відповідними дозволами RBAC.

- **PodCertificateRequests (бета-версія у K8s 1.35)** забезпечують нативну ідентифікацію навантажень з автоматичною ротацією сертифікатів. Kubelet генерує ключі та запитує сертифікати X.509 через об'єкти `PodCertificateRequest`, що дозволяє використовувати чистий mTLS без bearer-токенів. Це майбутнє автентифікації між Pod у Kubernetes.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Використання стандартного SA для всього | Спільні дозволи, складний аудит | Створюйте окремі SA |
| Не вимикати автомонтування | Непотрібний доступ до API | Вимкнути за замовчуванням |
| Довгоживучі токени у Secret | Ніколи не закінчуються, можуть бути викрадені | Використовуйте прив'язані токени |
| Надмірний RBAC для SA | Скомпрометований Pod = надмірний доступ | Мінімальні дозволи |
| Припущення: без токена = безпечно | Існують інші вектори атак | Захист у глибину |

---

## Тест

1. **За яким шляхом токен ServiceAccount монтується за замовчуванням?**
   <details>
   <summary>Відповідь</summary>
   `/var/run/secrets/kubernetes.io/serviceaccount/` — містить файли `token`, `ca.crt` та `namespace`.
   </details>

2. **Як вимкнути автоматичне монтування токена для ServiceAccount?**
   <details>
   <summary>Відповідь</summary>
   Встановити `automountServiceAccountToken: false` у специфікації ServiceAccount або у специфікації Pod. Специфікація Pod має пріоритет.
   </details>

3. **Що таке прив'язані токени і чому вони безпечніші?**
   <details>
   <summary>Відповідь</summary>
   Прив'язані токени є короткоживучими, прив'язаними до аудиторії та пов'язаними з конкретним Pod. Вони мають термін дії і стають недійсними після видалення Pod, на відміну від застарілих довгоживучих токенів у Secret.
   </details>

4. **Чому не всі Pod повинні використовувати стандартний ServiceAccount?**
   <details>
   <summary>Відповідь</summary>
   Спільні ServiceAccount ускладнюють аудит та контроль дозволів. Якщо одному застосунку потрібно більше дозволів, усі застосунки, що використовують цей SA, отримують їх. Окремі SA забезпечують принцип найменших привілеїв.
   </details>

---

## Практична вправа

**Завдання**: Забезпечити безпеку ServiceAccount у просторі імен.

```bash
# Підготовка
kubectl create namespace sa-security
kubectl run app1 --image=nginx -n sa-security
kubectl run app2 --image=nginx -n sa-security

# Крок 1: Перевірити поточне використання SA
kubectl get pods -n sa-security -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.serviceAccountName}{"\n"}{end}'

# Крок 2: Переконатися, що токен змонтовано
kubectl exec app1 -n sa-security -- ls /var/run/secrets/kubernetes.io/serviceaccount/

# Крок 3: Вимкнути автомонтування для стандартного SA
kubectl patch serviceaccount default -n sa-security \
  -p '{"automountServiceAccountToken": false}'

# Крок 4: Створити окремий SA (без автомонтування)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: sa-security
automountServiceAccountToken: false
EOF

# Крок 5: Перестворити Pod з новим SA
kubectl delete pod app1 app2 -n sa-security

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: app1
  namespace: sa-security
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: app2
  namespace: sa-security
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: nginx
EOF

# Крок 6: Переконатися, що токен НЕ змонтовано
kubectl exec app1 -n sa-security -- ls /var/run/secrets/kubernetes.io/serviceaccount/ 2>&1 || echo "Directory not found (expected!)"

# Крок 7: Переконатися, що Pod використовують правильний SA
kubectl get pods -n sa-security -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.serviceAccountName}{"\n"}{end}'

# Очищення
kubectl delete namespace sa-security
```

**Критерії успіху**: Pod використовують окремий SA без змонтованого токена.

---

## Підсумок

**Стандартна поведінка (небезпечна)**:
- Токен автоматично монтується до всіх Pod
- Часто використовується стандартний SA
- Довгоживучі токени

**Безпечна конфігурація**:
- Вимкнути автомонтування для стандартного SA
- Створити окремий SA для кожного застосунку
- Монтувати тільки коли потрібно
- Використовувати прив'язані токени з терміном дії

**Основні команди**:
```bash
# Вимкнути автомонтування
kubectl patch sa default -p '{"automountServiceAccountToken": false}'

# Створити токен вручну
kubectl create token myapp-sa --duration=1h
```

**Поради для іспиту**:
- Знайте налаштування автомонтування і на рівні SA, і на рівні Pod
- Практикуйте оновлення стандартного SA
- Розумійте різницю між прив'язаними та застарілими токенами

---

## Наступний модуль

[Модуль 2.3: Безпека API-сервера](module-2.3-api-server-security/) — Захист API-сервера Kubernetes.
