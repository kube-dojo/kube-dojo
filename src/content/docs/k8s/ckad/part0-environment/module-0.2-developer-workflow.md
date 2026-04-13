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

## Learning Outcomes

After completing this module, you will be able to:
- **Configure** kubectl aliases and CKAD-specific shortcuts for maximum speed
- **Create** Kubernetes resources imperatively using `kubectl run`, `kubectl create`, and `kubectl expose`
- **Debug** resource issues rapidly using `kubectl describe`, `kubectl logs`, and `kubectl exec`
- **Explain** the developer-centric kubectl workflow that distinguishes CKAD from CKA tasks

---

## Why This Module Matters

CKAD is about speed AND correctness. You have 2 hours to complete the performance-based tasks. Every second counts. The difference between a passing and failing score is often not knowledge—it's execution speed.

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
export kdr='--dry-run=client -o yaml'

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
k run nginx --image=nginx --dry-run=client -o yaml > pod.yaml

# Generate deployment YAML
k create deploy web --image=nginx --replicas=3 --dry-run=client -o yaml > deploy.yaml

# Generate job YAML
k create job backup --image=busybox --dry-run=client -o yaml -- echo done > job.yaml

# Generate service YAML
k expose deploy web --port=80 --dry-run=client -o yaml > svc.yaml
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

> **Pause and predict**: What happens if you run a test pod using `k run test --image=busybox -- wget ...` without including the `--restart=Never` flag? What happens to the Pod's lifecycle after the `wget` command completes successfully? Think about it before reading on.

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
  - name: multi
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

> **Stop and think**: You need to verify that a Service called `backend` is reachable from within the cluster. What one-liner kubectl command would you use to test this without leaving any resources behind?

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

> **Stop and think**: What would happen if you forget to switch namespaces between two consecutive exam tasks? If the first task uses the `dev` namespace and the second uses `prod`, what goes wrong, and how long might it take you to realize the mistake?

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

- **The `--restart=Never` flag** sets the pod's `restartPolicy` to `Never`. This is crucial for test pods that run a single command and exit, preventing Kubernetes from continuously restarting the container after it finishes.
- **The `--rm` flag** deletes the pod after it exits, which is perfect for one-off tests and keeps your environment clean.
- **You can combine `-it` and `--rm`** for ephemeral debug sessions. The pod runs interactively and disappears entirely when you exit the shell.
- **JSONPath in kubectl** uses a custom implementation based on the JSONPath template. Practicing it helps with both the exam and real-world automation scripts.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting `--restart=Never` on test pods | Pod enters CrashLoopBackOff as it restarts continuously after exiting | Make it part of your one-off test pattern |
| Wrong namespace | Resources are created in default or previous namespace | Always check/set namespace first |
| Editing YAML with wrong indent | Invalid YAML, cryptic errors | Use `:set paste` in Vim before pasting |
| Not using `--dry-run` | Slower YAML creation | Make `$kdr` variable second nature |
| Searching docs too much | Time wasted | Memorize common specs |

---

## Quiz

1. **Your team lead asks you to quickly generate the YAML for a new batch Job without actually running it in the cluster. You need to hand off the YAML file for code review. What's the fastest approach?**
   <details>
   <summary>Answer</summary>
   Use `kubectl create job myjob --image=busybox --dry-run=client -o yaml -- echo done > job.yaml`. The `--dry-run=client` flag generates valid YAML without contacting the API server, and `-o yaml` outputs it in YAML format. This is the standard generate-then-edit workflow for CKAD because you generate a skeleton imperatively, then customize the YAML as needed. This practice saves significant time compared to writing YAML completely from scratch.
   </details>

2. **After deploying a new Service called `api-gateway`, you need to verify it's reachable from inside the cluster -- but you don't want to leave any debug resources behind. How do you test this cleanly?**
   <details>
   <summary>Answer</summary>
   Run `kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://api-gateway`. The `--rm` flag automatically deletes the pod when it exits, and `-it` gives you interactive output. The `--restart=Never` flag is critical because it ensures the Pod does not continuously restart itself after the `wget` command finishes successfully. This one-liner is essential for CKAD, as you will use it repeatedly to verify Services, DNS resolution, and connectivity without polluting the cluster.
   </details>

3. **A CKAD exam task says: "Write the image used by the first container in pod `web-app` to the file `/opt/answer.txt`." You need to extract just the image string, not the full pod spec. How do you do this efficiently?**
   <details>
   <summary>Answer</summary>
   Use `kubectl get pod web-app -o jsonpath='{.spec.containers[0].image}' > /opt/answer.txt`. JSONPath allows you to drill directly into the pod spec and extract exactly the field you need without any extra text. The `{.spec.containers[0].image}` path navigates exactly to the first container's image field. This approach is much faster than running a `describe` followed by manual copying, and it is far less error-prone than attempting to `grep` on YAML output.
   </details>

4. **You just completed a task in the `payments` namespace and moved to the next task, which requires working in `inventory`. You create a Deployment, but `kubectl get pods` shows nothing. What likely went wrong, and what's the fastest fix?**
   <details>
   <summary>Answer</summary>
   You are likely still operating in the `payments` namespace, meaning your Deployment was created there instead of in `inventory`. The fastest fix is to switch contexts immediately using `kubectl config set-context --current --namespace=inventory`, then verify with `kubectl get pods`. To prevent this frustrating issue, you must always check or explicitly set your namespace at the start of every single exam task. Many candidates lose points purely to namespace placement errors.
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
<details>
<summary>Solution</summary>

```bash
k run web --image=nginx $kdr > web.yaml
k create deploy api --image=httpd --replicas=2 $kdr > api.yaml
k create job backup --image=busybox $kdr -- echo complete > backup.yaml
k create cronjob hourly --image=busybox --schedule="0 * * * *" $kdr -- echo complete > hourly.yaml
```
</details>

**Part 2: Multi-Container Creation (Target: 4 minutes)**
```bash
# Create a pod with two containers:
# - main: nginx
# - sidecar: busybox running "sleep 3600"
```
<details>
<summary>Solution</summary>

```bash
cat <<EOF > pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
spec:
  containers:
  - name: main
    image: nginx
  - name: sidecar
    image: busybox
    command: ["sleep", "3600"]
EOF
k apply -f pod.yaml
k wait --for=condition=Ready pod/multi
```
</details>

**Part 3: Quick Testing (Target: 2 minutes)**
```bash
# Test connectivity to a service
# Verify pod logs work
# Execute a command in a container
```
<details>
<summary>Solution</summary>

```bash
k run test --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default.svc
k logs multi -c main
k exec multi -c main -- ls /
```
</details>

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
k run test-alias --image=nginx
kgy pod test-alias  # Get YAML of a pod
echo $kdr      # Should echo "--dry-run=client -o yaml"
k delete pod test-alias
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
k create job backup --image=busybox $kdr -- echo done > /tmp/job.yaml

# CronJob
k create cronjob hourly --image=busybox --schedule="0 * * * *" $kdr -- date > /tmp/cronjob.yaml

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

# Edit to add sidecar (use vim in practice)
# vim /tmp/multi.yaml
# 
# (Using cat to overwrite for non-interactive execution)
cat <<EOF > /tmp/multi.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
  labels:
    run: multi
spec:
  containers:
  - name: multi
    image: nginx
  - name: sidecar
    image: busybox
    command: ["sleep", "3600"]
EOF

# Apply
k apply -f /tmp/multi.yaml

# Verify both containers running
k wait --for=condition=Ready pod/multi
k get pod multi -o jsonpath='{.spec.containers[*].name}'
# Expected: multi sidecar

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

# 4. Edit to add sidecar (logs container) and shared volume
# In practice, use vim to add the emptyDir volume and this container:
#   - name: logger
#     image: busybox
#     command: ["sh", "-c", "tail -f /var/log/nginx/access.log"]
#     volumeMounts:
#     - name: logs
#       mountPath: /var/log/nginx
#
# (Using cat to overwrite for non-interactive execution)
cat <<EOF > /tmp/webapp.yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
  labels:
    run: webapp
spec:
  volumes:
  - name: logs
    emptyDir: {}
  containers:
  - name: webapp
    image: nginx
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx
  - name: logger
    image: busybox
    command: ["sh", "-c", "tail -f /var/log/nginx/access.log"]
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx
EOF

# 5. Apply
k apply -f /tmp/webapp.yaml

# 6. Verify both containers running
k wait --for=condition=Ready pod/webapp
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

[Module 1.1: Container Images](/k8s/ckad/part1-design-build/module-1.1-container-images/) - Build, tag, and push container images for CKAD.