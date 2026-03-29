---
title: "Module 1.6: Security Practices (DevSecOps)"
slug: prerequisites/modern-devops/module-1.6-devsecops/
sidebar:
  order: 7
---
> **Complexity**: `[MEDIUM]` - Essential security mindset
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: CI/CD concepts (Module 3)

---

## Why This Module Matters

Security used to be an afterthought—a team that said "no" at the end of development. That doesn't work in cloud-native environments where you deploy multiple times per day. DevSecOps integrates security into every stage of the development lifecycle. For Kubernetes environments, where misconfiguration is the #1 security risk, this is critical.

---

## What is DevSecOps?

DevSecOps is **security integrated into DevOps**, not bolted on afterward.

```
┌─────────────────────────────────────────────────────────────┐
│              TRADITIONAL vs DEVSECOPS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Traditional Security:                                      │
│  ┌─────┐    ┌─────┐    ┌──────────┐    ┌─────────────┐   │
│  │ Dev │───►│ QA  │───►│ Security │───►│ Production  │   │
│  └─────┘    └─────┘    │ Review   │    └─────────────┘   │
│                        └──────────┘                        │
│                             │                               │
│                        Bottleneck!                          │
│                        "Go back and fix"                   │
│                                                             │
│  DevSecOps:                                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Security at EVERY stage                             │  │
│  │                                                      │  │
│  │  Plan → Code → Build → Test → Deploy → Monitor     │  │
│  │    ↑      ↑      ↑       ↑       ↑         ↑       │  │
│  │  Threat  SAST   SCA   DAST   Config   Runtime     │  │
│  │  Model        (deps)       Scan    Security       │  │
│  │                                                      │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Key shift: Security is everyone's job                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Shift Left Philosophy

"Shift Left" means finding security issues earlier:

```
┌─────────────────────────────────────────────────────────────┐
│              COST OF FIXING SECURITY ISSUES                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cost to Fix                                               │
│       │                                                     │
│   $$$│                                         ┌────┐      │
│      │                                    ┌────┤    │      │
│      │                               ┌────┤    │    │      │
│    $$│                          ┌────┤    │    │    │      │
│      │                     ┌────┤    │    │    │    │      │
│     $│                ┌────┤    │    │    │    │    │      │
│      │           ┌────┤    │    │    │    │    │    │      │
│      │      ┌────┤    │    │    │    │    │    │    │      │
│      └──────┴────┴────┴────┴────┴────┴────┴────┴────┴──►   │
│           Code  Build Test Stage Prod Breach               │
│                                                             │
│  Find it early = cheap fix                                 │
│  Find it in production = expensive fix                     │
│  Find it after breach = catastrophic                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security in CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              SECURE CI/CD PIPELINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PRE-COMMIT                                             │
│     ├── Secret scanning (prevent committing secrets)       │
│     └── git-secrets, detect-secrets                        │
│                                                             │
│  2. STATIC ANALYSIS (SAST)                                 │
│     ├── Scan source code for vulnerabilities              │
│     └── Semgrep, SonarQube, CodeQL                        │
│                                                             │
│  3. DEPENDENCY SCAN (SCA)                                  │
│     ├── Check dependencies for known CVEs                 │
│     └── npm audit, Snyk, Dependabot                       │
│                                                             │
│  4. CONTAINER SCAN                                          │
│     ├── Scan images for vulnerabilities                   │
│     └── Trivy, Grype, Clair                               │
│                                                             │
│  5. CONFIG SCAN                                             │
│     ├── Check Kubernetes YAML for misconfigurations       │
│     └── KubeLinter, Checkov, Kubescape                    │
│                                                             │
│  6. DYNAMIC ANALYSIS (DAST)                                │
│     ├── Test running application                          │
│     └── OWASP ZAP, Burp Suite                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Container Security

### 1. Image Security

```dockerfile
# BAD: Large attack surface, runs as root
FROM ubuntu:latest
RUN apt-get update && apt-get install -y nginx
COPY app /app
CMD ["nginx"]

# GOOD: Minimal image, non-root user
FROM nginx:1.25-alpine
RUN adduser -D -u 1000 appuser
COPY --chown=appuser:appuser app /app
USER appuser
EXPOSE 8080
```

### 2. Image Scanning

```bash
# Trivy - most popular open-source scanner
trivy image nginx:1.25

# Example output:
# nginx:1.25 (debian 12.0)
# Total: 142 (UNKNOWN: 0, LOW: 89, MEDIUM: 45, HIGH: 7, CRITICAL: 1)
```

### 3. Image Signing

```bash
# Sign images to ensure they haven't been tampered with
# Using cosign (sigstore)
cosign sign myregistry/myapp:v1.0

# Verify before deploying
cosign verify myregistry/myapp:v1.0
```

---

## Kubernetes Security

### Common Misconfigurations

```yaml
# BAD: Overly permissive pod
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod
spec:
  containers:
  - name: app
    image: myapp
    securityContext:
      privileged: true          # Never do this!
      runAsUser: 0              # Don't run as root
    volumeMounts:
    - name: host
      mountPath: /host          # Don't mount host filesystem
  volumes:
  - name: host
    hostPath:
      path: /

# GOOD: Secure pod configuration
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: myapp
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
```

### Pod Security Standards

Kubernetes 1.25+ uses Pod Security Standards:

```yaml
# Enforce security standards at namespace level
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

| Level | Description |
|-------|-------------|
| privileged | No restrictions (dangerous) |
| baseline | Minimal restrictions, prevents known escalations |
| restricted | Highly restrictive, follows best practices |

---

## Secret Management

### The Problem

```yaml
# NEVER DO THIS
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_PASSWORD: "supersecret123"  # In Git history forever!
```

### Solutions

```
┌─────────────────────────────────────────────────────────────┐
│              SECRET MANAGEMENT OPTIONS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. External Secret Managers                               │
│     ├── HashiCorp Vault         (most popular)            │
│     ├── AWS Secrets Manager                               │
│     ├── Azure Key Vault                                   │
│     └── Google Secret Manager                             │
│                                                             │
│  2. Kubernetes-Native                                      │
│     ├── Sealed Secrets         (encrypt for Git)          │
│     ├── External Secrets       (sync from managers)       │
│     └── SOPS                   (encrypt YAML files)       │
│                                                             │
│  3. Runtime Injection                                      │
│     ├── Vault Agent Sidecar                              │
│     └── CSI Secret Store Driver                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Sealed Secrets Example

```bash
# Install sealed-secrets controller
# Then create sealed secrets that can be committed to Git

kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# sealed-secret.yaml can be committed
# Only the cluster can decrypt it
```

---

## Network Security

```yaml
# Network Policy: Only allow specific traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

---

## Security Scanning Tools

### KubeLinter (Configuration)

```bash
# Scan Kubernetes YAML for issues
kube-linter lint deployment.yaml

# Example output:
# deployment.yaml: (object: myapp apps/v1, Kind=Deployment)
# - container "app" does not have a read-only root file system
# - container "app" is not set to runAsNonRoot
```

### Kubescape (Comprehensive)

```bash
# Full security scan against frameworks like NSA-CISA
kubescape scan framework nsa

# Scans for:
# - Misconfigurations
# - RBAC issues
# - Network policies
# - Image vulnerabilities
```

### Trivy (Everything)

```bash
# Scan container image
trivy image myapp:v1

# Scan Kubernetes manifests
trivy config .

# Scan running cluster
trivy k8s --report summary cluster
```

---

## Runtime Security

```
┌─────────────────────────────────────────────────────────────┐
│              RUNTIME SECURITY                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Detection: What's happening right now?                    │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Falco (CNCF)                                        │  │
│  │  - Monitors system calls                            │  │
│  │  - Detects anomalous behavior                       │  │
│  │  - Alerts on security events                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Example Falco rules:                                      │
│  - Shell spawned in container                             │
│  - Sensitive file read (/etc/shadow)                      │
│  - Outbound connection to unusual port                    │
│  - Process running as root                                │
│                                                             │
│  Prevention: Stop bad things from happening               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  OPA Gatekeeper / Kyverno                           │  │
│  │  - Policy enforcement                               │  │
│  │  - Admission control                                │  │
│  │  - Block non-compliant resources                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## RBAC Best Practices

```yaml
# Principle of least privilege
# Give only the permissions needed

# BAD: Cluster admin for everything
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: developer-admin
subjects:
- kind: User
  name: developer@company.com
roleRef:
  kind: ClusterRole
  name: cluster-admin    # Too much power!

# GOOD: Namespace-scoped, minimal permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: developer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: development
subjects:
- kind: User
  name: developer@company.com
roleRef:
  kind: Role
  name: developer
```

---

## Did You Know?

- **Over 90% of Kubernetes security incidents** are caused by misconfiguration, not zero-day exploits. Scanning for misconfigurations is more valuable than most people think.

- **The Log4Shell vulnerability (2021)** could have been detected by dependency scanning. Companies with good SCA practices knew within hours which applications were affected.

- **Falco processes billions of events** at companies like Shopify. It can detect a shell being spawned in a container within milliseconds.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Secrets in Git | Permanent exposure | Use secret managers |
| Running as root | Container escape risk | Always runAsNonRoot |
| No network policies | Lateral movement | Default deny policies |
| Latest tag | No vulnerability tracking | Pin specific versions |
| No image scanning | Unknown vulnerabilities | Scan in CI/CD |
| Cluster-admin everywhere | Blast radius | Least privilege RBAC |

---

## Quiz

1. **What does "Shift Left" mean in DevSecOps?**
   <details>
   <summary>Answer</summary>
   Finding security issues earlier in the development lifecycle (closer to code, further from production). Early detection is cheaper and faster to fix than finding issues in production.
   </details>

2. **Why shouldn't containers run as root?**
   <details>
   <summary>Answer</summary>
   If an attacker compromises the container, running as root makes container escape easier. Non-root containers limit the blast radius of a compromise.
   </details>

3. **What's the difference between SAST and DAST?**
   <details>
   <summary>Answer</summary>
   SAST (Static Analysis) scans source code without running it. DAST (Dynamic Analysis) tests the running application. SAST finds coding issues; DAST finds runtime vulnerabilities like SQL injection.
   </details>

4. **What problem do Sealed Secrets solve?**
   <details>
   <summary>Answer</summary>
   Sealed Secrets allow you to store encrypted secrets in Git. Only the cluster can decrypt them. This enables GitOps workflows where everything, including secrets, is version-controlled.
   </details>

---

## Hands-On Exercise

**Task**: Practice Kubernetes security scanning.

```bash
# 1. Create an insecure deployment
cat << 'EOF' > insecure-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insecure-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: insecure
  template:
    metadata:
      labels:
        app: insecure
    spec:
      containers:
      - name: app
        image: nginx:latest
        securityContext:
          privileged: true
          runAsUser: 0
        ports:
        - containerPort: 80
EOF

# 2. Scan with kubectl (basic check)
kubectl apply -f insecure-deployment.yaml --dry-run=server
# Note: This won't catch security issues, just syntax

# 3. If you have trivy installed:
# trivy config insecure-deployment.yaml

# 4. Manual security checklist:
echo "Security Review Checklist:"
echo "[ ] Image uses specific tag (not :latest)"
echo "[ ] Container runs as non-root"
echo "[ ] privileged: false"
echo "[ ] Resource limits set"
echo "[ ] readOnlyRootFilesystem: true"
echo "[ ] Capabilities dropped"

# 5. Create a secure version
cat << 'EOF' > secure-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secure
  template:
    metadata:
      labels:
        app: secure
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: app
        image: nginx:1.25-alpine
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        ports:
        - containerPort: 8080
        resources:
          limits:
            memory: "128Mi"
            cpu: "500m"
          requests:
            memory: "64Mi"
            cpu: "250m"
EOF

# 6. Compare the two
echo "=== Insecure vs Secure ==="
diff insecure-deployment.yaml secure-deployment.yaml || true

# 7. Cleanup
rm insecure-deployment.yaml secure-deployment.yaml
```

**Success criteria**: Understand insecure vs secure configurations.

---

## Summary

**DevSecOps** integrates security into every stage:

**Key concepts**:
- Shift Left: Find issues early
- Security as code
- Automated scanning
- Least privilege

**CI/CD security**:
- SAST: Scan source code
- SCA: Scan dependencies
- Container scanning: Scan images
- Config scanning: Scan Kubernetes YAML

**Kubernetes security**:
- Pod Security Standards
- Network Policies
- RBAC (least privilege)
- Secret management

**Tools**:
- Trivy: Images and configs
- KubeLinter/Kubescape: K8s configs
- Falco: Runtime detection
- Vault/Sealed Secrets: Secret management

**Mindset**: Security is everyone's job, not just the security team's.

---

## Track Complete!

Congratulations! You've finished the **Modern DevOps Practices** prerequisite track. You now understand:

1. Infrastructure as Code
2. GitOps workflows
3. CI/CD pipelines
4. Observability fundamentals
5. Platform Engineering concepts
6. Security practices (DevSecOps)

**Next Steps**:
- [CKA Curriculum](../../k8s/cka/part0-environment/module-0.1-cluster-setup/) - Administrator certification
- [CKAD Curriculum](../../k8s/ckad/part0-environment/module-0.1-ckad-overview/) - Developer certification
- [Philosophy & Design](../philosophy-design/module-1.1-why-kubernetes-won/) - Why Kubernetes?
