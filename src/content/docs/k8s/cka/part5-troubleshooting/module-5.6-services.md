---
title: "Module 5.6: Service Troubleshooting"
slug: k8s/cka/part5-troubleshooting/module-5.6-services
sidebar:
  order: 7
lab:
  id: cka-5.6-services
  url: https://killercoda.com/kubedojo/scenario/cka-5.6-services
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical for application access
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 5.5 (Network Troubleshooting), Module 3.1-3.4 (Services)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Diagnose** service connectivity failures using the endpoint → selector → pod readiness chain
- **Fix** services with no endpoints by correcting label selectors, checking pod readiness, and verifying ports
- **Debug** NodePort and LoadBalancer services by checking external access, firewall rules, and cloud provider integration
- **Trace** a service request through kube-proxy rules to the backend pod

---

## Why This Module Matters

Services are how applications are exposed in Kubernetes - both internally and externally. When a service isn't working, applications become unreachable. Understanding the different service types and their failure modes is essential for keeping applications accessible.

> **The Reception Desk Analogy**
>
> A Kubernetes Service is like a reception desk. ClusterIP is an internal desk - only people inside the building can use it. NodePort opens a window to the street. LoadBalancer sets up a whole new public entrance. Ingress is like a lobby directory that routes people to different desks based on their request. Each has different ways to break.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Troubleshoot ClusterIP services
- Fix NodePort accessibility issues
- Diagnose LoadBalancer problems
- Debug Ingress configuration
- Identify kube-proxy issues

---

## Did You Know?

- **Service IPs are virtual**: ClusterIP addresses don't exist on any interface - they're just rules in iptables/IPVS
- **NodePort range**: Default is 30000-32767. You can change it with API server flag but rarely need to
- **LoadBalancer includes NodePort**: LoadBalancer services automatically get a ClusterIP AND NodePort
- **Headless services have no ClusterIP**: Setting `clusterIP: None` returns pod IPs directly in DNS

---

## Part 1: Service Architecture Review

### 1.1 Service Types

```
┌──────────────────────────────────────────────────────────────┐
│                    SERVICE TYPES                              │
│                                                               │
│   ClusterIP (default)                                         │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ Internal only, virtual IP, no external access       │    │
│   └─────────────────────────────────────────────────────┘    │
│                            ▲                                  │
│                            │ Builds on                        │
│   NodePort                 │                                  │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ ClusterIP + port on every node (30000-32767)        │    │
│   └─────────────────────────────────────────────────────┘    │
│                            ▲                                  │
│                            │ Builds on                        │
│   LoadBalancer             │                                  │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ ClusterIP + NodePort + cloud load balancer          │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
│   ExternalName                                                │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ DNS CNAME record, no proxy, just name resolution    │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 kube-proxy Role

```
┌──────────────────────────────────────────────────────────────┐
│                    KUBE-PROXY FUNCTION                        │
│                                                               │
│   Service Created                                             │
│        │                                                      │
│        ▼                                                      │
│   kube-proxy watches API server                              │
│        │                                                      │
│        ▼                                                      │
│   Programs rules on each node:                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ iptables mode: iptables -t nat rules                │    │
│   │ IPVS mode:    virtual servers in kernel             │    │
│   └─────────────────────────────────────────────────────┘    │
│        │                                                      │
│        ▼                                                      │
│   Traffic to ClusterIP → redirected to pod IPs              │
│                                                               │
│   If kube-proxy fails → Services stop working                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Part 2: ClusterIP Troubleshooting

### 2.1 ClusterIP Checklist

When a ClusterIP service isn't working:

```
┌──────────────────────────────────────────────────────────────┐
│               CLUSTERIP TROUBLESHOOTING                       │
│                                                               │
│   □ Service exists and has correct ports                     │
│   □ Endpoints exist (selector matches pods)                  │
│   □ Pods are in Ready state                                  │
│   □ Target port matches container port                       │
│   □ Pod is actually listening on the port                    │
│   □ kube-proxy is running on nodes                          │
│   □ No NetworkPolicy blocking traffic                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Step-by-Step Diagnosis

```bash
# 1. Check service exists
k get svc my-service
k describe svc my-service

# 2. Check endpoints (CRITICAL)
k get endpoints my-service
# No endpoints = problem with selector or pod readiness

# 3. Verify selector matches pods
k get svc my-service -o jsonpath='{.spec.selector}'
# Compare to:
k get pods --show-labels

# 4. Check pods are Ready
k get pods -l <selector>
# All should show Ready (e.g., 1/1)

# 5. Verify pod is listening on port
k exec <pod> -- netstat -tlnp
# Or: k exec <pod> -- ss -tlnp

# 6. Test directly to pod IP
k exec <client-pod> -- wget -qO- http://<pod-ip>:<container-port>
```

### 2.3 Common ClusterIP Issues

| Issue | Symptom | Check | Fix |
|-------|---------|-------|-----|
| No endpoints | Connection refused | `k get ep` | Fix selector or pod labels |
| Wrong targetPort | Timeout/refused | Compare port to container | Fix targetPort |
| Pod not Ready | Missing endpoints | `k get pods` | Fix readiness probe |
| App not listening | Direct pod access fails | `netstat` in container | Fix application |
| kube-proxy down | All services fail | kube-proxy pods | Restart kube-proxy |

### 2.4 Port Configuration Deep Dive

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: myapp
  ports:
  - port: 80          # Port clients use to access service
    targetPort: 8080  # Port on the pod/container
    protocol: TCP     # TCP (default) or UDP
    name: http        # Optional name
```

```bash
# Verify the mapping
k get svc my-service -o yaml | grep -A 5 ports:

# Check container is listening on targetPort
k exec <pod> -- sh -c 'netstat -tlnp 2>/dev/null || ss -tlnp'
```

---

## Part 3: NodePort Troubleshooting

### 3.1 NodePort Checklist

```
┌──────────────────────────────────────────────────────────────┐
│               NODEPORT TROUBLESHOOTING                        │
│                                                               │
│   All ClusterIP checks, plus:                                │
│                                                               │
│   □ NodePort is in valid range (30000-32767)                │
│   □ Node firewall allows the port                           │
│   □ Cloud security group allows the port                    │
│   □ Node is reachable on the port                          │
│   □ Testing with correct node IP                           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Testing NodePort

```bash
# Get NodePort value
k get svc my-service -o jsonpath='{.spec.ports[0].nodePort}'

# Get node IPs
k get nodes -o wide

# Test from outside cluster
curl http://<node-ip>:<nodeport>

# Test from inside cluster (should also work)
k exec <pod> -- wget -qO- http://<node-ip>:<nodeport>

# Test all nodes (NodePort works on any node)
for node_ip in $(k get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'); do
  curl -s --connect-timeout 2 http://${node_ip}:<nodeport> && echo "OK: $node_ip" || echo "FAIL: $node_ip"
done
```

### 3.3 Common NodePort Issues

| Issue | Symptom | Check | Fix |
|-------|---------|-------|-----|
| Firewall blocking | Timeout from external | `iptables -L -n` | Open port in firewall |
| Cloud SG blocking | Timeout from external | Cloud console | Add security group rule |
| Wrong node IP | Connection refused | `k get nodes -o wide` | Use correct IP (internal vs external) |
| Port conflict | Service create fails | `netstat -tlnp` on node | Use different nodePort |
| externalTrafficPolicy | Only some nodes work | Check policy | Set to Cluster or fix endpoints |

### 3.4 externalTrafficPolicy

```yaml
spec:
  type: NodePort
  externalTrafficPolicy: Local  # Only nodes with pods respond
  # vs
  externalTrafficPolicy: Cluster  # All nodes respond (default)
```

```bash
# Check current policy
k get svc my-service -o jsonpath='{.spec.externalTrafficPolicy}'

# With Local policy, check which nodes have pods
k get pods -l <selector> -o wide
# Only those node IPs will respond to NodePort
```

---

## Part 4: LoadBalancer Troubleshooting

### 4.1 LoadBalancer Requirements

```
┌──────────────────────────────────────────────────────────────┐
│             LOADBALANCER REQUIREMENTS                         │
│                                                               │
│   Cloud environment:                                          │
│   • Cloud controller manager running                         │
│   • Proper cloud credentials configured                      │
│   • Cloud provider supports LoadBalancer                     │
│                                                               │
│   On-premises:                                                │
│   • MetalLB or similar solution installed                   │
│   • IP address pool configured                               │
│                                                               │
│   Without these → LoadBalancer stays Pending forever        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Checking LoadBalancer Status

```bash
# Check if external IP is assigned
k get svc my-service
# EXTERNAL-IP column should show an IP, not <pending>

# Get detailed status
k describe svc my-service

# Check events for errors
k get events --field-selector involvedObject.name=my-service

# Test the LoadBalancer IP
curl http://<external-ip>:<port>
```

### 4.3 Common LoadBalancer Issues

| Issue | Symptom | Check | Fix |
|-------|---------|-------|-----|
| No cloud controller | Stays Pending | Check cloud-controller-manager | Install/configure CCM |
| Quota exceeded | Stays Pending | Cloud console | Request quota increase |
| Wrong annotations | LB misconfigured | Service annotations | Fix cloud-specific annotations |
| Security group | Can't reach LB | Cloud security rules | Open LB ports |
| MetalLB not installed | Stays Pending (bare metal) | Check MetalLB pods | Install MetalLB |

### 4.4 Debugging LoadBalancer in Cloud

```bash
# For AWS
k describe svc my-service | grep "LoadBalancer Ingress"
aws elb describe-load-balancers

# For GCP
k describe svc my-service
gcloud compute forwarding-rules list

# Check cloud controller manager logs
k -n kube-system logs -l component=cloud-controller-manager
```

---

## Part 5: Ingress Troubleshooting

### 5.1 Ingress Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  INGRESS FLOW                                 │
│                                                               │
│   External Request                                            │
│        │                                                      │
│        ▼                                                      │
│   Ingress Controller (nginx, traefik, etc.)                  │
│        │                                                      │
│        │ Reads Ingress resources                             │
│        ▼                                                      │
│   Matches host/path rules                                     │
│        │                                                      │
│        ▼                                                      │
│   Routes to backend Service                                   │
│        │                                                      │
│        ▼                                                      │
│   Pod                                                         │
│                                                               │
│   Ingress Controller missing → Ingress rules do nothing      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Ingress Troubleshooting Steps

```bash
# 1. Check Ingress Controller is running
k -n ingress-nginx get pods  # For nginx-ingress
# Or check your specific ingress controller namespace

# 2. Check Ingress resource exists
k get ingress my-ingress
k describe ingress my-ingress

# 3. Verify backend service exists
k get svc <backend-service>

# 4. Check Ingress events
k describe ingress my-ingress | grep -A 10 Events

# 5. Check Ingress Controller logs
k -n ingress-nginx logs -l app.kubernetes.io/name=ingress-nginx

# 6. Test with correct Host header
curl -H "Host: myapp.example.com" http://<ingress-ip>
```

### 5.3 Common Ingress Issues

| Issue | Symptom | Check | Fix |
|-------|---------|-------|-----|
| No Ingress Controller | 404 or nothing | Controller pods | Install Ingress Controller |
| Wrong ingressClassName | Rules ignored | `spec.ingressClassName` | Match controller class |
| Backend service missing | 503 error | `k get svc` | Create backend service |
| TLS secret missing | TLS errors | `k get secret` | Create TLS secret |
| Wrong host header | 404 | Test with -H flag | Use correct hostname |
| Path type mismatch | 404 on subpaths | Check pathType | Use Prefix or Exact |

### 5.4 Ingress Path Types

```yaml
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix   # /api, /api/, /api/v1 all match
      - path: /exact
        pathType: Exact    # Only /exact matches
      - path: /
        pathType: Prefix   # Catch-all
```

### 5.5 Testing Ingress

```bash
# Get Ingress IP/hostname
k get ingress my-ingress

# Test with specific host header
curl -v -H "Host: myapp.example.com" http://<ingress-ip>/path

# Test TLS
curl -v -H "Host: myapp.example.com" https://<ingress-ip>/path -k

# Check Ingress Controller configuration (nginx)
k -n ingress-nginx exec <controller-pod> -- cat /etc/nginx/nginx.conf | grep -A 20 "server_name myapp"
```

---

## Part 6: kube-proxy Troubleshooting

### 6.1 kube-proxy Modes

```
┌──────────────────────────────────────────────────────────────┐
│                 KUBE-PROXY MODES                              │
│                                                               │
│   iptables mode (default)                                     │
│   • Uses iptables rules for routing                          │
│   • Good for < 1000 services                                 │
│   • Check: iptables -t nat -L                                │
│                                                               │
│   IPVS mode                                                   │
│   • Uses kernel IPVS for load balancing                     │
│   • Better for many services                                 │
│   • Check: ipvsadm -Ln                                       │
│                                                               │
│   If kube-proxy fails → Service routing breaks               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Checking kube-proxy

```bash
# Check kube-proxy pods
k -n kube-system get pods -l k8s-app=kube-proxy

# Check kube-proxy logs
k -n kube-system logs -l k8s-app=kube-proxy

# Check kube-proxy config
k -n kube-system get configmap kube-proxy -o yaml

# Check iptables rules (on node)
sudo iptables -t nat -L KUBE-SERVICES | head -20

# Check IPVS (if using IPVS mode)
sudo ipvsadm -Ln
```

### 6.3 Common kube-proxy Issues

| Issue | Symptom | Check | Fix |
|-------|---------|-------|-----|
| Not running | All services fail | Check pods | Restart DaemonSet |
| Wrong mode | Unexpected behavior | ConfigMap | Reconfigure mode |
| Stale rules | Service changes not reflected | iptables on node | Restart kube-proxy |
| conntrack full | Random connection drops | dmesg for conntrack | Increase conntrack limit |

### 6.4 Fixing kube-proxy

```bash
# Restart kube-proxy pods
k -n kube-system rollout restart daemonset kube-proxy

# Check for errors in logs
k -n kube-system logs -l k8s-app=kube-proxy --since=5m | grep -i error

# Verify iptables rules exist for a service
sudo iptables -t nat -L KUBE-SERVICES | grep <service-cluster-ip>

# Force sync (delete and let kube-proxy recreate)
# This is disruptive - use carefully
k -n kube-system delete pod -l k8s-app=kube-proxy
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not checking endpoints first | Miss the real issue | Always start with `k get endpoints` |
| Confusing port vs targetPort | Wrong port configuration | port=service access, targetPort=container |
| Testing NodePort from wrong IP | Connection fails | Use node IP, not pod IP |
| Missing Ingress Controller | Ingress rules ignored | Verify controller is installed |
| Wrong ingressClassName | Rules not picked up | Match the controller's class name |
| Ignoring kube-proxy | Blame app or network | Check kube-proxy pods and logs |

---

## Quiz

### Q1: Service Without Endpoints
`k get svc nginx` shows ClusterIP, but `k get endpoints nginx` shows `<none>`. What's wrong?

<details>
<summary>Answer</summary>

The service selector doesn't match any **Ready** pods. Either:
1. No pods exist with matching labels
2. Pods exist but aren't Ready (failed readiness probe)
3. Selector in service is wrong

Debug:
```bash
k get svc nginx -o jsonpath='{.spec.selector}'
k get pods --show-labels | grep <expected-labels>
```

</details>

### Q2: NodePort Not Working
NodePort service created. `curl http://node:30080` times out from outside, but works from inside the cluster. Why?

<details>
<summary>Answer</summary>

A **firewall or security group** is blocking the NodePort from external access. Check:
- Node's iptables: `sudo iptables -L INPUT`
- Cloud security groups (AWS, GCP, Azure)
- Network ACLs

NodePort requires the port to be open on all nodes from the source network.

</details>

### Q3: LoadBalancer Pending
Service type LoadBalancer stays `<pending>` for EXTERNAL-IP. What do you check?

<details>
<summary>Answer</summary>

Check if cloud controller manager is running and configured:
```bash
k -n kube-system get pods | grep cloud-controller
k get events --field-selector involvedObject.name=<service>
```

If on-premises/bare-metal, you need MetalLB or similar:
```bash
k -n metallb-system get pods
```

No cloud integration = LoadBalancer stays pending.

</details>

### Q4: Ingress 404
Ingress is configured, but all requests return 404. What's the first thing to check?

<details>
<summary>Answer</summary>

Check if an **Ingress Controller is installed** and the Ingress has the correct **ingressClassName**:

```bash
# Check for ingress controller
k get pods -A | grep -i ingress

# Check Ingress class
k get ingress <name> -o yaml | grep ingressClassName

# See available classes
k get ingressclass
```

Without an Ingress Controller, Ingress resources do nothing.

</details>

### Q5: Port vs TargetPort
Service has `port: 80, targetPort: 3000`. Container runs on port 80. Will it work?

<details>
<summary>Answer</summary>

**No.** Traffic reaches the service on port 80, but gets forwarded to container port 3000, where nothing is listening.

Fix either:
1. Change `targetPort: 80` to match the container
2. Change the container to listen on 3000

</details>

### Q6: kube-proxy Mode
How do you check which mode kube-proxy is running in?

<details>
<summary>Answer</summary>

```bash
# Check ConfigMap
k -n kube-system get configmap kube-proxy -o yaml | grep mode

# Or check pod logs
k -n kube-system logs -l k8s-app=kube-proxy | grep "Using"

# Common modes: iptables (default), ipvs
```

</details>

---

## Hands-On Exercise: Service Troubleshooting Scenarios

### Scenario

Practice diagnosing and fixing service issues.

### Setup

```bash
# Create test namespace
k create ns service-lab

# Create a deployment
cat <<EOF | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: service-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
EOF
```

### Task 1: Create and Test ClusterIP Service

```bash
# Create service
k -n service-lab expose deployment web --port=80

# Create test pod
k -n service-lab run client --image=busybox:1.36 --command -- sleep 3600

# Test connectivity
k -n service-lab exec client -- wget -qO- http://web

# Check endpoints
k -n service-lab get endpoints web
```

### Task 2: Simulate Selector Mismatch

```bash
# Break the service
k -n service-lab patch svc web -p '{"spec":{"selector":{"app":"broken"}}}'

# Test (should fail)
k -n service-lab exec client -- wget -qO- --timeout=2 http://web

# Check endpoints (should be empty)
k -n service-lab get endpoints web

# Diagnose
k -n service-lab get svc web -o jsonpath='{.spec.selector}'
k -n service-lab get pods --show-labels

# Fix
k -n service-lab patch svc web -p '{"spec":{"selector":{"app":"web"}}}'

# Verify
k -n service-lab get endpoints web
k -n service-lab exec client -- wget -qO- --timeout=2 http://web
```

### Task 3: Create NodePort Service

```bash
# Create NodePort service
k -n service-lab expose deployment web --type=NodePort --name=web-nodeport --port=80

# Get NodePort
k -n service-lab get svc web-nodeport

# Get node IP
k get nodes -o wide

# Test from within cluster
k -n service-lab exec client -- wget -qO- --timeout=2 http://<node-ip>:<nodeport>
```

### Task 4: Wrong Port Configuration

```bash
# Create service with wrong targetPort
cat <<EOF | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: wrong-port
  namespace: service-lab
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080  # Wrong! nginx listens on 80
EOF

# Test (should fail)
k -n service-lab exec client -- wget -qO- --timeout=2 http://wrong-port

# Diagnose
k -n service-lab get endpoints wrong-port  # Has endpoints
k -n service-lab exec client -- wget -qO- --timeout=2 http://<pod-ip>:80  # Works
k -n service-lab exec client -- wget -qO- --timeout=2 http://<pod-ip>:8080  # Fails

# Fix
k -n service-lab patch svc wrong-port -p '{"spec":{"ports":[{"port":80,"targetPort":80}]}}'

# Verify
k -n service-lab exec client -- wget -qO- --timeout=2 http://wrong-port
```

### Success Criteria

- [ ] Created and tested ClusterIP service
- [ ] Identified and fixed selector mismatch
- [ ] Created and tested NodePort service
- [ ] Diagnosed and fixed wrong targetPort

### Cleanup

```bash
k delete ns service-lab
```

---

## Practice Drills

### Drill 1: Check Service Details (30 sec)
```bash
# Task: View service configuration
k get svc <service> -o yaml
```

### Drill 2: Check Endpoints (30 sec)
```bash
# Task: List endpoints for a service
k get endpoints <service>
k describe endpoints <service>
```

### Drill 3: Get NodePort Value (30 sec)
```bash
# Task: Find the NodePort of a service
k get svc <service> -o jsonpath='{.spec.ports[0].nodePort}'
```

### Drill 4: Test Service Connectivity (1 min)
```bash
# Task: Test HTTP to service
k exec <pod> -- wget -qO- --timeout=2 http://<service>
```

### Drill 5: Fix Selector Mismatch (2 min)
```bash
# Task: Update service selector
k patch svc <service> -p '{"spec":{"selector":{"app":"correct-label"}}}'
```

### Drill 6: Check Ingress Controller (1 min)
```bash
# Task: Verify Ingress Controller is running
k get pods -A | grep -i ingress
k get ingressclass
```

### Drill 7: Check kube-proxy (1 min)
```bash
# Task: Verify kube-proxy status
k -n kube-system get pods -l k8s-app=kube-proxy
k -n kube-system logs -l k8s-app=kube-proxy --tail=20
```

### Drill 8: Test Ingress with Host Header (1 min)
```bash
# Task: Test Ingress rule
curl -H "Host: <hostname>" http://<ingress-ip>
```

---

## Next Module

Continue to [Module 5.7: Logging & Monitoring](../module-5.7-logging-monitoring/) to learn how to use logs and metrics for troubleshooting.
