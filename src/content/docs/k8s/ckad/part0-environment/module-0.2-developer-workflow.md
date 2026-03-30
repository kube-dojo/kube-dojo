---
title: "Module 0.2: Developer Workflow"
slug: k8s/ckad/part0-environment/module-0.2-developer-workflow
sidebar:
  order: 2
lab:
  id: ckad-0.2-developer-workflow
  url: https://killercoda.com/kubedojo/scenario/ckad-0.2-developer-workflow
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[QUICK]` - Essential kubectl patterns
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 0.1 (CKAD Overview), CKA Module 0.2 (Shell Mastery)

---

## Why This Module Matters

CKAD is about speed AND correctness. You have 2 hours for ~15-20 tasks. Every second counts. The difference between a passing and failing score is often not knowledge—it's execution speed.

This module focuses on the developer-specific kubectl patterns you'll use repeatedly. If you completed the CKA curriculum, you already have aliases and completions set up. Here we add CKAD-specific optimizations.

> **The Carpenter's Toolbelt Analogy**
>
> A master carpenter doesn't rummage through a toolbox for each nail. Their most-used tools hang at their waist, positioned for instant access. Similarly, your most-used kubectl patterns should be at your fingertips—aliased, memorized, and practiced until they're muscle memory.

---

## Essential Aliases for CKAD

If you completed the CKA curriculum, you already have these. If not, add them now:

```bash
# Add to ~/.bashrc or ~/.zshrc

# Basic alias (MUST have)
alias k='kubectl'

# Common actions
alias kaf='kubectl apply -f'
alias kdel='kubectl delete'
alias kd='kubectl describe'
alias kg='kubectl get'
alias kl='kubectl logs'
alias kx='kubectl exec -it'

# Output formats
alias kgy='kubectl get -o yaml'
alias kgw='kubectl get -o wide'

# Dry-run pattern (CKAD essential)
alias kdr='kubectl --dry-run=client -o yaml'

# Quick run
alias kr='kubectl run'

# Watch
alias kgpw='kubectl get pods -w'
```

### CKAD-Specific Additions

```bash
# Jobs and CronJobs (CKAD heavy)
alias kcj='kubectl create job'
alias kccj='kubectl create cronjob'

# Quick debug pod
alias kdebug='kubectl run debug --image=busybox --rm -it --restart=Never --'

# Logs with container selection
alias klc='kubectl logs -c'

# Fast context switch
alias kctx='kubectl config use-context'
alias kns='kubectl config set-context --current --namespace'
```

---

## The Dry-Run Pattern: Your Best Friend

The `--dry-run=client -o yaml` pattern generates YAML without creating resources. This is essential for CKAD:

```bash
# Generate pod YAML
k run nginx --image=nginx $kdr > pod.yaml

# Generate deployment YAML
k create deploy web --image=nginx --replicas=3 $kdr > deploy.yaml

# Generate job YAML
k create job backup --image=busybox -- echo done $kdr > job.yaml

# Generate service YAML
k expose deploy web --port=80 $kdr > svc.yaml
```

### The $kdr Variable

Set this for even faster YAML generation:

```bash
export kdr='--dry-run=client -o yaml'

# Now use it anywhere
k run nginx --image=nginx $kdr > pod.yaml
k create deploy web --image=nginx $kdr > deploy.yaml
```

---

## Multi-Container Pod YAML Generation

This is a CKAD signature skill. You can't create multi-container pods imperatively—you need YAML. Here's the fastest approach:

### Step 1: Generate Base YAML

```bash
k run multi --image=nginx $kdr > multi-pod.yaml
```

### Step 2: Add Second Container

Edit the file and duplicate the container section:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
spec:
  containers:
  - name: nginx
    image: nginx
  - name: sidecar          # Add this
    image: busybox         # Add this
    command: ["sleep", "3600"]  # Add this
```

### Practice Until Automatic

This pattern appears in ~20% of CKAD questions. You should be able to:
1. Generate base YAML
2. Add a sidecar container
3. Apply and verify

All in under 2 minutes.

---

## Quick Testing Patterns

CKAD often asks you to verify your work. These patterns help:

### Test Pod-to-Service Connectivity

```bash
# One-liner test pod
k run test --image=busybox --rm -it --restart=Never -- wget -qO- http://service-name

# DNS resolution test
k run test --image=busybox --rm -it --restart=Never -- nslookup service-name

# Test with curl
k run test --image=curlimages/curl --rm -it --restart=Never -- curl http://service-name
```

### Check Pod Logs Quickly

```bash
# Last 10 lines
k logs pod-name --tail=10

# Follow logs
k logs pod-name -f

# Specific container in multi-container pod
k logs pod-name -c container-name

# Previous container (if restarted)
k logs pod-name --previous
```

### Debug Inside a Container

```bash
# Interactive shell
k exec -it pod-name -- sh

# Specific container
k exec -it pod-name -c container-name -- sh

# Run a single command
k exec pod-name -- cat /etc/config/app.conf
```

---

## JSON Path for Quick Data Extraction

Some CKAD questions ask for specific values. JSONPath helps:

```bash
# Get pod IP
k get pod nginx -o jsonpath='{.status.podIP}'

# Get all pod IPs
k get pods -o jsonpath='{.items[*].status.podIP}'

# Get container image
k get pod nginx -o jsonpath='{.spec.containers[0].image}'

# Get node where pod runs
k get pod nginx -o jsonpath='{.spec.nodeName}'
```

### Common JSONPath Patterns for CKAD

```bash
# All container names in a pod
k get pod multi -o jsonpath='{.spec.containers[*].name}'

# All service cluster IPs
k get svc -o jsonpath='{.items[*].spec.clusterIP}'

# ConfigMap data
k get cm myconfig -o jsonpath='{.data.key}'

# Secret data (base64 encoded)
k get secret mysecret -o jsonpath='{.data.password}' | base64 -d
```

---

## Namespace Management

CKAD questions often specify namespaces. Be fast:

```bash
# Create namespace
k create ns dev

# Set default namespace for session
k config set-context --current --namespace=dev

# Run command in specific namespace
k get pods -n prod

# All namespaces
k get pods -A
```

### Pro Tip: Check Namespace First

Many exam questions fail because candidates work in the wrong namespace. Always verify:

```bash
# Check current namespace
k config view --minify | grep namespace

# Or set it explicitly in each command
k get pods -n specified-namespace
```

---

## Vim Speed for YAML Editing

You'll edit YAML constantly. These Vim settings help:

```vim
" Add to ~/.vimrc
set tabstop=2
set shiftwidth=2
set expandtab
set autoindent
```

### Essential Vim Commands for YAML

```vim
" Copy a line
yy

" Paste below
p

" Delete a line
dd

" Indent a block (visual mode)
>>

" Unindent a block
<<

" Search for text
/searchterm

" Jump to line 50
:50

" Save and quit
:wq
```

### Copying YAML Blocks

When adding a sidecar container, you'll copy an existing container spec:

```vim
1. Position cursor on the line with "- name:"
2. V (visual line mode)
3. Move down to select all container lines
4. y (yank/copy)
5. Move to where you want the new container
6. p (paste)
7. Edit the pasted block
```

---

## Did You Know?

- **The `--restart=Never` flag** is crucial for test pods. Without it, Kubernetes creates a Deployment instead of a bare Pod. The `--rm` flag deletes the pod after it exits—perfect for one-off tests.

- **You can combine `-it` and `--rm`** for ephemeral debug sessions. The pod runs interactively and disappears when you exit.

- **JSONPath in kubectl** uses the same syntax as the Kubernetes API. Practicing it helps with both the exam and real-world automation.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting `--restart=Never` | Creates Deployment instead of Pod | Make it part of your test pattern |
| Wrong namespace | Resources created in default | Always check/set namespace first |
| Editing YAML with wrong indent | Invalid YAML, cryptic errors | Use `:set paste` in Vim before pasting |
| Not using `--dry-run` | Slower YAML creation | Make `$kdr` variable second nature |
| Searching docs too much | Time wasted | Memorize common specs |

---

## Quiz

1. **What command generates a Job YAML without creating the resource?**
   <details>
   <summary>Answer</summary>
   `kubectl create job myjob --image=busybox -- echo done --dry-run=client -o yaml`
   </details>

2. **How do you create a test pod that auto-deletes after running wget?**
   <details>
   <summary>Answer</summary>
   `kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://service`
   </details>

3. **What's the JSONPath to get the first container's image from a pod?**
   <details>
   <summary>Answer</summary>
   `kubectl get pod podname -o jsonpath='{.spec.containers[0].image}'`
   </details>

4. **How do you set the default namespace for your current context?**
   <details>
   <summary>Answer</summary>
   `kubectl config set-context --current --namespace=namespace-name`
   </details>

---

## Hands-On Exercise

**Task**: Practice the CKAD developer workflow patterns.

**Part 1: Dry-Run Mastery (Target: 3 minutes)**
```bash
# Generate these YAML files using --dry-run
# 1. Pod named 'web' with nginx image
# 2. Deployment named 'api' with httpd image, 2 replicas
# 3. Job named 'backup' that echoes "complete"
# 4. CronJob named 'hourly' running every hour
```

**Part 2: Multi-Container Creation (Target: 4 minutes)**
```bash
# Create a pod with two containers:
# - main: nginx
# - sidecar: busybox running "sleep 3600"
```

**Part 3: Quick Testing (Target: 2 minutes)**
```bash
# Test connectivity to a service
# Verify pod logs work
# Execute a command in a container
```

**Success Criteria**:
- [ ] All YAML files generated correctly
- [ ] Multi-container pod running with both containers Ready
- [ ] Test commands execute successfully

---

## Practice Drills

### Drill 1: Alias Verification (Target: 1 minute)

Verify your aliases work:

```bash
# These should all work
k get pods
kgy pod nginx  # Get YAML of a pod
kdr            # Should echo "--dry-run=client -o yaml"
```

### Drill 2: YAML Generation Speed (Target: 5 minutes)

Generate YAML for each resource type without looking at notes:

```bash
# Pod
k run nginx --image=nginx $kdr > /tmp/pod.yaml

# Deployment
k create deploy web --image=nginx $kdr > /tmp/deploy.yaml

# Service
k create svc clusterip mysvc --tcp=80:80 $kdr > /tmp/svc.yaml

# Job
k create job backup --image=busybox -- echo done $kdr > /tmp/job.yaml

# CronJob
k create cronjob hourly --image=busybox --schedule="0 * * * *" -- date $kdr > /tmp/cronjob.yaml

# ConfigMap
k create cm myconfig --from-literal=key=value $kdr > /tmp/cm.yaml

# Secret
k create secret generic mysecret --from-literal=password=secret $kdr > /tmp/secret.yaml
```

### Drill 3: Multi-Container Speed (Target: 3 minutes)

Create a multi-container pod from scratch:

```bash
# Generate base
k run multi --image=nginx $kdr > /tmp/multi.yaml

# Edit to add sidecar (use vim)
vim /tmp/multi.yaml

# Apply
k apply -f /tmp/multi.yaml

# Verify both containers running
k get pod multi -o jsonpath='{.spec.containers[*].name}'
# Expected: nginx sidecar

# Cleanup
k delete pod multi
```

### Drill 4: JSONPath Extraction (Target: 3 minutes)

```bash
# Create a test pod first
k run nginx --image=nginx

# Wait for running
k wait --for=condition=Ready pod/nginx

# Extract these values using JSONPath:
# 1. Pod IP
k get pod nginx -o jsonpath='{.status.podIP}'

# 2. Container image
k get pod nginx -o jsonpath='{.spec.containers[0].image}'

# 3. Node name
k get pod nginx -o jsonpath='{.spec.nodeName}'

# 4. Pod phase (Running/Pending/etc)
k get pod nginx -o jsonpath='{.status.phase}'

# Cleanup
k delete pod nginx
```

### Drill 5: Namespace Workflow (Target: 2 minutes)

```bash
# Create a namespace
k create ns ckad-test

# Set as default
k config set-context --current --namespace=ckad-test

# Verify
k config view --minify | grep namespace

# Create a pod (should go to ckad-test)
k run nginx --image=nginx

# Verify pod is in ckad-test
k get pods  # Should show nginx
k get pods -n default  # Should NOT show nginx

# Reset namespace
k config set-context --current --namespace=default

# Cleanup
k delete ns ckad-test
```

### Drill 6: Complete Developer Workflow (Target: 8 minutes)

Simulate a CKAD task end-to-end:

**Scenario**: Create a web application with a sidecar that logs access.

```bash
# 1. Create namespace
k create ns web-app

# 2. Set namespace
k config set-context --current --namespace=web-app

# 3. Generate multi-container pod YAML
k run webapp --image=nginx $kdr > /tmp/webapp.yaml

# 4. Edit to add sidecar (logs container)
# Add this container:
#   - name: logger
#     image: busybox
#     command: ["sh", "-c", "tail -f /var/log/nginx/access.log"]
#     volumeMounts:
#     - name: logs
#       mountPath: /var/log/nginx

# 5. Apply
k apply -f /tmp/webapp.yaml

# 6. Verify both containers running
k get pod webapp -o wide
k describe pod webapp | grep -A5 Containers

# 7. Test connectivity
k expose pod webapp --port=80
k run test --image=busybox --rm -it --restart=Never -- wget -qO- http://webapp

# 8. Cleanup
k config set-context --current --namespace=default
k delete ns web-app
```

---

## Next Module

[Module 1.1: Container Images](../part1-design-build/module-1.1-container-images/) - Build, tag, and push container images for CKAD.
