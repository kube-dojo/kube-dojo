---
title: "Module 2.2: Helm Package Manager"
slug: k8s/ckad/part2-deployment/module-2.2-helm
sidebar:
  order: 2
lab:
  id: ckad-2.2-helm
  url: https://killercoda.com/kubedojo/scenario/ckad-2.2-helm
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Essential tool added to CKAD 2025
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 2.1 (Deployments), understanding of YAML templates

---

## Learning Outcomes

After completing this module, you will be able to:
- **Deploy** applications using `helm install` with custom values and namespace targeting
- **Create** value overrides to customize chart behavior for different environments
- **Debug** failed Helm releases using `helm status`, `helm history`, and rollback operations
- **Explain** Helm chart structure including templates, values, and the release lifecycle

---

## Why This Module Matters

Helm is the package manager for Kubernetes. Instead of managing dozens of YAML files, Helm bundles them into "charts" that can be installed, upgraded, and rolled back as a unit. The 2025 CKAD exam added Helm as a required skill.

You'll encounter questions like:
- Install a chart from a repository
- Upgrade a release with new values
- Rollback a failed release
- List and inspect releases
- Create basic chart customizations

> **The App Store Analogy**
>
> Helm is like an app store for Kubernetes. Charts are apps—pre-packaged, tested, and ready to install. Just like you'd install Slack with one click instead of compiling it yourself, Helm lets you install complex applications (databases, monitoring stacks, web servers) with a single command. Values are like app settings—you customize behavior without modifying the app itself.

---

## Helm Concepts

### Key Terminology

| Term | Description |
|------|-------------|
| **Chart** | Package of Kubernetes resources (like an app) |
| **Release** | Installed instance of a chart |
| **Repository** | Collection of charts (like apt repos) |
| **Values** | Configuration for customizing a chart |
| **Revision** | Version of a release after upgrade/rollback |

### How Helm Works

```
Chart (template) + Values (config) = Release (running app)
```

```
┌─────────────────────────────────────────────────────────┐
│                    Helm Workflow                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Repository          Chart            Release           │
│  ┌─────────┐       ┌─────────┐      ┌─────────┐        │
│  │ bitnami │──────▶│  nginx  │─────▶│ my-web  │        │
│  │  repo   │ pull  │  chart  │install│ release │        │
│  └─────────┘       └─────────┘      └─────────┘        │
│                         │                 │            │
│                         ▼                 ▼            │
│                    ┌─────────┐      ┌─────────┐        │
│                    │ values  │      │  Pods   │        │
│                    │  .yaml  │      │Services │        │
│                    └─────────┘      │ConfigMaps│       │
│                                     └─────────┘        │
└─────────────────────────────────────────────────────────┘
```

---

## Helm Commands

### Repository Management

```bash
# Add a repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# Add stable repo
helm repo add stable https://charts.helm.sh/stable

# Update repository cache
helm repo update

# List repositories
helm repo list

# Search for charts
helm search repo nginx
helm search repo bitnami/nginx

# Search with versions
helm search repo nginx --versions
```

### Installing Charts

```bash
# Install with default values
helm install my-release bitnami/nginx

# Install in specific namespace
helm install my-release bitnami/nginx -n production

# Install and create namespace
helm install my-release bitnami/nginx -n production --create-namespace

# Install with custom values file
helm install my-release bitnami/nginx -f values.yaml

# Install with inline values
helm install my-release bitnami/nginx --set replicaCount=3

# Install with multiple value overrides
helm install my-release bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=NodePort

# Dry-run (see what would be created)
helm install my-release bitnami/nginx --dry-run

# Generate name automatically
helm install bitnami/nginx --generate-name
```

### Listing Releases

```bash
# List releases in current namespace
helm list

# List in all namespaces
helm list -A

# List in specific namespace
helm list -n production

# List with status
helm list --all

# Filter by status
helm list --failed
helm list --pending
```

### Inspecting Charts and Releases

```bash
# Show chart info
helm show chart bitnami/nginx

# Show default values
helm show values bitnami/nginx

# Show all info
helm show all bitnami/nginx

# Get release values
helm get values my-release

# Get all release info
helm get all my-release

# Get release manifest (rendered YAML)
helm get manifest my-release

# Get release history
helm history my-release
```

### Upgrading Releases

```bash
# Upgrade with new values
helm upgrade my-release bitnami/nginx --set replicaCount=5

# Upgrade with values file
helm upgrade my-release bitnami/nginx -f new-values.yaml

# Upgrade or install if not exists
helm upgrade --install my-release bitnami/nginx

# Reuse existing values and add new ones
helm upgrade my-release bitnami/nginx --reuse-values --set image.tag=1.21
```

> **Stop and think**: You run `helm upgrade my-release bitnami/nginx --set replicaCount=5` without `--reuse-values`. What happens to all the other custom values you set during the initial install? This is a very common mistake.

### Rolling Back

```bash
# Rollback to previous revision
helm rollback my-release

# Rollback to specific revision
helm rollback my-release 2

# Check history first
helm history my-release
```

### Uninstalling

```bash
# Uninstall release
helm uninstall my-release

# Uninstall but keep history
helm uninstall my-release --keep-history

# Uninstall from namespace
helm uninstall my-release -n production
```

---

## Working with Values

> **Pause and predict**: If you pass both a values file with `replicaCount: 2` AND use `--set replicaCount=5` on the same `helm install` command, which value wins? Think about why Helm would design it this way.

### Values Hierarchy (Lowest to Highest Priority)

1. Default values in chart (`values.yaml`)
2. Parent chart values
3. Values file passed with `-f`
4. Individual values with `--set`

### Values File Example

```yaml
# my-values.yaml
replicaCount: 3

image:
  repository: nginx
  tag: "1.21"
  pullPolicy: IfNotPresent

service:
  type: NodePort
  port: 80

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

nodeSelector:
  disktype: ssd
```

### Using Values Files

```bash
# Install with values file
helm install my-release bitnami/nginx -f my-values.yaml

# Multiple values files (later overrides earlier)
helm install my-release bitnami/nginx -f values.yaml -f production.yaml

# Combine file and inline
helm install my-release bitnami/nginx -f values.yaml --set replicaCount=5
```

### Common --set Syntax

```bash
# Simple value
--set replicaCount=3

# Nested value
--set image.tag=1.21

# String value (use quotes for special chars)
--set image.repository="my-registry.com/nginx"

# Array value
--set nodeSelector.disktype=ssd

# Multiple values
--set replicaCount=3,service.type=NodePort

# List items
--set ingress.hosts[0].host=example.com
```

---

## Practical Exam Scenarios

### Scenario 1: Install and Configure

```bash
# Add repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install with custom values
helm install my-nginx bitnami/nginx \
  --set replicaCount=2 \
  --set service.type=ClusterIP \
  -n web --create-namespace

# Verify
helm list -n web
k get pods -n web
```

### Scenario 2: Upgrade and Rollback

```bash
# Check current release
helm list -n web
helm get values my-nginx -n web

# Upgrade
helm upgrade my-nginx bitnami/nginx --set replicaCount=3 -n web

# Verify upgrade
helm history my-nginx -n web
k get pods -n web

# Something goes wrong - rollback
helm rollback my-nginx 1 -n web

# Verify
helm list -n web
```

### Scenario 3: Inspect Before Install

```bash
# See what you're installing
helm show values bitnami/nginx | head -50

# Dry run to see generated manifests
helm install test bitnami/nginx --dry-run | head -n 50

# Then install
helm install test-nginx bitnami/nginx
```

---

## Chart Structure (Reference)

```
my-chart/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default configuration
├── charts/             # Dependency charts
├── templates/          # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── _helpers.tpl    # Template helpers
│   └── NOTES.txt       # Post-install notes
└── README.md
```

You won't create charts in the CKAD exam, but understanding structure helps with debugging.

---

> **What would happen if**: You run `helm install my-app bitnami/nginx` in the `default` namespace, then later run `helm list` in the `production` namespace. Would you see `my-app` in the output? Why does this matter during the exam?

## Troubleshooting Helm

### Common Issues

```bash
# Release stuck in pending-install
helm list --pending
helm uninstall stuck-release

# See what's wrong
helm get manifest my-release | k apply --dry-run=server -f -

# Debug template rendering
helm template my-release bitnami/nginx --debug

# Check release status
helm status my-release
```

### Useful Debug Commands

```bash
# See rendered templates
helm template my-release bitnami/nginx > rendered.yaml

# Validate without installing
helm install my-release bitnami/nginx --dry-run --debug

# Get notes (post-install instructions)
helm get notes my-release
```

---

## Did You Know?

- **Helm 3 removed Tiller.** Helm 2 required a server-side component (Tiller) with cluster-admin privileges. Helm 3 runs entirely client-side, using your kubeconfig permissions.

- **Helm 4 is the Current Major Version.** Released in 2025, Helm 4 defaults to server-side apply for installs and renamed flags (e.g., `--atomic` to `--rollback-on-failure`), while maintaining backward compatibility with Helm 3 charts.

- **`helm upgrade --install`** is idempotent—it installs if the release doesn't exist, or upgrades if it does. Great for CI/CD pipelines.

- **Helm stores release data as Secrets** (default) or ConfigMaps. Each revision is a separate Secret, enabling rollback to any previous state.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting `helm repo update` | Install old chart versions | Always update before installing |
| Wrong namespace | Release in default namespace | Use `-n namespace` consistently |
| `--set` typos | Values not applied | Use `--dry-run` to verify |
| Forgetting `--reuse-values` | Upgrade resets to defaults | Add flag when only changing some values |
| Not checking history before rollback | Roll back to wrong version | Run `helm history` first |

---

## Quiz

1. **Your CI/CD pipeline needs to deploy a chart that may or may not already be installed in the cluster. It should install on first run and upgrade on subsequent runs, without error. What single Helm command handles both cases?**
   <details>
   <summary>Answer</summary>
   Use `helm upgrade --install my-release bitnami/nginx`. The `--install` flag makes the command idempotent -- it installs if the release doesn't exist and upgrades if it does. This is the standard pattern for CI/CD pipelines because it eliminates the need for conditional logic to check whether a release exists. Add `--rollback-on-failure` (formerly `--atomic` in Helm 3) to automatically roll back if the upgrade fails, ensuring the pipeline never leaves a broken release behind.
   </details>

2. **A teammate upgraded a Helm release with `helm upgrade my-app bitnami/nginx --set replicaCount=5` but now reports that the `service.type` they set during initial install has reverted to the chart default `LoadBalancer` instead of their custom `ClusterIP`. What happened and how do they fix future upgrades?**
   <details>
   <summary>Answer</summary>
   Without `--reuse-values`, `helm upgrade` resets all values to chart defaults except those explicitly passed in the current command. Only `replicaCount=5` was set, so `service.type` reverted to the default. Fix with: `helm rollback my-app` to restore the previous state, then `helm upgrade my-app bitnami/nginx --reuse-values --set replicaCount=5`. The `--reuse-values` flag carries forward all values from the previous revision. Better yet, maintain a values file with all customizations and always pass it: `helm upgrade my-app bitnami/nginx -f values.yaml --set replicaCount=5`.
   </details>

3. **During the CKAD exam, you're told to "find what values the release `web-prod` is using in the `frontend` namespace." You run `helm get values web-prod` and get "release not found." The release definitely exists. What's wrong?**
   <details>
   <summary>Answer</summary>
   Helm releases are namespace-scoped. You need to specify the namespace: `helm get values web-prod -n frontend`. By default, Helm looks in the current kubectl context namespace. This is a common exam pitfall -- always include `-n <namespace>` when working with Helm releases outside the default namespace. Use `helm list -A` to find releases across all namespaces when you're not sure where a release lives.
   </details>

4. **You installed a Helm chart but the pods are crash-looping. You need to inspect the exact Kubernetes manifests that Helm generated to see if the configuration is correct. How do you view the rendered YAML without uninstalling and reinstalling?**
   <details>
   <summary>Answer</summary>
   Run `helm get manifest web-prod` to see the exact rendered Kubernetes YAML that was applied. This shows every resource (Deployments, Services, ConfigMaps, etc.) as they were sent to the API server. For debugging before deploying, use `helm template my-release bitnami/nginx -f values.yaml` to render templates locally without contacting the cluster, or `helm install my-release bitnami/nginx --dry-run --debug` to simulate the install with server-side validation.
   </details>

---

## Hands-On Exercise

**Task**: Complete Helm workflow with a real chart.

**Setup:**
```bash
# Add repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

**Part 1: Inspect and Install**
```bash
# See available values
helm show values bitnami/nginx | head -30

# Install with custom values
helm install web bitnami/nginx \
  --set replicaCount=2 \
  --set service.type=ClusterIP

# Verify installation
helm list
k get pods -l app.kubernetes.io/instance=web
```

**Part 2: Upgrade**
```bash
# Upgrade replicas
helm upgrade web bitnami/nginx --reuse-values --set replicaCount=3

# Check history
helm history web

# Verify pods
k get pods -l app.kubernetes.io/instance=web
```

**Part 3: Rollback**
```bash
# Rollback to revision 1
helm rollback web 1

# Verify reverted
helm get values web
k get pods -l app.kubernetes.io/instance=web
```

**Part 4: Cleanup**
```bash
helm uninstall web
```

---

## Practice Drills

### Drill 1: Repository Management (Target: 2 minutes)

```bash
# Add bitnami repo
helm repo add bitnami https://charts.bitnami.com/bitnami

# Update
helm repo update

# Search for mysql
helm search repo mysql

# List repos
helm repo list
```

### Drill 2: Basic Install (Target: 2 minutes)

```bash
# Install nginx
helm install drill2 bitnami/nginx

# List releases
helm list

# Check status
helm status drill2

# Cleanup
helm uninstall drill2
```

### Drill 3: Install with Values (Target: 3 minutes)

```bash
# Create values file
cat << 'EOF' > /tmp/values.yaml
replicaCount: 2
service:
  type: ClusterIP
EOF

# Install with values file
helm install drill3 bitnami/nginx -f /tmp/values.yaml

# Verify values applied
helm get values drill3

# Cleanup
helm uninstall drill3
```

### Drill 4: Upgrade and Rollback (Target: 4 minutes)

```bash
# Install
helm install drill4 bitnami/nginx --set replicaCount=1

# Verify install
helm status drill4

# Upgrade
helm upgrade drill4 bitnami/nginx --set replicaCount=3

# Check history
helm history drill4

# Rollback
helm rollback drill4 1

# Verify
helm get values drill4

# Cleanup
helm uninstall drill4
```

### Drill 5: Namespace Operations (Target: 3 minutes)

```bash
# Install in new namespace
helm install drill5 bitnami/nginx -n helm-test --create-namespace

# List in namespace
helm list -n helm-test

# Get pods in namespace
k get pods -n helm-test

# Cleanup
helm uninstall drill5 -n helm-test
k delete ns helm-test
```

### Drill 6: Complete Scenario (Target: 6 minutes)

**Scenario**: Deploy a production-ready nginx.

To make the deployment production-ready, we increase replicas for high availability, use a NodePort to ensure external connectivity, and apply strict resource limits to prevent the application from consuming excess cluster capacity.

```bash
# 1. Create values file
cat << 'EOF' > /tmp/prod-values.yaml
replicaCount: 3
service:
  type: NodePort
  nodePorts:
    http: 30080
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
EOF

# 2. Dry-run first
helm install prod-web bitnami/nginx -f /tmp/prod-values.yaml --dry-run

# 3. Install
helm install prod-web bitnami/nginx -f /tmp/prod-values.yaml

# 4. Verify
helm list
helm get values prod-web
k get pods -l app.kubernetes.io/instance=prod-web

# 5. Upgrade with more replicas
helm upgrade prod-web bitnami/nginx -f /tmp/prod-values.yaml --set replicaCount=5

# Verify upgrade
helm status prod-web
k get pods -l app.kubernetes.io/instance=prod-web

# 6. Something wrong - rollback
helm rollback prod-web 1

# 7. Cleanup
helm uninstall prod-web
```

---

## Next Module

[Module 2.3: Kustomize](../module-2.3-kustomize/) - Customize Kubernetes resources without templates.
