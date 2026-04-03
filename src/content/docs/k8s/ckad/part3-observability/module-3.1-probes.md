---
title: "Module 3.1: Application Probes"
slug: k8s/ckad/part3-observability/module-3.1-probes
sidebar:
  order: 1
lab:
  id: ckad-3.1-probes
  url: https://killercoda.com/kubedojo/scenario/ckad-3.1-probes
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical exam topic with multiple probe types
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 1.1 (Pods), understanding of container lifecycle

---

## Learning Outcomes

After completing this module, you will be able to:
- **Configure** liveness, readiness, and startup probes with appropriate thresholds and timing
- **Debug** pod restart loops and traffic routing issues caused by misconfigured probes
- **Explain** the difference between liveness, readiness, and startup probes and when each applies
- **Implement** HTTP, TCP, and exec probes matched to your application's health-check capabilities

---

## Why This Module Matters

Probes tell Kubernetes how to check if your application is alive, ready to receive traffic, or needs more startup time. Without probes, Kubernetes has no way to know if your application is actually working—it only knows if the container process is running.

The CKAD exam frequently tests probes because they're essential for production applications. Expect questions on:
- Configuring liveness, readiness, and startup probes
- Choosing between HTTP, TCP, and exec probes
- Setting appropriate thresholds and timing

> **The Health Checkup Analogy**
>
> Think of probes like a hospital monitoring system. A **liveness probe** checks if the patient is alive (if not, emergency intervention). A **readiness probe** checks if the patient can receive visitors (if not, no visitors yet). A **startup probe** gives the patient time to wake up from surgery before checking vital signs. Each serves a different purpose, and using the wrong one causes problems.

---

## The Three Probe Types

### Liveness Probe

**Question it answers**: "Is the application alive, or should we restart it?"

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
  failureThreshold: 3
```

**When liveness fails**: Kubernetes kills the container and restarts it.

**Use when**:
- Application can get into a stuck state (deadlock, infinite loop)
- Restart would fix the issue
- You need automatic recovery from application bugs

> **Pause and predict**: If you configure a liveness probe with `initialDelaySeconds: 0` on an app that takes 30 seconds to start, what will happen? Think through the timeline before reading on.

### Readiness Probe

**Question it answers**: "Is the application ready to receive traffic?"

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

**When readiness fails**: Pod removed from Service endpoints (no traffic).

**Use when**:
- Application needs warmup time (loading caches, connecting to DB)
- Application temporarily overloaded
- Dependent services unavailable

### Startup Probe

**Question it answers**: "Has the application finished starting up?"

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

**When startup succeeds**: Liveness and readiness probes begin.

**Use when**:
- Application has long/variable startup times
- You'd set a very high `initialDelaySeconds` on liveness otherwise
- Legacy applications with unpredictable boot times

---

## Probe Mechanisms

### HTTP GET Probe

Most common for web applications:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
    httpHeaders:
    - name: Custom-Header
      value: Awesome
  initialDelaySeconds: 10
  periodSeconds: 5
```

- Success: HTTP status 200-399
- Failure: Any other status or timeout

### TCP Socket Probe

For non-HTTP services (databases, message queues):

```yaml
livenessProbe:
  tcpSocket:
    port: 3306
  initialDelaySeconds: 15
  periodSeconds: 10
```

- Success: Connection established
- Failure: Connection refused or timeout

### Exec Probe

Run a command inside the container:

```yaml
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

- Success: Exit code 0
- Failure: Non-zero exit code

---

## Probe Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `initialDelaySeconds` | Wait before first probe | 0 |
| `periodSeconds` | How often to probe | 10 |
| `timeoutSeconds` | Probe timeout | 1 |
| `successThreshold` | Successes needed after failure | 1 |
| `failureThreshold` | Failures before action | 3 |

> **Stop and think**: You have an app that connects to a database on startup. Should you use the same endpoint for liveness and readiness probes? What could go wrong if you do?

### Calculating Probe Timing

**Time before first probe**: `initialDelaySeconds`

**Time before failure action**:
`initialDelaySeconds + (failureThreshold × periodSeconds)`

Example with defaults:
- `initialDelaySeconds: 0`
- `periodSeconds: 10`
- `failureThreshold: 3`
- Time to restart: `0 + (3 × 10) = 30 seconds`

---

## Common Patterns

### Combined Probes for Web App

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  containers:
  - name: app
    image: myapp:v1
    ports:
    - containerPort: 8080
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 30
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      periodSeconds: 5
      failureThreshold: 3
```

### Database Connection Check

```yaml
livenessProbe:
  exec:
    command:
    - pg_isready
    - -U
    - postgres
  initialDelaySeconds: 30
  periodSeconds: 10
```

> **Pause and predict**: For a Redis container, would you use an HTTP, TCP, or exec probe for liveness? Why might one be better than the others?

### gRPC Health Check

```yaml
livenessProbe:
  grpc:
    port: 50051
  initialDelaySeconds: 10
  periodSeconds: 10
```

---

## Probe Comparison

```
┌─────────────────────────────────────────────────────────────┐
│                    Probe Comparison                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Startup Probe                                              │
│  ├── Runs FIRST (before liveness/readiness)                │
│  ├── Failure: Keeps trying until threshold                 │
│  └── Success: Enables liveness/readiness probes            │
│                                                             │
│  Liveness Probe                                             │
│  ├── Runs AFTER startup succeeds                           │
│  ├── Failure: KILL and RESTART container                   │
│  └── Success: Container is alive, do nothing               │
│                                                             │
│  Readiness Probe                                            │
│  ├── Runs AFTER startup succeeds                           │
│  ├── Failure: REMOVE from Service endpoints                │
│  └── Success: ADD to Service endpoints                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Exam Shortcuts

### Add Probe to Existing Pod YAML

```bash
# Generate pod with no probes
k run webapp --image=nginx --port=80 --dry-run=client -o yaml > pod.yaml

# Add probes manually (fastest in exam)
```

### Quick Liveness Probe Pod

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: liveness-demo
spec:
  containers:
  - name: app
    image: nginx
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
EOF
```

### Verify Probes Working

```bash
# Check pod events for probe activity
k describe pod webapp | grep -A 10 Events

# Watch for restarts (liveness failures)
k get pod webapp -w

# Check endpoint membership (readiness)
k get endpoints myservice
```

---

## Did You Know?

- **Startup probe was added in Kubernetes 1.16** to solve the "legacy app" problem. Before that, you had to set huge `initialDelaySeconds` on liveness probes, which delayed detection of actual failures.

- **An exec probe runs inside the container**, meaning it shares the container's filesystem and environment. This is powerful for custom health checks but adds overhead.

- **HTTP probes follow redirects (3xx).** If your `/healthz` redirects to `/login`, the probe sees `200 OK` from the final destination and succeeds.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Liveness probe too aggressive | Kills healthy slow apps | Use startup probe for slow starters |
| Same probe for liveness and readiness | Different purposes mixed | Separate endpoints: `/healthz` vs `/ready` |
| Readiness checking external deps | Entire cluster fails if one dep down | Only check what this pod controls |
| No `initialDelaySeconds` | Container killed before app starts | Give app time to initialize |
| `timeoutSeconds: 1` for slow checks | Timeouts cause restarts | Increase for slow health endpoints |

---

## Quiz

1. **A developer deploys a pod with a liveness probe pointing to `/healthz`. The pod starts, runs for about 30 seconds, then restarts. The restart count keeps climbing. The application logs show no errors. What is likely wrong and how do you fix it?**
   <details>
   <summary>Answer</summary>
   The liveness probe is likely failing because the `/healthz` endpoint is returning a non-2xx status code or timing out, even though the application itself is running fine. This commonly happens when the probe path doesn't exist in the app, the wrong port is specified, or `timeoutSeconds` is too low for the health endpoint's response time. Check with `kubectl describe pod` to see the probe failure events, verify the endpoint exists by exec-ing into the pod and curling it, and adjust the probe path, port, or timing parameters accordingly.
   </details>

2. **After deploying a new version, users report that the application is intermittently unavailable. You check and see all pods are Running with 0 restarts. However, `kubectl get endpoints` for the Service shows pods appearing and disappearing. What probe is likely misconfigured and why?**
   <details>
   <summary>Answer</summary>
   The readiness probe is failing intermittently, causing pods to be removed from and re-added to Service endpoints. This creates the appearance of intermittent availability even though the pods never restart (readiness failures remove traffic, not kill containers). The fix depends on the root cause: the readiness probe might be checking an external dependency that's flaky, or the thresholds might be too aggressive. Investigate with `kubectl describe pod` to see readiness probe failure messages, and consider whether the readiness endpoint is checking something the pod actually controls versus an external service.
   </details>

3. **A legacy Java application takes between 60 and 180 seconds to start. The team has set `initialDelaySeconds: 200` on the liveness probe to compensate. What is the problem with this approach and what is a better solution?**
   <details>
   <summary>Answer</summary>
   Setting `initialDelaySeconds: 200` means that if the application genuinely crashes after startup, Kubernetes won't detect it for over 3 minutes (200s delay + failureThreshold * periodSeconds). This delays recovery from real failures. The better solution is to use a startup probe with a high `failureThreshold` and reasonable `periodSeconds` (e.g., `failureThreshold: 30, periodSeconds: 10` gives 300 seconds of startup time). Once the startup probe succeeds, the liveness probe kicks in with aggressive settings (e.g., `periodSeconds: 10, failureThreshold: 3`) for fast failure detection.
   </details>

4. **You create a pod with all three probe types. The startup probe uses `failureThreshold: 30` and `periodSeconds: 10`. How long does Kubernetes wait before killing the pod if the app never starts? What happens to the liveness and readiness probes during this time?**
   <details>
   <summary>Answer</summary>
   Kubernetes waits up to 300 seconds (30 failures x 10 seconds) before killing the container due to startup probe failure. During this entire startup period, the liveness and readiness probes are completely disabled — they don't run at all until the startup probe succeeds at least once. This is the key advantage of startup probes: they gate the other probes, preventing premature liveness kills during slow startups while still allowing aggressive liveness checking after startup completes.
   </details>

---

## Hands-On Exercise

**Task**: Configure all three probe types for a web application.

**Setup:**
```bash
# Create a test pod with long startup
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: probe-demo
  labels:
    app: probe-demo
spec:
  containers:
  - name: app
    image: nginx
    ports:
    - containerPort: 80
    startupProbe:
      httpGet:
        path: /
        port: 80
      failureThreshold: 10
      periodSeconds: 5
    livenessProbe:
      httpGet:
        path: /
        port: 80
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /
        port: 80
      periodSeconds: 5
      failureThreshold: 2
EOF
```

**Verify:**
```bash
# Watch pod status
k get pod probe-demo -w

# Check probe events
k describe pod probe-demo | grep -A 15 Events

# Create service
k expose pod probe-demo --port=80

# Check endpoints
k get ep probe-demo
```

**Break it (for learning):**
```bash
# Make liveness fail - exec into pod and break nginx
k exec probe-demo -- rm /usr/share/nginx/html/index.html

# Watch restart happen
k get pod probe-demo -w
```

**Cleanup:**
```bash
k delete pod probe-demo
k delete svc probe-demo
```

---

## Practice Drills

### Drill 1: HTTP Liveness Probe (Target: 2 minutes)

```bash
# Create pod with HTTP liveness probe
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill1
spec:
  containers:
  - name: nginx
    image: nginx
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
EOF

# Verify
k describe pod drill1 | grep Liveness

# Cleanup
k delete pod drill1
```

### Drill 2: Exec Probe (Target: 2 minutes)

```bash
# Create pod with exec probe
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill2
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'touch /tmp/healthy && sleep 3600']
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      initialDelaySeconds: 5
      periodSeconds: 5
EOF

# Verify running
k get pod drill2

# Cleanup
k delete pod drill2
```

### Drill 3: TCP Probe (Target: 2 minutes)

```bash
# Create pod with TCP probe
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: redis
    image: redis
    livenessProbe:
      tcpSocket:
        port: 6379
      initialDelaySeconds: 10
      periodSeconds: 5
EOF

# Verify
k describe pod drill3 | grep Liveness

# Cleanup
k delete pod drill3
```

### Drill 4: Readiness Probe (Target: 3 minutes)

```bash
# Create deployment with readiness probe
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill4
spec:
  replicas: 2
  selector:
    matchLabels:
      app: drill4
  template:
    metadata:
      labels:
        app: drill4
    spec:
      containers:
      - name: nginx
        image: nginx
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 2
          periodSeconds: 3
EOF

# Create service
k expose deploy drill4 --port=80

# Check endpoints (should have 2)
k get endpoints drill4

# Cleanup
k delete deploy drill4
k delete svc drill4
```

### Drill 5: Combined Probes (Target: 4 minutes)

```bash
# Create pod with startup, liveness, and readiness
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill5
  labels:
    app: drill5
spec:
  containers:
  - name: app
    image: nginx
    ports:
    - containerPort: 80
    startupProbe:
      httpGet:
        path: /
        port: 80
      failureThreshold: 30
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /
        port: 80
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      periodSeconds: 5
EOF

# Verify all probes
k describe pod drill5 | grep -E "Liveness|Readiness|Startup"

# Create service and verify endpoint
k expose pod drill5 --port=80
k get ep drill5

# Cleanup
k delete pod drill5 svc drill5
```

### Drill 6: Failing Probe Scenario (Target: 5 minutes)

**Scenario**: Debug a pod that keeps restarting.

```bash
# Create intentionally broken probe
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill6
spec:
  containers:
  - name: app
    image: nginx
    livenessProbe:
      httpGet:
        path: /nonexistent
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 3
      failureThreshold: 2
EOF

# Watch restarts
k get pod drill6 -w

# After a few restarts, check events
k describe pod drill6 | tail -20

# Fix the probe
k delete pod drill6
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill6
spec:
  containers:
  - name: app
    image: nginx
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
EOF

# Verify fixed
k get pod drill6

# Cleanup
k delete pod drill6
```

---

## Next Module

[Module 3.2: Container Logging](../module-3.2-logging/) - Access, manage, and troubleshoot container logs.
