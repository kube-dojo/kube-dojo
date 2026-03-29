---
title: "Module 3.2: Container Logging"
slug: k8s/ckad/part3-observability/module-3.2-logging
sidebar:
  order: 2
---
> **Complexity**: `[QUICK]` - Essential daily skill, simple commands
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 1.1 (Pods), basic understanding of stdout/stderr

---

## Why This Module Matters

Logs are your window into what's happening inside containers. When something goes wrong, logs are usually the first place you look. Kubernetes doesn't store logs permanently—it provides access to stdout/stderr from running containers.

The CKAD exam tests your ability to:
- View logs from containers
- Access logs from previous container instances
- Handle multi-container pods
- Filter and search log output

> **The Flight Recorder Analogy**
>
> Container logs are like an airplane's black box. They record everything the application says (stdout/stderr). When something goes wrong, you retrieve the recording to understand what happened. But unlike a black box, Kubernetes only keeps recent logs—if the "plane" is destroyed and rebuilt, the old recording is gone.

---

## Basic Log Commands

### View Logs

```bash
# Basic logs
k logs pod-name

# Follow logs (stream)
k logs -f pod-name

# Last N lines
k logs --tail=100 pod-name

# Logs since timestamp
k logs --since=1h pod-name
k logs --since=30m pod-name
k logs --since=10s pod-name

# Logs since specific time
k logs --since-time=2024-01-15T10:00:00Z pod-name

# Show timestamps
k logs --timestamps pod-name
```

### Multi-Container Pods

```bash
# Specify container (required for multi-container)
k logs pod-name -c container-name

# All containers
k logs pod-name --all-containers=true

# List containers in pod
k get pod pod-name -o jsonpath='{.spec.containers[*].name}'
```

### Previous Container Instance

```bash
# Logs from previous crashed/restarted container
k logs pod-name --previous
k logs pod-name -p

# Previous instance of specific container
k logs pod-name -c container-name --previous
```

---

## Log Sources

### What Gets Logged

Kubernetes captures:
- **stdout**: Standard output from container processes
- **stderr**: Standard error from container processes

Applications MUST log to stdout/stderr for `kubectl logs` to work.

### What Doesn't Get Logged

- Files written inside container (e.g., `/var/log/app.log`)
- System logs from the node
- Logs from init containers (use `-c init-container-name`)

---

## Deployment and Label-Based Logs

### Logs from Deployment Pods

```bash
# Logs from all pods with a label
k logs -l app=myapp

# Follow logs from all matching pods
k logs -l app=myapp -f

# Limit to specific number of pods
k logs -l app=myapp --max-log-requests=5

# With tail
k logs -l app=myapp --tail=50
```

### Combining Filters

```bash
# Label + container + tail
k logs -l app=myapp -c nginx --tail=100

# Label + since
k logs -l app=myapp --since=30m
```

---

## Log Patterns

### Streaming Logs for Debugging

```bash
# Stream with timestamps
k logs -f --timestamps pod-name

# Stream only errors (grep)
k logs -f pod-name | grep -i error

# Stream from multiple pods
k logs -f -l app=myapp --all-containers
```

### Exporting Logs

```bash
# Save to file
k logs pod-name > pod-logs.txt

# Save with timestamps
k logs --timestamps pod-name > pod-logs-$(date +%s).txt

# All containers
k logs pod-name --all-containers > all-logs.txt
```

---

## Multi-Container Log Scenarios

### Sidecar Pattern

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-demo
spec:
  containers:
  - name: app
    image: nginx
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'while true; do echo sidecar running; sleep 10; done']
```

```bash
# View main app logs
k logs sidecar-demo -c app

# View sidecar logs
k logs sidecar-demo -c sidecar

# All containers
k logs sidecar-demo --all-containers
```

### Init Container Logs

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  initContainers:
  - name: init-setup
    image: busybox
    command: ['sh', '-c', 'echo Init complete']
  containers:
  - name: app
    image: nginx
```

```bash
# View init container logs
k logs init-demo -c init-setup
```

---

## Log Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    Container Logging                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Application                                                │
│       │                                                     │
│       ▼                                                     │
│  stdout/stderr ─────────────▶ Container Runtime             │
│                                      │                      │
│                                      ▼                      │
│                              /var/log/containers/           │
│                              /var/log/pods/                 │
│                                      │                      │
│                                      ▼                      │
│                              kubectl logs                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Pod: my-pod                                         │   │
│  │ ┌──────────────┐  ┌──────────────┐                 │   │
│  │ │ Container A  │  │ Container B  │                 │   │
│  │ │  (stdout)    │  │  (stdout)    │                 │   │
│  │ │  (stderr)    │  │  (stderr)    │                 │   │
│  │ └──────────────┘  └──────────────┘                 │   │
│  │        │                 │                          │   │
│  │        ▼                 ▼                          │   │
│  │   k logs -c a       k logs -c b                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

```bash
# Essential commands
k logs POD                      # Basic logs
k logs POD -f                   # Follow/stream
k logs POD --tail=100           # Last 100 lines
k logs POD --since=1h           # Last hour
k logs POD -c CONTAINER         # Specific container
k logs POD --previous           # Previous instance
k logs POD --all-containers     # All containers
k logs -l app=myapp             # By label
k logs POD --timestamps         # With timestamps
```

---

## Did You Know?

- **Logs are stored on the node** at `/var/log/containers/` and `/var/log/pods/`. When a pod is deleted, these logs are eventually cleaned up.

- **There's no built-in log aggregation in Kubernetes.** For production, teams use tools like Fluentd, Fluent Bit, Loki, or Elasticsearch to collect and store logs centrally.

- **Log rotation is handled by the container runtime.** By default, Docker/containerd rotates logs to prevent disk overflow, but this means old logs disappear.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting `-c` for multi-container | Error: must specify container | List containers first, then specify |
| Looking for logs from deleted pods | Logs are gone | Use `--previous` before pod restarts |
| App logging to files, not stdout | `kubectl logs` shows nothing | Configure app to log to stdout |
| Not using `--tail` for large logs | Terminal floods with data | Always limit initial output |
| Ignoring init container logs | Miss setup errors | Check init containers with `-c` |

---

## Quiz

1. **How do you view logs from a previous container instance?**
   <details>
   <summary>Answer</summary>
   `kubectl logs pod-name --previous` or `kubectl logs pod-name -p`
   </details>

2. **How do you view logs from a specific container in a multi-container pod?**
   <details>
   <summary>Answer</summary>
   `kubectl logs pod-name -c container-name`
   </details>

3. **How do you view the last 50 lines of logs from the past hour?**
   <details>
   <summary>Answer</summary>
   `kubectl logs pod-name --since=1h --tail=50`
   </details>

4. **How do you stream logs from all pods with label `app=web`?**
   <details>
   <summary>Answer</summary>
   `kubectl logs -l app=web -f` (add `--max-log-requests=N` if many pods)
   </details>

---

## Hands-On Exercise

**Task**: Practice log retrieval from various pod configurations.

**Setup:**
```bash
# Create a pod that generates logs
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: log-demo
  labels:
    app: log-demo
spec:
  containers:
  - name: logger
    image: busybox
    command: ['sh', '-c', 'i=0; while true; do echo "$(date) - Log entry $i"; i=$((i+1)); sleep 2; done']
EOF
```

**Part 1: Basic Logs**
```bash
# View logs
k logs log-demo

# Follow logs (Ctrl+C to stop)
k logs log-demo -f

# Last 5 lines
k logs log-demo --tail=5

# With timestamps
k logs log-demo --timestamps --tail=5
```

**Part 2: Multi-Container**
```bash
# Create multi-container pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: multi-log
spec:
  containers:
  - name: app
    image: nginx
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'while true; do echo Sidecar log; sleep 5; done']
EOF

# List containers
k get pod multi-log -o jsonpath='{.spec.containers[*].name}'

# View each container
k logs multi-log -c app
k logs multi-log -c sidecar

# All containers
k logs multi-log --all-containers
```

**Part 3: Previous Instance**
```bash
# Create pod that crashes
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: crasher
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo "Starting..."; echo "About to crash!"; exit 1']
EOF

# Wait for restart, then check previous logs
k get pod crasher -w
k logs crasher --previous
```

**Cleanup:**
```bash
k delete pod log-demo multi-log crasher
```

---

## Practice Drills

### Drill 1: Basic Logs (Target: 1 minute)

```bash
# Create pod
k run drill1 --image=nginx

# View logs
k logs drill1

# Cleanup
k delete pod drill1
```

### Drill 2: Follow Logs (Target: 2 minutes)

```bash
# Create logging pod
k run drill2 --image=busybox -- sh -c 'while true; do echo tick; sleep 1; done'

# Follow (Ctrl+C after a few ticks)
k logs drill2 -f

# Cleanup
k delete pod drill2
```

### Drill 3: Multi-Container (Target: 3 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: web
    image: nginx
  - name: monitor
    image: busybox
    command: ['sh', '-c', 'while true; do echo monitoring; sleep 5; done']
EOF

# Get logs from each
k logs drill3 -c web
k logs drill3 -c monitor

# Cleanup
k delete pod drill3
```

### Drill 4: Label Selection (Target: 2 minutes)

```bash
# Create multiple pods
k run drill4a --image=nginx -l app=drill4
k run drill4b --image=nginx -l app=drill4

# Logs from all with label
k logs -l app=drill4

# Cleanup
k delete pod -l app=drill4
```

### Drill 5: Previous Instance (Target: 3 minutes)

```bash
# Create crashing pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill5
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo "Run at $(date)"; sleep 5; exit 1']
EOF

# Watch it crash
k get pod drill5 -w

# After restart, get previous logs
k logs drill5 --previous

# Cleanup
k delete pod drill5
```

### Drill 6: Complete Logging Scenario (Target: 4 minutes)

**Scenario**: Debug a failing application using logs.

```bash
# Create "broken" deployment
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill6
spec:
  replicas: 2
  selector:
    matchLabels:
      app: drill6
  template:
    metadata:
      labels:
        app: drill6
    spec:
      containers:
      - name: app
        image: busybox
        command: ['sh', '-c', 'echo "Starting app"; echo "ERROR: Database connection failed"; exit 1']
EOF

# Find pods
k get pods -l app=drill6

# Check logs from one pod
k logs -l app=drill6 --tail=10

# Get previous instance logs
POD=$(k get pods -l app=drill6 -o jsonpath='{.items[0].metadata.name}')
k logs $POD --previous

# Cleanup
k delete deploy drill6
```

---

## Next Module

[Module 3.3: Debugging in Kubernetes](../module-3.3-debugging/) - Troubleshoot pods, containers, and cluster issues.
