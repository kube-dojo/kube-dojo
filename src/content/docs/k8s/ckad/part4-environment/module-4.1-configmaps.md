---
revision_pending: false
title: "Module 4.1: ConfigMaps"
slug: k8s/ckad/part4-environment/module-4.1-configmaps
sidebar:
  order: 1
lab:
  id: ckad-4.1-configmaps
  url: https://killercoda.com/kubedojo/scenario/ckad-4.1-configmaps
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Multiple ways to create and consume
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 1.1 (Pods), understanding of environment variables

---

## Learning Outcomes

After completing this module, you will be able to:

- **Create and validate** ConfigMaps from literals, files, directories, and declarative manifests.
- **Configure and compare** ConfigMap consumption through environment variables, `envFrom`, projected volume files, and `subPath` mounts.
- **Diagnose and debug** stale, missing, or masked configuration caused by update semantics, key names, namespace boundaries, and mount paths.
- **Design** a ConfigMap strategy that separates non-sensitive configuration from Secrets, keeps images reusable, and supports Kubernetes 1.35 operations.

## Why This Module Matters

Hypothetical scenario: a team ships a small web application through the same container image in development, staging, and production. The image is healthy, the Pod starts, and the Deployment rollout finishes, but production suddenly points at the staging database because the wrong runtime value was baked into the image during a rushed build. Rolling back the image fixes production but breaks staging, and every emergency rebuild creates another chance to mix code changes with environment-specific settings. ConfigMaps exist to keep those two concerns separate, so the image carries the application and the cluster injects the non-sensitive configuration that changes between environments.

That separation is not just a style preference. On the CKAD exam, ConfigMaps appear because they sit at the intersection of Pod design, command-line fluency, YAML editing, and debugging under time pressure. You need to create them quickly from literals, files, and directories, but you also need to recognize when a Pod is reading a ConfigMap as startup-only environment variables versus live-updating projected files. A correct answer often depends on one small detail: the namespace where the ConfigMap was created, the key name inside the object, or whether a volume mount has hidden files that were already present in the container image.

The restaurant menu analogy is still useful if you keep the limits in mind. A container image is the kitchen: it contains the equipment, recipes, and staff workflow needed to produce the meal. A ConfigMap is the specials board: it changes the day-specific choices without rebuilding the kitchen. The analogy stops where security begins, because the specials board is visible to the dining room. If the value is a password, private token, or certificate key, it belongs in a Secret or an external secret system, not in a ConfigMap.

In this module, you will build the same configuration object several ways and then wire it into Pods through the two main consumption paths. You will also practice the failure modes that matter in real clusters: stale environment values, missing keys, directory masking, `subPath` tradeoffs, and the operational cost of mutable versus immutable configuration. The goal is not to memorize a command list. The goal is to make a defensible decision when the exam or an incident gives you only symptoms and a few minutes.

## Creating ConfigMaps as Runtime Inputs

A ConfigMap is a namespaced Kubernetes API object that stores non-confidential key-value data. The key is always a string, and the value can be a short scalar such as `LOG_LEVEL=info` or a whole configuration file stored under a key such as `app.properties`. That sounds small, but it changes the release model of an application. Instead of producing one image per environment, you produce one image and attach the environment's runtime contract when the Pod is created.

The simplest creation path is imperative because it is fast and easy to inspect. Use literals when the values are short, when you are practicing an exam task, or when the configuration is naturally a set of environment-like names. The command below preserves the original single-key and multi-key examples, but it uses the full `kubectl` command so the block can run in a script or non-interactive shell. Before running this, what output do you expect from the final YAML view, and where will each literal appear under the ConfigMap object?

```bash
# Single key-value
kubectl create configmap app-config-single --from-literal=APP_ENV=production

# Multiple key-values
kubectl create configmap app-config-multi \
  --from-literal=APP_ENV=production \
  --from-literal=LOG_LEVEL=info \
  --from-literal=MAX_CONNECTIONS=100

# View the result
kubectl get configmap app-config-multi -o yaml
```

The output places literal values under the `data` field, not under `spec`, because a ConfigMap is not a controller that reconciles desired state into child objects. It is a data container that other Pod specs reference. That distinction matters when debugging. If a Pod does not pick up a value, you do not look for ConfigMap events that restart the Pod. You inspect the ConfigMap data, the consuming Pod spec, and the way the kubelet projected or injected the data at container start.

Files become useful when the application already expects a configuration file format. A Java service might read `application.properties`, nginx might read a `.conf` file, and a small script might read a JSON document. When you create a ConfigMap from a file, the default key name is the base filename. You can keep that default, remap the key to a different name, or add multiple files so the ConfigMap becomes a small bundle of named configuration documents.

```bash
# Create config files
echo "database.host=db.example.com
database.port=5432
database.name=myapp" > app.properties
echo "log.level=debug" > logging.properties

# Create ConfigMap from file
kubectl create configmap app-config-file --from-file=app.properties

# Custom key name
kubectl create configmap app-config-custom --from-file=config.properties=app.properties

# Multiple files
kubectl create configmap app-config-multifile \
  --from-file=app.properties \
  --from-file=logging.properties
```

The custom key form is easy to overlook, but it is one of the cleanest ways to adapt infrastructure to an existing application. If the repository stores a file named `settings-prod.properties` but the application insists on reading `application.properties`, you can create the ConfigMap key with the name the application expects. That avoids rebuilding the image or adding a wrapper script whose only job is to rename files at startup. It also makes the expected filename visible in the Kubernetes manifest instead of hiding it in container startup logic.

Directories are a convenience layer over the same file behavior. Each regular file in the directory becomes one ConfigMap key, and the file content becomes the value. Directory input is useful for local practice and small bundles, but it can surprise teams when editor backup files, temporary files, or unrelated notes are present in the directory. In production workflows, generated manifests from Kustomize, Helm, or another packaging tool often make the selected inputs more explicit.

```bash
# Create directory and files
mkdir ./config-dir
cp app.properties logging.properties ./config-dir/

# All files in directory become keys
kubectl create configmap app-config-dir --from-file=./config-dir/
```

Declarative YAML is the form you should prefer for reviewable changes, repeatable environments, and Git-based delivery. The object below contains the same mix of literal-style settings and a multi-line properties file. YAML block scalars are helpful because they preserve line breaks inside a single ConfigMap value, which is exactly what file-oriented applications need after the value is projected as a file in a volume.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: production
  LOG_LEVEL: info
  app.properties: |
    database.host=db.example.com
    database.port=5432
    database.name=myapp
```

ConfigMaps also support `binaryData` for byte-oriented values, but most CKAD ConfigMap tasks use `data` because the examples are text files and environment-like strings. Treat `binaryData` as a specialized tool, not a reason to store large artifacts or sensitive data in ConfigMaps. If the application needs a certificate private key, use a Secret. If it needs a large model file, route that through an image, artifact store, or volume designed for that payload.

Another useful boundary is ownership. A ConfigMap should usually have the same ownership and release cadence as the workload that consumes it. If three unrelated applications share one ConfigMap because it was convenient during a lab, a later edit can create a confusing cross-application blast radius. Splitting configuration by workload or component makes review easier because the object name, labels, and consumers describe one operational concern instead of a miscellaneous drawer of settings, and stale assumptions surface quickly.

Imperative and declarative creation are not competing religions; they are tools for different moments. During the CKAD exam, imperative creation with `--dry-run=client -o yaml` can generate a starting manifest quickly, although this module keeps the examples direct so the command behavior stays clear. During normal engineering work, a reviewed YAML file or a generated manifest gives you history, code review, and a cleaner rollback path. The important habit is to inspect the resulting keys and values before wiring them into a Pod, because Kubernetes will not infer that `APP_ENV` and `APP_ENVIRONMENT` were meant to be the same setting.

ConfigMaps are namespaced, so the same object name can safely mean different values in different environments. That is why teams often create `app-config` in a `development` namespace and another `app-config` in a `production` namespace. The Pod reference does not cross namespace boundaries. A Pod in `production` that references `app-config` only sees the ConfigMap named `app-config` in `production`, which is a useful guardrail when environment names are managed consistently.

```bash
# Create namespaces
kubectl create ns development
kubectl create ns production

# Development
kubectl create configmap app-config \
  --from-literal=APP_ENV=development \
  --from-literal=DEBUG=true \
  -n development

# Production
kubectl create configmap app-config \
  --from-literal=APP_ENV=production \
  --from-literal=DEBUG=false \
  -n production
```

The namespace pattern reduces accidental sharing, but it does not replace review. If both namespaces use the same object name, your troubleshooting commands must include the namespace or run in a context that is already set correctly. A common exam trap is to create the ConfigMap in the default namespace and then create the Pod somewhere else. The Pod will fail to resolve the reference even though `kubectl get configmap app-config` appears to work from your current namespace.

## Consuming ConfigMaps Through Environment and Files

Creating a ConfigMap only makes data available through the Kubernetes API. A Pod still needs an explicit reference that tells kubelet how to put that data into the container. Kubernetes supports two main consumption models: environment variables and projected volume files. The right model depends on how the application reads configuration, how often the values change, and whether you need the possibility of live reload after the container has started.

Use a single environment variable when you want to map one ConfigMap key to one container environment name. The environment variable name can differ from the ConfigMap key, which is useful when the upstream ConfigMap uses one naming convention and the application expects another. If the named key is absent and the reference is not marked optional, the Pod cannot start successfully because kubelet cannot build the container environment.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: APP_ENVIRONMENT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: APP_ENV
```

Use `envFrom` when you want every key in the ConfigMap to become an environment variable with the same name. This is compact and effective for settings that already follow environment variable naming rules. The tradeoff is that the Pod spec no longer documents each individual variable, and invalid environment names are skipped rather than magically rewritten into valid names. For exam work, `envFrom` is fast, but for production manifests you should decide whether the convenience is worth the reduced explicitness.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    envFrom:
    - configMapRef:
        name: app-config
```

Pause and predict: you update a ConfigMap that a Pod consumes via `envFrom`. Will the running container automatically pick up the new values, and would your answer change if the same ConfigMap were mounted as a projected volume file instead of injected as environment variables?

Environment variables are simple because most applications can read them, but they are startup-time data. Once the container process begins, the values are part of that process environment. Kubernetes does not rewrite the environment of an already running process after the ConfigMap changes. That makes environment variables a good fit for stable settings such as mode, feature flags that are only read at startup, and values where a Deployment restart is an acceptable part of the change process.

Projected volume files are a better fit when the application already reads files, when the file format matters, or when you want Kubernetes to update the mounted data after the ConfigMap changes. In the full-volume mount below, each ConfigMap key becomes a file under `/etc/config`, and the file content is the corresponding value. The container image does not need to contain those files, and the same image can receive different file content in different namespaces or releases.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
```

The full-volume mount has one major operational edge: mounting a volume at a directory path hides any files that were already present at that path in the container image. Kubernetes is not merging two directories. It is placing the projected volume at that mount point, so the image's original directory contents are no longer visible through that path. Stop and think: if `/etc/config` already contained default certificates or a base configuration shipped in the image, what would this mount do to those files, and how could you avoid hiding them?

When you only need selected keys, the `items` field gives you a whitelist and an optional filename remap. This is useful when a ConfigMap contains several settings but a particular container should see only one file. It also solves the filename mismatch problem: the ConfigMap key can be `app.properties`, while the file inside the container can be named `application.properties`. The choice is visible in the Pod spec, which is easier to review than a startup command that copies files around.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: application.properties
```

When you need to place one file into an existing directory without hiding the rest of the directory, use a `subPath` mount. The mount path names the final file location, and `subPath` selects the ConfigMap key that should appear at that location. This avoids the directory masking problem, but it changes update behavior. A `subPath` mount does not receive automatic ConfigMap updates after the container starts, so you should use it when preserving existing image files is more important than live projection.

```yaml
volumeMounts:
- name: config-volume
  mountPath: /etc/config/app.conf
  subPath: app.properties
```

The two consumption paths are easiest to remember as a data-flow diagram. The same ConfigMap can feed environment variables or files, but the container sees different shapes of data. Environment injection turns keys into process environment entries at startup. Volume projection turns keys into files under a mounted path. The application decides whether those files are read once, polled, watched, or ignored after startup.

```text
┌─────────────────────────────────────────────────────────────┐
│                    ConfigMap Usage                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ConfigMap: app-config                                      │
│  ┌─────────────────────────────────────┐                   │
│  │ APP_ENV: production                 │                   │
│  │ LOG_LEVEL: info                     │                   │
│  │ app.properties: |                   │                   │
│  │   database.host=db.example.com      │                   │
│  │   database.port=5432                │                   │
│  └─────────────────────────────────────┘                   │
│           │                    │                           │
│           ▼                    ▼                           │
│    ┌──────────────┐    ┌──────────────┐                   │
│    │   envFrom    │    │   volume     │                   │
│    │              │    │   mount      │                   │
│    │  $APP_ENV    │    │              │                   │
│    │  $LOG_LEVEL  │    │ /etc/config/ │                   │
│    └──────────────┘    │  app.properties│                  │
│                        └──────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

That diagram also shows why a ConfigMap does not automatically make an application configurable in every way. Kubernetes can put data in the container, but it cannot force the application to reread the data at the right time. If the application reads `/etc/config/app.properties` once during startup, a live-updated volume file will change on disk but the process may keep using the old in-memory settings. Good Kubernetes design and good application design meet at this boundary.

## Update Semantics and Debugging in Kubernetes 1.35

ConfigMap update behavior depends on the consumption method. Environment variables are copied into the container process environment at startup, so they require a Pod restart to change. Full ConfigMap volume mounts are updated by kubelet after the ConfigMap changes, subject to kubelet sync timing and cache behavior. `subPath` mounts are a special case because the mounted file path is bound at container start and does not receive the later projection updates that a normal ConfigMap volume receives.

| Method | Update Behavior |
|--------|-----------------|
| Environment variables | **NOT updated** - requires pod restart |
| Volume mounts | **Updated automatically** (kubelet sync period is commonly about 1 min) |
| subPath mounts | **NOT updated** - requires pod restart |

The table is short, but it drives many debugging decisions. If a Deployment reads `APP_ENV` through `envFrom`, editing the ConfigMap and waiting will not change the running process environment. The correct operational action is to restart or roll out replacement Pods so the new containers are created with the new environment. If a Pod reads a mounted file and the application watches that file correctly, waiting for kubelet projection can be enough. If the Pod uses `subPath`, the file location may look precise, but restart remains part of the update plan.

```bash
# Restart pods to pick up env var changes
kubectl rollout restart deployment/myapp

# For volume-mounted configs, wait or force sync
# Pods auto-update within the kubelet sync period
```

Debugging a ConfigMap issue starts with a simple chain of evidence. First, verify the ConfigMap exists in the same namespace as the Pod. Second, inspect the exact key names and values in the object. Third, inspect the Pod spec to see whether the reference uses `env`, `envFrom`, a volume, selected `items`, or `subPath`. Finally, check the running container in the same shape the application sees: print the environment for environment injection, list the mounted directory for files, or read the specific file path the application opens.

The quick reference below keeps the original command coverage while using runnable full commands. It is tempting to jump straight to `edit`, but in a timed exam or a production incident you should inspect before changing. A typo in a key can look like an application bug, a namespace mismatch can look like a missing object, and a mounted directory can look like an empty configuration directory when it is actually masking image content.

```bash
# Create
kubectl create configmap NAME --from-literal=KEY=VALUE
kubectl create configmap NAME --from-file=FILE
kubectl create configmap NAME --from-file=DIR/

# View
kubectl get configmap NAME -o yaml
kubectl describe configmap NAME

# Edit
kubectl edit configmap NAME

# Delete
kubectl delete configmap NAME
```

Kubernetes 1.35 still treats ConfigMaps as ordinary API objects with normal namespace and RBAC behavior. Anyone who can read the ConfigMap can read its data, and the data is not a place for secrets. Secrets have their own object type, and even Secrets require careful cluster encryption and access control. ConfigMaps are for non-sensitive configuration such as log levels, feature toggles that are safe to expose, file names, hostnames that are not credentials, and application modes.

Immutable ConfigMaps are another operational choice. Adding `immutable: true` prevents later changes to the object data, which can reduce accidental edits and lower kubelet watch pressure for stable configuration. The tradeoff is that updates require creating a new ConfigMap name and changing the Pod template reference, which is often a good release pattern but less convenient for quick experiments. Use immutability when the configuration should move with a release, not when you expect an operator to tune it in place during a lab.

## Validating and Troubleshooting ConfigMap References

ConfigMap troubleshooting is faster when you separate object problems from projection problems. An object problem means Kubernetes cannot find or read the ConfigMap or key that the Pod references. A projection problem means the object exists, but the container does not see the expected environment variable or file. Those two categories lead to different evidence. Object problems show up in Pod events and kubelet messages, while projection problems show up in the container's environment, filesystem, or application logs.

Start with the namespace and object name because those failures are common and cheap to eliminate. A Pod does not search the cluster for a matching ConfigMap name. It resolves the reference inside its own namespace, using the exact object name written in the Pod spec. If you created `app-config` in `default` and applied the Pod in `production`, both resources can look correct when inspected separately, but the reference still fails. This is why reliable troubleshooting commands include `-n` once namespaces enter the scenario.

After the object exists in the right namespace, compare keys exactly. ConfigMap keys are not schema-aware, and Kubernetes will not treat `APP_ENV`, `APP_ENVIRONMENT`, and `app_env` as related values. A single-key `env` reference fails differently from `envFrom`: the explicit reference points at one required key, while `envFrom` attempts to turn all valid keys into environment variables. If the application sees a blank variable, the cause may be a typo in the app command, a missing key, or a key that never became a valid environment variable.

The optional flag changes failure behavior, not data quality. Kubernetes lets you mark some ConfigMap references optional, which can be useful for defaults or extension points, but optional references can also hide mistakes. If the application truly has safe defaults, optional references may be appropriate. If the setting is required for correctness, an optional reference turns a clear startup failure into a runtime mystery. In exam tasks, avoid optional unless the prompt explicitly asks for it or the scenario clearly describes fallback behavior.

For file projections, inspect both the mounted path and the ConfigMap key-to-path mapping. A full ConfigMap volume creates one file per key at the mount path unless `items` narrows the selection. If `items` is present and the named key is wrong, the projected file will not appear as expected. If the mount path is a directory, remember that the directory view comes from the volume. If the mount path is a file with `subPath`, remember that updates require Pod replacement.

File permissions can also be part of the diagnosis, although they are less common in introductory CKAD tasks. ConfigMap volumes are mounted read-only, and applications should treat them as inputs, not writable state. If a process tries to edit its own config file in place, the failure is not a ConfigMap creation issue. The correct design is to write runtime state somewhere else, such as an `emptyDir` or application data volume, and keep the ConfigMap as the source of desired configuration.

Deployment rollouts add another layer. Editing a ConfigMap does not automatically change the Deployment's Pod template, so the Deployment controller has no reason to create a new ReplicaSet just because a referenced ConfigMap changed. If your operating model needs every ConfigMap edit to produce new Pods, include a deliberate rollout step or use a packaging pattern that changes a Pod template annotation when configuration content changes. This is why many Helm charts add checksum annotations for ConfigMaps, while simpler labs often use `kubectl rollout restart`.

The best debugging question is "where did the value stop moving?" If the ConfigMap object has the right key and value, the data made it into the API server. If the Pod spec references the right object and key, the desired projection is declared. If the container environment or mounted file shows the right value, Kubernetes delivered it to the process boundary. If the application still behaves incorrectly, the next investigation is application reload behavior, parsing rules, or a different configuration source overriding the value.

Before changing a live configuration, predict the blast radius. A ConfigMap can be shared by many Pods in the same namespace, so an edit that fixes one Deployment may affect another consumer. A volume-mounted change may reach running Pods on kubelet's projection schedule, while an environment-variable change waits for Pod replacement. A versioned ConfigMap name makes the blast radius explicit because only Pods that reference the new name receive it. That extra object name is often less confusing than a mutable shared object with unclear consumers.

Hypothetical scenario: an application has both `LOG_LEVEL` from an environment variable and `log.level` inside a mounted properties file. The operator changes only the ConfigMap key used by the file, then expects the process log level to change immediately. A careful diagnosis asks which source the application actually reads for log level, whether it rereads the file, and whether the process environment has a different value that wins during startup. ConfigMaps can deliver data in multiple shapes, but application precedence still decides behavior.

For exam practice, build a short mental checklist before you type: namespace, object name, key name, consumption method, mount path, update behavior, and application read behavior. That list is faster than trying random edits because each item rules out a category of failure. It also keeps you from using the wrong fix. Restarting a Pod helps environment variables and `subPath` mounts, but it does not fix a typo in a ConfigMap key. Editing a ConfigMap helps data values, but it does not fix a mount path that hides required image files.

## Worked Example: Nginx Configuration Without Rebuilding the Image

The original module used nginx to show why file-based configuration is a natural ConfigMap use case. Nginx already reads configuration files, so a ConfigMap can provide a file without building a custom image. The example below writes an `nginx.conf`, creates a ConfigMap from it, and mounts that one file over `/etc/nginx/conf.d/default.conf` with `subPath`. The point of `subPath` here is deliberate: nginx images already contain useful directory structure, and replacing the entire directory would be a different operational choice.

```bash
# nginx.conf
cat << 'EOF' > nginx.conf
server {
    listen 80;
    server_name localhost;
    location / {
        root /usr/share/nginx/html;
    }
}
EOF

kubectl create configmap nginx-config --from-file=nginx.conf

# Mount in pod
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx-custom
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
  volumes:
  - name: config
    configMap:
      name: nginx-config
EOF
```

After this Pod starts, the container sees a file at `/etc/nginx/conf.d/default.conf` whose content came from the ConfigMap key `nginx.conf`. Other files in `/etc/nginx/conf.d` remain visible because the volume did not replace the whole directory. The cost is update behavior: changing the ConfigMap will not update that `subPath` file in the running container. If you need a new nginx configuration, restart the Pod or roll a Deployment so the file is mounted fresh during container creation.

Exercise scenario: a logging agent container ships with certificates and defaults under `/etc/agent`, but your custom logging configuration needs to appear beside those files. If you mount the entire ConfigMap at `/etc/agent`, the projected volume hides the certificates and defaults from the image. The safer design is to create a ConfigMap key such as `custom.conf` and mount it at `/etc/agent/custom.conf` with `subPath`, then document that updating the file requires replacing the Pod. This is not a dramatic story about a real outage; it is the exact mechanics of volume mounting applied to a common agent layout.

The worked example also demonstrates a review habit that scales beyond nginx. When you see `mountPath` ending in a directory, ask whether the image had important content there. When you see `mountPath` ending in a file and `subPath` present, ask whether the release plan includes restarts for updates. When you see `envFrom`, ask whether every key is a valid and intended environment variable name. These questions turn ConfigMap work from syntax recall into operational reasoning.

## Patterns & Anti-Patterns

Patterns and anti-patterns for ConfigMaps are mostly about choosing the right boundary. A ConfigMap should describe non-sensitive runtime choices that are allowed to vary outside the image. It should not become a dumping ground for credentials, large blobs, generated state, or values that the application cannot reload safely. The table below focuses on concrete choices you can defend during design, review, or debugging.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| One image, per-namespace ConfigMap | The same application runs in development, staging, and production | The image stays reusable while each namespace owns its runtime values | Keep object names consistent, but always include namespaces in operational commands |
| File projection for file-native apps | The application already reads `.conf`, `.properties`, JSON, or YAML files | Kubernetes projects keys as files without image rebuilds | Decide whether the app watches files or needs a restart after changes |
| Explicit key selection with `items` | A ConfigMap has several keys, but one container needs only selected files | The Pod spec documents which keys become visible and what filenames they use | Missing selected keys can block startup unless optional behavior is configured |
| Immutable release ConfigMaps | Configuration changes should move with reviewed releases | New ConfigMap names make rollbacks and audit trails clearer | Use generated names or versioned names so Pod templates change on update |

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Storing passwords in ConfigMaps | Plain text values are easy to read through the API and tooling | Use Secrets with appropriate RBAC and encryption at rest where required |
| Mounting a ConfigMap over a populated directory | Files from the image are hidden by the volume mount | Mount selected keys into file paths with `subPath`, or mount into an empty dedicated directory |
| Expecting env vars to live-update | The process environment is fixed after container start | Restart Pods for environment changes, or move reloadable data to files |
| Using one giant ConfigMap for unrelated concerns | Small changes create broad blast radius and confusing ownership | Split by application component, lifecycle, or ownership boundary |

The anti-patterns are not moral failures; they are usually shortcuts that worked during a first test and then became expensive under change. A full-directory mount is quicker than a precise file mount, but it changes the filesystem view. A giant ConfigMap is easy to create, but it makes review and ownership vague. Environment variables are familiar, but they do not reload. The senior move is to choose the smallest mechanism that matches how the application actually reads configuration.

## Decision Framework

Use the decision framework when you are choosing between literals, file projection, full volume mounts, selected keys, `subPath`, Secrets, and immutable release patterns. The first question is sensitivity. If a value is confidential, a ConfigMap is the wrong object even if the syntax is convenient. The second question is shape. If the application expects a file, preserve the file shape instead of flattening it into environment variables. The third question is lifecycle. If the value must change without replacing Pods, environment variables and `subPath` mounts do not meet that requirement by themselves.

| Decision Question | Choose This | Avoid This |
|-------------------|-------------|------------|
| Is the value sensitive? | Secret or external secret manager | ConfigMap |
| Does the app read environment variables at startup? | `env` or `envFrom` | File mount unless the app expects files |
| Does the app read a named file? | ConfigMap volume with `items` path mapping | Rebuilding the image just to change a file |
| Must the mounted data update in a running Pod? | Full ConfigMap volume and app-level reload support | `subPath` without a restart plan |
| Must existing image files stay visible? | `subPath` file mount or dedicated empty directory | Full mount over a populated image directory |
| Should config change only through releases? | Immutable, versioned ConfigMaps | In-place edits with unclear rollout history |

Which approach would you choose here and why: a service reads `LOG_LEVEL` only at startup, while a sidecar process reads a routing table from `/etc/routes/routes.yaml` every few seconds? A defensible answer is to put `LOG_LEVEL` in an environment variable and the routing table in a projected ConfigMap volume. If the sidecar truly rereads the file, it can observe kubelet's projection updates. If the main service needs a new log level, restart the Pod or roll the Deployment so the process environment is recreated.

For CKAD work, the framework also helps with speed. If the task says "create a ConfigMap from this file and mount it as `/etc/app/app.conf`," create from file and use either `items` or `subPath` depending on whether the target is a directory projection or one file inside an existing directory. If the task says "expose all ConfigMap keys as environment variables," reach for `envFrom`. If the symptom says "ConfigMap changed but Pod still has old value," identify the consumption method before changing anything.

## Did You Know?

- **ConfigMaps have a 1 MiB size limit.** The Kubernetes API server enforces object size constraints, so large configuration payloads belong in another storage mechanism or an application-specific delivery path.
- **ConfigMaps are namespaced objects.** A Pod can reference a ConfigMap only in its own namespace, which is why namespace mismatches are such common lab and exam failures.
- **Environment variable values from ConfigMaps are fixed at container startup.** Editing the ConfigMap later does not rewrite the environment of an already running process.
- **The `immutable: true` field became stable in Kubernetes 1.21.** It can protect stable configuration from accidental edits and reduce watch overhead for clusters with many mounted ConfigMaps.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Expecting env vars to update | Environment variables are copied into the process at container start | Restart the Pod or roll the Deployment after ConfigMap changes |
| Using `subPath` while expecting live updates | `subPath` mounts bind the selected file at startup | Use a full ConfigMap volume for projection updates, or plan a restart |
| Storing secrets in ConfigMaps | ConfigMap data is plain text through normal API reads | Move sensitive values to Secrets or an approved external secret system |
| Creating the ConfigMap in the wrong namespace | ConfigMaps are namespaced and Pod references do not cross namespaces | Recreate or apply the ConfigMap in the Pod's namespace and verify with `-n` |
| Typing the wrong key name | Kubernetes matches exact key strings and does not infer intent | Inspect `kubectl get configmap NAME -o yaml` and match the Pod reference exactly |
| Mounting over a populated directory | A volume mount hides image files at the mount path | Mount into an empty directory or use `subPath` for one file |
| Using `envFrom` for messy key names | Not every ConfigMap key is a valid environment variable name | Use explicit `env` mappings or rename the ConfigMap keys |

## Quiz

**Question 1. Exercise scenario:** A developer updates a ConfigMap with new database connection settings and confirms the object is correct with `kubectl get configmap app-config -o yaml`. The Pod still uses the old settings, and its manifest shows `envFrom` under the container. What should you check and what change makes the new values appear?

A. Wait for kubelet to project the new data into the process environment.
B. Restart or roll the Pod because environment variables are set at container startup.
C. Add `items` to the ConfigMap volume because `envFrom` needs file path mapping.
D. Convert the ConfigMap to a Secret because Secrets update environment variables live.

<details>
<summary>Answer and reasoning</summary>

B is correct because values consumed through `env` or `envFrom` are copied into the container environment when the container starts. A is wrong because kubelet projection applies to mounted volumes, not to a running process environment. C is wrong because `items` belongs to ConfigMap volume projection, not environment injection. D is wrong because Secrets have the same startup behavior when consumed as environment variables.

</details>

**Question 2. Exercise scenario:** You mount a ConfigMap at `/etc/nginx/conf.d/`, and nginx fails because the default file that came from the image is no longer visible. Which diagnosis best explains the failure, and which fix preserves the image's other files?

A. The ConfigMap is in the wrong namespace; recreate it in `kube-system`.
B. The volume mount hides the image directory; mount one key as a file with `subPath`.
C. The ConfigMap is too large; split it into several smaller ConfigMaps.
D. The image cannot read ConfigMaps; rebuild nginx with the file included.

<details>
<summary>Answer and reasoning</summary>

B is correct because a volume mounted at a directory path replaces the container's view of that directory. A is wrong because namespace mismatch would prevent resolution before this filesystem symptom appeared, and `kube-system` is not a general fix. C is unrelated unless the API rejected the ConfigMap. D gives up the main benefit of runtime configuration and is not required for nginx to read a mounted file.

</details>

**Question 3. Exercise scenario:** A Pod is in the `production` namespace and references `app-config`, but `kubectl get configmap app-config` from your shell shows the expected object and the Pod still reports that the ConfigMap was not found. What is the most likely explanation?

A. The ConfigMap exists in a different namespace than the Pod.
B. ConfigMaps cannot be referenced by Pods created from YAML.
C. The ConfigMap must be immutable before a Pod can consume it.
D. The Pod can only consume ConfigMaps through `subPath`.

<details>
<summary>Answer and reasoning</summary>

A is correct because ConfigMaps are namespaced, and a Pod reference resolves only inside the Pod's namespace. The shell command may have used the default namespace or a different current context namespace. B is wrong because YAML is the normal declarative way to reference ConfigMaps. C is wrong because immutability is optional, and D is wrong because Pods can consume ConfigMaps through environment variables and volumes.

</details>

**Question 4. Exercise scenario:** An application expects a file named `/etc/app/application.properties`, but your ConfigMap key is `app.properties`. You want the mounted filename to match the application without changing the image. Which approach is best?

A. Use `items` to map the key `app.properties` to the path `application.properties`.
B. Store the value under `binaryData` so Kubernetes renames it automatically.
C. Put the file name in an environment variable and hope the app discovers it.
D. Add `immutable: true` because immutable ConfigMaps remap file names.

<details>
<summary>Answer and reasoning</summary>

A is correct because `items` lets the Pod volume map a ConfigMap key to a specific projected file path. B is wrong because `binaryData` is for bytes encoded as base64-style data, not filename remapping. C is unreliable unless the application already supports that environment variable. D is wrong because immutability controls whether data can change, not how keys become paths.

</details>

**Question 5. Exercise scenario:** A review finds a database password next to `LOG_LEVEL` and `APP_ENV` in a ConfigMap. The team says it is acceptable because only the application Pod references the object. What is the right response?

A. Keep it because Pod references make ConfigMaps private.
B. Move the password to a Secret or approved secret manager and keep only non-sensitive settings in the ConfigMap.
C. Add the password through `envFrom` because environment variables are hidden.
D. Mark the ConfigMap immutable because immutable data is encrypted.

<details>
<summary>Answer and reasoning</summary>

B is correct because ConfigMaps are for non-sensitive data and can be read as plain text by users or controllers with access to the object. A is wrong because a Pod reference does not make the object private. C is wrong because environment variables can be inspected in several ways and do not change the sensitivity of the source. D is wrong because immutability prevents edits; it does not encrypt the stored data.

</details>

**Question 6. Exercise scenario:** A sidecar watches files under `/etc/routes`, and you need route updates to appear without rebuilding the image. The image has no important files under `/etc/routes`. Which ConfigMap consumption method best fits?

A. Full ConfigMap volume mounted at `/etc/routes`, paired with application reload behavior.
B. `envFrom`, because all keys become route files automatically.
C. `subPath` mount for every route file, because `subPath` is the only live-updating path.
D. Literal creation only, because file-based ConfigMaps cannot update.

<details>
<summary>Answer and reasoning</summary>

A is correct because a full ConfigMap volume can receive kubelet projection updates, and the sidecar's file-watching behavior can react to those changes. B is wrong because `envFrom` creates environment variables, not files. C is wrong because `subPath` mounts do not receive later ConfigMap projection updates. D is wrong because ConfigMaps created from files or literals can both be projected as volume files.

</details>

**Question 7. Exercise scenario:** You want configuration changes to be reviewed, versioned, and rolled out with a Deployment template change rather than edited in place. Which design best matches that operating model?

A. Use one mutable ConfigMap named `app-config` forever and edit it during incidents.
B. Use immutable, versioned ConfigMaps and update the Pod template reference during release.
C. Put all configuration into image labels so Pods never need ConfigMaps.
D. Store unrelated applications in one ConfigMap so there is only one object to review.

<details>
<summary>Answer and reasoning</summary>

B is correct because immutable, versioned ConfigMaps make configuration part of the release artifact and force a Pod template change for rollout. A is wrong for this operating model because in-place edits are harder to audit and roll back. C misuses image metadata and does not provide runtime files or environment variables. D increases blast radius and makes ownership unclear.

</details>

## Hands-On Exercise

Exercise scenario: create a small configuration set, consume it as environment variables, consume another ConfigMap as files, then practice several CKAD-speed drills. The commands assume you are working in a disposable namespace or local training cluster. If you run these in a shared cluster, add `-n YOUR_NAMESPACE` consistently and clean up the objects at the end.

### Success Criteria

- [ ] Create and validate ConfigMaps from literals, files, directories, and YAML manifests.
- [ ] Configure and compare environment variables, `envFrom`, volume files, and `subPath` mounts.
- [ ] Diagnose and debug stale, missing, or masked configuration by checking keys, namespaces, update behavior, and mount paths.
- [ ] Design a ConfigMap strategy that keeps non-sensitive configuration separate from Secrets for Kubernetes 1.35 workloads.
- [ ] Clean up every Pod and ConfigMap created during the lab.

### Setup: Create a Literal ConfigMap

```bash
# Create ConfigMap from literals
kubectl create configmap web-config \
  --from-literal=APP_COLOR=blue \
  --from-literal=APP_MODE=production

# Verify
kubectl get configmap web-config -o yaml
```

This setup creates a short ConfigMap that is naturally shaped like environment variables. The verification step matters because it confirms the exact key names before a Pod tries to consume them. If you see `APP_COLOUR` in the object but `APP_COLOR` in the Pod, Kubernetes will not guess the spelling you intended.

### Setup: Create from a Directory

Each regular file in the directory becomes one ConfigMap key. This matches the directory workflow shown earlier in the theory section and is useful when you already have a small folder of configuration files on disk.

```bash
mkdir -p ./config-dir
echo "database.host=db.example.com" > ./config-dir/app.properties
echo "log.level=debug" > ./config-dir/logging.properties

kubectl create configmap web-config-dir --from-file=./config-dir/
kubectl get configmap web-config-dir -o yaml

kubectl delete cm web-config-dir
rm -rf ./config-dir
```

<details>
<summary>Solution notes</summary>

The resulting ConfigMap should contain two keys named after the filenames: `app.properties` and `logging.properties`. If extra files appear, check the directory for editor backups or temporary files before creating the object.

</details>

### Setup: Create from Declarative YAML

Declarative YAML is the form you should prefer for reviewable changes and Git-based delivery. Apply the manifest below, inspect the keys under `data`, then delete the object.

```bash
cat << 'EOF' > /tmp/app-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-yaml
data:
  APP_ENV: production
  LOG_LEVEL: info
  app.properties: |
    database.host=db.example.com
    database.port=5432
    database.name=myapp
EOF

kubectl apply -f /tmp/app-config.yaml
kubectl get configmap app-config-yaml -o yaml
kubectl delete cm app-config-yaml
```

<details>
<summary>Solution notes</summary>

Literal-style keys such as `APP_ENV` appear as plain strings under `data`, while `app.properties` preserves line breaks through the YAML block scalar. This is the same shape you will wire into Pods through environment variables or volume mounts in the next parts.

</details>

### Part 1: Environment Variables

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: env-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo Color: $APP_COLOR, Mode: $APP_MODE && sleep 3600']
    envFrom:
    - configMapRef:
        name: web-config
EOF

# Verify environment
kubectl wait --for=condition=Ready pod/env-pod --timeout=30s
kubectl logs env-pod
```

<details>
<summary>Solution notes</summary>

The log output should include the color and mode values from the ConfigMap. If the Pod does not become ready, inspect `kubectl describe pod env-pod` and look for messages about missing ConfigMaps or invalid references. If the values are blank, compare the ConfigMap keys with the environment variable names used in the command.

</details>

### Part 2: Volume Mount

```bash
# Create config file
kubectl create configmap nginx-index --from-literal=index.html='<h1>Hello from ConfigMap</h1>'

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: vol-pod
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
  volumes:
  - name: html
    configMap:
      name: nginx-index
EOF

# Test
kubectl wait --for=condition=Ready pod/vol-pod --timeout=30s
kubectl exec vol-pod -- cat /usr/share/nginx/html/index.html
```

<details>
<summary>Solution notes</summary>

The file `/usr/share/nginx/html/index.html` should contain the HTML value from the ConfigMap key named `index.html`. This full-directory mount is acceptable for the lab because the goal is to replace the default nginx page. In a production image directory that contained required files, you would check whether a more precise `items` or `subPath` mount was safer.

</details>

### Cleanup

```bash
kubectl delete pod env-pod vol-pod
kubectl delete configmap web-config nginx-index
```

### Practice Drill 1: Create from Literals

```bash
kubectl create configmap drill1 --from-literal=KEY1=value1 --from-literal=KEY2=value2
kubectl get cm drill1 -o yaml
kubectl delete cm drill1
```

<details>
<summary>Solution notes</summary>

Confirm that both keys appear under `data`. The short resource name `cm` is acceptable as a Kubernetes resource abbreviation, while the command still uses the full `kubectl` binary. Delete the ConfigMap after inspection so later drills start from a clean state.

</details>

### Practice Drill 2: Create from File

```bash
echo "setting1=on
setting2=off" > /tmp/settings.conf

kubectl create configmap drill2 --from-file=/tmp/settings.conf
kubectl get cm drill2 -o yaml
kubectl delete cm drill2
```

<details>
<summary>Solution notes</summary>

The key should be `settings.conf` because Kubernetes uses the base filename when no custom key name is provided. If you needed a different key, you would use `--from-file=desired-name=/tmp/settings.conf`. This drill prepares you for volume mounts where the key becomes a filename.

</details>

### Practice Drill 3: Environment Variables

```bash
kubectl create configmap drill3 --from-literal=DB_HOST=localhost --from-literal=DB_PORT=5432

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'env | grep DB && sleep 3600']
    envFrom:
    - configMapRef:
        name: drill3
EOF

kubectl wait --for=condition=Ready pod/drill3 --timeout=30s
kubectl logs drill3
kubectl delete pod/drill3 cm/drill3
```

<details>
<summary>Solution notes</summary>

The log should show both database-related variables. If you edit the ConfigMap after the Pod starts, the log will not change because the process environment is fixed. Delete both resources before repeating the drill so you do not collide with existing object names.

</details>

### Practice Drill 4: Volume Mount

```bash
kubectl create configmap drill4 --from-literal=config.json='{"debug": true}'

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill4
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'cat /config/config.json && sleep 3600']
    volumeMounts:
    - name: cfg
      mountPath: /config
  volumes:
  - name: cfg
    configMap:
      name: drill4
EOF

kubectl wait --for=condition=Ready pod/drill4 --timeout=30s
kubectl logs drill4
kubectl delete pod/drill4 cm/drill4
```

<details>
<summary>Solution notes</summary>

The ConfigMap key `config.json` should appear as a file under `/config`. Because this is a full ConfigMap volume, later ConfigMap projection updates can change the mounted file, although the application must still reread the file to use the new content. BusyBox simply prints the file once, so this drill demonstrates projection rather than live reload.

</details>

### Practice Drill 5: Specific Key Mount

```bash
kubectl create configmap drill5 \
  --from-literal=app.conf='main config' \
  --from-literal=log.conf='log config'

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill5
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls /config && cat /config/application.conf && sleep 3600']
    volumeMounts:
    - name: cfg
      mountPath: /config
  volumes:
  - name: cfg
    configMap:
      name: drill5
      items:
      - key: app.conf
        path: application.conf
EOF

kubectl wait --for=condition=Ready pod/drill5 --timeout=30s
kubectl logs drill5
kubectl delete pod/drill5 cm/drill5
```

<details>
<summary>Solution notes</summary>

Only `application.conf` should be visible in `/config`, even though the ConfigMap also has `log.conf`. The `items` list selected one key and remapped its filename. This is the pattern to use when a ConfigMap contains several keys but a container should receive only a precise subset.

</details>

### Practice Drill 6: Complete Scenario

```bash
# Create nginx config
cat << 'NGINX' > /tmp/nginx.conf
server {
    listen 8080;
    location / {
        return 200 'Custom Config Works!\n';
        add_header Content-Type text/plain;
    }
}
NGINX

kubectl create configmap drill6-nginx --from-file=/tmp/nginx.conf

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill6
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
  volumes:
  - name: nginx-config
    configMap:
      name: drill6-nginx
EOF

# Verify nginx loaded the mounted ConfigMap-backed config
kubectl wait --for=condition=Ready pod/drill6 --timeout=30s
kubectl exec drill6 -- nginx -T 2>&1 | grep -F "Custom Config Works!"

kubectl delete pod/drill6 cm/drill6-nginx
```

<details>
<summary>Solution notes</summary>

The `nginx -T` command dumps the effective nginx configuration, and the `grep` match should print the `Custom Config Works!` response rule from the mounted file. The `subPath` mount places one ConfigMap key at the file path nginx expects while preserving the rest of the directory. If you change `/tmp/nginx.conf` and recreate the ConfigMap, replace the Pod as well because the `subPath` file does not live-update.

</details>

## Learner check

> When you delete mixed resource types in one `kubectl delete` command, use slash notation such as `kubectl delete pod/drill3 cm/drill3` so each argument names both the resource type and the object.

## Sources

- https://kubernetes.io/docs/concepts/configuration/configmap/
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/
- https://kubernetes.io/docs/concepts/configuration/secret/
- https://kubernetes.io/docs/concepts/storage/volumes/#configmap
- https://kubernetes.io/docs/concepts/storage/volumes/#using-subpath
- https://kubernetes.io/docs/concepts/configuration/overview/
- https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.35/#configmap-v1-core
- https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#-em-configmap-em-
- https://kubernetes.io/docs/concepts/workloads/pods/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- https://12factor.net/config

## Next Module

[Module 4.2: Secrets](../module-4.2-secrets/) - Manage sensitive data securely.
