---
title: "Module 8.1: k9s & CLI Tools"
slug: platform/toolkits/developer-experience/devex-tools/module-8.1-k9s-cli
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[QUICK]` | Time: 30-35 minutes

## Overview

`kubectl` is powerful but verbose. When you're debugging a production issue at 2 AM, you don't want to type `kubectl get pods -n production -o wide --watch`. k9s provides a terminal UI that makes Kubernetes interaction fast and visual. This module covers k9s and other CLI productivity tools.

**What You'll Learn**:
- k9s navigation and commands
- kubectl plugins with krew
- Productivity tools (stern, kubectx, kubens)
- Shell integration and aliases

**Prerequisites**:
- Basic kubectl familiarity
- Terminal/shell basics
- Kubernetes resource concepts

---

## Why This Module Matters

Developers spend hours in kubectl. Every second saved compounds. k9s turns 30-second operations into 1-second operations. Over a year, that's weeks of productivity recovered. More importantly, visual feedback means faster debugging and fewer mistakes.

> 💡 **Did You Know?** k9s was created by Fernand Galiana and has become one of the most popular Kubernetes tools with over 20,000 GitHub stars. The name is a play on "canines" (K-9s)—it's your loyal companion for Kubernetes. The project started because Fernand was tired of typing the same kubectl commands repeatedly.

---

## k9s: Terminal UI for Kubernetes

### Installation

```bash
# macOS
brew install k9s

# Linux
curl -sS https://webinstall.dev/k9s | bash

# Windows (scoop)
scoop install k9s

# Verify
k9s version
```

### Starting k9s

```bash
# Default context
k9s

# Specific context
k9s --context production

# Specific namespace
k9s -n kube-system

# Read-only mode (safe for production)
k9s --readonly

# All namespaces
k9s -A
```

### k9s Interface

```
k9s INTERFACE
════════════════════════════════════════════════════════════════════

┌─ K9s - production-cluster ──────────────────────────────────────┐
│ Context: prod │ Cluster: eks-prod │ User: admin │ K9s: 0.28.0   │
├─────────────────────────────────────────────────────────────────┤
│ <pods> all [0]                                     Filter: <f>  │
├─────────────────────────────────────────────────────────────────┤
│ NAMESPACE      NAME                    READY  STATUS   RESTARTS │
│ production     api-7f9b4c8d9-abc12     1/1    Running  0        │
│ production     web-5d4c7b8f-def34      1/1    Running  0        │
│ production     worker-6e5d8c9f-ghi56   1/1    Running  0        │
│ staging        api-8a0c5d9e-jkl78      1/1    Running  2        │
│ staging        web-9b1d6e0f-mno90      0/1    Error    5        │
├─────────────────────────────────────────────────────────────────┤
│ <0> all <1> default <2> kube-system <3> production <4> staging  │
├─────────────────────────────────────────────────────────────────┤
│ <:> Command <ctrl-a> Aliases <ctrl-d> Delete <l> Logs <s> Shell │
└─────────────────────────────────────────────────────────────────┘
```

### Essential Commands

| Key | Action |
|-----|--------|
| `:` | Command mode (type resource name) |
| `/` | Filter current view |
| `?` | Help / keyboard shortcuts |
| `Esc` | Back / clear filter |
| `Ctrl+A` | Show all aliases |
| `Enter` | View resource details |
| `d` | Describe resource |
| `y` | YAML view |
| `l` | View logs |
| `s` | Shell into container |
| `Ctrl+K` | Kill/delete resource |
| `e` | Edit resource |
| `p` | Port-forward |

### Navigation Aliases

```bash
# Quick resource access with ':'
:pods       # or :po
:deploy     # or :dp
:svc        # Services
:no         # Nodes
:ns         # Namespaces
:cm         # ConfigMaps
:sec        # Secrets
:pvc        # PersistentVolumeClaims
:ing        # Ingress
:events     # or :ev
```

### Pro Tips

```
K9S PRO TIPS
════════════════════════════════════════════════════════════════════

1. FUZZY FILTERING
   /api           → Shows pods containing "api"
   /!api          → Shows pods NOT containing "api"
   /-Error        → Filter by status

2. COLUMN SORTING
   Shift+C        → Sort by CPU
   Shift+M        → Sort by Memory
   Shift+S        → Sort by Status

3. CONTEXT SWITCHING
   :ctx            → List and switch contexts

4. NAMESPACE SWITCHING
   :ns             → List namespaces
   0-9 keys        → Quick namespace switch (shown at bottom)

5. PORT FORWARDING
   p on pod        → Interactive port-forward setup

6. MULTI-CONTAINER PODS
   l on pod        → Choose container for logs
```

> 💡 **Did You Know?** k9s can show resource usage (CPU/memory) directly in the pod list if metrics-server is installed. Press `Shift+C` to sort by CPU and instantly find the pod eating all your resources. No more `kubectl top pods | sort -k3 -r | head`.

---

## kubectl Plugins with Krew

### Installing Krew

```bash
# macOS/Linux
(
  set -x; cd "$(mktemp -d)" &&
  OS="$(uname | tr '[:upper:]' '[:lower:]')" &&
  ARCH="$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/')" &&
  KREW="krew-${OS}_${ARCH}" &&
  curl -fsSLO "https://github.com/kubernetes-sigs/krew/releases/latest/download/${KREW}.tar.gz" &&
  tar zxvf "${KREW}.tar.gz" &&
  ./"${KREW}" install krew
)

# Add to PATH
export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"

# Verify
kubectl krew version
```

### Essential Plugins

```bash
# Install plugins
kubectl krew install ctx      # Context switching
kubectl krew install ns       # Namespace switching
kubectl krew install neat     # Clean YAML output
kubectl krew install tree     # Resource hierarchy
kubectl krew install images   # Show container images
kubectl krew install access-matrix  # RBAC visualization

# Search available plugins
kubectl krew search

# Update plugins
kubectl krew upgrade
```

### Plugin Usage

```bash
# kubectx - Context switching
kubectl ctx                # List contexts
kubectl ctx production     # Switch to production
kubectl ctx -              # Switch to previous context

# kubens - Namespace switching
kubectl ns                 # List namespaces
kubectl ns production      # Switch to production
kubectl ns -               # Switch to previous namespace

# kubectl-neat - Clean YAML output
kubectl get pod nginx -o yaml | kubectl neat

# kubectl-tree - Resource hierarchy
kubectl tree deployment nginx
# Shows: Deployment → ReplicaSet → Pod

# kubectl-images - Show images
kubectl images -A          # All images in cluster
```

---

## Stern: Multi-Pod Log Tailing

### Installation

```bash
# macOS
brew install stern

# Linux
curl -LO https://github.com/stern/stern/releases/latest/download/stern_linux_amd64.tar.gz
tar xzf stern_linux_amd64.tar.gz
sudo mv stern /usr/local/bin/
```

### Usage

```bash
# Tail logs from all pods matching regex
stern "api-.*"

# Specific namespace
stern api -n production

# All namespaces
stern api --all-namespaces

# Specific container
stern api --container nginx

# Since duration
stern api --since 1h

# Color by pod
stern api --output raw

# With timestamps
stern api --timestamps

# Exclude patterns
stern ".*" --exclude-container istio-proxy
```

```
STERN VS KUBECTL LOGS
════════════════════════════════════════════════════════════════════

kubectl logs:
• One pod at a time
• Must know exact pod name
• No color coding
• Awkward multi-container

stern:
• Multiple pods simultaneously
• Regex matching
• Color-coded by pod
• Follow across deployments
• Auto-reconnects
```

---

## Shell Integration

### Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc

# Basic kubectl aliases
alias k='kubectl'
alias kg='kubectl get'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias kx='kubectl exec -it'

# Resource shortcuts
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgd='kubectl get deploy'
alias kgn='kubectl get nodes'

# Watch mode
alias kgpw='kubectl get pods -w'

# All namespaces
alias kgpa='kubectl get pods -A'

# Context/namespace
alias kctx='kubectl ctx'
alias kns='kubectl ns'

# Logs
alias klf='kubectl logs -f'
alias kl1h='kubectl logs --since=1h'

# Quick delete
alias kdel='kubectl delete'
alias krm='kubectl delete pod --force --grace-period=0'

# Apply/create
alias ka='kubectl apply -f'
alias kc='kubectl create'

# Port forward
alias kpf='kubectl port-forward'
```

### Shell Completion

```bash
# Bash
source <(kubectl completion bash)

# Zsh
source <(kubectl completion zsh)

# Fish
kubectl completion fish | source

# Also for k9s
source <(k9s completion bash)
```

### Prompt Integration

```bash
# Show current context/namespace in prompt
# Using kube-ps1 (https://github.com/jonmosco/kube-ps1)
source /path/to/kube-ps1.sh
PS1='$(kube_ps1)'$PS1

# Result:
# (⎈|prod-cluster:production) user@host:~$
```

> 💡 **Did You Know?** Kubernetes developers use aliases so heavily that many can't remember the full commands anymore. The official kubectl cheat sheet recommends aliases, and some teams enforce standard aliases so everyone speaks the same "language" when pair debugging.

> 💡 **Did You Know?** krew started as a side project and now hosts over 200 kubectl plugins. The `kubectl-neat` plugin alone has saved countless hours—it strips the clutter (managedFields, status, defaults) from YAML output, giving you clean manifests you can actually use. Many SREs consider `krew install neat` their first command on any new machine.

---

## Other Productivity Tools

### fzf Integration

```bash
# Fuzzy pod selection
kfp() {
  kubectl get pods --all-namespaces | fzf --header-lines=1 | awk '{print "-n", $1, $2}'
}

# Fuzzy context switching
kctxf() {
  kubectl ctx $(kubectl ctx | fzf)
}

# Fuzzy namespace switching
knsf() {
  kubectl ns $(kubectl ns | fzf)
}
```

### kubectl-who-can

```bash
kubectl krew install who-can

# Who can delete pods?
kubectl who-can delete pods

# Who can exec into pods in production?
kubectl who-can create pods/exec -n production
```

### kubecolor

```bash
# Colorized kubectl output
brew install kubecolor

# Use instead of kubectl
kubecolor get pods

# Alias it
alias kubectl='kubecolor'
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No context indicator | Run commands on wrong cluster | Use kube-ps1 in prompt |
| Forgetting namespace | Commands fail or hit wrong namespace | Use kubens, check with `kubectl config view` |
| Verbose commands | Slow, error-prone typing | Use aliases and k9s |
| `kubectl logs` on many pods | See only one pod | Use stern for multi-pod logs |
| No shell completion | Typing full resource names | Enable bash/zsh completion |
| `kubectl delete pod` without check | Wrong pod deleted | Use k9s confirm dialogs or aliases with -i |

---

## War Story: The Wrong Cluster Delete

*An engineer typed `kubectl delete deployment api` intending to hit staging. They were still in production context from a previous debugging session.*

**What went wrong**:
1. No visual indicator of current context
2. Muscle memory from staging work
3. Production context from earlier session

**The fix**:
```bash
# kube-ps1 in prompt shows context
PS1='$(kube_ps1)'$PS1
# (⎈|production:default) $
# ^^^^^^^^^^^^^^^^^^^^^^^
# Now you ALWAYS know where you are

# Separate terminal colors per environment
# Production = red terminal background
# Staging = green
```

**Best practice**: Different terminal profiles for different environments. Visual cues save careers.

---

## Quiz

### Question 1
How do you filter pods in k9s to only show those with "api" in the name?

<details>
<summary>Show Answer</summary>

Type `/api` in the pods view.

k9s uses fuzzy filtering:
- `/api` - shows pods containing "api"
- `/!api` - shows pods NOT containing "api"
- `/-Error` - filter by status column

Press `Esc` to clear the filter.

</details>

### Question 2
What's the difference between stern and `kubectl logs -f`?

<details>
<summary>Show Answer</summary>

**kubectl logs -f**:
- Single pod only
- Need exact pod name
- Disconnects if pod restarts
- Single container at a time

**stern**:
- Multiple pods via regex
- Color-coded by pod name
- Follows across pod restarts
- All containers by default
- `stern api-.*` tails all api pods

stern is essential for microservices debugging where one "service" is multiple pods.

</details>

### Question 3
Why use kube-ps1 in your shell prompt?

<details>
<summary>Show Answer</summary>

kube-ps1 shows current context and namespace in your prompt:

```
(⎈|production:payments) user@host:~$
```

Benefits:
1. **Always know** which cluster you're targeting
2. **Prevent accidents** - see "production" before pressing Enter
3. **No extra commands** to check context
4. **Team visibility** - others can see in screenshots/recordings

Prevents the "I deleted production" accidents that haunt engineers' dreams.

</details>

---

## Hands-On Exercise

### Objective
Install and configure k9s and CLI productivity tools.

### Environment Setup

```bash
# Install tools
brew install k9s stern kubectx

# Or on Linux
curl -sS https://webinstall.dev/k9s | bash
# Install stern and kubectx similarly
```

### Tasks

1. **Start k9s**:
   ```bash
   k9s
   ```

2. **Navigate resources**:
   - Type `:pods` to view pods
   - Press `/` and filter by name
   - Press `l` on a pod to view logs
   - Press `d` to describe
   - Press `Esc` to go back

3. **Try namespace switching**:
   - Type `:ns` to view namespaces
   - Press `Enter` to switch
   - Or use number keys shown at bottom

4. **Set up aliases**:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   alias k='kubectl'
   alias kgp='kubectl get pods'
   alias kctx='kubectl ctx'
   alias kns='kubectl ns'

   # Reload shell
   source ~/.bashrc
   ```

5. **Test stern** (if you have multiple pods):
   ```bash
   # Tail all pods in default namespace
   stern ".*" -n default
   ```

6. **Enable shell completion**:
   ```bash
   # Bash
   echo 'source <(kubectl completion bash)' >> ~/.bashrc

   # Zsh
   echo 'source <(kubectl completion zsh)' >> ~/.zshrc
   ```

### Success Criteria
- [ ] k9s launches and shows cluster resources
- [ ] Can navigate between resource types
- [ ] Can filter and search
- [ ] Aliases work (e.g., `kgp` shows pods)
- [ ] Tab completion works for kubectl

### Bonus Challenge
Set up kube-ps1 to show context/namespace in your prompt, with different colors for production vs staging.

---

## Further Reading

- [k9s Documentation](https://k9scli.io/)
- [Krew Plugin Index](https://krew.sigs.k8s.io/plugins/)
- [stern GitHub](https://github.com/stern/stern)
- [kube-ps1](https://github.com/jonmosco/kube-ps1)

---

## Next Module

Continue to [Module 8.2: Telepresence & Tilt](module-8.2-telepresence-tilt/) to learn about local development with remote Kubernetes clusters.

---

*"A 10x engineer isn't 10x smarter—they're 10x more efficient. Tools like k9s make that possible."*
