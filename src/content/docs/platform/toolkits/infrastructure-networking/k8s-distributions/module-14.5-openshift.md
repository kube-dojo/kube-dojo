---
revision_pending: false
title: "Module 14.5: OpenShift - Enterprise Kubernetes with Batteries Included"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.5-openshift
sidebar:
  order: 6
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 70-85 minutes
>
> **Prerequisites**: [Module 14.1: k3s](../module-14.1-k3s/), [Module 14.4: Talos](../module-14.4-talos/), Kubernetes fundamentals, CRDs, RBAC, Operators, and the [Platform Engineering Discipline](/platform/disciplines/core-platform/platform-engineering/).

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Explain** enterprise Kubernetes distribution integration, support, lifecycle, lock-in, and cost tradeoffs without turning the discussion into vendor advocacy.
- **Map** OpenShift architecture across the control plane, Router, Routes, registry, ImageStreams, Source-to-Image, OperatorHub, and Operators.
- **Design** project-based multi-tenancy with RBAC, ResourceQuotas, LimitRanges, and Security Context Constraints for teams sharing one platform.
- **Build** developer workflows with `oc new-app`, Templates, Source-to-Image, OpenShift Pipelines, and OpenShift GitOps.
- **Decide** when OpenShift earns its cost and when vanilla Kubernetes plus a capable platform team is the better operating model.

## Why This Module Matters

Hypothetical scenario: a platform team is asked to give twelve product teams a supported Kubernetes platform within one quarter. The Kubernetes API is only the starting point. The teams also need ingress, certificate handling, image builds, image promotion, registry policy, GitOps, monitoring, logging, tenant boundaries, identity integration, upgrade policy, and support escalation. The platform team can assemble those pieces from upstream projects, or it can buy an enterprise distribution that arrives with many of those choices already integrated.

That scenario is common because Kubernetes is a kernel for platforms, not a complete platform by itself. Upstream Kubernetes gives you a portable API for scheduling, service discovery, storage attachment, workload rollout, and extension through controllers. It intentionally leaves many production decisions outside the core. The moment a company asks for self-service onboarding, regulated tenant isolation, supported upgrades, or a developer path from source code to running application, the platform team has to choose how much of the surrounding system it wants to build and own.

OpenShift is one answer to that pressure. It is Red Hat's commercial enterprise Kubernetes distribution, built from the same broad family of technology as OKD, the upstream community distribution. OpenShift is not a CNCF project in the way Kubernetes, Argo, or Tekton are CNCF projects. It is a Red Hat product that participates in the CNCF Certified Kubernetes conformance program, which means the Kubernetes API surface is expected to behave compatibly while the distribution adds opinionated platform services around it.

The durable lesson is not "OpenShift is better than Kubernetes." OpenShift is Kubernetes plus product decisions, support boundaries, and a lifecycle model. Those decisions can be valuable when an organization wants one supported stack and fewer integration projects. They can be constraining when a platform team already has mature choices for every layer, or when subscription cost and vendor coupling outweigh the operational savings. A serious platform engineer learns to evaluate both sides with evidence.

The useful analogy is a commercial kitchen. Kubernetes is the set of reliable burners, prep tables, refrigeration units, and safety controls. OpenShift is a franchised kitchen design where the supplier also specifies the workflow, approved appliances, maintenance plan, and inspection checklist. The franchise model can help a new location open faster and operate consistently. It can also limit substitutions when a chef has a specialized process that the approved design was not built to support.

OpenShift matters in platform engineering because it makes the build-versus-buy question concrete. If your organization treats platform integration as undifferentiated heavy lifting, buying an integrated distribution can release scarce engineers to work on developer experience, reliability, and product enablement. If your organization treats platform composition as a strategic capability, a more modular vanilla Kubernetes stack may be worth the extra ownership. The decision turns on operating maturity, workload needs, compliance context, upgrade appetite, and the cost of coordination.

## Enterprise Kubernetes Distribution Tradeoffs

An enterprise Kubernetes distribution adds more than an installer. It usually packages a tested Kubernetes minor, a supported operating-system baseline, a default container runtime, networking defaults, ingress behavior, identity integration, an update mechanism, monitoring, logging, support policy, and an extension catalog. The vendor is selling reduced integration risk and a clearer support path. The customer is buying a boundary where fewer teams have to debug whether the ingress controller, registry, CNI, and cluster upgrade process were meant to work together.

The phrase "undifferentiated heavy lifting" is useful here because many platform chores are necessary but not unique to the business. Every organization needs a secure ingress path, image provenance controls, upgrade testing, quota defaults, auditability, and incident response for the control plane. Very few organizations win customers because they wrote their own image trigger controller or maintained their own catalog of operator update channels. A distribution can be rational when it removes work that is expensive, repetitive, and not a source of business advantage.

The counterargument is equally serious. Integrated platforms encode assumptions. They shape how workloads are built, which APIs are first-class, how upgrades are sequenced, which operators are supported, and which failure modes the vendor will help with. The more a team leans into OpenShift-specific resources such as Routes, BuildConfigs, ImageStreams, Projects, and Security Context Constraints, the more migration work it accepts if it later moves to a vanilla Kubernetes stack. That is not automatically bad; it is a tradeoff that should be visible.

Support also has two meanings. Vendor support can help when a supported component fails, a documented upgrade path breaks, or a cluster operator enters a degraded state. Vendor support cannot make a poorly designed workload reliable, write your tenant model, or decide which teams deserve elevated privileges. Buying OpenShift does not replace platform engineering. It changes the platform team's work from assembling every component to governing an opinionated system and teaching teams how to use it well.

Lifecycle is the other large value proposition. In a hand-assembled Kubernetes platform, each component has its own release cadence, compatibility window, and operational owner. The CNI may have one upgrade rhythm, the ingress controller another, the registry another, and the GitOps controller another. OpenShift tries to make the cluster itself a managed product, with cluster operators, release channels, and documented upgrade paths. That reduces choice, but it also reduces the number of unsupported combinations a team can accidentally create.

Cost should be evaluated with the same discipline. Subscription cost is visible because it appears as a line item. Integration cost is often hidden because it appears as engineering time, delayed delivery, platform toil, and incident recovery. A fair comparison estimates both sides without invented precision. If a mature platform team already operates ingress, registry, monitoring, GitOps, policy, and upgrades well, OpenShift may duplicate investments. If a small team is drowning in integration work, the subscription may buy focus.

The most useful decision question is not whether OpenShift has more features than upstream Kubernetes. It does. The useful question is whether those features align with your operating model. A bank with regulated tenants, central operations, strict support expectations, and many product teams may value the opinionated defaults. A software company with a deep Kubernetes platform team, strong open-source integration skills, and custom internal tooling may prefer a thinner distribution plus carefully chosen upstream projects.

## Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.

Red Hat documentation currently lists OpenShift Container Platform 4.22 as the current documented release, and the 4.22 release notes state that it uses Kubernetes 1.35 with CRI-O. The 4.21 release notes show Kubernetes 1.34, and the 4.20 release notes show Kubernetes 1.33. Treat any older plan that calls 4.20 the latest general-availability release as stale, because the exact OpenShift minor and its Kubernetes mapping move faster than durable platform architecture principles.

OpenShift Container Platform is the commercial Red Hat product with subscription support, lifecycle policy, and certified Kubernetes conformance. OKD is the community distribution that serves as the upstream code base for OpenShift. The practical relationship for a learner is simple: OKD teaches the open community lineage, while OpenShift teaches the supported enterprise operating model that many organizations buy when they want a vendor-backed platform.

Feature rosters also move quickly. In the current documentation set, OpenShift documents integrated areas such as ingress and load balancing, images and ImageStreams, BuildConfig builds, Pipelines, GitOps, Operators, monitoring, logging, authentication, and cluster updates. Those areas are useful teaching anchors, but the exact operator versions, default feature status, and supported add-on combinations must be checked against current Red Hat documentation before a design is approved.

### Enterprise-distro Rosetta

| Durable capability | OpenShift | Vanilla Kubernetes | Rancher/RKE2 stack |
|--------------------|-----------|--------------------|--------------------|
| Routing and ingress | Routes through the OpenShift Router, plus Kubernetes Ingress and evolving Gateway API support | Kubernetes defines Service, Ingress, and Gateway APIs, but you install and operate controllers | RKE2 supplies Kubernetes; Rancher commonly manages ingress choices through charts and cluster configuration |
| Build system | BuildConfig and Source-to-Image remain OpenShift-specific workflow options, alongside newer build integrations | No built-in image build workflow; teams choose tools such as BuildKit, Kaniko, Tekton, or CI runners | Usually external CI/CD or Rancher-managed charts; image builds are not core RKE2 behavior |
| GitOps | OpenShift GitOps packages Argo CD through an Operator | Install Argo CD, Flux, or another controller yourself | Rancher includes Fleet and can also manage Argo CD or other GitOps tools |
| Operator catalog | OperatorHub and Operator Lifecycle Manager are central extension paths | OLM can be installed, but it is not part of upstream Kubernetes | Rancher catalogs and apps provide a separate packaging experience |
| Multi-tenancy model | Projects combine namespaces with OpenShift metadata, RBAC patterns, quotas, and platform conventions | Namespaces, RBAC, quotas, policies, and admission controls are assembled by the operator | Rancher adds projects and fleet-style management around RKE2 clusters |
| Security defaults | Security Context Constraints, SELinux integration, and restricted defaults are visible day-one constraints | Pod Security Admission, RBAC, admission webhooks, and node hardening depend on your baseline | RKE2 emphasizes hardened Kubernetes defaults, with Rancher policy and management layered above |

This Rosetta table is not a ranking. It is a translation aid. Each column can be a rational choice when it matches the team's operating model. OpenShift concentrates platform choices in a supported product. Vanilla Kubernetes maximizes composition freedom. Rancher with RKE2 emphasizes hardened Kubernetes plus multi-cluster management through a different control plane. The wrong choice is the one made without naming who owns integration, support, upgrade testing, and developer experience.

## OpenShift Architecture: Control Plane, Router, Registry, and Operators

OpenShift starts with the Kubernetes control plane, so the familiar objects still matter. Pods, Deployments, Services, ConfigMaps, Secrets, PersistentVolumeClaims, RBAC objects, admission, controllers, and CRDs remain the foundation. The `oc` CLI can run ordinary Kubernetes operations, and `kubectl` still works against the Kubernetes API. The difference is that OpenShift adds APIs, operators, defaults, and workflows that make the cluster behave like a complete application platform rather than a raw scheduler.

The control plane is operated through cluster operators. Each cluster operator owns an area such as authentication, console, ingress, image registry, monitoring, networking, or the cluster version itself. Operators report status through the cluster, which gives administrators a system-level view of whether the platform is Available, Progressing, or Degraded. This is one of the central OpenShift ideas: the platform is not only a pile of manifests, but a set of controllers that continuously reconcile desired cluster behavior.

```text
OPENSHIFT PLATFORM LAYERS

Developer workflow:
  oc CLI, web console, templates, S2I, Pipelines, GitOps

Platform APIs:
  Projects, Routes, BuildConfigs, ImageStreams, SCCs, OperatorHub

Kubernetes APIs:
  Pods, Deployments, Services, RBAC, NetworkPolicy, PVCs, CRDs

Cluster operators:
  authentication, console, ingress, image registry, monitoring, version

Infrastructure:
  RHCOS, CRI-O, machine management, storage, cloud or on-premises nodes
```

The Router is the OpenShift ingress path most learners notice first. A Kubernetes Service gives stable access inside the cluster. A Route tells the OpenShift Router to expose that service at an external hostname, often with TLS termination at the edge, passthrough TLS, or re-encryption from router to backend. The Router implementation is traditionally HAProxy-based, and the Ingress Operator manages the default ingress controller. That means a developer can often expose a service with one `oc expose` command while the platform team controls the router domain, certificates, placement, and policy.

Routes are not the same thing as Kubernetes Ingress. Ingress is a Kubernetes API that needs a controller, and different controllers implement different annotations and edge behavior. Routes are an OpenShift API with OpenShift-specific fields and conventions. Gateway API is the newer Kubernetes family of APIs for more expressive traffic management, and it is designed to improve portability across implementations. In practice, an OpenShift platform may support more than one exposure path, so the platform team should document which one teams should use for ordinary HTTP services.

The internal image registry and ImageStreams form another OpenShift-specific layer. A registry stores images. An ImageStream stores references, tags, and change history in the OpenShift API. That sounds like a small distinction until you use image-change triggers. A build can output to an ImageStreamTag, and a Deployment can react when that tag changes. The platform now has an API-level object that connects build output, image promotion, and rollout behavior without every team hard-coding registry digests by hand.

Source-to-Image, usually shortened to S2I, is a build workflow that combines source code with a builder image. Instead of every developer writing a Dockerfile, the platform provides a builder that knows how to assemble a Node.js, Java, Python, or other application into a runnable image. S2I is not the only valid build model, and many teams now use Dockerfiles, BuildKit, Tekton tasks, or external CI. The durable idea is that OpenShift includes a source-to-running-image path that can lower onboarding friction when teams fit the supported builder model.

OperatorHub and Operator Lifecycle Manager are the extension story. A Kubernetes Operator encodes operational knowledge for a component such as a database, queue, service mesh, or security tool. OperatorHub is the discovery and installation surface, while OLM handles subscription, install plans, catalog sources, and upgrade mechanics. This is powerful because it moves complex platform capabilities into a managed lifecycle. It also requires governance, because installing an Operator can add CRDs, controllers, permissions, and failure modes that affect the whole cluster.

The architecture lesson is that OpenShift turns many platform choices into first-class APIs. Routes, Projects, ImageStreams, BuildConfigs, SCCs, and OperatorHub are not decorative features. They are the mechanism by which Red Hat packages a supported platform opinion. A team choosing OpenShift should plan to teach those APIs clearly, because treating OpenShift like vanilla Kubernetes with a different logo leaves much of the value unused while keeping the cost and coupling.

## Routing: Routes, Ingress, and Gateway API

Routing is where the enterprise distribution tradeoff becomes visible to application teams. In vanilla Kubernetes, the platform team chooses an ingress controller, installs it, defines ingress classes, decides certificate handling, documents annotations, and explains how teams request hostnames. In OpenShift, the default path usually starts with the platform-provided Router and the Route API. That makes the common path shorter, but it also means teams learn OpenShift terminology and behavior.

```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: nodejs-demo
  namespace: demo-app
spec:
  host: nodejs-demo-demo-app.apps.example.com
  to:
    kind: Service
    name: nodejs-demo
  port:
    targetPort: 8080
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```

The Route above tells OpenShift to send external traffic for a hostname to a Service. Edge termination means the Router terminates TLS and sends traffic to the backend service inside the cluster. Passthrough termination keeps TLS encrypted all the way to the pod, which is useful when the application must present its own certificate. Re-encrypt termination terminates TLS at the router and establishes a second TLS connection to the backend. Those choices are operational policy decisions, not just YAML options.

OpenShift also supports Kubernetes Ingress, and teams may use Ingress when portability or ecosystem tooling matters. The tradeoff is that Ingress behavior often depends on controller-specific conventions, while Route behavior is specific to OpenShift. Gateway API aims to make routing more expressive and portable, especially when teams need richer separation between infrastructure owners and route owners. A durable platform standard should name the preferred API for ordinary web services, the exception path for advanced traffic management, and the migration plan as Gateway API support matures.

For learners, the main gotcha is assuming every OpenShift exposure path is a normal Ingress. When a manifest generated for kind or minikube uses an Ingress with annotations for NGINX, it may not match the OpenShift platform standard. The fix is not to panic or force every workload through the same controller. The fix is to ask which routing API the platform supports, who owns hostname and certificate policy, and what the application actually needs from the edge.

## ImageStreams, Registry, and Source-to-Image Build Flow

OpenShift's build and image model is easiest to understand as a chain of API objects. Source code enters through a BuildConfig. The build strategy may use S2I, Dockerfile builds, or another supported build path. The output lands in an ImageStreamTag. A Deployment can then follow that tag and roll out when a new image appears. This chain gives the platform an internal vocabulary for build input, build execution, image identity, and deployment triggers.

```text
SOURCE-TO-IMAGE FLOW

Git repository
  |
  v
BuildConfig with Source strategy
  |
  v
Builder image assembles application source
  |
  v
Result image pushed to internal registry
  |
  v
ImageStreamTag records the new image reference
  |
  v
Deployment rolls out the new image when policy allows it
```

This model is valuable when many teams need a simple path from source to application. A developer can start from a known builder image, avoid writing a Dockerfile on day one, and still get a real container image stored in the platform's registry. The platform team can curate builder images, registry access, base-image update behavior, and promotion patterns. The workflow is especially helpful for teaching because it exposes the difference between source code, build execution, image metadata, and runtime rollout.

```yaml
apiVersion: build.openshift.io/v1
kind: BuildConfig
metadata:
  name: nodejs-demo
  namespace: demo-app
spec:
  source:
    type: Git
    git:
      uri: https://github.com/sclorg/nodejs-ex.git
  strategy:
    type: Source
    sourceStrategy:
      from:
        kind: ImageStreamTag
        name: nodejs:20-ubi9
        namespace: openshift
  output:
    to:
      kind: ImageStreamTag
      name: nodejs-demo:latest
  triggers:
    - type: ConfigChange
    - type: ImageChange
```

The BuildConfig example is intentionally small. It assumes the cluster provides a suitable Node.js builder ImageStreamTag in the `openshift` namespace. In a real platform, the platform team should decide which builders are supported, how base-image updates are tested, how image scanning and signing fit into promotion, and when teams should move from S2I to a more explicit Dockerfile or Tekton build. S2I is a paved road, not a law.

ImageStreams are often confusing because they look like a registry feature but behave like an API abstraction. A registry tag points at image content. An ImageStreamTag can track, import, and trigger behavior around that content. This abstraction lets OpenShift react to image changes without every workload polling a registry. It also creates an OpenShift-specific dependency, so teams that require strong portability should know where they rely on ImageStreams and where they can use ordinary image references.

The practical teaching point is that OpenShift can provide an integrated build loop before an organization has a fully mature CI/CD platform. That can be a strong early advantage. As teams mature, they may still use OpenShift Pipelines, external CI, or GitOps promotion flows. The OpenShift value is not that every build must stay in BuildConfig forever. The value is that the platform includes a supported path that lets teams become productive while the delivery model evolves.

## OperatorHub and Operator Lifecycle Management

Operators are one of the places where OpenShift's product shape is strongest. Kubernetes makes it possible to extend the API with CRDs and controllers. OpenShift adds a catalog-centered lifecycle experience through OperatorHub and OLM. The result is a workflow where cluster administrators can discover an Operator, install it from a catalog, subscribe to an update channel, and expose a self-service API to application teams. That is very different from copying manifests from a README and hoping the upgrade path remains clear.

The benefit is repeatability. If a database Operator is installed through a supported catalog source, the platform has a record of the package, channel, subscription, install plan, and installed version. Administrators can inspect whether an Operator is healthy, whether an upgrade is pending, and which namespaces can use it. That matters in enterprise environments where auditability and supportability are part of the platform contract.

The risk is scope creep. Operators can be powerful enough to change cluster-wide behavior, create privileged pods, add admission webhooks, or manage infrastructure outside the cluster. A platform team should treat Operator installation as a change to the platform, not as a casual application deployment. The right process usually includes catalog policy, namespace scoping, upgrade-channel selection, rollback expectations, and a clear owner for the service that the Operator manages.

OpenShift's own cluster operators also teach the same reconciliation pattern. When the authentication operator, ingress operator, image registry operator, or cluster version operator reports a degraded condition, the platform team investigates the desired state, the observed state, and the controller's reason for failing. This is a useful mental model for all Kubernetes operations. The cluster is not a static set of files; it is a collection of controllers trying to make reality match declared intent.

```bash
oc get clusteroperators
oc describe clusteroperator ingress
oc get clusterversion
oc adm upgrade
```

These commands are day-two commands rather than developer commands. They help an administrator see whether the platform is healthy and which updates are available. They also show why OpenShift can feel more appliance-like than a hand-built cluster. The platform exposes status through supported APIs, but administrators still need to understand what the conditions mean and how changes can affect workloads.

## Designing Project-Based Multi-Tenancy with RBAC, Quotas, LimitRanges, and SCCs

OpenShift Projects are one of the first concepts developers encounter. A Project is backed by a Kubernetes namespace, but OpenShift adds metadata and conventions around requesting, displaying, and governing that namespace. The durable value is not the word "Project." The value is a tenant boundary that can carry RBAC, quota, limit, network, and security defaults in a way developers can understand.

In a healthy OpenShift platform, a Project is not just a folder for YAML. It is the unit where a team receives access, deploys workloads, consumes quotas, sees logs and metrics, and follows platform policy. Platform teams often create templates or automation that provisions a Project with default RoleBindings, ResourceQuotas, LimitRanges, NetworkPolicies, and service accounts. The exact mechanism varies, but the goal is constant: every tenant starts from a governed baseline instead of an empty namespace.

RBAC answers who can do what. A product team might get admin rights inside its own Project, edit rights in a staging Project, and view rights in a shared observability Project. Cluster-admin rights should be rare because a cluster-admin can cross tenant boundaries. OpenShift's web console and `oc` commands make role assignment visible, but the underlying model is still Kubernetes RBAC. Teams that already understand Roles, RoleBindings, ClusterRoles, and ClusterRoleBindings are well prepared to reason about Projects.

ResourceQuotas and LimitRanges answer how much a tenant can consume and what defaults apply. A ResourceQuota can cap total CPU requests, memory requests, object counts, persistent volume claims, or other resources inside a Project. A LimitRange can require or default requests and limits for containers. Together they protect the shared platform from accidental exhaustion. Without them, one noisy team can consume capacity, trigger autoscaling, or make scheduling unreliable for everyone else.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: demo-app
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-defaults
  namespace: demo-app
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      default:
        cpu: 500m
        memory: 512Mi
```

Security Context Constraints answer what a pod is allowed to ask from the node and kernel. SCCs predate Kubernetes Pod Security Admission and remain central in OpenShift. They control privileges such as running as root, using host namespaces, adding Linux capabilities, selecting SELinux behavior, and using certain volume types. A pod is admitted only if the user or service account can use an SCC that allows the requested security context.

The most common "works on kind, fails on OpenShift" failure is an image that expects to run as root. On many development clusters, a container image with `USER 0` or root-owned writable directories may start without complaint. On OpenShift, the default restricted model commonly runs workloads with a non-root UID and blocks privilege requests that are outside the allowed SCC. The application may fail at admission time, or it may start and then fail because it cannot write to a root-owned path.

The best fix is usually to repair the image, not to grant broad privileges. Build images so the application can run as an arbitrary non-root UID, write only to intended directories, and avoid privileged operations at runtime. For legacy software, a narrowly scoped service account with a more permissive SCC can be a temporary exception, but it should be reviewed like any other privilege escalation. The platform should make the secure path easy and the exception path explicit.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: root-demo
  namespace: demo-app
spec:
  containers:
    - name: ubi
      image: registry.access.redhat.com/ubi9/ubi:latest
      command: ["sleep", "3600"]
      securityContext:
        runAsUser: 0
```

On a default restricted Project, a pod like this is a teaching example for admission failure. The learner should inspect the error, identify that the pod requests root, and then decide whether the image can be changed. That process is more important than memorizing every SCC field. The platform skill is recognizing when security policy is protecting the cluster and when a workload needs a carefully governed exception.

## Building Developer Workflows with oc new-app, Templates, Pipelines, and GitOps

OpenShift's developer workflow starts with the `oc` CLI and the web console. The `oc` command includes Kubernetes-compatible operations and OpenShift-specific helpers. A developer can create a Project, deploy from source, expose a service, inspect a Route, start a build, read logs, and view rollout state without assembling every object manually. That is valuable for onboarding because it gives learners a guided path while still producing real Kubernetes and OpenShift resources.

```bash
oc new-project demo-app
oc new-app nodejs~https://github.com/sclorg/nodejs-ex.git --name=nodejs-demo
oc logs -f buildconfig/nodejs-demo
oc expose service/nodejs-demo
oc get route nodejs-demo
oc get deployment,service,route,imagestream,buildconfig
```

The command `oc new-app` is convenient, but it should be taught as scaffolding rather than magic. It detects source, creates build and deployment resources, and wires enough objects together to run the application. A platform team can use it for learning, demos, and simple workloads. For production, teams should commit the generated intent to Git, review it, and manage changes through a repeatable delivery process.

Templates are another OpenShift workflow primitive. A Template packages parameters and Kubernetes or OpenShift objects into a reusable starter. Templates can be useful when a team needs a simple self-service pattern and does not yet need a full operator. They are less powerful than Helm charts or Operators, but they are easy to understand: substitute parameters, create objects, and give teams a repeatable starting point.

```yaml
apiVersion: template.openshift.io/v1
kind: Template
metadata:
  name: simple-web-template
objects:
  - apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: ${APP_NAME}
    spec:
      replicas: 2
      selector:
        matchLabels:
          app: ${APP_NAME}
      template:
        metadata:
          labels:
            app: ${APP_NAME}
        spec:
          containers:
            - name: ${APP_NAME}
              image: ${IMAGE}
              ports:
                - containerPort: 8080
parameters:
  - name: APP_NAME
    value: simple-web
  - name: IMAGE
    value: registry.access.redhat.com/ubi9/httpd-24:latest
```

OpenShift Pipelines is the Tekton-based CI/CD path. Tekton models delivery as Kubernetes resources such as Tasks, Pipelines, PipelineRuns, and workspaces. That design matters because the pipeline itself becomes cluster-native API state rather than an external script hidden inside a CI server. OpenShift Pipelines packages that model for OpenShift and integrates it with the platform experience.

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: build-and-rollout
  namespace: demo-app
spec:
  params:
    - name: image
      type: string
  tasks:
    - name: rollout
      taskSpec:
        params:
          - name: image
            type: string
        steps:
          - name: update-deployment
            image: registry.redhat.io/openshift4/ose-cli:latest
            script: |
              oc set image deployment/nodejs-demo nodejs-demo=$(params.image)
      params:
        - name: image
          value: $(params.image)
```

The example is deliberately minimal because real pipelines need source workspaces, authentication, image build tasks, tests, promotion gates, and rollback strategy. The durable point is that OpenShift Pipelines uses Tekton CRDs, so pipeline behavior can be reviewed, versioned, and reconciled like other cluster resources. That makes it a good fit for teams that want Kubernetes-native delivery and understand the security implications of running build steps in cluster pods.

OpenShift GitOps packages Argo CD for declarative delivery. GitOps changes the workflow from "push commands into the cluster" to "commit desired state and let a controller reconcile it." On OpenShift, GitOps is often used for cluster configuration, tenant bootstrap, and application delivery. The platform team still needs to design repository structure, RBAC, secret handling, promotion flow, and drift policy. Installing Argo CD does not automatically create a delivery operating model.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nodejs-demo
  namespace: openshift-gitops
spec:
  project: default
  source:
    repoURL: https://github.com/example/platform-apps.git
    targetRevision: main
    path: apps/nodejs-demo
  destination:
    server: https://kubernetes.default.svc
    namespace: demo-app
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

The developer workflow story should end with a platform rule: scaffolding is for speed, Git is for memory, and policy is for shared safety. `oc new-app` can help a developer learn quickly. Templates can standardize common resources. S2I can remove early Dockerfile friction. Pipelines can build and test. GitOps can reconcile desired state. The platform team's job is to connect those tools into a workflow that developers can repeat without needing cluster-admin knowledge.

## Day-Two Operations: Cluster Operators, Upgrades, Monitoring, and Logging

Day-two operations decide whether a platform remains useful after the launch celebration. OpenShift's day-two model revolves around cluster operators, the Cluster Version Operator, supported update channels, and integrated observability components. That does not make operations automatic. It gives administrators a supported control surface for upgrades, health, monitoring, and logging that should be incorporated into runbooks and service reviews.

The Cluster Version Operator manages cluster update orchestration. Administrators inspect the current version, available updates, and channel information, then choose an update path that matches their risk tolerance. Fast channels expose updates earlier, stable channels wait for more signal, candidate channels exist for pre-release evaluation, and EUS channels matter for organizations that need longer support windows on selected even-numbered releases. The key practice is to test workload compatibility before treating any channel as a calendar reminder.

```bash
oc get clusterversion
oc describe clusterversion version
oc adm upgrade
oc adm upgrade --to-latest=true
```

Upgrade planning still belongs to the platform team. The team should review deprecated APIs, validate Operator compatibility, check disruption budgets, confirm node capacity during rolling updates, and communicate maintenance expectations to tenants. OpenShift can orchestrate much of the platform update, but it cannot know whether a product team's application depends on a removed API or an unsafe startup sequence. The strongest OpenShift teams build upgrade rehearsals into their normal operating rhythm.

Monitoring is integrated because OpenShift ships a supported monitoring stack for cluster components and can support user workload monitoring depending on configuration. The durable practice is to separate platform health from application health. Cluster operators, node pressure, API availability, router errors, and image registry health belong to the platform SLO. Application latency, error rate, and business symptoms belong to the product SLO. Good dashboards make both layers visible without mixing ownership.

Logging is similar. OpenShift logging can collect, forward, and store log data, but a platform team still has to decide retention, privacy boundaries, tenant access, and destination systems. Logs are often sensitive because they can contain identifiers, tokens, or business data. A good platform does not merely collect everything. It defines what is collected, where it goes, who can read it, how long it is kept, and how teams debug incidents without crossing tenant boundaries.

Day-two also includes support workflow. A supported distribution is most valuable when the organization preserves the evidence needed for support. That means keeping clusters in supported configurations, avoiding unreviewed modifications to platform-managed components, collecting must-gather data when appropriate, and documenting local changes. If a team heavily customizes the platform outside supported paths, it may keep the subscription cost while losing much of the support value.

## Patterns & Anti-Patterns

OpenShift works best when the platform team treats it as a product with opinionated paved roads. The strongest pattern is to define a small set of blessed workflows for ordinary teams: Project request, source-to-image or pipeline build, GitOps promotion, Route exposure, quota defaults, and observability access. Teams can still request exceptions, but the common path should be boring, documented, and supportable.

| Pattern | Why It Works | Practice Signal |
|---------|--------------|-----------------|
| Paved-road Projects | Every tenant starts with RBAC, quotas, limits, and security defaults | A new team can receive a usable Project without a custom ticket chain |
| Secure image baselines | Images are built to run as non-root and handle arbitrary UIDs | Fewer workloads need elevated SCC exceptions |
| Catalog governance | Operators are approved with owners, scope, and upgrade policy | OperatorHub remains an extension mechanism rather than a surprise factory |
| Git-backed delivery | Generated resources are committed and reviewed before promotion | `oc new-app` scaffolding becomes reproducible platform memory |
| Upgrade rehearsals | Clusters and workloads are tested before production channel moves | OpenShift updates become planned work rather than emergency archaeology |

The main anti-pattern is fighting the distribution. Teams sometimes buy OpenShift and then disable or bypass the opinions that make it useful. They install parallel ingress controllers without a standard, ignore Projects and quotas, grant broad SCCs to avoid fixing images, and run every add-on as if the cluster were a blank kubeadm installation. That creates the worst combination: OpenShift cost and coupling without OpenShift discipline.

| Anti-Pattern | Why It Hurts | Better Approach |
|--------------|--------------|-----------------|
| Blanket `anyuid` grants | It removes the most visible security guardrail for many workloads | Fix images first, then approve narrow service-account exceptions |
| Treating Routes as portable Ingress | It hides OpenShift-specific routing behavior until migration or tooling fails | Document Route, Ingress, and Gateway API use cases explicitly |
| Installing every appealing Operator | Operators add CRDs, permissions, controllers, and upgrade obligations | Require owner, scope, support tier, and rollback notes |
| Click-only production changes | Console actions vanish from review history and drift from Git | Use console for learning, then commit desired state to Git |
| Ignoring quotas | Shared clusters become vulnerable to noisy neighbors and accidental exhaustion | Apply ResourceQuotas and LimitRanges through Project automation |
| Customizing platform components casually | Unsupported changes can weaken the support contract and complicate upgrades | Prefer documented configuration APIs and record exceptions |

### Decision Framework

OpenShift earns its cost when integration risk is higher than subscription and adoption cost. That often happens in organizations with many application teams, strict compliance needs, limited platform headcount, regulated audit requirements, or a strong desire for one supported stack. OpenShift is also attractive when developer onboarding matters and the organization can benefit from opinionated source-to-route workflows, integrated console views, curated operators, and a single vendor support path.

Vanilla Kubernetes plus a platform team is often better when the organization already has mature internal platform capabilities. If the team operates ingress, registry, identity, monitoring, GitOps, policy, and upgrades well, OpenShift may add product constraints without enough operational savings. A modular stack can also fit teams that need unusual components, strong portability across distributions, or a deliberate avoidance of vendor-specific APIs. The price of that freedom is owning the integration work every release.

Use a decision record instead of a feature checklist. The record should name the workload classes, tenant model, compliance requirements, team skill level, upgrade ownership, support expectations, and exit strategy. It should also identify which OpenShift-specific APIs are acceptable. If Routes, ImageStreams, BuildConfigs, SCCs, and Projects become core to the platform, say so clearly. Portability is not free, and neither is avoiding useful platform features for the sake of theoretical neutrality.

## Did You Know?

- **OKD is the community lineage**: OKD documentation describes OKD as a Kubernetes distribution optimized for continuous application development and multi-tenant deployment, and as the upstream code base for Red Hat OpenShift products.
- **OpenShift 4.22 tracks Kubernetes 1.35**: Red Hat's 4.22 release notes list Kubernetes 1.35 with CRI-O, while earlier 4.20 documentation lists Kubernetes 1.33.
- **OpenShift Pipelines is Tekton-based**: Red Hat documents OpenShift Pipelines as a cloud-native CI/CD solution built from Tekton resources and CRDs.
- **SCCs remain a signature gotcha**: OpenShift documents Security Context Constraints as the mechanism that controls pod permissions, which is why root-running images often fail before they fail on permissive local clusters.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---------|---------|-----------------|
| Treating OpenShift as just another kubeconfig | Teams miss Projects, Routes, SCCs, ImageStreams, and operator lifecycle practices | Teach the OpenShift-specific APIs that your platform standard supports |
| Granting `anyuid` to every failing workload | The exception becomes the default security model | Fix images to run as non-root and approve narrow exceptions only when needed |
| Using `oc new-app` without committing the result | The cluster becomes the source of truth and review history disappears | Export, review, and manage desired state through Git or a template |
| Installing Operators without owners | CRDs and controllers linger after the original need fades | Require owner, support tier, namespace scope, and upgrade channel notes |
| Confusing Routes, Ingress, and Gateway API | Applications receive inconsistent edge behavior and certificate handling | Publish a routing standard with examples and exception criteria |
| Skipping quotas in shared Projects | One workload can consume resources intended for other tenants | Apply ResourceQuotas and LimitRanges during Project creation |
| Assuming vendor support replaces runbooks | Support needs evidence, supported configuration, and local context | Keep upgrade, must-gather, incident, and exception runbooks current |
| Comparing cost only by subscription | Hidden integration toil is ignored, or subscription cost is justified without evidence | Compare subscription, staffing, risk, portability, and delivery impact together |

## Quiz

### Question 1

A platform leader asks whether OpenShift is "worth it" because vanilla Kubernetes is free to download. How would you explain enterprise Kubernetes distribution integration, support, lifecycle, lock-in, and cost tradeoffs in a balanced answer?

<details>
<summary>Answer</summary>

Vanilla Kubernetes reduces product cost but leaves the organization responsible for integrating ingress, registry, identity, monitoring, logging, policy, GitOps, upgrades, and support workflows. OpenShift sells an integrated and supported lifecycle, which can reduce coordination toil when the organization lacks time or specialist capacity. The tradeoff is subscription cost, vendor-specific APIs, and a stronger dependency on Red Hat's supported paths. A balanced recommendation compares total operating cost and risk, not only license price or feature count.
</details>

### Question 2

An application team asks why OpenShift has Routes, ImageStreams, Source-to-Image, and OperatorHub when Kubernetes already has Services, container images, CI tools, and CRDs. How would you map OpenShift architecture across those pieces?

<details>
<summary>Answer</summary>

OpenShift starts with the Kubernetes control plane and adds productized APIs and operators around common platform needs. Routes expose Services through the OpenShift Router, ImageStreams track image tags and triggers in the API, Source-to-Image builds images from source with builder images, and OperatorHub provides a catalog-backed extension path. These pieces are not replacements for Kubernetes foundations; they are OpenShift's opinionated platform layer. The architecture is valuable when those opinions match the organization's desired developer workflow.
</details>

### Question 3

A team moves a container from kind to OpenShift, and the pod fails because the image expects to run as root. What should the platform team teach about project-based multi-tenancy, RBAC, quotas, LimitRanges, and SCCs?

<details>
<summary>Answer</summary>

The failure is likely caused by OpenShift's restricted security model and SCC admission, not by Kubernetes scheduling. The first fix should be to make the image run as an arbitrary non-root UID and write only to appropriate paths. The Project should also have RBAC, ResourceQuota, and LimitRange defaults so tenant access and consumption are governed consistently. A more permissive SCC should be a narrow service-account exception, not a broad workaround for every image problem.
</details>

### Question 4

A developer used `oc new-app` in a lab and now wants to use the same method for production. How should you build developer workflows with `oc new-app`, Templates, S2I, Pipelines, and GitOps without losing reviewability?

<details>
<summary>Answer</summary>

`oc new-app` is useful scaffolding because it quickly creates build, image, deployment, and service resources from source. Production workflow should capture the generated intent in Git, then use Templates, Tekton-based OpenShift Pipelines, or OpenShift GitOps for repeatable delivery. S2I can remain a paved road when builder images fit the application, but teams should understand what it creates. The platform standard should make the fast path reproducible rather than click-only or command-only.
</details>

### Question 5

A security team wants every product team isolated but does not want a separate cluster for each team. What OpenShift design would you propose, and what limits would you document?

<details>
<summary>Answer</summary>

Use Projects as tenant boundaries, backed by Kubernetes namespaces, RBAC, quotas, LimitRanges, NetworkPolicies where appropriate, and default SCC behavior. Document which roles teams receive, which service accounts can deploy, and what resource ceilings protect the shared cluster. Also document which requests require platform review, such as elevated SCCs, cluster-scoped Operators, or external routes. This design gives shared-cluster efficiency while keeping privilege and resource boundaries visible.
</details>

### Question 6

During an upgrade rehearsal, the Cluster Version Operator is healthy, but a product team's deployment fails after the new version. Who owns the problem, and how should OpenShift day-two operations handle it?

<details>
<summary>Answer</summary>

The vendor and platform own the supported cluster update path, but the product team and platform team still own workload compatibility. Day-two operations should include deprecated API checks, operator compatibility reviews, disruption-budget validation, and application smoke tests before production upgrades. The failure should become an upgrade-readiness improvement, not a reason to skip updates indefinitely. OpenShift provides the update machinery, but local workload evidence remains necessary.
</details>

### Question 7

A team wants to install a database Operator from OperatorHub because it is visible in the console. What governance question should be answered before installation?

<details>
<summary>Answer</summary>

The platform team should ask who owns the Operator, which namespaces it affects, which permissions it needs, which update channel it follows, and how incidents will be handled. Operators can add CRDs, controllers, webhooks, and privileged behavior, so installation changes the platform surface. OperatorHub makes discovery easier, but it does not remove the need for ownership and support policy. A small approval record prevents catalog sprawl from becoming day-two risk.
</details>

### Question 8

Your organization has a strong Kubernetes platform team, mature GitOps, established observability, and a strict portability requirement. How would you decide whether OpenShift earns its cost?

<details>
<summary>Answer</summary>

In that scenario, OpenShift may still be useful, but the case must be proven rather than assumed. Compare what OpenShift would replace against the platform capabilities the team already operates well. If OpenShift-specific APIs would violate portability goals or duplicate mature internal systems, vanilla Kubernetes plus selected upstream tools may be a better fit. If support, regulated defaults, or enterprise lifecycle requirements outweigh the duplication, OpenShift can still be justified with a clear decision record.
</details>

## Hands-On

This exercise assumes access to OpenShift Local or a training OpenShift cluster where you can create a Project. The commands use the `oc` CLI and intentionally stay inside a disposable `demo-app` Project. If your cluster has different builder ImageStreams or route domains, inspect the available tags and adapt only those environment-specific values.

- [ ] Create a Project with quota and limits, then verify that tenant defaults are visible with `oc describe quota` and `oc describe limitrange`.
- [ ] Deploy a sample Node.js application with `oc new-app`, inspect the BuildConfig, ImageStream, Deployment, Service, and Route, then explain how S2I connected source code to a running pod.
- [ ] Apply the root-running pod example in a disposable Project, capture the SCC-related failure, then fix the image or explain the narrow exception that would be required.
- [ ] Inspect cluster operator and version status with read-only commands, then write down which findings belong to platform health and which belong to application health.

```bash
oc new-project demo-app

cat <<'EOF' | oc apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-defaults
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      default:
        cpu: 500m
        memory: 512Mi
EOF

oc describe quota tenant-quota
oc describe limitrange tenant-defaults

oc new-app nodejs~https://github.com/sclorg/nodejs-ex.git --name=nodejs-demo
oc logs -f buildconfig/nodejs-demo
oc expose service/nodejs-demo
oc get deployment,service,route,imagestream,buildconfig
oc get route nodejs-demo
```

```bash
cat <<'EOF' | oc apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: root-demo
spec:
  containers:
    - name: ubi
      image: registry.access.redhat.com/ubi9/ubi:latest
      command: ["sleep", "3600"]
      securityContext:
        runAsUser: 0
EOF

oc get events --sort-by=.lastTimestamp
oc describe pod root-demo
```

```bash
oc get clusteroperators
oc get clusterversion
oc adm upgrade

oc delete project demo-app
```

## Sources

- [OpenShift Container Platform 4.22 documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22)
- [OpenShift Container Platform 4.22 release notes](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/release_notes/index)
- [OpenShift Container Platform 4.20 release notes](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html-single/release_notes/index)
- [Red Hat OpenShift Container Platform product page](https://www.redhat.com/en/technologies/cloud-computing/openshift/container-platform)
- [OKD documentation](https://docs.okd.io/)
- [OpenShift ingress and load balancing documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/ingress_and_load_balancing/index)
- [OpenShift images and ImageStreams documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/images/index)
- [OpenShift builds using BuildConfig documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/builds_using_buildconfig/index)
- [OpenShift authentication and authorization documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/authentication_and_authorization/index)
- [OpenShift Operators documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/operators/index)
- [OpenShift updating clusters documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/updating_clusters/index)
- [OpenShift monitoring documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/monitoring/index)
- [OpenShift logging documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/logging/index)
- [OpenShift Pipelines documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/pipelines/index)
- [Red Hat OpenShift GitOps documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_gitops/1.20)
- [Tekton Pipelines documentation](https://tekton.dev/docs/pipelines/)
- [Argo CD documentation](https://argo-cd.readthedocs.io/en/stable/)
- [RKE2 documentation](https://docs.rke2.io/)
- [Rancher Manager documentation](https://ranchermanager.docs.rancher.com/)
- [Kubernetes Gateway API documentation](https://kubernetes.io/docs/concepts/services-networking/gateway/)

## Next Module

Continue to [Module 14.6: Managed Kubernetes - EKS vs GKE vs AKS](../module-14.6-managed-kubernetes/) to compare managed control-plane services after seeing how a commercial distribution packages the broader platform.
