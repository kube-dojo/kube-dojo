---
title: "Module 6.3: Container Investigation"
slug: k8s/cks/part6-runtime-security/module-6.3-container-investigation
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Incident response skills
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 6.2 (Falco), Linux process basics

---

## Why This Module Matters

When you receive a security alert, you need to investigate quickly. What processes are running? What files were modified? What network connections exist? Container investigation is a critical incident response skill.

CKS tests your ability to investigate suspicious container behavior.

---

## Investigation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER INVESTIGATION WORKFLOW               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DETECT                                                 │
│     └── Alert from Falco, audit logs, or monitoring        │
│                                                             │
│  2. IDENTIFY                                               │
│     └── Which pod/container? Which node?                   │
│                                                             │
│  3. INVESTIGATE                                            │
│     ├── Running processes                                  │
│     ├── Network connections                                │
│     ├── File modifications                                 │
│     └── User activity                                      │
│                                                             │
│  4. CONTAIN                                                │
│     ├── Isolate with NetworkPolicy                        │
│     ├── Stop the container                                 │
│     └── Preserve evidence                                  │
│                                                             │
│  5. REMEDIATE                                              │
│     ├── Fix vulnerability                                  │
│     ├── Update image                                       │
│     └── Deploy clean replacement                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Investigation Tools

### kubectl Commands

```bash
# List pods with status
kubectl get pods -o wide

# Get pod details
kubectl describe pod suspicious-pod

# Get pod YAML (check securityContext, volumes)
kubectl get pod suspicious-pod -o yaml

# Check pod logs
kubectl logs suspicious-pod
kubectl logs suspicious-pod --previous  # Previous container

# Check events
kubectl get events --field-selector involvedObject.name=suspicious-pod
```

### Inside Container Investigation

```bash
# Execute into container
kubectl exec -it suspicious-pod -- /bin/bash
# Or without bash
kubectl exec -it suspicious-pod -- /bin/sh

# List running processes
kubectl exec suspicious-pod -- ps aux
kubectl exec suspicious-pod -- ps -ef

# Check network connections
kubectl exec suspicious-pod -- netstat -tulnp
kubectl exec suspicious-pod -- ss -tulnp

# Check open files
kubectl exec suspicious-pod -- ls -la /proc/1/fd/

# Check environment variables (may contain secrets!)
kubectl exec suspicious-pod -- env

# Check mounted filesystems
kubectl exec suspicious-pod -- mount
kubectl exec suspicious-pod -- df -h

# Check recent file modifications
kubectl exec suspicious-pod -- find / -mmin -60 -type f 2>/dev/null
```

---

## Process Investigation

### Using /proc Filesystem

```bash
# Inside container, examine process details
# Process 1 is usually the main container process

# Command line
cat /proc/1/cmdline | tr '\0' ' '

# Current working directory
ls -la /proc/1/cwd

# Executable path
ls -la /proc/1/exe

# Environment variables
cat /proc/1/environ | tr '\0' '\n'

# Open files
ls -la /proc/1/fd/

# Memory maps (loaded libraries)
cat /proc/1/maps

# Network connections
cat /proc/1/net/tcp
cat /proc/1/net/tcp6
```

### Using crictl (on node)

```bash
# List containers
sudo crictl ps

# Get container ID for pod
CONTAINER_ID=$(sudo crictl ps --name suspicious-pod -q)

# Inspect container
sudo crictl inspect $CONTAINER_ID

# Get container PID
PID=$(sudo crictl inspect $CONTAINER_ID | jq '.info.pid')

# Access container's namespace from host
sudo nsenter -t $PID -p -n ps aux
sudo nsenter -t $PID -p -n netstat -tulnp
```

---

## Network Investigation

### From Inside Container

```bash
# Check listening ports
netstat -tulnp
ss -tulnp

# Check established connections
netstat -an | grep ESTABLISHED
ss -s

# Check routing table
route -n
ip route

# DNS configuration
cat /etc/resolv.conf

# Check iptables rules (if accessible)
iptables -L -n
```

### From Host

```bash
# Find container network namespace
CONTAINER_ID=$(sudo crictl ps --name suspicious-pod -q)
PID=$(sudo crictl inspect $CONTAINER_ID | jq '.info.pid')

# Enter container's network namespace
sudo nsenter -t $PID -n netstat -tulnp
sudo nsenter -t $PID -n ss -tulnp

# Check for connections to suspicious IPs
sudo nsenter -t $PID -n ss -tnp | grep -E "(22|23|3389)"
```

---

## File System Investigation

### Check for Modifications

```bash
# Recent file modifications
find / -mmin -30 -type f 2>/dev/null | head -50

# Files modified today
find / -mtime 0 -type f 2>/dev/null

# Check for suspicious files in /tmp
ls -la /tmp/
ls -la /var/tmp/
ls -la /dev/shm/

# Check for hidden files
find / -name ".*" -type f 2>/dev/null

# Check for setuid/setgid binaries
find / -perm -4000 -type f 2>/dev/null
find / -perm -2000 -type f 2>/dev/null

# Check crontabs
cat /etc/crontab
ls -la /etc/cron.d/
crontab -l
```

### Check Known Attack Patterns

```bash
# Cryptocurrency miners often use these
find / -name "*xmrig*" 2>/dev/null
find / -name "*minerd*" 2>/dev/null

# Web shells
find / -name "*.php" -exec grep -l "eval\|base64_decode\|system\|passthru" {} \; 2>/dev/null

# Suspicious shell history
cat /root/.bash_history
cat /home/*/.bash_history

# Check for reverse shells
netstat -an | grep -E ":(4444|5555|6666|7777|8888|9999)"
```

---

## Ephemeral Debug Containers

When container has no shell or tools, use debug containers.

```bash
# Add debug container to running pod
kubectl debug -it suspicious-pod --image=busybox --target=main-container

# This creates a new container in the pod's namespace
# that can see processes, files, network of the target container

# Or create a copy of the pod with debug container
kubectl debug suspicious-pod --copy-to=debug-pod --container=debugger --image=ubuntu

# Debug node issues
kubectl debug node/worker-1 -it --image=ubuntu
```

### Debug Container Investigation

```bash
# Inside debug container, access target container's filesystem
# (if shareProcessNamespace is enabled)

# List processes in target container
ps aux

# Access target's filesystem via /proc
ls /proc/1/root/

# Check network
netstat -tulnp
```

---

## Real Exam Scenarios

### Scenario 1: Investigate Suspicious Process

```bash
# Alert: Crypto miner detected in pod "app" in namespace "production"

# Step 1: Get pod details
kubectl get pod app -n production -o wide

# Step 2: Check running processes
kubectl exec -n production app -- ps aux

# Look for suspicious processes like:
# - xmrig, minerd, cpuminer
# - Random character process names
# - Processes with high CPU usage

# Step 3: Check process details
kubectl exec -n production app -- cat /proc/$(pgrep suspicious)/cmdline

# Step 4: Check network connections
kubectl exec -n production app -- netstat -tulnp

# Look for:
# - Connections to mining pools (port 3333, 4444)
# - Connections to suspicious IPs

# Step 5: Check recent file modifications
kubectl exec -n production app -- find /tmp -mmin -60

# Step 6: Document findings and delete pod
kubectl delete pod app -n production
```

### Scenario 2: Network Exfiltration Investigation

```bash
# Alert: Outbound connection to suspicious IP from pod "data-processor"

# Step 1: Check current connections
kubectl exec data-processor -- ss -tnp

# Step 2: Check DNS queries (if possible)
kubectl exec data-processor -- cat /etc/resolv.conf

# Step 3: Check for data staging
kubectl exec data-processor -- ls -la /tmp/
kubectl exec data-processor -- ls -la /var/tmp/

# Step 4: Check what process made the connection
kubectl exec data-processor -- netstat -anp | grep <suspicious-ip>

# Step 5: Isolate the pod with NetworkPolicy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-data-processor
spec:
  podSelector:
    matchLabels:
      app: data-processor
  policyTypes:
  - Egress
  egress: []  # Block all egress
EOF

# Step 6: Continue investigation with pod isolated
```

### Scenario 3: File System Tampering

```bash
# Alert: Write to /etc detected in container

# Step 1: Check what was modified
kubectl exec suspicious-pod -- find /etc -mmin -30 -type f

# Step 2: Check file contents
kubectl exec suspicious-pod -- cat /etc/passwd
kubectl exec suspicious-pod -- cat /etc/shadow  # If readable

# Step 3: Compare with original image
# Get image name
IMAGE=$(kubectl get pod suspicious-pod -o jsonpath='{.spec.containers[0].image}')

# Run fresh container to compare
kubectl run compare --image=$IMAGE --rm -it -- cat /etc/passwd

# Step 4: Check for persistence mechanisms
kubectl exec suspicious-pod -- crontab -l
kubectl exec suspicious-pod -- ls -la /etc/cron.d/
kubectl exec suspicious-pod -- ls -la /etc/init.d/
```

---

## Evidence Preservation

### Capture Container State

```bash
# Export pod YAML
kubectl get pod suspicious-pod -o yaml > pod-evidence.yaml

# Export logs
kubectl logs suspicious-pod > pod-logs.txt
kubectl logs suspicious-pod --previous > pod-logs-previous.txt

# Export events
kubectl get events --field-selector involvedObject.name=suspicious-pod > events.txt

# If possible, create filesystem snapshot
kubectl exec suspicious-pod -- tar -czf - / > container-filesystem.tar.gz
```

### Using crictl for Evidence

```bash
# On the node
CONTAINER_ID=$(sudo crictl ps --name suspicious-pod -q)

# Create checkpoint (if supported)
sudo crictl checkpoint $CONTAINER_ID

# Export container filesystem
sudo crictl export $CONTAINER_ID > container-export.tar
```

---

## Did You Know?

- **Ephemeral debug containers** (kubectl debug) were introduced in Kubernetes 1.18 and became stable in 1.25. They're perfect for investigating distroless images.

- **Containers share the host kernel** but have separate /proc views. Each container's /proc shows only its own processes.

- **nsenter** allows you to enter any Linux namespace. Combined with the container PID, you can access container's network, mount, and PID namespaces from the host.

- **Read-only root filesystem doesn't prevent all writes**. Attackers can still write to mounted volumes, /tmp (if tmpfs), and /dev/shm.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Deleting pod immediately | Evidence lost | Investigate first |
| No network isolation | Attack continues | Apply NetworkPolicy first |
| Missing logs | Can't reconstruct timeline | Export before deletion |
| Not checking all containers | Multi-container pods | Check sidecars too |
| Forgetting previous logs | First container crashed | Use --previous flag |

---

## Quiz

1. **How do you check running processes in a container without exec access?**
   <details>
   <summary>Answer</summary>
   Use `kubectl debug` to create an ephemeral debug container, or use `crictl inspect` and `nsenter` from the node to enter the container's namespaces.
   </details>

2. **What command finds files modified in the last 30 minutes?**
   <details>
   <summary>Answer</summary>
   `find / -mmin -30 -type f 2>/dev/null`. The `-mmin` flag specifies minutes, and `-mtime` specifies days.
   </details>

3. **How do you isolate a suspicious pod while investigating?**
   <details>
   <summary>Answer</summary>
   Apply a NetworkPolicy with empty egress rules to block all outbound traffic. This prevents data exfiltration while you investigate.
   </details>

4. **What's the advantage of using ephemeral debug containers?**
   <details>
   <summary>Answer</summary>
   They work with distroless images that have no shell, share the target container's namespaces for full visibility, and don't modify the original container.
   </details>

---

## Hands-On Exercise

**Task**: Practice container investigation techniques.

```bash
# Step 1: Create a "suspicious" pod for investigation
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: suspicious-app
  labels:
    app: suspicious
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "
      echo 'suspicious data' > /tmp/exfil.txt &&
      while true; do sleep 10; done
    "]
EOF

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/suspicious-app --timeout=60s

# Step 2: Investigate processes
echo "=== Running Processes ==="
kubectl exec suspicious-app -- ps aux

# Step 3: Check network (limited in busybox)
echo "=== Network Configuration ==="
kubectl exec suspicious-app -- cat /etc/resolv.conf
kubectl exec suspicious-app -- ip addr 2>/dev/null || kubectl exec suspicious-app -- ifconfig

# Step 4: Check for recent file modifications
echo "=== Recent File Modifications ==="
kubectl exec suspicious-app -- find / -mmin -10 -type f 2>/dev/null

# Step 5: Check /tmp for suspicious files
echo "=== /tmp Contents ==="
kubectl exec suspicious-app -- ls -la /tmp/
kubectl exec suspicious-app -- cat /tmp/exfil.txt

# Step 6: Check process details
echo "=== Main Process Details ==="
kubectl exec suspicious-app -- cat /proc/1/cmdline | tr '\0' ' '
echo ""

# Step 7: Check environment
echo "=== Environment Variables ==="
kubectl exec suspicious-app -- env | head -10

# Step 8: Create isolation NetworkPolicy
echo "=== Creating Isolation Policy ==="
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-suspicious
spec:
  podSelector:
    matchLabels:
      app: suspicious
  policyTypes:
  - Egress
  - Ingress
  egress: []
  ingress: []
EOF

echo "Pod isolated with NetworkPolicy"

# Step 9: Preserve evidence
echo "=== Preserving Evidence ==="
kubectl get pod suspicious-app -o yaml > /tmp/pod-evidence.yaml
kubectl logs suspicious-app > /tmp/pod-logs.txt
echo "Evidence saved to /tmp/"

# Step 10: Cleanup
kubectl delete pod suspicious-app
kubectl delete networkpolicy isolate-suspicious
rm -f /tmp/pod-evidence.yaml /tmp/pod-logs.txt

echo "=== Investigation Complete ==="
```

**Success criteria**: Understand investigation commands and workflow.

---

## Summary

**Investigation Steps**:
1. Detect (alerts, logs)
2. Identify (pod, namespace, node)
3. Investigate (processes, network, files)
4. Contain (NetworkPolicy, isolation)
5. Remediate (delete, redeploy)

**Key Commands**:
- `kubectl exec` for running commands
- `kubectl debug` for debug containers
- `kubectl logs` for application logs
- `crictl` and `nsenter` on nodes

**What to Check**:
- Running processes (ps aux)
- Network connections (netstat, ss)
- File modifications (find -mmin)
- Environment variables (env)

**Exam Tips**:
- Know kubectl exec syntax
- Understand /proc filesystem
- Be able to isolate pods
- Remember evidence preservation

---

## Next Module

[Module 6.4: Immutable Infrastructure](../module-6.4-immutable-infrastructure/) - Building containers that can't be modified at runtime.
