---
title: "Module 5.1: Services"
slug: k8s/ckad/part5-networking/module-5.1-services
sidebar:
  order: 1
---
> **Complexity**: `[MEDIUM]` - Core networking concept, multiple types to understand
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 1.1 (Pods), Module 2.1 (Deployments), understanding of basic networking

---

## Why This Module Matters

Services provide stable networking for pods. Since pods are ephemeral and get new IPs when recreated, you need Services to provide consistent access to your applications. Services are fundamental to how applications communicate in Kubernetes.

The CKAD exam tests:
- Creating Services (ClusterIP, NodePort, LoadBalancer)
- Understanding Service discovery
- Debugging Service connectivity
- Working with endpoints

> **The Phone Directory Analogy**
>
> Services are like a company phone directory. Employees (pods) come and go, change desks (IPs), but the department extension (Service) stays the same. When you call "Sales" (Service name), the system routes to whoever is currently working there. The directory (DNS) translates names to numbers, and the switchboard (kube-proxy) routes the call.

---

## Service Types

### ClusterIP (Default)

Internal-only access within the cluster:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP          # Default, can be omitted
  selector:
    app: my-app
  ports:
  - port: 80               # Service port
    targetPort: 8080       # Container port
```

```bash
# Create imperatively
k expose deployment my-app --port=80 --target-port=8080

# Access from within cluster
curl http://my-service:80
curl http://my-service.default.svc.cluster.local:80
```

### NodePort

Exposes on each node's IP at a static port:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-nodeport
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
  - port: 80               # Service port (ClusterIP)
    targetPort: 8080       # Container port
    nodePort: 30080        # Node port (30000-32767)
```

```bash
# Create imperatively
k expose deployment my-app --type=NodePort --port=80 --target-port=8080

# Access from outside cluster
curl http://<node-ip>:30080
```

### LoadBalancer

Provisions external load balancer (cloud environments):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-loadbalancer
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

```bash
# Create imperatively
k expose deployment my-app --type=LoadBalancer --port=80 --target-port=8080

# Get external IP
k get svc my-loadbalancer
# EXTERNAL-IP column shows the LB IP
```

### ExternalName

Maps to external DNS name (no proxying):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: database.example.com
```

---

## Service Discovery

### DNS Names

Kubernetes creates DNS records for Services:

```
<service-name>.<namespace>.svc.cluster.local
```

| DNS Name | Resolves To |
|----------|-------------|
| `my-service` | Same namespace |
| `my-service.default` | default namespace |
| `my-service.default.svc` | default namespace, svc |
| `my-service.default.svc.cluster.local` | Full FQDN |

### Environment Variables

Pods get environment variables for Services that existed when the pod started:

```bash
# Inside a pod
env | grep MY_SERVICE
# MY_SERVICE_SERVICE_HOST=10.96.0.1
# MY_SERVICE_SERVICE_PORT=80
```

---

## Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Types                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ClusterIP (Internal Only)                                  │
│  ┌─────────────────────────────────────┐                   │
│  │  cluster.local:80 ──► Pod:8080      │                   │
│  │                   ──► Pod:8080      │                   │
│  │                   ──► Pod:8080      │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  NodePort (ClusterIP + Node Access)                        │
│  ┌─────────────────────────────────────┐                   │
│  │  <NodeIP>:30080 ──► ClusterIP:80 ──► Pods              │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  LoadBalancer (NodePort + External LB)                     │
│  ┌─────────────────────────────────────┐                   │
│  │  <ExternalIP>:80 ──► NodePort ──► ClusterIP ──► Pods   │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  Service Port Flow:                                        │
│  ┌──────────────────────────────────────────────────┐     │
│  │                                                   │     │
│  │  External ──► nodePort ──► port ──► targetPort   │     │
│  │    :80         :30080      :80       :8080       │     │
│  │                                                   │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Selectors and Endpoints

### How Services Find Pods

Services use **label selectors** to find pods:

```yaml
# Service
spec:
  selector:
    app: my-app
    tier: frontend

# Pod (must match ALL labels)
metadata:
  labels:
    app: my-app
    tier: frontend
```

### Endpoints

Endpoints are automatically created/updated:

```bash
# View endpoints
k get endpoints my-service
# NAME         ENDPOINTS                         AGE
# my-service   10.244.0.5:8080,10.244.0.6:8080   5m

# Describe shows pod IPs
k describe endpoints my-service
```

### No Matching Pods?

If selector doesn't match any pods:

```bash
k get endpoints my-service
# NAME         ENDPOINTS   AGE
# my-service   <none>      5m
```

---

## Headless Services

For direct pod discovery without load balancing:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: headless-svc
spec:
  clusterIP: None          # Makes it headless
  selector:
    app: my-app
  ports:
  - port: 80
```

DNS returns all pod IPs instead of the Service IP:

```bash
# Returns multiple A records (one per pod)
nslookup headless-svc.default.svc.cluster.local
```

Use cases: StatefulSets, databases, peer discovery.

---

## Multi-Port Services

```yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-port
spec:
  selector:
    app: my-app
  ports:
  - name: http           # Name required for multi-port
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
```

---

## Session Affinity

Route same client to same pod:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sticky-service
spec:
  selector:
    app: my-app
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  ports:
  - port: 80
```

---

## Quick Reference

```bash
# Create Service
k expose deployment NAME --port=80 --target-port=8080
k expose deployment NAME --type=NodePort --port=80
k expose deployment NAME --type=LoadBalancer --port=80

# View Services
k get svc
k describe svc NAME

# View Endpoints
k get endpoints NAME
k get ep NAME

# Debug DNS
k run tmp --image=busybox --rm -it --restart=Never -- nslookup my-service

# Test connectivity
k run tmp --image=busybox --rm -it --restart=Never -- wget -qO- my-service:80
```

---

## Did You Know?

- **kube-proxy doesn't actually proxy traffic.** Despite its name, it configures iptables/IPVS rules. Traffic flows directly from source to destination pod.

- **Services exist cluster-wide even though they're namespaced.** The DNS name includes namespace, but the underlying ClusterIP works across namespaces.

- **NodePort uses ALL nodes.** Even nodes without the target pods will forward traffic to the correct pod.

- **The port range 30000-32767** is configurable via kube-apiserver's `--service-node-port-range` flag.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Selector doesn't match pod labels | Service has no endpoints | `k get ep` to verify, fix labels |
| Wrong targetPort | Connection refused | Match container's listening port |
| Using pod IP instead of Service | Breaks when pod restarts | Always use Service name/IP |
| Forgetting namespace in DNS | Can't reach service | Use `svc.namespace` or full FQDN |
| NodePort without firewall rule | Can't access from outside | Open node port in cloud firewall |

---

## Quiz

1. **What's the difference between `port` and `targetPort` in a Service?**
   <details>
   <summary>Answer</summary>
   `port` is the Service's port (what clients connect to). `targetPort` is the container's port (where traffic is forwarded). Example: Service listens on 80, forwards to container's 8080.
   </details>

2. **How do you find out which pods a Service is routing to?**
   <details>
   <summary>Answer</summary>
   `kubectl get endpoints <service-name>` shows the pod IPs and ports that the Service routes to.
   </details>

3. **What happens if a Service's selector matches no pods?**
   <details>
   <summary>Answer</summary>
   The Service exists but has no endpoints. Connections will fail. `kubectl get endpoints` will show `<none>`.
   </details>

4. **How can pods in namespace A access a Service in namespace B?**
   <details>
   <summary>Answer</summary>
   Use the DNS name with namespace: `service-name.namespace-b` or full FQDN `service-name.namespace-b.svc.cluster.local`.
   </details>

---

## Hands-On Exercise

**Task**: Create and test different Service types.

**Setup:**
```bash
# Create a deployment
k create deployment web --image=nginx --replicas=3

# Wait for pods
k wait --for=condition=Ready pod -l app=web --timeout=60s
```

**Part 1: ClusterIP Service**
```bash
# Create ClusterIP service
k expose deployment web --port=80 --target-port=80

# Verify endpoints
k get endpoints web

# Test from within cluster
k run test --image=busybox --rm -it --restart=Never -- wget -qO- web:80

# Check DNS
k run test --image=busybox --rm -it --restart=Never -- nslookup web.default.svc.cluster.local
```

**Part 2: NodePort Service**
```bash
# Delete ClusterIP service
k delete svc web

# Create NodePort service
k expose deployment web --type=NodePort --port=80 --target-port=80

# Get assigned NodePort
k get svc web -o jsonpath='{.spec.ports[0].nodePort}'
echo

# Test (if you have node access)
# curl http://<node-ip>:<nodeport>
```

**Part 3: Debug No Endpoints**
```bash
# Create service with wrong selector
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: broken-svc
spec:
  selector:
    app: wrong-label
  ports:
  - port: 80
EOF

# Check endpoints (should be empty)
k get endpoints broken-svc

# Fix by patching selector
k patch svc broken-svc -p '{"spec":{"selector":{"app":"web"}}}'

# Verify endpoints now exist
k get endpoints broken-svc
```

**Cleanup:**
```bash
k delete deployment web
k delete svc web broken-svc
```

---

## Practice Drills

### Drill 1: Create ClusterIP Service (Target: 1 minute)

```bash
k create deployment drill1 --image=nginx
k expose deployment drill1 --port=80
k get svc drill1
k get ep drill1
k delete deploy drill1 svc drill1
```

### Drill 2: Create NodePort Service (Target: 2 minutes)

```bash
k create deployment drill2 --image=nginx
k expose deployment drill2 --type=NodePort --port=80 --target-port=80

# Get NodePort
k get svc drill2 -o jsonpath='{.spec.ports[0].nodePort}'
echo

k delete deploy drill2 svc drill2
```

### Drill 3: Test DNS Resolution (Target: 2 minutes)

```bash
k create deployment drill3 --image=nginx
k expose deployment drill3 --port=80

# Test DNS
k run dns-test --image=busybox --rm -it --restart=Never -- nslookup drill3

k delete deploy drill3 svc drill3
```

### Drill 4: Service with Named Port (Target: 2 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: drill4
spec:
  selector:
    app: drill4
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: metrics
    port: 9090
    targetPort: 9090
---
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
EOF

k get svc drill4
k get ep drill4
k delete deploy drill4 svc drill4
```

### Drill 5: Debug Service Connectivity (Target: 3 minutes)

```bash
# Create deployment and broken service
k create deployment drill5 --image=nginx
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: drill5
spec:
  selector:
    app: wrong
  ports:
  - port: 80
EOF

# Debug
k get ep drill5                        # No endpoints
k get pods --show-labels               # Check pod labels
k describe svc drill5 | grep Selector  # Check service selector

# Fix
k patch svc drill5 -p '{"spec":{"selector":{"app":"drill5"}}}'
k get ep drill5                        # Should now have endpoints

k delete deploy drill5 svc drill5
```

### Drill 6: Cross-Namespace Service Access (Target: 3 minutes)

```bash
# Create namespace and service
k create ns drill6
k create deployment drill6-app --image=nginx -n drill6
k expose deployment drill6-app --port=80 -n drill6

# Access from default namespace
k run test --image=busybox --rm -it --restart=Never -- wget -qO- drill6-app.drill6:80

k delete ns drill6
```

---

## Next Module

[Module 5.2: Ingress](../module-5.2-ingress/) - HTTP routing and TLS termination.
