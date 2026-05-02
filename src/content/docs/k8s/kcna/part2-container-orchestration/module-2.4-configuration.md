---
revision_pending: false
title: "Module 2.4: Configuration"
slug: k8s/kcna/part2-container-orchestration/module-2.4-configuration
sidebar:
  order: 5
---

# Module 2.4: Configuration

> **Complexity**: `[MEDIUM]` - Configuration concepts
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.3 (Storage), basic Pod and Deployment manifests, and a Kubernetes 1.35+ cluster or local sandbox. This module uses the `k` alias for `kubectl`; define it once with `alias k=kubectl` before running the examples.

## Learning Outcomes

After completing this module, you will be able to:

1. **Design** Kubernetes workloads that separate application configuration from container images using ConfigMaps, Secrets, environment variables, arguments, and mounted files.
2. **Compare** ConfigMaps and Secrets for sensitivity, access control, update behavior, and operational risk in Kubernetes 1.35+ environments.
3. **Diagnose** configuration drift when a Pod keeps using stale values after a ConfigMap or Secret changes.
4. **Implement** immutable ConfigMaps and Secrets for stable rollouts where accidental mutation would create broad production impact.
5. **Evaluate** whether a configuration value belongs in a ConfigMap, a Secret, a command argument, an environment variable, or a volume mount.

## Why This Module Matters

In 2017, a large credit reporting company disclosed that attackers had exploited an unpatched web application framework and eventually accessed sensitive personal data for about 143 million people. The incident is usually discussed as a patching failure, but it also exposed a deeper operational truth: configuration controls, secrets, certificates, credentials, and runtime switches shape how quickly teams can contain damage when something goes wrong. When configuration is welded into images, copied through scripts, or scattered across many Deployment manifests, responders lose the ability to change behavior cleanly under pressure.

Kubernetes does not make configuration safe by magic. It gives you first-class objects, mainly ConfigMaps and Secrets, so you can separate the application artifact from the values that vary between environments. That separation sounds simple until a production rollout depends on it. A container image should answer the question, "What code are we running?" Configuration should answer the different question, "How should this same code behave here, today, in this namespace, with these privileges?"

This module teaches configuration as an operating discipline rather than a YAML trivia topic. You will see how ConfigMaps and Secrets are stored, projected into Pods, updated, protected, and misused. You will also practice deciding where a value belongs, because KCNA questions often hide the real test inside a scenario: the cluster has the right object type, but the workload consumes it in a way that prevents reloads, leaks sensitive values, or creates surprise during a rollout.

## The Configuration Problem

Configuration exists because useful software changes its behavior without changing its code. A web service may use the same binary in development, staging, and production, yet it needs different database hosts, logging levels, feature flags, public URLs, certificate bundles, and integration endpoints. If every environment needs a different image, then the image is no longer a trustworthy release artifact; it becomes a pile of similar artifacts that must be rebuilt, scanned, promoted, and explained separately.

The operational goal is to build once and configure many times. That goal matters because container images are expensive to treat casually. Images pass through vulnerability scanners, provenance checks, registry permissions, and deployment approvals. When a team rebuilds an image just to change `LOG_LEVEL` from `debug` to `info`, it spends release-system effort on a value that should have been supplied by the environment.

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

The diagram shows the most important mental model for Kubernetes configuration. The image should be portable, while the namespace supplies environment-specific values through API objects. A development namespace can point the same Deployment at a disposable database, while production points it at a managed database with stricter credentials. The Pod template stays readable because it declares where configuration comes from instead of embedding every value directly.

This separation also improves failure recovery. If a feature flag causes a spike in errors, a platform team should not rebuild and redeploy the application just to turn the feature off. If a certificate bundle must rotate, the team should not bake the bundle into an image layer where old copies remain in registries and caches. Kubernetes configuration objects give you a controlled place to express those changes, but the control only works when you choose the right object and the right consumption method.

Pause and predict: if two environments run the same image but one environment injects `LOG_LEVEL=debug` through an environment variable and the other mounts a logging file from a ConfigMap, which environment can reload without restarting the Pod, and what must the application know how to do?

The answer depends on the interface between Kubernetes and the application. Kubernetes can update a projected ConfigMap volume after the object changes, but it cannot force an already-running process to reread a file. Environment variables are even more static, because a process receives its environment when it starts. Kubernetes gives you delivery mechanisms, not an automatic application reconfiguration engine.

A practical configuration design therefore has two halves. The platform half asks which Kubernetes object should hold the value, which identities may read it, and how it reaches the container. The application half asks when the process reads the value, whether it can reload the value safely, and what happens when a required key is missing. Teams get reliability when both halves are designed together instead of patched after an outage.

## ConfigMaps: Non-Sensitive Configuration as Data

A ConfigMap stores non-sensitive configuration data as key-value pairs. That simple definition hides a useful distinction: the values are not secret, but they may still be operationally important. A bad database hostname, timeout, feature flag, or application properties file can take a service down just as surely as a bad image tag. Treat ConfigMaps as controlled runtime inputs, not as casual scratch space.

Kubernetes stores ConfigMap data under the `data` field, where keys and values are strings. The string constraint is easy to forget when examples show numbers and booleans. If a YAML value looks numeric, quote it when the consuming application expects a string, and let the application parse the value deliberately. That habit prevents confusing differences between YAML parsing, Kubernetes API storage, and application configuration libraries.

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

The same ConfigMap can represent several shapes of configuration. Short values such as `LOG_LEVEL` fit naturally as individual keys. Longer files such as `app.properties`, `nginx.conf`, or a logging configuration can also fit as multi-line values. That flexibility is useful, but it can tempt teams into creating oversized "everything" ConfigMaps that are hard to review and risky to update.

In a real cluster, a ConfigMap is namespaced. A Deployment in the `payments-prod` namespace does not read a ConfigMap from `payments-dev` unless some external tool copies or renders it there. This namespace scoping supports the "same image, different environment" model. Each namespace can contain an `app-config` object with the same name but different values, and the workload template can stay consistent across environments.

Here is a runnable example that creates a ConfigMap from literal values and then inspects it. The examples use `k` after the alias introduction because KCNA expects you to recognize standard `kubectl` operations even when the shorthand is used in day-to-day shell sessions.

```bash
alias k=kubectl
k create namespace config-lab
k create configmap app-config \
  --namespace config-lab \
  --from-literal=DATABASE_HOST=mysql.default.svc \
  --from-literal=LOG_LEVEL=info \
  --from-literal=MAX_CONNECTIONS=100
k get configmap app-config --namespace config-lab -o yaml
```

This command is convenient for practice, but declarative YAML is easier to review in production. A ConfigMap change can alter how many requests an application sends to a dependency, which endpoint it calls, or which feature it exposes to users. Put important configuration under the same review discipline as other deployment changes, even when the data is not confidential.

When a ConfigMap key becomes part of an application contract, document its expected format near the workload or in the application repository. Kubernetes can verify that the ConfigMap object exists, but it cannot know whether `MAX_CONNECTIONS=banana` is meaningful to your service. Admission policies, schema-aware deployment tools, and application startup validation can close that gap, yet the first defense is a small and readable configuration surface.

## Injecting Configuration into Pods

Kubernetes lets a Pod consume ConfigMaps and Secrets in several ways: environment variables, specific environment variables from individual keys, command arguments that reference environment variables, and projected files through volumes. The right choice depends on when the application reads the value and what shape the value has. A short string read once at process start fits an environment variable; a file that a process can reload fits a volume mount.

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

The `envFrom` pattern is compact, but compactness has a cost. Every key becomes an environment variable, so accidental keys can enter the process environment and key naming must follow environment variable rules. The explicit `env` pattern takes more YAML, but it lets you rename a key, choose only the values the container needs, and make the workload contract obvious during review.

Volume mounts are a better fit when the application already expects files. NGINX reads configuration files, Java applications often read properties files, and many TLS libraries expect certificate files on disk. Kubernetes projects each key as a file, and the file contents match the corresponding value. That projection makes a ConfigMap feel like a small, managed filesystem that is populated by the API server and kubelet.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: configured-demo
  namespace: config-lab
spec:
  restartPolicy: Never
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "echo DB=$DB_HOST; echo file=$(cat /etc/config/LOG_LEVEL); sleep 3600"]
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: DATABASE_HOST
    volumeMounts:
    - name: app-config-files
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: app-config-files
    configMap:
      name: app-config
```

Before running this Pod, predict the two places where the same ConfigMap appears. `DB_HOST` is read from the process environment, while `/etc/config/LOG_LEVEL` is read from a mounted file. If you later update the ConfigMap, the environment variable inside the running process will remain unchanged, while the mounted file can eventually reflect the new value.

The delay on projected volumes matters in troubleshooting. Kubernetes does not promise instant propagation from an updated ConfigMap to every mounted file. The kubelet refreshes projected volumes on its sync loop and may use cached data, so you should think in seconds to a couple of minutes rather than milliseconds. Applications that need immediate configuration changes usually require a dedicated reload signal, a controller that restarts Pods, or an external configuration system designed for that behavior.

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

The worked exercise above shows why explicit key mapping is often worth the extra lines. A platform team can keep a stable ConfigMap key while an application uses a clearer internal environment variable name. That decoupling is useful during migrations, because the platform object can remain compatible with several versions of an application while each container chooses the variable names its framework expects.

Command arguments are the third consumption pattern. Kubernetes does not read a ConfigMap directly into `args`, but it can populate an environment variable from a ConfigMap and then expand that variable in the container command or arguments. This pattern is useful for programs that prefer flags such as `--log-level=$(LOG_LEVEL)`, but it still behaves like environment configuration because the value is resolved when the container starts.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: args-demo
  namespace: config-lab
spec:
  restartPolicy: Never
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c"]
    args: ["echo starting with --log-level=$(LOG_LEVEL); sleep 3600"]
    env:
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: LOG_LEVEL
```

Choose command arguments when the application already exposes a stable flag interface and the value rarely changes without a restart. Choose environment variables when a framework expects them or when the value is a simple process-level setting. Choose volumes when the application expects files, when the value is multi-line, or when the reload path reads from disk. The best answer is the one that matches the application behavior, not the shortest YAML.

## Secrets: Sensitive Data with Different Risk

A Secret stores sensitive data such as passwords, API tokens, TLS private keys, registry credentials, and SSH keys. Secrets look similar to ConfigMaps because both can be consumed as environment variables or mounted files. The difference is not that Secrets are magically safe; the difference is that Kubernetes and cluster operators can apply stricter access control, storage encryption, audit rules, and handling conventions to Secret objects.

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

Base64 encoding is the most commonly misunderstood detail in Kubernetes Secrets. The `data` field stores base64-encoded values because the API object must carry arbitrary bytes through JSON and YAML safely. Encoding is not encryption. Anyone who can read the Secret object can decode the value, so a secure production posture depends on RBAC, encryption at rest, namespace boundaries, careful logging, and limited human access.

The `stringData` field is convenient for authoring because you can write plain strings and let the API server encode them into `data`. That convenience does not mean plain secrets should live in Git. In production, teams usually generate Secret manifests from a secure delivery process, use sealed or external secret tooling, or synchronize from a cloud secret manager. KCNA expects you to know the native Secret object, but real operations also require secret lifecycle design.

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

The consumption choice has security consequences. A Secret injected as an environment variable can be exposed through process inspection, crash reports, debugging dumps, or application logs that print environment state. A Secret mounted as a file can be easier to protect with file permissions and easier for certificate-based libraries to consume. Neither pattern is universally safe, so choose based on the application, the threat model, and how the value rotates.

```bash
k create secret generic db-credentials \
  --namespace config-lab \
  --from-literal=username=admin \
  --from-literal=password='example-password-only'
k describe secret db-credentials --namespace config-lab
k get secret db-credentials --namespace config-lab -o jsonpath='{.data.username}' | base64 --decode
```

Notice the difference between `describe` and `get -o yaml` or `jsonpath`. `k describe secret` hides the raw values and shows metadata such as keys and sizes. Directly retrieving the object can expose encoded data to anyone with permission. This distinction is one reason RBAC policies often allow broader read access to ConfigMaps than to Secrets.

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

War story: a platform team once rotated a database password by updating a Secret and assumed every workload would immediately use the new value. Several Deployments consumed the password as an environment variable, so those Pods kept authenticating with the old credential until they restarted. The fix was not merely "update the Secret"; the fix was to document consumption patterns, restart affected Pods during rotations, and move certificate-style material to read-only volume mounts where the application could reload it.

Stop and think: Secrets in Kubernetes are base64 encoded, not encrypted. If someone can run `k get secret db-credentials -o yaml`, what cluster permissions, storage settings, and operational processes would you review before calling the setup production-ready?

## ConfigMap vs Secret: Classification and Tradeoffs

The decision between ConfigMap and Secret starts with sensitivity, but it should not stop there. A value is sensitive if disclosure would grant access, reveal private data, weaken authentication, expose private infrastructure, or help an attacker move laterally. A value can be non-sensitive and still dangerous to change, so ConfigMaps require review even when they do not require secrecy.

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

The original diagram says "no size limit" for ConfigMaps as a beginner contrast, but operationally you should keep ConfigMaps small. Kubernetes objects live in the API server and backing store, and very large configuration objects can increase load, slow watch traffic, and make review harder. Secrets have a documented one-mebibyte size limit, and ConfigMaps should be treated with similar restraint even when an exact hard limit is not the main concern.

Classification becomes easier when you ask what happens if the value appears in a support ticket, terminal recording, or `k get` output. A feature flag may be safe to reveal, but a payment API token is not. An NGINX configuration file may be public architecture data, but a TLS private key is authentication material. A database hostname is usually not a credential, but it may still expose internal topology, so some organizations classify even hostnames carefully.

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

There is one subtle trap in this exercise. A value can start non-sensitive and become sensitive when combined with other values. A service URL by itself may not be confidential, but a URL containing embedded credentials or tenant identifiers belongs in a Secret or should be redesigned. Review configuration as actual data, not just as a key name that sounds harmless.

RBAC reinforces the distinction. Teams often grant application operators permission to read ConfigMaps so they can diagnose behavior, while limiting Secret access to narrower roles. If secrets are stored in ConfigMaps, those RBAC boundaries collapse. The workload may still run, but the cluster loses an important administrative control, and auditors will correctly treat the design as a data exposure risk.

## Updates, Drift, and Immutable Configuration

Configuration drift happens when the object in the API server and the value inside a running process no longer match. This is common after a ConfigMap or Secret update because the Kubernetes object changes immediately, while running containers may keep old environment variables, old command arguments, or cached file contents. Debugging drift requires you to trace the path from API object to Pod spec to container runtime to application reload behavior.

The first question is where the Pod gets its value. If the value came from `env` or `envFrom`, the Pod must restart before the process sees the new value. If the value came from a projected volume, the mounted file may update after kubelet refreshes it, but the application must reread the file. If the value came from a command argument, it behaves like startup configuration and needs a restart.

```bash
k get configmap app-config --namespace config-lab -o yaml
k get pod configured-demo --namespace config-lab -o jsonpath='{.spec.containers[0].env}'
k exec configured-demo --namespace config-lab -- sh -c 'echo "$DB_HOST"; cat /etc/config/LOG_LEVEL'
```

These three commands inspect three different layers. The first shows the source object, the second shows how the Pod template references it, and the third shows what the running container can actually read. Many configuration incidents drag on because teams check only the source object and assume the process state has already changed. In Kubernetes, that assumption is often wrong.

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

Immutable ConfigMaps and Secrets change the operating model. Once created with `immutable: true`, the object cannot be updated in place. To change the data, you create a new object, usually with a versioned name, and update the workload to reference it. That sounds less convenient, but it makes rollouts explicit and prevents a single edit from silently changing many running Pods.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-v2
  namespace: config-lab
immutable: true
data:
  DATABASE_HOST: mysql.default.svc
  LOG_LEVEL: info
  MAX_CONNECTIONS: "100"
```

Immutable objects are especially useful at scale. The kubelet does not need to watch for changes to an immutable ConfigMap or Secret, which reduces API server load in large clusters. They also fit GitOps workflows because a new name creates a visible rollout boundary. You can review `app-config-v2`, deploy it, watch the rollout, and keep `app-config-v1` available until the new Pods are stable.

The tradeoff is operational ceremony. Emergency changes require creating a new object and updating references, which may be slower than patching a mutable ConfigMap. That is why immutable configuration is strongest for values that should change only through a planned rollout, such as application property files, known-good TLS bundles, or versioned feature configurations. Use mutable objects when fast in-place edits are an intentional part of the support model, and pair that choice with monitoring and audit logs.

Before you choose immutability, ask which failure you fear more. If accidental edits to shared configuration are the bigger risk, immutable objects help. If delayed emergency changes are the bigger risk, mutable objects may be acceptable with tighter RBAC and clear restart procedures. The KCNA-level answer is to know that immutability protects stability and can reduce watch load, but the engineering answer is to match the feature to the rollout model.

## Environment Variables vs Volume Mounts

Environment variables and volume mounts are not competing syntax styles; they are different runtime contracts. An environment variable belongs to a process at startup, while a mounted file belongs to the filesystem view that the process can read later. This difference explains most surprises after configuration updates. If you remember nothing else, remember that Kubernetes can change an object, but a running process does not automatically change its mind.

| Aspect | Environment Variables | Volume Mounts |
|--------|----------------------|---------------|
| **Update** | Requires Pod restart | Hot reload possible |
| **Access** | Process environment | File system |
| **Use case** | Simple key-value | Config files |
| **Size** | Limited | Larger files OK |

Environment variables work well for small, startup-only settings such as a log level, a service mode, or a feature toggle that the application reads during initialization. They are easy to inspect from the Pod spec and easy for many frameworks to consume. The downside is that changes require a Pod restart, and sensitive values in environment variables can leak through process diagnostics or careless logging.

Volume mounts work well for file-shaped data such as application properties, NGINX configuration, certificate chains, trusted certificate authority bundles, and policy files. They support multi-line content cleanly, and projected files can update after the source object changes. The downside is that the application must watch or reread files, and mounting over an existing directory can hide files that were present in the image at that path.

There is also a useful middle path: mount only specific keys at specific paths. This avoids projecting an entire ConfigMap or Secret when the container needs only one file. It also lets you choose filenames that match application expectations. Be careful with `subPath`, though, because ConfigMap and Secret updates do not propagate through `subPath` mounts in the same way as normal projected volumes.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: selected-key-demo
  namespace: config-lab
spec:
  restartPolicy: Never
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "cat /etc/app/app.properties; sleep 3600"]
    volumeMounts:
    - name: config-volume
      mountPath: /etc/app
      readOnly: true
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: app.properties
```

Which approach would you choose here and why: an application needs a TLS certificate chain, a private key, and a log level, and it can reload certificates from disk but reads the log level only during startup. A good design may use both mechanisms. Mount the certificate material from a Secret as read-only files, and inject the log level from a ConfigMap environment variable with a planned restart when it changes.

The important habit is to avoid one-size-fits-all configuration. A Deployment can consume multiple ConfigMaps and Secrets through different mechanisms. That is normal when values have different shapes, sensitivity, and update needs. Clear naming and small objects make this manageable, while a single giant object with every value creates unnecessary coupling between unrelated changes.

## Operational Review Example: Shipping a Configuration Change

Imagine a team that owns an order-processing service. The service has one image, three namespaces, a ConfigMap for behavior, and a Secret for database credentials. Product wants to enable a new fraud-scoring integration in staging, then production, without rebuilding the service. The naive change is a single ConfigMap patch, but a disciplined review asks what the value controls, how it reaches the process, who can read it, and what rollback looks like.

The first review step is classification. The integration endpoint and feature flag can live in a ConfigMap if they do not contain credentials, while the integration token belongs in a Secret because disclosure would grant access to a third-party system. This split may feel tedious, yet it preserves separate RBAC boundaries. Operators can inspect the non-sensitive rollout settings without gaining permission to read payment-related credentials.

The second review step is consumption behavior. If the service reads the feature flag only during startup, the rollout plan must include a Deployment restart or a new ReplicaSet. If the service reads a mounted properties file on every request, the team must confirm that the application handles partial changes safely. Kubernetes can project files, but only the application can decide whether a new flag value is valid while requests are in flight.

The third review step is blast radius. A ConfigMap shared by all order-processing replicas can change every Pod that references it, while a versioned ConfigMap referenced by a new Deployment revision changes only Pods in the rollout. For staging, a mutable ConfigMap patch may be acceptable because the namespace is small and rollback is quick. For production, a versioned immutable ConfigMap gives the team a clearer deployment event, stronger review history, and a safer rollback path.

The fourth review step is observability. Before applying the change, the team should know which metric confirms success and which signal triggers rollback. For a fraud-scoring flag, that might include request latency, integration error rate, declined-order count, and application startup failures. Configuration work is still production work, so it deserves the same readiness thinking as code changes. A perfectly valid ConfigMap can still carry a value that breaks the service.

The fifth review step is missing-key behavior. Kubernetes can stop a Pod from starting when a required ConfigMap key is absent, unless the reference is marked optional. That default is often helpful because a loudly failing Pod is easier to diagnose than an application running with hidden defaults. Optional references are useful for gradual migrations, but they should be chosen deliberately and removed when the migration ends.

The sixth review step is rollback. If the team patches a mutable ConfigMap in place, rollback means patching it again and restarting any Pods that captured old environment variables. If the team uses an immutable `app-config-v3` object, rollback means updating the workload reference back to `app-config-v2` and watching the rollout. Both methods can work, but the second gives release tooling a more visible state transition.

This example is deliberately ordinary because most configuration incidents are ordinary. They happen when teams skip classification, forget startup behavior, or assume a changed object means a changed process. Strong Kubernetes operators do not memorize every field in isolation. They trace the chain from value to object, object to Pod, Pod to process, and process to user-visible behavior.

When you review a real pull request, look for that chain in the manifest. A ConfigMap should tell you which non-sensitive behavior is changing. A Secret reference should tell you that sensitive material is separated and protected. The Pod spec should reveal whether the value arrives as an environment variable, argument, or file. The rollout plan should explain how running Pods move from the old value to the new one.

The same chain is useful during incident response. If a service behaves as though it has the wrong configuration, do not stop after `k get configmap`. Inspect the Pod template, the mounted files, the process environment when appropriate, and the application logs around startup or reload. This methodical path prevents the common mistake of fixing the source object while leaving old Pods alive with old values.

## Patterns & Anti-Patterns

Configuration patterns become valuable when several teams share a cluster. Without conventions, every workload invents its own key names, secret rotation method, and restart behavior. The result is not just messy YAML; it is slower incident response because responders must rediscover how each service receives its values before they can safely change anything.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| One image, namespace-local configuration | The same service runs in dev, staging, and production | The image stays portable while each namespace supplies its own ConfigMap and Secret values | Keep object names consistent across namespaces so manifests remain easy to promote |
| Explicit key references for important values | A container needs only a few keys or needs internal names | Reviewers can see exactly which keys become runtime inputs | Avoid `envFrom` for large shared objects because accidental keys become process state |
| File projection for config files and certificates | Applications expect structured files or TLS material | Kubernetes presents each key as a file without rebuilding the image | Teach the application to reload files or restart Pods deliberately during changes |
| Versioned immutable objects | Configuration changes should be released like code | New object names create explicit rollout boundaries and prevent accidental mutation | Add cleanup practices so old versioned objects do not accumulate forever |

These patterns all reduce surprise. They make the path from configuration object to running process visible during review. They also keep ownership boundaries clear: application teams define which values the application needs, platform teams define how sensitive data is protected, and release tooling coordinates when new values reach Pods. The exact YAML matters less than the shared operating model.

Anti-patterns usually begin as shortcuts. A developer puts a password in a ConfigMap because the demo needs to work quickly. A team uses `envFrom` because it saves lines. Someone patches a shared ConfigMap during an incident without checking which Pods consume it. Each choice can look harmless in isolation, but clusters magnify shortcuts because many workloads can depend on the same object shape.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|-------------------|
| Secrets stored in ConfigMaps | Sensitive values become visible to roles that can read ordinary configuration | Store credentials in Secrets, restrict RBAC, and enable encryption at rest |
| One giant ConfigMap per namespace | Unrelated changes become coupled and review becomes noisy | Split configuration by application or operational lifecycle |
| Assuming Secret update means application update | Running Pods may keep old environment variables or cached files | Document restart or reload behavior for each Secret consumer |
| Mounting over populated image directories | Projected files can hide files that were built into the image | Mount into a dedicated path or use specific key paths intentionally |
| Mutable shared configuration for broad fleets | One patch can affect many Pods with little rollout visibility | Use immutable, versioned objects for stable fleet-wide values |

A useful review question is, "Who else changes when this object changes?" If the answer is unclear, the configuration object is too broad or the ownership model is too vague. Good Kubernetes configuration is boring in the best way: small objects, obvious consumers, predictable updates, and no credentials where ordinary operators expect harmless settings.

## Decision Framework

Use this decision framework when you design or review workload configuration. Start with sensitivity, then move to shape, update behavior, and operational ownership. That order prevents the most damaging mistake first, while still producing a practical consumption method for the application.

| Question | Choose This | Reasoning |
|----------|-------------|-----------|
| Would disclosure grant access, reveal private material, or weaken authentication? | Secret | Sensitivity drives stricter RBAC, storage encryption, and handling rules |
| Is the value non-sensitive application behavior such as a flag, host, timeout, or config file? | ConfigMap | The data belongs outside the image but does not need Secret treatment |
| Does the application read the value only at startup? | Environment variable or command argument | Startup-only values require a restart anyway, so simple injection is acceptable |
| Does the application expect a file or support reload from disk? | Volume mount | File projection matches the application contract and can support reload workflows |
| Must changes be deliberate rollouts rather than in-place edits? | Immutable ConfigMap or Secret with a versioned name | Immutability protects stability and creates clear rollout history |
| Does the value need external rotation or central audit beyond Kubernetes? | External secret workflow plus Kubernetes Secret projection | Native Secret objects are a delivery point, not a complete enterprise secret manager |

You can also reason through the choice as a flow. First, classify the value as sensitive or non-sensitive. Second, decide whether the application wants a string, flag, or file. Third, decide whether change should happen by restart, reload, or new rollout. Fourth, document who owns the value and who may read it. That sequence produces a design that can survive both exams and incidents.

For KCNA, the exam-level distinction is usually straightforward: ConfigMaps hold non-sensitive configuration, Secrets hold sensitive data, environment variables are static until restart, and mounted files can update with application cooperation. For real work, the same facts become design constraints. The right answer is not merely the right object kind; it is the full path from object to process with the correct security and update expectations.

When the choice still feels ambiguous, write down the value, the reader, the consumer, and the change trigger in one sentence. For example, "the fraud endpoint is non-sensitive, read by the order service at startup, and changed only during planned releases." That sentence usually reveals the object kind, the injection method, and the rollout procedure more clearly than arguing about YAML fields in isolation.

## Did You Know?

- Kubernetes Secrets can be marked immutable, and this feature has been stable since Kubernetes 1.21, which makes it available in Kubernetes 1.35+ clusters without feature-gate ceremony.
- A single Secret object is limited to one mebibyte of data, which keeps the API server and backing store from becoming a general-purpose file delivery system.
- `stringData` is write-only convenience in practice: you submit plain text through the API, and Kubernetes stores the resulting values in the encoded `data` field.
- Projected ConfigMap and Secret volumes update eventually through kubelet refresh behavior, but environment variables and command arguments are fixed for the life of the container process.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Storing secrets in ConfigMaps | Teams see both objects as key-value stores and ignore the access-control difference | Put credentials in Secrets, restrict Secret RBAC, and enable encryption at rest for production clusters |
| Thinking base64 is encryption | Encoded Secret values look unreadable in YAML output | Treat base64 as transport encoding only, and protect the Secret object itself |
| Hardcoding configuration in images | The first environment works, so the shortcut hides until promotion | Build one image and inject environment-specific values through ConfigMaps and Secrets |
| Updating a ConfigMap and expecting environment variables to change | The API object changed, but the process environment was created at container start | Restart Pods or use a mounted file plus application reload behavior |
| Mounting a ConfigMap over an existing application directory | The projected volume hides files already present at the mount path | Mount into a dedicated config directory or map specific keys to specific paths |
| Using one broad `envFrom` for many keys | It saves YAML, but every key becomes process environment | Use explicit `env` entries for important values and keep shared objects small |
| Leaving mutable shared configuration for large fleets | A single edit can surprise many Pods and create API watch load | Use immutable, versioned ConfigMaps or Secrets for stable fleet-wide configuration |
| Assuming native Secrets are a full secret-management program | Kubernetes delivers values, but it does not define rotation ownership or external audit by itself | Combine Secrets with RBAC, encryption, audit logging, rotation procedures, and external managers when needed |

## Quiz

<details><summary>Your team updates a ConfigMap key from `LOG_LEVEL=debug` to `LOG_LEVEL=info`, but a running Pod still prints debug logs. The Deployment injects the key as an environment variable. What should you check and what action should you take?</summary>

Environment variables are fixed when the container process starts, so the running Pod will not see the new ConfigMap value. Check the Pod spec to confirm the value comes from `env` or `envFrom`, then restart or roll out the workload so new Pods receive the updated environment. If the team needs reload without restart, redesign the application to read a mounted file and reload it safely. This diagnoses configuration drift across the object, Pod spec, and process layers.

</details>

<details><summary>A payment service stores an API token in a ConfigMap because the token is just a string. During an audit, operators with ConfigMap read access can view it. What design change should you make?</summary>

Move the token into a Secret because disclosure would grant access to an external financial system. The fact that Secrets use base64 encoding by default does not make them encrypted, but it does let the cluster apply different RBAC, encryption-at-rest, audit, and handling practices. Review which roles can read Secrets, and avoid committing plain token values to Git. This compares ConfigMaps and Secrets by sensitivity and operational risk.

</details>

<details><summary>A TLS-enabled application expects certificate files under `/etc/tls` and can reload them from disk. The team currently passes certificate text through environment variables. Which consumption method is better and why?</summary>

A read-only Secret volume mount is the better fit because TLS libraries commonly expect certificate and key material as files. Mounted files keep multi-line certificate material out of the process environment and can support reload workflows when the application rereads the files. Environment variables would require a restart and can leak through diagnostics more easily. The Secret should still be protected with RBAC and storage encryption.

</details>

<details><summary>A platform team supports hundreds of Pods that all reference the same rarely changed configuration file. Accidental edits have caused outages. Which Kubernetes feature helps, and what rollout model should they use?</summary>

Use an immutable ConfigMap or Secret, depending on whether the data is sensitive. Immutability prevents in-place edits and can reduce watch load because Kubernetes does not need to watch the object for updates. To change the configuration, create a new versioned object and update workloads to reference that name. This makes the change a deliberate rollout rather than a quiet mutation of shared state.

</details>

<details><summary>A developer mounts a ConfigMap at `/etc/app`, and the application suddenly cannot find files that were built into the image at that directory. What happened?</summary>

The projected volume mounted at `/etc/app` hid the files that were already present in the container image at the same path. Kubernetes did not delete the image files, but the mount changed what the process sees at that directory. Mount the ConfigMap into a dedicated directory, or project specific keys to specific paths that do not cover existing application assets. This is a volume-design issue, not a ConfigMap data issue.

</details>

<details><summary>You run the same container image in dev, staging, and production, but each environment needs a different database host. How do you design the Kubernetes configuration?</summary>

Create namespace-local ConfigMaps with the same expected key, such as `DATABASE_HOST`, and let each environment supply its own value. The Deployment can reference the same object name and key in each namespace while the image remains unchanged. This follows the build-once, configure-per-environment model and keeps environment differences out of the container image. If credentials are also needed, put those in namespace-local Secrets instead.

</details>

<details><summary>A Secret was rotated in the cluster, but some Pods still authenticate with the old password while new Pods use the new one. What is the likely cause?</summary>

The older Pods probably consumed the Secret as an environment variable or command argument, so the value was captured at startup. New Pods started after the rotation received the new value, which explains the split behavior. Check the Pod template and running containers, then restart affected Pods or move to a file-based pattern if the application supports reload. Rotation plans should document exactly which workloads need restarts.

</details>

## Hands-On Exercise

In this lab, you will create non-sensitive configuration, create sensitive credentials, consume both from a Pod, observe update behavior, and practice the decision process. Use a disposable namespace so cleanup is simple. The commands assume Kubernetes 1.35+ behavior and use the `k` alias introduced at the start of the module.

```bash
alias k=kubectl
k create namespace config-lab
```

### Task 1: Create Configuration Objects

Create a ConfigMap for application settings and a Secret for credentials. The values are intentionally simple examples, not production credentials. Notice that the ConfigMap contains behavior settings, while the Secret contains authentication material.

```bash
k create configmap app-config \
  --namespace config-lab \
  --from-literal=DATABASE_HOST=mysql.default.svc \
  --from-literal=LOG_LEVEL=info \
  --from-literal=MAX_CONNECTIONS=100

k create secret generic db-credentials \
  --namespace config-lab \
  --from-literal=username=admin \
  --from-literal=password='example-password-only'
```

<details><summary>Solution notes for Task 1</summary>

The ConfigMap should appear with three keys under `data`, and the Secret should appear with encoded values under `data`. Use `k describe secret db-credentials --namespace config-lab` to confirm the keys without printing the values. Use `k get configmap app-config --namespace config-lab -o yaml` to confirm the non-sensitive settings directly.

</details>

### Task 2: Consume a ConfigMap as an Environment Variable and a Volume

Apply a Pod that reads the database host from an environment variable and reads the log level from a projected ConfigMap file. This deliberately uses both consumption patterns so you can compare their behavior later.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-consumer
  namespace: config-lab
spec:
  restartPolicy: Never
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "while true; do echo env=$DB_HOST file=$(cat /etc/config/LOG_LEVEL); sleep 10; done"]
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: DATABASE_HOST
    volumeMounts:
    - name: config-files
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: config-files
    configMap:
      name: app-config
```

```bash
k apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: config-consumer
  namespace: config-lab
spec:
  restartPolicy: Never
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "while true; do echo env=$DB_HOST file=$(cat /etc/config/LOG_LEVEL); sleep 10; done"]
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: DATABASE_HOST
    volumeMounts:
    - name: config-files
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: config-files
    configMap:
      name: app-config
EOF
k logs config-consumer --namespace config-lab --tail=5
```

<details><summary>Solution notes for Task 2</summary>

The logs should show the database host from the environment variable and the log level from the mounted file. If the Pod is still pending, use `k describe pod config-consumer --namespace config-lab` to check image pulls and scheduling events. The important observation is that the Pod has two separate paths from the same ConfigMap into the container.

</details>

### Task 3: Update the ConfigMap and Observe Drift

Patch the ConfigMap and watch the Pod logs. The file value may update after kubelet refreshes the projected volume, while the environment variable remains the same until the Pod restarts.

```bash
k patch configmap app-config \
  --namespace config-lab \
  --type merge \
  -p '{"data":{"DATABASE_HOST":"mysql-new.default.svc","LOG_LEVEL":"warn","MAX_CONNECTIONS":"100"}}'
k logs config-consumer --namespace config-lab --tail=10
```

<details><summary>Solution notes for Task 3</summary>

You should expect the environment value to remain `mysql.default.svc` in the running process. The file value can eventually become `warn`, but the exact timing depends on kubelet refresh behavior. This is the drift pattern you must diagnose in production: the API object, projected file, and process environment can disagree for valid reasons.

</details>

### Task 4: Mount a Secret as Read-Only Files

Create a second Pod that mounts the Secret as files. This mirrors the common pattern for credentials and certificates that applications read from disk.

```bash
k apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: secret-consumer
  namespace: config-lab
spec:
  restartPolicy: Never
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "ls -l /etc/secrets; sleep 3600"]
    volumeMounts:
    - name: secret-files
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-files
    secret:
      secretName: db-credentials
EOF
k logs secret-consumer --namespace config-lab
```

<details><summary>Solution notes for Task 4</summary>

The logs should list files named `username` and `password` under `/etc/secrets`. The Pod should not need the Secret values printed in logs for this verification. In real systems, avoid logging secret contents even during troubleshooting, because logs often have broader retention and access than the Secret object itself.

</details>

### Task 5: Create an Immutable Versioned ConfigMap

Create an immutable ConfigMap with a versioned name and inspect it. Then try to patch it so you can see the failure mode directly.

```bash
k apply -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-v2
  namespace: config-lab
immutable: true
data:
  DATABASE_HOST: mysql.default.svc
  LOG_LEVEL: info
  MAX_CONNECTIONS: "100"
EOF
k patch configmap app-config-v2 \
  --namespace config-lab \
  --type merge \
  -p '{"data":{"LOG_LEVEL":"debug"}}'
```

<details><summary>Solution notes for Task 5</summary>

The patch should fail because immutable ConfigMaps cannot be changed after creation. The correct update path is to create a new object name, update the workload reference, and roll out new Pods. This pattern turns configuration updates into visible deployment events.

</details>

### Task 6: Clean Up

Remove the namespace when you are done. Cleanup is part of the lab because configuration experiments often leave objects that future tests accidentally reuse.

```bash
k delete namespace config-lab
```

<details><summary>Solution notes for Task 6</summary>

The namespace deletion removes the ConfigMaps, Secrets, and Pods created by the lab. If deletion waits for a while, use `k get namespace config-lab` to observe progress. Avoid reusing lab namespaces for later modules unless you intentionally want leftover state.

</details>

Success criteria:

- [ ] You created a ConfigMap for non-sensitive application settings.
- [ ] You created a Secret for credential-style data.
- [ ] You consumed a ConfigMap as both an environment variable and a mounted file.
- [ ] You observed why a running process can keep stale environment values after a ConfigMap update.
- [ ] You mounted a Secret as read-only files without printing the secret value.
- [ ] You created an immutable, versioned ConfigMap and confirmed that in-place patching fails.

## Sources

- [Kubernetes Documentation: ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Kubernetes Documentation: Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Kubernetes Documentation: Configure a Pod to Use a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
- [Kubernetes Documentation: Distribute Credentials Securely Using Secrets](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/)
- [Kubernetes Documentation: Managing Secrets Using kubectl](https://kubernetes.io/docs/tasks/configmap-secret/managing-secret-using-kubectl/)
- [Kubernetes Documentation: Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Kubernetes Documentation: Good Practices for Kubernetes Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [Kubernetes Documentation: Assign Memory Resources to Containers and Pods](https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/)
- [Kubernetes Documentation: Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Kubernetes Documentation: Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
- [Kubernetes Documentation: RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)

## Next Module

Next, move into [Part 3: Cloud Native Architecture](/k8s/kcna/part3-cloud-native-architecture/module-3.1-cloud-native-principles/) to connect these workload mechanics to cloud native design principles and the CNCF ecosystem.
