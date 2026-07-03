---
title: "Module 7.12: Ansible Operator SDK Fundamentals"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.12-ansible-operator-sdk
sidebar:
  order: 13
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: ~90 minutes
>
> **Prerequisites**: [Module 7.4: Ansible for Infrastructure](../module-7.4-ansible/), Kubernetes custom resources from [K8s Extending Module 1.2: CRDs Advanced](/k8s/extending/module-1.2-crds-advanced/), controller fundamentals from [K8s Extending Module 1.3: Controllers and client-go](/k8s/extending/module-1.3-controllers-client-go/), `operator-sdk`, Ansible, `kubectl`, Docker, and access to a Kubernetes cluster

---

## Prerequisites

Before starting this module, you should be comfortable reading an Ansible role,
explaining why idempotent tasks are safer than shell scripts, and applying
ordinary Kubernetes resources with `kubectl`. Module 7.4 gives you the Ansible
side: playbooks, roles, collections, variables, and task result handling. The
Kubernetes Extending modules give you the control-plane side: custom resources,
the `spec` and `status` split, reconciliation, owner references, and why a
controller turns desired state into child objects.

You also need a local toolchain that can build and run a small operator. The
commands in this module assume `kind`, `kubectl`, Docker, `make`, `ansible`,
and `operator-sdk` are on your `PATH`. Operator SDK installation changes over
time, so use the official installation page for your platform; on macOS,
Homebrew is the simplest path, while Linux users commonly install the signed
release binary. Verify the tools before you begin so any later failure belongs
to the operator workflow rather than to a missing local dependency.

```bash
operator-sdk version
ansible --version
kubectl version --client=true
kind version
docker version --format '{{.Client.Version}}'
```

You do not need to know Go to complete this module. That is the point of the
Ansible Operator pattern. You do need to know enough Kubernetes to recognize
that an operator is not a batch job: it is a controller that keeps watching a
custom resource, rerunning automation when the desired state or managed
children change, and publishing observed state back to the API server.

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design** an Ansible Operator architecture that maps a `watches.yaml` entry
  to an Ansible role, Kubernetes custom resource, RBAC boundary, and
  reconciliation loop.
- **Implement** a minimum viable `DemoApp` operator with Operator SDK,
  `kubernetes.core.k8s` tasks, custom status updates, and a kind deployment
  path.
- **Diagnose** reconciliation failures by reading operator logs, CR status,
  RBAC denials, Ansible task output, and child-resource ownership signals.
- **Evaluate** when an Ansible Operator beats a Go Operator or Helm Operator
  for platform automation work.
- **Plan** a production readiness path for idempotency, status management,
  finalizers, image publishing, testing, and future advanced watch patterns.

## Why This Module Matters

Hypothetical scenario: a platform team already has a mature Ansible role that
creates a per-application Deployment, Service, ConfigMap, network policy, and a
few external configuration hooks. Application teams keep asking for a
self-service API: "I want to submit a small object to the cluster and let the
platform handle the rest." The platform engineers know Kubernetes well enough
to model the request as a custom resource, but they do not want the first
iteration to become a Go/Kubebuilder project with generated types, controller
runtime clients, cache predicates, and a month of new language conventions.

An Ansible Operator gives that team a middle path. Operator SDK still provides
the Kubernetes controller shell: manager process, watches, RBAC manifests, CRD
generation, container image, kustomize deployment, and optional OLM packaging.
Instead of writing the reconcile function in Go, the team maps a custom
resource to an Ansible role. When the resource changes, the operator runs the
role with CR fields as variables. The role uses the modern
`kubernetes.core.k8s` collection to create or patch child resources. The API
server remains the source of desired state, while Ansible remains the language
the platform team already knows.

This is not a shortcut around controller design. Ansible Operators still need
idempotent logic, clear ownership, safe status reporting, RBAC that matches the
managed resources, and a plan for deletion. The advantage is that the first
controller can be built from the team's existing operational vocabulary:
roles, variables, tasks, handlers, `changed_when`, `failed_when`, and rescue
blocks. This module establishes that vocabulary so later modules can go deep
on advanced `watches.yaml` patterns, AWX and Event-Driven Ansible integration,
Helm-versus-Ansible decisions, production hardening, and testing.

## War Story - The Rollout Role That Became a Controller

Hypothetical scenario: a platform group owned a configuration rollout job for
internal web services. Each service needed a Deployment, Service, standard
labels, a team-owned ConfigMap, and a sidecar toggle for environments that
required extra telemetry. The first version was a normal Ansible playbook run
from a release pipeline. It worked during scheduled changes, but it did not
respond when an application team edited replicas directly, deleted a Service
while debugging, or created a new environment outside the release window.

The team considered a Go Operator because the desired interface was clearly a
Kubernetes API: create a `DemoApp`-like object and let the platform reconcile
the underlying objects. The barrier was not ideology; it was delivery cost.
The team had strong Ansible habits, a tested role, and a short window to make
the workflow self-service. Rewriting the whole thing in Go would have created
new code paths before they had proven the API contract.

They chose an Ansible Operator for the first release. The winning pattern was
simple: keep the custom resource small, map it to one role, let
`kubernetes.core.k8s` apply complete object definitions, and update `.status`
with enough information for application teams to debug readiness without
reading operator logs. The team did not try to model every future toggle in
the first CRD. They shipped `image`, `replicas`, `port`, and a short set of
labels, then added fields only after real users needed them.

The footgun was periodic reconciliation. Someone set a very short
`reconcilePeriod` because it felt safer to check often. It was not safer. The
role was idempotent, but it still made API calls, produced Ansible artifacts,
and generated log volume on every run. A low period turned harmless drift
checks into controller noise. The fix was to rely on Kubernetes watch events
for ordinary changes, keep the periodic interval conservative, and make
explicit decisions about which dependent resources should trigger new runs.

The lesson is practical: Ansible Operators are strongest when they turn known,
idempotent operational procedures into Kubernetes-native reconciliation. They
are weakest when teams treat them as cron jobs in disguise or hide a complex
state machine inside YAML because they are avoiding a more appropriate Go
controller.

## Conceptual Model: Ansible Operator Architecture

An ordinary Kubernetes controller watches one or more object types, receives an
event, reads the desired state, compares it with observed state, and issues
API calls until the cluster moves closer to the desired state. A Go Operator
puts that logic in a reconcile function. A Helm Operator renders a chart with
values from the custom resource. An Ansible Operator runs a role or playbook
with variables derived from the custom resource.

```text
+--------------------------------------------------------------------+
|                    ANSIBLE OPERATOR MENTAL MODEL                   |
+--------------------------------------------------------------------+
|                                                                    |
|  Custom Resource                                                   |
|  apiVersion: app.example.com/v1                                    |
|  kind: DemoApp                                                     |
|  spec:                                                             |
|    replicas: 2                                                     |
|    image: nginx:1.27-alpine                                        |
|                                                                    |
|               watch event or periodic reconcile                    |
|                         |                                          |
|                         v                                          |
|  watches.yaml maps DemoApp to role demoapp                         |
|                         |                                          |
|                         v                                          |
|  Operator SDK manager starts ansible-runner                        |
|                         |                                          |
|                         v                                          |
|  Role variables include CR spec fields and metadata                |
|                         |                                          |
|                         v                                          |
|  kubernetes.core.k8s creates Deployment and Service                |
|                         |                                          |
|                         v                                          |
|  operator_sdk.util.k8s_status updates observed status              |
|                                                                    |
+--------------------------------------------------------------------+
```

The crucial file is `watches.yaml`. It tells the operator which group, version,
and kind should trigger which Ansible role or playbook. For a foundational
operator, one custom resource maps to one role. Later modules will explore
selectors, multiple watches, dependent watches, custom finalizers, and
collection roles, but the anchor idea stays the same: `watches.yaml` is the
bridge between the Kubernetes API and your Ansible content.

```yaml
---
- version: v1
  group: app.example.com
  kind: DemoApp
  role: demoapp
  manageStatus: false
```

This mapping means: when the controller sees an `app.example.com/v1` `DemoApp`,
run the `demoapp` Ansible role. `manageStatus: false` is deliberate in this
module because the role will update a small custom status block itself. If you
leave status management enabled, the Ansible Operator can publish generic
Ansible run information for you. That default is useful for scaffolding, but
production APIs usually deserve status fields that communicate application
state rather than raw automation internals.

The reconcile loop looks familiar if you already write Ansible. Instead of
"run this role against host group webservers," the operator effectively says
"run this role for this custom resource instance." The inventory is not a
fleet of servers. The target is the Kubernetes API, accessed through the
operator process and the service account mounted into the controller Pod. The
role receives variables from `.spec`, plus metadata about the CR instance, and
then uses the Kubernetes collection to converge resources.

```text
+----------------------+        +------------------------------------+
| Ansible term         |        | Operator term                      |
+----------------------+--------+------------------------------------+
| Role                 |        | Reconcile implementation           |
| Task                 |        | One step toward desired state       |
| Variable             |        | CR spec field or derived value      |
| Idempotent module    |        | Safe repeated API operation         |
| Task failure         |        | Failed reconcile                    |
| Registered result    |        | Observed state evidence             |
| changed_when         |        | Signal whether work actually moved  |
| rescue block         |        | Controlled error handling           |
| k8s_status module    |        | Custom resource status update       |
+----------------------+--------+------------------------------------+
```

Operator SDK calls your role when a watched custom resource is created,
updated, or deleted, and it can also rerun periodically according to the
`reconcilePeriod` option. It may also reconcile when owned dependent resources
change, depending on the watch settings. The healthy default mental model is
event-driven first, conservative periodic resync second. A controller should
react promptly to meaningful Kubernetes events without turning every resource
into a high-frequency polling loop.

`spec` and `status` have different jobs. The `spec` is the user's desired
state: image, replica count, port, feature toggles, or whatever contract your
CRD exposes. The `status` is the operator's observed state: whether the child
Deployment is ready, which Service was created, what phase the operator last
reported, and which error is currently blocking convergence. Users should edit
`spec`; controllers should write `status`.

Finalizers are the deletion hook. Without a custom finalizer, Kubernetes can
delete the custom resource and garbage collect owned in-cluster children. That
is enough for a simple DemoApp. If the operator creates external resources, the
delete path may need a role or playbook that removes them before Kubernetes
lets the CR disappear. This module mentions finalizers only to set vocabulary;
the future arc module on production patterns will handle finalizer design in
depth.

Pause and predict: if the role creates a Deployment without an owner reference
or operator-injected ownership metadata, what happens when the custom resource
is deleted? The child object may remain behind because Kubernetes does not know
the CR owns it. Ansible Operator's Kubernetes proxy normally helps inject owner
references for same-namespace objects created through the Kubernetes modules,
but you should still verify ownership with `kubectl get deployment -o yaml`
when designing cleanup behavior.

## Ansible Operator, Helm Operator, and Go Operator

The three common Operator SDK implementation styles solve different problems.
They all expose Kubernetes APIs, but they place the implementation logic in
different places. Choosing between them is less about which tool is fashionable
and more about the shape of your desired state, the skills of the team, and
the complexity of the reconciliation logic.

| Implementation | Reconcile logic lives in | Best fit | Main trade-off |
|---|---|---|---|
| Ansible Operator | Ansible role or playbook | Teams with existing roles, procedural setup, post-install checks, or mixed Kubernetes and external tasks | Slower and less type-safe than Go for complex state machines |
| Helm Operator | Helm chart rendered from CR values | Applications that are already cleanly packaged as charts and mostly need install or upgrade semantics | Harder to express imperative validation, branching, and custom status |
| Go Operator | Go code using controller-runtime | Latency-sensitive controllers, complex resource graphs, custom caches, advanced predicates, webhooks, or strong typing | Higher implementation cost for teams that do not already write Go controllers |

An Ansible Operator is not "Helm with more YAML." Helm is a template renderer
plus release manager. Ansible is a task runner with modules, facts, conditionals,
registered results, retries, and error blocks. If your operator needs to call a
Kubernetes API, wait for readiness, inspect a resource, branch on the observed
result, and update a status field, Ansible can express that more naturally than
a chart. If your operator mostly installs a packaged application with a values
file, a Helm Operator may be simpler.

An Ansible Operator is also not "Go without Go." You still need controller
discipline. The controller process, cache, RBAC, CRD, image, and deployment
shape are real Kubernetes artifacts. Ansible only changes the implementation
language of the reconcile body. If the reconcile body needs sophisticated
queues, fine-grained event predicates, admission webhooks, cross-resource
indexing, or high-frequency decisions, Go is usually the right tool.

The practical rule is this: use Ansible when the domain logic already looks
like a role, use Helm when the domain logic already looks like a chart, and use
Go when the domain logic already looks like a controller.

## Designing the DemoApp API Before Scaffolding

Before running `operator-sdk init`, pause on the API contract. Operators become
hard to change when teams treat the first custom resource as an internal
implementation detail. A custom resource is a product surface. Application
teams will copy examples, dashboards will query fields, runbooks will mention
status values, and automation may patch spec fields directly. Even a teaching
operator should distinguish user intent from controller internals so the first
version teaches the right design habits.

The `DemoApp` API in this module is intentionally small: `replicas`, `image`,
and `port`. These fields are enough to prove the whole loop without pretending
the operator is a production application platform. `replicas` changes the
Deployment scale. `image` changes the container image. `port` changes the
Service port that other workloads would use inside the cluster. Every field is
observable in a child resource, which makes debugging concrete for learners.

Notice what the API does not expose. It does not expose every Deployment field,
every Service field, raw pod template patches, arbitrary annotations, or a
free-form map of extra Kubernetes objects. Those features are tempting because
they make the operator appear flexible, but they also erase the purpose of the
custom API. If users need to understand every underlying Kubernetes field, the
operator has not simplified the workflow; it has merely wrapped raw manifests
in another layer.

Good operator APIs are opinionated at the boundary and transparent in status.
The spec should contain the knobs the platform team wants users to own. The
role can apply labels, probes, selectors, service type, and naming conventions
consistently. The status should then explain what happened: whether the
Deployment is ready, which Service name was created, and which endpoint the
user can test. That split lets the platform team enforce defaults without
turning the CR into a black box.

Schema validation is part of the teaching model, not an optional polish step.
If `replicas` must be between 1 and 10, the API server should reject `20`
before Ansible runs. If `port` must be a valid TCP port, the CRD should say so.
Fast API rejection produces better user feedback and prevents the role from
becoming a second, inconsistent validation layer. The role can still assert
critical assumptions, but it should not be the only guardrail.

Status design should be equally deliberate. A beginner operator often starts
with whatever status the framework can produce automatically. That is useful
while scaffolding, but it rarely answers the user's question. A user does not
usually ask, "Did Ansible task 5 mark changed?" They ask, "Is my application
ready, how many replicas are ready, and what Service should I call?" The status
fields in this module answer those operational questions directly.

The `DemoApp` status is still not a full Kubernetes conditions model. That is
intentional. A production API would likely publish conditions such as
`Ready`, `Progressing`, and `ReconcileFailed`, each with status, reason,
message, and last transition time. This module stays lighter so the first
operator remains readable. The important habit is that status belongs to the
controller and should communicate observed state rather than repeat the spec.

RBAC belongs in API design too. The moment a CRD promises "create a DemoApp,"
the operator service account needs permission to create the child resources
that promise requires. If the role creates Deployments and Services, the RBAC
must say exactly that. If a later version creates Ingresses, Secrets, Jobs, or
external-provider objects, the permission review changes. A small API makes
that review easier because each field maps to a known operational effect.

Ownership is another early design decision. The custom resource should be the
stable parent, and the child objects should be named from the parent metadata.
If child names include the image tag, environment label, or a mutable display
name, updates can create new objects instead of patching existing ones. Stable
identity is what makes reconciliation feel boring: the same CR keeps managing
the same Deployment and Service as their specs evolve.

The same principle applies to labels. The role uses both
`app.kubernetes.io/name` and `app.kubernetes.io/instance` because those labels
separate the operator's application class from the individual CR instance. The
Service selector depends on those labels, the Deployment selector depends on
those labels, and troubleshooting commands can filter by those labels. A
controller that changes labels casually can break its own Service routing or
make garbage collection harder to reason about.

Finally, keep the first CRD boring enough that future modules can extend it.
Advanced watch patterns, AWX integration, finalizers, Molecule tests, and
Kuttl tests all become easier to teach when the first API is not overloaded.
The vocabulary you need today is simple: a spec with a few user-owned fields,
a role that reconciles child resources, status that reports observed state,
and RBAC that permits exactly the promised operations.

## Building a Minimum Viable Operator

The minimum viable operator in this module manages a custom resource called
`DemoApp`. A user creates a small object with `replicas`, `image`, and `port`.
The Ansible role reconciles a Deployment and Service, then writes a compact
status block back to the CR. The example is intentionally small because the
goal is to understand the SDK structure rather than to hide the model under a
large application.

Create a working directory and initialize the project with the Ansible plugin.
The domain becomes part of the API group, so `example.com` plus group `app`
will produce `app.example.com`.

```bash
mkdir demoapp-operator
cd demoapp-operator

operator-sdk init --plugins=ansible --domain=example.com
```

Add the custom resource API and ask the SDK to generate a role. The role name
will match the kind in lower-case form, so this module uses `demoapp`
throughout the example.

```bash
operator-sdk create api --group=app --version=v1 --kind=DemoApp --generate-role
```

The exact generated files can change slightly between SDK versions, but the
important layout is stable. `watches.yaml` maps the custom resource to the
role, `roles/` contains your Ansible implementation, and `config/` contains the
Kubernetes manifests used to install the CRD, service account, RBAC, and
controller Deployment.

```text
demoapp-operator/
├── Dockerfile
├── Makefile
├── PROJECT
├── requirements.yml
├── watches.yaml
├── roles/
│   └── demoapp/
│       ├── defaults/
│       │   └── main.yml
│       ├── meta/
│       │   └── main.yml
│       └── tasks/
│           └── main.yml
└── config/
    ├── crd/
    │   └── bases/
    ├── default/
    ├── manager/
    ├── rbac/
    └── samples/
```

Open `watches.yaml` and make the mapping explicit. The SDK usually scaffolds
the basic entry for you, but editing it now reinforces the contract. This
module disables generic status management because the role will publish the
status fields directly.

```yaml
---
- version: v1
  group: app.example.com
  kind: DemoApp
  role: demoapp
  manageStatus: false
```

Add the Ansible collections required by the role. The Kubernetes collection
provides `kubernetes.core.k8s` and `kubernetes.core.k8s_info`; the Operator SDK
utility collection provides `operator_sdk.util.k8s_status`. In a scaffolded
project, check both `requirements.yml` and the role metadata. The
`requirements.yml` file drives collection installation during `make docker-build` (the SDK
Dockerfile runs `ansible-galaxy collection install -r requirements.yml`). The
`meta/main.yml` `collections:` entry is a Galaxy dependency declaration — useful
only if the role is later published to Galaxy as a standalone artifact.

```yaml
# requirements.yml
---
collections:
  - name: kubernetes.core
  - name: operator_sdk.util
```

```yaml
# roles/demoapp/meta/main.yml
---
collections:
  - kubernetes.core
  - operator_sdk.util
```

The custom resource should have a small structural schema. Edit the CRD under
`config/crd/bases/app.example.com_demoapps.yaml` so users get validation before
the role ever runs. The full generated CRD contains metadata and conversion
details; the important part for this module is the schema under the served
version.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: demoapps.app.example.com
spec:
  group: app.example.com
  names:
    kind: DemoApp
    listKind: DemoAppList
    plural: demoapps
    singular: demoapp
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            apiVersion:
              type: string
            kind:
              type: string
            metadata:
              type: object
            spec:
              type: object
              properties:
                replicas:
                  type: integer
                  minimum: 1
                  maximum: 10
                  default: 1
                image:
                  type: string
                  default: nginx:1.27-alpine
                port:
                  type: integer
                  minimum: 1
                  maximum: 65535
                  default: 80
              required:
                - replicas
            status:
              type: object
              x-kubernetes-preserve-unknown-fields: true
      subresources:
        status: {}
```

Now write the role. The role does four things: derive defaults, validate the
requested replica count, reconcile a Deployment, reconcile a Service, and write
status. Notice that the role never shells out to `kubectl`. It uses the
Kubernetes collection so Ansible can perform idempotent API operations and
return structured results.

```yaml
# roles/demoapp/tasks/main.yml
---
- name: Derive DemoApp desired values
  ansible.builtin.set_fact:
    demoapp_name: "{{ ansible_operator_meta.name }}"
    demoapp_namespace: "{{ ansible_operator_meta.namespace }}"
    demoapp_replicas: "{{ replicas | default(1) | int }}"
    demoapp_image: "{{ image | default('nginx:1.27-alpine') }}"
    demoapp_port: "{{ port | default(80) | int }}"

- name: Validate DemoApp replica bounds
  ansible.builtin.assert:
    that:
      - demoapp_replicas >= 1
      - demoapp_replicas <= 10
    fail_msg: "DemoApp replicas must be between 1 and 10."

- name: Reconcile DemoApp Deployment
  kubernetes.core.k8s:
    state: present
    wait: true
    wait_timeout: 120
    # This blocks the reconcile loop for up to 120 s; production operators should use `k8s_info` with `retries`/`until` (see the Common Patterns section below) rather than blocking the worker on slow or flapping pods.
    definition:
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: "{{ demoapp_name }}"
        namespace: "{{ demoapp_namespace }}"
        labels:
          app.kubernetes.io/name: demoapp
          app.kubernetes.io/instance: "{{ demoapp_name }}"
          app.kubernetes.io/managed-by: ansible-operator
      spec:
        replicas: "{{ demoapp_replicas }}"
        selector:
          matchLabels:
            app.kubernetes.io/name: demoapp
            app.kubernetes.io/instance: "{{ demoapp_name }}"
        template:
          metadata:
            labels:
              app.kubernetes.io/name: demoapp
              app.kubernetes.io/instance: "{{ demoapp_name }}"
          spec:
            containers:
              - name: demoapp
                image: "{{ demoapp_image }}"
                imagePullPolicy: IfNotPresent
                ports:
                  - name: http
                    containerPort: 80
                # The `containerPort` stays at 80 because nginx serves on 80
                # regardless of which port the Service exposes; the CR `port` field
                # controls only the Service-facing port (its `targetPort` continues
                # to route to container port 80).
                readinessProbe:
                  httpGet:
                    path: /
                    port: http
                  initialDelaySeconds: 3
                  periodSeconds: 5
                livenessProbe:
                  httpGet:
                    path: /
                    port: http
                  initialDelaySeconds: 10
                  periodSeconds: 10

- name: Reconcile DemoApp Service
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Service
      metadata:
        name: "{{ demoapp_name }}"
        namespace: "{{ demoapp_namespace }}"
        labels:
          app.kubernetes.io/name: demoapp
          app.kubernetes.io/instance: "{{ demoapp_name }}"
          app.kubernetes.io/managed-by: ansible-operator
      spec:
        type: ClusterIP
        selector:
          app.kubernetes.io/name: demoapp
          app.kubernetes.io/instance: "{{ demoapp_name }}"
        ports:
          - name: http
            port: "{{ demoapp_port }}"
            targetPort: http

- name: Read DemoApp Deployment after reconcile
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: "{{ demoapp_name }}"
    namespace: "{{ demoapp_namespace }}"
  register: demoapp_deployment

- name: Publish DemoApp status
  operator_sdk.util.k8s_status:
    api_version: app.example.com/v1
    kind: DemoApp
    name: "{{ demoapp_name }}"
    namespace: "{{ demoapp_namespace }}"
    status:
      phase: >-
        {{
          'Ready'
          if ((demoapp_deployment.resources | first | default({}, true)).status.readyReplicas | default(0) | int) == demoapp_replicas
          else 'Progressing'
        }}
      replicas: "{{ demoapp_replicas }}"
      readyReplicas: "{{ (demoapp_deployment.resources | first | default({}, true)).status.readyReplicas | default(0) }}"
      serviceName: "{{ demoapp_name }}"
      endpoint: "http://{{ demoapp_name }}.{{ demoapp_namespace }}.svc.cluster.local:{{ demoapp_port }}"
```

The role is deliberately boring. Boring is good here. Reconciliation runs more
than once, so the tasks must be safe when the Deployment and Service already
exist. The `kubernetes.core.k8s` module patches resources toward the supplied
definition rather than creating duplicates. The status task publishes the
current observation and can run repeatedly without changing the desired spec.

The operator service account also needs permission to manage the child
resources. Edit `config/rbac/role.yaml` and make sure it includes Deployments,
Services, and the custom resource status subresource. The generated file may
already contain the custom resource rules; add the core and apps permissions if
they are missing.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: manager-role
rules:
  - apiGroups:
      - ""
    resources:
      - services
    verbs:
      - create
      - delete
      - get
      - list
      - patch
      - update
      - watch
  - apiGroups:
      - apps
    resources:
      - deployments
    verbs:
      - create
      - delete
      - get
      - list
      - patch
      - update
      - watch
  - apiGroups:
      - app.example.com
    resources:
      - demoapps
      - demoapps/status
      - demoapps/finalizers
    verbs:
      - create
      - delete
      - get
      - list
      - patch
      - update
      - watch
```

Update the sample custom resource under
`config/samples/app_v1_demoapp.yaml`. The sample is what you will apply after
the operator is running.

```yaml
apiVersion: app.example.com/v1
kind: DemoApp
metadata:
  name: demoapp-sample
spec:
  replicas: 2
  image: nginx:1.27-alpine
  port: 80
```

Build the operator image. In a normal shared cluster, push the image to a
registry that the cluster can pull. Replace the registry namespace with one you
control. This command path is the production-shaped path because Kubernetes
nodes pull the operator image from a real registry.

```bash
export IMG="quay.io/YOUR_NAMESPACE/demoapp-operator:v0.1.0"

make docker-build docker-push IMG="${IMG}"
make deploy IMG="${IMG}"
```

For a local kind lab, you can build the image and load it directly into the
kind node instead of using a remote registry. This keeps the lab runnable even
when you do not want to create a registry repository for a throwaway example.

```bash
export IMG="demoapp-operator:v0.1.0"

make docker-build IMG="${IMG}"
kind load docker-image "${IMG}" --name ansible-operator-lab
make deploy IMG="${IMG}"
```

The `make deploy` target uses kustomize under the hood. If you want to see the
manifests before applying them, render the default overlay. This is especially
useful when debugging image names, service account names, or RBAC scope.

```bash
kustomize build config/default | sed -n '1,180p'
```

Create a namespace for the managed application and apply the sample custom
resource. The operator itself is usually deployed into a system namespace such
as `demoapp-operator-system`, while the custom resources can live in tenant
namespaces if RBAC allows it.

```bash
kubectl create namespace demoapp-lab
kubectl apply -n demoapp-lab -f config/samples/app_v1_demoapp.yaml
```

Observe the reconciliation. First confirm that the custom resource exists,
then inspect the child Deployment and Service. The Deployment should converge
to two ready replicas, and the Service should point at the Pods selected by the
labels in the role.

```bash
kubectl get demoapps.app.example.com -n demoapp-lab
kubectl get deployment,service,pods -n demoapp-lab
kubectl get demoapp demoapp-sample -n demoapp-lab -o yaml
```

Expected output will vary in timestamps and image IDs, but the shape should be
recognizable. The custom resource should exist, the Deployment should have the
requested replica count, and the Service should expose port 80.

```text
NAME             AGE
demoapp-sample   1m

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/demoapp-sample   2/2     2            2           1m

NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/demoapp-sample   ClusterIP   10.96.120.15    <none>        80/TCP    1m
```

Finally, check the operator logs. Ansible output is one of the best early
debugging surfaces because it tells you which task ran, which task changed
something, and which task failed. In a generated SDK project, the controller
Deployment name usually includes `controller-manager`.

```bash
kubectl logs -n demoapp-operator-system deployment/demoapp-operator-controller-manager
```

Pause and predict: if you edit `spec.replicas` from 2 to 3, should the
operator create a new Deployment or patch the existing Deployment? The correct
behavior is a patch. The resource identity is still the same; only desired
state changed. If you see duplicate Deployments, your role is deriving names
from mutable inputs or bypassing the Kubernetes module in a way that breaks
idempotency.

## Common Patterns for Ansible Reconcilers

The first production pattern is to make every task idempotent. A reconcile loop
will run after create events, update events, dependent resource changes, and
periodic resyncs. A task that is safe only once is not a controller task. Use
`kubernetes.core.k8s` with complete resource definitions, stable names, stable
labels, and explicit state. Avoid shell commands that call `kubectl apply`
unless you have a very specific reason and a test proving idempotency.

```yaml
- name: Reconcile a ConfigMap with a stable name
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: "{{ ansible_operator_meta.name }}-settings"
        namespace: "{{ ansible_operator_meta.namespace }}"
      data:
        logLevel: "{{ log_level | default('info') }}"
```

The second pattern is to treat status as a user interface. A status field is
not a dump of every Ansible variable; it is the compact observation users need
after they apply a CR. For a workload wrapper, useful fields might include
`phase`, `readyReplicas`, `serviceName`, `endpoint`, and a `conditions` list.
For an external integration, useful fields might include provider ID, last
sync time, and a clear failure reason. Keep status stable enough that humans
and automation can rely on it.

```yaml
- name: Publish a focused status block
  operator_sdk.util.k8s_status:
    api_version: app.example.com/v1
    kind: DemoApp
    name: "{{ ansible_operator_meta.name }}"
    namespace: "{{ ansible_operator_meta.namespace }}"
    status:
      phase: Ready
      readyReplicas: 2
      serviceName: "{{ ansible_operator_meta.name }}"
```

The third pattern is controlled failure. A failed Ansible task becomes a failed
reconcile, which is useful when the error is truly blocking. For expected
transient states, use retries, readiness checks, `failed_when`, and `rescue`
blocks so the status tells the truth. Do not hide every failure, but do not
make the controller crash-loop because a Deployment needed another few seconds
to become ready.

```yaml
- name: Read Deployment availability with controlled retry
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: "{{ ansible_operator_meta.name }}"
    namespace: "{{ ansible_operator_meta.namespace }}"
  register: deployment_read
  retries: 10
  delay: 6
  until: >
    (deployment_read.resources | length) == 1 and
    ((deployment_read.resources | first | default({}, true)).status.readyReplicas | default(0) | int) >=
    (replicas | default(1) | int)
```

The fourth pattern is to keep variable translation obvious. Operator SDK passes
custom resource `spec` fields into Ansible as variables and, by default, case
converts camelCase into snake_case. If your CRD uses `serviceAccountName`, your
role should expect `service_account_name` unless you explicitly disable the
conversion in `watches.yaml`. Document that mapping because it becomes a
common source of "variable is undefined" failures.

```yaml
---
- version: v1
  group: app.example.com
  kind: DemoApp
  role: demoapp
  snakeCaseParameters: true
```

The fifth pattern is to keep external side effects behind explicit fields and
finalizers. It is easy to call a cloud API from Ansible, but a controller must
also know how to observe, retry, report, and delete that external state. If
the first version only manages in-cluster resources, you can rely on owner
references and ordinary garbage collection. Once you create external state,
design the finalizer and status story before adding the task.

## Decision Framework: When Ansible Operator Beats Go Operator

An Ansible Operator beats a Go Operator when the reconciliation problem is
mostly operational automation and the team can express it safely with existing
roles. It does not beat Go because YAML is inherently easier. It beats Go when
the cost of introducing a full Go controller exceeds the value of strong
typing, custom caches, advanced event filtering, and fine-grained control over
the reconcile loop.

| Question | Ansible Operator is a strong fit when | Go Operator is a stronger fit when |
|---|---|---|
| Team skill | The team already writes and reviews Ansible roles well | The team already maintains Go services or controllers |
| Logic shape | Reconciliation is a sequence of idempotent tasks | Reconciliation is a complex state machine |
| Resource graph | A small CR manages a modest set of children | Many related resource types need indexes and predicates |
| Latency | Seconds-level convergence is acceptable | Sub-second or high-frequency decisions matter |
| Validation | Ansible assertions and CRD schema are enough | Compile-time types and admission webhooks are central |
| External systems | Existing modules already automate the external API | Custom API clients, caches, or streaming watches are needed |
| Delivery pressure | A working role can become a controller quickly | Long-term controller complexity justifies the upfront cost |
| Operations | Logs and task output are useful to the team | Structured metrics and custom reconcile paths dominate |

Use this table as a design review tool, not as a permanent identity. A team
can start with an Ansible Operator to prove the custom resource contract, then
rewrite the controller in Go later if the API becomes central and the state
machine outgrows role-based automation. The custom resource interface is often
more durable than the first implementation language.

## When Not to Use Ansible Operator

Do not use an Ansible Operator for latency-sensitive controllers. A role run
has Ansible startup overhead, task execution overhead, API calls through
modules, and artifact handling. That is acceptable for many platform workflows,
but it is the wrong shape for controllers that need very fast reactions to
large numbers of events.

Do not use an Ansible Operator for high-frequency reconcile loops. A short
`reconcilePeriod` can multiply API traffic and logs even when no meaningful
state has changed. If you are tempted to reconcile every few seconds, first
ask why watch events and dependent watches are not enough. If the answer is
"the domain requires constant control decisions," Go is probably a better
implementation.

Do not use an Ansible Operator as a place to hide a complex state machine.
Ansible can branch, retry, rescue, include tasks, and call APIs, but a large
graph of states, timers, cross-resource dependencies, and partial failure
paths becomes hard to reason about in YAML. Complex controllers benefit from
typed structs, unit tests, explicit state transitions, and controller-runtime
primitives.

Do not use an Ansible Operator when the desired behavior is already a clean
Helm chart install. If the CR mostly passes values into templates and the
application lifecycle is install, upgrade, and uninstall, a Helm Operator or
plain GitOps-managed Helm release may be less surprising. Ansible earns its
place when task logic, checks, external operations, or status reporting matter.

Do not use an Ansible Operator to bypass platform boundaries. The operator Pod
runs with a service account, and that service account can be powerful. A role
that talks to arbitrary external APIs or broad cluster resources must go
through the same security review as any controller. YAML does not make side
effects safer.

## Troubleshooting the First Reconcile

The fastest troubleshooting path starts with the custom resource, not with the
operator code. Read the CR and confirm that the `spec` the API server stored
is the spec you intended to submit. If schema defaults applied, they should be
visible. If validation rejected the object, no role run happened, so operator
logs will not explain the failure. This separation matters because API
validation failures and reconcile failures live in different parts of the
system.

After the CR is accepted, inspect status. A useful Ansible Operator status
field should tell you whether the role reached the point where it could observe
child resources. If `phase` is missing, the role may not have run, the status
task may have failed, or `manageStatus` may be fighting with your custom
status behavior. If `phase` is `Progressing`, compare the reported ready
replicas with the Deployment status before assuming Ansible is wrong.

The next step is child-resource inspection. Look at the Deployment and Service
labels, selectors, owner references, and events. A Service with the wrong
selector can make an application look down even while Pods are healthy. A
Deployment with a missing owner reference may survive CR deletion. A Pod image
pull error may be a registry problem, not an operator problem. The controller
is responsible for creating resources, but Kubernetes still owns scheduling,
pulling images, probing containers, and recording Pod events.

Only after those checks should you read the operator logs in detail. Ansible
logs are task-oriented, which is useful when you know which CR triggered the
run. Search around the CR name and namespace, then identify the first failed
task rather than the last stack trace. If the first failed task is a
`kubernetes.core.k8s` call with a forbidden error, the fix is probably RBAC. If
the failed task is an assertion, the fix is probably input validation or a
clearer CRD schema.

Finally, verify permissions as the operator service account. `kubectl auth
can-i` is not a replacement for logs, but it quickly proves whether the
controller is allowed to perform the operation your role requested. This habit
prevents a common time sink: editing Ansible tasks for an hour when the real
bug is that the deployed ClusterRole cannot patch Deployments in the tenant
namespace.

## Production Readiness Checklist

Use this checklist when a prototype starts moving toward shared-cluster use.
The goal is not to make a small operator heavyweight; the goal is to identify
the production decisions that are easy to forget when the first lab works.

- [ ] The CRD schema validates required fields, allowed ranges, and defaults.
- [ ] The role is idempotent when the same CR is reconciled repeatedly.
- [ ] The role uses `kubernetes.core.k8s` and `kubernetes.core.k8s_info`
  instead of shelling out to `kubectl`.
- [ ] The operator service account has only the Kubernetes verbs and resources
  the role actually needs.
- [ ] The role publishes stable status fields that help users debug without
  reading controller logs.
- [ ] Failure paths use clear Ansible errors, controlled retries, and status
  updates for expected transient states.
- [ ] Any external resource creation has a deletion story, usually involving a
  finalizer.
- [ ] The image tag is immutable in production deployment manifests.
- [ ] The container registry, image signature, and vulnerability scanning
  workflow are defined.
- [ ] The operator logs are collected, searchable, and mapped to CR names and
  namespaces.
- [ ] The team has a local test path and a cluster test path before changing
  production roles.
- [ ] The team has decided which future advanced watch patterns are allowed
  before adding multiple CRDs or dependent watches.

## Did You Know?

- Operator SDK's current documentation shows the Ansible quickstart using
  `operator-sdk init --domain example.com --plugins ansible`, followed by
  `operator-sdk create api --generate-role`, which is the same scaffold pattern
  this module uses.
- `watches.yaml` supports a periodic `reconcilePeriod` for cases where watch
  events are not enough, and the documentation warns that low values can make
  expensive operators perform worse rather than safer.
- Custom resource `spec` fields are converted to Ansible variables, and the
  default case conversion turns camelCase fields such as `serviceAccountName`
  into snake_case variables such as `service_account_name`.
- The modern Kubernetes Ansible collection is `kubernetes.core`; older examples
  that use legacy Kubernetes modules should be treated as historical unless a
  maintained project still documents that exact path.

## Common Mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Treating the operator as a scheduled playbook runner | The role runs repeatedly without a clear event model, creating noisy logs and surprising API load | Design for watch-driven reconciliation first, then add periodic reconciliation only for a specific reason |
| Using shell tasks that call `kubectl` | Tasks become harder to make idempotent, harder to inspect, and dependent on CLI behavior inside the image | Use `kubernetes.core.k8s` and `kubernetes.core.k8s_info` for structured API operations |
| Forgetting RBAC for child resources | The CR is accepted but reconciliation fails with forbidden errors when the role creates Deployments or Services | Add only the required verbs and resources to `config/rbac/role.yaml`, then test with the deployed service account |
| Publishing raw Ansible output as the only status signal | Users cannot tell whether the application is ready without reading controller logs | Set `manageStatus: false` and write focused fields with `operator_sdk.util.k8s_status` |
| Deriving child resource names from mutable spec fields | Edits create duplicate Deployments or Services instead of patching the existing children | Derive names from CR metadata and keep mutable inputs inside the child spec |
| Setting a very short `reconcilePeriod` | The operator polls aggressively, burns API budget, and hides real event-driven behavior under noise | Keep the period conservative and rely on watched resource events for ordinary convergence |
| Creating external resources without deletion design | Deleting the CR leaves cloud or SaaS resources behind because Kubernetes garbage collection cannot see them | Add a finalizer and make deletion idempotent before shipping the external side effect |
| Letting the CRD schema stay loose | Invalid values reach the role and fail later with unclear Ansible errors | Add structural schema validation for required fields, ranges, enums, and defaults |

## Quiz: Self-Check

<details>
<summary>Your team has a working Ansible role that creates a Deployment and Service from a few variables. Product teams want a Kubernetes-native self-service API. Why might an Ansible Operator be a reasonable first implementation?</summary>

An Ansible Operator lets the team keep the existing role vocabulary while
placing it behind a Kubernetes custom resource and reconcile loop. The team can
ship a small CRD, map it in `watches.yaml`, and use `kubernetes.core.k8s` tasks
to converge child resources without immediately writing a Go controller. This
is a good fit when seconds-level convergence is acceptable and the logic is a
sequence of idempotent tasks rather than a complex state machine.

</details>

<details>
<summary>A `DemoApp` custom resource is accepted, but the operator logs show forbidden errors when creating Deployments. What should you inspect first?</summary>

Inspect the operator service account's RBAC, especially `config/rbac/role.yaml`
and the rendered ClusterRole or Role applied to the cluster. The CRD being
accepted only proves the API server understands the custom resource; it does
not prove the controller can create child objects. Add the minimal `apps`
Deployment verbs the role needs, redeploy the operator manifests, and rerun the
reconcile by editing or reapplying the CR.

</details>

<details>
<summary>Your CR has `spec.serviceAccountName`, but the role fails because `serviceAccountName` is undefined. What is the likely cause?</summary>

Operator SDK passes spec fields into Ansible and, by default, converts camelCase
field names into snake_case variables. The role should look for
`service_account_name` unless `snakeCaseParameters` was disabled in
`watches.yaml`. The better fix is to document the mapping and keep role
variable names consistent with the operator's conversion behavior rather than
guessing at both forms.

Note: the CRD declares `spec.serviceAccountName` (camelCase), but inside the Ansible
role you receive it as `service_account_name` (snake_case) because watches.yaml
has `snakeCaseParameters: true`. This is the most common point of confusion when
porting between SDK and Ansible Operator.

</details>

<details>
<summary>A teammate proposes setting `reconcilePeriod: 5s` because frequent reconciliation feels safer. How would you evaluate that proposal?</summary>

Frequent periodic reconciliation is not automatically safer; it can create API
load, log noise, and repeated Ansible artifact churn even when no desired state
changed. First confirm whether ordinary watch events and dependent resource
watches already cover the failure mode the teammate is worried about. A short
period should be reserved for a documented case where no useful Kubernetes
event exists and where the operator's API cost has been tested.

</details>

<details>
<summary>The role creates an external DNS record through an API call when the CR is created. What design topic becomes mandatory before production?</summary>

Deletion design becomes mandatory because Kubernetes garbage collection cannot
clean up an external DNS record by itself. The operator likely needs a
finalizer so a delete event can run an idempotent cleanup role or playbook
before the custom resource is removed. The status should also expose enough
external identity information for operators to confirm which remote object is
being managed.

</details>

<details>
<summary>The `DemoApp` role creates a new Deployment every time `spec.image` changes. Which implementation smell does that reveal?</summary>

The role is probably deriving the child Deployment name from mutable spec data,
or it is creating resources outside an idempotent `kubernetes.core.k8s`
definition. Child resource identity should normally come from stable CR
metadata such as the CR name and namespace. Mutable values such as image,
replicas, and port belong inside the Deployment or Service spec so edits patch
the existing child resources.

</details>

## Hands-On Exercise: Runnable End-to-End Lab

This lab builds the `DemoApp` operator in a kind cluster. It uses a local image
load path so you do not need a public registry, and it keeps the managed
application in a separate namespace from the operator. The lab assumes your
machine can run Docker containers and that `operator-sdk` is installed from
the official installation instructions.

### Task 1: Create the kind Cluster

Create a Kubernetes 1.35 kind cluster for the operator lab. If you already have
a cluster with this name, delete it first so the lab starts from known state.

```bash
kind delete cluster --name ansible-operator-lab
kind create cluster --name ansible-operator-lab --image kindest/node:v1.35.0
kubectl cluster-info --context kind-ansible-operator-lab
```

If your local kind version doesn't have the v1.35.0 node image cached, drop the `--image` flag entirely — `kind create cluster` will default to whatever node image your installed kind ships with, which is typically a recent stable release.

Expected output should show the control plane endpoint for the kind cluster and
confirm that `kubectl` is using the correct context. If `kubectl` points at a
different cluster, stop and fix the context before deploying the operator.

```bash
kubectl config current-context
```

<details>
<summary>Solution guidance for Task 1</summary>

The context should be `kind-ansible-operator-lab`. If it is not, run
`kubectl config use-context kind-ansible-operator-lab` and repeat the current
context check. Starting with a known local cluster keeps the operator RBAC,
namespace, and image-loading behavior predictable during the rest of the lab.

</details>

### Task 2: Scaffold the Operator Project

Create the SDK project and generate the API. The command names and flags are
the same as the conceptual walkthrough, but this time you will edit the files
for a real local run.

```bash
mkdir demoapp-operator
cd demoapp-operator

operator-sdk init --plugins=ansible --domain=example.com
operator-sdk create api --group=app --version=v1 --kind=DemoApp --generate-role
```

Inspect the generated files before editing. This is not busywork; knowing what
the SDK generated helps you debug later when a manifest, RBAC rule, or image
name is not what you expected.

```bash
find . -maxdepth 3 -type f | sort | sed -n '1,120p'
cat watches.yaml
```

<details>
<summary>Solution guidance for Task 2</summary>

You should see `watches.yaml`, `roles/demoapp/`, `config/rbac/`,
`config/crd/`, `config/manager/`, and `config/samples/`. If the role directory
has a different case or spelling, use the generated name consistently rather
than forcing the tutorial's spelling. The watch entry must point to the role
name that exists inside `roles/`.

</details>

### Task 3: Add the Role, Schema, and RBAC

Replace or edit `watches.yaml` so it maps `DemoApp` to the `demoapp` role and
disables generic status management for this module.

```yaml
---
- version: v1
  group: app.example.com
  kind: DemoApp
  role: demoapp
  manageStatus: false
```

Ensure `requirements.yml` includes the two collections used by the role.

```yaml
---
collections:
  - name: kubernetes.core
  - name: operator_sdk.util
```

Ensure `roles/demoapp/meta/main.yml` declares the same collections for role
execution.

```yaml
---
collections:
  - kubernetes.core
  - operator_sdk.util
```

Edit `roles/demoapp/tasks/main.yml` with the role from the walkthrough. If you
copy the full role, keep the names stable and keep `imagePullPolicy:
IfNotPresent`; that setting lets kind use the locally loaded operator-managed
workload image if you later experiment with custom images.

```yaml
---
- name: Derive DemoApp desired values
  ansible.builtin.set_fact:
    demoapp_name: "{{ ansible_operator_meta.name }}"
    demoapp_namespace: "{{ ansible_operator_meta.namespace }}"
    demoapp_replicas: "{{ replicas | default(1) | int }}"
    demoapp_image: "{{ image | default('nginx:1.27-alpine') }}"
    demoapp_port: "{{ port | default(80) | int }}"

- name: Validate DemoApp replica bounds
  ansible.builtin.assert:
    that:
      - demoapp_replicas >= 1
      - demoapp_replicas <= 10
    fail_msg: "DemoApp replicas must be between 1 and 10."

- name: Reconcile DemoApp Deployment
  kubernetes.core.k8s:
    state: present
    wait: true
    wait_timeout: 120
    definition:
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: "{{ demoapp_name }}"
        namespace: "{{ demoapp_namespace }}"
        labels:
          app.kubernetes.io/name: demoapp
          app.kubernetes.io/instance: "{{ demoapp_name }}"
          app.kubernetes.io/managed-by: ansible-operator
      spec:
        replicas: "{{ demoapp_replicas }}"
        selector:
          matchLabels:
            app.kubernetes.io/name: demoapp
            app.kubernetes.io/instance: "{{ demoapp_name }}"
        template:
          metadata:
            labels:
              app.kubernetes.io/name: demoapp
              app.kubernetes.io/instance: "{{ demoapp_name }}"
          spec:
            containers:
              - name: demoapp
                image: "{{ demoapp_image }}"
                imagePullPolicy: IfNotPresent
                ports:
                  - name: http
                    containerPort: 80
                readinessProbe:
                  httpGet:
                    path: /
                    port: http
                  initialDelaySeconds: 3
                  periodSeconds: 5
                livenessProbe:
                  httpGet:
                    path: /
                    port: http
                  initialDelaySeconds: 10
                  periodSeconds: 10

- name: Reconcile DemoApp Service
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Service
      metadata:
        name: "{{ demoapp_name }}"
        namespace: "{{ demoapp_namespace }}"
        labels:
          app.kubernetes.io/name: demoapp
          app.kubernetes.io/instance: "{{ demoapp_name }}"
          app.kubernetes.io/managed-by: ansible-operator
      spec:
        type: ClusterIP
        selector:
          app.kubernetes.io/name: demoapp
          app.kubernetes.io/instance: "{{ demoapp_name }}"
        ports:
          - name: http
            port: "{{ demoapp_port }}"
            targetPort: http

- name: Read DemoApp Deployment after reconcile
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: "{{ demoapp_name }}"
    namespace: "{{ demoapp_namespace }}"
  register: demoapp_deployment

- name: Publish DemoApp status
  operator_sdk.util.k8s_status:
    api_version: app.example.com/v1
    kind: DemoApp
    name: "{{ demoapp_name }}"
    namespace: "{{ demoapp_namespace }}"
    status:
      phase: >-
        {{
          'Ready'
          if ((demoapp_deployment.resources | first | default({}, true)).status.readyReplicas | default(0) | int) == demoapp_replicas
          else 'Progressing'
        }}
      replicas: "{{ demoapp_replicas }}"
      readyReplicas: "{{ (demoapp_deployment.resources | first | default({}, true)).status.readyReplicas | default(0) }}"
      serviceName: "{{ demoapp_name }}"
      endpoint: "http://{{ demoapp_name }}.{{ demoapp_namespace }}.svc.cluster.local:{{ demoapp_port }}"
```

Add the CRD schema and RBAC snippets from the walkthrough. Then render the
operator manifests before deploying so you can catch indentation mistakes or
image placeholder problems early.

```bash
kustomize build config/default >demoapp-operator-rendered.yaml
sed -n '1,220p' demoapp-operator-rendered.yaml
```

<details>
<summary>Solution guidance for Task 3</summary>

If kustomize fails, the problem is usually malformed YAML in the CRD, RBAC, or
manager overlay. If kustomize succeeds but the operator later fails to create
child resources, inspect RBAC first. Rendering manifests before deployment is
one of the fastest ways to move from "the SDK generated something" to "I know
what Kubernetes will receive."

</details>

### Task 4: Build and Deploy the Operator

Build the operator image, load it into kind, and deploy the operator. This path
avoids a remote image registry while still exercising the same image and
kustomize deployment mechanics used by the production-shaped flow.

```bash
export IMG="demoapp-operator:v0.1.0"

make docker-build IMG="${IMG}"
kind load docker-image "${IMG}" --name ansible-operator-lab
make deploy IMG="${IMG}"
```

Wait for the controller Deployment. The namespace name comes from the generated
project name; if your directory name differs, inspect `config/default` or list
namespaces to find the generated system namespace.

```bash
kubectl get namespaces | grep demoapp
kubectl rollout status deployment/demoapp-operator-controller-manager \
  -n demoapp-operator-system \
  --timeout=180s
```

<details>
<summary>Solution guidance for Task 4</summary>

If the rollout waits forever, check the controller Pod events and image name.
In kind, `kind load docker-image` must target the same cluster name you created
in Task 1. If the Pod starts but crashes, read the logs; collection install
errors, malformed `watches.yaml`, and RBAC mistakes usually appear clearly in
the controller output.

</details>

### Task 5: Create a DemoApp Instance and Observe Reconciliation

Create the namespace for the managed application and apply the sample custom
resource. If your sample file lacks a namespace, the `-n demoapp-lab` flag
places the CR in the lab namespace.

```bash
kubectl create namespace demoapp-lab
kubectl apply -n demoapp-lab -f config/samples/app_v1_demoapp.yaml
```

Watch the child resources. A successful reconciliation creates a Deployment,
two Pods, and a Service with the same stable instance label.

```bash
kubectl get demoapps.app.example.com -n demoapp-lab
kubectl get deployment,service,pods -n demoapp-lab
kubectl get demoapp demoapp-sample -n demoapp-lab -o jsonpath='{.status.phase}{"\n"}'
```

Scale through the custom resource instead of editing the Deployment. This is
the point of the operator API: users change desired state on the CR, and the
controller converges children.

```bash
kubectl patch demoapp demoapp-sample \
  -n demoapp-lab \
  --type=merge \
  -p '{"spec":{"replicas":3}}'

kubectl rollout status deployment/demoapp-sample -n demoapp-lab --timeout=180s
kubectl get deployment demoapp-sample -n demoapp-lab
```

<details>
<summary>Solution guidance for Task 5</summary>

The Deployment should scale to three replicas without creating a second
Deployment. If the status remains `Progressing`, check the Pods and then the
operator logs. If the Deployment does not change at all, confirm the CR patch
actually changed `.spec.replicas` and that the operator has permission to patch
Deployments in `demoapp-lab`.

</details>

### Task 6: Break It Deliberately and Diagnose the Failure

Patch the CR to an invalid replica count. The CRD schema should reject the
request before Ansible runs. This proves validation is happening at the API
boundary.

```bash
kubectl patch demoapp demoapp-sample \
  -n demoapp-lab \
  --type=merge \
  -p '{"spec":{"replicas":20}}'
```

Now simulate an RBAC-style failure by reading the operator logs and identifying
the service account that would need additional permissions if a task failed.
You do not need to break RBAC manually for the lab; the diagnostic workflow is
the important part.

```bash
kubectl get pod -n demoapp-operator-system
kubectl logs -n demoapp-operator-system deployment/demoapp-operator-controller-manager | tail -n 80
kubectl auth can-i patch deployments \
  --as=system:serviceaccount:demoapp-operator-system:demoapp-operator-controller-manager \
  -n demoapp-lab
```

<details>
<summary>Solution guidance for Task 6</summary>

The invalid patch should fail because the schema caps replicas at 10. The
`kubectl auth can-i` command should answer `yes` after RBAC is correct. When a
real reconcile fails, collect three pieces of evidence before changing code:
the CR `.status`, the operator logs around the failed task, and the Kubernetes
authorization result for the service account.

</details>

### Task 7: Clean Up

Delete the custom resource, undeploy the operator, and delete the kind cluster.
Cleanup matters because controller labs can leave CRDs and namespaces behind,
which makes later runs confusing.

```bash
kubectl delete demoapp demoapp-sample -n demoapp-lab
make undeploy
kind delete cluster --name ansible-operator-lab
```

### Success Criteria

- [ ] You designed the `watches.yaml` mapping from `DemoApp` to the `demoapp`
  role and can explain how the mapping starts reconciliation.
- [ ] You implemented the DemoApp operator with Operator SDK,
  `kubernetes.core.k8s`, and `operator_sdk.util.k8s_status`.
- [ ] You deployed the operator image into a kind cluster and created a
  `DemoApp` custom resource.
- [ ] You observed the Deployment, Service, Pods, and custom resource status
  created by the role.
- [ ] You diagnosed at least one validation or reconciliation failure using CR
  status, operator logs, and RBAC checks.
- [ ] You evaluated whether the example would still fit Ansible Operator if it
  grew external resources, short reconcile periods, or a complex state machine.

## Next Arc Modules

This module is the vocabulary-setter for the Ansible Operator arc. Future
modules can now assume that `watches.yaml`, role-driven reconciliation,
`kubernetes.core`, custom status, and the Ansible-versus-Go trade-off have
already been introduced.

- **Module 7.13: Advanced `watches.yaml` Patterns** - selectors,
  multiple watches, dependent watches, reconcile period tuning, and annotation
  overrides.
- **Module 7.14: AWX, Tower, and Event-Driven Ansible Integration** -
  where cluster controllers and enterprise automation controllers should meet,
  and where they should remain separate.
- **Module 7.15: Helm vs. Ansible Operator Decision Framework** -
  a deeper implementation-choice guide for chart-shaped, role-shaped, and
  code-shaped controllers.
- **Module 7.16: Production Ansible Operator Patterns** - finalizers,
  status conditions, RBAC minimization, image publishing, observability, and
  upgrade strategy.
- **Module 7.17: Testing Ansible Operators with Molecule and Kuttl** -
  local role tests, cluster integration tests, and CI gates for operator
  behavior.

## Sources

- https://sdk.operatorframework.io/docs/building-operators/ansible/
- https://sdk.operatorframework.io/docs/building-operators/ansible/quickstart/
- https://sdk.operatorframework.io/docs/building-operators/ansible/tutorial/
- https://sdk.operatorframework.io/docs/building-operators/ansible/reference/watches/
- https://sdk.operatorframework.io/docs/building-operators/ansible/reference/information-flow-ansible-operator/
- https://sdk.operatorframework.io/docs/building-operators/ansible/reference/finalizers/
- https://sdk.operatorframework.io/docs/installation/
- https://github.com/ansible-collections/kubernetes.core
- https://docs.ansible.com/ansible/latest/collections/kubernetes/core/k8s_module.html
- https://docs.ansible.com/ansible/latest/collections/kubernetes/core/k8s_info_module.html
- https://github.com/operator-framework/ansible-operator-plugins
- https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
- https://kubernetes.io/docs/concepts/architecture/controller/

## Next Module

Continue with **Module 7.13: Advanced `watches.yaml` Patterns** to
learn how one Ansible Operator can manage multiple kinds, tune event behavior,
control dependent watches, and make deliberate choices about periodic
reconciliation.
