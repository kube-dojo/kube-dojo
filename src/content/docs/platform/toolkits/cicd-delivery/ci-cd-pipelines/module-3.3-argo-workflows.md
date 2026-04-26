---
title: "Module 3.3: Argo Workflows"
slug: platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.3-argo-workflows
sidebar:
  order: 4
---

# Module 3.3: Argo Workflows

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 55-70 min | Prerequisites: CI/CD concepts, Kubernetes Pods and Jobs, container images, basic YAML, and the idea of a Directed Acyclic Graph.

## Learning Outcomes

After completing this module, you will be able to:

- **Design** Argo Workflows that express sequential, parallel, and fan-out/fan-in delivery or data-processing pipelines without overloading a Kubernetes cluster.
- **Debug** failed workflow nodes by connecting Argo status, pod status, logs, retry policy, resource requests, and artifact movement into one investigation path.
- **Evaluate** when to use parameters, artifacts, WorkflowTemplates, retries, timeouts, and `parallelism` controls for a given operational scenario.
- **Compare** Argo Workflows with Tekton and Airflow for CI/CD, ML, batch processing, and event-driven orchestration use cases.
- **Implement** a reusable workflow pattern that uses dependency gates, runtime parameters, bounded parallelism, and cleanup behavior suitable for shared clusters.

## Why This Module Matters

A platform team inherited a nightly model-training pipeline that looked reliable on paper. The repository had a tidy CI workflow, the Python dependencies were pinned, and the training code had unit tests. In production, however, the work ran on a mixture of long-lived virtual machines, manually patched notebooks, and shared shell scripts. Every failed run started the same argument: was the data stale, was the environment different, did the worker run out of memory, or did someone change a hidden dependency?

The team moved each stage into a container and scheduled the work on Kubernetes, but a plain set of Jobs was still not enough. The pipeline needed to extract data, validate it, train several candidates in parallel, compare metrics, publish artifacts, and notify the model registry only if the right branches succeeded. They needed a workflow engine that treated Kubernetes pods as the execution units while still letting engineers describe dependencies, retries, artifacts, and cleanup as one versioned object.

[Argo Workflows is a container-native workflow engine for orchestrating parallel jobs on Kubernetes](https://argoproj.github.io/workflows/). It is not just "CI inside Kubernetes." While [Tekton focuses on CI/CD pipelines](https://tekton.dev/docs/concepts/overview/), Argo Workflows is strongest when the shape of the work is a graph: data pipelines, ML workflows, simulation batches, security scans, report generation, or delivery flows where some branches run together and others wait for a merge point.

The senior-level lesson is that Argo gives you power that Kubernetes alone does not constrain for you. A workflow that creates ten pods is convenient; a workflow that creates thousands of pods can stress the API server, scheduler, etcd, storage system, and neighboring workloads. Good Argo design is therefore two skills at once: expressing the dependency graph clearly, and putting operational limits around how that graph runs on a real cluster.

## Prerequisites

You should already understand what a Kubernetes Pod is, how a Job differs from a long-running Deployment, and why containers make runtime environments repeatable. If you have used `kubectl apply`, read pod logs, and followed a basic CI pipeline from clone to test to build, you have enough background to start this module.

This module uses `k` as a shell alias for `kubectl` after the first installation command. The alias is not magic; it is just a shorter command used by many Kubernetes practitioners. When you copy commands into a fresh shell, create the alias first so the remaining examples work as written.

```bash
alias k=kubectl
```

## Core Concepts: How Argo Thinks About Work

Argo Workflows turns a workflow specification into Kubernetes pods. The specification says what tasks exist, which template each task runs, which tasks must finish before another task can start, and what values or files move between tasks. The controller watches the custom resource, creates pods for runnable nodes, records status back onto the Workflow object, and repeats that loop until the graph succeeds, fails, or is terminated.

```ascii
┌──────────────────────────────────────────────────────────────────────┐
│                     ARGO WORKFLOWS CONTROL LOOP                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Workflow YAML                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ apiVersion: argoproj.io/v1alpha1                              │    │
│  │ kind: Workflow                                                │    │
│  │ spec:                                                         │    │
│  │   entrypoint: main                                            │    │
│  │   templates:                                                  │    │
│  │     - name: main                                              │    │
│  │       dag:                                                    │    │
│  │         tasks:                                                │    │
│  │           - name: A                                           │    │
│  │           - name: B    dependencies: [A]                      │    │
│  │           - name: C    dependencies: [A]                      │    │
│  │           - name: D    dependencies: [B, C]                   │    │
│  └───────────────────────────────┬──────────────────────────────┘    │
│                                  │                                   │
│                                  ▼                                   │
│  Workflow Controller                                                 │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Parses the graph, checks dependencies, creates pods, records │    │
│  │  node phase, handles retries, enforces timeouts, and moves    │    │
│  │  parameters or artifacts according to the template contracts. │    │
│  └───────────────────────────────┬──────────────────────────────┘    │
│                                  │                                   │
│                                  ▼                                   │
│  Kubernetes Execution                                                │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                                                              │    │
│  │   A completes                                                │    │
│  │   ├──────────────► B runs ───────┐                           │    │
│  │   └──────────────► C runs ───────┤                           │    │
│  │                                  ▼                           │    │
│  │                                  D runs after B and C         │    │
│  │                                                              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

The important mental model is that Argo is not running your code inside the controller. The controller is an orchestrator, and your code runs in ordinary pods. That separation is what makes Argo fit Kubernetes well: scheduling, logs, image pulls, resource limits, service accounts, network policies, and secrets all behave like Kubernetes primitives because the work is executed by Kubernetes primitives.

A Workflow contains templates, and templates are reusable task definitions inside that workflow. A template can run a container, run a script, define a list of steps, or define a DAG. Tasks are invocations of those templates with specific arguments. This distinction matters because a template is like a function definition, while a task is like a function call placed at a specific point in the graph.

| Concept | What it means in practice | Design question it answers |
|---------|---------------------------|----------------------------|
| **Workflow** | A submitted run with metadata, status, arguments, and templates. | What complete unit of work should the controller execute and track? |
| **Template** | A reusable definition for a container, script, steps group, or DAG. | What kind of pod or subgraph should this task create? |
| **Task** | A named use of a template inside a DAG, usually with arguments. | When should this particular unit run, and what inputs should it receive? |
| **Parameter** | A small string value passed through templates and task outputs. | Is this value small enough to treat as configuration or a simple result? |
| **Artifact** | A file or directory passed through an artifact repository or local path. | Is this data too large or structured to safely squeeze into a string? |
| **WorkflowTemplate** | A reusable workflow definition stored in the cluster. | Should many teams or runs share the same graph shape? |

> **Active check:** Before reading further, describe a three-stage pipeline you already know. Mark which stages are task invocations, which parts could become reusable templates, and which outputs are small parameters versus file artifacts. If everything in your sketch is a task but nothing is reusable, you are probably designing a one-off run rather than a platform pattern.

## Installing Argo Workflows Safely

Installation is simple, but the field choices around installation are not trivial. Argo installs a controller, a server, service accounts, CRDs, and supporting RBAC. In a learning cluster, it is reasonable to install the upstream manifest into an `argo` namespace. In a shared platform cluster, the safer pattern is to treat Argo like any other control-plane extension: pin a release, review RBAC, decide authentication mode, decide artifact storage, and decide which namespaces may submit workflows.

The commands below use a local or disposable cluster. They install Argo Workflows into the `argo` namespace, wait for the controller, and port-forward the UI. The example uses the upstream `latest` install URL because it is convenient for a lab, but production teams should pin a tested release artifact so a rebuild of the same environment does not silently change controller behavior.

```bash
k create namespace argo

k apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml

k -n argo wait --for=condition=ready pod -l app=workflow-controller --timeout=120s
```

The CLI is useful because it gives workflow-specific commands such as `argo submit`, `argo get`, `argo logs`, and `argo terminate`. You can still inspect everything with Kubernetes commands, but the Argo CLI presents the graph and node status in a way that maps directly to the workflow specification.

```bash
brew install argo

argo version
```

On Linux, you can download the release binary directly. In a corporate environment, prefer your approved package mirror or internal tool distribution system rather than having every engineer download binaries manually from the internet.

```bash
curl -sLO https://github.com/argoproj/argo-workflows/releases/latest/download/argo-linux-amd64.gz
gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64
sudo mv argo-linux-amd64 /usr/local/bin/argo

argo version
```

The Argo Server UI is useful for learning because it shows the workflow graph, node status, logs, and artifacts. For a local lab, you can port-forward it and open the HTTPS endpoint on the loopback address. For a real platform, expose the UI through your normal ingress, identity provider, TLS policy, and audit controls.

```bash
k -n argo port-forward svc/argo-server 2746:2746
```

Open `https://127.0.0.1:2746` in a browser while the port-forward is running. Some local browsers will warn about the development certificate; that is expected in a lab, but it is not a production authentication design.

> **Pause and predict:** What would change if ten teams shared this one `argo` namespace? Think about workflow names, service accounts, secrets, resource quotas, artifact locations, and log visibility before you answer. The install command succeeds either way, but the governance model changes from "my lab controller" to "shared execution service."

A useful first verification is to check the custom resource definitions and controller pod. This confirms that Kubernetes knows the Workflow kind and that the controller is present to reconcile submitted runs.

```bash
k get crd | grep workflows.argoproj.io
k -n argo get pods
k -n argo get deploy
```

If the controller pod is not ready, do not start by editing workflow YAML. First inspect the controller deployment, events, and logs. A broken controller means no workflow will reconcile correctly, no matter how valid the workflow specification is.

```bash
k -n argo describe deploy workflow-controller
k -n argo logs deploy/workflow-controller
k -n argo get events --sort-by=.lastTimestamp
```

The installation step teaches a pattern you will use repeatedly: separate platform health from workflow health. If the controller, CRDs, RBAC, or artifact repository are broken, workflow authors will see confusing task failures that are not caused by their code. A senior operator proves the substrate is healthy before debugging the pipeline itself.

## From a Single Container to a Graph

The smallest Argo Workflow runs one container. This example looks almost too simple, but it reveals the core fields. `generateName` asks Kubernetes to create a unique name for each run, `entrypoint` tells Argo which template starts the workflow, and the `hello` template defines the container that becomes a pod.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-world-
  namespace: argo
spec:
  entrypoint: hello
  templates:
    - name: hello
      container:
        image: alpine:3.20
        command: [echo]
        args: ["Hello, Argo Workflows!"]
```

Save that as `hello-workflow.yaml`, then submit and watch it. The `--watch` flag is helpful while learning because it shows phase transitions immediately instead of making you poll.

```bash
argo submit -n argo hello-workflow.yaml --watch
argo get -n argo @latest
argo logs -n argo @latest
```

The first important design choice is whether you need `steps` or `dag`. A `steps` template is stage-oriented: each outer list item is a stage, and all inner items in the same stage can run in parallel. A `dag` template is dependency-oriented: each task declares what it depends on, and Argo runs tasks as soon as their dependencies are satisfied.

| Shape | Best fit | Why it helps | Common trap |
|-------|----------|--------------|-------------|
| **Single container** | One-off utility work, smoke tests, simple reports. | Minimal YAML and direct mapping to one pod. | Teams later bolt on many unrelated concerns without refactoring. |
| **Steps** | Mostly linear flows with occasional parallel work inside a stage. | The visual order matches the reading order. | Deep nesting becomes hard to reason about. |
| **DAG** | Complex graphs, fan-out/fan-in, independent branches, shared prerequisites. | Dependencies are explicit and Argo can maximize safe parallelism. | Unbounded parallel branches can overload shared clusters. |

A `steps` template is a good bridge from traditional CI thinking. The syntax is unusual because each stage is a list of steps, and each step in the same stage can run together. In the example below, `step1` runs first, `step2` runs second, and `step3a` plus `step3b` run together after `step2`.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: steps-example-
  namespace: argo
spec:
  entrypoint: main
  templates:
    - name: main
      steps:
        - - name: step1
            template: echo
            arguments:
              parameters:
                - name: message
                  value: "Step 1 prepares the workspace"
        - - name: step2
            template: echo
            arguments:
              parameters:
                - name: message
                  value: "Step 2 validates the input"
        - - name: step3a
            template: echo
            arguments:
              parameters:
                - name: message
                  value: "Step 3A publishes a report"
          - name: step3b
            template: echo
            arguments:
              parameters:
                - name: message
                  value: "Step 3B sends a notification"

    - name: echo
      inputs:
        parameters:
          - name: message
      container:
        image: alpine:3.20
        command: [echo]
        args: ["{{inputs.parameters.message}}"]
```

The `echo` template declares an input parameter named `message`. Each step passes a different value into the same template. This is the first example of the function-call mental model: the template defines the reusable operation, and each task or step invocation supplies the arguments.

> **Active check:** In the `steps` example, predict which pod names will appear first and which ones can appear together. Then run the workflow and compare your prediction with `argo get -n argo @latest`. If your prediction was wrong, look again at the nested list shape under `steps`.

A DAG expresses the same idea with explicit dependencies rather than stage order. The example below models a delivery flow where clone must complete before lint, test, and scan; build waits for all three quality gates; deploy waits for the image build. The graph is clearer than a steps list once there are several branches.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: dag-example-
  namespace: argo
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
        image: alpine/git:2.45.2
        command: [sh, -c]
        args:
          - |
            git clone https://github.com/argoproj/argo-workflows.git /work
            cd /work
            git rev-parse --short HEAD

    - name: run-lint
      container:
        image: alpine:3.20
        command: [sh, -c]
        args: ["echo 'lint would run here'"]

    - name: run-test
      container:
        image: alpine:3.20
        command: [sh, -c]
        args: ["echo 'tests would run here'"]

    - name: run-trivy
      container:
        image: alpine:3.20
        command: [sh, -c]
        args: ["echo 'security scan would run here'"]

    - name: build-image
      container:
        image: alpine:3.20
        command: [sh, -c]
        args: ["echo 'image build would run here'"]

    - name: kubectl-apply
      container:
        image: bitnami/kubectl:1.35
        command: [sh, -c]
        args: ["kubectl version --client=true"]
```

This YAML is intentionally runnable without registry credentials, but the template names still match real delivery work. In production, `run-lint` might use a language-specific linter image, `build-image` might use Kaniko or BuildKit, and `deploy` might apply manifests or notify a GitOps controller. The field design stays the same: templates define operations, tasks define dependency placement, and arguments make each invocation specific.

```ascii
┌──────────┐
│ checkout │
└────┬─────┘
     │
     ├──────────────► ┌──────┐
     │                │ lint │
     │                └──┬───┘
     │                   │
     ├──────────────► ┌──▼───┐
     │                │ test │
     │                └──┬───┘
     │                   │
     └──────────────► ┌──▼──────────┐
                      │ security-scan │
                      └──────┬───────┘
                             │
                      ┌──────▼──────┐
                      │    build    │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │   deploy    │
                      └─────────────┘
```

The diagram makes one limitation visible: a dependency list is a control-flow dependency, not a shared filesystem. The `checkout` pod does not automatically give `/work` to the lint pod. Every task runs in its own pod unless you explicitly use artifacts, volumes, or an external service. Many first Argo failures come from assuming a directory created in one task magically exists in the next one.

## Parameters and Artifacts: Choosing the Right Data Contract

A workflow needs data contracts between tasks. Argo gives you parameters for small string values and artifacts for files or directories. The rule is simple, but the operational consequences are large: parameters live in workflow status and are convenient for branch names, versions, metric numbers, or JSON snippets; artifacts belong in an artifact repository when they represent real data, model files, reports, or build outputs.

| Data type | Use it for | Avoid it when | Operational concern |
|-----------|------------|---------------|---------------------|
| **Parameter** | Short strings, flags, image tags, small JSON arrays for `withParam`. | The value is large, binary, sensitive, or repeatedly appended. | It appears in workflow metadata and can make status bulky. |
| **Artifact** | Files, directories, models, reports, extracted data, scan results. | The value is just a small decision or scalar. | You need artifact storage, retention, access control, and cleanup. |
| **External store** | Databases, object stores, registries, warehouse tables, long-lived datasets. | A workflow run should be fully self-contained for a tiny lab. | You must pass references and credentials safely. |

The parameter example below has one task generate a message and another task print it. The output parameter reads the content of `/tmp/message.txt` from the producer pod, stores it as a workflow output value, and injects it into the consumer task. This is useful for small computed values such as a version string, selected environment, or validation result.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: params-example-
  namespace: argo
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: repo
        value: https://github.com/example/app.git
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
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            echo "Generated for {{workflow.parameters.repo}} on branch {{workflow.parameters.branch}}" > /tmp/message.txt
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
        image: alpine:3.20
        command: [echo]
        args: ["Received: {{inputs.parameters.msg}}"]
```

Notice the two levels of substitution. `{{workflow.parameters.repo}}` reads a workflow-level argument, while `{{tasks.generate.outputs.parameters.message}}` reads an output from a previous task. That difference matters during debugging because a missing workflow parameter is usually a submission or template-reference problem, while a missing task output is usually a producer-task failure or path problem.

> **Pause and predict:** If `generate-message` writes to `/tmp/other.txt` but `valueFrom.path` still points at `/tmp/message.txt`, what phase should you expect for `consume`? Explain whether the consumer is broken, the dependency is broken, or the producer output contract is broken.

Artifacts solve a different problem. The producer writes a file or directory, declares it as an output artifact, and the consumer declares an input artifact with a path where Argo should make it available. This keeps file content out of workflow status and gives the platform a place to manage retention, size, and access control.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: artifacts-example-
  namespace: argo
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
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            mkdir -p /tmp/out
            echo '{"records":[1,2,3,4,5]}' > /tmp/out/data.json
      outputs:
        artifacts:
          - name: output
            path: /tmp/out/data.json

    - name: process-file
      inputs:
        artifacts:
          - name: input
            path: /tmp/input.json
      container:
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            cat /tmp/input.json
            echo "Processed artifact"
```

For a local lab, Argo may use a default artifact mechanism depending on the installation mode. For a production platform, configure an explicit artifact repository such as S3-compatible storage, GCS, or another supported backend. The workflow should not pretend artifacts are invisible; they are a storage system with cost, permissions, lifecycle policy, and failure modes.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: s3-artifacts-
  namespace: argo
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
        image: python:3.12-alpine
        command: [python, -c]
        args:
          - |
            import json
            data = {"results": [1, 2, 3, 4, 5]}
            with open("/tmp/data.json", "w", encoding="utf-8") as handle:
                json.dump(data, handle)
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
        image: python:3.12-alpine
        command: [python, -c]
        args:
          - |
            import json
            with open("/tmp/data.json", encoding="utf-8") as handle:
                data = json.load(handle)
            print(f"Sum: {sum(data['results'])}")
```

This example uses `artifactRepositoryRef` to make the storage choice visible. The workflow writer should know whether artifacts are stored centrally, encrypted, retained, and accessible to the right teams. A workflow that produces model files or customer-derived reports is making a data governance decision, not just a YAML decision.

A senior design habit is to write the task contract in words before writing YAML. For example: "The extractor produces one compressed JSON Lines file named `raw-orders`; the transformer consumes `raw-orders` at `/input/orders.jsonl.gz` and produces a validation count parameter plus a transformed Parquet artifact." That sentence prevents ambiguous template names, accidental string outputs, and hidden coupling through image behavior.

## Loops, Fan-Out, and Controlled Parallelism

Loops are where Argo starts to feel more powerful than a traditional CI system. `withItems` expands a task over a static list, while `withParam` expands a task over a JSON array produced at runtime. The result is fan-out: one logical task definition becomes many node executions.

The static loop below processes three items. Each item becomes the `item` input parameter for one task execution. Argo can run the expanded tasks concurrently unless dependencies or parallelism limits prevent it.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: parallel-loop-
  namespace: argo
spec:
  entrypoint: main
  parallelism: 3
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
        image: alpine:3.20
        command: [echo]
        args: ["Processing: {{inputs.parameters.item}}"]
```

The `parallelism: 3` field is not decorative. It tells Argo the maximum number of pods from the workflow that may run at once. In a tiny lab that limit may not matter, but in a shared cluster it is the difference between a batch job that coexists with production and a batch job that floods the control plane.

A dynamic loop uses a producer task to generate the list. The producer prints a JSON array as its result, and the fan-out task consumes that JSON with `withParam`. This pattern is common for nightly data processing because the list of partitions, files, tenants, or experiments may not be known until the workflow starts.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: fan-out-
  namespace: argo
spec:
  entrypoint: main
  parallelism: 4
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
        image: python:3.12-alpine
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
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            echo "Processing: {{inputs.parameters.item}}"
            sleep 2

    - name: aggregate-results
      container:
        image: alpine:3.20
        command: [echo]
        args: ["Aggregation runs after every expanded process-items task completes"]
```

> **Active check:** Change `parallelism` from `4` to `2` in the fan-out example and predict the effect on total runtime. The graph shape does not change, but the scheduler behavior does. That distinction is central to operating Argo responsibly.

Large fan-out workflows need more than a single workflow-level cap. You may need namespace `ResourceQuota`, `LimitRange`, lower-priority classes for batch workloads, pod garbage collection, workflow TTL cleanup, and batching logic that converts a huge item list into smaller groups. Argo makes it easy to express "do this for every item," but Kubernetes still has finite control-plane and node capacity.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: controlled-backtest-
  namespace: argo
spec:
  entrypoint: main
  parallelism: 50
  podGC:
    strategy: OnPodCompletion
  ttlStrategy:
    secondsAfterCompletion: 3600

  templates:
    - name: main
      dag:
        tasks:
          - name: generate-batches
            template: create-batches

          - name: process-batch
            template: batch-processor
            dependencies: [generate-batches]
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
        image: python:3.12-alpine
        command: [python]
        source: |
          import json
          batches = [
              {"start": index * 100, "end": (index + 1) * 100}
              for index in range(100)
          ]
          print(json.dumps(batches))

    - name: batch-processor
      inputs:
        parameters:
          - name: batch
      container:
        image: python:3.12-alpine
        command: [python, -c]
        args:
          - |
            import json
            batch = json.loads("""{{inputs.parameters.batch}}""")
            print(f"Processing records {batch['start']} through {batch['end']}")
        resources:
          requests:
            cpu: "200m"
            memory: "512Mi"
          limits:
            cpu: "500m"
            memory: "1Gi"
      retryStrategy:
        limit: 3
        backoff:
          duration: 30s
          factor: 2

    - name: aggregate-results
      container:
        image: alpine:3.20
        command: [echo]
        args: ["Aggregating all completed batches"]
```

The batching approach is slower than launching every record as a pod, but it is usually more reliable. Each pod has scheduling overhead, status writes, log collection, image pull behavior, and cleanup. If a record takes milliseconds to process, launching one pod per record is usually worse than processing a batch inside each pod.

## Reuse with WorkflowTemplates

A `WorkflowTemplate` is a reusable workflow definition stored in the cluster. It is useful when platform teams want to publish a supported pipeline shape, such as "clone, test, build, scan, publish," while application teams provide only the repository, branch, image, and environment values. Reuse matters because copy-pasted workflow YAML ages badly: one team gets the new timeout, another team keeps the old risky retry policy, and a third team quietly removes resource limits to make a deadline.

The example below defines a reusable CI pipeline. The workflow-level arguments declare the public contract: callers must provide a repository and image, while `branch` defaults to `main`. The graph then passes those values into templates at the point where they are needed.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: ci-pipeline
  namespace: argo
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
        parameters:
          - name: repo
          - name: branch
      container:
        image: alpine/git:2.45.2
        command: [git, clone, "--branch", "{{inputs.parameters.branch}}", "{{inputs.parameters.repo}}", "/work"]

    - name: run-tests
      container:
        image: golang:1.22
        command: [sh, -c]
        args: ["echo 'go test ./... would run here'"]

    - name: build-push
      inputs:
        parameters:
          - name: image
      container:
        image: gcr.io/kaniko-project/executor:v1.23.2-debug
        args: ["--destination={{inputs.parameters.image}}"]
```

A caller can then submit a small Workflow that references the shared template. This makes the run-specific file shorter and moves the platform-owned graph into one controlled object.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: run-ci-
  namespace: argo
spec:
  workflowTemplateRef:
    name: ci-pipeline
  arguments:
    parameters:
      - name: repo
        value: https://github.com/example/app.git
      - name: image
        value: ghcr.io/example/app:latest
```

The hidden risk is versioning. A cluster-scoped or namespace-scoped WorkflowTemplate can change underneath callers unless the platform treats it like an API. Senior platform teams document template contracts, publish change notes, test common caller workflows, and provide a migration path when arguments or behavior change.

> **Active check:** Imagine one team needs a longer test timeout and another team needs a different build image. Decide whether those should be template parameters, separate WorkflowTemplates, or team-owned workflow YAML. Your answer should mention how often the value changes, who owns the risk, and whether the change affects the shared contract.

WorkflowTemplates are also a governance boundary. Platform teams can require certain images, resource requests, retries, artifact conventions, labels, and exit handlers in the shared template. Application teams still get flexibility through parameters, but the dangerous defaults are centralized.

## Error Handling, Timeouts, and Debugging

Errors in Argo Workflows fall into several categories. Your application can fail, a pod can fail before the application starts, an artifact can fail to upload or download, a dependency can wait forever because an upstream node failed, or the controller can be unable to create more pods because of quota or RBAC. Good error handling starts by deciding which failures are worth retrying and which failures should stop the graph immediately.

| Failure type | Typical signal | Retry decision | Better control |
|--------------|----------------|----------------|----------------|
| Transient network call | Exit code from application, timeout from dependency, temporary service error. | Retry with backoff if the operation is idempotent. | `retryStrategy` with bounded attempts and clear logs. |
| Deterministic validation failure | Same bad input fails every attempt. | Do not retry blindly because it wastes cluster capacity. | Fail fast and publish validation artifacts. |
| Resource exhaustion | Pod shows `OOMKilled`, `Evicted`, or long `Pending`. | Retry only after changing resources, placement, or input size. | Requests, limits, batching, quotas, and node capacity checks. |
| Optional branch failure | A report or non-blocking scan fails while core output is still useful. | Continue only if the business rule allows degraded output. | `continueOn` and explicit downstream handling. |
| Hung task | Pod runs far longer than the expected envelope. | Terminate and retry only when the operation is safe. | `activeDeadlineSeconds` and external idempotency. |

A retry strategy belongs on a template because the operation knows whether retrying is safe. Pulling a file from object storage is often retryable. Charging a customer, publishing a release, or sending a deployment command may not be retryable unless the operation is idempotent. The YAML cannot know that business rule for you.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: retry-example-
  namespace: argo
spec:
  entrypoint: flaky-task
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
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            value=$((RANDOM % 2))
            echo "Generated value: ${value}"
            exit "${value}"
```

The `limit` prevents infinite retry loops, and `backoff` gives dependent systems time to recover. Without backoff, a workflow can amplify an outage by hammering a dependency that is already failing. Without a limit, a workflow can consume cluster capacity long after the original run has stopped being useful.

`continueOn` is for explicitly optional work. It should not be used as a quick way to make a red workflow green. If a required security scan fails and the workflow deploys anyway, the YAML is now hiding risk from reviewers and operators.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: continue-example-
  namespace: argo
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: optional-report
            template: might-fail
            continueOn:
              failed: true

          - name: required-deploy
            template: must-succeed
            dependencies: [optional-report]

    - name: might-fail
      container:
        image: alpine:3.20
        command: [sh, -c]
        args: ["echo 'non-blocking report failed'; exit 1"]

    - name: must-succeed
      container:
        image: alpine:3.20
        command: [echo]
        args: ["Deploy is allowed only because optional-report is truly optional"]
```

Timeouts protect the cluster and the business process. A task that normally takes five minutes but has been running for two hours is no longer "just slow"; it is consuming resources, delaying downstream work, and confusing operators. `activeDeadlineSeconds` gives the template an upper bound.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: timeout-example-
  namespace: argo
spec:
  entrypoint: limited-task
  templates:
    - name: limited-task
      activeDeadlineSeconds: 300
      container:
        image: alpine:3.20
        command: [sleep, "600"]
```

> **Pause and predict:** The timeout example sleeps for ten minutes but has a five-minute active deadline. Predict the workflow phase, the pod phase, and the kind of operator message you would want in a production runbook. Then explain why a timeout is better than letting the pod run until someone notices.

A practical debugging workflow starts broad and narrows down. First get the workflow graph and node phases, then identify the failed pod, then inspect pod events and logs, then decide whether the failure is code, scheduling, resources, artifacts, or platform configuration.

```bash
argo list -n argo
argo get -n argo @latest
argo logs -n argo @latest

WORKFLOW_NAME="$(argo list -n argo -o name | head -n 1)"
argo get -n argo "${WORKFLOW_NAME}" -o yaml > workflow-status.yaml

k -n argo get pods
k -n argo describe pod <pod-name>
k -n argo logs <pod-name> --previous
k -n argo get events --sort-by=.lastTimestamp
```

If a task is `Pending`, inspect scheduling constraints, quota, resource requests, image pulls, and service accounts. If a task is `Error`, inspect init containers and artifact handling before assuming the application code failed. If a task is `Failed`, the main container usually exited non-zero, so logs and exit codes are the first stop.

The most common debugging mistake is reading the workflow YAML only. The YAML tells you intended behavior, but Kubernetes status tells you observed behavior. An Argo operator needs both: the graph explains why a task should run, and pod status explains why it did or did not run.

## Argo Events and External Triggers

Argo Workflows can be submitted manually, scheduled by CronWorkflow, created by another controller, or triggered through Argo Events. Event integration is useful when the workflow is naturally caused by something outside the cluster: a Git push, an object appearing in storage, a message on a queue, or a webhook from a data platform.

The example below shows a Sensor creating a Workflow from a GitHub push event. The important idea is not the exact GitHub fields; it is the mapping from event payload into workflow parameters. A trigger should create a workflow with explicit inputs, not a workflow that reaches back into an opaque event blob at every task.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: github-sensor
  namespace: argo
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
                namespace: argo
              spec:
                workflowTemplateRef:
                  name: ci-pipeline
                arguments:
                  parameters:
                    - name: repo
                      value: ""
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

Event-driven workflows need deduplication, authorization, and rate limits. A webhook endpoint that blindly creates workflows can become a denial-of-service path into your cluster. Treat event sources like public APIs: authenticate them, validate payloads, limit the trigger rate, and give the resulting workflow a service account with only the permissions it needs.

> **Active check:** A storage bucket sends one event for every uploaded object, and a partner accidentally uploads several thousand small files in a minute. Decide where you would add protection: event source, sensor, workflow `parallelism`, namespace quota, batching logic, or all of them. Explain which layer fails open if the previous layer misses the spike.

## Worked Example: Designing a Nightly ETL Workflow

A useful worked example is a nightly ETL pipeline. The pipeline extracts from three databases in parallel, transforms each dataset, loads the warehouse only after all transforms succeed, runs several quality checks, and sends a notification regardless of outcome. This shape teaches most Argo design choices without becoming a toy.

```ascii
┌────────────────┐      ┌─────────────────┐
│ extract-users  │─────►│ transform-users │─────┐
└────────────────┘      └─────────────────┘     │
                                                  │
┌────────────────┐      ┌─────────────────┐     ▼
│ extract-orders │─────►│ transform-orders│──► load warehouse
└────────────────┘      └─────────────────┘     │
                                                  │
┌──────────────────┐    ┌───────────────────┐   ▼
│ extract-products │───►│ transform-products│── quality checks
└──────────────────┘    └───────────────────┘   │
                                                  ▼
                                          exit notification
```

The graph has two kinds of parallelism. Extracts can run together because the source systems are independent, and quality checks can run together because they read the loaded warehouse state. The load task is a fan-in point because it should not run until all transformed artifacts exist.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: nightly-etl-
  namespace: argo
spec:
  entrypoint: main
  parallelism: 12
  activeDeadlineSeconds: 14400
  onExit: exit-handler
  arguments:
    parameters:
      - name: run-date
        value: "2026-04-26"

  templates:
    - name: main
      dag:
        tasks:
          - name: extract-users
            template: extract
            arguments:
              parameters:
                - name: source
                  value: users

          - name: extract-orders
            template: extract
            arguments:
              parameters:
                - name: source
                  value: orders

          - name: extract-products
            template: extract
            arguments:
              parameters:
                - name: source
                  value: products

          - name: transform-users
            template: transform
            dependencies: [extract-users]
            arguments:
              parameters:
                - name: dataset
                  value: users
              artifacts:
                - name: raw-data
                  from: "{{tasks.extract-users.outputs.artifacts.data}}"

          - name: transform-orders
            template: transform
            dependencies: [extract-orders]
            arguments:
              parameters:
                - name: dataset
                  value: orders
              artifacts:
                - name: raw-data
                  from: "{{tasks.extract-orders.outputs.artifacts.data}}"

          - name: transform-products
            template: transform
            dependencies: [extract-products]
            arguments:
              parameters:
                - name: dataset
                  value: products
              artifacts:
                - name: raw-data
                  from: "{{tasks.extract-products.outputs.artifacts.data}}"

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

          - name: quality-checks
            template: run-quality-check
            dependencies: [load-warehouse]
            arguments:
              parameters:
                - name: check
                  value: "{{item}}"
            withItems:
              - row-count
              - null-check
              - duplicate-check
              - freshness
              - business-rules

    - name: extract
      inputs:
        parameters:
          - name: source
      retryStrategy:
        limit: 3
        backoff:
          duration: 60s
          factor: 2
      activeDeadlineSeconds: 1800
      container:
        image: python:3.12-alpine
        command: [python, -c]
        args:
          - |
            import json
            import pathlib
            source = "{{inputs.parameters.source}}"
            pathlib.Path("/tmp/out").mkdir(parents=True, exist_ok=True)
            with open("/tmp/out/data.json", "w", encoding="utf-8") as handle:
                json.dump({"source": source, "records": [1, 2, 3]}, handle)
            print(f"extracted {source}")
      outputs:
        artifacts:
          - name: data
            path: /tmp/out/data.json

    - name: transform
      inputs:
        parameters:
          - name: dataset
        artifacts:
          - name: raw-data
            path: /tmp/raw.json
      container:
        image: python:3.12-alpine
        command: [python, -c]
        args:
          - |
            import json
            dataset = "{{inputs.parameters.dataset}}"
            with open("/tmp/raw.json", encoding="utf-8") as handle:
                payload = json.load(handle)
            payload["dataset"] = dataset
            payload["validated"] = True
            with open("/tmp/transformed.json", "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            print(f"transformed {dataset}")
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"
      outputs:
        artifacts:
          - name: transformed
            path: /tmp/transformed.json

    - name: load
      inputs:
        artifacts:
          - name: users
            path: /tmp/data/users.json
          - name: orders
            path: /tmp/data/orders.json
          - name: products
            path: /tmp/data/products.json
      retryStrategy:
        limit: 2
      container:
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            ls -l /tmp/data
            echo "loading warehouse for {{workflow.parameters.run-date}}"

    - name: run-quality-check
      inputs:
        parameters:
          - name: check
      container:
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            echo "running quality check {{inputs.parameters.check}}"
            sleep 1

    - name: exit-handler
      steps:
        - - name: notify-status
            template: notify

    - name: notify
      container:
        image: alpine:3.20
        command: [echo]
        args: ["Nightly ETL finished with status {{workflow.status}}"]
```

The field choices are as important as the graph. `parallelism: 12` prevents a quality-check expansion from consuming unlimited cluster capacity. Extract tasks have retries because source connections can fail transiently. Transform tasks have resource requests and limits because data shape can change. `onExit` provides a single notification path for success, failure, or error, which prevents silent failed runs.

This worked example is intentionally complete before the exercise asks you to build a similar workflow. You have seen the design sequence: draw dependencies, choose parameters versus artifacts, place retries only where they are safe, bound parallelism, add timeouts, and provide an exit path. The exercise later changes the scenario so you must apply the same reasoning rather than copy the same YAML.

## War Story: Uncontrolled Parallelism Can Overload a Cluster

A financial analytics team once used Argo Workflows to backtest many strategy variants. The first prototype worked beautifully with a few dozen inputs, so the team scaled the input list without changing the workflow-level controls. The workflow did exactly what it was told to do: it tried to create an enormous number of pods quickly.

```ascii
THE 10,000 POD INCIDENT TIMELINE
────────────────────────────────────────────────────────────────────────
FRIDAY, 2:00 PM    Workflow submitted: 10,000 pods requested
FRIDAY, 2:01 PM    1,000 pods scheduled immediately
FRIDAY, 2:02 PM    Kubernetes API server latency spikes to 30s
FRIDAY, 2:05 PM    etcd disk I/O at 100%, cluster becoming unresponsive
FRIDAY, 2:08 PM    Production trading systems experiencing timeouts
FRIDAY, 2:10 PM    kubectl commands failing: "context deadline exceeded"
FRIDAY, 2:15 PM    INCIDENT DECLARED: Production trading halted
FRIDAY, 2:30 PM    Workflow manually terminated while kubectl was still failing
FRIDAY, 2:45 PM    Cluster recovery begins
FRIDAY, 4:00 PM    Normal operations restored
FRIDAY, 4:30 PM    Post-incident analysis starts

IMPACT ASSESSMENT
────────────────────────────────────────────────────────────────────────
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

The root cause was not that Argo was unreliable. The root cause was that the workflow treated cluster capacity as infinite. Every pod creation created API server work, scheduler work, etcd writes, admission checks, secret lookups, and status updates. The workflow became an accidental load test of the control plane.

```ascii
ROOT CAUSE ANALYSIS
────────────────────────────────────────────────────────────────────────
1. Argo Workflow Controller attempted to create 10,000 pods rapidly
   └── API server received a burst of pod creation requests

2. Each pod creation triggered several Kubernetes operations
   ├── Pod object write to etcd
   ├── Secret and service account lookups
   ├── Scheduling decisions
   ├── Volume and image pull coordination
   └── Status updates from kubelet and controllers

3. etcd write-ahead log could not keep up
   └── Latency spike caused timeouts across unrelated cluster operations

4. Kubernetes controllers started missing normal reconciliation windows
   └── Production workloads could not scale or report health consistently

5. Trading systems lost supporting service connectivity
   └── Failsafe triggered and automated trading halted
```

The fix was defense in depth. The team added workflow-level parallelism, batched inputs, cleaned completed pods quickly, set TTL cleanup, applied namespace quotas, added LimitRanges, and moved batch workflows to lower scheduling priority. No single control was trusted as the only safeguard.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: backtest-all-strategies-v2
  namespace: argo
spec:
  entrypoint: main
  parallelism: 50
  podGC:
    strategy: OnPodCompletion
  ttlStrategy:
    secondsAfterCompletion: 3600
  templates:
    - name: main
      dag:
        tasks:
          - name: generate-batches
            template: create-batches

          - name: process-batch
            template: batch-processor
            dependencies: [generate-batches]
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
        image: python:3.12-alpine
        command: [python]
        source: |
          import json
          batches = [
              {"start": index * 100, "end": (index + 1) * 100}
              for index in range(100)
          ]
          print(json.dumps(batches))

    - name: batch-processor
      inputs:
        parameters:
          - name: batch
      container:
        image: python:3.12-alpine
        command: [python, -c]
        args:
          - |
            import json
            batch = json.loads("""{{inputs.parameters.batch}}""")
            print(f"running batch {batch['start']} to {batch['end']}")
        resources:
          requests:
            cpu: "200m"
            memory: "512Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
      retryStrategy:
        limit: 3
        backoff:
          duration: 30s
          factor: 2

    - name: aggregate-results
      container:
        image: python:3.12-alpine
        command: [python, -c]
        args: ["print('aggregate results')"]
```

```yaml
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
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: batch-workflow
value: -100
globalDefault: false
description: "Low priority for batch data processing"
```

```ascii
BEFORE VS AFTER
────────────────────────────────────────────────────────────────────────
                            Before          After
Max concurrent pods:        10,000          50
Workflow duration:          FAILED          4 hours
API server latency:         30+ seconds     < 100ms
Production impact:          INCIDENT        None
Success rate:               0%              99.8%
Cluster stability:          Compromised     Stable
```

The lesson is not "avoid Argo for large work." The lesson is that a workflow engine makes large work easy to describe, so the platform must make safe execution easy as well. Parallelism is a dial, batching is a design tool, and Kubernetes control-plane capacity is a shared dependency.

## Choosing Argo Workflows, Tekton, or Airflow

Tool choice should follow workload shape. Tekton is often a better fit for standardized CI/CD tasks because its model and ecosystem center on pipeline runs, catalog tasks, and supply-chain integrations. Airflow remains common for scheduled data workflows with rich operator ecosystems and external-system orchestration. Argo Workflows is strongest when Kubernetes-native execution and graph-shaped parallel work are the core requirement.

| Scenario | Stronger default | Why that choice usually wins | When to reconsider |
|----------|------------------|------------------------------|--------------------|
| Standard clone-test-build-publish for many services | Tekton | CI/CD primitives, catalog tasks, and supply-chain tooling match the job. | Use Argo if the pipeline becomes graph-heavy or batch-oriented. |
| ML training with many parameter combinations | Argo Workflows | Dynamic fan-out, artifact passing, pod-native execution, and long-running jobs fit naturally. | Use Airflow if most work happens in external managed services. |
| Nightly warehouse orchestration across many SaaS APIs | Airflow | Mature scheduling and provider ecosystem can reduce custom glue. | Use Argo if each stage is containerized and Kubernetes is the execution plane. |
| Event-driven image or document processing | Argo Workflows plus Argo Events | Event payloads can create bounded Kubernetes workflows with clear graph status. | Add a queue if events can arrive faster than the cluster should process them. |
| GitOps deployment after image publication | Tekton or Argo CD integration | Deployment may be better represented as a GitOps reconciliation than a custom pod. | Use Argo Workflows for pre-deploy batch validation or complex promotion gates. |

The wrong tool is often the one chosen because a team already likes it, not because the workload fits it. Argo can run CI/CD, but that does not make every CI/CD flow an Argo problem. Tekton can express graphs, but that does not make it the best choice for a giant simulation fan-out. Airflow can trigger Kubernetes jobs, but that does not mean Kubernetes-native artifact and pod lifecycle are first-class in every Airflow deployment.

A practical evaluation question is: where should the state live? If the most important state is Kubernetes pod execution, artifacts from containers, and graph node status, Argo is a strong candidate. If the most important state is a chain of standardized delivery tasks, Tekton may be cleaner. If the most important state is a schedule of external system operations, Airflow may be easier to operate and staff.

## Did You Know?

- **Argo Workflows runs each workflow step as a Kubernetes pod**, which means normal cluster controls such as service accounts, resource limits, node selection, and pod events remain central to debugging.
- **WorkflowTemplates are API contracts as much as reusable YAML**, because changing an argument name, default value, retry policy, or artifact convention can break teams that submit against the template.
- **Large workflows usually fail operationally before they fail syntactically**, because API server throughput, scheduler capacity, artifact storage, and namespace quota become the limiting systems.
- **The Argo project includes Workflows, CD, Events, and Rollouts**, and many production platforms combine them rather than expecting one tool to cover every delivery concern.

## Common Mistakes

| Mistake | Why it causes trouble | Better approach |
|---------|-----------------------|-----------------|
| Treating a dependency as shared storage | A downstream pod waits for the upstream pod to finish, but it does not inherit that pod's filesystem. | Pass small values as parameters and files or directories as artifacts. |
| Launching one pod per tiny record | Pod startup, scheduling, status, and cleanup overhead can dominate the actual work. | Batch small records inside each pod and cap workflow `parallelism`. |
| Retrying every failure automatically | Deterministic validation errors waste capacity and can hide the real problem. | Retry only idempotent transient operations and fail fast on bad input. |
| Using `continueOn` to hide required failures | The workflow may turn red business risk into green automation status. | Reserve `continueOn` for explicitly optional work with clear downstream handling. |
| Leaving resource requests out of templates | The scheduler cannot make good placement decisions and nodes can be overcommitted. | Set requests and limits that match observed memory and CPU behavior. |
| Copy-pasting WorkflowTemplates into every repository | Fixes and policy improvements drift because every copy becomes its own fork. | Publish supported templates and keep caller workflows small. |
| Debugging only with `argo get` | Argo status shows graph state, but pod events reveal scheduling, image, quota, and runtime failures. | Combine `argo get`, `argo logs`, `k describe pod`, and namespace events. |
| Exposing event triggers without rate and identity controls | External spikes or unauthorized payloads can create uncontrolled workflow load. | Authenticate events, validate payloads, batch inputs, and enforce namespace quotas. |

## Quiz

### Question 1

Your team converts a nightly data job into an Argo Workflow. The first task clones a repository into `/work`, and the second task fails because `/work` does not exist. The dependency is configured correctly and the first task succeeded. What should you change, and why?

<details>
<summary>Show Answer</summary>

The dependency only controls execution order; it does not share the producer pod's filesystem with the consumer pod. The correct fix is to declare the cloned repository, generated files, or build context as an output artifact from the first task and pass it as an input artifact to the second task. If the downstream task only needs a commit SHA or image tag, pass that small value as a parameter instead.

A senior answer also checks whether cloning should happen in every task, whether a shared volume is appropriate for the cluster and workflow shape, or whether a build system should consume the repository directly. The key is to make the data contract explicit rather than relying on pod-local paths.
</details>

### Question 2

A workflow processes a runtime-generated list of customer partitions. The generator task prints a JSON array, and the processor task uses `withParam`. During a launch, the list grows from dozens of partitions to several thousand. The workflow is valid but starts harming other workloads. Which controls would you add first?

<details>
<summary>Show Answer</summary>

Add workflow-level `parallelism`, consider batching partitions inside each pod, and enforce namespace `ResourceQuota` plus `LimitRange` so the workflow cannot exceed agreed capacity. If the input spike is expected to recur, add rate control or batching before workflow creation as well. `withParam` is the right feature for dynamic fan-out, but it does not automatically make the fan-out safe.

The strongest answer separates graph correctness from operational safety. The graph may correctly express "process every partition," while the platform still needs concurrency limits, resource requests, priority, cleanup, and observability. Safe throughput is an engineering decision, not a YAML default.
</details>

### Question 3

A security scan task sometimes fails because the scanner service returns a temporary network error. Another task fails when a policy violation is found. A teammate proposes the same `retryStrategy` for both tasks. How would you evaluate that proposal?

<details>
<summary>Show Answer</summary>

The temporary network error is a good candidate for bounded retries with backoff because a later attempt may succeed and the scan operation is usually safe to repeat. The policy violation should not be retried blindly because the same input is likely to fail again, and repeated attempts waste cluster capacity while delaying feedback. The policy task should fail clearly and publish enough logs or artifacts for the owner to fix the violation.

The decision depends on idempotency and failure class. Retry transient infrastructure or dependency failures. Do not retry deterministic validation failures unless the task itself can change the condition it is validating.
</details>

### Question 4

Your platform team publishes a `WorkflowTemplate` for application CI. One product team asks to remove resource limits because their tests occasionally hit memory ceilings. Another team asks to increase the test timeout for integration tests. Which change belongs in the shared template, and which might belong in parameters or a separate template?

<details>
<summary>Show Answer</summary>

Removing resource limits from the shared template is usually a platform risk and should not be accepted as a one-team convenience. The better response is to measure the test workload, set realistic requests and limits, or offer a controlled parameter with approved bounds if teams have legitimate size differences. A longer timeout may be a template parameter if it is common and safe within a maximum, or a separate template if it represents a distinct class of workflow such as long integration testing.

The evaluation should consider ownership, blast radius, and contract stability. Shared templates encode safe defaults for many users, so changes that weaken guardrails require stronger justification than changes that expose controlled configuration.
</details>

### Question 5

A workflow has an optional report-generation task with `continueOn.failed: true`. A downstream notification says the release is ready even when the report failed. The business now treats the report as required for regulated releases but optional for internal previews. How should the workflow design change?

<details>
<summary>Show Answer</summary>

The workflow should make the business rule explicit instead of using one unconditional `continueOn`. One design is to add a workflow parameter such as `release-type`, run the report task, and gate the downstream release notification differently for regulated releases and previews. For regulated releases, report failure should block readiness; for previews, the notification should clearly state that the optional report failed.

The important point is that optionality is not a technical convenience. It is a policy decision. The workflow should encode the policy clearly enough that reviewers and operators can see when a failed task is acceptable.
</details>

### Question 6

A model-training workflow fails with `OOMKilled` during one fan-out branch. The same template succeeds for smaller input partitions. What investigation steps would you take, and what design changes might fix the issue?

<details>
<summary>Show Answer</summary>

Start with `argo get` to identify the failed node, then inspect the pod with `k describe pod`, check logs including previous logs if the container restarted, and compare the failed partition size with successful partitions. Look at resource requests and limits, node memory pressure, and whether the task accumulates large artifacts in memory. The likely causes are an undersized memory limit, an unusually large partition, application memory growth, or a batching strategy that creates uneven chunks.

Fixes include increasing memory limits based on measurements, splitting large partitions into smaller batches, changing the application to stream data, setting clearer input-size limits, or routing memory-heavy tasks to appropriate nodes. Retrying the same pod without changing the resource or input condition is unlikely to help.
</details>

### Question 7

A team wants to use Argo Workflows for every pipeline because they already operate Argo CD. They have three workloads: simple microservice CI, hyperparameter training with many parallel runs, and scheduled SaaS-to-warehouse extraction. How would you recommend tools?

<details>
<summary>Show Answer</summary>

For simple microservice CI, Tekton or another CI-focused system may be cleaner because standardized clone, test, build, and publish flows match its strengths. For hyperparameter training with many parallel runs, Argo Workflows is a strong fit because dynamic fan-out, artifacts, and Kubernetes pod execution are central. For scheduled SaaS-to-warehouse extraction, Airflow may be the better default if provider integrations and external orchestration dominate, while Argo is reasonable if each stage is already containerized and Kubernetes-native execution is the main requirement.

The recommendation should be based on workload shape, state location, operator skill, and integration needs. Sharing the Argo name with Argo CD is not enough reason to force every pipeline into Argo Workflows.
</details>

### Question 8

A GitHub webhook triggers an Argo Events Sensor, and the Sensor creates a Workflow for each push. A misconfigured repository starts sending repeated push events. The cluster remains healthy, but the workflow namespace fills with pending runs. What should you change?

<details>
<summary>Show Answer</summary>

Add protection at multiple layers: authenticate and validate the webhook, deduplicate or rate-limit events before workflow creation, set workflow `parallelism`, enforce namespace quota, and add TTL cleanup for completed workflows. If pending runs are not useful after a newer event arrives, add cancellation or superseding logic so stale runs do not consume queue space.

The answer should not rely on only one control. Event-driven systems need upstream filtering and downstream resource protection because either layer can fail or be bypassed.
</details>

## Hands-On Exercise

### Scenario: Build a Bounded Data Processing Workflow

You are supporting a platform team that needs a small but realistic Argo Workflow for data processing. The workflow must generate a runtime list of work items, process those items with bounded parallelism, aggregate the result, and expose enough status for an operator to debug a failed task. You will first run the healthy version, then intentionally break one template and practice the debugging path.

### Step 1: Create a Disposable Cluster and Install Argo

Use a disposable local cluster for this exercise. The commands assume `kind` is installed and your current shell has access to Docker or another supported local container runtime.

```bash
kind create cluster --name argo-lab

alias k=kubectl

k create namespace argo

k apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml

k patch deployment argo-server -n argo --type='json' -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--auth-mode=server"}]'

k -n argo wait --for=condition=ready pod -l app=workflow-controller --timeout=120s

k -n argo port-forward svc/argo-server 2746:2746
```

Open `https://127.0.0.1:2746` while the port-forward runs. This authentication mode is for a disposable lab only. Do not copy it into a shared cluster.

### Step 2: Create the Workflow Manifest

Create a file named `bounded-data-pipeline.yaml`. This workflow uses `withParam` for dynamic fan-out, `parallelism: 3` to limit concurrency, explicit resources for the processing pods, and a final aggregation task that waits for every expanded processing node.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: bounded-data-pipeline-
  namespace: argo
spec:
  entrypoint: main
  parallelism: 3
  podGC:
    strategy: OnPodCompletion
  ttlStrategy:
    secondsAfterCompletion: 1800

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
        image: python:3.12-alpine
        command: [python]
        source: |
          import json
          items = [f"item-{index}" for index in range(8)]
          print(json.dumps(items))

    - name: process
      inputs:
        parameters:
          - name: item
      activeDeadlineSeconds: 60
      retryStrategy:
        limit: 2
        backoff:
          duration: 5s
          factor: 2
      container:
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            echo "Processing {{inputs.parameters.item}}"
            sleep 2
            echo "Finished {{inputs.parameters.item}}"
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "250m"
            memory: "128Mi"

    - name: aggregate
      container:
        image: alpine:3.20
        command: [echo]
        args: ["All bounded processing tasks completed"]
```

### Step 3: Submit and Observe the Healthy Run

Submit the workflow with the Argo CLI and watch it complete. Then inspect the graph, logs, and pods so you connect the workflow view with Kubernetes objects.

```bash
argo submit -n argo bounded-data-pipeline.yaml --watch

argo get -n argo @latest

argo logs -n argo @latest

k -n argo get pods
```

While the run is active, observe that only a small number of processing pods run concurrently. The list contains more items than the parallelism limit, so Argo must queue some expanded nodes until running nodes finish.

### Step 4: Break the Workflow on Purpose

Edit the `process` template command so it fails for one item. This turns the exercise into a debugging scenario rather than a copy-and-run lab.

```yaml
        args:
          - |
            echo "Processing {{inputs.parameters.item}}"
            if [ "{{inputs.parameters.item}}" = "item-3" ]; then
              echo "simulated bad partition"
              exit 1
            fi
            sleep 2
            echo "Finished {{inputs.parameters.item}}"
```

Submit the modified workflow and inspect the result.

```bash
argo submit -n argo bounded-data-pipeline.yaml --watch

argo get -n argo @latest

argo logs -n argo @latest
```

### Step 5: Debug Like an Operator

Use the workflow graph to identify the failed node, then use Kubernetes status to inspect the pod. Your goal is to connect the Argo failure to the container exit and prove that the aggregate task waited because an upstream expanded task failed.

```bash
argo get -n argo @latest

k -n argo get pods

k -n argo describe pod <failed-pod-name>

k -n argo logs <failed-pod-name>
```

Explain your finding in one short runbook note. A good note says which item failed, what the container printed, whether retries happened, whether the failure is transient or deterministic, and what change would fix the workflow.

### Step 6: Improve the Design

Change the workflow so deterministic bad input fails fast but transient processing still has retries. You can keep the simulated failure, but describe why retrying it is wasteful. Then remove the simulated failure and run the workflow successfully again.

```bash
argo submit -n argo bounded-data-pipeline.yaml --watch

argo get -n argo @latest
```

### Success Criteria

- [ ] Argo Workflows is installed in the `argo` namespace and the controller pod is ready.
- [ ] You can submit a Workflow and inspect it with both `argo get` and Kubernetes pod commands.
- [ ] The workflow uses `withParam` to process a runtime-generated list of items.
- [ ] `parallelism: 3` visibly limits concurrent processing pods.
- [ ] You can explain why the aggregate task waits for all expanded processing nodes.
- [ ] You intentionally caused one processing task to fail and traced the failure from workflow node to pod logs.
- [ ] You can explain whether the failure should be retried, fixed in code, or handled as bad input.
- [ ] The final workflow succeeds after you remove the simulated failure.

### Cleanup

Delete the disposable cluster when you are finished. This removes the Argo installation, Workflow CRDs, pods, and any lab state created inside the cluster.

```bash
kind delete cluster --name argo-lab
```

## Next Module

Continue to [Security Tools Toolkit](/platform/toolkits/security-quality/security-tools/) where you will evaluate Vault, OPA, Falco, and supply-chain security tools for platform engineering workflows.

## Sources

- [Argo Workflows Overview](https://argoproj.github.io/workflows/) — Official overview of Argo Workflows concepts, DAG capabilities, and common Kubernetes workload patterns.
- [Tekton Overview](https://tekton.dev/docs/concepts/overview/) — Official Tekton overview describing its Kubernetes-native CI/CD model and core concepts.
- [Argo Project Overview](https://argoproj.github.io/) — Official project landing page summarizing the Argo ecosystem tools, including Workflows, CD, Events, and Rollouts.
- [Considerations for Large Clusters](https://kubernetes.io/docs/setup/best-practices/cluster-large/) — Kubernetes guidance on control-plane, scheduler, and etcd limits in large clusters.
