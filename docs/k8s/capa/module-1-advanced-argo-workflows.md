# Module 1: Advanced Argo Workflows

> **CAPA Track -- Domain 1 (36%)** | Complexity: `[COMPLEX]` | Time: 50-60 min

The platform team at a fintech company had a problem. Their nightly reconciliation workflow ran 14 steps sequentially, took 3 hours, and failed silently twice a week. Nobody knew until morning standup. After migrating to Argo Workflows with exit handlers for Slack alerts, CronWorkflows for scheduling, memoization to skip unchanged steps, and lifecycle hooks for audit logging, the pipeline shrank to 40 minutes. Failures triggered immediate notifications, and transient errors retried automatically. The team went from 12 hours per week of pipeline babysitting to zero.

## Prerequisites

- [Module 3.3: Argo Workflows](../../platform/toolkits/ci-cd-pipelines/module-3.3-argo-workflows.md) -- Container, Script, Steps, DAG, Artifacts
- Kubernetes RBAC basics (ServiceAccounts, Roles)
- CronJob scheduling syntax

## Why This Module Matters

The CAPA exam dedicates 36% to Domain 1, covering Argo Workflows in depth. Module 3.3 taught the fundamentals. This module covers everything else: remaining template types, scheduled workflows, reusable templates, exit handlers, synchronization, memoization, lifecycle hooks, variables, retry strategies, and security.

## Did You Know?

- **Argo Workflows supports 7 template types** -- most teams only use 2-3, but the CAPA exam expects all of them
- **CronWorkflows are not Kubernetes CronJobs** -- they are a separate CRD creating Workflow objects on a schedule
- **Memoization has a hard 1MB limit per entry** -- ConfigMap values are capped at 1MB; exceed it and your workflow fails cryptically
- **Expression tags use expr-lang, not Go templates** -- `{{=expression}}` gives you conditionals, math, and string ops inline

## Remaining Template Types

Module 3.3 covered Container, Script, Steps, and DAG. Here are the rest.

### Resource Template

Performs CRUD on Kubernetes resources directly -- no kubectl container needed.

```yaml
- name: create-configmap
  resource:
    action: create          # create | patch | apply | delete | get
    manifest: |
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: output-{{workflow.name}}
      data:
        result: "done"
    successCondition: "status.phase == Active"
    failureCondition: "status.phase == Failed"
```

The `successCondition`/`failureCondition` fields use jsonpath -- useful with Jobs or CRDs where you wait for a status field.

### Suspend Template

Pauses execution until manually resumed or a duration elapses. This is how you build approval gates.

```yaml
- name: approval-gate
  suspend:
    duration: "0"     # Wait indefinitely until resumed
- name: timed-pause
  suspend:
    duration: "30m"   # Auto-resume after 30 minutes
```

Resume from CLI: `argo resume my-workflow -n argo`

### HTTP Template

Makes HTTP requests without spinning up a container. Requires the Argo Server.

```yaml
- name: call-webhook
  http:
    url: "https://api.example.com/notify"
    method: POST
    headers:
      - name: Authorization
        valueFrom:
          secretKeyRef: {name: api-creds, key: token}
    body: '{"workflow": "{{workflow.name}}", "status": "{{workflow.status}}"}'
    successCondition: "response.statusCode >= 200 && response.statusCode < 300"
```

### ContainerSet Template

Multiple containers in a single pod sharing volumes. Like init-containers with dependency ordering.

```yaml
- name: multi-container
  containerSet:
    volumeMounts:
      - name: workspace
        mountPath: /workspace
    containers:
      - name: clone
        image: alpine/git
        command: [sh, -c, "git clone https://github.com/org/repo /workspace/repo"]
      - name: build
        image: golang:1.22
        command: [sh, -c, "cd /workspace/repo && go build ./..."]
        dependencies: [clone]
      - name: test
        image: golang:1.22
        command: [sh, -c, "cd /workspace/repo && go test ./..."]
        dependencies: [clone]
  volumes:
    - name: workspace
      emptyDir: {}
```

Key difference from DAG: all containers share one pod -- shared filesystem without artifacts, but limited to one node's resources.

### Data and Plugin Templates

**Data** sources data from artifact storage with transformations (e.g., filtering S3 files). **Plugin** extends Argo via executor plugins registered on the cluster. Both are less common on exams but know they exist.

## CronWorkflow

CronWorkflows create Workflow objects on a schedule -- their own CRD, not a wrapper around K8s CronJobs.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: nightly-etl
spec:
  schedule: "0 2 * * *"           # 2 AM daily
  timezone: "America/New_York"    # Default: UTC
  startingDeadlineSeconds: 300    # Skip if missed by >5min
  concurrencyPolicy: Replace      # Kill previous if still running
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  workflowSpec:
    entrypoint: main
    templates:
      - name: main
        dag:
          tasks:
            - name: extract
              template: run-etl
            - name: load
              template: run-etl
              dependencies: [extract]
      - name: run-etl
        container:
          image: etl-runner:v3
          command: [python, run.py]
```

| Concurrency Policy | Behavior |
|---|---|
| `Allow` | Multiple concurrent runs permitted |
| `Forbid` | Skip new run if previous still active |
| `Replace` | Kill running workflow, start new one |

**Backfill**: CronWorkflows do not backfill missed runs. Manual trigger: `argo submit -n argo --from cronwf/nightly-etl`

## WorkflowTemplate and ClusterWorkflowTemplate

**WorkflowTemplate** is namespace-scoped; **ClusterWorkflowTemplate** is cluster-scoped (accessible from any namespace).

Reference an entire template as your workflow:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: ci-run-
spec:
  workflowTemplateRef:
    name: build-test-deploy       # WorkflowTemplate
  # clusterScope: true            # Add for ClusterWorkflowTemplate
  arguments:
    parameters:
      - name: image-tag
        value: ghcr.io/org/app:v1.2.3
```

Reference individual templates within a DAG using `templateRef`:

```yaml
dag:
  tasks:
    - name: scan
      templateRef:
        name: org-standard-ci
        template: security-scan
        clusterScope: true
      arguments:
        parameters: [{name: image, value: "myapp:latest"}]
```

Templates are resolved at submission time -- updating a WorkflowTemplate does not affect running workflows.

## Exit Handlers

Run at workflow end regardless of outcome. Specified via `spec.onExit`.

```yaml
spec:
  entrypoint: main
  onExit: exit-handler
  templates:
    - name: main
      container:
        image: alpine
        command: [sh, -c, "echo 'working'"]
    - name: exit-handler
      steps:
        - - name: success-notify
            template: notify
            when: "{{workflow.status}} == Succeeded"
          - name: failure-notify
            template: alert
            when: "{{workflow.status}} != Succeeded"
```

`{{workflow.status}}` resolves to `Succeeded`, `Failed`, or `Error` inside exit handlers.

## Synchronization

### Mutex -- exclusive lock, one workflow at a time:

```yaml
spec:
  synchronization:
    mutex:
      name: deploy-production
```

### Semaphore -- N concurrent holders, backed by a ConfigMap:

```yaml
# ConfigMap: data: { gpu-jobs: "3" }
spec:
  synchronization:
    semaphore:
      configMapKeyRef:
        name: semaphore-config
        key: gpu-jobs
```

Both can be applied at workflow level or template level.

## Memoization

Cache step outputs in a ConfigMap. If inputs match, skip execution.

```yaml
- name: expensive-step
  memoize:
    key: "{{inputs.parameters.dataset}}-{{inputs.parameters.version}}"
    maxAge: "24h"
    cache:
      configMap:
        name: memo-cache
  inputs:
    parameters: [{name: dataset}, {name: version}]
  container:
    image: processor:v2
    command: [python, process.py]
  outputs:
    parameters:
      - name: result
        valueFrom:
          path: /tmp/result.json
```

Constraints: **1MB limit** per entry (ConfigMap cap), only **output parameters** cached (not artifacts), `maxAge: "0"` for infinite TTL.

## Lifecycle Hooks

Execute actions when a template starts or finishes, without modifying the main logic.

```yaml
- name: deploy
  hooks:
    running:
      template: log-start
    exit:
      template: log-completion
      expression: "steps['deploy'].status == 'Failed'"  # Conditional
  container:
    image: bitnami/kubectl
    command: [kubectl, apply, -f, /manifests/]
```

Triggers: `running` (node starts), `exit` (node finishes regardless of outcome).

## Variables: Simple Tags vs Expression Tags

**Simple tags** (`{{...}}`) -- plain string substitution:

```yaml
"{{workflow.name}}"                  "{{workflow.status}}"
"{{inputs.parameters.my-param}}"     "{{tasks.task-a.outputs.result}}"
```

**Expression tags** (`{{=...}}`) -- evaluate expr-lang expressions:

```yaml
"{{=workflow.status == 'Succeeded' ? 'PASS' : 'FAIL'}}"
"{{=asInt(inputs.parameters.replicas) + 1}}"
"{{=sprig.upper(workflow.name)}}"
```

Use simple tags for references. Use expression tags for conditionals, math, or string manipulation.

## Retry Strategies

```yaml
- name: call-api
  retryStrategy:
    limit: 5
    retryPolicy: OnError         # See table
    backoff:
      duration: 10s              # Initial delay
      factor: 2                  # Multiplier per retry
      maxDuration: 5m            # Cap
    affinity:
      nodeAntiAffinity: {}       # Retry on different node
  container:
    image: curlimages/curl
    command: [curl, -f, "https://api.example.com/process"]
```

| Policy | Retries on... |
|---|---|
| `Always` | Any failure (non-zero exit, OOM, node failure) |
| `OnFailure` | Non-zero exit code only |
| `OnError` | System errors (OOM, node failure), NOT non-zero exit |
| `OnTransientError` | Transient K8s errors only (pod eviction) |

## Security

**Per-workflow service accounts** for least privilege:

```yaml
spec:
  serviceAccountName: argo-deployer       # Workflow-level
  templates:
    - name: build-step
      serviceAccountName: argo-builder    # Template-level override
```

**Pod security contexts**:

```yaml
- name: secure-step
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
  container:
    image: my-app:v1
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: [ALL]
```

Resource templates need RBAC on the resources they manage -- create a Role granting only the required verbs on specific resources, and bind it to the workflow's ServiceAccount.

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| `Always` retry for logic errors | Bad code retries forever | `OnError` for infra, `OnFailure` for self-healing bugs |
| Memoized outputs > 1MB | ConfigMap silently fails | Keep memoized outputs small; artifacts for large data |
| CronWorkflow without `startingDeadlineSeconds` | Missed runs vanish silently | Set deadline, monitor for skips |
| Single SA for all workflows | One compromise = full access | Least-privilege SA per workflow |
| Missing `clusterScope: true` in templateRef | ClusterWorkflowTemplate ref fails | Always set when referencing cluster-scoped |
| Exit handler uses artifacts | Artifacts may not be available | Pass data via parameters or external store |
| Mutex name collisions across teams | Unrelated workflows block each other | Namespace mutex names: `team-a/deploy-prod` |
| Unquoted expression tags | YAML parser breaks on `{{=...}}` | Always quote: `"{{=expr}}"` |

## Quiz

### Question 1: What is the difference between a Resource template and a Container running kubectl?

<details><summary>Show Answer</summary>
Resource templates operate through the API server directly -- no container, no image pull, supports `successCondition`/`failureCondition` for watching status. Container+kubectl is heavier but allows shell scripting. Use Resource for simple CRUD, Container for complex logic.
</details>

### Question 2: Write the CronWorkflow spec for 3 AM UTC weekdays, skip if missed by >10 min.

<details><summary>Show Answer</summary>

```yaml
spec:
  schedule: "0 3 * * 1-5"
  timezone: "UTC"
  startingDeadlineSeconds: 600
  concurrencyPolicy: Forbid
```
</details>

### Question 3: How does memoization work, and what is its key limitation?

<details><summary>Show Answer</summary>
Caches output parameters in a ConfigMap keyed by a user-defined key. On cache hit (matching key, not expired), returns cached output without executing. Key limitation: **1MB per entry** (ConfigMap value cap). Only output parameters are cached, not artifacts.
</details>

### Question 4: Explain `{{workflow.name}}` vs `{{=workflow.name}}`.

<details><summary>Show Answer</summary>
`{{workflow.name}}` is simple string substitution. `{{=workflow.name}}` evaluates an expr-lang expression -- identical for simple refs, but expression tags enable logic: `"{{=workflow.status == 'Succeeded' ? 'PASS' : 'FAIL'}}"`.
</details>

### Question 5: Limit GPU training workflows to 4 concurrent. How?

<details><summary>Show Answer</summary>
Create ConfigMap with `data: { gpu: "4" }`, then use `spec.synchronization.semaphore.configMapKeyRef` pointing to that key. Fifth workflow queues until one completes. ConfigMap value can be changed at runtime.
</details>

### Question 6: What happens when an exit handler fails?

<details><summary>Show Answer</summary>
The workflow's final status becomes `Error`. Design robust exit handlers: add retries, use HTTP templates for speed, keep logic minimal. For critical notifications, use a fallback (dead-letter queue or persistent store).
</details>

### Question 7: A WorkflowTemplate is updated after a workflow starts. Old or new version?

<details><summary>Show Answer</summary>
**Old version.** Templates are resolved at submission time and stored in the Workflow object. Updates do not affect in-flight workflows.
</details>

### Question 8: Write a retry strategy: 3 retries, 30s exponential backoff capped at 5m, different nodes.

<details><summary>Show Answer</summary>

```yaml
retryStrategy:
  limit: 3
  retryPolicy: Always
  backoff: {duration: 30s, factor: 2, maxDuration: 5m}
  affinity:
    nodeAntiAffinity: {}
```

Sequence: attempt 1 immediate, retry after 30s/60s/120s on different nodes each time.
</details>

### Question 9: When use ContainerSet vs DAG with Containers?

<details><summary>Show Answer</summary>
**ContainerSet**: shared filesystem, tightly coupled steps, minimize scheduling overhead, fits on one node. **DAG**: independent steps, different resource needs, artifact passing via S3, independent retry/timeout per step, exceeds single-node capacity.
</details>

## Hands-On Exercise: Production-Ready Scheduled Pipeline

### Setup

```bash
kind create cluster --name capa-lab
kubectl create namespace argo
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml
kubectl -n argo wait --for=condition=ready pod -l app=workflow-controller --timeout=120s
```

### Step 1: Create supporting ConfigMaps

```bash
kubectl apply -n argo -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: deploy-semaphore
data:
  limit: "1"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: build-cache
data: {}
EOF
```

### Step 2: Create WorkflowTemplate and CronWorkflow

```yaml
# Save as pipeline.yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: build-step
  namespace: argo
spec:
  templates:
    - name: build
      inputs:
        parameters: [{name: app-name}]
      memoize:
        key: "build-{{inputs.parameters.app-name}}"
        maxAge: "1h"
        cache:
          configMap: {name: build-cache}
      container:
        image: alpine
        command: [sh, -c]
        args: ["echo 'Building {{inputs.parameters.app-name}}' && sleep 3 && echo 'done' > /tmp/result.txt"]
      outputs:
        parameters:
          - name: build-id
            valueFrom: {path: /tmp/result.txt}
---
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: scheduled-pipeline
  namespace: argo
spec:
  schedule: "*/5 * * * *"
  startingDeadlineSeconds: 120
  concurrencyPolicy: Forbid
  workflowSpec:
    entrypoint: main
    onExit: cleanup
    synchronization:
      semaphore:
        configMapKeyRef: {name: deploy-semaphore, key: limit}
    templates:
      - name: main
        dag:
          tasks:
            - name: build-app
              templateRef: {name: build-step, template: build}
              arguments:
                parameters: [{name: app-name, value: my-service}]
            - name: approval
              template: pause
              dependencies: [build-app]
            - name: deploy
              template: deploy-step
              dependencies: [approval]
      - name: pause
        suspend: {duration: "10s"}
      - name: deploy-step
        retryStrategy: {limit: 2, retryPolicy: OnError, backoff: {duration: 5s, factor: 2}}
        container:
          image: alpine
          command: [sh, -c, "echo 'Deploying...' && sleep 2 && echo 'Done'"]
      - name: cleanup
        container:
          image: alpine
          command: [sh, -c]
          args: ["echo 'Exit handler: {{workflow.name}} status={{workflow.status}}'"]
```

```bash
kubectl apply -n argo -f pipeline.yaml
# Manually trigger instead of waiting 5 min
argo submit -n argo --from cronwf/scheduled-pipeline --watch
# Run again to verify memoization (build step should be cached)
argo submit -n argo --from cronwf/scheduled-pipeline --watch
```

### Success Criteria

- [ ] CronWorkflow creates workflows on schedule
- [ ] WorkflowTemplate referenced via `templateRef`
- [ ] Memoization caches build on second run
- [ ] Suspend template pauses and auto-resumes
- [ ] Exit handler reports workflow status
- [ ] Semaphore prevents concurrent runs

### Cleanup

```bash
kind delete cluster --name capa-lab
```

## Key Takeaways

- [ ] Describe all 7 template types and when to use each
- [ ] Configure CronWorkflows with timezone, deadline, and concurrency policy
- [ ] Create and reference WorkflowTemplates and ClusterWorkflowTemplates
- [ ] Implement exit handlers that branch on workflow status
- [ ] Use mutexes and semaphores for synchronization
- [ ] Configure memoization within the 1MB ConfigMap limit
- [ ] Attach lifecycle hooks for audit/observability
- [ ] Distinguish simple tags from expression tags
- [ ] Design retry strategies with backoff and node anti-affinity
- [ ] Apply least-privilege security with per-workflow service accounts

---

*"Advanced workflows are not about complexity for its own sake. They are about making failure visible, recovery automatic, and operations predictable."*
