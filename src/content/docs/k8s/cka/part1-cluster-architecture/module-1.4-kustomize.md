---
qa_pending: true
title: "Module 1.4: Kustomize - Template-Free Configuration"
slug: k8s/cka/part1-cluster-architecture/module-1.4-kustomize
sidebar:
  order: 5
lab:
  id: cka-1.4-kustomize
  url: https://killercoda.com/kubedojo/scenario/cka-1.4-kustomize
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---

> **Complexity**: `[MEDIUM]` - Essential CKA skill for Kubernetes 1.35+
>
> **Time to Complete**: 40-55 minutes
>
> **Prerequisites**: Module 0.1 (working cluster), basic YAML knowledge, comfortable reading Deployments and Services

---

## What You'll Be Able to Do

After this module, you will be able to:

- **Design** a base-and-overlay directory structure that keeps shared Kubernetes manifests reusable while allowing environment-specific changes.
- **Apply** Kustomize transformations for namespaces, names, labels, images, ConfigMaps, Secrets, and patches without editing the base resources.
- **Debug** rendered Kustomize output before applying it to a cluster, using `kubectl kustomize`, `kubectl diff -k`, and dry-run validation.
- **Evaluate** when Kustomize is the right tool compared with Helm, plain `kubectl apply`, or a GitOps controller.
- **Repair** common overlay failures such as bad relative paths, patch target mismatches, selector label damage, and generator hash surprises.

---

## Why This Module Matters

A platform team inherits a Kubernetes repository with three nearly identical folders named `dev`, `staging`, and `prod`. Each folder contains a Deployment, Service, ConfigMap, and Ingress for the same application. During an incident, the team patches a missing readiness probe in production, then forgets to apply the same fix to staging. Two weeks later, staging passes a release candidate that production would have rejected. The outage was not caused by Kubernetes being unpredictable; it was caused by configuration drift that the repository design made easy.

Kustomize solves that exact class of problem by separating what stays the same from what changes by environment. The shared application shape lives in a base. Each environment has an overlay that references the base and describes only the differences: namespace, image tag, replica count, labels, resource limits, or generated configuration. The learner still works with normal Kubernetes YAML, but the final manifest is assembled by a deterministic renderer before `kubectl` sends anything to the API server.

For the CKA, Kustomize matters because it is built into `kubectl` and appears in practical tasks where speed and correctness both matter. You may be asked to apply a provided overlay, fix a broken `kustomization.yaml`, preview rendered output, or patch a Deployment without modifying the base. Outside the exam, the same skills show up in GitOps repositories, promotion workflows, and multi-environment application delivery.

> **The Transparent Film Analogy**
>
> Think of Kustomize like transparent film overlays on a projector. The base slide contains the stable application: Deployment, Service, labels, probes, and container ports. The production film adds five replicas and stronger resource limits. The development film adds a different namespace and a cheaper image tag. Each film changes what the audience sees, but the original slide remains intact and reusable.

---

## Part 1: The Mental Model

Kustomize is not a package manager and it is not a template engine. It is a manifest renderer that reads Kubernetes resources, applies transformations, applies patches, runs generators, and prints the final YAML. That distinction matters because Kustomize does not install release history, manage chart dependencies, or remember a previous deployment. It produces manifests; `kubectl apply -k` then applies those manifests.

The first habit to build is previewing the rendered output before you apply it. The command `kubectl kustomize <directory>` prints the YAML that Kustomize would generate. The command `kubectl apply -k <directory>` renders and applies that same output. In the exam and in real clusters, previewing first catches broken paths, incorrect names, unwanted selector changes, and surprising generated names before they become API objects.

```text
┌────────────────────────────────────────────────────────────────┐
│                     Kustomize Rendering Flow                    │
│                                                                │
│   base/                              overlays/prod/             │
│   ┌──────────────────────┐          ┌────────────────────────┐  │
│   │ deployment.yaml       │          │ kustomization.yaml      │  │
│   │ service.yaml          │          │ patch-replicas.yaml     │  │
│   │ kustomization.yaml    │          │ patch-resources.yaml    │  │
│   └──────────┬───────────┘          └───────────┬────────────┘  │
│              │                                  │               │
│              └──────────────┬───────────────────┘               │
│                             ▼                                   │
│                    ┌─────────────────┐                          │
│                    │ Kustomize build │                          │
│                    │ render only     │                          │
│                    └────────┬────────┘                          │
│                             ▼                                   │
│                  final Kubernetes YAML                          │
│                             │                                   │
│                 kubectl apply sends this                        │
│                             ▼                                   │
│                    Kubernetes API server                        │
└────────────────────────────────────────────────────────────────┘
```

The base should be boring. It should define the objects that every environment needs, with safe defaults and names that make sense before environment-specific prefixes are added. The overlay should be small and opinionated. It says, "for this environment, use this namespace, this image tag, these resource limits, and these generated configuration values."

| Term | What it means | Practical test |
|------|---------------|----------------|
| **Base** | A directory containing reusable Kubernetes resources and a `kustomization.yaml` that lists them. | Could another environment reuse this without copying files? |
| **Overlay** | A directory with its own `kustomization.yaml` that references a base and adds environment-specific changes. | Does this contain only what differs for one environment? |
| **Patch** | A partial YAML document or JSON patch that modifies a matching resource in the rendered set. | Does the target match the resource kind and original name? |
| **Transformer** | A Kustomize feature that changes many resources, such as names, namespaces, labels, annotations, or images. | Would it apply consistently across all included resources? |
| **Generator** | A feature that creates ConfigMaps or Secrets from literals, files, or environment files. | Does the generated object name change when content changes? |
| **Rendered output** | The final YAML produced by Kustomize before it is applied to Kubernetes. | Did you inspect this before changing the cluster? |

> **Active learning prompt:** Before reading the next section, predict what should live in a base and what should live in an overlay for a web application. If your answer puts `replicas: 10` in the base, ask whether every environment really wants that same production capacity.

---

## Part 2: Build a Clean Base

A base directory starts with normal Kubernetes manifests. There is no special syntax inside the Deployment or Service just because Kustomize will render them. This is one reason Kustomize works well for teams that already know Kubernetes YAML: the base remains readable by standard Kubernetes tooling, code review, and documentation.

The base also needs a `kustomization.yaml` file. This file is the local build recipe. It tells Kustomize which resources belong in this unit and which transformations or generators should run. If a directory has YAML files but no `kustomization.yaml`, `kubectl apply -k` does not know how to treat it as a Kustomize package.

A common convention is to use `k` as a shell alias for `kubectl` after explaining it once. The CKA environment may not provide aliases by default, so use the full `kubectl` command until you intentionally create the alias. If you do create it during practice, remember that the exam grader only sees cluster state, not your shell preferences.

```bash
alias k=kubectl
```

The following base defines a small web application. It deliberately keeps the namespace out of the base because namespaces usually differ by environment. It also uses stable labels for selectors and pod matching. Later sections will explain why changing selector labels casually is one of the easiest ways to break an otherwise valid overlay.

```bash
mkdir -p webapp/base
```

```yaml
# webapp/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  labels:
    app.kubernetes.io/name: webapp
    app.kubernetes.io/component: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: webapp
      app.kubernetes.io/component: frontend
  template:
    metadata:
      labels:
        app.kubernetes.io/name: webapp
        app.kubernetes.io/component: frontend
    spec:
      containers:
        - name: webapp
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
```

```yaml
# webapp/base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp
  labels:
    app.kubernetes.io/name: webapp
spec:
  selector:
    app.kubernetes.io/name: webapp
    app.kubernetes.io/component: frontend
  ports:
    - name: http
      port: 80
      targetPort: 80
```

```yaml
# webapp/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
```

Preview the base before creating overlays. This step teaches you to treat Kustomize as a renderer first and an apply mechanism second. If the rendered base is invalid, every overlay that references it inherits the problem.

```bash
kubectl kustomize webapp/base/
```

You should see a Deployment and a Service. Nothing has been applied to the cluster yet. The command is safe because it only prints YAML. If you want Kubernetes client-side validation without changing the cluster, pipe the rendered output to a dry-run apply.

```bash
kubectl kustomize webapp/base/ | kubectl apply --dry-run=client -f -
```

The base is intentionally minimal, but it is not a stub. It contains the API resources that define the workload shape. The overlay will decide the environment, image version, replica count, and operational policy. That separation is what prevents environment drift from becoming a maintenance habit.

---

## Part 3: Add Overlays Without Copying the Base

An overlay references the base by relative path. If the overlay is in `webapp/overlays/dev/`, then `../../base` means "go up from `dev` to `overlays`, go up from `overlays` to `webapp`, then enter `base`." Most beginner Kustomize failures are not YAML syntax failures; they are path failures caused by counting directory levels incorrectly.

The development overlay below adds a namespace, a name prefix, and an environment label. The prefix prevents name collisions when multiple rendered variants share a cluster. The namespace keeps objects in the correct administrative boundary. The label makes it easy to query, filter, and operate on all resources for the development environment.

```bash
mkdir -p webapp/overlays/dev webapp/overlays/prod
```

```yaml
# webapp/overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: dev-
namespace: development

labels:
  - pairs:
      environment: dev
      app.kubernetes.io/managed-by: kustomize
    includeSelectors: false
```

The `labels` transformer is safer here than a blind selector-changing label strategy. Environment labels are useful on object metadata and pod templates, but adding them to selectors can make Services and Deployments select a narrower set of pods than you intended. For a new workload, selector changes may work. For an existing workload, selector mutations can fail because Deployment selectors are immutable.

> **Active learning prompt:** Predict the rendered names before running the command. Will the Service be named `webapp`, `dev-webapp`, or `webapp-dev`? Then run the preview and verify whether your mental model matched the output.

```bash
kubectl kustomize webapp/overlays/dev/
```

A production overlay usually needs stronger differences. It may change replicas, image tags, resource limits, generated configuration, or annotations used by policy and observability tools. The key is that the overlay still avoids copying the entire Deployment. It expresses only the production-specific decisions.

```yaml
# webapp/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
namespace: production

labels:
  - pairs:
      environment: production
      app.kubernetes.io/managed-by: kustomize
    includeSelectors: false

images:
  - name: nginx
    newTag: "1.25-alpine"

patches:
  - path: patch-replicas.yaml
  - path: patch-resources.yaml
```

```yaml
# webapp/overlays/prod/patch-replicas.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 5
```

```yaml
# webapp/overlays/prod/patch-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  template:
    spec:
      containers:
        - name: webapp
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

Notice the patch target name: `webapp`, not `prod-webapp`. Kustomize matches patches against the original resource identity before the name prefix is applied. This surprises learners because the final object name includes the prefix, but the patch file still describes the base resource it wants to modify.

Preview production and inspect the output carefully. The final Deployment name should include the prefix, the namespace should be production, the image tag should be changed, and the replica count should be five. If any of those are missing, fix the render before applying to a cluster.

```bash
kubectl kustomize webapp/overlays/prod/
```

---

## Part 4: Transformers as Controlled Bulk Edits

Transformers are powerful because they apply a consistent change across many resources. They are also risky because a broad transformation can affect more fields than a beginner expects. The right way to use them is to understand which fields they touch, preview output, and keep environment overlays narrow enough that review stays meaningful.

The name transformers are straightforward. `namePrefix` prepends text to resource names, while `nameSuffix` appends text. Kustomize also updates internal references when it understands the relationship, such as a Deployment referring to a generated ConfigMap. This is one reason Kustomize is better than simple search-and-replace.

```yaml
# Example name transformation
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
nameSuffix: -blue
```

```text
┌──────────────────────────┐
│ Base name                │
│ webapp                   │
└─────────────┬────────────┘
              │ namePrefix: prod-
              │ nameSuffix: -blue
              ▼
┌──────────────────────────┐
│ Rendered name            │
│ prod-webapp-blue         │
└──────────────────────────┘
```

The namespace transformer sets `metadata.namespace` on namespaced resources. It does not make cluster-scoped resources namespaced. A Namespace object, ClusterRole, ClusterRoleBinding, CustomResourceDefinition, and StorageClass are cluster-scoped, so the namespace transformer cannot turn them into namespaced objects. This is important when an overlay includes both application resources and cluster-level resources.

```yaml
# Example namespace transformation
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namespace: production
```

The image transformer is the preferred way to change image tags when the image name already exists in the base. It avoids writing a patch against the nested container list, and it is easier to scan during review. It can change the tag, the registry, or both.

```yaml
# Example image transformation
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

images:
  - name: nginx
    newName: registry.example.com/platform/nginx
    newTag: "1.25-alpine"
```

Labels deserve special care. Older examples often use `commonLabels`, which can add labels to selectors as well as object metadata. That can be acceptable when creating a brand-new workload, but it is dangerous when updating a live Deployment because selector fields are immutable. Prefer the newer `labels` transformer when you need control over whether selector fields are included.

```yaml
# Safer label transformation for environment metadata
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

labels:
  - pairs:
      environment: production
      team: platform
    includeSelectors: false
```

| Transformer | What it changes | Main risk | Safer habit |
|-------------|-----------------|-----------|-------------|
| `namePrefix` | Resource names and known references. | Patches written against prefixed names do not match. | Patch the base name and preview final names. |
| `nameSuffix` | Resource names and known references. | Long names may exceed Kubernetes name length limits. | Keep suffixes short and environment-oriented. |
| `namespace` | Namespaced resource metadata. | Cluster-scoped resources remain cluster-scoped. | Preview mixed resource sets before applying. |
| `images` | Container image references matching the original image name. | A name mismatch leaves the image unchanged. | Preview and search rendered output for `image:`. |
| `labels` | Metadata, selectors, and templates depending on options. | Selector changes can break or be rejected. | Use `includeSelectors: false` for operational labels. |
| `commonAnnotations` | Object annotations. | Sensitive values may be exposed in metadata. | Keep secrets in Secret data, not annotations. |

A senior-level Kustomize review asks whether the transformer expresses intent better than a patch. If you are changing every resource in the overlay, a transformer is clearer. If you are changing one field on one object, a patch is often clearer. If you are changing behavior that Kubernetes treats as immutable, you need to plan a migration instead of assuming the renderer can force it through.

---

## Part 5: Patches and Why Names Matter

Patches are how overlays make targeted changes to resources from the base. The two practical patch styles you will see most often are strategic merge patches and JSON 6902 patches. Strategic merge patches look like partial Kubernetes objects. JSON patches look like a list of operations against JSON paths. Both are useful, but they solve different problems.

Strategic merge is usually easier for Kubernetes-native objects such as Deployments. It understands merge keys for many Kubernetes lists. For example, containers merge by `name`, so a patch that mentions the `webapp` container modifies that container instead of replacing the entire container list. This is exactly why container names must be accurate.

```yaml
# webapp/overlays/prod/patch-probes.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  template:
    spec:
      containers:
        - name: webapp
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
```

If the base container is named `webapp` and the patch uses `app`, the strategic merge patch can add a second container instead of modifying the existing one. That rendered YAML may even be valid Kubernetes YAML while still being operationally wrong. This is why previewing the full output and reading the container list matters.

> **What would happen if:** Your production patch references a container named `app`, but the base Deployment's container is named `webapp`. Before running the command, decide whether you expect a validation error, a new container, or a modified existing container. Then render the overlay and inspect `spec.template.spec.containers`.

JSON 6902 patches are better when you need exact operations, especially against scalar fields or lists where strategic merge behavior is not what you want. They are also useful when you want the patch to fail if a path is missing, because a `replace` operation expects the target path to exist.

```yaml
# webapp/overlays/prod/kustomization.yaml fragment
patches:
  - target:
      kind: Deployment
      name: webapp
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: add
        path: /metadata/annotations/reviewed-by
        value: platform-team
```

Patch targeting can also use kind, name, namespace, group, version, and label selectors. For exam work, target by kind and name unless the task clearly asks for label selection. For repository work, target enough identity to make accidental matches unlikely.

```yaml
# Target one Deployment by kind and base name
patches:
  - path: patch-resources.yaml
    target:
      kind: Deployment
      name: webapp
```

```yaml
# Target all frontend Deployments by label
patches:
  - path: patch-frontend-memory.yaml
    target:
      kind: Deployment
      labelSelector: "app.kubernetes.io/component=frontend"
```

| Patch style | Best use | Example decision | Failure mode to check |
|-------------|----------|------------------|-----------------------|
| Strategic merge | Kubernetes-native objects where partial YAML is readable. | Add resources, probes, replicas, or pod security context. | Wrong list merge key creates a new list item. |
| JSON 6902 | Precise operations against exact paths. | Replace `/spec/replicas` or add a single annotation. | Wrong path fails or modifies an unintended path. |
| Targeted patch | One resource needs a known change. | Patch only `Deployment/webapp`. | Target name uses rendered name instead of base name. |
| Label-selected patch | A class of resources needs the same change. | Patch all frontend Deployments. | Selector matches more resources than intended. |

The senior habit is to make patch intent obvious during review. A patch file named `patch.yaml` forces reviewers to open it before they know what risk it carries. A patch named `patch-resources.yaml` or `patch-readiness-probe.yaml` tells the reviewer what behavior should change and makes accidental scope creep easier to spot.

---

## Part 6: ConfigMap and Secret Generators

Generators create ConfigMaps and Secrets from files, literals, or environment files. They are useful because configuration content often belongs near the overlay that owns it. A development overlay may set a verbose log level. A production overlay may set a stricter timeout. The generator keeps that environment-owned configuration close to the environment-owned kustomization.

The most important generator behavior is the hash suffix. By default, Kustomize appends a content hash to generated ConfigMap and Secret names. When the content changes, the generated name changes. If a Deployment references that generated object through Kustomize-managed name references, the Pod template changes too, which triggers a rollout.

```bash
mkdir -p webapp/overlays/prod/config
```

```bash
cat > webapp/overlays/prod/config/app.properties << 'EOF'
LOG_LEVEL=info
FEATURE_FLAGS=checkout-v2
REQUEST_TIMEOUT_SECONDS=10
EOF
```

```yaml
# webapp/overlays/prod/kustomization.yaml fragment
configMapGenerator:
  - name: webapp-config
    files:
      - config/app.properties
```

A Deployment can consume that generated ConfigMap by the logical name from the generator. Kustomize rewrites the reference to the hashed rendered name. This is the useful part: you write the stable logical name, and Kustomize keeps the applied name content-addressed.

```yaml
# Example base Deployment fragment
envFrom:
  - configMapRef:
      name: webapp-config
```

```text
┌──────────────────────────┐
│ Generator logical name   │
│ webapp-config            │
└─────────────┬────────────┘
              │ content changes
              ▼
┌──────────────────────────┐
│ Rendered ConfigMap name  │
│ webapp-config-abc123     │
└─────────────┬────────────┘
              │ Deployment reference rewritten
              ▼
┌──────────────────────────┐
│ Pod template changes     │
│ rollout is triggered     │
└──────────────────────────┘
```

Secrets can be generated the same way, but generating a Secret does not make secret handling secure by itself. If you commit plaintext password files to Git, Kustomize will faithfully create Secrets from leaked material. For real environments, use sealed secrets, external secret operators, SOPS, or another secret management workflow. For the CKA, you only need to understand the Kustomize mechanics.

```yaml
# webapp/overlays/prod/kustomization.yaml fragment
secretGenerator:
  - name: webapp-db
    literals:
      - username=webapp
      - password=change-me-in-real-life
    type: Opaque
```

Sometimes teams disable hash suffixes because an old application expects a fixed ConfigMap name. That is a trade-off, not a harmless preference. A stable generated name is easier for legacy references, but it removes the automatic rollout trigger caused by name changes.

```yaml
# Disabling the generator hash suffix
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

configMapGenerator:
  - name: webapp-config
    literals:
      - LOG_LEVEL=info

generatorOptions:
  disableNameSuffixHash: true
```

The field name is `disableNameSuffixHash`, not `disableNameSuffix`. This detail matters in troubleshooting because examples from memory or outdated notes can lead to a kustomization that does not behave as expected. When in doubt, render output and inspect the generated names instead of assuming the option worked.

---

## Part 7: Debugging Kustomize Like an Operator

Debugging Kustomize starts before you talk to the API server. If rendering fails, Kubernetes never sees the resources. If rendering succeeds but the output is wrong, Kubernetes may accept an object that behaves differently than you intended. The safest workflow is render, inspect, validate, diff, then apply.

```bash
kubectl kustomize webapp/overlays/prod/
```

Use `grep` or `yq` if available to inspect a specific field quickly, but do not depend on them in the exam unless you know they exist. Plain `kubectl kustomize` output is enough for most tasks. Search the rendered YAML for `name:`, `namespace:`, `image:`, `replicas:`, and any field the task specifically asked you to change.

```bash
kubectl kustomize webapp/overlays/prod/ | grep -E "name:|namespace:|image:|replicas:"
```

Dry-run validation catches API-level mistakes without creating resources. It is not a full server-side admission test when using client dry-run, but it catches many structural errors. Server dry-run can be stronger when the API server is reachable and supports the resource types involved.

```bash
kubectl kustomize webapp/overlays/prod/ | kubectl apply --dry-run=client -f -
```

```bash
kubectl apply --dry-run=server -k webapp/overlays/prod/
```

Diff shows what would change compared with the current cluster. This is useful when a rendered overlay is valid but may update existing objects in surprising ways. In a GitOps workflow, the controller may perform the apply, but the human still benefits from rendering and diffing locally during review.

```bash
kubectl diff -k webapp/overlays/prod/
```

Apply only after the render matches the task. In the CKA, create namespaces first if the overlay expects them and the task does not provide them. Kustomize setting `namespace: production` does not automatically create the Namespace object unless you include a Namespace resource.

```bash
kubectl create namespace production
kubectl apply -k webapp/overlays/prod/
kubectl get deploy,svc -n production
```

A good troubleshooting sequence is intentionally repetitive. First, prove the path exists. Second, prove the base renders. Third, prove the overlay renders. Fourth, prove the rendered output contains the intended change. Fifth, apply or diff. This sequence prevents you from debugging the cluster when the problem is really a relative path in a local directory.

```text
┌──────────────────────────────┐
│ Kustomize troubleshooting    │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Does the overlay path exist? │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Does the base render alone?  │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Does the overlay render?     │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ Is the intended field right? │
└───────────────┬──────────────┘
                ▼
┌──────────────────────────────┐
│ dry-run, diff, then apply    │
└──────────────────────────────┘
```

When an overlay fails with a resource accumulation error, read the path in the error message literally. It usually tells you which file or directory Kustomize tried to load. When a patch appears to do nothing, check the target kind, target name, API version, and container names. When a generated ConfigMap does not roll pods, inspect whether the Deployment reference was rewritten and whether hash suffixing was disabled.

---

## Part 8: Kustomize vs Helm vs Plain Manifests

Kustomize, Helm, and plain manifests can all deploy Kubernetes objects, but they optimize for different situations. Plain manifests are easiest when there is only one environment and little variation. Kustomize is strongest when you own the manifests and need environment overlays without templates. Helm is strongest when you want packaging, values files, dependencies, and release history.

The wrong decision often shows up as friction during change. If every environment folder contains copied YAML, plain manifests have exceeded their useful size. If a Kustomize repository starts simulating conditionals, loops, and reusable functions, the team may be trying to use Kustomize as a template language. If a Helm chart has only one Deployment and three values, Helm may be more machinery than the task needs.

| Aspect | Plain manifests | Kustomize | Helm |
|--------|-----------------|-----------|------|
| Primary model | Apply YAML files directly. | Render bases plus overlays. | Render charts with templates and values. |
| Best fit | Single environment or simple demos. | Owned manifests with controlled environment differences. | Packaged applications, dependencies, release lifecycle. |
| Template language | None. | None. | Go templates. |
| Built into `kubectl` | Yes, through normal apply. | Yes, through `kubectl apply -k` and `kubectl kustomize`. | No, separate Helm CLI. |
| Release history | No. | No. | Yes, Helm releases track revisions. |
| Drift control | Manual unless paired with GitOps. | Strong repository structure, stronger with GitOps. | Stronger release model, stronger with GitOps. |
| Exam speed | Fast for simple resources. | Fast for overlays and patch tasks. | Useful when chart tasks are explicit. |

For the CKA, choose the tool the task asks for. If the task says apply a Kustomize configuration, use `kubectl apply -k`. If it asks you to preview a Kustomize directory, use `kubectl kustomize`. If it asks for a Helm release, use Helm. Do not convert a Kustomize task into a Helm task because you prefer Helm; the grader expects a specific cluster outcome and sometimes a specific workflow.

In real teams, Kustomize often pairs with GitOps controllers such as Argo CD or Flux. The repository contains bases and overlays. The controller watches an overlay path and applies the rendered output. Rollback then comes from Git history or controller sync behavior, not from Kustomize itself. That division is healthy: Kustomize renders configuration, while GitOps manages continuous reconciliation.

---

## Part 9: Worked Example - Fix a Broken Production Overlay

A team reports that `kubectl apply -k webapp/overlays/prod/` fails after a directory cleanup. The base still exists, but the overlay cannot find it. Instead of editing randomly, debug the render path first.

Broken overlay:

```yaml
# webapp/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../base

namePrefix: prod-
namespace: production
```

The overlay lives at `webapp/overlays/prod/`. From there, `../base` means `webapp/overlays/base`, which does not exist. The correct path is `../../base`, because the overlay must go up to `overlays`, then up to `webapp`, then down into `base`.

Corrected overlay:

```yaml
# webapp/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
namespace: production
```

Now render before applying:

```bash
kubectl kustomize webapp/overlays/prod/
```

Suppose the render succeeds, but the production task also requires five replicas and the rendered Deployment still has one. Add a patch with the base resource name, not the prefixed final name.

```yaml
# webapp/overlays/prod/patch-replicas.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 5
```

```yaml
# webapp/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
namespace: production

patches:
  - path: patch-replicas.yaml
```

Finally, render and check the exact field:

```bash
kubectl kustomize webapp/overlays/prod/ | grep -A 8 "kind: Deployment"
```

This example is small, but it models the senior workflow. You corrected the path, verified the render, added the smallest patch that expressed the production difference, and verified the rendered field before applying. The important skill is not memorizing this exact file layout; it is following a repeatable reasoning path when Kustomize output surprises you.

---

## Did You Know?

- **Kustomize has been built into `kubectl` since Kubernetes v1.14**: That makes it practical in exam environments because you can use `kubectl kustomize` and `kubectl apply -k` without installing a separate binary.
- **GitOps tools commonly understand Kustomize paths directly**: Argo CD and Flux can watch an overlay directory, render it, and continuously reconcile the resulting resources to a cluster.
- **Generated ConfigMap and Secret names are content-sensitive by default**: The hash suffix changes when generator input changes, which helps trigger Deployment rollouts when Pod template references are rewritten.
- **Kustomize can be combined with Helm in advanced workflows**: Teams sometimes render or inflate Helm chart output and then apply Kustomize overlays, but this adds complexity and should be justified by a real need.

---

## Common Mistakes

| Mistake | Why it hurts | How to fix it |
|---------|--------------|---------------|
| Referencing the base with the wrong relative path | Kustomize fails before Kubernetes sees any resource, often with an accumulation or "must resolve to a file" error. | Count from the overlay directory and verify with `kubectl kustomize <overlay>`. |
| Forgetting a `kustomization.yaml` file in the base or overlay | A directory full of YAML is not automatically a Kustomize unit. | Add `apiVersion`, `kind: Kustomization`, and a `resources` list to each Kustomize directory. |
| Writing patches against rendered prefixed names | Patches do not match because Kustomize targets the original base resource name. | Use `metadata.name` from the base, then verify the final prefixed name in rendered output. |
| Using broad label transformations that mutate selectors | Deployment selectors are immutable after creation, and Services may stop selecting the intended pods. | Prefer the `labels` transformer with `includeSelectors: false` for environment metadata. |
| Disabling generator hash suffixes without understanding the rollout impact | Pods may keep running with old configuration because the referenced object name does not change. | Keep hash suffixes enabled unless a legacy integration requires stable names, then plan restarts separately. |
| Applying before rendering | Valid YAML can still be the wrong YAML, and apply makes mistakes live. | Run `kubectl kustomize`, then dry-run or diff before `kubectl apply -k`. |
| Treating Kustomize like Helm | Kustomize has no release history, rollback command, chart dependencies, or templating language. | Use Git history or GitOps for rollback, and choose Helm when package management is the requirement. |
| Copying base manifests into every overlay | Shared changes drift across environments, recreating the problem Kustomize is meant to solve. | Keep the base as the source of shared resources and put only differences in overlays. |

---

## Quiz

1. **Your team deploys the same API to development, staging, and production. A developer copied the Deployment into all three environment folders and changed the replica count in each copy. A security context fix was later applied only to production. How would you redesign the repository with Kustomize, and why does that reduce risk?**

   <details>
   <summary>Answer</summary>

   Create a shared `base/` directory containing the Deployment, Service, and any common configuration. Then create `overlays/dev/`, `overlays/staging/`, and `overlays/prod/`, each with its own `kustomization.yaml` referencing `../../base`. Put environment-specific changes such as namespace, name prefix, image tag, replica count, and resource limits in overlays. This reduces risk because the security context fix is made once in the base and inherited by every environment. The overlays still express real differences, but they no longer duplicate the whole workload definition.

   </details>

2. **During a CKA task, `kubectl apply -k webapp/overlays/staging/` fails with a message that Kustomize cannot accumulate resources from `../base`. The base directory is `webapp/base`, and the overlay is `webapp/overlays/staging`. What should you check and change before trying to apply again?**

   <details>
   <summary>Answer</summary>

   Check the relative path from the overlay directory, not from your current shell directory. From `webapp/overlays/staging`, the path `../base` points to `webapp/overlays/base`, which is wrong. The correct path is usually `../../base`. Change the overlay's `resources` entry to `../../base`, then run `kubectl kustomize webapp/overlays/staging/` to verify rendering before applying.

   </details>

3. **A production overlay uses `namePrefix: prod-`. A patch file targets `metadata.name: prod-webapp`, but the rendered Deployment still has the old replica count. The final object is named `prod-webapp`. Why did the patch not work, and what is the correct patch target name?**

   <details>
   <summary>Answer</summary>

   Kustomize matches patches against the base resource identity before applying the name prefix. Even though the final rendered object is named `prod-webapp`, the patch should target the base resource name, usually `webapp`. Change the patch file to `metadata.name: webapp`, render with `kubectl kustomize`, and confirm that `spec.replicas` changed in the final output.

   </details>

4. **A team adds `commonLabels: { environment: prod }` to an overlay for an existing Deployment. The apply fails because the Deployment selector is immutable. What happened, and how should the team add environment labels more safely?**

   <details>
   <summary>Answer</summary>

   The label transformation likely tried to add the environment label to selector fields as well as metadata. Deployment selectors are immutable after the Deployment exists, so Kubernetes rejected the update. Use the `labels` transformer with `includeSelectors: false` when adding operational metadata that should not change selectors. Then render the output and verify that metadata and pod template labels are appropriate while immutable selectors remain unchanged.

   </details>

5. **Your application reads settings from a ConfigMap generated by Kustomize. After changing the config file and reapplying the overlay, you expect a rollout, but the Deployment does not restart. What two Kustomize-related details would you inspect first?**

   <details>
   <summary>Answer</summary>

   First, inspect whether generator hash suffixing is enabled. If `generatorOptions.disableNameSuffixHash: true` is set, the ConfigMap name stays stable and may not trigger a Pod template change. Second, inspect whether the Deployment reference is managed in a way Kustomize can rewrite to the generated name. Render the overlay and compare the generated ConfigMap name with the name referenced by the Deployment. If the reference does not change, Kubernetes has no reason to roll the Pods.

   </details>

6. **A teammate wants to use Kustomize for a third-party monitoring stack that already has a maintained Helm chart with dependencies and release notes. They also want rollback history. How would you evaluate that choice?**

   <details>
   <summary>Answer</summary>

   Kustomize is strongest when the team owns the manifests and needs environment overlays. A third-party monitoring stack with chart dependencies and expected rollback history is often a better fit for Helm. Helm provides chart packaging, values, dependencies, and release revisions. Kustomize could still be used to customize rendered output in an advanced workflow, but that adds complexity. The recommendation should be based on the operational requirement: if package management and release history are central, Helm is likely the better primary tool.

   </details>

7. **You render a production overlay and notice two containers in the Deployment: `webapp` and `app`. The base originally had only `webapp`, and your patch was meant to add resource limits. What likely caused the second container, and how do you repair it?**

   <details>
   <summary>Answer</summary>

   The strategic merge patch probably used the wrong container name. Kubernetes strategic merge uses `name` as the merge key for the container list, so a patch entry named `app` does not modify the existing `webapp` container; it can create a new container entry. Repair the patch by changing the container name to `webapp`, render the overlay again, and verify that there is one container with the expected resource requests and limits.

   </details>

---

## Hands-On Exercise

**Task**: Build, inspect, apply, and troubleshoot a Kustomize structure for a web application with development and production overlays.

This exercise follows the same progression you should use in the exam: create the base, add a simple overlay, add a production overlay, render before applying, validate with dry-run, apply only after the output is correct, and then clean up. The commands are written to run in a shell with `kubectl` available and a working Kubernetes cluster.

### Step 1: Create the directory structure

```bash
mkdir -p webapp/base
mkdir -p webapp/overlays/dev
mkdir -p webapp/overlays/prod
mkdir -p webapp/overlays/prod/config
```

### Step 2: Create the base Deployment

```bash
cat > webapp/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  labels:
    app.kubernetes.io/name: webapp
    app.kubernetes.io/component: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: webapp
      app.kubernetes.io/component: frontend
  template:
    metadata:
      labels:
        app.kubernetes.io/name: webapp
        app.kubernetes.io/component: frontend
    spec:
      containers:
        - name: webapp
          image: nginx:1.25
          ports:
            - containerPort: 80
          envFrom:
            - configMapRef:
                name: webapp-config
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
EOF
```

### Step 3: Create the base Service

```bash
cat > webapp/base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: webapp
  labels:
    app.kubernetes.io/name: webapp
spec:
  selector:
    app.kubernetes.io/name: webapp
    app.kubernetes.io/component: frontend
  ports:
    - name: http
      port: 80
      targetPort: 80
EOF
```

### Step 4: Create the base kustomization

```bash
cat > webapp/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

configMapGenerator:
  - name: webapp-config
    literals:
      - LOG_LEVEL=debug
      - FEATURE_FLAGS=local
EOF
```

### Step 5: Render the base and inspect generated names

```bash
kubectl kustomize webapp/base/
```

Look for the generated ConfigMap name and the Deployment reference to that name. They should match after Kustomize rewrites the reference. If the Deployment still references plain `webapp-config` while the generated ConfigMap has a suffix, stop and inspect the YAML before moving on.

### Step 6: Create the development overlay

```bash
cat > webapp/overlays/dev/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: dev-
namespace: development

labels:
  - pairs:
      environment: dev
      app.kubernetes.io/managed-by: kustomize
    includeSelectors: false

images:
  - name: nginx
    newTag: "1.25"
EOF
```

### Step 7: Render development and verify the transformation

```bash
kubectl kustomize webapp/overlays/dev/
```

Confirm that names begin with `dev-`, namespaced resources use `development`, the image is `nginx:1.25`, and the selector labels still match the pod template labels needed by the Service and Deployment.

### Step 8: Create production configuration input

```bash
cat > webapp/overlays/prod/config/app.properties << 'EOF'
LOG_LEVEL=info
FEATURE_FLAGS=checkout-v2
REQUEST_TIMEOUT_SECONDS=10
EOF
```

### Step 9: Create production patches

```bash
cat > webapp/overlays/prod/patch-replicas.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 5
EOF
```

```bash
cat > webapp/overlays/prod/patch-resources.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  template:
    spec:
      containers:
        - name: webapp
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
EOF
```

### Step 10: Create the production overlay

```bash
cat > webapp/overlays/prod/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
namespace: production

labels:
  - pairs:
      environment: production
      app.kubernetes.io/managed-by: kustomize
    includeSelectors: false

images:
  - name: nginx
    newTag: "1.25-alpine"

configMapGenerator:
  - name: webapp-config
    behavior: replace
    files:
      - config/app.properties

patches:
  - path: patch-replicas.yaml
  - path: patch-resources.yaml
EOF
```

### Step 11: Render production and verify specific fields

```bash
kubectl kustomize webapp/overlays/prod/
```

```bash
kubectl kustomize webapp/overlays/prod/ | grep -E "name:|namespace:|replicas:|image:|memory:|cpu:"
```

The production Deployment should be named with a `prod-` prefix, run in the `production` namespace, use five replicas, use `nginx:1.25-alpine`, and include the stronger resource requests and limits.

### Step 12: Validate without changing the cluster

```bash
kubectl apply --dry-run=client -k webapp/overlays/prod/
```

If your cluster supports the relevant server-side validation, also run:

```bash
kubectl apply --dry-run=server -k webapp/overlays/prod/
```

### Step 13: Apply development and production

```bash
kubectl create namespace development
kubectl create namespace production
kubectl apply -k webapp/overlays/dev/
kubectl apply -k webapp/overlays/prod/
```

If either namespace already exists, the create command may report that it already exists. In a practice environment, you can continue if the namespace is present and you have permission to use it.

### Step 14: Verify cluster state

```bash
kubectl get deploy,svc,configmap -n development
kubectl get deploy,svc,configmap -n production
```

```bash
kubectl get deploy prod-webapp -n production -o jsonpath='{.spec.replicas}{"\n"}'
kubectl get deploy prod-webapp -n production -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

### Step 15: Break and repair one overlay on purpose

Edit `webapp/overlays/prod/kustomization.yaml` and temporarily change `../../base` to `../base`. Then run:

```bash
kubectl kustomize webapp/overlays/prod/
```

Read the error message, repair the path, and render again. This deliberate failure builds the diagnostic habit you need under exam pressure.

### Success Criteria

- [ ] You can explain why the base contains shared resources but not environment-specific production settings.
- [ ] You can render a base and an overlay before applying either one.
- [ ] You can use `namePrefix`, `namespace`, `labels`, `images`, patches, and generators in a working overlay.
- [ ] You can explain why production patches target `metadata.name: webapp` instead of `prod-webapp`.
- [ ] You can verify that generated ConfigMap names and Deployment references match in rendered output.
- [ ] You can diagnose and repair a broken relative path in an overlay.
- [ ] You can validate with dry-run before applying resources to the cluster.
- [ ] You can clean up everything created by the exercise.

### Cleanup

```bash
kubectl delete -k webapp/overlays/dev/
kubectl delete -k webapp/overlays/prod/
kubectl delete namespace development production
rm -rf webapp/
```

---

## Practice Drills

### Drill 1: Preview Before Apply

Create a tiny Kustomize base and prove to yourself that previewing does not change the cluster. This drill trains the safest first move for any exam task involving `-k`.

```bash
mkdir -p drill-preview
cat > drill-preview/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: preview-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: preview-demo
  template:
    metadata:
      labels:
        app: preview-demo
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
EOF

cat > drill-preview/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
EOF

kubectl kustomize drill-preview/
kubectl get deploy preview-demo
kubectl apply -k drill-preview/
kubectl get deploy preview-demo
kubectl delete -k drill-preview/
rm -rf drill-preview
```

### Drill 2: Repair a Patch Name

This drill creates a patch that targets the wrong name. Your job is to render, observe that the change is missing, repair the patch target, and render again.

```bash
mkdir -p drill-patch/base drill-patch/overlay
cat > drill-patch/base/deployment.yaml << 'EOF'
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
          image: nginx:1.25
EOF

cat > drill-patch/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
EOF

cat > drill-patch/overlay/patch-replicas.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prod-api
spec:
  replicas: 3
EOF

cat > drill-patch/overlay/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../base

namePrefix: prod-

patches:
  - path: patch-replicas.yaml
EOF

kubectl kustomize drill-patch/overlay/
```

Repair `patch-replicas.yaml` so the target name is `api`, then render again and confirm that the final `prod-api` Deployment has three replicas.

```bash
rm -rf drill-patch
```

### Drill 3: Generator Hash Observation

This drill shows why generated ConfigMap names change when content changes. Render once, change a literal, and render again.

```bash
mkdir -p drill-generator
cat > drill-generator/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

configMapGenerator:
  - name: app-config
    literals:
      - LOG_LEVEL=info
EOF

kubectl kustomize drill-generator/

cat > drill-generator/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

configMapGenerator:
  - name: app-config
    literals:
      - LOG_LEVEL=debug
EOF

kubectl kustomize drill-generator/
rm -rf drill-generator
```

### Drill 4: Choose the Right Tool

Read each scenario and decide whether plain manifests, Kustomize, or Helm is the best primary tool. Then compare your answer with the explanation.

1. You have one Namespace and one debug Pod for a quick troubleshooting task.
2. You own a web application and need dev, staging, and production variants.
3. You need to install a third-party ingress controller with dependencies and release rollback.

<details>
<summary>Suggested reasoning</summary>

Plain manifests are enough for the quick debug Pod because there is no reusable environment structure. Kustomize fits the owned web application because the base can hold the shared workload while overlays hold environment differences. Helm fits the third-party ingress controller because chart packaging, dependencies, values, and release history are part of the requirement.

</details>

---

## Next Module

[Module 1.5: CRDs & Operators](../module-1.5-crds-operators/) - Extending Kubernetes with Custom Resource Definitions.
