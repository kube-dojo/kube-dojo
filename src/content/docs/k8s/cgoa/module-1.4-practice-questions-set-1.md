---
title: "CGOA Practice Questions Set 1"
slug: k8s/cgoa/module-1.4-practice-questions-set-1
sidebar:
  order: 104
---

> **CGOA Track** | Practice questions | Set 1  
> **Complexity:** Beginner to intermediate  
> **Estimated time:** 45-60 minutes  
> **Prerequisites:** Basic Kubernetes objects, Git pull requests, YAML manifests, and the CGOA introduction modules

## Learning Outcomes

By the end of this module, you will be able to:

1. **Apply** the GitOps reconciliation model to decide whether a cluster change should be made through Git, CI, or a controller.
2. **Analyze** drift scenarios by comparing desired state in Git with actual state in a Kubernetes cluster.
3. **Compare** Helm, Kustomize, Argo CD, Flux, and CI/CD responsibilities when designing a delivery workflow.
4. **Evaluate** whether a pull-based or push-based deployment pattern is safer for a given environment.
5. **Debug** common GitOps practice-question traps by explaining why plausible answers are incomplete or misleading.

## Why This Module Matters

A platform team has just finished a migration from manual `kubectl apply` commands to GitOps. For the first week, everything looks cleaner: pull requests describe changes, reviewers can see the history, and application teams no longer need broad cluster credentials. Then a production incident starts with a small hotfix applied directly to the cluster. The fix works for ten minutes, but the GitOps controller notices that the live object no longer matches Git and quietly restores the previous configuration.

Nobody on the incident call thinks the controller is broken. It is doing exactly what it was designed to do. The real problem is that the team has not yet internalized the operating model. In GitOps, Git is not merely a convenient storage location for YAML. Git is the declared source of desired state, and reconciliation is the mechanism that keeps the cluster aligned with that declaration.

CGOA practice questions often test this distinction indirectly. A beginner may memorize that "GitOps uses Git" and still miss the exam question, because the correct answer usually includes desired state, continuous reconciliation, drift detection, and operational boundaries. A senior practitioner also needs that distinction in real work, because it determines who gets credentials, where rollbacks happen, how audit trails are preserved, and what should happen when the live cluster disagrees with the repository.

This module turns the first practice-question set into a teaching module. Instead of asking only short recall questions, it builds the mental model behind the answers. You will see how GitOps differs from a regular CI/CD pipeline, how drift appears in live clusters, why pull-based reconciliation reduces risk, and how common tools fit together without pretending they all do the same job.

## Core Content

### 1. GitOps Is an Operating Model, Not a Folder of YAML

The shortest weak definition of GitOps is "Kubernetes YAML stored in Git." That description is not completely false, but it is incomplete in the way a map without roads is incomplete. Git storage helps with history and review, but GitOps starts to matter when a controller continuously compares what Git says should exist with what the cluster actually has. The reconciliation loop is the part that changes Git from a file cabinet into an operating model.

A useful definition for the CGOA level is: GitOps is a pull-based operating model where desired state is declared in Git, reviewed through normal Git workflows, and continuously reconciled into the target environment by an automated controller. Each part of that sentence does work. "Desired state" says Git contains the intended outcome. "Reviewed through Git workflows" says changes are proposed and approved before becoming the new target. "Continuously reconciled" says the system keeps checking for mismatch instead of treating deployment as a one-time event.

The important consequence is that Git becomes the place where operators explain intent. If someone changes a Deployment replica count directly in the cluster, that action may be useful during an emergency, but it is not yet the desired state according to Git. A GitOps controller should notice the mismatch and either report it or correct it, depending on policy and configuration. That behavior is not a surprise feature; it is the core design.

```ascii
+------------------------+        +------------------------+
| Git repository         |        | Kubernetes cluster     |
|                        |        |                        |
| desired Deployment     |        | live Deployment        |
| replicas: 3            |        | replicas: 2            |
| image: app:v1.8        |        | image: app:v1.8        |
+-----------+------------+        +------------+-----------+
            |                                  ^
            | controller compares desired      |
            | state with live state            |
            v                                  |
+------------------------+                     |
| GitOps controller      |---------------------+
| detects drift          |
| plans reconciliation   |
+------------------------+
```

The diagram shows the shape of a common drift problem. Git says the Deployment should have three replicas, while the cluster currently has two. That mismatch may have been caused by a manual edit, a failed rollout, a temporary autoscaling experiment, or a partial restore. The GitOps controller does not need to know the human story before it can detect the technical mismatch. It compares desired state to live state and then follows its reconciliation policy.

**Active learning prompt:** Before reading further, decide what should happen if the live cluster has `replicas: 2` but Git still has `replicas: 3`. Should the controller leave the cluster alone because the live system is currently working, or should it restore the Git-declared value? Write down your answer and include the condition that would change your decision during a production incident.

A strong answer separates emergency response from desired-state management. During an incident, an operator might temporarily pause reconciliation, apply a direct fix, or change Git immediately through an expedited review. What should not happen is pretending that a direct cluster edit is automatically the new long-term state. If Git remains the source of truth, the durable fix must land in Git.

This is why practice questions that mention "a pull request was merged, but the cluster did not change" are testing more than Git knowledge. They are asking you to reason about the whole chain: Git commit, controller observation, manifest rendering, authorization, application to the cluster, health assessment, and status reporting. Missing any link can make the delivery fail while the repository still looks correct.

### 2. Desired State, Actual State, and Drift

Desired state is the configuration the organization says should exist. In GitOps, that configuration usually lives as Kubernetes manifests, Helm values, Kustomize overlays, policy files, or application definitions inside a Git repository. Actual state is what the cluster is currently running. Drift is the gap between those two states.

Drift can be harmless, intentional, dangerous, or simply misunderstood. A HorizontalPodAutoscaler changing the number of Pods is not the same kind of drift as a person manually changing a container image. A controller updating a status field is not the same kind of drift as an unreviewed change to a Service type. Good GitOps practice depends on knowing which fields are owned by Git, which fields are owned by Kubernetes controllers, and which differences should trigger action.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  namespace: shop
spec:
  replicas: 3
  selector:
    matchLabels:
      app: checkout
  template:
    metadata:
      labels:
        app: checkout
    spec:
      containers:
        - name: checkout
          image: registry.example.com/checkout:v1.8
          ports:
            - containerPort: 8080
```

Imagine this Deployment is the version stored in Git. If a teammate runs `kubectl scale deployment/checkout --replicas=2 -n shop`, the live `spec.replicas` field changes while Git remains unchanged. A GitOps controller that manages this Deployment can detect the difference because `spec.replicas` is part of the desired configuration. Depending on configuration, it may mark the application as out of sync, automatically restore three replicas, or wait for a human to approve synchronization.

Now imagine that the Deployment creates Pods and Kubernetes later writes status information such as available replicas, observed generation, and conditions. Those fields are not usually declared in Git because they are runtime observations. Treating every status difference as drift would create noise and confusion. GitOps is powerful because it is precise about ownership; it is not a blind text comparison between a YAML file and a live object dump.

A practical drift investigation starts by asking three questions. First, which object and field differ between Git and the cluster? Second, who is supposed to own that field: Git, a Kubernetes controller, an autoscaler, or a human operator during a break-glass event? Third, what should the reconciliation system do now: report, sync, pause, or escalate? These questions turn a vague "GitOps is broken" complaint into a concrete diagnosis.

```bash
kubectl -n shop get deployment checkout -o yaml
```

In KubeDojo modules, the `kubectl` command is often shortened to `k` after this first explanation. The alias is common in real exam and operations environments, but the full command is shown first so the intent is clear. If you use the alias locally, the same inspection command becomes:

```bash
k -n shop get deployment checkout -o yaml
```

A worked example makes the distinction clearer. Suppose Git contains `registry.example.com/checkout:v1.8`, but the live Deployment uses `registry.example.com/checkout:v1.9-hotfix`. The team needs to know whether that hotfix was applied directly during an incident, rendered by a newer Helm chart, or produced by a controller that mutates images. The correct next step is not automatically "roll back" or "force sync." The correct next step is to identify the owner and origin of the change.

If the hotfix was applied directly and should become permanent, the team should create a Git commit that declares the hotfix image. If the hotfix was unsafe, the team can sync back to the Git version. If the image was changed by an image automation controller, the team should inspect that controller's configuration and commit behavior. In all cases, the GitOps mental model gives the team a disciplined way to reason about state.

**Active learning prompt:** Your cluster is running image `checkout:v1.9-hotfix`, but Git still declares `checkout:v1.8`. Name two safe responses and one unsafe response. The safe responses should preserve auditability; the unsafe response should explain how the team could make future drift harder to understand.

### 3. GitOps and CI/CD Solve Different Problems

CI/CD and GitOps are often used together, which is why practice questions try to blur them. CI/CD usually answers: how do we build, test, package, scan, and publish software changes? GitOps answers: how do we declare the desired runtime state and keep the environment reconciled to it? A healthy platform can use both, but replacing one term with the other causes design mistakes.

A CI pipeline may compile code, run tests, build a container image, scan it for vulnerabilities, and publish it to a registry. It may then open a pull request that updates a Kubernetes manifest or Helm values file with the new image tag. At that point, GitOps takes over: a controller notices the merged change, renders the desired manifests if needed, compares them with the cluster, and applies changes according to policy.

```ascii
+-------------------+      +-------------------+      +-------------------+
| Source commit     |      | CI pipeline       |      | GitOps repo       |
| app code changes  |----->| test, build, scan |----->| desired runtime   |
|                   |      | publish image     |      | state changes     |
+-------------------+      +-------------------+      +---------+---------+
                                                                  |
                                                                  v
                                                        +-------------------+
                                                        | GitOps controller |
                                                        | reconcile cluster |
                                                        +---------+---------+
                                                                  |
                                                                  v
                                                        +-------------------+
                                                        | Kubernetes        |
                                                        | actual runtime    |
                                                        +-------------------+
```

The separation matters because credentials and responsibility differ. A CI system often needs access to source code, test services, artifact registries, and signing tools. A GitOps controller needs permission to read the desired-state repository and apply a scoped set of Kubernetes changes inside a target cluster. Giving the CI system direct production cluster-admin access because "it deploys things" collapses those boundaries and increases blast radius.

There are legitimate push-based deployment systems where CI applies manifests directly to a cluster. Those systems can work, and many organizations used them before adopting GitOps. The CGOA distinction is not that push-based CI is impossible. The distinction is that GitOps emphasizes a declared desired state and a reconciliation loop, commonly with a controller running in or near the target environment.

| Concern | CI/CD pipeline | GitOps controller |
|---|---|---|
| Primary job | Build, test, package, scan, and promote artifacts | Reconcile declared runtime state into the environment |
| Typical trigger | Source commit, tag, pull request, or release event | Git change, polling interval, webhook, or manual sync |
| Credential shape | Access to code, build secrets, registries, and test systems | Scoped access to target cluster resources and Git repository |
| Failure signal | Failed test, failed build, failed scan, failed publish | Out-of-sync app, failed apply, health degradation, drift |
| Audit focus | How the artifact was produced and promoted | Who changed desired state and what the cluster reconciled |

A common exam trap says that GitOps is "a replacement for CI/CD." That answer is too broad. GitOps can replace the deployment step of a push-based pipeline, but it does not replace compiling code, running tests, signing artifacts, or scanning images. In a mature platform, CI/CD and GitOps cooperate. CI produces trusted artifacts and proposes desired-state changes; GitOps reconciles those changes into Kubernetes.

The practical design question is where the handoff should happen. If CI updates a manifest in Git and stops, the GitOps controller becomes responsible for applying that declared change. If CI both updates Git and directly applies to the cluster, the team has two writers for the same state, which can create race conditions and confusing audit trails. The cleaner design gives one system ownership of each responsibility.

### 4. Pull-Based Reconciliation and Security Boundaries

Pull-based GitOps means the target environment, or a controller trusted by that environment, fetches desired state and reconciles it. This pattern is popular because it avoids giving an external CI runner broad inbound access to the cluster. Instead of pushing commands into the cluster from the outside, the controller pulls approved configuration from Git and applies it from inside a controlled boundary.

The security benefit is not magic. A pull-based model still needs credentials, repository access, Kubernetes RBAC, network connectivity, and careful secret handling. The improvement is about reducing where powerful credentials live and limiting which systems can directly mutate production. If a CI service is compromised, the attacker should not automatically gain direct production cluster access simply because the service can build application images.

```ascii
Push-oriented deployment
------------------------

+-------------------+        cluster credentials        +-------------------+
| External CI       |----------------------------------->| Kubernetes API    |
| runner            |        apply manifests            | production        |
+-------------------+                                   +-------------------+


Pull-oriented GitOps
--------------------

+-------------------+        reads desired state         +-------------------+
| GitOps controller |----------------------------------->| Git repository    |
| in target env     |                                   | reviewed changes  |
+---------+---------+                                   +-------------------+
          |
          | scoped Kubernetes RBAC
          v
+-------------------+
| Kubernetes API    |
| production        |
+-------------------+
```

A senior practitioner evaluates this pattern by threat model, not slogan. If the cluster cannot reach the Git repository, a pull model needs network design. If the GitOps controller has excessive RBAC, it can still cause serious damage. If secrets are stored unencrypted in Git, the model has failed an essential security requirement. Pull-based GitOps is safer when it is paired with least privilege, protected branches, signed commits or tags where appropriate, and secret-management controls.

The operational benefit is also significant. A controller can keep reconciling even when nobody is actively running a deployment job. It can report that an application is out of sync, retry transient failures, and expose health status. It gives operators a stable place to ask, "What does this environment think it should be running?" That question is harder to answer when several external systems can push changes independently.

Consider a production cluster behind a private network boundary. With a push model, the team must let a CI runner reach the API server or create a tunnel that effectively does the same thing. With a pull model, the cluster-side controller only needs to reach the repository and any required artifact sources. The exact network design varies by organization, but the direction of trust changes the risk discussion.

The CGOA exam will not expect you to design an entire enterprise network. It will expect you to recognize why "pull-based" is not just a deployment preference. It supports auditability, limits exposed credentials, aligns with reconciliation, and makes Git the place where reviewed desired-state changes enter the system.

### 5. Tool Responsibilities: Helm, Kustomize, Argo CD, and Flux

Tool questions become easier when you separate rendering tools from reconciliation controllers. Helm packages and templates Kubernetes resources, usually through charts and values. Kustomize customizes plain YAML through overlays and patches without requiring a template language. Argo CD and Flux are GitOps controllers that can watch repositories, render manifests through supported tools, compare desired and live state, and reconcile changes into clusters.

The tools can be combined. A repository might contain a Helm chart for a shared service, Kustomize overlays for environment-specific patches, and an Argo CD Application that points at the production path. Another platform might use Flux with HelmRelease resources to manage chart releases. The important exam skill is not memorizing every feature. It is identifying which layer a tool primarily occupies in a delivery design.

```ascii
+--------------------------+
| Desired-state repository |
|                          |
| charts/                  |
| overlays/                |
| apps/                    |
+------------+-------------+
             |
             v
+--------------------------+
| Render or customize      |
| Helm templates           |
| Kustomize overlays       |
+------------+-------------+
             |
             v
+--------------------------+
| GitOps reconciliation    |
| Argo CD or Flux          |
+------------+-------------+
             |
             v
+--------------------------+
| Kubernetes cluster       |
| live resources           |
+--------------------------+
```

Helm is often chosen when an application needs reusable packaging, configurable values, dependency management, and release conventions. A chart can define a Deployment, Service, ConfigMap, and other resources with values that differ by environment. The risk is that complex templates can hide what Kubernetes objects will actually be produced, so teams need rendering checks and review discipline.

Kustomize is often chosen when a team wants to start with readable base YAML and apply environment-specific changes as overlays. For example, a base Deployment might be shared across environments, while production adds a higher replica count and stricter resource requests. The benefit is that the final output remains close to Kubernetes YAML, but large overlay stacks can still become difficult to reason about if patches are scattered.

Argo CD and Flux are both used for GitOps reconciliation, but their user experience and resource models differ. At the CGOA level, you do not need to turn every comparison into a product debate. You should be able to say that both can reconcile desired state from Git into Kubernetes, both can work with common manifest-generation tools, and both are part of the controller layer rather than simply being YAML templating tools.

A common wrong answer says "Helm reconciles drift." Helm can install or upgrade a release, and Helm has release history, but plain Helm by itself is not the same as a continuously running GitOps reconciliation controller. A GitOps controller may use Helm to render manifests, then perform comparison and synchronization. The distinction is subtle enough to appear in practice questions and important enough to matter in platform design.

Another common wrong answer says "Kustomize manages secrets." Kustomize can generate Secret manifests from local inputs, but secret management in production usually needs a stronger pattern, such as sealed secrets, external secret operators, cloud secret stores, or another approved mechanism. The exam-level trap is over-assigning a tool responsibility because the tool can touch a resource type. Being able to render a Secret object is not the same as being a complete secret-management system.

### 6. Worked Example: Diagnosing a GitOps Practice Scenario

The following scenario combines the main ideas from this module. A team merges a pull request that changes the image tag for the `checkout` service from `v1.8` to `v1.9`. The CI pipeline has already built and scanned the image. Ten minutes later, the team sees that the cluster is still running `v1.8`, and the GitOps dashboard marks the application as out of sync.

A weak response is to say, "Run `kubectl set image` and fix it." That might update the cluster temporarily, but it bypasses the operating model and may create more drift. A stronger response starts with the reconciliation chain. Did the desired-state repository receive the correct image tag? Did the controller observe the new commit? Did the manifest render correctly? Did Kubernetes reject the apply because of RBAC, admission policy, missing image pull secret, or invalid YAML? Did the workload apply but fail health checks?

```bash
k -n argocd get applications
k -n shop get deployment checkout -o wide
k -n shop describe deployment checkout
k -n shop get events --sort-by=.lastTimestamp
```

These commands are examples of the kind of evidence an operator would collect. The exact namespace for the GitOps controller may differ, and Flux uses different custom resources from Argo CD. The teaching point is the sequence: inspect controller status, inspect the workload, inspect events, and compare live state with declared state. Jumping directly to manual mutation skips diagnosis.

Suppose the Application status says the rendered manifest contains `v1.9`, but Kubernetes events show an admission controller denied the update because the image lacks a required signature. The GitOps controller is not failing because it forgot the commit. It is failing because the cluster policy rejected the desired state. The correct fix is to satisfy the policy, update the artifact or signature process, and let reconciliation proceed. Manually forcing the image would violate the control the organization intentionally installed.

Now suppose the controller status says it never observed the new commit. The likely investigation moves toward repository access, branch configuration, path configuration, webhook delivery, polling interval, or controller logs. In that case, the Deployment itself may be healthy but stale. The fix is different because the failure happened before Kubernetes admission or workload rollout.

The worked example illustrates why scenario-based questions are better than recall questions. Real GitOps operations involve deciding where the failure sits in a chain. The correct answer depends on evidence, ownership, and the difference between desired and actual state.

**Active learning prompt:** In the scenario above, create a two-column note with "evidence points to repository/controller" on one side and "evidence points to Kubernetes/workload" on the other. Put at least three observations in each column. This forces you to separate synchronization failure from runtime failure.

### 7. How to Read CGOA Practice Questions Without Falling for Traps

Practice questions for this topic usually contain one correct answer and several answers that are partly true. The partly true options are the dangerous ones. "GitOps stores YAML in Git" is partly true. "A pull request is involved" is partly true. "Helm helps deploy applications" is partly true. The exam asks for the most accurate answer, so you need to choose the option that includes the mechanism and boundary conditions.

A reliable method is to underline the operating verb in the question. If the question asks what GitOps "is," look for desired state and reconciliation. If it asks what drift "means," look for mismatch between desired and actual state. If it asks why pull-based operation is preferred, look for credential boundary and controller-initiated reconciliation. If it asks how GitOps differs from CI/CD, look for runtime-state reconciliation rather than build and test automation.

You should also reject answers that use absolute claims without support. "GitOps eliminates all networking concerns" is wrong because the controller still needs network access to Git, registries, and the Kubernetes API. "GitOps does not use CI/CD" is wrong because the two patterns commonly cooperate. "Argo CD renders JSON only" is wrong because it invents an artificial limitation. Most low-quality distractors either exaggerate, swap tool responsibilities, or remove the reconciliation loop.

When you review your own wrong answers, do not stop at the correct option. Explain why every wrong option is wrong. This is one of the fastest ways to build exam readiness because it trains comparison rather than recognition. In real operations, the ability to reject a plausible but wrong diagnosis is often more valuable than remembering a slogan.

## Did You Know?

1. OpenGitOps principles emphasize a declarative desired state, versioned and immutable storage, automatic application, and continuous reconciliation.

2. A GitOps controller can report drift without automatically fixing it if the platform is configured for manual synchronization or approval gates.

3. Helm and Kustomize can both produce Kubernetes manifests, and GitOps controllers can use either one as part of the rendering step.

4. Pull-based GitOps reduces the need for external systems to hold direct cluster credentials, but it still requires careful RBAC and secret-management design.

## Common Mistakes

| Mistake | Why it causes trouble | Better practice |
|---|---|---|
| Defining GitOps as "YAML in Git" only | This misses the reconciliation loop, which is the mechanism that keeps the cluster aligned with declared intent. | Include desired state, Git review, and continuous reconciliation in the definition. |
| Treating CI/CD and GitOps as the same thing | CI/CD may build and publish artifacts, while GitOps reconciles runtime state into an environment. | Design an explicit handoff from artifact promotion to desired-state change. |
| Manually fixing drift without updating Git | The live cluster may work briefly, but the controller can restore the previous Git-declared value. | Make durable changes through Git or intentionally pause reconciliation during break-glass work. |
| Giving CI broad production cluster credentials | A compromised CI runner can become a direct production mutation path. | Prefer scoped controller credentials and pull-based reconciliation where appropriate. |
| Assuming every live difference is bad drift | Some fields are owned by Kubernetes controllers, autoscalers, or status updates rather than Git. | Identify field ownership before deciding whether to sync, ignore, or investigate. |
| Saying Helm or Kustomize is the GitOps controller | These tools can render or customize manifests, but they do not by themselves provide the full reconciliation loop. | Pair rendering tools with a controller such as Argo CD or Flux when implementing GitOps. |
| Choosing answers that are only partly true | Practice-question distractors often mention Git, pull requests, or YAML while omitting the operating mechanism. | Prefer answers that explain the complete model and reject incomplete slogans. |
| Ignoring failed health or admission signals | A repository change can be correct while the cluster rejects or fails to run the resulting workload. | Trace the chain from Git commit to render, apply, admission, rollout, and health. |

## Quiz

### 1. A developer changes a Deployment image directly with `kubectl set image` during an incident. The GitOps controller later changes it back to the older image from Git. What is the best explanation?

1. The GitOps controller failed because it should always preserve live emergency changes.
2. The controller reconciled the cluster back to the desired state declared in Git.
3. Helm automatically rejected the hotfix because Helm owns all image fields.
4. CI/CD rebuilt the old image and forced it into the cluster.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The direct cluster change created drift because Git still declared the older image. A GitOps controller is expected to detect that mismatch and reconcile according to its policy. If the hotfix should become durable, the team needs to update Git or intentionally pause reconciliation during the emergency process.
</details>

### 2. Your CI pipeline successfully builds and scans an image, then opens a pull request that updates a Helm values file. After the pull request merges, the cluster does not change. Which investigation sequence best matches a GitOps mental model?

1. Re-run unit tests, delete the namespace, and apply the manifests manually.
2. Check whether the controller observed the commit, rendered the desired manifests, and encountered apply or health errors.
3. Disable branch protection because Git review is slowing down deployment.
4. Move all Kubernetes credentials into the CI system so it can bypass the controller.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The failure happened after artifact creation, so the investigation should follow the reconciliation path. The controller must observe the commit, render the desired state, compare it with live state, apply changes, and report health. Manual bypasses may hide the actual failure and create more drift.
</details>

### 3. A platform team is deciding between a push-based CI deployment and a pull-based GitOps controller for production. Their main concern is reducing direct production credentials in external systems. Which recommendation is strongest?

1. Use pull-based GitOps so the cluster-side controller reconciles reviewed desired state with scoped Kubernetes permissions.
2. Use push-based CI because external runners never need credentials when applying manifests.
3. Avoid Git because Git repositories cannot represent desired state safely.
4. Use manual `kubectl apply` because humans are easier to audit than commits.

<details>
<summary>Answer</summary>

**Correct answer: 1**

Pull-based GitOps can reduce the need for external CI systems to hold direct production cluster credentials. The controller still needs carefully scoped permissions, but the trust boundary is cleaner than giving broad production mutation rights to an outside runner.
</details>

### 4. Your team sees that a GitOps dashboard marks an application as out of sync, but the workload is healthy. Git declares `replicas: 3`, while the live Deployment has `replicas: 2` because someone scaled it during a traffic drop. What should the team do first?

1. Decide who owns the replica field and whether the temporary live change should be committed, reverted, or handled through an autoscaler.
2. Delete the Deployment so the controller must recreate it from Git.
3. Ignore the warning permanently because a healthy workload can never be drifted.
4. Remove the Deployment from Git because Git cannot represent replica counts.

<details>
<summary>Answer</summary>

**Correct answer: 1**

The team should analyze ownership and intent before acting. If Git owns `spec.replicas`, the live value is drift unless an approved process changes the desired state. The durable response may be a Git commit, a sync back to Git, or a design change such as using an autoscaler.
</details>

### 5. A practice question asks which pairing is most accurate for common Kubernetes delivery tools. Which option should you choose?

1. Helm templates charts and values, while Kustomize applies overlays and patches to YAML.
2. Argo CD is only a JSON renderer, while Flux is only a YAML renderer.
3. Kustomize is a complete production secret manager by default.
4. Helm is the same thing as a continuously running GitOps reconciliation controller.

<details>
<summary>Answer</summary>

**Correct answer: 1**

Helm and Kustomize are commonly used to produce or customize manifests before reconciliation. Argo CD and Flux are examples of GitOps controllers that may use rendering tools. The other answers exaggerate or swap responsibilities.
</details>

### 6. A GitOps controller reports that the desired manifest uses image `payments:v2.3`, but Kubernetes events show the update was denied by an admission policy requiring signed images. What is the best next action?

1. Bypass the controller with a direct `kubectl set image` command.
2. Fix the artifact signing or policy compliance issue, then let reconciliation apply the desired state.
3. Delete the admission controller because GitOps and policy controls cannot work together.
4. Change the dashboard status manually so the application appears healthy.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The repository and render step may be correct, but the cluster rejected the change for policy reasons. The right fix is to satisfy the policy or correct the desired state, not bypass the controls. GitOps and admission control can work together when the delivery chain produces compliant artifacts.
</details>

### 7. A teammate answers a GitOps definition question with "GitOps means every deployment uses pull requests." Why is that answer insufficient?

1. Pull requests are unrelated to audit history.
2. The answer mentions review workflow but omits desired state and continuous reconciliation.
3. GitOps forbids pull requests and requires direct commits.
4. Pull requests only work for Helm, not for Kustomize.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Pull requests are often part of GitOps workflows, but they are not the whole model. The answer must include declared desired state and a reconciliation loop that compares and applies that state to the environment.
</details>

### 8. A team uses CI to build images, update a manifest repository, and then directly apply the same manifests to the cluster while Argo CD also watches the repository. What is the main design risk?

1. There are two systems writing the same runtime state, which can create unclear ownership and confusing drift behavior.
2. Kubernetes cannot run manifests that were created by CI.
3. Git repositories can only be watched by Flux, not Argo CD.
4. Helm and Kustomize stop working when CI is present.

<details>
<summary>Answer</summary>

**Correct answer: 1**

When CI directly applies manifests and a GitOps controller also reconciles them, ownership becomes muddy. A cleaner design lets CI produce artifacts and propose desired-state changes, while the GitOps controller owns reconciliation into the cluster.
</details>

## Hands-On Exercise

In this exercise, you will practice diagnosing a GitOps scenario without needing a real cluster. The goal is to reason from evidence, identify drift, and choose a response that preserves the operating model. You can complete it in a text editor, but the commands shown are runnable in a Kubernetes environment if you want to adapt the scenario later.

### Scenario

The `checkout` service is managed by a GitOps controller. The desired state in Git declares three replicas and image `registry.example.com/checkout:v1.8`. During a traffic incident, an operator manually changed the live Deployment to two replicas and image `registry.example.com/checkout:v1.9-hotfix`. The application is currently responding to traffic, but the GitOps dashboard reports the app as out of sync.

### Step 1: Write the Desired and Actual State

Create a short comparison using the following structure. The point is not to produce perfect YAML; the point is to identify the fields that matter and classify the mismatch.

```yaml
desired_state:
  source: Git
  deployment: checkout
  namespace: shop
  replicas: 3
  image: registry.example.com/checkout:v1.8

actual_state:
  source: Kubernetes API
  deployment: checkout
  namespace: shop
  replicas: 2
  image: registry.example.com/checkout:v1.9-hotfix
```

- [ ] You identified at least two fields that differ between desired and actual state.
- [ ] You marked Git as the source of desired state.
- [ ] You marked the Kubernetes API as the source of actual state.
- [ ] You avoided calling the live state "correct" just because the app is currently responding.

### Step 2: Classify the Drift

Write three sentences explaining whether each changed field should be considered drift. Your answer should mention field ownership. For example, a manually changed image is usually drift if Git owns the Deployment spec. A manually changed replica count is also drift if Git owns `spec.replicas`, unless the team has intentionally delegated replica ownership to an autoscaler or another approved process.

- [ ] You explained why the image difference is operationally important.
- [ ] You explained why the replica difference may need a different response if an autoscaler owns replica count.
- [ ] You separated runtime health from desired-state agreement.

### Step 3: Choose a Safe Response

Choose one of the following response paths and justify it in four to six sentences.

1. Commit `v1.9-hotfix` and the replica decision to Git after expedited review.
2. Sync the cluster back to Git because the manual change was not approved and should not persist.
3. Pause reconciliation briefly, investigate the incident, then either commit the desired change or revert to Git.

A strong answer explains why the chosen path preserves auditability. It also explains what could go wrong if the team silently keeps manual cluster changes without updating Git. If you choose to pause reconciliation, include the condition that tells the team when to unpause it.

- [ ] Your response includes a Git-based durable action or a clear rollback to Git.
- [ ] Your response avoids direct mutation as the final long-term fix.
- [ ] Your response names the operational risk of leaving Git stale.
- [ ] Your response includes how the team communicates or records the decision.

### Step 4: Map the Tool Responsibilities

For the same scenario, assign each responsibility to CI/CD, Helm or Kustomize, and the GitOps controller. If a responsibility does not belong to a tool, say so directly.

| Responsibility | Best owner |
|---|---|
| Build and scan the container image | CI/CD pipeline |
| Store reviewed desired runtime state | Git repository |
| Render chart templates or overlays | Helm or Kustomize |
| Compare desired state with live state | GitOps controller |
| Apply approved desired state to the cluster | GitOps controller |
| Own emergency human decision-making | Incident process, not a tool |

- [ ] You did not assign image building to the GitOps controller.
- [ ] You did not describe Helm or Kustomize as full reconciliation controllers by themselves.
- [ ] You described Git as the reviewed desired-state store.
- [ ] You described the controller as the system that compares and reconciles.

### Step 5: Turn the Scenario Into an Exam-Ready Explanation

Write a final answer as if you were explaining the scenario to a teammate preparing for CGOA. Your explanation should define GitOps, define drift, distinguish GitOps from CI/CD, and explain why pull-based reconciliation helps with security boundaries. Keep the explanation practical rather than slogan-based.

- [ ] Your explanation includes desired state and continuous reconciliation.
- [ ] Your explanation defines drift as mismatch between desired and actual state.
- [ ] Your explanation distinguishes CI artifact work from GitOps runtime reconciliation.
- [ ] Your explanation explains pull-based security benefits without claiming it removes all risk.
- [ ] Your explanation uses the scenario evidence rather than generic definitions only.

## Next Module

Continue with [CGOA Practice Questions Set 2](./module-1.5-practice-questions-set-2/).
