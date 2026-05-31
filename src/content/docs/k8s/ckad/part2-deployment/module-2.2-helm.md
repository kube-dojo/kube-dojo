---
revision_pending: false
title: "Module 2.2: Helm Package Manager"
slug: k8s/ckad/part2-deployment/module-2.2-helm
sidebar:
  order: 2
lab:
  id: ckad-2.2-helm
  url: https://killercoda.com/kubedojo/scenario/ckad-2.2-helm
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Essential CKAD deployment tooling
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 2.1 (Deployments), understanding of YAML templates

---

## Learning Outcomes

After completing this module, you will be able to:

- **Deploy** Helm charts with repository configuration, namespace targeting, custom values, and Kubernetes 1.35+ verification.
- **Design** values override strategies that separate chart defaults, reusable environment files, and command-line overrides.
- **Diagnose** failed Helm releases by combining `helm status`, `helm history`, rendered manifests, Kubernetes events, and rollback operations.
- **Evaluate** when to install, upgrade, rollback, uninstall, or render a chart locally in CKAD-style deployment scenarios.
- **Compare** chart structure, release revisions, and generated Kubernetes objects to trace how a value becomes running workload state.

## Why This Module Matters

Hypothetical scenario: you are given a namespace named `web`, a chart repository, and a requirement to deploy nginx with two replicas and an internal service. If you hand-write a Deployment, Service, labels, probes, and resource settings from memory, you may finish with valid YAML but fail the task because the question asked for a Helm release. If you install the chart quickly but forget the namespace, the workload may run in `default`, the release will be invisible from the requested namespace, and every follow-up command will look misleading.

Helm solves a practical packaging problem that shows up as soon as Kubernetes manifests stop being tiny. A real application is rarely one object; it is usually a Deployment, Service, ConfigMap, Secret, ServiceAccount, role binding, ingress object, and several labels that must agree with one another. A chart packages those related resources so they can be installed, upgraded, inspected, and rolled back as a unit instead of being copied between directories by hand.

For a CKAD learner, Helm is not about becoming a chart author on day one. Your immediate job is to recognize the release lifecycle, choose the right command under time pressure, and prove that the generated Kubernetes objects match the task. That means you need to know how repositories feed charts, how values change rendered manifests, how namespaces scope releases, and how history lets you recover when an upgrade creates the wrong state.

The useful mental model is an app store, but with source-controlled settings instead of a graphical preferences window. Charts are packaged applications, repositories are catalogs, releases are installed instances, and values are the settings that adapt the same chart to different environments. The analogy stops where Kubernetes begins: Helm does not make a broken image healthy, bypass RBAC, or guarantee that a Service is reachable. It renders and submits Kubernetes resources, then the cluster still enforces every normal scheduling, validation, and readiness rule.

Helm also gives you a vocabulary for repeatability. Without a package manager, the phrase "deploy nginx" could mean applying a random local YAML file, copying a manifest from a tutorial, or editing a previous Deployment until it looks close enough. With Helm, the phrase can become precise: install this chart, with this release name, in this namespace, using this values file and these overrides. That precision is what lets another operator reproduce your work.

The tradeoff is that Helm adds an abstraction layer you must learn to peel back. When a Pod fails, you should not blame Helm automatically, but you also should not ignore Helm's role in producing the manifest. A reliable operator can move in both directions: from chart and values down to rendered YAML, and from live Kubernetes object back up to the value or template that created it.

For the CKAD exam, that bidirectional movement saves time because tasks are usually small and tightly scoped. You may not need to explain every template function, but you do need to find the value key that controls replica count, install the release into the requested namespace, and prove that the generated objects match the requirement. The goal is operational fluency, not memorizing every possible Helm flag.

## Helm's Packaging Model

Helm begins with a separation between intent and instance. The chart describes the shape of an application, the values describe how this installation should vary, and the release records what Helm created for a particular name in a particular namespace. That separation is why the same nginx chart can produce a tiny one-replica classroom workload, a three-replica internal service, or a production chart pinned to specific resources without copying the templates.

The vocabulary is compact, but each word matters during troubleshooting. A chart is not the running application; it is the package. A release is not the chart; it is one installation of that chart. A revision is not a container image tag; it is Helm's stored record of one install, upgrade, or rollback event for that release. When you keep those boundaries clear, Helm errors become much easier to read.

| Term | Description |
|------|-------------|
| **Chart** | Package of Kubernetes resources (like an app) |
| **Release** | Installed instance of a chart |
| **Repository** | Collection of charts (like apt repos) |
| **Values** | Configuration for customizing a chart |
| **Revision** | Version of a release after upgrade/rollback |

At render time, Helm combines templates with values to produce ordinary Kubernetes YAML. The API server never sees a magic Helm object for your Deployment; it sees a Deployment manifest that Helm generated and submitted. Helm then stores release metadata so it can compare, upgrade, roll back, and show you what happened later.

```
Chart (template) + Values (config) = Release (running app)
```

```
┌─────────────────────────────────────────────────────────┐
│                    Helm Workflow                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Repository          Chart            Release           │
│  ┌─────────┐       ┌─────────┐      ┌─────────┐        │
│  │ bitnami │──────▶│  nginx  │─────▶│ my-web  │        │
│  │  repo   │ pull  │  chart  │install│ release │        │
│  └─────────┘       └─────────┘      └─────────┘        │
│                         │                 │            │
│                         ▼                 ▼            │
│                    ┌─────────┐      ┌─────────┐        │
│                    │ values  │      │  Pods   │        │
│                    │  .yaml  │      │Services │        │
│                    └─────────┘      │ConfigMaps│       │
│                                     └─────────┘        │
└─────────────────────────────────────────────────────────┘
```

The diagram hides one operational detail that becomes important during debugging: the Kubernetes objects are still first-class cluster resources. You can inspect Pods with `kubectl`, check labels with selectors, and read events when scheduling or image pull failures occur. Helm gives you the release context, while Kubernetes gives you the workload truth.

Pause and predict: if the chart renders a Deployment whose Pod template references a missing image tag, which tool tells you that Helm installed successfully, and which tool shows that the Pods are failing afterward? The useful answer is both: Helm can report a deployed release because resources were accepted, while `kubectl get pods` and `kubectl describe pod` reveal the runtime failure after controllers start reconciling the workload.

This is the first senior habit to build: always connect Helm state to Kubernetes state. A release can exist while its Pods are pending, a Pod can crash while Helm history looks clean, and a rollback can create a new revision while the old broken revision remains visible in history. Treat Helm as the package manager and Kubernetes as the runtime, then move between them deliberately.

Helm release metadata is useful because it gives you a stable audit trail for operations that otherwise look like separate Kubernetes updates. If an upgrade changes a Deployment and Service at the same time, Kubernetes can show each object, but Helm can show that both changes belonged to one release revision. That grouping is why `helm history` is often the fastest way to reconstruct what changed during a hurried lab or automated deployment.

The release name is part of that audit trail, so naming discipline matters. Two releases can install the same chart with different values, and those releases may create objects whose names include the release name. If you accidentally install `web` and then later install `web-prod`, you have not renamed the first release; you have created a second release with separate history and potentially overlapping Kubernetes resources.

Labels are the bridge between the two worlds. Many charts apply common labels such as `app.kubernetes.io/instance` and `app.kubernetes.io/name`, which make it possible to select the Pods created by a release without guessing generated resource names. When a task asks you to verify a release, label-based `kubectl` queries usually give cleaner evidence than scanning every Pod in the namespace.

Chart versions and application versions are another boundary worth keeping straight. A chart version describes the package and templates, while an app version often describes the software shipped by the chart. Upgrading the chart can change templates, defaults, labels, or helper behavior even when the container image remains the same. Upgrading only the image tag can change runtime behavior while the chart package stays stable.

Helm is therefore best treated as a change coordinator rather than a health oracle. It can coordinate the desired change, store revisions, and render manifests, but controllers still decide whether Pods become ready and Services get endpoints. When troubleshooting, first locate the release and intended configuration, then read the Kubernetes status that proves whether the cluster accepted and achieved that intended state.

## Installing Charts Without Losing Context

Repository management is the front door to most CKAD Helm tasks. You add a repository once, refresh the local index, search for a chart, and then install by repository-qualified chart name. In an exam environment, the repository may already exist, but checking `helm repo list` and refreshing with `helm repo update` costs little and prevents stale chart-index confusion.

```bash
# Add a repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# Add stable repo
helm repo add stable https://charts.helm.sh/stable

# Update repository cache
helm repo update

# List repositories
helm repo list

# Search for charts
helm search repo nginx
helm search repo bitnami/nginx

# Search with versions
helm search repo nginx --versions
```

The archived `stable` repository appears in many older examples, so you should recognize it, but prefer maintained vendor repositories when the task gives you a choice. The repository URL is not where the release lives; it is only where Helm downloads chart metadata and packages. The release lives in a Kubernetes namespace, and that namespace decision follows you through install, list, status, get, history, rollback, and uninstall commands.

Repository cache behavior is easy to overlook because Helm commands feel immediate. `helm repo add` records where a repository lives, while `helm repo update` refreshes the local index that search and install commands consult. If you add a repository and skip the update, you may still be looking at whatever index already existed on disk. In a clean lab that may be nothing; in a long-running workstation it may be stale information.

Search results should also be read carefully. A short name like `nginx` can match multiple charts across multiple repositories, and the first result is not automatically the chart required by the task. Use the repository-qualified name, such as `bitnami/nginx`, when installing so the command is unambiguous. If the task provides a chart version, pin it explicitly instead of letting the repository's latest version decide the package.

Installing a chart is a commitment to a release name, chart reference, namespace, and values set. The release name is the handle you will use later, so choose the exact name from the task rather than improvising. The namespace is equally important because Helm scopes releases by namespace; `helm list -n web` and `helm list -n production` can show different worlds even when the cluster has the same chart installed twice.

```bash
# Install with default values
helm install my-release bitnami/nginx

# Install in specific namespace
helm install my-release bitnami/nginx -n production

# Install and create namespace
helm install my-release bitnami/nginx -n production --create-namespace

# Install with custom values file
helm install my-release bitnami/nginx -f values.yaml

# Install with inline values
helm install my-release bitnami/nginx --set replicaCount=3

# Install with multiple value overrides
helm install my-release bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=NodePort

# Dry-run (see what would be created)
helm install my-release bitnami/nginx --dry-run=client

# Generate name automatically
helm install bitnami/nginx --generate-name
```

Use `--generate-name` only when the task does not care about a stable release name. Most assessment and production workflows do care, because follow-up commands must address the release predictably. A generated name can be fine for a throwaway smoke test, but it is a poor fit for a requirement that later says "upgrade the release named `web`" or "rollback `frontend` to revision 1."

Install commands should be written as if someone will need to explain them later. The release name, chart reference, namespace, values file, and inline overrides are the evidence of your intent. A command copied from a tutorial with a different release name may create valid resources while still failing the requirement. A command that names the release and namespace exactly as requested gives you a clean path to later verification.

When a chart creates several objects, do not assume the resource names will all match the release name exactly. Many charts generate names through helpers that combine release name, chart name, fullname overrides, and truncation rules. Labels are often more stable for verification than generated names. That is why the lab checks Pods with `app.kubernetes.io/instance=web` rather than assuming a specific Pod prefix.

Listing releases is your orientation step after installation. Use the namespace flag when the task names a namespace, and use all namespaces when you are unsure where a release was created. In practice, many apparent Helm failures are simply namespace mismatches: the chart installed correctly, but the operator is listing from the wrong scope.

```bash
# List releases in current namespace
helm list

# List in all namespaces
helm list -A

# List in specific namespace
helm list -n production

# List with status
helm list --all

# Filter by status
helm list --failed
helm list --pending
```

The next layer is inspection before and after install. `helm show` reads chart metadata and default values from the chart source, while `helm get` reads information from an installed release. That distinction prevents a common debugging error: looking at defaults and assuming they are the live values. Defaults are the recipe; release data is the meal that was actually cooked.

```bash
# Show chart info
helm show chart bitnami/nginx

# Show default values
helm show values bitnami/nginx

# Show all info
helm show all bitnami/nginx

# Get release values
helm get values my-release

# Get all release info
helm get all my-release

# Get release manifest (rendered YAML)
helm get manifest my-release

# Get release history
helm history my-release
```

Before running this, what output do you expect from `helm show values bitnami/nginx` compared with `helm get values my-release` after you install with `--set replicaCount=3`? The first command should show the chart's default configuration, while the second should show values stored for the release. If you need every computed value, including defaults, use `helm get values <release> -a` (or `--all`) rather than assuming user-supplied values are the whole picture.

Namespace targeting is also why Helm and `kubectl` verification commands should be paired. If you install `my-release` into `web`, verify the release with `helm list -n web` and verify the workload with `kubectl get pods -n web`. Keeping the namespace flag consistent makes your transcript easy to audit and prevents you from chasing objects in the wrong place.

If a release appears missing, resist the urge to reinstall immediately. First run `helm list -A` and inspect namespaces, because a second install with the same chart and a different namespace can make cleanup harder. If the release is found elsewhere, decide whether the correct action is uninstalling the mistaken release or reinstalling in the required namespace. The right answer depends on the task, but discovery should come before mutation.

The same principle applies to chart inspection. `helm show values` is useful before installation because it tells you which knobs the chart exposes, but it does not prove what an installed release is using. After installation, switch to `helm get values` and `helm get manifest` so you inspect the release that exists in the cluster. Mixing those two perspectives is a common source of false confidence.

## Values as the Contract Between Chart and Cluster

Values are the contract between the generic chart and the specific cluster state you want. The chart author chooses which knobs exist, and you choose how to set those knobs for this environment. That contract is powerful because it reduces duplication, but it is also where many Helm mistakes begin: a misspelled key can be silently ignored by a template, a string can be parsed as a number, and an upgrade can unintentionally drop a previous override.

Helm applies values in a precedence order, with later and more specific inputs winning. Think of the chart default as the factory setting, the values file as the environment profile, and `--set` as a command-line correction for this one run. The model is simple, but it becomes easy to misuse when you spread important settings across a long shell command that nobody can review.

### Values Hierarchy (Lowest to Highest Priority)

1. Default values in chart (`values.yaml`)
2. Parent chart values
3. Values file passed with `-f`
4. Individual values with `--set`

The hierarchy explains why an inline value wins over a file. It also explains why multiple files are read from left to right, with later files overriding earlier ones when the same key appears. That design lets you keep a base `values.yaml`, layer a `production.yaml`, and still apply a one-off override for a short exercise without editing the file.

### Values File Example

```yaml
# my-values.yaml
replicaCount: 3

image:
  repository: nginx
  tag: "1.21"
  pullPolicy: IfNotPresent

service:
  type: NodePort
  ports:
    http: 80

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

nodeSelector:
  disktype: ssd
```

The example file intentionally quotes the image tag. YAML has type coercion rules that can surprise you, and version-looking strings are better treated as strings. Resource requests and limits remain Kubernetes quantities, so their units matter. A chart can make those values convenient to set, but the resulting Deployment must still be valid for the Kubernetes 1.35+ API server.

Values are not automatically validated unless the chart provides a schema or the rendered manifests fail Kubernetes validation. That means a typo may simply produce no change if the template never reads the misspelled key. The safest habit is to inspect defaults to find the exact path, apply the override, render or dry-run the manifest, and then verify that the live object contains the expected field.

Secret values deserve special caution. Helm can render Secrets, but release history may still store rendered manifests and values in Kubernetes storage depending on the command and driver behavior. Do not put realistic credentials into examples, and do not treat a values file as a secure secret manager. For production systems, integrate chart values with the organization's approved secret workflow instead of embedding sensitive material in reusable files.

```bash
# Install with values file
helm install my-release bitnami/nginx -f my-values.yaml

# Multiple values files (later overrides earlier)
helm install my-release bitnami/nginx -f values.yaml -f production.yaml

# Combine file and inline
helm install my-release bitnami/nginx -f values.yaml --set replicaCount=5
```

Values files are usually the safer default for anything you would want to repeat. They are reviewable, diffable, and less error-prone than a long `--set` chain. Inline overrides still matter in CKAD-style tasks because they are fast, but use them for small changes such as replica count, service type, or one named key rather than for a whole environment profile.

There is also a human factor. A values file can be read by someone who does not know the exact shell command that created the release, while a long command may only live in terminal history. When an upgrade fails, a file gives you a stable comparison point: expected values, previous values, and current release values. That comparison is often enough to reveal whether the mistake is an omitted key, a typo, or an intentional change.

```bash
# Simple value
--set replicaCount=3

# Nested value
--set image.tag=1.21

# String value (use quotes for special chars)
--set image.repository="my-registry.com/nginx"

# Array value
--set nodeSelector.disktype=ssd

# Multiple values
--set replicaCount=3,service.type=NodePort

# List items
--set ingress.hosts[0].host=example.com
```

Pause and predict: if you pass both a values file with `replicaCount: 2` and `--set replicaCount=5` on the same install command, which value wins? The inline `--set` value wins because it is the most specific layer. That behavior lets command-line overrides patch a reusable file, but it also means a rushed shell command can hide the value that reviewers expect to see in version control.

The design rule is to keep durable intent in a file and temporary intent on the command line. If a setting explains how production should run, put it in a values file. If a setting exists only to complete a lab or test a small change, `--set` is acceptable. This distinction makes upgrades safer because you can reapply the full file instead of reconstructing previous choices from memory.

For CKAD practice, learn both forms instead of choosing one permanently. A time-boxed task may reward a short inline override, while a troubleshooting prompt may require you to open or create a values file. The skill is not "always use files" or "always use `--set`"; the skill is matching the persistence of the configuration to the persistence of the task.

When multiple value sources are involved, write the command in the same order you want Helm to reason about them. Start with broad defaults through files, then add the narrowest override last. If the final result surprises you, simplify the command and render again. Debugging values is much easier when each layer has an identifiable purpose instead of being a pile of unrelated flags.

## Release Lifecycle: Install, Upgrade, Roll Back, and Uninstall

A Helm release has a history, and that history is the reason rollback is possible. The first install creates revision 1. Each upgrade creates a later revision. A rollback also creates a new revision that points the live resources back toward an earlier state, so history is not erased. This is different from thinking "rollback deletes the bad upgrade"; Helm records the recovery action as part of the timeline.

History is especially helpful when two changes happen close together. Imagine one upgrade changed `replicaCount`, and the next changed the image tag. If Pods start failing after the second change, rolling back to the immediately previous revision may preserve the replica change while undoing the image change. If you instead roll back too far, you may fix the image problem but also undo a valid scaling change. The history table is how you decide.

Release descriptions can improve that decision when automation uses them, because they give future operators context beyond a revision number. Even without custom descriptions, the status and updated timestamp can guide your investigation. The key is to read history before action, not after. Once you have rolled back, the history changes again, and the original sequence becomes slightly harder for beginners to interpret.

Upgrades are where values discipline matters most. If you run `helm upgrade` with only one inline value, Helm has to decide what to do with values from the previous release and values from the new chart defaults. The `--reuse-values` flag tells Helm to carry the previous release's values forward and then apply your new overrides, which is often the intended behavior for a small change.

```bash
# Upgrade with new values
helm upgrade my-release bitnami/nginx --set replicaCount=5

# Upgrade with values file
helm upgrade my-release bitnami/nginx -f new-values.yaml

# Upgrade or install if not exists
helm upgrade --install my-release bitnami/nginx

# Reuse existing values and add new ones
helm upgrade my-release bitnami/nginx --reuse-values --set image.tag=1.21
```

Stop and think: you run `helm upgrade my-release bitnami/nginx --set replicaCount=5` without `--reuse-values`. What should you check before assuming the release still has every customization from the previous install? Inspect the release values and compare them with the values file you intended to preserve. The bug is not that Helm upgraded; the bug is that the operator did not make the desired value set explicit.

In automated delivery, `helm upgrade --install` is popular because it turns two possible states into one command path. That convenience does not remove the need for explicit values, chart version selection, namespace targeting, and verification. The command answers "should this release exist after the job runs?" It does not answer "did we select the exact package and configuration intended for this environment?"

Helm also has failure-management flags that can change the operational result of an upgrade, but you should understand the release model before relying on them. A rollback-on-failure behavior can help avoid leaving a failed release as the visible end state, yet the attempted change still deserves investigation. Automated rollback is not a substitute for reading history, status, and Kubernetes events when a deployment fails.

Rollback should be deliberate, not a reflex. First read history, identify the revision that corresponds to the last known good state, and then roll back to that revision. If you omit the revision, Helm rolls back to the previous revision, which is convenient when you know the last upgrade is the only problem and risky when several changes have happened quickly.

```bash
# Rollback to previous revision
helm rollback my-release

# Rollback to specific revision
helm rollback my-release 2

# Check history first
helm history my-release
```

Uninstalling removes the release's Kubernetes resources, while `--keep-history` preserves release history metadata. In an exam lab, cleanup matters because old resources can interfere with later tasks. In production, cleanup decisions need more care because PVCs, CRDs, and external resources may have lifecycle rules that outlive the Helm release itself.

```bash
# Uninstall release
helm uninstall my-release

# Uninstall but keep history
helm uninstall my-release --keep-history

# Uninstall from namespace
helm uninstall my-release -n production
```

The quickest complete workflow is install, verify, upgrade, verify, rollback only if needed, and cleanup when the task is done. Notice that verification appears after every state-changing command. Helm can tell you whether the release operation ran, but Kubernetes tells you whether the Pods, Services, labels, and events match the desired state.

One more lifecycle detail matters for cleanup: uninstalling a release is not the same as deleting every object that ever touched the application. Charts can use hooks, retain policies, persistent volumes, or CRDs that need separate handling depending on chart design. For this module's nginx exercises, normal uninstall is enough, but the habit of checking remaining resources is valuable when you later work with databases or operators.

If a chart includes CRDs, understand that Helm has special behavior around installing and upgrading them. Many application charts avoid this complexity, but platform charts and operators often depend on it. The practical takeaway for CKAD-level work is to recognize when a chart creates ordinary namespaced workloads versus cluster-scoped supporting resources. That recognition affects cleanup, permissions, and what namespace flags can actually control.

### Scenario 1: Install and Configure

```bash
# Add repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install with custom values
helm install my-nginx bitnami/nginx \
  --set replicaCount=2 \
  --set service.type=ClusterIP \
  -n web --create-namespace

# Verify
helm list -n web
kubectl get pods -n web
```

This first scenario demonstrates why `--create-namespace` is useful and why it should not replace clear namespace thinking. The flag creates the target namespace if needed, but every later Helm and Kubernetes command still needs the same namespace. If the task asks for `web`, write `-n web` consistently so that your release and workload checks line up.

### Scenario 2: Upgrade and Rollback

```bash
# Check current release
helm list -n web
helm get values my-nginx -n web

# Upgrade
helm upgrade my-nginx bitnami/nginx --reuse-values --set replicaCount=3 -n web

# Verify upgrade
helm history my-nginx -n web
kubectl get pods -n web

# Something goes wrong - rollback
helm rollback my-nginx 1 -n web

# Verify
helm list -n web
```

This second scenario is intentionally narrow: only replica count changes because `--reuse-values` carries forward the prior `service.type=ClusterIP` override. Omitting `--reuse-values` on an upgrade that passes only `--set replicaCount=3` re-applies chart defaults for every value not listed on that command line (for example, `service.type` can revert to `LoadBalancer`). In a real environment, you would usually prefer a values file or `--reuse-values` so the upgrade does not depend on remembering every previous override. In an exam, the important habit is to check values and history before taking recovery action, because rolling back to the wrong revision wastes time and may hide the actual mistake.

### Scenario 3: Inspect Before Install

```bash
# See what you're installing
helm show values bitnami/nginx | head -50

# Dry run to see generated manifests
helm install test bitnami/nginx --dry-run=client | head -n 50

# Then install
helm install test-nginx bitnami/nginx
```

Dry runs are a cheap way to catch obvious rendering and configuration surprises. Helm 4 also distinguishes client and server dry-run behavior, but the operational idea is the same: inspect generated manifests before you make the cluster change when the task is ambiguous. Remember that a dry run can show rendered Secrets, so do not paste sensitive output into tickets or chat systems.

Pinning chart versions is another lifecycle control that matters more outside a timed lab. Repository defaults move as maintainers publish new packages, so "install the latest chart" is not reproducible unless latest is truly the requirement. A real delivery pipeline should usually pin chart versions, review release notes, and intentionally upgrade the chart package. In a CKAD exercise, follow the version the prompt gives you, if any.

## Chart Structure and Debugging Workflow

You do not need to author a complete chart for this module, but chart structure explains what you are inspecting. `Chart.yaml` describes metadata, `values.yaml` defines defaults, `templates/` holds the Kubernetes manifests with template expressions, and `charts/` stores dependencies. When Helm renders, it reads those pieces together and produces ordinary manifests that the Kubernetes API server can validate.

```
my-chart/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default configuration
├── charts/             # Dependency charts
├── templates/          # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── _helpers.tpl    # Template helpers
│   └── NOTES.txt       # Post-install notes
└── README.md
```

The tree also explains why debugging should move from broad to specific. First ask whether the release exists in the expected namespace. Then ask what values Helm stored. Then render or retrieve the manifest and compare the generated resource fields with the task. Finally, use `kubectl` to inspect the live objects and events because runtime failures belong to Kubernetes controllers, not to the chart package alone.

Template helpers are worth recognizing even if you never edit them in this module. Files such as `_helpers.tpl` often define names, labels, and selector fragments reused across multiple templates. If a generated Deployment and Service share a selector, that consistency may come from a helper. If labels look different from what you expected, the helper is one reason the chart may produce names that do not exactly mirror the release name.

`NOTES.txt` is another chart file with operational value. It does not create Kubernetes objects, but it can print useful post-install instructions, service URLs, test commands, or chart-specific caveats. When a release installs successfully and you do not know how to reach it, `helm get notes` can be faster than guessing which Service port or label the chart author intended you to use.

What would happen if you run `helm install my-app bitnami/nginx` in the `default` namespace, then later run `helm list` in the `production` namespace? You would not see `my-app` from the production-scoped list because Helm release records are namespace-scoped. This matters during the exam because a correct release in the wrong namespace is still wrong for a namespaced requirement.

```bash
# Release stuck in pending-install
helm list --pending
helm uninstall stuck-release

# See what's wrong
helm get manifest my-release | kubectl apply --dry-run=server -f -

# Debug template rendering
helm template my-release bitnami/nginx --debug

# Check release status
helm status my-release
```

The `helm get manifest` pipeline is especially useful when the release already exists. It lets you retrieve the exact manifest Helm stored for that release and ask the Kubernetes API server to validate it. That does not prove the workload is healthy, but it can reveal schema and admission issues without guessing which template or value produced the problematic field.

Rendered-manifest debugging should stay connected to ownership. If you hand-edit a Helm-managed Deployment with `kubectl edit`, Helm does not automatically learn that as a values change. A later upgrade can overwrite the manual edit because Helm renders from chart and values again. For managed resources, prefer fixing the value input or chart version so future Helm operations reproduce the desired state.

```bash
# See rendered templates
helm template my-release bitnami/nginx > rendered.yaml

# Validate without installing
helm install my-release bitnami/nginx --dry-run=client --debug

# Get notes (post-install instructions)
helm get notes my-release
```

`helm template` renders locally and is excellent for understanding how values turn into YAML. `helm install --dry-run=client --debug` simulates the install path and prints diagnostic context. `helm get notes` is easy to ignore, but many charts include post-install instructions there, including service discovery hints or default credentials placeholders that explain how to test the application safely.

A practical debugging sequence for CKAD work is: list the release, get status, get values, get manifest, inspect Kubernetes objects by label, then read events from a failing Pod. Do not start by changing values blindly. The fastest fix is usually the one that proves whether the failure is chart selection, namespace scope, values precedence, rendered YAML, or runtime behavior.

The same sequence works when the release status itself is pending or failed. Pending states can come from hooks, waiting behavior, unavailable resources, or interrupted operations, so read `helm status` before cleanup. If you decide to uninstall a stuck release, verify whether any Pods, Jobs, or Services remain afterward. Cleanup without inspection can hide useful evidence or leave objects that interfere with the next install.

Finally, keep command output scoped. `helm get all` can be useful, but it may be noisy, and noisy output burns exam time. Use the narrow command first: values when debugging configuration, manifest when debugging rendered YAML, notes when looking for access instructions, and history when recovering a previous state. The right narrow command gives you a cleaner answer than a broad dump you have to skim.

## Patterns & Anti-Patterns

Patterns and anti-patterns are useful only when they change your next command. For Helm, the difference between a reliable workflow and a fragile one is usually not the syntax of `helm install`; it is whether the operator keeps values reviewable, namespaces explicit, and verification connected to both Helm and Kubernetes state. The table below turns those habits into decision rules you can apply during labs and real deployments.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Values file as environment contract | Repeated installs or upgrades for dev, staging, or production | Keeps durable settings reviewable and reproducible | Store files with the application or platform repo so chart upgrades can be reviewed |
| Namespace-explicit commands | Any task outside `default` or any multi-team cluster | Prevents release lookup and workload verification from drifting apart | Use scripts or CI variables to pass the namespace consistently |
| Inspect before mutate | Unknown chart, unclear defaults, or high-risk upgrade | `helm show values`, dry run, and template output expose generated intent | Add render validation to pipelines before cluster changes |
| History-first rollback | Failed upgrade or suspected bad release revision | Avoids rolling back to the wrong revision under pressure | Keep release descriptions meaningful when automation performs upgrades |

| Anti-pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Long unrepeated `--set` chains | Important settings disappear from review and are easy to mistype | Move durable settings into a values file and reserve `--set` for small overrides |
| Listing without namespace context | A valid release appears missing, or the wrong release is inspected | Use `helm list -A` for discovery, then repeat `-n <namespace>` on focused commands |
| Treating Helm success as app health | The release exists while Pods crash, stay pending, or fail readiness | Pair Helm checks with `kubectl get pods`, `kubectl describe`, and label-based selectors |
| Rollback without history | Recovery targets the wrong revision or hides the original failure | Run `helm history` and choose the revision intentionally |

The senior habit underneath both tables is evidence sequencing. Helm has enough commands that you can always run another command, but another command is not automatically useful. Choose the command that narrows the failure domain: repository, chart, values, release history, rendered manifest, or live Kubernetes object. When each step has a purpose, Helm becomes fast instead of noisy.

## Decision Framework

Use this framework when a task gives you a Helm release and asks for a change or diagnosis. Start by identifying whether the release already exists, then decide whether you are reading, rendering, mutating, or recovering. The table is intentionally command-oriented because under time pressure you need a small set of reliable moves, not a philosophical taxonomy of package managers.

| Situation | First Command | Follow-up Command | Decision Rule |
|-----------|---------------|-------------------|---------------|
| You do not know where the release lives | `helm list -A` | `helm status <release> -n <namespace>` | Discover globally, then work in the exact namespace |
| You need default chart options | `helm show values <chart>` | `helm show chart <chart>` | Read chart defaults before choosing override keys |
| You need live release settings | `helm get values <release> -n <namespace>` | `helm get manifest <release> -n <namespace>` | Inspect stored release state, not just chart defaults |
| You need a first deployment | `helm install <release> <chart> -n <namespace>` | `kubectl get pods -n <namespace>` | Install, then verify workload objects in Kubernetes |
| You need repeatable deployment | `helm upgrade --install <release> <chart>` | `helm history <release> -n <namespace>` | Use idempotent upgrade/install when automation may run twice |
| You need a small change | `helm upgrade <release> <chart> --reuse-values --set key=value` | `helm get values <release> -n <namespace>` | Carry forward prior settings unless you intentionally replace them |
| You need recovery | `helm history <release> -n <namespace>` | `helm rollback <release> <revision> -n <namespace>` | Pick the known-good revision, then verify Pods and Services |

The framework also tells you when Helm is the wrong first tool. If Pods are already created and failing image pulls, start with Kubernetes events after confirming the release exists. If the Service is unreachable, inspect the generated Service and the selected Pods. If the release itself is pending or failed, stay in Helm long enough to read status and manifest, then cross-check the Kubernetes objects that Helm created.

Which approach would you choose here and why: a one-time lab asks you to set `replicaCount=3`, while your production deployment needs replicas, resource requests, service type, node selector, and image tag? The lab can use `--set` because the override is small and disposable. The production deployment should use a values file because the settings define long-lived operational intent that deserves review and repeatability.

## Did You Know?

- **Helm 3 removed Tiller.** Helm 2 used a server-side component called Tiller that commonly required broad cluster permissions, while Helm 3 and later use the user's Kubernetes credentials directly from the client workflow.
- **Helm 4 is the current major line in the official documentation.** The Helm docs now show Helm 4 features such as server-side apply for new releases, while Helm 3 releases can continue to use their existing client-side apply behavior after an upgrade.
- **`helm upgrade --install` is idempotent.** It installs when the release does not exist and upgrades when it does, which makes it useful for CI/CD jobs and repeatable exam practice scripts.
- **Helm stores release history in Kubernetes storage.** The default driver stores revisions as Secrets, which is why rollback can target older revisions and why namespace scope matters for release discovery.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Forgetting `helm repo update` | The local repository index is stale, so searches and installs may not reflect current chart metadata | Run `helm repo update` after adding a repository and before relying on search results |
| Wrong namespace | Helm commands default to the current namespace, while the task may require `web`, `production`, or another target | Use `-n namespace` consistently and use `helm list -A` when discovering an unknown release |
| `--set` typos | Chart values are key-based, so a misspelled path may not change the rendered field you intended | Check `helm show values`, run a dry run, and inspect `helm get values` after installation |
| Forgetting `--reuse-values` | An upgrade meant to change one field can lose previous customizations when the full desired values are not supplied | Use a complete values file or add `--reuse-values` for small follow-up changes |
| Not checking history before rollback | The previous revision might not be the last known good state after multiple changes | Run `helm history` and rollback to a specific revision when the target matters |
| Confusing chart defaults with release values | `helm show values` reads the chart, not the installed release | Use `helm get values <release> -n <namespace>` for the live release configuration |
| Treating rendered YAML as runtime proof | A manifest can be valid while Pods fail image pulls, scheduling, or readiness | Pair `helm get manifest` with `kubectl get pods`, `kubectl describe`, and events |

## Quiz

<details>
<summary>Question 1: Your CI/CD pipeline needs to deploy a chart that may or may not already be installed in the cluster. It should install on first run and upgrade on later runs without failing on an existing release. What Helm pattern should you use?</summary>

Use `helm upgrade --install my-release bitnami/nginx` with the correct namespace and values inputs. The `--install` flag makes the upgrade path idempotent because Helm installs when the release is absent and upgrades when it already exists. A plain `helm install` would fail after the first successful run, while a plain `helm upgrade` would fail before the release exists. For safer automation, add the chart version and the values file you intend to be authoritative rather than depending on changing repository defaults.
</details>

<details>
<summary>Question 2: A teammate upgraded a release with `helm upgrade my-app bitnami/nginx --set replicaCount=5`, and now `service.type` has gone back to the chart default instead of the earlier `ClusterIP` value. What should you diagnose and how should future upgrades be written?</summary>

Diagnose the release values first with `helm get values my-app -n <namespace>` and compare them with the values file or install command that created the previous revision. The likely mistake is that the upgrade supplied only one inline value and did not carry forward the earlier custom settings. Future upgrades should use a complete values file or use `--reuse-values` when applying a small additional override. Rolling back can restore the previous revision, but the durable fix is making the desired values explicit.
</details>

<details>
<summary>Question 3: During an exam task, the release `web-prod` exists in the `frontend` namespace, but `helm get values web-prod` returns a release-not-found error. What should you check before changing the chart?</summary>

Check namespace scope before changing anything. Helm releases are namespaced, so the command should be `helm get values web-prod -n frontend` unless your current context already points there. Use `helm list -A` when you are unsure where the release lives, then repeat the discovered namespace on status, values, history, rollback, and uninstall commands. Changing values before confirming namespace context wastes time and can create a second release in the wrong namespace.
</details>

<details>
<summary>Question 4: You installed a chart and the Pods are crash-looping. You need to inspect the exact Kubernetes YAML that Helm generated and then decide whether the problem is rendering or runtime behavior. What sequence should you use?</summary>

Start with `helm get manifest <release> -n <namespace>` to retrieve the rendered YAML stored for the release. If the manifest looks suspicious, validate or render again with `helm template` or a dry run using the same values. If the manifest is correct, switch to Kubernetes checks such as `kubectl get pods -n <namespace>` and `kubectl describe pod` to read events, container state, and readiness details. Helm can show what it submitted, but Kubernetes explains why the workload is not healthy.
</details>

<details>
<summary>Question 5: You need to deploy nginx into a new `web` namespace with two replicas and an internal service. Which parts of the command protect you from the two most common mistakes?</summary>

Use the explicit namespace and creation flags, such as `helm install my-nginx bitnami/nginx --set replicaCount=2 --set service.type=ClusterIP -n web --create-namespace`. The namespace flag prevents the release from landing in `default`, and `--create-namespace` handles the case where `web` does not exist yet. The inline values set the required replica count and service type for this small task. Verification should still include `helm list -n web` and `kubectl get pods -n web`.
</details>

<details>
<summary>Question 6: An upgrade failed, and a teammate wants to immediately run `helm rollback my-app` with no revision argument. What information should you gather first, and when is the shorthand acceptable?</summary>

Run `helm history my-app -n <namespace>` first so you can see the revision sequence and identify the last known good state. The no-revision shorthand is acceptable only when you are confident that the immediately previous revision is the desired target. If several upgrades or rollbacks happened recently, an explicit revision is safer because it avoids recovering to another bad state. After rollback, verify both Helm status and Kubernetes workload health.
</details>

<details>
<summary>Question 7: You are choosing between a values file and `--set` for a deployment that includes resources, service type, image tag, node selector, and replica count. Which approach should you choose and why?</summary>

Choose a values file for that deployment because the configuration is durable, multi-key, and worth reviewing as a complete environment contract. A long `--set` command is easy to mistype and hard to reconstruct during the next upgrade. Inline overrides are still useful for small, temporary changes such as one replica adjustment in a lab. For the larger deployment, store the values file, install or upgrade with `-f`, and inspect the release values afterward.
</details>

## Hands-On Exercise

Exercise scenario: deploy and operate a Helm-managed nginx release, then prove that you can inspect values, upgrade safely, roll back deliberately, and clean up without leaving stray resources. The workflow uses the Bitnami nginx chart because it exposes enough values to practice real override behavior without requiring chart authoring. Run the commands in a disposable Kubernetes 1.35+ lab cluster or the linked Killercoda environment.

**Setup:**

```bash
# Add repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Task 1: Inspect and Install

Read the available values before installing, then deploy a release named `web` with two replicas and a ClusterIP service. This task trains the habit of inspecting the chart first, applying a small override second, and verifying both Helm state and Kubernetes Pods after the install. If the chart defaults already match part of the requirement, still set the requested values so your command transcript is explicit.

```bash
# See available values
helm show values bitnami/nginx | head -30

# Install with custom values
helm install web bitnami/nginx \
  --set replicaCount=2 \
  --set service.type=ClusterIP

# Verify installation
helm list
kubectl version --short
kubectl get pods -l app.kubernetes.io/instance=web
```

<details>
<summary>Solution notes for Task 1</summary>

The release should appear in `helm list`, and the Pod selector should return Pods labeled with `app.kubernetes.io/instance=web`. If no Pods appear, check whether the release was installed into a namespace other than your current context. If Pods appear but are not ready, describe one Pod and read the events before changing Helm values.
</details>

### Task 2: Upgrade

Upgrade the same release to three replicas while carrying forward the existing custom service setting. The important part is not merely increasing replica count; it is preserving prior intent during a follow-up command. After the upgrade, use history to confirm a new revision exists and use Kubernetes to confirm the Deployment reconciled the requested number of Pods.

```bash
# Upgrade replicas
helm upgrade web bitnami/nginx --reuse-values --set replicaCount=3

# Check history
helm history web

# Verify pods
kubectl get pods -l app.kubernetes.io/instance=web
```

<details>
<summary>Solution notes for Task 2</summary>

`helm history web` should show a later revision after the upgrade. The Pod count should move toward the requested replica count, though Kubernetes may take a short time to create or terminate Pods. If the service setting changed unexpectedly, inspect `helm get values web` and review whether your upgrade reused or replaced previous values.
</details>

### Task 3: Rollback

Roll the release back to revision 1, then inspect the values and Pods again. This task reinforces that rollback is a release operation with observable Kubernetes consequences. Do not treat rollback as invisible; it creates another history entry and asks the cluster to reconcile resources back toward the selected revision's rendered state.

```bash
# Rollback to revision 1
helm rollback web 1

# Verify reverted
helm get values web
kubectl get pods -l app.kubernetes.io/instance=web
```

<details>
<summary>Solution notes for Task 3</summary>

After rollback, `helm get values web` should reflect the values stored for the target revision. The Pod count may change again as the Deployment reconciles. If the values look right but Pods do not, move to Kubernetes events and Deployment status rather than repeating rollback commands blindly.
</details>

### Task 4: Cleanup

Remove the release after you finish the workflow. Cleanup is part of the exercise because a stale release can make later drills confusing, especially when selectors return old Pods or `helm install` fails because the release name is already taken. If you installed into a non-default namespace, include the same namespace flag during uninstall.

```bash
helm uninstall web
```

<details>
<summary>Solution notes for Task 4</summary>

`helm list` should no longer show the release in the namespace where it was installed. If workload objects remain, check whether they were created by hooks, retained by chart policy, or installed into a different namespace. For this basic nginx workflow, normal uninstall should remove the release-managed objects.
</details>

### Practice Drills

The drills below are intentionally small and repetitive. Run them after the main workflow until the command sequence feels automatic: repository, install, inspect, upgrade, history, rollback, namespace, cleanup. Speed matters in CKAD-style work, but only after the command sequence is correct.

#### Drill 1: Repository Management (Target: 2 minutes)

```bash
# Add bitnami repo
helm repo add bitnami https://charts.bitnami.com/bitnami

# Update
helm repo update

# Search for mysql
helm search repo mysql

# List repos
helm repo list
```

#### Drill 2: Basic Install (Target: 2 minutes)

```bash
# Install nginx
helm install drill2 bitnami/nginx

# List releases
helm list

# Check status
helm status drill2

# Cleanup
helm uninstall drill2
```

#### Drill 3: Install with Values (Target: 3 minutes)

```bash
# Create values file
cat << 'EOF' > /tmp/values.yaml
replicaCount: 2
service:
  type: ClusterIP
EOF

# Install with values file
helm install drill3 bitnami/nginx -f /tmp/values.yaml

# Verify values applied
helm get values drill3

# Cleanup
helm uninstall drill3
```

#### Drill 4: Upgrade and Rollback (Target: 4 minutes)

```bash
# Install
helm install drill4 bitnami/nginx --set replicaCount=1

# Verify install
helm status drill4

# Upgrade
helm upgrade drill4 bitnami/nginx --set replicaCount=3

# Check history
helm history drill4

# Rollback
helm rollback drill4 1

# Verify
helm get values drill4

# Cleanup
helm uninstall drill4
```

#### Drill 5: Namespace Operations (Target: 3 minutes)

```bash
# Install in new namespace
helm install drill5 bitnami/nginx -n helm-test --create-namespace

# List in namespace
helm list -n helm-test

# Get pods in namespace
kubectl get pods -n helm-test

# Cleanup
helm uninstall drill5 -n helm-test
kubectl delete ns helm-test
```

#### Drill 6: Complete Scenario (Target: 6 minutes)

**Scenario**: Deploy a production-ready nginx.

To make the deployment production-ready, we increase replicas for high availability, use a NodePort to ensure external connectivity, and apply strict resource limits to prevent the application from consuming excess cluster capacity. In a real production system you would usually review those values in a file and pin the chart version; this drill keeps the focus on the Helm release lifecycle.

```bash
# 1. Create values file
cat << 'EOF' > /tmp/prod-values.yaml
replicaCount: 3
service:
  type: NodePort
  nodePorts:
    http: 30080
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
EOF

# 2. Dry-run first
helm install prod-web bitnami/nginx -f /tmp/prod-values.yaml --dry-run=client

# 3. Install
helm install prod-web bitnami/nginx -f /tmp/prod-values.yaml

# 4. Verify
helm list
helm get values prod-web
kubectl get pods -l app.kubernetes.io/instance=prod-web

# 5. Upgrade with more replicas
helm upgrade prod-web bitnami/nginx -f /tmp/prod-values.yaml --set replicaCount=5

# Verify upgrade
helm status prod-web
kubectl get pods -l app.kubernetes.io/instance=prod-web

# 6. Something wrong - rollback
helm rollback prod-web 1

# 7. Cleanup
helm uninstall prod-web
```

### Success Criteria

- [ ] Your cluster reports Kubernetes 1.35+ (`kubectl version` shows a compatible server version).
- [ ] You can add and update the Bitnami repository without relying on a preconfigured environment.
- [ ] You can deploy a named Helm release with custom values and verify it with both Helm and `kubectl`.
- [ ] You can explain which value wins when defaults, values files, and `--set` all define the same key.
- [ ] You can upgrade a release while preserving previous values intentionally.
- [ ] You can inspect release history and roll back to a specific revision.
- [ ] You can clean up releases and namespaces without leaving stale lab resources.

## Learner check

> Omitting `--reuse-values` on an upgrade that passes only `--set replicaCount=3` re-applies chart defaults for every value not listed on that command line (for example, `service.type` can revert to `LoadBalancer`).

## Sources

- https://docs.helm.sh/docs/
- https://docs.helm.sh/docs/overview/
- https://docs.helm.sh/docs/intro/using_helm/
- https://docs.helm.sh/docs/topics/charts/
- https://docs.helm.sh/docs/chart_best_practices/values/
- https://docs.helm.sh/docs/helm/helm_install/
- https://docs.helm.sh/docs/helm/helm_upgrade/
- https://docs.helm.sh/docs/helm/helm_rollback/
- https://docs.helm.sh/docs/helm/helm_history/
- https://docs.helm.sh/docs/helm/helm_get_values/
- https://docs.helm.sh/docs/helm/helm_get_manifest/
- https://docs.helm.sh/docs/helm/helm_template/
- https://docs.helm.sh/docs/helm/helm_uninstall/
- https://artifacthub.io/packages/helm/bitnami/nginx
- https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/
- https://www.cncf.io/training/certification/ckad/

## Next Module

[Module 2.3: Kustomize](../module-2.3-kustomize/) - Customize Kubernetes resources without templates.
