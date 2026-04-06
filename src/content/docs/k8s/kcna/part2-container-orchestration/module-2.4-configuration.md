---
title: "Module 2.4: Configuration"
slug: k8s/kcna/part2-container-orchestration/module-2.4-configuration
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Configuration concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 2.3 (Storage)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the purpose of ConfigMaps and Secrets for separating config from code
2. **Compare** methods of injecting configuration: environment variables, volume mounts, and command args
3. **Identify** when to use ConfigMaps vs. Secrets based on data sensitivity
4. **Evaluate** immutable ConfigMaps and their benefits for large-scale deployments

---

## Why This Module Matters

Applications need configuration—database URLs, feature flags, API keys. Kubernetes provides ConfigMaps and Secrets to manage configuration separately from container images. This is a core concept tested on KCNA.

---

## The Configuration Problem

```
┌─────────────────────────────────────────────────────────────┐
│              WHY SEPARATE CONFIGURATION?                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Without ConfigMaps/Secrets (Bad Practice):                │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Configuration baked into image:                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Dockerfile:                                        │   │
│  │  ENV DATABASE_URL=prod-db.example.com              │   │
│  │  ENV API_KEY=sk-12345...                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Problems:                                                 │
│  • Need different images for dev/staging/prod             │
│  • Secrets visible in image layers                         │
│  • Can't change config without rebuilding image           │
│                                                             │
│  With ConfigMaps/Secrets (Best Practice):                 │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Same image everywhere:                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [my-app:v1.0] ←── same image                      │   │
│  │       │                                             │   │
│  │       ├── dev:    ConfigMap with dev settings      │   │
│  │       ├── staging: ConfigMap with staging settings │   │
│  │       └── prod:   ConfigMap with prod settings     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Benefits:                                                 │
│  • One image, many environments                           │
│  • Change config without rebuilding                       │
│  • Secrets managed separately and securely               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ConfigMaps

A **ConfigMap** stores non-sensitive configuration data:

```
┌─────────────────────────────────────────────────────────────┐
│              CONFIGMAP                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMaps store:                                         │
│  • Key-value pairs                                         │
│  • Configuration files                                     │
│  • Environment variables                                   │
│                                                             │
│  Example ConfigMap:                                        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  apiVersion: v1                                            │
│  kind: ConfigMap                                           │
│  metadata:                                                 │
│    name: app-config                                        │
│  data:                                                     │
│    DATABASE_HOST: mysql.default.svc                       │
│    LOG_LEVEL: info                                         │
│    MAX_CONNECTIONS: "100"                                 │
│    app.properties: |                                      │
│      server.port=8080                                     │
│      server.name=myapp                                    │
│                                                             │
│  Note: All values are strings (even "100")                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: The 12-Factor App methodology says "store config in the environment." If you bake a database password into your container image, what problems does that create when you need to deploy the same application to dev, staging, and production environments?

### Using ConfigMaps

```
┌─────────────────────────────────────────────────────────────┐
│              USING CONFIGMAPS                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. As Environment Variables:                              │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  spec:                                                     │
│    containers:                                             │
│    - name: app                                             │
│      envFrom:                                              │
│      - configMapRef:                                       │
│          name: app-config    # All keys become env vars   │
│                                                             │
│  Or specific keys:                                         │
│  env:                                                      │
│  - name: DB_HOST                                          │
│    valueFrom:                                              │
│      configMapKeyRef:                                      │
│        name: app-config                                    │
│        key: DATABASE_HOST                                 │
│                                                             │
│  2. As Volume (files):                                    │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  volumes:                                                  │
│  - name: config-volume                                    │
│    configMap:                                              │
│      name: app-config                                      │
│                                                             │
│  volumeMounts:                                             │
│  - name: config-volume                                    │
│    mountPath: /etc/config                                 │
│                                                             │
│  Result:                                                   │
│  /etc/config/DATABASE_HOST    (contains: mysql.default..) │
│  /etc/config/LOG_LEVEL        (contains: info)           │
│  /etc/config/app.properties   (contains: server.port...) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Exercise: Injecting Environment Variables**
> You have a ConfigMap named `backend-config` with a key `LOG_LEVEL`. Complete this partial Pod definition to inject that value as an environment variable named `APP_LOG_LEVEL`.
> ```yaml
> apiVersion: v1
> kind: Pod
> metadata:
>   name: backend-pod
> spec:
>   containers:
>   - name: app
>     image: my-app:v1
>     # ADD YOUR CODE HERE
> ```
> <details>
> <summary>Solution</summary>
> 
> ```yaml
>     env:
>     - name: APP_LOG_LEVEL
>       valueFrom:
>         configMapKeyRef:
>           name: backend-config
>           key: LOG_LEVEL
> ```
> By explicitly using `valueFrom` and `configMapKeyRef`, you map a specific key from your ConfigMap to a specific environment variable name inside the container.
> </details>

---

## Secrets

A **Secret** stores sensitive data:

```
┌─────────────────────────────────────────────────────────────┐
│              SECRETS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Secrets store:                                            │
│  • Passwords                                               │
│  • API keys                                                │
│  • Certificates                                            │
│  • SSH keys                                                │
│                                                             │
│  Secret Types:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Opaque: Generic secret (default)                       │
│  • kubernetes.io/tls: TLS certificates                    │
│  • kubernetes.io/dockerconfigjson: Docker registry auth   │
│  • kubernetes.io/basic-auth: Basic authentication         │
│  • kubernetes.io/ssh-auth: SSH credentials                │
│                                                             │
│  Example Secret:                                           │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  apiVersion: v1                                            │
│  kind: Secret                                              │
│  metadata:                                                 │
│    name: db-credentials                                    │
│  type: Opaque                                              │
│  data:                                                     │
│    username: YWRtaW4=        # base64 encoded "admin"     │
│    password: cGFzc3dvcmQxMjM= # base64 encoded "password123"│
│                                                             │
│  Or use stringData (plain text, encoded automatically):   │
│  stringData:                                               │
│    username: admin                                         │
│    password: password123                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Using Secrets

```
┌─────────────────────────────────────────────────────────────┐
│              USING SECRETS                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Same patterns as ConfigMaps:                              │
│                                                             │
│  1. As Environment Variables:                              │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  env:                                                      │
│  - name: DB_PASSWORD                                       │
│    valueFrom:                                              │
│      secretKeyRef:                                         │
│        name: db-credentials                                │
│        key: password                                       │
│                                                             │
│  2. As Volume:                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  volumes:                                                  │
│  - name: secret-volume                                    │
│    secret:                                                 │
│      secretName: db-credentials                           │
│                                                             │
│  volumeMounts:                                             │
│  - name: secret-volume                                    │
│    mountPath: /etc/secrets                                │
│    readOnly: true          # Best practice for secrets    │
│                                                             │
│  Result:                                                   │
│  /etc/secrets/username     (contains: admin)              │
│  /etc/secrets/password     (contains: password123)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Exercise: Mounting a Secret Volume**
> Your application needs access to a TLS certificate stored in a Secret named `tls-certs`. Update this Deployment to mount the secret as a volume at `/etc/tls` and ensure it's read-only.
> ```yaml
> apiVersion: apps/v1
> kind: Deployment
> metadata:
>   name: secure-app
> spec:
>   template:
>     spec:
>       containers:
>       - name: app
>         image: secure-app:v2
>         # ADD VOLUME MOUNTS HERE
>       # ADD VOLUMES HERE
> ```
> <details>
> <summary>Solution</summary>
> 
> ```yaml
>         volumeMounts:
>         - name: cert-volume
>           mountPath: /etc/tls
>           readOnly: true
>       volumes:
>       - name: cert-volume
>         secret:
>           secretName: tls-certs
> ```
> Providing certificates as a read-only volume mount is the standard pattern because applications expect certificates to exist as files on the filesystem, and `readOnly: true` prevents accidental modification.
> </details>

---

## ConfigMap vs Secret

```
┌─────────────────────────────────────────────────────────────┐
│              CONFIGMAP vs SECRET                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │     ConfigMap        │  │       Secret         │        │
│  ├──────────────────────┤  ├──────────────────────┤        │
│  │ • Non-sensitive      │  │ • Sensitive data     │        │
│  │ • Plain text         │  │ • Base64 encoded     │        │
│  │ • Not encrypted      │  │ • Can be encrypted   │        │
│  │ • No size limit      │  │ • 1MB limit          │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                             │
│  When to use what:                                         │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ConfigMap:                Secret:                         │
│  • Database host          • Database password              │
│  • Log level              • API keys                       │
│  • Feature flags          • TLS certificates               │
│  • Config files           • SSH keys                       │
│                                                             │
│  Important:                                                │
│  ─────────────────────────────────────────────────────────  │
│  Base64 is NOT encryption!                                │
│  It's just encoding. Anyone can decode it.                │
│  For real security, enable encryption at rest.            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Exercise: Choose Your Configuration Object**
> For each of the following data types, decide whether you should use a ConfigMap or a Secret, and explain why.
> 1. A feature flag enabling a new UI layout (`ENABLE_NEW_UI=true`)
> 2. A third-party payment gateway API token
> 3. An NGINX configuration file (`nginx.conf`)
> 4. A private SSH key for accessing a Git repository
> <details>
> <summary>Solution</summary>
> 
> 1. **ConfigMap**: Feature flags are not sensitive. If exposed, they don't pose a security risk.
> 2. **Secret**: API tokens provide access to external systems and represent financial risk. They must be protected using RBAC and encryption at rest.
> 3. **ConfigMap**: Configuration files define application behavior but typically don't contain credentials. They are meant to be visible and editable.
> 4. **Secret**: SSH keys grant access to external resources. Exposing them could compromise your infrastructure or codebase.
> </details>

---

> **Stop and think**: Secrets in Kubernetes are base64 encoded, not encrypted. If someone has access to run `kubectl get secret db-creds -o yaml`, they can decode the password instantly. What additional security measures would you need for real production secret management?

## Immutable ConfigMaps and Secrets

```
┌─────────────────────────────────────────────────────────────┐
│              IMMUTABLE CONFIGMAPS/SECRETS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  apiVersion: v1                                            │
│  kind: ConfigMap                                           │
│  metadata:                                                 │
│    name: app-config                                        │
│  immutable: true     ← Cannot be changed after creation   │
│  data:                                                     │
│    key: value                                              │
│                                                             │
│  Benefits:                                                 │
│  • Protects against accidental changes                    │
│  • Improves performance (no watches needed)               │
│  • Reduces API server load                                │
│                                                             │
│  To update: Delete and recreate with new name             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables vs Volume Mounts

| Aspect | Environment Variables | Volume Mounts |
|--------|----------------------|---------------|
| **Update** | Requires Pod restart | Hot reload possible |
| **Access** | Process environment | File system |
| **Use case** | Simple key-value | Config files |
| **Size** | Limited | Larger files OK |

---

## Did You Know?

- **Secrets are not encrypted by default** - They're only base64 encoded. Enable encryption at rest for real security.

- **ConfigMap updates** - If mounted as a volume, changes propagate to Pods (with a delay). Environment variables require Pod restart.

- **Secret size limit** - Secrets are limited to 1MB because they're stored in etcd.

- **Mounting specific keys** - You can mount only specific keys from a ConfigMap/Secret, not the entire resource.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Storing secrets in ConfigMaps | Security risk, visible in logs | Use Secrets for sensitive data |
| Thinking base64 is encryption | False sense of security | Enable encryption at rest |
| Hardcoding in images | Can't change without rebuild | Use ConfigMaps/Secrets |
| Large ConfigMaps | Performance issues | Keep configs small, split if needed |

---

## Quiz

1. **A developer stores an API key in a ConfigMap because "it's just a string." During a security audit, the API key is found in plain text in kubectl output and etcd. What should they have done differently, and why does the distinction between ConfigMap and Secret matter even though Secrets are also not encrypted by default?**
   <details>
   <summary>Answer</summary>
   The API key should be stored in a Secret, not a ConfigMap. While Secrets are only base64 encoded by default (not truly encrypted), they receive additional protections: RBAC can be configured to restrict Secret access separately from ConfigMaps, Secrets can be encrypted at rest in etcd when encryption is enabled, and Secret data is not displayed in `kubectl describe` output. ConfigMaps are designed for non-sensitive data and have none of these protections. For production, enable encryption at rest for Secrets in etcd and consider external secret management tools.
   </details>

2. **Your application reads its database URL from an environment variable injected via a ConfigMap. You update the ConfigMap to point to a new database, but the application still connects to the old one. What is happening, and how would you fix it?**
   <details>
   <summary>Answer</summary>
   Environment variables are set when the Pod starts and do not update when the underlying ConfigMap changes. The Pod must be restarted for the new value to take effect. To avoid this, mount the ConfigMap as a volume instead. Volume-mounted ConfigMaps automatically update when the ConfigMap changes (with a delay of up to a minute). The application would then read the configuration from a file rather than an environment variable, and could watch for file changes to reload without a restart.
   </details>

3. **A new hire asks: "Why not just put the database password directly in the Deployment YAML as an environment variable value?" What are the problems with this approach compared to using a Secret?**
   <details>
   <summary>Answer</summary>
   Hardcoding secrets in YAML means: the password is visible in version control (Git) to anyone with repository access, the same password is baked into the Deployment definition making it impossible to use different credentials per environment without duplicating the YAML, changing the password requires editing and redeploying the Deployment, and the plain text password appears in `kubectl get deployment -o yaml` output. Using a Secret separates the credential from the workload definition, allows different Secrets per namespace (dev/staging/prod), enables RBAC control over who can read Secrets, and keeps sensitive values out of Git.
   </details>

4. **Your team runs 500 Pods that all reference the same ConfigMap. Every time someone updates the ConfigMap, all 500 Pods detect the change and the API server experiences a load spike. What Kubernetes feature would solve this problem?**
   <details>
   <summary>Answer</summary>
   Mark the ConfigMap as `immutable: true`. Immutable ConfigMaps cannot be modified after creation, which means Kubernetes does not need to maintain watches for changes on them, significantly reducing API server load. When you need to update the configuration, create a new ConfigMap with a different name (e.g., `app-config-v2`), update the Pod specs to reference it, and delete the old one. This also protects against accidental configuration changes that could affect all 500 Pods simultaneously.
   </details>

5. **You deploy the same application to dev, staging, and production. Each environment needs a different database host and different replica count, but the container image is identical. How do ConfigMaps enable this pattern, and how does it relate to the 12-Factor App methodology?**
   <details>
   <summary>Answer</summary>
   Create a separate ConfigMap in each namespace (dev, staging, prod) with the appropriate database host value. The Deployment references the ConfigMap by name, which resolves to the namespace-local ConfigMap. The same container image runs everywhere -- only the injected configuration differs. This implements 12-Factor App principle #3 ("Store config in the environment") by strictly separating configuration from code. The build artifact (container image) is immutable and environment-agnostic, while ConfigMaps provide environment-specific settings at deploy time.
   </details>

---

## Summary

**ConfigMaps**:
- Store non-sensitive configuration
- Plain text key-value pairs or files
- Use for: database hosts, log levels, feature flags

**Secrets**:
- Store sensitive data
- Base64 encoded (not encrypted!)
- Use for: passwords, API keys, certificates

**Consumption methods**:
- Environment variables (requires restart for updates)
- Volume mounts (can hot-reload)

**Best practices**:
- Never hardcode config in images
- Use Secrets for sensitive data
- Enable encryption at rest for Secrets
- Consider immutable for stability

---

## Part 2 Complete!

You've finished **Container Orchestration** (22% of the exam). You now understand:
- How scheduling decides where Pods run
- Scaling with HPA, VPA, and Cluster Autoscaler
- Storage with PVs, PVCs, and StorageClasses
- Configuration with ConfigMaps and Secrets

**Next Part**: [Part 3: Cloud Native Architecture](../part3-cloud-native-architecture/module-3.1-cloud-native-principles/) - Understanding cloud native design patterns and the CNCF ecosystem.