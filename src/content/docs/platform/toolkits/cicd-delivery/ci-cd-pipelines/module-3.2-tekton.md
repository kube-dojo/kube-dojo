---
title: "Module 3.2: Tekton"
slug: platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.2-tekton
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

The platform architect presented the migration proposal to the CTO with unexpected confidence. Their hosted CI service had been steadily increasing costs—$340,000 per year for a 90-person engineering team—and vendor lock-in was strangling their ability to customize pipelines. "We can run the same workloads on our own Kubernetes clusters for a third of the cost," she explained, "and we'll own our CI infrastructure like we own our application infrastructure." Eighteen months later, with Tekton powering 2,400 pipeline runs per day across five clusters, they'd reduced CI costs to **$95,000 per year** while gaining the ability to run pipelines on-premise for their government clients—a capability that won them a **$12 million contract**.

## Prerequisites

Before starting this module:
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) — CI/CD concepts
- Kubernetes basics (Pods, Services, CRDs)
- Container fundamentals
- YAML proficiency

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Tekton on Kubernetes and configure Tasks, Pipelines, and PipelineRuns for CI/CD workflows**
- **Implement reusable Tekton task catalogs with parameterized inputs and workspace sharing**
- **Configure event-driven pipeline triggers using Tekton Triggers and interceptors**
- **Evaluate Tekton's Kubernetes-native approach against hosted CI services for cost and control trade-offs**


## Why This Module Matters

Tekton is a Kubernetes-native CI/CD framework. Unlike hosted CI services, Tekton runs in your cluster—giving you full control, no vendor lock-in, and the ability to scale pipelines like any other Kubernetes workload.

Born from Google's Knative Build project and now a CNCF project, Tekton powers enterprise CI/CD at companies like IBM, Red Hat, and Google.

## Did You Know?

- **Tekton is named after the Greek word for "builder"**—appropriate for a build system
- **Tekton powers Google Cloud Build and OpenShift Pipelines**—it's the foundation of major enterprise CI/CD offerings
- **Tekton Pipelines runs as pods in your cluster**—each task step is a container, scaling naturally with Kubernetes
- **The Tekton Catalog has 100+ reusable tasks**—from Git clone to Kubernetes deploy, pre-built and maintained

## Tekton Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEKTON ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CUSTOM RESOURCES                                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                           │   │
│  │  Task          TaskRun         Pipeline       PipelineRun│   │
│  │  (template)    (instance)      (template)     (instance) │   │
│  │  ┌─────────┐   ┌─────────┐    ┌─────────┐    ┌─────────┐│   │
│  │  │ Steps:  │──▶│ Pod     │    │ Tasks:  │───▶│ TaskRuns││   │
│  │  │ - clone │   │ running │    │ - build │    │ running ││   │
│  │  │ - build │   │         │    │ - test  │    │         ││   │
│  │  │ - push  │   │         │    │ - deploy│    │         ││   │
│  │  └─────────┘   └─────────┘    └─────────┘    └─────────┘│   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 TEKTON CONTROLLERS                        │   │
│  │                                                           │   │
│  │  ┌─────────────────┐    ┌─────────────────┐              │   │
│  │  │    Pipeline     │    │   Triggers      │              │   │
│  │  │   Controller    │    │   Controller    │              │   │
│  │  │                 │    │                 │              │   │
│  │  │ Watches CRs     │    │ Webhooks        │              │   │
│  │  │ Creates Pods    │    │ Creates Runs    │              │   │
│  │  └─────────────────┘    └─────────────────┘              │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              KUBERNETES CLUSTER                           │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │                    POD (TaskRun)                    │ │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │ │   │
│  │  │  │ Step 1  │  │ Step 2  │  │ Step 3  │            │ │   │
│  │  │  │ (init)  │─▶│ (main)  │─▶│ (post)  │            │ │   │
│  │  │  └─────────┘  └─────────┘  └─────────┘            │ │   │
│  │  │                                                     │ │   │
│  │  │  Shared workspace volume                           │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Task** | A template defining a sequence of steps (containers) |
| **TaskRun** | An instance of a Task execution |
| **Pipeline** | A template defining a sequence of Tasks |
| **PipelineRun** | An instance of a Pipeline execution |
| **Workspace** | Shared storage between steps and tasks |
| **Trigger** | Webhook listener that creates PipelineRuns |

## Installing Tekton

```bash
# Install Tekton Pipelines
kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Install Tekton Triggers (for webhooks)
kubectl apply -f https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml
kubectl apply -f https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml

# Install Tekton Dashboard (optional)
kubectl apply -f https://storage.googleapis.com/tekton-releases/dashboard/latest/release.yaml

# Wait for components
kubectl -n tekton-pipelines wait --for=condition=ready pod -l app=tekton-pipelines-controller --timeout=120s

# Install tkn CLI
brew install tektoncd-cli  # macOS
```

## Tasks

### Basic Task

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: hello
spec:
  steps:
    - name: hello
      image: alpine
      script: |
        echo "Hello from Tekton!"
```

### Task with Parameters

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: greet
spec:
  params:
    - name: name
      type: string
      description: Name to greet
      default: World

  steps:
    - name: greet
      image: alpine
      script: |
        echo "Hello, $(params.name)!"
```

### Task with Workspaces

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: git-clone
spec:
  params:
    - name: url
      type: string

  workspaces:
    - name: output
      description: The git repo will be cloned here

  steps:
    - name: clone
      image: alpine/git
      workingDir: $(workspaces.output.path)
      script: |
        git clone $(params.url) .
        ls -la
```

### Task with Results

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: get-version
spec:
  workspaces:
    - name: source

  results:
    - name: version
      description: The version from package.json

  steps:
    - name: get-version
      image: node:20-alpine
      workingDir: $(workspaces.source.path)
      script: |
        VERSION=$(node -p "require('./package.json').version")
        echo -n $VERSION | tee $(results.version.path)
```

### Build and Push Task

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: build-push
spec:
  params:
    - name: image
      type: string
    - name: dockerfile
      default: Dockerfile

  workspaces:
    - name: source
    - name: dockerconfig
      description: Docker config for registry auth

  results:
    - name: digest
      description: Image digest

  steps:
    - name: build-push
      image: gcr.io/kaniko-project/executor:latest
      workingDir: $(workspaces.source.path)
      env:
        - name: DOCKER_CONFIG
          value: $(workspaces.dockerconfig.path)
      args:
        - --dockerfile=$(params.dockerfile)
        - --destination=$(params.image)
        - --context=.
        - --digest-file=$(results.digest.path)
```

## TaskRuns

### Running a Task

```yaml
apiVersion: tekton.dev/v1
kind: TaskRun
metadata:
  generateName: greet-run-
spec:
  taskRef:
    name: greet
  params:
    - name: name
      value: "Tekton"
```

```bash
# Create TaskRun
kubectl create -f taskrun.yaml

# List TaskRuns
tkn taskrun list

# View logs
tkn taskrun logs -f greet-run-xyz

# Describe
tkn taskrun describe greet-run-xyz
```

### TaskRun with Workspace

```yaml
apiVersion: tekton.dev/v1
kind: TaskRun
metadata:
  generateName: clone-run-
spec:
  taskRef:
    name: git-clone
  params:
    - name: url
      value: https://github.com/tektoncd/pipeline.git
  workspaces:
    - name: output
      emptyDir: {}  # Or use PVC for persistence
```

## Pipelines

### Basic Pipeline

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: build-test-deploy
spec:
  params:
    - name: repo-url
      type: string
    - name: image
      type: string

  workspaces:
    - name: shared-workspace
    - name: docker-credentials

  tasks:
    - name: fetch-source
      taskRef:
        name: git-clone
      workspaces:
        - name: output
          workspace: shared-workspace
      params:
        - name: url
          value: $(params.repo-url)

    - name: run-tests
      runAfter:
        - fetch-source
      taskRef:
        name: npm-test
      workspaces:
        - name: source
          workspace: shared-workspace

    - name: build-push
      runAfter:
        - run-tests
      taskRef:
        name: build-push
      workspaces:
        - name: source
          workspace: shared-workspace
        - name: dockerconfig
          workspace: docker-credentials
      params:
        - name: image
          value: $(params.image)
```

### Pipeline with Parallel Tasks

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: parallel-ci
spec:
  workspaces:
    - name: shared-workspace

  tasks:
    - name: fetch-source
      taskRef:
        name: git-clone
      workspaces:
        - name: output
          workspace: shared-workspace

    # These run in parallel after fetch-source
    - name: lint
      runAfter: [fetch-source]
      taskRef:
        name: lint
      workspaces:
        - name: source
          workspace: shared-workspace

    - name: test
      runAfter: [fetch-source]
      taskRef:
        name: test
      workspaces:
        - name: source
          workspace: shared-workspace

    - name: security-scan
      runAfter: [fetch-source]
      taskRef:
        name: trivy-scan
      workspaces:
        - name: source
          workspace: shared-workspace

    # This runs after all parallel tasks complete
    - name: build
      runAfter: [lint, test, security-scan]
      taskRef:
        name: build-push
      workspaces:
        - name: source
          workspace: shared-workspace
```

### Pipeline with Conditional Tasks

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: conditional-deploy
spec:
  params:
    - name: deploy-to-prod
      type: string
      default: "false"

  tasks:
    - name: build
      taskRef:
        name: build-push

    - name: deploy-staging
      runAfter: [build]
      taskRef:
        name: kubectl-deploy
      params:
        - name: namespace
          value: staging

    - name: deploy-production
      runAfter: [deploy-staging]
      when:
        - input: $(params.deploy-to-prod)
          operator: in
          values: ["true"]
      taskRef:
        name: kubectl-deploy
      params:
        - name: namespace
          value: production
```

### Using Results Between Tasks

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: version-pipeline
spec:
  tasks:
    - name: get-version
      taskRef:
        name: get-version
      workspaces:
        - name: source
          workspace: shared-workspace

    - name: build-image
      runAfter: [get-version]
      taskRef:
        name: build-push
      params:
        - name: image
          # Use result from previous task
          value: "myregistry/myapp:$(tasks.get-version.results.version)"
```

## PipelineRuns

### Running a Pipeline

```yaml
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: build-test-deploy-run-
spec:
  pipelineRef:
    name: build-test-deploy
  params:
    - name: repo-url
      value: https://github.com/org/app.git
    - name: image
      value: ghcr.io/org/app:latest
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 1Gi
    - name: docker-credentials
      secret:
        secretName: docker-credentials
```

```bash
# Create PipelineRun
kubectl create -f pipelinerun.yaml

# List PipelineRuns
tkn pipelinerun list

# View logs
tkn pipelinerun logs -f build-test-deploy-run-xyz

# Cancel a running pipeline
tkn pipelinerun cancel build-test-deploy-run-xyz
```

## Triggers

### Webhook Trigger

```yaml
# EventListener - receives webhooks
apiVersion: triggers.tekton.dev/v1beta1
kind: EventListener
metadata:
  name: github-listener
spec:
  serviceAccountName: tekton-triggers-sa
  triggers:
    - name: github-push
      bindings:
        - ref: github-push-binding
      template:
        ref: github-push-template

---
# TriggerBinding - extracts data from webhook
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerBinding
metadata:
  name: github-push-binding
spec:
  params:
    - name: repo-url
      value: $(body.repository.clone_url)
    - name: revision
      value: $(body.head_commit.id)
    - name: branch
      value: $(body.ref)

---
# TriggerTemplate - creates PipelineRun
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerTemplate
metadata:
  name: github-push-template
spec:
  params:
    - name: repo-url
    - name: revision
    - name: branch

  resourcetemplates:
    - apiVersion: tekton.dev/v1
      kind: PipelineRun
      metadata:
        generateName: github-triggered-
      spec:
        pipelineRef:
          name: build-test-deploy
        params:
          - name: repo-url
            value: $(tt.params.repo-url)
          - name: revision
            value: $(tt.params.revision)
        workspaces:
          - name: shared-workspace
            volumeClaimTemplate:
              spec:
                accessModes: [ReadWriteOnce]
                resources:
                  requests:
                    storage: 1Gi
```

### Exposing the Webhook

```yaml
# Ingress for webhook
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: github-webhook
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
    - host: tekton.example.com
      http:
        paths:
          - path: /hooks
            pathType: Prefix
            backend:
              service:
                name: el-github-listener
                port:
                  number: 8080
```

## Tekton Catalog

```bash
# Install a task from catalog
kubectl apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/git-clone/0.9/git-clone.yaml
kubectl apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/kaniko/0.6/kaniko.yaml
kubectl apply -f https://raw.githubusercontent.com/tektoncd/catalog/main/task/kubernetes-actions/0.2/kubernetes-actions.yaml

# Or use tkn hub
tkn hub install task git-clone
tkn hub install task kaniko
```

### Using Catalog Tasks

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: catalog-pipeline
spec:
  params:
    - name: repo-url
    - name: image

  workspaces:
    - name: shared-data
    - name: docker-credentials

  tasks:
    - name: fetch-repo
      taskRef:
        name: git-clone  # From catalog
      workspaces:
        - name: output
          workspace: shared-data
      params:
        - name: url
          value: $(params.repo-url)

    - name: build-push
      runAfter: [fetch-repo]
      taskRef:
        name: kaniko  # From catalog
      workspaces:
        - name: source
          workspace: shared-data
        - name: dockerconfig
          workspace: docker-credentials
      params:
        - name: IMAGE
          value: $(params.image)
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| No workspaces | Data lost between steps | Use PVC workspaces for shared data |
| Large PVC for each run | Expensive, slow | Use volumeClaimTemplate with cleanup |
| No resource limits | Pods can starve cluster | Set CPU/memory limits on steps |
| Hardcoded secrets | Insecure | Use Secrets and Workspaces |
| No timeouts | Stuck pipelines waste resources | Set `timeout` on Tasks and Pipelines |
| Ignoring results | Can't pass data between tasks | Use `results` for task outputs |

## War Story: The $890,000 Workspace Disaster

An e-commerce company migrated from CircleCI to Tekton to reduce costs and gain multi-cloud capability. The migration seemed successful—pipelines ran faster, costs dropped initially, and teams loved the Kubernetes-native approach. Then Black Friday hit.

```
THE WORKSPACE DISASTER TIMELINE
─────────────────────────────────────────────────────────────────
NOVEMBER 25 (BLACK FRIDAY EVE)
9:00 AM     Feature freeze lifted, 47 PRs merge in first hour
9:30 AM     PipelineRuns start queuing (normal)
10:15 AM    Storage alerts: EBS provisioning hitting rate limits
10:45 AM    47 pipelines stuck in "Pending" - no PVCs available
11:00 AM    Storage costs spiking: 10GB PVC per run, not cleaning up
11:30 AM    Kubernetes cluster storage at 94% capacity
12:00 PM    Critical hotfix needed for checkout bug
12:15 PM    Hotfix pipeline can't start - no storage available
12:45 PM    Manual PVC cleanup begins (47 orphaned PVCs)
1:30 PM     Hotfix finally deploys - 90 minutes late
2:00 PM     Checkout page slow - cache invalidated during chaos
5:00 PM     Black Friday traffic starts ramping

POST-INCIDENT DISCOVERY
─────────────────────────────────────────────────────────────────
Orphaned PVCs found:              847 (from 3 months of runs)
Storage wasted:                   8,470 GB
Storage cost (accumulated):       $42,350 over 3 months
Lost revenue (hotfix delay):      ~$340,000 (90 min during peak prep)
Engineering time for cleanup:     120 hours @ $100/hr = $12,000
Incident response costs:          $15,000
Customer trust impact:            $500,000+ (estimated)

TOTAL COST OF WORKSPACE MISMANAGEMENT: ~$890,000
```

The root cause analysis revealed multiple failures:

```yaml
# MISTAKE 1: Static PVC (never cleaned up)
workspaces:
  - name: shared
    persistentVolumeClaim:
      claimName: pipeline-pvc  # Reused but eventually abandoned

# MISTAKE 2: Oversized storage requests
resources:
  requests:
    storage: 10Gi  # Actual usage: 200-500 MB

# MISTAKE 3: No resource quotas on tekton-pipelines namespace
# Any pipeline could request unlimited storage

# MISTAKE 4: No monitoring on PVC lifecycle
# 847 PVCs accumulated without anyone noticing
```

**The Fix—Comprehensive Workspace Strategy:**

```yaml
# FIX 1: volumeClaimTemplate for automatic cleanup
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: build-
spec:
  pipelineRef:
    name: build-pipeline
  workspaces:
    - name: shared
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          storageClassName: fast-ssd  # Explicit storage class
          resources:
            requests:
              storage: 500Mi  # Right-sized for actual needs
          # PVC automatically deleted when PipelineRun completes

# FIX 2: Resource quotas for tekton namespace
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tekton-storage-quota
  namespace: tekton-pipelines
spec:
  hard:
    persistentvolumeclaims: "100"
    requests.storage: "100Gi"

# FIX 3: LimitRange for default sizes
---
apiVersion: v1
kind: LimitRange
metadata:
  name: tekton-storage-limits
  namespace: tekton-pipelines
spec:
  limits:
    - type: PersistentVolumeClaim
      max:
        storage: 2Gi
      default:
        storage: 500Mi

# FIX 4: PVC cleanup CronJob for any stragglers
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-orphaned-pvcs
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: pvc-cleaner
          containers:
            - name: cleaner
              image: bitnami/kubectl
              command:
                - /bin/sh
                - -c
                - |
                  # Delete PVCs older than 2 hours with no owner
                  kubectl get pvc -n tekton-pipelines \
                    --field-selector status.phase=Bound \
                    -o json | jq -r '.items[] |
                    select(.metadata.ownerReferences == null) |
                    select(now - (.metadata.creationTimestamp | fromdateiso8601) > 7200) |
                    .metadata.name' | xargs -r kubectl delete pvc -n tekton-pipelines
          restartPolicy: OnFailure
```

**Results After Fix:**

```
BEFORE VS AFTER
─────────────────────────────────────────────────────────────────
                            Before          After
Orphaned PVCs/month:        280             0
Storage costs/month:        $14,000         $2,100
Pipeline queue time:        5-15 min        < 30 sec
Storage provisioning:       Rate limited    Never limited
Black Friday readiness:     FAILED          PASSED
```

**Key Takeaway**: Tekton is Kubernetes-native—which means Kubernetes storage problems become Tekton problems. Plan your workspace strategy before your first pipeline, not after your first incident.

## Quiz

### Question 1
What's the difference between a Task and a Pipeline in Tekton?

<details>
<summary>Show Answer</summary>

**Task**: A single unit of work containing one or more sequential steps. Each step runs as a container in the same pod. Steps share the pod's workspace and environment.

**Pipeline**: A collection of Tasks that can run sequentially or in parallel. Each Task runs as a separate pod. Pipelines use workspaces to share data between Tasks.

Think of it as:
- Task = one pod with multiple containers (steps)
- Pipeline = multiple pods (tasks) orchestrated together
</details>

### Question 2
How do you pass data between Tasks in a Pipeline?

<details>
<summary>Show Answer</summary>

Two mechanisms:

1. **Workspaces**: Shared storage (PVC) mounted in multiple Tasks. Good for files (source code, artifacts).

```yaml
workspaces:
  - name: shared-data
```

2. **Results**: Small string values (< 4KB) written by one Task and read by another. Good for versions, digests, URLs.

```yaml
# Task A writes
echo -n "v1.2.3" > $(results.version.path)

# Pipeline uses in Task B
value: $(tasks.taskA.results.version)
```

Use workspaces for file data, results for small values.
</details>

### Question 3
Your pipeline has lint, test, and security-scan tasks that should run in parallel after git-clone. Write the YAML.

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: parallel-checks
spec:
  tasks:
    - name: git-clone
      taskRef:
        name: git-clone

    # All three run in parallel (same runAfter)
    - name: lint
      runAfter: [git-clone]
      taskRef:
        name: lint

    - name: test
      runAfter: [git-clone]
      taskRef:
        name: test

    - name: security-scan
      runAfter: [git-clone]
      taskRef:
        name: security-scan

    # Build waits for all parallel tasks
    - name: build
      runAfter: [lint, test, security-scan]
      taskRef:
        name: build
```

Tasks with the same `runAfter` dependency run in parallel. A task with multiple `runAfter` entries waits for all of them.
</details>

### Question 4
How would you trigger a Tekton pipeline from a GitHub push webhook?

<details>
<summary>Show Answer</summary>

You need three components:

1. **EventListener**: Receives the webhook
2. **TriggerBinding**: Extracts data from the webhook payload
3. **TriggerTemplate**: Creates the PipelineRun

```yaml
apiVersion: triggers.tekton.dev/v1beta1
kind: EventListener
metadata:
  name: github
spec:
  triggers:
    - bindings: [github-binding]
      template:
        ref: github-template
---
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerBinding
metadata:
  name: github-binding
spec:
  params:
    - name: repo
      value: $(body.repository.clone_url)
---
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerTemplate
metadata:
  name: github-template
spec:
  params: [repo]
  resourcetemplates:
    - apiVersion: tekton.dev/v1
      kind: PipelineRun
      spec:
        pipelineRef: {name: my-pipeline}
        params:
          - name: repo-url
            value: $(tt.params.repo)
```

Then expose the EventListener service via Ingress and configure GitHub webhook to POST to it.
</details>

### Question 5
A company runs 500 Tekton pipeline runs per day. Each run uses a 2GB workspace PVC. Without volumeClaimTemplate (manual cleanup), they clean up PVCs weekly. With volumeClaimTemplate, PVCs are deleted immediately. Storage costs $0.10/GB/month. Calculate monthly storage cost savings.

<details>
<summary>Show Answer</summary>

**Without volumeClaimTemplate (weekly cleanup):**
```
Daily PVCs created:     500
PVCs accumulated before cleanup: 500 × 7 days = 3,500 PVCs
Average PVCs existing:  ~1,750 (middle of week)
Storage:                1,750 × 2GB = 3,500 GB
Monthly cost:           3,500 × $0.10 = $350/month
```

**With volumeClaimTemplate (immediate cleanup):**
```
Concurrent pipelines:   ~20 at any time (estimate)
Storage:                20 × 2GB = 40 GB
Monthly cost:           40 × $0.10 = $4/month
```

**Monthly Savings:** $350 - $4 = **$346/month** ($4,152/year)

But this calculation is conservative! The real cost includes:
- EBS provisioning API rate limits
- Time waiting for storage provisioning
- Risk of running out of storage quota
- Engineering time for cleanup scripts

The actual value of proper workspace management is often 10-100x the raw storage savings.
</details>

### Question 6
Your Tekton pipeline has these tasks: git-clone (30s), lint (2m), unit-test (3m), integration-test (5m), build (2m), push (1m). Currently all tasks run sequentially. Lint, unit-test, and integration-test can run in parallel after git-clone. Build requires all three to pass. What's the time savings from parallelization?

<details>
<summary>Show Answer</summary>

**Sequential execution (current):**
```
git-clone → lint → unit-test → integration-test → build → push
   30s      2m       3m            5m              2m      1m

Total: 30s + 2m + 3m + 5m + 2m + 1m = 13 minutes 30 seconds
```

**Parallel execution (optimized):**
```
git-clone → [lint (2m), unit-test (3m), integration-test (5m)] → build → push
   30s              parallel: max(2m, 3m, 5m) = 5m               2m      1m

Total: 30s + 5m + 2m + 1m = 8 minutes 30 seconds
```

**Time savings:** 13m30s - 8m30s = **5 minutes per run** (37% faster)

At 500 runs/day:
- Time saved: 500 × 5 min = 2,500 min = **41.7 hours/day**
- If developers wait for pipelines: 41.7 hrs × $75/hr = **$3,125/day**

Pipeline YAML for parallel:
```yaml
tasks:
  - name: lint
    runAfter: [git-clone]  # Same runAfter = parallel
  - name: unit-test
    runAfter: [git-clone]
  - name: integration-test
    runAfter: [git-clone]
  - name: build
    runAfter: [lint, unit-test, integration-test]  # Waits for all
```
</details>

### Question 7
You're designing a Tekton setup for a company with 15 teams, each with their own pipelines but sharing common tasks (git-clone, build-push, deploy). How would you structure the Tekton resources? Consider maintenance, security, and team autonomy.

<details>
<summary>Show Answer</summary>

**Recommended Structure:**

```
NAMESPACE STRATEGY
─────────────────────────────────────────────────────────────────
tekton-system/          # Tekton controllers (installed once)
tekton-catalog/         # Shared Tasks (ClusterTasks deprecated)
team-alpha-pipelines/   # Team Alpha's pipelines and runs
team-beta-pipelines/    # Team Beta's pipelines and runs
...
```

**Implementation:**

```yaml
# 1. Shared Tasks in central namespace (or use Tekton Hub)
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: git-clone
  namespace: tekton-catalog
  labels:
    app.kubernetes.io/version: "1.0"
# ...

# 2. Team namespaces with RBAC
---
apiVersion: v1
kind: Namespace
metadata:
  name: team-alpha-pipelines
  labels:
    team: alpha
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-alpha-tekton
  namespace: team-alpha-pipelines
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: tekton-pipelines-admin
subjects:
  - kind: Group
    name: team-alpha
    apiGroup: rbac.authorization.k8s.io

# 3. Teams reference shared tasks
---
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: team-alpha-build
  namespace: team-alpha-pipelines
spec:
  tasks:
    - name: clone
      taskRef:
        resolver: cluster
        params:
          - name: kind
            value: task
          - name: name
            value: git-clone
          - name: namespace
            value: tekton-catalog
```

**Key Decisions:**
| Aspect | Recommendation |
|--------|----------------|
| Controllers | Single installation, cluster-wide |
| Common Tasks | Central namespace with versioning |
| Team Pipelines | Per-team namespace with RBAC |
| Secrets | Per-team, never shared |
| Storage | Per-namespace ResourceQuotas |
| Triggers | Per-team EventListeners |

This gives teams autonomy while maintaining governance over shared components.
</details>

### Question 8
Your Tekton TaskRun shows status "Pending" with message "pod has unbound immediate PersistentVolumeClaims". List all possible causes and how you'd diagnose each.

<details>
<summary>Show Answer</summary>

**Diagnostic Checklist:**

```bash
# 1. Check PVC status
kubectl get pvc -n <namespace>
kubectl describe pvc <pvc-name>

# 2. Check StorageClass
kubectl get storageclass
kubectl describe storageclass <class-name>

# 3. Check available storage capacity
kubectl get pv
kubectl describe nodes | grep -A 5 "Allocatable"

# 4. Check resource quotas
kubectl get resourcequota -n <namespace>
kubectl describe resourcequota -n <namespace>

# 5. Check events
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

**Possible Causes and Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| **No StorageClass default** | `kubectl get sc` shows no `(default)` | Add annotation `storageclass.kubernetes.io/is-default-class: "true"` |
| **StorageClass doesn't exist** | PVC shows "storageclass not found" | Create StorageClass or use existing one |
| **Insufficient storage quota** | ResourceQuota shows exceeded | Increase quota or clean up old PVCs |
| **CSI driver not ready** | CSI pods not running | Check `kubectl get pods -n kube-system \| grep csi` |
| **Cloud provider limits** | Events show "rate limit" or "quota" | Check cloud provider quotas, request increase |
| **Wrong access mode** | PV exists but mode mismatch | Match PVC accessModes to available PVs |
| **Node affinity mismatch** | PV bound to unavailable node | Check PV nodeAffinity, ensure nodes available |
| **Storage class provisioner failing** | Provisioner pod logs show errors | `kubectl logs -n kube-system <provisioner-pod>` |

**Quick Fix Workflow:**
```bash
# Fast diagnosis
kubectl get events -n tekton-pipelines | grep -i pvc
kubectl describe pvc -n tekton-pipelines | grep -A 10 "Events"

# If quota issue
kubectl delete pvc -n tekton-pipelines -l tekton.dev/pipelineRun  # Clean completed runs

# If StorageClass issue
kubectl get pvc <name> -o yaml | grep storageClassName
kubectl get sc  # Verify class exists
```
</details>

## Hands-On Exercise

### Scenario: Build a Tekton Pipeline

Create a Tekton pipeline that clones a repo, runs tests, and builds a container.

### Setup

```bash
# Create kind cluster
kind create cluster --name tekton-lab

# Install Tekton
kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Wait for controller
kubectl -n tekton-pipelines wait --for=condition=ready pod -l app=tekton-pipelines-controller --timeout=120s

# Install tkn CLI if not installed
brew install tektoncd-cli
```

### Create Tasks

```yaml
# tasks.yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: git-clone-simple
spec:
  params:
    - name: url
  workspaces:
    - name: output
  steps:
    - name: clone
      image: alpine/git
      script: |
        cd $(workspaces.output.path)
        git clone $(params.url) .
        ls -la
---
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: npm-test
spec:
  workspaces:
    - name: source
  steps:
    - name: test
      image: node:20-alpine
      workingDir: $(workspaces.source.path)
      script: |
        if [ -f package.json ]; then
          npm install
          npm test || echo "No tests defined"
        else
          echo "No package.json found"
        fi
---
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: echo-done
spec:
  steps:
    - name: done
      image: alpine
      script: |
        echo "Pipeline completed successfully!"
```

```bash
kubectl apply -f tasks.yaml
```

### Create Pipeline

```yaml
# pipeline.yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: build-pipeline
spec:
  params:
    - name: repo-url
      type: string
      default: https://github.com/tektoncd/pipeline.git

  workspaces:
    - name: shared-workspace

  tasks:
    - name: fetch-source
      taskRef:
        name: git-clone-simple
      params:
        - name: url
          value: $(params.repo-url)
      workspaces:
        - name: output
          workspace: shared-workspace

    - name: run-tests
      runAfter: [fetch-source]
      taskRef:
        name: npm-test
      workspaces:
        - name: source
          workspace: shared-workspace

    - name: finish
      runAfter: [run-tests]
      taskRef:
        name: echo-done
```

```bash
kubectl apply -f pipeline.yaml
```

### Run Pipeline

```yaml
# pipelinerun.yaml
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: build-pipeline-run-
spec:
  pipelineRef:
    name: build-pipeline
  params:
    - name: repo-url
      value: https://github.com/kubernetes/examples.git
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 500Mi
```

```bash
# Create and watch
kubectl create -f pipelinerun.yaml

# Watch logs
tkn pipelinerun logs -f $(tkn pipelinerun list -o name | head -1 | cut -d'/' -f2)

# List runs
tkn pipelinerun list
```

### Success Criteria

- [ ] Tekton is running in the cluster
- [ ] Tasks are created
- [ ] Pipeline combines tasks
- [ ] PipelineRun executes successfully
- [ ] Can view logs with tkn CLI

### Cleanup

```bash
kind delete cluster --name tekton-lab
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain the difference between Task, TaskRun, Pipeline, and PipelineRun
- [ ] Write a multi-step Task with parameters, workspaces, and results
- [ ] Design pipelines with parallel tasks using `runAfter` patterns
- [ ] Configure workspace strategies (volumeClaimTemplate vs static PVC)
- [ ] Set up Tekton Triggers for webhook-driven pipeline execution
- [ ] Calculate storage costs and implement cleanup strategies
- [ ] Use the Tekton Catalog for common tasks (git-clone, kaniko)
- [ ] Debug "Pending" TaskRuns using kubectl and tkn CLI
- [ ] Design multi-team Tekton setups with proper namespace isolation
- [ ] Compare Tekton's Kubernetes-native approach with hosted CI services

## Next Module

Continue to [Module 3.3: Argo Workflows](../module-3.3-argo-workflows/) where we'll explore DAG-based workflow orchestration.

---

*"Kubernetes-native means your pipelines scale like pods, fail like pods, and are debugged like pods. Tekton makes CI/CD a first-class Kubernetes citizen."*
