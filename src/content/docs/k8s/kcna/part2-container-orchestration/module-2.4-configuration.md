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

---

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

1. **What's the difference between ConfigMap and Secret?**
   <details>
   <summary>Answer</summary>
   ConfigMaps store non-sensitive configuration data in plain text. Secrets store sensitive data (passwords, keys) and are base64 encoded. Both can be consumed as environment variables or mounted as volumes.
   </details>

2. **Is base64 encoding secure?**
   <details>
   <summary>Answer</summary>
   No! Base64 is encoding, not encryption. Anyone can decode it. For real security, enable encryption at rest for Secrets in etcd.
   </details>

3. **How can an application consume ConfigMap data?**
   <details>
   <summary>Answer</summary>
   Two ways: (1) As environment variables using envFrom or valueFrom, (2) As files by mounting the ConfigMap as a volume. Environment variables require Pod restart to update; volume mounts can update automatically.
   </details>

4. **What does immutable: true do?**
   <details>
   <summary>Answer</summary>
   Makes the ConfigMap or Secret unchangeable after creation. This protects against accidental changes and improves performance. To update, you must delete and recreate it.
   </details>

5. **Why separate configuration from container images?**
   <details>
   <summary>Answer</summary>
   To use the same image across environments (dev/staging/prod), change configuration without rebuilding images, and keep sensitive data out of image layers.
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
