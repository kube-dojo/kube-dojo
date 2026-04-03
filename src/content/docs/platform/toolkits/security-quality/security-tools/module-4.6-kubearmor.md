---
title: "Module 4.6: KubeArmor - Runtime Security with Least Privilege"
slug: platform/toolkits/security-quality/security-tools/module-4.6-kubearmor
sidebar:
  order: 7
---
## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 4.3 (Falco), Module 4.5 (Tetragon basics), Understanding of Linux security (AppArmor/SELinux)
**Learning Objectives**:
- Understand runtime security enforcement with KubeArmor
- Deploy KubeArmor for workload protection
- Create KubeArmorPolicy for allow-listing and blocking
- Implement least-privilege security at the container level

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy KubeArmor for container-aware runtime security with LSM-based policy enforcement**
- **Configure KubeArmor security policies for process, file, and network access control per workload**
- **Implement KubeArmor's visibility mode to discover application behavior before enforcing restrictions**
- **Compare KubeArmor's LSM approach against Tetragon's eBPF enforcement for different kernel requirements**


## Why This Module Matters

Container security defaults are permissive. A container can typically execute any binary, access any file it has permissions for, and make any network connection. This is the "default allow" model—everything is permitted unless explicitly blocked.

**KubeArmor flips this to "default deny" for containers.**

Instead of listing what to block (and missing something), you define what's allowed. Everything else is automatically denied. This is **least privilege enforcement**—containers can only do what they need, nothing more.

> "Stop playing whack-a-mole with threats. Define what's legitimate, block everything else."

---

## Did You Know?

- KubeArmor supports **three enforcement backends**: AppArmor, BPF-LSM, and SELinux—choosing the best available on each node
- KubeArmor can auto-generate policies by **observing your application's behavior** in learning mode
- You can get **immediate visibility** into what your containers are actually doing before enforcing anything
- KubeArmor is CNCF Sandbox project with roots in AccuKnox's enterprise security platform
- The same policies work across **VMs, containers, and bare metal** with the KubeArmor host protection agent
- KubeArmor integrates with Kubernetes admission control to **prevent insecure workloads from starting**

---

## The Security Model Problem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Traditional "Block List" Model                       │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                     Everything Allowed                           │  │
│   │   ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐       │  │
│   │   │ bash  │  │ curl  │  │ wget  │  │ python│  │  ???  │       │  │
│   │   │  ✓    │  │  ✓    │  │  ✓    │  │  ✓    │  │  ✓    │       │  │
│   │   └───────┘  └───────┘  └───────┘  └───────┘  └───────┘       │  │
│   │                                                                  │  │
│   │   Block: xmrig, nc, ncat, ...                                   │  │
│   │   (always one step behind attackers)                            │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   Problem: What about the tools you haven't heard of yet?              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    KubeArmor "Allow List" Model                         │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                     Everything Blocked                           │  │
│   │   ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐       │  │
│   │   │ bash  │  │ curl  │  │ wget  │  │ python│  │  ???  │       │  │
│   │   │  ✗    │  │  ✗    │  │  ✗    │  │  ✗    │  │  ✗    │       │  │
│   │   └───────┘  └───────┘  └───────┘  └───────┘  └───────┘       │  │
│   │                                                                  │  │
│   │   Allow: /app/server, /usr/bin/node, /lib/*.so                  │  │
│   │   (only what's needed)                                          │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   Solution: Unknown tools are blocked by default.                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## KubeArmor Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                              │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    KubeArmor Components                            │ │
│  │                                                                    │ │
│  │  ┌────────────────┐  ┌─────────────────────────────────────────┐ │ │
│  │  │ KubeArmor      │  │  KubeArmorPolicy CRDs                   │ │ │
│  │  │ Operator       │  │  - Workload policies                    │ │ │
│  │  └────────────────┘  │  - Host policies                        │ │ │
│  │                      │  - Cluster policies                      │ │ │
│  │                      └─────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐              │
│  │    Node 1     │  │    Node 2     │  │    Node 3     │              │
│  │  ┌─────────┐  │  │  ┌─────────┐  │  │  ┌─────────┐  │              │
│  │  │KubeArmor│  │  │  │KubeArmor│  │  │  │KubeArmor│  │              │
│  │  │ Agent   │  │  │  │ Agent   │  │  │  │ Agent   │  │              │
│  │  │(DaemonSet│  │  │  │(DaemonSet│  │  │  │(DaemonSet│  │              │
│  │  └────┬────┘  │  │  └────┬────┘  │  │  └────┬────┘  │              │
│  │       │       │  │       │       │  │       │       │              │
│  │  ┌────┴────┐  │  │  ┌────┴────┐  │  │  ┌────┴────┐  │              │
│  │  │Enforcer │  │  │  │Enforcer │  │  │  │Enforcer │  │              │
│  │  │(AppArmor│  │  │  │(BPF-LSM)│  │  │  │(SELinux)│  │              │
│  │  │   or    │  │  │  │         │  │  │  │         │  │              │
│  │  │BPF-LSM) │  │  │  │         │  │  │  │         │  │              │
│  │  └─────────┘  │  │  └─────────┘  │  │  └─────────┘  │              │
│  └───────────────┘  └───────────────┘  └───────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Role | Description |
|-----------|------|-------------|
| **KubeArmor Agent** | Policy enforcement | DaemonSet on each node, enforces policies |
| **KubeArmor Relay** | Log aggregation | Collects alerts from all agents |
| **kArmor CLI** | Management | CLI tool for policy management |
| **KubeArmorPolicy** | Workload policy | Pod-level security rules |
| **KubeArmorHostPolicy** | Host policy | Node-level security rules |
| **KubeArmorClusterPolicy** | Cluster policy | Cluster-wide security rules |

### Enforcement Backends

| Backend | Kernel Version | Distribution Support |
|---------|----------------|---------------------|
| **AppArmor** | 2.6+ | Ubuntu, Debian, SUSE |
| **BPF-LSM** | 5.7+ | Any with BTF support |
| **SELinux** | 2.6+ | RHEL, CentOS, Fedora |

KubeArmor automatically detects and uses the best available enforcer.

---

## Installing KubeArmor

### Option 1: Helm (Recommended)

```bash
# Add KubeArmor Helm repo
helm repo add kubearmor https://kubearmor.github.io/charts
helm repo update

# Install KubeArmor
helm install kubearmor kubearmor/kubearmor -n kubearmor --create-namespace

# Verify installation
kubectl get pods -n kubearmor
```

### Option 2: kArmor CLI

```bash
# Install kArmor CLI
curl -sfL http://get.kubearmor.io/ | sudo sh -s -- -b /usr/local/bin

# Install KubeArmor using CLI
karmor install

# Check status
karmor probe
```

### Option 3: Manifest Apply

```bash
kubectl apply -f https://raw.githubusercontent.com/kubearmor/KubeArmor/main/deployments/get/kubearmor.yaml
```

### Verify Installation

```bash
# Check KubeArmor pods
kubectl get pods -n kubearmor

# Check if enforcement is working
karmor probe

# Expected output:
# Found node with mass_security: apparmor
# KubeArmor is running
# Active enforcers: [AppArmor]
```

---

## KubeArmorPolicy: The Core Concept

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: example-policy
  namespace: default
spec:
  selector:
    matchLabels:
      app: myapp           # Which pods this applies to

  process:
    matchPaths:
      - path: /bin/bash
        action: Block      # Block bash execution

  file:
    matchDirectories:
      - dir: /etc/
        readOnly: true     # /etc is read-only

  network:
    matchProtocols:
      - protocol: raw
        action: Block      # Block raw sockets
```

### Policy Structure

```
KubeArmorPolicy
├── selector           # Which pods to target
│   └── matchLabels
│
├── process            # Process execution rules
│   ├── matchPaths[]   # Specific binaries
│   ├── matchPatterns[]    # Pattern matching
│   └── matchDirectories[] # Directory-based
│
├── file               # File access rules
│   ├── matchPaths[]
│   ├── matchPatterns[]
│   └── matchDirectories[]
│
├── network            # Network access rules
│   └── matchProtocols[]
│
├── capabilities       # Linux capability rules
│   └── matchCapabilities[]
│
└── action             # Default: Audit | Block | Allow
```

### Actions Explained

| Action | Effect | Use Case |
|--------|--------|----------|
| `Allow` | Explicitly permit (in default-deny mode) | Whitelist specific operations |
| `Block` | Deny and log the attempt | Block known-bad operations |
| `Audit` | Allow but log | Learning mode, observation |

---

## Practical Security Policies

### 1. Minimal Node.js Application

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: nodejs-minimal
  namespace: production
spec:
  selector:
    matchLabels:
      app: nodejs-api

  # Only allow node and necessary system binaries
  process:
    matchPaths:
      - path: /usr/local/bin/node
        action: Allow
      - path: /usr/bin/node
        action: Allow
    matchDirectories:
      - dir: /
        recursive: true
        action: Block    # Block all other executables

  # Only allow reading app files and node_modules
  file:
    matchDirectories:
      - dir: /app/
        recursive: true
        readOnly: true
        action: Allow
      - dir: /usr/local/lib/node_modules/
        recursive: true
        readOnly: true
        action: Allow
      - dir: /tmp/
        action: Allow    # Allow tmp for scratch space
    matchPaths:
      - path: /etc/passwd
        readOnly: true
        action: Allow    # Node needs this for user lookup
      - path: /etc/hosts
        readOnly: true
        action: Allow

  # Only allow TCP connections
  network:
    matchProtocols:
      - protocol: tcp
        action: Allow
      - protocol: udp
        action: Allow    # DNS
      - protocol: raw
        action: Block    # No raw sockets
```

### 2. Database Container Protection

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: postgres-hardened
  namespace: database
spec:
  selector:
    matchLabels:
      app: postgres

  process:
    matchPaths:
      - path: /usr/lib/postgresql/*/bin/postgres
        action: Allow
      - path: /usr/lib/postgresql/*/bin/pg_ctl
        action: Allow
      - path: /usr/lib/postgresql/*/bin/initdb
        action: Allow
    matchDirectories:
      - dir: /
        recursive: true
        action: Block    # Only postgres binaries allowed

  file:
    matchDirectories:
      - dir: /var/lib/postgresql/
        recursive: true
        action: Allow    # Data directory
      - dir: /var/run/postgresql/
        action: Allow    # Socket directory
      - dir: /etc/postgresql/
        recursive: true
        readOnly: true
        action: Allow    # Config (read-only)

  capabilities:
    matchCapabilities:
      - capability: net_bind_service
        action: Block    # Don't allow binding to privileged ports
```

### 3. Block Shell Access in All Containers

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorClusterPolicy
metadata:
  name: block-shells-cluster-wide
spec:
  selector:
    matchExpressions:
      - key: app
        operator: Exists   # Applies to all pods with an 'app' label

  process:
    matchPaths:
      - path: /bin/bash
        action: Block
      - path: /bin/sh
        action: Block
      - path: /bin/dash
        action: Block
      - path: /bin/zsh
        action: Block
      - path: /usr/bin/bash
        action: Block
      - path: /usr/bin/sh
        action: Block
    matchPatterns:
      - pattern: "**/python*"
        action: Block
      - pattern: "**/perl*"
        action: Block
      - pattern: "**/ruby*"
        action: Block
```

### 4. Protect Kubernetes Service Account Tokens

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorClusterPolicy
metadata:
  name: protect-service-account-tokens
spec:
  selector:
    matchExpressions:
      - key: app
        operator: Exists

  file:
    matchDirectories:
      - dir: /var/run/secrets/kubernetes.io/serviceaccount/
        recursive: true
        action: Block    # Block all access to SA tokens
```

### 5. Network Segmentation

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: frontend-network-policy
  namespace: production
spec:
  selector:
    matchLabels:
      tier: frontend

  network:
    matchProtocols:
      - protocol: tcp
        action: Allow
      - protocol: udp
        action: Allow    # DNS lookups
      - protocol: icmp
        action: Block    # No ping
      - protocol: raw
        action: Block    # No raw sockets

  # Note: KubeArmor network policies complement NetworkPolicies
  # They enforce at the container level, not pod level
```

---

## Learning Mode: Auto-Generate Policies

KubeArmor can observe your application and suggest policies:

```bash
# Start observing a deployment
karmor discover --namespace production --deployment api-server --output api-policy.yaml

# This watches the application and generates a policy based on:
# - What processes are executed
# - What files are accessed
# - What network connections are made

# Review and apply the generated policy
cat api-policy.yaml
kubectl apply -f api-policy.yaml
```

### How Discovery Works

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Policy Discovery Flow                               │
│                                                                        │
│  ┌──────────────────┐                                                 │
│  │  1. Start        │                                                 │
│  │  Discovery       │                                                 │
│  └────────┬─────────┘                                                 │
│           │                                                            │
│           ▼                                                            │
│  ┌──────────────────┐      ┌──────────────────────────────────────┐  │
│  │  2. KubeArmor    │      │  Application runs normally:          │  │
│  │  observes all    │◀────│  - Executes /usr/bin/node             │  │
│  │  activity        │      │  - Reads /app/config.json             │  │
│  └────────┬─────────┘      │  - Connects to postgres:5432          │  │
│           │                │  - Writes to /tmp/cache               │  │
│           │                └──────────────────────────────────────┘  │
│           ▼                                                            │
│  ┌──────────────────┐                                                 │
│  │  3. Generate     │                                                 │
│  │  allowlist       │                                                 │
│  │  policy          │                                                 │
│  └────────┬─────────┘                                                 │
│           │                                                            │
│           ▼                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  4. Output: KubeArmorPolicy YAML                                 │ │
│  │                                                                   │ │
│  │  process:                                                         │ │
│  │    matchPaths:                                                    │ │
│  │      - path: /usr/bin/node                                        │ │
│  │        action: Allow                                              │ │
│  │  file:                                                            │ │
│  │    matchDirectories:                                              │ │
│  │      - dir: /app/                                                 │ │
│  │        action: Allow                                              │ │
│  │  ...                                                              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Monitoring and Visibility

### View Security Events

```bash
# Stream all KubeArmor logs
karmor logs

# Filter by namespace
karmor logs --namespace production

# JSON output for processing
karmor logs --json | jq '.Result'

# Filter by operation type
karmor logs --logFilter=policy  # Only policy violations
```

### Event Types

| Event Type | Description |
|------------|-------------|
| `MatchedPolicy` | Action taken due to a policy match |
| `MatchedHostPolicy` | Host-level policy triggered |
| `Alert` | Security alert generated |
| `Log` | General activity log |

### Export to SIEM

```yaml
# Configure KubeArmor to export logs
# In Helm values:
kubearmor:
  relay:
    exporters:
      - type: elasticsearch
        url: http://elasticsearch:9200
        index: kubearmor-logs
      - type: kafka
        brokers: kafka:9092
        topic: kubearmor-alerts
```

---

## KubeArmor vs Tetragon vs Falco

| Feature | KubeArmor | Tetragon | Falco |
|---------|-----------|----------|-------|
| **Primary Model** | Allow-listing | Block-listing | Detection |
| **Enforcement** | Yes (LSM) | Yes (eBPF) | No (alert only) |
| **Policy Discovery** | Yes (built-in) | No | Limited |
| **Kubernetes Native** | CRDs | CRDs | Helm + YAML |
| **Backend** | AppArmor/BPF-LSM/SELinux | eBPF only | Kernel module/eBPF |
| **Host Protection** | Yes | Yes | Yes |
| **File Integrity** | Yes | Limited | Yes |
| **Learning Mode** | Yes | No | No |

### When to Choose KubeArmor

**KubeArmor is ideal when:**
- You want **default-deny** security (allow-listing)
- You need **automatic policy discovery**
- Your nodes use AppArmor or SELinux
- You want **least-privilege enforcement** without writing complex rules
- You're securing containers without modifying them

**Tetragon is better when:**
- You need **immediate kernel-level blocking**
- You're already using Cilium
- You want to block specific attack patterns

**Falco is better when:**
- You need **rich behavioral detection**
- You're building a detection & response pipeline
- You want community-maintained rule sets

---

## War Story: The Compromised Image

An e-commerce company discovered that one of their third-party container images had been compromised. The image maintainer's credentials were stolen, and a cryptominer was injected into the image.

**The Attack Path**:
1. Malicious image pushed to public registry
2. CI/CD pulls "latest" tag (the compromised version)
3. Container starts, miner runs alongside legitimate app
4. 3 weeks before detection (unusual CPU usage noticed)

**The Problem**:
- Vulnerability scanning didn't help (miner wasn't a known CVE)
- Runtime detection (Falco) would have alerted, but miner had already run
- No way to know what "normal" looked like

**The KubeArmor Solution**:

First, they used discovery mode to understand legitimate behavior:

```bash
# Observe the known-good version
karmor discover --namespace production --deployment checkout-service --output checkout-policy.yaml
```

Then they reviewed and applied the generated policy:

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: checkout-service-lockdown
  namespace: production
spec:
  selector:
    matchLabels:
      app: checkout-service

  process:
    matchPaths:
      - path: /usr/local/bin/node
        action: Allow
    matchDirectories:
      - dir: /
        recursive: true
        action: Block

  file:
    matchDirectories:
      - dir: /app/
        recursive: true
        action: Allow
      - dir: /tmp/
        action: Allow
    # Default: block all other file access

  network:
    matchProtocols:
      - protocol: tcp
        action: Allow
      - protocol: udp
        action: Allow
```

**The Results**:

When the compromised image was deployed:
```bash
# KubeArmor logs showed:
# [BLOCKED] Process: /usr/bin/xmrig
# [BLOCKED] File write: /var/tmp/.cache/miner.conf
# [BLOCKED] Network: tcp connect to mining-pool.com:3333
```

The miner couldn't:
- Execute (not in process allow-list)
- Write config files (outside allowed directories)
- Connect to the mining pool (no exception for that destination)

**The container ran normally** because the legitimate Node.js app was in the allow-list. The attack was **completely neutralized**.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Too restrictive initial policy | Break legitimate functionality | Start in Audit mode, then Block |
| Not using discovery mode | Manual policies miss edge cases | Run discovery in staging first |
| Applying Block globally too soon | Production outage | Test thoroughly before enforcement |
| Forgetting system libraries | App won't start | Include `/lib/`, `/usr/lib/` as needed |
| Not allowing /tmp | Many apps need temp files | Include `/tmp/` in file allow-list |
| Blocking DNS UDP | Network failures | Always allow UDP for DNS |

---

## Hands-On Exercise: Secure a Web Application

**Objective**: Use KubeArmor to create a least-privilege policy for a web application.

### Setup

```bash
# Create test namespace
kubectl create namespace kubearmor-demo

# Deploy a simple web application
kubectl apply -n kubearmor-demo -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  selector:
    app: web-app
  ports:
  - port: 80
EOF

# Wait for deployment
kubectl wait --for=condition=available deployment/web-app -n kubearmor-demo --timeout=60s
```

### Task 1: Observe Without Policies

```bash
# Start monitoring KubeArmor logs for this namespace
karmor logs --namespace kubearmor-demo

# In another terminal, generate some activity
kubectl exec -n kubearmor-demo deploy/web-app -- ls /
kubectl exec -n kubearmor-demo deploy/web-app -- cat /etc/nginx/nginx.conf
kubectl exec -n kubearmor-demo deploy/web-app -- wget -q -O- http://example.com
```

### Task 2: Apply an Audit Policy

```bash
# Apply a policy in Audit mode first
kubectl apply -f - <<EOF
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: web-app-audit
  namespace: kubearmor-demo
spec:
  selector:
    matchLabels:
      app: web-app

  process:
    matchPaths:
      - path: /bin/sh
        action: Audit
      - path: /bin/bash
        action: Audit
      - path: /usr/bin/wget
        action: Audit

  file:
    matchDirectories:
      - dir: /etc/
        recursive: true
        action: Audit
EOF

# Try the same commands and watch the logs
kubectl exec -n kubearmor-demo deploy/web-app -- cat /etc/passwd
# Should see audit log entries
```

### Task 3: Apply Enforcement Policy

```bash
# Now apply a blocking policy
kubectl apply -f - <<EOF
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: web-app-hardened
  namespace: kubearmor-demo
spec:
  selector:
    matchLabels:
      app: web-app

  process:
    matchPaths:
      - path: /usr/sbin/nginx
        action: Allow
    matchDirectories:
      - dir: /
        recursive: true
        action: Block

  file:
    matchDirectories:
      - dir: /etc/nginx/
        recursive: true
        readOnly: true
        action: Allow
      - dir: /var/log/nginx/
        action: Allow
      - dir: /var/cache/nginx/
        action: Allow
      - dir: /usr/share/nginx/html/
        readOnly: true
        action: Allow
    matchPaths:
      - path: /etc/passwd
        readOnly: true
        action: Allow
      - path: /etc/group
        readOnly: true
        action: Allow
EOF
```

### Task 4: Test the Hardened Container

```bash
# Nginx should still work
kubectl exec -n kubearmor-demo deploy/web-app -- curl -s localhost

# Shell should be blocked
kubectl exec -n kubearmor-demo deploy/web-app -- sh -c "echo test"
# Should fail or be killed

# wget should be blocked
kubectl exec -n kubearmor-demo deploy/web-app -- wget -q http://example.com
# Should fail

# Reading sensitive files outside allow-list should fail
kubectl exec -n kubearmor-demo deploy/web-app -- cat /etc/shadow
# Should fail
```

### Task 5: Check the Logs

```bash
# See all blocked attempts
karmor logs --namespace kubearmor-demo --logFilter=policy

# You should see entries like:
# MatchedPolicy - Block - Process /bin/sh
# MatchedPolicy - Block - File /etc/shadow
```

### Success Criteria

- [ ] Observed normal activity in Audit mode
- [ ] Applied the hardened policy
- [ ] Verified nginx still serves requests
- [ ] Verified shell access is blocked
- [ ] Verified wget/curl are blocked
- [ ] Saw blocked attempts in KubeArmor logs

### Cleanup

```bash
kubectl delete namespace kubearmor-demo
```

---

## Quiz

### Question 1
What is the fundamental security model difference between KubeArmor and traditional block-lists?

<details>
<summary>Show Answer</summary>

**KubeArmor uses allow-listing (default-deny) instead of block-listing (default-allow)**

With allow-listing, you explicitly define what is permitted, and everything else is automatically blocked. This is more secure because new/unknown attacks are blocked by default, rather than requiring you to know about them in advance.
</details>

### Question 2
What enforcement backends does KubeArmor support?

<details>
<summary>Show Answer</summary>

**AppArmor, BPF-LSM, and SELinux**

KubeArmor automatically detects and uses the best available enforcer on each node. AppArmor is common on Ubuntu/Debian, SELinux on RHEL/CentOS, and BPF-LSM works on newer kernels (5.7+) regardless of distribution.
</details>

### Question 3
What is the purpose of KubeArmor's discovery mode?

<details>
<summary>Show Answer</summary>

**To automatically generate security policies by observing application behavior**

Discovery mode watches what processes execute, files are accessed, and network connections are made. It then generates a KubeArmorPolicy that allows only those observed behaviors, providing a starting point for least-privilege enforcement.
</details>

### Question 4
What is the difference between KubeArmorPolicy and KubeArmorClusterPolicy?

<details>
<summary>Show Answer</summary>

**KubeArmorPolicy is namespaced; KubeArmorClusterPolicy applies cluster-wide**

KubeArmorPolicy only affects pods in its namespace. KubeArmorClusterPolicy can target pods across all namespaces, useful for enforcing security baselines like "block shell access everywhere."
</details>

### Question 5
How does KubeArmor differ from Kubernetes NetworkPolicies?

<details>
<summary>Show Answer</summary>

**KubeArmor enforces at the container/process level; NetworkPolicies enforce at the pod network level**

KubeArmor can block specific binaries from making network connections, control file access, and manage process execution. NetworkPolicies only control pod-to-pod network traffic.
</details>

### Question 6
What action should you use when first deploying KubeArmor policies?

<details>
<summary>Show Answer</summary>

**`action: Audit`**

Audit mode allows the operation but logs it. This lets you verify the policy works correctly without breaking the application. Once you're confident, switch to `Block`.
</details>

### Question 7
Why should you include /tmp in most allow-lists?

<details>
<summary>Show Answer</summary>

**Many applications need to write temporary files**

Applications often use /tmp for scratch space, caching, or temporary data. Blocking /tmp can cause unexpected application failures.
</details>

### Question 8
How do you view KubeArmor security events?

<details>
<summary>Show Answer</summary>

**`karmor logs` command or by checking the KubeArmor relay logs**

`karmor logs` streams security events in real-time. You can filter by namespace with `--namespace` or by event type with `--logFilter=policy`.
</details>

---

## Key Takeaways

1. **Allow-listing beats block-listing** - define what's permitted, block everything else
2. **Discovery mode generates policies** - observe first, enforce later
3. **Multiple enforcement backends** - AppArmor, BPF-LSM, SELinux
4. **Start in Audit mode** - verify before blocking
5. **Kubernetes-native CRDs** - policies are just YAML
6. **Process + File + Network** - comprehensive control
7. **Complements other tools** - use alongside Falco and Tetragon
8. **No application changes** - security without code modification
9. **Visibility is built-in** - logs show all blocked attempts
10. **Least privilege enforced** - containers only do what they need

---

## Further Reading

- [KubeArmor Documentation](https://docs.kubearmor.io/) - Official guides
- [KubeArmorPolicy Reference](https://docs.kubearmor.io/kubearmor/specification/policy-specification) - Complete spec
- [KubeArmor GitHub](https://github.com/kubearmor/KubeArmor) - Source and examples
- [CNCF KubeArmor](https://www.cncf.io/projects/kubearmor/) - Project overview

---

## Next Module

You've completed the security tools toolkit! Continue to [Platform Engineering Disciplines](../../../disciplines/) to learn how to apply these tools in practice.
