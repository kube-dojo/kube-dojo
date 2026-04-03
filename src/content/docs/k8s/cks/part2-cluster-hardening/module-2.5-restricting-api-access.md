---
title: "Module 2.5: Restricting API Access"
slug: k8s/cks/part2-cluster-hardening/module-2.5-restricting-api-access
sidebar:
  order: 5
lab:
  id: cks-2.5-restricting-api-access
  url: https://killercoda.com/kubedojo/scenario/cks-2.5-restricting-api-access
  duration: "35 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Essential for cluster security
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 2.3 (API Server Security), networking basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** API server network restrictions using firewall rules and CIDR allowlists
2. **Implement** authentication webhooks and OIDC integration for API access control
3. **Audit** API access patterns to detect unauthorized or anomalous requests
4. **Design** multi-layer API access controls combining network, authentication, and RBAC

---

## Why This Module Matters

The Kubernetes API is the crown jewel—access to it means control over everything. While RBAC controls what authenticated users can do, restricting WHO can even reach the API is equally important.

This module covers network-level and authentication-based API access restrictions.

---

## API Access Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│              API ACCESS ATTACK SURFACE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet                                                   │
│     │                                                       │
│     ├──► API Server :6443  ← Exposed?                      │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ATTACK VECTORS                          │   │
│  │                                                      │   │
│  │  1. Direct API access from internet                 │   │
│  │     → Brute force auth, exploit vulnerabilities     │   │
│  │                                                      │   │
│  │  2. Compromised pod in cluster                      │   │
│  │     → Uses mounted token to call API                │   │
│  │                                                      │   │
│  │  3. Compromised node                                │   │
│  │     → Uses kubelet credentials                      │   │
│  │                                                      │   │
│  │  4. Stolen kubeconfig                               │   │
│  │     → Direct cluster access from anywhere           │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Network-Level Restrictions

### Firewall Rules (External)

```bash
# Only allow API access from specific IPs
# On cloud: Security Groups, Firewall Rules, NSGs

# AWS Security Group example:
# Inbound rule: TCP 6443 from 10.0.0.0/8 (internal only)

# iptables on API server node
sudo iptables -A INPUT -p tcp --dport 6443 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 6443 -s 192.168.1.0/24 -j ACCEPT  # Admin VPN
sudo iptables -A INPUT -p tcp --dport 6443 -j DROP
```

### Private API Endpoint

```yaml
# EKS: Enable private endpoint, disable public
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config endpointPrivateAccess=true,endpointPublicAccess=false

# GKE: Private cluster
gcloud container clusters create private-cluster \
  --enable-private-endpoint \
  --master-ipv4-cidr 172.16.0.0/28

# AKS: Private cluster
az aks create \
  --name myAKSCluster \
  --enable-private-cluster
```

---

## Kubernetes-Native Network Restrictions

### API Server NetworkPolicy (Limited)

```yaml
# Note: NetworkPolicy doesn't directly apply to API server
# But you can restrict which pods can reach it

# Block pods from directly accessing API server IP
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-api-direct
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - to:
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
  # Allow everything except API server
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.96.0.1/32  # Kubernetes service IP
```

### API Server Bind Address

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    # Bind only to specific interface
    - --bind-address=10.0.0.10  # Internal IP only
    # Or bind to all (less secure)
    - --bind-address=0.0.0.0
```

---

## Authentication Restrictions

### Disable Anonymous Authentication

```yaml
# API server flag
- --anonymous-auth=false

# Verification
curl -k https://<api-server>:6443/api/v1/namespaces
# Should return 401 Unauthorized
```

### Client Certificate Requirements

```yaml
# Require client certificates (mutual TLS)
- --client-ca-file=/etc/kubernetes/pki/ca.crt

# Clients must present valid certificate signed by CA
# This is default in kubeadm clusters
```

### Token Validation

```yaml
# Configure token authentication
- --service-account-key-file=/etc/kubernetes/pki/sa.pub
- --service-account-issuer=https://kubernetes.default.svc

# Optional: External OIDC provider
- --oidc-issuer-url=https://accounts.example.com
- --oidc-client-id=kubernetes
- --oidc-username-claim=email
- --oidc-groups-claim=groups
```

---

## Webhook Authentication

```
┌─────────────────────────────────────────────────────────────┐
│              WEBHOOK AUTHENTICATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Request ──► API Server ──► Webhook ──► Response           │
│                               │                             │
│                               ▼                             │
│                      ┌─────────────────┐                   │
│                      │ Auth Service    │                   │
│                      │                 │                   │
│                      │ - Validate token│                   │
│                      │ - Return user   │                   │
│                      │   info          │                   │
│                      └─────────────────┘                   │
│                                                             │
│  Use cases:                                                │
│  • Custom authentication systems                           │
│  • Integration with SSO                                    │
│  • Additional validation logic                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Configure Webhook Authentication

```yaml
# API server flags
- --authentication-token-webhook-config-file=/etc/kubernetes/webhook-config.yaml
- --authentication-token-webhook-cache-ttl=2m

# /etc/kubernetes/webhook-config.yaml
apiVersion: v1
kind: Config
clusters:
- name: auth-service
  cluster:
    certificate-authority: /etc/kubernetes/pki/webhook-ca.crt
    server: https://auth.example.com/authenticate
users:
- name: api-server
  user:
    client-certificate: /etc/kubernetes/pki/webhook-client.crt
    client-key: /etc/kubernetes/pki/webhook-client.key
contexts:
- context:
    cluster: auth-service
    user: api-server
  name: webhook
current-context: webhook
```

---

## API Rate Limiting

### EventRateLimit Admission

```yaml
# Enable admission controller
- --enable-admission-plugins=EventRateLimit
- --admission-control-config-file=/etc/kubernetes/admission-config.yaml

# /etc/kubernetes/admission-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: EventRateLimit
  path: /etc/kubernetes/event-rate-limit.yaml

# /etc/kubernetes/event-rate-limit.yaml
apiVersion: eventratelimit.admission.k8s.io/v1alpha1
kind: Configuration
limits:
- type: Namespace
  qps: 50
  burst: 100
- type: User
  qps: 10
  burst: 20
```

### API Priority and Fairness

```yaml
# Kubernetes 1.20+: API Priority and Fairness
# Controls API request queuing and priority

# Check current flow schemas
kubectl get flowschemas

# Check priority levels
kubectl get prioritylevelconfigurations

# Example: Lower priority for batch workloads
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: FlowSchema
metadata:
  name: batch-jobs-low-priority
spec:
  priorityLevelConfiguration:
    name: low-priority
  matchingPrecedence: 1000
  rules:
  - subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: batch-runner
        namespace: batch
    resourceRules:
    - apiGroups: ["batch"]
      resources: ["jobs"]
      verbs: ["*"]
```

---

## Audit and Monitor API Access

### API Access Logging

```yaml
# Audit policy to log all API access attempts
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all authentication attempts
- level: RequestResponse
  omitStages:
  - RequestReceived
  resources:
  - group: "authentication.k8s.io"

# Log failed requests
- level: Metadata
  omitStages:
  - RequestReceived
```

### Monitoring API Metrics

```bash
# Check API server metrics
kubectl get --raw /metrics | grep apiserver_request

# Authentication failures
kubectl get --raw /metrics | grep authentication_attempts

# Rate limiting metrics
kubectl get --raw /metrics | grep apiserver_flowcontrol
```

---

## Real Exam Scenarios

### Scenario 1: Restrict API to Internal Network

```bash
# Check current API server bind address
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep bind-address

# Edit to bind to internal interface only
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Change:
# --bind-address=0.0.0.0
# To:
# --bind-address=10.0.0.10  # Internal IP

# API server will restart automatically
```

### Scenario 2: Verify Anonymous Access Disabled

```bash
# Test anonymous access
curl -k https://<api-server>:6443/api/v1/namespaces

# If anonymous is disabled, should get:
# {"kind":"Status","apiVersion":"v1","status":"Failure","message":"Unauthorized",...}

# If anonymous is enabled, may get namespace list or partial data
# Fix by adding --anonymous-auth=false to API server
```

### Scenario 3: Configure API Access for Specific Users

```bash
# Create kubeconfig for specific user with limited network access
kubectl config set-cluster restricted \
  --server=https://internal-api.example.com:6443 \
  --certificate-authority=/path/to/ca.crt

kubectl config set-credentials limited-user \
  --client-certificate=/path/to/user.crt \
  --client-key=/path/to/user.key

kubectl config set-context limited \
  --cluster=restricted \
  --user=limited-user
```

---

## Defense in Depth for API

```
┌─────────────────────────────────────────────────────────────┐
│              API ACCESS DEFENSE LAYERS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Network                                          │
│  └── Firewall, private endpoint, VPN                       │
│                                                             │
│  Layer 2: TLS                                              │
│  └── Mutual TLS, certificate validation                    │
│                                                             │
│  Layer 3: Authentication                                   │
│  └── No anonymous, OIDC, client certs                      │
│                                                             │
│  Layer 4: Authorization                                    │
│  └── RBAC with least privilege                            │
│                                                             │
│  Layer 5: Admission                                        │
│  └── Rate limiting, validation                             │
│                                                             │
│  Layer 6: Audit                                            │
│  └── Log all access, monitor anomalies                     │
│                                                             │
│  All layers should be active!                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The Kubernetes API server by default binds to 0.0.0.0**, making it accessible from all network interfaces. This is convenient but potentially dangerous.

- **Cloud providers offer private clusters** where the API server has no public IP at all. Access is only through VPN or bastion hosts.

- **API Priority and Fairness** (APF) replaced the older max-in-flight limits in Kubernetes 1.20. It provides fairer queuing during overload.

- **Some organizations use API gateways** in front of the Kubernetes API for additional security, logging, and rate limiting.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Public API endpoint | Anyone can attempt auth | Private endpoint + VPN |
| No firewall rules | Network-level exposure | Restrict to known IPs |
| Anonymous auth enabled | Unauthenticated access | --anonymous-auth=false |
| No rate limiting | DoS vulnerability | EventRateLimit admission |
| Not monitoring access | Can't detect attacks | Enable audit logging |

---

## Quiz

1. **How do you make the API server accessible only from internal network?**
   <details>
   <summary>Answer</summary>
   Set `--bind-address` to internal IP, use firewall rules to block external access, or use cloud provider's private endpoint feature.
   </details>

2. **What happens when anonymous authentication is disabled and an unauthenticated request arrives?**
   <details>
   <summary>Answer</summary>
   The API server returns 401 Unauthorized. The request is rejected before any authorization check.
   </details>

3. **What is the purpose of the EventRateLimit admission controller?**
   <details>
   <summary>Answer</summary>
   It limits the rate of events (and other API requests) per namespace or user, preventing DoS attacks and excessive API load from misbehaving clients.
   </details>

4. **Why should you combine multiple API access restrictions?**
   <details>
   <summary>Answer</summary>
   Defense in depth. Network restrictions prevent access, but if bypassed, authentication stops unauthenticated users, RBAC limits what authenticated users can do, and audit logs everything.
   </details>

---

## Hands-On Exercise

**Task**: Audit and verify API access restrictions.

```bash
# Step 1: Check API server configuration
echo "=== API Server Config ==="
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -E "bind-address|anonymous-auth|authorization-mode"

# Step 2: Test anonymous access (from within cluster)
echo "=== Anonymous Access Test ==="
kubectl run curlpod --image=curlimages/curl --rm -it --restart=Never -- \
  curl -sk https://kubernetes.default.svc/api/v1/namespaces 2>&1 | head -5

# Step 3: Check if API is accessible externally
echo "=== External Access Check ==="
API_IP=$(kubectl get svc kubernetes -o jsonpath='{.spec.clusterIP}')
echo "API Server internal IP: $API_IP"
# In production, also check external IP/DNS

# Step 4: Review authentication methods
echo "=== Authentication Config ==="
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -E "client-ca|oidc|token|webhook"

# Step 5: Check for rate limiting
echo "=== Rate Limiting ==="
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -E "EventRateLimit|admission-control"

# Step 6: Review flow schemas (API Priority and Fairness)
echo "=== Flow Schemas ==="
kubectl get flowschemas --no-headers | head -5

# Success criteria:
# - Anonymous access denied
# - Multiple auth methods configured
# - Rate limiting or APF active
```

**Success criteria**: Identify current API access restrictions and verify anonymous access is blocked.

---

## Summary

**Network Restrictions**:
- Private API endpoints
- Firewall rules
- VPN-only access

**Authentication Restrictions**:
- Disable anonymous auth
- Require client certificates
- OIDC for user authentication

**Rate Limiting**:
- EventRateLimit admission
- API Priority and Fairness

**Defense in Depth**:
- Layer all restrictions
- Audit everything
- Monitor for anomalies

**Exam Tips**:
- Know how to check bind-address
- Understand anonymous-auth implications
- Practice verifying API accessibility

---

## Part 2 Complete!

You've finished **Cluster Hardening** (15% of CKS). You now understand:
- RBAC deep dive and escalation prevention
- ServiceAccount security and token management
- API server security configuration
- Kubernetes upgrade security
- Restricting API access

**Next Part**: [Part 3: System Hardening](../part3-system-hardening/module-3.1-apparmor/) - AppArmor, seccomp, and OS-level security.
