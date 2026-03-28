---
title: "Модуль 0.2: Налаштування лабораторії безпеки"
slug: uk/k8s/cks/part0-environment/module-0.2-security-lab
sidebar:
  order: 2
---
> **Складність**: `[СЕРЕДНЯ]` — Декілька інструментів для встановлення
>
> **Час на виконання**: 45-60 хвилин
>
> **Передумови**: Працюючий кластер Kubernetes (з CKA), налаштований kubectl

---

## Чому цей модуль важливий

CKS вимагає практичної роботи з інструментами безпеки. Ви не можете вивчити Trivy лише з документації — вам потрібно сканувати образи, бачити вразливості та практикувати виправлення. Те саме з Falco: написання правил вимагає працюючого інстансу, що генерує сповіщення.

Цей модуль будує вашу лабораторію безпеки: кластер, обладнаний усіма інструментами, які ви зустрінете на іспиті.

---

## Архітектура лабораторії

```
┌─────────────────────────────────────────────────────────────┐
│              ЛАБОРАТОРІЯ БЕЗПЕКИ CKS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Кластер Kubernetes                        │   │
│  │                                                     │   │
│  │  Розгорнуті інструменти безпеки:                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐            │   │
│  │  │ Falco   │ │ Trivy   │ │ kube-bench│            │   │
│  │  │(runtime)│ │(сканер) │ │(CIS аудит)│            │   │
│  │  └─────────┘ └─────────┘ └───────────┘            │   │
│  │                                                     │   │
│  │  Увімкнені функції безпеки:                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐            │   │
│  │  │AppArmor │ │ seccomp │ │Журналю-   │            │   │
│  │  │профілі  │ │профілі  │ │вання      │            │   │
│  │  │         │ │         │ │аудиту     │            │   │
│  │  └─────────┘ └─────────┘ └───────────┘            │   │
│  │                                                     │   │
│  │  Вразливі застосунки (для практики):               │   │
│  │  ┌─────────────────────────────────────────┐      │   │
│  │  │ Навмисно небезпечні розгортання         │      │   │
│  │  │ для практики сканування та зміцнення    │      │   │
│  │  └─────────────────────────────────────────┘      │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Варіант 1: Кластер Kind (Рекомендований для навчання)

Для більшості підготовки до CKS кластер kind з інструментами безпеки добре підходить:

```bash
# Create kind cluster with audit logging enabled
cat <<EOF > kind-cks.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        audit-policy-file: /etc/kubernetes/audit-policy.yaml
        audit-log-path: /var/log/kubernetes/audit.log
        audit-log-maxage: "30"
        audit-log-maxbackup: "3"
        audit-log-maxsize: "100"
      extraVolumes:
      - name: audit-policy
        hostPath: /etc/kubernetes/audit-policy.yaml
        mountPath: /etc/kubernetes/audit-policy.yaml
        readOnly: true
        pathType: File
      - name: audit-logs
        hostPath: /var/log/kubernetes
        mountPath: /var/log/kubernetes
        pathType: DirectoryOrCreate
  extraMounts:
  - hostPath: ./audit-policy.yaml
    containerPath: /etc/kubernetes/audit-policy.yaml
    readOnly: true
  - hostPath: ./audit-logs
    containerPath: /var/log/kubernetes
- role: worker
- role: worker
EOF

# Create the audit log directory on the host
mkdir -p audit-logs

# Create basic audit policy
cat <<EOF > audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Request
  resources:
  - group: ""
    resources: ["pods"]
- level: None
  users: ["system:kube-proxy"]
  verbs: ["watch"]
  resources:
  - group: ""
    resources: ["endpoints", "services"]
- level: Metadata
  omitStages:
  - RequestReceived
EOF

# Create the cluster
kind create cluster --name cks-lab --config kind-cks.yaml
```

---

## Варіант 2: Кластер Kubeadm (Ближче до іспиту)

Якщо у вас є кластер kubeadm з практики CKA, додайте конфігурації безпеки:

```bash
# Enable audit logging on existing cluster
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml on control plane

# Add these flags to the API server:
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# --audit-log-path=/var/log/kubernetes/audit.log
# --audit-log-maxage=30
# --audit-log-maxbackup=3
# --audit-log-maxsize=100

# Create the audit policy file
sudo mkdir -p /etc/kubernetes
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
  - group: ""
    resources: ["pods"]
    verbs: ["create", "delete"]
- level: Metadata
  omitStages:
  - RequestReceived
EOF

# Create log directory
sudo mkdir -p /var/log/kubernetes
```

---

## Встановлення інструментів безпеки

### 1. Trivy (Сканер образів)

```bash
# Install Trivy CLI
# On Ubuntu/Debian
sudo apt-get install wget apt-transport-https gnupg lsb-release -y
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy -y

# On macOS
brew install trivy

# Verify installation
trivy --version

# Test scan
trivy image nginx:latest
```

### 2. Falco (Безпека виконання)

```bash
# Install Falco using Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install Falco with modern eBPF driver
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=modern_ebpf \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# For kind clusters, use kernel module driver instead
# helm install falco falcosecurity/falco \
#   --namespace falco \
#   --create-namespace \
#   --set driver.kind=kmod

# Verify Falco is running
kubectl get pods -n falco

# Check Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco
```

### 3. kube-bench (CIS Benchmark)

```bash
# Run kube-bench as a job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Wait for completion
kubectl wait --for=condition=complete job/kube-bench --timeout=120s

# View results
kubectl logs job/kube-bench

# For detailed output, run interactively on control plane node
# Download and run kube-bench directly
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.7.0/kube-bench_0.7.0_linux_amd64.tar.gz -o kube-bench.tar.gz
tar -xvf kube-bench.tar.gz
./kube-bench run --targets=master
```

### 4. kubesec (Статичний аналіз)

```bash
# Install kubesec
# Binary installation
wget https://github.com/controlplaneio/kubesec/releases/download/v2.14.0/kubesec_linux_amd64.tar.gz
tar -xvf kubesec_linux_amd64.tar.gz
sudo mv kubesec /usr/local/bin/

# Or use Docker
# docker run -i kubesec/kubesec scan /dev/stdin < deployment.yaml

# Test kubesec
cat <<EOF | kubesec scan /dev/stdin
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
  - name: test
    image: nginx
    securityContext:
      runAsUser: 0
EOF
```

---

## Перевірка підтримки AppArmor

```bash
# Check if AppArmor is enabled (on nodes)
cat /sys/module/apparmor/parameters/enabled
# Should output: Y

# List loaded profiles
sudo aa-status

# Check if container runtime supports AppArmor
# For containerd, it's enabled by default
```

---

## Перевірка підтримки Seccomp

```bash
# Check kernel seccomp support
grep CONFIG_SECCOMP /boot/config-$(uname -r)
# Should see: CONFIG_SECCOMP=y

# Kubernetes default seccomp profile location
ls /var/lib/kubelet/seccomp/

# Create a test seccomp profile directory
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
```

---

## Розгортання вразливих застосунків (Цілі для практики)

Створіть навмисно небезпечні розгортання для практики:

```bash
# Create namespace for practice
kubectl create namespace insecure-apps

# Deploy vulnerable app 1: Privileged container
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    securityContext:
      privileged: true
EOF

# Deploy vulnerable app 2: Root user
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: root-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    securityContext:
      runAsUser: 0
EOF

# Deploy vulnerable app 3: No resource limits
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: unlimited-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    # No resources specified = unlimited
EOF

# Deploy vulnerable app 4: Vulnerable image
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: vulnerable-image
  namespace: insecure-apps
spec:
  containers:
  - name: app
    image: vulnerables/web-dvwa  # Known vulnerable image
EOF
```

---

## Скрипт валідації лабораторії

Запустіть це для перевірки готовності лабораторії:

```bash
#!/bin/bash
echo "=== CKS Lab Validation ==="
echo ""

# Check cluster
echo "1. Cluster Status:"
kubectl cluster-info | head -2
echo ""

# Check Trivy
echo "2. Trivy:"
if command -v trivy &> /dev/null; then
    trivy --version
else
    echo "   NOT INSTALLED"
fi
echo ""

# Check Falco
echo "3. Falco:"
kubectl get pods -n falco -l app.kubernetes.io/name=falco --no-headers 2>/dev/null | head -1 || echo "   NOT RUNNING"
echo ""

# Check kube-bench
echo "4. kube-bench:"
if command -v kube-bench &> /dev/null; then
    echo "   Installed"
else
    echo "   Available as Job"
fi
echo ""

# Check AppArmor
echo "5. AppArmor:"
if [ -f /sys/module/apparmor/parameters/enabled ]; then
    cat /sys/module/apparmor/parameters/enabled
else
    echo "   Check on cluster nodes"
fi
echo ""

# Check Audit Logging
echo "6. Audit Logging:"
kubectl get pods -n kube-system kube-apiserver-* -o yaml 2>/dev/null | grep -q "audit-log-path" && echo "   Enabled" || echo "   Check API server config"
echo ""

echo "=== Validation Complete ==="
```

---

## Чи знали ви?

- **Falco може виявляти криптомайнінг** у реальному часі, моніторячи підозрілі патерни використання CPU та мережеві підключення до майнінгових пулів.

- **Trivy сканує більше, ніж образи** — він може сканувати файлові системи, git-репозиторії та маніфести Kubernetes на предмет неправильних конфігурацій.

- **CIS Kubernetes Benchmark** містить понад 200 перевірок. kube-bench автоматизує їх усі.

- **AppArmor та SELinux є альтернативами** — більшість середовищ Kubernetes використовують AppArmor (стандарт Ubuntu) або SELinux (стандарт RHEL/CentOS). CKS фокусується на AppArmor.

---

## Поширені помилки

| Помилка | Чому це шкодить | Рішення |
|---------|-----------------|---------|
| Не увімкнено журналювання аудиту | Неможливо практикувати завдання з аудиту | Налаштуйте API server з політикою аудиту |
| Falco не працює | Неможливо практикувати виявлення в реальному часі | Встановіть через Helm, перевірте драйвер |
| Сканування образів лише раз | Потрібна практика робочого процесу | Інтегруйте в рутину |
| Пропуск налаштування вразливих застосунків | Немає цілей для практики зміцнення | Розгорніть навмисно небезпечні застосунки |
| Не перевірено інструменти рівня вузла | AppArmor/seccomp — функції вузла | Підключіться до вузлів по SSH, перевірте підтримку |

---

## Тест

1. **Що сканує Trivy?**
   <details>
   <summary>Відповідь</summary>
   Вразливості (CVE) в образах контейнерів, файловій системі, git-репозиторіях та неправильні конфігурації Kubernetes. Він переважно використовується для сканування вразливостей образів у CKS.
   </details>

2. **Де повинні зберігатися профілі seccomp, щоб Kubernetes міг їх використовувати?**
   <details>
   <summary>Відповідь</summary>
   У /var/lib/kubelet/seccomp/ на вузлі, де запущений Pod. Kubernetes посилається на профілі відносно цього каталогу.
   </details>

3. **Яка мета розгортання навмисно вразливих застосунків?**
   <details>
   <summary>Відповідь</summary>
   Цілі для практики сканування безпеки та зміцнення. Ви можете сканувати їх за допомогою Trivy, виявляти проблеми з Falco та практикувати виправлення — все в безпечному середовищі.
   </details>

4. **Які варіанти драйверів підтримує Falco?**
   <details>
   <summary>Відповідь</summary>
   Модуль ядра (kmod), зонд eBPF або modern_ebpf. Modern eBPF є кращим, коли підтримується. Модуль ядра є найбільш сумісним, але потребує заголовків ядра.
   </details>

---

## Практична вправа

**Завдання**: Перевірте налаштування вашої лабораторії безпеки.

```bash
# 1. Verify cluster is running
kubectl get nodes

# 2. Install Trivy and scan an image
trivy image nginx:latest | head -50

# 3. Check Falco is running (if installed)
kubectl get pods -n falco

# 4. Run kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s
kubectl logs job/kube-bench | head -100

# 5. Create a test pod and scan it
kubectl run test-pod --image=nginx:1.25
trivy image nginx:1.25

# 6. Cleanup
kubectl delete pod test-pod
kubectl delete job kube-bench
```

**Критерії успіху**: Trivy сканує образи, kube-bench видає результати, кластер доступний.

---

## Підсумок

Ваша лабораторія CKS потребує:

**Встановлені інструменти**:
- Trivy (сканування образів)
- Falco (виявлення в реальному часі)
- kube-bench (CIS benchmarks)
- kubesec (статичний аналіз)

**Увімкнені функції кластера**:
- Журналювання аудиту
- Підтримка AppArmor (рівень вузла)
- Підтримка Seccomp (рівень вузла)

**Цілі для практики**:
- Навмисно вразливі розгортання
- Образи з відомими вразливостями

Це лабораторне середовище дозволяє практикувати кожен домен іспиту CKS на практиці.

---

## Наступний модуль

[Модуль 0.3: Опанування інструментів безпеки](module-0.3-security-tools/) — Глибоке занурення у використання Trivy, Falco та kube-bench.
