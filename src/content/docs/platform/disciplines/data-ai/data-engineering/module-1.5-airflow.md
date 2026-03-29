---
title: "Module 1.5: Data Orchestration with Apache Airflow"
slug: platform/disciplines/data-ai/data-engineering/module-1.5-airflow
sidebar:
  order: 6
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2.5 hours

## Prerequisites

Before starting this module:
- **Required**: Basic Python programming — Variables, functions, decorators, context managers
- **Required**: Kubernetes fundamentals — Pods, Deployments, Services, ConfigMaps, Secrets
- **Recommended**: [Module 1.4 — Batch Processing & Apache Spark on K8s](../module-1.4-spark/) — Understanding batch job execution
- **Recommended**: Familiarity with cron syntax and scheduling concepts

---

## Why This Module Matters

You have Kafka streaming events. Flink processing them in real time. Spark running batch transformations. Databases storing results. Dashboards visualizing insights.

Who coordinates all of this?

Without orchestration, your data platform is a collection of independent tools. Somebody has to ensure the Spark job runs after the data lands in S3. Somebody has to retry the failed transformation. Somebody has to alert the team when the pipeline is 3 hours late. Somebody has to make sure the downstream dashboard only refreshes after all upstream jobs succeed.

That somebody is Apache Airflow.

Airflow is the most widely adopted data orchestration platform in the world. It runs at Airbnb (where it was created), Google, Spotify, Slack, PayPal, and thousands of other organizations. It is not a data processing engine — it does not move or transform data itself. It **orchestrates** other tools to do that work, providing scheduling, dependency management, retries, alerting, and observability.

On Kubernetes, Airflow gains a superpower: the **KubernetesExecutor**. Instead of running tasks on a pool of permanent workers, each task runs in its own isolated Pod. Different tasks can use different Docker images, different resource limits, and different Python dependencies — all without conflicts.

This module teaches you to deploy Airflow on Kubernetes, write DAGs that orchestrate real workloads, and operate it in production.

---

## Did You Know?

- **Airflow was created at Airbnb in 2014 by Maxime Beauchemin**, who later also created Apache Superset (the visualization tool). He built Airflow because existing tools like Oozie and Luigi could not handle Airbnb's increasingly complex data pipelines.
- **The name "DAG" is not Airflow-specific.** A Directed Acyclic Graph is a mathematical concept used everywhere from Git (commit history) to build systems (Make) to spreadsheets (cell dependency). Airflow popularized the term in data engineering, but the concept is universal.
- **Airflow 2.0 was the most significant rewrite in the project's history.** Released in December 2020, it introduced the TaskFlow API, a stable REST API, independent task scheduling, and the High Availability scheduler. The codebase was almost entirely rewritten.

---

## Airflow Architecture

### The Four Components

```
┌──────────────────────────────────────────────────────────┐
│                    AIRFLOW ON KUBERNETES                  │
│                                                          │
│  ┌─────────────────┐     ┌──────────────────────┐       │
│  │    Webserver     │     │     Scheduler        │       │
│  │  (Flask UI)      │     │  (parses DAGs,       │       │
│  │                  │     │   triggers tasks,    │       │
│  │  DAG view        │     │   manages state)     │       │
│  │  Task logs       │     │                      │       │
│  │  Variables/       │     │  ┌────────────────┐ │       │
│  │  Connections     │     │  │ DAG Processor  │ │       │
│  └──────────────────┘     │  └────────────────┘ │       │
│           │                └──────────┬───────────┘       │
│           │                          │                    │
│           ▼                          ▼                    │
│  ┌──────────────────┐     ┌──────────────────────┐       │
│  │   Metadata DB    │     │   Executor           │       │
│  │  (PostgreSQL)    │◄────│                      │       │
│  │                  │     │  KubernetesExecutor: │       │
│  │  DAG state       │     │  Each task = 1 Pod   │       │
│  │  Task history    │     │                      │       │
│  │  Variables       │     │  ┌───┐ ┌───┐ ┌───┐ │       │
│  │  Connections     │     │  │Pod│ │Pod│ │Pod│ │       │
│  └──────────────────┘     │  └───┘ └───┘ └───┘ │       │
│                           └──────────────────────┘       │
└──────────────────────────────────────────────────────────┘
```

**Webserver**: The Flask-based UI where you view DAGs, monitor task execution, check logs, manage variables and connections. Runs as a Deployment.

**Scheduler**: The brain of Airflow. It parses DAG files, determines which tasks are ready to run, and tells the executor to launch them. Supports HA with multiple replicas since Airflow 2.0.

**Metadata Database**: PostgreSQL (or MySQL) storing all state: DAG definitions, task instances, run history, variables, connections, XComs. This is the source of truth.

**Executor**: Determines HOW tasks run. The KubernetesExecutor creates a new Pod for each task, which is the recommended approach on Kubernetes.

### DAGs, Tasks, and Operators

A **DAG** (Directed Acyclic Graph) defines the workflow: what tasks to run and in what order.

```python
# Simple DAG structure:
#
#        ┌──→ transform_users ──→┐
# extract ──→ transform_orders ──→ load ──→ notify
#        └──→ transform_products─→┘
```

A **Task** is a single unit of work within a DAG. It could be running a SQL query, executing a Python function, triggering a Spark job, or calling an API.

An **Operator** defines what a task does:

| Operator | Purpose | Example |
|----------|---------|---------|
| `PythonOperator` | Run a Python function | Data validation |
| `BashOperator` | Run a shell command | File processing |
| `KubernetesPodOperator` | Run a task in a dedicated Pod | ML training |
| `SparkKubernetesOperator` | Submit a Spark job | Batch ETL |
| `PostgresOperator` | Execute SQL | Data warehousing |
| `S3ToGCSOperator` | Move data between clouds | Migration |
| `SlackWebhookOperator` | Send notifications | Alerting |

### KubernetesExecutor vs CeleryExecutor vs KubernetesPodOperator

This is the most confusing part of Airflow on Kubernetes. Let me clear it up:

```
┌──────────────────────────────────────────────────────────────┐
│              EXECUTOR COMPARISON                             │
├───────────────┬──────────────────┬───────────────────────────┤
│               │ KubernetesExec.  │ CeleryExecutor            │
├───────────────┼──────────────────┼───────────────────────────┤
│ Workers       │ Ephemeral Pods   │ Long-running worker Pods  │
│ Isolation     │ Per-task Pod     │ Shared worker process     │
│ Startup time  │ 5-30 seconds     │ Instant (worker running)  │
│ Resource use  │ Pay per task     │ Always-on workers         │
│ Dependencies  │ Per-task image   │ Shared worker image       │
│ Scaling       │ Infinite (K8s)   │ Fixed pool (+ autoscaler) │
│ Best for      │ Varied workloads │ Homogeneous, fast tasks   │
└───────────────┴──────────────────┴───────────────────────────┘
```

**KubernetesPodOperator** is different from the KubernetesExecutor. It is a specific operator that runs a task inside a custom Pod, regardless of which executor you use. You can use it with CeleryExecutor to run specific heavy tasks in isolated Pods while other tasks run on Celery workers.

**Recommendation**: Start with KubernetesExecutor. Switch to CeleryExecutor only if Pod startup latency is unacceptable for your use case (sub-second task scheduling).

---

## Deploying Airflow on Kubernetes with Helm

### The Official Helm Chart

```bash
# Add the Apache Airflow Helm repository
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Create the namespace
kubectl create namespace airflow
```

### Production-Ready Values

```yaml
# airflow-values.yaml
# Core settings
airflowVersion: "2.10.4"
defaultAirflowRepository: apache/airflow
defaultAirflowTag: "2.10.4"

# Use KubernetesExecutor
executor: KubernetesExecutor

# Webserver
webserver:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      memory: 2Gi
  service:
    type: ClusterIP
  defaultUser:
    enabled: true
    username: admin
    password: changeme         # Use a Secret in production
    role: Admin
    email: admin@example.com

# Scheduler (HA with multiple replicas)
scheduler:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      memory: 2Gi

# Triggerer (for deferrable operators)
triggerer:
  replicas: 1
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      memory: 1Gi

# Metadata database
postgresql:
  enabled: true
  auth:
    postgresPassword: airflow
    database: airflow
  primary:
    persistence:
      size: 10Gi
      storageClass: standard

# DAG synchronization via Git
dags:
  gitSync:
    enabled: true
    repo: https://github.com/your-org/airflow-dags.git
    branch: main
    subPath: dags
    wait: 60                   # Sync every 60 seconds

# Logging
logs:
  persistence:
    enabled: true
    size: 10Gi
    storageClassName: standard

# KubernetesExecutor worker Pod template
workers:
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      memory: 1Gi

# Environment variables
env:
  - name: AIRFLOW__CORE__LOAD_EXAMPLES
    value: "False"
  - name: AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION
    value: "True"
  - name: AIRFLOW__WEBSERVER__EXPOSE_CONFIG
    value: "False"
  - name: AIRFLOW__CORE__DEFAULT_TIMEZONE
    value: "UTC"

# Extra ConfigMaps and Secrets
extraEnvFrom: |
  - secretRef:
      name: airflow-connections

# Enable PgBouncer for connection pooling
pgbouncer:
  enabled: true
  maxClientConn: 100
  metadataPoolSize: 10
  resultBackendPoolSize: 5
```

```bash
# Install Airflow
helm install airflow apache-airflow/airflow \
  --namespace airflow \
  --values airflow-values.yaml \
  --timeout 10m

# Wait for deployment
kubectl -n airflow wait --for=condition=Available deployment/airflow-webserver --timeout=300s

# Access the web UI
kubectl -n airflow port-forward svc/airflow-webserver 8080:8080 &
# Open http://localhost:8080 (admin / changeme)
```

---

## Writing DAGs

### The TaskFlow API (Modern Approach)

```python
# dags/sales_pipeline.py
from datetime import datetime, timedelta
from airflow.decorators import dag, task

default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "email_on_failure": True,
    "email": ["data-team@example.com"],
}


@dag(
    dag_id="sales_pipeline",
    description="Daily sales data pipeline: extract, transform, load",
    schedule="0 6 * * *",       # Every day at 6 AM UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,              # Don't backfill missed runs
    max_active_runs=1,          # Only one run at a time
    tags=["sales", "production"],
    default_args=default_args,
)
def sales_pipeline():

    @task()
    def extract_sales_data(**context):
        """Extract sales data from source systems."""
        execution_date = context["ds"]
        print(f"Extracting sales data for {execution_date}")

        # Simulate extraction
        import json
        records = [
            {"id": i, "amount": 100 + i * 10, "city": "NYC"}
            for i in range(1000)
        ]
        return json.dumps(records)

    @task()
    def validate_data(raw_data: str):
        """Validate extracted data quality."""
        import json
        records = json.loads(raw_data)
        total = len(records)
        valid = sum(1 for r in records if r["amount"] > 0)
        ratio = valid / total

        print(f"Validation: {valid}/{total} records valid ({ratio:.1%})")
        if ratio < 0.95:
            raise ValueError(f"Data quality below threshold: {ratio:.1%}")

        return raw_data

    @task()
    def transform_data(validated_data: str):
        """Apply business transformations."""
        import json
        records = json.loads(validated_data)

        # Add computed fields
        for record in records:
            record["revenue_category"] = (
                "high" if record["amount"] > 500
                else "medium" if record["amount"] > 100
                else "low"
            )

        print(f"Transformed {len(records)} records")
        return json.dumps(records)

    @task()
    def load_to_warehouse(transformed_data: str):
        """Load transformed data into the data warehouse."""
        import json
        records = json.loads(transformed_data)
        print(f"Loading {len(records)} records to warehouse")
        # In production: write to PostgreSQL, BigQuery, Redshift, etc.
        return len(records)

    @task()
    def send_notification(record_count: int, **context):
        """Send Slack notification on pipeline completion."""
        execution_date = context["ds"]
        message = (
            f"Sales pipeline completed for {execution_date}. "
            f"Processed {record_count} records."
        )
        print(f"Notification: {message}")
        # In production: use SlackWebhookOperator or HTTP hook

    # Define the DAG flow
    raw = extract_sales_data()
    validated = validate_data(raw)
    transformed = transform_data(validated)
    count = load_to_warehouse(transformed)
    send_notification(count)


sales_pipeline()
```

### Using KubernetesPodOperator for Heavy Tasks

When a task needs a different Docker image, specific resources, or complete isolation:

```python
# dags/ml_training_pipeline.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.operators.python import PythonOperator
from kubernetes.client import models as k8s

default_args = {
    "owner": "ml-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="ml_training_pipeline",
    description="Train ML model using Spark for feature prep and custom image for training",
    schedule="0 2 * * 0",        # Weekly on Sunday at 2 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["ml", "training"],
    default_args=default_args,
) as dag:

    # Task 1: Feature preparation using PySpark
    prepare_features = KubernetesPodOperator(
        task_id="prepare_features",
        name="feature-prep",
        namespace="airflow",
        image="my-registry.io/spark-feature-prep:v2.0.0",
        cmds=["python", "/app/prepare_features.py"],
        arguments=["--date", "{{ ds }}", "--output", "s3://ml-data/features/"],
        resources=k8s.V1ResourceRequirements(
            requests={"cpu": "2", "memory": "4Gi"},
            limits={"memory": "8Gi"},
        ),
        env_vars={
            "SPARK_MASTER": "k8s://https://kubernetes.default.svc",
            "AWS_REGION": "us-east-1",
        },
        env_from=[
            k8s.V1EnvFromSource(
                secret_ref=k8s.V1SecretEnvSource(name="aws-credentials")
            )
        ],
        is_delete_operator_pod=True,
        get_logs=True,
        startup_timeout_seconds=300,
    )

    # Task 2: Model training using GPU
    train_model = KubernetesPodOperator(
        task_id="train_model",
        name="model-training",
        namespace="airflow",
        image="my-registry.io/ml-trainer:v3.1.0",
        cmds=["python", "/app/train.py"],
        arguments=[
            "--features", "s3://ml-data/features/{{ ds }}/",
            "--model-output", "s3://ml-models/{{ ds }}/",
            "--epochs", "50",
        ],
        resources=k8s.V1ResourceRequirements(
            requests={"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": "1"},
            limits={"memory": "16Gi", "nvidia.com/gpu": "1"},
        ),
        node_selector={"accelerator": "nvidia-tesla-t4"},
        tolerations=[
            k8s.V1Toleration(
                key="nvidia.com/gpu",
                operator="Exists",
                effect="NoSchedule",
            )
        ],
        is_delete_operator_pod=True,
        get_logs=True,
        startup_timeout_seconds=600,
    )

    # Task 3: Model validation
    validate_model = KubernetesPodOperator(
        task_id="validate_model",
        name="model-validation",
        namespace="airflow",
        image="my-registry.io/ml-validator:v1.5.0",
        cmds=["python", "/app/validate.py"],
        arguments=[
            "--model", "s3://ml-models/{{ ds }}/",
            "--test-data", "s3://ml-data/test/",
            "--threshold", "0.85",
        ],
        resources=k8s.V1ResourceRequirements(
            requests={"cpu": "2", "memory": "4Gi"},
            limits={"memory": "4Gi"},
        ),
        is_delete_operator_pod=True,
        get_logs=True,
    )

    # Task 4: Send Slack notification
    def notify_completion(**context):
        ti = context["task_instance"]
        dag_run = context["dag_run"]
        message = (
            f"ML Training Pipeline completed.\n"
            f"Run: {dag_run.run_id}\n"
            f"Date: {context['ds']}\n"
        )
        print(message)

    notify = PythonOperator(
        task_id="notify_completion",
        python_callable=notify_completion,
    )

    prepare_features >> train_model >> validate_model >> notify
```

---

## Monitoring DAGs

### The Airflow UI

The Airflow web UI provides comprehensive monitoring:

| View | What It Shows | When To Use |
|------|-------------|------------|
| **DAGs list** | All DAGs with status, schedule, last run | Daily overview |
| **Grid view** | Historical task status in a grid layout | Spot patterns (recurring failures) |
| **Graph view** | DAG structure with task states | Debug dependencies |
| **Gantt view** | Task execution timeline | Identify bottlenecks and parallelism |
| **Task logs** | Stdout/stderr from each task | Debug failures |
| **Landing times** | Time between scheduled and actual execution | Detect growing delays |

### Airflow Metrics with Prometheus

```yaml
# In airflow-values.yaml
config:
  metrics:
    statsd_on: true
    statsd_host: statsd-exporter
    statsd_port: 9125
    statsd_prefix: airflow

# Deploy StatsD exporter
extraObjects:
  - apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: statsd-exporter
      namespace: airflow
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: statsd-exporter
      template:
        metadata:
          labels:
            app: statsd-exporter
          annotations:
            prometheus.io/scrape: "true"
            prometheus.io/port: "9102"
        spec:
          containers:
            - name: statsd-exporter
              image: prom/statsd-exporter:v0.27.2
              ports:
                - containerPort: 9125
                  protocol: UDP
                - containerPort: 9102
              resources:
                requests:
                  cpu: 100m
                  memory: 128Mi
```

**Key metrics to monitor:**

| Metric | Alert Threshold | Meaning |
|--------|----------------|---------|
| `airflow_scheduler_heartbeat` | Missing for > 30s | Scheduler is down |
| `airflow_dag_processing_total_parse_time` | > 30s | DAG parsing is too slow |
| `airflow_pool_open_slots` | 0 for > 5 min | All task slots are full |
| `airflow_dagrun_duration_success` | 2x normal duration | Pipeline is slower than usual |
| `airflow_ti_failures` | > 3 per hour | Tasks are failing frequently |
| `airflow_zombie_killed` | > 0 | Tasks are becoming zombies (bad) |

---

## Retry Strategies and Error Handling

### Configuring Retries

```python
default_args = {
    # Retry up to 3 times
    "retries": 3,

    # Wait 5 minutes before first retry
    "retry_delay": timedelta(minutes=5),

    # Exponential backoff: 5 min, 10 min, 20 min
    "retry_exponential_backoff": True,

    # Cap maximum retry delay at 1 hour
    "max_retry_delay": timedelta(hours=1),

    # Timeout the task after 2 hours
    "execution_timeout": timedelta(hours=2),

    # Send email on failure (after all retries exhausted)
    "email_on_failure": True,
    "email_on_retry": False,
}
```

### SLA Monitoring

```python
@dag(
    dag_id="critical_pipeline",
    schedule="0 */2 * * *",  # Every 2 hours
    sla_miss_callback=sla_alert,
    default_args=default_args,
)
def critical_pipeline():

    @task(sla=timedelta(minutes=30))
    def time_sensitive_task():
        """This task must complete within 30 minutes."""
        # If it takes longer, the sla_miss_callback fires
        pass
```

### Handling Upstream Failures with Trigger Rules

```python
from airflow.utils.trigger_rule import TriggerRule

@task(trigger_rule=TriggerRule.ALL_SUCCESS)
def proceed_if_all_pass():
    """Default: runs only if all upstream tasks succeeded."""
    pass

@task(trigger_rule=TriggerRule.ONE_SUCCESS)
def proceed_if_any_pass():
    """Runs if at least one upstream task succeeded."""
    pass

@task(trigger_rule=TriggerRule.ALL_DONE)
def cleanup_always():
    """Runs regardless of upstream success/failure. Good for cleanup."""
    pass

@task(trigger_rule=TriggerRule.ALL_FAILED)
def alert_on_total_failure():
    """Runs only if ALL upstream tasks failed."""
    pass
```

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Putting heavy logic directly in DAG files | Treating DAGs like scripts | DAG files should define structure. Put logic in separate modules, or use KubernetesPodOperator for heavy work |
| Using `catchup=True` without understanding it | Default behavior | Airflow will run ALL missed DAG runs since `start_date`. Set `catchup=False` unless you explicitly need backfilling |
| Not setting `max_active_runs` | Seems unnecessary | Without it, multiple runs of the same DAG execute simultaneously, causing resource contention and data corruption |
| Hardcoding dates instead of using Jinja templates | Quick and easy | Use `{{ ds }}`, `{{ ds_nodash }}`, `{{ execution_date }}` for date-aware pipelines that support backfilling |
| Making DAGs that are hard to parse | Complex Python at top level | Keep DAG files simple. Avoid heavy imports, API calls, or database queries at module level — the scheduler parses DAGs every 30 seconds |
| Running the scheduler with 1 replica | Works for development | Run 2+ scheduler replicas in production for HA. If the single scheduler dies, nothing gets scheduled |
| Not using PgBouncer | "PostgreSQL handles connections fine" | Each task Pod opens its own database connection. With 50 concurrent tasks, that is 50 connections — PgBouncer pools them efficiently |
| Ignoring XCom size limits | Passing large datasets between tasks | XComs are stored in the metadata DB. Pass file paths (S3 URIs) instead of actual data. Max recommended XCom size: 48 KB |
| Using CeleryExecutor when KubernetesExecutor is sufficient | Following outdated guides | KubernetesExecutor is simpler to operate and provides better isolation. Use Celery only when sub-second task startup is required |

---

## Quiz

**Question 1:** What is the difference between the KubernetesExecutor and the KubernetesPodOperator?

<details>
<summary>Show Answer</summary>

**KubernetesExecutor** is an executor type — it determines HOW tasks run. With KubernetesExecutor, every task in every DAG runs in its own isolated Kubernetes Pod. The executor creates and manages these Pods.

**KubernetesPodOperator** is a specific operator — it determines WHAT a task does. It explicitly launches a specific container image in a Pod with custom configuration (resources, volumes, node selectors). It can be used with ANY executor (KubernetesExecutor, CeleryExecutor, LocalExecutor).

They serve different purposes: KubernetesExecutor is about execution infrastructure; KubernetesPodOperator is about task definition. You can use both together — a DAG running on KubernetesExecutor can have some tasks as PythonOperators (running in the default worker image) and some as KubernetesPodOperators (running in custom images).

</details>

**Question 2:** Why should DAG files be kept simple and avoid heavy imports or computations at the module level?

<details>
<summary>Show Answer</summary>

The Airflow scheduler parses **all** DAG files every 30 seconds (configurable via `dag_dir_list_interval`). During parsing, Python imports the file and executes all top-level code. If a DAG file has:
- Heavy imports (pandas, tensorflow, pyspark)
- Database queries
- API calls
- Complex computations

...these execute on EVERY parse cycle, consuming scheduler resources and slowing down DAG discovery. This can cause the scheduler to fall behind, creating a cascade of delayed task executions.

Best practice: Keep DAG files lightweight. Move heavy logic into separate modules, use lazy imports inside task functions, or use KubernetesPodOperator where the heavy code runs inside the task Pod, not during parsing.

</details>

**Question 3:** What does `catchup=False` do, and why is it usually set for production DAGs?

<details>
<summary>Show Answer</summary>

When `catchup=True` (the default), Airflow creates a DAG run for every scheduled interval between `start_date` and the current time. If your DAG has `start_date=datetime(2025, 1, 1)` and `schedule="@daily"`, deploying it in March 2026 would trigger 449 backfill runs.

`catchup=False` tells Airflow to only create runs from the current time forward, skipping all missed intervals. This is usually what you want in production because:
1. Backfilling hundreds of runs unexpectedly can overwhelm your cluster
2. Most pipelines process the latest data and do not need historical reruns
3. If you DO need to backfill, you can trigger it explicitly with the CLI or UI

</details>

**Question 4:** How does Airflow handle task retries, and what is the purpose of exponential backoff?

<details>
<summary>Show Answer</summary>

When a task fails, Airflow marks it as `up_for_retry` and waits for `retry_delay` before attempting it again, up to `retries` times. After all retries are exhausted, the task is marked as `failed`.

**Exponential backoff** (`retry_exponential_backoff=True`) increases the delay between retries: if `retry_delay=5m`, the first retry waits 5 minutes, the second waits 10 minutes, the third waits 20 minutes, and so on (capped by `max_retry_delay`).

This is important because many failures are caused by transient issues (database overload, API rate limits, network partitions). Fixed-interval retries can compound the problem by hitting the failing resource at regular intervals. Exponential backoff gives the failing system progressively more time to recover, increasing the chance of success on later retries.

</details>

**Question 5:** What are XComs, and why should you avoid passing large datasets through them?

<details>
<summary>Show Answer</summary>

**XComs** (Cross-Communications) are Airflow's mechanism for tasks to pass small pieces of data to downstream tasks. When a task returns a value or uses `xcom_push()`, the data is serialized and stored in the Airflow metadata database. Downstream tasks access it via `xcom_pull()`.

You should avoid large datasets in XComs because:
1. **Database bloat**: XCom data is stored in PostgreSQL/MySQL. Large values bloat the metadata DB and slow down queries.
2. **Serialization overhead**: Large objects must be serialized/deserialized, adding latency.
3. **Memory pressure**: The scheduler and webserver load XCom data when rendering UI pages.

Best practice: Pass **references** (S3 URIs, database table names, file paths) through XComs, not actual data. Keep XCom values under 48 KB. For larger data exchange, write to shared storage (S3, GCS, NFS) and pass the path.

</details>

---

## Hands-On Exercise: Airflow with KubernetesExecutor + DAG Triggering a Task

### Objective

Deploy Airflow on Kubernetes using the official Helm chart with KubernetesExecutor, create a DAG that processes data and sends a notification, and observe task execution as isolated Pods.

### Environment Setup

```bash
# Create the kind cluster
kind create cluster --name airflow-lab

# Create namespace
kubectl create namespace airflow
```

### Step 1: Install Airflow via Helm

```yaml
# airflow-lab-values.yaml
executor: KubernetesExecutor

webserver:
  replicas: 1
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      memory: 1Gi
  defaultUser:
    enabled: true
    username: admin
    password: admin123
    role: Admin

scheduler:
  replicas: 1
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      memory: 1Gi

triggerer:
  enabled: false

postgresql:
  enabled: true
  auth:
    postgresPassword: airflow
  primary:
    persistence:
      size: 2Gi

pgbouncer:
  enabled: false

logs:
  persistence:
    enabled: false

dags:
  persistence:
    enabled: true
    size: 1Gi
    accessMode: ReadWriteOnce

config:
  core:
    load_examples: "False"
    dags_are_paused_at_creation: "False"
  kubernetes_executor:
    delete_worker_pods: "True"
    delete_worker_pods_on_failure: "False"
```

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update

helm install airflow apache-airflow/airflow \
  --namespace airflow \
  --values airflow-lab-values.yaml \
  --timeout 10m

kubectl -n airflow wait --for=condition=Available \
  deployment/airflow-webserver --timeout=300s
```

### Step 2: Create a DAG

```bash
# Copy a DAG file into the DAGs PVC
# First, find the DAGs PVC
kubectl -n airflow get pvc

# Create a DAG file via a temporary Pod
kubectl -n airflow run dag-loader --rm -it --restart=Never \
  --image=busybox:1.37 \
  --overrides='{
    "spec": {
      "containers": [{
        "name": "dag-loader",
        "image": "busybox:1.37",
        "command": ["sh", "-c", "cat > /opt/airflow/dags/data_pipeline.py << '\''DAGEOF'\''\nfrom datetime import datetime, timedelta\nfrom airflow.decorators import dag, task\n\n\n@dag(\n    dag_id=\"data_pipeline_lab\",\n    description=\"Lab exercise: data pipeline with notifications\",\n    schedule=None,\n    start_date=datetime(2026, 1, 1),\n    catchup=False,\n    tags=[\"lab\", \"data-engineering\"],\n    default_args={\"retries\": 1, \"retry_delay\": timedelta(minutes=1)},\n)\ndef data_pipeline_lab():\n\n    @task()\n    def generate_data():\n        import json\n        import random\n        random.seed(42)\n        records = [\n            {\"id\": i, \"value\": round(random.uniform(10, 1000), 2), \"category\": random.choice([\"A\", \"B\", \"C\"])}\n            for i in range(500)\n        ]\n        print(f\"Generated {len(records)} records\")\n        return json.dumps(records)\n\n    @task()\n    def validate(raw: str):\n        import json\n        records = json.loads(raw)\n        valid = [r for r in records if r[\"value\"] > 0]\n        print(f\"Validation: {len(valid)}/{len(records)} records valid\")\n        return json.dumps(valid)\n\n    @task()\n    def aggregate(validated: str):\n        import json\n        records = json.loads(validated)\n        from collections import defaultdict\n        totals = defaultdict(float)\n        counts = defaultdict(int)\n        for r in records:\n            totals[r[\"category\"]] += r[\"value\"]\n            counts[r[\"category\"]] += 1\n        result = {cat: {\"total\": round(totals[cat], 2), \"count\": counts[cat], \"avg\": round(totals[cat]/counts[cat], 2)} for cat in totals}\n        print(f\"Aggregation results: {json.dumps(result, indent=2)}\")\n        return json.dumps(result)\n\n    @task()\n    def notify(results: str):\n        import json\n        data = json.loads(results)\n        print(\"=\" * 50)\n        print(\"PIPELINE COMPLETE - NOTIFICATION\")\n        print(\"=\" * 50)\n        for cat, stats in data.items():\n            print(f\"  Category {cat}: {stats['count']} records, total=${stats['total']:.2f}, avg=${stats['avg']:.2f}\")\n        print(\"=\" * 50)\n        print(\"Notification sent successfully!\")\n\n    raw = generate_data()\n    validated = validate(raw)\n    aggregated = aggregate(validated)\n    notify(aggregated)\n\n\ndata_pipeline_lab()\nDAGEOF\necho DAG written successfully"],
        "volumeMounts": [{"name": "dags", "mountPath": "/opt/airflow/dags"}]
      }],
      "volumes": [{"name": "dags", "persistentVolumeClaim": {"claimName": "airflow-dags"}}]
    }
  }'
```

### Step 3: Access the UI and Trigger the DAG

```bash
# Port-forward to the Airflow web UI
kubectl -n airflow port-forward svc/airflow-webserver 8080:8080 &

# Open http://localhost:8080 in your browser
# Login: admin / admin123
# You should see "data_pipeline_lab" in the DAG list
# Click on it, then click "Trigger DAG" (play button)
```

### Step 4: Watch Task Pods

```bash
# In a separate terminal, watch Pods being created for each task
kubectl -n airflow get pods -w

# You should see Pods like:
# data-pipeline-lab-generate-data-xxxxx   (runs, completes)
# data-pipeline-lab-validate-xxxxx        (runs, completes)
# data-pipeline-lab-aggregate-xxxxx       (runs, completes)
# data-pipeline-lab-notify-xxxxx          (runs, completes)
```

### Step 5: Check Task Logs

```bash
# View logs from the notification task (or any task)
# In the Airflow UI: click on DAG → click on task → click "Log"
# Or via kubectl:
kubectl -n airflow logs -l dag_id=data_pipeline_lab --tail=50
```

### Step 6: Clean Up

```bash
kill %1  # Stop port-forward
helm -n airflow uninstall airflow
kubectl delete namespace airflow
kind delete cluster --name airflow-lab
```

### Success Criteria

You have completed this exercise when you:
- [ ] Deployed Airflow on Kubernetes with KubernetesExecutor via Helm
- [ ] Created a DAG with 4 tasks (generate, validate, aggregate, notify)
- [ ] Triggered the DAG from the Airflow web UI
- [ ] Observed individual task Pods being created and completed
- [ ] Verified task outputs in the logs (aggregation results, notification message)

---

## Key Takeaways

1. **Airflow orchestrates, it does not process** — Airflow schedules and monitors other tools (Spark, Flink, dbt). Keep logic out of DAG files.
2. **KubernetesExecutor gives each task its own Pod** — Complete isolation, per-task resource allocation, and different Docker images per task.
3. **DAG files must be lightweight** — The scheduler parses them every 30 seconds. Heavy imports or computations at module level slow down the entire system.
4. **Retries with exponential backoff are essential** — Transient failures are normal in distributed systems. Give failing services time to recover.
5. **Monitor your Airflow installation, not just your DAGs** — Scheduler heartbeat, parse time, pool utilization, and zombie tasks are as important as individual DAG success rates.

---

## Further Reading

**Books:**
- **"Data Pipelines with Apache Airflow"** — Bas Harenslak, Julian de Ruiter (Manning)
- **"Apache Airflow Best Practices"** — Astronomer.io documentation (free)

**Articles:**
- **"Airflow on Kubernetes"** — Apache Airflow documentation (airflow.apache.org/docs/helm-chart/)
- **"KubernetesExecutor Architecture"** — Apache Airflow docs (airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/kubernetes.html)

**Talks:**
- **"How to Use Apache Airflow on Kubernetes"** — Marc Lamberti, Airflow Summit 2024 (YouTube)
- **"Apache Airflow 2.x: The Full Story"** — Astronomer.io webinar series (YouTube)

---

## Summary

Apache Airflow is the glue that holds a data platform together. It does not move data or train models — it ensures the right tool runs at the right time with the right inputs, retries on failure, and alerts the team when something goes wrong.

On Kubernetes, the KubernetesExecutor transforms Airflow from a monolithic system with permanent workers into a cloud-native platform where every task gets its own isolated, ephemeral Pod. This eliminates dependency conflicts, enables per-task resource tuning, and integrates naturally with the Kubernetes ecosystem.

The most important lesson: keep your DAGs simple, your tasks idempotent, and your data references in XComs (not data itself).

---

## Next Module

Continue to [Module 1.6: Building a Data Lakehouse on Kubernetes](../module-1.6-lakehouse/) to learn how to combine the best of data lakes and data warehouses into a unified architecture on Kubernetes.

---

*"Airflow is not a data processing framework. It is a platform for programmatically authoring, scheduling, and monitoring workflows."* — Apache Airflow documentation
