---
revision_pending: false
title: "Module 2.3: Kustomize"
slug: k8s/ckad/part2-deployment/module-2.3-kustomize
sidebar:
  order: 3
lab:
  id: ckad-2.3-kustomize
  url: https://killercoda.com/kubedojo/scenario/ckad-2.3-kustomize
  duration: "40-50 minutes"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Template-free customization for Kubernetes
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.1 (Deployments), basic YAML understanding

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** Kustomize base and overlay layouts that keep shared Kubernetes manifests stable while allowing environment-specific changes.
- **Implement** transformations, image overrides, generators, and patches with `kubectl kustomize` and `kubectl apply -k`.
- **Diagnose** rendering and apply failures caused by wrong paths, patch target mismatches, selector changes, or generated name behavior.
- **Evaluate** when Kustomize is a better deployment fit than Helm and when Helm's packaging model is the right tradeoff.

## Why This Module Matters

Hypothetical scenario: your team owns one web application that runs in development, staging, and production. The Deployment, Service, labels, and port layout are mostly identical, but production needs more replicas, a different namespace, a fixed image tag, and stricter runtime settings. If every environment owns a complete copy of the YAML, the copies begin to drift. One person updates the selector in development, another updates the image in production, and a third forgets that the Service depends on the same label shape in every environment.

Kustomize solves that problem by treating Kubernetes YAML as the source material instead of replacing it with a template language. A base contains ordinary manifests that `kubectl` could already apply. An overlay references that base, then layers changes such as labels, namespaces, image tags, generated ConfigMaps, or targeted patches. The result is still ordinary Kubernetes YAML, but it is rendered from a small composition graph that makes shared intent visible and environment-specific intent explicit.

This matters for the CKAD because Kustomize is built into `kubectl`, and the exam rewards fast, reliable command habits. It also matters outside the exam because a clean Kustomize layout gives reviewers a useful question to ask: "What changed between dev and prod?" Instead of reading two almost identical Deployment files line by line, they can inspect the overlay and see only the customization. In this module you will build that structure, preview the rendered output, apply it with `kubectl apply -k`, and debug the failures that usually appear when overlays become more than a toy example.

## Kustomize as Layered Kubernetes YAML

Kustomize begins with a deliberately plain idea: keep the resource YAML valid before customization, then describe edits next to it. That is different from a text template. A Helm template can contain conditionals, loops, and values that do not form a valid Kubernetes object until rendering time. Kustomize prefers a smaller surface: start with real objects, then add transformations that know enough about Kubernetes references to keep related fields consistent when names and namespaces change.

The most important mental model is that a base is not an abstract parent class. It is a directory of resources that can be rendered on its own, and an overlay is another directory that imports the base and applies a controlled set of changes. For a small application, the base might contain one Deployment and one Service. For a larger application, it may also include ServiceAccounts, NetworkPolicies, ConfigMaps, and Ingress resources. The overlay should not repeat those files unless the entire object is genuinely different.

| Concept | Description |
|---------|-------------|
| **Base** | Original, unmodified Kubernetes resources |
| **Overlay** | Customizations applied on top of base |
| **Patch** | Modifications to specific fields |
| **kustomization.yaml** | File that defines what to customize |

The table is short, but the operational distinction is important. A base is where you put the durable shape of the application. An overlay is where you put the local decision for a specific environment, cluster, tenant, or exam task. A patch is where you say, "for this rendered variant, change this field on that object." The `kustomization.yaml` file is the bill of materials and transformation plan for the directory.

```
┌─────────────────────────────────────────────────────────┐
│                   Kustomize Flow                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Base                    Overlay                        │
│  ┌─────────────┐        ┌─────────────┐                │
│  │ deployment  │───────▶│  + replicas │                │
│  │   service   │        │  + env vars │                │
│  │  configmap  │        │  + labels   │                │
│  └─────────────┘        └─────────────┘                │
│         │                     │                         │
│         └─────────┬───────────┘                         │
│                   ▼                                     │
│            ┌─────────────┐                              │
│            │  Combined   │                              │
│            │  Resources  │                              │
│            └─────────────┘                              │
│                   │                                     │
│                   ▼                                     │
│         kubectl apply -k ./                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

The diagram shows a rendering pipeline, not a controller running in the cluster. Kustomize runs on the client side when you execute `kubectl kustomize`, `kubectl apply -k`, or `kubectl delete -k`. The API server receives the final rendered objects, just as it would receive objects from separate YAML files. That means debugging starts before you touch the cluster: render the output, inspect the names, selectors, images, namespaces, and generated references, then apply only when the rendered YAML matches the intended state.

Pause and predict: if a Service selector is `app: web` in the base and an overlay changes labels on both the Deployment template and Service selector, what would break if only one side changed? The answer should guide how you use label transformers. Selectors are contracts between objects. A label change that reaches Pods but not Services can make the rollout look healthy while traffic quietly goes nowhere.

Kustomize also has a boundary that is easy to miss. It is excellent at composing a known set of manifests, but it is not trying to become a general-purpose programming language. When your deployment needs optional subcharts, deep conditional branching, reusable versioned packages, or install-time value schemas, Helm may be a better tool. When your problem is "same resources, different environment details," Kustomize keeps the configuration closer to the Kubernetes API.

## Building a Base Kustomization

A base directory should be boring. That is the point. You want a teammate to open the base and see the application anatomy without searching through environment-specific noise. If the base Deployment says the container listens on port 80, the Service selects `app: web`, and the resource name is `web-app`, those choices should remain true across environments unless a real environment boundary requires a difference.

The smallest useful layout has a `kustomization.yaml` beside the resources it manages. Kustomize discovers only the resources listed in that file; it does not automatically apply every YAML file in the directory. This explicit list prevents surprising applies when scratch files, temporary manifests, or old experiments sit nearby. It also gives you an exam-friendly checklist: if a rendered object is missing, first check whether it is listed under `resources:`.

```
my-app/
├── kustomization.yaml
├── deployment.yaml
└── service.yaml
```

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
```

The `apiVersion` and `kind` identify the file as a Kustomize configuration rather than a Kubernetes workload object. Under `resources`, each path is relative to the directory containing this `kustomization.yaml`. A resource can be a file, a directory containing another kustomization, or in some Kustomize workflows a remote reference, but for CKAD work you should expect local files and local bases. Keep paths simple and verify them from the directory you are rendering.

```bash
# Preview what will be applied
kubectl kustomize ./my-app/

# Apply the kustomization
kubectl apply -k ./my-app/

# Delete resources
kubectl delete -k ./my-app/
```

Previewing and applying are separate habits. `kubectl kustomize ./my-app/` prints the rendered YAML and exits without changing the cluster. `kubectl apply -k ./my-app/` renders the same composition and sends it to the API server. `kubectl delete -k ./my-app/` renders the same set of objects and deletes those objects by identity. If a directory path is wrong, a resource file is missing, or a patch fails to match, preview catches it before the API server sees anything.

Exercise scenario: you inherit a directory that contains `deployment.yaml`, `service.yaml`, and `old-service.yaml`, but only the first two are referenced by `resources:`. A teammate asks why `old-service.yaml` did not deploy. The correct answer is not "Kustomize missed it." The correct answer is that `kustomization.yaml` is the authoritative resource list, and unlisted files are ignored. That explicitness is safer than directory globbing because it makes deployment membership reviewable.

For exam speed, use `kubectl kustomize` as your local diff viewer. Scan the rendered `metadata.name`, `metadata.namespace`, selectors, container image, and patch result before applying. If your output is long, pipe to `less` locally when available, but keep the core command copy-paste safe. In constrained labs, a simple `kubectl kustomize ./path | sed -n '1,120p'` is often enough to confirm the first resource names and the fields you changed.

## Transformations: Names, Labels, Namespaces, and Images

Transformations are broad edits that Kustomize can apply across resources. They are useful when a change is not tied to one field in one object. A namespace belongs on almost every namespaced resource. A name prefix might apply to all objects in an overlay so development and production resources can coexist. A label can be added to resources for ownership, environment tracking, or selection. The value of a transformation is consistency: one declaration changes the rendered set in a predictable way.

Labels deserve extra care because some labels are descriptive and others are selectors. A descriptive label can be added freely to help humans and automation find objects. A selector label is part of a relationship between a controller, its Pods, and Services that route to those Pods. Kustomize's newer `labels` transformer lets you choose whether the label should be included in selectors and Pod templates. That choice is safer than blindly adding labels everywhere.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

labels:
- pairs:
    app: my-app
    environment: production
  includeSelectors: true
  includeTemplates: true
```

Use `includeSelectors: true` only when you mean to change selectors as part of the rendered identity. If a Service and Deployment both start with matching selectors, Kustomize can keep the relationship consistent when the transformer applies to both sides. If you are adding an operational label such as `owner: platform` or `cost-center: shared`, you often do not want that label in immutable selectors. Selector changes can force controller replacement or cause apply failures on existing Deployments.

```yaml
commonAnnotations:
  owner: team-platform
  managed-by: kustomize
```

Annotations are usually safer for metadata that should not participate in selection. They can hold ownership hints, rollout notes, or tool markers without changing how Services find Pods. Kustomize can add common annotations across resources, but you should still avoid putting secrets or volatile values there. An annotation change on a Pod template can trigger a rollout, which is useful for some workflows and surprising for others.

```yaml
namePrefix: prod-
nameSuffix: -v1
```

Result: `deployment` becomes `prod-deployment-v1`

Name transformations look simple, but they are one of Kustomize's strongest features because it understands common Kubernetes name references. If a Deployment references a generated ConfigMap, or a ServiceAccount is referenced by a Pod template, Kustomize can update those references when the name is transformed. This is much safer than a search-and-replace because Kubernetes resource names appear in different fields depending on kind and API version.

```yaml
namespace: production
```

All resources will be deployed to this namespace.

The namespace transformer is a good example of why preview matters. Cluster-scoped resources do not receive a namespace because the Kubernetes API does not allow one. Namespaced resources do. If the namespace does not exist, `kubectl apply -k` will fail when it tries to create namespaced objects there. Kustomize renders desired YAML; it does not create namespaces implicitly unless a Namespace object is listed as a resource.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

images:
- name: nginx
  newTag: "1.21"

- name: myapp
  newName: my-registry.com/myapp
  newTag: v2.0.0
```

Image overrides are the cleanest way to move one base across environments without editing the Deployment. The base can use a readable image such as `nginx:1.20` or `myapp:latest`, while the overlay pins the environment's chosen tag or registry. The `name` field matches the image name found in the resource. `newTag` changes the tag, and `newName` changes the repository portion. This keeps image promotion visible in the overlay instead of buried in a copied Deployment.

Before running this, what output do you expect if a Deployment uses `nginx:1.20` and the overlay declares `images: [{ name: nginx, newTag: "1.21" }]`? You should expect the rendered Deployment to keep the same container name and other fields, but the image field should become `nginx:1.21`. If the output does not change, check whether the image name in the resource actually matches `nginx`, or whether the image is already written with a different registry prefix.

These transformations compose, so order matters conceptually even when you do not write it as a script. Kustomize reads resources, applies generators, applies transformations, resolves references, and emits final objects. When debugging, inspect the final YAML rather than assuming a transformation applied because the declaration exists. A declaration with the wrong target or an image name that does not match is harmless in the worst way: it produces valid YAML that does not contain the change you intended.

## Generating ConfigMaps and Secrets

ConfigMaps and Secrets are often the first objects that make learners appreciate Kustomize. In plain Kubernetes, you can create them as static YAML. In Kustomize, generators let you describe the data source in `kustomization.yaml`, then Kustomize creates the object and updates references. The important behavior is the content hash suffix. By default, generated ConfigMaps and Secrets receive a name suffix derived from their content, so a data change produces a new object name.

That hash is useful because Pods do not automatically restart just because the contents of an existing ConfigMap changed. If a Deployment references `app-config-abc123` and the generator data changes, Kustomize renders a new name such as `app-config-def456` and updates the Deployment reference. That Pod template change triggers a rollout. In other words, the generated name turns configuration content into part of the workload revision.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=info
  - API_URL=http://api.example.com
```

The generated ConfigMap name will not usually be exactly `app-config`. It will include a suffix unless you disable that behavior. References inside known fields are updated, which is why a Deployment can still say it wants `app-config` in the source manifest while the rendered output points to the suffixed name. This is another place where previewing the output teaches you what the API server will see.

```yaml
configMapGenerator:
- name: app-config
  files:
  - config.properties
  - settings.json
```

Generating from files is useful when configuration already lives in application-like formats. Each file becomes a key in the ConfigMap unless you use a custom key mapping. This keeps large configuration blobs out of the Deployment manifest while still making the full rendered result inspectable. For CKAD practice, literals are faster to type, but file-based generation is common in real repositories because it mirrors how applications read local configuration.

The same kustomization can declare multiple Secret generators in one list — literals for credentials and files for TLS material:

```yaml
secretGenerator:
- name: db-credentials
  literals:
  - username=admin
  - password=secret123
- name: tls-certs
  files:
  - tls.crt
  - tls.key
  type: kubernetes.io/tls
```

Secrets generated by Kustomize are Kubernetes Secret objects, not a secret management system. The generated YAML still contains base64-encoded values that should be handled carefully in repositories and logs. For exam exercises, a placeholder value is enough to demonstrate mechanics. In production, pair Kustomize with an approved secret workflow such as sealed secrets, external secret controllers, or a secure CI process that injects secret material outside the public source tree.

Stop and think: Kustomize appends a hash suffix to generated ConfigMaps, for example `app-config-abc123`. Why would this be useful? The useful part is not the uniqueness by itself. The useful part is that a configuration content change becomes a name change, and that name change updates the Pod template reference. Kubernetes then has a clear reason to create new Pods with the new configuration.

By default, Kustomize adds a hash suffix to generated ConfigMaps and Secrets:

- `app-config` becomes `app-config-abc123`
- References are automatically updated

Disable with (useful if legacy systems require fixed names, though it prevents automatic rolling updates):

```yaml
generatorOptions:
  disableNameSuffixHash: true
```

Disabling the suffix is a tradeoff, not a cleanup trick. A fixed name can be necessary when an external system, older manifest, or manual process expects the exact object name. The cost is that a data change may not trigger a rollout by itself because the Pod template reference remains unchanged. If you disable the suffix, decide how the workload will pick up configuration changes. That may mean a manual `kubectl rollout restart`, an annotation bump, or a controller that watches ConfigMaps.

The old generated object may remain after an update, and that is not automatically a bug. It can support rollbacks because a previous ReplicaSet may still reference the previous hashed name. In a small namespace, old generated objects are easy to spot and clean manually. In a long-lived environment, you need a cleanup policy that respects rollback windows. Do not delete old ConfigMaps blindly during an active rollout investigation.

## Patches and Overlay Composition

Patches are for changes that are specific enough that a broad transformer would be too blunt. Changing all resource names belongs in a transformer. Changing the replica count of one Deployment belongs in a patch. Adding resource limits to every Deployment might be a targeted patch with a kind selector, but it needs review because container lists and names vary across applications. Patches give you precision, and precision requires matching the right object.

The most common patching failure is a target mismatch. A patch names `my-app`, but the base Deployment is named `web-app`. Or the overlay adds `namePrefix: prod-`, and the learner thinks the patch must target `prod-web-app` rather than the original name. Kustomize patches usually target the pre-transformed resource identity from the base, then transformations are applied to the final output. When in doubt, render before and after removing the patch to see what changed.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 5
```

This inline patch reads like a small Kubernetes object because it is a strategic merge style patch. It identifies the object by kind and name, then provides only the fields that should be added or changed. The patch does not need to repeat the entire Deployment. That is why patches are more reviewable than copying the full object into an overlay: the reviewer sees exactly which field is being overridden.

```yaml
patches:
- path: increase-replicas.yaml
```

**increase-replicas.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
```

Patch files are better when the patch is more than a few lines or when several overlays reuse the same patch shape. A file also keeps `kustomization.yaml` readable. The tradeoff is navigation: the person reviewing the overlay must open another file to understand the change. For small exam tasks, inline patches are fast. For team repositories, patch files often age better because they can be named after the intent, such as `increase-replicas.yaml` or `add-resource-limits.yaml`.

For precise modifications:

```yaml
patches:
- target:
    kind: Deployment
    name: my-app
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 5
    - op: add
      path: /metadata/labels/version
      value: v2
```

JSON patches are useful when you need an exact operation such as `replace`, `add`, or `remove` at a JSON pointer path. They are less forgiving than strategic merge patches because the path must match the rendered object structure. That strictness is useful for surgical edits and risky for learners who have not inspected the YAML. If you use a JSON patch, preview immediately and confirm the modified field appears exactly where you expected.

What would happen if your overlay references `../../base` but the base directory was renamed to `common`? You should see an accumulation or path error before anything is applied. The fast diagnosis is to render the overlay and read the path in the error. Then inspect the overlay's `resources:` list, not the base manifests. The failing resource reference lives in the overlay because that is where the relative path is declared.

```yaml
patches:
- target:
    kind: Deployment
  patch: |-
    - op: add
      path: /spec/template/spec/containers/0/resources
      value:
        limits:
          memory: 256Mi
          cpu: 200m
```

Targeting all Deployments can save time, but it also hides assumptions. The JSON pointer above assumes the first container is the one that should receive limits. In a one-container CKAD exercise, that is fine. In a real multi-container Pod, index `0` may be a sidecar, an init pattern may change later, or a new container may be inserted before the application. Prefer named strategic merge patches when container identity matters, and use broad target patches only when the resource structure is uniform by policy.

Patching should follow a simple workflow. First render the base alone so you know the starting shape. Then render the overlay and inspect only the changed fields. Finally apply the overlay when the rendered result matches the intent. This workflow catches wrong names, wrong paths, and unintended selector edits while the cost is still a local command. It also builds the CKAD habit of proving output before changing cluster state.

## Overlays for Environments

An overlay directory turns Kustomize from a single-directory convenience into a maintainable deployment pattern. The base says what the application is. Each overlay says how that application should differ for one target. Development may use one replica, a development namespace, and a fast-moving image tag. Production may use more replicas, a production namespace, a pinned release tag, and stricter configuration. The shared base remains unchanged.

```
my-app/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── overlays/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── prod/
│       └── kustomization.yaml
```

This layout is common because it makes review paths obvious. A change under `base/` affects every overlay that imports it. A change under `overlays/prod/` affects production only. That is a strong ownership signal. It also helps with rollback reasoning: if production broke after an overlay-only change, you can focus on the production overlay. If every environment broke after a base change, start in the base.

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
```

The base kustomization should avoid environment-specific namespace, replica, and image promotion decisions unless every environment truly shares them. It is fine for a base to include stable labels that describe the application, but be cautious with labels that imply environment or release channel. A base that already says `environment: production` forces every non-production overlay to undo it, which is the opposite of clean composition.

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: dev-
namespace: development

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 1

images:
- name: my-app
  newTag: dev-latest
```

The development overlay is intentionally small. It imports the base, prefixes names, selects a namespace, sets one replica, and points at a development image tag. Because the patch targets the base name `my-app`, the overlay remains readable even though the rendered Deployment will be named `dev-my-app`. That distinction is worth practicing because many learners waste time patching the post-prefix name and wondering why the patch does not match.

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: prod-
namespace: production

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 5

images:
- name: my-app
  newTag: v1.2.3

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=warn
  - ENABLE_DEBUG=false
```

The production overlay introduces a different kind of change: configuration generation. It still does not copy the Deployment or Service. Instead, it describes the production differences. This keeps the environment delta compact enough for review. A reviewer can ask whether five replicas are enough, whether `v1.2.3` is the approved tag, and whether `LOG_LEVEL=warn` is appropriate without revalidating the entire Deployment shape.

```bash
# Apply dev
kubectl apply -k overlays/dev/

# Apply prod
kubectl apply -k overlays/prod/

# Preview
kubectl kustomize overlays/prod/
```

Apply commands should point at the overlay you intend to deploy, not at the base, when environment-specific changes are required. Applying the base directly is sometimes useful for a local smoke test, but it bypasses the overlay decisions. In a cluster where development and production can coexist, name prefixes and namespaces make the rendered identities distinct. In a single exam namespace, you may omit prefixes if the task expects exact names, but then you must avoid applying multiple overlays into the same namespace.

Which approach would you choose here and why: copy the full Deployment into `overlays/prod/`, or keep the Deployment in `base/` and patch only replicas and image tag? The patch approach is better when the object shape is shared because it reduces drift and review noise. Copying the full object is justified only when production is genuinely a different workload shape, not merely a different environment setting.

Overlays can also become too clever. If an overlay has many patches that undo other patches, imported components whose order is hard to reason about, and generated names that external systems depend on, the design has outgrown the simple "base plus environment delta" model. At that point, split the base, introduce clearer components, or consider whether a packaging tool with explicit values is more honest. Kustomize stays maintainable when each layer has a single reason to exist.

## Previewing, Applying, and Debugging Fast

Kustomize debugging is mostly disciplined rendering. If `kubectl kustomize overlays/prod/` does not render the object you expect, `kubectl apply -k overlays/prod/` will not magically fix it. Start with the local output and classify the failure. A path error means Kustomize could not read a file or directory. A patch mismatch means it could not find the target. A valid render with the wrong image or labels means the transformer declaration did not match what you thought it matched.

```bash
# Preview kustomization
kubectl kustomize ./

# Apply kustomization
kubectl apply -k ./

# Delete kustomization
kubectl delete -k ./

# View specific overlay
kubectl kustomize overlays/prod/
```

These four commands are the exam quick reference because they cover the full loop. Preview, apply, delete, and render a specific overlay. Use full `kubectl` commands in scripts and copied examples. Many engineers use a short alias interactively, but aliases are not reliable in non-interactive shells and should not appear in runnable examples. Copy-paste safety matters when a lab timer is running.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
```

A minimal kustomization is often enough to begin. Add one transformation at a time and render after each one. If you add namespace, labels, images, generators, and patches all at once, the first render failure gives you too many suspects. Incremental rendering is not slow; it is the fastest way to isolate the mistake. On Kubernetes 1.35 and newer exam environments, the `kubectl` integration is expected behavior, so the local render loop should be part of your normal workflow.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

namespace: my-namespace
namePrefix: prod-

labels:
- pairs:
    app: my-app
  includeSelectors: true
  includeTemplates: true

images:
- name: nginx
  newTag: "1.21"

configMapGenerator:
- name: config
  literals:
  - KEY=value
```

When a rendered output is wrong, read it as the API server would. Are the resource names correct after prefixing? Are the namespaces present where allowed? Do the Service selectors still match the Pod template labels? Did the image tag change on the intended container? Did the generated ConfigMap name appear in the Deployment reference? These checks are more useful than staring at the kustomization file because the rendered output is the truth that `apply` will send.

For path failures, run `pwd` and inspect the overlay path you passed to `kubectl`. Relative paths inside `resources:` are resolved from the kustomization file's directory, not from the shell directory in a vague global sense. For patch failures, compare `apiVersion`, `kind`, `metadata.name`, and sometimes namespace. For generator surprises, check whether the suffix hash is expected. For selector surprises, inspect both sides of the relationship, not just the field you edited.

Debugging should end with an apply only after the render is credible. If apply fails after a good render, the error has moved from Kustomize composition to Kubernetes validation, admission, or cluster state. That might mean a namespace does not exist, an immutable selector changed on an existing Deployment, or an image pull policy is not accepted by policy. Keeping render failures and API failures separate saves time because they require different fixes.

One practical debugging trick is to classify the failure by the earliest command that can reproduce it. If `kubectl kustomize overlays/prod/` fails, stay out of the cluster and repair the kustomization graph. If render succeeds but `kubectl apply -k overlays/prod/` fails, keep the rendered output visible while reading the API error. A namespace error, immutable selector error, or admission denial is no longer a Kustomize composition problem. It is a Kubernetes apply problem using YAML that Kustomize happened to generate.

When the rendered YAML is valid but surprising, compare resource identities before comparing every field. Check `kind`, `metadata.name`, and `metadata.namespace` first because those fields decide what object will be created, updated, or deleted. Then check relationship fields such as selectors, ServiceAccount references, ConfigMap references, and container images. This order prevents noisy diffs from distracting you. A generated ConfigMap suffix may look dramatic, but a mismatched Service selector is usually the more urgent operational failure.

For overlays, render the base and overlay separately when the source of a change is unclear. The base render tells you the shared starting point. The overlay render tells you the final state after imports, generators, transformers, and patches. If a field is already wrong in the base, fix the base or decide whether every environment should inherit that shape. If the field is correct in the base and wrong only in the overlay, inspect the overlay's transformers and patches before touching the shared files.

This same method helps during cleanup. `kubectl delete -k` renders the kustomization and deletes the objects identified by the current render. If you changed names, prefixes, namespaces, or generator options after applying, the delete command may no longer point at the same object identities. Preview the current render before deleting. If it no longer matches the applied identities, either restore the previous overlay long enough to delete cleanly or delete the leftover objects explicitly after confirming their names.

Finally, treat generated resources as part of the rendered contract. A generated ConfigMap or Secret is not an invisible helper; it is a real Kubernetes object with a real name, labels, data keys, and references from workloads. If an application cannot find configuration after a rollout, inspect the rendered generated object and the rendered Pod template together. The mistake may be a missing key, an unexpected suffix because a reference was not updated, or a fixed-name generator option that prevented a rollout from happening.

## Patterns & Anti-Patterns

Kustomize works best when the repository structure tells the same story as the deployment process. Put stable application shape in the base, put environment decisions in overlays, and use patches for focused changes. That is not just style. It gives reviewers a smaller diff, gives operators a predictable render path, and gives learners a clean way to reason about what `kubectl apply -k` will change.

| Pattern | When to Use | Why It Works |
|---------|-------------|--------------|
| Base plus environment overlays | The same app runs in dev, staging, and production with small differences | Shared manifests stay in one place while overlays expose environment deltas |
| Preview before apply | Any time a kustomization includes transformations, generators, or patches | The rendered YAML reveals name, selector, namespace, image, and patch results before cluster mutation |
| Small patches with clear targets | One resource needs a field change such as replicas, image-related policy, or resources | Reviewers can see the intended override without rereading an entire copied object |
| Hash-suffixed generators | Workloads should roll when configuration content changes | Generated names make configuration changes visible in Pod template references |

The patterns all share one property: they reduce hidden state. A base plus overlays makes inheritance explicit through `resources:`. Preview before apply separates local rendering from cluster mutation. Small patches show intent. Hash-suffixed generators make configuration revisions visible. When a Kustomize repository becomes hard to debug, it is usually because one of those visibility properties has been lost.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Copying full manifests into every overlay | Environments drift and reviewers cannot tell which differences are intentional | Keep shared objects in the base and patch only real deltas |
| Adding labels to selectors casually | Existing Deployments may reject immutable selector changes, or Services may stop matching Pods | Decide whether a label is descriptive or selective before setting `includeSelectors` |
| Disabling generator hashes by default | Config changes may not roll Pods because object names stay fixed | Keep hashes unless a fixed-name integration requires otherwise |
| Patching by list index in complex Pods | A new sidecar or reordered container list can patch the wrong container | Prefer patches that match named containers when workload shape is not guaranteed |

Anti-patterns are attractive because they feel faster at the start. Copying a manifest is faster than learning a patch for the first change. Adding labels everywhere is faster than thinking about selectors. Disabling hashes makes names easier to read. Index-based JSON patches are quick to type. The cost appears later, when the rendered output is valid but operationally wrong. The better alternative is slightly more deliberate and much easier to audit.

## Decision Framework

Choose Kustomize when your primary problem is controlled variation of Kubernetes manifests. Choose Helm when your primary problem is packaging, distribution, and parameterized installation. The difference is not "simple tool versus advanced tool" in a moral sense. It is a difference in where complexity lives. Kustomize keeps complexity in overlays and patches against valid YAML. Helm keeps complexity in templates, values, chart metadata, and release management.

```
Start
  |
  v
Do you already have valid Kubernetes YAML?
  |-- no --> Need a reusable install package with values? --> Use Helm
  |
 yes
  |
  v
Are differences mostly labels, namespaces, images, replicas, config, or small patches?
  |-- yes --> Use Kustomize overlays
  |
 no
  |
  v
Do you need conditionals, loops, dependencies, or chart distribution?
  |-- yes --> Use Helm
  |
 no
  |
  v
Split the manifests or simplify the deployment shape, then reassess.
```

This framework keeps you from forcing every deployment through the tool you happen to know best. If a third-party project ships a Helm chart and you need versioned release management, Helm is the natural fit. If your team has first-party YAML and needs development, staging, and production variants, Kustomize is usually lower ceremony. If you need both, a common pattern is to render a Helm chart and then use Kustomize as a post-render customization layer, but that adds another boundary to debug.

| Situation | Prefer Kustomize | Prefer Helm |
|-----------|------------------|-------------|
| Existing YAML needs environment variants | Yes, overlays and patches fit directly | Only if packaging or values schemas are also needed |
| CKAD task asks for built-in customization | Yes, `kubectl apply -k` is available | Usually unnecessary unless the task explicitly uses Helm |
| Application has many optional components | Possible, but overlays can become tangled | Yes, templates and values handle conditional structure |
| Team wants release objects and chart versions | Kustomize alone does not provide Helm release history | Yes, Helm tracks releases and chart packaging |
| Need to patch third-party rendered YAML | Yes, Kustomize is useful as a post-render step | Helm may still own the initial render |

For CKAD practice, default to Kustomize when the task mentions `kustomization.yaml`, overlays, patches, generated ConfigMaps, or `kubectl apply -k`. Do not reach for Helm simply because Helm can also produce Kubernetes YAML. The exam is testing whether you can compose and render the resources with the built-in tool. For production engineering, make the same decision based on maintainability: use the tool whose failure modes your team can debug under pressure.

## Did You Know?

- **Kustomize is built into kubectl since Kubernetes 1.14.** That means a Kubernetes 1.35 or newer exam environment can render and apply kustomizations without a separate Kustomize binary.

- **Hash suffixes on generated ConfigMaps and Secrets are rollout signals.** A content change creates a new generated name, and Kustomize updates references so the Pod template changes.

- **The `labels` transformer can include or exclude selectors.** That choice matters because selector labels define relationships, while descriptive labels are mostly for humans and automation.

- **Kustomize and Helm can be combined, but that adds a debugging boundary.** Helm may render a chart first, then Kustomize may patch the rendered YAML, so preview each stage.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Wrong path to base | The overlay uses a relative path such as `../../base`, but the directory moved or the path was typed from the wrong mental location | Render with `kubectl kustomize overlays/name/`, read the path error, and fix the `resources:` entry relative to that overlay's `kustomization.yaml` |
| Patch target name mismatch | The patch targets the post-prefix name or a stale resource name instead of the base object identity | Match the target to the base `apiVersion`, `kind`, and `metadata.name`, then preview the overlay to confirm the rendered field changed |
| Missing `apiVersion` in kustomization | The file looks like ordinary YAML, so the required Kustomize header is skipped | Start every kustomization with `apiVersion: kustomize.config.k8s.io/v1beta1` and `kind: Kustomization` |
| Forgetting `resources` section | Files exist in the directory, but Kustomize applies only resources that are listed or imported | List every resource file or base directory explicitly under `resources:` |
| Not previewing before apply | The overlay is treated like a static manifest, so mistakes are discovered only after cluster mutation | Run `kubectl kustomize <dir>` first and inspect names, namespaces, selectors, images, generated references, and patches |
| Adding selector labels without intent | Labels feel harmless, but selectors affect Deployment immutability and Service-to-Pod routing | Use `includeSelectors` only when selector relationships should change, and use annotations or non-selector labels for metadata |
| Disabling generator hash suffixes reflexively | Stable generated names look easier to read, but Pods may not roll when config changes | Keep suffix hashes unless a fixed-name integration requires them, and define a separate restart mechanism if hashes are disabled |
| Patching container index `0` in shared workloads | The patch works in a one-container example but can hit the wrong container when sidecars are added | Patch by container name when possible, or enforce a policy that makes index-based patches safe |

## Quiz

<details>
<summary>Question 1: Your team has a base deployment that works in development. For production, you need to change the namespace to `production`, increase replicas to 5, and use image tag `v2.1.0` instead of `latest` without modifying the base files. How do you set this up with Kustomize?</summary>

Create a production overlay such as `overlays/prod/kustomization.yaml` that references `../../base`, sets `namespace: production`, declares an `images` override, and patches the Deployment replica count. The base remains the shared application definition, while the overlay captures only the production differences. This is better than copying the full Deployment because future base fixes flow into production automatically. Before applying, run `kubectl kustomize overlays/prod/` and confirm the rendered namespace, image tag, and replica count are correct.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namespace: production
images:
- name: nginx
  newTag: "v2.1.0"
patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web-app
    spec:
      replicas: 5
```

</details>

<details>
<summary>Question 2: You run `kubectl apply -k ./` and get an error that a listed resource has no such file or directory. The file appears to exist when you list the current shell directory. What should you check first?</summary>

Check the path from the perspective of the `kustomization.yaml` file that contains the `resources:` entry. Relative resource paths are resolved from that file's directory, so your shell directory can mislead you if you are rendering an overlay from elsewhere. Also check exact filename spelling, case, and `.yaml` versus `.yml`. The fix is to update the `resources:` path or run the command against the intended directory, then preview again before applying.

</details>

<details>
<summary>Question 3: A colleague asks why the team should not use Helm for every environment variation. Give two concrete cases where Kustomize is the better fit.</summary>

Kustomize is better when the team already has valid Kubernetes YAML and only needs environment differences such as namespace, image tag, replicas, labels, generated ConfigMaps, or small patches. It is also a strong fit when you need to customize third-party rendered YAML without maintaining a fork, because patches can be applied after the base resources are available. Helm is still useful for packaging, dependencies, release records, and conditional templates. The decision should follow the problem shape, not tool preference.

</details>

<details>
<summary>Question 4: You update a `configMapGenerator` literal and reapply the overlay. The new Pods reference a new ConfigMap name, but the old ConfigMap still exists. Is this a failure?</summary>

This is expected behavior when generated names include a content hash. The data change produces a new generated ConfigMap name, and Kustomize updates references so the Deployment's Pod template changes and a rollout can happen. The old ConfigMap may remain so older ReplicaSets or rollbacks can still reference the configuration they were created with. You can clean old generated ConfigMaps after the rollback window, but you should not treat their temporary presence as a render failure.

</details>

<details>
<summary>Question 5: A production overlay uses `namePrefix: prod-`, and a patch targets a Deployment named `prod-api`. The base Deployment is named `api`, and the patch does not apply. What is the likely problem?</summary>

The patch is probably targeting the transformed name instead of the base resource name. Kustomize matches many patches against the resource identity from the base, then applies name transformations to the rendered output. The patch should target `metadata.name: api`, and the final rendered Deployment can still become `prod-api`. Previewing the overlay will confirm whether the replica, image, or resource field changed as intended.

</details>

<details>
<summary>Question 6: Your Service exists and your Deployment rollout is healthy, but traffic to the Service returns no endpoints after a label transformation. What do you inspect?</summary>

Inspect both the Service selector and the Pod template labels in the rendered output. A label transformer may have changed one side of the relationship or added a selector label that does not exist on the Pods. The Service routes only to Pods whose labels match its selector, so a healthy Deployment can still be unreachable through the Service. Fix the label transformer settings or the base labels, then render again before applying.

</details>

<details>
<summary>Question 7: A JSON patch adds resource limits at `/spec/template/spec/containers/0/resources`. It works today, but the team plans to add a sidecar. What risk should you raise in review?</summary>

The patch depends on container list order, so it may target the wrong container if a sidecar is inserted before the application container. That is acceptable in a tightly controlled one-container exercise, but it is fragile in a shared production workload. A safer approach is to use a patch that matches the container by name when the workload has multiple containers or may grow sidecars. The review should ask whether the list order is guaranteed by policy before accepting the patch.

</details>

## Hands-On Exercise

Exercise scenario: create a complete Kustomize setup with a base and two overlays. You will render both overlays, apply the development overlay, verify the live objects, then clean up. The goal is not only to make the commands work. The goal is to read the rendered YAML and explain how the base, transformations, generators, and patches combine into the final resources.

### Part 1: Create Base

```bash
mkdir -p /tmp/kustomize-demo/base
cd /tmp/kustomize-demo

# Create deployment
cat << 'EOF' > base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF

# Create service
cat << 'EOF' > base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  selector:
    app: web
  ports:
  - port: 80
EOF

# Create base kustomization
cat << 'EOF' > base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
- service.yaml
EOF
```

The base is intentionally small. It contains one Deployment, one Service, and a resource list that includes both files. Before adding overlays, render the base with `kubectl kustomize base/` and check that the Deployment selector matches the Pod template labels, and that the Service selector still uses `app: web`. If the base is wrong, every overlay that imports it will inherit the mistake.

### Part 2: Create Dev Overlay

```bash
mkdir -p overlays/dev

cat << 'EOF' > overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: dev-
namespace: development

images:
- name: nginx
  newTag: "1.21"

configMapGenerator:
- name: app-config
  literals:
  - ENV=development
  - DEBUG=true
EOF
```

The development overlay changes identity, placement, image tag, and configuration without copying the Deployment. Render it and inspect the generated ConfigMap name. You should see a suffix on the generated object and a development namespace on the namespaced resources. If you do not see the image tag change, inspect the base image name and the `images.name` match.

### Part 3: Create Prod Overlay

```bash
mkdir -p overlays/prod

cat << 'EOF' > overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: prod-
namespace: production

patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web-app
    spec:
      replicas: 3

images:
- name: nginx
  newTag: "1.22"

configMapGenerator:
- name: app-config
  literals:
  - ENV=production
  - DEBUG=false
EOF
```

The production overlay adds a patch because replica count is a specific field on one Deployment. Notice that the patch names `web-app`, not `prod-web-app`. The prefix is a rendered transformation, while the patch target identifies the base object. Render production and confirm that the final name has the prefix and the final replica count is three.

### Part 4: Preview and Apply

```bash
# Preview dev
kubectl kustomize overlays/dev/

# Preview prod
kubectl kustomize overlays/prod/

# Apply dev (create namespace first)
kubectl create ns development
kubectl apply -k overlays/dev/

# Verify
kubectl get all -n development

# Cleanup
kubectl delete -k overlays/dev/
kubectl delete ns development
```

Apply only after both previews are understandable. The development apply creates names prefixed with `dev-` in the `development` namespace. Cleanup uses the same overlay, which matters because delete needs to render the same object identities. If you change the overlay after apply and before delete, preview the delete target first so you do not leave old generated objects or prefixed resources behind.

### Success Criteria

- [ ] The base renders a Deployment and Service with matching labels and selectors.
- [ ] The development overlay renders `dev-` prefixed names, the `development` namespace, image tag `1.21`, and a generated ConfigMap.
- [ ] The production overlay renders `prod-` prefixed names, the `production` namespace, image tag `1.22`, and the patched replica count.
- [ ] `kubectl apply -k overlays/dev/` succeeds after the namespace is created.
- [ ] `kubectl get all -n development` shows the expected Deployment, ReplicaSet, Pod, and Service resources.
- [ ] Cleanup removes the development resources and namespace without relying on manual object names.

<details>
<summary>Solution notes</summary>

If the render fails before apply, fix the local Kustomize input first. Path errors usually point to `resources:` entries, while patch errors usually point to a target mismatch. If apply fails after a clean render, check cluster state, especially whether the namespace exists. For the production overlay, the final Deployment name should include the prefix, but the patch target should remain the base name. For generated ConfigMaps, expect a suffix and do not try to guess it in source YAML.

</details>

### Practice Drills

These drills preserve the same mechanics in smaller timed slices. Use them when you want repetition without rebuilding the full base and overlay tree. The cleanup commands remove local scratch directories or cluster resources created by the drill, but still preview before apply when a drill touches the cluster.

### Drill 1: Basic Kustomization (Target: 3 minutes)

```bash
mkdir -p /tmp/drill1 && cd /tmp/drill1

# Create deployment
cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Create kustomization
cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
namespace: default
labels:
- pairs:
    environment: test
  includeSelectors: true
  includeTemplates: true
EOF

# Preview
kubectl kustomize ./

# Apply
kubectl apply -k ./

# Verify
kubectl get deployments,pods -l environment=test

# Cleanup
kubectl delete -k ./
```

### Drill 2: Image Override (Target: 2 minutes)

```bash
mkdir -p /tmp/drill2 && cd /tmp/drill2

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: nginx:1.19
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
images:
- name: nginx
  newTag: "1.22"
EOF

# Verify image changed
kubectl kustomize ./ | grep image

# Cleanup
cd /tmp && rm -rf drill2
```

### Drill 3: ConfigMap Generator (Target: 3 minutes)

```bash
mkdir -p /tmp/drill3 && cd /tmp/drill3

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: nginx
        envFrom:
        - configMapRef:
            name: app-config
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
configMapGenerator:
- name: app-config
  literals:
  - DATABASE_URL=postgres://localhost
  - LOG_LEVEL=debug
EOF

# Preview - notice hash suffix
kubectl kustomize ./

# Cleanup
cd /tmp && rm -rf drill3
```

### Drill 4: Patches (Target: 4 minutes)

```bash
mkdir -p /tmp/drill4 && cd /tmp/drill4

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web
    spec:
      replicas: 3
      template:
        spec:
          containers:
          - name: nginx
            resources:
              limits:
                memory: 128Mi
                cpu: 100m
EOF

# Verify patch applied
kubectl kustomize ./

# Cleanup
cd /tmp && rm -rf drill4
```

### Drill 5: Name Prefix and Namespace (Target: 2 minutes)

```bash
mkdir -p /tmp/drill5 && cd /tmp/drill5

cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

cat << 'EOF' > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
namePrefix: staging-
namespace: staging
labels:
- pairs:
    env: staging
  includeSelectors: true
  includeTemplates: true
EOF

# Verify transformations
kubectl kustomize ./

# Cleanup
cd /tmp && rm -rf drill5
```

### Drill 6: Complete Overlay Scenario (Target: 6 minutes)

```bash
mkdir -p /tmp/drill6/{base,overlays/dev,overlays/prod}
cd /tmp/drill6

# Base
cat << 'EOF' > base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: my-api:latest
        ports:
        - containerPort: 8080
EOF

cat << 'EOF' > base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml
EOF

# Dev overlay
cat << 'EOF' > overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: dev-
namespace: dev
images:
- name: my-api
  newTag: dev-latest
EOF

# Prod overlay
cat << 'EOF' > overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: prod-
namespace: prod
images:
- name: my-api
  newTag: v1.0.0
patches:
- patch: |-
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: api
    spec:
      replicas: 3
EOF

# Compare outputs
echo "=== DEV ===" && kubectl kustomize overlays/dev/
echo "=== PROD ===" && kubectl kustomize overlays/prod/

# Cleanup
cd /tmp && rm -rf drill6
```

## Learner check

> The same kustomization can declare multiple Secret generators in one list — literals for credentials and files for TLS material:

When you render that kustomization with `kubectl kustomize`, how many Secret objects should appear, and what would happen if you used two separate top-level `secretGenerator:` keys instead?

## Sources

- [Kubernetes documentation: Managing Kubernetes objects using Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
- [kubectl apply reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/)
- [kubectl kustomize reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_kustomize/)
- [Kustomize kustomization reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/)
- [Kustomize resources reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/resource/)
- [Kustomize patches reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/patches/)
- [Kustomize images reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/images/)
- [Kustomize ConfigMap generator reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/configmapgenerator/)
- [Kustomize Secret generator reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/secretgenerator/)
- [Kustomize labels reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/labels/)
- [Kustomize namePrefix reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/nameprefix/)
- [Kustomize namespace reference](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/namespace/)

## Next Module

[Module 2.4: Deployment Strategies](../module-2.4-deployment-strategies/) - Blue/green, canary, and rolling deployment patterns.
