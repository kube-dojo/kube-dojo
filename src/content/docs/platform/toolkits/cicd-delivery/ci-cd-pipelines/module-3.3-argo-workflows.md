---
title: "Module 3.3: Argo Workflows"
slug: platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.3-argo-workflows
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 40-45 min

Teams that run ML pipelines on inconsistent worker environments often spend significant time debugging dependency drift instead of training and shipping models. Moving each step into a pinned container on Kubernetes can make those workflows more reproducible and improve reliability.

## Prerequisites

Before starting this module:
- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/) — CI/CD concepts
- Kubernetes basics (Pods, Services)
- Container fundamentals
- DAG (Directed Acyclic Graph) concepts helpful

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Argo Workflows and configure DAG-based pipelines for complex multi-step processing**
- **Implement artifact passing, parameter substitution, and conditional logic between workflow steps**
- **Configure workflow templates with retry strategies, timeouts, and resource limits**
- **Evaluate Argo Workflows against Tekton and Airflow for data processing and ML pipeline use cases**


## Why This Module Matters

[Argo Workflows is a container-native workflow engine for orchestrating parallel jobs on Kubernetes](https://argoproj.github.io/workflows/). While [Tekton focuses on CI/CD pipelines](https://tekton.dev/docs/concepts/overview/), [Argo Workflows excels at complex DAGs, data processing, and ML workflows](https://argoproj.github.io/workflows/).

For example, Argo Workflows is used in industry for machine-learning and data-processing pipelines. When you need more than simple build-test-deploy, Argo Workflows provides the flexibility.

## Did You Know?

- **Argo Workflows is commonly used for Kubernetes-based machine-learning workflows**
- **GitHub Actions and Argo Workflows both support dependency-driven workflows, but they are separate systems**
- **Argo Workflows is designed for very large workflows, but you should validate cluster and controller capacity before assuming that scale**
- **The Argo project includes 4 tools**—[Workflows, CD (ArgoCD), Events, and Rollouts](https://argoproj.github.io/)—all designed to work together

## Argo Workflows Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 ARGO WORKFLOWS ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WORKFLOW SPEC                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  apiVersion: argoproj.io/v1alpha1                         │   │
│  │  kind: Workflow                                           │   │
│  │  spec:                                                    │   │
│  │    templates:                                             │   │
│  │      - name: main                                         │   │
│  │        dag:                                               │   │
│  │          tasks:                                           │   │
│  │            - name: A                                      │   │
│  │            - name: B (depends: A)                         │   │
│  │            - name: C (depends: A)                         │   │
│  │            - name: D (depends: B && C)                    │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               WORKFLOW CONTROLLER                         │   │
│  │                                                           │   │
│  │  • Parses workflow DAG                                    │   │
│  │  • Creates pods for each step                             │   │
│  │  • Handles retries, timeouts                              │   │
│  │  • Passes artifacts between steps                         │   │
│  │  • Reports status                                         │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               KUBERNETES CLUSTER                          │   │
│  │                                                           │   │
│  │   A ──────────────────┐                                   │   │
│  │   │                   │                                   │   │
│  │   ▼                   ▼                                   │   │
│  │   B                   C     (parallel)                    │   │
│  │   │                   │                                   │   │
│  │   └───────────────────┘                                   │   │
│  │           │                                               │   │
│  │           ▼                                               │   │
│  │           D                                               │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Workflow** | A complete job definition with templates |
| **Template** | A step type (container, DAG, steps, script) |
| **DAG** | Directed Acyclic Graph of tasks |
| **Artifact** | Data passed between steps (files, S3 objects) |
| **Parameter** | Values passed between steps (strings) |
| **WorkflowTemplate** | Reusable workflow definition |

## Installing Argo Workflows

```bash
# Create namespace
kubectl create namespace argo

# Install Argo Workflows
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml

# Wait for controller
kubectl -n argo wait --for=condition=ready pod -l app=workflow-controller --timeout=120s

# Install CLI
brew install argo  # macOS
# or
curl -sLO https://github.com/argoproj/argo-workflows/releases/latest/download/argo-linux-amd64.gz
gunzip argo-linux-amd64.gz && chmod +x argo-linux-amd64 && sudo mv argo-linux-amd64 /usr/local/bin/argo

# Port forward UI
kubectl -n argo port-forward svc/argo-server 2746:2746 &
# Open https://localhost:2746
```

## Workflow Types

### Simple Container Workflow

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-world-
spec:
  entrypoint: hello
  templates:
    - name: hello
      container:
        image: alpine
        command: [echo]
        args: ["Hello, Argo Workflows!"]
```

### Steps (Sequential)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: steps-example-
spec:
  entrypoint: main
  templates:
    - name: main
      steps:
        - - name: step1
            template: echo
            arguments:
              parameters: [{name: message, value: "Step 1"}]
        - - name: step2
            template: echo
            arguments:
              parameters: [{name: message, value: "Step 2"}]
        - - name: step3a
            template: echo
            arguments:
              parameters: [{name: message, value: "Step 3A"}]
          - name: step3b
            template: echo
            arguments:
              parameters: [{name: message, value: "Step 3B"}]

    - name: echo
      inputs:
        parameters:
          - name: message
      container:
        image: alpine
        command: [echo]
        args: ["{{inputs.parameters.message}}"]
```

### DAG (Directed Acyclic Graph)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: dag-example-
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: checkout
            template: git-clone

          - name: lint
            template: run-lint
            dependencies: [checkout]

          - name: test
            template: run-test
            dependencies: [checkout]

          - name: security-scan
            template: run-trivy
            dependencies: [checkout]

          - name: build
            template: build-image
            dependencies: [lint, test, security-scan]

          - name: deploy
            template: kubectl-apply
            dependencies: [build]

    - name: git-clone
      container:
        image: alpine/git
        command: [sh, -c]
        args: ["git clone https://github.com/org/repo.git /work"]

    - name: run-lint
      container:
        image: golangci/golangci-lint
        command: [golangci-lint, run]

    - name: run-test
      container:
        image: golang:1.21
        command: [go, test, ./...]

    - name: run-trivy
      container:
        image: aquasec/trivy
        command: [trivy, fs, /work]

    - name: build-image
      container:
        image: gcr.io/kaniko-project/executor
        args: ["--destination=myregistry/app:latest"]

    - name: kubectl-apply
      container:
        image: bitnami/kubectl
        command: [kubectl, apply, -f, /work/k8s/]
```

## Parameters and Artifacts

### Parameters (Strings)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: params-example-
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: repo
        value: https://github.com/org/app.git
      - name: branch
        value: main

  templates:
    - name: main
      dag:
        tasks:
          - name: generate
            template: generate-message

          - name: consume
            template: print-message
            dependencies: [generate]
            arguments:
              parameters:
                - name: msg
                  value: "{{tasks.generate.outputs.parameters.message}}"

    - name: generate-message
      container:
        image: alpine
        command: [sh, -c]
        args: ["echo 'Generated at $(date)' > /tmp/message.txt"]
      outputs:
        parameters:
          - name: message
            valueFrom:
              path: /tmp/message.txt

    - name: print-message
      inputs:
        parameters:
          - name: msg
      container:
        image: alpine
        command: [echo]
        args: ["Received: {{inputs.parameters.msg}}"]
```

### Artifacts (Files)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: artifacts-example-
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: generate
            template: generate-file

          - name: process
            template: process-file
            dependencies: [generate]
            arguments:
              artifacts:
                - name: input
                  from: "{{tasks.generate.outputs.artifacts.output}}"

    - name: generate-file
      container:
        image: alpine
        command: [sh, -c]
        args: ["echo 'data: 12345' > /tmp/data.json"]
      outputs:
        artifacts:
          - name: output
            path: /tmp/data.json

    - name: process-file
      inputs:
        artifacts:
          - name: input
            path: /tmp/input.json
      container:
        image: alpine
        command: [sh, -c]
        args: ["cat /tmp/input.json && echo 'Processed!'"]
```

### S3 Artifacts

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: s3-artifacts-
spec:
  entrypoint: main
  artifactRepositoryRef:
    configMap: artifact-repositories
    key: default

  templates:
    - name: main
      dag:
        tasks:
          - name: generate
            template: generate-data

          - name: process
            template: process-data
            dependencies: [generate]
            arguments:
              artifacts:
                - name: input
                  from: "{{tasks.generate.outputs.artifacts.output}}"

    - name: generate-data
      container:
        image: python:3.11
        command: [python, -c]
        args:
          - |
            import json
            data = {"results": [1, 2, 3, 4, 5]}
            with open('/tmp/data.json', 'w') as f:
                json.dump(data, f)
      outputs:
        artifacts:
          - name: output
            path: /tmp/data.json
            s3:
              key: workflows/{{workflow.name}}/data.json

    - name: process-data
      inputs:
        artifacts:
          - name: input
            path: /tmp/data.json
      container:
        image: python:3.11
        command: [python, -c]
        args:
          - |
            import json
            with open('/tmp/data.json') as f:
                data = json.load(f)
            print(f"Sum: {sum(data['results'])}")
```

## Loops and Parallelism

### Parallel Loops

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: parallel-loop-
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: process
            template: process-item
            arguments:
              parameters:
                - name: item
                  value: "{{item}}"
            withItems:
              - one
              - two
              - three

    - name: process-item
      inputs:
        parameters:
          - name: item
      container:
        image: alpine
        command: [echo]
        args: ["Processing: {{inputs.parameters.item}}"]
```

### Dynamic Parallelism (Fan-out)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: fan-out-
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: generate-list
            template: generate

          - name: process-items
            template: process-item
            dependencies: [generate-list]
            arguments:
              parameters:
                - name: item
                  value: "{{item}}"
            withParam: "{{tasks.generate-list.outputs.result}}"

          - name: aggregate
            template: aggregate-results
            dependencies: [process-items]

    - name: generate
      script:
        image: python:3.11-alpine
        command: [python]
        source: |
          import json
          items = ["item1", "item2", "item3", "item4", "item5"]
          print(json.dumps(items))

    - name: process-item
      inputs:
        parameters:
          - name: item
      container:
        image: alpine
        command: [echo]
        args: ["Processing: {{inputs.parameters.item}}"]
```

## WorkflowTemplates

### Reusable Template

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: ci-pipeline
spec:
  arguments:
    parameters:
      - name: repo
      - name: branch
        value: main
      - name: image

  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: clone
            template: git-clone
            arguments:
              parameters:
                - name: repo
                  value: "{{workflow.parameters.repo}}"
                - name: branch
                  value: "{{workflow.parameters.branch}}"

          - name: test
            template: run-tests
            dependencies: [clone]

          - name: build
            template: build-push
            dependencies: [test]
            arguments:
              parameters:
                - name: image
                  value: "{{workflow.parameters.image}}"

    - name: git-clone
      inputs:
        parameters: [{name: repo}, {name: branch}]
      container:
        image: alpine/git
        command: [git, clone, "--branch", "{{inputs.parameters.branch}}", "{{inputs.parameters.repo}}"]

    - name: run-tests
      container:
        image: golang:1.21
        command: [go, test, ./...]

    - name: build-push
      inputs:
        parameters: [{name: image}]
      container:
        image: gcr.io/kaniko-project/executor
        args: ["--destination={{inputs.parameters.image}}"]
```

### Using WorkflowTemplate

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: run-ci-
spec:
  workflowTemplateRef:
    name: ci-pipeline
  arguments:
    parameters:
      - name: repo
        value: https://github.com/org/app.git
      - name: image
        value: ghcr.io/org/app:latest
```

## Error Handling

### Retries

```yaml
templates:
  - name: flaky-task
    retryStrategy:
      limit: 3
      retryPolicy: Always
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 1m
    container:
      image: alpine
      command: [sh, -c]
      args: ["exit $((RANDOM % 2))"]  # Randomly fails
```

### Continue on Error

```yaml
dag:
  tasks:
    - name: optional-task
      template: might-fail
      continueOn:
        failed: true

    - name: required-task
      template: must-succeed
      dependencies: [optional-task]
```

### Timeouts

```yaml
templates:
  - name: limited-task
    activeDeadlineSeconds: 300  # 5 minute timeout
    container:
      image: alpine
      command: [sleep, "600"]  # Would run 10 min
```

## Argo Events Integration

```yaml
# Trigger workflow from GitHub webhook
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: github-sensor
spec:
  template:
    serviceAccountName: argo-events-sa
  dependencies:
    - name: github
      eventSourceName: github
      eventName: push
  triggers:
    - template:
        name: workflow-trigger
        k8s:
          operation: create
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
              metadata:
                generateName: github-triggered-
              spec:
                workflowTemplateRef:
                  name: ci-pipeline
                arguments:
                  parameters:
                    - name: repo
                      value: ""  # Filled by parameter
                    - name: branch
                      value: ""
          parameters:
            - src:
                dependencyName: github
                dataKey: body.repository.clone_url
              dest: spec.arguments.parameters.0.value
            - src:
                dependencyName: github
                dataKey: body.ref
              dest: spec.arguments.parameters.1.value
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| No resource limits | Pods consume all resources | Set limits on all containers |
| Large artifacts in-line | Slow, memory issues | Use S3/GCS artifact repository |
| No timeouts | Stuck workflows | Set `activeDeadlineSeconds` |
| Sequential when parallel | Slow workflows | Use DAG for parallel tasks |
| Hardcoded secrets | Insecure | Use Kubernetes Secrets |
| No retry strategy | Transient failures kill workflow | Add retries for flaky tasks |

## War Story: Uncontrolled Parallelism Can Overload a Cluster

A large fan-out workflow can overwhelm a cluster if you launch too many pods at once without parallelism caps, quotas, and capacity testing.

```
THE 10,000 POD INCIDENT TIMELINE
─────────────────────────────────────────────────────────────────
FRIDAY, 2:00 PM    Workflow submitted: 10,000 pods requested
FRIDAY, 2:01 PM    1,000 pods scheduled immediately
FRIDAY, 2:02 PM    Kubernetes API server latency spikes to 30s
FRIDAY, 2:05 PM    etcd disk I/O at 100%, cluster becoming unresponsive
FRIDAY, 2:08 PM    Production trading systems experiencing timeouts
FRIDAY, 2:10 PM    kubectl commands failing: "context deadline exceeded"
FRIDAY, 2:15 PM    INCIDENT DECLARED: Production trading halted
FRIDAY, 2:30 PM    Workflow manually terminated (kubectl still failing)
FRIDAY, 2:45 PM    Cluster recovery begins
FRIDAY, 4:00 PM    Normal operations restored
FRIDAY, 4:30 PM    Post-incident analysis starts

IMPACT ASSESSMENT
─────────────────────────────────────────────────────────────────
Trading halt duration:           105 minutes
Missed trade opportunities:      ~$890,000
Emergency incident response:     12 people × 4 hours = $24,000
Cluster recovery costs:          $15,000
Reputation with trading desk:    Severe damage
Compliance review triggered:     $50,000 in documentation
Weekend remediation work:        $45,000

TOTAL INCIDENT COST: ~$1,024,000
Add: Lost productivity for 2 weeks while implementing fixes: ~$200,000

TOTAL COST OF UNCONTROLLED PARALLELISM: ~$1,224,000
```

The root cause analysis revealed cascading failures:

```
ROOT CAUSE ANALYSIS
─────────────────────────────────────────────────────────────────
1. Argo Workflow Controller attempted to create 10,000 pods simultaneously
   └── API server overwhelmed with pod creation requests

2. Each pod creation triggered:
   - 1 pod object write to etcd
   - 3+ secret lookups (image pull, service account, config)
   - Volume attachment requests
   - Node scheduling decisions
   └── 10,000 × ~10 API calls = 100,000+ API operations in seconds

3. etcd write-ahead log couldn't keep up
   └── Latency spike caused timeouts across ALL cluster operations

4. Kubernetes controllers (deployment, service, etc.) started failing
   └── Production workloads couldn't scale, health checks failed

5. Trading systems lost connection to supporting services
   └── Failsafe triggered: halt all automated trading
```

**The Comprehensive Fix:**

```yaml
# BEFORE: Unlimited parallelism (caused incident)
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: backtest-all-strategies
spec:
  entrypoint: fan-out
  templates:
    - name: fan-out
      dag:
        tasks:
          - name: backtest
            template: run-backtest
            withSequence:
              count: "10000"  # 10,000 parallel pods - DISASTER

# AFTER: Controlled parallelism with multiple safeguards
---
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: backtest-all-strategies-v2
spec:
  entrypoint: main
  # SAFEGUARD 1: Workflow-level parallelism cap
  parallelism: 50

  # SAFEGUARD 2: Pod GC to clean up completed pods quickly
  podGC:
    strategy: OnPodCompletion

  # SAFEGUARD 3: TTL to auto-delete old workflows
  ttlStrategy:
    secondsAfterCompletion: 3600

  # SAFEGUARD 4: Resource quotas respected
  podSpecPatch: |
    containers:
      - name: main
        resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"

  templates:
    - name: main
      dag:
        tasks:
          # SAFEGUARD 5: Batch into chunks
          - name: generate-batches
            template: create-batches

          - name: process-batch
            template: batch-processor
            dependencies: [generate-batches]
            # SAFEGUARD 6: Template-level parallelism
            parallelism: 10
            arguments:
              parameters:
                - name: batch
                  value: "{{item}}"
            withParam: "{{tasks.generate-batches.outputs.result}}"

          - name: aggregate
            template: aggregate-results
            dependencies: [process-batch]

    - name: create-batches
      script:
        image: python:3.11-alpine
        command: [python]
        source: |
          import json
          # 10,000 items into 100 batches of 100
          batches = [
            {"start": i*100, "end": (i+1)*100}
            for i in range(100)
          ]
          print(json.dumps(batches))

    - name: batch-processor
      inputs:
        parameters:
          - name: batch
      # SAFEGUARD 7: Each batch runs sequentially within
      container:
        image: backtest-runner:v2
        command: [python, run_batch.py]
        args: ["--start={{inputs.parameters.batch.start}}", "--end={{inputs.parameters.batch.end}}"]
        resources:
          requests:
            cpu: "200m"
            memory: "512Mi"
      # SAFEGUARD 8: Retry transient failures
      retryStrategy:
        limit: 3
        backoff:
          duration: 30s
          factor: 2

    - name: aggregate-results
      container:
        image: backtest-runner:v2
        command: [python, aggregate.py]
```

**Additional Infrastructure Safeguards:**

```yaml
# ResourceQuota to prevent runaway workflows
apiVersion: v1
kind: ResourceQuota
metadata:
  name: argo-workflows-quota
  namespace: argo
spec:
  hard:
    pods: "100"
    requests.cpu: "50"
    requests.memory: "100Gi"

---
# LimitRange for sensible defaults
apiVersion: v1
kind: LimitRange
metadata:
  name: argo-workflows-limits
  namespace: argo
spec:
  limits:
    - type: Pod
      max:
        cpu: "4"
        memory: "8Gi"
      default:
        cpu: "500m"
        memory: "512Mi"
      defaultRequest:
        cpu: "100m"
        memory: "256Mi"

---
# PriorityClass to deprioritize batch workflows
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: batch-workflow
value: -100
globalDefault: false
description: "Low priority for batch data processing"
```

**Results After Fix:**

```
BEFORE VS AFTER
─────────────────────────────────────────────────────────────────
                            Before          After
Max concurrent pods:        10,000          50
Workflow duration:          FAILED          4 hours
API server latency:         30+ seconds     < 100ms
Production impact:          INCIDENT        None
Success rate:               0%              99.8%
Cluster stability:          Compromised     Stable
```

**Key Lessons:**

1. **Kubernetes has finite capacity** — [The API server, etcd, and scheduler have throughput limits](https://kubernetes.io/docs/setup/best-practices/cluster-large/)
2. **Parallelism is a dial, not a switch** — Start low, increase with monitoring
3. **Batch processing beats fan-out** — 100 batches of 100 > 10,000 parallel pods
4. **Defense in depth** — ResourceQuota + LimitRange + workflow parallelism
5. **Separate namespaces** — Never run experimental workflows in production clusters

## Quiz

### Question 1
What's the difference between Steps and DAG templates?

<details>
<summary>Show Answer</summary>

**Steps**: Defines sequential stages. Each stage can have parallel items (using `- -` syntax), but stages execute in order.

```yaml
steps:
  - - name: step1  # Stage 1
  - - name: step2a  # Stage 2 (parallel)
    - name: step2b
  - - name: step3  # Stage 3
```

**DAG**: Defines explicit dependencies. Tasks run as soon as their dependencies complete—maximum parallelism automatically.

```yaml
dag:
  tasks:
    - name: A
    - name: B
      dependencies: [A]
    - name: C
      dependencies: [A]
    - name: D
      dependencies: [B, C]
```

Use Steps for simple sequential logic. Use DAG for complex dependency graphs.
</details>

### Question 2
How do you pass a file from one task to another?

<details>
<summary>Show Answer</summary>

Use artifacts:

```yaml
templates:
  - name: generate
    container:
      image: alpine
      command: [sh, -c, "echo 'data' > /tmp/file.txt"]
    outputs:
      artifacts:
        - name: my-artifact
          path: /tmp/file.txt

  - name: consume
    inputs:
      artifacts:
        - name: my-artifact
          path: /tmp/input.txt
    container:
      image: alpine
      command: [cat, /tmp/input.txt]
```

In the DAG:
```yaml
- name: consume
  dependencies: [generate]
  arguments:
    artifacts:
      - name: my-artifact
        from: "{{tasks.generate.outputs.artifacts.my-artifact}}"
```

For small strings (< 256KB), use parameters instead.
</details>

### Question 3
Write a DAG that runs A, then B and C in parallel, then D.

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: abc-dag-
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: A
            template: echo
            arguments:
              parameters: [{name: msg, value: "A"}]

          - name: B
            template: echo
            dependencies: [A]
            arguments:
              parameters: [{name: msg, value: "B"}]

          - name: C
            template: echo
            dependencies: [A]
            arguments:
              parameters: [{name: msg, value: "C"}]

          - name: D
            template: echo
            dependencies: [B, C]
            arguments:
              parameters: [{name: msg, value: "D"}]

    - name: echo
      inputs:
        parameters: [{name: msg}]
      container:
        image: alpine
        command: [echo]
        args: ["{{inputs.parameters.msg}}"]
```
</details>

### Question 4
Your workflow processes 1000 items. How do you prevent cluster overload?

<details>
<summary>Show Answer</summary>

Use the `parallelism` setting at workflow and template level:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
spec:
  # Workflow-level limit
  parallelism: 50  # Max 50 pods total

  templates:
    - name: process-items
      # Template-level limit
      parallelism: 10  # Max 10 concurrent within this template
      dag:
        tasks:
          - name: process
            template: process-one
            withItems: "{{workflow.parameters.items}}"
```

Also consider:
- `resourceDuration` limits
- `activeDeadlineSeconds` for timeouts
- Node selectors to spread load
- Batch items into chunks
</details>

### Question 5
A data processing workflow needs to process 5,000 records. Each record takes 30 seconds to process. With `parallelism: 50`, how long will the workflow take? What would happen without the parallelism limit on a 100-node cluster (4 CPU each)?

<details>
<summary>Show Answer</summary>

**With `parallelism: 50`:**
```
Total records:            5,000
Processing time per record: 30 seconds
Concurrent pods:          50

Batches needed: 5,000 / 50 = 100 batches
Time per batch: 30 seconds (parallel)
Total time: 100 × 30 seconds = 3,000 seconds = 50 minutes
```

**Without parallelism limit:**
```
Cluster capacity: 100 nodes × 4 CPU = 400 CPU
Assuming each pod needs 0.5 CPU → ~800 concurrent pods possible

If all 5,000 pods schedule at once:
- 800 run immediately (cluster capacity)
- 4,200 wait in Pending
- First batch: 30 seconds
- ~7 more batches needed (5000/800 ≈ 6.25)
- Total: ~7 × 30 seconds = 3.5 minutes

BUT THIS IS DANGEROUS:
- 5,000 pod creation requests overwhelm API server
- Scheduler struggles with 5,000 pending pods
- etcd performance degrades
- Other workloads affected
- Risk of cluster instability
```

**The Lesson:** Unlimited parallelism might be faster in theory, but:
- 50 minutes with stability beats 3.5 minutes with risk
- Production clusters need protection from batch jobs
- The 15x slower time is the cost of reliability

**Right-sizing parallelism:**
```yaml
# Consider: How many pods can your cluster handle comfortably?
# Rule of thumb: parallelism < 10% of cluster capacity
# 100 nodes → parallelism: 50-100
```
</details>

### Question 6
Your Argo Workflow fails at step 47 of 100 with "OOMKilled". What's your debugging workflow and what are the likely causes?

<details>
<summary>Show Answer</summary>

**Debugging Workflow:**

```bash
# 1. Get workflow status
argo get <workflow-name> -n argo

# 2. Find the failed node (step 47)
argo get <workflow-name> -n argo -o yaml | grep -A 20 "step-47"

# 3. Get pod details
kubectl describe pod <step-47-pod-name> -n argo

# 4. Check previous container logs (might have logs before OOM)
kubectl logs <pod-name> -n argo --previous

# 5. Check node status (was node under memory pressure?)
kubectl describe node <node-name> | grep -A 10 "Conditions"

# 6. Check resource usage across cluster
kubectl top pods -n argo
kubectl top nodes
```

**Likely Causes and Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| **Insufficient memory limit** | Container uses more than limit | Increase `resources.limits.memory` |
| **Memory leak in code** | Usage grows over time | Fix application code, add heap limits |
| **Large data processing** | Step 47 has larger data | Process in smaller chunks |
| **No resource limits** | Using node's full memory | Add explicit limits |
| **Cumulative artifacts** | Previous artifacts not cleaned | Add `podGC: OnPodCompletion` |
| **Node memory pressure** | All pods affected | Add node selectors, spread load |

**Fix Example:**

```yaml
templates:
  - name: memory-intensive-step
    container:
      resources:
        requests:
          memory: "512Mi"
        limits:
          memory: "2Gi"  # Increased from default
      env:
        # For Java applications
        - name: JAVA_OPTS
          value: "-Xmx1536m"
        # For Python
        - name: PYTHONUNBUFFERED
          value: "1"
    # Prevent cascading failures
    retryStrategy:
      limit: 2
      retryPolicy: OnError
```

**Proactive Monitoring:**
```yaml
# Add resource monitoring to workflows
metadata:
  labels:
    workflows.argoproj.io/workflow-type: "data-processing"
# Then alert on OOMKilled events in this namespace
```
</details>

### Question 7
Compare Argo Workflows vs Tekton for these scenarios: (A) ML training pipeline with 100 hyperparameter combinations, (B) Standard CI/CD for microservices, (C) Event-driven image processing.

<details>
<summary>Show Answer</summary>

**Comparison Matrix:**

| Scenario | Better Choice | Reasoning |
|----------|---------------|-----------|
| **A: ML hyperparameter tuning** | **Argo Workflows** | Complex DAGs, fan-out/fan-in, artifact passing |
| **B: Standard CI/CD** | **Tekton** or Either | Both work well; Tekton has better catalog |
| **C: Event-driven processing** | **Argo Workflows + Events** | Argo Events integration, complex triggers |

**Detailed Analysis:**

**A: ML Training Pipeline (100 hyperparameters)**
```yaml
# Argo Workflows - Natural fit
spec:
  templates:
    - name: hyperparameter-search
      dag:
        tasks:
          - name: generate-params
            template: param-generator
          - name: train
            dependencies: [generate-params]
            template: train-model
            withParam: "{{tasks.generate-params.outputs.result}}"
          - name: evaluate
            dependencies: [train]
            template: evaluate-best
```
Why Argo: Dynamic fan-out, artifact passing (model files), complex dependencies, Kubeflow integration.

**B: Standard CI/CD**
```yaml
# Tekton - Optimized for this
# git-clone → lint → test → build → push → deploy
# Linear with some parallelism
```
Why Tekton: Catalog tasks (git-clone, kaniko), simple steps, GitOps integration, lower overhead.

**C: Event-Driven Processing**
```yaml
# Argo Events + Workflows
apiVersion: argoproj.io/v1alpha1
kind: Sensor
spec:
  triggers:
    - template:
        k8s:
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
          parameters:
            - src:
                dependencyName: s3-event
                dataKey: body.Records.0.s3.object.key
              dest: spec.arguments.parameters.0.value
```
Why Argo: Argo Events for complex triggers, natural workflow integration, stateful processing.

**Decision Framework:**
```
Use Argo Workflows when:
- DAG complexity > 10 nodes
- Fan-out/fan-in patterns
- Artifact-heavy (ML, data processing)
- Long-running jobs (hours)
- Complex retry/error handling

Use Tekton when:
- Standard CI/CD patterns
- Strong catalog ecosystem important
- Simpler linear or star-shaped DAGs
- Integration with other Tekton tools (Chains, Results)
- GitOps-first deployment
```
</details>

### Question 8
Design an Argo Workflow for a nightly data pipeline that: (1) extracts from 3 databases in parallel, (2) transforms each dataset, (3) loads all into a data warehouse, (4) runs 10 quality checks in parallel, (5) sends Slack notification. Include error handling and timeouts.

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: nightly-etl-
spec:
  entrypoint: main
  parallelism: 20
  activeDeadlineSeconds: 14400  # 4 hour max

  # Retry entire workflow on failure
  onExit: exit-handler

  arguments:
    parameters:
      - name: run-date
        value: "{{workflow.creationTimestamp.Y}}-{{workflow.creationTimestamp.m}}-{{workflow.creationTimestamp.d}}"

  templates:
    - name: main
      dag:
        tasks:
          # 1. EXTRACT: 3 databases in parallel
          - name: extract-users-db
            template: extract
            arguments:
              parameters: [{name: source, value: "users"}]

          - name: extract-orders-db
            template: extract
            arguments:
              parameters: [{name: source, value: "orders"}]

          - name: extract-products-db
            template: extract
            arguments:
              parameters: [{name: source, value: "products"}]

          # 2. TRANSFORM: Each dataset (after its extract)
          - name: transform-users
            template: transform
            dependencies: [extract-users-db]
            arguments:
              artifacts:
                - name: raw-data
                  from: "{{tasks.extract-users-db.outputs.artifacts.data}}"
              parameters: [{name: dataset, value: "users"}]

          - name: transform-orders
            template: transform
            dependencies: [extract-orders-db]
            arguments:
              artifacts:
                - name: raw-data
                  from: "{{tasks.extract-orders-db.outputs.artifacts.data}}"
              parameters: [{name: dataset, value: "orders"}]

          - name: transform-products
            template: transform
            dependencies: [extract-products-db]
            arguments:
              artifacts:
                - name: raw-data
                  from: "{{tasks.extract-products-db.outputs.artifacts.data}}"
              parameters: [{name: dataset, value: "products"}]

          # 3. LOAD: All into warehouse (after all transforms)
          - name: load-warehouse
            template: load
            dependencies: [transform-users, transform-orders, transform-products]
            arguments:
              artifacts:
                - name: users
                  from: "{{tasks.transform-users.outputs.artifacts.transformed}}"
                - name: orders
                  from: "{{tasks.transform-orders.outputs.artifacts.transformed}}"
                - name: products
                  from: "{{tasks.transform-products.outputs.artifacts.transformed}}"

          # 4. QUALITY: 10 checks in parallel
          - name: quality-checks
            template: run-quality-check
            dependencies: [load-warehouse]
            arguments:
              parameters: [{name: check, value: "{{item}}"}]
            withItems:
              - "row-count"
              - "null-check"
              - "duplicate-check"
              - "referential-integrity"
              - "value-ranges"
              - "freshness"
              - "schema-validation"
              - "cross-table-consistency"
              - "historical-comparison"
              - "business-rules"

          # 5. NOTIFY: Only after all quality checks pass
          - name: notify-success
            template: slack-notify
            dependencies: [quality-checks]
            arguments:
              parameters: [{name: status, value: "SUCCESS"}]

    # EXTRACT template with retry
    - name: extract
      inputs:
        parameters: [{name: source}]
      retryStrategy:
        limit: 3
        backoff:
          duration: 60s
          factor: 2
      activeDeadlineSeconds: 1800  # 30 min per extract
      container:
        image: etl-tools:v2
        command: [python, extract.py]
        args: ["--source={{inputs.parameters.source}}"]
      outputs:
        artifacts:
          - name: data
            path: /tmp/extracted/

    # TRANSFORM template
    - name: transform
      inputs:
        parameters: [{name: dataset}]
        artifacts:
          - name: raw-data
            path: /tmp/raw/
      container:
        image: etl-tools:v2
        command: [python, transform.py]
        args: ["--dataset={{inputs.parameters.dataset}}"]
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
      outputs:
        artifacts:
          - name: transformed
            path: /tmp/transformed/

    # LOAD template
    - name: load
      inputs:
        artifacts:
          - name: users
            path: /tmp/data/users/
          - name: orders
            path: /tmp/data/orders/
          - name: products
            path: /tmp/data/products/
      retryStrategy:
        limit: 2
      container:
        image: etl-tools:v2
        command: [python, load.py]
        env:
          - name: WAREHOUSE_CREDS
            valueFrom:
              secretKeyRef:
                name: warehouse-credentials
                key: connection-string

    # Quality check template
    - name: run-quality-check
      inputs:
        parameters: [{name: check}]
      container:
        image: dbt-runner:v1
        command: [dbt, test]
        args: ["--select={{inputs.parameters.check}}"]

    # Slack notification
    - name: slack-notify
      inputs:
        parameters: [{name: status}]
      container:
        image: curlimages/curl
        command: [sh, -c]
        args:
          - |
            curl -X POST $SLACK_WEBHOOK \
              -H 'Content-type: application/json' \
              -d '{"text": "ETL Pipeline {{inputs.parameters.status}} - {{workflow.parameters.run-date}}"}'
        env:
          - name: SLACK_WEBHOOK
            valueFrom:
              secretKeyRef:
                name: slack-webhook
                key: url

    # Exit handler for failures
    - name: exit-handler
      steps:
        - - name: notify-status
            template: slack-notify
            arguments:
              parameters:
                - name: status
                  value: "{{workflow.status}}"
```

**Key Design Decisions:**
- `parallelism: 20` prevents cluster overload
- Individual timeouts per stage
- Retry with exponential backoff for transient failures
- `onExit` ensures notification regardless of outcome
- Secrets via Kubernetes Secrets, not hardcoded
</details>

## Hands-On Exercise

### Scenario: Build a Data Processing Workflow

Create an Argo Workflow that processes data in parallel.

### Setup

```bash
# Create kind cluster
kind create cluster --name argo-lab

# Install Argo Workflows
kubectl create namespace argo
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml

# Patch to allow running workflows without auth (dev only)
kubectl patch deployment argo-server -n argo --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--auth-mode=server"}]'

# Wait for controller
kubectl -n argo wait --for=condition=ready pod -l app=workflow-controller --timeout=120s

# Port forward UI
kubectl -n argo port-forward svc/argo-server 2746:2746 &
```

### Create Workflow

```yaml
# workflow.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: data-pipeline-
  namespace: argo
spec:
  entrypoint: main
  parallelism: 3

  templates:
    - name: main
      dag:
        tasks:
          - name: generate-data
            template: generate

          - name: process-items
            template: process
            dependencies: [generate-data]
            arguments:
              parameters:
                - name: item
                  value: "{{item}}"
            withParam: "{{tasks.generate-data.outputs.result}}"

          - name: aggregate
            template: aggregate
            dependencies: [process-items]

    - name: generate
      script:
        image: python:3.11-alpine
        command: [python]
        source: |
          import json
          items = [f"item-{i}" for i in range(5)]
          print(json.dumps(items))

    - name: process
      inputs:
        parameters:
          - name: item
      container:
        image: alpine
        command: [sh, -c]
        args:
          - |
            echo "Processing: {{inputs.parameters.item}}"
            sleep 2
            echo "Done: {{inputs.parameters.item}}"

    - name: aggregate
      container:
        image: alpine
        command: [echo]
        args: ["All items processed!"]
```

### Run Workflow

```bash
# Submit workflow
argo submit -n argo workflow.yaml --watch

# List workflows
argo list -n argo

# Get details
argo get -n argo @latest

# View logs
argo logs -n argo @latest
```

### View in UI

Open https://localhost:2746 and explore:
- Workflow visualization
- Task logs
- Artifact inspection

### Success Criteria

- [ ] Argo Workflows is running
- [ ] Workflow executes successfully
- [ ] Parallel processing works (3 at a time)
- [ ] Can view in UI
- [ ] Understand DAG structure

### Cleanup

```bash
kind delete cluster --name argo-lab
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain the difference between Steps and DAG templates
- [ ] Design workflows with fan-out/fan-in patterns using `withItems` and `withParam`
- [ ] Pass data between tasks using parameters (strings) and artifacts (files)
- [ ] Configure S3/GCS artifact repositories for large data
- [ ] Set appropriate `parallelism` limits at workflow and template level
- [ ] Implement retry strategies with exponential backoff
- [ ] Debug OOMKilled and Pending workflow failures
- [ ] Choose between Argo Workflows and Tekton for specific use cases
- [ ] Create WorkflowTemplates for reusable pipeline patterns
- [ ] Design workflows with `onExit` handlers for cleanup and notifications

## Summary

You've completed the CI/CD Pipelines Toolkit! You now understand:

- **Dagger**: [Programmable, portable pipelines](https://github.com/dagger/dagger)
- **Tekton**: [Kubernetes-native CI/CD](https://tekton.dev/docs/concepts/overview/)
- **Argo Workflows**: [DAG-based workflow orchestration](https://argoproj.github.io/workflows/)

These tools provide different approaches to the same problem—choose based on your needs.

## Next Steps

Continue to [Security Tools Toolkit](/platform/toolkits/security-quality/security-tools/) where we'll cover Vault, OPA, Falco, and supply chain security.

---

*"A workflow is a program. Write it like code, test it like code, version it like code."*

## Sources

- [Argo Workflows Overview](https://argoproj.github.io/workflows/) — Official overview of Argo Workflows concepts, DAG capabilities, and common Kubernetes workload patterns.
- [Tekton Overview](https://tekton.dev/docs/concepts/overview/) — Official Tekton overview describing its Kubernetes-native CI/CD model and core concepts.
- [Argo Project Overview](https://argoproj.github.io/) — Official project landing page summarizing the Argo ecosystem tools, including Workflows, CD, Events, and Rollouts.
- [Considerations for Large Clusters](https://kubernetes.io/docs/setup/best-practices/cluster-large/) — Kubernetes guidance on control-plane, scheduler, and etcd limits in large clusters.
- [Dagger](https://github.com/dagger/dagger) — Project repository describing Dagger as a programmable delivery engine for portable pipelines.
- [Argo Workflows: Running At Massive Scale](https://argoproj.github.io/argo-workflows/running-at-massive-scale) — Scaling guidance relevant to teaching safe parallelism and large-workflow operation.
