---
title: "Module 3.2: Endpoints & EndpointSlices"
slug: k8s/cka/part3-services-networking/module-3.2-endpoints
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Understanding service mechanics
>
> **Time to Complete**: 30-40 minutes
>
> **Prerequisites**: Module 3.1 (Services)

---

## Why This Module Matters

When you create a Service, Kubernetes automatically creates an Endpoints object that tracks which pod IPs should receive traffic. Understanding endpoints is crucial for debugging service issues—when a service has no endpoints, traffic goes nowhere.

The CKA exam tests your ability to troubleshoot services, and endpoint inspection is your primary debugging tool. You'll also encounter EndpointSlices, the newer, more scalable version of Endpoints.

> **The Phone Book Analogy**
>
> If a Service is a phone number (stable), Endpoints are the phone book entries that map that number to actual people (pods). When you call the number, the phone system looks up who's available in the book and connects you. Kubernetes does the same—the Service IP is looked up in Endpoints to find available pod IPs.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand how Endpoints connect Services to Pods
- Debug services by inspecting endpoints
- Create manual endpoints for external services
- Understand EndpointSlices and their benefits
- Handle headless services and their unique endpoint behavior

---

## Did You Know?

- **Endpoints can be huge**: In clusters with thousands of pods, a single Endpoints object can contain thousands of IP addresses. This caused performance issues, leading to EndpointSlices.

- **EndpointSlices are the future**: Since Kubernetes 1.21, EndpointSlices are the default. Each slice holds up to 100 endpoints, making updates much more efficient.

- **Controllers watch endpoints**: Many controllers (like Ingress controllers) watch Endpoints to know where to route traffic. When endpoints change, routing tables update automatically.

---

## Part 1: Endpoints Fundamentals

### 1.1 What Are Endpoints?

Endpoints are the glue between Services and Pods:

```
┌────────────────────────────────────────────────────────────────┐
│                   Service → Endpoints → Pods                    │
│                                                                 │
│   ┌──────────────────┐    ┌──────────────────┐                │
│   │    Service       │    │    Endpoints     │                │
│   │    web-svc       │    │    web-svc       │                │
│   │                  │    │                  │                │
│   │  selector:       │───►│  subsets:        │                │
│   │    app: web      │    │  - addresses:    │                │
│   │                  │    │    - 10.244.1.5  │───► Pod 1      │
│   │  ports:          │    │    - 10.244.2.8  │───► Pod 2      │
│   │  - port: 80      │    │    - 10.244.1.12 │───► Pod 3      │
│   │                  │    │    ports:        │                │
│   │                  │    │    - port: 8080  │                │
│   └──────────────────┘    └──────────────────┘                │
│                                                                 │
│   Endpoints auto-created and updated by endpoint controller    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Endpoint Lifecycle

```
┌────────────────────────────────────────────────────────────────┐
│                   Endpoint Controller                           │
│                                                                 │
│   Watches: Pods and Services                                   │
│   Updates: Endpoints objects                                   │
│                                                                 │
│   Pod Created (label: app=web)                                 │
│       │                                                         │
│       ▼                                                         │
│   Controller finds Service with selector app=web               │
│       │                                                         │
│       ▼                                                         │
│   Adds Pod IP to Service's Endpoints                           │
│                                                                 │
│   Pod Deleted or Fails Readiness                               │
│       │                                                         │
│       ▼                                                         │
│   Removes Pod IP from Endpoints                                │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Viewing Endpoints

```bash
# List all endpoints
k get endpoints
k get ep                    # Short form

# Get specific endpoint
k get endpoints web-svc

# Detailed view
k describe endpoints web-svc

# Get endpoints as YAML
k get endpoints web-svc -o yaml

# Wide output with pod IPs
k get endpoints -o wide
```

### 1.4 Endpoint Structure

```yaml
# What an Endpoints object looks like
apiVersion: v1
kind: Endpoints
metadata:
  name: web-svc           # Must match Service name
  namespace: default
subsets:
- addresses:              # Ready pod IPs
  - ip: 10.244.1.5
    nodeName: worker-1
    targetRef:
      kind: Pod
      name: web-abc123
      namespace: default
  - ip: 10.244.2.8
    nodeName: worker-2
    targetRef:
      kind: Pod
      name: web-def456
      namespace: default
  notReadyAddresses:      # Pods not passing readiness probe
  - ip: 10.244.1.12
    nodeName: worker-1
    targetRef:
      kind: Pod
      name: web-ghi789
      namespace: default
  ports:
  - port: 8080
    protocol: TCP
```

---

## Part 2: Debugging with Endpoints

### 2.1 No Endpoints = No Traffic

```bash
# Service exists but has no endpoints
k get svc web-svc
# NAME      TYPE        CLUSTER-IP     PORT(S)
# web-svc   ClusterIP   10.96.45.123   80/TCP

k get endpoints web-svc
# NAME      ENDPOINTS   AGE
# web-svc   <none>      5m     ← Problem!
```

### 2.2 Common Causes of Missing Endpoints

| Symptom | Cause | Debug Command | Solution |
|---------|-------|---------------|----------|
| `<none>` endpoints | No pods match selector | `k get pods --show-labels` | Fix selector or pod labels |
| `<none>` endpoints | Pods not running | `k get pods` | Fix pod issues |
| `<none>` endpoints | Pods in wrong namespace | `k get pods -A` | Check namespace |
| Partial endpoints | Some pods not ready | `k describe endpoints` | Check readiness probes |

### 2.3 Debugging Workflow

```bash
# Step 1: Check if endpoints exist
k get endpoints web-svc
# If <none>, proceed to step 2

# Step 2: Check service selector
k get svc web-svc -o yaml | grep -A5 selector
# selector:
#   app: web

# Step 3: Find pods with matching labels
k get pods --selector=app=web
# Should list pods backing the service

# Step 4: If no pods found, check what labels pods have
k get pods --show-labels
# Compare with service selector

# Step 5: If pods exist but not in endpoints, check pod status
k get pods
# Look for pods that aren't Running

# Step 6: Check for readiness probe failures
k describe pod <pod-name> | grep -A10 Readiness
```

### 2.4 Endpoints with NotReady Pods

```bash
# Describe shows both ready and not-ready addresses
k describe endpoints web-svc

# Output:
# Name:         web-svc
# Subsets:
#   Addresses:          10.244.1.5,10.244.2.8
#   NotReadyAddresses:  10.244.1.12
#   Ports:
#     Name     Port  Protocol
#     ----     ----  --------
#     <unset>  8080  TCP
```

Pods in `NotReadyAddresses` are **not** receiving traffic.

---

## Part 3: Manual Endpoints

### 3.1 When to Use Manual Endpoints

Create endpoints manually when pointing to:
- External databases outside Kubernetes
- Services in other clusters
- IP-based resources that aren't pods

### 3.2 Creating Manual Endpoints

```yaml
# Step 1: Create service WITHOUT selector
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  ports:
  - port: 5432
    targetPort: 5432
  # No selector! This is intentional.
---
# Step 2: Create Endpoints with same name
apiVersion: v1
kind: Endpoints
metadata:
  name: external-db     # Must match service name exactly
subsets:
- addresses:
  - ip: 192.168.1.100   # External database IP
  - ip: 192.168.1.101   # Backup database IP
  ports:
  - port: 5432
```

```bash
# Apply both
k apply -f external-db.yaml

# Verify
k get svc,endpoints external-db

# Now pods can reach external DB via:
# external-db.default.svc.cluster.local:5432
```

### 3.3 Manual Endpoints Use Cases

```yaml
# Example: External API endpoint
apiVersion: v1
kind: Service
metadata:
  name: external-api
spec:
  ports:
  - port: 443
---
apiVersion: v1
kind: Endpoints
metadata:
  name: external-api
subsets:
- addresses:
  - ip: 52.84.123.45     # External API server
  ports:
  - port: 443
```

---

## Part 4: EndpointSlices

### 4.1 Why EndpointSlices?

```
┌────────────────────────────────────────────────────────────────┐
│                   Endpoints Problem                             │
│                                                                 │
│   Large Service with 5000 pods                                 │
│                                                                 │
│   Single Endpoints object:                                     │
│   - Contains all 5000 IPs                                      │
│   - Any pod change = entire object update                      │
│   - Large payload sent to all watchers                         │
│   - API server and etcd strain                                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   EndpointSlices Solution                       │
│                                                                 │
│   Same 5000 pods split across 50 slices                        │
│                                                                 │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐      ┌─────────┐        │
│   │ Slice 1 │ │ Slice 2 │ │ Slice 3 │ ...  │Slice 50 │        │
│   │ 100 IPs │ │ 100 IPs │ │ 100 IPs │      │ 100 IPs │        │
│   └─────────┘ └─────────┘ └─────────┘      └─────────┘        │
│                                                                 │
│   Pod change = update only affected slice                      │
│   Small payload, minimal API server load                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 EndpointSlice Structure

```yaml
# What an EndpointSlice looks like
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: web-svc-abc12      # Auto-generated name
  labels:
    kubernetes.io/service-name: web-svc
addressType: IPv4
ports:
- name: ""
  port: 8080
  protocol: TCP
endpoints:
- addresses:
  - 10.244.1.5
  conditions:
    ready: true
    serving: true
    terminating: false
  nodeName: worker-1
  targetRef:
    kind: Pod
    name: web-abc123
    namespace: default
- addresses:
  - 10.244.2.8
  conditions:
    ready: true
  nodeName: worker-2
```

### 4.3 Viewing EndpointSlices

```bash
# List all EndpointSlices
k get endpointslices
k get eps                   # Short form (might conflict with endpoints)

# Get EndpointSlices for a service
k get endpointslices -l kubernetes.io/service-name=web-svc

# Detailed view
k describe endpointslice web-svc-abc12

# Get as YAML
k get endpointslice web-svc-abc12 -o yaml
```

### 4.4 Endpoints vs EndpointSlices Comparison

| Aspect | Endpoints | EndpointSlices |
|--------|-----------|----------------|
| Max entries | Unlimited (but problematic) | 100 per slice |
| Update scope | Entire object | Single slice |
| API version | v1 | discovery.k8s.io/v1 |
| Default since | Always | Kubernetes 1.21 |
| Dual-stack support | Limited | Full IPv4/IPv6 |
| Topology hints | No | Yes |

---

## Part 5: Headless Services

### 5.1 What Is a Headless Service?

A headless service has no ClusterIP. DNS returns pod IPs directly.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: headless-svc
spec:
  clusterIP: None          # This makes it headless
  selector:
    app: web
  ports:
  - port: 80
```

### 5.2 Headless Service Behavior

```
┌────────────────────────────────────────────────────────────────┐
│                   Regular vs Headless Service                   │
│                                                                 │
│   Regular Service (ClusterIP: 10.96.45.123)                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  DNS: web-svc.default.svc → 10.96.45.123 (Service IP)   │  │
│   │  Client → Service IP → kube-proxy → random Pod          │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   Headless Service (clusterIP: None)                           │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  DNS: web-svc.default.svc →                             │  │
│   │       10.244.1.5 (Pod 1)                                │  │
│   │       10.244.2.8 (Pod 2)                                │  │
│   │       10.244.1.12 (Pod 3)                               │  │
│   │  Client gets ALL pod IPs, chooses one itself            │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 Headless Service Use Cases

| Use Case | Why Headless? |
|----------|---------------|
| StatefulSets | Need to address specific pods (pod-0, pod-1) |
| Client-side load balancing | Client needs all IPs to implement custom balancing |
| Service discovery | Discover all backend instances |
| Database clusters | Need direct connection to specific node |

### 5.4 Headless Service Endpoints

```bash
# Endpoints still track pods
k get endpoints headless-svc
# NAME           ENDPOINTS
# headless-svc   10.244.1.5,10.244.2.8,10.244.1.12

# DNS returns multiple A records
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-svc

# Output:
# Name:    headless-svc.default.svc.cluster.local
# Address: 10.244.1.5
# Address: 10.244.2.8
# Address: 10.244.1.12
```

---

## Part 6: Service Topology and Topology Hints

### 6.1 Topology-Aware Routing

EndpointSlices support topology hints for zone-aware routing:

```yaml
# EndpointSlice with hints
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: web-svc-abc12
endpoints:
- addresses:
  - 10.244.1.5
  zone: us-east-1a          # Pod is in this zone
  hints:
    forZones:
    - name: us-east-1a      # Prefer traffic from same zone
```

### 6.2 Enabling Topology-Aware Hints

```yaml
# Service with topology hints
apiVersion: v1
kind: Service
metadata:
  name: web-svc
  annotations:
    service.kubernetes.io/topology-mode: Auto   # Enable hints
spec:
  selector:
    app: web
  ports:
  - port: 80
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Wrong endpoint name | Endpoints not associated with service | Name must exactly match service name |
| Selector typo | No endpoints | Double-check label selectors |
| Missing targetRef | Can't trace endpoint to pod | Include targetRef in manual endpoints |
| Ignoring NotReadyAddresses | Think pods are healthy | Check describe output for not-ready |
| Confusing endpoints/endpointslices | Get wrong data | Use both commands for debugging |

---

## Quiz

1. **Why might a service show `<none>` for endpoints?**
   <details>
   <summary>Answer</summary>
   The service's selector doesn't match any running pods' labels, OR no pods with matching labels are in Running state.
   </details>

2. **How do you create endpoints for an external service?**
   <details>
   <summary>Answer</summary>
   1. Create a Service without a selector
   2. Create an Endpoints object with the same name as the service
   3. Add the external IP addresses to the Endpoints subsets
   </details>

3. **What's the difference between `addresses` and `notReadyAddresses` in endpoints?**
   <details>
   <summary>Answer</summary>
   `addresses` contains pod IPs that are ready and receiving traffic. `notReadyAddresses` contains pod IPs that aren't passing their readiness probe and won't receive traffic.
   </details>

4. **Why were EndpointSlices introduced?**
   <details>
   <summary>Answer</summary>
   To handle large services better. A single Endpoints object for thousands of pods caused performance issues. EndpointSlices split endpoints into chunks of 100, so updates only affect one slice.
   </details>

5. **What makes a service "headless" and what's special about its endpoints?**
   <details>
   <summary>Answer</summary>
   Setting `clusterIP: None` makes a service headless. Its endpoints are returned directly via DNS (multiple A records) instead of through a virtual ClusterIP.
   </details>

---

## Hands-On Exercise

**Task**: Debug a service with endpoint issues.

**Steps**:

1. **Create a deployment**:
```bash
k create deployment web --image=nginx --replicas=3
```

2. **Create a service with wrong selector**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: broken-service
spec:
  selector:
    app: webapp          # Wrong! Should be "web"
  ports:
  - port: 80
EOF
```

3. **Observe the problem**:
```bash
k get endpoints broken-service
# Shows: <none>
```

4. **Debug the issue**:
```bash
# Check what selector the service has
k get svc broken-service -o yaml | grep -A2 selector

# Check what labels the pods have
k get pods --show-labels

# Find the mismatch!
```

5. **Fix the service**:
```bash
k delete svc broken-service
k expose deployment web --port=80 --name=broken-service
```

6. **Verify endpoints exist**:
```bash
k get endpoints broken-service
# Should show 3 pod IPs
```

7. **Check EndpointSlices too**:
```bash
k get endpointslices -l kubernetes.io/service-name=broken-service
```

8. **Test with a headless service**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless-web
spec:
  clusterIP: None
  selector:
    app: web
  ports:
  - port: 80
EOF

# Check DNS returns multiple IPs
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-web
```

9. **Cleanup**:
```bash
k delete deployment web
k delete svc broken-service headless-web
```

**Success Criteria**:
- [ ] Can identify missing endpoints
- [ ] Can debug selector mismatches
- [ ] Understand endpoints vs endpointslices
- [ ] Can create headless services
- [ ] Understand DNS behavior differences

---

## Practice Drills

### Drill 1: Endpoint Inspection (Target: 2 minutes)

```bash
# Setup
k create deployment drill --image=nginx --replicas=2
k expose deployment drill --port=80

# Check endpoints
k get endpoints drill

# Get detailed endpoint info
k describe endpoints drill

# Get as YAML (see pod IPs)
k get endpoints drill -o yaml

# Check EndpointSlices
k get endpointslices -l kubernetes.io/service-name=drill

# Cleanup
k delete deployment drill
k delete svc drill
```

### Drill 2: Debug Missing Endpoints (Target: 3 minutes)

```bash
# Create deployment
k create deployment debug-app --image=nginx

# Create service with typo in selector
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: debug-svc
spec:
  selector:
    app: debug-apps    # Typo: extra 's'
  ports:
  - port: 80
EOF

# Observe problem
k get endpoints debug-svc
# <none>

# Debug
k get pods --show-labels
k get svc debug-svc -o jsonpath='{.spec.selector}'

# Fix
k delete svc debug-svc
k expose deployment debug-app --port=80 --name=debug-svc

# Verify
k get endpoints debug-svc

# Cleanup
k delete deployment debug-app
k delete svc debug-svc
```

### Drill 3: Manual Endpoints (Target: 4 minutes)

```bash
# Create service without selector
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: external-svc
spec:
  ports:
  - port: 80
EOF

# Check - no endpoints yet
k get endpoints external-svc

# Create manual endpoints
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Endpoints
metadata:
  name: external-svc
subsets:
- addresses:
  - ip: 1.2.3.4
  - ip: 5.6.7.8
  ports:
  - port: 80
EOF

# Verify endpoints
k get endpoints external-svc
k describe endpoints external-svc

# Cleanup
k delete svc external-svc
k delete endpoints external-svc
```

### Drill 4: Headless Service (Target: 3 minutes)

```bash
# Create deployment
k create deployment headless-test --image=nginx --replicas=3

# Create headless service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless
spec:
  clusterIP: None
  selector:
    app: headless-test
  ports:
  - port: 80
EOF

# Verify no ClusterIP
k get svc headless
# CLUSTER-IP should be "None"

# Check endpoints (still exist!)
k get endpoints headless

# Test DNS - should return multiple IPs
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless

# Cleanup
k delete deployment headless-test
k delete svc headless
```

### Drill 5: EndpointSlice Analysis (Target: 3 minutes)

```bash
# Create deployment
k create deployment slice-test --image=nginx --replicas=3
k expose deployment slice-test --port=80

# Get EndpointSlice name
k get endpointslices -l kubernetes.io/service-name=slice-test

# Describe it
SLICE_NAME=$(k get endpointslices -l kubernetes.io/service-name=slice-test -o jsonpath='{.items[0].metadata.name}')
k describe endpointslice $SLICE_NAME

# Get YAML
k get endpointslice $SLICE_NAME -o yaml

# Note the endpoints array with conditions

# Cleanup
k delete deployment slice-test
k delete svc slice-test
```

### Drill 6: Readiness and Endpoints (Target: 4 minutes)

```bash
# Create pod with failing readiness probe
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: unready-pod
  labels:
    app: unready
spec:
  containers:
  - name: nginx
    image: nginx
    readinessProbe:
      httpGet:
        path: /nonexistent
        port: 80
      initialDelaySeconds: 1
      periodSeconds: 2
EOF

# Create service
k expose pod unready-pod --port=80 --name=unready-svc

# Wait a moment, then check endpoints
sleep 10
k get endpoints unready-svc
# Should be <none> or empty!

# Check why
k describe endpoints unready-svc
# Look for notReadyAddresses

# Check pod status
k get pod unready-pod
# Not ready due to probe

# Cleanup
k delete pod unready-pod
k delete svc unready-svc
```

### Drill 7: Scale and Watch Endpoints (Target: 3 minutes)

```bash
# Create deployment
k create deployment watch-test --image=nginx --replicas=1
k expose deployment watch-test --port=80

# Watch endpoints in terminal 1 (or background)
k get endpoints watch-test -w &

# Scale up and observe endpoints change
k scale deployment watch-test --replicas=5
sleep 5

# Scale down
k scale deployment watch-test --replicas=2
sleep 5

# Bring watch to foreground and stop
fg
# Ctrl+C

# Cleanup
k delete deployment watch-test
k delete svc watch-test
```

### Drill 8: Challenge - Complete Endpoint Workflow

Without looking at solutions:

1. Create deployment `ep-challenge` with 3 replicas of nginx
2. Create a service that intentionally has wrong selector
3. Diagnose why endpoints are empty
4. Fix the service
5. Create a headless service for same deployment
6. Verify DNS returns 3 IPs for headless service
7. Create manual endpoints for IP 10.0.0.1
8. Cleanup everything

```bash
# YOUR TASK: Complete in under 6 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. Create deployment
k create deployment ep-challenge --image=nginx --replicas=3

# 2. Create service with wrong selector
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: wrong-svc
spec:
  selector:
    app: wrong
  ports:
  - port: 80
EOF

# 3. Diagnose
k get endpoints wrong-svc
# <none>
k get pods --show-labels
# Labels show app=ep-challenge, not app=wrong

# 4. Fix
k delete svc wrong-svc
k expose deployment ep-challenge --port=80 --name=fixed-svc
k get endpoints fixed-svc
# Shows 3 IPs

# 5. Create headless service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless-challenge
spec:
  clusterIP: None
  selector:
    app: ep-challenge
  ports:
  - port: 80
EOF

# 6. Verify DNS
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-challenge
# Should show 3 IPs

# 7. Manual endpoints
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: manual-svc
spec:
  ports:
  - port: 80
---
apiVersion: v1
kind: Endpoints
metadata:
  name: manual-svc
subsets:
- addresses:
  - ip: 10.0.0.1
  ports:
  - port: 80
EOF
k get endpoints manual-svc

# 8. Cleanup
k delete deployment ep-challenge
k delete svc fixed-svc headless-challenge manual-svc
k delete endpoints manual-svc
```

</details>

---

## Next Module

[Module 3.3: DNS & CoreDNS](../module-3.3-dns/) - Deep-dive into Kubernetes DNS and service discovery.
