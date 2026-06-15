---
revision_pending: false
title: "Module 9.2: MLflow"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.2-mlflow
sidebar:
  order: 3
---

> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes
>
> **Prerequisites**: Python basics, fundamental ML concepts (training, validation, inference), Kubernetes fundamentals (Pods, Deployments, Services, Secrets), and the [MLOps Discipline](/platform/disciplines/data-ai/mlops/) module recommended for lifecycle context.

## What You'll Be Able To Do

After completing this module, you will be able to:

- **Deploy** MLflow on Kubernetes with a PostgreSQL backend store, object-storage artifact backend, and proxied artifact access suitable for a shared team tracking server.
- **Implement** experiment tracking with runs, parameters, metrics, artifacts, and autolog discipline so training attempts remain reproducible and comparable across teammates and time.
- **Operate** the model registry using versions, tags, and aliases to promote approved models through a governed lifecycle without hard-coding version numbers in serving code.
- **Package and serve** MLflow Models locally and on Kubernetes, then connect registry-backed models to KServe or Seldon when production inference needs platform-grade rollout and scaling.
- **Choose** when MLflow Projects cover reproducible run packaging versus when a workflow orchestrator such as Kubeflow Pipelines or Airflow should own scheduling and dependencies.

## Why This Module Matters

**Hypothetical scenario:** A fraud-detection team trains twelve model variants in one sprint. Offline accuracy improves from 91% to 96%, and stakeholders ask for production deployment by Friday. The data scientist who achieved the best score is on vacation. Nobody can reconstruct which dataset snapshot, feature pipeline, hyperparameters, or random seed produced the winning run because most work happened in notebooks with overwritten variables and informal filenames. The platform team spends four days re-running experiments, delays a release, and ships a model that scores well in staging but behaves differently on live traffic because preprocessing drifted during the scramble.

That failure is not mysterious. It is what happens when experiment metadata is treated as optional overhead instead of production infrastructure. Machine learning systems fail in two places at once: the model may be wrong, and the organization may be unable to say how the model was built. The second failure is often more expensive because it destroys trust, blocks audits, and turns every promotion into guesswork.

MLflow addresses the metadata half of MLOps without pretending to be a full ML platform. It gives teams a durable record of what changed between training attempts, which artifacts belong to each attempt, and which approved model version should receive production traffic. Kubeflow, Airflow, and Kubernetes schedulers answer when and where work runs. MLflow answers what was tried, what resulted, and which trained artifact is allowed to serve. This module teaches that separation using MLflow as the running example. The concepts transfer to peer tools in the landscape table later, but the worked patterns here are expressed in MLflow APIs and deployment shapes you can run on a lab cluster today.

Platform engineers sometimes resist experiment tracking because it feels like "extra logging." The better framing is risk reduction. When a regulator, customer, or on-call engineer asks why a model behaved differently on Tuesday than on Monday, the answer must be a traceable chain: data snapshot, code revision, parameters, metrics, approval record, and serving pointer. Without that chain, incident response becomes archaeology. With it, you can roll forward confidently because promotion is a pointer move rather than a blind swap.

Data scientists benefit for a simpler reason: speed. When you can filter a thousand runs in seconds, you stop re-training models you already trained. When aliases replace hard-coded version numbers, you stop opening pull requests across six services just to promote a model. The tooling does not replace scientific judgment, but it removes the mechanical friction that makes judgment hard to apply under deadline pressure.

## The Durable Capability: Managing the ML Experiment and Model Lifecycle

Before touching installation commands, name the durable spine this toolkit module is really about. Experiment tracking captures the searchable history of training attempts: parameters, metrics, code references, and artifacts for every run. Model registry governance turns promising runs into named, versioned products with promotion rules your team agrees on. Packaging expresses a trained artifact in a portable format with explicit dependencies and inference entrypoints. Serving exposes that package through a stable URI so applications and platform controllers can load the same object in development and production.

Those capabilities are older than any single vendor interface. Teams felt the pain without them long before Kubernetes existed: spreadsheets of learning rates, emailed pickle files, and production services pinned to filenames like `model_final_v3_REAL.pkl`. MLflow is one open-source implementation of the spine. Weights & Biases, Comet, Neptune, DVC, and managed cloud ML services implement overlapping pieces with different tradeoffs in hosting, collaboration, and Kubernetes integration. The curriculum uses MLflow here because its APIs are explicit, its self-hosted tracking server maps cleanly to Kubernetes primitives, and its model URI scheme shows up frequently in KServe and Seldon examples. That is an illustrative choice, not a ranking.

Teaching the spine first also protects you from tutorial churn. Vendor screenshots and menu names change quarterly, but the questions remain stable. Where do runs live? How do binaries survive pod restarts? How do you promote without editing version integers in six repositories? How does serving resolve the approved artifact? When you can answer those questions, reading release notes becomes a targeted update rather than a full retraining of your mental model.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> | Item | Current snapshot |
> |------|------------------|
> | MLflow OSS release line | `v3.13.0` on [GitHub releases](https://github.com/mlflow/mlflow/releases) |
> | Model Registry stages | Deprecated since MLflow 2.9.0; aliases and tags are the supported promotion model ([workflow docs](https://mlflow.org/docs/latest/ml/model-registry/workflow/)) |
> | Governance home | Open-source project under the `mlflow` GitHub organization; originated at Databricks and remains widely integrated with managed ML platforms |
> | Typical self-hosted tracking stack | SQLAlchemy-backed metadata store (PostgreSQL common) plus object storage (S3-compatible) and optional artifact proxying via the tracking server |
> | MLflow 3 tracking additions | Logged-model search APIs and model-id URIs complement classic run-centric logging ([tracking docs](https://mlflow.org/docs/latest/tracking.html)) |

| Capability | MLflow | Weights & Biases | Comet | Neptune | DVC | SageMaker / Vertex |
|------------|--------|------------------|-------|---------|-----|-------------------|
| Experiment tracking | Native runs, metrics, params, artifacts | Native runs with rich UI collaboration | Experiments with panels and collaboration | Run-centric metadata and comparison views | Git-native experiment commits and metrics files | Managed experiment services with cloud IAM integration |
| Model registry | Registered models, versions, aliases, tags | Registry with deployment hooks in managed offerings | Model registry features in enterprise tiers | Model registry and stage-like workflows in product docs | Versioned models via Git tags and `dvc.yaml` pipelines | Cloud model registry with endpoint aliases and deployment integration |
| Packaging / serving | MLflow Model format, flavors, `mlflow models serve`, containers | Artifacts plus deployment integrations | Model production monitoring adjacent to experiments | Export and deployment helpers | Pipeline artifacts; serving usually external | Built-in endpoints and managed inference options |
| Self-hostable OSS core | Yes (tracking server + registry with DB backend) | Primarily SaaS; enterprise hosting options vary | Primarily SaaS | SaaS with self-hosted options per vendor docs | Yes (Git remote + optional DVC remotes) | Managed cloud services |
| OSS license posture | Apache-2.0 (`mlflow` repository) | Commercial SaaS with client libraries | Commercial SaaS with client libraries | Commercial SaaS | Apache-2.0 | Proprietary managed platforms |

Read the Rosetta row by row. If your organization already standardized on Git-based reproducibility, DVC may cover experiment lineage while MLflow covers registry and serving URIs. If your organization wants a managed control plane with minimal cluster operations, SageMaker or Vertex experiment tracking may be enough without self-hosting MLflow. The point is to match capabilities to constraints, not to chase a single tool name.

The architecture diagram below is intentionally boring. Boring is good here because MLflow's power comes from stable contracts, not from flashy components. Clients speak HTTP to a tracking server. The server writes small metadata to a database and large binaries to object storage. Training code anywhere—laptop, CI runner, Kubernetes Job, or pipeline step—uses the same API surface.

```ascii
MLFLOW TRACKING AND REGISTRY DATA PLANE
====================================================================

 Training clients                Tracking Server                 Durable stores
 ┌─────────────────┐            ┌──────────────────┐            ┌─────────────────┐
 │ notebook / job  │  HTTP API  │  REST + UI       │  SQL       │  PostgreSQL     │
 │ pipeline step   │ ─────────▶ │  artifact proxy  │ ────────▶  │  (metadata)     │
 └─────────────────┘            │  registry APIs   │  S3 API    └─────────────────┘
                                └────────┬─────────┘ ────────▶  ┌─────────────────┐
                                         │                      │  Object storage │
                                         │                      │  (artifacts)    │
                                         ▼                      └─────────────────┘
                                Serving runtimes load
                                models:/name@alias URIs
```

When you evaluate peers, ask the same structural questions: where metadata lives, where artifacts live, how promotion pointers work, and how serving systems resolve a deployment URI. Vendors change feature names frequently, but those questions remain stable across years.

## Experiment Tracking: Runs, Parameters, Metrics, and Artifacts

Experiment tracking is the discipline of logging everything that varies between training attempts so comparisons are fair and reproduction is possible. In MLflow, the atomic unit is the **run**: one execution of training or evaluation code with a start time, end time, user, source context, parameters, metrics, tags, and artifacts. Runs are grouped into **experiments**, which act as namespaces for related work such as `fraud-detection-v2` or `recommendation-reranker`.

Parameters are the knobs you deliberately change: learning rate, tree depth, embedding dimension, data snapshot identifier, or feature flag names. Metrics are the measurements you use to judge quality: accuracy, AUC, RMSE, latency on a validation set, or business proxies such as predicted fraud dollars in a holdout window. Artifacts are the files produced along the way: model weights, evaluation plots, confusion matrices, SHAP summaries, or a serialized preprocessing pipeline. If a value influenced training or evaluation and you might need it later, it belongs in the run record.

The manual tracking pattern wraps training code in a run context and logs each category explicitly. This is the teaching baseline because it makes the contract visible: nothing is recorded unless your code or an autolog hook records it.

```python
# train.py — explicit tracking pattern
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

mlflow.set_tracking_uri("http://mlflow-server.mlflow.svc:5000")
mlflow.set_experiment("iris-classification")

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

with mlflow.start_run(run_name="rf-baseline"):
    n_estimators = 100
    max_depth = 10
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    mlflow.log_param("random_state", 42)

    model = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth, random_state=42
    )
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    mlflow.log_metric("accuracy", accuracy)

    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        input_example=X_test[:3],
        registered_model_name="iris-classifier",
    )
    print(f"Run ID: {mlflow.active_run().info.run_id}")
```

The explicit pattern teaches three habits that survive every framework change. First, set the tracking URI and experiment before training so runs do not silently land in a local `./mlruns` directory on a laptop. Second, log parameters before training and metrics after evaluation so partial runs still reveal intent even when jobs fail midway. Third, log models with signatures or input examples when serving is a downstream goal, because inference servers need predictable input schemas.

Autologging is the second pattern. After `mlflow.autolog()` or a flavor-specific autolog call, supported libraries emit parameters, metrics, and models without hand-written log statements for every field. Autolog is not magic privacy: it logs what the integration knows about, and it does not replace your responsibility to log dataset versions, business metrics, or custom preprocessing artifacts that live outside the framework hook.

```python
import mlflow

mlflow.autolog()
# or: mlflow.sklearn.autolog()

from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
```

Use autolog to reduce boilerplate once the team understands what is being captured. Keep explicit logging for domain-specific metadata autolog cannot infer, such as the identifier of an approved feature view, the hash of a training query, or compliance tags that gate promotion. Many production teams combine both: autolog for standard framework telemetry, explicit `log_param` and `log_artifact` calls for the business and data-contract context that autolog does not see.

Comparison is where tracking pays rent. `mlflow.search_runs` and the `MlflowClient.search_runs` API accept filter strings such as `metrics.accuracy > 0.95 and params.max_depth < 12`, which turns a pile of attempts into an ordered shortlist. MLflow 3 extends comparison with `search_logged_models` for checkpoint-centric workflows, but the durable lesson is unchanged: if you cannot query your history, you will recreate spreadsheets with extra steps.

Design experiments for searchability from day one. Consistent parameter names across scripts matter more than clever abbreviations. If one run logs `lr` and another logs `learning_rate`, your filter strings become brittle. Likewise, keep metric names stable across refactors so longitudinal charts remain meaningful when code moves between repositories.

Custom artifacts matter when metrics alone lie. A model can score well while misclassifying an important slice. Logging a confusion matrix image, calibration plot, or error analysis JSON gives reviewers evidence beyond a single scalar. Use `mlflow.log_artifact` for individual files and `mlflow.log_artifacts` for directories such as `plots/` or `reports/`.

```python
import json
import matplotlib.pyplot as plt
import mlflow

with mlflow.start_run():
    # ... train ...
    plt.figure()
    # build confusion matrix plot
    plt.savefig("confusion_matrix.png", bbox_inches="tight")
    mlflow.log_artifact("confusion_matrix.png", artifact_path="evaluation")

    metadata = {
        "data_snapshot": "features-2026-06-01",
        "label_policy": "chargeback-within-30d",
        "reviewer": "model-risk",
    }
    with open("metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle)
    mlflow.log_artifact("metadata.json", artifact_path="governance")
```

Tracking also needs operational boundaries. Logging metrics inside tight training loops can explode metadata and slow runs. Prefer epoch-level or phase-level metrics unless step-level curves are genuinely required. Use run names and tags such as `git_commit`, `pipeline_id`, or `dataset_hash` so automated searches can connect MLflow runs to CI builds and data contracts. Treat the tracking server as shared infrastructure with authentication, backup, and retention policies rather than as a personal notebook accessory.

Reproducibility is the hidden outcome of good tracking. Reproducibility does not mean "the same random seed always works on different hardware." It means your team can identify the inputs required to approximate a historical result and explain known sources of drift such as library upgrades, data changes, or hardware differences. That is why artifact logging matters alongside metrics. A metric tells you how good the model was; artifacts tell you what the model was.

Teams new to tracking often log only accuracy or loss. That is enough for leaderboard comparisons during research, but production reviewers ask different questions. They ask whether evaluation used the same label definition as last month, whether the validation slice excluded leaked users, and whether preprocessing matched training. Those answers live in parameters, tags, and artifacts more often than in a single scalar metric. Build the habit early: when you change something material, log it explicitly even if autolog covers the model hyperparameters.

MLflow 3's logged-model search features are useful when training emits many checkpoints per run, which is common in deep learning. The durable pattern nonetheless remains run-centric for most classical ML teams: one run per training attempt, one registered version per approved artifact, aliases for deployment pointers. Adopt checkpoint search when your framework training loop actually produces meaningful intermediate models worth comparing.

## Model Registry: Versions, Tags, and Aliases

Tracking answers which runs happened. The registry answers which trained artifacts are approved for downstream use. A **registered model** is a named product such as `iris-classifier` or `fraud-scorer-champion-candidate`. Each time you register a new artifact, MLflow creates a **model version** with monotonically increasing integers and links back to the originating run or logged model for lineage.

Historically, MLflow exposed **stages** such as Staging, Production, and Archived. That model was easy to teach but awkward in real deployments: only one version could occupy a stage, promotions were coarse, and serving code often hard-coded stage names. Starting in MLflow 2.9.0, stages are **deprecated** in favor of **aliases** and richer **tags** ([deprecation RFC](https://github.com/mlflow/mlflow/issues/10336), [migration guide](https://mlflow.org/docs/latest/model-registry.html#migrating-from-stages)). Aliases are mutable named pointers such as `champion`, `challenger`, or `shadow-eu`, and a single version may carry multiple aliases and tags simultaneously.

Teach aliases as the durable promotion mechanism. Application and serving code should load `models:/iris-classifier@champion` instead of `models:/iris-classifier/3`. When validation completes, operators move the alias with one API call or UI action. Consumers pick up the new artifact on their next load without rewriting version numbers across repositories.

```python
from mlflow import MlflowClient

client = MlflowClient()

# Register during training (preferred) via log_model(..., registered_model_name=...)
# Or register an existing run artifact:
run_id = "abc123def456"
model_uri = f"runs:/{run_id}/model"
client.create_registered_model("iris-classifier")
client.create_model_version(name="iris-classifier", source=model_uri, run_id=run_id)

client.set_registered_model_alias("iris-classifier", "champion", version=1)
client.set_model_version_tag(
    "iris-classifier", 1, "validation_status", "approved"
)

model = mlflow.pyfunc.load_model("models:/iris-classifier@champion")
```

Tags express governance metadata that aliases alone cannot capture: `validation_status:approved`, `risk_tier:high`, `data_contract:2026-06-01`, or `owner_team:fraud`. Descriptions and Markdown annotations on registered models and versions give human reviewers a place to record methodology, known limitations, and approval notes. Promotion workflows therefore become a combination of automated tests, human review, alias movement, and tag checks rather than a rigid stage state machine.

```ascii
ALIAS-CENTRIC REGISTRY WORKFLOW
====================================================================

Run 101 ──register──▶ iris-classifier v1 ──alias──▶ champion
Run 118 ──register──▶ iris-classifier v2 ──alias──▶ challenger
Run 124 ──register──▶ iris-classifier v3 (tags: validation_status=pending)

Serving code always loads models:/iris-classifier@champion
After offline + shadow tests pass:
  set_registered_model_alias("iris-classifier", "champion", version=2)
  delete_registered_model_alias("iris-classifier", "challenger")  # optional cleanup
```

If you inherit pipelines that still call `transition_model_version_stage`, treat them as legacy debt. New work should set aliases and tags, and CI should fail if production manifests reference deprecated stage URIs. Managed platforms may wrap MLflow APIs with their own governance layers, but the portable pattern remains: separate immutable version numbers from mutable deployment pointers.

Human approval workflows benefit from tags because tags carry meaning stages tried to encode with a single word. A version might be technically excellent yet blocked by a `legal_review:pending` tag. Another might be approved for offline replay but not online serving until `shadow_test:passed` appears. Aliases should move only after automated checks and human gates agree. This is slower than dragging a model to a Production column in a UI, but it is also more honest about the checks your organization actually runs.

Registry design also needs naming discipline. Model names should be products, not experiments. `fraud-linear-champion-june-test` is a run name or tag story, not a registry name. Prefer stable product identifiers such as `fraud-scorer` or `recommendation-ranker` with versions underneath. Serving systems, dashboards, and on-call runbooks become easier when registry names match how the business discusses models.

## Packaging and Serving: MLflow Models, Flavors, and Runtime Boundaries

An MLflow **Model** is a directory with a standard layout: a `MLmodel` metadata file, optional `conda.yaml` or `python_env.yaml`, serialized weights, and a flavor-specific representation. **Flavors** are adapters for frameworks such as scikit-learn, PyTorch, TensorFlow, XGBoost, and the generic `python_function` (`pyfunc`) flavor that many serving paths understand. The durable lesson is that packaging captures both the artifact and how to load it, which is why `mlflow models serve` and many Kubernetes integrations can start a server from a URI instead of from a bespoke Dockerfile every time.

Packaging also forces teams to confront environment drift early. A model that loads in a notebook with implicit global packages may fail in a container with a minimal environment unless dependencies are recorded. MLflow environment files are not perfect substitutes for disciplined container images, but they provide a baseline that serving teams can extend rather than guessing from memory.

When multiple flavors are logged together, understand which flavor your serving path will load. Many platforms default to `pyfunc` because it offers a uniform inference surface even when training used a framework-specific object. Document that choice in registry descriptions so future maintainers do not accidentally switch flavors during a refactor.

```bash
# Local smoke test from registry alias
mlflow models serve \
  --model-uri "models:/iris-classifier@champion" \
  --host 127.0.0.1 \
  --port 5001 \
  --env-manager local

curl -s -X POST http://127.0.0.1:5001/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
```

Local serving is for developer verification, not for production traffic on its own. Production needs health checks, autoscaling, authentication, rate limits, and rollout policies. MLflow can build a container image from a model URI with `mlflow models build-docker`, which is useful when you want a minimal serving image without writing a custom server file. Platform teams often combine registry URIs with KServe or Seldon so inference inherits Kubernetes-native rollout, metrics, and protocol standards from [Module 9.8](../module-9.8-kserve/) and [Module 9.9](../module-9.9-seldon-core/).

```yaml
# mlflow-model-server.yaml — illustrative Deployment serving @champion
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iris-model-server
  namespace: ml-serving
spec:
  replicas: 2
  selector:
    matchLabels:
      app: iris-model
  template:
    metadata:
      labels:
        app: iris-model
    spec:
      containers:
        - name: model-server
          image: ghcr.io/mlflow/mlflow:v3.13.0
          command:
            - mlflow
            - models
            - serve
            - --model-uri=models:/iris-classifier@champion
            - --host=0.0.0.0
            - --port=5001
            - --no-conda
          ports:
            - containerPort: 5001
          env:
            - name: MLFLOW_TRACKING_URI
              value: "http://mlflow-server.mlflow.svc:5000"
          readinessProbe:
            httpGet:
              path: /health
              port: 5001
---
apiVersion: v1
kind: Service
metadata:
  name: iris-model-server
  namespace: ml-serving
spec:
  selector:
    app: iris-model
  ports:
    - port: 80
      targetPort: 5001
```

Know where MLflow serving stops. It exposes a REST inference endpoint for a loaded model artifact. It does not replace a full inference platform when you need canary rollouts across many models, GPU fractioning, request logging pipelines, or standardized V2 inference protocols. That boundary is healthy. Use MLflow to package and address models. Use KServe or Seldon when serving becomes a multi-team platform concern with CRDs, autoscaling, and traffic management.

Container builds deserve explicit mention because packaging is where science meets supply chain. `mlflow models build-docker` can produce an image from a registry URI, which is convenient for GitOps pipelines that promote immutable image digests alongside alias changes. Whether you build from MLflow directly or wrap a model server in your own Dockerfile, keep the registry URI or artifact hash in deployment metadata so incident response can connect running pods to training lineage.

Inference contracts matter as much as training accuracy. The `pyfunc` flavor loads many model types through one interface, but clients still need consistent JSON shapes or tensor formats. Use `infer_signature` when feasible so MLflow records input and output schema. When teams skip signatures, serving issues show up only under production traffic patterns where nulls, missing columns, or string-encoded numbers appear more often than in curated validation sets.

## Projects and Pipelines: Where MLflow Stops and Orchestrators Begin

MLflow **Projects** package code, entry points, and dependencies so a run can be reproduced with `mlflow run` or submitted to a remote target. A `MLproject` file names the environment, entry points, and parameters. This is valuable when you want a lightweight, Git-centric reproducibility layer for training scripts without adopting a full workflow engine.

```yaml
# MLproject (minimal illustration)
name: iris-training
conda_env: conda.yaml
entry_points:
  main:
    parameters:
      n_estimators: {type: int, default: 100}
      max_depth: {type: int, default: 10}
    command: "python train.py --n-estimators {n_estimators} --max-depth {max_depth}"
```

Projects answer how to invoke a training job consistently. They do not answer how to schedule nightly retraining, wait for upstream data partitions, retry failed Spark stages, or coordinate feature engineering and evaluation in a DAG. That is orchestrator territory. Kubeflow Pipelines, Airflow, Argo Workflows, and similar systems own dependencies, retries, parallelism, and infrastructure glue. MLflow should appear inside those steps as the metadata and registry layer, not as a replacement for them.

```python
# pipeline_with_mlflow.py — Kubeflow Pipelines component sketch
from kfp import dsl

@dsl.component(
    base_image="python:3.12",
    packages_to_install=["mlflow", "scikit-learn", "boto3"],
)
def train_with_mlflow(mlflow_uri: str, experiment_name: str, n_estimators: int) -> str:
    import mlflow
    import mlflow.sklearn
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(experiment_name)
    X_train, X_test, y_train, y_test = train_test_split(
        load_iris().data, load_iris().target, test_size=0.2, random_state=42
    )
    with mlflow.start_run() as run:
        mlflow.log_param("n_estimators", n_estimators)
        model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
        model.fit(X_train, y_train)
        mlflow.log_metric("accuracy", model.score(X_test, y_test))
        mlflow.sklearn.log_model(
            model, "model", registered_model_name="iris-classifier"
        )
        return run.info.run_id

@dsl.pipeline(name="mlflow-training-pipeline")
def training_pipeline(
    mlflow_uri: str = "http://mlflow-server.mlflow.svc:5000",
    experiment_name: str = "kubeflow-experiments",
    n_estimators: int = 100,
):
    train_with_mlflow(
        mlflow_uri=mlflow_uri,
        experiment_name=experiment_name,
        n_estimators=n_estimators,
    )
```

The integration pattern is straightforward: orchestrator launches containers, MLflow records what happened inside them, registry captures promoted artifacts, and serving platforms load aliases. Avoid duplicating orchestration logic inside training scripts and avoid expecting MLflow to schedule dependencies it does not know about.

Airflow teams often call MLflow from a `PythonOperator` or container task after feature tables land. Kubeflow teams wrap training in a pipeline component as shown earlier. Argo users do the same with script templates. In each case, pass the tracking URI and experiment name as explicit parameters rather than hard-coding them inside library code. Central configuration makes environment promotion safer when dev, staging, and production tracking servers differ.

A practical rule of thumb helps scope conversations with stakeholders. If the question is "what happened during training," MLflow is the right conversation. If the question is "what runs at 2 a.m. after the warehouse refresh finishes," an orchestrator is the right conversation. Mixing the two roles creates either a fragile scheduler written in training scripts or a metadata vacuum inside otherwise beautiful DAGs.

## MLflow on Kubernetes: Tracking Server as Stateful Infrastructure

Self-hosting MLflow on Kubernetes is less about YAML cleverness and more about respecting state. The tracking server splits responsibilities between a **backend store** for metadata and an **artifact store** for large files. SQLite and local disk are acceptable for solo labs. Shared team environments should use PostgreSQL or another SQLAlchemy-supported database plus S3-compatible object storage.

The tracking server is stateful infrastructure even when the Deployment itself is stateless. Back up the database, protect object storage buckets, rotate credentials, and front the service with TLS and authentication. MLflow’s `--serve-artifacts` mode proxies artifact uploads and downloads through the server so clients do not need direct object-store credentials on laptops, which simplifies corporate network policies.

```yaml
# mlflow-deployment.yaml — team tracking server pattern
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
  namespace: mlflow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mlflow
  template:
    metadata:
      labels:
        app: mlflow
    spec:
      containers:
        - name: mlflow
          image: ghcr.io/mlflow/mlflow:v3.13.0
          command:
            - mlflow
            - server
            - --host=0.0.0.0
            - --port=5000
            - --backend-store-uri=postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres:5432/mlflow
            - --default-artifact-root=s3://mlflow-artifacts/
            - --serve-artifacts
          ports:
            - containerPort: 5000
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: mlflow-secrets
                  key: postgres-user
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mlflow-secrets
                  key: postgres-password
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: mlflow-secrets
                  key: aws-access-key
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: mlflow-secrets
                  key: aws-secret-key
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-server
  namespace: mlflow
spec:
  selector:
    app: mlflow
  ports:
    - port: 5000
      targetPort: 5000
```

PostgreSQL is commonly deployed as a StatefulSet with persistent volumes for the metadata database. Object storage may be cloud S3, MinIO inside the cluster, or another S3-compatible provider. Keep the artifact bucket lifecycle separate from ephemeral pod storage so rescheduled MLflow pods do not lose model binaries.

```yaml
# postgres.yaml — metadata backend (lab-sized)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: mlflow
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: mlflow
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: mlflow-secrets
                  key: postgres-user
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mlflow-secrets
                  key: postgres-password
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 20Gi
```

Expose the tracking UI through Ingress only after authentication is wired. Basic auth annotations are acceptable in labs; production should integrate SSO or reverse-proxy auth aligned with your platform standards. NetworkPolicies should limit which namespaces may reach the tracking API and artifact proxy paths. Monitor database growth, artifact bucket size, and API latency together because registry adoption increases metadata write volume faster than teams expect.

High availability for the tracking Deployment is straightforward horizontally, but the database and bucket are the real availability story. Run PostgreSQL with backups and tested restore drills. Version object storage lifecycle rules carefully so automation does not delete artifacts still referenced by registered models. If you enable artifact proxying, watch egress and ingress through the tracking pods because large model artifacts can dominate bandwidth during promotion events.

```yaml
# mlflow-ingress.yaml — lab ingress with TLS hook points
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mlflow-ingress
  namespace: mlflow
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - mlflow.example.com
      secretName: mlflow-tls
  rules:
    - host: mlflow.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: mlflow-server
                port:
                  number: 5000
```

Debugging self-hosted MLflow on Kubernetes usually follows a short checklist. If runs never appear, verify client `MLFLOW_TRACKING_URI`, DNS resolution to the Service, and network policies from client namespaces. If runs appear but artifacts fail, verify object-store credentials, bucket policy, and whether `--serve-artifacts` is enabled consistently with client expectations. If the UI is slow, inspect database size and runaway per-step metric logging before scaling tracking pods that do not fix metadata bloat.

## Debugging Tracking and Registry Failures

Operational fluency separates teams that "installed MLflow" from teams that depend on it daily. Permission errors often show up as partial success: parameters log while artifact uploads fail, leaving runs that look complete in the UI until someone opens the model folder. Fix credentials, bucket paths, and proxy settings together rather than toggling one field at random.

Registry issues frequently trace to URI confusion. `runs:/<id>/model` references a run artifact path. `models:/name/version` references an immutable registry version. `models:/name@alias` references the mutable deployment pointer you want in serving code. Mixing those forms in CI is a common source of "works in notebook, fails in cluster" bugs because notebooks sometimes load local run paths while Kubernetes loads registry aliases.

Another class of failures is semantic drift. Training logs `accuracy` on a slice while production monitoring tracks business precision on live traffic. The registry shows a promoted model, but arguments erupt because teams used the same metric name for different definitions. Solve that with explicit metric names (`val_accuracy_holdout_june`) and tags that document evaluation slices. Tracking tools record what you tell them; they do not enforce statistical hygiene by themselves.

When runs look successful yet reviewers reject promotion, inspect tags and artifacts before retraining. Missing evaluation plots, absent calibration checks, or unclear dataset identifiers are process failures that no amount of hyperparameter tuning fixes. The registry is a governance layer; it amplifies the quality of evidence you attach to each version.

Long-running distributed jobs add another failure mode: partial runs. If a worker crashes after logging parameters but before metrics finalize, you may inherit ambiguous run records. Use run status tags, nested runs, or orchestrator-level retry identifiers so incomplete attempts are searchable and separable from completed candidates. The goal is to prevent a half-finished run from being mistaken for a champion candidate during a rushed release window.

## Security, Tenancy, and Governance on Shared Servers

Shared tracking servers need identity. Authentication can live at the ingress layer, beside the MLflow process, or in a managed offering outside this module's scope. Authorization is equally important: who may create experiments, who may delete runs, and who may move aliases on regulated models. Open-source MLflow assumes you will integrate platform controls rather than delivering a full enterprise RBAC story out of the box.

Namespace isolation on Kubernetes complements MLflow's experiment namespaces. Platform teams often map data science teams to Kubernetes namespaces for compute while mapping the same teams to MLflow experiments or registered model prefixes for metadata. The two namespaces are not identical concepts, but aligning naming reduces cognitive load during incidents.

Secrets belong in Kubernetes Secrets or external secret managers, never in training repositories. Rotate database and object-store credentials on a schedule. Audit alias changes with the same seriousness as production deploy events because changing `champion` is a deploy in the logical sense even when no container image changes.

Retention policies deserve explicit thought because experiment metadata accumulates quietly. Teams rarely delete runs until storage costs spike or legal asks for minimization. Define retention windows per experiment class: exploratory notebooks may expire quickly, while regulated model lines may require years of immutable history. Object storage lifecycle rules should align with registry references so automation does not orphan approved models.

Finally, separate read access from promote access. Scientists may need broad read access to compare runs while only automation service accounts or release managers may move `champion`. That separation reduces accidental promotion during demo sessions, which is more common than platform teams like to admit.

## Worked Example: Log, Register, Alias, and Serve

The following end-to-end path ties the module together without implying that every organization should run every step the same way. Train a model while logging parameters and metrics, register the resulting artifact, assign a `champion` alias after review, smoke-test serving locally or in a Kubernetes Deployment, and only then integrate with KServe or Seldon if you need advanced rollout features.

```python
# end_to_end.py
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

TRACKING_URI = "http://127.0.0.1:5000"
EXPERIMENT = "module-9-2-demo"
MODEL_NAME = "iris-classifier"

mlflow.set_tracking_uri(TRACKING_URI)
mlflow.set_experiment(EXPERIMENT)
client = MlflowClient()

X_train, X_test, y_train, y_test = train_test_split(
    load_iris().data, load_iris().target, test_size=0.2, random_state=42
)

with mlflow.start_run(run_name="rf-100-10") as run:
    params = {"n_estimators": 100, "max_depth": 10, "random_state": 42}
    mlflow.log_params(params)
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    mlflow.log_metric("accuracy", model.score(X_test, y_test))
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name=MODEL_NAME,
        input_example=X_test[:3],
    )
    run_id = run.info.run_id

versions = client.search_model_versions(f"name='{MODEL_NAME}'")
latest = max(int(v.version) for v in versions)
client.set_registered_model_alias(MODEL_NAME, "champion", latest)
client.set_model_version_tag(MODEL_NAME, latest, "validation_status", "approved")

loaded = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
print(loaded.predict(X_test[:2]))
print(f"Promoted run {run_id} as version {latest} @champion")
```

For platform serving, point KServe or Seldon at the same alias URI or sync the artifact into their storage expectations. Seldon documents MLflow model server integration paths in its navigation guides. KServe's ecosystem frequently treats MLflow as one model-source option among many storage backends. The registry alias remains the stable contract even when the serving controller changes.

When you wire KServe or Seldon, read their storage integration docs for the exact URI or secret pattern they expect. Some deployments pull directly from MLflow tracking APIs. Others expect object-store paths populated from registry artifacts. The alias URI still anchors human and automation workflows even if the serving controller copies weights into its own bucket during rollout.

Promotion automation often follows a repeatable script: train, evaluate gates, register version, run integration tests against `challenger`, shift alias, monitor business metrics, and roll back by resetting the alias if error budgets burn. GitOps repositories store the desired alias target or serving manifest hash while MLflow stores lineage. Neither layer should silently override the other without a visible audit event.

Document the rollback path before you need it. If `champion` moves to a bad version, reversing the alias should be a one-line API change plus a serving reload, not a frantic retraining session. Teams that practice alias rollback in staging quarterly discover missing permissions and broken runbooks early, which is far cheaper than discovering them during a revenue-impacting incident.

## Patterns & Anti-Patterns

Patterns are repeatable designs that keep experiment and registry data trustworthy as teams scale. Anti-patterns are shortcuts that create silent metadata loss or production drift. Read both tables as engineering checklists during design reviews rather than as slogans to memorize for a quiz.

Good patterns often look like extra work until the first serious incident. Logging dataset hashes feels redundant until someone retrains on the wrong snapshot. Splitting metadata and artifact stores feels heavy until the first time a pod restart would have lost binaries on emptyDir. Alias pointers feel abstract until a Friday promotion requires zero application redeploys. The tables below name those designs explicitly so teams can adopt them before pain arrives.

| Pattern | When to Use It | Why It Works |
|---------|----------------|--------------|
| Log everything that varies | Every training or retraining job | Comparisons and audits require identical metadata fields across runs |
| Alias-based production pointers | Any service loading `models:/name@champion` | Promotion becomes pointer movement instead of code edits across repos |
| Split metadata DB and artifact store | Shared tracking servers | PostgreSQL scales metadata queries; object storage scales model binaries |
| Proxied artifacts via tracking server | Laptops without direct S3 credentials | Clients talk only to MLflow while credentials stay in the cluster |
| Orchestrator owns schedule, MLflow owns lineage | Kubeflow Pipelines or Airflow DAGs | Each tool stays in its durable capability lane |
| Signatures or input examples on log_model | Any model bound for serving | Inference servers fail early on schema mismatch instead of silently mis-scoring |

| Anti-Pattern | Why Teams Do It | Better Approach |
|--------------|-----------------|-----------------|
| Notebook-only experimentation | Fast interactive work | Wrap notebook cells in `mlflow.start_run()` or export to scripts with tracking |
| Hard-coded model version in serving repos | Version numbers feel explicit | Load `@champion` and move aliases after validation |
| Using deprecated stages for new pipelines | Old tutorials and copy-paste | Migrate to aliases and tags per MLflow 2.9+ guidance |
| Logging per-step metrics for millions of steps | Fear of missing detail | Log epoch-level curves; use framework callbacks thoughtfully |
| SQLite backend for multi-user teams | Simple default | Move to PostgreSQL before sharing the tracking server |
| Treating MLflow as workflow orchestrator | One tool feels simpler | Keep DAG scheduling in Kubeflow, Airflow, or Argo |
| Skipping artifact store backups | Storage is "just files" | Backup object storage and database with the same urgency as production DBs |

## Decision Framework

Choosing tooling is an exercise in matching durable capabilities to organizational constraints. MLflow fits when you want self-hosted experiment tracking and a registry with portable model URIs. Weights & Biases, Comet, and Neptune fit when managed collaboration and SaaS operations are acceptable tradeoffs for less cluster ownership. DVC fits when Git-native experiment lineage already anchors your workflow. SageMaker and Vertex fit when cloud IAM, managed endpoints, and billing integration matter more than running your own tracking Deployment.

No row in the decision table is a forever answer. A team may begin with managed Vertex autologging during early experimentation, adopt self-hosted MLflow when registry URIs must stay inside a VPC, and later add KServe when inference standardization becomes the bottleneck. The curriculum emphasizes capability transfer: if you understand aliases, artifact stores, and alias-based serving URIs in MLflow, you can read analogous concepts in other vendors without starting from zero.

Cost conversations belong here even though prices change monthly. Self-hosted MLflow shifts spend to databases, object storage, ingress, and engineer time operating stateful services. SaaS trackers shift spend to per-seat or per-run billing while reducing operational load. Cloud ML control planes bundle costs into managed endpoints and experiment storage with IAM integration. The durable question is which costs your organization can operate well, not which invoice looks smallest on day one.

| Question | Lean toward MLflow self-hosted | Lean toward managed experiment SaaS | Lean toward DVC-first | Lean toward cloud ML control plane |
|----------|-------------------------------|-------------------------------------|----------------------|-----------------------------------|
| Must data stay in your VPC? | Strong fit | Depends on vendor hosting options | Strong fit (Git remotes) | Use private endpoints and policies |
| Need Kubernetes-served tracking UI? | Strong fit | Usually external SaaS UI | Tracking is secondary | Optional; cloud UI instead |
| Team already lives in Git PR workflows? | Integrate via CI steps | Integrate via API | Strong fit | Use cloud SDK pipelines |
| Need enterprise RBAC on models? | Combine OSS with platform auth | Vendor enterprise features | Limited native registry | Cloud IAM and registry |
| Primary pain is serving scale-out? | Add KServe/Seldon layer | Add vendor deployment hooks | External serving required | Managed endpoints |

```mermaid
flowchart TD
    A[Start: what problem hurts most?] --> B{Need shared experiment history and registry in your cluster?}
    B -- yes --> C{Also need DAG scheduling and data dependencies?}
    C -- yes --> D[Orchestrator + MLflow inside steps]
    C -- no --> E[MLflow tracking server + registry]
    B -- no --> F{Git-native reproducibility is the center?}
    F -- yes --> G[DVC experiments + optional registry integration]
    F -- no --> H{Prefer managed cloud ML operations?}
    H -- yes --> I[SageMaker or Vertex experiment services]
    H -- no --> J[Evaluate SaaS experiment trackers against compliance needs]
    E --> K{Production inference at platform scale?}
    K -- yes --> L[Add KServe or Seldon loading @alias URIs]
    K -- no --> M[mlflow models serve or small Deployment]
```

When you facilitate a tooling workshop, ask participants to write the dominant pain on a sticky note before debating vendors. If the sticky says "cannot reproduce training," start with tracking discipline and shared servers. If it says "cannot schedule retrains," start with orchestrators. If it says "cannot serve safely at scale," start with KServe or Seldon while keeping MLflow as the registry spine. The diagram is only useful when the diagnosis step is honest.

## Did You Know?

- MLflow introduced model registry stages that influenced how teams think about lifecycle labels, but stages were deprecated in MLflow 2.9.0 in favor of aliases and richer tags for flexible promotion workflows.
- The `--serve-artifacts` tracking-server flag lets clients upload and download artifacts through MLflow instead of requiring direct object-store credentials on every laptop.
- MLflow 3 adds logged-model search APIs so teams can rank checkpoints without manually stitching together run artifact paths.
- Google Cloud’s Vertex AI Experiments autologging leverages MLflow autologging under the hood for several frameworks, which shows how the tracking API became a de facto integration surface across vendors.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No `MLFLOW_TRACKING_URI` set | Runs land in local `./mlruns` and never reach the team server | Export URI in CI, notebooks, and Kubernetes Job manifests |
| Using SQLite for shared servers | Locking and corruption under concurrent writers | Deploy PostgreSQL or another supported SQL backend |
| Missing artifact store configuration | Metadata exists but model binaries are lost on pod restart | Configure `default-artifact-root` to durable object storage |
| Training outside `mlflow.start_run()` | Metrics and params never attach to a run | Wrap training or enable notebook autolog helpers |
| Logging metrics inside tight loops | Metadata bloat and slow UI queries | Log epoch-level aggregates unless step curves are required |
| No model signature or input example | Serving fails on schema mismatch | Pass `input_example` or `signature` to `log_model` |
| Production code pins version integers | Every promotion requires code changes | Load `models:/name@champion` and move aliases |
| Keeping stage-based URIs after 2.9 | Deprecated paths break on upgrades | Migrate to aliases per official migration guide |

## Quiz

<details><summary>Your team runs twelve nightly training jobs. Scientists still cannot find which run produced the best validation AUC last week. Tracking is enabled, but results are scattered across laptops. What is the most likely root cause and fix?</summary>

The root cause is usually missing shared tracking configuration, not missing ML science. Runs are probably logging to local `./mlruns` directories because `MLFLOW_TRACKING_URI` and a shared experiment namespace were never enforced. Deploy a central tracking server with a database-backed metadata store, set the URI in CI and notebooks, and require `mlflow.set_experiment` for project work. Once runs land in one server, `search_runs` can rank by `metrics.val_auc` without manual spreadsheets.

</details>

<details><summary>A legacy service loads `models:/fraud-scorer/Production`. You upgrade MLflow and stages behave inconsistently. What migration path aligns with current registry guidance?</summary>

Stages are deprecated since MLflow 2.9.0. Create aliases such as `champion` and `challenger`, assign them to the approved versions, and change serving code to `models:/fraud-scorer@champion`. Use tags like `validation_status:approved` for governance metadata that stages used to imply. Keep version numbers immutable for audit history while aliases carry the mutable deployment pointer.

</details>

<details><summary>Platform engineers deploy MLflow on Kubernetes with emptyDir for artifacts and SQLite for metadata. It works in demos but fails when three data scientists train concurrently. What should change?</summary>

Treat the tracking server as stateful infrastructure. Move metadata to PostgreSQL or another supported SQL backend and store artifacts in S3-compatible object storage with `--serve-artifacts` if clients lack direct bucket access. SQLite and ephemeral disks are solo-lab shortcuts, not shared-team architecture. Add backups and auth before widening namespace access.

</details>

<details><summary>Your Kubeflow Pipeline trains, logs to MLflow, and registers a model, but nobody schedules retraining when upstream data changes. Which tool owns that gap?</summary>

MLflow records what happened during training; it does not watch data partitions or schedule downstream dependencies. Kubeflow Pipelines, Airflow, or another orchestrator should trigger retraining when data or features change. Keep MLflow inside the training step for parameters, metrics, artifacts, and registry promotion while the orchestrator owns cron schedules, retries, and DAG dependencies.

</details>

<details><summary>A data scientist enables autolog and assumes dataset lineage is complete. Auditors ask which feature snapshot trained the production model. What was missed?</summary>

Autolog captures framework parameters and metrics, not necessarily business data contracts. Add explicit `log_param` or `log_artifact` calls for dataset identifiers, feature view versions, label policies, and approval tags. Registry tags such as `data_contract:2026-06-01` make promotion decisions auditable beyond framework defaults.

</details>

<details><summary>You need canary rollouts, multi-model graphs, and V2 inference protocol compliance on Kubernetes 1.35. Should `mlflow models serve` be your only serving layer?</summary>

Usually not. `mlflow models serve` is excellent for smoke tests and small deployments, but platform-grade rollouts belong in KServe or Seldon. Keep MLflow as the packaging and registry source with alias URIs, then let the serving platform handle traffic splitting, autoscaling, and protocol standards. This preserves a clean boundary between artifact governance and inference operations.

</details>

<details><summary>Two models are registered as versions 4 and 5. Product wants A/B testing without changing application code each time. How do aliases help?</summary>

Assign `champion` to version 4 and `challenger` to version 5, or run two services that load different aliases. Application code references stable alias URIs instead of integers. When version 5 wins offline and shadow tests, move `champion` to version 5 in the registry. Consumers reload or restart according to serving platform semantics without editing hard-coded version numbers in Git.

</details>

<details><summary>Your organization must choose between self-hosted MLflow and a managed experiment SaaS. Compliance requires data residency in your VPC, but scientists want rich comparison UI. What decision factors matter most?</summary>

Start with residency and identity requirements. Self-hosted MLflow keeps metadata and artifacts inside your network boundary at the cost of operating PostgreSQL, object storage, ingress, and backups. Managed SaaS may offer superior UI collaboration but needs contractual and technical proof that data stays in approved regions. Many teams self-host MLflow for registry URIs while using orchestrators and serving platforms they already operate.

</details>

## Hands-On Exercise

Deploy a minimal MLflow tracking server on Kubernetes, log a run from your workstation, register a model, assign a `champion` alias, and verify you can load the model by alias URI. The lab uses a single-replica Deployment for simplicity; production would add PostgreSQL, object storage, and authentication.

Treat the exercise as a vertical slice through the durable spine rather than as a production blueprint. You will stand up the control plane endpoint, emit a run from client code, promote a registry version with an alias, and load that alias from a serving process. If any step fails, fix it before moving on because later steps assume earlier contracts. This mirrors real platform debugging more faithfully than jumping straight to a Helm chart without understanding the data paths.

The minimal Deployment intentionally uses default local artifact storage so the lab runs on kind or minikube without MinIO credentials. That is a teaching compromise. In shared environments you would never accept ephemeral artifact storage, but here it keeps focus on API flow. When you graduate the pattern to a team server, add PostgreSQL and S3-compatible storage before inviting other scientists to connect.

### Task 1: Create namespace and deploy MLflow

```bash
kubectl create namespace mlflow

kubectl create secret generic mlflow-secrets \
  --namespace mlflow \
  --from-literal=postgres-user=mlflow \
  --from-literal=postgres-password=mlflow-dev-only
```

```yaml
# mlflow-minimal.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
  namespace: mlflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlflow
  template:
    metadata:
      labels:
        app: mlflow
    spec:
      containers:
        - name: mlflow
          image: ghcr.io/mlflow/mlflow:v3.13.0
          command: ["mlflow", "server", "--host=0.0.0.0", "--port=5000"]
          ports:
            - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-server
  namespace: mlflow
spec:
  selector:
    app: mlflow
  ports:
    - port: 5000
      targetPort: 5000
```

```bash
kubectl apply -f mlflow-minimal.yaml
kubectl port-forward -n mlflow svc/mlflow-server 5000:5000
```

### Task 2: Log a run and register a model

```bash
python3 -m venv .mlflow-lab && source .mlflow-lab/bin/activate
pip install "mlflow>=3.13" scikit-learn
python end_to_end.py   # use the worked example with TRACKING_URI=http://127.0.0.1:5000
```

### Task 3: Verify alias loading

```bash
mlflow models serve \
  --model-uri "models:/iris-classifier@champion" \
  --host 127.0.0.1 --port 5001 --env-manager local

curl -s -X POST http://127.0.0.1:5001/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
```

### Success Criteria

- [ ] MLflow tracking server is reachable at `http://127.0.0.1:5000` via port-forward
- [ ] A run appears under the `module-9-2-demo` experiment with parameters and metrics
- [ ] `iris-classifier` has a registered version with the `champion` alias
- [ ] `mlflow pyfunc.load_model("models:/iris-classifier@champion")` succeeds locally
- [ ] The served `/invocations` endpoint returns a prediction for the sample payload

### Cleanup

```bash
kubectl delete namespace mlflow
deactivate
```

If something failed mid-lab, capture the symptom before deleting resources. Runs missing in the UI usually indicate URI or experiment misconfiguration. Artifact upload errors often indicate missing `--serve-artifacts` or bucket credentials when you extend the lab to object storage. Serving failures after promotion usually indicate alias not set, wrong model name, or tracking server unreachable from the serving process environment.

## Sources

- [MLflow Tracking documentation](https://mlflow.org/docs/latest/tracking.html) — Runs, experiments, autolog, and tracking server concepts used throughout this module.
- [MLflow Tracking API](https://mlflow.org/docs/latest/tracking/tracking-api.html) — Reference for `log_param`, `log_metric`, `log_artifact`, and run lifecycle calls.
- [MLflow Tracking Server](https://mlflow.org/docs/latest/tracking/server.html) — Backend store, artifact store, and `--serve-artifacts` deployment patterns.
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html) — Registered models, versions, aliases, tags, and registry URIs.
- [Model Registry Workflows](https://mlflow.org/docs/latest/ml/model-registry/workflow/) — Current alias-centric promotion guidance and stages deprecation context.
- [Migrating from Stages](https://mlflow.org/docs/latest/model-registry.html#migrating-from-stages) — Official migration notes for teams replacing stage URIs with aliases.
- [RFC: Deprecating Model Registry Stages](https://github.com/mlflow/mlflow/issues/10336) — Upstream rationale for deprecating stages starting in MLflow 2.9.0.
- [MLflow Models](https://mlflow.org/docs/latest/models.html) — Model format, flavors, signatures, and deployment tool overview.
- [MLflow Projects](https://mlflow.org/docs/latest/projects.html) — Reproducible entry points and `mlflow run` packaging boundaries.
- [Deploy MLflow Model Locally](https://mlflow.org/docs/latest/deployment/deploy-model-locally/) — `mlflow models serve` smoke-testing pattern used in Hands-On.
- [Deploy MLflow Model to Kubernetes](https://mlflow.org/docs/latest/deployment/deploy-model-to-kubernetes/) — Container build and Kubernetes deployment guidance for served models.
- [mlflow.sklearn API](https://mlflow.org/docs/latest/python_api/mlflow.sklearn.html) — Scikit-learn flavor logging used in training examples.
- [mlflow.pyfunc API](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html) — Generic Python function loading path for alias-based URIs.
- [MLflow GitHub repository](https://github.com/mlflow/mlflow) — Source, releases, and issue tracking for the open-source project.
- [Weights & Biases Tracking Guide](https://docs.wandb.ai/guides/track) — Peer experiment-tracking capability comparison reference.
- [Comet Documentation](https://www.comet.com/docs/v2/) — Peer experiment-management and model registry documentation.
- [Neptune.ai Documentation](https://docs.neptune.ai/) — Peer run-tracking and model registry documentation.
- [DVC Experiment Management](https://dvc.org/doc/user-guide/experiment-management) — Git-native experiment lineage peer reference.
- [Amazon SageMaker MLflow](https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html) — Managed MLflow-compatible tracking on AWS.
- [Vertex AI Experiments Autologging](https://docs.cloud.google.com/vertex-ai/docs/experiments/user-journey/uj-autologging) — Managed autologging integration that uses MLflow autologging APIs.
- [Seldon Core MLflow Integration](https://docs.seldon.io/projects/seldon-core/en/latest/navigating/mlflow.html) — Serving integration path for MLflow-packaged models.
- [KServe Project Site](https://kserve.github.io/website/) — Kubernetes-native inference platform cross-reference for production serving.

## Next Module

Continue to [Module 9.3: Feature Stores](../module-9.3-feature-stores/) to learn how feature data is managed, versioned, and served consistently for training and inference.

Experiment metadata tells you which model ran; feature stores answer whether training and inference used the same inputs. The next module closes that loop so promoted models do not silently consume drifting features after alias promotion.

If you completed the Hands-On lab, carry your alias URI habit forward. Feature pipelines and serving endpoints should reference the same logical data contracts you log as parameters during training.

That discipline is what turns experiment tracking from a scientist-only convenience into an organization-wide reliability practice in production teams.
