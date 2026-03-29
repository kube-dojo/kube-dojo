---
title: "Module 1.2: kubectl Basics"
slug: prerequisites/kubernetes-basics/module-1.2-kubectl-basics
sidebar:
  order: 3
lab:
  id: "prereq-k8s-1.2-kubectl"
  url: "https://killercoda.com/kubedojo/scenario/prereq-k8s-1.2-kubectl"
  duration: "30 min"
  difficulty: "beginner"
  environment: "kubernetes"
---
> **Complexity**: `[MEDIUM]` - Essential commands to master
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 1 (First Cluster running)

---

## Why This Module Matters

kubectl is your primary interface to Kubernetes. Every interaction—creating resources, debugging problems, checking status—goes through kubectl. Mastering it is essential for both daily work and certification exams.

---

## The kubectl Command Structure

```
kubectl [command] [TYPE] [NAME] [flags]

Examples:
kubectl get pods                    # List all pods
kubectl get pod nginx              # Get specific pod
kubectl get pods -o wide           # More output columns
kubectl describe pod nginx         # Detailed info
kubectl delete pod nginx           # Delete resource
```

---

## Essential Commands

### Getting Information

```bash
# List resources
kubectl get pods                   # Pods in current namespace
kubectl get pods -A                # Pods in all namespaces
kubectl get pods -n kube-system    # Pods in specific namespace
kubectl get pods -o wide           # More columns (node, IP)
kubectl get pods -o yaml           # Full YAML output
kubectl get pods -o json           # JSON output

# Common resource types
kubectl get nodes                  # Cluster nodes
kubectl get deployments           # Deployments
kubectl get services              # Services
kubectl get all                   # Common resources
kubectl get events                # Cluster events

# Describe (detailed info)
kubectl describe pod nginx
kubectl describe node kind-control-plane
kubectl describe deployment myapp
```

### Creating Resources

```bash
# From YAML file
kubectl apply -f pod.yaml
kubectl apply -f .                  # All YAML files in directory
kubectl apply -f https://example.com/resource.yaml  # From URL

# Imperatively (quick creation)
kubectl run nginx --image=nginx
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80

# Generate YAML without creating
kubectl run nginx --image=nginx --dry-run=client -o yaml
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml
```

### Modifying Resources

```bash
# Apply changes
kubectl apply -f updated-pod.yaml

# Edit live resource
kubectl edit deployment nginx

# Patch resource
kubectl patch deployment nginx -p '{"spec":{"replicas":3}}'

# Scale
kubectl scale deployment nginx --replicas=5

# Set image
kubectl set image deployment/nginx nginx=nginx:1.25
```

### Deleting Resources

```bash
# Delete by name
kubectl delete pod nginx
kubectl delete deployment nginx

# Delete from file
kubectl delete -f pod.yaml

# Delete all of a type
kubectl delete pods --all
kubectl delete pods --all -n my-namespace

# Force delete (stuck pods)
kubectl delete pod nginx --force --grace-period=0
```

---

## Output Formats

```bash
# Default (table)
kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   0          5m

# Wide (more columns)
kubectl get pods -o wide
# NAME    READY   STATUS    RESTARTS   AGE   IP           NODE
# nginx   1/1     Running   0          5m    10.244.0.5   kind-control-plane

# YAML
kubectl get pod nginx -o yaml

# JSON
kubectl get pod nginx -o json

```

> **Bonus: Power User Syntax** (come back to these after you're comfortable with the basics)
>
> ```bash
> # Custom columns (great for dashboards)
> kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase
>
> # JSONPath (extract specific fields — exam gold!)
> kubectl get pod nginx -o jsonpath='{.status.podIP}'
> kubectl get pods -o jsonpath='{.items[*].metadata.name}'
> ```

---

## Working with Namespaces

```bash
# List namespaces
kubectl get namespaces
kubectl get ns

# Set default namespace
kubectl config set-context --current --namespace=my-namespace

# Create namespace
kubectl create namespace my-namespace

# Run command in specific namespace
kubectl get pods -n kube-system
kubectl get pods --namespace=my-namespace

# All namespaces
kubectl get pods -A
kubectl get pods --all-namespaces
```

---

## Debugging Commands

```bash
# View logs
kubectl logs nginx                  # Current logs
kubectl logs nginx -f               # Follow (stream) logs
kubectl logs nginx --tail=100       # Last 100 lines
kubectl logs nginx -c container1    # Specific container
kubectl logs nginx --previous       # Previous instance logs

# Execute command in container
kubectl exec nginx -- ls /          # Run command
kubectl exec -it nginx -- bash      # Interactive shell
kubectl exec -it nginx -- sh        # If bash not available

# Port forwarding
kubectl port-forward pod/nginx 8080:80
kubectl port-forward svc/nginx 8080:80
# Access at localhost:8080

# Copy files
kubectl cp nginx:/etc/nginx/nginx.conf ./nginx.conf
kubectl cp ./local-file.txt nginx:/tmp/
```

---

## Useful Flags

```bash
# Watch (auto-refresh)
kubectl get pods -w
kubectl get pods --watch

# Labels and selectors
kubectl get pods -l app=nginx
kubectl get pods --selector=app=nginx,tier=frontend

# Sort output
kubectl get pods --sort-by=.metadata.creationTimestamp
kubectl get pods --sort-by=.status.startTime

# Field selectors
kubectl get pods --field-selector=status.phase=Running
kubectl get pods --field-selector=spec.nodeName=kind-control-plane

# Show labels
kubectl get pods --show-labels

# Output to file
kubectl get pod nginx -o yaml > pod.yaml
```

---

## Configuration and Context

```bash
# View current config
kubectl config view
kubectl config current-context

# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context kind-kind
kubectl config use-context my-cluster

# Set default namespace for context
kubectl config set-context --current --namespace=default
```

---

## Visualization: kubectl Flow

```
┌─────────────────────────────────────────────────────────────┐
│              HOW kubectl WORKS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │   Your Terminal │                                       │
│  │   $ kubectl ... │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │   ~/.kube/config│  ← Credentials, cluster info         │
│  │   (kubeconfig)  │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼  HTTPS                                         │
│  ┌─────────────────┐                                       │
│  │   API Server    │  ← Validates, processes              │
│  │   (K8s cluster) │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │     Response    │  ← YAML/JSON/Table                   │
│  │                 │                                       │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Helpful Shortcuts

### Shell Alias (Add to ~/.bashrc or ~/.zshrc)

```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kaf='kubectl apply -f'
alias kdel='kubectl delete'
alias klog='kubectl logs'
alias kexec='kubectl exec -it'
```

### kubectl Autocomplete

```bash
# Bash
source <(kubectl completion bash)
echo 'source <(kubectl completion bash)' >> ~/.bashrc

# Zsh
source <(kubectl completion zsh)
echo 'source <(kubectl completion zsh)' >> ~/.zshrc

# With alias
complete -F __start_kubectl k  # Bash
compdef k=kubectl              # Zsh
```

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| List pods | `kubectl get pods` |
| All namespaces | `kubectl get pods -A` |
| Detailed info | `kubectl describe pod NAME` |
| View logs | `kubectl logs NAME` |
| Shell access | `kubectl exec -it NAME -- bash` |
| Port forward | `kubectl port-forward pod/NAME 8080:80` |
| Create from file | `kubectl apply -f file.yaml` |
| Delete | `kubectl delete pod NAME` |
| Generate YAML | `kubectl run NAME --image=IMG --dry-run=client -o yaml` |

---

## Did You Know?

- **kubectl talks to the API server over HTTPS.** All commands are API calls. You could use `curl` instead (but why would you?).

- **`-o yaml` is exam gold.** Get any resource as YAML, modify it, apply it back. Faster than writing from scratch.

- **`--dry-run=client -o yaml` generates templates.** Never memorize YAML structure—generate it.

- **kubectl has built-in help.** `kubectl explain pod.spec.containers` shows field documentation.

---

## Common Mistakes

| Mistake | Solution |
|---------|----------|
| Forgetting namespace | Use `-n namespace` or set default |
| Wrong context | `kubectl config use-context` |
| Typos in resource names | Use tab completion |
| Not using `-o yaml` for templates | Always generate, don't memorize |
| Using `create` instead of `apply` | `apply` is idempotent, prefer it |

---

## Quiz

1. **How do you see all pods in all namespaces?**
   <details>
   <summary>Answer</summary>
   `kubectl get pods -A` or `kubectl get pods --all-namespaces`
   </details>

2. **How do you generate YAML for a pod without creating it?**
   <details>
   <summary>Answer</summary>
   `kubectl run nginx --image=nginx --dry-run=client -o yaml`
   </details>

3. **How do you get an interactive shell in a running container?**
   <details>
   <summary>Answer</summary>
   `kubectl exec -it POD_NAME -- bash` (or `-- sh` if bash isn't available)
   </details>

4. **How do you follow logs in real-time?**
   <details>
   <summary>Answer</summary>
   `kubectl logs POD_NAME -f` or `kubectl logs POD_NAME --follow`
   </details>

---

## Hands-On Exercise

**Task**: Practice essential kubectl commands.

```bash
# 1. Create a namespace
kubectl create namespace practice

# 2. Run a pod in that namespace
kubectl run nginx --image=nginx -n practice

# 3. List pods in the namespace
kubectl get pods -n practice

# 4. Get detailed info
kubectl describe pod nginx -n practice

# 5. View logs
kubectl logs nginx -n practice

# 6. Execute a command
kubectl exec nginx -n practice -- nginx -v

# 7. Get YAML output
kubectl get pod nginx -n practice -o yaml

# 8. Delete everything
kubectl delete namespace practice
```

**Success criteria**: All commands complete without error.

---

## Summary

Essential kubectl commands:

**Information**:
- `kubectl get` - List resources
- `kubectl describe` - Detailed info
- `kubectl logs` - Container output

**Creation**:
- `kubectl apply -f` - Create/update from file
- `kubectl run` - Quick pod creation
- `kubectl create` - Create resources

**Modification**:
- `kubectl edit` - Edit live resource
- `kubectl scale` - Change replicas
- `kubectl delete` - Remove resources

**Debugging**:
- `kubectl exec` - Run commands in container
- `kubectl port-forward` - Local access
- `kubectl logs` - View output

---

## Next Module

[Module 3: Pods](../module-1.3-pods/) - The atomic unit of Kubernetes.
