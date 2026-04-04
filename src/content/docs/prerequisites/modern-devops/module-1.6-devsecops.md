---
title: "Module 1.6: Security Practices (DevSecOps)"
slug: prerequisites/modern-devops/module-1.6-devsecops
sidebar:
  order: 7
---
> **Complexity**: `[MEDIUM]` - Essential security mindset
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: CI/CD concepts (Module 3)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Explain** the "shift left" security principle and why it's cheaper to catch issues early
- **Identify** the top Kubernetes security risks (misconfiguration, exposed dashboards, excessive RBAC)
- **Describe** a secure CI/CD pipeline with image scanning, secret management, and policy enforcement
- **Compare** DevSecOps tools (Trivy, OPA/Gatekeeper, Falco) and explain what each protects against
- **Configure** Pod Security Standards (PSS) to restrict container privileges at the namespace level
- **Set up** pre-commit scanning concepts to prevent secret leaks before they reach version control
- **Write** a NetworkPolicy to explicitly control and restrict pod-to-pod traffic

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

> **Stop and think**: If a developer hardcodes a password in a feature branch, at what stage of the pipeline should it ideally be caught to minimize cost and risk?

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

> **Pause and predict**: If you apply a default-deny NetworkPolicy to a namespace, what happens to the existing pods that are currently communicating with each other?

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

- **Over 90% of Kubernetes security incidents** are caused by misconfiguration, not zero-day exploits. The infamous 2018 Tesla breach happened simply because an administrative Kubernetes dashboard was left exposed to the internet without a password.
- **The Capital One Breach (2019)** resulted in the theft of 100 million credit card applications due to an overly permissive IAM role, highlighting exactly why the principle of least privilege (like strict RBAC) is critical.
- **The Codecov Supply Chain Attack (2021)** occurred when attackers modified a bash script to exfiltrate CI/CD environment variables, emphasizing why secret management and dependency scanning must be integrated into pipelines.
- **Falco processes billions of events** at companies like Shopify. At that scale, it can detect a malicious anomaly—like a shell being unexpectedly spawned in a production container—within milliseconds.

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

1. **Your team is planning a new microservice. The lead developer suggests running security scans only on the final container image right before production deployment to save CI time. Why is this approach risky in a DevSecOps culture?**
   <details>
   <summary>Answer</summary>
   This approach violates the "Shift Left" principle, which advocates finding security issues as early in the development lifecycle as possible. Waiting until the final container image is built means any discovered vulnerabilities (like outdated dependencies or insecure code) will require sending the work all the way back to the development phase. Fixing issues in production or staging is significantly more expensive and time-consuming than catching them during local development or at the pull request stage. By shifting left, teams can address flaws when the context is still fresh in the developer's mind.
   </details>

2. **A developer creates a Pod manifest that sets `runAsUser: 0` because their application needs to install a package at startup. If this container is compromised, what is the primary risk, and how should it be mitigated?**
   <details>
   <summary>Answer</summary>
   Setting `runAsUser: 0` means the container runs as the root user, which creates a severe security risk if an attacker gains execution capabilities inside the container. If a vulnerability is exploited, the attacker would have root-level permissions, making it much easier to escape the container boundary and compromise the underlying Kubernetes worker node. To mitigate this, the container image should be built with all necessary packages installed during the CI phase, not at runtime. The Pod manifest should enforce `runAsNonRoot: true` and specify a non-privileged user ID to limit the blast radius of any potential compromise.
   </details>

3. **You need to implement security checks in your CI/CD pipeline. Your manager asks you to choose between SAST (Static Application Security Testing) and DAST (Dynamic Application Security Testing) because of budget constraints. How do you explain the different threats each one addresses?**
   <details>
   <summary>Answer</summary>
   SAST and DAST are complementary tools that address different types of security threats, so choosing only one leaves a significant blind spot. SAST analyzes the static source code before it is compiled or run, making it excellent for catching hardcoded secrets, dangerous function calls, and logic flaws early in the development cycle. Conversely, DAST interacts with the running application from the outside, simulating an attacker to find runtime vulnerabilities like cross-site scripting (XSS), misconfigured HTTP headers, or authentication bypasses. Because they evaluate the application in entirely different states, a robust DevSecOps pipeline requires both to ensure comprehensive coverage.
   </details>

4. **A junior engineer proposes committing a Kubernetes `Secret` manifest containing database credentials directly to the Git repository, arguing that the repository is private and secure. What is the fundamental flaw in this reasoning, and what is a better alternative?**
   <details>
   <summary>Answer</summary>
   Committing raw secrets to any version control system, even a private one, is fundamentally flawed because Git retains a permanent history of all changes. Once a secret is committed, anyone with read access to the repository—or anyone who gains access in the future—can retrieve the credentials from the commit history, even if the file is later deleted. A better alternative is to use a tool like Sealed Secrets, which uses asymmetric cryptography to encrypt the secret so that it can be safely committed to Git. Only the Kubernetes cluster holds the private key required to decrypt the SealedSecret back into a usable Kubernetes Secret object.
   </details>

5. **Your organization wants to enforce a policy where no pods can run in the `production` namespace with privileged access or host-level mounts. How can you implement this natively in Kubernetes 1.25+ without installing third-party admission controllers?**
   <details>
   <summary>Answer</summary>
   You can achieve this natively by configuring Pod Security Standards (PSS) at the namespace level using specific labels. By applying the label `pod-security.kubernetes.io/enforce: restricted` to the `production` namespace, the Kubernetes built-in admission controller will automatically reject any Pod creation requests that violate the restricted profile. This profile explicitly forbids privileged containers, host network namespaces, and hostpath volumes, among other insecure configurations. This native approach requires no additional tooling and ensures that misconfigured pods are blocked before they are ever scheduled onto a node.
   </details>

6. **A developer accidentally commits an AWS access key to their local Git repository. They realize the mistake before pushing to the remote repository, but they want to ensure this never happens again. What DevSecOps practice should be implemented to prevent this specific scenario?**
   <details>
   <summary>Answer</summary>
   The team should implement pre-commit scanning using a tool like `git-secrets` or `trufflehog` configured to run as a Git pre-commit hook. This practice intercepts the commit process locally on the developer's machine and scans the staged files for patterns matching known sensitive data formats, such as API keys or passwords. If a secret is detected, the hook aborts the commit, providing immediate feedback to the developer and preventing the secret from ever entering the local Git history. This is a prime example of "shifting left," as it addresses the vulnerability at the earliest possible moment in the development lifecycle.
   </details>

7. **An attacker compromises a frontend web pod and immediately attempts to connect to the backend database pod on port 5432. By default, Kubernetes allows this traffic. What specific resource must you write to block this unauthorized lateral movement?**
   <details>
   <summary>Answer</summary>
   You must write a Kubernetes `NetworkPolicy` resource to explicitly control and restrict pod-to-pod communication. By default, all pods in a Kubernetes cluster can communicate with each other freely, which facilitates lateral movement during a breach. By defining a default-deny NetworkPolicy and then explicitly allowing only ingress traffic from the frontend pod to the database pod on port 5432, you create a zero-trust network boundary. This ensures that even if an attacker compromises a pod in a different part of the cluster, they cannot reach the database because the network layer will drop the unauthorized packets.
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