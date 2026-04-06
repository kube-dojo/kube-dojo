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

> **Pause and predict**: If `kube-proxy` crashes on just a single node, how will that impact pods trying to access a ClusterIP service from that specific node versus other nodes?

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

> **Stop and think**: Why is it possible for a Pod to be in a Ready state, yet still fail the "Pod is actually listening on the port" check?

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

> **Pause and predict**: If you set `externalTrafficPolicy: Local` on a NodePort service, but a specific node has no pods for that service running on it, what happens when an external client hits that node's IP on the NodePort?

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

> **Stop and think**: How does an Ingress Controller routing HTTP traffic at Layer 7 differ fundamentally from a `type: LoadBalancer` Service routing traffic at Layer 4 when things go wrong?

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

### Q1: The Empty Endpoints List
You've just deployed a new backend API and created a ClusterIP service for it. When you run `k get svc backend-api`, the service has an IP, but `k get endpoints backend-api` returns `<none>`. Your frontend pods are throwing connection refused errors. What are the likely causes for this missing endpoint mapping?

<details>
<summary>Answer</summary>

When a service has no endpoints, it means the Endpoint controller couldn't find any pods that both match the service's label selector and are currently in a Ready state. This usually happens for three reasons: no pods have the exact labels specified in the service selector, the pods exist but are stuck in a non-Ready state (like CrashLoopBackOff or failing their readiness probes), or there's a typo in the service's selector configuration itself. Since services route traffic exclusively to Ready pods, even a single mismatched character in a label or a failing probe will result in an empty endpoints list, leading directly to connection refused errors for clients.

Debug:
```bash
k get svc nginx -o jsonpath='{.spec.selector}'
k get pods --show-labels | grep <expected-labels>
```

</details>

### Q2: The Internal-Only NodePort
Your team needs to access a temporary debug dashboard. You expose the deployment with a NodePort service on port 30080. You can successfully `curl http://<node-ip>:30080` from a pod inside the cluster, but when your developer tries to access that same URL from their local machine, the connection simply times out. Why is the service reachable internally but failing from the outside?

<details>
<summary>Answer</summary>

A timeout when accessing a NodePort from outside the cluster, while internal access works, almost universally points to a network firewall or security group blocking the traffic. When you hit the NodePort from inside the cluster, the traffic stays within the internal software-defined network, bypassing external boundary restrictions. However, external traffic must pass through your cloud provider's security groups, network ACLs, or the node's host-level firewall (like ufw or iptables) before it even reaches kube-proxy. If you haven't explicitly whitelisted the specific NodePort range (or the exact port like 30080) in these external firewalls, the packets are silently dropped, resulting in a timeout rather than an immediate connection refusal.

Check:
- Node's iptables: `sudo iptables -L INPUT`
- Cloud security groups (AWS, GCP, Azure)
- Network ACLs

NodePort requires the port to be open on all nodes from the source network.

</details>

### Q3: The Infinite Pending State
You are migrating an application from AWS EKS to your company's new bare-metal on-premises Kubernetes cluster. You apply the exact same manifest for a `type: LoadBalancer` service that worked perfectly in AWS. However, an hour later, `k get svc` still shows the EXTERNAL-IP stuck in `<pending>`. What is the architectural reason for this behavior?

<details>
<summary>Answer</summary>

The `<pending>` state occurs because Kubernetes itself does not natively provide network load balancers; it merely requests them from the underlying infrastructure provider. In a managed cloud environment like EKS, a Cloud Controller Manager intercepts this request and provisions an AWS ELB/NLB. On a bare-metal cluster, there is no underlying cloud provider to fulfill this request by default, so the service waits infinitely. To resolve this on-premises, you must install and configure a dedicated software load balancer controller, such as MetalLB, which will monitor for these services and assign them an IP address from a pre-configured local pool.

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

### Q4: The Confusing 404
You've carefully written an Ingress resource routing `myapp.example.com` to your backend service. The DNS points to your cluster's load balancer IP. However, when you visit the URL, you get an immediate `404 Not Found` error. You've verified the backend pods are running and the Service is correctly selecting them. What configuration mismatch is likely causing the Ingress controller to drop the traffic?

<details>
<summary>Answer</summary>

A 404 error from an Ingress endpoint means the traffic successfully reached an Ingress Controller, but the controller didn't know what to do with the request because it didn't find a matching routing rule. This most commonly happens because the `ingressClassName` specified in your Ingress resource doesn't match the class monitored by the running controller, causing the controller to completely ignore your resource. Another frequent cause is a mismatch in the `Host` header, where the domain name the client is requesting doesn't exactly match the `host` field defined in the Ingress rules. Finally, it could be a missing controller entirely, but a quick 404 usually implies a web server (like Nginx) is active but lacks the specific server block configuration.

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

### Q5: The Misaligned Ports
A developer asks for your help with a failing deployment. They have an Nginx container configured to listen on port 80. Their Service definition has `port: 80` and `targetPort: 3000`. When they try to curl the service, the connection times out. Why is this specific configuration failing to deliver traffic to the application?

<details>
<summary>Answer</summary>

This configuration fails because of a mismatch between where the Service expects to send traffic and where the application is actually listening. The `port` field defines the virtual port exposed by the Service itself, while the `targetPort` dictates the actual port on the pod where kube-proxy will forward the traffic. In this scenario, requests arrive at the Service on port 80, and are then forwarded to port 3000 on the pod's IP. Since the Nginx container is only listening on port 80, the pod's network stack rejects the traffic on port 3000, resulting in a connection failure despite the pods being healthy and selected correctly.

Fix either:
1. Change `targetPort: 80` to match the container
2. Change the container to listen on 3000

</details>

### Q6: Verifying Routing Mechanisms
You are auditing a cluster that recently experienced scaling issues, and you suspect the routing performance is degrading because of an excessive number of iptables rules. You want to verify if the cluster administrators migrated kube-proxy to use the more performant IPVS mode. How do you confirm the current operational mode of kube-proxy?

<details>
<summary>Answer</summary>

To confirm the operational mode of kube-proxy, you need to inspect its active configuration or startup logs, as this setting dictates how the daemon translates Service IPs into actual routing rules on each node. The most direct method is to examine the `kube-proxy` ConfigMap in the `kube-system` namespace, which serves as the source of truth for the daemonset configuration and will explicitly declare the mode. Alternatively, you can view the logs of any running kube-proxy pod, which will log a startup message indicating whether it is initializing in "iptables" or "ipvs" mode. Confirming this ensures you understand the underlying mechanism (sequential iptables chains vs. efficient IPVS hash tables) handling your cluster's internal load balancing.

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