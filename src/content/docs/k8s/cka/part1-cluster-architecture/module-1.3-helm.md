---
title: "Module 1.3: Helm - Kubernetes Package Manager"
slug: k8s/cka/part1-cluster-architecture/module-1.3-helm
sidebar:
  order: 4
lab:
  id: cka-1.3-helm
  url: https://killercoda.com/kubedojo/scenario/cka-1.3-helm
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Essential exam skill for 2025
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 0.1 (working cluster), basic YAML knowledge

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Deploy** applications using Helm charts (install, upgrade, rollback, uninstall)
- **Customize** Helm releases with values files and --set overrides
- **Debug** a failed Helm release by inspecting release history and template rendering
- **Explain** the Helm architecture (charts, releases, repositories) and when to use Helm vs raw manifests

---

## Why This Module Matters

Helm is **new to the CKA 2025 curriculum**. You will be tested on it.

Before Helm, deploying a complex application meant managing dozens of YAML files. A typical web app needs Deployments, Services, ConfigMaps, Secrets, Ingress, ServiceAccounts, RBAC rules... all maintained separately, all needing updates together.

Helm packages all these resources into a single **chart**. Install with one command. Upgrade with one command. Rollback with one command. It's why Helm is called "the package manager for Kubernetes"—same concept as apt/yum/brew, but for K8s resources.

> **The App Store Analogy**
>
> Think of Helm like an app store. Instead of manually downloading and configuring software piece by piece, you search for what you need (nginx, prometheus, mysql), click install, and everything is set up correctly. Want to customize? Adjust the settings (values). Want to update? Click upgrade. Something broke? Rollback to the previous version.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Install and manage applications with Helm
- Search for and use public charts
- Customize deployments with values
- Upgrade and rollback releases
- Understand chart structure (for troubleshooting)

---

## Part 1: Helm Concepts

### 1.1 Core Terminology

| Term | Definition |
|------|------------|
| **Chart** | A package of Kubernetes resources (like a .deb or .rpm) |
| **Release** | An instance of a chart running in your cluster |
| **Repository** | A collection of charts (like apt repository) |
| **Values** | Configuration options to customize a chart |

### 1.2 How Helm Works

```
┌────────────────────────────────────────────────────────────────┐
│                      Helm Architecture                          │
│                                                                 │
│   You                                                           │
│    │                                                            │
│    │  helm install myapp bitnami/nginx                         │
│    ▼                                                            │
│   ┌──────────┐     ┌─────────────┐     ┌────────────────────┐  │
│   │  Helm    │────►│   Chart     │────►│ Kubernetes API     │  │
│   │  CLI     │     │  (template) │     │ (creates resources)│  │
│   └──────────┘     └─────────────┘     └────────────────────┘  │
│        │                                                        │
│        │  Values (customization)                               │
│        │  --set replicas=3                                     │
│        │  -f myvalues.yaml                                     │
│        ▼                                                        │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │ Release stored as Secret in cluster                       │ │
│   │ (tracks version, values, manifests for rollback)          │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Helm 3 vs Helm 2

Helm 3 (current) removed Tiller—a server component that ran in the cluster. Now Helm talks directly to the Kubernetes API using your kubeconfig. This is simpler and more secure.

```bash
# Helm 3 (current) - no Tiller needed
helm install myapp ./mychart

# Helm 2 (deprecated) - required Tiller
# Don't use this anymore
```

> **Did You Know?**
>
> Helm release information is stored as Secrets in your cluster. Run `kubectl get secrets -l owner=helm` to see them. This is how Helm tracks what's installed and enables rollback.

---

## Part 2: Installing Helm

### 2.1 Install Helm CLI

```bash
# macOS
brew install helm

# Linux (script)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Linux (package manager)
# Debian/Ubuntu
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm

# Verify installation
helm version
```

### 2.2 Add a Repository

```bash
# Add the Bitnami repository (popular, well-maintained charts)
helm repo add bitnami https://charts.bitnami.com/bitnami

# Add other common repositories
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Update repository index
helm repo update

# List configured repositories
helm repo list
```

---

## Part 3: Working with Charts

### 3.1 Searching for Charts

```bash
# Search in Artifact Hub (online registry)
helm search hub nginx

# Search in your added repositories
helm search repo nginx

# Show all versions of a chart
helm search repo bitnami/nginx --versions

# Get info about a specific chart
helm show chart bitnami/nginx
helm show readme bitnami/nginx
helm show values bitnami/nginx  # See all configurable values
```

### 3.2 Installing a Chart

```bash
# Basic install
helm install my-nginx bitnami/nginx
#           ^^^^^^^^  ^^^^^^^^^^^^^
#           release   chart name
#           name

# Install in specific namespace
helm install my-nginx bitnami/nginx -n web --create-namespace

# Install with custom values
helm install my-nginx bitnami/nginx --set replicaCount=3

# Install with values file
helm install my-nginx bitnami/nginx -f myvalues.yaml

# Install specific version
helm install my-nginx bitnami/nginx --version 15.0.0

# Dry-run (see what would be created)
helm install my-nginx bitnami/nginx --dry-run

# Generate manifests only (don't install)
helm template my-nginx bitnami/nginx > manifests.yaml
```

### 3.3 Listing and Inspecting Releases

```bash
# List all releases
helm list

# List in all namespaces
helm list -A

# List including failed releases
helm list --all

# Get status of a release
helm status my-nginx

# Get values used for a release
helm get values my-nginx

# Get all values (including defaults)
helm get values my-nginx --all

# Get the manifests that were installed
helm get manifest my-nginx
```

> **Gotcha: Namespace Matters**
>
> Helm releases are namespaced. If you installed in namespace `web`, you must specify `-n web` for all subsequent commands, or you'll get "release not found."

---

## Part 4: Customizing with Values

### 4.1 Values Hierarchy

Values can be set in multiple ways. Priority (highest to lowest):
1. `--set` flags on command line
2. `-f` values files (later files override earlier)
3. Default values in chart's `values.yaml`

```bash
# Example: Multiple ways to set replicas
helm install my-nginx bitnami/nginx \
  -f base-values.yaml \
  -f production-values.yaml \
  --set replicaCount=5  # This wins
```

### 4.2 Using --set

```bash
# Simple value
helm install my-nginx bitnami/nginx --set replicaCount=3

# Nested value
helm install my-nginx bitnami/nginx --set service.type=NodePort

# Multiple values
helm install my-nginx bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=NodePort \
  --set service.nodePorts.http=30080

# Array values
helm install my-app ./mychart --set 'ingress.hosts[0]=example.com'

# String that looks like number (use quotes)
helm install my-app ./mychart --set 'version="1.0"'
```

### 4.3 Using Values Files

```yaml
# myvalues.yaml
replicaCount: 3

service:
  type: NodePort
  nodePorts:
    http: 30080

resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"

ingress:
  enabled: true
  hostname: myapp.example.com
```

```bash
# Use the values file
helm install my-nginx bitnami/nginx -f myvalues.yaml
```

### 4.4 Viewing Default Values

```bash
# See all configurable options
helm show values bitnami/nginx

# Save to file for reference
helm show values bitnami/nginx > nginx-defaults.yaml
```

> **Exam Tip**
>
> During the CKA exam, use `helm show values <chart>` to quickly see what can be customized. Don't memorize chart values—learn to look them up.

---

## Part 5: Upgrading and Rolling Back

### 5.1 Upgrading a Release

```bash
# Upgrade with new values
helm upgrade my-nginx bitnami/nginx --set replicaCount=5

# Upgrade with values file
helm upgrade my-nginx bitnami/nginx -f newvalues.yaml

# Upgrade to new chart version
helm upgrade my-nginx bitnami/nginx --version 16.0.0

# Upgrade or install if not exists
helm upgrade --install my-nginx bitnami/nginx

# Reuse values from previous release + new values
helm upgrade my-nginx bitnami/nginx --reuse-values --set replicaCount=5
```

### 5.2 Release History

```bash
# View upgrade history
helm history my-nginx

# Output:
# REVISION  STATUS      CHART           DESCRIPTION
# 1         superseded  nginx-15.0.0    Install complete
# 2         superseded  nginx-15.0.0    Upgrade complete
# 3         deployed    nginx-15.0.1    Upgrade complete
```

### 5.3 Rolling Back

```bash
# Rollback to previous revision
helm rollback my-nginx

# Rollback to specific revision
helm rollback my-nginx 1

# Dry-run rollback
helm rollback my-nginx 1 --dry-run
```

> **War Story: The Accidental Upgrade**
>
> An engineer ran `helm upgrade my-app ./chart` without specifying values, accidentally resetting everything to defaults. Production database credentials? Gone. Custom resource limits? Gone. The fix was `helm rollback my-app 1`, but it took 20 minutes to figure out what happened. Lesson: Always use `--reuse-values` or explicitly specify all values on upgrade.

---

## Part 6: Uninstalling

```bash
# Uninstall a release
helm uninstall my-nginx

# Uninstall but keep history (allows rollback)
helm uninstall my-nginx --keep-history

# Uninstall in specific namespace
helm uninstall my-nginx -n web
```

---

## Part 7: Chart Structure (For Understanding)

You don't need to create charts for CKA, but understanding structure helps troubleshooting.

```
mychart/
├── Chart.yaml          # Metadata (name, version, description)
├── values.yaml         # Default configuration
├── charts/             # Dependencies (subcharts)
├── templates/          # Kubernetes manifest templates
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl    # Template helpers
│   └── NOTES.txt       # Post-install message
└── README.md           # Documentation
```

### 7.1 How Templates Work

```yaml
# templates/deployment.yaml (simplified)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-nginx
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
      - name: nginx
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

Values from `values.yaml` or `--set` replace the `{{ }}` placeholders.

### 7.2 Debugging Templates

```bash
# See what YAML would be generated
helm template my-nginx bitnami/nginx -f myvalues.yaml

# Install with debug info
helm install my-nginx bitnami/nginx --debug --dry-run
```

---

## Part 8: Common Exam Scenarios

### 8.1 Install an Application

```bash
# Task: Install nginx with 3 replicas exposed on NodePort 30080

# Solution:
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install web bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=NodePort \
  --set service.nodePorts.http=30080
```

### 8.2 Upgrade with New Configuration

```bash
# Task: Upgrade the existing nginx release to use 5 replicas

# Solution:
helm upgrade web bitnami/nginx --reuse-values --set replicaCount=5

# Verify:
kubectl get deployment
```

### 8.3 Rollback After Failed Upgrade

```bash
# Task: Rollback to the previous working version

# Solution:
helm history web
helm rollback web

# Verify:
helm status web
```

---

## Did You Know?

- **Helm hooks** let you run jobs before/after install, upgrade, or delete. Charts use this for database migrations, certificate generation, etc.

- **Helm uses Go templates**. The `{{ }}` syntax is Go's template language. Understanding basic Go templating helps when debugging complex charts.

- **ChartMuseum** is an open-source Helm repository server. Organizations use it to host private charts.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Forgetting `-n namespace` | Release not found | Always specify namespace |
| Not using `--reuse-values` | Values reset on upgrade | Use `--reuse-values` or specify all values |
| Wrong repo URL | Chart not found | Check `helm repo list`, `helm repo update` |
| Ignoring dry-run | Unexpected resources created | Always `--dry-run` first for complex changes |
| Not checking helm status | Don't know if install succeeded | Run `helm status <release>` after install |

---

## Quiz

1. **What command shows all configurable options for a chart?**
   <details>
   <summary>Answer</summary>
   `helm show values <chart-name>` displays all the values that can be customized. Example: `helm show values bitnami/nginx`
   </details>

2. **You installed a release in namespace "production" but `helm list` shows nothing. Why?**
   <details>
   <summary>Answer</summary>
   Helm releases are namespaced. You need to specify the namespace: `helm list -n production`. Or use `helm list -A` to see all namespaces.
   </details>

3. **How do you upgrade a release while keeping existing values and changing only replicas?**
   <details>
   <summary>Answer</summary>
   `helm upgrade my-release chart-name --reuse-values --set replicaCount=5`

   The `--reuse-values` flag keeps all previously set values, and `--set` overrides only the specified value.
   </details>

4. **What's the difference between `helm template` and `helm install --dry-run`?**
   <details>
   <summary>Answer</summary>
   `helm template` renders templates locally without connecting to the cluster—it can't validate if resources already exist or if the API types are valid.

   `helm install --dry-run` connects to the cluster, performs validation, but doesn't create resources. It's a more accurate test.
   </details>

---

## Hands-On Exercise

**Task**: Deploy and manage an nginx application using Helm.

**Steps**:

1. **Add the Bitnami repository**:
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

2. **Search for nginx charts**:
```bash
helm search repo nginx
```

3. **View default values**:
```bash
helm show values bitnami/nginx | head -50
```

4. **Install nginx with custom values**:
```bash
helm install my-web bitnami/nginx \
  --set replicaCount=2 \
  --set service.type=ClusterIP \
  -n helm-demo --create-namespace
```

5. **Verify the installation**:
```bash
helm list -n helm-demo
helm status my-web -n helm-demo
kubectl get all -n helm-demo
```

6. **Upgrade to 3 replicas**:
```bash
helm upgrade my-web bitnami/nginx \
  --reuse-values \
  --set replicaCount=3 \
  -n helm-demo
```

7. **Check history**:
```bash
helm history my-web -n helm-demo
```

8. **Rollback to revision 1**:
```bash
helm rollback my-web 1 -n helm-demo
kubectl get pods -n helm-demo  # Should show 2 pods
```

9. **Get the values used**:
```bash
helm get values my-web -n helm-demo
helm get values my-web -n helm-demo --all
```

10. **Cleanup**:
```bash
helm uninstall my-web -n helm-demo
kubectl delete namespace helm-demo
```

**Success Criteria**:
- [ ] Can add repositories and search for charts
- [ ] Can install charts with custom values
- [ ] Can upgrade releases
- [ ] Can view history and rollback
- [ ] Understand the relationship between releases and Kubernetes resources

---

## Practice Drills

### Drill 1: Helm Speed Test (Target: 3 minutes)

Complete these tasks as fast as possible:

```bash
# 1. Add bitnami repo (if not added)
helm repo add bitnami https://charts.bitnami.com/bitnami

# 2. Search for redis
helm search repo redis

# 3. Show available values for redis
helm show values bitnami/redis | head -50

# 4. Install redis with custom replica count
helm install my-redis bitnami/redis --set replica.replicaCount=2 --set auth.enabled=false

# 5. List releases
helm list

# 6. Uninstall
helm uninstall my-redis
```

### Drill 2: Values File Practice (Target: 5 minutes)

```bash
# Create a values file
cat << 'EOF' > nginx-values.yaml
replicaCount: 3
service:
  type: NodePort
  nodePorts:
    http: 30080
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "100m"
EOF

# Install with values file
helm install web bitnami/nginx -f nginx-values.yaml

# Verify values applied
kubectl get pods  # Should show 3 replicas
kubectl get svc   # Should show NodePort 30080

# Get values used
helm get values web

# Cleanup
helm uninstall web
rm nginx-values.yaml
```

### Drill 3: Upgrade and Rollback Race (Target: 5 minutes)

```bash
# Install initial version
helm install rollback-test bitnami/nginx --set replicaCount=2

# Upgrade to 3 replicas
helm upgrade rollback-test bitnami/nginx --reuse-values --set replicaCount=3

# Verify
kubectl get pods | grep rollback-test | wc -l  # Should be 3

# Check history
helm history rollback-test

# Rollback to revision 1
helm rollback rollback-test 1

# Verify rollback
kubectl get pods | grep rollback-test | wc -l  # Should be 2

# Cleanup
helm uninstall rollback-test
```

### Drill 4: Troubleshooting - Wrong Values (Target: 5 minutes)

```bash
# Setup: Install with "broken" values
helm install broken-nginx bitnami/nginx --set image.tag=nonexistent-tag

# Observe the problem
kubectl get pods  # ImagePullBackOff

# YOUR TASK: Fix by upgrading with correct image tag
```

<details>
<summary>Solution</summary>

```bash
# Check current values
helm get values broken-nginx

# Fix with upgrade
helm upgrade broken-nginx bitnami/nginx --reuse-values --set image.tag=1.25

# Verify
kubectl get pods  # Running!

# Cleanup
helm uninstall broken-nginx
```

</details>

### Drill 5: Dry Run and Template (Target: 3 minutes)

```bash
# See what would be created without creating
helm install dry-test bitnami/nginx --dry-run

# Generate YAML only (for inspection or GitOps)
helm template my-nginx bitnami/nginx > nginx-manifests.yaml
cat nginx-manifests.yaml | head -100

# Validate YAML
kubectl apply -f nginx-manifests.yaml --dry-run=client

# Cleanup
rm nginx-manifests.yaml
```

### Drill 6: Multi-Release Management (Target: 5 minutes)

```bash
# Install multiple releases
helm install prod-web bitnami/nginx --set replicaCount=3 -n production --create-namespace
helm install dev-web bitnami/nginx --set replicaCount=1 -n development --create-namespace
helm install staging-web bitnami/nginx --set replicaCount=2 -n staging --create-namespace

# List all releases across namespaces
helm list -A

# Get status of specific release
helm status prod-web -n production

# Cleanup all
helm uninstall prod-web -n production
helm uninstall dev-web -n development
helm uninstall staging-web -n staging
kubectl delete ns production development staging
```

### Drill 7: Challenge - Install Without Documentation

Without looking at docs, complete this task:

**Task**: Install PostgreSQL with:
- Database name: myapp
- Username: appuser
- Password: secret123
- Storage: 5Gi

```bash
# Hint: Use helm show values to find the right parameters
helm show values bitnami/postgresql | grep -A5 -i "auth\|primary\|persistence"
```

<details>
<summary>Solution</summary>

```bash
helm install mydb bitnami/postgresql \
  --set auth.database=myapp \
  --set auth.username=appuser \
  --set auth.password=secret123 \
  --set primary.persistence.size=5Gi

# Verify
kubectl get pods
kubectl get pvc

# Cleanup
helm uninstall mydb
```

</details>

---

## Next Module

[Module 1.4: Kustomize](../module-1.4-kustomize/) - Configuration management without templates, Kubernetes-native customization.
