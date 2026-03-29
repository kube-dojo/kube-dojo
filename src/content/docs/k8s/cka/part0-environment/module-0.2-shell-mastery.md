---
title: "Module 0.2: Shell Mastery"
slug: k8s/cka/part0-environment/module-0.2-shell-mastery
sidebar:
  order: 2
---
> **Complexity**: `[QUICK]` - Setup once, benefit forever
>
> **Time to Complete**: 15-20 minutes
>
> **Prerequisites**: Module 0.1 (working cluster)

---

## Why This Module Matters

In the CKA exam, you have roughly **7 minutes per question on average**. Every keystroke counts. The difference between typing `kubectl get pods --all-namespaces` and `k get po -A` is small, but multiply that by 50+ kubectl commands and you've saved 5-10 minutes.

5-10 minutes is an entire question. Maybe two.

This module sets up your shell for maximum speed.

> **The Race Car Pit Crew Analogy**
>
> In Formula 1, pit stops are won or lost by fractions of a second. The crew doesn't wing it—every movement is rehearsed, every tool is positioned perfectly, every action is muscle memory. Your shell setup is your pit crew. Aliases are your pre-positioned tools. Autocomplete is your practiced muscle memory. Without preparation, you fumble. With it, you're changing tires in 2 seconds flat while others are still looking for the wrench.

---

## What You'll Configure

```
Before: kubectl get pods --namespace kube-system --output wide
After:  k get po -n kube-system -o wide

Before: kubectl describe pod nginx-deployment-abc123
After:  k describe po nginx<TAB>  → auto-completes full name

Before: kubectl config use-context production-cluster
After:  kx production<TAB>  → switches context with autocomplete
```

---

## Part 1: kubectl Autocomplete

This is **non-negotiable**. Autocomplete saves more time than any alias.

### 1.1 Enable Bash Completion

```bash
# Install bash-completion if not present
sudo apt-get install -y bash-completion

# Enable kubectl completion
echo 'source <(kubectl completion bash)' >> ~/.bashrc

# Apply now
source ~/.bashrc
```

### 1.2 Test Autocomplete

```bash
kubectl get <TAB><TAB>
```

You should see a list of resources (pods, deployments, services, etc.).

```bash
kubectl get pods -n kube<TAB>
```

Should autocomplete to `kube-system`.

```bash
kubectl describe pod cal<TAB>
```

Should autocomplete to the full Calico pod name.

> **Did You Know?**
>
> The CKA exam environment has bash completion pre-installed. But if you practice without it, you'll build bad habits (memorizing full resource names, typing everything manually). Always practice with autocomplete enabled.

---

## Part 2: Essential Aliases

### 2.1 The Core Alias

```bash
# The most important alias
echo 'alias k=kubectl' >> ~/.bashrc

# Enable completion for the alias too
echo 'complete -o default -F __start_kubectl k' >> ~/.bashrc

source ~/.bashrc
```

Now `k get pods` works just like `kubectl get pods`, with full autocomplete.

### 2.2 Resource Type Shortcuts

kubectl already supports short names. Know these:

| Full Name | Short | Example |
|-----------|-------|---------|
| pods | po | `k get po` |
| deployments | deploy | `k get deploy` |
| services | svc | `k get svc` |
| namespaces | ns | `k get ns` |
| nodes | no | `k get no` |
| configmaps | cm | `k get cm` |
| secrets | (none) | `k get secrets` |
| persistentvolumes | pv | `k get pv` |
| persistentvolumeclaims | pvc | `k get pvc` |
| serviceaccounts | sa | `k get sa` |
| replicasets | rs | `k get rs` |
| daemonsets | ds | `k get ds` |
| statefulsets | sts | `k get sts` |
| ingresses | ing | `k get ing` |
| networkpolicies | netpol | `k get netpol` |
| storageclasses | sc | `k get sc` |

These aren't aliases—they're built into kubectl. Use them.

### 2.3 Recommended Additional Aliases

Add these to your `~/.bashrc`:

```bash
# Faster common operations
alias kgp='kubectl get pods'
alias kgpa='kubectl get pods -A'
alias kgs='kubectl get svc'
alias kgn='kubectl get nodes'
alias kgd='kubectl get deploy'

# Describe shortcuts
alias kdp='kubectl describe pod'
alias kds='kubectl describe svc'
alias kdn='kubectl describe node'

# Logs
alias kl='kubectl logs'
alias klf='kubectl logs -f'

# Apply/Delete
alias ka='kubectl apply -f'
alias kd='kubectl delete -f'

# Context and namespace
alias kx='kubectl config use-context'
alias kn='kubectl config set-context --current --namespace'

# Quick debug pod
alias krun='kubectl run debug --image=busybox --rm -it --restart=Never --'
```

### 2.4 Apply All Aliases

```bash
source ~/.bashrc
```

---

## Part 3: Context and Namespace Switching

The CKA exam uses **multiple clusters**. You'll need to switch contexts constantly.

> **War Story: The $15,000 Mistake**
>
> A DevOps engineer meant to delete a test namespace in the staging cluster. They typed `kubectl delete ns payment-service` and hit enter. Then their stomach dropped—they were in the production context. 47 pods serving real customers vanished. Recovery took 3 hours. The fix? They now have `PS1` configured to show the current context in their prompt, highlighted in red when it's production. Context awareness isn't optional—it's survival.

### 3.1 Understand Contexts

```bash
# List all contexts
kubectl config get-contexts

# See current context
kubectl config current-context

# Switch context
kubectl config use-context <context-name>
```

### 3.2 Quick Context Switching

With the `kx` alias:

```bash
kx prod<TAB>     # Autocompletes to production-context
kx staging<TAB>  # Autocompletes to staging-context
```

### 3.3 Namespace Switching

Instead of typing `-n namespace` every time:

```bash
# Set default namespace for current context
kn kube-system

# Now all commands default to kube-system
k get po  # Shows kube-system pods

# Switch back to default
kn default
```

> **Gotcha: Wrong Cluster**
>
> The #1 exam mistake is solving problems on the wrong cluster. Each question specifies a context. **Always switch context first.** Make it muscle memory:
> 1. Read question
> 2. Switch context
> 3. Then solve

---

## Part 4: Environment Variables

### 4.1 Dry-Run Shortcut

You'll generate YAML templates constantly:

```bash
export do='--dry-run=client -o yaml'

# Usage
k run nginx --image=nginx $do > pod.yaml
k create deploy nginx --image=nginx $do > deploy.yaml
k expose deploy nginx --port=80 $do > svc.yaml
```

### 4.2 Force Delete (Use Carefully)

```bash
export now='--force --grace-period=0'

# Usage (when you need instant deletion)
k delete po nginx $now
```

### 4.3 Add to .bashrc

```bash
echo "export do='--dry-run=client -o yaml'" >> ~/.bashrc
echo "export now='--force --grace-period=0'" >> ~/.bashrc
source ~/.bashrc
```

---

## Part 5: Complete .bashrc Setup

Here's everything together. Add to your `~/.bashrc`:

```bash
# ============================================
# Kubernetes CKA Exam Shell Configuration
# ============================================

# kubectl completion
source <(kubectl completion bash)

# Core alias
alias k=kubectl
complete -o default -F __start_kubectl k

# Get shortcuts
alias kgp='kubectl get pods'
alias kgpa='kubectl get pods -A'
alias kgs='kubectl get svc'
alias kgn='kubectl get nodes'
alias kgd='kubectl get deploy'
alias kgpv='kubectl get pv'
alias kgpvc='kubectl get pvc'

# Describe shortcuts
alias kdp='kubectl describe pod'
alias kds='kubectl describe svc'
alias kdn='kubectl describe node'
alias kdd='kubectl describe deploy'

# Logs
alias kl='kubectl logs'
alias klf='kubectl logs -f'

# Apply/Delete
alias ka='kubectl apply -f'
alias kd='kubectl delete -f'

# Context and namespace
alias kx='kubectl config use-context'
alias kn='kubectl config set-context --current --namespace'

# Quick debug
alias krun='kubectl run debug --image=busybox --rm -it --restart=Never --'

# Environment variables
export do='--dry-run=client -o yaml'
export now='--force --grace-period=0'

# ============================================
```

---

## Part 6: Speed Test

Time yourself on these commands. Target times in parentheses.

### Without Optimization
```bash
kubectl get pods --all-namespaces --output wide      # (5+ seconds typing)
kubectl describe pod <pod-name>                       # (3+ seconds + finding name)
kubectl config use-context production                 # (3+ seconds)
```

### With Optimization
```bash
k get po -A -o wide                                   # (<2 seconds)
kdp <TAB>                                             # (<1 second with autocomplete)
kx prod<TAB>                                          # (<1 second)
```

### Generate YAML Template
```bash
# Without
kubectl run nginx --image=nginx --dry-run=client -o yaml > nginx.yaml  # (6+ seconds)

# With
k run nginx --image=nginx $do > nginx.yaml                              # (<2 seconds)
```

---

## Did You Know?

- **The exam terminal has kubectl completion pre-installed**, but your aliases won't be there. Some candidates memorize a quick alias setup script to type at the start of the exam. It takes 30 seconds and saves much more.

- **`kubectl explain`** is your friend. Instead of searching docs:
  ```bash
  k explain pod.spec.containers
  k explain deploy.spec.strategy
  ```
  This works offline and is faster than the browser.

- **You can run `kubectl` with `--help` on any subcommand**:
  ```bash
  k create --help
  k run --help
  k expose --help
  ```
  The examples in `--help` output are often exactly what you need.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not using autocomplete | Slow, typos | Always `<TAB>` |
| Forgetting `-A` for all namespaces | Miss resources | Default to `-A` when searching |
| Typing full resource names | Slow | Use short names: `po`, `svc`, `deploy` |
| Wrong context | Work on wrong cluster | Always `kx` first |
| Not using `$do` | Manually typing dry-run | Export the variable |

---

## Quiz

1. **What does this command do: `k get po -A -o wide`?**
   <details>
   <summary>Answer</summary>
   Lists all pods in all namespaces with extended information (node, IP, etc.). `-A` is short for `--all-namespaces`, `-o wide` shows additional columns.
   </details>

2. **How do you quickly generate a deployment YAML without creating it?**
   <details>
   <summary>Answer</summary>
   `k create deploy nginx --image=nginx --dry-run=client -o yaml > deploy.yaml`
   Or with the alias: `k create deploy nginx --image=nginx $do > deploy.yaml`
   </details>

3. **What's the first thing you should do when starting a new exam question?**
   <details>
   <summary>Answer</summary>
   Switch to the correct context. Each question specifies which cluster to use. Working on the wrong cluster is a common exam mistake.
   </details>

4. **What's the short name for persistentvolumeclaims?**
   <details>
   <summary>Answer</summary>
   `pvc` — as in `k get pvc`
   </details>

---

## Hands-On Exercise

**Task**: Configure your shell and verify speed improvement.

**Setup**:
```bash
# Add all configurations to ~/.bashrc (use the complete setup from Part 5)
source ~/.bashrc
```

**Speed Test**:
1. Time yourself listing all pods across namespaces
2. Time yourself describing a pod (use autocomplete)
3. Time yourself generating a deployment YAML
4. Time yourself switching contexts

**Success Criteria**:
- [ ] `k get po -A` works
- [ ] Tab completion works for pod names
- [ ] `$do` variable is set
- [ ] Can switch context in <2 seconds

**Verification**:
```bash
# Test alias
k get no

# Test completion (should show options)
k get <TAB><TAB>

# Test variable
echo $do  # Should output: --dry-run=client -o yaml

# Test YAML generation
k run test --image=nginx $do
```

---

## Practice Drills

### Drill 1: Speed Test - Basic Commands (Target: 30 seconds each)

Time yourself on these. If any takes >30 seconds, practice until automatic.

```bash
# 1. List all pods in all namespaces with wide output
# Target command: k get po -A -o wide

# 2. Get all nodes
# Target command: k get no

# 3. Describe a pod (use autocomplete for name)
# Target command: kdp <TAB>

# 4. Switch to kube-system namespace
# Target command: kn kube-system

# 5. Generate deployment YAML without creating
# Target command: k create deploy nginx --image=nginx $do
```

### Drill 2: Context Switching Race (Target: 1 minute total)

```bash
# Setup: Create multiple contexts to practice
kubectl config set-context practice-1 --cluster=kubernetes --user=kubernetes-admin
kubectl config set-context practice-2 --cluster=kubernetes --user=kubernetes-admin
kubectl config set-context practice-3 --cluster=kubernetes --user=kubernetes-admin

# TIMED DRILL: Switch between contexts as fast as possible
# Start timer now!

kx practice-1
kubectl config current-context  # Verify

kx practice-2
kubectl config current-context  # Verify

kx practice-3
kubectl config current-context  # Verify

kx kubernetes-admin@kubernetes  # Back to default
kubectl config current-context  # Verify

# Stop timer. Target: <1 minute for all 4 switches + verifications
```

### Drill 3: YAML Generation Sprint (Target: 3 minutes)

Generate all these YAML files using `$do` variable. Don't create the resources, just generate files.

```bash
# 1. Pod
k run nginx --image=nginx $do > pod.yaml

# 2. Deployment
k create deploy web --image=nginx --replicas=3 $do > deploy.yaml

# 3. Service (ClusterIP)
k create svc clusterip my-svc --tcp=80:80 $do > svc-clusterip.yaml

# 4. Service (NodePort)
k create svc nodeport my-np --tcp=80:80 $do > svc-nodeport.yaml

# 5. ConfigMap
k create cm my-config --from-literal=key=value $do > cm.yaml

# 6. Secret
k create secret generic my-secret --from-literal=password=secret123 $do > secret.yaml

# Verify all files exist and are valid
ls -la *.yaml
kubectl apply -f . --dry-run=client

# Cleanup
rm -f *.yaml
```

### Drill 4: Troubleshooting - Aliases Not Working

**Scenario**: Your aliases stopped working. Diagnose and fix.

```bash
# Setup: Break the aliases
unalias k 2>/dev/null
unset do

# Test: These should fail
k get nodes  # Command not found
echo $do     # Empty

# YOUR TASK: Fix without looking at the solution

# Verify fix worked:
k get nodes
echo $do
```

<details>
<summary>Solution</summary>

```bash
# Option 1: Re-source bashrc
source ~/.bashrc

# Option 2: Manually set (if bashrc is broken)
alias k=kubectl
complete -o default -F __start_kubectl k
export do='--dry-run=client -o yaml'

# Verify
k get nodes
echo $do
```

</details>

### Drill 5: Resource Short Names Memory Test

Without looking at the table, write commands using short names:

```bash
# 1. Get all deployments → k get ____
# 2. Get all daemonsets → k get ____
# 3. Get all statefulsets → k get ____
# 4. Get all persistentvolumes → k get ____
# 5. Get all persistentvolumeclaims → k get ____
# 6. Get all configmaps → k get ____
# 7. Get all serviceaccounts → k get ____
# 8. Get all ingresses → k get ____
# 9. Get all networkpolicies → k get ____
# 10. Get all storageclasses → k get ____
```

<details>
<summary>Answers</summary>

```bash
k get deploy
k get ds
k get sts
k get pv
k get pvc
k get cm
k get sa
k get ing
k get netpol
k get sc
```

</details>

### Drill 6: Challenge - Custom Alias Set

Create your own productivity aliases for these scenarios:

1. Show pod logs with timestamps
2. Watch pods in current namespace
3. Get events sorted by time
4. Exec into a pod with bash
5. Port-forward to port 8080

```bash
# Add to ~/.bashrc:
alias klt='kubectl logs --timestamps'
alias kw='kubectl get pods -w'
alias kev='kubectl get events --sort-by=.lastTimestamp'
alias kex='kubectl exec -it'
alias kpf='kubectl port-forward'

source ~/.bashrc

# Test each one
```

### Drill 7: Exam Simulation - First 2 Minutes

Practice what you'd do at the very start of the CKA exam:

```bash
# Timer starts NOW

# Step 1: Set up aliases (type from memory)
alias k=kubectl
complete -o default -F __start_kubectl k
export do='--dry-run=client -o yaml'
export now='--force --grace-period=0'

# Step 2: Verify setup
k get nodes
echo $do

# Step 3: Check available contexts
kubectl config get-contexts

# Timer stop. Target: <2 minutes
```

---

## Next Module

[Module 0.3: Vim for YAML](../module-0.3-vim-yaml/) - Essential Vim configuration for editing YAML files efficiently.
