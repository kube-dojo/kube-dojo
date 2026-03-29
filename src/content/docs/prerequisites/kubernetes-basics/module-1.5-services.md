---
title: "Module 1.5: Services - Stable Networking"
slug: prerequisites/kubernetes-basics/module-1.5-services/
sidebar:
  order: 6
lab:
  id: "prereq-k8s-1.5-services"
  url: "https://killercoda.com/kubedojo/scenario/prereq-k8s-1.5-services"
  duration: "25 min"
  difficulty: "beginner"
  environment: "kubernetes"
---
> **Complexity**: `[MEDIUM]` - Essential networking concept
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 4 (Deployments)

---

## Why This Module Matters

Pods are ephemeral—they come and go, each with a different IP address. Services provide stable networking: a fixed IP and DNS name that routes to your Pods, no matter how many there are or how often they change.

---

## The Problem Services Solve

```
┌─────────────────────────────────────────────────────────────┐
│              WITHOUT SERVICES                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pod IPs change constantly:                                │
│                                                             │
│  Time 0:  [Pod: 10.1.0.5]                                  │
│  Time 1:  Pod crashes, recreated                           │
│  Time 2:  [Pod: 10.1.0.9]   ← Different IP!               │
│                                                             │
│  Problem: How do other apps find your Pod?                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│              WITH SERVICES                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Service: my-app.default.svc.cluster.local                 │
│           ClusterIP: 10.96.0.100 (stable!)                 │
│                    │                                        │
│           ┌────────┴────────┐                              │
│           ▼                 ▼                               │
│  [Pod: 10.1.0.5]   [Pod: 10.1.0.9]                        │
│                                                             │
│  Service routes to healthy pods, IPs don't matter          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Creating Services

### Imperative (Quick)

```bash
# Expose a deployment
kubectl expose deployment nginx --port=80

# With specific type
kubectl expose deployment nginx --port=80 --type=NodePort

# Check the service
kubectl get services
kubectl get svc              # Short form
```

### Declarative (Production)

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  selector:
    app: nginx               # Match pod labels
  ports:
  - port: 80                 # Service port
    targetPort: 80           # Container port
  type: ClusterIP            # Default type
```

```bash
kubectl apply -f service.yaml
```

---

## Service Types

### ClusterIP (Default)

Internal-only access within the cluster:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: internal-api
spec:
  type: ClusterIP            # Default, can omit
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080
```

```bash
# Access from within cluster only
curl http://internal-api:80
```

### NodePort

Exposes on every node's IP at a static port:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080          # Optional: 30000-32767
```

```bash
# Access from outside cluster
curl http://<node-ip>:30080
```

### LoadBalancer

Creates external load balancer (cloud environments):

```yaml
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
    targetPort: 80
```

```bash
# Get external IP (cloud only)
kubectl get svc web-lb
# EXTERNAL-IP column shows the load balancer IP
```

---

## Service Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE TYPES                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ClusterIP (Internal Only)                                 │
│  ┌─────────────────────────────────────┐                  │
│  │  ClusterIP:80 ──► Pod:8080          │                  │
│  │               ──► Pod:8080          │                  │
│  │  (Accessible only within cluster)   │                  │
│  └─────────────────────────────────────┘                  │
│                                                             │
│  NodePort (External via Node)                              │
│  ┌─────────────────────────────────────┐                  │
│  │  <NodeIP>:30080 ──► ClusterIP:80 ──► Pods             │
│  │  (Accessible from outside)          │                  │
│  └─────────────────────────────────────┘                  │
│                                                             │
│  LoadBalancer (Cloud External)                             │
│  ┌─────────────────────────────────────┐                  │
│  │  <ExternalIP>:80 ──► NodePort ──► ClusterIP ──► Pods  │
│  │  (Cloud provider manages LB)        │                  │
│  └─────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Discovery (DNS)

Kubernetes creates DNS entries for Services:

```
<service-name>.<namespace>.svc.cluster.local
```

```bash
# From any pod, you can reach:
curl nginx                           # Same namespace
curl nginx.default                   # Explicit namespace
curl nginx.default.svc               # More explicit
curl nginx.default.svc.cluster.local # Full FQDN
```

### Example

```bash
# Create deployment and service
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80

# Test DNS from another pod
kubectl run test --image=busybox --rm -it -- wget -qO- nginx
# Returns nginx HTML!

# Test with full DNS name
kubectl run test --image=busybox --rm -it -- nslookup nginx.default.svc.cluster.local
```

---

## Selectors: How Services Find Pods

Services use label selectors:

```yaml
# Service
spec:
  selector:
    app: nginx
    tier: frontend

# Pod (must match ALL labels)
metadata:
  labels:
    app: nginx
    tier: frontend
```

```bash
# Check what pods a service targets
kubectl get endpoints nginx
# Shows IP:Port of matched pods
```

---

## Port Mapping

```yaml
spec:
  ports:
  - port: 80           # Service port (what clients use)
    targetPort: 8080   # Container port (where app listens)
    protocol: TCP      # TCP (default) or UDP
```

```
┌─────────────────────────────────────────────────────────────┐
│  Client ──► Service:80 ──► Pod:8080                        │
│                │                 │                          │
│             "port"         "targetPort"                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Services use iptables or IPVS.** kube-proxy sets up rules that route Service IPs to Pod IPs. No actual proxy process handles each connection.

- **ClusterIP is virtual.** No network interface has this IP. It only exists in iptables rules.

- **NodePort uses ALL nodes.** Even nodes without target pods will route traffic correctly.

- **Services load balance randomly** by default. Each connection might hit a different pod.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Selector doesn't match pod labels | Service has no endpoints | Check `kubectl get endpoints` |
| Wrong targetPort | Connection refused | Match container's listening port |
| Using pod IP instead of service | Breaks when pod restarts | Always use service name |

---

## Quiz

1. **Why use Services instead of Pod IPs?**
   <details>
   <summary>Answer</summary>
   Pod IPs change when pods restart. Services provide a stable IP and DNS name that persist regardless of which pods are running. They also load balance across multiple pods.
   </details>

2. **What's the difference between ClusterIP and NodePort?**
   <details>
   <summary>Answer</summary>
   ClusterIP is only accessible within the cluster. NodePort exposes the service on every node's IP at a static port (30000-32767), making it accessible from outside the cluster.
   </details>

3. **How do Services find which Pods to route to?**
   <details>
   <summary>Answer</summary>
   Label selectors. The Service's `selector` field specifies labels. Only pods with matching labels receive traffic. Check `kubectl get endpoints` to see matched pods.
   </details>

4. **What DNS name can a pod use to reach a Service named "api" in namespace "backend"?**
   <details>
   <summary>Answer</summary>
   `api.backend`, `api.backend.svc`, or the full `api.backend.svc.cluster.local`. From the same namespace, just `api` works.
   </details>

---

## Hands-On Exercise

**Task**: Create a deployment and expose it via Service.

```bash
# 1. Create deployment
kubectl create deployment web --image=nginx --replicas=3

# 2. Expose as ClusterIP
kubectl expose deployment web --port=80

# 3. Check service
kubectl get svc web
kubectl get endpoints web

# 4. Test from within cluster
kubectl run test --image=busybox --rm -it -- wget -qO- web

# 5. Create NodePort service
kubectl expose deployment web --port=80 --type=NodePort --name=web-external

# 6. Get NodePort
kubectl get svc web-external
# Note the port in 30000-32767 range

# 7. Cleanup
kubectl delete deployment web
kubectl delete svc web web-external
```

**Success criteria**: Internal service works, endpoints show pod IPs.

---

## Summary

Services provide stable networking:

**Types**:
- ClusterIP - Internal only (default)
- NodePort - External via node port
- LoadBalancer - External via cloud LB

**Key concepts**:
- Selectors match pod labels
- DNS names for discovery
- Port mapping (port → targetPort)
- Endpoints show matched pods

**Commands**:
- `kubectl expose deployment NAME --port=PORT`
- `kubectl get svc`
- `kubectl get endpoints`

---

## Next Module

[Module 6: ConfigMaps and Secrets](module-1.6-configmaps-secrets/) - Managing configuration.
