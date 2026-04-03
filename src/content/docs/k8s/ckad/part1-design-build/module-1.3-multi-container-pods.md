---
title: "Module 1.3: Multi-Container Pods"
slug: k8s/ckad/part1-design-build/module-1.3-multi-container-pods
sidebar:
  order: 3
lab:
  id: ckad-1.3-multi-container-pods
  url: https://killercoda.com/kubedojo/scenario/ckad-1.3-multi-container-pods
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Essential CKAD skill requiring pattern recognition
>
> **Time to Complete**: 50-60 minutes
>
> **Prerequisites**: Module 1.1 (Container Images), Module 1.2 (Jobs and CronJobs)

---

## Learning Outcomes

After completing this module, you will be able to:
- **Create** multi-container pods using sidecar, init container, and ambassador patterns
- **Explain** when to use each multi-container pattern and their trade-offs
- **Debug** init container failures and shared-volume communication issues between containers
- **Implement** a sidecar logging pattern that ships logs from the main application container

---

## Why This Module Matters

Most applications need more than one container. A web server needs a log shipper. An API needs a proxy. A data processor needs an initializer. Multi-container pods are how you compose these pieces.

**This is a CKAD signature topic.** Expect 2-4 questions specifically about multi-container patterns. You need to recognize when to use each pattern and implement them quickly.

> **The Food Truck Analogy**
>
> A pod is like a food truck. The main container is the chef—they cook the food. But a successful food truck needs more: someone to take orders (sidecar), someone to prep before opening (init), and maybe a cashier window facing customers differently (ambassador). They all share the same truck (pod), share the counter space (filesystem), and work together—but each has a distinct role.

---

## Multi-Container Patterns

### The Three Patterns You Must Know

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Container Patterns                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INIT CONTAINER                                                  │
│  ┌─────────────┐    ┌─────────────┐                             │
│  │    Init     │───▶│    Main     │                             │
│  │  Container  │    │  Container  │                             │
│  │ (runs first)│    │ (runs after)│                             │
│  └─────────────┘    └─────────────┘                             │
│  • Initialize data, wait for dependencies, setup                 │
│                                                                  │
│  SIDECAR                                                        │
│  ┌─────────────┐    ┌─────────────┐                             │
│  │    Main     │◀──▶│   Sidecar   │                             │
│  │  Container  │    │  Container  │                             │
│  │ (app logic) │    │  (helper)   │                             │
│  └─────────────┘    └─────────────┘                             │
│  • Log shipping, monitoring, config sync                         │
│                                                                  │
│  AMBASSADOR                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    Main     │───▶│  Ambassador │───▶│   External  │         │
│  │  Container  │    │   (proxy)   │    │   Service   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│  • Proxy connections, handle TLS, rate limiting                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

> **Pause and predict**: You have a pod that needs to (a) wait for a database to be ready, (b) run a web server, and (c) continuously ship logs to Elasticsearch. Which of the three patterns -- init, sidecar, or ambassador -- would you use for each task? Decide before reading the details below.

## Init Containers

Init containers run **before** application containers start. They run sequentially, each must complete successfully before the next starts.

### Use Cases

- Wait for a service to be ready
- Clone a git repo or download files
- Generate configuration files
- Run database migrations
- Wait for permissions to be set

### Init Container YAML

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  initContainers:
  - name: init-wait
    image: busybox
    command: ['sh', '-c', 'until nslookup myservice; do echo waiting; sleep 2; done']
  - name: init-setup
    image: busybox
    command: ['sh', '-c', 'echo "Setup complete" > /data/ready']
    volumeMounts:
    - name: shared
      mountPath: /data
  containers:
  - name: main
    image: nginx
    volumeMounts:
    - name: shared
      mountPath: /usr/share/nginx/html
  volumes:
  - name: shared
    emptyDir: {}
```

### Key Properties

| Property | Behavior |
|----------|----------|
| Run order | Sequential (init1, then init2, then main) |
| Failure | Pod restarts if any init container fails |
| Restart policy | Always rerun from first init on pod restart |
| Resources | Can have different resource limits than app containers |
| Probes | No liveness/readiness probes (they just need to exit 0) |

### Init Container Status

```bash
# Check init container status
k get pod init-demo

# Detailed status
k describe pod init-demo | grep -A10 "Init Containers"

# Init container logs
k logs init-demo -c init-wait
```

---

## Sidecar Containers

Sidecars run **alongside** the main container for the pod's lifetime. They extend functionality without modifying the main application.

### Use Cases

- Log aggregation (ship logs to central system)
- Monitoring agents (metrics collection)
- Configuration sync (watch for config changes)
- Service mesh proxies (Istio, Linkerd)
- Cache population

### Sidecar YAML

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-demo
spec:
  containers:
  - name: main
    image: nginx
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx
  - name: log-shipper
    image: busybox
    command: ['sh', '-c', 'tail -F /var/log/nginx/access.log']
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx
  volumes:
  - name: logs
    emptyDir: {}
```

> **Stop and think**: Two containers in the same pod need to communicate. One approach is shared volumes; another is localhost networking. When would you choose one over the other? What kind of data flows better through files vs network calls?

### Sharing Data Between Containers

Containers in a pod can share:

1. **Volumes** (most common)
```yaml
volumes:
- name: shared
  emptyDir: {}
```

2. **Network** (same localhost)
```yaml
# Main container exposes :8080
# Sidecar can access localhost:8080
```

3. **Process namespace** (rare)
```yaml
spec:
  shareProcessNamespace: true
```

---

## Ambassador Pattern

Ambassadors proxy connections to external services, abstracting complexity from the main container.

### Use Cases

- Database connection pooling
- TLS termination
- Service discovery
- Rate limiting
- Protocol translation

### Ambassador YAML

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-demo
spec:
  containers:
  - name: main
    image: myapp
    env:
    - name: DB_HOST
      value: "localhost"    # Ambassador handles actual connection
    - name: DB_PORT
      value: "5432"
  - name: db-proxy
    image: ambassador-proxy
    env:
    - name: REAL_DB_HOST
      value: "db.production.svc"
    - name: REAL_DB_PORT
      value: "5432"
    ports:
    - containerPort: 5432   # Listens on localhost:5432 for main
```

---

## Pattern Recognition

When do you use each pattern?

| Scenario | Pattern | Why |
|----------|---------|-----|
| Wait for database before starting | Init | One-time dependency check |
| Ship logs to Elasticsearch | Sidecar | Continuous operation |
| Download config before app starts | Init | Setup task |
| Watch config file for changes | Sidecar | Continuous operation |
| Proxy database connections | Ambassador | Abstraction layer |
| Run database migrations | Init | One-time operation |
| Add TLS to non-TLS app | Ambassador | Protocol handling |
| Collect Prometheus metrics | Sidecar | Continuous operation |

---

> **What would happen if**: An init container has a bug and runs `sleep 3600` instead of completing. What state would the pod be stuck in, and how would you diagnose it?

## Creating Multi-Container Pods Quickly

You can't create multi-container pods imperatively. Use the generate-and-edit pattern:

### Step 1: Generate Base

```bash
k run multi --image=nginx --dry-run=client -o yaml > multi.yaml
```

### Step 2: Add Containers

Edit `multi.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
spec:
  containers:
  - name: nginx
    image: nginx
  - name: sidecar           # ADD THIS
    image: busybox          # ADD THIS
    command: ["sleep", "3600"]  # ADD THIS
```

### Step 3: Add Init Containers (if needed)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
spec:
  initContainers:           # ADD THIS SECTION
  - name: init
    image: busybox
    command: ["sh", "-c", "echo init done"]
  containers:
  - name: nginx
    image: nginx
  - name: sidecar
    image: busybox
    command: ["sleep", "3600"]
```

---

## Debugging Multi-Container Pods

### Specify Container

```bash
# Logs from specific container
k logs multi -c sidecar

# Exec into specific container
k exec -it multi -c sidecar -- sh

# Describe shows all containers
k describe pod multi
```

### Check Container Status

```bash
# All container statuses
k get pod multi -o jsonpath='{.status.containerStatuses[*].name}'

# Check if ready
k get pod multi -o jsonpath='{range .status.containerStatuses[*]}{.name}{"\t"}{.ready}{"\n"}{end}'
```

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Pod stuck in `Init:0/1` | Init container not completing | Check init container logs |
| One container `CrashLoopBackOff` | Container command exits | Fix command or add `sleep` |
| Containers can't share data | No shared volume | Add `emptyDir` volume |
| Main can't reach sidecar | Network misconfiguration | Use `localhost:port` |

---

## Did You Know?

- **Init containers can have different images than app containers.** Use specialized tools (like `git`, database clients) in init containers without bloating your app image.

- **Sidecar containers traditionally restart with the pod**, but Kubernetes 1.28+ introduced native sidecar support with `restartPolicy: Always` for init containers, making them true sidecars that restart independently.

- **The ambassador pattern predates service meshes.** Before Istio and Linkerd, developers used ambassador containers to handle cross-cutting concerns. Now service meshes automate sidecar injection.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting `-c container` | Wrong container logs | Always specify container |
| Init container with `sleep` | Pod never starts | Init must exit 0 |
| No shared volume | Containers can't communicate via files | Add `emptyDir` |
| Sidecar exits immediately | Pod keeps restarting | Add `sleep infinity` or actual service |
| Wrong port in localhost | Connection refused | Verify port mappings |

---

## Quiz

1. **Your pod has two init containers: `init-db` (waits for database) and `init-config` (downloads configuration). The pod is stuck showing `Init:1/2`. Which init container succeeded and which is still running? How do you find out what's wrong?**
   <details>
   <summary>Answer</summary>
   `Init:1/2` means the first init container (`init-db`) completed successfully, but the second (`init-config`) is still running or failing. Init containers run sequentially -- `init-config` can't start until `init-db` exits 0. Diagnose with `kubectl logs <pod> -c init-config` to see its output, and `kubectl describe pod <pod>` to check Events for errors like image pull failures or command errors. If `init-config` is stuck in a retry loop (e.g., downloading from an unreachable URL), fix the URL or the network issue.
   </details>

2. **A microservice team deploys their API with a sidecar that ships logs to Elasticsearch. After deployment, `kubectl get pod api-pod` shows `1/2 Ready`. The main container is fine but the sidecar keeps crashing. What are the most likely causes, and does this affect the main application?**
   <details>
   <summary>Answer</summary>
   The sidecar is likely crashing because: (1) its command exits immediately -- sidecar containers need a long-running process like `tail -F` or a proper log shipper daemon; (2) the Elasticsearch endpoint is unreachable and the shipper exits on connection failure; or (3) there's no shared volume, so the sidecar can't read the main container's logs. Check with `kubectl logs api-pod -c log-shipper`. While the main app continues running, the pod's Ready status stays `1/2`, which affects Service endpoints -- if readiness checks are configured, traffic may stop routing to this pod.
   </details>

3. **You're building an application that needs to: (1) clone a git repository before starting, (2) serve the repo content via nginx, and (3) have a background process that pulls git updates every 60 seconds. Which multi-container pattern(s) do you use, and how do the containers share the git data?**
   <details>
   <summary>Answer</summary>
   Use an init container for the initial git clone (one-time setup task), nginx as the main container to serve content, and a sidecar for the periodic git pull (continuous background operation). All three share an `emptyDir` volume mounted at the same path. The init container clones into `/data`, nginx serves from `/data`, and the sidecar runs `git pull` in `/data` every 60 seconds. This is a classic combination of init + sidecar patterns working together through shared volumes.
   </details>

4. **During the CKAD exam, you need to add a sidecar container to an existing pod. You run `kubectl logs mypod` and get an error asking you to specify a container name. Why does this happen, and what's the fastest way to find the container names?**
   <details>
   <summary>Answer</summary>
   When a pod has multiple containers, `kubectl logs` doesn't know which container's logs you want and requires the `-c` flag. The fastest way to find container names is `kubectl get pod mypod -o jsonpath='{.spec.containers[*].name}'`, which prints all container names on one line. Alternatively, `kubectl describe pod mypod` shows containers under the "Containers:" section. Once you have the name, use `kubectl logs mypod -c container-name`. In the exam, always use `-c` for multi-container pods to avoid wasting time on this error.
   </details>

---

## Hands-On Exercise

**Task**: Build a pod with init, sidecar, and main containers.

**Scenario**: Create an app that:
1. Init: Downloads config from a URL (simulated)
2. Main: Runs nginx serving the config
3. Sidecar: Monitors and logs changes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: full-pattern
spec:
  initContainers:
  - name: config-init
    image: busybox
    command: ['sh', '-c', 'echo "Welcome to CKAD!" > /data/index.html']
    volumeMounts:
    - name: html
      mountPath: /data
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
    ports:
    - containerPort: 80
  - name: monitor
    image: busybox
    command: ['sh', '-c', 'while true; do echo "Checking..."; cat /data/index.html; sleep 10; done']
    volumeMounts:
    - name: html
      mountPath: /data
  volumes:
  - name: html
    emptyDir: {}
```

**Verification:**
```bash
# Apply
k apply -f full-pattern.yaml

# Wait for ready
k get pod full-pattern -w

# Check init completed
k describe pod full-pattern | grep -A5 "Init Containers"

# Check nginx serves content
k exec full-pattern -c nginx -- curl localhost

# Check monitor logs
k logs full-pattern -c monitor

# Cleanup
k delete pod full-pattern
```

---

## Practice Drills

### Drill 1: Basic Init Container (Target: 3 minutes)

```bash
# Create pod with init container
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: init-pod
spec:
  initContainers:
  - name: init
    image: busybox
    command: ["sh", "-c", "echo 'Init complete' && sleep 3"]
  containers:
  - name: main
    image: nginx
EOF

# Watch pod start
k get pod init-pod -w

# Check init logs
k logs init-pod -c init

# Cleanup
k delete pod init-pod
```

### Drill 2: Basic Sidecar (Target: 3 minutes)

```bash
# Create pod with sidecar
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-pod
spec:
  containers:
  - name: main
    image: nginx
  - name: sidecar
    image: busybox
    command: ["sh", "-c", "while true; do echo 'Sidecar running'; sleep 5; done"]
EOF

# Verify both containers
k get pod sidecar-pod -o jsonpath='{.spec.containers[*].name}'

# Check sidecar logs
k logs sidecar-pod -c sidecar

# Cleanup
k delete pod sidecar-pod
```

### Drill 3: Shared Volume (Target: 4 minutes)

```bash
# Create pod with shared volume
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: shared-vol
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "while true; do date >> /shared/log.txt; sleep 5; done"]
    volumeMounts:
    - name: shared
      mountPath: /shared
  - name: reader
    image: busybox
    command: ["sh", "-c", "tail -f /shared/log.txt"]
    volumeMounts:
    - name: shared
      mountPath: /shared
  volumes:
  - name: shared
    emptyDir: {}
EOF

# Check reader sees writer's data
k logs shared-vol -c reader

# Cleanup
k delete pod shared-vol
```

### Drill 4: Init Waiting for Service (Target: 5 minutes)

```bash
# Create a service first
k create svc clusterip wait-svc --tcp=80:80

# Create pod that waits for service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: wait-pod
spec:
  initContainers:
  - name: wait
    image: busybox
    command: ['sh', '-c', 'until nslookup wait-svc; do echo waiting; sleep 2; done']
  containers:
  - name: main
    image: nginx
EOF

# Check init status
k describe pod wait-pod | grep -A3 "Init Containers"

# Cleanup
k delete pod wait-pod
k delete svc wait-svc
```

### Drill 5: Ambassador Pattern (Target: 5 minutes)

```bash
# Create pod with ambassador proxy
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-pod
spec:
  containers:
  - name: main
    image: busybox
    command: ["sh", "-c", "while true; do wget -qO- localhost:8080; sleep 10; done"]
  - name: proxy
    image: nginx
    ports:
    - containerPort: 8080
EOF

# Main accesses proxy via localhost
k logs ambassador-pod -c main

# Cleanup
k delete pod ambassador-pod
```

### Drill 6: Complete Multi-Container Challenge (Target: 8 minutes)

**No hints—build from memory:**

Create a pod named `app-complete` with:
1. Init container: Creates `/data/config.txt` with "Config loaded"
2. Main container (nginx): Serves `/data` directory
3. Sidecar: Monitors `/data/config.txt` every 5 seconds

After creating, verify:
- Pod is Running
- Init completed successfully
- Sidecar shows config content

<details>
<summary>Solution</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-complete
spec:
  initContainers:
  - name: init
    image: busybox
    command: ["sh", "-c", "echo 'Config loaded' > /data/config.txt"]
    volumeMounts:
    - name: data
      mountPath: /data
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  - name: monitor
    image: busybox
    command: ["sh", "-c", "while true; do cat /data/config.txt; sleep 5; done"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
```

```bash
k apply -f app-complete.yaml
k get pod app-complete
k logs app-complete -c init
k logs app-complete -c monitor
k delete pod app-complete
```

</details>

---

## Next Module

[Module 1.4: Volumes for Developers](../module-1.4-volumes/) - Persistent and ephemeral storage patterns.
