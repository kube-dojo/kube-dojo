---
title: "Module 8.2: Telepresence & Tilt"
slug: platform/toolkits/developer-experience/devex-tools/module-8.2-telepresence-tilt
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

"It works on my machine" meets Kubernetes. How do you develop locally against a remote cluster? How do you get fast feedback loops when containers take minutes to build? Telepresence connects your local machine to a remote cluster, and Tilt automates the build-deploy-test cycle. Together, they make cloud-native development feel local.

**What You'll Learn**:
- Telepresence for local-to-remote development
- Tilt for automated development workflows
- Inner loop optimization strategies
- When to use each tool

**Prerequisites**:
- Local Kubernetes basics (Docker Desktop, minikube)
- Container build process understanding
- [Module 8.1: k9s & CLI Tools](../module-8.1-k9s-cli/)

---

## Why This Module Matters

The traditional Kubernetes development loop is: edit code → build container → push to registry → deploy to cluster → test → repeat. This takes 5-10 minutes per iteration. With Telepresence and Tilt, it takes seconds. Faster feedback means faster development, fewer bugs, and happier developers.

> 💡 **Did You Know?** Telepresence was created by Ambassador Labs (formerly Datawire) and is now a CNCF sandbox project. The name comes from "telepresence robots"—robots that let you be present somewhere remotely. Telepresence lets your local code be "present" in a remote Kubernetes cluster.

---

## The Development Loop Problem

```
TRADITIONAL K8S DEVELOPMENT LOOP
════════════════════════════════════════════════════════════════════

Edit Code
    │
    ▼ (1 min)
Build Container
    │
    ▼ (2 min)
Push to Registry
    │
    ▼ (1 min)
Deploy to Cluster
    │
    ▼ (1 min)
Pod Starts
    │
    ▼ (5+ min total)
Test Change

Problem: 5-10 minute cycles = ~6-12 iterations per hour
Developer: Loses context, checks Twitter, gets coffee

═══════════════════════════════════════════════════════════════════

WITH TELEPRESENCE / TILT
════════════════════════════════════════════════════════════════════

Edit Code
    │
    ▼ (seconds)
Test Against Real Cluster

Developer: Stays in flow, ships faster
```

---

## Telepresence

### How It Works

```
TELEPRESENCE ARCHITECTURE
════════════════════════════════════════════════════════════════════

BEFORE TELEPRESENCE:
─────────────────────────────────────────────────────────────────
Local Machine              Kubernetes Cluster

┌──────────────┐          ┌──────────────────────────────┐
│  Your Code   │          │  api-pod                     │
│  (can't talk │          │  ┌────────────────────────┐ │
│   to cluster)│          │  │ api container          │ │
│              │    ✗     │  │ (deployed version)     │ │
│              │◀────────▶│  └────────────────────────┘ │
└──────────────┘          │                              │
                          │  database-pod                │
                          │  ┌────────────────────────┐ │
                          │  │ postgres container     │ │
                          │  └────────────────────────┘ │
                          └──────────────────────────────┘

═══════════════════════════════════════════════════════════════════

WITH TELEPRESENCE INTERCEPT:
─────────────────────────────────────────────────────────────────
Local Machine              Kubernetes Cluster

┌──────────────┐          ┌──────────────────────────────┐
│  Your Code   │◀────────▶│  Traffic Manager             │
│  (running    │  tunnel  │  ┌────────────────────────┐ │
│   locally)   │          │  │ Intercepts traffic to  │ │
│              │          │  │ api-pod, sends to local│ │
│              │          │  └────────────────────────┘ │
│              │                                        │
│  • Uses real │          │  database-pod                │
│    database  │          │  ┌────────────────────────┐ │
│  • Real DNS  │          │  │ postgres container     │ │
│  • Real envs │          │  └────────────────────────┘ │
└──────────────┘          └──────────────────────────────┘

Your local code receives real cluster traffic!
```

### Installation

```bash
# macOS
brew install datawire/blackbird/telepresence

# Linux
curl -fL https://app.getambassador.io/download/tel2/linux/amd64/latest/telepresence -o telepresence
chmod +x telepresence
sudo mv telepresence /usr/local/bin/

# Verify
telepresence version
```

### Basic Commands

```bash
# Connect to cluster (creates tunnel)
telepresence connect

# Check status
telepresence status

# List available services
telepresence list

# Intercept traffic to a deployment
telepresence intercept api --port 8080

# Run local service on intercepted port
telepresence intercept api --port 8080 -- python app.py

# Disconnect
telepresence quit
```

### Intercept Modes

```bash
# Global intercept (all traffic)
telepresence intercept api --port 8080

# Personal intercept (header-based)
telepresence intercept api --port 8080 --http-header x-telepresence-id=$(whoami)
# Only traffic with matching header comes to you
# Others see normal cluster service
```

### Environment and Volumes

```bash
# Get environment variables from pod
telepresence intercept api --env-file api.env

# Mount pod volumes locally
telepresence intercept api --mount /tmp/api-mount

# Use in your local run
source api.env && python app.py
```

> 💡 **Did You Know?** Telepresence's personal intercepts let multiple developers work on the same service simultaneously. Each developer's requests (identified by header) go to their local machine, while everyone else's traffic goes to the cluster version. No more "who's using staging?"

---

## Tilt

### How It Works

```
TILT WORKFLOW
════════════════════════════════════════════════════════════════════

1. You edit code
        │
        ▼
2. Tilt detects change (file watch)
        │
        ▼
3. Tilt decides what to do:
   • live_update: Sync files to running container
   • docker_build: Rebuild container (smart caching)
        │
        ▼
4. Container updated in seconds
        │
        ▼
5. Tilt shows logs, status in UI
        │
        ▼
6. You see your change immediately
```

### Installation

```bash
# macOS
brew install tilt

# Linux
curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash

# Verify
tilt version
```

### Tiltfile Basics

```python
# Tiltfile (Python-like syntax)

# Build Docker image
docker_build('myapp', '.')

# Deploy Kubernetes manifest
k8s_yaml('k8s/deployment.yaml')

# Port forward
k8s_resource('myapp', port_forwards='8080:8080')
```

### Live Update (No Rebuild)

```python
# Tiltfile with live_update
docker_build(
    'myapp',
    '.',
    live_update=[
        # Sync local files to container
        sync('./src', '/app/src'),
        # Run command after sync
        run('pip install -r requirements.txt', trigger=['requirements.txt']),
        # Restart process if needed
        restart_container(),
    ]
)

k8s_yaml('k8s/deployment.yaml')
k8s_resource('myapp', port_forwards='8080:8080')
```

### Running Tilt

```bash
# Start Tilt
tilt up

# Access UI at http://localhost:10350

# Stop Tilt
tilt down

# Run specific resources
tilt up myapp
```

### Tilt UI

```
TILT UI (http://localhost:10350)
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│ TILT                                                      ≡    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RESOURCES                                                       │
│                                                                  │
│  ✓ myapp          [Running]   Build: 0.5s   Deploy: 1.2s       │
│    └─ Pod: myapp-7f9b4c8d9-abc12   1/1   10m                   │
│                                                                  │
│  ✓ database       [Running]   (unconfigured build)              │
│    └─ Pod: postgres-5d4c7b8f-def34   1/1   10m                 │
│                                                                  │
│  ● worker         [Building]  Building image...                 │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  LOGS: myapp                                                     │
│  ────────────────────────────────────────────────────────────── │
│  [myapp] Starting server on :8080                               │
│  [myapp] Connected to database                                  │
│  [myapp] Ready to accept connections                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

> 💡 **Did You Know?** Tilt's live_update can sync file changes without rebuilding the container at all. For interpreted languages like Python or JavaScript, this means sub-second updates. You save a file, and within 1-2 seconds you see the change in the running application.

> 💡 **Did You Know?** Tilt was created by Docker veterans who experienced the pain of slow container development firsthand. The team includes engineers who built Docker Compose. Their insight: developers don't want to think about containers at all—they want to edit code and see changes. Tilt's entire architecture is designed around making the container layer invisible.

---

## Complete Tiltfile Example

```python
# Tiltfile for a microservices project

# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────
allow_k8s_contexts('docker-desktop')  # Safety: only run on local
default_registry('localhost:5000')

# ─────────────────────────────────────────────────────────────────
# API Service
# ─────────────────────────────────────────────────────────────────
docker_build(
    'api',
    context='./api',
    dockerfile='./api/Dockerfile',
    live_update=[
        sync('./api/src', '/app/src'),
        run('pip install -r requirements.txt', trigger=['requirements.txt']),
    ]
)

k8s_yaml('k8s/api.yaml')
k8s_resource('api',
    port_forwards=['8080:8080'],
    resource_deps=['database'],  # Start after database
)

# ─────────────────────────────────────────────────────────────────
# Worker Service
# ─────────────────────────────────────────────────────────────────
docker_build(
    'worker',
    context='./worker',
    live_update=[
        sync('./worker', '/app'),
    ]
)

k8s_yaml('k8s/worker.yaml')
k8s_resource('worker', resource_deps=['database', 'redis'])

# ─────────────────────────────────────────────────────────────────
# Dependencies
# ─────────────────────────────────────────────────────────────────
k8s_yaml('k8s/database.yaml')
k8s_resource('database', port_forwards=['5432:5432'])

k8s_yaml('k8s/redis.yaml')
k8s_resource('redis', port_forwards=['6379:6379'])

# ─────────────────────────────────────────────────────────────────
# Local Resource (non-K8s)
# ─────────────────────────────────────────────────────────────────
local_resource(
    'migrate',
    cmd='cd api && python manage.py migrate',
    deps=['api/migrations'],
    resource_deps=['database'],
)
```

---

## Telepresence vs Tilt

```
WHEN TO USE WHICH
════════════════════════════════════════════════════════════════════

TELEPRESENCE:
─────────────────────────────────────────────────────────────────
Best for:
• Working with shared dev/staging cluster
• Need real cloud services (databases, queues)
• Team uses same cluster
• Don't want to run everything locally

Workflow:
• Connect to remote cluster
• Intercept your service
• Run code locally with remote dependencies

═══════════════════════════════════════════════════════════════════

TILT:
─────────────────────────────────────────────────────────────────
Best for:
• Local Kubernetes (Docker Desktop, minikube)
• Need to modify multiple services
• Want visual feedback
• Fast iteration on entire stack

Workflow:
• Run entire stack locally
• Tilt auto-rebuilds on changes
• See all logs in one place

═══════════════════════════════════════════════════════════════════

COMBINED:
─────────────────────────────────────────────────────────────────
Use Tilt for local development
Use Telepresence when you need to test against
real staging/production services

Some teams use Tilt locally, then Telepresence
to verify against shared staging before PR.
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Telepresence on production | Traffic goes to your laptop | Use personal intercepts, staging only |
| No live_update in Tilt | Slow rebuild every change | Configure live_update for hot reload |
| Tilt on remote cluster | Accidental deploys | Use `allow_k8s_contexts()` |
| Forgetting to disconnect | Cluster traffic still routed to laptop | Always `telepresence quit` |
| Too many services in Tilt | Laptop overloaded | Use resource_deps, stub external services |
| No port forwards | Can't access services | Add port_forwards in Tiltfile |

---

## War Story: The Staging Outage

*A developer used Telepresence to intercept the payment service in staging. They forgot to disconnect before closing their laptop and going home. All payment traffic went to their sleeping laptop.*

**What went wrong**:
1. Global intercept (not personal)
2. No timeout on intercept
3. Laptop closed, connection dropped
4. Traffic black-holed until someone noticed

**The fix**:
```bash
# Always use personal intercepts in shared environments
telepresence intercept payment --http-header x-dev-id=$(whoami)

# Set intercept timeout
telepresence intercept payment --timeout 2h

# Have alerting on service response times
```

**Best practice**: Personal intercepts only in shared environments. Global intercepts only on dedicated dev clusters.

---

## Quiz

### Question 1
How does Telepresence's personal intercept work?

<details>
<summary>Show Answer</summary>

Personal intercepts use HTTP headers to route specific traffic:

```bash
telepresence intercept api --http-header x-user=alice
```

How it works:
1. Traffic Manager inspects incoming requests
2. Requests with `x-user: alice` → Alice's laptop
3. All other requests → normal cluster service

Benefits:
- Multiple developers can intercept same service
- Shared clusters remain functional
- No "who broke staging?" issues

Use with browser plugins or API headers to set the routing header.

</details>

### Question 2
What's the advantage of Tilt's live_update over regular docker_build?

<details>
<summary>Show Answer</summary>

**Regular docker_build**:
- Full container rebuild on every change
- Cache invalidation from early layers
- Push to registry
- Pod restart
- Time: 30-120 seconds

**live_update**:
- Syncs only changed files
- No container rebuild
- No registry push
- Optional process restart (or none for hot reload)
- Time: 1-5 seconds

For interpreted languages (Python, JS, Ruby), live_update can be 100x faster.

</details>

### Question 3
When would you use Telepresence instead of Tilt?

<details>
<summary>Show Answer</summary>

**Use Telepresence when**:
- Need access to real cloud services (managed databases, SQS, etc.)
- Team shares a dev/staging cluster
- Can't run all dependencies locally
- Testing integration with services you don't own
- Need production-like environment

**Use Tilt when**:
- Have local Kubernetes (Docker Desktop)
- Want to modify multiple services
- Need visual workflow management
- Working on full stack changes
- Don't need external services

Many teams use both: Tilt locally, Telepresence for integration testing.

</details>

---

## Hands-On Exercise

### Objective
Set up Tilt for local development with live reload.

### Environment Setup

```bash
# Ensure you have Docker Desktop with Kubernetes enabled
# Or minikube running

# Install Tilt
brew install tilt
```

### Tasks

1. **Create sample project**:
   ```bash
   mkdir tilt-demo && cd tilt-demo
   mkdir -p app k8s
   ```

2. **Create simple app**:
   ```python
   # app/main.py
   from flask import Flask
   app = Flask(__name__)

   @app.route('/')
   def hello():
       return "Hello from Tilt!"

   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=8080)
   ```

   ```dockerfile
   # app/Dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   RUN pip install flask
   COPY . .
   CMD ["python", "main.py"]
   ```

3. **Create Kubernetes manifest**:
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: demo
   spec:
     selector:
       matchLabels:
         app: demo
     template:
       metadata:
         labels:
           app: demo
       spec:
         containers:
         - name: demo
           image: demo
           ports:
           - containerPort: 8080
   ```

4. **Create Tiltfile**:
   ```python
   # Tiltfile
   docker_build(
       'demo',
       context='./app',
       live_update=[
           sync('./app', '/app'),
       ]
   )

   k8s_yaml('k8s/deployment.yaml')
   k8s_resource('demo', port_forwards='8080:8080')
   ```

5. **Run Tilt**:
   ```bash
   tilt up
   # Open http://localhost:10350 for UI
   # Open http://localhost:8080 for app
   ```

6. **Test live update**:
   - Edit `app/main.py`
   - Change "Hello from Tilt!" to "Hello, updated!"
   - Watch Tilt sync the change
   - Refresh http://localhost:8080

### Success Criteria
- [ ] Tilt starts without errors
- [ ] App accessible at localhost:8080
- [ ] Tilt UI shows resource status
- [ ] File changes sync in seconds
- [ ] Can see logs in Tilt UI

### Bonus Challenge
Add a second service (database) and configure resource dependencies so the app waits for the database.

---

## Further Reading

- [Telepresence Documentation](https://www.telepresence.io/docs/)
- [Tilt Documentation](https://docs.tilt.dev/)
- [Tilt Snippets Library](https://github.com/tilt-dev/tilt-extensions)

---

## Next Module

Continue to [Module 8.3: Local Kubernetes](../module-8.3-local-kubernetes/) to learn about kind, minikube, and local Kubernetes development environments.

---

*"The best development environment is one where you forget infrastructure exists. Telepresence and Tilt make that possible."*
