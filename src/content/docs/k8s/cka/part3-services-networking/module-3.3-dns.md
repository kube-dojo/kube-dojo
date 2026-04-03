---
title: "Module 3.3: DNS & CoreDNS"
slug: k8s/cka/part3-services-networking/module-3.3-dns
sidebar:
  order: 4
lab:
  id: cka-3.3-dns
  url: https://killercoda.com/kubedojo/scenario/cka-3.3-dns
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical infrastructure component
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 3.1 (Services), Module 3.2 (Endpoints)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Resolve** service names to IPs using Kubernetes DNS conventions (service.namespace.svc.cluster.local)
- **Debug** DNS failures by checking CoreDNS pods, configmap, and testing resolution from pods
- **Configure** custom DNS entries and upstream DNS forwarding in CoreDNS
- **Explain** how DNS-based service discovery enables microservice communication

---

## Why This Module Matters

DNS is how pods find services. Every time a pod makes a request to `my-service`, DNS resolves that name to an IP address. If DNS breaks, your entire cluster's service discovery breaks. Understanding CoreDNS is essential for troubleshooting connectivity issues.

The CKA exam tests DNS debugging, CoreDNS configuration, and understanding how Kubernetes names resolve. You'll need to troubleshoot DNS issues and understand the resolution hierarchy.

> **The Phone Book Analogy**
>
> DNS is your cluster's phone book. Instead of remembering that the "web-service" lives at IP 10.96.45.123, you just dial "web-service" and DNS looks up the number for you. CoreDNS is the phone operator who maintains this phone book and answers lookups.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand how Kubernetes DNS works
- Troubleshoot DNS resolution issues
- Configure CoreDNS
- Use different DNS name formats
- Debug pods with DNS problems

---

## Did You Know?

- **CoreDNS replaced kube-dns**: Before Kubernetes 1.11, kube-dns handled DNS. CoreDNS is faster, more flexible, and uses plugins for extensibility.

- **DNS is the #1 troubleshooting target**: Most "network issues" are actually DNS issues. When in doubt, check DNS first!

- **Pods get DNS configured automatically**: The kubelet injects `/etc/resolv.conf` into every pod, pointing to the cluster DNS service.

---

## Part 1: DNS Architecture

### 1.1 How Kubernetes DNS Works

```
┌────────────────────────────────────────────────────────────────┐
│                   Kubernetes DNS Architecture                   │
│                                                                 │
│   ┌────────────────┐                                           │
│   │     Pod        │                                           │
│   │                │                                           │
│   │ curl web-svc   │                                           │
│   │      │         │                                           │
│   │      ▼         │                                           │
│   │ /etc/resolv.conf                                           │
│   │ nameserver 10.96.0.10  ──────────────────────┐            │
│   │ search default.svc...                         │            │
│   └────────────────┘                              │            │
│                                                   │            │
│                                                   ▼            │
│   ┌──────────────────────────────────────────────────────────┐│
│   │              CoreDNS Service (10.96.0.10)                ││
│   │                                                           ││
│   │  ┌─────────┐ ┌─────────┐                                 ││
│   │  │CoreDNS  │ │CoreDNS  │  (2 replicas by default)        ││
│   │  │  Pod    │ │  Pod    │                                 ││
│   │  └────┬────┘ └────┬────┘                                 ││
│   │       │           │                                       ││
│   │       └─────┬─────┘                                       ││
│   │             ▼                                             ││
│   │    Query: web-svc.default.svc.cluster.local              ││
│   │             │                                             ││
│   │             ▼                                             ││
│   │    Response: 10.96.45.123 (Service ClusterIP)            ││
│   └──────────────────────────────────────────────────────────┘│
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 CoreDNS Components

| Component | Location | Purpose |
|-----------|----------|---------|
| CoreDNS Deployment | `kube-system` namespace | Runs CoreDNS pods |
| CoreDNS Service | `kube-system` namespace | Stable IP for DNS queries (usually 10.96.0.10) |
| Corefile ConfigMap | `kube-system` namespace | CoreDNS configuration |
| Pod /etc/resolv.conf | Every pod | Points to CoreDNS service |

### 1.3 Pod DNS Configuration

Every pod gets this automatically:

```bash
# Inside any pod
cat /etc/resolv.conf

# Output:
nameserver 10.96.0.10           # CoreDNS service IP
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

| Field | Purpose |
|-------|---------|
| `nameserver` | IP of CoreDNS service |
| `search` | Domains to append when resolving short names |
| `ndots:5` | If name has <5 dots, try search domains first |

---

## Part 2: DNS Name Formats

### 2.1 Service DNS Names

```
┌────────────────────────────────────────────────────────────────┐
│                   Service DNS Naming                            │
│                                                                 │
│   Full format (FQDN):                                          │
│   <service>.<namespace>.svc.<cluster-domain>                   │
│                                                                 │
│   Example: web-svc.production.svc.cluster.local                │
│            ───────  ──────────  ───  ─────────────             │
│               │        │         │        │                    │
│           service  namespace   fixed   cluster domain          │
│                                 suffix  (default)              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Shorthand Names (Search Domains)

```bash
# From pod in "default" namespace, reaching "web-svc" in "default":
curl web-svc                    # ✓ Works (same namespace)
curl web-svc.default            # ✓ Works
curl web-svc.default.svc        # ✓ Works
curl web-svc.default.svc.cluster.local  # ✓ Works (FQDN)

# From pod in "default" namespace, reaching "api" in "production":
curl api                        # ✗ Fails (wrong namespace)
curl api.production             # ✓ Works (cross-namespace)
curl api.production.svc.cluster.local   # ✓ Works (FQDN)
```

### 2.3 How Search Domains Work

```
┌────────────────────────────────────────────────────────────────┐
│                   Search Domain Resolution                      │
│                                                                 │
│   Pod in namespace "default" resolves "web-svc":               │
│                                                                 │
│   search default.svc.cluster.local svc.cluster.local ...      │
│                                                                 │
│   Step 1: Try web-svc.default.svc.cluster.local               │
│           └── Found! Returns IP                                │
│                                                                 │
│   If not found:                                                │
│   Step 2: Try web-svc.svc.cluster.local                       │
│   Step 3: Try web-svc.cluster.local                           │
│   Step 4: Try web-svc (external DNS)                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.4 Pod DNS Names

Pods also get DNS names:

```
┌────────────────────────────────────────────────────────────────┐
│                   Pod DNS Names                                 │
│                                                                 │
│   Pod IP: 10.244.1.5                                           │
│   DNS: 10-244-1-5.default.pod.cluster.local                    │
│        ──────────  ───────  ───  ─────────────                 │
│          IP with   namespace pod  cluster domain               │
│          dashes                                                 │
│                                                                 │
│   For StatefulSet pods with headless service:                  │
│   DNS: web-0.web-svc.default.svc.cluster.local                 │
│        ─────  ───────  ───────  ───                            │
│        pod    headless  namespace                              │
│        name   service                                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 3: CoreDNS Configuration

### 3.1 Viewing CoreDNS Components

```bash
# Check CoreDNS pods
k get pods -n kube-system -l k8s-app=kube-dns

# Check CoreDNS deployment
k get deployment coredns -n kube-system

# Check CoreDNS service
k get svc kube-dns -n kube-system
# Note: Service is named "kube-dns" for compatibility

# View CoreDNS configuration
k get configmap coredns -n kube-system -o yaml
```

### 3.2 Understanding the Corefile

```yaml
# CoreDNS ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors                          # Log errors
        health {                         # Health check endpoint
            lameduck 5s
        }
        ready                           # Readiness endpoint
        kubernetes cluster.local in-addr.arpa ip6.arpa {  # K8s plugin
            pods insecure               # Pod DNS resolution
            fallthrough in-addr.arpa ip6.arpa
            ttl 30                      # Cache TTL
        }
        prometheus :9153                # Metrics
        forward . /etc/resolv.conf {    # External DNS forwarding
            max_concurrent 1000
        }
        cache 30                        # Response caching
        loop                            # Detect loops
        reload                          # Auto-reload config
        loadbalance                     # Round-robin DNS
    }
```

### 3.3 Key Corefile Plugins

| Plugin | Purpose |
|--------|---------|
| `kubernetes` | Resolves Kubernetes service/pod names |
| `forward` | Forwards external queries to upstream DNS |
| `cache` | Caches responses to reduce load |
| `errors` | Logs DNS errors |
| `health` | Provides health check endpoint |
| `prometheus` | Exposes metrics |
| `loop` | Detects and breaks DNS loops |

### 3.4 Customizing CoreDNS

```yaml
# Add custom DNS entries
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        # ... existing config ...

        # Add custom hosts
        hosts {
            10.0.0.1 custom.example.com
            fallthrough
        }

        # Forward specific domain to custom DNS
        forward example.com 10.0.0.53
    }
```

```bash
# After editing, restart CoreDNS
k rollout restart deployment coredns -n kube-system
```

---

## Part 4: DNS Debugging

### 4.1 DNS Debugging Workflow

```
DNS Issue?
    │
    ├── Step 1: Test from inside a pod
    │   k run test --rm -it --image=busybox:1.36 -- nslookup <service>
    │       │
    │       ├── Works? → DNS is fine, issue is elsewhere
    │       │
    │       └── Fails? → Continue debugging
    │
    ├── Step 2: Check CoreDNS is running
    │   k get pods -n kube-system -l k8s-app=kube-dns
    │       │
    │       └── Not running? → Fix CoreDNS deployment
    │
    ├── Step 3: Check CoreDNS logs
    │   k logs -n kube-system -l k8s-app=kube-dns
    │       │
    │       └── Errors? → Check Corefile config
    │
    ├── Step 4: Check pod resolv.conf
    │   k exec <pod> -- cat /etc/resolv.conf
    │       │
    │       └── Wrong nameserver? → Check kubelet config
    │
    └── Step 5: Test external DNS
        k run test --rm -it --image=busybox:1.36 -- nslookup google.com
            │
            └── Fails? → Check forward config in Corefile
```

### 4.2 Common DNS Commands

```bash
# Test DNS from inside cluster
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup kubernetes

# Test specific service
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web-svc.default.svc.cluster.local

# Test with specific DNS server
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web-svc 10.96.0.10

# Check resolv.conf
k exec <pod> -- cat /etc/resolv.conf

# Check CoreDNS logs
k logs -n kube-system -l k8s-app=kube-dns --tail=50

# Verify CoreDNS is responding
k run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup kubernetes.default.svc.cluster.local
```

### 4.3 DNS Debug Pod

Use a debug pod with more tools:

```bash
# Create a debug pod
k run dns-debug --image=nicolaka/netshoot --restart=Never -- sleep 3600

# Use it for debugging
k exec -it dns-debug -- dig web-svc.default.svc.cluster.local
k exec -it dns-debug -- host web-svc
k exec -it dns-debug -- nslookup web-svc

# Cleanup
k delete pod dns-debug
```

### 4.4 Common DNS Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `NXDOMAIN` | Service doesn't exist | Check service name/namespace |
| `Server failure` | CoreDNS down | Check CoreDNS pods |
| Timeout | Network issue to CoreDNS | Check pod network, CNI |
| Wrong IP returned | Stale cache | Restart CoreDNS, check cache TTL |
| External domains fail | Forward config wrong | Check Corefile forward directive |

---

## Part 5: DNS Policies

### 5.1 Pod DNS Policies

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-policy-demo
spec:
  dnsPolicy: ClusterFirst    # Default
  containers:
  - name: app
    image: nginx
```

| Policy | Behavior |
|--------|----------|
| `ClusterFirst` (default) | Use cluster DNS, fall back to node DNS |
| `Default` | Use node's DNS settings (inherit from host) |
| `ClusterFirstWithHostNet` | Use cluster DNS even with `hostNetwork: true` |
| `None` | No DNS config, must specify dnsConfig |

### 5.2 Custom DNS Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns
spec:
  dnsPolicy: "None"          # Required for custom config
  dnsConfig:
    nameservers:
    - 1.1.1.1                # Custom DNS server
    - 8.8.8.8
    searches:
    - custom.local           # Custom search domain
    - svc.cluster.local
    options:
    - name: ndots
      value: "2"             # Custom ndots
  containers:
  - name: app
    image: nginx
```

### 5.3 Using hostNetwork with DNS

```yaml
# Pod using host network but still using cluster DNS
apiVersion: v1
kind: Pod
metadata:
  name: host-network-pod
spec:
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet   # Important!
  containers:
  - name: app
    image: nginx
```

---

## Part 6: SRV Records

### 6.1 What Are SRV Records?

SRV records include port information along with IP:

```bash
# Query SRV record for service
dig SRV web-svc.default.svc.cluster.local

# Returns:
# _http._tcp.web-svc.default.svc.cluster.local. 30 IN SRV 0 100 80 web-svc.default.svc.cluster.local.
```

### 6.2 Named Ports and SRV Records

```yaml
# Service with named port
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  selector:
    app: web
  ports:
  - name: http          # Named port
    port: 80
    targetPort: 8080
```

```bash
# SRV record format: _<port-name>._<protocol>.<service>.<namespace>.svc.cluster.local
# Query:
dig SRV _http._tcp.web-svc.default.svc.cluster.local
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using wrong namespace | `NXDOMAIN` error | Use FQDN or check namespace |
| Forgetting `.svc` | Resolution fails | Use `service.namespace` or FQDN |
| CoreDNS not running | All DNS fails | Check `kube-system` pods |
| Wrong dnsPolicy | Pod can't resolve | Use `ClusterFirst` for cluster services |
| Editing wrong ConfigMap | Config not applied | Edit `coredns` ConfigMap in `kube-system` |

---

## Quiz

1. **What DNS server do pods use by default?**
   <details>
   <summary>Answer</summary>
   The CoreDNS service in kube-system namespace, typically at IP 10.96.0.10. This is configured via `/etc/resolv.conf` injected by kubelet.
   </details>

2. **How would a pod in namespace "app" reach a service "db" in namespace "data"?**
   <details>
   <summary>Answer</summary>
   Use `db.data` or the FQDN `db.data.svc.cluster.local`. The short name `db` alone won't work from a different namespace.
   </details>

3. **Where is CoreDNS configuration stored?**
   <details>
   <summary>Answer</summary>
   In a ConfigMap named `coredns` in the `kube-system` namespace. The configuration is in the `Corefile` key.
   </details>

4. **What does `ndots:5` mean in `/etc/resolv.conf`?**
   <details>
   <summary>Answer</summary>
   If a query has fewer than 5 dots, try appending search domains first before querying as absolute. This optimizes resolution for Kubernetes names like `web-svc.default.svc.cluster.local` (4 dots).
   </details>

5. **A pod can't resolve `google.com`. What's likely wrong?**
   <details>
   <summary>Answer</summary>
   The `forward` directive in CoreDNS Corefile might be misconfigured, or there's no network path from the cluster to external DNS servers. Check Corefile and pod network connectivity.
   </details>

---

## Hands-On Exercise

**Task**: Debug and understand DNS in Kubernetes.

**Steps**:

1. **Check CoreDNS is running**:
```bash
k get pods -n kube-system -l k8s-app=kube-dns
k get svc -n kube-system kube-dns
```

2. **View CoreDNS configuration**:
```bash
k get configmap coredns -n kube-system -o yaml
```

3. **Create test service**:
```bash
k create deployment web --image=nginx
k expose deployment web --port=80
```

4. **Test DNS resolution**:
```bash
# Short name
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web

# With namespace
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default

# FQDN
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default.svc.cluster.local
```

5. **Check pod resolv.conf**:
```bash
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  cat /etc/resolv.conf
```

6. **Test cross-namespace DNS**:
```bash
# Create service in another namespace
k create namespace other
k create deployment db -n other --image=nginx
k expose deployment db -n other --port=80

# Resolve from default namespace
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup db.other
```

7. **Test external DNS**:
```bash
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup google.com
```

8. **Check CoreDNS logs**:
```bash
k logs -n kube-system -l k8s-app=kube-dns --tail=20
```

9. **Cleanup**:
```bash
k delete deployment web
k delete svc web
k delete namespace other
```

**Success Criteria**:
- [ ] Can verify CoreDNS is running
- [ ] Understand DNS name formats
- [ ] Can resolve services by short name and FQDN
- [ ] Can resolve cross-namespace services
- [ ] Can troubleshoot DNS issues

---

## Practice Drills

### Drill 1: DNS Basics (Target: 3 minutes)

```bash
# Create a service
k create deployment dns-test --image=nginx
k expose deployment dns-test --port=80

# Test all name formats
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  sh -c 'nslookup dns-test && nslookup dns-test.default && nslookup dns-test.default.svc.cluster.local'

# Cleanup
k delete deployment dns-test
k delete svc dns-test
```

### Drill 2: Check CoreDNS Health (Target: 2 minutes)

```bash
# Check pods
k get pods -n kube-system -l k8s-app=kube-dns -o wide

# Check service
k get svc kube-dns -n kube-system

# Check deployment
k get deployment coredns -n kube-system

# View logs
k logs -n kube-system -l k8s-app=kube-dns --tail=10
```

### Drill 3: Cross-Namespace Resolution (Target: 3 minutes)

```bash
# Create services in two namespaces
k create namespace ns1
k create namespace ns2
k create deployment app1 -n ns1 --image=nginx
k create deployment app2 -n ns2 --image=nginx
k expose deployment app1 -n ns1 --port=80
k expose deployment app2 -n ns2 --port=80

# From ns1, reach ns2 (and vice versa)
k run test -n ns1 --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup app2.ns2

k run test -n ns2 --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup app1.ns1

# Cleanup
k delete namespace ns1 ns2
```

### Drill 4: Inspect Pod DNS Config (Target: 2 minutes)

```bash
# Create a pod
k run dns-check --image=busybox:1.36 --command -- sleep 3600

# Check its DNS config
k exec dns-check -- cat /etc/resolv.conf

# Verify the nameserver matches kube-dns service
k get svc kube-dns -n kube-system -o jsonpath='{.spec.clusterIP}'

# Cleanup
k delete pod dns-check
```

### Drill 5: CoreDNS ConfigMap (Target: 3 minutes)

```bash
# View the Corefile
k get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}'

# Describe the configmap
k describe configmap coredns -n kube-system

# Check what plugins are enabled
k get configmap coredns -n kube-system -o yaml | grep -E "kubernetes|forward|cache"
```

### Drill 6: Headless Service DNS (Target: 4 minutes)

```bash
# Create deployment
k create deployment headless-test --image=nginx --replicas=3

# Create headless service
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless-svc
spec:
  clusterIP: None
  selector:
    app: headless-test
  ports:
  - port: 80
EOF

# Regular service returns single IP
# Headless returns all pod IPs
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup headless-svc
# Should return multiple IPs

# Cleanup
k delete deployment headless-test
k delete svc headless-svc
```

### Drill 7: Custom DNS Policy (Target: 4 minutes)

```bash
# Create pod with custom DNS
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  dnsPolicy: None
  dnsConfig:
    nameservers:
    - 8.8.8.8
    searches:
    - custom.local
    options:
    - name: ndots
      value: "2"
  containers:
  - name: app
    image: busybox:1.36
    command: ["sleep", "3600"]
EOF

# Check the custom resolv.conf
k exec custom-dns-pod -- cat /etc/resolv.conf
# Should show 8.8.8.8 and custom.local

# Note: won't resolve cluster services!
k exec custom-dns-pod -- nslookup kubernetes
# Will fail

# Cleanup
k delete pod custom-dns-pod
```

### Drill 8: Debug DNS Failure (Target: 4 minutes)

```bash
# Create service
k create deployment web --image=nginx
k expose deployment web --port=80

# Simulate debugging workflow
# Step 1: Test from pod
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web
# Should work

# Step 2: Test FQDN
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup web.default.svc.cluster.local
# Should work

# Step 3: Check CoreDNS
k get pods -n kube-system -l k8s-app=kube-dns

# Step 4: Check logs
k logs -n kube-system -l k8s-app=kube-dns --tail=5

# Cleanup
k delete deployment web
k delete svc web
```

### Drill 9: Challenge - Complete DNS Workflow

Without looking at solutions:

1. Verify CoreDNS is running
2. Create deployment `challenge` with nginx
3. Expose it as a service
4. Test DNS resolution with short name, namespace, and FQDN
5. Create the same service in a new namespace `test`
6. Resolve across namespaces
7. View the CoreDNS logs
8. Cleanup everything

```bash
# YOUR TASK: Complete in under 5 minutes
```

<details>
<summary>Solution</summary>

```bash
# 1. Verify CoreDNS
k get pods -n kube-system -l k8s-app=kube-dns

# 2. Create deployment
k create deployment challenge --image=nginx

# 3. Expose
k expose deployment challenge --port=80

# 4. Test DNS formats
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  sh -c 'nslookup challenge; nslookup challenge.default; nslookup challenge.default.svc.cluster.local'

# 5. Create in new namespace
k create namespace test
k create deployment challenge -n test --image=nginx
k expose deployment challenge -n test --port=80

# 6. Cross-namespace resolution
k run test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup challenge.test

# 7. View logs
k logs -n kube-system -l k8s-app=kube-dns --tail=10

# 8. Cleanup
k delete deployment challenge
k delete svc challenge
k delete namespace test
```

</details>

---

## Next Module

[Module 3.4: Ingress](../module-3.4-ingress/) - HTTP routing and external access to services.
