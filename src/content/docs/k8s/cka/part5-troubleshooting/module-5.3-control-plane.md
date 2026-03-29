---
title: "Module 5.3: Control Plane Failures"
slug: k8s/cka/part5-troubleshooting/module-5.3-control-plane
sidebar:
  order: 4
---
> **Complexity**: `[COMPLEX]` - Critical infrastructure troubleshooting
>
> **Time to Complete**: 50-60 minutes
>
> **Prerequisites**: Module 5.1 (Methodology), Module 1.1 (Control Plane Deep-Dive)

---

## Why This Module Matters

When the control plane fails, the entire cluster is at risk. The API server down means no kubectl. The scheduler down means no new pods. The controller manager down means no reconciliation. These are the most critical and stressful incidents you'll face. Understanding how to diagnose and fix control plane issues quickly is essential.

> **The Air Traffic Control Analogy**
>
> The control plane is like air traffic control for your cluster. The API server is the radio tower - if it goes down, no communication. The scheduler is the flight planner - without it, new flights (pods) can't take off. The controller manager is the monitoring system - it ensures all planes follow their routes. When any of these fail, you need to act fast.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Diagnose API server failures
- Troubleshoot scheduler issues
- Fix controller manager problems
- Understand etcd health checks
- Work with static pods for control plane components

---

## Did You Know?

- **Control plane runs as pods**: In kubeadm clusters, control plane components run as static pods managed directly by kubelet
- **Static pod manifests location**: `/etc/kubernetes/manifests/` - edit these files to fix control plane issues
- **etcd is the brain**: Every piece of cluster state is stored in etcd - if it's corrupt or slow, everything suffers
- **API server is stateless**: The API server itself stores nothing - it just reads/writes to etcd. Restarting it loses no data

---

## Part 1: Control Plane Architecture Review

### 1.1 Component Dependencies

```
┌──────────────────────────────────────────────────────────────┐
│                 CONTROL PLANE DEPENDENCIES                    │
│                                                               │
│                      ┌─────────────┐                         │
│                      │    etcd     │                         │
│                      │  (storage)  │                         │
│                      └──────┬──────┘                         │
│                             │                                │
│                             ▼                                │
│                      ┌─────────────┐                         │
│                      │ API Server  │◄──── kubectl            │
│                      │  (gateway)  │◄──── kubelet            │
│                      └──────┬──────┘◄──── controllers        │
│                             │                                │
│              ┌──────────────┼──────────────┐                 │
│              │              │              │                 │
│              ▼              ▼              ▼                 │
│       ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│       │ Scheduler │  │ Controller│  │   Cloud   │           │
│       │           │  │  Manager  │  │ Controller│           │
│       └───────────┘  └───────────┘  └───────────┘           │
│                                                               │
│   If etcd fails     → Everything fails                       │
│   If API server     → Nothing can communicate                │
│   If scheduler      → New pods won't be scheduled            │
│   If controller-mgr → Resources won't reconcile              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Static Pods Overview

Control plane components are deployed as static pods:

```bash
# Static pod manifest location
/etc/kubernetes/manifests/
├── etcd.yaml
├── kube-apiserver.yaml
├── kube-controller-manager.yaml
└── kube-scheduler.yaml

# kubelet watches this directory
# Changes to these files = automatic restart of component
```

### 1.3 Checking Control Plane Health

```bash
# Quick health check (deprecated but useful)
k get componentstatuses

# Check control plane pods
k -n kube-system get pods | grep -E 'etcd|api|controller|scheduler'

# Verify all components are running
k -n kube-system get pods -o wide | grep -E 'kube-'
```

---

## Part 2: API Server Troubleshooting

### 2.1 API Server Failure Symptoms

```
┌──────────────────────────────────────────────────────────────┐
│                API SERVER FAILURE SYMPTOMS                    │
│                                                               │
│   Symptom                        Indicates                    │
│   ─────────────────────────────────────────────────────────  │
│   kubectl hangs/times out        API server unreachable       │
│   "connection refused"           API server not listening     │
│   "unable to connect to server"  Network/firewall issue       │
│   "Unauthorized"                 Auth/cert issue              │
│   "etcd cluster is unavailable"  API can't reach etcd         │
│   Very slow responses            Overloaded or etcd slow      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Diagnosing API Server Issues

**Step 1: Check if API server pod is running**
```bash
# From a control plane node
crictl ps | grep kube-apiserver

# Or check static pod status
ls -la /etc/kubernetes/manifests/kube-apiserver.yaml
```

**Step 2: Check API server logs**
```bash
# If running as pod
k -n kube-system logs kube-apiserver-<node>

# If pod is down, use crictl
crictl logs $(crictl ps -a | grep apiserver | awk '{print $1}')

# Or check kubelet logs for why it's not starting
journalctl -u kubelet | grep apiserver
```

**Step 3: Check certificates**
```bash
# Verify certificates
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep -A 2 "Validity"

# Check if certs are expired
kubeadm certs check-expiration
```

### 2.3 Common API Server Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Certificate expired | "x509: certificate has expired" | `kubeadm certs renew all` |
| etcd unreachable | "etcd cluster is unavailable" | Check etcd health, fix etcd |
| Wrong etcd endpoints | Startup failure | Check `--etcd-servers` in manifest |
| Port conflict | "bind: address already in use" | Find and kill conflicting process |
| Out of memory | OOMKilled, slow responses | Increase node resources |
| Incorrect flags | Won't start | Check manifest YAML syntax |

### 2.4 Fixing API Server Issues

**Certificate renewal**:
```bash
# Check certificate status
kubeadm certs check-expiration

# Renew all certificates
kubeadm certs renew all

# Restart control plane pods
# kubelet automatically restarts static pods when manifests change
```

**Manifest fixes**:
```bash
# Edit static pod manifest
sudo vim /etc/kubernetes/manifests/kube-apiserver.yaml

# Common fixes:
# - Fix typos in flags
# - Correct certificate paths
# - Fix etcd endpoints

# kubelet automatically detects changes and restarts the pod
```

---

## Part 3: Scheduler Troubleshooting

### 3.1 Scheduler Failure Symptoms

```
┌──────────────────────────────────────────────────────────────┐
│               SCHEDULER FAILURE SYMPTOMS                      │
│                                                               │
│   Symptom                           Check                     │
│   ─────────────────────────────────────────────────────────  │
│   All new pods stuck Pending        Scheduler not running     │
│   "no nodes available to schedule"  All nodes unschedulable   │
│   Pods not being distributed        Scheduler misconfigured   │
│   Very slow scheduling              Scheduler overloaded      │
│                                                               │
│   Remember: Existing pods keep running when scheduler fails!  │
│   Only NEW pods are affected.                                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Diagnosing Scheduler Issues

```bash
# Check scheduler pod status
k -n kube-system get pod -l component=kube-scheduler

# Check scheduler logs
k -n kube-system logs kube-scheduler-<node>

# Check for scheduling events
k get events -A --field-selector reason=FailedScheduling

# Describe pending pod for scheduling failure reason
k describe pod <pending-pod> | grep -A 10 Events
```

### 3.3 Common Scheduler Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Scheduler not running | All new pods Pending | Check static pod manifest |
| Can't connect to API | "connection refused" | Check kubeconfig, certs |
| Leader election failed | Scheduler not active | Check `--leader-elect` flag |
| No nodes available | Scheduling failures | Check node taints, resources |

### 3.4 Fixing Scheduler Issues

**Check and fix static pod**:
```bash
# Check manifest exists
cat /etc/kubernetes/manifests/kube-scheduler.yaml

# Check for YAML errors
cat /etc/kubernetes/manifests/kube-scheduler.yaml | python3 -c "import yaml,sys; yaml.safe_load(sys.stdin)"

# Common fixes in manifest:
# --kubeconfig=/etc/kubernetes/scheduler.conf
# --leader-elect=true

# Verify kubeconfig exists
ls -la /etc/kubernetes/scheduler.conf
```

**Manual scheduling (workaround)**:
```bash
# If scheduler is down, you can manually schedule pods
k patch pod <pod> -p '{"spec":{"nodeName":"worker-1"}}'
```

---

## Part 4: Controller Manager Troubleshooting

### 4.1 Controller Manager Failure Symptoms

```
┌──────────────────────────────────────────────────────────────┐
│            CONTROLLER MANAGER FAILURE SYMPTOMS                │
│                                                               │
│   Symptom                           Affected Controller       │
│   ─────────────────────────────────────────────────────────  │
│   Pods not created from Deployment  ReplicaSet controller     │
│   Deleted pods not replaced         ReplicaSet controller     │
│   PVCs stay Pending                 PV controller             │
│   Services have no endpoints        Endpoints controller      │
│   Nodes stay NotReady forever       Node controller           │
│   Jobs don't complete               Job controller            │
│   No automatic cleanup              GC controller             │
│                                                               │
│   The cluster "freezes" in current state - no reconciliation │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Diagnosing Controller Manager Issues

```bash
# Check controller manager pod
k -n kube-system get pod -l component=kube-controller-manager

# Check logs
k -n kube-system logs kube-controller-manager-<node>

# Check for specific controller issues
k -n kube-system logs kube-controller-manager-<node> | grep -i error

# Verify controllers are working
# Create a deployment and verify ReplicaSet is created
k create deployment test --image=nginx
k get rs | grep test
```

### 4.3 Common Controller Manager Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Not running | No reconciliation | Check static pod manifest |
| Service account missing | Can't create pods | Check service-account-private-key-file |
| Can't connect to API | All controllers fail | Check kubeconfig path |
| Cluster-signing-cert missing | CSR not approved | Check cert paths in manifest |

### 4.4 Fixing Controller Manager Issues

```bash
# Check manifest
cat /etc/kubernetes/manifests/kube-controller-manager.yaml

# Key flags to verify:
# --kubeconfig=/etc/kubernetes/controller-manager.conf
# --service-account-private-key-file=/etc/kubernetes/pki/sa.key
# --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
# --root-ca-file=/etc/kubernetes/pki/ca.crt

# Verify files exist
ls -la /etc/kubernetes/pki/
```

---

## Part 5: etcd Troubleshooting

### 5.1 etcd Failure Impact

```
┌──────────────────────────────────────────────────────────────┐
│                   ETCD FAILURE IMPACT                         │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │                    etcd DOWN                         │    │
│   └────────────────────────┬────────────────────────────┘    │
│                            │                                  │
│              ┌─────────────┼─────────────┐                   │
│              ▼             ▼             ▼                   │
│         No writes      No reads     API errors               │
│              │             │             │                   │
│              ▼             ▼             ▼                   │
│         Can't create   Can't list  "etcd cluster            │
│         resources      resources    is unavailable"          │
│                                                               │
│   Note: Existing pods keep running (kubelet is independent)  │
│   But no new changes can be made to the cluster              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Diagnosing etcd Issues

```bash
# Check etcd pod status
k -n kube-system get pod -l component=etcd

# Check etcd logs
k -n kube-system logs etcd-<node>

# Check etcd health with etcdctl
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health

# Check etcd member list
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list
```

### 5.3 Common etcd Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Data directory corrupt | Won't start | Restore from backup |
| Certificate expired | TLS errors | Renew certificates |
| Disk full | Write failures | Free disk space |
| Member not reachable | Cluster unhealthy | Check network, restart member |
| Clock skew | Raft failures | Sync NTP |

### 5.4 etcd Backup and Restore

**Backup** (for reference - exam may test this):
```bash
ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify backup
ETCDCTL_API=3 etcdctl snapshot status /tmp/etcd-backup.db
```

**Restore** (conceptual - complex in practice):
```bash
# Stop API server first
mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/

# Restore snapshot
ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd-restored

# Update etcd manifest to use new data dir
# Move API server manifest back
```

---

## Part 6: Static Pod Troubleshooting

### 6.1 How Static Pods Work

```
┌──────────────────────────────────────────────────────────────┐
│                    STATIC POD LIFECYCLE                       │
│                                                               │
│   /etc/kubernetes/manifests/           kubelet               │
│   ┌───────────────────────┐           ┌──────────────────┐  │
│   │ kube-apiserver.yaml   │◄─ watch ──│                  │  │
│   │ kube-scheduler.yaml   │           │  Creates pods    │  │
│   │ controller-manager... │──────────▶│  from manifests  │  │
│   │ etcd.yaml             │           │                  │  │
│   └───────────────────────┘           └──────────────────┘  │
│                                              │               │
│   File changed/created ─────────────────────▶│               │
│   File deleted ─────────────────────────────▶│               │
│                                              ▼               │
│                                     Pod created/deleted      │
│                                                               │
│   Naming: <name>-<node-name> (e.g., kube-apiserver-master)  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Common Static Pod Problems

```bash
# Check kubelet is configured to watch manifests dir
cat /var/lib/kubelet/config.yaml | grep staticPodPath

# Check manifest syntax
cat /etc/kubernetes/manifests/kube-apiserver.yaml | head -20

# Common issues:
# - YAML syntax errors (tabs instead of spaces)
# - Wrong file extension (must be .yaml or .yml)
# - Wrong file permissions (must be readable)
# - Missing required fields
```

### 6.3 Debugging Static Pods

```bash
# If static pod won't start, check kubelet logs
journalctl -u kubelet -f

# Look for errors about specific manifest
journalctl -u kubelet | grep -i "kube-apiserver\|error\|failed"

# Check if container exists but unhealthy
crictl ps -a | grep kube-

# Get container logs directly
crictl logs <container-id>
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Editing pods instead of manifests | Changes lost on restart | Edit `/etc/kubernetes/manifests/` files |
| Using kubectl when API is down | Commands fail | Use crictl for container management |
| Not checking kubelet logs | Miss root cause | Always check `journalctl -u kubelet` |
| Forgetting cert dependencies | Components can't communicate | Verify all cert paths exist |
| Not checking etcd first | Miss storage-level issues | etcd problems affect everything |
| Restarting before diagnosing | Lose evidence | Gather logs first, then restart |

---

## Quiz

### Q1: Static Pod Location
Where are control plane static pod manifests stored in a kubeadm cluster?

<details>
<summary>Answer</summary>

`/etc/kubernetes/manifests/`

This directory contains:
- kube-apiserver.yaml
- kube-scheduler.yaml
- kube-controller-manager.yaml
- etcd.yaml

kubelet watches this directory and automatically creates/updates/deletes pods when files change.

</details>

### Q2: API Server Down
kubectl is timing out. What's your first troubleshooting step on the control plane node?

<details>
<summary>Answer</summary>

Check if the API server container is running:
```bash
crictl ps | grep kube-apiserver
```

If not running, check why:
```bash
crictl ps -a | grep kube-apiserver  # See if it exists but stopped
journalctl -u kubelet | grep apiserver  # Check kubelet logs
```

</details>

### Q3: Scheduler vs Controller Manager
Pods are stuck Pending but Deployments show the correct replica count. Which component is likely failing?

<details>
<summary>Answer</summary>

The **scheduler** is likely failing.

- Controller manager creates ReplicaSets and ensures replica counts (working - that's why deployment shows correct count)
- Scheduler assigns pods to nodes (failing - pods stuck Pending)

Check: `k -n kube-system logs kube-scheduler-<node>`

</details>

### Q4: etcd Health Check
Write the command to check etcd cluster health.

<details>
<summary>Answer</summary>

```bash
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

Or if environment variables are set:
```bash
etcdctl endpoint health
```

</details>

### Q5: Certificate Expiry
How do you check if Kubernetes certificates are expired?

<details>
<summary>Answer</summary>

```bash
kubeadm certs check-expiration
```

This shows expiry dates for all cluster certificates. To renew:
```bash
kubeadm certs renew all
```

</details>

### Q6: Controller Manager Symptoms
The controller manager is down. Which of these would you observe?
a) kubectl commands fail
b) Existing pods stop running
c) New pods from deployments aren't created
d) Services lose their endpoints

<details>
<summary>Answer</summary>

**c) and d)** are correct:
- New pods from deployments aren't created (ReplicaSet controller)
- Services lose their endpoints (Endpoints controller)

a) is wrong - API server handles kubectl
b) is wrong - kubelet keeps pods running independently

The controller manager handles reconciliation loops. When it's down, the cluster "freezes" - existing state remains but no changes are reconciled.

</details>

---

## Hands-On Exercise: Control Plane Troubleshooting

### Scenario

Practice diagnosing control plane issues in a controlled way.

### Prerequisites

This exercise requires a kubeadm-based cluster with SSH access to control plane nodes.

### Setup

```bash
# Verify you have control plane access
ssh <control-plane-node>
sudo ls /etc/kubernetes/manifests/
```

### Task 1: Explore Control Plane Components

```bash
# List all static pod manifests
ls -la /etc/kubernetes/manifests/

# Check current control plane pod status
k -n kube-system get pods | grep -E 'etcd|api|scheduler|controller'

# View API server configuration
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -A 5 "command:"
```

### Task 2: Check etcd Health

```bash
# Use etcdctl to check health
# First, set up an alias for convenience
alias etcdctl='ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key'

# Check health
etcdctl endpoint health

# Check member list
etcdctl member list

# Check cluster status
etcdctl endpoint status --write-out=table
```

### Task 3: Simulate Scheduler Failure (Careful!)

```bash
# First, note a pending pod's behavior
k run test-scheduler --image=nginx
k get pods test-scheduler

# Temporarily rename scheduler manifest (this stops it)
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /tmp/

# Wait 30 seconds, try to create another pod
sleep 30
k run test-scheduler-2 --image=nginx

# Check status - should be Pending
k get pods test-scheduler-2
k describe pod test-scheduler-2 | grep -A 5 Events

# Restore scheduler
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/

# Wait for scheduler to restart
sleep 30
k get pods -w
```

### Task 4: Check Certificate Expiration

```bash
# Use kubeadm to check all certificates
sudo kubeadm certs check-expiration

# Manually check a specific certificate
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep -A 2 Validity
```

### Success Criteria

- [ ] Listed all static pod manifests
- [ ] Verified etcd health with etcdctl
- [ ] Understood scheduler failure symptoms
- [ ] Checked certificate expiration dates

### Cleanup

```bash
k delete pod test-scheduler test-scheduler-2
```

---

## Practice Drills

### Drill 1: Control Plane Pod Status (30 sec)
```bash
# Task: Show all control plane pods status
k -n kube-system get pods | grep -E 'etcd|api|scheduler|controller'
```

### Drill 2: Check Component Logs (1 min)
```bash
# Task: View last 50 lines of API server logs
k -n kube-system logs kube-apiserver-<node> --tail=50
```

### Drill 3: Static Pod Manifest Check (30 sec)
```bash
# Task: View scheduler configuration
cat /etc/kubernetes/manifests/kube-scheduler.yaml
```

### Drill 4: etcd Health (1 min)
```bash
# Task: Check etcd endpoint health
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

### Drill 5: Certificate Check (30 sec)
```bash
# Task: Check all certificate expiration dates
kubeadm certs check-expiration
```

### Drill 6: kubelet Logs for Control Plane (1 min)
```bash
# Task: Check kubelet logs for control plane errors
journalctl -u kubelet --since "10 minutes ago" | grep -i "error\|failed"
```

### Drill 7: Container Status with crictl (30 sec)
```bash
# Task: List all control plane containers
crictl ps | grep kube
```

### Drill 8: API Server Connectivity Test (30 sec)
```bash
# Task: Test API server endpoint
curl -k https://localhost:6443/healthz
```

---

## Next Module

Continue to [Module 5.4: Worker Node Failures](../module-5.4-worker-nodes/) to learn how to troubleshoot kubelet, container runtime, and node-level issues.
