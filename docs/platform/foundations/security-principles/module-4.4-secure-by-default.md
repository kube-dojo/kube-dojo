# Module 4.4: Secure by Default

> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: [Module 4.3: Identity and Access Management](module-4.3-identity-and-access.md)
>
> **Track**: Foundations

---

**January 2017. Security researchers discover 27,000 MongoDB databases exposed to the internet.**

No exploit was needed. MongoDB's default configuration bound to all network interfaces (0.0.0.0) with authentication disabled. Install MongoDB, start it, and the entire database is accessible to anyone on the internet.

Attackers ran automated scripts across the internet, finding these databases, deleting the contents, and leaving ransom notes demanding Bitcoin for data recovery. Many victims had no backups. Some databases contained medical records, customer data, and financial information.

**Over 28,000 MongoDB instances were ransomed in the first wave alone.** The total data loss was incalculable. And the root cause wasn't a bug or vulnerability—it was the default configuration.

MongoDB changed their defaults. New installations bind to localhost only. Authentication is strongly encouraged during setup. But thousands of organizations had already learned the hard way: insecure defaults become insecure deployments.

This module teaches secure by default—how to build systems where the easy path is also the safe path.

---

## Why This Module Matters

Most security breaches don't exploit sophisticated zero-days. They exploit misconfigurations, default passwords, and forgotten settings. The attacker didn't have to be clever—they just found what was left open.

**Secure by default** means systems ship in a secure state. Instead of requiring users to enable security, they have to explicitly disable it. Instead of hoping developers remember to validate input, the framework does it automatically.

This module teaches you how to build systems where the path of least resistance is also the secure path—where doing things the easy way is also doing them safely.

> **The Seatbelt Analogy**
>
> Old cars required you to find the seatbelt and buckle it. Many people didn't. Modern cars beep until you buckle up—the annoying path is the unsafe path. Some won't even start until passengers are buckled. The default became safe, and the unsafe choice became harder.

---

## What You'll Learn

- What "secure by default" means in practice
- How to design secure defaults for configurations
- Common insecure defaults and how to fix them
- Security guardrails that prevent mistakes
- How Kubernetes implements secure defaults

---

## Part 1: The Secure Default Philosophy

### 1.1 Default State Matters

```
THE IMPORTANCE OF DEFAULTS
═══════════════════════════════════════════════════════════════

INSECURE BY DEFAULT
─────────────────────────────────────────────────────────────
    Installation → Everything open
    User must manually secure each setting

    ┌────────────────────────────────────────────────────────┐
    │ Default Settings:                                      │
    │   Admin password: admin                                │
    │   API authentication: disabled                         │
    │   Encryption: disabled                                 │
    │   Firewall: allow all                                  │
    │   Debug mode: enabled                                  │
    │                                                        │
    │ "Please secure before production use"                  │
    │                                                        │
    │ Reality: Most users don't.                            │
    └────────────────────────────────────────────────────────┘

SECURE BY DEFAULT
─────────────────────────────────────────────────────────────
    Installation → Everything locked down
    User must explicitly open what's needed

    ┌────────────────────────────────────────────────────────┐
    │ Default Settings:                                      │
    │   Admin password: must be set on first run            │
    │   API authentication: required                         │
    │   Encryption: TLS enabled                             │
    │   Firewall: deny all (allowlist needed)               │
    │   Debug mode: disabled                                 │
    │                                                        │
    │ "Enable features as needed"                           │
    │                                                        │
    │ Reality: Security happens automatically.              │
    └────────────────────────────────────────────────────────┘
```

### 1.2 Why Secure Defaults Win

| Factor | Insecure Default | Secure Default |
|--------|------------------|----------------|
| **Setup friction** | Easy setup, insecure | Slightly harder, but safe |
| **User expertise** | Requires security knowledge | Works for everyone |
| **Forgotten configs** | Become attack vectors | Remain safe |
| **Time pressure** | "We'll secure later" (won't) | Already secure |
| **Audit findings** | Many defaults insecure | Clean by default |

> **Try This (2 minutes)**
>
> Think of software you've installed. What were the defaults?
>
> | Software | Default Setting | Secure? |
> |----------|----------------|---------|
> | | | |
> | | | |
> | | | |
>
> How many required you to manually enable security?

---

## Part 2: Designing Secure Defaults

### 2.1 Authentication Defaults

```
AUTHENTICATION DEFAULTS
═══════════════════════════════════════════════════════════════

PASSWORDS
─────────────────────────────────────────────────────────────
    ✗ Default password: "admin" or "password"
    ✗ No password required initially
    ✓ Force password set on first use
    ✓ Require minimum complexity

    # Good: Force password creation
    if not user.has_password_set():
        redirect('/setup/create-password')

API ACCESS
─────────────────────────────────────────────────────────────
    ✗ API accessible without authentication
    ✗ Optional authentication ("can be enabled")
    ✓ Authentication required by default
    ✓ All endpoints protected unless explicitly public

    # Framework level default
    @require_auth  # Applied to all routes by default
    class APIView:
        pass

    @public  # Must explicitly mark as public
    class HealthCheck:
        pass

SESSION MANAGEMENT
─────────────────────────────────────────────────────────────
    ✗ Sessions never expire
    ✗ Long session timeouts (30 days)
    ✓ Reasonable session timeout (hours, not days)
    ✓ Secure cookie flags by default (HttpOnly, Secure, SameSite)
```

### 2.2 Network Defaults

```
NETWORK DEFAULTS
═══════════════════════════════════════════════════════════════

BINDING
─────────────────────────────────────────────────────────────
    ✗ Listen on 0.0.0.0 (all interfaces)
    ✓ Listen on localhost by default
    ✓ Require explicit config to expose externally

    # Dangerous default
    server.listen('0.0.0.0', 8080)  # World-accessible

    # Secure default
    server.listen('127.0.0.1', 8080)  # Local only
    # User must configure to expose

ENCRYPTION
─────────────────────────────────────────────────────────────
    ✗ Plain HTTP by default
    ✗ TLS "optional"
    ✓ TLS required by default
    ✓ Modern TLS versions only (1.2+)
    ✓ Strong cipher suites only

FIREWALL / NETWORK POLICY
─────────────────────────────────────────────────────────────
    ✗ Allow all traffic
    ✗ No firewall rules
    ✓ Deny all by default
    ✓ Explicit allowlist required
```

### 2.3 Data Defaults

```
DATA DEFAULTS
═══════════════════════════════════════════════════════════════

ENCRYPTION
─────────────────────────────────────────────────────────────
    ✗ Store data in plain text
    ✗ Encryption available but not enabled
    ✓ Encryption at rest by default
    ✓ Encryption in transit required

LOGGING
─────────────────────────────────────────────────────────────
    ✗ Log everything including secrets
    ✗ No log sanitization
    ✓ Automatic secret redaction
    ✓ PII filtering by default

    # Automatic redaction
    logger.info("User login", extra={
        "username": user.email,      # Logged
        "password": user.password,   # [REDACTED]
        "api_key": request.api_key   # [REDACTED]
    })

INPUT HANDLING
─────────────────────────────────────────────────────────────
    ✗ Trust all input
    ✗ Validation optional
    ✓ Validate and sanitize all input by default
    ✓ Parameterized queries enforced (no string concatenation)

    # Framework prevents SQL injection by default
    users = db.query(User).filter_by(email=email).all()
    # Not: f"SELECT * FROM users WHERE email = '{email}'"
```

---

## Part 3: Guardrails and Constraints

### 3.1 What are Guardrails?

```
GUARDRAILS
═══════════════════════════════════════════════════════════════

Guardrails are constraints that prevent mistakes without
blocking legitimate work.

HIGHWAY GUARDRAILS
─────────────────────────────────────────────────────────────
    - Don't slow you down during normal driving
    - Prevent you from going off a cliff
    - You hit them only when something goes wrong

SECURITY GUARDRAILS
─────────────────────────────────────────────────────────────
    - Don't block normal development
    - Prevent dangerous configurations
    - You notice them only when doing something risky

EXAMPLES
─────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────┐
│ CI/CD Pipeline:                                            │
│   ✓ Allows all normal deployments                         │
│   ✗ Blocks deployment without security scan               │
│   ✗ Blocks deployment of containers as root               │
│   ✗ Blocks deployment with critical vulnerabilities       │
│                                                            │
│ Policy as Code:                                            │
│   ✓ Allows pods with security context                     │
│   ✗ Blocks pods without resource limits                   │
│   ✗ Blocks pods with hostNetwork: true                    │
│   ✗ Blocks images from untrusted registries               │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Implementing Guardrails

```
GUARDRAIL IMPLEMENTATION
═══════════════════════════════════════════════════════════════

PRE-COMMIT HOOKS
─────────────────────────────────────────────────────────────
Stop problems before they're committed.

    # .pre-commit-config.yaml
    repos:
    - repo: https://github.com/gitleaks/gitleaks
      hooks:
      - id: gitleaks  # Prevent committing secrets

    - repo: https://github.com/hadolint/hadolint
      hooks:
      - id: hadolint  # Lint Dockerfiles for security

CI PIPELINE GATES
─────────────────────────────────────────────────────────────
Stop problems before they're merged.

    pipeline:
      - security-scan:
          fail_on: CRITICAL, HIGH
      - container-scan:
          fail_on: CVE score > 7.0
      - policy-check:
          policies: [no-root, resource-limits, no-privileged]

ADMISSION CONTROLLERS
─────────────────────────────────────────────────────────────
Stop problems before they're deployed.

    # OPA Gatekeeper, Kyverno
    Block at the Kubernetes API:
    - Pods without security context
    - Containers running as root
    - Images from unauthorized registries
    - Resources without limits
```

### 3.3 Kubernetes Pod Security Standards

```
POD SECURITY STANDARDS
═══════════════════════════════════════════════════════════════

Kubernetes defines three security levels:

PRIVILEGED (No restrictions)
─────────────────────────────────────────────────────────────
    For system-level workloads that need full access.
    Use only when necessary.

BASELINE (Minimal restrictions)
─────────────────────────────────────────────────────────────
    Prevents known privilege escalations.
    Blocks: hostNetwork, hostPID, privileged containers

RESTRICTED (Maximum security)
─────────────────────────────────────────────────────────────
    Enforces security best practices.
    Requires: non-root, drop all capabilities,
              read-only root filesystem

APPLYING STANDARDS
─────────────────────────────────────────────────────────────
# Namespace-level enforcement
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted

# Now all pods in production must meet restricted standard
```

> **War Story: The $2.3 Million Privileged Container**
>
> **September 2022.** A developer at a healthcare technology company needed to debug a production networking issue. "I'll just run a privileged container real quick to capture network traffic." They deployed with `privileged: true`, fixed the issue, and moved on to the next ticket. The privileged container stayed running.
>
> Eight months later, attackers exploited a Log4j vulnerability in a different service running on the same node. Normally, container isolation would have limited the blast radius. But the attacker discovered the privileged container.
>
> **With `privileged: true`, the container had full access to the host.** The attacker escaped the container, accessed the node's filesystem, read Kubernetes secrets for 47 other services, and exfiltrated patient health records for 340,000 individuals.
>
> **The breach cost $2.3 million** in HIPAA fines, breach notification, credit monitoring, and forensic investigation. The company was required to implement comprehensive security controls and submit to three years of audits.
>
> After the breach, the team implemented Pod Security Standards with `enforce: restricted` on all production namespaces. Now `privileged: true` is blocked at admission—the developer would have gotten an immediate error instead of a deployed vulnerability sitting dormant for eight months.

---

## Part 4: Secure Configuration Management

### 4.1 Configuration as Code

```
CONFIGURATION MANAGEMENT
═══════════════════════════════════════════════════════════════

ANTI-PATTERN: Manual configuration
─────────────────────────────────────────────────────────────
    - SSH into server
    - Edit config file
    - Restart service
    - Hope you didn't break anything
    - No record of what changed

    Problems:
    - Configuration drift between environments
    - No audit trail
    - Easy to make mistakes
    - Hard to reproduce

PATTERN: Configuration as code
─────────────────────────────────────────────────────────────
    - All configuration in version control
    - Changes go through pull request
    - Automated deployment
    - Full history of changes

    Benefits:
    - Identical configuration across environments
    - Review before apply
    - Easy rollback
    - Audit trail
```

### 4.2 Secrets Management

```
SECRETS MANAGEMENT
═══════════════════════════════════════════════════════════════

WRONG: Secrets in config files
─────────────────────────────────────────────────────────────
    # config.yaml (checked into git!)
    database:
      password: "super_secret_password"

    Problems:
    - Visible to anyone with repo access
    - In git history forever
    - Same secret across environments

RIGHT: External secrets management
─────────────────────────────────────────────────────────────
    # config.yaml
    database:
      password: ${DATABASE_PASSWORD}  # From environment

    # Even better: from secrets manager
    database:
      password_path: vault://secret/db/password

KUBERNETES SECRETS
─────────────────────────────────────────────────────────────
    # Still not great: base64 encoded, not encrypted
    apiVersion: v1
    kind: Secret
    data:
      password: c3VwZXJfc2VjcmV0  # Just base64!

    # Better: External Secrets Operator
    apiVersion: external-secrets.io/v1beta1
    kind: ExternalSecret
    spec:
      secretStoreRef:
        name: vault
      target:
        name: db-credentials
      data:
      - secretKey: password
        remoteRef:
          key: secret/db/password
```

### 4.3 Immutable Infrastructure

```
IMMUTABLE INFRASTRUCTURE
═══════════════════════════════════════════════════════════════

MUTABLE (Traditional)
─────────────────────────────────────────────────────────────
    Deploy server → Update in place → Update again → ...

    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Server   │──▶│ Updated  │──▶│ Updated  │
    │ v1       │   │ v1.1     │   │ v1.2     │
    └──────────┘   └──────────┘   └──────────┘

    Problems:
    - Configuration drift
    - "Works on my machine"
    - Security patches inconsistent
    - Hard to know current state

IMMUTABLE
─────────────────────────────────────────────────────────────
    Build image → Deploy → Replace (never update)

    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │ Image v1 │        │ Image v2 │        │ Image v3 │
    └────┬─────┘        └────┬─────┘        └────┬─────┘
         │   Delete          │   Delete          │
    ┌────▼─────┐        ┌────▼─────┐        ┌────▼─────┐
    │ Server A │        │ Server B │        │ Server C │
    └──────────┘        └──────────┘        └──────────┘

    Benefits:
    - Reproducible deployments
    - Known state at all times
    - Easy rollback (deploy previous image)
    - Security: can't modify running container
```

> **Try This (3 minutes)**
>
> Audit your configuration:
>
> | Configuration | In Version Control? | Has Secrets? | Secure? |
> |---------------|--------------------|--------------|---------|
> | App config | | | |
> | Infrastructure | | | |
> | CI/CD pipelines | | | |
> | Kubernetes manifests | | | |

---

## Part 5: Security by Design Patterns

### 5.1 Secure Framework Patterns

```
SECURE FRAMEWORK PATTERNS
═══════════════════════════════════════════════════════════════

AUTO-ESCAPING (XSS Prevention)
─────────────────────────────────────────────────────────────
    # Django template - auto-escapes by default
    {{ user_input }}  →  &lt;script&gt;...

    # To allow HTML, must explicitly disable
    {{ user_input|safe }}  # Developer knows they're taking risk

PARAMETERIZED QUERIES (SQL Injection Prevention)
─────────────────────────────────────────────────────────────
    # ORM forces parameterization
    User.objects.filter(email=user_email)  # Safe

    # Raw SQL requires explicit params
    cursor.execute("SELECT * FROM users WHERE email = %s", [email])

    # String formatting errors immediately
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
    # ^ Framework should warn or error

CSRF PROTECTION
─────────────────────────────────────────────────────────────
    # Framework adds CSRF token to forms automatically
    <form method="post">
        {% csrf_token %}  <!-- Auto-injected -->
        ...
    </form>

    # POST without valid token is rejected by default
```

### 5.2 Secure API Patterns

```
SECURE API PATTERNS
═══════════════════════════════════════════════════════════════

AUTHENTICATION REQUIRED BY DEFAULT
─────────────────────────────────────────────────────────────
    # All routes require auth unless marked public
    @app.route('/api/users')
    @require_auth  # Applied globally
    def get_users():
        pass

    @app.route('/health')
    @public  # Explicit opt-out
    def health_check():
        return 'OK'

RATE LIMITING BY DEFAULT
─────────────────────────────────────────────────────────────
    # Default rate limit for all endpoints
    app.config['RATELIMIT_DEFAULT'] = "100/minute"

    # Specific endpoints can override
    @app.route('/api/expensive')
    @rate_limit("10/minute")  # Stricter
    def expensive_operation():
        pass

INPUT VALIDATION BY DEFAULT
─────────────────────────────────────────────────────────────
    # Pydantic, Marshmallow, etc.
    class UserInput(BaseModel):
        email: EmailStr        # Must be valid email
        age: int = Field(ge=0, le=150)  # Bounded integer

    @app.route('/api/users', methods=['POST'])
    def create_user(user: UserInput):  # Auto-validated
        pass  # Only reaches here if input is valid
```

### 5.3 Secure Deployment Patterns

```
SECURE DEPLOYMENT PATTERNS
═══════════════════════════════════════════════════════════════

MINIMAL BASE IMAGES
─────────────────────────────────────────────────────────────
    # Bad: Full OS with unnecessary packages
    FROM ubuntu:22.04
    # Contains: bash, curl, wget, apt, hundreds of packages

    # Better: Minimal base
    FROM alpine:3.18
    # Contains: minimal shell, busybox utilities

    # Best: Distroless (no shell at all)
    FROM gcr.io/distroless/static
    # Contains: only what your app needs
    # Attacker can't run shell commands if there's no shell

NON-ROOT BY DEFAULT
─────────────────────────────────────────────────────────────
    # Dockerfile
    FROM node:20-alpine

    # Create non-root user
    RUN addgroup -S app && adduser -S app -G app

    # Set ownership
    COPY --chown=app:app . /app
    WORKDIR /app

    # Run as non-root
    USER app
    CMD ["node", "server.js"]

READ-ONLY FILESYSTEM
─────────────────────────────────────────────────────────────
    # Kubernetes deployment
    spec:
      containers:
      - name: app
        securityContext:
          readOnlyRootFilesystem: true
        volumeMounts:
        - name: tmp
          mountPath: /tmp  # Writable temp if needed
      volumes:
      - name: tmp
        emptyDir: {}
```

---

## Did You Know?

- **MongoDB's default config** used to bind to 0.0.0.0 with no authentication. In 2017, 27,000+ MongoDB instances were found exposed and ransomed. Now it binds to localhost by default.

- **AWS S3 bucket ACLs** defaulted to private for years, but complex permission systems led to many accidental public exposures. In 2023, AWS added "Block Public Access" settings that default to blocking all public access.

- **Kubernetes 1.25** removed Pod Security Policies (PSP) in favor of Pod Security Standards (PSS), which are simpler and enabled by default in new namespaces.

- **The Docker Hub default** of pulling `latest` tag has caused countless production incidents. The tag is mutable—meaning `nginx:latest` today might be a completely different image than `nginx:latest` tomorrow. Secure by default means pinning to immutable digests like `nginx@sha256:abc123...`, which is why many organizations now enforce digest-based image references in admission policies.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| "We'll secure it later" | Later never comes | Secure by default from start |
| Default admin credentials | Easy target | Force credential setup |
| Debug mode in production | Exposes internals | Disable unless explicitly enabled |
| Overly permissive CORS | XSS exposure | Explicit allowed origins |
| No resource limits | DoS vulnerability | Limits required by policy |
| Trust all registries | Malicious images | Allowlist registries |

---

## Quiz

1. **Why is "secure by default" more effective than "security checklist"?**
   <details>
   <summary>Answer</summary>

   A security checklist requires active effort—someone must remember to check each item. Items get skipped under time pressure, forgotten during updates, or missed by new team members.

   Secure by default means security happens automatically:
   - No action required to be secure
   - Must take explicit action to be insecure
   - Works for experts and beginners alike
   - Survives staff turnover
   - Can't be skipped under pressure

   Example: A checklist says "configure firewall rules." Secure by default means the firewall denies all traffic until rules are added. The checklist can be ignored; the default cannot.
   </details>

2. **What's the difference between a guardrail and a gate?**
   <details>
   <summary>Answer</summary>

   **Guardrails** prevent you from going off course while allowing normal movement. They're passive—you don't notice them until you hit them.
   - Example: Pod Security Standards that block privileged containers
   - Normal deployments pass through; only dangerous ones are stopped

   **Gates** are checkpoints everyone must pass through. They're active—everyone interacts with them.
   - Example: Manual security review required for every PR
   - All deployments wait; throughput slows

   Best practice: Use guardrails for common risks (automated, scalable) and gates for high-stakes decisions (manual review when warranted). Too many gates slow everything down; too few guardrails let problems through.
   </details>

3. **How does immutable infrastructure improve security?**
   <details>
   <summary>Answer</summary>

   Immutable infrastructure improves security several ways:

   1. **Known state**: Servers match the deployed image exactly. No configuration drift or unknown modifications.

   2. **No persistent attackers**: Attackers can't install backdoors that survive deployment. Next deploy starts fresh.

   3. **Easy patching**: Deploy new image with patches. No complex in-place upgrade process.

   4. **Forensics**: Can compare running container to original image to detect modifications.

   5. **Reduced attack surface**: Read-only filesystems prevent attackers from writing malicious files.

   With mutable infrastructure, an attacker who gains access can modify the system and persist. With immutable, they're removed on next deploy.
   </details>

4. **Why should secrets never be in version control?**
   <details>
   <summary>Answer</summary>

   Version control creates permanent, searchable history:

   1. **History is forever**: Even if you delete a secret, it's in git history. Anyone with repo access can find it.

   2. **Broad access**: Many people have repo access who shouldn't have production secrets.

   3. **Forks and clones**: Secrets spread to every fork, every developer's machine.

   4. **No rotation**: Secrets in code are hard to rotate. Change requires redeploy.

   5. **Audit**: No log of who accessed the secret—anyone who cloned the repo has it.

   Instead:
   - Use environment variables (for simple cases)
   - Use secrets managers (Vault, AWS Secrets Manager)
   - Use Kubernetes ExternalSecrets to sync from secrets manager
   - Reference secrets by path/name, not value
   </details>

5. **An organization deploys 500 new services per month. Each deployment has a 5% chance of having a misconfiguration if checked manually. With automated guardrails, the chance drops to 0.1%. Over a year, how many misconfigurations does each approach produce?**
   <details>
   <summary>Answer</summary>

   **Manual checks:**

   - Services per year: 500 × 12 = 6,000
   - Misconfigurations: 6,000 × 0.05 = **300 misconfigurations per year**

   **Automated guardrails:**

   - Services per year: 6,000
   - Misconfigurations: 6,000 × 0.001 = **6 misconfigurations per year**

   **Difference: 294 fewer misconfigurations per year**

   This illustrates why secure by default scales:
   - Manual processes degrade under volume and time pressure
   - Automated checks run consistently on every deployment
   - Small percentage improvements compound across thousands of deployments
   - Security doesn't depend on individual vigilance

   If each misconfiguration has a 10% chance of being exploited and costs $50,000 on average:
   - Manual: 300 × 0.1 × $50,000 = $1.5M expected annual cost
   - Automated: 6 × 0.1 × $50,000 = $30K expected annual cost
   </details>

6. **The MongoDB ransomware attacks exploited databases binding to 0.0.0.0 by default. What "secure by default" changes would have prevented this, and what trade-offs do they create?**
   <details>
   <summary>Answer</summary>

   **Secure default changes:**

   1. **Bind to localhost (127.0.0.1) by default**
      - Trade-off: Remote connections require explicit configuration
      - Users must know to change the bind address for legitimate remote access

   2. **Require authentication setup during installation**
      - Trade-off: Adds friction to getting started
      - Development/testing environments need extra steps

   3. **Block external connections until auth is configured**
      - Trade-off: Can't run a quick test database remotely
      - Local development is easy; production requires configuration

   4. **Warning messages when running in insecure mode**
      - Trade-off: Noise in development environments
      - Can be ignored (but at least it's explicit)

   **The principle:**

   Secure by default shifts the burden:
   - Before: Easy to run insecurely, hard to run securely
   - After: Easy to run securely, requires effort to run insecurely

   The trade-off is intentional friction. Users who need insecure configurations (development, isolated networks) must explicitly choose them. Users who don't know better are protected by default.
   </details>

7. **A framework auto-escapes HTML output by default. Why is it better to require developers to explicitly mark unsafe output with `|safe` rather than requiring them to explicitly escape output?**
   <details>
   <summary>Answer</summary>

   **Forgetting has different consequences:**

   **If escaping is opt-in (insecure default):**
   - Developer forgets to escape → XSS vulnerability
   - Mistakes create security holes
   - Every template is a potential vulnerability
   - Must review all code for missing escaping

   **If raw output is opt-in (secure default):**
   - Developer forgets to mark as safe → Broken HTML display
   - Mistakes create visual bugs, not security holes
   - Vulnerabilities only possible where `|safe` is used
   - Security review focuses on explicit `|safe` usage

   **The key insight:**

   With secure defaults, mistakes fail safe:
   - Forgotten escaping → Content renders as literal text `&lt;script&gt;`
   - User sees broken display, reports bug, developer fixes it
   - No security impact

   With insecure defaults, mistakes fail dangerous:
   - Forgotten escaping → XSS attack possible
   - User might not notice
   - Attacker notices, exploits it

   The same principle applies to: parameterized queries (prevent SQL injection by default), CSRF tokens (validated by default), authentication (required by default).
   </details>

8. **A Kubernetes deployment uses `image: nginx:latest`. Why is this insecure by default, and what should be used instead?**
   <details>
   <summary>Answer</summary>

   **Problems with `nginx:latest`:**

   1. **Mutable tag**: `latest` points to different images over time. The image running today might not be the image running after a restart.

   2. **No reproducibility**: Can't rebuild the exact same deployment. `latest` six months ago is different from `latest` today.

   3. **Surprise changes**: Nginx might update `latest` to a new major version with breaking changes or new vulnerabilities.

   4. **No audit trail**: Can't determine what image was running at a specific time.

   5. **Supply chain risk**: If an attacker compromises the `latest` tag, all future pulls get the malicious image.

   **Secure alternatives:**

   ```yaml
   # Good: Specific version tag
   image: nginx:1.25.3

   # Better: Include variant
   image: nginx:1.25.3-alpine

   # Best: Immutable digest
   image: nginx@sha256:abc123def456...
   ```

   **Why digests are best:**

   - `sha256` digest is a content hash—if the image changes, the hash changes
   - Completely immutable—you always get exactly this image
   - Can't be overwritten by attackers
   - Admission controllers can enforce digest-based images

   Trade-off: Updating requires changing the digest in manifests. This is a feature—updates are explicit and trackable.
   </details>

---

## Hands-On Exercise

**Task**: Implement secure defaults for a Kubernetes deployment.

**Scenario**: You have this insecure deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: myapp:latest
        ports:
        - containerPort: 8080
```

**Part 1: Identify Security Issues (5 minutes)**

List everything wrong with this deployment:

| Issue | Risk | Severity |
|-------|------|----------|
| | | |
| | | |
| | | |
| | | |
| | | |

**Part 2: Fix the Deployment (15 minutes)**

Rewrite with secure defaults:

```yaml
# Your secure deployment here
```

**Part 3: Add Network Policy (10 minutes)**

Create a NetworkPolicy that:
- Denies all ingress by default
- Allows only from specific sources

```yaml
# Your NetworkPolicy here
```

**Part 4: Add Pod Security (10 minutes)**

Create namespace labels to enforce restricted pod security:

```yaml
# Your Namespace with pod security labels
```

**Success Criteria**:
- [ ] Identified at least 5 security issues in original deployment
- [ ] Fixed deployment includes: non-root user, read-only fs, resource limits, image tag (not latest), security context
- [ ] Network policy implements default deny
- [ ] Namespace enforces restricted pod security standard

**Sample Solution**:

<details>
<summary>Show secure deployment</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      serviceAccountName: web-app
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: web
        image: myapp:v1.2.3@sha256:abc123...  # Pinned
        ports:
        - containerPort: 8080
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
      volumes:
      - name: tmp
        emptyDir: {}
```

</details>

---

## Further Reading

- **"Building Secure and Reliable Systems"** - Google. Comprehensive guide to building secure systems from the ground up.

- **"Container Security"** - Liz Rice. Essential reading for securing containerized applications.

- **CIS Benchmarks** - cisecurity.org. Industry-standard secure configuration baselines for various platforms.

---

## Key Takeaways Checklist

Before moving on, verify you can answer these:

- [ ] Can you explain why secure by default is more effective than security checklists?
- [ ] Do you understand the difference between guardrails (passive blockers) and gates (active checkpoints)?
- [ ] Can you describe secure defaults for authentication, networking, and data?
- [ ] Do you understand Pod Security Standards (Privileged, Baseline, Restricted) and how to enforce them?
- [ ] Can you explain why secrets should never be in version control and what to use instead?
- [ ] Do you understand immutable infrastructure and why it improves security?
- [ ] Can you explain secure framework patterns (auto-escaping, parameterized queries, CSRF tokens)?
- [ ] Do you understand why `image:latest` is insecure and what to use instead?

---

## Track Complete: Security Principles

Congratulations! You've completed the Security Principles foundation. You now understand:

- The security mindset: think like an attacker, design like a defender
- Defense in depth: layer independent security controls
- Identity and access: authentication, authorization, least privilege
- Secure by default: build security in, don't bolt it on

**Where to go from here:**

| Your Interest | Next Track |
|---------------|------------|
| Security in practice | [DevSecOps Discipline](../../disciplines/devsecops/README.md) |
| Security tools | [Security Tools Toolkit](../../toolkits/security-tools/README.md) |
| Kubernetes security | [CKS Certification](../../../k8s/cks/README.md) |
| Foundations | [Distributed Systems](../distributed-systems/README.md) |

---

## Track Summary

| Module | Key Takeaway |
|--------|--------------|
| 4.1 | Security is a mindset—think like attackers to defend against them |
| 4.2 | Layer defenses—no single control is enough |
| 4.3 | Authenticate who, authorize what—principle of least privilege |
| 4.4 | Make security the default—secure path should be the easy path |

*"Security is not a product, but a process."* — Bruce Schneier
