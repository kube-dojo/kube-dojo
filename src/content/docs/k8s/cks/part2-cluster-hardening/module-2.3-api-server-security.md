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

### War Story: The Anonymous API Takeover

In 2020, cloud security researchers discovered thousands of Kubernetes clusters actively hijacked by the TeamTNT threat group. The root cause wasn't a sophisticated zero-day vulnerability; it was a simple configuration oversight. 

Administrators had exposed their API servers to the internet without explicitly setting `--anonymous-auth=false`. Worse, someone had previously bound the `system:anonymous` user to the `cluster-admin` role for "troubleshooting purposes" and forgot to remove it. 

The attackers simply ran `kubectl --server=https://<target-ip>:6443 get secrets -A` without needing any credentials. Within minutes, they extracted cloud IAM keys stored in cluster secrets, deployed daemonsets running crypto-miners, and wiped the audit logs to hide their tracks. This incident illustrates why the API server is the ultimate prize for attackers and why defense-in-depth (disabling anonymous auth *plus* strict RBAC) is non-negotiable.

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

> **Stop and think**: The API server manifest lives at `/etc/kubernetes/manifests/kube-apiserver.yaml`. When you edit this file, the kubelet detects the change and restarts the API server. What happens to your cluster if you introduce a typo in a flag? How would you recover if `kubectl` stops working?

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

> **What would happen if**: You set `--authorization-mode=RBAC` without including `Node` in the mode list. The cluster seems to work fine for users. But what subtle security risk have you introduced for kubelet communication?

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

> **Pause and predict**: You enable encryption at rest for secrets using `aescbc` provider. Existing secrets were created before encryption was enabled. Are they now encrypted, or do you need to take additional action?

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

1. **A security scanner reports that your API server accepts anonymous requests and returns namespace listings to unauthenticated clients. You check the API server manifest and don't see `--anonymous-auth` at all. Why is anonymous access working, and what change fixes it?**
   <details>
   <summary>Answer</summary>
   When `--anonymous-auth` is not explicitly set, it defaults to `true` -- anonymous authentication is enabled by default in Kubernetes. This means any unauthenticated request is assigned the `system:anonymous` user and `system:unauthenticated` group. If any ClusterRoleBinding grants permissions to these identities, anonymous users get access. Fix by explicitly adding `--anonymous-auth=false` to the API server manifest at `/etc/kubernetes/manifests/kube-apiserver.yaml`. The API server will restart automatically. Verify with `curl -k https://<api-server>:6443/api/v1/namespaces` -- it should return 401 Unauthorized.
   </details>

2. **After enabling audit logging on the API server, you notice the API server pod is in CrashLoopBackOff. The `crictl logs` output shows "open /var/log/kubernetes/audit.log: no such file or directory." You added `--audit-log-path` and `--audit-policy-file` flags. What did you miss?**
   <details>
   <summary>Answer</summary>
   The API server container needs both the directory to exist AND volume mounts configured. Three things are required: (1) Create the log directory on the host: `mkdir -p /var/log/kubernetes`. (2) Add a `hostPath` volume in the API server manifest pointing to both the audit policy file and the log directory. (3) Add corresponding `volumeMounts` in the container spec. You also need the `--audit-policy-file` pointing to a valid audit policy YAML -- without a valid policy, the API server also fails. Always use `crictl logs` to diagnose static pod failures when `kubectl` is unavailable.
   </details>

3. **During a compliance audit, the auditor asks you to prove that secrets stored in etcd are encrypted at rest. You show them the EncryptionConfiguration with `aescbc` provider. They say "prove it's actually encrypting, not just configured." How do you demonstrate this?**
   <details>
   <summary>Answer</summary>
   Read a secret directly from etcd using etcdctl: `ETCDCTL_API=3 etcdctl get /registry/secrets/default/<secret-name> --endpoints=https://127.0.0.1:2379 --cacert=... --cert=... --key=... | hexdump -C | head`. If encryption is working, the output shows binary/encrypted data with the encryption provider prefix (e.g., `k8s:enc:aescbc:v1:key1`), not the plain-text secret value. If you see the actual secret data in readable form, encryption is not working despite being configured. Also important: existing secrets created before encryption was enabled remain unencrypted until you re-create them or run `kubectl get secrets -A -o json | kubectl replace -f -`.
   </details>

4. **A compromised kubelet on worker node `node-3` is making API calls to modify pods on `node-1` and `node-2`. Your API server uses `--authorization-mode=RBAC` (without Node). Why doesn't RBAC prevent this cross-node manipulation, and what authorization mode is missing?**
   <details>
   <summary>Answer</summary>
   RBAC alone grants permissions based on identity and role, not on node affinity. If the kubelet's credentials have a ClusterRoleBinding to `system:node` (which grants broad pod access), RBAC allows it to modify pods on any node. The missing mode is `Node` -- the Node authorizer restricts kubelets to only accessing resources related to pods scheduled on their own node. With `--authorization-mode=Node,RBAC`, a kubelet on `node-3` can only read/modify pods assigned to `node-3`. The NodeRestriction admission plugin adds further limits, preventing kubelets from modifying labels on other Node objects. Always use both: `Node,RBAC`.
   </details>

---

## Practice Scenario: Securing the Control Plane

Before diving into the exercise, let's look at how to troubleshoot an API server that fails to start after a configuration change.

### Worked Example: Diagnosing a CrashLooping API Server

**The Situation**: You added audit logging flags to `/etc/kubernetes/manifests/kube-apiserver.yaml`, but now `kubectl` commands immediately fail with `The connection to the server <ip>:6443 was refused`. 

**The Thought Process**:
1. **Identify the failure**: Since the API server is a static pod managed by the kubelet, `kubectl` won't work if the API server is down. I need to check the container runtime directly on the control plane node.
2. **Check the logs**: I run `crictl ps -a | grep kube-apiserver` to find the recently exited container ID, then inspect it with `crictl logs <container-id>`.
3. **Spot the error**: The logs clearly show `Error: unknown flag: --audit-log-pathh`.
4. **Fix and verify**: I edit the manifest to correct the typo to `--audit-log-path`, wait 30 seconds for the kubelet to detect the change and restart the pod, and run `kubectl get nodes` to confirm recovery.

### Your Turn: Fix the Misconfigured API Server

**Task**: You have inherited a cluster with a dangerously misconfigured API server. Your job is to secure it without breaking existing cluster operations.

1. **Verify the Vulnerability**:
   Test if the API server currently accepts anonymous requests by running:
   ```bash
   curl -k https://localhost:6443/api/v1/namespaces
   ```
   *(If it returns a JSON list of namespaces instead of an "Unauthorized" message, your cluster is vulnerable).*

2. **Harden the Configuration**:
   Edit the API server manifest at `/etc/kubernetes/manifests/kube-apiserver.yaml` to enforce the following security boundaries:
   * Disable anonymous authentication completely.
   * Ensure kubelets are restricted by adding the `Node` authorization mode (ensure `RBAC` remains in the list).
   * Enable the `NodeRestriction` admission plugin.

3. **Validate the Fix**:
   Monitor the API server restart using the container runtime:
   ```bash
   watch crictl ps
   ```
   Once the `kube-apiserver` container is up and running again for more than 30 seconds, re-run the `curl` command. You should now receive a `401 Unauthorized` error. 
   
   Finally, verify that legitimate authenticated traffic still works:
   ```bash
   kubectl get nodes
   ```

**Success criteria**: Anonymous access is explicitly denied, kubelets are restricted to their own nodes, and `kubectl` continues to function normally.

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