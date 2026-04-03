---
title: "Module 6.1: Kubernetes Audit Logging"
slug: k8s/cks/part6-runtime-security/module-6.1-audit-logging
sidebar:
  order: 1
lab:
  id: cks-6.1-audit-logging
  url: https://killercoda.com/kubedojo/scenario/cks-6.1-audit-logging
  duration: "45 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical CKS skill
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: API server basics, JSON/YAML proficiency

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** audit policy files with appropriate logging levels per resource and verb
2. **Implement** audit log backends (file and webhook) on the API server
3. **Trace** security incidents by analyzing audit log entries for suspicious API activity
4. **Design** audit policies that balance security visibility with storage and performance costs

---

## Why This Module Matters

Audit logs record all requests to the Kubernetes API server. They're your primary tool for investigating security incidents—who did what, when, and from where. Without audit logging, you're flying blind.

CKS heavily tests audit log configuration and analysis.

---

## What Gets Audited

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES AUDIT LOGGING                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Every API request is logged:                              │
│                                                             │
│  WHO (User Information):                                   │
│  ├── user.username                                         │
│  ├── user.groups                                           │
│  └── serviceAccountName                                    │
│                                                             │
│  WHAT (Request Details):                                   │
│  ├── verb (create, get, list, delete, etc.)               │
│  ├── resource (pods, secrets, deployments)                │
│  ├── namespace                                             │
│  └── requestURI                                            │
│                                                             │
│  WHEN (Timing):                                            │
│  ├── requestReceivedTimestamp                             │
│  └── stageTimestamp                                        │
│                                                             │
│  WHERE (Source):                                           │
│  └── sourceIPs                                             │
│                                                             │
│  RESULT:                                                   │
│  ├── responseStatus.code                                  │
│  └── responseStatus.reason                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Audit Levels

```
┌─────────────────────────────────────────────────────────────┐
│              AUDIT LEVELS                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  None                                                      │
│  └── Don't log this event                                  │
│                                                             │
│  Metadata                                                  │
│  └── Log request metadata only                             │
│      (user, timestamp, resource, verb)                     │
│      NO request or response body                           │
│                                                             │
│  Request                                                   │
│  └── Log metadata + request body                           │
│      Useful for create/update operations                   │
│      NO response body                                      │
│                                                             │
│  RequestResponse                                           │
│  └── Log metadata + request body + response body           │
│      Most detailed, largest logs                           │
│      Use sparingly (can be huge)                           │
│                                                             │
│  ⚠️ Higher levels = larger logs = more storage            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Audit Stages

```
┌─────────────────────────────────────────────────────────────┐
│              AUDIT STAGES                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RequestReceived                                           │
│  └── As soon as the request is received                    │
│      Before any processing                                 │
│                                                             │
│  ResponseStarted                                           │
│  └── Response headers sent, body not yet sent              │
│      Only for long-running requests (watch, exec)          │
│                                                             │
│  ResponseComplete                                          │
│  └── Response body complete, no more bytes sent            │
│      Most common stage to log                              │
│                                                             │
│  Panic                                                     │
│  └── Panic occurred during request processing              │
│      Always logged when it happens                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Audit Policy

### Basic Audit Policy Structure

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Don't log read-only requests to certain endpoints
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
      - group: ""
        resources: ["endpoints", "services", "services/status"]

  # Log secrets at Metadata level only (don't log secret data!)
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]

  # Log pod changes at Request level
  - level: Request
    resources:
      - group: ""
        resources: ["pods"]
    verbs: ["create", "update", "patch", "delete"]

  # Log everything else at Metadata level
  - level: Metadata
    omitStages:
      - "RequestReceived"
```

### Recommended Security-Focused Policy

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Don't log requests to certain non-sensitive endpoints
  - level: None
    nonResourceURLs:
      - /healthz*
      - /version
      - /readyz
      - /livez

  # Don't log kube-system service account watches
  - level: None
    users:
      - "system:kube-controller-manager"
      - "system:kube-scheduler"
      - "system:serviceaccount:kube-system:*"
    verbs: ["get", "watch", "list"]

  # Log authentication failures
  - level: RequestResponse
    resources:
      - group: "authentication.k8s.io"
        resources: ["tokenreviews"]

  # Log secret access at metadata only (NEVER log secret data)
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  # Log RBAC changes (who changed permissions?)
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
    verbs: ["create", "update", "patch", "delete"]

  # Log pod exec/attach (potential shell access)
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]

  # Log node modifications
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["nodes", "nodes/status"]
    verbs: ["create", "update", "patch", "delete"]

  # Default: Metadata for everything else
  - level: Metadata
    omitStages:
      - "RequestReceived"
```

---

## Enabling Audit Logging

### Configure API Server

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    # Audit policy file
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    # Log to file
    - --audit-log-path=/var/log/kubernetes/audit/audit.log
    # Log rotation
    - --audit-log-maxage=30        # days to keep
    - --audit-log-maxbackup=10     # files to keep
    - --audit-log-maxsize=100      # MB per file
    volumeMounts:
    - mountPath: /etc/kubernetes/audit-policy.yaml
      name: audit-policy
      readOnly: true
    - mountPath: /var/log/kubernetes/audit/
      name: audit-log
  volumes:
  - hostPath:
      path: /etc/kubernetes/audit-policy.yaml
      type: File
    name: audit-policy
  - hostPath:
      path: /var/log/kubernetes/audit/
      type: DirectoryOrCreate
    name: audit-log
```

### Verify Configuration

```bash
# Check API server has audit flags
ps aux | grep kube-apiserver | grep audit

# Check audit log exists
ls -la /var/log/kubernetes/audit/

# Tail the audit log
tail -f /var/log/kubernetes/audit/audit.log | jq .
```

---

## Audit Log Format

### Sample Audit Log Entry

```json
{
  "kind": "Event",
  "apiVersion": "audit.k8s.io/v1",
  "level": "RequestResponse",
  "auditID": "12345678-1234-1234-1234-123456789012",
  "stage": "ResponseComplete",
  "requestURI": "/api/v1/namespaces/default/pods",
  "verb": "create",
  "user": {
    "username": "admin",
    "groups": ["system:masters", "system:authenticated"]
  },
  "sourceIPs": ["192.168.1.100"],
  "userAgent": "kubectl/v1.28.0",
  "objectRef": {
    "resource": "pods",
    "namespace": "default",
    "name": "nginx-pod",
    "apiVersion": "v1"
  },
  "responseStatus": {
    "metadata": {},
    "code": 201
  },
  "requestReceivedTimestamp": "2024-01-15T10:30:00.000000Z",
  "stageTimestamp": "2024-01-15T10:30:00.100000Z"
}
```

---

## Analyzing Audit Logs

### Find Specific Events

```bash
# Find all secret accesses
cat audit.log | jq 'select(.objectRef.resource == "secrets")'

# Find all admin actions
cat audit.log | jq 'select(.user.username == "admin")'

# Find failed requests (non-2xx status)
cat audit.log | jq 'select(.responseStatus.code >= 400)'

# Find pod exec commands
cat audit.log | jq 'select(.objectRef.subresource == "exec")'

# Find requests from specific IP
cat audit.log | jq 'select(.sourceIPs[] == "192.168.1.100")'

# Find RBAC changes
cat audit.log | jq 'select(.objectRef.resource | test("role"))'
```

### Common Investigation Queries

```bash
# Who created this pod?
cat audit.log | jq 'select(.objectRef.name == "suspicious-pod" and .verb == "create") | {user: .user.username, time: .requestReceivedTimestamp}'

# What did this user do?
cat audit.log | jq 'select(.user.username == "attacker") | {verb: .verb, resource: .objectRef.resource, name: .objectRef.name}'

# All exec into pods in last hour
cat audit.log | jq 'select(.objectRef.subresource == "exec" and .requestReceivedTimestamp > "2024-01-15T09:30:00Z")'

# Who accessed secrets?
cat audit.log | jq 'select(.objectRef.resource == "secrets" and .verb == "get") | {user: .user.username, secret: .objectRef.name, ns: .objectRef.namespace}'
```

---

## Real Exam Scenarios

### Scenario 1: Enable Audit Logging

```bash
# Step 1: Create audit policy
sudo tee /etc/kubernetes/audit-policy.yaml << 'EOF'
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: None
    nonResourceURLs:
      - /healthz*
      - /version
      - /readyz

  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach"]

  - level: Metadata
    omitStages:
      - "RequestReceived"
EOF

# Step 2: Create log directory
sudo mkdir -p /var/log/kubernetes/audit

# Step 3: Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Add these flags:
# - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# - --audit-log-path=/var/log/kubernetes/audit/audit.log
# - --audit-log-maxage=30
# - --audit-log-maxbackup=3
# - --audit-log-maxsize=100

# Add volume mounts and volumes for:
# - audit-policy.yaml
# - /var/log/kubernetes/audit/

# Step 4: Wait for API server restart
kubectl get nodes

# Step 5: Verify logs are created
ls /var/log/kubernetes/audit/
tail -1 /var/log/kubernetes/audit/audit.log | jq .
```

### Scenario 2: Investigate Security Incident

```bash
# Question: Find who deleted the "important" secret from namespace "production"

# Search audit logs
cat /var/log/kubernetes/audit/audit.log | jq '
  select(
    .objectRef.resource == "secrets" and
    .objectRef.name == "important" and
    .objectRef.namespace == "production" and
    .verb == "delete"
  ) | {
    user: .user.username,
    groups: .user.groups,
    sourceIP: .sourceIPs[0],
    time: .requestReceivedTimestamp,
    userAgent: .userAgent
  }
'
```

### Scenario 3: Create Policy for Sensitive Resources

```yaml
# Audit policy that focuses on sensitive operations
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Skip health checks
  - level: None
    nonResourceURLs: ["/healthz*", "/readyz*", "/livez*"]

  # Log all secret operations
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  # Log all RBAC changes with full details
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["*"]
    verbs: ["create", "update", "patch", "delete"]

  # Log all pod exec/attach with full details
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]

  # Log namespace deletions
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["namespaces"]
    verbs: ["delete"]

  # Default
  - level: Metadata
```

---

## Webhook Backend

### Send Audit Logs to External System

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    - --audit-webhook-config-file=/etc/kubernetes/audit-webhook.yaml
    - --audit-webhook-initial-backoff=5s
```

### Webhook Configuration

```yaml
# /etc/kubernetes/audit-webhook.yaml
apiVersion: v1
kind: Config
clusters:
- name: audit
  cluster:
    server: https://audit.example.com/receive
    certificate-authority: /etc/kubernetes/pki/audit-ca.crt
contexts:
- name: audit
  context:
    cluster: audit
current-context: audit
```

---

## Did You Know?

- **Audit logs can be huge**. A busy cluster can generate gigabytes per day. Always configure rotation (`--audit-log-maxsize`, `--audit-log-maxbackup`).

- **Never log secret data at Request or RequestResponse level**. The secret values will be in plain text in your audit logs!

- **Audit logs are your forensic trail**. In a security incident, they're the first place to look. Without them, you can't prove what happened.

- **omitStages: ["RequestReceived"]** halves your log volume. You rarely need the RequestReceived stage.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No audit logging | No forensic trail | Enable immediately |
| Logging secrets at Request level | Secret data in logs | Use Metadata for secrets |
| No log rotation | Disk fills up | Set maxsize, maxage, maxbackup |
| Too verbose policy | Huge logs, noise | Use appropriate levels |
| Not testing policy | Syntax errors | Apply and verify logs appear |

---

## Quiz

1. **What's the difference between Metadata and RequestResponse audit levels?**
   <details>
   <summary>Answer</summary>
   Metadata logs only request metadata (user, timestamp, resource, verb). RequestResponse also logs the full request and response bodies. RequestResponse generates much larger logs.
   </details>

2. **Why should secrets never be logged at Request or RequestResponse level?**
   <details>
   <summary>Answer</summary>
   Because the secret values would be logged in plain text. Anyone with access to audit logs could read all secrets. Always use Metadata level for secrets.
   </details>

3. **What API server flags are needed to enable audit logging?**
   <details>
   <summary>Answer</summary>
   `--audit-policy-file` (path to policy) and `--audit-log-path` (path to log file). Optionally `--audit-log-maxsize`, `--audit-log-maxbackup`, `--audit-log-maxage` for rotation.
   </details>

4. **How do you find all pod exec commands in audit logs?**
   <details>
   <summary>Answer</summary>
   `cat audit.log | jq 'select(.objectRef.subresource == "exec")'` - Pod exec is logged as a subresource of pods.
   </details>

---

## Hands-On Exercise

**Task**: Create and test an audit policy.

```bash
# Step 1: Create audit policy
cat <<'EOF' > /tmp/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Don't log health checks
  - level: None
    nonResourceURLs:
      - /healthz*
      - /readyz*
      - /livez*

  # Log secrets at metadata only
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  # Log pod exec with full details
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach"]

  # Log all pod creation/deletion
  - level: Request
    resources:
      - group: ""
        resources: ["pods"]
    verbs: ["create", "delete"]

  # Default: metadata
  - level: Metadata
    omitStages:
      - "RequestReceived"
EOF

echo "=== Audit Policy Created ==="
cat /tmp/audit-policy.yaml

# Step 2: Validate policy syntax
echo "=== Validating Policy ==="
python3 -c "import yaml; yaml.safe_load(open('/tmp/audit-policy.yaml'))" && echo "Valid YAML"

# Step 3: Simulate audit log analysis
cat <<'EOF' > /tmp/sample-audit.json
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"Metadata","auditID":"1","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/secrets/db-password","verb":"get","user":{"username":"developer","groups":["developers"]},"sourceIPs":["10.0.0.5"],"objectRef":{"resource":"secrets","namespace":"default","name":"db-password"},"responseStatus":{"code":200},"requestReceivedTimestamp":"2024-01-15T10:00:00Z"}
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"RequestResponse","auditID":"2","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/pods/web/exec","verb":"create","user":{"username":"admin","groups":["system:masters"]},"sourceIPs":["10.0.0.1"],"objectRef":{"resource":"pods","namespace":"default","name":"web","subresource":"exec"},"responseStatus":{"code":101},"requestReceivedTimestamp":"2024-01-15T10:05:00Z"}
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"Request","auditID":"3","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/pods","verb":"delete","user":{"username":"attacker","groups":[]},"sourceIPs":["192.168.1.100"],"objectRef":{"resource":"pods","namespace":"default","name":"important-pod"},"responseStatus":{"code":200},"requestReceivedTimestamp":"2024-01-15T10:10:00Z"}
EOF

# Step 4: Analyze sample logs
echo "=== Finding Secret Access ==="
cat /tmp/sample-audit.json | jq 'select(.objectRef.resource == "secrets") | {user: .user.username, secret: .objectRef.name}'

echo "=== Finding Pod Exec ==="
cat /tmp/sample-audit.json | jq 'select(.objectRef.subresource == "exec") | {user: .user.username, pod: .objectRef.name}'

echo "=== Finding External IPs ==="
cat /tmp/sample-audit.json | jq 'select(.sourceIPs[] | startswith("192.")) | {user: .user.username, action: .verb, resource: .objectRef.resource}'

# Cleanup
rm -f /tmp/audit-policy.yaml /tmp/sample-audit.json
```

**Success criteria**: Understand audit policy configuration and log analysis.

---

## Summary

**Audit Levels**:
- None (no logging)
- Metadata (who, what, when)
- Request (+ request body)
- RequestResponse (+ response body)

**Key Configuration**:
- `--audit-policy-file` (policy path)
- `--audit-log-path` (log path)
- `--audit-log-maxsize/maxbackup/maxage` (rotation)

**Security Best Practices**:
- Use Metadata for secrets (never log secret data)
- Log pod/exec at RequestResponse
- Log RBAC changes at RequestResponse
- Configure log rotation

**Exam Tips**:
- Know policy YAML structure
- Understand audit levels
- Be able to query logs with jq

---

## Next Module

[Module 6.2: Runtime Security with Falco](../module-6.2-falco/) - Detecting suspicious container behavior.
