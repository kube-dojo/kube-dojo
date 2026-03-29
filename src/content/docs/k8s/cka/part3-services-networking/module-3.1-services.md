---
title: "Module 3.1: Services Deep-Dive"
slug: k8s/cka/part3-services-networking/module-3.1-services
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Core networking concept
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 2.1 (Pods), Module 2.2 (Deployments)

---

## Why This Module Matters

Pods are ephemeral—they come and go, and their IP addresses change. Services provide **stable networking** for your applications. Without services, you'd have to track every pod IP manually, which is impossible at scale.

The CKA exam heavily tests services. You'll need to create services quickly, expose deployments, debug service connectivity, and understand when to use each service type.

> **The Restaurant Analogy**
>
> Imagine a restaurant (your application). Pods are the individual chefs—they might change shifts, get sick, or be replaced. The restaurant's phone number (Service) stays the same regardless of which chefs are working. Customers (clients) call the same number, and the call gets routed to an available chef. That's exactly what Services do in Kubernetes.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand the four service types and when to use each
- Create services imperatively and declaratively
- Expose deployments and pods
- Debug service connectivity issues
- Use selectors to target the right pods

---

## Did You Know?

- **Services predate Pods**: The concept of stable service IPs was designed before pods existed in Kubernetes. The founders knew ephemeral pods needed stable endpoints.

- **Virtual IPs are magic**: ClusterIP addresses don't exist on any network interface. They're "virtual" IPs that kube-proxy intercepts and routes using iptables or nftables rules. (Note: IPVS mode was deprecated in K8s 1.35 — nftables is the recommended replacement.)

- **NodePort range is configurable**: The default 30000-32767 range can be changed with the `--service-node-port-range` flag on the API server, though most clusters stick with defaults.

---

## Part 1: Service Fundamentals

### 1.1 Why Services?

```
┌────────────────────────────────────────────────────────────────┐
│                     The Problem                                 │
│                                                                 │
│   Client wants to reach "web app"                              │
│                                                                 │
│   ┌─────────────────────────────────────────────────────┐      │
│   │  Pod: web-abc123   IP: 10.244.1.5   ← Created       │      │
│   │  Pod: web-def456   IP: 10.244.2.8   ← Running       │      │
│   │  Pod: web-ghi789   IP: 10.244.1.12  ← Created       │      │
│   │  Pod: web-abc123   IP: 10.244.1.5   ← Deleted!      │      │
│   │  Pod: web-xyz999   IP: 10.244.3.2   ← New pod       │      │
│   └─────────────────────────────────────────────────────┘      │
│                                                                 │
│   Which IP should the client use? They keep changing!          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                     The Solution: Services                      │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐    │
│   │            Service: web-service                        │    │
│   │            ClusterIP: 10.96.45.123                    │    │
│   │            (Never changes!)                            │    │
│   │                                                        │    │
│   │     Selector: app=web                                  │    │
│   │         │                                              │    │
│   │         ├──► Pod: web-def456 (10.244.2.8)             │    │
│   │         ├──► Pod: web-ghi789 (10.244.1.12)            │    │
│   │         └──► Pod: web-xyz999 (10.244.3.2)             │    │
│   └───────────────────────────────────────────────────────┘    │
│                                                                 │
│   Client always uses 10.96.45.123 - Kubernetes handles rest    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Service Components

| Component | Description |
|-----------|-------------|
| **ClusterIP** | Stable internal IP address for the service |
| **Selector** | Labels that identify which pods to route to |
| **Port** | The port the service listens on |
| **TargetPort** | The port on the pods to forward traffic to |
| **Endpoints** | Actual pod IPs backing the service |

### 1.3 How Services Work

```
┌────────────────────────────────────────────────────────────────┐
│                   Service Request Flow                          │
│                                                                 │
│   1. Client sends request to Service IP (10.96.45.123:80)      │
│                         │                                       │
│                         ▼                                       │
│   2. kube-proxy (on each node) intercepts                      │
│                         │                                       │
│                         ▼                                       │
│   3. kube-proxy uses iptables/nftables rules                   │
│                         │                                       │
│                         ▼                                       │
│   4. Request forwarded to one of the pod IPs                   │
│      (load balanced - round robin by default)                  │
│                         │                                       │
│                         ▼                                       │
│   5. Pod receives request on targetPort                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Service Types

### 2.1 The Four Service Types

| Type | Scope | Use Case | Exam Frequency |
|------|-------|----------|----------------|
| **ClusterIP** | Internal only | Pod-to-pod communication | ⭐⭐⭐⭐⭐ |
| **NodePort** | External via node IP | Development, testing | ⭐⭐⭐⭐ |
| **LoadBalancer** | External via cloud LB | Production in cloud | ⭐⭐⭐ |
| **ExternalName** | DNS alias | External services | ⭐⭐ |

### 2.2 ClusterIP (Default)

```yaml
# Internal-only access - most common type
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: ClusterIP           # Default, can be omitted
  selector:
    app: web                # Match pods with label app=web
  ports:
  - port: 80                # Service listens on port 80
    targetPort: 8080        # Forward to pod port 8080
```

```
┌────────────────────────────────────────────────────────────────┐
│                     ClusterIP Service                           │
│                                                                 │
│   Only accessible from within the cluster                      │
│                                                                 │
│   ┌────────────────┐        ┌────────────────┐                │
│   │  Other Pod     │───────►│  ClusterIP     │                │
│   │  (client)      │        │  10.96.45.123  │                │
│   └────────────────┘        │                │                │
│                             │  ┌──────────┐  │                │
│                             │  │ Pod      │  │                │
│                             │  │ app=web  │  │                │
│   ┌────────────────┐        │  └──────────┘  │                │
│   │  External      │───X───►│                │                │
│   │  (blocked)     │        │  ┌──────────┐  │                │
│   └────────────────┘        │  │ Pod      │  │                │
│                             │  │ app=web  │  │                │
│                             │  └──────────┘  │                │
│                             └────────────────┘                │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 NodePort

```yaml
# Exposes service on each node's IP at a static port
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80              # ClusterIP port (internal)
    targetPort: 8080      # Pod port
    nodePort: 30080       # External port (30000-32767)
```

```
┌────────────────────────────────────────────────────────────────┐
│                     NodePort Service                            │
│                                                                 │
│   External access via <NodeIP>:<NodePort>                      │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    Cluster                               │  │
│   │                                                          │  │
│   │  Node 1 (192.168.1.10)     Node 2 (192.168.1.11)       │  │
│   │  ┌──────────────────┐      ┌──────────────────┐        │  │
│   │  │ :30080 ──────────┼──────┼─► Pod (app=web)  │        │  │
│   │  └──────────────────┘      └──────────────────┘        │  │
│   │                                                          │  │
│   └─────────────────────────────────────────────────────────┘  │
│                 ▲                          ▲                   │
│                 │                          │                   │
│   External: 192.168.1.10:30080  OR  192.168.1.11:30080        │
│             (Both work!)                                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.4 LoadBalancer

```yaml
# Creates external load balancer (cloud provider)
apiVersion: v1
kind: Service
metadata:
  name: web-lb
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

```
┌────────────────────────────────────────────────────────────────┐
│                   LoadBalancer Service                          │
│                                                                 │
│   Cloud provider creates an external load balancer             │
│                                                                 │
│   ┌──────────────────┐                                         │
│   │   Internet       │                                         │
│   └────────┬─────────┘                                         │
│            │                                                    │
│            ▼                                                    │
│   ┌──────────────────┐     External IP: 34.85.123.45           │
│   │   Cloud LB       │                                         │
│   │   (AWS/GCP/Azure)│                                         │
│   └────────┬─────────┘                                         │
│            │                                                    │
│            ▼                                                    │
│   ┌──────────────────────────────────────────────────┐         │
│   │             NodePort (auto-created)               │         │
│   │                      │                            │         │
│   │        ┌─────────────┼─────────────┐             │         │
│   │        ▼             ▼             ▼             │         │
│   │    ┌──────┐     ┌──────┐     ┌──────┐           │         │
│   │    │ Pod  │     │ Pod  │     │ Pod  │           │         │
│   │    └──────┘     └──────┘     └──────┘           │         │
│   └──────────────────────────────────────────────────┘         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.5 ExternalName

```yaml
# DNS alias to external service (no proxying)
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: database.example.com   # Returns CNAME record
  # No selector - points to external DNS name
```

```
┌────────────────────────────────────────────────────────────────┐
│                   ExternalName Service                          │
│                                                                 │
│   DNS alias - no ClusterIP, no proxying                        │
│                                                                 │
│   ┌────────────────┐                                           │
│   │  Pod           │                                           │
│   │                │──► DNS: external-db.default.svc           │
│   │                │          │                                │
│   └────────────────┘          │ Returns CNAME                  │
│                               ▼                                │
│                     database.example.com                       │
│                               │                                │
│                               ▼                                │
│                     ┌──────────────────┐                       │
│                     │  External DB     │                       │
│                     │  (outside K8s)   │                       │
│                     └──────────────────┘                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Creating Services

### 3.1 Imperative Commands (Fast for Exam)

```bash
# Expose a deployment (most common exam task)
k expose deployment nginx --port=80 --target-port=8080 --name=nginx-svc

# Expose with NodePort
k expose deployment nginx --port=80 --type=NodePort --name=nginx-np

# Expose a pod
k expose pod nginx --port=80 --name=nginx-pod-svc

# Generate YAML without creating
k expose deployment nginx --port=80 --dry-run=client -o yaml > svc.yaml

# Create service for existing pods by selector
k create service clusterip my-svc --tcp=80:8080
```

### 3.2 Expose Command Options

```bash
# Full syntax
k expose deployment <name> \
  --port=<service-port> \
  --target-port=<pod-port> \
  --type=<ClusterIP|NodePort|LoadBalancer> \
  --name=<service-name> \
  --protocol=<TCP|UDP>

# Examples
k expose deployment web --port=80 --target-port=8080
k expose deployment web --port=80 --type=NodePort
k expose deployment web --port=80 --type=LoadBalancer
```

### 3.3 Declarative YAML

```yaml
# Complete service example
apiVersion: v1
kind: Service
metadata:
  name: web-service
  labels:
    app: web
spec:
  type: ClusterIP
  selector:
    app: web              # MUST match pod labels
    tier: frontend
  ports:
  - name: http            # Named port (good practice)
    port: 80              # Service port
    targetPort: 8080      # Pod port (can be name or number)
    protocol: TCP         # TCP (default) or UDP
```

### 3.4 Multi-Port Services

```yaml
# Service with multiple ports
apiVersion: v1
kind: Service
metadata:
  name: multi-port-svc
spec:
  selector:
    app: web
  ports:
  - name: http            # Required when multiple ports
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
  - name: metrics
    port: 9090
    targetPort: 9090
```

---

## Part 4: Service Discovery

### 4.1 DNS-Based Discovery

Every service gets a DNS entry:
- `<service-name>` - within same namespace
- `<service-name>.<namespace>` - cross-namespace
- `<service-name>.<namespace>.svc.cluster.local` - fully qualified

```bash
# From a pod in the same namespace
curl web-service

# From a pod in different namespace
curl web-service.production

# Fully qualified (always works)
curl web-service.production.svc.cluster.local
```

### 4.2 Environment Variables

Kubernetes injects service info into pods:

```bash
# Environment variables for service "web-service"
WEB_SERVICE_SERVICE_HOST=10.96.45.123
WEB_SERVICE_SERVICE_PORT=80

# Note: Only works for services created BEFORE the pod
```

### 4.3 Finding Services

```bash
# List services
k get services
k get svc                    # Short form

# Get service details
k describe svc web-service

# Get service endpoints
k get endpoints web-service

# Get service YAML
k get svc web-service -o yaml

# Find service ClusterIP
k get svc web-service -o jsonpath='{.spec.clusterIP}'
```

---

## Part 5: Selectors and Endpoints

### 5.1 How Selectors Work

```yaml
# Service selector MUST match pod labels exactly
# Service:
spec:
  selector:
    app: web
    tier: frontend

# Pod (will be selected):
metadata:
  labels:
    app: web
    tier: frontend
    version: v2          # Extra labels OK

# Pod (will NOT be selected - missing tier):
metadata:
  labels:
    app: web
    version: v2
```

### 5.2 Endpoints

Endpoints are automatically created when pods match the selector:

```bash
# View endpoints (pod IPs backing the service)
k get endpoints web-service
# NAME          ENDPOINTS                         AGE
# web-service   10.244.1.5:8080,10.244.2.8:8080   5m

# Detailed endpoint info
k describe endpoints web-service
```

### 5.3 Service Without Selector

Create a service that points to manual endpoints:

```yaml
# Service without selector
apiVersion: v1
kind: Service
metadata:
  name: external-service
spec:
  ports:
  - port: 80
    targetPort: 80
---
# Manual endpoints
apiVersion: v1
kind: Endpoints
metadata:
  name: external-service    # Must match service name
subsets:
- addresses:
  - ip: 192.168.1.100      # External IP
  - ip: 192.168.1.101
  ports:
  - port: 80
```

Use case: Pointing to external databases or services outside the cluster.

---

## Part 6: Debugging Services

### 6.1 Service Debugging Workflow

```
Service Not Working?
    │
    ├── kubectl get svc (check service exists)
    │       │
    │       └── Check TYPE, CLUSTER-IP, EXTERNAL-IP, PORT
    │
    ├── kubectl get endpoints <svc> (check endpoints)
    │       │
    │       ├── No endpoints? → Selector doesn't match pods
    │       │                   Check pod labels
    │       │
    │       └── Endpoints exist? → Pods aren't responding
    │                              Check pod health
    │
    ├── kubectl describe svc <svc> (check selector)
    │       │
    │       └── Verify selector matches pod labels
    │
    └── Test from inside cluster:
        kubectl run test --rm -it --image=busybox -- wget -qO- <svc>
```

### 6.2 Common Service Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| No endpoints | Selector doesn't match pods | Fix selector or pod labels |
| Connection refused | Pod not listening on targetPort | Check pod port configuration |
| Timeout | Pod not running or crashlooping | Debug pod issues first |
| NodePort not accessible | Firewall blocking port | Check node firewall rules |
| Wrong service type | Using ClusterIP for external access | Change to NodePort/LoadBalancer |

### 6.3 Debugging Commands

```bash
# Check service and endpoints
k get svc,endpoints

# Verify selector matches pods
k get pods --selector=app=web

# Test connectivity from within cluster
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://web-service

# Test with curl
k run test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s http://web-service

# Check DNS resolution
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web-service

# Check port on pod directly
k exec <pod> -- netstat -tlnp
```

> **War Story: The Selector Mismatch**
>
> A developer spent hours debugging why their service had no endpoints. The deployment used `app: web-app` but the service selector was `app: webapp` (no hyphen). One character difference = zero connectivity. Always copy-paste selectors!

---

## Part 7: Service Session Affinity

### 7.1 Session Affinity Options

```yaml
# Sticky sessions - route same client to same pod
apiVersion: v1
kind: Service
metadata:
  name: sticky-service
spec:
  selector:
    app: web
  sessionAffinity: ClientIP      # None (default) or ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800      # 3 hours (default)
  ports:
  - port: 80
```

### 7.2 When to Use Session Affinity

| Scenario | Use Affinity? |
|----------|---------------|
| Stateless API | No (default) |
| Shopping cart in pod memory | Yes (but better: use Redis) |
| WebSocket connections | Yes |
| Authentication sessions in memory | Yes (but better: external store) |

---

## Traffic Distribution (K8s 1.35+)

Kubernetes 1.35 graduated **PreferSameNode** traffic distribution to GA, giving you fine-grained control over where service traffic is routed:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: latency-sensitive
spec:
  selector:
    app: cache
  ports:
  - port: 6379
  trafficDistribution: PreferSameNode  # Route to local node first
```

| Value | Behavior |
|-------|----------|
| `PreferSameNode` | Strictly prefer endpoints on the same node, fall back to remote (GA in 1.35) |
| `PreferClose` | Prefer endpoints topologically close — same zone when using topology-aware routing |

This is particularly useful for latency-sensitive workloads like caches, sidecars, and node-local services.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Selector mismatch | Service has no endpoints | Ensure selector matches pod labels exactly |
| Port vs TargetPort confusion | Connection refused | Port = service, TargetPort = pod |
| Missing service type | Can't access externally | Specify NodePort or LoadBalancer |
| Using ClusterIP externally | Connection timeout | ClusterIP is internal only |
| Forgetting namespace | Service not found | Use FQDN for cross-namespace |

---

## Quiz

1. **What's the difference between `port` and `targetPort` in a service?**
   <details>
   <summary>Answer</summary>
   `port` is the port the service listens on. `targetPort` is the port on the pod that receives the traffic. Example: Service listens on 80, forwards to pod's 8080.
   </details>

2. **A service shows "No endpoints". What's the most likely cause?**
   <details>
   <summary>Answer</summary>
   The service's selector doesn't match any running pod's labels. Check that the selector labels exactly match the pod labels using `k get pods --show-labels`.
   </details>

3. **How do you access a ClusterIP service from outside the cluster?**
   <details>
   <summary>Answer</summary>
   You can't directly. ClusterIP is internal only. You need to either:
   - Change to NodePort or LoadBalancer type
   - Use `kubectl port-forward`
   - Access via an Ingress or Gateway
   </details>

4. **What command exposes a deployment as a NodePort service on port 80?**
   <details>
   <summary>Answer</summary>
   `k expose deployment <name> --port=80 --type=NodePort`

   The nodePort will be auto-assigned (30000-32767) unless specified.
   </details>

5. **What DNS name can a pod in namespace "prod" use to reach service "api" in namespace "staging"?**
   <details>
   <summary>Answer</summary>
   `api.staging` or the full FQDN `api.staging.svc.cluster.local`
   </details>

---

## Hands-On Exercise

**Task**: Create and debug services for a multi-tier application.

**Steps**:

1. **Create a backend deployment**:
```bash
k create deployment backend --image=nginx --replicas=2
k set env deployment/backend APP=backend
```

2. **Label the pods properly**:
```bash
k label deployment backend tier=backend
```

3. **Expose backend as ClusterIP**:
```bash
k expose deployment backend --port=80 --name=backend-svc
```

4. **Verify the service**:
```bash
k get svc backend-svc
k get endpoints backend-svc
```

5. **Create a frontend deployment**:
```bash
k create deployment frontend --image=nginx --replicas=2
```

6. **Expose frontend as NodePort**:
```bash
k expose deployment frontend --port=80 --type=NodePort --name=frontend-svc
```

7. **Test internal connectivity**:
```bash
# From a test pod, reach the backend service
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://backend-svc
```

8. **Test cross-namespace**:
```bash
# Create another namespace and test
k create namespace other
k run test -n other --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://backend-svc.default
```

9. **Debug a broken service**:
```bash
# Create a service with wrong selector
k create service clusterip broken-svc --tcp=80:80
# Check endpoints (should be empty)
k get endpoints broken-svc
# Fix by creating proper service
k delete svc broken-svc
k expose deployment backend --port=80 --name=broken-svc --selector=app=backend
k get endpoints broken-svc
```

10. **Cleanup**:
```bash
k delete deployment frontend backend
k delete svc backend-svc frontend-svc broken-svc
k delete namespace other
```

**Success Criteria**:
- [ ] Can create ClusterIP and NodePort services
- [ ] Understand port vs targetPort
- [ ] Can debug services with no endpoints
- [ ] Can access services across namespaces
- [ ] Understand when to use each service type

---

## Practice Drills

### Drill 1: Service Creation Speed (Target: 2 minutes)

Create services for a deployment as fast as possible:

```bash
# Setup
k create deployment drill-app --image=nginx --replicas=2

# Create ClusterIP service
k expose deployment drill-app --port=80 --name=drill-clusterip

# Create NodePort service
k expose deployment drill-app --port=80 --type=NodePort --name=drill-nodeport

# Verify both
k get svc drill-clusterip drill-nodeport

# Generate YAML
k expose deployment drill-app --port=80 --dry-run=client -o yaml > svc.yaml

# Cleanup
k delete deployment drill-app
k delete svc drill-clusterip drill-nodeport
rm svc.yaml
```

### Drill 2: Multi-Port Service (Target: 3 minutes)

```bash
# Create deployment
k create deployment multi-port --image=nginx

# Create multi-port service from YAML
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: multi-port-svc
spec:
  selector:
    app: multi-port
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: https
    port: 443
    targetPort: 443
EOF

# Verify
k describe svc multi-port-svc

# Cleanup
k delete deployment multi-port
k delete svc multi-port-svc
```

### Drill 3: Service Discovery (Target: 3 minutes)

```bash
# Create service
k create deployment web --image=nginx
k expose deployment web --port=80

# Test DNS resolution
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web

# Test full FQDN
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default.svc.cluster.local

# Test connectivity
k run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s http://web

# Cleanup
k delete deployment web
k delete svc web
```

### Drill 4: Endpoint Debugging (Target: 4 minutes)

```bash
# Create deployment with specific labels
k create deployment endpoint-test --image=nginx
k label deployment endpoint-test tier=web --overwrite

# Create service with WRONG selector (intentionally broken)
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: broken-endpoints
spec:
  selector:
    app: wrong-label    # This won't match!
  ports:
  - port: 80
EOF

# Observe: no endpoints
k get endpoints broken-endpoints
# ENDPOINTS: <none>

# Debug: check what selector should be
k get pods --show-labels

# Fix: delete and recreate with correct selector
k delete svc broken-endpoints
k expose deployment endpoint-test --port=80 --name=fixed-endpoints

# Verify: endpoints exist now
k get endpoints fixed-endpoints

# Cleanup
k delete deployment endpoint-test
k delete svc fixed-endpoints
```

### Drill 5: Cross-Namespace Access (Target: 3 minutes)

```bash
# Create service in default namespace
k create deployment app --image=nginx
k expose deployment app --port=80

# Create other namespace
k create namespace testing

# Access from other namespace - short form
k run test -n testing --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://app.default

# Access with FQDN
k run test -n testing --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- http://app.default.svc.cluster.local

# Cleanup
k delete deployment app
k delete svc app
k delete namespace testing
```

### Drill 6: NodePort Specific Port (Target: 3 minutes)

```bash
# Create deployment
k create deployment nodeport-test --image=nginx

# Create NodePort with specific port
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: specific-nodeport
spec:
  type: NodePort
  selector:
    app: nodeport-test
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080    # Specific port
EOF

# Verify port
k get svc specific-nodeport
# Should show 80:30080/TCP

# Cleanup
k delete deployment nodeport-test
k delete svc specific-nodeport
```

### Drill 7: ExternalName Service (Target: 2 minutes)

```bash
# Create ExternalName service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: external-api
spec:
  type: ExternalName
  externalName: api.example.com
EOF

# Check the service (no ClusterIP!)
k get svc external-api
# Note: CLUSTER-IP shows as <none>

# Test DNS resolution
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup external-api
# Shows CNAME to api.example.com

# Cleanup
k delete svc external-api
```

### Drill 8: Challenge - Complete Service Workflow

Without looking at solutions:

1. Create deployment `challenge-app` with nginx, 3 replicas
2. Expose as ClusterIP service on port 80
3. Verify endpoints show 3 pod IPs
4. Scale deployment to 5 replicas
5. Verify endpoints now show 5 pod IPs
6. Change service to NodePort type
7. Get the NodePort number
8. Cleanup everything

```bash
# YOUR TASK: Complete in under 5 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. Create deployment
k create deployment challenge-app --image=nginx --replicas=3

# 2. Expose as ClusterIP
k expose deployment challenge-app --port=80

# 3. Verify 3 endpoints
k get endpoints challenge-app

# 4. Scale to 5
k scale deployment challenge-app --replicas=5

# 5. Verify 5 endpoints
k get endpoints challenge-app

# 6. Change to NodePort (delete and recreate)
k delete svc challenge-app
k expose deployment challenge-app --port=80 --type=NodePort

# 7. Get NodePort
k get svc challenge-app -o jsonpath='{.spec.ports[0].nodePort}'

# 8. Cleanup
k delete deployment challenge-app
k delete svc challenge-app
```

</details>

---

## Next Module

[Module 3.2: Endpoints & EndpointSlices](../module-3.2-endpoints/) - Deep-dive into how services track pods.
