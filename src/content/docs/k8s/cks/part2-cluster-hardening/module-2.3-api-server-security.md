---
title: "Module 2.3: API Server Security"
slug: k8s/cks/part2-cluster-hardening/module-2.3-api-server-security
sidebar:
  order: 3
lab:
  id: cks-2.3-api-server-security
  url: https://killercoda.com/kubedojo/scenario/cks-2.3-api-server-security
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[COMPLEX]` - Critical infrastructure component
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: CKA API server knowledge, Module 1.2 (CIS Benchmarks)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Harden** API server flags for authentication, authorization, and encryption at rest
2. **Audit** API server configuration against security best practices and CIS benchmarks
3. **Configure** API server admission plugins and authentication mechanisms
4. **Diagnose** API server security issues from logs and failed request patterns

---

## Why This Module Matters

The API server is the control plane's front door. Every `kubectl` command, every controller, every node—they all talk to the API server. Compromising it means compromising the entire cluster.

CKS tests your ability to harden API server configuration and understand its security boundaries.

---

## API Server Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│              API SERVER REQUEST FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Request ──────────────────────────────────────────────►   │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ Authentication  │  Who are you?                         │
│  │ (authn)         │  - X.509 certs                        │
│  │                 │  - Bearer tokens                       │
│  │                 │  - ServiceAccount tokens              │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ Authorization   │  Are you allowed?                     │
│  │ (authz)         │  - RBAC                               │
│  │                 │  - Node authorizer                    │
│  │                 │  - Webhook                            │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ Admission       │  Should we modify/reject?             │
│  │ Control         │  - Mutating webhooks                  │
│  │                 │  - Validating webhooks                │
│  │                 │  - PodSecurity                        │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │    etcd         │  Persist the resource                 │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Critical API Server Flags

### Authentication Flags

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    # Disable anonymous authentication
    - --anonymous-auth=false

    # Client certificate authentication
    - --client-ca-file=/etc/kubernetes/pki/ca.crt

    # Bootstrap token authentication (for node join)
    - --enable-bootstrap-token-auth=true

    # ServiceAccount token authentication
    - --service-account-key-file=/etc/kubernetes/pki/sa.pub
    - --service-account-issuer=https://kubernetes.default.svc
```

### Authorization Flags

```yaml
    # Authorization modes (order matters!)
    - --authorization-mode=Node,RBAC
    # Node: kubelet authorization
    # RBAC: role-based access control
    # Don't use: AlwaysAllow (dangerous!)
```

### Admission Controller Flags

```yaml
    # Enable essential admission controllers
    - --enable-admission-plugins=NodeRestriction,PodSecurity,EventRateLimit

    # Disable risky admission controllers
    - --disable-admission-plugins=AlwaysAdmit
```

---

## Security-Critical Settings

```
┌─────────────────────────────────────────────────────────────┐
│              CRITICAL API SERVER SETTINGS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  anonymous-auth=false                                      │
│  └── Prevents unauthenticated API access                   │
│                                                             │
│  authorization-mode=Node,RBAC                              │
│  └── Never use AlwaysAllow                                 │
│  └── Node mode restricts kubelets to their own resources   │
│                                                             │
│  enable-admission-plugins=PodSecurity                      │
│  └── Enforces pod security standards                       │
│                                                             │
│  audit-log-path=<path>                                     │
│  └── Records all API requests                              │
│                                                             │
│  insecure-port=0 (deprecated but check!)                   │
│  └── Disabled insecure HTTP port                           │
│                                                             │
│  profiling=false                                           │
│  └── Disables profiling endpoints                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Audit Logging

### Enable Audit Logging

```yaml
# API server flags
- --audit-policy-file=/etc/kubernetes/audit-policy.yaml
- --audit-log-path=/var/log/kubernetes/audit.log
- --audit-log-maxage=30
- --audit-log-maxbackup=10
- --audit-log-maxsize=100
```

### Audit Policy

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Log authentication failures
  - level: Metadata
    omitStages:
    - RequestReceived

  # Log secret access
  - level: RequestResponse
    resources:
    - group: ""
      resources: ["secrets"]

  # Log all pod operations
  - level: Request
    resources:
    - group: ""
      resources: ["pods"]
    verbs: ["create", "update", "patch", "delete"]

  # Log RBAC changes
  - level: RequestResponse
    resources:
    - group: "rbac.authorization.k8s.io"

  # Skip noisy events
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
    - group: ""
      resources: ["endpoints", "services"]
```

### Audit Log Levels

```
┌─────────────────────────────────────────────────────────────┐
│              AUDIT LOG LEVELS                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  None                                                      │
│  └── Don't log this event                                  │
│                                                             │
│  Metadata                                                  │
│  └── Log request metadata (user, timestamp, resource)      │
│  └── Don't log request or response body                    │
│                                                             │
│  Request                                                   │
│  └── Log metadata and request body                         │
│  └── Don't log response body                               │
│                                                             │
│  RequestResponse                                           │
│  └── Log everything: metadata, request, response           │
│  └── Most verbose, use selectively                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## API Server Access Control

### Restrict API Server Network Access

```yaml
# API server flags to bind to specific address
- --advertise-address=10.0.0.10
- --bind-address=0.0.0.0  # Or specific IP

# In production, use firewall rules to restrict access
# iptables -A INPUT -p tcp --dport 6443 -s 10.0.0.0/8 -j ACCEPT
# iptables -A INPUT -p tcp --dport 6443 -j DROP
```

### NodeRestriction Admission

```yaml
# Enable NodeRestriction (limits what kubelets can modify)
- --enable-admission-plugins=NodeRestriction

# What it prevents:
# - Kubelets can only modify pods scheduled to them
# - Kubelets can only modify their own Node object
# - Kubelets cannot modify other nodes' labels
```

---

## Encryption at Rest

### Enable etcd Encryption

```yaml
# Create encryption configuration
# /etc/kubernetes/enc/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: <base64-encoded-32-byte-key>
    - identity: {}  # Fallback for reading old unencrypted data
```

```yaml
# API server flag
- --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml

# Mount the config
volumeMounts:
- name: enc
  mountPath: /etc/kubernetes/enc
  readOnly: true
volumes:
- name: enc
  hostPath:
    path: /etc/kubernetes/enc
```

### Verify Encryption

```bash
# Create a secret
kubectl create secret generic test-secret --from-literal=key=value

# Check etcd directly (should be encrypted)
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/test-secret | hexdump -C | head

# Should see encrypted data, not plain text
```

---

## Secure Kubelet Communication

```yaml
# API server flags for secure kubelet communication
- --kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt
- --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
- --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key

# Enable HTTPS for kubelet (on kubelet side)
# /var/lib/kubelet/config.yaml
serverTLSBootstrap: true
```

---

## Real Exam Scenarios

### Scenario 1: Disable Anonymous Auth

```bash
# Check current setting
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep anonymous

# Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Add to command section:
# - --anonymous-auth=false

# Wait for API server to restart
kubectl get pods -n kube-system -w
```

### Scenario 2: Enable Audit Logging

```bash
# Create audit policy
sudo tee /etc/kubernetes/audit-policy.yaml <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: RequestResponse
  resources:
  - group: "rbac.authorization.k8s.io"
EOF

# Create log directory
sudo mkdir -p /var/log/kubernetes

# Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Add flags:
# - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# - --audit-log-path=/var/log/kubernetes/audit.log
# - --audit-log-maxage=30
# - --audit-log-maxbackup=3
# - --audit-log-maxsize=100

# Add volume mounts for policy and logs
```

### Scenario 3: Check Authorization Mode

```bash
# Verify authorization mode
kubectl get pods -n kube-system kube-apiserver-* -o yaml | grep authorization-mode

# Should see: --authorization-mode=Node,RBAC
# Should NOT see: AlwaysAllow
```

---

## API Server Hardening Checklist

```bash
#!/bin/bash
# api-server-audit.sh

echo "=== API Server Security Audit ==="

# Get API server pod
POD=$(kubectl get pods -n kube-system -l component=kube-apiserver -o name | head -1)

# Check anonymous auth
echo "Anonymous auth:"
kubectl get $POD -n kube-system -o yaml | grep -E "anonymous-auth" || echo "  Not explicitly set (check default)"

# Check authorization mode
echo "Authorization mode:"
kubectl get $POD -n kube-system -o yaml | grep -E "authorization-mode"

# Check admission plugins
echo "Admission plugins:"
kubectl get $POD -n kube-system -o yaml | grep -E "enable-admission-plugins"

# Check audit logging
echo "Audit logging:"
kubectl get $POD -n kube-system -o yaml | grep -E "audit-log-path" || echo "  Not configured"

# Check encryption
echo "Encryption at rest:"
kubectl get $POD -n kube-system -o yaml | grep -E "encryption-provider-config" || echo "  Not configured"

# Check profiling
echo "Profiling:"
kubectl get $POD -n kube-system -o yaml | grep -E "profiling=false" || echo "  May be enabled"
```

---

## Did You Know?

- **The insecure port (--insecure-port)** was completely removed in Kubernetes 1.24. Before that, it exposed an unauthenticated API on localhost.

- **Node authorization mode** is specifically for kubelets. It restricts them to only access resources related to pods scheduled on their node.

- **Audit logs can be sent to webhooks** for real-time security monitoring. Many organizations use this for SIEM integration.

- **The API server is stateless**—all data is in etcd. You can run multiple API servers for high availability.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Anonymous auth enabled | Unauthenticated access | --anonymous-auth=false |
| AlwaysAllow authorization | No access control | Use Node,RBAC |
| No audit logging | Can't investigate incidents | Configure audit policy |
| Unencrypted etcd | Secrets in plain text | Enable encryption at rest |
| Missing NodeRestriction | Kubelets can modify any pod | Enable admission plugin |

---

## Quiz

1. **What authorization modes should be configured for production?**
   <details>
   <summary>Answer</summary>
   `--authorization-mode=Node,RBAC` - Node authorizer restricts kubelet access, RBAC provides role-based access control. Never use AlwaysAllow.
   </details>

2. **What does the NodeRestriction admission plugin do?**
   <details>
   <summary>Answer</summary>
   It limits kubelets to only modifying pods scheduled on their node and their own Node object. Prevents a compromised kubelet from affecting other nodes.
   </details>

3. **How do you verify etcd encryption is working?**
   <details>
   <summary>Answer</summary>
   Read a secret directly from etcd using etcdctl. The data should appear encrypted (not plain text). The command includes the encryption key prefix in the output.
   </details>

4. **What audit log level records both request and response bodies?**
   <details>
   <summary>Answer</summary>
   `RequestResponse` - This is the most verbose level and captures everything. Use it selectively for sensitive resources like secrets and RBAC.
   </details>

---

## Hands-On Exercise

**Task**: Audit and verify API server security configuration.

```bash
# This exercise inspects existing configuration
# (Modifying API server requires control plane access)

# Step 1: Get API server configuration
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml > /tmp/apiserver.yaml

# Step 2: Check authentication settings
echo "=== Authentication ==="
grep -E "anonymous-auth|client-ca-file" /tmp/apiserver.yaml

# Step 3: Check authorization settings
echo "=== Authorization ==="
grep -E "authorization-mode" /tmp/apiserver.yaml

# Step 4: Check admission plugins
echo "=== Admission Plugins ==="
grep -E "enable-admission-plugins|disable-admission-plugins" /tmp/apiserver.yaml

# Step 5: Check audit configuration
echo "=== Audit ==="
grep -E "audit-log|audit-policy" /tmp/apiserver.yaml

# Step 6: Check encryption
echo "=== Encryption ==="
grep -E "encryption-provider" /tmp/apiserver.yaml

# Step 7: Test anonymous access (should fail if properly configured)
echo "=== Anonymous Access Test ==="
curl -k https://$(kubectl get svc kubernetes -o jsonpath='{.spec.clusterIP}')/api/v1/namespaces 2>/dev/null | head -5

# Expected output for secure cluster:
# {
#   "kind": "Status",
#   "apiVersion": "v1",
#   "status": "Failure",
#   "message": "Unauthorized"
# }

# Cleanup
rm /tmp/apiserver.yaml
```

**Success criteria**: Identify current security settings and verify anonymous access is denied.

---

## Summary

**Critical API Server Settings**:
- `--anonymous-auth=false`
- `--authorization-mode=Node,RBAC`
- `--enable-admission-plugins=NodeRestriction,PodSecurity`
- `--audit-log-path=<path>`

**Security Layers**:
1. Authentication (who are you)
2. Authorization (what can you do)
3. Admission Control (should we allow/modify)

**Audit Logging**:
- Four levels: None, Metadata, Request, RequestResponse
- Log sensitive operations (secrets, RBAC)
- Store logs securely

**Exam Tips**:
- Know where API server manifest is located
- Understand flag syntax
- Practice reading audit policies

---

## Next Module

[Module 2.4: Kubernetes Upgrades](../module-2.4-kubernetes-upgrades/) - Security considerations for cluster upgrades.
