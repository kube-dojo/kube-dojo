---
revision_pending: false
title: "Module 4.6: Custom Resource Definitions (CRDs)"
slug: k8s/ckad/part4-environment/module-4.6-crds
sidebar:
  order: 6
lab:
  id: ckad-4.6-crds
  url: https://killercoda.com/kubedojo/scenario/ckad-4.6-crds
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - New to CKAD 2025, conceptual understanding important
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Understanding of Kubernetes resources and API structure

---

## Learning Outcomes

After completing this module, you will be able to:
- **Design** a namespaced CustomResourceDefinition with schema validation, version flags, and predictable resource names.
- **Implement** custom resources and use `kubectl` discovery commands to confirm served resources, short names, and validation behavior.
- **Diagnose** validation, naming, scope, and operator-reconciliation failures by separating API-server behavior from controller behavior.
- **Evaluate** when a CRD, ConfigMap, built-in workload API, or full Operator is the right abstraction for a Kubernetes 1.35+ platform.

## Why This Module Matters

Hypothetical scenario: your platform team installs a database operator into a shared Kubernetes cluster. Application teams are told to create `Database` objects instead of writing StatefulSets, PersistentVolumeClaims, Services, Secrets, and backup CronJobs by hand. The first request appears simple, but the operational stakes are high: if the CRD schema accepts misspelled fields, the API server stores invalid intent; if the operator is missing, the custom object exists but no database appears; if someone deletes the CRD, every custom resource of that type can disappear with it.

That scenario is why CRDs matter for CKAD candidates even when the exam does not ask you to write a production-grade operator. Custom Resource Definitions extend the Kubernetes API with new nouns, so `kubectl get databases` can become as natural as `kubectl get pods`. The API server stores and validates those new objects, while a controller, often packaged as an Operator, watches the objects and turns declared intent into real cluster resources.

The practical skill is not memorizing one CRD manifest. The skill is reading the contract between the CRD, the custom resource, the API server, and the controller. In Kubernetes 1.35 and newer, that contract is strict enough to catch many mistakes before an operator ever runs, yet flexible enough that teams can model domain-specific workflows such as certificates, monitoring rules, gateways, backups, and databases.

The custom forms analogy still works well. Kubernetes built-in resources are like standard government forms: everyone recognizes a Pod, a Service, and a Deployment. A CRD lets an organization introduce a new official form with its own required fields, allowed values, and storage location. The operator is the clerk that reads submitted forms, performs the work, records status, and keeps checking until reality matches the form.

## CRDs Extend the Kubernetes API

A CustomResourceDefinition is a Kubernetes object that tells the API server about another Kubernetes object type. That sounds circular at first, but it is the same extension mechanism used by many mature platform projects. You create one cluster-scoped CRD named in `plural.group` form, and the API server starts serving a new REST endpoint under `/apis/<group>/<version>/<plural>`, complete with discovery, authorization, admission, validation, watch support, and standard `kubectl` behavior.

Think of the CRD as the registration desk, not the workload itself. Registering `databases.example.com` tells Kubernetes how to accept objects named `Database`, but it does not create a database engine, a disk, or a network endpoint. The CRD gives the cluster a new vocabulary word; a custom resource uses that vocabulary word; a controller may then translate that resource into lower-level resources.

Here is the compact CRD from the original module. It is intentionally small so the shape is visible before the later sections add validation details, discovery commands, and operator behavior. Notice that the CRD uses `apiextensions.k8s.io/v1`, declares `example.com` as its API group, serves one version named `v1`, and defines the names that users will type through `kubectl`.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.example.com    # plural.group format
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              engine:
                type: string
              size:
                type: string
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames:
    - db
```

Once that CRD is established, a user can submit a custom resource. The custom resource has the group and version from the CRD in `apiVersion`, the `kind` from `spec.names.kind`, normal Kubernetes metadata, and a `spec` payload whose shape should match the schema. From the API server's point of view, this object is not a second-class note tucked into a ConfigMap; it is an API object with the same storage, watch, RBAC, and admission pipeline that built-in resources use.

```yaml
apiVersion: example.com/v1
kind: Database
metadata:
  name: my-database
spec:
  engine: postgres
  size: large
```

Pause and predict: you see `kubectl get certificates` being used in a cluster. Is `Certificate` a built-in Kubernetes resource, a CRD-backed custom resource, or something else? Before running a command, decide what evidence would prove the answer, because CKAD tasks often reward fast discovery more than prior knowledge of every add-on project.

The quickest proof is API discovery. `kubectl api-resources` lists both built-in resources and CRD-backed resources, including their API groups, whether they are namespaced, and any short names. `kubectl get crd` lists only the CRD definitions themselves. If `certificates.cert-manager.io` exists as a CRD and `kubectl api-resources` shows `certificates` in the `cert-manager.io` group, you know the resource is provided by an extension rather than by the Kubernetes core API.

The endpoint view explains why normal commands work after a CRD is accepted. Kubernetes already serves built-in endpoints such as Pods, Services, and Deployments. A CRD adds another endpoint under the aggregated API path, and `kubectl` discovers that endpoint rather than carrying a hard-coded list of every possible resource kind in the ecosystem.

```text
┌─────────────────────────────────────────────────────────────┐
│                 CRD Creates New API Endpoint                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Before CRD:                                                │
│  ┌─────────────────────────────────┐                       │
│  │ /api/v1/pods                    │                       │
│  │ /api/v1/services                │                       │
│  │ /apis/apps/v1/deployments       │                       │
│  └─────────────────────────────────┘                       │
│                                                             │
│  After CRD (group: example.com, plural: databases):        │
│  ┌─────────────────────────────────┐                       │
│  │ /api/v1/pods                    │                       │
│  │ /api/v1/services                │                       │
│  │ /apis/apps/v1/deployments       │                       │
│  │ /apis/example.com/v1/databases  │  ← NEW!               │
│  └─────────────────────────────────┘                       │
│                                                             │
│  kubectl commands now work:                                │
│  $ kubectl get databases                                   │
│  $ kubectl describe database my-db                         │
│  $ kubectl delete database my-db                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The important boundary is that CRDs extend the API, not the scheduler, not the kubelet, and not application code by themselves. If you create a `Database` custom resource and no controller watches that type, the API server will happily store the object and do nothing more. That is not a Kubernetes failure; it is a missing reconciliation loop, and diagnosing that boundary is one of the main operational skills in this module.

## Anatomy of a CRD Schema

A useful CRD is more than a name. It defines how people refer to the resource, where resource instances live, which versions are served, which version is used for storage, and which field shapes the API server accepts. Each piece changes the behavior a user sees through `kubectl`, so learning the manifest is really learning the API contract.

The `names` block is the user-facing vocabulary. The plural form is used in URLs and common list commands, the singular form is accepted by the CLI, the kind appears in YAML, and short names give interactive shortcuts when the author provides them. Short names are convenient, but they should not be used in scripts unless the team controls the CRD, because a short name can collide with another resource or be absent in a different cluster.

```yaml
names:
  plural: databases      # Used in URLs: /apis/example.com/v1/databases
  singular: database     # Used in CLI: kubectl get database
  kind: Database         # Used in YAML: kind: Database
  shortNames:
  - db                   # Shortcuts: kubectl get db
```

Scope decides whether each custom resource belongs to a namespace or to the whole cluster. A namespaced resource behaves like a ConfigMap or Secret: `kubectl get databases -n production` and `kubectl get databases -n staging` can show different objects. A cluster-scoped resource behaves more like a Node or StorageClass: there is one shared namespace-free collection, and RBAC needs to be designed with cluster-level access in mind.

```yaml
scope: Namespaced    # Resources exist in namespaces
# or
scope: Cluster       # Resources are cluster-wide
```

Scope is not a stylistic choice. Use namespaced scope when the object represents application-owned intent, tenant-owned configuration, or something that should follow namespace lifecycle and namespace RBAC boundaries. Use cluster scope when the object represents infrastructure shared across namespaces, such as a cluster-wide policy, gateway class, or storage backend definition. If you choose cluster scope for tenant intent, you make isolation harder; if you choose namespace scope for shared infrastructure, you may force duplicate objects and unclear ownership.

Versions let a CRD evolve without breaking every client at once. A version with `served: true` can be requested through the API, while the single version with `storage: true` is the version written to etcd. Production CRDs often begin with alpha or beta versions, later add a stable version, and keep old versions served for a migration window while conversion logic or compatible schemas protect existing resources.

```yaml
versions:
- name: v1
  served: true       # API server serves this version
  storage: true      # Store in etcd using this version (only one can be true)
```

For CKAD work, you usually need to read these flags rather than design a multi-version conversion plan. If a manifest uses `apiVersion: example.com/v1beta1` but the CRD serves only `v1`, the resource is rejected before any controller sees it. If two versions are served but only one is storage, the API server can accept both versions while persisting the storage version internally.

Versioning becomes important the moment a CRD leaves a private lab and becomes a contract for other teams. A field that looks harmless today can become hard to remove once GitOps repositories, Helm charts, scripts, and controllers depend on it. For that reason, good CRD authors treat early versions as experimental, publish stable versions only when the schema has settled, and avoid changing field meanings under the same version name.

The `served` and `storage` flags also explain a subtle migration behavior. Serving an old version lets existing manifests keep applying while users move to a newer API version. Storing only one version keeps etcd from becoming a mixed archive of historical shapes. In advanced CRDs, conversion webhooks can translate between versions, but CKAD-level troubleshooting still begins with reading which versions are served and which one is storage.

Schema validation is the part that prevents bad intent from entering the cluster. With `openAPIV3Schema`, the CRD author declares types, required fields, enumerations, defaults, numeric bounds, object structures, and other constraints. The API server applies these constraints during admission, so a wrong value can be rejected immediately instead of turning into a silent operator failure later.

```yaml
schema:
  openAPIV3Schema:
    type: object
    required: ["spec"]
    properties:
      spec:
        type: object
        required: ["engine"]
        properties:
          engine:
            type: string
            enum: ["postgres", "mysql", "mongodb"]
          size:
            type: string
            default: "small"
```

This schema says the custom resource must include `spec`, that `spec.engine` is required, that the engine must be one of three strings, and that `spec.size` has a default when omitted. The schema does not know how to run PostgreSQL or MongoDB. It only protects the API boundary so the stored object has a predictable shape for users, admission controllers, controllers, documentation tools, and `kubectl explain`.

Kubernetes requires modern CRD schemas to be structural, which means the schema must be regular enough for pruning, defaulting, validation, and server-side apply to behave predictably. In practice, this pushes CRD authors toward explicit object types and field definitions rather than arbitrary nested blobs. That discipline helps users because a rejected manifest usually names the exact field path that failed, and it helps controllers because the watch stream contains objects with expected shapes.

Unknown fields deserve special attention. If a CRD schema does not preserve unknown fields and a user submits a field the schema does not recognize, Kubernetes can prune that field before storing the object. If the schema is too loose, the field might be stored but ignored by the controller. Either result can surprise a learner, so the safe debugging habit is to apply the manifest, then read back the stored object with `kubectl get <resource> <name> -o yaml` to see what the API server kept.

Before running this, what output do you expect if `engine` is set to `redis`? The answer matters because it tells you which component is enforcing the contract. In this example, the API server rejects the object during validation, which means the database operator never receives the invalid custom resource through its watch stream.

```yaml
apiVersion: example.com/v1
kind: Database
metadata:
  name: my-database
spec:
  engine: redis
  size: large
```

The rejection looks like a normal Kubernetes validation error. The wording varies across Kubernetes releases and clients, but the cause is consistent: the CRD's schema did not allow the submitted value. When you see this class of error, inspect the CRD schema before debugging controller logs, because the controller did not get a chance to act on the rejected object.

```bash
$ kubectl apply -f bad-db.yaml
The Database "my-database" is invalid: spec.engine: Unsupported value: "redis": supported values: "postgres", "mysql", "mongodb"
```

Strict schemas also protect against misspellings. Without a schema that requires `engine`, a user might submit `engin: postgres`, the API server might store the object, and the operator might ignore it or record a vague status condition. A good CRD fails early with a precise error, which is friendlier for application teams and safer for automation.

Defaults are useful, but they should not hide important choices. A default like `size: small` can make simple examples easier, while a default for a destructive retention policy could create unexpected data loss. When you inspect a CRD, read defaults as part of the API behavior, not as documentation decoration. A custom resource read back from the API may include fields the user did not write because the API server defaulted them during admission.

The `spec` and `status` split is another part of the schema contract. Users write desired state in `spec`; controllers write observed state in `status` when the CRD enables a status subresource. That separation prevents a normal user update from accidentally overwriting controller observations, and it makes troubleshooting clearer because you can compare what the user asked for with what the operator has actually seen or achieved.

## Working With Custom Resources

CRDs are discovered and operated through ordinary Kubernetes commands. That is one of their best design qualities: once the API server knows the new resource, users do not need a special client just to list, describe, patch, delete, or explain it. The same mental model you use for Deployments applies, with one added step: identify the API group, exact resource name, scope, and schema before assuming what a command should show.

Start with the definitions. `kubectl get crd` lists cluster-scoped CRD objects, not the custom resources created from them. `kubectl describe crd` is useful because it shows versions, names, accepted names, conditions, and sometimes schema details. `kubectl get crd <name> -o yaml` is the deepest view when you need to inspect validation, status subresources, printer columns, or version flags.

```bash
# List all CRDs
kubectl get crd

# Describe a CRD
kubectl describe crd certificates.cert-manager.io

# Get CRD YAML
kubectl get crd mycrd.example.com -o yaml
```

After the CRD exists, use the resource names defined by the CRD. Plural names are common for listing, singular names are readable for a single object, and short names are convenient if they are present. For scripts and learning material, the full `kubectl` binary name is safer than a shell alias, because aliases do not expand in non-interactive shells and copied examples should run as written.

```bash
# List custom resources (once CRD exists)
kubectl get databases
kubectl get db                    # Using shortName

# Describe a CR
kubectl describe database my-database

# Get CR YAML
kubectl get database my-database -o yaml

# Delete a CR
kubectl delete database my-database
```

The most common discovery mistake is mixing the CRD name with the resource name. `databases.example.com` is the CRD object name, while `databases`, `database`, and possibly `db` are names for the custom resource endpoint. If `kubectl get database` fails, do not guess the plural; run `kubectl api-resources | grep example.com` or inspect `spec.names` in the CRD.

```bash
# List CRDs
kubectl get crd

# View CRD details
kubectl describe crd NAME

# Work with custom resources
kubectl get <resource>
kubectl describe <resource> NAME
kubectl delete <resource> NAME

# Get API resources (includes CRDs)
kubectl api-resources | grep example.com

# Check if CRD exists
kubectl get crd myresource.example.com
```

`kubectl explain` works for CRDs when the CRD publishes a structural schema. That makes it a fast exam tool because it can tell you accepted field paths without opening documentation in another window. If `kubectl explain database.spec` returns useful field information, the CRD author has exposed enough schema for the client to navigate the custom object shape.

```bash
# Works for installed CRDs too, after discovery refreshes
until kubectl explain database >/dev/null 2>&1; do sleep 1; done
kubectl explain database

until kubectl explain database.spec >/dev/null 2>&1; do sleep 1; done
kubectl explain database.spec

until kubectl explain certificate.spec.secretName >/dev/null 2>&1; do sleep 1; done
kubectl explain certificate.spec.secretName
```

Some common CRDs are worth recognizing because they appear in many clusters. cert-manager creates certificate-related resources, the Prometheus Operator creates monitoring resources, and Gateway API provides gateway and route resources. Recognition helps you move faster, but the reliable method is still discovery through the API server, not memory.

```bash
kubectl get crd | grep cert-manager
# certificates.cert-manager.io
# clusterissuers.cert-manager.io
# issuers.cert-manager.io

# Create a Certificate
kubectl get certificates
kubectl describe certificate my-cert
```

```bash
kubectl get crd | grep monitoring
# servicemonitors.monitoring.coreos.com
# prometheusrules.monitoring.coreos.com
```

```bash
kubectl get crd | grep gateway
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
```

Which approach would you choose here and why: read the CRD YAML first, run `kubectl explain`, or inspect operator logs? If the question is "what fields can I set," start with schema and explain. If the question is "why did my valid object not create child resources," move to status, events, and controller logs. That order prevents you from debugging the wrong layer.

## Operators and Reconciliation

An Operator is usually described as "CRD plus controller," but the phrase is only useful if you keep the two responsibilities separate. The CRD defines the shape of desired state. The controller watches custom resources, compares desired state with actual cluster state, creates or updates supporting objects, records status, and repeats whenever something changes.

```text
┌─────────────────────────────────────────────────────────────┐
│                    Operator Pattern                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User Creates Custom Resource                            │
│  ┌─────────────────────────────────┐                       │
│  │ apiVersion: example.com/v1      │                       │
│  │ kind: Database                  │                       │
│  │ spec:                           │                       │
│  │   engine: postgres              │                       │
│  └─────────────────────────────────┘                       │
│                    │                                        │
│                    ▼                                        │
│  2. Controller Watches for Database CRs                    │
│  ┌─────────────────────────────────┐                       │
│  │ Operator Pod                    │                       │
│  │ - Sees new Database CR          │                       │
│  │ - Creates StatefulSet           │                       │
│  │ - Creates Service               │                       │
│  │ - Creates Secret (password)     │                       │
│  │ - Updates CR status             │                       │
│  └─────────────────────────────────┘                       │
│                    │                                        │
│                    ▼                                        │
│  3. Actual Resources Created                               │
│  ┌─────────────────────────────────┐                       │
│  │ StatefulSet: my-database        │                       │
│  │ Service: my-database            │                       │
│  │ Secret: my-database-creds       │                       │
│  └─────────────────────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The diagram preserves the original database example because it shows the operational boundary clearly. The user creates one custom resource. The controller sees that object and creates a StatefulSet, a Service, a Secret, and often other resources such as PersistentVolumeClaims, backup jobs, PodDisruptionBudgets, or monitoring rules. The custom resource is the stable interface; the generated resources are implementation details managed by the operator.

That split is powerful because it lets domain experts encode operational knowledge once. Instead of teaching every application team how to set every PostgreSQL flag, the platform team publishes a `Database` API with fields such as `engine`, `size`, `backupPolicy`, and `version`. The operator can translate those fields into safe Kubernetes primitives, enforce naming conventions, rotate credentials, and update status conditions that users can inspect.

| Benefit | Example |
|---------|---------|
| Abstraction | Create `Database`, operator handles StatefulSet, PVC, etc. |
| Automation | Operator handles backups, failover, scaling |
| Domain expertise | Operator knows how to properly configure Postgres |
| Day 2 operations | Upgrades, restores, monitoring built-in |

The table is useful, but it hides an important tradeoff. Operators reduce repeated manual work only when the controller is actively maintained, observable, and compatible with the cluster version. A neglected operator can become a fragile dependency because users keep submitting custom resources while the reconciliation logic lags behind API changes, image changes, or operational requirements.

Status conditions are the operator's public progress report. A mature controller does not force users to infer everything from child resources or logs; it updates fields such as observed generation, readiness, reason, message, and last transition time. When a custom resource has useful conditions, the fastest troubleshooting command is often `kubectl describe <resource> <name>` because it shows whether the controller accepted the latest desired state and what it is waiting for.

Observed generation is especially helpful because it connects a user's latest edit to the controller's latest reconciliation. The metadata generation increments when `spec` changes, and a controller can copy that value into status after processing the change. If metadata generation is newer than the observed generation, the controller may not have reconciled the latest version yet. That distinction is more precise than simply asking whether a child Pod exists.

Finalizers are another operator mechanism that CRD users encounter during deletion. A controller can add a finalizer string to a custom resource to delay deletion while it cleans up external systems or child resources. If the controller is gone or broken, the custom resource may sit in a terminating state because Kubernetes is waiting for the finalizer to be removed. That is a controller-lifecycle problem, not a schema-validation problem.

Owner references connect generated child resources back to the custom resource when the owner and child are in compatible scopes. They help Kubernetes garbage collection remove child resources after the owner is deleted, but they are not a substitute for operator logic. A database operator might still need finalizers because it manages external backups, cloud resources, or ordered shutdown steps that Kubernetes garbage collection cannot understand.

RBAC is part of reconciliation too. A controller can watch `Database` objects successfully but fail to create StatefulSets or Secrets if its service account lacks permissions. In that case the custom resource exists, the operator pod runs, and the schema is valid, yet reconciliation still fails. Status conditions and events should point toward authorization errors, which is why reading the custom resource before tailing logs is a practical habit.

Additional printer columns can make CRDs feel like built-in resources by showing selected fields in `kubectl get` output. For example, a `Database` CRD might print engine, size, ready status, and age. These columns do not change the stored object, but they improve operational scanning and can reveal whether a controller is writing status. If a CRD lacks printer columns, use `-o yaml` or JSONPath instead of assuming the resource has no useful state.

Stop and think: a CRD for `Database` exists in the cluster, and you create a `Database` custom resource, but no actual database gets provisioned. What is missing, and which command would you run before opening the operator logs? A good first answer is to describe the custom resource and inspect its events and status, because those fields often show whether the controller has seen the object at all.

The controller boundary also explains why deletion behavior deserves caution. Deleting a custom resource should trigger the operator's cleanup logic if the operator uses finalizers. Deleting the CRD itself is much broader: the API definition is removed, and all custom resources of that type can be removed as well. Treat CRD deletion as an administrative change, not as a normal application cleanup command.

A well-designed operator makes this boundary visible instead of mysterious. It documents which fields users own, which child resources it owns, which status conditions it writes, and what happens during deletion. That documentation is not just for platform engineers. CKAD users benefit because the same clues show up in `kubectl describe`, YAML output, events, and RBAC failures during ordinary troubleshooting.

## Debugging and Discovery Workflow

When a CRD-backed workflow fails, resist the urge to jump straight to controller logs. The API server and the controller fail in different ways, and the error location tells you which evidence matters. A validation failure means the API server rejected the object. A successful apply followed by no child resources points toward reconciliation. A command that cannot find the resource may be a naming, group, version, or scope problem.

The first branch is discovery. Confirm that the CRD exists, that it is established, and that the resource appears in API discovery. CRDs have status conditions, and an unestablished CRD may not serve the endpoint yet. In automated examples, waiting for the `Established` condition avoids a race where the next command runs before the API server is ready to accept custom resources.

The second branch is schema. If `kubectl apply` fails with a validation message, inspect `spec.versions[*].schema.openAPIV3Schema`. Look for required fields, enum values, minimums, type mismatches, and nested object shapes. Remember that CRD validation happens before the controller sees the object, so controller logs are not the first evidence for schema rejection.

The third branch is scope and namespace. A namespaced CRD can have one `my-database` object in `dev` and another in `production`; a cluster-scoped CRD cannot. If `kubectl get databases` shows nothing, add `-A` or the expected namespace, then compare `kubectl api-resources` output to see whether the resource is namespaced. This single check prevents many false assumptions about missing resources.

The last branch is reconciliation. If the custom resource is accepted and visible, describe it, inspect its `status` field, check events, then inspect the operator deployment, pods, RBAC, and logs. Many operators record conditions such as `Ready`, `Reconciling`, or `Error` directly on the custom resource, and those status fields are usually more focused than scrolling through every controller log line.

Events are short-lived but valuable. A controller may emit an event when it cannot create a child resource, when it rejects a value that passed basic schema validation, or when it is waiting for an external dependency. Because events are namespaced for namespaced resources, query the same namespace as the custom resource. If the resource is cluster-scoped, expect the event pattern to vary by controller implementation.

Managed fields can help when server-side apply or multiple automation systems are involved. They show which field manager last claimed ownership of particular fields, which can explain why an update conflicts or why a field keeps reverting. You do not need to memorize the full managed-fields format for CKAD, but knowing that it exists helps you distinguish a validation problem from a field-ownership or automation-overwrite problem.

Discovery cache staleness can create confusing moments during fast CRD creation and deletion. `kubectl` caches discovery data locally, and the API server also needs a short moment to establish a new endpoint. Waiting for the CRD condition and rerunning discovery commands usually resolves the race. In scripts, use `kubectl wait --for condition=established` so the next command does not depend on timing luck.

RBAC errors should be read literally. A user may have permission to create custom resources in a namespace but not permission to list CRDs, or an operator may have permission to watch the custom resource but not to create the child resources it needs. These are different subjects and verbs. `kubectl auth can-i` is often the right next command when the error message says forbidden rather than invalid.

Deletion debugging has its own order. If a custom resource stays terminating, inspect metadata finalizers, then check whether the controller that owns the finalizer is running. Removing a finalizer manually can unblock a lab, but it can also skip cleanup that the operator was supposed to perform. In real environments, finalizer removal should be a deliberate recovery action with a clear understanding of what cleanup is being bypassed.

Schema and controller validation can both exist, and they fail at different times. The API server catches structural mistakes such as wrong types, missing required fields, and enum violations. A controller may still reject a semantically valid object because the requested database version is unavailable, a referenced Secret is missing, or an external quota is exhausted. Good troubleshooting asks which layer had enough information to make the decision.

This diagnostic order is also a CKAD time saver. The exam rewards precise use of `kubectl`, and CRDs can look unfamiliar under pressure. If you separate "is the API endpoint present," "was the object accepted," "is the object in the namespace I queried," and "is a controller reconciling it," most CRD problems collapse into a small set of repeatable commands.

Exercise scenario: a teammate gives you a `KafkaTopic` manifest and says the operator should create the topic automatically. `kubectl apply` rejects `spec.partitions: 0` with a minimum-value error. The correct fix is not to restart the Kafka operator; it is to either submit a value accepted by the CRD schema or ask the CRD owner to change the schema if `0` is supposed to mean "operator decides."

## Worked Example: Website CRD

This worked example keeps the original module's `Website` CRD because it is small enough to inspect in one sitting. The point is not to build a website operator; there is no controller in this exercise. The point is to see the API server accept a new resource type, store custom resources, expose the resource through discovery, support `kubectl explain`, and enforce the boundary between stored intent and automated action.

First create the CRD and wait until the API endpoint is established. The wait command is not decorative. Without it, a fast terminal can submit the first custom resource before discovery catches up, producing a confusing "no matches for kind" error even though the CRD was just applied successfully.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.example.com
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              domain:
                type: string
              replicas:
                type: integer
  scope: Namespaced
  names:
    plural: websites
    singular: website
    kind: Website
    shortNames:
    - ws
EOF

# Verify CRD created and API endpoint is established
kubectl wait --for condition=established --timeout=60s crd/websites.example.com
kubectl get crd websites.example.com
```

Now create two custom resources. They will be stored by the API server because the CRD exists and the `spec` fields match the schema types. No Deployment, Service, or Ingress appears, because this example deliberately has no controller watching `Website` objects. That absence is useful: it forces you to see what a CRD alone does and does not do.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: example.com/v1
kind: Website
metadata:
  name: my-blog
spec:
  domain: blog.example.com
  replicas: 3
---
apiVersion: example.com/v1
kind: Website
metadata:
  name: my-shop
spec:
  domain: shop.example.com
  replicas: 5
EOF

# List using different names
kubectl get websites
kubectl get website
kubectl get ws
```

Inspect one object and patch it. The patch command uses `--type=merge` because CRDs do not support strategic merge patch in the same way built-in Kubernetes types do. Strategic merge relies on built-in type metadata that custom resources do not have, so explicit merge patch is a safer habit when automating custom resource updates.

```bash
# Describe
kubectl describe website my-blog

# Get YAML
kubectl get ws my-blog -o yaml

# Edit (using patch for non-interactive automation)
# Rationale: CRDs do not support strategic merge patch (the default), so we must explicitly use --type=merge
kubectl patch website my-blog --type=merge -p '{"spec":{"replicas":2}}'
```

Finally, confirm discovery and schema visibility. `kubectl api-resources` shows the new resource group, namespaced status, kind, and short names. The safest discovery habit is to wait for the CRD to become established, then retry `kubectl explain` until discovery can resolve the custom resource. `kubectl explain` reads the published schema and helps you navigate the custom object fields without leaving the terminal.

```bash
# Check API resources
kubectl api-resources | grep example.com

# Use explain
until kubectl explain website >/dev/null 2>&1; do sleep 1; done
kubectl explain website
```

Clean up the custom resources before removing the CRD. This order mirrors safe operational practice: remove instances first, verify what remains, and only then remove the API definition when you are intentionally decommissioning that resource type.

```bash
kubectl delete website my-blog my-shop
kubectl delete crd websites.example.com
```

The example ends at the cleanup because it has proven the full API behavior: definition, establishment, custom resource creation, listing through plural and short names, description, YAML retrieval, merge patch, discovery, explanation, and deletion. A real operator would add reconciliation after the custom resources exist, but the API mechanics are the same.

## Patterns & Anti-Patterns

Use CRDs when you need a durable Kubernetes API for domain-specific desired state. They work best when users should declare intent and a controller should reconcile that intent repeatedly. They are weaker when you only need one application setting, a short-lived script input, or a value that does not benefit from Kubernetes API semantics such as RBAC, watch, validation, ownership, and status.

| Pattern | When to Use It | Why It Works |
|---------|----------------|--------------|
| Schema-first CRD | Users or automation submit custom resources directly | Validation catches bad intent before reconciliation and gives `kubectl explain` useful structure. |
| Namespaced tenant resource | Application teams own separate instances in separate namespaces | Namespace RBAC, quotas, and lifecycle boundaries align with the resource ownership model. |
| Controller-owned status | The operator needs to report readiness, errors, or observed state | Status separates desired state in `spec` from observed state, making troubleshooting faster. |
| Stable names with optional short names | Humans use the resource interactively, but scripts must be portable | Full names remain predictable while short names improve interactive ergonomics. |

Anti-patterns usually come from using CRDs as either too much or too little. Too much means every small configuration value becomes a new API type, creating documentation, RBAC, versioning, and migration work for little benefit. Too little means the CRD accepts unstructured blobs, so the API server cannot protect users and the operator becomes responsible for every validation error after the fact.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| CRD without a controller when action is expected | Users create objects and wait for child resources that never appear. | Install or build a controller, or document clearly that the CRD is storage-only. |
| Loose schema with arbitrary fields | Misspellings and wrong types are accepted, then fail later in controller logic. | Define a structural OpenAPI v3 schema with required fields, enums, bounds, and defaults. |
| Cluster-scoped resource for tenant-owned intent | Namespace isolation and delegated RBAC become awkward or unsafe. | Use namespaced scope unless the object truly represents shared cluster infrastructure. |
| Deleting CRDs as cleanup | All custom resources of that type may be removed across the cluster. | Delete instances intentionally, back them up when needed, and restrict CRD deletion with RBAC. |

The scaling consideration is operational ownership. A CRD is an API promise, so changing it affects every manifest, GitOps pipeline, user script, and controller that depends on it. Before introducing one, decide who owns versioning, documentation, upgrade testing, backup and restore, RBAC examples, and failure-mode support.

## Decision Framework

The decision to create or use a CRD should start with the problem's lifecycle. If the data is static application configuration read by one workload, a ConfigMap may be enough. If the desired state should be validated by the API server, watched by a controller, exposed through RBAC, and reported through status, a CRD is a stronger fit. If the behavior maps cleanly to a built-in Kubernetes API, use the built-in API instead of inventing a parallel abstraction.

```text
Need to model new Kubernetes-facing desired state?
  |
  +-- No --> Use a built-in resource, ConfigMap, Secret, or application config.
  |
  +-- Yes
       |
       +-- Does Kubernetes already provide the API shape?
       |      |
       |      +-- Yes --> Use the built-in API and avoid duplicate abstractions.
       |      |
       |      +-- No
       |
       +-- Should the API server validate and store the object?
       |      |
       |      +-- No --> Use a simpler configuration or external service API.
       |      |
       |      +-- Yes
       |
       +-- Does something need to reconcile the object continuously?
              |
              +-- No --> CRD can be storage/discovery only, but document that clearly.
              |
              +-- Yes --> CRD plus controller/operator is the right pattern.
```

Use the matrix when you are reviewing another team's design. It keeps the conversation concrete by comparing lifecycle, validation, ownership, and operational behavior rather than arguing about whether CRDs are fashionable. The best choice is the one whose failure modes your team is prepared to own.

| Choice | Fits Best When | Avoid When |
|--------|----------------|------------|
| Built-in Kubernetes API | Deployments, Services, Jobs, Ingress-like routing, or standard workload needs already model the problem | You need domain fields and status that built-ins cannot express cleanly. |
| ConfigMap or Secret | A workload only needs key-value configuration or credentials | Users need validation, discovery, status, or controller-driven lifecycle management. |
| CRD without controller | The cluster needs typed storage, validation, and discovery for custom intent | Users expect the object to create or repair real infrastructure automatically. |
| CRD plus Operator | Desired state must be reconciled into lower-level resources over time | The team cannot maintain controller logic, RBAC, upgrades, and observability. |

For CKAD tasks, the framework usually reduces to a smaller checklist. Confirm the CRD exists, confirm the resource name and scope, apply a valid custom resource, inspect the object, and determine whether an operator should act on it. If action is expected but absent, debug the controller side; if acceptance fails, debug the schema and manifest side.

The same framework helps when you inherit a cluster with many extensions already installed. Begin by grouping CRDs by API group, because the group name usually reveals the owning project or platform team. Then sample one custom resource from each important group and compare its `spec`, `status`, events, and generated child resources. That exercise turns a long unfamiliar CRD list into a map of which APIs are only declarations, which APIs are reconciled, and which teams own the operational behavior.

When you are designing a new abstraction, write one example custom resource before writing the CRD. If the example reads like a clear request a user would naturally make, the CRD may be justified. If the example is just a bag of low-level knobs copied from Deployments, Services, and ConfigMaps, the abstraction probably leaks implementation details. A good CRD makes the user's desired outcome easier to state while keeping enough detail for safe reconciliation.

## Did You Know?

- **CRDs are themselves Kubernetes resources.** The `apiextensions.k8s.io/v1` API group defines how to register custom resource types, so the extension mechanism is managed through the same API style learners already use for other cluster objects.
- **Deleting a CRD can delete all of its custom resources.** `kubectl delete crd databases.example.com` is not just deleting a schema document; it removes the API definition and can remove every stored `Database` object served by that definition.
- **A CRD can serve multiple versions while storing only one.** This lets API authors support migration windows such as `v1alpha1`, `v1beta1`, and `v1` while keeping one storage representation in etcd.
- **Many widely used Kubernetes projects are API extensions.** cert-manager, the Prometheus Operator, Gateway API implementations, Argo CD, and service mesh projects commonly rely on CRDs to expose domain-specific resources.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Confusing the CRD with a custom resource | The names look related, and both are manipulated with `kubectl`. | Treat the CRD as the API definition and the custom resource as one instance of that API. |
| Deleting a CRD as routine cleanup | The command looks like removing one object, but it removes the resource type. | Delete custom resources first, back up important instances, and restrict CRD deletion through RBAC. |
| Querying the wrong name | The CRD name, plural, singular, kind, and short name are different entry points. | Use `kubectl api-resources` and `spec.names` to choose the correct command form. |
| Expecting a CRD to perform work by itself | The API server stores objects but does not run domain automation. | Install or debug the controller/operator that watches the custom resource type. |
| Ignoring namespace scope | Namespaced resources disappear from the default view when they live elsewhere. | Check `kubectl api-resources` for the namespaced column and query with `-n` or `-A`. |
| Debugging controller logs before validation | API-server schema rejection happens before the controller receives the object. | Read the validation error, inspect `openAPIV3Schema`, and fix the manifest or schema. |
| Using loose schemas for important APIs | It feels faster during early development, but users can submit invalid intent. | Add required fields, types, enums, defaults, and bounds as soon as the API is shared. |

## Quiz

<details>
<summary>Question 1: Your team installs a `Database` CRD and creates a custom resource with `spec.engine: postgres`. No StatefulSet, Service, or PVC appears, but `kubectl get database my-database` succeeds. What should you check next?</summary>

The custom resource was accepted by the API server, so the next question is whether a controller is reconciling it. Describe the custom resource and inspect status and events, then check whether the database operator deployment and pods are running with the right RBAC. A CRD alone only stores and validates the object; it does not create child resources. Restarting the API server or rewriting the schema would not address the missing reconciliation loop.
</details>

<details>
<summary>Question 2: A colleague accidentally runs `kubectl delete crd databases.example.com` and several namespaces lose their `Database` objects. Why did this happen, and what control would reduce the risk?</summary>

The CRD is the API definition for every custom resource of that type, so deleting it can remove the stored resources served by that definition. This is different from deleting one `Database` instance in one namespace. Restrict CRD deletion with RBAC, back up important custom resources, and require an explicit change process for cluster-scoped API definitions. Deleting individual custom resources should be the normal cleanup path.
</details>

<details>
<summary>Question 3: You receive `The KafkaTopic "orders-topic" is invalid: spec.partitions: Invalid value: 0: spec.partitions in body should be greater than or equal to 1`. The operator owner says zero means automatic sizing. Where is the mismatch?</summary>

The mismatch is between the submitted custom resource and the CRD's OpenAPI schema. The API server rejected the object because the schema requires `spec.partitions` to be at least one, so the operator never saw the custom resource. Either the manifest must use a valid partition count, or the CRD owner must change the schema if zero is truly supported. Operator logs are secondary evidence here because admission failed first.
</details>

<details>
<summary>Question 4: A developer runs `kubectl get databases` in the `staging` namespace and sees no objects, while you know `my-database` exists in `production`. What should you explain?</summary>

If the CRD uses `scope: Namespaced`, each `Database` custom resource lives inside one namespace. The resource can exist in `production` and be invisible from `staging` unless the command uses `-n production` or `-A`. The CRD is not broken; the query scope is wrong. If the resource should be shared cluster-wide, that is a CRD design decision with different RBAC and ownership tradeoffs.
</details>

<details>
<summary>Question 5: You run `kubectl get database` and receive a resource-not-found style error, but the CRD `databases.example.com` exists. What discovery commands help you avoid guessing?</summary>

Run `kubectl api-resources | grep example.com` to see the actual resource names, group, kind, short names, and namespaced status. Then inspect `kubectl get crd databases.example.com -o yaml` if you need the exact `spec.names` block. The CRD object name is not always the command form you should use. Guessing pluralization wastes time and can hide a simple naming mismatch.
</details>

<details>
<summary>Question 6: You need to update `spec.replicas` on a custom resource from an automation script. Why is `kubectl patch --type=merge` safer than relying on the default patch behavior?</summary>

Custom resources do not support strategic merge patch the way built-in Kubernetes types do, because strategic merge relies on built-in type metadata. An explicit merge patch makes the patch type clear and portable for CRDs. Server-side apply can also be appropriate when you manage field ownership deliberately, but an unqualified default patch can surprise learners moving between built-in resources and custom resources.
</details>

<details>
<summary>Question 7: You are reviewing a proposal to model one application's static feature flags as a new cluster-scoped CRD plus operator. How would you evaluate that design?</summary>

Start by asking whether the problem needs Kubernetes API semantics: validation, discovery, RBAC, watch behavior, status, and reconciliation. Static feature flags for one application often fit better in a ConfigMap or the application's own configuration system. A cluster-scoped CRD plus operator adds versioning, RBAC, lifecycle, and controller maintenance responsibilities. It becomes a good design only if many teams need a shared declarative API and continuous reconciliation.
</details>

## Hands-On Exercise

In this lab you will create a CRD, create custom resources, inspect discovery output, patch a custom resource, and verify schema validation. The commands are designed for a disposable Kubernetes environment such as the linked Killercoda scenario, because the cleanup steps remove the custom API definitions after each drill. Read each solution only after you have tried the task or predicted the output.

### Setup

Confirm that `kubectl` can reach your cluster and that you are in a namespace where you are allowed to create namespaced resources. Creating CRDs is a cluster-scoped operation, so a locked-down production cluster may reject these examples even if normal workload commands work. A local kind cluster, a classroom cluster, or the module lab environment is the right place to practice.

### Task 1: Create and Inspect the Website CRD

- [ ] Apply the `websites.example.com` CRD and wait until it is established.
- [ ] Confirm that `kubectl api-resources` lists `websites` in the `example.com` group.
- [ ] Use `kubectl explain website.spec` to inspect the published schema.

<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.example.com
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              domain:
                type: string
              replicas:
                type: integer
  scope: Namespaced
  names:
    plural: websites
    singular: website
    kind: Website
    shortNames:
    - ws
EOF

kubectl wait --for condition=established --timeout=60s crd/websites.example.com
kubectl api-resources | grep example.com
until kubectl explain website.spec >/dev/null 2>&1; do sleep 1; done
kubectl explain website.spec
```
</details>

### Task 2: Create, List, and Patch Website Resources

- [ ] Create `my-blog` and `my-shop` Website custom resources.
- [ ] List the resources using plural, singular, and short-name command forms.
- [ ] Patch `my-blog` so `spec.replicas` becomes `2`, then inspect the YAML.

<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: example.com/v1
kind: Website
metadata:
  name: my-blog
spec:
  domain: blog.example.com
  replicas: 3
---
apiVersion: example.com/v1
kind: Website
metadata:
  name: my-shop
spec:
  domain: shop.example.com
  replicas: 5
EOF

kubectl get websites
kubectl get website
kubectl get ws
kubectl patch website my-blog --type=merge -p '{"spec":{"replicas":2}}'
kubectl get ws my-blog -o yaml
```
</details>

### Task 3: Practice Fast CRD Discovery

- [ ] List every CRD installed in the cluster and count them.
- [ ] Describe `certificates.cert-manager.io` if cert-manager is installed, otherwise describe the first available CRD.
- [ ] List CRD definitions with their groups, kinds, and scopes, then filter API resources for one known extension group.

<details>
<summary>Solution</summary>

```bash
# List all CRDs
kubectl get crd

# Count CRDs
kubectl get crd --no-headers | wc -l
```

```bash
# If cert-manager or similar is installed
kubectl describe crd certificates.cert-manager.io 2>/dev/null || echo "cert-manager not installed"

# Otherwise use any CRD
kubectl get crd -o name | head -1 | xargs kubectl describe
```

```bash
# List all API resources
kubectl api-resources

# Filter for a specific built-in API group
kubectl api-resources --api-group=networking.k8s.io

# Show only CRD definitions with CRD-specific metadata
kubectl get crd -o custom-columns=NAME:.metadata.name,GROUP:.spec.group,KIND:.spec.names.kind,SCOPE:.spec.scope

# Show resources from the extension group created earlier in the lab
kubectl api-resources --api-group=example.com
```
</details>

### Task 4: Create Small Drill CRDs

- [ ] Create `backups.drill.example.com`, verify the CRD exists, then delete it.
- [ ] Create `tasks.drill.example.com`, create one `Task`, describe it, then clean up.
- [ ] Create `configs.drill.example.com`, use `kubectl explain`, then remove the CRD.

<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backups.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              schedule:
                type: string
              retention:
                type: integer
  scope: Namespaced
  names:
    plural: backups
    singular: backup
    kind: Backup
    shortNames:
    - bk
EOF

kubectl get crd backups.drill.example.com
kubectl delete crd backups.drill.example.com
```

```bash
# First create CRD
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: tasks.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              priority:
                type: string
  scope: Namespaced
  names:
    plural: tasks
    singular: task
    kind: Task
EOF

# Verify CRD is established
kubectl wait --for condition=established --timeout=60s crd/tasks.drill.example.com

# Create CR
cat << 'EOF' | kubectl apply -f -
apiVersion: drill.example.com/v1
kind: Task
metadata:
  name: important-task
spec:
  priority: high
EOF

# Query
kubectl get tasks
kubectl describe task important-task
kubectl get task important-task -o yaml

# Cleanup
kubectl delete task important-task
kubectl delete crd tasks.drill.example.com
```

```bash
# Create a simple CRD
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: configs.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              key:
                type: string
              value:
                type: string
  scope: Namespaced
  names:
    plural: configs
    singular: config
    kind: Config
EOF

# Verify CRD is established
kubectl wait --for condition=established --timeout=60s crd/configs.drill.example.com

# Use explain
until kubectl explain config >/dev/null 2>&1; do sleep 1; done
kubectl explain config
until kubectl explain config.spec >/dev/null 2>&1; do sleep 1; done
kubectl explain config.spec

# Cleanup
kubectl delete crd configs.drill.example.com
```
</details>

### Task 5: Trigger and Fix Validation

- [ ] Create a `Cache` CRD that requires `spec.memoryLimit` to be an integer of at least `128`.
- [ ] Apply an invalid `Cache` with `"64"` as a string and observe the API-server validation error.
- [ ] Apply a valid `Cache`, confirm it exists, and delete the CRD.

<details>
<summary>Solution</summary>

```bash
# 1. Create a CRD with validation
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: caches.drill.example.com
spec:
  group: drill.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        required: ["spec"]
        properties:
          spec:
            type: object
            required: ["memoryLimit"]
            properties:
              memoryLimit:
                type: integer
                minimum: 128
  scope: Namespaced
  names:
    plural: caches
    singular: cache
    kind: Cache
EOF

# Verify CRD is established
kubectl wait --for condition=established --timeout=60s crd/caches.drill.example.com

# 2. Try to apply an invalid CR (memoryLimit is a string instead of an integer)
cat << 'EOF' | kubectl apply -f -
apiVersion: drill.example.com/v1
kind: Cache
metadata:
  name: bad-cache
spec:
  memoryLimit: "64"
EOF

# Notice the validation error from the API server!
# error: ValidationError(Cache.spec.memoryLimit): invalid type for drill.example.com/v1.Cache.spec.memoryLimit: got "string", expected "integer"

# 3. Fix the CR by providing a valid integer >= 128
cat << 'EOF' | kubectl apply -f -
apiVersion: drill.example.com/v1
kind: Cache
metadata:
  name: good-cache
spec:
  memoryLimit: 256
EOF

# 4. Verify it was created successfully
kubectl get cache good-cache

# 5. Cleanup
kubectl delete crd caches.drill.example.com
```
</details>

### Success Criteria

- [ ] You can explain the difference between a CRD and a custom resource without using the word "operator" as a shortcut.
- [ ] You can use `kubectl get crd`, `kubectl api-resources`, and `kubectl explain` to discover an unfamiliar CRD-backed API.
- [ ] You can identify whether a failure belongs to API-server validation, namespace scope, resource naming, or controller reconciliation.
- [ ] You can create and remove the drill CRDs without leaving custom resources behind.
- [ ] You can describe when a CRD is unnecessary because a ConfigMap, Secret, or built-in Kubernetes resource is simpler.

## Learner check

> The safest discovery habit is to wait for the CRD to become established, then retry `kubectl explain` until discovery can resolve the custom resource.

Before moving on, explain why the CRD's Established condition and client-side discovery refresh are related but separate readiness checks. Your answer should mention what the API server has accepted, what `kubectl explain` still needs to discover, and how a retry avoids a misleading failure immediately after CRD creation.

## Sources

- https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
- https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/
- https://kubernetes.io/docs/reference/kubernetes-api/extend-resources/custom-resource-definition-v1/
- https://kubernetes.io/docs/reference/using-api/api-concepts/
- https://kubernetes.io/docs/reference/using-api/server-side-apply/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_explain/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_api-resources/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/
- https://kubernetes.io/docs/concepts/architecture/controller/
- https://cert-manager.io/docs/concepts/certificate/
- https://gateway-api.sigs.k8s.io/docs/concepts/api-overview/
- https://prometheus-operator.dev/docs/getting-started/introduction/

## Next Module

[Part 4 Cumulative Quiz](../part4-cumulative-quiz/) - Test your mastery of environment, configuration, and security topics.
